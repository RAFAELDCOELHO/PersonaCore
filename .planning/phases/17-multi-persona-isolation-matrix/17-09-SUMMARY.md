---
phase: 17-multi-persona-isolation-matrix
plan: 09
subsystem: isolation-matrix-run-and-verdict
tags: [iso-02, iso-03, iso-04, stat-05, d-10, d-13, d-14, d-15, d-18, d-19, f-13, sc3, sc4, gate-cleared]
requires:
  - scripts/phase17_isolation.py (the 17-04/17-06/17-08 driver, run unmodified in all three modes)
  - scripts/teach_persona.py (17-02's widened train_arm — seed= and prefix= threaded)
  - scripts/phase17_personas.py (PERSONA_SEEDS, HOLM_FAMILY_CELLS, gate_cleared — byte-untouched)
  - scripts/phase17_persona_facts.py (the 24 gated values)
  - results/phase17_personas_report.md (the hand-recorded GO this run reads, never hardcodes)
  - results/phase16_recall_sample.json (the binding fixture — 104 core_held_out questions)
  - checkpoints/convbase_slim.pt (W0: git 04e724c6 / step 4000 / val_loss 1.5235939979553224)
provides:
  - checkpoints/phase17_persona_{a,b,c}_adapter.pt (three adapters, three distinct seeds)
  - results/phase17_training_run.log + results/phase17_persona_{a,b,c}/run.csv
  - results/phase17_sweep_{persona_a,persona_b,persona_c,base}.json (the whole evidentiary basis)
  - results/phase17_isolation_report.md (the matrix, the base row, six Holm rows, the verdict)
  - the FIRST production exercise of ISO-04's cross-process half
affects:
  - plan 17-10 (replaces the one `not yet measured` line; worst_pair already selected a/b)
  - plan 17-11 (adds --replicate; its seed-scoped records stay unreachable from read_sweep_records)
  - the isolation report is now WRITE-ONCE — a re-drive needs a reviewed deletion commit
tech-stack:
  added: []
  patterns:
    - the run is detached (ppid=1) and its success is read from an on-disk exit-code sentinel,
      never inferred from log text
    - a warning-sign check performed and published BEFORE the matrix is scored, either way it lands
    - a scope addendum that can only reduce what the phase claims, appended after the numbers
key-files:
  created:
    - results/phase17_training_run.log
    - results/phase17_persona_a/run.csv
    - results/phase17_persona_b/run.csv
    - results/phase17_persona_c/run.csv
    - results/phase17_sweep_persona_a.json
    - results/phase17_sweep_persona_b.json
    - results/phase17_sweep_persona_c.json
    - results/phase17_sweep_base.json
    - results/phase17_isolation_report.md
  modified:
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - .planning/REQUIREMENTS.md
decisions:
  - the plan's Task-2 verify command reads a `forbid_digest` key 17-06 deliberately never wrote;
    the COMMAND was corrected, not the record — a second copy of one hash is a second place it
    can stop agreeing about the same mask
  - F-13's checkpoint label went into a dated hand-appended addendum rather than into the
    committed report writer, because editing a writer that was committed before any number
    existed is the post-hoc amendment the whole pre-registration exists to prevent
  - the D-13 anchor miss was investigated to a cause BEFORE `--report` ran, not after
metrics:
  duration: 70min
  tasks: 3
  files: 12
  completed: 2026-08-14
---

# Phase 17 Plan 09: The Isolation Matrix Run and the Cleared Gate Summary

Three adapters trained at three distinct seeds from GO-gated material, four sweeps ran in four
fresh processes on provably different weights under one git SHA, and the pre-registered gate
**CLEARED** — all six Holm comparisons rejected at `p = 0.0078125` each, every one of the 48
slot-level observations favouring the diagonal, with all six off-diagonals at `0/104` and an
adapter-off base row at `0/104` that gives every one of those zeros an empirical reading.

## The Numbers

**Diagonals (question unit, STAT-01):**

| adapter | diagonal | rate | cluster bootstrap 95% |
|---|---|---|---|
| `persona_a` | 104/104 questions | 1.000000 | (1.000000, 1.000000) |
| `persona_b` | 103/104 questions | 0.990385 | (0.961538, 1.000000) |
| `persona_c` | 103/104 questions | 0.990385 | (0.961538, 1.000000) |

**All six off-diagonals: `0/104` questions** (`0/936` draws), each carrying a one-sided 95% Wilson
upper bound of `0.025355` and BOTH clustering ends of the rule of three — `3/104 = 0.028846`
question-level (optimistic) and `3/8 = 0.375000` slot-level (conservative).

**The base row, quoted, all three cells:** `(base, persona_a)` `0/104`, `(base, persona_b)` `0/104`,
`(base, persona_c)` `0/104` — `0/936` draws each. Per **D-15 these three diagonals are three
separate anchors and are NOT a ranking**; at n=1 seed per persona, content and seed are confounded
between personas, and no sentence here or in the report orders them.

**The gate.** Six comparisons, six rejections, `p = 0.0078125` on every one (8/8 slot unanimity,
the only achievable value that clears) against step alphas `0.0083333 … 0.0500000`.
`gate_cleared` returns **`True`**.

**Re-derived independently, as the criterion requires.** The six rows were parsed back OUT of the
published table in `results/phase17_isolation_report.md` and handed to the imported
`personas.gate_cleared`: it returned `True`, the published cell pairs equal `HOLM_FAMILY_CELLS`
exactly, and the truncation control — the same six rows minus one — returned `False`. The verdict
was not read off the prose.

## What Was Built

### Task 1 — three adapters at three seeds (`b6b2fed`)

Three invocations of the committed `--train` mode. **No driver code was written in this plan.**

| | measured |
|---|---|
| ISO-01 gate | `[phase17_isolation] ISO-01 verdict in phase17_personas_report.md: GO` — READ, never hardcoded |
| Phase 14 gate | `[teach_persona] D-06 verdict: ADAPT` — both gates fired on every arm |
| Resolved path (checked on the FIRST invocation, before the other two ran) | `checkpoints/phase17_persona_a_adapter.pt` — the `phase17_` prefix, at both `arm_outputs` call sites |
| `ls checkpoints/ \| grep -c "phase14_persona_"` | **0** (TH-17-47) |
| Artifacts | 1,351,367 B each, 331,776 trainable params, `r=8` / `alpha=16.0` |
| Base fingerprint on all three | `04e724c6` / step `4000` — the same W0 the ISO-01 gate probed |
| Seeds in the provenance lines | `seed=1337`, `seed=1338`, `seed=1339` |
| Wall | 82 s / 80 s / 80 s, MPS fp32 |

**Pairwise `lora_B` comparison — the check the plan asks to be stated explicitly.** All 36 `lora_B`
tensors compared per pair with `torch.equal`:

| pair | identical tensors | max abs difference |
|---|---|---|
| a vs b | **0 of 36** | 0.0570608 |
| a vs c | **0 of 36** | 0.0534719 |
| b vs c | **0 of 36** | 0.0563148 |

**Result: no two adapters share a single `lora_B` tensor.** The `seed=` parameter reached the init
draw; the ISO-04 canary did not have to catch this after 15 minutes of sweeps.

`sanity_check`'s proofs printed for all three arms and none raised — including **proof 6**,
`130 held-out questions: none present at token level`, re-proving the never-seen split against each
new persona's own teaching bin (RESEARCH F-06). Bins landed at `data/persona_persona_a_train.bin` —
17-02's recorded doubled word, expected and gitignored.

### Task 2 — four sweeps, four fresh processes (`1df7384`)

| sweep | pid | `adapter_enabled` | live `lora_B` sha256 | adapter file sha256 | wall |
|---|---|---|---|---|---|
| `persona_a` | 72355 | `true` | `ab0a8d678521d078…` | `b420c22ac0d576a1…` | 3.2 min |
| `persona_b` | 72803 | `true` | `5a35d2056f9938e7…` | `7d6dde9eef0bbbc6…` | 3.2 min |
| `persona_c` | 73385 | `true` | `bc9429f6a0f1d61b…` | `0842b617bb163f14…` | 3.2 min |
| `base` | 73652 | **`false`** | `433cc42fe3a2bb15…` | `226f2ae59938e389…` | 5.3 min |

One `git_sha` (`b6b2fed…`) across all four; one `forbid_ids` digest `79b55770…` with 7,645 of 8,192
masked — the same mask the ISO-01 pre-flight used. 104 questions, 8 slots x 13, 9 draws each, and
the `(slot, seed_index, question)` triple set **identical across all four records**, asserted rather
than eyeballed.

**The two facts the criterion asks to be stated SEPARATELY:**

1. **`adapter_enabled` is `false` on the base record and `true` on the other three.** This — and
   not any weight digest — is what records the column as a control, backed by the driver's runtime
   proof over every `LoRALinear.enabled` inside the `adapter_disabled` context.
2. **The base record's `lora_b_sha256` is `433cc42fe3a2bb15…`, the digest of the weights loaded
   from `checkpoints/persona_adapter.pt`, and it differs from all three Phase 17 adapters.** It is
   NOT an all-zero digest (that would be `3ff92f1b…`) and was never expected to be. Independently
   confirmed: the base record's `adapter_file_sha256` `226f2ae59938e389…` equals the sha256 of
   `checkpoints/persona_adapter.pt` computed directly off disk, byte for byte.

**Total sweep wall: 14.9 min** (192 + 195 + 191 + 319 s) against the plan's ~18-19 min band — a
**~20% underrun, stated rather than absorbed.** The adapter sweeps ran at ~1.85 s/question against
the predicted 2.4-2.7, the base at ~3.07 s/question exactly as predicted.

### Task 3 — the report and the verdict (`68033ab`)

`--report` ran in 3.7 s CPU-only. `assert_sweeps_ran_on_distinct_weights` ran before scoring
(17-08 already wires it; not duplicated here). Checked against the pre-registration rather than
against expectation: four matrix rows, six Holm rows, none naming `base`, one `not yet measured`
line, no bare zero percentage anywhere, no ranking sentence, no aggregate over the nine cells.
`ALL_FAIL_BRANCH` is correctly absent — the gate cleared, so D-10's branch was not taken.

## The Two Base-Column Warning Signs, Checked BEFORE Anything Was Scored

**Warning sign 1 — a non-zero base column. It is zero.** Scored with the committed
`score_completion` against `values_by_slot()`:

| persona's values | base column containment |
|---|---|
| `persona_a` | **0/104 questions, 0/936 draws** |
| `persona_b` | **0/104 questions, 0/936 draws** |
| `persona_c` | **0/104 questions, 0/936 draws** |

Matches Phase 16's `base-neither` 0/104 on this tier and the ISO-01 pre-flight's zero containments.
Neither a gate failure nor a sweep bug; the matrix was safe to read.

**Warning sign 2 — the D-13 anchor. It is a PARTIAL MISS, and it is published as one.**

| slot | seeded prior | reproduced |
|---|---|---|
| `hometown` | `the country` | **yes** — 7 of 108 base draws |
| `pet_name` | `rose` | **NO** — 0 of 103 base draws |

D-13 and 17-08's handover #7 both require this to be investigated before the derivation is trusted
on the other six slots, and require it published either way. **Investigated, with three independent
lines of evidence that it is a property of the seed list rather than of this sweep:**

1. **Provenance.** `BASE_PRIOR_SEEDS` was measured on `convbase_slim.pt` under *greedy decoding
   from a bare `<|system|>` prompt* (`scripts/phase14_factset.py:295-296`). This sweep samples 9
   draws per question from the 104-question recall fixture with `forbid_ids` masked and `stop_ids`
   set. A different decoder on a different prompt is not required to reproduce a greedy mode.
2. **An independent instrument agrees.** The 17-07 ISO-01 pre-flight ran on the **pure un-adapted
   base with no adapter loaded at all** — a different code path (`build_unadapted_base`) — over 416
   completions on the same fixture. `results/phase17_personas_report.md` contains `the country`
   **11 times** and the word `rose` **zero times**. This sweep reproduces that independently
   measured base rather than diverging from it.
3. **D-13 already says so.** `BASE_PRIOR_SEEDS` covers 2 of 8 core slots and is "a seed list for
   screening candidate values, never an enumeration of what the base may say".

What the base actually does on `pet_name` is emit no name at all — `i have a dog. i love dogs.`,
`i hate pets? i can take a baller one soon`, `i am sorry. my best friends say so.` — the same
character 17-07 recorded from the un-adapted base. The empirical adapter-off column, which is the
instrument D-13 designates precisely because the seed list cannot be complete, is present and is
what the off-diagonals are read against.

## The Two Base Artifacts Are PHASE 13 RESULTS, Not Phase 17 Findings

Counted across all four sweeps, 936 draws each:

| sweep | `college student` attractor | `<\|assistant\|>` leakage |
|---|---|---|
| `persona_a` | 0 of 936 | 0 of 936 |
| `persona_b` | 0 of 936 | 0 of 936 |
| `persona_c` | 0 of 936 | 0 of 936 |
| `base` | **47 of 936** | **56 of 936** |

Both are **already-published properties of this base** — Phase 13 measured and published the
role-token leakage at **79 naive / 70 EWC**, and 17-07 re-confirmed the attractor at up to 7 of 52
in a slot on the un-adapted base. They are recorded in the report as such and are claimed by this
phase as nothing. Neither string contains any of the 24 minted values, so neither can enter
`score_completion`'s containment test in any cell.

**One thing here is newly measured, and it is a correction rather than a claim.** 17-07's handover
note 7 predicted both would also appear in 17-09's adapter completions. Across 2,808 adapter draws
the measured count is **0 of 936 in each of the three adapter columns**. The prediction does not
hold for the adapted rows. Recorded as a falsified expectation; no gate reads it.

## F-13 Is Labeled CHECKPOINT-SPECIFIC Wherever This Plan Invokes It

The committed report writer makes **no F-13 claim at all** (`grep -n "F-13\|cannot be the base"`
over `scripts/phase17_isolation.py` and `scripts/phase17_personas.py`: zero hits), so there was no
unlabeled inheritance already in the artifact. The label was added to the report anyway, because
this plan's own base row invites the stronger reading and a later reader would take it:

> F-13 is a property of ONE checkpoint — `checkpoints/convbase_slim.pt` at git
> `04e724c67033f9a2ed8b705a07ad025c867a18c5`, step `4000`, val_loss `1.5235939979553224`. It is
> **NOT** a standing invariant of this project, of the LoRA mechanism, or of the tokenizer. Any
> future checkpoint requires the guessability gate to be **RE-RUN**, never inherited by assumption
> from this report, from `results/phase17_personas_report.md`, or from `17-RESEARCH.md`.

Nothing in §Gate or §Verdict depends on F-13: the six comparisons are computed from the three
adapter rows alone, and the separator that contextualizes them is the **measured** adapter-off
column in §The Matrix, not the pre-flight.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's Task-2 verify command reads a record key that deliberately does not exist**

- **Found during:** Task 2, first run of the plan's `<automated>` verification.
- **Issue:** the command reads `r['forbid_digest']` and raised `KeyError: 'forbid_digest'` on all
  four records. 17-06 declined to write that top-level key and recorded the reason in its handover
  #2: `phase16_persistence.arm_config_record` already carries `forbid_ids_sha256` as a committed
  parity column, and *"two copies of one hash in one file is two places it can stop agreeing about
  the same mask"*. The hash lives at `record["config"]["forbid_ids_sha256"]`, one hash in one place.
- **Fix:** the **command** was corrected to read the committed key, not the record. Adding a
  duplicate top-level hash to satisfy a stale verify line would have re-introduced exactly the
  drift surface 17-06 removed, on the axis T-16-40 records as the repudiation surface. Every other
  assertion in the command was left byte-identical and all of them pass: four records, four pids,
  one `git_sha`, one forbid digest, four distinct live digests, four distinct file digests,
  `adapter_enabled` false on base alone.
- **Files modified:** none (a stale-criterion finding, not a code defect).
- **Commit:** `1df7384`

**2. [Rule 2 - Missing critical functionality] The report carried no scope label on F-13 and no disclosure of the two Phase 13 base artifacts**

- **Found during:** Task 3, after `--report` produced the artifact.
- **Issue:** the report is the phase's public evidence artifact and `results/` ships publicly. Its
  base row is the leak-vs-prior separator, which invites the stronger F-13 reading; and the raw
  completions a reader will meet carry two artifacts that Phase 13 already published, which a
  reader could take as new Phase 17 discoveries.
- **Fix:** a dated `## Scope Addendum` appended **after** `## Provenance`, stating in its own first
  paragraph that everything above it is the driver's own output and byte-untouched. It alters no
  rate, no p value, no step alpha, no sign, no verdict and no pre-registered constant, and it can
  only REDUCE what the phase claims. Verified after the edit: the `recorded_verdict` body is
  unchanged at 1,402 characters and still anchors on `## Verdict`; six Holm rows; zero rows naming
  `base`; exactly one `not yet measured` line; no bare zero percentage anywhere in the file.
- **Why an addendum and not an edit to the writer:** `render_report` was committed in 17-08 before
  a single Phase 17 number existed. Editing it now to emit this text would be amending a
  pre-registered artifact after seeing the numbers — the exact move this phase's whole ordering
  discipline exists to prevent. Phase 15's CR-02 addendum to `phase13_ab_report.md` is the
  established precedent for a dated hand-appended section on a recorded report.
- **Files modified:** `results/phase17_isolation_report.md`
- **Commit:** `68033ab`

### Interpretations recorded

**Collateral collapse is far larger than Phase 14's, and the reason is structural rather than
anomalous.** Measured masked dialogue-val PPL, adapter OFF `4.5733` in all three runs:

| arm | ON | delta |
|---|---|---|
| `persona_a` | 14.2507 | +211.60% |
| `persona_b` | 14.9068 | +225.95% |
| `persona_c` | 15.6121 | +241.37% |

Phase 14's shipped `real` arm recorded **+27.16%**. The difference is not a defect and not a
finding about isolation: Phase 14's `real` arm trained at `replay_ratio=0.5` (220 episodes, 20,036
tokens = 10,018 teaching + 10,018 replay), while `run_one_persona_training` calls `train_arm` at
the committed default `replay_ratio=0.0` (176 episodes, ~7,500 tokens, no replay). Replay is the
mechanism that protects dialogue capability, and these adapters have none. **This is recorded, not
repaired** — changing the recipe after the gate report would put code after the report it obeys,
and this phase measures isolation, not conversational retention. It does mean the three Phase 17
adapters are **not shippable demo substrate** and no claim about them should imply otherwise.

