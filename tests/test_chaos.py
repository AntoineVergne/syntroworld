"""Stress test: a hostile offline 'model' (synw/brains/chaos.py). No model is called."""
from collections import Counter

import pytest

from synw.brains.chaos import ChaosTransport
from synw.brains.model import ReplayTransport
from synw.config import load
from synw.runner import World, run

from conftest import wpath


def chaos_world(world, seed, ticks, bad=0.3):
    tr = ChaosTransport(seed, bad_share=bad)
    w = World(load(wpath(world)), seed, arm="full", brain={"type": "model", "transport": tr,
                                                            "budget_tokens": 10**12})
    tr.world = w
    w.run(ticks)
    return w


@pytest.mark.parametrize("world,ticks", [("a.yaml", 160), ("b.yaml", 160), ("c.yaml", 100),
                                         ("size40/b.yaml", 60)])
def test_engine_survives_bad_replies(world, ticks):
    w = chaos_world(world, 1, ticks)
    c = Counter(e["type"] for e in w.log.events)
    assert w.log.footer["status"] == "partial"
    assert c["invalid_action"] + c["invalid_output"] > 0      # junk was logged (S15)
    assert c["model_call"] > 0


def test_random_only_replies_do_not_crash():
    w = run(wpath("b.yaml"), 3, arm="full", ticks=100,
            brain={"type": "model", "transport": ChaosTransport(3, bad_share=0.5), "budget_tokens": 10**12})
    assert w.log.footer["status"] == "partial"


def test_a_chaos_run_replays_exactly():
    a = chaos_world("b.yaml", 2, 120)
    b = run(wpath("b.yaml"), 2, arm="full", ticks=120,
            brain={"type": "model", "transport": ReplayTransport(a.log.events), "budget_tokens": 10**12})
    strip = lambda evs: [(e["tick"], e["type"], e["actor"], e["payload"]) for e in evs]
    assert strip(a.log.events) == strip(b.log.events)
    assert a.log.footer["state_hash"] == b.log.footer["state_hash"]
