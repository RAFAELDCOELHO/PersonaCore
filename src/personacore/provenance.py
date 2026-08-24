"""Git provenance capture (QA-02).

``git_sha()`` records the exact commit a run was produced from so any checkpoint can be
traced back to source. Reproducibility in this project comes from git + the recorded SHA
(D-01), not from config files — making this the load-bearing provenance primitive.

The capture NEVER aborts a run: when ``.git`` is absent (e.g. a Kaggle Dataset copy of the
code rather than a clone — Pitfall 4) it returns the ``default`` ("unknown") instead of
raising. Provenance is best-effort; a missing SHA must not kill a long Kaggle job.

``refuse_if_dirty()`` is the OTHER half, and it lives here rather than in a caller because
``git_sha()`` is the function whose output it qualifies. A SHA recorded from a dirty tree
names a commit that does NOT contain the code that produced the record — the artifact points
at a tree it cannot be regenerated from. Phase 21 shipped exactly that defect twice
(``21-REVIEW.md`` CR-02: both ``results/phase21_*.json`` recorded a ``git_sha`` under which
their own emitter was not yet defined), so the refusal now sits next to the primitive, where
the next caller that PUBLISHES a SHA will find it.

**The two are deliberately NOT wired together.** ``git_sha()`` must stay best-effort: it is
called by ``save_checkpoint`` on every training run, and training from a dirty tree is normal
and must never abort. ``refuse_if_dirty()`` is opt-in and belongs only to callers that
PUBLISH a permanent, committed record whose whole value is that the SHA can reproduce it.
"""

import subprocess


def git_sha(default: str = "unknown") -> str:
    """Return the current ``HEAD`` commit SHA, or ``default`` if git is unavailable.

    Wraps ``git rev-parse HEAD`` in a broad try/except so a missing ``.git`` directory,
    a missing git binary, or any subprocess failure degrades gracefully to ``default``.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        # No .git (Dataset copy), no git binary, or any other failure -> never crash.
        return default


def refuse_if_dirty(*, who, detail, pathspec=(), cwd=None):
    """``SystemExit`` unless ``pathspec`` is clean in git. Returns the (empty) status on success.

    The counterpart to :func:`git_sha` for callers that PUBLISH a SHA — see this module's
    docstring for why it is opt-in rather than folded into ``git_sha()``.

    ``pathspec`` is passed to ``git status --porcelain`` after ``--``, so it takes git's own
    pathspec syntax including ``:(exclude)``. An empty tuple means the WHOLE tree. Callers name
    their own scope because the honest scope differs: a driver about to import a sibling module
    watches that module, while an emitter about to write a permanent record watches everything
    except the record it is replacing.

    ``who`` prefixes the abort and ``detail`` states what the dirt would falsify, because a
    refusal that does not say what it prevented gets deleted by the next person who hits it.

    Untracked files count as dirty. A ``.py`` that is not in HEAD cannot be at the recorded SHA
    either, so a record produced with one in the import path is exactly as unreproducible as one
    produced from a modified tracked file. ``.gitignore``d paths (``data/``, ``checkpoints/``)
    are invisible to ``--porcelain`` and correctly do not block: they are inputs the SHA never
    claimed to carry.

    A git failure (no binary, no ``.git``) raises ``CalledProcessError`` rather than degrading —
    the opposite of ``git_sha``'s posture, and deliberately so. Here, "cannot tell" must not read
    as "clean": a guard that silently passes when it could not run is the guard-that-cannot-fail
    class this project keeps removing.
    """
    args = ["git", "status", "--porcelain"]
    if pathspec:
        args += ["--", *pathspec]
    dirty = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit(f"[{who}] REFUSING: the working tree is dirty.\n{dirty}\n{detail}")
    return dirty
