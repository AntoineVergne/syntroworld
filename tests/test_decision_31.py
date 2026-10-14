"""Decision 31: a member's seat counts as one civic act per cycle in P3 and S8."""
from test_decisions_25_27 import T, _log, ev

from synw.metrics.participation import p3_civic_breadth, voluntary_acts
from synw.metrics.secondary import civic_act_counts


def test_seat_counts_once_per_cycle():
    c2 = 7 * T - 5            # day 7: cycle 3 (first window cycle)
    later = 8 * T - 5         # day 8: still cycle 3
    c3 = 10 * T - 5           # day 10: cycle 4
    r = _log([ev(c2, "attend", 0, {"bodies": ["cycle_assembly"]}),
              ev(c2, "ballot", 0, {"body": "cycle_assembly", "vote": "yes"}),
              ev(later, "attend", 0, {"bodies": ["budget"]}),
              ev(c3, "attend", 0, {"bodies": ["cycle_assembly"]})])
    acts = voluntary_acts(r)
    assert [(c, t) for c, _, t in acts] == [(0, "seat"), (0, "seat")]
    assert p3_civic_breadth(r) == 2 / (4 * 6)
    assert civic_act_counts(r)[0] == 2


def test_attend_with_nothing_open_is_not_a_seat():
    r = _log([ev(7 * T - 5, "attend", 1, {"bodies": []})])
    assert voluntary_acts(r) == []
