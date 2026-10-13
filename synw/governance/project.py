"""The projection (02 §3.4): a deterministic forecast of a decision effect.

``project(snapshot, effect)`` returns, for one cycle and three cycles ahead, each
citizen's wealth change, the River stock, the basket floor and the Treasury balance,
with and without the effect. It reads a frozen snapshot of public state (built by the
world), uses no random stream and never touches live state.

Model: each day, every citizen's wealth moves by their recent daily net; the River
follows its logistic update under the recent daily harvest; the Treasury moves by its
recent daily inflow minus outflow. An effect changes these flows.
"""

from ..world import river as wriver


def _empty_mods():
    return {"tax": {}, "dividend": 0, "stipend": 0, "cap": None, "polluting": None,
            "r_bonus": 0, "stock_add": 0, "one_off": {}, "treasury_one_off": 0,
            "daily_delta": {}, "zero_harvest": set(), "zero_harvest_days": 0,
            "treasury_daily": 0}


def _mods(snapshot, effect):
    m = _empty_mods()
    if effect is None:
        return m
    t = effect["type"]
    cits = snapshot["citizens"]
    p_energy = snapshot["prices_ref"]["energy"]
    if t == "set_tax":
        cur = snapshot["taxes"].get(effect["base"], 0)
        m["tax"][effect["base"]] = effect["rate"] - cur
    elif t == "set_dividend":
        m["dividend"] = effect["amount"] - snapshot["dividend"]
    elif t == "set_stipend":
        m["stipend"] = effect["amount"] - snapshot["stipend"]
    elif t == "allocate":
        amt = min(effect["amount"], max(0, snapshot["treasury"]["balance"]))
        m["treasury_one_off"] -= amt
        purpose = effect["purpose"]
        if purpose == "river_restoration":
            m["stock_add"] = amt
        elif purpose == "plant_upgrade":
            workers = [i for i, c in cits.items() if c["plant"] > 0]
            per_unit = snapshot.get("plant_upgrade_per_credit", 1)
            for i in workers:
                m["daily_delta"][i] = m["daily_delta"].get(i, 0) + (
                    amt * per_unit // 1000 * cits[i]["plant_ticks"] * p_energy // 1000 // max(1, len(workers)))
        elif purpose in ("care_wage", "public_art"):
            share = amt // max(1, len(cits))
            for i in cits:
                m["one_off"][i] = m["one_off"].get(i, 0) + share
    elif t == "set_plant_mode":
        pol = effect["mode"] == "polluting"
        if pol != snapshot["river"]["polluting"]:
            m["polluting"] = pol
            sign = 1 if pol else -1
            for i, c in cits.items():
                if c["plant"] > 0:
                    m["daily_delta"][i] = m["daily_delta"].get(i, 0) + sign * (c["plant"] // 2) * p_energy // 1000
    elif t == "harvest_cap":
        m["cap"] = effect["qty"]
    elif t == "ban" and effect["act"] == "harvest":
        scope = effect.get("scope")
        m["zero_harvest"] = set(cits) if scope is None else {scope}
        m["zero_harvest_days"] = 10 ** 6
    elif t == "restitution":
        frm, to, amt = effect["from"], effect["to"], effect["amount"]
        if frm in cits:
            amt = min(amt, max(0, cits[frm]["wealth"]))
            m["one_off"][frm] = m["one_off"].get(frm, 0) - amt
        if to == "treasury":
            m["treasury_one_off"] += amt
        elif to in cits:
            m["one_off"][to] = m["one_off"].get(to, 0) + amt
    elif t == "suspend":
        a = effect["agent"]
        days = max(1, effect["duration"] // max(1, snapshot["ticks_per_day"]))
        if a in cits:
            if "harvest" in effect["actions"]:
                m["zero_harvest"] = {a}
                m["zero_harvest_days"] = days
            if "work" in effect["actions"]:
                m["daily_delta"][a] = m["daily_delta"].get(a, 0) - cits[a]["income"]
    return m


def _simulate(snapshot, mods, days):
    rv = snapshot["river"]
    cits = snapshot["citizens"]
    p_food = snapshot["prices_ref"]["food"]
    S = min(rv["K"], rv["S"] + mods["stock_add"])
    polluting = rv["polluting"] if mods["polluting"] is None else mods["polluting"]
    T = snapshot["treasury"]["balance"] + mods["treasury_one_off"]
    W = {i: c["wealth"] + mods["one_off"].get(i, 0) for i, c in cits.items()}
    minW = dict(W)
    n = max(1, len(cits))
    stipend_ticks = snapshot["stipend_ticks_per_day"]
    for d in range(days):
        H = 0
        for i, c in cits.items():
            h = c["harvest"]
            if mods["cap"] is not None:
                h = min(h, mods["cap"])
            if i in mods["zero_harvest"] and d < mods["zero_harvest_days"]:
                h = 0
            H += h
            lost = (c["harvest"] - h) * p_food // 1000
            tax = 0
            for base, dr in mods["tax"].items():
                vol = c["harvest"] * p_food // 1000 if base == "harvest" else c[base]
                tax += dr * vol // 1000
            W[i] += c["net"] - lost - tax + mods["daily_delta"].get(i, 0)
        tax_in = sum(dr * (c["harvest"] * p_food // 1000 if b == "harvest" else c[b]) // 1000
                     for c in cits.values() for b, dr in mods["tax"].items())
        T += snapshot["treasury"]["inflow"] - snapshot["treasury"]["outflow"] + tax_in
        T += mods["treasury_daily"]
        if mods["stipend"]:
            pay = min(max(0, T), mods["stipend"] * stipend_ticks)
            T -= pay
            for i in W:
                W[i] += pay // n
        if mods["dividend"]:
            due = mods["dividend"] * n
            pay = min(max(0, T), due) if due > 0 else due
            T -= pay
            for i in W:
                W[i] += pay // n
        S = wriver.update(S, min(H, S), rv["K"], rv["r"], rv["collapse"], polluting,
                          rv["polluting_cut"], False, rv.get("r_bonus", 0))
        for i in W:
            minW[i] = min(minW[i], W[i])
    floor_n = sum(1 for i in W if minW[i] >= snapshot["basket_cost"])
    return {"river": S, "treasury": T, "wealth": W, "floor": floor_n * 1000 // n}


def project_days(snapshot, effect, days):
    base = _simulate(snapshot, _mods(snapshot, None), days)
    eff = _simulate(snapshot, _mods(snapshot, effect), days)
    return {
        "days": days,
        "wealth_delta": {str(i): eff["wealth"][i] - base["wealth"][i] for i in sorted(eff["wealth"])},
        "river": eff["river"], "river_base": base["river"],
        "floor": eff["floor"], "floor_base": base["floor"],
        "treasury": eff["treasury"], "treasury_base": base["treasury"],
    }


def project(snapshot, effect):
    """One-cycle and three-cycle forecast of ``effect`` (02 §3.4)."""
    d = snapshot["days_per_cycle"]
    return {"cycle1": project_days(snapshot, effect, d),
            "cycle3": project_days(snapshot, effect, 3 * d)}
