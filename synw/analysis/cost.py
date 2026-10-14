"""Cost estimate before each phase L step (06 §8.2), printed for Antoine's approval.

    cost = runs × citizens × ticks × (input_tokens × input_price + output_tokens × output_price)

Tokens per agent-tick come from a measured log (step L0) or are given by hand before L0.
Prices are per token, read from the LiteLLM price table on the day of the estimate
(``litellm.model_cost``), or given by hand in USD per million tokens. No price is stored
in this repository.

    python -m synw.analysis.cost --step L0 --tokens-in 4000 --tokens-out 60 \\
        --usd-in-per-mtok <in> --usd-out-per-mtok <out>
    python -m synw.analysis.cost --step L1 --log runs/l0/B-full-s1.jsonl --model <litellm name>
    python -m synw.analysis.cost --step L2 --seeds 60 --log ... --model ...
"""

import argparse
import sys

from ..events import read_log

CITIZENS = 11                 # 10 founders + Sam (06 §4); an upper bound, Sam arrives day 4
SEASON_TICKS = 384
CYCLE_TICKS = 48


def step_plan(step, seeds=None, twins=True):
    """(runs, ticks per run, description) for a phase L step (06 §8.2)."""
    if step == "L0":
        return 1, CYCLE_TICKS, "World B, 1 seed, 1 cycle"
    if step == "L1":
        return 3 * 2 * 2, SEASON_TICKS, "Worlds A, B, C × 2 seeds × arms full and none"
    if step == "L2":
        if not seeds:
            raise ValueError("L2 needs --seeds (n from 06 §7.4 and the pilot)")
        arms = 2 if twins else 1
        return 4 * seeds * arms, SEASON_TICKS, (f"Worlds A, B, C, A+text × {seeds} seeds × "
                                                + ("arms full and none" if twins else "arm full"))
    raise ValueError(f"unknown step {step!r}")


def estimate(runs, citizens, ticks, tokens_in, tokens_out, price_in, price_out):
    """06 §8.2. Tokens are per agent-tick; prices per token."""
    return runs * citizens * ticks * (tokens_in * price_in + tokens_out * price_out)


def measure(path):
    """Tokens per agent-tick and invalid-output rate from a model run log (step L0)."""
    header, events, footer = read_log(path)
    calls = [e for e in events if e["type"] == "model_call"]
    agent_ticks = sum(1 for e in calls if e["payload"]["call"] == "act")
    if not agent_ticks:
        raise ValueError(f"{path}: no model act calls")
    tin = sum(e["payload"]["input_tokens"] for e in calls)
    tout = sum(e["payload"]["output_tokens"] for e in calls)
    invalid = sum(1 for e in events if e["type"] in ("invalid_action", "invalid_output"))
    return {"agent_ticks": agent_ticks, "calls": len(calls), "tokens_in": tin / agent_ticks,
            "tokens_out": tout / agent_ticks, "invalid_rate": invalid / len(calls),
            "model": header.get("brain", {}).get("model"), "status": (footer or {}).get("status", "ok")}


def litellm_prices(model):
    """(input, output) USD per token from LiteLLM's price table, read today."""
    import litellm
    row = litellm.model_cost.get(model)
    if not row:
        raise KeyError(f"{model!r} is not in the LiteLLM price table")
    return row["input_cost_per_token"], row["output_cost_per_token"]


def report(step, runs, ticks, desc, tokens_in, tokens_out, price_in, price_out, source,
           citizens=CITIZENS):
    usd = estimate(runs, citizens, ticks, tokens_in, tokens_out, price_in, price_out)
    return "\n".join([
        f"Cost estimate for step {step} ({desc})",
        f"  runs {runs} × citizens {citizens} × ticks {ticks} = {runs * citizens * ticks:,} agent-ticks",
        f"  tokens per agent-tick: {tokens_in:,.0f} in, {tokens_out:,.0f} out ({source})",
        f"  prices: ${price_in * 1e6:.4f} / M in, ${price_out * 1e6:.4f} / M out",
        f"  estimate: ${usd:,.2f}",
        "  Needs Antoine's explicit yes before the step runs (06 §8.2).",
    ]), usd


def main(argv=None):
    ap = argparse.ArgumentParser(description="06 §8.2 cost estimate for a phase L step")
    ap.add_argument("--step", required=True, choices=["L0", "L1", "L2"])
    ap.add_argument("--seeds", type=int, help="seeds per world (L2)")
    ap.add_argument("--no-twins", action="store_true", help="L2 without none twins (05 P4, weaker)")
    ap.add_argument("--log", help="a measured model run log (L0) for tokens per agent-tick")
    ap.add_argument("--tokens-in", type=float)
    ap.add_argument("--tokens-out", type=float)
    ap.add_argument("--model", help="LiteLLM model name; prices read from its price table")
    ap.add_argument("--usd-in-per-mtok", type=float)
    ap.add_argument("--usd-out-per-mtok", type=float)
    a = ap.parse_args(argv)
    runs, ticks, desc = step_plan(a.step, a.seeds, not a.no_twins)
    if a.log:
        m = measure(a.log)
        tin, tout, source = m["tokens_in"], m["tokens_out"], f"measured in {a.log}"
    elif a.tokens_in is not None and a.tokens_out is not None:
        tin, tout, source = a.tokens_in, a.tokens_out, "given by hand, not measured"
    else:
        ap.error("give --log or both --tokens-in and --tokens-out")
    if a.usd_in_per_mtok is not None and a.usd_out_per_mtok is not None:
        pin, pout = a.usd_in_per_mtok / 1e6, a.usd_out_per_mtok / 1e6
    elif a.model:
        pin, pout = litellm_prices(a.model)
    else:
        ap.error("give --model or both --usd-in-per-mtok and --usd-out-per-mtok")
    text, _ = report(a.step, runs, ticks, desc, tin, tout, pin, pout, source)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
