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
import fnmatch
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)
import erasure_gate  # noqa: E402  (same reason)
import mitigation_gate  # noqa: E402  (same reason)

_PROSE_PATH = _ROOT / "scripts" / "_prose.py"

# THE HYBRID REGISTER (20-PATTERNS.md 3d). Both halves exist and neither is redundant.
#
# The repo's established register is a GLOB (`tests/test_phase18_prereg.py:59`,
# `tests/test_phase17_stats.py:62`) over `phaseNN_*.py`, and its stated purpose is that "every
# driver a later plan adds enters these scans the moment it exists". But the pin
# `scripts/mitigation_gate.py` matches NO `phase20_*.py` glob — it is named for its subject rather
# than for its phase — so the
# established form alone would scan nothing here and `_collapsed_glob_guard()` would go red over a
# register that is simply looking in the wrong place.
#
# The other established form is a hand-listed tuple (`tests/test_phase16_stats.py:747`), and that is
# exactly the F-08 blindness the glob register was introduced to CLOSE: Phase 23's
# `scripts/mitigation_budget.py` would sit silently uncovered until someone remembered to add it,
# and the one guard that must never be forgotten is the one forbidding the gate from importing it.
#
# So: an explicit path constant for the file that exists today, PLUS a `mitigation_*.py` glob that
# admits `mitigation_budget.py` the moment Phase 23 creates it, PLUS a membership assertion tying
# the two together so they cannot drift into naming two different files.
_MITIGATION_GATE_PATH = _ROOT / "scripts" / "mitigation_gate.py"
_GATE_MODULES = tuple(sorted((_ROOT / "scripts").glob("mitigation_*.py")))

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


