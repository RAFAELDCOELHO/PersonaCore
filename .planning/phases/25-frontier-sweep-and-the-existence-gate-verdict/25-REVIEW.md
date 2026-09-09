---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
reviewed: 2026-09-09T18:03:39Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - scripts/phase25_interior_log.py
  - scripts/phase25_promotion.py
  - scripts/phase25_recall.py
  - scripts/phase25_record.py
  - tests/test_phase25_close.py
  - tests/test_phase25_frontier.py
  - tests/test_phase25_interior.py
  - tests/test_phase25_promotion.py
  - tests/test_phase25_recall.py
  - tests/test_phase25_venue.py
findings:
  critical: 1
  warning: 4
  info: 10
  total: 15
status: issues_found
---

# Phase 25: Code Review Report

**Reviewed:** 2026-09-09T18:03:39Z (HEAD 2191ee6, diff base 799aa18, plans 25-17 to 25-20)
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Four scripts (the interior log emitter, the recall driver, the promotion pass, and the write-once
frontier assembly appended to `phase25_record.py`) and six test files. Every Critical and Warning
below was checked by running the one command that would confirm it; the outcome is stated on each.

Things checked that did NOT reproduce as defects (recorded so they are not re-raised):
the frontier's recorded digests for `phase25_promotion.json`, `phase25_recall.json`,
`phase23_never_taught.json` and `phase21_multiplicity.json` all MATCH the live bytes, as does
`verdicts.source_sha256`; the recall artifact's `emitted_git_sha` (4841f00) is the direct parent
of its own commit with nothing under `scripts/` moved in between, so there is no 21-REVIEW CR-02
class drift; heartbeat stamps are tz-aware so `find_kills`'s datetime arithmetic is sound; the run
had 2 kills on distinct points so the pairing assumption in `find_kills` (IN-04) did not bite; the
five non-venue test files pass locally (622 passed, 3 skipped, 7 s).

The one Critical is a CI-reliability defect: `tests/test_phase25_recall.py` depends on a macOS-only
binary and on gitignored adapters with no guard, CI runs on ubuntu-latest, `main` is 91 commits
ahead of `origin/main`, and the last CI run (2026-09-07T12:40Z) predates every file in this
review — so the "confirmed by CI" claim written into `test_phase25_venue.py` on 2026-09-09 has
no run behind it. The Warnings are about the two CPU artifacts being overwritable in place with
no refusal while the frontier pins their digests, a broad `except SystemExit` that would record
any structural failure as a "refusal", a published governs string that misdescribes the lot rule
for 32 of 44 points, and retyped numbers in published prose with no write-time assertion.

## Structural Findings (fallow)

No structural pre-pass was provided.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `tests/test_phase25_recall.py` fails on ubuntu CI — `plutil` and gitignored adapters with no guard; the "confirmed by CI" claim has no CI run behind it

**File:** `tests/test_phase25_recall.py:207` (plutil), `:63-76`, `:119-125`, `:135`, `:140`, `:152` (adapter hashes / `score_point`); `tests/test_phase25_venue.py:215-217` (the claim)
**Issue:** Six tests hard-depend on the developer's machine:

- `test_the_recall_agent_does_not_start_itself_and_lints` calls `subprocess.run(["plutil", ...])`. `plutil` does not exist on Linux; `subprocess.run` raises `FileNotFoundError` before any assertion.
- `test_every_adapter_is_on_disk_and_hashes_to_its_record`, `test_the_dry_run_walks_all_44_and_scores_none`, `test_a_matching_sidecar_is_reused`, `test_a_sidecar_for_a_different_adapter_is_refused`, `test_a_control_is_never_rescored_even_with_no_sidecar` and the subprocess in `test_the_dry_run_and_reuse_paths_never_import_torch` all reach `score_point`, whose first `_prove` is `adapter.exists()`. `checkpoints/` is gitignored (`git ls-files checkpoints` → 0 files), so on a clone every one of these exits with `SystemExit: ... adapter ... is not on disk`.

`.github/workflows/ci.yml` runs `pytest -q` on `ubuntu-latest` on every push. `main` is 91 commits ahead of `origin/main`; the newest CI run is `2026-09-07T12:40:47Z`, before `test_phase25_recall.py` (2026-09-08 07:21) or any other file in this review existed. Yet `tests/test_phase25_venue.py:215-217` (added 2026-09-09) states the ubuntu skip counts "55 / 55 (DERIVED from the same three artifact-gated skips, confirmed by CI)". No such confirmation exists, and the next push will be red — and once these tests are guarded with skips, the ubuntu pin will be wrong by exactly the number of newly skipped tests, so the pinned-integer mechanism that file protects has already drifted.

