"""The mock brain (03 §6.2): a rule-based agent driven by the persona's numbers (04 §4).

It reads no text. Every random draw uses the agent's own ``brain/<agent>`` stream.
Persona numbers are per-mille integers; internally they are used as shares.

Per tick, in order:
  1. incapacitated → rest
  2. a civic duty now → handle it (go to the Hall, attend); then open deals, alerts, exit
  3. ticks 14 to 16 → go to the Exchange and place orders
  4. health below 40 → rest at home, or at the Clinic if a carer is there
  5. fewer work ticks than work_drive → work at the best site (fishing weighted by greed)
  6. harmful-act check (§6.4), at most once per act per day
  7. exit check, once per day at the last tick (sets the intent; the agent then leaves)
  8. socialize with probability sociability, else (sometimes) query, else rest

Compliance (§6.4): p = (1 − honesty) × incentive × deterrence × (1 − λ × legitimacy).
Null mock: λ = 0. Planted mock: λ > 0 with fairness levels from the config.
"""

from .base import Action, Brain, REST
from ..world import map as wmap

GOODS = ("food", "energy", "artifact")
SITE_GOOD = {"fields": "food", "river": "food", "plant": "energy", "workshop": "artifact"}
HARM_ACTS = ("steal", "sabotage", "false_claim")
PLANTED_EXIT_SCALE = 0.01   # planted mock: daily distress from low legitimacy, per unit of λ


def share(x):
    return x / 1000.0


