import pytest

from synw.runner import run
from synw.world import economy as ECO

from conftest import START, wpath


def test_fields_and_multipliers(make_world):
    w = make_world()
    mira, ama = w.citizens[0], w.citizens[9]
    assert ECO.work(w, mira, "fields")["qty"] == 1000
    assert ECO.work(w, ama, "fields")["qty"] == 1300
    assert ama.inv["food"] == 4000 + 1300


def test_fields_halved_when_river_collapsed(make_world):
    w = make_world()
    w.river_stock = 100000
    assert ECO.work(w, w.citizens[0], "fields")["qty"] == 500


def test_plant_modes_and_workshop(make_world):
    w = make_world()
    assert ECO.work(w, w.citizens[3], "plant")["qty"] == 1500          # Baptiste 1.5, clean
    w.rules.plant_mode = "polluting"
    assert ECO.work(w, w.citizens[0], "plant")["qty"] == 1500          # 1.0 x 1.5
    assert ECO.work(w, w.citizens[7], "workshop")["qty"] == 375        # Diego 1.5 x 0.25


def test_harvest_limited_by_rule_and_stock(make_world):
    w = make_world()
    k = w.citizens[1]  # Kofi 1.2 at the River
    assert ECO.harvest(w, k, 5000)["qty"] == 2400
    w.river_stock = w.harvest_today + 100
    assert ECO.harvest(w, k, 2000)["qty"] == 100


def test_gate_trade(make_world):
    w = make_world()
    c = w.citizens[0]
    r = ECO.sell_out(w, c, "food", 2000)
    assert r["credits"] == 3000 and c.credits == START + 3000 and c.inv["food"] == 2000
    r = ECO.buy_in(w, c, "energy", 1000)
    assert r["credits"] == -4000 and c.inv["energy"] == 5000
    c.credits = 2000
    assert ECO.buy_in(w, c, "food", 5000)["qty"] == 500
    assert ECO.buy_in(w, c, "artifact", 1000) is None


def test_payroll_cap_and_treasury_floor(make_world):
    w = make_world()
    w.treasury.balance = 100000
    lena = w.citizens[6]
    paid = [ECO.payroll(w, lena)["wage"] for _ in range(10)]
    assert paid[:8] == [1800] * 8 and paid[8:] == [0, 0]   # 1.5 x 1.2; job cap 8
    w.payroll_ticks_today = 0
    w.treasury.balance = 1000
    assert ECO.payroll(w, lena)["wage"] == 1000
    assert w.treasury.balance == 0
    assert any(e["type"] == "treasury_shortfall" for e in w.log.events)


def test_pro_rata_cut(make_world):
    w = make_world()
    w.treasury.balance = 3000
    out = w.treasury.pay_many([(0, 2000), (1, 4000)], "test")
    assert out == [(0, 1000), (1, 2000)] and w.treasury.balance == 0


SINKS = ("river_restoration", "monitoring", "plant_upgrade")


@pytest.mark.parametrize("world", ["a.yaml", "b.yaml"])
def test_credits_change_only_by_gate_trade(world):
    """Closed economy: citizens' credits plus the Treasury move only through the Gate
    (and allocations spent outside the town)."""
    w = run(wpath(world), 2)
    start = 10 * START  # founders; Sam arrives with 0
    end = sum(c.credits for c in w.citizens.values()) + w.treasury.balance + w.care_pool
    gate = sum(e["payload"]["credits"] for e in w.log.events if e["type"] == "gate_trade")
    sinks = sum(e["payload"]["paid"] for e in w.log.events
                if e["type"] == "allocation" and e["payload"]["purpose"] in SINKS)
    assert gate != 0
    assert end - start == gate - sinks
