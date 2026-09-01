"""Install-parity smoke test (ENV-01) and the v3.0 dependency freeze (STAT-04)."""

import hashlib
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# sha256 of pyproject.toml. STAT-04 freezes the whole file: a new extra, a widened version
# specifier and a new runtime dependency are all the same defect from this test's point of view.
# Updated in the same commit as `[project] license = "MIT"` (explicit reviewed decision; no
# dependency change).
PYPROJECT_SHA256 = "15ffd6b58e289447ac6460bdd6210c04d20d5ff5831f741bb3db3bdc0ca7926f"


def test_import_personacore():
    import personacore

    assert personacore is not None


def test_version_is_nonempty_string():
    import personacore

    assert isinstance(personacore.__version__, str)
    assert personacore.__version__ != ""


def test_pyproject_unchanged_since_v2_close():
    """STAT-04: no runtime dependency may enter v3.0 without turning a committed test red.

    The file was last changed at commit 6a46441cc17b6fc3c951a12ee0b6620b88b82d91 — diff against
    that commit to see what the pin below is protecting.

    Read as BYTES, never as text: a text read normalizes line endings, so a CRLF rewrite of the
    dependency table would pass a text-mode hash while changing the file on disk.
    """
    actual = hashlib.sha256((_ROOT / "pyproject.toml").read_bytes()).hexdigest()
    assert actual == PYPROJECT_SHA256, (
        f"pyproject.toml changed: expected sha256 {PYPROJECT_SHA256}, got {actual}. "
        "STAT-04 requires pyproject.toml to be byte-identical at v3.0 close. This project has "
        "declined scipy in committed code twice (continual/fisher.py, scripts/phase15_stats.py), "
        "and every statistic in v3.0 is hand-rolled stdlib built on scripts/erasure_gate.py — "
        "taking a statistics dependency now, in a milestone whose entire output is trust in a "
        "measurement, would retcon both refusals. If a dependency genuinely must change, update "
        "PYPROJECT_SHA256 in the SAME commit as an explicit, reviewed decision — never silently."
    )
