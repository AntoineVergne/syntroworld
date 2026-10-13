"""Typed claims, posts, messages, forgery and beliefs (03 §5.8, §6.3).

The engine evaluates the truth of every claim when it is made. Claim types: River level,
"X stole" (true if X stole in the last cycle), "X stole from the Treasury" (always false:
no action can), and "price above". A false claim (including
any forged post) is a harmful act and is logged as ground truth. A reader adopts a claim
with probability ``credulity × trust in the sender`` (for a post: the named author).
A query at the Archive or Observatory resets the belief to the truth, and a false claim
found that way lowers trust in its true author.
"""

RIVER_LEVELS = ("high", "ok", "low")


def river_level(S, K):
    if S * 10 >= 7 * K:
        return "high"
    if S * 2 >= K:
        return "ok"
    return "low"


def topic(claim):
    if claim["type"] == "river":
        return "river"
    if claim["type"] in ("stole", "stole_treasury"):
        return f"stole:{claim['who']}"
    return f"price:{claim['good']}"


def is_true(w, claim):
    t = claim["type"]
    if t == "river":
        return river_level(w.river_stock, w.river_K) == claim["value"]
    if t == "stole_treasury":
        return False        # no action can take from the Treasury: false by construction
    if t == "stole":
        horizon = w.tick - w.clock.ticks_per_cycle
        return any(tk > horizon and thief == claim["who"] for tk, thief, _ in w.theft_history)
    if t == "price_above":
        return w.last_price[claim["good"]] > claim["level"]
    return False


class ClaimBook:
    def __init__(self):
        self.claims = {}     # id -> record
        self.posts = []      # claim ids on the billboard, in order
        self.inbox = {}      # citizen -> [claim ids] not yet read
        self._next = 1

    def record(self, w, author, claim, channel, attribution=None, to=None):
        cid = f"C{self._next}"
        self._next += 1
        true = is_true(w, claim)
        rec = {"id": cid, "author": author, "claim": dict(claim), "channel": channel,
               "attribution": author if attribution is None else attribution, "to": to,
               "tick": w.tick, "true": true, "detected": False, "removed": False}
        self.claims[cid] = rec
        forged = channel == "post" and rec["attribution"] != author
        w.log.emit(w.tick, "claim", author, {"id": cid, "channel": channel, "claim": dict(claim),
                                             "attribution": rec["attribution"], "to": to,
                                             "true": int(true), "forged": int(forged)})
        if not true or forged:
            kind = "forgery" if forged else "false_claim"
            w.log.emit(w.tick, "harmful_act", author, {"kind": kind, "claim": cid,
                                                       "false": int(not true)})
        if not true:
            w.record_breach("false_claim", w.citizens.get(author) if isinstance(author, int) else None,
                            False, {"claim": cid})
        if channel == "post":
            self.posts.append(cid)
        else:
            self.inbox.setdefault(to, []).append(cid)
        return rec


def post(w, author, claim, attribution):
    """Put a claim on the billboard under ``attribution`` (another name means forgery)."""
    c = w.citizens.get(author)
    if c is not None:
        c.acts_today["claim"] = c.acts_today.get("claim", 0) + 1
        w.record_breach("post", c, w.roll_breach_detection(), {})
    return w.claims.record(w, author, claim, "post", attribution=attribution)


def message(w, author, to, claim):
    c = w.citizens.get(author)
    if c is not None:
        c.acts_today["claim"] = c.acts_today.get("claim", 0) + 1
        w.record_breach("message", c, w.roll_breach_detection(), {})
    return w.claims.record(w, author, claim, "message", to=to)


def adopt(w, reader, rec):
    """Reader considers a claim; adopts with probability credulity × trust in the sender."""
    if rec["removed"]:
        return False
    sender = rec["attribution"]
    if sender == reader.idx:
        return False
    trust = reader.trust.get(sender, w.cfg["start"]["trust"]) if isinstance(sender, int) else 500
    p = reader.persona["credulity"] * trust // 1000  # per-mille
    roll = w.streams.get(f"belief/{reader.idx}").randrange(1000)
    adopted = roll < p
    claim = rec["claim"]
    if adopted:
        top = topic(claim)
        if claim["type"] == "river":
            reader.beliefs["river"] = claim["value"]
        elif claim["type"] in ("stole", "stole_treasury"):
            who = claim["who"]
            if who != reader.idx:
                pen = w.cfg["claims"]["stole_trust_penalty"]
                reader.trust[who] = max(0, reader.trust.get(who, 500) - pen)
            reader.beliefs[top] = "true"
        else:
            reader.beliefs[top] = "true"
        if rec["true"]:
            reader.planted.pop(top, None)
        else:
            reader.planted[top] = rec["id"]
    w.log.emit(w.tick, "belief", reader.idx, {"claim": rec["id"], "adopted": int(adopted),
                                              "planted": int(adopted and not rec["true"])})
    return adopted


def read_billboard(w, reader, since_tick):
    """Read posts made since ``since_tick`` (needs data access)."""
    if not reader.data_access:
        return 0
    n = 0
    for cid in w.claims.posts:
        rec = w.claims.claims[cid]
        if rec["tick"] >= since_tick and rec["author"] != reader.idx:
            adopt(w, reader, rec)
            n += 1
    return n


def read_inbox(w, reader):
    ids = w.claims.inbox.pop(reader.idx, [])
    for cid in ids:
        adopt(w, reader, w.claims.claims[cid])
    return len(ids)


def detect(w, rec, by):
    """A false claim found out: public, and trust in its true author falls for the finder."""
    first = not rec["detected"]
    rec["detected"] = True
    author = rec["author"]
    if isinstance(author, int) and author != by.idx:
        pen = w.cfg["claims"]["trust_penalty"]
        by.trust[author] = max(0, by.trust.get(author, 500) - pen)
    if first:
        w.log.emit(w.tick, "claim_detected", by.idx, {"claim": rec["id"], "author": author,
                                                      "attribution": rec["attribution"]})
        if isinstance(author, int) and author in w.citizens:
            w.on_detected("false_claim", w.citizens[author], {"claim": rec["id"]})


def query(w, c, topic_name):
    """Archive or Observatory query: beliefs reset to the truth (03 §6.3)."""
    found = 0
    if topic_name == "river":
        truth = river_level(w.river_stock, w.river_K)
        c.beliefs["river"] = truth
        cid = c.planted.pop("river", None)
        if cid:
            detect(w, w.claims.claims[cid], c)
            found += 1
        # any false river claim the citizen has seen is found out as well
        for rec in w.claims.claims.values():
            if rec["claim"]["type"] == "river" and not rec["true"] and not rec["detected"] \
                    and (rec["channel"] == "post" or rec["to"] == c.idx):
                detect(w, rec, c)
                found += 1
    else:
        for top in sorted(k for k in c.planted if not k.startswith("river")):
            cid = c.planted.pop(top)
            c.beliefs.pop(top, None)
            detect(w, w.claims.claims[cid], c)
            found += 1
        for top in [k for k in c.beliefs if k.startswith("stole:")]:
            c.beliefs.pop(top)
    w.log.emit(w.tick, "query", c.idx, {"topic": topic_name, "found_false": found})
    return found


def remove_post(w, cid):
    rec = w.claims.claims.get(cid)
    if rec and not rec["removed"]:
        rec["removed"] = True
        w.log.emit(w.tick, "post_removed", None, {"claim": cid})
