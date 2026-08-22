# Phase 21: The Privacy Unit, the DP Data Path, and the n=64 Corpus — Research

**Researched:** 2026-08-22
**Domain:** Test/validation architecture for structural proofs (pytest, git-history guards, byte-level fixtures)
**Confidence:** HIGH — every claim below was measured against this repository in this session, with the command recorded.
**Scope:** SCOPED validation pass. The design (D-01 … D-26) is CLOSED and is treated as settled input.
This file answers exactly one question: **how do we sample the behaviour space so this phase's structural
proofs are PROVABLY TESTED rather than ASSERTED?**

---

<user_constraints>
## User Constraints (from 21-CONTEXT.md)

### Locked Decisions

D-01 … D-26 are locked with 0 open questions. This research does not re-derive, re-litigate, or
"confirm" any of them. Reproduced here only to the extent the validation architecture must honour them:

- **D-01** — RAGGED shard geometry: each fact padded to its OWN `ceil(tokens / block_size)` windows.
  8 facts → `(4,4,4,4,4,5,4,4)` = 33 windows, 176 rows, 7,581 tokens, 10.26% pad.
- **D-03 / D-04** — within one fact the loss is a MEAN over its windows; costs zero new loss code
  (`data.py:125` `y[m == 0] = -100` + `gpt.py:212` default `reduction="mean"`).
- **D-05** — the aligned path carries a THIRD BIN `*_fact.bin`, `uint16`, 1:1 aligned. Every
  `block_size`-aligned window contains exactly ONE distinct fact id. **Direct proof of content, not
  inference from offsets.**
- **D-06** — the fact-id map is CONSUMED BY THE LOADER AT RUN TIME, not merely asserted at build time.
  `build_bins`' proof-1 extends from two files to three.
- **D-07 / D-10** — replay sits OUTSIDE the privacy N (`q = 1`, `N = n_facts`) and LEAVES the teaching
  bin entirely; drawn at train time from `data/dialog_train.bin` via the existing
  `get_batch_memmap_masked`.
- **D-11 / D-24 / D-25** — replay VOLUME depends only on public quantities: `4 windows per fact =
  1,024 tokens`, window-quantized, drawn in its OWN pass per lot, structurally outside the per-record
  accumulation loop.
- **D-12 … D-18** — the corpus is `8 scored LOCKED_FACTS + 56 unscored filler`. Filler lives in a NEW
  `scripts/phase21_filler.py` OUTSIDE `all_pools()`, uses a filler-only slot grammar DISJOINT from the
  8 scored slots, renders through the SAME `render_family` over `TAUGHT_FAMILY_IDS`, re-implements the
  deterministic minting discipline in full, and waives the base-model guessability probe with the
  reason recorded IN THE MODULE. "Unscored" is STRUCTURAL: no filler value may enter the 10-value leak
  vocabulary.
- **D-19 … D-23** — the constants live in a NEW `scripts/mitigation_<subject>.py`. The freeze comes
  from a hand-written explicit path constant, NOT from the filename. The module is armed NOW against
  `results/phase21_*` in the phase's FIRST plan. Joining the `mitigation_*.py` glob imposes a HARD
  IMPORT CEILING `{pathlib, sys, erasure_gate}` → `json` is unreachable → the artifact writer lives
  OUTSIDE the glob in `scripts/phase21_unit_record.py`. The unfrozen sibling is NOT created.
- **D-26** — BOTH multiplicity paths measured on an INSTRUMENTED loader at `SEED = 1337`,
  `MAX_STEPS = 200`, `BATCH_SIZE = 8`, each row labelled with its exact bin composition.

### Claude's Discretion

- The exact filename of the frozen module, constrained to match `mitigation_*.py` and to be named for
  its SUBJECT rather than its phase (`test_phase20_prereg.py:59-60`).
- The shape of every test, fixture and assertion below.

### Deferred Ideas (OUT OF SCOPE)

- The GATE-10 fallback tolerance (Phase 20 D-26) — **Phase 23**, not this phase.
- The extraction noise floor (Phase 20 D-13 / CTRL-03) — Phase 23.
- Generalizing `train()`'s replay seam to an arbitrary auxiliary-bin list.
- Re-benchmarking D-02's ratios on the real bins — belongs beside the UNIT-03 measurement, not in its
  own phase.
- **No ε is computed in this phase.**
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (REQUIREMENTS.md:89-110) | Research Support — the section that makes it testable |
|----|-------------|------------------|
| UNIT-01 | The privacy unit is **the fact**, recorded as a decision with its arithmetic | §V.3 (frozen-module guards), §V.6 (SC5 non-disturbance), §V.5 (the instrumented measurement that carries UNIT-01's indictment of the old loader) |
| UNIT-02 | Fact-aligned batching, `grad_accum_steps = n_facts`, no subsampling (q=1) | §V.1 (loader consumes the map), §V.2 (per-window content equality), §V.4 (`build_bins(..., align_facts=None)` byte-identity) |
| UNIT-03 | Effective per-fact multiplicity **measured**, not inferred | §V.5 (validating the instrument itself) |
| UNIT-04 | Recorded decision on replay in the DP lot, with its ε consequence | §V.3 (frozen module holds it), §V.4b (the D-11 side-channel differential) |
| UNIT-05 | δ pinned as the literal `1e-5`, rejected `1/N^1.1` recorded | §V.3 (in-module `_prove` guards, zero-import arithmetic) |
| UNIT-06 | n=64 corpus of **unscored filler facts** disturbing no published instrument | §V.6 (SC5 non-disturbance proof), §V.2 (the corpus renders into the aligned bins) |

**Not marked complete by this research.** That is not research's job (`<code_context>` — Over-claim avoidance).
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

| Directive | Consequence for this phase's validation |
|-----------|------------------------------------------|
| Python 3.11 venv MANDATORY; dev box is 3.14 and is NOT a supported target | Every command below is `.venv/bin/python -m pytest …`. **Measured:** the venv runs Python 3.11.15 / pytest 9.0.3 [VERIFIED: `.venv/bin/python -c "import sys,pytest;print(...)"`]. Never validate against the system 3.14. |
| `make test` is CPU-only, GPU-free | Every new test in this phase must run without MPS/CUDA. The three named proofs are all CPU-only by nature (file bytes, numpy, git). |
| No new runtime dependencies (RPT-03) | `pyproject.toml` is UNTOUCHED. `tests/test_package.py:11` pins its sha256 to `81d07d5d…2bdf` and reads it as **bytes** [CITED: tests/test_package.py:11,37]. Nothing below needs a new package. |
| From-scratch ethos, stdlib + PyTorch only | Every instrument below is `hashlib`, `pathlib`, `subprocess`+`git`, `numpy`, `ast`, `pytest` — all already imported by committed tests. |
| Offline / zero-network | No test below reaches the network. `git` operations are local-only; the throwaway-repo fixture uses `tmp_path`. |

**Project skills:** none. `ls .claude/skills .agents/skills` → both absent [VERIFIED: `ls`].

---

## Summary

The phase's design is closed; what is open is whether its three structural proofs will be *sampled* or
merely *declared*. The repo has already learned the exact failure mode twice and written the lesson
into its own tests: `tests/test_masked_batch.py:8-10` states it plainly — *"mask off-by-ones can ONLY
hide from tests that recompute the expectation"* — and `tests/test_phase14_scoring.py:352-358` records
a guard that passed while its invariant was false, because the predicate was whole-string equality
where the real leak was substring containment. Both lessons apply directly to all three of this
phase's proofs.

The single generalization that covers this whole phase: **a positive assertion whose negative case was
never observed is not evidence.** Every guard here needs a paired, committed, re-executed
deliberate-RED — not a one-time manual observation. `tests/test_phase20_prereg.py:281-330` already
demonstrates the shape at full strength (five states, each red distinguished from the others by which
assertion fired), and Phase 21 copies it rather than inventing anything.

Three measurements in this session changed what the validation architecture has to do. **(1)** The
`len(forbidden) == 10` invariant is asserted at **7 sites across 6 files**, not the 4 CONTEXT names —
so SC5's non-disturbance guard has broader existing coverage than assumed, and the sampling set must
include the 3 extra sites or it under-samples the wall it depends on. **(2)** `SLOT_QUESTION_BANK` is
read at exactly **one** site, `phase14_factset.py:279` inside `_assign_probes()`, and `_render_family`
(`:690`) reads only `SLOT_FORMS` — so a byte-identity fixture over `render_family`'s output is
*structurally incapable* of distinguishing `question_bank=None` from any other value. That half of
D-16's kwarg pair would be an untestable parameter as currently sited. **(3)** The Phase 20 ancestry
guard is **live today, not vacuous** — 9 pin commits × 3 tracked artifacts = 27 checked pairs — so the
`bool(checked) == bool(tracked_artifacts)` equivalence has already survived the artifacts' arrival
once, and Phase 21's guard will follow the same trajectory the moment its first result lands.

**Primary recommendation:** build every Phase 21 guard as a **matched pair** — the assertion plus a
committed fixture that drives it RED on a named mutation and back to GREEN on a byte-identical restore
— and site each proof at the tier that actually owns it (run time for D-06, file content for D-05,
git history for the freeze). Where CONTEXT's phrasing admits two readings (input-space vs target-space
window purity; the `question_bank` siting), assert the stricter one directly rather than inferring it.

---

## Architectural Responsibility Map

The whole phase is an argument about *which tier owns a proof*. Getting the tier wrong is how a guard
becomes vacuous without anyone noticing.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `*_fact.bin` 1:1 length equality | **Build time** (`build_bins` proof-1) | Run time (loader raises) | D-06 explicitly extends proof-1 from 2 files to 3, AND requires run-time consumption. Build time alone is the exact failure D-06 names. |
| Per-window content equality (one fact id per window) | **File content** (bytes on disk) | Build time | D-05 is a claim about *bytes*, deliberately not about offsets. The instrument is `np.fromfile` + `reshape(-1, block_size)`, not the packer's own arithmetic. |
| `grad_accum_steps = n_facts` literally true | **Run time** (loader/loop) | Build time (bin shape) | A build-time count is a declaration; the loop's actual step count is the fact. |
| Replay volume independent of private content | **Build/draw time** (differential over fact values) | — | The property is *invariance under a change of private data*. Only a differential can see it; a single-value assertion cannot. |
| Frozen-module immutability | **Git history** (`git log --` on the pin) | File content (import-graph AST scan) | `test_phase20_prereg.py:143,157` — the freeze is a history property. No file-content check can express "never edited after". |
| Import ceiling `{pathlib, sys, erasure_gate}` | **File content** (AST) | — | `:498,:522` accumulate `imported` across the whole glob. Already enforced; the new module joins for free. |
| "Unscored" filler | **File content** (substring scan) + **git history** (pin untouched) | Build time (collision refusal) | D-18's structural definition is about which strings reach which files. |
| Byte-identity of a default-`None` kwarg | **File bytes** (sha256) + **in-process identity** | — | `build_bins` writes to disk, so a file hash is directly available — the strongest available instrument. |
| Multiplicity measurement | **Run time**, instrumented | Analytic (as a cross-check only) | UNIT-03 explicitly refuses the analytic number as the artifact. |

---

## Premise Checks Run This Session

CONTEXT.md's own carried lesson is *state the position, name the premise, measure the premise* — and
the discipline note for this pass extends it to premises about the **test infrastructure**, because
the validation architecture rests on them. Six were checkable cheaply. **Four survived. Two did not.**

