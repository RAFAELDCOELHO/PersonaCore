---
phase: 23
plan: 13
subsystem: cost-calibration
tags: [CAL-02, CAL-03, D-06, D-19, D-20, budget-pin, ratchet, checkpoint-decision, ast-guard]
requires:
  - results/phase23_cost.json (23-11) — the measuring artifact; every hours figure re-derives from it
  - .planning/phases/23-*/23-12-SUMMARY.md — the h/point table's floor/ceiling disclosure
  - scripts/mitigation_gate.py::K_RUNGS / ratchet_k / promote_to_full_fidelity (FROZEN, read-only)
  - results/phase23_cal03_wiring.json (23-04) — D-06's verdict, read LIVE
  - results/phase23_never_taught_training.json — the binding source for N_CONTROL_SEEDS
provides:
  - Z pinned in scripts/mitigation_budget.py — SWEEP_POINTS, CURVE_K, FULL_FIDELITY_K, STEP_BUDGET, N_CONTROL_SEEDS, N64_LEG_WITHDRAWN, each with a _PROVENANCE sibling
  - the user's checkpoint answer persisted as data (selected_by / selected_value / selected_reply_verbatim)
  - seven new tests: re-derivation under exact ==, the ratchet-by-import, the ceiling-sizing identity, both D-06 branches, the never-taught pricing, and a watched perturbation control
  - CAL-02 ticked, with its traceability row filled
