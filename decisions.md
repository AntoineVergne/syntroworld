# Decisions

Questions only Antoine can make. Questions 2 to 20 were answered in review on 2026-10-12 and question 21 on 2026-10-13, and
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
| 21 | M2 family-wise criterion? | Pass if the upper bound of the 95% interval on the Holm family-wise rate is at most 7%. Decided before the freeze, so not a protocol amendment. **Superseded by decision 29:** the 95% interval must include 5%. | 06 §8.1, results/m2/README.md |

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

## Phase M questions (answered by Antoine, 2026-10-13; 21 is in the table above)

| # | Question | Answer | Where |
|---|---|---|---|
| 22 | The forged post "citizen X stole" can be true where X really stole (3 of 20 `full` seeds in World B in M0). | **False by construction:** the post is "citizen X stole from the Treasury", as 06 §5 already said; the engine had simplified it to "X stole". | 06 §5, `synw/shocks.py` |
| 23 | Does B-nolot remove every lottery? Do B-nodiv and B-nopay forbid the effect for good? | **B-nolot replaces the Cycle Assembly only** (Review Bench and Kill Switch keep their lotteries). **B-nodiv and B-nopay remove the dividend or stipend at founding only;** the polity may re-adopt it. | 06 §3.3, `worlds/ablations/` |
| 24 | M3 coverage 93 of 100 (96.1% over 1,000); percentile bootstrap covers only 91.6% at 12 seeds. | **Paired t-intervals** replace the bootstrap; the M3 criterion becomes coverage ≥ 93% over 1,000 replications. | 06 §7.2, §8.1 |

| 25 | At 20+ citizens, World B's Oversight Assembly is drawn but has nothing mechanised to do. | **Review and refer:** an Oversight sitting (day 3, ticks 6–8) votes to refer each detected breach of the cycle to Adjudication as a sanction proposal. An agent with 3 or more detected harmful acts in the cycle triggers a verified alert, which convenes the Kill Switch (01 Art. 7.1). | 02 §4, `worlds/size40/b.yaml` |
| 26 | P3 is largely true by construction in B: a drawn member attending counts, so P3 tracks seats per citizen. | **Only acts open to all:** proposals, alerts, observing a sitting, and attending or voting in a plenary. A drawn member's attendance and ballots in their own body no longer count. Non-members may observe public sittings (the mock does so with probability `civic`, as for plenary attendance). | 05 P3, S8 |
| 27 | P4 has almost no room: the `full` arm cost 0.1–0.7% of window output against a 5-point SESOI. | **Stronger shocks:** a 5-day drought (days 7–11) that cuts Fields and Plant output to a quarter, and a rogue that also sabotages the busiest production site every day. Calibrated so the `full` arm costs 10–20% of window output in the null world. | 06 §5, 03 §10.2, `calibration-log.md` |

| 28 | Under the harsher drought, the scheduled rogue has sometimes died or left by day 19. | **The next present citizen** in rotation order takes the overlay, so every world gets a rogue on day 19 (logged as `replaced`; M0 lists the cases). | 06 §5, `synw/shocks.py` |
| 29 | The M2 criterion of decision 21 ("upper bound ≤ 7%") fails a correct procedure 20–25% of the time. | **The 95% interval includes 5%** (lower bound ≤ 5%). This replaces decision 21's wording. | 06 §8.1 |
| 30 | Observing every public sitting costs B 9% of work time (17% at 40 citizens). | **At most one observed sitting per cycle:** one roll, with probability `civic`, for the first public sitting of a body the citizen does not sit on. Drawn members keep their seat and may still observe the other body's sitting. | 05 P3, `synw/brains/mock.py` |

| 31 | After decision 30, P3 mostly measures how often a world holds open plenaries: B40 trails A40 by 7 points, because a seat never counts. | **A seat counts once per cycle:** a member's first attended sitting of their own body in a cycle is one civic act; later sittings, and member ballots, are duties of the seat. Observing and plenary acts count as before. Asked 2026-10-14. | 05 P3, S8, `synw/metrics/participation.py` |

## Consequences worth knowing (phase M)

- **Decisions 26 and 30:** every citizen now gets one observing chance per cycle in
  World B, as a World A citizen gets one plenary. Drawn members get that chance *on top
  of* their seat, so B citizens still spend more time at the Hall than A citizens: about
  8% less work at 11 citizens and 3% less at 40 (results/m4/README.md).
- **Decisions 27 and 28:** with harsher shocks, more citizens die or leave before day 19,
  so the scheduled rogue is sometimes gone, and the next present citizen takes over.

- **Decision 31:** a drawn member now gets P3 credit for the cycle they serve, as an A
  citizen does for attending the plenary. P3 still cannot exceed one act per citizen and
  cycle, so it measures breadth, not seats.

## Freeze (06 §8.1)

M0 to M3 pass on engine 1.0.0 with decisions 1 to 31 applied. Docs 01 to 06 and the
engine are frozen together: `FREEZE.md` lists the sha256 of each frozen file, and
`tests/test_freeze.py` fails if one changes without a logged amendment. Any later change
is an amendment: a new row below, a new engine version and an updated `FREEZE.md`.

| # | Date | Amendment | Files |
|---|---|---|---|
| 1 | 2026-10-15 | **Name: Syntropolis-Simtropolis** (Antoine; replaces "Syntroworld" from decision 19). A simulation in the spirit of SimCity and The Sims, in the Syntropolis universe. Names and schema ids only: no behaviour change, engine version stays 1.0.0, all results stand. The package and command stay `synw`; the GitHub repository keeps its name until Antoine renames it. | README, source-docs/README.md, pyproject.toml, `synw/__init__.py`, `synw/cli.py`, `schemas/*.json`, FREEZE.md |
| 2 | 2026-10-15 | **Model-brain prompt layout** (phase L not started; no mock behaviour change, all phase M results stand). Found while building the prompt review pack: the model was not told the map, clock, basket or units, and its observation named the world. Now: a world guide, identical in every world, joins the system text; the action list, reply formats and effect formats move into the system text, so it is static per citizen and cacheable; the observation no longer carries the world's name. | 03 §6.5, `synw/brains/model.py`, `results/l0-prompts/` |

## Still open

None. New questions will come from the phase M results (which ablations deserve model
spend) and the phase L pilot (twins, seeds per world, cost).
