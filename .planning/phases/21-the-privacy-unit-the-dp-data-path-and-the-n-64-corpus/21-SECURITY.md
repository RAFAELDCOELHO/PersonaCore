---
phase: 21
slug: the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
status: verified
threats_open: 0
threats_total_rows: 91
threats_distinct_ids: 65
asvs_level: 1
created: 2026-08-25
audited_at_head: 3af80b0ca96fb2fc5ce62a4925e36f52b691905a
---

# Phase 21 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (`register_authored_at_plan_time: true`). This document
> **verifies** the declared mitigations exist in implemented code. It does **not** scan for
> new threats.

---

## Boundary of this audit — read this first

What was done:

- All 11 `<threat_model>` blocks extracted from `21-01-PLAN.md` .. `21-11-PLAN.md` — **91 rows**.
- Every row keyed on the **(threat_id, component) pair**, never on the id alone.
- Every `mitigate` row traced to a named symbol, assertion or constant **in the implementation
  at HEAD `3af80b0`**, by grep + source read. Where the plan named a test, the test's presence
  *and* the mechanism it exercises were both located.
- Targeted suite executed: `164 passed` over
  `tests/test_phase21_*.py tests/test_phase20_prereg.py tests/test_package.py`
  via the absolute `.venv/bin/python`. `ruff check .` → `All checks passed!`.
- The four post-execution review closures (CR-01, WR-02, CR-02, WR-04) and WR-06 were
  re-verified in source directly, not accepted from `21-REVIEW.md`.
- Ancestry re-derived with `OUT=$(cmd); E=$?` — never `$?` after a pipe.

What was **not** done, and is therefore not evidence here:

- **The full suite was not re-run.** The stated baseline (1024 passed / 1 skipped) is inherited,
  not measured by this audit. `deferred-items.md` D-1 records a pre-existing RED in
  `tests/test_phase18_docs.py` from a README edit; not re-checked, not security-relevant.
- **No independent vulnerability scan.** Per `register_origin`, the register is treated as
  complete. Attack surface outside these 91 rows was not sought.
- **Deliberate-RED observations were not re-run.** Where a plan's evidence is "OBSERVED going
  red" (a transient working-tree mutation), this audit verified the *permanent mechanism* and
  cites the SUMMARY for the observation. Nine rows rest on that split; each is flagged
  `[RED cited]` below.
- **The working tree is NOT clean.** `.gitignore` carries one uncommitted hunk (adds
  `.obsidian/`) unrelated to Phase 21. It does not touch any guarded path. Flagged because the
  task brief asserted a clean tree.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| git history → published claim | The pre-registration's authority rests entirely on commit ordering. Ancestry is the only property that costs a full object rewrite to falsify. | commit SHAs, `results/phase21_*.json` |
| the `mitigation_*.py` glob → runtime dependency surface | A new module joining the glob widens an accumulated `imported` set that four assertions read. | import graph |
| working tree → committed baseline | A fixture or artifact captured from an edited tree encodes NEW behaviour as the OLD baseline, converting downstream identity assertions into tautologies. | golden fixtures, `provenance.git_sha` |
| build artifact → training loop | The three aligned bins are untrusted input. A shape or length error becomes an epsilon that bounds nothing, silently. | `uint16`/`uint8` memmaps |
| private fact values → observable volume of "public" data | The DP argument requires the public term to be independent of the private records. `round(replay_ratio * teaching_tokens)` makes it a function of them. | replay token count |
| a new fact value → every published instrument | A filler value reaching the 10-value LOCKED+SOFT leak vocabulary confounds the GATE-10 capacity comparison and would force an edit to an ancestry-guarded file. | fact value strings |
| an unordered container → a byte-level guarantee | A `frozenset` iterated raw yields a different order per process; every downstream sha256 inherits the nondeterminism and it never surfaces as an error. | rendered episodes |
| an instrument's output → a published record | An instrument nobody has tested produces a number indistinguishable from a guess. | multiplicity counts |

---

## ID collisions — PRE-EXISTING at HEAD, recorded not renumbered

Ten IDs are overloaded across the 91 rows, and the overloading is **mixed**: some are one
threat legitimately cross-referenced, some are several distinct threats colliding on one id.
This was introduced during planning, is present at HEAD, and is **not** an execution defect.
Nothing is renumbered — naming the collisions is the deliverable.

| ID | Plans | Verdict | Detail |
|----|-------|---------|--------|
| `T-21-11` | all 11 | **1 threat, cross-referenced 11x** | Identical text every time: supply chain, `accept`, `tests/test_package.py:36`. Legitimate. |
| `T-21-05` | 01, 02, 03, 04, 05 | **5 DISTINCT threats** | (01) glob ships as unenforced declaration; (02) golden fixture certifies the change it should detect; (03) fixture guards the wrong prefix; (04) `align_facts=None` identity vacuous because kwarg never read; (05) `question_bank=None` ships as an unfailable guard. Same *class* ("a guard that cannot fail"), five different components. **Closing one would silently close five.** |
| `T-21-03` | 01, 03, 11 | **3 DISTINCT threats** | (01) post-hoc edit to `scripts/mitigation_unit.py` after an artifact lands; (03) the glob addition silently reverted leaving the fixture green; (11) an artifact committed BEFORE the pin, permanently reddening the ancestry guard. |
| `T-21-04` | 05, 07, 09 | **2 distinct** | (05) an edit to `phase14_factset.py` moves a published row — different threat. (07)+(09) are ONE threat in two tiers: a filler value entering the 10-value leak vocabulary, refused at import (tier 1, 07) and scanned from outside (tier 2, 09). |
| `T-21-08` | 05, 07, 09 | **2 distinct** | (05)+(07) identical: an edit reaches `phase18_extraction.py` or the FROZEN `mitigation_gate.py`, checked by `git diff --exit-code`. (09) is a variant: `phase18_extraction.py` + `results/phase16_recall_sample.json`, checked by two byte-mode sha256 pins. Different second file, different mechanism. |
| `T-21-06` | 01, 03, 11 | **1 threat, 3x** | Ancestry laundering via `git rm` + re-add. Same threat, same mechanism (`adds[-1]`), cited from three plans. |
| `T-21-07` | 01, 03 | **1 threat, 2x** | A `phase21_`-named probe reaching the real git history. |
| `T-21-15` | 02, 08 | **1 threat, 2 components** | A test unrunnable on CI because it reads machine-local `data/`. (02) the golden fixture; (08) the replay differential. |
| `T-21-20` | 04, 06 | **1 threat, 2 enforcement points** | Correct offsets over wrong bytes (roll-by-1), caught at BUILD time (04) and at DRAW time (06). |
| `T-21-24` | 04, 06 | **1 threat, 2x** | A test writes into `data/`, overwriting recorded arm evidence. |

