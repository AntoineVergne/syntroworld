"""Procedural blocks and the sittings that run them (02 §1, §4, §5, §8).

A block is YAML validated against ``schemas/procedural-block.schema.json``. The
``Governance`` service keeps the Register of Proposals, draws standing bodies, opens
sittings on schedule, runs their phases tick by tick (examination, deliberation,
Advocates, vote, publication) and puts decided effects in force.
"""

import copy
import json
import os

import jsonschema

from ..config import SCHEMA_DIR, load_yaml, resolve_path
from ..brains.base import (validate_ballot, validate_draw_response, validate_evaluation,
                           validate_speech)
from . import advocates as ADV
from . import deliberation as DL
from . import effects as E
from . import kleroterion as K

DEFAULT_PHASES = {"information": 1, "debate": 2, "dialogue": 2}
KILL_SWITCH_ACTIONS = ["steal", "sabotage", "post", "message", "deal"]
PROPOSAL_LIFETIME_CYCLES = 2

_VALIDATOR = None


def block_validator():
    global _VALIDATOR
    if _VALIDATOR is None:
        with open(os.path.join(SCHEMA_DIR, "procedural-block.schema.json"), encoding="utf-8") as fh:
            schema = json.load(fh)
        cls = jsonschema.validators.validator_for(schema)
        cls.check_schema(schema)
        _VALIDATOR = cls(schema)
    return _VALIDATOR


class BlockError(ValueError):
    pass


def validate_block(block):
    e = jsonschema.exceptions.best_match(block_validator().iter_errors(block))
    if e is not None:
        where = "/".join(str(p) for p in e.absolute_path) or "(root)"
        raise BlockError(f"invalid block {block.get('id')!r} at {where}: {e.message}")
    types = [s["type"] for s in block["steps"]]
    if types[-1] != "publication":
        raise BlockError(f"block {block['id']}: must end with publication")
    if "vote" not in types:
        raise BlockError(f"block {block['id']}: needs a vote step")
    if "market" in types:
        raise BlockError(f"block {block['id']}: market steps are reserved, not implemented")
    return block


def load_block(path):
    return validate_block(load_yaml(path))


def step(block, type_):
    for s in block["steps"]:
        if s["type"] == type_:
            return s
    return None


def classes(block):
    return block.get("classes") or [block["decision_class"]]


def body_name(block):
    b = block["body"]
    if isinstance(b, str):
        return b
    if b["type"] == "panel":
        return f"panel:{block['id']}"
    return f"fresh:{block['id']}"


