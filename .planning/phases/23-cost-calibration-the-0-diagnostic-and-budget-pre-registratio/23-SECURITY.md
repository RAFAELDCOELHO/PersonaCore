---
phase: 23
slug: cost-calibration-the-0-diagnostic-and-budget-pre-registratio
status: verified
threats_open: 0
threats_total_rows: 164
threats_distinct_ids: 113
asvs_level: 1
created: 2026-08-29
audited_at_head: 522f8a5c91f99537b630c06b5690373e7ca18fc7
---

# Phase 23 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (`register_authored_at_plan_time: true`). This document
> **verifies** the declared mitigations exist in implemented code. It does **not** scan for
> new threats.

**Gate status: CLOSED.** `threats_open: 0`. 164 register rows across 20 plans, **113 distinct
threat IDs**, every row resolved to `closed` or to a logged accepted risk. `### Open` reads
`None.` Five findings (S-1 … S-5) are recorded below; none is a BLOCKER under `block_on: high`,
and the two that name a residual are logged as accepted-risk rows so they cannot resurface
unclassified.

---

## Boundary of this audit — read this first

What was done:

- All 20 `<threat_model>` blocks extracted from `23-01-PLAN.md` … `23-20-PLAN.md` — **164 rows**,
  **113 distinct IDs**. This reconciles exactly with the orchestrator's independent parse.
- Every row keyed on the **(threat_id, component) pair**, never on the id alone. 25 IDs collide
  across plans; the collisions are named below and nothing is renumbered.
- Every `mitigate` row traced to a named symbol, constant, assertion or committed record field
  **at HEAD `522f8a5`**. 50 backticked symbols were cross-checked against an AST index of every
  `FunctionDef` in `scripts/`, `tests/` and `src/`: **49 resolved to a definition**, and the one
  that did not (`prior_scored_seeds_at_start`) resolved to a local binding plus a `_prove` plus a
  recorded record field, verified individually.
- **AST, not grep, wherever the searched term also occurs in prose.** This repository has produced
  false-GREEN and false-RED greps repeatedly. Measured here: `CURVE_K = 16` occurs **twice** as
  text in `scripts/mitigation_budget.py` (once as the assignment, once inside a provenance string),
  and `ckpt["step"]` occurs once — **inside a docstring explaining why it must not be used**. Both
  were resolved by `ast` walk.
- **Every published number re-derived by this audit, not quoted.** All eight `ratios.*` entries,
  the `wall_clock_gap_vs_superseded`, both noise floors, and all four `source_record_sha256`
  digests were recomputed here under exact `==` / byte comparison.
- Targeted suite executed in this audit: `.venv/bin/python -m pytest -q tests/test_phase23_*.py`
  → **`232 passed in 137.46s`**, exit 0, **zero skips**. `.venv/bin/python -m ruff check .` →
  `All checks passed!`, exit 0.
- The five D-04 gate conjuncts were **re-executed independently by this audit** against real git,
  not read out of the driver.

What was **not** done, and is therefore not evidence here:

- **The full suite was not re-run.** The stated baseline (1591 passed / 1 skipped) is inherited
  from the task brief, not measured by this audit. The Phase-23 subset was measured.
- **No independent vulnerability scan.** Per `register_origin` the register is treated as
  complete; attack surface outside these 164 rows was not sought.
- **Deliberate-RED observations taken during execution were not re-applied.** Where a plan's
  evidence is a transient working-tree mutation, this audit verified the *permanent mechanism*.
  Where the watched-RED case is a **committed, permanently-executing** assertion — as in
  `test_every_noised_sweep_point_is_under_the_noised_glob`, whose two escape routes are driven
  and asserted inside the test body on every suite run — that is counted as re-run, because it
  ran in this audit's `232 passed`.
- **The working tree is NOT clean.** `.gitignore` carries one uncommitted hunk, unrelated to
  Phase 23 and touching no guarded path. Flagged rather than assumed benign.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| a frozen rule ↔ the numbers it judges | The phase's central integrity property: a verdict rule committed before the data existed, never edited to change its own answer. | `scripts/phase23_prereg.py` (`c7de5d4`), `phase23_matched_prereg.py` (`c100388`), `phase23_resume_prereg.py` (`e70a035`) |
| resource budget ↔ outcome gate | CAL-02. A reader who can mistake a resource calibration for an outcome-threshold peek makes the pre-registration meaningless. | Import graph: `mitigation_gate` must never import `mitigation_budget` |
| σ=0 diagnostic ↔ the first noised point | D-04 commits to zero noised points on a breach. That commitment is real only if the ordering is checkable in git. | earliest-add SHAs of `results/phase23_sigma_zero.json` and `results/phase23_noised_*` |
| a measurement verdict ↔ a human release | `results/phase23_matched_verdict.json`'s own `governs` forbids reading itself as an unblock. Release is verdict **AND** a committed human act. | verdict string + commit `746ecf6` |
| a routine agent commit ↔ the human unblock act | Sentinel + ancestry + `git show HEAD:` is satisfiable by ANY commit touching `.planning/STATE.md`, and agent commits to that file are routine in this phase. | pinned 40-char SHA + act-shape check |
| a record's NAME ↔ a record's CONTENT | Every ordering guard binds on a path glob. A record declaring a sweep point but named outside the glob is invisible to all of them. | `sigma`, `sweep_point` keys |
| the floor ↔ the mean | Sizing Z against the floor is unrescuable in the direction that matters, because the K ratchet is one-way. | `h_per_point_floor` / `_ceiling`; `FORBIDDEN_MEAN_KEYS` |
| the OLD control protocol ↔ the protocol-matched comparator | The old control was proven invalid as a comparator by three protocol differences, none about noise. A gate read against it is a verdict about the wrong quantity. | `control_taught_recall`, `control_heldout_recall`, `control_gap` |
| a published figure ↔ its denominator and provenance | Privacy claims are the product. A number without its denominator is a security-class defect here, not a style nit. | 11 pre-registered scalar leaves in `results/phase23_cost.json` |
| a false claim ↔ its correction | A pre-registration or a published traceability row may be corrected only by a dated continuation beside it, never by an edit over it. | sentinel-delimited spans in `.planning/{REQUIREMENTS,ROADMAP,STATE}.md` |
| a coded mechanism ↔ an operator discipline | A procedure typed at a shell prevents nothing on the next run. Disciplines must be recorded as disciplines. | detached-launch recipe; `data/` full-delete residual |
| gitignored inputs ↔ the audit trail | `data/` and `checkpoints/` are gitignored, so the one-attempt rule binds across commits only. | `data/phase23_run_state.json` |

