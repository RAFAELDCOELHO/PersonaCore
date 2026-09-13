---
phase: 26-empirical-privacy-audit-canary
reviewed: 2026-09-13T21:30:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - scripts/phase26_canary.py
  - scripts/phase26_prereg.py
  - artifacts/com.personacore.phase26.canary.plist
  - tests/test_phase26_canary.py
  - tests/test_phase26_prereg.py
  - tests/test_phase25_venue.py
  - results/phase26_operational_note.md
  - results/phase26_canary.json
findings:
  critical: 1
  warning: 7
  info: 3
  total: 11
status: issues_found
---

# Phase 26: Code Review Report

**Reviewed:** 2026-09-13T21:30:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the frozen pre-registration, the LaunchAgent-supervised driver, the plist, the three test files and the two data artifacts. Quick gate: `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py` = 43 passed; `ruff check` clean on all five Python files.

**What holds.** The epsilon_lower arithmetic is correct against the (epsilon, delta)-DP hypothesis-testing constraints: direction 1 uses `(TPR_lb - delta)/FPR_ub`, direction 2 uses `(1 - FPR_ub - delta)/(1 - TPR_lb)`, both conservative in both operands, both Wilson bounds imported by reference, `z` shared. The degenerate cases are named, never clipped; `wilson_lower_bound` returns exactly `0.0` at zero successes so direction 1 is correctly undefined at every noised point. I re-derived every one of the 15 verdicts, the auditor ceiling and the power gate from the committed artifact's own counts through `phase26_prereg` — all match bit-for-bit. Hashes cross-check: artifact sha256 `d2a71e2d…` equals the note (§8.3, §8.8a) and the committed blob at `8652c15`; `prereg_module_sha256 b524ad1a…` equals the module on disk; `frontier_bytes 22311714` matches; `emitted_git_sha c4a5511` is the commit the note names; `reachable_claims 4/15` is the set with `epsilon < 2.7859` (σ = 24, 32, 50, 80); summary sums to 15. The plist is sound: absolute paths, no shell, `RunAtLoad`/`KeepAlive` false, minimal `PATH`, the driver's only subprocess is `git rev-parse HEAD` as list argv. Resume refusal paths (adapter/base sha mismatch, missing sidecars, write-once) are real and tested. The three both-state tests do execute their PRESENT branch now that the artifact is tracked.

