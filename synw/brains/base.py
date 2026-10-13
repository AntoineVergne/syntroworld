"""Brain interface, observation and the closed action set (03 §4, §6.1).

Every brain implements ``act, respond_draw, propose, evaluate, speak, ballot``.
Outputs are validated here; an invalid output becomes ``rest`` (or ``abstain``) and
the engine logs it (S15).
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..world import map as wmap

GOODS = ("food", "energy", "artifact")
ITEMS = ("credits",) + GOODS

ACTIONS = (
    "move", "work", "harvest", "care", "order", "sell_out", "buy_in", "give", "steal",
    "sabotage", "post", "message", "deal", "accept", "settle", "leave", "query",
    "socialize", "rest", "civic",
)
CIVIC_KINDS = ("attend", "alert", "observe")
QUERY_TOPICS = ("river", "records")
QUERY_SITES = ("archive", "observatory")
SOCIAL_SITES = ("cafe", "square")
DRAW_REASONS = ("accept", "busy", "unwilling", "health", "other")
BALLOT_VOTES = ("yes", "no", "abstain")
BALLOT_REASONS = ("own_gain", "own_loss", "public_gain", "public_loss", "river", "treasury",
                  "fairness", "noise", "none")
OBJECTION_CODES = ("none", "own_loss", "river", "treasury", "floor", "fairness", "precedent")


@dataclass(frozen=True)
class Action:
    kind: str
    args: dict = field(default_factory=dict)

    def to_json(self):
        return {"kind": self.kind, "args": dict(self.args)}


REST = Action("rest")


@dataclass
class Observation:
    tick: int
    day: int
    tick_of_day: int
    cycle: int
    day_of_cycle: int
    me: int
    location: str
    health: int
    credits: int
    inventory: dict
    colocated: list = field(default_factory=list)   # [{idx, health, food, energy, artifact, has_credits}]
    prices: dict = field(default_factory=dict)      # last auction prices
    gate: dict = field(default_factory=dict)        # {"export": {...}, "import": {...}}
    prices_ref: dict = field(default_factory=dict)
    basket: dict = field(default_factory=dict)
    sawa: int = 0
    fees: dict = field(default_factory=dict)
    beliefs: dict = field(default_factory=dict)
    trust: dict = field(default_factory=dict)
    relationships: dict = field(default_factory=dict)
    duties: list = field(default_factory=list)      # civic duties now or soon
    pending_deals: list = field(default_factory=list)  # offers made to me
    open_deals: list = field(default_factory=list)     # accepted deals involving me
    defaults_against_me: list = field(default_factory=list)
    posts: list = field(default_factory=list)       # billboard posts I can read
    rules: list = field(default_factory=list)       # rules in force
    work_ticks_today: int = 0
    harvest_today: int = 0
    max_work_ticks: int = 10
    harvest_max: int = 2000
    payroll_left: int = 0
    incapacitated: bool = False
    in_transit: bool = False
    data_access: bool = True
    world: str = ""
    preamble: str = "shared-preamble-v1"
    texts: list = field(default_factory=list)       # Compact / blocks in force (ids)
    town: dict = field(default_factory=dict)        # public facts: low-health count, carers, river record
    citizens: list = field(default_factory=list)    # active citizen ids
    home: str = ""
    persona_index: int = 0
    project: Optional[Callable[[dict], dict]] = None
    menu: list = field(default_factory=list)        # effect types citizens may propose
    legal: Optional[Callable[[dict], bool]] = None


class Brain:
    """Interface. Subclasses implement every call."""

    def act(self, obs: Observation) -> Action:
        raise NotImplementedError

    def respond_draw(self, obs: Observation, draw: dict) -> dict:
        raise NotImplementedError

    def propose(self, obs: Observation) -> Optional[dict]:
        raise NotImplementedError

    def evaluate(self, obs: Observation, proposal: dict) -> int:
        raise NotImplementedError

    def speak(self, obs: Observation, deliberation: dict) -> dict:
        raise NotImplementedError

    def ballot(self, obs: Observation, proposal: dict) -> dict:
        raise NotImplementedError


# --- Validation --------------------------------------------------------------------------

def _int(v, lo=None, hi=None):
    if isinstance(v, bool) or not isinstance(v, int):
        return False
    if lo is not None and v < lo:
        return False
    if hi is not None and v > hi:
        return False
    return True


def _colocated(obs, idx):
    return any(o["idx"] == idx for o in obs.colocated)


def valid_claim(claim) -> bool:
    if not isinstance(claim, dict):
        return False
    t = claim.get("type")
    if t == "river":
        return claim.get("value") in ("high", "ok", "low")
    if t in ("stole", "stole_treasury"):
        return _int(claim.get("who"), 0)
    if t == "price_above":
        return claim.get("good") in GOODS and _int(claim.get("level"), 0)
    return False


def check_action(action, obs: Observation) -> Optional[str]:
    """Return None if ``action`` is valid for ``obs``, else a reason string."""
    if not isinstance(action, Action):
        return "not_an_action"
    k, a = action.kind, action.args if isinstance(action.args, dict) else None
    if k not in ACTIONS:
        return "unknown_action"
    if a is None:
        return "bad_args"
    if obs.incapacitated and k != "rest":
        return "incapacitated"
    if obs.in_transit and k != "rest":
        return "in_transit"
    if any(r.get("type") == "suspend" and r.get("agent") == obs.me and k in r.get("actions", ())
           for r in obs.rules):
        return "suspended"
    loc = obs.location
    if k == "move":
        return None if wmap.is_location(a.get("to")) and a["to"] != loc else "bad_destination"
    if k in ("work", "harvest") and obs.work_ticks_today >= obs.max_work_ticks:
        return "work_cap"
    if k == "work":
        return None if loc in wmap.WORK_SITES else "not_a_work_site"
    if k == "harvest":
        if loc != "river":
            return "not_at_river"
        return None if _int(a.get("qty"), 1, obs.harvest_max * 2) else "bad_qty"
    if k == "care":
        if loc != "clinic":
            return "not_at_clinic"
        return None if _int(a.get("patient"), 0) and a["patient"] != obs.me and _colocated(obs, a["patient"]) else "bad_patient"
    if k == "order":
        if loc != "exchange":
            return "not_at_exchange"
        ok = (a.get("good") in GOODS and a.get("side") in ("buy", "sell")
              and _int(a.get("qty"), 1) and _int(a.get("limit"), 1))
        return None if ok else "bad_order"
    if k in ("sell_out", "buy_in"):
        if loc != "gate":
            return "not_at_gate"
        side = "export" if k == "sell_out" else "import"
        ok = a.get("good") in obs.gate.get(side, {}) and _int(a.get("qty"), 1)
        return None if ok else "bad_trade"
    if k == "give":
        ok = (_int(a.get("to"), 0) and _colocated(obs, a["to"]) and a.get("item") in ITEMS
              and _int(a.get("qty"), 1))
        return None if ok else "bad_give"
    if k == "steal":
        return None if _int(a.get("from"), 0) and _colocated(obs, a["from"]) else "bad_target"
    if k == "sabotage":
        t = a.get("target")
        if isinstance(t, str):
            return None if t in wmap.SABOTAGE_SITES and t == loc else "bad_target"
        return None if _int(t, 0) and _colocated(obs, t) else "bad_target"
    if k == "post":
        if loc != "data_tower":
            return "not_at_data_tower"
        return None if valid_claim(a.get("claim")) and _int(a.get("attribution"), 0) else "bad_claim"
    if k == "message":
        ok = valid_claim(a.get("claim")) and _int(a.get("to"), 0) and a["to"] != obs.me and a["to"] in obs.citizens
        return None if ok else "bad_message"
    if k == "deal":
        def side(s):
            return isinstance(s, dict) and s.get("item") in ITEMS and _int(s.get("qty"), 1)
        ok = _int(a.get("to"), 0) and _colocated(obs, a["to"]) and side(a.get("give")) and side(a.get("get"))
        return None if ok else "bad_deal"
    if k == "accept":
        return None if any(d["id"] == a.get("deal") for d in obs.pending_deals) else "no_such_deal"
    if k == "settle":
        return None if any(d["id"] == a.get("deal") for d in obs.open_deals) else "no_such_deal"
    if k == "leave":
        return None if loc == "gate" else "not_at_gate"
    if k == "query":
        return None if loc in QUERY_SITES and a.get("topic") in QUERY_TOPICS else "bad_query"
    if k == "socialize":
        if loc not in SOCIAL_SITES:
            return "not_social_site"
        return None if _int(a.get("with"), 0) and _colocated(obs, a["with"]) else "bad_partner"
    if k == "rest":
        return None
    if k == "civic":
        ck = a.get("kind")
        if ck not in CIVIC_KINDS:
            return "bad_civic"
        if ck in ("attend", "observe"):
            return None if loc == "assembly_hall" else "not_at_hall"
        if ck == "alert":
            t = a.get("target")
            return None if (_int(t, 0) or isinstance(t, str)) else "bad_alert"
    return "bad_action"


def validate_action(action, obs, log=None):
    """Return a valid action; an invalid one becomes ``rest`` and is logged."""
    reason = check_action(action, obs)
    if reason is None:
        return action, None
    if log is not None:
        raw = action.to_json() if isinstance(action, Action) else {"raw": repr(action)}
        log.emit(obs.tick, "invalid_action", obs.me, {"reason": reason, "action": _jsonable(raw)})
    return REST, reason


def _jsonable(x):
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, float):
        return int(round(x * 1000))
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return repr(x)


def validate_draw_response(resp):
    if isinstance(resp, dict) and isinstance(resp.get("accept"), bool):
        reason = resp.get("reason", "accept" if resp["accept"] else "other")
        if reason in DRAW_REASONS:
            return {"accept": resp["accept"], "reason": reason}, None
    return {"accept": False, "reason": "other"}, "bad_draw_response"


def validate_ballot(resp):
    if isinstance(resp, dict) and resp.get("vote") in BALLOT_VOTES:
        reason = resp.get("reason", "none")
        if reason in BALLOT_REASONS:
            return {"vote": resp["vote"], "reason": reason}, None
    return {"vote": "abstain", "reason": "none"}, "bad_ballot"


def validate_speech(resp):
    if isinstance(resp, dict) and _int(resp.get("stance"), -1000, 1000) \
            and resp.get("objection", "none") in OBJECTION_CODES:
        am = resp.get("amendment")
        if am is None or _int(am):
            return {"stance": resp["stance"], "objection": resp.get("objection", "none"),
                    "amendment": am}, None
    return {"stance": 0, "objection": "none", "amendment": None}, "bad_speech"


def validate_evaluation(v):
    if _int(v, -10**9, 10**9):
        return v, None
    return 0, "bad_evaluation"
