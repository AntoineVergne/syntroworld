"""Participation (05 P3): share of (citizen, window cycle) pairs with a voluntary civic act.

Voluntary acts: registering a proposal, casting a ballot, attending a sitting (as a member
or observer), lodging an alert. A citizen counts from the first cycle they were present
for in full; a departed citizen counts as a pair with no act for every later cycle.
"""

from . import as_run

ACTS = ("proposal_registered", "ballot", "attend", "observe", "alert")


def p3_civic_breadth(run):
    run = as_run(run)
    acted = set()
    for t in ACTS:
        for e in run.of(t):
            if isinstance(e["actor"], int):
                acted.add((e["actor"], run.cycle_of_day(run.day_of(e["tick"]))))
    tpc = run.ticks_per_day * run.days_per_cycle
    first_full = {}
    for e in run.of("day_end"):
        for k in e["payload"]["holdings"]:
            first_full.setdefault(int(k), None)
    arrivals = {e["actor"]: e["tick"] for e in run.of("arrival")}
    for i in first_full:
        t = arrivals.get(i, 1)
        first_full[i] = 1 if t == 1 else (t - 1) // tpc + 1 + (0 if (t - 1) % tpc == 0 else 1)
    departed = {e["actor"]: run.cycle_of_day(run.day_of(e["tick"])) for e in run.of("departure")}
    num = den = 0
    for i, first in first_full.items():
        for c in run.window_cycles:
            if c < first:
                continue
            den += 1
            if i in departed and c > departed[i]:
                continue
            num += (i, c) in acted
    return num / den if den else None
