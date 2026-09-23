---
phase: 20-pre-registration-the-three-condition-gate
plan: 07
subsystem: measurement
tags: [pre-registration, ancestry-guard, bit-identity-control, unpinned-driver, retention-floor, irreversible-ordering]

# Dependency graph
requires:
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 01
    provides: "tests/test_phase20_prereg.py's ancestry guard with V4_ARTIFACT_GLOBS = ('results/phase20_*',) — the guard this plan makes non-vacuous"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 04
    provides: "scripts/mitigation_gate.py::retention_cap — the required-kwarg consumer of the floor measured here"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 05
    provides: "the CLOSED pin at abf9072, sha256 86db4798...1997e14"
  - phase: 20-pre-registration-the-three-condition-gate
    plan: 06
    provides: "the fourteen CI guards that keep the pin honest while it is still editable"
  - phase: 19-selective-erasure
    provides: "results/phase19_noise_floors.json's retention_ppl_pre_erasure block (the three published values the bit-identity control reproduces); results/phase19_dialogue_floor.json's recipe; the two checkpoints/phase19_erase_dialogue_floor_seed*_adapter.pt arms; scripts/phase19_run.py:787-882 as the driver precedent and :803 as the instrument-trap precedent"
provides:
  - "scripts/phase20_run.py — the UNPINNED MPS retention-floor driver, with the seed-1337 bit-identity control armed inside the seed loop"
  - "results/phase20_retention_floor.json — the ADAPTER-REGIME retention noise floor 0.008681618994239138 and cap 3.9085032379884783, with every reading, denominator, window count, seed, adapter path, adapter sha256, git SHA, device and torch version embedded"
  - "THE FIRST v4.0 ARTIFACT — and therefore the moment scripts/mitigation_gate.py became permanently uneditable"
  - "A non-vacuous ancestry guard: checked 0 -> 9 against tracked_artifacts 0 -> 1"
affects: [phase-21, phase-23, phase-25, phase-27]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The bit-identity control is placed INSIDE the seed loop, not after it, so it fires before the untrusted reading is TAKEN rather than merely before it is published — and a failure costs one seed of MPS instead of two"
    - "A transcribed constant is PROVED equal to the committed record it mirrors at run time (RECIPE vs results/phase19_dialogue_floor.json), so a retyped regime bound is a SystemExit rather than a silently wrong artifact"
    - "_refuse(path) runs before a single tensor is loaded — an expensive measurement never discovers its output path is occupied at the end"
    - "The instrument trap is closed STRUCTURALLY and asserted by AST, not by grep: two retention_perplexity call sites, five positional args, tok fifth, zero keywords — because ruff format wraps the OFF call at line-length 100 and a whole-call grep cannot hold"
    - "An UNPINNED driver's docstring states its import property EXACTLY and no wider: this file's own torch/numpy/personacore imports are function-local, and `import phase19_erasure as pin` is named as the single module-scope import that DOES pull torch transitively"

key-files:
  created:
    - scripts/phase20_run.py
    - results/phase20_retention_floor.json
  modified:
    - tests/test_phase19_erasure.py
    - .planning/phases/20-pre-registration-the-three-condition-gate/20-VALIDATION.md
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "The bit-identity control was placed INSIDE the seed loop rather than after it, as the plan's step ordering (4 loop, 5 window accounting, 6 control) would read. The plan's own words for step 6 are 'before any new number is trusted', and inside-the-loop is the strictly stronger reading: seed 2024 is not merely unpublished when the control fires, it is UNMEASURED. It also halves the cost of a failure"
  - "RECIPE is a module constant per the plan, but retention_floor() PROVES it equal to results/phase19_dialogue_floor.json's committed recipe before measuring. 20-VALIDATION.md's own landmine list says a retyped double is a wrong double; the D-06 regime bound travels inside this artifact, so it is verified rather than transcribed"
  - "The artifact records the sha256 of BOTH checkpoints/persona_adapter.pt (the file the published block was measured on) and checkpoints/phase19_erase_dialogue_floor_seed1337_adapter.pt (the file measured here), plus a control_is_across_two_distinct_files boolean. checkpoints/ is gitignored, so a reader can never check this themselves — without the digests, 'the control passed' would be indistinguishable from a re-read of the same bytes"
  - "tests/test_phase19_erasure.py's retention call-site census was scoped by NAME, not by lowering its count. phase20_run.py is the THIRD successor; the census stays at 6 calls in 4 modules, so a genuinely new unadapted caller anywhere else still reddens the guard. scripts/phase19_erasure.py was not edited"
  - "GATE-02's stated `retention_cap 4.029000` is recorded as SUPERSEDED in three places (REQUIREMENTS.md traceability note, ROADMAP.md SC1 amendment, the artifact's own governs field) rather than being quietly edited out of the requirement text. The requirement is a pre-registration record and the supersession is a finding, not a correction"

