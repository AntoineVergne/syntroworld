"""The v0.1 map of Kleros: 15 locations in 5 districts.

Movement (03 §4): a `move` takes the tick in which it is made and the citizen arrives
next tick, so moving between locations (and so between districts) costs one tick.
Districts group nearby locations; they carry no extra travel cost in v0.1.
"""

LOCATIONS = {
    # production district
    "fields": "production",
    "river": "production",
    "plant": "production",
    # commerce district
    "exchange": "commerce",
    "workshop": "commerce",
    "data_tower": "commerce",
    "cafe": "commerce",
    # civic district
    "assembly_hall": "civic",
    "archive": "civic",
    "observatory": "civic",
    "square": "civic",
    # edge district
    "gate": "edge",
    "clinic": "edge",
    # residential district
    "north_residences": "residential",
    "south_residences": "residential",
}

DISTRICTS = sorted(set(LOCATIONS.values()))

WORK_SITES = ("fields", "plant", "workshop", "data_tower")
PRODUCTION_SITES = ("fields", "river", "plant", "workshop")
SABOTAGE_SITES = ("fields", "river", "plant", "workshop")
HOMES = ("north_residences", "south_residences")


def district(loc: str) -> str:
    return LOCATIONS[loc]


def is_location(loc) -> bool:
    return isinstance(loc, str) and loc in LOCATIONS


def travel_ticks(a: str, b: str) -> int:
    """Ticks a move from ``a`` to ``b`` costs: the move tick itself, 0 if already there."""
    return 0 if a == b else 1


def transit_ticks(a: str, b: str) -> int:
    """Ticks spent in transit after the move tick (none in v0.1)."""
    return 0


def home_of(index: int) -> str:
    return HOMES[index % 2]
