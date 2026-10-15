"""Phase L analysis (06 §7, §8.3): written and tested on phase M data before any model run.

Reads a campaign directory (``runs.csv`` and the run logs, ``synw.analysis.campaign``)
and writes:

- ``rows.jsonl``: run-level outcomes, one row per completed run (the same as phase M);
- ``pilot.md`` (step L1): σ_d of each primary contrast and the seeds per world it asks
  for, 06 §7.4: ``n = max(12, ceil(12.8 × (σ_d / SESOI)²))``;
- ``report.md`` (step L2): the 8 primary tests with Holm and verdicts (06 §7.2); the
  secondary contrasts (A vs C, A+text vs A, B vs A+text) as estimates only; H2's output
  check, H5's capture index; and each primary estimate's **departure from the mechanical
  baseline** (M4, null mock, same contrast, ``results/m4/contrasts.csv``);
- ``seeds.svg``: seed-level paired differences for each primary test;
- ``runs.csv`` copied in as the run list, with the seeds each contrast had to drop.

    python -m synw.analysis.phase_l --campaign runs/l2 [--pilot] [--baseline results/m4/contrasts.csv]
"""

import argparse
import csv
import json
import math
import os
import shutil
import sys

from ..events import read_log
from ..metrics import Run
from . import compare as K
from .grid import row

PRIMARY = ("P1", "P2", "P3", "P4")
CONTRASTS = (("B", "A"), ("B", "C"))
SECONDARY = (("A", "C"), ("A+text", "A"), ("B", "A+text"))
Z_PLAN = 12.8            # (z(1 − 0.05/16) + z(0.80))², 06 §7.4
MIN_SEEDS = 12           # decision 8


def load_campaign(cdir):
    """Rows for every completed run in ``cdir`` (P4 from the ``none`` twin when present)."""
    with open(os.path.join(cdir, "runs.csv"), encoding="utf-8") as fh:
        listed = list(csv.DictReader(fh))
    ok = {(r["world"], r["arm"], int(r["seed"])): os.path.join(cdir, r["log"])
          for r in listed if r["status"].startswith("ok")}
    runs = {}
    for key, path in ok.items():
        header, events, footer = read_log(path)
        runs[key] = (Run(header, events), footer)
    rows = []
    for (world, arm, seed), (r, footer) in sorted(runs.items()):
        twin = runs.get((world, "none", seed))
        twin_run = r if arm == "none" else (twin[0] if twin else None)
        rows.append(row(r, twin_run, arm, seed, None, footer["state_hash"]))
    return rows, listed


def sd(xs):
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pilot(rows, arm="full", sesoi=None):
    """Seeds per world asked by each primary test (06 §7.4), from the pilot's σ_d."""
    sesoi = dict(K.SESOI, **(sesoi or {}))
    table = [r for r in rows if r["arm"] == arm]
    out = []
    for t, c in CONTRASTS:
        for y in PRIMARY:
            d = [x for _, x in K.paired_differences(table, t, c, y)]
            s = sd(d)
            n = None if s is None else max(MIN_SEEDS, math.ceil(Z_PLAN * (s / sesoi[y]) ** 2))
            out.append({"contrast": f"{t} vs {c}", "outcome": y, "pairs": len(d), "sd_d": s,
                        "sesoi": sesoi[y], "seeds_per_world": n})
    return out


def baseline(path):
    """{(contrast, outcome): (estimate, lo, hi, n)} for the primary `full` contrasts in M4."""
    out = {}
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("family") == "primary" and r.get("arm") == "full":
                out[(r["contrast"], r["outcome"])] = (float(r["estimate"]), float(r["lo"]), float(r["hi"]),
                                                      int(r["n"]))
    return out


def departure(model_row, base):
    """Model estimate minus mechanical estimate, with an approximate 95% interval.

    The two estimates come from independent runs, so their standard errors add in
    quadrature; each s.e. is read back from its t-interval. Approximate, and labelled so.
    """
    if base is None or model_row["estimate"] is None or model_row["ci"][0] is None:
        return None
    b_est, b_lo, b_hi, b_n = base
    m_lo, m_hi = model_row["ci"]
    se_m = (m_hi - m_lo) / (2 * K.t_quantile(0.975, model_row["n"] - 1))
    se_b = (b_hi - b_lo) / (2 * K.t_quantile(0.975, b_n - 1))
    se = math.sqrt(se_m ** 2 + se_b ** 2)
    d = model_row["estimate"] - b_est
    return {"mechanical": b_est, "departure": d, "lo": d - 1.96 * se, "hi": d + 1.96 * se}


