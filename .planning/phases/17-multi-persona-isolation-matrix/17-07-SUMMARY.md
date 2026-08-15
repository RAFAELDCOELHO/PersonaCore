---
phase: 17-multi-persona-isolation-matrix
plan: 07
subsystem: persona-preflight
tags: [iso-01, sc2, d-06, f-13, th-17-23, th-17-24, th-17-44, stat-05, go-verdict]
requires:
  - scripts/phase17_persona_gate.py (the 17-05 driver, run unmodified)
  - checkpoints/convbase_slim.pt (the frozen un-adapted base, git 04e724c6 / step 4000)
  - artifacts/tokenizer.json (the FROZEN production tokenizer)
  - results/phase16_recall_sample.json (the binding fixture — 104 core_held_out questions)
  - scripts/phase17_persona_facts.py (the 24 minted values + VALUE_TOKEN_CENSUS)
provides:
  - results/phase17_personas_report.md (the ISO-01 evidence artifact, carrying a hand-recorded GO)
  - results/phase17_personas_gate_run.log (the run log)
  - the FIRST results/phase17_* artifact — STAT-05's ordering guard stops being vacuous here
  - an armed assert_report_not_clobbered (permissive -> refuses without --force)
  - the GO that teach_persona._require_go_verdict reads before any Phase 17 adapter trains
