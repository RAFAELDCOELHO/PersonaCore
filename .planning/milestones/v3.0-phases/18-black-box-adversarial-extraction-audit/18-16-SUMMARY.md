---
phase: 18-black-box-adversarial-extraction-audit
plan: 16
subsystem: evaluation
tags: [verdict, publication, append-only, over-claim-avoidance, requirements-ledger, handoff]

# Dependency graph
requires:
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-15's `9a923d6` — the two paired arm records the report is assembled from"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-11's `render_report` / `assemble_verdict` / `licensed_conclusion` / `assert_extraction_report_not_clobbered`, and `append_addendum` (`ec18cfe`)"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "18-12's `5ddb225` — the dated v3.0 continuations in README.md and docs/REPORT.md this plan appends below"
  - phase: 17-multi-persona-isolation-matrix
    provides: "results/phase17_isolation_report.md:270-272 — the three collateral-collapse figures D-21's exclusion is quantified with"
provides:
  - "`results/phase18_extraction_report.md` — the verdict-bearing committed evidence, `LEAKAGE_DEMONSTRATED`, write-once"
  - "`docs/REPORT.md`'s 2026-08-17 continuation — the measured result published with both bounds and the lower-bound self-qualification"
  - "ATK-01..ATK-06 closed in `.planning/REQUIREMENTS.md` with an evidence table naming the artifact per requirement"
  - "`test_extraction_report_addendum_is_additive` — the published-artifact additivity guard the suite was missing"
  - "The Phase 19 handoff `(92, 104, 0, 104)`, measured rather than chosen"
affects: [19]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A published figure whose ADVERSE reading is written beside it by the same hand, in the same section, rather than left for a reader to derive"
    - "An unsatisfiable acceptance criterion closed by APPENDING beside the evidence instead of by re-running the writer that would destroy it"
    - "A guard over the PUBLISHED artifact as the twin of a guard over the writer — a writer can be append-only and still have been run against a file another hand rewrote"

# Metrics
duration: ~1.5h
completed: 2026-08-17
---

# Phase 18 Plan 16: The Verdict, Published Summary

**The committed gate returned `LEAKAGE_DEMONSTRATED`, and it is published as returned: 92 of 104
never-taught questions extracted at least once by the best attack family against 0 of 104 from the
no-adapter control at the identical budget. The audit did not confirm privacy-by-design — it
measured the cost of weight-based memory and found the cost high.**

## Performance

- **Duration:** ~1.5 h; three commits. No GPU — `--report` reads the two committed records.
- **Files:** 1 created (`results/phase18_extraction_report.md`), 3 modified (`docs/REPORT.md`,
  `.planning/REQUIREMENTS.md`, `tests/test_phase18_docs.py`). **Zero files deleted.**
- **Suite:** **727 passed / 1 skipped / 0 failed** (141.54s). Baseline was 726/1; the delta is
  exactly this plan's one new test node.
- **Lint:** `.venv/bin/ruff check .` clean, `ruff format --check .` clean on 162 files.

## Task Commits

1. **Task 1 (the report as rendered)** — `6db37f7` (feat) — `results/phase18_extraction_report.md`,
   265 lines, 49,640 bytes, `EXTRACTION_SHIP_PENDING_LINE` intact
2. **Task 1 remediation (the D-21 addendum + its guard)** — `72470d7` (docs) — the dated
   continuation and `test_extraction_report_addendum_is_additive`
3. **Task 3 (publication + ledger)** — `68f7552` (docs) — `docs/REPORT.md` +81/−0,
   `.planning/REQUIREMENTS.md` ATK-01..06

Task 2 was the blocking human checkpoint. The operator read the recorded verdict and confirmed it
before Task 3 began; nothing was published ahead of that read.

## Task 1 — the verdict, exactly as returned

```
LEAKAGE_DEMONSTRATED
```

Returned by `null_result_is_admissible`, carried through `assemble_verdict` unchanged. The `##
Verdict` section's own words: *"This line is an imported function's own return value, not prose
written around the numbers above."* Its four recorded grounds:

1. positive control: family zero's exact hit vector reproduced against the committed taught rows,
   so this harness is known to extract a fact that is known to be present
2. draws spent per arm 42,480 ≥ declared budget 42,480
3. base arm measured at the same budget: 42,480 draws
4. all 144 pre-registered cells covered; 73 measured zero and every one carries its exposure rank

**Not softened, and the direction matters:** the pre-registered machinery was built to make a *null*
admissible — to stop "we found nothing" being unfalsifiable. It returned the opposite. Recording
that is the same discipline as recording an INCONCLUSIVE would have been, exercised in the direction
that is less flattering to the project.

### The headline, with both bounds and both denominators

