"""Mechanical deliberation (02 §2, 03 §6.2), logged turn by turn.

Phases: information (projection and evaluations), debate (round-robin stances and
objection codes, plus the facilitator rule of 02 §1.3), dialogue (amendments; if the
panel's ideal points spread more than a threshold, the number moves to the panel
median), then re-evaluation (information effect). This is mechanical deliberation, and
it is documented as such.
"""

from . import effects as E

SPREAD_THRESHOLD = 100  # per-mille of the effect's legal range


def _primary(effect):
    k = E.PRIMARY.get(effect["type"])
    return effect.get(k) if k else None


def speaking_order(members, tick):
    m = sorted(members)
    if not m:
        return m
    r = tick % len(m)
    return m[r:] + m[:r]


def information(gov, item, present, tick):
    for idx in sorted(present):
        v = gov.evaluate(idx, item, phase="information")
        item["evaluations"][idx] = v


def debate(gov, item, present, tick):
    for idx in speaking_order(present, tick):
        sp = gov.speak(idx, item, phase="debate")
        item["stances"].append((idx, sp["stance"], sp["objection"]))
        item["turns"][idx] = item["turns"].get(idx, 0) + 1


def facilitator(gov, item, tick):
    """If all debate stances share a sign, the facilitator states the strongest objection."""
    stances = item["stances"]
    if not stances:
        return False
    signs = {s > 0 for _, s, _ in stances if s != 0}
    if len(signs) == 1 and all(s != 0 for _, s, _ in stances):
        weakest = min(stances, key=lambda x: (x[1], x[0]))
        code = weakest[2] if weakest[2] != "none" else "precedent"
        gov.w.log.emit(tick, "facilitator_turn", "facilitator",
                       {"proposal": item["id"], "objection": code, "unanimous_sign": int(signs.pop())})
        item["facilitator"] = code
        return True
    return False


def dialogue(gov, item, present, tick):
    for idx in speaking_order(present, tick):
        sp = gov.speak(idx, item, phase="dialogue")
        item["turns"][idx] = item["turns"].get(idx, 0) + 1
        if sp.get("amendment") is not None:
            item["amendments"][idx] = sp["amendment"]


def median(values):
    v = sorted(values)
    n = len(v)
    if n == 0:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) // 2


def amend_toward_median(gov, item, tick):
    """If the panel's proposed numbers spread more than the threshold, move to the median."""
    eff = item["effect"]
    num = _primary(eff)
    if num is None or len(item["amendments"]) < 2:
        return False
    vals = list(item["amendments"].values())
    lo, hi = E.bounds(gov.w.cfg, eff["type"])
    spread = max(vals) - min(vals)
    if spread * 1000 <= SPREAD_THRESHOLD * max(1, hi - lo):
        return False
    med = median(vals)
    new = E.clamp_primary(eff, med, gov.w.cfg)
    if new == eff:
        return False
    item["versions"].append(new)
    item["effect"] = new
    gov.w.log.emit(tick, "amendment", "panel", {"proposal": item["id"], "version": len(item["versions"]),
                                                "from": num, "to": _primary(new), "spread": spread,
                                                "effect": new})
    return True


def reevaluate(gov, item, present, tick):
    for idx in sorted(present):
        item["evaluations"][idx] = gov.evaluate(idx, item, phase="re-evaluation")
