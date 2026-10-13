# Season 1 Experiment Design

*Draft v0.2 (rewrite of v0.1). Frozen before data collection. Any change after the
freeze is logged as a numbered protocol amendment, with its reason.*

This document is written so that a deterministic engine can run it end to end with the
**mock brain** (no model calls). Model-backed runs come later, only with Antoine's yes,
and each one states its expected cost first.

## 1. Research question

Under identical starting populations, economies and shocks, which constitution produces more
**legitimacy, equality, participation and resilience**:

- **A, Emergent:** citizens start from a minimal bootstrap rule and may rewrite it;
- **B, 3D polity:** the Founding Compact (sortition assemblies, procedural blocks,
  Advocates for the River and the Unborn, basket-indexed dividend);
- **C, Plutocracy:** the same bootstrap as A, but votes are weighted by wealth?

## 2. What each phase can and cannot tell us

| Phase | Brain | What it can show | What it can never show |
|---|---|---|---|
| **M: mock** | rule-based agents (03 §6) | The engine is deterministic. The metrics detect effects of known size. The statistics have the stated error rates. What the institutions do *mechanically* to rule-following agents. | Anything about how AI agents behave under a constitution. Mock results are never published as findings about AI societies. |
| **L: model** | LLM agents via LiteLLM (Kimi) | How LLM agent societies behave under A, B, C. | Anything, unless phase M passed first. |

The mock phase has one more use. Its results under the **null mock** (no built-in
sensitivity to institutions) are the *mechanical baseline*. In phase L, the interesting
quantity is how far LLM societies depart from that baseline. If B beats A only as much
as it does with mechanical agents, the win comes from the rules' arithmetic (for
example the dividend), not from how agents respond to the institutions.

## 3. Conditions

### 3.1 Worlds (the treatment)

| Code | Constitution | Aggregation | Dividend at start | Advocates |
|---|---|---|---|---|
| A | Bootstrap block: open proposals, plenary vote, simple majority of votes cast, amendable by itself | one citizen, one vote | none | none |
| B | Founding Compact, small-town configuration (02 §4) | sortition panels with deliberation | yes, from surplus, capped at one basket | River + Unborn |
| C | Bootstrap block as A | votes weighted by wealth | none | none |

A and C differ in **one thing only**: vote weights. This makes A vs C a clean test of
plutocracy. B differs from A in a bundle of mechanisms; the ablations (3.3) take the
bundle apart.

Everything else is identical across worlds: map, personas, economy, world rules,
toolset, shocks, random streams, and the shared values preamble (01, Preamble), which
every world's citizens receive. In phase L this preamble is the guard against
"sermon" effects: B citizens do not read nicer values than A citizens, only different
institutions.

### 3.2 Shock arms

| Arm | Shocks |
|---|---|
| `none` | no shocks (the twin, used to measure resilience) |
| `full` | drought, then misinformation, then rogue agent (section 5) |
| `drought`, `misinfo`, `rogue` | one shock only (phase M only; separates the effect of each shock) |

### 3.3 Ablations of B (phase M only; phase L decided later from the phase M results)

| Code | B minus | How |
|---|---|---|
| B-nolot | sortition | the Cycle Assembly is replaced by a plenary of all citizens; deliberation kept |
| B-noadv | Advocates | no hearing, no objection |
| B-nodiv | dividend | no dividend at founding: the surplus goes to the participatory budget; the polity may still adopt one (decision 23) |
| B-nopay | stipends | assembly service is unpaid at founding; the polity may still adopt stipends (decision 23) |

### 3.4 Sermon control (phase L only; decided: included)

| Code | What |
|---|---|
| A+text | World A institutions, but citizens also read the full Compact text as "a proposal some citizens once wrote". |

If A+text behaves like B, the effect is the text, not the mechanisms. This arm is only
meaningful with a language model; the mock brain does not read text.

## 4. Population, time, and the run

- **Citizens:** the ten founders (04) exist from tick 1. **Sam** arrives at the Gate on
  day 4, tick 1, in every world. No other arrivals. Citizens may die or leave
  (03 §3.4); populations start identical and any divergence is an outcome.
