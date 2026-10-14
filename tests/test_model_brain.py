"""The model brain (03 §6.5) with offline transports only: no model is called."""
import json

import pytest

from synw.analysis import cost
from synw.brains import texts as T
from synw.brains.model import (LiteLLMTransport, ReplayMismatch, ReplayTransport, StubTransport,
                               integral, parse_json)
from synw.events import read_log
from synw.runner import ApprovalRequired, run

from conftest import wpath

REPLIES = {"act": '{"kind": "work", "args": {}}', "respond_draw": '{"accept": true, "reason": "accept"}',
           "propose": '{"proposal": null}', "evaluate": '{"value": 5}',
           "speak": '{"stance": 100, "objection": "none", "amendment": null}',
           "ballot": '{"vote": "yes", "reason": "public_gain"}'}


def stub(replies=REPLIES):
    return StubTransport(lambda agent, call, system, user: replies[call])


def model(transport, budget=10**9):
    return {"type": "model", "transport": transport, "budget_tokens": budget}


def test_one_cycle_logs_every_request_and_reply(tmp_path):
    w = run(wpath("b.yaml"), 1, out=str(tmp_path), brain=model(stub()), ticks=48)
    calls = [e for e in w.log.events if e["type"] == "model_call"]
    ctx = {e["payload"]["sha256"]: e["payload"]["text"] for e in w.log.events if e["type"] == "model_context"}
    assert len([c for c in calls if c["payload"]["call"] == "act"]) == 10 * 48     # founders, one cycle
    assert all(c["payload"]["context"] in ctx for c in calls)                      # every request is in the log
    assert w.log.footer["status"] == "partial" and w.log.footer["tokens"]["calls"] == len(calls)
    header, _, _ = read_log(w.log_path)
    assert header["brain"] == {"type": "model", "model": "stub", "budget_tokens": 10**9}


def test_replay_reproduces_the_log_exactly(tmp_path):
    a = run(wpath("b.yaml"), 2, out=str(tmp_path / "a"), brain=model(stub()), ticks=60)
    b = run(wpath("b.yaml"), 2, out=str(tmp_path / "b"), brain=model(ReplayTransport(a.log.events)), ticks=60)
    assert open(a.log_path).read() == open(b.log_path).read()


def test_replay_detects_a_different_request():
    a = run(wpath("b.yaml"), 2, brain=model(stub()), ticks=20)
    with pytest.raises(ReplayMismatch):
        run(wpath("a.yaml"), 2, brain=model(ReplayTransport(a.log.events)), ticks=20)


def test_budget_stops_the_run_cleanly():
    w = run(wpath("a.yaml"), 1, brain=model(stub(), budget=200000), ticks=48)
    assert w.log.footer["status"] == "failed" and w.log.footer["reason"] == "budget"


def test_live_transport_needs_approval():
    with pytest.raises(ApprovalRequired):
        run(wpath("a.yaml"), 1, brain=model(LiteLLMTransport("any")), ticks=1)


def test_unparseable_reply_is_an_invalid_action():
    bad = dict(REPLIES, act="I would like to fish today.")
    w = run(wpath("a.yaml"), 1, brain=model(stub(bad)), ticks=3)
    inv = [e for e in w.log.events if e["type"] == "invalid_action"]
    assert len(inv) == 30 and all(e["payload"]["reason"] == "unknown_action" for e in inv)


def test_world_texts_follow_02_9():
    from synw.config import load
    def titles(world):
        return [t for t, _ in T.world_texts(load(wpath(world)), [])]
    assert titles("a.yaml") == ["Shared preamble"]
    assert titles("b.yaml") == ["Shared preamble", "The Founding Compact (in force)"]
    assert titles("a-text.yaml") == ["Shared preamble", T.A_TEXT_LABEL]
    assert "Design notes" not in T.compact() and T.compact().startswith("# The Founding Compact")
    assert "We, the founding citizens of Kleros" in T.preamble()


def test_rogue_text_replaces_goals():
    t = T.persona_text(5, rogue=True)
    assert T.ROGUE_GOALS in t and "*Tension" in t and t.count("Goals:") == 1


def test_a_text_runs_like_a_under_the_mock():
    a = run(wpath("a.yaml"), 4, arm="full")
    t = run(wpath("a-text.yaml"), 4, arm="full")
    assert a.log.footer["state_hash"] == t.log.footer["state_hash"]


def test_parsing():
    assert parse_json('```json\n{"kind": "rest"}\n```') == {"kind": "rest"}
    assert parse_json('Sure: {"vote": "no"} done') == {"vote": "no"}
    assert parse_json("no json") is None
    assert integral({"qty": 3.0}) == {"qty": 3}
    with pytest.raises(ValueError):
        integral({"qty": 2.5})


def test_cost_formula_and_measurement(tmp_path):
    assert cost.estimate(2, 11, 384, 1000, 10, 1e-6, 2e-6) == pytest.approx(2 * 11 * 384 * (1e-3 + 2e-5))
    assert cost.step_plan("L1")[:2] == (12, 384)
    assert cost.step_plan("L2", seeds=50)[0] == 4 * 50 * 2
    rest = dict(REPLIES, act='{"kind": "rest", "args": {}}')
    w = run(wpath("b.yaml"), 1, out=str(tmp_path), brain=model(stub(rest)), ticks=48)
    m = cost.measure(w.log_path)
    assert m["agent_ticks"] == 480 and m["tokens_in"] > 1000 and m["invalid_rate"] == 0
    work = run(wpath("b.yaml"), 1, out=str(tmp_path / "w"), brain=model(stub()), ticks=48)
    assert cost.measure(work.log_path)["invalid_rate"] > 0.5     # "work" away from a work site