---

## ID collisions — PRE-EXISTING at HEAD, recorded not renumbered

25 IDs are overloaded across the 164 rows. This was introduced during planning, is present at
HEAD, and is **not** an execution defect. Nothing is renumbered — naming the collisions is the
deliverable, and it is why every row below is keyed on **(id, component)**.

| ID | Plans | Verdict |
|----|-------|---------|
| `T-23-SC` | all 20 | **1 threat, cross-referenced 20x.** Supply chain, identical component every time. Legitimate. |
| `T-23-60`, `T-23-61`, `T-23-62`, `T-23-63` | 23-11, 23-15 | **2 DISTINCT threats each.** 23-11's are cost-record figures; 23-15's are the matched comparator's protocol, ledger, one-attempt rule and σ=0 visibility. |
| `T-23-64`, `T-23-64b`, `T-23-65`, `T-23-66`, `T-23-67` | 23-12, 23-16 | **2 DISTINCT threats each.** 23-12's are the retract-in-place guards; 23-16's are the matched control call, corpus and clip shadow. |
| `T-23-68`, `T-23-68b` | 23-12, 23-17 | **2 DISTINCT threats each.** |
| `T-23-69` | 23-13, 23-17 | **2 DISTINCT threats.** |
| `T-23-70`, `T-23-71`, `T-23-72`, `T-23-73`, `T-23-74`, `T-23-75`, `T-23-76`, `T-23-77` | 23-13/14, 23-17/18/19, 23-20 | **3 DISTINCT threats each.** The widest overloading in the phase. |
| `T-23-78`, `T-23-79`, `T-23-80` | 23-14, 23-19 | **2 DISTINCT threats each.** |
| `T-23-81` | 23-03, 23-14 | **2 DISTINCT threats.** (03) a σ>0 point named outside the glob; (14) CTRL-03 left unticked. |

**Consequence, stated so a later reader does not mis-count:** the published total is **164 rows**
and **113 distinct IDs**. Neither number is derivable from the other, and a "closed 113/113" claim
would silently under-count 51 rows. Both are carried in the frontmatter.

---

## Threat Register

**164 rows. 164 closed, 0 open.** 142 `mitigate` · 16 `accept` · 6 `accept + disclose`.

*(The orchestrator's parse reported 125 mitigate / 16 accept / 5 accept+disclose / 2 retroactive /
"a handful of free-text rows". This audit's normalization differs and is stated rather than
reconciled silently: the 2 rows marked `**mitigate (retroactive, from the commit) + disclose**`
and the 1 marked `mitigate (in 23-17)` are counted under `mitigate`, and the 6th `accept +
disclose` row is `T-23-63` at 23-15. Row and distinct-ID totals agree exactly.)*

### Open

**None.**

### Closed — grouped by plan, with the verification that closed each group

Full mitigation text lives in each `23-NN-PLAN.md` `<threat_model>` block. What follows is the
**evidence this audit found itself**, not a transcription of intent.

