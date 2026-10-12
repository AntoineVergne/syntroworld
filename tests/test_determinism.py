import subprocess
import sys

import pytest

from synw.cli import main
from synw.events import log_hash, read_log
from synw.runner import run

from conftest import ROOT, wpath


def test_cli_same_seed_same_hash(tmp_path, capsys):
    a, b = tmp_path / "a", tmp_path / "b"
    assert main(["run", wpath("a.yaml"), "--seed", "1", "--out", str(a)]) == 0
    assert main(["run", wpath("a.yaml"), "--seed", "1", "--out", str(b)]) == 0
    assert log_hash(a / "A-none-s1.jsonl") == log_hash(b / "A-none-s1.jsonl")
    assert "sha256=" in capsys.readouterr().out


def test_different_seeds_differ(tmp_path):
    run(wpath("a.yaml"), 1, out=str(tmp_path))
    run(wpath("a.yaml"), 2, out=str(tmp_path))
    assert log_hash(tmp_path / "A-none-s1.jsonl") != log_hash(tmp_path / "A-none-s2.jsonl")


@pytest.mark.parametrize("world", ["a.yaml", "b.yaml", "c.yaml"])
@pytest.mark.parametrize("arm", ["none", "full"])
def test_worlds_deterministic(tmp_path, world, arm):
    p1, p2 = tmp_path / "1", tmp_path / "2"
    w1 = run(wpath(world), 3, out=str(p1), arm=arm, keep_events=False)
    w2 = run(wpath(world), 3, out=str(p2), arm=arm, keep_events=False)
    assert log_hash(w1.log_path) == log_hash(w2.log_path)


def test_one_run_under_ten_seconds():
    w = run(wpath("a.yaml"), 1, keep_events=False)
    assert w.tick == 384
    assert w.elapsed < 10.0


def test_log_shape(tmp_path):
    w = run(wpath("a.yaml"), 5, out=str(tmp_path))
    header, events, footer = read_log(w.log_path)
    assert header["seed"] == 5 and header["engine"] == "synw" and header["config_hash"]
    assert footer["state_hash"] and footer["events"] == len(events)
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    arrival = [e for e in events if e["type"] == "arrival"]
    assert len(arrival) == 1 and arrival[0]["actor"] == 10 and arrival[0]["tick"] == 49


def test_shock_streams_identical_across_worlds():
    """Common random numbers: same seed, same shocks and weather in every world (06 M0)."""
    shocks = []
    for world in ("a.yaml", "b.yaml", "c.yaml"):
        w = run(wpath(world), 4, arm="full")
        shocks.append([(e["tick"], e["payload"]) for e in w.log.events if e["type"] == "shock"])
    assert shocks[0] == shocks[1] == shocks[2] and shocks[0]


def test_module_entry_point(tmp_path):
    r = subprocess.run([sys.executable, "-m", "synw.cli", "run", wpath("a.yaml"), "--seed", "1",
                        "--out", str(tmp_path)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_identical_across_processes_and_hash_seeds(tmp_path):
    """Byte-identical logs do not depend on Python's per-process string hashing."""
    import os
    hashes = []
    for hs in ("1", "2"):
        out = tmp_path / hs
        env = dict(os.environ, PYTHONHASHSEED=hs)
        r = subprocess.run([sys.executable, "-m", "synw.cli", "run", wpath("b.yaml"), "--seed", "2",
                            "--arm", "full", "--out", str(out)], cwd=ROOT, env=env,
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        hashes.append(log_hash(out / "B-full-s2.jsonl"))
    assert hashes[0] == hashes[1]
