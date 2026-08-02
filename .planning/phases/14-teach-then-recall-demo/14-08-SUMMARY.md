---
phase: 14-teach-then-recall-demo
plan: 08
subsystem: ui
tags: [gradio, blocks, lora, demo, offline, clean-room, ci]

# Dependency graph
requires:
  - phase: 14-05
    provides: "scripts/phase14_recall.py — RECALL_MAX_NEW_TOKENS (D-19 budget) and render_context_dump (D-18 shared renderer)"
  - phase: 14-06
    provides: "the harness's model-load and completion helpers; RECALL_MAX_NEW_TOKENS = 48"
  - phase: 14-01
    provides: "personacore.dialogue.build_recall_prompt and personacore.generation.generate_text_from_ids_cumulative"
provides:
  - "scripts/personalize_demo.py — the gr.Blocks teach-then-recall demo: live memory toggle, one-way Reset, live prompt-token-id panel, budget-floored slider"
  - "tests/test_phase14_demo.py — 17 CI-enforced structural tests + 2 local-only"
  - "The demo extra installed in CI, Makefile, and CLAUDE.md so the demo tests actually run"
affects: [14-10, 14-11, 15]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gr.Blocks tuple-yield streaming: the callback yields (history, panel_text) so a second output can update alongside the chat"
    - "Checkpoint-free module surface (build_forbid_ids / render_token_panel) so CI can test a demo whose build_demo() needs gitignored artifacts"
    - "Permanent file-freeze test via `git diff <PINNED_SHA> HEAD -- <path>` rather than a working-tree `git diff --quiet`"

key-files:
  created:
    - scripts/personalize_demo.py
    - tests/test_phase14_demo.py
  modified:
    - .github/workflows/ci.yml
    - Makefile
    - CLAUDE.md

key-decisions:
  - "Memory toggle bound to Checkbox.input(), not .change() — .change() also fires on programmatic updates, so on_reset's gr.update(value=False) would have re-entered on_toggle and overwritten the MEMORY: DELETED banner with MEMORY: OFF"
  - "STOP_IDS imported from phase14_recall rather than retyping the {8184, 8185} literal — same module already imported, removes a drift risk between demo and harness"
  - "MISSING_BUDGET_MSG declared above the import it guards, so the three SystemExit sites share one constant instead of triplicating the message"
  - "Fact-set module NAME is absent from the demo source entirely (the plan's `grep -c phase14_factset == 0` criterion), so the clean-room claim holds under a plain grep as well as under the sys.modules check"
  - "Decode settings left at the package defaults (temperature=1.0, no top-k/top-p) because the plan enumerated the generation kwargs exactly; flagged below as an open item for 14-11 rather than silently chosen"

patterns-established:
  - "Closure-walking test helper recovers a build-time tensor from either a gr.Blocks or a gr.ChatInterface, so one assertion covers two different UI shapes"
  - "Every skipif carries a comment naming which assertion is local-only and why — a silently-skipped test is convention wearing a test's clothes"

requirements-completed: [DEMO-07]

# Metrics
duration: 58min
completed: 2026-08-02
---

# Phase 14 Plan 08: Teach-Then-Recall Demo Summary

**A `gr.Blocks` demo whose memory ON/OFF switch is 36 boolean writes on the live model — with a token panel that proves, every turn, that the context never changed.**

## Performance

- **Duration:** ~58 min
- **Tasks:** 3/3
- **Files created:** 2
- **Files modified:** 3
- **Tests:** 17 CI-enforced + 2 local-only; full suite 381 passed, 1 skipped (pre-existing)

## Accomplishments

### Task 1 — module surface (`379a4de`)

`scripts/personalize_demo.py`'s checkpoint-free half: the offline-verified `THEME`
(`gr.Blocks(theme=THEME).stylesheets == []`), `build_forbid_ids`, `render_token_panel`, and every
UI copy constant verbatim from 14-UI-SPEC. `RECALL_MAX_NEW_TOKENS` is imported (48) and never
re-derived. Importing the module loads no model and opens no window.