| # | Stated premise | Verdict | Measurement |
|---|---|---|---|
| P1 | D-18: "**Four** tests assert `len(forbidden) == 10`" at `test_phase14_scoring.py:405`, `test_phase16_driver.py:313`, `test_phase16_ladder.py:443`, `test_phase18_corpus.py:430` | **FALSE — undercount.** 7 sites / 6 files. The 4 named lines are all real; 3 more exist. `test_phase18_corpus.py:430` asserts `len(values) == 10` (variable named `values`, not `forbidden`) — the line is right, the prose name is off. | `grep -rn "len(forbidden)" tests/ scripts/ src/` → 6 hits; `sed -n '425,440p' tests/test_phase18_corpus.py` → the 7th |
| P2 | D-16: `render_family` gains `forms=None` / `question_bank=None`, byte-identical when `None` | **HALF FALSE.** `forms` is genuine — `_render_family:690` reads `SLOT_FORMS[fact.slot]`. `question_bank` is **not read by `render_family` at all**: `SLOT_QUESTION_BANK` has exactly 3 occurrences — `:55` (a comment), `:151` (the definition), `:279` (the sole read, inside `_assign_probes()`, which iterates `all_pools()`). | `grep -n "SLOT_QUESTION_BANK" scripts/phase14_factset.py`; `sed -n '265,300p'`; `sed -n '685,700p'` |
| P3 | D-20 / `:129`: `globs` is used ONLY for the `assert artifact_glob in globs` consistency check; the loop runs on singular `artifact_glob` | **TRUE.** `globs` appears exactly once in the function body (`:129`); `artifact_glob` drives `git ls-files` at `:150`. | `grep -n "V4_ARTIFACT_GLOBS\|artifact_glob" tests/test_phase20_prereg.py` |
| P4 | D-20 / `:300-304`: `git merge-base --is-ancestor X X` exits **0**, so pin and artifact in the SAME commit PASS | **TRUE.** Exit 0 measured against this repo's HEAD. | `H=$(git rev-parse HEAD); git merge-base --is-ancestor "$H" "$H"; echo $?` → `0` |
| P5 | D-19: the `_MITIGATION_GATE_PATH`-singular scans at `:740`, `:805`, `:928`, `:991` do NOT extend to siblings | **TRUE.** All four read `_tree(_MITIGATION_GATE_PATH)`. Only `:498` iterates `_GATE_MODULES`. | `sed -n` at each of the four sites |
| P6 | `test_phase20_prereg.py:281-296` docstring: the live ordering guard is "vacuous today by construction" | **NO LONGER TRUE — and this is good news.** 9 commits touch `scripts/mitigation_gate.py`; 3 `results/phase20_*` artifacts are tracked → `checked = 27`. The guard is LIVE and the `bool(checked) == bool(tracked_artifacts)` equivalence has already survived the transition once. | `git log --format=%H -- scripts/mitigation_gate.py \| wc -l` → 9; `git ls-files 'results/phase20_*' \| wc -l` → 3 |

**Two more measurements, taken because a test design depends on them:**

