# Step M4: mechanical baseline (06 §8.1)

**Mechanical baseline (null mock), not findings about AI agents.**

Every number below comes from the null mock: rule-following agents whose behaviour does
not respond to how legitimate an institution is. Differences between worlds are what the
institutions do *mechanically*: through rules, sanctions, money and information. Phase L
compares model societies against this baseline (06 §2).

Means with 95% t-intervals over seeds. Paired contrasts are by seed (common random numbers).
Files: `summary.csv` (every cell and outcome), `contrasts.csv`, raw rows in `rows/`.

## Primary outcomes, worlds A, B, C

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| A | none | 200 | 93.6% (93.4%–93.8%) | 0.297 (0.291–0.304) | 60.7% (59.6%–61.8%) | 0.0% (0.0%–0.0%) |
| A | full | 200 | 91.3% (91.1%–91.5%) | 0.371 (0.361–0.380) | 59.9% (58.8%–61.0%) | 18.2% (17.5%–19.0%) |
| B | none | 200 | 93.6% (93.5%–93.8%) | 0.256 (0.251–0.261) | 61.6% (60.7%–62.6%) | 0.0% (0.0%–0.0%) |
| B | full | 200 | 91.6% (91.4%–91.8%) | 0.314 (0.306–0.321) | 61.1% (60.3%–61.9%) | 20.4% (19.5%–21.3%) |
| C | none | 200 | 94.4% (94.2%–94.7%) | 0.328 (0.319–0.337) | 61.5% (60.4%–62.6%) | 0.0% (0.0%–0.0%) |
| C | full | 200 | 92.3% (92.0%–92.5%) | 0.417 (0.404–0.430) | 59.4% (58.3%–60.5%) | 18.5% (17.6%–19.4%) |

## Economy, commons and harm

| World | Arm | n | S1 basket floor | S2 output (credits) | S3 days River ≥ K/2 | S4 founding-norm compliance | S16 deaths per run | S17 exits per run | S18 harm per 100 citizen-days |
|---|---|---|---|---|---|---|---|---|---|
| A | none | 200 | 91.8% (91.2%–92.5%) | 2,935 (2,908–2,962) | 71.2% (65.9%–76.5%) | 96.8% (96.6%–96.9%) | 0.01 (-0.00–0.03) | 0.34 (0.27–0.41) | 8.7 (8.4–8.9) |
| A | full | 200 | 79.8% (78.9%–80.6%) | 2,397 (2,369–2,425) | 50.2% (44.5%–55.9%) | 94.9% (94.7%–95.0%) | 0.10 (0.06–0.15) | 0.79 (0.67–0.90) | 13.6 (13.2–13.9) |
| B | none | 200 | 92.2% (91.6%–92.8%) | 2,820 (2,788–2,853) | 96.9% (95.1%–98.8%) | 97.0% (96.8%–97.1%) | 0.02 (0.00–0.04) | 0.27 (0.20–0.33) | 8.0 (7.7–8.2) |
| B | full | 200 | 81.0% (80.3%–81.8%) | 2,238 (2,211–2,264) | 88.7% (85.2%–92.2%) | 95.1% (95.0%–95.3%) | 0.14 (0.09–0.20) | 0.61 (0.51–0.71) | 12.8 (12.5–13.1) |
| C | none | 200 | 90.6% (89.9%–91.3%) | 2,974 (2,945–3,004) | 52.7% (47.1%–58.3%) | 96.9% (96.7%–97.0%) | 0.03 (0.00–0.05) | 0.48 (0.41–0.56) | 8.6 (8.3–8.8) |
| C | full | 200 | 76.2% (74.9%–77.6%) | 2,421 (2,389–2,454) | 35.6% (30.0%–41.1%) | 94.8% (94.6%–94.9%) | 0.23 (0.14–0.32) | 1.23 (1.05–1.40) | 13.9 (13.6–14.3) |

## Governance outcomes (`full` arm)

