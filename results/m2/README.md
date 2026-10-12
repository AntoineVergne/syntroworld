# Step M2: false-positive check (06 §8.1)

**Data.** World B, `full` arm, null mock, seeds 1 to 2,000, each with its `none` twin
for P4 (`grid-b-full-2000.jsonl`, one row per run). All 2,000 runs completed.

**Procedure.** 1,000 replications. Each draws 400 seeds without replacement and pairs
them at random into two pseudo-contrasts of 100 pairs. Each replication then runs the
06 §7.2 analysis on P1 to P4: a two-sided sign-flip test with 100,000 random flips,
Holm across the 8 tests, and 95% bootstrap intervals for the verdicts. Replication
seed 20261012.

Reproduce:
`python -m synw.analysis.false_positive --grid results/m2/grid-b-full-2000.jsonl --json results/m2/false-positive.json`

## Result

| Check | Criterion | Observed | Monte Carlo s.e. | Verdict as written |
|---|---|---|---|---|
| Uncorrected rejection rate (8,000 tests) | 3% to 7% | **5.09%** | 0.24% | pass |
| Holm family-wise rate (1,000 replications) | ≤ 5% | **5.20%** (52 of 1,000) | 0.69% | **fail by 0.2 points** |

By outcome (uncorrected): P1 4.80%, P2 5.30%, P3 5.20%, P4 5.05%. False "better" or
"worse" verdicts: 0.69% of tests.

## Reading

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
