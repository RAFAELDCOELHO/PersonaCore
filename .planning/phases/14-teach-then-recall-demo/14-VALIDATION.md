---
phase: 14
slug: teach-then-recall-demo
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-01
updated: 2026-08-12
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `14-RESEARCH.md` § *Validation Architecture*. That file is frozen at research
> time; **this** file is the living status tracker — the Status column moves as tasks land.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (already installed; no Wave 0 framework install needed) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]`, `testpaths=["tests"]`, `pythonpath=["."]` |
| **Quick run command** | `.venv/bin/pytest -q tests/test_phase14_*.py tests/test_recall_prompt.py` |
| **Full suite command** | `make test` (`.venv/bin/pytest -q`) |
| **Estimated runtime** | quick: **5.65 s** (107 tests) · full: **122.35 s** (408 passed / 1 skipped) — re-measured 2026-08-12. Phase-close figures were 3.74 s / 101 tests and ~110 s / 389 tests; the growth is Phase 15's tests landing in the shared suite, not Phase-14 drift. |

The suite is **CPU-only and GPU-free by contract**. No test in this phase may require MPS, a
checkpoint file, or a Gradio launch.

---

## Sampling Rate

- **After every task commit:** `.venv/bin/pytest -q tests/test_phase14_*.py tests/test_recall_prompt.py`
- **After every plan wave:** `make test` **and** `make lint`
- **Before `/gsd:verify-work`:** full suite green + all four `results/phase14_*.md` artifacts
  committed + the D-06 blocking user verdict recorded
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

Task ID / Plan / Wave name the task that **shipped** each check. The three script-proof rows were
shipped by earlier plans and **executed** by plan 14-11 (wave 9): the teaching canary by 14-11 T1,
the scored recall run and Control 3 by 14-11 T2 — both runs exited 0, which is what turns those
rows green.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T2 | 14-03 | 3 | DEMO-05 | — | Locked fact values keep token census + byte-fallback round-trip (D-07) | unit | `.venv/bin/pytest tests/test_phase14_factset.py -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-05 | — | Teaching episodes mask exactly the answer span + eos (golden fixture) | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_answer_span_mask -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-05 | — | Teaching bin length > `block_size + 1`; token/mask bins element-aligned | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_bin_shape -x` | ✅ exists | ✅ green |
| T1 | 14-07 | 5 | DEMO-05 | T-14-25 | Base params bit-untouched while LoRA learns the facts | script proof (`SystemExit` canary, MPS) | `.venv/bin/python scripts/teach_persona.py` | ✅ exists | ✅ green |
| T2 | 14-06 | 5 | DEMO-05 | T-14-18 | Fresh-process empty-prompt recall meets pre-registered thresholds; context dump proves no fact in context | script proof + committed report | `.venv/bin/python scripts/phase14_recall.py` | ✅ exists | ✅ green |
| T3 | 14-05 | 4 | DEMO-05 | — | D-19 generation-budget derivation + fit guard (pure function) | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_generation_budget -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-06 | — | Taught and held-out family id sets are disjoint | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_families_disjoint -x` | ✅ exists | ✅ green |
| T3 | 14-04 | 4 | DEMO-06 | — | No held-out question's id sequence is a contiguous subsequence of the teaching bin | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_no_token_leakage -x` | ✅ exists | ✅ green |
| T3 | 14-05 | 4 | DEMO-06 | — | Normalizer + substring gate + contradiction detector behave as specified | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py -x` | ✅ exists | ✅ green |
| T3 | 14-05 | 4 | DEMO-06 | T-14-34 | Pre-registered thresholds are literal module constants in the committed driver | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_preregistration_constants -x` | ✅ exists | ✅ green |
| T3 | 14-11 | 9 | DEMO-06 | T-14-18 | Taught vs held-out reported separately; all transcripts committed incl. failures | manual review | inspect `results/phase14_recall_report.md`, `results/phase14_transcripts.md` | ✅ exists | ✅ green (verdict recorded 2026-08-02) |
| T3 | 14-08 | 6 | DEMO-07 | — | `personalize_demo.py` `forbid_ids` mask tensor equals `demo_app.py`'s (D-17) | unit (CPU, no launch) | `.venv/bin/pytest tests/test_phase14_demo.py::test_forbid_ids_parity -x` | ✅ exists | ✅ green |
| T3 | 14-08 | 6 | DEMO-07 | — | UI token-panel ids byte-identical to the harness's committed dump (D-18) | unit | `.venv/bin/pytest tests/test_phase14_demo.py::test_prompt_ids_identical -x` | ✅ exists | ✅ green |
| T3 | 14-08 | 6 | DEMO-07 | T-14-27 | Demo emits zero remote stylesheet URLs (`build_demo().stylesheets == []`, UI-SPEC offline lock) | unit (CPU, no launch) | `.venv/bin/pytest tests/test_phase14_demo.py::test_no_remote_stylesheets -x` | ✅ exists | ✅ green |
| T3 | 14-01 | 1 | DEMO-07 | T-14-18 | `build_recall_prompt` ends at the assistant tag and contains no fact substring; `generate_text_from_ids` streams cumulatively | unit (tiny GPT fixture) | `.venv/bin/pytest tests/test_recall_prompt.py -x` | ✅ exists | ✅ green |
| T1 | 14-10 | 8 | DEMO-07 | T-14-28 | Adapter-off logits bit-identical to un-adapted base on real weights (D-11.3) | script proof, CPU | `.venv/bin/python scripts/phase14_recall.py` (control 3) | ✅ exists | ✅ green |
| — | pre-existing (Phase 9) | — | DEMO-07 | T-14-28 | Toggle enable/disable round-trip; eject returns vanilla tree; merged-module refusals | unit | `.venv/bin/pytest tests/test_lora_toggle.py -x` | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

