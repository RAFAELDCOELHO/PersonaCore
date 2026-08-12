---
phase: 14-teach-then-recall-demo
verified: 2026-08-02T14:40:00Z
status: passed
score: 57/57 must-haves verified
overrides_applied: 0
re_verification:
  re_verified: 2026-08-12
  previous_status: gaps_found
  previous_score: 55/57 must-haves verified
  gaps_closed:
    - truth: "Importing scripts/phase14_recall.py loads zero fact strings into the process (plan 14-05)"
      evidence: "Fresh-interpreter probe, independent of the suite: imported scripts/personalize_demo.py, scanned all 2378 loaded modules' globals for 5 locked values. phase14_recall confirmed RESIDENT in sys.modules — so the scan reached the module that used to hold the hit, ruling out a false negative — and HITS == []. RECONCILIATION_A no longer embeds the value."
    - truth: "The demo process holds no locked fact value, by any path including a transitive import (plan 14-08)"
      evidence: "Same probe, same run: zero hits with personalize_demo imported at module level. Both enforcing tests were rewritten substring-aware and re-run green on 2026-08-12 (2 passed in 4.27s): tests/test_phase14_scoring.py::test_no_fact_strings_at_import (now uses _strings_in, a depth-capped recursion reaching strings nested in tuples/dicts, replacing the exact-equality predicate that could not see substring embedding) and tests/test_phase14_demo.py::test_demo_process_is_fact_free (now spawns a fresh interpreter, scans every repo-owned module for all 10 locked + soft values, and asserts both that the scan reached personalize_demo and phase14_recall and that result['hits'] == [])."
  gaps_remaining: []
  regressions: []
  note: "Re-stamp only — NO code change was made in this pass. Both fixes landed during Phase 14/15 execution, after the 2026-08-02T14:40Z verification timestamp, and this file was simply never re-stamped. The gaps below are retained as the historical record of what was found and fixed; they are closed, not open."
gaps:
  - truth: "Importing scripts/phase14_recall.py loads zero fact strings into the process — the demo can read the budget without holding the answers (plan 14-05)"
    status: failed
    reason: "The module-level constant RECONCILIATION_A (1302 chars) embeds the locked fact value 'zorp' twice as report prose. Verified by direct scan of phase14_recall module globals in a fresh process: 1 hit. The enforcing test uses an exact-equality predicate (`getattr(driver, name) in forbidden`) that can only catch a whole-string match, so a value embedded in a longer string is invisible to it."
    artifacts:
      - path: "scripts/phase14_recall.py"
        issue: "RECONCILIATION_A (line 1379) contains the locked value 'zorp' in two places: the persona-span probe quotes at lines ~1385 and ~1394"
      - path: "tests/test_phase14_scoring.py"
        issue: "test_no_fact_strings_at_import (line 298) predicate is exact string equality against the forbidden set — structurally unable to detect substring embedding, so it passes while the invariant is violated"
    missing:
      - "Move RECONCILIATION_A's probe quotes out of the module-level constant (e.g. read them from 14-RESEARCH at report-write time, or redact the value to `<taught value>`)"
      - "Change the test predicate from `value in forbidden` to `any(v in value.lower() for v in forbidden)` so substring embedding is caught"
  - truth: "The demo process holds no locked fact value, by any path including a transitive import — it imports an integer, not the answers (plan 14-08)"
    status: failed
    reason: "Same root cause. scripts/personalize_demo.py imports phase14_recall at module level, so 'zorp' is resident in the demo process. Confirmed by importing personalize_demo in a fresh interpreter and scanning every loaded module's globals: exactly one hit, phase14_recall.RECONCILIATION_A. No prompt path reads it, so no user-visible leak occurs — but the stated invariant is false as written."
    artifacts:
      - path: "scripts/personalize_demo.py"
        issue: "module-level `from phase14_recall import ... render_context_dump` pulls the whole module, including RECONCILIATION_A, into the demo process"
      - path: "tests/test_phase14_demo.py"
        issue: "test_demo_process_is_fact_free (line 470) only asserts that 'phase14_factset' and 'teach_persona' are absent from sys.modules — it never inspects the strings that ARE resident, so it cannot see a value hard-coded directly in phase14_recall"
    missing:
      - "Extend test_demo_process_is_fact_free to scan loaded module globals for embedded locked values, not just sys.modules membership"
      - "Once RECONCILIATION_A is fixed, this truth holds without further change"
