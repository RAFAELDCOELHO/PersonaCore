---
phase: quick-260922-qlm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [tests/test_phase28_prereg.py]
autonomous: true
requirements: [WR-02]
must_haves:
  truths:
    - "A commit after ce2a151 that touches results/phase25_operational_note.md makes tests/test_phase28_prereg.py RED"
    - "An UNCOMMITTED edit to the note makes the same test RED (byte-identity against the pinned blob)"
    - "A shallow clone is refused with the Phase-27 message before any ancestry question is asked"
    - "The renderer's output is unchanged: `scripts/phase28_report.py check` exits 0 and the REPORT block stays byte-identical"
  artifacts:
    - path: "tests/test_phase28_prereg.py"
      provides: "OP_NOTE_FROZEN_AT pin + _assert_frozen_at + three tests (identity, freeze, natural RED)"
      contains: "OP_NOTE_FROZEN_AT"
  key_links:
    - from: "tests/test_phase28_prereg.py"
      to: "scripts/phase28_report.py"
      via: "phase28_report.OP_NOTE (path read from the renderer, never retyped)"
      pattern: "phase28_report\\.OP_NOTE"
    - from: "tests/test_phase28_prereg.py"
      to: "git"
      via: "git log <pin>..HEAD -- <note> and git show <pin>:<note>"
      pattern: "\\.\\.HEAD"
---

<objective>
Close WR-02 (28-REVIEW.md): the frozen provenance table in docs/REPORT.md digests
`results/phase25_operational_note.md` (sha256 + bytes at `scripts/phase28_report.py:605-607`) but
nothing structurally keeps that file stable. Add an ancestry/freeze guard that pins the note at
its last touching commit `ce2a1517aca60940bcf5b798a2c23dae92d6266e` and fails on (1) any later
commit touching it and (2) any working-tree drift from the pinned blob.

Purpose: the WR-02 comment "Only FROZEN published sources are digested" becomes true by test, not
by prose. The renderer, the note, docs/REPORT.md are NOT edited (D-20 freeze).
Output: one guard in tests/test_phase28_prereg.py; one commit naming WR-02.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/28-report-the-published-null-and-milestone-close/28-REVIEW.md
@tests/test_phase28_prereg.py
@tests/test_phase16_prereg.py
@scripts/phase28_report.py

<placement_rationale>
Guard lives in `tests/test_phase28_prereg.py`, pin lives in the TEST (not the renderer):
- That file already has `_git`, `_SHALLOW_REFUSAL`, and imports `phase28_report`, so `OP_NOTE` is
  read from the renderer rather than retyped. WR-02 names this exact file as "checks ordering,
  not immutability" — the immutability half belongs beside the ordering half.
- The analogs put freeze pins in the test, not the code under test: `PREREG_COMMIT` in
  tests/test_phase16_prereg.py:49, `_PRE_COMMIT` in tests/test_phase25_close.py:55.
  `phase28_report.EXPECTATION_COMMIT` is a RENDER input (it feeds `QUOTES`); a freeze pin is not,
  and touching the renderer for a no-op constant is exactly what D-20 says not to do.
- Closest existing "unchanged since" guard: tests/test_phase25_close.py:321
  (`test_the_frontier_artifact_is_unchanged_since_its_single_write`: commit count + `git diff`).
  The note has 13 commits so a count is wrong; a `<pin>..HEAD` range log (the mechanic at
  tests/test_phase25_close.py:207) plus byte-identity to `git show <pin>:<path>` is the right form.
</placement_rationale>

