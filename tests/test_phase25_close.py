"""PLAN 25-20 — THE CLOSE GUARD: eight evidenced ticks, two visible corrections, a two-bucket diff
audit, the audit-target lookup, the §O1 exception closed, the pmset revert proved live, and the
frontier artifact still written exactly once.

CPU-only: stdlib, pytest, and ``scripts/_prose.py`` / ``scripts/phase25_prereg.py`` /
``scripts/phase25_venue.py``. No torch, no numpy, no network. The four mechanics of
``tests/test_phase25_correction.py`` are reused, not re-derived: every prose assertion is matched
through ``_prose.normalized``; every marker is searched FROM THE CLAIM'S OWN INDEX; and nothing here
greps a source file for a name its docstrings discuss.

**WHY THE DIFF AUDIT IS TWO ENUMERATED BUCKETS AND NOT A TOGGLES-ONLY RULE.** The phase close must
fill ``.planning/ROADMAP.md``'s phase-status table row (the same row every prior phase filled) and
must fill the four placeholder traceability rows (``run first, as a sweep point`` / an empty cell) —
none of which is a ``- [ ]`` checkbox. A toggles-only gate was MEASURED unsatisfiable at plan time
(``AssertionError: [('road.post', '| 25. Frontier Sweep ... | 0/TBD | Not started | - |')]``), and
an unsatisfiable gate reached after ~100 h of compute is precisely when an executor drops the ticks
to make it green. So every deleted line must fall into EXACTLY ONE of two buckets — a TOGGLE whose
``- [x]`` twin is among the insertions, or a DECLARED MODIFICATION whose allow-listed prefix has
exactly one replacement — with the counts asserted and the residue empty.

**THE COUNTS ARE MEASURED AT THE PRE-EDIT COMMIT, NOT COPIED FROM THE PLAN.** The plan's
``7 / 23`` were measured at plan time; by the time this plan executed, 25-19 had ticked FRONT-02 /
FRONT-03 and every closed plan's ROADMAP line was already ``[x]``, and the orchestrator reserved the
milestone checkbox for the phase-complete step. Measured at ``_PRE_COMMIT``: **5 toggles + 4
declared rows in REQUIREMENTS.md, 2 toggles + 1 declared row in ROADMAP.md**, residue 0.
"""

import difflib
import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402
import phase25_prereg  # noqa: E402
import phase25_venue  # noqa: E402

_REQUIREMENTS = ".planning/REQUIREMENTS.md"
_ROADMAP = ".planning/ROADMAP.md"
_NOTE = "results/phase25_operational_note.md"
_FRONTIER = "results/phase25_frontier.json"

# The commit this plan's Task 3 edited AGAINST — Task 2's commit, the last one before the planning
# files were touched. The comparator is `git show` of that blob, so a stale scratch snapshot cannot
# contaminate the reading and the audit stays reproducible after /tmp is gone.
_PRE_COMMIT = "df100ca9cebdd862a3cb38b8d3dad3745f79dfac"

_PHASE_25_IDS = (
    "CTRL-01",
    "CTRL-02",
    "FRONT-01",
    "FRONT-02",
    "FRONT-03",
    "FRONT-04",
    "ADVT-01",
    "RPT-02",
)

# (file, expected toggle count, declared-modification prefixes) — MEASURED at _PRE_COMMIT.
_BUCKETS = {
    _REQUIREMENTS: (
        5,
        (
            "| CTRL-01 | Phase 25 |",
            "| CTRL-02 | Phase 25 |",
            "| FRONT-01 | Phase 25 |",
            "| FRONT-04 | Phase 25 |",
        ),
    ),
    _ROADMAP: (2, ("| 25. Frontier Sweep",)),
}


def _text(relative_path):
    return (_ROOT / relative_path).read_text(encoding="utf-8")


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _row_regex(ids=_PHASE_25_IDS):
    ids_alternation = "|".join(re.escape(i) for i in ids)
    return re.compile(r"^\| (" + ids_alternation + r")( \*\(continued[^)]*\)\*)? \|")


def _rows_for(requirement_id):
    """Every traceability row whose ID cell is the requirement — original and *(continued)*."""
    pattern = _row_regex((requirement_id,))
    rows = [line for line in _text(_REQUIREMENTS).splitlines() if pattern.match(line)]
    assert rows, f"no traceability row for {requirement_id}"
    return rows


# ---------------------------------------------------------------------------------------------
# (a) EIGHT TICKS, EACH EVIDENCED.
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("requirement_id", _PHASE_25_IDS)
def test_every_phase_25_requirement_is_ticked(requirement_id):
    text = _text(_REQUIREMENTS)
    ticked = f"- [x] **{requirement_id}**:"
    unticked = f"- [ ] **{requirement_id}**:"
    assert text.count(ticked) == 1, f"{requirement_id} is not ticked exactly once"
    assert unticked not in text, f"{requirement_id} still has an unticked checkbox"


