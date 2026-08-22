---
phase: 21
slug: the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-22
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Source of truth for the full requirement→test map:** `21-RESEARCH.md` §`## Validation
> Architecture` (`:175`), whose every command and timing is marked `[VERIFIED]` against a real run.
> This file is the execution-time contract; that file is the evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Python** | 3.11.15 — **`.venv` only.** The dev box is 3.14 and is NOT a supported target (CLAUDE.md). Never validate there. |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`:24-26`) — `testpaths = ["tests"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py` |
| **SC5 guard set** | `.venv/bin/python -m pytest -q tests/test_phase14_scoring.py tests/test_phase16_driver.py tests/test_phase16_ladder.py tests/test_phase18_corpus.py tests/test_phase18_prereg.py tests/test_phase19_erasure.py tests/test_phase14_factset.py tests/test_phase14_demo.py` |
| **Full suite command** | `make test` (`pytest -q`) |
| **Estimated runtime** | quick **3.45s** (62 passed) · SC5 guard set **~36s** (314 passed for 7 files; +`test_phase14_demo.py`) · full **195.26s** (877 passed, 1 skipped, exit 0) |

**The one skip is expected by design:** `test_loop_penalty_fn::test_golden_trajectory_bit_identity`
is platform-gated; the in-process identity tests carry the guarantee
(`tests/test_loop_penalty_fn.py:95-107`). A run reporting `877 passed, 1 skipped` is GREEN.

**CI prerequisite that is load-bearing here:** `.github/workflows/ci.yml:21` sets `fetch-depth: 0`.
`_assert_ordering_holds` asserts `rev-parse --is-shallow-repository == "false"` and refuses to skip
(`tests/test_phase20_prereg.py:136-141`) — a shallow clone turns the ancestry guard into an error,
not a silent pass.

---

## Sampling Rate

- **After every task commit:** the **quick run command** + every `tests/test_phase21_*.py` that
  exists at that point. ~3.5s.
- **After every plan wave:** the **SC5 guard set** + all `tests/test_phase21_*.py`. ~36s.
- **Before the first `results/phase21_*` COMMIT:** `pytest -q tests/test_phase20_prereg.py` must be
  **armed and green first** (1.86s / 21 tests). `git ls-files` is the guard's input, so an artifact
  becomes watched when it is **committed**, not when it is written. Arm-then-write is an ordering
  constraint on commits, and `:157` (`adds[-1]`, the earliest add) makes it irrevocable.
- **Before `/gsd:verify-work`:** full suite green — `877 passed, 1 skipped`.
- **Max feedback latency:** 36s at wave granularity; 3.5s at task granularity.

---

## Per-Task Verification Map

Task IDs are assigned by the planner. Rows below are the requirement-level contract every plan
must map its tasks onto; `File Exists` is measured against the repo as of 2026-08-22.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | UNIT-02 | — | N/A | golden fixture | `pytest -q tests/test_phase21_aligned_bins.py -k byte_identity` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | unit (non-vacuity) | `... -k align_facts_is_wired` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | content | `... -k window_purity_input` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | content | `... -k window_purity_target` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | adversarial | `... -k window_purity_adversaries` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | unit | `... -k three_bin_alignment` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 | — | N/A | integration | `pytest -q tests/test_phase21_aligned_loader.py -k grad_accum` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 (D-06) | — | fact map read on EVERY access | adversarial | `... -k consumed_at_runtime` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-02 (D-06) | — | loader RAISES on missing/truncated fact bin | unit | `... -k fact_bin_required` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-03 | — | N/A | unit | `pytest -q tests/test_phase21_multiplicity.py -k conservation` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-03 | — | N/A | adversarial | `... -k instrument_can_report_not_one` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-03 | — | N/A | unit | `... -k seed_reproducible` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-04 (D-11) | — | replay volume independent of private fact VALUES | differential | `pytest -q tests/test_phase21_replay_volume.py -k side_channel_closed` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-04 (D-24) | — | N/A | unit | `... -k window_quantized` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | N/A | unit | `pytest -q tests/test_phase21_unit_pin.py -k prove_guards` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | frozen module imports ⊆ `{pathlib, sys, erasure_gate}` | AST | `pytest -q tests/test_phase20_prereg.py -k import_graph` | ✅ covers the new module via the glob | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | guard armed BEFORE first artifact | git history | `pytest -q tests/test_phase20_prereg.py -k phase21` | ❌ W0 (two additive edits, both required) | ⬜ pending |
| TBD | TBD | TBD | UNIT-01/04/05 | — | guard proven non-vacuous | git fixture | `... -k phase21_glob_red_then_green` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-16) | — | N/A | golden fixture | `pytest -q tests/test_phase21_filler.py -k render_family_byte_identity` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-16) | — | N/A | unit (non-vacuity) | `... -k forms_is_wired` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-16) | — | filler slots DISJOINT from the 11 published slots | unit | `... -k slots_disjoint` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-17) | — | collision refusal vs the 10, the 28, and each other | unit | `... -k minting_discipline` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 (D-13) | — | filler OUTSIDE `all_pools()`; `_BY_ID` gains no keys | unit | `... -k outside_all_pools` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 (D-18) | — | no filler value reaches any published instrument | content | `pytest -q tests/test_phase21_sc5.py -k no_filler_leak` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | `scripts/phase18_extraction.py` byte-unchanged | sha256 | `... -k instruments_unchanged` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | 270-question fixture byte-unchanged | sha256 | `... -k instruments_unchanged` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | all 8 `== 10` wall sites still green | existing | the **SC5 guard set** command above | ✅ exists | ⬜ pending |
| TBD | TBD | TBD | UNIT-06 / SC5 | — | `len(LOCKED_FACTS) <= 8`, `len(SOFT_TIER_FACTS) <= 3` | existing | `pytest -q tests/test_phase14_factset.py -k composition_targets` | ✅ `tests/test_phase14_factset.py:101-103` | ⬜ pending |
| TBD | TBD | TBD | all (RPT-03) | — | `pyproject.toml` untouched — zero new deps | sha256 | `pytest -q tests/test_package.py` | ✅ `tests/test_package.py:37` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### The `== 10` wall is 8 sites across 7 files, not 4

