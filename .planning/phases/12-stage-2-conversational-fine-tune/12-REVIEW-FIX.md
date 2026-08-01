---
phase: 12-stage-2-conversational-fine-tune
fixed_at: 2026-08-01T14:35:00Z
review_path: .planning/phases/12-stage-2-conversational-fine-tune/12-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 12: Code Review Fix Report

**Fixed at:** 2026-08-01T14:35:00Z
**Source review:** .planning/phases/12-stage-2-conversational-fine-tune/12-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (WR-01..WR-04; Info findings excluded per scope)
- Fixed: 4
- Skipped: 0

**Test suite (main checkout, post-merge, 3.11 venv):** `274 passed, 1 skipped` — exactly the
pre-fix baseline. The single skip is the pre-existing CUDA-only fp16 AMP smoke
(`tests/test_train_loop.py:81`). No existing test passed `val_mask_bin` with an in-RAM val
source, so WR-01's guard required no test reconciliation. No frozen `results/` artifacts,
checkpoints, or data bins were touched; no driver scripts were run.

## Fixed Issues

### WR-01: `val_mask_bin` silently ignored on non-memmap val sources

**Files modified:** `src/personacore/training/loop.py`
**Commit:** fd2fedb
**Applied fix:** Added a guard in `train()` mirroring the `train_mask_bin` guard. Per the
review's NOTE, the condition was verified against `estimate_loss` routing and **strengthened**
beyond the review's literal suggestion: the mask is only honored when `val_ids` is a `.bin`
path, and `val_ids` is only ever `val_bin` on the `train_bin` data branch — so the guard is
`val_mask_bin is not None and (train_bin is None or not _is_bin_path(val_bin))`. This catches
both review paths (val_bin=None → train-loss-as-val; in-RAM val → mask dropped) plus the
`corpus_path` + `val_bin` slip-through the review's literal condition would have missed
(`_is_bin_path(None)` is False, so `val_bin is None` is subsumed). Guard fires only on invalid
NEW usage; all default/driver paths unchanged (v1.0 identity tests still pass bit-for-bit).

### WR-02: `finetune_dialog.py` silently clobbers committed evidence on rerun

**Files modified:** `scripts/finetune_dialog.py`
**Commit:** 561b90c
**Applied fix:** Added the review's refuse-to-rerun `SystemExit` guard in `main()` immediately
after the GO-verdict check (fail-fast, before any model load and before `_preseed_csv`) over
`PROD_CSV`, `CONVBASE_LATEST`, `CONVBASE_BEST`, `CONVBASE_SLIM`. For the resume half, took the
review's simpler option (the recorded run is complete and the guard makes rerun impossible):
dropped `checkpoint_interval=CHECKPOINT_INTERVAL` from the `train()` call, deleted the
`CHECKPOINT_INTERVAL` constant, and replaced the kill-survivability comment with an honest one
explaining why periodic latest.pt saves bought nothing (`resume_from` never wired; a mid-run
kill is delete-and-restart, and determinism makes the restart exact). `convbase_latest.pt` is
still written end-of-call — the docstring's "full resumable state" claim remains true.

### WR-03: smoke skip-if-done never validates arm config against the checkpoint

**Files modified:** `scripts/finetune_smoke.py`
**Commit:** 67a3a5f
**Applied fix:** In `_run_arm`'s skip branch, after loading `lblob`, compare
`(tc["lr"], tc["seed"], tc["batch_size"])` from the checkpoint's `train_config` (a plain dict —
`save_checkpoint` stores `asdict(train_config)`, verified in `checkpoint.py:100`) against the
requested `(lr, seed, BATCH_SIZE)`. On mismatch it prints the old-vs-new values and falls
through to the existing stale-restart branch (`csv_path.unlink()` + fresh anchor run) — the
review's exact restart semantics without duplicating the unlink. λ/masked are covered by the
arm name keying the CSV/checkpoint filenames, as the review notes.

### WR-04: `_cap_persona` + `PERSONA_CAP` copy-pasted between two drivers

**Files modified:** `src/personacore/dialogue/serialize.py`,
`src/personacore/dialogue/__init__.py`, `scripts/make_transcripts.py`,
`scripts/prepare_dialog_corpus.py`
**Commit:** 3f45ff8
**Applied fix:** Moved the (logic-identical) function into
`personacore.dialogue.serialize` as public `cap_persona` with `PERSONA_CAP = 140`, next to
`encode_dialogue` (the review's requested location), exported both from
`personacore.dialogue.__init__`. Both scripts now import the shared function; both local
copies and both local constants deleted. `prepare_dialog_corpus.py` imports `PERSONA_CAP`
for its summary print; its now-unused `detokenize` import removed (ruff F401).
`ruff check` + `ruff format --check` clean on all touched files. The "tokenizes identically
to the bins" claim is now true by construction — the drift class is deleted.

---

_Fixed: 2026-08-01T14:35:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