affects:
  - 23-14 (CTRL-03 — scores the N_CONTROL_SEEDS adapters this plan priced)
  - every v4.0 sweep plan (CURVE_K is now the ratchet's floor; K may only increase)
tech-stack:
  added: []
  patterns:
    - "an IRREVERSIBLE spend decision crosses to the user at a blocking checkpoint; the executor computes the evidence and selects nothing"
    - "a checkpoint answer is persisted by the SAME write that consumes it, so a literal cannot be pinned without its selection being recorded"
    - "a provenance field is carried only where it is TRUE — sized_against is scoped to the ceiling-side multiplicands and asserted ABSENT elsewhere"
    - "a frozen constant that cannot be imported is RESTATED as a literal and the agreement is asserted by a test that DOES import it"
    - "both branches of a measured verdict are written and tested, so 'confirmed' is distinguishable from 'never checked'"
key-files:
  created: []
  modified:
    - scripts/mitigation_budget.py
    - tests/test_phase23_budget.py
    - .planning/REQUIREMENTS.md
decisions:
  - "CURVE_K = 16 and SWEEP_POINTS = 16 — SELECTED BY THE USER at Task 1's blocking checkpoint, not by the executor"
  - "FULL_FIDELITY_K = 48, STEP_BUDGET = 200, N_CONTROL_SEEDS = 5 are RULES, not options; each verified against its live source rather than transcribed"
  - "sized_against is SCOPED to SWEEP_POINTS / CURVE_K / N_CONTROL_SEEDS and ABSENT on the three constants no throughput figure feeds"
  - "the two source-module-backed constants carry record_sha256: None and git_sha: None by construction; the symbol is resolved live instead"
  - "the ceiling-sizing check is a re-derivation IDENTITY plus >=, never a strict >"
  - "the docstring got a dated CONTINUATION rather than an edit — the module's own device for a sentence that has gone stale"
requirements-completed: [CAL-02]
metrics:
  duration: ~50 min (3 task commits + 1 full-suite run)
  completed: 2026-08-28
---

# Phase 23 Plan 13: Z — the Sweep's Resource Budget, Pinned Summary

**`CURVE_K = 16` and `SWEEP_POINTS = 16` — chosen by the USER at a blocking checkpoint against a
ceiling-side total of `66.09021780091668` h per leg — are pinned in `scripts/mitigation_budget.py`
beside three rule-constants, in a module an AST guard forbids the outcome gate from importing, with
every literal re-deriving from `results/phase23_cost.json` through `phase23_cost.size_sweep` under
exact `==` on every suite run.**

## Performance

- **Duration:** ~50 min
- **Tasks:** 3 of 4 executed here (Task 1 was resolved by the user before this agent was spawned)
- **Files modified:** 3
- **Commits:** 3 task commits + this metadata commit

## The Checkpoint Answer, Verbatim, Beside the Pinned Literals

Task 1 computed the per-rung table and **selected nothing**. The user selected. Both answers are
recorded in the module as data, not only in this document — `CURVE_K_PROVENANCE` and
`SWEEP_POINTS_PROVENANCE` each carry `selected_by`, `selected_value` and
`selected_reply_verbatim`, and that write is the FIRST bytes this plan produced, so the answer was
persisted by the same write that consumed it.

| Pinned literal | User's answer | Where it is durable |
|---|---|---|
| `CURVE_K = 16` | `16` | `CURVE_K_PROVENANCE.selected_value` / `.selected_reply_verbatim` |
| `SWEEP_POINTS = 16` | `16` | `SWEEP_POINTS_PROVENANCE.selected_value` / `.selected_reply_verbatim` |

**On `CURVE_K`, verbatim (original Portuguese, recorded untranslated in the provenance field):**

> "Confirma opção 1: CURVE_K = 16. Correção registrada da minha posição anterior — o ratchet protege
> contra reduzir K depois de ver resultado ruim, mas não protege contra nunca perceber que o
> resultado ERA ruim se a escada truncar exatamente onde sinal real se revelaria. K=16 preserva o
> degrau que ancora com Phase 18 step 3, mantém promote_to_full_fidelity significativo (16→48), e
> evita o risco nomeado de 'curva truncada lida como nulo' que K=8 especificamente carrega."

The substance: the ratchet guards against **lowering** K after seeing a bad result, but it does not
guard against **never noticing the result was bad** if the ASR ladder truncates exactly where real
signal would have revealed itself. `K = 16` preserves the rung that anchors to Phase 18's step 3,
keeps `promote_to_full_fidelity` meaningful (16 → 48), and avoids the "truncated curve read as a
null" risk that `K = 8` specifically carries.

**On `SWEEP_POINTS`, verbatim:**

> "Confirma opção 1: W=16, o número já pré-registrado em ROADMAP.md:47 e REQUIREMENTS.md:179. Nenhuma
> razão nomeada para desviar dele nesta checkpoint — desvio de número já publicado exige
> justificativa científica explícita, não ajuste de conveniência no momento de gastar o compute. Nota
> registrada para decisão futura, se aplicável: número de pernas é alavanca de custo muito maior que
> largura (100,7h de diferença entre 4 e 2 pernas no mesmo degrau) — qualquer revisão de orçamento
> total deveria mirar aí primeiro, não em W."

**No recomputation was owed before Task 2.** The plan's W13 branch — recompute and re-present at the
answered width — applies only when `W != 16`. The answer is 16, which is the width the presented
table was already computed at and the width committed at `.planning/ROADMAP.md:47` /
`.planning/REQUIREMENTS.md:179` (and recorded in the cost record's own `sweep_points_source`), so
the totals the rung was chosen against **are** the totals pinned.

**A RECORDED NOTE FOR A FUTURE DECISION, NOT ACTED ON HERE.** The user additionally recorded that
leg count is a far larger cost lever than sweep width — 100.7 h between 4 legs and 2 at the same
rung — so any future revision of the total budget should target the leg count first, not `W`. This
plan pins no leg count and did not act on that note; it is carried here and in
`SWEEP_POINTS_PROVENANCE.governs` so a later budget decision meets it.

**No spend bound exists and none was invented.** Searched and measured: `23-CONTEXT.md`'s D-01…D-10
carry no hours figure, no cost ceiling and no budget; its *Claude's Discretion* section delegates
"sweep width and the concrete Z values" as a **derivation** rule and supplies no criterion to select
against; `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` carry none either. The plan named no
default rung and made no recommendation. The reason this had to cross to the user is one line of
frozen code: `scripts/mitigation_gate.py:917`'s `ratchet_k` calls `_prove(proposed_k >= fixed_k)`,
so the selection is **one-way** and the rungs span 5.36× in draws per point (42,480 at K=48 against
7,920 at K=8).

## What Was Pinned

| Constant | Value | Kind | Source, verified live |
|---|---|---|---|
| `SWEEP_POINTS` | `16` | user's selection | `results/phase23_cost.json` → `sweep_points_priced` |
| `CURVE_K` | `16` | user's selection | member of the frozen `mitigation_gate.K_RUNGS` |
| `FULL_FIDELITY_K` | `48` | **RULE** | `scripts/phase18_extraction.py:93` → `K = 48` |
| `STEP_BUDGET` | `200` | **RULE** | `scripts/teach_persona.py:1220` → `MAX_STEPS = 200` |
| `N_CONTROL_SEEDS` | `5` | **RULE** (measured count) | `results/phase23_never_taught_training.json` → `n_seeds = 5`, `seeds = [1337, 2024, 1338, 2025, 1339]` |
| `N64_LEG_WITHDRAWN` | `False` | **RULE** (verdict read) | `results/phase23_cal03_wiring.json`, read live |

Each of the three rule-constants was **resolved against its live source**, not transcribed from the
prompt: `phase18_extraction.K` and `teach_persona.MAX_STEPS` are imported and compared by
`_resolve_derivation`, and `n_seeds` is read from the never-taught training record — the binding one,
because its seeds are the adapters 23-14 actually scores. `results/phase23_control_floor.json`
carries the same five by D-08's same-N rule; that agreement is the reason the lists match and is not
a second source.

## The Figures, at Full Stored Precision

Every number below was re-derived through `phase23_cost.size_sweep(...)` in this session and
asserted equal to the committed `sizing["16"]` block, key for key, under exact `==`. Source:
`results/phase23_cost.json`, sha256
`f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`.

| Quantity at K=16, W=16, one leg | Value |
|---|---|
| `draws_per_point_at_k` | `14832` |
| `h_per_point_floor_at_k` | `1.9979696709667354` |
| `h_per_point_ceiling_at_k` | `3.1471532286150796` |
| sweep term, ceiling (`projected_hours`) | `50.354451657841274` |
| sweep term, floor (`floor_hours`) | `31.967514735467766` |
| never-taught term, ceiling (5 seeds) | `15.735766143075399` |
| never-taught term, floor (5 seeds) | `9.989848354833677` |
| **CEILING TOTAL** | **`66.09021780091668`** |

## The Ceiling-Sizing, and Why the Inequality Is `>=`

Z is sized against `h_per_point_ceiling` because the ratchet has no cheap direction: a sweep sized
against the floor and then found too expensive cannot be shrunk. `test_z_was_sized_against_the_ceiling`
proves it by **re-derivation identity** — the committed total recomputes from the *ceiling* field and
not from the *floor* field, under exact `==` — with `>=` against the floor-derived total as the
sanity conjunct.

A strict `>` was **not** asserted, and the reason is this plan set's own premise: a noised adapter
that stops emitting EOS runs every draw to the full 48 tokens, and in that regime no draw
stop-terminates, the two conditions measure the same thing, and `h_per_point_floor ==
h_per_point_ceiling`. A strict `>` would fail against a perfectly correct measurement.

**WHICH BRANCH FIRED HERE: the non-degenerate one.** `1.9979696709667354` (floor) against
`3.1471532286150796` (ceiling) — they are not equal, so the earned-equality branch did not run. It
is written and armed anyway: if the two ever coincide, the test additionally requires the record to
disclose `stop_terminated_n_ceiling == 0` and per-shape stop counts equal between the two
conditions, so a degenerate bracket has to come from the measurement rather than from one field
being copied into the other. (Measured at HEAD for the record: `stop_terminated_n_ceiling` is `0`
and `stop_terminated_n_floor` is `232` — the two conditions genuinely differ.)

`sized_against` is carried by exactly the three multiplicands of the ceiling-side total
(`SWEEP_POINTS`, `CURVE_K`, `N_CONTROL_SEEDS`) and is **absent — not empty** — on `STEP_BUDGET`,
`FULL_FIDELITY_K` and `N64_LEG_WITHDRAWN`, where no throughput figure participates at all. The test
asserts both halves, so neither an omission nor an invention passes. Requiring the field universally
would have written a provenance field that lies on three constants.

## D-06, Resolved From a Live Read

`results/phase23_cal03_wiring.json` read live in this session:

| Field | Value |
|---|---|
| `verdict` | `True` |
| `epsilon_n8` | `24.38161088311366` |
| `epsilon_n64` | `24.38161088311366` |
| `t_n8` | `4` |
| `t_n64` | `4` |

The verdict was **recomputed** through `phase23_prereg.n64_leg_is_committable` (committed blind in
23-03, strictly ancestral to the record's earliest add) rather than read off the record's field, and
the two agree. **The confirming branch fired: `N64_LEG_WITHDRAWN = False`, the n=64 leg is
committed, and the n=8 leg is untouched.**

The withdrawal branch is written and tested anyway. `test_n64_leg_matches_the_cal03_verdict` collects
**2** cases; the inactive one is driven from a **constructed** copy of the real record with
`epsilon_n64` nudged by one ULP — never by editing the committed artifact — and asserts that such a
record *would* imply a withdrawal. Without it, a pinned `False` would be indistinguishable from a
constant that could only ever say `False`.

## Both Import Ceilings, at Their True Strength

There are **two** ceilings over the same `scripts/mitigation_*.py` union, not one, and the SUMMARY
states both because an earlier draft of this plan described the ceiling by the weaker guard alone:

| Guard | Assertion | Breaks on ADD | Breaks on REMOVE |
|---|---|:---:|:---:|
| `tests/test_phase20_prereg.py:1190` | `imported <= {"pathlib", "sys", "erasure_gate"}` — **SUBSET** | yes | no |
| `tests/test_phase23_budget.py:565` | `imported == {"erasure_gate", "pathlib", "sys"}` — **EQUALITY** | yes | **yes** |

The equality guard has **zero headroom in both directions**, by its own recorded reason: a shrunken
union would tell a future sibling it has an import budget it must not use. Both are green after this
plan's edit.

The guard that actually **binds this file**, however, is neither of those: it is the literal-only
guard at `tests/test_phase23_budget.py:308`, which asserts every module-level node after the
docstring is an `ast.Assign` whose value passes `literal_eval`. An `import` is not an `Assign`, so it
fails there first. This plan is append-only into a module that imports nothing, so all three are
satisfied trivially — the point of stating them correctly is that this document is read as a record
of what the constraints are.

Because the module cannot import the gate, `CURVE_K` and `FULL_FIDELITY_K` are **restated literals**.
`test_selected_k_is_a_ratcheted_rung` closes that copy: it imports the frozen `mitigation_gate` from
the test, asserts both are members of `K_RUNGS = (48, 24, 16, 8)`, calls `ratchet_k` and
`promote_to_full_fidelity` with the pinned pair, and **watches a decrease being refused**.

## Additivity, Measured

| File | Insertions | Deletions |
|---|---:|---:|
| `scripts/mitigation_budget.py` | 306 | **0** |
| `tests/test_phase23_budget.py` | 600 | **0** |
| `.planning/REQUIREMENTS.md` | 3 | 2 (the CAL-02 checkbox line and its traceability row) |

The module's whole history stays additive (`153/0`, `148/0`, now `306/0`). `CONTROL_NOISE_FLOOR` and
`MATCHED_CONTROL_NOISE_FLOOR` are byte-unchanged with their `_PROVENANCE` siblings, and the AST walk
lists the four pre-existing names **first and unchanged** before the twelve new ones.

**The 23-09 / 23-18 floor cases in `test_budget_constants_re_derive` were EXTENDED, not rewritten —
zero deletions in that file, so there are no deletions to account for by name.** The docstring got a
dated **continuation** paragraph (a pure insertion) rather than an edit, because two of its
forward-tense sentences went stale the moment Z landed: "The Z values … arrive in 23-13" and "No such
restatement exists yet … 23-13's Z values are the first that will need one." That is the module's own
device, copied from the 23-18 continuation six lines above it.

## Every Structural Criterion Is an AST Gate

`MATCHED_CONTROL_NOISE_FLOOR` contains `CONTROL_NOISE_FLOOR` as a substring, and this plan's own
provenance strings mention the rung numbers in prose — `CURVE_K_PROVENANCE.selected_reply_verbatim`
literally contains the text `CURVE_K = 16`. So:

- the constant census is an AST walk over module-level `Assign` target names, never a `grep -c`;
- the register `_Z_CONSTANTS` is asserted **equal** to that walk, so a seventh constant added without
  being registered cannot be silently skipped by the loops that iterate it;
- the perturbation control's needle is **line-anchored** (`"\nSWEEP_POINTS = 16"`), because the
  pinned width also appears inside the provenance dict and inside the user's verbatim reply — a bare
  needle would have been ambiguous by construction;
- the two pre-existing needle-uniqueness guards (`test_a_hand_edited_floor_is_detected`,
  `test_the_original_needle_is_still_unique`) are still green: no added line re-types either floor's
  literal assignment.

## The Digest Note — One Key Name, Two Meanings, Disclosed

The two floors carry `record_sha256` = the record's **own** field, an INPUTS digest over `per_seed`,
plus a separate `record_file_sha256` for the bytes. **None** of the three records the Z constants
cite carries an inputs digest of its own, so on every Z provenance dict `record_sha256` is the
sha256 of the committed **file's bytes**. Rather than leave a reader to infer that from four dicts,
it is stated once in the Z banner and **asserted** in `test_budget_constants_re_derive`, which checks
each one live against `read_bytes()`.

The two source-module-backed constants (`FULL_FIDELITY_K`, `STEP_BUDGET`) carry `record_sha256:
None` and `git_sha: None` **by construction**, and that absence is asserted rather than tolerated:
their source is a live source module this phase does not freeze, so a digest pinned here would go
stale on any unrelated edit while asserting nothing. Resolving the symbol is the check a digest would
only approximate.

## CAL-02 Ticked — and All Six of the Phase's Requirements Accounted For

| Requirement | State | Owner |
|---|---|---|
| CAL-01 | `[x]` | 23-12 |
| **CAL-02** | **`[x]` — this plan** | **23-13** |
| CAL-03 | `[x]` (untouched here) | 23-04 |
| CAL-05 | `[x]` | 23-12 |
| DPSGD-06 | `[x]` | 23-10 |
| CTRL-03 | `[ ]` — still open | 23-14, next wave |

The state backstop confirms exactly that: five ticked, `CTRL-03` `False`.

**No `gsd-sdk` mutation handler touched `.planning/REQUIREMENTS.md`.** It was hand-edited with
`Edit`, for the recorded reason that `roadmap.update-plan-progress` keys on SUMMARY existence and
falsely ticked 23-17 in this repository.

The narrow freeze holds in both directions, measured with the swapped diff indicators (git 2.50.1):

```
changed lines NOT naming CAL-02 : 0
changed lines matching CAL-03   : 0
```

The requirement 23-04 closed is cited in the note **by path** — "the wiring record
`results/phase23_cal03_wiring.json`" — never by requirement id, so the no-re-tick guard sees nothing.

## Deviations from Plan

**None of the deviation rules fired.** No bug, no missing critical functionality, no blocker, and no
architectural question arose. Three implementation choices were made inside the plan's own latitude
and are recorded because they are visible in the diff:

1. **`selected_reply_verbatim` is a third provenance field.** The plan named `selected_by` and
   `selected_value`. Putting the user's prose into `selected_value` would have made that field a
   paragraph sitting beside `CURVE_K = 16`, so `selected_value` holds the number, `selected_by` holds
   the actor and the reason it was theirs to choose, and the verbatim reply gets its own field. All
   three are additive; nothing the plan asked for is missing.
2. **`record_sha256: None` / `git_sha: None` on the two source-module-backed constants**, with the
   absence asserted and the reason recorded in `governs`. The plan required the five keys on every
   dict; a fabricated digest over a file this phase does not freeze would have been a provenance
   field that goes stale while asserting nothing — the same defect W9 exists to prevent one field
   later.
3. **A dated continuation paragraph in the module docstring** (pure insertion, 0 deletions), because
   two of its forward-tense sentences described Z as not yet existing.

## Authentication Gates

None. This plan ran no GPU work, needed no detached launch, and made no network call — it is
arithmetic over committed JSON.

## Known Stubs

None. Every constant pinned is a real measured or resolved value with a live-checked source; no
placeholder, no `TODO`, no empty default.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file-access pattern and no schema at a
trust boundary. It appends literal constants to a module that imports nothing and executes nothing.

## Test Suite

| | Result |
|---|---|
| Baseline before this plan | **1571 passed, 1 skipped** |
| After Task 3 (full suite) | **1578 passed, 1 skipped** |
| Delta | +7, exactly the 7 tests this plan added |

Zero regressions. `tests/test_phase23_budget.py` went from 12 to 19 tests, all passing, **zero
skips**. `make lint` (`ruff check . && ruff format --check .`) exits 0.

The seven added tests:

| Test | Proves |
|---|---|
| `test_selected_k_is_a_ratcheted_rung` | the restated rungs and the frozen gate agree, checked by importing the gate; a decrease is watched being refused |
| `test_the_step_budget_agrees_with_the_production_constant` | the restate-and-assert route's second half, plus a third witness from the cost record's four training legs |
| `test_z_was_sized_against_the_ceiling` | `sized_against` present on exactly the three multiplicands and absent on the other three; the total re-derives from the ceiling field by identity; `>=` against the floor |
| `test_n64_leg_matches_the_cal03_verdict[False]` | the pinned branch matches the committed record's live verdict |
| `test_n64_leg_matches_the_cal03_verdict[True]` | a falsified record *would* withdraw — the selector discriminates |
| `test_the_never_taught_floor_is_priced_in_z` | `N_CONTROL_SEEDS` matches the distinct-seed count, and the control term recomputes at **every** rung, not only the selected one |
| `test_a_z_constant_that_does_not_re_derive_is_detected` | watched RED, permanent: a one-off perturbation of `SWEEP_POINTS` is observed being caught |

## Frozen Artifacts — Still Clean

```
git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py \
  scripts/phase23_prereg.py scripts/phase23_matched_prereg.py scripts/phase23_resume_prereg.py \
  scripts/phase18_extraction.py results/ pyproject.toml      -> exit 0
git log --format=%H -- scripts/phase23_matched_prereg.py | wc -l  -> 1
```

The two pre-registration scripts the ancestry guard binds are byte-unchanged, and
`scripts/phase23_matched_prereg.py` still has **exactly one** commit.

## Commits

| Task | Commit | Message |
|---|---|---|
| 2 | `0a23aca` | `feat(23-13): pin Z — CURVE_K=16 and SWEEP_POINTS=16, selected by the user` |
| 3 | `bb2822d` | `test(23-13): make every Z constant checkable — re-derivation, the ratchet, both D-06 branches` |
| 4 | `810cad4` | `docs(23-13): tick CAL-02 — Z is committed, and the rung was the user's` |

Task 1 wrote no file and made no commit, exactly as its own last acceptance criterion requires.

## What 23-14 Inherits

- `N_CONTROL_SEEDS = 5` and the seeds `(1337, 2024, 1338, 2025, 1339)` — the adapters CTRL-03 scores,
  now priced into the budget at `15.735766143075399` h on the ceiling side.
- `CURVE_K = 16` as the ratchet's floor. Any later K may only **increase**; `ratchet_k` refuses every
  decrease, with no override flag.
- The filled CAL-02 traceability row as the convention for CTRL-03's own tick, and the all-six state
  backstop that expects `CTRL-03` to be the last `False`.

## Self-Check: PASSED

- All three modified files and this SUMMARY exist on disk.
- All three task commits (`0a23aca`, `bb2822d`, `810cad4`) resolve in `git log`.
- The headline figure re-derives live: `phase23_cost.size_sweep` at the pinned pair returns a
  ceiling-side total of `66.09021780091668` h, equal under `==` to the committed
  `sizing["16"].total_hours_ceiling_with_never_taught_floor`, and
  `results/phase23_cost.json` still hashes to
  `f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`.
