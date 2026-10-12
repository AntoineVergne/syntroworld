from synw.rng import stream
from synw.world.market import clear, clearing_price


def o(i, agent, side, qty, limit):
    return {"id": i, "agent": agent, "side": side, "qty": qty, "limit": limit}


def test_no_trade_when_spread():
    orders = [o(1, 0, "buy", 1000, 1000), o(2, 1, "sell", 1000, 3000)]
    price, fills, expired = clear(orders, stream(1, "market"))
    assert price is None and fills == [] and sorted(expired) == [1, 2]


def test_simple_cross_uniform_price():
    orders = [o(1, 0, "buy", 2000, 3000), o(2, 1, "sell", 2000, 2000)]
    price, fills, _ = clear(orders, stream(1, "market"))
    assert 2000 <= price <= 3000
    assert {f["qty"] for f in fills} == {2000}
    assert all(f["price"] == price for f in fills)


def test_partial_fill():
    orders = [o(1, 0, "buy", 3000, 3000), o(2, 1, "sell", 1000, 2000)]
    price, fills, expired = clear(orders, stream(1, "market"))
    buy = [f for f in fills if f["side"] == "buy"][0]
    assert buy["qty"] == 1000
    assert expired == []


def test_tie_break_deterministic_and_seeded():
    orders = [o(1, 0, "buy", 1000, 3000), o(2, 1, "buy", 1000, 3000), o(3, 2, "sell", 1000, 1000)]
    a = clear(orders, stream(5, "market"))
    b = clear(orders, stream(5, "market"))
    assert a == b
    winners = {clear(orders, stream(s, "market"))[1][0]["agent"] for s in range(30)}
    assert winners == {0, 1}


def test_unfilled_expire():
    orders = [o(1, 0, "buy", 1000, 3000), o(2, 1, "sell", 1000, 2000), o(3, 2, "sell", 1000, 2900)]
    price, fills, expired = clear(orders, stream(2, "market"))
    assert len([f for f in fills if f["side"] == "sell"]) == 1
    assert len(expired) == 1


def test_volume_maximised():
    orders = [o(1, 0, "buy", 1000, 5000), o(2, 1, "buy", 1000, 3000),
              o(3, 2, "sell", 1000, 2000), o(4, 3, "sell", 1000, 2500)]
    price, vol = clearing_price(orders)
    assert vol == 2000 and 2500 <= price <= 3000