| # | Question | Measured answer |
|---|---|---|
| P7 | Does a freshly-opened `np.memmap(mode="r")` in the SAME process see a mutation written to the file after the first open? (Proof 1's whole design hinges on this.) | **YES.** Write 16 `uint16`, memmap-read → `[3] == 3`; rewrite file with `[3] = 999`; fresh memmap-read → `[3] == 999`. Measured on this platform/numpy. [VERIFIED: scratch script, Darwin 25.5.0, venv numpy] |
| P8 | Does every taught episode begin with `mask[0] == 0`? (Determines whether target-space window purity *follows* from input-space purity.) | **YES — 176/176.** All 8 `LOCKED_FACTS` × 5 `TAUGHT_FAMILY_IDS` = 176 episodes, zero with `mask[0] != 0`. Sample episode: 31 tokens, first non-zero mask at index 18, mask sum 13, `mask[-1] == 1`. **176 / 8 = 22 rows per fact — independently reconfirms D-01's row count from a different probe.** |

---

## Validation Architecture

### Test Framework

| Property | Value | Provenance |
|----------|-------|-----------|
| Framework | pytest 9.0.3 | [VERIFIED: `.venv/bin/python -c "import pytest;print(pytest.__version__)"`] |
| Python | 3.11.15 (venv). System is 3.14 — **never validate there** | [VERIFIED: same command] · [CITED: CLAUDE.md] |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests"]`, `pythonpath = ["."]` | [CITED: pyproject.toml:24-26] |
| Dependency pin | `dev = ["pytest~=9.0", "ruff~=0.15", "tiktoken~=0.13", "isort~=8.0"]`; whole file sha256-pinned | [CITED: pyproject.toml:19; tests/test_package.py:11] |
| Quick run command | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py` — **62 passed in 3.45s** | [VERIFIED: timed run] |
| SC5 guard set | `.venv/bin/python -m pytest -q tests/test_phase14_scoring.py tests/test_phase16_driver.py tests/test_phase16_ladder.py tests/test_phase18_corpus.py tests/test_phase18_prereg.py tests/test_phase19_erasure.py tests/test_phase14_factset.py` — **314 passed in 36.02s** | [VERIFIED: timed run] |
| Full suite command | `make test` (`pytest -q`). **877 passed, 1 skipped in 195.26s** (0:03:15); 878 collected | [VERIFIED: full run this session, exit 0] · [CITED: Makefile:13-14] |
| CI | `.github/workflows/ci.yml` — `fetch-depth: 0` (`:21`), Python 3.11 (`:26`), `pip install -e ".[cpu,dev,demo]"` (`:36`) | [CITED: .github/workflows/ci.yml:21,26,36] |
| Ancestry-guard prerequisite | `fetch-depth: 0` is **load-bearing**: `_assert_ordering_holds` asserts `rev-parse --is-shallow-repository == "false"` and refuses to skip | [CITED: tests/test_phase20_prereg.py:136-141] |

**No new dependency is required by anything in this document.** Every instrument is `hashlib`,
`pathlib`, `subprocess`+`git`, `numpy`, `ast`, `json` (driver only), `pytest`.

### Phase Requirements → Test Map

`✅` = an existing test already covers it. `❌ Wave 0` = a new test file/function is required.

| Req | Behaviour to sample | Type | Automated command | Exists? |
|-----|---------------------|------|-------------------|---------|
| UNIT-02 | `build_bins(..., align_facts=None)` bins byte-identical to today | golden fixture | `pytest -q tests/test_phase21_aligned_bins.py -k byte_identity` | ❌ Wave 0 |
| UNIT-02 | `align_facts=<facts>` **changes** the output (non-vacuity of the above) | unit | same file, `-k align_facts_is_wired` | ❌ Wave 0 |
| UNIT-02 | Every `block_size` window holds exactly one fact id — **input space** | content | same file, `-k window_purity_input` | ❌ Wave 0 |
| UNIT-02 | Same, **target space** (`fact[s+1 : s+1+B]` where `m != 0`) | content | same file, `-k window_purity_target` | ❌ Wave 0 |
| UNIT-02 | Offset-correct / bytes-wrong adversary FAILS the content check | adversarial | same file, `-k window_purity_adversaries` | ❌ Wave 0 |
| UNIT-02 | Three-bin 1:1 length equality (proof-1 extended) | unit | same file, `-k three_bin_alignment` | ❌ Wave 0 |
| UNIT-02 | `grad_accum_steps == n_facts` observed from the loop, not declared | integration | `pytest -q tests/test_phase21_aligned_loader.py -k grad_accum` | ❌ Wave 0 |
| UNIT-02 / D-06 | Loader **consumes** the fact map on every access (mutate-between-calls) | adversarial | `tests/test_phase21_aligned_loader.py -k consumed_at_runtime` | ❌ Wave 0 |
| UNIT-02 / D-06 | Loader **raises** on a missing / truncated / mis-length fact bin | unit | same file, `-k fact_bin_required` | ❌ Wave 0 |
| UNIT-03 | Instrument conservation law: `sum(counts)` equals the exact draw budget | unit | `tests/test_phase21_multiplicity.py -k conservation` | ❌ Wave 0 |
| UNIT-03 | Instrument reports ≠1 on a deliberately mis-built aligned bin | adversarial | same file, `-k instrument_can_report_not_one` | ❌ Wave 0 |
| UNIT-03 | Same seed → byte-identical counts (the record is regenerable) | unit | same file, `-k seed_reproducible` | ❌ Wave 0 |
| UNIT-04 / D-11 | Replay volume **invariant** under a change of fact values at fixed `n_facts` | differential | `tests/test_phase21_replay_volume.py -k side_channel_closed` | ❌ Wave 0 |
| UNIT-04 / D-24 | Replay volume is `4 × n_facts` windows = `1024 × n_facts` tokens at n=8 and n=64 | unit | same file, `-k window_quantized` | ❌ Wave 0 |
| UNIT-01/04/05 | Frozen module's `_prove` guards: δ·N at N=8 and N=64, both recipes | unit | `tests/test_phase21_unit_pin.py -k prove_guards` | ❌ Wave 0 |
| UNIT-01/04/05 | Frozen module import ceiling ⊆ `{pathlib, sys, erasure_gate}` | AST | `pytest -q tests/test_phase20_prereg.py -k import_graph` | ✅ **already covers the new module via the glob** |
| UNIT-01/04/05 | Ancestry guard armed against `results/phase21_*` **before** any artifact | git history | `tests/test_phase20_prereg.py -k phase21` | ❌ Wave 0 (two additive changes, both required) |
| UNIT-01/04/05 | The phase21 guard proven RED-then-GREEN in a throwaway repo | git fixture | `tests/test_phase20_prereg.py -k phase21_glob_red_then_green` | ❌ Wave 0 |
| UNIT-06 / D-16 | `render_family(..., forms=None)` byte-identical, both registers | golden fixture | `tests/test_phase21_filler.py -k render_family_byte_identity` | ❌ Wave 0 |
| UNIT-06 / D-16 | `forms=<modified>` **changes** the output (non-vacuity) | unit | same file, `-k forms_is_wired` | ❌ Wave 0 |
| UNIT-06 / D-16 | Filler slots DISJOINT from the 11 published slots | unit | same file, `-k slots_disjoint` | ❌ Wave 0 |
| UNIT-06 / D-17 | `token_census` round-trip + collision refusal vs the 10, the 28, and each other | unit | same file, `-k minting_discipline` | ❌ Wave 0 |
| UNIT-06 / D-13 | Filler is OUTSIDE `all_pools()`; `_BY_ID` and `GATE_PROBES` gain no filler keys | unit | same file, `-k outside_all_pools` | ❌ Wave 0 |
| UNIT-06 / D-18 (SC5) | No filler value reaches any published instrument (substring scan) | content | `tests/test_phase21_sc5.py -k no_filler_leak` | ❌ Wave 0 |
| UNIT-06 / SC5 | `scripts/phase18_extraction.py` byte-unchanged | sha256 | same file, `-k instruments_unchanged` | ❌ Wave 0 |
| UNIT-06 / SC5 | `results/phase16_recall_sample.json` (270 questions) byte-unchanged | sha256 | same file, `-k instruments_unchanged` | ❌ Wave 0 |
| UNIT-06 / SC5 | All 7 `len(forbidden) == 10` sites still green | existing | the **SC5 guard set** command above | ✅ **exists — 314 tests / 36.02s** |
| UNIT-06 / SC5 | `len(LOCKED_FACTS) <= 8`, `len(SOFT_TIER_FACTS) <= 3` | existing | `pytest -q tests/test_phase14_factset.py -k composition_targets` | ✅ [CITED: tests/test_phase14_factset.py:101-103] |
| all | `pyproject.toml` untouched (RPT-03) | sha256 | `pytest -q tests/test_package.py` | ✅ [CITED: tests/test_package.py:37] |

### Sampling Rate

| When | Command | Cost |
|------|---------|------|
| **Per task commit** | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_package.py tests/test_masked_batch.py tests/test_phase14_teaching.py` **+ the new `tests/test_phase21_*.py` files** | 3.45s today [VERIFIED] |
| **Per wave merge** | the **SC5 guard set** (7 files) + all `tests/test_phase21_*.py` | 36.02s today for the 7 [VERIFIED] |
| **Phase gate** | `make test` — full suite green before `/gsd:verify-work` | **195.26s / 877 passed, 1 skipped** [VERIFIED: full run, exit 0]. The single skip is `test_loop_penalty_fn::test_golden_trajectory_bit_identity` on a non-capture platform — expected by design; the in-process identity tests carry the guarantee (`test_loop_penalty_fn.py:95-107`). |
| **Before the first `results/phase21_*` commit** | `pytest -q tests/test_phase20_prereg.py` — the ordering guard must be armed AND green **first**. Once an artifact lands the freeze is irrevocable (`:157` `adds[-1]`). | 1.86s for 21 tests [VERIFIED] |

**The ordering constraint is not a preference.** `git ls-files` is the guard's input, so an artifact
becomes watched at the moment it is **committed**, not written. Arm-then-write means: the two
`test_phase20_prereg.py` edits land and go green in a commit that is a strict ancestor of the first
`results/phase21_*` commit.

### Wave 0 Gaps

- [ ] `tests/test_phase21_aligned_bins.py` — UNIT-02 content proofs + `build_bins` golden fixture
- [ ] `tests/test_phase21_aligned_loader.py` — UNIT-02/D-06 run-time consumption proofs
- [ ] `tests/test_phase21_multiplicity.py` — UNIT-03 instrument validation
- [ ] `tests/test_phase21_replay_volume.py` — UNIT-04/D-11/D-24 side-channel differential
- [ ] `tests/test_phase21_unit_pin.py` — the frozen module's `_prove` guards
- [ ] `tests/test_phase21_filler.py` — UNIT-06 corpus + `render_family` golden fixture
- [ ] `tests/test_phase21_sc5.py` — SC5 non-disturbance
- [ ] `tests/fixtures/golden_build_bins_v2.json` — captured from git-clean pre-edit `teach_persona.py`
- [ ] `tests/fixtures/golden_render_family_v2.json` — captured from git-clean pre-edit `phase14_factset.py`
- [ ] **Two additive edits** to `tests/test_phase20_prereg.py` (D-20 — both required, neither sufficient)

**No new framework, no new fixture infrastructure, no conftest change.** Every file above uses idioms
already committed in this repo.

---

## §V.1 — Proof 1: `*_fact.bin` is CONSUMED BY THE LOADER AT RUN TIME (D-06)

### The observable

The claim is not "the fact bin exists" and not "the fact bin was once correct." It is: **the loader's
output is a function of the fact bin's current on-disk contents, evaluated on every access.**

That phrasing names the instrument directly. A test can only distinguish run-time consumption from a
past build-time check by making the *only* thing that changes be the fact bin, *after* the build, and
observing the loader's behaviour change.

### Why the obvious test fails

A test that builds bins and asserts the loader returns fact-aligned batches passes identically whether
the loader reads `*_fact.bin` or reconstructs the boundaries from its own copy of the padded lengths.
Both produce the same batches on a correctly-built corpus. The test has one input class and cannot
separate two implementations.

Same for "the third bin exists and is the right length": that is `build_bins` proof-1 extended, a
**build-time** check, and D-06 is explicitly the claim that build time is not enough.

### The decisive sampling strategy: mutate between two calls in one process

`get_batch_memmap_masked` re-opens both memmaps on **every call** (`data.py:110-111`) — an explicit,
documented design choice (the nanoGPT RSS-leak fix, `data.py:98-99`). The sibling must do the same for
all three bins. That gives a discriminator no build-time check can pass:

1. Build a small aligned corpus. Call the loader once, seeded; record the output.
2. **Without rebuilding**, overwrite `*_fact.bin` on disk so one window now carries two ids.
   Leave the token bin and the mask bin byte-identical (assert their sha256 before and after).
3. Call the loader again with the same seed.

**Assertion:** call 2 raises (or returns a demonstrably different attribution). If the loader ignores
the fact bin, call 2 is identical to call 1 → RED, and the RED means exactly "the map is not consumed."

**This is mechanically viable on this platform** — measured, not assumed: a fresh
`np.memmap(path, mode="r")` opened in the same process after an on-disk rewrite returns the **new**
bytes (`[3]` went `3 → 999`) [VERIFIED: scratch probe, Darwin 25.5.0, venv numpy]. Without that
measurement the whole design would be a guess about page-cache behaviour.

A weaker but complementary variant, if the loader's public output does not expose attribution: expose
the per-micro-step fact id the loader used (the aligned path needs it anyway to make
`grad_accum_steps = n_facts` meaningful) and assert *that* changes.

### The adversarial set that makes it non-vacuous

| # | Mutation (fact bin only) | Expected | What it separates |
|---|---|---|---|
| N1 | Fact bin **deleted** | loader raises, naming the path | "silently drops the third bin" — the failure mode the objective names |
| N2 | Fact bin **truncated by 1** | loader raises a length-mismatch, naming all three lengths | proof-1 extended from 2 files to 3; the existing 2-file raise is at `data.py:112-116` |
| N3 | Fact bin **rolled by 1** (same length, same multiset of ids) | loader raises / reports impurity | length checks and multiset checks both pass → only a positional read catches it |
| N4 | One interior element flipped to a neighbouring fact's id | loader raises / reports impurity on exactly one window | the sharpest single-byte discriminator |
| N5 | Fact bin **unmutated** (negative control) | loader returns normally | without this, a guard that always raises would pass N1–N4 |
| N6 | Token bin mutated, fact bin untouched | fact-attribution is **unchanged** | proves the guard reads the *fact* bin and not the token bin |

N5 and N6 are the two that stop the test being "assert it raises." N5 is the standard negative
control; N6 is the one that is easy to omit and the one that proves *which* file is being read.

### Executor-writable assertions

```python
# tests/test_phase21_aligned_loader.py
def test_fact_map_is_consumed_at_runtime(tmp_path):
    bins = _build_tiny_aligned_corpus(tmp_path)          # token, mask, fact
    tok_sha, mask_sha = _sha(bins.tokens), _sha(bins.mask)

    first = get_batch_fact_aligned(**bins, step=0)        # seeded, deterministic

    fact = np.fromfile(bins.fact, dtype=np.uint16)
    fact[BLOCK_SIZE // 2] = fact[BLOCK_SIZE // 2] + 1     # N4: one interior byte
    fact.tofile(bins.fact)

    assert _sha(bins.tokens) == tok_sha                   # ONLY the fact bin moved
    assert _sha(bins.mask) == mask_sha

    with pytest.raises(ValueError) as impure:
        get_batch_fact_aligned(**bins, step=0)
    assert "fact" in str(impure.value).lower()            # name the failing bin, not "something raised"

    # byte-identical restore — the guard returns GREEN, proving the RED was the mutation
    fact[BLOCK_SIZE // 2] = fact[BLOCK_SIZE // 2] - 1
    fact.tofile(bins.fact)
    assert _sha(bins.fact) == original_fact_sha           # captured before the mutation
    assert get_batch_fact_aligned(**bins, step=0) == first
```

The final three lines are the deliberate-RED-then-byte-identical-restore discipline made mechanical:
the restore is proven byte-identical by **sha256 of the file**, not by "we put the value back."

### Deliberate-RED for this guard

**Mutation that makes it RED:** in the loader, delete the `np.memmap(fact_path, …)` line and derive
the fact boundaries from `np.cumsum(padded_lengths)` instead. **Observable:** the mutate-between-calls
test returns `first == second` → RED. **Restore proof:** `git stash` / re-apply, then
`sha256(src/personacore/training/data.py)` equals the value recorded before the mutation.

---

## §V.2 — Proof 2: the per-window content-equality guard (D-05)

### The observable

`fact_bin` reshaped to `(-1, block_size)`: **every row has exactly one distinct value.** The
instrument is `np.fromfile` on the committed bytes, never the packer's return value and never the
packer's arithmetic.

### The one-line statement of the trap

`tests/test_masked_batch.py:8-10` already wrote it for a different invariant and it transfers verbatim:

> *"hand-built exactness fixtures (Pitfall 14 — mask off-by-ones can ONLY hide from tests that
> recompute the expectation): both the token/mask arrays AND the expected final `y` tensor are
> hand-written literals, never derived in-test from the mask."*

Applied here: **a window-purity check that derives its expected fact-id array from the same cumulative
padded lengths the packer used is not a content check. It is the offset check wearing a different
name.** The expected array in the adversarial fixture must be a hand-written literal.

### Minimum adversarial input set separating offset-pass from content-fail

Let `B = block_size`. Use a toy `B` (e.g. 4) and 3 facts of lengths `(5, 3, 6)` → padded windows
`(2, 1, 2)` → a 5-window, 20-element fact bin. Small enough to write the expected literal by hand.

