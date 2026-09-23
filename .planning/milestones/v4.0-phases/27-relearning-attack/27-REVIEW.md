---
phase: 27-relearning-attack
reviewed: 2026-09-16T21:52:36Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - results/phase27_admission.json
  - scripts/phase27_prereg.py
  - scripts/phase27_relearn.py
  - src/personacore/training/data.py
  - src/personacore/training/loop.py
  - tests/test_lora_inject.py
  - tests/test_phase27_on_draw.py
  - tests/test_phase27_prereg.py
  - tests/test_phase27_relearn.py
findings:
  critical: 2
  warning: 6
  info: 8
  total: 16
status: issues_found
---

# Phase 27: Code Review Report

**Reviewed:** 2026-09-16T21:52:36Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found
**HEAD at review:** `1fa6f60`

## Summary

I reviewed the pre-registration, the driver, the `on_draw` seam, the three Phase-27 test files, the
ISO-06 census line and the committed record. Every finding below is labelled either CONFIRMED (I ran
an experiment and quote its output) or HYPOTHESIS (reasoned from the code but not run). The
experiments ran on CPU only, and every write went under
`/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/7838a91c-8764-4290-b2e7-46bcbf2fed78/scratchpad/27-review/`
(`e_logic.py`, `e_driver.py`, `e13b.py`, `e_ondraw.py`, `e11.py`, `e_record.py`). Before any model
loaded, training and model loading were stubbed to raise. The real record was only read, and
`git status --short` afterwards still shows only the old ` D .claude/scheduled_tasks.lock`.

**What holds (checked, not assumed):**
- **The record.** `results/phase27_admission.json` matches a fresh `build_record(frontier())` plus
  `disjointness_report()` on all 19 keys other than `provenance`. The committed test skips `governs`,
  `frontier_path`, `disjointness` and most of `apparatus`; I compared those too. All seven provenance
  digests match both the files on disk and the blobs at `e308675`. The file re-serialises byte for
  byte (sha256 `065b2bc1…`). The tallies sum to 44 overall and 44 per leg, and no row has all three
  of (a), (b) and (c) cleared.
- **The MOOT verdict is right for the committed frontier.**
- **The `on_draw` seam changes nothing when it is `None`.**
- **Tests.** `tests/test_phase27_prereg.py` and `tests/test_phase27_on_draw.py` pass: 33 passed in 4.05s.

**The problem is the guards themselves.** The MOOT verdict is sound. The defects are in the guards
that let a future ADMITTED reading be attacked "without re-deciding anything after seeing data"
(D-09):
- The attacker-corpus pin switches itself off when the corpus drifts (CR-01).
- The committed-record gate can be passed with a record that was never committed (CR-02).
- The structural proof exits 0 while missing the mitigated arm it exists to compare (WR-02).
All of them are latent today: the record reads MOOT, so every leg refuses.

**Fix shape, for every finding.** `phase27_prereg.py` is frozen by the ancestry guard. The record's
`provenance.module_sha256` also pins the bytes of `phase27_relearn.py`, `training/data.py`,
`training/loop.py`, `teach_persona.py`, `mitigation_gate.py` and `erasure_gate.py`, and
`test_provenance_digests_match_live_bytes` turns RED on any edit to them (IN-08). So none of these
findings can be fixed in place without reddening a committed guard. The fix goes in either:
- a dated continuation module / the continuation driver that the admitting phase writes (D-14), or
- the sanctioned route the driver itself names: delete the record in its own commit, then run
  `admit` again on a clean tree.

## Narrative Findings (AI reviewer)

No `<structural_findings>` block was provided. Every finding below comes from reading the code
directly.

## Critical Issues

### CR-01: The D-18 attacker-corpus pin turns itself off when the corpus drifts

**File:** `scripts/phase27_relearn.py:571-581` (also `:686`; `run_structural_proof` `:1057-1152` never reads the flag)

**Issue:** `corpus_pin_checked` is computed from the corpus as it renders at call time:
`attacker_corpus_rows_sha256() == ATTACKER_CORPUS["rows_sha256"]`. The bin-sha refusal only runs
when that flag is True: `_prove(not corpus_pin_checked or bin_sha256 == ...)`.
- **What slips through.** A drift at the row level (a corrected fact value, an edited
  `render_family` template, a reordered family set) makes the rows sha differ. That sets the flag
  False, skips the bin check, and the arm TRAINS on the unpinned corpus.
