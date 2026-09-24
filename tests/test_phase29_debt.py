"""DEBT-03 (D-18, amended 2026-09-24): the archived Phase-17 SUMMARYs validate as ``summary``.

The GSD validator wants ``phase, plan, subsystem, tags, duration, completed`` at the TOP level;
these 11 files carried ``duration``/``completed`` only nested under ``metrics:``. The top-level
values are copies of the nested ones, and ``completed`` is the file's real first-add date
(``git log --follow`` — plain ``--diff-filter=A`` returns the 2026-08-20 archive move).
"""

import pathlib
import re
import subprocess

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DIR = _ROOT / ".planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix"
SUMMARIES = sorted(_DIR.glob("17-*-SUMMARY.md"))
_REQUIRED = ("phase", "plan", "subsystem", "tags", "duration", "completed")
_KEY = re.compile(r"^([a-z_]+):\s*(.*)$")


def _frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", path
    body = lines[1 : lines.index("---", 1)]
    top, nested, in_metrics = {}, {}, False
    for line in body:
        match = _KEY.match(line)
        if match:
            top[match[1]] = match[2]
            in_metrics = match[1] == "metrics"
        elif in_metrics and line.startswith(" ") and ":" in line:
            key, value = line.strip().split(":", 1)
            nested[key] = value.strip()
    return top, nested


def test_all_eleven_phase17_summaries_are_covered():
    assert len(SUMMARIES) == 11, SUMMARIES


@pytest.mark.parametrize("path", SUMMARIES, ids=[p.name for p in SUMMARIES])
def test_phase17_summary_frontmatter_validates(path):
    top, nested = _frontmatter(path)
    assert [key for key in _REQUIRED if key not in top] == []
    assert top["duration"] == nested["duration"]
    assert top["completed"] == nested["completed"]
    added = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%ad", "--date=short", "--", path],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert added, f"{path.name} has no add in history"
    assert top["completed"] == added[-1]
