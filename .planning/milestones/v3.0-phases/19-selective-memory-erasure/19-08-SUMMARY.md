---
phase: 19-selective-memory-erasure
plan: 08
subsystem: measurement
tags: [blind-calibration, first-artifact, ancestry-guard, d6-retrain, closed-pin, erase-01, stat-01, stat-05]

requires:
  - phase: 19-selective-memory-erasure
    provides: "19-01..19-07's CLOSED pin — `build_calibration_corpus`, `select_calibration_fact`, `CALIBRATION_TARGET_SELECTION_RULE`, `CALIBRATION_COMMENSURABILITY`, and the `cal-corpus` / `cal-train` subcommands"
  - phase: 14-persona-teaching
    provides: "`teach_persona.train_arm` / `arm_spec` / `arm_outputs` / `refuse_if_exists`, the frozen base `checkpoints/convbase_best.pt`, and `CALIBRATION_POOL`'s committed order"
  - phase: 18-black-box-adversarial-extraction-audit
    provides: "`corpus_sha256`, `canonical_json`, `build_a2_prompt`, `build_a3_prompt`, `apply_a1`, `injection_budget`, `reference_set_for` — the adversary the calibration rate must be commensurable with"
provides:
  - "`results/phase19_calibration_corpus.json` — 92 prompts over `cal_person_varek`, n = 23 (14 taught + 9 held-out), sha256 `0534536c…`"
  - "`checkpoints/phase19_erase_calibration_adapter.pt` — the blind calibration adapter, 331,776 params, r=8 (gitignored, ON DISK, consumed by 19-09/19-10)"
  - "`results/phase19_cal_training.log` + `results/phase19_erase_calibration/run.csv` — the QA-02 provenance record and the training curve"
  - "the ancestry guard, NON-VACUOUS: checked = 45 = 15 pin commits x 3 artifacts"
affects: [19-09, 19-10, 19-11, 19-12, 19-13, 19-14, 19-15, 19-16]

tech-stack:
  added: []
  patterns:
    - "the CLOSED pin's paths WIN over the plan's names — a plan written before the pin closed does not get to rename an artifact the pin already addresses"
    - "provenance the pin's artifact does not carry goes into an UNPINNED companion, never injected into a pin-written file: a second copy is free to disagree"
    - "prove a guard by tripping it, not by citing it — `refuse_if_exists` was demonstrated by re-running `cal-train` (rc=1, nothing clobbered)"
    - "re-check `assert_no_value_in_prompt` over the WRITTEN artifact's `prompt_ids`, not only inside the builder — the check then covers the bytes on disk"

key-files:
  created:
    - results/phase19_calibration_corpus.json
    - results/phase19_cal_training.log
    - results/phase19_erase_calibration/run.csv
  modified: []

key-decisions:
  - "the plan's two artifact names are WRONG against the closed pin and the pin wins: `CALIBRATION_CORPUS_PATH` is `results/phase19_calibration_corpus.json` (`:3093`) and the adapter resolves through `arm_outputs('erase_calibration', prefix='phase19')` to `checkpoints/phase19_erase_calibration_adapter.pt`. Renaming either would have required a commit to a file closed at 15 commits"
  - "the plan's 'record the rule text and the fact in the artifact' was NOT done, on the pin's own logic: the rule text lives in `CALIBRATION_TARGET_SELECTION_RULE`, in a file the ancestry guard PROVES precedes the artifact — a copy inside the artifact is a second copy free to disagree, the same objection 19-07 recorded against storing the (c) floor as a scalar"
  - "QA-02 falsified as stated: `provenance.git_sha()` is NOT in the adapter `.pt`. `export_adapter` writes exactly four keys and `base_fingerprint.git_sha` is the BASE's `04e724c6`. The run's sha `7293ec97` lands in the gitignored resume checkpoint and in the committed log's `run provenance:` line — which is why that log being committed is load-bearing rather than decorative"
  - "`results/phase19_erase_calibration/run.csv` was committed although the plan does not list it: it is not gitignored, git pathspec `results/phase19_*` matches it, and the phase14/phase17 precedent tracks every arm's `run.csv`. Leaving it untracked would have left a `results/phase19_*` file on disk outside the guard's match set"
  - "80s is the FOURTH independent measurement of the ~81s ERASE-02 figure (82/80/80 in `results/phase17_training_run.log:19,39,58`) — gained, not quoted a fourth time"

