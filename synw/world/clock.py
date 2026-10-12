"""Time (03 §2). Ticks are 1-based: tick 1 is day 1, tick 1 of day, cycle 1."""

from typing import NamedTuple

TICKS_PER_DAY = 16
DAYS_PER_CYCLE = 3
CYCLES_PER_SEASON = 8


class Time(NamedTuple):
    tick: int
    day: int
    tick_of_day: int
    cycle: int
    day_of_cycle: int


class Clock:
    def __init__(self, ticks_per_day=TICKS_PER_DAY, days_per_cycle=DAYS_PER_CYCLE,
                 cycles=CYCLES_PER_SEASON):
        self.ticks_per_day = ticks_per_day
        self.days_per_cycle = days_per_cycle
        self.cycles = cycles

    @classmethod
    def from_config(cls, cfg):
        c = cfg["clock"]
        return cls(c["ticks_per_day"], c["days_per_cycle"], c["cycles"])

    @property
    def days(self):
        return self.days_per_cycle * self.cycles

    @property
    def ticks(self):
        return self.ticks_per_day * self.days

    @property
    def ticks_per_cycle(self):
        return self.ticks_per_day * self.days_per_cycle

    def at(self, tick: int) -> Time:
        if tick < 1:
            raise ValueError("ticks start at 1")
        day = (tick - 1) // self.ticks_per_day + 1
        tod = (tick - 1) % self.ticks_per_day + 1
        cycle = (day - 1) // self.days_per_cycle + 1
        doc = (day - 1) % self.days_per_cycle + 1
        return Time(tick, day, tod, cycle, doc)

    def tick_of(self, day: int, tick_of_day: int = 1) -> int:
        return (day - 1) * self.ticks_per_day + tick_of_day

    def cycle_start_day(self, cycle: int) -> int:
        return (cycle - 1) * self.days_per_cycle + 1

    def tick_in_cycle(self, cycle: int, day_of_cycle: int, tick_of_day: int) -> int:
        return self.tick_of(self.cycle_start_day(cycle) + day_of_cycle - 1, tick_of_day)


def at(tick: int) -> Time:
    return Clock().at(tick)
