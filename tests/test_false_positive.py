import random

import pytest

np = pytest.importorskip("numpy")

from synw.analysis import compare  # noqa: E402
from synw.analysis.false_positive import bootstrap_ci, check, report, sign_flip_p  # noqa: E402


def test_exact_matches_compare():
    rnd = random.Random(1)
    for n in (5, 8, 12):
        d = [rnd.gauss(0.1, 1) for _ in range(n)]
        p = sign_flip_p(np.array([d]).T)[0]
        assert p == pytest.approx(compare.sign_flip_p(d))
    assert sign_flip_p(np.array([[0.1] * 8]).T)[0] == pytest.approx(2 / 256)


def test_random_flips_detect_a_real_shift_and_not_noise():
    rng = np.random.default_rng(3)
    D = np.stack([rng.normal(0.5, 1, 100), rng.normal(0, 1, 100)], axis=1)
    p = sign_flip_p(D, 20000, np.random.default_rng(4))
    assert p[0] < 0.001 and p[1] > 0.001


def test_bootstrap_brackets_mean():
    rng = np.random.default_rng(5)
    D = rng.normal(0, 1, (60, 3))
    lo, hi = bootstrap_ci(D, 2000, np.random.default_rng(6))
    assert np.all(lo < D.mean(axis=0)) and np.all(D.mean(axis=0) < hi)


def _rows(n=600, seed=7):
    rng = random.Random(seed)
    return [{"seed": s, "P1": rng.gauss(0.9, 0.02), "P2": rng.gauss(0.2, 0.03),
             "P3": rng.gauss(0.6, 0.05), "P4": rng.gauss(0.0, 0.02)} for s in range(1, n + 1)]


def test_null_rates_and_determinism():
    a = check(_rows(), reps=300, n_flips=2000, n_resamples=500)
    b = check(_rows(), reps=300, n_flips=2000, n_resamples=500)
    assert a == b
    assert 0.025 <= a["uncorrected_rate"] <= 0.075
    assert a["holm_fwer"] <= 0.08
    assert len(report(a)) == 5


def test_needs_enough_runs():
    with pytest.raises(ValueError):
        check(_rows(100), reps=1)
