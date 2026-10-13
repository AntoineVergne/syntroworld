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
| B | none | 200 | 93.7% (93.6%–93.9%) | 0.260 (0.254–0.265) | 65.8% (64.9%–66.8%) | 0.0% (0.0%–0.0%) |
| B | full | 200 | 91.8% (91.6%–92.0%) | 0.323 (0.316–0.331) | 64.5% (63.6%–65.4%) | 20.6% (19.7%–21.5%) |
| C | none | 200 | 94.4% (94.2%–94.7%) | 0.328 (0.319–0.337) | 61.5% (60.4%–62.6%) | 0.0% (0.0%–0.0%) |
| C | full | 200 | 92.3% (92.0%–92.5%) | 0.417 (0.404–0.430) | 59.4% (58.3%–60.5%) | 18.5% (17.6%–19.4%) |

## Economy, commons and harm

| World | Arm | n | S1 basket floor | S2 output (credits) | S3 days River ≥ K/2 | S4 founding-norm compliance | S16 deaths per run | S17 exits per run | S18 harm per 100 citizen-days |
|---|---|---|---|---|---|---|---|---|---|
| A | none | 200 | 91.8% (91.2%–92.5%) | 2,935 (2,908–2,962) | 71.2% (65.9%–76.5%) | 96.8% (96.6%–96.9%) | 0.01 (-0.00–0.03) | 0.34 (0.27–0.41) | 8.7 (8.4–8.9) |
| A | full | 200 | 79.8% (78.9%–80.6%) | 2,397 (2,369–2,425) | 50.2% (44.5%–55.9%) | 94.9% (94.7%–95.0%) | 0.10 (0.06–0.15) | 0.79 (0.67–0.90) | 13.6 (13.2–13.9) |
| B | none | 200 | 91.2% (90.6%–91.8%) | 2,758 (2,726–2,789) | 96.8% (95.0%–98.6%) | 97.0% (96.9%–97.1%) | 0.04 (0.01–0.07) | 0.32 (0.25–0.39) | 8.1 (7.8–8.3) |
| B | full | 200 | 79.6% (78.9%–80.4%) | 2,184 (2,156–2,213) | 89.5% (86.0%–92.9%) | 95.2% (95.1%–95.3%) | 0.23 (0.16–0.29) | 0.70 (0.61–0.80) | 12.8 (12.5–13.1) |
| C | none | 200 | 90.6% (89.9%–91.3%) | 2,974 (2,945–3,004) | 52.7% (47.1%–58.3%) | 96.9% (96.7%–97.0%) | 0.03 (0.00–0.05) | 0.48 (0.41–0.56) | 8.6 (8.3–8.8) |
| C | full | 200 | 76.2% (74.9%–77.6%) | 2,421 (2,389–2,454) | 35.6% (30.0%–41.1%) | 94.8% (94.6%–94.9%) | 0.23 (0.14–0.32) | 1.23 (1.05–1.40) | 13.9 (13.6–14.3) |

## Governance outcomes (`full` arm)

| World | Arm | n | S5 loser's compliance | S6 capture index | S7 influence Gini | S8 participation Gini | S10 rogue theft (credits) | S11 containment (ticks) | S12 misbelief (citizen-days) | S13 sittings decided under shock | S13 dividend days paid in full | S14 idle Treasury (credits) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | full | 200 | 68.4% (65.4%–71.3%) | -0.11 (-0.16–-0.06) | 0.175 (0.161–0.188) | 0.301 (0.293–0.309) | 17 (16–19) | 69 (65–73) | 38 (36–41) | 73.5% (70.7%–76.3%) | 41.1% (36.6%–45.7%) | 78 (62–93) |
| B | full | 200 | 73.1% (69.6%–76.6%) | -0.15 (-0.19–-0.10) | 0.131 (0.125–0.138) | 0.261 (0.253–0.269) | 17 (16–19) | 49 (45–52) | 43 (41–45) | 88.7% (87.3%–90.1%) | 0.6% (0.3%–0.9%) | 77 (76–78) |
| C | full | 200 | 71.3% (68.0%–74.6%) | +0.35 (+0.31–+0.40) | 0.289 (0.266–0.312) | 0.298 (0.289–0.306) | 18 (17–20) | 79 (75–82) | 38 (36–41) | 41.7% (38.8%–44.7%) | 54.2% (48.9%–59.6%) | 174 (140–208) |

## Primary contrasts (`full` arm, 8 tests, Holm)

Paired by seed. Sign-flip test with 100,000 random flips; Holm across the 8 tests; verdicts per 06 §7.2.

