"""Phase 39 E6 (CTX-02) — instrument x context, on MPS under the ledger.

    .venv/bin/python scripts/phase39_ctx.py preflight   # every refusal, writes nothing
    .venv/bin/python scripts/phase39_ctx.py run         # THE run: gates, then one scoring pass
    .venv/bin/python scripts/phase39_ctx.py crosscheck  # CPU cross-check (descriptive; plan 06)
    .venv/bin/python scripts/phase39_ctx.py emit        # the write-once record (plan 06)
    .venv/bin/python scripts/phase39_ctx.py report      # the report, from the record (plan 07)

WHAT E6 MEASURES. For each of the eight locked slots under each adapter reading, the same fact read
by two instruments in two contexts: R_a (the taught value's rank in the anchor context a, the
``ans1`` frame of phase18_extraction.value_span_nll), R_q (n1, the questions of the 27 A2 entries
whose taught value ranks 1 in the question context b, ``_guarded_span(entry)`` plus the whole
value), G_a (some hit in K anchor draws) and G_q (the committed A2 answered count). Two extras are
descriptive only and never classified: (i) the adapter switched off, (ii) the minted reference
sets at |R| = 8 (phase39_prereg.minted_members).

GATE 1 (D-18 + D-30 condition 1). Before anything new is scored, every committed
reference_set_for cell is scored by BOTH the pinned value_span_nll and this module's copy of
span_nll_from_ids; nll_sum and nll_mean must be bitwise equal in every cell, and the committed
ranks must be reproduced.

GATE 2 (D-19). The committed A2 counts are re-derived from the SHA-verified draws
(phase39_prereg.gate2) in preflight; a mismatch refuses before the ledger start line.

LEDGER DISCIPLINE (D-03). Every refusal runs BEFORE the ledger start line and writes nothing; the
committed stop is ``phase36_ledger.require_launch("E6")``, no second stop rule.

A partial shape (readings / slots) and a CPU device exist only for a rehearsal into a tmp root
outside the repository; the real root runs the full READINGS x SLOTS shape on MPS.

Torch-free at import: phase39_prereg (torch through phase35_prereg.a2_corpus_entries) and every
torch-importing module are imported inside the functions that need them.
"""

import contextlib
import datetime
import gc
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, beat, start_heartbeat
import phase36_caps  # noqa: E402
import phase36_ledger  # noqa: E402
import phase36_probe  # noqa: E402  — adapted_model, silenced (torch-free)
import phase38_prereg  # noqa: E402  (torch-free; frozen: import only)
import phase38_rank  # noqa: E402  (torch-free at import; pinned: import only)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

# FIXED: the cwd of every git call, the base of the module digests and of every tracked input.
_REPO = pathlib.Path(__file__).resolve().parent.parent
# The default OUTPUT root (results/, data/) and the identity that selects the real-root branches.
_ROOT = _REPO
FRONT = "E6"
RUN_ID = phase36_ledger.run_id(39, FRONT, "ctx")
# 38-REVIEW DI-01: artifacts/ (the tokenizer) is part of the clean-tree check.
LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")
PREREG_FILE = "scripts/phase39_prereg.py"
# 38-REVIEW DI-05: the src-modules half of DI-05's fix plus the modules that define MARGIN
# (erasure_gate, phase19_floor) and the Wilson bounds (erasure_gate, phase20_gate_coverage); NOT the
# full transitive import closure, and NOT DI-05's optional base-checkpoint digest
# (checkpoints/convbase_slim.pt is not hashed; the 64-cell gate 1 is the de facto check on the
# base, as in Phase 38).
MODULES = (
    "scripts/erasure_gate.py",
    "scripts/phase14_factset.py",
    "scripts/phase14_recall.py",
    "scripts/phase16_persistence.py",
    "scripts/phase18_extraction.py",
    "scripts/phase19_erasure.py",
    "scripts/phase19_floor.py",
    "scripts/phase19_run.py",
    "scripts/phase20_gate_coverage.py",
    "scripts/phase25_run.py",
    "scripts/phase35_prereg.py",
    "scripts/phase36_caps.py",
    "scripts/phase36_ledger.py",
    "scripts/phase36_probe.py",
    "scripts/phase38_prereg.py",
    "scripts/phase38_rank.py",
    PREREG_FILE,
    "scripts/phase39_ctx.py",
    "scripts/teach_persona.py",
    "src/personacore/lora/inject.py",
    "src/personacore/lora/layer.py",
    "src/personacore/lora/config.py",
    "src/personacore/model/gpt.py",
)
RUN_PROVENANCE_KEYS = (
    "git_sha_at_launch",
    "git_sha_at_end",
    "head_moved_during_run",
    "device",
    "torch_version",
    "started_utc",
    "finished_utc",
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase39_ctx] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _json(rel):
    return json.loads((_REPO / rel).read_text(encoding="utf-8"))


