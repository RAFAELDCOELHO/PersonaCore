---
phase: 17-multi-persona-isolation-matrix
plan: 06
subsystem: isolation-swap-canary-and-run-modes
tags: [iso-02, iso-03, iso-04, iso-05, d-04, d-13, d-14, d-20, th-17-18, th-17-43, mutation-proved]
requires:
  - scripts/phase17_isolation.py (the 17-04 scoring core — extended ADDITIVELY, nothing edited)
  - src/personacore/lora (load_adapter_weights / adapter_disabled / LoRALinear — imported, and
    deliberately NOT modified: `git diff -- src/personacore/lora/` is empty)
  - scripts/phase14_recall.py (load_adapted_model, complete_question, question_seed, _sha256,
    assert_no_value_in_prompt, SEED, ADAPTER_PATH — imported, never copied)
  - scripts/phase16_persistence.py (SHARED_ARM_CONFIG, resolve_forbid, forbid_digest,
    arm_config_record, serializable_config, and assert_arms_are_pairable as the template)
  - scripts/teach_persona.py (train_arm/_require_go_verdict/arm_outputs — 17-02's widened form)
  - scripts/phase17_persona_facts.py (PERSONA_FACTS — reached through ONE lazy accessor)
provides:
  - lora_b_digest / load_adapter_with_canary / assert_sweeps_ran_on_distinct_weights (ISO-04)
  - BASE_COLUMN_NOTE + LORA_B_DIGEST_KEY / ADAPTER_FILE_DIGEST_KEY / ADAPTER_ENABLED_KEY
  - _minted_facts / slot_values / values_by_slot (the ONE reader of the material)
  - SWEEPS / sweep_record_path / resolve_seed / build_parser / main (the CLI, no mode runs two)
  - run_one_sweep / run_one_persona_training (the two run bodies)
  - tests/test_phase17_scoring.py — 18 tests (11 from 17-04, 1 widened, 6 new)
affects:
  - plan 17-08 (defines run_report_mode, which main() already dispatches to; it MUST call
    assert_sweeps_ran_on_distinct_weights before scoring — nothing else calls it in production)
  - plan 17-09 (runs `--train` x3 then `--sweep` x4, one fresh process each)
  - plan 17-10 / 17-11 (the ISO-05 replication reuses --train --seed / --sweep --seed unchanged)
tech-stack:
  added: []
  patterns:
    - two-layer guards where each layer's LIMIT is written down, not just its claim
    - two independent record fields rather than one field asked to prove two claims
    - a run contract kept OUT of the library choke point, with the measured reason recorded
    - the material reachable through exactly one named accessor
    - guards mutation-proved — watched failing before being trusted
key-files:
  created: []
  modified:
    - scripts/phase17_isolation.py (404 -> 1172 lines, purely additive)
    - tests/test_phase17_scoring.py (567 -> 928 lines, 1 test widened, 6 added, 0 deleted)
decisions:
  - no weight digest can witness "the adapter was off"; adapter_enabled carries ISO-03's claim
    and lora_b_sha256 is never asked to
  - the must-differ assertion is a Phase 17 RUN contract, not a library invariant — a
    same-adapter re-apply is a legitimate load_adapter_weights call, measured
  - the material has exactly ONE named reader, because the plan's own Task-2 criterion and
    Task-3 action contradicted each other and one accessor satisfies both
metrics:
  duration: 28min
  tasks: 4
  files: 2
  completed: 2026-08-14
---

# Phase 17 Plan 06: The ISO-04 Swap Canary and the Run Modes Summary

A silently no-opped adapter swap now aborts before a single completion is generated, a report
assembled from sweeps that ran on the same weights is structurally unreachable, and the adapter-off
column's control property is recorded by the one field that can actually carry it — all three
watched failing rather than argued.

## What Was Built

### Task 1 — the canary, in both layers (commit `18e76a8`)

| Name | What it proves | What it CANNOT prove |
|---|---|---|
| `lora_b_digest(model)` | which weights are RESIDENT — sha256 over the live `lora_B` tensors in sorted module-name order, off a detached CPU copy so it is device-stable | that the adapter was off; that a particular file was read |
| `load_adapter_with_canary` | in-process: at least one `lora_B` MOVED, and none is all-zero (the identity gate) | persona A's artifact from persona B's — in a fresh process ANY Phase 17 artifact differs from the Phase 14 adapter `load_adapted_model` just loaded |
| `assert_sweeps_ran_on_distinct_weights` | cross-process, and the unskippable half: eight named aborts before any scoring | nothing about a single record in isolation |

**The B3 correction is implemented as two fields, not one.** `adapter_disabled` flips
`LoRALinear.enabled` — a plain Python bool at `src/personacore/lora/layer.py:35`, deliberately kept
out of `state_dict()` (D-05) — and leaves `lora_B` exactly as loaded. So `lora_b_sha256` says WHICH
WEIGHTS were resident and `adapter_enabled` says WHETHER THE DELTA BRANCH could execute, and neither
is asked to prove the other's claim. `BASE_COLUMN_NOTE` records that the planning-time all-zero
expectation is false, so it is not re-derived from the same wrong premise.

**The eight cross-process aborts** (each with its own message, verified distinct): one `git_sha`;
four distinct pids; identical `(slot, seed_index, question)` sets; pairwise-distinct adapter LIVE
digests; pairwise-distinct adapter FILE digests; the base's `adapter_enabled` is `False`; every
adapter's is `True`; the base's live digest equals no adapter's.

**W5 declined with a measured reason, not overlooked.** Putting the must-differ assertion at
`load_adapter_weights` would be the smaller diff and would cover `personalize_demo.py` and every
future consumer. It is declined because that call legitimately supports re-applying an identical
adapter onto the model it came from — `tests/test_lora_artifact.py::test_real_slim_two_artifact_load_cpu`
nudges `lora_B`, exports that model's own adapter and loads it straight back onto the SAME model, so
no `lora_B` changes. `checkpoints/model_slim.pt` exists in this tree (55.6 MB), so its `skipif` does
not engage and it runs locally. A same-adapter re-apply is a valid library call; "the adapter must
differ from the previous one" is a Phase 17 RUN contract. `git diff -- src/personacore/lora/` is
empty.

### Task 2 — the material readers, the paths and the CLI (commit `e77de4b`)

`--train {persona_a,persona_b,persona_c} | --sweep {persona_a,persona_b,persona_c,base} | --report`
as one REQUIRED mutually exclusive group, plus a non-exclusive `--seed`. Measured: `--help` prints
the three modes and no fourth; `--sweep persona_a --report`, `--train persona_a --sweep persona_a`
and a bare invocation all exit 2.

`resolve_seed(mode, target, seed)` is the single implementation both the parser path and the tests
hit. `--sweep base --seed N` is REFUSED with **both** halves in one message: the base row has no
persona and therefore no `REPLICATION_SEEDS` entry, so any integer would be accepted (which is not
validation); and D-13 derives the base prior from ONE adapter-off column, so a per-seed base column
would be four controls where the design has one. A seed outside `REPLICATION_SEEDS[persona]` names
the pre-registration. An explicit default seed resolves to the SAME canonical arm, adapter and
record as no `--seed` at all, so the default run has exactly one set of paths.

Resolved through the real modules, no training:

| invocation | arm | adapter | record |
|---|---|---|---|
| `--sweep persona_a` | `persona_a` | `checkpoints/phase17_persona_a_adapter.pt` | `results/phase17_sweep_persona_a.json` |
| `--sweep persona_a --seed 1437` | `persona_a_seed1437` | `checkpoints/phase17_persona_a_seed1437_adapter.pt` | `results/phase17_sweep_persona_a_seed1437.json` |
| `--sweep base` | — | — | `results/phase17_sweep_base.json` |

`checkpoints/phase17_persona_a_adapter.pt` is exactly the path 17-09 Task 1's `test -f` asserts.

### Task 3 — `run_one_sweep` and `run_one_persona_training` (commit `e97c7d4`)

Ordered deliberately: clobber-refusal FIRST (before anything expensive), then preflight/device/
`seed_everything(recall.SEED)`, then the load and its two digests plus one flag, then ONE
`forbid_ids` mask proved against `resolve_forbid`'s seam, then generation, then the write.

The base sweep loads the SAME way the adapter sweeps do — Phase 14's `persona_adapter.pt`, which
`load_adapted_model` reads by default — and generates inside `adapter_disabled(model)`, never a
second un-adapted model. Immediately inside the context it `_prove`s that no `LoRALinear` is still
enabled, with the message stating that this runtime check is the ONLY witness of inertness.

The record carries `slot`, `seed_index`, `question`, `fact_id`, `prompt_ids`, `completions`,
`stopped` — and **no `value`, `k`, `n` or `hits`**. Those are per-persona and belong to the scoring
pass; writing them here would put the cell into the generation record, which is the one thing the
two-pass design exists to prevent.

`run_one_persona_training` gates on `_require_go_verdict(PHASE17_REPORT)` so BOTH gates fire
(Phase 14's inside `train_arm`, Phase 17's here) and passes `prefix="phase17"` **and** `seed=` at
the `train_arm` call. `arm_outputs` is not called here to "choose" a path — `train_arm` owns its own
write targets, and the path printed before training is resolved through `resolve_seed`, which reads
that same function.

### Task 4 — the mutation proofs (commit `dec138b`)

Six new tests on a 1-layer / 2-head / 16-embd CPU GPT copied from `tests/test_lora_inject.py`. No
checkpoint I/O; whole file **18 tests in 0.92 s**, slowest test 0.26 s.

## The Guards, Watched Failing

### Proof 1 — the in-process canary, on the deliberate no-op swap

```
(ii) [phase17_isolation] PROOF FAILED: loading sweep 'persona_a''s adapter changed NO lora_B
     tensor (ISO-04). All three personas share an identical lora_ key set, identical shapes and an
     identical lora_config, so every audit in load_adapter_weights passes for the WRONG artifact —
     a no-op swap is invisible in the completions and the matrix it produces is fabricated: the
     resident adapter's column reads high in every row while the other two read zero

(iii) [phase17_isolation] PROOF FAILED: sweep 'persona_b' loaded an adapter whose lora_B is
     all-zero at ['blocks.0.attn.c_proj', ... 'blocks.0.mlp.fc_out'] — that is the identity gate
     (`src/personacore/lora/layer.py:30` initialises lora_B to zeros so a fresh wrapper is
     bit-identical to the bare Linear), not an adapter. The delta branch would contribute exactly
     nothing and this sweep would be the base model wearing a persona name
```

Both raises name their contract. The honest load beside them returns a 64-character digest — the
positive control, without which the test would also pass against a canary that refused everything.

**Ordering note worth carrying forward.** Case (iii) must be built on a model that already holds a
nonzero adapter. On a freshly injected model `lora_B` is already zeros, so loading an all-zero
artifact changes nothing and the *delta* proof fires first. That is not a defect: in the real path
`load_adapted_model` always loads Phase 14's nonzero adapter first, so an all-zero Phase 17 artifact
does change the tensors and the identity gate is the branch that bites.

### Proof 2 — the delta `_prove` stripped

`any(not torch.equal(...))` replaced with `True`:

```
E   AssertionError: no SystemExit — the guard never fired for 'ISO-04'
FAILED tests/test_phase17_scoring.py::test_swap_canary_bites
```

That `_prove` is the only thing catching the double load. Restored from a pre-probe copy;
`git diff --quiet -- scripts/phase17_isolation.py` confirms the file is **byte-identical**.

### Proof 3 — the base record's `adapter_enabled` flipped to `True` (the B3 assertion)

```
>       assert base[iso.ADAPTER_ENABLED_KEY] is False
E       assert True is False
FAILED tests/test_phase17_scoring.py::test_base_column_is_a_control
```

This is the assertion that REPLACED the false all-zero-digest claim. Reverted; file restored.

### The measurement that refutes the planning-time expectation

Read off `checkpoints/persona_adapter.pt`'s own `lora_B` tensors, and independently reproduced by
`lora_b_digest` on the live model during the end-to-end run below:

| quantity | sha256 |
|---|---|
| Phase 14 `persona_adapter.pt` live `lora_B` digest (what the base sweep records) | `433cc42fe3a2bb1522723c96558d18ef0f0528c75f59d989e552b9c8a3e54478` |
| an all-zero `lora_B` digest (what an earlier draft expected) | `3ff92f1bf4386b3e693370dcecfae955502dac5c6b106ef5728cb0efcb66d342` |

Not equal. An assertion built on the wrong expectation would have aborted `--report` after all four
GPU sweeps were already paid for.

## End-to-End Run (truncated, written OUTSIDE `results/`)

The base sweep was executed for real on MPS with `held_out_by_slot` truncated to one question per
slot and `SWEEP_RECORD_DIR` redirected to the scratchpad — 8 questions, 0.5 min, no artifact under
`results/`, `checkpoints/` or `data/`:

| observation | value |
|---|---|
| device / preflight | `mps`, torch 2.7.1 |
| `adapter_enabled` | `False` — the in-context `_prove` over every `LoRALinear.enabled` passed |
| `lora_b_sha256` | `433cc42f…` (Phase 14's adapter, resident and inert — exactly what the field claims) |
| draws per question | **9**, read off `SHARED_ARM_CONFIG.n_draws` |
| config block | `max_new_tokens 48, stop_ids [8184, 8185], context_length 256, n_draws 9, forbid_ids_sha256 79b55770…` |
| entry keys | `completions, fact_id, prompt_ids, question, seed_index, slot, stopped` — no `value`/`k`/`n`/`hits` |
| forbid mask | 7645 of 8192 ids masked |
| base column hits | **0** over 72 draws — matching Phase 16's `base-neither` 0/104 on this tier (RESEARCH F-12) |
| clobber guard on rerun | fired, naming the file |

The prelude was also exercised on the adapter path: `--sweep persona_a` runs preflight, loads the
model, proves `block_size` parity and the `forbid_ids` seam, then refuses on the missing
`checkpoints/phase17_persona_a_adapter.pt` with the `--train` command to run first.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 2's `PERSONA_FACTS` criterion and Task 3's action contradict each other**

- **Found during:** Task 2 acceptance criteria, confirmed against Task 3's action text.
- **Issue:** Task 2's criterion asserts `sorted(functions naming PERSONA_FACTS) == ['slot_values']`,
  while Task 3's action mandates
  `train_arm(arm, facts=phase17_persona_facts.PERSONA_FACTS[persona], ...)` inside
  `run_one_persona_training` — a second namer, in the same plan. The criterion's own prose header
  disagrees with its command as well ("`slot_values` **and** `values_by_slot`" vs `== ['slot_values']`;
  `values_by_slot` calls `slot_values` and never names the constant). And 17-04's handover is
  explicit that `grep -c "PERSONA_FACTS"` returning 2 after this plan is a regression.
- **Fix:** one private lazy accessor, `_minted_facts()`, is the sole namer. `slot_values` (scoring,
  needs a slot's three values) and `run_one_persona_training` (teaching, needs a persona's eight
  `Fact` objects) both route through it. Measured: `grep -c "PERSONA_FACTS"` = **1** — 17-04's
  cross-plan contract held exactly — and the AST command returns `['_minted_facts']` rather than
  `['slot_values']`. That is strictly one reader where the criterion asked for one, and it is the
  only form that survives Task 3. Promoted to a committed test,
  `test_the_material_has_exactly_one_reader`, which additionally asserts that none of
  `score_completion` / `classify` / `base_texts_by_slot` / `assemble_matrix` reaches it — the
  invariant 17-04's grep was a proxy for.
- **Files modified:** `scripts/phase17_isolation.py`, `tests/test_phase17_scoring.py`
- **Commit:** `e77de4b`

**2. [Rule 1 - Bug] Task 2's `run_scored_recall` criterion forbids the identifier its action asks for**

- **Found during:** Task 2 acceptance criteria.
- **Issue:** the action says *"Do not dispatch to `recall.run_scored_recall` anywhere"* and the
  criterion is `grep -c "run_scored_recall" ... returns 0`. The first draft's `main()` docstring
  recorded the warning by name and the grep returned **1**. This is 17-01/17-04/17-05's recorded
  shape arriving a fourth time.
- **Fix:** the mechanical criterion wins (17-05's precedent). The docstring carries the whole
  argument — that it scores `item.fact.value`, which is Phase 14's value, and re-running it per cell
  is the N^2 cost ISO-02 prevents — without writing the identifier, and states explicitly why the
  name is omitted. `grep -c` returns **0**; the warning survives intact.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `e77de4b`

**3. [Rule 3 - Blocking] `test_nothing_executes_at_import` goes red the moment `main()` lands**

- **Found during:** Task 2, on adding the `__main__` guard.
- **Issue:** 17-04's test counts every module-SCOPE `ast.Expr(Call)` and asserts exactly one. A
  `main()` call inside `if __name__ == "__main__":` is at module scope by that walk, so the test
  fails — even though the guard is precisely what stops it running under `importlib`. 17-04's own
  SUMMARY anticipated this ("plan 17-06 adds a `main()` to this file that loads a model") without
  widening the test.
- **Fix:** the guard's body is excluded, and the exclusion is **paid for** rather than granted: the
  test now asserts there is exactly ONE `if __name__ == "__main__":` block and that it calls exactly
  `main` (`tests/test_phase16_ladder.py::test_main_exists_and_is_guarded`'s register). Without those
  two assertions the exclusion would be an escape hatch a second, differently-shaped guard could
  widen. Landed in the SAME commit that added the guard, so no commit is red in between.
- **Files modified:** `tests/test_phase17_scoring.py`
- **Commit:** `e77de4b`

**4. [Rule 2 - Missing critical functionality] The sweep record publishes a `context_length` nothing checked**

- **Found during:** Task 3.
- **Issue:** the payload publishes `SHARED_ARM_CONFIG`'s four parity columns, and
  `ArmConfig.context_length` reads `ModelConfig.block_size` — the DATACLASS DEFAULT — while the run
  loads its config from `convbase_slim.pt`. They agree today. If a future checkpoint changed it,
  every cross-sweep parity check would still pass (all four sweeps read the same default) while the
  published column described a model none of the completions came from. This is 16-08's recorded gap,
  closed in `phase16_persistence.run_one_condition:2748`; the plan does not carry it forward.
- **Fix:** `_prove(model_cfg.block_size == SHARED_ARM_CONFIG.context_length, ...)` immediately after
  the load, in the same register and with the same message shape as the Phase 16 original.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `e97c7d4`

### Interpretations recorded

**The `forbid_ids` hash lives in exactly ONE place in the payload.** The plan lists both a
`forbid_digest` field and "the serializable `SHARED_ARM_CONFIG`", but
`persistence.arm_config_record(forbid)` already carries `forbid_ids_sha256` as a committed parity
column. Two copies of one hash in one file is two places it can stop agreeing about the same mask —
the exact failure the constant-not-literal discipline exists to prevent everywhere else in this
phase. **17-08 reads `record["config"]["forbid_ids_sha256"]`.** `forbid_ids_masked` and `vocab_size`
stay top level as the plan specifies.

**`SWEEPS` landed in Task 1's commit rather than Task 2's.** `assert_sweeps_ran_on_distinct_weights`
genuinely needs "the four sweeps" as a set, and defining it there rather than writing
`set(PERSONAS) | {BASE_ROW}` twice is the same import-never-retype rule the constant exists for.
Task 2's AST criterion (a top-level `Assign` whose value is a `BinOp`) was verified and passes.

**The base sweep loads through `resolve_seed` too.** It returns `{"seed": None, "arm": None,
"adapter": None, "record": ...}` for the base row, so one function owns every path decision in the
driver and the base row's *absence* of an adapter is explicit rather than implied by a branch
elsewhere.

**`torch` now enters `tests/test_phase17_scoring.py`.** 17-04 recorded the file as torch-free. The
Task-4 fixtures (`_tiny_config` / `_build_injected` / `_nudge_lora_b`) require it, and it is not a
new cost: the driver this file loads imports `phase16_persistence` -> `phase14_recall`, which puts
torch in `sys.modules` before any test runs. The property that matters is unchanged and stated in the
file — no test loads a checkpoint, reaches a GPU or generates a token; whole file 0.92 s.

**`requirements mark-complete` was NOT run.** ISO-02, ISO-03 and ISO-04 all stay `[ ]` / `Pending`.
17-08 and 17-09 also claim all three, and the first plan to name a requirement marks it Complete for
the whole phase. No adapter has trained, no sweep has run and no matrix exists, so ISO-02's "the
isolation **matrix** scores…" and ISO-03's "the **matrix** carries…" would be flatly false. ISO-04 is
the closer call and is still declined for a concrete reason: **the canary's unskippable half has no
production caller yet** — `assert_sweeps_ran_on_distinct_weights` is called only by tests until
17-08's `run_report_mode` wires it in. This is 17-01's over-claim pattern avoided a fifth time.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase17_scoring.py -x` | **18 passed** in 0.92s (>= 14 required; was 11) |
| `pytest -q tests/test_phase17_scoring.py --durations=5` | slowest **0.26 s** (all < 5 s) |
| `pytest -q tests/test_phase17_scoring.py tests/test_lora_inject.py tests/test_phase14_scoring.py -x` | **66 passed** |
| `pytest -q tests/test_lora_inject.py -x` | **12 passed**, `git diff -- tests/test_lora_inject.py` EMPTY |
| `pytest -q` (full suite) | **636 passed, 1 skipped** in 127.23s (baseline 629/1 + 6 new + 1 widened; floor 579/1) |
| `python scripts/phase17_isolation.py --help` | three modes, one required exclusive group, no mode that runs two sweeps |
| `--sweep persona_a --report` / `--train persona_a --sweep persona_a` / no args | exit **2** each |
| `git diff -- src/personacore/lora/` | **empty** — the canary is a run contract |
| `git diff -- pyproject.toml` (STAT-04) | empty |
| `git status --short results/ checkpoints/ data/` | empty — no recorded evidence touched |
| `grep -c "all-zero"` | **2** — `BASE_COLUMN_NOTE` and the identity-gate message, nowhere else |
| `grep -n "lora_b_sha256\|adapter_file_sha256\|adapter_enabled"` | all three in the writer AND the checker |
| `grep -c "run_scored_recall"` / `grep -c "build_recall_prompt"` | **0** / **0** |
| `grep -c "PERSONA_FACTS"` | **1** — 17-04's handover contract |
| `grep -nE "n_draws\s*=\s*9\|N_DRAWS\s*=\s*9"` | nothing — the draw count is read off `SHARED_ARM_CONFIG` |
| `SWEEPS` is a derived `BinOp` (AST) | exits 0 |
| `train_arm` call carries both `prefix` and `seed` (AST) | exits 0, 1 call site |
| eight cross-process failure modes | eight raises, **eight distinct messages**, positive control passes |
| `.venv/bin/ruff check .` + `format --check .` (the CI version, 0.15.16) | clean, 155 files |
| `make lint` | **red — pre-existing DEF-17-01, count unchanged at 9** |

## Deferred Issues

`make lint` still fails from **DEF-17-01** (recorded at 17-01, pre-existing to it). `Makefile:16`
runs bare `ruff`, which resolves on this box to a pyenv shim holding **ruff 0.1.15** against the
project's `ruff~=0.15` pin. The count is **unchanged at 9** — `tests/test_phase17_scoring.py` was
already in the list after 17-04, and `scripts/phase17_isolation.py` is not in it. `.venv/bin/ruff`
0.15.16 — the version `.github/workflows/ci.yml:36-38` installs and runs — is clean on both files.
Nothing new deferred by this plan.

## Known Stubs

None. Every function this plan commits is complete and exercised.

One forward reference is deliberate and is not a stub: `main()`'s `--report` branch calls
`run_report_mode()`, which **plan 17-08 defines in this same module**, carried with an explicit
`# noqa: F821` and a comment naming its owner. Nothing was written to stand in for it — there is no
placeholder to replace, and a stub here would be a mode that looks runnable and produces nothing.
`--report` before 17-08 lands raises `NameError` naming the missing function.

## Handover Notes

1. **17-08 MUST call `assert_sweeps_ran_on_distinct_weights(records)` inside `run_report_mode`,
   before any scoring.** It is the unskippable half of ISO-04 and nothing in production calls it
   today. Also drop the `# noqa: F821` on `main()`'s `--report` branch in the same commit.
2. **The `forbid_ids` hash is at `record["config"]["forbid_ids_sha256"]`**, not at a top-level
   `forbid_digest` key. One hash, one place.
3. **`results/phase17_personas_report.md` does not exist yet** — 17-05 built the ISO-01 gate driver
   and its tests; 17-07 runs the measurement and records the verdict. `--train` therefore refuses
   today, naming that exact path, which is the gate working. **17-09 cannot run `--train` until
   17-07's GO/ADAPT is recorded.**
4. **17-09's operator sequence is four fresh processes for the sweeps and three for the training,
   and there is no flag that batches them.** `--sweep base` must run too; it is not optional
   (`assemble_matrix` refuses three records).
5. **A Phase-17 arm named `persona_a` builds `data/persona_persona_a_train.bin`** (17-02's recorded
   doubled word, gitignored). A replicate builds `data/persona_persona_a_seed1437_train.bin`.
6. **Do not add the must-differ assertion to `load_adapter_weights` later.** The measured reason is
   in `load_adapter_with_canary`'s docstring: it would refuse
   `tests/test_lora_artifact.py::test_real_slim_two_artifact_load_cpu`, a committed v2.0 test whose
   `skipif` does not engage in this tree.
7. **The category counts remain a ROW property** (17-04's handover #5) — unchanged by this plan.

## Threat Flags

None. No new network endpoint, auth path or schema change at a trust boundary. The one new
file-access pattern — reading a Phase 17 adapter artifact — goes through
`personacore.checkpoint.load_adapter` at `weights_only=True`, the same choke point every other
adapter consumer uses; `torch.load` is never called directly on a shareable artifact anywhere in
this path.

Register dispositions: **TH-17-18** mitigated (both layers, mutation-proved, with each layer's limit
recorded); **TH-17-19** mitigated (`load_adapter_weights` audits keys, shape/dtype and scale before
any tensor is copied; no bare `strict=False` anywhere in this driver); **TH-17-20** mitigated
(`load_adapter`, `weights_only=True`); **TH-17-21** mitigated (one `SHARED_ARM_CONFIG` object, one
`forbid_ids` mask proved against `resolve_forbid`'s seam and recorded by sha256,
`question_seed(index)` identical across all four sweeps, `adapter_disabled` rather than a second
model); **TH-17-43** mitigated (`adapter_enabled` recorded per sweep, cross-checked in
`assert_sweeps_ran_on_distinct_weights`, plus the runtime `_prove` over every `LoRALinear.enabled`
inside the context — and the live digest is never asked to prove inertness); **TH-17-22** mitigated
(refuse-to-rerun on `sweep_record_path` FIRST, watched firing); **TH-17-SC** holds — zero packages
installed, `pyproject.toml` byte-identical.

## Self-Check: PASSED

Files:

- FOUND: `scripts/phase17_isolation.py` (1172 lines, was 404)
- FOUND: `tests/test_phase17_scoring.py` (928 lines, was 567)

Commits:

- FOUND: `18e76a8` feat(17-06): add the ISO-04 adapter-swap canary in both layers
- FOUND: `e77de4b` feat(17-06): add the parser, the slot values and the exhaustive dispatch
- FOUND: `e97c7d4` feat(17-06): add run_one_sweep and run_one_persona_training
- FOUND: `dec138b` test(17-06): mutation-prove both canary layers and pin the cross-process guards
