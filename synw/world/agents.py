"""Citizens: needs, health, departures, theft and sabotage (03 §3, §5.6, §5.7).

Functions take the running world ``w`` (see ``synw.runner.World``) for config, log,
Treasury, random streams and rules.
"""

from dataclasses import dataclass, field

from . import map as wmap

GOODS = ("food", "energy", "artifact")
BASKET_GOODS = ("food", "energy")


@dataclass
class Citizen:
    idx: int
    name: str
    persona: dict
    home: str
    location: str
    credits: int = 0
    inv: dict = field(default_factory=lambda: {g: 0 for g in GOODS})
    health: int = 100
    status: str = "absent"          # absent (not yet arrived), active, dead, exited
    arrived_tick: int = 0
    departed_tick: int = 0
    departure: dict = None          # frozen holdings at departure
    zero_days: int = 0              # consecutive end-of-day steps at health 0
    transit_until: int = 0          # in transit through this tick
    work_ticks_today: int = 0
    harvest_today: int = 0
    data_access: bool = True
    relationships: dict = field(default_factory=dict)
    trust: dict = field(default_factory=dict)
    beliefs: dict = field(default_factory=lambda: {"river": "ok"})
    planted: dict = field(default_factory=dict)   # topic -> claim id
    suspended: dict = field(default_factory=dict)  # action -> until tick (inclusive)
    rogue: bool = False
    exit_intent: bool = False
    served: dict = field(default_factory=dict)     # body -> last cycle served
    acts_today: dict = field(default_factory=dict)  # act -> count (ground truth)

    @property
    def active(self):
        return self.status == "active"

    @property
    def departed(self):
        return self.status in ("dead", "exited")

    @property
    def incapacitated(self):
        return self.active and self.health <= 0

    def holdings(self):
        return {"credits": self.credits, **{g: self.inv[g] for g in GOODS}}

    def wealth(self, p_ref):
        return self.credits + sum(self.inv[g] * p_ref[g] // 1000 for g in GOODS)

    def productivity(self, site, low=30):
        """Per-mille multiplier at ``site`` (04 §4), halved below the low-health line."""
        p = self.persona
        if p.get("main_site") == "any":
            m = p["mult"]
        elif site in (p.get("main_site"), p.get("second_site")):
            m = p["mult"]
        else:
            m = 1000
        if self.health < low:
            m //= 2
        return m

    def is_suspended(self, action, tick):
        return self.suspended.get(action, 0) >= tick

    def state(self):
        return {"idx": self.idx, "status": self.status, "location": self.location,
                "credits": self.credits, "inv": dict(self.inv), "health": self.health,
                "zero_days": self.zero_days, "beliefs": dict(self.beliefs),
                "trust": {str(k): v for k, v in sorted(self.trust.items())},
                "relationships": {str(k): v for k, v in sorted(self.relationships.items())},
                "rogue": self.rogue}


def make_citizen(persona, cfg, founder=True):
    start = cfg["start"]["founder" if founder else "newcomer"]
    home = wmap.home_of(persona["index"])
    c = Citizen(idx=persona["index"], name=persona["name"], persona=dict(persona),
                home=home, location=home if founder else "gate",
                credits=start["credits"], health=cfg["start"]["health"])
    c.inv["food"] = start["food"]
    c.inv["energy"] = start["energy"]
    return c


def init_relations(citizens, cfg):
    for c in citizens.values():
        for o in citizens.values():
            if o.idx != c.idx:
                c.relationships[o.idx] = cfg["start"]["relationship"]
                c.trust[o.idx] = cfg["start"]["trust"]


def _units_missing(milli):
    return (milli + 999) // 1000 if milli > 0 else 0


def consume_basket(w, c):
    """End-of-day basket, rent and data fee for one citizen (03 §3.2). Logs and returns the result."""
    cfg = w.cfg
    hcfg = cfg["health"]
    res = {"food": 0, "energy": 0, "rent": False, "data": False}
    loss = 0
    for g in BASKET_GOODS:
        need = cfg["basket"][g]
        take = min(need, c.inv[g])
        c.inv[g] -= take
        res[g] = take
        loss += hcfg["missing_unit"] * _units_missing(need - take)
    rent = cfg["fees"]["rent"]
    if c.credits >= rent:
        c.credits -= rent
        w.treasury.collect(rent, "rent", c.idx)
        res["rent"] = True
    else:
        loss += hcfg["missing_unit"]
        c.location = "square"
    fee = cfg["fees"]["data"]
    if c.credits >= fee:
        c.credits -= fee
        w.treasury.collect(fee, "data_fee", c.idx)
        res["data"] = True
    c.data_access = res["data"]
    full = (res["food"] == cfg["basket"]["food"] and res["energy"] == cfg["basket"]["energy"]
            and res["rent"] and res["data"])
    before = c.health
    if full:
        c.health = min(hcfg["max"], c.health + hcfg["full_basket"])
    else:
        c.health = max(0, c.health - loss)
    res["full"] = full
    res["health_before"] = before
    res["health"] = c.health
    w.log.emit(w.tick, "consume", c.idx, {**res, "full": int(full), "rent": int(res["rent"]),
                                          "data": int(res["data"])})
    return res


def health_check(w, c):
    """After consumption: incapacitation, and death after ``death_days`` end-of-days at 0 (03 §3.4)."""
    if c.health <= 0:
        c.zero_days += 1
        if c.zero_days == 1:
            w.log.emit(w.tick, "incapacitated", c.idx, {})
        if c.zero_days >= w.cfg["health"]["death_days"]:
            die(w, c)
    else:
        c.zero_days = 0


def _depart(w, c, status, reason):
    frozen = c.holdings()
    c.departure = {"tick": w.tick, "reason": reason, "holdings": frozen,
                   "wealth": c.wealth(w.cfg["prices_ref"])}
    c.status = status
    c.departed_tick = w.tick
    w.log.emit(w.tick, "departure", c.idx, {"reason": reason, "holdings": frozen,
                                            "wealth": c.departure["wealth"],
                                            "day": w.time.day})


def die(w, c):
    """Death; the estate goes to the Treasury (world rule, 03 §3.4)."""
    _depart(w, c, "dead", "death")
    if c.credits:
        w.treasury.collect(c.credits, "estate", c.idx)
    goods = {g: c.inv[g] for g in GOODS if c.inv[g]}
    if goods:
        w.treasury.receive_goods(goods, "estate", c.idx)
    c.credits = 0
    c.inv = {g: 0 for g in GOODS}


def leave(w, c):
    """Exit through the Gate with all holdings (03 §3.4). Rogues never choose to exit."""
    if c.location != "gate":
        return False
    _depart(w, c, "exited", "exit")
    return True


def apply_rest(w, c):
    gain = w.cfg["health"]["rest"] if c.location in (c.home, "clinic") else 0
    before = c.health
    c.health = min(w.cfg["health"]["max"], c.health + gain)
    return c.health - before


def apply_care(w, carer, patient):
    if patient.location != carer.location or carer.location != "clinic" or not patient.active:
        return 0
    before = patient.health
    patient.health = min(w.cfg["health"]["max"], patient.health + w.cfg["health"]["care"])
    if patient.health > 0:
        patient.zero_days = 0
    return patient.health - before


def give(c, to, item, qty):
    qty = int(qty)
    if qty <= 0:
        return 0
    if item == "credits":
        qty = min(qty, c.credits)
        c.credits -= qty
        to.credits += qty
    else:
        qty = min(qty, c.inv[item])
        c.inv[item] -= qty
        to.inv[item] += qty
    return qty


# --- Harmful acts ----------------------------------------------------------------------

def _roll(w, prob_milli):
    return w.streams.get("world").randrange(1000) < prob_milli


def steal(w, thief, target):
    """Theft (03 §5.6): the smaller of a share of the target's credits and a cap.

    Detection is rolled on the ``world`` stream. A detected theft is public and is
    reversed automatically. Every theft is logged as ground truth, with a breach event
    for each rule in force that bans it (the founding ban from tick 1).
    """
    tcfg = w.cfg["theft"]
    amount = min(target.credits * tcfg["share"] // 1000, tcfg["cap"])
    target.credits -= amount
    thief.credits += amount
    detected = _roll(w, w.detection("steal"))
    w.log.emit(w.tick, "theft", thief.idx, {"target": target.idx, "amount": amount,
                                            "detected": int(detected)})
    w.record_breach("steal", thief, detected, {"target": target.idx, "amount": amount})
    if detected:
        back = min(amount, thief.credits)
        thief.credits -= back
        target.credits += back
        w.log.emit(w.tick, "restitution", thief.idx, {"to": target.idx, "amount": back,
                                                      "kind": "theft"})
        target.relationships[thief.idx] = max(0, target.relationships.get(thief.idx, 500) - 200)
        target.trust[thief.idx] = max(0, target.trust.get(thief.idx, 500) - 200)
        w.on_detected("steal", thief, {"target": target.idx, "amount": amount})
    else:
        w.undetected_thefts.append((w.tick, thief.idx, target.idx))
    return amount, detected


def sabotage(w, actor, target):
    """Sabotage (03 §5.7): a site's output is halved for the day, or up to N units of one
    good the target citizen holds are destroyed. A detected saboteur pays the damage at
    reference prices to the victim (or the Treasury for a site), as far as credits allow.
    """
    scfg = w.cfg["sabotage"]
    p_ref = w.cfg["prices_ref"]
    if isinstance(target, str):
        w.site_factor[target] = w.site_factor.get(target, 1000) * scfg["site_factor"] // 1000
        # damage: estimated lost output for the rest of the day, at reference prices
        damage = w.estimate_site_damage(target)
        payload = {"site": target, "damage": damage}
        victim = None
    else:
        good = max(("food", "energy", "artifact"),
                   key=lambda g: (target.inv[g] * p_ref[g], g))
        qty = min(scfg["goods"], target.inv[good])
        target.inv[good] -= qty
        damage = qty * p_ref[good] // 1000
        payload = {"target": target.idx, "good": good, "qty": qty, "damage": damage}
        victim = target
    detected = _roll(w, w.detection("sabotage"))
    payload["detected"] = int(detected)
    w.log.emit(w.tick, "sabotage", actor.idx, payload)
    w.record_breach("sabotage", actor, detected, payload)
    if detected:
        pay = min(damage, actor.credits)
        actor.credits -= pay
        if victim is not None:
            victim.credits += pay
            victim.relationships[actor.idx] = max(0, victim.relationships.get(actor.idx, 500) - 200)
            victim.trust[actor.idx] = max(0, victim.trust.get(actor.idx, 500) - 200)
        else:
            w.treasury.collect(pay, "sabotage_damage", actor.idx)
        w.log.emit(w.tick, "damage_paid", actor.idx, {"to": victim.idx if victim else "treasury",
                                                      "amount": pay, "damage": damage})
        w.on_detected("sabotage", actor, payload)
    return damage, detected
