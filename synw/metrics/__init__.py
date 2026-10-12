"""The 3DI indicators (05), computed mechanically from the event log.

Every function takes ``(header, events)`` as returned by ``synw.events.read_log`` (or a
World's ``log.header``/``log.events``) and reads nothing else.
"""

from ..events import read_log


def load(path):
    header, events, _ = read_log(path)
    return header, events


class Run:
    """Indexes a run log once for the metric functions."""

    def __init__(self, header, events):
        self.header = header
        self.events = events
        cfg = header["config"]
        self.cfg = cfg
        clk = cfg["clock"]
        self.ticks_per_day = clk["ticks_per_day"]
        self.days_per_cycle = clk["days_per_cycle"]
        self.days = clk["days_per_cycle"] * clk["cycles"]
        self.window = range(2 * clk["days_per_cycle"] + 1, self.days + 1)   # days 7..24
        self.window_cycles = range(3, clk["cycles"] + 1)
        self.p_ref = cfg["prices_ref"]
        self.by_type = {}
        for e in events:
            self.by_type.setdefault(e["type"], []).append(e)

    def of(self, type_):
        return self.by_type.get(type_, [])

    def day_of(self, tick):
        return (tick - 1) // self.ticks_per_day + 1

    def cycle_of_day(self, day):
        return (day - 1) // self.days_per_cycle + 1


def as_run(header, events=None):
    if isinstance(header, Run):
        return header
    return Run(header, events)
