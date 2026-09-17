---
phase: 27
slug: relearning-attack
status: verified
threats_open: 0
threats_total_rows: 35
threats_distinct_ids: 14
asvs_level: 1
created: 2026-09-16
audited_at_head: b627997
---

# Phase 27 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (`register_authored_at_plan_time: true`). This document
> **verifies** the declared mitigations exist in implemented code. It does **not** scan for
> new threats.

**Gate status: CLOSED.** `threats_open: 0`. 35 register rows across 5 plans, **14 distinct threat
IDs**, every row resolved to `closed` (by a verified mitigation, or by a logged accepted risk for the
two `accept` IDs). Ten accepted-risk rows (AR-27-01 … AR-27-10): two are the plan-time `accept`
dispositions (T-27-13, T-27-SC); **eight are residuals** — the confirmed-but-latent code-review
findings the developer ruled on 2026-09-16 (`27-HUMAN-UAT.md` rulings 1 and 2, carried by
`.planning/todos/pending/phase28-carry-phase27-latent-review-findings.md`), each logged under the
threat whose guard it weakens. **No plan-stated mitigation was found absent or contradicted**: every
ruled residual weakens a guard a future ADMITTED run depends on while the plan sentence itself holds.
One unruled review finding (IN-03) bears on T-27-02 and is recorded as Finding S-2, deliberately NOT
accepted here (the ruling names specific findings; this audit does not extend it).

---

## Boundary of this audit — read this first