class Governance:
    def __init__(self, w):
        self.w = w
        g = w.cfg["governance"]
        self.g = g
        self.blocks = {}
        self.order = []
        for rel in g["blocks"]:
            b = load_block(resolve_path(w.cfg, rel))
            if b["id"] in self.blocks:
                raise BlockError(f"duplicate block id {b['id']}")
            self.blocks[b["id"]] = b
            self.order.append(b["id"])
        self.bodies = g.get("bodies", {})
        self.advocates = list(g.get("advocates", []))
        self.agenda_cfg = g["agenda"]
        self.register = []
        self._pid = 1
        self._sid = 1
        self.sittings = []           # scheduled or open
        self.members = {}            # body -> members this cycle
        self.pending_amendments = []
        self.alerts_today = {}
        self.kill_switch_cycle = {}  # target -> cycle convened
        self.detected = []           # (tick, act, agent, payload)
        self.adjudicated = set()
        self.harm_detected_today = {}
        self.sitting_counts = {}
        self.block_versions = {bid: 1 for bid in self.order}

    # --- helpers -------------------------------------------------------------------------
    @property
    def log(self):
        return self.w.log

    def fairness(self, block):
        """Declared fairness of a procedure, used only by the planted mock (03 §6.4).

        With a ``brain.fairness`` map in the config, the level follows the procedure's
        features: wealth-weighted votes, a drawn body (sortition, with or without
        deliberation), or a plenary. Otherwise the block's own ``fairness_level``.
        """
        fmap = self.w.cfg.get("brain", {}).get("fairness")
        if not fmap:
            return block.get("fairness_level", 500)
        vote = step(block, "vote") or {}
        if vote.get("weights") == "wealth":
            return fmap["wealth_weighted"]
        if block["body"] != "plenary":
            return fmap["deliberation_sortition"]
        return fmap["plenary"]

    def primary_block(self):
        return self.blocks[self.order[0]]

    def route(self, effect):
        cls = E.DECISION_CLASS[effect["type"]]
        for bid in self.order:
            b = self.blocks[bid]
            if isinstance(b["body"], dict) and b["body"]["type"] == "fresh_panel":
                continue
            if cls in classes(b):
                return b
        return None

    def projection(self, effect):
        return self.w.projection(effect)

    def proposal_view(self, item):
        return {"id": item["id"], "effect": item["effect"], "projection": self.projection(item["effect"]),
                "sanction": item.get("sanction", False), "author": item.get("author")}

    # --- brain calls (validated and logged) ------------------------------------------------
    def evaluate(self, idx, item, phase="evaluation"):
        obs = self.w.observe(idx)
        raw = self.w.brains[idx].evaluate(obs, self.proposal_view(item))
        v, err = validate_evaluation(raw)
        if err:
            self.log.emit(self.w.tick, "invalid_output", idx, {"call": "evaluate", "reason": err})
        self.log.emit(self.w.tick, "evaluation", idx, {"proposal": item["id"], "value": v, "phase": phase})
        item.setdefault("logged_eval", {})[idx] = v
        return v

    def speak(self, idx, item, phase):
        obs = self.w.observe(idx)
        num = DL._primary(item["effect"])
        raw = self.w.brains[idx].speak(obs, {"proposal": self.proposal_view(item), "number": num,
                                             "phase": phase})
        sp, err = validate_speech(raw)
        if err:
            self.log.emit(self.w.tick, "invalid_output", idx, {"call": "speak", "reason": err})
        self.log.emit(self.w.tick, "speech", idx, {"proposal": item["id"], "phase": phase, **sp})
        return sp

    def ballot(self, idx, item, weight):
        obs = self.w.observe(idx)
        raw = self.w.brains[idx].ballot(obs, self.proposal_view(item))
        b, err = validate_ballot(raw)
        if err:
            self.log.emit(self.w.tick, "invalid_output", idx, {"call": "ballot", "reason": err})
        self.log.emit(self.w.tick, "ballot", idx, {"proposal": item["id"], "vote": b["vote"],
                                                   "reason": b["reason"], "weight": weight,
                                                   "round": item.get("round", 1)})
        return b

    # --- the Register of Proposals ---------------------------------------------------------
    def examine(self, effect, block):
        st = step(block, "examination")
        criteria = st["criteria"] if st else ["within_legal_range"]
        if "within_legal_range" in criteria:
            err = E.check(effect, self.w.cfg)
            if err:
                return err
        if "not_duplicate" in criteria:
            k = E.key(effect)
            if self.w.rules.is_duplicate(effect) or any(
                    E.key(p["effect"]) == k for p in self.register if p["status"] in ("admissible", "on_agenda")):
                return "duplicate"
        if "within_compact" in criteria:
            sawa = self.w.sawa()
            t = effect["type"]
            if t == "set_dividend" and effect["amount"] > sawa:
                return "dividend above one Sawa"
            if t == "set_fine" and effect["amount"] > 2 * sawa:
                return "fine above 2 Sawa"
            if t == "restitution" and effect["to"] == "treasury" and effect["amount"] > 2 * sawa:
                return "fine above 2 Sawa"
        return None

    def register_proposal(self, author, effect, sanction=False, mandatory=False, urgent=False, reason=None):
        pid = f"P{self._pid}"
        self._pid += 1
        block = self.route(effect) if isinstance(effect, dict) and effect.get("type") in E.KIND else None
        if block is None:
            err = "no block for this decision class"
        else:
            err = self.examine(effect, block)
        status = "rejected" if err else "admissible"
        item = {"id": pid, "author": author, "effect": copy.deepcopy(effect), "tick": self.w.tick,
                "cycle": self.w.time.cycle, "status": status, "block": block["id"] if block else None,
                "sanction": sanction, "mandatory": mandatory, "urgent": urgent}
        self.log.emit(self.w.tick, "proposal_registered", author,
                      {"id": pid, "effect": item["effect"] if isinstance(effect, dict) else {},
                       "admissible": int(not err), "reason": err, "block": item["block"],
                       "sanction": int(sanction), "mandatory": int(mandatory), "urgent": int(urgent),
                       "origin": reason})
        if not err:
            self.register.append(item)
        return item

    def collect_proposals(self):
        """``propose`` is called at most once per cycle per citizen (03 §6.1)."""
        for idx in self.w.active_ids():
            c = self.w.citizens[idx]
            if c.incapacitated:
                continue
            obs = self.w.observe(idx)
            eff = self.w.brains[idx].propose(obs)
            if eff is None:
                continue
            if not isinstance(eff, dict):
                self.log.emit(self.w.tick, "invalid_output", idx, {"call": "propose", "reason": "not_a_dict"})
                continue
            self.register_proposal(idx, eff)

    # --- cycle start: amendments, proposals, draws ------------------------------------------
    def on_cycle_start(self):
        w = self.w
        for item, _block in self.pending_amendments:
            self.apply_amendment(item["effect"], item["id"])
        self.pending_amendments = []
        cyc = w.time.cycle
        for p in self.register:
            if p["status"] == "admissible" and p["cycle"] <= cyc - PROPOSAL_LIFETIME_CYCLES:
                p["status"] = "expired"
                self.log.emit(w.tick, "proposal_expired", None, {"id": p["id"]})
        self.register = [p for p in self.register if p["status"] in ("admissible", "on_agenda")]
        self.collect_proposals()
        self.draw_bodies()
        self.schedule_sittings()

    def eligible_pool(self):
        w = self.w
        tpc = w.clock.ticks_per_cycle
        out = []
        for idx in w.active_ids():
            c = w.citizens[idx]
            if c.incapacitated:
                continue
            if any(r.effect["agent"] == idx for r in w.rules.suspensions()):
                continue
            founder = c.arrived_tick == 1
            if not founder and c.arrived_tick > w.tick - tpc:
                continue
            out.append(idx)
        return out

    def standing_bodies(self):
        """(name, size, sitting, strata) for bodies drawn at the start of each cycle."""
        out = []
        for name, b in self.bodies.items():
            out.append((name, b["size"], b["sitting"], b.get("strata", "none")))
        for bid in self.order:
            blk = self.blocks[bid]
            if isinstance(blk["body"], dict) and blk["body"]["type"] == "panel":
                out.append((body_name(blk), blk["body"]["size"], blk["sitting"], "none"))
        return out

    def _respond(self, body, size):
        def respond(idx):
            obs = self.w.observe(idx)
            raw = self.w.brains[idx].respond_draw(obs, {"body": body, "size": size})
            r, err = validate_draw_response(raw)
            if err:
                self.log.emit(self.w.tick, "invalid_output", idx, {"call": "respond_draw", "reason": err})
            self.log.emit(self.w.tick, "draw_response", idx, {"body": body, "accept": int(r["accept"]),
                                                              "reason": r["reason"]})
            return r["accept"], r["reason"]
        return respond

    def draw_bodies(self):
        w = self.w
        cyc = w.time.cycle
        self.members = {}
        taken = set()
        for name, size, _sitting, strata in self.standing_bodies():
            pool = [i for i in self.eligible_pool() if i not in taken]
            weights = {i: 500 if w.citizens[i].served.get(name) == cyc - 1 else 1000 for i in pool}
            st = None
            if strata == "wealth_tercile":
                wealth = {i: w.citizens[i].wealth(w.cfg["prices_ref"]) for i in pool}
                st = K.terciles(pool, wealth)
            res = K.draw(w.streams.get("kleroterion"), pool, size, weights,
                         respond=self._respond(name, size), strata=st, log=w.log, tick=w.tick, body=name)
            self.members[name] = list(res["members"])
            for i in res["members"]:
                w.citizens[i].served[name] = cyc
                taken.add(i)

    def schedule_sittings(self):
        w = self.w
        cyc = w.time.cycle
        plan = []
        seen = set()
        for bid in self.order:
            blk = self.blocks[bid]
            name = body_name(blk)
            if name.startswith("fresh:") or name in seen:
                continue
            seen.add(name)
            if name in self.bodies:
                sitting = self.bodies[name]["sitting"]
            else:
                sitting = blk.get("sitting")
            if not sitting:
                continue
            start = w.clock.tick_in_cycle(cyc, sitting["day_of_cycle"], sitting["ticks"][0])
            end = w.clock.tick_in_cycle(cyc, sitting["day_of_cycle"], sitting["ticks"][1])
            plan.append((start, name, bid, end))
        for start, name, bid, end in sorted(plan):
            self._new_sitting(name, bid, start, end)

    def _new_sitting(self, body, block_id, start, end, items=None, members=None, kind="regular"):
        s = {"id": f"S{self._sid}", "body": body, "block": block_id, "start": start, "end": end,
             "state": "scheduled", "items": items or [], "members": members, "presence": {},
             "schedule": {}, "kind": kind, "wealth": {}}
        self._sid += 1
        self.sittings.append(s)
        return s

    # --- duties ------------------------------------------------------------------------------
    def _pending_for_body(self, body):
        bids = {bid for bid in self.order if body_name(self.blocks[bid]) == body}
        if body == "review_bench" and self._bench_candidates():
            return True
        return any(p["status"] == "admissible" and p["block"] in bids for p in self.register)

    def body_members(self, body):
        if body == "plenary":
            return None
        return self.members.get(body, [])

    def duties_for(self, idx):
        out = []
        t = self.w.tick
        for s in self.sittings:
            if s["state"] == "closed" or t > s["end"] or s["start"] - t > 4:
                continue
            if s["state"] == "scheduled" and not self._pending_for_body(s["body"]) and s["kind"] == "regular":
                continue
            if s["state"] == "open" and not s["items"]:
                continue
            members = s["members"] if s["members"] is not None else self.body_members(s["body"])
            if members is None:
                role = "plenary"
            elif idx in members:
                role = "member"
            else:
                continue
            out.append({"kind": "sitting", "id": s["id"], "body": s["body"], "role": role,
                        "start": s["start"], "end": s["end"], "location": "assembly_hall"})
        return out

    # --- sittings -----------------------------------------------------------------------------
    def on_tick_start(self):
        w = self.w
        if w.time.day_of_cycle == 1 and w.time.tick_of_day == 1:
            self.on_cycle_start()
        if w.time.tick_of_day == 1:
            self.alerts_today = {}
            self.harm_detected_today = {}
        for s in self.sittings:
            if s["state"] == "scheduled" and s["start"] == w.tick:
                self.open_sitting(s)

    def _agenda(self, s):
        w = self.w
        blk = self.blocks[s["block"]]
        cap = blk.get("agenda", {}).get("cap", self.agenda_cfg["cap"])
        order = blk.get("agenda", {}).get("order", self.agenda_cfg["order"])
        if s["body"] in self.bodies:
            cap, order = self.agenda_cfg["cap"], self.agenda_cfg["order"]
        bids = {bid for bid in self.order if body_name(self.blocks[bid]) == s["body"]}
        if s["body"] == "review_bench":
            self._bench_items()
        cands = [p for p in self.register if p["status"] == "admissible" and p["block"] in bids]
        first = [p for p in cands if p["urgent"] or p["mandatory"]]
        rest = [p for p in cands if not (p["urgent"] or p["mandatory"])]
        chosen = first[:cap]
        n = cap - len(chosen)
        if n > 0 and rest:
            if order == "lottery":
                rng = w.streams.get("kleroterion")
                pool = list(rest)
                picks = []
                while pool and len(picks) < n:
                    picks.append(pool.pop(rng.randrange(len(pool))))
                chosen += sorted(picks, key=lambda p: int(p["id"][1:]))
                self.log.emit(w.tick, "agenda_lottery", "kleroterion",
                              {"sitting": s["id"], "pool": [p["id"] for p in rest],
                               "chosen": [p["id"] for p in picks]})
            else:
                chosen += rest[:n]
        return chosen

    def open_sitting(self, s):
        w = self.w
        s["state"] = "open"
        self.sitting_counts[s["body"]] = self.sitting_counts.get(s["body"], 0) + 1
        if s["body"] == "cycle_assembly" and self.g.get("concentration_trigger"):
            self._concentration_item()
        if s["kind"] == "regular":
            for p in self._agenda(s):
                p["status"] = "on_agenda"
                s["items"].append(self._item(p))
        if s["members"] is None:
            s["members"] = self.body_members(s["body"])
        blk = self.blocks[s["block"]]
        vote = step(blk, "vote")
        if vote.get("weights") == "wealth" or (vote.get("quorum") or {}).get("of") == "wealth":
            s["wealth"] = {i: max(0, w.citizens[i].wealth(w.cfg["prices_ref"])) for i in w.active_ids()}
        delib = step(blk, "deliberation")
        sched = {}
        t = s["start"]
        if delib:
            ph = delib["phases"]
            for _ in range(ph["information"]):
                sched[t] = "information"; t += 1
            for k in range(ph["debate"]):
                sched[t] = "debate_last" if k == ph["debate"] - 1 else "debate"; t += 1
            for k in range(ph["dialogue"]):
                sched[t] = "dialogue_last" if k == ph["dialogue"] - 1 else "dialogue"; t += 1
            sched[t] = "aggregation"
            s["end"] = max(s["end"], t)
        else:
            sched[s["end"]] = "aggregation"
        s["schedule"] = sched
        s["deliberative"] = bool(delib)
        reflex = (s["body"] == "cycle_assembly" and self.g.get("reflexivity")
                  and self.sitting_counts[s["body"]] % 2 == 0)
        self.log.emit(w.tick, "sitting_opened", s["body"],
                      {"sitting": s["id"], "block": s["block"], "items": [i["id"] for i in s["items"]],
                       "members": sorted(s["members"]) if s["members"] is not None else None,
                       "start": s["start"], "end": s["end"], "reflexivity": int(bool(reflex))})
        if reflex:
            self.log.emit(w.tick, "reflexivity_session", s["body"], {"sitting": s["id"]})
        if not s["items"]:
            s["state"] = "closed"
            self.log.emit(w.tick, "sitting_closed", s["body"], {"sitting": s["id"], "decided": 0})

    def _item(self, p):
        return {"id": p["id"], "proposal": p, "effect": copy.deepcopy(p["effect"]),
                "versions": [copy.deepcopy(p["effect"])], "block": p["block"],
                "sanction": p["sanction"], "author": p["author"], "evaluations": {}, "stances": [],
                "amendments": {}, "turns": {}, "objections": {}, "decided": False, "extra": {},
                "round": 1, "provisional": None}

    def _present(self, s, tick, attendees):
        if s["members"] is None:
            return sorted(i for i in attendees)
        return sorted(i for i in attendees if i in s["members"])

    def on_tick_end(self, attendees):
        """Run each open sitting's phase for this tick. ``attendees``: ids who attended the Hall."""
        w = self.w
        t = w.tick
        for s in self.sittings:
            if s["state"] != "open" or t < s["start"]:
                continue
            present = self._present(s, t, attendees)
            s["presence"][t] = set(present)
            self._pay_stipends(s, present)
            phase = s["schedule"].get(t)
            for item in s["items"]:
                if item["decided"]:
                    continue
                ph = item["extra"].get(t, phase)
                if ph is None:
                    continue
                self._run_phase(s, item, ph, present, t)
            if all(i["decided"] for i in s["items"]) or t >= s["end"] + 2:
                for i in s["items"]:
                    if not i["decided"]:
                        i["decided"] = True
                        i["proposal"]["status"] = "lapsed"
                        self.log.emit(t, "decision", s["body"], {"proposal": i["id"], "outcome": "lapsed",
                                                                 "sitting": s["id"]})
                s["state"] = "closed"
                self.log.emit(t, "sitting_closed", s["body"],
                              {"sitting": s["id"], "decided": sum(1 for i in s["items"] if i.get("outcome"))})

    def _pay_stipends(self, s, present):
        amt = self.w.rules.stipend
        if amt <= 0 or not present:
            return
        paid = self.w.treasury.pay_many([(i, amt) for i in present], "stipend")
        for i, p in paid:
            self.w.citizens[i].credits += p

    def _run_phase(self, s, item, ph, present, t):
        if ph == "information":
            DL.information(self, item, present, t)
        elif ph in ("debate", "debate_last"):
            DL.debate(self, item, present, t)
            if ph == "debate_last":
                DL.facilitator(self, item, t)
        elif ph in ("dialogue", "dialogue_last", "reopened_dialogue"):
            DL.dialogue(self, item, present, t)
            if ph in ("dialogue_last", "reopened_dialogue"):
                DL.amend_toward_median(self, item, t)
                DL.reevaluate(self, item, present, t)
            if ph == "dialogue_last" and step(self.blocks[item["block"]], "advocate_hearing") and self.advocates:
                hearing = step(self.blocks[item["block"]], "advocate_hearing")
                advs = [a for a in hearing["advocates"] if a in self.advocates]
                ADV.hearing(self, item, t, advs)
        elif ph == "aggregation":
            self._aggregate(s, item, present, t)

    def _eligible(self, s, present, t):
        if s["members"] is None or not s.get("deliberative"):
            return list(present)
        ticks = [tk for tk in sorted(s["presence"]) if s["start"] <= tk <= t]
        ok = []
        for i in present:
            if all(i in s["presence"][tk] for tk in ticks):
                ok.append(i)
        logged = s.setdefault("absent_logged", set())
        for i in s["members"]:
            if i not in ok and i not in logged:
                logged.add(i)
                self.log.emit(t, "absent", i, {"sitting": s["id"]})
        return ok

    def _aggregate(self, s, item, present, t):
        w = self.w
        blk = self.blocks[item["block"]]
        vote = step(blk, "vote")
        voters = self._eligible(s, present, t)
        weights_kind = vote.get("weights", "one_citizen_one_vote")
        tallies = {"yes": 0, "no": 0, "abstain": 0}
        counts = {"yes": 0, "no": 0, "abstain": 0}
        votes = {}
        for i in sorted(voters):
            wt = s["wealth"].get(i, 0) if weights_kind == "wealth" else 1
            b = self.ballot(i, item, wt)
            tallies[b["vote"]] += wt
            counts[b["vote"]] += 1
            votes[i] = b["vote"]
        cast = sum(tallies.values())
        q = vote.get("quorum")
        quorum_ok = True
        if q is not None:
            if "count" in q:
                quorum_ok = sum(counts.values()) >= q["count"]
            else:
                of = q.get("of", "wealth" if weights_kind == "wealth" else "citizens")
                if of == "wealth":
                    base = sum(s["wealth"].values())
                elif s["members"] is not None:
                    base = len(s["members"])
                else:
                    base = len(w.active_ids())
                quorum_ok = cast * 1000 >= q["share"] * base and cast > 0
        rule = vote["rule"]
        if rule == "majority_of_votes_cast":
            passed = cast > 0 and 2 * tallies["yes"] > cast
        else:
            passed = counts["yes"] >= rule["yes"]
        allowed = vote.get("allowed_effects")
        if allowed and item["effect"]["type"] not in allowed:
            passed = False
        outcome = "adopted" if (passed and quorum_ok) else ("no_quorum" if not quorum_ok else "rejected")
        provisional = bool(item["objections"]) and item["round"] == 1
        self.log.emit(t, "decision", s["body"],
                      {"proposal": item["id"], "outcome": outcome, "yes": tallies["yes"],
                       "no": tallies["no"], "abstain": tallies["abstain"], "voters": len(voters),
                       "sitting": s["id"], "block": item["block"], "round": item["round"],
                       "provisional": int(provisional), "effect": item["effect"],
                       "amended": int(len(item["versions"]) > 1)})
        if provisional:
            item["provisional"] = outcome
            item["round"] = 2
            item["extra"][t + 1] = "reopened_dialogue"
            item["extra"][t + 2] = "aggregation"
            s["end"] = max(s["end"], t + 2)
            return
        item["decided"] = True
        item["outcome"] = outcome
        item["proposal"]["status"] = outcome
        if item.get("provisional") is not None:
            self.log.emit(t, "objection_result", s["body"],
                          {"proposal": item["id"], "first": item["provisional"], "second": outcome,
                           "changed": int(item["provisional"] != outcome or len(item["versions"]) > 1)})
        if outcome == "adopted":
            self.enact(item, votes, t)

    # --- publication and enactment ----------------------------------------------------------
    def enact(self, item, votes, t):
        w = self.w
        eff = item["effect"]
        blk = self.blocks[item["block"]]
        self.log.emit(t, "publication", "archive", {"proposal": item["id"], "effect": eff,
                                                    "block": item["block"]})
        typ = eff["type"]
        if typ == "amend_block":
            self.pending_amendments.append(({"id": item["id"], "effect": eff}, eff["block"]))
            return
        if typ == "allocate":
            w.allocate(eff, item["id"])
            return
        if typ == "restitution":
            w.restitution(eff, item["id"])
            return
        rule = w.rules.adopt(eff, t + 1, item["id"], fairness=self.fairness(blk), votes=votes)
        if typ == "suspend":
            c = w.citizens.get(eff["agent"])
            if c is not None:
                for a in eff["actions"]:
                    c.suspended[a] = max(c.suspended.get(a, 0), rule.until)

    def apply_amendment(self, eff, pid):
        bid = eff["block"]
        if bid not in self.blocks:
            self.log.emit(self.w.tick, "amendment_rejected", None, {"proposal": pid, "reason": "no such block"})
            return
        blk = copy.deepcopy(self.blocks[bid])
        f, v = eff["field"], eff["value"]
        vote = step(blk, "vote")
        if f == "quorum":
            vote["quorum"] = v
        elif f == "rule":
            vote["rule"] = v
        elif f == "weights":
            vote["weights"] = v
        elif f == "agenda_cap":
            blk.setdefault("agenda", {"cap": 3, "order": "first_registered"})["cap"] = v
        elif f == "deliberation":
            has = step(blk, "deliberation") is not None
            if v and not has:
                i = [s["type"] for s in blk["steps"]].index("vote")
                blk["steps"].insert(i, {"type": "deliberation", "phases": dict(DEFAULT_PHASES),
                                        "location": "assembly_hall"})
            elif not v and has:
                blk["steps"] = [s for s in blk["steps"] if s["type"] != "deliberation"]
        elif f == "sortition_size":
            blk["body"] = "plenary" if v == 0 else {"type": "panel", "size": v}
            if v and blk.get("sitting") is None:
                blk["sitting"] = {"day_of_cycle": 2, "ticks": [9, 14]}
        try:
            validate_block(blk)
        except BlockError as e:
            self.log.emit(self.w.tick, "amendment_rejected", None, {"proposal": pid, "reason": str(e)})
            return
        self.blocks[bid] = blk
        self.block_versions[bid] += 1
        self.log.emit(self.w.tick, "block_amended", None, {"proposal": pid, "block": bid, "field": f,
                                                           "value": v, "version": self.block_versions[bid]})

    # --- alerts, sanctions, kill switch ------------------------------------------------------
    def alert(self, alerter, target, deal=None, reason=None):
        w = self.w
        self.log.emit(w.tick, "alert", alerter, {"target": target, "deal": deal, "reason": reason})
        if deal is not None:
            from ..world import deals as D
            d = w.deals.deals.get(deal)
            if d is not None and d.get("victim") == alerter and D.raise_default(w, w.citizens[alerter], deal):
                if not self.bodies:
                    amt = min(d["value"], E.bounds(w.cfg, "restitution")[1])
                    if amt > 0 and d["defaulter"] != alerter:
                        self.register_proposal("archive", {"type": "restitution", "from": d["defaulter"],
                                                           "to": alerter, "amount": amt},
                                               sanction=True, urgent=True, reason=f"alert:{deal}")
        if self.g.get("kill_switch") and isinstance(target, int):
            s = self.alerts_today.setdefault(target, set())
            s.add(alerter)
            if len(s) >= 3:
                self.convene_kill_switch(target, "three_alerts")

    def note_detected(self, act, agent, payload):
        w = self.w
        self.detected.append((w.tick, act, agent.idx, dict(payload)))
        n = self.harm_detected_today.get(agent.idx, 0) + 1
        self.harm_detected_today[agent.idx] = n
        if n >= 3 and self.g.get("kill_switch"):
            self.log.emit(w.tick, "monitor_alarm", "observatory", {"target": agent.idx, "reason": "harm"})
            self.convene_kill_switch(agent.idx, "monitor")

    def _bench_candidates(self):
        horizon = self.w.tick - self.w.clock.ticks_per_cycle
        out = []
        for tk, act, agent, payload in self.detected:
            key = (tk, act, agent)
            if tk > horizon and key not in self.adjudicated and self.w.citizens[agent].active:
                out.append((tk, act, agent, payload))
        return out

    def _bench_items(self):
        w = self.w
        if "review_bench" not in self.bodies:
            return
        fine = min(2 * w.sawa(), E.bounds(w.cfg, "restitution")[1])
        for tk, act, agent, payload in self._bench_candidates()[:self.agenda_cfg["cap"]]:
            self.adjudicated.add((tk, act, agent))
            amt = min(fine, max(0, w.citizens[agent].credits))
            if amt <= 0:
                continue
            self.register_proposal("review_bench", {"type": "restitution", "from": agent,
                                                    "to": "treasury", "amount": amt},
                                   sanction=True, mandatory=True, reason=f"breach:{act}")

    def _concentration_item(self):
        w = self.w
        from ..metrics.economy import gini
        wealth = [max(0, w.citizens[i].wealth(w.cfg["prices_ref"])) for i in w.active_ids()]
        total = sum(wealth)
        if total <= 0:
            return
        top = max(wealth) * 1000 // total
        g = gini(wealth)
        if top > 300 or g > 400:
            eff = {"type": "set_tax", "base": "income", "rate": 100}
            self.log.emit(w.tick, "concentration_trigger", "treasury", {"top_share": top, "gini": g})
            if not w.rules.is_duplicate(eff):
                self.register_proposal("treasury", eff, mandatory=True, reason="concentration_trigger")

    def convene_kill_switch(self, target, reason):
        w = self.w
        ks = [bid for bid in self.order if isinstance(self.blocks[bid]["body"], dict)
              and self.blocks[bid]["body"]["type"] == "fresh_panel"]
        if not ks:
            return
        cyc = w.time.cycle
        if self.kill_switch_cycle.get(target) == cyc:
            return
        self.kill_switch_cycle[target] = cyc
        blk = self.blocks[ks[0]]
        sort = step(blk, "sortition")
        size = sort["size"] if sort else blk["body"]["size"]
        pool = [i for i in self.eligible_pool() if i != target]
        res = K.draw(w.streams.get("kleroterion"), pool, size, None,
                     respond=self._respond(body_name(blk), size), log=w.log, tick=w.tick,
                     body=body_name(blk))
        eff = {"type": "suspend", "agent": target, "actions": list(KILL_SWITCH_ACTIONS),
               "duration": w.clock.ticks_per_cycle}
        pid = f"P{self._pid}"
        self._pid += 1
        p = {"id": pid, "author": "kill_switch", "effect": eff, "tick": w.tick, "cycle": cyc,
             "status": "on_agenda", "block": blk["id"], "sanction": True, "mandatory": True, "urgent": True}
        self.log.emit(w.tick, "proposal_registered", "kill_switch",
                      {"id": pid, "effect": eff, "admissible": 1, "reason": None, "block": blk["id"],
                       "sanction": 1, "mandatory": 1, "urgent": 1, "origin": reason})
        start = w.tick + 2
        delib = step(blk, "deliberation")
        n = sum(delib["phases"].values()) if delib else 0
        s = self._new_sitting(body_name(blk), blk["id"], start, start + n, items=[self._item(p)],
                              members=list(res["members"]), kind="kill_switch")
        self.log.emit(w.tick, "kill_switch_convened", "kleroterion",
                      {"target": target, "reason": reason, "sitting": s["id"], "members": res["members"]})

    # --- state -------------------------------------------------------------------------------
    def state(self):
        return {"blocks": {bid: self.blocks[bid] for bid in self.order},
                "register": [{"id": p["id"], "status": p["status"]} for p in self.register],
                "members": {k: sorted(v) for k, v in sorted(self.members.items())}}