| # | Input | Offset check (boundaries from cumulative padded lengths) | Content check (`unique(row).size == 1`) | Separates |
|---|-------|---|---|---|
| A0 | Correct bin: `[0,0,0,0, 0,0,0,0, 1,1,1,1, 2,2,2,2, 2,2,2,2]` | PASS | PASS | negative control — without it a guard that always fails passes A1–A4 |
| **A1** | **Rolled by 1**: `[2,0,0,0, 0,0,0,0, 0,1,1,1, 1,2,2,2, 2,2,2,2]` | **PASS** — length, window count, run-length multiset all unchanged | **FAIL** — 3 impure rows | **the load-bearing case.** Correct offsets, wrong bytes. |
| **A2** | **One interior flip**: `fact[5] = 1` | **PASS** — boundaries untouched | **FAIL** — exactly row 1 | single-byte packing bug; the finest resolution the guard has |
| A3 | **Boundary flip**: `fact[7] = 1` (last slot of fact 0's 2nd window) | PASS | FAIL — row 1 | the padding-labelling error specifically (see the derived constraint below) |
| A4 | **Truncated by 1** (19 elements) | FAIL (length) | FAIL (`len % B != 0`) | proof-1 extended; fires a *different* assertion — the message must say which |
| A5 | **Content pure, count wrong**: 4 windows of one id where 5 were expected | FAIL | PASS | proves the two checks are complementary, not redundant — content purity alone does not pin `n_facts` |

**A1 is the minimum adversarial input that satisfies the objective's exact requirement.** It is the
only mutation in this set that a correctly-implemented offset check cannot see: it preserves length,
window count, the number of distinct ids, and the multiset of run lengths. Only a positional read of
the bytes catches it.

A5 is the mirror and is worth including because it stops the plan collapsing the two checks into one.

### The derived constraint the guard forces (state it, don't discover it in code review)

D-01 pads each fact to its own whole windows; D-05 demands exactly ONE distinct id per window.
Together these force: **padding slots inside a fact's final window must carry that fact's own id.**

- A reserved sentinel would put 2 distinct ids in every fact's last window → D-05 unsatisfiable.
- Sentinel `0` additionally **collides with fact index 0** in a `uint16` map.
- The padding is masked to 0 anyway (`y[m == 0] = -100`, `data.py:125`), so it contributes nothing to
  the loss and the id it carries is purely an accounting label.

This is a consequence, not a decision — but it must be written into the test as an explicit assertion
(`fact[pad_slice] == owner_id`), because otherwise the first implementation to use a sentinel makes
the purity guard permanently unsatisfiable and the debugging path is long.

### The reading CONTEXT's phrasing leaves open: input space vs target space

D-05 says "every `block_size`-aligned window". The loss is computed in **target space**:
`get_batch_memmap_masked` takes `x = data[i : i+B]` but `y = data[i+1 : i+1+B]` and
`m = mask[i+1 : i+1+B]`, and `data.py:103-105` says so in the code's own words — *"target-space
semantics, D-01."*

So there are two distinct claims:

- **(a) input space** — `fact[s : s+B]` is pure.
- **(b) target space** — `fact[s+1 : s+1+B]` is pure at every position where `m != 0`.

**(b) is the one an ε rests on**, because (b) is what says no other record's token contributed to this
record's gradient.

Measured: (b) currently *follows* from (a) via three premises — (i) every episode begins with
`mask[0] == 0` (**176/176 measured**, all 8 `LOCKED_FACTS` × 5 `TAUGHT_FAMILY_IDS`), (ii) padding is
mask-0, (iii) a fact's final window ends in padding. So at a fact boundary the shifted target is
always `-100`.

**But that is a three-premise inference, and D-05's entire stance is "direct proof of content, not
inference."** The direct assertion costs one extra reshape and removes all three premises:

```python
target_fact = fact_bin[1:1 + n_windows * B].reshape(-1, B)
target_mask = mask_bin[1:1 + n_windows * B].reshape(-1, B)
for row_f, row_m in zip(target_fact, target_mask):
    assert np.unique(row_f[row_m != 0]).size <= 1
```

Note the extrapolation risk the direct form removes: premise (i) was measured over **8** facts. The
n=64 arm renders 56 more facts through the same path. Asserting (b) directly over whatever facts the
arm actually built is invariant to that; inferring it from an n=8 measurement is not.

### Executor-writable assertions

```python
# tests/test_phase21_aligned_bins.py
BLOCK = 4
# HAND-WRITTEN LITERAL — never derived from lengths (test_masked_batch.py:8-10)
GOOD  = np.array([0,0,0,0, 0,0,0,0, 1,1,1,1, 2,2,2,2, 2,2,2,2], dtype=np.uint16)
ROLL1 = np.roll(GOOD, 1)                       # A1
FLIP  = GOOD.copy(); FLIP[5] = 1               # A2

def _impure_rows(fact, block):
    assert len(fact) % block == 0, f"fact bin is {len(fact)} elements, not a multiple of {block}"
    rows = fact.reshape(-1, block)
    return [i for i, r in enumerate(rows) if np.unique(r).size != 1]

@pytest.mark.parametrize("bin_,expected", [(GOOD, []), (ROLL1, [0, 2, 3]), (FLIP, [1])])
def test_window_purity_separates_offsets_from_content(bin_, expected):
    assert _impure_rows(bin_, BLOCK) == expected

def test_offsets_alone_cannot_see_the_roll():
    # The offset-derived check that ROLL1 defeats — asserted PASSING, so the separation is
    # OBSERVED rather than argued.
    assert len(ROLL1) == len(GOOD)
    assert sorted(np.bincount(ROLL1)) == sorted(np.bincount(GOOD))
    assert len(ROLL1) % BLOCK == len(GOOD) % BLOCK == 0
```

`test_offsets_alone_cannot_see_the_roll` is the part that turns a claim into evidence: it *asserts the
weak check passes* on the adversary the strong check catches. Without it, "an offset check would miss
this" is prose.

### Deliberate-RED for this guard

**Mutation:** replace `np.unique(r).size != 1` with `len(r) != block`. **Observable:** the `ROLL1` and
`FLIP` parametrizations return `[]` → RED on two of three cases while `GOOD` stays green — proving the
parametrization discriminates rather than the assertion being universally true. **Restore proof:**
sha256 of the test file back to the recorded value.

---

## §V.3 — Proof 3: the irrevocable freeze of the new `mitigation_*.py` module (D-19, D-20, D-22, D-23)

### What is already enforced for free (do not rebuild it)

The moment `scripts/mitigation_<subject>.py` exists it joins `_GATE_MODULES`
(`test_phase20_prereg.py:72`, a `scripts/mitigation_*.py` glob) and inherits, with **zero new test
code**:

| Guard | Site | What it gives the new module |
|-------|------|------------------------------|
| Import-graph subset scan | `:474-579` | `imported` accumulates across **all** glob members (`:498`), asserted `⊆ {"pathlib","sys","erasure_gate"}` (`:522`). D-22's ceiling is enforced by an existing test. |
| Classic-offender scan | `:528-533` | `{"scipy","numpy","torch"} & imported` must be empty, named separately so the message says which. |
| `from erasure_gate import` exact-equality | `:538` | Exactly five names. A **subset** import by the new module is a no-op; a sixth name is RED. |
| `mitigation_budget` non-import | `:511` | The gate/budget separation extends to siblings automatically. |
| Glob non-collapse | `:445-449` (`_collapsed_glob_guard`) | A broken glob is caught rather than silently making every scan green. |
| Leading-underscore exclusion | `:638` | `_prose.py` stays out; the naming convention is asserted, not assumed. |

**Measured and confirmed:** the four content scans that read `_MITIGATION_GATE_PATH` **singular**
(`:740`, `:805`, `:928`, `:991`) do **not** reach a sibling — all four call
`_tree(_MITIGATION_GATE_PATH)`. D-19's table is accurate. The new module is *protected but not
over-constrained*, exactly as D-19/D-21 describe, and that is the repo's default state rather than
something to build.

### The two halves that are NOT free (D-20 — both required)

1. `V4_ARTIFACT_GLOBS` gains `"results/phase21_*"` (Phase 20 D-33).
2. A new test calls
   `_assert_ordering_holds(root=_ROOT, prereg_artifact=<the new module>, artifact_glob="results/phase21_*", globs=V4_ARTIFACT_GLOBS)`.

**Measured:** `globs` is referenced exactly once inside `_assert_ordering_holds` — the
`assert artifact_glob in globs` consistency check at `:129`. The loop runs on `artifact_glob`
**singular** at `:150`. So half 1 alone enforces nothing; half 2 alone fails at `:129`. Neither is
sufficient; both are necessary.

### The vacuity problem, and why the existing fixture is the answer

An ordering guard armed before any artifact exists is **green having compared nothing**:
`checked == len(prereg_commits) * 0 == 0`. Reading the pattern and confirming it bites are different
acts.

Two things stop the vacuity surviving:

- **In the live guard:** `assert bool(checked) == bool(tracked_artifacts)` (`:176-183`) — the first
  committed artifact makes a still-empty match set RED instead of quietly green.
- **In a committed fixture:** `test_phase20_glob_sees_the_phase20_prefix_red_then_green`
  (`:281-441`) drives the guard through five states in a throwaway repo.

**Measured, and it changes how this should be read:** the Phase 20 live guard is **no longer
vacuous** — 9 commits touch `scripts/mitigation_gate.py`, 3 `results/phase20_*` artifacts are tracked,
so `checked = 27` today. The docstring's *"vacuous today by construction"* is historical. The
equivalence assertion has already carried the transition once, in production, on this repository.

### The throwaway-repo fixture shape Phase 21 copies

Copy `:281-441` verbatim with `phase20_` → `phase21_` and the new pin path. The five states, and why
each exists:

| State | Setup | Expected | Assertion that makes it non-vacuous |
|-------|-------|----------|-------------------------------------|
| 1 | Commit `results/phase21_probe.json`. **No pin.** | `AssertionError` | `assert PHASE21_PREREG_ARTIFACT in str(excinfo.value)` — the expected red is the `assert prereg_commits` branch, **not** "something raised". Distinguishing the two reds is the point. |
| 2 | Commit the pin **second** (the forbidden order) | `subprocess.CalledProcessError` | `assert _git("ls-files","results/phase21_*",cwd=tmp) == ["results/phase21_probe.json"]` **first** — this is *the positive observation of the prefix*, not an inference from the pattern's text. Then `assert tuple(exc.value.cmd[:3]) == ("git","merge-base","--is-ancestor")` — otherwise any git failure anywhere satisfies `raises`. |
| 3 | `git rm` the probe | **GREEN** at `tracked = 0` | Proves the red is reversible **only** by having no artifact. |
| 4 | Re-add at the **identical path** | `CalledProcessError` again | `assert len(adds) == 2` and `assert adds[-1] == state1_add` — **laundering is impossible**, measured across a real delete-and-re-add cycle. |
| 5 | Remove the probe; commit a real-shaped `results/phase21_*` artifact **after** the pin | **GREEN**, `checked` non-zero | The GREEN half of RED-then-GREEN. |

**Three properties of this fixture the objective asks about explicitly:**

- **It proves the guard is LIVE rather than VACUOUS** because state 2's failure is *unreachable*
  unless `git ls-files "results/phase21_*"` matched. The prefix is observed matching, not read.
- **It runs against the SAME `_assert_ordering_holds`**, parameterized on `root` (`:121`). A lookalike
  copy would prove something about a different function (`:296-298` says so in its own words).
- **The real repository's history is never touched.** Everything is under `tmp_path`; no `shell=True`,
  no `rm -rf`. A `phase21_`-named probe reaching the real history would permanently corrupt the
  evidence this phase exists to produce. The plan should assert the invariant
  `git log --diff-filter=A -- 'results/phase21_*'` is EMPTY on the real repo before and after.

### Reflexivity — carry it forward as a written note, not a discovery

**Measured on this repository:** `git merge-base --is-ancestor $HEAD $HEAD` exits **0**. Pin and
artifact in the SAME commit therefore **PASS**. "Strictly after" is a discipline tighter than the
mechanism enforces. Copy that note into the Phase 21 fixture docstring so a later reader reads it as
neither a defect nor a licence — that is the phrasing `:300-304` already chose and it earned its
place.

### Non-vacuity for the pin's own content (`_prove` guards)

D-23's δ arithmetic needs **no import** (`N ** -1.1` is an operator), which is what makes it fit the
ceiling. Sample it at both capacities this milestone runs — a guard checked at one capacity is a guard
that has not been asked the question twice:

```python
# tests/test_phase21_unit_pin.py
@pytest.mark.parametrize("n,expect_pass", [(8, True), (64, True)])
def test_pinned_delta_passes_its_own_assertion(n, expect_pass):
    assert (pin.DELTA * n < 0.01) is expect_pass

@pytest.mark.parametrize("n,delta_n,ratio", [(8, 0.812252, 81.2), (64, 0.659754, 66.0)])
def test_rejected_recipe_fails_its_own_assertion(n, delta_n, ratio):
    rejected = n ** -1.1
    assert rejected * n == pytest.approx(delta_n, rel=1e-5)
    assert rejected * n >= 0.01                       # the self-contradiction, asserted
    assert (rejected * n) / 0.01 == pytest.approx(ratio, rel=1e-2)
```

The `n=64` row is the one that matters most: it converts "the recipe is wrong at the small capacity"
into "the recipe is wrong at **both** capacities this milestone runs" — a strictly stronger record,
and one a single-N test cannot make.

### Deliberate-RED for this guard

**Mutation:** in the new test, change `artifact_glob="results/phase21_*"` to `"results/phase20_*"`.
**Observable:** the test still passes (both are in `V4_ARTIFACT_GLOBS` after the D-33 addition) but
now guards the wrong prefix — which is precisely why the throwaway fixture's state-2 `ls-files`
assertion is mandatory: with it, the mutation is caught; without it, it is invisible.
**Second mutation:** revert the `V4_ARTIFACT_GLOBS` addition while keeping the new test → RED at
`:129` with the "watching two different sets of paths" message. This is the cheapest demonstration
that both halves are load-bearing.
**Restore proof:** `sha256(tests/test_phase20_prereg.py)` back to the value recorded before.

---

## §V.4 — The byte-identity proofs

### The generalization that governs all of them

**A byte-identity assertion with no paired non-identity assertion is vacuous.** "Byte-identical when
`None`" is trivially satisfied by a kwarg that is never read at all. Every `X=None` byte-identity test
in this phase must be a **pair**:

1. `f(...)` ≡ `f(..., X=None)` ≡ the golden fixture — byte-for-byte.
2. `f(..., X=<a real value>)` ≠ the golden fixture — **and asserted to differ in a named way.**

Half 2 is the one that is easy to skip and the one that proves the parameter exists.

### §V.4a — `build_bins(..., align_facts=None)`

**`build_bins` writes bins to disk — so a byte-level file hash IS the right instrument, and it is the
strongest one available.** `ids_all.tofile(bin_path)` / `mask_all.tofile(mask_path)`
(`teach_persona.py:277-278`). No float kernel sits between the input and those bytes: the path is
`encode_dialogue` → `np.asarray(uint16/uint8)` → `np.concatenate` → `tofile`. This is integer-exact
and platform-stable, which means **no platform gate is needed** — unlike
`tests/test_loop_penalty_fn.py:95-107`, whose gate exists because fp32 transcendental kernels drift
across OS/arch/BLAS/torch versions.

Two floats *do* appear, but only in the returned stats dict: `float(np.mean(mask))` and
`float(np.mean(lengths))` (`teach_persona.py:269, 316`). Both are float64 means over integer arrays —
deterministic for a fixed array. Assert them with exact `repr` equality; if one ever drifts, that is a
finding worth surfacing, not noise worth tolerating.

**Golden fixture shape** — `tests/fixtures/golden_build_bins_v2.json`:

```json
{
  "meta": {
    "captured_at_sha": "<git rev-parse HEAD, on a git-clean pre-edit teach_persona.py>",
    "arm": "real",
    "facts": ["cand_person_quillon", "..."],
    "family_ids": ["F1", "F2", "F4", "F5", "F6"],
    "second_person": false,
    "replay_ratio": 0.0,
    "tokenizer_sha256": "<sha256 of artifacts/tokenizer.json>",
    "recipe": "build_bins(tok, render_episodes(facts, TAUGHT_FAMILY_IDS), bin, mask)"
  },
  "token_bin_sha256": "…",
  "mask_bin_sha256":  "…",
  "token_bin_bytes":  15162,
  "mask_bin_bytes":   7581,
  "stats_repr": "{'episodes': 176, 'tokens': 7581, ...}"
}
```

`tokenizer_sha256` is in `meta` for a reason: the bins are a function of the tokenizer, and
`artifacts/tokenizer.json` is FROZEN (CLAUDE.md — *loaded, never retrained*). If it ever moves, the
fixture is stale rather than the code being wrong, and the message must say which.

**The four assertions:**

```python
def test_build_bins_omitted_equals_align_facts_none(tmp_path):
    a = _run_build_bins(tmp_path / "a")                        # omitted
    b = _run_build_bins(tmp_path / "b", align_facts=None)      # explicit None
    assert a == b            # (token_sha, mask_sha, stats_repr), never skips, no platform read

def test_build_bins_default_matches_the_v2_golden(tmp_path):
    got = _run_build_bins(tmp_path / "g")
    assert got.token_sha == _GOLDEN["token_bin_sha256"]
    assert got.mask_sha  == _GOLDEN["mask_bin_sha256"]
    assert got.stats_repr == _GOLDEN["stats_repr"]

def test_align_facts_is_actually_wired(tmp_path):            # NON-VACUITY — the load-bearing half
    aligned = _run_build_bins(tmp_path / "al", align_facts=fs.LOCKED_FACTS)
    assert aligned.fact_bin_path.exists()                      # the third bin appears
    assert aligned.token_sha != _GOLDEN["token_bin_sha256"]    # padding changed the bytes
    assert _impure_rows(np.fromfile(aligned.fact_bin_path, np.uint16), BLOCK_SIZE) == []
    assert aligned.n_windows == 33                             # D-01's ragged geometry, observed

def test_three_bins_are_1to1(tmp_path):                        # D-06 / proof-1 extended
    a = _run_build_bins(tmp_path / "t", align_facts=fs.LOCKED_FACTS)
    n = a.token_bin_bytes // 2
    assert n == a.mask_bin_bytes == a.fact_bin_bytes // 2
```

`test_build_bins_omitted_equals_align_facts_none` never reads a platform identity and never skips —
it is the assertion CI relies on unconditionally, exactly as `test_loop_penalty_fn.py:118-124` is.

### §V.4b — `_prepend_replay` / the D-11 side channel: the differential is the only real proof

A test asserting `replay_tokens == 8192` **passes on the defective implementation**, because
`round(1.0 × teaching_tokens)` could coincidentally equal 8192. Asserting a constant does not prove
independence from private data; it proves one value.

**The direct proof of the property is a differential:**

```python
def test_replay_volume_is_invariant_under_fact_values(tmp_path):
    """D-11: the volume must depend only on n_facts, never on the facts' token lengths.

    Two corpora, SAME n_facts, DIFFERENT fact values -> different teaching_tokens.
    Old behaviour: replay_tokens tracks teaching_tokens (the side channel).
    D-11/D-24:     replay_tokens is identical (4 windows/fact = 1024 tokens).
    """
    short = _build(facts=_facts_with_short_values(n=8), replay_ratio=1.0)
    long_ = _build(facts=_facts_with_long_values(n=8),  replay_ratio=1.0)

    assert short.teaching_tokens != long_.teaching_tokens, \
        "the fixture does not vary private token length — this test would be vacuous"
    assert short.replay_tokens == long_.replay_tokens == 8 * 4 * BLOCK_SIZE   # 8192
```

The first assertion is what stops the test being vacuous: if both corpora happened to have equal
teaching lengths, the differential proves nothing and must say so rather than pass.

Two supporting assertions, both cheap:

```python
@pytest.mark.parametrize("n", [8, 64])
def test_replay_volume_is_window_quantized(n):
    assert replay_tokens(n) == n * 4 * BLOCK_SIZE
    assert replay_tokens(n) % BLOCK_SIZE == 0     # D-24's "integral windows?" column, asserted

def test_replay_constant_is_not_derived_from_the_corpus():
    # 7581/8 = 947.625 is the number D-24 rejected precisely because it was read off private data.
    assert REPLAY_WINDOWS_PER_FACT * BLOCK_SIZE != pytest.approx(947.625, abs=1.0)
```

This is CONTEXT's own stated defect class applied as a test: *"whatever guards the aligned path should
refuse the property, not the name."* The differential refuses the property. A constant assertion
refuses only the name.

### §V.4c — `render_family(..., forms=None, question_bank=None)`

`render_family` returns `list[tuple[str, str]]` (`phase14_factset.py:824-827`, dispatching
`table[family_id](fact)`). The observable is those strings.

**Golden fixture shape** — `tests/fixtures/golden_render_family_v2.json`:

```json
{
  "meta": {"captured_at_sha": "…", "family_ids": ["F1","F2","F3","F4","F5","F6","F7","F8"]},
  "first_person":  {"sha256": "…", "rows": 8},
  "second_person": {"sha256": "…", "rows": 8}
}
```

where each `sha256` is over
`json.dumps(rendered, ensure_ascii=False, sort_keys=False, separators=(",", ":")).encode("utf-8")`
for the full cross product of **all 8 `FAMILY_IDS`** × all 8 `LOCKED_FACTS` + `SOFT_TIER_FACTS`.

Two coverage points that are easy to miss and both matter:

- **All 8 families, not just the 5 taught.** `HELDOUT_FAMILY_IDS = {F3, F7, F8}` feeds
  `heldout_questions()` (`:830-847`), which feeds the published held-out split. An additive edit that
  broke a held-out family would pass a taught-only fixture.
- **Both registers.** `FAMILIES_SECOND_PERSON = _family_table(True)` (`:775`) is a live path for the
  `cal_second_person` arm (`teach_persona.py:411-412`). `_family_table` closes over `second_person`
  per family id (`:763-769`), so an additive kwarg has to thread through **both** closures.

**Non-vacuity pair — required, and this is where P2 bites:**

```python
def test_forms_is_actually_wired():
    modified = dict(fs.SLOT_FORMS)
    slot = fs.LOCKED_FACTS[0].slot
    modified[slot] = replace(modified[slot], np1="THE CANARY")
    out = fs.render_family("F1", fs.LOCKED_FACTS[0], forms=modified)
    assert any("THE CANARY" in q for q, _a in out), \
        "forms= did not reach the output — the `forms=None` byte-identity guard is vacuous"
```

**`question_bank` cannot be given the equivalent test as currently sited.** Measured:
`SLOT_QUESTION_BANK` has exactly three occurrences in `scripts/phase14_factset.py` — `:55` (a comment
on `Fact.slot`), `:151` (the definition), `:279` (the sole read, inside `_assign_probes()`).
`_render_family` (`:690`) reads only `SLOT_FORMS[fact.slot]`. `_assign_probes()` iterates
`all_pools()` (`:275`) — which filler is deliberately outside (D-13) — and its result becomes
`GATE_PROBES` (`:290`) at import time. **So `render_family(..., question_bank=X)` cannot change
`render_family`'s return value for any `X`, and a byte-identity guard over that parameter is
unfalsifiable.** See Open Question 1.

### Deliberate-RED for the byte-identity guards

**Mutation:** add a single trailing newline to one `SLOT_FORMS` entry's `ans1` template.
**Observable:** `test_build_bins_default_matches_the_v2_golden` goes RED on `token_bin_sha256`, AND
`test_render_family_matches_the_v2_golden` goes RED on `first_person.sha256` — two independent guards
firing on one byte, which is what proves both are reading the real path.
**Restore proof:** `git checkout scripts/phase14_factset.py` then
`sha256(scripts/phase14_factset.py)` equals the value recorded before; re-run → both GREEN.

---

## §V.5 — UNIT-03: validating the instrument, because a measurement with an untested instrument is not evidence

D-26 fixes the measurement: BOTH paths, instrumented loader, `SEED = 1337`, `MAX_STEPS = 200`,
`BATCH_SIZE = 8`, each row labelled with bin composition. What it does not fix is **how we know the
counter counts.**

### The instrument's four validations, cheapest first

**1. The conservation law — exact, deterministic, no statistics.**

```python
def test_multiplicity_instrument_conserves_the_draw_budget(tmp_path):
    counts = run_instrumented(bin=tiny, steps=MAX_STEPS, batch=BATCH_SIZE, seed=SEED)
    assert sum(counts.values()) == MAX_STEPS * BATCH_SIZE * WINDOWS_ATTRIBUTED_PER_DRAW
```

This is the single highest-value instrument test. Double-counting, dropped draws, an off-by-one in the
step loop and a silently-skipped batch all fail it deterministically, with no distributional
assumptions and no tolerance to tune.

**The plan must pin `WINDOWS_ATTRIBUTED_PER_DRAW` explicitly**, because a random `block_size` window
over an unaligned bin can overlap **two** facts and the two defensible attributions give different
RHS values:

| Attribution rule | RHS | Note |
|---|---|---|
| First token's fact owns the draw | `MAX_STEPS × BATCH_SIZE` = 1,600 | matches D-26's "1,600 draws" phrasing exactly |
| Every overlapped fact is credited | `> 1,600`, data-dependent | richer, but the conservation law becomes an inequality — weaker instrument |

Recommend the first: it makes the conservation law an **equality**, it matches D-26's own denominator,
and the aligned path's answer is unchanged either way (an aligned window overlaps exactly one fact by
construction). Whichever is chosen, **the test must name it** — an unnamed attribution rule is how the
two rows in the artifact stop being comparable.

