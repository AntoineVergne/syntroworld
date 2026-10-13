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
| A | full | 200 | 92.1% (91.9%–92.3%) | 0.302 (0.296–0.308) | 61.1% (59.9%–62.3%) | 0.1% (-0.5%–0.7%) |
| B | none | 200 | 93.2% (93.1%–93.4%) | 0.241 (0.237–0.246) | 69.1% (68.2%–70.0%) | 0.0% (0.0%–0.0%) |
| B | full | 200 | 91.8% (91.6%–92.0%) | 0.244 (0.239–0.248) | 70.0% (69.2%–70.9%) | 0.2% (-0.5%–0.9%) |
| C | none | 200 | 94.4% (94.2%–94.7%) | 0.328 (0.319–0.337) | 61.5% (60.4%–62.6%) | 0.0% (0.0%–0.0%) |
| C | full | 200 | 93.2% (92.9%–93.5%) | 0.331 (0.322–0.339) | 61.6% (60.5%–62.7%) | 0.7% (0.1%–1.3%) |

## Economy, commons and harm

| World | Arm | n | S1 basket floor | S2 output (credits) | S3 days River ≥ K/2 | S4 founding-norm compliance | S16 deaths per run | S17 exits per run | S18 harm per 100 citizen-days |
|---|---|---|---|---|---|---|---|---|---|
| A | none | 200 | 91.8% (91.2%–92.5%) | 2,935 (2,908–2,962) | 71.2% (65.9%–76.5%) | 96.8% (96.6%–96.9%) | 0.01 (-0.00–0.03) | 0.34 (0.27–0.41) | 8.7 (8.4–8.9) |
| A | full | 200 | 91.2% (90.5%–91.9%) | 2,931 (2,902–2,959) | 57.1% (51.3%–62.8%) | 96.2% (96.1%–96.3%) | 0.01 (-0.00–0.02) | 0.36 (0.30–0.43) | 10.4 (10.1–10.7) |
| B | none | 200 | 94.0% (93.7%–94.4%) | 2,998 (2,969–3,027) | 96.2% (94.3%–98.2%) | 96.7% (96.6%–96.8%) | 0.00 (0.00–0.00) | 0.09 (0.05–0.13) | 8.8 (8.6–9.1) |
| B | full | 200 | 93.5% (93.0%–93.9%) | 2,988 (2,960–3,017) | 87.2% (83.8%–90.7%) | 96.1% (96.0%–96.3%) | 0.00 (0.00–0.00) | 0.07 (0.04–0.11) | 10.7 (10.4–11.0) |
| C | none | 200 | 90.6% (89.9%–91.3%) | 2,974 (2,945–3,004) | 52.7% (47.1%–58.3%) | 96.9% (96.7%–97.0%) | 0.03 (0.00–0.05) | 0.48 (0.41–0.56) | 8.6 (8.3–8.8) |
| C | full | 200 | 89.8% (89.1%–90.5%) | 2,951 (2,920–2,981) | 41.6% (35.8%–47.5%) | 96.3% (96.2%–96.5%) | 0.02 (0.00–0.04) | 0.50 (0.43–0.57) | 10.2 (9.9–10.5) |

## Governance outcomes (`full` arm)

| World | Arm | n | S5 loser's compliance | S6 capture index | S7 influence Gini | S8 participation Gini | S10 rogue theft (credits) | S11 containment (ticks) | S12 misbelief (citizen-days) | S13 sittings decided under shock | S13 dividend days paid in full | S14 idle Treasury (credits) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | full | 200 | 69.7% (66.9%–72.5%) | -0.05 (-0.10–+0.00) | 0.167 (0.158–0.177) | 0.291 (0.283–0.299) | 17 (15–18) | 67 (62–72) | 41 (39–44) | 70.6% (67.5%–73.7%) | 32.1% (27.7%–36.6%) | 59 (50–68) |
| B | full | 200 | 70.5% (67.0%–74.1%) | -0.08 (-0.12–-0.03) | 0.121 (0.115–0.126) | 0.237 (0.231–0.243) | 18 (16–19) | 47 (44–50) | 45 (42–47) | 94.0% (92.9%–95.2%) | 0.0% (0.0%–0.0%) | 80 (80–80) |
| C | full | 200 | 71.6% (68.5%–74.6%) | +0.28 (+0.23–+0.32) | 0.266 (0.246–0.287) | 0.295 (0.287–0.303) | 16 (15–18) | 77 (73–81) | 42 (39–44) | 44.3% (41.0%–47.5%) | 44.5% (39.1%–49.8%) | 102 (81–123) |