deferred: []
---

# Phase 14: Teach-Then-Recall Demo — Verification Report

**Phase Goal:** The core-value proof — a LoRA adapter on the frozen conversational base recalls taught user facts in a clean room: fresh process, empty prompt, no store, with a live memory on/off toggle
**Verified:** 2026-08-02T14:40:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Headline

**All four ROADMAP success criteria are VERIFIED against the codebase, not against SUMMARY claims.**
Every headline number in `results/phase14_recall_report.md` was independently re-derived by this
verifier from the raw transcripts, and the live memory toggle was behaviorally reproduced in a
fresh process. The phase goal is achieved.

**Two plan-level must-haves are observably FALSE**, both from one root cause: a locked fact value
(`zorp`) is hard-coded into a module-level report-prose constant in `scripts/phase14_recall.py`,
which the demo imports. The two tests written to enforce "no fact value in this process" use
predicates too weak to detect it. No prompt, no score, and no user-visible behavior is affected —
but a clean-room invariant that the phase asserts twice is not actually true, and its guard rails
do not guard.

## Goal Achievement

### Observable Truths — ROADMAP Success Criteria (the contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 5-10 atomic user facts taught via ~20-50 template/hand-written paraphrases per fact (zero external-API augmentation) into a LoRA adapter trained on the frozen conversational base | VERIFIED | Loaded `scripts/phase14_factset.py` in-process: `LOCKED_FACTS`=8 core + `SOFT_TIER_FACTS`=2 soft = **10 facts**, one per distinct slot. Counted taught renders per fact across `TAUGHT_FAMILY_IDS` {F1,F2,F4,F5,F6}: **22 paraphrases/fact** (teaching log independently asserts "paraphrases/fact inside (20, 50) for 10 facts"). All paraphrases are pure-Python template functions in `FAMILIES`; grep for `requests`/`urllib`/API hosts across all four phase-14 scripts returns **zero hits** — no external-API augmentation is possible. `checkpoints/persona_adapter.pt` loaded with `weights_only=True`: 72 tensors, **331,776 parameters**, `lora_config` r=8/alpha=16 over 6 projections, `base_fingerprint` = `{git_sha: 04e724c6…, step: 4000, val_loss: 1.5235939979553224}` matching `convbase_slim.pt`. Teaching log: `canary passed: all lora_ moved, base bit-untouched`. |
| 2 | Fresh-process, empty-prompt scripted recall meets pre-registered thresholds, with a context-token dump proving no prompt leakage and the base-without-adapter control failing closed-book | VERIFIED | **Thresholds pre-registered:** `TAUGHT_THRESHOLD = 0.2486` became a literal at `921a6bc` (07:58:13 -0300); the recall driver ran at `6f873a5` (08:32) producing the report at 09:10 local. `git merge-base --is-ancestor 921a6bc 6f873a5` = true. **Result clears both the corrected AND the originally-derived thresholds** (taught 0.4921 > 0.4095; held-out 0.3483 > 0.3311), which defuses the "threshold lowered after calibration" concern entirely. **Fresh process:** teaching pid 27638 (teaching log) → recall pid 32721 (report + transcripts) — a real process boundary with the adapter file on disk in between. **Empty prompt:** `build_recall_prompt(tok, "")` returns exactly `[8187, 8185, 8186]` (executed); every scored dump decodes to `<\|system\|><\|user\|>{question}<\|assistant\|>` with a bare, zero-content system span. **No leakage — independently re-verified:** parsed all **540** `decoded :` dumps out of `results/phase14_transcripts.md` and checked each against all 10 locked values: **0 hits**. `assert_no_value_in_prompt` (line 396) is a real two-level guard (normalized-string absence + contiguous-id-run absence) raising `SystemExit`. **Control fails closed-book:** re-derived from raw transcripts, closed-book control = **0/2430 = 0.0000** over the same 270 prompts. Reproduced independently: adapter OFF answers `what is your dog's name?` with `i am a cop. i am a cop.` while ON answers `my dog is named zorp.` |
| 3 | Taught phrasings and never-seen phrasings scored and reported separately (learning vs memorization), with all transcripts committed — failures included | VERIFIED | Re-derived every tier rate from `results/phase14_transcripts.md` by regex, independent of the report: core taught **496/1008 = 0.4921** (112 questions), core held-out **326/936 = 0.3483** (104 questions), closed-book **0/2430** (270), soft tier **201/486 = 0.4136** (54). **Every number matches the report exactly.** Separate report sections and separate gate rows confirmed. **Held-out is genuinely never-seen — independently re-verified:** memmapped `data/persona_real_train.bin` (20,036 tokens) and searched for each of the **130** `heldout_questions()` id sequences as a contiguous subsequence: **0 of 130 present**. Transcripts are unfiltered: 540 question blocks × 9 draws = 4,860 completions, misses printed verbatim next to hits (`seeded #1 · miss` … `> i go by swings and swings.`). |
| 4 | In the Gradio demo, the adapter toggles on/off live — same process, same prompt, memory on/off | VERIFIED | **Behaviorally reproduced by this verifier** in one process (pid 22135), CPU, real `convbase_slim.pt` + real `persona_adapter.pt`, no server launched: 36 LoRA wrappers injected (matches the "36 boolean flags" claim); flipping `set_adapter_enabled` between identical `build_recall_prompt` id sequences gave ON `my name is quillon.` / OFF `i am a college student…`, ON `i live on marrowgate.` / OFF `i live in the country…`, ON `i was born in 1987.` / OFF garbage — with `render_context_dump` **byte-identical across ON and OFF on all four questions**. `eject_adapter` left 0 wrappers and the bare base still chatted (`i am doing well, just finished cooking.`). Wiring confirmed in `scripts/personalize_demo.py`: `memory_box.input(on_toggle, …)` → `set_adapter_enabled(model, bool(enabled))` on the live model object; `on_ask` rebuilds the prompt per turn from `build_recall_prompt` and never concatenates history. Browser-level checks (zero third-party origins, streaming monotonic 0/65 shrink, panel stationary) are human-recorded in `14-VALIDATION.md` Part B with measured values. |

