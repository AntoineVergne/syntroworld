from synw.brains.base import Action, check_action
from synw.world import agents as A


def _c(w, idx=0):
    return w.citizens[idx]


def test_full_basket(make_world):
    w = make_world()
    c = _c(w)
    c.health = 50
    t0 = w.treasury.balance
    res = A.consume_basket(w, c)
    assert res["full"]
    assert c.health == 60
    assert c.inv["food"] == 2000 and c.inv["energy"] == 2000
    assert c.credits == 60000 - 3000 - 1000
    assert w.treasury.balance == t0 + 4000
    c.health = 95
    A.consume_basket(w, c)
    assert c.health == 100


def test_missing_food(make_world):
    w = make_world()
    c = _c(w)
    c.inv["food"] = 0
    res = A.consume_basket(w, c)
    assert not res["full"] and c.health == 80


def test_missing_one_energy_unit(make_world):
    w = make_world()
    c = _c(w)
    c.inv["energy"] = 1000
    A.consume_basket(w, c)
    assert c.health == 90 and c.inv["energy"] == 0


def test_partial_unit_counts_as_missing(make_world):
    w = make_world()
    c = _c(w)
    c.inv["food"] = 1500
    A.consume_basket(w, c)
    assert c.health == 90


def test_missing_rent_sleeps_in_square(make_world):
    w = make_world()
    c = _c(w)
    c.credits = 1000
    res = A.consume_basket(w, c)
    assert not res["rent"] and res["data"]
    assert c.health == 90 and c.location == "square"


def test_missing_data_no_health_loss(make_world):
    w = make_world()
    c = _c(w)
    c.credits = 3000
    c.health = 70
    res = A.consume_basket(w, c)
    assert res["rent"] and not res["data"] and not res["full"]
    assert c.health == 70
    assert c.data_access is False


def test_low_health_halves_productivity(make_world):
    w = make_world()
    c = _c(w, 9)  # Ama, Fields 1.3
    assert c.productivity("fields") == 1300
    c.health = 29
    assert c.productivity("fields") == 650
    assert c.productivity("plant") == 500


def test_incapacitation(make_world):
    w = make_world()
    c = _c(w)
    c.health = 10
    c.inv["food"] = 0
    c.inv["energy"] = 0
    A.consume_basket(w, c)
    A.health_check(w, c)
    assert c.health == 0 and c.incapacitated and c.active
    obs = w.observe(0)
    assert obs.incapacitated
    assert check_action(Action("work"), obs) == "incapacitated"
    assert check_action(Action("rest"), obs) is None
