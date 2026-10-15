"""Run a phase L step as one campaign (06 §8.2, §7.5): many model runs, safely.

- **Plan**: L0 (B, seed 1, one cycle), L1 (A, B, C × seeds 1–2 × arms full and none),
  L2 (A, B, C, A+text × seeds 1..n × full, plus none twins unless ``--no-twins``).
- **Approval**: prints the 06 §8.2 estimate and refuses to start without ``--approve``.
- **Caps**: a token cap per run (the run stops cleanly, footer ``failed``) and a spend
  cap for the whole campaign (no new run starts once spent + the next run's estimate
  would pass it).
- **Failures** (06 §7.5): a run that crashes or hits its budget is re-run once with the
  same seed. A second failure makes it missing; the analysis drops that seed from every
  contrast that needs it, and the run list says so. Failed logs are kept as
  ``*.failed-<attempt>.jsonl``.
- **Resume**: a run whose log already ends with a clean footer is not run again.
- **Run list**: ``runs.csv`` lists every planned run with status, attempts, tokens
  and spend, including failures (06 §8.3).

    python -m synw.analysis.campaign --step L1 --out runs/l1 --model <litellm name> \\
        --run-budget-tokens <n> --spend-cap-usd <usd> --tokens-in <n> --tokens-out <n> [--approve]

Offline transports (``--transport stub|chaos``) need no approval and call no model; the
tests use them.
"""

import argparse
import csv
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from ..config import load
from ..events import read_log
from ..runner import World
from . import cost

WORLDS = {"A": "worlds/a.yaml", "B": "worlds/b.yaml", "C": "worlds/c.yaml", "A+text": "worlds/a-text.yaml"}
FIELDS = ["world", "arm", "seed", "ticks", "status", "attempts", "input_tokens", "output_tokens",
          "usd", "log", "note"]


def plan(step, seeds=None, twins=True):
    """[(world, arm, seed, ticks)] for a phase L step."""
    if step == "L0":
        return [("B", "none", 1, cost.CYCLE_TICKS)]
    if step == "L1":
        return [(w, arm, s, cost.SEASON_TICKS) for w in ("A", "B", "C") for s in (1, 2)
                for arm in ("full", "none")]
    if step == "L2":
        if not seeds:
            raise ValueError("L2 needs seeds (06 §7.4)")
        arms = ("full", "none") if twins else ("full",)
        return [(w, arm, s, cost.SEASON_TICKS) for w in ("A", "B", "C", "A+text")
                for s in range(1, seeds + 1) for arm in arms]
    raise ValueError(step)


def log_name(world, arm, seed):
    return f"{world}-{arm}-s{seed}.jsonl"


def clean_footer(path):
    """True if the log at ``path`` ends with a footer that is not failed."""
    if not os.path.exists(path):
        return False
    try:
        _, _, footer = read_log(path)
    except Exception:
        return False
    return bool(footer) and footer.get("status") in (None, "partial")


