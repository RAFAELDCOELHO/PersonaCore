---
phase: 35
slug: v6-0-pre-registration-and-the-research-it-rests-on
status: verified
threats_open: 0
asvs_level: 1
created: 2026-10-01
register_authored_at_plan_time: true
audited_at: 62c67e4 (last code commit bbcec95)
---

# Phase 35 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Threats here are integrity threats to a pre-registration (post-hoc re-tuning, retyped values,
> forged fills, broken ordering), not network/auth surface. Every `mitigate` row was checked
> against the code at HEAD `62c67e4`; where a developer ruling superseded the plan text, the row is
> judged against the ruling (35-05-SUMMARY.md, 35-CONTEXT.md "Addendum to D-15").

Baseline commands run for this audit (no file written outside the session scratchpad):
- `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase35_prereg.py` → **88 passed** in 21.79 s.
- `.venv/bin/python scripts/phase28_report.py check` → exit 0; `scripts/phase34_report.py check` → exit 0.
- `git ls-files 'results/phase3[5-9]_*' 'results/phase4[0-5]_*'` and the `find` equivalent → 0 files.
- Scratchpad probe `sec35_probe.py` (imports the module, repoints nothing on disk): `fill("e7_x")`
  refused (D-02); `SLOTS[...] = ...` and `SLOTS["e2_S"]["rule"] = ...` raise (read-only proxies);
  `hasattr(phase35_prereg, "_SLOTS")` is False; `_prove_budget(..., len(seed_list())+1)` refused
  with the D-06 STOP; `fill("e4_parameters", ...)` with `eps_lower_one_run` stubbed refused (D-11).