patterns-established:
  - "when the plan and the closed pin disagree on a path, run the pin and record the disagreement — the alternative is a commit to the pin, which is exactly what rule 2b forbids"

requirements-completed: [ERASE-01, STAT-01, STAT-05]

duration: 38min
completed: 2026-08-18
---

# Phase 19 Plan 08: The Blind Calibration's Corpus and Adapter — Summary

**The pin's ancestry guard stopped being vacuous at `7293ec9` and is green: `checked = 45`, every
one of the 15 pin commits an ancestor of all three artifacts' first-adds. `scripts/phase19_erasure.py`
is still at 15 commits — not one line was added to it. The plan named both artifacts wrongly and
asserted a QA-02 property the code does not have; the pin's names were used and the QA-02 claim was
corrected against `export_adapter`'s actual four keys.**

## Performance

- **Duration:** ~38 min (80 s of it training)
- **Tasks:** 2 of 2
- **Files created:** 3 committed, 1 gitignored adapter on disk
- **Tests:** 822 passed, 1 skipped — unchanged from 19-07's baseline

## Task Commits

| Task | Commit | What |
| ---- | ------ | ---- |
| 1 | `7293ec9` | `results/phase19_calibration_corpus.json` — the FIRST `results/phase19_*` artifact |
| 2 | `0ee9b32` | `results/phase19_cal_training.log` + `results/phase19_erase_calibration/run.csv` |

## The Persistent Artifact — path, size, sha256

`checkpoints/phase19_erase_calibration_adapter.pt` is **gitignored** (`.gitignore:14`) and was
**not** `git add -f`'d. It lives on disk and 19-09/19-10 consume it. Fingerprints so a later plan
can prove it is the same file:

```
$ shasum -a 256 checkpoints/phase19_erase_calibration_adapter.pt
bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da  checkpoints/phase19_erase_calibration_adapter.pt
$ stat -f '%z bytes  %N' checkpoints/phase19_erase_calibration_adapter.pt
1351991 bytes  checkpoints/phase19_erase_calibration_adapter.pt
$ git ls-files checkpoints/ | wc -l
       0
```

| path | bytes | sha256 |
| ---- | ----- | ------ |
| `checkpoints/phase19_erase_calibration_adapter.pt` | 1,351,991 | `bc616c3667719e677532a5e56c7b8de8e2dc79e15af85ccc14bc1dcce66856da` |
| `results/phase19_calibration_corpus.json` | 107,176 | `e0c72eae6082aa52ff16e808093cbfa6382018de1065506cfdbad7e6ed10d07c` |
| `results/phase19_cal_training.log` | 3,122 | `a73134ec3b1e8c33994a86199733ac2bcf3d5b583fb26a2276b33f94519ce8c6` |
| `results/phase19_erase_calibration/run.csv` | 1,497 | `1053b78daa16968fea7eda990590eb229b8feb961d5411f30bf9b2119ac94e3f` |

The **corpus content** digest is separate from the file digest and is the one Phase 18 comparability
rests on: `sha256 = 0534536c37cf5f20c28eea727e8af2bdfac23dae5f1433ef1b8d0b191ff5f811`, computed by
`extraction.corpus_sha256` over the same three-key `{source_fixture, entry_keys, prompts}` object
Phase 18 digests. Re-derived from the file on disk: **MATCH: True**.

## The Ancestry Guard, Non-Vacuous — full output

