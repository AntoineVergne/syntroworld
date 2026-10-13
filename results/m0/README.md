# Step M0: determinism (06 §8.1)

**Run.** Worlds A, B and C × arms `none` and `full` × seeds 1 to 20, each run twice. The
two passes run in separate process trees, with `PYTHONHASHSEED` 1 and 2.

Reproduce: `python -m synw.analysis.determinism --seeds 1-20 --out results/m0`

## Result: PASS

| Check | Result |
|---|---|
| Identical event-log hashes (pass 1 vs pass 2) | **120 of 120** |
| Shock and weather streams identical across worlds, per seed and arm | **40 of 40** |

`hashes.csv` lists both hashes for every run. `world-streams.csv` lists the cross-world
comparison per seed and arm. `result.json` holds the summary.

## What "shock and weather streams" covers

The world events that must not depend on governance:
- `shock` events (drought onset and end, misinformation targets X and Y, rogue target);
- Sam's `arrival`;
- the two forged misinformation posts.

The comparison covers what was *scheduled*. Fields that report how a shock landed in that
particular world are excluded:
- the running claim id, which counts every claim made earlier in the run;
- the engine's truth flag, which evaluates world state when the post appears;
- the rogue actually hit (`target`, `applied`, `replaced`). If the scheduled rogue has
  died or left, the next present citizen takes the overlay (decision 28).

## Latest run (after decisions 25–30)

| Check | Result |
|---|---|
| Identical event-log hashes | **120 of 120** |
| Scheduled shocks identical across worlds | **40 of 40** |
| Forged posts whose truth differs across worlds | none |
| Rogue replaced because the scheduled one had left | 6 of 60 `full` runs: A seed 10; B seed 7; C seeds 2, 6, 7, 10 (`result.json`, `rogue_replaced`) |

The replacements come from the stronger drought (decision 27): more citizens now die or
leave before day 19, most often in World C.

## History

The first M0 run used an engine whose forged post read "citizen X stole". For `full`
seeds 2, 8 and 15, that post was *true* in World B, because X had in fact stolen
there. Following decision 22, the post now reads "citizen X stole from the Treasury",
as 06 §5 specifies. No action can take from the Treasury, so the post is false by
construction. In this re-run the truth flags agree across worlds for every seed and
arm (`shock_claim_truth_differs` is empty in `result.json`). The River post ("the
River stock is high") can still be true in one world and false in another; it did not
happen for seeds 1 to 20.
