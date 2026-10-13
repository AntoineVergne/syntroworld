from synw.world import river

K = 1000000
R = 250


def run(S, harvest, days, **kw):
    for _ in range(days):
        S = river.update(S, min(harvest, S), K, R, **kw)
    return S


def test_no_harvest_converges_to_K():
    S = run(800000, 0, 200)
    assert K - S < K // 100
    assert run(100000, 0, 400) > 0.95 * K


def test_harvest_above_msy_collapses():
    msy = R * K // 4000  # r*K/4 per day = 62500
    S = 800000
    collapsed_day = None
    for d in range(400):
        S = river.update(S, min(msy + 10000, S), K, R)
        if river.is_collapsed(S, K, 200) and collapsed_day is None:
            collapsed_day = d
    assert collapsed_day is not None
    assert S == 0


def test_harvest_below_msy_sustains():
    S = run(800000, 40000, 300)
    assert river.is_sustainable(S, K, 500)


def test_never_negative():
    assert river.update(1000, 10**9, K, R) == 0
    assert river.update(0, 0, K, R) == 0


def test_collapse_halves_r_and_pollution_cuts():
    assert river.effective_r(R, 100000, K, 200) == R // 2
    assert river.effective_r(R, 500000, K, 200) == R
    assert river.effective_r(R, 500000, K, 200, polluting=True) == 200
    assert river.effective_r(R, 500000, K, 200, drought=True) == 0
