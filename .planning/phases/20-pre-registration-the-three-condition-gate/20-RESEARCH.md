# Phase 20: Pre-Registration — The Three-Condition Gate - Research

**Researched:** 2026-08-20
**Domain:** In-repo code archaeology — exact shapes, identifiers and git mechanics the 30 locked decisions must reference correctly
**Confidence:** HIGH (every claim below was read from the file or executed; nothing inferred from CONTEXT.md alone)

## Summary

Scope was deliberately narrow: no web research, no alternatives, no re-litigation. This document
establishes the **real** code shapes and identifiers behind CONTEXT.md's 30 locked decisions, so no
plan names a path, constant, signature or line range the code refuses.

**Every measured number in CONTEXT.md verifies exactly** — all fifteen arithmetic claims (D-01,
D-04, D-06, D-09, D-11, D-12, D-17, GATE-02's two caps) were recomputed from the committed JSON and
reproduce bit-for-bit, including the `0.005214448168350039` bit-identity in D-04 and the
`3.9085032379884783` cap in D-06. **Three citations in CONTEXT.md are wrong** and one measured
number is unpersisted; all four are itemised below. The most consequential: `scripts/erasure_gate.py`
is **291 lines**, so the cited `:454-458` "must-not-amend text" does not exist — the non-amendment is
enforced by a *test* (`tests/test_phase18_prereg.py:212`), not by a self-statement in the gate.

**Primary recommendation:** Build `scripts/mitigation_gate.py` on the `erasure_succeeded` skeleton
(`erasure_gate.py:200-255`) with its own `VERDICTS = ("PASS", "FAIL", "INCONCLUSIVE")` tuple —
GATE-01's domain differs from `erasure_gate.VERDICTS`, which is `("SUCCESS", "FAILURE",
"INCONCLUSIVE")`, so the domain tuple **must not** be imported. Copy the ancestry guard from
`tests/test_phase16_prereg.py:406-497` (the Phase 19 twin — Phase 18's shape, one iteration more
recent and with better-worded comments) rather than `:322-403`. Measure the D-06 retention floor with
a **new unpinned driver**, on the `phase19_run.py` precedent.

## Project Constraints (from CLAUDE.md)

| Directive | Bearing on this phase |
|---|---|
| **GSD Workflow Enforcement** — no direct repo edits outside a GSD workflow | Phase 20 runs under `/gsd-execute-phase`. |
| **Python 3.11 venv MANDATORY** — dev box is 3.14, unsupported | Every command is `.venv/bin/python`. Verified: `.venv` is Python **3.11.15**. |
| **Tests CPU-only, GPU-free** | The ancestry test and gate self-check are pure stdlib. **Exception:** the D-06 retention re-measurement is an MPS model-load — it is a *driver*, not a test. |
| **stdlib only, no torch/numpy in the pin** | `erasure_gate.py` imports only `math`. `mitigation_gate.py` must match. |
| **RPT-03 zero new runtime deps** | `pyproject.toml` sha256-pinned at `tests/test_package.py:11`. Do not touch it. |
| **No wandb/network** | N/A this phase. |
| Extras `[cpu,dev,demo]` identical in `Makefile:install`, `.github/workflows/ci.yml`, CLAUDE.md | Omitting `demo` makes `make test` a hard **collection error**, not a skip. |

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

All 30 decisions D-01…D-30 in `20-CONTEXT.md:32-303` are LOCKED and are **not** restated here —
read that file, it is binding. This research verifies their *citations*, not their *content*.

Summary of what is locked, by group:
- **Condition (c) form** — D-01…D-08: (c)-dialogue is a **band on the ON−OFF adaptation gap**, not a
  raw-PPL cap; `control_gap` is a required kwarg; the upper bound is **additive** (`control_gap +
  MARGIN_K × gap_noise_floor`), never a `hi_frac`; the retention leg stays a **one-sided upper cap**
  (asymmetry recorded with its reason); the retention floor is **re-measured** at
  `0.008681618994239138` and stays a required kwarg; `results/phase20_retention_floor.json` lands
  **strictly after** the pin.
- **X, the extraction ceiling** — D-09…D-14: `X = wilson_upper_bound(nt_successes, n) + MARGIN_K ×
  extraction_noise_floor`, unit = QUESTIONS; `wilson_upper_bound` imported **by object identity**;
  reachability is by construction (no clamp); the extraction floor is **not measurable in Phase 20**;
  the Phase 23 obligation travels as **code** (armed tripwire + tolerance reporter).
- **Y and the two chosen constants** — D-15…D-18: `f_Y = 0.7` applied to both legs against each leg's
  own retrained control; `f_C = 0.5` separate; **exactly two chosen constants**, both labelled in
  source as milestone PREFERENCE.
- **K, promotion, gate/budget split** — D-19, D-20: `K_RUNGS = (48, 24, 16, 8)` committed now;
  Phase 23 selects the rung; **RATCHET — K may only increase**; the promotion rule lives in the gate
  and takes K as a required kwarg (so the gate never imports the budget).
- **Module structure and ordering** — D-21…D-24: ancestry guard copies the **Phase 18 shape**;
  `V4_ARTIFACT_GLOBS` includes `phase20_*`, proven RED-then-GREEN in a **throwaway repo**;
  `scripts/_prose.py` sits **outside** the pin; corrections are **dated continuations**.
- **GATE-10** — D-25…D-27: equivalence is **structural** (same σ, steps, δ, q — zero tolerance
  constant); the fallback branch is committed now; both branches publishable.

### Claude's Discretion

- **D-28 — GATE-07 arm identity.** `arm` required kwarg from a closed `ARMS = ("dp", "adversarial")`;
  verdict carries it; ∃ computed per arm; `exists_clearing_point` **refuses a mixed-arm point list**.
  Module-scope `_prove` asserts the claim-string table equals `ARMS`.
- **D-29 — GATE-08 provisional.** Verdict domain stays **exactly three**. All-three-conditions-clear
  without second-seed replication returns **`INCONCLUSIVE`**. Replication argument required, no
  default. A `PASS` with `provisional=True` was **explicitly REJECTED**.
- **D-30 — GATE-09 destroyed-model fixture.** Built from Phase 19's real published M1 readings
  (dialogue `4.851119149910443`, retention `3.6709177253236867`, 77.637% destruction). **Labelled a
  fixture, never a second reading of the experiment.**

### Deferred Ideas (OUT OF SCOPE)

- **GATE-10 fallback tolerance** (D-26) — a third chosen constant, deliberately unset. Decide before
  Phase 21's CAL-03 runs.
- **Extraction noise floor measurement** (D-13) — two seeds on the never-taught arm. Phase 23
  (CTRL-03), gated behind Phase 21's corpus design. Carried by the D-14 tripwire, not prose.
- **Re-measuring `V20_RETENTION_NOISE_FLOOR`'s consumers** — `erasure_gate`'s own `retention_cap`
  keeps the Phase 12 floor. `23a830c` must not be amended.
- **Retention leg becoming a gap band** — deferred behind a measurement that does not exist.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (source line) | Research support |
|----|---------------------------|------------------|
| GATE-01 | `REQUIREMENTS.md:27` — module returns `PASS`/`FAIL`/`INCONCLUSIVE`, three conditions, keyword-only, no defaults, every condition rendered into a reason string | §2 anatomy; **§1 flags the verdict-domain mismatch with `erasure_gate.VERDICTS`** |
| GATE-02 | `REQUIREMENTS.md:31` — (c) computed from four imported `erasure_gate` constants + measured `dialogue_ppl_noise_floor`; caps `4.5837288963367` / `4.029000` | §1 exact names + import line; §6 both caps recomputed and confirmed |
| GATE-03 | `REQUIREMENTS.md:36` — Y is a pair | §2 signature shape |
| GATE-04 | `REQUIREMENTS.md:38` — Y as fraction of retrained control | D-16 `f_Y = 0.7`; §1 confirms 0.4921/0.3483 exist only as `V20_TAUGHT_RECALL`/`V20_HELDOUT_RECALL` (must NOT be imported for Y) |
| GATE-05 | `REQUIREMENTS.md:40` — zero-extraction-without-NLL INCONCLUSIVE, precedence over FAIL | §2 the exact `zero_results_have_nll` mechanics at `erasure_gate.py:223-227` |
| GATE-06 | `REQUIREMENTS.md:43` — truncated-sweep discriminator | §2 the `not nontarget_deltas → INCONCLUSIVE` late-return precedent at `:253-254` |
| GATE-07 | `REQUIREMENTS.md:46` — arm identity | §2 module-scope `_prove` precedent (`phase19_erasure.py:3878-3883`) |
| GATE-08 | `REQUIREMENTS.md:48` — provisional until second-seed replication | §2; D-29 precedent is `zero_results_have_nll`'s shape |
| GATE-09 | `REQUIREMENTS.md:50` — `__main__` exercises every branch incl. failing ones; destroyed-model fixture observed returning `FAIL` | §2 `__main__` convention (`erasure_gate.py:258-291`), verified runnable |
| GATE-10 | `REQUIREMENTS.md:53` — capacity comparison rule in the same module, both branches | D-25…D-27; no in-repo precedent — new construction |
| CAL-04 | `REQUIREMENTS.md:131` — per-point K + promotion rule before any v4.0 artifact | §7 the ATK-03/P18-4 record verified at `phase18_extraction.py:84-92` (**not `:88-92`**) |
| RPT-02 | `REQUIREMENTS.md:218` — whitespace-normalizing prose-search helper | §5 the v3.0 incident located and the prescribed implementation found verbatim |
</phase_requirements>

---

## 1. Identifier & Path Table

> **This is the highest-value section.** `RETROSPECTIVE.md:182-185` records: *"Plans kept naming APIs
> and paths the code refuses."* Every row below was read from the source.

### 1a. Imports from `scripts/erasure_gate.py` (EXISTS, 291 lines, one commit `23a830c`)

| Real name | Defining line | Value / signature | Status |
|---|---|---|---|
| `V20_MASKED_DIALOGUE_VAL_PPL` | `:75` | `4.5733` | EXISTS |
| `V20_EWC_RETENTION_PPL` | `:76` | `3.891140` | EXISTS |
| `V20_RETENTION_NOISE_FLOOR` | `:77` | `0.068930` | EXISTS — **D-06 supersedes for v4.0; do NOT import for the v4.0 retention cap** |
| `MARGIN_K` | `:86` | `2` | EXISTS |
| `CONFIDENCE` | `:89` | `0.95` | EXISTS |
| `_Z_ONE_SIDED_95` | `:90` | `1.6448536269514722` | EXISTS (private; `wilson_upper_bound`'s `z=` default) |
| `wilson_upper_bound` | `:139` | `(successes, n, z=_Z_ONE_SIDED_95) -> float` | EXISTS — returns a **bare float**, `min(1.0, …)` |
| `rule_of_three` | `:161` | `(n) -> float` (`3.0/n`) | EXISTS — returns a **bare float** |
| `VERDICTS` | `:136` | `("SUCCESS", "FAILURE", "INCONCLUSIVE")` | EXISTS — **⚠ WRONG DOMAIN for GATE-01, must not be imported** |
| `ERASURE_DECISION_RULE` | `:95-127` | 6-element `tuple[str, ...]` | EXISTS (CONTEXT `:95-127` ✅) |
| `ERASURE_GOAL_FRAMING` | `:130-134` | single `str` | EXISTS (CONTEXT `:130-134` ✅) |
| `erasure_succeeded` | `:200-255` | keyword-only, `-> (verdict, reasons)` | EXISTS — **the template** |
| `erasure_is_worth_attempting` | `:173` | positional, `-> (bool, reason)` | EXISTS |
| `V20_TAUGHT_RECALL` / `V20_HELDOUT_RECALL` | `:78` / `:79` | `0.4921` / `0.3483` | EXISTS — **GATE-04 forbids deriving Y from these** |

**Exact import statement** (matches `test_phase16_stats.py:396`'s AST expectation of
`node.module == "erasure_gate"` — a flat module name, not `scripts.erasure_gate`):

```python
from erasure_gate import (
    MARGIN_K,
    V20_EWC_RETENTION_PPL,
    V20_MASKED_DIALOGUE_VAL_PPL,
    V20_RETENTION_NOISE_FLOOR,
    rule_of_three,
    wilson_upper_bound,
)
```

This requires the `sys.path` bootstrap every `scripts/` module uses (see `_addendum.py:43-47`):

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
```

