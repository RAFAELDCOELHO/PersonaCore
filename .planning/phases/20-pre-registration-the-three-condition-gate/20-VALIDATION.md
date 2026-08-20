---
phase: 20
slug: pre-registration-the-three-condition-gate
status: active
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
| **Quick run command** | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` |
| **Full suite command** | `make test` (equivalently `.venv/bin/python -m pytest -q`) |
| **Full-suite runtime** | **RE-MEASURED with this phase's tests present, plan 20-06 Task 3, 2026-08-20: `863 passed, 1 skipped, 0 failed` in `188.55s`** (wall `189.72s`). Timed, not estimated. Supersedes the pre-phase baseline `845 passed, 1 skipped` in `201.99s`, which was measured before any Phase 20 code existed. **The 18 tests Phase 20 adds cost `~1.6s`; the `13.44s` drop against the old row is MACHINE VARIANCE, not a speedup** — an unreplicated single-run difference on a laptop, stated as such rather than claimed as an improvement. |
| **Quick-run runtime** | **MEASURED, plan 20-06 Task 3, 2026-08-20: `18 passed` in `0.79–0.81s`** across three consecutive runs (wall `0.95–0.97s` including interpreter startup). This is the latency that actually governs this phase, and it is `~235x` cheaper than the full suite. |
| **Environment** | Python 3.11 venv, `pip install -e ".[cpu,dev,demo]"`. The `demo` extra is **required for collection**, not just for running the demo. |

**Exception, stated explicitly:** the D-32 retention-floor driver is the one artifact in this phase
that **requires MPS** and is therefore **not** part of the CPU-only suite. It is run once, by hand,
and its output artifact is what the suite may read. The driver itself is never invoked from a test.

**Ruff is part of every gate.** `pyproject.toml:44` sets `select = ["E", "F", "W", "I"]`, so an
imported-but-unused name is an **F401** and turns `ruff check .` red. That is why every import in
this phase — in `scripts/mitigation_gate.py`, in `tests/test_phase20_prereg.py` — lands in the task
that **first consumes it**, never earlier. The IMPORT ACCUMULATION LEDGER in `20-01-PLAN.md`
`<interfaces>` is authoritative for which name enters where.

---

## Sampling Rate

- **After every task commit:** `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py`
- **After every plan wave:** `make test` (the full suite, at the plan's `<verification>` block)
- **Before `/gsd:verify-work`:** full suite green
- **Max feedback latency: `0.81 s`** — the per-task gate, MEASURED at plan 20-06 Task 3 (`18 passed`,
  three runs, `0.79–0.81s`). Its ceiling is the full suite at **`188.55 s`**, which is precisely the
  cost the per-task/per-wave split exists to avoid paying eighteen times. Over the **14 non-exempt
  tasks** — the four exemptions below pay it deliberately — the split saves
  `14 x (188.55 - 0.81) = 2628 s`, about **44 minutes** of serial waiting. The naive "18 x" figure
  would read 56 minutes and would be wrong, because four of the eighteen run the full suite anyway.

**Four tasks are exempt and run the FULL suite by design**, each for a stated reason:
`20-06-03` must measure the full-suite runtime; `20-07-01` is the blocking human checkpoint that
declares the pin final and must see the whole repo green; `20-07-02` introduces a new `scripts/*.py`
file, which enters repo-wide AST scans that glob `scripts/*.py` (for example
`tests/test_phase16_stats.py`'s `persona=` guard over 69 files) — only the full suite catches that.
`20-07-03` also runs it, because it is the commit that makes the ordering irreversible.

---

## Per-Task Verification Map

*One row per task. Eighteen tasks, eighteen rows.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | GATE-01 | T-20-03, T-20-04 | Verdict domain and arm set proved at MODULE SCOPE via `SystemExit`, not `assert` — unstrippable under `-O`. A dead gate fails at import, not after the compute it would waste. | unit | `.venv/bin/python -c "…import mitigation_gate…"` + `.venv/bin/ruff check scripts/mitigation_gate.py` | ⬜ created by this task | ⬜ pending |
| 20-01-02 | 01 | 1 | GATE-02, CAL-04 | T-20-06 | Exactly two chosen constants; the superseded GATE-02 dialogue cap is COMPUTED from two imported terms, never retyped. Float audit prints exactly `[0.5, 0.7]`. | unit | `.venv/bin/python -c "…CHOSEN_CONSTANTS / superseded_dialogue_cap / float audit…"` + `.venv/bin/ruff check .` | ✅ | ⬜ pending |
| 20-01-03 | 01 | 1 | CAL-04 | T-20-01, T-20-02, T-20-05 | Ancestry guard armed BEFORE any artifact, answered against git's object DAG and never against committer dates. `bool(checked) == bool(tracked_artifacts)`, never `assert checked`. | integration | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | ⬜ created by this task | ⬜ pending |
| 20-02-01 | 02 | 2 | GATE-01 | T-20-07, T-20-08, T-20-10 | Armed provenance tripwire at the ONE choke point: wrong arm, <2 distinct seeds, or missing key each abort with `SystemExit`. X is never a literal. | unit | `.venv/bin/python -c "…extraction_ceiling tripwire drive…"` + `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | ✅ | ⬜ pending |
| 20-02-02 | 02 | 2 | GATE-01 | T-20-09 | Criterion strength is PUBLISHED, not computed into a local that never reaches the caller (`erasure_gate.py:245-247`'s defect). Every number carries its denominator. | unit | `.venv/bin/python -c "…tolerance_report 25/104 + zero-tolerance drive…"` | ✅ | ⬜ pending |
| 20-03-01 | 03 | 2 | RPT-02 | T-20-15, T-20-16 | DIFFERENTIAL proof: the naive read returns 0 on the same bytes where `normalized` succeeds. Zero-import AST scan over `_prose.py`. | unit | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py -k "normalized or imports_nothing"` | ✅ | ⬜ pending |
| 20-03-02 | 03 | 2 | RPT-02, CAL-04 | T-20-12, T-20-13, T-20-14, T-20-17 | Four-state RED-then-GREEN in a THROWAWAY repo against the real `_assert_ordering_holds`; `adds[-1]` proved unlaunderable; the real history verified untouched before and after. | integration | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | ✅ | ⬜ pending |
| 20-04-01 | 04 | 3 | GATE-02, GATE-03 | T-20-18, T-20-19 | (c)'s two legs ASYMMETRIC by design, with the reason in the source so a "unify them" refactor goes red. `V20_RETENTION_NOISE_FLOOR` neither imported nor retyped. | unit | `.venv/bin/python -c "…dialogue_gap_band / retention_cap drive…"` | ✅ | ⬜ pending |
| 20-04-02 | 04 | 3 | GATE-01, GATE-04, GATE-05, GATE-06, GATE-08 | T-20-20, T-20-21, T-20-22, T-20-23, T-20-24 | 21 keyword-only defaultless args; INCONCLUSIVE ahead of FAIL; no `provisional`; no `V20_TAUGHT_RECALL` / `V20_HELDOUT_RECALL`. | unit | `.venv/bin/python -c "…AST signature + forbidden-name scan…"` + `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | ✅ | ⬜ pending |
| 20-05-01 | 05 | 4 | GATE-07 | T-20-29 | The existential is computed PER ARM and a mixed-arm point list is refused with `SystemExit`, so a DP clear and an adversarial clear cannot be unioned. INCONCLUSIVE never satisfies ∃. | unit | `.venv/bin/python -c "…exists_clearing_point drive…"` | ✅ | ⬜ pending |
| 20-05-02 | 05 | 4 | GATE-10, CAL-04 | T-20-25, T-20-26, T-20-27, T-20-28 | K ratchet refuses any decrease (the ATK-03 / P18-4 weakening); capacity dispatch TOTAL over all four flag pairs; unset fallback tolerance raises naming D-26. | unit | `.venv/bin/python -c "…ratchet_k / promote_to_full_fidelity / capacity_comparison drive…"` | ✅ | ⬜ pending |
| 20-05-03 | 05 | 4 | GATE-09 | T-20-30, T-20-31, T-20-32 | SIX outcomes watched firing; three precedence claims proved DIFFERENTIALLY against the verdict each overrides; fixtures proved equal to the published artifact, `control_gap` built as a subtraction. | integration | `.venv/bin/python scripts/mitigation_gate.py` + `.venv/bin/python -c "…fixture-vs-JSON identity…"` | ✅ | ⬜ pending |
| 20-06-01 | 06 | 5 | GATE-02 | T-20-33, T-20-34, T-20-39 | Import graph proved stdlib + `erasure_gate` only, by SUBSET over an allow-set; the five-name `from erasure_gate` list proved COMPLETE by exact equality; bounds proved imported by `is`, never `==`. | unit | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | ✅ | ⬜ pending |
| 20-06-02 | 06 | 5 | GATE-01, GATE-04 | T-20-35, T-20-36, T-20-37 | Exactly two chosen constants; six baselines proved absent; no fourth verdict state; the `FIXTURE_*` exclusion's residual hole stated in words and narrowed by a name allow-list. | unit | `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | ✅ | ⬜ pending |
| 20-06-03 | 06 | 5 | GATE-05, GATE-06, GATE-07, GATE-08, GATE-09, GATE-10 | T-20-38 | `__main__` is not collected by pytest, so every branch is re-run in CI against the SAME module-scope fixtures, plus the module run as a subprocess in a fresh interpreter. | integration | `.venv/bin/python -m pytest -q` **(FULL — this task measures its runtime)** | ✅ | ⬜ pending |
| 20-07-01 | 07 | 6 | CAL-04 | T-20-40, T-20-41 | BLOCKING human gate: nine commands run and reported verbatim; `HEAD == @{u}` proves PUSHED, not merely committed; the last moment an edit is legal. | manual + automated | `.venv/bin/python -m pytest -q` **(FULL)** + `git fetch && rev-parse HEAD/@{u}` | ✅ | ⬜ pending |
| 20-07-02 | 07 | 6 | GATE-02 | T-20-43 | The `forbid`-into-`batch_size` instrument trap closed by AST: two `retention_perplexity` call sites, five positional args, `tok` fifth, zero keywords; `forbid_ids` absent. | unit | AST call-site check + `.venv/bin/python -m pytest -q` **(FULL — new `scripts/*.py` enters repo-wide scans)** | ⬜ created by this task | ⬜ pending |
| 20-07-03 | 07 | 6 | CAL-04 | T-20-42, T-20-44, T-20-45, T-20-46 | Seed-1337 bit-identity control (`==`, no tolerance) runs BEFORE seed 2024 is trusted; non-reproduction is a STOP, not a reconciliation; artifact lands in its OWN commit strictly after a pushed pin. | manual (MPS) + automated | `.venv/bin/python -c "…artifact JSON assertions…"` + `.venv/bin/python -m pytest -q` **(FULL)** + `git merge-base --is-ancestor` | ⬜ created by this task | ⬜ pending |

**Requirement coverage from this map:** GATE-01, GATE-02, GATE-03, GATE-04, GATE-05, GATE-06,
GATE-07, GATE-08, GATE-09, GATE-10, CAL-04, RPT-02 — 12 of 12. RPT-03 (`pyproject.toml` untouched)
is asserted in every plan's `<verification>` block rather than owned by a single task, because it is
a property of the whole phase.

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

## Wave 1 is this phase's Wave 0

There is no separate wave 0: plan `20-01` is wave 1 and arms both the pin and the guard, which is the
point (the guard must exist before there is anything to miss).

- [x] Full-suite baseline measured and recorded above — `845 passed, 1 skipped` in `201.99s`,
      2026-08-20, **before** any Phase 20 code exists. Re-measured with this phase's tests at
      plan `20-06` Task 3.
- [ ] `tests/test_phase20_prereg.py` created — plan `20-01` Task 3, ticked by plan `20-07` Task 3's
      sweep. This box is what `wave_0_complete: true` asserts. Coverage for GATE-01…GATE-10, CAL-04
      and RPT-02 accumulates across waves 1→5 per the map above; there are no stubs, because a stub
      for a rule that does not exist yet is an unproven assertion.

The fresh-venv `[cpu,dev,demo]` collection check is deliberately NOT a box here: no task in this
phase owns it, and the packaging surface it guards is asserted byte-unchanged
(`git status --porcelain pyproject.toml` prints nothing) in all seven plans' `<verification>` blocks.
An unowned checkbox is an unproven assertion.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| D-32 retention-floor driver run | D-06 / D-32 | Requires **MPS**; the suite is CPU-only by mandate. One run, no retraining. | Run the driver against `checkpoints/phase19_erase_dialogue_floor_seed{1337,2024}_*`. It must reproduce `seed_1337 = 4.219759892336485` and `seed_2024 = 4.2284415113307245`, then write `results/phase20_retention_floor.json`. **Commit strictly AFTER `scripts/mitigation_gate.py` (D-08).** |
| Ordering discipline on commit sequence | CAL-04, D-08 | Git ordering is established by the human's commit sequence, not by a test that can enforce it prospectively. `git merge-base --is-ancestor` is **reflexive** — research confirmed same-commit passes — so D-08's "strictly after" is **discipline, not mechanism**. | Verify `scripts/mitigation_gate.py` is committed **and pushed** before any `results/phase20_*` file is added. |
| Pin declared FINAL | CAL-04, D-24 | Task `20-07-01` is a blocking checkpoint. Only a human can judge "is this rule right?" while an edit is still legal and reversible. | Read `scripts/mitigation_gate.py` end to end. After the next commit, editing it turns the ancestry guard permanently red and `git rm` + re-add cannot undo it (`adds[-1]` is the EARLIEST add). |

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
- **An import ahead of its consumer is an F401 and turns every task in the wave red.** The gate's
  `from erasure_gate import ...` list and the test module's imports are BUILT UP name-by-name across
  waves 1→5. Follow the IMPORT ACCUMULATION LEDGER in `20-01-PLAN.md` `<interfaces>`; do not declare
  the final list early "to save an edit."
- **A retyped double is a wrong double.** `5.815445876712191 - 4.573349214207799` is
  `1.2420966625043919`, not `1.242096662504392`. Build derived values as their arithmetic; both float
  audits exclude `FIXTURE_*`, so a retyped fixture field ships unaudited.

---

## Validation Sign-Off

- [x] All tasks have an `<automated>` verify — 18 of 18 rows above, no task without one
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Per-task gate is the phase test file, not the 202 s full suite; the four full-suite
      exemptions each carry a stated reason
- [x] No watch-mode flags
- [x] Full-suite runtime measured and recorded (not estimated) — pre-phase baseline
- [x] Full-suite runtime **re-measured with this phase's tests** — plan `20-06` Task 3:
      `863 passed, 1 skipped` in `188.55s`
- [x] Quick-run (`tests/test_phase20_prereg.py`) runtime measured — plan `20-06` Task 3:
      `18 passed` in `0.79–0.81s`, three runs
- [ ] `nyquist_compliant: true` set in frontmatter — plan `20-07` Task 3
- [ ] `wave_0_complete: true` set in frontmatter — plan `20-07` Task 3

**Approval:** planner, 2026-08-20 — Per-Task Verification Map complete at 18/18 with 12/12
requirement coverage; sampling rate split into per-task (phase file) and per-wave (full suite).
Runtime re-measurement and the two frontmatter flags are owned by `20-06` Task 3 and `20-07` Task 3
respectively and remain open until those tasks run.
