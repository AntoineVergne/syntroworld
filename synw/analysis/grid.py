"""Run a grid of seeds and write one row of run-level outcomes per run (06 §7.1).

    python -m synw.analysis.grid --world worlds/b.yaml --arm full --seeds 1-2000 \\
        --out runs/grid-b-full.jsonl --procs 4

For any arm other than ``none``, each seed is also run on the ``none`` twin (same world,
same seed) so P4 can be computed. Rows are written in seed order, so the output file
is deterministic.
"""

import argparse
import json
import os
import sys
from multiprocessing import Pool

from ..metrics import Run
from ..metrics.economy import p2_gini, s1_basket_floor, s2_output, s3_commons
from ..metrics.harm import s16_deaths, s17_exits, s18_harm_rate
from ..metrics.legitimacy import p1_compliance, s4_founding_compliance
from ..metrics.participation import p3_civic_breadth
from ..metrics.resilience import p4_output_loss
from ..metrics.secondary import compute as secondary
from ..runner import run as run_world
from .calibrate import parse_seeds


def outcomes(world, seed, arm="none", lam=None, twin=True):
    """Run-level outcomes for one world, arm and seed (P4 against the ``none`` twin)."""
    w = run_world(world, seed, arm=arm, lam=lam)
    r = Run(w.log.header, w.log.events)
    twin_run = r
    if arm != "none" and twin:
        t = run_world(world, seed, arm="none", lam=lam)
        twin_run = Run(t.log.header, t.log.events)
    return row(r, twin_run if (arm == "none" or twin) else None, arm, seed, w.lam, w.log.footer["state_hash"])


def row(r, twin_run, arm, seed, lam, state_hash):
    """Run-level outcomes from a run (and its ``none`` twin for P4; None leaves P4 empty)."""
    s3 = s3_commons(r)
    sec = secondary(r)
    return {
        "world": r.header["world"], "arm": arm, "seed": seed, "lambda": lam,
        "P1": p1_compliance(r), "P2": p2_gini(r), "P3": p3_civic_breadth(r),
        "P4": p4_output_loss(r, twin_run) if twin_run is not None else None,
        "S1": s1_basket_floor(r), "S2": s2_output(r), "S3": s3["share_sustainable"] if s3 else None,
        "S4": s4_founding_compliance(r), "S16": s16_deaths(r)["count"], "S17": s17_exits(r)["count"],
        "S18": s18_harm_rate(r), "state_hash": state_hash,
        "S5": sec["S5"], "S6": sec["S6"]["run"], "S7": sec["S7"], "S8": sec["S8"],
        "S9": sec["S9"]["count"],
        "S10": sec["S10"]["gross"] if sec["S10"] else None,
        "S11": sec["S11"]["ticks"] if sec["S11"] else None,
        "S11_censored": sec["S11"]["censored"] if sec["S11"] else None,
        "S12": sec["S12"], "S13_sittings": sec["S13"]["sittings"], "S13_dividend": sec["S13"]["dividend_full"],
        "S14_idle": sec["S14"]["idle_end"], "S14_deficit_days": sec["S14"]["deficit_days"],
        "S15": sec["S15"]["share"],
    }


def _one(args):
    return outcomes(*args)


def run_grid(world, seeds, arm="none", lam=None, procs=1, twin=True):
    jobs = [(world, s, arm, lam, twin) for s in seeds]
    if procs > 1:
        with Pool(procs) as p:
            return p.map(_one, jobs, chunksize=4)
    return [_one(j) for j in jobs]


def write_rows(rows, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a seed grid and write run-level outcomes")
    ap.add_argument("--world", required=True)
    ap.add_argument("--arm", default="none")
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--lambda", dest="lam", type=int, default=None)
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--no-twin", action="store_true", help="skip the none twin (P4 left empty)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows = run_grid(args.world, parse_seeds(args.seeds), args.arm, args.lam, args.procs, twin=not args.no_twin)
    write_rows(rows, args.out)
    print(f"{len(rows)} runs -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
