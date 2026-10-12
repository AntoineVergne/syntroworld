"""Rules in force (02 §3.2): enforced effects are applied, normative ones can be broken.

Founding norms ``ban(steal)`` and ``ban(sabotage)`` are in force from tick 1 in every
world (02 §3.3). Exposures for compliance (P1) are computed per (citizen, rule, day).
"""

from . import effects as E

FOUNDING = [
    {"id": "R0-steal", "effect": {"type": "ban", "act": "steal", "scope": None}},
    {"id": "R0-sabotage", "effect": {"type": "ban", "act": "sabotage", "scope": None}},
]


class Rule:
    __slots__ = ("id", "effect", "kind", "since", "until", "source", "fairness", "votes")

    def __init__(self, id, effect, since, source, fairness=500, votes=None, until=None):
        self.id = id
        self.effect = dict(effect)
        self.kind = E.KIND[effect["type"]]
        self.since = since
        self.until = until
        self.source = source
        self.fairness = fairness
        self.votes = dict(votes or {})  # citizen idx -> "yes" | "no" | "abstain"

    def to_json(self):
        return {"id": self.id, "effect": self.effect, "kind": self.kind, "since": self.since,
                "until": self.until, "source": self.source, "fairness": self.fairness}


class RuleRegistry:
    def __init__(self, cfg, log=None, now=lambda: 0, founding_fairness=500):
        self.cfg = cfg
        self.log = log
        self.now = now
        self.rules = []          # every rule ever adopted (history)
        self._next = 1
        self.taxes = {"income": 0, "trade": 0, "harvest": 0}
        self.dividend = 0
        self.stipend = 0
        self.plant_mode = "clean"
        self.records = []        # amend_text and other recorded-only decisions
        for f in FOUNDING:
            self._install(Rule(f["id"], f["effect"], 1, "founding", founding_fairness))

    # -- adoption -------------------------------------------------------------------------
    def _emit(self, type_, payload):
        if self.log is not None:
            self.log.emit(self.now(), type_, "rules", payload)

    def _install(self, rule):
        s = E.slot(rule.effect)
        if s is not None:
            for r in self.active():
                if E.slot(r.effect) == s:
                    r.until = rule.since - 1
                    self._emit("rule_repealed", {"rule": r.id, "by": rule.id})
        self.rules.append(rule)
        self._apply_state(rule.effect)
        self._emit("rule_in_force", rule.to_json())
        return rule

    def _apply_state(self, eff):
        t = eff["type"]
        if t == "set_tax":
            self.taxes[eff["base"]] = eff["rate"]
        elif t == "set_dividend":
            self.dividend = eff["amount"]
        elif t == "set_stipend":
            self.stipend = eff["amount"]
        elif t == "set_plant_mode":
            self.plant_mode = eff["mode"]

    def adopt(self, effect, tick, source, fairness=500, votes=None):
        """Put a decided effect in force. One-shot effects are returned for the caller to execute."""
        err = E.check(effect, self.cfg)
        if err:
            raise ValueError(f"illegal effect: {err}")
        rid = f"R{self._next}"
        self._next += 1
        until = None
        if effect["type"] == "suspend":
            until = tick + effect["duration"] - 1
        rule = Rule(rid, effect, tick, source, fairness, votes, until)
        if effect["type"] == "amend_text":
            self.records.append(rule)
            self.rules.append(rule)
            self._emit("text_recorded", rule.to_json())
            return rule
        return self._install(rule)

    # -- queries --------------------------------------------------------------------------
    def active(self, tick=None):
        t = self.now() if tick is None else tick
        return [r for r in self.rules
                if r.since <= t and (r.until is None or r.until >= t) and r.kind != E.RECORDED
                and r.effect["type"] not in ("allocate", "restitution", "amend_block")]

    def normative(self, tick=None):
        return [r for r in self.active(tick) if r.kind == E.NORMATIVE]

    def bans(self, act, agent, tick=None):
        out = []
        for r in self.normative(tick):
            e = r.effect
            if e["type"] == "ban" and e["act"] == act and e.get("scope") in (None, agent):
                out.append(r)
            if act == "harvest" and e["type"] == "harvest_cap" and e["qty"] == 0:
                out.append(r)
        return out

    def harvest_cap(self, tick=None):
        caps = [r for r in self.normative(tick) if r.effect["type"] == "harvest_cap"]
        return (caps[-1].effect["qty"], caps[-1]) if caps else (None, None)

    def fine(self, action, tick=None):
        fs = [r for r in self.active(tick) if r.effect["type"] == "set_fine"
              and r.effect["action"] == action]
        return fs[-1].effect["amount"] if fs else 0

    def tax_rate(self, base):
        return self.taxes.get(base, 0)

    def suspensions(self, tick=None):
        return [r for r in self.active(tick) if r.effect["type"] == "suspend"]

    def is_duplicate(self, effect, tick=None):
        k = E.key(effect)
        return any(E.key(r.effect) == k for r in self.active(tick))

    def in_force_json(self, tick=None):
        out = []
        for r in self.active(tick):
            d = {"id": r.id, "type": r.effect["type"], "kind": r.kind, "fairness": r.fairness,
                 **{k: v for k, v in r.effect.items() if k != "type"}}
            d["votes"] = {str(k): v for k, v in r.votes.items()}
            out.append(d)
        return out

    # -- exposures (02 §3.2) ----------------------------------------------------------------
    def exposures(self, citizen_day, tick=None):
        """For one citizen-day, return ``[(rule, exposed, breached)]`` for normative rules.

        ``citizen_day`` holds ``agent``, ``feasible`` (acts feasible at least once that
        day), ``claims`` (claims made), ``deals_due`` (accepted deals due), ``harvested``
        (harvest ticks), and ``breaches`` (set of rule ids breached).
        """
        out = []
        agent = citizen_day["agent"]
        for r in self.normative(tick):
            e = r.effect
            if e["type"] == "ban":
                if e.get("scope") not in (None, agent):
                    continue
                act = e["act"]
                if act == "false_claim":
                    exposed = citizen_day["claims"] > 0
                elif act == "default":
                    exposed = citizen_day["deals_due"] > 0
                else:
                    exposed = act in citizen_day["feasible"]
            elif e["type"] == "harvest_cap":
                exposed = citizen_day["harvested"] > 0 or ("harvest" in citizen_day["feasible"] and e["qty"] == 0)
            else:
                continue
            breached = r.id in citizen_day["breaches"]
            out.append((r, exposed or breached, breached))
        return out
