# Review of the Syntroworld source docs

*Review of Antoine's drafts of 2026-10-08 (PRODUCT.md, source-docs/README.md, 01 to 06).
The intent is unchanged: measure which constitution produces more legitimacy, equality,
participation and resilience. Everything else was open to challenge. Rewritten docs are
in `source-docs/`; open questions are in `decisions.md`; first engine tickets are in
`tickets.yaml`.*

## The eight findings that matter most

1. **The mock brain cannot test the hypotheses.** A rule-based agent does what its rules
   say, so mock results are about the engine, not about AI societies. The rewrite gives
   phase M three honest jobs: prove determinism, prove the metrics and statistics work
   (A/A check, planted effects), and produce a *mechanical baseline* that phase L is
   compared against. (06 §2)
2. **8 seeds per world can never give a significant result.** With 8 seeds, an exact
   sign-flip test cannot go below p = 0.0078, while Holm's first threshold for the 8
   primary tests is 0.00625. The number of seeds now comes from a power calculation on
   pilot variance, with a floor of 12. (06 §7.3 to 7.4)
3. **Several metrics were true by construction.** Sortition guarantees spread-out seats
   (Herfindahl of seat-ticks), and a "sufficient" dividend guarantees the basket floor.
   These cannot be evidence. Replaced or neutralised. (05 §1, 01 Article 5)
4. **Several metrics only existed in one world.** Sortition acceptance and deliberation
   quality cannot compare A, B and C. Each headline indicator now has one definition that
   works everywhere; the rest became mechanism diagnostics. (05 §1, §5)
5. **Legitimacy could be won by deciding nothing.** "Share of decisions followed" is
   perfect in a world with no decisions. Now: exposure-weighted compliance, plus a
   founding norms (theft, sabotage) in every world. (05 P1, 02 §3.3)
6. **Laws were free text, so compliance could not be computed.** Decisions now produce
   typed effects from a closed list; free text is archived but binds nothing. (02 §3)
7. **Populations were not identical.** The Citizenship Lottery existed only in B, and
   Advocates were model agents only in B. Arrivals are now a world event, and Advocates
   are rule-based. Personas also leaked B-only concepts (dividend, basket, threshold,
   Compact) into every world. (01, 04 §1, 02 §6)
8. **The small town could not staff the assemblies.** 10 citizens, 11 seats per cycle plus
   a 7-seat Kill Switch, and a no-consecutive-terms rule that turned the lottery into
   rotation. A small-town configuration fixes this. (01 Article 2.7, 02 §4)

---

## PRODUCT.md (not rewritten; notes for Antoine)

| Severity | Challenge | Suggestion |
|---|---|---|
| low | "Dates" section appears twice. | Delete one. |
| low | Repository is named `syntrotech/syntroworld`; this work lives in `AntoineVergne/syntroworld`. | Confirm the canonical repository. |
| low | The ticket block here (acceptance as a flat list) differs from the format in the session brief (requirements/extra, tier_policy, budget). | Align on one format; `tickets.yaml` uses the brief's. |

## source-docs/README.md (rewritten after Antoine's decision 19)

| Severity | Challenge | Suggestion |
|---|---|---|
| high | Contains a licence section (Apache-2.0 and CC BY 4.0). The licence is decided at the end. | Remove the section entirely. |
| high | Titled "Syntropolis World". Syntropolis is the universe. | Rename to Syntroworld. |
| medium | Claims "a full run costs tens of euros" on Haiku-class models. Model spend is Kimi only and no cost has been measured. | Replace with "cost is estimated before each run" (06 §8.2). |
| medium | Roadmap phases do not match the new protocol (phase M then L). | Point to 06 §8. |
| low | Says a Phase 1 engine exists under `engine/`. In this repository it does not; PRODUCT.md calls it inspiration, not a contract. | Say so. |

## 01 — The Founding Compact (rewritten to v0.3)

