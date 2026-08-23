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
import json
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
# than for its phase — so the established form alone would scan nothing here and
# `_collapsed_glob_guard()` would go red over a register that is simply looking in the wrong place.
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

# Phase 21's pin (D-19). THIS HAND-WRITTEN EXPLICIT PATH — and NOT the `mitigation_*.py` filename —
# is what confers the freeze, and the distinction was MEASURED before it was relied on because half
# the obvious premise is false. The premise "a mitigation_*.py module is frozen once its first
# artifact lands" is true of the FREEZE and false of the NAMING:
#
#   * the `_GATE_MODULES` glob (`:72`) reaches exactly ONE content test — the import-graph scan at
#     `:474` — plus `_collapsed_glob_guard()` and the `_prose.py` exclusion. It confers no freeze.
#   * `_MITIGATION_GATE_PATH` is SINGULAR and drives `:740`, `:805`, `:928`, `:991`. It does NOT
#     extend to a sibling.
#   * only a `prereg_artifact=` constant reaches `_assert_ordering_holds`, and that is the whole
#     mechanism.
#
# So a `mitigation_*.py` sibling is protected-but-not-frozen BY DEFAULT, which is exactly the
# "middle ground" a phase might otherwise think it had to invent (D-21). Naming a module here is
# the deliberate act that gives that up, and it is irrevocable from the first matching artifact.
PHASE21_PREREG_ARTIFACT = "scripts/mitigation_unit.py"

# Every v4.0 results artifact this phase can PROVE it watches — `phase20_*` and nothing else
# (D-33). Pre-declaring `phase21_*`..`phase28_*` was considered and REJECTED: only `phase20_*` can
# be proven RED-then-GREEN by this phase's own throwaway-repo fixture, and an advance declaration
# without demonstration is exactly the kind of unproven assertion this phase exists to refuse. Each
# of Phases 21-28 adds its own prefix at the moment it first writes results, following Phase 16's
# recorded lesson literally — real proof per prefix. THE COST IS NAMED, NOT HIDDEN: an `assert`
# catches an EMPTY match set, never an INCOMPLETE one, so a future phase that forgets its prefix
# fails silently. That risk is ACCEPTED in exchange for never asserting coverage this phase cannot
# demonstrate. So this tuple is DELIBERATELY NARROW, not stale.
#
# PHASE 21 ADDED `results/phase21_*` HERE, AND FOUND THAT THIS ADDITION ENFORCES NOTHING BY ITSELF
# (Phase 21 D-20). Recorded rather than left for the next phase to re-discover: `globs` is read in
# exactly ONE place inside `_assert_ordering_holds` — the `assert artifact_glob in globs`
# consistency check at `:129` — while the ordering loop at `:150` runs on the SINGULAR
# `artifact_glob`. So widening this tuple buys a consistency check and no ancestry check at all.
# D-33 above names the glob addition as the obligation and stops there, which means a phase doing
# exactly what D-33 literally says would ship an UNENFORCED DECLARATION: a tuple entry that reads
# like coverage while nothing iterates it. BOTH HALVES ARE REQUIRED — this entry AND a live test
# calling `_assert_ordering_holds(artifact_glob="results/phase21_*")`. See
# `test_phase21_prereg_is_frozen_before_every_phase21_result` for the second half.
V4_ARTIFACT_GLOBS = ("results/phase20_*", "results/phase21_*")


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


def test_phase21_prereg_is_frozen_before_every_phase21_result():
    """Phase 21 D-20: the privacy-unit pin never moved after a Phase 21 number existed.

    **Vacuous TODAY BY CONSTRUCTION, and that is the point rather than a weakness.** Plan 21-01 is
    the FIRST plan of Phase 21 and it arms this guard deliberately before any `results/phase21_*`
    artifact exists, so `git ls-files results/phase21_*` matches nothing, `checked` is 0, and the
    product assertion reads `0 == n * 0` — green, having compared nothing. Arming first is what
    buys the guarantee: `git ls-files` is this guard's input, so an artifact becomes watched when it
    is COMMITTED, not when it is written, and `:157` (`adds[-1]`, the EARLIEST add) makes a wrong
    order permanent. A guard retro-fitted once there is something to miss has already missed it.

    The closing equivalence assertion at `:178` is what stops that vacuity SURVIVING the artifacts'
    arrival: it ties `checked` to whether anything was tracked at all, so the first committed Phase
    21 result makes a still-empty match set RED instead of quietly green.

    **This calls the SAME `_assert_ordering_holds` the Phase 20 guard calls**, parameterized on
    `root`, rather than copying its body. A lookalike copy would prove something about a different
    function — the reason recorded at `:296-298`.

    **Reflexivity, inherited deliberately and not silently.** Measured on this repository:
    `git merge-base --is-ancestor X X` exits 0, so a pin and an artifact landing in the SAME commit
    PASS this guard. D-20's "strictly after" is therefore a DISCIPLINE tighter than the mechanism
    enforces. That gap is written down here, as it is at `:300-304`, so a later reader meets it as a
    known property rather than mistaking it for either a bug or a licence.
    """
    _assert_ordering_holds(
        root=_ROOT,
        prereg_artifact=PHASE21_PREREG_ARTIFACT,
        artifact_glob="results/phase21_*",
        globs=V4_ARTIFACT_GLOBS,
    )


