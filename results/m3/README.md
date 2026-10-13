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

## The known effect (after decisions 25–27)

| | P1, B − A |
|---|---|
| Null mock (mechanical difference) | +0.51 points (s.e. 0.04) |
| Planted mock (the truth for this check) | **+1.29 points** (s.e. 0.03) |
| Increment from the plant | **+0.78 points** |

The truth is the mean paired difference over the whole pool of 2,000 seeds.

## Result: PASS

| Check | Criterion (decisions 21, 24) | Observed |
|---|---|---|
| 95% t-interval contains the truth, n = 200 | ≥ 93% of 1,000 replications | **964 of 1,000 = 96.4%** (95% CI 95.1–97.5%) |

Power curve and coverage (1,000 replications each, paired t-intervals):

| Seeds n | Power, α = 0.05 | Power, α = 0.05/8 (Holm lower bound) | Interval coverage | Mean estimate |
|---|---|---|---|---|
| 12 | 83.4% | 45.5% | 96.2% | +1.28 |
| 25 | 99.5% | 92.6% | 94.8% | +1.28 |
| 50 | 100% | 100% | 96.0% | +1.30 |
| 100 | 100% | 100% | 96.2% | +1.29 |
| 200 | 100% | 100% | 96.8% | +1.29 |

## Reading

- **The estimate recovers the truth** without bias at every n.
- **Coverage holds down to 12 seeds** with paired t-intervals.
- **Power.** A difference of about 1.3 points on P1 is found under Holm about half the
  time at 12 seeds, and reliably from about 25 seeds per world.
- **Compared with the previous run** (truth +1.08, null −0.32, plant +1.39), the
  mechanical difference is now positive and the plant adds less. The new shocks and
  observing (decisions 26, 27) change what each world's rules face; see M4.

## History

**Second run (decisions 21, 22, 24):** truth +1.08 points (null −0.32, plant +1.39);
coverage 95.5% at n = 200 and 96.1% at n = 12. Pass.

**First run:**
The first M3 run (before decisions 21, 22 and 24) used percentile bootstrap intervals and
the criterion "at least 95 of 100 replications". It gave 93 of 100 (96.1% over 1,000)
at n = 200, and 91.6% coverage at n = 12. Those results led to decisions 21 and 24. The
grids were then regenerated, because decision 22 changed the misinformation post. The
truth and the null difference are unchanged to four decimals.
