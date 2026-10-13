from synw.brains.base import check_action


def _act(w, idx):
    o = w.observe(idx)
    a = w.brains[idx].act(o)
    assert check_action(a, o) is None
    return a


def test_hungry_agent_works(make_world):
    w = make_world()
    w.tick, w.time = 3, w.clock.at(3)
    c = w.citizens[9]  # Ama, a farmer
    c.inv["food"] = 0
    c.location = c.home
    a = _act(w, 9)
    assert a.kind == "move" and a.args["to"] in ("fields", "river", "plant", "workshop", "data_tower")
    c.location = a.args["to"]
    assert _act(w, 9).kind in ("work", "harvest")


def test_rich_agent_sells(make_world):
    w = make_world()
    w.tick, w.time = 14, w.clock.at(14)
    c = w.citizens[1]
    c.inv["food"] = 30000
    c.location = "fields"
    a = _act(w, 1)
    assert a.kind == "move" and a.args["to"] == "exchange"
    c.location = "exchange"
    a = _act(w, 1)
    assert a.kind == "order" and a.args["side"] == "sell" and a.args["good"] == "food"
    assert a.args["qty"] == 30000 - 4000


def test_incapacitated_rests(make_world):
    w = make_world()
    w.citizens[0].health = 0
    assert _act(w, 0).kind == "rest"


def test_compliance_formula(make_world):
    w = make_world()
    b = w.brains[5]  # Viktor, honesty 0.5
    o = w.observe(5)
    p = b.breach_probability(o, "steal", gain=12000, detection=500, sanction_share=1.0)
    assert abs(p - 0.25) < 1e-9
    rule = {"votes": {"5": "yes"}, "fairness": 1000}
    assert abs(b.breach_probability(o, "steal", 12000, 500, 1.0, [rule]) - 0.25) < 1e-9  # null: λ = 0
    b.lam = 1.0
    assert b.breach_probability(o, "steal", 12000, 500, 1.0, [rule]) == 0.0


def test_mock_is_deterministic(make_world):
    a = make_world(seed=4)
    b = make_world(seed=4)
    for t in range(1, 40):
        a.step(t)
        b.step(t)
    assert a.log.events == b.log.events