## Primary contrasts (`full` arm, 8 tests, Holm)

Paired by seed. Sign-flip test with 100,000 random flips; Holm across the 8 tests; verdicts per 06 §7.2.

| Contrast | Outcome | n | Estimate | 95% CI | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| B vs A | P1 compliance | 200 | -0.28 pts | -0.53 pts to -0.02 pts | 0.03300 | 0.09900 | no meaningful difference |
| B vs A | P2 wealth Gini | 200 | -0.058 | -0.065 to -0.051 | 0.00001 | 0.00008 | better |
| B vs A | P3 civic breadth | 200 | +8.95 pts | +7.47 pts to +10.42 pts | 0.00001 | 0.00008 | better |
| B vs A | P4 output loss | 200 | +0.08 pts | -0.80 pts to +0.97 pts | 0.85146 | 0.85146 | no meaningful difference |
| B vs C | P1 compliance | 200 | -1.37 pts | -1.70 pts to -1.05 pts | 0.00001 | 0.00008 | worse |
| B vs C | P2 wealth Gini | 200 | -0.087 | -0.096 to -0.078 | 0.00001 | 0.00008 | better |
| B vs C | P3 civic breadth | 200 | +8.44 pts | +7.06 pts to +9.82 pts | 0.00001 | 0.00008 | better |
| B vs C | P4 output loss | 200 | -0.52 pts | -1.38 pts to +0.35 pts | 0.23956 | 0.47912 | no meaningful difference |

Better is: higher P1 and P3, lower P2 and P4. SESOI: P1 5 points, P2 0.05, P3 10 points, P4 5 points.

## A vs C (secondary)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| A vs C | full | P1 compliance | 200 | -1.10 pts | -1.34 pts to -0.86 pts | 0.0000 |
| A vs C | full | P2 wealth Gini | 200 | -0.029 | -0.035 to -0.022 | 0.0000 |
| A vs C | full | P3 civic breadth | 200 | -0.51 pts | -1.57 pts to +0.55 pts | 0.3560 |
| A vs C | full | P4 output loss | 200 | -0.60 pts | -1.34 pts to +0.14 pts | 0.1113 |

## B vs A and B vs C without shocks (`none` arm)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs A | none | P1 compliance | 200 | -0.32 pts | -0.55 pts to -0.09 pts | 0.0073 |
| B vs A | none | P2 wealth Gini | 200 | -0.056 | -0.063 to -0.049 | 0.0000 |
| B vs A | none | P3 civic breadth | 200 | +8.40 pts | +7.02 pts to +9.79 pts | 0.0000 |
| B vs A | none | P4 output loss | 200 | +0.00 pts | +0.00 pts to +0.00 pts | 1.0000 |
| B vs C | none | P1 compliance | 200 | -1.17 pts | -1.45 pts to -0.88 pts | 0.0000 |
| B vs C | none | P2 wealth Gini | 200 | -0.087 | -0.096 to -0.077 | 0.0000 |
| B vs C | none | P3 civic breadth | 200 | +7.58 pts | +6.18 pts to +8.99 pts | 0.0000 |
| B vs C | none | P4 output loss | 200 | +0.00 pts | +0.00 pts to +0.00 pts | 1.0000 |

## Ablations: B minus one mechanism (`full` arm)

