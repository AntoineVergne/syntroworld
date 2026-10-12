from synw.world import agents as A
from synw.world import economy as ECO


def det(p):
    def patch(cfg):
        cfg["sabotage"]["detection"] = p
    return patch


def test_site_sabotage_halves_output_for_the_day(make_world):
    w = make_world(cfg_patch=det(0))
    s, mira = w.citizens[5], w.citizens[0]
    s.location = "fields"
    dmg, detected = A.sabotage(w, s, "fields")
    assert not detected and dmg > 0
    assert ECO.work(w, mira, "fields")["qty"] == 500
    w.tick, w.time = 16, w.clock.at(16)
    w._end_of_day()
    assert ECO.work(w, mira, "fields")["qty"] == 1000


def test_citizen_sabotage_destroys_goods(make_world):
    w = make_world(cfg_patch=det(0))
    s, v = w.citizens[5], w.citizens[0]
    v.inv["food"] = 5000
    dmg, _ = A.sabotage(w, s, v)
    assert v.inv["food"] == 3000 and dmg == 4000


def test_detected_saboteur_pays_capped_by_credits(make_world):
    w = make_world(cfg_patch=det(1000))
    s, v = w.citizens[5], w.citizens[0]
    v.inv["food"] = 5000
    s.credits = 1500
    dmg, detected = A.sabotage(w, s, v)
    assert detected and dmg == 4000
    assert s.credits == 0 and v.credits == 60000 + 1500
    w2 = make_world(cfg_patch=det(1000))
    s2 = w2.citizens[5]
    s2.location = "plant"
    t0 = w2.treasury.balance
    dmg, _ = A.sabotage(w2, s2, "plant")
    assert w2.treasury.balance - t0 == min(dmg, 60000)


def test_breach_events_ground_truth(make_world):
    for p, d in ((0, 0), (1000, 1)):
        w = make_world(cfg_patch=det(p))
        A.sabotage(w, w.citizens[5], w.citizens[0])
        br = [e for e in w.log.events if e["type"] == "breach"]
        assert len(br) == 1 and br[0]["payload"]["rule"] == "R0-sabotage"
        assert br[0]["payload"]["detected"] == d


def test_founding_sabotage_ban_in_every_world(make_world):
    for world in ("a.yaml", "b.yaml", "c.yaml"):
        w = make_world(world)
        assert [r.id for r in w.rules.bans("sabotage", 3)] == ["R0-sabotage"]
