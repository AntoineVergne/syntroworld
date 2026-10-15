"""Do citizens behave like their personas? (04 §1 rule 3, checked in the L1 pilot.)

A model brain reads only the persona text; the mock brain reads only the numbers (04 §4).
For each trait with a clean behavioural trace, this ranks citizens by the persona number
and by what they did, and reports Spearman's rank correlation, per run and averaged.
The null mock is the reference: it *is* the numbers, so its correlations show how much
of a trait the measure can recover at all. A model run should show the same sign.

| Trait | Behaviour measured (per day present) |
|---|---|
| work_drive | work, harvest and wage ticks |
| honesty | harmful acts (theft, sabotage, false claims, defaults), sign reversed |
| civic | civic acts (P3's acts plus every attended sitting) |
| credulity | planted or false claims adopted as beliefs |
| greed | share of production ticks spent fishing (confounded with the River workers' niche) |

Runs on the `full` arm, days 1 to 18 only: the misinformation shock (day 13) gives
credulity something to act on, and the rogue overlay (day 19) has not yet changed anyone's
numbers.

    python -m synw.analysis.persona_check --campaign runs/l1 [--mock-seeds 1-20]
"""

import argparse
import os
import sys

from ..config import load_personas
from ..metrics import Run
from ..metrics.secondary import spearman
from ..runner import run as run_world
from .calibrate import parse_seeds

TRAITS = ("work_drive", "honesty", "civic", "credulity", "greed")
SIGN = {"honesty": -1}       # more honest → fewer harmful acts


LAST_DAY = 18


def behaviour(r, last_day=LAST_DAY):
    """{citizen: {trait: value}} from one run's events, days 1 to ``last_day``."""
    last_tick = last_day * r.ticks_per_day
    days = {}
    for e in r.of("day_end"):
        if e["tick"] > last_tick:
            continue
        for k in e["payload"]["holdings"]:
            days[int(k)] = days.get(int(k), 0) + 1
    out = {c: {"work": 0, "fish": 0, "harm": 0, "civic": 0, "credulous": 0} for c in days}

    def bump(c, k, by=1):
        if isinstance(c, int) and c in out:
            out[c][k] += by
    for e in r.events:
        if e["tick"] > last_tick:
            break
        t, a = e["type"], e["actor"]
        if t in ("produce", "wage"):
            bump(a, "work")
        elif t == "harvest":
            bump(a, "work")
            bump(a, "fish")
        elif t == "harmful_act":
            bump(a, "harm")
        elif t in ("attend", "observe") and e["payload"].get("bodies"):
            bump(a, "civic")
        elif t in ("proposal_registered", "alert"):
            bump(a, "civic")
        elif t == "belief" and e["payload"].get("adopted") and e["payload"].get("planted"):
            bump(a, "credulous")
    res = {}
    for c, v in out.items():
        d = max(days[c], 1)
        res[c] = {"work_drive": v["work"] / d, "honesty": v["harm"] / d, "civic": v["civic"] / d,
                  "credulity": v["credulous"] / d, "greed": v["fish"] / v["work"] if v["work"] else 0.0}
    return res


def correlations(r, personas):
    beh = behaviour(r)
    num = {p["index"]: p for p in personas}
    cs = sorted(c for c in beh if c in num)
    out = {}
    for trait in TRAITS:
        xs = [num[c][trait] for c in cs]
        ys = [SIGN.get(trait, 1) * beh[c][trait] for c in cs]
        out[trait] = spearman(xs, ys) if len(set(ys)) > 1 else None
    return out


def summarise(per_run):
    out = {}
    for trait in TRAITS:
        v = [x[trait] for x in per_run if x.get(trait) is not None]
        out[trait] = {"runs": len(v), "mean": sum(v) / len(v) if v else None,
                      "positive": sum(1 for x in v if x > 0) / len(v) if v else None}
    return out


def mock_reference(worlds=("worlds/a.yaml", "worlds/b.yaml", "worlds/c.yaml"), seeds=range(1, 6)):
    per = []
    for wp in worlds:
        for s in seeds:
            w = run_world(wp, s, arm="full")
            per.append(correlations(Run(w.log.header, w.log.events), w.personas["citizens"]))
    return summarise(per)


def campaign_runs(cdir, root="."):
    import csv
    from ..config import load
    from ..events import read_log
    from .campaign import WORLDS
    with open(os.path.join(cdir, "runs.csv"), encoding="utf-8") as fh:
        listed = [r for r in csv.DictReader(fh) if r["status"].startswith("ok") and r["arm"] == "full"]
    per = []
    for r in listed:
        header, events, _ = read_log(os.path.join(cdir, r["log"]))
        personas = load_personas(load(os.path.join(root, WORLDS[r["world"]])))["citizens"]
        per.append(correlations(Run(header, events), personas))
    return summarise(per)


def table(model, mock):
    lines = ["| Trait | Null mock: mean ρ (share > 0) | Model: mean ρ (share > 0) |", "|---|---|---|"]
    f = lambda s: "NA" if s["mean"] is None else f"{s['mean']:+.2f} ({s['positive']:.0%} of {s['runs']})"
    for t in TRAITS:
        lines.append(f"| {t} | {f(mock[t])} | {f(model[t]) if model else 'no model runs'} |")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Persona check (04 §1 rule 3)")
    ap.add_argument("--campaign", help="a model campaign directory (uses its `full` runs)")
    ap.add_argument("--mock-seeds", default="1-5")
    a = ap.parse_args(argv)
    mock = mock_reference(seeds=parse_seeds(a.mock_seeds))
    model = campaign_runs(a.campaign) if a.campaign else None
    print(table(model, mock))
    return 0


if __name__ == "__main__":
    sys.exit(main())
