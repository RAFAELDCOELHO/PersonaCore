---
phase: 39
slug: instrument-context-2-2
status: verified
threats_open: 0
asvs_level: 1
created: 2026-10-05
register_authored_at_plan_time: true
audited_at: 035f7af (prereg frozen 9366134; driver last code commit 3590057; ledger 4268f26; record 78d2605; report 86de12a)
---

# Phase 39 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> The threats are integrity threats to a pre-registered measurement: a rule tuned after the data, retyped
> values, swapped records, an instrument that drifts, MPS time outside the ledger, and records or reports
> that the data does not support. There is no network or auth surface. Every `mitigate` row was checked
> against the code, tests, git history and committed files at HEAD `035f7af`. Where Rafael's rulings
> reshaped a mitigation (39-REVIEW.md, 39-REVIEW-3.md Resolutions; the dated `<orchestrator_amendment>`
> blocks in 39-05..39-10), the row is judged against what was built and ruled.

Baseline commands run for this audit. Nothing was written outside this file and the session scratchpad.
- `.venv/bin/pytest -q -p no:cacheprovider -rA tests/test_phase39_prereg.py tests/test_phase39_ctx.py` gave **197 passed in 78.31 s**, EXIT=0, with 0 skipped.
- `.venv/bin/pytest ... tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte tests/test_phase35_prereg.py::test_slot_census_is_green_on_the_real_tree tests/test_phase35_prereg.py::test_slot_ordering_is_green_on_the_real_repo tests/test_phase36_caps.py::test_owner_fill_files_respect_the_caps_on_the_real_repo tests/test_phase36_ledger.py tests/test_phase25_driver.py` gave **73 passed**. That run includes `test_every_tracked_v6_mps_record_has_a_launch_line` and `test_os_replace_appears_only_in_the_two_phase25_writers`.
- `.venv/bin/pytest tests/test_phase14_scoring.py -k draw_all` gave 1 passed (the draw_all census, which lists `phase39_ctx.anchor_draws`).
- `shasum -a 256 scripts/phase39_prereg.py` gave `4355b880…8297`. `git diff --quiet 9366134 HEAD -- scripts/phase39_prereg.py` reported it unchanged. The driver hash is `4eb5a945…213e`, which equals the record's `provenance.module_sha256` and the 39-08 launch digest.
- `data/phase39_rehearsal.json` was read only. It holds git_sha `7b32c41`, ctx `0a9dbf81…c73b` and prereg `4355b880…8297`, on 8 readings × pet_name/birth_year. Its md5 is `f3d2bf74…c19e`, the same as 39-08's. It is gitignored (`.gitignore:17 data/`).
- `results/phase39_ctx.json` was read only, and the values below were checked against it:
  - status SCORED, device mps
  - launch SHA = end SHA = `852e6b4`, with `head_moved_during_run` False
  - gate rows 64/64 equal; copy equality 448/448 with `unequal` []; work_load_check 8/8 equal
  - gate2 passed; the k0/pet_name row is `independent: True` against the report total
  - `approval == approval_block()` is True
  - 48 cells per event, with no k0 or adapter_off cell; `adapter_off` = "descriptive (D-11 i): never classified"
  - tie audit: criterion False, flips [], exact tie [k8, person_name, G_q], class_changes []
  - CPU cross-check: criterion False, 0/64 gate, 0/1728 R_q and 0/1728 (ii) ranks differing; suffix sums 1728/1728 equal
  - cost: run_hours 0.2279 with run_within_stop True; projection 0.73088 ≤ stop 0.74242 with projection_within_stop True
  - rehearsal_disclosure: 7 commits, prereg_changed False, driver_changed True
  - `modules_changed_since_launch` []
