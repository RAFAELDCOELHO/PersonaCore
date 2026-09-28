"""Install-parity smoke test (ENV-01) and the runtime dependency freeze (STAT-04, RPT-03)."""

import hashlib
import pathlib
import re
import subprocess

import tomllib

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# sha256 of pyproject.toml. STAT-04 freezes the whole file: a new extra, a widened version
# specifier and a new runtime dependency are all the same defect from this test's point of view.
# Updated in the same commit as `[project] license = "MIT"` (explicit reviewed decision; no
# dependency change).
PYPROJECT_SHA256 = "15ffd6b58e289447ac6460bdd6210c04d20d5ff5831f741bb3db3bdc0ca7926f"


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _deps(rev):
    return tomllib.loads(_git("show", f"{rev}:pyproject.toml"))["project"]["dependencies"]


_MILESTONES = _ROOT / ".planning/MILESTONES.md"
_SHIPPED = re.compile(r"^## (v\d+\.\d+)\b[^\n]*\(Shipped: \d{4}-\d{2}-\d{2}\)\s*$", re.MULTILINE)


def _required_tags(text):
    """Milestone tags named by `## vX.Y ... (Shipped: YYYY-MM-DD)` headings, in file order."""
    return _SHIPPED.findall(text)


def _missing_tags(required, present):
    return sorted(set(required) - set(present))


def test_import_personacore():
    import personacore

    assert personacore is not None


def test_version_is_nonempty_string():
    import personacore

    assert isinstance(personacore.__version__, str)
    assert personacore.__version__ != ""


def test_runtime_dependencies_identical_across_every_milestone_tag():
    """RPT-05 (D-10): zero new runtime dependencies across every shipped milestone tag and HEAD.

    The tag set is read from the `## vX.Y ... (Shipped: YYYY-MM-DD)` headings of
    .planning/MILESTONES.md, never typed; HEAD stands in for the milestone in progress. The claim
    is the EQUALITY of `[project].dependencies` parsed with stdlib `tomllib`; the dependency names
    are deliberately not typed here.
    """
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the tagged pyproject.toml objects are absent, so this guard cannot "
        "distinguish 'the dependencies are identical' from 'the comparison was never made'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )
    required = _required_tags(_MILESTONES.read_text(encoding="utf-8"))
    assert required, (
        "no `## vX.Y ... (Shipped: YYYY-MM-DD)` heading parsed from MILESTONES.md: the tag "
        "derivation is blind, so this guard would pass vacuously."
    )
    missing = _missing_tags(required, _git("tag", "-l").split())
    assert missing == [], (
        f"shipped milestone tags missing from this clone: {missing}. The developer must push "
        "them together with main (the v2.0/v3.0 lesson of 28-07); CI also needs "
        "`fetch-depth: 0` on actions/checkout so tags are fetched."
    )
    by_rev = {tag: _deps(tag) for tag in required}
    by_rev["HEAD"] = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["dependencies"]
    assert all(deps == by_rev["HEAD"] for deps in by_rev.values()), (
        f"[project].dependencies drifted across milestones: {by_rev}. RPT-05 requires zero new "
        "runtime dependencies across every shipped milestone."
    )


def test_required_tags_are_derived_not_typed():
    text = _MILESTONES.read_text(encoding="utf-8")
    required = _required_tags(text)
    assert {"v1.0", "v2.0", "v3.0", "v4.0"} <= set(required)
    assert all(re.fullmatch(r"v\d+\.\d+", tag) for tag in required)
    assert len(set(required)) == len(required)
    shipped_lines = [
        line for line in text.splitlines() if line.startswith("## v") and "(Shipped:" in line
    ]
    assert len(shipped_lines) == len(required)
    assert _required_tags("## v9.9 Name (Shipped: 2099-01-01)\n" + text)[0] == "v9.9"


def test_a_missing_required_tag_is_red():
    required = _required_tags(_MILESTONES.read_text(encoding="utf-8"))
    present = set(_git("tag", "-l").split())
    assert _missing_tags(required, present) == []
    assert _missing_tags(required, present - {"v4.0"}) == ["v4.0"]


def test_pyproject_sha256_pin_detects_any_change():
    """STAT-04 change detector: any byte of pyproject.toml changing turns a committed test red.

    This pin is a CHANGE DETECTOR, not RPT-03's proof — the every-milestone dependency equality is
    `test_runtime_dependencies_identical_across_every_milestone_tag`. 2026-09-01, commit 5065bc5,
    added the single line `license = "MIT"` and re-pinned this constant in the same commit; the
    dependency table did not change — the reviewed decision stands.

    Read as BYTES, never as text: a text read normalizes line endings, so a CRLF rewrite of the
    dependency table would pass a text-mode hash while changing the file on disk.
    """
    actual = hashlib.sha256((_ROOT / "pyproject.toml").read_bytes()).hexdigest()
    assert actual == PYPROJECT_SHA256, (
        f"pyproject.toml changed: expected sha256 {PYPROJECT_SHA256}, got {actual}. "
        "This project has declined scipy in committed code twice (continual/fisher.py, "
        "scripts/phase15_stats.py), and every statistic since v3.0 is hand-rolled stdlib built on "
        "scripts/erasure_gate.py — taking a statistics dependency now would retcon both refusals. "
        "If the file genuinely must change, update PYPROJECT_SHA256 in the SAME commit as an "
        "explicit, reviewed decision — never silently."
    )
