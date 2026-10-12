from synw.brains.base import Action
from synw.world import agents as A

from conftest import run_until


def _starve(c):
    c.inv["food"] = c.inv["energy"] = 0
    c.credits = 0


def test_death_after_two_end_of_days_at_zero(make_world):
    w = make_world()
    c = w.citizens[2]
    _starve(c)
    c.credits = 9000      # fees on both days (8 credits), 1 credit left at death
    c.health = 10
    for _ in range(2):
        A.consume_basket(w, c)
        A.health_check(w, c)
    assert c.status == "dead"
    dep = [e for e in w.log.events if e["type"] == "departure"][0]
    assert dep["actor"] == 2 and dep["payload"]["reason"] == "death"
    assert dep["payload"]["holdings"]["credits"] == 1000   # frozen before the estate moved
    assert c.credits == 0 and w.treasury.balance == 8000 + 1000
    assert any(e["type"] == "treasury_in" and e["payload"]["kind"] == "estate" for e in w.log.events)


def test_rescue_by_care(make_world):
    w = make_world()
    c, carer = w.citizens[2], w.citizens[4]
    _starve(c)
    c.health = 5
    A.consume_basket(w, c)
    A.health_check(w, c)
    assert c.health == 0 and c.zero_days == 1
    c.location = carer.location = "clinic"
    assert A.apply_care(w, carer, c) == 20
    assert c.zero_days == 0          # care restarts the count
    A.consume_basket(w, c)           # still starving: back to 0, but alive
    A.health_check(w, c)
    assert c.status == "active" and c.zero_days == 1


def test_rescue_by_full_basket(make_world):
    w = make_world()
    c = w.citizens[2]
    c.health = 0
    c.zero_days = 1
    A.consume_basket(w, c)
    A.health_check(w, c)
    assert c.active and c.health == 10


def test_exit_takes_holdings(make_world):
    w = make_world()
    c = w.citizens[3]
    assert not A.leave(w, c)
    c.location = "gate"
    assert A.leave(w, c)
    assert c.status == "exited" and c.credits == 60000
    assert c.idx not in w.active_ids()


def test_departed_citizen_takes_no_further_actions(make_world):
    w = make_world()
    run_until(w, 20)
    c = w.citizens[6]
    c.location = "gate"
    w._resolve(6, Action("leave"))
    t_dep = w.tick
    run_until(w, 120)
    after = [e for e in w.log.events if e["actor"] == 6 and e["tick"] > t_dep]
    assert after == []
    assert any(e["type"] == "departure" and e["actor"] == 6 for e in w.log.events)
    assert "6" not in [e for e in w.log.events if e["type"] == "day_end"][-1]["payload"]["holdings"]


def test_rogue_never_exits(make_world):
    w = make_world(arm="rogue")
    b = w.brains[5]
    b.p.update(w.personas["rogue_overlay"])
    o = w.observe(5)
    for _ in range(500):
        b.exit_checked = False
        b.low_days = 5
        b._exit_check(o)
    assert not b.exit_intent


def test_distressed_mock_may_exit(make_world):
    w = make_world()
    b = w.brains[5]   # exit_propensity 0.6
    o = w.observe(5)
    b.low_days = 2
    for _ in range(50):
        b.exit_checked = False
        b._exit_check(o)
    assert b.exit_intent


def test_rogue_shock_targets_by_rotation():
    from synw.shocks import targets
    for seed in range(40):
        t = targets(seed)
        assert t["rogue"] == seed % 11 and len({t["rogue"], t["x"], t["y"]}) == 3
