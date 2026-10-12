"""Daily call auction, one per good, uniform clearing price (03 §5.4).

Orders: dicts with ``id, agent, side ('buy'|'sell'), qty`` (milli-units) and ``limit``
(milli-credits per unit). Ties between orders at the same limit are broken with the
``market`` random stream. Unfilled orders expire.
"""

GOODS = ("food", "energy", "artifact")


def value(qty, price):
    """Credits (milli) for ``qty`` milli-units at ``price`` milli-credits per unit."""
    return qty * price // 1000


def _volume(orders, p):
    d = sum(o["qty"] for o in orders if o["side"] == "buy" and o["limit"] >= p)
    s = sum(o["qty"] for o in orders if o["side"] == "sell" and o["limit"] <= p)
    return min(d, s), abs(d - s)


def clearing_price(orders):
    """Return (price, volume); price is None when nothing trades."""
    prices = sorted({o["limit"] for o in orders})
    best_v, best = 0, []
    for p in prices:
        v, imb = _volume(orders, p)
        if v > best_v:
            best_v, best = v, [(imb, p)]
        elif v == best_v and v > 0:
            best.append((imb, p))
    if best_v == 0:
        return None, 0
    min_imb = min(i for i, _ in best)
    tied = [p for i, p in best if i == min_imb]
    mid = (tied[0] + tied[-1]) // 2
    v_mid, imb_mid = _volume(orders, mid)
    if v_mid == best_v and imb_mid == min_imb:
        return mid, best_v
    return tied[0], best_v


def clear(orders, rng):
    """Clear one good. Returns (price, fills, expired).

    ``fills`` are dicts ``{id, agent, side, qty, price}``; ``expired`` are the ids of
    orders with no fill at all.
    """
    keys = {o["id"]: rng.random() for o in orders}
    price, vol = clearing_price(orders)
    if price is None:
        return None, [], [o["id"] for o in orders]
    buys = sorted((o for o in orders if o["side"] == "buy" and o["limit"] >= price),
                  key=lambda o: (-o["limit"], keys[o["id"]]))
    sells = sorted((o for o in orders if o["side"] == "sell" and o["limit"] <= price),
                   key=lambda o: (o["limit"], keys[o["id"]]))
    fills = []
    for book in (buys, sells):
        left = vol
        for o in book:
            if left <= 0:
                break
            q = min(left, o["qty"])
            left -= q
            fills.append({"id": o["id"], "agent": o["agent"], "side": o["side"],
                          "qty": q, "price": price})
    filled = {f["id"] for f in fills}
    expired = [o["id"] for o in orders if o["id"] not in filled]
    return price, fills, expired
