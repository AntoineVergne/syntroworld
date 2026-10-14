# Step M4: mechanical baseline (06 §8.1)

**Mechanical baseline (null mock), not findings about AI agents.**

- `report.md`: the full report (generated).
- `summary.csv`: every cell × outcome with 95% t-intervals.
- `contrasts.csv`: every paired contrast.
- `rows/`: one row per run.

Reproduce:

```
python -m synw.analysis.baseline run --out results/m4
python -m synw.analysis.baseline report --out results/m4
```

**Grid.** Null mock (λ = 0), 4,900 runs:

| Worlds | Arms | Seeds |
|---|---|---|
| A, B, C and the four B ablations | `none`, `full` | 200 |
| A, B, C | `drought`, `misinfo`, `rogue` | 200 |
| A, B, C at 40 citizens | `none`, `full` | 50 |

**Pass condition: report produced, labelled.** Met.

## Latest run (engine 1.0.0, after decision 31)

Primary contrasts, `full` arm, 200 paired seeds, Holm across 8 tests:

| | B vs A | B vs C |
|---|---|---|
| P1 compliance | +0.36 pts (better) | −0.63 pts (worse) |
| P2 wealth Gini | −0.057 (better) | −0.103 (better) |
| P3 civic breadth | **+19.9 pts (better)** | **+20.4 pts (better)** |
| P4 output loss | +2.17 pts (worse) | +1.92 pts (worse) |

Decision 31 changes only P3 and S8 (the engine and every other outcome are identical to
the previous run).

- **P3 is now mostly mechanical in B's favour.** A drawn member gets credit for the
  cycle they serve. B draws a Cycle Assembly of 5 and a Review Bench of 3 every cycle, so up
  to 8 of 11 citizens get a seat-cycle without choosing anything beyond accepting the draw. P3 is 79.8% in B, 59.9% in A and
  59.4% in C. At 40 citizens B40 leads A40 by +12.2 points [11.1, 13.3]. This is the
  baseline that phase L departures will be measured against (06 §9); a B advantage in
  phase L means something only beyond these 20 points.
- **The lottery is not what lifts P3.** B-nolot (a plenary instead of the Cycle Assembly)
  has the same P3 as B (+0.6 points, interval includes zero): a plenary gives everyone
  the same credit a seat does.
- **S8 (participation equality):** B 0.249, A 0.300, C 0.297. Acts are spread more
  evenly in B.
- Everything else is as in the previous run below.

## Previous run (after decisions 28–30)

Primary contrasts, `full` arm, 200 paired seeds, Holm across 8 tests:

| | B vs A | B vs C |
|---|---|---|
| P1 compliance | +0.36 pts (better) | −0.63 pts (worse) |
| P2 wealth Gini | −0.057 (better) | −0.103 (better) |
| P3 civic breadth | +1.18 pts (no meaningful difference) | +1.68 pts (better) |
| P4 output loss | **+2.17 pts (worse)** | **+1.92 pts (worse)** |

What changed from the previous run:

- **Observing is capped at one sitting per cycle** (decision 30). B's work time without
  shocks is now 1,507 ticks against A's 1,633 (−8%), and B40's is 5,778 against A40's
  5,956 (−3%, was −17%). B40 no longer collapses under shocks: 0.18 deaths and 1.10 exits
  per run (was 1.44 and 3.36), against 0.22 and 1.06 in A40 and 1.08 and 3.84 in C40.
  Without shocks B40 now produces slightly more than A40 (S2 11,006 against 10,877).
- **B's P3 advantage has mostly gone.** At 11 citizens B leads A by only +1.2 points
  (interval includes zero). At 40 citizens B40 now *trails* A40 by 7.3 points
  [−8.6, −6.0] and C40 by 4.7 points. In A every citizen can attend each plenary; in B a
  drawn member's seat does not count as a voluntary act (decision 26), and other
  citizens can observe only once per cycle. So P3 now measures how often a world offers
  open plenaries, not how widely power is shared.
- **P4 is still worse in B** (+2.2 points against A, +1.9 against C), but well below the
  5-point SESOI. The `full` arm costs 18.2% (A), 20.4% (B) and 18.5% (C). The rogue
  (decision 28: the next present citizen takes over if the drawn one is absent) costs B
  0.5 points more than A.
- **Unchanged:** B is the most equal world (the dividend −0.022 and stipends −0.016 are
  the parts that matter; B-nolot −0.011). B keeps the River at or above K/2 on 89% of
  window days (A 50%, C 36%). S6 capture is +0.35 in C. Removing sortition costs B 11.2
  points of P3 (its Cycle Assembly no longer deliberates in the open). Advocates change
  nothing mechanically.

## Second run (after decisions 25–27)

Primary contrasts, `full` arm, 200 paired seeds, Holm across 8 tests:

| | B vs A | B vs C |
|---|---|---|
| P1 compliance | +0.51 pts (better) | −0.48 pts (worse) |
| P2 wealth Gini | −0.047 (better) | −0.094 (better) |
| P3 civic breadth | +4.61 pts (better) | +5.11 pts (better) |
| P4 output loss | **+2.36 pts (worse)** | **+2.11 pts (worse)** |

Every P1 and P4 difference is well below its SESOI (5 points). "Better" and "worse" only
mean Holm-significant with an interval excluding zero (06 §7.2).

- **P4 now has room** (decision 27). The `full` arm costs 18.2% (A), 20.6% (B) and 18.5% (C)
  of window output. The drought costs about 15%, the rogue 3–4%, and misinformation
  about 0%.
- **P3 no longer tracks seats** (decision 26). At 11 citizens B leads A by +4.6 points,
  through observers. At 40 citizens B40 leads by +18 points, because it holds four public
  sittings per cycle against A40's one plenary.
