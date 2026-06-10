---
phase: 08-demo-writeup
verified: 2026-06-10T22:30:00Z
status: gaps_found
score: 6/7 must-haves verified
overrides_applied: 0
gaps:
  - truth: "A Gradio chat UI (gr.ChatInterface, share=False, localhost) runs the model on laptop CPU fully offline with temperature/top-k controls"
    status: partial
    reason: "CR-01 (08-REVIEW, mechanism independently re-confirmed in code during this verification): the demo crashes mid-generation at slider settings its own UI offers. The frozen production tokenizer decodes only 547 of the model's 8192 ids (283 learned merges; the BPE trainer itself warns '7645 dead ids' during the test run). BPETokenizer.decode raises plain ValueError for any dead id (src/personacore/tokenizer/bpe.py:208), but the streaming wrapper's per-step decode catches ONLY UnicodeDecodeError (src/personacore/generation/text.py:86-89), so the ValueError propagates through generate_text_cumulative and kills the tell_story callback. Reachable via the UI: the Top-k slider offers '0 = disabled' and Temperature goes to 1.5 (scripts/demo_app.py:109-110); the review measured ~29% crash probability per 400-token generation at those extremes. Defaults (temp 0.8, top-k 50) are safe — which is why the 08-02 human Wi-Fi-off smoke, the notebook, and the hero GIF all passed."
    artifacts:
      - path: "scripts/demo_app.py"
        issue: "Sliders expose temp up to 1.5 and top-k 0 (disabled); no protection against sampling tokenizer-undecodable ids"
      - path: "src/personacore/generation/text.py"
        issue: "Per-step decode catches only UnicodeDecodeError; unknown-id ValueError propagates and errors the user's message in the UI"
    missing:
      - "Mask tokenizer-undecodable ids out of the logits before sampling (review's suggested fix: optional forbid_ids mask threaded through next_token/generate/generate_text, built in build_demo from the live vocab + specials) — do NOT fix by catching ValueError (would silently truncate and swallow genuine strict-decode defects)"
      - "Regression test forcing an undecodable id through a stub model, asserting generation either masks it or fails loudly"
      - "While closing this gap, fold in WR-01: state the effective vocabulary (547 live ids of the 8192 table) wherever README/REPORT claim 'vocabulary 8192' — same root cause, honesty bar for a rigor-branded writeup"
---

# Phase 8: Demo & Writeup Verification Report

**Phase Goal:** The tangible portfolio artifacts — an offline laptop-CPU Gradio chat demo, a narrated research notebook, a green per-component test suite, and the consolidated technical writeup — proving the from-scratch model runs on-device and reads as rigorous.
**Verified:** 2026-06-10T22:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

**Mode note:** ROADMAP marks this phase `mode: mvp`, but the goal is not in User Story format (`user-story.validate` → false), as is true for every phase 2-8 in this roadmap. Prior phase verifications (e.g., Phase 7) proceeded with standard goal-backward methodology against descriptive goals, and the orchestrator dispatched this as a standard verification — so standard methodology was applied. If MVP-style user-flow UAT framing is wanted, run `/gsd mvp-phase 8` to reformat the goal.

## Goal Achievement

### Observable Truths

