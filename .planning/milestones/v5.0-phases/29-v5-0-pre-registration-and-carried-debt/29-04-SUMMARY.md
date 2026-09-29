---
phase: 29-v5-0-pre-registration-and-carried-debt
plan: 04
subsystem: v5.0-pre-registration
tags: [pre-registration, admission, gate-08, d-15, prereg-02, prereg-03]
requires: ["29-01 (keys, paths, refusal)", "29-02", "29-03"]
provides:
  - "phase29_prereg.admission(frontier) -> {verdict, reasons, admitted_point_keys, control_readings}"
  - "phase29_prereg.recall_threshold(frontier, leg, arm)"
  - "phase29_prereg.relearning_scope / SCOPE_RULE"
  - "phase29_prereg.CANDIDATE_UNREPLICATED, VERDICTS, EXPECTED_POINTS, FRONTIER_SCHEMA"
  - "D-09 pins by reference (MARGIN_K .. cleared_abc, REFUSED, V4_VERDICTS), NEVER_TAUGHT_BASELINES, control_baseline_source, RECOVERY_FIXTURE_SOURCE"
affects: [Phase 30, Phase 31, Phase 32, Phase 33]
tech-stack:
  added: []
  patterns: ["AST attribute-reference pin guard (is is vacuous on small ints)", "admission as a pure function over a forged-dict-testable frontier"]
key-files:
  created: []
  modified:
    - scripts/phase29_prereg.py
    - tests/test_phase29_prereg.py
    - .planning/phases/29-v5-0-pre-registration-and-carried-debt/29-RESEARCH.md
    - .planning/phases/29-v5-0-pre-registration-and-carried-debt/29-VALIDATION.md
decisions:
  - "D-15 ruled option-2: no promotion; the admission reads CANDIDATE-UNREPLICATED (never MOOT) when an INCONCLUSIVE carries REPLICATION_PENDING_MARKER; RELRN-06..09 then ship as a named limitation"
  - "D-09 (b) accepted: five never_taught_* baselines imported by reference; the advr control is pinned by Phase-32 record reference; the recovery fixture is pinned by source reference"
  - "(c) filenames and (d) ADVR_ARMS seam accepted unchanged"
requirements-completed: []
# PREREG-02 / PREREG-03 closure is the orchestrator's call (after its full-suite run).
duration: ~25 min
completed: 2026-09-24
---

# Phase 29 Plan 04: Admission contract, CANDIDATE-UNREPLICATED reading and scope rule Summary

This plan freezes the v5.0 admission contract (D-06..D-10) in `scripts/phase29_prereg.py` as a pure function, before any v5.0 number exists. Its precedence is INCONCLUSIVE, then ADMITTED, then CANDIDATE-UNREPLICATED, then REFUSED, then MOOT. The threshold is keyed to the arm (advr only). The scope rule is fixed, and every relearning parameter is bound by reference to `phase27_prereg`. All of this follows the developer's D-15 ruling (option-2).

## D-15 ruling

Received 2026-09-24, at the Task-1 checkpoint. At that moment `git diff --quiet -- scripts/phase29_prereg.py` exited 0, and `git log -- scripts/phase29_prereg.py` showed only f517c58 (Plan 01). No D-15-dependent line was written before the ruling.

The developer's replies, verbatim:

D-15: "Confirma opção 1 (no menu: "Option 2: no promotion"): leituradistinta CANDIDATE-UNREPLICATED; gate congelado importado semalteração; zero código de execução novo. RELRN-06..09 tornam-selimitação nomeada se um candidato aparecer — preservando o achadocientífico real sem inventar infraestrutura de promoção cara e semprecedente limpo de importação (phase25_promotion hardwired aos 44pontos de v4.0, dependência oculta de DP, leitura de accountant quejá contradiz DEBT-04). Mesma disciplina de honestidade que jádecidiu All-refused nesta mesma discussão — estado epistemológicodistinto, nunca forçado a virar PASS sem a segunda evidência queGATE-08 genuinamente exige."
(b) D-09 control baseline: "Accept"
(c) filenames: "Accept"
(d) ADVR_ARMS seam: "Accept"

**Clarification.** The menu the developer saw listed "Option 2: no promotion" first. "Confirma opção 1 (no menu: ...)" therefore means menu item 1, which is **option-2**. The content of the reply also clearly describes option-2: the CANDIDATE-UNREPLICATED reading, the frozen gate imported unchanged, and no new execution code.

**Effective ruling:** option-2. (b), (c) and (d) were all accepted, so Step 0 of Task 2 (overrides) was skipped and no override was applied. There was no option-1 content, so there is no "Required Phase-31 input", no promotion namespace and no ROADMAP edit. The plan prescribes the ROADMAP note for option-1 only, so `.planning/ROADMAP.md` is unchanged.

## Tasks

| Task | Commit | Files |
|------|--------|-------|
| 1. Record D-15 ruling; RESEARCH Q1/Q2/Q3 -> RESOLVED | 2969994 | 29-04-SUMMARY.md, 29-RESEARCH.md (3 lines replaced, no other byte) |
| 2. Admission contract + scope rule + D-09 pins + 24 tests | e44f045 | scripts/phase29_prereg.py, tests/test_phase29_prereg.py |
| 3. VALIDATION.md targeted evidence (full suite: orchestrator) | (final docs commit) | 29-VALIDATION.md, 29-04-SUMMARY.md |

## What was built

