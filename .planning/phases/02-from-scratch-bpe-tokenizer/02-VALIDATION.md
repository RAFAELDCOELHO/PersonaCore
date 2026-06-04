---
phase: 2
slug: from-scratch-bpe-tokenizer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-04
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `02-RESEARCH.md` §Validation Architecture. Task IDs are assigned by the planner; the requirement→test map below is the source of truth.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already pinned in `[dev]`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) — exists |
| **Quick run command** | `python3.11 -m pytest tests/test_tokenizer_roundtrip.py tests/test_tokenizer_special.py -x` |
| **Full suite command** | `make test` (pytest over all of `tests/`, CPU-only) |
| **Estimated runtime** | ~5s quick / <30s full (oracle skips when offline) |

---

## Sampling Rate

- **After every task commit:** Run quick command (roundtrip + special) — <5s, no network.
- **After every plan wave:** Run `make test` full suite — CPU-only, oracle skips if offline.
- **Before `/gsd:verify-work`:** Full suite green AND the tiktoken oracle run at least once with network/cache (documented evidence).
- **Max feedback latency:** ~5 seconds (quick), ~30 seconds (full).

---

## Per-Requirement Verification Map

| Requirement | Behavior | Test Type | Automated Command | File Exists |
|-------------|----------|-----------|-------------------|-------------|
| TOK-01 | Train twice → identical merges & ids (determinism, lowest-rank replay) | unit | `pytest tests/test_tokenizer_train.py -x` | ❌ W0 |
| TOK-02 | `decode(encode(x))==x` over tricky set; no `<unk>`; `"".join(chunks)==text` | unit | `pytest tests/test_tokenizer_roundtrip.py -x` | ❌ W0 |
| TOK-03 | EOS atomic (never split/merged-across); `eos_id` present in `ModelConfig` | unit | `pytest tests/test_tokenizer_special.py -x` | ❌ W0 |
| TOK-04 | save→load→identical encode/decode; `vocab_size==8192`; schema version asserted | unit | `pytest tests/test_tokenizer_io.py -x` | ❌ W0 |
| TOK-05 | from-scratch == tiktoken `gpt2` on oracle strings; tiktoken not in runtime | unit (skip-on-offline) | `pytest tests/test_tokenizer_oracle.py -x` | ❌ W0 |
| D-01 | `ModelConfig.vocab_size == 8192` (updated from 50304) | unit | `pytest tests/test_config.py -x` | ✅ (update existing) |
| Pitfall 4 | no `tiktoken` import under `src/` | unit (guard) | `pytest tests/test_tokenizer_oracle.py::test_no_runtime_tiktoken -x` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky — planner maps these to concrete task IDs.*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/tricky_strings.py` — round-trip corpus: ASCII+leading/trailing space, smart quotes/em-dash/ellipsis, ZWJ emoji + flags, multi-byte scripts (café/日本語/Привет), newlines/tabs/whitespace runs, digits+punctuation, embedded `<|endoftext|>` literal, empty + single byte (TOK-02)
- [ ] `tests/fixtures/tiny_corpus.txt` — small committed corpus for offline train tests (TOK-01)
- [ ] `tests/test_tokenizer_train.py` — determinism + lowest-rank replay (TOK-01)
- [ ] `tests/test_tokenizer_roundtrip.py` — round-trip + chunk-join invariant (TOK-02)
- [ ] `tests/test_tokenizer_special.py` — EOS atomicity + config `eos_id` (TOK-03)
- [ ] `tests/test_tokenizer_io.py` — freeze/load + `vocab_size==8192` + schema version (TOK-04)
- [ ] `tests/test_tokenizer_oracle.py` — tiktoken equivalence (skip-on-offline) + no-runtime-tiktoken guard (TOK-05, Pitfall 4)
- [ ] Update `tests/test_config.py` — assert `vocab_size==8192`, `eos_id` present
- [ ] Dependency install: `regex` (core), `tiktoken` (`[dev]`) — add to `pyproject.toml` + `requirements.txt`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| tiktoken `gpt2` oracle exact-ID equivalence with live network/cache | TOK-05 | CI runs offline (CPU-only, no network) so the oracle test skips; the equivalence must be confirmed at least once with `TIKTOKEN_CACHE_DIR` seeded or network available | Run `pytest tests/test_tokenizer_oracle.py -x` once on a networked machine (or with a seeded `TIKTOKEN_CACHE_DIR`); record pass as phase-gate evidence |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
