# Pilot (step L1): seeds per world from σ_d (06 §7.4)

`n = max(12, ceil(12.8 × (σ_d / SESOI)²))`. Each σ_d rests on the listed number of paired differences; with the L1 pilot's 2 seeds per world that is 1 degree of freedom, so treat those values as rough.

| Contrast | Outcome | Pairs | σ_d | SESOI | Seeds per world |
|---|---|---|---|---|---|
| B vs A | P1 | 20 | 0.0159 | 0.05 | 12 |
| B vs A | P2 | 20 | 0.0797 | 0.05 | 33 |
| B vs A | P3 | 20 | 0.0700 | 0.1 | 12 |
| B vs A | P4 | 20 | 0.0821 | 0.05 | 35 |
| B vs C | P1 | 20 | 0.0184 | 0.05 | 12 |
| B vs C | P2 | 20 | 0.1075 | 0.05 | 60 |
| B vs C | P3 | 20 | 0.1015 | 0.1 | 14 |
| B vs C | P4 | 20 | 0.0984 | 0.05 | 50 |

Largest: **60 seeds per world**. Decision 8: if the budget cannot reach it, raise that outcome's SESOI in writing before running, or report it as descriptive.