- `results/phase39_ctx_report.md` == `phase39_ctx.render_report(record)` is **True**, and `_tracked_and_clean("results/phase39_ctx.json")` is True.
- `ledger/v6_mps_ledger.jsonl` was read only. It holds exactly two `v6/39/E6/ctx` lines (15 and 16): a start at 16:15:38Z and an end at 16:29:18Z, with the end naming `results/phase39_ctx.json`.
- `data/v6_mps_heartbeat.jsonl` was read only. It holds 14 beats for the run, every gap 60.00–60.01 s.
- `scripts/phase28_report.py check` and `scripts/phase34_report.py check` both exited 0.
- `git status --short` after every command showed only the pre-existing ` D .claude/scheduled_tasks.lock`.
- Not run, under the audit's constraints: the full suite (cited as green at 3590057, 78d2605 and 86de12a, 4300 passed and 4 skipped), and every `phase39_ctx.py run/crosscheck/emit/report` command.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| committed budget / A2 records → prereg values | Pins, caps, prices and projections are read from git bytes and never typed | `results/phase36_budget.json`, the eight A2 draw records, sha256 |
| prereg commit → first `results/phase39_*` record | The whole rule must cross before any record (leg a) | module source, ancestry-guarded |
| Rafael's rulings → ENTRIES | Defaults become confirmed or changed rulings with their quote | 39-REVIEW.md Resolution (cf51309), verbatim |
| gitignored checkpoints → models | D-20 digests via `phase38_rank.reconstruction_checks` before the start line | persona / M2 / components digests |
| scored prompt ids → model | `assert_no_value_in_prompt` on every dispatched anchor and question context | token ids |
| pinned NLL → driver copy | Bitwise equality on CPU (tests), on MPS at gate 1 and per work-pass load (IN-02) | float.hex |
| driver → ledger | Start only after every refusal; the end line names the record; emit refuses while open | ledger JSONL lines |
| rehearsal → MPS launch | The identity is written before scoring; prereg drift refuses; every later driver commit is disclosed | `data/phase39_rehearsal.json` |
| sidecars → record | The sha256 of the gate and reading sidecars is verified against the run sidecar | `data/phase39_ctx_*.json` |
| untracked record / report → git | Each crosses alone, only after Rafael's "approved" and after its ledger line | single-path commits |
| planning files → later phases | Guarded inputs, edited by hand | STATE / ROADMAP / REQUIREMENTS |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (evidence) | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-39-01 | Repudiation | decomposition rule chosen after E6 numbers | mitigate | The rule is written as ENTRIES plus `phase35_prereg.fill` (`scripts/phase39_prereg.py:931-940`). `test_phase39_prereg_is_frozen_before_every_phase39_record` uses `_assert_frozen_before`: every one of the 12 prereg commits is a strict ancestor of each record's first add. It has a natural-RED leg and passed. Phase 35 leg (a): `test_slot_ordering_is_green_on_the_real_repo` passed. The review came before any rehearsal: `git merge-base --is-ancestor a9fa058 783b9be` is true ("reviewed" before the first driver commit, and so before the rehearsal at 7b32c41). | closed |
| T-39-02 | Tampering | hand-typed projection / stop / margin / count | mitigate | Projections and stop are computed at import (`:285-306`), with `_prove` that the 7/7 formula reproduces `front_hours.E6` bit for bit (`:286-291`). `test_no_derived_value_is_typed_in_the_prereg` runs `_literal_failures` with the WR-05 seeds (10584, 56, 27, 48, the report totals) and the d11/d26 floats, plants each one and checks it goes RED, and confirms the real file's bytes are unchanged. It passed. The one typed approval value is `APPROVED_E6_ADAPTERS = 8` (`:212`), labelled as such. | closed |
| T-39-03 | Tampering | swapped A2 draw record | mitigate | Seven pins are parsed by regex `_PIN` from `cap_rulings["E6.a2_regenerated_entries"]`, with `_prove(len == 7)` and the labels one-to-one (`:318-327`). Adapter-off is typed once (`:332`). `test_a2_sha_pins_match_the_tracked_bytes` checks all eight against `git show HEAD:` bytes, and `test_a2_sha_seven_pins_parse_from_the_budget_ruling` covers the parsed seven. Both passed. | closed |
| T-39-04 | Elevation of privilege | 8-adapter run past the 7-adapter cap | mitigate | `COMMITTED_*_CAP` are read from the budget and `_prove`d == `len(PREFIXES)+1` == 7 (`:214-224`). `len(READINGS) == APPROVED_E6_ADAPTERS`. Both projections are `_prove`d ≤ `E6_STOP_HOURS`, with "D-03 forbids a second stop rule" (`:302-308`). `test_d11_ruling_is_quoted_verbatim` reads the bullet at fixed commit `62af2fe`, and `test_d26_ruling_is_quoted_verbatim` reads `3499c3b`. Preflight re-proves the caps against `phase36_caps.committed_budget()` (`scripts/phase39_ctx.py:683-692`). | closed |
| T-39-05 | Elevation of privilege | second fill / private registry reach | mitigate | `test_phase39_scripts_pass_the_slot_census` runs `_slot_census_failures` over `scripts/phase39_*.py`, a glob that covers both the prereg and the driver. The repo-wide `test_slot_census_is_green_on_the_real_tree` also passed. | closed |
| T-39-06 | Repudiation | preference dressed as a derivation | mitigate | `test_entries_are_the_twenty_names_with_honest_kinds` pins every entry's kind (derived vs preference). `test_preferences_are_labelled` checks that the quotes are byte-equal to 39-REVIEW.md at cf51309 and that `_unconfirmed(entries) == []`, with planted non-vacuity. `test_entries_have_exactly_four_fields_and_no_proposer` plants a proposer key and FORBIDDEN_PHRASE and checks both go RED. | closed |
| T-39-07 | Tampering | swapped/edited A2 record feeding G_q | mitigate | `gate2` calls `verify_a2_records` before any read (`:1061-1079`). The committed sources are `phase38_prereg.a2_counts` (k0..k78, `pre_answerable`-checked), the retrain scores (M2), and the report (adapter-off 0). **WR-01 (ruling):** `_target_k0_check` checks the target k0 against the SHA-pinned `results/phase18_extraction_report.md` total minus the seven non-target counts (`:1011-1058`). Tests: `test_gate2_refuses_a_tampered_record`, `test_gate2_target_k0_row_is_independent`, `test_gate2_refuses_a_shifted_target_k0`, `test_report_k0_totals_refuses_a_tampered_report`. On the real record, the k0/pet_name row has `independent: True` and names its source. Gate 2 is re-run at emit (`scripts/phase39_ctx.py:1417-1421`). | closed |
| T-39-08 | Repudiation | classifier precedence ≠ written rule | mitigate | **As ruled (e, f, g):** the door is `cell_spec`/`cells`/`_door`/`classify_cell` → `_precedence` → `disagreement_of`, with REVERSE_DISAGREEMENT counted apart (`:1213-1340`). `test_classify_cell_exhaustive` covers all 256 combinations and asserts REVERSE vs NO_DISAGREEMENT. The named cases are `test_classify_cell_sufficiency_table` and `test_classify_cell_no_disagreement_and_reverse_disagreement`. Plan-03 review: 39-REVIEW.md plus 39-REVIEW-2.md §1, where old and new `_precedence` were compared over 256 combinations and mutants were killed. | closed |
| T-39-09 | Tampering | damage decided by float rounding / non-strict compare | mitigate | `count_status` uses the committed `count_k0/n - count_k/n > MARGIN`, strict (`:1187-1205`). `test_lost_count_status_damage_on_every_exact_eight_drop` pins LOST at {15, 17, 19, 21}. `test_lost_count_status_damage` pins the 26→18 exact tie as INTACT. **Ruling j:** the frozen `tie_audit`/`drop_audit` (`:1384-1457`) gives the class by both formulas, with M2 and G_a n = 1 included. Tests: `test_drop_audit_names_the_rounding_decided_ties`, `test_tie_audit_gives_the_class_by_both_formulas`. The record's `drop_formula_audit` is `tie_audit` output (criterion False, exact tie k8/person_name/G_q). | closed |
| T-39-10 | Repudiation | share without denominator | mitigate | `_tally` always returns `cells`, `disagreement_cells`, `reverse_disagreement_cells`, `undecided_cells` and `denominator`. Shares are `None` when n = 0 (`:1360-1381`). `test_class_counts_publish_denominators` passed. | closed |
| T-39-11 | Repudiation | rule tuned after the rehearsal read E6 | mitigate | Rulings and "reviewed" (a9fa058) landed before driver code (783b9be): ancestry verified. The identity pins prereg sha256 `4355b880…8297`, equal to HEAD's. Preflight's D-27 refusal is at `scripts/phase39_ctx.py:669-674`, tested by `test_preflight_on_the_real_root_requires_the_identity_and_no_prereg_drift`. The prereg is unchanged since 9366134. | closed |
| T-39-12 | Repudiation | planner reading presented as Rafael's decision | mitigate | 39-REVIEW.md "Resolution (2026-10-05)" records a-j and WR/IN verbatim (cf51309). `RULINGS` (`:422`) is checked byte-equal to the cf51309 text by `test_preferences_are_labelled`. "reviewed" is recorded in a9fa058. Residual REVIEW-2 IN-05 (entry `source` fields do not cite 39-REVIEW.md, only the comment at `:420` does) is in AR-39-03. | closed |
| T-39-13 | Tampering | review "fix" silently changing a frozen definition | mitigate | Each fix is its own commit with its reason in the subject: 2c0c300, 76eff2e, 5079fed, b846fd9, f078603, f4dfd48, cf47e2d, f0e6560 and 9366134. `git show --name-only` shows each touches only the prereg and/or its test. 39-REVIEW-2 found no regression on committed data (old vs new side by side, constants equal, mutants killed). 39-03 SUMMARY: full suite 4171 passed / 4 skipped at a9fa058. | closed |
| T-39-14 | Tampering | copy drifting from `span_nll_from_ids` | mitigate | `span_nll_tokens` (`scripts/phase39_ctx.py:375`) is checked by `_same_bits` (float.hex, `:449`). `test_copy_equality_with_the_pinned_function` (fake_lm and tiny GPT) and `test_suffix_sum_is_bitwise_the_pinned_call` passed. On MPS, gate 1 double-scored 448/448 equal and the record shows `unequal` []. | closed |
| T-39-15 | Information disclosure | taught value leaking into a scored prompt | mitigate | `assert_no_value_in_prompt` runs on the dispatched anchor ids before `draw_all` (`:539`) and on every guarded question context (`:579`). `test_anchor_draws_guard_runs_before_any_draw` checks that a leak means no draw. `test_phase14_scoring.py -k draw_all` (the census) passed. `_PINNED_CALLS` requires `phase14_recall.assert_no_value_in_prompt` (AST census). | closed |
| T-39-16 | Elevation of privilege | MPS time outside the ledger / over a cap | mitigate | Preflight calls `phase36_ledger.require_launch(FRONT)` (`:682`) and `check_unit_caps` without `adapters=` (`:694-700`). `test_ast_caps_never_get_the_raised_counts` (planted RED), `test_ast_ledger_calls_are_the_allowed_five` (a per-function register) and `test_preflight_refusals_write_no_ledger_line` all passed. The ledger has exactly one start/end pair. run_hours is 0.2279 ≤ stop 0.7424. | closed |
| T-39-17 | Spoofing | wrong adapter / prefix order / A2 record | mitigate | Preflight runs `phase38_rank.reconstruction_checks()` (D-20 digests), `verify_a2_records()` and `gate2()`, then refuses on any unequal row (`:706-724`), all before the start line. Refusal tests `_refuse_persona_digest`, `_refuse_m2_digest`, `_refuse_components_digest`, `_refuse_a2_record` and `_refuse_gate2` go through `test_preflight_refusals_write_no_ledger_line`. | closed |
| T-39-18 | Tampering | sampler override changing A2 parameters | mitigate | `draw_all(..., anchor_seed_index(slot), n_samples=K - 1)` is the only call (`:541-543`). `test_anchor_draws_dispatch_the_anchor_ids_at_the_d28_index` asserts `kwargs == {"n_samples": K - 1}`. `test_ast_no_os_replace_and_no_sampler_override` plants `temperature=` and `top_p=` and checks both go RED. | closed |
| T-39-19 | Tampering | instrument drift (copy, rank, batching) | mitigate | `run()` gate pass: every committed cell goes through both functions, then `phase38_rank.gate_reading`, and GATE_FAILED is set before any work score (`:801-847`). `gate_cells` and `score_question` make one call per candidate. **IN-02 ruling:** `work_load_check` re-scores the gate's taught cell on each work-pass load, bitwise, else WORK_CHECK_FAILED (`:494-520`, `:853-872`). Tests: `test_a_gate_rank_mismatch_is_gate_failed`, `test_a_bitwise_inequality_is_gate_failed`, `test_a_work_load_check_failure_stops_the_run`, and the AST census `test_ast_instruments_are_imported_not_redefined`. The record shows 8/8 equal. | closed |
| T-39-20 | Repudiation | rule/driver tuned after the rehearsal | mitigate | `record_rehearsal` writes the identity, with the prereg sha256, before the first score (`test_the_identity_is_written_before_the_first_score`). DR-02: `_kept_identity` refuses a different slice before the start line (`:204-216`, `:791-792`). D-27 drift refusal: T-39-11. `rehearsal_disclosure` lists every commit to a disclosed module with its subject (`:239-292`, `test_rehearsal_disclosure_lists_every_commit_to_a_disclosed_module`). The record lists exactly the 7 fix commits 4f859b3..3590057. | closed |
| T-39-21 | Elevation of privilege | rehearsal writing to the milestone ledger | mitigate | DR-01: a non-real root must pass a tmp `ledger_path` and `heartbeat_path` disjoint from the milestone ones (`:765-782`). `test_a_rehearsal_root_needs_its_own_ledger_and_heartbeat` passed. The real ledger holds no rehearsal line: only lines 15/16 for `v6/39/E6/ctx`, both at the MPS time. | closed |
| T-39-22 | Denial of service | crash after start line losing readings | mitigate | `_write_once` sidecars, each reading written before the next loads (`:337-341`, `:874-885`). `test_a_crash_mid_scoring_leaves_an_open_start_that_reconcile_closes` checks the sidecars stay byte-identical. **WR-01:** preflight names partial sidecars as kept crash evidence (`:629-639`, the `_plant_output` "crashed attempt" legs). **WR-02:** emit refuses while the attempt is open (`:1505-1511`, `test_emit_refuses_while_the_ledger_attempt_is_open`). | closed |
| T-39-23 | Tampering | per-token values feeding a rank/event | mitigate | `test_ast_per_token_values_never_feed_a_rank_or_event`: `_RANK_CALLEES` is exactly the 14-name set from the 39-05 amendment. Planted subscript and `.get` legs go RED, and the real readers `_descriptive_block` and `_suffix_check` are not offenders. Passed. | closed |
| T-39-24 | Tampering | swapped sidecar between run and emit | mitigate | `build_record` proves the gate and every reading sidecar sha256 against `run["gate_sha256"]` and `run["reading_sha256"]` (`:1405-1416`). The `_emit_gate_bytes` and `_emit_reading_bytes` legs of `test_emit_refusals_write_nothing` passed. The record carries `provenance.sidecar_sha256`. | closed |
| T-39-25 | Tampering | classes by a drifting second definition | mitigate | **As ruled:** `_classified` and `_decomposition` call only `prereg.cells`, `classify_cell`, `class_counts`, `tie_audit` and `baseline_table` (`:1263-1308`). grep finds no `rank_status`, `count_status`, `_drop_audit`, `CLASSIFIED_READINGS` or `phase38_prereg.drop_formula_audit` in the driver. `test_classify_on_the_committed_counts` and `test_emit_drop_formula_audit_is_recomputed` recompute through the prereg. 39-VERIFICATION re-classified all 96 cells independently and found them identical. | closed |
| T-39-26 | Tampering | descriptive extras leaking into decomposition | mitigate | `cell_spec` refuses adapter_off and k0 under both events (`:1266-1282`). `test_cell_door_is_cell_readings_by_slots_for_both_events` and `test_cell_statuses_and_classify_refuse_a_cell_outside_the_door` passed. The driver test asserts `{"k8","k78","M2"}`, "no k0, no adapter_off" (`tests/test_phase39_ctx.py:2534`). The record's cell readings are {k8..k78, M2}, and `adapter_off` says "never classified". | closed |
| T-39-27 | Repudiation | G_a hit not re-derivable | mitigate | Each record cell carries `anchor_record` with 48 `completions`, `stopped` and `prompt_ids`. `test_readings_block_recomputes_through_the_prereg` re-scores them with `phase18_extraction.score_records` (`tests/test_phase39_ctx.py:2075`). 39-VERIFICATION matched 64/64 cells on the real record. | closed |
| T-39-28 | Repudiation | cross-check presented as a criterion | mitigate | `_cpu_block` returns `"criterion": False` and the generation statement (`scripts/phase39_ctx.py:1332-1366`). The record shows `criterion False` and "no generation cross-check: generation is seeded per device (D-20)". | closed |
| T-39-29 | Repudiation | share/rate without denominator | mitigate | `render_report` prints "… of {cells}" and "… of {disagreement_cells}" (`:1738-1792`). `test_render_report_renders_the_scored_record` parses the GFM tables back (`_assert_gfm_tables`, `_count_of`). The real report's CTX-03 section has 96 "of N" occurrences. | closed |
| T-39-30 | Repudiation | unwired live path behind green fakes | mitigate | A real CPU rehearsal ran run → crosscheck → emit → report. Evidence: the gitignored identity at 7b32c41 (written only by `run()` after preflight passes), and the 39-07 SUMMARY log with REHEARSAL_EXIT=0 and report == render_report. A second rehearsal at 3590057 is recorded in the 39-08 SUMMARY. `test_the_full_fake_chain_through_the_commands` passed. The live MPS producer → consumer chain closed on real data: the report bytes equal `render_report(record)`. | closed |
| T-39-31 | Repudiation | report text the record doesn't support | mitigate | `report()` refuses on the real root unless the record is tracked and clean (`_tracked_and_clean`, `:2222-2240`). `test_report_writes_once_and_the_real_root_needs_a_committed_record` passed. Byte equality was re-run in this audit: True. | closed |
| T-39-32 | Tampering | rehearsal writing to the milestone ledger | mitigate | Same control as T-39-21 (DR-01). The 39-07 SUMMARY records the real ledger and heartbeat mtimes as untouched. The ledger grep shows only the MPS pair. | closed |
| T-39-33 | Elevation of privilege | MPS launch without approval / past a stop | mitigate | Process: 39-08 SUMMARY Task 3 records Rafael's "approved", after "reviewed" (852e6b4). Code: `require_launch` inside preflight before the start line (`:682`). The ledger start (16:15:38Z) comes after 852e6b4 (13:01 -03 = 16:01Z), and the run sidecar launch SHA is 852e6b4. | closed |
| T-39-34 | Tampering | quiet relaunch after crash / gate failure | mitigate | GATE_FAILED and WORK_CHECK_FAILED are run statuses ("emit, then STOP for Rafael"). Preflight refuses any existing output or open attempt (`:629-648`), so a relaunch cannot be quiet. WR-01/WR-02/IN-02 (39-REVIEW-3 Resolution) are implemented and tested (T-39-19, T-39-22). The ledger shows exactly one attempt. | closed |
| T-39-35 | Tampering | GPU contention / sleep distorting the run | mitigate | 39-08 SUMMARY: `nohup caffeinate -dims .venv/bin/python scripts/phase39_ctx.py run`, with `logs/phase39_ctx.err` empty (0 bytes, verified). The heartbeat has 14 beats with gaps of 60.00–60.01 s, so there was no sleep stall. The commit timeline shows no suite overlapping the 13:15–13:29 (-03) window: the 3590057 suite was reported before 852e6b4 (13:01), and the 78d2605 suite came after 13:38. "No other MPS job" rests on the SUMMARY and the single ledger attempt. | closed |
| T-39-36 | Repudiation | reported numbers no file holds | mitigate | Every number in the 39-08/39-09 SUMMARYs was compared with the record in this audit: gate 64/64, copy 448/448, work-load 8/8, run_hours 0.2278947125, projection 0.7308777162950072, collapse 9/48, damage 24/48, tie audit, and CPU 0/64, 0/1728, 0/1728, 1728/1728. All match. | closed |
| T-39-37 | Repudiation | prereg/driver change after rehearsal unreported | mitigate | The identity file equals the 39-07 SUMMARY JSON field by field. The D-27 refusal is in place (T-39-11). The record discloses `driver_changed True`, `prereg_changed False` and the 7 commits, each with its subject. | closed |
| T-39-38 | Repudiation | MPS record tracked without its launch line | mitigate | 4268f26 (ledger) is the parent side of 78d2605 (record). `test_every_tracked_v6_mps_record_has_a_launch_line` passed in this audit. | closed |
| T-39-39 | Tampering | latent red "fixed" by editing a frozen file | mitigate | `git log 78d2605..HEAD -- scripts tests ledger results/phase39_ctx.json` is empty. 39-09 SUMMARY: the suite on 78d2605 was 4300/4 with no test fix. Leg (a) `test_slot_ordering_is_green_on_the_real_repo` and the phase39 ancestry trio passed in this audit. | closed |
| T-39-40 | Repudiation | record committed without approval / mixed paths | mitigate | `git show --name-only`: 4268f26 contains only `ledger/v6_mps_ledger.jsonl`, 78d2605 only `results/phase39_ctx.json`, and 86de12a only `results/phase39_ctx_report.md`. The subjects carry "Rafael approved 2026-10-05", and the approvals are recorded in 39-09 T1 and 39-10 T2. | closed |
| T-39-41 | Repudiation | report text the record doesn't support | mitigate | `report == render_report(record)` was True in this audit, on the tracked record. The 39-10 SUMMARY records the same check before approval. Residual REVIEW-3 IN-04 (non-atomic write) is in AR-39-02. | closed |
| T-39-42 | Tampering | report "fix" by editing driver or record | mitigate | Neither `scripts/phase39_ctx.py` nor `results/phase39_ctx.json` has a commit after 78d2605. The record's driver digest equals HEAD. Rafael's two carry-forward notes (the second rehearsal, the 1/48 baseline) are recorded in SUMMARYs and the milestone carry-forward, not in edits to the record or driver. | closed |
| T-39-43 | Tampering | `phase18_extraction.py` touched | mitigate | `git log d05f18c^..HEAD -- scripts/phase18_extraction.py` is empty. `test_instruments_unchanged_byte_for_byte` passed in this audit. | closed |
| T-39-44 | Tampering | planning-file corruption by a mutation handler | mitigate | Close commit 035f7af touches only STATE, ROADMAP, REQUIREMENTS and 39-VERIFICATION, and its subject says "by hand, zero gsd-sdk mutation handlers". `phase28_report.py check` and `phase34_report.py check` both exit 0 at HEAD. The pre/post snapshot diff itself is attested only by the commit message and SUMMARY. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No threat in the register carries an `accept` disposition. The residuals below are known limitations that Rafael ruled on. None of them changes a value read or a verdict emitted in the E6 record.

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-39-01 | — (D-28 declaration) | 39-REVIEW IN-03: the D-28 seed-window test is tautological. The anchor seed index itself is asserted at the dispatch (`test_anchor_draws_dispatch_the_anchor_ids_at_the_d28_index`: `index == SLOTS.index(slot) * K`). | Rafael, 39-REVIEW.md Resolution ("IN-03: limitação conhecida") | 2026-10-05 |
| AR-39-02 | T-39-31, T-39-41 (residual) | 39-REVIEW-3 IN-04: `report()` writes non-atomically. A torn file is refused by the write-once check, so it cannot be silently published, and byte equality with `render_report(record)` was checked before approval. | Rafael, 39-REVIEW-3.md Resolution ("IN-04: limitação conhecida") | 2026-10-05 |
| AR-39-03 | T-39-07, T-39-12 (residual) | 39-REVIEW-2 info items left as written. IN-01: a regenerated phase18 report makes gate 2 SystemExit rather than fall back; this is consistent with the "SHA fixado" ruling. IN-05: entry `source` fields do not cite 39-REVIEW.md, although the quotes are test-pinned to it at cf51309. IN-02 was closed later by the driver's IN-06 fix (`_full_classification`), IN-03 by 9366134, and IN-04 by `test_classify_on_the_committed_counts`. There was no item-by-item ruling: these were accepted as part of Rafael's "reviewed" after the second-pass review. | Rafael ("reviewed", a9fa058) | 2026-10-05 |

*Accepted risks do not resurface in future audit runs.*

---

## Threat Flags (from SUMMARY.md)

| Plan | Flag | Mapping |
|------|------|---------|
| 39-01 .. 39-10 | no `## Threat Flags` section in any SUMMARY | — |

Unregistered flags: none. I did not scan for new attack surface beyond the register.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-05 | 44 | 44 (all `mitigate`; code rows verified in code, tests and committed files; process rows (T-39-12, 13, 30, 33-37, 40, 44) verified from git history, commit contents, heartbeat and ledger reads, SUMMARYs and REVIEW Resolutions) | 0 | gsd-security-auditor (Claude), at HEAD 035f7af |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-05