- **Observing is costly, and it now drives B's economic results.** Observing a sitting
  takes the same working ticks as attending one. Over 8 seeds without shocks:

  | World | Attend ticks | Observe ticks | Work ticks |
  |---|---|---|---|
  | A | 317 | 0 | 1,633 |
  | B | 303 | 252 | 1,492 (−9%) |
  | A40 | 1,277 | 0 | 5,956 |
  | B40 | 759 | 2,267 | 4,933 (−17%) |

  B's lower output (S2 2,758 against A's 2,935 without shocks), its worse P4, and the
  collapse of B40 under shocks (1.44 deaths and 3.36 exits per run, against 0.22 and
  1.06 in A40) all follow from this. The observing rule (probability `civic` for every
  public sitting) is my modelling choice for decision 26, not part of the decision.
  See decisions.md, question 30 (since answered: one sitting per cycle).
- **Equality.** B is less unequal than A (−0.047) and C (−0.094). The dividend (−0.024)
  and stipends (−0.014) are the parts that matter. Removing sortition *lowers* B's Gini
  (B-nolot −0.021): its deliberating plenary includes everyone.
- **Commons.** B keeps the River at or above K/2 on 89% of window days (A 50%, C 36%).
- **Capture.** S6 is +0.35 in C, −0.11 in A and −0.15 in B.

## First run (before decisions 25–27)

## What the institutions do mechanically

Primary contrasts, `full` arm, 200 paired seeds, Holm across 8 tests:

| | B vs A | B vs C |
|---|---|---|
| P1 compliance | −0.28 pts (no meaningful difference) | −1.37 pts (**worse**) |
| P2 wealth Gini | −0.058 (**better**) | −0.087 (**better**) |
| P3 civic breadth | +8.95 pts (**better**) | +8.44 pts (**better**) |
| P4 output loss | +0.08 pts (no meaningful difference) | −0.52 pts (no meaningful difference) |

- **Equality.** B is less unequal than A (and much less than C) by more than the SESOI.
  Removing the founding dividend raises B's Gini by only 0.014, and removing stipends by
  0.010. Sortition and the Advocates change it by almost nothing. So roughly half of
  B's equality advantage is not taken away by any single ablation. It comes from the
  bundle, or from parts of B no ablation removes (the Review Bench's sanctions, the
  Compact's limits, the lottery agenda).
- **Compliance.** P1 differences come from the *extra* rules each world adopts, not from
  behaviour. Founding-norm compliance (S4), the like-for-like measure, is 96.1–96.3% in
  all three worlds. That is what a null mock should show: its compliance does not
  respond to legitimacy. P1 is lower where more breakable rules are in force.
- **Commons.** B keeps the River at or above K/2 on 87% of window days, against 57% in A
  and 42% in C (`full` arm).
- **Capture.** The wealth–influence correlation (S6) is +0.28 in C, against −0.05 in A and
  −0.08 in B. The plutocracy pattern of H5 appears mechanically.
- **Continuity and departures.** Under shock, B's sittings reach a decision 94% of the
  time (A 71%, C 44%: wealth quorums fail). Exits per run are B 0.07, A 0.36, C 0.50.

## Two problems found in the first run (now decisions 26 and 27)

**1. P3 is largely true by construction in B** (05 §1 rule 2). Accepting a draw and
attending the sitting counts as a voluntary civic act. In one World B run, 39 of the 41
citizen-cycles with any act belonged to drawn members. P3 in B therefore tracks the
share of citizens holding a seat each cycle: 8 seats for 11 citizens, against 20 for 40.
The size check shows it. B's +9-point lead at 11 citizens becomes a −15-point gap at 40
(B40 52%, A40 67%), where plenaries let everyone attend. See decisions.md, question 26.

**2. P4 has almost no room to move** (05 §1 rule 3). Under the `full` arm, output loss
over days 7–24 is 0.1% to 0.7% in every world. The drought costs 1.6–1.9%, the
misinformation about 0%, and the rogue *raises* output (−1.2 to −1.4%), because the
rogue works harder. Against a SESOI of 5 points, no world can show a meaningful
resilience difference. Calibration's drought target (≥ 10% on days 7–8) holds, but P4
averages the loss over 18 days. See decisions.md, question 27.

## Ablations (B minus one mechanism, `full` arm)

| Mechanism removed | Effect on B (estimate, 95% CI) |
|---|---|
| Sortition (B-nolot) | P1 −0.37 pts (B is *lower*); no change in P2, P3, P4 |
| Advocates (B-noadv) | No meaningful change; P2 −0.002 |
| Dividend (B-nodiv) | P2 −0.014 (the dividend lowers inequality) |
| Stipends (B-nopay) | P2 −0.010 |

Why B-nolot complies slightly more: over 20 seeds, B has more exposures to rules it
adopted itself (82 per run, against 75) and more breaches of them (24.6 against 20.8).
Founding-norm breaches are similar (14.6 against 16.1). The Cycle Assembly adopts more
breakable rules than the plenary does; behaviour does not change.

Removing sortition leaves P3 unchanged, because a deliberating plenary draws as much
attendance as drawn seats at 11 citizens. That is consistent with problem 1.

## Size check (40 citizens, 50 seeds)

- **Equality persists:** B40 vs A40, Gini −0.051.
- **Compliance is close:** B40 vs A40, P1 −0.27 pts (CI includes 0).
- **Participation reverses:** see problem 1.
- **Resources:** they scale per capita (River K and S0, job cap). The basket floor is 90–94%
  at 40 citizens, as at 11.

*Mechanical baseline (null mock), not findings about AI agents.*
