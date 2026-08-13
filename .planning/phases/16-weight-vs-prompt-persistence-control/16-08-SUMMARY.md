---
phase: 16-weight-vs-prompt-persistence-control
plan: 08
subsystem: evaluation
tags: [PERS-02, PERS-04, STAT-05, pre-registration, arm-parity, cosine-baseline, structural-guard]

# Dependency graph
requires:
  - phase: 16 (plan 02)
    provides: "run_fairness_control's PERS-05 seed fix and assert_value_in_prompt — arm B is only paired because that landed first"
  - phase: 16 (plan 03)
    provides: "the widened persona= / draw_all AST guards, which now scan this new file automatically"
  - phase: 16 (plan 07)
    provides: "the committed capability ladder — PERS-01's ordering constraint discharged before this pre-registration exists"
  - phase: 14 (teach-then-recall)
    provides: "run_scored_recall / run_closed_book_control / run_fairness_control / contains_value / RECALL_MAX_NEW_TOKENS / STOP_IDS / N_SEEDED_SAMPLES — the instrument this driver invokes rather than reimplements"
provides:
  - "CONDITION_ORDER locked as a four-name tuple before any arm produces a number (D-03)"
  - "ONE SHARED_ARM_CONFIG object holding the four SCALAR parity fields, read by identity — not four agreeing literals"
  - "forbid_ids parity as a sha256 content hash, because undecodable_ids_mask needs a loaded tokenizer and cannot be an import-time constant"
  - "PER_QUESTION_KEYS + normalize_by_split + assert_record_shape: one per-question shape across four arms whose committed return shapes disagree"
  - "Arm D — embedding/cosine over the committed 20-value lexicon, adapter structurally off, emitting TEXT scored by the phase's single scorer"
