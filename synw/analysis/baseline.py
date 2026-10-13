"""Mechanical baseline (06 §8.1, step M4). Null mock only.

Cells (world × arm):
- worlds A, B, C and the four B ablations × arms ``none`` and ``full``, 200 seeds;
- worlds A, B, C × single-shock arms ``drought``, ``misinfo``, ``rogue``, 200 seeds;
- the population-size check: A, B, C at 40 citizens (``worlds/size40/``) × ``none`` and
  ``full``, 50 seeds.

P4 needs the no-shock twin of the same world and seed. Its formula,
1 − output(arm, days 7–24) / output(none, days 7–24), is 1 − S2(arm) / S2(none), so it is
computed from the ``none`` cell instead of running every twin again.

    python -m synw.analysis.baseline run --out results/m4      # resumable, one file per cell
    python -m synw.analysis.baseline report --out results/m4

Every number here is a property of the rules' arithmetic acting on rule-following mock
agents: a mechanical baseline, not a finding about AI agents (06 §2).
"""

import argparse
import csv
import os
import sys

from .compare import ALPHA, BETTER, SESOI, holm, t_interval, verdict
from .false_positive import _np, sign_flip_p
from .grid import read_rows, run_grid, write_rows

LABEL = "Mechanical baseline (null mock), not findings about AI agents."

MAIN = {"A": "worlds/a.yaml", "B": "worlds/b.yaml", "C": "worlds/c.yaml"}
ABLATIONS = {"B-nolot": "worlds/ablations/b-nolot.yaml", "B-noadv": "worlds/ablations/b-noadv.yaml",
             "B-nodiv": "worlds/ablations/b-nodiv.yaml", "B-nopay": "worlds/ablations/b-nopay.yaml"}
SIZE = {"A40": "worlds/size40/a.yaml", "B40": "worlds/size40/b.yaml", "C40": "worlds/size40/c.yaml"}
SINGLE = ("drought", "misinfo", "rogue")
PRIMARY = ("P1", "P2", "P3", "P4")
SECONDARY = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S10", "S11", "S12", "S13_sittings",
             "S13_dividend", "S14_idle", "S16", "S17", "S18")


def cells(seeds=200, size_seeds=50):
    out = []
    for w, path in {**MAIN, **ABLATIONS}.items():
        for arm in ("none", "full"):
            out.append((w, path, arm, seeds))
    for w, path in MAIN.items():
        for arm in SINGLE:
            out.append((w, path, arm, seeds))
    for w, path in SIZE.items():
        for arm in ("none", "full"):
            out.append((w, path, arm, size_seeds))
    return out


def cell_file(out, world, arm):
    return os.path.join(out, "rows", f"{world}-{arm}.jsonl")


def run_cells(out, seeds=200, size_seeds=50, procs=4, log=print):
    for world, path, arm, n in cells(seeds, size_seeds):
        f = cell_file(out, world, arm)
        if os.path.exists(f):
            log(f"skip {world} {arm} (done)")
            continue
        rows = run_grid(path, list(range(1, n + 1)), arm, lam=0, procs=procs, twin=False)
        for r in rows:
            r["world"] = world
        write_rows(rows, f + ".tmp")
        os.replace(f + ".tmp", f)
        log(f"done {world} {arm}: {len(rows)} runs")


def load(out, seeds=200, size_seeds=50):
    """{(world, arm): {seed: row}} with P4 filled in from the matching none cell."""
    data = {}
    for world, _path, arm, _n in cells(seeds, size_seeds):
        f = cell_file(out, world, arm)
        if os.path.exists(f):
            data[(world, arm)] = {r["seed"]: r for r in read_rows(f)}
    for (world, arm), rows in data.items():
        twin = data.get((world, "none"), {})
        for s, r in rows.items():
            t = twin.get(s)
            if arm == "none":
                r["P4"] = 0.0
            elif t and t.get("S2"):
                r["P4"] = 1.0 - r["S2"] / t["S2"]
            else:
                r["P4"] = None
    return data


def _vals(rows, y):
    return [r[y] for r in rows.values() if r.get(y) is not None]


def summary(data, outcomes=PRIMARY + SECONDARY):
    out = []
    for (world, arm), rows in sorted(data.items()):
        rec = {"world": world, "arm": arm, "n": len(rows)}
        for y in outcomes:
            v = _vals(rows, y)
            if v:
                lo, hi = t_interval(v) if len(v) > 1 else (None, None)
                rec[y] = sum(v) / len(v)
                rec[y + "_lo"], rec[y + "_hi"] = lo, hi
        out.append(rec)
    return out


def paired(data, a, b, arm, y):
    ra, rb = data.get((a, arm), {}), data.get((b, arm), {})
    seeds = sorted(s for s in ra if s in rb and ra[s].get(y) is not None and rb[s].get(y) is not None)
    return [ra[s][y] - rb[s][y] for s in seeds]


def contrast(d, seed, n_flips):
    np = _np()
    est = sum(d) / len(d) if d else None
    ci = t_interval(d)
    p = float(sign_flip_p(np.array(d)[:, None], n_flips, np.random.default_rng(seed))[0]) if len(d) > 1 else None
    return est, ci, p


