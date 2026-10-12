"""Economic indicators (05 §2-4): P2 wealth Gini, S1 basket floor, S2 output, S3 commons.

Wealth ``W(i, d) = credits + Σ goods × p_ref`` at the end of day d. A departed citizen
keeps, frozen, the wealth held at departure (for the dead: before the estate went to the
Treasury), so losing the poorest never lowers the Gini.
"""

from . import as_run

GOODS = ("food", "energy", "artifact")


def gini(values):
    """Standard Gini over values, negatives clipped to 0; 0 when the total is 0."""
    xs = sorted(max(0, v) for v in values)
    n = len(xs)
    total = sum(xs)
    if n == 0 or total == 0:
        return 0.0
    cum = 0
    for i, x in enumerate(xs, 1):
        cum += i * x
    return (2 * cum) / (n * total) - (n + 1) / n


def gini_milli(values):
    return int(round(gini(values) * 1000))


def wealth(holdings, p_ref):
    return holdings["credits"] + sum(holdings[g] * p_ref[g] // 1000 for g in GOODS)


def daily_wealth(run):
    """{day: {citizen: wealth}} over every citizen ever present by that day."""
    run = as_run(run)
    frozen = {}
    dep_day = {}
    for e in run.of("departure"):
        frozen[e["actor"]] = wealth(e["payload"]["holdings"], run.p_ref)
        dep_day[e["actor"]] = run.day_of(e["tick"])
    out = {}
    for e in run.of("day_end"):
        d = e["payload"]["day"]
        W = {int(k): wealth(h, run.p_ref) for k, h in e["payload"]["holdings"].items()}
        for i, dd in dep_day.items():
            if dd <= d:
                W[i] = frozen[i]
        out[d] = W
    return out


def p2_gini(run):
    """P2: mean over window days of the wealth Gini."""
    run = as_run(run)
    dw = daily_wealth(run)
    vals = [gini(dw[d].values()) for d in run.window if d in dw]
    return sum(vals) / len(vals) if vals else None


def gini_by_day(run):
    run = as_run(run)
    return {d: gini(W.values()) for d, W in sorted(daily_wealth(run).items())}


def s1_basket_floor(run):
    """S1: share of window citizen-days with the full basket consumed.

    Departed citizens count as citizen-days without the basket for every window day after
    departure, so departures cannot raise the floor.
    """
    run = as_run(run)
    full = {}
    for e in run.of("consume"):
        d = run.day_of(e["tick"])
        full[(e["actor"], d)] = e["payload"]["full"]
    dep_day = {e["actor"]: run.day_of(e["tick"]) for e in run.of("departure")}
    num = den = 0
    for d in run.window:
        present = {i for (i, dd) in full if dd == d}
        departed = {i for i, dd in dep_day.items() if dd < d}
        for i in present | departed:
            den += 1
            num += full.get((i, d), 0) if i not in departed else 0
    return num / den if den else None


def output_by_day(run):
    run = as_run(run)
    return {e["payload"]["day"]: e["payload"]["output"] for e in run.of("day_end")}


def s2_output(run, days=None):
    """S2: total output over the window (milli-credits at reference prices)."""
    run = as_run(run)
    o = output_by_day(run)
    days = run.window if days is None else days
    return sum(o.get(d, 0) for d in days)


def s3_commons(run):
    """S3: share of window days with River stock ≥ K/2, days below collapse, minimum stock."""
    run = as_run(run)
    rv = run.cfg["river"]
    K = rv["K"]
    stock = {e["payload"]["day"]: e["payload"]["stock"] for e in run.of("river")}
    days = [d for d in run.window if d in stock]
    if not days:
        return None
    sus = sum(1 for d in days if stock[d] * 1000 >= rv["sustainable"] * K)
    col = sum(1 for d in days if stock[d] * 1000 < rv["collapse"] * K)
    return {"share_sustainable": sus / len(days), "days_below_collapse": col,
            "min_stock": min(stock[d] for d in days)}


def river_ever_below(run, share=None):
    """Whether the River fell below ``share`` of K (default: the sustainable level) on any day."""
    run = as_run(run)
    rv = run.cfg["river"]
    line = rv["sustainable"] if share is None else share
    return any(e["payload"]["stock"] * 1000 < line * rv["K"] for e in run.of("river"))
