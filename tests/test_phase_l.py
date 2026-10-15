"""Phase L analysis (06 §7, §8.3) on a small null-mock campaign."""
import csv
import os

import pytest

from synw.analysis import phase_l as L
from synw.analysis.grid import outcomes

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def camp(tmp_path_factory):
    d = tmp_path_factory.mktemp("camp")
    L.mock_campaign(str(d), seeds=range(1, 4), root=HERE)
    return str(d)


def test_rows_match_phase_m(camp):
    rows, listed = L.load_campaign(camp)
    assert len(rows) == 18 and len(listed) == 18
    r = next(x for x in rows if (x["world"], x["arm"], x["seed"]) == ("B", "full", 2))
    m = outcomes(os.path.join(HERE, "worlds/b.yaml"), 2, arm="full")
    for k in ("P1", "P2", "P3", "P4", "S2", "S6", "state_hash"):
        assert r[k] == m[k]


def test_report_and_departures(camp):
    rows, _ = L.load_campaign(camp)
    text, prim = L.report(rows, os.path.join(HERE, "results/m4/contrasts.csv"))
    assert len(prim) == 8 and text.count("| B vs ") >= 8
    base = L.baseline(os.path.join(HERE, "results/m4/contrasts.csv"))
    dep = L.departure(prim[0], base[(prim[0]["contrast"], prim[0]["outcome"])])
    assert dep["lo"] <= dep["departure"] <= dep["hi"]
    assert "<svg" in L.svg_strips(rows)


def test_pilot_asks_at_least_twelve(camp):
    rows, _ = L.load_campaign(camp)
    p = L.pilot(rows)
    assert len(p) == 8 and all(r["seeds_per_world"] >= 12 for r in p)


def test_missing_run_drops_the_seed(camp, tmp_path):
    import shutil
    d = tmp_path / "c"
    shutil.copytree(camp, d)
    with open(d / "runs.csv") as fh:
        listed = list(csv.DictReader(fh))
    for r in listed:
        if (r["world"], r["arm"], r["seed"]) == ("A", "full", "3"):
            r["status"] = "missing"
    with open(d / "runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(listed[0]))
        w.writeheader()
        w.writerows(listed)
    rows, _ = L.load_campaign(str(d))
    assert L.dropped_seeds(rows)["B vs A"] == [3]
    _, prim = L.report(rows)
    assert {r["n"] for r in prim if r["contrast"] == "B vs A"} == {2}