**No aggregate isolation rate was computed anywhere, including in this SUMMARY** (STAT-06). Every
number above carries its own denominator.

## Verification

Every number came from a command run in this session.

| Check | Result |
|---|---|
| Training detached | pid **68200**, **ppid 1** — reparented to launchd, survives the session |
| Training exit code | **0**, read from the on-disk sentinel, not from log text |
| Sweep run detached | pid **72238**, **ppid 1** |
| Sweep exit code | **0**, read from the on-disk sentinel |
| Plan's Task-2 automated check (corrected key) | `four distinct sweeps, one codebase, base recorded adapter-off` |
| Plan's Task-1 automated check | three `test -f` pass; `pytest -q tests/test_phase17_personas.py tests/test_phase14_teaching.py` green |
| `pytest -q tests/test_phase17_stats.py tests/test_phase16_prereg.py -x` | **22 passed** in 3.72s |
| `pytest -q` (full suite) | **645 passed, 1 skipped** in 124.30s — baseline 645/1 held exactly, floor 579 |
| **STAT-05 `checked`** | **11** (1 prereg commit `d549e0b` x 11 matched paths), **0 untracked** — was 2 at 17-07 |
| `git log -- scripts/phase17_personas.py` | **`d549e0b` only** — the uneditable pre-registration is byte-untouched |
| `re.search(r'\b0(\.0+)?%', report)` (STAT-02) | **`None`** |
| Holm rows / rows naming `base` | **6 / 0** |
| `+1` sign vectors of length 8 | **6** — all 48 slot observations favour the diagonal |
| `recorded_verdict` on the report | parses; body 1,402 chars, first line is `gate_cleared` returns `True` |
| `gate_cleared` re-derived from the published rows | **`True`**; truncation control on 5 rows **`False`** |
| Published cell pairs == `HOLM_FAMILY_CELLS` | **True** |
| `git diff -- pyproject.toml` (STAT-04) | **empty** |
| `.venv/bin/ruff check .` + `format --check .` (the CI version, 0.15.16) | **clean, 155 files** |
| `make lint` | **red — pre-existing DEF-17-01, count unchanged at 9** |
| `git status --short` | empty after each commit |
| `git diff --diff-filter=D` per commit | **empty** — no deletions in any of the three |
| `scripts/phase17_persona_gate.py` re-run | **never invoked** — the armed clobber guard was not touched |