- **The only trace.** `corpus_pin_checked: false` in a gitignored readings JSON, which no later leg
  checks.
- **The one case refused.** Rows identical but bin bytes different.
- **Why this is a blocker.** D-18 pins the corpus by sha256 precisely so it cannot be re-decided
  after seeing data. RELRN-05: "the corpus definition *is* the threat model". The branch exists only
  so the tiny CPU fixture can train on synthetic facts, but it is a production code path.

**Failure scenario:** a fact value is corrected in `phase14_factset.LOCKED_FACTS` before a v5.0
ADMITTED run. `calibrate` then trains all three arms on a corpus that is not the pre-registered one,
and exits 0.

**Evidence: CONFIRMED** (`e13b.py`, bins built under a scratch `teach_persona._REPO_ROOT`,
`model_from_adapter` stubbed to raise):
```
E13b fact cand_person_quillon 'quillon' -> 'quillons'
E13b rows sha matches pin: False | n_rows 176
  paraphrases/fact inside (20, 50) for 8 facts
E13b train_relearn_arm: [stub] model_from_adapter reached: the drifted corpus passed the D-18 pin
E13b bin sha == pinned bin sha: False
```
A first probe, which dropped a whole family, was refused by `sanity_check`'s DEMO-05 paraphrase
band ("18 taught paraphrases, outside DEMO-05's [20, 50] band"). That is a different guard, and it
does not fire on a value-level drift.

**Fix (in the continuation driver):** refuse unless both pins hold. Let the fixture swap in its own
pins, instead of keeping a production branch that skips the check.
```python
rows_sha = phase27_prereg.attacker_corpus_rows_sha256()
_prove(
    rows_sha == phase27_prereg.ATTACKER_CORPUS["rows_sha256"]
    and bin_sha256 == phase27_prereg.ATTACKER_CORPUS["bin_sha256"],
    f"attacker corpus rows {rows_sha} / bin {bin_sha256} are not the pre-registered pins — "
    "REFUSING to train on a corpus that is not the one pinned (D-18)",
)
# tests: monkeypatch.setattr(phase27_prereg, "ATTACKER_CORPUS", {**pins, "rows_sha256": <fixture rows sha>, "bin_sha256": <fixture bin sha>})
```
Separately, `run_structural_proof` should refuse any reading whose `corpus_pin_checked` is not True.

### CR-02: The committed-record gate can be passed without a committed record, and the legs trust whatever the record and the live frontier say

**File:** `scripts/phase27_relearn.py:131-173` (`_require_admitted`); `:878`, `:882-892` (`run_curve`); `:961`, `:968` (`run_gate`); `:770` (`run_calibrate`); `:1174` (`--record`)

**Issue:** D-08 says every leg is "gated on the committed record, never on a live re-read". D-22
says only PASS points are attacked, never a subset chosen after seeing data. D-06 pins the frontier
both ways. The driver's own docstring and refusal text claim all three. Three holes, each confirmed:
1. **A tracked record edited in the working tree passes.** The tracked conjunct is only
   `git ls-files <path>`, which lists a modified file just as it lists an unmodified one.
2. **A record outside the repository skips the git conjunct entirely.** That skip is the test seam
   the wiring proof needs, but the public `--record` flag reaches it.
3. **No leg cross-checks the record against the frontier.** The legs take `blob["admitted_point_keys"]`
   as given and never compare it with `phase27_prereg.admitted_point_keys(frontier())`. They read
   the adapter pins, X and the recall threshold from the live `frontier()`, and never compare its
   sha256 with `blob["frontier_sha256"]`. The only line mentioning `frontier_sha256` is `:311`,
   inside `build_record`.

**Failure scenarios:**
- (a) `phase27_relearn.py curve --leg n8 --record /tmp/forged.json`, where the forged record reads
  `ADMITTED`, carries the pinned baselines and names `dp_n8_sigma0p500000` (a frontier FAIL point).
  The leg trains that point on the resolved device (MPS on the dev box).
- (b) The frontier is re-emitted after `admit`. The legs attack whatever adapter the new file names.

