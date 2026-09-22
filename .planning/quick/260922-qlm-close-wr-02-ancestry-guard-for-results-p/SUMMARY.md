---
phase: quick-260922-qlm
plan: 01
status: complete
subsystem: tests / provenance guards
tags: [WR-02, ancestry-guard, freeze, phase28]
requires: [28-REVIEW.md WR-02, scripts/phase28_report.py OP_NOTE]
provides: [OP_NOTE_FROZEN_AT pin, _assert_frozen_at, 3 tests in tests/test_phase28_prereg.py]
affects: [tests/test_phase28_prereg.py]
key-files:
  created: []
  modified: [tests/test_phase28_prereg.py]
decisions:
  - "Freeze pin lives in the test, not the renderer (D-20 freeze; analog PREREG_COMMIT in test_phase16_prereg.py)"
  - "Guard = range-log <pin>..HEAD (empty) + byte-identity to `git show <pin>:<path>`; shallow refusal first, reusing _SHALLOW_REFUSAL verbatim"
  - "Natural RED against <pin>^ instead of planting — no residue for the planted-bit / from-import censuses"
commit: a4971cb
metrics:
  duration: ~10 min
  completed: 2026-09-22
  tasks: 2/2
---

# Quick 260922-qlm: Close WR-02 — ancestry guard for results/phase25_operational_note.md Summary

`results/phase25_operational_note.md` (digested sha256+bytes into the frozen provenance table of
docs/REPORT.md) is now frozen by test at `ce2a1517aca60940bcf5b798a2c23dae92d6266e`: any later
commit touching it, or any uncommitted working-tree drift, turns `tests/test_phase28_prereg.py`
RED with a message naming WR-02. Renderer, note, REPORT.md untouched (D-20).

## Commit

- `a4971cb` `test(quick-260922-qlm): WR-02 — freeze results/phase25_operational_note.md at ce2a151 under an ancestry guard; the frozen provenance row now has a structural guarantee`
- `git show --stat HEAD`: `tests/test_phase28_prereg.py | 59 ++++` — 1 file changed.

## What was added (tests/test_phase28_prereg.py)

- Docstring: one paragraph naming WR-02 and the freeze.
- `OP_NOTE_FROZEN_AT = "ce2a1517aca60940bcf5b798a2c23dae92d6266e"` — written from `git rev-parse ce2a151` output (resolves to itself; touches the note, +49).
- `_assert_frozen_at(commit, path)`: shallow refusal (`_SHALLOW_REFUSAL`) → `git log --format=%H <pin>..HEAD -- <path>` must be empty → `(_ROOT/path).read_bytes() == git show <pin>:<path>` (subprocess bytes, not `_git`).
- `test_op_note_freeze_pin_is_itself_and_touches_the_note` (len 40, resolves to itself, `phase28_report.OP_NOTE in git show --stat`)
- `test_op_note_is_frozen_at_its_pin`
- `test_a_pin_one_commit_too_early_is_red` (natural RED against `<pin>^`, `match="touched after"`)
- `grep -c "phase25_operational_note" tests/test_phase28_prereg.py` = 0 — path comes from `phase28_report.OP_NOTE`.

## RED-then-GREEN transcripts (verbatim)

Step 1 — fresh guard, nothing planted:

```
$ .venv/bin/pytest tests/test_phase28_prereg.py -q -p no:cacheprovider
........                                                                 [100%]
8 passed in 9.53s
```

Step 2 — RED, uncommitted drift (`printf '\nWR-02 probe line\n' >> results/phase25_operational_note.md`):

```
$ .venv/bin/pytest tests/test_phase28_prereg.py -q -p no:cacheprovider -k "frozen_at_its_pin"
            f"{path} in the working tree differs from its pinned blob {commit}:{path} — WR-02: "
E       AssertionError: results/phase25_operational_note.md in the working tree differs from its pinned blob ce2a1517aca60940bcf5b798a2c23dae92d6266e:results/phase25_operational_note.md — WR-02: uncommitted drift would change the digested sha256/bytes
tests/test_phase28_prereg.py:164: AssertionError
1 failed, 7 deselected in 0.24s
```

Exactly one failure; the byte-identity conjunct (the range-log conjunct passed — no commit was made).

Step 3 — GREEN after `git checkout -- results/phase25_operational_note.md`:

```
$ .venv/bin/pytest tests/test_phase28_prereg.py -q -p no:cacheprovider -k "frozen_at_its_pin"
1 passed, 7 deselected in 0.20s
```

Natural RED against `<pin>^` (the message the third test matches on):

```
AssertionError: results/phase25_operational_note.md was touched after its freeze pin ce2a1517aca60940bcf5b798a2c23dae92d6266e^: ['ce2a1517aca60940bcf5b798a2c23dae92d6266e'] — WR-02: the frozen provenance row in docs/REPORT.md digests this file; move OP_NOTE_FROZEN_AT deliberately or revert
```

Step 4 — clean tree before staging:

```
$ git status --short results/ tests/
 M tests/test_phase28_prereg.py
```

## Post-commit verification

- `.venv/bin/python scripts/phase28_report.py check` → exit 0 (renderer/REPORT unchanged).
- `make lint` → `All checks passed!` / `288 files already formatted`.
- `.venv/bin/pytest tests/test_phase28_report.py tests/test_phase28_prereg.py -q -p no:cacheprovider` → `32 passed in 11.78s` (range-log conjunct re-evaluated with a4971cb in history: still empty).
- `git status --short results/` → empty.
- Gate greps (`== 10`, `os.replace`, `inject_lora`, `train_arm(`, `train_never_taught`) → no matches in the file.
- Full suite NOT run here — orchestrator runs it once.

## Deviations from Plan

None — plan executed as written.

## Self-Check: PASSED

- tests/test_phase28_prereg.py exists and contains `OP_NOTE_FROZEN_AT`.
- Commit a4971cb in `git log`.