<interfaces>
From tests/test_phase28_prereg.py (reuse as-is):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SHALLOW_REFUSAL = ("shallow clone: the pre-registration commit objects are absent, ...")
def _git(*args): ...  # text=True, .strip() — NOT byte-exact; do not use it for the blob
```
From scripts/phase28_report.py:72:
```python
OP_NOTE = "results/phase25_operational_note.md"
```
Measured: `git rev-parse ce2a151` = `ce2a1517aca60940bcf5b798a2c23dae92d6266e`;
`git show --stat ce2a151` touches the note (+49); `git log ce2a151..HEAD -- <note>` is empty;
`git rev-parse --is-shallow-repository` = false; CI `fetch-depth: 0` (ci.yml:28).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Freeze guard for the op note in tests/test_phase28_prereg.py</name>
  <files>tests/test_phase28_prereg.py</files>
  <behavior>
    - test_op_note_freeze_pin_is_itself_and_touches_the_note: `git log -1 --format=%H <pin>` == pin (full 40-hex, resolves to itself) AND `phase28_report.OP_NOTE in git show --stat --format= <pin>` (identity, per test_phase16_prereg.py:216-234 — a wrong pin must not degrade into a tautology)
    - test_op_note_is_frozen_at_its_pin: shallow refusal first (`_SHALLOW_REFUSAL`), then `git log --format=%H <pin>..HEAD -- <note>` is EMPTY, then `(_ROOT/note).read_bytes() == git show <pin>:<note>` bytes
    - test_a_pin_one_commit_too_early_is_red: NATURAL RED — `_assert_frozen_at(OP_NOTE_FROZEN_AT + "^", OP_NOTE)` raises AssertionError whose message names the later commit (ce2a151 itself is "after" its own parent). No planting, no file edit.
  </behavior>
  <action>
    Append a section "(3) WR-02: THE OP NOTE IS FROZEN AT ITS PIN — RANGE-LOG + BYTE-IDENTITY, SHALLOW-REFUSING" to tests/test_phase28_prereg.py, following the file's existing `# ====` banner style.

    Add module-level constant `OP_NOTE_FROZEN_AT = "ce2a1517aca60940bcf5b798a2c23dae92d6266e"` with a 3-4 line comment: full 40-hex per test_phase16_prereg.py:46-49; this is the last commit that touched the note, and the digest at scripts/phase28_report.py:605-607 was published with the note at this content; WR-02 is the cause; a sanctioned correction to the note must be a dated continuation PLUS a deliberate move of this pin in the same commit (which then also requires a re-render, which D-20 forbids — that tension is the point: the row is frozen).

    Add helper `_assert_frozen_at(commit, path)`:
    1. `assert _git("rev-parse", "--is-shallow-repository") == "false", _SHALLOW_REFUSAL` (reuse the existing constant verbatim so `test_ancestry_guard_refuses_a_shallow_clone_message_is_the_phase27_one` stays the single source).
    2. `later = _git("log", "--format=%H", f"{commit}..HEAD", "--", path).split()`; `assert not later, (f"{path} was touched after its freeze pin {commit}: {later} — WR-02: the frozen provenance row in docs/REPORT.md digests this file; move OP_NOTE_FROZEN_AT deliberately or revert")`.
    3. Pinned blob via `subprocess.run(("git", "show", f"{commit}:{path}"), cwd=_ROOT, capture_output=True, check=True).stdout` — bytes, NOT `_git` (it is text+strip, not byte-exact). `assert (_ROOT / path).read_bytes() == pinned, f"{path} in the working tree differs from its pinned blob {commit}:{path} — WR-02: uncommitted drift would change the digested sha256/bytes"`.

    Add the three tests from `<behavior>`, all using `phase28_report.OP_NOTE` (never the string literal). For the natural-RED test use `pytest.raises(AssertionError, match="touched after")`.

    Extend the module docstring by one sentence naming the new guard and WR-02.

    Gates: no `== 10` literal, no `os.replace`, no `inject_lora`/`train_arm(`/`train_never_taught` tokens anywhere in the file. Run `.venv/bin/ruff check tests/test_phase28_prereg.py && .venv/bin/ruff format tests/test_phase28_prereg.py`.
  </action>
  <verify>
    <automated>.venv/bin/pytest tests/test_phase28_prereg.py -q -p no:cacheprovider && .venv/bin/ruff check tests/test_phase28_prereg.py && .venv/bin/ruff format --check tests/test_phase28_prereg.py</automated>
  </verify>
  <done>All tests in tests/test_phase28_prereg.py pass (the 5 pre-existing + 3 new); ruff clean; `grep -c "phase25_operational_note" tests/test_phase28_prereg.py` is 0 (path comes from the renderer).</done>