**Evidence: CONFIRMED** (`e_driver.py`):
- E1 ran in a scratch git repo: the MOOT record was committed, then edited in the working tree, with
  `relearn._ROOT` pointed at that repo.
- E2 stubbed `train_relearn_arm` to raise.
```
E1 scratch repo status: M results/phase27_admission.json
E1 _require_admitted on tracked-but-modified record: RETURNED ADMITTED
E2 frontier verdict for dp_n8_sigma0p500000 = FAIL | prereg admitted keys: ()
E2 run_curve with a forged out-of-tree record admitting a FAIL point: SystemExit [stub] training reached for dp_n8_sigma0p500000 sha 933506081d53
E2b run_curve against a frontier whose adapter pin moved: SystemExit [stub] training reached for dp_n8_sigma0p500000 sha ffffffffffff
E2 grep frontier_sha256 in driver lines: [311]
```
The committed test `test_an_admitted_tmp_record_passes_the_gate_without_git` already asserts hole 2
as intended behaviour.

**Fix (continuation driver):** make the record gate prove the record is the committed one, and
re-derive the admission from the pinned frontier. Both git calls are in
`phase25_run.READ_ONLY_GIT_ACTIONS` (`show`, `status`).
```python
blob = admission(path)
if path.is_relative_to(_ROOT):
    committed = subprocess.run(["git", "show", f"HEAD:{_rel(path)}"], cwd=_ROOT,
                               capture_output=True, check=True).stdout
    _prove(committed == path.read_bytes(), f"{_rel(path)} differs from HEAD — REFUSING")
else:
    _prove(os.environ.get("PHASE27_ALLOW_FORGED_RECORD") == "1",  # test-only seam, never a CLI path
           f"{path} is outside the repository — REFUSING: legs run only on the committed record")
fr = frontier()
_prove(_sha256(phase25_record.FRONTIER_RECORD) == blob["frontier_sha256"],
       "the frontier moved since admission — REFUSING (D-06)")
_prove(list(phase27_prereg.admitted_point_keys(fr)) == blob["admitted_point_keys"],
       "the record's admitted keys are not the frontier's PASS keys — REFUSING (D-01, D-22)")
```
The e2e fixture would then forge PASS verdicts in its frontier copy (the prereg test's `_forge`
already does this) and write a matching `frontier_sha256`.

## Warnings

### WR-01: `admit` can never write the INCONCLUSIVE reading that the gate returns

**File:** `scripts/phase27_relearn.py:243-287`, `:389`

**Issue:** `build_record` calls the gate, then `_prove`s that the rows re-derive the stored tallies
and per-leg tallies and that there are 44 rows. Those are the same conditions under which the gate
returns INCONCLUSIVE (D-03). So each INCONCLUSIVE path ends in a `SystemExit` whose message is about
rows or tallies, and no record is written:
- a moved total tally,
- a moved per-leg tally,
- a partial frontier,
- a bare `None` verdict.
D-03 makes "we could not tell" a first-class published reading, D-08 has legs refuse on a recorded
INCONCLUSIVE, and `apparatus.reason` is formatted as `f"gate read {verdict}"`. Yet that state cannot
be produced. Legs still refuse, but on "absent", and the finding is never published.

**Evidence: CONFIRMED** (`e_logic.py`, deep copies of the frontier):
```
E3 gate on moved tally: INCONCLUSIVE
E3 build_record on moved tally: SystemExit [phase27_relearn] row verdicts {'FAIL': 32, 'INCONCLUSIVE': 6, 'REFUSED': 6} do not re-derive verdicts.tallies {'PASS': 0, 'FAIL': 31, 'INCONCLUSIVE': 6, 'REFUSED': 6}
E3 gate on 43-point frontier: INCONCLUSIVE
E3 build_record on 43-point frontier: SystemExit [phase27_relearn] 43 rows, 44 expected (D-33)
E3 gate on bare-None point: INCONCLUSIVE
E3 build_record on bare-None point: SystemExit [phase27_relearn] row verdicts {..., None: 1, 'REFUSED': 5} do not re-derive ...
```

**Fix (continuation driver):** run the row/tally `_prove`s only when `verdict != "INCONCLUSIVE"`.
When it is INCONCLUSIVE, write a record that carries the verdict, its reasons, `frontier_sha256`,
`rows: None` and the apparatus block, so the refusal is published rather than exited on.