A positive estimate means B scores higher than the ablation, i.e. the mechanism raises that outcome.

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs B-nolot | full | P1 compliance | 200 | -0.37 pts | -0.60 pts to -0.14 pts | 0.0018 |
| B vs B-nolot | full | P2 wealth Gini | 200 | -0.001 | -0.007 to +0.005 | 0.7074 |
| B vs B-nolot | full | P3 civic breadth | 200 | -0.03 pts | -1.30 pts to +1.24 pts | 0.9723 |
| B vs B-nolot | full | P4 output loss | 200 | +0.12 pts | -0.79 pts to +1.04 pts | 0.7909 |
| B vs B-noadv | full | P1 compliance | 200 | +0.03 pts | -0.07 pts to +0.12 pts | 0.6011 |
| B vs B-noadv | full | P2 wealth Gini | 200 | -0.002 | -0.004 to -0.000 | 0.0248 |
| B vs B-noadv | full | P3 civic breadth | 200 | +0.31 pts | -0.19 pts to +0.81 pts | 0.2378 |
| B vs B-noadv | full | P4 output loss | 200 | -0.01 pts | -0.43 pts to +0.42 pts | 0.9720 |
| B vs B-nodiv | full | P1 compliance | 200 | +0.01 pts | -0.20 pts to +0.22 pts | 0.9136 |
| B vs B-nodiv | full | P2 wealth Gini | 200 | -0.014 | -0.019 to -0.010 | 0.0000 |
| B vs B-nodiv | full | P3 civic breadth | 200 | +0.45 pts | -0.65 pts to +1.55 pts | 0.4300 |
| B vs B-nodiv | full | P4 output loss | 200 | -0.59 pts | -1.48 pts to +0.31 pts | 0.1957 |
| B vs B-nopay | full | P1 compliance | 200 | +0.09 pts | -0.07 pts to +0.25 pts | 0.2704 |
| B vs B-nopay | full | P2 wealth Gini | 200 | -0.010 | -0.014 to -0.006 | 0.0000 |
| B vs B-nopay | full | P3 civic breadth | 200 | +0.53 pts | -0.38 pts to +1.44 pts | 0.2582 |
| B vs B-nopay | full | P4 output loss | 200 | +0.24 pts | -0.45 pts to +0.93 pts | 0.4985 |

## Ablation cells

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| B-nolot | none | 200 | 93.7% (93.6%–93.9%) | 0.242 (0.238–0.246) | 69.6% (68.6%–70.5%) | 0.0% (0.0%–0.0%) |
| B-nolot | full | 200 | 92.2% (92.0%–92.3%) | 0.245 (0.240–0.249) | 70.1% (69.2%–70.9%) | 0.1% (-0.6%–0.7%) |
| B-noadv | none | 200 | 93.2% (93.1%–93.4%) | 0.243 (0.239–0.247) | 69.5% (68.6%–70.4%) | 0.0% (0.0%–0.0%) |
| B-noadv | full | 200 | 91.8% (91.6%–92.0%) | 0.246 (0.241–0.250) | 69.7% (68.8%–70.6%) | 0.2% (-0.4%–0.8%) |
| B-nodiv | none | 200 | 93.4% (93.2%–93.5%) | 0.256 (0.252–0.260) | 69.0% (68.1%–69.9%) | 0.0% (0.0%–0.0%) |
| B-nodiv | full | 200 | 91.8% (91.6%–92.0%) | 0.258 (0.253–0.262) | 69.6% (68.7%–70.5%) | 0.8% (0.2%–1.4%) |
| B-nopay | none | 200 | 93.2% (93.1%–93.4%) | 0.252 (0.248–0.257) | 69.6% (68.7%–70.5%) | 0.0% (0.0%–0.0%) |
| B-nopay | full | 200 | 91.7% (91.5%–91.9%) | 0.254 (0.249–0.258) | 69.5% (68.6%–70.4%) | -0.0% (-0.6%–0.5%) |