**One collision was avoided by the planner and is recorded as good practice:** `21-10-PLAN.md`
renumbered its own `T-21-49` → `T-21-64` on discovering `21-11` already used `T-21-49` for a
different threat, with the reason written into the register row. That is the correct handling
and the reason the ten above are recorded rather than repaired.

---

## Threat Register

Keyed on **(id, component)**. Rows sharing an id are separate entries. `[RED cited]` means the
permanent mechanism was verified in source by this audit but the deliberate-RED observation is
cited from the plan's SUMMARY, not re-run.

### 21-01 — the privacy-unit pin

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-03 | Tampering | `scripts/mitigation_unit.py` post-hoc edit after an artifact lands | mitigate | `tests/test_phase20_prereg.py:171` reads EVERY commit touching the pin (`git log --format=%H -- <pin>`); each is ancestry-checked at `:186-205` | closed |
| T-21-06 | Tampering | ancestry laundering via `git rm` + re-add | mitigate | `tests/test_phase20_prereg.py:185` `first_add = adds[-1]` (earliest add) | closed |
| T-21-05 | Repudiation | the glob addition ships as an unenforced declaration | mitigate | BOTH halves present: `V4_ARTIFACT_GLOBS` at `:130` AND the live call `test_phase21_prereg_is_frozen_before_every_phase21_result` at `:257`; consistency assert at `:157` | closed |
| T-21-13 | Elevation of Privilege | the new sibling widens `{pathlib, sys, erasure_gate}` for every glob member | mitigate | `scripts/mitigation_unit.py` has **0** import statements (measured); asserted twice — accumulated glob scan `test_phase20_prereg.py:867-899`, and `test_phase21_unit_pin.py:136` | closed |
| T-21-07 | Tampering | a `phase21_`-named probe reaching the real git history | mitigate | **declared test was replaced by design at 21-11.** Property re-derived by this audit: `git log --all --diff-filter=A -- 'results/phase21_probe*'` = EMPTY; 62 `cwd=tmp_path/legit/root` sites vs 2 `cwd=_ROOT` (the `_git` default at `:133` and a legitimate subprocess re-import at `:1430`) | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` sha256 over `pyproject.toml` bytes | accepted |
| T-21-14 | Info Disclosure | a constant read off private data reaching the pin | accept | `scripts/mitigation_unit.py:60` explicitly excludes the D-11 VOLUME constant; pin sha256 `45f37e15…` UNCHANGED (measured) | accepted |

### 21-02 — golden fixtures

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-05 | Repudiation | a golden fixture that certifies the change it was meant to detect | mitigate | `scripts/phase21_golden_capture.py:147` — `_refuse_if_dirty()` at **module scope, ahead of** the `phase14_factset`/`teach_persona` imports at `:149-150`; again at call time `:263` | closed |
| T-21-15 | DoS | fixture unregenerable on CI because it reads `data/dialog_train.bin` | mitigate | `replay_ratio = 0.0` at `:175`; `grep -c dialog_train` on both fixtures = **0** (measured) | closed |
| T-21-16 | Spoofing | a stale fixture read as a code regression | mitigate | `meta.captured_at_sha` present in all 3 golden fixtures; `meta.tokenizer_sha256` in `golden_build_bins_v2.json` and compared with a naming message at `tests/test_phase21_aligned_bins.py:203-206`. *Scope: `tokenizer_sha256` is absent from `golden_render_family_v2.json` — that capture does not tokenize, so the field is N/A there.* | closed |
| T-21-17 | Tampering | the capture overwrites recorded arm evidence under `data/` | mitigate | `tempfile.TemporaryDirectory()` at `:181`; `tp.refuse_if_exists([...])` at `:264` | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-03 — throwaway-repo ancestry fixture

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-07 | Tampering | a `phase21_`-named probe reaching the real git history | mitigate | every fixture `_git` call passes `cwd=tmp_path`; real-history probe adds = EMPTY (measured) | closed |
| T-21-06 | Tampering | ancestry laundering via delete-and-re-add | mitigate | `adds[-1]` at `:185`; state-4 `len(adds)==2 AND adds[-1]==state1_add` driven across a real cycle [RED cited: 21-03-SUMMARY] | closed |
| T-21-05 | Repudiation | the fixture guards the wrong prefix and nobody can tell | mitigate | positive `ls-files 'results/phase21_*'` observation at `:748-750`; Mutation A (swap to `phase20_*`) [RED cited] | closed |
| T-21-03 | Tampering | the glob addition silently reverted, leaving the fixture green | mitigate | `assert artifact_glob in globs` at `:157`; Mutation B observed firing at both tiers [RED cited] | closed |
| T-21-18 | Spoofing | an unrelated `CalledProcessError` satisfies `pytest.raises` | mitigate | `tuple(exc.value.cmd[:3]) == ("git","merge-base","--is-ancestor")` at `:584`, `:627`, `:761`, `:805` | closed |
| T-21-19 | Injection | a glob containing a shell metacharacter is expanded by a shell | mitigate | `_git` at `:144-146` passes an argv tuple to `subprocess`; `shell=True` occurs in **no** executable position repo-wide (only in prose) | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-04 — the aligned packer

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-20 | Tampering | a packing bug writes correct offsets over wrong bytes (build side) | mitigate | `fact_window_impurities` reads bytes back from disk (`data.py:162`); `test_a1_is_the_roll_it_claims_to_be` + `test_offsets_alone_cannot_see_the_roll` (`aligned_bins.py:64,119`) | closed |
| T-21-05 | Repudiation | the `align_facts=None` identity guard is vacuous because the kwarg is never read | mitigate | kwarg IS read: `data`-path branch at `teach_persona.py:441-442`; `test_align_facts_is_wired` at `aligned_bins.py:229` | closed |
| T-21-21 | Tampering | a sentinel-padded fact bin makes the INPUT-space guard unsatisfiable | mitigate | constraint in `fact_window_impurities`' docstring; adversary `A3` at `aligned_bins.py:55` asserted `[1]` at `:76` | closed |
| T-21-59 | DoS | a purity predicate unioning input and target space refuses every correct bin | mitigate | `space="input"` is the DEFAULT (`data.py:156`); **no union mode** — stated `:173`, refused `:209-213`; A0 asserted `[]` input / `[1,2]` target on the SAME fixture (`:97`, `:109`) | closed |
| T-21-60 | Repudiation | the target-space boundary is DROPPED rather than stated | mitigate | `aligned_bins.py:110` asserts `len(...) == n_facts - 1`; `teach_persona.py:663-664` asserts `expected = len(align_facts) - 1` on the build path | closed |
| T-21-22 | DoS | a truncated or mis-length fact bin reaches the loop | mitigate | `_window_count` (`data.py:129-149`) raises naming the remainder; A4 at BLOCK=4 (`:84`) **and** at the real `block_size` (`:298-299`) | closed |
| T-21-23 | Repudiation | content purity mistaken for a proof that `grad_accum_steps == n_facts` | mitigate | A5 asserted **passing** purity (`aligned_bins.py:77`, `("A5-short", A5, [])`) while `test_n_facts_is_asserted_not_trusted` (`aligned_loader.py:415`) carries the complementary check | closed |
| T-21-24 | Tampering | a test writes into `data/`, overwriting recorded arm evidence | mitigate | Tier 1 REAL: `monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)` at `aligned_bins.py:333`; `refuse_if_exists` at `teach_persona.py:922`. **Tier 2 VACUOUS — see Finding S-1.** | closed (tier 1) |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-05 — the `forms=` override

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-05 | Repudiation | shipping `question_bank=None` — a guard that CANNOT fail | mitigate | the kwarg is **DROPPED**: `question_bank` appears nowhere as a parameter; the measurement forcing the drop is recorded at `scripts/phase14_factset.py:856-859`. Threat removed rather than guarded. | closed |
| T-21-25 | Repudiation | `forms=None` identity certifies a kwarg that is never read | mitigate | kwarg IS read: `phase14_factset.py:699` `(SLOT_FORMS if forms is None else forms)[fact.slot]`, second register at `:869-871`; `test_forms_is_wired` parametrized over both registers (`test_phase21_filler.py:130`) [RED cited: inert-kwarg revert, 21-05-SUMMARY] | closed |
| T-21-04 | Tampering (instrument) | an edit to `phase14_factset.py` moves a published row | mitigate | diff restricted to two functions (50+/6− across the phase, measured); full SC5 guard set re-run — 164 passed | closed |
| T-21-26 | Tampering | a filler grammar typo silently renders through a SCORED slot | mitigate | `phase14_factset.py:699` raises `KeyError` on a missing slot — no fallback to `SLOT_FORMS`; `test_forms_missing_slot_raises` at `test_phase21_filler.py:140` | closed |
| T-21-08 | Tampering | an edit reaches `phase18_extraction.py` or the FROZEN `mitigation_gate.py` | mitigate | `git diff --exit-code` → **0** (measured at HEAD); both files byte-unchanged across the entire phase (`git diff 8d3beb4^ HEAD` empty). **See Finding S-3 for the persistence gap.** | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-06 — the aligned loader

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-02 | Repudiation | a silently-dropped fact bin makes `grad_accum_steps != n_facts` | mitigate | `test_fact_map_is_consumed_at_runtime` (`aligned_loader.py:109-129`) mutates the fact bin between two calls in one process [RED cited: cumsum reimplementation] | closed |
| T-21-12 | DoS | a truncated / missing / mis-length fact bin reaches the loop | mitigate | `data.py:367-372` names WHICH bin is unopenable; `:374-380` names all three lengths; `:387-393` the whole-bin contract; `test_fact_bin_required_raises_distinguishably` at `:180` | closed |
| T-21-20 | Tampering | correct offsets over wrong bytes (draw side) | mitigate | `test_positional_mutation_raises_input_space_impurity` at `aligned_loader.py:273` | closed |
| T-21-61 | DoS | the draw-time purity check widened to target space raises on a CORRECT bin | mitigate | `data.py:407` calls `fact_window_impurities(slice, block_size)` with **no `space=`** → pinned to the input default; `test_valid_bin_never_raises_on_any_fact` at `:353`. Repo-wide `space="target"` audit: 5 sites, all deliberate boundary counts. | closed |
| T-21-62 | Repudiation | 21-10 re-implements window arithmetic and counts a different draw | mitigate | `fact_window_span` is exported (`data.py:225`) and is the ONE computing site: loader `data.py:404`, counter `phase21_unit_record.py:128,497` | closed |
| T-21-27 | Spoofing | the guard reads the TOKEN bin and reports fact attribution from it | mitigate | `fact_index` derives only from `facts`/`step` (`data.py:403`); `test_n6_token_bin_mutation_leaves_fact_attribution_unchanged` at `:324` | closed |
| T-21-28 | Repudiation | a loader that always raises passes every adversarial case | mitigate | `test_n5_unmutated_fact_bin_is_the_negative_control` at `aligned_loader.py:311` | closed |
| T-21-29 | Repudiation | platform-dependent memmap coherence makes the proof flaky, not false | mitigate | `aligned_loader.py:125-129` — file sha256 asserted for token+mask bins **before** the behavioural assertion, with assumption A1 named in the message | closed |
| T-21-24 | Tampering | a test writes into `data/` | mitigate | Tier 1 REAL (`tmp_path` throughout). **Tier 2 VACUOUS — Finding S-1.** | closed (tier 1) |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-07 — the n=64 filler corpus

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-04 | Tampering (instrument) | a filler value enters the 10-value leak vocabulary (tier 1) | mitigate | `refuse_collisions()` runs at import (`phase21_filler.py:316-334`), bidirectional containment via `_collides`; the `!= 10` wall at `:270-275` **raises `SystemExit`, not `assert`** (WR-06 closure verified in source) | closed |
| T-21-30 | Tampering | refusal over the NAME (equality) while the harm is a PROPERTY (containment) | mitigate | `_collides(value, scored)` returns `(collided, direction)` — containment in BOTH directions, never equality (`:327`, `:340`, `:355`); reason restated independently at `test_phase21_sc5.py:139` [RED cited: `marrowgatex`, 21-07-SUMMARY — no live occurrence remains, only the explanatory comment] | closed |
| T-21-31 | Tampering | filler seated in a slot GATE-10 scores | mitigate | `set(pf.FILLER_SLOT_FORMS) & set(fs.SLOT_FORMS) == set()` at `test_phase21_filler.py:220`, and against `SLOT_QUESTION_BANK` at `:225`; missing-slot `KeyError` from 21-05 | closed |
| T-21-32 | Spoofing | filler acquires scored-fact authority via a pool, `_BY_ID` or `GATE_PROBES` | mitigate | four set-intersection assertions at `test_phase21_filler.py:242-246`; before/after `len(_BY_ID)`/`len(GATE_PROBES)` shape check at `:262-271` | closed |
| T-21-33 | Repudiation | the guessability waiver reads as an oversight | mitigate | `GUESSABILITY_WAIVER` module constant at `phase21_filler.py:391` carrying its measured price (1,792 generations, `:410`); `test_guessability_waiver_is_recorded` at `:375` | closed |
| T-21-34 | Tampering | filler and scored records differ in size under one clip norm | mitigate | filler renders through the SAME `fs.render_family` over `TAUGHT_FAMILY_IDS` (`phase21_filler.py:437-438`); row count asserted EQUAL to a `LOCKED_FACTS` member and inside `PARAPHRASES_PER_FACT_TARGET` (`test_phase21_filler.py:328-339`) | closed |
| T-21-57 | Repudiation | raw `frozenset` iteration makes the n=64 bin byte-different every run | mitigate | `for family_id in sorted(family_ids)` at `phase21_filler.py:437`; `test_render_filler_episodes_is_order_stable` compares digests across separate interpreters via `subprocess` (`test_phase21_filler.py:183-194, 351`) [RED cited: `sorted()` removal → 2 digests] | closed |
| T-21-58 | Repudiation | an unmeasured 1,232 asserted as a target | mitigate | `phase21_filler.py:164` labels the geometry an `ESTIMATE`; the binding assertion is observed equality + `PARAPHRASES_PER_FACT_TARGET` membership (`test_phase21_filler.py:328-339`) | closed |
| T-21-08 | Tampering | an edit reaches `phase18_extraction.py` or FROZEN `mitigation_gate.py` | mitigate | as 21-05; both byte-unchanged across the phase (measured). **Finding S-3.** | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-08 — the replay seam (D-11 side channel)

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-01 | Info Disclosure | replay volume `round(replay_ratio * teaching_tokens)` leaks private token lengths | mitigate | `replay_window_budget(n_facts, block_size)` at `teach_persona.py:180-204` — both factors public; taken by the `n_facts` branch at `:763-769` with `replay_ratio`/`teaching_tokens` explicitly IGNORED. Differential `test_side_channel_closed` (`:182`) + legacy negative control (`:221`). **Scope boundary — Finding S-2.** | closed (v4.0 path) |
| T-21-09 | Info Disclosure | the replay CONSTANT itself read off private data (947.625 = 7581/8) | mitigate | `test_replay_constant_is_not_derived_from_the_corpus` at `test_phase21_replay_volume.py:260` | closed |
| T-21-35 | Repudiation | a constant assertion (`== 8192`) mistaken for a proof of independence | mitigate | `_assert_fixture_actually_varies` at `:164-176` runs FIRST and asserts `short.teaching_tokens != long.teaching_tokens` with its own message; only then `:199` asserts the invariant | closed |
| T-21-36 | Repudiation | the off-identity guard certifies three kwargs accepted and discarded | mitigate | `loop.py:349-367` validates the trio and refuses partial/malformed wiring; `test_replay_seam_on_changes_the_trajectory` (`:332`), `..._draws_exactly_the_public_budget` (`:344`), `..._refuses_partial_or_malformed_wiring` (`:386`) | closed |
| T-21-37 | Repudiation | claiming an un-clipped public-gradient guarantee this plan does not deliver | mitigate | `loop.py:278-281` states per-record clipping is DPSGD-01/DPSGD-04, Phase 22, and names the overlap a RECORDED COST | closed |
| T-21-38 | DoS | `4 * 64 = 256` windows in one allocation on MPS | accept | micro-batched by ceil division at the loop's own `batch_size`, documented `loop.py:269-272` with the ragged-final-micro-batch weighting; D-25 defers sizing to Phase 22 | accepted |
| T-21-15 | DoS | a test reads machine-local `data/dialog_train.bin` | mitigate | Tier 1 REAL: `monkeypatch.setattr(tp, "DIALOG_TRAIN_BIN"/"DIALOG_TRAIN_MASK", <tmp_path>)` at `test_phase21_replay_volume.py:153-154`. **Tier 2 VACUOUS — Finding S-1.** | closed (tier 1) |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-09 — SC5 and the two capacity arms

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-04 | Tampering (instrument) | a filler value reaches the leak vocabulary (tier 2, from outside) | mitigate | `test_no_filler_leak` (`test_phase21_sc5.py:74`): direction 1 over six `INSTRUMENT_SOURCES` (`:44-51`), direction 2 over the 270-question fixture text (`:111-117`) | closed |
| T-21-39 | Tampering | a scored value leaks INTO the filler module | mitigate | direction 3 at `test_phase21_sc5.py:121-145`, asserted from OUTSIDE the module implementing the refusal. **The plan's literal prescription (`embedded_fact_values(<phase21_filler module>, scored)`) was measured unsatisfiable and replaced with the property it was for — recorded in-source at `:123-133`. Mitigation is stronger than declared, not weaker.** | closed (form changed) |
| T-21-08 | Tampering | any edit to `phase18_extraction.py` or `results/phase16_recall_sample.json` | mitigate | two byte-mode sha256 pins at `test_phase21_sc5.py:347-356`; both hashes re-computed by this audit and MATCH (`d2b44806…`, `407c4b93…`). Second tier: Phase-18 ancestry guard via `PHASE18_PREREG_ARTIFACT` (`test_phase16_prereg.py:80,364`) [RED cited: `# canary`] | closed |
| T-21-55 | DoS | a transient canary live beside a concurrent full-suite reader | mitigate | `21-09-PLAN.md:13` `depends_on: ["21-07","21-08","21-10"]` with the scheduling reason recorded at `:5-11` | closed |
| T-21-56 | Spoofing | an ancestry-guarded file in `files_modified` reads as permission to edit | mitigate | `21-09-PLAN.md:14-16` lists only `teach_persona.py` + `test_phase21_sc5.py`; the three guarded paths are DELIBERATELY absent with the reason at `:17-24` | closed |
| T-21-40 | Tampering | a CRLF rewrite passes a text-mode hash | mitigate | `.read_bytes()` at `test_phase21_sc5.py:351`, with the reason copied into this test's own docstring at `:333-336` rather than cited elsewhere | closed |
| T-21-41 | Repudiation | sampling only D-18's four wall sites | mitigate | `test_wall_census_is_the_measured_set` (`:258`) discovers sites mechanically by regex over `tests/` and compares a `(file, expr)` **multiset**, failing with the observed list. **Declared as 8 sites; MEASURED 11** (`_EXPECTED_WALL`, `:217-231`). The plan's name (`test_wall_census_is_eight_sites`) and count are both superseded — Finding S-4. | closed (count corrected) |
| T-21-42 | Tampering | the n=64 arm reintroduces replay into the teaching bin | mitigate | `arm_spec` returns `0.0` for `dp_n8` (`teach_persona.py:881`) and `dp_n64`; asserted `stats["replay_tokens"] == 0` at `test_phase21_aligned_bins.py:368`; `test_dp_arm_replay_ratio_is_still_refused_through_build_arm_bins` at `:416` | closed |
| T-21-43 | Spoofing | a mutation committed rather than restored | mitigate | measured by this audit: `git diff 8d3beb4^ HEAD -- scripts/mitigation_gate.py scripts/phase18_extraction.py results/phase16_recall_sample.json` is **EMPTY** — no mutation entered history at any point in the phase | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-10 — the multiplicity instrument

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-10 | Spoofing | the instrument prints its own conclusion | mitigate | `test_instrument_can_report_not_one` (`test_phase21_multiplicity.py:488`) with the correct-bin negative control at `:539` in the same area | closed |
| T-21-44 | Repudiation | an UNNAMED attribution rule makes the two labelled rows non-comparable | mitigate | `ATTRIBUTION_RULE = "first-token-owns-draw"` in ONE place (`phase21_unit_record.py:153`), reused at `:325`, `:1107`, `:1200`, `:1287`; present in every committed row's `analytic_expectation.rule_this_row_was_counted_under` (measured) | closed |
| T-21-45 | Tampering | double-counting, dropped draws or an off-by-one | mitigate | `test_conservation` (`:154`) and `test_conservation_holds_at_the_real_budget_denominator` (`:180`) as exact equalities [RED cited: overshoot to 1,993] | closed |
| T-21-46 | Repudiation | the seed is not reaching the draw | mitigate | `test_seed_reproducible` at `test_phase21_multiplicity.py:200` | closed |
| T-21-47 | Repudiation | the instrument measures a re-implementation of the draw | mitigate | `count_unaligned` calls the real `get_batch_memmap_masked`; `count_aligned` takes its range from the exported `fact_window_span` (`phase21_unit_record.py:128,497`); `test_the_wrapper_call_count_is_asserted_not_assumed` at `:440` | closed |
| T-21-63 | Repudiation | `strict=False` becomes the path that produces the published row | mitigate | `strict=True` is the DEFAULT (`phase21_unit_record.py:448`), and `:1181` records that the published call runs at the default; `test_the_correct_bin_returns_normally_at_the_strict_default` at `:539` | closed |
| T-21-65 | DoS | `strict=False` guards only the loader call, so `fact_window_span` aborts the count | mitigate | BOTH calls inside ONE `try/except ValueError` (`:495-516`); `stage`/`per_step_raised` records `"span"` as its own outcome class (`:474`, `:495`, `:530`) [RED cited: `"span"` observed at step 7 of a full lot] | closed |
| T-21-48 | Repudiation | an analytic number becomes the artifact | mitigate | `test_analytic_cross_check_only` (`:568`); every committed row carries `analytic_expectation.labelled = "ANALYTIC — … NOT a measurement"` (measured) | closed |
| T-21-64 | Tampering | an artifact committed before the pin | mitigate | **declared test replaced by design at 21-11.** Property re-derived: pin `8d3beb4`, first-add `c79b9bf`, `git merge-base --is-ancestor` exit **0** and `pin != first_add`. Successor: `test_the_committed_artifacts_are_exactly_the_declared_paths` (`:615`) | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

