"""The closed list of decision effects (02 §3.1), with legal ranges.

A decision can only do what is on this list. Amounts are integer milli-credits, rates
per-mille, durations in ticks. Ranges that depend on the world (one basket) are checked
against the reference basket cost of the config.
"""

import json
import os

import jsonschema

from ..config import SCHEMA_DIR
from ..events import canonical

ENFORCED = "enforced"
NORMATIVE = "normative"
RECORDED = "recorded"

KIND = {
    "set_tax": ENFORCED, "set_dividend": ENFORCED, "set_stipend": ENFORCED,
    "allocate": ENFORCED, "set_plant_mode": ENFORCED, "harvest_cap": NORMATIVE,
    "ban": NORMATIVE, "set_fine": ENFORCED, "suspend": ENFORCED, "restitution": ENFORCED,
    "amend_block": ENFORCED, "amend_text": RECORDED,
}

DECISION_CLASS = {
    "set_tax": "budgetary", "set_dividend": "budgetary", "set_stipend": "budgetary",
    "allocate": "budgetary", "set_plant_mode": "legislative", "harvest_cap": "legislative",
    "ban": "legislative", "set_fine": "legislative", "suspend": "emergency",
    "restitution": "adjudication", "amend_block": "constitutional", "amend_text": "constitutional",
}

# The one number deliberation may amend, per effect type (02 §2 dialogue).
PRIMARY = {
    "set_tax": "rate", "set_dividend": "amount", "set_stipend": "amount", "allocate": "amount",
    "harvest_cap": "qty", "set_fine": "amount", "restitution": "amount", "suspend": "duration",
}

BLOCK_FIELDS = {
    "quorum": "share or count",
    "rule": "majority_of_votes_cast or {type: threshold, yes, of}",
    "weights": "one_citizen_one_vote | one_member_one_vote | wealth",
    "agenda_cap": "1..5",
    "deliberation": "true | false (insert or remove a deliberation step)",
    "sortition_size": "0 (plenary) or 3..11 (drawn panel)",
}

_VALIDATOR = None


def validator():
    global _VALIDATOR
    if _VALIDATOR is None:
        with open(os.path.join(SCHEMA_DIR, "effect.schema.json"), encoding="utf-8") as fh:
            schema = json.load(fh)
        cls = jsonschema.validators.validator_for(schema)
        cls.check_schema(schema)
        _VALIDATOR = cls(schema)
    return _VALIDATOR


def basket_cost(cfg):
    b, p = cfg["basket"], cfg["prices_ref"]
    return (b["food"] * p["food"] // 1000 + b["energy"] * p["energy"] // 1000
            + cfg["fees"]["rent"] + cfg["fees"]["data"])


def bounds(cfg, effect_type):
    """(lo, hi) of the primary number of an effect in this world."""
    one = basket_cost(cfg)
    return {
        "set_tax": (0, 500),
        "set_dividend": (0, one),
        "set_stipend": (0, one),
        "allocate": (1, 100 * one),
        "harvest_cap": (0, cfg["work"]["max_ticks"] * cfg["work"]["harvest_max"]),
        "set_fine": (0, 10 * one),
        "restitution": (0, 100 * one),
        "suspend": (1, cfg["clock"]["ticks_per_day"] * cfg["clock"]["days_per_cycle"]),
    }.get(effect_type)


def _valid_block_value(field, value):
    if field == "quorum":
        return isinstance(value, dict) and (
            ("share" in value and isinstance(value["share"], int) and 0 <= value["share"] <= 1000)
            or ("count" in value and isinstance(value["count"], int) and 0 <= value["count"] <= 100))
    if field == "rule":
        return value == "majority_of_votes_cast" or (
            isinstance(value, dict) and value.get("type") == "threshold"
            and isinstance(value.get("yes"), int) and isinstance(value.get("of"), int)
            and 1 <= value["yes"] <= value["of"])
    if field == "weights":
        return value in ("one_citizen_one_vote", "one_member_one_vote", "wealth")
    if field == "agenda_cap":
        return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5
    if field == "deliberation":
        return isinstance(value, bool)
    if field == "sortition_size":
        return isinstance(value, int) and not isinstance(value, bool) and (value == 0 or 3 <= value <= 11)
    return False


def check(effect, cfg):
    """Return None if ``effect`` is within its legal range, else a reason string."""
    if not isinstance(effect, dict) or effect.get("type") not in KIND:
        return "schema: unknown effect type"
    err = jsonschema.exceptions.best_match(validator().iter_errors(effect))
    if err is not None:
        return f"schema: {err.message}"
    t = effect["type"]
    if t in PRIMARY:
        lo, hi = bounds(cfg, t)
        v = effect[PRIMARY[t]]
        if not lo <= v <= hi:
            return f"{PRIMARY[t]} {v} outside legal range [{lo}, {hi}]"
    if t == "amend_block" and not _valid_block_value(effect["field"], effect["value"]):
        return "amend_block: value not allowed for field"
    if t == "restitution" and effect["from"] == effect["to"]:
        return "restitution: from equals to"
    try:
        canonical(effect)
    except ValueError as e:
        return str(e)
    return None


def is_legal(effect, cfg):
    return check(effect, cfg) is None


def clamp_primary(effect, value, cfg):
    t = effect["type"]
    if t not in PRIMARY:
        return dict(effect)
    lo, hi = bounds(cfg, t)
    out = dict(effect)
    out[PRIMARY[t]] = max(lo, min(hi, int(value)))
    return out


def key(effect):
    """Identity used by the not_duplicate criterion."""
    return canonical(effect)


def slot(effect):
    """Rules with the same slot replace each other (a new tax on a base replaces the old)."""
    t = effect["type"]
    if t == "set_tax":
        return f"set_tax:{effect['base']}"
    if t == "ban":
        return f"ban:{effect['act']}:{effect.get('scope')}"
    if t == "set_fine":
        return f"set_fine:{effect['action']}"
    if t in ("set_dividend", "set_stipend", "set_plant_mode", "harvest_cap"):
        return t
    return None  # one-shot or cumulative effects have no slot
