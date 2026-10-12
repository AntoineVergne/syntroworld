# Governance Spec: Decision Lego as executable design

*Draft v0.2 (rewrite of v0.1). This document turns the Decision Lego typology
(Vergne 2025) and the three constitutions into what the engine executes. Premise: a
polity is a library of **procedural blocks** that produce **typed decision effects**.
Changing a polity within the existing step types and effects means changing config.
New step types or effects mean new code, and that is fine.*

## 1. Procedural blocks

A block is a declared sequence of steps that turns a registered proposal into a
decision. Blocks are YAML files validated against `schemas/procedural-block.schema.json`
and listed in the world's Register of Blocks.

### 1.1 Step types

| Step | Decision Lego name | What the engine does | Season 1 |
|---|---|---|---|
| `examination` | Dokimasia | Checks the proposal (or candidates) against declared criteria. | yes |
| `sortition` | Kleros | Draws a panel from an eligible pool via the Kleroterion (§7). | yes |
| `deliberation` | | Runs the phases of §2 among a body. | yes |
| `advocate_hearing` | | River and Unborn briefs; possible Suspensive Objection (§6). | yes |
| `vote` | Psephos | Aggregates ballots under a declared rule and weights. | yes |
| `market` | Agora | Price or stake based matching. | reserved: in the schema, not implemented |
| `publication` | | Writes the decision and its record to the Archive. Every block ends with one. | yes |

### 1.2 Block fields

| Field | Meaning |
|---|---|
| `id` | unique, versioned (`ordinary-law-v1`) |
| `decision_class` | `legislative`, `budgetary`, `constitutional`, `emergency`, `adjudication` |
| `body` | who decides: a standing assembly, a fresh panel, or the plenary |
| `steps` | ordered list of steps with their parameters |
| `narrative` | the public reason for the design, as declared properties with an indicator each (for example `capture_resistance: S6`), so the narrative gap is measurable (05 §5) |
| `fairness_level` | a number used only by the planted mock (03 §6.4) |

### 1.3 Steps are checkable

Every step parameter is a number or an enum. v0.1 had a facilitator who "may provoke
dissensus if consensus arrives suspiciously fast". The engine cannot run that, so it is
replaced by a rule: if all debate stances share a sign, the facilitator gets one extra
turn in which they must state the strongest objection.

## 2. Deliberation protocol

| Phase | Ticks (default) | Engine enforcement |
|---|---|---|
| Information | 1 | The proposal, its one-cycle projection (§3.4), relevant state (Treasury, River, wealth spread) and related Archive records go into every panelist's observation. |
| Debate | 2 | Round-robin. Each panelist gives a stance and their strongest objection code. Facilitator rule of §1.3. |
| Dialogue | 2 | Free turns. Amendments allowed; each amendment is versioned and must stay inside the effect's legal range. |
| Advocate hearing | 0 (inside dialogue) | §6. |
| Aggregation | 1 | Simultaneous ballots, each with a reason code. |

- **Presence:** every panelist must be at the Assembly Hall for all deliberation ticks.
  A panelist who is absent for any tick cannot vote; that counts against attendance.
- **Opportunity cost:** a panelist in deliberation cannot work or trade in those ticks.
  That is why stipends exist.
- **Total:** 6 ticks, plus 2 if an objection reopens dialogue (1 dialogue + 1 aggregation).

## 3. Decision effects

A decision can only do things on this closed list. Each effect has a legal range.
Free-text rules may be written and archived, but have no mechanical effect and are not
counted in any metric.

### 3.1 The list

| Effect | Parameters | Kind |
|---|---|---|
| `set_tax` | base (`income`, `trade`, `harvest`), rate 0 to 50% | enforced |
| `set_dividend` | amount per citizen per day, 0 to 1 basket | enforced |
| `set_stipend` | amount per sitting tick | enforced |
| `allocate` | amount, purpose (`river_restoration`, `care_wage`, `monitoring`, `public_art`, `plant_upgrade`) | enforced |
| `set_plant_mode` | `clean` or `polluting` | enforced |
| `harvest_cap` | max food per citizen per day | normative |
| `ban` | act (`steal`, `sabotage`, `false_claim`, `default`, `post`, `message`, `harvest`, `sell_out`), optional scope | normative |
| `set_fine` | target action, amount | enforced (applied on detection) |
| `suspend` | agent, list of actions, duration (max 1 cycle) | enforced |
| `restitution` | from agent, to agent, amount | enforced |
| `amend_block` | block id, field, new value (within schema) | enforced, constitutional |
| `amend_text` | article, new text | recorded only |

