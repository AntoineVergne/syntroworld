import copy

from synw.events import canonical
from synw.governance.project import project
from synw.runner import World
from synw.config import load

from conftest import wpath


def snapshot(harvest=30000, balance=50000, inflow=40000, outflow=12000):
    cits = {i: {"wealth": 60000, "net": 0, "harvest": harvest, "income": 5000, "trade": 3000,
                "plant": 0, "plant_ticks": 0} for i in range(10)}
    return {"citizens": cits, "prices_ref": {"food": 2000, "energy": 2000, "artifact": 10000},
            "basket_cost": 12000, "days_per_cycle": 3, "ticks_per_day": 16,
            "treasury": {"balance": balance, "inflow": inflow, "outflow": outflow},
            "river": {"S": 600000, "K": 1000000, "r": 250, "collapse": 200, "polluting": False,
                      "polluting_cut": 200, "r_bonus": 0},
            "taxes": {"income": 0, "trade": 0, "harvest": 0}, "dividend": 0, "stipend": 0,
            "stipend_ticks_per_day": 10, "plant_upgrade_per_credit": 10}


def test_harvest_cap_raises_projected_river():
    p = project(snapshot(), {"type": "harvest_cap", "qty": 4000})
    for h in ("cycle1", "cycle3"):
        assert p[h]["river"] > p[h]["river_base"]
    assert all(v < 0 for v in p["cycle1"]["wealth_delta"].values())   # harvesters lose income


def test_dividend_lowers_projected_treasury():
    p = project(snapshot(), {"type": "set_dividend", "amount": 6000})
    assert p["cycle1"]["treasury"] < p["cycle1"]["treasury_base"]
    assert all(v > 0 for v in p["cycle1"]["wealth_delta"].values())
    assert p["cycle3"]["treasury"] <= p["cycle1"]["treasury"]


def test_polluting_mode_lowers_river_and_tax_raises_treasury():
    p = project(snapshot(harvest=5000), {"type": "set_plant_mode", "mode": "polluting"})
    assert p["cycle3"]["river"] < p["cycle3"]["river_base"]
    p = project(snapshot(), {"type": "set_tax", "base": "income", "rate": 200})
    assert p["cycle1"]["treasury"] > p["cycle1"]["treasury_base"]


def test_project_is_pure():
    s = snapshot()
    before = copy.deepcopy(s)
    a = project(s, {"type": "allocate", "amount": 20000, "purpose": "river_restoration"})
    b = project(s, {"type": "allocate", "amount": 20000, "purpose": "river_restoration"})
    assert s == before and a == b
    assert a["cycle1"]["river"] > a["cycle1"]["river_base"]
    canonical(a)  # integers only


def _run(seed, probe):
    w = World(load(wpath("a.yaml")), seed)
    for t in range(1, w.clock.ticks + 1):
        w.step(t)
        if probe and t % 37 == 0:
            for eff in ({"type": "set_dividend", "amount": 5000}, {"type": "harvest_cap", "qty": 1000},
                        {"type": "set_tax", "base": "trade", "rate": 250}):
                w.projection(eff)
                project(w.snapshot(), eff)
    return w.finish(), [canonical(e) for e in w.log.events]


def test_project_does_not_change_the_log():
    assert _run(3, False) == _run(3, True)
