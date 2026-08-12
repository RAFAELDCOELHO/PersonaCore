---
phase: 12-stage-2-conversational-fine-tune
reviewed: 2026-08-01T13:48:40Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - src/personacore/training/loop.py
  - src/personacore/evaluation/perplexity.py
  - src/personacore/evaluation/__init__.py
  - src/personacore/generation/core.py
  - scripts/build_retention_bin.py
  - scripts/finetune_smoke.py
  - scripts/finetune_smoke_stage3_override.py
  - scripts/finetune_dialog.py
  - scripts/make_transcripts.py
  - tests/test_masked_train_seam.py
  - tests/test_extra_eval_fns.py
  - tests/test_masked_perplexity.py
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-08-01T13:48:40Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Adversarial review of the Phase-12 masked-training seams, gate metric, stop machinery, and
the four driver scripts. The load-bearing correctness claims held under tracing:

- **Mask alignment is correct.** `masked_perplexity` slices the mask `mask[i+1:end]` — the
  identical bounds as the shifted target `data[i+1:end]` — and `get_batch_memmap_masked`
  shares the `i+1 : i+1+block_size` slice between `y` and `m`. The hand-counted K=7 oracle
  (`tests/test_masked_perplexity.py`) proves the denominator independently. No off-by-one.
- **`-100` sentinels are honored.** `gpt.py:212` uses `F.cross_entropy` with the default
  `ignore_index=-100`, so masked targets are excluded from both training CE and the in-loop
  masked val loss. Verified at the source, not assumed.
- **v1.0 default paths are pinned bit-identical** (omitted-vs-explicit-None identity tests in
  both seam test files + the golden-trajectory replay per 12-01-SUMMARY; the `estimate_loss`
  call site is byte-identical when `val_mask_bin` is None — commit `c2a1133`).
- **`stop_ids` replacement semantics** (`stops = stop_ids if stop_ids is not None else {eid}`)
  are exactly as documented and pinned by four tests including EOS-not-implicit.
- **weights_only contract followed:** `weights_only=False` only on the project's own full
  checkpoints (documented trusted-only), `weights_only=True` for fisher cache and the slim
  proof load. fp32/MPS posture respected (no AMP/GradScaler introduced; MPS-fallback env set
  before torch import in every driver).
- **Device handling:** the `make_transcripts.py` forbid-mask `.to(device)` fix is present
  (line 125); evaluation moves masks itself (`forbid_ids.to(logits.device)`).

What did not hold up: the seams and drivers have **silent-failure gaps** — a mask kwarg that
can be silently ignored, a production driver that silently clobbers committed evidence on
rerun, a skip-if-done resume that never validates arm config, and a copy-pasted persona-cap
whose drift would silently invalidate the transcript-evidence claim. Per scope instruction,
pre-registered gate thresholds were NOT flagged as magic numbers, and performance was out of
scope.

## Warnings

### WR-01: `val_mask_bin` is silently ignored on non-memmap val sources — asymmetric with the `train_mask_bin` guard

**File:** `src/personacore/training/loop.py:277-281` (guard), `src/personacore/training/loop.py:407-426` (silent fallback), `src/personacore/training/loop.py:93-111` (`estimate_loss` routing)
**Issue:** `train()` raises `ValueError` when `train_mask_bin` is set without `train_bin`, but
there is **no equivalent guard for `val_mask_bin`**:

1. `val_mask_bin` set with `val_bin=None` → `val_ids is None` → the eval block silently uses
   `val_loss = train_loss` (loop.py:425-426). The caller asked for masked val CE and gets
   unmasked train loss gating `best.pt` — no error, no warning.
2. `val_mask_bin` set with the `corpus_path` branch (in-RAM val array) → `estimate_loss`'s
   `is_bin` check is False, so `mask_bin` is never consulted (loop.py:102-111) — the mask is
   silently dropped and val CE is unmasked.

The docstring sells `val_mask_bin` as the USER LOCK 3 guarantee that "best is selected FOR
assistant-token dialogue capability"; both silent paths violate that guarantee without any
signal. The current drivers happen to always pass `val_bin`, so no shipped evidence is wrong —
this is a loaded trap for the Phase-13 λ=0 twin and any future caller.
**Fix:** Mirror the existing guard:
```python
if val_mask_bin is not None and (val_bin is None or not _is_bin_path(val_bin)):
    raise ValueError(
        "val_mask_bin requires val_bin (a memmap .bin PATH): the masked val seam "
        "only routes through get_batch_memmap_masked on the memmap data branch."
    )
```

### WR-02: `finetune_dialog.py` silently clobbers committed evidence on rerun; "kill-survivability" checkpointing is never consumed

**File:** `scripts/finetune_dialog.py:115-123` (`_preseed_csv` mode `"w"`), `scripts/finetune_dialog.py:215`, `scripts/finetune_dialog.py:229-254`
**Issue:** Two silent-failure modes in the production driver:

1. **No refuse-to-rerun guard.** `build_retention_bin.py` refuses to rebuild frozen outputs
   and `write_report` has `_never_clobber_guard`, but re-running `finetune_dialog.py`
   unconditionally truncates `results/finetune_prod.csv` (git-tracked TUNE-02 evidence) via
   `_preseed_csv(..., "w")` and overwrites the convbase checkpoint trio — no prompt, no
   SystemExit. If code/data drifted since the recorded run, the committed forgetting curve is
   silently replaced with numbers from a different substrate.
2. **`checkpoint_interval=250` is passed but `resume_from` never is.** The docstring and the
   constant comment claim "kill-survivability: latest.pt every K steps," yet a mid-run kill +
   rerun restarts from `best.pt` at step 0 (and wipes the partial CSV). Determinism makes the
   restart *correct*, but the 250-step checkpoint cadence buys nothing: 37 minutes of work is
   silently redone and the claimed resume property does not exist in this driver.

**Fix:** Add a run-once guard in `main()` before `_preseed_csv`:
```python
for out in (PROD_CSV, CONVBASE_LATEST, CONVBASE_BEST, CONVBASE_SLIM):
    if out.exists():
        raise SystemExit(
            f"[finetune_dialog] {out} already exists — the production run is recorded "
            "evidence. Delete the convbase trio + finetune_prod.csv to re-run."
        )
```
and either wire `resume_from=CONVBASE_LATEST if CONVBASE_LATEST.exists() else None` (with an
append-not-truncate preseed) or drop `checkpoint_interval` and the kill-survivability claim.

### WR-03: smoke skip-if-done validates only (arm name, final step) — config drift silently reuses stale results as current evidence

**File:** `scripts/finetune_smoke.py:355-388`
**Issue:** `_run_arm`'s skip path declares an arm complete when `rows[-1]["step"] == max_steps`
and `lblob["step"] == max_steps`. It never checks that the completed CSV/checkpoint was
produced with the **requested** `lr`, `lam`, `masked`, or `seed`. The two-pass flow explicitly
requires editing a constant (`SMOKE_STEPS`) and re-running; edits to `LR_MID`, `SEED`,
`NOISE_SEEDS`, or `BATCH_SIZE` between passes would make the driver silently reuse a
`ft_noise_a.csv` / `ft_cal.csv` trained under the *old* config while reporting it under the
new constants — corrupting every downstream gate number without any signal. The checkpoint
already carries `train_config` (saved by `save_checkpoint`), so the material for a loud check
is sitting in `lblob`.
**Fix:** In the skip branch, verify the reloaded config before accepting:
```python
tc = lblob["train_config"]
if (tc["lr"], tc["seed"], tc["batch_size"]) != (lr, seed, BATCH_SIZE):
    print(f"[finetune_smoke] arm '{name}': config mismatch vs checkpoint — restarting")
    csv_path.unlink()
else:
    ...  # existing skip path
```
(λ and masked are not in TrainConfig; they are encoded in the arm *name* for the λ/lr arms,
which covers them — the unprotected knobs are exactly the shared constants.)

### WR-04: `_cap_persona` + `PERSONA_CAP` copy-pasted into `make_transcripts.py` — drift silently invalidates the "tokenizes identically to the bins" evidence claim

**File:** `scripts/make_transcripts.py:58` (`PERSONA_CAP = 140`), `scripts/make_transcripts.py:61-74`; duplicate of `scripts/prepare_dialog_corpus.py:42,85-103`
**Issue:** The transcript generator's core evidence claim (docstring + committed
`results/transcripts.md` header) is that prompts "tokenize identically to the training bins"
(Pitfall 4). That claim rests on `_cap_persona` and `PERSONA_CAP` being byte-equivalent to
`prepare_dialog_corpus.py` — enforced today only by a "copied verbatim / MUST match" comment.
Any future change to the corpus-side cap (a Phase-13/14 re-prep, a cap bump) leaves the
transcript path silently stale: transcripts would still generate, still look plausible, and
no test or runtime check would catch that the prompts no longer match the bins.
**Fix:** Move `_cap_persona` and the cap constant into `src/personacore/dialogue` (next to
`encode_dialogue`, which both scripts already import) and import it from both drivers. One
shared function is a smaller diff than two guarded copies and deletes the drift class.

## Info

### IN-01: extras/eval RNG snapshot excludes device (CUDA/MPS) RNG

**File:** `src/personacore/training/loop.py:52-62`, `src/personacore/training/loop.py:432-438`
**Issue:** `_rng_state()` captures python/numpy/torch-**CPU** state only. An `extra_eval_fns`
entry (or masked val path) that sampled on the training device would advance the CUDA/MPS
generator outside the snapshot. All shipped fns (`masked_perplexity`, `retention_perplexity`,
`ewc_penalty`, role norms) are deterministic and batch draws use the numpy CPU RNG, so the
resume-equality contract holds today — but the docstring's general claim ("keeps a non-pure
fn from perturbing the train trajectory") is broader than the implementation.
**Fix:** Either note the CPU-only scope in the `extra_eval_fns` docstring, or extend the
snapshot with `torch.cuda.get_rng_state_all()` / `torch.mps.get_rng_state()` when available.

