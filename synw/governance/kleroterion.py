"""The Kleroterion (02 §7): one service for every lottery.

Weights are integers (1000 = full weight; halved for service on the same body in the
previous cycle). Optional stratification by wealth tercile. A decline triggers a
replacement draw from the remaining pool. Only the ``kleroterion`` stream is used, and
the pool, weights and result are archived.
"""


def weighted_pick(rng, items, weights):
    total = sum(weights)
    if total <= 0:
        return None
    r = rng.randrange(total)
    acc = 0
    for it, w in zip(items, weights):
        acc += w
        if r < acc:
            return it
    return items[-1]


def terciles(pool, wealth):
    """Split ``pool`` into three wealth strata (poorest first); ties broken by id."""
    ordered = sorted(pool, key=lambda i: (wealth[i], i))
    n = len(ordered)
    a, b = n // 3 + (1 if n % 3 > 0 else 0), n // 3 + (1 if n % 3 > 1 else 0)
    return [ordered[:a], ordered[a:a + b], ordered[a + b:]]


def seats_per_stratum(size, strata):
    """Proportional seats, remainders to the largest strata (then the poorest)."""
    n = sum(len(s) for s in strata)
    if n == 0:
        return [0] * len(strata)
    base = [size * len(s) // n for s in strata]
    rem = size - sum(base)
    order = sorted(range(len(strata)), key=lambda k: (-(size * len(strata[k]) % n), k))
    for k in order[:rem]:
        base[k] += 1
    return [min(b, len(s)) for b, s in zip(base, strata)]


def draw(rng, pool, size, weights=None, respond=None, strata=None, log=None, tick=0, body=""):
    """Draw ``size`` members from ``pool``.

    ``weights``: dict id → int weight (default 1000). ``respond(id)`` returns
    ``(accepted, reason)``; a decline triggers a replacement from the remaining pool.
    ``strata``: optional list of lists of ids; seats are allocated proportionally.
    Returns ``{"members": [...], "declines": [(id, reason)], "draws": [...]}``.
    """
    pool = list(pool)
    weights = {i: (weights or {}).get(i, 1000) for i in pool}
    groups = strata if strata else [pool]
    seats = seats_per_stratum(size, groups) if strata else [min(size, len(pool))]
    members, declines, order = [], [], []
    for group, n in zip(groups, seats):
        remaining = [i for i in group if i in weights]
        got = 0
        while got < n and remaining:
            pick = weighted_pick(rng, remaining, [weights[i] for i in remaining])
            remaining.remove(pick)
            order.append(pick)
            ok, reason = respond(pick) if respond else (True, "accept")
            if ok:
                members.append(pick)
                got += 1
            else:
                declines.append((pick, reason))
    result = {"members": members, "declines": declines, "draws": order}
    if log is not None:
        log.emit(tick, "lottery", "kleroterion", {
            "body": body, "size": size, "pool": sorted(pool),
            "weights": {str(i): weights[i] for i in sorted(pool)},
            "strata": [sorted(g) for g in strata] if strata else None,
            "members": members, "declines": [[i, r] for i, r in declines], "draws": order})
    return result