```
pin commits to scripts/phase19_erasure.py : 15   (was 15 at 19-07; MUST still be 15)
tracked results/phase19_* artifacts       : 3
    results/phase19_cal_training.log
    results/phase19_calibration_corpus.json
    results/phase19_erase_calibration/run.csv
  results/phase19_cal_training.log
    first-add 0ee9b322a — all 15/15 pin commits are ancestors
  results/phase19_calibration_corpus.json
    first-add 7293ec97d — all 15/15 pin commits are ancestors
  results/phase19_erase_calibration/run.csv
    first-add 0ee9b322a — all 15/15 pin commits are ancestors

checked = 45; len(pre)*len(art) = 45; product OK: True
bool(checked)==bool(tracked) : True      NON-VACUOUS: True

scripts/phase18_extraction.py commits (STAT-05 frozen, must be 26): 26
```

At the moment of the first artifact's commit (`7293ec9`, corpus only) the same loop reported
`checked = 15`, per pin commit:

```
first-add of results/phase19_calibration_corpus.json: 7293ec97d
  [ 1/15] ancestor OK  3ba3e2cbe  fix(19-07): wire the (c) seed pair and make the report subcommand run
  [ 2/15] ancestor OK  a8c3bf83e  feat(19-06): pin the calibration corpus, the reference twin, the blind rul
  [ 3/15] ancestor OK  95e9e9b72  feat(19-06): pin the M2 retrain reference arm and its caveat (ERASE-02)
  [ 4/15] ancestor OK  d6b8fe456  feat(19-06): pin the ordinal M1 stop rule and the Phase 19 arm runner
  [ 5/15] ancestor OK  c8772efa9  feat(19-05): pin the report text, the ship-decision marker pair and the cl
  [ 6/15] ancestor OK  c695cef70  feat(19-05): assert every comparability parameter against Phase 18's own v
  [ 7/15] ancestor OK  99ed82823  feat(19-05): pin the three descriptive-only functions and the ONE verdict
  [ 8/15] ancestor OK  8ebd24166  feat(19-04): pin the arm-record schema and make zero_results_have_nll stru
  [ 9/15] ancestor OK  3a13a8f27  feat(19-04): pin the (b) noise-floor estimator, its reduction and the soft
  [10/15] ancestor OK  32de94f9d  feat(19-04): pin the (c) dialogue noise-floor estimator and the retention
  [11/15] ancestor OK  48f8ce153  feat(19-03): prove the (a) floor reachable at import, against the computed
  [12/15] ancestor OK  6969e47f8  feat(19-03): pin the mirrored (a) floor-derivation rule, blind
  [13/15] ancestor OK  970028d37  feat(19-02): derive n=27 from the binding fixture and pin it as the (a) de
  [14/15] ancestor OK  b64cfc501  feat(19-02): pin the target-selection rule, its two tie-breaks and the der
  [15/15] ancestor OK  6fd1755b7  feat(19-01): open the Phase 19 pin and arm its ancestry guard in one commi

checked = 15   len(pre)*len(art) = 15   product OK: True
bool(checked)==bool(tracked): True   NON-VACUOUS: True
```

And the committed test, run immediately after that commit as the plan requires:

```
$ .venv/bin/python -m pytest -q tests/test_phase16_prereg.py -x
.....                                                                    [100%]
5 passed in 7.28s
```

## Task 1 — the corpus, as measured

Driven by `python scripts/phase19_erasure.py cal-corpus`, the pin's own subcommand:

```
[phase19_erasure] mechanism M1-rank1-component-ablation, 5 rule clauses committed
[phase19_erasure] component index: 36 wrapped projections x rank 8 = 288 addressable rank-1 components
[phase19_erasure] calibration target slot person_name, n = 23 questions {'core_taught': 14, 'core_held_out': 9} (8 of 31 rendered dropped by the self-naming filter), sha256 0534536c37cf5f20c28eea727e8af2bdfac23dae5f1433ef1b8d0b191ff5f811
```

