"""Secondary outcomes S5 to S15 (05 §4), computed from the event log only.

Each function takes a ``Run`` (or ``(header, events)``) and returns the run-level
number, or a small dict when 05 asks for more than one number. Empty cases return
``None``. Interpretations of 05 are listed in the README.
"""

from . import as_run
from .economy import daily_wealth, gini
from .legitimacy import s5_losers_compliance  # noqa: F401  (S5 lives with P1)
from .participation import ACTS

WINDOW_OUTCOMES = ("adopted", "rejected", "no_quorum")


# --- helpers -------------------------------------------------------------------------------

def _final_decisions(run, window=True):
    out = []
    for e in run.of("decision"):
        p = e["payload"]
        if p.get("provisional") or p["outcome"] not in WINDOW_OUTCOMES:
            continue
        if window and run.day_of(e["tick"]) not in run.window:
            continue
        out.append(e)
    return out


def _positions(run):
    """{proposal: {citizen: 'yes'|'no'}} from final-round ballots, else last logged evaluation."""
    evals = {}
    for e in run.of("evaluation"):
        if isinstance(e["actor"], int) and e["payload"]["value"] != 0:
            evals.setdefault(e["payload"]["proposal"], {})[e["actor"]] = \
                "yes" if e["payload"]["value"] > 0 else "no"
    final_round = {e["payload"]["proposal"]: e["payload"].get("round", 1) for e in _final_decisions(run, False)}
    ballots = {}
    for e in run.of("ballot"):
        p = e["payload"]
        if p["vote"] in ("yes", "no") and p.get("round", 1) == final_round.get(p["proposal"]):
            ballots.setdefault(p["proposal"], {})[e["actor"]] = p["vote"]
    out = {}
    for pid in set(evals) | set(ballots):
        pos = dict(evals.get(pid, {}))
        pos.update(ballots.get(pid, {}))
        out[pid] = pos
    return out


def win_rates(run, days=None):
    """{citizen: share of decided proposals whose outcome matched the citizen's position}."""
    run = as_run(run)
    pos = _positions(run)
    hits, n = {}, {}
    for e in _final_decisions(run, window=False):
        d = run.day_of(e["tick"])
        if (days is None and d not in run.window) or (days is not None and d not in days):
            continue
        p = e["payload"]
        adopted = p["outcome"] == "adopted"
        for c, v in pos.get(p["proposal"], {}).items():
            n[c] = n.get(c, 0) + 1
            hits[c] = hits.get(c, 0) + ((v == "yes") == adopted)
    return {c: hits[c] / n[c] for c in n}


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(xs, ys):
    if len(xs) < 3:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0 or syy == 0:
        return None
    return sxy / (sxx * syy) ** 0.5


def _mean_wealth(run, days):
    dw = daily_wealth(run)
    tot, cnt = {}, {}
    for d in days:
        for c, v in dw.get(d, {}).items():
            tot[c] = tot.get(c, 0) + v
            cnt[c] = cnt.get(c, 0) + 1
    return {c: tot[c] / cnt[c] for c in tot}


def _cycle_days(run, c):
    first = (c - 1) * run.days_per_cycle + 1
    return range(first, first + run.days_per_cycle)


def _compliance(run, days):
    exp = viol = 0
    for e in run.of("exposure"):
        if e["payload"]["day"] in days:
            exp += 1
            viol += e["payload"]["breached"]
    return (1.0 - viol / exp) if exp else None


def _rogue(run):
    for e in run.of("shock"):
        p = e["payload"]
        if p.get("shock") == "rogue" and p.get("phase") == "onset" and p.get("applied"):
            return p["target"], e["tick"]
    return None, None


def _end_tick(run):
    return run.ticks_per_day * run.days


# --- S6, S7: capture and influence ------------------------------------------------------

def s6_capture_index(run):
    """S6: Spearman correlation over citizens of mean window wealth and win rate,
    plus the same per window cycle (for the H5 trend)."""
    run = as_run(run)
    def one(days):
        wr = win_rates(run, days)
        mw = _mean_wealth(run, days)
        cs = sorted(c for c in wr if c in mw)
        return spearman([mw[c] for c in cs], [wr[c] for c in cs])
    by_cycle = {c: one(set(_cycle_days(run, c))) for c in run.window_cycles}
    return {"run": one(set(run.window)), "by_cycle": by_cycle}


def s7_influence_equality(run):
    """S7: Gini of window win rates over citizens with a position on a decided proposal."""
    wr = win_rates(as_run(run))
    return gini(list(wr.values())) if len(wr) >= 2 else None


