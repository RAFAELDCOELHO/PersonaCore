---
phase: 26
slug: empirical-privacy-audit-canary
status: verified
threats_open: 0
threats_total_rows: 27
threats_distinct_ids: 12
asvs_level: 1
created: 2026-09-13
audited_at_head: 0b169fb
---

# Phase 26 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (`register_authored_at_plan_time: true`). This document
> **verifies** the declared mitigations exist in implemented code. It does **not** scan for
> new threats.

**Gate status: CLOSED.** `threats_open: 0`. 27 register rows across 5 plans, **12 distinct
threat IDs**, every row resolved to `closed` or to a logged accepted risk. Six accepted-risk rows
(AR-26-01 … AR-26-06); three of them (AR-26-04 … AR-26-06) are **residuals** the 2026-09-13 code
review (`26-REVIEW.md` WR-02 … WR-05) surfaced under threats otherwise closed — logged here so
they cannot resurface unclassified, and correctable only by dated continuation, never by `--force`
or by editing the frozen pre-registration.

---

## Boundary of this audit — read this first

What was done (auditor: gsd-security-auditor, State B from the plan-time register, HEAD `0b169fb`):

- All 5 `<threat_model>` blocks extracted from `26-01-PLAN.md` … `26-05-PLAN.md` — 27 rows,
  12 distinct IDs (T-26-01 … T-26-11, T-26-SC). IDs recur across plans by design (the same threat
  re-declared per plan with that plan's control); rows keyed on (threat_id, component).
- Every `mitigate` row traced to a named symbol, plist key, test or git fact at HEAD, with the
  file:line quoted in the register. Named guard tests re-run individually → **19 passed**; the
  phase gate `pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py
  tests/test_phase25_close.py -x` → **69 passed in 3.87s** (`PERSONACORE_SWEEP_ACTIVE` unset).
- Git facts measured, not quoted: `scripts/phase26_prereg.py` at exactly one commit `e6a8851`;
  `results/phase26_operational_note.md` first-add `4c01c43`; `results/phase26_canary.json`
  first-add `8652c15` (author Rafael, the operator, 1 file / 1 insertion, sole commit touching it);
  `git merge-base --is-ancestor e6a8851 {4c01c43, 8652c15}` both true;
  `results/phase25_frontier.json` at exactly one commit `4030d0e`, `frontier_sha256 1f182b40…`
  equals the on-disk hash; `prereg_module_sha256` in the artifact equals the on-disk `b524ad1a…`.
- Live machine: `launchctl list | grep -i phase26` → empty. `data/` and `logs/` gitignored
  (`.gitignore:17`, `:16`; `git check-ignore` confirmed).
- `git log df256d3..HEAD -- pyproject.toml requirements.txt` → 0 commits (T-26-SC).

What was **not** done:

- `--emit` was not run (write-once; the artifact is committed); no LaunchAgent was loaded.
- No new-threat scan; the full suite was not re-run here (measured green at `8652c15`:
  2792 passed / 4 skipped / 0 failed, recorded in `26-05-SUMMARY.md`).
- 26-REVIEW CR-01 (the ubuntu venue skip-count off by one) is a CI-correctness defect, not a
  threat, and is not classified here.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| `results/phase25_frontier.json` → `phase26_prereg` | Committed artifact read as data; pinned by sha256 and single commit | 16 point keys, 16 `adapter_sha256`, published ε claims |
| git history → ancestry guard | Ordering proof relies on a non-shallow clone | commit graph |
| `checkpoints/*.pt` → driver | Untrusted pickle bytes cross into torch only via `load_adapted_model` (`weights_only=True`) | adapter + base weights |
| `data/` sidecars → `emit` | Gitignored run-time JSON re-read after kills/restarts; pinned by sha256 to the frontier's adapters | per-tier counts, per-fact k/n, provenance |
| CLI argv (`--points`) → sidecar paths | Key-derived filesystem paths | 16 literal keys |
| launchd → driver | Unattended ≈ 25 h (measured 30 h 43 min) process on `main` | process lifetime, caffeinate assertions |
| tests → driver | Tests stub only the model and the draw primitive; scoring rule, hashing and writes stay real | fakes |
| operator console → launchd | Plist copied to `~/Library/LaunchAgents`, kickstarted by hand; absolute paths, minimal PATH | plist |
| running agent → repo | Writes only gitignored `data/` and `logs/`; reads `checkpoints/` and the frontier | sidecars, logs |
| peer sessions → working tree | A `git checkout` by another session changes `git_sha()` in later sidecars — recorded, not prevented | `instrument_git_sha` |
| `data/` sidecars → `results/phase26_canary.json` | 17 gitignored records become one committed artifact through `emit` only | verdict artifact |
| operator → git | The only write to git in the run's lifetime is the operator's commit of the artifact | one commit |
| `results/phase26_canary.json` → Phase 28 | Downstream may quote ε only beside its verdict (D-40 continuation) | published numbers |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (verified at HEAD `0b169fb`) | Status |
|-----------|----------|-----------|-------------|------------------------------------------|--------|
| T-26-01 | Tampering | checkpoint deserialisation | mitigate | Driver loads weights only via `pr.load_adapted_model` (`scripts/phase26_canary.py:274`, `:337`) → `load_slim`/`load_adapter` → `torch.load(..., weights_only=True)` (`src/personacore/checkpoint.py:244`, `:296`); `grep torch.load` on the driver empty; AST test `test_the_driver_never_calls_torch_load_directly` (`tests/test_phase26_canary.py:238-248`) PASSED | closed |
| T-26-02 | Tampering / DoS | sidecar + artifact writes on kill; run killed by sleep/jetsam | mitigate | All three writes via `phase25_run.atomic_write_json` (`phase26_canary.py:297`, `:377`, `:617`; helper `scripts/phase25_run.py:118-143`: temp-in-dest-dir, fsync, `os.replace`); `caffeinate -dims` is the plist's argv[0..1] (`artifacts/com.personacore.phase26.canary.plist:28-29`); resume-by-hash `:314-322` / `:247-257`; `test_a_matching_sidecar_is_reused` PASSED | closed |
| T-26-03 | Repudiation | pre-registration frozen | mitigate | `scripts/phase26_prereg.py` at one commit `e6a8851`; ancestry test `tests/test_phase26_prereg.py:51-92` (strict ancestor, same-commit refusal, `checked == prereg × tracked` = 2) PASSED | closed |
| T-26-03 | Repudiation | post-hoc favourable reading | mitigate | `emit` order: write-once `_prove` (`:441-446`) → OFF exists (`:454-459`) → 16 sidecars (`:469-475`) → exclusions (`:491-494`) → ceiling (`:503`) → power gate (`:520`) → verdicts (`:563`); `--force` the only overwrite path (`:634`, `:642`); `prereg_module_sha256` (`:597`) equals on-disk; `test_the_power_gate_goes_red_on_a_forged_pass` (`:564-592`, on a copy) PASSED | closed |
| T-26-03 | Repudiation | partial / favourable assembly | mitigate | `test_emit_refuses_a_partial_audit` (`:307-326`) and `test_emit_refuses_to_overwrite_the_committed_artifact` PASSED; Branch B path (D-19) not taken — 17 sidecars existed | closed |
| T-26-03 | Repudiation | note authored after the fact | mitigate | Note first-add `4c01c43` is a strict descendant of `e6a8851`; heading register `test_the_operational_note_carries_every_required_block` (`:657-675`) PASSED — residual AR-26-06 (headings pinned, not quotedness) | closed |
| T-26-03 | Repudiation | `emitted_git_sha` / `instrument_git_sha` | mitigate | Pre-registration property holds via in-artifact sha256 pins (prereg, frontier, adapters) — residual AR-26-04: `emit` does not call `provenance.refuse_if_dirty` (`src/personacore/provenance.py:47`), so `emitted_git_sha = c4a5511` (`:613`) was taken on a dirty tree; `_provenance` calls `git_sha()` per write (`:229`), 17 sidecars carry two SHAs | closed |
| T-26-04 | Tampering | supervisor re-entering a point | mitigate | Plist `KeepAlive false` (`:20-21`), `RunAtLoad false` (`:23-24`), asserted by `test_the_canary_agent_mirrors_the_recall_agent` (`:358-359`) PASSED; watcher `scripts/phase25_watch.py` imports no `subprocess` (`:42`), `FORBIDDEN_ACTIONS` (`:430`); live `launchctl list \| grep -i phase26` → empty (note §8.8) | closed |
| T-26-05 | Elevation | driver git surface | mitigate | No `"git"`/`subprocess` in the driver, only `from personacore.provenance import git_sha` (`:59`); AST test `test_the_driver_never_commits` (`:341-352`, planted `push` RED on a copy) PASSED; artifact first-add exactly `8652c15` by the operator | closed |
| T-26-06 | Tampering | key-derived paths | mitigate | `sidecar_path` (`:93-96`) → `phase25_prereg.point_record_path` charset `_prove` (`scripts/phase25_prereg.py:286-293`); `point_record` (`:109-115`) proves membership in `audited_point_keys` (`phase26_prereg.py:119-132`); `--points` reaches `point_record` via `score_point` → `_prove_host_adapter` (`:311`, `:212`); `test_sidecar_paths_refuse_a_path_separator` PASSED | closed |
| T-26-07 | Spoofing | sidecar from other weights reused / assembled | mitigate | Reuse refusals `:316-320` (adapter) and `:251-255` (OFF base vs live); `emit` re-checks OFF base (`:461-467`) and all 16 adapters against the frontier (`:479-483`); `_prove_host_adapter` hashes the adapter on disk (`:210-220`); `test_a_sidecar_for_a_different_adapter_is_refused` PASSED; PRESENT-branch link test (`:595-618`) PASSED — residual AR-26-05 | closed |
| T-26-08 | Information disclosure | sidecars / artifact | accept | Control sidecar `per_fact` entries carry only `{answered_questions, k, member, n, n_questions}`; fact ids already published 9900× in the frontier; `data/` gitignored (`.gitignore:17`) — AR-26-01 | closed |
| T-26-09 | Tampering | Wilson bounds / z | mitigate | `Z = erasure_gate._Z_ONE_SIDED_95` (`phase26_prereg.py:211`); bounds imported by reference (`:245-246`); `_prove_count` int-only, bool excluded (`:218-224`); `test_epsilon_lower_matches_the_hand_computed_table` (6 rows) and `test_counts_are_ints_only` PASSED | closed |
| T-26-10 | Information disclosure | logs/ | accept | `logs/` gitignored (`.gitignore:16`); `logs/phase26_canary.out` = 87 counter lines, no prompt text, no secret-pattern hits; `.err` = two MallocStackLogging notices — AR-26-02 | closed |
| T-26-11 | Tampering | frontier re-emitted with the verdict | mitigate | `results/phase25_frontier.json` at one commit `4030d0e`, `git diff` empty, artifact `frontier_sha256` equals on-disk; `test_the_frontier_artifact_is_unchanged_since_its_single_write` (`tests/test_phase25_close.py:321-324`) PASSED; driver writes only `RECORD` (`:61`) | closed |
| T-26-SC | Tampering | package installs | accept | `git log df256d3..HEAD -- pyproject.toml requirements.txt` → 0 commits; driver top-level imports stdlib + sibling scripts + `personacore.provenance` (`:35-59`), torch lazy — `test_the_driver_imports_no_torch_touching_module_at_top_level` PASSED — AR-26-03 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Open

None.

---

## Findings

- **S-1 (WARNING, documentation).** `26-03-SUMMARY.md`, `26-04-SUMMARY.md` and `26-05-SUMMARY.md`
  carry no `## Threat Flags` section. The rows those plans introduced (T-26-08, T-26-10, T-26-11)
  are in the consolidated register above and verified, so nothing is unmapped — but the executor's
  "no new surface" attestation is absent for three of five plans.
- **S-2 (residual, T-26-03).** `emit` publishes `emitted_git_sha` without `refuse_if_dirty`, and
  note §8.7 records a dirty tree at emit time; the sidecars' `instrument_git_sha` is read per write.
  The pre-registration guarantee rests on in-artifact sha256 pins and single commits, not on these
  SHA fields, so the threat stays closed with the field's weakness named (AR-26-04).
- **S-3 (residual, T-26-07 / T-26-03).** `emit` proves adapter/base hashes but not per-tier
  question counts or OFF-vs-ON fact-set identity, and publishes `reproduction_gate` without a
  `_prove`; the current control is scoring-time enforcement (`:365-375`), and the control sidecar
  measured `{'passed': True, 'observed': [790, 1008]}` today (AR-26-05).
- **S-4 (residual, T-26-03).** The note test pins headings, not that each block is a quoted
  command output (AR-26-06).

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-26-01 | T-26-08 | Sidecars/artifact carry published fact ids and counts only; no completions, no PII; `data/` gitignored | orchestrator (secure-phase 26) | 2026-09-13 |
| AR-26-02 | T-26-10 | Gitignored logs carry counters only (measured: 87 lines, no prompt text) | orchestrator (secure-phase 26) | 2026-09-13 |
| AR-26-03 | T-26-SC | Zero installs over the phase, measured on `pyproject.toml` / `requirements.txt` | orchestrator (secure-phase 26) | 2026-09-13 |
| AR-26-04 | T-26-03 | `emitted_git_sha` taken on a dirty tree (`phase26_canary.py:613`, no `refuse_if_dirty`); per-write `instrument_git_sha` (`:229`) → two SHAs across 17 sidecars (26-REVIEW WR-02/WR-03). Guarantee rests on sha256 pins. Correct by dated continuation; never `--force` | orchestrator (secure-phase 26) | 2026-09-13 |
| AR-26-05 | T-26-07 / T-26-03 | `emit` trusts sidecar shape / fact-set and publishes `reproduction_gate` unchecked (`:395-405`, `:561`; 26-REVIEW WR-04/WR-05); scoring-time enforcement is the current control | orchestrator (secure-phase 26) | 2026-09-13 |
| AR-26-06 | T-26-03 | Note test pins headings, not quotedness of blocks (`tests/test_phase26_canary.py:657-675`) | orchestrator (secure-phase 26) | 2026-09-13 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total (rows / ids) | Closed | Open | Accepted | Run By |
|------------|----------------------------|--------|------|----------|--------|
| 2026-09-13 | 27 / 12 | 27 | 0 | 6 rows | `/gsd:secure-phase 26` — gsd-security-auditor, State B (create) from plan-time register, HEAD `0b169fb` |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-13
