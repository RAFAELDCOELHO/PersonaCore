---
phase: 17-multi-persona-isolation-matrix
plan: 11
subsystem: iso-05-replication-mode-and-append-only-writer
tags: [iso-05, stat-02, d-13, d-15, d-16, d-19, th-17-36, th-17-37, th-17-38, th-17-46, mutation-proved, folded-correction]
requires:
  - scripts/phase17_personas.py (worst_pair, REPLICATION_SEEDS, PERSONA_SEEDS, PERSONAS,
    SIGN_UNIT — imported UNCHANGED; the file is uneditable and stayed at d549e0b)
  - scripts/phase17_isolation.py (17-04's assemble_matrix / base_texts_by_slot, 17-06's
    sweep_record_path / values_by_slot / assert_sweeps_ran_on_distinct_weights, 17-08's
    read_sweep_records / draws_per_question / REPLICATION_PENDING_LINE — extended ADDITIVELY)
  - scripts/phase16_persistence.py (report_proportion — imported unchanged)
  - scripts/_verdict.py (recorded_verdict — the ONE anchored `## Verdict` read)
provides:
  - run_replicate_mode / read_replicate_records / replicate_record_path / replication_payload /
    render_replication_addendum / append_addendum / _question_triples / _unordered_pairs
  - REPLICATION_RECORD_PATH / REPLICATION_ADDENDUM_HEADING / REPLICATION_MEASURED_LINE and the
    five ISO-05 framing constants
  - tests/test_phase17_stats.py — 24 tests (19 from 17-08, 5 new)
  - the corrected D-13 remediation pointer, at all three sites that carried it
affects:
  - plan 17-10 (RUNS `--replicate`; this plan produces no number)
  - results/phase17_isolation_report.md is still byte-untouched by this plan — the report is
    write-once and `--report` was NOT re-run, so the 9fcfc50 addendum is intact
tech-stack:
  added: []
  patterns:
    - the writer committed BEFORE it renders a number, with its ordering claim stated NARROWLY
      rather than inherited from the plan that established it
    - an append proved on the PRODUCED BYTES, at two independent layers (runtime + test)
    - a corrected diagnostic pointer that changes no verdict logic and no threshold
key-files:
  created: []
  modified:
    - scripts/phase17_isolation.py (1937 -> 2574 lines)
    - tests/test_phase17_stats.py (975 -> 1279 lines)
decisions:
  - the D-13 pointer was corrected at THREE sites, not the two named — the third
    (BASE_PRIOR_SEED_ANCHOR_NOTE) is the only one that actually renders into the report, so
    fixing the other two alone would have left the published defect regenerating
  - resolve_seed is NOT reused for replicate path resolution: it resolves an adapter path through
    teach_persona.arm_outputs, which imports torch, and this mode is CPU-only. sweep_record_path —
    the thing that actually has to agree — IS shared
  - git_sha is recorded per replicate cell and deliberately NOT proved single-valued: two of the
    six records are 17-09's, produced at an earlier commit BY CONSTRUCTION
metrics:
  duration: 25min
  tasks: 2
  files: 2
  completed: 2026-08-15
---

# Phase 17 Plan 11: The ISO-05 Replication Mode and the Append-Only Writer Summary

`--replicate` is a committed driver mode with an owning plan, in git history before it renders a
single replication number, and its append-only property is proved on the produced bytes by a test
that was watched failing — at two independent layers. **This plan produced no measurement.**
`git status --short results/` is empty and `results/phase17_isolation_report.md` is byte-identical
to what plan 17-09 and commit `9fcfc50` left (sha256 `6096aaf6bed891f6…`, verified before and
after).

## What Was Built

### Task 1 — the `--replicate` mode and the append-only writer (`6619677`)

`--replicate` joins the **REQUIRED mutually exclusive group** as a fourth action beside `--train`,
`--sweep` and `--report`. It scores recorded JSON and renders text — it trains nothing and generates
nothing — so admitting it does not weaken the "no process runs two sweeps" property the group
exists to hold. `main()`'s exhaustive dispatch gained the branch with no default.

`run_replicate_mode()` is pure CPU: no torch, no model, no tokenizer, no generation. The order is
the contract:

| # | step | what it forecloses |
|---|---|---|
| 1 | report exists AND `recorded_verdict` is non-empty | a replication appended to a result that was never recorded — a conclusion written before there is one to append it TO |
| 2 | refuse to clobber `results/phase17_replication.json` | recorded evidence overwritten; the path is named in the refusal |
| 3 | `read_sweep_records` + `assert_sweeps_ran_on_distinct_weights` | selection inputs read off sweeps that provably ran on different weights |
| 4 | `assemble_matrix` → six off-diagonal rates → **`personas.worst_pair(...)`** | a post-hoc pair choice; the rates come out of the RECORDS, never out of the rendered markdown |
| 5 | `read_replicate_records` (six proofs) | six records that are not six independent measurements of the same questions |
| 6 | `replication_payload` → write JSON → `append_addendum` | — |

**`worst_pair` is CALLED, not reimplemented**, and the file contains no `argmax`-shaped identifier
(asserted by the plan's own AST command, exit 0). `tie_break_decided` is computed and recorded
separately — `list(means.values()).count(max(means.values())) > 1` over the three unordered pairs —
so a tie-break outcome is published AS a tie-break outcome rather than inferred from the answer.

`read_replicate_records` proves, before anything is scored: all six paths exist (each named in its
own abort); six **distinct pids**; six **distinct live `lora_B` digests**; six **distinct artifact
file digests** (a separate claim — ISO-04's own two-claim structure, and neither implies the other);
`adapter_enabled` **True on all six**; and the **same `(slot, seed_index, question)` triple set as
the main sweeps**, because only an identical generation side makes seed variance readable.

**`git_sha` is recorded per cell and deliberately NOT proved single-valued.** Two of the six records
are the main sweeps from 17-09 and the other four are produced later, at a later commit, *by
construction*. A one-SHA proof here would refuse every honest run. The test fixture sets the
replicates to a different SHA so that a future tightening goes red.

`append_addendum` is textual and surgical rather than a re-render, and the reason is load-bearing:
**`render_report` rewrites the WHOLE file**, so re-running it would destroy the recorded verdict,
17-09's `## Scope Addendum`, and the dated D-13 addendum at `9fcfc50` along with it. The prefix
before the placeholder is carried through byte-identically, `REPLICATION_PENDING_LINE` becomes
`REPLICATION_MEASURED_LINE`, and the addendum is concatenated at the end. It `_prove`s the
placeholder occurs **exactly once** and names the count found, `_prove`s the recorded verdict is
unchanged, and `_prove`s the produced bytes still start with the original prefix. **There is no
override flag** (`grep -n "force"` shows four occurrences, all pre-existing at lines 22, 1169, 1179
and 1501 — none inside `run_replicate_mode` or `append_addendum`).

**No p value, no correction step, no verdict, at any depth** (D-16 / ISO-05 / STAT-06). The output
is `min` / `max` / `median` of the selected pair's **mean off-diagonal rate** — the same quantity
`worst_pair` maximises, so the spread is reported on the axis the selection was made on rather than
on a second one invented for the addendum. Every per-seed rate travels through `report_proportion`,
so no number appears without both denominators and its bound, and the rule of three travels with
every zero.

### Task 2 — the tests (`726488d`)

Five new tests, **24 in the file**, **1.78 s**, CPU-only, all on synthetic records and a synthetic
report in `tmp_path`.

| test | what it pins |
|---|---|
| `test_addendum_writer_is_append_only` | prefix byte-identical, exactly ONE line differs above the addendum, everything past it a pure insertion, `recorded_verdict` unchanged — four claims, because each admits a different way a rewrite could pass the others |
| `test_addendum_refuses_an_ambiguous_placeholder` | zero and two both `SystemExit`, the message names the count, and the file is byte-identical after (a refusal that has already written is not a refusal) |
| `test_replication_output_is_descriptive_only` | no `p =` / `alpha` / `rejected` / bare zero percentage in the addendum; the literal "descriptive" and D-15's "never a ranking" present; no `p_value` / `alpha` / `rejected` key at ANY depth in the payload; and the written payload's key set equals the returned one |
| `test_worst_pair_is_read_from_the_records_not_the_report` | structural, not textual: `worst_pair`'s argument is traced to its SINGLE assignment and that assignment must index the matrix; no regex call anywhere in the function |
| `test_replicate_seeds_come_from_the_preregistration` | the seeds are `REPLICATION_SEEDS`; the first resolves to the UNSCOPED record (k=3 counts the original, reused not re-run); a missing record aborts naming its path with nothing written |

## The Guards, Watched Failing

`scripts/phase17_isolation.py` sha256 is
**`a0c2392dc8f6505a04b115fedb90f4cd8118f6e445573fe9f6b4ed6fa7ede90e`** before and after every probe.

| probe | observed |
|---|---|
| the append helper made to rewrite instead of append | `SystemExit: [phase17_isolation] PROOF FAILED: appending to … changed its recorded `## Verdict` section` — the **RUNTIME** guard fired first |
| the same mutation, with BOTH runtime `_prove`s also removed | `AssertionError: the bytes before the placeholder line changed` — the test's own byte-identical-prefix assertion, which is the one the plan asks for |
| a `p_value` key added to the payload | `AssertionError: the replication payload carries a hypothesis-test key: [… 'p_value' …]` |

The first two rows are worth keeping together: a rewrite is caught at **two independent layers**,
and the runtime one fires *earlier* than the test's assertion. That was discovered by running the
probe, not designed for — the mutation deleted the `## Verdict` section outright, so
`recorded_verdict(updated)` went to `None` before the prefix comparison was reached. The second
probe was run specifically to confirm the test's own assertion is not dead code behind it.

## The Folded Correction — the D-13 Remediation Pointer

The user directed one additional scoped change into this pass: the misdirecting D-13 pointer, which
sent a reader to *"investigate this sweep before trusting the derivation on the other six slots"*.
That pointer is factually wrong. The investigation was performed in 17-09 and the cause is
**UPSTREAM of the sweep**: `phase14_factset.BASE_PRIOR_SEEDS` was measured under **greedy decoding
from a bare `<|system|>` prompt** (`scripts/phase14_factset.py:295-296` records it verbatim), a
different decoding regime from the sampled sweeps that get scored — corroborated independently by
the ISO-01 pre-flight producing `rose` **zero times across 416 completions** on the un-adapted base.

**It was corrected at three sites, not the two named in the direction.** The two named were
`base_prior_anchor`'s docstring (~1373) and `render_report`'s per-slot verdict cell (~1658). The
third — `BASE_PRIOR_SEED_ANCHOR_NOTE` — carried the identical sentence and is **the only one of the
three that actually renders into the report**. Fixing the two named sites alone would have left the
published defect regenerating on the next `--report` run, which is the exact failure the direction
exists to close. All three now point at the seed list's provenance.

**What did NOT change, checked rather than asserted:**

- `base_prior_anchor`'s `reproduced` value is still a plain `any`-over-seeds `contains_value` match.
  `git diff` over the function body shows **docstring lines only** — no expression changed.
- `render_report`'s branch is still `"yes" if entry["reproduced"] else "**NO — …**"`. **A miss still
  renders as a miss**, in bold, with `NO` first. No threshold was softened, no result re-priced.
- No count from this run entered the generator constants. The constants carry the causal pointer and
  the ISO-01 corroboration (both facts about committed source and a previously published artifact);
  the run-specific counts stay where they already are, in the `9fcfc50` addendum.
- **`results/phase17_isolation_report.md` was not regenerated and not edited.** sha256
  `6096aaf6bed891f6d7229b26281fd1536f57c95424480dd91a4ca9a1dbda242a` before this plan's first commit
  and after its last; `git status --short results/` empty; `grep -c "Addendum — 2026-08-15"` = **1**.
  The report is write-once (`assert_isolation_report_not_clobbered`) and `--report` was never
  invoked, so the corrected text will first appear in an artifact only if the report is ever
  regenerated in a reviewed commit.

One consistency fix went in alongside it: `REPLICATION_MEASURED_LINE` names the appended section
**without** its `## ` prefix. A heading literal repeated in prose is the CR-02 defect
(`scripts/_verdict.py:6-14`) this repository already paid for once, and the first draft of that line
reintroduced it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `--replicate --seed` would be silently ignored**

- **Found during:** Task 1, wiring `main()`'s dispatch.
- **Issue:** `--seed` sits outside the mutually exclusive group by design (it modifies a mode rather
  than being one), so `--replicate --seed 1437` would parse cleanly and the seed would be dropped on
  the floor. The replication reads **all** of the selected pair's `REPLICATION_SEEDS` by
  construction, so an operator passing a seed there believes they scoped the run — and a silently
  ignored flag lets them keep believing it while every seed is read anyway.
- **Fix:** `main()`'s `--replicate` branch `_prove`s `args.seed is None`, with a message naming both
  wrong readings (ignored, or a k=3 narrowed to k=1 without saying so in the artifact).
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `6619677`

**2. [Rule 2 - Missing critical functionality] the six replicate artifact digests were unproved**

- **Found during:** Task 1, writing `read_replicate_records`.
- **Issue:** the plan mandates pairwise-distinct `lora_b_sha256`. It does not mandate the artifact
  file digests. `assert_sweeps_ran_on_distinct_weights` asserts **both** for the main sweeps and
  records why in its own docstring — *"a file digest proves which file was read, a live digest
  proves which weights the model ended up holding"*, and neither implies the other. Asserting only
  one here would leave the weaker of two same-size options in the replication path.
- **Fix:** both are proved, in one loop with `pid`, each with its own message.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `6619677`

**3. [Rule 3 - Blocking] `resolve_seed` cannot be reused — it drags torch into a CPU-only mode**

- **Found during:** Task 1. The plan's step 3 says to read the seed-scoped records via
  `sweep_record_path(persona, seed)`, and `resolve_seed` already owns the
  `seed != PERSONA_SEEDS[persona]` scoping rule. Reusing it would have been the shorter diff — but
  it resolves an adapter path through `teach_persona.arm_outputs`, and `scripts/teach_persona.py:65`
  imports torch at module scope. `run_replicate_mode` is CPU-only by construction.
- **Fix:** `replicate_record_path(persona, seed)` re-states the two-line scoping rule and `_prove`s
  the seed against `REPLICATION_SEEDS`, while **sharing `sweep_record_path`** — the thing that
  actually has to agree with the sweep writer. The docstring records why the larger reuse was
  rejected so it is not attempted again.
- **Files modified:** `scripts/phase17_isolation.py`
- **Commit:** `6619677`

### Interpretations recorded

**Only the two rows of the selected pair are read, but `assemble_matrix` takes four records.** Each
seed index is scored on `[first@seed, second@seed, third(main), base(main)]`. The un-selected
persona is present only to satisfy the committed four-record contract and its cells are never read;
it cannot influence the two that are, because cell `(i, j)` counts what **row i's own completions**
contained and depends on no other row's record. The base column and the third row come from the MAIN
sweeps deliberately: D-13 derives the base prior from ONE adapter-off column under one set of
questions and seeds, so a per-seed base column would be four controls where the design has exactly
one — the same reason `resolve_seed` refuses `--sweep base --seed`.

**The min/max/median are rendered as bare six-decimal floats and that is not a STAT-02 violation.** A
mean of two proportions has no single denominator to attach, and inventing one would be worse than
omitting it. Each of the six underlying cells is published through `report_proportion` with both
denominators and its bound in the table directly above, and the summary sentence says so. The six
selection-input rates match the committed writer's existing `{:.6f}` rendering in
`§Replication (ISO-05)`, which they are the same six numbers as.

**No aggregate over the matrix was computed anywhere, including in this SUMMARY** (STAT-06).

## Verification

Every number below came from a command run in this session.

| Check | Result |
|---|---|
| `.venv/bin/pytest -q tests/test_phase17_stats.py -x` | **24 passed** in 1.78s (>= 21 required; was 19) |
| `.venv/bin/pytest -q tests/test_phase17_stats.py tests/test_phase17_scoring.py -x` | **42 passed** |
| `.venv/bin/pytest -q tests/test_phase17_stats.py -k "replication or nine_cell or addendum" -x` | **5 passed**, 19 deselected |
| `.venv/bin/pytest -q` (full suite) | **650 passed, 1 skipped** in 127.56s — baseline 645/1 + 5 new; floor 579 |
| `--help` shows four actions in one required group | `(--train … \| --sweep … \| --report \| --replicate)` |
| `--report --replicate` | **exit 2**, `argument --replicate: not allowed with argument --report` |
| `worst_pair` CALLED / no `argmax` identifier (plan's AST command) | **exit 0** |
| `re.search(r'\b0(\.0+)?%', source)` (STAT-02) | **None** |
| `grep -n "force"` inside `run_replicate_mode` / `append_addendum` | **0** (4 pre-existing hits at lines 22, 1169, 1179, 1501) |
| `git status --short results/` | **empty** — this plan writes no artifact |
| `results/phase17_isolation_report.md` sha256, before and after | **`6096aaf6bed891f6…`**, identical |
| `grep -c "Addendum — 2026-08-15"` (the `9fcfc50` addendum) | **1** — present and unduplicated |
| `git diff --stat -- results/` | **empty** |
| `.venv/bin/ruff check .` + `format --check .` (CI version **0.15.16**) | **clean, 155 files** |
| `make lint` | **red — pre-existing DEF-17-01, count unchanged at 9** |
| **STAT-05 `checked`** | **11** (1 prereg commit `d549e0b` x 11 tracked `results/phase17_*` paths), **0 untracked** — unchanged from 17-09 |
| `git log -- scripts/phase17_personas.py` | **`d549e0b` only** — the uneditable pre-registration is byte-untouched |
| `git diff -- pyproject.toml` (STAT-04) | **empty** — zero packages installed |
| `git diff --diff-filter=D` per commit | **empty** — no deletions in either |
| `git status --short` | empty after each commit |
| `scripts/phase17_persona_gate.py` re-run | **never invoked** — the armed clobber guard was not touched |

**Smoke-run, before either commit:** the whole mode was exercised end to end on a synthetic
`tmp` fixture (four main records + four seed-scoped ones, `--report` then `--replicate`). It
selected `persona_a` / `persona_b` at the all-zero three-way tie with `tie_break_decided: True`,
wrote six cells, produced `min`/`max`/`median` all `0.0`, and left the report's prefix
byte-identical with `recorded_verdict` unchanged. **That is a synthetic fixture and none of those
numbers is a Phase 17 result.**

## Deferred Issues

`make lint` remains red from **DEF-17-01** (pre-existing to this phase, recorded at 17-01):
`Makefile:16` runs bare `ruff`, which resolves on this box to a pyenv shim holding ruff 0.1.15
against the project's `ruff~=0.15` pin. The count is **unchanged at 9** — `tests/test_phase17_stats.py`
was already in that list and `scripts/phase17_isolation.py` is not. `.venv/bin/ruff` 0.15.16, the
version `.github/workflows/ci.yml` installs, is clean on all 155 files. Nothing new deferred.

## Known Stubs

None in this plan's own code — every function committed here is complete and exercised by a test.

**One inherited placeholder is still live by design:** `results/phase17_isolation_report.md` still
carries its single `ISO-05 replication result: not yet measured.` line. That is correct at this
point in the phase: this plan ships the writer, **plan 17-10 runs it**, and the line is what makes
the absence visible. `test_all_fail_branch` still asserts the count is 1 in both gate outcomes and
`append_addendum` refuses any count other than 1.

## Requirements

**Nothing marked.** The plan's frontmatter lists `[ISO-05, STAT-02]`.

- **ISO-05** reads *"the worst-colliding pair **is replicated** across seeds, so seed variance is
  not confounded"*. **Nothing has been replicated.** This plan ships the rendering path and produces
  no number; the six replicate sweeps do not exist and plan 17-10 owns the run. Marking it Complete
  here would be flatly false in the one artifact a reader consults to see what is done — this is the
  over-claim pattern 17-01 recorded and 17-03, 17-04 and 17-08 each avoided, applied a fifth time.
  It stays `[ ]` / Pending.
- **STAT-02** is **already Complete** from Phase 16 (`.planning/REQUIREMENTS.md:29,184`) and is
  untouched. This plan honours it — every per-seed rate renders through `report_proportion` and the
  source regex is clean — rather than re-claiming it.

`requirements mark-complete` was **not run**.

## Handover Notes

1. **17-10 runs `python scripts/phase17_isolation.py --replicate`** after the four extra sweeps
   exist. It writes `results/phase17_replication.json` and APPENDS to the report. Both are
   write-once: the payload refuses to clobber, and the addendum refuses any placeholder count other
   than exactly 1 — so a second `--replicate` run on the same report aborts naming the count `0`.
2. **The mode requires the four MAIN records plus the four seed-scoped ones on disk**, and re-runs
   `assert_sweeps_ran_on_distinct_weights` over the main four. The first seed of each persona is the
   UNSCOPED record — reused, never re-run.
3. **`git_sha` will legitimately differ between the first seed's cell and the rest.** Do not "fix"
   that by proving it single-valued; the addendum says so in its own text and
   `read_replicate_records`'s docstring records why.
4. **Never run `--report` again to pick up the corrected D-13 pointer.** `render_report` rewrites the
   whole file and would destroy the recorded verdict, 17-09's `## Scope Addendum` and the `9fcfc50`
   D-13 addendum. The corrected generator text is for a future regeneration only, and the published
   artifact already carries the correction as a dated addendum.
5. **The published report still has ONE `not yet measured` line.** `append_addendum` is the only
   thing that may replace it. Nothing in this plan touched it.
6. **The three Phase 17 adapters remain NOT shippable demo substrate** (17-09 handover 4,
   `replay_ratio=0.0`, +211% to +241% masked dialogue-val PPL). The replicate adapters 17-10 trains
   will share that property.
7. **`scripts/phase17_personas.py` is still at `d549e0b` and still uneditable.** STAT-05 covers 11
   paths with zero untracked.

## Threat Flags

None. No new network endpoint, auth path or schema change at a trust boundary. The one new
file-access pattern — reading six recorded JSON sweep records, writing one JSON payload and
appending to one markdown file — is `json.loads` over files this repository wrote, guarded on the
write side by a clobber refusal and a placeholder-count refusal.

Register dispositions from this plan's own `<threat_model>`:

- **TH-17-46** (a public artifact produced by an uncommitted ad-hoc script) — **mitigated**:
  `--replicate` is committed in Wave 5, before plan 17-10 runs it. `results/phase17_replication.json`
  and the addendum have exactly one writer and it is in git history first.
- **TH-17-37** (the verdict rewritten under cover of an addendum) — **mitigated, two independent
  layers, both watched failing**: `append_addendum`'s runtime `_prove`s (placeholder count, verdict
  unchanged, prefix preserved on the produced bytes) and `test_addendum_writer_is_append_only`'s
  four assertions. No override flag.
- **TH-17-36** (a post-hoc "worst pair" choice) — **mitigated**: `worst_pair` was committed in Wave 1
  with its tie-break and is CALLED here on rates read from the sweep RECORDS.
  `test_worst_pair_is_read_from_the_records_not_the_report` traces the argument to its single
  matrix-indexing assignment, and `tie_break_decided` is recorded explicitly.
- **TH-17-38** (a descriptive replication reported as a test) — **mitigated**: the call-site
  identifier ban stays green, and both the addendum and the payload are asserted free of
  `p =` / `alpha` / `rejected`, on the rendered text AND at every depth of the JSON — the p_value
  probe was watched failing.
- **TH-17-SC** — holds. **Zero packages installed**; `git diff -- pyproject.toml` empty.

## Self-Check: PASSED

Files:

- FOUND: `/Users/juliorcoelho/PersonaCore/scripts/phase17_isolation.py` (2574 lines, was 1937)
- FOUND: `/Users/juliorcoelho/PersonaCore/tests/test_phase17_stats.py` (1279 lines, was 975)
- FOUND: every symbol this plan claims — `run_replicate_mode`, `append_addendum`,
  `render_replication_addendum`, `replication_payload`, `read_replicate_records`,
  `replicate_record_path`, `_question_triples`, `_unordered_pairs`
- FOUND: all five test functions — `test_addendum_writer_is_append_only`,
  `test_addendum_refuses_an_ambiguous_placeholder`, `test_replication_output_is_descriptive_only`,
  `test_worst_pair_is_read_from_the_records_not_the_report`,
  `test_replicate_seeds_come_from_the_preregistration`
- UNCHANGED (verified, not assumed): `/Users/juliorcoelho/PersonaCore/results/phase17_isolation_report.md`

Commits:

- FOUND: `6619677` feat(17-11): add the --replicate mode and its append-only addendum writer
- FOUND: `726488d` test(17-11): pin the append-only property and the descriptive-only contract
