"""PREREG for v4.0: the three-condition gate was committed BEFORE the numbers it judges.

``scripts/mitigation_gate.py`` states, in code and in prose, what a swept mitigation point has to
achieve to count as a PASS. That statement is only worth anything if it was written blind — before
Phase 23 measured a single wall-clock number, not merely before the Phase 25 sweep. This module is
what turns the claim into a checkable fact: for every committed ``results/phase20_*`` artifact, the
commit that FIRST ADDED it must be a descendant of EVERY commit touching the pin.

**Ancestry, never dates.** The obvious implementation compares committer dates and is wrong.
Committer dates are rewritable by anyone with a shell, skewed across machines, and non-monotonic
after a rebase — a history rewrite could invert the ordering this guard claims to enforce while
both dates still look perfectly ordered. Ancestry is a property of the commit DAG: making
``git merge-base --is-ancestor`` lie means rewriting every object between the two commits, which
changes both SHAs. So the ordering is asked of the object graph, not of a clock. The reasoning is
``tests/test_phase16_prereg.py:11-17``, and this file inherits it rather than restating it as a new
argument.

**Derived from history, not pinned to a SHA.** There is no ``PHASE20_PREREG_COMMIT`` constant here.
The pre-registration side of every ancestry query is ``git log -- <pin>`` — EVERY commit touching
the pin — so a LATER edit is caught, not merely a wrong first commit. That is the Phase 18/19 shape
(``tests/test_phase16_prereg.py:322-403`` and ``:406-497``); a hand-pinned SHA would need its own
identity test and would still permit exactly the post-hoc edit this discipline exists to forbid.

**Vacuous TODAY BY CONSTRUCTION, and that is a RECORDED state rather than a hidden one.** Plan
20-01 arms this guard in the first plan of the phase, deliberately before any ``results/phase20_*``
artifact exists, so ``checked`` is 0 and the product assertion reads ``0 == n * 0``. The closing
equivalence assertion is what stops that vacuity surviving the artifacts' arrival. See
``test_phase20_prereg_is_frozen_before_every_phase20_result`` for why arming first is the point.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)

_PROSE_PATH = _ROOT / "scripts" / "_prose.py"

# The REAL v3.0 incident, never a synthetic one — D-30's register, that a defect which actually
# happened is not hypothetical. `.planning/RETROSPECTIVE.md:179-181` records that a single-line
# `grep -c "three reductions"` returned 0 on a file that CONTAINED the phrase, and
# `.planning/milestones/v3.0-MILESTONE-AUDIT.md:104-111` (defect W2, `resolved_by: 5703bbe`) gives
# the concrete failing form — the source line-wraps it as "the three\nreductions", and the sweep
# that finally saw it had to be whitespace-normalised. These two constants are those exact bytes:
# the wrap sits BETWEEN "three" and "reductions", which is the whole reason the naive read misses.
WRAPPED_INCIDENT_TEXT = (
    "The table above is a rank-only reading, and the paragraph describing the three\n"
    "reductions has no generation number beside it.\n"
)
WRAPPED_INCIDENT_PHRASE = "the three reductions"

# STAT-05: Phase 20's OWN pre-registration, and it is ONE file. The correction path for a defect
# found after an artifact lands is a DATED CONTINUATION beside the published text
# (`scripts/_addendum.py`, D-24), never an edit — so there is no unpinned sibling to move a rule
# into, and after the first artifact every commit here is a reviewed cost.
PHASE20_PREREG_ARTIFACT = "scripts/mitigation_gate.py"

# Every v4.0 results artifact this phase can PROVE it watches — `phase20_*` and nothing else
# (D-33). Pre-declaring `phase21_*`..`phase28_*` was considered and REJECTED: only `phase20_*` can
# be proven RED-then-GREEN by this phase's own throwaway-repo fixture, and an advance declaration
# without demonstration is exactly the kind of unproven assertion this phase exists to refuse. Each
# of Phases 21-28 adds its own prefix at the moment it first writes results, following Phase 16's
# recorded lesson literally — real proof per prefix. THE COST IS NAMED, NOT HIDDEN: an `assert`
# catches an EMPTY match set, never an INCOMPLETE one, so a future phase that forgets its prefix
# fails silently. That risk is ACCEPTED in exchange for never asserting coverage this phase cannot
# demonstrate. So this tuple is DELIBERATELY NARROW, not stale.
V4_ARTIFACT_GLOBS = ("results/phase20_*",)


def _git(*args, cwd=_ROOT):
    """Run git inside a repository and return its stdout, raising on a non-zero exit.

    ``tests/test_phase16_prereg.py:169-173`` with ONE additive widening: ``cwd`` is a keyword-only
    parameter defaulting to this repository. That is the import-never-copy discipline applied to a
    test helper — the live guard below and the D-22 throwaway-repo fixture (plan 20-03) call ONE
    implementation parameterized by its root, rather than two implementations free to drift.

    The argv tuple is passed to ``subprocess`` directly and ``shell=True`` is never used, so a glob
    containing a shell metacharacter reaches git as a pathspec instead of being expanded.
    """
    return subprocess.run(
        ("git", *args), cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def _assert_ordering_holds(*, root, prereg_artifact, artifact_glob, globs):
    """The Phase 18/19 ancestry body, parameterized on ``root``.

    Keyword-only so a caller cannot transpose the pin path with the glob. Shared by the live guard
    below and by the D-22 fixture that proves it RED-then-GREEN in a throwaway repo: a guard proved
    correct in a scratch repository and a guard running against this one must be the SAME code, or
    the proof is about a different function than the one CI runs.
    """
    assert artifact_glob in globs, (
        f"{artifact_glob} is not in {globs} — this guard and the declared artifact set would be "
        "watching two different sets of paths"
    )

    # A shallow clone does not hold the earlier commit objects, so it cannot answer an ancestry
    # question — it can only fail to find one. Assert, never skip: a silently-skipped ordering
    # guard is the "declared invariant silently becomes false" defect this project keeps naming.
    assert _git("rev-parse", "--is-shallow-repository", cwd=root) == "false", (
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )

    prereg_commits = _git("log", "--format=%H", "--", prereg_artifact, cwd=root).split()
    assert prereg_commits, (
        f"{prereg_artifact} has no commits — this guard would be scanning a pre-registration that "
        "does not exist, which is green and blind in the worst possible place. Plan 20-01 Task 1 "
        "commits it."
    )

    tracked_artifacts = _git("ls-files", artifact_glob, cwd=root).split()

    checked = 0
    for artifact in tracked_artifacts:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact, cwd=root).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=root,
                check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked_artifacts), (
        f"checked {checked} pairs but {len(prereg_commits)} pre-registration commit(s) x "
        f"{len(tracked_artifacts)} tracked artifact(s) is "
        f"{len(prereg_commits) * len(tracked_artifacts)} — a `git ls-files` pattern that matches "
        "nothing while artifacts sit on disk would otherwise make this green having checked "
        "nothing."
    )
    # The product above is satisfied by 0 == n * 0. Today both sides ARE zero and that is correct:
    # D-08 forbids a `results/phase20_*` artifact existing before the pin's first commit, and plan
    # 20-01 arms this guard in the same plan that makes that first commit. This ties the two
    # together so the EQUIVALENCE, not the count, is what is asserted — green while no artifact is
    # tracked, and demanding a non-zero `checked` from the first one onward.
    assert bool(checked) == bool(tracked_artifacts), (
        f"checked {checked} pair(s) against {len(tracked_artifacts)} tracked artifact(s) matching "
        f"`git ls-files {artifact_glob}` — those disagree, so either committed Phase 20 results "
        "went unchecked or the ancestry loop ran on paths the match set does not contain. A "
        "STAT-05 guard that checks zero artifacts once results exist is green and blind."
    )


def test_phase20_prereg_is_frozen_before_every_phase20_result():
    """STAT-05: Phase 20's pin never moved after a Phase 20 number existed.

    **Vacuous TODAY BY CONSTRUCTION, and that is a recorded state rather than a hidden one.** The
    pin is armed in plan 20-01 — the first plan of the phase — deliberately BEFORE any
    `results/phase20_*` artifact exists, and D-08 forbids one landing before the pin's first
    commit. So at this moment `git ls-files results/phase20_*` matches nothing, `checked` is 0, and
    the product assertion reads `0 == n * 0`: green, having compared nothing. Arming the guard
    first is the point — every pin commit from 20-01 onward is watched from the start instead of
    being retro-fitted once there is something to miss.

    The closing equivalence assertion is what stops that vacuity surviving the artifacts' arrival.
    It ties `checked` to whether anything was tracked at all, so the FIRST committed Phase 20
    result makes a still-empty match set RED instead of quietly green.

    **What this pins is Phase 18/19's shape, never Phase 16's.** `tests/test_phase16_prereg.py:209`
    uses an unconditional `assert checked` over a working-tree glob, which is RED from the pin's
    first commit until an artifact lands — inverting the very ordering this phase exists to
    establish — and it pins a hand-written SHA, which `:243-247` records as happily permitting the
    later edit STAT-05 forbids. Neither shape appears here.
    """
    _assert_ordering_holds(
        root=_ROOT,
        prereg_artifact=PHASE20_PREREG_ARTIFACT,
        artifact_glob="results/phase20_*",
        globs=V4_ARTIFACT_GLOBS,
    )


def test_normalized_finds_a_line_wrapped_phrase_grep_reports_absent():
    """RPT-02 / ROADMAP SC5: the DIFFERENTIAL, not a bare containment check.

    SC5 requires that `normalized` "finds a line-wrapped phrase that `grep -c` reports as absent",
    and BOTH halves of that sentence are load-bearing. Assertion (1) is the NEGATIVE CONTROL — it
    proves the naive single-line method returns 0 on the very bytes assertion (2) succeeds on.
    Without it this test degrades into "a string containment check passes", which would stay green
    against a `normalized` that returned its argument unchanged, and would therefore certify a
    helper that closes nothing.

    The fixture is the REAL v3.0 defect (see the constants above), on the D-30 register: a defect
    that actually happened is not hypothetical.
    """
    # (1) THE NEGATIVE CONTROL. `str.count` is `grep -c`'s single-line semantics in Python: it
    # cannot see across the newline the source wrapped the phrase on, so it reports a real
    # occurrence as absent. That is the shipped v3.0 defect, reproduced.
    assert WRAPPED_INCIDENT_TEXT.count(WRAPPED_INCIDENT_PHRASE) == 0, (
        "the fixture no longer reproduces the v3.0 incident: the NAIVE single-line read already "
        f"finds {WRAPPED_INCIDENT_PHRASE!r} in it, so the positive assertion below would prove "
        "nothing about whitespace normalisation. The phrase must stay LINE-WRAPPED in the text."
    )

    # (2) The positive, on the SAME BYTES the naive read just failed on.
    haystack = _prose.normalized(WRAPPED_INCIDENT_TEXT)
    needle = _prose.normalized(WRAPPED_INCIDENT_PHRASE)
    assert needle in haystack, (
        f"normalized() failed to find {needle!r} in the normalised v3.0 incident text — the one "
        "defect class RPT-02 exists to close is open again"
    )

    # (3) Idempotence: normalising an already-normalised string is a no-op, so a sweep that
    # normalises twice (a caller normalising a value another caller already normalised) cannot
    # drift from one that normalises once.
    assert _prose.normalized(haystack) == haystack

    # (4) NOT newline-specific. A helper that only collapsed "\n" would miss the tab- and
    # double-space-wrapped forms that the same class of defect produces in tables and lists.
    assert _prose.normalized("a\tb") == "a b"
    assert _prose.normalized("a   b") == "a b"
    assert _prose.normalized("a\r\nb") == "a b"
    assert _prose.normalized("  a \t\n b  ") == "a b"


def test_prose_module_imports_nothing():
    """RPT-03's second layer, and the only one that can see INSIDE the helper.

    `tests/test_package.py`'s `pyproject.toml` sha256 pin catches a DECLARED dependency — a name
    added to the project's install surface. It cannot catch an import statement inside a file, and a
    stdlib-adjacent one (`re` for a "just a small regex", `regex` for a "slightly better" one) is
    exactly how a zero-dependency helper stops being one. Only an AST scan sees that.

    `normalized` is `" ".join(text.split())`. It has no reason to import anything, ever.
    """
    tree = ast.parse(_PROSE_PATH.read_text())
    imports = [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert imports == [], (
        f"{_PROSE_PATH.name} imports {imports} — it is specified as a zero-import stdlib one-liner "
        '(`" ".join(text.split())`), and D-23\'s phase-neutral, dependency-free guarantee is what '
        "lets every driver and every CPU-only test take it without dragging anything in"
    )