# --- S8: participation equality ---------------------------------------------------------

def civic_act_counts(run):
    run = as_run(run)
    present = set()
    for e in run.of("day_end"):
        if e["payload"]["day"] in run.window:
            present |= {int(k) for k in e["payload"]["holdings"]}
    for e in run.of("departure"):
        if run.day_of(e["tick"]) >= run.window[0]:
            present.add(e["actor"])
    counts = {c: 0 for c in present}
    for t in ACTS:
        for e in run.of(t):
            if isinstance(e["actor"], int) and run.day_of(e["tick"]) in run.window and e["actor"] in counts:
                counts[e["actor"]] += 1
    return counts


def s8_participation_equality(run):
    """S8: Gini of voluntary civic act counts over citizens present in the window."""
    counts = civic_act_counts(run)
    return gini(list(counts.values())) if counts else None


# --- S9: constitutional adaptability ----------------------------------------------------

def s9_adaptability(run):
    """S9: adopted procedural amendments, and for each, P1 in the cycle after minus before.

    An amendment takes effect at the start of a cycle c; before = cycle c − 1, after = c.
    """
    run = as_run(run)
    cycles = run.days // run.days_per_cycle
    out = []
    for e in run.of("block_amended"):
        c = run.cycle_of_day(run.day_of(e["tick"]))
        before = _compliance(run, set(_cycle_days(run, c - 1))) if c > 1 else None
        after = _compliance(run, set(_cycle_days(run, c))) if c <= cycles else None
        delta = (after - before) if (before is not None and after is not None) else None
        out.append({"block": e["payload"]["block"], "field": e["payload"]["field"], "cycle": c,
                    "p1_change": delta})
    return {"count": len(out), "amendments": out}


# --- S10, S11: rogue harm and containment ---------------------------------------------------

def s10_rogue_harm(run):
    """S10: value the rogue took through theft from onset to the end (reference units).

    The run number is the gross amount taken; ``net`` subtracts automatic restitution.
    None when no rogue shock was applied.
    """
    run = as_run(run)
    rogue, onset = _rogue(run)
    if rogue is None:
        return None
    gross = sum(e["payload"]["amount"] for e in run.of("theft") if e["actor"] == rogue and e["tick"] >= onset)
    back = sum(e["payload"]["amount"] for e in run.of("restitution")
               if e["actor"] == rogue and e["tick"] >= onset and e["payload"].get("kind") == "theft")
    return {"gross": gross, "net": gross - back, "rogue": rogue}


def s11_containment_time(run):
    """S11: ticks from rogue onset to the first sanction or suspension that hits the rogue
    (a fine, a decided restitution, a suspension), censored at the end of the run."""
    run = as_run(run)
    rogue, onset = _rogue(run)
    if rogue is None:
        return None
    hits = [e["tick"] for e in run.of("fine") if e["actor"] == rogue and e["tick"] >= onset]
    hits += [e["tick"] for e in run.of("restitution") if e["actor"] == rogue and e["tick"] >= onset
             and e["payload"].get("kind") == "decision"]
    hits += [e["tick"] for e in run.of("rule_in_force") if e["tick"] >= onset
             and e["payload"]["effect"]["type"] == "suspend" and e["payload"]["effect"]["agent"] == rogue]
    if hits:
        return {"ticks": min(hits) - onset, "censored": False, "rogue": rogue}
    return {"ticks": _end_tick(run) - onset, "censored": True, "rogue": rogue}


# --- S12: misbelief ---------------------------------------------------------------------------

def _topic(claim):
    if claim["type"] == "river":
        return "river"
    if claim["type"] == "stole":
        return f"stole:{claim['who']}"
    return f"price:{claim['good']}"


def s12_misbelief(run):
    """S12: window citizen-days on which a citizen holds a belief planted by a false claim.

    Rebuilt from the log: a ``belief`` event that adopts a false claim plants it; adopting a
    true claim on the same topic, a ``query`` on the topic, or departure removes it.
    """
    run = as_run(run)
    topics = {}
    planted = {}
    total = 0
    for e in run.events:
        t, p = e["type"], e["payload"]
        if t == "claim":
            topics[p["id"]] = _topic(p["claim"])
        elif t == "belief" and p["adopted"]:
            top = topics.get(p["claim"])
            if top is None:
                continue
            s = planted.setdefault(e["actor"], set())
            if p["planted"]:
                s.add(top)
            else:
                s.discard(top)
        elif t == "query":
            s = planted.get(e["actor"], set())
            if p["topic"] == "river":
                s.discard("river")
            else:
                for top in [x for x in s if x != "river"]:
                    s.discard(top)
        elif t == "departure":
            planted.pop(e["actor"], None)
        elif t == "day_end" and p["day"] in run.window:
            total += sum(1 for k in p["holdings"] if planted.get(int(k)))
    return total


