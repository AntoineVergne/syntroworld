import os

import pytest

from synw.brains.base import REST, Action, Brain
from synw.config import load
from synw.runner import World

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wpath(name):
    return os.path.join(ROOT, "worlds", name)


class StubBrain(Brain):
    """A predictable brain for governance tests: attends every sitting it is due at."""

    def __init__(self, attend=True, vote="yes", value=1000, amendment=None, accept=True,
                 absent_ticks=()):
        self.attend = attend
        self.vote = vote
        self.value = value
        self.amendment = amendment
        self.accept = accept
        self.absent_ticks = set(absent_ticks)

    def act(self, obs):
        if obs.incapacitated or obs.in_transit:
            return REST
        if self.attend and obs.tick not in self.absent_ticks:
            for d in obs.duties:
                if d["start"] - 2 <= obs.tick <= d["end"]:
                    if obs.location != "assembly_hall":
                        return Action("move", {"to": "assembly_hall"})
                    return Action("civic", {"kind": "attend"})
        if obs.tick in self.absent_ticks and obs.location == "assembly_hall":
            return Action("move", {"to": "square"})
        return REST

    def respond_draw(self, obs, draw):
        return {"accept": self.accept, "reason": "accept" if self.accept else "busy"}

    def propose(self, obs):
        return None

    def evaluate(self, obs, proposal):
        return self.value

    def speak(self, obs, deliberation):
        return {"stance": max(-1000, min(1000, self.value)), "objection": "none",
                "amendment": self.amendment}

    def ballot(self, obs, proposal):
        return {"vote": self.vote, "reason": "none"}


@pytest.fixture
def make_world():
    def make(name="a.yaml", seed=1, arm="none", lam=None, cfg_patch=None, log_path=None):
        cfg = load(wpath(name))
        if cfg_patch:
            cfg_patch(cfg)
        w = World(cfg, seed, arm=arm, lam=lam, log_path=log_path)
        w.tick = 1
        w.time = w.clock.at(1)
        return w
    return make


def stub_all(w, **kw):
    for i in w.brains:
        w.brains[i] = StubBrain(**kw)


def run_until(w, tick):
    """Step the world through ``tick`` (continuing from the last stepped tick)."""
    start = getattr(w, "_last_step", 0) + 1
    for t in range(start, tick + 1):
        w.step(t)
    w._last_step = max(tick, start - 1)