### 21-11 — the two published artifacts

| Threat ID | Category | Component | Disp. | Mitigation verified at | Status |
|---|---|---|---|---|---|
| T-21-03 | Tampering | an artifact committed BEFORE the pin | mitigate | measured: `git merge-base --is-ancestor 8d3beb4 c79b9bf` exit **0**, captured as `OUT=$(…); E=$?` not after a pipe; strict-ancestor conjunct `prereg != first_add` enforced at `test_phase20_prereg.py:194-199` | closed |
| T-21-06 | Tampering | laundering a wrong order by `git rm` + re-add | mitigate | `adds[-1]` at `:185`; measured non-launderable across a real cycle by 21-03 [RED cited] | closed |
| T-21-50 | Tampering | the artifact restates a pinned value that later drifts | mitigate | `test_artifact_values_come_from_the_pin` (`test_phase21_unit_record.py:152`) recomputes every pinned field from `mitigation_unit`; `test_the_artifact_records_the_pin_it_was_written_against` at `:308` | closed |
| T-21-51 | Repudiation | an analytic number published as the measurement | mitigate | `analytic_expectation` is a SEPARATE field beside `mean` in all 5 committed rows (measured); `test_analytic_expectation_sits_beside_the_measurement_never_in_place_of_it` at `:538`. **See Finding S-5 for the residual (WR-05).** | closed |
| T-21-52 | Repudiation | A3's assumed 264-window geometry published as a measurement | mitigate | `a3_discharge` in `phase21_multiplicity.json`: `assumed 264 / observed 316 / holds: false / "The corpus was NOT adjusted to reach 264"` (measured); `test_corpus_geometry_is_observed_and_discharges_a3` at `:563` | closed |
| T-21-53 | Repudiation | a row silently omitted because `data/dialog_train.bin` is absent | mitigate | all **5** rows present in the committed artifact (measured); labelling path present in schema | closed |
| T-21-49 | Tampering | the guard stays vacuous after the artifacts land | mitigate | `test_phase21_guard_is_now_live` (`test_phase20_prereg.py:391-425`); measured: 2 tracked artifacts × 1 pin commit → `checked = 2`, non-zero. **21-11-SUMMARY recorded this as "not yet discharged" — it IS discharged at HEAD.** | closed |
| T-21-54 | Repudiation | publishing an epsilon this phase has no basis for | mitigate | `provenance.epsilon_computed` is `False` in BOTH committed artifacts (measured); no accountant code in the phase | closed |
| T-21-11 | Tampering | supply chain | accept | `tests/test_package.py:36` | accepted |

