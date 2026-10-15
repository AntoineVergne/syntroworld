"""The phase L campaign runner (06 §7.5, §8.2), with offline transports only."""
import csv
import os

from synw.analysis import campaign as C
from synw.brains.model import StubTransport


REST = '{"kind": "rest", "args": {}}'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stub(*_):
    return StubTransport(lambda *a: REST)


class Flaky:
    """Crashes on the first request of the first ``fail_first`` attempts per seed."""
    model = "flaky"

    def __init__(self, crash):
        self.crash = crash

    def complete(self, agent, call, system, user):
        if self.crash:
            raise RuntimeError("provider went away")
        return {"text": REST, "input_tokens": 100, "output_tokens": 5, "model": self.model}


def campaign(tmp_path, runs, factory, budget=10**9, cap=None, est=0.0, prices=(1e-6, 2e-6)):
    return C.Campaign(str(tmp_path), runs, factory, budget, prices[0], prices[1], cap, est, workers=2, root=HERE)


def rows(tmp_path):
    with open(os.path.join(tmp_path, "runs.csv")) as fh:
        return list(csv.DictReader(fh))


def test_plans_follow_06():
    assert C.plan("L0") == [("B", "none", 1, 48)]
    assert len(C.plan("L1")) == 12
    assert len(C.plan("L2", seeds=13)) == 4 * 13 * 2 and len(C.plan("L2", 13, twins=False)) == 52


def test_runs_and_resume(tmp_path):
    runs = [("A", "none", 1, 20), ("B", "none", 1, 20)]
    campaign(tmp_path, runs, stub).run()
    assert [r["status"] for r in rows(tmp_path)] == ["ok", "ok"]
    assert all(float(r["usd"]) > 0 for r in rows(tmp_path))
    campaign(tmp_path, runs, stub).run()
    assert [r["status"] for r in rows(tmp_path)] == ["ok (resumed)", "ok (resumed)"]


def test_a_crash_is_rerun_once_then_missing(tmp_path):
    attempts = {}

    def once(world, arm, seed):
        attempts[seed] = attempts.get(seed, 0) + 1
        return Flaky(crash=(seed == 2) or attempts[seed] == 1)   # seed 1 recovers; seed 2 never
    campaign(tmp_path, [("A", "none", 1, 10), ("A", "none", 2, 10)], once).run()
    r = {int(x["seed"]): x for x in rows(tmp_path)}
    assert r[1]["status"] == "ok" and r[1]["attempts"] == "2"
    assert r[2]["status"] == "missing" and r[2]["attempts"] == "2" and "crash" in r[2]["note"]
    assert os.path.exists(tmp_path / "A-none-s2.failed-1.jsonl") and os.path.exists(tmp_path / "A-none-s2.failed-2.jsonl")


def test_budget_stop_counts_as_failed(tmp_path):
    campaign(tmp_path, [("A", "none", 1, 30)], stub, budget=5000).run()
    r = rows(tmp_path)[0]
    assert r["status"] == "missing" and r["note"] == "budget"


def test_spend_cap_stops_new_runs(tmp_path):
    runs = [("A", "none", s, 10) for s in (1, 2, 3)]
    campaign(tmp_path, runs, stub, cap=0.5, est=0.2).run()
    statuses = [r["status"] for r in rows(tmp_path)]
    assert statuses.count("ok") == 2 and statuses.count("not run") == 1
