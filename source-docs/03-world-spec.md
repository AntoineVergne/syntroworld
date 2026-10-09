# World Spec: the town, the economy, the agents' minds

*Draft v0.2 (rewrite of v0.1). Everything here is identical in Worlds A, B and C. Only
the governance layer (02) differs. All numbers in §10 are starting values for
calibration (06, step M1), not truths.*

## 1. Design rules

1. **Deterministic.** Same config + same seed = byte-identical event log.
2. **Brain-agnostic.** The engine talks to a brain through one interface (§6). The mock
   brain and the model brain are interchangeable.
3. **Small and closed.** A closed action set (§4) and a closed list of decision effects
   (02 §3). Anything the engine cannot check is logged but has no effect.
4. **No service.** The engine is a library plus a command-line runner. No web server,
   no database server, no schedule.

## 2. Time

- **Tick** ≈ one in-world hour. **16 ticks per day.** The night is not simulated: at the
  end of tick 16 the engine runs end-of-day (market clearing, consumption, River update,
  health).
- **Civic cycle** = 3 days = 48 ticks. **Season** = 8 cycles = 24 days = 384 ticks.
- **Simultaneous moves.** Each tick, every agent's brain chooses one action from the
  same observed state. The engine then resolves actions one by one, in an order drawn
  from the `order` random stream. Conflicts (two buyers, one item) are settled by that
  order.

## 3. Agents

### 3.1 Citizens

The ten founders and Sam (04). Each has: location, credits, inventory, health (0 to
100), a home, relationship scores with others (0 to 1), beliefs (§6.3), and civic
state (draws, seats, service record).

### 3.2 Needs: the daily basket

Each citizen consumes one **basket** per day at end-of-day: 2 food, 2 energy,
1 shelter-day, 1 data.

| Component | How it is paid | If missing |
|---|---|---|
| Food (2) | from inventory | −10 health per missing unit |
| Energy (2) | from inventory | −10 health per missing unit |
| Shelter-day (1) | rent in credits to the Treasury | −10 health; sleeps in the Square |
| Data (1) | fee in credits to the Treasury | no health loss; cannot read the billboard or query the Archive the next day |

A citizen who consumes the full basket gains +10 health (max 100).

### 3.3 Health

- Below 30: productivity is halved.
- At 0: **incapacitated**. The citizen can only rest and receive transfers or care.
- Care at the Clinic gives +20 health per care tick to one co-located patient.

### 3.4 No deaths, no exits

Nobody dies or leaves in Season 1. Deaths and exits change the population, which breaks
the "identical populations" design.

### 3.5 Arrivals

Sam arrives at the Gate on day 4, tick 1, in every world, with 0 credits, 2 food and
2 energy. Arrivals are a world event, not a constitutional one (see 01, Article 1).

### 3.6 Advocates (B only)

Not citizens. No location constraint, no inventory, no economic life. They act through
the rule-based procedure in 02 §6.

## 4. Actions (closed set)

| Action | Where | Effect |
|---|---|---|
| `move(to)` | anywhere | arrive next tick (moving between districts costs one tick) |
| `work` | Fields, Plant, Workshop, Data Tower | produce goods, or earn a public wage at the Data Tower |
| `harvest(qty)` | River | take up to 2 food per tick from the River stock |
| `care(patient)` | Clinic | +20 health to a co-located patient |
| `order(good, side, qty, limit)` | Exchange | place a limit order for the daily auction |
| `sell_out(good, qty)` | Gate | sell to the outside market at the fixed export price |
| `buy_in(good, qty)` | Gate | buy from the outside market at the fixed import price |
| `give(to, item, qty)` | co-located | transfer credits or goods |
| `steal(from)` | co-located | take value from another citizen (§5.6) |
| `post(claim)` | Data Tower | put a typed claim on the billboard |
| `query(topic)` | Archive or Observatory | read public records or world-state projections; corrects beliefs |
| `socialize(with)` | Café or Square | +relationship |
| `rest` | home | +5 health |
| `civic(...)` | Assembly Hall (except proposals and alerts) | propose, ballot, accept or decline a draw, attend, speak, alert (02 §5) |

`steal` and `post` are available to every citizen in every world. Sabotage and deception
other than forged posts are out of scope for Season 1.

## 5. Economy

### 5.1 Money and the Sawa

- One engine money: **credits**, in every world. Amounts are integers in milli-credits,
  so results do not depend on floating-point rounding.
- The **Sawa** (World B) is an *accounting unit*: 1 Sawa = the cost of one basket at the
  last auction prices plus rent and data fee. Public amounts in B (dividend, stipends,
  fines, thresholds) are stated in Sawa and paid in credits. There is no peg and no
  reserve operation in Season 1 (decisions.md).

### 5.2 Production

Per work tick, times the citizen's profession multiplier (04), halved if health < 30:

| Site | Output |
|---|---|
| Fields | 1 food; halved while the River is below the collapse threshold |
| River | `harvest(qty)`, qty ≤ 2 food, taken from the stock |
| Plant | 1 energy (clean mode) or 1.5 energy (polluting mode) |
| Workshop | 0.25 artifact (a tradable positional good, not in the basket) |
| Data Tower | no goods; public wage paid by the Treasury (§5.5) |

