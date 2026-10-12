from synw import config
from synw.governance.blocks import load_block, step
from synw.runner import run

from conftest import wpath


def _flat(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(_flat(v, f"{prefix}{i}."))
    else:
        out[prefix.rstrip(".")] = d
    return out


def _resolved(name):
    cfg = config.public(config.load(wpath(name)))
    blocks = [load_block(config.resolve_path(config.load(wpath(name)), p)) for p in cfg["governance"]["blocks"]]
    cfg = dict(cfg, governance=dict(cfg["governance"], blocks=blocks))
    return cfg


def test_c_differs_from_a_only_in_weights_and_quorum():
    a, c = _flat(_resolved("a.yaml")), _flat(_resolved("c.yaml"))
    ignore = {"world", "description", "governance.blocks.0.id"}
    diff = {k for k in set(a) | set(c) if a.get(k) != c.get(k) and k not in ignore}
    assert diff == {"governance.blocks.0.steps.1.weights", "governance.blocks.0.steps.1.quorum.of"}
    b = load_block(wpath("blocks/bootstrap-wealth-v1.yaml"))
    assert step(b, "vote")["weights"] == "wealth"
    assert step(b, "vote")["quorum"] == {"share": 500, "of": "wealth"}


def test_wealth_weighted_ballots():
    w = run(wpath("c.yaml"), 1)
    ballots = [e for e in w.log.events if e["type"] == "ballot"]
    assert ballots and len({e["payload"]["weight"] for e in ballots}) > 2