**2. The instrument must be able to report ≠1 — the non-vacuity of the aligned row.**

D-26's aligned row records an *observed* count so "1 by construction" is verified rather than assumed.
But an instrument that prints `1` without counting also produces that row. Feed it a deliberately
mis-built aligned bin and assert it reports > 1:

```python
def test_instrument_reports_more_than_one_on_a_mis_built_aligned_bin(tmp_path):
    bad = _aligned_bin_with_two_facts_in_one_window(tmp_path)   # A1's roll, at real block_size
    observed = run_instrumented_aligned(bad, steps=10)
    assert max(observed.per_step_distinct_facts) > 1, \
        "the instrument reported 1-per-step on a bin that provably carries two — it is not counting"
```

Without this, the aligned row is a constant printed by an untested instrument, which is the exact
thing UNIT-03 exists to refuse.

**3. Seeded reproducibility — the record must be regenerable.**

```python
def test_multiplicity_is_reproducible_at_the_pinned_seed(tmp_path):
    a = run_instrumented(bin=tiny, steps=20, batch=8, seed=1337)
    b = run_instrumented(bin=tiny, steps=20, batch=8, seed=1337)
    assert a == b
    c = run_instrumented(bin=tiny, steps=20, batch=8, seed=1338)
    assert c != a, "a different seed produced identical counts — the seed is not reaching the draw"
```