**Roadmap score: 4/4 VERIFIED.**

### Observable Truths — Plan-Level Must-Haves (sampled and checked)

| Plan | Truth | Status | Evidence |
|------|-------|--------|----------|
| 14-01 | The empty-question prompt is exactly `[8187, 8185, 8186]` | VERIFIED | Executed `build_recall_prompt(tok, "")` → `[8187, 8185, 8186]` |
| 14-01 | One function builds the recall prompt; harness and demo both call it | VERIFIED | `personacore.dialogue.serialize.build_recall_prompt`; imported by `phase14_recall.py` and `personalize_demo.py`; `ASSISTANT_ID` resolved from `SPECIAL_TOKENS`, never the literal 8186 |
| 14-02 | Every close-call rejection quotes the base completion that triggered it | VERIFIED | `results/phase14_factset_report.md` § *Close-Call Rejections (D-03, human-recorded)*, 22 close-call references; verdict **ADAPT** recorded |
| 14-03 | Locked fact set is a committed constant with a recorded gate SHA | VERIFIED | `LOCKED_FACTS`/`SOFT_TIER_FACTS`/`GATE_REJECTED_CANDIDATES`/`VALUE_TOKEN_CENSUS` are module constants; `FACTSET_GATE_SHA = 446afab…` resolves to the real commit "docs(14-02): record D-06 verdict ADAPT — 8 core + 2 labelled soft" |
| 14-04 | Teaching episodes mask exactly the answer span plus the terminating eos | VERIFIED | Executed `encode_dialogue`: masked span decodes to `my dog is named zorp.<\|endoftext\|>` — answer + eos, nothing else |
| 14-04 | No held-out question's id sequence appears anywhere inside the teaching bin | VERIFIED | Re-run independently on the real bin: 0/130 present |
| 14-04 | The bins builder refuses to run until the fact-set verdict reads GO or ADAPT | VERIFIED | `_require_go_verdict` present; teaching log line 1: `D-06 verdict: ADAPT — proceeding with arm 'real'` |
| 14-05 | The generation budget is derivable without running anything | VERIFIED | `RECALL_MAX_NEW_TOKENS = 48` = max census (8) + preamble (32) + tail (8), rounded to step 8; `assert_values_fit` raises `SystemExit` on census drift |
| **14-05** | **Importing `phase14_recall.py` loads zero fact strings into the process** | **FAILED** | `RECONCILIATION_A` (module-level, 1302 chars) contains `zorp` twice. See Gaps. |
| 14-06 | Every question's exact prompt token ids written into evidence before the model is called | VERIFIED | `run_scored_recall` calls `render_context_dump` then `assert_no_value_in_prompt` then `complete_question`, in that order; 540 dumps in the committed transcripts |
| 14-06 | Any locked fact value in any prompt aborts with `SystemExit` | VERIFIED | `assert_no_value_in_prompt` two-level check via `_prove`; the run completing is the proof |
| 14-07 | Trains only the 331,776 LoRA parameters; frozen base bit-identical afterward | VERIFIED | `snapshot_params` canary; teaching log `canary passed: all lora_ moved, base bit-untouched`; adapter blob holds only LoRA tensors |
| 14-07 | An arm that has already produced outputs refuses to re-run | VERIFIED | `refuse_if_exists` (line 203) raises `SystemExit` naming the file |
| 14-08 | `scripts/demo_app.py` is byte-for-byte unchanged (D-17) | VERIFIED | `git log -- scripts/demo_app.py` last touched at `cdd7786` (Phase 8); zero commits since 2026-08-01 |
| 14-08 | Demo serves zero remote stylesheets / makes zero outbound calls | VERIFIED | `test_no_remote_stylesheets`, `test_served_page_loads_nothing_third_party`, `test_analytics_killswitch_precedes_gradio_import` all pass; browser-confirmed in `14-VALIDATION.md` (only origin: `127.0.0.1:7860`) |
| 14-08 | Memory ON/OFF flips 36 boolean flags, same process, same prompt, panel proves context unchanged | VERIFIED | Reproduced: 36 wrappers, panel byte-identical, answers differ |
| **14-08** | **The demo process holds no locked fact value, by any path including a transitive import** | **FAILED** | Fresh-process scan of every loaded module global after `import personalize_demo`: 1 hit — `phase14_recall.RECONCILIATION_A` contains `zorp`. See Gaps. |
| 14-09 | Thresholds stop being `None` and become committed literals before the real recall run exists | VERIFIED | Git ancestry proves ordering; both threshold sets published side by side in the calibration report; verdict ADAPT recorded |
| 14-10 | The D-20 three-part reconciliation is committed as report text BEFORE the run | VERIFIED | `RECONCILIATION_A/B/C` introduced at `48d557a` (08:21:48), ancestor of the run driver `6f873a5` (08:32:17) |
| 14-10 | Adapter-off logits bit-identical to the un-adapted base on real weights, on CPU | VERIFIED | Report Control 3: `torch.equal` True on all 5 prompts, max abs diff **0.0**; independently corroborated — adapter OFF reproduces base-characteristic completions |
| 14-10 | Soft tier gets a NAMED report section stating it has no bearing on the thresholds | VERIFIED | `## Soft Tier — Excluded From The Gate (D-05)` present with explicit "no bearing" language |
| 14-10 | Threats-to-validity names the deliberate exclusion of reversed phrasings (D-22) | VERIFIED | `## Threats To Validity` § 1, cites arxiv 2309.12288 and scopes the held-out claim |
| 14-11 | D-12: a missed threshold recorded unamended; ship decision in a separate post-verdict section | VERIFIED | `## Verdict` records ADAPT verbatim with both qualifications; `## Ship Decision — post-verdict, discretionary` correctly empty (no gate was missed) |

