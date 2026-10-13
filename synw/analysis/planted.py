"""Planted-effect check (06 §8.1, step M3).

The planted mock (03 §6.4, λ > 0) makes compliance respond to the declared fairness
of the procedure that made each rule (deliberation + sortition 0.8, plenary 0.5,
wealth-weighted 0.2). So under the planted mock, P1 in World B differs from World A
by a known amount on top of the mechanical difference.

- **Truth:** the mean paired difference ``P1(B, s) − P1(A, s)`` over the whole pool of
  seeds (2,000), which is exact for the population the replications sample from.
- **Coverage (pass condition):** in at least 95 of 100 replications of ``n`` seeds
  (default 200, the phase M size), the 95% bootstrap interval contains the truth.
- **Power curve:** for each ``n``, the share of 1,000 replications in which the paired
  sign-flip test rejects at α = 0.05, and at α = 0.05 / 8 (the Bonferroni level, a
  lower bound on the Holm power for one of the 8 primary tests).
- **Decomposition** (when the null grids are given): mechanical difference under the
  null mock, and the increment the plant adds.

Seeds are drawn without replacement from the pool, so intervals are slightly
conservative (finite-population factor √(1 − n/N) ≈ 0.95 at n = 200 of 2,000).

    python -m synw.analysis.planted --planted-b results/m3/grid-b-full-planted.jsonl \\
        --planted-a results/m3/grid-a-full-planted.jsonl \\
        --null-b results/m2/grid-b-full-2000.jsonl --null-a results/m3/grid-a-full-null.jsonl
"""

import argparse
import json
import sys

from .false_positive import _np, bootstrap_ci, sign_flip_p
from .grid import read_rows


def paired(rows_t, rows_c, outcome="P1"):
    np = _np()
    t = {r["seed"]: r[outcome] for r in rows_t if r.get(outcome) is not None}
    c = {r["seed"]: r[outcome] for r in rows_c if r.get(outcome) is not None}
    seeds = sorted(set(t) & set(c))
    return seeds, np.array([t[s] - c[s] for s in seeds], dtype=float)


def check(planted_b, planted_a, null_b=None, null_a=None, outcome="P1", coverage_n=200,
          coverage_reps=100, ns=(12, 25, 50, 100, 200), power_reps=1000, seed=20261013,
          n_flips=100000, n_resamples=10000):
    np = _np()
    rng = np.random.default_rng(seed)
    seeds, d = paired(planted_b, planted_a, outcome)
    N = len(d)
    truth = float(d.mean())
    res = {"outcome": outcome, "pool": N, "truth": truth, "truth_se": float(d.std(ddof=1) / N ** 0.5),
           "sd_d": float(d.std(ddof=1))}
    if null_b is not None and null_a is not None:
        _, d0 = paired(null_b, null_a, outcome)
        res["null_difference"] = float(d0.mean())
        res["null_se"] = float(d0.std(ddof=1) / len(d0) ** 0.5)
        res["planted_increment"] = truth - res["null_difference"]

    def covered(n, reps):
        hits = 0
        for _ in range(reps):
            x = d[rng.choice(N, size=n, replace=False)][:, None]
            lo, hi = bootstrap_ci(x, n_resamples, rng)
            hits += bool(lo[0] <= truth <= hi[0])
        return hits

    hits = covered(coverage_n, coverage_reps)
    res["coverage"] = {"n": coverage_n, "reps": coverage_reps, "covered": hits,
                       "pass": hits >= int(0.95 * coverage_reps)}
    curve = []
    for n in ns:
        rej05 = rej_b = cov = 0
        est = []
        for _ in range(power_reps):
            x = d[rng.choice(N, size=n, replace=False)][:, None]
            p = float(sign_flip_p(x, n_flips, rng)[0])
            rej05 += p <= 0.05
            rej_b += p <= 0.05 / 8
            lo, hi = bootstrap_ci(x, n_resamples, rng)
            cov += bool(lo[0] <= truth <= hi[0])
            est.append(float(x.mean()))
        curve.append({"n": n, "reps": power_reps, "power_05": rej05 / power_reps,
                      "power_bonferroni": rej_b / power_reps, "coverage": cov / power_reps,
                      "mean_estimate": sum(est) / len(est)})
    res["power_curve"] = curve
    return res


def report(res):
    y = res["outcome"]
    lines = [f"planted-effect check on {y}: pool of {res['pool']} paired seeds (B vs A, planted mock)",
             f"      truth (pool mean of d): {res['truth']:+.4f}  (s.e. {res['truth_se']:.4f}; sd of d {res['sd_d']:.4f})"]
    if "planted_increment" in res:
        lines.append(f"      null-mock difference: {res['null_difference']:+.4f} (s.e. {res['null_se']:.4f}); "
                     f"planted increment: {res['planted_increment']:+.4f}")
    c = res["coverage"]
    lines.append(f"{'PASS' if c['pass'] else 'FAIL'}  interval contains the truth in >= 95% of {c['reps']} "
                 f"replications (n = {c['n']}): {c['covered']} of {c['reps']}")
    lines.append("      n     power(a=.05)  power(a=.05/8)  coverage  mean estimate")
    for r in res["power_curve"]:
        lines.append(f"      {r['n']:<5d} {r['power_05']:>10.1%}  {r['power_bonferroni']:>13.1%}  "
                     f"{r['coverage']:>8.1%}  {r['mean_estimate']:+.4f}")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="06 step M3: planted-effect check")
    ap.add_argument("--planted-b", required=True)
    ap.add_argument("--planted-a", required=True)
    ap.add_argument("--null-b")
    ap.add_argument("--null-a")
    ap.add_argument("--outcome", default="P1")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--power-reps", type=int, default=1000)
    ap.add_argument("--ns", default="12,25,50,100,200")
    ap.add_argument("--seed", type=int, default=20261013)
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    res = check(read_rows(args.planted_b), read_rows(args.planted_a),
                read_rows(args.null_b) if args.null_b else None,
                read_rows(args.null_a) if args.null_a else None,
                args.outcome, args.n, args.reps, tuple(int(x) for x in args.ns.split(",")),
                args.power_reps, args.seed)
    for line in report(res):
        print(line)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, sort_keys=True)
    return 0 if res["coverage"]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