| World | Arm | n | S5 loser's compliance | S6 capture index | S7 influence Gini | S8 participation Gini | S10 rogue theft (credits) | S11 containment (ticks) | S12 misbelief (citizen-days) | S13 sittings decided under shock | S13 dividend days paid in full | S14 idle Treasury (credits) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | full | 200 | 68.4% (65.4%–71.3%) | -0.11 (-0.16–-0.06) | 0.175 (0.161–0.188) | 0.301 (0.293–0.309) | 17 (16–19) | 69 (65–73) | 38 (36–41) | 73.5% (70.7%–76.3%) | 41.1% (36.6%–45.7%) | 78 (62–93) |
| B | full | 200 | 71.2% (67.8%–74.6%) | -0.17 (-0.22–-0.13) | 0.126 (0.120–0.133) | 0.278 (0.270–0.287) | 17 (15–18) | 48 (44–51) | 43 (40–45) | 90.9% (89.6%–92.2%) | 0.8% (0.5%–1.1%) | 78 (77–79) |
| C | full | 200 | 71.3% (68.0%–74.6%) | +0.35 (+0.31–+0.40) | 0.289 (0.266–0.312) | 0.298 (0.289–0.306) | 18 (17–20) | 79 (75–82) | 38 (36–41) | 41.7% (38.8%–44.7%) | 54.2% (48.9%–59.6%) | 174 (140–208) |

## Primary contrasts (`full` arm, 8 tests, Holm)

Paired by seed. Sign-flip test with 100,000 random flips; Holm across the 8 tests; verdicts per 06 §7.2.

| Contrast | Outcome | n | Estimate | 95% CI | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| B vs A | P1 compliance | 200 | +0.36 pts | +0.09 pts to +0.63 pts | 0.01027 | 0.03081 | better |
| B vs A | P2 wealth Gini | 200 | -0.057 | -0.068 to -0.045 | 0.00001 | 0.00008 | better |
| B vs A | P3 civic breadth | 200 | +1.18 pts | -0.13 pts to +2.49 pts | 0.07954 | 0.07954 | no meaningful difference |
| B vs A | P4 output loss | 200 | +2.17 pts | +0.98 pts to +3.35 pts | 0.00038 | 0.00190 | worse |
| B vs C | P1 compliance | 200 | -0.63 pts | -0.95 pts to -0.32 pts | 0.00013 | 0.00078 | worse |
| B vs C | P2 wealth Gini | 200 | -0.103 | -0.119 to -0.088 | 0.00001 | 0.00008 | better |
| B vs C | P3 civic breadth | 200 | +1.68 pts | +0.27 pts to +3.10 pts | 0.02085 | 0.04170 | better |
| B vs C | P4 output loss | 200 | +1.92 pts | +0.62 pts to +3.23 pts | 0.00431 | 0.01724 | worse |

Better is: higher P1 and P3, lower P2 and P4. SESOI: P1 5 points, P2 0.05, P3 10 points, P4 5 points.

## A vs C (secondary)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| A vs C | full | P1 compliance | 200 | -0.99 pts | -1.24 pts to -0.74 pts | 0.0000 |
| A vs C | full | P2 wealth Gini | 200 | -0.046 | -0.057 to -0.036 | 0.0000 |
| A vs C | full | P3 civic breadth | 200 | +0.50 pts | -0.67 pts to +1.67 pts | 0.4094 |
| A vs C | full | P4 output loss | 200 | -0.24 pts | -1.18 pts to +0.70 pts | 0.6144 |

## B vs A and B vs C without shocks (`none` arm)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs A | none | P1 compliance | 200 | +0.09 pts | -0.14 pts to +0.32 pts | 0.4355 |
| B vs A | none | P2 wealth Gini | 200 | -0.042 | -0.050 to -0.034 | 0.0000 |
| B vs A | none | P3 civic breadth | 200 | +0.95 pts | -0.45 pts to +2.36 pts | 0.1863 |
| B vs A | none | P4 output loss | 200 | +0.00 pts | +0.00 pts to +0.00 pts | 1.0000 |
| B vs C | none | P1 compliance | 200 | -0.76 pts | -1.04 pts to -0.48 pts | 0.0000 |
| B vs C | none | P2 wealth Gini | 200 | -0.072 | -0.082 to -0.062 | 0.0000 |
| B vs C | none | P3 civic breadth | 200 | +0.14 pts | -1.15 pts to +1.42 pts | 0.8427 |
| B vs C | none | P4 output loss | 200 | +0.00 pts | +0.00 pts to +0.00 pts | 1.0000 |

