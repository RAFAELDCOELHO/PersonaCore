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

import pathlib
import subprocess

_ROOT = pathlib.Path(__file__).resolve().parent.parent

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