| Plan | Threat IDs | Verified at | Status |
|------|-----------|-------------|--------|
| 23-01 | T-23-01, -02, -03, -04, -05, -SC | venue ledger `23-06-SUMMARY.md:127` records `tests 90 failures 0 errors 0 skipped 0`, asserted by `tests/test_phase23_mps_venue.py:452` (`skipped == 0`, `failures == 0`, `errors == 0`, `tests > 0`, exactly one such line); `_VENUE_SUMMARY_PATH` resolved and **exists**, so the assertion is live not skipped. `test_cpu_written_dp_noise_rng_is_refused_on_mps` at `tests/test_phase22_checkpoint.py:581`. Exemption count asserted at `:385` by regex `\b53 of (?:the )?\d+\b` — see S-3 | closed |
| 23-02 | T-23-06, -07, -08, -09, -10, -SC | Out-of-process probe at `tests/test_phase23_budget.py:145-173` spawns a fresh interpreter, `exec_module`s the real gate and asserts no `_FORBIDDEN` name reached `sys.modules`; the **sentinel meta-guard** (T-23-07) is at `:134-136`. AST-verified independently by this audit: `mitigation_gate.py` imports exactly `{erasure_gate, pathlib, sys}` — `mitigation_budget` **absent**. `git status --short scripts/` **EMPTY**; `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py` → **0** | closed |
| 23-03 | T-23-11, -12, -13, -14, -15, -16, -81, -82, -84, -SC | `scripts/phase23_prereg.py` has **exactly one commit** (`c7de5d4`) and `git diff --exit-code c7de5d4` → **0** — byte-identical, as required. `sigma_zero_verdict` (`:207-300`) has **no warning branch and no override parameter**: the only outcomes are `"proceed"` and `SystemExit`, with three `_prove`s ahead of the comparison (provenance keys, `floor == noise_floor(readings)` under exact `==`, `math.isfinite`). `test_sigma_zero_precedes_every_noised_point:447`; `test_no_phase23_artifact_sits_outside_the_prefix:553`; `bool(checked) == bool(tracked)` non-vacuity at `:396` and `:640` | closed |
| 23-03 (content-side) | T-23-81, T-23-84 | `test_every_noised_sweep_point_is_under_the_noised_glob` (`tests/test_phase23_prereg.py:614-666`). Both escape routes are **watched RED inside the committed test body** — the FILENAME escape and the OMITTED-key escape — plus two one-sided controls proving neither refusal is blanket. These ran in this audit's `232 passed` | closed |
| 23-04 | T-23-17, -18, -19, -20, -21, -22, -SC | `n64_leg_is_committable` takes **no tolerance parameter**; `grep -cE 'rel_tol\|isclose\|approx'` on `tests/test_phase23_cal03.py` → **0**. T-23-19 verified by **AST**: zero executable `ckpt[...]` subscripts in `scripts/phase23_run.py`, T sourced from `_count_composed_steps` (`:843`) and recorded as `"t_source"` at `:1007` / `:3160` — see S-1. `results/phase23_cal03_wiring.json` carries `sweep_point: false`, `exports_adapter: false` | closed |
| 23-05 | T-23-23, -24, -25, -26, -27, -SC | `scripts/phase23_cost.py`: `TRAINING_RECORD_KEYS` (18 keys incl. `warmup_iterations_discarded`, `timed_iterations`), `GENERATION_RECORD_KEYS` (18 keys incl. both `stop_terminated_n_*`, `draws_per_point`, `questions`, `n_draws_measured`), `FORBIDDEN_MEAN_KEYS` (4) refused **at any nesting depth** by `_walk_items`, floor≤ceiling refused in `validate_record`. `torch.mps.synchronize()` at BOTH bracket boundaries, `scripts/phase23_run.py:496` and `:500` | closed |
| 23-06 | T-23-28, -29, -30, -31, -32, -SC | `git diff --exit-code -- src/personacore/privacy/dpsgd.py` → **0**. `test_the_ledger_states_a_skip_count_of_zero` live (see 23-01). `rng["mps"]` literal present ×2 in `tests/test_phase22_fakes.py` | closed |
| 23-07 | T-23-33, -34, -35, -36, -37, -38, -SC | `scripts/teach_persona.py`: resume branch at `:1417-1432` moves the three bin/csv/checkpoint targets to `expected=` (refused if **ABSENT**) while the adapter stays refused-if-present; **cross-arm** refusal at `:1425-1432` (`resolved != paths["checkpoint"]` → `SystemExit`); `_refuse_cross_device_resume` at `:1237-1291` raises naming **arm, file, recorded device and resolved device** by measured generator-state byte width. `resume_from=None` sentinel at `:954` / `:1304`. `test_the_resume_aware_branch_is_watched_red` at `tests/test_phase23_resume.py:349` | closed |
| 23-08 | T-23-39, -40, -41, -42, -43, -44, -45, -83, -SC | `choose_n_seeds` **imported** from the edit-once pin (`scripts/phase23_run.py:115`); `grep -c "def choose_n_seeds" scripts/phase23_run.py` → **0**. `rebuild_arm_bins_verifying_sha256` at `:281` and `prove_bins_match` at `:232`. Seed count **5 distinct** vs the **imported** `mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS` (`:1578`, `:1655`) — never a retyped `2`. `results/phase23_control_floor.json` carries a non-empty `residual_differences` | closed |
| 23-09 | T-23-46, -47, -48, -49, -50, -SC | **AST-verified by this audit:** `scripts/mitigation_budget.py` has **0** `Import`/`ImportFrom` nodes and a module body of exactly `{Expr: 1, Assign: 16}` — no `FunctionDef`, `If`, `For` or `Import` node exists. All 16 assigned values pass `ast.literal_eval`. `test_the_budget_module_is_protected_but_not_frozen` at `tests/test_phase23_budget.py:726` | closed |
| 23-10 | T-23-51, -52, -53, -54, -55, -56, -SC | **Re-derived by this audit:** `results/phase23_sigma_zero.json`'s `floor` = `0.05357142857142849` is **exactly** `mitigation_budget.CONTROL_NOISE_FLOOR` (bit-identical). `clip_bind_count == 0` recorded. `verdict == "HALT"` stored and re-derived every suite run by `test_the_sigma_zero_verdict_re_derives:709`. Ancestry re-derived here: `c7de5d4` ≺ `2d06989` (σ=0) ≺ `ab9d246` (noised), all `git merge-base --is-ancestor` exit **0** | closed |
| 23-11 | T-23-57, -57b, -57c, -57d, -58, -58b, -58c, -59, -60, -61, -62, -63, -63b, -SC | **The D-04 gate, re-executed by this audit against real git.** `prove_d04_gate` at `scripts/phase23_run.py:2923` is called in **all three** run sub-modes (`noised:3197`, `throughput:3584`, `never_taught:4940`). All five conjuncts of `unblock_act_is_committed` independently re-verified — see the table below. 11 published figure paths **all resolve to scalar leaves**; the gap `2.035849685343305` **re-derives under exact `==`** from the two `training_seconds_mean` fields; every timing block names its `protocol` and the superseded protocol is recorded beside, never deleted | closed |
| 23-12 | T-23-64, -64b, -64c, -65, -65b, -66, -66b, -66c, -67, -68, -68b, -SC | Sentinel-delimited continuation spans present and correctly ordered in **all three** files: `.planning/REQUIREMENTS.md:186/271`, `.planning/STATE.md:951/969`, `.planning/ROADMAP.md:51/71`. `_required_figures_missing` (`tests/test_phase23_cost.py:745`) and `_long_figures_not_sourced` (`:759`) run over the sentinel slice only (`:732-742`, both sentinels asserted present and BEGIN-before-END). `projection_not_published` is a required record field naming the projection and stating it appears in NO numeric field | closed |
| 23-13 | T-23-69, -69b, -70, -71, -72, -73, -73b, -73c, -74, -74b, -74c, -SC | **W9 discipline verified exactly as declared:** `sized_against = "h_per_point_ceiling"` is present on the three ceiling-side multiplicands (`SWEEP_POINTS`, `CURVE_K`, `N_CONTROL_SEEDS`) and **ABSENT** on the three constants no throughput figure feeds (`FULL_FIDELITY_K`, `STEP_BUDGET`, `N64_LEG_WITHDRAWN`) — a universal requirement would have written a false provenance field. `ratchet_k` (`scripts/mitigation_gate.py:917-961`) is one-way (`proposed_k >= fixed_k`) with **no override parameter** and both values constrained to `K_RUNGS`. `test_selected_k_is_a_ratcheted_rung:1211`, `test_z_was_sized_against_the_ceiling:1291` | closed |
| 23-14 | T-23-75, -76, -77, -78, -79, -79b, -80, -80b, -81, -SC | `git diff --exit-code -- scripts/phase18_extraction.py` → **0** (predicate imported read-only from an ancestry-guarded, byte-unchanged file). **X is not published:** this audit walked **every key at every depth** of the 1.1 MB `results/phase23_never_taught.json` — zero `X` / `extraction_ceiling` / `x_ceiling` keys. Denominator present and question-denominated: `questions=416`, `draws_per_question=16`, `total_draws=6656`. `pooled.pooling_rule` is a **named required field** stating the designated-seed choice explicitly | closed |
| 23-15 | T-23-60, -61, -62, -62b, -62c, -62d, -63, -SC | `scripts/phase23_matched_prereg.py` has **exactly one commit** (`c100388`), first-added while `results/phase23_matched_*` was untracked. Three AST censuses present: `prove_branch_ledger_complete:295`, `prove_dp_wiring_keys:402`, `prove_train_call_keys:462`. `prove_first_attempt:616` takes the caller's `git ls-files` result as an argument and has **no override parameter**. T-23-62c and T-23-63 are `accept + disclose` → **AR-23-02**, **AR-23-03**; T-23-62d is disclosed at its true strength → **AR-23-07** | closed |
| 23-16 | T-23-64, -64b, -65, -66, -67, -67b, -SC | The `clip_grad_norm_` shadow is installed at `scripts/phase23_run.py:1250` and **restored in `finally`** at `:1254`. Pre-clip norms captured and published as `grad_clip_calls` / `grad_clip_max_pre_clip_norm` / `grad_clip_min_pre_clip_norm` (`:1450-1452`), asserted `== MAX_STEPS` and `< MATCHED_GRAD_CLIP` at `:2300-2305` **before** scoring. T-23-67b is `accept + disclose` → **AR-23-04** | closed |
| 23-17 | T-23-68, -68b, -68c, -69, -70, -71, -71b, -71c, -SC | `prior_scored_seeds_at_start` — the one cited symbol with no `FunctionDef` — resolved: local binding at `scripts/phase23_run.py:2176`, refusal `_prove` at `:2219-2223`, **required record field** at `:2368`, asserted by `tests/test_phase23_matched.py:514` (branch-correct: the record declares `attempt: "continuation"`). `noise_floor` is **CALLED** at `:1763`, never inlined. T-23-71b / -71c → **AR-23-03**, **AR-23-04**; T-23-68c → **AR-23-07** | closed |
| 23-18 | T-23-72, -72b, -73, -74, -75, -SC | **Re-derived by this audit:** `phase23_prereg.noise_floor` on the matched record's own five `readings` returns `0.0267857142857143`, **bit-identical** to `mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR`. `MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE` carries 11 keys including `record_file_sha256` and `sigma_zero_was_visible`. `test_a_hand_edited_floor_is_detected:828` plus its own uniqueness guard `test_the_original_needle_is_still_unique:1160`. Zero-import AST assertion re-run here (0 nodes) | closed |
| 23-19 | T-23-76, -77, -77b, -78, -79, -80, -SC | **Re-verified by this audit:** `results/phase23_matched_verdict.json` records `verdict: "proceed"`, `deviation: 0.0`, `deviation_over_floor: 0.0`, `floor` **bit-identical** to `MATCHED_CONTROL_NOISE_FLOOR`, `sigma_zero_was_re_run: false`, `sigma_zero_was_visible: true`. Its cited `sigma_zero_record_file_sha256` **matches the live file's recomputed sha256**. T-23-77b verified by AST: `matched_verdict()`'s only numeric literals are `{0, 2}` — no retyped `1008` or `648`. T-23-78 → **AR-23-03** | closed |
| 23-20 | T-23-70, -71, -72, -73, -74, -75, -76, -77, -SC | `scripts/phase23_resume_prereg.py` has **exactly one commit** (`e70a035`); `prove_killed_run_continuation` present with `committed_scored_seeds` sourced from git (`:160`, `:177`). All three run logs are **tracked** and none matches `NOISED_RECORD_GLOB` (verified by `fnmatch` against the imported glob). T-23-76 and T-23-77 are `accept` → **AR-23-06**, **AR-23-05**. T-23-75's procedural half → **S-2 / AR-23-08** | closed |