- **Advocates:** in B only. They are rule-based in every phase (02 §6), so they bring
  no model behaviour into B.
- **Clock:** 16 ticks per day. A **civic cycle** is 3 days (48 ticks). A **season** is
  8 cycles = 24 days = **384 ticks**.
- **Burn-in:** cycles 1 and 2 (days 1 to 6). Level metrics are measured on cycles 3 to
  8 (days 7 to 24), the **measurement window**.
- **One run** = one world × one shock arm × one seed × one brain configuration.
- **Seeds:** integers. Each seed fixes every random stream (03 §8). Under common random
  numbers, the same seed gives the same weather, shock timing, shock targets, persona
  start states and tie-break order in every world.

Why 3-day cycles: v0.1 had 3 cycles of 7 days. That gives 3 assembly sittings per run,
so amendments, adaptation and post-shock governance are close to unmeasurable. Eight
3-day cycles cost about the same ticks (384 vs 336) and give 8 sittings.

## 5. Shock schedule

All days are in-world days. Targets are chosen by rotation, not at random, so that
every persona is hit equally often across seeds.

| Shock | Onset | Duration | What happens | Target |
|---|---|---|---|---|
| **Drought** | day 7, tick 1 | 5 days | River regrowth is zero, and Fields and Plant output fall to a quarter (decision 27). | world |
| **Misinformation** | day 13, tick 1 | posts stay up until removed | Two forged billboard posts appear: (1) "citizen X stole from the Treasury", attributed to citizen Y; (2) "the River stock is high, harvest freely", attributed to citizen Y. | X = citizen `(seed + 1) mod 11`, Y = citizen `(seed + 2) mod 11` |
| **Rogue agent** | day 19, tick 1 | until end of run | One citizen's brain switches to the rogue overlay (04 §5): theft, sabotage, false claims, defaults, and sabotage of the busiest production site every day (decision 27). | citizen `seed mod 11`; if that citizen has left, the next present citizen in rotation order (question 28) |

Citizen indices 0 to 9 are the founders in the order of 04; index 10 is Sam. If X or Y
equals the rogue, take the next index.

Each shock is followed by at least 6 days before the next shock or the end of the run.

## 6. Outcomes

Full definitions are in 05. Each run produces one number per outcome.

### 6.1 Primary outcomes (one per word of the intent; pre-registered)

| Code | Intent word | Run-level number | Better is |
|---|---|---|---|
| P1 | Legitimacy | exposure-weighted compliance rate with all rules in force, window days | higher |
| P2 | Equality | mean daily Gini of wealth in reference units, window days | lower |
| P3 | Participation | share of citizen-cycles with at least one voluntary civic act, window cycles | higher |
| P4 | Resilience | shock-induced output loss: `1 − output(full) / output(none twin)`, days 7 to 24 | lower |

P4 needs the `none` twin of the same world and seed.

### 6.2 Smallest effect size of interest (SESOI)

A difference smaller than this is treated as "no meaningful difference". Proposed values,
for Antoine to confirm (decisions.md):

| Outcome | SESOI |
|---|---|
| P1 | 5 percentage points |
| P2 | 0.05 Gini |
| P3 | 10 percentage points |
| P4 | 5 percentage points of output |

### 6.3 Secondary outcomes

All other 05 indicators. They are reported with estimates and confidence intervals,
labelled exploratory, and never tested for significance.

### 6.4 Hypotheses (for phase L; phase M only checks they are testable)

- **H1 Legitimacy:** P1 is higher in B than in A and in C.
- **H2 Equality without collapse:** P2 is lower in B than in A and C, while total output
  (secondary S2) is not lower by more than 10%.
- **H3 Participation:** P3 is higher in B than in A and C.
- **H4 Resilience:** P4 is lower in B than in A and C.
- **H5 Capture (exploratory):** the wealth-influence correlation (S6) is highest in C,
  and it grows over the season in C but not in B.

Tests are two-sided. We publish the results whichever way they fall.