def test_phase21_has_no_artifact_yet_so_the_arming_is_honest():
    """The arm-then-write claim made CHECKABLE on this repository, not merely promised.

    The guard above is vacuous today, and its docstring says so — but "vacuous because we armed
    early" and "vacuous because the glob is looking in the wrong place" are indistinguishable from
    inside that test. This one distinguishes them from the outside: it asserts that NO
    `results/phase21_*` file has ever been ADDED in this history, which is the fact that makes the
    vacuity honest rather than accidental.

    **It is also the invariant that protects the evidence.** A `phase21_`-named probe reaching the
    real git history — rather than staying under a throwaway `tmp_path` repo — would permanently
    corrupt the ordering record this phase exists to produce, and `:157` means it could not be
    laundered by deleting the file afterwards. This assertion fires the moment that happens.

    **EXPECTED TO BE DELETED OR INVERTED BY PLAN 21-11**, which commits the first real
    `results/phase21_*` artifact. Removing it there is the RECORDED TRANSITION from "armed, nothing
    to watch" to "armed and watching", not an erasure of an inconvenient guard — and from that
    commit onward the equivalence assertion at `:178` carries the same duty this test carries now.
    """
    adds = _git("log", "--diff-filter=A", "--format=%H", "--", "results/phase21_*").split()
    assert adds == [], (
        f"{len(adds)} commit(s) already ADDED a results/phase21_* artifact: {adds}. Plan 21-01 "
        "arms the ordering guard BEFORE the first artifact, so finding one here means either the "
        "arming is no longer first — and `adds[-1]` makes that permanent — or a phase21-named "
        "probe escaped a tmp_path fixture into the real history"
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


# The published Phase 19 M1 readings the D-30 fixture reuses. Parsed, never transcribed.
_PHASE19_ARM_ERASED = _ROOT / "results" / "phase19_arm_erased.json"


def _module_scope_floats(tree):
    """Float constants inside MODULE-SCOPE ``ast.Assign`` nodes, excluding ``FIXTURE_*`` targets.

    Module scope is where a chosen constant would live, and ``_enclosing_functions`` records it as
    ``None`` rather than dropping it precisely because it is the most dangerous placement there is.
    Note that an assignment inside ``if __name__ == "__main__":`` is STILL module scope under that
    definition — the pin's self-check was deliberately written with zero float literals so this
    audit reads the same set either way.

    WHY ``FIXTURE_*`` IS EXCLUDED, AND EXACTLY HOW BIG THE RESULTING HOLE IS. The three fixture
    dicts hold roughly forty numbers between them, and they are INPUTS to a demonstration rather
    than criteria. FOUR fields, and only four, are proved against a published source by
    ``test_destroyed_model_fixture_matches_the_published_phase19_readings`` below:
    ``point_dialogue_ppl_on``, ``point_dialogue_ppl_off``, ``point_retention_ppl`` and
    ``control_gap``, each asserted equal to a value parsed from
    ``results/phase19_arm_erased.json``. EVERY OTHER FLOAT inside a ``FIXTURE_*`` dict is a
    DELIBERATELY FABRICATED value with no external source to check it against — no v4.0 arm exists
    (D-13), so there is nothing for them to be equal to.

    THE RESIDUAL HOLE, STATED IN WORDS RATHER THAN GLOSSED: a third chosen constant could hide
    inside a ``FIXTURE_*`` dict and THIS AUDIT WOULD NOT SEE IT. That risk is ACCEPTED. The
    alternative — asserting fabricated fixture inputs against a source that does not exist — is
    exactly the kind of unprovable assertion this phase exists to refuse, and buying a tighter
    number by making a claim nobody can check would be the defect, not the fix. What the hole IS
    narrowed by is a name allow-list: the module-scope ``FIXTURE_*`` names are asserted to be
    exactly the three that exist, so the cheapest evasion — a FOURTH fixture dict added to carry
    constants past this scan — is caught even though a constant buried in one of the three is not.
    """
    owner = _enclosing_functions(tree)
    floats = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or owner.get(node) is not None:
            continue
        if any(
            isinstance(target, ast.Name) and target.id.startswith("FIXTURE_")
            for target in node.targets
        ):
            continue
        floats.update(
            child.value
            for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, float)
        )
    return floats


def _module_scope_fixture_names(tree):
    """The module-scope names beginning ``FIXTURE_`` — the allow-list narrowing the hole above."""
    owner = _enclosing_functions(tree)
    return {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign) and owner.get(node) is None
        for target in node.targets
        if isinstance(target, ast.Name) and target.id.startswith("FIXTURE_")
    }


def _numeric_constants_outside_fixtures(tree):
    """Every numeric constant in the pin except those inside a ``FIXTURE_*`` assignment.

    Booleans are excluded explicitly: ``isinstance(True, int)`` is ``True`` in Python, so a naive
    numeric filter would collect ``True``/``False`` as ``1``/``0`` and make ``1 in numbers``
    meaningless.
    """
    numbers = set()
    for top in tree.body:
        if isinstance(top, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id.startswith("FIXTURE_")
            for target in top.targets
        ):
            continue
        numbers.update(
            node.value
            for node in ast.walk(top)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        )
    return numbers


