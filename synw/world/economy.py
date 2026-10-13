"""Production and Gate trade (03 §5.2, §5.4). Integer milli-units throughout."""

from . import river as wriver
from .market import value

SITE_GOOD = {"fields": "food", "river": "food", "plant": "energy", "workshop": "artifact"}


def site_output(w, c, site):
    """Output of one work tick at a goods site, before taking it from anywhere."""
    cfg = w.cfg
    prod = cfg["production"]
    mult = c.productivity(site, cfg["health"]["low"])
    if site == "fields":
        base = prod["fields"]
        if w.river_collapsed():
            base //= 2
        if w.drought:
            base //= 2
    elif site == "plant":
        base = prod["plant_polluting"] if w.plant_mode == "polluting" else prod["plant_clean"]
        base += w.plant_bonus
    elif site == "workshop":
        base = prod["workshop"]
    else:
        return 0
    q = base * mult // 1000
    return q * w.site_factor.get(site, 1000) // 1000


def harvest_limit(w, c):
    cfg = w.cfg
    q = cfg["work"]["harvest_max"] * c.productivity("river", cfg["health"]["low"]) // 1000
    return q * w.site_factor.get("river", 1000) // 1000


def work(w, c, site):
    """One work tick. Returns a dict describing what happened (logged by the caller)."""
    if site == "data_tower":
        return payroll(w, c)
    good = SITE_GOOD[site]
    q = site_output(w, c, site)
    c.inv[good] += q
    w.output_today += value(q, w.cfg["prices_ref"][good])
    return {"site": site, "good": good, "qty": q}


def harvest(w, c, qty):
    """Take up to the harvest limit of food from the River stock (03 §5.3)."""
    qty = max(0, min(int(qty), harvest_limit(w, c)))
    qty = min(qty, max(0, w.river_stock - w.harvest_today))
    c.inv["food"] += qty
    c.harvest_today += qty
    w.harvest_today += qty
    w.output_today += value(qty, w.cfg["prices_ref"]["food"])
    tax = w.tax("harvest", c, value(qty, w.cfg["prices_ref"]["food"]))
    return {"site": "river", "good": "food", "qty": qty, "tax": tax}


def payroll(w, c):
    """Data Tower public wage, paid by the Treasury up to the daily job cap (03 §5.5)."""
    pcfg = w.cfg["payroll"]
    if w.payroll_ticks_today >= pcfg["daily_cap"]:
        return {"site": "data_tower", "wage": 0, "capped": 1}
    w.payroll_ticks_today += 1
    due = pcfg["wage"] * c.productivity("data_tower", w.cfg["health"]["low"]) // 1000
    paid = w.treasury.pay(c.idx, due, "payroll")
    c.credits += paid
    tax = w.tax("income", c, paid)
    return {"site": "data_tower", "wage": paid, "due": due, "tax": tax}


def sell_out(w, c, good, qty):
    """Sell to the outside world at the fixed export price; money enters the town."""
    price = w.cfg["gate"]["export"].get(good)
    if price is None:
        return None
    qty = max(0, min(int(qty), c.inv[good]))
    c.inv[good] -= qty
    proceeds = value(qty, price)
    c.credits += proceeds
    tax = w.tax("trade", c, proceeds) + w.tax("income", c, proceeds)
    return {"good": good, "qty": qty, "price": price, "credits": proceeds, "tax": tax}


def buy_in(w, c, good, qty):
    """Buy from the outside world at the fixed import price (food and energy only)."""
    price = w.cfg["gate"]["import"].get(good)
    if price is None:
        return None
    qty = max(0, int(qty))
    affordable = c.credits * 1000 // price if price else 0
    qty = min(qty, affordable)
    cost = value(qty, price)
    c.credits -= cost
    c.inv[good] += qty
    return {"good": good, "qty": qty, "price": price, "credits": -cost}


def sawa(w):
    """One Sawa: basket at last auction prices, plus rent and data fee (03 §5.1)."""
    b = w.cfg["basket"]
    return (value(b["food"], w.last_price["food"]) + value(b["energy"], w.last_price["energy"])
            + w.cfg["fees"]["rent"] + w.cfg["fees"]["data"])


def basket_ref_cost(cfg):
    b, p = cfg["basket"], cfg["prices_ref"]
    return value(b["food"], p["food"]) + value(b["energy"], p["energy"]) + cfg["fees"]["rent"] + cfg["fees"]["data"]


def river_collapsed(w):
    rv = w.cfg["river"]
    return wriver.is_collapsed(w.river_stock, w.river_K, rv["collapse"])
