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

## Result (after decisions 25–27): FAIL as written

| Check | Criterion (decision 21) | Observed |
|---|---|---|
| Uncorrected rejection rate (8,000 tests) | 3% to 7% | **4.78%** (s.e. 0.24%), pass |
| Holm family-wise rate (1,000 replications) | upper bound of exact 95% interval ≤ 7% | **5.80%**, 95% CI 4.43–7.43%: **fail** |

By outcome (uncorrected): P1 4.95%, P2 4.90%, P3 4.00%, P4 5.25%. False "better" or
"worse" verdicts: 0.76% of tests.

**Why this is not evidence of a broken test.** Holm controls the family-wise rate at or
below 5% under any dependence between tests, and every per-outcome rate is at or near
5%. The observed 5.80% (58 of 1,000) is within noise. If the true rate is 4.89% (Holm
on 8 independent tests), 58 or more happens about 11% of the time.

**The criterion is poorly calibrated, and the fault is mine.** I proposed "upper bound
≤ 7%" when decision 21 was taken. At 1,000 replications it fails whenever 55 or more
replications reject, which a correct procedure does 20–25% of the time. A
well-calibrated version is "the 95% interval includes 5%" (that is, the lower bound is
at most 5%). It fails a correct procedure about 2.5% of the time, and this run passes
it (lower bound 4.43%). I did not change the agreed criterion or re-run with another
seed. See decisions.md, question 29.

## Previous run (after decisions 21, 22 and 24)

Uncorrected 5.29%; Holm 4.50% (95% CI 3.30–5.98%): pass.

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
The tests behave as designed: the uncorrected rate is at its nominal 5%, and every
outcome is close to it. The Holm rate is within noise of its expected value:

- Holm on 8 independent tests at α = 0.05 has an expected family-wise rate of
  1 − (1 − 0.05/8)⁸ = **4.89%**.
- The 95% exact interval for the observed rate is **3.9% to 6.8%**. It contains both
  4.89% and 5%.
- With 1,000 replications, a procedure whose true rate is 4.89% would show more than
  5.0% about **40%** of the time.

So the "≤ 5%" criterion, applied to a 1,000-replication estimate, fails a correct
procedure close to half the time. The fail is a property of how the criterion is
written, not evidence that the statistics are wrong. I did not re-run with other
seeds: choosing a replication seed after seeing a fail would defeat the check.

**Open question for Antoine (protocol amendment, 06 §8.1):** restate the M2 family-wise
criterion with its Monte Carlo error, for example "the upper 95% bound of the
family-wise rate is at most 7%" or "the rate is at most 5% + 2 s.e.". Alternatively,
keep "≤ 5%" and raise the replication count. Even 10,000 replications (s.e. 0.22%)
would still fail a procedure sitting exactly at 5% about half the time. Until
then, M2 is recorded as **failed as written, consistent with nominal**.

**Resolved (decision 21, 2026-10-13):** Antoine restated the criterion as "the upper
bound of the 95% interval on the family-wise rate is at most 7%", before the freeze.
The observed interval is 3.9–6.8%, so **M2 passes**. No run was repeated.