### 1b. Test-side identifiers (`tests/test_phase16_prereg.py`, EXISTS, 622 lines)

| Real name | Line | Value | Note |
|---|---|---|---|
| `PREREG_COMMIT` | `:49` | `"23a830c0181acf799dadc1e9aecdf1818d8678e2"` | full 40 chars, never abbreviated |
| `V3_ARTIFACT_GLOBS` | `:56-61` | 4-tuple `results/phase1{6,7,8,9}_*` | **CONTEXT says `:45-60`; the tuple closes at `:61`** |
| `PREREG_ARTIFACT` | `:63` | `"scripts/erasure_gate.py"` | |
| `PHASE17_PREREG_ARTIFACT` | `:68` | `"scripts/phase17_personas.py"` | |
| `PHASE18_PREREG_ARTIFACT` | `:80` | `"scripts/phase18_extraction.py"` | |
| `PHASE19_PREREG_ARTIFACT` | `:87` | `"scripts/phase19_erasure.py"` | |
| `PHASE19_FLOOR_ARTIFACT` | `:94` | `"scripts/phase19_floor.py"` | the sanctioned post-artifact write |
| `_ROOT` | `:166` | `pathlib.Path(__file__).resolve().parent.parent` | |
| `_git(*args)` | `:169-173` | `subprocess.run(("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True).stdout.strip()` | copy verbatim |

### 1c. Helper modules (phase-neutral, outside every pin)

| Path | Line | Signature | Status |
|---|---|---|---|
| `scripts/_addendum.py::append_addendum` | `:56` | `(path, addendum, *, pending, recorded)` | EXISTS — **both keywords REQUIRED** |
| `scripts/_addendum.py::_prove` | `:50` | `(condition, message)` → `SystemExit` | EXISTS |
| `scripts/_verdict.py::VERDICT_SECTION` | `:24` | `re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M \| re.S)` | EXISTS |
| `scripts/_verdict.py::recorded_verdict` | `:27` | `(text) -> str \| None` | EXISTS |

### 1d. Files this phase CREATES (all verified ABSENT)

| Path | Status | Verified by |
|---|---|---|
| `scripts/mitigation_gate.py` | **NEW** | `ls` + `git ls-files` — absent, untracked |
| `scripts/_prose.py` | **NEW** | absent, untracked |
| `tests/test_phase20_prereg.py` | **NEW** | absent, untracked |
| `results/phase20_retention_floor.json` | **NEW** | absent; `git log --diff-filter=A -- 'results/phase20_*'` is **EMPTY** — D-22's clean-history requirement currently holds |
| `scripts/mitigation_budget.py` | **Phase 23, NOT this phase** | absent |

### 1e. New identifiers the plans must declare (none exist yet — names are the planner's to fix)

| Proposed name | Source decision | Suggested shape |
|---|---|---|
| `V4_ARTIFACT_GLOBS` | D-22 | tuple, must contain `"results/phase20_*"` |
| `PHASE20_PREREG_ARTIFACT` | D-21 | `"scripts/mitigation_gate.py"` |
| `VERDICTS` (in `mitigation_gate`) | GATE-01 | `("PASS", "FAIL", "INCONCLUSIVE")` — **own tuple, not imported** |
| `ARMS` | D-28 | `("dp", "adversarial")` |
| `K_RUNGS` | D-19 | `(48, 24, 16, 8)` |
| `F_Y`, `F_C` | D-16, D-17 | `0.7`, `0.5` — labelled PREFERENCE in source |
| `normalized` (in `_prose`) | RPT-02 | `(text) -> " ".join(text.split())` |

### 1f. ⚠ CONTEXT.md citation defects — corrected

| CONTEXT.md claim | Reality | Correction |
|---|---|---|
| `erasure_gate.py:454-458` — "the must-not-amend text", "`:454-458` says so in its own text" (`20-CONTEXT.md:316`) | **The file is 291 lines.** There is no `:454`. `git show --stat 23a830c` → `291 ++++`, one commit, never amended. | The nearest self-statement is **`erasure_gate.py:71-73`**: *"Nothing here is new, and nothing here may be silently updated: if a baseline is ever re-measured, the new number goes in a DATED note, never over the top of these"* — scoped to the **baselines block**, not the whole file. The whole-file non-amendment is enforced **by a test**, `tests/test_phase18_prereg.py:212 test_erasure_gate_untouched`, which asserts (a) `git log -- scripts/erasure_gate.py == [PREREG_COMMIT]` exactly, and (b) the bytes on disk equal `git show 23a830c:scripts/erasure_gate.py`. **The decision stands; only the citation was wrong.** |
| "Phase 17 `_GATE_MODULES`" located in `scripts/phase17_isolation.py` / `phase17_persona_gate.py` (`20-CONTEXT.md:380`, `:393`) | `_GATE_MODULES` appears in **no `scripts/` file**. It is declared in **tests**. | `tests/test_phase17_stats.py:62` and `tests/test_phase18_prereg.py:59`: `_GATE_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("phase18_*.py")))`. The AST scan lives in the **test**, scanning a `scripts/` glob. See §7 landmine L4 — this matters because `mitigation_gate.py` matches **no `phase20_*.py` glob**. |
| `tests/test_phase16_prereg.py:45-60` for `PREREG_COMMIT` + `V3_ARTIFACT_GLOBS` | Constants at `:49` and `:56-**61**` | Use `:46-63`. |
| `phase18_extraction.py:88-92` (also `REQUIREMENTS.md:132`) | The ATK-03/P18-4 record runs `:84-92`; `K = 48` is at `:93` | Use **`:84-93`**. The exact sentence CONTEXT quotes ("this is the one moment / the pin leaves open for it") is at `:90-91`. |
| `tests/test_phase16_prereg.py:322-399` = "the Phase 18 shape" | Function is `:322-**403**`. D-21's cited `:387` (product assert) ✅; `:399` for `bool(checked)==bool(tracked_artifacts)` is off by one — the assert is at **`:398`**, its message `:399-402`. `:396-398` for "the reason in its own words" ✅ (comment `:394-397`). | Use `:322-403`. |

### 1g. ⚠ Unpersisted measured number (blocks D-08 without a driver)

**`4.2284415113307245`** — the seed-2024 `adapter_on` retention reading that D-06's floor depends on
— exists in **exactly one file on disk: `20-CONTEXT.md`.** Verified by `grep -rl` across the repo.

`results/phase19_noise_floors.json` carries only the **seed-1337** retention pair
(`retention_ppl_pre_erasure.adapter_off = 3.891139975617828`, `.adapter_on = 4.219759892336485`,
`.delta_on_minus_off = 0.3286199167186572`, `n_scored_tokens = 1000285`). There is **no seed-2024
retention block anywhere in `results/`.**

**Consequence for the planner:** `results/phase20_retention_floor.json` cannot be produced by
transcription from a committed artifact. It requires **re-running** the two-seed ON/OFF retention
measurement. See §7 landmine L1.

---

## 2. `erasure_gate.py` Template Anatomy

### 2a. The signature shape (`:200-211`) — copy this exactly

```python
def erasure_succeeded(
    *,
    target_successes,
    target_questions,
    target_floor,
    nontarget_deltas,
    nontarget_noise_floor,
    dialogue_ppl,
    dialogue_ppl_noise_floor,
    retention_ppl,
    zero_results_have_nll,
):
```

**Mechanics, all verified by reading:**

| Property | How it is achieved | Line |
|---|---|---|
| **Keyword-only enforcement** | A bare `*,` as the first parameter. **No type hints anywhere in the file.** No `dataclass`, no `TypedDict`. | `:201` |
| **No defaults** | Zero `=` in the parameter list. GATE-01 requires this. | `:202-210` |
| **Return type** | A plain 2-tuple `(verdict: str, reasons: list[str])`. Not a dataclass, not a namedtuple. | `:212` |
| **Reason assembly** | `reasons = []` then `reasons.append(f"...")` per condition. f-strings with **explicit format specs** (`:.4f` for PPL/bounds, `:.6f` for floors/margins). | `:219`, `:231`, `:239`, `:248` |
| **Comparator rendered into the string** | `{'<=' if a_ok else '>'}` — the reason states which way the comparison went, so a reader never re-derives it. | `:233`, `:241` |
| **Bare-value returns** | `wilson_upper_bound` returns a float, not a `(value, n)` pair. | `:158` |

