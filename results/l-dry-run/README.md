# Dry run of the phase L analysis on phase M data

06 §8.3 asks that the analysis code be written and tested on phase M data before any
phase L run. This folder is that test: worlds A, B and C, seeds 1 to 20, arms `full` and
`none`, **null mock** (no model), put through exactly the phase L pipeline
(`synw.analysis.phase_l`).

    python -c "from synw.analysis.phase_l import mock_campaign; mock_campaign('runs/dry', seeds=range(1, 21))"
    python -m synw.analysis.phase_l --campaign runs/dry --pilot --out results/l-dry-run

## Checks

- **Same numbers as phase M.** For all 120 runs, P1, P2, P3, S2, S6 and the state
  hash are identical to the M4 rows for the same seeds. P4 is identical to M4's
  `1 − S2(full) / S2(none)` (largest difference 0).
- **No false departures.** The model and the baseline are the same null mock here, so
  every departure from the mechanical baseline should be near zero. All 8 approximate
  95% intervals include zero (`report.md`).

## What the pilot table says about phase L budget (`pilot.md`)

With the null mock's own seed-to-seed noise, 06 §7.4 asks for **12 seeds per world for
P1 and P3, but 33 to 60 for P2 and P4** (σ_d of the Gini and of output loss is large
next to their SESOI of 0.05). A model brain will likely be noisier still. So L2 may need
around 60 seeds per world: 4 worlds × 60 seeds × 2 arms = 480 runs. If that is too
costly, decision 8 applies: raise the P2 and P4 SESOI in writing before L2, drop the
`none` twins (weaker P4, labelled), or report those outcomes as descriptive. The L1
pilot gives the real numbers.

*Null mock, not findings about AI agents.*
