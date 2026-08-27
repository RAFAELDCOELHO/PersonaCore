---
slug: sigma-zero-beats-control
status: root-caused
trigger: "Phase 23 D-04 HALT: the σ=0 arm BEATS the unmitigated control by 0.2222222222222222 (4.15× the 0.05357142857142849 floor). Split the hypothesis between (A) INVALID COMPARATOR — the control was trained under a different data-exposure protocol than the DP arm, leading suspicion the OLD random-window loader vs the NEW fact-aligned path — and (B) REAL DP-PATH DEFECT. Task 1: independently re-derive the headline numbers from the raw artifacts. Task 2: recover and systematically check all four residual differences 23-08 enumerated in advance, not only the 8× token difference. Only then decide whether the fix is a pre-registered comparator (own phase) or a localized DP-mechanism correction; if it touches a frozen file, use the dated-continuation discipline, never an in-place edit of a closed pin."
created: 2026-08-27
updated: 2026-08-27
---

# sigma-zero-beats-control

## Symptoms

- **Expected:** σ=0 is DP-SGD with the noise term exactly zero, so its taught-recall reading
  should reproduce the unmitigated control's reading to within the seed-to-seed noise floor.
  `phase23_prereg.sigma_zero_verdict` would then return `"proceed"` and the noised sweep
  would be cleared to run.
- **Actual:** σ=0 read **790/1008 = 0.7837301587301587** taught recall (adapter ON) against a
  control central reading of **566/1008 = 0.5615079365079365** (the reading at the FIRST
  recorded seed, 1337 — pinned, not a mean). Deviation **0.2222222222222222** against a floor
  of **0.05357142857142849** — **4.15×**. Direction: **BEATS**. The σ=0 reading sits 215 draws
  above the control's *maximum* seed. Control per-seed: 566, 530, 575, 531, 521 / 1008
  (112 questions × 9 draws), seeds 1337, 2024, 1338, 2025, 1339.
  Every secondary reading moves the same way: held-out ON 346/648 vs 238/648;
  PPL ON +2.95% vs +36.2%.
- **Error:** `SystemExit` raised by `scripts/phase23_prereg.py:271` —
  `"[phase23_prereg] D-04 HALT — THE SWEEP IS HALTED: zero noised points will run."` followed
  by the reading/central/deviation/floor block and: *"σ=0 must reproduce the unmitigated
  control inside the seed-to-seed floor. It does not. The cause must be ROOT-CAUSED AND FIXED
  before any noised point runs — this is not a warning and there is no override flag. Every
  correctness bug in this class IMPROVES utility, which is why a σ=0 that BEATS the control is
  the signal rather than noise. Stop-and-fix is reversible; publish-compromised is not."*
- **Timeline:** first occurrence, and necessarily so — the σ=0 point is the DP arm's **first
  executed run** (DPSGD-06). It has never worked because it has never run before. Phase 23
  plan 23-10, 2026-08-27, commits `0e503ed` (run) and `2d06989` (record).
- **Reproduction:** deterministic from committed artifacts — no re-run needed.
  `results/phase23_sigma_zero.json` (the σ=0 readings and the verdict),
  `results/phase23_control_floor.json` (the 5 control readings, the floor, and the four
  residual differences), the run CSVs under `results/phase23_control_seed*/` and
  `results/phase23_sigma0_dp_n8/`, and the per-seed adapter sha256s.

## Current Focus

- **status:** TASKS 1, 2 AND 3 COMPLETE. Root cause attributed to branch **(A) INVALID
  COMPARATOR**; branch **(B) EXCLUDED** by direct falsification. No fix applied — the fix is a
  pre-registered comparator and merits its own phase.
- **hypothesis (CONFIRMED):** The control and the σ=0 arm were trained under materially different
  data-exposure AND step-size protocols. `is_dp = arm in DP_ARMS` simultaneously switches the
  packer (random mixed-bin sample → deterministic full-coverage fact-aligned), the lot size
  (8 windows → 65) and the gradient clip (`clip_grad_norm_` at 1.0 → none). All three push the
  same direction and all three are measured. The σ=0 reading is a reading of a DIFFERENT
  TRAINING PROTOCOL, not of the same protocol with the noise term zeroed.
- **falsification test that would have overturned this:** if the DP seam at σ=0 with non-binding
  C had produced a gradient differing from the ordinary grad-accum reference, branch (B) would be
  live. It does not: 72/72 tensors agree to 2.178e-07 relative.