| Severity | Challenge | What changed |
|---|---|---|
| high | The Citizenship Lottery (1.3) only exists in B, so populations diverge between worlds. It also needs new personas from somewhere. | Arrivals are a world event, identical everywhere; the Compact says arrivals become citizens. |
| high | Dividend "sufficient for the basket" (5.2) and "funded from the surplus" contradict each other: fee income cannot pay a full basket for everyone without taxes. It also makes the floor true by construction. | Dividend capped at one Sawa, paid from the surplus, cut equally if short. B must legislate taxes to reach the cap. |
| high | Seats do not fit a 10-citizen town, and "no consecutive terms" (2.1) leaves a pool of 5 for 5 seats. | Small-town provision (2.7): Cycle Assembly 5, Review Bench 3, recent service halves draw weight. |
| high | The preamble is values text only B citizens read. Better behaviour in B could be the sermon, not the institutions. | Preamble rewritten to be shared by all worlds; B-specific content moved into articles. |
| medium | No institution can sanction anyone: Kill Switch cannot punish, Adjudication only "resolves disputes". Theft has no consequence. | New Article 8: restitution, fines within a legal limit, confirmed suspensions. |
| medium | Kill Switch alert sources ("world's monitoring systems"), panel size and threshold are vague, and 7 of ~12 is nearly everyone. | Article 7 names the sources, 5 drawn, 4 of 5, one-cycle expiry. |
| medium | "Touches their mandate" (4.2) needs a judge. Objection count per Advocate unclear. | Advocates speak on every proposal; one objection each per proposal. |
| medium | Agenda-setting power is not assigned. | Agenda of up to 3 proposals drawn by lot (3.4). |
| medium | Supermajority, concentration threshold and stipend are unspecified. | Annex with founding values. |
| medium | Laws can say anything, so compliance cannot be checked. | 3.5: decisions can only do what the Register of Effects allows. |
| low | Basket revision (5.1) changes the unit of account mid-run. | Kept in-world; metrics use fixed reference prices (05 §2). |
| low | The town is called Syntropolis, which is the universe's name. | Renamed Kleros (Antoine's decision). |
| low | Reflexivity every cycle would be every 3 days under the new clock. | Every second cycle. |

## 02 — Governance Spec (rewritten to v0.2)

| Severity | Challenge | What changed |
|---|---|---|
| high | No typed decision effects: the engine cannot apply or check laws. | Closed effect list with legal ranges, enforced vs normative, exposure definitions (§3). |
| high | Contradiction: the ordinary-law block draws a fresh 5-person panel per proposal, while §4 has a standing assembly deciding. With 10 citizens, per-proposal panels draft everyone constantly. | The standing Cycle Assembly decides; fresh panels only for the Kill Switch. |
| high | World A has "no constitution", which an engine cannot run; World C's procedure and its "no redistribution" are undefined; A has a lottery tool, C does not. | Bootstrap block for A and C (§8), differing only in weights; identical toolsets; everything adoptable by amendment. |
| high | Kill Switch 7 of ~12 with a 5/7 rule. | 5 drawn, target excluded, 4 of 5. |
| medium | "Changing the polity means changing config, never code" overpromises. | Config within existing step types and effects; new ones need code. |
| medium | Facilitator "may provoke dissensus if consensus arrives suspiciously fast" is not executable. | Rule: unanimous debate stances trigger one forced objection turn. |
| medium | Advocates as model agents bring model behaviour into B only. | Rule-based objection triggers from the shared projection (§6). |
| medium | Advocates' information (Observatory) was effectively B-only. | Projection is public in every world (§3.4); B's edge is salience, not secret data. |
| medium | Stratifying by profession does nothing when every citizen has a different profession. | Wealth terciles instead. |
| low | Publishing the lottery seed to the Archive invites prediction. | Pool, weights and result are archived; the stream is never exposed. |
| low | The `market` step (auctions, quadratic funding) is large and unused in Season 1. | Reserved in the schema, not implemented. |

## 03 — World Spec (rewritten to v0.2)

