---
phase: quick-260802-h3g
plan: 01
status: complete
subsystem: phase-14 drivers / report clobber guards
tags: [CR-02, T-14-06, tdd, data-loss, evidence-protection]
requires:
  - scripts/phase14_recall.py::_recorded_verdict (the reference implementation, unmodified)
provides:
  - scripts/_verdict.py::recorded_verdict (the single anchored verdict-section read)
  - scripts/phase14_factset_gate.py::assert_report_not_clobbered (extracted, testable)
affects:
  - scripts/teach_persona.py::_refuse_clobber
  - .planning/phases/14-teach-then-recall-demo/14-SECURITY.md (UF-4, T-14-06 evidence)
tech-stack:
  added: []
  patterns:
    - "one importable copy of a guard predicate instead of five hand-copied instances"
    - "zero-arg module-level guard reading module globals + sys.argv at call time (monkeypatchable)"
key-files:
  created:
    - scripts/_verdict.py
  modified:
    - scripts/teach_persona.py
    - scripts/phase14_factset_gate.py
    - tests/test_phase14_teaching.py
    - tests/test_phase14_factset.py
    - .planning/phases/14-teach-then-recall-demo/14-SECURITY.md
decisions:
  - "phase14_recall keeps its own private _recorded_verdict copy — duplication retained deliberately to protect the T-14-17 clean-room property"
  - "the naive split(\"## Verdict\")[-1] control is KEPT in the teaching test as an intentional regression tripwire, commented so a future cleanup does not delete it"
  - "measure_inflation.py:70 and finetune_smoke.py:727 left carrying the idiom — out of scope, recorded in UF-4"
metrics:
  duration: ~35min
  completed: 2026-08-02
requirements: [T-14-06]
---

# Quick Task 260802-h3g: Anchor the Verdict-Section Clobber Guard Summary

Killed the `split("## Verdict")[-1]` idiom at the two remaining in-scope sites and left ONE
importable copy of the anchored regex (`scripts/_verdict.py`), so the next guard cannot
reintroduce CR-02 by copy-paste.

## What Changed

**`scripts/_verdict.py` (new, 30 lines, imports only `re`).** `VERDICT_SECTION` +
`recorded_verdict(text)` — the body of the FIRST `## Verdict` section, `None` when the file has
no such section. The docstring records why five copies of this read is what produced CR-02, and
why `None` and an empty body are deliberately different.

**`scripts/teach_persona.py`.** `_refuse_clobber` (now `:1137-1154`) reads
`recorded_verdict(...)` and refuses on `recorded is None or "PENDING" not in recorded`. Signature
`(report_path, force)` unchanged; both callers (`:1124`, `:1512`) untouched; the `SystemExit`
message text is byte-identical.

**`scripts/phase14_factset_gate.py`.** The inline block at the top of `main()` is now
module-level `assert_report_not_clobbered()` (`:116-137`), zero-arg, reading `REPORT_PATH` and
`sys.argv` at call time — which is what makes it monkeypatchable. `main()`'s first statement is
a call to it (`:141`), not a copy. Message text byte-identical, `--force` semantics unchanged.
This extraction is the reason the defect survived the first CR-02 fix at all: inline in `main()`,
the guard was unreachable from any test without a 278 MB checkpoint and an MPS device.

## TDD — RED first, actually run

Both tests were written and executed against the **unmodified** naive-split guards before any
production code was touched. The transcript below is the real pytest output, captured by
restoring the pre-fix scripts from the Task-1 commit (`f16ce64`) and re-running:

```
FF                                                                       [100%]
=================================== FAILURES ===================================
______ test_refuse_clobber_reads_the_verdict_section_not_the_last_mention ______

tmp_path = PosixPath('/private/var/folders/7k/hgktxwvx6p54ch16qtg7pwlw0000gn/T/pytest-of-juliorcoelho/pytest-523/test_refuse_clobber_reads_the_0')

    def test_refuse_clobber_reads_the_verdict_section_not_the_last_mention(tmp_path):
        """CR-02, second site: the clobber guard must anchor on the verdict SECTION.

        The fixture is the real report shape — a PENDING verdict followed by a ``## Ship Decision``
        section whose D-12 comment QUOTES the heading (``phase14_recall.SHIP_DECISION_HEADER``). The
        old ``split("## Verdict")[-1]`` took the tail after the LAST occurrence of that literal, which
        lands in the ship-decision prose and never contains ``PENDING`` — so the guard fired on every
        legitimate re-drive of an interrupted run and ``--force`` (which disables the guard entirely)
        became the only way through. An operator who learns ``--force`` is always required passes it
        after a human HAS recorded a verdict, and the guard then destroys the hand-written evidence it
        exists to protect. That is the data-loss path this test closes.
        """
        report = tmp_path / "phase14_calibration_report.md"
        text = (
            "# Phase 14 Calibration Report\n\n"
            "## Verdict\n\n"
            "PENDING — user decision at checkpoint.\n\n"
            "## Ship Decision\n\n"
            "<!-- D-12, verbatim: a missed threshold is recorded UNAMENDED in\n"
            "`## Verdict` above. Any subsequent decision is logged HERE. -->\n\n"
            "_No post-verdict decision recorded._\n"
        )
        report.write_text(text, encoding="utf-8")

        # INTENTIONAL CONTROL — do not delete in a future cleanup. This is the defect itself, kept
        # beside the fix: the naive tail lands in the ship-decision prose, which never says PENDING.
        # A regression back to `split("## Verdict")[-1]` fails HERE, with the reason written next to it.
        assert "PENDING" not in text.split("## Verdict")[-1]

        # The anchored read sees the real section instead.
        assert "PENDING" in vd.recorded_verdict(text)

        # The legitimate re-drive: an interrupted run must be re-drivable WITHOUT --force.
>       tp._refuse_clobber(report, False)

tests/test_phase14_teaching.py:595:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

report_path = PosixPath('/private/var/folders/7k/hgktxwvx6p54ch16qtg7pwlw0000gn/T/pytest-of-juliorcoelho/pytest-523/test_refuse_clobber_reads_the_0/phase14_calibration_report.md')
force = False

    def _refuse_clobber(report_path, force):
        """The ``measure_inflation.py:66-75`` guard: a RECORDED verdict is committed evidence.

        A rerun would reset ``## Verdict`` to PENDING and silently drop whatever the human wrote
        beside it. ``--force`` is the only way past.
        """
        if report_path.exists() and not force:
            recorded = report_path.read_text(encoding="utf-8").split("## Verdict")[-1]
            if "PENDING" not in recorded:
>               raise SystemExit(
                    f"[teach_persona] {report_path} already carries a recorded verdict — it is "
                    "committed evidence (D-09). Pass --force to overwrite and re-measure."
                )
E               SystemExit: [teach_persona] /private/var/folders/7k/hgktxwvx6p54ch16qtg7pwlw0000gn/T/pytest-of-juliorcoelho/pytest-523/test_refuse_clobber_reads_the_0/phase14_calibration_report.md already carries a recorded verdict — it is committed evidence (D-09). Pass --force to overwrite and re-measure.

scripts/teach_persona.py:1145: SystemExit
______________ test_gate_clobber_guard_reads_the_verdict_section _______________