### The D-04 gate — five conjuncts, re-executed by this audit

`prove_d04_gate` is the release condition in front of every noised run. Sentinel + ancestry +
`git show HEAD:` alone is **forgeable** — any commit introducing the phrase into
`.planning/STATE.md` satisfies all three, and agent commits to that exact file are routine in this
phase. The SHA pin and the act-shape check are what bind the act to a human. All five were
re-run here against real git rather than read out of the driver:

| # | Conjunct | Re-executed result |
|---|----------|--------------------|
| 1 | **PROVENANCE** — pinned 40-char SHA | `746ecf699904e7c97bf73614e1c617a646da30ad`, author **`Rafael <rafael.d.cooelho@gmail.com>`** — the repository's own git user, not an agent identity |
| 2 | **PRESENCE** — sentinel membership | `git log -S"UNBLOCKED 2026-08-28 — by the user…" -- .planning/STATE.md` returns a set of size **1**, and the pinned SHA is its sole member. Membership, never a positional read |
| 3 | **ANCESTRY** | `git merge-base --is-ancestor 746ecf6 HEAD` → exit **0** |
| 4 | **COMMITTED STATE** | the sentinel is present in `git show HEAD:.planning/STATE.md` (count 1) — not merely in the working tree |
| 5 | **ACT SHAPE** | the commit touched **4 paths, all planning documents**; paths under `scripts/` or `src/` = **0** |

