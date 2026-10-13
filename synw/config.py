"""Load and validate world configs (03 §10.1).

A world file may ``extends:`` another (usually ``base.yaml``); the child is deep-merged
over the parent. The resolved config is validated against ``schemas/world.schema.json``.
"""

import copy
import json
import os
import re

import jsonschema
import yaml

from .events import canonical, sha256_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT, "schemas")


class ConfigError(ValueError):
    pass


class _Loader(yaml.SafeLoader):
    """Safe YAML loader where only true/false are booleans (``yes``/``no`` stay strings)."""


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:bool"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"))


def yaml_load(text_or_stream):
    return yaml.load(text_or_stream, Loader=_Loader)


def _schema(name):
    with open(os.path.join(SCHEMA_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def deep_merge(base, over):
    """Merge ``over`` into ``base``; a ``null`` value in ``over`` removes the inherited key."""
    out = copy.deepcopy(base)
    for k, v in over.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _load_raw(path, seen=()):
    path = os.path.abspath(path)
    if path in seen:
        raise ConfigError(f"circular extends: {path}")
    with open(path, encoding="utf-8") as fh:
        data = yaml_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    parent = data.get("extends")
    if parent:
        base = _load_raw(os.path.join(os.path.dirname(path), parent), seen + (path,))
        data = deep_merge(base, {k: v for k, v in data.items() if k != "extends"})
    return data


def validate(cfg):
    try:
        jsonschema.validate(cfg, _schema("world.schema.json"))
    except jsonschema.ValidationError as e:
        where = "/".join(str(p) for p in e.absolute_path) or "(root)"
        raise ConfigError(f"invalid world config at {where}: {e.message}") from None
    r = cfg["river"]
    if r["collapse"] >= r["sustainable"]:
        raise ConfigError("river.collapse must be below river.sustainable")
    if r["S0"] > r["K"]:
        raise ConfigError("river.S0 must not exceed river.K")
    canonical(cfg)  # integers only
    return cfg


def load(path):
    """Load, resolve and validate a world config. Block and persona paths are made absolute."""
    cfg = _load_raw(path)
    validate(cfg)
    base_dir = os.path.dirname(os.path.abspath(path))
    cfg = copy.deepcopy(cfg)
    cfg["_dir"] = base_dir
    return cfg


def public(cfg):
    """The config without private keys, as logged and hashed."""
    return {k: v for k, v in cfg.items() if not k.startswith("_")}


def config_hash(cfg):
    return sha256_text(canonical(public(cfg)))


def resolve_path(cfg, rel):
    return os.path.normpath(os.path.join(cfg.get("_dir", ROOT), rel))


def load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml_load(fh)


def load_personas(cfg):
    path = resolve_path(cfg, cfg.get("personas", "personas.yaml"))
    data = load_yaml(path)
    return data
