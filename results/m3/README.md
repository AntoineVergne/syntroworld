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

## Result: PASS

| Check | Criterion (decisions 21, 24) | Observed |
|---|---|---|
| 95% t-interval contains the truth, n = 200 | ≥ 93% of 1,000 replications | **955 of 1,000 = 95.5%** (95% CI 94.0–96.7%) |

Power curve and coverage (1,000 replications each, paired t-intervals):

| Seeds n | Power, α = 0.05 | Power, α = 0.05/8 (Holm lower bound) | Interval coverage | Mean estimate |
|---|---|---|---|---|
| 12 | 70.0% | 30.9% | **96.1%** | +1.07 |
| 25 | 96.3% | 81.6% | 94.8% | +1.07 |
| 50 | 100% | 99.7% | 93.7% | +1.07 |
| 100 | 100% | 100% | 94.8% | +1.07 |
| 200 | 100% | 100% | 95.7% | +1.08 |

## Reading

- **The estimate recovers the plant** without bias at every n: +1.07 to +1.08 points
  against a truth of +1.08.
- **Small n is fixed.** With paired t-intervals, coverage stays near 95% down to 12 seeds
  (96.1%), where the percentile bootstrap gave 91.6%. The tests themselves are exact and
  were never affected.
- **Power.** A planted effect of about 1 point on P1 needs about 25 seeds per world to be
  found under Holm with reasonable power. At the floor of 12 it is found less than a
  third of the time.

## History

The first M3 run (before decisions 21, 22 and 24) used percentile bootstrap intervals and
the criterion "at least 95 of 100 replications". It gave 93 of 100 (96.1% over 1,000)
at n = 200, and 91.6% coverage at n = 12. Those results led to decisions 21 and 24. The
grids were then regenerated, because decision 22 changed the misinformation post. The
truth and the null difference are unchanged to four decimals.
