---
phase: 08-demo-writeup
verified: 2026-06-10T22:57:08Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 6/7
  gaps_closed:
    - "A Gradio chat UI (gr.ChatInterface, share=False, localhost) runs the model on laptop CPU fully offline with temperature/top-k controls — CR-01 crash at in-UI slider extremes closed by the forbid_ids dead-id logits mask (08-07); WR-01 effective-vocabulary honesty, WR-02 export_slim val_loss=None, WR-03 clone-first quickstart, WR-04 notebook-extra matplotlib all closed (08-07/08-08)"
  gaps_remaining: []
  regressions: []
---

# Phase 8: Demo & Writeup Verification Report

**Phase Goal:** The tangible portfolio artifacts — an offline laptop-CPU Gradio chat demo, a narrated research notebook, a green per-component test suite, and the consolidated technical writeup — proving the from-scratch model runs on-device and reads as rigorous.
**Verified:** 2026-06-10T22:57:08Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plans 08-07, 08-08)

**Mode note:** ROADMAP marks this phase `mode: mvp`, but the goal is not in User Story format (`user-story.validate` → false), as is true for every phase 2-8 in this roadmap. Consistent with the initial verification and prior phases, standard goal-backward methodology was applied.

## Re-Verification Focus

Previous verification (2026-06-10T22:30:00Z) found one blocking gap: **CR-01** — the flagship demo could crash a user's message at slider settings its own UI offers (~29% per 400-token generation at temp 1.5 / top-k disabled), because the model samples over 8192 ids while the frozen tokenizer decodes only 547, and the streaming wrapper let the unknown-id `ValueError` propagate. The gap's `missing` list locked the fix contract: a `forbid_ids` logits mask (never catch-and-truncate), regression tests, and the WR-01 effective-vocabulary honesty fold-in.

Gap items received full 3-level + behavioral verification; the 6 previously-passed truths received regression checks.

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | Slim fp32 inference checkpoint (no optimizer state, safe `weights_only` load) loads and generates on laptop CPU, verified by an offline test | ✓ VERIFIED | Regression: `checkpoints/model_slim.pt` (55,601,269 bytes) loaded via `load_slim` in the demo smoke during this verification; `tests/test_slim_checkpoint.py` now 5 tests (4 prior + WR-02 round-trip), all green in the suite run. `load_slim` `weights_only=True` choke point unchanged |
| 2   | A Gradio chat UI (`gr.ChatInterface`, `share=False`, localhost) runs the model on laptop CPU fully offline with temperature/top-k controls | ✓ VERIFIED | **Gap closed.** `forbid_ids` mask applied at the TOP of `next_token` (sampling.py:88-89, `masked_fill` to -inf before BOTH the greedy argmax and the temperature/top-k/top-p pipeline), passed per-step by `generate` (core.py:65), threaded via `**gen_kw` through the text wrappers; `build_demo` constructs the mask from the live vocab + specials (demo_app.py:90) and `tell_story` passes `forbid_ids=forbid_ids` (demo_app.py:105). Behavioral: `build_demo()` → `ChatInterface`; 5-seed real-artifact sweep at the EXACT measured crash settings (temp 1.5, top-k None, 400 tokens) → zero crashes, mask sum exactly 7645. Do-not-catch contract intact: `grep -c "except ValueError"` text.py → 0; the wrapper still catches ONLY `UnicodeDecodeError` (text.py:111). UI untouched per 08-UI-SPEC: 3 sliders, ranges byte-identical (0.1-1.5 / 0-200 / 16-1024). `share=False` (demo_app.py:125), CPU pinned, analytics killed before `import gradio` |
| 3   | `demo.ipynb` reads the CSV log to show training curves, sampling, and the exact parameter count as a research artifact | ✓ VERIFIED | Regression: notebook unmodified since 08-06 (`git log` last touch ff4c7f4); 4 code cells, exec counts 1..4, 4/4 with committed outputs, 176,139 bytes; `results/run.csv` still byte-identical to `logs/run.csv` (cmp clean, 201 lines) |
| 4   | Full per-component test suite runs green via pytest; reproducibility discipline holds (config saved with each checkpoint, seeds fixed, git SHA recorded) | ✓ VERIFIED | Ran `.venv/bin/python -m pytest -q` during this verification: **137 passed, 1 skipped (CUDA fp16 smoke), 77s** — exactly baseline 130 + 7 gap-closure tests; both real-artifact tests RAN (not skipped) since the slim checkpoint exists locally. `ruff check` + `ruff format --check` clean (77 files). Provenance trio (`model_config`/`git_sha`/`step`) inside the slim artifact pinned by the green `test_slim_carries_provenance` |
| 5   | A polished technical writeup (README/report) documenting design decisions, architecture, training, and results, consolidated from document-as-we-go notes | ✓ VERIFIED | Improved by 08-08: effective vocabulary stated honestly everywhere — `547` in README (1 site) and REPORT (3 sites); `2,935,680` dead-row parameters quantified (REPORT:373); no unqualified `vocabulary 8192`/`an 8192 vocabulary` remains (grep fails in both files); CR-01 mitigation documented (REPORT:363 "masks the 7645 tokenizer-undecodable ids out of the logits before sampling"); stale "126 passed" unpinned. Locked rigor signals survive: `2.1066` counts unchanged (README 1, REPORT 3), `12,636,922` in both, `NOT to the headline` verbatim, `ln(8192)` untouched (REPORT:381). README now 111 lines with clone-first quickstart (clone line 52 + `cd` 53 precede venv line 56); all linked artifacts resolve |
| 6   | `assets/demo.gif` README hero proves live CPU streaming (light mode, 720px, <10 MB) | ✓ VERIFIED | Regression: magic `GIF89a`, width 720, 128,309 bytes; hero at README.md:9 with locked alt text |
| 7   | The slim weights are obtainable (GitHub Release asset per developer decision) | ✓ VERIFIED | Regression: `git ls-remote --tags origin m1-demo-v1` → 882af22 (same SHA as initial verification) |