| Contrast | Outcome | n | Estimate | 95% CI | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| B vs A | P1 compliance | 200 | +0.51 pts | +0.27 pts to +0.75 pts | 0.00003 | 0.00012 | better |
| B vs A | P2 wealth Gini | 200 | -0.047 | -0.058 to -0.036 | 0.00001 | 0.00008 | better |
| B vs A | P3 civic breadth | 200 | +4.61 pts | +3.22 pts to +5.99 pts | 0.00001 | 0.00008 | better |
| B vs A | P4 output loss | 200 | +2.36 pts | +1.10 pts to +3.61 pts | 0.00043 | 0.00129 | worse |
| B vs C | P1 compliance | 200 | -0.48 pts | -0.79 pts to -0.17 pts | 0.00292 | 0.00508 | worse |
| B vs C | P2 wealth Gini | 200 | -0.094 | -0.109 to -0.078 | 0.00001 | 0.00008 | better |
| B vs C | P3 civic breadth | 200 | +5.11 pts | +3.69 pts to +6.52 pts | 0.00001 | 0.00008 | better |
| B vs C | P4 output loss | 200 | +2.11 pts | +0.76 pts to +3.46 pts | 0.00254 | 0.00508 | worse |

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
| B vs A | none | P1 compliance | 200 | +0.15 pts | -0.07 pts to +0.37 pts | 0.1790 |
| B vs A | none | P2 wealth Gini | 200 | -0.038 | -0.045 to -0.030 | 0.0000 |
| B vs A | none | P3 civic breadth | 200 | +5.14 pts | +3.67 pts to +6.60 pts | 0.0000 |
| B vs A | none | P4 output loss | 200 | +0.00 pts | +0.00 pts to +0.00 pts | 1.0000 |
| B vs C | none | P1 compliance | 200 | -0.70 pts | -0.96 pts to -0.44 pts | 0.0000 |
| B vs C | none | P2 wealth Gini | 200 | -0.068 | -0.078 to -0.058 | 0.0000 |
| B vs C | none | P3 civic breadth | 200 | +4.32 pts | +2.90 pts to +5.74 pts | 0.0000 |
| B vs C | none | P4 output loss | 200 | +0.00 pts | +0.00 pts to +0.00 pts | 1.0000 |

## Ablations: B minus one mechanism (`full` arm)

A positive estimate means B scores higher than the ablation, i.e. the mechanism raises that outcome.

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs B-nolot | full | P1 compliance | 200 | -0.08 pts | -0.31 pts to +0.14 pts | 0.4544 |
| B vs B-nolot | full | P2 wealth Gini | 200 | +0.021 | +0.011 to +0.030 | 0.0000 |
| B vs B-nolot | full | P3 civic breadth | 200 | -7.96 pts | -9.20 pts to -6.72 pts | 0.0000 |
| B vs B-nolot | full | P4 output loss | 200 | +1.37 pts | +0.14 pts to +2.60 pts | 0.0287 |
| B vs B-noadv | full | P1 compliance | 200 | -0.01 pts | -0.13 pts to +0.12 pts | 0.9156 |
| B vs B-noadv | full | P2 wealth Gini | 200 | -0.002 | -0.006 to +0.002 | 0.4123 |
| B vs B-noadv | full | P3 civic breadth | 200 | +0.05 pts | -0.55 pts to +0.66 pts | 0.8817 |
| B vs B-noadv | full | P4 output loss | 200 | -0.63 pts | -1.22 pts to -0.05 pts | 0.0328 |
| B vs B-nodiv | full | P1 compliance | 200 | +0.05 pts | -0.18 pts to +0.28 pts | 0.6530 |
| B vs B-nodiv | full | P2 wealth Gini | 200 | -0.024 | -0.032 to -0.016 | 0.0000 |
| B vs B-nodiv | full | P3 civic breadth | 200 | +0.35 pts | -0.89 pts to +1.59 pts | 0.5890 |
| B vs B-nodiv | full | P4 output loss | 200 | -0.16 pts | -1.24 pts to +0.92 pts | 0.7653 |
| B vs B-nopay | full | P1 compliance | 200 | -0.02 pts | -0.17 pts to +0.12 pts | 0.7401 |
| B vs B-nopay | full | P2 wealth Gini | 200 | -0.014 | -0.019 to -0.009 | 0.0000 |
| B vs B-nopay | full | P3 civic breadth | 200 | -0.62 pts | -1.54 pts to +0.30 pts | 0.1915 |
| B vs B-nopay | full | P4 output loss | 200 | -0.22 pts | -1.12 pts to +0.69 pts | 0.6362 |