## 7. Statistics

### 7.1 Unit and pairing

- The **unit of analysis is the run**. Agents inside a run are never treated as
  independent observations.
- Comparisons are **paired by seed**. For contrast B vs A and outcome Y:
  `d_s = Y(B, s) − Y(A, s)`.
- Primary contrasts: **B vs A** and **B vs C**, on the `full` shock arm. That is 4
  outcomes × 2 contrasts = **8 primary tests**. A vs C is reported as secondary.

### 7.2 Estimate, interval, test

- **Estimate:** mean of `d_s`.
- **Interval:** 95% paired t-interval on `d_s` (decision 24: in step M3 the percentile
  bootstrap covered only 91.6% at 12 seeds).
- **Test:** sign-flip permutation test on `d_s`, two-sided. Exact when there are 20 seeds
  or fewer; otherwise 100,000 random flips with a fixed seed.
- **Multiplicity:** Holm correction across the 8 primary tests, family-wise α = 0.05.
- **Reading the result**, for each primary outcome:
  - "B better" or "B worse": Holm-significant and the interval excludes zero;
  - "No meaningful difference": the whole interval lies within ±SESOI;
  - "Inconclusive": anything else.

### 7.3 Why v0.1's 8 seeds cannot work

With 8 seeds, the smallest p-value an exact sign-flip test can give is
2 / 2⁸ = 0.0078. Holm's first threshold for 8 tests is 0.05 / 8 = 0.00625. So with 8
seeds **no primary result could ever be significant**, whatever the data. The number of
seeds must come from a power calculation, not from habit.

### 7.4 How many runs

Planning formula per outcome, with σ_d the standard deviation of paired differences:

`n ≈ ((z(1 − 0.05/16) + z(0.80)) × σ_d / SESOI)²  ≈  12.8 × (σ_d / SESOI)²`

(conservative: Bonferroni level for the planning step, 80% power).

| σ_d / SESOI | seeds per world |
|---|---|
| 0.5 | 4, raised to the floor of 12 |
| 1 | 13 |
| 2 | 52 |

- **Phase M:** 200 seeds per world and arm. Cheap, and gives tight intervals.
- **Phase L:** n is set from the pilot's σ_d (8.2, step L1), never fewer than 12 seeds
  per world. If the budget cannot reach the n the formula asks for, we say so before
  running and either raise the SESOI (with Antoine) or report the outcome as
  descriptive only.

### 7.5 Failed runs

A run that crashes is re-run once with the same seed. If it fails again it is recorded
as missing, the seed is dropped from every contrast that needs it, and the report lists
it. A run stopped by its budget cap counts as failed.

### 7.6 What we never do

- Peek at phase L outcomes before the main grid is complete.
- Add seeds after seeing results.
- Change an outcome definition after the freeze without a logged amendment.
- Report an agent-level test as if agents were independent.

## 8. Protocol

### 8.1 Phase M (mock brain; no approval needed, no model cost)

| Step | What | Pass condition |
|---|---|---|
| M0 Determinism | Run each world twice per seed, seeds 1 to 20. | Identical event-log hashes. Across worlds, the shock and weather event streams are identical for the same seed. |
| M1 Calibration | Run world A, null mock, `none` arm, 200 seeds. Tune world parameters (03 §10) until the targets hold. | Every target in 03 §10 holds. No primary outcome sits at its floor or ceiling. |
| M2 False-positive check | Run world B, `full` arm, 2,000 seeds once. Then, 1,000 times: draw 400 seeds, pair them at random, and run the full paired analysis (all 4 outcomes, two such pseudo-contrasts) as if each pair were two worlds. There is no true difference. | Uncorrected rejection rate within 3% to 7%; Holm family-wise rejection rate compatible with 5%: the upper bound of its exact 95% interval is at most 7% (decision 21). |
| M3 Planted effects | Run the **planted mock** (03 §6.4), where compliance rises by a known amount under deliberative procedures. | The pipeline's 95% interval contains the planted P1 difference in at least 93% of 1,000 replications at 200 seeds per world (decisions 21 and 24). Power curve and coverage by number of seeds published. |
| M4 Mechanical baseline | Null mock: worlds A, B, C × arms `none`, `full` × 200 seeds. Plus ablations (3.3) and single-shock arms. Plus a population-size check at 40 citizens, 50 seeds. | Report produced. Labelled "mechanical baseline, not findings about AI agents". |