**Score:** 7/7 truths verified

### Gap-Closure Plan Must-Haves (08-07 / 08-08)

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Demo never errors at ANY in-UI slider setting: sampling can only emit tokenizer-decodable ids | ✓ VERIFIED | Mask wired end-to-end; 5-seed 400-token sweep at temp 1.5 / top-k off → zero crashes (pre-fix: ~82% chance ≥1 crash in 5 runs); `test_real_artifact_crash_settings_no_crash` green |
| 2 | `next_token`/`generate` accept optional `forbid_ids` applied BEFORE greedy argmax and BEFORE the sampling pipeline | ✓ VERIFIED | sampling.py:71/88-92 (mask precedes the `if greedy` branch); core.py:37/65 passthrough |
| 3 | Regression test forces an undecodable id through a stub model: mask → only decodable ids; no mask → loud `ValueError("unknown token id")` | ✓ VERIFIED | `test_generate_text_with_mask_streams_clean` (dead id 9 holds top logit; output `"d"*5`) + `test_generate_text_without_mask_fails_loudly` (`pytest.raises(ValueError, match="unknown token id")`) — both green |
| 4 | `forbid_ids=None` default leaves every existing consumer bit-for-bit unchanged | ✓ VERIFIED | Full pre-existing suite green inside the 137-passed run; mask logic is a no-op when None |
| 5 | `export_slim` on `val_loss=None` writes None instead of raising (WR-02) | ✓ VERIFIED | checkpoint.py:134/141 (`float(val_loss) if val_loss is not None else None`); `test_export_slim_handles_val_loss_none` round-trips through `load_slim`, green |
| 6 | Effective vocabulary stated honestly wherever 8192 was claimed (WR-01) | ✓ VERIFIED | All four claim sites corrected; trainer-warning paragraph in the BPE decision section; greps above |
| 7 | Dead embedding rows quantified (2,935,680 of 13,891,584) | ✓ VERIFIED | REPORT:373 |
| 8 | README quickstart works verbatim from an empty directory (WR-03) | ✓ VERIFIED | `git clone` + `cd PersonaCore` at README:52-53, before venv at :56; install/release/launch lines unchanged |
| 9 | `.[cpu,notebook]` provides matplotlib (WR-04) | ✓ VERIFIED | pyproject.toml:18 `notebook = ["ipykernel~=7.3", "nbconvert~=7.17", "matplotlib~=3.10"]`; `matplotlib~=3.10` count exactly 2 (demo extra untouched) |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/personacore/generation/sampling.py` | `next_token(..., forbid_ids=None)` mask in both branches | ✓ VERIFIED | Keyword-only param; `masked_fill(forbid_ids, float("-inf"))` at function top, before greedy and before `apply_temperature`; non-mutating |
| `src/personacore/generation/core.py` | `generate(..., forbid_ids=None)` passthrough | ✓ VERIFIED | `forbid_ids=forbid_ids` in the explicit `next_token(...)` call each step |
| `src/personacore/generation/text.py` | `undecodable_ids_mask(tokenizer, vocab_size)` helper | ✓ VERIFIED | (1, vocab) bool tensor, True off `set(tok.vocab) | set(tok.special_tokens.values())` — same id test as `BPETokenizer.decode`; duck-typed; eos never masked |
| `src/personacore/generation/__init__.py` | Exports `undecodable_ids_mask` | ✓ VERIFIED | Imported from `.text`, in `__all__` |
| `tests/test_forbid_ids.py` | 6 CR-01 regression tests, min 60 lines, contains "unknown token id" | ✓ VERIFIED | 225 lines, 6 tests (greedy mask, sampled-never-forbidden x50 draws, mask shape/content, wrapper-clean-with-mask, fail-loudly-without, real-artifact crash-settings skipif-gated); all green |
| `scripts/demo_app.py` | Mask built in `build_demo`, threaded into callback, UI untouched | ✓ VERIFIED | Import line 40, mask at line 90 with decision-citing comment, `forbid_ids=forbid_ids` at line 105; 3 sliders unchanged; docstring SECURITY paragraph records the mitigation (line 25-26) |
| `src/personacore/checkpoint.py` | `export_slim` None-safe val_loss, contains "val_loss is not None" | ✓ VERIFIED | Lines 131-141 with WR-02 comment; primitive None survives `weights_only=True` |
| `tests/test_slim_checkpoint.py` | New `test_export_slim_handles_val_loss_none` | ✓ VERIFIED | Line 132; 5 tests total, green |
| `README.md` | "547" honesty claim + clone-first quickstart | ✓ VERIFIED | 111 lines; both present; hero/links/rigor signals intact |
| `docs/REPORT.md` | "2,935,680" + effective-vocab + CR-01 note | ✓ VERIFIED | All present; locked signals untouched |
| `pyproject.toml` | matplotlib in notebook extra | ✓ VERIFIED | Line 18 |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| scripts/demo_app.py | generation/text.py | `undecodable_ids_mask(tok, model.config.vocab_size)` in build_demo | ✓ WIRED | demo_app.py:40 (import), :90 (call) |
| scripts/demo_app.py | generation/text.py | `forbid_ids=` kwarg into `generate_text_cumulative` in tell_story | ✓ WIRED | demo_app.py:105; closure captures the mask once at build time |
| generation/core.py | generation/sampling.py | `forbid_ids=forbid_ids` passthrough | ✓ WIRED | core.py:65 |
| generation/sampling.py | logits | `masked_fill` to -inf before greedy/temperature | ✓ WIRED | sampling.py:89, precedes the `if greedy` branch at :91 |
| README.md | github.com/RAFAELDCOELHO/PersonaCore | `git clone` step 1 in the quickstart | ✓ WIRED | README:52, inside the fenced bash block |
| docs/REPORT.md | scripts/demo_app.py (08-07 fix) | demo decision section documents the dead-id logits mask | ✓ WIRED | REPORT:363 "tokenizer-undecodable", cites `tests/test_forbid_ids.py` |
| pyproject.toml | demo.ipynb matplotlib imports | `matplotlib~=3.10` in the notebook extra | ✓ WIRED | pyproject.toml:18 |
| (regression) all 10 previously-verified links | — | — | ✓ WIRED | Spot-rechecked: analytics kill before import (demo_app.py:34→36), `load_slim` choke point (demo_app.py:78), README hero (line 9) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| scripts/demo_app.py | `forbid_ids` mask | live `tok.vocab` + `tok.special_tokens` from the frozen `artifacts/tokenizer.json` | Yes — mask sums to exactly 7645 against the real artifact | ✓ FLOWING |
| scripts/demo_app.py | streamed story text | real GPT from `model_slim.pt` through the masked sampling path | Yes — 5 seeded 400-token generations produced non-empty strings | ✓ FLOWING |
| docs/REPORT.md honesty claims | 547 / 7645 / 2,935,680 | trainer's own warning (bpe.py) + 7645×384 arithmetic; cross-checked by the post-closure review by hand | Yes | ✓ FLOWING |
| (regression) demo.ipynb curves / README metrics | committed `results/run.csv` / results artifacts | unchanged since initial verification | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full suite green (QA-01) | `.venv/bin/python -m pytest -q` | 137 passed, 1 skipped, 77.57s | ✓ PASS |
| Editable install points at main checkout | `python -c "import personacore; print(__file__)"` | `/Users/juliorcoelho/PersonaCore/src/personacore/__init__.py` | ✓ PASS |
| Demo constructs against real artifact with mask | importlib exec of demo_app + `build_demo()` | prints `ChatInterface` | ✓ PASS |
| Crash-settings sweep (the closed gap) | 5 seeds × 400 tokens, temp 1.5, top-k None, `forbid_ids` mask, real slim + frozen tokenizer | zero crashes; mask sum == 7645 | ✓ PASS |
| Do-not-catch contract | `grep -c "except ValueError" src/personacore/generation/text.py` | 0 | ✓ PASS |
| Honesty greps (08-08 gates) | 547≥1/≥3, 2,935,680, no `vocabulary 8192`, no `126 passed`, `undecodable` present | all pass | ✓ PASS |
| Quickstart order | clone (52) < cd (53) < venv (56) | confirmed | ✓ PASS |
| Lint | `.venv/bin/ruff check .` + `format --check` | All checks passed; 77 files formatted | ✓ PASS |
| Notebook / CSV / GIF / Release regression | json inspect, cmp, magic parse, ls-remote | exec 1..4 + outputs, identical 201 lines, GIF89a 720px 128 KB, tag at 882af22 | ✓ PASS |
| Claimed commits exist | `git cat-file -t` 144d287 cdd7786 3162b36 225a962 3923bd8 | all `commit` | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist in the repository and none are declared in any phase-8 PLAN/SUMMARY. Step 7c: SKIPPED (no probes).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DEMO-01 | 08-02, 08-07 | Gradio local web UI (offline, share=False) runs the model on laptop CPU | ✓ SATISFIED | CR-01 closed: every in-UI slider setting safe (mask + sweep + 6 regression tests); offline streaming human-verified at the 08-02 gate, UI byte-untouched by the fix |
| DEMO-02 | 08-01 | Slim fp32 inference checkpoint, safe weights_only load, generates on CPU, offline test | ✓ SATISFIED | Regression green; WR-02 broadens the export contract |
| DEMO-03 | 08-03 | demo.ipynb with curves and sampling from the CSV log | ✓ SATISFIED | Regression green (untouched since 08-06) |
| DOC-01 | 08-04, 08-05, 08-06, 08-08 | Polished technical writeup (README/report) | ✓ SATISFIED | WR-01/WR-03 closed; honesty claims added without regressing any locked rigor signal |
| QA-01 | 08-01, 08-06 | Per-component tests green via pytest as first-class deliverable | ✓ SATISFIED | 137 passed / 1 skipped, run by verifier |
| QA-02 | 08-01, 08-03, 08-06 | Config + seeds + git SHA discipline, incl. shipped artifact | ✓ SATISFIED | Provenance trio inside `model_slim.pt`; seeding/checkpoint tests green |

**Orphaned requirements:** None — REQUIREMENTS.md maps exactly these 6 IDs to Phase 8 and every ID appears in at least one plan's `requirements` field (gap plans claim DEMO-01 and DOC-01). REQUIREMENTS.md checkboxes for DEMO-01/DOC-01/QA-02 now read Complete; DEMO-02/DEMO-03/QA-01 remain Pending — bookkeeping owned by the orchestrator at milestone close.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (all gap-closure files) | — | TBD/FIXME/XXX/TODO/HACK | — | None found — debt-marker gate clean |
| scripts/demo_app.py | 114 | `placeholder=` | ℹ Info | Gradio textbox kwarg, not a stub marker (carryover classification) |
| README.md | — | "not yet implemented" style M2 framing | ℹ Info | Deliberate D-02 honest framing (carryover classification) |

### Post-Gap-Closure Code Review Cross-Reference (08-REVIEW.md @ 2c4a041)

The fresh review (2026-06-10T22:49:47Z, 0 critical / 2 warning / 9 info) independently confirms the prior Critical and all four Warnings fixed. Its two NEW warnings do not fail any must-have:

| Finding | Disposition in this verification |
| ------- | -------------------------------- |
| New WR-01: `forbid_ids` mask is CPU-built; crashes on MPS if a consumer follows the wrapper's MPS contract | ⚠ Warning, non-blocking — DEMO-01 and every phase-8 must-have are laptop-CPU-scoped; the demo pins CPU (demo_app.py:81). Latent for future M2 consumers; one-line `.to(logits_last.device)` fix suggested in the review. Backlog item |
| New WR-02: 7 untrained non-EOS specials (8185-8191) remain sampleable — literal `<|user|>`/`<|pad|>` markup possible (~3.1e-4 per 400-token story at extremes) | ⚠ Warning, non-blocking — these ids ARE decodable, so no crash is possible; the must-have truth ("sampling can only emit tokenizer-decodable ids") and the REPORT claim ("can only produce decodable ids") hold as written. Quality polish for the backlog |
| IN-01..IN-09 | Info — none affect must-haves |

### Human Verification Required

None outstanding. All human gates were resolved during execution with documented resume signals (08-02 Wi-Fi-off streaming smoke APPROVED; 08-03/08-05/08-06 gates approved; GIF re-capture reviewed). The gap-closure plans (08-07/08-08) were fully autonomous with automated verification only — no `<verify><human-check>` blocks exist to harvest. The CR-01 fix changes only the sampling path (UI, networking, and launch flow byte-untouched), and its behavior is pinned programmatically by the real-artifact regression test plus this verification's 5-seed sweep at the exact measured crash settings.

### Gaps Summary

No gaps remain. The single blocking gap (CR-01) is closed exactly per the locked contract: dead ids are masked from the logits before sampling (prevention, never catch-and-truncate — `except ValueError` count in the wrapper is still 0), the mask-or-fail-loudly contract is pinned by six regression tests, and the demo wires the mask once at build time from the live vocab + specials. Behavioral proof on the real shipped artifact at the exact pre-fix crash settings (temp 1.5, top-k disabled, 400 tokens): zero crashes across 5 seeds, where pre-fix odds of at least one crash were ~82%. All four warnings (WR-01..WR-04) closed alongside: the writeup now states the 547-live/7645-dead vocabulary honestly with the 2,935,680 dead-row parameters quantified, the quickstart works verbatim from an empty directory, the notebook extra can run the notebook, and `export_slim` survives `val_loss=None`. No regressions: suite green at 137 passed (130 baseline + 7 new), lint clean, every previously-verified truth re-checked and holding, all locked rigor signals intact. The post-closure code review's two new warnings (MPS mask device alignment; sampleable untrained specials) are real but outside the phase's CPU-scoped must-haves — recommended for the review backlog, not this phase.

---

_Verified: 2026-06-10T22:57:08Z_
_Verifier: Claude (gsd-verifier)_
