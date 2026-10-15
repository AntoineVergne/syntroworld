# Persona check (04 §1 rule 3): reference from the null mock

04 §1 rule 3 says the L1 pilot checks that model behaviour and the persona numbers
"roughly agree". A model reads only the persona text; the mock reads only the numbers.
`synw.analysis.persona_check` ranks the citizens by each persona number and by what they
did (days 1 to 18 of the `full` arm, before the rogue overlay), and reports Spearman's ρ.

The null mock *is* the numbers, so its column is the ceiling: how much of each trait the
measure can recover. A model whose behaviour follows its persona text should show the
same signs. Reference on worlds A, B and C, seeds 1 to 10:

| Trait | Null mock: mean ρ (share > 0) | Model: mean ρ (share > 0) |
|---|---|---|
| work_drive | +0.68 (100% of 30) | no model runs |
| honesty | +0.65 (100% of 30) | no model runs |
| civic | +0.76 (100% of 30) | no model runs |
| credulity | +0.30 (87% of 30) | no model runs |
| greed | +0.72 (100% of 30) | no model runs |

- **Credulity** is the weakest measure (ρ +0.30): only the misinformation shock plants
  false claims, so few citizens get the chance to believe one.
- **Greed** is measured as the share of production time spent fishing, which also
  reflects each citizen's niche (Kofi, Yuki and Viktor work the River).

After L1: `python -m synw.analysis.persona_check --campaign runs/l1 --mock-seeds 1-10`
fills the model column.