### 2b. INCONCLUSIVE precedence — three distinct mechanisms

The docstring states the rule at `:215-217`: *"All three conditions must hold for SUCCESS;
INCONCLUSIVE takes precedence over FAILURE, because 'we could not tell' and 'it did not work' are
different findings and collapsing them is the mistake this project's honest-negatives discipline
exists to prevent."*

It is implemented three ways, and **the third is the one Phase 20 most needs**:

**(i) Early return, missing denominator** — `:221-222`:
```python
if target_questions <= 0:
    return "INCONCLUSIVE", ["no target questions scored"]
```

**(ii) Early return, the GATE-05 shape** — `:223-227`:
```python
if target_successes == 0 and not zero_results_have_nll:
    return "INCONCLUSIVE", [
        "target recall is zero but no teacher-forced NLL was recorded — cannot distinguish "
        "'the fact is absent' from 'the probe was too weak', so no erasure claim is admissible"
    ]
```
Returns **before** any reason is appended — the caller gets a single-element list. GATE-05 ports
this verbatim; D-29 reuses the same shape for the missing-replication branch.

**(iii) LATE return, after all reasons are built** — `:253-255`:
```python
if not nontarget_deltas:
    return "INCONCLUSIVE", reasons
return ("SUCCESS" if (a_ok and b_ok and c_ok) else "FAILURE"), reasons
```
This is the **precedence** mechanism proper: every condition is evaluated and rendered, then the
INCONCLUSIVE check intercepts *before* the SUCCESS/FAILURE ternary. **GATE-06's truncated-sweep
discriminator must use this form** — the reader needs the per-condition reasons even when the verdict
is INCONCLUSIVE.

`tests/test_phase19_erasure.py:1535` records why the refusal must be upstream: *"into INCONCLUSIVE
(`erasure_gate.py:253-254`), so the refusal has to happen here."*

### 2c. Cap computation — GATE-02's "imported, never retyped"

`:245-247`:
```python
dialogue_cap = V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * dialogue_ppl_noise_floor
retention_cap = V20_EWC_RETENTION_PPL + MARGIN_K * V20_RETENTION_NOISE_FLOOR
c_ok = dialogue_ppl <= dialogue_cap and retention_ppl <= retention_cap
```

**Both caps are computed in LOCALS and never returned.** `tests/test_phase19_erasure.py:1214`
records this explicitly: *"The gate computes the cap in a local (`erasure_gate.py:245`) and never
returns it, so its [value] …"* — the cap reaches the caller **only through the reason string**.
D-14's tolerance reporter exists precisely because this makes criterion strength invisible otherwise.

**Recomputed and confirmed** (`.venv/bin/python`):
```
4.5733   + 2 × 0.005214448168350039 = 4.5837288963367   ✅ matches GATE-02 / ROADMAP SC1
3.891140 + 2 × 0.068930             = 4.029             ✅ matches GATE-02 / ROADMAP SC1
```

### 2d. The `_prove` module-scope pattern (D-28's precedent)

**`erasure_gate.py` has no `_prove`.** The pattern lives in the phase drivers. Canonical definition
(`phase19_erasure.py:164-173`) — raises `SystemExit`, deliberately **not** `assert` (an `assert` is
strippable under `-O`):

```python
def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase19_erasure] {message}")
```