## Deferred Issues

`make lint` remains red from **DEF-17-01** (pre-existing to this phase, recorded at 17-01):
`Makefile:16` runs bare `ruff`, which resolves on this box to a pyenv shim holding ruff 0.1.15
against the project's `ruff~=0.15` pin. The count is **unchanged at 9**. This plan modified no
Python file at all, so it cannot have moved it. `.venv/bin/ruff` 0.15.16 — the version CI installs
— is clean on all 155 files. Nothing new deferred.

## Known Stubs

One, inherited and deliberate: `## Replication (ISO-05)` carries its single
`ISO-05 replication result: not yet measured.` line. That is 17-08's committed placeholder, owned
by plans 17-10 and 17-11, and everything the section needs at report time is already rendered above
it — the six ordered off-diagonal rates, `worst_pair`'s selection over them, the k=3 seeds and the
D-16 descriptive-only statement. `worst_pair` selected `persona_a` / `persona_b` at seeds
`(1337, 1437, 1537)` and `(1338, 1438, 1538)`, which is the D-19 tie-break resolving the **three-way
tie at `0.000000`** — the phase's success case, exactly the situation the committed tie-break exists
for. Nothing in this plan stands in for missing code.

## Requirements

**ISO-02, ISO-03 and ISO-04 marked Complete.** The claimant sets were re-derived across every plan
in the phase and every predecessor explicitly deferred to here:

