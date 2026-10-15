# Dry run on phase M data (null mock, 20 seeds) report

`full` arm. Paired by seed; 95% t-intervals; two-sided sign-flip tests; Holm across the 8 primary tests (06 §7.2).

## Primary tests

| Contrast | Outcome | n | Estimate | 95% CI | p (Holm) | Verdict | Mechanical (M4) | Departure [approx. 95% CI] |
|---|---|---|---|---|---|---|---|---|
| B vs A | P1 | 20 | -0.10 pts | [-0.84 pts, +0.65 pts] | 0.7885 | no meaningful difference | +0.36 pts | -0.45 pts [-1.20 pts, +0.29 pts] |
| B vs A | P2 | 20 | -0.0505 | [-0.0878, -0.0132] | 0.0385 | better | -0.0567 | +0.0062 [-0.0306, +0.0431] |
| B vs A | P3 | 20 | +18.94 pts | [+15.67 pts, +22.21 pts] | 0.0000 | better | +19.90 pts | -0.96 pts [-4.29 pts, +2.37 pts] |
| B vs A | P4 | 20 | +3.09 pts | [-0.75 pts, +6.94 pts] | 0.3172 | inconclusive | +2.17 pts | +0.93 pts [-2.86 pts, +4.72 pts] |
| B vs C | P1 | 20 | -1.25 pts | [-2.11 pts, -0.39 pts] | 0.0385 | worse | -0.63 pts | -0.62 pts [-1.48 pts, +0.25 pts] |
| B vs C | P2 | 20 | -0.1261 | [-0.1764, -0.0758] | 0.0005 | better | -0.1030 | -0.0230 [-0.0726, +0.0265] |
| B vs C | P3 | 20 | +21.82 pts | [+17.07 pts, +26.57 pts] | 0.0000 | better | +20.40 pts | +1.42 pts [-3.23 pts, +6.07 pts] |
| B vs C | P4 | 20 | +2.49 pts | [-2.11 pts, +7.10 pts] | 0.5553 | inconclusive | +1.92 pts | +0.57 pts [-3.93 pts, +5.07 pts] |

The departure is the model estimate minus the null-mock estimate for the same contrast (06 §9: phase L reports departures from the mechanical baseline). Its interval is approximate: independent standard errors added in quadrature.

## Secondary contrasts (estimates only, no test)

| Contrast | Outcome | n | Estimate | 95% CI |
|---|---|---|---|---|
| A vs C | P1 | 20 | -1.15 pts | [-1.86 pts, -0.44 pts] |
| A vs C | P2 | 20 | -0.0756 | [-0.1139, -0.0373] |
| A vs C | P3 | 20 | +2.88 pts | [-1.30 pts, +7.06 pts] |
| A vs C | P4 | 20 | -0.60 pts | [-3.50 pts, +2.29 pts] |
| A vs C | S2 | 20 | -35073.3000 | [-137765.2837, +67618.6837] |
| A vs C | S6 | 20 | -0.5149 | [-0.7526, -0.2772] |

## H2: equality without collapse (S2, total output)

- B / A mean output: 0.905 (H2 needs ≥ 0.90)
- B / C mean output: 0.892 (H2 needs ≥ 0.90)

## H5: capture (S6, exploratory)

- A: mean S6 -0.180 over 20 runs
- B: mean S6 -0.261 over 20 runs
- C: mean S6 +0.335 over 20 runs

## Runs

Every planned run, including failures, is in `runs.csv`.
Seeds dropped from a contrast because a run is missing (06 §7.5): none.

Seed-level distributions: `seeds.svg`.