- **next_action:** Await user decision. Recommended: schedule a NEW PHASE for a pre-registered
  protocol-matched comparator (equalising lot volume, teaching loss weight and `grad_clip`),
  re-reduce the floor on that comparator's seeds, then re-run the D-04 verdict. 23-11/12/13/14
  stay BLOCKED. **The halt stands and is better understood — that is the intended outcome.**

## Evidence

- **The verdict was produced by a rule pinned BLIND.** `scripts/phase23_prereg.py` is
  byte-identical to its birth commit `c7de5d4` (verified with `git diff --stat c7de5d4 HEAD`,
  empty), which was written in wave 1 while `git ls-files 'results/phase23_*'` returned
  nothing. `sigma_zero_verdict` is keyword-only —
  `(*, control_readings, sigma_zero_reading, floor, floor_provenance)` — with no override
  parameter; its only outcomes are the string `"proceed"` and `SystemExit`. So the halt cannot
  be an artefact of a rule adjusted after the number existed.
- **Clipping is already excluded as the confound.** `clip_bind_count == 0` over all 200 steps
  at `C = 1e6` (`_NON_BINDING_CLIP`), with `clip_checked_before_scoring: true` recorded as a
  field of `results/phase23_sigma_zero.json` — the refusal was proven before the reading
  existed. One attempt; no second C was tried.
- **Both arms ran the same number of optimizer steps.** `composed_steps = 200`, counted off
  real `DPSGD.finalize` invocations via `_count_composed_steps`, not off a `step` field.
- **THE FOUR RESIDUAL DIFFERENCES, enumerated IN ADVANCE by 23-08 and recorded at
  `results/phase23_control_floor.json` → `residual_differences`. All four are UNCHECKED as of
  session open — checking each is TASK 2.** Verbatim:
  1. *"replay lives IN the teaching bin here; it is drawn at TRAIN time on the DP path."*
     Matched quantity: the replay TOKEN volume, which IS matched and recorded in
     `recipe.replay`. Not eliminable because D-10/D-24 put replay outside the teaching bin for
     DP arms, and `train()`'s replay seam (`replay_bin`/`replay_mask_bin`/`replay_windows`) is
     wired at `teach_persona.py`'s `dp_kwargs`, gated on `is_dp`.
  2. *"grad_accum_steps is 1 here and `n_facts` on the DP path."* Matched quantity: **none**.
     `dp_accum = dict(grad_accum_steps=stats['n_facts']) if is_dp else {}`. The control's lot
     is one micro-batch; the DP arm's lot is one privacy record per micro-step (SC2).
     **This is the difference that produces the 8× training-token gap** — 3,276,800 vs 409,600
     tokens over the same 200 optimizer steps.
  3. *"the flat v3.0 pack here; the ragged fact-aligned three-bin pack there."* Matched
     quantity: the fact set (`phase14_factset.LOCKED_FACTS`, n=8) and the taught family ids,
     which ARE identical. Not eliminable because the arm NAME couples an arm to its packer —
     `build_arm_bins` reads `DP_ARMS` and nothing else.
     **This is the user's leading suspicion for branch (A).**
  4. *"the DP arithmetic itself — per-record clip at C, a summed accumulator, and the division
     by N last."* Matched quantity: **none**. `DPSGD` is constructed only when `is_dp`. At σ=0
     the noise term is exactly zero but the CLIP and the accumulate-then-divide remain, so
     **σ=0 is not the control computation with a zero added to it.**
     **This is the core of branch (B), and note it is stated as a known fact, not a suspicion.**
- **23-10 did not attribute the halt.** Its SUMMARY states the 8× token difference "does not
  rule out a real DP-path defect" and that separating the hypotheses "needs a comparator,
  which this plan is not entitled to invent." No attribution has been made yet.

### TASK 1 — INDEPENDENT RE-DERIVATION (2026-08-27). EVERY FIGURE REPRODUCES.

Recomputed from raw counts, run CSVs and on-disk bytes — never from a SUMMARY or a summary field.

- **Per-seed primary, from `per_seed[].primary.k / .n`:** 566, 530, 575, 531, 521 over n=1008.
  `questions × draws_per_question = 112 × 9 = 1008` on every seed. Each `k/n` equals the recorded
  `rate` bit-for-bit. `readings[]` matches the per-seed re-derivation IN ORDER, and `seeds[]`
  matches `per_seed[].seed` in order (so `readings[0]` really is seed 1337).
