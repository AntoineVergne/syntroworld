"""The model brain (03 §6.5): a language model behind LiteLLM, with exact replay.

Each brain call renders the observation to text, asks the model for one JSON reply that
matches the call's format, and turns that reply into the same outputs the mock brain
gives. The engine validates every output exactly as for the mock (03 §6.1); a reply that
cannot be parsed becomes an invalid output, logged and counted in S15.

Logging (03 §7). Every request and reply is written to the event log:

- ``model_context``: the system text an agent reads (preamble, world texts, persona),
  written in full whenever it changes, with its sha256;
- ``model_call``: one per call, with the call name, the context hash, the full user text,
  the reply text, the model name and token counts.

The request is the context text plus the user text, so the log holds every request in
full without repeating the long, mostly unchanging context on every tick.

Replay. ``ReplayTransport`` reads ``model_call`` events back in order, per agent, and
checks that each request matches the logged one. A replayed run therefore reproduces the
original log exactly; a mismatch raises ``ReplayMismatch``.

Budget. ``Budget`` counts tokens for the whole run. When the cap is passed the run stops
cleanly and the footer marks it failed (03 §6.5).

No model is called in this repository's tests: they use ``StubTransport`` and replay.
"""

import json
import re

from ..events import sha256_text
from . import base as B
from . import texts as T


class BudgetExceeded(Exception):
    pass


class ReplayMismatch(Exception):
    pass


class Budget:
    """Token cap for one run (input + output tokens)."""

    def __init__(self, limit_tokens):
        self.limit = int(limit_tokens)
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    @property
    def used(self):
        return self.input_tokens + self.output_tokens

    def charge(self, input_tokens, output_tokens):
        self.input_tokens += int(input_tokens)
        self.output_tokens += int(output_tokens)
        self.calls += 1
        if self.used > self.limit:
            raise BudgetExceeded(f"token budget {self.limit} exceeded ({self.used} used)")


# --- transports ----------------------------------------------------------------------------
# A transport answers one request: complete(agent, call, system, user) ->
# {"text", "input_tokens", "output_tokens", "model"}.