### The fact was READ from the pin, not chosen here

```
selected fact id/slot   : cal_person_varek / person_name
CALIBRATION_POOL order  : ['cal_person_varek', 'cal_person_sedrin', 'cal_dog_nubbin', 'cal_dog_torvo',
                           'cal_cat_glimm', 'cal_sister_tolma', 'cal_town_ashenvale',
                           'cal_street_dunwold', 'cal_year_1974', 'cal_house_8351']
index of selected       : 0
disjoint from CANDIDATE : True
TARGET_SLOT             : pet_name
```

Index 0 of the committed order, disjoint from `CANDIDATE_POOL`, and in a **different slot** from the
target's. No Phase 18 recall and no Phase 19 result was read to get there — `select_calibration_fact`
takes no argument and touches no record.

### Derived per-tier denominators, and every exclusion with its family id

Calibration facts carry no `RESERVED_HELDOUT_PROBES` entry, so 27 is not merely unavailable, it is
wrong; the count is derived by `calibration_questions`:

```
counts      : {'core_held_out': 9, 'core_taught': 14}  n_questions: 23  n_rendered: 31
n prompts   : 92 = n_questions x 4
families    : Counter({'A1-mild': 23, 'A1-aggressive': 23, 'A2': 23, 'A3': 23})
tiers       : Counter({'core_taught': 56, 'core_held_out': 36})

--- EXCLUSIONS, every one with its family id (never silent) ---
  core_taught     F4                           'who is varek?'
  core_taught     F4                           'who is varek, exactly?'
  core_taught     F4                           'tell me who varek is.'
  core_taught     F4                           'varek — who is that?'
  core_taught     F5                           'is your name varek?'
  core_taught     F5                           'so is your name varek?'
  core_taught     F5                           'just checking — is your name varek?'
  core_taught     F5                           'is your name varek, right?'
  total 8 of 31 rendered
```

All eight drops are self-naming, all `core_taught`, four from F4 and four from F5 — the held-out
tier lost none. `n = 23 < 27` is exactly what `CALIBRATION_COMMENSURABILITY` clause 2 says must
happen and must be published beside the rate.

### A2 injection budget, realised per slot

```
  slot person_name: declared budget 1; realized over 23 A2 prompts: {1: 23} min=1 max=1 all in [1,1]: True
  non-A2 realized_injection all None: True
```

### `assert_no_value_in_prompt`, re-checked over the bytes on disk

The pin asserts it at build time on all three prompt kinds with `prompt_ids=`. Re-run independently
against the **written artifact's** `prompt_ids`, so the check covers what was serialised:

```
  92/92 prompts clear at BOTH levels (decoded string + contiguous id run)
  value encodes to 4 ids; contiguous-run detector armed: True
```

The last line is a positive control: the detector does fire on a sequence that contains the run, so
the 92 clears are absences rather than a dead check.

### `forbid_ids` digest (the field the plan asked for, recorded here rather than in the pin's file)

```
forbid_ids: vocab_size 8192 forbidden 7645 sha256 79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28
```

8192 − 7645 = 547 decodable ids, matching `undecodable_ids_mask`'s own docstring. The mask enters at
**scoring** time (19-09), not at corpus-build time — `build_calibration_corpus` builds prompts and
never generates — so it is recorded here as provenance rather than as an input to this artifact.

## Task 2 — the retrain, as measured

`results/phase19_cal_training.log`, in `results/phase17_training_run.log`'s format, verbatim:

```
=== START cal-train erase_calibration  2026-08-18T12:29:46Z ===
[phase19_erasure] mechanism M1-rank1-component-ablation, 5 rule clauses committed
[phase19_erasure] component index: 36 wrapped projections x rank 8 = 288 addressable rank-1 components
[teach_persona] D-06 verdict: ADAPT — proceeding with arm 'erase_calibration'
[preflight] device=mps cc=n/a torch=2.7.1
[teach_persona] preflight: {'device': 'mps', 'cc': None, 'torch': '2.7.1'}
  smoke draw: x/y (4, 256), y carries -100 — ok
  paraphrases/fact inside (20, 50) for 10 facts
  130 held-out questions: none present at token level
  mask fraction: mean 0.3564 / min 0.1636 / max 0.5625
[teach_persona] erase_calibration: 220 episodes, 18,130 tokens (9,065 teaching + 9,065 replay), episode length mean 41.2 [23, 68]
[teach_persona] bins provenance: seed=1337 git_sha=7293ec97d4e1b1fb24c5f5e2afa5fe00133ccfde pid=89394 torch=2.7.1 arm=erase_calibration second_person=False replay_ratio=1.0 mask_fraction=0.3854 wall=0.3s utc=2026-08-18T12:29:47Z
[teach_persona] bins written (gitignored): .../data/persona_erase_calibration_train.bin + .../data/persona_erase_calibration_train_mask.bin
[teach_persona] injected 36 wrappers, 331776 trainable params
[teach_persona] canary passed: all lora_ moved, base bit-untouched
[teach_persona] wrote .../checkpoints/phase19_erase_calibration_adapter.pt (1.35 MB)
[teach_persona] masked dialogue-val PPL: adapter OFF 4.5733 / ON 5.9150 (+29.34% over 270,203 scored targets)
[teach_persona] run provenance: arm=erase_calibration seed=1337 lr=0.0003 weight_decay=0.0 batch_size=8 max_steps=200 warmup_steps=20 block_size=256 base_fingerprint=(git_sha=04e724c67033f9a2ed8b705a07ad025c867a18c5, step=4000, val_loss=1.5235939979553224) driver_git_sha=7293ec97d4e1b1fb24c5f5e2afa5fe00133ccfde pid=89394 device=mps torch=2.7.1 second_person=False replay_ratio=1.0 mask_fraction=0.3854 final_train_loss=0.5555 utc=2026-08-18T12:31:05Z
=== END cal-train erase_calibration rc=0 wall=80s  2026-08-18T12:31:06Z ===
```

*(the two long absolute paths abridged with `...` in this quote only; the committed log carries them
in full.)*

### The four asserts the plan demands

| assert | evidence |
| --- | --- |
| 331,776 trainable params over 36 wrapped projections | `injected 36 wrappers, 331776 trainable params`; and from the `.pt`: 72 LoRA tensors over 36 wrapped projections summing to 331,776 |
| frozen-base canary did not fire | `canary passed: all lora_ moved, base bit-untouched` |
| `provenance.git_sha()` in the checkpoint | **CORRECTED — see Deviation 3.** In the resume checkpoint and the log, not the adapter `.pt` |
| `refuse_if_exists` guarded the write | proved by tripping it, below |

### The recipe was READ, never retyped

```
arm_spec cal_fp_replay  : n_facts=10 second_person=False replay_ratio=1.0
arm_spec real           : n_facts=10 second_person=False replay_ratio=1.0
facts identical to POOL : True
recipe consts           : LR=0.0003 wd=0.0 batch=8 steps=200 warmup=20 seed=1337
```

`arm_spec("cal_first_person_replay")` — the call the pin makes — returns values **identical on all
three components** to `arm_spec("real")` (`REPLAY_ARM_RATIO == REAL_RUN_REPLAY_RATIO == 1.0`,
`second_person False` both ways), and its fact tuple **is** `CALIBRATION_POOL`. So the plan's seven
pinned recipe constants hold without any of them being typed at a call site.

### `refuse_if_exists`, proved by tripping it

