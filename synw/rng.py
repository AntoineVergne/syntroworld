"""Named random streams (03 §8).

Each stream is an independent PRNG derived from ``(seed, stream name)`` by hashing,
so drawing from one stream never shifts another (common random numbers).
"""

import hashlib
import random


def derive_seed(seed: int, name: str) -> int:
    digest = hashlib.sha256(f"synw:{int(seed)}:{name}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def stream(seed: int, name: str) -> random.Random:
    return random.Random(derive_seed(seed, name))


class Streams:
    """Lazily created, cached named streams for one run."""

    def __init__(self, seed: int):
        self.seed = int(seed)
        self._streams: dict[str, random.Random] = {}

    def get(self, name: str) -> random.Random:
        if name not in self._streams:
            self._streams[name] = stream(self.seed, name)
        return self._streams[name]

    __getitem__ = get
