"""Determinism check (06 §8.1, step M0).

Each world is run twice per seed (seeds 1 to 20 by default, arms ``none`` and ``full``).
The two passes run in separate processes with different ``PYTHONHASHSEED`` values, so
nothing can depend on per-process string hashing. Pass conditions:

1. identical event-log hashes for every (world, arm, seed);
2. across worlds, the shock and weather event streams are identical for the same seed
   and arm: ``shock`` events, Sam's ``arrival``, and the misinformation posts (claims by
   the shock, compared without their running claim id and without the engine's truth
   flag, which evaluates world state at that moment and so may legitimately differ:
   "citizen X stole" is true in a world where X did steal).

    python -m synw.analysis.determinism --worlds worlds/a.yaml,worlds/b.yaml,worlds/c.yaml \\
        --seeds 1-20 --out results/m0
"""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool

from ..events import canonical, log_hash, read_log
from ..runner import run as run_world
from .calibrate import parse_seeds

ARMS = ("none", "full")
# fields that report how a shock landed in this world rather than what was scheduled:
# claim ids, the truth of a forged post, and the rogue actually hit (a replacement if the
# scheduled one had left; decisions.md, 28). Compared separately and listed in result.json.
WORLD_DEPENDENT = ("id", "true", "target", "applied", "replaced")


def world_stream(events):
    out = []
    for e in events:
        if e["type"] in ("shock", "arrival") or (e["type"] == "claim" and e["actor"] == "shock"):
            payload = {k: v for k, v in e["payload"].items() if k not in WORLD_DEPENDENT}
            out.append([e["tick"], e["type"], payload])
    return out


def rogue_replaced(events):
    return [e["payload"].get("target") for e in events if e["type"] == "shock"
            and e["payload"].get("shock") == "rogue" and e["payload"].get("replaced")]


def shock_claim_truth(events):
    return [e["payload"]["true"] for e in events if e["type"] == "claim" and e["actor"] == "shock"]


def _one(job):
    world, seed, arm, tmp = job
    w = run_world(world, seed, arm=arm, out=tmp, keep_events=False)
    _, events, _ = read_log(w.log_path)
    stream = world_stream(events)
    truth = shock_claim_truth(events)
    replaced = rogue_replaced(events)
    h = log_hash(w.log_path)
    os.remove(w.log_path)
    return {"world": w.cfg.get("world"), "path": world, "arm": arm, "seed": seed, "hash": h,
            "events": w.log.seq,
            "world_stream": hashlib.sha256(canonical(stream).encode()).hexdigest(), "n_world_events": len(stream), "shock_claims_true": truth,
            "rogue_replaced": replaced}


def one_pass(worlds, seeds, arms=ARMS, procs=1):
    with tempfile.TemporaryDirectory() as tmp:
        jobs = [(w, s, a, os.path.join(tmp, f"{i}")) for i, (w, s, a) in
                enumerate((w, s, a) for w in worlds for a in arms for s in seeds)]
        if procs > 1:
            with Pool(procs) as p:
                return p.map(_one, jobs, chunksize=2)
        return [_one(j) for j in jobs]


def _subprocess_pass(worlds, seeds, arms, procs, hashseed):
    with tempfile.NamedTemporaryFile("r", suffix=".json", delete=False) as fh:
        path = fh.name
    env = dict(os.environ, PYTHONHASHSEED=str(hashseed))
    cmd = [sys.executable, "-m", "synw.analysis.determinism", "--internal-pass", path,
           "--worlds", ",".join(worlds), "--seeds", ",".join(map(str, seeds)),
           "--arms", ",".join(arms), "--procs", str(procs)]
    subprocess.run(cmd, env=env, check=True)
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    os.remove(path)
    return rows


