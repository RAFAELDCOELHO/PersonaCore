---
phase: 27-relearning-attack
verified: 2026-09-16T22:11:40Z
head: a1dec50
status: human_needed
score: "5/5 ROADMAP Success Criteria verified (SC1 in its MOOT form; SC2-SC5 as guarded code, in a form weaker than a future ADMITTED run needs); 28/28 PLAN must-have truths verified"
overrides_applied: 0
re_verification: false
requirements_accounted: "5/5 (RELRN-01 SATISFIED in its MOOT form; RELRN-02..05 NOT SATISFIED by design, the D-05 named limitation) - no orphaned IDs"
verifier_ran:
  - "record bytes: sha256 065b2bc19e9d1a3527e7b538f16106a54b1c62c9dd8e1915513cb1c942609199 for the working tree, the HEAD blob and the 88dff77 blob (3 of 3 equal)"
  - "git: results/phase27_admission.json has one add, 88dff77 (author Rafael, parent e308675, 1 file, no trailer in the body); git ls-files results/phase27_* = 1 file; scripts/phase27_prereg.py has one commit, 916ad4d, which is an ancestor of 88dff77 and a distinct commit (strict); results/phase25_frontier.json has one commit, 4030d0e, sha256 1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5, 22311714 bytes, equal to the record's frontier_sha256 and frontier_bytes"
  - "record fields read: 20 top-level keys; verdict MOOT with 7 reasons; admitted_point_keys []; tallies FAIL 32 / INCONCLUSIVE 6 / PASS 0 / REFUSED 6; cleared a 30 / b 4 / c 1 over 38 reached, 6 refused; 44 rows, 0 rows with (a),(b),(c) all cleared; x.value 0.006461685297443485 at 416 questions, tolerated 0; apparatus.status 'not exercised', reason 'gate read MOOT', 4 legs; disjointness overlaps 0/0/0 over 104 checked question strings (416 gated prompts, held-out family A2, 336 trained attack rows)"
  - "provenance: 7 of 7 module_sha256 digests recomputed with hashlib from file bytes equal the recorded ones (0 drifted); git_sha == head_at_write == e308675; git diff --stat e308675..HEAD -- scripts src tests is empty"
  - "independent re-derivation from the frontier (my own counting, not the gate's code): 44 point_keys, 44 unique, set-equal to 44 points; tally FAIL 32 / INCONCLUSIVE 6 / REFUSED 6, PASS keys []; Wilson bound with a stdlib NormalDist one-sided z gives wub(0,416) = 0.006461685297443481 against X 0.006461685297443485; (a) 30 (dp_n8 15, dp_n64 15, adv_n8 0), (b) 4 (dp_n8 1, dp_n64 1, adv_n8 2), reached 38. (My first recount used a two-sided z = 1.96 and disagreed; the project's bound is one-sided (erasure_gate.py:90), so I discarded it.) The live gate on the frontier reads MOOT with reasons equal to the record's"
  - ".venv/bin/pytest -q -p no:cacheprovider tests/test_phase27_prereg.py tests/test_phase27_on_draw.py tests/test_phase27_relearn.py -> 69 passed in 50.10s, 0 skipped; git status afterwards shows only ' D .claude/scheduled_tasks.lock', and the real results/ data/ checkpoints/ finds show only the tracked record"
  - "pytest --collect-only -q (whole suite) -> 2871 tests collected; ruff check . -> All checks passed; ruff format --check . -> 284 files already formatted. I did NOT re-run the full suite; the orchestrator's figure is 2867 passed / 4 skipped / 0 failed in 1417.73s at 1fa6f60"
  - "D-37 re-watched on the committed record: calibrate / curve / gate --baseline never_taught_1337 / structural-proof --leg n8 -> 4 of 4 exit 1, stdout 0 bytes, stderr sha256 efd445c86b24e752794ff7df6baee9be234cd9f809c7e608bead8bb377c73b61 (identical to the 8 captures quoted in 27-05-SUMMARY); the data/ finds are empty afterwards"
  - "the SC2 ordering guard, which no test covers, watched with an out-of-tree forged ADMITTED record and device/config/training stubbed to raise: curve without calibration REFUSED; gate without calibration REFUSED; gate with calibration but no curve REFUSED (3 of 3; no stub reached)"
  - "apparatus node ids: 5 distinct ids named in the record, 0 missing from a fresh pytest --collect-only of tests/test_phase27_relearn.py"
  - "ledgers: the 5 RELRN traceability rows cite 26 guard tests, 0 missing from the file each row attributes them to; 'not admitted by the gate' appears 4 times; git diff 4c451fa..HEAD of REQUIREMENTS.md changes only the RELRN-01 checkbox and the 5 traceability cells (the requirement text is unedited); the ROADMAP Phase 27 SC text is unedited since a655198"
  - "D-39 / D-14: git diff --stat 916ad4d..HEAD over pyproject.toml, scripts/teach_persona.py, results/phase25_frontier.json, scripts/phase27_prereg.py, scripts/mitigation_gate.py and scripts/erasure_gate.py is empty; no *phase27* plist under artifacts/ or ~/Library/LaunchAgents; launchctl list | grep -c -i phase27 -> 0"
  - "D-20: the attacker's replay_windows = replay_window_budget(8) // BLOCK_SIZE = 32, equal to dp_n8's recorded replay_windows=32 (results/phase25_operational_note.md:984)"
  - "anti-patterns: TBD/FIXME/XXX -> 0 hits over the 7 phase-27 code/test files + the record; TODO/HACK/placeholder -> 0 hits; no probes declared or present"
  - "review experiments (CPU only, every write under the session scratchpad 27-verify/, model load and training stubbed before any weights): CR-01, CR-02, WR-01..WR-06 and IN-02 - outputs quoted under Code Review Rulings"
