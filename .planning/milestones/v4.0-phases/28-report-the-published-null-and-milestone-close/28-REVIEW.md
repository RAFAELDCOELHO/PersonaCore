---
phase: 28-report-the-published-null-and-milestone-close
reviewed: 2026-09-22T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - README.md
  - docs/REPORT.md
  - results/phase28_ledger.json
  - scripts/phase16_persistence.py
  - scripts/phase28_glance.md.tmpl
  - scripts/phase28_report.md.tmpl
  - scripts/phase28_report.py
  - src/personacore/evaluation/perplexity.py
  - tests/test_package.py
  - tests/test_perplexity.py
  - tests/test_phase16_driver.py
  - tests/test_phase25_correction.py
  - tests/test_phase25_venue.py
  - tests/test_phase28_ledger.py
  - tests/test_phase28_prereg.py
  - tests/test_phase28_report.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 28: Code Review Report

**Reviewed:** 2026-09-22
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the diff `62fd5db..HEAD` across the renderer (`scripts/phase28_report.py`), its two templates, the disposition ledger, the three new Phase 28 test files, and the small edits to `perplexity.py`, `phase16_persistence.py` and four pre-existing test files. Verified directly: `README.md` and `docs/REPORT.md` changed by pure additions inside their sentinel pairs (numstat 19/0 and 283/0); `scripts/phase28_report.py check` exits 0; `tests/test_phase28_report.py`, `tests/test_phase28_prereg.py`, `tests/test_phase28_ledger.py`, `tests/test_package.py`, `tests/test_phase25_correction.py` and the two new single tests all pass in `.venv`; the `_github_anchor` rule is byte-identical to `tests/test_phase15_docs.py:368` and the branch value (`null-at-both-capacities`) has no underscore so the README deep link resolves; no stray unbraced `$` exists in either template.

No Critical defects were found. The four Warnings are all about guards that can pass vacuously or a freeze that the code does not itself enforce:

1. `write` replaces an already-published block in place; D-20's "write never runs again" is discipline, not code.
2. The frozen provenance table digests `results/phase25_operational_note.md`, a file under no ancestry guard and edited three times on 2026-09-09; the project's own correction route (a dated continuation) would redden byte-identity permanently.
3. The ledger's FIXED-row commit check takes the first 7+ hex-char token, which any decimal run id also matches.
4. The new `test_phase16_driver.py` test executes a whole test module to assert `isinstance(len(x), int)`, which cannot fail.

## Warnings

### WR-01: `write` has no post-publish refusal — a present sentinel pair is silently replaced

**File:** `scripts/phase28_report.py:745-749`, `scripts/phase28_report.py:806-808`
**Issue:** The module docstring and `install()` both say the path is "PRE-PUBLISH ONLY (D-20)", and the ROADMAP row pinned in `tests/test_phase25_correction.py` records "write never runs again; append_addendum is the only route". But when `n_begin == 1` the code takes the replace-in-place branch and rewrites the frozen span. Nothing in the module or the tests refuses. Worse, `test_report_block_is_byte_identical` compares the committed span against a *fresh* render, so a drifted re-`write` lands green: the guard detects drift only while `write` has not been re-run, which is exactly the case it was meant to catch.
**Fix:** Make `write` refuse once the pair exists; keep `install`'s replace branch only for an explicit, separately-named pre-publish path if one is still needed.
```python
# in main(), before the two install() calls
_prove(
    _span(REPORT_PATH, REPORT_STEM) is None and _span(README_PATH, GLANCE_STEM) is None,
    "write refused: the blocks are already installed (D-20 — corrections are dated "
    "continuations through scripts/_addendum.py; `check` is the only post-publish verb)",
)
```

### WR-02: The frozen provenance table digests a source that is not frozen

**File:** `scripts/phase28_report.py:605-607` (and the slice at `:158`)
**Issue:** `_sources()` appends sha256 + byte length of `results/phase25_operational_note.md` into the published table. The comment says "Only FROZEN published sources are digested", but that file is under no ancestry guard: `V3_ARTIFACT_GLOBS` covers `phase16_*`..`phase19_*` only, and `tests/test_phase28_prereg.py` checks first-add *ordering*, not immutability. `git log` shows the note edited three times on 2026-09-09, and this repository's sanctioned correction route is appending a dated continuation to exactly such `.md` files. The first continuation appended to the note changes its sha/bytes, `check` and `test_report_block_is_byte_identical` go permanently RED, and WR-01's freeze (correctly) forbids the re-render that would fix it. The `.planning` files were exempted from digesting for precisely this reason (lines 602-604); the op note was not.
**Fix:** Digest the note at the same pinned revision its slice is proved from, reusing the `git:` mechanism `_source_text` already has, so the row is stable by construction:
```python
# QUOTES/SLICES already support "git:<sha>:<path>"; do the same for the digest rows
for source in (f"git:{OP_NOTE_COMMIT}:{OP_NOTE}", EXTRACTION_REPORT, ERASURE_REPORT):
    raw = _source_bytes(source)  # git show --binary via subprocess for git: sources
    rows.append((source, hashlib.sha256(raw).hexdigest(), len(raw), "—"))
```
(or, ponytail rung 1: drop the op-note digest row and keep only the verbatim-slice proof, which already runs at every render).

