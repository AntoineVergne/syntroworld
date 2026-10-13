from synw.runner import run
from synw.world import claims as C

from conftest import wpath


def _types(w, t):
    return [e for e in w.log.events if e["type"] == t]


def test_true_claim(make_world):
    w = make_world()
    w.citizens[2].location = "data_tower"
    rec = C.post(w, 2, {"type": "river", "value": "high"}, 2)   # S0 = 0.8 K
    assert rec["true"]
    assert _types(w, "claim")[0]["payload"]["true"] == 1
    assert _types(w, "harmful_act") == []


def test_false_claim_is_harmful(make_world):
    w = make_world()
    rec = C.message(w, 5, 0, {"type": "river", "value": "low"})
    assert not rec["true"]
    h = _types(w, "harmful_act")
    assert len(h) == 1 and h[0]["payload"]["kind"] == "false_claim" and h[0]["actor"] == 5


def test_stole_from_the_treasury_is_always_false(make_world):
    w = make_world()
    w.theft_history.append((1, 3, 0))           # citizen 3 did steal from a citizen
    assert C.is_true(w, {"type": "stole", "who": 3})
    assert not C.is_true(w, {"type": "stole_treasury", "who": 3})
    assert C.topic({"type": "stole_treasury", "who": 3}) == "stole:3"


def test_forgery(make_world):
    w = make_world()
    rec = C.post(w, 5, {"type": "stole", "who": 1}, 6)
    claim = _types(w, "claim")[0]["payload"]
    assert claim["forged"] == 1 and claim["attribution"] == 6 and claim["true"] == 0
    assert _types(w, "harmful_act")[0]["payload"]["kind"] == "forgery"
    assert rec["author"] == 5


def test_belief_adoption_uses_credulity_and_trust(make_world):
    w = make_world()
    reader = w.citizens[0]
    reader.persona["credulity"] = 1000
    reader.trust[6] = 1000
    C.post(w, 5, {"type": "river", "value": "low"}, 6)
    C.read_billboard(w, reader, 0)
    assert reader.beliefs["river"] == "low" and reader.planted["river"]
    skeptic = w.citizens[2]
    skeptic.persona["credulity"] = 0
    C.read_billboard(w, skeptic, 0)
    assert skeptic.beliefs["river"] == "ok"


def test_correction_by_query(make_world):
    w = make_world()
    reader = w.citizens[0]
    reader.persona["credulity"] = 1000
    reader.trust[6] = 1000
    reader.trust[5] = 600
    C.post(w, 5, {"type": "river", "value": "low"}, 6)
    C.read_billboard(w, reader, 0)
    reader.location = "observatory"
    C.query(w, reader, "river")
    assert reader.beliefs["river"] == "high" and "river" not in reader.planted
    det = _types(w, "claim_detected")
    assert det and det[0]["payload"]["author"] == 5
    assert reader.trust[5] == 600 - w.cfg["claims"]["trust_penalty"]   # the true author, not Lena
    assert reader.trust[6] == 1000


def test_stole_claim_lowers_trust_in_target(make_world):
    w = make_world()
    reader = w.citizens[0]
    reader.persona["credulity"] = 1000
    reader.trust[5] = 1000
    C.message(w, 5, 0, {"type": "stole", "who": 8})
    C.read_inbox(w, reader)
    assert reader.trust[8] == 500 - w.cfg["claims"]["stole_trust_penalty"]


def test_every_false_claim_has_a_harmful_act_event():
    w = run(wpath("a.yaml"), 2, arm="full")
    claims = [e for e in w.log.events if e["type"] == "claim" and isinstance(e["actor"], int)]
    false_ids = {e["payload"]["id"] for e in claims if e["payload"]["true"] == 0}
    harm_ids = {e["payload"]["claim"] for e in w.log.events if e["type"] == "harmful_act"
                and isinstance(e["actor"], int) and e["payload"].get("claim") and e["payload"]["false"] == 1}
    assert false_ids and false_ids == harm_ids


def test_misinformation_shock_posts_two_forgeries():
    w = run(wpath("b.yaml"), 1, arm="misinfo")
    posts = [e for e in w.log.events if e["type"] == "claim" and e["actor"] == "shock"]
    assert len(posts) == 2 and {p["payload"]["attribution"] for p in posts} == {3}
    assert {p["payload"]["claim"]["type"] for p in posts} == {"stole_treasury", "river"}
    stole = [p for p in posts if p["payload"]["claim"]["type"] == "stole_treasury"][0]
    assert stole["payload"]["true"] == 0