The `seed=1338` half is the non-vacuity: without it, an instrument that ignores the seed entirely
passes.

**4. Analytic agreement as a cross-check only, never as the artifact.**

D-26 states the analytic expectations *as analytic* precisely because they are the kind of number
UNIT-03 refuses. Use them as a **sanity band on a synthetic bin with a closed-form answer** — e.g. 2
facts of exactly equal length: the two counts must be within a stated binomial interval of `n/2`. State
the interval and the draw count in the test; do not let a loose tolerance make it unfalsifiable.

**The instrument's output must carry its denominator into the artifact.** CONTEXT's `<code_context>`
names this as an Established Pattern (*"Measured numbers travel with their denominator and their
provenance"*). Each row in `results/phase21_*` should carry: bin composition label
(`replay-in-bin @1.0` / `facts-only (D-10)` / `fact-aligned (D-01, D-05)`), `seed`, `max_steps`,
`batch_size`, total draws, bin token count, window count, n_facts, and the min/max/mean/spread — not
merely the mean. D-26 says "min/max/mean/spread, not merely an expectation"; a test asserting the
artifact's schema contains all four keys is one line and prevents a silently-thinned record.

**Refuse-to-rerun.** `scripts/phase21_unit_record.py` writes recorded evidence and needs
`teach_persona.refuse_if_exists` (`teach_persona.py:236-244`) — an existing helper, imported not
copied. Test: call the driver twice into the same output path, assert the second call raises
`SystemExit` naming the file.

---

## §V.6 — SC5: the non-disturbance proof, and the cheapest test that fails if filler leaks

### What must be provably unchanged and still green

| Instrument | Location | Cheapest instrument available **today** |
|---|---|---|
| The 8 `LOCKED_FACTS` | `scripts/phase14_factset.py:390-399` | `tests/test_phase14_factset.py:101-103` already asserts `5 <= len(LOCKED_FACTS) <= 8`, `2 <= len(SOFT_TIER_FACTS) <= 3`, one taught fact per slot [CITED] |
| The 270-question fixture | **`results/phase16_recall_sample.json`** — tracked in git, sha256 `407c4b9304a74801ae15445360dcf3edc8002a65ce1011f9991c88b768307c55` [VERIFIED: `git ls-files` + `shasum -a 256`] | a `test_package.py`-style byte-level sha256 pin — one line |
| The 7 `len(forbidden) == 10` sites | measured below | the SC5 guard set command — 314 tests / 36.02s [VERIFIED] |
| `scripts/phase18_extraction.py` | ancestry-guarded via `PHASE18_PREREG_ARTIFACT` [CITED: tests/test_phase16_prereg.py:80] | the live ordering guard at `test_phase16_prereg.py:322-403` + a sha256 pin |

### The `len(forbidden) == 10` census — MEASURED, and CONTEXT undercounts it

D-18 names **four** sites. There are **seven, across six files** [VERIFIED:
`grep -rn "len(forbidden)" tests/ scripts/ src/` → 6 hits, plus
`sed -n '425,440p' tests/test_phase18_corpus.py` → the 7th]:

| # | Site | Named in D-18? | Form |
|---|------|---|---|
| 1 | `tests/test_phase14_scoring.py:405` | ✅ | `assert len(forbidden) == 10` |
| 2 | `tests/test_phase16_driver.py:313` | ✅ | `assert len(forbidden) == 10` |
| 3 | `tests/test_phase16_ladder.py:443` | ✅ | `assert len(forbidden) == 10` |
| 4 | `tests/test_phase18_corpus.py:430` | ✅ (line right) | `assert len(values) == 10` — **variable is `values`, not `forbidden`** |
| 5 | `tests/test_phase16_ladder.py:711` | ❌ | `assert len(forbidden) == 10` |
| 6 | `tests/test_phase18_prereg.py:127` | ❌ | `assert len(forbidden) == 10, "…a shrunken set would narrow it silently"` |
| 7 | `tests/test_phase19_erasure.py:625` | ❌ | `assert len(forbidden) == 10` (lowercased values) |

All seven construct the set the same way — `LOCKED_FACTS + SOFT_TIER_FACTS` — so all seven turn RED
the instant a filler fact enters either tier. **This is good news:** existing coverage is broader than
CONTEXT assumes. It is also actionable: the SC5 sampling command above must include
`test_phase18_prereg.py` and `test_phase19_erasure.py`, which a plan derived from D-18's four-site
list would omit.

Site 6 is the most valuable of the three unnamed ones: `test_phase18_prereg.py:132` then scans every
member of the `scripts/phase18_*.py` glob for embedded fact values — so it is a *coverage-widening*
guard, not just a count.

### The cheapest test that FAILS if filler leaks anywhere

**Reuse `embedded_fact_values`, reversed.** `tests/test_phase14_scoring.py:349-364` is a committed
helper that does substring containment over every string a module holds, including strings nested in
tuples and dicts. Its docstring records exactly why equality was not enough — a taught pet name quoted
three times inside a 1,302-character report paragraph passed a whole-string-equality predicate while
the invariant was false. That is precisely the shape a filler leak would take.

```python
# tests/test_phase21_sc5.py
def test_no_filler_value_reaches_any_published_instrument():
    """SC5 in one assertion, using the committed helper that already learned this lesson."""
    from test_phase14_scoring import embedded_fact_values

    filler = tuple(f.value.lower() for f in phase21_filler.FILLER_FACTS)
    assert len(filler) == 56
    assert len(set(filler)) == 56                      # no duplicate filler value

    # Direction 1 — no filler value inside any frozen instrument's SOURCE.
    for path in (P18_EXTRACTION, MITIGATION_GATE, FACTSET, ERASURE_GATE, P19_ERASURE):
        module = _load(path.stem, path)
        assert embedded_fact_values(module, filler) == [], f"{path.name} embeds a filler value"

    # Direction 2 — no filler value inside the binding 270-question fixture, as raw TEXT.
    fixture = FIXTURE_PATH.read_text(encoding="utf-8").lower()
    assert [v for v in filler if v in fixture] == []

    # Direction 3 — the reverse: no scored/soft value inside the filler module.
    forbidden = tuple(f.value.lower() for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    assert len(forbidden) == 10                        # the same wall, the 8th assertion site
    assert embedded_fact_values(phase21_filler, forbidden) == []

    # Direction 4 — filler never enters the pools, _BY_ID, or GATE_PROBES.
    pooled = {f.id for _n, pool in fs.all_pools() for f in pool}
    assert {f.id for f in phase21_filler.FILLER_FACTS} & pooled == set()
    assert {f.id for f in phase21_filler.FILLER_FACTS} & set(fs.GATE_PROBES) == set()
```

**Why this is the cheapest:** zero new machinery, one already-committed helper, no model, no
generation, no GPU, sub-second. It covers the leak in **both directions** — which matters, because
"filler leaks into an instrument" and "a scored value leaks into filler" are different defects and
only one of them is caught by the existing `len(forbidden) == 10` wall.

Direction 3 is also where the D-17 collision refusal gets its independent check: the module's own
internal refusal proves the values were minted correctly; this assertion proves it from outside the
module that implements it.

### The byte-unchanged half — two sha256 lines

```python
P18_SHA256     = "…"   # capture with: shasum -a 256 scripts/phase18_extraction.py
FIXTURE_SHA256 = "407c4b9304a74801ae15445360dcf3edc8002a65ce1011f9991c88b768307c55"

def test_frozen_instruments_are_byte_unchanged():
    """Read as BYTES, never text — a CRLF rewrite passes a text-mode hash (test_package.py:34-35)."""
    assert _sha(P18_EXTRACTION)  == P18_SHA256
    assert _sha(FIXTURE_PATH)    == FIXTURE_SHA256
```

`FIXTURE_SHA256` is measurable **today** [VERIFIED: `shasum -a 256 results/phase16_recall_sample.json`].
The bytes-not-text rule is copied verbatim from `tests/test_package.py:34-35`, which already records
why: a text read normalizes line endings.

This is a **stronger** guard than "no filler leaked" — it fails on *any* edit for *any* reason, which
is exactly what SC5's "unchanged" asks for. The two guards are complementary: the sha256 catches
every edit; `embedded_fact_values` catches a leak that reached a file *not* in the pin list.

### Deliberate-RED for the SC5 guard

**Mutation:** append `# canary` to `scripts/phase18_extraction.py`.
**Observable:** `test_frozen_instruments_are_byte_unchanged` goes RED on `P18_SHA256`, AND
`test_phase16_prereg.py::test_phase18_prereg_is_frozen_before_every_phase18_result` goes RED on the
ancestry check once committed — two independent tiers firing.
**Restore proof:** `git checkout scripts/phase18_extraction.py`; `shasum -a 256` equals `P18_SHA256`;
`git status --porcelain scripts/phase18_extraction.py` is empty. **Do not commit the mutation** — an
ancestry guard reddened by a real commit cannot be laundered by `git rm` + re-add
(`test_phase20_prereg.py:157`, and measured in state 4 of the fixture at `:394-404`).

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Ancestry ordering check for `results/phase21_*` | A copy of `_assert_ordering_holds` | **Call the existing one** with new kwargs (`test_phase20_prereg.py:121`) | `:296-298` says it in its own words: a lookalike copy proves something about a different function. The helper is already keyword-only and parameterized on `root` for exactly this. |
| Throwaway-repo RED-then-GREEN fixture | A new fixture design | **Copy `:281-441` verbatim**, `phase20_` → `phase21_` | Five states, each red distinguished by which assertion fired. Already handles the `mkdir` gotcha at `:387-388` and sets git identity as local repo config so it works on CI runners with no global `user.email`. |
| Substring leak scan over module strings | A `value in source` loop | **`embedded_fact_values`** (`test_phase14_scoring.py:349`) | Walks nested tuples and dicts, returns `(value, count)`, and already learned the equality-vs-containment lesson the hard way. |
| Import-ceiling enforcement for the new module | A new AST scan | **Nothing — it is free.** The `mitigation_*.py` glob (`:72`) picks up the new module and `:498/:522/:538` enforce D-22 | Verified: `imported` accumulates across **all** glob members. |
| Refuse-to-rerun on the new driver | A new existence check | **`teach_persona.refuse_if_exists`** (`:236-244`) | Names the offender and names the delete command. |
| Bitwise trajectory fingerprint | A tensor-equality loop | **`hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes())`** (`test_loop_penalty_fn.py:67-70`) | Three committed test modules already use this exact recipe. |
| A "one distinct id per window" check | Boundary arithmetic from cumulative padded lengths | **`fact.reshape(-1, B)` + `np.unique(row).size`** on bytes read back from disk | The offset form is what A1 defeats. `test_masked_batch.py:8-10` states the rule. |
| Dependency freeze | A parsed dependency list | **`test_package.py`'s byte-level sha256** | Already committed; catches a new extra, a widened specifier and a CRLF rewrite identically. |
| Statistical tolerance for the multiplicity instrument | A tuned threshold | **The conservation law** — an exact equality | No tolerance to tune, no distributional assumption, fails deterministically. |

**Key insight:** this repository has already paid for every instrument this phase needs. The correct
posture is *import and parameterize*, not *write a variant*. Every "variant" in the list above is a
place where a guard could drift from the code it claims to prove.

---

## Common Pitfalls

### Pitfall 1: The byte-identity test that passes because the kwarg is never read
**What goes wrong:** `f(..., X=None)` is byte-identical to the golden fixture — because `X` is
accepted and discarded. **Why:** the assertion only samples the `None` branch. **Avoid:** every
byte-identity test is a pair; half 2 asserts `X=<real value>` **changes** the output in a named way.
**Warning sign:** a `X=None` test that passes on the very first run, before the feature is wired.

### Pitfall 2: The content check that recomputes the packer's arithmetic
**What goes wrong:** a window-purity check that derives expected boundaries from the same cumulative
padded lengths the packer used is an offset check with a content check's name; A1 (roll-by-1) passes
it. **Why:** the test and the code share the defect. **Avoid:** hand-written literal expectations;
read bytes back from disk. **Warning sign:** the test imports the packer's length helper.

### Pitfall 3: The ordering guard that is green having compared nothing
**What goes wrong:** `checked == n * 0 == 0`. **Why:** armed before artifacts exist — which is
correct and deliberate. **Avoid:** `assert bool(checked) == bool(tracked_artifacts)` (`:176-183`) plus
the throwaway fixture. **Warning sign:** the state-2 `ls-files` assertion missing — without it the
prefix is inferred from the pattern's text rather than observed matching.

### Pitfall 4: Declaring the glob and forgetting the test
**What goes wrong:** `V4_ARTIFACT_GLOBS` gains `results/phase21_*` and nothing else changes; the
declaration enforces nothing. **Why:** `globs` is used only at `:129`; the loop runs on singular
`artifact_glob`. **Avoid:** both halves in the same plan. **Warning sign:** a diff touching only
`:102`.

### Pitfall 5: Committing a `results/phase21_*` artifact before the pin
**What goes wrong:** `adds[-1]` is the **earliest** add (`:157`), so `git rm` + re-add cannot launder
it — measured in state 4 of the existing fixture. **Avoid:** the guard is armed, green, and committed
in a commit that is a strict ancestor of the first artifact. **Warning sign:** any `results/phase21_*`
in `git status` while `tests/test_phase20_prereg.py` is still unmodified.

### Pitfall 6: A `phase21_`-named probe reaching the real git history
**What goes wrong:** the fixture writes a probe into the real repo; the artifact this phase exists to
produce is permanently mis-ordered. **Avoid:** everything under `tmp_path`; assert
`git log --diff-filter=A -- 'results/phase21_*'` is EMPTY on the real repo before and after the
fixture runs. **Warning sign:** any `cwd=_ROOT` inside the fixture.

### Pitfall 7: The instrument that prints its own conclusion
**What goes wrong:** the aligned row records `1` because the code writes `1`, not because it counted.
**Avoid:** feed the instrument a mis-built aligned bin and assert it reports > 1. **Warning sign:**
the aligned row is a literal in the driver rather than a value returned by the counter.

### Pitfall 8: Asserting the replay constant instead of the invariance
**What goes wrong:** `assert replay_tokens == 8192` passes on `round(1.0 * teaching_tokens)` when the
corpus happens to be 8,192 tokens. **Avoid:** the differential over fact values at fixed `n_facts`,
with a guard asserting the two corpora actually differ in teaching length. **Warning sign:** the test
has one corpus.

### Pitfall 9: Sampling only D-18's four `len(forbidden) == 10` sites
**What goes wrong:** three of the seven sites go unsampled, including
`test_phase18_prereg.py:127`, which is the one that also widens the scan across the `phase18_*` glob.
**Avoid:** the SC5 guard set command as written above (7 files, 314 tests, 36.02s).
**Warning sign:** a plan quoting four file paths.

### Pitfall 10: Validating on the system Python
**What goes wrong:** the dev box runs 3.14, which is not a supported target; results are meaningless.
**Avoid:** `.venv/bin/python -m pytest` everywhere. **Warning sign:** a bare `pytest` in a plan step.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | `np.memmap` re-open sees on-disk mutations on **CI's** platform (measured only on Darwin 25.5.0 + this venv's numpy) | §V.1 | The mutate-between-calls test could be flaky on Linux CI. **Mitigation:** the test asserts the mutation is visible (`sha256` before/after) before asserting the loader's behaviour, so a page-cache surprise fails with a message naming the cause. |
| A2 | `build_bins`' returned float stats (`np.mean` over integer arrays) are platform-stable, so the golden fixture needs **no** platform gate | §V.4a | If a float drifts, the golden test fails on a non-capture platform. **Mitigation:** split the assertion — bins' sha256 unconditional, `stats_repr` in a separate test that can be gated later without weakening the byte-level guarantee. [ASSUMED] |
| A3 | The 56 filler facts render to ~22 rows / ~4 windows each, matching a scored fact (D-15) | §V.2 target-space | If a filler value's tokenization is longer, its window count differs — harmless for purity, but the n=64 window total (≈264) shifts. Assert the observed total in the artifact rather than hard-coding 264. [ASSUMED — depends on values not yet minted] |
| A4 | Attribution rule "first token's fact owns the draw" is the right choice for the conservation law | §V.5 | If the plan picks the other rule, the RHS becomes an inequality and the instrument is weaker. **Not a decision research may make** — flagged for the planner. [ASSUMED] |
| A5 | Padding slots carry the owning fact's id (derived from D-01 + D-05, not stated in either) | §V.2 | If a sentinel is used, the purity guard is unsatisfiable and the debugging path is long. Assert `fact[pad_slice] == owner_id` explicitly. |

