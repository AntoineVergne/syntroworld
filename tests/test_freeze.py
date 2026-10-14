"""06 §8.1: docs 01 to 06 and the engine are frozen together (FREEZE.md)."""
from synw import __version__, freeze


def test_nothing_changed_since_the_freeze():
    version, changed = freeze.diff()
    assert version == __version__, "engine version changed: log an amendment and rewrite FREEZE.md"
    assert not changed, f"frozen files changed without an amendment: {changed}"


def test_manifest_covers_docs_and_engine():
    files = freeze.frozen_files()
    assert "source-docs/01-constitution.md" in files and "source-docs/06-experiment-design.md" in files
    assert "synw/runner.py" in files and "worlds/a-text.yaml" in files and "schemas/world.schema.json" in files
    assert not any("README" in f for f in files)
