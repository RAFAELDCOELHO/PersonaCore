---
phase: 20
slug: pre-registration-the-three-condition-gate
status: blocked
threats_open: 1
asvs_level: 1
created: 2026-08-20
---

# Phase 20 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

**Register origin:** `register_authored_at_plan_time: true` — all twelve PLAN files carried a
parseable `<threat_model>` block, and every SUMMARY carried `## Threat Flags`. This audit therefore
**verified that the declared mitigations exist**; it did not build a retroactive STRIDE register.

**Gate status: BLOCKED.** `threats_open: 1`. **`T-20-19` is carried OPEN again at plan `20-13`
(2026-08-21), pending the D-38 magnitude bound** — `20-VERIFICATION.md` gap 2 reproduced two defeats
of the guard on which its `20-12` closure rests. See `### Open` below for both reproductions and the
named closing condition.
The three-item dated continuation landed across plans
`20-08` (the superseding module), `20-10` (the D-24 continuation artifact) and `20-11` (the armed
tripwires), and the two remaining threats were closed at `20-12` **against a re-run of the guards in
the closing process** — not against any SUMMARY. See *Blocking Remediation* below for the item-by-item
resolution.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| git object DAG ↔ the evidentiary record | The only boundary that matters this phase. A rule's authority comes from provably preceding the numbers it judges. | Commit SHAs, first-add ordering |
| `erasure_gate.py` (`23a830c`, closed) ↔ `mitigation_gate.py` | v3.0's closed pin is an immutable input. Any write across this boundary voids the milestone. | Imported constants and functions, by object identity |
| Phase 20 (rule) ↔ Phase 23 (measurement) | The extraction floor crosses this boundary. Phase 20 cannot measure it. | `extraction_noise_floor` + its provenance dict |
| Measured floor ↔ borrowed floor | An already-published number from a different quantity or regime is the cheapest way to make a criterion look rigorous while being wrong. | `retention_noise_floor`, `extraction_noise_floor` |
| outcome thresholds ↔ resource parameters | The gate/budget split — a resource calibration must never be mistakable for an outcome threshold. | Import graph: `mitigation_gate` must never import `mitigation_budget` |
| "we could not tell" ↔ "it did not work" | Collapsing INCONCLUSIVE into FAIL is the single most likely way this gate produces a dishonest negative. | Verdict strings and reason lists |
| a written branch ↔ a fired branch | A branch nobody has watched fire is a branch nobody has verified. | Six `__main__` outcomes + the CI twin |
| gitignored inputs ↔ CI | `checkpoints/` is gitignored, so CI can never re-derive the artifact. | Every reading, denominator, seed, adapter sha256 embedded in the JSON |
| a frozen pin ↔ its correction | A defect found in a pre-registration may be corrected only by a dated continuation beside it, never by an edit to it. | `results/phase20_gate_coverage_correction.{md,json}`, `scripts/phase20_gate_coverage.py` |
| a plan that says a thing will be done ↔ a guard that proves it was | Flipping a gate on the strength of a written plan is how a security gate goes green over a known wrong verdict. | This file's own `status` and `threats_open` |
| a published total ↔ the rows that substantiate it | A total counted from a prior audit but not carried by this file's own rows is phantom coverage. | The 66 register rows below |

---

## Threat Register

66 threats. **65 closed, 1 open.**

**THE COUNTING METHOD, stated once here and BINDING on `20-17` too** — two incompatible methods would
let a later reader re-derive a different total from the same rows. A threat is counted once per
DISTINCT `T-20-NN` id appearing **anywhere inside this file's register TABLES**, including the ids
enumerated inside a single cell of the grouped-by-plan table below, which are threats but not
row-starts. MEASURED at `5da028a`, this file's state immediately before the `20-13` flip: distinct
ids across table lines = **66** — the published total, which therefore already reconciles; table
lines that START with `| T-20-NN |` = **39**, carrying **35** distinct ids. Counting row-starts would
publish 35, contradicting the total this file already substantiates in the paragraph below. The
method is not changed here; it is written down. It is also why `### Open` names `T-20-19` in PROSE
rather than as a row: a second `| T-20-19 |` row-start there would make the count of rows at Status
`open` read 2 against a published 1.

**The total is substantiated by this file's own rows: `38` previously named `+ 8` inherited rows now
transcribed from the committed `20-05` / `20-06` registers `+ 20` new gap-closure threats `= 66`.**
Every one of the 66 is an actual row below, so the published total is no longer inherited from a
prior audit. The eight transcribed rows are `T-20-26`…`T-20-30` and `T-20-36`…`T-20-38`: they were
always counted in the earlier `46` and always enumerated by the inclusive ranges in the plan-grouped
table, and their full mitigation text was committed one directory over in `20-05-PLAN.md` /
`20-05-SUMMARY.md` and `20-06-PLAN.md` / `20-06-SUMMARY.md`. Each is copied from that source and
cites it, so the count reconciles by transcription rather than by disclosure.

### Open

