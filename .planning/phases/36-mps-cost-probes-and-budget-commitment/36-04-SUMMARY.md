---
phase: 36-mps-cost-probes-and-budget-commitment
plan: 04
subsystem: v6.0 MPS cost probes (COST-01)
tags: [probe-driver, E5, E6, D-07, D-08, D-16, B1, B2, PERS-06, launchagent]
requires:
  - scripts/phase36_probe.py core + E1 (36-03): STAGES, RECORD_BUILDERS, run_front, emit, DrawTimer, silenced, e1_components, prove_published_adapter
  - scripts/phase14_recall.py: load_adapted_model, draw_all, assert_no_value_in_prompt, SEED
  - scripts/phase19_erasure.py: ablate_components, value_span_nll_mean
  - scripts/phase18_extraction.py: _frame_preamble, ADMISSIBLE_NLL_FRAME, reference_set_for
  - scripts/phase17_persona_gate.py: build_unadapted_base, TOKENIZER_PATH
  - scripts/phase14_factset_gate.py: probe_guessability
provides:
  - scripts/phase36_probe.py: adapted_model, stage_e6, _e6_stages, e6_a2_context_beside, stage_e5, _e5_stages
  - artifacts/com.personacore.phase36.probe.plist
  - tests/test_phase36_probe.py: _e6_light, _e5_light, _e5_e6_live_fixture / e5_e6_live, plist mirror test
affects: [36-05 (e3/e2 + preflight extend the same registries), 36-06 (reads the E5/E6 record shapes), 36-07 (loads the plist, runs the probes)]
tech-stack:
  added: []
  patterns: [in-place PERS-06 assertion before every draw_all, readings bound only to locals consumed for completions/len, signature-bound stand-in for an adapter CI cannot have]
key-files:
  created:
    - artifacts/com.personacore.phase36.probe.plist
  modified:
    - scripts/phase36_probe.py
    - tests/test_phase36_probe.py
decisions:
  - "E6 draws pass index i * K to draw_all (disjoint seed windows per slot, the caller convention draw_all's docstring names), not the plan's i"
  - "E5 clearance and scoring both run under silenced(); clearance keeps only completions in an in-memory cache that is deleted before scoring"
  - "emit dispatches the beside block per front: e1 -> phase31_beside, e6 -> e6_a2_context_beside"
requirements-completed: []
metrics:
  duration: ~45 min
  completed: 2026-10-02
---

# Phase 36 Plan 04: E5 and E6 inference fronts + the probe LaunchAgent Summary

This plan adds the two inference-only fronts and the LaunchAgent that runs every probe.

- **E6, anchor-context generation (D-07).** It loads the k = 78 erased adapter and builds one anchor context per locked slot: `[ASSISTANT_ID]` followed by the `ans1` preamble. Each context gets K = 48 draws through `draw_all`, and the PERS-06 assertion runs in place before each draw. Only seconds and counts are kept. The record also carries the A2-context per-question unit, read from the E1 probe's sidecar.
- **E5 (D-08).** This front has two samples:
  - The published Phase 17 clearance is re-run on the un-adapted base. That is one cached `probe_guessability` pass per slot, then one `exact_match_clean` per published value.
  - `value_span_nll_mean` runs per reference-set candidate on the k = 0 and k = 78 adapters.
  - No verdict, completion or NLL is kept.
- **The plist.** `artifacts/com.personacore.phase36.probe.plist` is mirrored against the Phase 31 agent.

`requirements-completed: []`: this plan contributes to COST-01. The orchestrator or verifier decides the ticks.

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | adapted_model + stage_e6 + E6 record with the A2-context beside | c119571 | scripts/phase36_probe.py, tests/test_phase36_probe.py |
| 2 | stage_e5 (clearance sample + scoring sample) + E5 record | 148a8d1 | scripts/phase36_probe.py, tests/test_phase36_probe.py |
| 3 | E5/E6 CPU live path via main(['run']) + real emit; the LaunchAgent plist + mirror test | efd6146 | tests/test_phase36_probe.py, artifacts/com.personacore.phase36.probe.plist |

## Verification (real output)

**Task 1**
- `pytest tests/test_phase36_probe.py -k "e6 and not live"` printed `4 passed, 59 deselected`.
- `pytest tests/test_phase14_scoring.py -k draw_all` printed `1 passed, 42 deselected`. This is the B2 check, and stage_e6 has no DRAW_ALL_ASSERTED_BY entry.
- `pytest tests/test_lora_inject.py tests/test_phase36_probe.py` printed `75 passed`.

**Task 2**
- `pytest tests/test_phase36_probe.py -k "e5 and not live"` printed `3 passed, 63 deselected`.
- `pytest tests/test_phase36_probe.py tests/test_lora_inject.py` printed `78 passed`.