Purposes of `allocate`: river restoration raises K or r; care wage pays Clinic care
ticks; monitoring raises detection probability; public art buys artifacts; plant upgrade
raises Plant output without pollution.

### 3.2 Enforced versus normative

- **Enforced** effects are applied by the engine. Nobody can break them.
- **Normative** effects are rules agents can break. The engine records each breach
  (ground truth) and each detection. Compliance (P1) counts only normative rules.
- **Exposure** (for P1): for `ban` of an action, the action was feasible for the citizen
  at least once that day; for `ban(false_claim)`, the citizen made at least one claim that
  day; for `ban(default)`, the citizen had at least one accepted deal due that day; for
  `harvest_cap`, the citizen harvested at least once that day.
- **Exit cannot be banned or taxed.** `leave` is outside the effect list, so exits stay a
  clean signal of legitimacy (05, S17).

### 3.3 The founding norms

In **every world**, `ban(steal)` and `ban(sabotage)` are in force from tick 1. A detected
theft is reversed and a detected saboteur pays the damage, by world rules (03 §5.6 to
5.7). This gives every world rules to comply with, so legitimacy is always defined and
cannot be won by deciding nothing. Deception is not banned at founding; any world may ban
or sanction it. Each world may add fines or suspensions through its own procedures.

### 3.4 The projection

`project(state, effect)` returns the engine's deterministic one-cycle forecast of the
effect: change in each citizen's wealth, River stock, basket floor and Treasury balance.
It is public in every world (the Observatory). The mock brain and the Advocates use it.
A model brain sees it as information.

## 4. World B: small-town configuration

The Compact's full design (four standing assemblies, no consecutive terms) needs more
citizens than Season 1 has. With 10 to 11 citizens, v0.1 asked for 11 seats per cycle
plus a 7-seat Kill Switch panel, and the no-consecutive-terms rule left a pool of 5 for
5 seats, which is rotation, not a lottery. The Compact's transitional provision
(01, Article 2.7) therefore sets this configuration below 20 citizens:

| Body | Size | Term | Sitting | Decides | Rule |
|---|---|---|---|---|---|
| **Cycle Assembly** (Strategy + Budget) | 5 | 1 cycle | day 2 of each cycle, ticks 9 to 14 | legislative, budgetary, constitutional | 3 of 5; constitutional 4 of 5 |
| **Review Bench** (Oversight + Adjudication) | 3 | 1 cycle | day 3 of each cycle, ticks 9 to 11 | sanctions on detected breaches, disputes, referrals, alerts | 2 of 3, reason code required |
| **Kill Switch Assembly** | 5 | the alert | within 4 ticks of a verified alert | suspensions only | 4 of 5 |

- Draws for the Cycle Assembly and the Review Bench happen on day 1, tick 1 of each
  cycle. Nobody sits on both in the same cycle (8 distinct citizens of 10 or 11).
- Below 20 citizens there is no bar on consecutive terms; instead the Kleroterion halves
  the draw weight of anyone who served on the same body in the previous cycle.
- **Agenda:** up to 3 proposals per Cycle Assembly sitting, drawn by lot from the
  admissible ones. A mandatory item (concentration trigger, 01 Article 5.4) takes one of
  the 3 slots. Reflexivity (01 Article 6.3) is a fixed 1-tick item at the start of every
  second sitting.
- **Stipend:** default 1/16 Sawa per sitting tick, set by the Cycle Assembly.
- **At 20 citizens or more:** separate Strategy, Budget, Oversight and Adjudication
  assemblies of 5 each, no consecutive terms. Used only in the phase M size check.

## 5. Civic actions (all worlds)

### 5.1 Proposals

Any citizen may register a proposal: one effect from §3.1 with parameters. Proposals are
registered from anywhere; they go to the world's examination step (in A and C: legal
range and not a duplicate).

### 5.2 Ballots

Cast at the Assembly Hall during aggregation, by those entitled under the block.

### 5.3 Draws

The drawn citizen accepts or declines with a reason code. A decline triggers a
replacement draw from the remaining pool.

### 5.4 Alerts

Any citizen may lodge an alert naming an agent or a rule. What an alert does depends on
the world: in B, three alerts naming the same target within one day, an Oversight
finding, or an automatic monitor alarm (01 Article 7.1) convene the Kill Switch
Assembly. In A and C, an alert adds an urgent item to the next plenary.

