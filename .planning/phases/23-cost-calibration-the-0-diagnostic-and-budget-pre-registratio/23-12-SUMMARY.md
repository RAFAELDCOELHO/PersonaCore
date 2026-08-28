---
phase: 23
plan: 12
subsystem: cost-calibration
tags: [CAL-01, CAL-05, D-10, retract-in-place, cost-record, planning-correction]
requires:
  - results/phase23_cost.json (23-11) — the measuring artifact; every published figure is a leaf of it
  - .planning/phases/23-*/23-11-SUMMARY.md — the eleven pre-registered figure paths, for the drift check
  - scripts/_prose.py::normalized — the ONE line-wrap-tolerant matcher, imported not re-written
provides:
  - the dated additive RETRACTED IN PLACE continuation in all three planning files
  - REQUIRED_FIGURE_PATHS + the two-direction guard (_required_figures_missing / _long_figures_not_sourced)
  - CAL-01 and CAL-05 ticked, with both traceability rows filled
affects:
  - 23-13 (selects K against the corrected ceiling, not the retracted 4.77 floor)
  - 23-14 (reads the filled traceability rows as the convention to match)
tech-stack:
  added: []
  patterns:
    - "a falsified figure is SUPERSEDED with its correction beside it, never deleted"
    - "a published figure is the repr() of a leaf at a PRE-REGISTERED field path"
    - "a guard binds in BOTH directions over ONE pre-registered set; an allow-list is refused"
    - "a residual is DISCLOSED in the docstring and the SUMMARY, not patched with a fourth rule"
key-files:
  created: []
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
    - tests/test_phase23_cost.py
decisions:
  - "route: the RETRACTED IN PLACE continuation shape, NOT scripts/_addendum.py — no pending/recorded pair and no `## Verdict` section exists in a planning document"
  - "the marker is searched FROM the claim's position, so a status line describing the correction above the claim is not a false RED"
  - "the four 6-11-digit leaves in phase23_cost.json are DISCLOSED; the threshold is not re-tuned"
metrics:
  duration: ~55 min (2 task commits + 2 full-suite runs)
  completed: 2026-08-28
---

# Phase 23 Plan 12: D-10 Retract-in-Place of the Falsified "~1,010×" Cost Claim Summary

The claim that evaluation costs `~1,010×` training is corrected in all three planning documents by a
dated additive continuation that publishes the eleven pre-registered figure paths at full stored
precision — **no arm at any protocol is `~1,010×`, but all eight measured ratios still bind, so only
the margin moves** — and the correction is held additive by a guard that runs in both directions over
one pre-registered set.

---

## What was published, and where it was read from

`results/phase23_cost.json`, sha256
`f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637`. Every figure below was resolved
by **field path** and rendered with `repr()`, never retyped from this plan's prompt or from 23-11's
prose. The eleven paths were diffed against 23-11-SUMMARY's own table programmatically — **identical
in both names and order**, so there is no drift to escalate.

| path | rendering | `protocol` it carries |
|---|---|---|
| `training.non_dp.training_seconds_mean` | `161.12400419991462` | protocol-matched non-DP comparator |
| `training.non_dp_superseded_protocol.training_seconds_mean` | `79.14336965046823` | old unmitigated control (superseded as a comparator) |
| `training.non_dp.wall_clock_gap_vs_superseded` | `2.035849685343305` | — (derived, names both) |
| `training.dp_n8.seconds_total` | `205.44225783273578` | dp_n8, seam active, sigma=0 |
| `training.dp_n64.seconds_total` | `1383.276182374917` | dp_n64, seam active, sigma>0 |
| `generation.h_per_point_floor` | `5.7223403197590965` | — (not a training figure) |
| `generation.h_per_point_ceiling` | `9.013691285839306` | — (not a training figure) |
| `ratios.non_dp.eval_over_training_ceiling` | `201.39326098648866` | protocol-matched non-DP comparator |
| `ratios.non_dp_superseded_protocol.eval_over_training_ceiling` | `410.006407009605` | old unmitigated control (superseded as a comparator) |
| `ratios.dp_n8.eval_over_training_ceiling` | `157.94846187604026` | dp_n8, seam active, sigma=0 |
| `ratios.dp_n64.eval_over_training_ceiling` | `23.458286235587472` | dp_n64, seam active, sigma>0 |