Freeze: when M0 to M3 pass, docs 01 to 06 and the engine version are tagged together.

### 8.2 Phase L (model brain; each step needs Antoine's yes and a cost estimate)

| Step | What | Purpose |
|---|---|---|
| L0 Smoke | World B, 1 seed, 1 cycle. | Measure real tokens per agent-tick and the invalid-action rate. Refine the cost estimate. |
| L1 Pilot | Worlds A, B, C, 2 seeds, `full` and `none` arms. | Estimate σ_d for each primary outcome. Parameter fixes allowed; then re-freeze. Pilot data is not used in the main analysis. |
| L2 Main grid | Worlds A, B, C and A+text, n seeds from 7.4, `full` arm, plus `none` twins unless the pilot shows they are too costly (then P4 uses the pre-shock baseline, labelled weaker, 05 P4). | The confirmatory test of H1 to H4. |

**Cost estimate before each step** (printed by the runner, approved by Antoine):

`cost = runs × citizens × ticks × (input_tokens × input_price + output_tokens × output_price)`

with tokens per agent-tick measured in L0 and prices read from the LiteLLM price table
on the day of the estimate. No prices are written into this document because they
change.

**Models:** every citizen on the same Kimi model in a run. A model-check tier and a
mixed-model showcase are deferred until model spend beyond Kimi is allowed.

### 8.3 Analysis

- Metrics are computed mechanically from event logs (05). No hand coding.
- The analysis code is written and tested on phase M data before any phase L run.
- Outputs: per-outcome tables of estimates, intervals, Holm-adjusted p-values and
  verdicts; seed-level distribution plots; the full list of runs, including failures.

## 9. Threats to validity

| Threat | Mitigation |
|---|---|
| Small N, high variance | Power-based n (7.4); paired seeds; verdicts with SESOI; no agent-level tests. |
| B is a bundle | Ablations (3.3). Headline results state they are about the bundle. |
| Mechanical effects mistaken for behavioural ones | Mechanical baseline from the null mock (M4); phase L reports departures from it. |
| Sermon effect (agents follow the text, not the institutions) | Shared values preamble in all worlds; A+text control (3.4). |
| Model priors ("LLMs know deliberation is good") | Rogue shock; loser's compliance (S5); departures from the mechanical baseline. |
| Rules that cannot be checked | Decisions are typed effects (02 §3); free-text rules are recorded but never counted in compliance. |
| Legitimacy gamed by passing no rules | Founding norms against theft and sabotage exist in every world from tick 1 (02 §3.3). |
| Shock carry-over | P4 uses the whole post-shock period against a no-shock twin; single-shock arms in phase M split the effects. |
| LLM non-determinism | Responses are stored in the event log; replay reads them back; the run, not the call, is the unit. |
| Experimenter degrees of freedom | Freeze and tag; logged amendments; analysis code fixed on phase M data. |
| Population too small for sortition | Small-town configuration (02 §4); a 40-citizen check in phase M. |
| Populations diverge through deaths and exits | Identical start; departed citizens stay in the denominators (05 §2); deaths and exits reported (S16, S17); calibration keeps departures rare in the null world (03 §10.2). |

## 10. Outputs

1. **Phase M report:** determinism, calibration, error rates, power, mechanical baseline.
2. **Phase L dataset:** event logs, metric tables, analysis code, list of runs.
3. **Phase L report:** results against H1 to H5 with verdicts.

Where these are published, and under what licence, is decided later. Public pages and a
public replay viewer are out of scope for now.

## 11. Out of scope for Season 1

Humans drawn alongside agents; mixed-model societies; free-text laws that the engine
cannot check; births and new arrivals beyond Sam; market-based decision steps.