**`T-20-19` — a v3.0-regime floor standing in for the v4.0 retention floor. RE-OPENED 2026-08-21 at
plan `20-13` (D-39).** Its register row is below, under *The two formerly-open threats*; that row's
`20-12` text is preserved byte-identically and only its Status cell moved back to `open`, with a
dated re-opening sentence appended beside the historical claim rather than over it.
**This entry is deliberately PROSE and not a table row.** `threats_open` must equal the count of
register ROWS whose Status cell reads `open`; a second `| T-20-19 |` row-start here would make that
count 2 against a published 1.

**What is open, in the present tense.** The declared mitigation refuses one bit pattern and one
caller-asserted string. `_prove_retention_floor` at `scripts/phase20_gate_coverage.py:353-406` never
constrains the floor's MAGNITUDE, and `20-VERIFICATION.md` gap 2 reproduced both consequences by
measurement. First: `0.06893 * (1 + 2**-50)` passes the
`retention_noise_floor != V20_RETENTION_NOISE_FLOOR` refusal at `:396-406` — float `!=` is
bit-pattern inequality, not numeric distinguishability — and buys a **BIT-IDENTICAL** `4.029`, the
exact borrowed cap, reaching `PASS` through `corrected_point_verdict`. Second, and needing no
malformed input at all: `retention_noise_floor=5.0` under clean
`{"regime": "adapter", "seeds": (1337, 2024)}` provenance reaches `PASS` at cap `13.89114` against
the governing `3.9085032379884783`. The control confirms the unperturbed `0.06893` IS refused, so the
guard exists, computes and is watched — its coverage is one bit wide. The harm T-20-19 names is *"the
looser cap a borrowing buys"*: a PROPERTY, guarded by a NAME.

**The closing condition, named here so a re-close that skips it contradicts this file.** The D-38
magnitude bound — `retention_noise_floor <= _ADAPTER_REGIME_RETENTION_FLOOR * (1.0 + 1e-9)`, which
admits every tighter floor a later phase measures and refuses the whole looser class — lands at plan
`20-15`, **and** its tripwires must be OBSERVED red-then-green against BOTH measured cases above,
`0.06893 * (1 + 2**-50)` and `5.0`. Only then is the row re-closed and `threats_open` returned to `0`,
at plan `20-17` (D-39). The flip and the re-close must not be the same commit.

**`T-20-21` is NOT re-opened.** It stays closed exactly as recorded at `20-12`, against a guard
watched failing in that closing process. This section re-opens one threat, not two.

### Closed

**Grouped by plan** (plans `20-01`…`20-07`); full mitigation text in each `20-0N-PLAN.md`
`<threat_model>` block and each `20-0N-SUMMARY.md` `## Threat Flags` table.

| Plan | Threat IDs | Category coverage | Status |
|------|-----------|-------------------|--------|
| 20-01 | T-20-01, T-20-02, T-20-03, T-20-04 | Repudiation, Tampering ×3 | closed |
| 20-01 | T-20-05, T-20-06 | Info disclosure, EoP — *disposition `accept`* | closed |
| 20-02 | T-20-07, T-20-08, T-20-09, T-20-10 | Spoofing, Tampering ×3 | closed |
| 20-02 | T-20-11 | Info disclosure — *disposition `accept`* | closed |
| 20-03 | T-20-12, T-20-13, T-20-14, T-20-15, T-20-16 | Repudiation ×2, Tampering ×3 | closed |
| 20-03 | T-20-17 | EoP — *disposition `accept`* | closed |
| 20-04 | T-20-18, T-20-20, T-20-22, T-20-23, T-20-24 | Tampering ×3, Spoofing ×2 | closed |
| 20-05 | T-20-25 … T-20-31 | Tampering ×4, EoP, Spoofing ×2 | closed |
| 20-05 | T-20-32 | Tampering — `accept` (this plan) / `mitigate` (downstream) | closed |
| 20-06 | T-20-33 … T-20-39 | EoP, Tampering ×3, Spoofing ×2, Repudiation | closed |
| 20-07 | T-20-40, T-20-41, T-20-42, T-20-43, T-20-44, T-20-46 | Repudiation ×3, Tampering ×3, Spoofing | closed |
| 20-07 | T-20-45 | Info disclosure — *disposition `accept`* | closed |

#### The two formerly-open threats, closed at `20-12`

