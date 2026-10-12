"""Command-line runner: ``synw run <world.yaml> --seed N --out runs/``."""

import argparse
import sys

from .events import log_hash
from .runner import run
from .shocks import ARMS


def main(argv=None):
    ap = argparse.ArgumentParser(prog="synw", description="Syntroworld engine (mock brain only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run one season and write its event log")
    r.add_argument("world", help="world config, e.g. worlds/a.yaml")
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--out", default="runs/")
    r.add_argument("--arm", default="none", choices=sorted(ARMS))
    r.add_argument("--lambda", dest="lam", type=int, default=None,
                   help="planted-mock sensitivity, per-mille (default: the world's brain.lambda)")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        w = run(args.world, args.seed, out=args.out, arm=args.arm, lam=args.lam, keep_events=False)
        print(f"{w.log_path}  sha256={log_hash(w.log_path)}  events={w.log.seq}  {w.elapsed:.2f}s")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