## Ablations: B minus one mechanism (`full` arm)

A positive estimate means B scores higher than the ablation, i.e. the mechanism raises that outcome.

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs B-nolot | full | P1 compliance | 200 | -0.24 pts | -0.48 pts to +0.01 pts | 0.0576 |
| B vs B-nolot | full | P2 wealth Gini | 200 | +0.011 | +0.002 to +0.020 | 0.0190 |
| B vs B-nolot | full | P3 civic breadth | 200 | -11.23 pts | -12.40 pts to -10.07 pts | 0.0000 |
| B vs B-nolot | full | P4 output loss | 200 | +1.26 pts | +0.03 pts to +2.50 pts | 0.0450 |
| B vs B-noadv | full | P1 compliance | 200 | -0.09 pts | -0.18 pts to +0.01 pts | 0.0656 |
| B vs B-noadv | full | P2 wealth Gini | 200 | +0.001 | -0.002 to +0.004 | 0.3976 |
| B vs B-noadv | full | P3 civic breadth | 200 | -0.02 pts | -0.61 pts to +0.58 pts | 0.9806 |
| B vs B-noadv | full | P4 output loss | 200 | +0.24 pts | -0.31 pts to +0.79 pts | 0.3978 |
| B vs B-nodiv | full | P1 compliance | 200 | -0.09 pts | -0.31 pts to +0.12 pts | 0.3971 |
| B vs B-nodiv | full | P2 wealth Gini | 200 | -0.022 | -0.030 to -0.015 | 0.0000 |
| B vs B-nodiv | full | P3 civic breadth | 200 | +0.91 pts | -0.12 pts to +1.94 pts | 0.0847 |
| B vs B-nodiv | full | P4 output loss | 200 | +0.65 pts | -0.46 pts to +1.76 pts | 0.2527 |
| B vs B-nopay | full | P1 compliance | 200 | -0.03 pts | -0.21 pts to +0.16 pts | 0.7776 |
| B vs B-nopay | full | P2 wealth Gini | 200 | -0.016 | -0.021 to -0.011 | 0.0000 |
| B vs B-nopay | full | P3 civic breadth | 200 | -0.28 pts | -1.24 pts to +0.68 pts | 0.5785 |
| B vs B-nopay | full | P4 output loss | 200 | -0.01 pts | -0.93 pts to +0.91 pts | 0.9806 |

## Ablation cells

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| B-nolot | none | 200 | 93.6% (93.4%–93.7%) | 0.248 (0.244–0.253) | 73.4% (72.4%–74.3%) | 0.0% (0.0%–0.0%) |
| B-nolot | full | 200 | 91.9% (91.7%–92.0%) | 0.303 (0.297–0.309) | 72.3% (71.4%–73.2%) | 19.1% (18.3%–20.0%) |
| B-noadv | none | 200 | 93.6% (93.4%–93.8%) | 0.257 (0.252–0.262) | 61.9% (60.9%–62.8%) | 0.0% (0.0%–0.0%) |
| B-noadv | full | 200 | 91.7% (91.5%–91.9%) | 0.313 (0.306–0.320) | 61.1% (60.3%–61.9%) | 20.2% (19.3%–21.1%) |
| B-nodiv | none | 200 | 93.7% (93.6%–93.9%) | 0.267 (0.262–0.272) | 61.4% (60.5%–62.2%) | 0.0% (0.0%–0.0%) |
| B-nodiv | full | 200 | 91.7% (91.5%–91.9%) | 0.336 (0.329–0.343) | 60.2% (59.3%–61.1%) | 19.8% (18.8%–20.7%) |
| B-nopay | none | 200 | 93.6% (93.5%–93.8%) | 0.266 (0.261–0.271) | 62.0% (61.2%–62.8%) | 0.0% (0.0%–0.0%) |
| B-nopay | full | 200 | 91.7% (91.5%–91.8%) | 0.330 (0.323–0.337) | 61.4% (60.4%–62.3%) | 20.4% (19.6%–21.3%) |

