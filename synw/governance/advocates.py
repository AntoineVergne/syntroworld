"""Rule-based Advocates and the Suspensive Objection (02 §6).

- River: brief = projected River stock after one and three cycles. Objects if the
  three-cycle projection is below the sustainable level (K/2) and lower than without
  the proposal.
- Unborn: brief = projected Treasury balance and basket floor after three cycles.
  Objects if either is projected below zero or below 80% respectively, and lower than
  without the proposal.
Each Advocate may object at most once per proposal.
"""

FLOOR_LINE = 800  # per-mille


def river_brief(projection, K, sustainable=500):
    c1, c3 = projection["cycle1"], projection["cycle3"]
    line = K * sustainable // 1000
    objects = c3["river"] < line and c3["river"] < c3["river_base"]
    return {"advocate": "river", "cycle1": c1["river"], "cycle3": c3["river"],
            "cycle3_without": c3["river_base"], "objects": objects}


def unborn_brief(projection):
    c3 = projection["cycle3"]
    t_bad = c3["treasury"] < 0 and c3["treasury"] < c3["treasury_base"]
    f_bad = c3["floor"] < FLOOR_LINE and c3["floor"] < c3["floor_base"]
    return {"advocate": "unborn", "treasury": c3["treasury"], "treasury_without": c3["treasury_base"],
            "floor": c3["floor"], "floor_without": c3["floor_base"], "objects": t_bad or f_bad}


def hearing(gov, item, tick, advocates=("river", "unborn")):
    """Give briefs; lodge objections (once per Advocate per proposal). Returns objections lodged now."""
    proj = gov.projection(item["effect"])
    K = gov.w.river_K
    sus = gov.w.cfg["river"]["sustainable"]
    lodged = []
    for name in advocates:
        brief = river_brief(proj, K, sus) if name == "river" else unborn_brief(proj)
        gov.w.log.emit(tick, "advocate_brief", f"advocate:{name}",
                       {"proposal": item["id"], **{k: (int(v) if isinstance(v, bool) else v)
                                                   for k, v in brief.items()}})
        if brief["objects"] and name not in item["objections"]:
            item["objections"][name] = tick
            lodged.append(name)
            gov.w.log.emit(tick, "objection", f"advocate:{name}", {"proposal": item["id"]})
    return lodged
