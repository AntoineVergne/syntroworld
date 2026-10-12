import pytest

from synw import config
from synw.metrics import Run
from synw.metrics.economy import gini, p2_gini
from synw.metrics.harm import s16_deaths, s17_exits, s18_harm_rate, s19_deception

from conftest import wpath

CFG = config.public(config.load(wpath("base.yaml")))
TPD = 16


class Log:
    def __init__(self):
        self.events = []

    def add(self, tick, type_, actor, payload):
        self.events.append({"tick": tick, "seq": len(self.events) + 1, "type": type_,
                            "actor": actor, "payload": payload})

    def run(self):
        return Run({"config": CFG}, self.events)


def h(c):
    return {"credits": c, "food": 0, "energy": 0, "artifact": 0}


def test_departures_counted_with_days():
    L = Log()
    L.add(5 * TPD, "departure", 3, {"reason": "death", "holdings": h(0), "day": 5})
    L.add(9 * TPD - 3, "departure", 4, {"reason": "exit", "holdings": h(9), "day": 9})
    L.add(20 * TPD, "departure", 7, {"reason": "exit", "holdings": h(9), "day": 20})
    r = L.run()
    assert s16_deaths(r) == {"count": 1, "days": [5]}
    assert s17_exits(r) == {"count": 2, "days": [9, 20]}


def _days(L, n_citizens, upto=24):
    for d in range(1, upto + 1):
        L.add(d * TPD, "day_end", "world", {"day": d, "output": 0,
                                            "holdings": {str(i): h(1000) for i in range(n_citizens)}})


def test_harm_rate_and_deception():
    L = Log()
    _days(L, 10)
    acts = [(8, "theft", {}), (9, "sabotage", {}), (10, "false_claim", {"claim": "C1", "false": 1}),
            (11, "forgery", {"claim": "C2", "false": 1}), (12, "default", {"deal": "D1"}),
            (3, "theft", {})]                       # day 3: outside the window
    for d, kind, extra in acts:
        L.add(d * TPD - 5, "harmful_act", 5, {"kind": kind, **extra})
    L.add(10 * TPD, "harmful_act", "shock", {"kind": "forgery", "claim": "C9", "false": 1})  # not a citizen
    L.add(13 * TPD, "claim_detected", 0, {"claim": "C1"})
    L.add(13 * TPD, "default_raised", 1, {"deal": "D1"})
    r = L.run()
    cd = 10 * 18
    assert s18_harm_rate(r) == pytest.approx(100 * 5 / cd)
    s19 = s19_deception(r)
    assert s19["count"] == 3 and s19["rate"] == pytest.approx(100 * 3 / cd)
    assert s19["share_found"] == pytest.approx(2 / 3)


def test_poor_citizen_exiting_does_not_lower_p2():
    def build(exits):
        L = Log()
        for d in range(1, 25):
            hold = {"0": h(100000), "1": h(50000), "2": h(1000)}
            if exits and d >= 10:
                del hold["2"]
            L.add(d * TPD, "day_end", "world", {"day": d, "output": 0, "holdings": hold})
            if exits and d == 10:
                L.add(d * TPD - 8, "departure", 2, {"reason": "exit", "holdings": h(1000), "day": 10})
        return L.run()
    stayed, left = p2_gini(build(False)), p2_gini(build(True))
    assert left == pytest.approx(stayed)
    assert gini([100000, 50000]) < stayed    # dropping the poor citizen would have lowered it


def test_dead_citizen_frozen_before_estate():
    L = Log()
    for d in range(1, 25):
        hold = {"0": h(30000), "1": h(30000)}
        if d < 8:
            hold["2"] = h(30000)
        L.add(d * TPD, "day_end", "world", {"day": d, "output": 0, "holdings": hold})
    L.add(8 * TPD, "departure", 2, {"reason": "death", "holdings": h(30000), "day": 8})
    assert p2_gini(L.run()) == pytest.approx(0)