## Single-shock arms

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| A | drought | 200 | 93.7% (93.5%–93.9%) | 0.367 (0.357–0.376) | 59.2% (58.1%–60.4%) | 14.4% (13.6%–15.2%) |
| A | misinfo | 200 | 93.6% (93.4%–93.8%) | 0.297 (0.291–0.304) | 60.6% (59.5%–61.7%) | 0.0% (-0.2%–0.2%) |
| A | rogue | 200 | 91.2% (90.9%–91.4%) | 0.302 (0.295–0.308) | 60.8% (59.7%–61.9%) | 3.5% (3.3%–3.7%) |
| B | drought | 200 | 93.6% (93.5%–93.8%) | 0.310 (0.303–0.317) | 60.3% (59.4%–61.2%) | 15.9% (15.0%–16.9%) |
| B | misinfo | 200 | 93.7% (93.5%–93.8%) | 0.256 (0.251–0.261) | 61.7% (60.7%–62.6%) | -0.2% (-0.3%–-0.0%) |
| B | rogue | 200 | 91.7% (91.5%–91.9%) | 0.260 (0.255–0.265) | 62.0% (61.2%–62.8%) | 4.0% (3.7%–4.2%) |
| C | drought | 200 | 94.6% (94.4%–94.9%) | 0.413 (0.400–0.427) | 59.2% (58.0%–60.3%) | 14.6% (13.7%–15.6%) |
| C | misinfo | 200 | 94.4% (94.2%–94.7%) | 0.328 (0.319–0.337) | 61.3% (60.3%–62.4%) | -0.2% (-0.3%–-0.0%) |
| C | rogue | 200 | 92.0% (91.8%–92.3%) | 0.333 (0.324–0.342) | 61.3% (60.3%–62.3%) | 3.3% (3.1%–3.5%) |

## B vs A and B vs C under each single shock

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs A | drought | P1 compliance | 200 | -0.07 pts | -0.30 pts to +0.15 pts | 0.5168 |
| B vs A | drought | P2 wealth Gini | 200 | -0.057 | -0.068 to -0.045 | 0.0000 |
| B vs A | drought | P3 civic breadth | 200 | +1.06 pts | -0.40 pts to +2.52 pts | 0.1577 |
| B vs A | drought | P4 output loss | 200 | +1.52 pts | +0.27 pts to +2.77 pts | 0.0177 |
| B vs C | drought | P1 compliance | 200 | -1.00 pts | -1.28 pts to -0.71 pts | 0.0000 |
| B vs C | drought | P2 wealth Gini | 200 | -0.103 | -0.119 to -0.088 | 0.0000 |
| B vs C | drought | P3 civic breadth | 200 | +1.11 pts | -0.37 pts to +2.60 pts | 0.1436 |
| B vs C | drought | P4 output loss | 200 | +1.34 pts | -0.02 pts to +2.69 pts | 0.0528 |
| B vs A | misinfo | P1 compliance | 200 | +0.07 pts | -0.17 pts to +0.31 pts | 0.5579 |
| B vs A | misinfo | P2 wealth Gini | 200 | -0.042 | -0.050 to -0.034 | 0.0000 |
| B vs A | misinfo | P3 civic breadth | 200 | +1.06 pts | -0.31 pts to +2.43 pts | 0.1333 |
| B vs A | misinfo | P4 output loss | 200 | -0.20 pts | -0.41 pts to +0.01 pts | 0.0659 |
| B vs C | misinfo | P1 compliance | 200 | -0.78 pts | -1.07 pts to -0.49 pts | 0.0000 |
| B vs C | misinfo | P2 wealth Gini | 200 | -0.072 | -0.082 to -0.062 | 0.0000 |
| B vs C | misinfo | P3 civic breadth | 200 | +0.32 pts | -0.99 pts to +1.63 pts | 0.6401 |
| B vs C | misinfo | P4 output loss | 200 | +0.00 pts | -0.20 pts to +0.21 pts | 0.9765 |
| B vs A | rogue | P1 compliance | 200 | +0.54 pts | +0.30 pts to +0.79 pts | 0.0000 |
| B vs A | rogue | P2 wealth Gini | 200 | -0.042 | -0.050 to -0.034 | 0.0000 |
| B vs A | rogue | P3 civic breadth | 200 | +1.23 pts | -0.07 pts to +2.54 pts | 0.0647 |
| B vs A | rogue | P4 output loss | 200 | +0.47 pts | +0.14 pts to +0.79 pts | 0.0050 |
| B vs C | rogue | P1 compliance | 200 | -0.33 pts | -0.63 pts to -0.03 pts | 0.0310 |
| B vs C | rogue | P2 wealth Gini | 200 | -0.073 | -0.083 to -0.063 | 0.0000 |
| B vs C | rogue | P3 civic breadth | 200 | +0.67 pts | -0.48 pts to +1.83 pts | 0.2565 |
| B vs C | rogue | P4 output loss | 200 | +0.70 pts | +0.39 pts to +1.01 pts | 0.0000 |