def contrasts(data, seed=20261014, n_flips=100000):
    rows = []
    primary = []
    for c in ("A", "C"):
        for y in PRIMARY:
            d = paired(data, "B", c, "full", y)
            est, ci, p = contrast(d, seed, n_flips)
            r = {"family": "primary", "contrast": f"B vs {c}", "arm": "full", "outcome": y, "n": len(d),
                 "estimate": est, "lo": ci[0], "hi": ci[1], "p": p}
            primary.append(r)
    adj = holm([r["p"] if r["p"] is not None else 1.0 for r in primary])
    for r, pa in zip(primary, adj):
        r["p_holm"] = pa
        r["verdict"] = verdict(r["estimate"], (r["lo"], r["hi"]), pa, SESOI[r["outcome"]], BETTER[r["outcome"]], ALPHA)
    rows += primary

    def descriptive(family, a, b, arm, outcomes=PRIMARY):
        for y in outcomes:
            d = paired(data, a, b, arm, y)
            if not d:
                continue
            est, ci, p = contrast(d, seed, n_flips)
            rows.append({"family": family, "contrast": f"{a} vs {b}", "arm": arm, "outcome": y, "n": len(d),
                         "estimate": est, "lo": ci[0], "hi": ci[1], "p": p})
    descriptive("secondary", "A", "C", "full")
    descriptive("no shocks", "B", "A", "none")
    descriptive("no shocks", "B", "C", "none")
    for abl in ABLATIONS:
        descriptive("ablation", "B", abl, "full")
    for arm in SINGLE:
        descriptive("single shock", "B", "A", arm)
        descriptive("single shock", "B", "C", arm)
    descriptive("size check", "B40", "A40", "full")
    descriptive("size check", "B40", "C40", "full")
    return rows


FMT = {"P1": ("{:.1%}", 1), "P2": ("{:.3f}", 1), "P3": ("{:.1%}", 1), "P4": ("{:.1%}", 1),
       "S1": ("{:.1%}", 1), "S2": ("{:,.0f}", 1e-3), "S3": ("{:.1%}", 1), "S4": ("{:.1%}", 1),
       "S5": ("{:.1%}", 1), "S6": ("{:+.2f}", 1), "S7": ("{:.3f}", 1), "S8": ("{:.3f}", 1),
       "S10": ("{:,.0f}", 1e-3), "S11": ("{:.0f}", 1), "S12": ("{:.0f}", 1), "S13_sittings": ("{:.1%}", 1),
       "S13_dividend": ("{:.1%}", 1), "S14_idle": ("{:,.0f}", 1e-3), "S16": ("{:.2f}", 1),
       "S17": ("{:.2f}", 1), "S18": ("{:.1f}", 1)}

NAMES = {"P1": "P1 compliance", "P2": "P2 wealth Gini", "P3": "P3 civic breadth", "P4": "P4 output loss",
         "S1": "S1 basket floor", "S2": "S2 output (credits)", "S3": "S3 days River ≥ K/2",
         "S4": "S4 founding-norm compliance", "S5": "S5 loser's compliance", "S6": "S6 capture index",
         "S7": "S7 influence Gini", "S8": "S8 participation Gini", "S10": "S10 rogue theft (credits)",
         "S11": "S11 containment (ticks)", "S12": "S12 misbelief (citizen-days)",
         "S13_sittings": "S13 sittings decided under shock", "S13_dividend": "S13 dividend days paid in full",
         "S14_idle": "S14 idle Treasury (credits)", "S16": "S16 deaths per run", "S17": "S17 exits per run",
         "S18": "S18 harm per 100 citizen-days"}


def fmt(y, v):
    if v is None:
        return "–"
    f, scale = FMT.get(y, ("{:.3f}", 1))
    return f.format(v * scale)


def fmt_diff(y, v):
    if v is None:
        return "–"
    if y in ("P1", "P3", "P4", "S1", "S3", "S4", "S5", "S13_sittings", "S13_dividend"):
        return f"{v * 100:+.2f} pts"
    if y in ("S2", "S10", "S14_idle"):
        return f"{v / 1000:+,.1f}"
    return f"{v:+.3f}"


