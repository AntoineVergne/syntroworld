"""False-positive check (06 §8.1, step M2).

World B, ``full`` arm, 2,000 seeds, run once (``synw.analysis.grid``). Then, 1,000 times:
draw 400 seeds without replacement, pair them at random into two pseudo-contrasts of
100 pairs each, and run the paired analysis of 06 §7.2 on all four primary outcomes, as
if each pair were two worlds. There is no true difference, so:

- the uncorrected rejection rate (p ≤ 0.05) must lie within 3% to 7%;
- the Holm family-wise rejection rate (any of the 8 tests rejected) must be ≤ 5%.

The tests are those of ``synw.analysis.compare``: a two-sided sign-flip test, exact up
to 20 pairs, otherwise 100,000 random flips; Holm across the 8 tests; 95% percentile
bootstrap intervals (10,000 resamples) for the verdicts. Within one replication, the
8 tests share the same random flips and bootstrap resamples. This only correlates their
Monte Carlo noise; each test is still the stated test.

numpy is required here (``pip install -e ".[analysis]"``); the engine itself does not
use it.

    python -m synw.analysis.false_positive --grid results/m2/grid-b-full-2000.jsonl
"""

import argparse
import itertools
import json
import sys

from .compare import ALPHA, BETTER, SESOI, holm, verdict
from .grid import read_rows

OUTCOMES = ("P1", "P2", "P3", "P4")


def _np():
    try:
        import numpy as np
    except ImportError:  # pragma: no cover
        raise SystemExit("the false-positive check needs numpy: pip install -e '.[analysis]'")
    return np


def sign_flip_p(D, n_flips=100000, rng=None, exact_max=20, chunk=20000):
    """Two-sided sign-flip p-values for each column of ``D`` (n pairs × k tests).

    Exact up to ``exact_max`` pairs; otherwise ``n_flips`` random flips plus the identity,
    p = (1 + #|T*| ≥ |T|) / (n_flips + 1).
    """
    np = _np()
    D = np.asarray(D, dtype=float)
    n, k = D.shape
    T = np.abs(D.sum(axis=0))
    thr = T - 1e-9 * np.maximum(1.0, T)
    if n <= exact_max:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=n)))
        S = np.abs(signs @ D)
        p = (S >= thr).sum(axis=0) / len(signs)
        return np.where(T > 0, p, 1.0)
    hits = np.zeros(k)
    left = n_flips
    while left > 0:
        m = min(chunk, left)
        signs = rng.integers(0, 2, size=(m, n), dtype=np.int8) * 2 - 1
        S = np.abs(signs.astype(float) @ D)
        hits += (S >= thr).sum(axis=0)
        left -= m
    p = (hits + 1) / (n_flips + 1)
    return np.where(T > 0, p, 1.0)


def bootstrap_ci(D, n_resamples=10000, rng=None, level=0.95):
    """Percentile bootstrap interval of the mean, for each column of ``D``."""
    np = _np()
    D = np.asarray(D, dtype=float)
    n = D.shape[0]
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = np.sort(D[idx].mean(axis=1), axis=0)
    lo_q = (1 - level) / 2
    lo = means[int(lo_q * n_resamples)]
    hi = means[min(n_resamples - 1, int((1 - lo_q) * n_resamples) - 1)]
    return lo, hi


def load_outcomes(rows, outcomes=OUTCOMES):
    """Seeds with every outcome present, and their values per outcome."""
    np = _np()
    keep = [r for r in rows if all(r.get(y) is not None for y in outcomes)]
    keep.sort(key=lambda r: r["seed"])
    return [r["seed"] for r in keep], {y: np.array([r[y] for r in keep], dtype=float) for y in outcomes}