- `git status --short` after every command: only the pre-existing ` D .claude/scheduled_tasks.lock`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| published paper → module | Values transcribed from arXiv PDFs become pins that decide whether E4 runs | two published ε values (0.673, 2.675) and their inputs |
| research note → thresholds | A threshold resting on an unverified citation would be locked into a frozen module | V6-PREREG-09.md citations, pages, verbatim lines |
| prereg → later v6.0 phases (36-45) | Later phases import paths, seeds, targets and cuts; a post-hoc edit would re-tune after seeing data | module source, ancestry-guarded |
| committed records → rules | Rules read committed JSON at call time (`json.loads` only) | results/*.json of Phases 16-26, 36-43 |
| owner fill files → registry | Phases 36-45 add `scripts/phase{NN}_*prereg.py` fill files that the census polices | `fill(...)` call sites |
| v4.0 record → E3 reuse | v4.0 control reused only byte-identical to tag v5.0 | `git show v5.0:<path>` bytes, SHA-256 |
| git history → ordering verdict | Ordering legs trust `git log`/`merge-base` on a full clone | commit graph |
| executor → planning files / vault | Hand edits only; Obsidian entry carries commits, totals, decisions | planning frontmatter, vault note |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (evidence) | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-35-01 | Spoofing | citation in V6-PREREG-09.md | mitigate | Note cites `2305.08846v1` (v1 only, `.planning/research/V6-PREREG-09.md:33-34,99-100`, re-read via gstack `/browse`) and `2110.03620v2`, with the verbatim PDF line per pin; `test_research_note_cites_both_sources_with_pages` asserts versions, theorems, "p. 46", "p. 28" and both verbatim lines. Numeric pin: `test_one_run_reproduces_appendix_d_p46`, `test_one_run_reproduces_section7_p28` (`ONE_RUN_PUBLISHED`, `scripts/phase35_prereg.py:287,294`), so a misread page fails numerically. | closed |
| T-35-02 | Tampering | threshold locked before research | mitigate | Note added alone in `8fba327` (1 file, 213 lines); `test_research_note_precedes_every_prereg_commit` (merge-base over every prereg commit, `pairs` = commit count) and `test_research_note_ordering_reds_on_a_planted_repo` (reversed / never-added RED). Shallow clone fails (`tests/test_phase35_prereg.py:228`). | closed |
| T-35-03 | Tampering | one-run port drift | mitigate | Two pins within 1e-3 (tests above), closed form within 1e-8 (`test_one_run_closed_form_at_delta_zero`), dropped-δ non-vacuity (`test_one_run_tolerance_cannot_absorb_a_dropped_delta`), `test_one_run_reproduction_holds` flips False on a stubbed port. | closed |
| T-35-04 | Repudiation | provenance inside an entry | mitigate | `_prove_entry` (`scripts/phase35_prereg.py:160-190`) refuses `proposer`/`adopted_by` and `FORBIDDEN_PHRASE`; runs at import via `_prove_entries()` (`:755-760`). `test_no_proposer_or_adopted_by_in_any_entry` plants a key and the phrase into a copy and watches the AST walk go RED; real file byte-unchanged. | closed |
| T-35-05 | Tampering | composition re-implemented | mitigate | `CURVE_TOTAL = phase25_epsilon.curve_total`, `SELECTION_ACCOUNTED = phase25_epsilon.SELECTION_ACCOUNTED` (`:199-200`); `test_composition_is_basic_and_by_reference` asserts `is` identity and a hand-computed total `(4.0, 3e-5)`. | closed |
| T-35-SC | Tampering | package installs | accept | No package added in this phase (`git diff --name-only 8fba327~1 HEAD -- tests/ scripts/ src/` lists only the two phase files; scipy not added). See Accepted Risks AR-35-01. | closed |
| T-35-06 | Tampering | prereg edited after a v6.0 record | mitigate | `V6_RESULT_PATHS` (`:317`) → derived `ARTIFACT_PATHSPECS` (`:336`); `test_phase35_prereg_is_frozen_before_every_v6_result`, `test_pathspecs_are_derived_and_cover_results_phase36_to_45`, `test_pathspecs_are_disjoint_from_every_v5_tag_result`. Zero v6.0 records today, so the guard is armed, not yet bitten (35-VERIFICATION SC1 watched it RED in a scratch clone). | closed |
| T-35-07 | Tampering | threshold retyped | mitigate | `test_six_closed_pins_imported_never_copied` (deleted import / copied pin / top-level lazy import planted RED), `test_no_seed_target_or_record_value_is_retyped` (seed, cut, target planted RED), `test_entries_bind_f_y_f_c_and_delta_by_attribute` (`_binding_failures`, planted RED). | closed |
| T-35-08 | Tampering | seed ladder edited in phase23_run.py | mitigate | `test_seed_ladder_is_unchanged_since_its_first_add`: AST of `SEED_LADDER` at first add `5303819` equals the live tuple; `seed_list() is phase23_run.SEED_LADDER`; shallow clone asserted out. | closed |
| T-35-09 | Tampering | a read record swapped | mitigate | Paths only via `phase26_canary.RECORD` (`:407`), `phase19_floor.EVIDENCE_ARTIFACT[...]` (`:442`), `phase19_erasure.arm_record_path("erased")` (`:473`); reads are `json.loads` only (no pickle / `torch.load` / eval in the module). Per the ruling, measured slots read through `_consume_inputs` (`:910-952`): declared pattern, repo-relative, exists, named in `source`, every non-optional declared pattern consumed; floors and the (c) band are READ (`_rule_e1_condition_a_floors` `:1261+`, `_rule_e1_condition_c_band_inputs` `:1700-1770`, supplied value refused unless equal to the read one; CR-01). | closed |
| T-35-10 | Information disclosure | config.k (48) vs R1a k (78) | mitigate | `r1a_rederive` uses `len(record["config"]["ablated_components"])` (`:474`); `test_r1a_assertions_rederive_from_the_erased_record` asserts `config.k == 48` and `len(ablated_components) == 78`. | closed |
| T-35-11 | Denial of service | torch import breaks CPU-only import | mitigate | `test_the_prereg_imports_without_torch` (subprocess probe: none of `_HEAVY` in `sys.modules`); top-level AST check in `_pin_import_failures` (`tests/test_phase35_prereg.py:678`, planted RED at `:701`); heavy imports are function-local (e.g. `import teach_persona` inside `_rule_e3_grid_subset`). | closed |
| T-35-12 | Elevation of privilege | slot filled by undeclared rule/name | mitigate | `fill` proves `slot in SLOTS` (`:1882-1888`); `SLOTS` is `MappingProxyType` over `MappingProxyType(dict(slot))` copies and `del _SLOTS` (`:1876-1879`); `_prove_slots()` at import ties each rule to `_rule_<slot>` in this module (`:1891-1923`). Tests: `test_slot_fill_refuses_an_undeclared_or_non_string_slot`, `test_registry_is_built_from_copies`, `test_slot_fill_dispatches_only_the_declared_rule`. Probe: undeclared refused, both write levels raise, `_SLOTS` absent. Deliberate-bypass residuals KL-01..09 accepted (AR-35-02). | closed |
| T-35-13 | Tampering | S raised above the seed list (D-06) | mitigate | Judged against the ruling (CONTEXT "Addendum to D-15"): `_prove_budget` refuses `e2_seed_count > len(seed_list())` with "STOP and ask Rafael (D-06)" (`:983-987`); reached from `_rule_v6_budget_and_stop_line` (`:1156`, owner 36, before `_consume_inputs`) and on every consumer read via `_budget_record` (`:1001`), including `_rule_e2_S` (`:1173-1189`, a typed S different from the read one refused). Tests: `test_e2_S_refuses_more_seeds_than_the_list`, `test_budget_record_is_revalidated_by_every_consumer`. Probe confirms the STOP. | closed |
| T-35-14 | Spoofing | E3 graded against another recipe's / stale control | mitigate | `_rule_e3_recall_threshold` (`:1525-1588`): key `(lr, steps, batch, seed)` read from each record, key set must equal the grid's, sigma = 0 proven; `_v4_control` (`:810-830`) compares SHA-256 of the working file with `git show v5.0:<path>`; reuse only at the v4.0 record's own seed (`:1462-1475`). Tests: `test_e3_grid_reuses_the_v4_control_only_when_byte_identical_to_v5`, `test_e3_recall_threshold_keys_each_control_by_its_recorded_recipe`. | closed |
| T-35-15 | Tampering | E4 ceiling from unreproduced bound | mitigate | `_rule_e4_parameters` proves `one_run_reproduction_holds()` (`:1605`) and `inclusion_probability == ENTRIES["e4_inclusion_probability"]` (0.5, `:720-721`, `:1617`); beta locked to `e4_beta` (Rafael round 1). Tests: `test_e4_parameters_gate_on_the_reproduction`, `test_e4_beta_is_the_one_sided_95_level_of_phase26_and_both_pins`. Probe: refused with D-11 on a stubbed port. | closed |
| T-35-16 | Tampering | E3 grid crossing P22 WARNING-4/5 | mitigate | `p22_onset_sigma` (`:1028`) evaluated for every T in the grid ∪ STEP_BUDGET, any noised σ ≤ onset refused before training (`:1494-1502`). `test_e3_grid_refuses_a_p22_crossing` reproduces 0.078902 within 1e-6 (`tests/test_phase35_prereg.py:1228`). | closed |
| T-35-17 | Repudiation | slot filled without derivation / unnamed record | mitigate | `_consume_inputs` runs `_prove_entry` on the derivation, proves its value, requires `source` to name every consumed path and every non-optional declared pattern consumed (`:910-952`); `optional=` used only by the two e3 rules (AST-pinned per 35-REVIEW-FIX). Design slots: `_frozen_entry` → `_prove_entry` (`:1133-1138`). Tests: `test_slot_measured_rules_consume_their_inputs`, `test_every_declared_input_pattern_is_consumed_unless_optional`, `test_slot_design_entries_refuse_a_proposer`, `test_e1_floors_corpus_is_a_declared_consumed_input`. | closed |
| T-35-28 | Tampering | 5th E3 recipe without a reuse | mitigate | `_rule_e3_grid_subset` (`:1477-1491`): 5 recipes only if `reused` and a `_prove_entry`-valid fifth-recipe derivation citing `results/phase36_budget.json`. Test: `test_e3_grid_refuses_a_fifth_recipe_without_a_reused_control`. | closed |
| T-35-18 | Elevation of privilege | fill outside owner / twice / alias | mitigate | `_slot_census_failures` (`tests/test_phase35_prereg.py:2166-2269`) over scripts/ and src/ (`test_slot_census_scans_scripts_recursively`, non-empty + src/ meta-guards `:2315-2316`); `test_slot_census_reds_on_planted_owner_files` plants 26 cases RED (outside owner, filled twice, alias, `_rule_` ref/import, registry write, private access, `vars`, `getattr`, `sys.modules`, `importlib`, `__import__`) with single- and multi-file positive controls; `test_slot_census_is_green_on_the_real_tree`. Residuals KL-01..09 accepted (AR-35-02). | closed |
| T-35-19 | Tampering | slot-name binding without fill | mitigate | Binding rule `slot.upper()` must be exactly `fill(slot, ...)` (`:2194-2203`); planted `E2_S = 5` and `S = fill(...)` RED ("different rule"). | closed |
| T-35-20 | Tampering | post-hoc fill file | mitigate | `_slot_ordering_failures` leg (a) (`:2510-2527`), per fill file, every commit, same-commit refused; planted RED `a40`, `a40_same`, `a41` (ordering-after-calibration), `b7_38`, `b7_41` (B7 bundles). `_ordering_after_every_commit` refuses the real repo (`:2541-2542`, `test_slot_ordering_every_commit_refuses_the_real_repo`). | closed |
| T-35-30 | Tampering | phase measures with a slot unfilled | mitigate | Leg (c) (`:2499-2506`); RED `c40`, `c41` (non-input Phase 41 record, both unfilled slots named); GREEN sequences `g36/g41/g42/g38` checked after every commit. | closed |
| T-35-29 | Tampering | fill derived from a not-yet-existing input | mitigate | Leg (b) (`:2529-2534`) runs whenever a fill file is tracked; isolated planted RED `b36`. | closed |
| T-35-21 | Repudiation | census passing on nothing | mitigate | Positive controls (valid single- and multi-file fills pass; green ordering sequences with `verdicts[-1][1] > 0`, `:2620`); non-empty scan and src/ meta-guards (`:2315-2316`); `meta-guard` asserts across the AST walks (`:364, 640, 650, 745, 753, 802, 2423, 2820`). | closed |
| T-35-22 | Denial of service | shallow clone skips ordering | mitigate | Leg check emits a failure when `--is-shallow-repository != false` (`tests/test_phase35_prereg.py:2479-2480`, also `:228`, `:481`); `.github/workflows/ci.yml:28` sets `fetch-depth: 0`. | closed |
| T-35-23 | Tampering | wrong derivation frozen | mitigate | Rafael's review happened before any v6.0 record: verbatim replies for rounds 1-3 and the code-review rulings in `35-05-SUMMARY.md` (Task 1, "Code review rounds"); corrections `f13ad62`, `d850d0c`, `1e1e1c5`, `3805beb`; zero v6.0 records exist (T-35-24). | closed |
| T-35-24 | Tampering | v6.0 record created during the phase | mitigate | `git ls-files` and `find` for `results/phase3[5-9]_*` / `phase4[0-5]_*` both return 0 at HEAD (run in this audit); ancestry test in the suite (T-35-06). | closed |
| T-35-25 | Repudiation | silent skip added | mitigate | `test_no_skips_in_this_file` (AST zero-skip guard, planted `pytest.skip` RED); `tests/test_phase25_venue.py` last commit `d2dcbe2` (2026-09-22), before the phase start `8fba327`; no skip/xfail line added to tests/ since `8fba327~1` other than the guard itself; final gate 4 skipped = last green run's 4 (`35-VALIDATION.md:119`, 3487/4/0 at `bbcec95` — recorded, not re-run here: the suite takes ~39 min). | closed |
| T-35-26 | Tampering | planning files corrupted at close | mitigate | `phase28_report.py check` and `phase34_report.py check` both exit 0 at HEAD (run in this audit); phase-close commit `477ae0a` records "STATE/ROADMAP/REQUIREMENTS by hand, zero gsd-sdk handlers". | closed |
| T-35-27 | Information disclosure | secrets in the vault | mitigate | The vault cannot be read by this auditor. Evidence: the orchestrator's statement that `01-Projects/PersonaCore — memória em pesos.md`, section "Fase 35: executada e FECHADA", holds commits, totals and decisions; plus a repo-side scan of every phase-35 artifact, the note, the module and the test file for key/token/secret/password patterns returning no credential (only the plan's own "No secrets" instruction and the threat row). | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-35-01 | T-35-SC | No package is installed by this phase; scipy deliberately not added; RESEARCH §Package Legitimacy Audit is empty. Nothing to audit until a dependency is added. | Plan 35-01 threat model (plan-time `accept`) | 2026-10-01 |
| AR-35-02 | T-35-12, T-35-18 (residuals) | KL-01..KL-09 in `35-REVIEW-FIX.md` ("Known limitations"): census/registry bypasses that need a deliberate route (appending to `_FILLED_GRIDS`, module passed as an argument, from-import of private names, iterating `SLOTS.values()`, `__globals__`, over-strict census on honest code, per-process grid identity, `_deep_frozen` scope, runtime monkeypatching). Accepted under Rafael's stopping rule (verbatim in `35-05-SUMMARY.md` and `35-REVIEW-FIX.md`): only a finding that changes a value read or a verdict emitted in a real fill blocks the freeze. Non-blocking notes N-01/N-02 (fail-closed) recorded there as well. | Rafael (stopping rule, Fix 2 `3805beb`) | 2026-10-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Threat Flags (from SUMMARY.md)

| Plan | Flag | Mapping |
|------|------|---------|
| 35-01 | no `## Threat Flags` section | — |
| 35-02 | none; `json.loads` of committed records through module constants | T-35-09 (informational) |
| 35-03 | none; `_v4_control` runs read-only `git show v5.0:<path>` inside the rule call only | T-35-14 (informational) |
| 35-04 | none; `checkout --detach` only in tmp repos, real repo refused by `_prove` | T-35-20 (informational; verified at `tests/test_phase35_prereg.py:2541-2542`) |
| 35-05 | no `## Threat Flags` section | — |

Unregistered flags: none.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-01 | 31 | 31 (30 mitigate verified in code/tests/commands, 1 accept logged) | 0 | gsd-security-auditor (Claude), at HEAD 62c67e4 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-01
