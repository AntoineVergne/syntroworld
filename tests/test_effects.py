import pytest

from synw.governance import effects as E


def test_set_tax_and_dividend(make_world):
    w = make_world()
    w.rules.adopt({"type": "set_tax", "base": "harvest", "rate": 100}, 1, "t")
    assert w.rules.tax_rate("harvest") == 100
    w.rules.adopt({"type": "set_tax", "base": "harvest", "rate": 50}, 2, "t")
    assert w.rules.tax_rate("harvest") == 50
    w.tick = 2
    assert len([r for r in w.rules.active() if r.effect["type"] == "set_tax"]) == 1
    w.rules.adopt({"type": "set_dividend", "amount": 3000}, 2, "t")
    assert w.rules.dividend == 3000


def test_harvest_tax_applied(make_world):
    from synw.world import economy as ECO
    w = make_world()
    w.rules.adopt({"type": "set_tax", "base": "harvest", "rate": 500}, 1, "t")
    k = w.citizens[1]
    res = ECO.harvest(w, k, 2000)
    assert res["qty"] == 2000 and res["tax"] == 2000 * 2000 // 1000 // 2
    assert w.treasury.balance == res["tax"]


def _day(agent, feasible=(), claims=0, deals_due=0, harvested=0, breaches=()):
    return {"agent": agent, "feasible": set(feasible), "claims": claims, "deals_due": deals_due,
            "harvested": harvested, "breaches": set(breaches)}


def test_harvest_cap_exposure(make_world):
    w = make_world()
    r = w.rules.adopt({"type": "harvest_cap", "qty": 4000}, 1, "t")
    exp = {rule.id: (e, b) for rule, e, b in w.rules.exposures(_day(1, harvested=2))}
    assert exp[r.id] == (True, False)
    exp = {rule.id: (e, b) for rule, e, b in w.rules.exposures(_day(1, harvested=0))}
    assert exp[r.id] == (False, False)
    exp = {rule.id: (e, b) for rule, e, b in w.rules.exposures(_day(1, harvested=3, breaches=[r.id]))}
    assert exp[r.id] == (True, True)


def test_ban_exposure(make_world):
    w = make_world()
    exp = {rule.id: (e, b) for rule, e, b in w.rules.exposures(_day(0, feasible={"steal"}))}
    assert exp["R0-steal"] == (True, False) and exp["R0-sabotage"] == (False, False)
    fc = w.rules.adopt({"type": "ban", "act": "false_claim", "scope": None}, 1, "t")
    d = w.rules.adopt({"type": "ban", "act": "default", "scope": None}, 1, "t")
    exp = {rule.id: e for rule, e, b in w.rules.exposures(_day(0, claims=1))}
    assert exp[fc.id] and not exp[d.id]
    exp = {rule.id: e for rule, e, b in w.rules.exposures(_day(0, deals_due=1))}
    assert exp[d.id] and not exp[fc.id]
    scoped = w.rules.adopt({"type": "ban", "act": "post", "scope": 3}, 1, "t")
    assert scoped.id not in {rule.id for rule, _, _ in w.rules.exposures(_day(0, feasible={"post"}))}


def test_enforced_rules_have_no_exposure(make_world):
    w = make_world()
    r = w.rules.adopt({"type": "set_tax", "base": "income", "rate": 100}, 1, "t")
    assert r.id not in {rule.id for rule, _, _ in w.rules.exposures(_day(0, feasible={"steal"}))}


@pytest.mark.parametrize("effect", [
    {"type": "set_tax", "base": "income", "rate": 600},
    {"type": "set_dividend", "amount": 13000},          # above one reference basket (12 credits)
    {"type": "harvest_cap", "qty": -1},
    {"type": "suspend", "agent": 1, "actions": ["steal"], "duration": 49},
    {"type": "ban", "act": "leave"},                    # exit cannot be banned
    {"type": "set_tax", "base": "exit", "rate": 10},    # nor taxed
    {"type": "amend_block", "block": "bootstrap-v1", "field": "quorum", "value": {"share": 2000}},
    {"type": "teleport"},
])
def test_out_of_range_rejected_at_examination(make_world, effect):
    w = make_world()
    assert E.check(effect, w.cfg) is not None
    item = w.governance.register_proposal(0, effect)
    assert item["status"] == "rejected"
    ev = [e for e in w.log.events if e["type"] == "proposal_registered"][-1]
    assert ev["payload"]["admissible"] == 0 and ev["payload"]["reason"]


def test_legal_effects_admissible(make_world):
    w = make_world()
    for eff in ({"type": "set_dividend", "amount": 12000}, {"type": "harvest_cap", "qty": 4000},
                {"type": "amend_block", "block": "bootstrap-v1", "field": "deliberation", "value": True}):
        assert E.check(eff, w.cfg) is None
        assert w.governance.register_proposal(0, eff)["status"] == "admissible"
    assert w.governance.register_proposal(1, {"type": "harvest_cap", "qty": 4000})["status"] == "rejected"  # duplicate