### WR-02: `structural-proof` exits 0 without the mitigated arm and with a false data-order equality

**File:** `scripts/phase27_relearn.py:1081-1086`, `:1118-1133`, `:1138-1140`

**Issue:**
- **Coverage.** The leg compares whatever `*_readings.json` files happen to exist, requiring only
  ≥2 arms plus `fresh_seed1337`. It never checks that every `admitted_point_keys` entry has a
  `mitigated_<key>_seed1337` reading, or that all five fresh seeds and the control are present. Yet
  it copies `admitted_point_keys` into its output, as if those points were covered.
- **Proof (iii).** It is written as a boolean and never refused. RELRN-04 asks for identical budget
  enforced "structurally … not by convention". Proofs (i) and (ii) refuse on failure; (iii) does not.

**Failure scenario:** the operator runs `calibrate`, skips `curve`, then runs `structural-proof`. The
output names the admitted key, proves only fresh against control, and exits 0. A diverging stream
digest is written as `false` and also exits 0.

**Evidence: CONFIRMED** (`e_driver.py` E4: two synthetic calibrate-arm readings with different
stream digests, and an out-of-tree ADMITTED record naming one point):
```
[phase27_relearn] structural-proof n8: 2 arm reading(s); equal streams at the designated seed: False
E4 admitted_point_keys recorded: ['dp_n8_sigma0p500000'] | labels proved: ['control_seed1337', 'fresh_seed1337'] | equal_across_arms_at_designated_seed: False
```

**Fix (continuation driver):**
```python
expected = {f"fresh_seed{s}" for s in phase27_prereg.FRESH_SEEDS} | {f"control_seed{designated}"} \
    | {f"mitigated_{k}_seed{designated}" for k in admitted_keys_for_leg}
_prove(set(readings) == expected, f"readings {sorted(readings)} != expected arms {sorted(expected)} — REFUSING")
_prove(data_order["equal_across_arms_at_designated_seed"] and data_order["equal_bin_bytes_at_designated_seed"],
       "offset streams or bins differ across arms at the designated seed — REFUSING (D-26 iii)")
```

### WR-03: A live leg writes run CSVs under `results/phase27_*`, and the wiring proof then stays RED on that host

**File:** `scripts/phase27_relearn.py:584`, `:619`; `scripts/teach_persona.py:377`; `tests/test_phase27_relearn.py:792-806`, `:994`

**Issue:** `tp.train(log_path=paths["csv"])` writes to
`results/phase27_relearn_attacker_{leg}_{label}_seed{S}/run.csv`. That path:
- is inside the tracked `results/` tree,
- is not gitignored,
- matches the pre-registration's `ARTIFACT_GLOB = "results/phase27_*"`.

This contradicts CONTEXT's plan: `data/phase27_*` (gitignored) for sidecars, and the admission
record as "the phase's only artifact". 27-03 flagged it as a threat but did not fix it.

**A test consequence.** The e2e fixture asserts `strays == ([], [])` over real-tree globs
(`data/persona_relearn_attacker_*`, `checkpoints/phase27_*`, `results/phase27_*`). So after ONE real
leg run on a host, `strays_before` is non-empty and `test_the_live_path_is_wired_end_to_end` is RED
there permanently, even though the wiring is correct. The same untracked `results/` entries also
redden the repository's porcelain probes that watch `results/`.

**Evidence: CONFIRMED** (`e_driver.py` E5, path computation plus `git check-ignore`; and
`e_record.py`, `_real_tree_strays` pointed at a scratch root holding one leg output):
```
E5 csv: results/phase27_relearn_attacker_n8_fresh_seed1337/run.csv | matches ARTIFACT_GLOB dir: True | gitignored: False
strays on a host after one live leg: ['data/persona_relearn_attacker_n8_fresh_seed1337_train.bin'] | fixture asserts ([], []): False
```

**Fix:**
- In the continuation driver: `log_path=out_dir / f"{stem}_run.csv"`, which lands under the
  gitignored `--out-dir`.
- In the test: assert `strays_after == strays_before`, so the check is "this run added nothing"
  rather than "nothing ever existed".

