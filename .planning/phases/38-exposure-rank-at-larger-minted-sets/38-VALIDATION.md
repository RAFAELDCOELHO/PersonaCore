---
phase: 38
slug: exposure-rank-at-larger-minted-sets
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-04
---

# Phase 38 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 38-RESEARCH.md §Validation Architecture, plus the plan-time rulings D-24..D-32 in 38-CONTEXT.md.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x in `.venv` (Python 3.11), CPU-only, zero skips in Phase 38 files |
| **Config file** | `pyproject.toml`; `make test` = `.venv/bin/pytest -q` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase38_*.py` (files named by the plans) |
| **Cross-phase guards** | `.venv/bin/pytest -q tests/test_phase35_prereg.py tests/test_phase36_caps.py tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase25_venue.py` |
| **Full suite command** | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + an `until grep -q '^EXIT='` waiter |
| **Estimated runtime** | quick ~1-3 min; full ~43-45 min |

---

## Sampling Rate

- **After every task commit:** quick run + the cross-phase guards.
- **After every plan wave AND after every `results/phase38_*` record commit:** full suite (records reveal latent reds — Phase 36).
- **Before `/gsd:verify-work`:** full suite green.
- **Max feedback latency:** ~180 s for the quick run.

---

## Per-Requirement Verification Map

| Req / SC | Behavior | Type | Automated command (target) | File exists |
|---|---|---|---|---|
| RANK-01 / SC1 | `e5_minting_rule` + `e5_rank_moves_and_generation_collapses` filled once in `scripts/phase38_prereg.py` via `phase35_prereg.fill`; rule text names grammar, seed `seed_list()[0]`, surface format, the 4 filters + D-27 neighbour screen (names only), D-26 global uniqueness, D-24 clearance source with report SHA-256 and parser invariants, D-25 2048 + global stop + continuation, D-31 \|R\| counts taught | unit + census | `pytest tests/test_phase38_prereg.py` | ❌ W0 |
| RANK-01 / SC1 | Generator deterministic, prefix-stable under the global stop, `random()` only (AST); numeric enumerate → exclude → clear → seeded shuffle; per-slot per-filter rejection counts (zero published as zero); every name/place slot ≥ 2048 or STOP | unit (tiny fixtures) + one real CPU run into tmp | `pytest tests/test_phase38_mint.py` | ❌ W0 |
| RANK-01 / SC1 | `e5_set_sizes` read from the minting record (never typed), ≤ 8 sets, ≤ 512, `check_unit_caps` called WITHOUT `prefixes`; the approved 8 prefixes checked against `phase38_prereg` (D-21/D-23); legs (a)/(b) | unit + ancestry | `pytest tests/test_phase38_sizes_prereg.py tests/test_phase36_caps.py` | ❌ W0 |
| RANK-02 / SC2 | New rank function ≡ `exposure_rank` at 6-8 with ties by string (property test); bits = log2(\|R\|/rank); moved (D-12/D-28), top-eighth (D-29), collapse (D-13), damage (D-14, strict >, person_name k=8 tie not damaged); before/same/after/never for both events (D-30) | unit | `pytest tests/test_phase38_prereg.py -k "rank or moved or eighth or collapse or damage"` | ❌ W0 |
| RANK-02 / SC2 | \|R\| gate: all 64 committed ranks (8 readings × 8 slots) reproduced before any minted set is scored, else STOP; SHA-256 of persona_adapter, ordered_prefix (= probe e1 `components_sha256`), M2 adapter | unit (JSON; checkpoint SHAs via monkeypatched path) | `pytest tests/test_phase38_rank.py -k "gate or sha"` | ❌ W0 |
| RANK-02 / SC2 | Driver: preflight refusals before the ledger start line, `require_launch("E5")`, live path wired end to end (one real smallest-shape run on CPU into tmp root + tmp ledger, and one real producer record fed to the report emitter) | unit + rehearsal | `pytest tests/test_phase38_rank.py -k "preflight or rehearsal or emit"` | ❌ W0 |
| RANK-03 / SC3 | `scripts/phase18_extraction.py` bytes unchanged; phase38 modules import `reference_set_for` / `value_span_nll_mean` (AST: ImportFrom/Attribute, not redefinition) | AST + bytes | `pytest tests/test_phase21_sc5.py tests/test_phase38_rank.py -k ast` | partly ✅ |
| SC4 | Prereg + its test committed before every `results/phase38_*`; records write-once (overwrite refused); committed only after Rafael's "approved" | git ancestry | `pytest tests/test_phase38_prereg.py -k "ancestry or frozen"` + `tests/test_phase35_prereg.py` | ❌ W0 |
| hygiene | torch-free prereg import (lazy `seed_list`), no `== 10` literal, no `os.replace`, no `inject_lora` outside the register, no `checkpoints/` dependency, zero skips, no grep acceptance over prose (AST gates) | census | `pytest tests/test_phase21_sc5.py tests/test_lora_inject.py tests/test_phase38_*.py` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase38_prereg.py` — ancestry, slot census, rule functions, rank/event definitions
- [ ] `tests/test_phase38_mint.py` — fixtures from the tracked Phase 17 report (runs on ubuntu)
- [ ] `tests/test_phase38_sizes_prereg.py`
- [ ] `tests/test_phase38_rank.py` — fake-model fixtures, no checkpoint dependency

No framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rafael writes "approved" before each record commit | RANK-01/02, SC4 | human gate | checkpoint task presents the record; commit only after the literal word |
| MPS scoring run | RANK-02 | device + ledger; not in CI | launch under `require_launch("E5")`; monitor; stop rule D-23 (0.5419 h) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 180 s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** plan-checker iteration 3 (final): 0 blockers, 1 warning accepted (38-07 has 4 tasks), 4 info — 3 fixed by the orchestrator (I-1, I-2, I-3, narrow-checked), I-4 accepted (38-08 Task 2 previews the disclosure by hand before launch). 2026-10-04

---

## Revision-loop finding origins

| Iteration | Finding | Origin (revision-introduced / pre-existing at HEAD) |
|---|---|---|
| 1 | BLOCKER 38-01 T1: tie example expects rank 2, `exposure_rank` gives 3 (re-verified by orchestrator) | initial |
| 1 | WARNING 38-06/07: rig lacks stand-ins for gitignored run_inputs; `_device` untested without patch (ubuntu latent red) | initial |
| 1 | WARNING 38-07 T3: verify uses unset `$T` | initial |
| 1 | WARNING RESEARCH Open Questions not marked RESOLVED (fixed by orchestrator) | initial |
| 1 | WARNING 38-01 T1 scope too large | initial |
| 1 | INFO ×5: 57,811 mislabel (plan measures 58,195), D-20 commit cite, sidecar watch, 38-08 routing, sign-off open | initial |
| 2 | All 9 iteration-1 findings resolved (checker re-measured) | — |
| 2 | BLOCKER 38-07: D-34 identity recorded last and read from the run sidecar, so a failed first rehearsal goes unrecorded (re-verified by orchestrator, 38-07 :103/:168) | revision-introduced |
| 2 | WARNING 38-01 T1: three dangling "Task 2 proves" refs after the split (one lands in the frozen file) | revision-introduced |
| 2 | WARNING 38-07 T1: emit under patched `_ROOT` runs git/module digests in a non-repo tmp dir | revision-introduced + pre-existing |
| 2 | WARNING 38-07: D-34 disclosure tracks only phase38_rank.py, though 38-08 allows sizes-file fixes | revision-introduced |
| 2 | WARNING 38-07 T1 scope grew with D-34 | revision-introduced |
| 2 | WARNING `ls <glob> 2>/dev/null` guards false-red / blind under zsh NOMATCH (38-01/03/06/07) | pre-existing |
| 2 | INFO ×5: T-38-43 "five" vs 7, 38-09 checklist lacks D-33/D-34, identity-path call + equal-sha test, identity tamper check, sign-off | 4 revision-introduced, 1 pre-existing |
| 3 | All iteration-2 findings resolved (B-1, W-1..W-5, I-1..I-4) | — |
| 3 | WARNING 38-07 has 4 auto tasks after the W-4 split (accepted) | revision-introduced |
| 3 | INFO 38-07 objective/verification said nothing written in the real tree (fixed by orchestrator) | revision-introduced |
| 3 | INFO 38-07 "reached scoring" over-approximates; fixed statement text (fixed by orchestrator: "passed preflight", statement built from slice_read) | revision-introduced |
| 3 | INFO 38-02 "Task 2 proves" in a frozen-file comment (fixed by orchestrator: named test_max_value_tokens_matches_phase17) | pre-existing |
| 3 | INFO 38-07 disclosure validated only at emit (accepted; 38-08 T2 previews by hand) | revision-introduced |
