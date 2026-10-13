from collections import defaultdict

from synw import config
from synw.runner import run
from synw.shocks import targets

from conftest import wpath


def test_size40_configs():
    for w in ("a", "b", "c"):
        cfg = config.load(wpath(f"size40/{w}.yaml"))
        assert cfg["arrival"]["agent"] == 39
        assert cfg["river"]["K"] == 3636364 and cfg["payroll"]["daily_cap"] == 29
        assert len(config.load_personas(cfg)["citizens"]) == 40
    b = config.load(wpath("size40/b.yaml"))
    assert set(b["governance"]["bodies"]) == {"strategy_assembly", "budget_assembly",
                                              "oversight_assembly", "adjudication_assembly"}


def test_large_town_b_draws_four_assemblies_without_consecutive_terms():
    w = run(wpath("size40/b.yaml"), 3)
    by_cycle = defaultdict(dict)
    for e in w.log.events:
        if e["type"] == "lottery":
            by_cycle[w.clock.at(e["tick"]).cycle][e["payload"]["body"]] = e["payload"]["members"]
    assert sorted(by_cycle) == list(range(1, 9))
    for cyc, bodies in by_cycle.items():
        assert len(bodies) == 4
        seated = [m for ms in bodies.values() for m in ms]
        assert len(seated) == len(set(seated)) == 20          # nobody on two bodies
        if cyc > 1:
            for body, ms in bodies.items():
                assert not set(ms) & set(by_cycle[cyc - 1][body])   # no consecutive terms
    assert w.governance.adjudication_body() == "adjudication_assembly"
    assert w.governance.main_body() == "strategy_assembly"


def test_shock_rotation_runs_over_the_population():
    assert targets(45, 40)["rogue"] == 5
    assert targets(45)["rogue"] == 45 % 11


def test_small_town_unchanged():
    w = run(wpath("b.yaml"), 1)
    assert w.governance.adjudication_body() == "review_bench"
    assert w.governance.main_body() == "cycle_assembly"
    assert run(wpath("a.yaml"), 1).governance.adjudication_body() is None
