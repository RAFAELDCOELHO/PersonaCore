---
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
plan: 16
subsystem: comparator
tags: [comparator, dp-sgd, protocol-match, ast-gate, grad-clip, d-04, cpu-only]
requires:
  - scripts/phase23_matched_prereg.py (CONSUMED as a pin; asserted byte-identical to c100388)
  - scripts/phase23_prereg.py (asserted byte-identical to c7de5d4; not imported by the new code)
  - scripts/teach_persona.py (every protocol value derived from its symbols; BYTE-UNCHANGED)
  - src/personacore/training/loop.py (the fact/replay seams the comparator reaches; BYTE-UNCHANGED)
  - results/phase23_sigma_zero.json (the committed protocol the comparator is asserted against)
  - data/persona_dp_n8_train{,_mask,_fact}.bin (INPUTS — this arm builds no bins)
provides:
  - phase23_run.matched_control_call(seed) — the (TrainConfig fields, train kwargs) pair
  - phase23_run.prove_matched_protocol() — the zero-GPU-cost three-gate preflight
  - phase23_run.captured_grad_clip() — the clip_grad_norm_ shadow, PRE-clip norms recorded
  - phase23_run.train_matched_control(seed) — the training leg (NOT RUN by this plan)
  - tests/test_phase23_matched.py — nine CPU-only tests
affects:
  - 23-17 (runs the 5-seed leg, writes MATCHED_CONTROL_RECORD, adds the sub-mode + record writer)
  - 23-19 (writes MATCHED_VERDICT_RECORD from the readings this leg will produce)
tech-stack:
  added: []
  patterns:
    - "AST completeness gates run BEFORE the GPU, so a protocol drift refuses at zero cost"
    - "module-attribute shadow at a torch seam, restored in `finally`, identity-checked outside"
    - "a declared absence recorded as explicit `None` + a stated reason, never a missing key"
    - "expected values read from the committed artifact rather than retyped as literals"
key-files:
  created:
    - tests/test_phase23_matched.py
  modified:
    - scripts/phase23_run.py
    - tests/test_lora_inject.py
decisions:
  - "Did NOT call `rebuild_arm_bins_verifying_sha256` from `train_matched_control`. It opens with
     `_prove(prove_bins_match(...) > 0, ...)` and `prove_bins_match` refuses a MISSING file, so it
     proves byte-identity of bins already present and CANNOT recreate an absent one. The bin gate
     is therefore build-only-if-absent, THEN prove."
  - "Added one refusal the plan did not spell: a PARTIAL dp_n8 corpus. `build_arm_bins` refuses when
     any target already exists, so the plan's literal any-absent branch would have produced an
     `already exists` SystemExit — correct outcome, misleading message. The `_prove` names the real
     state and points at the reviewed delete-and-rebuild route; it does not change WHETHER the run
     refuses, only WHAT the refusal says."
  - "Recorded `float(norm)`'s per-step host sync as a DECLARED cost in `captured_grad_clip`'s
     docstring. It moves no float in the gradient path but it does change the TIMING leg relative
     to the σ=0 arm, and the comparator's wall clock should be read with it in mind."
metrics:
  duration: ~55min
  completed: 2026-08-27
  tasks: 2
  files: 3
  commits: 2
---

# Phase 23 Plan 16: The Protocol-Matched Comparator's Training Leg and Preflight — Summary

The comparator now exists as code whose protocol match is checked **by construction**, and every
refusal in it is reachable at **zero GPU cost**. `DP_ARMS` was not widened, `scripts/teach_persona.py`
and `src/personacore/training/loop.py` are byte-unchanged, and the 5-seed run belongs to 23-17 — it
was not started.

**Commits:** `5ae34b0` (Task 1, the leg) · `e7a9ca0` (Task 2, the nine CPU tests)

## The obstacle dissolved, and it was verified against live source rather than accepted

The planning brief warned that a non-DP arm "cannot reach the `dp_kwargs` seam today". That is true
of `build_arm_bins` and **false of `train()`**, and both halves were measured before a line was
written:

| Claim | Verified at | Reads |
|---|---|---|
| the fact-aligned seam is keyed on the FACT half, not on `dp_fn` | `loop.py:512` | `_fact = {"fact_bin": fact_bin, "n_facts": n_facts}` |
| the replay pass is gated on `replay_windows`, not on `dp_fn` | `loop.py:683` | `if replay_windows is not None:` |
| the legacy clip fires IFF `dp_fn is None` | `loop.py:220-221` | `if dp_fn is None:` / `torch.nn.utils.clip_grad_norm_(...)` |
| `dp_fn` defaults to `None` | live `inspect.signature(train)` | `..., dp_fn=None, ...` |

So the comparator calls `tp.train(...)` directly with the six data kwargs and `dp_fn` absent — the
same register `train_never_taught` already uses for an arm `build_arm_bins` cannot express. **No seam
change at all.**

## Divergences between the plan's cited locations and the live files

The plan instructed me to re-verify every cited line number and symbol against the live file and
**report divergence rather than silently adapt**. Result: **every line number in `loop.py`,
`config.py` and `teach_persona.py` is EXACT.** The four divergences are all in `scripts/phase23_run.py`,
whose `<read_first>` pointers predate 23-10's growth of that file. Measured at `59c28de` (pre-edit):

| Plan cites | Measured at `59c28de` | Delta |
|---|---|---|
| `train_never_taught` at `phase23_run.py:574-690` | **597-713** | +23 |
| `captured_dp_seam` at `:780-812` | **803-835** | +23 |
| `prove_bins_match` / `rebuild_arm_bins_verifying_sha256` at `:194-290` | **217-263** / **266-309** | +23 |
| `prove_bins_match`'s MISSING-file refusal at `:220-226` | **234-249** | +14 |
| `rebuild`'s opening `_prove` at `:266-271` | **289-294** (`:266` is the `def` line) | +23 |
| `train_sigma_zero`'s bin handling at `:841-900` | fn **864-1017**, bins **890-918** | +23 |

Exact and reproduced, needing no adjustment:

| Plan cites | Live line reads |
|---|---|
| `loop.py:512` | `_fact = {"fact_bin": fact_bin, "n_facts": n_facts}` ✓ |
| `loop.py:683` | `if replay_windows is not None:` ✓ |
| `loop.py:220-221` | the `dp_fn is None` clip branch ✓ |
| `config.py:105-106` | `grad_clip: float = 1.0` / `grad_accum_steps: int = 1` ✓ |
| `teach_persona.py:1389` | `is_dp = arm in DP_ARMS` ✓ |
| `teach_persona.py:1585` | `dp_accum = dict(grad_accum_steps=stats["n_facts"]) if is_dp else {}` ✓ |
| `teach_persona.py:1586` | `dp_kwargs = (` ✓ |
| `teach_persona.py:1613` | `final = train(` ✓ |
| `teach_persona.py:1705,1709` | the two `masked_perplexity(` sweeps ✓ |

**Every symbol the plan named resolved.** `tp.arm_spec`, `tp.replay_window_budget`, `tp.BLOCK_SIZE`,
`tp.fact_bin_path`, `tp.LR`, `tp.WARMUP_STEPS`, `tp.MAX_STEPS`, `tp.BATCH_SIZE`, `tp.WEIGHT_DECAY`,
`DP_N8_BIN_SHA256`, and all of `phase23_matched_prereg`'s. `arm_spec("dp_n8")` returns
`(LOCKED_FACTS, False, 0.0)` — the plan's stated `(False, 0.0)` reproduced.

## What landed

### `scripts/phase23_run.py` — a new section (e2), between the σ=0 leg and the sub-modes

**`matched_control_call(seed)`** — returns `(train_config_fields, train_kwargs)` as plain dicts, so
the whole protocol is inspectable without a GPU. **Nothing is retyped**: `n_facts` from
`len(tp.arm_spec(SIGMA_ZERO_ARM)[0])`, `replay_windows` from
`tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE`, `fact_bin` from `tp.fact_bin_path(...)`, the
budget from `tp.LR`/`tp.WARMUP_STEPS`/`tp.MAX_STEPS`/`tp.BATCH_SIZE`/`tp.WEIGHT_DECAY`. Measured:
`grad_accum_steps=8`, `grad_clip=1e6`, `n_facts=8`, `replay_windows=32`. `dp_fn` and `resume_from` are
both deliberately absent, each with its reason in a comment.

