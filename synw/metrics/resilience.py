"""Resilience (05 P4): shock-induced output loss against the no-shock twin."""

from . import as_run
from .economy import output_by_day


def p4_output_loss(run, twin):
    run, twin = as_run(run), as_run(twin)
    o, t = output_by_day(run), output_by_day(twin)
    base = sum(t.get(d, 0) for d in run.window)
    if base == 0:
        return None
    return 1.0 - sum(o.get(d, 0) for d in run.window) / base