affects: [16-09, 16-10, 16-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Parity is a shared OBJECT plus an identity assertion, never N literals that agree today"
    - "A field that needs runtime state (a loaded tokenizer, a device) is recorded by CONTENT HASH instead of being forced into an import-time constant"
    - "A derived constant (COSINE_POOL_SIZE = round(1/COSINE_CHANCE_FLOOR)) instead of a second literal that must agree"
    - "A superseded figure lives in exactly one comment and is AST-pinned out of executable code"
    - "Dispatch is exhaustive with NO default branch, guarded from both sides: unknown name aborts, and known-name-without-branch aborts"

key-files:
  created:
    - "scripts/phase16_persistence.py — 700 lines: the pre-registration, arm dispatch, and arm D"
    - "tests/test_phase16_driver.py — 29 tests, CPU-only, no checkpoint required"
  modified: []

key-decisions:
  - "CONDITION_ORDER's rationale is a module-level STRING (CONDITION_ORDER_RATIONALE), not a comment — a comment cannot be printed into the report nor pinned byte-for-byte against 16-CONTEXT.md"
  - "The four scalar parity fields are checked by `is`, and the SHARED_ARM_CONFIG object itself travels on every arm record, because `is` on a small int is satisfied trivially by CPython interning"
  - "run_condition contains zero `for` statements: arm A's per-tier calls are a comprehension over TIERS, and the flatten/regroup lives in normalize_by_split"
  - "split is resolved by membership in the committed heldout_questions() set, then cross-checked against the two core buckets — the fixture does not record split per entry"
  - "embed_sequence uses a forward hook on model.ln_f: GPT.forward returns only (logits, loss) and exposes no hidden-state seam, so a hook is the fallback the plan sanctioned"
  - "Arm D calls contains_value directly and never score_question, so its n=1 comes from D-22's decision rather than from a list length"

requirements-completed: [PERS-02, PERS-04, STAT-05]

# Metrics
duration: 35min
completed: 2026-08-13
---

# Phase 16 Plan 08: The four-arm comparison driver's pre-registration Summary

**The condition order, the one shared arm-parity config, the dispatch onto the three committed Phase 14 arm functions, and the one genuinely new arm — all committed to git before any of the four arms produces a number they will be judged by.**

## Performance

- **Duration:** ~35 min wall clock (19:40 → 20:14 -03:00)
- **Tasks:** 3
- **Files created:** 2
- **Tests added:** 29 (469 → 498 passed)

## Task Commits

1. **Task 1 — the pre-registration block** — `d2d1294` (feat)
2. **Task 2 — arm dispatch onto the committed instrument** — `35fc303` (feat)
3. **Task 3 — arm D, the embedding/cosine baseline** — `59dd473` (feat)

## The two constants under external review, as landed

```python
CONDITION_ORDER = ("adapter-only", "base-neither", "embedding-cosine", "prompt-stuffed")
COSINE_CHANCE_FLOOR = 0.05
```

`CONDITION_ORDER_RATIONALE` records **exactly two reasons** — pre-registration prevents choosing
the order after seeing numbers, and "adapter-only first" means the most critical result is already
in hand under interruption — followed by D-03's required sentence, byte-identical to
`16-CONTEXT.md` and asserted against the file rather than against a second hand-typed copy:

> sob o split de quatro processos frescos, o resultado é invariante à ordem — a ordem é
> pré-registro puro, sem efeito físico sobre o resultado.

The deleted third rationale is **absent from the source, not annotated in it**.
`test_condition_order_does_not_carry_the_deleted_rationale` greps the SOURCE (not the loaded
module), because a comment is as inheritable downstream as a constant. The rationale string states
that a third reason was drafted and deleted, and that it is not restorable from anything in this
repository — which records the fact of the deletion without re-typing the false claim.

`COSINE_CHANCE_FLOOR = 0.05` carries D-25's numeric reconciliation in the comment beside it: the
qualifier text was written citing 8 candidates and a floor of 0.125, the pool decision taken in the
same round chose the 20-value lexicon, and **0.05 is the number the report uses**. The superseded
figure appears on exactly one line of the module, in that comment, and
`test_chance_floor_literal_matches_the_pool` walks the AST asserting `0.125` is not a `float`
constant anywhere in executable code (T-16-35). `COSINE_POOL_SIZE` is `round(1 / COSINE_CHANCE_FLOOR)`
— derived, so there is no second literal that must agree.

## The resolved `SHARED_ARM_CONFIG`

```
ArmConfig(max_new_tokens=48, stop_ids=frozenset({8184, 8185}), context_length=256, n_draws=9)
```

Every field is READ from the committed instrument, never retyped:

| field | source | value |
|---|---|---|
| `max_new_tokens` | `phase14_recall.RECALL_MAX_NEW_TOKENS` (D-19, derived from the token census) | 48 |
| `stop_ids` | `phase14_recall.STOP_IDS` | `frozenset({8184, 8185})` |
| `context_length` | `personacore.config.ModelConfig.block_size` | 256 |
| `n_draws` | `1 + phase14_recall.N_SEEDED_SAMPLES` | 9 |

`test_all_arms_share_one_config_object` asserts all four by `is` against `SHARED_ARM_CONFIG` AND
that each field `is` the instrument's own constant. Because `is` on a small int is satisfied
trivially by CPython interning, `arm_config_record` also carries the **object itself** under
`shared_arm_config`; `assert_arm_parity` rejects an `ArmConfig` twin whose fields are equal but
whose identity is not (`test_arm_parity_rejects_a_mismatch` builds exactly that twin).

### How `forbid` is injected, and its content hash

`forbid_ids` is deliberately **not** a field on `ArmConfig`. `undecodable_ids_mask(tokenizer,
vocab_size)` needs a LOADED tokenizer, so it cannot run at import time, and it returns a torch
tensor whose `==` is elementwise and whose identity is meaningless across the four fresh processes
D-01 requires. Parity on `forbid` is already **structural** (`phase14_recall.py:520` threads one
object through every arm), so what this driver adds is auditability:

- `resolve_forbid(tok, vocab_size) -> (mask, sha256)` — the ONE runtime seam that calls
  `undecodable_ids_mask`. Plan 16-10's `main()` calls it once and threads the mask into all four
  conditions.
- `forbid_digest(forbid)` — sha256 of the mask's bytes, read off a CPU copy so the hash is
  device-stable.
- `arm_config_record(forbid)` puts `forbid_ids_sha256` on every arm's record, and
  `assert_arm_parity` compares it as one of the five `PARITY_COLUMNS`.

Measured on the real frozen tokenizer (`artifacts/tokenizer.json`, `vocab_size=8192`):

```
forbid shape (1, 8192), 7645 ids masked  (the committed 547-of-8192 decodable fact)
sha256 79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28
```

`test_forbid_is_not_resolved_at_import` asserts no module-level call to `undecodable_ids_mask` /
`from_json` / `load_adapted_model`, and that **no module attribute is a torch tensor**.

## The normalized per-question shape

```python
PER_QUESTION_KEYS = ("fact_id", "split", "seed_index", "k", "n")
```

The four committed arms disagree about their return shape, and the disagreement is load-bearing
rather than sloppy. `normalize_by_split` flattens all three cases onto one per-question list, then
regroups on **each entry's own `split` field** — never on which record it came out of. Arm A's
`core_taught` record happens to be split-pure today; a grouping that assumed so would silently
mislabel the moment it stopped being, and the mislabelling is invisible in the resulting rate.

| arm | committed return | flattening path | example entry (extra keys beyond the five) |
|---|---|---|---|
| A `adapter-only` | **three** tier records (`run_scored_recall` per tier) | list of dicts → each `["questions"]` | `question, slot, value, reserved, prompt_ids, dump, completions, hits, stopped, contradictions, hedging` |
| C `base-neither` | **one** record (`run_closed_book_control`) | single dict → `["questions"]` | same as arm A — it routes through `run_scored_recall` |
| B `prompt-stuffed` | **one** record (`run_fairness_control`) | single dict → `["questions"]` | `question, persona, prompt_ids, completions, hits, stopped` |
| D `embedding-cosine` | one record, **and** a bare per-question list is accepted | dict → `["questions"]`, or entries passed through | `question, emitted, similarities` (20 floats) |

One arm-D entry, with the emitted value elided (the SUMMARY is not a place for fact material):

```python
{"fact_id": "cand_...", "split": "held-out", "seed_index": 0, "k": 0, "n": 1,
 "question": "the name you go by is", "emitted": "<a pool value>",
 "similarities": [0.41, ...]}   # 20 floats, one per candidate
```

`run_condition` returns `{"condition", "config", "by_split"}` — an identical outer shape for all
four arms — and calls `assert_record_shape` last, so a dropped key aborts at the arm that produced
it rather than at 16-09's `record["fact_id"]` several waves later.
`test_assert_record_shape_rejects_a_missing_key` drops each of the five keys in turn and asserts the
failure message names the one that went missing.

## Arm D

- **Pool:** `sorted(set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES})` — the exact
  lexicon `find_contradictions` already consumes (D-23), with zero new editorial judgment.
  Measured: **20 distinct values**, and `1 / 20 == COSINE_CHANCE_FLOOR` is `_prove`d inside
  `candidate_pool()` at every call, not only in a test. Sorted, so the argmax index means the same
  thing in every process of the four-process split.
- **Embedding seam:** a `register_forward_hook` on `model.ln_f`, removed in a `finally`. **No
  cleaner already-exposed seam exists** — `GPT.forward(idx, targets=None) -> (logits, loss)` is a
  LOCKED contract and returns nothing but logits, and `ln_f`'s output at `gpt.py:206` is the final
  hidden state. `ln_f` is not one of the six per-block projections `inject_lora` wraps, so the hook
  sees the LayerNorm itself in both the injected and un-injected model.
  `test_embed_sequence_does_not_mutate_the_forward_contract` asserts the 2-tuple survives, that
  `model.ln_f._forward_hooks` is empty afterwards, **and** that a raising forward still leaves no
  hook behind (the `finally` path, exercised by overrunning `block_size`).
- **Adapter OFF is structural** (D-24): `with adapter_disabled(model)` encloses the whole body,
  including the 20 candidate embeddings. An AST test asserts the manager is present AND that the
  question loop is INSIDE it — a `with` beside the loop would make the flag a no-op.
- **One deterministic draw** (`n = 1`), per D-22. `run_cosine_arm` calls `contains_value` directly
  and never `score_question`, so `n` comes from D-22's decision rather than from a list length; an
  AST test pins that.
- **The clean room is not relaxed for it** (T-16-32): every prompt is the same bare
  `build_recall_prompt(tok, question)` arms A and C receive, and `assert_no_value_in_prompt` runs
  per question.
- **PERS-04's out-of-scope bound** is a grep, not a sentence: `faiss`, `sklearn`, `rerank`,
  `chunk`, `top_k`, `annoy`, `hnsw`, `bm25` and `scipy` are all absent from the module.

## What this plan did NOT do, deliberately

- **No `persona=` call site was added**, so `PERSONA_ALLOWLIST` is untouched at its two entries
  (verified: `run_fairness_control`, `build_far_prompt`). Arm B routes through the one allowlisted
  site. A local test asserts the same thing so the failure names the file a reader is editing.
- **No `draw_all` call site was added**, so `DRAW_ALL_ASSERTED_BY` is untouched at one entry.
  `test_driver_defines_no_draw_loop` asserts the module calls none of `draw_all`, `_complete`,
  `complete_question` or `generate`, and that `run_condition` holds zero `ast.For` nodes.
- **No model was loaded and no generation was run.** This plan is pre-registration only. The one
  place a model is touched is the arm-D test, which builds a tiny randomly-initialized
  `GPT(ModelConfig(n_layer=1, n_head=1, n_embd=8))` — the real 13.9M checkpoint is not required by
  any test in this file.
- **`results/` and `pyproject.toml` are byte-unchanged** (`git diff --stat` empty across all three
  commits). No package was installed; STAT-04's freeze was never approached.

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_driver.py -q
    12 passed        (Task 1 gate)
    20 passed        (Task 2 gate)
    29 passed        (Task 3 gate)

.venv/bin/python -m pytest tests/test_phase16_driver.py tests/test_phase14_scoring.py -q
    62 passed        (Task 2 acceptance — the D-21 guards still green with the new file in scan)

.venv/bin/python -m pytest tests/test_package.py tests/test_phase14_scoring.py \
                          tests/test_phase16_ladder.py tests/test_phase16_fixture_regen.py -q
    94 passed

.venv/bin/python -m pytest -q
    498 passed, 1 skipped, 83 warnings in 121.34s (0:02:01)

.venv/bin/python -m ruff check .           All checks passed!
.venv/bin/python -m ruff format --check .  147 files already formatted

git diff --stat results/ pyproject.toml    (empty)
git status --short                          (empty)
```

**Baseline was `469 passed, 1 skipped`, captured by the orchestrator immediately before dispatch.
Result `498 passed, 1 skipped`. Delta `+29` = this plan's 29 new tests. Zero failed, zero errors,
zero collection errors.**

### Acceptance criteria, item by item

| Criterion | Result |
|---|---|
| `CONDITION_ORDER == ('adapter-only','base-neither','embedding-cosine','prompt-stuffed')` via importlib | exit 0 |
| `grep -c "residual context-window\|context-window risk"` | **0** |
| `grep -c "DEGEN-2"` | **0** |
| D-03 sentence byte-identical to `16-CONTEXT.md` | asserted by test, extracted from the file |
| No module-level import of `phase14_factset` / `phase14_factset_gate` (AST) | asserted by test |
| `tests/test_phase16_fixture_regen.py` green, fixture byte-unchanged | 5 passed, `git diff --stat` empty |
| `PERSONA_ALLOWLIST` still exactly 2 entries | **2** |
| `run_scored_recall` / `run_closed_book_control` / `run_fairness_control` each called once in `run_condition` (AST) | asserted by test |
| `run_condition` contains no `for` loop | asserted by test (zero `ast.For`) |
| `>= 18` tests collected | **29** |
| `grep -c "COSINE_CHANCE_FLOOR = 0.05"` | **1** |
| `grep -c "0.125"` | **1** (the D-25 reconciliation comment) |
| `grep -ciE "faiss\|sklearn\|rerank\|chunk"` | **0** |
| `grep -c "scipy"`, `git diff pyproject.toml` | **0**, empty |
| `contains_value` the only scoring predicate in `run_cosine_arm` (AST) | asserted by test |
| `test_embed_sequence_does_not_mutate_the_forward_contract` | passes, incl. the `finally` path |
| `tests/test_package.py` green (STAT-04) | passed |
| `scripts/phase16_persistence.py` >= 250 lines, contains `CONDITION_ORDER` | **700** lines |
| `tests/test_phase16_driver.py` contains `test_condition_order_is_locked` | present |

## Deviations from Plan

### 1. [Structure] `CONDITION_ORDER`'s rationale is a module-level STRING, not a comment

- **Plan text:** "Its comment block records exactly two reasons and nothing else … Plus this
  sentence, verbatim and required."
- **What landed:** `CONDITION_ORDER_RATIONALE` and `CONDITION_ORDER_PREREGISTRATION` as module-level
  strings, with a short comment above `CONDITION_ORDER` pointing at them.
- **Why:** the plan requires the sentence to be pinned **byte-for-byte against `16-CONTEXT.md` by a
  test, not by eye**, and requires 16-10 to print it into the report. A comment can do neither. The
  sibling driver `scripts/phase16_ladder.py` already uses module-level strings for exactly this
  register (`PROXY_FRAME_CAVEAT`, `REPORT_FRAMING`), and this plan itself asks for
  `SEQUENTIAL_QUESTIONS_JUSTIFICATION`, `NO_KV_CACHE_NOTE` and `PROCESS_SPLIT_NOTE` in that shape.
  The two reasons are recorded once, in one place, and nothing is duplicated between the comment and
  the string.

### 2. [Sequencing] Task 2's commit carried a one-line `# noqa: F821`, removed by Task 3's commit

- **What happened:** the plan puts `run_cosine_arm` / `candidate_pool` in Task 3 and their call site
  in Task 2's `run_condition`. That forward reference is legal Python (resolved at call time) but is
  an F821 for ruff, so Task 2's commit would have been lint-red standing alone — and `ruff check` is
  part of the gate.
- **What was done:** a `# noqa: F821` scoped to that ONE line, with a three-line comment naming the
  commit that removes it. Task 3's commit deletes both. Both commits are green standing alone.
- **The alternative considered and rejected:** swapping the commit order. It does not work — Task 3's
  `test_cosine_arm_records_the_full_per_question_key_set` consumes `PER_QUESTION_KEYS`, which is
  Task 2's deliverable, so the dependency is circular across the boundary in either direction.
- **The residual gap, stated plainly:** between `35fc303` and `59dd473` a real `run_condition(
  "embedding-cosine", ...)` call would have raised `NameError` rather than aborting cleanly. Nothing
  calls it in that window — `main()` is 16-10's — and the window is one commit long.

### 3. [Environment] `make test` / `make lint` substituted with venv-explicit invocations

- **Plan text:** `<verification>` specifies `make test`.
- **What was run:** `.venv/bin/python -m pytest -q`, `.venv/bin/python -m ruff check .`.
- **Why:** recorded fact about this machine, same substitution as 16-01/16-02/16-03 — a bare
  `pytest` resolves to a pyenv 3.12 shim and yields ~63 spurious
  `ModuleNotFoundError: No module named 'torch'` collection errors across files this plan never
  touched. The gate actually run is the full suite the `make` target wraps.

### 4. [Interpretation] Arm D returns a full record; `normalize_by_split` also accepts a bare entry list

- **Plan text, Task 2:** "arm D … returns per-question entries directly." **Plan text, Task 3:**
  "`run_cosine_arm(…)` -> a record in the same shape the other arms return."
- **What landed:** `run_cosine_arm` returns a record (Task 3's wording), and `normalize_by_split`
  accepts a single record, a list of records, **or** a bare list of per-question entries.
- **Why:** the record shape makes 16-10's report writer uniform across four arms and carries the
  arm's `n_answerable` and `chance_floor`. Accepting the bare list costs one conditional expression
  and makes both readings of the plan true, which is cheaper than choosing one and being wrong.
  `test_every_arm_normalizes_to_the_same_record_shape` exercises all three inputs.

---

**Total deviations:** 4 (1 structure, 1 sequencing, 1 environment, 1 interpretation). **Zero code
deviations under rules 1-4** — nothing was auto-fixed, no bug was found, and no locked value was
altered. Deviation 1 is the only one that changes the shape of an artifact relative to the plan text,
and it strengthens the pin the plan asked for rather than relaxing it.

## Concerns recorded, implemented AS LOCKED

**`COSINE_CHANCE_FLOOR = 0.05` is implemented exactly as pre-registered, and the concern is about
what it will be compared against, not about the number.** Arm D is closed-set retrieval over 20
candidates; arms A/B/C are open-vocabulary generation. D-25 already requires the qualifier to travel
into the report, and 16-10 must carry it — but note that the qualifier's own text says "8 candidatos,
piso de acaso 0.125", so whoever writes the report will be quoting a verbatim user instruction whose
numbers disagree with the pool that was chosen. The module comment records the reconciliation; the
report must quote the qualifier AND state that the operative floor is 0.05, or a reader who checks
the arithmetic will find a contradiction with no resolution attached.

**Arm D embeds each candidate as its bare `tok.encode(value)` id sequence** (4-8 tokens) against a
33-token prompt embedding. That asymmetry is a property of the baseline PERS-04 specifies, not a
tuning choice, and it is recorded here rather than adjusted: any "improvement" — embedding the value
inside a carrier sentence, length-normalizing, calibrating — would be exactly the editorial judgment
D-23 chose the committed lexicon to avoid, and would be a knob tuned before a number exists to tune
it against.

**No deliberate-RED observation is recorded, because this plan's acceptance criteria require none.**
16-08 has no `Deliberate-RED, observed and recorded` item in any of its three tasks (unlike 16-09,
which has three). Nothing was mutated and nothing needed restoring, so `git diff --exit-code` is
clean by construction rather than by repair.

## Issues Encountered

- **The soft tier's `split` is not recorded in the fixture.** `results/phase16_recall_sample.json`
  stores `seed_index` / `fact_id` / `question` / `reserved` and leaves the split implicit in the
  ordering of its lists. Resolved by membership in the committed `phase14_factset.heldout_questions()`
  set — the same seam `phase14_recall.main()` already `_prove`s its constructed split against — and
  then cross-checked: `core_taught` must resolve entirely to `taught` and `core_held_out` entirely to
  `held-out`, or the fixture and the fact set have drifted apart. Measured: 54 soft questions split
  28 taught / 26 held-out, matching `2 facts x (14 + 13)`.
- **`ArmConfig.context_length` reads `ModelConfig.block_size` (the dataclass default, 256), not the
  loaded checkpoint's config.** That is the pre-registered value; the real run's model is loaded from
  `convbase_slim.pt`, whose `model_config` also carries 256 (recorded in `16-CONTEXT.md` §Measured
  Facts). If a future checkpoint ever changed it, `assert_arm_parity` would still pass while the
  published column disagreed with the model — worth a one-line `_prove` in 16-10's `main()` against
  the loaded `model_cfg`, which is where the loaded config is in scope.
- **No package was installed and none was needed**, so 16-01's `pyproject.toml` sha256 freeze was
  never approached.
- **The dangling identifier D-10 declares non-existent** stayed out of both created files, all three
  commit messages, and this summary.

## Next Phase Readiness

- **16-09 can key on `record["fact_id"]` uniformly across all four arms.** `normalize_by_split`
  guarantees it, and `assert_record_shape` fails at the producing arm if it ever stops being true.
  `PER_QUESTION_KEYS` is the constant to import rather than a shape to re-derive.
- **16-09's `aggregate_by_fact` gets a `by_split` dict keyed by `"taught"` / `"held-out"`** — the
  exact two labels `RecallItem.split` carries, not the fixture's tier names.
- **Arm D's denominator is different by design and that is D-22-compatible.** Its per-fact rate is
  `hits/13 held-out questions` against `hits/117 draws` for A/B/C, because the sign test uses only
  the ORDERING between arms. 16-09 must not normalize the two to a common denominator.
- **16-10 needs three things from this module that do not exist yet:** `main()` under a `__main__`
  guard, the four-process launcher, and the report writer. `resolve_forbid` is the seam to call once
  per process; `PROCESS_SPLIT_NOTE`, `SEQUENTIAL_QUESTIONS_JUSTIFICATION` and `NO_KV_CACHE_NOTE` are
  the three strings that travel together into the report; `PARITY_COLUMNS` is the SC2 column list.
- **One thing to watch:** `assert_arm_parity` is defined here but nothing calls it yet — 16-10 must
  call it after all four conditions return, or the parity claim ships as an unexecuted function.
  There is no structural guard forcing that call today, and adding one would require knowing the
  shape of 16-10's `main()`.

## Threat Flags

None. Every file this plan touched is new, CPU-only and non-networked; the one runtime surface it
adds (`resolve_forbid`, `embed_sequence`, `run_cosine_arm`) reads a committed tokenizer and a
locally-loaded model and writes nothing to disk.

## Self-Check: PASSED

Both created files exist on disk carrying every claimed symbol — `scripts/phase16_persistence.py`
(`CONDITION_ORDER`, `CONDITION_ORDER_PREREGISTRATION`, `CONDITION_ORDER_RATIONALE`,
`SEQUENTIAL_QUESTIONS_JUSTIFICATION`, `NO_KV_CACHE_NOTE`, `ArmConfig`, `SHARED_ARM_CONFIG`,
`forbid_digest`, `resolve_forbid`, `arm_config_record`, `PARITY_COLUMNS`, `assert_arm_parity`,
`load_fixture_items`, `PROCESS_SPLIT_NOTE`, `PER_QUESTION_KEYS`, `TIER_LABELS`, `all_items`,
`fairness_statements`, `normalize_by_split`, `assert_record_shape`, `run_condition`,
`COSINE_CHANCE_FLOOR`, `COSINE_POOL_SIZE`, `candidate_pool`, `embed_sequence`, `run_cosine_arm`) and
`tests/test_phase16_driver.py` (29 test functions, all exercised by the file run). All three task
commits resolve in `git log`: `d2d1294`, `35fc303`, `59dd473`. `git status --short` is empty and
`git diff --stat results/ pyproject.toml` is empty.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
