"""PREREG-02: the pre-registered erasure rule was committed BEFORE the numbers it judges.

``scripts/erasure_gate.py`` states, in prose, what would make selective erasure worth attempting
and what erasure would have to achieve to count as successful. That prose is only worth anything
if it was written blind — before Phase 16, 17 or 18 produced a single result. Its own docstring
makes exactly that claim and names git history as the proof. This module is what turns the claim
into a checkable fact: for every v3.0 results artifact on disk, the commit that FIRST ADDED it must
be a descendant of the commit that added the rule. A threshold chosen after seeing the data is not
a threshold, and a pre-registration nobody can verify the date of is not a pre-registration.

**Ancestry, never dates.** The obvious implementation compares committer dates and is wrong.
Committer dates are rewritable by anyone with a shell, skewed across machines, and non-monotonic
after a rebase — a history rewrite could invert the ordering this guard claims to enforce while
both dates still look perfectly ordered. Ancestry is a property of the commit DAG: to make
``git merge-base --is-ancestor`` lie you would have to rewrite every object between the two
commits, which changes both SHAs, which fails the identity check below. So the ordering is asked
of the object graph, not of a clock.

**Three ways this guard could be green while proving nothing, all closed here.**

  1. *A shallow clone.* ``actions/checkout`` defaults to ``fetch-depth: 1``, and in a depth-1 clone
     the pre-registration commit object simply is not present — the ancestry question cannot be
     answered at all. That is failed loudly with a named reason rather than skipped:
     a silently-skipped ordering guard is the "declared invariant silently becomes false" defect
     this project names as its most recurring. ``.github/workflows/ci.yml`` carries the
     ``fetch-depth: 0`` that makes the check answerable in CI.
  2. *An empty match set.* If the artifact globs stop matching — renamed directory, moved results,
     a typo — every loop below runs zero times and the test passes having checked nothing. The
     closing ``assert checked`` is what makes that outcome red.
  3. *A wrong pinned SHA.* An ancestry assertion against an unrelated (but genuinely early) commit
     passes just as happily as one against the real pre-registration. So the SHA is also checked
     for IDENTITY: it must resolve, and the commit it resolves to must actually touch the erasure
     gate. The pin is the full 40 characters — an abbreviated SHA can become ambiguous as the
     object store grows, and this pin has to outlive the repository.

An artifact that exists in the working tree but has never been committed has no history at all,
so it is trivially after the pre-registration. Those are collected by name rather than dropped
in silence, and reported if the guard ends up having checked nothing.

CPU-only, GPU-free, no torch, no network.
"""

import pathlib
import subprocess

# PREREG-01: the commit that added scripts/erasure_gate.py. Full 40 characters, never the short
# form — an abbreviation is a prefix query against a growing object store, and this pin must stay
# unambiguous for the life of the repository.
PREREG_COMMIT = "23a830c0181acf799dadc1e9aecdf1818d8678e2"

# Every v3.0 results artifact. Phases 16, 17 and 18 are the milestone whose numbers the
# pre-registered rule judges; a new phase writing results under a fourth prefix must be added here,
# and the `assert checked` below is what makes a silently-stale list visible.
V3_ARTIFACT_GLOBS = ("results/phase16_*", "results/phase17_*", "results/phase18_*")

PREREG_ARTIFACT = "scripts/erasure_gate.py"

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_prereg_commit_precedes_every_v3_results_artifact():
    """Every committed v3.0 results artifact was added AFTER the erasure rule was pre-registered.

    Fails loudly, never skips: on a shallow clone, on a non-ancestor, and on an empty match set.
    """
    # A shallow clone does not hold the pre-registration commit object, so it cannot answer an
    # ancestry question — it can only fail to find one. Assert, never skip.
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the pre-registration commit object is absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )

    checked = 0
    untracked = []
    for pattern in V3_ARTIFACT_GLOBS:
        for path in sorted(_ROOT.glob(pattern)):
            rel = path.relative_to(_ROOT).as_posix()
            adds = _git("log", "--diff-filter=A", "--format=%H", "--", rel).split()
            if not adds:
                # Working-tree only: no history at all, so trivially after the pre-registration.
                # Recorded by name so this branch is a stated outcome, not an empty loop.
                untracked.append(rel)
                continue
            # git log is newest-first, so the commit that ADDED the file is the last entry.
            first_add = adds[-1]
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", PREREG_COMMIT, first_add),
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked, (
        "no committed v3.0 results artifact was checked — the guard matched nothing. "
        f"Globs {V3_ARTIFACT_GLOBS} found only uncommitted paths {untracked}. "
        "A pre-registration guard that checks zero artifacts is green and blind."
    )


def test_prereg_commit_exists_and_touches_the_erasure_gate():
    """The pinned SHA is the pre-registration itself, not merely some early commit.

    Without this, a typo in the pin degrades the ancestry check into a tautology: almost any old
    commit in this repository is an ancestor of every v3.0 artifact, so a wrong SHA would stay
    green forever. Identity is checked two ways — the SHA must resolve to itself, and the commit
    it names must actually touch the pre-registered rule.
    """
    resolved = _git("log", "-1", "--format=%H", PREREG_COMMIT)
    assert resolved == PREREG_COMMIT, (
        f"pinned pre-registration SHA resolved to {resolved!r}, not itself — "
        "the pin is not a full, unambiguous commit id"
    )

    touched = _git("show", "--stat", "--format=", PREREG_COMMIT)
    assert PREREG_ARTIFACT in touched, (
        f"commit {PREREG_COMMIT} does not touch {PREREG_ARTIFACT}; it is not the "
        f"pre-registration commit. Files it does touch:\n{touched}"
    )
