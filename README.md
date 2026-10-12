# Syntroworld engine

A deterministic simulation of Kleros, the town in `source-docs/`, where the
constitution is the experimental variable. This is the phase M engine: **mock brain
only, no model calls**. It implements tickets SYNW-001 to SYNW-029 of `tickets.yaml`.

## Run it

```
pip install -e ".[test]"
synw run worlds/a.yaml --seed 1 --out runs/              # World A, no shocks
synw run worlds/b.yaml --seed 1 --arm full --out runs/   # World B, drought + misinformation + rogue
python -m synw.analysis.calibrate --world worlds/a.yaml --seeds 1-20
pytest -q
```

Each run writes one JSON Lines event log (`runs/<world>-<arm>-s<seed>.jsonl`): a header
(engine version, config hash, seed, brain, full config), the events, and a footer with
the final state hash. Same config and seed give a byte-identical log, in any process.
A season (384 ticks) takes about 1 second.

## Layout

```
synw/
  rng.py events.py config.py runner.py cli.py shocks.py
  world/       clock map agents economy river market treasury claims deals
  brains/      base (interface, observation, action validator)  mock
  governance/  effects rules project blocks kleroterion deliberation advocates
  metrics/     economy (P2 S1 S2 S3)  harm (S16-S19)  legitimacy (P1 S4 S5)
               participation (P3)  resilience (P4)
  analysis/    compare (paired statistics, 06 §7)  calibrate (06 step M1)
worlds/        base.yaml personas.yaml a.yaml b.yaml c.yaml blocks/
schemas/       world.schema.json effect.schema.json procedural-block.schema.json
tests/         one file per ticket
```

Units are integers everywhere: credits and goods in milli-units, shares and
probabilities in per-mille, health 0 to 100.

## Calibration status

All eight null-world targets of 03 §10.2 hold on 200 seeds after calibration. Three
world parameters changed: River r 0.25 → 0.06, S0 0.8 K → 0.7 K, founders' credits
60 → 45. Five mock-brain fixes were also made. See `calibration-log.md` for the
values, the reasons and what to watch.

## Where the specs left room: choices made in code

These are interpretations, not decisions. Each one lives in the module named and can be
changed there.

- **Travel** (`world/map.py`): every move costs its tick and the citizen arrives next
  tick; districts add no extra delay. An extra transit tick between districts left
  the mock unable to reach the Exchange in time to trade.
- **Rest** (`world/agents.py`) restores health only at home or at the Clinic.
- **Deals** (`world/deals.py`): `accept` is an action (the "other side accepts or not"
  of 03 §4). An unaccepted offer expires after one day. If neither side settles, the deal
  expires without a default.
- **Prices with no trade** (`runner.py`): with bids only, the last price rises toward the
  best unfilled bid, up to the import price; with asks only, it falls 10% a day toward
  the export price. This lets shortages and gluts show up in prices.
- **Beliefs** (`world/claims.py`): posts are read at the start of each day by citizens
  who paid the data fee; messages are read at the start of the next tick. Belief rolls
  use a separate `belief/<agent>` stream, so the brains' own streams are untouched.
  Claim types: River level (high ≥ 0.7 K, ok ≥ 0.5 K, low), "X stole" (true if X
  stole in the last cycle), and "price above".
- **Mock brain** (`brains/mock.py`) follows 03 §6.2 and adds: morning Gate purchases for
  needs the auction left unmet; selling large surpluses at the Gate after work, but
  only when the Gate pays about as well as the Exchange; distress sales at the Gate;
  heading to the Exchange at tick 13 and staying there until the auction; Clinic care
  by carers; occasional Observatory queries (more often for low-credulity personas); a
  harmful-act check at most once per act per day. "Buy shortfall" is measured against
  the same two-day holding as "sell surplus".
  Evaluations add a small honesty-based term for bans, fines and sanctions, which the
  projection alone scores as zero.
- **Suspensive Objection** (`governance/blocks.py`): the first vote after an objection is
  logged as provisional. Dialogue reopens for one tick, then a second vote, which
  stands (+2 ticks, as in 02 §2).
- **Review Bench**: each breach detected in the last cycle becomes a mandatory item:
  restitution to the Treasury of up to 2 Sawa. **Kill Switch**: three alerts on one
  target in a day, or three detected harmful acts by one agent in a day, convene a fresh
  panel of 5. The panel votes on suspending steal, sabotage, post, message and deal for
  one cycle. Review Bench confirmation is not modelled, since the suspension lapses
  after one cycle anyway. The River-collapse alarm is logged but convenes nothing.
- **Concentration trigger** (B): when it is reached, the next Cycle Assembly gets a
  mandatory item, a 10% income tax. **Reflexivity session**: logged at the start of
  every second sitting; it does not shift the sitting's phases.
- **Alerts in A and C**: an alert about a default adds an urgent restitution item to the
  next plenary.
- **Allocations**: river restoration adds 1 milli-food of stock per milli-credit;
  monitoring adds +1‰ detection per 0.2 credits (at most +500‰); plant upgrade adds
  +1 milli-energy per tick per 0.1 credits (at most +1 energy). Restoration, monitoring
  and upgrades are spent outside the town.
- **Amendments** (`amend_block`) take effect at the start of the next cycle, in every
  world. Fields: quorum, rule, weights, agenda_cap, deliberation (on/off), and
  sortition_size (0 = plenary, otherwise a panel drawn each cycle).
- **Quorum** carries an explicit base (`of: citizens | members | wealth`). That is the
  second field in which World C differs from A.
- **S1** counts departed citizens as citizen-days without the basket, in line with 05 §2.
- **YAML**: only `true`/`false` are booleans, so `{yes: 3, of: 5}` reads as written.

## Not built yet

The model brain and replay (phase L), ablation and arm configs, `analysis/grid.py`, and
secondary outcomes S5–S15 beyond the compliance variants in `metrics/legitimacy.py`.
