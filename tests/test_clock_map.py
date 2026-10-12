from synw.world import map as wmap
from synw.world.clock import Clock


def test_clock_points():
    c = Clock()
    assert c.at(1) == (1, 1, 1, 1, 1)
    assert c.at(16) == (16, 1, 16, 1, 1)
    assert c.at(17) == (17, 2, 1, 1, 2)
    assert c.at(48) == (48, 3, 16, 1, 3)
    assert c.at(49) == (49, 4, 1, 2, 1)
    assert c.at(384) == (384, 24, 16, 8, 3)
    assert c.ticks == 384 and c.days == 24


def test_tick_of_round_trip():
    c = Clock()
    for t in (1, 16, 17, 48, 49, 384):
        tm = c.at(t)
        assert c.tick_of(tm.day, tm.tick_of_day) == t
        assert c.tick_in_cycle(tm.cycle, tm.day_of_cycle, tm.tick_of_day) == t


def test_map():
    assert len(wmap.LOCATIONS) == 15
    assert len(wmap.DISTRICTS) == 5
    assert wmap.district("fields") == wmap.district("river") != wmap.district("exchange")
    assert wmap.travel_ticks("fields", "exchange") == 1
    assert wmap.travel_ticks("fields", "river") == 1
    assert wmap.travel_ticks("gate", "gate") == 0
    assert wmap.transit_ticks("fields", "exchange") == 0
    for site in ("fields", "river", "plant", "workshop", "data_tower", "exchange", "gate",
                 "clinic", "archive", "observatory", "cafe", "square", "assembly_hall"):
        assert wmap.is_location(site)