## Single-shock arms

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss |
|---|---|---|---|---|---|---|
| A | drought | 200 | 93.6% (93.4%–93.8%) | 0.304 (0.297–0.310) | 60.8% (59.6%–62.0%) | 1.7% (1.2%–2.2%) |
| A | misinfo | 200 | 93.6% (93.4%–93.8%) | 0.297 (0.291–0.304) | 60.6% (59.5%–61.7%) | 0.0% (-0.2%–0.2%) |
| A | rogue | 200 | 92.0% (91.8%–92.2%) | 0.296 (0.290–0.302) | 60.7% (59.5%–61.9%) | -1.4% (-1.7%–-1.2%) |
| B | drought | 200 | 93.3% (93.2%–93.5%) | 0.245 (0.241–0.249) | 69.1% (68.2%–70.0%) | 1.6% (1.0%–2.2%) |
| B | misinfo | 200 | 93.2% (93.1%–93.4%) | 0.241 (0.237–0.245) | 69.2% (68.2%–70.2%) | -0.1% (-0.3%–0.1%) |
| B | rogue | 200 | 91.8% (91.6%–91.9%) | 0.241 (0.237–0.245) | 69.8% (68.9%–70.8%) | -1.3% (-1.6%–-1.1%) |
| C | drought | 200 | 94.5% (94.2%–94.7%) | 0.332 (0.324–0.341) | 61.6% (60.4%–62.7%) | 1.9% (1.3%–2.5%) |
| C | misinfo | 200 | 94.4% (94.2%–94.7%) | 0.328 (0.319–0.337) | 61.3% (60.3%–62.4%) | -0.2% (-0.3%–-0.0%) |
| C | rogue | 200 | 93.1% (92.8%–93.4%) | 0.327 (0.318–0.336) | 61.4% (60.3%–62.4%) | -1.2% (-1.4%–-1.0%) |

## B vs A and B vs C under each single shock

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B vs A | drought | P1 compliance | 200 | -0.31 pts | -0.53 pts to -0.09 pts | 0.0055 |
| B vs A | drought | P2 wealth Gini | 200 | -0.059 | -0.066 to -0.051 | 0.0000 |
| B vs A | drought | P3 civic breadth | 200 | +8.29 pts | +6.75 pts to +9.83 pts | 0.0000 |
| B vs A | drought | P4 output loss | 200 | -0.10 pts | -0.91 pts to +0.71 pts | 0.8097 |
| B vs C | drought | P1 compliance | 200 | -1.16 pts | -1.45 pts to -0.88 pts | 0.0000 |
| B vs C | drought | P2 wealth Gini | 200 | -0.087 | -0.097 to -0.078 | 0.0000 |
| B vs C | drought | P3 civic breadth | 200 | +7.52 pts | +6.11 pts to +8.93 pts | 0.0000 |
| B vs C | drought | P4 output loss | 200 | -0.26 pts | -1.14 pts to +0.63 pts | 0.5692 |
| B vs A | misinfo | P1 compliance | 200 | -0.36 pts | -0.58 pts to -0.14 pts | 0.0014 |
| B vs A | misinfo | P2 wealth Gini | 200 | -0.056 | -0.063 to -0.049 | 0.0000 |
| B vs A | misinfo | P3 civic breadth | 200 | +8.61 pts | +7.21 pts to +10.00 pts | 0.0000 |
| B vs A | misinfo | P4 output loss | 200 | -0.16 pts | -0.44 pts to +0.12 pts | 0.2716 |
| B vs C | misinfo | P1 compliance | 200 | -1.21 pts | -1.50 pts to -0.93 pts | 0.0000 |
| B vs C | misinfo | P2 wealth Gini | 200 | -0.087 | -0.096 to -0.077 | 0.0000 |
| B vs C | misinfo | P3 civic breadth | 200 | +7.86 pts | +6.43 pts to +9.29 pts | 0.0000 |
| B vs C | misinfo | P4 output loss | 200 | +0.04 pts | -0.18 pts to +0.27 pts | 0.6986 |
| B vs A | rogue | P1 compliance | 200 | -0.25 pts | -0.51 pts to +0.00 pts | 0.0523 |
| B vs A | rogue | P2 wealth Gini | 200 | -0.056 | -0.063 to -0.049 | 0.0000 |
| B vs A | rogue | P3 civic breadth | 200 | +9.14 pts | +7.70 pts to +10.59 pts | 0.0000 |
| B vs A | rogue | P4 output loss | 200 | +0.09 pts | -0.19 pts to +0.38 pts | 0.5243 |
| B vs C | rogue | P1 compliance | 200 | -1.31 pts | -1.65 pts to -0.98 pts | 0.0000 |
| B vs C | rogue | P2 wealth Gini | 200 | -0.087 | -0.096 to -0.077 | 0.0000 |
| B vs C | rogue | P3 civic breadth | 200 | +8.48 pts | +7.08 pts to +9.89 pts | 0.0000 |
| B vs C | rogue | P4 output loss | 200 | -0.18 pts | -0.40 pts to +0.04 pts | 0.1060 |