**Merged score: 55/57 truths verified** (4 roadmap SCs + 53 deduplicated plan truths).

### Deferred Items

None. Phase 15 (Figures & Writeup) covers `REPORT.md`/`README`/`demo.ipynb` narrative, not the
integrity of Phase 14's own committed evidence artifacts. The two gaps are not deferrable.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/personacore/dialogue/serialize.py` | `build_recall_prompt` — D-18 single source of truth | VERIFIED | Present, substantive (138 lines), imported by harness + demo, `ASSISTANT_ID` from locked registry |
| `src/personacore/generation/text.py` | `generate_text_from_ids` + cumulative variant | VERIFIED | Present; cumulative form drives the demo's streaming callback |
| `scripts/phase14_factset.py` | Pools, locked facts, family grammar | VERIFIED | 40 KB; `CANDIDATE_POOL`, `LOCKED_FACTS`, `FAMILIES`, `render_family`, `FACTSET_GATE_SHA` all real and loadable |
| `scripts/phase14_factset_gate.py` | Gated census + guessability report driver | VERIFIED | 20 KB, produced the 67 KB committed report |
| `scripts/teach_persona.py` | Masked-bin builder + LoRA training half + decision rule | VERIFIED | 89 KB; `build_bins`, `train_arm`, `refuse_if_exists`, verdict gate all present and exercised by the real run |
| `scripts/phase14_recall.py` | Pre-registration, scoring, 3 controls, report writer | VERIFIED (with defect) | 100 KB; all named functions present and exercised. Carries the `zorp` literal — see Gaps |
| `scripts/personalize_demo.py` | Blocks demo: live toggle, Reset, token panel, floored slider | VERIFIED | 35 KB; `build_demo` wired end to end; behaviorally reproduced |
| `results/phase14_factset_report.md` | Committed gate evidence + verdict | VERIFIED | 67 KB, `## Verdict` = ADAPT with recorded deviation |
| `results/phase14_calibration_report.md` | Three arms + four derivations + verdict | VERIFIED | 22 KB, `## Verdict` = ADAPT, both threshold sets side by side |
| `results/phase14_recall_report.md` | DEMO-05/06 verdict, 3 controls, D-20 reconciliation | VERIFIED (with defect) | 48 KB, all pre-registered sections present. One false sentence — see WARNINGS |
| `results/phase14_transcripts.md` | Every completion with exact prompt ids, failures included | VERIFIED | 666 KB, 540 question blocks, 4,860 completions, 0 dumps carrying a fact value |
| `checkpoints/persona_adapter.pt` | 1.35 MB LoRA adapter produced in its own process | VERIFIED | 1,350,523 bytes; sha256 `226f2ae5…` matches the report's provenance block exactly |
| `tests/test_recall_prompt.py` etc. (5 test files) | CPU-only regression pins | VERIFIED (2 weak predicates) | All present; suite green. Two predicates cannot detect what their docstrings claim — see Gaps |
| `.github/workflows/ci.yml`, `Makefile` | `cpu,dev,demo` extra so demo tests run in CI | VERIFIED | Both carry `pip install -e ".[cpu,dev,demo]"` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `serialize.py` | `tokenizer.special.SPECIAL_TOKENS` | `ASSISTANT_ID` from registry | WIRED | `SPECIAL_TOKENS[_ASSISTANT]`, literal 8186 never retyped |
| `phase14_recall.py` | `dialogue.build_recall_prompt` | `render_context_dump` + `complete_question` | WIRED | Both call sites confirmed; AST test pins `persona=` to the fairness control only |
| `phase14_recall.py` | `checkpoint.load_slim` / `lora.load_adapter_weights` | fingerprint trio | WIRED | Provenance block shows the trios agree, no mismatch |
| `phase14_recall.py` | `evaluation.masked_perplexity` | D-11.2 collapse control | WIRED | Called with `forbid_ids=forbid` on both arms; denominators asserted equal |
| `phase14_recall.py` | `lora.adapter_disabled` | D-11.3 bit-identity + closed-book control | WIRED | Both controls route through it |
| `teach_persona.py` | `dialogue.encode_dialogue` | single shared encoder | WIRED | No second masking implementation exists |
| `teach_persona.py` | `training.data.get_batch_memmap_masked` | post-build smoke | WIRED | Teaching log: `smoke draw: x/y (4, 256), y carries -100 — ok` |
| `teach_persona.py` | `checkpoint.export_adapter` | `base_fingerprint` read not recomputed | WIRED | Adapter blob's trio byte-matches the base checkpoint's |
| `personalize_demo.py` | `phase14_recall.RECALL_MAX_NEW_TOKENS` | imported integer, never re-derived | WIRED | Confirmed `= 48`, `type int`; slider `minimum` bound to it |
| `personalize_demo.py` | `lora.set_adapter_enabled` | 36 boolean writes | WIRED | `memory_box.input(on_toggle, …)` → live model |
| `personalize_demo.py` | `checkpoints/persona_adapter.pt` | loads the adapter teaching exported, third process | WIRED | `ADAPTER_PATH` + `load_adapter(expected_fingerprint=…)` |
| `personalize_demo.py` | `phase14_recall` (module) | imports the budget integer | **PARTIAL** | The import also drags `RECONCILIATION_A` and its `zorp` literal into the demo process — the stated "integer, not the answers" contract is violated |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `results/phase14_recall_report.md` | tier `k/N` rates | `run_scored_recall` over real MPS generation | Yes — 4/4 tier rates re-derived from raw transcripts match to the digit | FLOWING |
| `results/phase14_transcripts.md` | completions + prompt ids | `complete_question` → `generate_text_from_ids` | Yes — 4,860 real completions, misses included | FLOWING |
| `checkpoints/persona_adapter.pt` | LoRA tensors | `train_arm` on real bins | Yes — 331,776 params, final_train_loss 0.6205, produces measurable recall | FLOWING |
| `personalize_demo.py` token panel | `panel_text` | `render_context_dump(tok, question)` | Yes — reproduced, byte-identical ON/OFF, id length does not grow with turns | FLOWING |
| `personalize_demo.py` chat bubble | `accumulated` | `generate_text_from_ids_cumulative` on live model | Yes — reproduced live, answers differ by toggle state | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite green | `.venv/bin/python -m pytest -q` | `388 passed, 1 skipped` in 110.83s | PASS |
| Lint clean | `.venv/bin/ruff check . && ruff format --check .` | `All checks passed!` / `132 files already formatted` | PASS |
| Empty-prompt id sequence | `build_recall_prompt(tok, "")` | `[8187, 8185, 8186]` | PASS |
| Adapter param count | `torch.load('checkpoints/persona_adapter.pt')` | 72 tensors, 331,776 params | PASS |
| Live memory toggle, same process/prompt | in-process ON/OFF over 4 questions | ON recalls (`my name is quillon.`), OFF fails closed-book; panel byte-identical | PASS |
| Reset / eject | `eject_adapter(model)` then generate | 0 wrappers left, base still chats | PASS |
| Tier rates re-derived from raw transcripts | regex parse of `phase14_transcripts.md` | 496/1008, 326/936, 0/2430, 201/486 — all match the report | PASS |
| Context-dump leakage | scan all 540 dumps against 10 locked values | **0 dumps carry a fact value** | PASS |
| Held-out leakage into teaching bin | contiguous-subsequence search over `persona_real_train.bin` | **0 of 130 held-out questions present** | PASS |
| Demo process fact-free | scan loaded module globals after `import personalize_demo` | **1 hit — `phase14_recall.RECONCILIATION_A` contains `zorp`** | **FAIL** |
| `demo_app.py` frozen (D-17) | `git log -- scripts/demo_app.py` | last touched Phase 8, zero phase-14 commits | PASS |
| Pre-registration ordering | `git merge-base --is-ancestor 921a6bc 6f873a5` | true — thresholds locked 34 min before the run driver | PASS |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| — | — | — | SKIPPED |

