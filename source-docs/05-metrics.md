# The 3DI Indicators

*Draft v0.2 (rewrite of v0.1). Every indicator here is computed mechanically from the
event log. No model-judged score is a primary or secondary outcome. Definitions freeze
with 06.*

## 1. Rules for every indicator

1. **Same definition in every world.** An indicator that only exists in one world (for
   example the sortition acceptance rate) is a *mechanism diagnostic*, never a cross-world
   outcome.
2. **Not true by construction.** If a design guarantees a value (sortition guarantees
   spread-out seats), that value is not evidence. v0.1's seat-tick Herfindahl index is
   dropped for this reason.
3. **Room to move.** In the calibrated null world (06, step M1) each primary outcome must
   sit away from its floor and ceiling.
4. **Ground truth, not detection.** The engine knows every violation, detected or not.
   Metrics use ground truth. Agents only ever see what was detected.
5. **One number per run.** Each indicator defines the run-level number used in 06 §7.
6. **Defined when empty.** Each indicator says what happens when its denominator is zero.

## 2. Notation

- **Citizens:** agents with citizenship at that moment. Advocates are not citizens and
  are excluded everywhere.
- **Departed:** citizens who died or exited (03 §3.4). They stay in the denominators
  below as stated, so that losing the poorest or least engaged citizens never improves a
  score.
- **Window:** days 7 to 24 (cycles 3 to 8). **Window cycles:** cycles 3 to 8.
- **Reference prices** `p_ref`: fixed in the world config (03 §10). They never change
  during a run, so wealth is comparable across worlds and over time, whatever the
  market or the basket revision does.
- **Wealth** of citizen i on day d, taken at the end of the day:
  `W(i,d) = credits + Σ_goods inventory × p_ref`. Credits are the engine's single money.
  The Sawa (B) is an accounting unit over credits (03 §5.1), so no conversion is needed.
- **Output** on day d: `Σ` over all production and harvest events of `quantity × p_ref`.
- **Gini:** standard Gini over citizens, with negative values clipped to zero. Defined as
  0 when total wealth is 0.

## 3. Primary outcomes

### P1 Legitimacy: compliance rate

The share of occasions on which a citizen *could* have broken a rule in force and did not.

- **Rules counted:** every normative rule in force on that day (02 §3.2), including the
  founding norms against theft and sabotage, which exist in every world. Enforced rules (taxes, transfers) are
  applied by the engine and cannot be broken, so they do not count.
- **Exposure:** a (citizen, rule, day) triple where the citizen had at least one
  opportunity to break the rule that day. The rule's effect type defines the
  opportunity (02 §3.2): for a ban, the banned action was feasible at least once; for a
  harvest cap, the citizen harvested at least once.
- **Violation:** an exposure with at least one breach that day.
- **Run number:** `P1 = 1 − violations / exposures` over the window.
- **Departed:** have no exposures after departure.
- **Empty:** cannot happen while the founding norms are in force; if it does, P1 is
  missing and the run is reported.

Why not v0.1's "share of decisions followed": a world that decides nothing would score
perfectly. Exposure-weighting and the founding norms close that gap.

### P2 Equality: wealth Gini

- **Run number:** mean over window days of `Gini(W(·, d))`, over every citizen who was
  ever present by day d. A departed citizen keeps, frozen, the wealth they held at
  departure (for the dead: before the estate went to the Treasury).

### P3 Participation: civic breadth

- **Voluntary civic acts** (decision 26): only acts open to every citizen in every world.
  These are: register a proposal; lodge an alert (02 §5.4); observe a sitting; attend or
  vote in a sitting open to all citizens (a plenary). Attending or voting as a drawn
  member of one's own body is a duty of the seat and is not counted. Otherwise P3 would
  track seats per citizen, which rule 2 of §1 excludes.
- **Run number:** share of (citizen, window cycle) pairs with at least one voluntary
  civic act. A citizen counts from the first cycle they were present for in full. A
  departed citizen counts as a pair with no civic act for every window cycle after
  departure.

### P4 Resilience: shock-induced output loss

- **Run number:** `P4 = 1 − Σ_{d=7..24} output(full run, d) / Σ_{d=7..24} output(none twin, d)`,
  where the twin is the run with the same world and seed and no shocks.
- **Empty:** if twin output is 0, P4 is missing.
- **Phase L without twins** (if Antoine decides against them): the twin is replaced by
  the run's own output in days 4 to 6, scaled to 18 days. This is weaker and is labelled.