### Task 2 — UI, callbacks, `main()` (`2910e36`)

`build_demo()` refuses before `launch()` on either missing artifact, loads both under
`weights_only=True`, does LOAD BEFORE INJECT, pins CPU, and surfaces a fingerprint mismatch as a
persistent in-UI Markdown blockquote. `on_ask` yields `(history, panel)` tuples with the panel
computed once at turn start; `on_toggle` flips the 36 flags; `on_reset` ejects one-way and
disables the toggle and Reset while chat stays live. Every model-touching event shares one
`concurrency_id`.

### Task 3 — tests + extras parity (`c18da24`)

`tests/test_phase14_demo.py` (434 lines) plus the one-word `.[cpu,dev,demo]` change in
`ci.yml`, `Makefile`, and CLAUDE.md.

## Verification performed

Rather than trusting the plan's source-level checks alone, `build_demo()` was executed
end-to-end against a **throwaway, untrained** adapter fabricated locally (see Deviations):

- `build_demo()` constructs; `stylesheets == []`
- `on_ask` yields 49 two-tuples; the panel string is byte-identical across all 49; the assistant
  bubble grows monotonically and carries `**memory ON**` from the first yield
- **the token panel is character-identical ON vs OFF for the same question** — the phase's claim
- `on_toggle` swaps the banner; `on_reset` returns `MEMORY: DELETED` and the model still answers
- `inject_lora` wrapped exactly **36** projections, matching the number in the UI copy
- with the adapter deleted: `FileNotFoundError(MISSING_ADAPTER_MSG)` before `launch()`; with the
  base also gone: `FileNotFoundError(MISSING_SLIM_MSG)` — no window on a broken demo
- `test_no_fact_values_in_ui_chrome` was confirmed RED by temporarily pasting a locked fact value
  into `EXAMPLES`, then reverted (`git diff` clean)
- with checkpoints absent: exactly 2 skips, both reported by name

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Memory toggle bound to `.change()` would have clobbered the DELETED banner**
- **Found during:** Task 2
- **Issue:** `on_reset` returns `gr.update(value=False, interactive=False)` for the checkbox.
  Gradio's `.change()` fires on programmatic updates as well as user input, so Reset would have
  re-entered `on_toggle`, which returns `STATUS_OFF` — leaving a banner claiming the adapter was
  merely *gated off* when it had actually been *ejected*. That is precisely the class of
  misrepresentation 14-RESEARCH Pitfall 9 exists to prevent.
- **Fix:** bound to `Checkbox.input()`, which fires on user interaction only. Comment records why.
- **Commit:** `2910e36`

**2. [Rule 3 - Blocking] Two acceptance criteria were literal source greps my comments violated**
- **Found during:** Tasks 1 and 2
- **Issue:** `grep -c "phase14_factset" == 0` and `"cache_examples" not in src` are whole-file
  literal checks; my explanatory comments named both strings while doing the right thing.
- **Fix:** reworded to "the fact-set module" and "Example caching is left OFF (its keyword is
  deliberately absent from this file)". No behavior change.
- **Commits:** `379a4de`, `2910e36`

### Judgment calls (not bugs)

- **`STOP_IDS` imported from `phase14_recall`** instead of retyping `{8184, 8185}`. The plan wrote
  the literal; the module was already imported, so importing the pinned frozenset costs nothing
  and removes a way for the demo and the harness to drift apart.
- **`MISSING_BUDGET_MSG` hoisted** above the import it guards so the three `SystemExit` sites
  share one constant. The plan listed it with the other failure messages further down.
- **`MISMATCH_BANNER_TEMPLATE` placeholders renamed.** 14-UI-SPEC writes both fingerprint trios as
  `{git_sha}/{step}/{val_loss}`; `str.format` needs distinct field names, so they are
  `expected_*` / `adapter_*`. The rendered text is the spec's.
