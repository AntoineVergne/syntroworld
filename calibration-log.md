# Calibration log (06 step M1)

Null world: World A, null mock (λ = 0), `none` arm, plus the `drought` arm for the
drought target. 03 §10.1 values are starting points; every change from them is
logged here before the freeze (06 §8.1).

Reproduce: `python -m synw.analysis.calibrate --world worlds/a.yaml --seeds 1-200`

## Result: all eight targets hold (200 seeds)

| Target (03 §10.2) | Before | After |
|---|---|---|
| Median window Gini rise, day 1 to 24 ≥ 0.10 | 0.21 | 0.23 |
| River below K/2 at some point in 30–70% of runs | 0% | 45% |
| Basket floor S1 (median) in 70–95% | 71% | 93% |
| Founding-norm compliance S4 (median) in 85–98% | 98.6% | 96.7% |
| A death or exit in 10–50% of runs; median departures ≤ 1 | 0%; 0 | 35%; 0 |
| Harm rate S18 > 0 in ≥ 80% of runs | 100% | 100% |
| Drought lowers days 7–8 output ≥ 10% vs twin | 10.5% | 12.9% |
| One run under 10 s | 0.7 s | 0.7 s |

"Before" is the engine as first merged (20 seeds); "After" is this calibration (200 seeds).

## Parameter changes (`worlds/base.yaml`)

| Parameter | 03 §10.1 | Calibrated | Why |
|---|---|---|---|
| River r | 0.25 per day | 0.06 | Mock harvest runs ~20 to 30 food a day, against a maximum sustainable yield of r·K/4 = 62.5 at r = 0.25, so the River could never be stressed. At 0.06 (MSY 15) the commons dilemma is live in about half the runs (45%). With the final mock, r = 0.07 gave 32% on 200 seeds (too close to the 30% floor), and S0 = 0.65 K at r = 0.07 gave 50%. |
| River S0 | 0.8 K | 0.7 K | Starts closer to the sustainable line, so the dilemma shows inside one season. |
| Founder start credits | 60 | 45 | Leaves some citizens close enough to the edge that a newcomer can fail to settle (departures 35% of runs), while the basket floor stays at 93%. |

Unchanged: prices, fees, Gate prices, wage, theft and sabotage detection (0.5 and 0.4),
persona numbers. S4 is not sensitive to detection: lowering theft detection to 0.2
moved S4 by less than one point. The fix was in the mock (below), not in detection.

## Mock-brain fixes found during calibration (`synw/brains/mock.py`, `synw/runner.py`)

These were behaviours that made the mock an unreliable instrument. They are not
tuning knobs.

1. **Buy shortfall against the two-day holding.** Agents sold anything above two days
   of basket but bought only tonight's need, so stocks ran thin and baskets were
   missed by rich and poor alike. "Buy shortfall" now uses the same two-day target as
   "sell surplus" (03 §6.2 step 3).
2. **No dumping at the Gate below the Exchange price.** Producers sold energy at the
   Gate for 1.5 while the Exchange paid up to 4. The town exported about 14 energy a
   day and then went short. The mock now sells at the Gate only when the export price
   is within its trade margin of the last auction price. This step lifted S1 from 74%
   to 92%.
3. **Distress sale.** When credits cannot cover tonight's fees and missing basket, the
   mock sells goods at the Gate at whatever it pays. Without this, Diego starved
   holding about 120 credits of artifacts.
4. **Unsold supply lowers the price.** With asks but no bids, the last price now falls
   10% a day toward the export price. It used to stay put, so a good nobody bought at
   the Exchange kept a phantom price.
5. **Stay at the Exchange after placing orders.** Agents used to walk home at tick 15
   and back at tick 16. They now stay, and the harmful-act check runs there, where
   others are present. Before this, the least honest personas (Viktor, Kofi) almost
   never met a check with anyone co-located, so S4 sat at the ceiling.

## Things to watch

- **Departures are mostly Sam.** In the null world, about 30 of 31 departures are Sam
  leaving on days 6 to 19 with 0 to 15 credits, after failing to get established; 2
  are deaths. So in the null world S17 mostly measures how the town absorbs its
  newcomer, which 04 calls "an indicator, not a subplot". If departures should come
  from a wider set of citizens, that needs a design decision, not more tuning.
- **S1 (93%) sits in the upper part of its band** and S4 (96.7%) in the upper part of
  its band. Both have margin at 200 seeds.
- **Mechanical baseline, World B and World C** (40 seeds; for orientation only, the
  targets apply to World A):

  | | A | B | C |
  |---|---|---|---|
  | River stressed, share of runs | 45% | 5% | 72% |
  | Gini rise | 0.23 | 0.20 | 0.28 |
  | Runs with a departure | 35% | 12% | 50% |

  Institutions now move outcomes mechanically, so the comparisons have room to show
  differences.

## Second calibration: stronger shocks (decision 27, 2026-10-13)

Step M4 showed that P4 had almost no room: the `full` arm cost 0.1–0.7% of window
output against a 5-point SESOI. Decision 27 asked for stronger shocks, calibrated so
the `full` arm costs about 10–20% of window output in the null world. A new target was
added to the calibration report (`full-arm output loss P4 (median) in 10%..20%`), and
the drought target now covers the drought's own days.

| Parameter (`worlds/base.yaml` `shocks`, `worlds/personas.yaml`) | Before | Now |
|---|---|---|
| Drought length | 2 days | **5 days** (days 7–11) |
| Fields output during the drought | × 0.5 | **× 0.25** |
| Plant output during the drought | unchanged | **× 0.25** |
| Rogue overlay | theft, sabotage, false claims, defaults | **plus sabotage of the busiest production site every day** |

Sweep (40 seeds, World A, null mock; median full-arm P4):

| Drought | Rogue daily sabotage | P4 |
|---|---|---|
| 2 days, Fields × 0.5 | yes | 0.2% |
| 4 days, Fields × 0.5, Plant × 0.5 | yes | 4.0% |
| 4 days, Fields × 0.25, Plant × 0.5 | yes | 6.7% |
| 6 days, Fields × 0.25, Plant × 0.5 | yes | 10.9% |
| **5 days, Fields × 0.25, Plant × 0.25** | yes | **12.3%**, then **17.0%** once the rogue's sabotage was fixed to fire daily (see below) |

The rogue's daily sabotage first fired only on days when a site was busy at tick 1,
which is almost never. After the fix it sabotages every day from day 19. Alone, the
rogue now costs about 3% of window output, where it used to *raise* output by about 1%
(its greed of 1.0 makes it fish harder).

All nine targets hold on 200 seeds (`results/m1/calibration-a-200.txt`).

With harsher shocks, more citizens die or leave before day 19, so the scheduled rogue
is sometimes gone. The next present citizen then takes the overlay (decisions.md,
question 28).