def _load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def module_sha256():
    """``{rel: sha256}`` of MODULES as they are in the repository now."""
    return {rel: _sha256(_REPO / rel) for rel in MODULES}


def _is_real(root):
    """The real root, or any root inside the repository: full shape and MPS only."""
    resolved = pathlib.Path(root).resolve()
    return resolved == pathlib.Path(_ROOT).resolve() or resolved.is_relative_to(_REPO.resolve())


def _prereg():
    """phase39_prereg, imported lazily (torch at import through the A2 corpus)."""
    import phase39_prereg

    return phase39_prereg


def _taught():
    import phase14_factset

    return {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}


def _guard_values():
    """Every locked and soft-tier value: the list stage_e6 guards the anchor prompt against."""
    import phase14_factset

    return [f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS]


def run_sidecar(root):
    return pathlib.Path(root) / "data" / "phase39_ctx_run.json"


def gate_sidecar(root):
    return pathlib.Path(root) / "data" / "phase39_ctx_gate.json"


def cpu_sidecar(root):
    return pathlib.Path(root) / "data" / "phase39_ctx_cpu.json"


def reading_sidecar(root, reading):
    readings = _prereg().READINGS
    _prove(reading in readings, f"{reading!r} is not one of {readings}")
    return pathlib.Path(root) / "data" / f"phase39_ctx_{reading}.json"


def outputs(root):
    """The record path, then every sidecar path: all must be absent before a run."""
    return (
        pathlib.Path(root) / _prereg().CTX_RECORD,
        run_sidecar(root),
        gate_sidecar(root),
        cpu_sidecar(root),
        *(reading_sidecar(root, reading) for reading in _prereg().READINGS),
    )


def tracked_inputs():
    """The tracked inputs the run reads, repo-relative: each must be committed before E6."""
    import phase18_extraction

    prereg = _prereg()
    corpus = pathlib.Path(phase18_extraction.CORPUS_PATH).resolve().relative_to(_REPO.resolve())
    paths = (
        PREREG_FILE,
        *(prereg.A2_RECORDS[reading]["path"] for reading in prereg.READINGS),
        phase38_prereg.MINTING_RECORD,
        phase38_prereg.RANK_RECORD,
        corpus.as_posix(),
        prereg.BUDGET_RECORD,
        phase38_prereg.PROBE_E1_RECORD,
        prereg.PROBE_E6_RECORD,
    )
    return tuple(dict.fromkeys(paths))


def run_inputs():
    """Every input file the run reads: refused before the start line when missing, because
    `refuse_if_dirty` cannot see the gitignored ones (checkpoints/)."""
    import phase14_recall

    paths = (
        phase14_recall.CONVBASE_SLIM,
        phase14_recall.ADAPTER_PATH,
        phase14_recall.TOKENIZER_PATH,
        phase38_rank.m2_adapter_path(),
        *phase38_rank.run_inputs()[4:],  # the Phase 38 reader set's tracked JSONs
        *(_REPO / rel for rel in tracked_inputs()),
    )
    return tuple(dict.fromkeys(paths))


def _device():
    from personacore.preflight import preflight_device

    return preflight_device(strict=True)["device"]


def _write_once(path, blob):
    _prove(not path.exists(), f"{path} exists: the sidecars are write-once")
    path.parent.mkdir(parents=True, exist_ok=True)
    phase25_run.atomic_write_json(path, blob)


@contextlib.contextmanager
def reading_model(reading, device):
    """``(model, tok, forbid)`` for one reading; the model is released on exit."""
    import torch

    prereg = _prereg()
    _prove(reading in prereg.READINGS, f"{reading!r} is not one of {prereg.READINGS}")
    scope = contextlib.nullcontext()
    if reading == "M2":
        import phase14_recall

        model, _cfg, tok, forbid, _artifact = phase14_recall.load_adapted_model(
            device, adapter_path=phase38_rank.m2_adapter_path()
        )
    else:
        k = 0 if reading == "adapter_off" else int(reading[1:])
        _prove(k in prereg.PREFIXES, f"k = {k} is not one of {prereg.PREFIXES}")
        model, tok, forbid = phase36_probe.adapted_model(device, k)
        if reading == "adapter_off":
            from personacore.lora import adapter_disabled

            scope = adapter_disabled(model)
    try:
        with scope:
            yield model, tok, forbid
    finally:
        model = None
        gc.collect()
        if torch.backends.mps.is_available():  # never reached on a CPU-only host (ubuntu CI)
            torch.mps.empty_cache()