No probe convention exists in this repository (`find . -name 'probe-*.sh'` → none) and no PLAN
declares one. The phase's equivalent contract is the pytest suite plus the two script proofs
(`teach_persona.py`, `phase14_recall.py`), both of which exited 0 and left committed artifacts;
the suite was re-run by this verifier.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DEMO-05 | 14-01…14-11 | Teach-then-recall clean-room demo — 5–10 atomic facts, ~20–50 paraphrases (no external-API augmentation), LoRA on frozen conversational base, fresh-process empty-prompt scripted recall with pre-registered thresholds, base-without-adapter control | SATISFIED | 10 facts × 22 paraphrases; 331,776-param adapter with frozen-base canary; pid 27638 → 32721 boundary; thresholds locked before the run and cleared on both the corrected and original derivations; control 0/2430 |
| DEMO-06 | 14-04…14-11 | Held-out-phrasing recall split — taught vs never-seen scored and reported separately | SATISFIED | Separate tiers with separate gates (0.4921 / 0.3483); held-out is entirely held-out template FAMILIES, independently proven absent from the teaching bin (0/130) |
| DEMO-07 | 14-01, 14-08, 14-10, 14-11 | Adapter on/off toggle in the Gradio demo — same process, same prompt, memory on/off live | SATISFIED | Toggle reproduced in-process; 36 flags; panel byte-identical while answers differ; adapter-off bit-identity max diff 0.0; browser pass recorded in `14-VALIDATION.md` |

