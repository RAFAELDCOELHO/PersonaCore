# Phase 20: Pre-Registration — The Three-Condition Gate - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 20 delivers **`scripts/mitigation_gate.py`** — a stdlib-only, phase-neutral, keyword-only
decision module returning `PASS` / `FAIL` / `INCONCLUSIVE` for a sweep point against three
conditions — plus **`scripts/_prose.py::normalized`** (RPT-02) and a **CPU-only ancestry test**
asserting the gate module's first-add precedes every v4.0 results artifact.

**No measurement happens in this phase.** The artifact is a rule. Its entire evidentiary value is
the ordering: `erasure_gate.py` was committed at `23a830c` before Phase 16 ran, and the v4.0 gate
must be committed and pushed before *any* v4.0 number exists — **before the Phase 23 cost
calibration, not merely before the Phase 25 sweep**.

Requirements: GATE-01 … GATE-10, CAL-04, RPT-02.

**A finding that reshaped this phase, established during discussion.** The v4.0 research
(`.planning/research/SUMMARY.md` R5) cites Phase 19's measured 77.6% dialogue-adaptation
destruction at `:445` as an argument *for* a one-sided condition (c) — and prescribes
`erasure_gate`'s exact one-sided cap form. But `results/phase19_erasure_report.md:446-450`
used the same number to reach the opposite conclusion: **a one-sided perplexity cap, anchored
either way, cannot separate "capability preserved" from "adaptation removed."** That finding is
published in three places, addressed in none, and carried into no requirement. GATE-02 and
ROADMAP SC1 inherit the indicted form verbatim. This CONTEXT supersedes that form — see D-01.

</domain>

<decisions>
## Implementation Decisions

### Condition (c) — form and anchors

- **D-01 — (c)'s dialogue leg is a BAND ON THE ON−OFF ADAPTATION GAP, not on raw PPL.**
  `gap = point_ppl_on − point_ppl_off`, and (c)-dialogue clears iff
  `f_C × control_gap ≤ gap ≤ control_gap + MARGIN_K × gap_noise_floor`.
  This measures directly the quantity `19-16` identified as missing — how much adaptation
  survives — instead of raw PPL, which collapses directionally between "capability preserved" and
  "adaptation removed."
  **Measured justification, from `results/phase19_arm_erased.json` and
  `results/phase19_noise_floors.json`:** against the literal GATE-02 cap `4.5837288963367`, the
  *untouched taught adapter* reads `5.815445876712191` and **fails by +1.231717 before any
  mitigation runs**, while M1 — which destroyed 77.637% of the adaptation — reads
  `4.851119149910443` and fails by only +0.267390. Retaining the literal cap as a band's upper
  bound is not merely tight, it **selects for destruction**: the only readings inside
  `[4.5733, 4.5837]` are adapters flattened back to adapter-off.

- **D-02 — `control_gap` is the v4.0 RETRAINED CONTROL's own gap, supplied as a REQUIRED KWARG,
  never hardcoded.** Same discipline PROJECT.md:187-189 applies to Y: v2.0's published numbers
  belong to a different training run and would confound the comparison with run-to-run variance.