The reproduction detail below is preserved **in the past tense**. A register that erases its own
findings on closure teaches the next audit nothing, and what was actually wrong is the whole value of
these two rows.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-20-21 | Repudiation | an INCONCLUSIVE silently reported as a FAIL, or vice versa | mitigate | **CLOSED at `20-12`.** *What was wrong, preserved:* the declared mitigation (three branches, each proved differentially against the counterfactual it overrides) was present and verified, but did not reach a **fourth** mislabeling path — GATE-06's sweep-coverage test decided on RAW rates (`mitigation_gate.py:798-812`) while condition (a) decided on `wilson_upper_bound(k, n)` (`:755`), against the same `ceiling`. Reproduced in **both** directions at n=104, X=0.04535522866494124: `FIXTURE_CLEARING_POINT` + `(1/104, 3/104)` brackets X under the (a) rule yet read as never-crossed → spurious `INCONCLUSIVE`; `FIXTURE_DESTROYED_MODEL` + `(3/104, 11/104)` read as covered while ZERO points cleared X → spurious `FAIL`. A third case in no prior report, `FIXTURE_CLEARING_POINT` + `(3/104, 11/104)`, returned `PASS` off that same truncated axis. No spurious `PASS` was constructible under self-consistent inputs. WR-09, the second hole in the same block: no `sweep_heldout_recalls` parameter existed in the 21-kwarg signature at all. *The closure:* `scripts/phase20_gate_coverage.py::coverage_verdict` decides each axis on the statistic that axis's criterion is decided on and decides BOTH Y legs, closing WR-09 in the same function (D-35); `corrected_point_verdict` is the one sanctioned route and has no `sweep_extraction_rates` parameter, so raw-rate space is unreachable through it. Published at `results/phase20_gate_coverage_correction.json` (`governs` / `supersedes`). **Watched by `tests/test_phase20_correction.py`** — both directions asserted RED against the frozen pin and GREEN through the correction in one differential body each — and watched FAILING in this closing process (row 6 of the Watched-RED table). `scripts/mitigation_gate.py` was NOT edited. | **closed** |
| T-20-19 | Spoofing | a v3.0-regime floor standing in for the v4.0 retention floor | mitigate | **CLOSED at `20-12`.** *What was wrong, preserved:* the declared mitigation was verified true — `V20_RETENTION_NOISE_FLOOR` is neither imported (AST: five names, absent) nor present as a numeric constant (`0.068930` absent) — but it did not cover the **caller-supplied** path. `extraction_ceiling` carried **3** `_prove` calls refusing wrong-arm / <2-seed / missing-provenance floors; `retention_cap` carried **0**. Measured: `retention_cap(retention_noise_floor=0.068930)` returned `4.029` — the *looser* cap — with no refusal. That was asymmetric against T-20-24, whose whole point is that `mitigation_point_verdict` calls `extraction_ceiling` itself so no path to a verdict skips the provenance check. *The closure:* `scripts/phase20_gate_coverage.py::_prove_retention_floor` supplies the four refusals the frozen function cannot be given — three mirroring `extraction_ceiling`'s at `mitigation_gate.py:417` / `:425` / `:436`, plus a fourth refusing `V20_RETENTION_NOISE_FLOOR` BY IDENTITY — and is called FIRST in `corrected_point_verdict`, before any compute, so it is a choke point and not an advisory. **Watched by `tests/test_phase20_correction.py::test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict`**, which drives all eight refusals THROUGH the route with a positive control, and which was watched FAILING in this closing process (row 8 of the Watched-RED table). GATE-02's traceability row is rewritten from RESIDUAL-OPEN to a discharge naming the same function and guard. **RE-OPENED 2026-08-21 at plan `20-13` (D-39).** Every character before this sentence is the `20-12` record, preserved byte-identically — what was wrong with it is recorded beside it rather than over it, the same additive discipline D-36 and the ROADMAP SC3 amendment used. `20-VERIFICATION.md` gap 2 defeated that closure twice, by measurement. (i) `0.06893 * (1 + 2**-50)` passes the `!=` refusal at `scripts/phase20_gate_coverage.py:396-406` and buys a **BIT-IDENTICAL** `4.029` — the exact borrowed cap — reaching `PASS`; the control confirms the unperturbed `0.06893` IS refused, so the refusal's coverage is one bit wide. (ii) `retention_noise_floor=5.0` under clean `{"regime": "adapter", "seeds": (1337, 2024)}` provenance reaches `PASS` at cap `13.89114` against the governing `3.9085032379884783`, with no malformed input at all — provenance is a caller assertion and nothing bounded magnitude. The guard refuses a NAME where this row's own named harm, "the looser cap a borrowing buys", is a PROPERTY. **The closing condition is stated in the `### Open` PARAGRAPH above — prose, deliberately not a second row for this id.** | **open** |

#### Transcribed from the committed `20-05` / `20-06` registers