- **Floor.** max = 0.5704365079365079 (seed 1338, k=575), min = 0.5168650793650794 (seed 1339,
  k=521). `noise_floor()` (called, not re-implemented) returns `0.05357142857142849`, identical to
  both `control_floor.json.floor` and `sigma_zero.json.floor`. Exact rational (575−521)/1008 =
  3/56; the recorded value is the fp `max − min`, which is what `sigma_zero_verdict`'s exact `==`
  requires.
- **σ=0 primary:** k=790, n=1008, 112×9=1008, `k/n = 0.7837301587301587` = recorded `rate` =
  top-level `reading`.
- **Deviation:** |790/1008 − 566/1008| = 224/1008 = **2/9 = 0.2222222222222222**, identical to
  the recorded value. dev/floor = 224/54 = **4.1481×**. Breach confirmed.
- **Adapter sha256 — all six re-hashed on disk, all six MATCH** the recorded digest AND byte
  count (5 control adapters at 1,351,913 B; `phase23_sigma0_dp_n8_adapter.pt` at 1,351,601 B,
  sha `0a897d23…6c64`, and `recipe.adapter_sha256` == `training.adapter_sha256`).
- **`record_sha256`** is an INPUTS digest, not a self-hash:
  `sha256(json.dumps(per_seed, sort_keys=True, default=str))` (`phase23_run.py:1291-1293`).
  Re-derived = `c62d7322…dfeb` = recorded, and `sigma_zero.json.floor_provenance.record_sha256`
  agrees. The separate `record_file_sha256` (`201cc58e…a75a59`) also matches the file on disk.
- **Run CSVs:** every `final_train_loss` equals the last CSV row's `train_loss` bit-for-bit; all
  six runs end at step 200 with 20 logged rows.
- **VERDICT: no figure fails to reproduce.** The halt stands on arithmetic that is exactly what
  the records claim. The investigation is about WHY the two readings differ, not whether they do.

### TASK 2 — THE FOUR RESIDUAL DIFFERENCES, MEASURED (2026-08-27)

Measured from the bins on disk (`data/persona_control_seed1337_train{,_mask}.bin`,
`data/persona_dp_n8_train{,_mask,_fact}.bin`) and from the code, not from the prose.

- **Bin geometry.** Control bin = 15,773 tokens = 8,192 replay (PREPENDED by `_prepend_replay`)
  + 7,581 teaching — matching `recipe.replay.teaching_tokens` exactly. DP bin = 8,449 tokens =
  33×256+1, pure teaching, windows/fact `[4,4,4,4,4,5,4,4]`.
- **Answer-token (mask=1) census.** Control: 3,543 replay + 2,719 teaching = 6,262 total. DP
  teaching bin: 2,719 — the SAME 2,719 teaching answer tokens. Per-fact: `[300,287,309,379,337,
  399,358,350]`.
- **#1 REPLAY — `matched: true` is a COMPOSITION match, not a VOLUME match, and the record does
  not say which.** `control_replay_ratio()` (`phase23_run.py:309-339`) solves for a ratio so the
  control bin CONTAINS `replay_window_budget(8) = 8192` replay tokens ONCE. On the DP path
  `replay_windows = replay_window_budget(8) // 256 = 32` windows drawn **per OPTIMIZER STEP**
  (`loop.py:306` states the unit explicitly). Run totals: control ≈ **212,733** replay tokens
  (200×8×256×8192/15773) vs DP **1,638,400** (200×32×256) — **7.70×**.
  **BUT the per-lot COMPOSITION IS matched, and that is what D-24's table actually sized:**
  control lot 48.06% teaching / 51.94% replay; DP lot 33 teaching + 32 replay windows =
  50.77% / **49.23%**, reproducing D-24's "4 windows → 49.23% share of the padded bin" row to four
  figures. So the replay design is CORRECT on the DP side; what is unmatched is the absolute lot
  volume — 65 windows vs 8, **8.125×**, the same ~8× as every other column. Retracted in place at
  `23-08-SUMMARY.md` and `23-10-SUMMARY.md` (2026-08-27).
