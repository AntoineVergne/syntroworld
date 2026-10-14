"""Participation (05 P3): share of (citizen, window cycle) pairs with a voluntary civic act.

Voluntary acts open to every citizen in every world (decision 26): registering a proposal,
lodging an alert, observing a sitting, and attending or voting in a sitting open to all
(a plenary). Attending or voting as a drawn member of one's own body is a duty of the
seat, not counted: otherwise P3 would track seats per citizen (05 §1 rule 2).

A citizen counts from the first cycle they were present for in full; a departed citizen
counts as a pair with no act for every later cycle.
"""

from . import as_run

ACTS = ("proposal_registered", "ballot", "attend", "observe", "alert")
OPEN_BODY = "plenary"


def voluntary_acts(run):
    """[(citizen, tick, type)] of counted civic acts (decisions 26 and 31)."""
    run = as_run(run)
    out = []
    seated = set()                  # (citizen, cycle) already credited for a seat
    for t in ("proposal_registered", "alert"):
        out += [(e["actor"], e["tick"], t) for e in run.of(t) if isinstance(e["actor"], int)]
    for e in run.of("observe"):     # only while a sitting is actually open
        if isinstance(e["actor"], int) and e["payload"].get("bodies", [None]):
            out.append((e["actor"], e["tick"], "observe"))
    for e in run.of("attend"):
        if not isinstance(e["actor"], int):
            continue
        bodies = e["payload"].get("bodies", [])
        if OPEN_BODY in bodies:
            out.append((e["actor"], e["tick"], "attend"))
        elif bodies:
            key = (e["actor"], run.cycle_of_day(run.day_of(e["tick"])))
            if key not in seated:
                seated.add(key)
                out.append((e["actor"], e["tick"], "seat"))
    for e in run.of("ballot"):
        if isinstance(e["actor"], int) and e["payload"].get("body") == OPEN_BODY:
            out.append((e["actor"], e["tick"], "ballot"))
    return out


def p3_civic_breadth(run):
    run = as_run(run)
    acted = {(c, run.cycle_of_day(run.day_of(t))) for c, t, _ in voluntary_acts(run)}
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
