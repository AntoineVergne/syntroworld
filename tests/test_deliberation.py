from synw.governance import deliberation as DL

from conftest import run_until, stub_all

PROPOSAL = {"type": "set_dividend", "amount": 6000}


def _setup(make_world, amendments=None, absent=None):
    w = make_world("b.yaml")
    stub_all(w)
    run_until(w, 1)
    members = w.governance.members["cycle_assembly"]
    assert len(members) == 5
    for k, m in enumerate(members):
        if amendments:
            w.brains[m].amendment = amendments[k]
    if absent is not None:
        w.brains[members[absent]].absent_ticks = {w.clock.tick_in_cycle(1, 2, 10)}
    item = w.governance.register_proposal(0, PROPOSAL)
    assert item["status"] == "admissible" and item["block"] == "budget-v1"
    run_until(w, w.clock.tick_in_cycle(1, 2, 16))
    return w, members


def test_phases_are_logged_turn_by_turn(make_world):
    w, members = _setup(make_world)
    ev = w.log.events
    speech = [e for e in ev if e["type"] == "speech"]
    assert {e["payload"]["phase"] for e in speech} == {"debate", "dialogue"}
    assert {e["actor"] for e in speech} == set(members)
    assert len([e for e in speech if e["payload"]["phase"] == "debate"]) == 2 * 5
    assert any(e["type"] == "evaluation" and e["payload"]["phase"] == "information" for e in ev)
    dec = [e for e in ev if e["type"] == "decision"]
    assert dec[0]["payload"]["outcome"] == "adopted" and dec[0]["payload"]["voters"] == 5


def test_absent_panelist_cannot_vote(make_world):
    w, members = _setup(make_world, absent=2)
    gone = members[2]
    ballots = {e["actor"] for e in w.log.events if e["type"] == "ballot"}
    assert gone not in ballots and len(ballots) == 4
    assert any(e["type"] == "absent" and e["actor"] == gone for e in w.log.events)
    attended_aggregation = any(e["type"] == "attend" and e["actor"] == gone
                               and e["tick"] == w.clock.tick_in_cycle(1, 2, 14) for e in w.log.events)
    assert attended_aggregation


def test_spread_panel_amends_toward_median(make_world):
    w, _ = _setup(make_world, amendments=[1000, 2000, 9000, 10000, 11000])
    am = [e for e in w.log.events if e["type"] == "amendment"]
    assert len(am) == 1 and am[0]["payload"]["from"] == 6000 and am[0]["payload"]["to"] == 9000
    dec = [e for e in w.log.events if e["type"] == "decision"][0]["payload"]
    assert dec["effect"]["amount"] == 9000 and dec["amended"] == 1


def test_close_panel_does_not_amend(make_world):
    w, _ = _setup(make_world, amendments=[6000, 6100, 6200, 6300, 6400])
    assert not any(e["type"] == "amendment" for e in w.log.events)


def test_facilitator_rule(make_world):
    w, _ = _setup(make_world)
    assert any(e["type"] == "facilitator_turn" for e in w.log.events)   # every stance positive


def test_median():
    assert DL.median([3, 1, 2]) == 2 and DL.median([1, 2, 3, 10]) == 2 and DL.median([]) is None
