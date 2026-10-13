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

The posts are compared without two fields:
- the running claim id, which counts every claim made earlier in the run;
- the engine's truth flag. The flag records whether the claim was true when posted,
  which depends on what happened in that world.

On the first comparison the flag differed for `full` seeds 2, 8 and 15: the forged
post "citizen X stole" was *true* in World B, because X had in fact stolen there that
cycle. The shock itself (time, targets, text, attribution) was identical. The
comparison now excludes the flag, and `result.json` lists those three seeds under
`shock_claim_truth_differs`.

This matters for reading the misinformation shock. Its *content* is a common random
number across worlds, but whether it is misinformation is not guaranteed. In a world
where X did steal, the post tells the truth. See decisions.md, question 22.