These eight IDs were always inside the published total and always enumerated by the inclusive ranges
above. They were never written into this file as individual rows, which made the total look
unsubstantiated. Each row below is copied from the committed register it cites — no memory, no
reconstruction.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-20-26 | Elevation of privilege | the gate importing `mitigation_budget` to read K | mitigate | D-20 — K is a required kwarg on `promote_to_full_fidelity`; `20-06`'s AST guard asserts `"mitigation_budget" not in imported`. Re-verified at implementation: `imported == {'erasure_gate', 'pathlib', 'sys'}`, `mitigation_budget` absent. *Transcribed from `20-05-PLAN.md` and `20-05-SUMMARY.md`.* | closed |
| T-20-27 | Tampering | a GATE-10 branch chosen after seeing data | mitigate | Both named branches plus the fallback are committed at `20-05`, before either run; the `_CAPACITY_DISPATCH` is TOTAL over all four cleared-flag combinations with a module-scope `_prove`, so there is no fall-through to select into. *Transcribed from `20-05-PLAN.md` and `20-05-SUMMARY.md`.* | closed |
| T-20-28 | Spoofing | a third chosen constant smuggled in as the fallback tolerance | mitigate | D-26 — `fallback_epsilon_tolerance` has no committed value; taking the fallback route with it unset raises `SystemExit` naming **D-26** and **CAL-03**, observed firing. *Transcribed from `20-05-PLAN.md` and `20-05-SUMMARY.md`.* | closed |
| T-20-29 | Spoofing | the arm existential formed over the union of both arms | mitigate | `exists_clearing_point` `_prove`s single-arm membership across the whole point list **before computing anything**; the mixed-arm refusal was observed naming both arms. *Transcribed from `20-05-PLAN.md` and `20-05-SUMMARY.md`.* | closed |
| T-20-30 | Repudiation | a fixture reading as a second measurement of the Phase 19 experiment | mitigate | D-30 — the fixture's comment carries `D-30`, `FIXTURE`, `0.22362988653603388` and `77.637` and states it is never a second reading of the experiment; its four published fields are asserted EQUAL to the parsed `results/phase19_arm_erased.json` rather than transcribed, with `control_gap` written as the subtraction. *Transcribed from `20-05-PLAN.md` and `20-05-SUMMARY.md`.* | closed |
| T-20-36 | Tampering | an imported baseline retyped as a literal | mitigate | Six baselines asserted absent from the pin's numeric constants; the superseded cap absent both as a constant and as a substring; `MARGIN_K` asserted present in the import list; the supersession proved to be a bit-exact computation. *Transcribed from `20-06-PLAN.md` and `20-06-SUMMARY.md`.* | closed |
| T-20-37 | Spoofing | a fabricated number passing as a published M1 reading | mitigate | D-30 — the fixture's readings asserted EQUAL to the parsed `results/phase19_arm_erased.json`, with `retention_ppl` accessed by index `[0]` as the LIST it is and `control_gap` asserted as the subtraction rather than against a typed decimal. *Transcribed from `20-06-PLAN.md` and `20-06-SUMMARY.md`.* | closed |
| T-20-38 | Repudiation | a branch that only fires when a human runs the self-check | mitigate | Six outcomes re-asserted in CI against the SAME module-scope fixtures the `__main__` uses, plus the module run as a subprocess in a fresh interpreter so `_prove_verdict_domain()` and the `ARM_CLAIMS` proof re-execute instead of hitting a `sys.modules` cache. *Transcribed from `20-06-PLAN.md` and `20-06-SUMMARY.md`.* | closed |