**No orphaned requirements.** `.planning/REQUIREMENTS.md` maps exactly DEMO-05/06/07 to Phase 14
and all three are claimed by phase-14 plans.

**Bookkeeping note (INFO):** `.planning/REQUIREMENTS.md` lines 116-118 still read
`| DEMO-05 | Phase 14 | Pending |` (and 06, 07) while `ROADMAP.md` marks Phase 14 Complete. The
traceability table was not updated at phase close.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/phase14_recall.py` | 1379 | Locked fact value `zorp` hard-coded in module-level constant `RECONCILIATION_A`, transitively resident in the demo process | Blocker (must-have) | Violates the plan-14-05 and plan-14-08 clean-room import invariants as literally stated. No prompt path reads it, so no user-visible leak |
| `tests/test_phase14_scoring.py` | 330-335 | Enforcement predicate is exact string equality (`getattr(driver, name) in forbidden`) where the docstring claims substring-level protection | Blocker (must-have) | Test passes while the invariant it names is false — the guard rail does not guard |
| `tests/test_phase14_demo.py` | 483-493 | Enforcement is `sys.modules` membership only; never inspects resident string values | Blocker (must-have) | Same — structurally blind to a value hard-coded directly in `phase14_recall` |
| `results/phase14_recall_report.md` | 62 | False methodological claim: "the SAME per-question seeds — so the arms are paired" | Warning | See WARNINGS below |
| `scripts/phase14_recall.py` | 594-595 | Same false pairing claim in `complete_question`'s docstring | Warning | Propagates the error into the code as documentation |
| `scripts/phase14_recall.py` | 1538-1544 | `assert_report_not_clobbered` splits on `## Verdict` and lands in the ship-decision comment, which also contains that literal | Warning | Every legitimate re-run needs `--force`, which disables the guard entirely |
| `scripts/teach_persona.py` | 648-654 | `masked_perplexity` called without `forbid_ids` while `phase14_recall` passes it, yet both reports describe them as the same instrument | Warning | Divergence measured at +0.0083%; did not flip the D-15 verdict |

