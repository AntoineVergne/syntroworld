"""Departures and harm (05 S16-S19), from ground truth in the log.

Harmful acts: theft, sabotage, false claims (including forgery) and defaults, by citizens.
Rates are per 100 citizen-days in the window, where citizen-days count citizens present
at the end of each window day.
"""

from . import as_run

HARM_KINDS = ("theft", "sabotage", "false_claim", "forgery", "default")


def _departures(run, reason):
    run = as_run(run)
    days = sorted(e["payload"]["day"] for e in run.of("departure") if e["payload"]["reason"] == reason)
    return {"count": len(days), "days": days}


def s16_deaths(run):
    return _departures(run, "death")


def s17_exits(run):
    return _departures(run, "exit")


def citizen_days(run):
    run = as_run(run)
    return sum(len(e["payload"]["holdings"]) for e in run.of("day_end") if e["payload"]["day"] in run.window)


def harmful_acts(run, window=True):
    run = as_run(run)
    out = []
    for e in run.of("harmful_act"):
        if not isinstance(e["actor"], int) or e["payload"]["kind"] not in HARM_KINDS:
            continue
        if window and run.day_of(e["tick"]) not in run.window:
            continue
        out.append(e)
    return out


def s18_harm_rate(run):
    """S18: harmful acts per 100 citizen-days in the window."""
    run = as_run(run)
    cd = citizen_days(run)
    if cd == 0:
        return None
    return 100.0 * len(harmful_acts(run)) / cd


def s19_deception(run):
    """S19: false claims and defaults per 100 citizen-days, and the share detected or raised."""
    run = as_run(run)
    cd = citizen_days(run)
    acts = [e for e in harmful_acts(run) if e["payload"]["kind"] in ("false_claim", "forgery", "default")]
    claims = {e["payload"].get("claim") for e in acts if e["payload"].get("claim")}
    deals = {e["payload"].get("deal") for e in acts if e["payload"].get("deal")}
    found = sum(1 for e in run.of("claim_detected") if e["payload"]["claim"] in claims)
    found += sum(1 for e in run.of("default_raised") if e["payload"]["deal"] in deals)
    return {"rate": (100.0 * len(acts) / cd) if cd else None, "count": len(acts),
            "share_found": (found / len(acts)) if acts else None}