#### New at the gap-closure plans `20-08` … `20-12`

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-20-48 | Elevation of privilege | a superseding module callers can bypass | mitigate | The correction has no authority a caller can be trusted to invoke. Enforced by the AST caller census `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module`, which matches BOTH `.id` and `.attr` — a bare-name matcher is invisible to the `module.function(...)` form a downstream driver actually writes — and is proved non-vacuous by asserting a match inside the sanctioned module. Measured green at zero bypassing callers, recorded as a state rather than skipped. Watched RED (row 7). *Declared at `20-08`, watched at `20-11`.* | closed |
| T-20-50 | Spoofing | `SUPERSEDED_SWEEP_SENTINEL` masking a genuine truncation | mitigate | A sentinel that neutralises the pin's GATE-06 branch could mask a genuine truncation if the corrected coverage test were skipped or wrong. Coverage is computed FIRST and a truncated result returns INCONCLUSIVE before the pin's verdict is trusted; `20-11` asserts across all three committed fixtures that the sentinel fires NO GATE-06 reason, so neutralising the superseded block is a proved property rather than an assumption. *Declared at `20-08`, proved at `20-11`.* | closed |
| T-20-53 | Tampering | a second copy of an imported estimator | mitigate | Proved per object by the mechanism that can actually FAIL for that object's type: `is`-identity across all three modules for `wilson_upper_bound` (a function) and for `F_Y` (the float `0.7`); AST import-alias membership plus absence from every module-scope `ast.Assign` target for `MARGIN_K` and `EXTRACTION_FLOOR_MIN_SEEDS`, both the small int `2` which CPython interns so an `is` check on them could not fail. X is obtained by calling `mitigation_gate.extraction_ceiling` itself, never recomputed. *Declared at `20-08`, proved at `20-11`.* | closed |
| T-20-54 | Repudiation | `wilson_lower_bound` misused as a deciding statistic on a floor | accept | Defined for REPORTING only, published alongside the deciding raw rate and never instead of it. Using it to decide Y coverage would re-introduce CR-01's defect class with the sign flipped. `COVERAGE_STATISTIC_BY_AXIS` names the deciding statistic per axis, so the misuse is contradicted by module data rather than only by prose. Accepted risk **R-20-05**. *Declared at `20-08`.* | closed |
| T-20-52 | Repudiation | the D-36 in-place amendment to a pre-registration record | mitigate | An amendment to a pre-registration reads as post-hoc licence unless it is dated, additive and provably against the amender's interest. All three enforced: the original `4.029000` stays byte-identical above the block, the block carries its plan attribution and date, and it states the measured arithmetic — `3.9085032379884783 < 4.029` from a floor `7.939763314393305x` smaller — showing the amendment makes condition (c) HARDER. *Declared and discharged at `20-09`.* | closed |
| T-20-55 | Tampering | a traceability note naming a guard that does not exist | mitigate | A note pointing at a non-existent guard is worse than an empty note — it manufactures the appearance of coverage. Enforced mechanically: the check AST-walks `scripts/mitigation_gate.py` for `FunctionDef` / module-scope `Assign` names and `tests/test_phase20_prereg.py` for `test_*` names and asserts each note resolves at least one backticked token into EACH set, plus that every row was visited. An AST resolution, not the `X in source` substring test that failed four times in this phase. *Declared and discharged at `20-09`.* | closed |
| T-20-56 | Repudiation | re-checking already-checked boxes | accept | The eight boxes were checked at `0f265e2`. Touching them again would make one discharge look like two in the commit record. Not touched; asserted unchanged. Accepted risk **R-20-06**. *Declared at `20-09`.* | closed |
| T-20-63 | Repudiation | a verify assertion that passes on text the file already contained | mitigate | MEASURED before writing: `2026-08-20` occurred 4x in `20-CONTEXT.md`, and `3.9085032379884783` / `0.008681618994239138` / `0.06893` were already in `.planning/REQUIREMENTS.md`. Both checks asserting them were therefore SCOPED to the span the plan itself wrote, so each can only pass on new text. The same discipline governs `20-12`: `T-20-21` and `T-20-19` were already present in this file as OPEN threats, so every assertion about their closure is scoped to their ROW rather than to the file. *Declared at `20-09`, carried into `20-12`.* | closed |
| T-20-47 | Repudiation | the correction is itself post-hoc | mitigate | It was written after the failures were reproduced, so it could in principle be shaped to license a preferred verdict. Refuted in the artifact itself: BOTH the pin's verdict and the corrected verdict are published for every case, and the correction only ever moves a verdict toward `INCONCLUSIVE` or restores a genuinely bracketed reading — never toward `PASS` from a truncated axis. The `direction_ii_on_clearing_fixture` row DEMOTES a `PASS`, against the amender's interest, and ships anyway. *Declared and discharged at `20-10`.* | closed |
| T-20-49 | Tampering | an addendum that alters published text | mitigate | `append_addendum`'s three checks run on the PRODUCED BYTES: exactly one placeholder, an unchanged `## Verdict` section, and original-prefix-plus-addendum. `recorded_verdict` was asserted non-`None` on BOTH sides — before the append at Task 1 and after it at Task 2 — because `None == None` would make that guard vacuous. `20-11`'s additivity guard proves the same against a pre-append revision DERIVED from `git log`. *Declared at `20-10`, proved at `20-11`.* | closed |
| T-20-51 | Tampering | a hand-typed float drifting from the code | mitigate | The correction JSON was generated by a throwaway script that imports the three modules and calls them; no float was typed. `20-11` re-derives every published number by calling the modules, and the artifact's `cap` was edited and watched firing (row 9). *Declared at `20-10`, watched at `20-11`.* | closed |
| T-20-57 | Repudiation | a defect description outliving its defect | mitigate | Every `recorded_not_corrected` entry carries a `stale_when` field saying what would make its description false, and `test_the_three_defects_are_still_live_in_the_frozen_pin` asserts each against the CODE with a message stating that a green result means the continuation needs RE-READING, not deleting. *Declared at `20-10`, proved at `20-11`.* | closed |
| T-20-58 | Tampering | the new artifact reddening the ancestry guard | accept | It cannot: the first add of each `results/phase20_gate_coverage_correction.*` file lands after all nine pin commits `95b3c8a`…`abf9072`. Accepted rather than mitigated because the guard IS the mitigation — asserted green by running `tests/test_phase20_prereg.py` rather than reasoned about. Accepted risk **R-20-07**. *Declared at `20-10`.* | closed |
| T-20-64 | Repudiation | a two-commit rule enforced by a check that passes on one commit | mitigate | MEASURED: `git ls-files` prints the path for a staged-but-never-committed file while `git log` prints nothing, so an `ls-files` guard would have passed on exactly the state its own message forbids. Both `20-10` tasks and `20-11`'s additivity guard therefore assert on the object actually consumed: `git log --format=%H -- <path>` for the revision list and `git show <rev>:<path>` for the blob. `git ls-files` is never used. *Declared at `20-10`, proved at `20-11`.* | closed |
| T-20-59 | Tampering | an audit that matches the prose explaining the pattern | mitigate | Every audit in `tests/test_phase20_correction.py` is an AST walk. No `grep -c` and no `X in source` substring check appears anywhere in it; the only substring assertions are on runtime `SystemExit` messages and on published `.md` / `.json` artifacts, never on source. This phase produced four instances of that exact defect class, recorded in `.planning/REQUIREMENTS.md`'s `| RPT-02 |` row. *Declared and discharged at `20-11`.* | closed |
| T-20-65 | Repudiation | a test-suite guard that passes on a degraded suite | mitigate | A bare `pytest <file> -q` exits 0 on a single passing test, so a file that silently loses a test or degrades one to a skip would satisfy it while the acceptance criteria claim "at least N passing, zero skips". Every verify block runs pytest as a subprocess and asserts the exit code, the extracted passing COUNT against its floor, the EXACT prereg count, and the absence of `skipped` / `xfail`. *Declared and discharged at `20-11`.* | closed |
| T-20-60 | Repudiation | a gate flipped green ahead of its evidence | mitigate | Both `20-12` tasks ran the guards BEFORE editing and would have stopped on failure: `tests/test_phase20_correction.py` + `tests/test_phase20_prereg.py` re-run in the closing process, `29 passed`, zero skips, and `git diff --exit-code` on both frozen files returning 0. Every acceptance criterion asserts the observed state of the file rather than the intent of the edit, and each of `T-20-47`…`T-20-66` is checked BY NAME as a register row rather than trusted to the published total. The four Watched-RED breaks were **re-run in this process** rather than transcribed from `20-11-SUMMARY.md`, and one of them was observed producing a materially different result (row 6). *Declared and discharged at `20-12`.* | closed |
| T-20-61 | Tampering | a closure that erases the finding it closes | mitigate | The original reproduction detail for `T-20-21` and `T-20-19` is preserved in the past tense inside their closed rows, and each closure names the guard that watches it. The same rule governs the two record halves: ROADMAP SC3's original text is byte-identical above its amendment (the ROADMAP diff at `20-12` is 40 insertions and 0 deletions) and the GATE-02 requirement bullet keeps its D-36 amendment intact. *Declared and discharged at `20-12`.* | closed |
| T-20-62 | Repudiation | an accepted risk that never reaches the Accepted Risks Log | mitigate | This file's own line — "accepted risks do not resurface in future audit runs" — is only true if they are logged. R-20-05, R-20-06 and R-20-07 are logged below with rationales and dates, and no R- entry is written for a `mitigate` disposition. The same reasoning forced the eight inherited rows to be TRANSCRIBED rather than disclosed: eight IDs counted in a published total but carried by no row are phantom coverage that resurfaces in the next audit, and the mitigation text was committed one directory over, so transcription cost nothing and fabricated nothing. *Declared and discharged at `20-12`.* | closed |
| T-20-66 | Repudiation | an amendment that mis-states its own direction of movement | mitigate | MEASURED across all three cases: direction (i) `INCONCLUSIVE → PASS`, direction (ii) `FAIL → INCONCLUSIVE`, third case `PASS → INCONCLUSIVE`. On the favourability ordering `FAIL < INCONCLUSIVE < PASS` the first two BOTH move toward a more favourable verdict, so an earlier draft's "in both directions" would have been an over-claim published inside an anti-over-claim amendment. The SC3 block says "Not uniformly tighter", attributes the tightening solely to the third demoted case, and names criterion-matching as the justification; the verify asserts `DEMOTED`, `FIXTURE_CLEARING_POINT` and `criterion-match` present and `TIGHTER` absent, so the corrected claim is machine-checked rather than trusted to prose review. *Declared and discharged at `20-12`.* | closed |