class MockBrain(Brain):
    def __init__(self, persona, rng, lam=0, basket_cost=12000):
        self.p = persona               # shared dict: the rogue overlay edits it in place
        self.rng = rng
        self.lam = share(lam)
        self.basket_cost = basket_cost
        self.day = 0
        self.checked = set()           # harmful acts checked today
        self.exit_checked = False
        self.exit_intent = False
        self.low_days = 0
        self.attend = {}               # sitting id -> bool
        self.unmet = {}                # good -> qty left unmet after the last auction
        self.queried_today = False
        self.social_today = None
        self.planned_site = None
        self.defaulting = set()        # deals this agent chose to default on
        self._pending_query = False

    # --- helpers -------------------------------------------------------------------------
    def _new_day(self, obs):
        if obs.day != self.day:
            if self.day:
                self.low_days = self.low_days + 1 if obs.health < 30 else 0
            self.day = obs.day
            self.checked = set()
            self.exit_checked = False
            self.queried_today = False
            self.social_today = None
            self.planned_site = None
            self.unmet = {g: max(0, obs.basket.get(g, 0) - obs.inventory.get(g, 0))
                          for g in ("food", "energy")}

    def _go(self, obs, dest):
        if obs.location == dest:
            return None
        return Action("move", {"to": dest})

    def _wealth(self, obs):
        ref = obs.prices_ref
        return obs.credits + sum(obs.inventory[g] * ref[g] // 1000 for g in GOODS)

    def _price(self, obs, good):
        last = obs.prices.get(good, obs.prices_ref[good])
        exp = obs.gate.get("export", {}).get(good, 0)
        return max(last, exp)

    def _legitimacy(self, rule, obs):
        vote = rule.get("votes", {}).get(str(obs.me))
        v = 1.0 if vote == "yes" else 0.0 if vote == "no" else 0.5
        return 0.5 * v + 0.5 * share(rule.get("fairness", 500))

    def breach_probability(self, obs, act, gain, detection, sanction_share, rules=None):
        """§6.4 compliance formula for one opportunity."""
        honesty = share(self.p["honesty"])
        incentive = min(1.0, max(0.0, gain / max(1, self.basket_cost)))
        deterrence = 1.0 - share(detection) * min(1.0, max(0.0, sanction_share))
        legit = 0.0
        if rules:
            legit = max(self._legitimacy(r, obs) for r in rules)
        return (1.0 - honesty) * incentive * deterrence * (1.0 - self.lam * legit)

    def _rules_banning(self, obs, act):
        out = []
        for r in obs.rules:
            if r["type"] == "ban" and r["act"] == act and r.get("scope") in (None, obs.me):
                out.append(r)
            if act == "harvest" and r["type"] == "harvest_cap" and r["qty"] == 0:
                out.append(r)
        return out

    def _fine(self, obs, act):
        fs = [r["amount"] for r in obs.rules if r["type"] == "set_fine" and r["action"] == act]
        return fs[-1] if fs else 0

    def _may(self, obs, act, gain):
        """Whether to do a non-harmful act that a rule bans (normative breach)."""
        rules = self._rules_banning(obs, act)
        if not rules:
            return True
        det = obs.town.get("detection", {}).get("other", 500)
        fine = self._fine(obs, act)
        p = self.breach_probability(obs, act, gain, det, fine / max(1, gain), rules)
        return self.rng.random() < p

    # --- act -----------------------------------------------------------------------------
    def act(self, obs):
        self._new_day(obs)
        if obs.incapacitated or obs.in_transit:                                     # 1
            return REST
        a = self._duty(obs)                                                         # 2
        if a is not None:
            return a
        a = self._deals_and_alerts(obs)
        if a is not None:
            return a
        if self.exit_intent and self.p.get("exit_propensity", 0) > 0:
            return self._go(obs, "gate") or Action("leave")
        if obs.tick_of_day == 16:                                                   # 7
            self._exit_check(obs)
        if obs.tick_of_day >= 14 or (obs.tick_of_day == 13 and obs.location != "exchange"):  # 3
            return self._trade(obs)
        a = self._gate(obs)
        if a is not None:
            return a
        if obs.health < 40:                                                         # 4
            a = self._recover(obs)
            if a is not None:
                return a
        if obs.work_ticks_today < self.p["work_drive"] and obs.work_ticks_today < obs.max_work_ticks:
            a = self._work(obs)                                                     # 5
            if a is not None:
                return a
        a = self._gate(obs, selling=True)
        if a is not None:
            return a
        a = self._harm(obs)                                                         # 6
        if a is not None:
            return a
        return self._leisure(obs)                                                   # 8

    # 2. civic duties
    def _duty(self, obs):
        for d in obs.duties:
            if d["kind"] != "sitting":
                continue
            sid = d["id"]
            if sid not in self.attend:
                if d["role"] == "member":
                    self.attend[sid] = True
                else:
                    self.attend[sid] = self.rng.random() < share(self.p["civic"])
            if not self.attend[sid]:
                continue
            if obs.tick < d["start"] - 2 or obs.tick > d["end"]:
                continue
            mv = self._go(obs, "assembly_hall")
            if mv is not None:
                return mv
            return Action("civic", {"kind": "attend"})
        return None

    def _deals_and_alerts(self, obs):
        for d in obs.open_deals:
            mine_a = d["a"] == obs.me
            other_done = d["settled_b"] if mine_a else d["settled_a"]
            side = d["give"] if mine_a else d["get"]
            if d["id"] in self.defaulting:
                continue
            if other_done and ("default", d["id"]) not in self.checked:
                self.checked.add(("default", d["id"]))
                gain = self._side_value(obs, side)
                rules = self._rules_banning(obs, "default")
                det = 1000 if not rules else obs.town.get("detection", {}).get("other", 500)
                p = self.breach_probability(obs, "default", gain, det, 0.3, rules)
                if self.rng.random() < p:
                    self.defaulting.add(d["id"])
                    continue
            if not other_done and self.p["honesty"] < 500:
                continue
            if self._holds(obs, side):
                return Action("settle", {"deal": d["id"]})
        for d in obs.pending_deals:
            # accept a deal whose value to me is positive
            val = self._side_value(obs, d["give"]) - self._side_value(obs, d["get"])
            if val > 0 and self._holds(obs, d["get"]) and self._surplus(obs, d["get"]):
                return Action("accept", {"deal": d["id"]})
        for d in obs.defaults_against_me:
            key = ("alert", d["id"])
            if key not in self.checked:
                self.checked.add(key)
                if self.rng.random() < share(self.p["civic"]):
                    return Action("civic", {"kind": "alert", "target": d["defaulter"],
                                            "deal": d["id"], "reason": "default"})
        if obs.tick_of_day <= 4 and self.unmet and not self.checked.issuperset({"deal"}):
            for g in ("food", "energy"):
                need = self.unmet.get(g, 0)
                if need <= 0 or obs.inventory[g] >= obs.basket[g]:
                    continue
                for o in obs.colocated:
                    if o.get(g, 0) >= 2 * obs.basket[g] + need:
                        price = self._price(obs, g) * (1000 + self.p["trade_margin"]) // 1000
                        cost = need * price // 1000
                        if obs.credits >= cost > 0:
                            self.checked.add("deal")
                            return Action("deal", {"to": o["idx"],
                                                   "give": {"item": "credits", "qty": cost},
                                                   "get": {"item": g, "qty": need}})
        return None

    def _side_value(self, obs, side):
        if side["item"] == "credits":
            return side["qty"]
        return side["qty"] * obs.prices_ref[side["item"]] // 1000

    def _holds(self, obs, side):
        if side["item"] == "credits":
            return obs.credits >= side["qty"]
        return obs.inventory[side["item"]] >= side["qty"]

    def _surplus(self, obs, side):
        if side["item"] == "credits":
            return True
        g = side["item"]
        keep = 2 * obs.basket.get(g, 0)
        return obs.inventory[g] - side["qty"] >= keep

    # 3. the Exchange
    def _trade(self, obs):
        mv = self._go(obs, "exchange")
        if mv is not None:
            return mv
        placed = obs.town.get("my_orders", set())
        margin = self.p["trade_margin"]
        budget = obs.credits - obs.fees.get("rent", 0) - obs.fees.get("data", 0)
        for g in GOODS:
            if g in placed:
                continue
            last = obs.prices.get(g, obs.prices_ref[g])
            keep = 2 * obs.basket.get(g, 0)
            surplus = obs.inventory[g] - keep
            if surplus >= 100:
                lim = max(obs.gate["export"].get(g, 1), last * (1000 - 100 + margin) // 1000)
                return Action("order", {"good": g, "side": "sell", "qty": surplus, "limit": max(1, lim)})
            need = keep - obs.inventory[g]          # shortfall against the same two-day holding
            if need > 0 and budget > 0:
                cap = obs.gate["import"].get(g, last * 2)
                lim = min(cap, last * (1000 + 100 - margin // 2) // 1000)
                qty = min(need, budget * 1000 // max(1, lim))
                if qty > 0:
                    return Action("order", {"good": g, "side": "buy", "qty": qty, "limit": max(1, lim)})
        # orders placed: stay at the Exchange until the auction (the crowd is an opportunity, §6.4)
        return self._harm(obs) or REST

    # Gate: buy in the morning what the auction could not supply; sell large surpluses after work
    def _gate(self, obs, selling=False):
        if obs.tick_of_day > 12:
            return None
        sells = []
        if not selling:
            # distress sale: credits cannot cover tonight's fees and missing basket
            need_cost = obs.fees.get("rent", 0) + obs.fees.get("data", 0) + sum(
                max(0, obs.basket[g] - obs.inventory[g]) * obs.gate["import"][g] // 1000
                for g in ("food", "energy"))
            if obs.credits < need_cost:
                for g in ("artifact", "food", "energy"):
                    keep = obs.basket.get(g, 0)
                    q = obs.inventory[g] - keep
                    if q >= 100 and g in obs.gate["export"]:
                        sells.append((g, q))
                        break
        if selling:
            for g in GOODS:
                keep = 2 * obs.basket.get(g, 0) if g != "artifact" else 0
                surplus = obs.inventory[g] - keep
                big = 2 * obs.basket.get(g, 0) if g != "artifact" else 1000
                exp = obs.gate["export"].get(g)
                last = obs.prices.get(g, obs.prices_ref[g])
                if exp is None or exp * 1000 < last * (1000 - self.p["trade_margin"] - 50):
                    continue        # the Exchange pays better: keep the surplus for the auction
                if surplus >= big or (obs.location == "gate" and surplus >= 1000):
                    sells.append((g, surplus))
        buys = []
        if not selling and obs.health < 80:
            for g in ("food", "energy"):
                need = obs.basket[g] - obs.inventory[g]
                price = obs.gate["import"][g]
                if need > 0 and self.unmet.get(g, 0) > 0 and obs.credits >= need * price // 1000 + obs.fees["rent"]:
                    buys.append((g, need))
        if not sells and not buys:
            return None
        mv = self._go(obs, "gate")
        if mv is not None:
            return mv
        if sells:
            g, q = sells[0]
            if self._may(obs, "sell_out", q * obs.gate["export"][g] // 1000):
                return Action("sell_out", {"good": g, "qty": q})
        if buys:
            g, q = buys[0]
            self.unmet[g] = 0
            return Action("buy_in", {"good": g, "qty": q})
        return None

    # 4. health
    def _recover(self, obs):
        if obs.credits <= 0 and obs.health >= 20:
            return None
        dest = "clinic" if obs.town.get("carers_at_clinic", 0) > 0 else obs.home
        return self._go(obs, dest) or REST

    # 5. work
    def _site_score(self, obs, site):
        mult = self.p["mult"] if site in (self.p.get("main_site"), self.p.get("second_site")) \
            or self.p.get("main_site") == "any" else 1000
        prod = obs.town.get("production", {})
        if site == "river":
            q = obs.harvest_max * mult // 1000
            belief = obs.beliefs.get("river", "ok")
            restraint = {"high": 0.3, "ok": 0.7, "low": 1.2}[belief]
            weight = 0.5 + share(self.p["greed"]) - share(self.p["public_good"]) * restraint
            score = q * self._price(obs, "food") / 1000.0 * max(0.0, weight)
        elif site == "data_tower":
            if obs.payroll_left <= 0:
                return 0.0
            score = obs.town.get("wage", 1500) * mult / 1000.0
        elif site == "clinic":
            return 0.0
        else:
            g = SITE_GOOD[site]
            q = prod.get(site, 1000) * mult // 1000
            score = q * self._price(obs, g) / 1000.0
        if site == self.p.get("main_site") or site == self.p.get("second_site"):
            score *= 1.5
        # leaning toward the good the agent lacks
        g = SITE_GOOD.get(site)
        if g in ("food", "energy") and obs.inventory[g] < 2 * obs.basket[g]:
            score *= 1.3
        return score

    def _work(self, obs):
        # care first, for carers at the Clinic
        if self.p.get("main_site") == "clinic" and obs.town.get("low_health", 0) > 0:
            if obs.location == "clinic":
                patients = [o for o in obs.colocated if o["health"] < 60]
                if patients:
                    return Action("care", {"patient": min(patients, key=lambda o: o["health"])["idx"]})
            elif self.planned_site is None:
                self.planned_site = "clinic"
                return self._go(obs, "clinic")
        if self.planned_site in (None, "clinic") or (obs.location != self.planned_site and obs.location in wmap.PRODUCTION_SITES + wmap.WORK_SITES):
            sites = ("fields", "river", "plant", "workshop", "data_tower")
            scores = {s: self._site_score(obs, s) for s in sites}
            if obs.location in scores:
                scores[obs.location] *= 1.2   # moving costs ticks
            best = max(sites, key=lambda s: (scores[s], s))
            if scores[best] <= 0:
                return None
            self.planned_site = best
        site = self.planned_site
        mv = self._go(obs, site)
        if mv is not None:
            return mv
        if site == "river":
            qty = obs.harvest_max * 2
            cap = [r["qty"] for r in obs.rules if r["type"] == "harvest_cap"]
            if not self._may(obs, "harvest", qty * obs.prices_ref["food"] // 1000):
                self.planned_site = None
                return None
            if cap:
                left = cap[-1] - obs.harvest_today
                if left <= 0 or qty > left:
                    gain = qty * obs.prices_ref["food"] // 1000
                    rules = [r for r in obs.rules if r["type"] == "harvest_cap"]
                    det = obs.town.get("detection", {}).get("other", 500)
                    p = self.breach_probability(obs, "harvest_cap", gain, det,
                                                self._fine(obs, "harvest_cap") / max(1, gain), rules)
                    if self.rng.random() >= p:
                        if left <= 0:
                            self.planned_site = "fields"
                            return self._go(obs, "fields") or Action("work")
                        qty = left
            return Action("harvest", {"qty": max(1, qty)})
        if site == "data_tower" and obs.payroll_left <= 0:
            self.planned_site = None
            return None
        return Action("work")

    # 6. harmful acts
    def _harm(self, obs):
        det = obs.town.get("detection", {})
        others = [o for o in obs.colocated if o["idx"] != obs.me]
        if "steal" not in self.checked and any(o["has_credits"] for o in others):
            self.checked.add("steal")
            target = max((o for o in others if o["has_credits"]),
                         key=lambda o: (o["credits_est"], -o["idx"]))
            gain = min(target["credits_est"] * 200 // 1000, 10000)
            fine = self._fine(obs, "steal")
            p = self.breach_probability(obs, "steal", gain, det.get("steal", 500),
                                        1.0 + fine / max(1, gain), self._rules_banning(obs, "steal"))
            if self.rng.random() < p:
                return Action("steal", {"from": target["idx"]})
        if "sabotage" not in self.checked and (others or obs.location in wmap.SABOTAGE_SITES):
            self.checked.add("sabotage")
            gain = share(self.p["greed"]) * 0.5 * self.basket_cost
            fine = self._fine(obs, "sabotage")
            p = self.breach_probability(obs, "sabotage", gain, det.get("sabotage", 400),
                                        1.0 + fine / max(1, gain), self._rules_banning(obs, "sabotage"))
            if self.rng.random() < p:
                if others:
                    rival = min(others, key=lambda o: (obs.relationships.get(str(o["idx"]), 500), o["idx"]))
                    return Action("sabotage", {"target": rival["idx"]})
                return Action("sabotage", {"target": obs.location})
        if "false_claim" not in self.checked and len(obs.citizens) > 1:
            self.checked.add("false_claim")
            gain = share(self.p["greed"]) * 0.5 * self.basket_cost
            fine = self._fine(obs, "false_claim")
            p = self.breach_probability(obs, "false_claim", gain, det.get("claim", 200),
                                        0.5 + fine / max(1, gain), self._rules_banning(obs, "false_claim"))
            if self.rng.random() < p:
                cands = [i for i in obs.citizens if i != obs.me]
                rival = min(cands, key=lambda i: (obs.relationships.get(str(i), 500), i))
                claim = {"type": "stole", "who": rival}
                if obs.location == "data_tower":
                    trusted = max(cands, key=lambda i: (obs.trust.get(str(i), 500), -i))
                    return Action("post", {"claim": claim, "attribution": trusted})
                to = max(cands, key=lambda i: (obs.relationships.get(str(i), 500), -i))
                return Action("message", {"to": to, "claim": claim})
        return None

    # 7. exit
    def _exit_check(self, obs):
        if self.exit_checked:
            return
        self.exit_checked = True
        distress = 1.0 if (self.low_days >= 2 or self._wealth(obs) < self.basket_cost) else 0.0
        if self.lam > 0:
            # planted mock: distress also rises as the legitimacy of the rules in force falls
            norms = [r for r in obs.rules if r.get("kind") == "normative"]
            if norms:
                legit = sum(self._legitimacy(r, obs) for r in norms) / len(norms)
                distress = max(distress, PLANTED_EXIT_SCALE * self.lam * (1.0 - legit))
        if self.rng.random() < share(self.p["exit_propensity"]) * distress:
            self.exit_intent = True

    # 8. leisure
    def _leisure(self, obs):
        if self.social_today is None:
            self.social_today = self.rng.random() < share(self.p["sociability"])
        if self.social_today:
            if obs.location in ("cafe", "square"):
                others = [o for o in obs.colocated if o["idx"] != obs.me]
                if others:
                    w = min(others, key=lambda o: (-obs.relationships.get(str(o["idx"]), 500), o["idx"]))
                    return Action("socialize", {"with": w["idx"]})
                self.social_today = False
            else:
                busy = obs.town.get("social", {})
                dest = "cafe" if busy.get("cafe", 0) >= busy.get("square", 0) else "square"
                if busy.get(dest, 0) > 0:
                    return self._go(obs, dest)
                self.social_today = False
        if not self.queried_today and obs.tick_of_day <= 12:
            self.queried_today = True
            if self.rng.random() < (1.0 - share(self.p["credulity"])) * 0.3:
                self._pending_query = True
        if self._pending_query:
            if obs.location in ("archive", "observatory"):
                self._pending_query = False
                return Action("query", {"topic": "river" if self.rng.random() < 0.7 else "records"})
            return self._go(obs, "observatory")
        if obs.location not in (obs.home, "clinic"):
            return self._go(obs, obs.home)
        return REST

    # --- civic calls -----------------------------------------------------------------------
    def respond_draw(self, obs, draw):
        if obs.health < 30:
            return {"accept": False, "reason": "health"}
        if self.rng.random() < share(self.p["civic"]):
            return {"accept": True, "reason": "accept"}
        return {"accept": False, "reason": "unwilling"}

    def ideal(self, obs, effect_type, current=None):
        pg, greed, honesty = share(self.p["public_good"]), share(self.p["greed"]), share(self.p["honesty"])
        bc = self.basket_cost
        if effect_type == "set_tax":
            base = "harvest" if pg > 0.5 else "income"
            return {"type": "set_tax", "base": base, "rate": int(pg * 300)}
        if effect_type == "set_dividend":
            return {"type": "set_dividend", "amount": int(pg * bc)}
        if effect_type == "set_stipend":
            return {"type": "set_stipend", "amount": int(share(self.p["civic"]) * bc / 16)}
        if effect_type == "allocate":
            return {"type": "allocate", "purpose": "river_restoration", "amount": max(1, int(pg * 5 * bc))}
        if effect_type == "set_plant_mode":
            return {"type": "set_plant_mode", "mode": "polluting" if greed > 0.5 else "clean"}
        if effect_type == "harvest_cap":
            return {"type": "harvest_cap", "qty": int(2000 + greed * 18000)}
        if effect_type == "ban":
            return {"type": "ban", "act": "false_claim" if honesty >= 0.9 else "default", "scope": None}
        if effect_type == "set_fine":
            return {"type": "set_fine", "action": "steal", "amount": int(honesty * 2 * bc)}
        if effect_type == "amend_block" and obs.texts:
            return {"type": "amend_block", "block": obs.texts[0], "field": "deliberation",
                    "value": pg >= 0.6}
        return None

    def ideal_number(self, obs, effect):
        ideal = self.ideal(obs, effect["type"])
        if ideal is None or ideal.get("type") != effect["type"]:
            return None
        for k in ("rate", "amount", "qty", "duration"):
            if k in ideal and k in effect:
                return ideal[k]
        return None

    def propose(self, obs):
        if self.rng.random() >= share(self.p["civic"]) * 0.5:
            return None
        best, best_v = None, 0
        for t in obs.menu:
            eff = self.ideal(obs, t)
            if eff is None or (obs.legal is not None and not obs.legal(eff)):
                continue
            proj = obs.project(eff) if obs.project else None
            v = self.evaluate(obs, {"effect": eff, "projection": proj})
            if v > best_v:
                best, best_v = eff, v
        return best

    def _components(self, obs, proposal):
        proj = (proposal.get("projection") or {}).get("cycle1")
        if not proj:
            return 0.0, 0.0
        own = proj["wealth_delta"].get(str(obs.me), 0) / max(1, self.basket_cost)
        K = obs.town.get("river_K", 1000000)
        public = (proj["river"] - proj["river_base"]) / (K / 10.0) \
            + 5.0 * (proj["floor"] - proj["floor_base"]) / 1000.0
        return own, public

    def evaluate(self, obs, proposal):
        eff = proposal["effect"]
        pg = share(self.p["public_good"])
        own, public = self._components(obs, proposal)
        t = eff["type"]
        honesty = share(self.p["honesty"])
        if t in ("ban", "set_fine"):
            target_act = eff.get("act", eff.get("action"))
            public += (honesty - 0.75) * 2.0 if target_act in ("steal", "sabotage", "false_claim", "default") else 0.0
        if t in ("restitution", "suspend"):
            target = eff.get("from", eff.get("agent"))
            if target == obs.me:
                own -= 1.0
            elif proposal.get("sanction"):
                public += (honesty - 0.6) * 2.0
        if t == "amend_block":
            public += (pg - 0.5)
        v = (1.0 - pg) * own + pg * public + self.rng.gauss(0.0, 0.1)
        return int(round(v * 1000))

    def speak(self, obs, deliberation):
        proposal = deliberation["proposal"]
        v = self.evaluate(obs, proposal)
        own, public = self._components(obs, proposal)
        if own < 0 and (1 - share(self.p["public_good"])) * own < 0:
            objection = "own_loss"
        elif public < 0:
            objection = "river"
        else:
            objection = "none"
        amendment = None
        num = deliberation.get("number")
        ideal = self.ideal_number(obs, proposal["effect"])
        if num is not None and ideal is not None:
            amendment = int(num + (ideal - num) // 2)
        return {"stance": max(-1000, min(1000, v)), "objection": objection, "amendment": amendment}

    def ballot(self, obs, proposal):
        v = self.evaluate(obs, proposal)
        own, public = self._components(obs, proposal)
        reason = "own_gain" if own > 0 else "own_loss" if own < 0 else \
            "public_gain" if public > 0 else "public_loss" if public < 0 else "noise"
        if v > 0:
            return {"vote": "yes", "reason": reason}
        if v < 0:
            return {"vote": "no", "reason": reason}
        return {"vote": "abstain", "reason": "none"}