patterns-established:
  - "An artifact whose inputs are gitignored must carry its own falsifiability: not just the readings but the digests of the files that produced them, so 'this control passed' is checkable in principle even when the bytes are not in the repo"

requirements-completed: [GATE-02, CAL-04]

# Metrics
duration: 26min
completed: 2026-08-20
---

# Phase 20 Plan 07: The Measured Retention Floor and the Irreversible Ordering Summary

**The adapter-regime retention noise floor is measured, published with full embedded provenance, and committed strictly after a pushed and unmodified pin — the seed-1337 bit-identity control passed with `abs_delta = 0.0` on both readings against a DIFFERENT adapter file, every D-06 expectation reproduced exactly with zero disagreement, and the ancestry guard has stopped being vacuous (`checked` 0 → 9).**

---

## What was built

Two commits, in the order that is the whole point of the plan.

| # | Commit | Files | What |
|---|--------|-------|------|
| 1 | `669d082` | `scripts/phase20_run.py` (new), `tests/test_phase19_erasure.py` | The UNPINNED driver. **No `results/` file.** |
| 2 | `9bb34ad` | `results/phase20_retention_floor.json` (new) | The artifact, alone, one file. |

`scripts/mitigation_gate.py` appears in **neither**, and is byte-unchanged at sha256
`86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14` — verified before Task 2, after
Task 2, and after Task 3.

---

## The driver's full stdout

```
[preflight] device=mps cc=n/a torch=2.7.1
[phase20_run] retention-floor retention_ppl_noise_floor = 0.008681618994239138
[phase20_run] retention-floor cap = 3.9085032379884783
[phase20_run] retention-floor borrowed_cap = 4.029
[phase20_run] retention-floor borrowed_floor_ratio = 7.939763314393305
[phase20_run] seed 1337: off = 3.891139975617828  on = 4.219759892336485  gap = 0.3286199167186572  n = 1000285
[phase20_run] seed 2024: off = 3.891139975617828  on = 4.2284415113307245  gap = 0.33730153571289634  n = 1000285
[phase20_run] wrote /Users/juliorcoelho/PersonaCore/results/phase20_retention_floor.json
```

Exit 0. One invocation: `.venv/bin/python scripts/phase20_run.py retention-floor`. No training of any
kind — the two committed `erase_dialogue_floor_seed*` adapters were re-read with a second instrument.

### The two seeds' four readings, with their shared denominator

| seed | `adapter_off` | `adapter_on` | `delta_on_minus_off` | `n_scored_tokens` |
|---|---|---|---|---|
| 1337 | `3.891139975617828` | `4.219759892336485` | `0.3286199167186572` | `1000285` |
| 2024 | `3.891139975617828` | `4.2284415113307245` | `0.33730153571289634` | `1000285` |

The denominator is **shared, not assumed**. Three checks, all inside the driver, all as
`raise SystemExit`:

- `on_tokens == off_tokens` per seed — otherwise the delta measures the corpus, not the adapter.
- `n_corpus - 1 == on_tokens` — the window accounting **checked rather than quoted**:
  `corpus_tokens = 1000286`, `n_windows = 3908` at `block_size = 256`, so `1000286 - 1 = 1000285`.
  Consecutive windows share their boundary token, so every target `1..n-1` is scored exactly once.
- `adapter_off_identical_across_seeds` is `true` — which is what makes `noise(gap) ≡ noise(ppl_on)`
  (D-04) and costs the gap form zero new constants.

---

## The seed-1337 bit-identity comparison

**It passed EXACTLY.** Exact `==` on all three values, no tolerance, enforced by `SystemExit` placed
**inside the seed loop** — so it fired before seed 2024 was measured at all, not merely before it was
published.

| | measured here | published (`results/phase19_noise_floors.json` `retention_ppl_pre_erasure`) | `abs_delta` |
|---|---|---|---|
| `adapter_off` | `3.891139975617828` | `3.891139975617828` | **`0.0`** |
| `adapter_on` | `4.219759892336485` | `4.219759892336485` | **`0.0`** |
| `n_scored_tokens` | `1000285` | `1000285` | — |

`bit_identical: true`.

**And it is a control, not a tautology.** The published block was measured on
`checkpoints/persona_adapter.pt`; this run measured
`checkpoints/phase19_erase_dialogue_floor_seed1337_adapter.pt`. These are **different files** —