**Watched-RED evidence (mitigations observed failing, then restored byte-identically):**

| Threat ID | Deliberate break | Observed |
|-----------|------------------|----------|
| T-20-33 | `import mitigation_budget` added to the pin | AST guard fired; reverted byte-identical |
| T-20-34 | local `def wilson_upper_bound` shadowing the import | both static and `is`-identity halves fired |
| T-20-35 | `THIRD_CONSTANT = 0.9` added at module scope | `_module_scope_floats` audit fired |
| T-20-03 | verdict relabel | `_prove_verdict_domain()` raised `SystemExit` at import (exit 1) |
| T-20-13 | `git rm` + re-add of a `phase20_*` artifact | earliest-add SHA byte-identical to the pre-delete state — laundering provably impossible |
| T-20-21 | `coverage_verdict`'s extraction statistic flipped from `wilson_upper_bound(k, n)` to `k / n` in `scripts/phase20_gate_coverage.py` | **Re-run at `20-12`, not transcribed. BOTH direction tests failed.** Direction (i): `AssertionError: the corrected route returns 'INCONCLUSIVE' where the frozen block returns 'INCONCLUSIVE'. A would-be PASS stays DEMOTED … 2 clearing, 0 failing` / `assert 'INCONCLUSIVE' == 'PASS'`. Direction (ii): `AssertionError: the corrected route returns 'FAIL' on a sweep where ZERO points clear X = 0.04535522866494124 (bounds (0.0699987834827904, 0.16574570864872762))` / `assert 'FAIL' == 'INCONCLUSIVE'`. Whole file: **`4 failed, 7 passed`** — see the note below. Restored byte-identically (`shasum -a 256` equal, `git diff --exit-code` 0) |
| T-20-48 | `scripts/_scratch_bypass_probe.py` added, calling `mitigation_gate.mitigation_point_verdict(...)` — the `ast.Attribute` form | **Re-run at `20-12`. Census fired:** `AssertionError: 1 call site(s) reach a v4.0 verdict through the frozen pin directly, bypassing scripts/phase20_gate_coverage.py::corrected_point_verdict: ['scripts/_scratch_bypass_probe.py:7']` / `assert ['scripts/_sc...s_probe.py:7'] == []`. Positive control: the same test returned `1 passed` the moment the scratch file was removed. This is precisely the form a bare-name matcher would have missed (WR-07) |
| T-20-19 | the distinct-seed `_prove` deleted from `_prove_retention_floor` (8 lines removed) | **Re-run at `20-12`: `Failed: DID NOT RAISE <class 'SystemExit'>`** on `test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` (`tests/test_phase20_correction.py:777`). Restored byte-identically |
| T-20-51 | `results/phase20_retention_floor.json`'s `cap` edited at the 16th significant digit (`…4783` → `…4793`) | **Re-run at `20-12`. WR-02 fired:** `AssertionError: the artifact publishes cap 3.908503237988479 but retention_cap on its own published floor returns 3.9085032379884783`. `1 failed, 10 passed`. Restored byte-identically |

