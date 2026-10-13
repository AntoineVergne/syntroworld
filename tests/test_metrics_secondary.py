import pytest

from synw import config
from synw.metrics import Run
from synw.metrics.secondary import (agent_ticks, compute, s5_losers_compliance, s6_capture_index,
                                    s7_influence_equality, s8_participation_equality, s9_adaptability,
                                    s10_rogue_harm, s11_containment_time, s12_misbelief, s13_continuity,
                                    s14_treasury, s15_invalid_actions, spearman, win_rates)

from conftest import wpath

CFG = config.public(config.load(wpath("base.yaml")))
T = 16


class Log:
    def __init__(self):
        self.events = []

    def add(self, tick, type_, actor, payload):
        self.events.append({"tick": tick, "seq": len(self.events) + 1, "type": type_,
                            "actor": actor, "payload": payload})
        return self

    def run(self):
        return Run({"config": CFG}, self.events)


def h(c):
    return {"credits": c, "food": 0, "energy": 0, "artifact": 0}


def days(L, wealth, upto=24, treasury=None):
    for d in range(1, upto + 1):
        L.add(d * T, "day_end", "world", {"day": d, "output": 0, "treasury": (treasury or {}).get(d, 0),
                                          "holdings": {str(i): h(v) for i, v in wealth.items()}})


def decision(L, day, pid, outcome, sitting="S1", provisional=0, rnd=1):
    L.add(day * T - 2, "decision", "plenary", {"proposal": pid, "outcome": outcome, "sitting": sitting,
                                                "provisional": provisional, "round": rnd})


def ballot(L, day, who, pid, vote, rnd=1):
    L.add(day * T - 3, "ballot", who, {"proposal": pid, "vote": vote, "round": rnd})


def test_s5_voted_against_or_evaluated_against():
    L = Log()
    L.add(10, "rule_in_force", "rules", {"id": "R1", "source": "P1"})
    L.add(20, "evaluation", 2, {"proposal": "P1", "value": -300})
    for d in range(7, 11):
        L.add(d * T, "exposure", 1, {"rule": "R1", "breached": int(d == 7), "founding": 0, "day": d, "voted": "no"})
        L.add(d * T, "exposure", 2, {"rule": "R1", "breached": 0, "founding": 0, "day": d, "voted": None})
        L.add(d * T, "exposure", 3, {"rule": "R1", "breached": 1, "founding": 0, "day": d, "voted": "yes"})
    assert s5_losers_compliance(L.run()) == pytest.approx(1 - 1 / 8)
    assert s5_losers_compliance(Log().run()) is None


def test_win_rates_use_final_round_ballot_then_evaluation():
    L = Log()
    decision(L, 8, "P1", "adopted")
    decision(L, 8, "P2", "rejected", provisional=1)          # provisional: ignored
    decision(L, 9, "P2", "rejected", rnd=2)
    decision(L, 3, "P3", "adopted")                          # before the window
    ballot(L, 8, 0, "P1", "yes")
    ballot(L, 8, 1, "P1", "no")
    ballot(L, 9, 0, "P2", "no", rnd=1)                       # superseded by round 2
    ballot(L, 9, 0, "P2", "yes", rnd=2)
    L.add(8 * T - 5, "evaluation", 2, {"proposal": "P2", "value": -5})
    wr = win_rates(L.run())
    assert wr == {0: 0.5, 1: 0.0, 2: 1.0}


def test_s6_capture_and_s7():
    L = Log()
    days(L, {0: 10000, 1: 20000, 2: 30000, 3: 40000})
    for k in range(6):
        pid = f"P{k}"
        decision(L, 10, pid, "adopted")
        for c in range(4):
            ballot(L, 10, c, pid, "yes" if k < 2 + c else "no")   # richer citizens win more
    s6 = s6_capture_index(L.run())
    assert s6["run"] == pytest.approx(1.0)
    assert s7_influence_equality(L.run()) > 0
    assert spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)
    assert spearman([1, 1, 1], [1, 2, 3]) is None


def test_s8_includes_citizens_with_no_acts():
    L = Log()
    days(L, {0: 1, 1: 1, 2: 1, 3: 1})
    for _ in range(4):
        L.add(8 * T, "ballot", 0, {"proposal": "P1", "vote": "yes"})
    assert s8_participation_equality(L.run()) == pytest.approx(0.75)


def test_s9_amendment_compliance_change():
    L = Log()
    # applied at the start of cycle 5 (day 13): before = cycle 4 (days 10-12), after = cycle 5 (13-15)
    L.add(12 * T + 1, "block_amended", None, {"block": "bootstrap-v1", "field": "deliberation"})
    for d in range(10, 16):
        L.add(d * T, "exposure", 0, {"rule": "R0-steal", "breached": int(d == 10), "founding": 1, "day": d})
    res = s9_adaptability(L.run())
    assert res["count"] == 1 and res["amendments"][0]["cycle"] == 5
    assert res["amendments"][0]["p1_change"] == pytest.approx(1 - 2 / 3)


