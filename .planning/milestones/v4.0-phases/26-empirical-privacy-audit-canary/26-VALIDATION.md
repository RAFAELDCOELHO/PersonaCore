---
phase: 26
slug: empirical-privacy-audit-canary
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-10
updated: 2026-09-10
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `26-RESEARCH.md` §"Validation Architecture"; per-task map filled from the five PLAN.md files.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ~= 9.0 (`pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`) |
| **Config file** | `pyproject.toml`; `tests/conftest.py` (`SWEEP_ACTIVE_ENV_VAR = "PERSONACORE_SWEEP_ACTIVE"`) |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py` |
| **Full suite command** | `make test` (run with `PERSONACORE_SWEEP_ACTIVE=1` while the LaunchAgent runs) |
| **Estimated runtime** | quick ~10 s (the wiring test loads the 22 MB frontier once); full suite ~ several minutes (last CI 2691 passed / 62 skipped) |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py`
- **After every plan wave:** Run `make test` (`PERSONACORE_SWEEP_ACTIVE=1` while the agent runs)
- **Before `/gsd:verify-work`:** Full suite must be green AND `tests/test_phase25_close.py` still green (frontier at one commit, §O1 git-surface exception closed)
- **Max feedback latency:** 60 seconds for the quick command

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-01 T1 prereg module | 26-01 | 1 | CANARY-02 | T-26-03, T-26-09 | Rule by reference; bounds imported; int-only counts; degenerate named not clipped | unit (python -c) | `.venv/bin/python -c "...phase26_prereg checks..."` (see plan) + `ruff check scripts/phase26_prereg.py` | ❌ W1 creates | ⬜ pending |
| 26-01 T2 prereg tests | 26-01 | 1 | CANARY-01, CANARY-02 | T-26-03 | Ancestry guard (earliest add, strictly-after), phase25_prereg byte-identity, formula table, verdict domain | unit + git integration | `.venv/bin/pytest -q tests/test_phase26_prereg.py -x` | ❌ W1 creates | ⬜ pending |
| 26-02 T1 driver scoring half | 26-02 | 2 | CANARY-01 | T-26-01, T-26-02, T-26-06, T-26-07 | No top-level torch; no torch.load; charset-refused paths; sha-pinned sidecars; prove_reproduction before write | AST + unit (python -c) | `.venv/bin/python -c "...AST + _items equality..."` + `ruff check` | ❌ W2 creates | ⬜ pending |
| 26-02 T2 emit/main/plist | 26-02 | 2 | CANARY-01, CANARY-02 | T-26-03, T-26-04, T-26-05 | Write-once first; ceiling before verdicts; refusal names the note; KeepAlive false; no git argv | CLI + unit | `python scripts/phase26_canary.py --dry-run` + emit-refusal one-liner + `plutil -lint artifacts/com.personacore.phase26.canary.plist` | ❌ W2 creates | ⬜ pending |
| 26-03 T1 structural tests | 26-03 | 3 | CANARY-01 | T-26-01, T-26-05, T-26-06, T-26-07 | items equality; dry-run torch-free; sidecar refusal; emit partial refusal; git surface empty; plist mirror | unit + subprocess + AST | `.venv/bin/pytest -q tests/test_phase26_canary.py -x -k "not live_path and not routes_its_in_taught and not power_gate and not sibling and not reproduced"` | ❌ W3 creates | ⬜ pending |
| 26-03 T2 wiring proof + RED + link | 26-03 | 3 | CANARY-01, CANARY-02 | T-26-03 | main→score_off_once→score_point→emit on stubbed draws; gate before write; forged power pass RED on a copy; link both ways (both-state) | integration (needs_adapters) | `.venv/bin/pytest -q tests/test_phase26_canary.py -x` and the same under `PERSONACORE_SWEEP_ACTIVE=1` | ❌ W3 creates | ⬜ pending |
| 26-04 T1 pre-launch + kickstart | 26-04 | 4 | CANARY-02 | T-26-02, T-26-03, T-26-04 | Note first-add after every prereg commit; quoted owners; wiring proof re-run on host; agent with own caffeinate | git integration + CLI | `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py -k "prereg_is_frozen or byte_identical or operational_note" -x` + `launchctl list` | ❌ W4 creates note | ⬜ pending |
| 26-04 T2 early-run gate | 26-04 | 4 | CANARY-01 | T-26-03 | OFF sidecar; consumer refused on real records; control 790/1008 | manual (checkpoint:human-verify) — commands listed in the task | `PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/pytest -q tests/test_phase26_canary.py::test_the_control_reproduced_the_published_reading` | ✅ (26-03) | ⬜ pending |
| 26-04 T3 record §6 | 26-04 | 4 | CANARY-01 | T-26-03, T-26-05 | Quoted outputs only; note is the only file committed | prose pin + suite | `PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/pytest -q tests/test_phase26_canary.py tests/test_phase26_prereg.py -x` + `! grep -q '^## 6\..*PENDING'` + grep for `"reproduction_gate"` or `D-19 named limitation` (transcript-only markers absent at 26-04 T1) | ✅ (26-04 T1) | ⬜ pending |
| 26-05 T1 emit once / D-19 | 26-05 | 5 | CANARY-01, CANARY-02 | T-26-03, T-26-07, T-26-11 | 17 sidecars or no artifact; artifact untracked after emit; frontier one commit | integration (present-state tests) | `.venv/bin/pytest -q tests/test_phase26_canary.py tests/test_phase26_prereg.py tests/test_phase25_close.py -x` | ✅ (26-03) | ⬜ pending |
| 26-05 T2 operator commit | 26-05 | 5 | CANARY-02 | T-26-05 | Human commits; ancestry guard checks two artifacts | manual (checkpoint:human-action) | `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py` after the commit | ✅ (26-01/03) | ⬜ pending |
| 26-05 T3 machine put back | 26-05 | 5 | CANARY-01 | T-26-04 | Agent booted out; assertion owners quoted | CLI + suite | `! launchctl list \| grep -q com.personacore.phase26.canary` + `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py tests/test_phase25_close.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 is folded into Wave 1 and Wave 3 by design (the ancestry guard needs the prereg module committed before its test can pass; the driver tests need the driver):

- [ ] `tests/test_phase26_prereg.py` (26-01 T2) — CANARY-02: ancestry guard, rule resolves to `dp_n8_sigma0p000000`, extension = 15 noised `dp_n8` keys in `point_keys` order, power threshold = `epsilon_for(80.0, 200, DELTA)`, ε_lower hand-computed table, degenerate cases named, three-valued verdict domain, continuations as data
- [ ] `tests/test_phase26_canary.py` (26-03 T1-T2; heading pins appended in 26-04 T1 / 26-05 T1) — CANARY-01 / D-16 / D-18 / D-19: items builder equals `calibration_items`, OUT counts 784/504, `--dry-run` without torch, sidecar sha256 reuse/refusal, `emit()` refuses partial, live path wired end to end, control routes through `prove_reproduction`, power-gate forged pass RED, sibling link both ways, plist mirrors the recall agent, driver never commits, no `torch.load`
- [ ] `results/phase26_operational_note.md` (26-04 T1) — created strictly AFTER every prereg commit (it is the first tracked `results/phase26_*` file); carries the D-19 named limitation if the audit is cut
- Framework install: none — pytest present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LaunchAgent kickstart, assertion read-back, first heartbeat | D-16 | Needs the MPS host and `launchctl`; not reproducible in CI | 26-04 T1 records `launchctl kickstart` output, `pmset -g assertions`, first heartbeat line in `results/phase26_operational_note.md` §5 |
| OFF sidecar lands; `emit()` refuses on the real record; control prints `REPRODUCTION GATE PASSED` (790/1008) | D-15, D-17, D-19 | ~25 h MPS run; sampled ≈ 2 h in | 26-04 T2 checkpoint (six commands), 26-04 T3 quotes them in §6 |
| 16th sidecar, `--emit`, operator commit of `results/phase26_canary.json` | D-18, D-19, §O1 | Driver git surface is read-only; the operator commits | 26-05 T1 emits once, 26-05 T2 operator commits and pastes the SHA, 26-05 T3 quotes it in §8 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (the two checkpoints list the automated commands the human runs)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (26-01 T2, 26-03 T1-T2, 26-04 T1)
- [x] No watch-mode flags
- [x] Feedback latency < 60s for the quick command
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending `/gsd:plan-check`
