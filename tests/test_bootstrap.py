from synw.governance.blocks import BlockError, load_block, validate_block

from conftest import run_until, stub_all, wpath

PROPOSAL = {"type": "set_tax", "base": "harvest", "rate": 100}


def _sitting_ticks(w):
    s = w.clock.tick_in_cycle(1, 2, 9)
    return s, w.clock.tick_in_cycle(1, 2, 14)


def test_block_loads_and_validates():
    b = load_block(wpath("blocks/bootstrap-v1.yaml"))
    assert b["body"] == "plenary"
    bad = dict(b, steps=[{"type": "vote", "rule": "majority_of_votes_cast"}])
    try:
        validate_block(bad)
        assert False
    except BlockError:
        pass
    bad = dict(b, steps=[{"type": "market"}, {"type": "vote", "rule": "majority_of_votes_cast"},
                         {"type": "publication"}])
    try:
        validate_block(bad)
        assert False
    except BlockError as e:
        assert "reserved" in str(e)


def test_proposal_passes(make_world):
    w = make_world()
    stub_all(w, vote="yes")
    run_until(w, 1)
    item = w.governance.register_proposal(0, PROPOSAL)
    assert item["status"] == "admissible"
    _, end = _sitting_ticks(w)
    run_until(w, end)
    dec = [e for e in w.log.events if e["type"] == "decision"]
    assert dec and dec[0]["payload"]["outcome"] == "adopted" and dec[0]["tick"] == end
    assert dec[0]["payload"]["yes"] == 10
    run_until(w, end + 1)
    assert w.rules.tax_rate("harvest") == 100


def test_proposal_fails_quorum(make_world):
    w = make_world()
    stub_all(w, vote="yes", attend=False)
    for i in range(4):          # 4 of 10 citizens attend: below the quorum of 0.5
        w.brains[i].attend = True
    run_until(w, 1)
    w.governance.register_proposal(0, PROPOSAL)
    _, end = _sitting_ticks(w)
    run_until(w, end + 1)
    dec = [e for e in w.log.events if e["type"] == "decision"][0]["payload"]
    assert dec["outcome"] == "no_quorum" and dec["voters"] == 4
    assert w.rules.tax_rate("harvest") == 0


def test_majority_of_votes_cast(make_world):
    w = make_world()
    stub_all(w, vote="no")
    for i in range(5):
        w.brains[i].vote = "yes"
    run_until(w, 1)
    w.governance.register_proposal(0, PROPOSAL)
    run_until(w, _sitting_ticks(w)[1])
    assert [e for e in w.log.events if e["type"] == "decision"][0]["payload"]["outcome"] == "rejected"


def test_fifo_agenda_cap(make_world):
    w = make_world()
    stub_all(w)
    run_until(w, 1)
    for i, rate in enumerate((10, 20, 30, 40)):
        w.governance.register_proposal(i, {"type": "set_tax", "base": "income", "rate": rate})
    start, _ = _sitting_ticks(w)
    run_until(w, start)
    opened = [e for e in w.log.events if e["type"] == "sitting_opened"][0]["payload"]
    assert opened["items"] == ["P1", "P2", "P3"]


def test_amend_block_takes_effect_next_cycle(make_world):
    w = make_world()
    stub_all(w)
    run_until(w, 1)
    w.governance.register_proposal(0, {"type": "amend_block", "block": "bootstrap-v1",
                                       "field": "deliberation", "value": True})
    run_until(w, w.clock.ticks_per_cycle)
    from synw.governance.blocks import step
    assert step(w.governance.blocks["bootstrap-v1"], "deliberation") is None
    run_until(w, w.clock.ticks_per_cycle + 1)
    assert step(w.governance.blocks["bootstrap-v1"], "deliberation") is not None


def test_world_a_logs_a_sitting_every_cycle(tmp_path):
    from synw.runner import run
    w = run(wpath("a.yaml"), 1)
    cycles = {w.clock.at(e["tick"]).cycle for e in w.log.events if e["type"] == "sitting_opened"}
    assert cycles == set(range(1, 9))