**`prove_matched_protocol()`** — the zero-cost preflight. Reads `loop.py` and `teach_persona.py` off
disk and drives all three of 23-15's gates, then proves **both directions** of the key-set
subtraction. Measured output:

```
[phase23_run] matched preflight: 7 dp_fn branch(es), 21 production train() keyword(s),
19 on the comparator (= production - {resume_from, dp_fn}) — all three AST gates GREEN
```

**`captured_grad_clip()`** — `captured_dp_seam`'s shadow register at `torch.nn.utils.clip_grad_norm_`.
`loop.py:221` resolves that attribute at CALL time on the shared module object, so the shadow is
visible without editing `loop.py`; `clip_grad_norm_` RETURNS the **pre-clip** global norm, so the
captured list is exactly the quantity probe 1 measured.

**`train_matched_control(seed)`** — the training leg. `train_never_taught`'s register throughout, plus
the bin gate, the non-binding proof before any reading exists, and a return block carrying the
protocol as numbers.

### `tests/test_phase23_matched.py` — nine CPU-only tests, none of which trains

Verified by the plan's **AST gate** (not a grep): `AST clean 65 calls scanned` — no `train`/`GPT`
call, no `CONVBASE_BEST`, no `convbase_best` string outside a docstring.

## The three findings this plan's own work produced

### 1. The bin gate's order is forced, and the obvious helper is the wrong one

`rebuild_arm_bins_verifying_sha256` **is not called** from `train_matched_control`. It opens with
`_prove(prove_bins_match(expected_sha256) > 0, ...)`, and `prove_bins_match` refuses a **MISSING**
file by name. It proves byte-identity of bins that are already present; it **cannot recreate an
absent one**. The gate is therefore: build only if absent, **then** prove — never prove-then-build.

### 2. A partial corpus needed a refusal the plan did not spell

Following the plan's any-absent branch literally when *some* bins survive hands `build_arm_bins` a
target that already exists, and its `refuse_if_exists` fires with an `already exists` message — the
right outcome behind a misleading explanation. One `_prove` now names the actual state (partial
corpus), says why it cannot be completed in place, and says why deleting the survivors here would
destroy the only evidence of how it went partial. **It does not change whether the run refuses.**

### 3. The clip capture buys an observation and costs a host sync

`float(norm)` inside the wrapper forces a per-optimizer-step host sync the σ=0 arm did not have. It
moves no float in the gradient path, so the arithmetic comparison is untouched — but it does perturb
the **timing** leg. Recorded in the docstring as a declared cost rather than discovered by 23-17
when its `training_seconds` reads slightly long.

**On 23-15's warning about on-device comparisons:** it was heeded. `captured_grad_clip` verifies
nothing by tensor comparison at all — it records a **scalar read back to host** and compares it in
Python. The one bitwise comparison in the leg is `train_never_taught`'s existing `torch.equal`
canary, copied verbatim and unchanged in scope; it checks whether parameters MOVED (a large,
normal-range difference), not whether a subnormal survived, so the MPS flush cannot make it green
and blind.

## Deviations from Plan

### 1. [Rule 3 - Blocking] `tests/test_lora_inject.py`'s `INJECT_LORA_PRODUCERS` register reddened

- **Found during:** Task 1, after the automated verification passed.
- **Issue:** `test_every_inject_lora_consumer_reads_the_artifact_config` classifies every
  `inject_lora(model, cfg)` site under `scripts/*.py` + `src/**/*.py` and asserts **hard equality**
  on all three buckets. `train_matched_control` calls `tp.inject_lora(model, tp.LORA_CFG)` and
  exports an adapter carrying `asdict(tp.LORA_CFG)`, so it is a genuine new PRODUCER:
  `found: [... ('scripts/phase23_run.py', 'train_matched_control'), ...]` against a 3-entry register.