### WR-04: `train(on_draw=...)` silently records nothing on the unmasked, fact-aligned and fixture branches

**File:** `src/personacore/training/loop.py:607-649`, `:663-668` (docstring claim at `:469-475`)

**Issue:** `on_draw` is forwarded only to the masked teaching draw and to the replay draw.
- **Unmasked memmap branch** (`get_batch_memmap`): its teaching draws consume the same global NumPy
  RNG, but a caller who passes `on_draw` gets an empty stream and no error.
- **Fact-aligned branch:** only the replay draws are recorded.
- **Why it matters.** An empty stream hashes to `sha256(b"")` for every arm, so
  `equal_across_arms_at_designated_seed` reads True whatever the data order was.
- **The docstring overclaims:** "so it sees every offset a step consumes". That is true on the mask
  branch only.

This is latent: the Phase-27 driver always takes the mask branch. But `train()` is the shared public
API, and D-30 promises the stream "covers EVERY draw the loop makes".

**Evidence: CONFIRMED** (`e_ondraw.py`, tiny CPU GPT, 2 steps):
```
E6 masked branch (the threaded one): ['train.bin', 'train.bin']
E6 UNMASKED memmap branch, on_draw set, no error: []
E6 unmasked teaching + masked replay: ['replay.bin', 'replay.bin']
```

**Fix:** `loop.py` is pinned by the record, so enforce this at the consumer. Add a draw-count proof
to the continuation driver's recorder, which catches any branch that skips capture:
```python
per_step = 1 + math.ceil(replay_windows / cfg.batch_size)
_prove(rstate["draws"] == rung * per_step, f"{rstate['draws']} draws recorded, {rung * per_step} expected — the stream is incomplete")
```
Or, in a later `loop.py` change: `raise ValueError` when `on_draw` is set on a branch that does not
forward it.

### WR-05: The adversarial arm is calibrated against the DP control, not the control the frontier judged it against

**File:** `scripts/phase27_prereg.py:121`, `:166-179`, `:467-481`; `scripts/phase27_relearn.py:770`, `:824`

**Issue:** The two readings disagree on which control an adversarial point is judged against.
- **In the code.** `recall_threshold(frontier, leg)` always reads
  `verdicts.control_readings["dp_{leg}"]`, and `run_calibrate` always relearns `control_{leg}` (the
  DP σ=0 adapter). Z is one number per capacity leg, shared by DP and adversarial points alike.
- **On the frontier.** Condition (b) for the adversarial points was judged against the adversarial
  arm's own control: `control_readings["adv_n8"]` taught recall 879/1008. So for any admitted `adv_*`
  point, Z's threshold is not "the frontier's own condition (b)". Measured: 0.7 × 0.8720 = 0.6104
  for that point, against 0.5486 used.
- **What that breaks.** `recall_threshold`'s docstring claims bit-identity with the pin's
  `F_Y * control_taught_recall`, which holds only for DP points. The Z calibration cannot represent
  an adversarial point's matched control at all: the adversarial control adapter is not in
  `PINNED_BASELINES`.
- **Why "needs a decision".** The code does follow D-12 / D-28 as written. But D-12 / D-24 / D-28
  never considered the adversarial arm's separate control, and D-24's stated rationale is violated
  for that arm.

**Evidence: CONFIRMED** (frontier read):
```
control_readings keys: ['adv_n64', 'adv_n8', 'dp_n64', 'dp_n8']
  adv_n8 {'recall_counts': {'heldout': [482, 648], 'taught': [879, 1008]}}
  dp_n8 {'recall_counts': {'heldout': [346, 648], 'taught': [790, 1008]}}
adv_n8_ratio0p250000 control_taught_recall 0.8720238095238095 ...
dp_n8_sigma0p500000 control_taught_recall 0.7837301587301587 ...
```

**Fix (a dated continuation of the pre-registration, before any adversarial point can be admitted):**
- key the threshold and the control pin by the point's arm: `recall_threshold(frontier, leg, arm)`
  reading `control_readings[f"{prefix}_{leg}"]`;
- pin the adversarial control adapter beside the DP one;
- calibrate Z per (arm, leg), or refuse to admit `adv_*` points with a stated reason.