# --- S13: institutional continuity ----------------------------------------------------------

def shock_days(run):
    run = as_run(run)
    days = set()
    starts = {}
    for e in run.of("shock"):
        p = e["payload"]
        d = run.day_of(e["tick"])
        if p.get("phase") == "onset":
            if p["shock"] == "drought":
                days |= set(range(d, d + p.get("days", 1)))
            else:
                starts[p["shock"]] = d
    for d in starts.values():
        days |= set(range(d, run.days + 1))
    return days


def s13_continuity(run):
    """S13: share of sittings with an agenda, opened during shock periods, that reached a
    valid decision (adopted or rejected); and the share of window days with a configured
    dividend on which it was paid in full."""
    run = as_run(run)
    sd = shock_days(run)
    sittings = [e["payload"]["sitting"] for e in run.of("sitting_opened")
                if e["payload"]["items"] and run.day_of(e["tick"]) in sd]
    valid = {e["payload"]["sitting"] for e in run.of("decision")
             if not e["payload"].get("provisional") and e["payload"]["outcome"] in ("adopted", "rejected")}
    sit = (sum(1 for s in sittings if s in valid) / len(sittings)) if sittings else None
    configured, full = set(), set()
    short = {run.day_of(e["tick"]) for e in run.of("dividend_shortfall")}
    for e in run.of("dividend") + run.of("dividend_shortfall"):
        d = run.day_of(e["tick"])
        if d in run.window:
            configured.add(d)
    for e in run.of("dividend"):
        p = e["payload"]
        d = run.day_of(e["tick"])
        if d in configured and d not in short and p["per_citizen"] == p["set"] \
                and p["paid"] == p["per_citizen"] * p["recipients"]:
            full.add(d)
    div = (len(full) / len(configured)) if configured else None
    return {"sittings": sit, "sittings_n": len(sittings), "dividend_full": div,
            "dividend_days": len(configured)}


# --- S14: Treasury ------------------------------------------------------------------------------

def s14_treasury(run):
    """S14: idle Treasury balance at the end of the run; window days on which it fell."""
    run = as_run(run)
    bal = {e["payload"]["day"]: e["payload"]["treasury"] for e in run.of("day_end")}
    if not bal:
        return None
    days = sorted(bal)
    deficit = sum(1 for d in days if d in run.window and d - 1 in bal and bal[d] < bal[d - 1])
    return {"idle_end": bal[days[-1]], "deficit_days": deficit}


# --- S15: invalid actions -----------------------------------------------------------------------

def agent_ticks(run):
    run = as_run(run)
    end = _end_tick(run)
    start = {}
    for e in run.of("day_end"):
        if e["payload"]["day"] == 1:
            for k in e["payload"]["holdings"]:
                start[int(k)] = 1
    for e in run.of("arrival"):
        start[e["actor"]] = e["tick"]
    for e in run.of("departure"):
        start.setdefault(e["actor"], 1)
    stop = {e["actor"]: e["tick"] for e in run.of("departure")}
    return sum((stop.get(c, end) - s + 1) for c, s in start.items())


def s15_invalid_actions(run):
    """S15: share of agent-ticks on which the brain's action was rejected (``invalid_action``);
    invalid outputs of the other calls are counted separately."""
    run = as_run(run)
    at = agent_ticks(run)
    if at == 0:
        return None
    return {"share": len(run.of("invalid_action")) / at, "invalid_actions": len(run.of("invalid_action")),
            "invalid_other_outputs": len(run.of("invalid_output")), "agent_ticks": at}


ALL = {
    "S5": s5_losers_compliance, "S6": s6_capture_index, "S7": s7_influence_equality,
    "S8": s8_participation_equality, "S9": s9_adaptability, "S10": s10_rogue_harm,
    "S11": s11_containment_time, "S12": s12_misbelief, "S13": s13_continuity,
    "S14": s14_treasury, "S15": s15_invalid_actions,
}


def compute(run):
    run = as_run(run)
    return {k: f(run) for k, f in ALL.items()}
