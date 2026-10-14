from synw.analysis.calibrate import collect, main, parse_seeds, report

from conftest import wpath


def test_parse_seeds():
    assert parse_seeds("1-3") == [1, 2, 3]
    assert parse_seeds("1,4-5") == [1, 4, 5]


def test_report_format(capsys):
    rows = collect(wpath("a.yaml"), [1, 2, 3])
    assert len(rows) == 3
    lines = report(rows)
    assert len(lines) == 10
    for line in lines:
        assert line.startswith("PASS  ") or line.startswith("FAIL  ")
        assert ": " in line
    assert main(["--world", wpath("a.yaml"), "--seeds", "1"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 11
