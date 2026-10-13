# Step M3: planted effects (06 §8.1)

**Data** (World A or B, `full` arm, seeds 1 to 2,000):

| File | World | Mock |
|---|---|---|
| `grid-b-full-planted.jsonl` | B | planted, λ = 1 |
| `grid-a-full-planted.jsonl` | A | planted, λ = 1 |
| `grid-a-full-null.jsonl` | A | null |
| `../m2/grid-b-full-2000.jsonl` (reused) | B | null |

The planted mock makes compliance respond to the declared fairness of the procedure
behind each rule: a drawn body 0.8, a plenary 0.5 (03 §6.4). Spot checks re-ran rows
from each grid with the final code; the state hashes were identical.

Reproduce:
```
python -m synw.analysis.planted --planted-b results/m3/grid-b-full-planted.jsonl \
  --planted-a results/m3/grid-a-full-planted.jsonl \
  --null-b results/m2/grid-b-full-2000.jsonl --null-a results/m3/grid-a-full-null.jsonl \
  --json results/m3/planted.json
```

## The known effect

| | P1, B − A |
|---|---|
| Null mock (mechanical difference) | −0.32 points (s.e. 0.04) |
| Planted mock (the truth for this check) | **+1.08 points** (s.e. 0.03) |
| Increment from the plant | **+1.39 points** |

The truth is the mean paired difference over the whole pool of 2,000 seeds. The
planted effect is smaller than the P1 SESOI of 5 points.

## Result

| Check | Criterion | Observed | Verdict as written |
|---|---|---|---|
| 95% interval contains the truth, n = 200 | ≥ 95 of 100 replications | **93 of 100** | **fail** |
| Same intervals, n = 200 | (1,000 replications, for stability) | 96.1% | — |

Power curve and coverage (1,000 replications each):

| Seeds n | Power, α = 0.05 | Power, α = 0.05/8 (Holm lower bound) | Interval coverage | Mean estimate |
|---|---|---|---|---|
| 12 | 70.1% | 31.0% | **91.6%** | +1.08 |
| 25 | 97.7% | 84.5% | 94.4% | +1.09 |
| 50 | 100% | 99.6% | 95.1% | +1.07 |
| 100 | 100% | 100% | 95.7% | +1.08 |
| 200 | 100% | 100% | 96.1% | +1.07 |

## Reading

- **The estimate recovers the plant.** The mean estimate is +1.07 to +1.09 points at
  every n, against a truth of +1.08, so there is no bias.
- **The 93/100 fail is mostly the criterion.** Over 1,000 replications the n = 200
  interval covers 96.1%, slightly above nominal, as expected when sampling 200 of 2,000
  seeds without replacement. With 100 replications, an interval with exactly 95%
  coverage reaches 95 of 100 only 62% of the time; one with 96.1% reaches it 80% of the
  time. Seeing 93 or fewer has a probability of about 10% at 96.1%. As with M2, I did
  not re-run with another seed.
- **Small n is a real problem.** At 12 seeds, the phase L floor (06 §7.4), percentile
  bootstrap intervals cover only 91.6%. That is far below 95% (p ≈ 4×10⁻⁶ over 1,000
  replications). Intervals that are too narrow make "no meaningful difference" verdicts
  too easy. The tests themselves are exact and unaffected; only the intervals are.
- **Power.** A planted effect of about 1 point on P1 needs about 25 seeds per world to be
  found under Holm with reasonable power. At the floor of 12 it is found less than a
  third of the time.

See decisions.md, question 24.