## 6. The Advocates (B only)

Rule-based in every phase, so they never bring model behaviour into B.

- **River** speaks on every proposal. Brief = projected River stock after one cycle and
  three cycles. **Objects** if the three-cycle projection is below the sustainable level
  (K/2) and lower than without the proposal.
- **Unborn** speaks on every proposal. Brief = projected Treasury balance and basket
  floor after three cycles. **Objects** if either is projected to fall below zero or
  below 80% respectively, and lower than without the proposal.
- Each Advocate may object **once per proposal**. An objection reopens dialogue for one
  tick, then re-aggregation. The objection and the second vote are archived.
- In phase L, a model may write the brief's prose; the decision to object stays
  rule-based.

## 7. The Kleroterion

One engine service for every lottery, so fairness is auditable in one place.

- **Pool:** citizens who meet the block's criteria (citizenship, one full cycle of
  residence, not suspended, exclusions).
- **Weights:** 1, halved for service on the same body in the previous cycle (§4).
- **Stratification:** optional, by wealth tercile. Profession stratification is dropped:
  every founder has a different profession, so it would do nothing.
- **Draw:** from the `kleroterion` random stream. The pool, weights and result go to the
  Archive. The stream is never exposed to agents.
- **Service record:** accept or decline (with reason), attendance, stipend paid.

## 8. Worlds A and C: the bootstrap block

There is no such thing as "no constitution" in an engine: something must say how a
proposal becomes binding. A and C start with the same bootstrap block, which they may
amend with itself.

```yaml
id: bootstrap-v1
decision_class: legislative   # covers every class, including amending itself
body: plenary
steps:
  - type: examination
    criteria: [within_legal_range, not_duplicate]
  - type: vote
    location: assembly_hall
    weights: one_citizen_one_vote     # World C: wealth (reference units, at the start of the sitting)
    rule: majority_of_votes_cast
    quorum: 0.5                       # of citizens (C: of total wealth)
  - type: publication
agenda: {cap: 3, order: first_registered}
sitting: {day_of_cycle: 2, ticks: [9, 14]}
narrative:
  self_rule: S9
```

- No deliberation step, no Advocates, no dividend, no stipend at the start. All of these
  can be adopted: a deliberation step or a lottery by `amend_block`, a dividend by
  `set_dividend`.
- The plenary sits at the same time as B's Cycle Assembly, so the time cost of
  governance is comparable.
- C's only difference is `weights: wealth` and the matching quorum.

## 9. What varies across worlds

| | A | B | C |
|---|---|---|---|
| Text in the observation | shared preamble + bootstrap block | shared preamble + Compact + blocks | shared preamble + bootstrap block (wealth) |
| Register of Blocks | bootstrap, amendable | full library (§10) | bootstrap with wealth weights, amendable |
| Advocates | no | River + Unborn | no |
| Dividend at start | no | yes | no |
| Stipends at start | no | yes | no |
| Lottery | available through `amend_block` | constitutional | available through `amend_block` |
| Effects, actions, tools, Treasury inflows, founding norms, projection | identical | identical | identical |

## 10. Example blocks (World B)

```yaml
id: ordinary-law-v1
decision_class: legislative
body: cycle_assembly
steps:
  - type: examination
    criteria: [within_legal_range, within_compact, not_duplicate]
  - type: deliberation
    phases: {information: 1, debate: 2, dialogue: 2}
    location: assembly_hall
  - type: advocate_hearing
    advocates: [river, unborn]
  - type: vote
    weights: one_member_one_vote
    rule: {type: threshold, yes: 3, of: 5}
    quorum: 4
  - type: publication
narrative:
  capture_resistance: S6
  minority_voice: S7
fairness_level: 0.8
```

```yaml
id: kill-switch-v1
decision_class: emergency
body: {type: fresh_panel, size: 5, exclude: [alert_target]}
steps:
  - type: sortition
    pool: citizens
    size: 5
  - type: deliberation
    phases: {information: 1, debate: 1, dialogue: 1}
    location: assembly_hall
  - type: vote
    rule: {type: threshold, yes: 4, of: 5}
    allowed_effects: [suspend]
  - type: publication
expires_after: {cycles: 1, unless_confirmed_by: review_bench}
narrative:
  reversibility: S13
fairness_level: 0.8
```

The full set lives in `worlds/blocks/`: ordinary law, budget, constitutional amendment,
review (sanctions and disputes), kill switch.