**What does not.** One deterministic CI failure is latent: the venue register's derived ubuntu skip count omits an in-body `pytest.skip` and is off by one; no CI run has executed any Phase-26 commit (last run 2026-09-09). Provenance is weaker than the artifact claims: the committed artifact points at gitignored sidecars by path only (no sha256, no per-sidecar instrument SHA), the 17 sidecars carry two different `instrument_git_sha` values from one process and neither is the SHA the code was loaded at, and `emit()` published `emitted_git_sha` from a dirty tree without the `refuse_if_dirty` guard the repo's other emitters use. `emit()` also trusts more of a sidecar than it proves (shape, fact-set identity between OFF and ON, the control's reproduction gate). The PRESENT-branch tests check shape and clauses but never re-derive a verdict from the artifact's counts, and no `emit()` call in the suite ever reaches the CONSISTENT/BROKEN branch.

## Critical Issues

### CR-01: The derived ubuntu skip register is off by one — CI goes red on the next push

**File:** `tests/test_phase25_venue.py:293` (with `tests/test_phase26_canary.py:314-315`)
**Issue:** `_CANARY_HOST_ONLY_SKIPS = 8  # 7 @needs_adapters + 1 @needs_plutil` misses a ninth skip: `test_emit_refuses_a_partial_audit` is not decorated but calls `pytest.skip(...)` in its body at line 315 when `_adapters_on_disk()` is false, and pytest reports an in-body skip as `skipped`. Measured on this host with `_ADAPTERS_ON_DISK` forced false (plutil present): `18 passed, 8 skipped`, the eighth being line 315. On ubuntu plutil is absent, so the file contributes 9, not 8, and `_UBUNTU_SWEEP_ACTIVE_EXPECTED_SKIPS` / `_UBUNTU_FLAG_UNSET_EXPECTED_SKIPS` (70) will be compared under `==` against 71 by `test_the_sweep_active_skip_count_is_the_number_stated_in_advance` and `test_with_the_flag_unset_the_baseline_is_unchanged`. The file's own comment says "ubuntu is DERIVED, NOT MEASURED — no CI run has executed this file yet"; `gh run list` confirms the last CI run is `76a3d0b` (2026-09-09, Phase 25).
**Fix:** Either fix the register with a dated continuation (the file's own convention) or remove the in-body skip so the derivation is decorator-only:
```python
# tests/test_phase25_venue.py — dated continuation, 2026-09-13 (review CR-01)
_CANARY_HOST_ONLY_SKIPS = 9  # ubuntu only; 7 @needs_adapters + 1 in-body pytest.skip
                             # (test_emit_refuses_a_partial_audit:315) + 1 @needs_plutil
```
or split the partial-sidecar sub-case of `test_emit_refuses_a_partial_audit` into its own `@needs_adapters` test (then the count is 8 @needs_adapters + 1 plutil = 9 and the comment becomes true by construction). Either way the number must be MEASURED on CI before the register comment claims it.

## Warnings

### WR-01: The committed artifact does not pin the sidecars it was assembled from

**File:** `scripts/phase26_canary.py:545-553`
**Issue:** Each point entry carries `"source": "data/phase26_canary_<key>.json"` — a path under gitignored `data/` — and nothing else about that file: no sha256, no `instrument_git_sha`, no `scoring_seconds`, no `device`/`torch_version`. The artifact pins the frontier in both directions and the prereg module by hash, but its own 17 inputs are unhashed and untracked, so a reader of `results/phase26_canary.json` cannot tie any reading to the sidecar that produced it. (The OFF sidecar is likewise named by path only at line 596.)
**Fix:** Pin every input at assembly. Because the artifact is write-once and already committed, this lands as a dated continuation (a sibling `results/phase26_canary_sources.json` written by a new `--pin-sources` path, or in the Phase-28 report), never a `--force` re-emit:
```python
entry = {
    ...,
    "source": _rel(sidecar_path(key)),
    "source_sha256": _sha256(sidecar_path(key)),
    "source_provenance": {k: blob[k] for k in ("instrument_git_sha", "scoring_seconds", "device", "torch_version", "utc")},
}
# and at top level:
"off_sidecar_sha256": _sha256(off),
```

### WR-02: `instrument_git_sha` names HEAD at write time, not the instrument that ran

**File:** `scripts/phase26_canary.py:223-234` (`_provenance`), consumed at 295 and 376
**Issue:** `git_sha()` is called per sidecar at write time. One driver process (pid 70302, loaded at HEAD `4c01c43`) produced sidecars carrying two different SHAs — `a7843b3` on OFF and the control, `c4a5511` on all 15 noised points (measured from the 17 files on disk) — and none of them is `4c01c43`, the tree the running code came from. The field's name asserts the instrument's identity and it is false for every sidecar. The note (§6.1) records this as "recorded, not prevented; nothing about the driver needs to change" — it should change: a per-write `git rev-parse` in a 30-hour run under an operator who is committing to the same tree is not provenance.
**Fix:** Resolve once, before anything scores, and thread it through:
```python
def main(argv=None):
    ...
    instrument_sha = git_sha()  # ONCE, at process start — the code that is actually loaded
    score_off_once(..., instrument_sha=instrument_sha)
    for key in points:
        score_point(key, ..., instrument_sha=instrument_sha)

def _provenance(device, scoring_seconds, *, instrument_sha):
    return {..., "instrument_git_sha": instrument_sha, "head_at_write": git_sha(), ...}
```

### WR-03: `emit()` publishes `emitted_git_sha` from a dirty tree — no `refuse_if_dirty`

**File:** `scripts/phase26_canary.py:613`
**Issue:** `personacore.provenance.refuse_if_dirty` exists precisely for "an emitter about to write a permanent record" and is the register at `scripts/phase21_emit.py:77`. `emit()` never calls it. The note's own §8.7 shows the tree at emit time carried ` M tests/test_phase26_canary.py`, ` M results/phase26_operational_note.md` and ` M .planning/STATE.md`, so `emitted_git_sha = c4a5511` names a commit whose tree is not the one that emitted. `prereg_module_sha256` and `frontier_sha256` are hashed from the working tree, which happened to be clean for those two paths — by luck, not by guard.
**Fix:** Refuse before assembly, with a deliberately chosen pathspec:
```python
from personacore.provenance import git_sha, refuse_if_dirty

def emit(out_path=RECORD, *, overwrite=False):
    refuse_if_dirty(
        who="phase26_canary",
        detail="emit publishes emitted_git_sha and hashes scripts/ and results/ from the working tree",
        pathspec=("scripts", "src", "results", f":(exclude){_rel(out_path)}"),
        cwd=_ROOT,
    )
    ...
```

### WR-04: `emit()` trusts sidecar shape beyond the adapter hash; the exclusion rule can be silently weakened

**File:** `scripts/phase26_canary.py:395-405, 469-494`
**Issue:** After the sha check, `emit()` never proves (a) `blob[tier]["questions"] == EXPECTED_QUESTIONS[tier]`, (b) that the OFF sidecar's `per_fact` key set equals every point's `per_fact` key set per tier, or (c) that `of` (hard-coded `56` / `8`) equals `len(off_blob[tier]["per_fact"])`. `_exclusions` iterates only the facts PRESENT in the OFF blob, so a fact missing from the OFF `per_fact` (a truncated or foreign sidecar that still carries the right `base_sha256`) is treated as "adapter-off never answered it" — the opposite of D-07's strictest reading. `_readings` at 413-417 catches a count mismatch only after exclusions and only by cardinality, not identity. `_lists()` proves the counts at scoring time, but `emit()` reads files, not `_lists()`.
**Fix:**
```python
def _prove_shape(blob, name):
    for tier in TIERS:
        _prove(blob[tier]["questions"] == EXPECTED_QUESTIONS[tier],
               f"{name}: {tier} has {blob[tier]['questions']} questions, expected {EXPECTED_QUESTIONS[tier]}")
        _prove(sum(f["n_questions"] for f in blob[tier]["per_fact"].values()) == EXPECTED_QUESTIONS[tier],
               f"{name}: {tier} per_fact n_questions do not sum to the question count")

_prove_shape(off_blob, off.name)
for key, blob in sidecars.items():
    _prove_shape(blob, key)
    for tier in TIERS:
        _prove(set(blob[tier]["per_fact"]) == set(off_blob[tier]["per_fact"]),
               f"{key}: {tier} fact set differs from the OFF sidecar's — exclusions would be computed over a different population")
in_of, out_of = len(off_blob["in_taught"]["per_fact"]), len(off_blob["out_taught"]["per_fact"])
_prove(in_of == 8 and out_of == 56, f"OFF populations {in_of}/{out_of}, expected 8/56")
out_x = _exclusions(off_blob, OUT_TIERS, out_of)
in_x = _exclusions(off_blob, IN_TIERS, in_of)
```

### WR-05: `emit()` publishes the control's reproduction gate without proving it passed

**File:** `scripts/phase26_canary.py:561`
**Issue:** `entry["reproduction_gate"] = blob.get("reproduction_gate")` — a control sidecar with the field absent, `passed: false`, or `observed != expected` is assembled into the artifact and its reading feeds the power gate unchecked. D-15 says the control's reading is trusted only AFTER reproduction; `score_point` enforces that before writing, but `emit()` reads whatever file carries the right `adapter_sha256`, and the D-15 precondition is exactly the thing the artifact should not take on faith.
**Fix:**
```python
gate = blob.get("reproduction_gate")
_prove(
    gate is not None and gate["passed"] is True
    and gate["observed"] == gate["expected"] == [phase25_prereg.REPRODUCTION_K, phase25_prereg.REPRODUCTION_N],
    f"{control}: sidecar carries no passed reproduction gate — its reading cannot be the power reading (D-15)",
)
entry["reproduction_gate"] = gate
```

### WR-06: PRESENT-branch tests never re-derive a verdict; no `emit()` in the suite reaches CONSISTENT/BROKEN

**File:** `tests/test_phase26_canary.py:595-639` and `385-518`, `563-592`
**Issue:** `test_the_sibling_is_pinned_to_the_frontier_both_ways` and `test_every_point_carries_its_reasons_and_the_ceiling_disclosure` check hashes, the presence of `reasons`, the ceiling clause and `sum(summary) == 15`. Neither recomputes `epsilon_lower`, `auditor_ceiling`, the power gate or any `verdict` from the artifact's own `members_answered / n_in / nonmembers_answered / n_out`, and the summary is never checked against the per-point verdicts. An artifact whose numbers were edited consistently in shape passes both. Separately, every `emit()` executed by the suite is fed all-zero readings (`fake_complete` returns `"answer {index}"`, which never contains a value), so the control's `epsilon_lower` is `-0.047`, the power gate FAILS, and `emit()`'s CONSISTENT/BROKEN branches (lines 563-568 with `power["passed"]` true) run only in production. `test_the_live_path_is_wired_end_to_end`'s `expected_verdict` at 485-490 is derived through the same function the driver calls, so it is tautological for the driver. I re-derived all 15 verdicts, the ceiling and the power gate by hand for this review and they match — the tests should do it every run.
**Fix:** Add to the PRESENT branch:
```python
fr = frontier
for key in phase26_prereg.noised_point_keys(fr):
    fu = blob["points"][key]["fact_unit"]
    reading = phase26_prereg.epsilon_lower(fu["members_answered"], fu["n_in"], fu["nonmembers_answered"], fu["n_out"])
    assert reading["epsilon_lower"] == fu["epsilon_lower"]
    assert phase26_prereg.point_verdict(reading, fr["points"][key]["epsilon"],
                                        power=blob["power_gate"], auditor_ceiling=blob["auditor_ceiling"]) == blob["points"][key]["verdict"]
assert phase26_prereg.auditor_ceiling(blob["n_in"], blob["n_out"]) == blob["auditor_ceiling"]
assert phase26_prereg.power_gate(blob["points"][CONTROL]["fact_unit"]["epsilon_lower"], phase26_prereg.power_threshold(fr)) == blob["power_gate"]
assert blob["summary"] == {v: sum(1 for k in noised if blob["points"][k]["verdict"]["verdict"] == v) for v in phase26_prereg.VERDICTS}
```
and give the wiring test one `fake_complete` that returns the fact's value for the control so `emit()` runs with a PASSED power gate at least once.

### WR-07: `test_emit_refuses_to_overwrite_the_committed_artifact` is vacuously green in the absent state

**File:** `tests/test_phase26_canary.py:329-338`
**Issue:** `else: pass` — with no artifact the test asserts nothing. Its two sibling both-state tests assert `not tracked` in that state; this one would go green on a checkout where the artifact was deleted but is still tracked, exactly the state the write-once guard exists to name.
**Fix:**
```python
    else:
        assert not _git("ls-files", "results/phase26_canary.json").strip(), "tracked but absent on disk"
```

## Info

### IN-01: Tautological guard after the sidecar loop

**File:** `scripts/phase26_canary.py:485-488`
**Issue:** `sidecars` is built by iterating `pinned`, so `set(sidecars) == set(pinned) and len(sidecars) == len(pinned)` cannot be false. Dead check that reads as a proof.
**Fix:** Delete it, or replace with the shape/identity proof from WR-04.

### IN-02: The dry-run reuse path imports torch to read one path constant

**File:** `scripts/phase26_canary.py:248-252`
**Issue:** When the OFF sidecar exists, `score_off_once(dry_run=True)` imports `phase14_recall` (which imports `torch` at module scope, `phase14_recall.py:60`) solely for `CONVBASE_SLIM`. The docstring's "`--dry-run` exercises every structural path without touching the device" and `test_the_dry_run_walks_off_and_sixteen_and_never_imports_torch` hold only because that test runs in an empty sidecar dir.
**Fix:** Hash `_ROOT / blob["base_path"]` exactly as `emit()` does at line 461, and drop the import.

### IN-03: Pre-registration refusals that are not `SystemExit` — for a dated continuation, never an edit

**File:** `scripts/phase26_prereg.py:245-246, 296` (frozen at `e6a8851`; ancestry-guarded)
**Issue:** `epsilon_lower` with `n_in == 0` or `n_out == 0` raises `ValueError` from the imported Wilson helpers, and `verdict(eps_lower, None)` raises `TypeError` on `>` — both contradict the module docstring's "Every refusal is `_prove` -> `SystemExit`". The driver guards both (`_prove(n_in > 0 and n_out > 0)` at 494; `point_verdict` is never called for the control), so nothing is reachable today.
**Fix:** Do not edit `phase26_prereg.py`. If Phase 28 wants the guarantee, record it in a further continuation module in the `phase21_unit_continuation.py` register, with the driver's guards named as the current enforcement.

---

_Reviewed: 2026-09-13T21:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