**Task 3**
- The whole of `tests/test_phase36_probe.py`, run with `-rs`, printed `75 passed in 6.12s`. Nothing was skipped. The file has no `skipif`, `pytest.skip` or `importorskip` call; "skipif" appears only in two comments.
- `plutil -lint artifacts/com.personacore.phase36.probe.plist` printed `OK`.

**Plan verification set.** I ran `tests/test_phase36_probe.py`, `tests/test_phase36_prereg.py`, `tests/test_phase36_ledger.py`, `tests/test_phase36_caps.py`, `tests/test_phase35_prereg.py` and `tests/test_lora_inject.py` together. They printed `271 passed in 25.84s`.

**Repo-wide censuses over scripts/ and tests/.** These printed `324 passed in 49.89s`. The files were:
- test_phase14_scoring, test_phase17_stats, test_phase21_unit_continuation, test_phase23_ctrl, test_phase30_calibration
- test_tokenizer_oracle, test_phase21_sc5, test_phase20_correction, test_phase20_prereg, test_phase25_record
- test_phase22_dpsgd_ast, test_phase25_driver, test_phase23_resume_prereg, test_phase17_personas, test_phase31_probe

I did not run `tests/test_phase25_venue.py`; the executor rules leave it to the orchestrator.

**Lint.** `ruff check .` printed `All checks passed!` and `ruff format --check .` printed `335 files already formatted`. Together these are the content of `make lint`.

**The `== 10` census.** `grep -nE "(==|!=)\s*10([^0-9_]|$)" tests/test_phase36_probe.py` returned nothing.

**Real live values.** I called the fixture once by hand on CPU with the fixture base:
- E5 clearance: setup 0.0079 s, total 0.6955 s, eight `per_slot_seconds` of about 0.083–0.090 s, `candidates_matched` 24, and a match max of 1.21e-04 s.
- E5 scoring: for both k = 0 and k = 78, 56 candidates with `candidates_per_slot` [8, 8, 7, 7, 7, 6, 7, 6].
- E6: 384 draws (8 × 48), with 380 at the 4-token cap, and `total_seconds` 0.5864.
- Repetitions were 8 for both records.
- Captured stdout: `'[phase25_launch] pid=… \n[phase36_probe] e5 0.8 s\n[phase36_probe] e6 0.6 s\n'`.

**Mutation checks.** Each edit below was restored byte-identical afterwards, confirmed with `cmp`.
- Moving the E6 assertion after `draw_all` made `-k "e6 and not live"` print `2 failed`.
- Deleting the E6 assertion made `test_every_draw_all_call_site_asserts_something` fail with "scripts/phase36_probe.py::stage_e6 draws completions but calls neither ...".
- Binding the `exact_match_clean` result made the E5 tests print `1 failed`.
- Doubling the per-match rows also made the E5 tests print `1 failed`.

**Natural RED in Task 2.** Registering e5 failed two tests:
- `test_build_record_refuses_a_front_mismatch_and_an_unbuilt_front`: e5 now has a builder.
- `test_every_probe_function_has_a_cpu_test`: the census, until the tests were written.

**Premises measured true:**
- phase14_recall: `:597` assert_no_value_in_prompt, `:712` load_adapted_model, `:846` draw_all, `:147` SEED = 1337.
- phase19_erasure: `:275` ablate_components, `:2407` value_span_nll_mean, and `:2874` the pin's `load_adapter_weights(model, ablate_components(artifact, list(components)))`.
- phase18_extraction: `:1031` _frame_preamble, `:985` ADMISSIBLE_NLL_FRAME = "ans1", `:1126` the anchor context, `:1159` reference_set_for.
- phase17_persona_gate: `:85` CONVBASE_SLIM, `:86` TOKENIZER_PATH, `:159` build_unadapted_base, `:285-320` the cached loop, `:325-345` the per-value checks.
- phase14_factset_gate: `:111` probe_guessability, which prints nothing.
- 8 LOCKED_FACTS slots, equal to `phase17_personas.CORE_SLOTS`. QUESTIONS_PER_SLOT is 13, and every slot has 13 held-out questions.
- 24 PERSONA_FACTS values. Reference sets have [8, 8, 7, 7, 7, 6, 7, 6] candidates, 56 in total.
- 10 LOCKED + SOFT_TIER values.
- **D-07 / B2 measured.** On the real tokenizer, `assert_no_value_in_prompt` passes on all 8 real anchor contexts. These are `my name is `, `my dog is named `, `my cat is named `, `my sister is named `, `i live in `, `i live on `, `i was born in ` and `my house number is `, each 6–10 ids. The STOP-and-report branch did not trigger.
- **D-08 premise measured.** `phase17_persona_gate.py:285-345` generates once per slot. Questions are cached, and `start_index=len(probe_cache)` gives each batch its own seed window. Each of the 24 values is then checked by `exact_match_clean`, which is a string check. So clearance costs one probe pass per slot plus a per-candidate CPU check. It is not one generation per candidate. The E5 record states this in `configuration.clearance_unit`.

