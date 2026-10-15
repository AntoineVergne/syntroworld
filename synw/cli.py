"""Command-line runner: ``synw run <world.yaml> --seed N --out runs/``."""

import argparse
import sys

from .events import log_hash
from .runner import run
from .shocks import ARMS


def main(argv=None):
    ap = argparse.ArgumentParser(prog="synw", description="Syntropolis-Simtropolis engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run one season and write its event log")
    r.add_argument("world", help="world config, e.g. worlds/a.yaml")
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--out", default="runs/")
    r.add_argument("--arm", default="none", choices=sorted(ARMS))
    r.add_argument("--lambda", dest="lam", type=int, default=None,
                   help="planted-mock sensitivity, per-mille (default: the world's brain.lambda)")
    r.add_argument("--ticks", type=int, help="stop after this many ticks (L0 runs one cycle: 48)")
    m = r.add_argument_group("model brain (phase L, 03 §6.5)")
    m.add_argument("--brain", choices=["mock", "model"], default="mock")
    m.add_argument("--model", help="LiteLLM model name")
    m.add_argument("--budget-tokens", type=int, help="token cap for the run")
    m.add_argument("--replay", help="replay the model replies of this run log (no model calls)")
    m.add_argument("--tokens-in", type=float, help="estimated input tokens per agent-tick")
    m.add_argument("--tokens-out", type=float, help="estimated output tokens per agent-tick")
    m.add_argument("--usd-in-per-mtok", type=float)
    m.add_argument("--usd-out-per-mtok", type=float)
    m.add_argument("--approve", action="store_true", help="Antoine's explicit yes to the printed cost")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        brain = _model_brain(ap, args) if args.brain == "model" else None
        if brain is False:
            return 2
        w = run(args.world, args.seed, out=args.out, arm=args.arm, lam=args.lam, keep_events=False,
                brain=brain, ticks=args.ticks)
        print(f"{w.log_path}  sha256={log_hash(w.log_path)}  events={w.log.seq}  {w.elapsed:.2f}s")
        return 0
    return 1


def _model_brain(ap, args):
    """Build the model brain spec; print the cost estimate and require --approve (06 §8.2)."""
    from .brains.model import LiteLLMTransport, ReplayTransport
    from .events import read_log
    if not args.budget_tokens:
        ap.error("--brain model needs --budget-tokens")
    if args.replay:
        _, events, _ = read_log(args.replay)
        return {"type": "model", "transport": ReplayTransport(events), "budget_tokens": args.budget_tokens}
    if not args.model:
        ap.error("--brain model needs --model (or --replay)")
    from .analysis import cost
    if args.tokens_in is None or args.tokens_out is None:
        ap.error("give --tokens-in and --tokens-out for the cost estimate (measure them in step L0)")
    if args.usd_in_per_mtok is not None and args.usd_out_per_mtok is not None:
        pin, pout = args.usd_in_per_mtok / 1e6, args.usd_out_per_mtok / 1e6
    else:
        pin, pout = cost.litellm_prices(args.model)
    ticks = args.ticks or cost.SEASON_TICKS
    text, _ = cost.report("run", 1, ticks, f"{args.world}, seed {args.seed}, arm {args.arm}",
                          args.tokens_in, args.tokens_out, pin, pout, "given")
    print(text)
    if not args.approve:
        print("Refusing to start a model run without --approve.", file=sys.stderr)
        return False
    return {"type": "model", "transport": LiteLLMTransport(args.model), "budget_tokens": args.budget_tokens,
            "approved": True}


if __name__ == "__main__":
    sys.exit(main())