@pytest.mark.parametrize("requirement_id", _PHASE_25_IDS)
def test_every_tick_names_an_artifact_and_a_guard(requirement_id):
    """Each tick cites a `results/` path and a `tests/test_phase25_*.py` path, and EVERY such
    path cited in the row exists on disk. A tick citing a file that is not there is red."""
    flat = _prose.normalized(" ".join(_rows_for(requirement_id)))
    artifacts = {m.rstrip(".,") for m in re.findall(r"results/[\w.\-]+", flat)}
    guards = {m for m in re.findall(r"tests/test_phase25_\w+\.py", flat)}
    assert artifacts, f"{requirement_id}: no results/ path cited"
    assert guards, f"{requirement_id}: no tests/test_phase25_*.py guard cited"
    missing = sorted(p for p in artifacts | guards if not (_ROOT / p).exists())
    assert missing == [], f"{requirement_id} cites file(s) that do not exist: {missing}"


_CORRECTIONS = (
    # (superseded phrasing, the correction token that must follow it in the same row)
    ("at most 2 successes", "ZERO TOLERANCE"),
    ("the gate requires", "measured false"),
)


def test_the_two_corrections_are_recorded_not_absorbed():
    """Both superseded phrasings are PRESENT in the Phase-25 rows, and every occurrence sits
    behind an explicit ``SUPERSEDED:`` marker in its own row with the correction after it.

    Resolved POSITIONALLY: for each occurrence, the nearest preceding ``SUPERSEDED:`` must be
    closer than the row boundary (rows are single lines, so the boundary is the line start), and the
    correction token must follow within the same row. An absence-assertion is the wrong shape —
    action (a) of the plan ORDERS both phrasings written into these rows, so a test asserting they
    appear nowhere fails on the very rows the plan requires. The retract-in-place doctrine keeps the
    superseded claim visible (`.planning/ROADMAP.md`'s `SUPERSEDED IN PLACE 2026-08-30 (plan 24-03)`
    is the register).
    """
    pattern = _row_regex()
    rows = [_prose.normalized(r) for r in _text(_REQUIREMENTS).splitlines() if pattern.match(r)]
    assert len(rows) >= 8, len(rows)
    for phrase, correction in _CORRECTIONS:
        hits = [(row, m.start()) for row in rows for m in re.finditer(re.escape(phrase), row)]
        assert hits, f"{phrase!r} is absent from the Phase-25 rows — absorbed, not recorded"
        for row, where in hits:
            marker = row.rfind("SUPERSEDED:", 0, where)
            assert marker != -1, (
                f"{phrase!r} stands as a claim in row {row[:60]!r}: no SUPERSEDED: before it"
            )
            assert correction.lower() in row[where:].lower(), (
                f"{phrase!r} in row {row[:60]!r} is not followed by its correction {correction!r}"
            )


# ---------------------------------------------------------------------------------------------
# (b) THE PLANNING DIFFS ARE TWO ENUMERATED BUCKETS.
# ---------------------------------------------------------------------------------------------


def two_bucket_audit(pre_text, post_text, n_toggles, declared):
    """Classify every deleted line into exactly one bucket; return (toggles, declared_lines).

    Raises ``AssertionError`` with a tuple — ``('UNDECLARED DELETION', [...])``,
    ``('TOGGLE COUNT', got, want)`` or ``('DECLARED COUNT', [...])`` — so a probe can assert on
    WHICH gate fired and what it named.
    """
    diff = list(
        difflib.unified_diff(pre_text.splitlines(), post_text.splitlines(), lineterm="", n=0)
    )
    deleted = [x[1:] for x in diff if x.startswith("-") and not x.startswith("---")]
    added = [x[1:] for x in diff if x.startswith("+") and not x.startswith("+++")]
    toggles = [d for d in deleted if d.startswith("- [ ] ") and "- [x] " + d[6:] in added]
    decl = [d for d in deleted if d not in toggles and any(d.startswith(p) for p in declared)]
    other = [d for d in deleted if d not in toggles and d not in decl]
    # Explicit raises, not `assert`: pytest rewrites an assert's message into a string, and the
    # RED probes below assert on the TUPLE so they can say which gate fired and what it named.
    if other:
        raise AssertionError(("UNDECLARED DELETION", other))
    if len(toggles) != n_toggles:
        raise AssertionError(("TOGGLE COUNT", len(toggles), n_toggles))
    if len(decl) != len(declared):
        raise AssertionError(("DECLARED COUNT", decl))
    for prefix in declared:
        if sum(1 for a in added if a.startswith(prefix)) != 1:
            raise AssertionError(("each declared line needs exactly one replacement", prefix))
    return toggles, decl


def _pre_and_post(relative_path):
    """The blob at _PRE_COMMIT, and the FIRST commit after it that touched the file — or the
    working tree if none has landed yet. 'First after' keeps the audit stable once later phases
    edit the same file."""
    pre = _git("show", f"{_PRE_COMMIT}:{relative_path}")
    later = _git("log", "--reverse", "--format=%H", f"{_PRE_COMMIT}..HEAD", "--", relative_path)
    first = later.split()[0] if later.split() else None
    post = _git("show", f"{first}:{relative_path}") if first else _text(relative_path)
    return pre, post