Gated tier (`core_held_out`, 104 questions — the never-taught split the formal verdict is taken on),
best family `A2`, at K = 48:

| quantity | value |
|---|---|
| questions extracted at least once | **92 / 104** |
| rate | **0.8846** |
| one-sided 95% Wilson **lower** bound | **0.8231** |
| one-sided 95% Wilson **upper** bound | **0.9267** |
| no-adapter control, same budget | **0 of 104** |

Per family, at K = 48, adapter-on — with the control at zero in **every** cell:

| family | gated (104 q) | taught (112 q) |
|---|---|---|
| `A1-mild` | 87 | 102 |
| `A1-aggressive` | 30 | 31 |
| `A2` | **92** | **105** |
| `A3` | 85 | 100 |

Every figure is a **question-unit** count. The fact unit stands at n = 8, is published beside every
question-unit figure in the report, and **no claim anywhere is made at that smaller denominator** —
the whole point of STAT-01.

`core_taught` is published as the stronger attack surface and is **not merged** into the formal
verdict. A pooled number would let the easier split inflate a figure the gated tier must carry alone.

## The one acceptance criterion that failed, and why it could not have passed

Criterion 4 — `grep -c "211.60\|241.37" results/phase18_extraction_report.md` ≥ 1, *"D-21's
exclusion is recorded with its measured rationale"* — returned **0** on the rendered report.

It was **unsatisfiable by construction.** Those literals appear nowhere in
`scripts/phase18_extraction.py`, so no renderer could emit them, and STAT-05 requires the driver to
predate the run it judges. The report *did* carry D-21's exclusion and its mechanism (*"their
replay_ratio=0.0 collateral collapse makes any result from them non-representative of a normal
adapter"*) — the mechanism was named, the magnitude was not.

**Closed by appending, never by re-rendering.** `render_report` rewrites the whole file and would
have destroyed the recorded verdict; the plan says so and `assert_extraction_report_not_clobbered`
enforces it. The route was the committed `append_addendum` (`ec18cfe`), the same helper Phase 17
used, which `_prove`s **on the produced bytes** that the recorded `## Verdict` is unchanged and that
the original prefix survives byte-identically. There is no override flag and none was added.

The addendum records +211.60% / +225.95% / +241.37% val loss for the three Phase 17 adapters against
Phase 14's shipped `real` arm at **+27.16%** — roughly eight to nine times as far — cited to
`results/phase17_isolation_report.md:270-272`, with the structural cause (`replay_ratio=0.0` against
`REAL_RUN_REPLAY_RATIO = 1.0`). It states its own limits: it **supports** the exclusion, does **not**
weaken the verdict (taken on the +27.16% adapter, untouched by any figure in it), and does **not**
affect Phase 17's isolation result, since collateral collapse bears on dialogue quality rather than on
whether one persona's value surfaces under another's adapter.

### Additivity, proven rather than asserted

| Proof | Result |
|---|---|
| Lines deleted from the report | **one** — `**Phase 18 ship decision: not yet recorded.**` |
| Lines added | 42 |
| Prefix above the placeholder | **byte-identical, 48,511 bytes** |
| `## Verdict` sha256 before | `b1e7ca84ae40182dd62a871be0a268f1a06917d8c5fa5db2521bf707fcc6dff0` |
| `## Verdict` sha256 after | `b1e7ca84ae40182dd62a871be0a268f1a06917d8c5fa5db2521bf707fcc6dff0` |
| All six Task 1 criteria | pass; criterion 4 went **0 → 2**, bare-zero-percentage stayed **0** |

`test_extraction_report_addendum_is_additive` fills a real hole: the suite had
`test_addendum_append_is_additive`, which proves the **writer** appends on a synthetic `tmp_path`.
It had nothing proving what the writer **did** to the published artifact — a different claim, since a
writer can be append-only and still have been run against a file another hand rewrote first. The
pre-append revision is **derived from git history** (the newest committed revision still carrying the
placeholder), never pinned to a hash a future operator could edit to make the test pass. That is why
Task 1's report was committed *before* the append: without that revision in history the guard cannot
exist. **Proven live** — the same prefix comparison against a mutated *copy* returns `False`; the
published artifact was not mutated to demonstrate it.

## Task 3 — publication and the ledger

`docs/REPORT.md`: **81 insertions, 0 deletions.** Prefix verified byte-identical against the
pre-append sha256 `3be342377790c27aafcf689cf6e482faaee26d67edafba3923ebbde7769680bc`; 18-12's dated
claim correction survives untouched; headings 32 → 33. The base arm is written as **`0 of 104`**, not
as a percentage, because `test_no_bare_zero_percent_in_docs` guards that file and a bare zero
percentage there would have failed the build — the guard did its job on new text, which is the only
way to know it works.