### IN-02: no guard against an all-masked effective batch → NaN mean CE

**File:** `src/personacore/training/data.py:125`, `src/personacore/training/loop.py:112`
**Issue:** If every target in a drawn masked batch were `-100`, `F.cross_entropy`'s mean over
zero scored elements is NaN — which would propagate silently into weights on the train path,
and on the val path silently freeze the `best.pt` gate (`NaN < best_val_loss` is False). At
batch 32 × block 256 over the real dialogue bins this is statistically negligible (all 32
windows simultaneously assistant-free), and the smoke `instability_check` would surface a NaN
in the CSV — but nothing guards the training step itself.
**Fix:** Cheap loud check in `get_batch_memmap_masked`:
`if (y == -100).all(): raise ValueError("drawn batch has zero scored targets")`.

### IN-03: non-atomic JSON writes for frozen/committed artifacts

**File:** `scripts/build_retention_bin.py:180-182`, `scripts/finetune_smoke.py:255-258`
**Issue:** `retention_anchors.json` and the wall-time cache are written with a direct
`open(..., "w")` / `write_text`. A mid-write kill leaves truncated JSON; for the anchors this
then trips refuse-to-rerun with a *corrupt* frozen artifact (recoverable — the error message
says delete both — but the failure reads as "frozen" rather than "broken").
**Fix:** Write to `path.with_suffix(".tmp")` then `os.replace` for the anchors JSON.

### IN-04: `estimate_loss` docstring claims "`iters` is clamped" — it is not

**File:** `src/personacore/training/loop.py:75-86`
**Issue:** The docstring (extended this phase with the `mask_bin` paragraph) says "``iters``
is clamped so a tiny fixture ... still produces a stable estimate." No clamping exists; the
window (`eff_block`) is shrunk instead, and `iters` always runs exactly as passed. The
documented behavior and the implementation disagree.
**Fix:** Reword to "the draw window is shrunk (`eff_block`) so a tiny fixture still yields
valid draws" — or actually clamp if that was the intent.

### IN-05: override wrapper duplicates ~60 lines of `fs.main()` context build

**File:** `scripts/finetune_smoke_stage3_override.py:111-155`
**Issue:** The ctx construction (blob load, theta_star, fisher, forbid, step-0 measurement,
role norms) is copied verbatim from `finetune_smoke.main()`. The docstring records this as a
deliberate D-07 choice ("the driver stays untouched by design"), which is a defensible
pre-registration posture — but the two copies can now drift (e.g., a fingerprint-key change in
one). Acceptable as a one-shot recorded override; do not extend the pattern. A future refactor
extracting `fs.build_ctx()` (an additive function, gates untouched) would preserve the
pre-registration discipline while deleting the duplication.
**Fix:** None required for the recorded artifact; extract `build_ctx()` if a third consumer
ever appears.

---

## Verified Clean (checked, not assumed)

| Concern (from review focus) | Result |
| --- | --- |
| Mask/target off-by-one in `masked_perplexity` + `get_batch_memmap_masked` | Correct — identical shifted slices; K=7 oracle independent of implementation |
| `ignore_index=-100` actually honored by the model loss | Confirmed at `gpt.py:212` (F.cross_entropy default) |
| v1.0 bit-identity of default paths (`train_mask_bin`/`val_mask_bin`/`extra_eval_fns` = None) | Pinned: identity tests + golden replay ran on this machine (12-01) |
| `stop_ids=None` ≡ v1.0 single-EOS; EOS not implicit in custom sets | Pinned by `tests/test_stop_ids.py` (4 tests) |
| `weights_only` contract | `False` only on own full checkpoints (documented); fisher via `load_fisher(weights_only=True)` + fingerprint; slim proof-loaded `weights_only=True` |
| Device handling in transcripts (forbid mask) | `.to(device)` present (`make_transcripts.py:125`); evaluation moves its own mask |
| fp32-on-MPS / no AMP / no network deps | No AMP/GradScaler introduced by phase code; CSV-only logging; `PYTORCH_ENABLE_MPS_FALLBACK` set pre-torch-import in all four drivers |
| CSV extras columns vs old files | Per-run fieldnames + DictWriter unknown-key raise; module constant never mutated (pinned) |
| `fieldnames` ternary precedence (loop.py:382) | `(A + B) if C else D` — parses as intended |
| GO-verdict gate regex | Correctly rejects `PENDING`/`NO-GO` (first-word match) |

---

_Reviewed: 2026-08-01T13:48:40Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