## Ablation cells

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| B-nolot | none | 200 | 93.6% (93.4%–93.7%) | 0.248 (0.244–0.253) | 73.4% (72.4%–74.3%) | 0.0% (0.0%–0.0%) |
| B-nolot | full | 200 | 91.9% (91.7%–92.0%) | 0.303 (0.297–0.309) | 72.5% (71.6%–73.4%) | 19.2% (18.4%–20.1%) |
| B-noadv | none | 200 | 93.7% (93.6%–93.9%) | 0.260 (0.254–0.265) | 65.1% (64.1%–66.0%) | 0.0% (0.0%–0.0%) |
| B-noadv | full | 200 | 91.8% (91.6%–92.0%) | 0.325 (0.317–0.332) | 64.5% (63.5%–65.4%) | 21.2% (20.3%–22.1%) |
| B-nodiv | none | 200 | 93.7% (93.6%–93.9%) | 0.273 (0.268–0.279) | 65.2% (64.2%–66.2%) | 0.0% (0.0%–0.0%) |
| B-nodiv | full | 200 | 91.7% (91.5%–91.9%) | 0.347 (0.340–0.355) | 64.2% (63.2%–65.1%) | 20.8% (19.9%–21.7%) |
| B-nopay | none | 200 | 93.7% (93.5%–93.8%) | 0.268 (0.263–0.273) | 66.2% (65.3%–67.1%) | 0.0% (0.0%–0.0%) |
| B-nopay | full | 200 | 91.8% (91.6%–92.0%) | 0.337 (0.330–0.345) | 65.1% (64.2%–66.0%) | 20.8% (19.9%–21.8%) |

## Single-shock arms

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| A | drought | 200 | 93.7% (93.5%–93.9%) | 0.367 (0.357–0.376) | 59.2% (58.1%–60.4%) | 14.4% (13.6%–15.2%) |
| A | misinfo | 200 | 93.6% (93.4%–93.8%) | 0.297 (0.291–0.304) | 60.6% (59.5%–61.7%) | 0.0% (-0.2%–0.2%) |
| A | rogue | 200 | 91.2% (90.9%–91.4%) | 0.302 (0.295–0.308) | 60.8% (59.7%–61.9%) | 3.5% (3.3%–3.7%) |
| B | drought | 200 | 93.8% (93.6%–93.9%) | 0.319 (0.311–0.327) | 63.7% (62.8%–64.7%) | 16.0% (15.0%–17.0%) |
| B | misinfo | 200 | 93.7% (93.5%–93.8%) | 0.260 (0.254–0.265) | 65.7% (64.8%–66.6%) | -0.2% (-0.3%–-0.1%) |
| B | rogue | 200 | 91.8% (91.6%–92.0%) | 0.264 (0.259–0.270) | 66.6% (65.6%–67.5%) | 4.4% (4.1%–4.7%) |
| C | drought | 200 | 94.6% (94.4%–94.9%) | 0.413 (0.400–0.427) | 59.2% (58.0%–60.3%) | 14.6% (13.7%–15.6%) |
| C | misinfo | 200 | 94.4% (94.2%–94.7%) | 0.328 (0.319–0.337) | 61.3% (60.3%–62.4%) | -0.2% (-0.3%–-0.0%) |
| C | rogue | 200 | 92.0% (91.8%–92.3%) | 0.333 (0.324–0.342) | 61.3% (60.3%–62.3%) | 3.3% (3.1%–3.5%) |

## B vs A and B vs C under each single shock

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs A | drought | P1 compliance | 200 | +0.06 pts | -0.15 pts to +0.26 pts | 0.5885 |
| B vs A | drought | P2 wealth Gini | 200 | -0.048 | -0.059 to -0.037 | 0.0000 |
| B vs A | drought | P3 civic breadth | 200 | +4.52 pts | +3.04 pts to +5.99 pts | 0.0000 |
| B vs A | drought | P4 output loss | 200 | +1.59 pts | +0.25 pts to +2.93 pts | 0.0194 |
| B vs C | drought | P1 compliance | 200 | -0.87 pts | -1.15 pts to -0.59 pts | 0.0000 |
| B vs C | drought | P2 wealth Gini | 200 | -0.094 | -0.109 to -0.079 | 0.0000 |
| B vs C | drought | P3 civic breadth | 200 | +4.57 pts | +3.06 pts to +6.07 pts | 0.0000 |
| B vs C | drought | P4 output loss | 200 | +1.41 pts | -0.04 pts to +2.86 pts | 0.0570 |
| B vs A | misinfo | P1 compliance | 200 | +0.08 pts | -0.14 pts to +0.31 pts | 0.4659 |
| B vs A | misinfo | P2 wealth Gini | 200 | -0.038 | -0.046 to -0.030 | 0.0000 |
| B vs A | misinfo | P3 civic breadth | 200 | +5.11 pts | +3.64 pts to +6.57 pts | 0.0000 |
| B vs A | misinfo | P4 output loss | 200 | -0.19 pts | -0.40 pts to +0.02 pts | 0.0826 |
| B vs C | misinfo | P1 compliance | 200 | -0.77 pts | -1.04 pts to -0.50 pts | 0.0000 |
| B vs C | misinfo | P2 wealth Gini | 200 | -0.068 | -0.078 to -0.058 | 0.0000 |
| B vs C | misinfo | P3 civic breadth | 200 | +4.36 pts | +2.94 pts to +5.79 pts | 0.0000 |
| B vs C | misinfo | P4 output loss | 200 | +0.02 pts | -0.16 pts to +0.19 pts | 0.8510 |
| B vs A | rogue | P1 compliance | 200 | +0.64 pts | +0.39 pts to +0.88 pts | 0.0000 |
| B vs A | rogue | P2 wealth Gini | 200 | -0.037 | -0.045 to -0.030 | 0.0000 |
| B vs A | rogue | P3 civic breadth | 200 | +5.80 pts | +4.40 pts to +7.19 pts | 0.0000 |
| B vs A | rogue | P4 output loss | 200 | +0.90 pts | +0.54 pts to +1.25 pts | 0.0000 |
| B vs C | rogue | P1 compliance | 200 | -0.23 pts | -0.51 pts to +0.05 pts | 0.1017 |
| B vs C | rogue | P2 wealth Gini | 200 | -0.068 | -0.079 to -0.058 | 0.0000 |
| B vs C | rogue | P3 civic breadth | 200 | +5.23 pts | +3.88 pts to +6.59 pts | 0.0000 |
| B vs C | rogue | P4 output loss | 200 | +1.13 pts | +0.80 pts to +1.46 pts | 0.0000 |