A guard nobody has watched fail is a guard nobody has verified; all nine above were watched, and the
four gap-closure rows were **re-run in `20-12`'s own process** rather than copied from
`20-11-SUMMARY.md` — which is the same discipline `T-20-60` names.

**One re-run diverged from the record, and the divergence is published rather than smoothed.**
`20-11-SUMMARY.md` records the `T-20-21` break as `2 failed, 3 passed`. Re-run against the COMPLETE
11-test file it is `4 failed, 7 passed`: `20-11` took that break during its Task 1, when the file held
five tests, so the same break now additionally reddens
`test_every_published_number_re_derives_from_the_modules` and the positive control inside
`test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict`. The load-bearing claim is
unchanged and strengthened — both direction tests still fail, with the assertion text above — and the
guard is broader than recorded, not narrower. `20-11`'s sub-resolution measurement was also
re-confirmed here: `3.9085032379884782 == 3.9085032379884783` is `True`, so an edit at the last
printed digit produces the identical double and the `T-20-51` break must be taken at the 16th
significant digit to exist at all.

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-20-01 | T-20-05, T-20-11 | No network, no secrets, no untrusted input anywhere in the pin. `_git` passes an argv tuple and never uses `shell=True`, so a glob containing a shell metacharacter reaches git as a pathspec. | Plan-time disposition, verified in implementation | 2026-08-20 |
| R-20-02 | T-20-06 | D-33, explicitly. Future-phase artifact prefixes cannot be asserted present in `V4_ARTIFACT_GLOBS` — an assertion catches an empty match set, never an incomplete one. Accepted in exchange for never asserting coverage this phase cannot demonstrate; recorded in the tuple's own comment. | Plan-time disposition (D-33) | 2026-08-20 |
| R-20-03 | T-20-17 | `git merge-base --is-ancestor X X` is reflexive (measured, exit 0), so a gate and artifact in the SAME commit would pass. D-08's strictly-after rule is a recorded **discipline** tighter than the mechanism. Stated in the fixture docstring so a later reader treats same-commit as neither a defect nor a licence. Not exercised: the pin and artifact landed in distinct commits (`abf9072` → `9bb34ad`). | Plan-time disposition (D-08) | 2026-08-20 |
| R-20-04 | T-20-45 | `checkpoints/` is gitignored by design (`.gitignore:14-15`), so CI can never re-derive `results/phase20_retention_floor.json`. Mitigated by embedding every reading, denominator, seed, adapter path, adapter sha256, git SHA, torch version and device in the JSON — 25 provenance keys. | Plan-time disposition (D-32) | 2026-08-20 |
| R-20-05 | T-20-54 | `wilson_lower_bound` ships in `scripts/phase20_gate_coverage.py` for REPORTING only — published alongside the deciding raw rate, never instead of it. Using it to decide Y coverage would re-introduce CR-01's defect class with the sign flipped, which is exactly what D-37 declines to do. The residual is that a future reader could still misuse it; accepted because `COVERAGE_STATISTIC_BY_AXIS` names the deciding statistic per axis, so the misuse is contradicted by module DATA and not only by the docstring. | Plan-time disposition (D-37), verified in implementation at `20-08` | 2026-08-21 |
| R-20-06 | T-20-56 | The eight requirement boxes GATE-01/03/04/05/07/08/09/10 were checked at `0f265e2`. Re-checking them at `20-09` would make one discharge look like two in the commit record and would inflate the bookkeeping phase's apparent yield. Accepted: they were left untouched and asserted unchanged rather than re-marked. | Plan-time disposition, verified at `20-09` | 2026-08-21 |
| R-20-07 | T-20-58 | The new `results/phase20_gate_coverage_correction.{md,json}` files cannot redden the ancestry guard — their first adds land after all nine pin commits `95b3c8a`…`abf9072`. Accepted rather than mitigated because the guard IS the mitigation: `tests/test_phase20_prereg.py` was run green as an acceptance criterion after each commit rather than reasoned about. | Plan-time disposition, verified at `20-10` | 2026-08-21 |

*Accepted risks do not resurface in future audit runs.*

**T-20-21 and T-20-19 were never accepted risks, and are not now.** They were open defects with
reproductions, deliberately left open across `20-08`…`20-11` rather than logged as accepted —
accepting a realized mislabeling defect would have made the security gate green over a known wrong
verdict. They are closed here on the opposite basis: a mitigation that exists, and that was watched
failing when deliberately broken.

---

## Blocking Remediation — RESOLVED