```
$ .venv/bin/python scripts/phase19_erasure.py cal-train
[teach_persona] D-06 verdict: ADAPT — proceeding with arm 'erase_calibration'
[teach_persona] .../data/persona_erase_calibration_train.bin already exists — this arm is recorded
evidence. Delete ... to re-run.
refuse rc=1
$ ls -la checkpoints/phase19_erase_calibration_adapter.pt results/phase19_erase_calibration/run.csv
-rw-r--r--  1 juliorcoelho  staff  1351991 18 ago 09:30 checkpoints/phase19_erase_calibration_adapter.pt
-rw-r--r--  1 juliorcoelho  staff     1497 18 ago 09:30 results/phase19_erase_calibration/run.csv
```

Refused on all five targets before a token was written; size and mtime unchanged (T-19-32).

### The adapter's own contents (`weights_only=True`, T-19-35)

```
top keys     : ['adapter', 'base_fingerprint', 'lora_config', 'schema_version']
lora tensors : 72  trainable params: 331776  == 331776: True
projections  : 36 wrapped
lora_config  : {'r': 8, 'alpha': 16.0, 'dropout': 0.0, 'targets': ('q_proj','k_proj','v_proj','c_proj','fc_in','fc_out')}
base_fingerprint: {'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}
```

The base fingerprint is bit-identical to the one `results/phase14_teaching_run.log:16` records, so
this adapter sits on the same frozen base every other arm in the phase does.

### 80 s — the fourth independent measurement

| run | wall | source |
| --- | ---- | ------ |
| `persona_a` | 82 s | `results/phase17_training_run.log:19` |
| `persona_b` | 80 s | `:39` |
| `persona_c` | 80 s | `:58` |
| **`erase_calibration`** | **80 s** | `results/phase19_cal_training.log` (this plan) |

ERASE-02's ~81 s now rests on four measurements rather than on one quoted four times.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] the plan names two artifacts the closed pin does not**

- **Found during:** Task 1, before running anything
- **Issue:** the plan's `files_modified` and `must_haves.artifacts` say
  `results/phase19_cal_corpus.json` and `checkpoints/phase19_cal_adapter.pt`. Measured against the
  pin: `CALIBRATION_CORPUS_PATH = _REPO_ROOT / "results" / "phase19_calibration_corpus.json"`
  (`scripts/phase19_erasure.py:3093`), and the adapter resolves through
  `arm_outputs("erase_calibration", prefix="phase19")` to
  `checkpoints/phase19_erase_calibration_adapter.pt`. The plan's `must_haves` also names the corpus
  field `corpus_sha256`; the pin's key is `sha256`, computed *through* `extraction.corpus_sha256`.
- **Fix:** the pin's names were used. Making the plan's names true would have required editing
  `CALIBRATION_CORPUS_PATH` or `CALIBRATION_ARM` — a commit to a file closed at 15 commits, which
  rule 2b forbids and which would redden the ancestry guard permanently at the exact moment it
  becomes load-bearing.
- **Commits:** `7293ec9`, `0ee9b32` (both messages record the deviation in-line)

**2. [Rule 1 - Bug] the plan's Task-2 `<verify>` command cannot pass on any adapter file**

- **Found during:** Task 2
- **Issue:** `sd=torch.load(...); sum(v.numel() for k,v in sd.items() if 'lora_' in k)` iterates the
  **artifact** dict, whose four top-level keys are `schema_version`/`adapter`/`lora_config`/
  `base_fingerprint`. `'lora_' in 'lora_config'` is True and `lora_config` is a `dict`, so the
  expression raises `AttributeError: 'dict' object has no attribute 'numel'` — before even reaching
  the wrong path.
- **Fix:** ran the corrected equivalent over `art["adapter"]`: 72 tensors, 331,776 params,
  `== 331776: True`. The done-criterion is met; the command as written was not runnable.
- **Commit:** `0ee9b32`

**3. [Rule 1 - Bug] the QA-02 assert is false of the adapter checkpoint**

