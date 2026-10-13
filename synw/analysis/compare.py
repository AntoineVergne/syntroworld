"""Paired comparison statistics (06 §7).

- Unit of analysis: the run. Pairing: by seed, ``d_s = Y(B, s) − Y(A, s)``.
- Estimate: mean of ``d_s``. Interval: 95% paired t-interval on ``d_s``
  (Antoine's decision 24: the percentile bootstrap covered only 91.6% at 12 seeds in
  step M3). ``bootstrap_ci`` is kept for comparison.
- Test: two-sided sign-flip permutation test on ``d_s``; exact up to 20 seeds, otherwise
  100,000 random flips with a fixed seed.
- Multiplicity: Holm across the primary tests, family-wise α = 0.05.
- Verdict: "better"/"worse" when Holm-significant and the interval excludes zero;
  "no meaningful difference" when the whole interval lies within ±SESOI; otherwise
  "inconclusive".
"""

import bisect
import itertools
import math
import random

ALPHA = 0.05
SESOI = {"P1": 0.05, "P2": 0.05, "P3": 0.10, "P4": 0.05}
BETTER = {"P1": "higher", "P2": "lower", "P3": "higher", "P4": "lower"}
_EPS = 1e-9


def paired_differences(table, treat, control, outcome):
    """``table``: rows ``{"world", "seed", <outcome>: value}``. Returns [(seed, d)] sorted by seed.

    Seeds missing (or with a missing value) in either world are dropped.
    """
    by = {}
    for r in table:
        by.setdefault((r["world"], r["seed"]), r)
    seeds = sorted({s for (w, s) in by if w == treat} & {s for (w, s) in by if w == control})
    out = []
    for s in seeds:
        a, b = by[(treat, s)].get(outcome), by[(control, s)].get(outcome)
        if a is None or b is None:
            continue
        out.append((s, a - b))
    return out


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def _betacf(a, b, x):
    """Continued fraction for the regularized incomplete beta (modified Lentz)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t >= 0 else tail


def t_quantile(q, df):
    """Quantile of Student's t with ``df`` degrees of freedom (bisection on the exact CDF)."""
    if q == 0.5:
        return 0.0
    if q < 0.5:
        return -t_quantile(1.0 - q, df)
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < q:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def t_interval(d, level=0.95):
    """Paired t-interval for the mean of ``d``; (None, None) below 2 values."""
    n = len(d)
    if n < 2:
        return (None, None)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    half = t_quantile(1 - (1 - level) / 2, n - 1) * sd / math.sqrt(n)
    return (m - half, m + half)


def beta_quantile(q, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def binom_ci(k, n, level=0.95):
    """Exact (Clopper-Pearson) interval for a binomial proportion k / n."""
    a = (1 - level) / 2
    lo = 0.0 if k == 0 else beta_quantile(a, k, n - k + 1)
    hi = 1.0 if k == n else beta_quantile(1 - a, k + 1, n - k)
    return (lo, hi)


def bootstrap_ci(d, n_resamples=10000, seed=12345, level=0.95):
    if not d:
        return (None, None)
    rng = random.Random(seed)
    n = len(d)
    means = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_resamples))
    lo_q = (1 - level) / 2
    lo = means[int(lo_q * n_resamples)]
    hi = means[min(n_resamples - 1, int((1 - lo_q) * n_resamples) - 1)]
    return (lo, hi)


def _half_sums(xs):
    sums = [0.0]
    for x in xs:
        sums = [s + x for s in sums] + [s - x for s in sums]
    return sums


def sign_flip_p(d, exact_max=20, n_random=100000, seed=12345):
    """Two-sided sign-flip permutation p-value for mean(d) = 0 (identity flip included)."""
    n = len(d)
    if n == 0:
        return None
    T = abs(sum(d))
    thr = T - _EPS * max(1.0, T)
    if n <= exact_max:
        h = n // 2
        left = _half_sums(d[:h])
        right = sorted(_half_sums(d[h:]))
        count = 0
        m = len(right)
        for s in left:
            # |s + r| >= thr  <=>  r >= thr - s  or  r <= -thr - s
            count += m - bisect.bisect_left(right, thr - s)
            if thr > 0:
                count += bisect.bisect_right(right, -thr - s)
            else:
                count -= 0
        if thr <= 0:
            return 1.0
        return count / (2 ** n)
    rng = random.Random(seed)
    hits = 1
    for _ in range(n_random):
        s = sum(x if rng.random() < 0.5 else -x for x in d)
        if abs(s) >= thr:
            hits += 1
    return hits / (n_random + 1)


def holm(pvals):
    """Holm step-down adjusted p-values, in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def verdict(estimate, ci, p_adj, sesoi, better="higher", alpha=ALPHA):
    lo, hi = ci
    if estimate is None or lo is None:
        return "missing"
    if p_adj is not None and p_adj <= alpha and (lo > 0 or hi < 0):
        good = (estimate > 0) == (better == "higher")
        return "better" if good else "worse"
    if -sesoi <= lo and hi <= sesoi:
        return "no meaningful difference"
    return "inconclusive"


def analyse(table, contrasts=(("B", "A"), ("B", "C")), outcomes=("P1", "P2", "P3", "P4"),
            sesoi=None, better=None, seed=12345):
    """Run the full paired analysis; Holm is applied across all contrast × outcome tests."""
    sesoi = dict(SESOI, **(sesoi or {}))
    better = dict(BETTER, **(better or {}))
    rows = []
    for (t, c), y in itertools.product(contrasts, outcomes):
        pairs = paired_differences(table, t, c, y)
        d = [x for _, x in pairs]
        rows.append({"contrast": f"{t} vs {c}", "outcome": y, "n": len(d), "estimate": mean(d),
                     "ci": t_interval(d), "p": sign_flip_p(d, seed=seed)})
    ps = [r["p"] if r["p"] is not None else 1.0 for r in rows]
    for r, pa in zip(rows, holm(ps)):
        r["p_holm"] = pa
        r["verdict"] = verdict(r["estimate"], r["ci"], pa, sesoi[r["outcome"]], better[r["outcome"]])
    return rows


def format_rows(rows):
    lines = []
    for r in rows:
        lo, hi = r["ci"]
        est = "NA" if r["estimate"] is None else f"{r['estimate']:+.4f}"
        ci = "NA" if lo is None else f"[{lo:+.4f}, {hi:+.4f}]"
        lines.append(f"{r['contrast']:8s} {r['outcome']}  n={r['n']:3d}  est={est}  95%CI={ci}  "
                     f"p={r['p'] if r['p'] is not None else 'NA'}  p_holm={r['p_holm']:.4f}  {r['verdict']}")
    return "\n".join(lines)