**The finding the continuation states.** No arm at any protocol is `~1,010×`. The largest measured
ceiling ratio is `410.006407009605`, on the arm the record itself argues is the **wrong** comparator.
**But all EIGHT of the record's ratios — the four ceiling ones above and the four floor-side ones the
continuation deliberately does not publish — are well above 1**, so evaluation still binds at every
capacity and at both ends of the bracket. D-03's ordering, D-04's halt rule and the decision to size Z
from the evaluation leg are unchanged; what moves is the margin, and it moves toward *more* wall clock.

---

## Does any real run reproduce the `20.4 s` / `843x` projection? NO.

The plan requires this stated here and **only** here, because the SUMMARY is a dated report while a
continuation is a standing correction whose every bare figure must load from the cost record.

| quantity | the PROJECTION (`23-RESEARCH.md:637-641`) | MEASURED, from `results/phase23_cost.json` |
|---|---:|---:|
| non-DP training, whole call | `20.4 s` (loop-only, accum=1) | `161.12400419991462` s at the protocol-matched comparator; `79.14336965046823` s at the superseded protocol |
| `eval ÷ training` | `843×` | `201.39326098648866` and `410.006407009605` respectively, at the ceiling |

**Neither measured non-DP protocol reproduces `20.4 s`, and neither is close.** The cheaper of the two
is still ~3.9× the projection, and the comparator that actually sizes the ratio is ~7.9× it. The
projection excludes `build_arm_bins`, 20 in-loop evals, 4 checkpoint writes, the replay memmap I/O and
two `masked_perplexity` sweeps — and `23-RESEARCH.md:665-685` already RETRACTED IN PLACE the same
table's lower-bound status after 23-10 measured its `dp_n8` row 9.8% high. So the projection is a
**third thing this retraction corrects**, not the surviving half of the claim. The continuation names
it by heading text and range and writes **none** of its numerals, because nothing measured them.

---

## Task 1 — the continuation, in all three files (`72ea546`)

**Route: the `RETRACTED IN PLACE` continuation shape, NOT `scripts/_addendum.py`.** The plan permits
either and asks which was used and why. `append_addendum(path, addendum, *, pending, recorded)`
requires a `pending`/`recorded` placeholder pair occurring exactly once, and it re-checks
`_verdict.recorded_verdict(updated) == _verdict.recorded_verdict(text)`. A planning document has
neither: there is no placeholder line to replace and no `## Verdict` section to preserve, and the
helper appends at **end of file** whereas the correction has to sit immediately beside the sentence
it corrects. The precedent shape was read from the two committed examples the plan names —
`.planning/REQUIREMENTS.md`'s DPSGD-03 row and `23-RESEARCH.md:665-685` — and reproduced: the marker
appended to the text it corrects, the original left unamended *"as the record of what was believed"*,
the attribution named, and what closed it stated.

### The deletion accounting — all FOUR named

`git show --numstat --format= 72ea546`:

| file | insertions | deletions |
|---|---:|---:|
| `.planning/REQUIREMENTS.md` | 98 | **4** |
| `.planning/ROADMAP.md` | 22 | **0** |
| `.planning/STATE.md` | 20 | **0** |

The four, quoted from `git diff -U0`:

1. `- [ ] **CAL-01**: The training leg is measured to complete the pair (~17 s per …` → `- [x]`
2. `- [ ] **CAL-05**: The rate above was measured on the **un-adapted base**, where …` → `- [x]`
3. `| CAL-01 | Phase 23 | |` → the filled traceability row
4. `| CAL-05 | Phase 23 | |` → the filled traceability row

Each is a **modify** — one deletion plus one insertion. Both SATISFIED notes were added as NEW lines
beneath the ticked checkbox rather than folded into them, precisely so the deletion count stays at
four. The claim sentence, the `h/point` table and every other original line are byte-unchanged.

*(Deletions rose to 1 on ROADMAP and 5 on STATE in the final metadata commit — the plan-list tick and
the frontmatter/position update this plan is also required to make. Those are state updates, not
corrections, and they are listed under "State updates" below.)*

### Baselines and final counts, MEASURED at HEAD before writing

| check | baseline at `fc39f50` | after | criterion |
|---|---:|---:|---|
| `grep -c "RETRACTED IN PLACE" .planning/REQUIREMENTS.md` | 1 | **6** | `-ge 2` ✓ |
| `grep -c "1,010"` REQUIREMENTS / ROADMAP / STATE | 1 / **3** / 1 | 4 / 5 / 6 | `>=` baseline ✓ |
| `grep -c 'R3.A — CAL-01: training wall-clock…'` in REQUIREMENTS | 0 | **1** | `-ge 1` ✓ |
| `grep -c '23-RESEARCH.md:637-641'` in REQUIREMENTS | 0 | **1** | `-ge 1` ✓ |
| `grep -c '(plan 23-12)'` in REQUIREMENTS | 0 | **3** | discriminating ✓ |
| sentinel occurrences per file (`grep -o … \| wc -l`) | 0 / 0 / 0 | 1 / 1 / 1 each | `= 1` ✓ |
| long literals (8+ frac digits) per file | 69 / **25** / **98** | — | whole-file scan refused ✓ |

