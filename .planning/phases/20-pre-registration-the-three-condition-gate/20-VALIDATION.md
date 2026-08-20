---
phase: 20
slug: pre-registration-the-three-condition-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-20
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `20-RESEARCH.md` § "Validation Architecture" (`:975`).

**What makes this phase unusual:** it produces a *rule*, not a measurement. Nothing here validates a
number's correctness — the thing under test is whether every verdict branch **actually fires**,
whether the **ordering guarantee** holds against git's object graph, and whether the dependency
surface stayed **empty**. A gate nobody has watched fail is a gate nobody has verified.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x — CPU-only, GPU-free (mandatory: `tests/` must not require MPS/CUDA) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_phase20_prereg.py -q` |
| **Full suite command** | `make test` |
| **Estimated runtime** | **UNMEASURED — measure at Wave 0 and write the real number here.** Do not fabricate. |
| **Environment** | Python 3.11 venv, `pip install -e ".[cpu,dev,demo]"`. The `demo` extra is **required for collection**, not just for running the demo. |

**Exception, stated explicitly:** the D-32 retention-floor driver is the one artifact in this phase
that **requires MPS** and is therefore **not** part of the CPU-only suite. It is run once, by hand,
and its output artifact is what the suite may read. The driver itself is never invoked from a test.

---

## Sampling Rate

- **After every task commit:** `pytest tests/test_phase20_prereg.py -q`
- **After every plan wave:** `make test`
- **Before `/gsd:verify-work`:** full suite green
- **Max feedback latency:** to be set from the Wave 0 measurement above

---

## Per-Task Verification Map

*Filled by the planner — one row per task, no task without a row.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | GATE-01 | — | N/A | unit | `pytest tests/test_phase20_prereg.py -q` | ❌ W0 | ⬜ pending |

---

## The three things this phase must prove

### 1. Every verdict branch is watched firing (GATE-05…GATE-09)

ROADMAP SC3 names **five distinct branch behaviors**. Each needs an observation, not an assertion
that it was written:

| # | Branch | Must be observed | Req |
|---|--------|------------------|-----|
| 1 | Destroyed-model fixture → `FAIL` | Run through `__main__`, from D-30's **real published M1 readings** (dialogue `4.851119149910443`, retention `3.6709177253236867`, 77.637% destruction). Labelled a **fixture**, never a second reading of the experiment. | GATE-09 |
| 2 | Zero extraction without corroborating teacher-forced NLL → `INCONCLUSIVE`, taking **precedence over `FAIL`** | `zero_results_have_nll` shape | GATE-05 |
| 3 | Sweep with no points on both sides of X (or of Y) → `INCONCLUSIVE`, **not** `FAIL` | | GATE-06 |
| 4 | Verdict carries **arm identity**; `exists_clearing_point` **refuses a mixed-arm point list** | so a DP clear and an adversarial clear cannot be conflated under one ∃ | GATE-07 |
| 5 | All three conditions clear **without** second-seed replication → `INCONCLUSIVE`, never `PASS` | replication argument **required, no default**. A `PASS` carrying `provisional=True` was **explicitly rejected** (D-29). | GATE-08 |

Plus, at import: **`_prove_verdict_domain()`** (D-31) — equal length, correct positional
correspondence against `erasure_gate.VERDICTS`, `INCONCLUSIVE` identical in both vocabularies.
A dead gate must fail **at import**, not after the compute it would waste.

### 2. The ordering guarantee holds (CAL-04, the phase goal)

- **Guard shape:** Phase 18 shape only (D-21) — `git ls-files`,
  `checked == len(prereg) × len(tracked)`, **and** `bool(checked) == bool(tracked_artifacts)`.
  Green while zero artifacts are tracked; demands non-zero from the first one onward.
  **Never** the Phase 16 shape (`assert checked` over a working-tree glob) — it is RED from the
  pin's first commit until an artifact lands, **inverting the ordering this phase exists to
  establish**. Research recommends `tests/test_phase16_prereg.py:406-497` (the Phase 19 twin) as
  the closest structural model — same Phase 18 shape, and its docstring describes Phase 20's exact
  arming-before-artifacts situation.
- **Globs:** `phase20_*` only (D-33).
- **RED-then-GREEN fixture (D-22):** committed, re-executed every CI run, in a **throwaway repo**.
  Four states, all measured during discussion and re-confirmed by research:
  probe-before-pin → RED via `assert prereg_commits` (a *different* red) · pin second → **RED with
  the ordering message** (this is the proof the glob sees the prefix) · `git rm` probe → **GREEN**,
  tracked=0 (the red is reversible) · re-add at identical path → **RED again**, first-add unchanged
  (laundering impossible).
  **Mechanical gotcha from research:** `git rm` of the last file removes the parent dir — the
  fixture needs `mkdir -p` before re-adding.
- **The real repo's history stays clean:** `git log --diff-filter=A -- 'results/phase20_*'` must
  remain empty of any probe. Research confirmed it is currently empty.

### 3. Zero new dependencies (RPT-03)

- `pyproject.toml` **untouched**. `tests/test_package.py` turns red on any new dependency.
- `scripts/mitigation_gate.py` is **stdlib-only** and must **never** import
  `scripts/mitigation_budget.py` (Phase 23). Enforced by an **AST guard**. Research finding:
  `_GATE_MODULES` lives in `tests/`, not `scripts/phase17_*.py`, and `mitigation_gate.py` matches
  **no `phase20_*.py` glob** — so the AST guard needs an **explicit path constant**, not a glob.

---

## Wave 0 Requirements

- [ ] `tests/test_phase20_prereg.py` — new file; stubs for GATE-01…GATE-10, CAL-04, RPT-02
- [ ] Measure and record the real full-suite runtime in the table above
- [ ] Confirm `pytest` collects cleanly on a fresh venv with `[cpu,dev,demo]`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| D-32 retention-floor driver run | D-06 / D-32 | Requires **MPS**; the suite is CPU-only by mandate. One run, no retraining. | Run the driver against `checkpoints/phase19_erase_dialogue_floor_seed{1337,2024}_*`. It must reproduce `seed_1337 = 4.219759892336485` and `seed_2024 = 4.2284415113307245`, then write `results/phase20_retention_floor.json`. **Commit strictly AFTER `scripts/mitigation_gate.py` (D-08).** |
| Ordering discipline on commit sequence | CAL-04, D-08 | Git ordering is established by the human's commit sequence, not by a test that can enforce it prospectively. `git merge-base --is-ancestor` is **reflexive** — research confirmed same-commit passes — so D-08's "strictly after" is **discipline, not mechanism**. | Verify `scripts/mitigation_gate.py` is committed **and pushed** before any `results/phase20_*` file is added. |

---

## Landmines (from `20-RESEARCH.md` § 7)

- **A red ancestry guard is irreversible.** The guard takes `adds[-1]` — the **earliest** add.
  `git rm` + re-add cannot launder it (research re-confirmed byte-identically). Once any
  `results/phase20_*` artifact is committed, **editing `mitigation_gate.py` turns the guard
  permanently red.** Corrections are **dated continuations** via `scripts/_addendum.py` (D-24),
  never edits, and must arm a **tripwire test** — a prose note gets missed.
- **`_addendum.py` refuses a second append** (`text.count(pending) == 0` → `SystemExit`).
  D-24 verified. Its three properties: exactly-one-placeholder, verdict-section invariance,
  append-only-prefix. **One correction from research:** property 1 runs on the **input**, not the
  produced bytes — the module's own docstring at `:37` overstates this.
  `RETROSPECTIVE.md:189-191` records a **cheaper sanctioned path** than "written directly": the
  identity marker pair `pending=recorded=<consumed line>`, used three times with zero deletions.
- **D-12's "25× swing" reproduces under no reading** (research candidates: 28.41×, 12.69×, 17.06×).
  Most likely a mis-stated "25 of 104 questions." **Do not retype this figure into any artifact.**

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Full-suite runtime measured and recorded (not estimated)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
