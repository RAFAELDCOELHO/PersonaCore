---
phase: 11
slug: conversational-data-pipeline
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-31
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_dialogue_parse.py tests/test_dialogue_serialize.py tests/test_masked_batch.py -x -q` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the quick run command above
- **After every plan wave:** Run `make test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| parse + fixture | 11-01 T1 | 1 | DATA-01 | T-11-03 | parser hard-fails on malformed lines | unit | `.venv/bin/python -m pytest tests/test_dialogue_parse.py -x -q` | ✅ exists | ✅ green |
| detok/render/encode+mask | 11-01 T2 | 1 | DATA-02 | — | ids from LOCKED registry, never retyped | unit | `.venv/bin/python -m pytest tests/test_dialogue_serialize.py tests/test_dialogue_parse.py -x -q` | ✅ exists | ✅ green |
| get_batch_memmap_masked | 11-02 T1 | 1 | DATA-03 | T-11-04 | length-alignment raise | unit (tdd) | `.venv/bin/python -m pytest tests/test_masked_batch.py -x -q` | ✅ exists | ✅ green |
| fetch + checksum | 11-03 T1 | 2 | DATA-01 | T-11-01, T-11-02 | sha256-before-parse; named-member extract only | CLI (run-once) | `.venv/bin/python scripts/fetch_personachat.py && test -s data/raw/personachat/train_self_revised.txt` | ✅ exists | ✅ green |
| inflation metrics + report | 11-03 T2 | 2 | DATA-04 | — | report-don't-gate; auditable denominators | unit + artifact | `.venv/bin/python -m pytest tests/test_dialogue_serialize.py -k inflation -x -q && test -s results/inflation_report.md` | ✅ exists | ✅ green |
| D-09 verdict checkpoint | 11-03 T3 | 2 | DATA-04 | — | verdict recorded before any bin | human + grep | `grep -A3 "## Verdict" results/inflation_report.md \| grep -v "^#" \| grep -c -E "GO\|ADAPT\|STOP"` | n/a | ✅ green |
| bin building + sanity | 11-04 T1 | 3 | DATA-02, DATA-03 | T-11-07 | SystemExit if verdict PENDING/STOP; sanity block enforced | CLI (run-once) | `.venv/bin/python scripts/prepare_dialog_corpus.py && test -s data/dialog_train.bin` | ✅ exists | ✅ green |
| build evidence + suite | 11-04 T2 | 3 | DATA-02 | — | report append only | full suite | `make test` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] No pre-existing test scaffolds required — all three test files (test_dialogue_parse.py, test_dialogue_serialize.py, test_masked_batch.py) land inside their Wave-1 plans in TDD order (tests written before implementation within each task).

*Existing pytest infrastructure covers the framework; new test files land with their plans.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GO/ADAPT/STOP verdict on tokenizer-inflation gate | DATA-04 | Pre-registered user decision (D-09) — measurement is automated, verdict is not | Review inflation report vs GO/ADAPT/STOP bands with 2.864 TinyStories baseline + 1.135× relative context (11-03 Task 3) |
| One-time ~223 MB fetch, full-corpus gate run, bin building | DATA-01/02/04 | Network + run-once discipline (same posture as v1.0 encode_corpus.py) | Each script carries a loud post-run sanity block (checksum, episode counts, eos counts, masked fraction, decoded prefix) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (tests land with their plans, TDD-ordered)
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner sign-off 2026-07-31