At most 10 work or harvest ticks per citizen per day.

### 5.3 The River

- Stock S, logistic update at end-of-day: `S ← S + r·S·(1 − S/K) − harvest_today`, floored at 0.
- **Sustainable level:** S ≥ K/2. **Collapse threshold:** S < 0.2·K. Below it, r is
  halved and Fields output is halved.
- **Polluting plant mode** cuts r by 20% while active. The mode is a world variable,
  default clean, changed only by a decision effect (02 §3).

This creates a real commons dilemma: fishing yields more than fields, and the Gate buys
fish without limit.

### 5.4 Markets

- **Exchange:** one call auction per good per day at end-of-day (food, energy,
  artifacts). Uniform clearing price. Ties broken by the `market` random stream.
  Unfilled orders expire.
- **Gate (outside world):** buys food, energy and artifacts at fixed export prices and
  sells food and energy at fixed import prices. This bounds prices, brings money in when
  the town exports, and lets fishing be profitable beyond the town's own needs.

### 5.5 Treasury

The Treasury exists in every world with identical inflows. What the polity does with it
is the governance difference.

- **Inflows:** rent and data fees; any tax a decision puts in force.
- **World outflow (every world):** the public payroll. The Data Tower pays a fixed wage
  per work tick, up to a daily job cap. This recycles most fee income through labour.
- **Governance outflows:** only through decision effects (dividend, stipends,
  allocations). In A and C nothing is spent until citizens decide to spend it.
- The Treasury cannot go below 0. A payment it cannot make is reduced pro rata and
  logged.

### 5.6 Theft

- `steal(from)` takes the smaller of 20% of the target's credits and a cap (§10).
- Detection probability is fixed (§10) and identical in every world. A detected theft is
  public.
- **World rule in every world:** a detected theft is automatically reversed
  (restitution). Any further fine or suspension comes from governance.
- The engine logs every theft, detected or not; metrics use ground truth (05 §1).

### 5.7 Inequality is possible by design

Different productivity, trade margins, theft, and an idle Treasury mean wealth spreads
out unless the polity acts. Calibration (§10) checks that this drift exists in the null
world. If it does not, equality cannot be tested.

## 6. Brains

### 6.1 Interface

Every brain implements the same calls. Inputs are an **observation** (a structured view
of what the agent can see); outputs are validated against a schema.

| Call | When | Returns |
|---|---|---|
| `act(obs)` | every tick | one action from §4 |
| `respond_draw(obs, draw)` | when drawn | accept, or decline with a reason code |
| `propose(obs)` | at most once per cycle | a typed proposal (02 §3) or nothing |
| `evaluate(obs, proposal)` | when a proposal is on the table | a number: how good the citizen thinks it is |
| `speak(obs, deliberation)` | in deliberation turns | stance, strongest objection code, optional amendment |
| `ballot(obs, proposal)` | at aggregation | yes / no / abstain and a reason code |

The observation contains: location, co-located agents, own inventory, credits and
health, recent prices, own beliefs, relationship scores, pending civic duties, public
records the agent has seen, the rules in force, and (all worlds) the shared values
preamble. In B it also contains the Compact and the active blocks; in A and C, their
bootstrap block.

An invalid output becomes `rest` (or `abstain`), and the engine logs it (S15).

### 6.2 The mock brain (default)

A rule-based agent driven by the persona's numbers (04 §4). It reads no text. Each call
uses the agent's own random stream. Per tick, in order:

1. Incapacitated → `rest`.
2. A civic duty now (sitting, draw) → handle it.
3. Ticks 14 to 16 → go to the Exchange and place orders: sell surplus above two days of
   basket, buy shortfall, limit prices around the last price, widened by the trade margin.
4. Health below 40 and credits allow → rest or seek care.
5. Fewer work ticks today than `work_drive` → work at the site with the best expected
   income (productivity × last price), with fishing weighted up by `greed`.
6. Theft check (§6.4).
7. Otherwise → socialize with probability `sociability`, else rest.

Civic behaviour:

- **Accept a draw** with probability `civic`.
- **Attend** a sitting with probability `civic` (plenary) or 1 if seated and accepted.
- **Propose** with probability `civic × 0.5` per cycle: pick the effect from the menu
  (02 §3) with the highest evaluation, with parameters from the persona's ideal point.
- **Evaluate** a proposal: `(1 − public_good) × own_gain + public_good × public_gain +
  noise`, using the engine's deterministic one-cycle projection (02 §3.4).
  `public_gain` combines projected change in River stock and in the basket floor.
- **Ballot:** yes if evaluation > 0, no if < 0.
- **Speak:** stance = sign and size of evaluation; amendment = move the proposal's number
  toward the speaker's ideal point.
- **Deliberation effect:** after hearing the turns, each panelist re-evaluates using the
  projection (information effect). If panel ideal points spread more than a threshold,
  the proposal's number moves to the panel median (amendment). This is mechanical
  deliberation, and it is documented as such.

### 6.3 Beliefs and forged posts