- **Admission contract** (`admission`). Checks run in this order: (1a) shape checks: the record is absent or not a dict, `point_keys != list(POINT_KEYS())`, the entry set differs, a point is not a dict with a `verdict` dict, or the advr control counts are malformed; (1b) a verdict string outside PASS/FAIL/INCONCLUSIVE/REFUSED, or non-list-of-str `reasons` on a V4 verdict; (1c) `tallies`/`tallies_by_leg` do not re-derive. Each of these returns INCONCLUSIVE and never raises. After that: (2) ADMITTED names every PASS key in `POINT_KEYS()` order; (3) CANDIDATE-UNREPLICATED applies when an INCONCLUSIVE passes `mitigation_gate.promote_to_full_fidelity` (the marker path). The guard `strings[k] == "INCONCLUSIVE"` keeps REFUSED away from the gate's `_prove`. (4) REFUSED applies when all 12 points are REFUSED; its reasons carry both legs' control counts and "could not be measured". (5) MOOT names each fully REFUSED leg with its counts, plus "MOOT does not extend to that capacity".
- `recall_threshold(frontier, leg, arm)` returns `F_Y*k/n` from `control_readings["advr_<leg>"]` and refuses any arm other than `"advr"` (WR-05).
- `SCOPE_RULE` and `relearning_scope`: INCONCLUSIVE raises SystemExit, and CANDIDATE-UNREPLICATED maps to "candidate cleared (a)(b)(c), replication not pre-registered".
- D-09 pins: 19 `= phase27_prereg.<name>` bindings plus `V4_VERDICTS = mitigation_gate.V4_VERDICTS`, guarded in the AST. The AST guard was confirmed red on scratch copies: both `MAX_STEPS = 200` and `band = phase27_prereg.z_rule` are flagged. `NEVER_TAUGHT_BASELINES` is derived and contains 5 entries. `CONTROL_BASELINE_SOURCE` is built from `POINT_RECORD_PREFIX`. `RECOVERY_FIXTURE_SOURCE` is a (reader, path) pair; the fixture itself is never read.
- `NAMED_LIMITATIONS["GATE-08-NO-PROMOTION"]`, and `FRONTIER_SCHEMA` (names `points[<key>].verdict.reasons` and states that no promotion field is defined).

## Verification (committed tree e44f045)

- `tests/test_phase29_prereg.py`: 53 passed, 0 skipped (29 from Plan 01 plus 24 new). `-k "admission or scope or threshold"` gives 21 passed; `-k "d09_pins… or recovery_fixture… or does_not_raise"` gives 4 passed.
- Running test_phase29_prereg, test_phase29_debt, test_phase14_scoring, test_phase17_stats, test_phase23_ctrl, test_phase21_unit_continuation, test_phase21_sc5, test_phase20_correction, test_phase25_driver and test_lora_inject together: 237 passed.
- `test_phase16_driver.py -k d28`: 4 passed. `test_phase27_relearn.py -k untracked_record`: 1 passed. mitigation_gate caller, wall and os.replace censuses: 3 passed.
- `ruff check` and `ruff format --check` on both touched files: clean.
- Acceptance prints: `False 12 True`, and `True True True results/phase16_recall_sample.json`.
- The frozen modules (phase27_prereg, phase25_promotion, mitigation_gate, phase20_gate_coverage, phase25_record) have an empty diff. `find results -name 'phase3*'` returns 0 files.
- **Full suite: not run here (orchestrator override).** 29-VALIDATION.md has a `**Full suite:** PENDING` line for the orchestrator to fill in. Its frontmatter stays `status: draft` / `nyquist_compliant: false` until then; `wave_0_complete: true` is set.

## Deviations from Plan

1. **[Rule 2 - Missing validation]** The admission (1a) step also returns INCONCLUSIVE when `verdicts.control_readings.advr_<leg>.recall_counts.{taught,heldout}` is missing or is not an int (non-bool) `[k, n]` pair with `0<=k<=n, n>0`. The plan's precedence list did not cover this case, and REFUSED/MOOT reasons read those counts, so without the check a malformed record would raise KeyError (T-29-14). Tests: `control-missing` and `bool-control-count`.
2. **Promotion-rule K values.** The step (3) call passes the pinned `CURVE_K`/`FULL_K`, which are the same objects as `mitigation_budget.CURVE_K`/`FULL_FIDELITY_K` through `phase27_prereg`. It does not name `mitigation_budget` directly. The value is identical (16 -> 48), and this avoids a second route to the same number.
3. **Test fixture bug (found and fixed before commit).** `_v5_frontier` first shared the module-level `_CONTROL` lists, so the `bool-control-count` case changed them for later tests. It now copies the lists for each frontier.
4. **VALIDATION.md DEBT-03 row.** The row pointed at `tests/test_phase29_prereg.py -k summary_frontmatter`. The test actually lives in `tests/test_phase29_debt.py` (11 passed); the row now names that file, as the plan's note anticipated.
5. **The plan's `promoted=` fixture parameter was omitted.** It exists for option-1 only.

## Plan-vs-code mismatches

- No mismatches in any name the code uses: `phase27_prereg` exports every listed pin, `ATTACKER_CORPUS` is a dict (as the plan measured), `PINNED_BASELINES` has 5 never_taught entries plus control_n8/control_n64, and `phase18_extraction.CORPUS_SOURCE_FIXTURE == _REPO_ROOT / "results/phase16_recall_sample.json"`.
- `teach_persona.REPLAY_WINDOWS_PER_FACT == 4` (measured), so the rule against a literal 4 applies. `_is_count_pair` writes its pair length as `len(("k", "n"))`, although any literal 2 would also be legal.

## Known Stubs

None.

## Obsidian

Pending. The plan puts the vault entry after the full-suite result, which the orchestrator owns, and this executor has no `obsidian` MCP tool. The vault record is **not** saved.

## Self-Check: PASSED

- FOUND: scripts/phase29_prereg.py (`def admission`), tests/test_phase29_prereg.py, 29-RESEARCH.md (3 × `RESOLVED (29-04 checkpoint`).
- FOUND commits: 2969994, e44f045.
