---
phase: 26
slug: empirical-privacy-audit-canary
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-10
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `26-RESEARCH.md` §"Validation Architecture"; the planner fills the per-task map.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ~= 9.0 (`pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`) |
| **Config file** | `pyproject.toml`; `tests/conftest.py` (`SWEEP_ACTIVE_ENV_VAR = "PERSONACORE_SWEEP_ACTIVE"`) |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py` |
| **Full suite command** | `make test` (run with `PERSONACORE_SWEEP_ACTIVE=1` while the LaunchAgent runs) |
| **Estimated runtime** | quick ~10 s; full suite ~ several minutes (last CI 2691 passed / 62 skipped) |

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
| (filled by the planner from each PLAN.md task) | | | CANARY-01 / CANARY-02 | | | | | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase26_prereg.py` — CANARY-02: ancestry guard, rule resolves to `dp_n8_sigma0p000000`, extension = 15 noised `dp_n8` keys in `point_keys` order, power threshold = `epsilon_for(80.0, 200, DELTA)`, ε_lower hand-computed table, degenerate cases named, three-valued verdict domain
- [ ] `tests/test_phase26_canary.py` — CANARY-01 / D-16 / D-18 / D-19: items builder equals `calibration_items` on `LOCKED_FACTS`, OUT counts 784/504, `--dry-run` without torch, sidecar sha256 reuse/refusal, `emit()` refuses partial, power-gate forged pass goes RED, sibling link both ways, plist mirrors the recall agent, driver never commits
- [ ] `results/phase26_operational_note.md` — created at plan time with the pre-launch blocks; carries the D-19 named limitation if the audit is cut
- Framework install: none — pytest present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LaunchAgent kickstart, assertion read-back, first heartbeat | D-16 | Needs the MPS host and `launchctl`; not reproducible in CI | Record `launchctl kickstart` output, `pmset -g assertions`, first heartbeat line in `results/phase26_operational_note.md` |
| OFF sidecar lands; control prints `REPRODUCTION GATE PASSED` (790/1008) | D-15, D-17 | ~25 h MPS run; sampling points during the run | Quote the sidecar path + hash and the gate line in the operational note |
| 16th sidecar, `--emit`, operator commit of `results/phase26_canary.json` | D-18, D-19, §O1 | Driver git surface is read-only; the operator commits | Run `--emit`, run the quick tests, commit the artifact by hand, quote the commit SHA |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