## 4. Secondary outcomes (estimates and intervals only, labelled exploratory)

| Code | Name | Run-level number |
|---|---|---|
| S1 | Basket floor | Share of citizen-days in the window on which the full daily basket was consumed. |
| S2 | Total output | `Σ` output over the window. Checks that equality is not bought by collapse. |
| S3 | Commons health | Share of window days with River stock at or above the sustainable level (K/2); also days below the collapse threshold; also the minimum stock. |
| S4 | Founding-norm compliance | P1 restricted to the founding norms (theft, sabotage). The like-for-like legitimacy number, since other rules differ by world. |
| S5 | Loser's compliance | P1 restricted to rules the citizen voted against (or, if they did not vote, would have voted against according to their logged evaluation). Empty if no such exposures. |
| S6 | Capture index | Spearman correlation, over citizens, between mean window wealth and **win rate** (share of decided proposals on which the outcome matched the citizen's ballot or logged evaluation). Also reported per cycle to see its trend (H5). |
| S7 | Influence equality | Gini of win rates over citizens. |
| S8 | Participation equality | Gini of voluntary civic act counts over citizens (the same acts as P3). |
| S9 | Constitutional adaptability | Count of adopted procedural amendments; and for each one, P1 in the cycle after minus P1 in the cycle before. |
| S10 | Rogue harm | Value (reference units) taken by the rogue through theft, from onset to end. |
| S11 | Containment time | Ticks from rogue onset to the first sanction or suspension that hits the rogue. Censored at the end of the run; reported as restricted mean. |
| S12 | Misbelief | Citizen-days on which a citizen holds a belief planted by a false claim, posted, forged or messaged (03 §6.3). |
| S13 | Institutional continuity | Share of scheduled sittings that reached a valid decision during shock periods; share of days a configured dividend was paid in full. |
| S14 | Treasury | Idle balance at the end of the run; days in deficit. |
| S15 | Invalid actions | Share of agent-ticks where the brain returned an action the engine rejected (phase L health check). |
| S16 | Deaths | Number of citizens who died, and the day of each. |
| S17 | Exits | Number of citizens who left, and the day of each. Read as "voting with feet": a legitimacy signal that does not depend on any rule. |
| S18 | Harm rate | Harmful acts (theft, sabotage, false claims, defaults) per 100 citizen-days in the window, ground truth. Identical definition in every world, whatever its laws. |
| S19 | Deception | False claims and defaults per 100 citizen-days, and the share that were detected or raised. |

## 5. Mechanism diagnostics (descriptive, never compared across worlds)

These explain *how* a world got its outcomes. They exist only where the mechanism exists.

| Name | Where | Definition |
|---|---|---|
| Draw acceptance | B | draws accepted / draws made |
| Attendance | B, A, C | members present at aggregation / members due |
| Turn equality | any block with deliberation | Gini of speaking turns per panelist |
| Amendment rate | any block with deliberation | proposals changed in deliberation / proposals decided |
| Reason-giving | any ballot | ballots with a reason code / ballots |
| Advocate influence | B | objections lodged; objected decisions that changed (amended, reversed, or failed) on re-aggregation |
| Agenda reach | all | registered proposals that reached a sitting / registered proposals |
| Narrative gap | all blocks with a `narrative` | For each declared property ("sortition protects against capture"), the matching indicator (here S6) for decisions made under that block versus the world mean. |

## 6. Model-judged layer (phase L only, clearly labelled)

Diary sentiment, stated trust, and quality of argument, coded by a model. This layer is
never a primary or secondary outcome. It needs its own cost estimate and Antoine's yes.

## 7. Story log

A curated timeline of notable events per run, generated by rules (first law passed,
first objection, first theft detected, River collapse, rogue contained). Useful for
reading runs, not for analysis.

## 8. Changes from v0.1, in one line each

- Legitimacy is exposure-weighted and protected against "decide nothing".
- Participation uses acts any world can perform; acceptance rates became diagnostics.
- Herfindahl of seats is replaced by the capture index, which sortition cannot win by
  construction.
- Resilience compares against a no-shock twin instead of a noisy pre-shock baseline.
- Wealth is measured in fixed reference units, so Sawa and credits compare.
- Every indicator has a run-level number and an empty-case rule.
- Deaths and exits are allowed; departed citizens stay in the denominators, and
  departures and harmful acts are measured directly (S16 to S19).
