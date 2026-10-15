# What a model citizen reads (prompt review pack)

Exactly what the model brain sends to a model, captured from a mock run (seed 1, `full`
arm) from day 7 on, for one citizen per call type. No model was called.

    python -m synw.analysis.prompts --out results/l0-prompts

Each file has two parts:

- **SYSTEM**: the same for that citizen on every request, until the rules in force or
  the rogue overlay change it. It holds the persona (04 §3), the shared preamble, the
  world's texts (02 §9), the world guide, the action list, the reply formats and the
  effect formats. Providers can cache it, so its tokens cost much less after the first
  request.
- **USER**: the call name, the observation as JSON, and the call's details (the
  proposal, the draw, the deliberation).

The world guide is word for word the same in every world: it describes the town, not
its institutions. What differs between worlds is only the texts section (02 §9): A and
C read their bootstrap block; B reads the Compact and its blocks; A+text reads A's
block plus the Compact as "a proposal some citizens once wrote".

`sizes.csv` gives a size estimate per request (4 characters per token). In A and C no
citizen is drawn and nobody deliberates, so those calls do not occur there.

**What to check before L0:** does the persona read right; is anything a citizen needs
missing from the world guide or the observation; does anything hint at which world is
"better" outside the texts section.