def test_phase20_glob_sees_the_phase20_prefix_red_then_green(tmp_path):
    """D-22: watch the ordering guard go RED then GREEN on a real `phase20_*` path.

    **Why this exists.** The live guard above is vacuous today by construction — nothing matches
    `results/phase20_*` yet — so `V4_ARTIFACT_GLOBS` has never once been observed MATCHING anything.
    Reading a glob pattern and confirming it bites are different acts, and a pattern that reads
    correctly while matching nothing is green over nothing: the exact failure this whole phase is
    built to refuse. So the prefix is DEMONSTRATED here, in a throwaway repository, by driving the
    guard through the four states measured during planning and asserting the observed failure at
    each. State 2 is the load-bearing one: an ORDERING failure is only reachable if
    `git ls-files "results/phase20_*"` matched the probe, so it is a positive observation of the
    prefix rather than an inference from the pattern's text.

    **And it is a COMMITTED FIXTURE, re-executed every CI run — not a one-time manual observation.**
    A guard verified once by hand in a scratch directory decays silently the moment someone edits
    `_assert_ordering_holds`. This runs against the SAME `_assert_ordering_holds` the live guard
    calls, parameterized on `root`, so what is proven here is the code that ships. A lookalike copy
    would prove something about a different function.

    **Reflexivity, recorded so it is read as neither a defect nor a licence.** Measured during
    planning: `git merge-base --is-ancestor X X` exits **0**. The pin and an artifact landing in the
    SAME commit would therefore PASS this guard. D-08's "strictly after" rule is a DISCIPLINE
    tighter than the mechanism enforces, deliberately, and that gap is written down here rather than
    left for a later reader to discover and mistake for either a bug or permission.

    **The real repository's history is never touched.** Every probe lives under pytest's `tmp_path`
    and is destroyed with it; there is no `shell=True` and no `rm -rf` anywhere in this module. The
    invariant `git log --diff-filter=A -- 'results/phase20_*'` is EMPTY on this repository must hold
    before and after this test runs — a v4.0-named probe reaching the real history would
    permanently corrupt the very evidence this phase exists to produce.

    The identity is set as LOCAL repo config rather than through the environment: it writes only to
    `tmp_path/.git/config`, needs no widening of `_git`, and makes the fixture independent of
    whether the host has a global `user.email` at all (CI runners generally do not).
    """
    _git("init", "-q", cwd=tmp_path)
    _git("config", "user.name", "phase20-fixture", cwd=tmp_path)
    _git("config", "user.email", "phase20-fixture@localhost", cwd=tmp_path)

    probe = tmp_path / "results" / "phase20_probe.json"
    probe.parent.mkdir()
    probe.write_text('{"probe": true}\n')
    _git("add", "results/phase20_probe.json", cwd=tmp_path)
    _git("commit", "-q", "-m", "state 1: a phase20 artifact, before any pin exists", cwd=tmp_path)
    state1_add = _git(
        "log", "--diff-filter=A", "--format=%H", "--", "results/phase20_probe.json", cwd=tmp_path
    ).split()[-1]

    # STATE 1 — probe committed, NO pin yet. RED, but a DIFFERENT RED: the run stops at
    # `assert prereg_commits` long before any ancestry is compared. Distinguishing the two reds is
    # the point — "the pre-registration does not exist" and "the ordering is violated" are
    # different findings, and a fixture that only checked "something raised" would conflate them.
    with pytest.raises(AssertionError) as no_pin:
        _assert_ordering_holds(
            root=tmp_path,
            prereg_artifact=PHASE20_PREREG_ARTIFACT,
            artifact_glob="results/phase20_*",
            globs=V4_ARTIFACT_GLOBS,
        )
    assert PHASE20_PREREG_ARTIFACT in str(no_pin.value), (
        "state 1 raised an AssertionError that does not name the pin — the expected red here is "
        f"the `assert prereg_commits` branch reporting that {PHASE20_PREREG_ARTIFACT} has no "
        "commits, not some other assertion that happens to fire first"
    )

    # STATE 2 — the pin lands SECOND, i.e. the ordering this phase forbids.
    pin = tmp_path / PHASE20_PREREG_ARTIFACT
    pin.parent.mkdir()
    pin.write_text(
        "# stand-in for the pin: the CONTENT is irrelevant here, the ORDER is the subject\n"
    )
    _git("add", PHASE20_PREREG_ARTIFACT, cwd=tmp_path)
    _git("commit", "-q", "-m", "state 2: the pin, committed AFTER the artifact", cwd=tmp_path)

    # THE PROOF THE GLOB SEES THE `phase20_` PREFIX, stated rather than inferred: the ordering
    # failure below is unreachable unless this match set is non-empty.
    assert _git("ls-files", "results/phase20_*", cwd=tmp_path).split() == [
        "results/phase20_probe.json"
    ], "`git ls-files results/phase20_*` did not match a committed results/phase20_probe.json"

    with pytest.raises(subprocess.CalledProcessError) as out_of_order:
        _assert_ordering_holds(
            root=tmp_path,
            prereg_artifact=PHASE20_PREREG_ARTIFACT,
            artifact_glob="results/phase20_*",
            globs=V4_ARTIFACT_GLOBS,
        )
    # `subprocess.run(check=True)` fails with no explanatory message, so name the failing command:
    # without this, ANY CalledProcessError from ANY git call would satisfy the `raises` above.
    assert tuple(out_of_order.value.cmd[:3]) == ("git", "merge-base", "--is-ancestor"), (
        f"state 2 failed on {out_of_order.value.cmd} — the expected red is the ancestry check "
        "itself, not an incidental git failure elsewhere in the helper"
    )

    # STATE 3 — `git rm` the probe and do not re-add it. GREEN at tracked=0: the red IS reversible,
    # but ONLY by not having the artifact, which for a real phase means having no result at all.
    _git("rm", "-q", "results/phase20_probe.json", cwd=tmp_path)
    _git("commit", "-q", "-m", "state 3: remove the probe", cwd=tmp_path)
    assert _git("ls-files", "results/phase20_*", cwd=tmp_path) == ""
    _assert_ordering_holds(
        root=tmp_path,
        prereg_artifact=PHASE20_PREREG_ARTIFACT,
        artifact_glob="results/phase20_*",
        globs=V4_ARTIFACT_GLOBS,
    )

    # STATE 4 — re-add at the IDENTICAL path. Measured gotcha: `git rm` of the last file in
    # `results/` removes the directory from the working tree, so the re-add needs the mkdir.
    probe.parent.mkdir(exist_ok=True)
    probe.write_text('{"probe": true}\n')
    _git("add", "results/phase20_probe.json", cwd=tmp_path)
    _git("commit", "-q", "-m", "state 4: re-add at the identical path", cwd=tmp_path)

    adds = _git(
        "log", "--diff-filter=A", "--format=%H", "--", "results/phase20_probe.json", cwd=tmp_path
    ).split()
    assert len(adds) == 2, f"expected two adds after a delete-and-re-add cycle, got {adds}"
    # LAUNDERING IS IMPOSSIBLE. `git log` is newest-first, so `adds[-1]` is the EARLIEST add — and
    # it is byte-identical to the SHA state 1 recorded, across a delete and a re-add. Once the
    # ordering is violated, deleting the artifact and committing it again does not reset it.
    assert adds[-1] == state1_add, (
        f"the earliest add is now {adds[-1]} but state 1 recorded {state1_add} — `adds[-1]` no "
        "longer identifies the FIRST add, so a delete-and-re-add cycle could launder a red guard"
    )

    with pytest.raises(subprocess.CalledProcessError) as still_out_of_order:
        _assert_ordering_holds(
            root=tmp_path,
            prereg_artifact=PHASE20_PREREG_ARTIFACT,
            artifact_glob="results/phase20_*",
            globs=V4_ARTIFACT_GLOBS,
        )
    assert tuple(still_out_of_order.value.cmd[:3]) == ("git", "merge-base", "--is-ancestor")

    # STATE 5 — the GREEN half of RED-then-GREEN. The probe is gone and a real-shaped artifact
    # lands whose FIRST add comes after the pin's commit: exactly one tracked artifact, checked
    # against the pin, and the guard passes. This is the ordering Phase 20 exists to establish.
    _git("rm", "-q", "results/phase20_probe.json", cwd=tmp_path)
    _git("commit", "-q", "-m", "state 5: remove the probe for good", cwd=tmp_path)
    artifact = tmp_path / "results" / "phase20_retention_floor.json"
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_text('{"note": "shape only — this repository is a throwaway"}\n')
    _git("add", "results/phase20_retention_floor.json", cwd=tmp_path)
    _git(
        "commit",
        "-q",
        "-m",
        "state 5: a real-shaped artifact, strictly after the pin",
        cwd=tmp_path,
    )

    assert _git("ls-files", "results/phase20_*", cwd=tmp_path).split() == [
        "results/phase20_retention_floor.json"
    ]
    _assert_ordering_holds(
        root=tmp_path,
        prereg_artifact=PHASE20_PREREG_ARTIFACT,
        artifact_glob="results/phase20_*",
        globs=V4_ARTIFACT_GLOBS,
    )


