"""Git provenance capture (QA-02).

``git_sha()`` records the exact commit a run was produced from so any checkpoint can be
traced back to source. Reproducibility in this project comes from git + the recorded SHA
(D-01), not from config files — making this the load-bearing provenance primitive.

The capture NEVER aborts a run: when ``.git`` is absent (e.g. a Kaggle Dataset copy of the
code rather than a clone — Pitfall 4) it returns the ``default`` ("unknown") instead of
raising. Provenance is best-effort; a missing SHA must not kill a long Kaggle job.
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