- `persona_adapter.pt` → `226f2ae59938e389b396d999bc5f3e1e464874db5f3352d513dc5cd85984ebfb`
- seed-1337 arm adapter → `f12ab4c3db4126b5399f46cd2b674d7ae5fdae83f7aff27fdffe9bb65ee64974`

— and the artifact carries both digests plus a `control_is_across_two_distinct_files: true` boolean.
`checkpoints/` is gitignored (T-20-45), so a reader can never re-run this; without the digests,
"the control passed" would be indistinguishable from a re-read of the same bytes.

---

## The measurement against D-06's expectations

Every value re-derived from real code. **Zero disagreement — nothing was bent to match.**

| Quantity | D-06 expected | **Measured** | Agrees |
|---|---|---|---|
| seed 1337 `adapter_on` | `4.219759892336485` | `4.219759892336485` | ✅ |
| seed 2024 `adapter_on` | `4.2284415113307245` | `4.2284415113307245` | ✅ |
| `adapter_off` (both) | `3.891139975617828` | `3.891139975617828` | ✅ |
| `n_targets` (both) | `1000285` | `1000285` | ✅ |
| `retention_ppl_noise_floor` | `0.008681618994239138` | `0.008681618994239138` | ✅ |
| `borrowed_floor_ratio` | `7.939763314393305` | `7.939763314393305` | ✅ |
| `cap` | `3.9085032379884783` | `3.9085032379884783` | ✅ |

**The seed-2024 reading `4.2284415113307245` now has code provenance.** Before commit `9bb34ad` it
existed in exactly one file on disk — `20-CONTEXT.md`, a discussion transcript. `20-RESEARCH.md`
assumption A1 named non-reproduction as the risk that would have forced a phase decision rather than
a fix. It reproduced.

**The re-measurement is TIGHTER, not easier.** `cap = 3.9085032379884783` against the borrowed
`borrowed_cap = 4.029`; the Phase 12 full-fine-tune floor `0.068930` is `7.939763314393305x` larger
than the measured adapter-regime one. The cap is anchored on the **imported** `3.891140`
(`pin.V20_EWC_RETENTION_PPL`), never on this run's measured `3.891139975617828` — the cap must be the
pinned rule's output, not this run's rounding. Its `cap_derivation` string reads
`3.89114 + 2 x 0.008681618994239138 (scripts/erasure_gate.py:246)`.

Both D-06 bounds travel **inside** the JSON, not in prose beside it: `bounds` states `n = 2` seeds
with no confidence interval, and `recipe` carries the v3.0 persona recipe (`n_facts: 10`,
`replay_ratio: 1.0`, `arm_spec: "real"`, `second_person: false`) — **proved equal at run time** to
`results/phase19_dialogue_floor.json`'s committed `recipe` rather than trusted as a transcription.

---

## The ordering, and the guard that stopped being vacuous

```
artifact first add: 9bb34ade60bf0bd690aba1d050ed5e4775a89d03
newest pin commit : abf9072c492cb7b87491bda94391187372dba6ab
distinct commits  : YES
git merge-base --is-ancestor abf9072 9bb34ad  ->  exit 0
git show --stat 9bb34ad  ->  exactly one file
```

D-08's discipline is **tighter than the mechanism**: `git merge-base --is-ancestor` is reflexive, so a
same-commit pair would have passed. The artifact was committed alone anyway.

The pin's commit list is **unchanged** from the Task 1 checkpoint — nine commits, `95b3c8a` through
`abf9072`.

### `checked` and `tracked_artifacts`, before and after

| | before `9bb34ad` | after `9bb34ad` |
|---|---|---|
| `tracked_artifacts` | `0` | **`1`** |
| `prereg_commits` | `9` | `9` |
| `checked` | `0` | **`9`** |
| `checked == len(prereg) × len(tracked)` | `0 == 9 × 0` ✅ *(vacuous)* | `9 == 9 × 1` ✅ **(demanding)** |
| `bool(checked) == bool(tracked_artifacts)` | `False == False` ✅ *(trivial side)* | `True == True` ✅ **(demanding side)** |

Through waves 1–5 the guard's green read `0 == n × 0` — it had never once observed
`V4_ARTIFACT_GLOBS` matching anything. **It has now.** `tests/test_phase20_prereg.py`: `18 passed` in
`1.08s`.

---

## `scripts/mitigation_gate.py` is now PERMANENTLY UNEDITABLE

This is the load-bearing consequence of commit `9bb34ad` and it is stated plainly.

