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

## The known effect (after decisions 25–30)

| | P1, B − A |
|---|---|
| Null mock (mechanical difference) | +0.41 points (s.e. 0.04) |
| Planted mock (the truth for this check) | **+1.31 points** (s.e. 0.03) |
| Increment from the plant | **+0.90 points** |

## Result: PASS

| Check | Criterion (decisions 21, 24) | Observed |
|---|---|---|
| 95% t-interval contains the truth, n = 200 | ≥ 93% of 1,000 replications | **958 of 1,000 = 95.8%** (95% CI 94.4–97.0%) |

| Seeds n | Power, α = 0.05 | Power, α = 0.05/8 (Holm lower bound) | Interval coverage | Mean estimate |
|---|---|---|---|---|
| 12 | 85.1% | 50.0% | 95.0% | +1.30 |
| 25 | 98.7% | 94.4% | 95.6% | +1.30 |
| 50 | 100% | 99.9% | 97.0% | +1.31 |
| 100 | 100% | 100% | 95.7% | +1.30 |
| 200 | 100% | 100% | 96.9% | +1.31 |

- **No bias:** the estimate recovers the truth at every n.
- **Coverage holds down to 12 seeds.**
- **Power:** a difference of about 1.3 points is found under Holm half the time at 12
  seeds and reliably from about 25.

## History

**Third run (decisions 25–27):** truth +1.29 points (null +0.51, plant +0.78); coverage
96.4% at n = 200. Pass.


**Second run (decisions 21, 22, 24):** truth +1.08 points (null −0.32, plant +1.39);
coverage 95.5% at n = 200 and 96.1% at n = 12. Pass.

**First run:**
The first M3 run (before decisions 21, 22 and 24) used percentile bootstrap intervals and
the criterion "at least 95 of 100 replications". It gave 93 of 100 (96.1% over 1,000)
at n = 200, and 91.6% coverage at n = 12. Those results led to decisions 21 and 24. The
grids were then regenerated, because decision 22 changed the misinformation post. The
truth and the null difference are unchanged to four decimals.