Plus two record-integrity conjuncts, also re-verified: the verdict record's cited
`sigma_zero_record_file_sha256` equals the live file's recomputed digest, and `git ls-files`
returns both gate records as tracked.

### Numbers re-derived by this audit, not quoted

No figure below was copied from a SUMMARY. Each was recomputed here under exact `==` or byte
comparison. Full stored precision throughout — a rounding is not a figure.

| Quantity | Rule | Re-derived | Match |
|---|---|---|---|
| `training.non_dp.wall_clock_gap_vs_superseded` | `161.12400419991462 / 79.14336965046823` | `2.035849685343305` | exact `==` |
| all 8 `ratios.*.eval_over_training_{ceiling,floor}` | `h_per_point_{end} * 3600 / seconds_total` | 8 of 8 | exact `==` |
| `CONTROL_NOISE_FLOOR` vs σ=0 record `floor` | pinned literal vs stored field | `0.05357142857142849` | bit-identical |
| `MATCHED_CONTROL_NOISE_FLOOR` | `phase23_prereg.noise_floor(readings)` on the record's own 5 readings | `0.0267857142857143` | bit-identical |
| verdict record `floor` | vs `MATCHED_CONTROL_NOISE_FLOOR` | `0.0267857142857143` | bit-identical |
| 4 × `source_record_sha256` in `phase23_cost.json` | `sha256` of each file on disk | 4 of 4 | MATCH |
| verdict's `sigma_zero_record_file_sha256` | `sha256(results/phase23_sigma_zero.json)` | `dd34e513…e85d36` | MATCH |
| never-taught denominator | `questions=416`, `draws_per_question=16` | `total_draws = 6656` | consistent |
| distinct never-taught seeds | vs **imported** `EXTRACTION_FLOOR_MIN_SEEDS = 2` | 5 ≥ 2 | satisfied |
| `mitigation_budget` module shape | `ast` walk | 0 imports, 16 literal `Assign`, 0 other node kinds | as declared |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Findings

Five findings. **None is a BLOCKER** under `block_on: high`. Two name a live residual and are
logged as accepted-risk rows so they cannot resurface unclassified — the same treatment Phase 21
gave WR-05 and WR-07.

**S-1 — INFO — a declared `grep -c` criterion is FALSE at HEAD; the mitigation is not.**
T-23-19 (23-04) declares `grep -c 'ckpt["step"]'` **asserted 0**. Measured at HEAD it returns
**1**. The single occurrence is at `scripts/phase23_run.py:802`, **inside `_count_composed_steps`'s
docstring**, in the sentence explaining why the field must not be used. AST resolution: **zero**
executable `ckpt[...]` subscripts anywhere in the module; T is sourced from
`_count_composed_steps` at `:843` and recorded as `"t_source": "_count_composed_steps"` at `:1007`
and `:3160`. The mitigation holds; the *criterion* is stale. This is precisely this repository's
own recorded `grep criteria measure prose` lesson, reproduced a further time — the criterion
should be an AST gate. Recorded, not patched: implementation files are read-only to this audit.

**S-2 — WARNING — a `mitigate` disposition whose procedural half exists in no committed file.**
Three rows — T-23-63b (23-11), T-23-80b (23-14) and T-23-75 (23-20) — declare a detached-launch
mitigation: `os.setsid()` inside the launched interpreter, `os.execv`, an `os.getsid(pid)` probe
asserting `pid == pgid == sid` before any GPU second, and `caffeinate -is -w <pid>`. **Measured:
`grep -rn "os\.setsid\|os\.execv\|os\.getsid\|caffeinate" scripts/ tests/ src/` returns ZERO
matches.** It is an operator shell recipe recorded in `23-20-SUMMARY.md:218-224`, not a mechanism
in the repository — nothing prevents the next long run being launched in the foreground.

