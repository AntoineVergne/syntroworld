# Phase L runbook

Every step that calls a model needs Antoine's explicit yes and a printed cost estimate
(06 §8.2). Nothing here has been run with a model yet.

## 0. Once: give the environment model access

In the cloud environment's settings (environment menu in the session title bar → Edit):

1. **Network access** → allow the provider's host (for example `api.moonshot.ai`, or
   `openrouter.ai`), keeping package managers allowed.
2. **Secrets / environment variables** → the provider's API key, under the name
   LiteLLM expects (for example `MOONSHOT_API_KEY` or `OPENROUTER_API_KEY`). Never paste
   a key into a chat.
3. Start a new session (settings apply to new sessions), then:
   `pip install -e ".[model]"`

Decide: the exact LiteLLM model name (one Kimi model for every citizen, 04 §6), and a
spend cap per step.

## 1. Before L0: read what the citizens read

`results/l0-prompts/`: the exact prompts in A, B, C and A+text. Check the persona,
the world guide, and that nothing hints at which world is "better" outside the texts
section.

## 2. L0 smoke: World B, seed 1, one cycle

    python -m synw.analysis.campaign --step L0 --out runs/l0 --model <name> \
        --run-budget-tokens 3000000 --spend-cap-usd <cap> --tokens-in 5500 --tokens-out 60
    # prints the estimate and stops; after Antoine's yes, add --approve

Then measure: `python -m synw.analysis.cost --step L1 --log runs/l0/B-none-s1.jsonl --model <name>`
gives real tokens per agent-tick, the invalid-output rate (S15), and the L1 estimate.

## 3. L1 pilot: A, B, C × seeds 1–2 × arms full and none (12 runs)

    python -m synw.analysis.campaign --step L1 --out runs/l1 --model <name> \
        --run-budget-tokens <n> --spend-cap-usd <cap> --log runs/l0/B-none-s1.jsonl --approve
    python -m synw.analysis.phase_l --campaign runs/l1 --pilot --label "L1 pilot"
    python -m synw.analysis.persona_check --campaign runs/l1 --mock-seeds 1-10

`pilot.md` gives seeds per world (06 §7.4; the null mock alone already asks 33–60 for
P2 and P4, `results/l-dry-run/`). Parameter fixes are allowed here, then re-freeze.
Pilot data is not used in the main analysis.

## 4. L2 main grid: A, B, C, A+text × n seeds

    python -m synw.analysis.campaign --step L2 --seeds <n> --out runs/l2 --model <name> \
        --run-budget-tokens <n> --spend-cap-usd <cap> --log runs/l0/B-none-s1.jsonl --approve
    python -m synw.analysis.phase_l --campaign runs/l2 --label "Phase L"

Add `--no-twins` if the pilot shows the `none` twins are too costly (weaker P4,
labelled). The campaign resumes if interrupted; failed runs are re-run once, then
listed as missing (06 §7.5).
