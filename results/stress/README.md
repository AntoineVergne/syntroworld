# Stress test: the model-brain path under bad replies (no model called)

`synw/brains/chaos.py` stands in for a model. A share of its replies (30% here) is junk:
free text, truncated JSON, unknown actions, wrong types, non-integral and huge numbers,
out-of-range values. The rest are the mock brain's own decisions sent as JSON, so
citizens live through the season and every late-season path runs (sittings, draws,
deliberation, the rogue, all three shocks).

Reproduce: `python results/stress/run_chaos.py` (about 8 minutes).

## Result: 18 of 18 full seasons, no crash

| World | Seeds | Model calls per run | Invalid outputs logged (S15) | Decisions |
|---|---|---|---|---|
| A | 1–3 | ~3,800 | ~1,080 | 11–20 |
| B | 1–3 | ~4,300 (every call type) | ~1,200 | 20–28 |
| C | 1–3 | ~3,100–3,800 | 840–1,090 | 13–20 |
| A+text | 1–3 | as A (same engine path) | as A | 11–20 |
| B40 | 1–3 | ~15,400 | ~4,500 | 46–60 |
| B-nolot | 1–3 | ~4,200 | ~1,200 | 25–32 |

## Found and fixed

- **The 40-citizen worlds crashed the model brain** (`KeyError: 11`): persona texts
  were looked up by index, and 04 §3 has only 11. A citizen now reads its persona by
  name ("Kofi 2" reads Kofi's text under its own name). Freeze amendment 3.

`tests/test_chaos.py` keeps a short version of this in the test suite, including an
exact replay of a chaos run.