What *is* coded, and what keeps this off the blocker list: (a) the **recovery** half is fully
implemented and was exercised for real — `prove_killed_run_continuation` with
`committed_scored_seeds` read from `git show HEAD:` (`scripts/phase23_resume_prereg.py:160,177`),
and 23-17's run was genuinely harness-killed at 3 of 5 seeds and admitted through that path;
(b) **evidence of execution is committed**: all three run logs carry `SESSION pid=N pgid=N sid=N`
as their **first line** (`55784`, `57006`, `23851`), all three are tracked, and none matches
`NOISED_RECORD_GLOB` (verified by `fnmatch` against the imported constant). The harm class is
Denial of Service — a lost training run, not a privacy leak. Logged as **AR-23-08** with the
disposition corrected from `mitigate` to a stated discipline.

**S-3 — INFO — a pinned numerator with an unpinned denominator.**
T-23-04 (23-01) requires the AST-probe exemption to be written "with its measured count (53 of
113)". The assertion at `tests/test_phase23_mps_venue.py:385` is
`re.search(r"\b53 of (?:the )?\d+\b", text)` — it pins the **numerator** `53` but accepts **any**
denominator. A drift in the 113 total would be invisible to it. The text is present and correct
in `23-06-SUMMARY.md` today (measured). Bounded and non-blocking, but the guard is narrower than
the claim it stands for.

**S-4 — INFO — the venue-pass evidence is a hand-written planning file.**
T-23-01 / T-23-30's skip-count-zero guard parses `tests 90 failures 0 errors 0 skipped 0` from
`23-06-SUMMARY.md:127` — a Markdown document, not a junit XML artifact. The assertion is live
(the path resolves and the file exists, so it is not a silent skip) and it does assert
`skipped == 0 and failures == 0 and errors == 0 and tests > 0` on exactly one such line. What it
cannot do is verify the run happened; a hand-edited line would satisfy it. Recorded as a
known bound on the M3-venue claim, not as a defect.

**S-5 — INFO — two emptiness assertions are now historical, and the phase has already said so.**
T-23-53 (23-10) and T-23-76 (23-20) both rest on `git ls-files 'results/phase23_noised_*'`
returning **0**. At HEAD it returns **1**: `results/phase23_noised_dp_n64_sigma0p500000.json`,
first added `ab9d246` (2026-08-28). Both assertions were true when their plans ran; the point
landed later at 23-11, **after** the D-04 gate opened, and the ancestry is correct (σ=0 `2d06989`
≺ verdict `0a275c9` ≺ noised `ab9d246`, all verified here). This audit raises it only to confirm
that the record already handles it honestly: the DPSGD-06 traceability row in
`.planning/REQUIREMENTS.md:455` was **retracted in place** on 2026-08-29 inside a dated
`23-UAT1-CONTINUATION-BEGIN` / `-END` span, with the false text left standing above it, and the
retraction names this exact measurement (`returns 1`, and the file). No gap.

---

## Accepted Risks Log