- **#2 grad_accum — the 8× is real but is NOT the largest teaching-side gap.** 409,600 vs
  3,276,800 nominal tokens (`tokens_per_step = batch_size × max(1,grad_accum) × block_size`,
  `loop.py:799`) — but that column is a FORMULA, not a measurement of windows drawn. Measured
  TEACHING-token exposure is control ≈196,867 vs DP 1,689,600 = **8.58×**.
- **#3 PACK — CONFIRMED, and it is the largest single effect. This is branch (A).** The control
  draws **8 RANDOM windows/step from a MIXED bin** (`get_batch_memmap_masked`), so in expectation
  only **3.85 of 8** are teaching windows and the masked-CE mean puts weight
  **p = 2719/6262 = 0.4342** on teaching. The DP arm draws via `get_batch_fact_aligned`, which is
  **DETERMINISTIC** (`fact_index = step % n_facts`) and returns **EVERY window of one fact**: all
  33 teaching windows every step, each fact exactly once, with the loop's
  `sorted(seen) == list(range(n_facts))` refusal enforcing it. Then `finalize` divides the SUM by
  N, so the teaching term enters at weight **1.0** while replay enters at weight 1.0 in a separate
  pass — a SUM of two full means, not a mean of a mixture. **Teaching loss weight DP/control =
  1/0.4342 = 2.30×**, on top of full deterministic coverage vs a 3.85-window random sample
  (drastically lower gradient variance, which AdamW compounds).
- **#4 DP ARITHMETIC — checked, and it is NOT a scale defect.** On the DP path `loop.py:211`
  bypasses `/accum` so each backward is UNDIVIDED; `absorb_record` clips (coef exactly 1.0 here,
  `clip_bind_count == 0`) and SUMS; `finalize` divides by N last. Net scale = mean of per-record
  gradients = the same scale a `/accum` path would give. The accumulate-then-divide does not
  inflate the gradient.
- **#5 (NOT enumerated by 23-08, found here) — `grad_clip` IS APPLIED TO THE CONTROL AND NOT TO
  THE DP ARM.** `loop.py:220-228`: `clip_grad_norm_(model.parameters(), train_cfg.grad_clip)`
  runs iff `dp_fn is None`. `TrainConfig.grad_clip` defaults to **1.0** (`config.py:105`) and
  `teach_persona.train_arm` never overrides it. `DPSGD.finalize`'s own docstring names this as
  the open question: *"Whether it binds on the REAL corpus at 200 overfit steps is UNMEASURED."*
  If it binds, the control's step was shrunk on every step the DP arm's was not.
- **#6 — the two CSV `train_loss` columns are NOT the same quantity.** `_optimizer_step` sums
  only `base_loss` from the per-record loop (`loop.py:216`); `replay_fn`'s loss is never added.
  So the control's 0.638 is a MIXED teaching+replay masked CE and the DP arm's 0.060 is a PURE
  teaching CE. They must not be compared, and nothing in the records says so.

### THE TWO DECISIVE PROBES (2026-08-27) — diagnostics only, nothing written to `results/`

**PROBE 1 — does `grad_clip = 1.0` bind on the control?** `DPSGD.finalize`'s own docstring calls
this UNMEASURED. Replayed the first 25 optimizer steps of each arm from `convbase_best.pt` with
the real bins and seed 1337 on MPS, capturing `clip_grad_norm_`'s return value (the PRE-clip
global norm).

| arm | clip called? | steps where norm > 1.0 | mean shrink factor |
|---|---|---|---|
| control | **YES**, every step (`loop.py:221`) | **19 / 25** | **0.8071** |
| σ=0 DP | **NO** — unreachable under `dp_fn` (`loop.py:222-228`) | 25 / 25 *would* have | 0.5279 *would* |

Control pre-clip norms ranged 0.690–1.954; DP norms 1.538–2.278 and were **never clipped**. So the
control's update was shrunk on 76% of steps while the DP arm's — consistently ~1.9× larger to begin
with, because its gradient is a SUM of two full means rather than a mean of a mixture — was never
shrunk at all. **`inert by accident` is now measured FALSE on the real corpus.**

**PROBE 2 — FALSIFICATION TEST FOR BRANCH (B): is the DP seam at σ=0 with non-binding C
arithmetically inert?** Two legs over the SAME materialised 8 fact micro-batches and the SAME 4
replay micro-batches, from identical model state:
(A) the DP seam — undivided backward → `absorb_record` ×8 → replay pass → `finalize(8)`;
(B) the ordinary grad-accum reference — `loss/8` ×8 → the identical replay pass.

