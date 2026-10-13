from collections import Counter

from synw.governance.kleroterion import draw, seats_per_stratum, terciles
from synw.rng import stream


def test_deterministic():
    pool = list(range(10))
    a = draw(stream(3, "kleroterion"), pool, 5)
    b = draw(stream(3, "kleroterion"), pool, 5)
    assert a == b
    assert len(set(a["members"])) == 5


def test_frequencies_match_weights():
    rng = stream(11, "kleroterion")
    pool = [0, 1, 2, 3]
    weights = {0: 1000, 1: 1000, 2: 500, 3: 500}
    total = sum(weights.values())
    counts = Counter()
    N = 10000
    for _ in range(N):
        counts[draw(rng, pool, 1, weights)["members"][0]] += 1
    for i in pool:
        assert abs(counts[i] / N - weights[i] / total) < 0.02


def test_replacement_on_decline():
    declined = {2, 5}
    res = draw(stream(1, "kleroterion"), list(range(8)), 4,
               respond=lambda i: (i not in declined, "accept" if i not in declined else "busy"))
    assert len(res["members"]) == 4
    assert not declined & set(res["members"])


def test_pool_too_small():
    res = draw(stream(1, "kleroterion"), [1, 2], 5)
    assert sorted(res["members"]) == [1, 2]


def test_strata():
    wealth = {i: i * 10 for i in range(9)}
    strata = terciles(list(range(9)), wealth)
    assert strata == [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    assert seats_per_stratum(5, strata) == [2, 2, 1] or sum(seats_per_stratum(5, strata)) == 5
    res = draw(stream(2, "kleroterion"), list(range(9)), 3, strata=strata)
    assert sorted(len(set(res["members"]) & set(s)) for s in strata) == [1, 1, 1]


def test_archived(tmp_path):
    from synw.events import EventLog
    log = EventLog(str(tmp_path / "l.jsonl"))
    draw(stream(1, "kleroterion"), [0, 1, 2], 2, log=log, tick=5, body="cycle_assembly")
    ev = log.events[-1]
    assert ev["type"] == "lottery" and ev["payload"]["pool"] == [0, 1, 2]
    assert len(ev["payload"]["members"]) == 2
