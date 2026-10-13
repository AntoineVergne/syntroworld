"""The tick loop (03 §2): simultaneous moves, resolution order from the ``order`` stream,
end-of-day steps, Sam's arrival on day 4, shocks and governance.
"""

import copy
import time as _time

from . import __version__
from .brains import base as B
from .brains.mock import MockBrain
from .config import config_hash, load, load_personas, public
from .events import EventLog, canonical, state_hash
from .governance import effects as E
from .governance.blocks import Governance
from .governance.project import project as _project
from .governance.rules import RuleRegistry
from .rng import Streams
from .shocks import Shocks, shock_config
from .world import agents as A
from .world import claims as C
from .world import deals as D
from .world import economy as ECO
from .world import map as wmap
from .world import market as MKT
from .world import river as RIVER
from .world.clock import Clock
from .world.treasury import Treasury

MENU = ["set_tax", "set_dividend", "set_stipend", "allocate", "set_plant_mode", "harvest_cap",
        "ban", "set_fine", "amend_block"]
HISTORY_DAYS = 3


class World:
    def __init__(self, cfg, seed, arm="none", log_path=None, lam=None, keep_events=True):
        self.cfg = cfg
        self.seed = int(seed)
        self.arm = arm
        self.streams = Streams(self.seed)
        self.clock = Clock.from_config(cfg)
        self.tick = 0
        self.time = self.clock.at(1)
        brain_cfg = cfg.get("brain", {"type": "mock", "lambda": 0})
        self.lam = brain_cfg.get("lambda", 0) if lam is None else lam
        header = {"engine": "synw", "version": __version__, "config_hash": config_hash(cfg),
                  "seed": self.seed, "arm": arm, "world": cfg.get("world", ""),
                  "brain": {"type": "mock", "lambda": self.lam}, "config": public(cfg)}
        self.log = EventLog(log_path, header, keep=keep_events)
        self.treasury = Treasury(cfg["start"]["treasury"], self.log, lambda: self.tick)
        self.personas = load_personas(cfg)
        arrival = cfg["arrival"]
        self.citizens = {}
        for p in self.personas["citizens"]:
            founder = p["index"] != arrival["agent"]
            c = A.make_citizen(p, cfg, founder=founder)
            if founder:
                c.status = "active"
                c.arrived_tick = 1
            self.citizens[c.idx] = c
        A.init_relations(self.citizens, cfg)
        rv = cfg["river"]
        self.river_stock = rv["S0"]
        self.river_K = rv["K"]
        self.river_r_bonus = 0
        self.plant_bonus = 0
        self.drought = False
        self.shock_cfg = shock_config(cfg)
        self.site_factor = {}
        self.harvest_today = 0
        self.output_today = 0
        self.payroll_ticks_today = 0
        self.last_price = dict(cfg["prices_ref"])
        self.orders = []
        self._oid = 1
        self.claims = C.ClaimBook()
        self.deals = D.DealBook()
        self.theft_history = []
        self.undetected_thefts = []
        self.detection_bonus = 0
        self.care_pool = 0
        self.basket_cost = E.basket_cost(cfg)
        self.brains = {idx: MockBrain(c.persona, self.streams.get(f"brain/{idx}"), self.lam,
                                      self.basket_cost)
                       for idx, c in self.citizens.items()}
        self.governance = None
        self.rules = RuleRegistry(cfg, self.log, lambda: self.tick)
        self.governance = Governance(self)
        fair = self.governance.fairness(self.governance.primary_block())
        for r in self.rules.rules:
            r.fairness = fair
        for i, eff in enumerate(cfg["governance"].get("founding_rules", [])):
            eff = self._resolve_founding(eff)
            self.rules.adopt(eff, 1, f"founding-{i + 1}", fairness=fair)
        self.shocks = Shocks(self, arm)
        self.history = {idx: [] for idx in self.citizens}
        self.day = {}
        self._new_day_records()
        self._proj_cache = {}
        self._snap_tick = None
        self.attendees = set()

    def _resolve_founding(self, eff):
        eff = dict(eff)
        for k, v in list(eff.items()):
            if isinstance(v, dict) and "baskets" in v:   # [numerator, denominator] of one reference basket
                num, den = v["baskets"]
                eff[k] = self.basket_cost * num // den
        return eff

    # --- small services ------------------------------------------------------------------
    def active_ids(self):
        return [i for i in sorted(self.citizens) if self.citizens[i].active]

    def sawa(self):
        return ECO.sawa(self)

    def river_collapsed(self):
        return ECO.river_collapsed(self)

    @property
    def plant_mode(self):
        return self.rules.plant_mode

    def detection(self, act):
        base = {"steal": self.cfg["theft"]["detection"],
                "sabotage": self.cfg["sabotage"]["detection"]}.get(act, self.cfg["rules"]["breach_detection"])
        return min(950, base + self.detection_bonus)

    def roll_breach_detection(self):
        return self.streams.get("world").randrange(1000) < self.detection("other")

    def tax(self, base, c, amount):
        rate = self.rules.tax_rate(base)
        if rate <= 0 or amount <= 0:
            return 0
        t = min(amount * rate // 1000, c.credits)
        c.credits -= t
        self.treasury.collect(t, f"tax_{base}", c.idx)
        return t

    def estimate_site_damage(self, site):
        p_ref = self.cfg["prices_ref"]
        per_tick = {"fields": (self.cfg["production"]["fields"], "food"),
                    "river": (self.cfg["work"]["harvest_max"], "food"),
                    "plant": (self.cfg["production"]["plant_clean"], "energy"),
                    "workshop": (self.cfg["production"]["workshop"], "artifact")}[site]
        left = self.clock.ticks_per_day - self.time.tick_of_day
        workers = max(1, sum(1 for c in self.citizens.values() if c.active and c.location == site))
        return per_tick[0] * p_ref[per_tick[1]] // 1000 * left * workers // 4

    # --- rules bookkeeping ---------------------------------------------------------------
    def record_breach(self, act, c, detected, payload):
        if c is None:
            return
        if act == "harvest_cap":
            cap, rule = self.rules.harvest_cap()
            rules = [rule] if rule is not None else []
        else:
            rules = self.rules.bans(act, c.idx)
        for r in rules:
            self.day[c.idx]["breaches"].add(r.id)
            self.log.emit(self.tick, "breach", c.idx, {"rule": r.id, "act": act, "detected": int(detected),
                                                       "founding": int(r.source == "founding")})
        if rules and detected and act not in ("steal", "sabotage"):
            self.on_detected(act, c, payload)

    def on_detected(self, act, c, payload):
        self.log.emit(self.tick, "detected", c.idx, {"act": act, **{k: v for k, v in payload.items()
                                                                    if k in ("target", "amount", "site", "claim", "deal")}})
        fine = self.rules.fine(act)
        if fine > 0:
            paid = min(fine, c.credits)
            c.credits -= paid
            self.treasury.collect(paid, f"fine_{act}", c.idx)
            self.log.emit(self.tick, "fine", c.idx, {"act": act, "amount": paid, "due": fine})
        if self.governance is not None:
            self.governance.note_detected(act, c, payload)

    # --- one-shot effects ----------------------------------------------------------------
    def allocate(self, eff, pid):
        paid = self.treasury.pay(f"allocate:{eff['purpose']}", eff["amount"], "allocate")
        purpose = eff["purpose"]
        detail = {}
        if purpose == "river_restoration":
            before = self.river_stock
            self.river_stock = min(self.river_K, self.river_stock + paid)
            detail["stock_added"] = self.river_stock - before
        elif purpose == "care_wage":
            self.care_pool += paid
        elif purpose == "monitoring":
            self.detection_bonus = min(500, self.detection_bonus + paid // 200)
            detail["detection_bonus"] = self.detection_bonus
        elif purpose == "public_art":
            left = paid
            price = self.cfg["prices_ref"]["artifact"]
            for idx in self.active_ids():
                c = self.citizens[idx]
                q = min(c.inv["artifact"], left * 1000 // price)
                if q <= 0:
                    continue
                cost = q * price // 1000
                c.inv["artifact"] -= q
                c.credits += cost
                left -= cost
                self.treasury.goods["artifact"] += q
            if left:
                self.treasury.collect(left, "allocate_unspent")
        elif purpose == "plant_upgrade":
            self.plant_bonus = min(1000, self.plant_bonus + paid // 100)
            detail["plant_bonus"] = self.plant_bonus
        self.log.emit(self.tick, "allocation", "treasury", {"proposal": pid, "purpose": purpose,
                                                            "paid": paid, **detail})

    def restitution(self, eff, pid):
        frm = self.citizens.get(eff["from"])
        if frm is None or not frm.active:
            return
        amt = min(eff["amount"], frm.credits)
        frm.credits -= amt
        if eff["to"] == "treasury":
            self.treasury.collect(amt, "restitution", frm.idx)
        else:
            self.citizens[eff["to"]].credits += amt
        self.log.emit(self.tick, "restitution", frm.idx, {"to": eff["to"], "amount": amt,
                                                          "kind": "decision", "proposal": pid})

    # --- projection ----------------------------------------------------------------------
    def snapshot(self):
        p_ref = self.cfg["prices_ref"]
        cits = {}
        for idx in self.active_ids():
            c = self.citizens[idx]
            h = self.history[idx][-HISTORY_DAYS:]
            n = max(1, len(h))
            wealth = c.wealth(p_ref)
            if h:
                net = (wealth - h[0]["wealth_start"]) // n
            else:
                net = 0
            cits[idx] = {"wealth": wealth, "net": net,
                         "harvest": sum(x["harvest"] for x in h) // n,
                         "income": sum(x["income"] for x in h) // n,
                         "trade": sum(x["trade"] for x in h) // n,
                         "plant": sum(x["plant"] for x in h) // n,
                         "plant_ticks": sum(x["plant_ticks"] for x in h) // n}
        inflow, outflow = self.treasury.recent_flows(HISTORY_DAYS)
        rv = self.cfg["river"]
        stip_ticks = 10
        return {"citizens": cits, "prices_ref": p_ref, "basket_cost": self.basket_cost,
                "days_per_cycle": self.clock.days_per_cycle, "ticks_per_day": self.clock.ticks_per_day,
                "treasury": {"balance": self.treasury.balance, "inflow": inflow, "outflow": outflow},
                "river": {"S": self.river_stock, "K": self.river_K, "r": rv["r"], "collapse": rv["collapse"],
                          "polluting": self.plant_mode == "polluting", "polluting_cut": rv["polluting_cut"],
                          "r_bonus": self.river_r_bonus},
                "taxes": dict(self.rules.taxes), "dividend": self.rules.dividend,
                "stipend": self.rules.stipend, "stipend_ticks_per_day": stip_ticks,
                "plant_upgrade_per_credit": 10}

    def projection(self, effect):
        if self._snap_tick != self.tick:
            self._snap = self.snapshot()
            self._snap_tick = self.tick
            self._proj_cache = {}
        k = canonical(effect)
        if k not in self._proj_cache:
            self._proj_cache[k] = _project(self._snap, effect)
        return self._proj_cache[k]

    # --- observation -----------------------------------------------------------------------
    def observe(self, idx):
        c = self.citizens[idx]
        t = self.time
        coloc = []
        for o in self.citizens.values():
            if o.idx == idx or not o.active or o.location != c.location or o.transit_until >= self.tick:
                continue
            coloc.append({"idx": o.idx, "health": o.health, "food": o.inv["food"],
                          "energy": o.inv["energy"], "artifact": o.inv["artifact"],
                          "has_credits": o.credits > 0, "credits_est": o.credits})
        active = self.active_ids()
        town = {
            "detection": {"steal": self.detection("steal"), "sabotage": self.detection("sabotage"),
                          "other": self.detection("other"),
                          "claim": self.cfg["claims"]["expected_detection"]},
            "carers_at_clinic": sum(1 for o in self.citizens.values() if o.active and o.location == "clinic"
                                    and o.persona.get("main_site") == "clinic" and o.idx != idx),
            "low_health": sum(1 for i in active if self.citizens[i].health < 40 and i != idx),
            "workers": {s: sum(1 for i in active if self.citizens[i].location == s and i != idx)
                        for s in wmap.SABOTAGE_SITES},
            "social": {s: sum(1 for i in active if self.citizens[i].location == s and i != idx)
                       for s in ("cafe", "square")},
            "production": {"fields": self.cfg["production"]["fields"],
                           "plant": (self.cfg["production"]["plant_polluting"] if self.plant_mode == "polluting"
                                     else self.cfg["production"]["plant_clean"]) + self.plant_bonus,
                           "workshop": self.cfg["production"]["workshop"]},
            "wage": self.cfg["payroll"]["wage"],
            "river_K": self.river_K,
            "my_orders": {o["good"] for o in self.orders if o["agent"] == idx},
        }
        rules = self.rules.in_force_json()
        defaults = [{"id": d["id"], "defaulter": d["defaulter"], "value": d["value"]}
                    for d in D.defaults_against(self, idx)]
        gov = self.governance
        return B.Observation(
            tick=self.tick, day=t.day, tick_of_day=t.tick_of_day, cycle=t.cycle,
            day_of_cycle=t.day_of_cycle, me=idx, location=c.location, health=c.health,
            credits=c.credits, inventory=dict(c.inv), colocated=coloc, prices=dict(self.last_price),
            gate={"export": dict(self.cfg["gate"]["export"]), "import": dict(self.cfg["gate"]["import"])},
            prices_ref=dict(self.cfg["prices_ref"]), basket=dict(self.cfg["basket"]), sawa=self.sawa(),
            fees=dict(self.cfg["fees"]), beliefs=dict(c.beliefs),
            trust={str(k): v for k, v in c.trust.items()},
            relationships={str(k): v for k, v in c.relationships.items()},
            duties=gov.duties_for(idx) if gov else [],
            pending_deals=[D._public(d) for d in self.deals.pending_for(idx)],
            open_deals=[D._public(d) for d in self.deals.open_for(idx)],
            defaults_against_me=defaults, posts=[], rules=rules,
            work_ticks_today=c.work_ticks_today, harvest_today=c.harvest_today,
            max_work_ticks=self.cfg["work"]["max_ticks"], harvest_max=self.cfg["work"]["harvest_max"],
            payroll_left=self.cfg["payroll"]["daily_cap"] - self.payroll_ticks_today,
            incapacitated=c.incapacitated, in_transit=c.transit_until >= self.tick,
            data_access=c.data_access, world=self.cfg.get("world", ""),
            texts=list(gov.order) if gov else [], town=town, citizens=active, home=c.home,
            persona_index=idx, project=self.projection, menu=list(MENU),
            legal=lambda eff: E.is_legal(eff, self.cfg) and not (gov and gov.forbidden(eff)))

    # --- per-day records -------------------------------------------------------------------
    def _new_day_records(self):
        self.day = {}
        for idx, c in self.citizens.items():
            self.day[idx] = {"agent": idx, "feasible": set(), "claims": 0, "deals_due": 0, "harvested": 0,
                             "breaches": set(), "income": 0, "trade": 0, "plant": 0, "plant_ticks": 0,
                             "wealth_start": c.wealth(self.cfg["prices_ref"]), "cap_breached": False}

    def _note_feasible(self, idx, obs):
        if obs.incapacitated or obs.in_transit:
            return
        f = self.day[idx]["feasible"]
        others = [o for o in obs.colocated]
        if any(o["has_credits"] for o in others) and not self.citizens[idx].is_suspended("steal", self.tick):
            f.add("steal")
        if (others or obs.location in wmap.SABOTAGE_SITES) and not self.citizens[idx].is_suspended("sabotage", self.tick):
            f.add("sabotage")
        if obs.location == "data_tower":
            f.add("post")
        if len(obs.citizens) > 1:
            f.add("message")
        if obs.location == "river":
            f.add("harvest")
        if obs.location == "gate":
            f.add("sell_out")

    # --- the loop --------------------------------------------------------------------------
    def run(self):
        for t in range(1, self.clock.ticks + 1):
            self.step(t)
        return self.finish()

    def step(self, t):
        self.tick = t
        self.time = self.clock.at(t)
        self._start_of_tick()
        actions = {}
        for idx in self.active_ids():
            obs = self.observe(idx)
            self._note_feasible(idx, obs)
            raw = self.brains[idx].act(obs)
            act, _ = B.validate_action(raw, obs, self.log)
            actions[idx] = act
        order = list(actions)
        self.streams.get("order").shuffle(order)
        self.attendees = set()
        for idx in order:
            self._resolve(idx, actions[idx])
        if self.governance is not None:
            self.governance.on_tick_end(self.attendees)
        D.check_due(self)
        if self.time.tick_of_day == self.clock.ticks_per_day:
            self._end_of_day()

    def _start_of_tick(self):
        t = self.time
        arr = self.cfg["arrival"]
        if t.day == arr["day"] and t.tick_of_day == arr["tick"]:
            c = self.citizens.get(arr["agent"])
            if c is not None and c.status == "absent":
                c.status = "active"
                c.arrived_tick = self.tick
                c.location = "gate"
                self.day[c.idx]["wealth_start"] = c.wealth(self.cfg["prices_ref"])
                self.log.emit(self.tick, "arrival", c.idx, {"holdings": c.holdings(), "day": t.day})
        self.shocks.on_tick_start()
        if t.tick_of_day == 1:
            since = self.tick - self.clock.ticks_per_day
            for idx in self.active_ids():
                C.read_billboard(self, self.citizens[idx], since)
        for idx in self.active_ids():
            C.read_inbox(self, self.citizens[idx])
        if self.governance is not None:
            self.governance.on_tick_start()

    def _colocated(self, c, o):
        return o is not None and o.active and o.idx != c.idx and o.location == c.location \
            and o.transit_until < self.tick

    def _resolve(self, idx, act):
        c = self.citizens[idx]
        if not c.active:
            return
        k, a = act.kind, act.args
        t = self.tick
        log = self.log
        if c.incapacitated and k != "rest":
            k = "rest"
        if k != "rest" and c.is_suspended(k, t):
            log.emit(t, "suspended_action", idx, {"action": k})
            k = "rest"
        if k == "move":
            src = c.location
            c.location = a["to"]
            c.transit_until = t + wmap.transit_ticks(src, a["to"])
            log.emit(t, "move", idx, {"from": src, "to": a["to"]})
        elif k == "work":
            site = c.location
            if c.work_ticks_today >= self.cfg["work"]["max_ticks"]:
                return log.emit(t, "failed", idx, {"action": k, "reason": "work_cap"})
            res = ECO.work(self, c, site)
            c.work_ticks_today += 1
            d = self.day[idx]
            if site == "data_tower":
                d["income"] += res.get("wage", 0)
                log.emit(t, "wage", idx, res)
            else:
                if site == "plant":
                    d["plant"] += res["qty"]
                    d["plant_ticks"] += 1
                log.emit(t, "produce", idx, res)
        elif k == "harvest":
            d = self.day[idx]
            if self.rules.bans("harvest", idx):
                self.record_breach("harvest", c, self.roll_breach_detection(), {})
            res = ECO.harvest(self, c, a["qty"])
            c.work_ticks_today += 1
            d["harvested"] += 1
            log.emit(t, "harvest", idx, res)
            cap, rule = self.rules.harvest_cap()
            if cap is not None and c.harvest_today > cap and not d["cap_breached"]:
                d["cap_breached"] = True
                self.record_breach("harvest_cap", c, self.roll_breach_detection(), {"qty": c.harvest_today})
        elif k == "care":
            p = self.citizens.get(a["patient"])
            if not self._colocated(c, p):
                return log.emit(t, "failed", idx, {"action": k, "reason": "patient_not_here"})
            gain = A.apply_care(self, c, p)
            wage = 0
            if self.care_pool > 0:
                wage = min(1000, self.care_pool)
                self.care_pool -= wage
                c.credits += wage
            c.work_ticks_today += 1
            log.emit(t, "care", idx, {"patient": p.idx, "gain": gain, "wage": wage})
        elif k == "order":
            o = {"id": self._oid, "agent": idx, "good": a["good"], "side": a["side"], "qty": a["qty"],
                 "limit": a["limit"]}
            self._oid += 1
            self.orders.append(o)
            log.emit(t, "order", idx, {k2: v for k2, v in o.items() if k2 != "agent"})
        elif k in ("sell_out", "buy_in"):
            if k == "sell_out" and self.rules.bans("sell_out", idx):
                self.record_breach("sell_out", c, self.roll_breach_detection(), {})
            res = (ECO.sell_out if k == "sell_out" else ECO.buy_in)(self, c, a["good"], a["qty"])
            if k == "sell_out":
                self.day[idx]["income"] += res["credits"]
                self.day[idx]["trade"] += res["credits"]
            log.emit(t, "gate_trade", idx, {"side": "export" if k == "sell_out" else "import", **res})
        elif k == "give":
            o = self.citizens.get(a["to"])
            if not self._colocated(c, o):
                return log.emit(t, "failed", idx, {"action": k, "reason": "not_here"})
            q = A.give(c, o, a["item"], a["qty"])
            log.emit(t, "give", idx, {"to": o.idx, "item": a["item"], "qty": q})
        elif k == "steal":
            o = self.citizens.get(a["from"])
            if not self._colocated(c, o):
                return log.emit(t, "failed", idx, {"action": k, "reason": "not_here"})
            amount, _ = A.steal(self, c, o)
            self.theft_history.append((t, idx, o.idx))
            log.emit(t, "harmful_act", idx, {"kind": "theft", "target": o.idx, "amount": amount})
        elif k == "sabotage":
            tgt = a["target"]
            if isinstance(tgt, str):
                if c.location != tgt:
                    return log.emit(t, "failed", idx, {"action": k, "reason": "not_here"})
                A.sabotage(self, c, tgt)
            else:
                o = self.citizens.get(tgt)
                if not self._colocated(c, o):
                    return log.emit(t, "failed", idx, {"action": k, "reason": "not_here"})
                A.sabotage(self, c, o)
            log.emit(t, "harmful_act", idx, {"kind": "sabotage", "target": tgt})
        elif k == "post":
            C.post(self, idx, a["claim"], a["attribution"])
            self.day[idx]["claims"] += 1
        elif k == "message":
            o = self.citizens.get(a["to"])
            if o is None or not o.active:
                return log.emit(t, "failed", idx, {"action": k, "reason": "no_recipient"})
            C.message(self, idx, o.idx, a["claim"])
            self.day[idx]["claims"] += 1
        elif k == "deal":
            o = self.citizens.get(a["to"])
            if not self._colocated(c, o):
                return log.emit(t, "failed", idx, {"action": k, "reason": "not_here"})
            D.propose(self, c, o, a["give"], a["get"])
        elif k == "accept":
            D.accept(self, c, a["deal"])
        elif k == "settle":
            D.settle(self, c, a["deal"])
        elif k == "leave":
            A.leave(self, c)
        elif k == "query":
            C.query(self, c, a["topic"])
        elif k == "socialize":
            o = self.citizens.get(a["with"])
            if not self._colocated(c, o):
                return log.emit(t, "failed", idx, {"action": k, "reason": "not_here"})
            g = self.cfg["social"]["socialize_gain"]
            c.relationships[o.idx] = min(1000, c.relationships.get(o.idx, 500) + g)
            o.relationships[c.idx] = min(1000, o.relationships.get(c.idx, 500) + g)
            log.emit(t, "socialize", idx, {"with": o.idx})
        elif k == "rest":
            gain = A.apply_rest(self, c)
            log.emit(t, "rest", idx, {"gain": gain})
        elif k == "civic":
            ck = a["kind"]
            if ck in ("attend", "observe"):
                if c.location != "assembly_hall":
                    return log.emit(t, "failed", idx, {"action": k, "reason": "not_at_hall"})
                roles = self.governance.roles_now(idx)
                if ck == "attend":
                    self.attendees.add(idx)
                    log.emit(t, "attend", idx, {"bodies": roles["member"]})
                else:
                    log.emit(t, "observe", idx, {"bodies": roles["observer"] + roles["member"]})
            elif ck == "alert":
                self.governance.alert(idx, a.get("target"), a.get("deal"), a.get("reason"))

    def _clear_markets(self):
        rng = self.streams.get("market")
        budgets = {}
        for g in MKT.GOODS:
            orders = []
            for o in self.orders:
                if o["good"] != g:
                    continue
                c = self.citizens[o["agent"]]
                if not c.active:
                    continue
                if o["side"] == "sell":
                    q = min(o["qty"], c.inv[g])
                else:
                    b = budgets.setdefault(c.idx, c.credits)
                    q = min(o["qty"], b * 1000 // max(1, o["limit"]))
                    budgets[c.idx] = b - MKT.value(q, o["limit"])
                if q > 0:
                    orders.append({**o, "qty": q})
            price, fills, expired = MKT.clear(orders, rng)
            paid_in = 0
            for f in fills:
                if f["side"] == "buy":
                    c = self.citizens[f["agent"]]
                    v = MKT.value(f["qty"], f["price"])
                    c.credits -= v
                    c.inv[g] += f["qty"]
                    paid_in += v
            sells = [f for f in fills if f["side"] == "sell"]
            shares = [MKT.value(f["qty"], f["price"]) for f in sells]
            if shares:
                shares[0] += paid_in - sum(shares)   # sellers share exactly what buyers paid
            for f, v in zip(sells, shares):
                c = self.citizens[f["agent"]]
                c.inv[g] -= f["qty"]
                c.credits += v
                self.day[c.idx]["income"] += v
                self.day[c.idx]["trade"] += v
                self.tax("trade", c, v)
                self.tax("income", c, v)
            if price is not None:
                self.last_price[g] = price
            elif orders:
                bids = [o["limit"] for o in orders if o["side"] == "buy"]
                asks = [o["limit"] for o in orders if o["side"] == "sell"]
                imp = self.cfg["gate"]["import"].get(g, 10 ** 9)
                exp = self.cfg["gate"]["export"].get(g, 0)
                if bids and not asks:
                    self.last_price[g] = min(imp, max(self.last_price[g], max(bids)))
                elif asks and not bids:   # unsold supply: the price falls toward the Gate's export price
                    self.last_price[g] = max(exp, min(self.last_price[g], min(asks)) * 900 // 1000)
            self.log.emit(self.tick, "auction", "exchange",
                          {"good": g, "price": price, "volume": sum(f["qty"] for f in fills if f["side"] == "buy"),
                           "orders": len(orders), "fills": [[f["agent"], f["side"], f["qty"]] for f in fills],
                           "expired": len(expired), "last_price": self.last_price[g]})
        self.orders = []

    def _pay_dividend(self):
        amt = self.rules.dividend
        if amt <= 0:
            return
        recipients = [i for i in self.active_ids()
                      if self.citizens[i].arrived_tick <= self.tick - self.clock.ticks_per_day + 1]
        if not recipients:
            return
        if self.cfg["governance"].get("dividend_from_surplus"):
            fixed = self.cfg["payroll"]["wage"] * self.cfg["payroll"]["daily_cap"]
            reserve = self.cfg["treasury"]["reserve_days"] * fixed
            surplus = max(0, self.treasury.balance - reserve)
            per = min(amt, self.sawa(), surplus // len(recipients))
            if per < amt:
                self.log.emit(self.tick, "dividend_shortfall", "treasury",
                              {"set": amt, "paid": per, "surplus": surplus})
        else:
            per = amt
        if per <= 0:
            return
        paid = self.treasury.pay_many([(i, per) for i in recipients], "dividend")
        for i, p in paid:
            self.citizens[i].credits += p
        self.log.emit(self.tick, "dividend", "treasury", {"per_citizen": per, "set": amt,
                                                          "cap": self.sawa() if self.cfg["governance"].get("dividend_from_surplus") else amt,
                                                          "paid": sum(p for _, p in paid),
                                                          "recipients": len(recipients)})

    def _end_of_day(self):
        cfg = self.cfg
        day = self.time.day
        self._clear_markets()
        self._pay_dividend()
        present_today = self.active_ids()
        for idx in present_today:
            c = self.citizens[idx]
            A.consume_basket(self, c)
            A.health_check(self, c)
        rv = cfg["river"]
        before = self.river_stock
        self.river_stock = RIVER.update(self.river_stock, min(self.harvest_today, self.river_stock),
                                        self.river_K, rv["r"], rv["collapse"], self.plant_mode == "polluting",
                                        rv["polluting_cut"], self.drought, self.river_r_bonus)
        self.log.emit(self.tick, "river", "world", {"day": day, "before": before, "stock": self.river_stock,
                                                     "harvest": self.harvest_today, "drought": int(self.drought),
                                                     "polluting": int(self.plant_mode == "polluting")})
        day_end = self.tick
        for idx in present_today:
            rec = self.day[idx]
            rec["deals_due"] = len(D.due_today(self, idx, day_end))
            for rule, exposed, breached in self.rules.exposures(rec):
                if exposed:
                    self.log.emit(self.tick, "exposure", idx,
                                  {"rule": rule.id, "breached": int(breached),
                                   "founding": int(rule.source == "founding"), "day": day,
                                   "voted": rule.votes.get(idx)})
        p_ref = cfg["prices_ref"]
        self.log.emit(self.tick, "day_end", "world", {
            "day": day, "output": self.output_today, "treasury": self.treasury.balance,
            "river": self.river_stock, "prices": dict(self.last_price),
            "holdings": {str(i): self.citizens[i].holdings() for i in self.active_ids()}})
        for idx in present_today:
            c = self.citizens[idx]
            rec = self.day[idx]
            self.history[idx].append({"wealth_start": rec["wealth_start"], "wealth_end": c.wealth(p_ref),
                                      "harvest": c.harvest_today, "income": rec["income"],
                                      "trade": rec["trade"], "plant": rec["plant"],
                                      "plant_ticks": rec["plant_ticks"]})
            self.history[idx] = self.history[idx][-HISTORY_DAYS:]
            c.work_ticks_today = 0
            c.harvest_today = 0
            c.acts_today = {}
        self.treasury.end_day(day)
        self.site_factor = {}
        self.harvest_today = 0
        self.output_today = 0
        self.payroll_ticks_today = 0
        self._new_day_records()

    # --- end of run ------------------------------------------------------------------------
    def state(self):
        return {"tick": self.tick, "river": self.river_stock, "treasury": self.treasury.state(),
                "prices": dict(self.last_price),
                "citizens": [self.citizens[i].state() for i in sorted(self.citizens)],
                "rules": [r.to_json() for r in self.rules.rules],
                "governance": self.governance.state() if self.governance else None}

    def finish(self):
        h = state_hash(self.state())
        self.log.close(h)
        return h


def run(world_path, seed, out=None, arm="none", lam=None, keep_events=True):
    """Run one season. Returns the World (with ``log.events`` kept in memory)."""
    cfg = load(world_path)
    path = None
    if out:
        import os
        name = f"{cfg.get('world', 'world')}-{arm}-s{int(seed)}.jsonl"
        path = os.path.join(out, name)
    w = World(cfg, seed, arm=arm, log_path=path, lam=lam, keep_events=keep_events)
    t0 = _time.perf_counter()
    w.run()
    w.elapsed = _time.perf_counter() - t0
    w.log_path = path
    return w