Result over all **72 trainable LoRA tensors**: `allclose(rtol=1e-5, atol=1e-7)` → **True**, worst
relative difference **2.178e-07** (abs 3.7e-09, at `blocks.2.mlp.fc_in.lora_B`) — float32
re-summation noise, nothing more.
**The DP mechanism at σ=0 with a non-binding C performs NO arithmetic the ordinary accumulation
does not.** Residual difference #4's premise — *"σ=0 is not the control computation with a zero
added to it"* — is TRUE as a statement about the CODE PATH and FALSE as a statement about the
ARITHMETIC. Branch (B) is excluded.

### PROVENANCE CLOSED

- `recipe.corpus_sha256` was recorded from `23-07-SUMMARY.md`, never measured at run time
  (`corpus_digest_source` says so). **All three re-hashed on disk: MATCH.**
- Both arms share `checkpoints/convbase_best.pt`, identical `lora_config`, identical
  `budget_constants`, identical `family_ids`, `n_facts = 8`, identical `ppl_adapter_off`
  (4.573349214207799) and identical `ppl_scored_targets` (270,203). The instrument is the same.
- **HELD-OUT (never-taught) facts are the tell.** Both arms score **0/648 with the adapter OFF**,
  so the base answers nothing. With it ON the σ=0 arm scores **346/648** against the control's
  **238/648** — on facts NEITHER arm was taught. A correctness bug that leaked taught facts could
  not raise a never-taught reading. This is ANSWER-FORMAT competence from better optimisation,
  which is exactly what branch (A) predicts and branch (B) does not.

## Eliminated

- **NOT a figure that fails to reproduce.** TASK 1 re-derived every headline number from raw
  counts, run CSVs and on-disk bytes. All reproduce bit-for-bit, including all six adapter
  sha256s and the `record_sha256` inputs digest.
