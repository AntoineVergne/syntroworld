from synw.metrics import Run
from synw.metrics.legitimacy import s4_founding_compliance
from synw.runner import run
from synw.world import agents as A

from conftest import START, wpath


def detection(p):
    def patch(cfg):
        cfg["theft"]["detection"] = p
    return patch


def _pair(w):
    thief, target = w.citizens[5], w.citizens[0]
    thief.location = target.location = "square"
    return thief, target


def test_detected_theft_is_reversed(make_world):
    w = make_world(cfg_patch=detection(1000))
    thief, target = _pair(w)
    target.credits = 60000
    amount, detected = A.steal(w, thief, target)
    assert amount == 10000 and detected     # min(20% of 60, cap 10)
    assert thief.credits == START and target.credits == 60000
    types = [e["type"] for e in w.log.events]
    assert "theft" in types and "breach" in types and "restitution" in types and "detected" in types


def test_undetected_theft_stands(make_world):
    w = make_world(cfg_patch=detection(0))
    thief, target = _pair(w)
    target.credits = 20000
    amount, detected = A.steal(w, thief, target)
    assert amount == 4000 and not detected
    assert thief.credits == START + 4000 and target.credits == 16000
    breach = [e for e in w.log.events if e["type"] == "breach"]
    assert breach and breach[0]["payload"]["rule"] == "R0-steal" and breach[0]["payload"]["detected"] == 0


def test_every_steal_produces_a_breach_event():
    w = run(wpath("a.yaml"), 1)
    thefts = [e for e in w.log.events if e["type"] == "theft"]
    breaches = [e for e in w.log.events if e["type"] == "breach" and e["payload"]["act"] == "steal"]
    assert thefts
    assert len(breaches) == len(thefts)
    assert {(e["tick"], e["actor"]) for e in thefts} == {(e["tick"], e["actor"]) for e in breaches}


def test_founding_ban_from_tick_one_in_every_world():
    for world in ("a.yaml", "b.yaml", "c.yaml"):
        w = run(wpath(world), 2)
        founding = [e for e in w.log.events if e["type"] == "rule_in_force" and e["payload"]["source"] == "founding"]
        assert {e["payload"]["id"] for e in founding} == {"R0-steal", "R0-sabotage"}
        assert all(e["payload"]["since"] == 1 for e in founding)
        exp = [e for e in w.log.events if e["type"] == "exposure" and e["payload"]["rule"] == "R0-steal"]
        assert exp and exp[0]["payload"]["day"] == 1
        assert s4_founding_compliance(Run(w.log.header, w.log.events)) is not None


def test_null_mock_lambda_zero():
    w = run(wpath("a.yaml"), 1)
    assert w.lam == 0 and all(b.lam == 0 for b in w.brains.values())
