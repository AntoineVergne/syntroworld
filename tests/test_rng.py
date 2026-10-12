from synw.rng import Streams, stream


def test_same_seed_same_name_same_sequence():
    a = stream(7, "world")
    b = stream(7, "world")
    assert [a.random() for _ in range(20)] == [b.random() for _ in range(20)]


def test_different_names_differ():
    a = stream(7, "world")
    b = stream(7, "order")
    assert [a.random() for _ in range(5)] != [b.random() for _ in range(5)]


def test_different_seeds_differ():
    assert stream(1, "world").random() != stream(2, "world").random()


def test_streams_are_independent():
    s1 = Streams(3)
    expected = Streams(3).get("world").random()
    for _ in range(100):
        s1.get("order").random()
    assert s1.get("world").random() == expected
