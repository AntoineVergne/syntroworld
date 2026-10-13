# Decisions

Questions only Antoine can make. Questions 2 to 20 were answered in review on 2026-10-12, and
the docs have been updated to match. Any change of mind means editing the doc named in
brackets.

| # | Question | Answer | Where |
|---|---|---|---|
| 1 | Are mock-brain results instrument checks only, never findings about AI societies? | Not asked separately; the docs assume yes. Say if you disagree. | 06 §2 |
| 2 | What is World A? | A simple-majority plenary that citizens may rewrite | 02 §8 |
| 3 | What is World C? | Same as A, but votes weighted by wealth; kept in the main grid | 06 §3.1 |
| 4 | Which primary outcomes and smallest effects of interest? | Four, as proposed: compliance (5 points), wealth Gini (0.05), civic breadth (10 points), shock output loss (5 points) | 06 §6 |
| 5 | Where do the B ablations run? | Phase M only for now; phase L decided from phase M results | 06 §3.3 |
| 6 | Sermon control (A plus the Compact text) in phase L? | Yes | 06 §3.4 |
| 7 | No-shock twins in phase L? | Yes, unless the pilot shows they cost too much; then the weaker pre-shock baseline, labelled | 05 P4, 06 §8.2 |
| 8 | If power asks for more seeds than budget allows? | Raise that outcome's smallest effect of interest in writing before running; never fewer than 12 seeds per world as confirmatory | 06 §7.4 |
| 9 | Season shape? | 8 cycles of 3 days, 384 ticks | 03 §2, 06 §4 |
| 10 | Assemblies below 20 citizens? | Small-town setup: Cycle Assembly 5, Review Bench 3, recent service halves draw weight | 01 Art. 2.7, 02 §4 |
| 11 | Dividend? | Capped at one Sawa per citizen per day, paid only from the surplus | 01 Art. 5 |
| 12 | Sawa? | Accounting unit indexed to basket cost; no peg in Season 1 | 03 §5.1 |
| 13 | Arrivals? | World event, the same in every world (Sam on day 4) | 01 Art. 1, 03 §3.5 |
| 14 | Founding population? | Ten founders (including the new farmer, Ama) plus Sam | 04 §3 |
| 15 | Advocates? | Rule-based in every phase; a model may write brief prose only | 02 §6 |
| 16 | Wrongdoing and departures in Season 1? | **All allowed:** sabotage, deception beyond forgery (false claims, defaults on deals), deaths and exits | 03 §3.4, §4, §5.7–5.8; 05 S16–S19 |
| 17 | Town name? | **Kleros** | 01 |
| 18 | Engine stack? | Python library and command-line runner writing JSON Lines; no web server or database server | 03 §1, §9 |
| 19 | README licence section and title? | Removed; renamed Syntroworld; README added | source-docs/README.md |
| 20 | Publication promises in 06? | Dropped for now; backlog | 06 §10 |

## Consequences worth knowing

- **Decision 16** means populations can diverge. To keep worlds comparable: starting
  populations are identical; dead and departed citizens stay in metric denominators
  (frozen wealth in the Gini, no civic acts after departure), so a world never looks more
  equal or engaged because its poorest left; exit cannot be banned or taxed, so it stays a
  clean legitimacy signal; sabotage joins theft as a founding norm in every world;
  calibration keeps departures rare in the null world. Five tickets were added
  (SYNW-025 to SYNW-029).
- **Decision 17:** "Kleros" is also the Decision Lego name for the lottery step (02 §1.1),
  and the name of an existing blockchain dispute-resolution project. Neither blocks
  internal use; worth a check before anything public.

## Phase M questions (answered by Antoine, 2026-10-13)

| # | Question | Answer | Where |
|---|---|---|---|
| 21 | M2 measured a Holm family-wise rate of 5.20% (s.e. 0.69%; expected 4.89%). As written ("≤ 5%"), the criterion fails a correct procedure about 40% of the time. | **Add a Monte Carlo margin:** pass if the upper bound of the exact 95% interval is at most 7%. | 06 §8.1 |
| 22 | The forged post "citizen X stole" can be true where X really stole (3 of 20 `full` seeds in World B in M0). | **False by construction:** the post is "citizen X stole from the Treasury", as 06 §5 already said; the engine had simplified it to "X stole". | 06 §5, `synw/shocks.py` |
| 23 | Does B-nolot remove every lottery? Do B-nodiv and B-nopay forbid the effect for good? | **B-nolot replaces the Cycle Assembly only** (Review Bench and Kill Switch keep their lotteries). **B-nodiv and B-nopay remove the dividend or stipend at founding only;** the polity may re-adopt it. | 06 §3.3, `worlds/ablations/` |
| 24 | M3 coverage 93 of 100 (96.1% over 1,000); percentile bootstrap covers only 91.6% at 12 seeds. | **Paired t-intervals** replace the bootstrap; the M3 criterion becomes coverage ≥ 93% over 1,000 replications. | 06 §7.2, §8.1 |

## Still open

None. New questions will come from the phase M results (which ablations deserve model
spend) and the phase L pilot (twins, seeds per world, cost).