**Two of the plan's stated baselines had drifted and are corrected here.** The ROADMAP `1,010` count
is **3**, not 2 — 23-11 added its own plan-list entry at `:641` mentioning the figure. And the long-
literal counts are **69 / 25 / 98**, not 69 / 20 / 86; ROADMAP and STATE both grew literals in 23-11.
Both were re-measured before Task 1 wrote, exactly as the plan instructs. Neither changes any
conclusion — the ROADMAP figure is a `>=` floor, and the literal counts only make the case for slice
scanning stronger.

The six `RETRACTED IN PLACE` lines in REQUIREMENTS, by name: the pre-existing DPSGD-03 traceability
row (`:446`, which carries **two** markers on that one line — the `grep -c` defect, live in this
repository); this plan's marker line (`:187`); the mandated third-thing-corrected citation, which
lands on its own wrapped line (`:257`); CAL-01's new SATISFIED note (`:278`); and the two filled
traceability rows (`:450`, `:453`).

### The three continuations

| file | what its continuation carries |
|---|---|
| `.planning/REQUIREMENTS.md` | the full set — all eleven renderings, both protocols side by side, the root cause, the third-thing-corrected citation, what does not change, and the floor/ceiling disclosure |
| `.planning/ROADMAP.md` | the record + digest, both `h_per_point` bounds, `training.non_dp.training_seconds_mean` with its protocol, and all four ceiling ratios — the figures the milestone preamble's own claim needs |
| `.planning/STATE.md` | the same shape, scoped to constraint **(3)**'s wording, and pointing at REQUIREMENTS for the full set |

Forcing all eleven into a milestone preamble or a status line would make them copies of the first,
which is what half one's REQUIREMENTS-only scope refuses.

---

## Task 2 — the guard (`81f0be2`)

`git show --numstat --format= 81f0be2` → `387 insertions, 1 deletion` in `tests/test_phase23_cost.py`.
**The one deletion is a modify**: `import mitigation_gate  # noqa: E402  (needs the sys.path insert
above)` became `(same reason)` when `import _prose` took over as the first import in the block. No
committed assertion was changed or removed.

### Both helper bodies, in full

The plan requires these quoted so a reader can confirm by eye that nothing is dropped, no span is
captured or classified, and no token is exempted. Docstrings elided; this is the executable body:

```python
def _required_figures_missing(text, record):
    return [
        f"{path} -> {_figure(record, path)}"
        for path in REQUIRED_FIGURE_PATHS
        if _figure(record, path) not in text
    ]


def _long_figures_not_sourced(text, record):
    sourced = {_figure(record, path) for path in REQUIRED_FIGURE_PATHS}
    return [match for match in LONG_FIGURE.findall(text) if match not in sourced]
```

That is the whole mechanism. The round-1..4 six-step extraction, the marker-token strip, the
backtick-refusal predicate, the comma-stripping and the allow-list are absent — asserted structurally,
not claimed: the AST census over module-level assigns with `ALLOW` in the name returns `[]`.

### Which defect each half catches

| half | direction | catches | does NOT catch |
|---|---|---|---|
| `test_the_correction_quotes_the_cost_record_faithfully` | record → continuation | an OMITTED figure, and any ROUNDING of a required one | an INVENTED extra figure |
| `test_the_continuation_invents_no_figure` | continuation → record | an INVENTED long figure | an omission or a rounding |

Half one binds on `.planning/REQUIREMENTS.md` **only**; half two binds on **all three** slices. Neither
implies the other, and `test_the_continuation_invents_no_figure` is the criterion for must_haves
truth 2.

### The tripwire — five constructed defects, literal return values

Each was written to a `tmp_path` copy of `.planning/REQUIREMENTS.md`, never to the committed file, with
the mutation applied to the sentinel slice so it lands where the guard looks. Literal helper output:

| case | `_required_figures_missing` | `_long_figures_not_sourced` | |
|---|---|---|---|
| compliant control (the committed file) | `[]` | `[]` | **PASS** |
| invention, written BARE | `[]` | `['37.51234567890123']` | **RED** |
| invention, INSIDE BACKTICKS | `[]` | `['37.51234567890123']` | **RED** |
| invention, on the MARKER LINE | `[]` | `['37.51234567890123']` | **RED** |
| ROUNDING (`2.04` for the gap) | `['training.non_dp.wall_clock_gap_vs_superseded -> 2.035849685343305']` | `[]` | **RED** |
| OMISSION (`h_per_point_ceiling` dropped) | `['generation.h_per_point_ceiling -> 9.013691285839306']` | `[]` | **RED** |

This reproduces the plan's round-5 verification table row for row.

### The threshold — MEASURED, and one honest disclosure

`MIN_FRACTIONAL_DIGITS = 8`, and `LONG_FIGURE` is **built from it** — verified by AST that the name is
loaded inside the pattern assignment, not merely present elsewhere. At 8 the constructed pattern string
is byte-identical to the literal `\d[\d,]*\.\d{8,}(?:[eE][+-]?\d+)?`; re-binding to 12 yields `\d{12,}`,
so the tie is real.

Fractional-digit histogram, re-derived over the float leaves:

| source | 1-5 digits | **6-11** | 12-18 | total |
|---|---:|---:|---:|---:|
| the four source records | 130 | **0** | 259 | 389 |
| `results/phase23_cost.json` itself | 22 | **4** | 114 | 140 |

**DISCLOSED, NOT RE-TUNED — the cost record has FOUR leaves in the 6-11 band**, which the four source
records do not:

| digits | path | rendering |
|---:|---|---|
| 8 | `generation.mean_tokens_floor` | `29.16796875` |
| 6 | `generation.per_shape[0].mean_tokens_floor` | `25.234375` |
| 6 | `generation.per_shape[2].mean_tokens_floor` | `25.390625` |
| 6 | `generation.per_shape[3].mean_tokens_floor` | `33.203125` |

All four are mean token counts — sums of integers over 64 draws, therefore **exact binary rationals**,
the same population as the 1-5 band rather than continuous measured quantities. The bimodal argument is
about exact-rational versus continuous, and these fall on the exact-rational side despite being long,
so the separation the threshold relies on is intact. Two consequences, both benign: `29.16796875` sits
**at** the threshold and so *would* be matched by `LONG_FIGURE` — correct behaviour, since it is not
one of the eleven and publishing it would RED. And **none of the eleven lands in the 6-11 band** (all
are 12-16 digits), so the plan's narrower second residual — a pre-registered leaf too short for half
two to cover a forged copy of — does not arise. **The threshold is unchanged.**

### Sub-threshold numeral inventory — the disclosed residual, made auditable

An invented numeral with fewer than 8 fractional digits is **not caught**, by design: shape cannot
separate it from the numerals the prose legitimately carries, and closing that half would require an
allow-list. Instead, here is every numeral in the `.planning/REQUIREMENTS.md` slice below the
threshold, with the long figures and the 64-char sha256 masked out first, and what each one is:

| numeral(s) | what it is |
|---|---|
| `1` `2` `3` `4` `5` `6` `7` | the continuation's own section numbers **(1)**…**(7)** |
| `0` `8` `64` `8,` `64,` | fragments of `dp_n8` / `dp_n64` / `sigma=0` in the protocol labels, and mask boundaries in the table cells |
| `2026` `08` `28` | the marker's date `2026-08-28` |
| `23` `12` `11` | plan ids `23-12`, `23-11` |
| `01` `03` `04` `05` | requirement and decision ids `CAL-01`, `DPSGD-03`, `UNIT-04`, `CAL-05` |
| `17` | the **quoted falsified figure** *"~17 s per arm"* |
| `1,010` | the **quoted falsified figure** `~1,010×` |
| `4.77` | the h/point table's own column, quoted as the thing being disclosed as a floor |
| `18` | `Phase-18` |
| `45` `56` | the stop-terminated counts `45–56 of 64`, echoed from the committed CAL-05 row |
| `256` | the tail of the word `sha256` |
| `308` `1585` | line citations — `loop.py:308`, `teach_persona.py:1585` |
| `637` `641` | the `23-RESEARCH.md:637-641` range |

**Thirty-three distinct tokens, every one accounted for, and no stray rounding among them.** In
particular `2.04`, `161.12` and `79.14` — the three roundings the plan names by hand — do **not**
appear anywhere in any slice. Nothing here is a figure that should have been a pre-registered
full-precision leaf, so there is no Task 1 defect to escalate. **No allow-list was added.**

