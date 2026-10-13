import os
import random

import pytest

pytest.importorskip("numpy")

from synw.analysis import baseline as BL  # noqa: E402
from synw.analysis.grid import write_rows  # noqa: E402


def _fake(out, seeds=6):
    rng = random.Random(1)
    for world, _path, arm, _n in BL.cells(seeds, 3):
        n = seeds if not world.endswith("40") else 3
        rows = []
        for s in range(1, n + 1):
            shift = 0.02 if world.startswith("B") else 0.0
            r = {"world": world, "arm": arm, "seed": s,
                 "P1": 0.9 + shift + rng.gauss(0, 0.005), "P2": 0.25 - shift + rng.gauss(0, 0.01),
                 "P3": 0.6 + rng.gauss(0, 0.02), "S2": 3_000_000 * (0.95 if arm != "none" else 1.0)}
            for y in BL.SECONDARY:
                r.setdefault(y, 0.5)
            rows.append(r)
        write_rows(rows, BL.cell_file(out, world, arm))


def test_p4_from_the_none_cell(tmp_path):
    _fake(str(tmp_path))
    data = BL.load(str(tmp_path), 6, 3)
    assert data[("A", "none")][1]["P4"] == 0.0
    assert data[("B", "full")][2]["P4"] == pytest.approx(0.05)
    assert data[("C", "drought")][3]["P4"] == pytest.approx(0.05)


def test_report(tmp_path):
    out = str(tmp_path)
    _fake(out)
    data = BL.load(out, 6, 3)
    rows = BL.contrasts(data, n_flips=2000)
    prim = [r for r in rows if r["family"] == "primary"]
    assert len(prim) == 8 and all("verdict" in r for r in prim)
    p1 = [r for r in prim if r["contrast"] == "B vs A" and r["outcome"] == "P1"][0]
    assert p1["estimate"] == pytest.approx(0.02, abs=0.01)
    lines = BL.write_report(out, data, rows, BL.summary(data))
    text = "\n".join(lines)
    assert BL.LABEL in text and "Population-size check" in text and "Ablations" in text
    for f in ("report.md", "summary.csv", "contrasts.csv"):
        assert os.path.exists(os.path.join(out, f))


def test_cells_cover_the_protocol():
    c = {(w, a): n for w, _p, a, n in BL.cells()}
    for w in ("A", "B", "C", "B-nolot", "B-noadv", "B-nodiv", "B-nopay"):
        assert c[(w, "none")] == 200 and c[(w, "full")] == 200
    for w in ("A", "B", "C"):
        for a in ("drought", "misinfo", "rogue"):
            assert c[(w, a)] == 200
    for w in ("A40", "B40", "C40"):
        assert c[(w, "none")] == 50 and c[(w, "full")] == 50
