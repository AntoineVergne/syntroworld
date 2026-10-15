"""Prompt review pack: exactly what a model citizen reads, before any model is called.

Runs a world with the mock brain and records, for one citizen, the first request of each
call type from day 7 on (act, respond_draw, propose, evaluate, speak, ballot). Each is
rendered with the model brain's own functions and written as plain text, with a size
estimate (4 characters per token; a tokenizer would differ by some tens of percent).

    python -m synw.analysis.prompts --out results/l0-prompts
"""

import argparse
import os
import sys

from ..brains.mock import MockBrain
from ..brains.model import render_system, render_user
from ..config import load
from ..runner import World

CALLS = ("act", "respond_draw", "propose", "evaluate", "speak", "ballot")
WORLDS = (("A", "worlds/a.yaml"), ("B", "worlds/b.yaml"), ("C", "worlds/c.yaml"),
          ("A+text", "worlds/a-text.yaml"))


class Recorder(MockBrain):
    """The mock brain, keeping the first request of each call from ``start_tick`` on."""

    def __init__(self, world, start_tick, *a, **kw):
        super().__init__(*a, **kw)
        self.world, self.start, self.seen = world, start_tick, {}

    def _keep(self, call, obs, extra=None):
        if obs.tick >= self.start and call not in self.seen:
            w = self.world
            blocks = [w.governance.blocks[b] for b in w.governance.order]
            c = w.citizens[obs.me]
            self.seen[call] = (obs.tick, render_system(w.cfg, blocks, obs.me, bool(c.rogue), name=c.persona.get("name")),
                               render_user(call, obs, extra))

    def act(self, obs):
        self._keep("act", obs)
        return super().act(obs)

    def respond_draw(self, obs, draw):
        self._keep("respond_draw", obs, draw)
        return super().respond_draw(obs, draw)

    def propose(self, obs):
        self._keep("propose", obs)
        return super().propose(obs)

    def evaluate(self, obs, proposal):
        self._keep("evaluate", obs, proposal)
        return super().evaluate(obs, proposal)

    def speak(self, obs, deliberation):
        self._keep("speak", obs, deliberation)
        return super().speak(obs, deliberation)

    def ballot(self, obs, proposal):
        self._keep("ballot", obs, proposal)
        return super().ballot(obs, proposal)


def collect(world_path, seed=1, arm="full", start_day=7):
    """{citizen: {call: (tick, system, user)}} for every citizen, from one mock run."""
    w = World(load(world_path), seed, arm=arm)
    start = (start_day - 1) * w.clock.ticks_per_day + 1
    for idx, c in w.citizens.items():
        old = w.brains[idx]
        w.brains[idx] = Recorder(w, start, c.persona, old.rng, w.lam, w.basket_cost)
    w.run()
    return {idx: b.seen for idx, b in w.brains.items()}


def pick(seen):
    """For each call, the first citizen (by index) who received it."""
    out = {}
    for call in CALLS:
        for idx in sorted(seen):
            if call in seen[idx]:
                out[call] = (idx,) + seen[idx][call]
                break
    return out


def write(out_dir, seed=1, arm="full"):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for name, path in WORLDS:
        chosen = pick(collect(path, seed, arm))
        wdir = os.path.join(out_dir, name.replace("+", "-plus-"))
        os.makedirs(wdir, exist_ok=True)
        for call in CALLS:
            if call not in chosen:
                rows.append((name, call, None, None, None, None))
                continue
            idx, tick, system, user = chosen[call]
            with open(os.path.join(wdir, f"{call}.txt"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(f"# World {name}, citizen {idx}, tick {tick} (seed {seed}, arm {arm})\n\n")
                fh.write("=" * 30 + " SYSTEM (static for this citizen; cacheable) " + "=" * 30 + "\n\n")
                fh.write(system + "\n\n")
                fh.write("=" * 30 + " USER (changes every request) " + "=" * 30 + "\n\n")
                fh.write(user + "\n")
            rows.append((name, call, idx, tick, len(system) // 4, len(user) // 4))
    with open(os.path.join(out_dir, "sizes.csv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("world,call,citizen,tick,system_tokens_est,user_tokens_est\n")
        for r in rows:
            fh.write(",".join("" if v is None else str(v) for v in r) + "\n")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="results/l0-prompts")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--arm", default="full")
    a = ap.parse_args(argv)
    for r in write(a.out, a.seed, a.arm):
        print(*("-" if v is None else v for v in r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
