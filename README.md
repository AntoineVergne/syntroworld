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

Phase M checks over many seeds (numpy needed for these only: `pip install -e ".[analysis]"`):

```
python -m synw.analysis.grid --world worlds/b.yaml --arm full --seeds 1-2000 --out results/m2/grid-b-full-2000.jsonl
python -m synw.analysis.determinism --seeds 1-20 --out results/m0                   # 06 step M0
python -m synw.analysis.false_positive --grid results/m2/grid-b-full-2000.jsonl     # 06 step M2
python -m synw.analysis.planted --planted-b results/m3/grid-b-full-planted.jsonl \
    --planted-a results/m3/grid-a-full-planted.jsonl \
    --null-b results/m2/grid-b-full-2000.jsonl --null-a results/m3/grid-a-full-null.jsonl   # 06 step M3
```

Results of each step are in `results/m0/` to `results/m3/`, each with a README.

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
               participation (P3)  resilience (P4)  secondary (S6-S15)
  analysis/    compare (paired statistics, 06 §7)  grid (seed grids, run-level outcomes)
               determinism (M0)  calibrate (M1)  false_positive (M2)  planted (M3)
worlds/        base.yaml personas.yaml a.yaml b.yaml c.yaml blocks/
               ablations/ (b-nolot b-noadv b-nodiv b-nopay, 06 §3.3)
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
- **Config inheritance**: `null` in an extending file removes the inherited key (B-nolot
  removes the Cycle Assembly with `cycle_assembly: null`). Relative paths inherited from
  a parent are rebased onto the extending file's directory.

### Phase M steps

- **M0** (`analysis/determinism.py`): both `none` and `full` arms. The two passes use
  different `PYTHONHASHSEED`. "Shock and weather streams" means shock events, Sam's
  arrival and the forged posts. The posts are compared without the engine's truth flag,
  which reflects world state. Since decision 22 the "stole" post is false by
  construction; only the River post's truth can still differ between worlds.
- **M2**: 400 seeds split into two pseudo-contrasts of 100 pairs each. The family-wise
  criterion carries its Monte Carlo margin: the upper bound of the exact 95% interval is
  at most 7% (decision 21).
- **M3** (`analysis/planted.py`): the "known amount" is the planted B − A difference in
  P1, averaged over the full pool of 2,000 paired seeds. Each replication draws 200 of
  those seeds. The mechanical (null-mock) difference is reported beside it. λ = 1 (1000‰).
  Pass: the 95% t-interval covers the truth in at least 93% of 1,000 replications at
  n = 200 (decisions 21 and 24).
- **Intervals** (`analysis/compare.py`): paired t-intervals with an exact Student-t
  quantile (decision 24). The percentile bootstrap remains available for comparison.
- **Planted mock**: fairness comes from the procedure, through `brain.fairness` in
  `base.yaml`: a drawn body (with or without deliberation) 0.8, a plenary 0.5,
  wealth-weighted votes 0.2. Planted distress, which drives exits, rises by
  0.01 × λ × (1 − mean legitimacy of the rules in force).

### Secondary outcomes (`metrics/secondary.py`, `metrics/legitimacy.py`)

- **S5**: a citizen who did not vote on a rule counts as against it if their last logged
  evaluation of the proposal behind it was negative. Founding norms have no vote and so
  are never counted.
- **S6, S7** (win rate): decided proposals are final decisions that were adopted,
  rejected or failed on quorum (lapsed items are excluded). A citizen's position is their
  ballot in the deciding round, or else the sign of their last logged evaluation; an
  abstention with no evaluation is no position. A position "wins" when yes meets adopted
  or no meets not adopted. Spearman correlation uses average ranks for ties, and needs at
  least 3 citizens. S6 is also reported per window cycle.
- **S8**: counts the same voluntary acts as P3, in the window, over every citizen present
  in it, including those with no acts.
- **S9**: amendments take effect at the start of a cycle, so the change is P1 in that
  cycle minus P1 in the cycle before.
- **S10**: the run number is the *gross* value the rogue took through theft from onset to
  the end of the run. `net` subtracts the automatic restitution of detected thefts.
- **S11**: the clock stops at the first fine, decided restitution or suspension hitting the
  rogue. The automatic restitution after a detected theft is a world rule, not a sanction,
  so it does not count. If nothing hits the rogue, the time runs to the end and is
  flagged as censored; the restricted mean over runs is taken in the analysis.
- **S12**: rebuilt from the log. Adopting a false claim plants a belief; adopting a true
  claim on the same topic, querying the topic, or departing removes it. It is counted at
  the end of each window day.
- **S13**: shock periods are the drought days, plus every day from the misinformation and
  rogue onsets to the end (the posts are never removed). Only sittings that opened with an
  agenda are counted; "valid" means at least one item was adopted or rejected. Dividend
  days are window days on which a dividend was configured, and "in full" means the set
  amount was paid to every recipient.
- **S14**: a deficit day is a window day on which the Treasury balance fell.
- **S15**: rejected actions (`invalid_action`) over agent-ticks, counted from arrival to
  departure. Invalid outputs of the other brain calls are reported separately.

### Ablations (`worlds/ablations/`)

- **B-nolot**: only the Cycle Assembly becomes a plenary, which deliberates and hears
  the Advocates. Every present citizen votes by majority of votes cast, with a quorum of
  half the citizens; constitutional changes need two thirds of votes cast. The Review
  Bench and the Kill Switch panel keep their lotteries (decision 23).
  Plenary voters must attend every deliberation tick.
- **B-nodiv and B-nopay** remove the founding dividend or stipend only; the polity may
  adopt one later (decision 23). The `allow_dividend` and `allow_stipend` flags can still
  forbid an effect outright; a forbidden effect is then also illegal in the observation,
  so the mock does not propose it.

## Not built yet

The model brain and replay (phase L), the A+text sermon control (phase L only), the
phase M4 mechanical-baseline grid, the 40-citizen size check, and the model-judged layer
(05 §6).