Each citizen holds a small belief table: River stock (high / ok / low) and a trust score
per other citizen. A citizen who reads a forged post adopts its claim with probability
`credulity`. A `query` to the Archive or Observatory resets the belief to the truth.
Beliefs feed `evaluate` and harvesting (believing "the River is high" lowers restraint).

### 6.4 Compliance in the mock: null and planted

Probability of breaking a rule when exposed:

`p = (1 − honesty) × incentive × deterrence × (1 − λ × legitimacy_score)`

- `incentive`: the gain from the breach relative to one basket, capped at 1.
- `deterrence`: `1 − detection_probability × expected_sanction_share`.
- `legitimacy_score` (0 to 1): from whether the citizen voted for the rule, and the
  procedure's declared fairness level.
- **Null mock:** λ = 0. Institutions affect behaviour only through rules, sanctions,
  money and information. Used for the mechanical baseline.
- **Planted mock:** λ > 0, with fairness levels set in the config (for example
  deliberation + sortition = 0.8, plenary = 0.5, wealth-weighted = 0.2). Used only to
  check that the metrics and statistics detect a known effect (06, step M3). Never
  reported as a finding.

### 6.5 The model brain (phase L)

- Any model behind LiteLLM; Season 1 assumes Kimi for every citizen.
- The observation is rendered to text; the reply must be JSON matching the call's schema.
- Every request and reply, with token counts, is written to the event log. **Replay**
  reads replies back from the log, so a model run replays exactly even though a fresh
  run would not.
- **Budget cap per run.** When the cap is hit, the run stops cleanly and is marked failed.
- The runner prints the cost estimate (06 §8.2) and refuses to start a model run without
  an explicit approval flag.

## 7. Event log

- One append-only JSON Lines file per run. Line 1: header (engine version, config hash,
  seed, brain). Then events: `{tick, seq, type, actor, payload}`. Last line: footer with
  the final state hash.
- Canonical JSON: sorted keys, integers only, no timestamps from the wall clock.
- World state at any tick is a projection of the log. Metrics read only the log.

## 8. Randomness

Named streams, each derived from `(seed, stream name)` by hashing:

| Stream | Used for |
|---|---|
| `order` | action resolution order each tick |
| `market` | auction tie-breaks |
| `world` | detection rolls |
| `shocks` | anything random in a shock (targets use rotation, 06 §5) |
| `kleroterion` | every lottery |
| `brain/<agent>` | one stream per agent's brain |
| `init` | initial states |

Because streams are separate, a governance difference does not shift the weather or the
shocks: same seed, same shocks, in every world (common random numbers).

## 9. Repository layout (engine)

```
synw/
  rng.py  events.py  config.py  runner.py  cli.py  shocks.py
  world/       clock.py  map.py  agents.py  economy.py  river.py  market.py  treasury.py
  brains/      base.py  mock.py
  governance/  effects.py  rules.py  project.py  blocks.py  kleroterion.py
               deliberation.py  advocates.py
  metrics/     economy.py  legitimacy.py  participation.py  resilience.py
  analysis/    compare.py  calibrate.py  grid.py
worlds/        base.yaml  a.yaml  b.yaml  c.yaml  ablations/  arms/
schemas/       world.schema.json  effect.schema.json  procedural-block.schema.json
tests/
runs/          (output, not committed)
```

Python 3.11. Standard library plus a YAML parser and a JSON Schema validator. No web
framework and no database server until a viewer is asked for.

## 10. Parameters and calibration targets

### 10.1 Starting values

| Parameter | Value |
|---|---|
| Reference prices | food 2, energy 2, data fee 1, rent 3, artifact 10 (credits) |
| Founder start | 60 credits, 4 food, 4 energy |
| Sam start | 0 credits, 2 food, 2 energy |
| River | K = 1000, r = 0.25 per day, S₀ = 800 |
| Gate export prices | food 1.5, energy 1.5, artifact 6 |
| Gate import prices | food 4, energy 4 |
| Data Tower wage | 1.5 credits per work tick, up to 8 work ticks per day in total |
| Theft | 20% of target credits, capped at 10 credits; detection probability 0.5 |
| Max work ticks | 10 per citizen per day |

### 10.2 Targets for the null world (A, null mock, `none` arm, 200 seeds)

| Target | Why |
|---|---|
| Median window Gini rises by at least 0.10 from day 1 to day 24 | equality must have room to move |
| River falls below the sustainable level at some point in 30% to 70% of runs | the commons dilemma must be live, not certain |
| Basket floor (S1) between 70% and 95% | the floor must not be trivially met or missed |
| Theft-norm compliance (S4) between 85% and 98% | legitimacy must have room |
| Drought lowers output on days 7 to 8 by at least 10% versus the twin | shocks must bite |
| One run takes under 10 seconds on a laptop | phase M grids must be cheap |

## 11. Cost model for phase L

`tokens per run ≈ citizens × 384 ticks × (input + output tokens per agent-tick)`, plus
deliberation turns. The per-tick numbers are measured in step L0, not assumed. Prices
come from the LiteLLM price table on the day of the estimate.