What was done (auditor: gsd-security-auditor, State B from the plan-time register, HEAD `b627997`,
CPU only, every scratch write under this session's scratchpad `27-secure/`):

- **Register extracted** from all five `<threat_model>` blocks: 27-01 (6 rows), 27-02 (3), 27-03
  (11), 27-04 (7), 27-05 (8) = 35 rows, 14 IDs (T-27-01 … T-27-13, T-27-SC). IDs recur across plans
  by design; rows are keyed on (threat_id, plan, component).
- **Guard suites re-run:** `PERSONACORE_SWEEP_ACTIVE=1 .venv/bin/pytest -v -rs -p no:cacheprovider
  tests/test_phase27_prereg.py tests/test_phase27_on_draw.py tests/test_phase27_relearn.py` →
  **69 passed in 49.89s, 0 skipped, 0 failed**. T-27-10's golden suites plus three census nodes
  (`tests/test_lora_training.py tests/test_loop_penalty_fn.py tests/test_phase22_wiring.py
  tests/test_phase23_resume.py tests/test_phase21_replay_volume.py::test_replay_seam_draws_exactly_the_public_budget
  tests/test_lora_inject.py::test_every_inject_lora_consumer_reads_the_artifact_config
  tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module
  tests/test_phase25_close.py::test_the_frontier_artifact_is_unchanged_since_its_single_write`) →
  **42 passed, 2 skipped in 25.92s**; the 2 skips are the MPS legs `tests/test_phase23_resume.py:509`
  and `:694`, skipped by the flag on purpose. After both runs `git status --short` showed only the
  pre-existing ` D .claude/scheduled_tasks.lock`, and `find data -maxdepth 1 \( -name 'phase27_*' -o
  -name 'phase25_phase27_*' -o -name 'persona_relearn_attacker_*' \)`, `find results -maxdepth 1 -name
  'phase27_*'` and `find checkpoints -maxdepth 1 -name '*phase27*'` returned nothing beyond the tracked
  record.
- **Git facts measured:** non-shallow (`false`); `scripts/phase27_prereg.py` at exactly one commit
  `916ad4d`; `git ls-tree -r --name-only 916ad4d -- results | grep '^results/phase27_'` → none;
  `git ls-files 'results/phase27_*'` → `results/phase27_admission.json` only; that record is touched by
  exactly one commit, `88dff77` (first-add, parent `e308675`, 1 file / 1 insertion);
  `git merge-base --is-ancestor 916ad4d 88dff77` → exit 0; `results/phase25_frontier.json` at exactly
  one commit `4030d0e`; `git log 88dff77..HEAD -- results/` → none.
- **Record, provenance, frontier recomputed** (`s1_record.py`, stdlib + torch-free prereg): record
  sha256 working tree = `HEAD` blob = `88dff77` blob = `065b2bc1…`; 20 keys, verdict MOOT, 7 reasons,
  `admitted_point_keys []`, apparatus `not exercised` / `gate read MOOT`; `frontier_sha256` and
  `frontier_bytes` equal the on-disk frontier (`1f182b40…`); 7 of 7 `provenance.module_sha256` equal
  both the live bytes and the `e308675` blobs; `git_sha == head_at_write == e308675`; frontier 44
  keys, 44 unique, set-equal to 44 points, equal to `phase25_record.ORDERED_POINT_KEYS()`; the live
  gate returns MOOT with reasons equal to the record's; `adv_*` verdict strings INCONCLUSIVE 6 /
  REFUSED 6 / PASS 0.
- **Guards watched refusing** on deep copies and scratch paths (`s2_guards.py`; no weights loaded, no
  training; loaders/builders stubbed to raise so "not reached" is observable) — quoted per row below.
- **D-37 re-watched** on the committed record: `.venv/bin/python scripts/phase27_relearn.py
  {calibrate,curve,gate --baseline never_taught_1337,structural-proof} --leg n8` → 4 of 4 exit 1,
  stdout 0 bytes, stderr sha256 `efd445c86b24e752794ff7df6baee9be234cd9f809c7e608bead8bb377c73b61`
  ×4 — byte-identical to the eight captures in `27-05-SUMMARY.md`; record sha unchanged; data finds
  empty.

What was **not** done:

- `admit` was not run against the real record; no attack leg ran except the four watched refusals;
  nothing ran on MPS.
- The full suite was not re-run (orchestrator: 2867 passed / 4 skipped / 0 failed, 2871 collected at
  `1fa6f60`; `git diff --stat e308675..HEAD -- scripts src` is empty).
- The experiments behind CR-01, CR-02, WR-01 … WR-06 were not repeated; their outputs are cited from
  `27-REVIEW.md` (`a1dec50`) as reproduced by `27-VERIFICATION.md` (`0ab0e53`).
- No new-threat scan. Info findings IN-01 … IN-08 are classified only where they bear on a register
  row (Findings S-2, S-5).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| `results/phase25_frontier.json` → `phase27_prereg` | Committed artifact read as data; pinned by sha256 and single commit; never re-emitted (27-01) | 44 point verdicts + 21 stored kwargs each, control readings |
| git history → ancestry guard | Ordering proof needs a non-shallow clone (`fetch-depth: 0`) (27-01) | commit graph |
| `phase23_never_taught_training.json` + two Phase-25 control records → `PINNED_BASELINES` | Source records re-read by the test; the module carries copied digests (27-01) | 7 adapter paths / sha256 / seeds |
| `train()` → `get_batch_memmap_masked` | Production loader edited additively; `None` forwards nothing; `estimate_loss` untouched (27-02) | global-NumPy offsets |
| recorder callback → `data/` sidecar | Callback receives the raw `ix`; the driver's recorder copies it (`astype`) (27-02) | offset stream bytes |
| `results/phase27_admission.json` → every leg | The committed record is the only admission input; refusal on verdict, moved pins, tracking (27-03) — "tracked", not "committed bytes": AR-27-03 | verdict, admitted keys, baselines |
| driver → git | Read-only: one `ls-files` argv; helpers use `rev-parse` / `status` (27-03) | none written |
| `checkpoints/` + frontier adapter paths → `model_from_adapter` | sha256 pin refused before any load; adapter/base via `weights_only=True` (27-03) | untrusted pickle bytes |
| driver → `data/` | Bins, rung adapters, offset streams, leg JSON, draw caches under gitignored `data/` / `checkpoints/` — **except the run CSV, which lands under `results/`** (threat flag; AR-27-09) (27-03) | sidecars |
| driver → device | One resolver `phase25_run.device()`; no refused leg reaches it; the wiring proof pins it to CPU (27-03) | device string |
| tests → driver → train path | E2E redirects paths, budgets, device cache, pins, frontier copy; train and score paths stay real (27-03, 27-04) | fixtures |
| tmp tree ↔ real tree | E2E writes only under `tmp_path`; real `data/`, `results/`, `checkpoints/` and the record asserted untouched (27-04) | none |
| record ↔ suite | Node ids and module digests checked against a fresh interpreter and live bytes, both-state (27-04) | digests, node ids |
| operator → git | The only git write of the record is the operator's commit (27-05; evidence limitation S-3) | one commit |
| `results/phase27_admission.json` → Phase 28 | Phase 28 quotes the record by sha256, never the prereg prose (27-05) | published verdict, limitations |
| the real record → the four sub-modes | Refusals watched on the real record, untracked and committed, CPU, no training (27-05) | stderr transcripts |
| ledgers ← hand edits | Snapshot → edit → diff; zero `gsd-sdk` mutation handlers (27-05) | planning text |

---

## Threat Register

Line numbers are at HEAD `b627997`. "PASSED" = observed in this audit's runs quoted above.
Residual risks are cross-referenced to the Accepted Risks Log.

| Threat ID | Category | Component (plan) | Disposition | Mitigation (verified at HEAD `b627997`) | Status |
|-----------|----------|------------------|-------------|------------------------------------------|--------|
| T-27-01 | Tampering | (27-01) `scripts/phase27_prereg.py` — gate shaped after data | mitigate | ONE commit before any record: `git log -- scripts/phase27_prereg.py` → `916ad4d` only; no `results/phase27_*` in `916ad4d`'s tree. Ancestry guard `tests/test_phase27_prereg.py:74-115` PASSED (non-shallow, strict ancestor, same-commit refusal, 1 prereg × 1 tracked). X by call `phase27_prereg.py:253` (`mitigation_gate.extraction_ceiling(`) + AST float-literal scan `test_x_is_the_frontier_ceiling_by_call_not_literal` PASSED. By-reference `is` pins `test_constants_are_by_reference` PASSED. `grep -c mitigation_point_verdict` → 0 in `phase27_prereg.py` and `phase27_relearn.py`; census `tests/test_phase20_correction.py:1377` PASSED. Residual AR-27-01 (CR-01) | closed |
| T-27-02 | Repudiation | (27-01) `relearning_is_worth_attempting` — "could not tell" read as MOOT | mitigate | `VERDICTS` three-valued (`:119`); every INCONCLUSIVE check precedes ADMITTED/MOOT: `None` `:352-353`, count/set `:356-364`, domain `:365-368`, total tally `:369-378`, per-leg tally `:379-390`. `test_partial_or_inconsistent_frontier_is_inconclusive` PASSED (43 points, FAIL 31, per-leg 15, `MAYBE`, `None`, bare `None`). Sole production caller `phase27_relearn.py:243` (grep over `scripts/`). Residual AR-27-02 (WR-01); unruled Finding S-2 (IN-03) | closed |
| T-27-03 | Tampering | (27-01) re-emitted frontier | mitigate | `test_the_record_is_pinned_to_the_frontier_both_ways` (`:118-130`; the one-commit assertion at `:130` sits outside the both-state branch) PASSED on its PRESENT branch; `git log -- results/phase25_frontier.json` → `4030d0e` only; record `frontier_sha256`/`frontier_bytes` equal the on-disk file. Route tripwire `test_every_frontier_verdict_re_derives_through_the_route` PASSED (38 equal, 6 `SystemExit`, perturbed copy disagrees) | closed |
| T-27-05 | Tampering | (27-01) baseline chosen after seeing data | mitigate | `recovery_gate(*, …, baseline)`: measured `KEYWORD_ONLY`, default `Parameter.empty`; `_prove(baseline in PINNED_BASELINES)` is its first statement (`:587-591`) → `baseline='made_up'` SystemExit (measured). Seven pins path + sha256 + seed (`:130-181`); `test_baselines_are_pinned_from_the_records`, `test_pinned_adapters_hash_on_host` (ran, not skipped), `test_gate_baseline_is_required_and_pinned` PASSED. Residuals AR-27-06 (WR-06), AR-27-07 (WR-05) | closed |
| T-27-09 | Tampering | (27-01) point keys / arm names | mitigate | `admitted_point_keys` subsequence `_prove` (`:432-436`) watched: PASS keys swapped out of order → `SystemExit: … are not a subsequence of phase25_record.ORDERED_POINT_KEYS()`; a PASS key renamed off the grid → SystemExit; in-order control returned both keys. `CONTROL_KEYS` (`:121`) both present as `dp` σ=0 frontier points. `first_clear` rung 75 → `SystemExit: rung 75 is off the pre-registered ladder` (`:503`); `test_z_rule_table` ×6 PASSED | closed |
| T-27-SC | Tampering | (27-01) package installs | accept | AR-27-10 | closed |
| T-27-10 | Tampering | (27-02) `src/personacore/training/{data,loop}.py` — byte-identity regression | mitigate | `git diff d528710 58ee800`: `data.py` adds only `*, on_draw=None` (`:93`) and the guard `if on_draw is not None: on_draw(bin_path, ix)` (`:122-123`); `loop.py` forwards `**({} if on_draw is None else dict(on_draw=on_draw))` (`:661`, `:706`), so the `None` call is the pre-change call — the fixed-signature loader fake `tests/test_phase21_replay_volume.py::test_replay_seam_draws_exactly_the_public_budget` PASSED; `estimate_loss` (`:88-131`) contains 0 `on_draw`. `test_on_draw_none_is_byte_neutral` PASSED. Golden suites re-run here: 42 passed / 2 skipped (the 2 MPS legs, flag; not run on MPS in this audit — the orchestrator's unflagged `make test` at `88dff77` reported 0 failed) | closed |
| T-27-04 | Denial (of evidence) | (27-02) recorder reachability | mitigate | `test_offset_stream_hash_covers_every_draw` (`tests/test_phase27_on_draw.py:149-181`: spy sees `[(train,2),(replay,2),(replay,1)]×2`, asserts no val-bin call, recorder order == spy order) and `test_rung_chain_stream_equals_one_run` (`:199-233`: equal sha, equal draws, `torch.equal` adapters, re-seed before resume) PASSED through the real `train()`. Residual AR-27-05 (WR-04) | closed |
| T-27-SC | Tampering | (27-02) package installs | accept | AR-27-10 | closed |
| T-27-01 | Tampering | (27-03) record rows shaped after data | mitigate | `build_record` derives rows through `phase27_prereg.cleared_abc` (`phase27_relearn.py:246-260`) and `_prove`s 44 rows (`:264-267`), row verdicts vs `verdicts.tallies` (`:269-273`) and per-leg (`:274-281`) at the single write — the tally `_prove` is live: it refused the IN-03 copy (S-2). Flip-one-row RED on a deep copy inside `test_admit_writes_the_full_schema_to_a_tmp_path` (`tests/test_phase27_relearn.py:303-316`) PASSED. Note S-5 (IN-01) | closed |
| T-27-04 | Denial (of evidence) | (27-03) unwired live path behind green refusals | mitigate | `test_main_passes_only_kwargs_the_legs_accept` (AST + `inspect.signature`; tmp-copy `baselne` RED) PASSED; `test_every_leg_opens_with_require_admitted` PASSED — first statement `blob = _require_admitted(record)` at `:764`, `:867`, `:946`, `:1066`; e2e `test_the_live_path_is_wired_end_to_end` PASSED. Residual AR-27-04 (WR-02) | closed |
| T-27-05 | Tampering | (27-03) baseline chosen after data | mitigate | `--baseline` `choices=phase27_prereg.BASELINE_KEYS, required=True` (`:1177-1181`) — parse without it → `SystemExit: 2` (measured); the sole `recovery_gate` call site (AST count 1) passes `baseline=baseline` (`:971-978`); `_require_admitted` refuses moved pins (`:155-159`). `test_a_record_with_moved_pins_is_refused`, `test_gate_cli_requires_a_pinned_baseline` PASSED. Residuals AR-27-06, AR-27-07 | closed |
| T-27-06 | Tampering | (27-03) pickle deserialisation of adapters / base | mitigate | Driver loader calls (AST): `ckpt_mod.load_slim` `:497`, `ckpt_mod.load_adapter` `:500`, `ckpt_mod.load_checkpoint` `:660` — nothing else; 0 `torch.load` / `tp.torch.load` attribute nodes; `test_the_driver_never_calls_torch_load_directly` PASSED. Adapter and base cross `weights_only=True` (`src/personacore/checkpoint.py:244`, `:296`); scorers load through `pr.load_adapted_model` → `load_slim`/`load_adapter`. `load_checkpoint` is `weights_only=False` (`checkpoint.py:175`) — sanctioned by this row's text and fed only a checkpoint the same arm run wrote first (Finding S-4) | closed |
| T-27-07 | Repudiation | (27-03) provenance from a dirty tree | mitigate | AST of `admit` body: overwrite `_prove` (stmt 2) → `refuse_if_dirty` (stmt 5; stmts 3-4 only build the pathspec) → `build_record(frontier())` (stmt 6, where `frontier_sha256` is hashed) → `disjointness_report` (7) → module digests / `git_sha()` (10) → `atomic_write_json` (11). `refuse_if_dirty` = `git status --porcelain -- <pathspec>` → `SystemExit` (`src/personacore/provenance.py:73-78`). `test_admit_refuses_a_dirty_tree_before_hashing` PASSED (recorded pathspec incl. exclude; refusing stub leaves no file; `disjointness_report` tripwire) | closed |
| T-27-08 | Elevation | (27-03) driver git surface | mitigate | AST: the driver's only git argv is `["git", "ls-files", …]` inside `_require_admitted` (`:161-167`), 1 `subprocess.run` call site; the provenance helpers it calls use `rev-parse` (`provenance.py:36`) and `status` (`:73`) — all members of `phase25_run.READ_ONLY_GIT_ACTIONS` (`ls-files`, `show`, `rev-parse`, `status`). `test_the_drivers_git_surface_is_read_only` PASSED (planted `add` RED on a copy) | closed |
| T-27-09 | Tampering | (27-03) point keys / arm names / paths | mitigate | Record keys come from `phase27_prereg.admitted_point_keys` (`:305`); `--leg` `choices=LEGS` (`:1175`; `n16` → exit 2, measured); `_prove(arm in ARMS)` (`:554`; `'bogus'` → SystemExit before `build_arm_bins`, measured) and the mitigated ⇔ `point_key` pairing (`:555-559`; measured); labels composed only from leg / arm / key / seed / rung / k (`:560-561`, `:593`, `:789-790`, `:900`, `:1009`); `score_rung` `_k{k}` suffix `_prove` (`:713-717`; measured); `phase25_run.draws_path('../evil')` → phase25_prereg charset SystemExit (measured). Residuals AR-27-03 (CR-02), AR-27-07 (WR-05) | closed |
| T-27-11 | Spoofing | (27-03) wrong-weights adapter attacked or scored | mitigate | `model_from_adapter`'s sha `_prove` (`:491-496`) precedes `load_slim` (`:497`) — watched with both loaders stubbed to raise: wrong sha → `SystemExit: … not the pinned 0000… — REFUSING to attack the wrong weights`, loaders not reached; matching sha → `RuntimeError: LOADER REACHED` (control). Called from `train_relearn_arm` (`:589`) before the first `tp.train` (`:607`); pins from the record's baselines (`:774-782`) or the frontier entry (`:885-895`); `run_gate` re-hashes the Z-rung adapter (`:1003-1007`). Residual AR-27-03 (CR-02) | closed |
| T-27-12 | Tampering | (27-03) provenance drift | mitigate | `admit` records `module_sha256` over the 7 `PINNED_MODULES` from bytes (`:399`); recomputed from bytes (never via `relearn._sha256`) in `test_admit_writes_the_full_schema_to_a_tmp_path` (`:286-289`) and `test_provenance_digests_match_live_bytes` — both PASSED; `s1_record.py`: 7/7 equal live bytes and the `e308675` blobs | closed |
| T-27-13 | Information disclosure | (27-03) `data/` sidecars | accept | AR-27-08; flagged run-CSV write surface → AR-27-09 (WR-03) | closed |
| T-27-SC | Tampering | (27-03) package installs | accept | AR-27-10 | closed |
| T-27-03 | Tampering | (27-04) hand-edited record | mitigate | `test_the_record_re_derives_from_build_record` (`tests/test_phase27_relearn.py:1251-1289`) PASSED on its PRESENT branch: 15 fields plus `apparatus.legs` equal a fresh `build_record(frontier())`; flipped-row deep copy names `["rows"]`. 27-01's both-ways pin PASSED. Residual AR-27-03 (CR-02) | closed |
| T-27-04 | Denial (of evidence) | (27-04) unwired live path | mitigate | `test_the_live_path_is_wired_end_to_end` PASSED: `main()` → 4 legs → 10 real `tp.train` calls, every device `cpu`, promotion K 8 → 16 under separate `_k8_` / `_k16_` caches, scorer module + source-file identity captured inside the patch context (`:853-862`, `:998-1004`); `test_every_apparatus_node_id_exists` PASSED (fresh-interpreter `--collect-only`, record PRESENT branch, misspelled-copy RED) | closed |
| T-27-05 | Tampering | (27-04) baseline after data | mitigate | E2E passes `--baseline never_taught_1337` (`:849`) and asserts `gate["baseline"]` (`:968`); AST caller pin `test_the_curve_cannot_reach_the_verdict_through_the_driver` PASSED (one call, inside `run_gate`, exactly the 5 keywords, no positional, no splat, `extraction_ceiling_x` called, no `"extraction_ceiling"` subscript). Residual AR-27-06 | closed |
| T-27-11 | Spoofing | (27-04) wrong-weights rung adapters | mitigate | E2E step (f) (`:981-986`) PASSED: every rung adapter loads through `ckpt_mod.load_adapter` and its recorded `adapter_sha256` equals a bytes recompute | closed |
| T-27-12 | Tampering | (27-04) provenance drift | mitigate | `test_provenance_digests_match_live_bytes` (`:1171-1201`) PASSED: PRESENT branch set-equal to `PINNED_MODULES`, hashlib over live bytes, one message naming every drifted module; tmp-copy RED names both edited modules; real tree re-checks clean | closed |
| T-27-13 | Information disclosure | (27-04) tmp sidecars | accept | AR-27-08; e2e asserts `strays == ([], [])` and unchanged record bytes (`:994-995`) PASSED; post-run finds empty | closed |
| T-27-SC | Tampering | (27-04) package installs | accept | AR-27-10; `test_pyproject_is_byte_identical` PASSED | closed |
| T-27-01 | Tampering | (27-05) prereg edited after the record | mitigate | Ancestry guard PRESENT state PASSED: `git log -- scripts/phase27_prereg.py` → 1 commit `916ad4d`; record first-add `88dff77`; `git merge-base --is-ancestor 916ad4d 88dff77` → 0 and the SHAs differ; `git diff --stat 916ad4d..HEAD -- scripts/phase27_prereg.py` empty | closed |
| T-27-02 | Repudiation | (27-05) MOOT vs INCONCLUSIVE confusion | mitigate | The record reads MOOT with 7 generated reasons; the live gate on the sha-pinned frontier returns MOOT with reasons equal to the record's (`s1_record.py`), so Task 1's STOP branch had nothing to stop; `test_moot_reasons_are_generated_from_counts` PASSED (no reason equals a stored frontier reason). Residual AR-27-02 | closed |
| T-27-03 | Tampering | (27-05) frontier re-emitted / record hand-edited | mitigate | Frontier at 1 commit (`4030d0e`); record at 1 commit (`88dff77`), 0 commits touching `results/` since; record sha256 working tree = `HEAD` = `88dff77` = `065b2bc1…`; `test_the_record_re_derives_from_build_record` PASSED (PRESENT). Residual AR-27-03 | closed |
| T-27-04 | Denial (of evidence) | (27-05) legs silently proceeding on MOOT | mitigate | Re-watched on the committed record: 4/4 sub-modes exit 1, stdout 0 B, stderr `[phase27_relearn] results/phase27_admission.json reads 'MOOT' — REFUSING to run this leg: nothing is admitted (0 of 44 points PASS; …)`, sha256 `efd445c8…` ×4 = the eight Task-1 / Task-3 captures in `27-05-SUMMARY.md`; record sha unchanged; data finds empty before and after | closed |
| T-27-07 | Repudiation | (27-05) dirty-tree provenance | mitigate | The CLI path carries no stub: the only `refuse_if_dirty` replacement is the test suite's autouse fixture (`tests/test_phase27_relearn.py:109-116`). Corroborated after the fact: `provenance.git_sha == head_at_write == e308675`; 7/7 `module_sha256` equal the `e308675` blobs; the Task-1 transcript shows `git status --short -- scripts src results` empty before the one `admit` (`27-05-SUMMARY.md` Task 1) | closed |
| T-27-08 | Elevation | (27-05) machine git write of the record | mitigate | The record is touched by exactly one commit (`88dff77`, 1 file); every later commit (`611141a`, `1fa6f60`, `a1dec50`, `0ab0e53`, `b627997`) lists `.planning/` paths only (measured `git show --name-only`); the driver has no git write argv (27-03 row). Human action: the blocking `checkpoint:human-action` Task 2 and the operator's recorded answer (`27-05-SUMMARY.md:248`) — not provable from git metadata (Finding S-3) | closed |
| T-27-12 | Tampering | (27-05) provenance drift after commit | mitigate | `test_provenance_digests_match_live_bytes` PASSED on its PRESENT branch; `git diff --stat 916ad4d..HEAD -- scripts/teach_persona.py results/phase25_frontier.json pyproject.toml scripts/phase27_prereg.py scripts/mitigation_gate.py scripts/erasure_gate.py` empty; `git diff --stat HEAD` over the 7 pinned modules empty | closed |
| T-27-SC | Tampering | (27-05) package installs | accept | AR-27-10 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Open

None.

---

## Threat Flags (from SUMMARY `## Threat Flags`)

| Flag | Source | Maps to | Disposition |
|------|--------|---------|-------------|
| `write-surface` | `27-03-SUMMARY.md` — `tp.train(log_path=paths["csv"])` (`scripts/phase27_relearn.py:620`) → `results/{prefix}_{arm}/run.csv` (`scripts/teach_persona.py:377`) | T-27-13 (sidecar write surface) | Informational mapping; residual logged as AR-27-09 (27-REVIEW WR-03, ruling 1). Measured: `git check-ignore -v --no-index` lists `data/persona_relearn_attacker_n8_fresh_seed1337_train.bin` (`.gitignore:17`), `checkpoints/phase27_relearn_attacker_n8_fresh_seed1337_latest.pt` (`:14`) and `data/phase25_phase27_n8_x_rung0050_k16_draws.json` (`:17`) and does NOT list `results/phase27_relearn_attacker_n8_fresh_seed1337/run.csv` |

**Unregistered flags:** none.

---

## Findings

- **S-1 (WARNING, documentation).** Four of five SUMMARYs (`27-01`, `27-02`, `27-04`, `27-05`) carry
  no `## Threat Flags` section. Nothing is unmapped — 27-02's loader edit is T-27-10, 27-04's
  point-keyed sidecar names (`c054d8b`) extend the write surface 27-03 flagged, 27-05's record is the
  declared artifact — but the executor's "no new surface" attestation is absent for four of five
  plans (Phase-26 precedent S-1).
- **S-2 (INFO, measured, UNRULED — deliberately not in the Accepted Risks Log).** 27-REVIEW IN-03
  reproduces at the function level: a deep copy with 44 `point_keys` over 43 unique keys and 43
  points (total tally REFUSED 5, per-leg adv_n64 REFUSED 6) reads `MOOT` from
  `relearning_is_worth_attempting` ("0 of 44 points PASS; tallies {… 'REFUSED': 5}"). It cannot reach
  a reader: the gate's sole production caller `build_record` (`phase27_relearn.py:243`) refuses the
  same copy — `SystemExit: row verdicts {'FAIL': 32, 'INCONCLUSIVE': 6, 'REFUSED': 6} do not
  re-derive verdicts.tallies …` — and an absent frontier FILE raises `FileNotFoundError` inside
  `admit` with nothing written. The committed frontier has 44 unique keys, set-equal to its points and
  equal to `ORDERED_POINT_KEYS()`. T-27-02 stays closed (its plan sentence's triggers all fire, and no
  published reading can be MOOT from this input), but the 2026-09-16 ruling does not name IN-03, so
  this audit does not accept it: the developer should rule on it or add it to Phase 28's carry list.
- **S-3 (INFO, evidence limitation, T-27-08).** All 13 phase-27 commits examined (`916ad4d` …
  `b627997`, operator and machine alike) carry author `Rafael` and 0 `Co-Authored-By` / Claude
  trailers, so git metadata cannot distinguish the operator's `88dff77` from a machine commit. The
  human-action half of the 27-05 mitigation rests on the blocking checkpoint and the operator's
  recorded answer, not on git. The machine-checkable half is measured: one commit touches the record,
  the driver's git surface is read-only, and every later commit is `.planning/`-only.
- **S-4 (INFO, T-27-06 posture).** `load_checkpoint` deserialises with `weights_only=False`
  (`checkpoint.py:175`). The row names it as a sanctioned loader, and the driver feeds it only the
  arm's `checkpoints/…_latest.pt` that the same run wrote first: `train()` loads only on an explicit
  `resume_from` (`loop.py:728`), the first rung passes `resume_from=None`
  (`phase27_relearn.py:624`), and the end-of-call save is unconditional (`loop.py:973-988`). This
  matches CLAUDE.md's stack guidance (`torch.save` for the resume checkpoint; `weights_only` /
  safetensors for shipped weights). Adapters and the base cross `weights_only=True`.
- **S-5 (INFO, not classified).** IN-01 (the cleared-count `_prove` in `build_record` compares
  `cleared_abc` with itself; the tally `_prove` beside it is live — T-27-01 27-03 row), IN-02,
  IN-04, IN-05 (the driver's recorder copies `ix` via `astype`), IN-06 (relative `--out`; fails
  toward over-refusal; hypothesis), IN-07 (this audit's runs left `git status` clean) and IN-08 do
  not falsify any register row's plan sentence and are not classified here.

---

## Accepted Risks Log

The eight residual rows (AR-27-01 … AR-27-07, AR-27-09) are the findings the developer ruled on
2026-09-16: carried to Phase 28's named-limitation list, the operator-committed record NOT re-issued,
and obligation (a)–(f) binding on the first phase that reads ADMITTED, before its first leg, in a
continuation driver / pre-registration continuation — never an edit of `scripts/phase27_prereg.py`
(ancestry guard) or of the seven modules `provenance.module_sha256` pins. All are latent today: the
committed record reads MOOT and every leg refuses (T-27-04, 27-05 row).

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-27-01 | T-27-01 | **CR-01.** The runtime D-18 bin pin checks the bin only when the rows sha matches its pin (`scripts/phase27_relearn.py:573-581`); a row-level corpus drift trains on an unpinned corpus, recorded only as `corpus_pin_checked: false` (`:686`), which `run_structural_proof` never reads. The pre-registration holds: both pins committed at `916ad4d`, and `test_attacker_corpus_sha_re_renders` PASSED. Obligation (a) | developer — ruling 1 (`27-HUMAN-UAT.md` test 1; `phase28-carry-phase27-latent-review-findings.md`) | 2026-09-16 |
| AR-27-02 | T-27-02 | **WR-01** (ruled inconsequential). `admit` cannot write an INCONCLUSIVE record: the `build_record` `_prove`s (`:264-287`) exit on inputs the gate reads INCONCLUSIVE. Conservative direction — no record means every leg refuses as "absent", never a false MOOT or ADMITTED | developer — ruling 1 | 2026-09-16 |
| AR-27-03 | T-27-03 / T-27-09 / T-27-11 | **CR-02.** `_require_admitted` enforces "tracked" (`git ls-files`, `:160-172`), not "committed bytes"; an out-of-tree `--record` skips the git conjunct; legs trust `blob["admitted_point_keys"]` (`:878`, `:961`, `:1138`) and read adapter pins, X and thresholds from the live frontier without comparing `frontier_sha256` (only at `:311`, inside `build_record`). Sanctioned path holds: default `--record` → 4/4 refusals; the suite reddens an edited record or a re-emitted frontier. Obligation (b) | developer — ruling 1 | 2026-09-16 |
| AR-27-04 | T-27-04 | **WR-02.** `run_structural_proof` requires only ≥ 2 arms plus `fresh_seed{designated}` (`:1081-1093`), not every admitted point's mitigated reading, and records data-order proof (iii) as a boolean (`:1118-1135`) instead of refusing. Recording (iii) was planned (27-03 Task 3 item 9); the missing coverage check was not. Obligation (c) | developer — ruling 1 | 2026-09-16 |
| AR-27-05 | T-27-04 | **WR-04** (ruled inconsequential). `train(on_draw=…)` forwards only at the masked teaching draw and the replay draw (`loop.py:661`, `:706`); unmasked / fact-aligned branches record nothing. The driver always passes `train_mask_bin` and never `fact_bin` (`phase27_relearn.py:607-628`), and the e2e proves `draws == rungs × (1 + replay)` on its branch | developer — ruling 1 | 2026-09-16 |
| AR-27-06 | T-27-05 | **WR-06.** `baseline` is validated and quoted but never moves the verdict (`phase27_prereg.py:575-615`); `run_gate` overwrites `phase27_{leg}_gate.json` on a re-run (`phase27_relearn.py:1053`). The verdict cannot move; the published label can. Obligation (e) | developer — ruling 1 | 2026-09-16 |
| AR-27-07 | T-27-05 / T-27-09 | **WR-05.** The Z threshold and control read the DP control for every point (`phase27_prereg.py:477` `control_readings["dp_<leg>"]`; `phase27_relearn.py:824` `control_{leg}`); the frontier judged `adv_*` points against their own control, and no adversarial control adapter is pinned. Latent, measured: 0 of 12 `adv_*` points admissible (INCONCLUSIVE 6, REFUSED 6). Ruling 2: no `adv_*` point is admissible until the v5.0 adversarial re-measurement pins the arm's own control; DP-control calibration of adversarial points is NOT accepted; the in-code refusal is obligation (f) | developer — ruling 2 (`27-HUMAN-UAT.md` test 2) | 2026-09-16 |
| AR-27-08 | T-27-13 | Plan-time accept (27-03, 27-04): sidecars carry only the synthetic persona facts already published in the frontier; `data/` and `checkpoints/` are gitignored (`.gitignore:17`, `:14`; `git check-ignore` measured); the e2e's sidecars live in tmp trees (`strays == ([], [])` PASSED) | plan-time disposition (27-03 / 27-04 PLAN); logged by `/gsd:secure-phase 27` | 2026-09-16 |
| AR-27-09 | T-27-13 | **WR-03 / 27-03 threat flag `write-surface`.** A live leg's `tp.train(log_path=paths["csv"])` (`phase27_relearn.py:620`) writes `results/phase27_relearn_attacker_{leg}_{label}_seed{S}/run.csv` (`teach_persona.py:377`) — not gitignored (measured) and matching `ARTIFACT_GLOB`. Its columns are `step, train_loss, val_loss, lr, tokens, wall_clock` (`loop.py:904-917`; the driver passes no `extra_eval_fns`), so the exposure is evidence-guard and porcelain noise, not disclosure. Latent: no live leg has run (finds empty). Obligation (d) | developer — ruling 1 | 2026-09-16 |
| AR-27-10 | T-27-SC | Plan-time accept (all five plans; D-39): no package installed in the phase — `git log a655198^..HEAD -- pyproject.toml requirements.txt Makefile .github/workflows/ci.yml` → 0 commits; newest `pyproject.toml` commit `5065bc5` (2026-09-01) predates `COMMITTED = "2026-09-16"`; `test_pyproject_is_byte_identical` PASSED | plan-time disposition (27-01 … 27-05 PLAN); logged by `/gsd:secure-phase 27` | 2026-09-16 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total (rows / ids) | Closed | Open | Accepted | Run By |
|------------|----------------------------|--------|------|----------|--------|
| 2026-09-16 | 35 / 14 | 35 | 0 | 10 rows (8 ruled residuals, 2 plan-time) | `/gsd:secure-phase 27` — gsd-security-auditor, State B (create) from plan-time register, HEAD `b627997` |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-16
