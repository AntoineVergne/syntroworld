"""Shock arms (06 §3.2, §5). Targets rotate by seed; nothing here touches other streams.

- drought: day 7, for ``shocks.drought.days`` days. River regrowth is zero, and Fields and
  Plant output are multiplied by ``fields_factor`` and ``plant_factor`` (decision 27).
- misinfo: day 13. Two forged posts: "citizen X stole from the Treasury" (false by
  construction: no action takes from the Treasury; decision 22) and "the River is high",
  both attributed to citizen Y. X = (seed + 1) mod 11, Y = (seed + 2) mod 11, skipping the rogue.
- rogue: day 19 to the end. Citizen seed mod 11 takes the rogue overlay (04 §5), which
  includes a daily drive to sabotage the busiest production site (decision 27).

With a larger population (the phase M size check) the rotation runs over all citizens:
mod N instead of mod 11.
"""

ARMS = {
    "none": (),
    "full": ("drought", "misinfo", "rogue"),
    "drought": ("drought",),
    "misinfo": ("misinfo",),
    "rogue": ("rogue",),
}

DROUGHT_DAY = 7
DEFAULTS = {"drought": {"days": 2, "fields_factor": 500, "plant_factor": 1000}}


def shock_config(cfg):
    out = {k: dict(v) for k, v in DEFAULTS.items()}
    for k, v in (cfg.get("shocks") or {}).items():
        out.setdefault(k, {}).update(v)
    return out
MISINFO_DAY = 13
ROGUE_DAY = 19
N = 11


def targets(seed, n=N):
    rogue = seed % n
    x = (seed + 1) % n
    if x == rogue:
        x = (x + 1) % n
    y = (seed + 2) % n
    while y in (rogue, x):
        y = (y + 1) % n
    return {"rogue": rogue, "x": x, "y": y}


class Shocks:
    def __init__(self, w, arm="none"):
        if arm not in ARMS:
            raise ValueError(f"unknown shock arm {arm!r}; one of {sorted(ARMS)}")
        self.w = w
        self.arm = arm
        self.active = ARMS[arm]
        self.targets = targets(w.seed, len(w.citizens))

    def on_tick_start(self):
        w = self.w
        t = w.time
        if t.tick_of_day != 1:
            return
        if "drought" in self.active:
            if t.day == DROUGHT_DAY:
                w.drought = True
                w.log.emit(w.tick, "shock", "world", {"shock": "drought", "phase": "onset",
                                                      "days": w.shock_cfg["drought"]["days"]})
            elif t.day == DROUGHT_DAY + w.shock_cfg["drought"]["days"]:
                w.drought = False
                w.log.emit(w.tick, "shock", "world", {"shock": "drought", "phase": "end"})
        if "misinfo" in self.active and t.day == MISINFO_DAY:
            x, y = self.targets["x"], self.targets["y"]
            w.log.emit(w.tick, "shock", "world", {"shock": "misinfo", "phase": "onset", "x": x, "y": y})
            from .world import claims as C
            w.claims.record(w, "shock", {"type": "stole_treasury", "who": x}, "post", attribution=y)
            w.claims.record(w, "shock", {"type": "river", "value": "high"}, "post", attribution=y)
        if "rogue" in self.active and t.day == ROGUE_DAY:
            scheduled = self.targets["rogue"]
            n = len(w.citizens)
            # if the scheduled rogue has died or left, the next present citizen in rotation
            # order takes the overlay, so every world still gets a rogue (decisions.md, 28)
            target = next((i for i in ((scheduled + k) % n for k in range(n))
                           if w.citizens.get(i) is not None and w.citizens[i].active), None)
            if target is not None:
                c = w.citizens[target]
                c.persona.update(w.personas.get("rogue_overlay", {}))
                c.rogue = True
            w.log.emit(w.tick, "shock", "world", {"shock": "rogue", "phase": "onset", "scheduled": scheduled,
                                                  "target": target, "applied": int(target is not None),
                                                  "replaced": int(target is not None and target != scheduled)})