## Population-size check: 40 citizens, 50 seeds

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss | S1 basket floor | S16 deaths per run | S17 exits per run |
|---|---|---|---|---|---|---|---|---|---|
| A40 | none | 50 | 93.8% (93.6%–94.0%) | 0.275 (0.267–0.284) | 66.6% (65.8%–67.4%) | 0.0% (0.0%–0.0%) | 91.9% (91.2%–92.6%) | 0.00 (0.00–0.00) | 0.32 (0.19–0.45) |
| A40 | full | 50 | 93.2% (93.0%–93.5%) | 0.340 (0.323–0.357) | 65.8% (64.8%–66.8%) | 16.0% (14.5%–17.5%) | 84.4% (83.2%–85.6%) | 0.22 (0.04–0.40) | 1.06 (0.58–1.54) |
| B40 | none | 50 | 93.9% (93.8%–94.1%) | 0.237 (0.231–0.244) | 59.5% (58.6%–60.4%) | 0.0% (0.0%–0.0%) | 93.2% (92.5%–93.9%) | 0.04 (-0.02–0.10) | 0.20 (0.09–0.31) |
| B40 | full | 50 | 93.5% (93.3%–93.8%) | 0.286 (0.278–0.295) | 58.5% (57.5%–59.5%) | 19.0% (17.1%–20.8%) | 85.1% (84.4%–85.9%) | 0.18 (0.07–0.29) | 1.10 (0.84–1.36) |
| C40 | none | 50 | 94.7% (94.2%–95.1%) | 0.315 (0.299–0.331) | 66.3% (65.5%–67.1%) | 0.0% (0.0%–0.0%) | 90.3% (89.5%–91.0%) | 0.06 (-0.01–0.13) | 0.62 (0.43–0.81) |
| C40 | full | 50 | 94.4% (94.0%–94.9%) | 0.422 (0.392–0.451) | 63.2% (61.4%–65.0%) | 16.7% (14.4%–19.0%) | 78.2% (75.2%–81.3%) | 1.08 (0.55–1.61) | 3.84 (2.42–5.26) |

## Size check contrasts (40 citizens, `full` arm)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B40 vs A40 | full | P1 compliance | 50 | +0.28 pts | -0.05 pts to +0.62 pts | 0.0927 |
| B40 vs A40 | full | P2 wealth Gini | 50 | -0.054 | -0.072 to -0.036 | 0.0000 |
| B40 vs A40 | full | P3 civic breadth | 50 | -7.29 pts | -8.56 pts to -6.02 pts | 0.0000 |
| B40 vs A40 | full | P4 output loss | 50 | +2.96 pts | +0.51 pts to +5.40 pts | 0.0187 |
| B40 vs C40 | full | P1 compliance | 50 | -0.91 pts | -1.44 pts to -0.38 pts | 0.0013 |
| B40 vs C40 | full | P2 wealth Gini | 50 | -0.136 | -0.167 to -0.105 | 0.0000 |
| B40 vs C40 | full | P3 civic breadth | 50 | -4.69 pts | -6.63 pts to -2.75 pts | 0.0000 |
| B40 vs C40 | full | P4 output loss | 50 | +2.26 pts | -0.79 pts to +5.31 pts | 0.1414 |

---

_Mechanical baseline (null mock), not findings about AI agents._