The sibling test in scope already shows the right idiom (`tests/test_phase25_close.py:315-318` branches on `sys.platform` / `shutil.which("pmset")`).

**Confirmed:** `env PATH=$(mktemp -d) .venv/bin/python -m pytest tests/test_phase25_recall.py::test_the_recall_agent_does_not_start_itself_and_lints` → `FileNotFoundError: [Errno 2] No such file or directory: 'plutil'`, 1 failed. Simulating a clone (`_ROOT` pointed at a temp dir with only `results/` linked) → `score_point("dp_n8_sigma0p500000", dry_run=True)` raises `SystemExit: [phase25_recall] dp_n8_sigma0p500000: adapter checkpoints/phase25_sigma0p500000_dp_n8_adapter.pt is not on disk`.
**Fix:**
```python
# tests/test_phase25_recall.py — one module-level guard for the adapter-bound tests, one for plutil
import shutil

_ADAPTERS_ON_DISK = all(
    (_ROOT / recall.point_record(k)["adapter_path"]).exists() for k in _KEYS
)
needs_adapters = pytest.mark.skipif(
    not _ADAPTERS_ON_DISK,
    reason="the 44 sweep adapters live under gitignored checkpoints/ — present only on the sweep host",
)
needs_plutil = pytest.mark.skipif(shutil.which("plutil") is None, reason="plutil is macOS-only")

@needs_adapters
def test_the_dry_run_walks_all_44_and_scores_none(...): ...
# (same marker on the other five adapter-bound tests; @needs_plutil on the lint test)
```
Then in `tests/test_phase25_venue.py` add the new skips to the ubuntu pins as a dated continuation (e.g. `_UBUNTU_* = 52 + 3 + _RECALL_HOST_ONLY_SKIPS`), delete the words "confirmed by CI", and push so an actual run measures the number before it is pinned.

## Warnings

### WR-01: `phase25_promotion.build()` and `phase25_recall.emit()` overwrite committed, downstream-pinned artifacts in place with no refusal and no dirty-tree check

**File:** `scripts/phase25_promotion.py:516,520-521`; `scripts/phase25_recall.py:267,284-285`
**Issue:** Both writers call `phase25_run.atomic_write_json(RECORD, blob)` unconditionally. Neither runs `refuse_existing_artifacts` nor `refuse_if_dirty`, yet both publish `emitted_git_sha`, and the frontier pins both files' bytes (`provenance.inputs.promotion_record.sha256`, `provenance.inputs.recall_record.sha256`, `verdicts.source_sha256`). The promotion module's own prose invites a re-run ("reversible in seconds by re-running this CPU pass", `:463`); doing so rewrites `results/phase25_promotion.json` with a new `emitted_git_sha`, silently desynchronising it from the committed frontier. This is the exact write discipline `phase25_record._write` and `_DIRTY_DETAIL` (`:1035-1043`) enforce for the frontier, applied to neither of its two inputs. No test guards the digest chain: `grep -rn "promotion_record\|recall_record\|source_sha256" tests/` finds only `test_phase25_probe2.py`'s unrelated check; `test_phase25_frontier.py::test_the_artifact_carries_the_pre_registered_commitments` asserts the 44 point-record digests only.
**Confirmed:** Both files have exactly one commit each and the frontier's recorded digests currently MATCH the live bytes — the defect is latent, not yet realised. `promotion.py:520` `if __name__ == "__main__": b = build()` has no guard by inspection.
**Fix:**
```python
# scripts/phase25_promotion.py (and the same three lines in phase25_recall.emit)
def build():
    _prove(not RECORD.exists(), f"{RECORD} exists — delete it in its own commit, then re-run")
    refuse_if_dirty(who="phase25_promotion", detail=..., pathspec=("scripts", "src", "results"), cwd=_ROOT)
    ...
```
and in `tests/test_phase25_frontier.py` add one assertion that `provenance.inputs.promotion_record.sha256`, `provenance.inputs.recall_record.sha256` and `verdicts.source_sha256` equal `hashlib.sha256(...)` of the live files, so the chain reddens if either input is ever rewritten.

### WR-02: `curve_pass` catches every `SystemExit` from `curve_verdicts` and records it as a "refusal", so a structural bug becomes six REFUSED verdicts with `promote: False`