D-28's precedent — the B7 dispatch-table proof at **module scope**, `phase19_erasure.py:3878-3883`
(**CONTEXT's "Phase 19 B7, where `SUBCOMMANDS` and the dispatch table are proved equal at module
scope"** ✅ verified):

```python
_prove(
    tuple(_SUBCOMMAND_TABLE) == SUBCOMMANDS,
    f"the dispatch table holds {tuple(_SUBCOMMAND_TABLE)} against the committed {SUBCOMMANDS}. "
    "The published set and the runnable set must be ONE set: a name with no handler is a "
    "subcommand a later plan would have to add code for, which is a commit to this file",
)
```

Note the closing clause — *"which is a commit to this file"* — that is the ancestry guard being
invoked as the deterrent. D-28's claim-string/`ARMS` proof should carry the same sentence.

`_addendum.py:50-53` shows the phase-neutral variant with a `[_addendum]` prefix; `mitigation_gate.py`
should use `[mitigation_gate]`.

### 2e. `__main__` convention (GATE-09 / SC3)

`erasure_gate.py:258-291`. Verified runnable — `.venv/bin/python scripts/erasure_gate.py` prints
`erasure_gate self-check OK — 6 rule clauses committed`.

Shape:
```python
if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    assert wilson_upper_bound(0, 100) < 0.04, "zero-success upper bound should be small but > 0"
    ...
    v, rs = erasure_succeeded(target_successes=0, ..., zero_results_have_nll=True)
    assert v == "SUCCESS", (v, rs)
    v2, _ = erasure_succeeded(..., zero_results_have_nll=False)
    assert v2 == "INCONCLUSIVE", v2
    print(f"erasure_gate self-check OK — {len(ERASURE_DECISION_RULE)} rule clauses committed")
```

**Five conventions to copy:**
1. `# pragma: no cover - self-check, not a test suite` on the guard line.
2. Bare `assert`, no pytest, no fixtures.
3. **Both** the passing and the failing twin are asserted — `zero_results_have_nll=True` → SUCCESS
   *and* `=False` → INCONCLUSIVE, from otherwise-identical kwargs.
4. Failure payload carries the observed value: `assert v == "SUCCESS", (v, rs)`.
5. Terminal `print` that **derives** its count (`len(ERASURE_DECISION_RULE)`) rather than retyping it.

**SC3 requires five distinct branch behaviors observed firing through `__main__`** (ROADMAP `:168-176`):
FAIL on the destroyed-model fixture; INCONCLUSIVE on zero-extraction-without-NLL (with precedence
over FAIL); INCONCLUSIVE on the truncated sweep; arm identity carried on the verdict; INCONCLUSIVE on
missing second-seed replication. `erasure_gate`'s `__main__` covers two branches; Phase 20's must
cover all five plus PASS.

### 2f. Object-identity import (D-09's "never redefined")

Two committed enforcement shapes:

**Runtime identity** — `tests/test_phase19_erasure.py:745-748`:
```python
"""STAT-05 / T-19-08: imported from ``erasure_gate`` by IDENTITY, not by matching values."""
import erasure_gate
assert erasure.wilson_upper_bound is erasure_gate.wilson_upper_bound
```
and `:1307-1308`: `assert erasure.V20_MASKED_DIALOGUE_VAL_PPL is erasure_gate.V20_MASKED_DIALOGUE_VAL_PPL`
(`is`, not `==` — a value-matching copy is a copy free to stop matching, per `:2149`).

**Static AST** — `tests/test_phase16_stats.py:386-411`, the direct template for the D-20 AST guard:
```python
def test_stats_use_only_stdlib_and_erasure_gate():
    tree = _tree(_DRIVER_PATH)
    imported = set()
    from_erasure_gate = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
            if node.module == "erasure_gate":
                from_erasure_gate.update(alias.name for alias in node.names)
    assert "scipy" not in imported
    assert "numpy" not in imported
    assert {"wilson_upper_bound", "rule_of_three"} <= from_erasure_gate
    defined = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert not ({"wilson_upper_bound", "rule_of_three"} & defined), (
        "a bound was re-implemented in this module instead of imported from erasure_gate — D-16's "
        "rule is import the instrument, never copy it, or the two silently diverge"
    )
```

**D-20's AST guard is this test with `"mitigation_budget" not in imported` added.** It covers both
`import mitigation_budget` and `from mitigation_budget import ...` because both branches feed
`imported`.

---

## 3. Ancestry Guard: Phase 18 Shape vs Phase 16 Shape

### 3a. The Phase 16 shape — `:176-213` — **DO NOT COPY** (D-21)

```python
    checked = 0
    untracked = []
    for pattern in V3_ARTIFACT_GLOBS:
        for path in sorted(_ROOT.glob(pattern)):          # <-- WORKING-TREE glob
            rel = path.relative_to(_ROOT).as_posix()
            adds = _git("log", "--diff-filter=A", "--format=%H", "--", rel).split()
            if not adds:
                untracked.append(rel)
                continue
            first_add = adds[-1]
            subprocess.run(("git", "merge-base", "--is-ancestor", PREREG_COMMIT, first_add),
                           cwd=_ROOT, check=True)
            checked += 1

    assert checked, (                                      # <-- :209, UNCONDITIONAL
        "no committed v3.0 results artifact was checked — the guard matched nothing. "
        f"Globs {V3_ARTIFACT_GLOBS} found only uncommitted paths {untracked}. "
        "A pre-registration guard that checks zero artifacts is green and blind."
    )
```

**Why it is fatal for Phase 20:** `assert checked` at `:209` is **unconditional**. It is RED whenever
nothing committed matched. Phase 20 arms its guard *before any v4.0 artifact exists* — so under this
shape the test is red from the gate's first commit until an artifact lands, **inverting the ordering
this phase exists to establish.** Also note it pins a **hand-written SHA** (`PREREG_COMMIT`), which
`:243-247` explains "happily permits a LATER edit to the pre-registration after the numbers are
visible, which is precisely the manoeuvre STAT-05 exists to forbid."

### 3b. The Phase 18 shape — `:322-403` — **THIS IS THE ONE**

```python
    artifact_glob = "results/phase18_*"
    assert artifact_glob in V3_ARTIFACT_GLOBS, (...)        # :351 — the two-sets-drift guard

    assert _git("rev-parse", "--is-shallow-repository") == "false", (...)  # :358 — shallow clone

    prereg_commits = _git("log", "--format=%H", "--", PHASE18_PREREG_ARTIFACT).split()
    assert prereg_commits, (...)                            # :365 — the pin must exist

    tracked_artifacts = _git("ls-files", artifact_glob).split()   # :371 — GIT INDEX, not the disk

    checked = 0
    for artifact in tracked_artifacts:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:                       # EVERY commit, not one pinned SHA
            subprocess.run(("git", "merge-base", "--is-ancestor", prereg, first_add),
                           cwd=_ROOT, check=True)
            checked += 1

    assert checked == len(prereg_commits) * len(tracked_artifacts), (...)   # :387 PRODUCT
    assert bool(checked) == bool(tracked_artifacts), (...)                  # :398 EQUIVALENCE
```

**The reason, in the code's own words** (`:394-397`, CONTEXT cites `:396-398` — close enough):
> *The product above is satisfied by `0 == n * 0`. Today both sides ARE zero and that is correct:
> D-04 forbids a `results/phase18_*` artifact existing before the pin is complete. This ties the two
> together so the equivalence, not the count, is what is asserted — **green while no artifact is
> tracked, and demanding a non-zero `checked` from the first one onward.***

### 3c. The difference, stated mechanically

| | Phase 16 (`:176-213`) | Phase 18 (`:322-403`) |
|---|---|---|
| Artifact discovery | `_ROOT.glob(pattern)` — **working tree** | `_git("ls-files", glob)` — **git index** |
| Pre-registration side | one **hand-pinned SHA**, `PREREG_COMMIT` | **every commit** touching the pin file (`git log --format=%H --`) |
| Catches a post-hoc edit? | **No** — only the first commit is checked | **Yes** — a later edit is a new `prereg` commit that fails ancestry |
| Needs a separate identity test? | **Yes** (`:216 test_prereg_commit_exists_and_touches_the_erasure_gate`) | **No** — self-identifying, there is no pin to get wrong |
| Empty match set | `assert checked` → **RED** | `bool(checked) == bool(tracked_artifacts)` → **GREEN** while tracked=0 |
| Uncommitted working-tree file | collected into `untracked[]`, skipped | invisible (not in the index) |
| Glob-membership guard | ✗ | ✓ `:351` — asserts the glob is in `V3_ARTIFACT_GLOBS` |
| Pin-exists guard | ✗ | ✓ `:365` — `assert prereg_commits` |

### 3d. ⭐ Recommendation: copy `:406-497` (the Phase 19 twin), not `:322-403`

`test_phase19_prereg_is_frozen_before_every_phase19_result` (`:406-497`) is **structurally identical**
to the Phase 18 guard — I diffed the bodies line by line — but it is one iteration more recent and its
docstring states the phase-zero situation Phase 20 is actually in (`:425-431`):

> *"**Vacuous TODAY BY CONSTRUCTION, and that is a recorded state rather than a hidden one.** The pin
> is armed in plan 19-01 — the first plan of the phase — deliberately BEFORE any `results/phase19_*`
> artifact exists… Arming the guard first is the point — every pin commit from 19-01 onward is
> watched from the start instead of being retro-fitted once there is something to miss."*

That is Phase 20's situation verbatim. Copy `:406-497`, substituting:

| `:406-497` | Phase 20 analogue |
|---|---|
| `artifact_glob = "results/phase19_*"` | `artifact_glob = "results/phase20_*"` |
| `V3_ARTIFACT_GLOBS` | `V4_ARTIFACT_GLOBS` (new, in `tests/test_phase20_prereg.py`) |
| `PHASE19_PREREG_ARTIFACT` | `PHASE20_PREREG_ARTIFACT = "scripts/mitigation_gate.py"` |
| `"Plan 19-01 Task 1 commits it."` | `"Plan 20-0N Task N commits it."` |
| test name | `test_phase20_prereg_is_frozen_before_every_phase20_result` |

Also copy `_ROOT` (`:166`) and `_git` (`:169-173`) verbatim — `tests/test_phase20_prereg.py` must be
self-contained (`test_phase18_prereg.py:227` shows cross-test imports are permitted, but only for the
`erasure_gate` pin constants).

### 3e. `V3_ARTIFACT_GLOBS` declaration shape (`:51-61`) — what the Phase 20 analogue must carry

The comment is load-bearing and D-22 requires the equivalent:

```python
# Every v3.0 results artifact. Phases 16, 17, 18 and 19 are the milestone whose numbers the
# pre-registered rule judges; a new phase writing results under a further prefix must be added here,
# and the `assert checked` below is what makes a silently-stale list visible. `results/phase19_*` is
# the fourth prefix and it was added BEFORE any such artifact existed — the guard watches the path
# set from the start rather than being retro-fitted once there is something to miss.
V3_ARTIFACT_GLOBS = (
    "results/phase16_*",
    "results/phase17_*",
    "results/phase18_*",
    "results/phase19_*",
)
```

**D-22's recorded lesson is right and is stated in the source:** *"an `assert` catches an empty match
set, never an incomplete one."* The v4.0 tuple should therefore pre-declare **every v4.0 prefix**
(`phase20_*` through `phase28_*`) at arming time, not just `phase20_*`, on the same reasoning the
comment gives for `phase19_*`. **Flag for the planner:** CONTEXT D-22 mandates only `phase20_*` — the
wider set is a discretionary strengthening, not a locked decision.

**Verified pathspec semantics:** `git ls-files "results/phase19_*"` returns **27** tracked files, and
`*` **does cross `/`** — entries like `results/phase19_erase_dialogue_floor_seed1337/run.csv` are
included. Directory-shaped artifacts are covered without a second glob.

### 3f. D-22's throwaway-repo RED-then-GREEN fixture — mechanics verified

**I re-ran the state machine in `mktemp -d` throwaway repos. Real project history untouched:
`git log --diff-filter=A -- 'results/phase20_*'` is still EMPTY.**

| Measured behaviour | Result |
|---|---|
| `git merge-base --is-ancestor X X` | **exit 0 — REFLEXIVE.** Confirms D-08: gate + artifact in the *same* commit **PASSES**. D-08's strict-after rule is a discipline, not a mechanical requirement. |
| add → `git rm` → commit | `git ls-files 'results/phase20_*'` → **empty**, tracked=0 → guard **GREEN**. The red **is reversible while the path stays deleted**. |
| re-add at the identical path | `git log --diff-filter=A` returns **two** adds, newest-first. `adds[-1]` is **byte-identical to the original first add**. **Laundering is impossible.** |
| pin commit *after* the artifact's first add | `git merge-base --is-ancestor` exits **1** → `subprocess.run(check=True)` raises → **RED**, permanently (D-24). |

**Fixture recipe (safe, no `rm -rf`, no touch of real history):**
```python
import subprocess, tempfile, pathlib
env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
with tempfile.TemporaryDirectory() as tmp:   # pytest's tmp_path fixture is equivalent
    ...  # git init -q; build the four states; assert RED then GREEN
```
Use pytest's `tmp_path` fixture — no manual cleanup, no destructive command.

**⚠ Gotcha found while running it:** `git rm` of the last file in `results/` **removes the directory
from the working tree**, so a naive re-add fails with `no such file or directory`. The fixture must
`mkdir -p` before re-adding, or seed a `results/.keep`.

**⚠ Failure ergonomics:** the ordering assertion is `subprocess.run(..., check=True)`, so a violation
surfaces as a bare `CalledProcessError` with **no explanatory message** — unlike every `assert` in
these guards. All four existing twins share this; Phase 20 inherits it. Consider a `try/except
subprocess.CalledProcessError` that re-raises with the two SHAs and the artifact path named. **This is
a discretionary improvement, not a locked decision.**

---

## 4. `_addendum.py` Refusal Semantics — D-24 VERIFIED

**D-24's claim** (`20-CONTEXT.md:373-375`): *"Note it **refuses once the marker is already RECORDED**,
so a second append must be written directly with the same three properties checked on the produced
bytes."*

**VERDICT: CONFIRMED**, with one precision correction.

### The refusal mechanism (`_addendum.py:70-77`)

```python
found = text.count(pending)
_prove(
    found == 1,
    f"{path} carries {found} occurrence(s) of the placeholder line {pending!r}, and this "
    f"writer replaces EXACTLY ONE. At {found} there is no unambiguous line to replace — zero "
    "means the file is not the shape this writer was committed against, and more than one "
    "means choosing between them, which is how an append silently becomes a rewrite",
)
```

The first append consumes `pending` (`:79-80`: `before, after = text.split(pending)`; `updated =
before + recorded + after`). On a second call with the same pair, `text.count(pending) == 0` →
`found == 0` → `_prove` raises **`SystemExit`**. The refusal is real.

**RETROSPECTIVE.md:189-191 records the sanctioned workaround** — *the identity marker pair*:
> *"When an append-only writer requires its placeholder to occur exactly once and the placeholder has
> already been consumed, `pending=recorded=<the consumed line>` is a provable no-op replacement that
> still appends. **Used three times, zero deletions each.**"*

This is cheaper and safer than "written directly." **Recommend the planner prefer the identity-marker
pair over a hand-written second append.**

### The three properties, by their real names

| # | Property | Line | Operates on |
|---|---|---|---|
| **1** | **Exactly-one placeholder** — `text.count(pending) == 1` | `:70-77` | the **input** `text` |
| **2** | **Verdict-section invariance** — `_verdict.recorded_verdict(updated) == _verdict.recorded_verdict(text)`; *"a writer that moves it has rewritten the report under cover of an append"* | `:85-90` | the **produced bytes** `updated` |
| **3** | **Append-only prefix + addendum presence** — `updated.startswith(before) and addendum.rstrip("\n") in updated`; *"the append-only property is the whole guarantee this helper offers and it is checked on the produced bytes, not assumed from the construction"* | `:91-96` | the **produced bytes** `updated` |

**Precision correction to both D-24 and the module's own docstring.** `_addendum.py:37` claims *"All
three checks run on the PRODUCED BYTES rather than on the construction above them."* **Property 1 runs
on the input `text`, not on `updated`.** Properties 2 and 3 do run on `updated`. A plan that says
"check all three on the produced bytes" would be prescribing something the reference implementation
does not do. State property 1 as *"exactly one placeholder existed in the input"* — that is the real
guarantee, and it is sufficient.

### Signature — the exact shape a prior plan got wrong

`RETROSPECTIVE.md:182-185`:
> *"`18-VERIFICATION.md` prescribed `append_addendum(..., placeholder=...)`; the live signature is
> `append_addendum(path, addendum, *, pending, recorded)` with both halves required. Every
> remediation had to resolve the real signature from the module before planning, not after."*

**Live signature, `_addendum.py:56`:**
```python
def append_addendum(path, addendum, *, pending, recorded):
```
Two positional, two required keyword-only. Returns `updated` (the full new text). Writes the file and
prints `[_addendum] appended a dated section to {path}`.

### D-24's machine-readable correction precedent — VERIFIED

`results/phase19_calibration_correction.json` exists, with keys:
`['calibration_per_tier', 'calibration_questions', 'calibration_rate', 'calibration_successes',
'continuation', 'corrected_floor_branch', 'corrected_target_floor', 'defects', 'evidence',
'governs', 'pin_internal_calibration_rate', 'pin_internal_floor_branch',
'pin_internal_is_superseded', 'pin_internal_target_floor', 'proof']`.

`governs = "corrected_target_floor"` — a **field-name pointer**, naming which key in the same document
is the operative value. That is the exact shape D-24 prescribes. `tests/test_phase19_correction.py`
(18,867 bytes) is the tripwire precedent.

### D-23's "outside the pin" mechanism — VERIFIED, with the caveat CONTEXT already states

`fnmatch` check executed: `_addendum.py`, `_verdict.py`, `_prose.py` are matched by **none** of
`phase16_*.py` / `phase17_*.py` / `phase18_*.py` / `phase19_*.py` / `phase20_*.py`. The **leading
underscore is the mechanism** ✅.

**But** — and CONTEXT is right to flag this — the precedent is **structural, not historical**:
- `scripts/_addendum.py` last commit: `f8441ec`, **2026-08-17**
- first `results/phase19_*` add: `7293ec9`, **2026-08-18**

Neither helper has actually been edited post-artifact. Verified by `git log -1 --date=short`.

**⚠ New landmine for `mitigation_gate.py`:** the underscore mechanism protects `_prose.py` from a
`phase20_*.py` glob — but the Phase 20 pin file is named `mitigation_gate.py`, which **also** matches
no `phase20_*.py` glob. The gate's own protection must come from an **explicit constant**
(`PHASE20_PREREG_ARTIFACT`), not from a glob. See §7 landmine L4.

---

## 5. RPT-02 / `scripts/_prose.py::normalized`

### The v3.0 incident — LOCATED, three independent records

**`.planning/RETROSPECTIVE.md:179-181`** (the primary record):
> *"**A single-line `grep -c` reported a real defect as absent.** "three reductions" is line-wrapped in
> the source, so `grep -c "three reductions"` returns **0** on a file that contains it. The
> pre-correction sweep had to be whitespace-normalised to see it."*

**`.planning/milestones/v3.0-MILESTONE-AUDIT.md:104-111`** (defect W2's resolution, `resolved_by: 5703bbe`):
> *"CLOSED. Corrected in a dated continuation at docs/REPORT.md:1316-1326… Verified before commit with
> a WHITESPACE-NORMALISED sweep, because the error is line-wrapped as `"the three\nreductions"` and a
> single-line `grep -c` returns 0 on it. Across all published surfaces the erroneous form occurred
> exactly ONCE (docs/REPORT.md) and nowhere else."*

**The concrete failing string is therefore `"the three\nreductions"`** — that is the fixture literal
the RPT-02 test should use.

### The prescribed implementation — found verbatim in the research

**`.planning/research/PITFALLS.md:1048`** already specifies it exactly, including the target phase:
> *"**There is no whitespace-normalizing prose-search helper anywhere in this repo — I checked.** Build
> one: `scripts/_prose.py::normalized(text) -> " ".join(text.split())`, one definition, and route
> every doc-consistency test through it. The one-definition-per-statistic discipline that already
> covers `holm` and `wilson_upper_bound`, extended to the thing that checks the prose. This is a
> **~5-line module** that closes a defect class the project has already shipped. | **P25 (build it in
> P20 so it is available all milestone)**"*

**Confirmed absent:** `scripts/_prose.py` does not exist; `git ls-files | grep _prose` is empty.

### What `normalized` must do

`" ".join(text.split())` — `str.split()` with no argument splits on **any** run of whitespace
(spaces, tabs, `\n`, `\r\n`, form feeds) and discards empty strings, so it collapses newlines,
runs of spaces, and leading/trailing whitespace in one operation. This is a **stdlib one-liner**
(ponytail rung 3 — stdlib does it). No `re`, no dependency. RPT-03 preserved.

**Ponytail note:** resist adding a `search(text, phrase)` wrapper, a case-fold flag, or a `count()`
helper. The one exported name is `normalized`. Callers write
`normalized(phrase) in normalized(text)`. Add more only when a second call site actually needs it.

### What the RPT-02 test must assert

ROADMAP SC5 (`:185-186`): *"`scripts/_prose.py::normalized` exists and **finds a line-wrapped phrase
that `grep -c` reports as absent**."* That is a **differential** assertion — both halves are required:

1. **The negative control:** `grep -c` (or its Python equivalent, `text.count(phrase)`) returns **0**
   on the fixture. Prove the naive method fails.
2. **The positive:** `normalized(phrase) in normalized(text)` is **True** on the same bytes.
3. **Idempotence:** `normalized(normalized(t)) == normalized(t)`.
4. **The real incident string:** the fixture should be `"the three\nreductions"` searched for
   `"the three reductions"` — the actual v3.0 defect, not a synthetic one. Precedent D-30: *a
   catastrophe that actually happened is not hypothetical.*

Assertion 1 is what stops the test degrading into "a string containment check passes."

---

## 6. Measured Numbers — All Verified

Every number CONTEXT.md cites was recomputed from the committed JSON. **All fifteen reproduce
exactly.**

| CONTEXT claim | Recomputed | Source |
|---|---|---|
| `dialogue_cap` = `4.5837288963367` | `4.5837288963367` ✅ | `4.5733 + 2×0.005214448168350039` |
| `retention_cap` = `4.029000` | `4.029` ✅ | `3.891140 + 2×0.068930` |
| taught adapter fails by `+1.231717` | `1.2317169803754915` ✅ | `phase19_arm_erased.json` `pre_erasure.dialogue_ppl.adapter_on` |
| M1 fails by `+0.267390` | `0.26739025357374313` ✅ | `phase19_arm_erased.json` `dialogue_ppl.adapter_on` |
| D-04 `\|gap₁₃₃₇−gap₂₀₂₄\|` = `0.005214448168350039` | `0.005214448168350039`, **`== DNF` is `True`** ✅ bit-identical | `phase19_dialogue_floor.json` |
| D-06 retention gap 1337 = `0.3286199167186572` | ✅ | `phase19_noise_floors.json` `retention_ppl_pre_erasure.delta_on_minus_off` |
| D-06 retention gap 2024 = `0.33730153571289634` | ✅ arithmetic — **but see §1g: the input `4.2284415113307245` is NOT persisted** | ⚠ CONTEXT.md only |
| D-06 floor = `0.008681618994239138` | ✅ | derived |
| D-06 ratio `7.939763314393305×` | `7.939763314393305` ✅ | `0.068930 / 0.008681618994239138` |
| D-06 new cap `3.9085032379884783` | ✅ — **anchored on the imported constant `3.891140`**, not the measured `3.891139975617828` (which gives `3.9085032136063065`) | ⚠ precision detail: the plan must anchor on `V20_EWC_RETENTION_PPL` |
| D-06 "within 1.66× of the dialogue floor" | `1.6649161548740037` ✅ | |
| D-11 ladder `n=27→0.091079 … 416→0.006462` | all five ✅ exact | `erasure_gate.wilson_upper_bound(0, n)` |
| D-11 "non-decreasing across all 105 outcomes at n=104" | **`True`** ✅ | verified by exhaustive enumeration |
| D-12 `X = 0.321652` → tolerates `25/104 = 24.04%` | `0.3216515249612375`, `25/104`, `24.03846…%` ✅ | |
| D-12 "a floor below `0.008298` tolerates zero leaked questions" | `0.008297560039857446` ✅ | `(wilson(1,104) − wilson(0,104))/2` |
| D-17 M1 retained `0.22362988653603388` of the dialogue gap | ✅; destruction `77.6370113463966%` ✅; `f_C=0.5` is `2.2358×` above (claimed 2.24×) ✅ | |
| D-05 retention gap sign change: taught `+0.3286199167186572`, M1 `−0.22022225029414155` | ✅ both | `3.6709177253236867 − 3.891139975617828` |

### ⚠ One claim I could not reproduce

**D-12: "The margin swings the criterion by 25×."** No computed ratio in the neighbourhood equals
25×:

| Candidate reading | Value |
|---|---|
| floor ratio `0.14814814814814814 / 0.005214448168350039` | **28.41×** |
| X ratio `0.321652 / 0.025355` | **12.69×** |
| borrowed-(b) / adapter-retention floor | **17.06×** |
| tolerated questions | **25** questions (not a ratio) |

Given the next sentence is *"At n=104 the criterion is quantized by the question count"*, the "25"
most plausibly refers to the **25/104 tolerated questions**, restated as a ratio by slip.
**Recommendation: do not retype "25×" into source.** Either write "25 of 104 questions" or re-derive
the ratio in the plan. Every other number in CONTEXT.md is exact; this one is not.

### Artifact shape gotchas

| Artifact | Key | Shape | Trap |
|---|---|---|---|
| `phase19_arm_erased.json` | `dialogue_ppl` | **dict** `{"adapter_off","adapter_on","n_targets"}` | |
| `phase19_arm_erased.json` | `retention_ppl` | **list** `[3.6709177253236867, 1000285]` | ⚠ **different shape from `dialogue_ppl`** — a `(ppl, n)` pair, not a dict. Index, don't `.get()`. |
| `phase19_arm_erased.json` | `pre_erasure` | keys `['dialogue_ppl','exposure','per_fact','retention_ppl']` | CONTEXT's `pre_erasure.dialogue_ppl / retention_ppl` ✅ both present |
| `phase19_noise_floors.json` | top level | `['dialogue_ppl_noise_floor','nontarget_noise_floor','retention_ppl_pre_erasure']` | The value is at `.dialogue_ppl_noise_floor.value`, **not** at the top level |
| `phase19_dialogue_floor.json` | `dialogue_ppl` | keyed by **string** seed: `{"1337": {...}, "2024": {...}}` | ⚠ string keys, not ints |

`phase19_noise_floors.json` also carries `retention_ppl_pre_erasure.cap_derivation =
"3.89114 + 2 x 0.06893 (scripts/erasure_gate.py:246)"` — an in-artifact citation to line 246 that
**is accurate** (`retention_cap = V20_EWC_RETENTION_PPL + MARGIN_K * V20_RETENTION_NOISE_FLOOR`).

---

## 7. Risks / Landmines

### L1 — ⛔ `results/phase20_retention_floor.json` requires a GPU/MPS measurement, and there is no driver

**The problem.** The seed-2024 retention reading `4.2284415113307245` exists **only in
`20-CONTEXT.md`** (§1g). It is in no committed artifact. `results/phase19_noise_floors.json` carries
seed 1337 only.

**Therefore the artifact cannot be produced by transcription.** It needs a re-run of
`retention_perplexity` ON/OFF against both adapters:

| Requirement | Status |
|---|---|
| `checkpoints/phase19_erase_dialogue_floor_seed1337_adapter.pt` | ✅ present locally |
| `checkpoints/phase19_erase_dialogue_floor_seed2024_adapter.pt` | ✅ present locally |
| `checkpoints/` in git | ❌ **gitignored** (`.gitignore:14 checkpoints/`, `:15 *.pt`) — CI can never reproduce this |
| `personacore.evaluation.perplexity.retention_perplexity` | ✅ `src/personacore/evaluation/perplexity.py:148` — `(model, val_bin_path, block_size, device, tokenizer, batch_size=32)` |
| `personacore.lora.adapter_disabled` | ✅ `src/personacore/lora/inject.py:157` — context manager |
| `phase14_recall.load_adapted_model` | ✅ `scripts/phase14_recall.py:513` — `(device, adapter_path=None) -> (model, cfg, tok, forbid, artifact)` |
| The committed ON/OFF pair shape | ✅ `phase19_erasure.dialogue_ppl_pair` at **`:2704-2729`** (CONTEXT ✅ exact), including the denominator `_prove` at `:2723-2727`: `_prove(n_on == n_off, "the two arms scored different denominators … so the delta would measure the corpus rather than the adapter")` |

**Implications the planner must handle:**
1. **This is not a CPU-only task.** It is an MPS model load. It must be a *driver* run once, not a
   test. Every `tests/` file stays GPU-free.
2. **It needs a home.** It cannot go in `scripts/mitigation_gate.py` — adding the driver in the pin,
   then re-running it, is fine, but any *later* edit to the pin after the artifact exists turns the
   ancestry guard permanently red (D-24 / L3). **Precedent: `scripts/phase19_run.py` — an UNPINNED
   driver** (11 commits, referenced in no ancestry guard, labelled `(UNPINNED)` inside
   `phase19_noise_floors.json`'s own `driver` fields) that produced the pinned rule's inputs.
   **Recommendation: a new unpinned driver, e.g. `scripts/phase20_run.py`.**
   ⚠ **But note:** `scripts/phase20_run.py` would match a `phase20_*.py` glob if one is ever created,
   and it is a *scripts* file, not a *results* file, so `V4_ARTIFACT_GLOBS` (which watches
   `results/phase20_*`) does not touch it. Safe.
3. **The ordering.** D-08 requires the artifact **strictly after** the pin. The driver may be committed
   before or with the pin; only the `results/` artifact is ordered.
4. **A bit-identity control is available and should be used.** D-06 claims seed 1337 reproduced
   `phase19_noise_floors.json` byte-for-byte before a new number was produced. That control is
   re-runnable: assert `adapter_off == 3.891139975617828` and `adapter_on == 4.219759892336485` and
   `n_scored_tokens == 1000285` before trusting seed 2024's reading.

### L2 — ⛔ Verdict-domain mismatch: `erasure_gate.VERDICTS` is the WRONG tuple

`erasure_gate.py:136`: `VERDICTS = ("SUCCESS", "FAILURE", "INCONCLUSIVE")`.
GATE-01 (`REQUIREMENTS.md:27`) and D-29 require `PASS` / `FAIL` / `INCONCLUSIVE`.

**`mitigation_gate.py` must declare its own `VERDICTS` tuple and must NOT import `erasure_gate`'s.**
This is easy to get wrong because the "import, never retype" discipline (GATE-02, D-03, D-09) applies
loudly to everything *else* in that file. Note also `ROADMAP.md:172` slips and writes `FAILURE` inside
SC3 ("returns `INCONCLUSIVE` rather than `FAILURE`") while `:167` writes `FAIL` — the requirement
text (`REQUIREMENTS.md:27`) is authoritative: **`FAIL`**.

### L3 — `git merge-base --is-ancestor` reflexivity, and the irreversibility of a red guard

**Reflexivity (D-08) — MEASURED:** `git merge-base --is-ancestor X X` exits **0**. Gate and artifact
in the *same commit* would **pass**. D-08's strict-after rule is therefore a *discipline*, tighter than
the mechanism. The plan must state this so a later reader reads same-commit as neither a defect nor a
licence.

**Irreversibility (D-24) — MEASURED:** `adds[-1]` is the **earliest** add. `git rm` + re-add at the
identical path produces two adds, and `adds[-1]` is byte-identical to the original. **Once the pin is
edited after an artifact exists, no delete-and-re-add recovers.** `tests/test_phase16_prereg.py:293-294`
and `:377-378` state the reason in comments; `:511-516` spells out the consequence:
> *"…permanently reddening `test_phase19_prereg_is_frozen_before_every_phase19_result`, **with no
> recovery**, since that guard takes `adds[-1]`, the EARLIEST add."*

**Practical rule for the executor:** every byte of `mitigation_gate.py` must be final **before** the
commit that adds `results/phase20_retention_floor.json`. There is no second chance.

**Partial escape hatch (measured):** while the artifact stays `git rm`'d, `tracked_artifacts` is empty
and the guard is GREEN. So the red is reversible *only* by not having the artifact — which defeats the
phase. Treat it as irreversible.

### L4 — `mitigation_gate.py` matches no `phase20_*.py` glob

The repo's established AST-scan register is *"a glob, not a hand-listed tuple"*
(`test_phase18_prereg.py:57-59`, `test_phase17_stats.py:62`). Its whole purpose
(`test_phase18_prereg.py:33-37`) is that *"every driver a later plan adds enters these scans the
moment it exists."*

`scripts/mitigation_gate.py` is matched by **no `phase*_*.py` glob**. So:
- D-20's AST guard must target the file by **explicit path constant**, not by glob; and
- if a later v4.0 plan adds a second gate-adjacent module, it **will not** enter the scan
  automatically. That is precisely the F-08 blindness the glob register exists to close.

**Recommendation:** declare `_GATE_MODULES = (_REPO_ROOT / "scripts" / "mitigation_gate.py",)` **plus**
a glob over `scripts/mitigation_*.py`, so `mitigation_budget.py` (Phase 23) enters the no-fact-values
and stdlib-only scans the moment it exists. Keep the `_collapsed_glob_guard()` idiom
(`test_phase18_prereg.py:66-71`) — a glob that stops matching makes every scan green over nothing.

### L5 — CI / pytest constraints

| Constraint | Detail |
|---|---|
| `fetch-depth: 0` | `.github/workflows/ci.yml:19` — already set, with a 14-line comment explaining exactly why. The Phase 20 guard inherits it. **Copy the shallow-clone assertion** (`test_phase16_prereg.py:451-455`) — it is what makes the blindness loud. |
| Python 3.11 | `ci.yml` `python-version: "3.11"`. Local `.venv` is **3.11.15** ✅. Dev box is 3.14 — never validate against it. |
| Extras `[cpu,dev,demo]` | Omitting `demo` → hard **collection error** (gradio imported at module scope by `scripts/personalize_demo.py` via `tests/test_phase14_demo.py`). Identical in `Makefile:11`, `ci.yml:33`, CLAUDE.md. |
| pytest config | `pyproject.toml:24-26` — `testpaths = ["tests"]`, `pythonpath = ["."]`. **No custom markers, no `-p no:randomly`.** `pytest~=9.0`. |
| Lint | `ruff check . && ruff format --check .`, `line-length = 100`. `make format` runs isort then ruff. New files must pass both. |
| RPT-03 | `tests/test_package.py:11` pins `pyproject.toml` sha256 `81d07d5d70…`. Read as **bytes**. Any dependency change turns it red. **Do not touch `pyproject.toml`.** |
| Baseline | `.venv/bin/python -m pytest -q tests/test_phase16_prereg.py tests/test_package.py` → **9 passed** (19.35 s). Confirmed green today. |

### L6 — The D-01 supersession must be written into the pin, not just decided

`results/phase19_erasure_report.md:446-450` publishes the finding CONTEXT D-01 supersedes:
> *"**That is the finding about (c):** at this capacity a one-sided upper cap on dialogue perplexity,
> **anchored either way**, cannot separate 'capability preserved' from 'adaptation removed', because
> both move the number in the same direction."*

and `:453-457` states the boundary the Phase 20 pin must respect:
> *"**NOT that `23a830c` was wrong to be written that way, and NOT that it should be amended.** …
> Amending it now to a cap the data would have cleared is the one move that would void the milestone."*

`docs/REPORT.md:1215` repeats: *"**`23a830c` is not amended.**"*

`.planning/research/SUMMARY.md:439-452` (R5) cites the same 77.6% toward the **opposite** conclusion —
it prescribes `erasure_gate`'s one-sided cap form. **The report is the correct reading; R5 is the
indicted one.** GATE-02 (`REQUIREMENTS.md:31`) and ROADMAP SC1 (`:163-167`) both inherit R5's form
verbatim, prescribing `dialogue_cap 4.5837288963367` as a cap. **CONTEXT D-01 supersedes them.** The
plan must say so explicitly, in the pin, or a plan-checker reading REQUIREMENTS.md alone will flag
D-01 as a deviation.

### L7 — Over-claim avoidance

`20-CONTEXT.md:398-399`: *"do not mark a requirement complete in the first plan that touches it.
Applied six times across Phases 17 and 19."* GATE-01…GATE-10 will be touched by several plans; only
the last one that closes a requirement may tick it.

### L8 — `subprocess.run(check=True)` gives a message-free failure

Noted in §3f. All four existing ancestry guards raise a bare `CalledProcessError` on an ordering
violation. Copying the shape faithfully means inheriting that. Discretionary improvement only.

---

## Runtime State Inventory

> Phase 20 is a **new-code** phase, not a rename/refactor. Included anyway because the phase's whole
> subject is *git-level state*, and one category is genuinely load-bearing.

| Category | Items found | Action required |
|---|---|---|
| **Stored data** | **None** — no database, no vector store. PersonaCore's design forbids them. Verified: no `.db`/`.sqlite` in the repo. | none |
| **Live service config** | **None** — no external services. Verified: no wandb, no network calls in committed code (`test_phase16_stats.py` and CLAUDE.md both forbid them). | none |
| **OS-registered state** | **None** — no launchd/systemd/cron. Verified: no `.plist`/`.service` in the repo. | none |
| **Secrets / env vars** | **None new.** `.gitignore` covers tokens. | none |
| **Build artifacts / gitignored state** | ⚠ **`checkpoints/` is gitignored** (`.gitignore:14-15`). The two adapters D-06's floor is measured from — `phase19_erase_dialogue_floor_seed{1337,2024}_adapter.pt` — exist **only on this machine**. | `results/phase20_retention_floor.json` must **embed** the readings, denominator, seeds, adapter paths, git SHA and record sha256 (the `phase19_noise_floors.json` register) — because the inputs are not reproducible from a fresh clone. |
| **Git-history state** | ✅ **`git log --diff-filter=A -- 'results/phase20_*'` is EMPTY.** D-22's "the real project history stays clean" precondition **currently holds**. Every RED/GREEN fixture must run in `tmp_path`. | Re-verify this command before and after every plan that touches `results/`. |

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| `git` (full clone) | ancestry guard, RED/GREEN fixture | ✓ | — | none — the phase is unimplementable without it |
| Python 3.11 venv | everything | ✓ | 3.11.15 (`.venv`) | none |
| `pytest` | test suite | ✓ | `~=9.0` (`pyproject.toml:19`) | none |
| `ruff` | `make lint` | ✓ | `~=0.15` | none |
| `torch` + MPS | **only** the D-06 retention re-measurement | ✓ | 2.7.1 (recorded in `phase19_noise_floors.json`) | none — cannot be done on CPU-only CI |
| `checkpoints/phase19_erase_dialogue_floor_seed{1337,2024}_adapter.pt` | D-06 floor | ✓ locally, ✗ in git | — | **none** — see L1 |
| `data/retention_val.bin` | D-06 floor | ✓ (`bin_bytes = 2000572`) | — | none |
| network | nothing | n/a | — | phase is fully offline |

**Missing with no fallback:** the two adapters are unavailable in CI. The floor measurement is a
one-time local driver run; only its JSON output is committed. **This is the single environmental
dependency that can block the phase.**

---

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest `~=9.0` (`pyproject.toml:19`) |
| Config | `pyproject.toml:24-26` — `testpaths = ["tests"]`, `pythonpath = ["."]` |
| Quick run | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` |
| Full suite | `.venv/bin/python -m pytest -q` (`make test`) |
| Gate self-check | `.venv/bin/python scripts/mitigation_gate.py` (the `__main__` convention, GATE-09) |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` |
| Baseline today | 9 passed on the two files this phase extends |

### The Nyquist problem for a rule-producing phase

**This phase produces a rule, not a measurement.** There is no number to validate. What must be
sampled is therefore **behaviour of the rule** and **properties of git history** — both fully
deterministic and CPU-only, so the sampling rate can be *every commit*.

Three claims need proof, and each needs a different instrument:

| Claim | Instrument | Why not the obvious one |
|---|---|---|
| Every verdict branch fires | `__main__` self-check **and** a pytest twin | `__main__` is not collected by pytest; a self-check nobody runs in CI is not a guard. SC3 says *"observed returning FAIL through `__main__`"* — so run **both**. |
| The ordering guarantee holds | ancestry test over `git ls-files` | A working-tree glob (Phase 16 shape) inverts the guarantee at arming time (D-21). |
| Zero new dependencies | `tests/test_package.py` sha256 + an AST import scan | The sha256 catches `pyproject.toml`; only the AST scan catches a stdlib-adjacent import inside the gate. |

### Phase Requirements → Test Map

| Req | Behavior | Type | Automated command | File |
|---|---|---|---|---|
| GATE-01 | verdict ∈ `("PASS","FAIL","INCONCLUSIVE")`; keyword-only; no defaults; a reason string per condition | unit + AST | `pytest tests/test_phase20_gate.py -x` | ❌ Wave 0 |
| GATE-02 | caps computed from imported constants; `is`-identity on all four; no `4.5733`/`3.891140`/`0.068930`/`2` literal in the gate's AST | unit + AST | same | ❌ Wave 0 |
| GATE-03 | `Y_taught` and `Y_heldout` are separate required kwargs | unit | same | ❌ Wave 0 |
| GATE-04 | Y derived from `control_*` kwargs; `0.4921`/`0.3483` absent from the gate's AST constants | AST | same | ❌ Wave 0 |
| GATE-05 | zero-extraction-without-NLL → `INCONCLUSIVE`, **precedence over FAIL** | unit | same | ❌ Wave 0 |
| GATE-06 | truncated sweep → `INCONCLUSIVE`, reasons still populated | unit | same | ❌ Wave 0 |
| GATE-07 | verdict carries `arm`; `exists_clearing_point` **raises** on a mixed-arm list; module-scope `_prove` on the claim table == `ARMS` | unit + import-time | same | ❌ Wave 0 |
| GATE-08 | replication kwarg required (no default); all-clear-without-replication → `INCONCLUSIVE`; **no `provisional` field exists** | unit + AST | same | ❌ Wave 0 |
| GATE-09 | `__main__` exits 0 and its output names every branch | subprocess | `.venv/bin/python scripts/mitigation_gate.py` | ❌ Wave 0 |
| GATE-10 | both branches present and reachable; **zero tolerance constant** in the primary branch | unit | `pytest tests/test_phase20_gate.py -x` | ❌ Wave 0 |
| CAL-04 | `K_RUNGS == (48,24,16,8)`; promotion rule takes K as required kwarg; **ratchet rejects a decrease** | unit | same | ❌ Wave 0 |
| RPT-02 | `normalized` finds `"the three\nreductions"`; naive `.count()` returns 0 on the same bytes | unit | `pytest tests/test_phase20_prose.py -x` | ❌ Wave 0 |
| D-20 | gate's AST contains **no** `mitigation_budget` import; no `scipy`/`numpy`/`torch`; bounds imported not redefined | AST | `pytest tests/test_phase20_prereg.py -x` | ❌ Wave 0 |
| D-21/D-22 | ancestry guard, Phase 18 shape; `"results/phase20_*" in V4_ARTIFACT_GLOBS`; shallow-clone assert; RED-then-GREEN in `tmp_path` | subprocess/git | same | ❌ Wave 0 |
| RPT-03 | `pyproject.toml` sha256 unchanged | unit | `pytest tests/test_package.py -x` | ✅ **EXISTS** |
| D-01…D-18 | the pin's own text carries the recorded reasons (asymmetry, `f_Y`/`f_C` as PREFERENCE, D-10's non-transfer) | doc-consistency **via `_prose.normalized`** | `pytest tests/test_phase20_gate.py -x` | ❌ Wave 0 |

### Proving every verdict branch fires (SC3's five behaviors)

`erasure_gate`'s `__main__` demonstrates the pattern for two branches; SC3 requires six outcomes:

| Outcome | Fixture | Expected |
|---|---|---|
| `PASS` | a synthetic clearing point with replication | `PASS` |
| `FAIL` | **D-30's destroyed-model fixture** — dialogue `4.851119149910443`, retention `3.6709177253236867` | `FAIL` |
| `INCONCLUSIVE` (GATE-05) | the `PASS` fixture with `zero_results_have_nll=False` | `INCONCLUSIVE`, **precedence over FAIL** — verify by using a fixture that would otherwise `FAIL` |
| `INCONCLUSIVE` (GATE-06) | a sweep with no points on both sides of X | `INCONCLUSIVE` |
| `INCONCLUSIVE` (GATE-08/D-29) | the `PASS` fixture with replication absent | `INCONCLUSIVE`, **and no `provisional` key on the verdict** |
| arm identity (GATE-07) | a mixed-arm point list | `exists_clearing_point` **raises** |

**Precedence is proved differentially, not by observation.** A fixture that returns INCONCLUSIVE when
it would otherwise return `PASS` proves nothing about precedence over `FAIL`. Each precedence fixture
must be one whose three conditions would produce `FAIL`, so the INCONCLUSIVE is demonstrably
*overriding* it. This is the `erasure_gate.py:253-254` late-return mechanic.

**`__main__` and pytest must both run them.** SC3 says "through `__main__`". Make the fixtures
module-level constants so the pytest twin imports the *same* objects — a second transcription is a
second fixture free to stop matching (the `:2149` register).

### Proving the ordering guarantee holds

Three independent assertions, all in `tests/test_phase20_prereg.py`:

1. **Live guard** — the Phase 18/19 shape over the real repo. Green today (tracked=0), demanding
   non-zero from the first artifact onward.
2. **RED-then-GREEN fixture (D-22)** — the four-state machine in `tmp_path`, re-executed every CI run.
   This is what proves the glob **sees the `phase20_` prefix**, rather than assuming it from reading
   the pattern. Verified mechanically in §3f.
3. **Glob-membership** — `assert "results/phase20_*" in V4_ARTIFACT_GLOBS` (the `:351` / `:444`
   idiom), so the guard and the tuple cannot drift into naming two different path sets.

Plus the **shallow-clone assertion** (`:451-455`) — without it, CI answers the ordering question by
failing to find one.

### Proving zero new dependencies

| Layer | Assertion |
|---|---|
| Package | `tests/test_package.py:27` — `pyproject.toml` sha256 (**exists, passing**) |
| Gate module | AST: `imported == {"math"}` (or a stdlib subset); `"scipy"`/`"numpy"`/`"torch"` absent — the `test_phase16_stats.py:386` template |
| Prose helper | AST: **zero** imports in `scripts/_prose.py`. `" ".join(text.split())` needs none. The `_verdict.py` precedent is a one-import module with a committed `grep -c` guard on it (`260802-h3g-PLAN.md:180`). |
| Test module | `tests/test_phase20_prereg.py` imports only `ast`, `pathlib`, `subprocess` (+ `pytest` for `tmp_path`) |

### Sampling Rate

- **Per task commit:** `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py tests/test_phase20_gate.py tests/test_phase20_prose.py && .venv/bin/python scripts/mitigation_gate.py`
- **Per wave merge:** `.venv/bin/python -m pytest -q && .venv/bin/ruff check . && .venv/bin/ruff format --check .`
- **Phase gate:** full suite green + `git log --diff-filter=A -- 'results/phase20_*'` reviewed for D-22 cleanliness + the ancestry guard green **on a fresh full-depth clone**.

### Wave 0 Gaps

- [ ] `tests/test_phase20_prereg.py` — ancestry guard (D-21), `V4_ARTIFACT_GLOBS` (D-22), RED/GREEN
      fixture, AST no-budget-import guard (D-20). Covers GATE ordering + CAL-04's ordering half.
- [ ] `tests/test_phase20_gate.py` — every verdict branch, keyword-only/no-default AST checks,
      imported-constant identity, the two-chosen-constants audit (D-18). Covers GATE-01…GATE-10, CAL-04.
- [ ] `tests/test_phase20_prose.py` — RPT-02, including the naive-`count()`-returns-0 negative control.
- [ ] **No framework install needed** — pytest 9 is present and the suite is green.
- [ ] **No `conftest.py` change needed** — `tests/conftest.py` provides `simulate_pascal` and
      `fake_lm`; Phase 20 needs neither (no torch). Use pytest's built-in `tmp_path`.

*Note: three test files rather than one is the repo's own register — `test_phase16_prereg.py` (ordering),
`test_phase16_stats.py` (AST/stdlib), `test_phase16_ladder.py` (behaviour) are already split this way.*

---

## Security Domain

`security_enforcement` is not set in `.planning/config.json`; the section is included for
completeness. **Phase 20 has effectively no attack surface**: a stdlib-only pure-function module, a
5-line string helper, and a test that shells out to `git` with a fixed argv.

| ASVS Category | Applies | Control |
|---|---|---|
| V2 Authentication | no | no auth surface |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | local CLI only |
| V5 Input Validation | **yes** (weakly) | The gate's inputs are numbers from committed JSON, not untrusted input. The real discipline is **semantic**: required kwargs, no defaults, `_prove` on denominators. `erasure_gate.py:150-153` raises `ValueError` on `n <= 0` and on `successes` outside `[0, n]` — **copy that guard shape** for any new estimator. |
| V6 Cryptography | no | sha256 is used as a content digest, not a security primitive |

**Relevant threat pattern — not a classic one.** The threat model here is *epistemic*: a threshold
edited after seeing the data. STRIDE-wise it is **Tampering** (with the evidentiary record) plus
**Repudiation** (of when a rule was written). The mitigation is exactly the one this phase builds:
ancestry against the git object DAG, never committer dates. `tests/test_phase16_prereg.py:11-17`
states the reasoning:

> *"**Ancestry, never dates.** The obvious implementation compares committer dates and is wrong.
> Committer dates are rewritable by anyone with a shell, skewed across machines, and non-monotonic
> after a rebase… To make `git merge-base --is-ancestor` lie you would have to rewrite every object
> between the two commits, which changes both SHAs, which fails the identity check below."*

**One real subprocess note:** every `git` call uses `subprocess.run(("git", *args), ...)` — an
**argv tuple, never `shell=True`**. `artifact_glob` is passed as an argv element, so the shell never
sees it and git handles it as a pathspec. Keep this. A `shell=True` variant would make a glob
containing a shell metacharacter an injection point.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | The seed-2024 retention reading `4.2284415113307245` was produced by the same instrument as seed 1337 and is reproducible on this machine | §1g, L1 | If not reproducible, `results/phase20_retention_floor.json` cannot be honestly produced and D-06's floor has no committed provenance. **Mitigation: the seed-1337 bit-identity control re-runs first.** |
| A2 | D-12's "25×" is a mis-stated restatement of "25 of 104 questions" | §6 | Retyping "25×" into the pin ships an unverifiable number into an unamendable file. **Mitigation: do not retype it.** |
| A3 | Widening `V4_ARTIFACT_GLOBS` beyond `phase20_*` to all v4.0 prefixes is desirable | §3e | Not a locked decision. If a later phase legitimately needs a pre-artifact write (the `phase19_floor.py` situation), a pre-declared glob could redden it. **Mitigation: raise with the user before widening.** |
| A4 | `scripts/phase20_run.py` is an acceptable name for the unpinned floor driver | L1 | Naming is the planner's to fix; only the *unpinned-driver* pattern is precedent-backed. |
| A5 | Three test files is the right split | Validation Architecture | Mirrors the Phase 16 split. One file would also work; this is style, not correctness. |

**Everything else in this document was read from the file or executed in this session.**

---

## Open Questions

1. **Where does the D-06 floor driver live, and is it in scope for Phase 20?**
   - Known: the artifact is required (D-08); its inputs are not persisted (§1g); the pin cannot own
     the driver safely (L3); `phase19_run.py` is the unpinned-driver precedent.
   - Unclear: CONTEXT.md names four deliverables and a driver is not among them.
   - **Recommendation:** the planner adds a fifth deliverable — an unpinned measurement driver — or
     escalates to the user. **Do not let a plan assume the JSON can be hand-written from CONTEXT.md**:
     that would publish a number with no re-runnable provenance, which is the exact discipline
     `20-CONTEXT.md:422-424` demands be carried into this phase.

2. **Does `V4_ARTIFACT_GLOBS` pre-declare all v4.0 prefixes, or only `phase20_*`?**
   - Known: D-22 mandates `phase20_*`. The `V3_ARTIFACT_GLOBS` comment argues for pre-declaring.
   - Unclear: whether a later v4.0 phase needs a `phase19_floor.py`-style sanctioned pre-artifact write.
   - **Recommendation:** start with `phase20_*` (the locked decision) and record the widening question
     as a decision for Phase 21's planning.

3. **Does the D-14 tolerance reporter need a committed test fixture with a real X?**
   - Known: X is not computable in Phase 20 (D-13); `floor_branch()` (`phase19_erasure.py:944-961`)
     is the precedent and is a pure function of its input.
   - **Recommendation:** test the reporter on the D-12 counterfactual (`X = 0.3216515249612375 →
     "tolerated 25/104"`) **explicitly labelled a counterfactual**, on the 19-16 precedent D-30 cites.

---

## Sources

### Primary — files read in full or in cited ranges (HIGH)
- `scripts/erasure_gate.py` (291 lines, read in full)
- `scripts/_addendum.py` (101 lines, read in full); `scripts/_verdict.py` (31 lines, read in full)
- `tests/test_phase16_prereg.py` `:1-130`, `:130-410`, `:406-605` (622 lines total)
- `tests/test_phase18_prereg.py` `:1-150`, `:212-252`
- `tests/test_package.py` (46 lines, read in full); `tests/conftest.py` (read in full)
- `tests/test_phase16_stats.py:380-415`
- `scripts/phase18_extraction.py:80-100`; `scripts/phase19_erasure.py:2695-2745`, `:3870-3890`,
  `:944-970`, `:1210-1235`; `scripts/phase19_floor.py:145-175`
- `.planning/REQUIREMENTS.md:21-56`, `:113-144`, `:214-226`, `:271-282`
- `.planning/ROADMAP.md:133-190`; `.planning/PROJECT.md:185-216`; `.planning/STATE.md` (tail)
- `.planning/RETROSPECTIVE.md:172-195`; `.planning/research/PITFALLS.md:1048`;
  `.planning/research/SUMMARY.md:439-452`; `.planning/milestones/v3.0-MILESTONE-AUDIT.md:100-118`
- `results/phase19_noise_floors.json`, `phase19_arm_erased.json`, `phase19_dialogue_floor.json`,
  `phase19_calibration_correction.json` (parsed programmatically)
- `results/phase19_erasure_report.md:440-466`; `results/phase14_recall_report.md:458-466`;
  `docs/REPORT.md:1172-1176`, `:1212-1216`
- `Makefile`, `pyproject.toml:19-39`, `.github/workflows/ci.yml:1-40`, `.gitignore:14-15`

### Executed in this session (HIGH — measured, not read)
- `git log --diff-filter=A -- 'results/phase20_*'` → **empty** (D-22 clean-history precondition)
- `git log --oneline -- scripts/erasure_gate.py` → **one commit, `23a830c`**; `git show --stat` → 291 lines
- Two throwaway `mktemp -d` git repos — reflexivity, `adds[-1]`, delete/re-add, red-after-edit
- `.venv/bin/python` arithmetic reproduction of all fifteen CONTEXT.md measured claims
- Exhaustive `wilson_upper_bound` monotonicity check over all 105 outcomes at n=104
- `fnmatch` check of `_addendum.py`/`_verdict.py`/`_prose.py` against `phase1[6-9]_*.py`/`phase20_*.py`
- `git ls-files 'results/phase19_*'` → 27 files, `*` crosses `/`
- `.venv/bin/python scripts/erasure_gate.py` → self-check OK, 6 clauses
- `.venv/bin/python -m pytest -q tests/test_phase16_prereg.py tests/test_package.py` → **9 passed**

### Not consulted
No web search, no Context7, no external documentation. **Deliberate** — the objective scoped this to
in-repo archaeology, and every question was answerable from the repository.

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|---|---|---|
| Identifier & path table | **HIGH** | Every name read from its defining line; every new file's absence verified two ways (`ls` + `git ls-files`) |
| `erasure_gate.py` anatomy | **HIGH** | File read in full (291 lines) and `__main__` executed |
| Ancestry guard shapes | **HIGH** | Both functions read in full; the state machine re-run in throwaway repos |
| `_addendum.py` refusal | **HIGH** | Module read in full; the refusal traced through `text.count(pending)` |
| RPT-02 incident | **HIGH** | Three independent records; the implementation prescribed verbatim in PITFALLS.md |
| Measured numbers | **HIGH** | All fifteen recomputed from committed JSON. **One exception: D-12's "25×" — LOW, could not be reproduced under any reading** |
| CONTEXT citation defects | **HIGH** | Each corrected location read directly |
| Validation architecture | **MEDIUM** | Framework and commands verified; the three-file split and specific test names are proposals |

**Research date:** 2026-08-20
**Valid until:** stable until any commit touches `scripts/erasure_gate.py` (which would itself be a
milestone-voiding event), `tests/test_phase16_prereg.py`, or `results/phase19_*`. **Re-verify
`git log --diff-filter=A -- 'results/phase20_*'` before every plan that touches `results/`.**