- **ISO-02** (17-04, 17-06, 17-09) — the matrix scores 104 shared-slot questions against every
  persona's value, 3 sweeps scored 3 ways. 17-04 and 17-06 both declined: "no adapter has trained,
  no sweep has run and no matrix exists".
- **ISO-03** (17-04, 17-06, 17-08, 17-09) — the matrix carries the explicit adapter-off column,
  published with three rates and their denominators. 17-08 declined and named this plan: "this plan
  ships the code that computes and publishes that column, and 17-09 produces it".
- **ISO-04** (17-06, 17-09) — both canary layers ran **in production** here for the first time:
  `load_adapter_with_canary` at each of the three adapter loads, and
  `assert_sweeps_ran_on_distinct_weights` inside `run_report_mode` before scoring. 17-06 declined
  for exactly this reason: "the canary's unskippable half has no production caller yet".

**STAT-05 was already Complete** from Phase 16 and is untouched; this plan records the count it
measured (`checked = 11`) rather than re-adding the assertion, per 17-07's handover 4.
**ISO-05 NOT marked** — nothing has been replicated; 17-10 and 17-11 own it.

## Handover Notes

1. **`results/phase17_isolation_report.md` is WRITE-ONCE and now carries a recorded verdict.**
   `assert_isolation_report_not_clobbered` refuses a second `--report`. A re-drive needs the file
   deleted in a reviewed commit — the same recovery 17-05/17-07 established for the gate report.