def dropped_seeds(rows, arm="full"):
    """For each contrast, seeds present in one world but missing in the other (06 §7.5)."""
    have = {}
    for r in rows:
        if r["arm"] == arm:
            have.setdefault(r["world"], set()).add(r["seed"])
    out = {}
    for t, c in CONTRASTS + SECONDARY:
        if t in have and c in have:
            out[f"{t} vs {c}"] = sorted(have[t] ^ have[c])
    return out


def descriptive(rows, pairs, outcomes, arm="full"):
    table = [r for r in rows if r["arm"] == arm]
    worlds = {r["world"] for r in table}
    out = []
    for t, c in pairs:
        if t not in worlds or c not in worlds:
            continue
        for y in outcomes:
            d = [x for _, x in K.paired_differences(table, t, c, y)]
            if d:
                out.append({"contrast": f"{t} vs {c}", "outcome": y, "n": len(d), "estimate": K.mean(d),
                            "ci": K.t_interval(d)})
    return out


def svg_strips(rows, arm="full", sesoi=None):
    """A small self-contained SVG: one strip of seed-level d per primary test."""
    sesoi = dict(K.SESOI, **(sesoi or {}))
    table = [r for r in rows if r["arm"] == arm]
    tests = [(t, c, y) for t, c in CONTRASTS for y in PRIMARY]
    W, H, pad, lab = 640, 34, 10, 150
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H * len(tests) + 30}" '
           'font-family="sans-serif" font-size="11">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="10" y="16">Seed-level paired differences d_s (dots), zero (line), ±SESOI (band)</text>']
    for k, (t, c, y) in enumerate(tests):
        d = [x for _, x in K.paired_differences(table, t, c, y)]
        y0 = 30 + k * H
        span = max([abs(x) for x in d] + [sesoi[y] * 2]) or 1.0
        sx = lambda v: lab + (W - lab - pad) * (v + span) / (2 * span)
        out.append(f'<text x="10" y="{y0 + 18}">{t} vs {c}, {y} (n={len(d)})</text>')
        out.append(f'<rect x="{sx(-sesoi[y]):.1f}" y="{y0 + 4}" width="{sx(sesoi[y]) - sx(-sesoi[y]):.1f}" '
                   f'height="{H - 8}" fill="#e8eef7"/>')
        out.append(f'<line x1="{sx(0):.1f}" x2="{sx(0):.1f}" y1="{y0 + 2}" y2="{y0 + H - 2}" stroke="#555"/>')
        for x in d:
            out.append(f'<circle cx="{sx(x):.1f}" cy="{y0 + H / 2:.1f}" r="3" fill="#1f4e99" fill-opacity="0.7"/>')
    out.append("</svg>")
    return "\n".join(out)


def _fmt(v, y):
    if v is None:
        return "NA"
    return f"{v * 100:+.2f} pts" if y in ("P1", "P3", "P4") else f"{v:+.4f}"