`scripts/mitigation_gate.py` is **permanently uneditable** — `results/phase20_retention_floor.json`
was committed at `9bb34ad`, and the frozen-pin guard
(`test_phase20_prereg_is_frozen_before_every_phase20_result`) takes `adds[-1]`, the earliest add.
Plan 20-03 proved across five observed states that `git rm` plus re-add reproduces that SHA
byte-identically. The only legal correction path was a **dated continuation** via
`scripts/_addendum.py::append_addendum(path, addendum, *, pending, recorded)` — both keywords
required — plus an armed tripwire test (D-24). **That is the path that was taken. The pin was not
edited: `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` returns 0, and
`tests/test_phase20_prereg.py` is green, so the pre-registration survives its own correction.**

Phase advancement is **no longer blocked**. The three items were bound to one gap-closure phase and
closed together, as required:

| # | Item | Threat | Requirement | Resolution |
|---|------|--------|-------------|------------|
| 1 | GATE-06's coverage test uses `wilson_upper_bound(k, n)`, matching what condition (a) already uses, on both axes — eliminating both reproduced failure modes | T-20-21 | GATE-06 | **RESOLVED.** `scripts/phase20_gate_coverage.py::coverage_verdict` at `20-08` decides the extraction axis on `wilson_upper_bound(k, n)`, the statistic condition (a) decides on. Both reproduced directions watched RED-then-GREEN by `tests/test_phase20_correction.py` at `20-11`, re-run at `20-12` |
| 2 | `sweep_heldout_recalls` added at the caller, covering the held-out leg SC2 makes load-bearing and which today has no coverage check at all (`grep -c` = 0 in the 21-kwarg signature) | T-20-21 | GATE-06 | **RESOLVED.** The same `coverage_verdict` decides BOTH Y legs (D-35), and `corrected_point_verdict` carries `sweep_heldout_recalls` as a required keyword argument. Its truncation case is asserted at the artifact's own `(0.30, 0.28)` sweep |
| 3 | A provenance tripwire on `retention_cap`, **mirroring the three `_prove` calls that already protect `extraction_ceiling`** — the same asymmetry T-20-19 identified, corrected with the same structural discipline rather than merely documented | T-20-19 | GATE-02 residual | **RESOLVED.** `scripts/phase20_gate_coverage.py::_prove_retention_floor` at `20-08` carries four `_prove` calls — three mirroring `mitigation_gate.py:417` / `:425` / `:436`, plus a fourth refusing the borrowed floor by identity — called first in `corrected_point_verdict` so it is a choke point. Its eight-case refusal suite at `20-11` was watched firing, re-run at `20-12` |

The armed tripwire was required to prove **RED-then-GREEN against both reproduced cases** —
`(1/104, 3/104)` and `(3/104, 11/104)` — not merely against the happy case. It does, in one
differential body each, plus a third case that appears in no prior report and demotes a `PASS`.

Entry point taken: `/gsd:plan-phase 20 --gaps`, executed as plans `20-08` … `20-12`. The GATE-06 row
in `.planning/REQUIREMENTS.md` now carries the discharge; the reproduction detail is preserved there
in the past tense.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-20 | 46 | 44 | 2 | `/gsd:secure-phase 20` — orchestrator, State B (create) from plan-time register |
| 2026-08-21 | 66 | 66 | 0 | `/gsd:plan-phase 20 --gaps` → plans `20-08`, `20-09`, `20-10`, `20-11`, `20-12`. Totals reconciled to this file's own rows: 38 previously named + 8 transcribed from `20-05` / `20-06` + 20 new gap-closure threats |
| 2026-08-21 | 66 | 65 | 1 | `/gsd:plan-phase 20 --gaps` (wave 2) — plan `20-13`, `T-20-19` re-opened against `20-VERIFICATION.md` gap 2 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed — 66 of 66 closed, `### Open` empty
- [ ] `status: verified` set in frontmatter

**Approval WITHDRAWN 2026-08-21 at plan `20-13` (D-39), pending plan `20-17`.** The two boxes above
were checked at `20-12` and are now false: `T-20-19` is open, the register reads 65 closed / 1 open,
and the frontmatter reads `status: blocked`. They are unchecked rather than rewritten, and the `20-12`
approval paragraph below is left byte-identical — it is the record of what was approved then, and of
the evidence it was approved on. Re-approval is gated on the condition named in `### Open`: the D-38
magnitude bound at plan `20-15` AND its tripwires observed red-then-green against both measured cases.

**Approval:** approved at plan `20-12` (2026-08-21). The three-item dated continuation was discharged
by plans `20-08` (`scripts/phase20_gate_coverage.py`), `20-10`
(`results/phase20_gate_coverage_correction.{md,json}`) and `20-11`
(`tests/test_phase20_correction.py`), and this file was flipped only after the following commands
were run in the approving process and their output observed:

- `.venv/bin/python -m pytest tests/test_phase20_correction.py tests/test_phase20_prereg.py -q` →
  `29 passed in 2.66s`, zero skips, zero xfail.
- `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` → exit 0; both frozen
  files byte-identical to their pinned commits.
- The four gap-closure Watched-RED breaks above, each applied, observed failing, and restored
  byte-identically (`shasum -a 256` equal and `git diff --exit-code -- results/ scripts/` exit 0
  afterwards).
- `.venv/bin/python -m pytest -q` → the full suite, green against its recorded baseline.