## Population-size check: 40 citizens, 50 seeds

| World | Arm | n | P1 compliance | P2 wealth Gini | P3 civic breadth | P4 output loss | S1 basket floor | S16 deaths per run | S17 exits per run |
|---|---|---|---|---|---|---|---|---|---|
| A40 | none | 50 | 93.8% (93.6%–94.0%) | 0.275 (0.267–0.284) | 66.6% (65.8%–67.4%) | 0.0% (0.0%–0.0%) | 91.9% (91.2%–92.6%) | 0.00 (0.00–0.00) | 0.32 (0.19–0.45) |
| A40 | full | 50 | 93.4% (93.1%–93.7%) | 0.282 (0.273–0.292) | 66.8% (66.0%–67.6%) | 0.5% (-0.5%–1.5%) | 92.1% (91.3%–92.9%) | 0.00 (0.00–0.00) | 0.34 (0.20–0.48) |
| B40 | none | 50 | 93.4% (93.2%–93.6%) | 0.223 (0.219–0.228) | 51.1% (50.2%–52.1%) | 0.0% (0.0%–0.0%) | 94.1% (93.3%–94.8%) | 0.02 (-0.02–0.06) | 0.16 (0.05–0.27) |
| B40 | full | 50 | 93.1% (92.9%–93.3%) | 0.231 (0.226–0.236) | 52.0% (51.1%–53.0%) | 1.0% (-0.8%–2.7%) | 94.1% (93.6%–94.6%) | 0.00 (0.00–0.00) | 0.18 (0.07–0.29) |
| C40 | none | 50 | 94.7% (94.2%–95.1%) | 0.315 (0.299–0.331) | 66.3% (65.5%–67.1%) | 0.0% (0.0%–0.0%) | 90.3% (89.5%–91.0%) | 0.06 (-0.01–0.13) | 0.62 (0.43–0.81) |
| C40 | full | 50 | 94.4% (93.9%–94.8%) | 0.330 (0.311–0.348) | 66.8% (65.8%–67.7%) | 1.3% (0.7%–1.9%) | 90.6% (89.9%–91.4%) | 0.08 (-0.02–0.18) | 0.68 (0.42–0.94) |

## Size check contrasts (40 citizens, `full` arm)

| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |
|---|---|---|---|---|---|---|
| B40 vs A40 | full | P1 compliance | 50 | -0.27 pts | -0.61 pts to +0.08 pts | 0.1229 |
| B40 vs A40 | full | P2 wealth Gini | 50 | -0.051 | -0.061 to -0.042 | 0.0000 |
| B40 vs A40 | full | P3 civic breadth | 50 | -14.76 pts | -16.02 pts to -13.50 pts | 0.0000 |
| B40 vs A40 | full | P4 output loss | 50 | +0.51 pts | -1.57 pts to +2.58 pts | 0.6267 |
| B40 vs C40 | full | P1 compliance | 50 | -1.25 pts | -1.77 pts to -0.72 pts | 0.0000 |
| B40 vs C40 | full | P2 wealth Gini | 50 | -0.099 | -0.117 to -0.081 | 0.0000 |
| B40 vs C40 | full | P3 civic breadth | 50 | -14.71 pts | -16.01 pts to -13.40 pts | 0.0000 |
| B40 vs C40 | full | P4 output loss | 50 | -0.29 pts | -2.17 pts to +1.59 pts | 0.7530 |

---

_Mechanical baseline (null mock), not findings about AI agents._
