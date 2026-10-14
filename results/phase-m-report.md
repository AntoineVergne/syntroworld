# Phase M report (06 §10, output 1)

**Mechanical baseline (null mock), not findings about AI agents.** Every number here
comes from a rule-based mock brain that reads no text (03 §6.2). It shows what the
institutions do by their mechanics alone, and whether the measurement pipeline works.

Engine 1.0.0, decisions 1 to 31, frozen with docs 01 to 06 (`FREEZE.md`). Each step has
its own README with the full tables and the history of earlier runs.

## Summary

| Step | What | Pass condition (06 §8.1) | Result |
|---|---|---|---|
| M0 | Determinism: A, B, C × `none`, `full` × seeds 1–20, twice | identical log hashes; shocks identical across worlds | **PASS**: 120/120; 40/40 |
| M1 | Calibration: A, null mock, 200 seeds | every 03 §10.2 target; no primary outcome at floor or ceiling | **PASS**: 10/10 |
| M2 | False positives: B, 2,000 seeds, 1,000 null replications | uncorrected 3–7%; Holm interval includes 5% | **PASS**: 4.72%; 3.30% [2.28, 4.60] |
| M3 | Planted effect: planted mock, 1,000 replications | 95% interval covers the truth ≥ 93% at 200 seeds | **PASS**: 95.8% |
| M4 | Mechanical baseline: 4,900 runs | report produced and labelled | **Done** |

## M0 Determinism (`results/m0/`)

- 120 of 120 runs give byte-identical event logs across two passes with different
  `PYTHONHASHSEED`.
- For each seed and arm, the drought, misinformation targets, rogue schedule, Sam's
  arrival and the forged posts are identical in A, B and C (common random numbers).
- The rogue was replaced in 6 of 60 `full` runs because the scheduled citizen had left
  (decision 28).

## M1 Calibration (`results/m1/calibration-a-200.txt`)

| Target (03 §10.2) | Value |
|---|---|
| Median Gini rise, day 1 to 24 ≥ 0.10 | 0.229 |
| Runs with the River below K/2 at some point, 30–70% | 45% |
| Basket floor S1 (median), 70–95% | 92.9% |
| Founding-norm compliance S4 (median), 85–98% | 96.7% |
| Runs with a death or exit, 10–50%; median ≤ 1 | 35%; 0 |
| Runs with harm S18 > 0, ≥ 80% | 100% |
| Drought output loss on its days, ≥ 10% | 48.2% |
| Full-arm P4 (median), 10–20% | 18.0% |
| Seeds at 0 or 1 for P1–P4, ≤ 10% each | 0% each |
| Slowest run, < 10 s | 0.83 s |

Calibration changed River r, S0, founders' credits and the shock strength
(`calibration-log.md`).

## M2 False positives (`results/m2/`)

- 1,000 replications of 2 pseudo-contrasts × 4 outcomes on null pairs (no true
  difference). The uncorrected rejection rate is 4.72% (P1 4.70, P2 4.85, P3 4.70,
  P4 4.65).
- The Holm family-wise rate is 3.30% [2.28, 4.60]: conservative, as expected with
  correlated outcomes. False "better" or "worse" verdicts occur in 0.41% of tests.

## M3 Planted effect (`results/m3/`)

- The planted mock makes compliance respond to procedural fairness. The truth is
  B − A P1 = +1.31 points, against +0.41 points with the null mock.
- At 200 seeds the 95% t-interval covers the truth in 95.8% of 1,000 replications
  (95.0% at 12 seeds).
- Power to detect the planted difference (α = 0.05): 85% at 12 seeds, 99% at 25, 100% from 50
  (`planted.txt`).

## M4 Mechanical baseline (`results/m4/`)

Primary contrasts, `full` arm, 200 paired seeds, Holm across 8 tests:

| | B vs A | B vs C | SESOI |
|---|---|---|---|
| P1 compliance | +0.36 pts | −0.63 pts | 5 pts |
| P2 wealth Gini | −0.057 | −0.103 | 0.05 |
| P3 civic breadth | +19.9 pts | +20.4 pts | 10 pts |
| P4 output loss | +2.17 pts | +1.92 pts | 5 pts |

What the mechanics alone do:

- **Equality (P2).** B is less unequal than A and C, by more than the 0.05 SESOI against both.
  The dividend (−0.022) and stipends (−0.016) are what matter. In C, wealth-weighted
  votes raise inequality.
- **Participation (P3).** B's lead is mechanical: it draws 8 seats per cycle, and a seat
  counts once per cycle (decision 31). A plenary does the same (B-nolot equals B).
  Phase L must beat this baseline, not zero.
- **Compliance (P1).** The differences are under 1 point: the mock reacts only to
  rules, sanctions and detection.
- **Resilience (P4).** B loses about 2 points more output under shocks, well below the
  SESOI. The time spent at the Hall is the cost.
- **Commons and capture.** B keeps the River at or above K/2 on 89% of window days,
  against 50% in A and 36% in C. Capture (S6) is +0.35 in C only.
- **Ablations.** Advocates change nothing mechanically. Without the lottery (B-nolot), P2 is
  0.011 lower and P4 1.3 points lower than in B.
- **Size check (40 citizens).** The same signs hold: B40 vs A40 P2 −0.054, P3 +12.2,
  P4 +3.0 points. Departures under shocks: B40 0.18 deaths and 1.10 exits per run, A40
  0.22 and 1.06, C40 1.08 and 3.84.

## What this means for phase L

- The pipeline detects a known effect of about 1 point in P1 with 50 seeds per world,
  and its false-positive rate is at or below nominal.
- Phase L results are read as departures from the M4 numbers (06 §9). Above all, a B
  advantage in P3 matters only beyond the mechanical +20 points.
- The A+text control (`worlds/a-text.yaml`) is ready. It runs like A under the mock.
- Next is step L0: World B, 1 seed, 1 cycle, with a model. It needs Antoine's yes and a
  cost estimate (`python -m synw.analysis.cost --step L0`).

*Mechanical baseline (null mock), not findings about AI agents.*