- **Fix:** added the one visible register line the guard's own docstring asks for ("a NEW consumer
  belongs in `INJECT_LORA_CONSUMERS` as one visible line"), with the reason: this arm passes
  `teach_persona.LORA_CFG` rather than a second bare `LoRAConfig()`, which is strictly stronger here
  — its whole purpose is to differ from the σ=0 arm by protocol and nothing else, so a second config
  definition free to drift would put a rank-or-scale difference inside the one comparison D-04 turns
  on. The guard's teeth are unmoved: hard equality, and the new site is classified as a producer by
  the same `_resolve`-through-the-alias path the existing `train_never_taught` entry uses.
- **Files modified:** `tests/test_lora_inject.py`
- **Commit:** `5ae34b0`
- **Not in the plan's frozen list.** The Task-1 acceptance criteria freeze seven files; this is not
  one of them, and `git diff --exit-code` over all seven exits 0.

### 2. [Rule 3 - Blocking] Two `E501` docstring lines

- **Found during:** Task 1, `ruff check`.
- **Fix:** rewrapped. No content removed.
- **Commit:** `5ae34b0`

### 3. [Rule 3 - Blocking] `I001` import-block ordering in the new test file

- **Found during:** Task 2, `ruff check .`.
- **Fix:** `ruff check --fix` separated the `sys.path`-dependent script imports from the
  `personacore` import with a blank line. Behaviour unchanged; the `# noqa: E402` markers stand.
- **Commit:** `e7a9ca0`

### Two guards that did NOT redden, checked because 23-15 named them