def test_exactly_two_chosen_constants():
    """D-18: a reviewer auditing this pin finds EXACTLY TWO numbers to argue with.

    Everything else in the module is measured, imported or computed. The audit is run three ways
    against each other so no single one of them can be satisfied alone: the SOURCE's module-scope
    floats, the RUNTIME values of `CHOSEN_CONSTANTS`, and its KEY SET. A constant added to the
    source but left out of `CHOSEN_CONSTANTS` fails the first-vs-second comparison; one added to
    `CHOSEN_CONSTANTS` under a different name fails the third.
    """
    _collapsed_glob_guard()
    tree = _tree(_MITIGATION_GATE_PATH)

    floats = _module_scope_floats(tree)
    assert floats == {0.7, 0.5}, (
        f"the pin's module-scope float literals outside FIXTURE_* assignments are "
        f"{sorted(floats)}, not {{0.5, 0.7}}. D-18 fixes the count at TWO — `F_Y` and `F_C`, "
        "both labelled in the "
        "source as milestone PREFERENCE rather than derivation — because a reviewer auditing a "
        "pre-registration should find exactly two numbers to argue with and be able to check that "
        "every other one was measured, imported or computed"
    )
    assert floats == set(mitigation_gate.CHOSEN_CONSTANTS.values()), (
        f"the source holds {sorted(floats)} while CHOSEN_CONSTANTS holds "
        f"{sorted(mitigation_gate.CHOSEN_CONSTANTS.values())}. CHOSEN_CONSTANTS is the audit "
        "surface kept AS DATA so a reviewer needs no second hand-maintained list; the moment it "
        "disagrees with the source it is a second list, and the wrong one is the one being read"
    )
    assert set(mitigation_gate.CHOSEN_CONSTANTS) == {"F_Y", "F_C"}, (
        f"CHOSEN_CONSTANTS is keyed {sorted(mitigation_gate.CHOSEN_CONSTANTS)}. The two chosen "
        "constants are `F_Y` (the utility target, D-15/D-16) and `F_C` (the catastrophe detector, "
        "D-17), and they are SEPARATE because binding them to one number would assert a coupling "
        "Phases 13 and 19 both measured to be absent"
    )

    # THE HOLE, NARROWED AS FAR AS IT HONESTLY CAN BE. The float audit above skips FIXTURE_*
    # assignments, so a constant hidden INSIDE one of them is not caught — see
    # `_module_scope_floats`'s docstring for why that risk is accepted. What IS caught is the
    # cheapest evasion: a FOURTH fixture dict added to carry constants past the scan.
    assert _module_scope_fixture_names(tree) == {
        "FIXTURE_CLEARING_POINT",
        "FIXTURE_DESTROYED_MODEL",
        "FIXTURE_TRUNCATED_SWEEP",
    }, (
        f"the pin's module-scope FIXTURE_* names are {sorted(_module_scope_fixture_names(tree))}. "
        "Three fixtures are committed and the float audit's exclusion is scoped to exactly those "
        "three; a fourth would widen an accepted hole into an unbounded one"
    )


def test_no_imported_baseline_is_retyped():
    """GATE-02 and GATE-04: nothing measured elsewhere is retyped as a literal in the pin.

    Six values, each forbidden for its own reason and each absent from the pin's numeric constants:

      * `4.5733` / `3.891140` — the v2.0 baselines. They are IMPORTED
        (`V20_MASKED_DIALOGUE_VAL_PPL`, `V20_EWC_RETENTION_PPL`), and the difference is decided at
        the eighth decimal: the retention cap computed from the imported 3.891140 is
        3.9085032379884783, while the measured 3.891139975617828 would give 3.9085032136063065.
        "Import, never retype" is an arithmetic fact here, not a style preference.
      * `0.068930` — a Phase 12 FULL-FINE-TUNE retention floor. D-06 supersedes it for v4.0, so it
        is neither imported nor retyped: the adapter-regime floor arrives as a required kwarg.
      * `0.005214448168350039` — the committed dialogue noise floor. A required kwarg (D-07), never
        a literal.
      * `0.4921` / `0.3483` — v2.0's published recall pair. GATE-04 forbids DERIVING Y from them;
        each Y leg is `F_Y` times its OWN v4.0 retrained-control value (D-16), which reproduces the
        generalization ratio for free with no borrowed run-to-run variance.

    AN AST SCAN, NEVER A SUBSTRING SCAN, AND THE DIFFERENCE IS LOAD-BEARING HERE. `0.4921` DOES
    appear in this pin's source — inside the `F_Y` provenance comment that says the pair must never
    be used — and `0.005214448168350039` appears inside `dialogue_gap_band.__doc__`, which is where
    D-04's bit-identity proof is recorded. A substring check would report both as violations and
    would be demanding the removal of the very prose that explains the rule. Prose ABOUT a number
    is not the number; only an AST walk over `ast.Constant` can tell them apart.
    """
    _collapsed_glob_guard()
    tree = _tree(_MITIGATION_GATE_PATH)
    numbers = _numeric_constants_outside_fixtures(tree)

    for banned, why in (
        (4.5733, "the v2.0 masked dialogue baseline — IMPORTED as V20_MASKED_DIALOGUE_VAL_PPL"),
        (3.891140, "the v2.0 EWC retention baseline — IMPORTED as V20_EWC_RETENTION_PPL"),
        (0.068930, "the Phase 12 FULL-FINE-TUNE retention floor — SUPERSEDED for v4.0 by D-06"),
        (0.005214448168350039, "the committed dialogue noise floor — a required kwarg (D-07)"),
        (0.4921, "v2.0's published taught recall — GATE-04 forbids deriving Y from it"),
        (0.3483, "v2.0's published held-out recall — GATE-04 forbids deriving Y from it"),
    ):
        assert banned not in numbers, (
            f"{banned} appears as a NUMERIC CONSTANT in {_MITIGATION_GATE_PATH.name}: {why}. "
            "GATE-02's discipline is imported-never-retyped and GATE-04's is that Y is a fraction "
            "of the v4.0 retrained control, never of v2.0's published pair. A retyped baseline is "
            "a second copy of a number, free to stop matching the one it was copied from"
        )

    # The SUPERSEDED GATE-02 dialogue cap, forbidden BOTH ways. Absent as a numeric constant AND
    # as a source substring — the one value in this file for which the stricter check is correct,
    # because MITIGATION_DECISION_RULE and `dialogue_gap_band.__doc__` both discuss the superseded
    # criterion at length and both were written to name it BY ITS COMPUTATION rather than by its
    # value. A pin whose whole discipline is "computed from imported constants, never retyped"
    # must not retype the one number it supersedes, in prose any more than in code.
    superseded = 4.5837288963367
    assert superseded not in numbers, (
        f"{superseded} — GATE-02's original one-sided dialogue cap — appears as a numeric constant "
        "in the pin. It is named by its COMPUTATION, `superseded_dialogue_cap(gap_noise_floor=...)`"
    )
    assert str(superseded) not in _MITIGATION_GATE_PATH.read_text(encoding="utf-8"), (
        f"{superseded} appears as a SOURCE SUBSTRING in the pin. The superseded criterion is named "
        "by its computation everywhere it is discussed, prose included, so that the supersession "
        "is something this module PERFORMS rather than a literal a reader has to trust"
    )

    # And the k=2 discipline itself is IMPORTED rather than retyped as the integer 2.
    from_erasure_gate = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "erasure_gate"
        for alias in node.names
    }
    assert "MARGIN_K" in from_erasure_gate, (
        f"MARGIN_K is not in the pin's erasure_gate import list {sorted(from_erasure_gate)}. The "
        "k=2 margin is a project-wide discipline (Phase 13's MARGIN, erasure_gate's caps, Phase "
        "19's condition (b)) and it is IMPORTED, never retyped as a bare 2 — a local 2 is a "
        "margin that can be changed here without changing it anywhere the discipline is stated"
    )

    # THE SUPERSESSION IS A COMPUTATION, NOT A CLAIM (ROADMAP SC1). This is the one place the two
    # forbidden literals above are allowed to appear together: a test file is not the pin and is
    # not audited by the constant scans. `==`, never a tolerance — the point is BIT-EXACT
    # reproduction of the v3.0 cap from two imported constants.
    assert (
        mitigation_gate.superseded_dialogue_cap(gap_noise_floor=0.005214448168350039)
        == 4.5837288963367
    ), (
        "superseded_dialogue_cap did not reproduce GATE-02's cap exactly. Asserted with `==` and "
        "no tolerance deliberately: 'GATE-02's dialogue cap, computed from two imported constants "
        "rather than retyped' is only a fact if the computation lands on the same double"
    )


