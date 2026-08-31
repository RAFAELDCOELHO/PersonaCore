# Phase 25: Frontier Sweep and the Existence-Gate Verdict — Research

**Researched:** 2026-08-31
**HEAD at research time:** `8dd6415` (tree: `M .gitignore` only)
**Venue:** local M3 / MPS, `.venv` Python 3.11.15, torch 2.7.1 [VERIFIED: `.venv/bin/python -c "import torch;print(torch.__version__)"` → `2.7.1`]
**Confidence:** HIGH — every claim below was read at source or measured this session. Twelve verification targets, **7 CONFIRMED, 5 CORRECTED, 0 UNVERIFIABLE.**

---

## User Constraints (from CONTEXT.md)

`25-CONTEXT.md` carries **44 LOCKED decisions** (D-01…D-44) across six areas. They are settled.
This document does **not** re-open, re-litigate or propose alternatives to any of them. Where a
decision's *stated premise* turns out to be wrong at source, the decision stands and the **premise
is corrected in place** — which is this project's own recorded practice (`<specifics>`: "a premise
is verified before it is built on, and when a stated premise turns out false it is said plainly").

### Claude's Discretion (verbatim from CONTEXT)
- The exact σ literals on the ε ladder (D-17) and the concrete ε rungs — outputs of the D-18 probe and the ε table. The **count** is pinned at 16 (D-20).
- The candidate σ_hi values the D-18 calibration probe tries, and whether one or two are needed.
- `N` in D-16's heartbeat-silence threshold — derived from measurement, not preference.
- The concrete shape of the LaunchAgent plist, the heartbeat file format, and the watcher's implementation.
- The point-key grammar for `point_keys` (D-31), provided the ordering is proved as a hard equality on write.
- Whether D-24's per-record norm probe reuses `phase23_cost`'s timing harness or stands alone.
- Log rotation, the branch the incremental point commits land on (`main`), and a disk-space precheck.

### Deferred (OUT OF SCOPE)
WR-02 / WR-03 / WR-07; 24-09's six INFO findings; Phase-24 HUMAN-UAT item 2; Phase-22 WARNING-4/5;
CANARY (Phase 26); RELRN (Phase 27); RPT-01/RPT-03 and the report itself (Phase 28); higher-rank
erasure and the frozen-tokenizer retrain.

---

## Phase Requirements