tmp_path = PosixPath('/private/var/folders/7k/hgktxwvx6p54ch16qtg7pwlw0000gn/T/pytest-of-juliorcoelho/pytest-523/test_gate_clobber_guard_reads_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10fe35090>

    def test_gate_clobber_guard_reads_the_verdict_section(tmp_path, monkeypatch):
        """CR-02, third site: the D-06 gate's clobber guard, anchored and finally reachable.

        It used to live inline at the top of ``main()``, so no test could reach it without a 278 MB
        checkpoint and an MPS device — which is why the same ``split("## Verdict")[-1]`` defect
        survived here after ``phase14_recall`` was fixed. Extracted to a module-level function, it is
        exercised with nothing but a ``tmp_path`` file: no checkpoint load, no device, no probes.

        The naive-tail control lives once, in ``tests/test_phase14_teaching.py``; this mirrors the
        ``phase14_recall`` proof at ``tests/test_phase14_scoring.py:617`` for the gate's own guard.
        """
        gate = _load("phase14_factset_gate")
        report = tmp_path / "phase14_factset_report.md"
        monkeypatch.setattr(gate, "REPORT_PATH", report)
        monkeypatch.setattr(sys, "argv", ["phase14_factset_gate.py"])

        text = (
            "# Phase 14 Fact-Set Pre-Flight Report\n\n"
            "## Verdict\n\n"
            "PENDING — user decision at checkpoint.\n\n"
            "## Close-Call Rejections\n\n"
            "Recorded beside the verdict; see `## Verdict` above for the D-06 decision itself.\n"
        )
        report.write_text(text, encoding="utf-8")
>       gate.assert_report_not_clobbered()  # the legitimate re-drive — must not need --force
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: module 'phase14_factset_gate' has no attribute 'assert_report_not_clobbered'

tests/test_phase14_factset.py:177: AttributeError
=========================== short test summary info ============================
FAILED tests/test_phase14_teaching.py::test_refuse_clobber_reads_the_verdict_section_not_the_last_mention
FAILED tests/test_phase14_factset.py::test_gate_clobber_guard_reads_the_verdict_section
2 failed in 0.67s
```

Both failures are exactly the ones the plan pre-registered, which is the point of stating them up
front: a `SystemExit` on the **legitimate re-drive** for `teach_persona` (the behavioural proof of
the defect — the guard refusing a PENDING report because the tail landed in the ship-decision
prose), and an `AttributeError` for the gate (the honest RED for an extraction — the guard did not
exist as a callable). Note the naive control on line `assert "PENDING" not in
text.split("## Verdict")[-1]` **passed** during RED: it asserts the broken behaviour deliberately,
which is what makes it a tripwire against a regression back to the split form.

GREEN, after applying the two fixes:

```
........................................                                 [100%]
40 passed in 0.92s
```

## Verification

`make lint` from a clean tree:

```
ruff check . && ruff format --check .
All checks passed!
133 files already formatted
```

`make test` — the FULL CPU-only suite, not just the phase-14 files (T-14-17 clean-room tests
`test_no_fact_strings_at_import` and `test_demo_process_is_fact_free` included):

```
392 passed, 1 skipped, 83 warnings in 113.08s (0:01:53)
```

The 1 skip is pre-existing and unrelated to this task.

Static gates, all run:

```
naive idiom gone from both in-scope files
out-of-scope sites untouched (gate has teeth)
recall untouched
no status/disposition drift
right symbols named
line refs in range
register table + frontmatter byte-identical
```

`git diff --name-only b7079ac..HEAD` lists exactly the six files in `files_modified` — no
`phase14_recall.py`, no `measure_inflation.py`, no `finetune_smoke.py`, no `14-0*-PLAN.md`.

## 14-SECURITY.md — what was corrected and what was already right

**Already correct, left untouched (recorded here rather than edited for the sake of a diff):**

- **UF-2** (`:608-613`) already says the T-14-12 build-time guard is `scripts/teach_persona.py:361-371`,
  proof 6 of `sanity_check`, and already explains the `build_arm_bins:415-416` back-to-back call.
- **UF-3** (`:615-620`) already says T-14-17 is **six** function-scoped import sites at
  `:628, 734, 783, 882, 1054, 1695`, not one in `main()`.
- The **T-14-12 evidence bullet** (`:232-235`) already names `sanity_check` explicitly.
- The **T-14-17 evidence block** (`:288-290`) already lists all six line numbers.
- The **closing approval summary** already named `sanity_check` and "six lazy-import sites".

The wrong names originate in the plan-authored registers (`14-04-PLAN.md:461` "in `build_bins`";
`14-05-PLAN.md:103,139` "inside `main()`"). Those are pre-registration evidence and were **not
edited**, per the constraint. Their symbol names are therefore still stale — deliberately so; the
SECURITY.md unresolved findings are where the correction lives.

**Actually changed (descriptions only):**

1. **T-14-06 evidence block** — refs updated to the real post-change lines
   (`phase14_factset_gate.py:116-137` called `:141`; `teach_persona.py:1137-1154` called `:1124`,
   `:1512`), `scripts/_verdict.py:24,27` named as the shared source, the "refuses a file with no
   verdict section" property recorded, the two new tests added to the test list, and the reason
   `phase14_recall` keeps a private copy stated inline. Status stays `closed`.
2. **UF-4** — rewritten from "still use the unanchored tail form" to the post-fix state: both
   phase-14 sites anchored, both now refusing a no-verdict-section file, the fix driven RED-first,
   the finding kept and still non-blocking, T-14-06 not reopened, and the two out-of-scope
   Phase-12/13 sites named as still carrying the idiom.
3. **Approval summary UF-4 clause** — one clause appended so it matches the rewritten finding.

No threat status, disposition, evidence verdict, or the `threats_open: 0` frontmatter changed —
verified mechanically: the register table rows and frontmatter diff **byte-identical**, and the
`| closed` count matches `HEAD` exactly.

## Deliberate non-goals (still carrying the naive idiom)

- **`scripts/measure_inflation.py:70`** (Phase 13) — still `split("## Verdict")[-1]`. Out of scope.
- **`scripts/finetune_smoke.py:727`** (Phase 12) — still `split("## Verdict")[-1]`. Out of scope.

Both are latent in exactly the same way: harmless while their reports mention `## Verdict` once,
a rerun-refusal false positive the moment either grows a second mention. Recorded in UF-4.

- **`scripts/phase14_recall.py`** keeps its own private `_recorded_verdict` copy. The duplication
  is retained **on purpose** to protect the T-14-17 clean-room property: the demo asserts
  `phase14_factset` / `teach_persona` are absent from a fresh demo process, which is why recall
  deliberately uses six function-scoped imports rather than module-level ones. Adding a
  module-level sibling import there would put a non-package name into `phase14_recall`'s import
  path for no behavioural gain. Its `_recorded_verdict` is already correct and is referenced by
  name in a passing test (`tests/test_phase14_scoring.py:638,641,650`).

## Deviations from Plan

None — plan executed as written. One mechanical detail the plan left open:
`tests/test_phase14_factset.py` had no generic `_load` helper (only a hardcoded `_load_factset`),
so it was generalized to `_load(name)` matching `tests/test_phase14_teaching.py`'s shape rather
than adding a second loader, per the plan's "do not add a second loader" instruction. The gate is
loaded **inside** the test rather than at module scope so the file's docstring claim that its
importlib load "runs nothing" and imports no torch stays true at collection time.

## Commits

- `f16ce64` — `feat(quick-260802-h3g): add scripts/_verdict.py — the single anchored verdict-section read`
- `2b8ed33` — `fix(quick-260802-h3g): anchor the clobber guard on the verdict SECTION at both remaining sites`
- `a39b753` — `docs(quick-260802-h3g): record the post-fix state in 14-SECURITY.md (descriptions only)`

## Threat Flags

None. `scripts/_verdict.py` imports only `re`, holds no fact values, and opens no new network,
auth, file-access, or schema surface. Zero packages added, installed, or upgraded —
`pyproject.toml` and `requirements.txt` untouched (T-14-SC).

## Self-Check: PASSED

- `scripts/_verdict.py` — FOUND
- `scripts/phase14_factset_gate.py::assert_report_not_clobbered` — FOUND (`:116`)
- `tests/test_phase14_teaching.py::test_refuse_clobber_reads_the_verdict_section_not_the_last_mention` — FOUND (`:562`)
- `tests/test_phase14_factset.py::test_gate_clobber_guard_reads_the_verdict_section` — FOUND (`:153`)
- Commits `f16ce64`, `2b8ed33`, `a39b753` — all FOUND in `git log`