## Population-size check: 40 citizens, 50 seeds

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss | S1 basket floor | S16 deaths per run | S17 exits per run |
|---|---|---|---|---|---|---|---|---|---|
| A40 | none | 50 | 93.8% (93.6%–94.0%) | 0.275 (0.267–0.284) | 66.6% (65.8%–67.4%) | 0.0% (0.0%–0.0%) | 91.9% (91.2%–92.6%) | 0.00 (0.00–0.00) | 0.32 (0.19–0.45) |
| A40 | full | 50 | 93.2% (93.0%–93.5%) | 0.340 (0.323–0.357) | 65.8% (64.8%–66.8%) | 16.0% (14.5%–17.5%) | 84.4% (83.2%–85.6%) | 0.22 (0.04–0.40) | 1.06 (0.58–1.54) |
| B40 | none | 50 | 94.4% (94.2%–94.6%) | 0.287 (0.280–0.293) | 87.4% (86.7%–88.1%) | 0.0% (0.0%–0.0%) | 91.5% (90.9%–92.1%) | 0.12 (0.03–0.21) | 0.64 (0.46–0.82) |
| B40 | full | 50 | 93.6% (93.4%–93.8%) | 0.383 (0.376–0.391) | 83.8% (82.9%–84.6%) | 22.1% (20.0%–24.2%) | 79.0% (77.8%–80.2%) | 1.44 (1.08–1.80) | 3.36 (2.83–3.89) |
| C40 | none | 50 | 94.7% (94.2%–95.1%) | 0.315 (0.299–0.331) | 66.3% (65.5%–67.1%) | 0.0% (0.0%–0.0%) | 90.3% (89.5%–91.0%) | 0.06 (-0.01–0.13) | 0.62 (0.43–0.81) |
| C40 | full | 50 | 94.4% (94.0%–94.9%) | 0.422 (0.392–0.451) | 63.2% (61.4%–65.0%) | 16.7% (14.4%–19.0%) | 78.2% (75.2%–81.3%) | 1.08 (0.55–1.61) | 3.84 (2.42–5.26) |

## Size check contrasts (40 citizens, `full` arm)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B40 vs A40 | full | P1 compliance | 50 | +0.37 pts | +0.07 pts to +0.68 pts | 0.0178 |
| B40 vs A40 | full | P2 wealth Gini | 50 | +0.043 | +0.025 to +0.061 | 0.0000 |
| B40 vs A40 | full | P3 civic breadth | 50 | +17.98 pts | +16.58 pts to +19.37 pts | 0.0000 |
| B40 vs A40 | full | P4 output loss | 50 | +6.13 pts | +3.54 pts to +8.72 pts | 0.0000 |
| B40 vs C40 | full | P1 compliance | 50 | -0.81 pts | -1.32 pts to -0.30 pts | 0.0026 |
| B40 vs C40 | full | P2 wealth Gini | 50 | -0.039 | -0.067 to -0.010 | 0.0100 |
| B40 vs C40 | full | P3 civic breadth | 50 | +20.57 pts | +18.71 pts to +22.44 pts | 0.0000 |
| B40 vs C40 | full | P4 output loss | 50 | +5.43 pts | +2.25 pts to +8.62 pts | 0.0013 |

---

_Mechanical baseline (null mock), not findings about AI agents._
