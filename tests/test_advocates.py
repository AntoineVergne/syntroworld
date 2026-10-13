from synw.events import EventLog
from synw.governance import advocates as ADV

from conftest import run_until, stub_all


def proj(river3, river3_base, treasury3=1000, treasury3_base=1000, floor3=1000, floor3_base=1000):
    c = {"river": river3, "river_base": river3_base, "treasury": treasury3,
         "treasury_base": treasury3_base, "floor": floor3, "floor_base": floor3_base}
    return {"cycle1": dict(c), "cycle3": dict(c)}


def test_river_objects_only_when_low_and_lower():
    K = 1000000
    assert ADV.river_brief(proj(400000, 450000), K)["objects"]
    assert not ADV.river_brief(proj(400000, 400000), K)["objects"]   # not lower than without
    assert not ADV.river_brief(proj(600000, 700000), K)["objects"]   # above K/2


def test_unborn_objects_on_treasury_or_floor():
    assert ADV.unborn_brief(proj(0, 0, treasury3=-1, treasury3_base=10))["objects"]
    assert ADV.unborn_brief(proj(0, 0, floor3=700, floor3_base=900))["objects"]
    assert not ADV.unborn_brief(proj(0, 0, floor3=900, floor3_base=950))["objects"]


class FakeGov:
    def __init__(self, p, tmp):
        self.p = p
        self.w = type("W", (), {"river_K": 1000000, "cfg": {"river": {"sustainable": 500}},
                                "log": EventLog(str(tmp / "l.jsonl"))})()

    def projection(self, effect):
        return self.p


def test_once_per_proposal(tmp_path):
    gov = FakeGov(proj(100000, 200000, treasury3=-5, treasury3_base=0), tmp_path)
    item = {"id": "P1", "effect": {"type": "set_plant_mode", "mode": "polluting"}, "objections": {}}
    assert ADV.hearing(gov, item, 10) == ["river", "unborn"]
    assert ADV.hearing(gov, item, 11) == []
    assert sum(1 for e in gov.w.log.events if e["type"] == "objection") == 2


def test_no_objection(tmp_path):
    gov = FakeGov(proj(800000, 800000), tmp_path)
    item = {"id": "P1", "effect": {}, "objections": {}}
    assert ADV.hearing(gov, item, 10) == []
    assert sum(1 for e in gov.w.log.events if e["type"] == "advocate_brief") == 2


def test_objection_reopens_dialogue_and_revotes(make_world):
    w = make_world("b.yaml")
    stub_all(w)
    w.river_stock = 150000
    run_until(w, 1)
    item = w.governance.register_proposal(0, {"type": "set_plant_mode", "mode": "polluting"})
    assert item["block"] == "ordinary-law-v1"
    run_until(w, w.clock.tick_in_cycle(1, 3, 1))
    ev = w.log.events
    obj = [e for e in ev if e["type"] == "objection"]
    assert [e["actor"] for e in obj] == ["advocate:river"]
    dec = [e["payload"] for e in ev if e["type"] == "decision" and e["payload"]["proposal"] == item["id"]]
    assert [d["round"] for d in dec] == [1, 2] and dec[0]["provisional"] == 1 and dec[1]["provisional"] == 0
    agg1 = w.clock.tick_in_cycle(1, 2, 14)
    assert [e["tick"] for e in ev if e["type"] == "decision"] == [agg1, agg1 + 2]
    assert any(e["type"] == "objection_result" for e in ev)
    reopened = [e for e in ev if e["type"] == "speech" and e["tick"] == agg1 + 1]
    assert reopened


def test_no_advocates_in_a(make_world):
    from synw.runner import run
    from conftest import wpath
    w = run(wpath("a.yaml"), 1)
    assert not any(e["type"] == "advocate_brief" for e in w.log.events)
    w = run(wpath("b.yaml"), 1)
    assert any(e["type"] == "advocate_brief" for e in w.log.events)