human_verification:
  - test: "Rule on how to carry the confirmed-but-latent review findings CR-01, CR-02, WR-02, WR-03 and WR-06, and the inconsequential WR-01 and WR-04. None of them has an owning phase today: Phase 28's SC3 names only the v3.0 debt and the stale stamps."
    expected: "A recorded ruling. The verifier recommends a named limitation carried to Phase 28's RPT-03 list, plus a stated obligation that whichever phase first reads ADMITTED fixes them in its continuation driver/pre-registration continuation BEFORE its first leg. The alternative is fixing now, which means deleting the operator-committed record in its own commit and re-running admit, because the record pins the bytes of all 7 modules. That churn cannot change the MOOT verdict."
    why_human: "Whether to re-issue an operator-committed record, and which phase owns latent debt, is a developer decision. No command can settle it."
  - test: "Rule on the WR-05 decision-coverage gap. D-12, D-24 and D-28 pin and instantiate the DP sigma=0 control per capacity leg. On the frontier, adversarial points were judged against their own arm's control (adv_n8 taught 879/1008, threshold 0.6104), but the apparatus would calibrate Z for them against dp_n8 (790/1008, threshold 0.5486), and no adversarial control adapter is pinned."
    expected: "A dated ruling, before any adv_* point can be admitted. Either a pre-registration continuation keys the threshold and the control pin by (arm, leg) and calibrates Z per (arm, leg), or adv_* admission is refused with the stated reason, or DP-control calibration for adversarial points is accepted with its reason written down."
    why_human: "This re-opens a LOCKED decision's scope. It is latent today (0 adversarial points can be admitted from the committed frontier: 6 INCONCLUSIVE, 6 REFUSED), but CONTEXT promises the apparatus is 'attackable in v5.0 without any decision being re-opened', and for the adversarial arm that promise does not hold without a ruling."
warnings:
  - "WARNING (CR-02): D-08's universal wording ('every attack leg refuses unless the committed record reads ADMITTED') and D-22's ('never a subset chosen after seeing a result') are FALSE outside the sanctioned path. A forged out-of-tree record passed through the public --record flag, or a tracked record edited in the working tree, drives a leg to training on a frontier FAIL point. Both are TRUE on the default invocation against the committed record (4 of 4 refusals watched). No must-have is false: 27-03 must-have #2 designs in the '(when inside the repo) be git-tracked' exception."
  - "WARNING (CR-01): the runtime D-18 bin pin in train_relearn_arm switches itself off on any row-level corpus drift. It is also weaker than the rule plan 27-03 specified ('compare len and ids', which would have refused the measured value drift), a change recorded as 27-03-SUMMARY deviation 8. No test exercises the refusal. D-18 itself holds: the pins are committed data, and test_attacker_corpus_sha_re_renders goes RED under the same drift."
  - "WARNING (WR-02): the data-order proof (iii) is recorded, not refused, which 27-03 planned. structural-proof does not require every admitted point's mitigated reading, which was not planned. SC5 holds as guarded code in that weaker form."
  - "INFO (D-13, letter vs intent): the user's recorded choice was teach_persona.train_arm (27-DISCUSSION-LOG:160). The driver calls teach_persona.train() directly (RESEARCH OQ1 option B: train_arm cannot take one shared TrainConfig, max_steps_override or on_draw, and teach_persona.py is digest-pinned). The deviation is disclosed in the operator-committed record (apparatus.train_path: 'teach_persona.train_arm is not called'). Same recipe symbols, same build_arm_bins data path."
  - "INFO (SC2/RELRN-01 wording): the SC text says 'recovered recall <= X'. D-16 makes extraction decide (X is the frontier's condition-(a) extraction ceiling over 416 questions) and reports recall beside it. Verified as CONTEXT resolved it."
  - "INFO (D-23, SC3's x-axis): scored_tokens = mask-bin ones x steps is a rescaled step count, not a count of scored tokens. On the pinned attacker bin (7581 tokens, 2719 mask ones) the rung-50 value is 135950, which is more than the 102400 teaching-window target positions 50 steps x 8 x 256 can draw at all. It was never exercised (MOOT); Phase 28 should not present it as tokens scored."
---

# Phase 27: Relearning Attack — Verification Report

**Phase Goal:** Prove adversarially that what survived the mitigation cannot be cheaply reverted, or
record measurably that it can.
**Verified:** 2026-09-16T22:11:40Z at `a1dec50`
**Status:** human_needed. Every must-have is verified. Two developer rulings are requested on how
latent, confirmed review findings are carried. No finding changes the committed MOOT finding.
**Re-verification:** No — initial verification

**How this phase is judged (27-CONTEXT D-05 / D-09 / D-10):** SC1 is judged in its MOOT form against
the committed record `results/phase27_admission.json` (`88dff77`). SC2–SC5 are judged as guarded code
with CPU tests, never run on MPS. On MOOT, RELRN-01 is ticked and RELRN-02..05 stay unticked with a
named limitation.

