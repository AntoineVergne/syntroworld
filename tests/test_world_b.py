from collections import defaultdict

from synw.events import log_hash
from synw.runner import run

from conftest import wpath


def test_world_b_one_seed(tmp_path):
    w = run(wpath("b.yaml"), 1, out=str(tmp_path / "x"))
    ev = w.log.events
    draws = defaultdict(dict)
    for e in ev:
        if e["type"] == "lottery":
            draws[w.clock.at(e["tick"]).cycle][e["payload"]["body"]] = e["payload"]["members"]
    assert sorted(draws) == list(range(1, 9))
    full = 0
    for cyc, bodies in draws.items():
        ca, rb = bodies["cycle_assembly"], bodies["review_bench"]
        assert not set(ca) & set(rb)                          # nobody sits on both
        assert len(ca) <= 5 and len(rb) <= 3
        full += len(set(ca) | set(rb)) == 8
    assert full >= 1                                          # 8 distinct members
    divs = [e["payload"] for e in ev if e["type"] == "dividend"]
    assert divs and all(d["per_citizen"] <= d["cap"] for d in divs)
    assert any(e["type"] == "treasury_out" and e["payload"]["kind"] == "stipend" for e in ev)
    assert any(e["type"] == "agenda_lottery" for e in ev)
    w2 = run(wpath("b.yaml"), 1, out=str(tmp_path / "y"))
    assert log_hash(w.log_path) == log_hash(w2.log_path)


def test_recent_service_halves_weight():
    w = run(wpath("b.yaml"), 2)
    lots = [e for e in w.log.events if e["type"] == "lottery" and e["payload"]["body"] == "cycle_assembly"]
    prev = set(lots[0]["payload"]["members"])
    weights = lots[1]["payload"]["weights"]
    for k, v in weights.items():
        assert v == (500 if int(k) in prev else 1000)


def test_sam_eligible_after_a_full_cycle():
    w = run(wpath("b.yaml"), 3)
    lots = [e for e in w.log.events if e["type"] == "lottery"]
    for e in lots:
        cyc = w.clock.at(e["tick"]).cycle
        if cyc <= 2:
            assert 10 not in e["payload"]["pool"]
    assert any(10 in e["payload"]["pool"] for e in lots if w.clock.at(e["tick"]).cycle >= 3)


def test_concentration_trigger_fires_on_gini_and_logs_integers(make_world):
    """01 Art. 5.4: richest > 30% or Gini > 0.40 puts a mandatory item on the next sitting.
    (The Gini was once compared on the wrong scale, so that half of the trigger never fired.)"""
    w = make_world("b.yaml")
    for i, c in w.citizens.items():
        c.inv = {g: 0 for g in c.inv}
        c.credits = 0 if i < 6 else 25000          # Gini 0.60, richest holds 25%
    w.governance._concentration_item()
    ev = [e for e in w.log.events if e["type"] == "concentration_trigger"]
    assert ev and isinstance(ev[0]["payload"]["gini"], int) and ev[0]["payload"]["gini"] > 400
    assert ev[0]["payload"]["top_share"] <= 300
    assert any(p["mandatory"] and p["effect"]["type"] == "set_tax" for p in w.governance.register)