2. **17-10 replaces exactly the `ISO-05 replication result: not yet measured.` line.** It is still
   the only line in the report carrying that phrase. Note that the file now ends with a
   `## Scope Addendum` section **after** `## Provenance`; any byte-identity assertion 17-10 makes
   about "everything above the addendum" must account for it, and it was committed here at
   `68033ab`, before 17-10 runs.
3. **`worst_pair` has already selected `persona_a` / `persona_b`** off the three-way tie at
   `0.000000`, at replication seeds `(1337, 1437, 1537)` and `(1338, 1438, 1538)`. 17-11's
   seed-scoped records remain structurally unreachable from `read_sweep_records`, which reads the
   four unscoped paths by name.
4. **The three Phase 17 adapters are NOT shippable demo substrate.** They trained at
   `replay_ratio=0.0` and cost +211% to +241% masked dialogue-val PPL against Phase 14's +27.16%.
   Fine for this phase, which measures isolation; do not reuse them anywhere a conversational
   claim is made.
5. **F-13 stays checkpoint-specific.** The report now says so in its own addendum with the
   fingerprint spelled out. Any future checkpoint requires the guessability gate re-run.
6. **17-07's handover 7 is falsified for the adapter rows** — the attractor and the role-token
   leakage measured 0 of 936 in each adapter column. Do not carry the prediction forward unchecked.