---

## Findings — WARNINGS, none blocking

No declared mitigation is absent. Five weaknesses in the *evidence* are recorded. None reaches
BLOCKER: in each case a real first-tier mechanism was located in source.

### S-1 (WARNING) — `git status --porcelain data/` is a guard that cannot fail

Declared as second-tier evidence for **T-21-24** (21-04, 21-06) and **T-21-15** (21-08).
Measured at HEAD: `data/` is gitignored (`.gitignore:17`, confirmed by `git check-ignore -v`)
and `git ls-files data` returns **0 files**. `git status --porcelain data/` therefore returns
empty *unconditionally* — including in the exact scenario it claims to detect, a test
overwriting `data/persona_dp_n8_train.bin`.

This is an instance of the phase's own **T-21-05 class** ("a guard that cannot fail") appearing
in the phase's own verification blocks. It appears in `21-06-PLAN.md:313,364`,
`21-08-PLAN.md:277,358,400` and is reported as satisfied in four SUMMARYs.

Not a blocker: tier 1 is real and was verified —
`monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)` (`test_phase21_aligned_bins.py:333`),
`monkeypatch.setattr(tp, "DIALOG_TRAIN_BIN", …)` (`test_phase21_replay_volume.py:153`), and
`refuse_if_exists(arm_bin_targets(...))` in production at `teach_persona.py:922`.