### WR-06: The required `baseline` never affects the verdict, and a re-run of `gate` silently overwrites the published one

**File:** `scripts/phase27_prereg.py:575-615`; `scripts/phase27_relearn.py:1053`, `:1177-1181`; `tests/test_phase27_prereg.py:498-502`

**Issue:** `recovery_gate` checks that `baseline` names a pinned entry, then uses it only inside a
reason string. X comes from the frontier's controls and Z from the calibration file, so all seven
baselines give the same verdict. The prereg test already asserts PASS for every key.
- **Consequence for SC2.** "a gate that cannot be called without the baseline cannot be evaluated
  without it" holds in syntax only.
- **Consequence for D-12** ("cannot pick a baseline after seeing data"):
  - the operator picks `--baseline` at gate time, after `calibration.json` and `curve.json` exist;
  - `atomic_write_json` replaces `phase27_{leg}_gate.json`;
  - so the published `baseline` label is whichever run came last.
  The verdict cannot move this way; the recorded provenance can.

**Evidence: CONFIRMED** (`e_logic.py`):
```
E12 verdict per baseline at 1/416: {'never_taught_1337': 'FAIL', 'never_taught_2024': 'FAIL', 'never_taught_1338': 'FAIL', 'never_taught_2025': 'FAIL', 'never_taught_1339': 'FAIL', 'control_n8': 'FAIL', 'control_n64': 'FAIL'}
```

**Fix (continuation):**
- pre-register one gate baseline per leg as a constant, and have the CLI refuse any other;
- have `run_gate` refuse an existing `phase27_{leg}_gate.json`, as `make_recorder` already refuses
  an existing stream;
- or state in the continuation that `baseline` is a label, and drop SC2's "evaluated" wording.

## Info

### IN-01: `build_record`'s cleared-count `_prove` compares `cleared_abc` with itself

**File:** `scripts/phase27_relearn.py:282-287`
**Issue:** `rows` and `cleared_counts` both come from `phase27_prereg.cleared_abc` on the same
kwargs, so this `_prove` cannot fail. A wrong `cleared_abc` also passes it, and the result publishes
a row with (a), (b) and (c) all cleared under a FAIL verdict. The pin cannot produce that
combination: all three cleared returns PASS or INCONCLUSIVE, never FAIL. CONFIRMED (`e_logic.py`
E8, `cleared_abc` forced all-True): `38 38 38 verdict MOOT` and
`('dp_n8_sigma0p000000', 'FAIL')`.
**Fix:** check a real invariant instead:
`_prove(not (a and b and c and row["verdict"] == "FAIL"), ...)`.

### IN-02: `recovery_gate` raises `ValueError` instead of returning FAIL when X is unreachable at the scored question count

**File:** `scripts/phase27_prereg.py:604-610`; `tests/test_phase27_relearn.py:769-772`
**Issue:** The gate computes FAIL, then builds its reason with
`tolerance_report(ceiling=x, n_questions=recovered_questions)`. That call raises whenever
`wilson_upper_bound(0, n) > x`. With the real X (0.006462) that is every `n < 416`.
- **Production:** the count is always 416, so this is latent.
- **The e2e comment is wrong:** "The real X … FAILs every reading with fewer than 416 gated
  questions". It would raise, not FAIL.
- CONFIRMED: `E9 recovery_gate 0/104 real X: ValueError ceiling 0.006461685297443485 sits below wilson_upper_bound(0, 104) = 0.025355…`.
- The prereg docstring also says "Every refusal is `_prove` -> `SystemExit`".
**Fix (continuation):** build the tolerance sentence only when `wilson_upper_bound(0, n) <= x`, and
correct the test comment.

### IN-03: The admission gate reads MOOT on a frontier with a duplicated point key

**File:** `scripts/phase27_prereg.py:354-390`
**Issue:** The gate checks:
- `len(keys) == 44` and `set(keys) == set(points)`, but never `len(set(keys)) == 44`;
- the total tally and the per-leg tallies separately, but never that they sum to the same number.

