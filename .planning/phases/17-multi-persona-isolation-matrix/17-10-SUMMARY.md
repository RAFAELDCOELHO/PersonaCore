---
phase: 17-multi-persona-isolation-matrix
plan: 10
subsystem: iso-05-replication-run-and-published-addendum
tags: [iso-05, stat-02, stat-05, stat-06, d-13, d-15, d-16, d-19, th-17-36, th-17-37, th-17-38, th-17-39, th-17-46, tie-break-outcome, descriptive-only, gate-cleared-unchanged]
requires:
  - scripts/phase17_personas.py (worst_pair, REPLICATION_SEEDS, PERSONA_SEEDS — CALLED,
    byte-untouched, still at d549e0b)
  - scripts/phase17_isolation.py (17-11's --replicate / read_replicate_records /
    replication_payload / render_replication_addendum / append_addendum; 17-04's --train and
    17-06's --sweep — all run UNMODIFIED, no code written this plan)
  - results/phase17_sweep_{persona_a,persona_b,persona_c,base}.json (17-09's four main records —
    the selection inputs and the single reused base column)
  - results/phase17_isolation_report.md (the recorded verdict --replicate refuses to run without)
  - checkpoints/phase17_persona_{a,b}_adapter.pt (17-09's first-seed adapters, REUSED)
provides:
  - results/phase17_replication.json (six per-seed cells with per-cell provenance, min/max/median)
  - results/phase17_isolation_report.md §Replication Addendum (ISO-05) — appended, zero deletions
  - results/phase17_replication_run.log + four run.csv (the detached run's own record)
  - results/phase17_sweep_persona_{a_seed1437,a_seed1537,b_seed1438,b_seed1538}.json
  - checkpoints/phase17_persona_{a_seed1437,a_seed1537,b_seed1438,b_seed1538}_adapter.pt
  - tests/test_phase17_stats.py::test_report_addendum_is_additive (25 tests in the file)
affects:
  - ISO-05 marked Complete — the LAST claimant of four (17-01, 17-08, 17-10, 17-11)
  - Phase 17 is now 11 of 11 plans complete
tech-stack:
  added: []
  patterns:
    - a plan that writes NO code and produces a public artifact only through modes committed in
      earlier waves — git diff -- scripts/ empty across all three tasks
    - a detached run whose success is read from an on-disk exit-code sentinel, never from log text
    - the same append-only property proved twice — synthetically on the writer (17-11) and on the
      PUBLISHED bytes (here)
key-files:
  created:
    - results/phase17_replication.json
    - results/phase17_replication_run.log
    - results/phase17_sweep_persona_a_seed1437.json
    - results/phase17_sweep_persona_a_seed1537.json
    - results/phase17_sweep_persona_b_seed1438.json
    - results/phase17_sweep_persona_b_seed1538.json
    - results/phase17_persona_{a_seed1437,a_seed1537,b_seed1438,b_seed1538}/run.csv
  modified:
    - results/phase17_isolation_report.md (APPENDED — 62 insertions / 1 deletion)
    - tests/test_phase17_stats.py (1279 -> 1379 lines, 24 -> 25 tests)
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - .planning/REQUIREMENTS.md
decisions:
  - the pair was learned from the committed mode's own abort, not from the report's prose; the
    six rates and tie_break_decided are read back out of the payload the mode wrote
  - the four run.csv files and the four seed-scoped sweep records are COMMITTED, matching what
    17-09 committed for the main arms — the six cells are unverifiable without them
  - the pre-append revision in the new test is DERIVED (newest committed revision still carrying
    the placeholder), never pinned to a hash, so later commits touching the report cannot stale it
metrics:
  duration: 40min
  tasks: 3
  files: 15
  completed: 2026-08-15
---

# Phase 17 Plan 10: The ISO-05 Replication Run Summary

The worst-colliding pair was replicated at k=3 seeds per persona and published **descriptively**:
**min `0.000000` / max `0.000000` / median `0.000000`** of the pair's mean off-diagonal rate across
the three seed indices, with all six underlying cells at **`0/104` questions (`0/936` draws)**. It is
an **addendum**: 62 insertions / 1 deletion against `9fcfc50`, and that one deletion is the
placeholder line becoming a pointer.

**This plan wrote no code.** `git diff -- scripts/` is empty across all three tasks; every artifact
came out of `--train`, `--sweep` and `--replicate`, committed in Waves 3-5.

## The Selection — a Tie-Break Outcome, Not a Finding

`worst_pair` was **CALLED** by the committed `--replicate` mode. Its six ordered inputs, read out of
the sweep **RECORDS** (never out of the rendered markdown), are in `results/phase17_replication.json`:

| ordered off-diagonal cell | question-unit rate | cell |
|---|---|---|
| `(persona_a, persona_b)` | `0.000000` | 0/104 questions |
| `(persona_a, persona_c)` | `0.000000` | 0/104 questions |
| `(persona_b, persona_a)` | `0.000000` | 0/104 questions |
| `(persona_b, persona_c)` | `0.000000` | 0/104 questions |
| `(persona_c, persona_a)` | `0.000000` | 0/104 questions |
| `(persona_c, persona_b)` | `0.000000` | 0/104 questions |

All three unordered pair means are `0.0`. **`tie_break_decided: true`** — recorded by the mode as a
separate field rather than inferred from the answer. The returned pair is
**`persona_a` / `persona_b`**, which is D-19's pre-registered lowest-index tie-break resolving a
**three-way tie**. That is the phase's success case, and it is exactly the situation the committed
tie-break exists for: **this is a tie-break result and says nothing about personas A and B.**

The pair was learned mechanically, not from prose: the first `--replicate` invocation aborted with
`…/phase17_sweep_persona_a_seed1437.json is missing`, which names the selection before any replicate
record exists. `worst_pair` was committed in Wave 1 at `d549e0b`, before the matrix was read.

## The Numbers

Six cells, 2 personas x 3 seeds. Every rate through `report_proportion`, so no number appears without
both denominators and its bound, and the rule of three travels with every zero:

| persona | seed | seed idx | cell | rate |
|---|---|---|---|---|
| `persona_a` | 1337 | 0 | `(persona_a, persona_b)` | 0/104 questions (95% Wilson UB 0.025355; rule-of-three UB 0.028846; 936 draws) |
| `persona_b` | 1338 | 0 | `(persona_b, persona_a)` | 0/104 questions (same bounds) |
| `persona_a` | 1437 | 1 | `(persona_a, persona_b)` | 0/104 questions (same bounds) |
| `persona_b` | 1438 | 1 | `(persona_b, persona_a)` | 0/104 questions (same bounds) |
| `persona_a` | 1537 | 2 | `(persona_a, persona_b)` | 0/104 questions (same bounds) |
| `persona_b` | 1538 | 2 | `(persona_b, persona_a)` | 0/104 questions (same bounds) |

Pair mean off-diagonal rate by seed index: `0.0` / `0.0` / `0.0` →
**min `0.000000`, max `0.000000`, median `0.000000`**.

**DESCRIPTIVE ONLY (D-16 / ISO-05 / STAT-06).** No p value, no alpha, no `rejected`, no Holm row and
no sign test — scanned at **every depth** of the payload and in the published addendum block, both
clean. **`gate_cleared` is closed at the six pre-registered `HOLM_FAMILY_CELLS` and structurally
cannot admit a replication row.** This number does not clear the gate, does not weaken it and does
not re-price it; the gate cleared in 17-09 and is untouched here. Per **D-15** the three diagonals
remain three separate anchors and never a ranking — this replication is what makes seed variance
readable, not what licenses an ordering.

## The Run

**Detached, and verified from disk rather than from log text.**

| | training (Task 1) | sweeps (Task 2) |
|---|---|---|
| wrapper pid | **55096**, **ppid 1** | **58328**, **ppid 1** |
| exit code | **0**, read from the on-disk sentinel | **0**, read from the on-disk sentinel |
| child pids | 55216 / 55890 / 55950 / 56009 | 58442 / 60031 / 60163 / 60297 |
| wall | 80 s / 81 s / 79 s / 80 s = **5.3 min** (est. ~5 min) | 186 / 189 / 194 / 191 s = **12.7 min** |
| device | MPS fp32, `torch=2.7.1` | MPS fp32 |

**Sweep wall clock deviates from the ~18 min estimate by −29.6% and that is stated rather than
absorbed** (the criterion asks for anything past 15%). 17-09's four sweeps ran 14.9 min against the
same band; this run is four adapter sweeps with no ~5.3-min base sweep among them, which accounts for
the difference. Both wrappers `tee`'d to `results/phase17_replication_run.log`, committed.

Four **additional** adapters trained — `persona_a@1437`, `persona_a@1537`, `persona_b@1438`,
`persona_b@1538`. The **first** seed of each persona (`1337`, `1338`) is 17-09's adapter, **reused,
never retrained**: k=3 counts the original. Each provenance line reads its own seed from
`REPLICATION_SEEDS`, at seed-scoped arm names (`persona_a_seed1437`) so `refuse_if_exists` protects
each run independently. `resolve_seed` never fired.

**No per-seed base sweep was run.** `resolve_seed` refuses `--sweep base --seed`, and the refusal is
the design: D-13 derives base-prior from ONE adapter-off column under one set of questions and seeds,
so the 17-09 base record is reused. Four controls where the design has one would be a different
experiment.

### TH-17-39 — six provably distinct adapters, checked BEFORE 12.7 min of sweeps were paid for

| key | live `lora_B` sha256 | adapter file sha256 |
|---|---|---|
| `persona_a` @ 1337 | `ab0a8d678521d078…` | `b420c22ac0d576a1…` |
| `persona_a` @ 1437 | `346a3038b26f11a7…` | `4a3527ed6430a638…` |
| `persona_a` @ 1537 | `8411c2de8ac7b0be…` | `a9da13dee7c33db5…` |
| `persona_b` @ 1338 | `5a35d2056f9938e7…` | `7d6dde9eef0bbbc6…` |
| `persona_b` @ 1438 | `23a92b0d453ebe37…` | `3581358a5e11dd30…` |
| `persona_b` @ 1538 | `82f5ed5f01f1e38c…` | `e2f4f802c4fac80d…` |

**6 distinct `lora_B` digests, 6 distinct file digests**, and across **all 15 pairs** the identical-
tensor count is **0 of 36** (max abs difference 0.0518-0.0593). The seed reached the init draw. The
two 17-09 rows' digests, computed here off the artifact files, equal the live digests 17-09 recorded
from its own sweeps — an independent corroboration, not a restatement.

The rendered payload carries **6 distinct pids** and **2 distinct `git_sha`** values
(`b6b2fed…` for the two reused 17-09 records, `f2c0272…` for the four new). That is expected **by
construction** and is deliberately not proved single-valued (17-11 handover 3).

## The Append — Zero Deletions Above It

Verified on the real artifact, not assumed:

| check | result |
|---|---|
| `PRE` (commit before the append) | **`9fcfc5015f8b2078eea4ff6c8b1e913824fbfe88`** |
| `git diff $PRE -- …report.md \| grep -c "^-"` | **2** — the diff header, plus the one replaced placeholder line |
| `git diff --stat` vs `PRE` | **62 insertions, 1 deletion** |
| placeholder byte offset | **15,306** bytes (15,243 characters — the file has multi-byte em-dashes) |
| bytes above it, pre vs post | **byte-identical** |
| lines differing in the overlap | **exactly 1**: `**ISO-05 replication result: not yet measured.**` → the pointer line |
| `_verdict.recorded_verdict` | **identical**, 1,402 chars before and after; first line still ``**`gate_cleared` returns `True`**`` |
| `grep -c "Addendum — 2026-08-15"` (the `9fcfc50` D-13 block) | **1** — present, unduplicated, byte-intact |
| report sha256 | `6096aaf6…` → `5090d2a7…` (the append, and nothing else) |
| `re.search(r"\b0(\.0+)?%")` over the WHOLE report | **`None`** (STAT-02) |
| `p =` / `alpha` / `rejected` / `reject` in the addendum block | **0 / 0 / 0 / 0** |
| "never a ranking" present in the block (D-15) | **True**; "descriptive" appears 4x in the report |

**`--report` was never invoked.** `render_report` rewrites the whole file and would have destroyed
`9fcfc50`, 17-09's `## Scope Addendum` and the recorded verdict together.
`scripts/phase17_persona_gate.py` was never invoked either — its armed clobber guard was not touched.

## The Test, Watched Failing

`test_report_addendum_is_additive` is the **real-artifact twin** of 17-11's synthetic
`test_addendum_writer_is_append_only`. The distinction is load-bearing: a writer can be append-only
and still have been run against a file some other hand already rewrote, so the two prove different
things. The pre-append revision is **derived, never pinned to a hash** — the newest committed
revision still carrying `REPLICATION_PENDING_LINE` is by definition the one before the append, and
that survives any number of later commits to the file.

| probe | observed |
|---|---|
| one byte changed ABOVE the placeholder (`## Verdict` → `## Verdict `) | `AssertionError: the published results/phase17_isolation_report.md no longer starts with its pre-append bytes…` |
| `the replication rejected the null.` appended to the published block | `AssertionError: the published ISO-05 addendum contains 'rejected'. ISO-05 is descriptive only (D-16)…` |

The report was restored **byte-identically** after each probe (sha256
`5090d2a77ef8c7c90aa87ba2e81115127a6cfa507bddf4c53f7fad3e402de9eb` both times, `git status --short
results/` empty), restored from a byte-copy rather than by any destructive git command.

## Deviations from Plan

**None affecting the plan's substance.** Two mechanical notes, neither a code change:

1. **The plan says `--replicate` "prints its inputs and its selection" before it needs a replicate
   record.** It does not print them — `run_replicate_mode` has no output before the payload write.
   The selection is nonetheless learned mechanically: the abort names
   `phase17_sweep_persona_a_seed1437.json`, which identifies the pair, and the six rates and
   `tie_break_decided` are read back out of the payload the mode itself wrote. No selection
   arithmetic was written anywhere in this plan; `worst_pair` was called, never re-derived.
2. **`gsd-sdk query state.record-metric` and `state.add-decision` both rejected positional
   arguments** (`add-decision` needs `--phase` / `--summary`; `record-metric` errored on every form
   tried). The decisions went in through the corrected flags; the metrics row was appended directly.
   `state.update-progress` reported "Progress field not found" and `advance-plan` overwrote
   `stopped_at` / `last_activity` with stale text, so the frontmatter was corrected by hand. Tooling
   friction, not a project finding.

### Interpretations recorded

**The four replicate adapters inherit 17-09's `replay_ratio=0.0` collateral collapse** and are
equally **NOT shippable demo substrate**. `run_one_persona_training` still calls `train_arm` at the
committed default, exactly as 17-09 recorded. Nothing was "fixed" here — that would put code after
the report it obeys.

**No aggregate over the matrix was computed anywhere, including in this SUMMARY** (STAT-06). Every
number above carries its own denominator, except the min/max/median, which are means of two
proportions with no single denominator to attach (17-11's recorded reading; each underlying cell is
published with both denominators in the table directly above it).

## Verification

Every number below came from a command run in this session.

| Check | Result |
|---|---|
| `.venv/bin/pytest -q` (full suite) | **651 passed, 1 skipped** in 126.97 s — was 650/1, +1 new test; floor 579 |
| `.venv/bin/pytest -q tests/test_phase17_stats.py` | **25 passed** in 1.89 s (was 24; >= 22 required) |
| `-k "replication or nine_cell or addendum"` | **6 passed**, 19 deselected |
| `.venv/bin/pytest -q tests/test_phase16_prereg.py` | **3 passed** |
| `git diff -- scripts/` (Tasks 1, 2 and 3) | **empty** |
| `git diff -- tests/` (Tasks 1 and 2) | **empty** |
| `git diff -- pyproject.toml` (STAT-04) | **empty** — zero packages installed |
| **STAT-05 `checked`** | **21** (1 prereg commit `d549e0b` x 21 tracked `results/phase17_*` paths), **0 untracked** — was 11 |
| `git log -- scripts/phase17_personas.py` | **`d549e0b` only** — still byte-untouched and uneditable |
| replication payload: distinct `pid` / `lora_b_sha256` / `adapter_file_sha256` | **6 / 6 / 6** |
| payload banned-key scan (`p_value`, `alpha`, `rejected`, `holm`, `sign_test`) at every depth | **0 hits** |
| `.venv/bin/ruff check .` + `format --check .` (CI version **0.15.16**) | **clean, 155 files** |
| `make lint` | **red — pre-existing DEF-17-01, count unchanged at 9** |
| `git status --short` | **empty** after each commit |
| `git diff --diff-filter=D` per commit | **empty** — no deletions in any of the three |
| detached sleep protection | `caffeinate -ims` pid **58309**, ppid **1** — untouched, not restarted, not killed |

## Deferred Issues

`make lint` remains red from **DEF-17-01** (pre-existing, recorded at 17-01): `Makefile:16` runs bare
`ruff`, which resolves on this box to a pyenv shim holding ruff 0.1.15 against the project's
`ruff~=0.15` pin. The count is **unchanged at 9** — `tests/test_phase17_stats.py` was already on that
list before this plan touched it. `.venv/bin/ruff` 0.15.16, the version `.github/workflows/ci.yml`
installs, is clean on all 155 files. Nothing new deferred.

## Known Stubs

**None, and the phase's one long-standing placeholder is now retired.**
`results/phase17_isolation_report.md` no longer carries `ISO-05 replication result: not yet
measured.` — `append_addendum` replaced it with a pointer at the appended section, which is the one
line that plan was ever permitted to change. Re-running `--replicate` now aborts naming the count
`0`, which is the intended write-once behaviour.

## Requirements

**ISO-05 marked Complete — here and only here.** The claimant set was re-derived from every plan's
frontmatter in the phase: **17-01, 17-08, 17-10, 17-11**. 17-01 recorded and **reverted its own
over-claim** and named the remaining claimants; 17-08 declined ("both require a measured artifact
that does not exist"); 17-11 declined ("nothing has been replicated"). This plan is the last
claimant and it produced the number, so the requirement now reads true:
*"the worst-colliding pair is replicated across seeds, so seed variance is not confounded"* — six
independent measurements across three seed indices, published with bounds.

**STAT-02 and STAT-06 were already Complete** (Phase 16) and are untouched. This plan honours both —
every rate through `report_proportion`, no aggregate anywhere — rather than re-claiming them.
`requirements mark-complete ISO-05` reports `not_found: []`, `total: 1`.

## Handover Notes

1. **`results/phase17_replication.json` and the addendum are both write-once.** The payload refuses
   to clobber; `append_addendum` refuses any placeholder count other than exactly 1, so a second
   `--replicate` aborts naming the count `0`. Neither has a force flag.
2. **Never run `--report`.** `render_report` rewrites the whole file and would destroy the recorded
   verdict, 17-09's `## Scope Addendum`, the `9fcfc50` D-13 addendum **and now this ISO-05 addendum**
   together. The corrected D-13 generator text from 17-11 is still for a future reviewed
   regeneration only.
3. **The replication number is not a gate result.** `min/max/median` at `0.000000` describes seed
   spread on the axis `worst_pair` maximises. `gate_cleared` cleared in 17-09 at the six
   pre-registered comparisons and is untouched; nothing here clears, weakens or re-prices it.
4. **`persona_a` / `persona_b` is a TIE-BREAK outcome.** Any downstream sentence that reads it as
   "the two personas that collided most" is false — all three pairs tied at `0.000000`.
5. **The six Phase 17 adapters (three main + four replicate, sharing two) are NOT shippable demo
   substrate** — `replay_ratio=0.0`, +211% to +241% masked dialogue-val PPL against Phase 14's
   +27.16%.
6. **`scripts/phase17_personas.py` is still at `d549e0b`.** STAT-05 now covers **21** paths with zero
   untracked; the tracked set grew by 10 this plan and every one is an ancestor-checked add.
7. **Phase 17 is complete at 11 of 11 plans.**

## Threat Flags

None. No new network endpoint, auth path or schema change at a trust boundary. The file-access
patterns are the ones 17-09 and 17-11 already established: `torch.load(..., weights_only=True)` on
adapters this repository wrote, `json.loads` over recorded sweeps, one JSON write behind a clobber
refusal, one markdown append behind a placeholder-count refusal.

Register dispositions from this plan's own `<threat_model>`:

- **TH-17-36** (a post-hoc "worst pair" choice) — **mitigated**: `worst_pair` was committed at
  `d549e0b` in Wave 1 and was **CALLED** by the Wave-5 `--replicate` mode over rates read from the
  sweep RECORDS. `tie_break_decided: true` is published as its own field. `REPLICATION_SEEDS` is
  derived from `PERSONA_SEEDS` in the same commit, and `resolve_seed` never had to refuse anything.
- **TH-17-37** (the verdict rewritten under cover of an addendum) — **mitigated, three layers**:
  `append_addendum`'s runtime `_prove`s, 17-11's synthetic test, and this plan's
  `test_report_addendum_is_additive` on the published bytes — the last watched failing twice. The
  measured diff is 62 insertions / 1 deletion and `recorded_verdict` is unchanged at 1,402 chars.
- **TH-17-46** (a public artifact produced by an uncommitted ad-hoc script) — **mitigated**:
  `git diff -- scripts/` empty across all three tasks; every published byte came from `--train`,
  `--sweep` or `--replicate`, all in git history before this plan ran.
- **TH-17-38** (a descriptive replication reported as a test) — **mitigated**: the identifier ban
  stays green (25/25), and the payload is free of `p_value` / `alpha` / `rejected` at every depth
  while the published block is free of `p =` / `alpha` / `rejected` and of any bare zero percentage.
- **TH-17-39** (two replicate seeds producing identical weights) — **mitigated**: six distinct
  `lora_B` digests and six distinct file digests, proved off the artifacts **before** the sweeps ran,
  and re-proved by `read_replicate_records` on the live digests the sweeps recorded. 0 of 36
  identical tensors across all 15 pairs.
- **TH-17-SC** — holds. **Zero packages installed**; `git diff -- pyproject.toml` empty.

## Self-Check: PASSED

Files:

- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_replication.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_replication_run.log`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_a_seed1437.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_a_seed1537.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_b_seed1438.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_b_seed1538.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_persona_{a_seed1437,a_seed1537,b_seed1438,b_seed1538}/run.csv`
- FOUND: `/Users/juliorcoelho/PersonaCore/checkpoints/phase17_persona_{a_seed1437,a_seed1537,b_seed1438,b_seed1538}_adapter.pt`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_isolation_report.md` §Replication Addendum (ISO-05)
- FOUND: `tests/test_phase17_stats.py::test_report_addendum_is_additive`

Commits:

- FOUND: `f2c0272` feat(17-10): train the four ISO-05 replicate adapters at the pre-registered seeds
- FOUND: `3d90fce` feat(17-10): run the four replicate sweeps and publish the ISO-05 addendum
- FOUND: `bc48d94` test(17-10): pin the addendum's additive property on the published artifact