7. **`scripts/phase17_personas.py` remains at `d549e0b` and is still uneditable.** STAT-05 now
   covers 11 paths with zero untracked; an edit turns the guard permanently red.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.

Register dispositions from this plan's own `<threat_model>`:

- **TH-17-31** (a silent adapter swap producing a fabricated matrix) — **mitigated, three layers
  all exercised in production**: `load_adapter_with_canary` at each of the three loads,
  `assert_sweeps_ran_on_distinct_weights` in `--report` before scoring, and Task 1's pairwise
  `lora_B` comparison proving the three artifacts differ before 15 minutes of sweeps were paid for.
  The four distinct live digests and four distinct file digests are recorded in the artifact.
- **TH-17-47** (a Phase 17 adapter under a `phase14_` path) — **mitigated**: the resolved path was
  echoed and checked on the FIRST invocation before the other two ran, and
  `ls checkpoints/ | grep -c "phase14_persona_"` returns 0.
- **TH-17-32** (a verdict softened after seeing the number) — **mitigated**: the verdict is
  `gate_cleared`'s return, re-derived here from the published rows; `ALL_FAIL_BRANCH` was committed
  in Wave 4 and is correctly absent because the gate cleared; STAT-05 is non-vacuous at 11.
- **TH-17-33** (pickled `.pt` read) — **mitigated**: adapters read at `weights_only=True` via
  `checkpoint.load_adapter`; the one `weights_only=False` read is the project's own
  `convbase_best.pt` full resume checkpoint, documented TRUSTED.
- **TH-17-34** (a clobbered record or report) — **mitigated**: refuse-to-rerun fired on nothing
  because nothing was re-driven; the report guard is now armed on a recorded verdict.
- **TH-17-35** (personal data in a public artifact) — **mitigated**: all 24 values invented (D-06)
  and human-reviewed at the 17-07 checkpoint. The completions quoted in this SUMMARY are base-model
  output about invented personas.
- **TH-17-SC** — holds. **Zero packages installed**; `git diff -- pyproject.toml` empty.

## Self-Check: PASSED

Files:

- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_isolation_report.md`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_a.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_b.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_persona_c.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_sweep_base.json`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_training_run.log`
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_persona_{a,b,c}/run.csv`
- FOUND: `/Users/juliorcoelho/PersonaCore/checkpoints/phase17_persona_{a,b,c}_adapter.pt`

Commits:

- FOUND: `b6b2fed` feat(17-09): train the three Phase 17 persona adapters at three distinct seeds
- FOUND: `1df7384` feat(17-09): run the four isolation sweeps in four fresh processes
- FOUND: `68033ab` feat(17-09): assemble the isolation report — the pre-registered gate CLEARED
