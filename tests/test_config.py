import copy
import os

import pytest
import yaml

from synw import config

BASE = os.path.join(os.path.dirname(__file__), "..", "worlds", "base.yaml")


def test_base_loads():
    cfg = config.load(BASE)
    assert cfg["river"]["K"] == 1000000
    assert cfg["prices_ref"]["food"] == 2000
    assert cfg["clock"]["ticks_per_day"] == 16


def _write(tmp_path, data):
    p = tmp_path / "w.yaml"
    p.write_text(yaml.safe_dump(data))
    return str(p)


def _base():
    with open(BASE) as fh:
        return yaml.safe_load(fh)


def test_missing_field_rejected(tmp_path):
    data = _base()
    del data["river"]["K"]
    with pytest.raises(config.ConfigError):
        config.load(_write(tmp_path, data))


def test_missing_section_rejected(tmp_path):
    data = _base()
    del data["theft"]
    with pytest.raises(config.ConfigError):
        config.load(_write(tmp_path, data))


def test_out_of_range_rejected(tmp_path):
    data = _base()
    data["theft"]["detection"] = 1500
    with pytest.raises(config.ConfigError):
        config.load(_write(tmp_path, data))


def test_float_rejected(tmp_path):
    data = _base()
    data["river"]["r"] = 0.25
    with pytest.raises(config.ConfigError):
        config.load(_write(tmp_path, data))


def test_extends_merges(tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text(yaml.safe_dump(_base()))
    child = tmp_path / "child.yaml"
    child.write_text(yaml.safe_dump({"extends": "base.yaml", "world": "X", "river": {"r": 300}}))
    cfg = config.load(str(child))
    assert cfg["river"]["r"] == 300
    assert cfg["river"]["K"] == 1000000
    assert cfg["world"] == "X"


def test_hash_stable():
    a = config.config_hash(config.load(BASE))
    b = config.config_hash(config.load(BASE))
    assert a == b