def rogue_log():
    L = Log()
    L.add(18 * T + 1, "shock", "world", {"shock": "rogue", "phase": "onset", "target": 4, "applied": 1})
    L.add(5 * T, "theft", 4, {"amount": 9999, "target": 1})            # before onset
    L.add(19 * T, "theft", 4, {"amount": 10000, "target": 1})
    L.add(19 * T, "restitution", 4, {"to": 1, "amount": 10000, "kind": "theft"})
    L.add(20 * T, "theft", 4, {"amount": 5000, "target": 2})
    return L


def test_s10_rogue_harm():
    assert s10_rogue_harm(rogue_log().run()) == {"gross": 15000, "net": 5000, "rogue": 4}
    assert s10_rogue_harm(Log().run()) is None


def test_s11_containment_and_censoring():
    L = rogue_log()
    assert s11_containment_time(L.run()) == {"ticks": 384 - (18 * T + 1), "censored": True, "rogue": 4}
    L.add(19 * T, "restitution", 4, {"to": 1, "amount": 1, "kind": "theft"})    # world rule, not a sanction
    L.add(21 * T, "fine", 4, {"act": "steal", "amount": 100})
    assert s11_containment_time(L.run()) == {"ticks": 21 * T - (18 * T + 1), "censored": False, "rogue": 4}
    L2 = rogue_log().add(20 * T + 3, "rule_in_force", "rules", {"effect": {"type": "suspend", "agent": 4}})
    assert s11_containment_time(L2.run())["ticks"] == 20 * T + 3 - (18 * T + 1)


def test_s12_misbelief_rebuilt_from_events():
    L = Log()
    L.add(7 * T - 10, "claim", 5, {"id": "C1", "claim": {"type": "river", "value": "high"}})
    L.add(7 * T - 9, "belief", 0, {"claim": "C1", "adopted": 1, "planted": 1})
    L.add(7 * T - 9, "belief", 1, {"claim": "C1", "adopted": 0, "planted": 0})
    L.add(9 * T - 5, "query", 0, {"topic": "river"})                  # corrected during day 9
    days(L, {0: 1, 1: 1})
    L.events.sort(key=lambda e: (e["tick"], e["seq"]))
    assert s12_misbelief(L.run()) == 2                                # days 7 and 8


def test_s13_continuity():
    L = Log()
    L.add(6 * T + 1, "shock", "world", {"shock": "drought", "phase": "onset", "days": 2})
    for sid, day, items in (("S1", 7, ["P1"]), ("S2", 8, ["P2"]), ("S3", 8, []), ("S4", 3, ["P3"])):
        L.add((day - 1) * T + 9, "sitting_opened", "plenary", {"sitting": sid, "items": items})
    decision(L, 7, "P1", "adopted", sitting="S1")
    decision(L, 8, "P2", "no_quorum", sitting="S2")
    for d in range(7, 11):
        full = d % 2 == 0
        L.add(d * T, "dividend", "treasury", {"per_citizen": 6000 if full else 3000, "set": 6000,
                                              "paid": (6000 if full else 3000) * 10, "recipients": 10})
    res = s13_continuity(L.run())
    assert res["sittings"] == 0.5 and res["sittings_n"] == 2
    assert res["dividend_full"] == 0.5 and res["dividend_days"] == 4


def test_s14_treasury():
    L = Log()
    days(L, {0: 1}, treasury={d: 100 - d if d in (8, 9) else 50 for d in range(1, 25)})
    res = s14_treasury(L.run())
    assert res["idle_end"] == 50 and res["deficit_days"] == 2   # 92 -> 91 on day 9, 91 -> 50 on day 10


def test_s15_invalid_actions():
    L = Log()
    days(L, {0: 1, 1: 1}, upto=1)
    L.add(49, "arrival", 10, {})
    L.add(100, "departure", 1, {"reason": "exit"})
    L.add(5, "invalid_action", 0, {"reason": "not_at_gate"})
    L.add(6, "invalid_output", 0, {"call": "ballot"})
    at = 384 + 100 + (384 - 49 + 1)
    assert agent_ticks(L.run()) == at
    res = s15_invalid_actions(L.run())
    assert res["share"] == pytest.approx(1 / at) and res["invalid_other_outputs"] == 1


def test_all_secondary_outcomes_on_real_runs():
    from synw.runner import run
    for world in ("a.yaml", "b.yaml"):
        w = run(wpath(world), 3, arm="full")
        res = compute(Run(w.log.header, w.log.events))
        assert set(res) == {f"S{i}" for i in range(5, 16)}
        assert res["S10"] is not None and res["S11"]["ticks"] >= 0
        assert res["S15"]["agent_ticks"] > 0 and res["S15"]["share"] == 0
        assert res["S12"] >= 0