The two adapter-gated demo tests (`test_forbid_ids_parity_real_artifacts`,
`test_build_demo_stylesheets_real`) skipped for the whole phase because
`checkpoints/persona_adapter.pt` did not exist. Plan 14-11 T1 produced it and they now **run and
pass**: the suite moved from 381 passed / 6 skipped to 386 passed / 1 skipped, and to **388 passed
/ 1 skipped** once 14-11 T3's demo-surface fix added its two `StripThirdPartyAssets` tests.

---

## Wave 0 Requirements

- [x] `tests/test_phase14_factset.py` — DEMO-05 (D-07 tokenizer census) — shipped 14-03 T2
- [x] `tests/test_phase14_teaching.py` — DEMO-05/DEMO-06 (mask fixture, bin shape, family disjointness, token-level no-leakage) — shipped 14-04 T3, extended 14-07 T3
- [x] `tests/test_phase14_scoring.py` — DEMO-06 (importlib-loaded scoring rules, thresholds, contradiction detector, D-19 budget) — shipped 14-05 T3, extended 14-09/14-10
- [x] `tests/test_phase14_demo.py` — DEMO-07 (D-17 mask parity, D-18 prompt byte-identity, offline stylesheet lock) — shipped 14-08 T3, extended 14-09
- [x] `tests/test_recall_prompt.py` — the two new package functions — shipped 14-01 T3
- [x] Framework install — **not needed**; pytest 9.0.3 present and the suite is green

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Guessability gate on the locked fact set | DEMO-05 | D-06 is a **blocking human verdict** by design — no automated proxy is legitimate | Run the gate script, read the candidate facts, record the verdict in the phase artifacts before teaching |
| Teaching run on real weights | DEMO-05 | Needs the 278 MB base checkpoint + MPS; forbidden in the CPU suite | `.venv/bin/python scripts/teach_persona.py`; canary raises `SystemExit` on base-weight drift |
| Calibration / scored recall run | DEMO-05, DEMO-06 | Needs checkpoints + MPS; produces the committed `results/phase14_*.md` artifacts | `.venv/bin/python scripts/phase14_recall.py`; review all four artifacts incl. failures |
| Demo surface on camera (toggle, Reset, token panel, streaming) | DEMO-07 | Gradio launch + human-visible behavior; the phase deliverable is a recorded frame | Launch `scripts/personalize_demo.py` locally, exercise ON → OFF → Reset, confirm the token panel and per-bubble stamps match the UI-SPEC contracts |

### Recorded outcomes — 2026-08-02, 14-11 Task 3 blocking checkpoint

**Part A — the evidence (DEMO-05 / DEMO-06).** Verdict recorded verbatim in
`results/phase14_recall_report.md` `## Verdict`: **ADAPT — GO with two qualifications** (residual
collateral collapse at +27.16%; the question-fairness control at 1/1944). Both qualifications are
recorded as named limitations *alongside* the passed gate numbers, not folded into them; no locked
threshold was touched and `## Ship Decision — post-verdict, discretionary` correctly stays empty
because no gate was missed.