affects:
  - plan 17-09 (trains three adapters at three seeds; _require_go_verdict now returns GO)
  - plan 17-10 / 17-11 (inherit F-13: no off-diagonal hit can be the base's own prior)
  - scripts/phase17_personas.py (now permanently uneditable — a results/phase17_* artifact exists)
tech-stack:
  added: []
  patterns:
    - the driver writes only PENDING; the verdict enters the record through a human's own commit
    - a clobber guard that is permissive before the verdict and armed after it, by design
    - an ordering guard's empty-match assertion added the moment its match set becomes non-empty
key-files:
  created:
    - results/phase17_personas_report.md
    - results/phase17_personas_gate_run.log
  modified:
    - tests/test_phase16_prereg.py
decisions:
  - the executor did NOT record the verdict and did not route around the permission denial that
    blocked it from committing one — TH-17-23's mitigation is that path being closed, not the
    git author field, which does not distinguish human from agent in this repo
  - STAT-05's Phase 17 guard gained the empty-match assertion its Phase 16 sibling already had;
    the product assertion alone is satisfied by 0 == n * 0
  - ISO-01 marked complete HERE and only here — 17-03 and 17-05 both claimed it and both
    explicitly deferred to this plan
metrics:
  duration: 60min
  tasks: 2
  files: 3
  completed: 2026-08-14
---

# Phase 17 Plan 07: ISO-01 Pre-Flight Run and GO Verdict Summary

The un-adapted base was asked, 416 times, whether it can already produce any of the 24 minted
persona values. It produced **zero** containments of any of them, every completion is quoted
verbatim in a committed artifact, and a human read them and wrote `GO` by hand — in his own commit,
after the agent was denied permission to write one.

## What Was Built

### Task 1 — the measurement (`6e7bad0`)

`scripts/phase17_persona_gate.py` run unmodified inside the 3.11 venv. Measured, from the run log
and the report:

| Property | Measured |
|---|---|
| Device | `{'device': 'mps', 'cc': None, 'torch': '2.7.1'}` — the primary M3 path, fp32 |
| Wall | 2.1 min, pid 24732 |
| Base | `checkpoints/convbase_slim.pt` via `load_slim` (`weights_only=True`) |
| Base fingerprint | git `04e724c67033f9a2ed8b705a07ad025c867a18c5`, step `4000`, val_loss `1.5235939979553224` |
| Architecture | 6 layers x 6 heads, n_embd 384, vocab_size 8192 |
| `forbid_ids` | sha256 `79b55770f4dcfa943d7528cb04829e8d2e7dd8823b9b5450da418b4fcf3cfc28`, 7645 of 8192 masked |
| Seed | 1337 (`seed_everything`, then per-probe `Generator(1337 + i)`) |
| Probes | 104 unique questions, 416 completions — 8 slots x 13 x 4, exactly the F-07 cache claim |
| Driver commit in provenance | `1c97a107a11a549754e10a0bea2dc559c702b2ae` = `git rev-parse HEAD` at run time |

**The `## Base` section, quoted, because it is the one thing that had to be confirmed first:**

> **No adapter was injected and no adapter weights were loaded.** The model probed below is the
> base checkpoint as exported, with nothing attached to it.

That fingerprint (`04e724c6` / 4000 / 1.5235939979553224) is the same W0 Phase 15 pinned for the
Phase 14 adapter, so the probe demonstrably ran on the base every other Phase 17 number will be
measured against. A guessability gate run against an adapted model returns clean for the wrong
reason and is the one failure here that looks like success; it did not happen.

**Guessability: 24 of 24 clean, every value at `0/52`.** Not one of the 416 completions contains any
minted value under `exact_match_clean`.

**Census: 24 of 24 agree.** Independently re-parsed the report's table against
`phase17_persona_facts.VALUE_TOKEN_CENSUS`: the transcribed column equals the module literal for all
24 ids, and equals the live re-measurement for all 24. Zero `**DIVERGED**`, zero `**FAILED**`
round-trips. Measured maximum 8 = `MAX_VALUE_TOKENS` (`brambleton`), so `derive_recall_budget` still
lands on the published 48. This is a stated comparison over all 24 ids, not an impression.

### Task 2 — the human verdict (`5183e0e`)

Committed by **Rafael**, message
`feat(17-07): record the human GO verdict on the ISO-01 pre-flight`, touching
`results/phase17_personas_report.md` only, 6 insertions / 1 deletion. The diff replaces
`PENDING — user decision at the ISO-01 checkpoint (ROADMAP SC2).` with six lines beginning `GO`.

Re-derived at HEAD after the commit: `recorded_verdict()` first word `GO`; the string `PENDING`
appears **nowhere in the file**; `teach_persona._require_go_verdict(...)` returns `'GO'`.

## The Semantic Evidence The Verdict Rests On

The mechanical floor is unforgiving but blind — it sees containment, not proximity. What the human
read (distilled from the 416 quoted completions; all of it is in the report):

- **`pet_name` / `cat_name` / `sibling_name` — the strongest result.** The base emits no name at all
  and visibly cannot: `i had a dog too, but they did not get a name`, `my dog is a wild animal. his
  name is good.`, `my name is name and mine is a fashion daughter`, `yes, she would need a name,
  yes, i just ret`, `i am looking for a new name?`. It understands a name is wanted and returns the
  concept instead of a token.
- **`person_name` — the only slot producing proper nouns**, 2 of 52: `i am charlier, what do you do
  for a living?` and `that would be very angela. thank you for asking`. Neither is near `thessaly` /
  `drovik` / `kessendra`.
- **`birth_year` — zero four-digit years in 52 completions.** Nearby numerics are small and
  unrelated (`no i have 5, i made 2 years later.`, `i am just turning 50 years.`).
- **`house_number` — zero numbers of that shape.** Closest: `oh cool! i just got a number of last
  constan`, `thank you! my 20 year olds`.
- **`hometown` / `street` — real places only**, never synthetic ones: `i just got back from
  chicago`, `i am in france but i love traveling`, `i am also from california`, `i live in the
  country` (recurring). The `street` slot's dominant mode is the base gluing the slot word onto its
  favourite sentence — `i am a college street major`, `i am a college streeter.` — producing no
  street name at all.

Two artifacts recorded rather than hidden, both named in the verdict itself: the base's
`i am a college student` attractor (up to 7 of 52 in a slot), and `<|assistant|>` role-token leakage
mid-completion — the same leakage Phase 13 already measured and published (79 naive / 70 EWC).
Neither moves any completion toward a minted string.

**Slot contradiction (D-04).** All eight slots hold three mutually exclusive values. 17-03's measured
neighbour screen backs it: minimum edit distance 3 across the 18 proper nouns (`fenmark` vs
`fenwyck`), 2 across the 6 four-digit numerics (`1893` vs `1953`).

**What this buys (RESEARCH F-13).** Zero base containments means an off-diagonal hit in the matrix
cannot be the base's own prior — it must come from adapter *i*. ISO-03's adapter-off column becomes
the higher-powered confirmation rather than the only control.

## The Clobber Guard Flipped — Read This Before Re-Driving The Gate

`assert_report_not_clobbered` was **permissive** for the whole of Task 1 and is **armed** now.
Measured at HEAD, both directions:

| Call | Before the verdict | After the verdict |
|---|---|---|
| `assert_report_not_clobbered()` | returns (re-drive allowed) | **raises SystemExit** |
| with `--force` in `sys.argv` | returns | returns |

This is designed behaviour, not a defect (TH-17-24), and it changes the recovery procedure. A
re-drive of this gate now requires `--force`, and `--force` **destroys the hand-written verdict** —
the blocking judgment ROADMAP SC2 exists to collect. Per 17-05's handover note 4, the honest
recovery if the report genuinely must be regenerated is a **reviewed deletion commit**, not
`--force`. The flag exists only so an interrupted run is re-drivable while the verdict still reads
PENDING, which is the window that has now closed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] STAT-05's Phase 17 guard could go vacuous again**