def check(rows, reps=1000, draw=400, contrasts=2, seed=20261012, n_flips=100000,
          n_resamples=10000, outcomes=OUTCOMES, alpha=ALPHA):
    np = _np()
    rng = np.random.default_rng(seed)
    seeds, vals = load_outcomes(rows, outcomes)
    N = len(seeds)
    if N < draw:
        raise ValueError(f"need at least {draw} complete runs, have {N}")
    per = draw // (2 * contrasts)          # pairs per pseudo-contrast
    labels = [(c, y) for c in range(contrasts) for y in outcomes]
    rej = np.zeros(len(labels))
    fwer = 0
    false_verdicts = 0
    for _ in range(reps):
        idx = rng.choice(N, size=draw, replace=False)
        cols = []
        for c in range(contrasts):
            a = idx[2 * c * per:(2 * c + 1) * per]
            b = idx[(2 * c + 1) * per:(2 * c + 2) * per]
            for y in outcomes:
                cols.append(vals[y][a] - vals[y][b])
        D = np.stack(cols, axis=1)
        p = sign_flip_p(D, n_flips, rng)
        rej += p <= alpha
        adj = holm([float(x) for x in p])
        if min(adj) <= alpha:
            fwer += 1
        lo, hi = bootstrap_ci(D, n_resamples, rng)
        est = D.mean(axis=0)
        for j, (c, y) in enumerate(labels):
            v = verdict(float(est[j]), (float(lo[j]), float(hi[j])), adj[j], SESOI[y], BETTER[y], alpha)
            if v in ("better", "worse"):
                false_verdicts += 1
    tests = reps * len(labels)
    unc = float(rej.sum() / tests)
    fw = fwer / reps
    by_outcome = {y: float(sum(rej[j] for j, (c, yy) in enumerate(labels) if yy == y) / (reps * contrasts))
                  for y in outcomes}
    return {
        "runs": N, "reps": reps, "draw": draw, "pairs_per_contrast": per, "contrasts": contrasts,
        "tests": tests, "uncorrected_rate": unc, "uncorrected_by_outcome": by_outcome,
        "holm_fwer": fw, "false_verdict_rate": false_verdicts / tests,
        "pass_uncorrected": 0.03 <= unc <= 0.07, "pass_fwer": fw <= 0.05,
        "seed": seed, "n_flips": n_flips, "n_resamples": n_resamples,
    }


def report(res):
    se_u = (0.05 * 0.95 / res["tests"]) ** 0.5
    se_f = (0.05 * 0.95 / res["reps"]) ** 0.5
    lines = [
        f"false-positive check: {res['runs']} runs, {res['reps']} replications x "
        f"{res['contrasts']} pseudo-contrasts x {len(res['uncorrected_by_outcome'])} outcomes "
        f"({res['pairs_per_contrast']} pairs each)",
        f"{'PASS' if res['pass_uncorrected'] else 'FAIL'}  uncorrected rejection rate in 3%..7%: "
        f"{res['uncorrected_rate']:.2%} (binomial s.e. at 5%: {se_u:.2%})",
        f"{'PASS' if res['pass_fwer'] else 'FAIL'}  Holm family-wise rejection rate <= 5%: "
        f"{res['holm_fwer']:.2%} (s.e. at 5%: {se_f:.2%})",
        "      by outcome (uncorrected): " + ", ".join(f"{y} {v:.2%}" for y, v in res["uncorrected_by_outcome"].items()),
        f"      false 'better'/'worse' verdicts: {res['false_verdict_rate']:.2%} of tests",
    ]
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="06 step M2: false-positive check on a World B grid")
    ap.add_argument("--grid", required=True, help="rows from synw.analysis.grid (World B, full arm)")
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--draw", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20261012)
    ap.add_argument("--flips", type=int, default=100000)
    ap.add_argument("--resamples", type=int, default=10000)
    ap.add_argument("--json", help="also write the result as JSON here")
    args = ap.parse_args(argv)
    res = check(read_rows(args.grid), args.reps, args.draw, seed=args.seed, n_flips=args.flips,
                n_resamples=args.resamples)
    for line in report(res):
        print(line)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, sort_keys=True)
    return 0 if res["pass_uncorrected"] and res["pass_fwer"] else 1


if __name__ == "__main__":
    sys.exit(main())
