import random

import pytest

pytest.importorskip("numpy")

from synw.analysis.planted import check, report  # noqa: E402


def _rows(world_shift, n=500, seed=1):
    rng = random.Random(seed)
    base = [rng.gauss(0.9, 0.02) for _ in range(n)]
    noise = random.Random(seed + 99)
    return [{"seed": s + 1, "P1": base[s] + world_shift + noise.gauss(0, 0.01)} for s in range(n)]


def test_known_shift_recovered_and_detected():
    b, a = _rows(0.02, seed=1), _rows(0.0, seed=1)
    res = check(b, a, outcome="P1", coverage_n=100, coverage_reps=60, ns=(12, 100),
                power_reps=60, n_flips=2000)
    assert res["truth"] == pytest.approx(0.02, abs=0.003)
    assert res["coverage"]["covered"] >= 52 and res["coverage"]["interval"] == "paired t"
    curve = {r["n"]: r for r in res["power_curve"]}
    assert curve[100]["power_05"] > 0.9 and curve[100]["power_05"] >= curve[12]["power_05"]
    assert len(report(res)) >= 4


def test_planted_mock_raises_compliance_with_fairness(make_world):
    """λ > 0 lowers the breach probability more under a fairer procedure."""
    wb = make_world("b.yaml", lam=1000)
    wa = make_world("a.yaml", lam=1000)
    pb = wb.brains[5].breach_probability(wb.observe(5), "steal", 12000, 500, 1.0, wb.observe(5).rules)
    pa = wa.brains[5].breach_probability(wa.observe(5), "steal", 12000, 500, 1.0, wa.observe(5).rules)
    p0 = make_world("a.yaml").brains[5].breach_probability(wa.observe(5), "steal", 12000, 500, 1.0, wa.observe(5).rules)
    assert pb < pa < p0


def test_fairness_follows_procedure(make_world):
    assert make_world("a.yaml").rules.rules[0].fairness == 500
    assert make_world("b.yaml").rules.rules[0].fairness == 800
    assert make_world("c.yaml").rules.rules[0].fairness == 200