**File:** `scripts/phase25_promotion.py:270-276`
**Issue:** `except SystemExit as refusal: refusals[leg] = str(refusal)` wraps the whole `verdict.curve_verdicts(...)` call. That function raises `SystemExit` for at least nine distinct `_prove` failures (`phase25_verdict.py:534-577`: unknown arm, capacity matching zero or two legs, empty leg, a record missing `POINT_RECORD_FIELDS`, `prove_control_gap_not_borrowed` firing, missing control leg, missing `CONTROL_READING_FIELDS`, plus everything downstream of `never_taught_anchors()`). Only one of those is the sanctioned route's pre-pin refusal the docstring describes. Any other would be written into the artifact under `leg_refusals` and `early_return_reason: "REFUSED by the sanctioned route before the pin was reached"`, `promote: False`, and the run would exit 0. The artifact then carries a misattributed cause for a null result — the failure class this phase's own D-34 prose calls the worst available.
**Confirmed:** The recorded refusal is the intended one (`tests/test_phase25_promotion.py::test_the_adv_n64_refusal_fires_live_on_the_recorded_inputs` reproduces it and asserts `"Y_heldout=0.0"` in the message). The breadth is by inspection of the two files; no run was needed.
**Fix:**
```python
except SystemExit as refusal:
    text = str(refusal)
    _prove(
        "Y_heldout=" in text and "corrected_point_verdict" in text,  # the route's own refusal shape
        f"{leg}: curve_verdicts exited for a reason that is not the sanctioned route's refusal: {text}",
    )
    refusals[leg] = text
```
(Better still: have `phase20_gate_coverage` raise a distinguishable subclass or carry a marker constant, and match on that.)

### WR-03: `MECHANISM_PIN_DISCLOSURE_GOVERNS` (published in the frontier) states a lot formula that the code does not apply to 32 of the 44 points

**File:** `scripts/phase25_record.py:1084-1096` (the governs string), `:1258-1270` (`_lot_from_train_config`), `:1560-1565` (the error message)
**Issue:** The governs string says the lot "is RE-DERIVED here for all 44 points from the record's own `training.train_config` (`batch_size x max(1, grad_accum_steps)`)". `_lot_from_train_config` applies that formula only on the adversarial arm; on DP it returns `n_facts` after proving `grad_accum_steps == n_facts`. `LOT_RULE_BY_ARM` beside it is accurate, but the governs string is the sentence a reader of `results/phase25_frontier.json::mechanism_pin_disclosure.governs` sees first, and it is wrong for every DP point. The `mechanism_pin_disclosure` refusal message (`:1562-1564`) has the same defect: on a DP mismatch it would print `!= batch_size x max(1, grad_accum_steps) = {lot}` where `lot` is `n_facts`.
**Confirmed:** By inspection of the three sites; the artifact carries the string verbatim (`assemble()` at `:1663`).
**Fix:** Reword the governs string to "re-derived here for all 44 points by the arm's rule in `lot_rule_by_arm` (DP: `n_facts`, asserted equal to `grad_accum_steps`; adversarial: `batch_size x max(1, grad_accum_steps)`)", and make the refusal message name `LOT_RULE_BY_ARM[rule]` rather than the adversarial formula. The frontier is write-once, so this lands on the next sanctioned re-assembly; record the discrepancy in the operational note until then.

### WR-04: Retyped numbers in published prose with no write-time assertion against the computed values beside them

**File:** `scripts/phase25_promotion.py:451` (`"n_questions": 416`), `:457-466` (`amended_criterion`: "38 of 44", "6", "0/648", "3-66 of 416"), `:484-491` (`pre_registered_null.statement`: "519.6981942303134"), `:504-509` (`dp_recall_disclosure.finding`: "0/1008", "0/648", "519.698")
**Issue:** Each of these literals sits next to the value it describes (`records[...]["epsilon"]`, `refused_points`, `recall_counts`) but is not derived from it or proved equal to it. The module invites re-runs (WR-01), and a re-run against changed inputs would rewrite the numbers and leave the prose stale — a fabricated-looking mismatch inside the one artifact whose stated purpose is "every number's source is named". `n_questions=416` is also fed into `tolerance_report` upstream via `extraction_ceiling_and_tolerance`, so the literal here is a second copy of a value the records already carry.
**Confirmed:** The literals match today (`test_phase25_promotion.py` asserts 519.6981942303134, [0,1008], [0,648], 38/6). The defect is that nothing at write time guarantees it.
**Fix:**
```python
n_questions = {f["point_extraction_questions"] for f in ...}  # prove len == 1, use it
eps05 = records["dp_n8_sigma0p500000"]["epsilon"]
"statement": f"epsilon is {eps05!r} at sigma=0.5 and condition (a) is ZERO TOLERANCE: ...",
_prove(len(refused) == 6 and len(verdicts) - len(refused) == 38, ...)  # before the amended_criterion text
```

## Info

### IN-01: Unused parameter `whole_curve` in `pin_kwargs_for`

**File:** `scripts/phase25_promotion.py:220,278`
**Issue:** The parameter is accepted and passed but never read; the docstring implies it is recorded here, while the recording actually happens in `curve_pass` (`:283`).
**Fix:** Drop the parameter, or use it and delete the duplicate at `:283`.

