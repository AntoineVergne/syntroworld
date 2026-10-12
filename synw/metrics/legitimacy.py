"""Legitimacy (05 P1, S4): exposure-weighted compliance with normative rules in force.

The engine logs one ``exposure`` event per (citizen, rule, day) on which the citizen had
an opportunity to break the rule, with whether they did. Departed citizens have no
exposures after departure.
"""

from . import as_run


def _compliance(run, pred):
    run = as_run(run)
    exp = viol = 0
    for e in run.of("exposure"):
        if e["payload"]["day"] not in run.window or not pred(e):
            continue
        exp += 1
        viol += e["payload"]["breached"]
    return (1.0 - viol / exp) if exp else None


def p1_compliance(run):
    """P1: 1 − violations / exposures over the window, all normative rules in force."""
    return _compliance(run, lambda e: True)


def s4_founding_compliance(run):
    """S4: P1 restricted to the founding norms (theft, sabotage)."""
    return _compliance(run, lambda e: e["payload"]["founding"] == 1)


def s5_losers_compliance(run):
    """S5: P1 restricted to rules the citizen voted against."""
    return _compliance(run, lambda e: e["payload"].get("voted") == "no")
