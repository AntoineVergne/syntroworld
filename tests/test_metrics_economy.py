import pytest

from synw import config
from synw.metrics import Run
from synw.metrics.economy import (gini, p2_gini, s1_basket_floor, s2_output, s3_commons)

from conftest import wpath

CFG = config.public(config.load(wpath("base.yaml")))
TPD = 16


def h(credits, food=0, energy=0, artifact=0):
    return {"credits": credits, "food": food, "energy": energy, "artifact": artifact}


def ev(tick, type_, actor, payload, seq=[0]):
    seq[0] += 1
    return {"tick": tick, "seq": seq[0], "type": type_, "actor": actor, "payload": payload}


def build(days):
    """``days``: {day: (holdings dict, output, river stock)}"""
    events = []
    for d, (hold, out, stock) in sorted(days.items()):
        t = d * TPD
        events.append(ev(t, "river", "world", {"day": d, "stock": stock}))
        events.append(ev(t, "day_end", "world", {"day": d, "output": out, "holdings":
                                                  {str(k): v for k, v in hold.items()}}))
    return Run({"config": CFG}, events)


def test_gini_extremes():
    assert gini([5, 5, 5, 5]) == 0
    for n in (2, 4, 10):
        assert gini([0] * (n - 1) + [100]) == pytest.approx((n - 1) / n)
    assert gini([]) == 0 and gini([0, 0]) == 0
    assert gini([-5, 0, 10]) == gini([0, 0, 10])


def test_p2_window_mean():
    equal = {i: h(10000) for i in range(4)}
    one = {0: h(40000), 1: h(0), 2: h(0), 3: h(0)}
    days = {d: (equal if d < 16 else one, 0, 800000) for d in range(1, 25)}
    r = build(days)
    window = list(range(7, 25))
    expected = sum(0.75 if d >= 16 else 0 for d in window) / len(window)
    assert p2_gini(r) == pytest.approx(expected)


def test_p2_uses_reference_prices():
    days = {d: ({0: h(0, food=5000), 1: h(10000)}, 0, 800000) for d in range(1, 25)}
    assert p2_gini(build(days)) == 0   # 5 food x 2 credits = 10 credits


def test_s1_basket_floor():
    events = []
    for d in range(1, 25):
        for i in range(2):
            events.append(ev(d * TPD, "consume", i, {"full": 1 if (i == 0 or d % 2) else 0}))
    r = Run({"config": CFG}, events)
    window = range(7, 25)
    full = sum(1 for d in window for i in range(2) if i == 0 or d % 2)
    assert s1_basket_floor(r) == pytest.approx(full / (2 * len(window)))


def test_s2_output_and_s3_commons():
    days = {d: ({0: h(1)}, 1000 * d, 600000 if d < 20 else 100000) for d in range(1, 25)}
    r = build(days)
    assert s2_output(r) == sum(1000 * d for d in range(7, 25))
    s3 = s3_commons(r)
    assert s3["share_sustainable"] == pytest.approx(13 / 18)
    assert s3["days_below_collapse"] == 5
    assert s3["min_stock"] == 100000


def test_metrics_on_a_real_run():
    from synw.runner import run
    w = run(wpath("a.yaml"), 1)
    r = Run(w.log.header, w.log.events)
    assert 0 <= p2_gini(r) < 1
    assert 0 <= s1_basket_floor(r) <= 1
    assert s2_output(r) > 0
