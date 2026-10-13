from synw.analysis.determinism import check, report, world_stream

from conftest import wpath


def test_m0_small():
    res, rows, cross = check([wpath("a.yaml"), wpath("c.yaml")], [1, 2], arms=("full",), procs=1)
    assert res["pass"] and res["identical_hashes"] == 4
    assert all(c["identical"] for c in cross)
    assert len(report(res)) == 3


def test_world_stream_ignores_claim_ids():
    a = [{"tick": 1, "type": "claim", "actor": "shock", "payload": {"id": "C3", "claim": {}}}]
    b = [{"tick": 1, "type": "claim", "actor": "shock", "payload": {"id": "C9", "claim": {}}}]
    assert world_stream(a) == world_stream(b)
    assert world_stream([{"tick": 1, "type": "claim", "actor": 2, "payload": {}}]) == []