- **Found during:** Task 1, discharging 17-01's handover note 2 (carried forward through 17-03 and
  17-05 and still open).
- **Issue:** `test_phase17_prereg_is_frozen_before_every_phase17_result` closed with only
  `assert checked == len(prereg_commits) * len(tracked_artifacts)`. That is satisfied by
  `0 == 1 * 0`, so through Waves 1-3 it was green having checked nothing. Committing this plan's
  report fixes the *present* — but the assertion would go quietly green again the moment the
  artifacts left the `git ls-files` match set (rename, move, delete). That is failure mode 2 from
  the module's own header, arriving in the half that did not guard against it; its Phase 16 sibling
  has carried `assert checked` since it was written.
- **Fix:** added the empty-match assertion after the product assertion, with a message naming what
  an empty set now means. Docstring's "stated vacuous pass" paragraph rewritten to describe the
  discharged state rather than the pending one.
- **Watched RED:** the `ls-files` pattern mutated to `results/phase17_NOPE_*` →
  `AssertionError: no committed Phase 17 result was checked — ... matched []` / `assert 0`. Restored
  from a byte-copy backup, not `git checkout` — a blanket restore would have discarded the fix
  itself.
- **Files modified:** `tests/test_phase16_prereg.py`
- **Commit:** `4579034`

### Interpretation recorded

**2. The git author field is NOT evidence of a human verdict, and TH-17-23 does not rest on it.**

It is tempting to record "author = Rafael, therefore a human wrote it" as the mitigation. Measured,
and it is false: this repository's `git config user.name/user.email` is
`Rafael <rafael.d.cooelho@gmail.com>`, and **all three** commits in this plan carry that author —
including `6e7bad0` and `4579034`, which the agent made. The author field distinguishes nothing here
and a SUMMARY asserting otherwise would put a false claim into the permanent record of the very
artifact built to prevent false claims.

What actually satisfied TH-17-23, in order:

1. The driver structurally can only write `PENDING` — pinned by 17-05's
   `test_gate_report_renders_and_does_not_read_as_recorded`.
2. The executor stopped at the checkpoint, returned the quoted evidence, and recorded no verdict.
3. The executor's `git commit` of the verdict was **denied by the permission system** — three times,
   including with a minimal one-line message — and it did not route around the denial. The commit
   exists because it was made outside the agent's tool surface.

Point 3 is the load-bearing one and it is a session-level fact not recoverable from git history.
Recording it here is the only place it survives.

## Verification

Every number below came from a command run in this session at `HEAD = 5183e0e`, after the verdict
commit.

| Check | Result |
|---|---|
| `python -m pytest -q` (full suite) | **645 passed, 1 skipped**, 123.84s, exit 0 — baseline 645/1 held, floor 579 |
| `pytest -q tests/test_phase16_prereg.py` | **3 passed** in 1.12s |
| STAT-05 `checked` | **2** (1 prereg commit `d549e0b` x 2 tracked artifacts) |
| `--diff-filter=A` on the report | **`6e7bad0`** — sole add; `5183e0e` MODIFIED it, so the ordering is untouched |
| `--diff-filter=A` on the run log | **`6e7bad0`** |
| `git log -- scripts/phase17_personas.py` | **`d549e0b`** only — the pinned pre-registration is byte-untouched by this plan |
| `recorded_verdict()` first word | `GO` |
| `"PENDING" in report text` | **False** — nowhere in the file |
| `teach_persona._require_go_verdict(report)` | `'GO'` |
| `assert_report_not_clobbered()` | **raises** without `--force`; returns with it |
| `## ` headings after `## Verdict` (744) | **none** — the section is last and holds the verdict alone; `## Recording The Verdict` stays at 725 |
| `grep -c "clean="` in the report | **24** — one flag per value; `clean=True` 24, `clean=False` 0 |
| Census `**DIVERGED**` / `**FAILED**` rows | **0 / 0** |
| Completion bullets / question bullets | **416 / 104** — matches 8 x 13 x 4 exactly |
| `.venv/bin/ruff check` + `format --check` | clean on `tests/test_phase16_prereg.py` |
| `git status --short` | empty |
| `git diff --diff-filter=D` on both agent commits | empty — no deletions |
| `5183e0e` scope | `results/phase17_personas_report.md` only, 6 insertions / 1 deletion |

## Deferred Issues