CONTEXT.md D-18 names **four**; `21-RESEARCH.md` corrected it to **seven across six**; a direct
grep finds **eight across seven**. Any plan sampling fewer under-samples the wall SC5 rests on:

| # | Site | Variable |
|---|------|----------|
| 1 | `tests/test_phase14_scoring.py:405` | `forbidden` |
| 2 | `tests/test_phase16_driver.py:313` | `forbidden` |
| 3 | `tests/test_phase16_ladder.py:443` | `forbidden` |
| 4 | `tests/test_phase16_ladder.py:711` | `forbidden` |
| 5 | `tests/test_phase18_prereg.py:127` | `forbidden` |
| 6 | `tests/test_phase19_erasure.py:625` | `forbidden` |
| 7 | `tests/test_phase18_corpus.py:430` | `values` |
| 8 | **`tests/test_phase14_demo.py:394`** | `values` — **named in neither CONTEXT.md nor RESEARCH.md**; B-01 demo fact-freedom, same `LOCKED_FACTS + SOFT_TIER_FACTS == 10` assertion |

`tests/test_phase14_demo.py` is therefore added to the SC5 guard set above.

---

## Wave 0 Requirements

- [ ] `tests/test_phase21_aligned_bins.py` — UNIT-02 content proofs + `build_bins` golden fixture
- [ ] `tests/test_phase21_aligned_loader.py` — UNIT-02 / D-06 run-time consumption proofs
- [ ] `tests/test_phase21_multiplicity.py` — UNIT-03 instrument validation
- [ ] `tests/test_phase21_replay_volume.py` — UNIT-04 / D-11 / D-24 side-channel differential
- [ ] `tests/test_phase21_unit_pin.py` — the frozen module's `_prove` guards
- [ ] `tests/test_phase21_filler.py` — UNIT-06 corpus + `render_family` golden fixture
- [ ] `tests/test_phase21_sc5.py` — SC5 non-disturbance
- [ ] `tests/fixtures/golden_build_bins_v2.json` — captured from a **git-clean, pre-edit**
      `teach_persona.py`. Captured after the edit it proves nothing.
- [ ] `tests/fixtures/golden_render_family_v2.json` — captured from a **git-clean, pre-edit**
      `phase14_factset.py`. Same constraint.
- [ ] **Two additive edits to `tests/test_phase20_prereg.py`** (D-20) — the `V4_ARTIFACT_GLOBS`
      addition **and** a `_assert_ordering_holds(..., artifact_glob="results/phase21_*")` call.
      Neither is sufficient alone: `globs` is used only at `:129` for a consistency check and the
      ordering loop runs on the singular `artifact_glob`.

**No new framework, no new fixture infrastructure, no conftest change, no new dependency.**

### The governing rule for every byte-identity proof in this phase

> **A byte-identity assertion with no paired non-identity assertion is vacuous.** `X=None` is
> trivially satisfied by a kwarg that is never read.

Every `*_byte_identity` row above is therefore paired with an `*_is_wired` row that fails if the
kwarg is inert. This is not redundancy — it is the only thing that makes the identity claim mean
anything. **RESEARCH.md Open Question 1 is a live instance:** `render_family(...,
question_bank=None)` appears **unfalsifiable as sited** — `SLOT_QUESTION_BANK` is read only at
`phase14_factset.py:279` inside `_assign_probes()`, and `_render_family:690` reads only
`SLOT_FORMS`, so no value of that kwarg can change `render_family`'s output. The planner must
either re-site the kwarg or drop it; it must not ship a guard that cannot fail.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Arm-then-write commit ORDER for the ancestry guard | UNIT-01/04/05 (D-20) | The property is over **git history**, not over a working tree. A test can assert the ordering holds, but only the operator controls which commit lands first — and `:157` (`adds[-1]`) makes a wrong order permanent. | Land the two `test_phase20_prereg.py` edits GREEN in a commit that is a strict ancestor of the first `results/phase21_*` commit. Verify with `git merge-base --is-ancestor <pin-commit> <artifact-commit>` before committing any artifact. Note `:300-304`: `--is-ancestor X X` exits 0, so same-commit PASSES the mechanism — "strictly after" is a tighter discipline than the guard enforces, and it is deliberate. |
| `results/phase21_*` artifacts are COMMITTED, not merely written | UNIT-03 (D-26) | `git ls-files` is the guard's input. `results/` is not gitignored, but an uncommitted artifact is invisible to the guard — a silent no-op, not a failure. | After the driver writes, confirm `git ls-files results/phase21_*` is non-empty before claiming the guard covers them. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] Every `*_byte_identity` test is paired with a non-vacuity `*_is_wired` test
- [ ] Every new guard proven **deliberate-RED then byte-identically restored**
- [ ] No watch-mode flags
- [ ] Feedback latency < 36s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
