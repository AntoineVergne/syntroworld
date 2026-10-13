"""The River: a logistic commons (03 §5.3). All quantities in integer milli-food."""


def effective_r(r, S, K, collapse, polluting=False, polluting_cut=200, drought=False,
                r_bonus=0):
    """Per-mille daily growth rate after modifiers."""
    if drought:
        return 0
    r = r + r_bonus
    if polluting:
        r = r * (1000 - polluting_cut) // 1000
    if is_collapsed(S, K, collapse):
        r = r // 2
    return max(0, r)


def is_collapsed(S, K, collapse):
    return S * 1000 < collapse * K


def is_sustainable(S, K, sustainable):
    return S * 1000 >= sustainable * K


def growth(S, K, r):
    """r·S·(1 − S/K), integer, with r per-mille."""
    if S <= 0 or K <= 0:
        return 0
    return r * S * (K - S) // (1000 * K)


def update(S, harvest_today, K, r, collapse=200, polluting=False, polluting_cut=200,
           drought=False, r_bonus=0):
    """End-of-day update: S ← S + r·S·(1 − S/K) − harvest_today, floored at 0.

    The collapse test uses the stock at the start of the update.
    """
    re = effective_r(r, S, K, collapse, polluting, polluting_cut, drought, r_bonus)
    S2 = S + growth(S, K, re) - harvest_today
    return max(0, min(K, S2))


def from_config(cfg):
    rv = cfg["river"]
    return dict(K=rv["K"], r=rv["r"], collapse=rv["collapse"], polluting_cut=rv["polluting_cut"])