`make lint` remains red from **DEF-17-01** (pre-existing to this phase, recorded at 17-01):
`Makefile:16` runs bare `ruff`, which resolves on this box to a pyenv shim holding ruff 0.1.15
against the project's `ruff~=0.15` pin. `.venv/bin/ruff` 0.15.16 — the version CI installs — is
clean on the one file this plan modified. Recorded resolution is still a quick task pointing
`Makefile:16` at `python -m ruff` (15-08 established that `.venv/bin/ruff` would break CI, which has
no venv).

## Known Stubs

None. This plan ran a committed driver and recorded a human decision; it introduced no new code
paths beyond the one test assertion, which is exercised and was watched failing.

**ISO-01 is marked complete here**, for the first and only time. The claimant set was re-derived
across every plan in every phase: exactly `17-03`, `17-05`, `17-07` name it in their `requirements:`
field. 17-03 recorded "ISO-01 stays Pending — the guessability half and SC2's human verdict belong
to 17-05 / 17-07"; 17-05 recorded "ISO-01 is deliberately NOT marked complete, for the third plan
running ... 17-07 runs the measurement and records the verdict, and 17-07 marks the requirement."
Both D-06 conditions have now happened: the checkpoint-specific guessability pass (`6e7bad0`) and
SC2's blocking human verdict (`5183e0e`). This plan marks ISO-01 and nothing else — the 17-01
over-claim pattern is avoided rather than repeated.

## Handover Notes

1. **17-09 is unblocked and must read the verdict, not assume it.**
   `teach_persona._require_go_verdict(pathlib.Path("results/phase17_personas_report.md"))` returns
   `'GO'`; `train_arm` runs the same enforcement. Do not hardcode GO anywhere.
2. **Do not re-run `scripts/phase17_persona_gate.py`.** It now refuses without `--force`, and
   `--force` destroys the human verdict. See the flipped-guard section above; the recovery is a
   reviewed deletion commit.
3. **`scripts/phase17_personas.py` is now permanently uneditable.** A `results/phase17_*` artifact
   exists as of `6e7bad0`, and `test_phase16_prereg.py` proves via `--diff-filter=A` that every
   commit touching the pre-registration is an ancestor of that add. A value change would go in
   `scripts/phase17_persona_facts.py` — but with a GO recorded there is no sanctioned reason to make
   one. Editing the prereg file now turns the guard permanently red with no recovery short of
   history surgery.
4. **STAT-05 is live at `checked = 2` and now fails on an empty match set.** 17-09 carries its own
   `checked > 0` criterion; that is already satisfied structurally, and 17-09 should record the
   count it measures rather than re-adding the assertion.
5. **F-13 is available to 17-10 and 17-11.** Zero base containments on all 24 values means an
   off-diagonal hit cannot be the base's own prior. State it with its scope: it is
   **checkpoint-specific** to `04e724c6`/step 4000 and has no meaning as a standing invariant — the
   report says so in its own header, and the permanent CPU test covers the tokenizer half only.
6. **Census max is 8, exactly on `MAX_VALUE_TOKENS`.** Zero headroom;
   `RECALL_MAX_NEW_TOKENS` stays 48 and shares a budget with every published Phase 14/16 number.
7. **The base's `i am a college student` attractor and the `<|assistant|>` leakage will appear in
   17-09's adapter completions too.** They are properties of this base, already published in Phase
   13. Do not report either as a Phase 17 finding.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.

- **TH-17-23** (a verdict written by code) — mitigated, and by the mechanism described in
  Interpretation 2 above, not by the git author field.
- **TH-17-24** (a clobbered gate report) — mitigated; `assert_report_not_clobbered` ran first in the
  driver and is now armed. `--force` was never passed.
- **TH-17-44** (an ADAPT edit indistinguishable from a post-hoc gate edit) — not exercised; the
  verdict is GO, no value was replaced, and `scripts/phase17_personas.py` sits at its single commit.
- **TH-17-25** (personal data in a public artifact) — mitigated; all 24 values are invented (D-06)
  and the human read in step 3 was the last check that nothing resembling a real identifier ships.
  The 416 quoted base completions are model output about invented personas, no real data.
- **TH-17-SC** — holds; zero packages installed.

## Self-Check: PASSED

Files:

- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_personas_report.md` (746 lines)
- FOUND: `/Users/juliorcoelho/PersonaCore/results/phase17_personas_gate_run.log`
- FOUND: `/Users/juliorcoelho/PersonaCore/tests/test_phase16_prereg.py` (modified)

Commits:

- FOUND: `6e7bad0` feat(17-07): run the ISO-01 pre-flight on the un-adapted base — verdict PENDING
- FOUND: `4579034` test(17-07): make the STAT-05 ordering guard non-vacuous now that a result exists
- FOUND: `5183e0e` feat(17-07): record the human GO verdict on the ISO-01 pre-flight
</content>
</invoke>
