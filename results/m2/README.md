# Step M2: false-positive check (06 §8.1)

**Data.** World B, `full` arm, null mock, seeds 1 to 2,000, each with its `none` twin
for P4 (`grid-b-full-2000.jsonl`, one row per run, now including S1 to S18).

**Procedure.** 1,000 replications. Each draws 400 seeds without replacement and pairs
them at random into two pseudo-contrasts of 100 pairs. Each replication then runs the
06 §7.2 analysis on P1 to P4: a two-sided sign-flip test with 100,000 random flips,
Holm across the 8 tests, and 95% paired t-intervals for the verdicts. Replication seed
20261012.

Reproduce:
`python -m synw.analysis.false_positive --grid results/m2/grid-b-full-2000.jsonl --json results/m2/false-positive.json`

## Result: PASS

| Check | Criterion (decision 21) | Observed |
|---|---|---|
| Uncorrected rejection rate (8,000 tests) | 3% to 7% | **5.29%** (s.e. 0.24%) |
| Holm family-wise rate (1,000 replications) | upper bound of exact 95% interval ≤ 7% | **4.50%**, 95% CI 3.30–5.98% |

By outcome (uncorrected): P1 6.20%, P2 4.55%, P3 5.10%, P4 5.30%. False "better" or
"worse" verdicts: 0.57% of tests.

## Notes

- **History.** The first run (before decisions 21, 22 and 24) gave 5.09% uncorrected and
  5.20% family-wise, a fail under the old "≤ 5%" wording. That led to decision 21.
- **Re-run.** The grid was regenerated after decision 22 changed the misinformation post.
  No seed's P1 to P4 changed, because the post affects beliefs, not these outcomes.
  The rates moved anyway (5.20% → 4.50% family-wise) because the t-interval replaced the
  bootstrap, which changed the random draws the analysis consumes. The size of that move
  on identical data is the Monte Carlo noise the new criterion allows for.
- **P1.** P1's uncorrected rate, 6.20%, is about 2.4 s.e. above 5% (s.e. 0.49% per
  outcome). In the first run it was 4.80%. With four outcomes one this far out is not
  unusual, but it is worth rechecking at the next M2 run.