Suggested successor check (for a future phase, **not** applied here):
`ls data/` before/after, or an mtime comparison — anything that observes the filesystem rather
than the index.

### S-2 (WARNING) — T-21-01 closes the v4.0 branch only; the legacy branch is a live, labelled side channel

The register states `replay_window_budget(n_facts)` is "**the single computing site**". Measured
at HEAD it is not: `scripts/teach_persona.py:757` is a second computing site,
`want = int(round(replay_ratio * teaching_tokens))`, taken whenever `n_facts is None`.

`build_bins`' flat path calls `_prepend_replay(...)` at `:455` with **no `n_facts` kwarg**, so
every non-DP arm with `replay_ratio > 0` takes the legacy branch. `REAL_RUN_REPLAY_RATIO = 1.0`
(`:227`) makes `cal_first_person_replay` — an arm the real run uses — one of them.

This is **deliberate and labelled in source** (`:760`: *"this branch carries the D-11 side
channel by design"*) and is actively measured by `test_side_channel_negative_control`
(`test_phase21_replay_volume.py:221`), which asserts the legacy branch still leaks by exactly
the private spread. It is the negative control that proves the differential can see a leak.

Recorded so the closure is not over-read: **the D-11 side channel is closed on the aligned/DP
data path, not repo-wide.** IN-04 (`21-REVIEW.md:488`) is the same fact from the other side —
`train()`'s replay seam has no production caller, so the replacement path is built but unwired.
Wiring it is Phase 22 (DPSGD-01/04).

### S-3 (WARNING) — T-21-08's `mitigation_gate.py` half has no persistent guard

`scripts/phase18_extraction.py` carries two persistent tiers (sha256 pin at
`test_phase21_sc5.py:348`, ancestry guard via `PHASE18_PREREG_ARTIFACT`).
`scripts/mitigation_gate.py` carries **neither**: it is not sha256-pinned and
`PHASE21_PREREG_ARTIFACT` is `scripts/mitigation_unit.py`, not the gate
(`test_phase20_prereg.py:100-108` records this as deliberate — "protected-but-not-frozen BY
DEFAULT").

T-21-08's declared evidence for it, `git diff --exit-code`, is a **plan-time working-tree
check**. It proves nothing about a committed edit. It does carry real structural guards
(banned numeric constants, superseded-string scan, import-graph scan at
`test_phase20_prereg.py:867-899, 1133-1435`) and is inside `INSTRUMENT_SOURCES` for the filler
leak scan — so it is not unguarded, only not byte-frozen.

Re-verified for this phase: `git diff --exit-code` exit **0** at HEAD, and
`git diff 8d3beb4^ HEAD -- scripts/mitigation_gate.py` is **empty** — nothing in Phase 21
touched it. The threat is closed *for this phase*; the mechanism does not extend forward.

### S-4 (INFO) — declared-vs-implemented drift in T-21-41, and stale line anchors

- `21-09-PLAN.md` declares `test_wall_census_is_eight_sites` and a must-have "All **EIGHT**
  `len(...) == 10` wall sites across SEVEN files". Implemented: `test_wall_census_is_the_measured_set`
  over **11** sites. The census discovers sites mechanically and would fail if the set moved, so
  the implementation is stronger; the plan's literal must-have is false as written.
- `21-01-PLAN.md` cites `:143`, `:157`, `:129` in `test_phase20_prereg.py`; the mechanisms are
  now at `:171`, `:185`, `:157`. All three located and verified — anchors drifted, mechanisms intact.
- `tests/test_phase21_sc5.py:268-269` still describes
  `scripts/phase21_filler.py:263`'s wall as a *"module-level `assert`"*. WR-06 promoted it to
  `raise SystemExit` at `:270-275`. Stale docstring; the code is correct.

This is the IN-02 class. Recorded, not fixed — no implementation file may be modified by this audit.

### S-5 (INFO) — two open review findings carry record-integrity, not code, consequences

Assessed per the brief. Of the five findings left open in `21-REVIEW.md`:

- **WR-05** — `findings.d10_doubles_the_unaligned_multiplicity` is built on
  `ratio_of_the_means`, which the same artifact's `budget.attribution_rule_note` says carries no
  information. Same *class* as T-21-51 ("an analytic number published as the measurement"), and
  it lives in a committed, ancestry-guarded artifact that cannot be quietly corrected.
  Consequence is a misreadable published privacy record, not an exploitable defect.
- **WR-07** — the FROZEN pin (`mitigation_unit.py:119-124`) tells the reader to attribute a
  **systematic** 55.93 rule gap to "sampling noise". Same class. The artifact side is correct:
  `pin_discrepancy` is present in `phase21_multiplicity.json` (measured) and names both rules,
  both formulas and the gap. Correction vehicle is `scripts/_addendum.py`, never an edit.
- **IN-01** — `_prove(SAMPLING_RATE_Q == 1.0, …)` at `mitigation_unit.py:247` compares a
  module-level literal (`:131`) to itself. A third in-phase instance of the T-21-05
  "guard that cannot fail" class, this one inside the frozen pin. Inflates a claimed guard count
  by one; the other four `_prove` guards evaluate real arithmetic (verified: `DELTA * 8`,
  `DELTA * 64`, and both `rejected_delta` products).
- **IN-02** — see S-4. No security consequence.
- **IN-04** — see S-2. Scope, not gap.

None is a BLOCKER. WR-05 and WR-07 are logged as accepted-risk rows below so they do not
resurface unclassified.

---

## Accepted Risks Log

The 13 `accept` rows (11 × T-21-11 + T-21-14 + T-21-38), plus the two record-integrity residuals
from S-5.

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| AR-21-01 | T-21-11 (all 11 plans) | Supply chain. **Zero package installs across the entire phase** — verified: `pyproject.toml` sha256 matches its v2.0 pin at `tests/test_package.py:36`, and no plan adds a dependency. The pin is byte-level, so a transitive change to the declared set is RED. Residual accepted: the pin covers the *declaration*, not the resolved wheel set. | Phase 21 plans 01-11 | 2026-08-22 |
| AR-21-02 | T-21-14 (21-01) | A corpus-derived constant reaching the frozen pin. Accepted because D-23 EXCLUDES the D-11 replay VOLUME constant from `mitigation_unit.py` by construction — recorded in-source at `:60` — and it lands in 21-08 with its own differential guard instead. Verified: pin sha256 `45f37e15…` unchanged, module holds no corpus-derived number. | Phase 21 plan 01 | 2026-08-22 |
| AR-21-03 | T-21-38 (21-08) | `4 * 64 = 256` replay windows in one MPS allocation. Accepted because the seam micro-batches by ceil division at the loop's own `batch_size` (`loop.py:269-272`), weighting each micro-batch by its actual window count so the ragged final batch contributes exactly one replay MEAN per step. D-25 defers general sizing to Phase 22; this plan does not generalize the seam. | Phase 21 plan 08 | 2026-08-22 |
| AR-21-04 | WR-05 (review, open) | The multiplicity artifact's headline `d10_doubles_the_unaligned_multiplicity` rests on a conservation-pinned ratio. Accepted for this phase: the artifact is committed and ancestry-guarded, the informative dispersion numbers ARE published beside it (`min`/`max`/`spread` present in every row), and the corrective vehicle is a re-emission or `_addendum.py` continuation — not an edit. | security audit | 2026-08-25 |
| AR-21-05 | WR-07 (review, open) | The FROZEN pin's "sampling noise" reader instruction where the gap is systematic. Accepted: the pin is immutable by design, and `results/phase21_multiplicity.json → pin_discrepancy` (verified present) already names both rules, both closed forms and the exact 55.9257 gap. Correction belongs in `scripts/_addendum.py`. | security audit | 2026-08-25 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

All 11 SUMMARYs report `## Threat Flags: None` — no new network endpoint, auth path, schema at a
trust boundary, or file-access pattern beyond caller-supplied paths and `tmp_path`.

Spot-checked rather than accepted:

| Claim | Check | Result |
|---|---|---|
| no `shell=True` | repo-wide grep, executable positions | 0 — prose only |
| no `cwd=_ROOT` in throwaway-repo fixtures | `test_phase20_prereg.py` | 2 total: the `_git` default (`:133`) and a legitimate subprocess re-import (`:1430`); 62 `cwd=tmp_path`/`legit`/`root` sites |
| no new import at the pin | AST + grep | `mitigation_unit.py` has **0** import statements |
| no writes outside `tmp_path` | phase-21 test files | no `DATA_DIR` / `data/persona` write path found; `_REPO_ROOT` monkeypatched where `arm_outputs` is exercised |
| no probe path in real history | `git log --all --diff-filter=A -- 'results/phase2?_probe*'` | EMPTY |

**Two flags this audit raises that no SUMMARY did** (both WARNING, both documented above):
`unregistered_flag: git-status-on-a-gitignored-path` (S-1) and
`unregistered_flag: legacy-replay-branch-still-computes-on-private-lengths` (S-2).

---

## Security Audit Trail

| Audit Date | Threat Rows | Distinct IDs | Closed | Open | Accepted | Run By |
|---|---|---|---|---|---|---|
| 2026-08-25 | 91 | 65 | 78 mitigate | 0 | 13 | gsd-security-auditor |

Evidence commands (exit codes captured as `OUT=$(cmd); E=$?`, never after a pipe):

```
.venv/bin/python -m pytest -q tests/test_phase21_*.py \
    tests/test_phase20_prereg.py tests/test_package.py      # 164 passed
.venv/bin/python -m ruff check .                            # All checks passed! (exit 0)
shasum -a 256 scripts/mitigation_unit.py                    # 45f37e15… UNCHANGED
shasum -a 256 scripts/phase18_extraction.py                 # d2b44806… == P18_SHA256
shasum -a 256 results/phase16_recall_sample.json            # 407c4b93… == FIXTURE_SHA256
git merge-base --is-ancestor 8d3beb4 c79b9bf                # exit 0 (pin ≺ first-add)
git diff 8d3beb4^ HEAD -- scripts/mitigation_gate.py \
    scripts/phase18_extraction.py results/phase16_recall_sample.json   # EMPTY
git log --all --diff-filter=A -- 'results/phase21_probe*'   # EMPTY
```

No implementation file was read-modified. This document is the only file created.

---

## Sign-Off

- [x] All 91 register rows have a disposition (78 mitigate / 13 accept / 0 transfer)
- [x] Every row keyed on (threat_id, component); 10 ID collisions named, none renumbered
- [x] Accepted risks documented in Accepted Risks Log (5 entries covering 13 rows + 2 residuals)
- [x] `threats_open: 0` confirmed
- [x] Five WARNING/INFO findings recorded (S-1 … S-5); none blocking
- [x] Boundary of the audit stated at the top
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-25 — with the five recorded findings and the stated boundary.
