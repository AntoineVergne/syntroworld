"""Persona check (04 §1 rule 3): the mock, which is the numbers, recovers them."""
import os

from synw.analysis import persona_check as P
from synw.analysis.phase_l import mock_campaign

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_mock_recovers_its_numbers():
    ref = P.mock_reference(worlds=(os.path.join(HERE, "worlds/b.yaml"),), seeds=range(1, 3))
    for t in ("work_drive", "honesty", "civic", "greed"):
        assert ref[t]["mean"] > 0.3


def test_reads_a_campaign(tmp_path):
    mock_campaign(str(tmp_path), worlds=("A",), seeds=range(1, 3), arms=("full",), root=HERE)
    got = P.campaign_runs(str(tmp_path), root=HERE)
    assert got["work_drive"]["runs"] == 2 and got["work_drive"]["mean"] > 0.3
    assert "| work_drive |" in P.table(got, got)