## Goal Achievement

### Observable Truths — ROADMAP Success Criteria

| # | Success Criterion | Status | Evidence |
|---|---|---|---|
| SC1 | Admitted by ONE gate call on measured frontier numbers; MOOT when nothing cleared, and the milestone ships it (RELRN-01) | ✓ VERIFIED (MOOT form) | `phase27_prereg.relearning_is_worth_attempting` is pre-registered at ONE commit (`916ad4d`), a strict ancestor of the record's only add (`88dff77`). The ancestry guard checks 1 pair (1 prereg commit × 1 tracked artifact). The record reads MOOT with `admitted_point_keys []`, 0 of 44 PASS, and 7 generated reasons. My own recount from the frontier gives the same tallies (FAIL 32 / INCONCLUSIVE 6 / REFUSED 6), no PASS key, and (a) 30 / (b) 4 over 38 reached points. The live gate returns MOOT with reasons byte-equal to the record's. The record is write-once (`test_admit_refuses_to_overwrite` PRESENT branch green), committed by the operator (checkpoint answer quoted in 27-05-SUMMARY:248), and the finding is shipped (REQUIREMENTS RELRN-01 row, ROADMAP progress row). |
| SC2 | Recovered ≤ X within fixed budget Z is the binary pre-registered gate; Z calibrated from both controls BEFORE the mitigated arm is attacked; `baseline` required keyword, no default (RELRN-01) | ✓ VERIFIED as guarded code (weaker form, see WR-05/WR-06) | `recovery_gate(*, recovered_successes, recovered_questions, x, z, baseline)`: `baseline` is KEYWORD_ONLY with `Parameter.empty` default, and a missing baseline raises TypeError (test). Any key outside the 7 pins refuses. The CLI `--baseline` is required and a closed choice. X is computed by calling `extraction_ceiling_x` and equals the record's X. `z_rule` = max(first clears) on rungs 50..400, capped at 400. The ordering is guarded in code: I watched curve refuse without calibration and gate refuse without calibration or without a curve (3 of 3; no test covers these). Caveats: the baseline never moves the verdict (WR-06), and for adversarial points Z would read the DP control (WR-05). |
| SC3 | Cost-to-recovery curve over scored tokens against the never-taught fresh adapter at identical budget and seed (RELRN-02) | ✓ VERIFIED as guarded code | `run_curve` relearns every admitted point in a leg (the D-22 fix `c054d8b`; the e2e drives 2 admitted points, 10 train calls in `admitted_point_keys` order), scores each at every rung, and places it in `band(...)` against the fresh arm's per-rung readings (MARGIN_K 2 × `phase23_prereg.noise_floor`). It reuses the leg's shared config and the designated seed. `scored_tokens` is recorded per rung by D-23's formula (INFO: that formula is a rescaled step count). |
| SC4 | The curve qualifies the verdict and is not a second gate (RELRN-03) | ✓ VERIFIED | The signature of `recovery_gate` has exactly 5 parameters, none of them curve/band/rungs/cost (`test_the_curve_cannot_reach_the_verdict`). An AST test shows the driver calls `recovery_gate` exactly once, inside `run_gate`, with those 5 keywords and no splat, and `run_gate` calls neither `band` nor `first_clear`. The curve output carries `"finding": "...not a second gate (RELRN-03)"`. |
| SC5 | Identical budget/seed enforced structurally (one shared TrainConfig, off-disk diff, data-order sha256); recovery on a disjoint fixture; attacker corpus pre-registered (RELRN-04, RELRN-05) | ✓ VERIFIED as guarded code (weaker form, see CR-01/WR-02) | (i) ONE `TrainConfig` per leg invocation, identity asserted by the e2e spy. (ii) The config `train()` received and serialised into its checkpoint (`checkpoint.py:135`) is diffed off disk against the driver's record, and a mismatch is refused. (iii) Per-arm offset-stream sha256 through `on_draw`; the e2e asserts equality across the designated-seed arms and inequality across seeds. The driver records this proof but does not refuse on it (WR-02). Disjointness is computed as 0/0/0 over 104 question strings and refused at `admit` when non-zero (planted-RED test). The attacker corpus is pinned by rows sha and bin sha in the prereg at `916ad4d`, and `test_attacker_corpus_sha_re_renders` re-renders both. The runtime pin self-disables on row drift (CR-01). |

**Score:** 5/5 Success Criteria verified.

### Observable Truths — PLAN frontmatter must-haves (merged; 28 truths)