def test_destroyed_model_fixture_matches_the_published_phase19_readings():
    """D-30: the fixture's four published fields are PROVED equal to their source, not transcribed.

    A catastrophe that actually happened is not hypothetical, which is why the destroyed-model
    fixture reuses Phase 19's real M1 readings rather than fabricating a plausible disaster. But
    reusing a published number and TRANSCRIBING one are different acts, and only the first survives
    someone fat-fingering a digit — so every field that claims a published source is asserted equal
    to the parsed artifact here. The remaining fields are fabricated and say so inline; they have no
    source to be checked against (see `_module_scope_floats`).

    `control_gap` is in this list because it is the field most likely to be retyped and the float
    audit's `FIXTURE_*` exclusion would let a wrong value straight through: its true double is
    1.2420966625043919 and the plausible-looking short form 1.242096662504392 is a DIFFERENT float.
    So it is asserted as the SUBTRACTION rather than against a typed decimal, which is also how the
    fixture itself writes it.
    """
    artifact = json.loads(_PHASE19_ARM_ERASED.read_text(encoding="utf-8"))
    fixture = mitigation_gate.FIXTURE_DESTROYED_MODEL

    assert fixture["point_dialogue_ppl_on"] == artifact["dialogue_ppl"]["adapter_on"]
    assert fixture["point_dialogue_ppl_off"] == artifact["dialogue_ppl"]["adapter_off"]

    # INDEXED, not `.get()`: `retention_ppl` is a LIST `[ppl, n_targets]` in this artifact while
    # `dialogue_ppl` is a dict. Calling `.get("adapter_on")` on the list would raise, and reading
    # index [0] on the dict would raise too — the two readings genuinely have different shapes.
    assert fixture["point_retention_ppl"] == artifact["retention_ppl"][0], (
        f"the fixture's retention reading {fixture['point_retention_ppl']} is not "
        f"{artifact['retention_ppl'][0]} from {_PHASE19_ARM_ERASED.name}"
    )

    assert (
        fixture["control_gap"]
        == artifact["pre_erasure"]["dialogue_ppl"]["adapter_on"]
        - artifact["dialogue_ppl"]["adapter_off"]
    ), (
        f"the fixture's control_gap {fixture['control_gap']!r} is not the untouched taught "
        "adapter's own gap, `pre_erasure.dialogue_ppl.adapter_on - dialogue_ppl.adapter_off`. "
        "Asserted as the SUBTRACTION rather than against a decimal because the true double is "
        "1.2420966625043919 and the short form one ULP away is a different number entirely"
    )