class Campaign:
    def __init__(self, out, runs, transport_factory, run_budget_tokens, price_in, price_out,
                 spend_cap_usd, estimate_per_run_usd, workers=4, root="."):
        self.out = out
        self.runs = runs
        self.factory = transport_factory
        self.budget = int(run_budget_tokens)
        self.pin, self.pout = price_in, price_out
        self.cap = spend_cap_usd
        self.est = estimate_per_run_usd
        self.workers = workers
        self.root = root
        self.spent = 0.0
        self.committed = 0.0
        self.lock = threading.Lock()
        self.rows = {}
        os.makedirs(out, exist_ok=True)

    def _usd(self, tin, tout):
        return tin * self.pin + tout * self.pout

    def _reserve(self):
        with self.lock:
            if self.cap is not None and self.spent + self.committed + self.est > self.cap:
                return False
            self.committed += self.est
            return True

    def _settle(self, usd):
        with self.lock:
            self.committed -= self.est
            self.spent += usd

    def _attempt(self, world, arm, seed, ticks, attempt):
        path = os.path.join(self.out, log_name(world, arm, seed))
        cfg = load(os.path.join(self.root, WORLDS[world]))
        w = None
        try:
            w = World(cfg, seed, arm=arm, log_path=path, keep_events=False,
                      brain={"type": "model", "transport": self.factory(world, arm, seed),
                             "budget_tokens": self.budget, "approved": True})
            w.run(ticks)
            status = w.log.footer.get("status") or "ok"
            note = w.log.footer.get("reason", "")
        except Exception as exc:          # a crash: keep what was written, mark it failed
            status, note = "failed", f"crash: {type(exc).__name__}: {exc}"[:200]
            if w is not None and not w.log.closed:
                w.log._fh and w.log._fh.close()
        tin = w.budget.input_tokens if w is not None and w.budget else 0
        tout = w.budget.output_tokens if w is not None and w.budget else 0
        if status == "failed" and os.path.exists(path):
            os.replace(path, path.replace(".jsonl", f".failed-{attempt}.jsonl"))
        return status, note, tin, tout, path

    def run_one(self, spec):
        world, arm, seed, ticks = spec
        key = (world, arm, seed)
        path = os.path.join(self.out, log_name(world, arm, seed))
        if clean_footer(path):
            self.rows[key] = dict(world=world, arm=arm, seed=seed, ticks=ticks, status="ok (resumed)",
                                  attempts=0, input_tokens=0, output_tokens=0, usd=0.0,
                                  log=os.path.basename(path), note="already complete")
            return
        tin_all = tout_all = 0
        usd_all = 0.0
        status, note, attempts = "missing", "", 0
        for attempt in (1, 2):           # 06 §7.5: re-run once with the same seed
            if not self._reserve():
                note = "spend cap reached; not started" if attempts == 0 else note + "; spend cap reached"
                status = "not run" if attempts == 0 else "missing"
                break
            attempts = attempt
            status, note, tin, tout, path = self._attempt(world, arm, seed, ticks, attempt)
            usd = self._usd(tin, tout)
            self._settle(usd)
            tin_all += tin
            tout_all += tout
            usd_all += usd
            if status != "failed":
                break
            status = "missing" if attempt == 2 else "failed"
        self.rows[key] = dict(world=world, arm=arm, seed=seed, ticks=ticks,
                              status="ok" if status in ("ok", "partial") else status,
                              attempts=attempts, input_tokens=tin_all, output_tokens=tout_all,
                              usd=round(usd_all, 4), log=log_name(world, arm, seed), note=note)

    def run(self):
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            list(ex.map(self.run_one, self.runs))
        self.write()
        return self.rows

    def write(self):
        with open(os.path.join(self.out, "runs.csv"), "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=FIELDS)
            wr.writeheader()
            for spec in self.runs:
                row = self.rows.get(spec[:3])
                if row is None:
                    row = dict(world=spec[0], arm=spec[1], seed=spec[2], ticks=spec[3], status="not run",
                               attempts=0, input_tokens=0, output_tokens=0, usd=0.0, log="", note="")
                wr.writerow(row)


def summary(rows):
    by = {}
    for r in rows.values():
        by[r["status"]] = by.get(r["status"], 0) + 1
    usd = sum(r["usd"] for r in rows.values())
    return f"runs: {by}; spent ${usd:,.2f}"


def _factory(args):
    if args.transport == "litellm":
        from ..brains.model import LiteLLMTransport
        return lambda world, arm, seed: LiteLLMTransport(args.model)
    if args.transport == "chaos":
        from ..brains.chaos import ChaosTransport
        return lambda world, arm, seed: ChaosTransport(seed, bad_share=0.5)
    from ..brains.model import StubTransport
    rest = '{"kind": "rest", "args": {}}'
    return lambda world, arm, seed: StubTransport(lambda *a: rest)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a phase L step as one campaign (06 §8.2, §7.5)")
    ap.add_argument("--step", required=True, choices=["L0", "L1", "L2"])
    ap.add_argument("--seeds", type=int)
    ap.add_argument("--no-twins", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--transport", choices=["litellm", "stub", "chaos"], default="litellm")
    ap.add_argument("--model")
    ap.add_argument("--run-budget-tokens", type=int, required=True)
    ap.add_argument("--spend-cap-usd", type=float)
    ap.add_argument("--tokens-in", type=float, help="per agent-tick, for the estimate")
    ap.add_argument("--tokens-out", type=float)
    ap.add_argument("--log", help="a measured L0 log for tokens per agent-tick")
    ap.add_argument("--usd-in-per-mtok", type=float)
    ap.add_argument("--usd-out-per-mtok", type=float)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--approve", action="store_true")
    a = ap.parse_args(argv)
    runs = plan(a.step, a.seeds, not a.no_twins)
    live = a.transport == "litellm"
    if live and not a.model:
        ap.error("--model is required for live runs")
    if a.usd_in_per_mtok is not None and a.usd_out_per_mtok is not None:
        pin, pout = a.usd_in_per_mtok / 1e6, a.usd_out_per_mtok / 1e6
    elif live:
        pin, pout = cost.litellm_prices(a.model)
    else:
        pin = pout = 0.0
    if a.log:
        m = cost.measure(a.log)
        tin, tout, src = m["tokens_in"], m["tokens_out"], f"measured in {a.log}"
    elif a.tokens_in is not None and a.tokens_out is not None:
        tin, tout, src = a.tokens_in, a.tokens_out, "given by hand"
    elif live:
        ap.error("give --log or --tokens-in/--tokens-out for the estimate")
    else:
        tin = tout = 0.0
        src = "offline"
    ticks = runs[0][3]
    text, total = cost.report(a.step, len(runs), ticks, f"{len(runs)} planned runs", tin, tout, pin, pout, src)
    print(text)
    if live and not a.approve:
        print("Refusing to start a model campaign without --approve.", file=sys.stderr)
        return 2
    per_run = total / len(runs) if runs else 0.0
    c = Campaign(a.out, runs, _factory(a), a.run_budget_tokens, pin, pout, a.spend_cap_usd, per_run,
                 workers=a.workers)
    rows = c.run()
    print(summary(rows))
    print(f"run list: {os.path.join(a.out, 'runs.csv')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