def check(worlds, seeds, arms=ARMS, procs=1, hashseeds=(1, 2)):
    p1 = _subprocess_pass(worlds, seeds, arms, procs, hashseeds[0])
    p2 = _subprocess_pass(worlds, seeds, arms, procs, hashseeds[1])
    key = lambda r: (r["world"], r["arm"], r["seed"])
    b = {key(r): r for r in p2}
    rows = []
    for r in p1:
        r2 = b[key(r)]
        rows.append({"world": r["world"], "arm": r["arm"], "seed": r["seed"], "hash_pass1": r["hash"],
                     "hash_pass2": r2["hash"], "identical": r["hash"] == r2["hash"], "events": r["events"],
                     "world_stream": r["world_stream"], "n_world_events": r["n_world_events"],
                     "shock_claims_true": r["shock_claims_true"], "rogue_replaced": r["rogue_replaced"]})
    rows.sort(key=lambda r: (r["world"], r["arm"], r["seed"]))
    cross = []
    for arm in arms:
        for s in seeds:
            streams = {r["world"]: r["world_stream"] for r in rows if r["arm"] == arm and r["seed"] == s}
            n = {r["world"]: r["n_world_events"] for r in rows if r["arm"] == arm and r["seed"] == s}
            truth = {r["world"]: r["shock_claims_true"] for r in rows if r["arm"] == arm and r["seed"] == s}
            cross.append({"arm": arm, "seed": s, "identical": len(set(streams.values())) == 1,
                          "worlds": sorted(streams), "n_world_events": n,
                          "truth_differs": len({json.dumps(v) for v in truth.values()}) > 1, "shock_claims_true": truth})
    res = {"worlds": sorted({r["world"] for r in rows}), "arms": list(arms), "seeds": list(seeds),
           "hashseeds": list(hashseeds), "runs_per_pass": len(rows),
           "identical_hashes": sum(r["identical"] for r in rows),
           "pass_hashes": all(r["identical"] for r in rows),
           "pass_world_streams": all(c["identical"] for c in cross),
           "shock_claim_truth_differs": [[c["arm"], c["seed"]] for c in cross if c["truth_differs"]],
           "rogue_replaced": [[r["world"], r["arm"], r["seed"], r["rogue_replaced"][0]] for r in rows if r["rogue_replaced"]]}
    res["pass"] = res["pass_hashes"] and res["pass_world_streams"]
    return res, rows, cross


def write(out, res, rows, cross):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "hashes.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["world", "arm", "seed", "hash_pass1", "hash_pass2", "identical", "events"])
        for r in rows:
            wr.writerow([r["world"], r["arm"], r["seed"], r["hash_pass1"], r["hash_pass2"],
                         int(r["identical"]), r["events"]])
    with open(os.path.join(out, "world-streams.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["arm", "seed", "identical_across_worlds", "world_events_per_world",
                     "shock_claim_truth_differs", "shock_claim_truth_by_world"])
        for c in cross:
            wr.writerow([c["arm"], c["seed"], int(c["identical"]), json.dumps(c["n_world_events"], sort_keys=True),
                         int(c["truth_differs"]), json.dumps(c["shock_claims_true"], sort_keys=True)])
    with open(os.path.join(out, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)


def report(res):
    n = res["runs_per_pass"]
    return [f"M0 determinism: worlds {', '.join(res['worlds'])}; arms {', '.join(res['arms'])}; "
            f"seeds {res['seeds'][0]}-{res['seeds'][-1]}; two passes with PYTHONHASHSEED "
            f"{res['hashseeds'][0]} and {res['hashseeds'][1]}",
            f"{'PASS' if res['pass_hashes'] else 'FAIL'}  identical event-log hashes: {res['identical_hashes']} of {n}",
            f"{'PASS' if res['pass_world_streams'] else 'FAIL'}  shock and weather streams identical across worlds for each seed and arm"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="06 step M0: determinism")
    ap.add_argument("--worlds", default="worlds/a.yaml,worlds/b.yaml,worlds/c.yaml")
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--out")
    ap.add_argument("--internal-pass", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    worlds = args.worlds.split(",")
    seeds = parse_seeds(args.seeds)
    arms = tuple(args.arms.split(","))
    if args.internal_pass:
        rows = one_pass(worlds, seeds, arms, args.procs)
        with open(args.internal_pass, "w", encoding="utf-8") as fh:
            json.dump(rows, fh)
        return 0
    res, rows, cross = check(worlds, seeds, arms, args.procs)
    if args.out:
        write(args.out, res, rows, cross)
    for line in report(res):
        print(line)
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