23-15's hand-off warned that new AST fixtures naming `train_arm` or comments reading `== 10` would
redden `tests/test_phase23_resume.py` and `tests/test_phase21_sc5.py`. Both were kept green **by
construction**: the literal `train_arm(` appears nowhere in the new code (docstrings say
`train_arm`'s / `teach_persona.train_arm` without a paren), and no line in the new test file matches
`(?:==|!=)\s*10(?![0-9_])`. Section banners use `TEST n —` form, per 23-15's deviation 3. Both files
were run explicitly and both passed.

**No authentication gates occurred. No package was installed. No architectural decision was needed.**

## Verification

| Check | Command | Result |
|---|---|---|
| Task 1 automated verify | the plan's 12-assertion probe | `OK 7 8 32` |
| Preflight against live source | `prove_matched_protocol()` | 7 branches / 21 production keys / 19 comparator keys |
| Key-set subtraction | exact set equality | `seen == set(TRAIN_CALL_KEYS) - {resume_from, dp_fn}` ✓ |
| `fact_bin` resolves | — | `data/persona_dp_n8_train_fact.bin` ✓ |
| `log_path` / `checkpoint_path` | — | `results/phase23_matched_control_seed1337/run.csv` / under `checkpoints/` ✓ |
| New tests | `pytest tests/test_phase23_matched.py -q` | **9 passed** |
| No-training AST gate | the plan's AST walk | `AST clean 65 calls scanned` |
| **Full suite** | `.venv/bin/python -m pytest -q` | **`1509 passed, 1 skipped`** (83 warnings, 361.41s) |
| Lint | `ruff check . && ruff format --check .` | clean, 217 files formatted |
| Frozen seven | `git diff --exit-code -- teach_persona, loop, phase23_prereg, phase23_matched_prereg, mitigation_{gate,accountant,budget}` | **exit 0** |
| Blind pin at its 23-15 state | `git diff --exit-code c100388 -- scripts/phase23_matched_prereg.py` | **exit 0** |
| Closed pin at `c7de5d4` | `git diff --exit-code c7de5d4 -- scripts/phase23_prereg.py` | **exit 0** |
| `DP_ARMS` not widened | `grep -c DP_ARMS scripts/teach_persona.py` | **9**, unchanged from pre-plan |
| Matched glob still empty | `git ls-files 'results/phase23_matched_*' \| wc -l` | **0** |
| No `results/` or `data/` change | `git status --short results/ data/` | empty |
| No accidental deletions | `git diff --diff-filter=D --name-only` over both commits | none |

**The full-suite count matches the plan's expectation exactly: `1509 passed, 1 skipped`** = 23-15's
1500 plus this plan's 9 new tests. No pre-existing test changed status.

## Requirements

**NO requirement is ticked, and none is claimed.** `DPSGD-06` remains open. This plan makes the
comparator *runnable*; it delivers no reading, so it delivers no part of CAL-01 / CAL-02 / CAL-05 /
CTRL-03. The plan's own success criteria end with "NO requirement is ticked."

## D-04 HALT compliance

**Zero noised sweep points ran. Zero training of any kind ran.** `23-11`…`23-14` were not touched.
No `results/` artifact was created, modified or deleted; `git ls-files 'results/phase23_matched_*'`
returns **0** at the end exactly as it did at the start. `train_matched_control` was **written and
never called** — the 5-seed run is 23-17's, and nothing in this plan's tests reaches it (proven by
the AST gate, not asserted).

## Known Stubs

None. Every function added is exercised: `matched_control_call` and `prove_matched_protocol` by six
tests plus the plan's probe, `captured_grad_clip` by a watched observe-and-restore test.

`train_matched_control` is the one function not executed, and that is **the plan's instruction, not
a stub** — it is the GPU leg, budgeted to 23-17 under the D-04 halt. Every piece of it that can be
decided without a GPU is decided here: its kwargs (tests 1-4), its clip constant (tests 5-6), its
capture bracket (test 7) and its preflight (test 9). What remains unexercised is the ~100 minutes of
optimizer steps between them.

## Notes for 23-17

- **Add the sub-mode and the record writer.** `_TABLE` and `USAGE` were deliberately NOT touched
  here, per the plan's Task 1 instruction.
- **The return block already carries the protocol fields under the σ=0 record's own names**
  (`n_facts`, `grad_accum_steps`, `replay_windows_per_step`, `replay_micro_batches_per_step`,
  `max_steps`, `batch_size`, `block_size`, `dp_seam_active: False`) plus the clip observation
  (`grad_clip_calls`, `grad_clip_{max,min}_pre_clip_norm`, `grad_clip_bound_count`,
  `grad_clip_checked_before_scoring`) and `corpus_sha256`.
- **Six fields are explicit `None` with `ppl_omitted_reason`** — `ppl_adapter_on`, `ppl_adapter_off`,
  `ppl_scored_targets`, `teaching_tokens`, `replay_tokens`, `replay_ratio`. Do not back-fill them;
  they are declared in `MATCHED_DIFFERENCES` and running the sweeps costs scoring time the budget
  does not hold.
- **Call `prove_matched_protocol()` before the first seed**, not per seed — it is free but it reads
  two files, and its refusal must arrive before any GPU second.
- **`captured_grad_clip` costs a per-step host sync.** Read `training_seconds` with that in mind
  when comparing against the σ=0 arm's `seconds_per_optimizer_step`.
- **`prove_first_attempt`** takes the caller's `git ls-files` result; it runs no subprocess. Wire it
  in 23-17 with `MATCHED_ARTIFACT_GLOB`.
- **`scripts/phase23_matched_prereg.py` is EDIT-ONCE from your first artifact.** Nothing here edited
  it and there is no safety valve.

## Threat Flags

None. No new network endpoint, auth path or schema at a trust boundary. The one process-global
mutation — the `torch.nn.utils.clip_grad_norm_` shadow — is T-23-66 in the plan's own register,
mitigated as specified: restored in `finally` and identity-checked outside the bracket by a
dedicated test. No package was installed (T-23-SC).

## Self-Check: PASSED

- `scripts/phase23_run.py` carries `matched_control_call`, `prove_matched_protocol`,
  `captured_grad_clip`, `train_matched_control` — all four FOUND and callable
- `tests/test_phase23_matched.py` — FOUND, 9 tests passing
- `tests/test_lora_inject.py` — FOUND, 12 tests passing
- Commit `5ae34b0` — FOUND in `git log`
- Commit `e7a9ca0` — FOUND in `git log`
- `git ls-files 'results/phase23_matched_*'` — still **0**
- All four frozen pre-registrations — byte-unchanged