### WR-03: FIXED-row commit resolution takes the first hex-looking token, which decimal run ids also match

**File:** `tests/test_phase28_ledger.py:38`, `tests/test_phase28_ledger.py:73-75`
**Issue:** `_SHA = r"\b[0-9a-f]{7,40}\b"` matches any 7+ run of decimal digits (e.g. a CI run id `35770563251`, a byte count, a node-id line number run). `_fixed_violations` then resolves only `shas[0]`: if a decimal token precedes the real SHA in `evidence`, the row is reported "no resolvable commit sha" (false RED); if a 7-digit decimal run happens to be a valid abbreviated object prefix, the row passes on an unrelated object (false GREEN). `tests/test_phase28_report.py:49` already carries the correct pattern (`(?=[0-9a-f]*[a-f])`), so the two guards disagree about what a SHA is.
**Fix:**
```python
_SHA = re.compile(r"\b(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b")
...
shas = _SHA.findall(row["evidence"])
if not any(_git("cat-file", "-e", f"{s}^{{commit}}").returncode == 0 for s in shas):
    failures.append((row["id"], "no resolvable commit sha", row["evidence"]))
```

### WR-04: New driver test executes a whole test module to make an assertion that cannot fail

**File:** `tests/test_phase16_driver.py:1818-1829`
**Issue:** `test_overwrite_statement_docstring_does_not_type_the_allowlist_size` loads `tests/test_phase14_scoring.py` via `spec_from_file_location` + `exec_module`, running that module's entire top level (imports, `sys.path` mutation, any module-scope setup) as a side effect inside another test, and then asserts `isinstance(len(module.PERSONA_ALLOWLIST), int) and len(...) >= 1`. `len()` always returns an `int`, and a non-empty allowlist is already the loaded module's own guard, so the second half of the test is green by construction; the docstring's claim "the count is read from the allowlist, never from prose" is not checked against anything. The first two asserts (the docstring string checks) are the whole test.
**Fix:** Delete the module exec and the vacuous assert; keep the two string asserts. If a cross-check is wanted, compare the count the D-21 guard asserts (read from `test_phase14_scoring.py` by AST, the mechanic `tests/test_phase25_correction.py::_called_names` already uses) against `len(driver.PERSONA_ALLOWLIST)`, not against `int`.

## Info

### IN-01: The rewritten `perplexity` docstring keeps an unreachable invariant and understates the true one

**File:** `src/personacore/evaluation/perplexity.py:11-16`, `tests/test_perplexity.py:145-147`
**Issue:** The loop is `for i in range(0, n - 1, block_size)`, so every visited window has at least 2 tokens and `chunk.numel() < 2` at line 65 (and line 125) is dead code; the trailing single token in `test_partial_window` is excluded by the `range` bound, not by the `numel` check the test comment credits. Consequently the denominator is `corpus_len - 1` for *every* corpus with `n >= 2`, not only "for a cleanly tiling corpus" — the D-32 correction is narrower than the truth and still documents a skip that never executes.
**Fix:** State "the denominator is `corpus_len - 1` for any corpus of at least two tokens (token 0 is the only unscored token)"; either drop the `numel < 2` bullet or note that the `range` upper bound already excludes the dangling token.

### IN-02: `check()` reports a duplicated sentinel as "absent (pre-publish state)"

**File:** `scripts/phase28_report.py:773-775`, `scripts/phase28_report.py:786-788`
**Issue:** `_span` returns `None` for any count other than exactly one, so a doubled BEGIN or END (the ambiguous case `install` refuses loudly) is diagnosed by `check` as the pre-publish state. Exit code is right; the message sends the operator to the wrong fix.
**Fix:** Return the counts from `_span` (or raise via `_prove` as `install` does) and print "sentinels occur N/M times" when either count is not 1.

### IN-03: `_fmt`'s `KeyError("unrenderable")` loses the placeholder name

**File:** `scripts/phase28_report.py:203`, `scripts/phase28_report.py:679-681`
**Issue:** A `None`/dict/nested-list value under a record path surfaces from `string.Template.substitute` as `KeyError: 'unrenderable'` with no indication of which `${...}` binding produced it; every other miss in `Bindings.__getitem__` carries the key.
**Fix:** In `__getitem__`, wrap the `_fmt(...)` calls: `except KeyError: raise KeyError(f"{key}: unrenderable value") from None`.

### IN-04: The ledger `bytes` column check is a tautology

**File:** `tests/test_phase28_report.py:300-301`
**Issue:** For the ledger row, `want_size = phase28_report.ledger_frozen_bytes(records["ledger"])` — the same function the renderer used to produce the cell — so the size column can only fail on a rendering bug, not on a wrong frozen view. The sha column is recomputed independently (line 294-297); the size column is not. The byte-identity test against the committed span is what actually pins the published `49057`.
**Fix:** Recompute in the test with an inline `json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False) + "\n"` over a `close.ci_run = None` copy, mirroring how the sha side is recomputed, so the two implementations must agree.

---

_Reviewed: 2026-09-22_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