The 22 `accept` and `accept + disclose` rows, plus the one residual this audit raises.

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| AR-23-01 | T-23-SC (all 20 plans) | Supply chain. **Zero installs across the entire phase** — verified: `pyproject.toml`'s last commit is `6a46441` (2026-07-31), predating Phase 23 entirely, and `tests/test_package.py` (3 passed) pins it by sha256. Two plans strengthen this structurally rather than by promise: `scripts/mitigation_budget.py` has **0** import statements at all (AST), and the `{pathlib, sys, erasure_gate}` import ceiling on the `mitigation_*.py` glob has zero headroom. Residual accepted: the pin covers the *declaration*, not the resolved wheel set. | Plan-time disposition, verified in implementation | 2026-08-29 |
| AR-23-02 | T-23-62c (23-15) | A **renamed** second comparator (`results/phase23_rematch_*`) is not refused by `prove_first_attempt` — one glob is watched, not the space of names. Accepted because the edit-once property raises its cost to "arrive with a NEW pre-registration", which is **VISIBLE, not REFUSED**, and the refusal message says which of the two cases it is. Recorded as clause (4) of `one_attempt_scope` in the artifact itself. | Plan-time disposition (23-15) | 2026-08-29 |
| AR-23-03 | T-23-63 (23-15), T-23-71b (23-17), T-23-78 (23-19) | The σ=0 reading `0.7837301587301587` was **already on screen** when the matched comparator's protocol was designed. That is the last remaining degree of freedom in the comparison and it is disclosed rather than inferred later: `sigma_zero_was_visible` is a REQUIRED key of **both** records (verified present and `true` in `phase23_matched_verdict.json`), refused-if-missing by `prove_verdict_record_declares_visibility` and `prove_control_record_declares_visibility`, and the full disclosure text travels verbatim with both artifacts. What remains blind is enumerated in the same field: the reduction, the central-reading pin, the verdict and the seed ladder, all pinned at `c7de5d4` and byte-unchanged. | Plan-time disposition (23-15/17/19) | 2026-08-29 |
| AR-23-04 | T-23-67b (23-16), T-23-71c (23-17) | The matched comparator's records omit `ppl_*` and token fields. Accepted because they are recorded as explicit `None` with a stated `ppl_omitted_reason` and declared in `MATCHED_DIFFERENCES` / `omitted_fields` rather than back-filled — a reader diffing against the old control record finds the reason in the record. Verified present: `omitted_fields.fields.ppl_scored_targets = null` and per-seed equivalents. | Plan-time disposition (23-16/17) | 2026-08-29 |
| AR-23-05 | T-23-77 (23-20) | `scripts/phase23_resume_prereg.py` **cannot** be frozen by the phase-20 ancestry guard: `adds[-1]` for `MATCHED_ARTIFACT_GLOB` is `d99d2aa`, which precedes any commit of this file, so conjunct 2 can never hold. What stands in is `test_the_resume_pin_has_exactly_one_commit` — **detection after the fact, strictly weaker than the frozen pin's guarantee**. Verified: the file has exactly one commit (`e70a035`). Accepted and DISCLOSED as clause (5) of `CONTINUATION_SCOPE`, not papered over. | Plan-time disposition (23-20) | 2026-08-29 |
| AR-23-06 | T-23-76 (23-20) | D-04's halt untouched by 23-20 — no verdict rendered there, and `git ls-files 'results/phase23_noised_*'` was `0` at that plan's start and end. Accepted rather than mitigated because the guard IS the mitigation: the ordering test and the gate are what enforce it, and both were re-run in this audit. See S-5 for the current (correct, later, gate-cleared) state of that glob. | Plan-time disposition (23-20) | 2026-08-29 |
| AR-23-07 | T-23-62d (23-15), T-23-68c (23-17) | **The full-delete case is PREVENTED BY NOTHING in real time.** A delete that removes `data/phase23_run_state.json`'s `matched` section reads `prior = {}` and `scored = []` and is indistinguishable from a first attempt at run time. Accepted at exactly that strength: the file is TRACKED as of `cfa2c87` with a baseline carrying no `matched` section and is committed WITH the record, so a later deletion is a **VISIBLE DIFF — auditable after the fact, not closed**. Tracking is explicitly **not** retroactive (before that commit a `git checkout --` leaves no history), so the same-session commit converts the residual from invisible to auditable rather than being its only bound. It remains a **DISCIPLINE, NOT A MECHANISM**, there is no force flag, and the four-clause scope is a required field of both records rather than a paragraph. | Plan-time disposition (23-15/17), disclosed in-artifact | 2026-08-29 |
| AR-23-08 | S-2 — T-23-63b (23-11), T-23-80b (23-14), T-23-75 (23-20) | **Disposition corrected by this audit from `mitigate` to a stated discipline.** The detached-launch procedure (`os.setsid` / `os.execv` / `os.getsid` probe / `caffeinate`) exists in **no committed file** — measured, zero matches across `scripts/`, `tests/`, `src/`. Accepted because (a) the harm class is Denial of Service — a lost training run, not a privacy leak; (b) the **recovery** half is fully coded and was exercised on a real harness kill (23-17, 3 of 5 seeds) through `prove_killed_run_continuation` + `committed_scored_seeds` from `git show HEAD:`; (c) execution evidence is committed and tracked — `SESSION pid=N pgid=N sid=N` is the first line of all three run logs. Residual accepted: nothing prevents the next long run being launched in the foreground. | security audit | 2026-08-29 |

*Accepted risks do not resurface in future audit runs.*

**No `mitigate` row was closed by acceptance.** AR-23-08 is a disposition *correction* recorded
against a threat whose coded half was verified present; the procedural half is named as a
discipline rather than allowed to read as a mechanism. That distinction is the whole point of
logging it.

---

## Pre-registered rule carried forward — CONTROL PROVENANCE

`deferred-items.md` pre-registers a rule for a caller that does not exist yet: any future consumer
of the formal gate's `control_taught_recall` / `control_heldout_recall` / `control_gap` **MUST**
source them from `results/phase23_matched_control.json` and **MUST NOT** source them from
`results/phase23_sigma_zero.json`'s `control_*` section. **This audit verified the rule is not
violated at HEAD**, rather than accepting the note's own claim:

- `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module`
  re-run here → **`1 passed`**.
- Independent AST census by this audit: the only non-test callers of `mitigation_point_verdict`
  are `scripts/mitigation_gate.py`'s own `FIXTURE_*` self-check (5 sites) and the single
  sanctioned route at `scripts/phase20_gate_coverage.py:660`. **Zero** live callers.
- No file under `scripts/` or `src/` reads a `control_*` field out of
  `results/phase23_sigma_zero.json`. The only occurrences of the three field names outside
  `mitigation_gate.py`'s labelled fixtures are `phase20_gate_coverage.py`'s **kwargs** (no source)
  and a string in `scripts/phase23_run.py:4019-4020` that **states the rule**.

The rule is carried forward unclosed by design — it governs a phase that has not been written.

---

## Unregistered Flags

**None.** 13 of 20 SUMMARYs carry a `## Threat Flags` section; all 13 report `None`, and each
states affirmatively that no network endpoint, auth path, file-access pattern or trust-boundary
schema was introduced. Seven SUMMARYs (23-01, 23-05, 23-06, 23-07, 23-08, 23-09, 23-10) carry
**no** `## Threat Flags` section at all — recorded here as a documentation gap rather than
inferred to be `None`.

Spot-checked rather than accepted:

| Claim | Check | Result |
|---|---|---|
| no `shell=True` | repo-wide grep over `scripts/` `src/` `tests/` | `_git` passes an argv tuple with explicit `cwd=`; no executable `shell=True` |
| no package installed | `git log -1 -- pyproject.toml` | `6a46441` (2026-07-31) — predates the phase; `tests/test_package.py` green |
| frozen gate untouched | `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py` | exit **0**; `mitigation_gate.py`'s last commit is `abf9072` (Phase 20) |
| frozen prereg untouched | `git diff --exit-code c7de5d4 -- scripts/phase23_prereg.py` | exit **0** — byte-identical |
| edit-once modules | `git log -- <each>` | `phase23_prereg.py` **1** commit, `phase23_matched_prereg.py` **1**, `phase23_resume_prereg.py` **1** |
| budget module literal-only | `ast` walk | 0 imports, 16 `Assign`, 0 `FunctionDef`/`If`/`For`/`Import` |
| gate ↛ budget import | `ast` import census | `{erasure_gate, pathlib, sys}` — `mitigation_budget` absent |
| no scratch probe survived | `git status --short scripts/` | **EMPTY** |
| run logs outside the noised glob | `fnmatch` against imported `NOISED_RECORD_GLOB` | 3 of 3 outside; 3 of 3 tracked |

**One INFO this audit raises that no SUMMARY did:** the never-taught arm publishes
`extraction_noise_floor = 0.0` from `nontarget_successes = 0` over 416 questions — a reading a
silently-degraded scorer would produce identically. Verified **not** vacuous: the standing
positive control `test_the_never_taught_scorer_registers_a_constructed_success`
(`tests/test_phase23_ctrl.py:740`) drives the **unmodified** `phase18_extraction.score_records` at
the real 416-question gated denominator over the real fact ids and all attack families, with a
meta-guard proving the miss filler leaks nothing through the scorer's own `contains_value`, and
asserts the miss→hit discrimination moves the reading `0 → 1`. A second control
(`test_the_retained_draws_move_the_gated_reading_from_zero_to_one`, `:855`) reproduces it on the
**real generated completions**, adapter-sha256-pinned against the committed block. Both ran in
this audit's `232 passed`. This landed at the UAT (`17c28c8`) rather than at plan time, so it is
not a register row — it is recorded here because it is what makes the published `0.0` evidence
rather than a coincidence.

---

## Security Audit Trail

| Audit Date | Threat Rows | Distinct IDs | Closed | Open | Accepted | Run By |
|---|---|---|---|---|---|---|
| 2026-08-29 | 164 | 113 | 164 (142 mitigate) | 0 | 22 rows / 8 log entries | `/gsd:secure-phase 23` — gsd-security-auditor, State B (create) from plan-time register |

Evidence commands (exit codes captured as `OUT=$(cmd); E=$?`, never after a pipe):

```
.venv/bin/python -m pytest -q tests/test_phase23_*.py          # 232 passed, 0 skipped (exit 0)
.venv/bin/python -m pytest -q tests/test_package.py            # 3 passed
.venv/bin/python -m pytest -q \
  tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module
                                                               # 1 passed
.venv/bin/python -m ruff check .                               # All checks passed! (exit 0)

git diff --exit-code c7de5d4 -- scripts/phase23_prereg.py      # exit 0 (byte-identical)
git diff --exit-code -- scripts/mitigation_gate.py \
                        scripts/mitigation_accountant.py       # exit 0
git diff --exit-code -- scripts/phase18_extraction.py          # exit 0
git diff --exit-code -- src/personacore/privacy/dpsgd.py       # exit 0
git status --short scripts/                                    # EMPTY

git merge-base --is-ancestor c7de5d4 2d06989                   # exit 0  prereg  < sigma_zero
git merge-base --is-ancestor 2d06989 0a275c9                   # exit 0  sigma_0 < verdict
git merge-base --is-ancestor 0a275c9 ab9d246                   # exit 0  verdict < noised
git merge-base --is-ancestor 746ecf6 HEAD                      # exit 0  human act < HEAD

git show --name-only --format= 746ecf6 | grep -c '^\(scripts\|src\)/'   # 0
git log -S"UNBLOCKED 2026-08-28 …" --format=%H -- .planning/STATE.md    # 1 sha, == the pin
git show HEAD:.planning/STATE.md | grep -c "<sentinel>"                 # 1
```

AST / re-derivation checks were run through `.venv/bin/python` with `ast`, `json` and `hashlib`;
their results are in the *Numbers re-derived by this audit* table above.

No implementation file was read-modified. This document is the only file created.

---

## Sign-Off

- [x] All 164 register rows have a disposition (142 mitigate / 16 accept / 6 accept + disclose / 0 transfer)
- [x] Every row keyed on (threat_id, component); 25 ID collisions named, none renumbered
- [x] Row total **and** distinct-ID total both published (164 / 113) so neither can be mis-derived
- [x] Accepted risks documented in Accepted Risks Log (8 entries covering 22 rows + 1 audit-raised residual)
- [x] `threats_open: 0` confirmed — `### Open` reads `None.`
- [x] Five findings recorded (S-1 … S-5); none blocking under `block_on: high`
- [x] The pre-registered CONTROL PROVENANCE rule verified un-violated at HEAD, by independent AST census
- [x] Boundary of the audit stated at the top, including what was NOT measured
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-29 at HEAD `522f8a5` — with the five recorded findings, the
disposition correction logged as AR-23-08, and the stated boundary. The frozen pre-registrations
were re-verified byte-identical in this process (`git diff --exit-code c7de5d4` → 0), the D-04
gate's five conjuncts were re-executed against real git rather than read out of the driver, and
every published figure cited above was recomputed here under exact equality rather than quoted
from a SUMMARY.