def report(rows, base_path=None, arm="full", label="Phase L"):
    table = [r for r in rows if r["arm"] == arm]
    prim = K.analyse(table)
    base = baseline(base_path)
    lines = [f"# {label} report", "",
             f"`{arm}` arm. Paired by seed; 95% t-intervals; two-sided sign-flip tests; Holm across the "
             "8 primary tests (06 §7.2).", "",
             "## Primary tests", "",
             "| Contrast | Outcome | n | Estimate | 95% CI | p (Holm) | Verdict | Mechanical (M4) | Departure [approx. 95% CI] |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in prim:
        dep = departure(r, base.get((r["contrast"], r["outcome"])))
        ci = "NA" if r["ci"][0] is None else f"[{_fmt(r['ci'][0], r['outcome'])}, {_fmt(r['ci'][1], r['outcome'])}]"
        dtxt = ("NA", "NA") if dep is None else (_fmt(dep["mechanical"], r["outcome"]),
                                                  f"{_fmt(dep['departure'], r['outcome'])} "
                                                  f"[{_fmt(dep['lo'], r['outcome'])}, {_fmt(dep['hi'], r['outcome'])}]")
        lines.append(f"| {r['contrast']} | {r['outcome']} | {r['n']} | {_fmt(r['estimate'], r['outcome'])} | {ci} | "
                     f"{r['p_holm']:.4f} | {r['verdict']} | {dtxt[0]} | {dtxt[1]} |")
    lines += ["", "The departure is the model estimate minus the null-mock estimate for the same contrast "
              "(06 §9: phase L reports departures from the mechanical baseline). Its interval is "
              "approximate: independent standard errors added in quadrature.", "",
              "## Secondary contrasts (estimates only, no test)", "",
              "| Contrast | Outcome | n | Estimate | 95% CI |", "|---|---|---|---|---|"]
    for r in descriptive(rows, SECONDARY, PRIMARY + ("S2", "S6"), arm):
        lo, hi = r["ci"]
        y = r["outcome"]
        ci = "NA" if lo is None else f"[{_fmt(lo, y)}, {_fmt(hi, y)}]"
        lines.append(f"| {r['contrast']} | {y} | {r['n']} | {_fmt(r['estimate'], y)} | {ci} |")
    lines += ["", "## H2: equality without collapse (S2, total output)", ""]
    s2 = {}
    for r in table:
        if r["S2"] is not None:
            s2.setdefault(r["world"], []).append(r["S2"])
    for t, c in CONTRASTS:
        if t in s2 and c in s2:
            ratio = (sum(s2[t]) / len(s2[t])) / (sum(s2[c]) / len(s2[c]))
            lines.append(f"- {t} / {c} mean output: {ratio:.3f} (H2 needs ≥ 0.90)")
    lines += ["", "## H5: capture (S6, exploratory)", ""]
    for wname in sorted({r["world"] for r in table}):
        v = [r["S6"] for r in table if r["world"] == wname and r["S6"] is not None]
        if v:
            lines.append(f"- {wname}: mean S6 {sum(v) / len(v):+.3f} over {len(v)} runs")
    dropped = {k: v for k, v in dropped_seeds(rows, arm).items() if v}
    lines += ["", "## Runs", "", "Every planned run, including failures, is in `runs.csv`.",
              "Seeds dropped from a contrast because a run is missing (06 §7.5): "
              + (", ".join(f"{k}: {v}" for k, v in dropped.items()) if dropped else "none") + ".",
              "", "Seed-level distributions: `seeds.svg`."]
    return "\n".join(lines) + "\n", prim


def pilot_report(p):
    lines = ["# Pilot (step L1): seeds per world from σ_d (06 §7.4)", "",
             "`n = max(12, ceil(12.8 × (σ_d / SESOI)²))`. Each σ_d rests on the listed number of paired "
             "differences; with the L1 pilot's 2 seeds per world that is 1 degree of freedom, so treat "
             "those values as rough.", "",
             "| Contrast | Outcome | Pairs | σ_d | SESOI | Seeds per world |", "|---|---|---|---|---|---|"]
    for r in p:
        sd_txt = "NA" if r["sd_d"] is None else f"{r['sd_d']:.4f}"
        lines.append(f"| {r['contrast']} | {r['outcome']} | {r['pairs']} | {sd_txt} | {r['sesoi']} | "
                     f"{r['seeds_per_world'] if r['seeds_per_world'] else 'NA'} |")
    need = [r["seeds_per_world"] for r in p if r["seeds_per_world"]]
    if need:
        lines += ["", f"Largest: **{max(need)} seeds per world**. Decision 8: if the budget cannot reach it, "
                  "raise that outcome's SESOI in writing before running, or report it as descriptive."]
    return "\n".join(lines) + "\n"


def mock_campaign(out, worlds=("A", "B", "C"), seeds=range(1, 21), arms=("full", "none"), root="."):
    """A campaign directory filled with null-mock runs: phase M data in phase L form,
    for testing this analysis before any model run (06 §8.3)."""
    from ..runner import run
    from .campaign import FIELDS, WORLDS, log_name
    os.makedirs(out, exist_ok=True)
    listed = []
    for wname in worlds:
        for seed in seeds:
            for arm in arms:
                w = run(os.path.join(root, WORLDS[wname]), seed, out=out, arm=arm, keep_events=False)
                name = log_name(wname, arm, seed)
                os.replace(w.log_path, os.path.join(out, name))
                listed.append(dict(world=wname, arm=arm, seed=seed, ticks=w.clock.ticks, status="ok", attempts=1,
                                   input_tokens=0, output_tokens=0, usd=0.0, log=name, note="null mock"))
    with open(os.path.join(out, "runs.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(listed)
    return listed


def main(argv=None):
    ap = argparse.ArgumentParser(description="Phase L analysis (06 §7, §8.3)")
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", help="default: the campaign directory")
    ap.add_argument("--pilot", action="store_true", help="also write pilot.md (step L1)")
    ap.add_argument("--baseline", default="results/m4/contrasts.csv")
    ap.add_argument("--label", default="Phase L")
    a = ap.parse_args(argv)
    out = a.out or a.campaign
    os.makedirs(out, exist_ok=True)
    rows, _listed = load_campaign(a.campaign)
    with open(os.path.join(out, "rows.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    if a.pilot:
        with open(os.path.join(out, "pilot.md"), "w", encoding="utf-8") as fh:
            fh.write(pilot_report(pilot(rows)))
    text, _ = report(rows, a.baseline, label=a.label)
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(os.path.join(out, "seeds.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg_strips(rows))
    if os.path.abspath(out) != os.path.abspath(a.campaign):
        shutil.copy(os.path.join(a.campaign, "runs.csv"), os.path.join(out, "runs.csv"))
    print(f"wrote {out}/report.md" + (" and pilot.md" if a.pilot else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