def write_report(out, data, rows, summ):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "summary.csv"), "w", newline="", encoding="utf-8") as fh:
        keys = ["world", "arm", "n"] + [k for y in PRIMARY + SECONDARY for k in (y, y + "_lo", y + "_hi")]
        wr = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        wr.writeheader()
        for r in summ:
            wr.writerow(r)
    with open(os.path.join(out, "contrasts.csv"), "w", newline="", encoding="utf-8") as fh:
        keys = ["family", "contrast", "arm", "outcome", "n", "estimate", "lo", "hi", "p", "p_holm", "verdict"]
        wr = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    S = {(r["world"], r["arm"]): r for r in summ}
    L = [f"# Step M4: mechanical baseline (06 §8.1)", "", f"**{LABEL}**", "",
         "Every number below comes from the null mock: rule-following agents whose behaviour does",
         "not respond to how legitimate an institution is. Differences between worlds are what the",
         "institutions do *mechanically*: through rules, sanctions, money and information. Phase L",
         "compares model societies against this baseline (06 §2).", "",
         "Means with 95% t-intervals over seeds. Paired contrasts are by seed (common random numbers).",
         "Files: `summary.csv` (every cell and outcome), `contrasts.csv`, raw rows in `rows/`.", ""]

    def cell_table(worlds, arms, outcomes, title):
        L.append(f"## {title}")
        L.append("")
        L.append("| World | Arm | n | " + " | ".join(NAMES[y] for y in outcomes) + " |")
        L.append("|---|---|---|" + "---|" * len(outcomes))
        for w in worlds:
            for a in arms:
                r = S.get((w, a))
                if not r:
                    continue
                cellv = []
                for y in outcomes:
                    if y not in r:
                        cellv.append("–")
                    elif r.get(y + "_lo") is None:
                        cellv.append(fmt(y, r[y]))
                    else:
                        cellv.append(f"{fmt(y, r[y])} ({fmt(y, r[y + '_lo'])}–{fmt(y, r[y + '_hi'])})")
                L.append(f"| {w} | {a} | {r['n']} | " + " | ".join(cellv) + " |")
        L.append("")

    cell_table(("A", "B", "C"), ("none", "full"), PRIMARY, "Primary outcomes, worlds A, B, C")
    cell_table(("A", "B", "C"), ("none", "full"), ("S1", "S2", "S3", "S4", "S16", "S17", "S18"),
               "Economy, commons and harm")
    cell_table(("A", "B", "C"), ("full",), ("S5", "S6", "S7", "S8", "S10", "S11", "S12", "S13_sittings",
                                            "S13_dividend", "S14_idle"), "Governance outcomes (`full` arm)")
    L += ["## Primary contrasts (`full` arm, 8 tests, Holm)", "",
          "Paired by seed. Sign-flip test with 100,000 random flips; Holm across the 8 tests; verdicts per 06 §7.2.",
          "", "| Contrast | Outcome | n | Estimate | 95% CI | p | p (Holm) | Verdict |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["family"] == "primary":
            L.append(f"| {r['contrast']} | {NAMES[r['outcome']]} | {r['n']} | {fmt_diff(r['outcome'], r['estimate'])} | "
                     f"{fmt_diff(r['outcome'], r['lo'])} to {fmt_diff(r['outcome'], r['hi'])} | {r['p']:.5f} | "
                     f"{r['p_holm']:.5f} | {r['verdict']} |")
    L += ["", "Better is: higher P1 and P3, lower P2 and P4. SESOI: P1 5 points, P2 0.05, P3 10 points, P4 5 points.", ""]

    def contrast_table(family, title, note=None):
        rr = [r for r in rows if r["family"] == family]
        if not rr:
            return
        L.append(f"## {title}")
        L.append("")
        if note:
            L.append(note)
            L.append("")
        L.append("| Contrast | Arm | Outcome | n | Estimate | 95% CI | p (uncorrected) |")
        L.append("|---|---|---|---|---|---|---|")
        for r in rr:
            L.append(f"| {r['contrast']} | {r['arm']} | {NAMES[r['outcome']]} | {r['n']} | "
                     f"{fmt_diff(r['outcome'], r['estimate'])} | {fmt_diff(r['outcome'], r['lo'])} to "
                     f"{fmt_diff(r['outcome'], r['hi'])} | {r['p']:.4f} |")
        L.append("")
    contrast_table("secondary", "A vs C (secondary)")
    contrast_table("no shocks", "B vs A and B vs C without shocks (`none` arm)")
    contrast_table("ablation", "Ablations: B minus one mechanism (`full` arm)",
                   "A positive estimate means B scores higher than the ablation, i.e. the mechanism raises "
                   "that outcome.")
    cell_table(("B-nolot", "B-noadv", "B-nodiv", "B-nopay"), ("none", "full"), PRIMARY, "Ablation cells")
    cell_table(("A", "B", "C"), SINGLE, PRIMARY, "Single-shock arms")
    contrast_table("single shock", "B vs A and B vs C under each single shock")
    cell_table(("A40", "B40", "C40"), ("none", "full"), PRIMARY + ("S1", "S16", "S17"),
               "Population-size check: 40 citizens, 50 seeds")
    contrast_table("size check", "Size check contrasts (40 citizens, `full` arm)")
    L += ["---", "", f"_{LABEL}_", ""]
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    return L


def main(argv=None):
    ap = argparse.ArgumentParser(description="06 step M4: mechanical baseline")
    ap.add_argument("command", choices=["run", "report"])
    ap.add_argument("--out", default="results/m4")
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--size-seeds", type=int, default=50)
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--flips", type=int, default=100000)
    args = ap.parse_args(argv)
    if args.command == "run":
        run_cells(args.out, args.seeds, args.size_seeds, args.procs)
        return 0
    data = load(args.out, args.seeds, args.size_seeds)
    rows = contrasts(data, n_flips=args.flips)
    write_report(args.out, data, rows, summary(data))
    print(f"report: {os.path.join(args.out, 'report.md')}  ({len(data)} cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