**Debt-marker gate: CLEAN.** No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK` markers in any phase-14
modified file. (The three `PLACEHOLDER` grep hits are the constant name `TEXTBOX_PLACEHOLDER`, a
UI copy string — not debt.)

## WARNINGS — judged against the success criteria

These are the code-review findings I was asked to adjudicate for goal impact.

### CR-01 — closed-book control is not seed-paired; the report says it is

**Confirmed in code.** `run_scored_recall` seeds via `enumerate(items)` →
`complete_question(..., index=index)` → `question_seed(i) = SEED + i`. The three adapter-ON arms
each restart at index 0 (112, 104, 54 items); `run_closed_book_control` receives the
concatenation `core_taught + core_held_out + soft_taught + soft_held_out` and enumerates 0..269.
Only the first 112 align — **158 of 270 questions draw from different generator seeds across
arms**. `results/phase14_recall_report.md:62` and `phase14_recall.py:594-595` both assert pairing.

**Verdict on criterion 2: does NOT undermine it.** Criterion 2 requires "the base-without-adapter
control failing closed-book." That is a measurement of the control arm alone, and it is
unambiguous: **0 successes across 2,430 completions on 270 prompts** — re-derived by this verifier
from the raw transcripts, not read from the report. A total-zero result has no seed-sensitivity to
lose: no reseeding of a control that never once produced a hit can turn it into a pass, so pairing
is not load-bearing for the number. I independently reproduced the qualitative result (adapter OFF
answers `what is your dog's name?` with `i am a cop. i am a cop.`) on a seed of my own choosing.