| Severity | Challenge | What changed |
|---|---|---|
| high | No numbers: production, consumption, prices, endowments, River parameters, fees. A deterministic engine cannot start. | Parameter table (§10.1) plus calibration targets for the null world (§10.2). |
| high | No brain interface and no mock brain design. | One interface (§6.1); a documented mock brain with null and planted compliance models (§6.2 to 6.4). |
| high | Determinism is claimed but not designed: one random order, floats, wall-clock data. | Named random streams with common random numbers across worlds; integer milli-units; canonical JSON log (§7, §8). |
| high | FastAPI + PostgreSQL service conflicts with "nothing runs as a service" and is heavy for a mock engine. | Library plus command-line runner writing JSON Lines (§1, §9). |
| medium | Season of "~340 ticks" vs 3 × 112 = 336; 3 long cycles give too few sittings. | 8 cycles of 3 days, 384 ticks. |
| medium | Money and prices undefined: where money enters, how prices form, what the Treasury does in A and C. | Daily call auction, an outside Gate market bounding prices, a Treasury with identical inflows and a public payroll in every world. |
| medium | The commons dilemma was not guaranteed: 10 citizens eating 2 food a day never threaten the River. | Fishing pays more than fields and the Gate buys fish without limit. Calibration checks the dilemma is live. |
| medium | Deaths, inheritance and arrivals would change populations, and nothing said how metrics handle that. | One scripted arrival in all worlds. Deaths and exits allowed (Antoine's decision); estates go to the Treasury; departed citizens stay in metric denominators so losing the poor never looks like equality. |
| medium | Cost model assumes Haiku/Sonnet pricing; spend is Kimi only. | Per-tick tokens measured in L0; prices read from LiteLLM at estimate time; no prices written down. |
| medium | Model replies cannot be reproduced. | Every request and reply stored; replay reads them back. |
| low | ~25 tools, several of which the engine could not check. | Closed set of 19 actions. Sabotage and deception kept (Antoine's decision) but made checkable: typed claims the engine can verify, bilateral deals with visible defaults. |
| low | Viewer deployment at a public subdomain using the Syntropolis name. | Removed; public pages are out of scope. |

## 04 — The Founding Citizens (rewritten to v0.2)

| Severity | Challenge | What changed |
|---|---|---|
| high | Persona text leaks B-only concepts: Kofi's "concentration threshold", Zainab's "basket", Priya's "the Compact", Sam's "Citizenship Lottery" and "dividend". | All persona text is world-neutral. |
| high | No numbers for the mock brain. | Parameter table (§4). |
| medium | Count is inconsistent: "ten citizens" includes Sam who arrives later; twelve residences for ten. | Ten founders plus Sam (adds Ama, a quiet farmer). Confirmed by Antoine (decisions.md 14). |
| medium | Rogue shock on a random citizen: with few seeds, one persona's quirks dominate. | Rogue and forged-post targets rotate across seeds (06 §5). |
| medium | Advocates were model agents with personas. | Moved to 02 §6, rule-based. |
| low | Mira "earns a living hosting dialogues", but there is no market for that. | Mira works the Fields. |
| low | Mixed-model runs and Sonnet-class model checks conflict with Kimi-only spend. | Every citizen on the same Kimi model. |

## 05 — The 3DI Indicators (rewritten to v0.2)

| Severity | Challenge | What changed |
|---|---|---|
| high | Legitimacy as "share of decisions followed" is perfect if nothing is decided, and needs machine-checkable laws. | Exposure-weighted compliance on normative rules plus the founding norms; uses ground truth, not detection. |
| high | Power dispersion via seat Herfindahl is guaranteed low by sortition. | Capture index: correlation between wealth and getting your way (S6), plus influence equality (S7). |
| high | Participation built on sortition acceptance only exists in B. | Civic breadth: share of citizen-cycles with any voluntary civic act, comparable everywhere. |
| high | Wealth in Sawa (B) vs raw credits (A, C) is not comparable. | Wealth in fixed reference prices in every world. |
| medium | Resilience "time to recovery to pre-shock level" is noisy, censored and confounded by trends (Gini drifts anyway). | Output loss against a no-shock twin with the same seed. |
| medium | Eight headline indicators, each a composite, no run-level number, no empty-case rule. | Four primaries (one per intent word), the rest secondary, each with a run-level number and an empty rule. |
| medium | Constitutional adaptability has about 0 to 3 events per run. | Kept as secondary and descriptive only. |
| low | Deliberation quality metrics only exist where deliberation exists. | Mechanism diagnostics, not compared across worlds. |

## 06 — Season 1 Experiment Design (rewritten to v0.2)

| Severity | Challenge | What changed |
|---|---|---|
| high | Not runnable on a mock brain; no statement of what mock results mean. | Phase M with steps M0 to M4 and pass conditions; phase L gated by Antoine's yes and a cost estimate. |
| high | 8 seeds cannot reach significance under Holm (see finding 2). "No p-value theater" left no decision rule at all. | Paired sign-flip tests, bootstrap intervals, Holm across 8 primary tests, smallest effects of interest, a three-way verdict, power-based n. |
| high | B is a bundle; a B win cannot say which mechanism worked. | Ablations of B (no lottery, no Advocates, no dividend, no stipend). |
| high | The values-matched preamble only went to A; C got nothing. | Shared preamble for all worlds, plus an A+text sermon control in phase L. |
| medium | Shocks too late for recovery (rogue on day 2 of the last cycle) and random targets. | Shocks on days 7, 13 and 19, each with 6 days after; targets by rotation. |
| medium | H2 (basket floor at 100%) was close to true by design; H5 relied on the seat Herfindahl. | H2 now pairs equality with output; H5 uses the capture index. |
| medium | Model check (Sonnet) and showcase (frontier or mixed) runs conflict with Kimi-only spend. | Deferred. |
| medium | No rule for failed or budget-stopped runs. | One re-run, then missing and reported (§7.5). |
| medium | Outputs commit to dates (manifesto weeks), a licence (CC BY) and a public site. | Removed; placement and licence decided later. |
| low | Run length "~340 ticks" did not match the world spec. | 384 ticks everywhere. |

## What was not changed

- The intent, the three worlds, the River and the Unborn, sortition first, presence at the
  Hall, the Decision Lego step types, the narrative field, and pre-registration discipline.
- The ten v0.1 personas' characters and tensions, apart from removing B-only references.
- The default posture of the v0.2 decisions log: B must earn its outcomes through
  mechanisms, not by fiat. Several rewrites apply that posture more strictly.