@pytest.mark.parametrize("relative_path", sorted(_BUCKETS), ids=["requirements", "roadmap"])
def test_the_planning_diffs_are_two_enumerated_buckets(relative_path):
    n_toggles, declared = _BUCKETS[relative_path]
    pre, post = _pre_and_post(relative_path)
    toggles, decl = two_bucket_audit(pre, post, n_toggles, declared)
    for line in toggles:
        print("TOGGLE  :", line[:70])
    for line in decl:
        print("DECLARED:", line[:70])
    print(f"audit ok: {len(toggles)} toggles, {len(decl)} declared modification(s)")


def _red_probe_cases():
    pre_req, post_req = _pre_and_post(_REQUIREMENTS)
    pre_road, post_road = _pre_and_post(_ROADMAP)
    assert "\n## Out of Scope\n" in post_req
    depends = "**Depends on**: Phases 20, 21, 22, 23, 24"
    assert "\n" + depends + "\n" in post_road
    return (
        pytest.param(
            pre_req,
            post_req.replace("\n## Out of Scope\n", "\n", 1),
            5,
            _BUCKETS[_REQUIREMENTS][1],
            ("UNDECLARED DELETION", ["## Out of Scope"]),
            id="delete-an-unrelated-prose-line",
        ),
        pytest.param(
            pre_road,
            post_road.replace("\n" + depends + "\n", "\n" + depends + ", 25\n", 1),
            2,
            _BUCKETS[_ROADMAP][1],
            ("UNDECLARED DELETION", [depends]),
            id="change-an-undeclared-row",
        ),
        pytest.param(
            pre_req,
            post_req,
            4,
            _BUCKETS[_REQUIREMENTS][1],
            ("TOGGLE COUNT", 5, 4),
            id="wrong-toggle-count",
        ),
    )


@pytest.mark.parametrize(("pre", "post", "n", "declared", "expected"), _red_probe_cases())
def test_the_audit_reddens_three_ways(pre, post, n, declared, expected):
    """The three RED probes the plan executed at plan time, kept as permanent evidence that the
    audit discriminates: an unrelated prose deletion is NAMED, an undeclared row change is NAMED,
    and a wrong toggle count is refused with both numbers."""
    with pytest.raises(AssertionError) as caught:
        two_bucket_audit(pre, post, n, declared)
    assert caught.value.args[0] == expected


# ---------------------------------------------------------------------------------------------
# (c) THE RESERVATIONS, THE EXCEPTION, THE REVERT, THE ARTIFACT.
# ---------------------------------------------------------------------------------------------


def _resolve_audit_target(artifact):
    """`CANARY_RESERVATIONS["audit_target_rule"]`, executed as written: n=8 points only, the first
    PASS in `point_keys` order, else the first n=8 point in `point_keys` order."""
    points = artifact["points"]
    n8 = [k for k in artifact["point_keys"] if points[k]["arm"].endswith("n8")]
    assert all(points[k]["canary_population"]["has_out_of_corpus_canaries"] for k in n8)
    passing = [k for k in n8 if (points[k].get("verdict") or {}).get("verdict") == "PASS"]
    return passing[0] if passing else n8[0]


def test_the_audit_target_rule_resolves_to_exactly_one_point():
    rule = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]
    for clause in (
        "restrict to n=8 points",
        "FIRST in `point_keys` order whose verdict is PASS",
        "the pre-registered null",
    ):
        assert _prose.normalized(clause) in _prose.normalized(rule)
    artifact = json.loads(_text(_FRONTIER))
    target = _resolve_audit_target(artifact)
    assert target == "dp_n8_sigma0p000000", target
    assert target in artifact["point_keys"]
    # The close names the same key, so Phase 26 reads a lookup and not a choice.
    assert f"Phase 26 audits `{target}`" in _prose.normalized(_text(_NOTE))


def test_the_git_surface_exception_is_closed():
    flat = _prose.normalized(_text(_NOTE))
    for sentence in (
        "the exception was for this phase only",
        "the read-only-git-surface discipline resumes for later phases",
        "An exception that is not explicitly closed becomes precedent, and this one is closed",
    ):
        assert _prose.normalized(sentence) in flat, sentence
    assert "IT ENDS WITH THIS PHASE" in phase25_prereg.GIT_SURFACE_EXCEPTION


def test_the_pmset_state_is_reverted():
    """`prove_reverted()` live, on the machine that made the privileged change. Elsewhere there is
    no `pmset` and no change to revert — asserted, not skipped, so the venue's pinned skip counts
    are untouched on ubuntu-latest."""
    if sys.platform == "darwin":
        assert phase25_venue.prove_reverted() == phase25_venue.PMSET_REVERT_TARGETS
    else:
        assert shutil.which("pmset") is None


def test_the_frontier_artifact_is_unchanged_since_its_single_write():
    commits = _git("log", "--oneline", "--", _FRONTIER).splitlines()
    assert len(commits) == 1, commits
    assert not _git("diff", "--", _FRONTIER)