- **Two extra CI tests beyond the plan's list** (19 total, plan asked for ≥12):
  `test_analytics_killswitch_precedes_gradio_import` (the kill-switch is order-dependent, so its
  position is the contract) and `test_memory_toggle_is_weights_not_prompt` (asserts `persona=`
  never appears in the demo source — the phase's central claim had no test otherwise).

## Open item for plan 14-11

**The demo's decode settings are the package defaults: `temperature=1.0`, no top-k, no top-p.**
The plan enumerated the generation call's kwargs exactly (`max_new_tokens`, `forbid_ids`,
`stop_ids`) and 14-UI-SPEC's layout exposes no temperature control, so no decode tuning was
invented here. Note that this is *looser* than both neighbours: `scripts/demo_app.py` defaults its
sliders to `temp 0.8 / top-k 50`, and the harness's seeded samples use `SAMPLE_TEMPERATURE=0.8`,
`SAMPLE_TOP_P=0.95`. Unconstrained temp-1.0 sampling will look worse on camera than the measured
condition. Picking a decode setting is a claim-affecting decision — `scripts/phase14_recall.py`
itself notes that a decode setting chosen to make a recall number look better is the same category
of error as a threshold chosen after seeing results — so it is surfaced here for the 14-11 human
checkpoint rather than settled by the executor.

## Known Stubs

None. Every code path is wired to real data. `checkpoints/persona_adapter.pt` does not exist yet —
plan 14-11 produces it — and the demo degrades by refusing to build with a named message, which is
14-UI-SPEC's specified behavior rather than a stub.

## Throwaway artifacts

An **untrained** `checkpoints/persona_adapter.pt` was fabricated in the worktree purely to execute
`build_demo()` and the callbacks (the plan's own verification is source-level only, which would
have left runtime API errors — `gr.Code` kwargs, `.input()`, `concurrency_id` on `.then()` — to
surface on camera in 14-11). **It was deleted before this summary and was never copied to the main
repo.** `checkpoints/convbase_slim.pt` and `checkpoints/model_slim.pt` were APFS-cloned into the
worktree for the same purpose; both are gitignored and pre-existing in the main repo. The real,
taught adapter remains plan 14-11's output.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern, or schema change was introduced
beyond the plan's `<threat_model>`. The mitigations assigned to this plan are all in place:
T-14-22 (`weights_only=True`, `torch.load` never called directly), T-14-27 (kill-switch ordering,
`analytics_enabled=False`, `share=False`, empty stylesheets — all four pinned by tests), T-14-17
(fact-free process, asserted three ways including the transitive `sys.modules` check), T-14-28 and
T-14-06 (no merge, slider bounded `[48, 256]`), T-14-29 (single shared renderer), T-14-23
(fingerprint mismatch surfaced in-UI), T-14-30 (one `concurrency_id`), T-14-36
(`test_demo_app_frozen`).

## Verification Results

- `pytest -q tests/test_phase14_demo.py -rs` — 17 passed, 2 skipped (named)
- `pytest -q` (full suite) — **381 passed, 1 skipped** (the skip is pre-existing and unrelated)
- `ruff check . && ruff format --check .` — clean, 132 files
- `git diff cdd7786 HEAD -- scripts/demo_app.py` — **empty** (D-17 holds)
- `grep -c "cpu,dev,demo"` — 1 in each of `ci.yml`, `Makefile`, `CLAUDE.md`
- `grep -c "merge_lora\|merged_state_dict\|cache_examples" scripts/personalize_demo.py` — 0

## Commits

| Task | Commit    | Description                                                 |
| ---- | --------- | ----------------------------------------------------------- |
| 1    | `379a4de` | module surface — theme, forbid_ids, token panel, UI copy     |
| 2    | `2910e36` | Blocks UI, callbacks, main()                                 |
| 3    | `c18da24` | tests + `.[cpu,dev,demo]` parity in CI, Makefile, CLAUDE.md  |

## Self-Check: PASSED

All claimed files exist on disk (`scripts/personalize_demo.py`, `tests/test_phase14_demo.py`,
`.github/workflows/ci.yml`, `Makefile`, `CLAUDE.md`, this summary) and all three commit hashes
resolve in `git log`.