def _collapsed_glob_guard():
    """A glob that stops matching makes every scan below green over nothing."""
    assert len(_GATE_MODULES) >= 1, (
        f"the mitigation_*.py glob collapsed to {len(_GATE_MODULES)} file(s) — a broken glob makes "
        "every static guard in this module green while scanning no source at all"
    )


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _enclosing_functions(tree):
    """``node -> the innermost FunctionDef containing it``, or ``None`` for module scope.

    Module scope is recorded as ``None`` rather than dropped, because module scope is the most
    dangerous placement there is. Byte-for-byte the idiom
    ``tests/test_phase18_prereg.py::_enclosing_functions`` uses.
    """
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            inner = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[child] = current if inner is child else inner
            walk(child, inner)

    walk(tree, None)
    return owner


def test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only():
    """RPT-03 / D-20 / GATE-02: the gate/budget split is a fact about the IMPORT GRAPH.

    `tests/test_phase16_stats.py:387-412` is the template. Four claims, each failing for a
    different reason so a reader debugging one does not have to guess which:

      1. The gate never imports the budget (D-20). Both `import mitigation_budget` and
         `from mitigation_budget import ...` feed the same `imported` set, so one assertion covers
         both forms.
      2. The import surface is a SUBSET of a named allow-set. A subset assertion is strictly
         stronger than a list of forbidden names: it fails on the import nobody thought to forbid.
      3. The `from erasure_gate import` list is EXACTLY five names — the accumulation proved
         complete AND proved to have stopped growing.
      4. No bound is re-implemented locally.
    """
    _collapsed_glob_guard()
    assert _MITIGATION_GATE_PATH in _GATE_MODULES, (
        f"the mitigation_*.py glob no longer matches {_MITIGATION_GATE_PATH.name} itself — every "
        "scan in this file would then be checking siblings while the pin went unread"
    )

    imported = set()
    from_erasure_gate = set()
    defined = set()
    for module in _GATE_MODULES:
        tree = _tree(module)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                # The FLAT module name, matching `tests/test_phase16_stats.py:396`'s expectation
                # and the gate's own `sys.path`-bootstrapped `from erasure_gate import ...`.
                imported.add((node.module or "").split(".")[0])
                if node.module == "erasure_gate":
                    from_erasure_gate.update(alias.name for alias in node.names)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(node.name)

    assert "mitigation_budget" not in imported, (
        f"a mitigation_*.py module imports mitigation_budget (imports: {sorted(imported)}). The "
        "GATE holds OUTCOME thresholds and the BUDGET holds RESOURCE parameters, and "
        "`.planning/ROADMAP.md:139-144` requires that separation to be structurally enforced: a "
        "resource budget measured beforehand is NOT an outcome threshold measured beforehand, and "
        "a reader must not be able to mistake one for the other. K reaches the gate as a REQUIRED "
        "KWARG on promote_to_full_fidelity instead (D-20), which is what lets the promotion rule "
        "live here while the import graph stays clean"
    )

    allowed = {"pathlib", "sys", "erasure_gate"}
    assert imported <= allowed, (
        f"the mitigation modules import {sorted(imported - allowed)} beyond the allow-set "
        f"{sorted(allowed)}. This is asserted as a SUBSET rather than as a list of forbidden "
        "names deliberately: a forbidden-name list only catches the import someone thought to "
        "forbid, while a subset assertion catches the one nobody anticipated. RPT-03 keeps v4.0's "
        "runtime dependency surface at zero, and this pin is stdlib plus the one v3.0 sibling it "
        "imports its instruments from"
    )
    assert not ({"scipy", "numpy", "torch"} & imported), (
        f"the classic offenders {sorted({'scipy', 'numpy', 'torch'} & imported)} reached a "
        "mitigation module — named separately from the subset assertion above so the failure "
        "message says which one, and so a reader sees the three this project has actually had to "
        "keep out of a CPU-only decision rule"
    )

    assert from_erasure_gate == {
        "MARGIN_K",
        "V20_EWC_RETENTION_PPL",
        "V20_MASKED_DIALOGUE_VAL_PPL",
        "rule_of_three",
        "wilson_upper_bound",
    }, (
        f"the `from erasure_gate import` list is {sorted(from_erasure_gate)}. EXACT equality, not "
        "a subset: this list was accumulated ONE NAME PER CONSUMER across four tasks in three "
        "plans (each name landing in the plan whose code first reads it, because an import ahead "
        "of its consumer is an F401), so exact equality is what proves the accumulation landed "
        "COMPLETE and then STOPPED. A subset assertion would be green on a truncated list, and a "
        "superset one would be green on a name imported for a consumer that never arrived"
    )
    assert {"wilson_upper_bound", "rule_of_three"} <= from_erasure_gate, (
        "GATE-02: the two bounds must be IMPORTED. Kept beside the exact-equality assertion above "
        "because this is the one carrying the 'import the instrument' message, and both names now "
        "have real consumers in the pin — `wilson_upper_bound` in `extraction_ceiling` and "
        "`tolerance_report`, `rule_of_three` in the GATE-05 zero-extraction reason"
    )

    assert "VERDICTS" not in from_erasure_gate, (
        "`erasure_gate.VERDICTS` is ('SUCCESS', 'FAILURE', 'INCONCLUSIVE') — the WRONG DOMAIN for "
        "v4.0, which returns PASS / FAIL / INCONCLUSIVE (GATE-01). Importing it would put the "
        "wrong three names in this module's namespace. D-31's resolution is to PROVE the "
        "relationship through the module handle (`_prove_verdict_domain`), never to import the "
        "tuple: this is the one tuple a phase whose discipline is 'import, never retype' cannot "
        "import, and the discipline is kept by proving the relabelling instead"
    )
    assert "V20_RETENTION_NOISE_FLOOR" not in from_erasure_gate, (
        "`erasure_gate.V20_RETENTION_NOISE_FLOOR` (0.068930) is a Phase 12 FULL-FINE-TUNE seed "
        "pair, and importing it would leave it governing an ADAPTER-REGIME verdict — the exact "
        "defect D-06 corrects for v4.0. The v4.0 retention floor arrives as a required kwarg "
        "(D-07), measured in the regime it judges"
    )

    assert not ({"wilson_upper_bound", "rule_of_three"} & defined), (
        "a bound was re-implemented in a mitigation module instead of imported from erasure_gate "
        "— the rule is import the instrument, never copy it, or the two silently diverge. A "
        "second copy of an estimator is a SECOND ESTIMATOR, and the day they stop agreeing is the "
        "day a verdict depends on which one the caller happened to reach"
    )