---

## Open Questions (RESOLVED)

> **All four were resolved during planning (`fc2e6dc`), not deferred.** The question bodies below
> are kept unedited as the record of what was asked; each carries its resolution inline.

| # | Question | RESOLVED in | How |
|---|----------|-------------|-----|
| 1 | `question_bank` siting | **plan 21-05** | **Dropped.** `SLOT_QUESTION_BANK` is read only at `phase14_factset.py:279` inside `_assign_probes()`, which iterates `all_pools()` — and filler is deliberately outside it (D-13). The guard could not fail, so the kwarg does not ship. Only `forms=None` lands, with a two-register `*_is_wired` pair. The measurement is recorded in the source as a waiver. |
| 2 | Multiplicity attribution rule | **plan 21-10** | `ATTRIBUTION_RULE = "first-token-owns-draw"`. Conservation is an exact **equality** at `200 × 8 = 1,600`, matching D-26's own denominator. Named in the instrument, the test message, and the artifact schema; the rejected alternative and its inequality cost are tabled. |
| 3 | Which site sizes replay after D-10 | **plan 21-08** | `_prepend_replay` **survives** and gains `n_facts=None`. The differential runs against **both** sites; the legacy branch is retained explicitly as the **negative control** that proves the differential can see a side channel at all. |
| 4 | `results/phase21_*` filenames | **plan 21-10** | `results/phase21_privacy_unit.json` and `results/phase21_multiplicity.json`, declared as the `ARTIFACTS` module constant in `scripts/phase21_unit_record.py` before either is written. Consistent across 21-03 / 21-10 / 21-11. |

**1. `render_family(..., question_bank=None)` has no path to `render_family`'s output.**
> **RESOLVED — plan 21-05: dropped.** The recommendation's option (a) was taken.
- **What we know (measured):** `SLOT_QUESTION_BANK` occurs exactly 3× in `scripts/phase14_factset.py`
  — `:55` (comment), `:151` (definition), `:279` (the sole read, inside `_assign_probes()`).
  `_render_family` at `:690` reads only `SLOT_FORMS[fact.slot]`. `_assign_probes()` iterates
  `all_pools()` (`:275`) and produces `GATE_PROBES` (`:290`) at import time.
- **What's unclear:** whether D-16's `question_bank=` belongs on `render_family` at all, or on the
  filler module's own probe assignment (which D-17 already requires to be re-implemented locally).
- **Why it matters for validation, not just design:** as currently sited, a `question_bank=None`
  byte-identity guard is **unfalsifiable** — no value of the parameter can change the observable.
- **Recommendation:** the planner either (a) drops `question_bank` from `render_family` and sites the
  filler question bank inside `scripts/phase21_filler.py` (where D-13/D-17 already put the
  re-implemented discipline), or (b) names the code path through which it reaches the output and
  writes the non-vacuity test for it. **This does not reopen D-16** — the decision is "additive kwarg,
  byte-identical when `None`"; only the siting of one of the two kwargs is at issue.

**2. Attribution rule for the unaligned multiplicity count.**
- **What we know:** D-26 says "1,600 draws" (200 × 8), which matches one-fact-per-draw.
- **What's unclear:** whether a draw whose window straddles two facts credits one fact or both.
- **Recommendation:** pin "first token's fact owns the draw" so the conservation law is an exact
  equality matching D-26's own denominator. Whichever is chosen, name it in the test and in the
  artifact's schema — an unnamed rule makes the two labelled rows non-comparable.

