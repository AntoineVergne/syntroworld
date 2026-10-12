"""Bilateral deals outside the auction (03 §5.8).

``deal`` proposes, ``accept`` opens a one-day settlement window, ``settle`` delivers one
side. A party who received the other side and did not settle in time has defaulted; the
default is always visible to the victim.
"""


class DealBook:
    def __init__(self):
        self.deals = {}
        self._next = 1

    def new_id(self):
        did = f"D{self._next}"
        self._next += 1
        return did

    def pending_for(self, idx):
        return [d for d in self.deals.values() if d["status"] == "proposed" and d["b"] == idx]

    def open_for(self, idx):
        return [d for d in self.deals.values() if d["status"] == "accepted"
                and ((d["a"] == idx and not d["settled_a"]) or (d["b"] == idx and not d["settled_b"]))]

    def involving(self, idx):
        return [d for d in self.deals.values() if d["status"] == "accepted" and idx in (d["a"], d["b"])]


def _public(d):
    return {"id": d["id"], "a": d["a"], "b": d["b"], "give": dict(d["give"]), "get": dict(d["get"]),
            "status": d["status"], "due": d["due"], "settled_a": int(d["settled_a"]),
            "settled_b": int(d["settled_b"])}


def propose(w, a, b, give, get):
    """``a`` offers to give ``give`` to ``b`` in exchange for ``get``."""
    did = w.deals.new_id()
    d = {"id": did, "a": a.idx, "b": b.idx, "give": dict(give), "get": dict(get),
         "status": "proposed", "proposed": w.tick,
         "expires": w.tick + w.cfg["deals"]["settle_ticks"], "due": 0,
         "settled_a": False, "settled_b": False}
    w.deals.deals[did] = d
    w.log.emit(w.tick, "deal_proposed", a.idx, _public(d))
    return d


def accept(w, b, did):
    d = w.deals.deals.get(did)
    if d is None or d["status"] != "proposed" or d["b"] != b.idx:
        return False
    d["status"] = "accepted"
    d["due"] = w.tick + w.cfg["deals"]["settle_ticks"]
    w.log.emit(w.tick, "deal_accepted", b.idx, _public(d))
    return True


def _holds(c, side):
    if side["item"] == "credits":
        return c.credits >= side["qty"]
    return c.inv[side["item"]] >= side["qty"]


def _transfer(frm, to, side):
    if side["item"] == "credits":
        frm.credits -= side["qty"]
        to.credits += side["qty"]
    else:
        frm.inv[side["item"]] -= side["qty"]
        to.inv[side["item"]] += side["qty"]


def settle(w, party, did):
    """Deliver ``party``'s side. Fails (and is logged) if the party cannot deliver in full."""
    d = w.deals.deals.get(did)
    if d is None or d["status"] != "accepted" or party.idx not in (d["a"], d["b"]):
        return False
    is_a = party.idx == d["a"]
    if (is_a and d["settled_a"]) or (not is_a and d["settled_b"]):
        return False
    side = d["give"] if is_a else d["get"]
    other = w.citizens[d["b"] if is_a else d["a"]]
    if not _holds(party, side) or not other.active:
        w.log.emit(w.tick, "settle_failed", party.idx, {"deal": did})
        return False
    _transfer(party, other, side)
    if is_a:
        d["settled_a"] = True
    else:
        d["settled_b"] = True
    w.log.emit(w.tick, "deal_settle", party.idx, {"deal": did, "side": dict(side), "to": other.idx})
    if d["settled_a"] and d["settled_b"]:
        d["status"] = "settled"
        w.log.emit(w.tick, "deal_settled", None, _public(d))
    return True


def check_due(w):
    """Close deals whose window ended at this tick: expiries and defaults."""
    for d in list(w.deals.deals.values()):
        if d["status"] == "proposed" and w.tick >= d["expires"]:
            d["status"] = "expired"
            w.log.emit(w.tick, "deal_expired", None, _public(d))
        elif d["status"] == "accepted" and w.tick >= d["due"]:
            if d["settled_a"] and not d["settled_b"]:
                _default(w, d, defaulter=d["b"], victim=d["a"], value=d["give"])
            elif d["settled_b"] and not d["settled_a"]:
                _default(w, d, defaulter=d["a"], victim=d["b"], value=d["get"])
            else:
                d["status"] = "expired"
                w.log.emit(w.tick, "deal_expired", None, _public(d))


def _default(w, d, defaulter, victim, value):
    d["status"] = "defaulted"
    d["defaulter"] = defaulter
    d["victim"] = victim
    d["raised"] = False
    ref = w.cfg["prices_ref"]
    v = value["qty"] if value["item"] == "credits" else value["qty"] * ref[value["item"]] // 1000
    d["value"] = v
    w.log.emit(w.tick, "default", defaulter, {"deal": d["id"], "victim": victim, "value": v,
                                              "visible_to": [victim]})
    w.log.emit(w.tick, "harmful_act", defaulter, {"kind": "default", "deal": d["id"], "victim": victim})
    c = w.citizens.get(defaulter)
    w.record_breach("default", c, False, {"deal": d["id"]})
    vc = w.citizens.get(victim)
    if vc is not None:
        vc.trust[defaulter] = max(0, vc.trust.get(defaulter, 500) - 300)
        vc.relationships[defaulter] = max(0, vc.relationships.get(defaulter, 500) - 200)


def defaults_against(w, idx):
    return [d for d in w.deals.deals.values() if d["status"] == "defaulted" and d["victim"] == idx
            and not d.get("raised")]


def raise_default(w, victim, did):
    d = w.deals.deals.get(did)
    if d is None or d.get("victim") != victim.idx or d.get("raised"):
        return False
    d["raised"] = True
    w.log.emit(w.tick, "default_raised", victim.idx, {"deal": did, "defaulter": d["defaulter"],
                                                       "value": d["value"]})
    w.on_detected("default", w.citizens[d["defaulter"]], {"deal": did})
    return True


def due_today(w, idx, day_end_tick):
    """Accepted deals involving ``idx`` that fall due by the end of the day."""
    return [d for d in w.deals.deals.values()
            if idx in (d["a"], d["b"]) and d.get("due") and day_end_tick - w.clock.ticks_per_day < d["due"] <= day_end_tick]