def test_mitigation_gate_imports_bounds_by_object_identity():
    """GATE-02 / D-09, the RUNTIME half — `is`, never `==`.

    `tests/test_phase19_erasure.py:745-748` is the shape and `:2149` records the reason: a
    value-matching copy is a copy FREE TO STOP MATCHING. The static scan above proves the name
    appears in an import statement and nowhere in a local `def`; this proves the object the running
    module actually holds is the same object `erasure_gate` holds. Both halves are needed — the
    static one reads the source, this one reads the loaded namespace, and a module that passed the
    first while failing the second would be one whose import had been shadowed after the fact.

    HONEST CAVEAT ON `MARGIN_K`, stated rather than glossed. It is the int 2, and CPython caches
    small ints, so a local `MARGIN_K = 2` would satisfy `is` here anyway. The identity assertion is
    load-bearing for the three FLOATS and for the two FUNCTIONS; for `MARGIN_K` the assertion that
    actually catches a retype is the static one above, which requires the name to be in the
    `from erasure_gate import` list. It is asserted here regardless, because a `MARGIN_K` rebound to
    a DIFFERENT int — a k=3 margin, say — is exactly the drift that would pass unnoticed otherwise.
    """
    assert mitigation_gate.wilson_upper_bound is erasure_gate.wilson_upper_bound
    assert mitigation_gate.rule_of_three is erasure_gate.rule_of_three
    assert mitigation_gate.MARGIN_K is erasure_gate.MARGIN_K
    assert mitigation_gate.V20_EWC_RETENTION_PPL is erasure_gate.V20_EWC_RETENTION_PPL
    assert mitigation_gate.V20_MASKED_DIALOGUE_VAL_PPL is erasure_gate.V20_MASKED_DIALOGUE_VAL_PPL


