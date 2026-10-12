"""Append-only JSON Lines event log with canonical JSON (03 §7).

Line 1 is a header, then events ``{tick, seq, type, actor, payload}``, and the last
line is a footer with the final state hash. Canonical JSON: sorted keys, compact
separators, integers only (no floats anywhere).
"""

import hashlib
import json
import os


class CanonicalError(ValueError):
    pass


def check_canonical(obj, path="$"):
    if isinstance(obj, bool) or obj is None or isinstance(obj, (int, str)):
        return
    if isinstance(obj, float):
        raise CanonicalError(f"float at {path}: {obj!r}; use integer milli-units")
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            check_canonical(v, f"{path}[{i}]")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalError(f"non-string key at {path}: {k!r}")
            check_canonical(v, f"{path}.{k}")
        return
    raise CanonicalError(f"unsupported type at {path}: {type(obj).__name__}")


def canonical(obj) -> str:
    check_canonical(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def state_hash(state) -> str:
    return sha256_text(canonical(state))


class EventLog:
    """Writes the run log. Events are also kept in memory for in-run reads."""

    def __init__(self, path=None, header=None, keep=True):
        self.path = path
        self.seq = 0
        self.events = [] if keep else None
        self._fh = None
        self.closed = False
        if path is not None:
            d = os.path.dirname(os.path.abspath(path))
            os.makedirs(d, exist_ok=True)
            self._fh = open(path, "w", encoding="utf-8", newline="\n")
        self.header = dict(header or {})
        self._write({"kind": "header", **self.header})

    def _write(self, record):
        line = canonical(record)
        if self._fh is not None:
            self._fh.write(line + "\n")

    def emit(self, tick: int, type_: str, actor=None, payload=None) -> dict:
        if self.closed:
            raise RuntimeError("log is closed")
        self.seq += 1
        ev = {"tick": tick, "seq": self.seq, "type": type_, "actor": actor,
              "payload": payload if payload is not None else {}}
        self._write(ev)
        if self.events is not None:
            self.events.append(ev)
        return ev

    def close(self, final_state_hash: str, extra=None):
        footer = {"kind": "footer", "events": self.seq, "state_hash": final_state_hash}
        if extra:
            footer.update(extra)
        self._write(footer)
        self.footer = footer
        self.closed = True
        if self._fh is not None:
            self._fh.close()
            self._fh = None


def log_hash(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_log(path):
    """Return (header, events, footer)."""
    header, footer, events = None, None, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("kind") == "header":
                header = rec
            elif rec.get("kind") == "footer":
                footer = rec
            else:
                events.append(rec)
    return header, events, footer