### IN-02: `parse_sweep_log` collects per-launch `commits` that nothing consumes

**File:** `scripts/phase25_interior_log.py:55,114,136-138`
**Issue:** `_COMMIT_RE` and `cur["commits"]` are populated and never read; `find_kills` and `build()` use `pid`, `done`, `reused_*` only.
**Fix:** Delete the regex and the dict, or cross-check them against `commit_times` (which would be a real assertion).

### IN-03: Dead proof and an unexplained 1.0 h threshold in `transcribe_stalls`

**File:** `scripts/phase25_interior_log.py:275,297`
**Issue:** `_prove(all_beats[-1]["utc"] == last_beat, "unreachable")` compares a value with itself. `if window_hours < 1.0:` decides whether `commits_inside_the_window` is populated or `None`; the 75.8 h pre-launch stall gets `None`, the seven ~0.1 h ones get lists, and the reason for the cut is not stated anywhere.
**Fix:** Remove the tautology; name the threshold (`_COMMIT_WINDOW_MAX_HOURS = 1.0` with a one-line reason) or always populate the list.

### IN-04: `find_kills` misattributes when one point is killed twice

**File:** `scripts/phase25_interior_log.py:190-196,212-216`
**Issue:** The walk-back for `shape_started` crosses any earlier `draw_index` reset in the same cell, and `resumed_by_launch` is always the LAST launch whose DONE names the point — both wrong for a second kill of the same (point, shape). Not triggered in this run (confirmed: 2 kills, distinct points).
**Fix:** Stop the walk-back at the previous reset, and pair each kill with the first launch banner after its `last_heartbeat.utc`; or document the single-kill-per-point assumption with a `_prove` on it.

### IN-05: `_measure_sidecar_device` respells a path `phase25_points.measure_sidecar` already owns

**File:** `scripts/phase25_recall.py:188-192`
**Issue:** `SIDECAR_DIR / f"phase25_{point_key}_measure.json"` re-derives `phase25_points.measure_sidecar(point_key)` (`scripts/phase25_points.py:265-266`) — the "two derivations of one path" this phase's own docstrings (`phase25_record.py:115-118`) warn against.
**Fix:** `import phase25_points` (CPU-safe at import per its own docstring) and call `phase25_points.measure_sidecar(point_key)`.

### IN-06: Tautological `_prove` in `attach_recall`

**File:** `scripts/phase25_record.py:1305-1308`
**Issue:** `entry["source"] == ("point_record" if source == "point_record" else entry["source"])` reduces to `x == x` on the sidecar branch; only the control branch is checked.
**Fix:** `_prove((entry["source"] == "point_record") == (source == "point_record"), ...)`.

### IN-07: The "torch-free" assembly requires torch to be installed

**File:** `scripts/phase25_record.py:1620`
**Issue:** `importlib.metadata.version("torch")` raises `PackageNotFoundError` on an environment without torch, contradicting `provenance.device` ("the assembly imports no torch") one line above.
**Fix:** Wrap in `try/except importlib.metadata.PackageNotFoundError` and record `None` with a note.

### IN-08: Vacuous final assertion and two deliberate tripwire tests

**File:** `tests/test_phase25_promotion.py:162` and `:277-284`
**Issue:** `assert promoted == set() or promoted == candidates` is always true after the preceding `assert promoted == candidates`. The two `skipif`-gated tests that `raise AssertionError("unreachable ...")` will fail, not skip, the day a candidate exists — intended as tripwires, but there is no comment saying so at the test site (only in the venue file's dated continuation).
**Fix:** Delete the redundant line; add a one-line docstring on each tripwire naming what must be written when it fires.

### IN-09: Substring `"rate"` match in the interior test — the false-RED class the frontier test already corrected

**File:** `tests/test_phase25_interior.py:184`
**Issue:** `"rate" in k.lower()` flags any key containing the substring (`tolerated`, `generated`, ...). `tests/test_phase25_frontier.py:58-59` already replaced this with a whole-token match and documents why (RPT-02).
**Fix:** Reuse `_is_rate_key` from the frontier test (or move it to `scripts/_prose.py`).

### IN-10: Line-number citations into a gitignored log

**File:** `scripts/phase25_promotion.py:75-78`
**Issue:** `ADVERSARIAL_NO_REPLAY` cites `logs/phase25_sweep.out:140`, `:14`, `:70`. `logs/` is gitignored (`.gitignore:16`), so the citations are unverifiable from a clone and the artifact's stated source is a file the recorded commit does not contain.
**Fix:** Quote the three lines verbatim (as `log_line` already does for one) and cite the sidecar/record field that carries `replay_windows`, or commit an excerpt under `results/`.

---

_Reviewed: 2026-09-09T18:03:39Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