def test_verdict_domain_stays_exactly_three():
    """GATE-01 / D-29 / D-31: three verdicts, and no fourth wearing a flag.

    `_prove_verdict_domain()` makes the relabelling claims at IMPORT, which is the right place for
    them — a dead gate should fail before the compute it would waste. They are restated here so a
    CI run proves them even if the module arrived from a `sys.modules` cache rather than being
    executed, which is exactly what happens once any other test in the session has imported it.

    D-29's `provisional` check is an AST WALK over identifiers and string constants, plus a
    normalised source read that extends the claim to comments. Not a bare `grep`: this phase has
    already had three acceptance criteria come out unsatisfiable because a naive substring scan
    conflated prose ABOUT code with the code itself, and the instrument that closes that class is
    the one being committed here.
    """
    assert mitigation_gate.V4_VERDICTS == ("PASS", "FAIL", "INCONCLUSIVE")
    assert len(mitigation_gate.V4_VERDICTS) == 3

    # (1) THE AST HALF — every identifier and every string constant, docstrings included.
    tree = _tree(_MITIGATION_GATE_PATH)
    surface = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            surface.add(node.id)
        elif isinstance(node, ast.Attribute):
            surface.add(node.attr)
        elif isinstance(node, ast.arg):
            surface.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            surface.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            surface.add(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            surface.add(node.value)
    offenders = sorted(item for item in surface if "provisional" in item.lower())
    assert offenders == [], (
        f"`provisional` reached the pin's identifiers or strings: {offenders}. A PASS carrying "
        "`provisional=True` was EXPLICITLY REJECTED (D-29): it would collapse the three-verdict "
        "domain into four disguised states and reintroduce the misreading risk "
        "`zero_results_have_nll` was built to eliminate — a truthy-pair return silently disarming "
        "the branch that needed to fire. A point clearing all three conditions without a "
        "second-seed replication returns INCONCLUSIVE, and the return carries no flag slot"
    )

    # (2) THE COMMENT HALF, routed through `_prose.normalized` — the one textual surface an AST
    # walk cannot see, since comments are discarded by the parser.
    assert (
        "provisional"
        not in _prose.normalized(_MITIGATION_GATE_PATH.read_text(encoding="utf-8")).lower()
    ), (
        "`provisional` appears in a comment in the pin. The verdict domain is exactly three names "
        "and the rejected fourth state is not discussed by name anywhere in the file"
    )

    # (3) THE RELABEL MAP, positional and with INCONCLUSIVE fixed — `_prove_verdict_domain`'s three
    # claims, restated so CI proves them rather than trusting that import-time ran.
    assert len(mitigation_gate.V4_VERDICTS) == len(erasure_gate.VERDICTS)
    for index, v3_name in enumerate(erasure_gate.VERDICTS):
        assert mitigation_gate._VERDICT_RELABEL[v3_name] == mitigation_gate.V4_VERDICTS[index], (
            f"position {index}: erasure_gate.VERDICTS[{index}] is {v3_name!r} but the relabel map "
            f"does not send it to V4_VERDICTS[{index}] = "
            f"{mitigation_gate.V4_VERDICTS[index]!r}. V4_VERDICTS must be a RELABELLING of the "
            "v3.0 domain, not a second vocabulary that happens to be three names long"
        )
    assert erasure_gate.VERDICTS.index("INCONCLUSIVE") == mitigation_gate.V4_VERDICTS.index(
        "INCONCLUSIVE"
    ), (
        "INCONCLUSIVE must sit at the same index in both vocabularies. It is the verdict this "
        "project's honest-negatives discipline exists to keep distinct from FAIL, so a silent "
        "respelling or reordering of it is the most damaging drift available"
    )


def test_every_gate_function_is_keyword_only_with_no_defaults():
    """GATE-01 over ALL public functions in the pin, not just the verdict function.

    A transposable positional argument is how two counts get swapped — `wilson_upper_bound(104, 1)`
    reads as fluently as `wilson_upper_bound(1, 104)` and means something else entirely — and a
    default is how a required anchor gets silently omitted. This pin has functions taking two,
    four, eight and twenty-one arguments; the twenty-one-argument one is where the risk is obvious
    and the two-argument ones are where it would actually happen.
    """
    tree = _tree(_MITIGATION_GATE_PATH)
    public = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    ]
    assert public, (
        f"no public function was found in {_MITIGATION_GATE_PATH.name} — this scan would be green "
        "having checked nothing"
    )
    for node in public:
        args = node.args
        assert args.posonlyargs == [], f"{node.name} takes positional-only arguments"
        assert args.args == [], (
            f"{node.name} takes {[a.arg for a in args.args]} positionally. Every argument in this "
            "pin is keyword-only — a bare `*,` first — so a caller cannot transpose two counts, "
            "which is the failure mode a decision rule reading twenty-one measured anchors is one "
            "slip away from"
        )
        assert args.defaults == [], f"{node.name} carries positional defaults"
        assert args.kw_defaults == [None] * len(args.kwonlyargs), (
            f"{node.name} carries a keyword default. GATE-01 fixes 'no defaults' because every "
            "anchor this gate reads is a MEASURED value arriving from the caller: a default would "
            "let one be silently omitted and still produce a verdict, which is precisely the "
            "protection the long argument list is being paid for"
        )