- **D-03 — (c)'s upper bound is DERIVED, and its derived form is ADDITIVE, not fractional.**
  `gap ≤ control_gap + MARGIN_K × gap_noise_floor`, the project-wide k=2 discipline
  (Phase 13 `MARGIN`, `erasure_gate`'s caps, Phase 19 (b)). `MARGIN_K` is **imported** from
  `erasure_gate`, never retyped. Do **not** spell this as a `hi_frac` — it is not a fraction, and
  dressing a derived additive quantity as one would misrepresent it.

- **D-04 — the gap form costs ZERO new constants, proven exactly.** Because
  `adapter_off_identical_across_seeds` is `true`, `noise(gap) ≡ noise(ppl_on)` by construction:
  `|gap₁₃₃₇ − gap₂₀₂₄| = 0.005214448168350039`, **bit-identical** to the already-committed
  `dialogue_ppl_noise_floor`. GATE-02's "import, never retype" survives unchanged.

- **D-05 — (c)'s legs are ASYMMETRIC IN FORM, BY DESIGN, and the reason is recorded in the pin.**
  Dialogue = the gap band above. Retention = a **one-sided upper cap**. The dialogue gap is
  sign-stable (always positive, direction known); the retention gap **changes sign inside the
  already-measured range** — taught `+0.3286199167186572`, M1 `−0.22022225029414155` — which makes
  a symmetric band geometrically incoherent for that leg specifically. Record the asymmetry with
  its reason so a later "unify the two legs" refactor goes red rather than looking like cleanup.

- **D-06 — the retention floor is RE-MEASURED in the adapter regime, never borrowed.**
  `V20_RETENTION_NOISE_FLOOR = 0.068930` is a **Phase 12 full-fine-tune** seed pair governing an
  adapter-regime verdict. Phase 19 explicitly recorded that the full-fine-tune *dialogue* floor
  `0.001704` "does NOT govern any Phase 19 verdict" — the retention floor inherited the same defect
  unremarked.
  **Measured during this discussion** (two seeds, no retraining, `n_targets = 1000285` each, on the
  committed `phase19_erase_dialogue_floor_seed{1337,2024}` arms):

  | seed | `adapter_off` | `adapter_on` | gap |
  |---|---|---|---|
  | 1337 | 3.891139975617828 | 4.219759892336485 | 0.3286199167186572 |
  | 2024 | 3.891139975617828 | 4.2284415113307245 | 0.33730153571289634 |

  **adapter-regime retention noise floor = `0.008681618994239138`** — the borrowed value is
  **7.939763314393305×** larger. The re-measurement makes the cap **tighter**
  (`3.9085032379884783` vs `4.029000`), not looser, so it is not a change that buys an easier pass.
  It also sits within 1.66× of the dialogue floor: two instruments, same regime, comparable noise.
  The Phase 12 number was the outlier.
  **Free bit-identity control:** seed 1337 reproduced `results/phase19_noise_floors.json`'s
  published readings byte-for-byte before producing a new number — the instrument is verified,
  not assumed.
  **Two bounds, stated not glossed:** `n = 2` seeds, one difference between two draws, no
  confidence interval (the same status the committed `dialogue_ppl_noise_floor` already has); and
  measured on the **v3.0 persona recipe** (`n_facts=10`, `replay_ratio=1.0`) — the right *regime*,
  not a v4.0 *arm*. Both are why D-07 keeps it a kwarg.

- **D-07 — the retention floor stays a REQUIRED KWARG in the gate, never a literal.**

- **D-08 — the retention floor artifact is `results/phase20_retention_floor.json`, committed
  STRICTLY AFTER `scripts/mitigation_gate.py` exists — never before.** This rule is **tighter than
  the guard mechanically requires**: `git merge-base --is-ancestor` is reflexive, so gate and
  artifact in the *same* commit would pass. Recorded as a discipline so nobody later reads
  same-commit as either a defect or as permission.

### X — the extraction ceiling

- **D-09 — `X = wilson_upper_bound(nt_successes, n) + MARGIN_K × extraction_noise_floor`.**
  The never-taught floor read as a **Wilson upper bound on the control arm** (not the raw rate),
  plus the k=2 margin imported from `erasure_gate`. **Zero chosen constants** — every term is
  measured or imported. `wilson_upper_bound` is imported **by object identity**, never redefined.
  The unit is **QUESTIONS**, never draws (`erasure_gate`'s locked unit).

- **D-10 — `ERASURE_GOAL_FRAMING`'s rejection of "indistinguishable from never-having-learned"
  does NOT transfer here, and the reason is recorded.** That rejection targets an unverifiable
  post-hoc assertion about an already-observed erasure result. v4.0's claim is categorically
  different: a mathematical guarantee built into the DP-SGD mechanism. The distinction is written
  into the pin so a reader does not read D-09 as reopening a claim this repo committed against.

- **D-11 — reachability is BY CONSTRUCTION, recorded as a deliberate strengthening over Phase 19,
  not as an omitted protection.** `wilson_upper_bound` was verified **non-decreasing across all
  105 outcomes at n=104**, so `X > wilson_upper(0, n)` always and a perfect mitigation always
  clears. Phase 19 needed an explicit clamp (`ERASURE_FLOOR_MIN`, `floor_branch`); this
  construction makes one unnecessary. Reachability ladder for sizing:
  `n=27 → 0.091079`, `n=52 → 0.049456`, **`n=104 → 0.025355`**, `n=208 → 0.012840`,
  `n=416 → 0.006462`.

- **D-12 — `MARGIN_K` multiplies an EXTRACTION noise floor measured on the never-taught arm,
  two-seed protocol** — the same pattern used for the dialogue and retention floors.
  **Never** the Phase 19 (b) floor `0.14814814814814814`, which measures non-target recall variance
  under ablation: wrong quantity, wrong regime, and it would set `X = 0.321652`, tolerating
  **25/104 = 24.04%** leakage. Borrowing it is the identical error D-06 corrects.
  **The margin swings the criterion by 25×**, so it is not a detail. At n=104 the criterion is
  quantized by the question count: a floor below `0.008298` tolerates **zero** leaked questions —
  the 19-03 "clears ONLY on a PERFECT ERASURE" regime.

- **D-13 — the extraction floor is NOT measurable in Phase 20, and X is never a literal.**
  Verified: no never-taught adapter exists in `checkpoints/`; CTRL-03 is **Phase 23**
  (`REQUIREMENTS.md:300`, `ROADMAP.md:261`); its corpus is **Phase 21** UNIT-01…06, which the
  roadmap marks *NEEDS DESIGN*. Cost once runnable: 42,480 draws = 4.77 h/point at K=48, ~9.5 h for
  two seeds. Running it now would produce a **genuine v4.0 arm before the gate exists** — strictly
  worse than the ordering violation ruled out in D-08. (The retention probe was legitimate because
  it only **re-read existing v3.0 adapters** with a second instrument.)
  Since every input is a kwarg, **there is nothing to lock and therefore nothing to measure first.**
  The pin commits the formula, the unit, the estimator, and the floor's provenance requirement.

- **D-14 — the Phase 23 floor obligation travels as CODE, not prose.** Both committed **now**:
  (a) an **armed tripwire** — the gate refuses to compute X unless `extraction_noise_floor` arrives
  with provenance naming both seeds and the never-taught arm; a borrowed or single-seed floor
  **raises**, never passes silently (W1's choke-point pattern, not a per-call-site check);
  (b) a **committed tolerance reporter** translating the computed X into gate-strength language
  (`X = 0.321652 → tolerated 25/104`, or the equivalent for whatever value emerges), so the Phase 23
  report can never omit how strong or weak the accepted criterion actually was
  (Phase 19 `floor_branch()` precedent).

### Y, and the two chosen constants

- **D-15 — Y's fraction CANNOT be derived, and that is named rather than disguised.** X and (c)'s
  upper bound came out fully derived. Y cannot: a k=2-derived Y would read "recall must be
  statistically indistinguishable from the un-mitigated control" — a demand for a free lunch that
  makes the gate vacuous in the opposite direction (guaranteed FAIL for any real mitigation). Y's
  fraction **encodes how much personalization the milestone will spend to buy privacy.** That is a
  preference, and committing it before any data is exactly what a pre-registration is for.

- **D-16 — `f_Y = 0.7`, applied to BOTH legs of Y, each against its OWN retrained-control value.**
  `Y_taught ≥ f_Y × control_taught_recall` and `Y_heldout ≥ f_Y × control_heldout_recall`.
  Using one fraction against each leg's own control value **reproduces the generalization ratio for
  free**, with no second constant and without borrowing v2.0's `0.3483 / 0.4921 = 0.707783` — which
  GATE-04 forbids. (Noted: GATE-04's worked example `0.7` sits 0.0078 from that ratio; likely its
  origin.) Locked now, before any Phase 23/25 curve point exists — the STAT-05 discipline.

- **D-17 — `f_C = 0.5`, SEPARATE from `f_Y`, governing (c)'s retained gap.** Condition (c) stays a
  **catastrophe detector**, distinct from Y as the **utility target** — the distinction
  `erasure_gate` states textually ("because (a) and (b) can BOTH be satisfied by a model that has
  been degraded into uselessness"). Binding them to one number would also assert a coupling the repo
  has **measured to be absent** (Phase 13 and Phase 19 both recorded these instruments diverging).
  **Hard non-vacuity floor, measured: `f_C > 0.2237`** — M1 retained `0.22362988653603388` of the
  dialogue gap, so any lower value fails to reject the one destruction event this project has
  actually measured. `f_C = 0.5` sits **2.24×** above it: real margin, not glued to the floor.

- **D-18 — exactly TWO chosen constants exist in the whole pin (`f_Y`, `f_C`), and both are labelled
  in the source as milestone PREFERENCE, not derivation.** Everything else is measured, imported, or
  computed. A reviewer auditing the pin should find exactly two numbers to argue with.

### K, the promotion rule, and the gate/budget split

- **D-19 — the CAL-04 / CAL-02 contradiction is resolved by a CLOSED MENU + RATCHET.**
  The sources genuinely conflict, and CAL-04 conflicts with itself: sentence 1 says "before any v4.0
  artifact exists" (Phase 20), sentence 3 says "before the first point is drawn" (Phase 25), while
  CAL-02 and `ROADMAP.md:139-144` put per-point K in `mitigation_budget.py` sized from the Phase 23
  measurement. Resolution:
  - **`K_RUNGS = (48, 24, 16, 8)`** — a closed, ordered tuple literal committed **now**, satisfying
    CAL-04 sentence 1.
  - **Phase 23 selects the actual rung by measured throughput**, satisfying CAL-05 (4.77 h/point is
    a **floor for noised points, not a mean** — the rate was measured on the un-adapted base where
    45–56 of 64 draws per shape terminated on a stop id).
  - **RATCHET: a selected K may only INCREASE, never decrease, once fixed** — structurally
    eliminating the post-null K reduction that `phase18_extraction.py:88-92` records as the ATK-03 /
    P18-4 weakening. Fewer draws means less power to observe extraction, i.e. an easier null.

- **D-20 — the promotion rule lives in the GATE and takes K as a REQUIRED KWARG.** It decides
  whether a point *counts*, so it is an outcome rule — but the AST guard forbids the gate importing
  the budget. The kwarg resolves both: `mitigation_gate.py` **never** imports
  `mitigation_budget.py`, and the AST guard stays intact.

### Module structure, guards, and the ordering mechanism

- **D-21 — the ancestry guard must copy the PHASE 18 SHAPE, not Phase 16's.** Two shapes exist:
  `tests/test_phase16_prereg.py:209` uses `assert checked` over a **working-tree glob** — **RED
  whenever nothing committed matched**; `:387` + `:399` use `git ls-files` with
  `checked == len(prereg) × len(tracked)` **and** `bool(checked) == bool(tracked_artifacts)` —
  **green while zero artifacts are tracked, demanding non-zero from the first one onward.**
  Phase 20 arms its guard *before any v4.0 artifact exists*; under Phase 16's shape the test is red
  from the gate's first commit until an artifact lands, **inverting the ordering this phase exists
  to establish**. The code says so itself at `:396-398`.

- **D-22 — `V4_ARTIFACT_GLOBS` must explicitly include the `phase20_*` prefix, proven RED-then-GREEN
  as a COMMITTED TEST FIXTURE in a throwaway repo, re-executed every CI run.** Not assumed correct
  by reading the pattern. **The real project history stays clean — no v4.0-named probe ever touches
  `git log --diff-filter=A -- 'results/phase20_*'`.**
  **Four guard states measured during discussion, in a throwaway repo:**

  | state | result |
  |---|---|
  | probe committed, no pin yet | RED via `assert prereg_commits` — **a different red** |
  | pin committed second | **RED with the ordering message** — this is the proof the glob sees the prefix |
  | `git rm` probe, not re-added | **GREEN**, tracked=0 — the red **is reversible** |
  | re-add at identical path | **RED again, first-add unchanged** — laundering is impossible |
  | probe gone, real artifact after pin | **GREEN**, tracked=1 checked=1 |

  Phase 16's recorded lesson applies: a phase writing results under a new prefix **must be added**
  to the globs — an `assert` catches an empty match set, never an incomplete one.

- **D-23 — `scripts/_prose.py` sits OUTSIDE the pin's scanned set**, same precedent as
  `scripts/_addendum.py`. A phase-neutral general utility must not freeze behind the first artifact
  of one specific phase — it has to keep serving Phases 21–28 without inheriting an immutability
  that only makes sense for the judgment rule itself.
  **Mechanism, verified:** `_addendum.py`, `_verdict.py` and `_prose.py` are matched by **none** of
  `phase16_*.py` / `phase17_*.py` / `phase18_*.py` / `phase19_*.py` — the **leading underscore is
  the mechanism**. Honest caveat: the precedent is **structural (fnmatch), not historical** —
  `_addendum.py`'s last commit (2026-08-17) predates the first `results/phase19_*` add
  (2026-08-18), so neither helper has actually been edited post-artifact.

- **D-24 — corrections to the closed pin are DATED CONTINUATIONS via `scripts/_addendum.py`, never
  edits.** Once any `results/phase20_*` artifact is committed, editing `mitigation_gate.py` turns
  the ancestry guard **permanently red**, and `git rm` + re-add cannot undo it (the guard takes
  `adds[-1]`, the *earliest* add). Make any correction **machine-readable** (Phase 19 used
  `results/phase19_calibration_correction.json` with a `governs:` field) and **arm a tripwire test**
  that fires when a later plan would consume the wrong value — a prose note gets missed.

### GATE-10 — the capacity comparison rule

- **D-25 — equivalence is STRUCTURAL, by identical inputs: same `σ`, same steps, same `δ`, same
  `q`.** Not a calibrated approximation. `ε` is a deterministic function of those parameters, so
  comparing at identical mechanism parameters **is** comparing at equivalent `ε_fact`, with **zero
  tolerance constant**. This preserves capacity (`N`) as the only genuinely free variable between
  the two compared points.

- **D-26 — the fallback branch is committed NOW, so neither branch is selectable after seeing
  data.** If CAL-03 **falsifies** the "ε is independent of N at q=1" premise (research marks it
  `[INFERENCE]`, not measured), the rule falls back to matched-ε within a tolerance.
  **EXPLICIT PENDING DECISION:** that fallback tolerance is a third chosen constant and is
  deliberately **not** set here. It must be decided **before Phase 21's CAL-03 runs** and named as
  such — not left implicit inside D-25. Flagged rather than smuggled, per the standard applied to
  `f_C` earlier in this discussion.

- **D-27 — both GATE-10 branches are publishable and neither may be chosen after seeing data.**
  Recovery at n=64 that n=8 did not achieve at equivalent `ε_fact` is a finding about where capacity
  stops destroying the mitigation; no recovery confirms the null at two capacities.

### Resolved during planning — conflicts surfaced by `20-RESEARCH.md`

*Added 2026-08-20, after research verified CONTEXT's citations against the source. Each of these
resolves a conflict the discussion did not see, and each is LOCKED on the same terms as D-01…D-30.*

- **D-31 — the verdict domain is RELABELLED WITH A PROVED MAP, not silently retyped.**
  `erasure_gate.py:136` defines `VERDICTS = ("SUCCESS", "FAILURE", "INCONCLUSIVE")`, while GATE-01
  and ROADMAP SC1 both require `PASS` / `FAIL` / `INCONCLUSIVE`. This is the one tuple the phase
  **cannot** import, inside a phase whose discipline is "import, never retype." Resolution:
  `mitigation_gate.py` declares `V4_VERDICTS = ("PASS", "FAIL", "INCONCLUSIVE")` beside an explicit
  `_VERDICT_RELABEL` mapping, and a module-scope **`_prove_verdict_domain()` runs at import** and
  asserts three things: **equal length**, **correct positional correspondence** against
  `erasure_gate.VERDICTS`, and **`INCONCLUSIVE` preserved identically in both vocabularies**.
  Correct v4.0 names without a silent duplicate of the original tuple — the discipline is kept by
  *proving the relationship*, not by asserting it in a comment a refactor can break.
  *Precedent: the module-scope `_prove` pattern already used for dispatch tables and reachability.*

- **D-32 — `results/phase20_retention_floor.json` is PRODUCED BY A COMMITTED DRIVER, not
  transcribed.** D-06's second input — seed-2024 retention `4.2284415113307245` — was verified to
  exist in **no committed artifact**, only in this CONTEXT. Transcribing it would publish a number
  whose only provenance is a discussion transcript, which is precisely the standard `<specifics>`
  forbids. Resolution: a **fifth deliverable** — an **unpinned driver**, same pattern as
  `scripts/phase19_run.py` — re-reads the two already-committed-arm adapters
  (`phase19_erase_dialogue_floor_seed{1337,2024}`, present locally, gitignored) with the retention
  instrument, runs on **MPS**, and writes the artifact, **committed STRICTLY after the pin per
  D-08**. It must reproduce `seed_1337 = 4.219759892336485` and `seed_2024 = 4.2284415113307245`
  **from real code**, not from discussion text. **One MPS run, no retraining** — the same
  "re-read existing v3.0 adapters with a second instrument" legitimacy D-13 already granted.
  Unpinned because it is a measurement driver, not a judgment rule (the D-23 / `phase19_floor.py`
  two-file split).

- **D-33 — `V4_ARTIFACT_GLOBS` contains `phase20_*` ONLY.** Pre-declaring `phase21_*`…`phase28_*`
  was considered and **rejected**: only `phase20_*` can be proven RED-then-GREEN by D-22's
  throwaway-repo fixture, and an advance declaration without demonstration is exactly the kind of
  unproven assertion this phase exists to refuse. Each future phase (21→28) **adds its own prefix at
  the moment it first writes results**, following Phase 16's recorded lesson literally — real proof
  per prefix. The cost is named, not hidden: an `assert` catches an empty match set, never an
  incomplete one, so a future phase that forgets its prefix fails silently. That risk is accepted in
  exchange for never asserting coverage this phase cannot demonstrate.

### Resolved during gap closure — decisions forced by 20-VERIFICATION.md

*Added 2026-08-20, after `20-VERIFICATION.md` reproduced the GATE-06 (CR-01 / WR-09) and T-20-19
defects against the running code rather than against a SUMMARY, and the gap-closure plans were
written. Recorded here at plan `20-09` — the whole of gap-closure wave 1, which `20-08` declares
`depends_on`, so no shipped artifact cites one of these IDs before its record exists. Each is LOCKED
on the same terms as D-01…D-33.*

- **D-34 — the GATE-06 correction is a REAL COMPUTATION in unpinned code, not a caller convention.**
  The rejected alternative was a documented calling convention plus a tripwire asserting that callers
  comply. It was rejected on two measured grounds: a convention cannot supply the held-out leg at all
  (there is no `sweep_heldout_recalls` parameter in the frozen 21-kwarg signature to hold it), and its
  tripwire could only assert COMPLIANCE, never COMPUTE the correction — so a compliant caller passing
  a wrong sweep still gets a wrong verdict. Resolution: `scripts/phase20_gate_coverage.py` computes
  coverage itself, and `corrected_point_verdict` is the sanctioned route. The cost is named rather
  than hidden: that route has no authority a Phase 23/25 caller cannot simply decline to invoke, so
  the AST caller census in `tests/test_phase20_correction.py` is what enforces it.

- **D-35 — WR-09's held-out leg closes in the SAME function and by the SAME discipline as the taught
  leg.** Not a separate work item, not a partially accepted risk, not a follow-on phase.
  `coverage_verdict` decides taught and held-out coverage in one body against one rule. ROADMAP SC2
  makes the held-out leg load-bearing; splitting its coverage check out would leave the load-bearing
  half guarded by a plan rather than by code.

- **D-36 — GATE-02's pre-registration TEXT is amended IN PLACE, dated, and additively.** This repo's
  convention is that pre-registration requirement text is not edited — which is why the supersession
  originally lived only in the traceability row. The amendment is accepted here on four grounds, all
  four required together: it is DATED, it is IN PLACE (so `grep 4.029000` cannot miss it), it is
  ADDITIVE (the original text stays byte-identical above it), and it is provably TIGHTER
  (`3.9085032379884783 < 4.029`, from a floor `7.939763314393305x` smaller — a self-serving amendment
  moves a threshold the other way). *Precedent: ROADMAP SC1 already carries exactly this shape, for
  exactly this number, from D-06 at plan `20-07`.*

- **D-37 — the coverage statistic is chosen by CRITERION-MATCHING per axis, not by "always use
  Wilson".** X is a ceiling and condition (a) decides on `wilson_upper_bound(k, n)`, so X coverage
  reads the Wilson upper bound. Both Y legs are floors and condition (b) decides on the RAW recall
  with no bound, so Y coverage reads the raw recall. A Wilson LOWER bound on a floor would decide
  coverage on a statistic the criterion does not read — CR-01's own defect class with the sign
  flipped — and would invert the conservatism of a floor. `wilson_lower_bound` is therefore defined
  for REPORTING only, published alongside and never instead of the deciding statistic, in
  `erasure_gate`'s own `rule_of_three` register. The cost is recorded and deliberately NOT fixed: the
  Y legs inherit condition (b)'s lack of a confidence bound, and fixing that would mean moving a
  pre-registered threshold after seeing the data it governs.

### Resolved during gap-closure wave 2 — decisions forced by the 2026-08-21 re-verification

*Added 2026-08-21, after `20-VERIFICATION.md` returned `gaps_found` at 5/6 must-haves and reproduced
both remaining holes in its own process rather than reading them off a SUMMARY. Recorded here at plan
`20-13`, which every later plan in this wave-set declares `depends_on`, so no shipped artifact cites
one of these IDs before its record exists. Each is LOCKED on the same terms as D-01…D-37.*

- **D-38 — the retention floor is refused by PROPERTY as well as by NAME.**
  `_prove_retention_floor` keeps its existing `retention_noise_floor != V20_RETENTION_NOISE_FLOOR`
  refusal at `scripts/phase20_gate_coverage.py:396-406` **and** gains a magnitude bound
  `retention_noise_floor <= _ADAPTER_REGIME_RETENTION_FLOOR * (1.0 + 1e-9)`, placed AFTER it. The two
  together are the one named value refused by identity plus the entire looser class refused by
  magnitude — of which `V20_RETENTION_NOISE_FLOOR` is **one member rather than the definition**.
  **Measured, re-derived at `20-13` by calling the committed modules, never transcribed:**
  `0.06893 * (1 + 2**-50)` = `0.06893000000000006` passes the `!=` (it is a different bit pattern)
  and buys a **BIT-IDENTICAL** `4.029` — `retention_cap(nudged) == retention_cap(0.06893)` is
  `True` — reaching `PASS` through `corrected_point_verdict`; the control confirms the unperturbed
  `0.06893` **is** refused, so the mechanism exists and computes, and its coverage is one bit wide.
  Separately, and with no malformed input at all, `retention_noise_floor=5.0` under clean
  `{"regime": "adapter", "seeds": (1337, 2024)}` provenance reaches `PASS` at cap `13.89114` against
  the governing `3.9085032379884783`. Provenance is a caller assertion; nothing bounded magnitude.
  **This also answers `20-VERIFICATION.md`'s escalation 1 BY ELIMINATION.** That escalation asks
  whether a rule authored 2026-08-21 to judge a floor measured 2026-08-20 is a D-24 dated
  continuation or a post-hoc rule. The question is well-posed against an IDENTITY rule, which names a
  single already-known value and could have been written to admit a preferred competitor. It does not
  arise for a PROPERTY bound: a magnitude bound authored after the measurement cannot be tuned toward
  a favourable answer, because every value it admits is TIGHTER than the committed measurement and a
  tighter floor buys a tighter cap. Taking the bound removes gap 2 and the policy question together.

- **D-39 — the security register is flipped OPEN first, and re-closed only on watched-RED evidence.**
  Stated as a requirement on the PLAN GRAPH, not as an intention: the flip to `threats_open: 1` is
  **this plan, `20-13`, wave 12**; the re-close to `threats_open: 0` is **plan `20-17`, wave 16**, and
  is gated on the D-38 magnitude bound's tripwires having been **OBSERVED red-then-green against BOTH
  measured cases** — `0.06893 * (1 + 2**-50)` and `5.0`. They must not be the same commit. The reason
  is this phase's own trust boundary at `20-SECURITY.md:39` — *"a plan that says a thing will be done
  ↔ a guard that proves it was."* At HEAD that file publishes `status: verified` / `threats_open: 0`
  over a guard the re-verification defeated twice by measurement; a register that publishes a closure
  it cannot substantiate is the exact failure its own boundary names. Flipping it open is therefore
  the FIRST act of this wave-set, not the last — a gate that goes honest only after its remediation
  lands was never carrying the state it published.

- **D-40 — both gaps close in this pass; the Y hole is NOT deferred to Phase 23.** This is the dated
  decision `20-VERIFICATION.md`'s human-verification item 2 (`:80-82`) asks for. What closes, in
  full: a per-element `[0.0, 1.0]` range `_prove` on **both** Y legs — which subsumes NaN with no
  special-case check, because `0.0 <= float("nan") <= 1.0` is `False` (measured) — the measured
  route-level differential armed as a tripwire (`(0.30, 0.28)` → `INCONCLUSIVE` carrying a GATE-06
  reason, versus `(nan, 0.28)` → `PASS` carrying none, on the identical axis against
  `Y_heldout = 0.24499999999999997`; `nan >= criterion` is `False`, so the NaN is COUNTED as a
  failing point and actively manufactures the bracket rather than merely passing through), the
  `isinstance(k, int) and not isinstance(k, bool)` count guard replacing the integral-float
  acceptance at `scripts/phase20_gate_coverage.py:257`, and D-38's magnitude bound.
  **The reachability finding is recorded honestly rather than used as an excuse:** no committed
  caller reaches `corrected_point_verdict` today — grepping `scripts/` and `src/` outside its own
  module returns nothing — so the hole does not block Phase 21. It closes now anyway, because
  Phase 23 is where sweep width is set and coverage stops being hypothetical, and a rule closed
  before its first consumer is the whole point of a pre-registration.

- **D-41 — the sanctioned route's TEST HARNESS supplies the governing retention floor; the bound's
  tolerance is never widened to admit a fixture.** Forced by a measurement neither the code review
  nor the verification recorded, and stated as a measurement. `mitigation_gate`'s **three** committed
  fixtures — `FIXTURE_DESTROYED_MODEL` (`:1237`), `FIXTURE_CLEARING_POINT` (`:1267`) and
  `FIXTURE_TRUNCATED_SWEEP`, which inherits the key through `**FIXTURE_DESTROYED_MODEL` — all carry
  `retention_noise_floor = 0.009`, and
  `0.009 > 0.008681618994239138 * (1.0 + 1e-9) = 0.008681619002920757`, so **D-38's bound REFUSES
  this repository's own fixtures.** The fixture floor is `1.0366729991228745x` looser than the
  measured adapter-regime floor and buys cap `3.90914` against the governing `3.9085032379884783`.
  **Two routes were available and one is rejected in writing.** Widening the tolerance until `0.009`
  passes is rejected outright: tuning a bound's tolerance to admit a value already in hand is exactly
  the researcher degree of freedom D-38 exists to remove, and it would make the bound's first act a
  concession to the fixture it was written to judge. **The taken route** is that
  `tests/test_phase20_correction.py::_corrected_call` supplies the governing floor READ from
  `results/phase20_retention_floor.json::retention_ppl_noise_floor`, in the same `base` dict
  (`:136-139`) that already supplies the two arguments the frozen fixtures cannot
  (`sweep_heldout_recalls`, `retention_floor_provenance`).
  **The against-interest half, recorded rather than omitted:** every published verdict is
  BIT-UNCHANGED under the substitution — `direction_i` `PASS`, `direction_ii` `INCONCLUSIVE`,
  `direction_ii_on_clearing_fixture` `INCONCLUSIVE` and `heldout_coverage` `INCONCLUSIVE`, all four
  measured at BOTH floors at `20-13`. The bound buys no verdict change here, so it cannot be read as
  having been taken for the answer it produces. `mitigation_gate.py` is frozen and its fixtures
  cannot be edited, so the bound's FIRST catch is a ~3.67% loosening inside this repository that no
  name-based refusal could ever have seen.

### Claude's Discretion

Accepted as proposed, with the precedent cited for each so a reviewer can contest any of them
explicitly:

- **D-28 — GATE-07, arm identity.** `arm` is a **required kwarg** from a closed
  `ARMS = ("dp", "adversarial")`; the verdict carries it; the ∃ is computed **per arm** and
  `exists_clearing_point` **refuses a mixed-arm point list**, so "∃ a point" over the union cannot
  be formed. A module-scope `_prove` asserts the claim-string table equals `ARMS` — a name with no
  claim string is a name a later plan must add code for.
  *Precedent: Phase 19 B7, where `SUBCOMMANDS` and the dispatch table are proved equal at module
  scope.* A DP point clearing carries a formal claim; an adversarial point clearing carries an
  explicitly non-formal one.

- **D-29 — GATE-08, provisional.** The verdict domain stays **exactly three** (GATE-01). A point
  clearing all three conditions **without** second-seed replication returns **`INCONCLUSIVE`**, not
  `PASS`. The replication argument is **required with no default**, so it cannot be silently
  omitted.
  *Precedent: `zero_results_have_nll` — identical shape, and INCONCLUSIVE already takes precedence
  over FAIL.*
  **A `PASS` carrying a `provisional=True` field was explicitly REJECTED**: it would collapse the
  three-verdict domain into four disguised states and reintroduce exactly the misreading risk
  `zero_results_have_nll` was designed to eliminate (a truthy-pair return silently disarming the
  branch that needed to fire).

- **D-30 — GATE-09, the destroyed-model fixture.** Built from Phase 19's **real published M1
  readings** — dialogue `4.851119149910443`, retention `3.6709177253236867`, 77.637% destruction —
  not fabricated numbers. A catastrophe that actually happened is not hypothetical. **Labelled a
  fixture, never a second reading of the experiment.**
  *Precedent: 19-16 ran its counterfactual through the committed gate exactly this way, labelled as
  operating on fabricated inputs so it could not be read as a second opinion.*

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The template and the rule Phase 20 extends
- `scripts/erasure_gate.py` — **THE template.** The four imported constants
  (`V20_MASKED_DIALOGUE_VAL_PPL` 4.5733, `V20_EWC_RETENTION_PPL` 3.891140,
  `V20_RETENTION_NOISE_FLOOR` 0.068930, `MARGIN_K` 2), `wilson_upper_bound`, `rule_of_three`,
  the keyword-only signature shape, the 3-verdict domain and the INCONCLUSIVE-precedence rule.
  Committed `23a830c` and **MUST NOT be amended**.
  **Citation corrected 2026-08-20 by `20-RESEARCH.md`:** the `:454-458` cited above **does not
  exist — the file is 291 lines.** The non-amendment is enforced by a **test**,
  `tests/test_phase18_prereg.py:212` (which checks both `git log == [PREREG_COMMIT]` and
  byte-identity against `git show`), **not** by self-statement. The nearest self-statement is
  `scripts/erasure_gate.py:71-73`, and it is scoped to the baselines block only. Trust the test,
  not the prose. Other corrected citations: `phase18_extraction.py:88-92` → **`:84-93`**;
  `test_phase16_prereg.py:45-60` → **`:46-63`**; `:322-399` → **`:322-403`**; `_GATE_MODULES` is
  **not** in `scripts/phase17_*.py` — it lives in `tests/` (`test_phase17_stats.py:62`,
  `test_phase18_prereg.py:59`), which matters because `mitigation_gate.py` matches no `phase20_*.py`
  glob, so D-20's AST guard needs an **explicit path constant**.
- `scripts/erasure_gate.py:95-127` — `ERASURE_DECISION_RULE`, especially clause (a)'s
  procedure-vs-constant sentence and clause (c)'s "degraded into uselessness" rationale.
- `scripts/erasure_gate.py:130-134` — `ERASURE_GOAL_FRAMING`, the claim D-10 explains does not
  transfer.

### The (c) finding this phase supersedes
- `results/phase19_erasure_report.md:355-466` — the (c) root-cause dated continuation. The
  both-readings table at `:420-426`; the non-discrimination finding at `:446-450`; the
  "what is explicitly NOT being claimed" list at `:452-466`.
- `docs/REPORT.md:1174`, `:1214-1215` — the published 77.637% and the "anchored either way"
  sentence.
- `.planning/research/SUMMARY.md:439-527` — R5, which cites the same number toward the **opposite**
  conclusion. Read alongside the report, not instead of it.

### Measured inputs
- `results/phase19_noise_floors.json` — `dialogue_ppl_noise_floor` `0.005214448168350039` and the
  `retention_ppl_pre_erasure` block (`adapter_off` 3.891139975617828 / `adapter_on`
  4.219759892336485).
- `results/phase19_dialogue_floor.json` — the two-seed protocol reused for the retention floor.
- `results/phase19_arm_erased.json` — `pre_erasure.dialogue_ppl` / `retention_ppl` and the M1
  post-erasure readings.
- `results/phase14_recall_report.md:462` — the published `4.5733 → 5.8154` (+27.16%) adapter-on
  dialogue cost, and the v2.0 recall pair 0.4921 / 0.3483.

### The ordering mechanism
- `tests/test_phase16_prereg.py:45-60` — `PREREG_COMMIT` and `V3_ARTIFACT_GLOBS`, with the comment
  explaining why a new prefix must be added.
- `tests/test_phase16_prereg.py:176-215` — the Phase 16 shape. **Do not copy** (D-21).
- `tests/test_phase16_prereg.py:322-399` — the Phase 18 shape. **This is the one to copy** (D-21);
  see `:396-398` for the reason in its own words.
- `scripts/_addendum.py` — the dated-continuation mechanism (D-24). `scripts/_verdict.py` — the
  anchored verdict-section read, for the report surface.

### Requirements and roadmap
- `.planning/REQUIREMENTS.md:21-56` — GATE-01…GATE-10 with the ordering rationale.
- `.planning/REQUIREMENTS.md:113-144` — the K / cost table and CAL-01…CAL-05 (note the CAL-04 vs
  CAL-02 conflict resolved by D-19).
- `.planning/REQUIREMENTS.md:218-220` — RPT-02; `:221-223` — RPT-03 (zero new runtime deps).
- `.planning/ROADMAP.md:133-144` — phase-zero ordering and the pre-registration boundary.
- `.planning/ROADMAP.md:148-188` — Phase 20 goal, dependencies and the five success criteria.
- `.planning/PROJECT.md:190-214` — the three-condition gate and the pre-registration boundary.

### Anti-weakening precedent
- `scripts/phase18_extraction.py:88-92` — the ATK-03 / P18-4 record on reducing K after seeing a
  null, and "pre-flight is the one moment the pin leaves open for it." The basis for D-19's ratchet.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`erasure_gate.wilson_upper_bound` / `rule_of_three`** — import by **object identity**, never
  redefine. A second definition is a second estimator; Phase 19 pinned this by identity for exactly
  that reason.
- **`erasure_gate.MARGIN_K`** — the k=2 discipline used by D-03, D-09 and D-12.
- **`scripts/_addendum.py::append_addendum`** — the only sanctioned correction path (D-24). Note it
  **refuses once the marker is already RECORDED**, so a second append must be written directly with
  the same three properties checked on the produced bytes.
- **`scripts/_verdict.py::VERDICT_SECTION`** — anchored section read; never
  `split("## Verdict")[-1]`.
- **`personacore.evaluation.perplexity.retention_perplexity`** and
  **`personacore.lora.adapter_disabled`** — the ON/OFF scoring pair used to produce D-06's floor;
  `phase19_erasure.dialogue_ppl_pair` (`:2704-2729`) is the committed shape, including its
  denominator `_prove`.
- **`phase14_recall.load_adapted_model`** — the load-before-inject, `weights_only=True` path every
  threshold-setting measurement must come off.

### Established Patterns
- **Keyword-only, no defaults, every condition rendered into a reason string** — so a caller cannot
  transpose two counts.
- **Constants imported, never retyped**; measured anchors arrive as **required kwargs**. Every
  anchor in this phase follows it: `control_gap`, the retention floor, the extraction floor, K.
- **Module-scope `_prove`** for facts that must hold at import (dispatch tables, reachability), so a
  dead gate fails at import rather than after the compute it would waste.
- **AST scans over a GLOB, not a hand-listed tuple** (Phase 17 `_GATE_MODULES`) so later drivers
  enter every scan automatically.
- **No fact values in a pin** — key by slot, never by `fact_id`; every core fact id embeds its own
  locked value. Applies to any fixture literal in `mitigation_gate.py`.
- **Deliberate-RED then byte-identical restore** — a guard nobody has watched fail is a guard nobody
  has verified. Record the sha256 both times.
- **Over-claim avoidance** — do not mark a requirement complete in the first plan that touches it.
  Applied six times across Phases 17 and 19.

### Integration Points
- `scripts/mitigation_gate.py` — **new**, the pin. Outcome thresholds only.
- `scripts/mitigation_budget.py` — **Phase 23**, resources only. An **AST guard forbids the gate
  importing it**, so the distinction is a fact about the import graph rather than a paragraph.
- `scripts/_prose.py` — **new**, phase-neutral, outside the pin (D-23). `normalized` must find a
  line-wrapped phrase that `grep -c` reports as absent.
- `tests/test_phase20_prereg.py` — **new**, CPU-only. Phase 18 shape (D-21) plus the throwaway-repo
  RED-then-GREEN fixture (D-22).
- `results/phase20_retention_floor.json` — **new**, lands strictly after the pin (D-08), **produced
  by the D-32 driver**, never transcribed.
- **The retention-floor driver** — **new, unpinned**, `scripts/phase19_run.py` pattern (D-32). The
  fifth deliverable. Re-reads the two `phase19_erase_dialogue_floor_seed{1337,2024}` adapters with
  the retention instrument on MPS; **no retraining**. Committed strictly after the pin.
- `pyproject.toml` — **untouched**; RPT-03 keeps the sha256 pin carrying forward, making it four
  milestones. `tests/test_package.py` turns red on any new dependency.

</code_context>

<specifics>
## Specific Ideas

- **The pin must name what it cannot do.** Where a criterion's strength depends on a
  later-measured floor, a **committed reporter** publishes the strength into the report (D-14), so
  no verdict is published without the reader learning how hard the bar actually was. Phase 19's
  `floor_branch()` exists because a criterion's strength should not be invisible in its own report.
- **Every measured number in this CONTEXT came with its denominator and its provenance**, and the
  two weakest (n=2 seeds; v3.0 recipe rather than a v4.0 arm) are stated in D-06 rather than
  glossed. Carry that standard into the report text committed in this phase.
- **Two constants, labelled as preference.** A reviewer should be able to find `f_Y` and `f_C`, see
  them marked as milestone preference rather than derivation, and argue with exactly those two.

</specifics>

<deferred>
## Deferred Ideas

- **The GATE-10 fallback tolerance** (D-26) — a third chosen constant, deliberately unset. Must be
  decided **before Phase 21's CAL-03 runs**, named explicitly, never left implicit inside D-25.
- **Extraction noise floor measurement** (D-13) — two seeds on the never-taught arm. Belongs to
  **Phase 23** (CTRL-03), gated behind Phase 21's corpus design. Carried by the D-14 tripwire, not
  by prose.
- **Re-measuring `V20_RETENTION_NOISE_FLOOR`'s consumers** — `erasure_gate`'s own `retention_cap`
  still uses the Phase 12 full-fine-tune floor. **Not in scope**: `23a830c` must not be amended, and
  D-06 corrects the value only for the v4.0 gate. If v3.0's cap is ever revisited it is a dated
  continuation, never an edit.
- **Whether the retention leg should eventually become a gap band too** — deferred behind a
  measurement that does not exist: the retention gap's sign change (D-05) would need
  characterising across more than two seeds before a band there could be specified.

</deferred>

---

*Phase: 20-Pre-Registration — The Three-Condition Gate*
*Context gathered: 2026-08-20*
