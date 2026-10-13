import pytest

from synw.events import CanonicalError, EventLog, canonical, log_hash, read_log


def _write(path):
    log = EventLog(str(path), header={"engine": "test", "seed": 1})
    log.emit(1, "move", 0, {"to": "fields"})
    log.emit(1, "work", 1, {"site": "plant", "qty": 1500})
    log.emit(2, "note", None, {"nested": {"b": 2, "a": [1, 2]}})
    log.close("abc")
    return log


def test_round_trip(tmp_path):
    p = tmp_path / "run.jsonl"
    _write(p)
    header, events, footer = read_log(p)
    assert header["seed"] == 1
    assert [e["seq"] for e in events] == [1, 2, 3]
    assert events[1] == {"tick": 1, "seq": 2, "type": "work", "actor": 1,
                         "payload": {"site": "plant", "qty": 1500}}
    assert footer["state_hash"] == "abc"


def test_same_events_same_hash(tmp_path):
    _write(tmp_path / "a.jsonl")
    _write(tmp_path / "b.jsonl")
    assert log_hash(tmp_path / "a.jsonl") == log_hash(tmp_path / "b.jsonl")


def test_rejects_floats(tmp_path):
    log = EventLog(str(tmp_path / "f.jsonl"))
    with pytest.raises(CanonicalError):
        log.emit(1, "bad", 0, {"qty": 1.5})
    with pytest.raises(CanonicalError):
        canonical({"x": [1, {"y": 0.1}]})


def test_sorted_keys():
    assert canonical({"b": 1, "a": 2}) == '{"a":2,"b":1}'