- **NOT a DP-arithmetic defect (branch B, residual difference #4).** Disproved by direct
  falsification: at σ=0 with `C = 1e6` non-binding, the DP seam reproduces the ordinary
  grad-accum gradient over all 72 LoRA tensors to `allclose(rtol=1e-5, atol=1e-7)`, worst relative
  difference 2.178e-07. Per-record clip + summed accumulator + divide-by-N-last is a no-op at
  this operating point.
- **NOT a corpus or provenance error.** All three `dp_n8` bin digests re-hash to the recorded
  values; both arms share the base checkpoint, LoRA config, budget constants, fact set and
  scoring instrument (identical `ppl_adapter_off`, identical `ppl_scored_targets`).
- **NOT fact leakage into the σ=0 arm.** Both arms read 0/648 with the adapter OFF, and the σ=0
  arm beats the control on NEVER-TAUGHT held-out facts too (346/648 vs 238/648) — a leak cannot
  raise a never-taught reading.



- **Not clipping.** `clip_bind_count == 0` over all 200 steps, asserted before scoring.
- **Not a post-hoc rule adjustment.** The pre-registration is byte-identical to its blind
  birth commit; there is no override branch to have been taken.
- **Not a floor that failed to re-derive.** `sigma_zero_verdict` refuses unless
  `floor == noise_floor(control_readings)` under exact `==`, so a hand-edited or one-ULP-nudged
  floor could not have reached the verdict at all. (Independent re-derivation is still TASK 1 —
  this only establishes that the *verdict function* checked it.)
- **Not a step-count mismatch.** Both arms at `composed_steps = 200` off real `finalize` calls.

## Resolution

- **root_cause:** **THE COMPARATOR IS INVALID — branch (A), and branch (B) is EXCLUDED by
  measurement.** The σ=0 DP arm and the unmitigated control were trained under materially
  different data-exposure and step-size protocols, and every difference pushes the same way.
  Three measured mechanisms, all rooted in ONE predicate — `is_dp = arm in DP_ARMS`
  (`teach_persona.py:1389`) — which simultaneously switches the packer, the lot size and the
  gradient clip:

  1. **Deterministic full-coverage teaching vs a random 3.85-window sample** (residual difference
     #3, the user's leading suspicion — CONFIRMED and the largest effect). `get_batch_fact_aligned`
     picks `fact_index = step % n_facts` and returns EVERY window that fact owns, so the DP arm
     sees all 33 teaching windows every step, each fact exactly once (enforced by the loop's
     `sorted(seen) == list(range(n_facts))` refusal). The control draws 8 RANDOM windows from a
     bin that is 51.94% replay, so only ~3.85 are teaching. Teaching enters the DP gradient at
     weight **1.0** and the control's at **p = 2719/6262 = 0.4342** — a **2.30×** loss-weight gap,
     on top of a drastically lower gradient variance that AdamW compounds over 200 steps.
  2. **8.125× the lot volume** (residual difference #2). DP lot = 33 teaching + 32 replay = 65
     windows; control lot = 8 windows. Measured teaching-token exposure over the run: 1,689,600
     vs 196,867 = **8.58×**.
  3. **`grad_clip = 1.0` is applied to the control and structurally NOT to the DP arm**
     (NOT enumerated by 23-08 — found here). `loop.py:220-228` calls `clip_grad_norm_` iff
     `dp_fn is None`. MEASURED on the real corpus: it **binds on 19 of the control's first 25
     steps, mean shrink 0.807**, while the DP arm's norm (1.54–2.28, consistently ~1.9× the
     control's because its gradient is a SUM of two full means) is never clipped at all.
     `DPSGD.finalize`'s "inert by accident … UNMEASURED" is now measured FALSE.

  **Branch (B) does not hold.** At σ=0 with `C = 1e6` proven non-binding (`clip_bind_count == 0`),
  the DP seam is arithmetically inert: it reproduces the ordinary grad-accum gradient across all
  72 LoRA tensors to a worst relative difference of 2.178e-07. There is no DP-mechanism defect to
  fix. The halt is a TRUE and PUBLISHABLE finding about the comparator, not about DP-SGD.

  **Corroborating sign:** the σ=0 arm also beats the control on NEVER-TAUGHT held-out facts
  (346/648 vs 238/648, both 0/648 adapter-off). Better optimisation raises both; a taught-fact
  leak cannot raise a never-taught reading.

- **fix:** **NOT APPLIED — out of scope for this session by the user's own rule.** The fix is a
  PRE-REGISTERED COMPARATOR and therefore merits its own phase. Direction:
  * The comparator must equalise **lot volume, teaching loss weight and gradient clip** — not just
    token count. The single lever is `is_dp`; a valid control needs the fact-aligned packer, the
    train-time replay pass and `grad_accum_steps = n_facts` **without** a σ, i.e. a non-DP arm
    that reaches the `dp_kwargs` seam. Today `build_arm_bins` reads `DP_ARMS` and nothing else,
    so this needs a new arm-to-packer coupling, not a widened `DP_ARMS`.
  * `grad_clip` must be equal on both sides. Either the comparator also skips
    `clip_grad_norm_`, or it is set non-binding — but it CANNOT stay at 1.0 on one side only.
  * The floor must be re-reduced on the NEW comparator's seeds. The existing
    `CONTROL_NOISE_FLOOR` governs the old protocol and cannot be carried over.
  * `scripts/phase23_prereg.py` must NOT be edited — `sigma_zero_verdict` and `noise_floor` are
    correct and blind, and the new comparator is a new *input* to them, not a rule change. Verified
    byte-identical to `c7de5d4`; `git diff --exit-code` over all three frozen files exits 0.
  * 23-11 / 23-12 / 23-13 / 23-14 stay BLOCKED until that phase lands.

- **verification:** (a) every headline figure re-derived from raw artifacts — all reproduce;
  (b) branch (B) falsified by a two-leg gradient-identity probe over 72 tensors;
  (c) the grad-clip asymmetry measured over 25 real steps per arm;
  (d) all six adapter sha256s and all three corpus digests re-hashed on disk — all match;
  (e) frozen-file guard: `git diff --exit-code -- scripts/phase23_prereg.py
  scripts/mitigation_gate.py scripts/mitigation_accountant.py` exits 0.

- **files_changed:**
  - `.planning/phases/23-…/23-08-SUMMARY.md` — dated PARTIAL RETRACTION of the replay
    "same public token volume" claim (true per step, false as a run total by 7.70×; what is
    matched is the per-lot composition).
  - `.planning/phases/23-…/23-10-SUMMARY.md` — dated CORRECTION of residual difference #1's
    "*Matched:* the replay TOKEN volume".
  - `.planning/debug/sigma-zero-beats-control.md` — this file.
  - **No source file changed.** No `results/` artifact touched.