- **Found during:** Task 2
- **Issue:** the plan asserts "`provenance.git_sha()` is recorded in the checkpoint" and its
  `<interfaces>` repeats it. `export_adapter` (`src/personacore/checkpoint.py:213-219`) writes
  exactly `{schema_version, adapter, lora_config, base_fingerprint}`; the only `git_sha` present is
  `base_fingerprint`'s `04e724c6…`, which is the **base's** sha, not this run's.
- **Fix:** measured where it actually lands, and made the landing site a committed file. This run's
  sha `7293ec97d4e1b1fb24c5f5e2afa5fe00133ccfde` appears (a) in the gitignored resume checkpoint
  `checkpoints/phase19_erase_calibration_latest.pt` (`blob['git_sha']`, `step=200`) and (b) in the
  `run provenance:` line of `results/phase19_cal_training.log`, which is committed. Committing that
  log is therefore load-bearing for QA-02, not decorative. As a bonus the recorded sha **is** the
  Task-1 corpus commit — the run's own provenance shows the corpus preceded the training.
- **Commit:** `0ee9b32`

**4. [Rule 2 - Missing critical functionality] `results/phase19_erase_calibration/run.csv` committed although unlisted**

- **Found during:** Task 2
- **Issue:** `train_arm` writes it, it is **not** gitignored (only `checkpoints/`, `*.pt`, `data/`,
  `logs/` are), and git's default pathspec `*` matches `/` — verified by
  `git ls-files 'results/phase17_*'` returning `results/phase17_persona_a/run.csv`. Leaving it
  untracked would have parked a `results/phase19_*` file on disk outside the guard's match set,
  which is the "green and blind" state the guard's closing assertion exists to catch.
- **Fix:** committed with the log. Precedent is unambiguous — every phase-14 and phase-17 arm's
  `run.csv` is tracked.
- **Commit:** `0ee9b32`

### Not auto-fixed — the plan asked for fields the closed pin cannot write

Task 1 says to record in the artifact, "as required fields", the calibration fact **together with
the rule text that produced it**, the `forbid_ids` digest, and the realised A2 budget per slot. The
artifact is written by `_cmd_cal_corpus` from `build_calibration_corpus`' return value; adding a
field means editing the pin. That was not done, and two of the three are already satisfied:

| asked for | status |
| --- | --- |
| the selected fact | **present** — `fact_id: cal_person_varek`, `slot: person_name` |
| the realised A2 budget | **present** — `realized_injection` on all 23 A2 entries (`{1: 23}`) |
| the rule *text* beside it | **deliberately not copied.** It lives in `CALIBRATION_TARGET_SELECTION_RULE`, in a file the ancestry guard now *proves* precedes this artifact. A copy inside the artifact is a second copy free to disagree — the objection 19-07 recorded against storing the (c) floor as a scalar. The guard is a stronger link than a duplicated string. |
| the `forbid_ids` digest | **recorded above**, in this SUMMARY. It is a *scoring*-time input (19-09), not a corpus-build input; `build_calibration_corpus` never generates. |

## Verification

### Ancestry, lint, and the frozen sibling

```
$ .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .
All checks passed!
166 files already formatted

pin commits to scripts/phase19_erasure.py : 15
scripts/phase18_extraction.py commits     : 26
checked = 45; len(pre)*len(art) = 45; product OK: True     NON-VACUOUS: True
```

### Full suite, fresh run on the committed tree

```
$ .venv/bin/python -m pytest -q
822 passed, 1 skipped, 83 warnings in 165.54s (0:02:45)
```

Identical to 19-07's baseline: 822 passed, 1 skipped (the single pre-existing CUDA-only skip).

### The invariants

```
$ git status --porcelain -uall
(clean)
$ git ls-files checkpoints/ | wc -l
       0
$ git check-ignore -v checkpoints/phase19_erase_calibration_adapter.pt
.gitignore:14:checkpoints/	checkpoints/phase19_erase_calibration_adapter.pt
```