Merged must-haves: 5 ROADMAP Success Criteria (the contract) + 2 plan-level truths not subsumed by any SC (GIF hero, weights distribution).

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Slim fp32 inference checkpoint (no optimizer state, safe `weights_only` load) loads and generates on laptop CPU, verified by an offline test | ✓ VERIFIED | Loaded `checkpoints/model_slim.pt` (55,601,269 bytes vs best.pt's ~159 MiB) directly via `load_slim` in this verification: keys exactly `{git_sha, model, model_config, schema_version, step, val_loss}`, `git_sha=3a46815d`, `step=49000`, dedup param count 13,891,584, `lm_head/wte` tying survives (`data_ptr` identity True). `load_slim` uses `weights_only=True` (checkpoint.py:150). `tests/test_slim_checkpoint.py` (4 tests incl. real-artifact CPU generation) passed in the full-suite run; skipif-gated for CI |
| 2 | A Gradio chat UI (`gr.ChatInterface`, `share=False`, localhost) runs the model on laptop CPU fully offline with temperature/top-k controls | ✗ PARTIAL | Demo IS wired end-to-end: `build_demo()` constructed a real `ChatInterface` against the real slim artifact in this verification; `share=False` (demo_app.py:117), CPU pinned via `RuntimeConfig(device="cpu")`, analytics killed before `import gradio`, offline streaming human-verified Wi-Fi-off at the 08-02 blocking checkpoint. BUT CR-01: crash at in-UI slider settings — see Gaps. The flagship demo can error out a user's message at temp/top-k values its own controls offer, undermining "reads as rigorous" |
| 3 | `demo.ipynb` reads the CSV log to show training curves, sampling, and the exact parameter count as a research artifact | ✓ VERIFIED | 4 code cells, execution counts exactly 1..4, all 4 with committed outputs, 176 KB (<5 MB). Contains `load_slim`, `results/run.csv` (committed copy — `logs/run.csv` absent), `manual_seed(1337)`, `13,891,584`, `2.1066`, `12,636,922`, `NOT to the headline` verbatim. `results/run.csv` byte-identical to `logs/run.csv` (cmp clean, 201 lines, exact header) |
| 4 | Full per-component test suite runs green via pytest; reproducibility discipline holds (config saved with each checkpoint, seeds fixed, git SHA recorded) | ✓ VERIFIED | Ran `.venv/bin/python -m pytest -q` during this verification: **130 passed, 1 skipped (CUDA fp16 smoke), 70s**. QA-02 verified directly on the shipped artifact: `model_config` + `git_sha` + `step` travel inside `model_slim.pt` (loaded and printed above); `ruff check` + `ruff format --check` clean via the venv |
| 5 | A polished technical writeup (README/report) documenting design decisions, architecture, training, and results, consolidated from document-as-we-go notes | ✓ VERIFIED | `docs/REPORT.md` (440 lines, 20 `##` sections, decision→rationale→evidence structure); `README.md` (105 lines) opens thesis → GIF hero (line 9) → results block, all before quickstart (line ~48). Rigor signals verified by grep in BOTH: `2.1066` always adjacent to `12,636,922`, `13,891,584`, `tok/s`, `weights_only=True`, caveat `NOT to the headline` verbatim in REPORT, "representative" present, M2 always labeled upcoming. Warnings WR-01/WR-03 noted below |
| 6 | `assets/demo.gif` README hero proves live CPU streaming (light mode, 720px, <10 MB) | ✓ VERIFIED | Structural check run: magic `GIF89a`, logical width 720 (720x374), 128,309 bytes — matches the 08-05 re-capture addendum; not gitignored; referenced as hero at README.md:9 with the locked alt text |
| 7 | The slim weights are obtainable (GitHub Release asset per developer decision) | ✓ VERIFIED | Tag `m1-demo-v1` exists on origin (`git ls-remote` → 882af22); release page returns HTTP 200; `model_slim.pt` listed on the expanded-assets endpoint — all checked live during this verification |

**Score:** 6/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `scripts/export_slim.py` | Thin no-CLI export driver (DEMO-02) | ✓ VERIFIED | Exists, substantive, imports `export_slim` from package; no argparse/preflight |
| `src/personacore/checkpoint.py` | `export_slim`/`load_slim`/`SLIM_SCHEMA_VERSION` | ✓ VERIFIED | All three present; `load_slim` is the `weights_only=True` choke point with schema ValueError; additive (full-checkpoint API untouched) |
| `tests/test_slim_checkpoint.py` | 4 DEMO-02/QA-02 tests, CI-safe skip | ✓ VERIFIED | 4 `def test_`, contains `weights_only=True`, `skipif`, `data_ptr()` (x3); green in suite |
| `checkpoints/model_slim.pt` | ~56 MB shippable artifact (gitignored local + Release asset) | ✓ VERIFIED | 55,601,269 bytes; loaded under restricted unpickler in this verification; published as Release asset |
| `scripts/demo_app.py` | Offline Gradio launcher (DEMO-01) | ⚠ VERIFIED w/ gap | 122 lines, fully wired (no stubs); constructs ChatInterface against real artifact; CR-01 crash reachable via its own sliders |
| `src/personacore/generation/text.py` | `generate_text_cumulative` adapter | ✓ VERIFIED | Additive pure adapter; exported from `generation/__init__.py`; unit-tested gradio-free |
| `tests/test_demo_callback.py` | Cumulative-yield contract tests | ✓ VERIFIED | 4 tests, zero `import gradio`; green in suite |
| `results/run.csv` | Committed 50k-step training curve | ✓ VERIFIED | Byte-identical to `logs/run.csv`, 201 lines, exact header, trackable (not ignored) |
| `demo.ipynb` | Executed-with-outputs research notebook (DEMO-03) | ✓ VERIFIED | Outputs committed, exec counts 1..4, 176 KB, all acceptance strings present |
| `pyproject.toml` | `notebook` extra | ⚠ VERIFIED w/ warning | `notebook = ["ipykernel~=7.3", "nbconvert~=7.17"]` present; WR-04: matplotlib missing from the extra that needs it |
| `docs/REPORT.md` | D-03 decision-driven writeup (≥200 lines) | ✓ VERIFIED | 440 lines, 20 sections, all rigor-signal greps pass |
| `assets/demo.gif` | README hero (720px, <10 MB, light mode) | ✓ VERIFIED | GIF89a, 720x374, 128 KB; human-reviewed at the 08-06 gate (re-capture) |
| `README.md` | D-01/D-04 front door (≥60 lines) | ⚠ VERIFIED w/ warning | 105 lines, GIF above the fold, all links resolve to existing files; WR-03: quickstart lacks a `git clone` step (works from a clean clone, fails verbatim from an empty directory) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| scripts/export_slim.py | personacore.checkpoint | `from personacore.checkpoint import export_slim` | ✓ WIRED | SDK-verified |
| load_slim | checkpoints/model_slim.pt | `weights_only=True` restricted unpickler | ✓ WIRED | checkpoint.py:150 (SDK false-negative — `from` field was a parenthetical, not a path; verified manually + behaviorally) |
| tests/test_slim_checkpoint.py | personacore.model.GPT | `data_ptr()` tying assert | ✓ WIRED | 3 occurrences (SDK false-negative on double-escaped regex; verified manually) |
| scripts/demo_app.py | generation/text.py | `generate_text_cumulative` callback | ✓ WIRED | SDK-verified + behavioral construction |
| scripts/demo_app.py | checkpoint.py | `load_slim(SLIM_PATH)` | ✓ WIRED | SDK-verified |
| scripts/demo_app.py | gradio analytics kill | env var before `import gradio` | ✓ WIRED | Line 33 precedes line 35 import |
| demo.ipynb | model_slim.pt / results/run.csv / generation | load_slim / DictReader / seeded tour | ✓ WIRED | All three SDK-verified |
| docs/REPORT.md | results/results.md + samples.md | caveat verbatim + representative note | ✓ WIRED | SDK-verified |
| README.md | assets/demo.gif / docs/REPORT.md / scripts/demo_app.py / demo.ipynb | hero, deep-dive link, quickstart | ✓ WIRED | Lines 9, 23/72, 61, 75 (SDK false-negatives on escaped patterns; verified manually) |
| assets/demo.gif | scripts/demo_app.py | screen capture | ✓ VERIFIED | Binary asset — verified by structure (720px GIF89a) + 08-06 human gate review, per plan's own note |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| scripts/demo_app.py | streamed story text | real GPT rebuilt from `model_slim.pt` + frozen tokenizer | Yes (constructed + human-verified streaming) | ✓ FLOWING |
| demo.ipynb curves | loss/lr/tokens series | committed `results/run.csv` (byte-identical to training log) | Yes | ✓ FLOWING |
| demo.ipynb load cell | param count / SHA / step | real slim checkpoint via `load_slim` | Yes (output prints 13,891,584 / 3a46815d / 49000) | ✓ FLOWING |
| README/REPORT numbers | headline metrics | re-cited from committed results artifacts | Yes (cross-grepped consistent) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full suite green (QA-01) | `.venv/bin/python -m pytest -q` | 130 passed, 1 skipped, 70s | ✓ PASS |
| Slim artifact safe-load + provenance + tying | `load_slim('checkpoints/model_slim.pt')` + GPT rebuild | keys exact; 3a46815d/49000; 13,891,584 params; tied=True | ✓ PASS |
| Demo constructs against real artifact | importlib exec of demo_app + `build_demo()` | prints `ChatInterface` | ✓ PASS |
| Notebook integrity | json inspection | exec counts [1,2,3,4], 4/4 cells with outputs, 176 KB | ✓ PASS |
| CSV identity | `cmp logs/run.csv results/run.csv` | identical, 201 lines, exact header | ✓ PASS |
| GIF structure | magic/width/size parse | GIF89a, 720x374, 128,309 B | ✓ PASS |
| Release published | `git ls-remote --tags origin` + HTTPS | tag at 882af22; page 200; asset `model_slim.pt` listed | ✓ PASS |
| Lint | `.venv/bin/ruff check .` + `format --check` | All checks passed; 76 files formatted | ✓ PASS |
| `make lint` | bare make target | FAILS — `ruff: command not found` (PATH quirk: bare tools resolve outside the venv, same known quirk as bare `pytest`) | ℹ ENV |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist in the repository and none are declared in any phase-8 PLAN/SUMMARY. Step 7c: SKIPPED (no probes).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DEMO-01 | 08-02 | Gradio local web UI (offline, share=False) runs the model on laptop CPU | ⚠ PARTIAL | Demo runs, streams offline (human-verified), CPU-pinned — but CR-01 crash reachable from its own sliders (see Gaps) |
| DEMO-02 | 08-01 | Slim fp32 inference checkpoint, safe weights_only load, generates on CPU, offline test | ✓ SATISFIED | Verified directly + 4 green tests incl. real-artifact generation |
| DEMO-03 | 08-03 | demo.ipynb with curves and sampling from the CSV log | ✓ SATISFIED | Executed outputs committed; reads committed `results/run.csv` |
| DOC-01 | 08-04, 08-05, 08-06 | Polished technical writeup (README/report) | ✓ SATISFIED | README (105 ln) + REPORT (440 ln) + GIF hero, rigor signals consistent; WR-01/WR-03 polish warnings |
| QA-01 | 08-01, 08-06 | Per-component tests green via pytest as first-class deliverable | ✓ SATISFIED | 130 passed / 1 skipped, run by verifier |
| QA-02 | 08-01, 08-03, 08-06 | Config + seeds + git SHA discipline, incl. shipped artifact | ✓ SATISFIED | Provenance trio verified inside `model_slim.pt`; seeding/checkpoint tests green |

**Orphaned requirements:** None — REQUIREMENTS.md maps exactly these 6 IDs to Phase 8 and every ID appears in at least one plan's `requirements` field. Note: REQUIREMENTS.md checkboxes for DEMO-01/02/03, DOC-01, QA-01 still read `[ ]` Pending and the traceability table says Pending — bookkeeping owned by the orchestrator (worktree agents deliberately did not edit it), to be flipped at milestone close.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (all phase-modified files) | — | TBD/FIXME/XXX | — | None found — debt-marker gate clean |
| scripts/demo_app.py | 106 | `placeholder=` | ℹ Info | Gradio textbox kwarg, not a stub marker |
| README.md | 96 | "not yet implemented" | ℹ Info | Deliberate D-02 honest M2 framing — required by acceptance criteria, not a stub |
| tests/test_demo_callback.py | 26-29 | dead `except ImportError: GPT = None` guard | ℹ Info | IN-03 from review — vestigial, copied from existing convention; cosmetic |

### Code Review Cross-Reference (08-REVIEW.md)

| Finding | Disposition in this verification |
| ------- | -------------------------------- |
| CR-01 (Critical): demo crash at slider extremes | **GAP** — contradicts must-have truth SC2/08-02-truth-3; mechanism independently re-confirmed in bpe.py:208, text.py:86-89, demo_app.py:109-110, tokenizer.json (283 merges) |
| WR-01: "vocabulary 8192" vs 547 live ids | **Warning** — no stated must-have fails (denominators/caveats/M2 labels all hold), but it is a material omission for a rigor-branded writeup; folded into the gap's `missing` list (same root cause as CR-01) |
| WR-02: `export_slim` opaque TypeError on `val_loss=None` | Warning — latent contract defect (checkpoint.py:137); current caller always passes a value; fix opportunistically with the gap |
| WR-03: README quickstart lacks clone step | Warning — the must-have truth says "from a clean clone," which holds; verbatim-from-empty-directory fails. Two-line fix |
| WR-04: `notebook` extra lacks matplotlib | Warning — confirmed in pyproject.toml:18; `.[cpu,notebook]` cannot run the notebook's curve cells |
| IN-01..IN-08 | Info — noted; none affect must-haves |

### Human Verification Required

None outstanding. All human gates were resolved during execution with documented resume signals: 08-02 Task 3 (Wi-Fi-off streaming smoke — APPROVED), 08-03 Task 1 (ipykernel/nbconvert PyPI gate — approved), 08-05 Tasks 1-2 (ffmpeg source "brew"; recording provided), 08-06 Task 1 (distribution decision "release") plus the GIF re-capture review. No `<verify><human-check>` blocks exist on `auto` tasks to harvest. Status is `gaps_found`, which takes precedence regardless.

### Gaps Summary

Phase 8's deliverables are real and almost entirely verified against the codebase: the slim artifact loads under the restricted unpickler with provenance intact, the suite is green at 130 passed, the notebook is executed-with-outputs from committed data, the writeup carries every rigor signal verbatim, the GIF and Release are live. SUMMARY claims checked out in every case tested — no phantom artifacts, no stubs, all 13 claimed commits exist.

One gap blocks `passed`: **CR-01**. The flagship demo — the artifact the phase goal calls "the live proof" — can crash a user's message at temperature/top-k settings its own sliders offer, because the model samples over 8192 ids while the frozen tokenizer can decode only 547, and the streaming wrapper lets the resulting `ValueError` propagate. The review measured ~29% crash probability per 400-token generation at the slider extremes on the shipped weights. A portfolio reviewer dragging the temperature slider to maximum (a natural first move) has roughly 1-in-3 odds of an error per long story — directly against the goal's "reads as rigorous" bar. The fix is small and well-specified in the review (mask dead ids from the logits; never catch-and-truncate), and closing it should also fold in the WR-01 prose fix since both stem from the same dead-id fact.

This does not look like an intentional deviation (no plan/decision anywhere accepts the crash risk), so no override is suggested.

---

_Verified: 2026-06-10T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
