"""Calibration report for the null world (03 §10.2, 06 step M1).

Runs a world (World A by default) with the null mock over a seed range, with no shocks
(plus the drought-only and full arms for the shock targets), and prints each target with its value
and pass/fail. Tuning the parameters is a separate step.

    python -m synw.analysis.calibrate --world worlds/a.yaml --seeds 1-20
"""

import argparse
import statistics
import sys

from ..metrics import Run
from ..metrics.economy import gini_by_day, output_by_day, river_ever_below, s1_basket_floor
from ..metrics.harm import s16_deaths, s17_exits, s18_harm_rate
from ..metrics.legitimacy import s4_founding_compliance
from ..metrics.resilience import p4_output_loss
from ..runner import run as run_world
from ..shocks import shock_config


def parse_seeds(spec):
    out = []
    for part in str(spec).split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def _run(world, seed, arm):
    w = run_world(world, seed, arm=arm, lam=0)
    return Run(w.log.header, w.log.events), w.elapsed


def collect(world, seeds):
    rows = []
    for s in seeds:
        r, t = _run(world, s, "none")
        rd, td = _run(world, s, "drought")
        rf, tf = _run(world, s, "full")
        g = gini_by_day(r)
        days = sorted(g)
        o_none, o_dr = output_by_day(r), output_by_day(rd)
        ddays = range(7, 7 + shock_config(r.cfg)["drought"]["days"])
        base = sum(o_none.get(d, 0) for d in ddays)
        drought_loss = (1 - sum(o_dr.get(d, 0) for d in ddays) / base) if base else None
        rows.append({
            "seed": s,
            "gini_rise": g[days[-1]] - g[days[0]],
            "river_below": river_ever_below(r),
            "s1": s1_basket_floor(r),
            "s4": s4_founding_compliance(r),
            "departures": s16_deaths(r)["count"] + s17_exits(r)["count"],
            "s18": s18_harm_rate(r),
            "drought_loss": drought_loss,
            "p4_full": p4_output_loss(rf, r),
            "seconds": max(t, td, tf),
        })
    return rows


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def targets(rows):
    n = len(rows)
    share = lambda pred: sum(1 for r in rows if pred(r)) / n if n else None
    gr = _median([r["gini_rise"] for r in rows])
    rb = share(lambda r: r["river_below"])
    s1 = _median([r["s1"] for r in rows])
    s4 = _median([r["s4"] for r in rows])
    dep_any = share(lambda r: r["departures"] > 0)
    dep_med = _median([r["departures"] for r in rows])
    harm = share(lambda r: (r["s18"] or 0) > 0)
    dl = _median([r["drought_loss"] for r in rows])
    p4 = _median([r["p4_full"] for r in rows])
    secs = max(r["seconds"] for r in rows) if rows else None
    ok = lambda v, lo=None, hi=None: v is not None and (lo is None or v >= lo) and (hi is None or v <= hi)
    return [
        ("median window Gini rise day 1 to day 24 >= 0.10", f"{gr:.3f}" if gr is not None else "NA", ok(gr, 0.10)),
        ("runs with River below K/2 at some point in 30%..70%", f"{rb:.0%}", ok(rb, 0.30, 0.70)),
        ("basket floor S1 (median) in 70%..95%", f"{s1:.1%}" if s1 is not None else "NA", ok(s1, 0.70, 0.95)),
        ("founding-norm compliance S4 (median) in 85%..98%", f"{s4:.1%}" if s4 is not None else "NA", ok(s4, 0.85, 0.98)),
        ("runs with a death or exit in 10%..50%; median departures <= 1",
         f"{dep_any:.0%}; median {dep_med}", ok(dep_any, 0.10, 0.50) and ok(dep_med, None, 1)),
        ("runs with harm rate S18 > 0 >= 80%", f"{harm:.0%}", ok(harm, 0.80)),
        ("drought lowers output on its days by >= 10% vs twin (median)", f"{dl:.1%}" if dl is not None else "NA", ok(dl, 0.10)),
        ("full-arm output loss P4 (median) in 10%..20% (decision 27)", f"{p4:.1%}" if p4 is not None else "NA", ok(p4, 0.10, 0.20)),
        ("one run takes under 10 seconds (slowest)", f"{secs:.2f}s" if secs is not None else "NA", ok(secs, None, 10.0)),
    ]


def report(rows):
    lines = []
    for name, value, passed in targets(rows):
        lines.append(f"{'PASS' if passed else 'FAIL'}  {name}: {value}")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="worlds/a.yaml")
    ap.add_argument("--seeds", default="1-20")
    args = ap.parse_args(argv)
    rows = collect(args.world, parse_seeds(args.seeds))
    print(f"calibration: {args.world}, null mock, seeds {args.seeds} ({len(rows)} seeds, arms none + drought + full)")
    for line in report(rows):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