| Plan | Truths | Status | Evidence (beyond the SC rows above) |
|---|---|---|---|
| 27-01 | 7 | ✓ 7/7 | MOOT on the committed frontier; ADMITTED only on a forged PASS copy; INCONCLUSIVE on a 43-point copy, a moved total or per-leg tally, an unknown string, `None`, or a bare-None verdict (`test_partial_or_inconsistent_frontier_is_inconclusive`). X is computed by call, and an AST scan finds no float literal equal to it. The (a)/(b)/(c) counts 30/4/1 re-derive (plus my independent recount). The 7 baselines match their source records, and the on-host adapter hashes were checked (`test_pinned_adapters_hash_on_host` ran, not skipped). Z table 6/6. Corpus rows and bin re-render. The module imports without torch. The ancestry guard runs non-vacuously. |
| 27-02 | 3 | ✓ 3/3 | `on_draw=None` is byte-neutral (`data.py` diff: +7/−1, a guarded call after the draw). `train()` forwards it at the masked teaching site (`loop.py:661`) and the replay site (`:706`), not at `estimate_loss`. Stream equality holds for equal seed, inequality across seeds, and the resume chain equals one run (5 tests green). Other branches are not threaded (WR-04, outside this truth's masked scope). |
| 27-03 | 7 | ✓ 7/7 | `admit` is write-once, runs the dirty check before hashing, and proves rows/tallies at the write. IN-01: the cleared-count `_prove` is tautological, but the counts are independently guarded. Each leg opens with `_require_admitted` (AST test). There are 12 parametrized refusals, plus moved-pins and untracked cases. Apparatus, provenance and disjointness are present. `train()` is called directly with one config and a resume chain, and the recorder tags by bin identity. `recovery_gate` is called with 5 keywords at the FULL_K promotion. The kwargs trace has a planted misspelling watched RED. There is no top-level torch import and no `torch.load`, and the git surface is `ls-files` only. |
| 27-04 | 6 | ✓ 6/6 | The CPU e2e runs `main()` through calibrate → curve → gate → structural-proof: device `cpu` everywhere, both base readers redirected, real `tp.train` and real scorers (module/file identity asserted), promotion K=8→16 under separate `_k8_`/`_k16_` caches with `prefix_identical` True. The off-disk diff is as expected, with a watched-RED copy. Offset streams: tag layout `[0]+[1]*replay` per rung. Disjointness is checked on the real fact set with a planted RED. Node ids: 5 of 5 collected. Provenance was recomputed. `pyproject` is byte-identical. The record re-derives from `build_record`. |
| 27-05 | 5 | ✓ 5/5 | One `admit`, record MOOT (fields above). Refusals: before the commit (SUMMARY) and after it (re-watched by me, identical bytes). No strays and no MPS artifacts. The operator committed the record, the ancestry check is 1×1, and the both-state tests take their PRESENT branches. The ledger diffs match intent: 26 of 26 cited tests exist, and the requirement text is unedited. No plist. Pinned inputs are byte-identical since `916ad4d`. Lint is clean; 2871 collected. The full-suite pass count is the orchestrator's, not re-run here. |

**Score:** 28/28 plan truths verified. 0 overrides.

### Deferred Items

None. Step 9b matched every forward-looking finding against Phase 28 (the only later phase). Its SCs
name only the v3.0 debt and stale stamps (SC3) and the adversarial recipe confound (SC4); none names
the Phase 27 apparatus. Conservative matching therefore defers nothing, and the owning-phase question
is human item 1.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `scripts/phase27_prereg.py` | Frozen gate, X by call, Z rule, band, pins, corpus, recovery gate (min 250 lines) | ✓ VERIFIED | 631 lines, all 38 planned exports present (`hasattr`); one commit `916ad4d`; digest equals the record's |
| `scripts/phase27_relearn.py` | CLI driver: admit + 4 legs (min 450 lines) | ✓ VERIFIED | 1208 lines, all 27 planned exports present (`hasattr`), 5 sub-modes via `DISPATCH`; exercised end to end on CPU; digest equals the record's |
| `src/personacore/training/data.py` | `on_draw=None` capture point | ✓ VERIFIED | Keyword-only, guarded call after `np.random.randint`; byte-neutral test green |
| `src/personacore/training/loop.py` | `on_draw` threaded to both training draws | ✓ VERIFIED | `:661` (masked teaching) and `:706` (replay); `estimate_loss` untouched |
| `tests/test_phase27_prereg.py` | Prereg guards (min 250) | ✓ VERIFIED | 632 lines, 28 tests collected |
| `tests/test_phase27_on_draw.py` | on_draw guards (min 120) | ✓ VERIFIED | 244 lines, 5 tests |
| `tests/test_phase27_relearn.py` | Driver structure + wiring proof (min 450) | ✓ VERIFIED | 1289 lines, 36 tests including the CPU e2e |
| `results/phase27_admission.json` | Operator-committed MOOT record containing `"verdict": "MOOT"` | ✓ VERIFIED | 16664 bytes, sha `065b2bc1…`, 1 add at `88dff77` |
| `.planning/REQUIREMENTS.md` | RELRN-01 ticked; 02..05 named limitation | ✓ VERIFIED | `- [x] **RELRN-01**`; 4 rows containing "never exercised on a mitigated arm" |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `phase27_prereg.py` | `mitigation_gate.py` | `extraction_ceiling(` call; `mitigation_point_verdict` never imported | ✓ WIRED | 1 call; 0 occurrences of `mitigation_point_verdict` |
| `phase27_prereg.py` | `erasure_gate` / `phase23_prereg` / `mitigation_budget` | `MARGIN_K`, `noise_floor`, `CURVE_K` by reference | ✓ WIRED | 4 matches; the `is`-identity test is green |
| `tests/test_phase27_prereg.py` | `phase20_gate_coverage.py` | `corrected_point_verdict(**…)` on all 44 points | ✓ WIRED | 38 equal + 6 SystemExit asserted |
| `tests/test_phase27_prereg.py` | git history | `merge-base --is-ancestor` | ✓ WIRED | checked 1 = 1 × 1 |
| `loop.py` | `data.py` | `get_batch_memmap_masked(..., on_draw=on_draw)` ×2 | ✓ WIRED | Masked and replay sites only (WR-04) |
| `phase27_relearn.py` | `phase27_prereg.py` | `relearning_is_worth_attempting(` in `build_record`; legs read constants at call time | ✓ WIRED | Gate call at `:243` |
| `phase27_relearn.py` | `teach_persona.py` | `tp.train(..., on_draw=recorder)` + `tp.build_arm_bins` | ✓ WIRED | e2e spy records 10 real train calls |
| `phase27_relearn.py` | `phase24_adversarial.py` | `adversarial_episodes(tok)` for set (ii) | ✓ WIRED | 336 trained rows in the record |
| `phase27_relearn.py` | `results/phase27_admission.json` | `atomic_write_json` after write-once + dirty checks | ✓ WIRED | The record exists and re-derives |
| `tests/test_phase27_relearn.py` | driver `main()` | `relearn.main(["calibrate", ...])` under `_e2e_env` | ✓ WIRED | Legs reached through `DISPATCH` |
| record | frontier | `frontier_sha256` both ways | ✓ WIRED (test-time) | Enforced by the suite; the legs never read it at run time (CR-02 hole 3) |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `results/phase27_admission.json` verdict/rows/tallies/cleared | frontier point verdicts + 21 kwargs | `build_record(frontier())` over `results/phase25_frontier.json` | Yes — independent recount matches, and a hand-edit reddens `test_the_record_re_derives_from_build_record` | ✓ FLOWING |
| record `disjointness` | question strings | `phase16_recall_sample.json`, `render_episodes`, `adversarial_episodes`, attacker rows | Yes — planted row counted 1/0/1 and refused | ✓ FLOWING |
| leg outputs (calibration/curve/gate/structural) | rung readings | real `tp.train` + `tp.score_arm` + `phase25_run.draw_point_shapes`/`score_point` | Yes on the CPU fixture (meaningless numbers by design, D-31); never on real weights (MOOT) | ✓ FLOWING (fixture) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Gate reads MOOT on the measured frontier | `relearning_is_worth_attempting(json.load(frontier))` | `MOOT`; reasons == record's | ✓ PASS |
| Every leg refuses on the committed record | `scripts/phase27_relearn.py {calibrate,curve,gate,structural-proof} --leg n8` | 4/4 exit 1, stdout 0 B, stderr sha `efd445c8…` ×4 | ✓ PASS |
| Z calibrated before the mitigated arm is attacked | forged out-of-tree ADMITTED; curve/gate without prerequisites | 3/3 REFUSED, "run calibrate first" / "run calibrate and curve first" | ✓ PASS |
| Phase test files | `pytest -q tests/test_phase27_{prereg,on_draw,relearn}.py` | 69 passed in 50.10s | ✓ PASS |
| Provenance recompute | hashlib over 7 pinned modules | 7/7 equal | ✓ PASS |
| Lint / collection | `ruff check . && ruff format --check .`; `pytest --collect-only -q` | clean, 284 formatted; 2871 collected | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED. No probe is declared by any PLAN or SUMMARY, and `find scripts -path '*/tests/probe-*.sh'` is empty.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| RELRN-01 | 27-01, 27-03, 27-04, 27-05 | Absolute recovery ceiling as the binary pre-registered gate | ✓ SATISFIED (MOOT form, D-05) | Gate call + committed MOOT record. `recovery_gate` is committed and guarded, never evaluated on a mitigated arm, and the row says so |
| RELRN-02 | 27-01, 27-03, 27-04, 27-05 | Cost-to-recovery curve vs the never-taught fresh adapter | NOT SATISFIED — named limitation, by design (D-05) | Row reads "not admitted by the gate; apparatus built and guarded, never exercised on a mitigated arm". The apparatus is verified as SC3 above |
| RELRN-03 | 27-01, 27-03, 27-04, 27-05 | The curve qualifies, not a second gate | NOT SATISFIED — named limitation, by design | Same limitation sentence; SC4 verified as code |
| RELRN-04 | 27-01, 27-02, 27-03, 27-04, 27-05 | Identical budget and seed enforced structurally | NOT SATISFIED — named limitation, by design | Same sentence. The row names "the three proofs of run_structural_proof" without claiming (iii) refuses. Accurate, though WR-02 shows (iii) is only recorded |
| RELRN-05 | 27-01, 27-03, 27-04, 27-05 | Disjoint fixture; attacker corpus pre-registered | NOT SATISFIED — named limitation, by design | Same sentence. `overlaps teaching 0` is literal to the record; IN-04: the teaching set checked is the n=8 rows only |

**Orphan check:** REQUIREMENTS maps exactly RELRN-01..05 to Phase 27, and every plan declares a
subset of them. 5/5 accounted for, 0 orphaned. The ledgers say what D-05 decided and nothing more.
The one sentence that goes further, RELRN-01's "SATISFIED … in its MOOT form", is qualified in the
same row: "The gate was never evaluated on a mitigated arm".

## Code Review Rulings (27-REVIEW.md, `a1dec50`)

Each Critical and Warning was treated as a hypothesis and settled by the cheapest CPU experiment
(scripts in this session's scratchpad `27-verify/`; tmp trees only, weights never loaded, the real
record only read). Classification key: **FALSIFIED** / **REAL BUT INCONSEQUENTIAL** (for this phase's
goal) / **REAL AND FORWARD-LOOKING** (names where it becomes live).

| ID | Claim | Experiment output (verbatim excerpts) | Ruling |
|---|---|---|---|
| CR-01 | The D-18 attacker-corpus pin switches itself off when the corpus drifts | Real facts: rows sha == pin `True`, n_rows 176. **(A)** real facts + a wrong bin pin → `REFUSED`. **(B)** `cand_person_quillon 'quillon' -> 'quillons'` (ids and count unchanged `True`) → drifted rows sha == pin `False` → `REACHED model load (the pin did not refuse)`; drifted bin sha == pinned `False`. Grep over `tests/` for the refusal text / `corpus_pin_checked`: 0 hits. `corpus_pin_checked` is only referenced in `train_relearn_arm` (AST: `:573`, `:578`, `:686`) and never in `run_structural_proof` | **REAL AND FORWARD-LOOKING.** It becomes live at the first `calibrate`/`curve` on an ADMITTED record. It also departs from 27-03's own specified rule ("compare `len` and ids"), which would have refused (B); 27-03-SUMMARY deviation 8 made the change. The refusal is never watched RED in any test. |
| CR-02 | Legs are passable without a committed record, and they trust record keys over the frontier | **H1** (read-only git): `.claude/scheduled_tasks.lock` status `D`, on disk `False`, yet `git ls-files` lists it. `ls-files` reads the index, not working-tree state, and `_require_admitted`'s only git argv is `['git', 'ls-files', _rel(path)]` with no HEAD byte comparison. **H2**: `dp_n8_sigma0p500000` frontier verdict `FAIL`, prereg admitted keys `()`. `main(['curve', '--record', <out-of-tree forged ADMITTED>])` → `training reached for dp_n8_sigma0p500000 sha 933506081d53`. **H3**: a frontier copy with that pin moved → `training reached … sha eeeeeeeeeeee`. AST: `admitted_point_keys(…)` is called only in `build_record:305`; legs read the record key at `:878/:961/:1138`; `frontier_sha256` appears only at `build_record:311`. Default path → `reads 'MOOT' — REFUSING` | **REAL AND FORWARD-LOOKING.** It becomes live at the first ADMITTED record, where a forged or edited record could choose the attacked points. Today it needs deliberate operator action and yields only untracked scratch outputs. |
| WR-01 | `admit` can never write an INCONCLUSIVE reading | 4/4 INCONCLUSIVE copies (moved total tally, moved per-leg tally, 43 points, bare None) → gate `INCONCLUSIVE`, `build_record` → `SystemExit` (e.g. `43 rows, 44 expected (D-33)`); no record | **REAL BUT INCONSEQUENTIAL.** The committed frontier reads MOOT and the record exists. The failure direction is conservative: no record means every leg refuses as "absent", and nothing ever reads a false MOOT or ADMITTED. It could only matter on a partial or re-emitted frontier, which D-06's suite guard reddens first. |
| WR-02 | `structural-proof` exits 0 without the mitigated arm and with a false data-order equality | `structural-proof n8: 2 arm reading(s); equal streams at the designated seed: False` → returned: admitted `['dp_n8_sigma0p500000']`, arms proved `['control_seed1337', 'fresh_seed1337']`, `equal_across_arms_at_designated_seed False` | **REAL AND FORWARD-LOOKING.** It becomes live at the first `structural-proof` on an ADMITTED record. Recording (iii) instead of refusing was planned (27-03 task 9). The missing coverage check for mitigated arms was not. |
| WR-03 | A live leg writes run CSVs under `results/phase27_*`, and the wiring proof then stays RED on that host | `csv results/phase27_relearn_attacker_n8_fresh_seed1337/run.csv \| gitignored: False \| … matches ARTIFACT_GLOB: True`; bin/mask/checkpoint gitignored `True`. The e2e's own scanner after one live leg sees `['data/persona_relearn_attacker_n8_fresh_seed1337_train.bin', 'results/phase27_relearn_attacker_n8_fresh_seed1337']`, so `strays == ([], [])` is `False` | **REAL AND FORWARD-LOOKING.** It becomes live at the first live leg on a host. After that the e2e is RED there, `results/` porcelain probes redden, and the ancestry guard would redden if the CSV were ever committed. |
| WR-04 | `train(on_draw=...)` silently records nothing on the unmasked and fact-aligned branches | masked: `['train.bin', 'train.bin']`; **unmasked, no replay: `[]` no error**; unmasked + replay: 4 replay draws only; the empty stream hashes to `e3b0c44298fc1c14` for every arm | **REAL BUT INCONSEQUENTIAL.** The driver always passes `train_mask_bin` and never `fact_bin` (`phase27_relearn.py:612-613`), so it takes the threaded branch, where the e2e proves `draws == rungs × (1 + replay)` and the tag layout. It matters only for a future caller on another branch. The `loop.py:469-475` docstring overclaims. |
| WR-05 | The adversarial arm is calibrated against the DP control, not the one the frontier judged it against | `control_readings` keys `adv_n64, adv_n8, dp_n64, dp_n8`; `dp_n8 taught [790, 1008]`, `adv_n8 taught [879, 1008]`; `recall_threshold(fr,'n8') = 0.548611111111111` vs adv_n8 points' own `0.6104166666666666`; adv_n8 verdicts `['INCONCLUSIVE']`, adv_n64 `['REFUSED']`; any adversarial control pinned `False`; `leg_of` puts both arms in `n8` | **REAL AND FORWARD-LOOKING, plus a DECISION-COVERAGE GAP.** The code follows D-12/D-24/D-28 as written (D-24's own worked numbers are the DP control's). No decision considered that adversarial points have their own control. Latent: 0 of 12 adversarial points are admissible from the committed frontier. It becomes live at the first ADMITTED reading containing an `adv_*` point, i.e. a re-emitted frontier from the v5.0 adversarial re-measurement Phase 28 SC4 defers. Needs a ruling (human item 2). |
| WR-06 | The required `baseline` never affects the verdict, and a re-run of `gate` overwrites the published output | `0/416 z=100` → `['PASS']` over 7 baselines; `1/416` → `['FAIL']`; `z=None` → `['INCONCLUSIVE']`; a second `atomic_write_json` replaced the first (`{'baseline': 'control_n8', …}`) | **REAL AND FORWARD-LOOKING (low severity).** It becomes live at the first `gate` run. The verdict cannot move; the published baseline label can. |

### Do CR-01 / CR-02 make anything FALSE as shipped?

- **Must-haves:** no. 27-03 must-have #2 designs in "(when inside the repo) be git-tracked", and no
  must-have claims a leg-time frontier cross-check or a leg-time corpus refusal. **SC2–SC5 "TRUE as
  guarded code": still true, in a form weaker than a future ADMITTED run needs.** The guards that
  matter for such a run (committed-bytes check, key/frontier re-derivation, both-pin corpus refusal,
  mitigated-arm coverage) are missing, and the D-09 tests pass without them.
- **D-08:** TRUE on the sanctioned path. With the default `--record`, the committed MOOT record makes
  4 of 4 legs refuse, and all 12 parametrized refusals plus the moved-pins and untracked cases are
  green. Its universal wording is **FALSE outside that path**: an out-of-tree record passed through the
  public `--record` flag, or a tracked record edited in the working tree, runs a leg (H1/H2).
  "Committed" is enforced as "tracked". The out-of-tree skip is a designed test seam, and a committed
  test (`test_an_admitted_tmp_record_passes_the_gate_without_git`) asserts it.
- **D-22:** TRUE on the sanctioned path (`admit` writes exactly the PASS keys in `point_keys` order,
  and the legs attack every key per leg; the two-point e2e proves both). **FALSE under a forged or
  edited record**: the legs never re-derive the keys from the frontier (H2).
- **D-12:** TRUE as shipped. The baselines are pinned by path + sha256 + seed; `_require_admitted`
  refuses moved pins (test); `recovery_gate` refuses unpinned keys; and `model_from_adapter` refuses a
  sha mismatch before loading. Nothing in the experiments bypassed it.
- **D-18:** TRUE as shipped. The corpus definition and both sha pins are committed data at
  `916ad4d`, carried in the record, and re-rendered by `test_attacker_corpus_sha_re_renders`, whose
  first assertion evaluates `False` under the measured drift, so the suite goes RED. Only the
  **run-time** refusal is weaker (CR-01).
- **Phase goal (MOOT form):** unaffected. No finding touches the committed record's correctness,
  which I re-derived independently above.

### WR-05 as a decision-coverage question

D-12 pins "the retrained unmitigated control (the Phase 25 `dp_n8` / `dp_n64` σ=0 points)". D-24
defines "clear" as "the frontier's own condition (b)" and instantiates it with the DP control's
numbers. D-28 fixes "ONE Z PER CAPACITY LEG". None of the three considered that the frontier judged
adversarial points against `control_readings["adv_<leg>"]`. For an adversarial point, D-24's stated
rationale ("clear means what it meant on the frontier") and the CONTEXT promise ("attackable in v5.0
without any decision being re-opened") therefore cannot both hold. The implementation is faithful to
the decisions; the decisions do not cover this arm. That is a gap for the developer to rule on (human
item 2), not an execution defect.

### Info findings (summarised, no experiments required)

- **IN-01:** `build_record`'s cleared-count `_prove` compares `cleared_abc` with itself. The counts are guarded elsewhere (hard-coded 30/4/1 test + my recount).
- **IN-02 (checked anyway, one call):** `recovery_gate` raises `ValueError` rather than returning FAIL when X is unreachable at n < 416 (`0/104` → `ValueError … wilson_upper_bound(0, 104) = 0.025355…`). It is latent (production n is always 416), but the e2e comment at `tests/test_phase27_relearn.py:769-772` is wrong.
- **IN-03:** the gate reads MOOT on a frontier with a duplicated key. The committed frontier has 44 unique keys (measured).
- **IN-04:** the disjointness teaching set covers only the n=8 rows. The n=64 filler rows were never compared (the reviewer measured 0 overlap).
- **IN-05:** `on_draw` receives the live `ix` array. The driver copies it (`astype`).
- **IN-06:** `admit` does not resolve `--out`. A hypothesis, not run.
- **IN-07:** a test writes a probe record into the real `results/phase27_*` glob, protected by `finally`. My run left `git status` clean.
- **IN-08:** the record pins 7 modules, two more than D-35's five. A deliberate choice, and the reason every fix above must be a continuation or a delete-and-re-admit.

### Recommended carry

Carry all of them as **named limitations**, not fixes. Every fix touches bytes the operator-committed
record pins (7 modules; `test_provenance_digests_match_live_bytes` reddens), and any edit to
`phase27_prereg.py` reddens the ancestry guard permanently. Re-issuing therefore means deleting the
record in its own commit and re-running `admit`, which is churn that cannot change MOOT. Concretely:

1. Add them to Phase 28's RPT-03 named-limitation list beside RELRN-02..05.
2. State the obligation for whichever phase first reads ADMITTED: before its first leg, its
   continuation driver/pre-registration continuation must (a) refuse unless both corpus pins hold
   (CR-01), (b) compare the record's bytes with HEAD, re-derive `admitted_point_keys` and check
   `frontier_sha256` at leg time (CR-02), (c) require every expected arm reading and refuse on
   diverging streams (WR-02), (d) route run CSVs under the gitignored out-dir (WR-03), (e) pre-register
   one gate baseline per leg and refuse to overwrite a gate output (WR-06), and (f) rule on WR-05 before
   any `adv_*` admission.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `scripts/phase27_relearn.py` | 573-581 | Guard that disables itself (`not corpus_pin_checked or …`) | ⚠️ Warning | CR-01; latent under MOOT |
| `scripts/phase27_relearn.py` | 160-172 | Out-of-tree record skips the tracked conjunct, reachable via public `--record` | ⚠️ Warning | CR-02; designed test seam |
| `scripts/phase27_relearn.py` | 282-287 | Tautological `_prove` | ℹ️ Info | IN-01 |
| `src/personacore/training/loop.py` | 469-475 | Docstring overclaims coverage ("every offset a step consumes") | ℹ️ Info | WR-04 |
| `tests/test_phase27_relearn.py` | 769-772 | Comment says FAIL; the call raises | ℹ️ Info | IN-02 |

Debt markers: 0 `TBD`/`FIXME`/`XXX` and 0 `TODO`/`HACK`/`placeholder` in the 8 phase files. No blocker.

### Disconfirmation pass

- **Partially met:** RELRN-04/SC5's data-order proof is recorded rather than enforced, and the leg does
  not require the mitigated arm (WR-02). SC2's "evaluated" baseline is inert (WR-06).
- **A test that passes without testing the stated behaviour:** the e2e runs with
  `corpus_pin_checked: false` (synthetic facts), so the D-18 runtime refusal is never exercised, and
  `test_an_admitted_tmp_record_passes_the_gate_without_git` asserts the CR-02 seam as intended.
- **Error paths with no test:** the driver's bin-pin refusal (I watched it refuse only with real facts
  and a wrong pin), and the curve/gate ordering refusals (I watched 3/3 refuse; no committed test).

## Human Verification Required

### 1. Carry ruling for the latent review findings

**Test:** Decide how CR-01, CR-02, WR-02, WR-03 and WR-06 (and the inconsequential WR-01, WR-04) are carried. None has an owning phase today.
**Expected:** A recorded ruling. Recommended: named limitations in Phase 28's RPT-03 list, plus the stated obligation (a)–(f) for the first phase that reads ADMITTED. The alternative is an explicit decision to re-issue the operator-committed record.
**Why human:** Re-issuing an operator-committed record and assigning an owning phase are developer decisions. They cannot be settled programmatically.

### 2. WR-05 decision-coverage ruling (adversarial arm's control)

**Test:** Decide which control an adversarial point's Z threshold and control pin read. Today the code reads `dp_<leg>` (790/1008 → 0.5486), but the frontier judged `adv_n8` against its own control (879/1008 → 0.6104), and no adversarial control adapter is pinned.
**Expected:** A dated ruling before any `adv_*` point can be admitted. One option is a pre-registration continuation that keys the threshold/pin/Z by (arm, leg). Another is a refusal to admit `adv_*` points with its reason. A third is acceptance of DP-control calibration with its reason stated.
**Why human:** It re-opens the scope of locked decisions D-12/D-24/D-28. It is latent today (0 of 12 adversarial points admissible) but breaks the "no decision re-opened in v5.0" promise for that arm.

## Gaps Summary

**No gap blocks the phase goal.** The phase set out to prove adversarially that what survived the
mitigation cannot be cheaply reverted, or to record measurably that it can. It reached the
pre-registered branch where nothing survived: one gate call on the measured frontier wrote a MOOT
record (0 of 44 PASS; (a) 30 / (b) 4 / (c) 1 over 38 reached). I re-derived that record independently,
and it is pinned to the frontier both ways, committed by the operator and descended from a one-commit
pre-registration. SC2–SC5 exist as committed, CPU-tested code, wired end to end through `main()` on the
real train and score paths, and every leg refuses on the committed record (4 of 4 watched).
RELRN-02..05 are unticked exactly as D-05 decided.

The code review's findings are **real**. Every Critical and Warning reproduced, and none was falsified.
They are **latent under MOOT** and concentrate in one concern: the run-time guards a future ADMITTED
attack depends on. Those guards are weaker than the decisions' prose: the committed-record check, the
key/frontier re-derivation, the corpus pin, structural-proof coverage, the baseline label, and the
adversarial control's scope. They do not make any must-have false. They do make D-08's and D-22's
universal wording false outside the sanctioned path, and they leave WR-05 as a decision gap. Status is
`human_needed` for the two rulings above, not `gaps_found`.

---

_Verified: 2026-09-16T22:11:40Z_
_Verifier: Claude (gsd-verifier)_