**3. Whether `_prepend_replay` survives D-10 at all.**
- **What we know:** D-10 moves replay out of the teaching bin entirely; `<code_context>` Integration
  Points nonetheless lists `_prepend_replay` as "corrected per D-11/D-24".
- **What's unclear:** whether the D-11 constant lands in `_prepend_replay` (the v3.0 build-time path,
  retained for compatibility) or only in the new `train()` seam.
- **Why it matters for validation:** the side-channel differential (§V.4b) must be pointed at whichever
  code path actually sizes replay. Pointed at the wrong one it is green and blind.
- **Recommendation:** the plan names the single site that computes replay volume, and the differential
  test targets that site by name. If both paths exist, the differential runs against both.

**4. `results/phase21_*` filename shapes.**
- **What we know:** the guard is `git ls-files results/phase21_*` — any tracked path under `results/`
  with that prefix. `results/` is **not** gitignored (`.gitignore:17` covers `data/` only)
  [VERIFIED: `grep -n` on `.gitignore`], so artifacts must be **committed** to be watched.
- **Recommendation:** the plan lists the exact artifact filenames before writing any, and the
  driver resolves them from a module constant rather than a string literal in a plan step.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.11 venv | every test | ✓ | 3.11.15 at `.venv/` | none — system 3.14 is NOT a supported target |
| pytest | every test | ✓ | 9.0.3 | — |
| numpy | bin content proofs | ✓ | installed in venv | — |
| torch | loader/loop tests | ✓ | installed (CPU path only) | — |
| `git` | ancestry guard + throwaway fixture | ✓ | repo is non-shallow [VERIFIED: `rev-parse --is-shallow-repository` → guard passes] | none — the guard asserts rather than skips |
| `artifacts/tokenizer.json` | any render/encode test | ✓ | present, frozen | none |
| `data/dialog_train.bin` / `_mask.bin` | D-10's replay draw | **not verified in this session** | — | tests can build a synthetic replay bin under `tmp_path`; the real bins are needed only for the real run |
| MPS / CUDA | nothing here | n/a | — | every test above is CPU-only by design |
| Network | nothing here | n/a | — | — |

**Missing with no fallback:** none identified.
**Not probed:** `data/dialog_train.bin` existence — `data/` is gitignored (`.gitignore:17`) so its
presence is machine-local. `_prepend_replay` already raises a named `SystemExit` if it is absent
(`teach_persona.py:333-337`), so the failure is loud rather than silent.

---

## Security Domain

`security_enforcement` is not present in `.planning/config.json`; treated as enabled. This is an
offline, single-user, zero-network ML repository, so most ASVS categories are structurally
inapplicable — recorded honestly rather than padded.

| ASVS category | Applies | Standard control here |
|---|---|---|
| V2 Authentication | no | no auth surface; no service |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | local files only |
| V5 Input Validation | **yes, narrowly** | the loader's three-bin length/shape validation is the trust boundary between a build artifact and the training loop. `data.py:112-116` is the existing pattern: raise loudly, name both paths and both lengths. Extend to three files. |
| V6 Cryptography | **yes, as integrity only** | `hashlib.sha256` used for byte-identity pins (`test_package.py:37`). Never hand-rolled; no secrets, no keys. |

| Pattern | STRIDE | Mitigation |
|---|---|---|
| **D-11's replay side channel** — a quantity *declared* public whose *value* is a function of private token lengths | **Information Disclosure** | The differential test in §V.4b. This is the phase's own named defect class, and STRIDE names it exactly: an observable public quantity leaking a private one. |
| Silently-dropped fact bin → `grad_accum_steps ≠ n_facts` → an ε that bounds nothing | **Repudiation** (a published claim without a verifiable basis) | §V.1's mutate-between-calls proof |
| Post-hoc edit of a pre-registered constant | **Tampering** | The git-history ancestry guard; `adds[-1]` makes it non-launderable (`:157`) |
| A filler value entering the leak vocabulary → an unconfounded comparison becomes confounded | **Tampering** (of the instrument) | §V.6's bidirectional `embedded_fact_values` scan + the sha256 pins |

No new attack surface is introduced by this phase: no network, no deserialization of untrusted input,
no subprocess with `shell=True` (the existing `_git` helper passes an argv tuple explicitly —
`test_phase20_prereg.py:113-119` records why).

---

## Standard Stack

**No new libraries. `pyproject.toml` is UNTOUCHED (RPT-03).** Every instrument required by this
document is already installed and already used by committed tests:

| Instrument | Module | Already used at |
|---|---|---|
| Byte-level content pin | `hashlib` | `tests/test_package.py:37`, `tests/test_loop_penalty_fn.py:70` |
| Git-history ancestry | `subprocess` + `git` | `tests/test_phase20_prereg.py:113-119` |
| Static import/AST scan | `ast` | `tests/test_phase20_prereg.py:498` |
| Bin content read-back | `numpy` | `tests/test_masked_batch.py` |
| Throwaway repo | `pytest` `tmp_path` | `tests/test_phase20_prereg.py:281` |
| Artifact serialization | `json` | driver only — **forbidden inside `mitigation_*`** (D-22, enforced at `:522`) |

**No Package Legitimacy Audit section is required:** this phase installs zero external packages.
`tests/test_package.py` turns RED on any change to `pyproject.toml`, byte-for-byte.

---

## Sources

### Primary (HIGH confidence — read and/or executed in this session)
- `tests/test_phase20_prereg.py` — `:55-102` (register constants), `:113-119` (`_git`), `:121-183`
  (`_assert_ordering_holds`), `:281-441` (RED-then-GREEN fixture), `:445-449`
  (`_collapsed_glob_guard`), `:474-579` (import-graph scan), `:630-645` (prose exclusion),
  `:740/:805/:928/:991` (singular-path scans)
- `tests/test_phase16_prereg.py:49,63,68,80,87,91` (the five pinned artifacts), `:322-403` (the Phase
  18 ordering shape)
- `tests/test_masked_batch.py:1-30` (the hand-written-literal discipline), `:83` (mismatch raise)
- `tests/test_loop_penalty_fn.py:1-130` (golden fixture + platform gate + in-process identity)
- `tests/test_package.py:1-40` (byte-level sha256 pin, bytes-not-text rule)
- `tests/test_phase14_scoring.py:349-364` (`embedded_fact_values`), `:398-410`
- `tests/test_phase14_factset.py:95-110` (composition caps)
- `tests/test_phase16_driver.py:306-318`, `tests/test_phase16_ladder.py:436-448, 705-715`,
  `tests/test_phase18_prereg.py:59, 118-135`, `tests/test_phase18_corpus.py:425-440`,
  `tests/test_phase19_erasure.py:618-630` — the seven-site census
- `src/personacore/training/data.py:93-126` (`get_batch_memmap_masked`)
- `scripts/teach_persona.py:236-244` (`refuse_if_exists`), `:247-249`, `:256-324` (`build_bins`),
  `:327-348` (`_prepend_replay`), `:405-421` (`arm_spec`)
- `scripts/phase14_factset.py:151` / `:265-300` (`_assign_probes`), `:685-700` (`_render_family`),
  `:763-778` (`_family_table`), `:816-821`, `:824-847` (`render_family`, `heldout_questions`)
- `scripts/phase16_persistence.py:281-294` (`FIXTURE_PATH`, `FIXTURE_TOTAL_QUESTIONS = 270`)
- `pyproject.toml:19,24-26,36-44`; `Makefile:9-22`; `.github/workflows/ci.yml:10,21,26,36`;
  `.gitignore:17`
- `.planning/phases/21-…/21-CONTEXT.md` (D-01 … D-26), `.planning/ROADMAP.md:311-341` (SC1-SC5),
  `.planning/REQUIREMENTS.md:89-110` (UNIT-01 … UNIT-06)

### Commands executed (every number above traces to one)
```
.venv/bin/python -c "import sys,pytest;print(sys.version.split()[0],pytest.__version__)"   -> 3.11.15 / 9.0.3
grep -rn "len(forbidden)" tests/ scripts/ src/                                             -> 6 hits
sed -n '425,440p' tests/test_phase18_corpus.py                                             -> the 7th site
grep -n "SLOT_QUESTION_BANK" scripts/phase14_factset.py                                    -> :55 :151 :279
grep -n "V4_ARTIFACT_GLOBS\|artifact_glob" tests/test_phase20_prereg.py                    -> globs only at :129
H=$(git rev-parse HEAD); git merge-base --is-ancestor "$H" "$H"; echo $?                   -> 0
git log --format=%H -- scripts/mitigation_gate.py | wc -l                                  -> 9
git ls-files 'results/phase20_*' | wc -l                                                   -> 3   (=> checked = 27)
git ls-files results/phase16_recall_sample.json; shasum -a 256 …                            -> tracked; 407c4b93…7c55
<scratch numpy probe: write/mutate/re-memmap>                                              -> [3] 3 -> 999, visible
<scratch: 8 LOCKED_FACTS x 5 TAUGHT_FAMILY_IDS encode_dialogue>                             -> 176 episodes, 0 with mask[0]!=0
.venv/bin/python -m pytest --collect-only -q | tail -3                                     -> 878 collected in 2.75s
timeout 900 .venv/bin/python -m pytest -q                                                  -> 877 passed, 1 skipped in 195.26s
time .venv/bin/python -m pytest -q <quick 4 files>                                         -> 62 passed in 3.45s
time .venv/bin/python -m pytest -q <SC5 7 files>                                           -> 314 passed in 36.02s
.venv/bin/python -m pytest tests/test_phase20_prereg.py tests/test_package.py -q           -> 21 passed in 1.86s
```

### Secondary (MEDIUM)
- None. Every claim in this document is either a direct read of committed source (cited `file:line`)
  or a command executed in this session (shown above). **No WebSearch, no Context7, no external
  documentation was consulted** — this is a repository-internal validation-architecture question and
  external sources would have been noise.

### Tertiary (LOW)
- None.

---

## Metadata

**Confidence breakdown:**
- Test framework & sampling rates: **HIGH** — every command timed and run in this session.
- Proof 1 (run-time consumption): **HIGH** — the enabling platform behaviour (`np.memmap` re-open sees
  on-disk mutation) was measured, not assumed. Cross-platform generality is A1 in the Assumptions Log.
- Proof 2 (content equality): **HIGH** — the adversarial separation is arithmetic on hand-written
  literals; the target-space subtlety rests on a 176/176 measurement plus a direct-assertion
  recommendation that removes the inference entirely.
- Proof 3 (the freeze): **HIGH** — every mechanism claim read line-by-line and four of them measured
  (`:129` sole use, reflexivity exit 0, singular-path scans, 27 live checked pairs).
- Byte-identity fixtures: **HIGH** for `build_bins` (integer-exact path to disk); **MEDIUM** for the
  `stats_repr` float half (A2).
- UNIT-03 instrument: **MEDIUM** — the conservation law is exact, but the attribution rule is an open
  decision (Open Question 2) and the RHS depends on it.
- SC5: **HIGH** — the census is measured, the fixture sha256 is measured, both instruments already exist.

**Research date:** 2026-08-22
**Valid until:** stable — this is a repository-internal analysis with no external dependency. It goes
stale only if `tests/test_phase20_prereg.py`, `scripts/phase14_factset.py`,
`src/personacore/training/data.py` or `scripts/teach_persona.py` change. Re-run the command block
above to revalidate in under a minute.