From the artifact's first add forward, **any** commit touching `scripts/mitigation_gate.py` turns
`test_phase20_prereg_is_frozen_before_every_phase20_result` **permanently red**. There is no recovery:
the guard takes `adds[-1]`, the **earliest** add, and plan 20-03 proved empirically across five
observed states in a throwaway repo that `git rm` plus re-add reproduces that earliest add
byte-identically. A delete-and-re-add cycle cannot launder the ordering.

**Every correction from here is a dated continuation, never an edit** (D-24):

```python
scripts/_addendum.py::append_addendum(path, addendum, *, pending, recorded)
```

Both `pending` and `recorded` are **required keyword arguments**, and the module **refuses a second
append** (`text.count(pending) == 0` → `SystemExit`). A continuation must also **arm a tripwire test**
that fires when a later plan would consume the wrong value — a prose note gets missed. That is a
decision for the human, not for an executor.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The Phase 19 retention call-site census went RED on the new driver**

- **Found during:** Task 2, at the full-suite gate the plan explicitly mandated for this task
  ("this is a new `scripts/*.py` file and therefore enters the repo-wide AST scans… do not skip it").
- **Issue:** `tests/test_phase19_erasure.py::test_retention_measurement_pins_a_new_call_site_with_no_adapted_precedent`
  failed with `the retention call-site census moved: 8 calls in ['build_retention_bin.py',
  'finetune_ab.py', 'finetune_dialog.py', 'finetune_smoke.py', 'phase20_run.py']` against its pinned
  `6 calls in 4 modules`. **This is the guard working as designed** — `RETENTION_MEASUREMENT`
  clause 2 promised "the claim cannot go stale the first time someone adds a fifth caller", and the
  guard's own comment records it already catching the *second* successor at 19-10.
- **Fix:** `scripts/phase20_run.py` excluded **BY NAME** as the third successor, on exactly the
  grounds the guard's comment prescribes, and under the same **positive obligation** the existing two
  exclusions carry — every excluded caller must actually reach the injection path, asserted in the
  loop (`phase20_run.py` calls `load_adapted_model`). **The census numbers were NOT lowered:** they
  remain `6` calls in `4` modules, so a genuinely new *unadapted* caller anywhere else still reddens
  it. A comment block records why, dated to 20-07.
- **What was NOT touched:** `scripts/phase19_erasure.py` (the Phase 19 pin) — the prose making the
  precedent claim is CLOSED and was not edited. `tests/test_phase19_erasure.py` is a test file and is
  watched by no ancestry guard: `PHASE19_PREREG_ARTIFACT` is `scripts/phase19_erasure.py` and
  `PHASE19_FLOOR_ARTIFACT` is `scripts/phase19_floor.py`; verified before editing.
- **Files modified:** `tests/test_phase19_erasure.py` (+14/-2)
- **Commit:** `669d082` (with the driver, in Task 2 — before any artifact existed)

### Deliberate departures from the plan's letter

**2. The bit-identity control was placed inside the seed loop, not after it**

The plan's numbered steps read `(4) loop → (5) window accounting → (6) control`, which places the
control after both seeds are measured. Step 6's own words are "**before any new number is trusted**".
Inside-the-loop is the strictly stronger reading of that sentence: when the control fires, seed 2024
is not merely unpublished, it is **unmeasured**. It also halves the cost of a failure. Recorded here
rather than silently.

**3. `RECIPE` is proved equal to its source, not merely transcribed**

The plan specifies `RECIPE` as a module constant, and it is one. `retention_floor()` additionally
`SystemExit`s if it disagrees with `results/phase19_dialogue_floor.json`'s committed `recipe`. This
is `20-VALIDATION.md`'s own landmine ("a retyped double is a wrong double") applied to the one bound
this artifact publishes about its own regime. Rule 2 — a bound that describes the wrong regime is a
correctness defect in a provenance artifact, not a cosmetic one.

**4. Three fields beyond the plan's key register**

`recipe_source`, `control_is_across_two_distinct_files` and `published_adapter_sha256` were added to
the artifact. Reason: `checkpoints/` is gitignored (T-20-45, accepted), so the artifact's own stated
mitigation is "embed everything a reader needs". The control compares against a **different file**
than the one measured; without both digests a reader cannot tell a control from a tautology.

**No other deviations.** No architectural change was needed; no Rule 4 decision arose.

---

## Authentication gates

None.

---

## Requirements assessed