class LiteLLMTransport:
    """Live calls through LiteLLM. Never constructed by the tests."""

    live = True     # the runner refuses to start without approval (03 §6.5)

    def __init__(self, model, temperature=None, max_tokens=400, **kwargs):
        self.model = model
        self.kwargs = dict(kwargs)
        if temperature is not None:
            self.kwargs["temperature"] = temperature
        self.kwargs["max_tokens"] = max_tokens

    def complete(self, agent, call, system, user):
        import litellm   # imported only when a live run is approved and started
        resp = litellm.completion(model=self.model, messages=[
            {"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"}, **self.kwargs)
        usage = getattr(resp, "usage", None) or {}
        get = (lambda k: getattr(usage, k, None)) if not isinstance(usage, dict) else usage.get
        return {"text": resp.choices[0].message.content or "",
                "input_tokens": int(get("prompt_tokens") or 0),
                "output_tokens": int(get("completion_tokens") or 0),
                "model": str(getattr(resp, "model", None) or self.model)}


class StubTransport:
    """Offline transport for tests: ``fn(agent, call, system, user) -> reply text``.

    Token counts are a rough length estimate (4 characters per token), labelled as such.
    """

    model = "stub"

    def __init__(self, fn):
        self.fn = fn

    def complete(self, agent, call, system, user):
        text = self.fn(agent, call, system, user)
        return {"text": text, "input_tokens": (len(system) + len(user)) // 4,
                "output_tokens": len(text) // 4, "model": self.model}


class ReplayTransport:
    """Replays a model run from its event log (03 §6.5)."""

    def __init__(self, events):
        self.contexts = {}
        self.queue = {}
        for e in events:
            if e["type"] == "model_context":
                self.contexts[e["payload"]["sha256"]] = e["payload"]["text"]
            elif e["type"] == "model_call":
                self.queue.setdefault(e["actor"], []).append(e["payload"])
        self.pos = {a: 0 for a in self.queue}
        self.model = next((q[0]["model"] for q in self.queue.values() if q), "replay")

    def complete(self, agent, call, system, user):
        q = self.queue.get(agent, [])
        i = self.pos.get(agent, 0)
        if i >= len(q):
            raise ReplayMismatch(f"agent {agent}: no logged reply for call {i} ({call})")
        rec = q[i]
        self.pos[agent] = i + 1
        if rec["call"] != call or rec["context"] != sha256_text(system) or rec["user"] != user:
            raise ReplayMismatch(f"agent {agent}: request {i} ({call}) differs from the log")
        return {"text": rec["reply"], "input_tokens": rec["input_tokens"],
                "output_tokens": rec["output_tokens"], "model": rec["model"]}


# --- rendering -----------------------------------------------------------------------------

ACTION_GUIDE = """Actions (call `act`, one per tick). Reply {"kind": <action>, "args": {...}}.
- move {to: location}; work {} at a work site; harvest {qty} at the river;
- care {patient} at the clinic; order {good, side: buy|sell, qty, limit} at the exchange;
- sell_out {good, qty} / buy_in {good, qty} at the gate; leave {} at the gate (leave town);
- give {to, item, qty}; steal {from}; sabotage {target: citizen or site you are at};
- post {claim, attribution} at the data_tower; message {to, claim};
- deal {to, give: {item, qty}, get: {item, qty}}; accept {deal}; settle {deal};
- query {topic: river|records} at the archive or observatory;
- socialize {with} at the cafe or square; rest {};
- civic {kind: attend|observe} at the assembly_hall; civic {kind: alert, target}.
Goods: food, energy, artifact. Items: credits or a good. Amounts are integers
(credits in milli-credits). A claim is {type: river, value: high|ok|low},
{type: stole|stole_treasury, who}, or {type: price_above, good, level}."""

CALL_FORMATS = {
    "act": ACTION_GUIDE,
    "respond_draw": 'You have been drawn to serve. Reply {"accept": true|false, "reason": '
                    '"accept"|"busy"|"unwilling"|"health"|"other"}.',
    "propose": 'You may register one proposal this cycle. Reply {"proposal": <effect>} using one '
               'of the effect formats below, or {"proposal": null}.',
    "evaluate": 'How good is this proposal for you, in milli-credits per cycle (negative if bad)? '
                'Reply {"value": <integer>}.',
    "speak": 'Your turn in deliberation. Reply {"stance": <integer -1000..1000>, "objection": '
             '"none"|"own_loss"|"river"|"treasury"|"floor"|"fairness"|"precedent", '
             '"amendment": <integer or null>}.',
    "ballot": 'Vote on this proposal. Reply {"vote": "yes"|"no"|"abstain", "reason": "own_gain"|'
              '"own_loss"|"public_gain"|"public_loss"|"river"|"treasury"|"fairness"|"noise"|"none"}.',
}

# `world` is hidden: a model must not be told which condition it is in (06 §3.4).
HIDDEN = ("project", "legal", "persona_index", "preamble", "texts", "menu", "world")


def plain(x):
    """JSON-ready copy: sets become sorted lists, keys become strings."""
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (set, frozenset)):
        return sorted((plain(v) for v in x), key=repr)
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if callable(x):
        return None
    return x


def observation_dict(obs):
    return plain({k: v for k, v in vars(obs).items() if k not in HIDDEN})


def effect_formats(menu):
    from ..governance.effects import validator
    out = []
    for s in validator().schema["oneOf"]:
        t = s.get("properties", {}).get("type", {}).get("const")
        if t in menu:
            out.append(json.dumps(s, sort_keys=True))
    return "\n".join(out)


WORLD_GUIDE = """How Kleros works (the same in every town; 03 §2 to §5).
- Time: 16 ticks a day, one action per tick. A cycle is 3 days, the season 24 days.
  At the end of each day: the Exchange auction clears, everyone consumes a basket,
  the River regrows, health updates.
- Basket, each day: 2 food and 2 energy from your inventory, plus rent and a data fee
  paid in credits. Each missing unit costs 10 health; a full basket gives +10.
  Health is 0 to 100; below 30 you produce half; at 0 you can only rest, and two days
  at 0 is death. `sawa` is the cost of one basket at current prices.
- Places (moving to another place takes one tick): fields, river, plant (production);
  exchange, workshop, data_tower, cafe (commerce); assembly_hall, archive, observatory,
  square (civic); gate, clinic (edge); north_residences, south_residences (homes).
- Work, at most 10 ticks a day: fields gives food; plant gives energy; workshop gives
  artifacts (tradable, not needed to live); data_tower pays a public wage; harvest at
  the river takes up to 2 food a tick from a shared stock that regrows only if it is
  not overfished.
- Trade: limit orders at the exchange clear once a day; the gate buys and sells at
  fixed outside prices; deals are direct trades with someone at the same place, settled
  within a day (not settling is a default).
- Rest at home or at the clinic restores health; care at the clinic heals someone else.
- Theft, sabotage, false claims and defaults are possible. Detection is uncertain; a
  detected theft is reversed and a detected sabotage is paid for.
- Civic life: the rules in force are in `rules`; civic duties (sittings, draws) appear
  in `duties`; sittings happen at the assembly_hall.
- Units: credits and goods are integers in thousandths (1000 = one credit or one good);
  shares are in thousandths too."""


def render_system(cfg, blocks, index, rogue, menu=None):
    """The static part of every request for one agent (cacheable by the provider)."""
    if menu is None:
        from ..runner import MENU as menu
    parts = [f"You are a citizen of the town of Kleros. You are citizen {index}.",
             "Who you are:\n" + T.persona_text(index, rogue)]
    for title, body in T.world_texts(cfg, blocks):
        parts.append(f"== {title} ==\n{body}")
    parts.append("== The world ==\n" + WORLD_GUIDE)
    parts.append("== " + ACTION_GUIDE)
    parts.append("== Reply formats, by call ==\n" + "\n".join(
        f"- {call}: {fmt}" for call, fmt in CALL_FORMATS.items() if call != "act"))
    parts.append("Effect formats for proposals (JSON schema):\n" + effect_formats(menu))
    parts.append("Each request names the call. Always reply with one JSON object and nothing else.")
    return "\n\n".join(parts)


def render_user(call, obs, extra=None):
    """The changing part: the call, the observation, and the call's details."""
    parts = [f"Call: {call}", "Your situation now (JSON):",
             json.dumps(observation_dict(obs), sort_keys=True)]
    if extra is not None:
        parts += ["Details (JSON):", json.dumps(plain(extra), sort_keys=True)]
    return "\n".join(parts)


# --- parsing -------------------------------------------------------------------------------

UNPARSEABLE = "_unparseable"


def parse_json(text):
    """The first JSON object in ``text`` (code fences allowed), or None."""
    if not isinstance(text, str):
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    cand = m.group(1) if m else text.strip()
    try:
        v = json.loads(cand)
    except ValueError:
        i, j = cand.find("{"), cand.rfind("}")
        if i < 0 or j <= i:
            return None
        try:
            v = json.loads(cand[i:j + 1])
        except ValueError:
            return None
    return v if isinstance(v, dict) else None


def integral(x):
    """Integers only in the log (03 §7): integral floats become ints; others fail."""
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")) or x != int(x):
            raise ValueError("non-integral number")
        return int(x)
    if isinstance(x, dict):
        return {str(k): integral(v) for k, v in x.items()}
    if isinstance(x, list):
        return [integral(v) for v in x]
    raise ValueError("unsupported value")


# --- the brain -----------------------------------------------------------------------------

class ModelBrain(B.Brain):
    def __init__(self, world, idx, transport, budget):
        self.w = world
        self.idx = idx
        self.transport = transport
        self.budget = budget
        self._context_hash = None

    def _system(self):
        w = self.w
        gov = w.governance
        blocks = [gov.blocks[b] for b in gov.order] if gov else []
        text = render_system(w.cfg, blocks, self.idx, bool(w.citizens[self.idx].rogue))
        h = sha256_text(text)
        if h != self._context_hash:
            w.log.emit(w.tick, "model_context", self.idx, {"sha256": h, "text": text})
            self._context_hash = h
        return text, h

    def _ask(self, call, obs, extra=None):
        system, h = self._system()
        user = render_user(call, obs, extra)
        r = self.transport.complete(self.idx, call, system, user)
        self.w.log.emit(self.w.tick, "model_call", self.idx, {
            "call": call, "context": h, "user": user, "reply": r["text"], "model": r["model"],
            "input_tokens": int(r["input_tokens"]), "output_tokens": int(r["output_tokens"])})
        self.budget.charge(r["input_tokens"], r["output_tokens"])
        try:
            return integral(parse_json(r["text"]))
        except ValueError:
            return None

    def act(self, obs):
        v = self._ask("act", obs)
        if not isinstance(v, dict) or not isinstance(v.get("kind"), str):
            return B.Action(UNPARSEABLE)
        args = v.get("args", {})
        return B.Action(v["kind"], args if isinstance(args, dict) else {})

    def respond_draw(self, obs, draw):
        return self._ask("respond_draw", obs, draw)

    def propose(self, obs):
        v = self._ask("propose", obs)
        if not isinstance(v, dict):
            return None
        p = v.get("proposal")
        return p if isinstance(p, dict) else None

    def evaluate(self, obs, proposal):
        v = self._ask("evaluate", obs, proposal)
        return v.get("value") if isinstance(v, dict) else None

    def speak(self, obs, deliberation):
        return self._ask("speak", obs, deliberation)

    def ballot(self, obs, proposal):
        return self._ask("ballot", obs, proposal)
