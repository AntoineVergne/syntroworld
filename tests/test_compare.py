import pytest

from synw.analysis.compare import (analyse, bootstrap_ci, holm, paired_differences, sign_flip_p,
                                   verdict)


def test_min_exact_p_for_8_seeds():
    d = [0.1, 0.2, 0.3, 0.15, 0.25, 0.05, 0.4, 0.12]
    assert sign_flip_p(d) == pytest.approx(2 / 256)
    assert 2 / 256 > 0.05 / 8   # why 8 seeds can never pass Holm's first threshold (06 §7.3)


def test_sign_flip_null_and_exact_counts():
    assert sign_flip_p([0.0, 0.0, 0.0]) == 1.0
    p = sign_flip_p([1.0, -1.0, 1.0, -1.0])
    assert p == pytest.approx(1.0)
    # brute force agreement on a small case
    import itertools
    d = [0.3, -0.1, 0.5, 0.2, -0.4, 0.7]
    T = abs(sum(d))
    brute = sum(1 for s in itertools.product((1, -1), repeat=6)
                if abs(sum(a * b for a, b in zip(s, d))) >= T - 1e-12) / 64
    assert sign_flip_p(d) == pytest.approx(brute)


def test_random_flips_beyond_20_seeds_are_seeded():
    d = [0.01 * (i % 7 - 2) for i in range(25)]
    assert sign_flip_p(d, seed=3, n_random=2000) == sign_flip_p(d, seed=3, n_random=2000)


def test_holm_known_values():
    assert holm([0.01, 0.04, 0.03, 0.005]) == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert holm([0.5]) == [0.5]


def test_bootstrap_reproducible_and_brackets_mean():
    d = [0.1, 0.3, -0.2, 0.4, 0.0, 0.25, 0.15, 0.05]
    a = bootstrap_ci(d, 2000, seed=9)
    assert a == bootstrap_ci(d, 2000, seed=9)
    assert a[0] < sum(d) / len(d) < a[1]


def test_paired_by_seed_drops_missing():
    t = [{"world": "B", "seed": 1, "P1": 0.9}, {"world": "A", "seed": 1, "P1": 0.8},
         {"world": "B", "seed": 2, "P1": 0.7}, {"world": "A", "seed": 2, "P1": None},
         {"world": "B", "seed": 3, "P1": 0.5}]
    assert paired_differences(t, "B", "A", "P1") == [(1, pytest.approx(0.1))]


def test_verdicts():
    assert verdict(0.1, (0.05, 0.15), 0.01, 0.05, "higher") == "better"
    assert verdict(0.1, (0.05, 0.15), 0.01, 0.05, "lower") == "worse"
    assert verdict(0.01, (-0.02, 0.03), 0.5, 0.05) == "no meaningful difference"
    assert verdict(0.04, (-0.02, 0.09), 0.5, 0.05) == "inconclusive"
    assert verdict(0.1, (0.05, 0.15), 0.2, 0.05) == "inconclusive"


def test_analyse_identical_across_calls():
    table = []
    for s in range(1, 13):
        for w, shift in (("A", 0.0), ("B", 0.08), ("C", -0.02)):
            table.append({"world": w, "seed": s, "P1": 0.8 + shift + 0.01 * (s % 3),
                          "P2": 0.3 - shift / 2, "P3": 0.5, "P4": 0.1 + 0.001 * s})
    a = analyse(table, n_resamples=2000, seed=7)
    b = analyse(table, n_resamples=2000, seed=7)
    assert a == b
    assert len(a) == 8
    p1 = [r for r in a if r["outcome"] == "P1" and r["contrast"] == "B vs A"][0]
    assert p1["verdict"] == "better" and p1["p"] == pytest.approx(2 / 4096)
    p3 = [r for r in a if r["outcome"] == "P3"][0]
    assert p3["verdict"] == "no meaningful difference"