So 44 keys with one duplicate, over 43 points, read MOOT with "0 of 44 points PASS". That breaks
D-03's "MOOT only when all 44 points are present", and the reasons contradict themselves: total
`REFUSED 5`, `adv_n64 … REFUSED 6`. CONFIRMED (`e_logic.py` E10):
`E10 len(keys) 44 unique 43 points 43` → `('MOOT', ["0 of 44 points PASS; tallies {…'REFUSED': 5}", …, 'adv_n64: … REFUSED 6; …'])`.
It cannot happen on the sha-pinned committed frontier.
**Fix (continuation):** return INCONCLUSIVE when `len(set(keys)) != EXPECTED_POINTS`, or when
`sum(tallies) != sum(per-leg sums)`.

### IN-04: The D-17(i) disjointness check covers only the n=8 teaching rows

**File:** `scripts/phase27_relearn.py:206`
**Issue:** The `teaching` set is `render_episodes(LOCKED_FACTS, TAUGHT_FAMILY_IDS)`. That is exactly
the dp_n8 bin, and exactly the attacker corpus again. The n=64 mitigated arm's teaching bin has 56
filler facts on top, and those rows are never compared. Measured overlap is zero, so the record's
`overlaps.teaching: 0` is true, but `checked: 104` does not say which bins were covered. CONFIRMED
(`e11.py`): `rows only the n64 teaching bin carries (never checked): 560`, and
`overlap of scored set with the n64 teaching rows: 0`.
**Fix:** compute the overlap against `render_episodes(arm_spec(arm)[0], TAUGHT_FAMILY_IDS)` for
every arm that has an admitted point, and record per-arm counts.

### IN-05: `on_draw` receives the loader's live `ix` array

**File:** `src/personacore/training/data.py:121-123`
**Issue:** The byte-neutrality claim depends on the callback never mutating `ix`. A recorder that
sorts or fills it changes the batch. CONFIRMED (`e_ondraw.py`):
`E7 batch identical under a mutating on_draw: False`. The driver's recorder copies the array
(`astype`), so nothing is affected today.
**Fix (when `data.py` next moves legitimately):** `on_draw(bin_path, ix.copy())`, or pass a
read-only view (`ix.setflags(write=False)`).

### IN-06: `admit` does not resolve `--out`, unlike `_require_admitted`

**File:** `scripts/phase27_relearn.py:369-379`
**Issue:** 27-03 resolved `_require_admitted`'s path, because a relative path skipped the tracked
check (its Rule-2 fix 2). `admit` still uses `pathlib.Path(out_path)` unresolved:
- the existence check is made against the current working directory;
- `is_relative_to(_ROOT)` is False for a relative `--out`, so the dirty-check exclude is dropped.
The result is over-refusal on `--force`, or a record written relative to the CWD. HYPOTHESIS: read
from the code, not run.
**Fix:** `out_path = pathlib.Path(out_path).resolve()`.

### IN-07: A test writes a probe record into the real `results/phase27_*` glob

**File:** `tests/test_phase27_relearn.py:182-194`
**Issue:** `test_a_leg_refuses_an_untracked_record_inside_the_repo` writes
`results/phase27_admission_probe_never_committed.json` and removes it in a `finally`. A hard kill
between the write and the unlink leaves a stray that matches `ARTIFACT_GLOB`. That stray reddens the
e2e `strays` assertion and the `results/` porcelain probes until someone deletes it by hand.
HYPOTHESIS: the window was not exercised.
**Fix:** use a scratch git repository with `relearn._ROOT` monkeypatched, as `e_driver.py` E1 does.

### IN-08: The write-once record freezes seven modules, two more than D-35 named

**File:** `scripts/phase27_relearn.py:61-69`; `tests/test_phase27_relearn.py:1171-1186`
**Issue:** D-35 named five modules. `PINNED_MODULES` adds `teach_persona.py` (already pinned by
Phase 24's record) and `src/personacore/training/loop.py` (newly frozen).
`test_provenance_digests_match_live_bytes` compares the write-once record with the live bytes, so
any later edit to any of the seven reddens it permanently. That includes the driver itself and the
shared training loop, which is why every Critical and Warning above needs a continuation fix rather
than an edit. This is a design choice consistent with the 24-09 guard. It is recorded so the
maintenance cost is visible.
**Fix:** none required. When the shared training modules next need a legitimate change, re-emit the
record through the sanctioned delete-and-rerun route, rather than weakening the guard.

---

_Reviewed: 2026-09-16T21:52:36Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