### The other two residuals, disclosed rather than patched

Stated in `_long_figures_not_sourced`'s docstring and repeated here:

- **A SIGN FLIP is not caught.** The pattern has no sign class, so `-2.035849685343305` matches as the
  required rendering and passes *both* halves. `[-−]?` is deliberately not added, because it makes a
  legitimate figure in a hyphenated range (`79-161.1239542257311`) match as a negative and FALSE-RED a
  correct continuation. All eleven published quantities are seconds, hours and ratios — all positive —
  so a negative rendering is nonsense a reader catches.
- **A NON-ASCII DECIMAL SEPARATOR is not caught.** `\.` matches only U+002E, so `37٫51234567890123`
  (U+066B) and `37．51234567890123` (U+FF0E) never match. The asymmetry is the useful half: Unicode
  **digits** around an ASCII point *are* caught, since `\d` is Unicode-aware by default.

Neither can displace a required figure — half one still demands all eleven renderings verbatim.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] My own STATE.md session-log entry duplicated a sentinel and broke the slice**

- **Found during:** the state update, by `test_cost_claim_correction_is_additive[.planning/STATE.md]`
- **Issue:** the session-log entry I wrote said *"each delimited by one `23-12-CONTINUATION-BEGIN` /
  `-END` sentinel pair"*, which put a **second** literal BEGIN sentinel in the file. `text.count(BEGIN)`
  went to **2** and `_continuation` refused. This is the exact failure the plan predicts — a duplicated
  sentinel makes the guard scan the wrong span — and it was caught **for real**, on my own writing,
  rather than only by the constructed tripwire.
- **Fix:** the log entry now describes the pair without repeating the marker strings, and says why.
- **Files modified:** `.planning/STATE.md`
- **Commit:** the final metadata commit

**2. [Rule 1 - Bug] The marker-position assertion read the FIRST marker, not one after the claim**

- **Found during:** the state update, by the same test
- **Issue:** `_MARKER.search(flat)` returns the file's first dated 23-12 marker. `.planning/STATE.md`'s
  `stopped_at:` frontmatter legitimately summarises this correction at byte **258**, far above the
  claim at **220845**, so the test RED-ed on a file whose continuation is perfectly additive. The
  plan's own wording is that a marker *"**exists** after the original claim's position"* — my first
  implementation asserted the strictly stronger *"the first marker in the file is after it"*, which has
  a measured false-RED channel and no extra teeth. `.planning/ROADMAP.md`'s plan-list entry would hit
  the same channel the moment it were written above `:46`.
- **Fix:** `_MARKER.search(flat, flat.index(claim))` — searched **from** the claim's position, with the
  reason recorded in a comment at the call site. Still fully-toothed: a file carrying the claim with
  only a marker *before* it finds nothing and REDs.
- **Files modified:** `tests/test_phase23_cost.py`
- **Commit:** the final metadata commit

Both were caught by this plan's own guard on this plan's own writing, before anything shipped.

### Deliberate departures from the plan text

**A. Two plan-stated baselines were re-measured and had drifted; the measured values are used.**
The plan states `grep -c "1,010"` = REQUIREMENTS 1 / ROADMAP **2** / STATE 1 and long-literal counts of
69 / **20** / **86**. Measured at `fc39f50` immediately before writing: **1 / 3 / 1** and **69 / 25 /
98**. 23-11 added a ROADMAP plan-list entry mentioning the figure and added long literals to both
ROADMAP and STATE. The plan explicitly instructs re-measuring these before Task 1 writes, and the
measured values are what this SUMMARY and the test docstring carry. No criterion changes sign.

**B. `scripts/_addendum.py` was not used.** Argued in full under Task 1 above — no `pending`/`recorded`
pair and no `## Verdict` section exists in a planning document, and the helper appends at end of file
rather than beside the corrected text. The plan permits this route explicitly and asks for the reason,
which is recorded here.

**C. Zero `gsd-sdk` mutation handlers were called.** The plan forbids them on these files, and 23-19's
recorded finding is that `roadmap.update-plan-progress` keys on SUMMARY existence and falsely ticked
23-17. All four planning files were hand-edited with `Edit` and diffed. **Zero corruptions to repair** —
this is the third consecutive session in the phase to skip every handler.

### Authentication gates

None.

---

## Requirements ticked

