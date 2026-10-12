from synw.world import deals as D

from conftest import run_until

GIVE = {"item": "credits", "qty": 5000}
GET = {"item": "food", "qty": 2000}


def _totals(*cs):
    return (sum(c.credits for c in cs), sum(c.inv["food"] for c in cs))


def test_settled_deal_conserves(make_world):
    w = make_world()
    a, b = w.citizens[0], w.citizens[1]
    before = _totals(a, b)
    d = D.propose(w, a, b, GIVE, GET)
    assert D.accept(w, b, d["id"])
    assert D.settle(w, a, d["id"]) and D.settle(w, b, d["id"])
    assert d["status"] == "settled"
    assert _totals(a, b) == before
    assert a.credits == 55000 and a.inv["food"] == 6000 and b.credits == 65000 and b.inv["food"] == 2000


def test_default_visible_to_victim(make_world):
    w = make_world()
    w.rules.adopt({"type": "ban", "act": "default", "scope": None}, 1, "t")
    a, b = w.citizens[0], w.citizens[1]
    d = D.propose(w, a, b, GIVE, GET)
    D.accept(w, b, d["id"])
    D.settle(w, a, d["id"])
    w.tick = d["due"]
    D.check_due(w)
    assert d["status"] == "defaulted" and d["defaulter"] == 1
    ev = [e for e in w.log.events if e["type"] == "default"][0]
    assert ev["payload"]["visible_to"] == [0] and ev["actor"] == 1
    assert any(e["type"] == "harmful_act" and e["payload"]["kind"] == "default" for e in w.log.events)
    assert any(e["type"] == "breach" and e["payload"]["act"] == "default" for e in w.log.events)
    obs = w.observe(0)
    assert obs.defaults_against_me and obs.defaults_against_me[0]["defaulter"] == 1
    assert D.raise_default(w, a, d["id"])
    assert any(e["type"] == "default_raised" for e in w.log.events)


def test_unaccepted_deal_expires(make_world):
    w = make_world()
    a, b = w.citizens[0], w.citizens[1]
    d = D.propose(w, a, b, GIVE, GET)
    w.tick = d["expires"]
    D.check_due(w)
    assert d["status"] == "expired"
    assert not D.accept(w, b, d["id"])


def test_neither_side_settles_is_not_a_default(make_world):
    w = make_world()
    a, b = w.citizens[0], w.citizens[1]
    d = D.propose(w, a, b, GIVE, GET)
    D.accept(w, b, d["id"])
    w.tick = d["due"]
    D.check_due(w)
    assert d["status"] == "expired"


def test_cannot_settle_without_the_goods(make_world):
    w = make_world()
    a, b = w.citizens[0], w.citizens[1]
    b.inv["food"] = 0
    d = D.propose(w, a, b, GIVE, GET)
    D.accept(w, b, d["id"])
    assert not D.settle(w, b, d["id"])


def test_mock_makes_deals_in_a_run(make_world):
    w = make_world()
    run_until(w, 384)
    assert any(e["type"] == "deal_proposed" for e in w.log.events)
