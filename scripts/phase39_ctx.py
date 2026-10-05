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
import math
import os
import pathlib
import subprocess
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
# D-21 / D-27: the modules that decide what is scored and are NOT frozen by an earlier record (no
# record precedes the E6 run, unlike Phase 38's minting record); the rehearsal identity pins them.
DISCLOSED_MODULES = ("scripts/phase39_ctx.py", PREREG_FILE)
_IDENTITY_KEYS = {"git_sha", "module_sha256", "readings", "slots", "started_utc"}
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


_prove(set(DISCLOSED_MODULES) <= set(MODULES), "DISCLOSED_MODULES must be a subset of MODULES")


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


def rehearsal_identity_path():
    """D-21 / D-27: the gitignored rehearsal identity under the output root (read at call time)."""
    return pathlib.Path(_ROOT) / "data" / "phase39_rehearsal.json"


def _kept_identity(path, *, readings, slots):
    """The identity already at ``path`` (None when absent), refused when it recorded a different
    slice: a wider rehearsal would go undisclosed under it (38-REVIEW DR-02)."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    kept = _load(path)
    _prove(
        (kept["readings"], kept["slots"]) == (list(readings), list(slots)),
        f"{path} recorded a different slice ({kept['readings']} x {kept['slots']}); a wider "
        "rehearsal would go undisclosed (D-21, 38-REVIEW DR-02)",
    )
    return kept


def record_rehearsal(path, *, readings, slots):
    """D-21 / D-27: the FIRST attempt that passed preflight is THE rehearsal; its identity (prereg
    digest included) is never overwritten, and a later attempt of another slice refuses."""
    path = pathlib.Path(path)
    kept = _kept_identity(path, readings=readings, slots=slots)
    if kept is not None:
        print(f"REHEARSAL KEPT {kept['git_sha']}", flush=True)
        return {"status": "kept", **kept}
    identity = {
        "git_sha": git_sha(),
        "module_sha256": {rel: _sha256(_REPO / rel) for rel in DISCLOSED_MODULES},
        "readings": list(readings),
        "slots": list(slots),
        "started_utc": _now(),
    }
    phase25_run.atomic_write_json(path, identity)
    print(f"REHEARSAL RECORDED {identity['git_sha']}", flush=True)
    return {"status": "recorded", **identity}


def rehearsal_disclosure(identity, *, launch_git_sha, launch_module_sha256):
    """D-21 / D-27: every commit touching a DISCLOSED_MODULES file between the rehearsal and the
    launch, its subject as the reason, and per-module changed flags (the prereg's on its own)."""
    log = subprocess.run(
        (
            "git",
            "log",
            "--format=%H%x09%s",
            f"{identity['git_sha']}..{launch_git_sha}",
            "--",
            *DISCLOSED_MODULES,
        ),
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits = []
    for line in log.splitlines():
        sha, reason = line.split("\t", 1)
        touched = subprocess.run(
            ("git", "show", "--name-only", "--format=", sha),
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        modules = [rel for rel in DISCLOSED_MODULES if rel in touched]
        commits.append({"sha": sha, "reason": reason, "modules": modules})
    changed = {
        rel: launch_module_sha256[rel] != identity["module_sha256"][rel]
        for rel in DISCLOSED_MODULES
    }
    driver_changed = any(changed.values())
    _prove(
        not driver_changed or commits,
        "a disclosed module changed after the rehearsal without a commit (D-21, D-27)",
    )
    slice_read = {key: identity[key] for key in ("readings", "slots")}
    return {
        "statement": (
            f"The CPU rehearsal (39-07) read {', '.join(slice_read['slots'])} under "
            f"{len(slice_read['readings'])} readings, all their A2 entries, before the driver "
            "review and the MPS run (D-21, D-27)."
        ),
        "slice_read": slice_read,
        "rehearsal_git_sha": identity["git_sha"],
        "rehearsal_module_sha256": identity["module_sha256"],
        "launch_git_sha": launch_git_sha,
        "launch_module_sha256": {rel: launch_module_sha256[rel] for rel in DISCLOSED_MODULES},
        "changed": changed,
        "prereg_changed": changed[PREREG_FILE],
        "driver_changed": driver_changed,
        "commits": commits,
    }


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


def span_nll_tokens(model, context_ids, value_ids, device, *, suffix_from=None):
    """D-30 (Rafael's Option 1): the driver-held COPY of phase18_extraction.span_nll_from_ids.

    Line for line the pinned body — the same ``_prove`` checks, the same single forward, the same
    span mask, the same two ``cross_entropy`` calls (sum, mean) in the same order — plus, on the
    SAME logits, ``cross_entropy(reduction='none')`` for the per-token values (D-23a) and, when
    ``suffix_from`` is given, a separate ``cross_entropy(reduction='sum')`` over a mask holding only
    the value targets from ``suffix_from`` on (D-30a: never a slice or sum of ``per_token``).

    Condition 1: gate 1 scores every cell through both this copy and the pinned value_span_nll and
    requires nll_sum and nll_mean bitwise equal. Condition 2: ``per_token`` and ``suffix_nll_sum``
    are descriptive only; ranks, n1 and every event read ``nll_mean`` / ``nll_sum``.
    """
    import torch
    import torch.nn.functional as F

    _prove(
        len(context_ids) >= 1,
        "a span NLL with an empty context has nothing to predict its first value token FROM; "
        "every frame is anchored on the assistant-turn opening precisely so this cannot happen",
    )
    _prove(
        len(value_ids) >= 1,
        "a span NLL over zero value tokens has no denominator, and its mean would be a "
        "ZeroDivisionError dressed up as a missing fact",
    )
    _prove(
        suffix_from is None or 1 <= suffix_from < len(value_ids),
        f"suffix_from {suffix_from!r} must leave at least one value id on each side "
        f"(1 <= suffix_from < {len(value_ids)}) (D-30a)",
    )
    ids = list(context_ids) + list(value_ids)
    with torch.no_grad():
        x = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
        y = torch.tensor([ids[1:]], dtype=torch.long, device=device)
        # Target index i predicts ids[i+1], so the value targets start at len(context_ids) - 1.
        span = torch.zeros_like(y, dtype=torch.bool)
        span[:, len(context_ids) - 1 :] = True
        targets = y
        y = y.masked_fill(~span, -100)
        logits, _ = model(x)
        flat_logits = logits.view(-1, logits.size(-1))
        flat_y = y.reshape(-1)
        nll_sum = F.cross_entropy(flat_logits, flat_y, reduction="sum", ignore_index=-100)
        nll_mean = F.cross_entropy(flat_logits, flat_y, reduction="mean", ignore_index=-100)
        n_scored = int((flat_y != -100).sum())
        per = F.cross_entropy(flat_logits, flat_y, reduction="none", ignore_index=-100)
        per_token = [float(v) for v in per[flat_y != -100]]
        suffix_nll_sum = None
        if suffix_from is not None:
            suffix = torch.zeros_like(targets, dtype=torch.bool)
            suffix[:, len(context_ids) - 1 + suffix_from :] = True
            y_suffix = targets.masked_fill(~suffix, -100)
            suffix_nll_sum = float(
                F.cross_entropy(
                    flat_logits, y_suffix.reshape(-1), reduction="sum", ignore_index=-100
                )
            )
    _prove(
        n_scored == len(value_ids),
        f"the span mask scored {n_scored} targets against {len(value_ids)} value ids. The count IS "
        "the claim: a mask off by one to the left scores the preamble's last token and reports a "
        "number about the frame as evidence about the value",
    )
    return {
        "n_scored": n_scored,
        "nll_sum": float(nll_sum),
        "nll_mean": float(nll_mean),
        "per_token": per_token,
        "suffix_from": suffix_from,
        "suffix_nll_sum": suffix_nll_sum,
    }


def _same_bits(a, b):
    return float(a).hex() == float(b).hex()


def anchor_ids(tok, slot):
    """Context (a): byte for byte the context phase18_extraction.value_span_nll builds at the
    admissible frame (D-04)."""
    import phase14_factset
    import phase18_extraction

    from personacore.dialogue import ASSISTANT_ID

    preamble = phase18_extraction._frame_preamble(
        phase14_factset.SLOT_FORMS[slot], phase18_extraction.ADMISSIBLE_NLL_FRAME
    )
    return [ASSISTANT_ID] + list(tok.encode(preamble))


def gate_cells(model, tok, device, slot, state):
    """D-18 + D-30 condition 1: every committed reference of ``slot`` scored by BOTH the pinned
    value_span_nll and the copy; a cell is equal only when both sums and both means are bitwise
    equal."""
    import phase18_extraction

    frame = phase18_extraction.ADMISSIBLE_NLL_FRAME
    context = anchor_ids(tok, slot)
    cells = {}
    with phase36_probe.silenced():
        for i, candidate in enumerate(phase18_extraction.reference_set_for(slot)):
            state["draw_index"] = i
            row = phase18_extraction.value_span_nll(
                model, tok, device, slot=slot, value=candidate, frame=frame
            )
            pinned = {key: row[key] for key in ("n_scored", "nll_sum", "nll_mean")}
            copy = span_nll_tokens(model, context, list(tok.encode(candidate)), device)
            cells[candidate] = {
                "pinned": pinned,
                "copy": copy,
                "equal": _same_bits(pinned["nll_sum"], copy["nll_sum"])
                and _same_bits(pinned["nll_mean"], copy["nll_mean"]),
            }
    return cells


def anchor_draws(model, tok, device, forbid, slot, reading):
    """G_a (D-05 / D-06 / D-08 / D-28): K draws from the anchor ids, every draw kept.

    Undecorated and asserting in place: tests/test_phase14_scoring.py's draw_all census."""
    import phase14_factset
    import phase14_recall
    import phase16_persistence
    import phase19_erasure

    prereg = _prereg()
    _prove(
        phase16_persistence.forbid_digest(forbid) == phase19_erasure.FORBID_IDS_SHA256,
        f"{reading}: the forbid mask is not the committed one (FORBID_IDS_SHA256)",
    )
    ids = anchor_ids(tok, slot)
    # PERS-06: nothing draws unchecked, on the ids actually dispatched.
    phase14_recall.assert_no_value_in_prompt(tok, tok.decode(ids), _guard_values(), prompt_ids=ids)
    with phase36_probe.silenced():
        completions, stopped = phase14_recall.draw_all(
            model, tok, ids, device, forbid, prereg.anchor_seed_index(slot), n_samples=prereg.K - 1
        )
    _prove(
        len(completions) == len(stopped) == prereg.K,
        f"{reading}/{slot}: {len(completions)} anchor draws, not K = {prereg.K} (D-05)",
    )
    fact_id = next(f.id for f in phase14_factset.LOCKED_FACTS if f.slot == slot)
    return {
        "family": "anchor",
        "dose": None,
        "fact_id": fact_id,
        "slot": slot,
        "tier": None,
        "arm": reading,
        "seed_index": prereg.SLOTS.index(slot),
        "prefix_text": None,
        "completions": list(completions),
        "stopped": list(stopped),
        "prompt_ids": ids,
    }


def score_question(model, tok, device, entry, candidates, *, taught, state):
    """Context (b) (D-23): each candidate scored by the copy after ``_guarded_span(entry)``, one
    call per candidate, never batched; only the taught value gets the D-23b suffix sum."""
    import phase14_recall
    import phase18_extraction

    context = phase18_extraction._guarded_span(entry)
    realized = entry["realized_injection"]
    _prove(
        list(entry["prompt_ids"]) == context + list(tok.encode(taught))[:realized],
        f"D-23b premise broken for {entry['fact_id']!r}/{entry['seed_index']}: prompt_ids are not "
        "the guarded span plus the taught value's first realized_injection ids",
    )
    phase14_recall.assert_no_value_in_prompt(
        tok, tok.decode(context), _guard_values(), prompt_ids=context
    )
    rows = {}
    with phase36_probe.silenced():
        for i, candidate in enumerate(candidates):
            state["draw_index"] = i
            rows[candidate] = span_nll_tokens(
                model,
                context,
                list(tok.encode(candidate)),
                device,
                suffix_from=realized if candidate == taught else None,
            )
    return rows


def preflight(*, root=None, ledger_path=None, device=None, readings=None, slots=None):
    """Every refusal before the ledger start line (D-02, D-03, D-11, D-19, D-20). Writes nothing."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else _ROOT
    # The I/O-free checks first (D-11, 38-REVIEW DI-02, D-21).
    readings = tuple(readings) if readings is not None else prereg.READINGS
    _prove(readings, "no readings: an empty run measures nothing (38-REVIEW DI-02)")
    for reading in readings:
        _prove(reading in prereg.READINGS, f"{reading!r} is not one of {prereg.READINGS}")
    _prove(
        len(readings) <= prereg.APPROVED_E6_ADAPTERS,
        f"{len(readings)} readings exceed the D-11 approval of {prereg.APPROVED_E6_ADAPTERS}",
    )
    slots = tuple(slots) if slots is not None else prereg.SLOTS
    _prove(slots, "no slots: an empty run measures nothing (38-REVIEW DI-02)")
    for slot in slots:
        _prove(slot in prereg.SLOTS, f"{slot!r} is not one of {prereg.SLOTS}")
    resolved = device or _device()
    _prove(
        resolved == "mps" or not _is_real(root),
        f"E6 runs on MPS on the real root (D-21); resolved {resolved!r}. A CPU device is only for "
        "a rehearsal root outside the repository",
    )
    identity = None
    if _is_real(root):
        _prove(
            rehearsal_identity_path().exists(),
            f"{rehearsal_identity_path()} is missing — D-21/D-27: run the 39-07 rehearsal first; "
            "the real run launches only after the rehearsal identity is recorded",
        )
        identity = _load(rehearsal_identity_path())
        _prove(
            isinstance(identity, dict)
            and set(identity) == _IDENTITY_KEYS
            and isinstance(identity["module_sha256"], dict)
            and set(identity["module_sha256"]) == set(DISCLOSED_MODULES),
            f"{rehearsal_identity_path()} is malformed: the disclosure would fail at emit, after "
            "the MPS hours (38-REVIEW DR-03)",
        )
    present = [path for path in outputs(root) if path.exists()]
    # 39-REVIEW-3 WR-01: sidecars with no run sidecar and no record are a crashed attempt's.
    _prove(
        not present or run_sidecar(root).exists() or (root / prereg.CTX_RECORD).exists(),
        "partial sidecars from a crashed attempt, with no run sidecar: "
        f"{[path.name for path in present]} in {root / 'data'}. They are root-cause evidence: "
        "keep them; they are never reused "
        "(nothing resumes from them). 39-08 crash rule (ii): reconcile the ledger, move them out "
        "of data/ into a kept evidence directory, write the root-cause note; a new attempt needs "
        "Rafael's approved",
    )
    for path in present:
        _prove(False, f"{path} exists: the E6 scoring has already run")
    _prove(
        RUN_ID not in phase36_ledger.open_runs(phase36_ledger.read_ledger(ledger_path)),
        f"the ledger holds an open attempt for {RUN_ID}: end it, or reconcile it once the run is "
        "dead, before a new attempt",
    )
    refuse_if_dirty(
        who="phase39_ctx",
        detail=(
            "the E6 record publishes git_sha and hashes its modules from the working tree; a run "
            "launched from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=LAUNCH_PATHSPEC,
        cwd=_REPO,
    )
    launch_sha = git_sha()
    _prove(launch_sha != "unknown", "git_sha() could not read HEAD (run from the repo root)")
    for rel in tracked_inputs():
        tracked = subprocess.run(
            ("git", "ls-files", "--error-unmatch", rel), cwd=_REPO, capture_output=True, text=True
        )
        _prove(tracked.returncode == 0, f"{rel} is not tracked: it must be committed before E6")
    launch_modules = module_sha256()
    disclosure = None
    if identity is not None:
        _prove(
            identity["module_sha256"][PREREG_FILE] == launch_modules[PREREG_FILE],
            "D-27: scripts/phase39_prereg.py changed after the rehearsal; only Rafael's ruling "
            "(with disclosure in the record) can lift this",
        )
        # 38-REVIEW DR-03: computed once here, so a foreign identity refuses before the hours.
        disclosure = rehearsal_disclosure(
            identity, launch_git_sha=launch_sha, launch_module_sha256=launch_modules
        )
    # D-03: the committed stop, no second rule.
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    committed = phase36_caps.committed_budget()["unit_caps"][FRONT]
    for name, cap in (
        ("adapters", prereg.COMMITTED_ADAPTER_CAP),
        ("anchor_adapters", prereg.COMMITTED_ANCHOR_ADAPTER_CAP),
    ):
        _prove(
            cap == committed[name],
            f"the budget's committed E6 {name} cap is {committed[name]}, not {cap}: the D-11 "
            "deviation must stay visible",
        )
    # D-11: never adapters= / anchor_adapters= — the approved 8 lives in the prereg.
    phase36_caps.check_unit_caps(
        FRONT,
        entries=len(prereg.E6_ENTRY_SUBSET),
        a2_regenerated_entries=prereg.A2_REGENERATED_ENTRIES,
        anchor_slots=len(prereg.SLOTS),
        max_k=prereg.K,
    )
    for path in run_inputs():
        _prove(
            pathlib.Path(path).exists(),
            f"{path} is missing: the run reads it, so this refuses before the ledger start line",
        )
    reconstruction = phase38_rank.reconstruction_checks()  # D-20
    prereg.verify_a2_records()  # D-02
    g2 = prereg.gate2()  # D-19
    unequal = [
        (reading, slot, row)
        for reading, by_slot in g2["rows"].items()
        for slot, row in by_slot.items()
        if not row["equal"]
    ]
    _prove(
        g2["passed"] and not unequal,
        "gate 2 (D-19): "
        + (
            "{}/{} re-derived {}, committed {}".format(
                unequal[0][0], unequal[0][1], unequal[0][2]["count"], unequal[0][2]["committed"]
            )
            if unequal
            else "not passed"
        )
        + "; nothing is regenerated — pause for Rafael",
    )
    print(
        f"PREFLIGHT OK {launch_sha} device={resolved} readings={len(readings)} slots={len(slots)} "
        f"entries={len(prereg.E6_ENTRY_SUBSET)} projection_h={prereg.E6_PROJECTION_HOURS} "
        f"stop_h={prereg.E6_STOP_HOURS} spent_E6_s={gate['spent_seconds'][FRONT]}",
        flush=True,
    )
    return {
        "git_sha": launch_sha,
        "module_sha256": launch_modules,
        "device": resolved,
        "gate": gate,
        "reconstruction": reconstruction,
        "readings": readings,
        "slots": slots,
        "gate2": g2,
        "rehearsal_disclosure": disclosure,
    }


def run(
    *,
    root=None,
    ledger_path=None,
    heartbeat_path=None,
    device=None,
    readings=None,
    slots=None,
    rehearsal_identity=None,
):
    """THE run: preflight, ledger start, the D-18 / D-30 gate pass over every reading, then (gate
    passed) one work pass per reading into a write-once sidecar, the run sidecar, ledger end. No
    in-run stop timer: the committed stop is require_launch's (D-03)."""
    import phase18_extraction
    import torch

    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else _ROOT
    if _is_real(root):
        _prove(
            readings is None and slots is None and rehearsal_identity is None,
            "the real root runs the full READINGS x SLOTS shape only and records no rehearsal; a "
            "partial shape is a rehearsal into a tmp root outside the repository (D-21)",
        )
    else:
        milestone = {
            (phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH).resolve(),
            pathlib.Path(phase36_ledger.HEARTBEAT_PATH).resolve(),
        }
        _prove(
            ledger_path is not None
            and heartbeat_path is not None
            and {
                pathlib.Path(ledger_path).resolve(),
                pathlib.Path(heartbeat_path).resolve(),
            }.isdisjoint(milestone),
            "a rehearsal root writes its own ledger and heartbeat, never the milestone ones: pass "
            "tmp ledger_path and heartbeat_path (38-REVIEW DR-01)",
        )
    pre = preflight(
        root=root, ledger_path=ledger_path, device=device, readings=readings, slots=slots
    )
    readings, slots, device = pre["readings"], pre["slots"], pre["device"]
    taught = _taught()
    entries = [(i, entry) for i, entry in prereg.e6_entries() if entry["slot"] in slots]
    if rehearsal_identity is not None:  # DR-02 refuses BEFORE the ledger start line
        _kept_identity(rehearsal_identity, readings=readings, slots=slots)
    phase36_ledger.append("start", run_id=RUN_ID, phase=39, front=FRONT, ledger_path=ledger_path)
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    state = {"point": RUN_ID, "stage": "gate", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)  # the thread's first beat waits a full period
    if rehearsal_identity is not None:  # D-21 / D-27: before the first value is scored
        record_rehearsal(rehearsal_identity, readings=readings, slots=slots)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    started = _now()
    try:
        # D-18 + D-30 condition 1: every committed cell through BOTH functions, every committed
        # rank reproduced, BEFORE anything new is scored.
        cells, rows = {}, {}
        for reading in readings:
            state.update(stage=f"gate_{reading}")
            with reading_model(reading, device) as (model, tok, forbid):
                cells[reading] = {
                    slot: gate_cells(model, tok, device, slot, state) for slot in slots
                }
                del model, tok, forbid  # 38-REVIEW DI-04: released before the next load
            rows[reading] = phase38_rank.gate_reading(
                reading,
                {
                    slot: {c: cell["pinned"]["nll_mean"] for c, cell in by_c.items()}
                    for slot, by_c in cells[reading].items()
                },
            )
        unequal = [
            [reading, slot, candidate]
            for reading, by_slot in cells.items()
            for slot, by_c in by_slot.items()
            for candidate, cell in by_c.items()
            if not cell["equal"]
        ]
        compared = sum(len(by_c) for by_slot in cells.values() for by_c in by_slot.values())
        copy_equality = {
            "cells_compared": compared,
            "cells_equal": compared - len(unequal),
            "unequal": unequal,
        }
        passed = not unequal and all(
            row["equal"] for by_slot in rows.values() for row in by_slot.values()
        )
        _write_once(
            gate_sidecar(root),
            {
                "run_id": RUN_ID,
                "readings": list(readings),
                "slots": list(slots),
                "rows": rows,
                "cells": cells,
                "copy_equality": copy_equality,
                "passed": passed,
            },
        )
        scored = []
        if passed:
            for reading in readings:
                state.update(stage=f"work_{reading}")
                with reading_model(reading, device) as (model, tok, forbid):
                    anchor = {
                        slot: anchor_draws(model, tok, device, forbid, slot, reading)
                        for slot in slots
                    }
                    questions = {}
                    for i, entry in entries:
                        slot = entry["slot"]
                        kw = {"taught": taught[slot], "state": state}
                        questions[str(i)] = {
                            "index": i,
                            **{
                                key: entry[key]
                                for key in (
                                    "slot",
                                    "fact_id",
                                    "tier",
                                    "seed_index",
                                    "realized_injection",
                                )
                            },
                            "references": score_question(
                                model,
                                tok,
                                device,
                                entry,
                                phase18_extraction.reference_set_for(slot),
                                **kw,
                            ),
                            # D-26: the taught NLL is shared with R_q, never re-scored here.
                            "minted": score_question(
                                model, tok, device, entry, prereg.minted_members(slot), **kw
                            ),
                        }
                    del model, tok, forbid  # 38-REVIEW DI-04
                # Write-once BEFORE the next reading: a crash keeps every reading already scored
                # as evidence (nothing resumes from it; 39-REVIEW-3 WR-01).
                _write_once(
                    reading_sidecar(root, reading),
                    {
                        "run_id": RUN_ID,
                        "reading": reading,
                        "anchor": anchor,
                        "questions": questions,
                    },
                )
                scored.append(reading)
        status = "SCORED" if passed else "GATE_FAILED"
        end_sha = git_sha()
        if end_sha != pre["git_sha"]:
            print(f"WARN HEAD moved during the run: {pre['git_sha']} -> {end_sha}", flush=True)
        _write_once(
            run_sidecar(root),
            {
                "run_id": RUN_ID,
                "status": status,
                "readings": list(readings),
                "slots": list(slots),
                "entries": [i for i, _ in entries],
                "git_sha_at_launch": pre["git_sha"],
                "git_sha_at_end": end_sha,
                "head_moved_during_run": end_sha != pre["git_sha"],
                "device": device,
                "torch_version": torch.__version__,
                "started_utc": started,
                "finished_utc": _now(),
                "module_sha256_at_launch": pre["module_sha256"],
                "reconstruction": pre["reconstruction"],
                "gate2": pre["gate2"],
                "gate_sha256": _sha256(gate_sidecar(root)),
                "reading_sha256": {r: _sha256(reading_sidecar(root, r)) for r in scored},
            },
        )
        state.update(stage="done")
    finally:
        stop.set()
        thread.join()
    phase36_ledger.append(
        "end",
        run_id=RUN_ID,
        phase=39,
        front=FRONT,
        record=prereg.CTX_RECORD,
        ledger_path=ledger_path,
    )
    print(f"RUN {status} — next: crosscheck, then emit", flush=True)
    return status


def rank_rows(rows, taught):
    """D-30 condition 2: the taught value's rank among ``rows`` by ``nll_mean`` alone
    (rank_in_prefix: ascending NLL, ties by the candidate string); never a per-token value."""
    nll = {candidate: row["nll_mean"] for candidate, row in rows.items()}
    return phase38_prereg.rank_in_prefix(nll, taught, [c for c in rows if c != taught])


def _suffix_check(model, tok, device, entry, refs, taught):
    """D-30a: the copy's taught suffix sum is bitwise the pinned span_nll_from_ids in A2's exact
    context (the committed prompt_ids, then the taught ids after realized_injection)."""
    import phase18_extraction

    pinned = phase18_extraction.span_nll_from_ids(
        model,
        list(entry["prompt_ids"]),
        list(tok.encode(taught))[entry["realized_injection"] :],
        device,
    )
    return _same_bits(refs[taught]["suffix_nll_sum"], pinned["nll_sum"])


def crosscheck(*, root=None, device="cpu"):
    """D-20 / D-30a: re-score on CPU every gate cell, every R_q question and every (ii) question
    through the same functions, and compare each taught suffix sum bitwise with the pinned call.
    Descriptive only, write-once, no ledger line; no generation cross-check (seeded per device)."""
    import phase18_extraction
    import torch

    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else _ROOT
    sidecar = run_sidecar(root)
    _prove(sidecar.exists(), f"{sidecar} is missing: there is no E6 run to cross-check")
    run = _load(sidecar)
    _prove(run["status"] == "SCORED", f"the run is {run['status']}, not SCORED: nothing to check")
    out = cpu_sidecar(root)
    _prove(not out.exists(), f"{out} exists: the CPU cross-check is write-once")
    taught = _taught()
    wanted = set(run["entries"])
    entries = [(i, entry) for i, entry in prereg.e6_entries() if i in wanted]
    _prove(len(entries) == len(wanted), f"the run's entries {sorted(wanted)} are not E6 entries")
    state = {"point": RUN_ID, "stage": "crosscheck", "shape": None, "draw_index": None}
    started, gate, rq, minted, unequal = _now(), {}, {}, {}, []
    for reading in run["readings"]:
        with reading_model(reading, device) as (model, tok, forbid):
            gate[reading] = {
                slot: rank_rows(
                    {
                        c: cell["pinned"]
                        for c, cell in gate_cells(model, tok, device, slot, state).items()
                    },
                    taught[slot],
                )
                for slot in run["slots"]
            }
            rq[reading], minted[reading] = {}, {}
            for i, entry in entries:
                slot = entry["slot"]
                kw = {"taught": taught[slot], "state": state}
                refs = score_question(
                    model, tok, device, entry, phase18_extraction.reference_set_for(slot), **kw
                )
                extra = score_question(model, tok, device, entry, prereg.minted_members(slot), **kw)
                rq[reading][str(i)] = rank_rows(refs, taught[slot])
                minted[reading][str(i)] = rank_rows(
                    {taught[slot]: refs[taught[slot]], **extra}, taught[slot]
                )
                if not _suffix_check(model, tok, device, entry, refs, taught[slot]):
                    unequal.append([reading, i])
            del model, tok, forbid  # 38-REVIEW DI-04
    compared = len(run["readings"]) * len(entries)
    _write_once(
        out,
        {
            "device": device,
            "torch_version": torch.__version__,
            "started_utc": started,
            "finished_utc": _now(),
            "gate": gate,
            "rq": rq,
            "minted": minted,
            "suffix_equality": {
                "compared": compared,
                "equal": compared - len(unequal),
                "unequal": unequal,
            },
        },
    )
    print(f"CROSSCHECK DONE {out}", flush=True)
    return out


# D-17 / D-29: the caveats every predicted hit rate carries (descriptive, never a criterion).
_D17_CAVEAT = (
    "D-17: descriptive, never a criterion; temperature, top-p and the hit rule separate the "
    "predicted hit rate from the observed one"
)
_D29_CONDITIONING = (
    "D-29 / D-23c: the (b) prediction uses the taught suffix sum after the injected prefix, so it "
    "is conditioned on that prefix exactly as G_q's hit is scored on prefix_text + completion"
)


def _a2_draws(reading):
    """The committed A2 draw rows of ``reading`` (preflight's verify_a2_records proved the bytes);
    loaded once per reading and shared by its slots (I2)."""
    rows = _json(_prereg().A2_RECORDS[reading]["path"])["draws"]
    return [row for row in rows if row["family"] == "A2"]


def _a2_question_hits(draws, fact_id, taught):
    """{"tier/seed_index": hits} of ``fact_id``'s committed A2 questions through score_records
    (A2 on prefix_text + completion). No file I/O."""
    import phase18_extraction

    K = _prereg().K
    rows = [row for row in draws if row["fact_id"] == fact_id]
    out = {}
    for row in phase18_extraction.score_records(rows, {fact_id: taught}):
        key = f"{row['tier']}/{row['seed_index']}"
        _prove(len(row["hits"]) == K, f"A2 {fact_id} {key}: {len(row['hits'])} draws, not K = {K}")
        _prove(key not in out, f"A2 {fact_id}: two rows for {key}")
        out[key] = sum(row["hits"])
    return out


def _rank_block(questions, taught):
    """R_q (D-10 / D-24) and the (ii) ranks (D-11 ii) over one slot's questions in entry order;
    nll_mean only (D-30 condition 2)."""
    prereg = _prereg()
    ranks = [rank_rows(q["references"], taught) for q in questions]
    minted = [
        rank_rows({taught: q["references"][taught], **q["minted"]}, taught) for q in questions
    ]
    candidates = list(questions[0]["references"])
    nll = {c: [q["references"][c]["nll_mean"] for q in questions] for c in candidates}
    return {
        "indices": [q["index"] for q in questions],
        "ranks": ranks,
        "n1": prereg.n1(ranks),
        "median": prereg.median_rank(ranks),
        "rank_of_mean_nll": prereg.rank_of_mean_nll(
            nll, taught, [c for c in candidates if c != taught]
        ),
        "minted": {"ranks": minted, "n1": prereg.n1(minted), "median": prereg.median_rank(minted)},
    }


def _generation_block(anchor_record, a2_hits, taught, fact_id, g2_count):
    """G_a from the anchor record (D-06 / D-08: re-derivable from the record) and G_q from the
    committed A2 draws, its count proved equal to gate 2's (D-07 rates, descriptive)."""
    import phase18_extraction

    prereg = _prereg()
    hits = phase18_extraction.score_records([anchor_record], {fact_id: taught})[0]["hits"]
    answered = sum(v > 0 for v in a2_hits.values())
    _prove(
        g2_count == answered,
        f"{fact_id}: gate 2 counts {g2_count} answered, the A2 draws {answered} (D-19)",
    )
    total = sum(a2_hits.values())
    return {
        "G_a": {
            "hits": hits,
            "unit": prereg.unit_of(hits),
            "h": sum(hits),
            "rate": prereg.draw_rate(sum(hits), prereg.K),
        },
        "G_q": {
            "count": g2_count,
            "per_question": dict(a2_hits),
            "total": total,
            "rate": prereg.draw_rate(total, len(a2_hits) * prereg.K),
        },
    }


def _descriptive_block(gate_cells_slot, questions, a2_hits, taught, h):
    """D-17 / D-23a / D-23c / D-29: the predicted vs observed hit rates and the per-token values of
    every candidate in both contexts. Descriptive: calls no rank, status or class function."""
    prereg = _prereg()
    K = prereg.K
    b = [
        {
            "index": q["index"],
            "predicted": prereg.predicted_hit_rate(q["references"][taught]["suffix_nll_sum"]),
            "observed": a2_hits[f"{q['tier']}/{q['seed_index']}"] / K,
        }
        for q in questions
    ]
    return {
        "predicted": {
            "a": prereg.predicted_hit_rate(gate_cells_slot[taught]["pinned"]["nll_sum"]),
            "a_observed": h / K,
            "b_per_question": b,
            "b_mean_predicted": math.fsum(x["predicted"] for x in b) / len(b),
            "b_observed": sum(a2_hits.values()) / (len(a2_hits) * K),
            "caveat": _D17_CAVEAT,
            "conditioning": _D29_CONDITIONING,
        },
        "per_token": {
            "anchor": {c: cell["copy"]["per_token"] for c, cell in gate_cells_slot.items()},
            "question": {
                str(q["index"]): {
                    c: row["per_token"] for c, row in {**q["references"], **q["minted"]}.items()
                }
                for q in questions
            },
        },
    }


def _reading_blocks(root, run, gate):
    """{reading: {slot: block}} from the reading sidecars, the committed A2 draws (one load per
    reading) and gate 2's counts. The sidecar digests are build_record's to verify."""
    prereg = _prereg()
    taught = _taught()
    blocks = {}
    for reading in run["readings"]:
        blob = _load(reading_sidecar(root, reading))
        draws = _a2_draws(reading)
        blocks[reading] = {}
        for slot in run["slots"]:
            questions = sorted(
                (q for q in blob["questions"].values() if q["slot"] == slot),
                key=lambda q: q["index"],
            )
            anchor = blob["anchor"][slot]
            hits = _a2_question_hits(draws, anchor["fact_id"], taught[slot])
            g2 = run["gate2"]["rows"][reading][slot]
            _prove(
                len(questions) == len(hits) == g2["n_questions"] == prereg.N_QUESTIONS
                and {f"{q['tier']}/{q['seed_index']}" for q in questions} == set(hits),
                f"{reading}/{slot}: the scored questions are not the committed A2 questions",
            )
            generation = _generation_block(
                anchor, hits, taught[slot], anchor["fact_id"], g2["count"]
            )
            blocks[reading][slot] = {
                "taught": taught[slot],
                "fact_id": anchor["fact_id"],
                "R_a": gate["rows"][reading][slot]["rank"],
                "rank": _rank_block(questions, taught[slot]),
                "generation": generation,
                "descriptive": _descriptive_block(
                    gate["cells"][reading][slot],
                    questions,
                    hits,
                    taught[slot],
                    generation["G_a"]["h"],
                ),
                "anchor_record": anchor,
            }
    return blocks


def _cell_values(blocks):
    """{reading: {slot: {R_a, R_q, G_a, G_q}}}: the rank, n1, the unit and the answered count."""
    return {
        reading: {
            slot: {
                "R_a": block["R_a"],
                "R_q": block["rank"]["n1"],
                "G_a": block["generation"]["G_a"]["unit"],
                "G_q": block["generation"]["G_q"]["count"],
            }
            for slot, block in by_slot.items()
        }
        for reading, by_slot in blocks.items()
    }


def _minted_ii(blocks):
    """D-11 (ii) / D-26: the minted ranks under the question beside the committed anchor-side rank
    at |R| = MINTED_SET_SIZE (results/phase38_rank.json). Descriptive."""
    prereg = _prereg()
    size = prereg.MINTED_SET_SIZE
    committed = _json(phase38_prereg.RANK_RECORD)["readings"]
    return {
        reading: {
            slot: {
                **block["rank"]["minted"],
                "size": size,
                "anchor_side_rank": committed[reading][slot]["curve"][str(size)]["rank"],
            }
            for slot, block in by_slot.items()
        }
        for reading, by_slot in blocks.items()
    }


def _classified(values, event):
    """Ruling f / WR-02: the door's cells of ``event`` (CELL_READINGS x SLOTS, filtered to the
    scored readings and slots), each classified against the k0 values of its slot."""
    prereg = _prereg()
    k0 = values[prereg.REFERENCE_READING]
    return [
        prereg.classify_cell(cell, values[cell["reading"]][cell["slot"]], k0[cell["slot"]])
        for cell in prereg.cells(event)
        if cell["reading"] in values and cell["slot"] in values[cell["reading"]]
    ]


def _decomposition(values, slots):
    """D-15 / D-16 / rulings f, g, j: the classification per event with class_counts, the D-33
    tie audit (tie_audit over the damage cells) and the k0 baseline table, each None with its
    reason when it cannot be computed (k0 not scored, no cell reading, a partial slot set)."""
    prereg = _prereg()
    out = dict.fromkeys(
        (
            "classification",
            "classification_reason",
            "drop_formula_audit",
            "drop_formula_audit_reason",
            "baseline",
            "baseline_reason",
        )
    )
    if prereg.REFERENCE_READING not in values:
        for key in ("classification", "drop_formula_audit", "baseline"):
            out[f"{key}_reason"] = "k0 not scored"
        return out
    if set(slots) == set(prereg.SLOTS):
        out["baseline"] = prereg.baseline_table(values[prereg.REFERENCE_READING])
    else:
        out["baseline_reason"] = "partial slots: baseline_table needs every slot"
    classified = {event: _classified(values, event) for event in prereg.EVENTS}
    if not classified[prereg.EVENTS[0]]:
        reason = f"no cell reading scored: the cells are {list(prereg.CELL_READINGS)}"
        out["classification_reason"] = out["drop_formula_audit_reason"] = reason
        return out
    out["classification"] = {
        event: {"cells": cells, "counts": prereg.class_counts(cells)}
        for event, cells in classified.items()
    }
    out["drop_formula_audit"] = prereg.tie_audit(classified["damage"])
    return out


def _hours(started, finished):
    delta = datetime.datetime.fromisoformat(finished) - datetime.datetime.fromisoformat(started)
    return delta.total_seconds() / 3600


def _cpu_block(cpu, blocks, gate_rows):
    """D-20: the CPU ranks against the record's (gate, R_q and (ii) per question), the differing
    cells named; descriptive, never a criterion."""
    gate_cells = [[r, s] for r, rows in gate_rows.items() for s in rows]
    gate_differing = [[r, s] for r, s in gate_cells if cpu["gate"][r][s] != gate_rows[r][s]["rank"]]
    cells, rq_differing, minted_differing = [], [], []
    for reading, by_slot in blocks.items():
        for slot, block in by_slot.items():
            rank = block["rank"]
            for i, rq, ii in zip(
                rank["indices"], rank["ranks"], rank["minted"]["ranks"], strict=True
            ):
                cells.append([reading, slot, i])
                if cpu["rq"][reading][str(i)] != rq:
                    rq_differing.append([reading, slot, i])
                if cpu["minted"][reading][str(i)] != ii:
                    minted_differing.append([reading, slot, i])
    return {
        "criterion": False,
        "device": cpu["device"],
        "torch_version": cpu["torch_version"],
        "gate_cells": len(gate_cells),
        "gate_differing": len(gate_differing),
        "gate_differing_cells": gate_differing,
        "rq_cells": len(cells),
        "rq_differing": len(rq_differing),
        "rq_differing_cells": rq_differing,
        "minted_cells": len(cells),
        "minted_differing": len(minted_differing),
        "minted_differing_cells": minted_differing,
        "suffix_equality": cpu["suffix_equality"],
        "generation": "no generation cross-check: generation is seeded per device (D-20)",
    }


def _cost(run):
    """The run's hours beside the projection, with the second adapter load per reading priced
    (I1): every number computed from the budget record, none typed."""
    prereg = _prereg()
    priced = len(run["readings"])
    setups_run = 2 * priced
    setup = _json(prereg.BUDGET_RECORD)["unit_prices"]["adapter_setup_high"]
    extra = (setups_run - priced) * setup / 3600
    projected = prereg.E6_PROJECTION_HOURS + extra
    return {
        "run_hours": _hours(run["started_utc"], run["finished_utc"]),
        "e6_projection_hours": prereg.E6_PROJECTION_HOURS,
        "e6_stop_hours": prereg.E6_STOP_HOURS,
        "setups_priced": priced,
        "setups_run": setups_run,
        "extra_setup_hours": extra,
        "projection_with_double_load_hours": projected,
        "within_stop": projected <= prereg.E6_STOP_HOURS,
        "note": "run() loads each reading twice (gate pass, then work pass) where the formula "
        "prices one adapter setup each (I1)",
    }


def build_record(root):
    """The E6 record, only from the sidecars, the committed records and the frozen prereg."""
    prereg = _prereg()
    root = pathlib.Path(root)
    run = _load(run_sidecar(root))
    _prove(
        _sha256(gate_sidecar(root)) == run["gate_sha256"],
        f"{gate_sidecar(root)} is not the bytes the run wrote (run sidecar SHA-256)",
    )
    for reading, digest in run["reading_sha256"].items():
        path = reading_sidecar(root, reading)
        _prove(
            _sha256(path) == digest,
            f"{path} is not the bytes the run wrote (run sidecar SHA-256)",
        )
    _prove(
        json.loads(json.dumps(prereg.gate2()["rows"])) == run["gate2"]["rows"],
        "gate 2 (D-19): the committed A2 counts changed since launch; nothing is regenerated — "
        "pause for Rafael",
    )
    gate = _load(gate_sidecar(root))
    equality = gate["copy_equality"]
    if _is_real(root):
        identity = rehearsal_identity_path()
        _prove(identity.exists(), f"{identity} is missing: the D-21 / D-27 disclosure needs it")
        disclosure = rehearsal_disclosure(
            _load(identity),
            launch_git_sha=run["git_sha_at_launch"],
            launch_module_sha256=run["module_sha256_at_launch"],
        )
    else:
        disclosure = {
            "this_is_the_rehearsal": True,
            "slice": {"readings": run["readings"], "slots": run["slots"]},
        }
    record = {
        "front": FRONT,
        "run_id": RUN_ID,
        "status": run["status"],
        "approval": prereg.approval_block(),
        "shape": {key: run[key] for key in ("readings", "slots", "entries")},
        "reconstruction": run["reconstruction"],
        "gate": {key: gate[key] for key in ("rows", "copy_equality", "cells")},
        "gate2": run["gate2"],
        "rehearsal_disclosure": disclosure,
        "limitations": list(prereg.ENTRIES["limitations"]["value"]),
        "not_measured": list(prereg.NOT_MEASURED),
        "context_b_instrument": (
            "scored with the driver's copy of span_nll_from_ids (D-30); gate-1 equality: "
            f"{equality['cells_equal']} of {equality['cells_compared']}"
        ),
    }
    sidecars = {
        "run": _sha256(run_sidecar(root)),
        "gate": run["gate_sha256"],
        "readings": run["reading_sha256"],
    }
    if run["status"] == "SCORED":
        _prove(
            set(run["reading_sha256"]) == set(run["readings"]),
            "a SCORED run has one reading sidecar per reading",
        )
        cpu_path = cpu_sidecar(root)
        _prove(cpu_path.exists(), f"{cpu_path} is missing: run crosscheck before emit (D-20)")
        blocks = _reading_blocks(root, run, gate)
        sidecars["cpu"] = _sha256(cpu_path)
        record.update(
            readings=blocks,
            **_decomposition(_cell_values(blocks), run["slots"]),
            adapter_off="descriptive (D-11 i): never classified",
            minted_ii=_minted_ii(blocks),
            cpu_crosscheck=_cpu_block(_load(cpu_path), blocks, gate["rows"]),
            cost=_cost(run),
        )
    launch, now = run["module_sha256_at_launch"], module_sha256()
    record["provenance"] = {
        "run": {key: run[key] for key in RUN_PROVENANCE_KEYS},
        "module_sha256_at_launch": launch,
        "module_sha256": now,
        "modules_changed_since_launch": sorted(
            rel for rel in MODULES if launch.get(rel) != now[rel]
        ),
        "sidecar_sha256": sidecars,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
    return record


def emit(*, root=None, ledger_path=None):
    """Write results/phase39_ctx.json ONCE from the sidecars (SC4, D-03), after every refusal."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else _ROOT
    out = root / prereg.CTX_RECORD
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The E6 record is write-once; corrections are "
        "dated continuations",
    )
    # 39-REVIEW-3 WR-02: a record for an attempt the ledger still holds open would later be
    # closed as lost by a reconcile, so the append-only ledger would deny the record's run.
    _prove(
        RUN_ID not in phase36_ledger.open_runs(phase36_ledger.read_ledger(ledger_path)),
        f"the ledger attempt {RUN_ID} is still open: apply 39-08 crash rule (i) (append the end "
        "line) before emit; never reconcile a run whose run sidecar exists",
    )
    sidecar = run_sidecar(root)
    _prove(sidecar.exists(), f"{sidecar} is missing: there is no E6 run to emit")
    run = _load(sidecar)
    _prove(
        not _is_real(root)
        or (
            run["readings"] == list(prereg.READINGS)
            and run["slots"] == list(prereg.SLOTS)
            and run["entries"] == list(prereg.E6_ENTRY_SUBSET)
        ),
        "the real root emits the full READINGS x SLOTS shape over every E6 entry only",
    )
    pathspec = LAUNCH_PATHSPEC
    if out.resolve().is_relative_to(_REPO.resolve()):
        pathspec = (*LAUNCH_PATHSPEC, f":(exclude){prereg.CTX_RECORD}")
    refuse_if_dirty(
        who="phase39_ctx",
        detail=(
            "the E6 record publishes git_sha and hashes its modules from the working tree; a "
            "record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_REPO,
    )
    _prove(
        run["status"] != "SCORED" or cpu_sidecar(root).exists(),
        f"{cpu_sidecar(root)} is missing: run crosscheck before emit (D-20)",
    )
    record = build_record(root)
    phase25_run.atomic_write_json(out, record)
    print(f"EMITTED {record['status']} {out}", flush=True)
    return record


# The report (CTX-03): the record rendered, nothing else. No number is typed in the template text;
# every sentence about the data (limitations, not measured, caveats) comes from the record.
_KEYS = ("R_a", "R_q", "G_a", "G_q")


def _table(header, rows):
    """A GFM table; a pipe inside a cell (|R|) is escaped, else it would add cells."""

    def line(cells):
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"

    return [line(header), "|" + "---|" * len(header), *(line(row) for row in rows), ""]


def _slots(keys):
    """The record's slots in the locked SLOTS order (the JSON keys are sorted)."""
    return [slot for slot in _prereg().SLOTS if slot in keys]


def _readings(keys):
    """The record's readings in READINGS order (the JSON keys are sorted)."""
    return [reading for reading in _prereg().READINGS if reading in keys]


def _disclosure_lines(disclosure):
    if disclosure.get("this_is_the_rehearsal"):
        part = disclosure["slice"]
        return [
            "This record IS the CPU rehearsal (D-21, D-27): it read slots "
            f"{', '.join(part['slots'])} under the readings {', '.join(part['readings'])}, all "
            "their A2 entries, before the driver review and the MPS run. The real record lists "
            f"every later commit to {' or '.join(DISCLOSED_MODULES)} with its reason.",
            "",
        ]
    part = disclosure["slice_read"]
    modules = [rel for rel in DISCLOSED_MODULES if rel in disclosure["changed"]]
    lines = [
        disclosure["statement"],
        "",
        f"- slice read: slots {', '.join(part['slots'])}, readings {', '.join(part['readings'])}",
        f"- rehearsal git sha: `{disclosure['rehearsal_git_sha']}`",
        f"- launch git sha: `{disclosure['launch_git_sha']}`",
        f"- driver changed: {disclosure['driver_changed']}; prereg changed: "
        f"{disclosure['prereg_changed']}",
        "",
        *_table(
            ("module", "rehearsal sha256", "launch sha256", "changed"),
            [
                [
                    rel,
                    f"`{disclosure['rehearsal_module_sha256'][rel]}`",
                    f"`{disclosure['launch_module_sha256'][rel]}`",
                    disclosure["changed"][rel],
                ]
                for rel in modules
            ],
        ),
    ]
    if not disclosure["commits"]:
        return [
            *lines,
            f"No commit touched {' or '.join(modules)} between the rehearsal and the launch.",
            "",
        ]
    return [
        *lines,
        *(
            f"- `{c['sha']}` {c['reason']} (touched: {', '.join(c['modules'])})"
            for c in disclosure["commits"]
        ),
        "",
    ]


def _scored_sections(record):
    """The sections only a SCORED record has, from the four readings to the CPU cross-check."""
    prereg = _prereg()
    readings = record["readings"]
    pairs = [(r, s) for r in _readings(readings) for s in _slots(readings[r])]
    out = [
        "## The four readings per slot and adapter (D-13)",
        "",
        "R_a: the taught value's rank in the anchor context (a). R_q: n1, the questions whose "
        "taught value ranks 1 in the question context (b), with the median rank and the rank of "
        "the mean NLL. G_a: the common unit (some hit in K anchor draws) and its hits. G_q: the "
        "committed A2 answered count and its hits. Adapter-off is descriptive (D-11 i).",
        "",
        *_table(
            (
                "reading",
                "slot",
                "R_a rank",
                "R_q n1",
                "R_q median",
                "R_q rank of mean NLL",
                "G_a unit",
                "G_a hits/K",
                "G_q answered",
                "G_q hits/(n K)",
            ),
            [
                [
                    f"{r} (descriptive)" if r in prereg.DESCRIPTIVE_READINGS else r,
                    s,
                    b["R_a"],
                    f"{b['rank']['n1']}/{len(b['rank']['ranks'])}",
                    b["rank"]["median"],
                    b["rank"]["rank_of_mean_nll"],
                    b["generation"]["G_a"]["unit"],
                    f"{b['generation']['G_a']['h']}/{len(b['generation']['G_a']['hits'])}",
                    f"{b['generation']['G_q']['count']}/"
                    f"{len(b['generation']['G_q']['per_question'])}",
                    f"{b['generation']['G_q']['total']}/{b['generation']['G_q']['rate']['n']}",
                ]
                for r, s in pairs
                for b in [readings[r][s]]
            ],
        ),
        "## Baseline at k0 (ruling f)",
        "",
    ]
    if record["baseline"] is None:
        out += [f"No baseline table: {record['baseline_reason']}.", ""]
    else:
        out += [
            f"k0 ({prereg.REFERENCE_READING}) is the reference in both events and a cell in "
            "neither: each reading's k0 value with its status under each event against itself.",
            "",
            *_table(
                ("slot", "reading", "k0 value", "collapse", "damage"),
                [
                    [s, key, row["value"], row["collapse"], row["damage"]]
                    for s in _slots(record["baseline"])
                    for key in _KEYS
                    if key in record["baseline"][s]
                    for row in [record["baseline"][s][key]]
                ],
            ),
        ]
    classification = record["classification"]
    groups = ("prefixes", prereg.RETRAIN_READING, "combined")
    for event in prereg.EVENTS:
        out += [f"## Decomposition under {event} (D-15, D-16)", ""]
        if classification is None:
            out += [f"Not classified: {record['classification_reason']}.", ""]
            continue
        out += [
            "Each cell: the status of each reading (its value), the k0 values of the same slot "
            "(the reference, ruling f), the class of the four-step precedence and whether the "
            "published disagreement (R_a INTACT, G_q LOST) holds. k0 is never a cell; adapter-off "
            "is never classified (D-11 i).",
            "",
            *_table(
                (
                    "reading",
                    "slot",
                    *_KEYS,
                    *(f"k0 {key}" for key in _KEYS),
                    "class",
                    "disagreement",
                ),
                [
                    [
                        c["reading"],
                        c["slot"],
                        *(f"{c['statuses'][key]} ({c['values'][key]})" for key in _KEYS),
                        *(c["k0"][key] for key in _KEYS),
                        c["class"],
                        c["disagreement"],
                    ]
                    for c in classification[event]["cells"]
                ],
            ),
        ]
    out += ["## Instrument share and context share (CTX-03)", ""]
    if classification is None:
        out += [f"Not classified: {record['classification_reason']}.", ""]
    else:
        counts = {event: classification[event]["counts"] for event in prereg.EVENTS}
        out += [
            f"Per event, the prefix readings ({', '.join(prereg.CELL_PREFIX_READINGS)}) apart "
            f"from {prereg.RETRAIN_READING}, then combined. {counts['collapse']['m2_label']}. "
            "Each outcome is counted of the cells and, for the outcomes reached through a "
            "published disagreement, of the disagreement cells with its share; a share is never "
            "given without its denominator.",
            "",
        ]
        for event in prereg.EVENTS:
            for group in groups:
                tally = counts[event][group]
                d = tally["disagreement_cells"]
                parts = [
                    f"{label} ({name}) {tally['disagreement_by_class'][name]} of {d} disagreement "
                    f"cells (share {'—' if share is None else repr(share)})"
                    for name, label in (
                        ("INSTRUMENT_SUFFICIENT", "instrument share"),
                        ("CONTEXT_SUFFICIENT", "context share"),
                    )
                    for share in [tally["shares"][name]]
                ]
                out.append(f"- {event}, {group}: {'; '.join(parts)}; {tally['cells']} cells.")
        out += [
            "",
            *_table(
                (
                    "event",
                    "group",
                    "outcome",
                    "of cells",
                    "of disagreement cells",
                    "share of disagreement cells",
                ),
                [
                    [
                        event,
                        group,
                        name,
                        f"{tally['by_class'][name]} of {tally['cells']}",
                        f"{tally['disagreement_by_class'][name]} of {tally['disagreement_cells']}"
                        if name in tally["disagreement_by_class"]
                        else "—",
                        "—" if tally["shares"].get(name) is None else repr(tally["shares"][name]),
                    ]
                    for event in prereg.EVENTS
                    for group in groups
                    for tally in [counts[event][group]]
                    for name in prereg.OUTCOMES
                ],
            ),
        ]
    out += ["## Reverse disagreement and undecided cells (ruling e, IN-01)", ""]
    if classification is None:
        out += [f"Not classified: {record['classification_reason']}.", ""]
    else:
        out += [
            f"{prereg.REVERSE_DISAGREEMENT} (R_a LOST with G_q INTACT) is counted apart, with no "
            "sufficiency class (ruling e); an undecided cell (a WR-01 outcome at step 1, "
            "disagreement None) is published apart (IN-01).",
            "",
            *_table(
                ("event", "group", "reverse disagreement", "undecided", "undecided by outcome"),
                [
                    [
                        event,
                        group,
                        f"{tally['reverse_disagreement_cells']} of {tally['cells']}",
                        f"{tally['undecided_cells']} of {tally['cells']}",
                        ", ".join(f"{k} {v}" for k, v in tally["undecided_by_class"].items()),
                    ]
                    for event in prereg.EVENTS
                    for group in groups
                    for tally in [classification[event]["counts"][group]]
                ],
            ),
        ]
        for event in prereg.EVENTS:
            apart = [
                c
                for c in classification[event]["cells"]
                if c["class"] == prereg.REVERSE_DISAGREEMENT or c["disagreement"] is None
            ]
            out += [f"- {event} `{c['reading']}` `{c['slot']}`: {c['class']}" for c in apart] or [
                f"No reverse disagreement and no undecided cell under {event}."
            ]
        out.append("")
    audit = record["drop_formula_audit"]
    out += ["## Drop-formula audit (D-33, descriptive)", ""]
    if audit is None:
        out += [f"No audit: {record['drop_formula_audit_reason']}.", ""]
    else:
        by_cell = {(c["reading"], c["slot"]): c for c in audit["cells"]}

        def named(triples, name):
            return [
                f"- `{r}` `{s}` {key}: {name}; class {by_cell[r, s]['class_committed']} by the "
                f"committed formula, {by_cell[r, s]['class_exact']} by the exact formula"
                for r, s, key in triples
            ]

        differing = [
            [
                c["reading"],
                c["slot"],
                key,
                f"{a['count_k0']} -> {a['count_k']} of {a['n']}",
                repr(a["rate_drop"]),
                repr(a["count_drop"]),
                a["status_committed"],
                a["status_exact"],
                c["class_committed"],
                c["class_exact"],
            ]
            for c in audit["cells"]
            for key in _KEYS[1:]
            for a in [c["audits"][key]]
            if a["differs"]
        ]
        out += [
            f"Criterion: {audit['criterion']} (descriptive only). Damage only: under collapse "
            f"there is no margin. The committed drop is {audit['formula']}; each count where "
            f"{audit['exact_formula']} differs from it, with its status under each against the "
            f"margin {audit['margin']!r} and the cell's class by both formulas. The main numbers "
            "use the committed formula (ruling j).",
            "",
            *(
                _table(
                    (
                        "reading",
                        "slot",
                        "count",
                        "k0 -> k of n",
                        "rate_drop",
                        "count_drop",
                        "status (committed)",
                        "status (exact)",
                        "class (committed)",
                        "class (exact)",
                    ),
                    differing,
                )
                if differing
                else ["No count differs between the two formulas.", ""]
            ),
            *(
                named(audit["flips"], audit["flip_name"])
                or ["No count status changes between the two formulas."]
            ),
            *(named(audit["exact_ties"], audit["exact_tie_name"]) or ["No exact margin tie."]),
            *(
                [
                    f"- class changes between the formulas: `{r}` `{s}`"
                    for r, s in audit["class_changes"]
                ]
                or ["No cell's class changes between the two formulas."]
            ),
            "",
        ]
    first = readings[pairs[0][0]][pairs[0][1]]
    n_questions = len(first["generation"]["G_q"]["per_question"])
    rate_cols = ("rate", "wilson_lower_95", "wilson_upper_95")
    out += [
        "## Common unit and per-draw rates (D-07, descriptive)",
        "",
        "The common unit (some hit in K draws) beside the draw-unit rates. The anchor gives one "
        f"unit per slot and A2 one per question ({n_questions} per slot): the 1-vs-{n_questions} "
        f"unit asymmetry (D-07). Unit: {first['generation']['G_a']['rate']['unit']}; "
        f"{first['generation']['G_a']['rate']['note']}.",
        "",
        *_table(
            (
                "reading",
                "slot",
                "G_a unit",
                "G_a hits/n",
                *(f"G_a {c}" for c in rate_cols),
                "G_q answered",
                "G_q hits/n",
                *(f"G_q {c}" for c in rate_cols),
            ),
            [
                [
                    r,
                    s,
                    ga["unit"],
                    f"{ga['rate']['successes']}/{ga['rate']['n']}",
                    *(repr(ga["rate"][c]) for c in rate_cols),
                    f"{gq['count']}/{len(gq['per_question'])}",
                    f"{gq['rate']['successes']}/{gq['rate']['n']}",
                    *(repr(gq["rate"][c]) for c in rate_cols),
                ]
                for r, s in pairs
                for ga, gq in [(readings[r][s]["generation"][k] for k in ("G_a", "G_q"))]
            ],
        ),
        "## Predicted vs observed hit rate (D-17, D-23c, D-29, descriptive)",
        "",
        f"{first['descriptive']['predicted']['caveat']}.",
        "",
        f"{first['descriptive']['predicted']['conditioning']}.",
        "",
        *_table(
            (
                "reading",
                "slot",
                "predicted (a)",
                "observed (a)",
                "mean predicted (b)",
                "observed (b)",
            ),
            [
                [
                    r,
                    s,
                    *(repr(p[k]) for k in ("a", "a_observed", "b_mean_predicted", "b_observed")),
                ]
                for r, s in pairs
                for p in [readings[r][s]["descriptive"]["predicted"]]
            ],
        ),
        "## Adapter-off (D-11 i, descriptive)",
        "",
        f"{record['adapter_off']}.",
        "",
    ]
    off = [(r, s) for r, s in pairs if r in prereg.DESCRIPTIVE_READINGS]
    out += (
        _table(
            ("slot", "reading", "R_a rank", "R_q n1", "G_a unit", "G_q answered"),
            [
                [
                    s,
                    r,
                    b["R_a"],
                    f"{b['rank']['n1']}/{len(b['rank']['ranks'])}",
                    b["generation"]["G_a"]["unit"],
                    f"{b['generation']['G_q']['count']}/"
                    f"{len(b['generation']['G_q']['per_question'])}",
                ]
                for r, s in off
                for b in [readings[r][s]]
            ],
        )
        if off
        else [f"{', '.join(prereg.DESCRIPTIVE_READINGS)} is not among this run's readings.", ""]
    )
    minted = record["minted_ii"]
    cpu = record["cpu_crosscheck"]
    suffix = cpu["suffix_equality"]
    out += [
        "## Minted sets under the full question at |R| = 8 (D-11 ii, D-26, descriptive)",
        "",
        "The taught value's rank among itself and the Phase 38 minted values under the full "
        "question (context b), beside the committed anchor-side rank at the same size "
        f"({phase38_prereg.RANK_RECORD}).",
        "",
        *_table(
            ("reading", "slot", "|R|", "n1", "median", "committed anchor-side rank"),
            [
                [
                    r,
                    s,
                    m["size"],
                    f"{m['n1']}/{len(m['ranks'])}",
                    m["median"],
                    m["anchor_side_rank"],
                ]
                for r in _readings(minted)
                for s in _slots(minted[r])
                for m in [minted[r][s]]
            ],
        ),
        "## CPU cross-check (D-20, descriptive)",
        "",
        f"Criterion: {cpu['criterion']} (descriptive only). On {cpu['device']} (torch "
        f"{cpu['torch_version']}) the rank differs from the run's in {cpu['gate_differing']} of "
        f"{cpu['gate_cells']} gate cells, in {cpu['rq_differing']} of {cpu['rq_cells']} R_q "
        f"questions and in {cpu['minted_differing']} of {cpu['minted_cells']} (ii) questions; the "
        f"taught suffix sum is bitwise the pinned call's in {suffix['equal']} of "
        f"{suffix['compared']} (D-30a). {cpu['generation']}.",
        "",
        *(
            f"- differing {kind} cell: {cell}"
            for kind in ("gate", "rq", "minted")
            for cell in cpu[f"{kind}_differing_cells"]
        ),
        *(f"- unequal suffix: {cell}" for cell in suffix["unequal"]),
        "",
    ]
    return out


def render_report(record):
    """The markdown report, from the record alone (CTX-03)."""
    run, approval = record["provenance"]["run"], record["approval"]
    gate, gate2 = record["gate"], record["gate2"]
    equality = gate["copy_equality"]
    out = [
        "# Phase 39 — E6 instrument × context 2×2",
        "",
        "## Status",
        "",
        f"Status: **{record['status']}** — run `{record['run_id']}`, front {record['front']}, "
        f"device `{run['device']}`, launched at `{run['git_sha_at_launch']}`.",
        "",
    ]
    if record["status"] == "GATE_FAILED":
        out += [
            "Gate 1 did not reproduce every committed rank, or the copy was not bitwise equal to "
            "the pinned function in every cell, so nothing new was scored: this record carries the "
            "gate rows and no readings.",
            "",
        ]
    out += [
        "## Approval and cost (D-11, D-26, D-30)",
        "",
        f'D-11 ruling (verbatim): "{approval["ruling"]}"',
        "",
        f'D-26 ruling (verbatim): "{approval["d26_ruling"]}" ({approval["source"]}).',
        "",
        *(
            f"- {key}: {approval[key]!r}"
            for key in (
                "approved_adapters",
                "committed_adapter_cap",
                "committed_anchor_adapter_cap",
                "reference_reading",
                "cell_readings",
                "descriptive_readings",
                "minted_set_size",
                "minted_extra_nlls",
                "gate_extra_nlls_priced",
                "gate_extra_nlls_actual",
            )
        ),
        *(f"- projection step {k}: {v!r}" for k, v in approval["projection_steps"].items()),
        *(
            f"- {key}: {approval[key]!r}"
            for key in (
                "e6_projection_hours",
                "committed_front_hours_e6",
                "e6_stop_hours",
                "budget_record",
            )
        ),
        *(f"- cost {key}: {value!r}" for key, value in record.get("cost", {}).items()),
        "",
        "## Gate 1: committed anchor ranks and the copy's equality (D-18, D-30)",
        "",
        "The rank on each committed reference set against the committed rank, before anything "
        "new was scored; every cell scored by the pinned value_span_nll and by the driver's copy.",
        "",
        *_table(
            ("reading", "slot", "|R|", "rank", "committed rank", "equal", "taught NLL", "abs diff"),
            [
                [
                    r,
                    s,
                    row["n_references"],
                    row["rank"],
                    row["committed_rank"],
                    row["equal"],
                    repr(row["taught_nll"]),
                    repr(row["abs_nll_diff"]),
                ]
                for r in _readings(gate["rows"])
                for s in _slots(gate["rows"][r])
                for row in [gate["rows"][r][s]]
            ],
        ),
        f"Copy equality (D-30 condition 1, nll_sum and nll_mean bitwise): cells compared "
        f"{equality['cells_compared']}, cells equal {equality['cells_equal']}.",
        "",
        f"Context (b) was scored with the copy: {record['context_b_instrument']}.",
        "",
        *(
            f"- rank not reproduced: `{r}` `{s}`"
            for r in _readings(gate["rows"])
            for s in _slots(gate["rows"][r])
            if not gate["rows"][r][s]["equal"]
        ),
        *(f"- unequal cell: `{r}` `{s}` `{c}`" for r, s, c in equality["unequal"]),
        "",
        "## Gate 2: committed A2 counts re-derived (D-19)",
        "",
        f"Passed: {gate2['passed']}. Each committed A2 answered count re-derived from the "
        "SHA-verified draws; `independent` marks the erasure target's k0 row checked against a "
        "committed total (WR-01).",
        "",
        *_table(
            ("reading", "slot", "count", "committed", "n questions", "equal", "independent"),
            [
                [
                    r,
                    s,
                    row["count"],
                    row["committed"],
                    row["n_questions"],
                    row["equal"],
                    row.get("independent", "—"),
                ]
                for r in _readings(gate2["rows"])
                for s in _slots(gate2["rows"][r])
                for row in [gate2["rows"][r][s]]
            ],
        ),
        *(
            f"- `{r}` `{s}` source: {row['source']}"
            for r in _readings(gate2["rows"])
            for s in _slots(gate2["rows"][r])
            for row in [gate2["rows"][r][s]]
            if "source" in row
        ),
        "",
    ]
    if record["status"] == "SCORED":
        out += _scored_sections(record)
    provenance = record["provenance"]
    out += [
        "## Rehearsal disclosure (D-21, D-27)",
        "",
        *_disclosure_lines(record["rehearsal_disclosure"]),
        "## Not measured (D-12, D-23d)",
        "",
        *(f"- {item}" for item in record["not_measured"]),
        "",
        "## Limitations (D-22)",
        "",
        *(f"- {item}" for item in record["limitations"]),
        "",
        "## Provenance",
        "",
        *(f"- {key}: `{value}`" for key, value in run.items()),
        f"- modules changed since launch: {provenance['modules_changed_since_launch']}",
        *(f"- sidecar {key}: `{value}`" for key, value in provenance["sidecar_sha256"].items()),
        f"- head at write: `{provenance['head_at_write']}`; written {provenance['written_utc']}",
        "",
    ]
    return "\n".join(out)


def _tracked_and_clean(rel):
    """True iff ``rel`` is tracked and unmodified against HEAD (cwd _REPO)."""
    return all(
        subprocess.run(("git", *args), cwd=_REPO, capture_output=True).returncode == 0
        for args in (("ls-files", "--error-unmatch", rel), ("diff", "--quiet", "HEAD", "--", rel))
    )


def report(*, root=None):
    """Write results/phase39_ctx_report.md ONCE from the record (on the real root only from a
    tracked, unmodified record)."""
    prereg = _prereg()
    root = pathlib.Path(root) if root is not None else _ROOT
    record_path = root / prereg.CTX_RECORD
    _prove(record_path.exists(), f"{record_path} is missing: emit the record first")
    _prove(
        not _is_real(root) or _tracked_and_clean(prereg.CTX_RECORD),
        f"{prereg.CTX_RECORD} must be committed and unmodified before the report renders it",
    )
    out = root / prereg.REPORT_RECORD
    _prove(
        not out.exists(),
        f"{out} exists — REFUSING to overwrite it. The report is write-once; corrections are "
        "dated continuations",
    )
    out.write_text(render_report(_load(record_path)), encoding="utf-8")
    print(f"REPORT {out}", flush=True)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {
        "preflight": preflight,
        "run": run,
        "crosscheck": crosscheck,
        "emit": emit,
        "report": report,
    }
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    # git_sha() reads the process cwd: every command runs at the repository root.
    os.chdir(_REPO)
    commands[argv[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