</task>

<task type="auto">
  <name>Task 2: RED-then-GREEN proof, renderer unchanged, single WR-02 commit</name>
  <files>tests/test_phase28_prereg.py</files>
  <action>
    RED (uncommitted drift): `printf '\nWR-02 probe line\n' >> results/phase25_operational_note.md`, then
    `.venv/bin/pytest tests/test_phase28_prereg.py -q -p no:cacheprovider -k "frozen_at_its_pin"`.
    MUST fail with exactly one failure; the failing assertion must be the byte-identity one
    ("differs from its pinned blob") — the range-log conjunct passes because no commit was made.
    Capture the transcript for the SUMMARY.

    GREEN: `git checkout -- results/phase25_operational_note.md`; re-run the same pytest command;
    MUST pass. Then `git status --short results/` MUST print nothing. Capture the transcript.

    Renderer untouched (D-20): `.venv/bin/python scripts/phase28_report.py check` exits 0 and
    `.venv/bin/pytest tests/test_phase28_report.py -q -p no:cacheprovider -k byte_identical` passes.

    `make lint` green.

    Commit EXACTLY one file, explicit path, no `-a`:
    `git add tests/test_phase28_prereg.py && git commit -m "test(quick-260922-qlm): WR-02 — freeze results/phase25_operational_note.md at ce2a151 under an ancestry guard; the frozen provenance row now has a structural guarantee"`.
    Before staging, `git status --short` and confirm the only modified tracked path is the test
    (peer sessions edit the tree; `.claude/scheduled_tasks.lock` deletion is pre-existing — leave it).
    After the commit: `.venv/bin/pytest tests/test_phase28_prereg.py -q -p no:cacheprovider` once more (the
    range-log conjunct is now evaluated with the new commit in HEAD's history — it must still be
    empty because the commit touches only the test).
  </action>
  <verify>
    <automated>.venv/bin/python scripts/phase28_report.py check && .venv/bin/pytest tests/test_phase28_prereg.py tests/test_phase28_report.py -q -p no:cacheprovider -k "prereg or byte_identical" && test -z "$(git status --short results/)" && git log -1 --format=%s | grep -q "WR-02" && test "$(git show --stat --format= HEAD | grep -c '|')" = "1"</automated>
  </verify>
  <done>RED transcript (byte-identity assertion quoted) and GREEN transcript recorded in the SUMMARY; `git status --short results/` empty; HEAD is one commit touching only tests/test_phase28_prereg.py with WR-02 in its subject; `phase28_report.py check` exits 0; byte-identity test green.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| git history → test | The guard trusts the object DAG, not dates or prose |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-qlm-01 | Tampering | results/phase25_operational_note.md | mitigate | range-log `<pin>..HEAD` + byte-identity to the pinned blob; shallow clone refused first |
| T-qlm-02 | Repudiation | OP_NOTE_FROZEN_AT typo → tautology | mitigate | identity test: pin resolves to itself and its commit touches OP_NOTE |
| T-qlm-03 | Tampering | guard silently green | mitigate | natural RED test against `<pin>^` |
| T-qlm-SC | Tampering | package installs | accept | no installs in this plan |
</threat_model>

<verification>
- `.venv/bin/pytest tests/test_phase28_prereg.py -q` green after commit
- RED-then-GREEN transcripts in SUMMARY
- `scripts/phase28_report.py check` exit 0; docs/REPORT.md, README.md, the note, the renderer untouched (`git diff --stat HEAD~1 HEAD` lists only the test)
- Orchestrator runs the full suite once after the commit (~25 min) — not part of this plan's verify
</verification>

<success_criteria>
WR-02 closed: a later commit or an uncommitted edit to results/phase25_operational_note.md turns
tests/test_phase28_prereg.py RED with a message naming WR-02; nothing rendered changed; one commit.
</success_criteria>

<output>
Create `.planning/quick/260922-qlm-close-wr-02-ancestry-guard-for-results-p/260922-qlm-SUMMARY.md` when done
</output>
