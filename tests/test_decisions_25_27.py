"""Decisions 25 (Oversight), 26 (P3 open to all) and 27 (stronger shocks)."""
from synw import config
from synw.metrics import Run
from synw.metrics.participation import p3_civic_breadth, voluntary_acts
from synw.runner import run
from synw.shocks import shock_config

from conftest import wpath

T = 16
CFG = config.public(config.load(wpath("base.yaml")))


def _log(events):
    out = []
    for d in range(1, 25):
        out.append({"tick": d * T, "seq": 0, "type": "day_end", "actor": "world",
                    "payload": {"day": d, "output": 0, "holdings": {"0": {}, "1": {}, "2": {}, "3": {}}}})
    return Run({"config": CFG}, out + events)


def ev(tick, t, actor, payload):
    return {"tick": tick, "seq": 0, "type": t, "actor": actor, "payload": payload}


def test_p3_counts_only_acts_open_to_all():
    day = 7 * T - 5
    r = _log([ev(day, "attend", 0, {"bodies": ["cycle_assembly"]}),      # seat duty: not counted
              ev(day, "ballot", 0, {"body": "cycle_assembly", "vote": "yes"}),
              ev(day, "attend", 1, {"bodies": ["plenary"]}),             # plenary: counted
              ev(day, "observe", 2, {"bodies": ["cycle_assembly"]}),     # observing: counted
              ev(day, "proposal_registered", 3, {})])
    assert sorted(c for c, _, _ in voluntary_acts(r)) == [1, 2, 3]
    assert p3_civic_breadth(r) == 3 / (4 * 6)     # 3 of 4 citizens act in 1 of 6 window cycles


def test_b_members_alone_do_not_make_p3():
    w = run(wpath("b.yaml"), 2)
    r = Run(w.log.header, w.log.events)
    acts = voluntary_acts(r)
    assert acts and not any(t in ("attend", "ballot") for _, _, t in acts)   # B has no plenary
    assert any(t == "observe" for _, _, t in acts)                      # non-members observe


def test_stronger_shocks_configured():
    sc = shock_config(config.load(wpath("a.yaml")))
    assert sc["drought"] == {"days": 5, "fields_factor": 250, "plant_factor": 250}
    w = run(wpath("a.yaml"), 3, arm="drought")
    onset = [e for e in w.log.events if e["type"] == "shock" and e["payload"]["phase"] == "onset"][0]
    end = [e for e in w.log.events if e["type"] == "shock" and e["payload"]["phase"] == "end"][0]
    assert w.clock.at(onset["tick"]).day == 7 and w.clock.at(end["tick"]).day == 12


def test_rogue_sabotages_the_busiest_site():
    w = run(wpath("a.yaml"), 4, arm="rogue")
    rogue = [e for e in w.log.events if e["type"] == "shock" and e["payload"]["shock"] == "rogue"][0]
    sab = [e for e in w.log.events if e["type"] == "sabotage" and e["actor"] == rogue["payload"]["target"]
           and "site" in e["payload"]]
    assert len(sab) >= 3


def test_rogue_replaced_if_the_scheduled_one_left(make_world):
    from conftest import run_until
    w = make_world("a.yaml", seed=2, arm="rogue")
    run_until(w, 10)
    sched = w.shocks.targets["rogue"]
    w.citizens[sched].location = "gate"
    from synw.world import agents as A
    A.leave(w, w.citizens[sched])
    run_until(w, w.clock.tick_of(19, 1))
    on = [e for e in w.log.events if e["type"] == "shock" and e["payload"]["shock"] == "rogue"][0]["payload"]
    assert on["scheduled"] == sched and on["target"] != sched and on["replaced"] == 1 and on["applied"] == 1
    assert w.citizens[on["target"]].rogue


def test_oversight_refers_to_adjudication():
    w = run(wpath("size40/b.yaml"), 3, arm="full")
    ev_ = w.log.events
    refs = [e for e in ev_ if e["type"] == "referral"]
    assert refs
    referred = {e["payload"]["to"] for e in refs}
    adj = {e["payload"]["proposal"] for e in ev_ if e["type"] == "decision" and e["actor"] == "adjudication_assembly"}
    assert referred & adj
    # with an Oversight body, Adjudication no longer picks breaches up by itself
    origins = {e["payload"].get("origin", "") for e in ev_ if e["type"] == "proposal_registered"
               and e["actor"] == "adjudication_assembly"}
    assert not any(o.startswith("breach:") for o in origins)
