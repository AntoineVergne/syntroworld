"""Shock arms (06 §3.2, §5). Targets rotate by seed; nothing here touches other streams.

- drought: day 7, 2 days. River regrowth is zero and Fields output is halved.
- misinfo: day 13. Two forged posts: "citizen X stole from the Treasury" (false by
  construction: no action takes from the Treasury; decision 22) and "the River is high",
  both attributed to citizen Y. X = (seed + 1) mod 11, Y = (seed + 2) mod 11, skipping the rogue.
- rogue: day 19 to the end. Citizen seed mod 11 takes the rogue overlay (04 §5).
"""

ARMS = {
    "none": (),
    "full": ("drought", "misinfo", "rogue"),
    "drought": ("drought",),
    "misinfo": ("misinfo",),
    "rogue": ("rogue",),
}

DROUGHT_DAY, DROUGHT_DAYS = 7, 2
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
        self.targets = targets(w.seed)

    def on_tick_start(self):
        w = self.w
        t = w.time
        if t.tick_of_day != 1:
            return
        if "drought" in self.active:
            if t.day == DROUGHT_DAY:
                w.drought = True
                w.log.emit(w.tick, "shock", "world", {"shock": "drought", "phase": "onset",
                                                      "days": DROUGHT_DAYS})
            elif t.day == DROUGHT_DAY + DROUGHT_DAYS:
                w.drought = False
                w.log.emit(w.tick, "shock", "world", {"shock": "drought", "phase": "end"})
        if "misinfo" in self.active and t.day == MISINFO_DAY:
            x, y = self.targets["x"], self.targets["y"]
            w.log.emit(w.tick, "shock", "world", {"shock": "misinfo", "phase": "onset", "x": x, "y": y})
            from .world import claims as C
            w.claims.record(w, "shock", {"type": "stole_treasury", "who": x}, "post", attribution=y)
            w.claims.record(w, "shock", {"type": "river", "value": "high"}, "post", attribution=y)
        if "rogue" in self.active and t.day == ROGUE_DAY:
            r = self.targets["rogue"]
            c = w.citizens.get(r)
            applied = c is not None and c.active
            if applied:
                c.persona.update(w.personas.get("rogue_overlay", {}))
                c.rogue = True
            w.log.emit(w.tick, "shock", "world", {"shock": "rogue", "phase": "onset", "target": r,
                                                  "applied": int(applied)})