def test_prose_helper_is_outside_every_pin_glob():
    """D-23 stated as a CHECK rather than as a paragraph: the underscore is the mechanism.

    `scripts/mitigation_gate.py` freezes at its first commit — once any `results/phase20_*`
    artifact exists, every later commit touching the pin reddens the ancestry guard permanently.
    A PHASE-NEUTRAL utility must not inherit an immutability that only makes sense for a judgment
    rule: `_prose.normalized` has to keep serving Phases 21-28. What buys that exemption is the
    LEADING UNDERSCORE, and it is an fnmatch fact rather than a convention — asserted here against
    every pin glob this repository has used, plus this phase's own `mitigation_*.py` register.

    THE HONEST CAVEAT THIS REPOSITORY ALREADY RECORDS: the precedent is STRUCTURAL, not HISTORICAL.
    `scripts/_addendum.py`'s last commit predates the first `results/phase19_*` add, so NEITHER
    `_addendum.py` NOR `_verdict.py` has actually been edited after an artifact existed. The
    exemption is proved by the pattern, never by a survived edit, and this test proves exactly the
    pattern and nothing more.
    """
    pin_globs = (
        "phase16_*.py",
        "phase17_*.py",
        "phase18_*.py",
        "phase19_*.py",
        "phase20_*.py",
        "mitigation_*.py",
    )
    matched = [glob for glob in pin_globs if fnmatch.fnmatch(_PROSE_PATH.name, glob)]
    assert matched == [], (
        f"{_PROSE_PATH.name} is matched by {matched} — it would enter that pin's scanned set and "
        "inherit the immutability D-23 exempts it from. The leading underscore IS the mechanism; "
        "a rename that drops it silently freezes a helper five later phases still need to change"
    )

    _collapsed_glob_guard()
    assert _PROSE_PATH not in _GATE_MODULES, (
        f"{_PROSE_PATH} entered _GATE_MODULES {[p.name for p in _GATE_MODULES]} — the register "
        "that governs this phase's pin must not govern the phase-neutral helper beside it"
    )
