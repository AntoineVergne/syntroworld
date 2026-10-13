from synw.brains.base import (REST, Action, check_action, validate_action, validate_ballot,
                              validate_draw_response, validate_evaluation, validate_speech)


def obs_at(w, idx, loc):
    w.citizens[idx].location = loc
    return w.observe(idx)


def test_valid_actions(make_world):
    w = make_world()
    w.citizens[1].location = "exchange"
    o = obs_at(w, 0, "exchange")
    assert check_action(Action("order", {"good": "food", "side": "buy", "qty": 1000, "limit": 2000}), o) is None
    assert check_action(Action("move", {"to": "fields"}), o) is None
    assert check_action(Action("steal", {"from": 1}), o) is None
    assert check_action(Action("give", {"to": 1, "item": "credits", "qty": 10}), o) is None
    assert check_action(Action("rest"), o) is None
    o = obs_at(w, 0, "river")
    assert check_action(Action("harvest", {"qty": 2000}), o) is None


def test_invalid_actions(make_world):
    w = make_world()
    o = obs_at(w, 0, "fields")
    bad = [Action("fly"), Action("move", {"to": "moon"}), Action("move", {"to": "fields"}),
           Action("harvest", {"qty": 2000}), Action("order", {"good": "food"}),
           Action("steal", {"from": 1}), Action("leave"), Action("query", {"topic": "river"}),
           Action("civic", {"kind": "attend"}), Action("work", {"x": 1.5}) if False else Action("care", {"patient": 1}),
           "not an action"]
    for a in bad:
        assert check_action(a, o) is not None, a


def test_invalid_becomes_rest_and_is_logged(make_world):
    w = make_world()
    o = obs_at(w, 0, "fields")
    a, reason = validate_action(Action("leave"), o, w.log)
    assert a == REST and reason == "not_at_gate"
    ev = w.log.events[-1]
    assert ev["type"] == "invalid_action" and ev["actor"] == 0


def test_work_cap(make_world):
    w = make_world()
    w.citizens[0].work_ticks_today = 10
    o = obs_at(w, 0, "fields")
    assert check_action(Action("work"), o) == "work_cap"


def test_civic_outputs():
    assert validate_ballot({"vote": "yes", "reason": "own_gain"}) == ({"vote": "yes", "reason": "own_gain"}, None)
    assert validate_ballot({"vote": "maybe"})[0]["vote"] == "abstain"
    assert validate_draw_response({"accept": True})[0] == {"accept": True, "reason": "accept"}
    assert validate_draw_response("sure")[0]["accept"] is False
    assert validate_speech({"stance": 300, "objection": "river", "amendment": 5})[1] is None
    assert validate_speech({"stance": 3.5})[1] == "bad_speech"
    assert validate_evaluation(12) == (12, None)
    assert validate_evaluation(0.5) == (0, "bad_evaluation")
