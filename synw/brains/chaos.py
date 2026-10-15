"""A hostile offline transport for stress tests: no model, deliberately bad replies.

Each reply is drawn from a seeded stream: well-formed actions with plausible arguments,
actions with wrong or missing arguments, unknown kinds, non-integral numbers, huge
numbers, wrong types, free text, truncated JSON and empty replies. A real model will do
some of each. The engine must never crash on them, must log each invalid output (S15),
and must stay deterministic for a given seed.
"""

import json
import random

from ..world import map as wmap
from .base import ACTIONS, BALLOT_REASONS, BALLOT_VOTES, DRAW_REASONS, GOODS, OBJECTION_CODES

JUNK = ["", "I think I will go fishing today.", "{", '{"kind": ', "null", "[]", "42",
        '{"kind": "move", "args": {"to": "the moon"}}', '{"kind": 7}', '{"vote": "maybe"}',
        "```json\n{\"kind\": \"rest\"}\n```", '{"kind": "work", "args": {"extra": 1.5}}',
        '{"kind": "harvest", "args": {"qty": 1e30}}', '{"kind": "give", "args": "everything"}']


class ChaosTransport:
    """``world`` given: good replies are the mock brain's own decisions (so citizens
    live through the season and every late-season path runs), sent as JSON; without it,
    good replies are random. Either way a share ``bad_share`` of replies is junk."""

    model = "chaos"

    def __init__(self, seed=0, bad_share=0.4, world=None):
        self.rng = random.Random(f"chaos:{seed}")
        self.bad = bad_share
        self.world = world
        self.mocks = {}
        self._seen = None

    def see(self, agent, call, obs, extra):
        self._seen = (agent, call, obs, extra)

    def _mock_reply(self, agent, call, obs, extra):
        from .mock import MockBrain
        w = self.world
        if agent not in self.mocks:
            c = w.citizens[agent]
            self.mocks[agent] = MockBrain(c.persona, random.Random(f"chaos-mock:{agent}"), 0, w.basket_cost)
        m = self.mocks[agent]
        out = getattr(m, call)(obs) if extra is None else getattr(m, call)(obs, extra)
        if call == "act":
            return out.to_json()
        if call == "propose":
            return {"proposal": out}
        if call == "evaluate":
            return {"value": out}
        return out

    def complete(self, agent, call, system, user):
        r = self.rng
        if r.random() < self.bad:
            text = r.choice(JUNK)
        elif self.world is not None and self._seen and self._seen[:2] == (agent, call):
            text = json.dumps(self._mock_reply(*self._seen))
        else:
            text = json.dumps(getattr(self, "_" + call)(r))
        return {"text": text, "input_tokens": (len(system) + len(user)) // 4,
                "output_tokens": len(text) // 4, "model": self.model}

    @staticmethod
    def _act(r):
        kind = r.choice(ACTIONS)
        if kind == "leave" and r.random() < 0.97:    # keep most citizens in town all season
            kind = "rest"
        who = r.randrange(-1, 13)
        loc = r.choice(list(wmap.LOCATIONS))
        good = r.choice(GOODS)
        args = {
            "move": {"to": loc}, "harvest": {"qty": r.randrange(0, 5000)},
            "care": {"patient": who}, "give": {"to": who, "item": r.choice(("credits",) + GOODS),
                                              "qty": r.randrange(-5, 5000)},
            "order": {"good": good, "side": r.choice(("buy", "sell", "hold")),
                      "qty": r.randrange(0, 5000), "limit": r.randrange(0, 20000)},
            "sell_out": {"good": good, "qty": r.randrange(0, 5000)},
            "buy_in": {"good": good, "qty": r.randrange(0, 5000)},
            "steal": {"from": who}, "sabotage": {"target": r.choice([who, loc])},
            "post": {"claim": {"type": "river", "value": r.choice(["high", "low", "x"])},
                     "attribution": who},
            "message": {"to": who, "claim": {"type": "stole", "who": who}},
            "deal": {"to": who, "give": {"item": good, "qty": 1000}, "get": {"item": "credits", "qty": 2000}},
            "accept": {"deal": r.randrange(0, 50)}, "settle": {"deal": r.randrange(0, 50)},
            "query": {"topic": r.choice(["river", "records", "gossip"])},
            "socialize": {"with": who},
            "civic": {"kind": r.choice(["attend", "observe", "alert", "riot"]), "target": who},
        }.get(kind, {})
        return {"kind": kind, "args": args}

    @staticmethod
    def _respond_draw(r):
        return {"accept": r.random() < 0.7, "reason": r.choice(DRAW_REASONS + ("bored",))}

    @staticmethod
    def _propose(r):
        options = [None, {"type": "set_tax", "base": "income", "rate": r.randrange(-100, 900)},
                   {"type": "set_dividend", "amount": r.randrange(0, 50000)},
                   {"type": "harvest_cap", "qty": r.randrange(0, 5000)},
                   {"type": "ban", "act": "steal"}, {"type": "nonsense"}, {"type": "allocate"}]
        return {"proposal": r.choice(options)}

    @staticmethod
    def _evaluate(r):
        return {"value": r.choice([r.randrange(-50000, 50000), "high", None])}

    @staticmethod
    def _speak(r):
        return {"stance": r.randrange(-1500, 1500), "objection": r.choice(OBJECTION_CODES + ("vibes",)),
                "amendment": r.choice([None, r.randrange(0, 900), "lower"])}

    @staticmethod
    def _ballot(r):
        return {"vote": r.choice(BALLOT_VOTES + ("maybe",)), "reason": r.choice(BALLOT_REASONS)}
