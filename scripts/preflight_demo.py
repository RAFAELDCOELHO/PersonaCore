"""Thin env-summary entry point — runs on a CPU laptop AND (manually) on Kaggle.

Wires together the Phase-1 primitives with no logic of its own (logic lives in
``src/personacore/``): seed the run, capture the git SHA, and print the preflight summary.
``preflight_device(strict=False)`` is the laptop summary path so it completes on any box —
on the user's M3 this resolves to MPS, elsewhere to CPU. On Kaggle cell-1 call
``preflight_device()`` (strict=True) to assert a live P100 (or MPS) before a long run.

Path/mount CONVENTION (D-07 — convention ONLY; the actual TinyStories encode/upload is
Phase 5, no data is downloaded here):

- ``CHECKPOINT_DIR = /kaggle/working/checkpoints`` — resumable ``latest.pt`` is written here
  during a run, then persisted to a versioned Kaggle Dataset before the session wipes.
- ``DATA_DIR = /kaggle/input/personacore-tinystories`` — the pre-encoded ``uint16`` memmap
  (``train.bin`` / ``val.bin``) is mounted READ-ONLY from a Kaggle Dataset (Phase 5 provisions
  it; nothing is encoded or downloaded in Phase 1).
"""

from personacore.preflight import preflight_device
from personacore.provenance import git_sha
from personacore.seeding import seed_everything

# Path/mount convention (D-07) — strings only; no I/O, no download in Phase 1.
CHECKPOINT_DIR = "/kaggle/working/checkpoints"
DATA_DIR = "/kaggle/input/personacore-tinystories"


def main() -> None:
    seed_everything(1337)
    print(f"[demo] git_sha={git_sha()}")
    print(f"[demo] checkpoint_dir={CHECKPOINT_DIR} data_dir={DATA_DIR}")
    info = preflight_device(strict=False)
    print(f"[demo] preflight ok: {info}")


if __name__ == "__main__":
    main()