**Part B — the demo, in a live browser** at http://127.0.0.1:7860, against the real
`checkpoints/persona_adapter.pt` and the post-fix demo surface (`5453d47`):

| Check (plan step) | Measured in the browser |
|---|---|
| Third-party origins on page load (13) | **`http://127.0.0.1:7860` only** — zero third-party requests |
| Off-origin `script[src]` / `link[href]` in the DOM (13) | **`[]`** |
| Startup token panel (8) | exactly `ids (3) : [8187, 8185, 8186]` |
| Accordion collapsed at load (8) | yes |
| **Token panel ON vs OFF, same question (10)** | **byte-identical**, while the answers differ — ON `i am going to go to the marrow.` / OFF `i work at a college state and could change him with scotch` |
| Recall on camera (9) | `i have a dog named zorp.`, `i live in brindlemoor.`, `i go by quick.` |
| Streaming monotonic (9) | 65 samples @ 200 ms, **SHRINK_EVENTS = 0**, growth trace `185 -> 235 -> 251` |
| Token panel stationary mid-stream (9) | **one** distinct bounding rect across all 65 samples (`top=306`, `left=782`) |
| Max-new-tokens slider clamp (11) | clamps at **48** — a programmatic `value=8` snapped back |
| Reset (12) | checkbox disabled + unchecked, Reset button disabled, banner `MEMORY: DELETED`, Ask still answers (`no it is the hockey.`) |
| Console errors | **zero** |

That fifth row is the phase's central claim in one frame: the prompt did not change and the answer
did. Full suite at close: **388 passed / 1 skipped**.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies — every task across 14-01…14-11 carries an `<automated>` block, including both blocking human checkpoints (14-02 T3, 14-11 T3)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify — longest gap is 0
- [x] Wave 0 covers all MISSING references — all five test files exist and are green
- [x] No watch-mode flags — every command is a single-shot `pytest -q` or script invocation
- [x] Feedback latency < 5s — quick run **measured at 3.74 s** (101 tests, 2026-08-02)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** **granted 2026-08-02** — the DEMO-05/06 recall verdict is recorded (ADAPT — GO with
two qualifications) and the DEMO-07 on-camera demo pass is confirmed in a live browser; see
*Recorded outcomes* above. Everything automatable is green (388 passed / 1 skipped).

---

## Validation Audit 2026-08-12

Re-audit of this file against the live repository (State A). Every claim below was re-measured in
this pass, not carried forward from the phase-close text above.

| Metric | Count |
|--------|-------|
| Requirements in scope | 3 (DEMO-05, DEMO-06, DEMO-07) |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**What was re-verified.**

- **Every pytest node id this file names still resolves.** All nine cited names —
  `test_answer_span_mask`, `test_bin_shape`, `test_generation_budget`, `test_families_disjoint`,
  `test_no_token_leakage`, `test_preregistration_constants`, `test_forbid_ids_parity`,
  `test_prompt_ids_identical`, `test_no_remote_stylesheets` — were confirmed present via
  `pytest --collect-only` against the six files in the map. No row points at a deleted test.
- **Phase-14 quick suite: 107 passed, 0 failed, 0 skipped** (5.65 s) on the command as written.
  Adding the map's `tests/test_lora_toggle.py` row gives **113 passed** (6.08 s).
- **Full suite: 408 passed / 1 skipped / 0 failed** (122.35 s). The single skip is
  `tests/test_train_loop.py:81` — *"fp16 AMP smoke needs a CUDA GPU"* — a CUDA-only guard that is
  correct to skip on the primary M3/MPS path, not a Phase-14 gap.
- **Requirement coverage is complete.** DEMO-05, DEMO-06 and DEMO-07 each carry at least one
  automated row in the Per-Task Verification Map; `REQUIREMENTS.md:113-118` marks all three
  Complete. No Phase-14 requirement lacks automated verification, so `nyquist_compliant: true`
  stands unchanged.

**Non-gap finding, recorded rather than fixed.** `make test` runs bare `pytest`, not
`.venv/bin/pytest` as the Test Infrastructure table states. Invoked without the venv activated it
fails with 62 collection errors (`No module named 'personacore' / 'torch' / 'gradio'`) — the
system Python 3.14 has none of them. This is not a regression and not a Phase-14 defect: CLAUDE.md
documents `source .venv/bin/activate` before `make test`, and under that flow the recipe resolves
to the venv pytest exactly as the table says. Noted here only so a future reader who hits the
collection wall does not mistake it for broken tests.