| Req | Marked | Reasoning |
|---|---|---|
| **CAL-04** | ✅ complete | "Per-point K and the promotion rule are committed **before any v4.0 artifact exists**." The rules landed at `20-05` (`ratchet_k`, `promote_to_full_fidelity`); **this plan is where the clause is proved**, because before commit `9bb34ad` no v4.0 artifact existed and the guard was vacuous. `abf9072` is an ancestor of `9bb34ad`, `checked = 9`. Fully discharged. |
| **GATE-02** | ✅ complete, **with a recorded supersession** | The **mechanism** — condition (c) computed from constants imported from `erasure_gate.py`, never retyped — is discharged across `20-01`/`20-04`/`20-06` and audited by AST. **But GATE-02's stated yield `retention_cap 4.029000` is superseded by D-06 and this phase does not produce it.** `retention_cap` deliberately does *not* import `V20_RETENTION_NOISE_FLOOR = 0.068930` (a Phase 12 full-fine-tune reading); it takes the floor as a required kwarg (D-07), and the governing v4.0 cap is `3.9085032379884783`. |

**The GATE-02 supersession is recorded in three places rather than quietly edited out of the
requirement text**, which is a pre-registration record:

1. `.planning/REQUIREMENTS.md` traceability note for GATE-02.
2. `.planning/ROADMAP.md` Phase 20 SC1, as an inline **"Amended by D-06 … and the amendment is
   TIGHTER"** block.
3. The artifact's own `governs` field, which also states that `scripts/erasure_gate.py:246` still
   computes `4.029` for **Phase 19** verdicts, that this is correct and deliberate, and that commit
   `23a830c` is **not** to be amended.

A reader checking `retention_cap == 4.029000` against the v4.0 gate will find `3.9085032379884783`
and, in all three places, why.

---

## Known Stubs

None. No placeholder values, no unwired data paths, no TODO/FIXME introduced.

---

## Threat Flags

None. This plan adds no network endpoint, auth path, file-access pattern or schema at a trust
boundary. The one new file-read surface — the two gitignored adapters — goes through
`phase14_recall.load_adapted_model`, i.e. the existing `weights_only=True` restricted-unpickler choke
point (T-14-22), and no `torch.load` is called directly.

---

## Verification

| Gate | Result |
|---|---|
| `.venv/bin/python -m pytest -q` (full, after both commits) | **`863 passed, 1 skipped`** in `194.68s` — the `20-06` baseline, unmoved |
| `.venv/bin/python -m pytest -q tests/test_phase20_prereg.py` | `18 passed` in `1.08s`, `checked = 9` |
| `.venv/bin/python scripts/mitigation_gate.py` | exit 0 |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | clean, 174 files |
| `git status --porcelain pyproject.toml` | empty — **RPT-03 holds, five milestones** |
| AST: module-scope imports of `phase20_run.py` | `['hashlib', 'json', 'pathlib', 'phase19_erasure', 'sys']` — no `torch`/`numpy`/`personacore` |
| AST: `retention_perplexity` call sites | 2 sites, 5 positional args each, `tok` fifth, 0 keywords |
| `grep -c "forbid_ids" scripts/phase20_run.py` | `0` — the trap is closed structurally |
| `git ls-files 'results/phase20_*'` after Task 2 | empty — the driver landed with no results file |
| `git show --stat 9bb34ad` | exactly one file |
| `shasum -a 256 scripts/mitigation_gate.py` | `86db4798…1997e14`, unchanged throughout |

**One thing worth flagging honestly:** the plan and the execution brief both anticipated the MPS run
would take "order of an hour". **It took under three minutes** — the driver was launched immediately
after `669d082` (`19:34:50-03:00`) and the artifact's mtime is `19:37:24`, bounding the whole
two-seed, four-reading run at **≤ 2 min 34 s**. Nothing was shortcut, no token budget was reduced,
and the denominator is the full `1,000,285` targets per reading. The expectation was simply wrong;
recording it rather than repeating it.

---

## Duration

**26 min**, git-derived, no estimate:

- Inherited tree at `4554c93`, `2026-08-20T19:11:41-03:00`.
- Task 2 commit `669d082`, `2026-08-20T19:34:50-03:00`.
- Task 3 commit `9bb34ad`, `2026-08-20T19:37:56-03:00`.
- Span across this plan's own two code commits: **3 min 06 s**. Span from the inherited tree to the
  final commit, which is the figure in the frontmatter: **26 min**.

---

## Self-Check: PASSED

- `scripts/phase20_run.py` — FOUND
- `results/phase20_retention_floor.json` — FOUND
- Commit `669d082` — FOUND
- Commit `9bb34ad` — FOUND
- `scripts/mitigation_gate.py` sha256 `86db479876ebeb2ba5b23c3b95da0ab20f13a3fbccf655b697280421b1997e14` — UNCHANGED, and absent from both commits
