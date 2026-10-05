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