| requirement | route |
|---|---|
| **CAL-01** | checkbox `- [ ]` → `- [x]` + a SATISFIED note naming plans 23-10 / 23-11 / 23-12 and the artifact; traceability row filled. The tick records that the leg is **MEASURED**, not that the ~17 s estimate held — it did not, and the falsification is retracted in place above the row. |
| **CAL-05** | checkbox `- [ ]` → `- [x]` + a SATISFIED note naming plans 23-11 / 23-12; traceability row filled. Records that the committed 4.77 h/point sits **below the measured floor**, so the requirement's own words "a floor, not a mean" understate it. |

Both by hand. `requirements mark-complete` was **not** called — it is an SDK mutation handler on the
file this plan is correcting.

---

## State updates

Hand-edited and diffed, per the plan's prohibition:

- `.planning/STATE.md` frontmatter: `stopped_at` rewritten for 23-12, `last_updated` stamped,
  `completed_plans` **63 → 64**. `percent` left at 33 — it tracks completed *phases* (3 of 9), which
  did not move.
- `.planning/STATE.md` Current Position: `Plan: 11 of 20` → `12 of 20`, commit hashes updated,
  **16 → 17 of 20 plans ticked**. 23-17 deliberately stays **UNTICKED**, as every session since 23-18
  has recorded.
- `.planning/STATE.md` decisions: four entries added above 23-10's.
- `.planning/ROADMAP.md`: `- [ ] 23-12-PLAN.md` → `- [x]` with the execution note, in the Wave 7 list.

---

## Frozen pins — all clean

| check | result |
|---|---|
| `git diff --exit-code -- results/` | exit **0** |
| `git diff --exit-code -- scripts/phase23_prereg.py scripts/phase23_matched_prereg.py scripts/phase23_resume_prereg.py` | exit **0** |
| `git diff --exit-code -- scripts/mitigation_accountant.py scripts/mitigation_gate.py scripts/mitigation_budget.py` | exit **0** |
| `git diff --exit-code -- pyproject.toml` (RPT-03) | exit **0** |
| `git log --format=%H -- scripts/phase23_matched_prereg.py \| wc -l` | **1** |

No `results/phase23_*` artifact was touched. The correction lives in the planning documents; the
artifacts are the evidence it cites.

---

## Suite and lint

**`1571 passed, 1 skipped`** in 371s, against 23-11's recorded baseline of **`1559 passed, 1 skipped`**.
The **+12** are exactly the tests this plan added and nothing else:

| test | cases |
|---|---:|
| `test_cost_claim_correction_is_additive` | 3 |
| `test_the_correction_quotes_the_cost_record_faithfully` | 1 |
| `test_the_continuation_invents_no_figure` | 1 |
| `test_the_guard_catches_a_constructed_defect` | 5 |
| `test_no_file_carrying_the_claim_was_left_uncorrected` | 1 |
| `test_the_h_per_point_table_is_disclosed_as_a_floor` | 1 |
| **total** | **12** |

`make lint` exits 0 over **245** files. No regression against the baseline.

---

## Known Stubs

None. Every figure published in every continuation is a `repr()` of a leaf resolved from a
pre-registered field path of a committed artifact, asserted present verbatim by half one and asserted
sourced by half two.

## Threat Flags

None. No network endpoint, auth path, file-access pattern or trust-boundary schema change was
introduced — this plan writes Markdown and one test file. Zero package installs; `pyproject.toml`
byte-unchanged (RPT-03). Every `mitigate` disposition in the plan's threat register is implemented:
T-23-64 (deletion counts, all four named), T-23-64b (the projection named and its numerals kept out),
T-23-64c (protocols derived from the record, never hardcoded), T-23-65 / T-23-65b (directory scan over
the normalized claim text), T-23-66 / T-23-66b / T-23-66c (both halves, the sentinel slice, five
tripwire cases), T-23-67 (the ceiling disclosed beside the table), T-23-68 (every location resolved by
text), T-23-68b (zero SDK handlers).

---

## Self-Check: PASSED

Files claimed, verified on disk:

- `.planning/REQUIREMENTS.md` — FOUND
- `.planning/ROADMAP.md` — FOUND
- `.planning/STATE.md` — FOUND
- `tests/test_phase23_cost.py` — FOUND
- `results/phase23_cost.json` — FOUND (unmodified)

Commits claimed, verified in `git log`:

- `72ea546` — Task 1, the continuation in all three files — FOUND
- `81f0be2` — Task 2, the two-direction guard — FOUND

The working tree is clean apart from the user's own pre-existing `.gitignore` modification, which this
plan did not touch and did not stage.