**What it DOES undermine is the stated rationale, and only that.** The sentence "so the arms are
paired, not merely comparable" is false as written in a committed evidence artifact of a project
whose core value is that the claim must be true. It would become load-bearing the instant a
closed-book arm returned non-zero. The correct disposition is a one-line correction to the report
plus a two-line fix to pass a tier-relative offset into the control — not a re-run.

**Classification: WARNING**, not a blocker. Criterion 2 stands on the measurement; the report
prose overstates why.

### CR-02 — the clobber guard is defeated by its own output

**Confirmed.** `SHIP_DECISION_HEADER` contains the literal `` `## Verdict` above. ``, so a written
report has two `## Verdict` occurrences and `.split("## Verdict")[-1]` lands in the ship-decision
comment, which never contains `PENDING`. Every legitimate re-run needs `--force`, which skips the
check entirely. **No success criterion depends on the guard**; the verdict is recorded and the
ship-decision section is correctly empty. Classification: **WARNING** — a re-run-safety defect on
committed evidence.

### WR-01 — collapse-control instrument divergence

**Confirmed.** `teach_persona.py:648` omits `forbid_ids`; `phase14_recall.py:1229` passes it. Both
reports call them the same instrument. The divergence is real but tiny (teaching log reports
+27.20%, recall report +27.16%) and each script is internally consistent — both of its own arms
use the same setting, so each delta is a valid within-script comparison. The D-15 verdict
(trigger tripped, descriptive, no gate) is identical either way. Classification: **WARNING** —
a false "same instrument" claim, not a wrong number.

## Gaps Summary

The phase goal is achieved. Every roadmap success criterion is backed by evidence I re-derived
myself rather than read from a SUMMARY: the tier rates recomputed from raw transcripts, the
zero-leakage claim re-checked across all 540 context dumps, the held-out split re-proven absent
from the teaching bin, and the live toggle reproduced in a fresh process where the adapter recalls
`quillon`/`zorp`/`1987` with the memory on and produces base garbage with it off, from a
byte-identical prompt. That is the core-value proof this phase existed to produce, and it holds.

The two gaps are one defect wearing two labels. `scripts/phase14_recall.py` hard-codes the locked
value `zorp` inside `RECONCILIATION_A`, a module-level report-prose constant quoting a
14-RESEARCH probe. `scripts/personalize_demo.py` imports that module at load time, so the demo
process holds a taught fact value — which plan 14-05 and plan 14-08 each explicitly promise cannot
happen "by ANY path". Two tests were written to enforce exactly this and neither can see it:
`test_no_fact_strings_at_import` compares whole strings for equality against the forbidden set, so
a value embedded in a 1,302-character paragraph is invisible; `test_demo_process_is_fact_free`
only asserts two module names are absent from `sys.modules`, so a value typed directly into a
third module is out of its field of view entirely. Both tests pass. Both invariants are false.

Nothing user-visible is wrong. `RECONCILIATION_A` is consumed only by `write_recall_report`, never
by any prompt path, and all 540 committed context dumps are clean. The practical exposure is
narrow. But this phase's entire methodological posture is that its guarantees are structural
rather than conventional — the demo's own docstrings say so — and here the structure is absent
while the claim is made twice. For a portfolio project whose thesis is "the novel claim must be
true and demonstrable," an assertion that the process cannot hold the answers, made in a process
that holds one, is the kind of detail a hostile reviewer finds. It is also about twenty minutes of
work to close: redact the value in the constant, and change two test predicates from equality to
substring containment.

Three warnings sit alongside. All three are false statements about method rather than wrong
numbers: the closed-book control is not seed-paired though the report says it is (the 0/2430
result is unaffected and criterion 2 stands), the report's own clobber guard is defeated by its
own output text, and the two collapse-PPL call sites use different `forbid_ids` settings while
being described as one instrument. Each is a small correction to committed evidence; none moves a
gate.

---

_Verified: 2026-08-02T14:40:00Z_
_Verifier: Claude (gsd-verifier)_