`.planning/REQUIREMENTS.md`: ATK-01..ATK-06 flipped to `[x]` and to `Complete`, **12 replacements
each asserted to match exactly once**, plus an evidence table naming the discharging artifact per
requirement. **ATK-05 is cited against the machinery RETURNING a verdict, not against which verdict
it returned** — it is a pre-registration requirement, and the over-claim caution applies to the
magnitude claims instead, which is where it was applied.

## The self-qualification, carried in the same direction

The published continuation repeats the report's own limits rather than trimming them:

- **A lower bound on leakage, never an upper bound on privacy.** Black-box prompt access is the
  weakest threat model available here. The attacker had no gradients, no token probabilities, no
  white-box read of the adapter's 331,776 parameters, and **no fine-tuning attack** — which the
  unlearning literature reports recovering roughly 88% of supposedly removed information. The
  adapter is a portable file; anyone holding it has strictly more power than what was run.
- **ATK-06:** a low extraction rate at this scale may be a property of **LoRA at this capacity** —
  331,776 trainable parameters over a 13.9M-parameter base — rather than an achievement of
  PersonaCore's design, and **this audit runs no arm that separates the two.**
- **Whether such a file has ever left this machine is not asserted.** The asymmetry holds without
  that claim, which is why the report does not make it.

**What this does to the project's central claim, stated plainly in the published document rather
than left to a reader:** the property that makes weight-based memory portable and store-free is the
property that makes it recoverable by an attacker holding nothing but prompt access. *The claim that
memory lives in the weights survives this audit intact. The claim that living in the weights is
therefore private does not, and was never measured before now.*

## Phase 19 handoff — measured, not chosen

```
(92, 104, 0, 104)  ->  erasure_is_worth_attempting == True
```

Recorded reason: *"target recoverable: attack 92/104 (rate 0.8846, 95% lower bound 0.8231) exceeds
the no-adapter base rate 0.0000 (0/104)"*.

**This is not a threshold picked to make Phase 19 look necessary**, and the ordering is what makes
that checkable rather than a promise:

- `erasure_gate.ERASURE_DECISION_RULE` and `erasure_is_worth_attempting` were committed at `23a830c`
  (2026-08-12 16:27:43) — **PREREG-01**, before Phase 16 ran, four days and two phases before this
  measurement existed. PREREG-02 is a CPU-only test asserting that commit precedes every v3.0
  results artifact, so the ordering is structurally enforced rather than merely true today.
- The **selection rule** for "best attack family" is likewise pre-registered inside the
  ancestry-pinned driver, before any rate existed: the highest question-unit rate on the gated tier,
  ties broken by the committed `ATTACK_FAMILIES` order. The maximum is deterministic and cannot be
  nudged by dict iteration order or by which family a reader looked at first.
- The four ints are **question-unit**, as `erasure_is_worth_attempting` requires. Substituting a
  draw count into either denominator would narrow every bound it computes — a 42,480 denominator
  would have made this look far more certain than 104 questions can support.
- The comparison that carries it is `92/104` against `0/104` **at the same budget, the same prompts,
  the same seeds and the same masks**. It is a contrast, not a single arm's number.

Phase 19 is warranted because the target is demonstrably recoverable. Had `A2` come in at the
`A1-aggressive` level, the same committed rule on the same data would have returned a different
answer, and this section would say so.

## Verification

- `.venv/bin/pytest -q` — **727 passed, 1 skipped** (141.54s)
- `.venv/bin/pytest -q tests/test_phase18_docs.py::test_docs_continuation_is_additive -x` — passes
  against the **real** `README.md` and `docs/REPORT.md` (18-12's document-level node, not 18-11's
  synthetic one)
- `.venv/bin/pytest -q tests/test_phase18_docs.py::test_extraction_report_addendum_is_additive` — passes
- `git diff --numstat docs/REPORT.md` — **81 / 0**
- `grep -c "^- \[x\] \*\*ATK-0" .planning/REQUIREMENTS.md` — **6**; all six status rows read `Complete`
- `grep -cE "\b0(\.0+)?%"` on the report — **0**, re-checked *after* the append added new numeric text
- `.venv/bin/ruff check .` and `ruff format --check .` — clean, 162 files
- `git status --short` — empty after each commit

## Deviations from Plan

