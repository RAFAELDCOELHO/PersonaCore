"""Offline append-only CSV logger.

The reproducibility/zero-budget intent (CLAUDE.md) forbids wandb/online tooling — training
curves are logged to a plain CSV that ``demo.ipynb`` (Phase 8) reads back with matplotlib.

The load-bearing property is **restart survivability**: Kaggle sessions cap at ~9h and wipe
in-memory state, so a resumed run must APPEND to the existing log without duplicating the
header. ``CSVLogger`` opens in append mode and writes the header only when the file is new or
empty — re-opening on the same path after a restart continues the same CSV.
"""

import csv
import os


class CSVLogger:
    """Append-only CSV writer that survives a process restart.

    Opens ``path`` in append mode; writes the header row exactly once (only if the file did
    not already exist with content). ``.log(**row)`` appends a row and flushes to disk so a
    mid-run kill loses nothing.
    """

    def __init__(self, path, fieldnames):
        self.path = os.fspath(path)
        self.fieldnames = list(fieldnames)
        # Header only if the file is new/empty — reopen-safe across a restart.
        write_header = not (os.path.exists(self.path) and os.path.getsize(self.path) > 0)
        self._fh = open(self.path, "a", newline="")
        self._writer = csv.DictWriter(self._fh, fieldnames=self.fieldnames)
        if write_header:
            self._writer.writeheader()
            self._fh.flush()

    def log(self, **row) -> None:
        """Append one row (keys must match ``fieldnames``) and flush to disk."""
        self._writer.writerow(row)
        self._fh.flush()

    def close(self) -> None:
        """Close the underlying file handle."""
        if self._fh is not None and not self._fh.closed:
            self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