Nothing was `git add -f`'d. `scripts/phase19_erasure.py` was never opened for edit.

## Known Stubs

None. Both artifacts are real measured outputs of committed code.

## Handover to 19-09+

1. **The adapter is at `checkpoints/phase19_erase_calibration_adapter.pt`, not
   `checkpoints/phase19_cal_adapter.pt`.** Never delete or move it; `cal-erase` reaches it through
   `tp.arm_outputs(CALIBRATION_ARM, prefix=RETRAIN_PREFIX)`, so a rename breaks the pin's own path.
   sha256 `bc616c36…`, 1,351,991 bytes.
2. **The corpus is at `results/phase19_calibration_corpus.json`.** `cal-erase` reads it through
   `CALIBRATION_CORPUS_PATH`; any downstream plan that types the plan's `phase19_cal_corpus.json`
   will read a file that does not exist.
3. **`cal-erase` is next and it is NOT free.** `_selected_components` runs `select_ablation_prefix`
   over ~288 components with a `dialogue_ppl` callback per prefix — budget accordingly; it is not
   the 80 s the retrain cost.
4. **n = 23, not 27.** Every table that publishes the calibration rate must publish 23 beside it
   (`CALIBRATION_COMMENSURABILITY` clause 3). The rate enters `lock_erasure_floor` as
   `successes / 23`.
5. **The floor's discrimination band, computed on the real denominator n = 23.** `lock_erasure_floor`
   run over every attainable rate — hypothetical, since the calibration rate does not exist yet:

   ```
   ERASURE_FLOOR_MIN == BEST_ATTAINABLE_TARGET_BOUND == 0.09107873950450847
   FLOOR_CEILING     == 0.2

    k/23 -> lock_erasure_floor(k/23)
     0/23 = 0.0000 -> 0.091079  == ERASURE_FLOOR_MIN
     1/23 = 0.0435 -> 0.091079  == ERASURE_FLOOR_MIN
     2/23 = 0.0870 -> 0.091079  == ERASURE_FLOOR_MIN
     3/23 = 0.1304 -> 0.091079  == ERASURE_FLOOR_MIN
     4/23 = 0.1739 -> 0.104300
     5/23 = 0.2174 -> 0.130400
     6/23 = 0.2609 -> 0.156500
     7/23 = 0.3043 -> 0.182600
     8/23 = 0.3478 -> 0.200000  == FLOOR_CEILING (saturated)
     9/23 = 0.3913 -> 0.200000  == FLOOR_CEILING (saturated)
    10/23 = 0.4348 -> 0.200000  == FLOOR_CEILING (saturated)
   ```

   **Only 4, 5, 6 or 7 successes out of 23 move the floor at all.** Below that it pins at
   `ERASURE_FLOOR_MIN`; from 8 upward it saturates at `FLOOR_CEILING` and the blind calibration stops
   discriminating — B4's recorded consequence, now with the actual denominator under it. Recorded
   before the rate exists so it cannot be presented afterwards as a surprise or a design win.
6. **The calibration rate has NOT been measured.** Nothing was erased and nothing was scored in this
   plan — the (a) floor's input is still unknown, which is the state the blind calibration requires.

## Self-Check: PASSED

```
FOUND: results/phase19_calibration_corpus.json
FOUND: results/phase19_cal_training.log
FOUND: results/phase19_erase_calibration/run.csv
FOUND: checkpoints/phase19_erase_calibration_adapter.pt (gitignored, on disk)
FOUND: .planning/phases/19-selective-memory-erasure/19-08-SUMMARY.md
FOUND commit: 7293ec9
FOUND commit: 0ee9b32
git ls-files 'results/phase19_*' -> 3, all three ancestry-checked against all 15 pin commits
git log --format=%H -- scripts/phase19_erasure.py | wc -l -> 15, unchanged
git log --format=%H -- scripts/phase18_extraction.py | wc -l -> 26, unchanged
```
