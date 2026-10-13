import collections
import os

import pytest

from synw import config
from synw.events import log_hash
from synw.runner import run

from conftest import wpath

ABL = ("ablations/b-nolot.yaml", "ablations/b-noadv.yaml", "ablations/b-nodiv.yaml", "ablations/b-nopay.yaml")


def _flat(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(_flat(v, f"{prefix}{i}."))
    else:
        out[prefix.rstrip(".")] = d
    return out


def _resolved(name):
    cfg = config.load(wpath(name))
    out = config.public(cfg)
    out["governance"] = dict(out["governance"], blocks=[
        os.path.normpath(config.resolve_path(cfg, b)) for b in cfg["governance"]["blocks"]])
    return _flat(out)


def _diff(name):
    b, x = _resolved("b.yaml"), _resolved(name)
    return {k for k in set(b) | set(x) if b.get(k) != x.get(k)} - {"world", "description", "personas"}


def _sections(name):
    return {".".join(k.split(".")[:2]) for k in _diff(name)}


def test_ablation_configs_change_only_their_mechanism():
    assert _sections("ablations/b-noadv.yaml") == {"governance.advocates"}
    assert _sections("ablations/b-nodiv.yaml") == {"governance.founding_rules", "governance.allow_dividend"}
    assert _sections("ablations/b-nopay.yaml") == {"governance.founding_rules", "governance.allow_stipend"}
    assert _sections("ablations/b-nolot.yaml") == {"governance.blocks", "governance.bodies"}
    assert {k for k in _diff("ablations/b-nolot.yaml") if k.startswith("governance.blocks")} == \
        {f"governance.blocks.{i}" for i in range(3)}     # review bench and kill switch kept
    for name in ABL:
        assert config.load(wpath(name))["personas"] == "../personas.yaml"


def _events(name, seed=2):
    w = run(wpath(name), seed, arm="full")
    return w, w.log.events


def test_nolot_replaces_the_cycle_assembly_with_a_deliberating_plenary():
    w, ev = _events("ablations/b-nolot.yaml")
    assert {e["payload"]["body"] for e in ev if e["type"] == "lottery"} == {"review_bench"}
    sittings = collections.Counter(e["actor"] for e in ev if e["type"] == "sitting_opened")
    assert sittings["plenary"] == 8 and "cycle_assembly" not in sittings
    plenary_items = {i for e in ev if e["type"] == "sitting_opened" and e["actor"] == "plenary"
                     for i in e["payload"]["items"]}
    assert any(e["type"] == "speech" and e["payload"]["proposal"] in plenary_items for e in ev)
    assert any(e["type"] == "advocate_brief" for e in ev)


def test_nolot_plenary_needs_presence_at_every_deliberation_tick(make_world):
    from conftest import run_until, stub_all
    w = make_world("ablations/b-nolot.yaml")
    stub_all(w)
    w.brains[3].absent_ticks = {w.clock.tick_in_cycle(1, 2, 10)}
    run_until(w, 1)
    w.governance.register_proposal(0, {"type": "set_tax", "base": "harvest", "rate": 100})
    run_until(w, w.clock.tick_in_cycle(1, 2, 16))
    voters = {e["actor"] for e in w.log.events if e["type"] == "ballot"}
    assert 3 not in voters and len(voters) == 9


def test_noadv_has_no_hearing():
    _, ev = _events("ablations/b-noadv.yaml")
    assert not any(e["type"] in ("advocate_brief", "objection") for e in ev)


def test_nodiv_has_no_dividend_and_none_can_be_adopted(make_world):
    _, ev = _events("ablations/b-nodiv.yaml")
    assert not any(e["type"] in ("dividend", "dividend_shortfall") for e in ev)
    assert not any(e["type"] == "proposal_registered" and e["payload"]["effect"].get("type") == "set_dividend"
                   for e in ev)                      # the mock does not propose what is forbidden
    w = make_world("ablations/b-nodiv.yaml")
    assert w.governance.register_proposal(0, {"type": "set_dividend", "amount": 1000})["status"] == "rejected"
    assert any(e["type"] == "treasury_out" and e["payload"]["kind"] == "stipend" for e in ev)


def test_nopay_has_no_stipends(make_world):
    _, ev = _events("ablations/b-nopay.yaml")
    assert not any(e["type"] == "treasury_out" and e["payload"]["kind"] == "stipend" for e in ev)
    assert any(e["type"] == "dividend" for e in ev)
    w = make_world("ablations/b-nopay.yaml")
    assert w.governance.register_proposal(0, {"type": "set_stipend", "amount": 500})["status"] == "rejected"


@pytest.mark.parametrize("name", ABL)
def test_ablations_deterministic(tmp_path, name):
    a = run(wpath(name), 4, out=str(tmp_path / "1"), keep_events=False)
    b = run(wpath(name), 4, out=str(tmp_path / "2"), keep_events=False)
    assert log_hash(a.log_path) == log_hash(b.log_path)


def test_b_unchanged_by_ablation_support():
    """The null B run behind the M2 grid is byte-identical."""
    import json
    rows = {json.loads(l)["seed"]: json.loads(l) for l in open(wpath("../results/m2/grid-b-full-2000.jsonl"))}
    from synw.analysis.grid import outcomes
    assert outcomes(wpath("b.yaml"), 7, "full", 0)["state_hash"] == rows[7]["state_hash"]