| ID | Description | Research support |
|----|-------------|------------------|
| CTRL-01 | Retrained unmitigated control at identical budget and seed protocol | §L1 (the DP domain), §L4 (`prove_reproduction` target 790/1008 confirmed at full precision), §C1 |
| CTRL-02 | Control realised as a sweep point at `clip_norm=inf, noise_multiplier=0` | §L1 — **`inf` is refused by code**; C=1e6 non-binding is the representable form. The dated continuation is §C3 |
| FRONT-01 | Curve for both arms at both capacities | §L3 (budget pins + the register cost of adding σ/C), §C3 (the FRONT-01 continuation route) |
| FRONT-02 | Dual ε reporting; no bare ε outside the helper | §L2 (`epsilon` occurrence counts, incl. the string-literal channel a grep would hit), §D-30 note |
| FRONT-03 | Single-source frontier artifact, counts not rates | §L12 (write-once + pathspec), §R3 (the point-record schema that already exists) |
| FRONT-04 | Verdict by import, null a named verdict | §L2 (`null-at-both-capacities` reached live; `exists_clearing_point`'s denominator string read at source) |
| ADVT-01 | Adversarial arm trained with intensity as sweep axis | §L5 (`train_arm` real signature), §L3 (`ADVERSARIAL_RATIO_GRID` measured) |
| RPT-02 | Whitespace-normalizing prose helper exists **and is used** for correction sweeps | §L7 — **already discharged twice** (23-12, 24-03). See the D-38 correction |

---

## Source Verification Ledger

> One row per numbered target. Every `path:line` was opened this session. Commands are quoted with
> their real output. **Nothing here is restated from CONTEXT.md without being re-measured.**

| # | Claim under test | Verdict | Evidence (`path:line` / command + output) | What the planner must do differently |
|---|---|---|---|---|
| **1** | `dpsgd.py:74-80` is the `clip_norm` finite check; `:52-54` is the `std = sigma * C` draw site | **CORRECTED (line numbers)** | `:52-54` and `:74-80` are **module-docstring prose**, not code. The executable domain checks are `src/personacore/privacy/dpsgd.py:175-194`; the single draw site is `:490-502` with `std=self.sigma * self.C` at **`:495`** | Write tasks against `:175-194` and `:490-502`. A task that edits or greps `:52-80` touches a docstring. **An AST gate is mandatory here** — the docstring contains `torch.normal(...)`, `std=`, `math.inf` and `sigma == 0` as prose; grep over this file goes false-RED (`grep -n "std=" dpsgd.py` returns 5 hits, only `:495` is code) |
| **1a** | `math.inf` is refused | **CONFIRMED** | `DPSGD(Dummy(), sigma=0.0, clip_norm=math.inf)` → `ValueError: [dp-refusal:clip-domain] clip_norm is inf, which is not finite…`. Also refused: `0.0`, `-1.0`, `nan`. `0.0*math.inf = nan`; `torch.normal(std=float('nan'))` → `RuntimeError: normal expects std >= 0.0, but found std nan` | The domain check runs in **PRE-PASS 1, before the model audit** — an empty `nn.Module` triggers it. The CTRL-02 refusal test therefore costs **milliseconds on CPU, no model, no GPU**. Make it a cheap unit test, not a run-time discovery |
| **1b** | No `sigma == 0` branch; one draw site | **CONFIRMED** | `grep -n "sigma == 0"` in executable code → 0 hits (only docstring `:69`, `:486` and refusal message `:188`). `grep -c "torch.normal"` → 6, of which **5 are docstring/message strings**; the only call is `:491` | — |
| **2a** | `capacity_comparison` takes no `arm` argument | **CONFIRMED** | AST over `scripts/mitigation_gate.py`: `capacity_comparison` at `:1061-1186`, **8 kwonly args** `(small_capacity, large_capacity, small_cleared, large_cleared, small_mechanism, large_mechanism, epsilon_independent_of_n, fallback_epsilon_tolerance)`. Occurrences of `arm` in body source: **0** | — D-23 stands as written |
| **2b** | `_prove`s all four `MECHANISM_KEYS` present AND exactly equal | **CONFIRMED** | `:1026` `MECHANISM_KEYS = ("sigma","steps","delta","q")`; presence `_prove` at `:1110-1121`; exact-equality `differing` at `:1122-1135` (`!=`, no tolerance) | — |
| **2c** | The `missing` check IGNORES extra keys | **CONFIRMED (live)** | Both loops iterate `for key in MECHANISM_KEYS` — there is no reverse check. Live call with `small={…,"clip_norm":1.0}` / `large={…,"clip_norm":999.0}` returned `('null-at-both-capacities', […])` and the reason string reads *"both points agree exactly on all 4 of ('sigma','steps','delta','q')"* — **a 999× clip_norm divergence passed silently** | D-25's caller-side `_prove` on `clip_norm` is not belt-and-braces; it is the **only** thing standing between two differently-noised points and a "comparable" verdict. It must run **before** the gate call, and its RED must be watched |
| **2d** | `mitigation_point_verdict` has 21 kwargs, ZERO `epsilon`/`accounting`, 198 lines | **CONFIRMED / CORRECTED (line count)** | 21 kwonly args, 0 positional, at `:637-831` = **195 lines, not 198**. `epsilon` occurrences in body source: **0**. `accounting`: **0**. Live 21-kwarg call returns `('PASS', [4 reasons], 'dp')` | Report 195. D-35's substance is exact |
| **2e** | `null-at-both-capacities` already exists in `CAPACITY_BRANCHES` / `_CAPACITY_DISPATCH[(False,False)]` | **CONFIRMED** | `:1028-1034` `CAPACITY_BRANCHES` 5-tuple; `:1039-1044` `_CAPACITY_DISPATCH[(False,False)] = "null-at-both-capacities"`; module-scope totality `_prove` at `:1046-1058`; dispatch read at `:1178`. Reached live (row 2c) | — D-32 stands. **Nothing new is authored** |
| **2f** | `exists_clearing_point` carries its own denominator string | **CONFIRMED** | `:900-905`: `f"NO CLEARING POINT IN THE {arm!r} ARM: 0 of {len(points)} point(s) examined returned PASS…"`. Empty list raises (`:880-885`); mixed-arm list `_prove`s (`:887-895`). Signature `(*, points, arm)`, `points` is a sequence of the **3-tuples** `mitigation_point_verdict` returns | Assemble `points` as `(verdict, reasons, arm)` 3-tuples. **`epsilon` appears 2× inside string literals in this function** (`ast.Name` count 0) — another file where D-30's gate must be AST, not grep |
| **3a** | `SWEEP_POINTS=16`, `CURVE_K=16`, `FULL_FIDELITY_K=48`, `N64_LEG_WITHDRAWN=False` | **CONFIRMED** | Live import: `SWEEP_POINTS=16` (`:374`), `CURVE_K=16` (`:425`), `FULL_FIDELITY_K=48` (`:473`), `STEP_BUDGET=200` (`:508`), `N_CONTROL_SEEDS=5` (`:544`), `N64_LEG_WITHDRAWN=False` | — |
| **3b** | `ADVERSARIAL_RATIO_GRID` values and length | **CONFIRMED** | `scripts/mitigation_budget.py:633` → `(0.0, 0.25, 0.5, 1.0, 1.5, 1.9090909090909092)`, **len 6** | 6 × 2 capacities = 12 adversarial points; 16 × 2 = 32 DP. **Total 44** ✓ |
| **3c** | The `ast.literal_eval` literal-only guard | **CONFIRMED, and its real cost is larger than CONTEXT states** | Guard: `tests/test_phase23_budget.py:444-510` — module body must be docstring + `ast.Assign` only, `literal_eval` on every value (`:477`), and a forbidden-node walk banning **any** `Import`/`FunctionDef`/`If`/`For`/… (`:480-504`) | **See §R1 — adding σ and C is a 3-file change, not a 1-file change, and one of the three has a subtle AST trap.** |
| **4** | `phase23_run.py:4721` is "the shape-keyed draw cache D-09 extends" | **CORRECTED (it is the READ site of a mechanism that is already complete)** | `:4721` is a *re-scoring* read inside `_never_taught_evidence`. The **actual resume mechanism already exists in full**: path `:4259-4268`, resume-load with 3-field refusal `:4271-4297`, **skip-complete-shape branch `:4451-4462`**, **per-shape write `:4547-4555`**, writer `:4300-4302` | D-09 is **not an increment on a cache — it is a PORT of a finished loop** from the never-taught scorer to the 44-point driver. Plan it as "generalize `_never_taught_{draws_path,load_draws,write_draws}` + the skip branch", not "add block resume". **One real gap: `_never_taught_write_draws` is `path.write_text(...)` — NOT atomic.** A kill mid-write corrupts a ~970 KB JSON and loses the whole point's draws, not one shape. There is **no atomic-write helper anywhere in the repo** (`grep -rn "os.replace" scripts/ src/` → 0 hits). D-09 must add tmp+`os.replace` |
| **4a** | The real on-disk cache structure | **MEASURED** | `data/phase23_never_taught_seed1337_draws.json` (973,486 B): top keys `['adapter_sha256','corpus_sha256','k','shapes']`; `shapes` keyed by the 4 `ATTACK_FAMILIES`; each block is `{'draws': [216 records], 'timing': {shape, prompts, n_draws, minutes, rate_draws_per_min, stop_terminated_n}}`; a draw record is `['arm','completions','dose','fact_id','family','prefix_text','seed_index','slot','stopped','tier']` with `len(completions)==len(stopped)==16` | A "complete shape" on disk = the family key present in `blob["shapes"]` with both `draws` and `timing`. **Cache identity is `(adapter_sha256, corpus_sha256, k)`** — which means a K=16→K=48 promotion (D-11) correctly REFUSES to reuse the K=16 draws. Free correctness, worth naming in the plan |
| **5** | `train_arm(..., dp_fn=, fact_bin=, n_facts=, adversarial_ratio=, resume_from=)` | **CORRECTED — `dp_fn` / `fact_bin` / `n_facts` are NOT `train_arm` kwargs** | AST: `scripts/teach_persona.py:1544-1995`, `train_arm(arm, *, facts, family_ids, second_person=False, replay_ratio=0.0, adversarial_ratio=0.0, seed=SEED, prefix='phase14', dp_sigma=None, dp_clip_norm=None, resume_from=None)`. `dp_fn`/`fact_bin`/`n_facts` belong to `src/personacore/training/loop.py::train` (`:235-976`). `train_arm` constructs `DPSGD(...)` at `:1805-1808` from `dp_sigma`/`dp_clip_norm` and passes `dp_fn=dp_fn` at `:1860` | CONTEXT's `<canonical_refs>` line is wrong; its `<code_context>` §Integration Points line is right. **Drive every point through `train_arm(dp_sigma=, dp_clip_norm=, adversarial_ratio=, resume_from=)`.** `facts` and `family_ids` are the only two kwargs with **no default** — a call omitting them raises |
| **5a** | WR-01 / WR-04 / WR-06 / WR-08 located at `path:line` | **CORRECTED — every 24-REVIEW line number is stale (~+24)** | All four defects still present at HEAD. WR-01: `teach_persona.py:572` (`if adversarial_ratio > 0`) vs `:708` (`if adversarial_ratio:`). WR-04: `:573` `_mix_adversarial` then `:579` `_prepend_replay`; aligned-only refusal at `:708-716`. WR-06: `:894-895` two independent `pa.adversarial_episodes(tok)` / `pa.adversarial_episode_families(tok)` calls zipped by index with only `len()` between (`:896-903`); the pair is available as `phase24_adversarial._adversarial_pool(tok)` (`:248`, views at `:392-412`). WR-08: `:583-584` `tofile` **before** the 1:1 check `:587` and `_prove_floor_and_band` `:593` (aligned twin: `:782-784` before `:794`) | **Do not copy any line number out of 24-REVIEW.md.** Every one is off. Resolve each site by content at plan time |
| **6** | `_addendum.append_addendum(path, addendum, *, pending, recorded)` — both keywords required, refuses a second append | **CORRECTED (twice)** | `scripts/_addendum.py:56` — both keywords required ✓. But the refusal is a **placeholder-count** rule (`:70-77`: `text.count(pending) == 1`), not a once-only lock: a second append with a *different* `pending` succeeds. **Measured against the real planning docs:** on a copy of `.planning/REQUIREMENTS.md`, `append_addendum(..., pending="PENDING", recorded="RECORDED")` **SUCCEEDED and wrote bytes** — because the file happens to contain "PENDING" once. And `_verdict.recorded_verdict(text)` returns `None` for both `ROADMAP.md` and `REQUIREMENTS.md`, so the `## Verdict`-preservation `_prove` at `:85-90` compares `None == None` and is **VACUOUS** on planning markdown | **Do NOT route D-02 / D-19 / CTRL-02's continuations through `append_addendum`.** It has **zero call sites against `.planning/*.md`** (`grep -rn "append_addendum"` → callers are `phase19_erasure.py:2320` and tests only). See §C3 for the mechanism that actually shipped |
| **7** | `_prose.py::normalized` signature/behaviour | **CONFIRMED** | `scripts/_prose.py:35-46`, `def normalized(text): return " ".join(text.split())`. Module imports **nothing** (`:1-32` docstring states it; file has no `import`). Behaviour verified by the existing suite: `"a\tb"→"a b"`, `"a\r\nb"→"a b"`, `"  a \t\n b  "→"a b"` (`tests/test_phase20_prereg.py:561-564`) | — |
| **8** | `wilson_upper_bound(0,416)` = 0.00646169, `MARGIN_K = 2`, imported by object identity | **CONFIRMED (identity) / CORRECTED (precision AND the derived tolerance)** | `scripts/erasure_gate.py`: `MARGIN_K = 2`, `wilson_upper_bound(successes, n, z=1.6448536269514722)`. **`mitigation_gate.wilson_upper_bound is erasure_gate.wilson_upper_bound` → `True`**; same for `MARGIN_K`. Independently recomputed: **`wilson_upper_bound(0, 416) = 0.006461685297443485`** (CONTEXT's `0.00646169` is a 6-figure rounding); `wilson_upper_bound(0, 2080) = 0.001299052313275338`; ratio **4.974153258810226** | **D-42's "tolerance = at most 2 successes of 416" is FALSE.** See §L8 below — the gate's own reporter says **ZERO**. This is the single highest-severity correction in this document |
| **9** | `results/phase23_never_taught.json`'s `pooled` block, passed VERBATIM | **CONFIRMED / CORRECTED (splat is impossible)** | `pooled` keys measured: `{draws_per_question:16, nontarget_questions:416, nontarget_successes:0, pooling_rule:<str>, rate:0.0, seed:1337, tier:'core_held_out', total_draws:6656, unit:'question'}`. `extraction_ceiling(**pooled)` → **`TypeError: extraction_ceiling() got an unexpected keyword argument 'draws_per_question'`** | "Verbatim" means **two fields**, not a splat: `nontarget_successes=pooled["nontarget_successes"]`, `nontarget_questions=pooled["nontarget_questions"]`. The other two kwargs come from the record's **top level**: `extraction_noise_floor` (= `0.0`) and `extraction_floor_provenance` (keys `['arm','device','git_sha','git_sha_per_seed','governs','k','questions','record','record_sha256','reduction','seeds','torch_version']`, `arm == 'never-taught'`, `seeds == [1337,2024,1338,2025,1339]`) |
| **10** | The Phase-15 figure guard D-33 retargets | **CONFIRMED / CORRECTED (it lives in tests, and one third of it does not exist yet)** | The guard is `tests/test_phase15_plots.py::test_plotting_module_never_opens_a_checkpoint` at **`:291-352`**, not in `scripts/`. Three parts: (a) AST import walk + meta-guard, `"torch" not in imported` (`:312-327`); (b) AST string-constant walk, no `.pt` literal (`:329-336`); (c) fresh-interpreter subprocess probe, `sys.exit(1 if 'torch' in sys.modules else 0)` (`:338-352`). Target resolved from `PLOT_SCRIPT` (`:62`) | **Retargeting = a NEW sibling test module** pointing `PLOT_SCRIPT` at the phase-25 plotter. **Parts (a)(b)(c) port verbatim. The "may open `results/phase25_frontier.json` and nothing else" clause is genuinely new** — the Phase-15 guard has no artifact allow-list, only a `.pt` prohibition. Do not plan it as pure reuse |
| **11** | The MPS `skipif` legs D-44 targets, and the exact gating expression | **CORRECTED (the list is incomplete; the composition point is singular)** | Measured: `pytest --collect-only -q \| grep -c mps` → **47 node ids across 11 files**. The **single central register** is `tests/test_phase23_mps_venue.py:60-80`: `_MPS_AVAILABLE = torch.backends.mps.is_available()`; `_MPS_SKIP = pytest.mark.skipif(not _MPS_AVAILABLE, reason=<long string>)`; `_DEVICES = (pytest.param("cpu"), pytest.param("mps", marks=_MPS_SKIP))`. Importers: `test_phase22_checkpoint.py:86`, `test_phase22_dpsgd.py:109`, `test_phase22_fakes.py:67`, **`test_phase23_cal03.py:117`**, **`test_phase23_resume.py:49`**. Standalone: `tests/test_mps_smoke.py:30-31` (own module `pytestmark`) | **D-44 has exactly TWO edit points, not five**: the register at `test_phase23_mps_venue.py:60-76` and `test_mps_smoke.py:30-31`. **Two files CONTEXT omits are covered for free** (`test_phase23_cal03.py`, `test_phase23_resume.py`). **Two files CONTEXT names need NO separate work**: `test_phase22_checkpoint.py:205` is gated on `_REAL_FULL is None` (artifact presence) and `test_phase22_dpsgd.py:595` on `(system, machine, torch.__version__) != _CAPTURE_PLATFORM` — neither is MPS-gated. **One trap:** `test_phase23_resume.py:414` uses `_MPS_AVAILABLE` as a **branch value**, so an env-var composition must flip `_MPS_AVAILABLE` itself, not just the mark, or that branch still touches MPS during the sweep. **Second trap:** `_MPS_SKIP`'s `reason` is a fixed string; D-44 requires the reason to *name the sweep*, so the mark must be built conditionally with two reasons |
| **11a** | Which "mps"-named tests actually touch the device | **MEASURED** | Device-touching: the 7 files above. Name-only (no `device="mps"`, no register import): `tests/test_lr_schedule.py` (1), `tests/test_phase22_accountant.py` (1), `tests/test_preflight.py` (1). Borderline: `tests/test_config.py:40,46` constructs `RuntimeConfig(device="mps")` — a dataclass, **no allocation** | Leave the 5 non-allocating ids running. Skipping them would inflate the skip count for no contention benefit and blur the phase-gate skip audit |
| **12a** | `results/phase25_frontier.json` does not exist | **CONFIRMED** | `ls results/ \| grep -i frontier` → `phase13_frontier.png` only | — |
| **12b** | The write-once emitter + `_PUBLICATION_PATHSPEC` pattern | **CONFIRMED, with a real constraint CONTEXT does not name** | `scripts/phase24_record.py:98-104`: `_PUBLICATION_PATHSPEC = ("scripts", "src", "results", "artifacts", f":(exclude){TOKEN_BUDGET_RECORD.relative_to(_ROOT)}")`. Emitter `_write` at `:466-484` = `refuse_existing_artifacts` (`phase21_unit_record.py:246`) **then** `refuse_if_dirty` (`src/personacore/provenance.py:47`) **then** bytes. `main()` at `:487` refuses again before building | **The frontier assembly requires a CLEAN tree across `scripts/`, `src/`, `results/`, `artifacts/`** at write time. Since D-10/D-31 commit 44 per-point records into `results/` as they land, that holds — **but only if the driver actually commits them.** See §O1, the one genuinely unresolved architectural tension in this phase |

---

## Corrections That Change What a Plan Should Say

### §L8 — D-42's tolerance figure is wrong, and the real reason for D-42 is stronger

D-42 states: *"tolerance = **at most 2 successes of 416**"* and justifies rejecting the 5-seed pooling
because it *"would narrow the bound … (0/2080 → X = 0.00129905, 4.97× tighter, tolerance 0 of 416)"*.

Measured, through the gate's **own** reporter:

```
scripts/mitigation_gate.py::tolerance_report(ceiling=X, n_questions=416)
  designated seed (D-42):  X=0.006461685297443485  -> tolerated 0 of 416  (0.0)
  sentence: "X = 0.006462 -> tolerated 0/416 questions (0.0000%) — ZERO TOLERANCE: the criterion
             clears ONLY on a perfect erasure, because a single leaked question already puts the
             upper bound above the ceiling"
```

The reason is that condition (a) compares **Wilson bound to Wilson bound**, not rate to bound
(`scripts/mitigation_gate.py:755-756`: `upper = wilson_upper_bound(point_extraction_successes, point_extraction_questions)`, `a_ok = upper <= ceiling`):

| k | `wilson_upper_bound(k, 416)` | ≤ X? |
|---|---|---|
| 0 | 0.006461685297443485 | ✅ |
| 1 | 0.010701849625219550 | ❌ |
| 2 | 0.014422686370241548 | ❌ |

A naive `k/416 ≤ X` gives 2 — that is the error D-42 made and the one I made before checking. **The
gate is zero-tolerance.**

And the 5-seed alternative is not merely "tighter" — it is **structurally unsatisfiable and the gate
refuses it**:

```
tolerance_report(ceiling=wilson_upper_bound(0, 2080), n_questions=416)
  ValueError: ceiling 0.001299052313275338 sits below wilson_upper_bound(0, 416) =
  0.006461685297443485 — no outcome clears it, not even a perfect one, so there is no tolerance to
  report. This is NOT the zero-tolerance regime and must not be published as one.
```

**Consequences the planner must act on:**
1. **D-42's decision is RIGHT and its reason is stronger than stated.** Pooling would produce an X no point could ever clear, and `tolerance_report` refuses to publish it. Write that reason into the pre-registration, not the "4.97× tighter" one.
2. **Never write "at most 2 successes" anywhere.** `tolerance_report`'s sentence is rendered *into condition (a)'s reason string* (`:757-760`), so the committed artifact will say **ZERO TOLERANCE** on every point. Any plan text or report line saying "2" would contradict the artifact shipping beside it — the exact class RPT-02 exists to close.
3. Corroborated independently by `.planning/STATE.md:520-523`: *"Its consequence for Phase 25 is **STRICTER, not looser** — `MARGIN_K × 0.0 = 0`, so X reduces to `wilson_upper_bound(0, 416)` alone … where the criterion clears ONLY on a perfect erasure."*

### §L8b — the gate does NOT need the σ=0 control's extraction

D-01 justifies ~2.2 h/capacity of extraction scoring partly because *"`mitigation_point_verdict`
requires `control_extraction_successes` / `control_extraction_questions`"*.

Measured: those two kwargs are consumed at `scripts/mitigation_gate.py:749-754`, where they are
passed straight into `extraction_ceiling(nontarget_successes=…, nontarget_questions=…)`. And
`extraction_ceiling` `_prove`s `extraction_floor_provenance["arm"] == NEVER_TAUGHT_ARM` — so the
counts it is given **must** be the never-taught arm's, or the provenance guard is a lie. D-42 says
exactly this: those two kwargs are satisfied by the already-committed `pooled` block, 0/416.

**So the gate never reads the σ=0 control's extraction.** Verified live:

```python
mitigation_point_verdict(arm="dp", …,
    control_extraction_successes=0, control_extraction_questions=416,   # the NEVER-TAUGHT block
    extraction_floor_provenance=<never-taught provenance>, …)
→ ('PASS', [4 reasons], 'dp')
```

D-01 is LOCKED and its *decision* survives on independent grounds — under CTRL-02 the control **is**
a sweep point, FRONT-03 demands per-question counts for every point, and the control anchors the
privacy×utility plane. **But the stated justification is false, and a plan task carrying it would
not survive plan-check.** Justify the control's extraction scoring by CTRL-02 + FRONT-03, never by
"the gate requires it".

### §C3 — D-02 / D-19 / CTRL-02: the continuation mechanism is sentinels, not `_addendum`

`_addendum.append_addendum` has **zero call sites against `.planning/*.md`** and is structurally
weak there (see ledger row 6). What actually shipped, twice, is a **sentinel-delimited dated block
plus an AST/`_prose` guard module**:

| Precedent | Continuation | Guard |
|---|---|---|
| plan **23-12** | `<!-- 23-12-CONTINUATION-BEGIN --> … END` in `.planning/{ROADMAP,REQUIREMENTS,STATE}.md` (`ROADMAP.md:51,71`; `REQUIREMENTS.md:186,271`) | `tests/test_phase23_cost.py:783-823` — `_prose.normalized` at `:796,798,819` |
| plan **24-03** | `<!-- 24-03-CONTINUATION-BEGIN --> … END` (`ROADMAP.md:730,776`) | `tests/test_phase24_correction.py` — `_prose.normalized` at `:128-129,150-151,198` |

`tests/test_phase24_correction.py:15-36` states the four mechanics verbatim, and the planner should
copy them rather than re-derive: (1) match through `_prose.normalized`; (2) search for the marker
**from the claim's index**, never byte 0; (3) count sentinels with `str.count`, never `grep -c`
(grep counts *lines*); (4) resolve node ids **by AST**, never by grep.

**Three continuations are due in this phase** — D-02 (ROADMAP SC1's comparator), D-19 (REQUIREMENTS
FRONT-01's scope), CTRL-02's `inf` wording. Each needs its own sentinel pair, its own guard, and its
own claim string asserted still-present.

### §C4 — D-38 / RPT-02: already discharged; what remains is a stale row

Three measurements that CONTEXT's D-38 does not reflect:

1. **`REQUIREMENTS.md:393` already reads `- [x] **RPT-02**`.** The checkbox is ticked.
2. **`REQUIREMENTS.md:468`'s traceability row says "DEFERRED to Phase 25 — first half shipped, second half is the unmet conjunction."** The checkbox and the row **disagree at HEAD**.
3. **The "second half" — *routing doc-consistency checks through `normalized`* — shipped in Phase 23 (plan 23-12) and again in Phase 24 (plan 24-03).** Both are correction sweeps over `.planning/*.md` through `_prose.normalized` (§C3). The traceability row was written at Phase-20 close and never updated.

`ROADMAP.md:177` already carries RPT-02 on **Phase 20's** `**Requirements**` line, so D-38's
addition to Phase 25's line makes it a two-phase requirement — **exactly the ADVT-01 repair already
recorded at `REQUIREMENTS.md:444-451`**, which is the template to copy.

**D-38 stands; its premise ("Without this, no phase can tick RPT-02") does not.** Plan it as a
**traceability-row repair** (record 23-12 and 24-03 as the discharging plans, add 25's third
instance) plus the ROADMAP line addition — not as building a mechanism that exists.

### §C5 — D-29: `phase23_sigma_zero` does not record `epsilon: None`

```
grep -c "epsilon" results/phase23_sigma_zero.json  →  0
```

The record has **no `epsilon` key at all** — 43 top-level keys, none named `epsilon`. D-29's
*substance* (the σ=0 control carries no ε, so no joint bound exists once it is published) is correct
and important; its *cited precedent* does not exist. Phase 25's control-point record must **decide**
whether to write `"epsilon": null` or omit the key, and say which — there is no precedent to inherit.

For contrast, the only noised record in the repo **does** carry it:
`results/phase23_noised_dp_n64_sigma0p500000.json` → `epsilon = 519.6981942303134`, alongside
`epsilon_rule`, `epsilon_comparison_made`, `epsilon_comparison_omitted_reason`.

### §C6 — D-10: `prove_first_attempt` cannot be reused as-is

`scripts/phase23_matched_prereg.prove_first_attempt(tracked)` takes the caller's `git ls-files`
result, so mechanically a Phase-25 list can be passed. But its refusal message **hard-codes**
`MATCHED_ARTIFACT_GLOB` (`= "results/phase23_matched_*"`) into the text:

> `"… while \`git ls-files {MATCHED_ARTIFACT_GLOB}\` returned nothing …"`

A Phase-25 call would emit a refusal naming the **wrong glob**. `phase23_matched_prereg` is
EDIT-ONCE and already spent. **D-10's per-point one-attempt rule needs its own function in Phase 25's
pre-registration module** (the same module D-07 puts `prove_reproduction(k, n)` in), written in
`prove_first_attempt`'s register — four scope clauses, its own glob — and importing nothing from the
spent one. Read `prove_first_attempt`'s four clauses first; clause (1) in particular (the
uncommitted-window hole, `.gitignore:14,17`) applies verbatim to Phase 25 and must be restated with
Phase 25's paths.

---

## §R1 — What Adding the σ Ladder and `C` to `mitigation_budget.py` Actually Costs (D-17, D-24)

Not one file. **Three**, and one has an AST trap.

**Step 1 — `scripts/mitigation_budget.py`.** Add `SIGMA_LADDER` (a literal tuple of floats),
`SIGMA_LADDER_PROVENANCE`, `CLIP_NORM` (a single float literal), `CLIP_NORM_PROVENANCE`. Constraints
from `tests/test_phase23_budget.py:444-510`: module body is docstring + `ast.Assign` only; every value
must pass `ast.literal_eval` (so **no `sigma_for(...)` call, no arithmetic — `336/176` is an `ast.BinOp`
and raises**, `mitigation_budget.py:622` records this); **zero imports of any kind**, because the
`mitigation_*.py` import ceiling has zero headroom (`:497-504`).

**Step 2 — `tests/test_phase23_budget.py`.** `test_z_was_sized_against_the_ceiling` at `:1305`
asserts, under **hard equality** (`:1354-1365`):

```python
discovered = [n for n in _module_level_constant_names()
              if not n.endswith("_PROVENANCE")
              and n not in _PRE_23_13_CONSTANTS and n not in _POST_23_13_CONSTANTS]
assert tuple(discovered) == _Z_CONSTANTS
```

Simulated with the two new constants appended:

```
discovered: ['SWEEP_POINTS','CURVE_K','FULL_FIDELITY_K','STEP_BUDGET','N_CONTROL_SEEDS',
             'N64_LEG_WITHDRAWN','SIGMA_LADDER','CLIP_NORM']
_Z_CONSTANTS: [ …the first six… ]
hard-equality holds?  False
```

**This is a NATURAL RED** — the tree produces it the moment the constants land, with a message that
names the unregistered constant. No planting required. Watch it, then register each name in
`_POST_23_13_CONSTANTS` (`:340-346`) mapped to its covering test file, exactly as
`ADVERSARIAL_RATIO_GRID → test_phase24_grid.py` was.

**Step 3 — the covering test file, and the trap.** The exclusion only holds while the named test
*genuinely reads* the constant, checked at `:1336-1350` by an AST walk that collects
**`ast.Attribute.attr` names only**:

```python
read = {node.attr for node in ast.walk(ast.parse(covering_path.read_text()))
        if isinstance(node, ast.Attribute)}
assert excluded in read
```

> **A `from mitigation_budget import SIGMA_LADDER` + bare-name usage is INVISIBLE to this walk** and
> the exclusion check goes RED with *"never reads SIGMA_LADDER"*. The covering test **must** use
> `mitigation_budget.SIGMA_LADDER` attribute access — the `test_phase24_grid.py` form.

**Step 4 — the D-17 correspondence assertion, and a float fact that constrains it.** D-17 requires
`epsilon_for(sigma, 200, 1e-5)` to land on the pre-registered ε ladder under exact `==`. Measured:
**round-number ε targets are not reachable under `==` via `sigma_for` inversion.**

```
sigma_for(8, 200, 1e-5)  = 8.488520944343772   ->  epsilon_for(...) = 7.9999999999999964   != 8
sigma_for(30, 200, 1e-5) = 3.0366014333372826  ->  epsilon_for(...) = 29.999999999999986   != 30
sigma_for(1, 200, 1e-5)  = 52.75909854174823   ->  epsilon_for(...) = 1.0000000000000004   != 1
```

`sigma_for` is a numerical inverse; the round trip is exact to ~1 ULP but **not** exact. The only
`==`-satisfiable formulation is `test_phase24_grid.py`'s: pin σ as float literals and pin the ε
ladder **at the full precision `epsilon_for` returns**, asserting
`epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, DELTA) == EPSILON_LADDER[i]`. Round σ values give clean,
stable ε — `epsilon_for(0.5, 200, 1e-5) = 519.6981942303134`, which is **bit-identical to the ε
already committed in `results/phase23_noised_dp_n64_sigma0p500000.json`**. That is the precedent.

**The measured ε(σ) curve at T=200, δ=1e-5** (re-measured this session; every CONTEXT figure
reproduced):

| σ | ε |
|---|---|
| 0.10 | 10602.161437899067 |
| 0.50 | 519.6981942303134 |
| 1.0 | 159.44148628736576 |
| 2.0 | 54.37663901498563 |
| 5.0 | 15.456155822609311 |
| 8.0 | 8.595865790470416 |
| 20 | 2.943225239801367 |
| 80 | 0.6339783761989397 |

**Also:** `CLIP_NORM` must be the same `1e6` Phase 23 used if D-01's bit-level reproduction is to
hold — `results/phase23_sigma_zero.json` records `clip_norm = 1000000.0`, `clip_bind_count = 0`. A
D-24-calibrated `C` for the *noised* points is a **different** number from the control's 1e6, so the
module needs **two** pinned clip constants or one pin plus a named control exception. CONTEXT does
not resolve this; the planner must.

---

## §R2 — Cost, Reproduced From the Committed Record

Every figure below is read from `results/phase23_cost.json` or `results/phase23_never_taught.json`
this session. **CONTEXT's ~107 h / ~150 h envelope reproduces.**

| Term | Source | Value |
|---|---|---|
| `sizing["16"].h_per_point_ceiling_at_k` | `phase23_cost.json` | **3.1471532286150796 h/point** |
| `sizing["16"].h_per_point_floor_at_k` | `phase23_cost.json` | 1.9979696709667354 h/point |
| observed never-taught rate (5 seeds) | `phase23_never_taught.json:scoring_seconds_per_seed` | 7334.8 / 7294.9 / 7292.0 / 7277.1 / 7295.8 s → **mean 7298.9 s = 2.0275 h** |
| training `dp_n8` / `dp_n64` / `non_dp` | `phase23_cost.json:training`,`ratios` | 205.4 s / 1383.3 s / **161.124 s** |
| 44 points × observed rate | derived | **89.2 h** |
| 44 points × ceiling | derived | **138.5 h** |
| + DP training (16×205.4 + 16×1383.3) | derived | 7.06 h |
| + D-03 n=64 matched floor | CONTEXT (measured) | 3.3 h |
| + D-04 / D-14 / D-18 probes | CONTEXT (measured) | ≈ 1.6 h |
| **envelope** | | **≈ 101 h observed → ≈ 150 h ceiling** ✓ |

**The floor/ceiling gap is the stop-termination regime, and it is not uniform across the sweep.** A
noised adapter that stops emitting EOS runs every draw to the full token budget
(`test_phase23_budget.py:1313-1318`). Low-σ points sit near the floor (2.0 h); high-σ points sit near
the ceiling (3.15 h). Schedule and heartbeat thresholds must be sized against the **ceiling**, which
is what `sized_against: "h_per_point_ceiling"` already pins.

**Disk, measured:** 494 GiB free. `*_adapter.pt` = **1,352,069 B** ✓ (D-37's 1.35 MB). **But
`arm_outputs` (`teach_persona.py:369-380`) also names `checkpoints/{prefix}_{arm}_latest.pt`, and
those measure ≈ 59,691,603 B each.** If every point retains its full resume checkpoint, 44 points is
**≈ 2.5 GB, not 59 MB** — a 42× under-estimate in D-37's precheck. Harmless here (494 GiB free,
`checkpoints/` is already 7.8 GB) but the precheck should be sized correctly or the retention rule
should say *adapter only*.

**Artifact size, D-31's ~9.7 MB:** confirmed arithmetically. `phase23_never_taught.json` = 1.1 MB for
4,320 `per_question` rows ⇒ ~254 B/row; 44 points × 864 questions = 38,016 rows ⇒ **≈ 9.7 MB** ✓.
Gitignored draw caches add ≈ 973 KB/point ⇒ ≈ 43 MB in `data/` at K=16.

---

## §R3 — The Point-Record Schema Already Exists

`results/phase23_noised_dp_n64_sigma0p500000.json` is the template for all 44 point records. Real
top-level keys measured this session:

```
arm, clip_bind_count, clip_bind_count_covers_steps, clip_is_binding, clip_norm, clip_provenance,
composed_lot_sizes, composed_steps, delta, device, epsilon, epsilon_comparison_made,
epsilon_comparison_omitted_reason, epsilon_rule, exports_adapter, gate, git_sha, governs,
ppl_adapter_off, ppl_adapter_on, ppl_scored_targets, python_version, recipe, record,
records_per_lot, seed, sigma, sigma_provenance, sweep_point, t_matches_across_capacities, t_n64,
t_n8, t_n8_source_record, timestamp, torch_version, training
```

**D-34's five live-read fields:** `composed_steps` ✓, `composed_lot_sizes` ✓, `records_per_lot` ✓,
`clip_norm` ✓ — **`q` is ABSENT** and is the one genuinely new field (source:
`mitigation_unit.SAMPLING_RATE_Q = 1.0`, verified live). Everything else D-34 asks for is already
in the schema.

**Anchors the driver must import, never retype** (all verified live):

| Quantity | Import site | Value |
|---|---|---|
| `extraction_noise_floor` | `results/phase23_never_taught.json` top level | `0.0` |
| `extraction_floor_provenance` | same, top level | `arm='never-taught'`, 5 seeds |
| `control_extraction_{successes,questions}` | `…["pooled"]` | `0` / `416` |
| `retention_noise_floor` | `scripts/phase20_gate_coverage.py:370` `_ADAPTER_REGIME_RETENTION_FLOOR` | `0.008681618994239138` |
| governing retention cap (derived) | `mitigation_gate.retention_cap` | `3.9085032379884783` — **not** `4.029` (`STATE.md:1625-1628`) |
| `control_taught_recall` | `results/phase23_matched_verdict.json:central_reading` | `0.7837301587301587` |
| matched floor | `mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR` | `0.0267857142857143` |
| `F_Y` / `F_C` / `K_RUNGS` / `MARGIN_K` | `mitigation_gate` / `erasure_gate` | `0.7` / `0.5` / `(48,24,16,8)` / `2` |
| `GATED_TIER` / `REPORTED_TIER` / `ATTACK_FAMILIES` | `phase18_extraction` | `core_held_out` / `core_taught` / 4 families |

**Verdict ordering constraint the planner must respect:** `mitigation_point_verdict` takes
`sweep_extraction_rates` and `sweep_taught_recalls` — **whole-curve** inputs (GATE-06's
did-the-curve-cross check, `:695-699`). So the per-point **record** lands incrementally (D-31) but the
per-point **verdict cannot be computed until the leg's curve is complete**. Plan the verdict pass as a
distinct, cheap, CPU-only stage after the sweep, reading the committed records — not as part of each
point.

---

## §R4 — Cross-Checked Records (all read this session)

| Record | Field | Measured |
|---|---|---|
| `phase23_sigma_zero.json` | `primary.k` / `primary.n` | **790 / 1008**; rate `0.7837301587301587` |
| | `clip_norm` / `clip_bind_count` | `1000000.0` / `0` |
| | `composed_steps` / `composed_lot_sizes` / `records_per_lot` | `200` / `[8]` / `8` |
| | `epsilon` | **absent** (see §C5) |
| `phase23_matched_verdict.json` | `verdict` / `deviation` / `halt_message` / `floor` | `"proceed"` / `0.0` / `null` / `0.0267857142857143` |
| `phase23_matched_control.json` | `declared_differences` | **4** entries ✓ (dp_noise_rng slot; arm name/paths; DP object graph; the two `masked_perplexity` sweeps) |
| | `grad_clip_evidence` max pre-clip norm | `2.277 / 2.202 / 2.302` across seeds — **batch-level**, all `bound_count: 0` ✓ D-24's premise |
| `phase23_control_floor.json` | `central_reading` / `floor` | `0.5615079365079365` / `0.05357142857142849` |
| `phase23_cal03_wiring.json` | `epsilon_n8` == `epsilon_n64` / `t_n8` == `t_n64` / `verdict` | `24.38161088311366` both / `4` both / `true` ✓ D-08 |
| `phase21_multiplicity.json` | `pin_discrepancy.pin_figure` / `artifact_rule_figure` | `262.9437465865647` / `207.0180229382851`; `status: "RECORDED, NOT RESOLVED — the pin is frozen and is not edited"`; `provenance.epsilon_computed: false` ✓ D-28 |
| `phase24_adversarial` | `HELD_OUT_FAMILY` / `TRAINED_FAMILIES` | `A2` / `('A1-mild','A1-aggressive','A3')` |
| `phase14_recall` (D-39) | `contains_refusal(completion, templates)` / `score_refusal(completions, templates) -> (k, n)` / `clean_frame_probe_populations()` | all three **exist and are importable** ✓ |

---

## §R5 — The Venue, Measured At HEAD

```
$ pmset -g
 sleep      1 (sleep prevented by AddressBookSourceSync, caffeinate, caffeinate, caffeinate,
                caffeinate, caffeinate, Claude)
 disksleep  10
 powernap   1
```

✓ CONTEXT's `sleep 1` confirmed, and `disksleep 10` / `powernap 1` are exactly D-13's revert targets.

**Correction for D-43's verification method.** `pmset -g`'s "sleep prevented by" line enumerates
**assertions**, not processes — it lists five `caffeinate` entries while only **three** caffeinate
processes exist (`pgrep -x caffeinate` → `7591 46029 58309`). Deduped owners from
`pmset -g assertions`: `pid 46029(caffeinate)`, `pid 58309(caffeinate)`, `pid 7591(caffeinate)`,
`pid 578(dasd)`, `pid 70095(Claude)`. **D-43's "verified by reading `pmset -g` back after launch"
cannot be done from the summary line** — it must read `pmset -g assertions` *listed by owning process*
and cross-check `pgrep -x caffeinate`, or "the run's own `caffeinate` is the only non-system
assertion" is unverifiable.

**The prior venue recipe, and why D-12 is an escalation of it rather than a novelty.**
`.planning/STATE.md:525-541` records 23-20's launch discipline, used for six real launches:
`os.setsid()` + `os.execv`, pid read **from the log** never `$!`, probed with `os.getsid()`,
`caffeinate -is -w <pid>`, `pid == pgid == sid` quoted **before any GPU second**. No LaunchAgent
exists in the repo (`grep -rln "launchctl\|LaunchAgent\|\.plist" scripts/ tests/` → nothing;
`.planning/STATE.md` only). D-12's `caffeinate -dims` (wrapping, holding its own assertion) is a
different and stronger form than `-is -w` (watching another pid) — name the change deliberately.

---

## §O1 — The One Unresolved Architectural Tension (OPEN QUESTION)

**`.planning/STATE.md:525-527`, recorded as a mechanism:**

> *"THE PER-SEED COMMIT DISCIPLINE HELD, AND IT IS A MECHANISM. **The driver's git surface is
> read-only**, so the sub-mode scores exactly ONE unscored seed and **exits**; the commit is the
> operator's act at the process boundary."*

Verified at source: `scripts/phase23_run.py` calls git only for `ls-files` (`:862`, `:2148`), `show`
(`:2194`) and `merge-base` (`:2886`). **Zero `commit` / `add` calls.**

This collides with three Phase-25 decisions at once:

- **D-10** — each point's committed record *is* the one-attempt evidence.
- **D-31** — per-point records land **incrementally**, and the frontier assembly's `refuse_if_dirty(pathspec=("scripts","src","results","artifacts", …))` **requires a clean tree**, so 43 uncommitted point records would refuse the final write.
- **D-12** — the sweep runs unattended for 4.5–6.3 days as a LaunchAgent with **`KeepAlive` FALSE**, i.e. no supervisor to re-launch it and no operator at the process boundary 44 times.

Three of these cannot all hold. The two resolutions, stated neutrally:

1. **The driver commits.** Phase 25 abandons the read-only-git-surface discipline for an unattended run, with the commit narrowly scoped (`git add <the one record> && git commit`) and the widened surface named explicitly in the pre-registration. Preserves D-12 exactly.
2. **The driver still exits per point; a thin supervisor commits and relaunches.** Preserves the read-only surface but is functionally `KeepAlive` by another name and must be reconciled with D-12's stated reason for `KeepAlive: FALSE` (an automatic restart re-entering a point without passing the deliberate resume logic).

CONTEXT names neither. It is not obviously covered by the discretion list — the LaunchAgent's *shape*
is discretionary, the driver's *git surface* is a recorded mechanism. **Surface this to the user at
plan time rather than choosing silently.**

---

## Validation Architecture

> The orchestrator builds `25-VALIDATION.md` from this section. `workflow.nyquist_validation: true`
> in `.planning/config.json` (measured).

### Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` 8.x — `[tool.pytest.ini_options]`, `pyproject.toml:24-26` |
| **Config** | `testpaths = ["tests"]`, `pythonpath = ["."]`; `tests/conftest.py` **exists** (D-44's natural home for a `--sweep-active` option) |
| **Quick run** | `.venv/bin/python -m pytest tests/test_phase25_*.py -q` |
| **Full suite** | `make test` → `.venv/bin/pytest -q` (`Makefile:12-13`) |
| **Measured suite size** | **1648 collected** (`pytest --collect-only -q` → `1648 tests collected in 2.84s`) |
| **Measured full-suite runtime** | **1647 passed, 1 skipped, 83 warnings in 386.21s (0:06:26)** — wall 387.73 s, run this session at `8dd6415` |
| **Lint** | `make lint` → `ruff check . && ruff format --check .` (`Makefile:15-16`) |
| **CI** | `.github/workflows/ci.yml` — ubuntu-latest, Python 3.11, CPU-only. Every MPS leg must stay `skipif`-gated |
| **MPS register** | `tests/test_phase23_mps_venue.py:60-80` — the ONE definition; 5 importers + `test_mps_smoke.py:30-31` standalone |
| **MPS-parametrized node ids** | **47** across 11 files; device-touching in 7 (§ledger row 11/11a) |

### The Nyquist question, answered from measurement (D-12 / D-16)

D-16 says `N` is *"derived from the measured worst-case gap between heartbeat lines at the slowest
attack shape"*. That measurement, taken this session:

**Existing print cadence** — `scripts/phase23_run.py:4524`: `if (index + 1) % 24 == 0 or index + 1 == len(cell)`, i.e. **one line per 24 prompts**.

**Per-shape timings, seed 1337, K=16, 216 prompts/shape** (`data/phase23_never_taught_seed1337_draws.json`, `shapes[*].timing`):

| shape | minutes | draws/min | **24-prompt gap** |
|---|---:|---:|---:|
| A3 | 34.034 | 101.54 | **3.78 min** |
| A1-aggressive | 32.731 | 105.59 | 3.64 min |
| A1-mild | 29.013 | 119.12 | 3.22 min |
| A2 | 26.468 | 130.57 | 2.94 min |

**Projected into the ceiling (no-EOS) regime** from `phase23_cost.json:generation.per_shape`:

| shape | ceiling min/shape @K=16 | **24-prompt gap** |
|---|---:|---:|
| A1-mild | 45.27 | **5.03 min** ← worst |
| A3 | 43.82 | 4.87 min |
| A1-aggressive | 43.53 | 4.84 min |
| A2 | 43.25 | 4.81 min |

At `FULL_FIDELITY_K = 48` (D-11 promotion) these triple: **≈ 15.1 min**.

**But the true worst-case gap is not in the draw loop.** `dp_n64` training is **1383.3 s = 23.06 min**
of a point with **no per-shape line at all**, plus `recall.load_adapted_model` at each scoring start.
An event-driven heartbeat tied to the prompt counter therefore forces `N ≥ ~35 min` to avoid firing
on every one of the 22 n=64 training legs — **7× coarser than the draw loop can resolve, and it buys
nothing.**

> **PRESCRIPTION.** Emit the heartbeat from the driver's **outer loop on a wall-clock timer**
> (60 s), carrying `(utc, point, stage, shape, draw_index)`, so the sampling rate is independent of
> which stage is running. Then set **`N = 5 min`** — ≥ 5 missed beats before a stall record is
> written, no false positive from a 5.03-min draw gap or a 23-min training leg, and detection
> latency 5 min against a 107–150 h run (**0.005%** of the run). Record N's derivation *from the
> table above*, which is what D-16 asks for.
>
> **The heartbeat and the stall watcher must themselves be watched.** Neither has ever been seen
> firing. Before the sweep: run the driver against a deliberately-stalled stub and observe the
> watcher writing a stall record — and observe that it does **not** kill, restart or clean up
> (D-16's detect-never-act half is the property most likely to rot).

### Distinguishing a kill from a genuine failure

| Signal | Where it is written | What it distinguishes |
|---|---|---|
| shape block present in `blob["shapes"][family]` with `draws` + `timing` | `data/phase25_*_draws.json` (gitignored) | a completed shape from an interrupted one — **the resume unit** |
| cache identity `(adapter_sha256, corpus_sha256, k)` | same, refused at load (`phase23_run.py:4281-4291`) | draws off different weights / corpus / budget — refuses rather than pools |
| committed per-point record present in `results/` | `git ls-files` | **"a reading landed"** vs "the point was killed before any reading" — D-10's one-attempt unit |
| per-shape sha256 committed as each block lands (D-10) | the point record | closes the delete-and-redraw leak, since `data/` is gitignored (`.gitignore:17`) |
| heartbeat last line | the heartbeat file | *where* it died — stage, point, shape, draw index |
| stall record | the watcher's output | silence detected, **no action taken** |

**Corollary the planner must not miss:** the block writer must become **atomic** (tmp + `os.replace`).
`_never_taught_write_draws` (`phase23_run.py:4300-4302`) is a bare `path.write_text` over ~970 KB, and
a kill mid-write yields a JSON that `json.loads` rejects — turning "lost one shape" into "lost the
whole point", the exact failure D-09 exists to prevent. There is **no atomic-write helper in the
repo** to reuse.

### Cheap (CPU, seconds) vs expensive (MPS, hours) — and where the proxy lives

| Property | Expensive form | **Cheap proxy that must exist first** | Cost |
|---|---|---|---|
| `clip_norm=inf` is refused (CTRL-02) | discovering it mid-sweep | `DPSGD(nn.Module(), sigma=0.0, clip_norm=math.inf)` → `ValueError[dp-refusal:clip-domain]`; the domain check is PRE-PASS 1, **no model needed** | **ms** |
| the gate's null branch is reachable (D-32/FRONT-04) | running 44 points | `capacity_comparison(small_cleared=False, large_cleared=False, …)` → `'null-at-both-capacities'` | **ms** |
| extra mechanism keys are ignored (D-25) | a silently-incomparable capacity verdict | live `capacity_comparison` with divergent `clip_norm` → passes; then the caller-side `_prove` refuses | **ms** |
| condition (a) is zero-tolerance (D-42) | reading it off a published verdict | `tolerance_report(ceiling=X, n_questions=416)` → `(0, 0.0, "ZERO TOLERANCE…")` | **ms** |
| a 21-kwarg verdict assembles | after the sweep | live `mitigation_point_verdict(...)` with the never-taught pooled block → `('PASS', […], 'dp')` | **ms** |
| the σ ladder ↔ ε ladder correspondence (D-17) | a mis-pinned grid discovered at point 30 | `epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, DELTA) == EPSILON_LADDER[i]`, stdlib `math` only | **ms** |
| mask fraction stays in band at every grid corner | a `SystemExit` **after** the compute is spent | the 24-07 four-corner build-only check, already green | **2.2 s** |
| bins rebuild byte-identically after a kill (D-09) | a 2 h loss | `tests/test_phase23_resume.py` | **s** |
| the budget register is complete (D-17/D-24) | a constant shipping with no re-derivation | `test_z_was_sized_against_the_ceiling` — **natural RED** (§R1) | **s** |
| the plotting module never loads torch (D-33) | a figure not regenerable from a clone | `test_phase15_plots.py:291-352` retargeted | **~1 s** (subprocess) |
| D-01's reproduction (790/1008) | ~40 s train + **2.04 h** score per capacity | *none exists* — this one is genuinely expensive, which is why `prove_reproduction` HALTS at zero sweep points (D-07) | **h** |
| adversarial scoring throughput | ~95% of the spend | D-14's timed 768-draw probe at both extremes | **≈30 min** |

**The rule:** every structural invariant in this phase has a millisecond CPU proxy. **No plan should
discover a structural fact by spending GPU hours.** Build all of the ms-cost gates in Wave 0, before
any point runs.

### Structurally checked vs merely declared

| Decision | Invariant | Structural? | Where | Watched RED? |
|---|---|---|---|---|
| D-04 | no later plan asserts bit-identity between σ=0 and seam-off | **yes** — armed tripwire test | Wave 0, new module | ⚠️ needs a **planted** RED (no natural one) — plant against a scratch copy, never the real file (this repo has been burned by planted REDs landing on the wrong occurrence) |
| D-07 | `prove_reproduction(k, n)` HALTS at zero sweep points on a miss | **yes** — hard `==` on integer counts (`k==790`, `n==1008`) | Phase-25 prereg module | ✅ natural: call it with `(789, 1008)` in a unit test and watch the halt message |
| D-25 | `clip_norm` equal across the two compared capacities | **yes** — caller-side `_prove` before the gate | driver | ✅ natural: the live divergent-`clip_norm` call in §ledger 2c already demonstrates the hole the `_prove` closes |
| D-30 | no bare ε printed outside the helper | **yes** — AST walk over the phase's modules | Wave 0 | ✅ natural: `mitigation_gate.py` itself carries `epsilon` **inside string literals** (2 in `exists_clearing_point`, 23 in `capacity_comparison`) with `ast.Name` count **0** — a grep gate goes false-RED on it today. Demonstrate grep-RED / AST-GREEN on the real file |
| D-33 | the plotter opens only `results/phase25_frontier.json` and never torch | **partly** — (a)(b)(c) port; the artifact allow-list is new | new sibling of `test_phase15_plots.py` | ✅ natural for (a)(c) (add `import torch` to a scratch copy); the allow-list clause needs its own RED |
| D-34 | live mechanism matches the pin, or the **whole sweep** halts | **yes** — exact `==` on 5 fields read at write time | driver | ✅ natural: write a record with `composed_steps=199` in a unit test |
| D-36 | `held_out_generalization` re-derives exactly from per-point counts | **yes** — write-time assertion | assembly | ✅ natural: perturb one per-family count in a fixture |
| D-42 | X comes from the designated-seed pooled block, never re-reduced | **yes and already enforced** — `extraction_ceiling` `_prove`s `provenance["arm"] == NEVER_TAUGHT_ARM`, and `tolerance_report` **refuses** the 5-seed X outright | frozen gate | ✅ already watched: the `ValueError` in §L8 is a live refusal, reproduced this session |
| D-44 | MPS legs skip with a reason naming the sweep | **yes** — `skipif` at the register | `test_phase23_mps_venue.py:60-76` + `test_mps_smoke.py:30-31` | ✅ natural: set the env var and assert the skip **count** and the **reason text** |

### Requirements → test map

| Req / D | Behaviour asserted | Type | Command | Exists? |
|---|---|---|---|---|
| CTRL-02 / D-01 | `clip_norm=math.inf` raises `[dp-refusal:clip-domain]`; `C=1e6` gives `clip_bind_count == 0` | unit (CPU) | `pytest tests/test_phase25_control.py -k clip_domain -x` | ❌ W0 |
| CTRL-01 / D-07 | `prove_reproduction(790, 1008)` passes; any miss HALTS with the ratio-0.0 / declared-differences message | unit, both branches | `pytest tests/test_phase25_prereg.py -k reproduction -x` | ❌ W0 |
| CTRL-01 / D-04 | armed tripwire fires if any later plan asserts σ=0 ≡ seam-off bit-identity | structural (AST) | `pytest tests/test_phase25_prereg.py -k bit_identity_tripwire -x` | ❌ W0 |
| FRONT-01 / D-17 | `epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, DELTA) == EPSILON_LADDER[i]` under exact `==`; ladder len == `SWEEP_POINTS` | unit | `pytest tests/test_phase25_grid.py -x` | ❌ W0 |
| FRONT-01 / D-17,24 | budget register completeness after adding σ and C | structural (AST, hard `==`) | `pytest tests/test_phase23_budget.py::test_z_was_sized_against_the_ceiling -x` | ✅ **exists and will go naturally RED** (`:1352-1365`) |
| FRONT-01 / D-24 | `C` re-derives from the committed per-record-norm measurement | unit (re-derivation) | `pytest tests/test_phase25_grid.py -k clip_norm_re_derives -x` | ❌ W0 |
| FRONT-02 / D-30 | no `print`/f-string/`.format`/`%` over a committed ε-name set outside the helper | structural (**AST, never grep**) | `pytest tests/test_phase25_epsilon.py -x` | ❌ W0 |
| FRONT-02 / D-28 | both multiplicities named; 262.9437465865647 and 207.0180229382851 both present, neither hidden | structural (`_prose.normalized` containment) | `pytest tests/test_phase25_record.py -k multiplicity -x` | ❌ W0 |
| FRONT-03 / D-31 | ordered `point_keys` hard equality on write; `accounting: null` on the adversarial arm; gate+budget sha256s inside | structural (write-time) | `pytest tests/test_phase25_record.py -x` | ❌ W0 |
| FRONT-03 / D-36 | `held_out_generalization` re-derives **exactly** from per-point A2 counts | unit | `pytest tests/test_phase25_record.py -k held_out -x` | ❌ W0 |
| FRONT-03 / D-33 | the plotter imports no torch (AST + fresh-interpreter) and opens only the frontier artifact | structural + subprocess | `pytest tests/test_phase25_plots.py -x` | ❌ W0 (ports `test_phase15_plots.py:291-352`) |
| FRONT-04 / D-32 | `_CAPACITY_DISPATCH[(False,False)] == "null-at-both-capacities"` reached through a real call; `exists_clearing_point` carries its denominator | unit | `pytest tests/test_phase25_verdict.py -x` | ❌ W0 |
| FRONT-04 / D-23 | `capacity_comparison` is never called with an adversarial point; the absence of an adversarial capacity rule is stated **in the artifact** | structural (AST over the driver + record key) | `pytest tests/test_phase25_verdict.py -k dp_only -x` | ❌ W0 |
| D-25 | driver `_prove`s `clip_norm` equality **before** the gate call | unit (refusal) | `pytest tests/test_phase25_verdict.py -k clip_norm_equality -x` | ❌ W0 |
| D-34 | any of the 5 live-read mechanism fields diverging halts the sweep | unit ×5 | `pytest tests/test_phase25_driver.py -k mechanism -x` | ❌ W0 |
| D-09 | a complete shape is skipped on restart; an incomplete one is redrawn; the write is atomic | unit | `pytest tests/test_phase25_driver.py -k resume -x` | ❌ W0 |
| D-10 | a point with a committed record is refused a second attempt; the message names **Phase 25's** glob | unit (refusal) | `pytest tests/test_phase25_prereg.py -k one_attempt -x` | ❌ W0 (must NOT reuse `phase23_matched_prereg.prove_first_attempt` — §C6) |
| D-16 | the watcher writes a stall record and does **not** kill/restart/clean | unit (both halves) | `pytest tests/test_phase25_watch.py -x` | ❌ W0 |
| ADVT-01 / D-41 | WR-01 negative/NaN ratio refused on **both** branches; WR-04 replay+adversarial refused on the flat branch; WR-06 one pool read; WR-08 bins written **after** the proofs | unit ×4 (refusals) | `pytest tests/test_phase25_wr.py -x` | ❌ W0 |
| D-39 | every adversarial point carries a refusal-rate column **in counts**, and it is **outside** the three-condition gate | structural | `pytest tests/test_phase25_record.py -k refusal -x` | ❌ W0 |
| D-42 | X imported by object identity; `tolerance_report` renders **ZERO TOLERANCE** into (a)'s reason; the 5-seed X is refused | unit | `pytest tests/test_phase25_verdict.py -k tolerance -x` | ❌ W0 |
| RPT-02 / D-02,19 | three dated continuations, each bounded by exactly one sentinel pair, matched through `_prose.normalized`, claim still standing | structural ×3 | `pytest tests/test_phase25_correction.py -x` | ❌ W0 (copies `test_phase24_correction.py`'s four mechanics) |
| D-44 | MPS legs skip with a reason naming the sweep when the env var is set; skip count is exact | unit | `SWEEP_ACTIVE=1 pytest tests/test_phase25_venue.py -x` | ❌ W0 |
| D-13 | the `pmset` revert is a committed, verifiable step | structural (operational note re-read) | `pytest tests/test_phase25_venue.py -k pmset -x` | ❌ W0 |

### Sampling rate

- **Per task commit:** `.venv/bin/python -m pytest tests/test_phase25_*.py -q` — target **< 30 s**.
  **Plus** `pytest tests/test_phase20_prereg.py -k import_graph -q` on any task touching
  `scripts/mitigation_*.py`, and `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py scripts/mitigation_unit.py scripts/phase18_extraction.py` returning **0** — those four are ancestry-guarded and permanently uneditable.
- **Per wave merge:** `make test` on the M3 (**measured 6m26s**, 1647 passed / 1 skipped) plus `make lint`.
  **Record the skip count explicitly** — a green run that skipped the MPS legs is the failure, not the pass.
- **While the sweep is running:** the full suite becomes **contending**, not free. Run it with
  D-44's sweep-active flag set and expect the MPS legs to skip **loudly**, with the reason naming
  the sweep, and the skip count to move from **1** to a number stated in advance. A contention
  failure must never be readable as a genuine one.
- **Phase gate:** full suite green on the M3 with the sweep **not** running and **zero** unexpected
  skips; quote the literal `N passed, M skipped` line. Baseline to beat: **1647 passed, 1 skipped**.
- **Max feedback latency:** 30 s per task; one 6.5-minute full-suite run per wave.

### Wave 0 requirements

- [ ] `tests/test_phase25_prereg.py` — `prove_reproduction` (both branches), the D-04 tripwire, Phase 25's **own** one-attempt rule (not `phase23_matched_prereg`'s)
- [ ] `tests/test_phase25_grid.py` — the σ↔ε correspondence under exact `==`, `C`'s re-derivation, and the covering-test **attribute-access** requirement (§R1 step 3)
- [ ] Register `SIGMA_LADDER` / `CLIP_NORM` in `tests/test_phase23_budget.py::_POST_23_13_CONSTANTS` — **after** watching the natural RED
- [ ] `tests/test_phase25_epsilon.py` — D-30's AST gate, demonstrated grep-RED / AST-GREEN on `scripts/mitigation_gate.py`
- [ ] `tests/test_phase25_record.py` — `point_keys` ordering, `accounting: null`, sha256 carriage, D-36 re-derivation, D-39 refusal counts, D-28 dual multiplicity
- [ ] `tests/test_phase25_verdict.py` — the null branch, DP-only scoping, `clip_norm` caller-side equality, D-42's zero-tolerance sentence
- [ ] `tests/test_phase25_driver.py` — D-34's five halts, D-09's resume + **atomic write**
- [ ] `tests/test_phase25_watch.py` — the heartbeat and the detect-never-act watcher, both halves watched
- [ ] `tests/test_phase25_wr.py` — WR-01 / WR-04 / WR-06 / WR-08 refusals, each watched RED
- [ ] `tests/test_phase25_plots.py` — the retargeted figure guard (ports `test_phase15_plots.py:291-352` + the new allow-list clause)
- [ ] `tests/test_phase25_correction.py` — three sentinel-bounded continuations through `_prose.normalized`
- [ ] `tests/test_phase25_venue.py` — D-44's sweep-active skip (assert count **and** reason text), D-13's revert
- [ ] `tests/conftest.py` — the `--sweep-active` option / env var read
- [ ] Framework install: **none**. pytest 8.x, ruff and the venv are present and green at 1647/1

### Two failure modes this contract exists to catch

1. **A structural fact discovered by spending GPU hours.** Every invariant in this phase has a
   millisecond CPU proxy (see the table above) and all of them belong in Wave 0. The measured
   precedent is 24-07, which converted a post-compute `SystemExit` into a 2.2-second CPU test.
2. **A contention failure read as a genuine one.** During a 4.5–6.3 day sweep the 47 MPS-parametrized
   node ids run and contend. D-44's skip must be **loud** — a named reason and a stated skip count —
   because the silent version is indistinguishable from the MPS legs having been quietly lost, which
   is the failure `23-VALIDATION.md` already names as Pitfall 1.

---

## Implementation Ordering (what the planner should sequence)

**Wave 0 — everything cheap, before any GPU second.** The full Wave-0 list above, plus the three
dated continuations (§C3) and the RPT-02 traceability repair (§C4). Every guard watched RED. This
wave is entirely CPU and should complete in well under an hour of compute.

**Wave 1 — the pins.** σ ladder + `C` into `mitigation_budget.py` (§R1, three files, natural RED
first). D-18's σ_hi calibration probe (~20-40 min, named prefix, excluded from the point set) is the
only GPU work, and its output feeds the ladder — so the ladder is committed **after** the probe, as
D-18 requires.

**Wave 2 — the fixes and the calibrations.** D-41's five WR fixes in `teach_persona.py`
(§ledger 5a — resolve each line by content, never from 24-REVIEW). D-24's `vmap` per-record norm
pass at both capacities (seconds to minutes). D-04's PROBE 2 at both capacities (~46 min).
D-14's adversarial throughput probe at both extremes (~30 min). The schedule is finalised **only
after** D-14 returns.

**Wave 3 — venue.** LaunchAgent + `caffeinate -dims` + heartbeat + watcher; D-43's assertion clear
verified through `pmset -g assertions` (§R5), not the summary line; D-13's `pmset` change **and its
committed revert step**; D-44's sweep-active skip proven working. **Resolve §O1 before this wave
ships.**

**Wave 4 — the run.** D-01's controls, D-03's n=64 matched floor, then D-15's eight extremes
**interleaved**, then the interior. 44 points, ~101–150 h.

**Wave 5 — assembly and verdict.** The CPU-only verdict pass (whole-curve inputs, §R3), the
write-once frontier assembly, the figures, D-40's committed publication obligation, D-37's three
Phase-26 reservations.

---

## Risks

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R1 | **A plan quotes "tolerance = at most 2 successes"** and contradicts the artifact it ships beside | §L8 — the gate renders `ZERO TOLERANCE` into (a)'s reason | Correct the figure everywhere in planning text; assert the artifact's own sentence in a test |
| R2 | **A task justified by "the gate requires the control's extraction"** fails plan-check | §L8b — measured; the gate reads the never-taught block | Re-justify by CTRL-02 + FRONT-03 |
| R3 | **A continuation routed through `append_addendum`** either fails (`found == 0`) or splices on an accidental substring with a vacuous verdict guard | §ledger 6 — measured live on both planning docs | Use the 23-12 / 24-03 sentinel + `_prose` pattern |
| R4 | **A non-atomic block write** turns "lost one shape" into "lost the point" during a 6-day run | `phase23_run.py:4300-4302`; no atomic helper in the repo | tmp + `os.replace` in D-09's port |
| R5 | **Adding σ/C to the budget without registering them** ships constants with no re-derivation | `test_phase23_budget.py:1352-1365` hard equality | Watch the natural RED, then register + covering test using **attribute access** |
| R6 | **A heartbeat threshold derived only from the slowest attack shape** fires on every n=64 training leg or is set so coarse it detects nothing | measured: 5.03 min draw gap vs 23.06 min training leg | Wall-clock timer heartbeat, N = 5 min |
| R7 | **The unattended driver cannot commit**, so `refuse_if_dirty` refuses the final assembly after 6 days of compute | §O1; `phase24_record.py:476-481` | Resolve §O1 with the user before Wave 3 |
| R8 | **A plan copies a line number from 24-REVIEW.md or CONTEXT's `dpsgd.py:74-80`** and edits prose | §ledger 1, 5a — every cited line is stale or a docstring | Resolve every site by content at plan time; AST gates over `dpsgd.py` and `mitigation_gate.py` |
| R9 | **A grep acceptance criterion over `mitigation_gate.py` or `dpsgd.py`** goes false-RED | measured: `epsilon` 23× in string literals with `ast.Name` count 0; `std=` 5× of which 1 is code | AST only, per D-30 |
| R10 | **D-37's 59 MB precheck under-sizes by 42×** if `latest.pt` is retained per point | measured: adapter 1.35 MB, `latest.pt` 59.7 MB | Size the precheck at ~2.5 GB or restrict retention to the adapter |

---

## Open Questions

1. **The driver's git surface during an unattended run.** §O1. Two resolutions, both with a cost; CONTEXT resolves neither and it is not clearly discretionary. **Ask.**
2. **One `C` or two?** D-01 needs the control at `1e6` (bit-level reproduction against `phase23_sigma_zero`); D-24 calibrates a different `C` for the noised points. `mitigation_budget.py` must hold either two pinned clip constants or one plus a named control exception. Not resolved in CONTEXT.
3. **Does the control point record `"epsilon": null` or omit the key?** §C5 — there is no precedent to inherit, and D-29's cited one does not exist. A decision, not a lookup.
4. **The RPT-02 traceability row's disposition.** §C4 — the checkbox is `[x]` and the row says DEFERRED. Repair the row additively (naming 23-12 and 24-03) and add Phase 25's third instance, or does the user want the row rewritten? Additive is this project's default; confirm.
5. **Exact skip count under D-44.** 47 node ids carry "mps"; 7 files touch the device; 5 ids are name-only. The stated-in-advance skip count depends on which set the flag covers. Recommend: the 7 device-touching files only; state the resulting number before the sweep.

---

## Sources

**Primary — read or executed at HEAD `8dd6415`, this session:**

- `src/personacore/privacy/dpsgd.py:52-95` (docstring), `:125-201` (`__init__` domain checks), `:295-296`, `:483-502` (the single draw site)
- `src/personacore/privacy/accountant.py` — `epsilon_for`, `sigma_for` (live-measured curve and inversions)
- `scripts/mitigation_gate.py:637-831` (`mitigation_point_verdict`, 21 kwargs, 195 lines), `:842-905` (`exists_clearing_point`), `:1026-1058` (`MECHANISM_KEYS`, `CAPACITY_BRANCHES`, `_CAPACITY_DISPATCH`, totality `_prove`), `:1061-1186` (`capacity_comparison`), `extraction_ceiling` and `tolerance_report` (live)
- `scripts/mitigation_budget.py:121-143, 277-303, 374-376, 425-427, 473-475, 508-510, 544-546, 586, 622, 633-635`
- `scripts/mitigation_unit.py` — `SAMPLING_RATE_Q = 1.0`, `DELTA = 1e-05`, `PRIVACY_UNIT`, `REPLAY_OUTSIDE_N`
- `scripts/erasure_gate.py` — `wilson_upper_bound(successes, n, z=1.6448536269514722)`, `MARGIN_K = 2` (object identity with `mitigation_gate` verified)
- `scripts/phase23_run.py:4259-4302` (cache path / load / write), `:4435-4475` (resume-skip branch), `:4495-4561` (draw loop, 24-prompt print cadence, per-shape persist), `:4690-4756` (`_never_taught_evidence`), git surface at `:862, 2148, 2194, 2886`
- `scripts/teach_persona.py:344-380` (`arm_outputs`), `:410-449` (`refuse_if_exists`), `:507-626` (`build_bins`, WR-01 `:572`, WR-04 `:573/579`, WR-08 `:583-593`), `:629` (`_prove_floor_and_band`), `:661-716` (aligned refusals), `:863-956` (`_mix_adversarial`, WR-06 `:894-895`, `n_want` `:905-916`), `:959-1028` (`_prepend_replay`), `:1090-1155` (`arm_spec`), `:1168-1316` (`build_arm_bins`), `:1544-1995` (`train_arm`), `:1805-1808` (`DPSGD(...)`), `:1860` (`dp_fn=`)
- `src/personacore/training/loop.py:149-232` (`_optimizer_step`), `:235-976` (`train`, the `dp_fn`/`fact_bin`/`n_facts` seam)
- `scripts/_addendum.py:1-100` (executed against copies of both planning docs), `scripts/_prose.py:1-46`, `scripts/_verdict.py:27-30`
- `scripts/phase23_prereg.py` (`H_PER_POINT_FLOOR_SECONDS = 17175`, `FLOOR_PROVENANCE_KEYS`, record constants), `scripts/phase23_matched_prereg.py` (`prove_first_attempt`, `MATCHED_ARTIFACT_GLOB`)
- `scripts/phase24_record.py:68, 75-118, 466-499`; `scripts/phase21_unit_record.py:183-186, 246-280`; `src/personacore/provenance.py:28-47`
- `scripts/phase18_extraction.py` (`GATED_TIER`, `REPORTED_TIER`, `CORPUS_TIERS`, `K = 48`, `ATTACK_FAMILIES`, `CORPUS_PATH`); `scripts/phase24_adversarial.py:248, 392-412`; `scripts/phase14_recall.py` (`contains_refusal`, `score_refusal`, `clean_frame_probe_populations`); `scripts/phase20_gate_coverage.py:370`
- `tests/test_phase23_budget.py:321-397, 433-441, 444-510, 513, 1305-1400`; `tests/test_phase24_grid.py:1-45`; `tests/test_phase24_correction.py:1-50, 89-200`; `tests/test_phase23_cost.py:783-825`; `tests/test_phase15_plots.py:60-62, 291-352`; `tests/test_phase23_mps_venue.py:56-84`; `tests/test_mps_smoke.py:30-31`; `tests/test_phase22_{fakes,checkpoint,dpsgd}.py` import sites; `tests/test_phase23_{cal03,resume}.py` import sites
- Records: `phase23_sigma_zero.json`, `phase23_matched_control.json`, `phase23_matched_verdict.json`, `phase23_control_floor.json`, `phase23_never_taught.json`, `phase23_cost.json`, `phase23_cal03_wiring.json`, `phase21_multiplicity.json`, `phase23_noised_dp_n64_sigma0p500000.json`, `data/phase23_never_taught_seed1337_draws.json`
- Planning: `.planning/ROADMAP.md:177, 809-843`; `.planning/REQUIREMENTS.md:304-397, 444-451, 468`; `.planning/STATE.md:515-545, 1613-1631`; `.planning/phases/24-…/24-REVIEW.md:248-488`
- Environment: `pmset -g`, `pmset -g assertions`, `pgrep -x caffeinate`, `df -h`, `.gitignore:1-25`, `pyproject.toml:20-26`, `Makefile:9-23`, `.planning/config.json`
- Suite: `pytest --collect-only -q` → 1648 collected; `pytest -q` → **1647 passed, 1 skipped, 83 warnings in 386.21s**

**Assumptions Log:** empty. Every claim above carries a `path:line`, a command with its real output,
or an explicit **CORRECTED** / **UNVERIFIABLE** label. There are zero `[ASSUMED]` claims and zero
UNVERIFIABLE rows. No external packages were consulted or recommended — this phase installs nothing,
so the Package Legitimacy Audit is not applicable.