def test_gate_self_check_runs_clean_in_a_fresh_interpreter():
    """GATE-09: the `__main__` self-check, run where CI can see it fail.

    `if __name__ == "__main__":` is NOT collected by pytest, so a self-check nobody runs is not a
    guard — it is a guard-shaped comment. This runs the module as a subprocess so the six outcomes
    it prints are re-observed on every CI run rather than on the days somebody remembers.

    A FRESH INTERPRETER IS THE POINT, not an implementation detail. `_prove_verdict_domain()` and
    the `ARM_CLAIMS` proof run at IMPORT, and every other test in this file has already imported
    `mitigation_gate` — so in-process they would be `sys.modules` cache hits and would re-prove
    nothing. A subprocess executes them again from source.

    argv tuple, never `shell=True`, and `sys.executable` rather than a bare "python" so the run
    lands in the same 3.11 venv as the suite.
    """
    completed = subprocess.run(
        (sys.executable, "scripts/mitigation_gate.py"),
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.returncode == 0, completed.stderr
    for verdict in mitigation_gate.V4_VERDICTS:
        assert verdict in completed.stdout, (
            f"the self-check's stdout never names {verdict!r}:\n{completed.stdout}\nAll three "
            "verdicts are supposed to be observed firing, and a run that prints only some of them "
            "is a run in which some branch stopped being reachable"
        )


def test_every_verdict_branch_fires():
    """GATE-05…GATE-09: all six outcomes, re-asserted in CI against the SAME module-scope fixtures.

    Every fixture is IMPORTED from `mitigation_gate`, never re-transcribed: a second transcription
    is a second fixture free to stop matching, and the two would then be proving different things
    under one name.

    THE THREE PRECEDENCE CLAIMS ARE DIFFERENTIAL, AND EACH NAMES THE VERDICT IT ACTUALLY OVERRIDES.
    An INCONCLUSIVE observed on its own proves only that the branch exists; an INCONCLUSIVE that
    overrides a PASS proves nothing about precedence over FAIL. So each of the three asserts BOTH
    arms — the base verdict AND the overridden one — from otherwise-identical kwargs.
    """
    # 1 — PASS.
    v1, r1, arm1 = mitigation_gate.mitigation_point_verdict(
        **mitigation_gate.FIXTURE_CLEARING_POINT
    )
    assert v1 == "PASS", (v1, r1)

    # 2 — FAIL, from D-30's real published M1 readings. (a) and (b) both CLEAR here: condition (c)
    # is the only thing between a model whose dialogue adaptation was 77.637% destroyed and a PASS.
    v2, r2, arm2 = mitigation_gate.mitigation_point_verdict(
        **mitigation_gate.FIXTURE_DESTROYED_MODEL
    )
    assert v2 == "FAIL", (v2, r2)

    # 3 — GATE-05, DIFFERENTIAL AGAINST FAIL. Same fixture, extraction zeroed with no corroborating
    # teacher-forced NLL. An EARLY return, before any reason is appended, so the caller gets a
    # ONE-element list. The differential is against FAIL and not PASS deliberately: an INCONCLUSIVE
    # that only overrode a PASS would prove nothing about precedence over FAIL, and FAIL is the
    # verdict this branch has to be able to override.
    v3, r3, _arm3 = mitigation_gate.mitigation_point_verdict(
        **{
            **mitigation_gate.FIXTURE_DESTROYED_MODEL,
            "point_extraction_successes": 0,
            "zero_extraction_has_nll": False,
        }
    )
    assert v2 == "FAIL", v2
    assert v3 == "INCONCLUSIVE", (v3, r3)
    assert len(r3) == 1, r3

    # 4 — GATE-06, DIFFERENTIAL AGAINST FAIL. A LATE return, so every per-condition reason survives
    # it: the reader keeps the detail even though the verdict is "we could not tell".
    v4, r4, _arm4 = mitigation_gate.mitigation_point_verdict(
        **mitigation_gate.FIXTURE_TRUNCATED_SWEEP
    )
    assert v2 == "FAIL", v2
    assert v4 == "INCONCLUSIVE", (v4, r4)
    assert len(r4) > 1, r4

    # 5 — GATE-08 / D-29, DIFFERENTIAL AGAINST PASS — the OPPOSITE direction from the two above.
    out5 = mitigation_gate.mitigation_point_verdict(
        **{**mitigation_gate.FIXTURE_CLEARING_POINT, "replicated_at_second_seed": False}
    )
    assert v1 == "PASS", v1
    assert len(out5) == 3, out5
    assert out5[0] == "INCONCLUSIVE", out5
    assert out5[1][-1].startswith(mitigation_gate.REPLICATION_PENDING_MARKER), out5[1][-1]

    # 6 — GATE-07 / D-28. Arm identity travels ON the verdict, and the union CANNOT BE FORMED.
    assert arm1 == mitigation_gate.FIXTURE_CLEARING_POINT["arm"]
    assert arm2 == mitigation_gate.FIXTURE_DESTROYED_MODEL["arm"]
    assert out5[2] == mitigation_gate.FIXTURE_CLEARING_POINT["arm"]
    found, claim = mitigation_gate.exists_clearing_point(
        points=[(v1, r1, arm1), (v2, r2, arm2)], arm=arm1
    )
    assert found is True, (found, claim)
    assert claim == mitigation_gate.ARM_CLAIMS[arm1]
    with pytest.raises(SystemExit) as mixed_arm:
        mitigation_gate.exists_clearing_point(
            points=[(v1, r1, arm1), (v2, r2, "adversarial")], arm=arm1
        )
    assert "adversarial" in str(mixed_arm.value), (
        "a mixed-arm point list was refused without naming the arms it mixed. A DP clear carries a "
        "FORMAL (epsilon, delta) guarantee and an adversarial clear carries evidence about the "
        "attacks that were actually run — unioning them publishes the stronger claim on the weaker "
        "evidence, and the refusal has to say which two claims were about to be merged"
    )

    # An INCONCLUSIVE never satisfies the existential (D-29): letting it would republish "we could
    # not tell" as "it worked", silently undoing GATE-08 in the very next function that reads it.
    inconclusive_only = [out5]
    no_clear, no_claim = mitigation_gate.exists_clearing_point(
        points=inconclusive_only, arm=out5[2]
    )
    assert no_clear is False, (no_clear, no_claim)
    assert f"0 of {len(inconclusive_only)} point(s)" in no_claim, (
        f"the not-cleared claim {no_claim!r} does not carry its denominator. An existential's "
        "strength is the size of the set it searched, and 'no point cleared' without a count is "
        "indistinguishable from 'no point was scored' — a missing measurement reported as a "
        "negative result"
    )


def test_promotion_rule_and_ratchet():
    """CAL-04 / D-19 / D-20: the closed menu, the ratchet, and the rule that reaches it.

    The ratchet is what structurally eliminates the post-null K reduction
    `scripts/phase18_extraction.py:84-93` records as the ATK-03 / P18-4 weakening: fewer draws is
    less power to observe extraction, i.e. an EASIER NULL, so a reduction taken after a null buys
    the very result it is reacting to.

    `promote_to_full_fidelity` CALLS `ratchet_k` rather than re-implementing it, and the last
    assertion here is what proves that: a `full_k` below `curve_k` aborts through the promotion
    rule, which it could only do by reaching the same single implementation. Two ratchets would be
    two ratchets free to stop agreeing, and the second would be the one nobody watched fire.
    """
    assert mitigation_gate.K_RUNGS == (48, 24, 16, 8)

    # Rungs are INDEXED off the committed menu, never retyped — a second 48 is a second number free
    # to stop agreeing with the menu it is supposed to have come from.
    low, high = mitigation_gate.K_RUNGS[-1], mitigation_gate.K_RUNGS[0]
    assert mitigation_gate.ratchet_k(fixed_k=low, proposed_k=high) == high

    with pytest.raises(SystemExit) as decrease:
        mitigation_gate.ratchet_k(fixed_k=high, proposed_k=low)
    assert "ATK-03" in str(decrease.value), (
        "the ratchet refused a decrease without citing the record it exists because of. "
        "`scripts/phase18_extraction.py:84-93` is the precedent and ATK-03 / P18-4 is the "
        "weakening; a refusal that does not name them sends its reader nowhere"
    )

    off_menu = max(mitigation_gate.K_RUNGS) + 1
    with pytest.raises(SystemExit):
        mitigation_gate.ratchet_k(fixed_k=low, proposed_k=off_menu)

    pass_promoted, pass_why = mitigation_gate.promote_to_full_fidelity(
        verdict="PASS", reasons=[], curve_k=low, full_k=high
    )
    assert pass_promoted is True, pass_why

    # The GATE-CANDIDATE INCONCLUSIVE is fed the GATE'S OWN output, so the marker the promotion
    # rule matches is the one the gate actually wrote — never a hand-built reason list carrying a
    # second spelling of the same sentence.
    candidate = mitigation_gate.mitigation_point_verdict(
        **{**mitigation_gate.FIXTURE_CLEARING_POINT, "replicated_at_second_seed": False}
    )
    candidate_promoted, candidate_why = mitigation_gate.promote_to_full_fidelity(
        verdict=candidate[0], reasons=candidate[1], curve_k=low, full_k=high
    )
    assert candidate_promoted is True, candidate_why

    fail_promoted, fail_why = mitigation_gate.promote_to_full_fidelity(
        verdict="FAIL", reasons=[], curve_k=low, full_k=high
    )
    assert fail_promoted is False, fail_why

    truncated = mitigation_gate.mitigation_point_verdict(**mitigation_gate.FIXTURE_TRUNCATED_SWEEP)
    truncated_promoted, truncated_why = mitigation_gate.promote_to_full_fidelity(
        verdict=truncated[0], reasons=truncated[1], curve_k=low, full_k=high
    )
    assert truncated_promoted is False, truncated_why

    # THE RATCHET IS REACHED THROUGH ONE IMPLEMENTATION. A full-fidelity K below the curve K aborts
    # from inside the promotion rule, which is only possible if it calls `ratchet_k`.
    with pytest.raises(SystemExit) as through_promotion:
        mitigation_gate.promote_to_full_fidelity(
            verdict="PASS", reasons=[], curve_k=high, full_k=low
        )
    assert "ATK-03" in str(through_promotion.value), (
        "promote_to_full_fidelity refused a K decrease with a message that is not the ratchet's — "
        "so it is refusing through a SECOND implementation, and the two are free to stop agreeing"
    )


def test_capacity_rule_commits_both_branches_and_refuses_the_unset_fallback():
    """GATE-10 / D-25, D-26, D-27: both branches committed before either capacity runs.

    All four `(small_cleared, large_cleared)` combinations are driven at IDENTICAL mechanisms, so
    the dispatch is observed TOTAL rather than asserted to be. A missing key would be a
    fall-through, and a fall-through in a decision function is where an investigate-the-instrument
    escape hatch gets added once the data is in.
    """
    mechanism = dict.fromkeys(mitigation_gate.MECHANISM_KEYS, 1)
    observed = {}
    for small_cleared in (False, True):
        for large_cleared in (False, True):
            branch, reasons = mitigation_gate.capacity_comparison(
                small_capacity=8,
                large_capacity=64,
                small_cleared=small_cleared,
                large_cleared=large_cleared,
                small_mechanism=mechanism,
                large_mechanism=dict(mechanism),
                epsilon_independent_of_n=True,
                fallback_epsilon_tolerance=None,
            )
            assert branch in mitigation_gate.CAPACITY_BRANCHES, (branch, reasons)
            observed[(small_cleared, large_cleared)] = branch
    assert observed == {
        (False, True): "capacity-recovers",
        (False, False): "null-at-both-capacities",
        (True, False): "capacity-destroys",
        (True, True): "recovery-at-both-capacities",
    }, observed

    # THE DISPATCH'S BRANCH SET IS A SUBSET OF THE CLOSED TUPLE, so a future branch name cannot be
    # added without entering `CAPACITY_BRANCHES` — where a reader looking for the publishable
    # outcomes will actually find it.
    assert set(mitigation_gate._CAPACITY_DISPATCH.values()) <= set(
        mitigation_gate.CAPACITY_BRANCHES
    )

    # D-25 — ZERO TOLERANCE on the structural route. ONE differing mechanism key is enough.
    differing = dict(mechanism)
    differing["sigma"] = 2
    not_comparable, why = mitigation_gate.capacity_comparison(
        small_capacity=8,
        large_capacity=64,
        small_cleared=False,
        large_cleared=True,
        small_mechanism=mechanism,
        large_mechanism=differing,
        epsilon_independent_of_n=True,
        fallback_epsilon_tolerance=None,
    )
    assert not_comparable == "not-comparable", (not_comparable, why)
    assert any("sigma" in reason for reason in why), why

    # D-26 — THE THIRD CHOSEN CONSTANT, DELIBERATELY UNSET. Taking the fallback route without it
    # RAISES rather than defaulting: the constant is FLAGGED rather than smuggled, on exactly the
    # standard applied to `F_C`. It must be decided and named before Phase 21's CAL-03 runs.
    with pytest.raises(SystemExit) as unset_fallback:
        mitigation_gate.capacity_comparison(
            small_capacity=8,
            large_capacity=64,
            small_cleared=False,
            large_cleared=True,
            small_mechanism=mechanism,
            large_mechanism=dict(mechanism),
            epsilon_independent_of_n=False,
            fallback_epsilon_tolerance=None,
        )
    assert "D-26" in str(unset_fallback.value), (
        "the fallback route refused an unset tolerance without naming D-26 — the decision that "
        "deliberately left it unset — so a reader hitting this abort cannot find out why the "
        "number is missing or who owes it"
    )


def test_extraction_floor_tripwire_is_the_only_route_to_a_verdict():
    """D-14(a) as a REACHABILITY claim, not a unit test of `extraction_ceiling` alone.

    The obligation Phase 23 owes — an extraction noise floor measured on the never-taught arm
    across two seeds — travels as CODE rather than as prose, because a prose note gets missed. What
    makes it unavoidable is not that `extraction_ceiling` checks provenance, but that
    `mitigation_point_verdict` CALLS `extraction_ceiling`: there is no path to a verdict that
    computes X from an unlabelled floor, and the check sits at ONE choke point rather than at each
    call site where a later caller could forget it.

    So the tripwire is driven THROUGH the verdict function, from a fixture that otherwise PASSES.
    A test that called `extraction_ceiling` directly would prove the check exists; this proves
    there is no way around it.
    """
    single_seed = {
        **mitigation_gate.FIXTURE_CLEARING_POINT,
        "extraction_floor_provenance": {
            "arm": mitigation_gate.NEVER_TAUGHT_ARM,
            "seeds": (1337,),
        },
    }
    with pytest.raises(SystemExit) as one_seed:
        mitigation_gate.mitigation_point_verdict(**single_seed)
    assert "1 distinct" in str(one_seed.value), (
        f"the single-seed refusal does not report the count it counted: {one_seed.value}. A "
        "single-seed floor is not a noise floor, it is ONE DRAW — there is no second reading for "
        "it to vary against — and the refusal has to say so with its number"
    )

    borrowed_arm = {
        **mitigation_gate.FIXTURE_CLEARING_POINT,
        "extraction_floor_provenance": {"arm": "erase-dialogue-floor", "seeds": (1337, 2024)},
    }
    with pytest.raises(SystemExit):
        mitigation_gate.mitigation_point_verdict(**borrowed_arm)

    # And the fixture that differs from those two in ONLY the provenance still PASSES, which is
    # what makes the two aborts above attributable to the tripwire rather than to anything else.
    verdict, _reasons, _arm = mitigation_gate.mitigation_point_verdict(
        **mitigation_gate.FIXTURE_CLEARING_POINT
    )
    assert verdict == "PASS", verdict


def test_condition_a_reason_carries_its_tolerance_sentence():
    """D-14(b): no verdict is published without the reader learning how strong the criterion was.

    `scripts/erasure_gate.py:245-247` computes both of its caps into LOCALS and never returns them
    — they reach the caller only through a reason string — which is exactly what makes criterion
    strength invisible in the report it governs. `tolerance_report` is the committed surface that
    closes it, and this asserts its sentence is rendered INTO condition (a)'s reason rather than
    merely being computable by someone who thought to ask.

    The expected sentence is RECOMPUTED here from the same fixture through the same two committed
    functions, never transcribed: a hand-typed expectation would be a second copy of the sentence,
    and the day the format string changed it is the test that would be wrong.
    """
    fixture = mitigation_gate.FIXTURE_CLEARING_POINT
    _verdict, reasons, _arm = mitigation_gate.mitigation_point_verdict(**fixture)

    ceiling = mitigation_gate.extraction_ceiling(
        nontarget_successes=fixture["control_extraction_successes"],
        nontarget_questions=fixture["control_extraction_questions"],
        extraction_noise_floor=fixture["extraction_noise_floor"],
        extraction_floor_provenance=fixture["extraction_floor_provenance"],
    )
    _tolerated, _fraction, sentence = mitigation_gate.tolerance_report(
        ceiling=ceiling, n_questions=fixture["point_extraction_questions"]
    )

    condition_a = [reason for reason in reasons if reason.startswith("(a)")]
    assert len(condition_a) == 1, reasons
    assert sentence in condition_a[0], (
        f"condition (a)'s reason {condition_a[0]!r} does not carry the tolerance sentence "
        f"{sentence!r}. A criterion whose strength is invisible in its own report is the "
        "`erasure_gate.py:245-247` defect, and D-14(b) exists so the Phase 23 report can never "
        "omit how strong or weak the accepted criterion actually was"
    )