## Deviations from Plan

1. **[Rule 1] E6 draws use `index = i * K`, not the plan's `i`.**
   - draw_all's docstring (`phase14_recall.py:862-863`) leaves disjoint seed windows to the caller: "an attack passes `src_index * K` as `index`".
   - With `i`, slot i's samples would reuse seeds `SEED+i+s` that overlap slot i−1's window.
   - Timing is unaffected either way. The light test asserts `drew[2] == i * K`.
2. **[Orchestrator rule] The live fixture launches through `probe.main(["run", "--heartbeat", …, "--ledger", …, "--front", "e5", "e6"])`, not `probe.run_all(...)`.** Every new stage must be reachable from main. Both records are still emitted through the real `probe.emit(front, out_path=root/"emitted"/…)`.
3. **[Rule 3] The live fixture widens the forbid mask.**
   - The fixture wraps `phase16_persistence.resolve_forbid` so it also forbids ids whose standalone `tok.decode([id])` raises.
   - Measured: without the wrapper, every e5_e6_live test errored with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb5 in position 1`.
   - The trace runs `phase14_factset_gate.py:144 probe_guessability` → `:107 _probe` (strict `tok.decode`) → `bpe.py:209`.
   - The cause is the fixture base's random weights, which emit lone continuation-byte tokens. The real base decoded all 416 published completions.
   - The wrapper is fixture-only, is documented in the fixture comment, and leaves the instrument unchanged.
4. **[Rule 3] The live fixture also patches `phase14_factset_gate.PROBE_MAX_NEW_TOKENS = 4`.** The plan named only `RECALL_MAX_NEW_TOKENS`. It is the same "scale the shape, not the instrument" knob, applied to the clearance probe's budget.
5. **[Rule 2] The `adapted_model` stand-in calls the real `probe.prove_published_adapter()`.** That is the real function's first line. It makes the B1 `_sha256` spy non-vacuous: the fixture adapter is hashed, and nothing under `_GIT_ROOT/checkpoints`.
6. **The plist header comment was rewritten for Phase 36.** The plan said to change only Label, the script argument, the heartbeat and the log pair. The XML comment is not parsed. Copying it verbatim would have left "PHASE 31 (D-12) … phase31_probe.py run measures the ARCAL-01 point probe" inside the phase36 file. All parsed keys outside the five fields are identical to Phase 31's, and the mirror test asserts this.
7. **[Natural RED] `test_build_record_refuses_a_front_mismatch_and_an_unbuilt_front` now uses `e4`.** e4 is never a probe front, so it never gets a builder. It previously used `e5`, which gets a builder in this plan.
8. **[Rule 2] Invariants beyond the plan:**
   - stage_e5 proves `len(cache) == QUESTIONS_PER_SLOT × slots`, which is the gate's own `:319-320` check, and `matched == published values`.
   - `e6_a2_context_beside` refuses unless the E1 sidecar holds exactly 2 runs.
   - The E5 scoring loop also runs under `silenced()`.
9. **`per_slot_draw_seconds_mean` is the mean of that slot's K DrawTimer rows,** which is per-draw seconds. It is not the slot's wall time divided by K, so decode overhead stays out of the draw unit, as in E1.
10. **AST "same loop" check.** The assertion and the draw are matched by the enclosing `For` node's `lineno`, because `_stage_calls` parses the module once per call.
11. **`preflight()` was not extended.** Plan 36-04 has no preflight task. 36-05 Task 3 owns "preflight + the main(['run']) end-to-end dispatch test", and the carried note's "36-04/05" was imprecise. `preflight()` still refuses e3 and e2 until 36-05 registers them, which is intended.
12. **Command forms.** I ran `.venv/bin/python -m pytest` and `ruff check . && ruff format --check .` in place of the plan's `.venv/bin/pytest` and `make lint`, as the executor rules require.
13. **TDD gate.** Each task is one `feat(36-04)` commit, the same convention as 36-02 and 36-03. The RED evidence is the natural Task 2 RED, the B2 RED in test_phase14_scoring and the mutation checks above.

## Names wave 5 (36-05) and later must extend

**New module-level defs in `scripts/phase36_probe.py`.** The census requires each to be called as `probe.<def>(…)` in the test file.
- `adapted_model(device, k) -> (model, tok, forbid)`. It calls `prove_published_adapter()` and then `phase14_recall.load_adapted_model(device)`. When k > 0 it also applies `load_adapter_weights(model, phase19_erasure.ablate_components(artifact, e1_components()[:k]))`.
- `stage_e6(state)`. The heartbeat stages are `e6_setup`, then `e6_anchor` with shape = slot.
- `_e6_stages(stages) -> (stages minus configuration, len(per_slot_draw_seconds_mean))`.
- `e6_a2_context_beside()`, which reads `run_sidecar("e1")`.
- `stage_e5(state)`. The heartbeat stages are `e5_clearance`, then `e5_scoring_k0` and `e5_scoring_k78`.
- `_e5_stages(stages) -> (stages minus configuration, len(clearance.per_slot_seconds))`.

**Registries and emit.**
- `STAGES` and `RECORD_BUILDERS` now hold e1, e6 and e5. 36-05 adds e3 and e2.
- `emit` takes its beside block from `{"e1": phase31_beside, "e6": e6_a2_context_beside}.get(front, lambda: None)()`.

**E6 record.**
- `stages`: `{setup_seconds, per_slot_draw_seconds_mean[8], draws (= 8 × 48), at_cap_draws, draw_seconds_spread{n,min,median,max}, total_seconds}`.
- `configuration`: `{arm: "erased", k: 78, K: 48, anchor_slots: 8, frame: "ans1", seed: 1337, context: <D-07 string>}`.
- Top level: `a2_context_from_e1: {a2_context_question_k48_seconds_high, path: "data/probe36_e1_run.json"}`.
- `repetitions` is 8.

**E5 record.**
- `stages.clearance`: `{setup_seconds, per_slot_seconds[8], match_seconds_spread, candidates_matched (24), total_seconds}`.
- `stages.scoring`: `{adapters: [{k: 0, …}, {k: 78, …}], candidate_seconds_spread}`. Each adapter row is `{k, setup_seconds, per_slot_mean_candidate_seconds[8], candidates_per_slot[8], candidates}`.
- `configuration`: `{slots: 8, questions_per_slot: 13, published_values: 24, clearance_unit, scoring_frame: "ans1", scoring_instrument}`.
- `repetitions` is 8.

**The plist.**
- File: `artifacts/com.personacore.phase36.probe.plist`, Label `com.personacore.phase36.probe`.
- ProgramArguments: `/usr/bin/caffeinate -dims /Users/juliorcoelho/PersonaCore/.venv/bin/python /Users/juliorcoelho/PersonaCore/scripts/phase36_probe.py run --heartbeat /Users/juliorcoelho/PersonaCore/data/v6_mps_heartbeat.jsonl`. With no `--front`, it runs all of RUN_ORDER.
- Logs: `logs/phase36_probe.out` and `logs/phase36_probe.err`.
- Environment: `PERSONACORE_SWEEP_ACTIVE=1`, `PATH=/usr/bin:/bin:/usr/sbin:/sbin`, `PYTHONUNBUFFERED=1`.
- RunAtLoad and KeepAlive are false, and ProcessType is Interactive.

**Test helpers in `tests/test_phase36_probe.py`.**
- `_e6_light(monkeypatch) -> log`. It uses the real tokenizer and the real `draw_all` over a fake `_complete`, with forwarding spies on `assert_no_value_in_prompt` and `draw_all`.
- `_e5_light(monkeypatch) -> calls{probe, match, adapter, nll}`. Every model-touching call is faked with sentinel readings (`_E5_SENTINEL_TEXT`, `_E5_SENTINEL_NLL`).
- `_stage_calls(name, attr) -> (calls, parents)` and `_with_items(node, parents)` are general AST helpers.
- `_planted_e6_stage`.
- `_planted_e1_sidecar()` writes a numbers-only E1 sidecar under the patched `_ROOT`. Its expected high is 4.0.
- `_e5_e6_live_fixture(root)` and the module-scoped `e5_e6_live`. They return `{root, sidecars{e5,e6}, records{e5,e6}, log, spies{guess, match, nll, adapter, hashed}, strays, stdout, ledger, components}`.
- The forbid-widening wrapper and `PROBE_MAX_NEW_TOKENS = 4` live inside that fixture. Reuse them if another live fixture drives `probe_guessability` on the random fixture base.

## Known Stubs

- `STAGES` and `RECORD_BUILDERS` still lack e3 and e2, which 36-05 adds. Until then `preflight()` and a default `run_all()` refuse "no registered stage", which is intended.

## Threat Flags

None. All new surface is in the plan's register:
- T-36-15: readings are never bound, an AST test checks this, and `silenced()`, `prove_no_reading` and the live stdout scan all apply.
- T-36-16: the plist sets `PERSONACORE_SWEEP_ACTIVE=1` and runs under caffeinate -dims.
- T-36-17: the D-07 string is in `configuration.context`.
- T-36-18: the stand-in is signature-bound and documented in the fixture.

## Self-Check: PASSED

- FOUND: scripts/phase36_probe.py, tests/test_phase36_probe.py, artifacts/com.personacore.phase36.probe.plist
- FOUND commits: c119571, 148a8d1, efd6146