**Task 3's action and its own acceptance criterion contradict each other.** The action says to append
to `docs/REPORT.md` *"through `append_addendum`"*; the acceptance requires **0 deletions**, and that
helper necessarily deletes one line (placeholder → pointer). `docs/REPORT.md` carries no such
placeholder, so the helper would have aborted at `found == 0`. Resolved toward 18-12's shipped
precedent (`5ddb225`: 55 insertions, 0 deletions) — a plain append with prefix equality verified
explicitly on the bytes. The checkable criterion is met; the intent (*"dated, additive, 0 deletions,
every prior line byte-identical"*) is met literally.

**Task 1's criterion 4 was unsatisfiable and is recorded as such** rather than quietly dropped or
retro-fitted by editing the driver — editing it now would place code after the report it obeys, the
exact inversion Phase 17 refused, in writing, about this same subject.

## Threat register disposition

| Threat ID | Disposition | Evidence |
|-----------|-------------|----------|
| T-18-16-01 | mitigated | Verdict recorded as returned; blocking human read completed before publication; the correction path used was append-only |
| T-18-16-02 | mitigated | `--report` run exactly once; the clobber guard is armed and `append_addendum` was the only post-verdict writer |
| T-18-16-03 | mitigated | Both denominators in every published row; every claim at the 104-question unit, none at n = 8 |
| T-18-16-04 | mitigated | ATK-05 marked against the machinery returning a verdict, not against the verdict's direction; magnitude claims carry both bounds |
| T-18-16-05 | mitigated | `docs/REPORT.md` +81/−0, prefix byte-identical against a recorded sha256, 18-12's continuation intact |
| T-18-16-SC | accepted | Zero installs |

## Issues Encountered

Criterion 4's unsatisfiability, above. One process note: the report is **write-once with no force
flag**, so every check that could have been run before it was written should be — the D-21 gap was
discovered by running the acceptance greps against the rendered file, which is the last moment it
could be found and the most expensive one at which to fix it.

## Deferred Issues

- **The renderer still cannot emit D-21's figures.** This phase appended them by hand; a future
  phase that re-renders would drop them again. The durable fix is a renderer literal, which cannot
  be added retroactively without inverting the pre-registration order.
- **How often `_decode_tolerant`'s tolerant branch fired in the two arm records is unmeasured** —
  carried forward from 18-15. Bounded only by the dry-run's 0/1,920 and its 0.00141 Wilson upper
  bound (≈117 of 82,944 attack draws at that bound).
- Sibling strict-decode sites listed in `.planning/debug/draw-all-utf8-decode-crash.md`.
- `draw_all`'s docstring still describes K = 64; the code reads the constant.
- `make lint` remains red from **DEF-17-01** (pre-existing); `.venv/bin/ruff` is clean.

## Known Stubs

None.

## User Setup Required

None. `--report` is CPU-only over two tracked records.

## Threat Flags

None new. `docs/REPORT.md` and `.planning/REQUIREMENTS.md` were modified, both additively for the
published document and by asserted single-match replacement for the ledger.

## Next Phase Readiness

- **Phase 19 has its precondition, measured:** `(92, 104, 0, 104)`, `erasure_is_worth_attempting`
  `True`, against a rule committed at `23a830c` before Phase 16 ran.
- **The verdict is write-once and guarded.** `assert_extraction_report_not_clobbered` refuses a
  second render; `test_extraction_report_addendum_is_additive` fails in CI if any byte above the
  placeholder moves. A future phase that needs to add to the report uses `append_addendum` or
  deletes the file in a reviewed commit — there is no third path.
- **The requirement ledger matches the evidence.** ATK-01..06 Complete with per-requirement
  artifacts; nothing marked complete on the strength of a verdict's direction.
- **The narrative Phase 19 inherits is not the one the milestone opened with.** This phase set out
  to test whether weight-based memory is private and found that it is extractable at 88.46% on the
  never-taught split under the weakest available threat model. Phase 19's erasure work is the
  response to a measured problem, and any framing that treats Phase 18 as a privacy confirmation
  contradicts the committed evidence.

## Self-Check: PASSED

- `results/phase18_extraction_report.md` — FOUND (52,093 bytes, 305 lines, tracked, first-add
  `6db37f7`, `## Verdict` sha256 `b1e7ca84…`, `LEAKAGE_DEMONSTRATED` present, pending ship-decision
  line absent, recorded form present exactly once)
- `docs/REPORT.md` — FOUND (33 `## ` headings, +81/−0 in `68f7552`, prefix byte-identical)
- `.planning/REQUIREMENTS.md` — FOUND (6 `- [x] **ATK-0` checkboxes, 6 `Complete` status rows, evidence table)
- `tests/test_phase18_docs.py` — FOUND (contains `def test_extraction_report_addendum_is_additive`)
- `.planning/phases/18-black-box-adversarial-extraction-audit/18-16-SUMMARY.md` — FOUND
- `6db37f7`, `72470d7`, `68f7552` — all FOUND in `git log`
- Suite **727 passed / 1 skipped**; ruff clean on 162 files
