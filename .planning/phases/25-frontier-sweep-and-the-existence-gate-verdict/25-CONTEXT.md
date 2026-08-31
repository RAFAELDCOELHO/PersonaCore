# Phase 25: Frontier Sweep and the Existence-Gate Verdict - Context

**Gathered:** 2026-08-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Run the v4.0 frontier sweep and render its verdict. Both mitigation arms — DP-SGD (noise) and
adversarial extraction-aware training (mixture ratio) — at both capacities (n=8, n=64), emitted as
`results/phase25_frontier.json`, with the verdict computed by **importing** `scripts/mitigation_gate.py`
rather than retyping any threshold.

Requirements: **CTRL-01, CTRL-02, FRONT-01, FRONT-02, FRONT-03, FRONT-04, ADVT-01, and RPT-02**
(RPT-02 by D-38 — it is deferred to this phase in the REQUIREMENTS traceability but is absent from the
ROADMAP Requirements line, so no phase can currently tick it).

**This is the first phase of the milestone that spends days rather than minutes.** 44 sweep points,
~150 h at the ceiling / ~107 h at the measured rate, on a machine whose last production run was
killed externally at 60 minutes. Roughly half of the decisions below exist because of that fact.

**This phase builds almost nothing.** The gate, the accountant, the DP mechanism, both data seams,
the attack corpus, the scorer, the never-taught floor, the budget pins and the adversarial grid all
ship already. Phase 25 runs them, and the work is the discipline around the run, not the run.

**Nine corrections this discussion produced, each measured rather than argued.** They travel with the
phase because five of them contradict text a planner would otherwise take literally:

1. **`clip_norm=inf` is REFUSED by the code.** `DPSGD.__init__` requires finite and positive;
   `math.inf` raises `[dp-refusal:clip-domain]`. Forcing measurement at `src/personacore/privacy/dpsgd.py:74-80`:
   noise std is `sigma * C` at one draw site with no `sigma == 0` branch, so `0.0 * inf = nan` and
   `torch.normal` raises. `C = ∞` is represented as **a finite bound proven not to bind**.
   **CTRL-02's `clip_norm=inf` wording needs a dated continuation.**
2. **SC1's comparator does not exist as written.** v2.0's 0.4921 / 0.3483 belong to a run whose recipe
   differs; the fact-aligned control reads 0.5615 and the protocol-matched σ=0 point reads **0.7837**.
   The held-out denominator also changed (936 → 648). See D-02.
3. **FRONT-01's "swept to the never-taught floor" is a DP-arm property.** The adversarial axis
   terminates at a **pool ceiling**, not a floor-reaching parameter. See D-19.
4. **GATE-10 cannot run on the adversarial arm.** `capacity_comparison` takes no `arm` argument and
   `_prove`s all four `MECHANISM_KEYS` present and exactly equal; the adversarial arm has no σ/δ/q.
   See D-23.
5. **`C` is pinned nowhere and is outside `MECHANISM_KEYS`** — yet `std = sigma * C`, so two points at
   equal nominal σ and different C carry different noise scale while passing the gate's equality check.
   See D-24 / D-25.
6. **`results/phase2X_frontier.json` in ROADMAP.md is a PLACEHOLDER, not a filename.** The artifact is
   `results/phase25_frontier.json` (D-31).
7. **RPT-02 is an orphan of the ADVT-01 shape** — deferred to Phase 25 in REQUIREMENTS traceability,
   absent from Phase 25's ROADMAP Requirements line. See D-38.
8. **Adversarial *training* cost is bounded, not unmeasured** (non-DP protocol-matched 161.1 s/point,
   `dp_n64` 1383.3 s). The genuinely unmeasured term is adversarial **scoring** throughput, ~95% of
   the spend. See D-14.
9. **The suite's MPS legs are `skipif`-gated on `mps.is_available()`, which is TRUE during the sweep**,
   so they will run and contend rather than skip. See D-44.

</domain>

<decisions>
## Implementation Decisions

**Forty-four decisions across six areas. Every one is LOCKED** — the researcher and planner act on
them rather than re-open them.

### Area 1 — The control point and SC1's stop rule (CTRL-01, CTRL-02)

- **D-01: The control is RE-RUN at both capacities under Phase 25's own prefix, scored for recall
  AND extraction.** `dp_n8` + `dp_n64` at σ=0. Phase 23's 790/1008 = 0.7837 becomes a declared
  **bit-level reproduction check** at seed 1337. Marginal cost over importing is ~40 s of training;
  the ~2.2 h extraction scoring is owed either way because **the control's extraction has never been
  measured** and `mitigation_point_verdict` requires `control_extraction_successes` /
  `control_extraction_questions`.

  **C = 1e6, proven non-binding — not `inf`** (correction 1 above). It must be *the same* 1e6 Phase 23
  used, or the reproduction check is not bit-level. `clip_bind_count == 0` is asserted before scoring.

- **D-02: SC1 stays an ACTIVE check; its binding comparator is superseded by a DATED CONTINUATION to
  the Phase 23 MATCHED control** (0.7837, floor `MATCHED_CONTROL_NOISE_FLOOR = 0.0267857142857143`).
  That is the only comparator differing from a real DP point by exactly the two DP parameters — a
  property v2.0's 0.4921 never had. v2.0 is retained as a **disclosed historical reference** with the
  recipe delta named explicitly (held-out denominator 936 → 648, 8× teaching-token exposure,
  replay-in-lot, fact-aligned bins). **The original SC1 text stays visible, superseded, never deleted.**

- **D-03: The n=64 leg gets its OWN matched-control floor at the full 5-seed `SEED_LADDER`**
  (1337, 2024, 1338, 2025, 1339), reduced by `phase23_prereg.noise_floor`. ≈ 3.3 h
  (5 × 23.1 min training + 5 × 16.6 min recall scoring), about 2% of the sweep. Same estimator that
  produced 0.0268 at n=8. No borrowed floor, no capacity asymmetry to disclose.

- **D-04: PROBE 2's tensor comparison is RE-RUN at BOTH capacities before any real sweep point.**
  n=64 has never been probed, so this is a first measurement, not a repetition. The measured
  per-tensor agreement is committed as a pre-run record alongside Phase 23's four
  `declared_differences` imported by path + digest, and an **armed tripwire test FAILS if any later
  plan asserts bit-identity** between the σ=0 point and the seam-off path. ≈ 46 min.
  (Phase 23's n=8 figure, for reference: 72/72 LoRA tensors agreeing to 2.178e-07 relative.)

- **D-05: The control's extraction scoring uses the identical 416 `core_held_out` questions as the
  never-taught floor** — 104 × 4 families, `family_zero_run: False` excluding A0 — at
  `draws_per_question = 16` from `mitigation_budget.CURVE_K`. `core_taught` (448 questions) is ALSO
  dispatched and reported, as the never-taught record does, but **only `core_held_out` feeds the
  gate** (`phase18_extraction.GATED_TIER`). Measured cost: 7,334.8 s = 2.04 h per seed for both tiers.

- **D-06: The seam-off comparator gets its OWN arm name; the σ=0 CONTROL POINT does not.** The control
  keeps arm identity `dp_n8` / `dp_n64` — it *is* a DP sweep point per CTRL-02 — and is separated by
  **prefix only**, which is what keeps D-01's bit-level reproduction reachable. Only the `dp_fn=None`
  comparator is renamed. Precedent: `phase23_matched_control` declared_difference #2, and
  `matched_arm(seed)` already distinct from `dp_n8`.

- **D-07: `prove_reproduction(k, n)` lives in a committed Phase-25 pre-registration module and is
  called BEFORE any non-control point runs.** On a miss it **HALTS — zero sweep points** — with a
  message naming the ratio-0.0 byte-identity assertion (`f146d426` / `a2c4771f`) as suspect #1 and the
  four `declared_differences` as the starting list, mirroring D-04's halt-message shape in Phase 23.
  Same structure as `phase23_prereg.sigma_zero`; **its refusal is watched before it is trusted.**
  Hard equality on integer counts (`k == 790`, `n == 1008`) — no tolerance, because the reading is a count.

### Area 2 — Sweep budget, legs, and kill-resumability

- **D-08: All 44 points run as pinned.** `SWEEP_POINTS = 16` × 2 capacities + `ADVERSARIAL_RATIO_GRID`
  (6) × 2 capacities. Neither is re-opened at the moment of spending — the same discipline as the
  23-13 blocking checkpoint ("desvio de número já publicado exige justificativa científica explícita").
  `N64_LEG_WITHDRAWN` stays `False` on the measured CAL-03 read (ε_n8 == ε_n64 == 24.3816, T == 4 both
  sides), preserving the full curve `GATE-06` needs so it does not read INCONCLUSIVE by truncation.

- **D-09: Shape-keyed block resume.** Each attack shape's draw block is written to the cache as it
  completes; the driver skips complete shapes on restart. A kill loses **≤ one shape (~33 min at
  K=16)**, not the point (~2.2 h). The cache is **already shape-keyed** (`phase23_run.py:4721`,
  `blob["shapes"][shape]["draws"]`). The ancestry-guarded `scripts/phase18_extraction.py` stays
  untouched — the driver owns the draw loop and calls it only as a scorer, the Phase 23 separation.

- **D-10: The one-attempt rule's unit is the SWEEP POINT, not the sweep.** A point with a committed
  reading is evidence and is never re-run — `prove_first_attempt`'s glob is the committed per-point
  records. A point killed mid-scoring produced no reading, so resuming it is the **same** attempt, and
  D-09's blocks make "no reading landed" checkable rather than asserted. **Each completed shape block's
  sha256 is committed as it lands**, closing the sub-point leak that would otherwise let a
  delete-and-redraw leave no trace, since the cache lives in gitignored `data/`.

- **D-11: Promotion and replication are LAZY and candidate-triggered.** All 44 curve points at
  `CURVE_K = 16` first; only points clearing all three conditions are promoted to
  `FULL_FIDELITY_K = 48` **and** replicated at a second seed **at K=48** — never a lower-power
  replication than the claim. An empty frontier (the pre-registered null, live given ε=519.70 at
  σ=0.5) means **exactly zero** tail cost. **Pre-registered rule, committed before the curve runs: if
  more candidates clear than the budget holds, promote and replicate ALL of them — never a subset
  chosen after seeing which cleared.**

- **D-12: The sweep runs as a user LaunchAgent, not a harness background child.** It survives session
  end, compaction and logout; stdout/stderr to file. It wraps itself in **`caffeinate -dims`, holding
  its OWN idle-sleep assertion** rather than borrowing a stray one. **`KeepAlive` stays FALSE** — an
  automatic restart would re-enter a point without passing the driver's deliberate resume logic and
  would violate D-10. A **heartbeat line** (utc, point, shape, draw index) makes any future kill
  diagnosable instead of a zero-traceback mystery.

  *Measured hazard:* `pmset -g` reads **`sleep 1`** on AC and battery — system sleep after one minute
  of idle — held off only by transient assertions including five stray `caffeinate` processes and
  `Claude` itself. A macOS compute process holds no idle-sleep assertion on its own.

- **D-13: A system-level `pmset` change is the independent second layer.**
  `sudo pmset -a sleep 0 disksleep 0 powernap 0` before the sweep, **reverted to the current values
  (`sleep 1`, `disksleep 10`, `powernap 1`) at the end**, both acts recorded as a dated operational
  note. **The revert is a COMMITTED plan step, verifiable, never dependent on human memory.**

- **D-14: Both adversarial extremes are throughput-probed BEFORE the schedule is committed.** Train one
  `adv_n8` at ratio 0.0 and one at 1.9090909090909092, each with a timed **768-draw** probe (CAL-05's
  own `n_draws_measured`). ≈ 30 min. Ratio 0.0 anchors against the measured non-DP 161.1 s (the
  seam-off twin of the matched comparator, bins byte-identical to v2.0); 1.909 measures the extreme most
  likely to diverge. **The schedule is finalised only after both points confirm the throughput curve's
  real shape** — never extrapolated from one.

- **D-15: The EIGHT extremes run before any interior point, INTERLEAVED across the four legs.**
  DP × {n8, n64} at σ→0 and at the never-taught end; adversarial × {n8, n64} at ratio 0.0 and 1.909.
  Not one leg exhausted before the next. A structural problem at any of the four corners appears on day
  one. The low extremes are already the D-01 control points and the ratio-0.0 arms — this is
  sequencing, not new work.

- **D-16: Heartbeat silence is DETECTED, never ACTED ON.** A separate lightweight watcher (second
  LaunchAgent or periodic check) reads the heartbeat; if it has not advanced in N minutes it writes a
  timestamped stall record and notifies — **no restart, no kill, no cleanup**. N is derived from the
  measured worst-case gap between heartbeat lines at the slowest attack shape, not chosen by
  convention. Detection and correction stay structurally separate so D-10 stays intact.

### Area 3 — σ grid placement and extremes-first (FRONT-01)

- **D-17: σ is pinned as float literals in `scripts/mitigation_budget.py`, and THE SAME LADDER IS
  REUSED AT BOTH CAPACITIES.** Forced twice over: `capacity_comparison` compares σ under exact
  equality, and the module's literal-only guard runs `ast.literal_eval` on every assigned value, so a
  derived `sigma_for()` call cannot be pinned there. Reusing one set satisfies `MECHANISM_KEYS`
  equality trivially rather than by coincidence. Values are chosen so
  `epsilon_for(sigma, 200, 1e-5)` lands on a **pre-registered round-number ε ladder**, committed
  alongside, with a **live test** (`test_phase24_grid`'s shape) asserting the correspondence under
  exact `==`, no tolerance.

  *Measured curve at T=200, δ=1e-5:* σ 0.10 → ε 10602.16 · 0.50 → 519.70 · 1.0 → 159.44 · 2.0 → 54.38 ·
  5.0 → 15.46 · 8.0 → 8.60 · 20 → 2.94 · 80 → 0.63. Inverting: **ε=8 needs σ=8.49; ε=1 needs σ=52.76.**

- **D-18: The high anchor is PROBED, not presumed.** One or two candidate σ_hi under a **named
  calibration prefix**, recall-only (~20 min each), **excluded from the sweep's point set** exactly as
  `phase23_sigma0` was. The ladder is committed only after the probe confirms the anchor. A
  **ratchet-shaped extension rule** is committed alongside: if the high extreme's *full* extraction read
  still misses the never-taught floor, the grid **extends upward** by a pre-registered rung (halve ε) —
  never shifts, never shrinks. The low anchor needs no probe: σ=0 **is** the control and reconnects by
  construction.

- **D-19: The adversarial axis's inability to reach the floor is a NAMED STRUCTURAL ASYMMETRY, not a
  deficit.** The DP axis has a physical mechanism driving utility toward zero under high noise; the
  adversarial axis terminates at its **pool ceiling** by construction (1.909 = the largest ratio at
  which the whole trained pool is used exactly once). A **dated continuation** corrects FRONT-01's
  "swept to the never-taught floor" to a DP-arm property, original text left visible and superseded.
  **Both arms are read against the SAME already-measured never-taught floor** (0/416, 5 seeds,
  `results/phase23_never_taught.json`) as the plane's shared lower-left reference; no adversarial point
  needs to reach it personally.

- **D-20: σ=0 is INSIDE `SWEEP_POINTS = 16`** — 15 noised points per DP leg, control at slot 1. Two
  converging lines: `SWEEP_POINTS_PROVENANCE.governs` reads "frontier points per leg, and nothing else"
  with CTRL-02 confirming the control as a real sweep point; and `phase23_cost.sizing["16"]` prices 16
  points plus the never-taught floor as a **separate term**, reserving nothing for a 17th. Total stays 44.

- **D-21: Every ε reading in the artifact carries its own `k` and `k_source` INLINE**, not as
  separately-consultable metadata. A K=16 curve reading and a K=48 promoted reading of the same point
  have **numerically identical ε** and differ only in statistical precision, so they must never be
  confusable. Precedent: `phase23_never_taught.json` already records `draws_per_question: 16` with
  `draws_per_question_source: "mitigation_budget.CURVE_K"` on every per-seed block.

- **D-22: The six adversarial ratios are IDENTICAL at both capacities.** `ADVERSARIAL_RATIO_GRID` is a
  single tuple whose `governs` reads "adversarial sweep points **per capacity**"; 24-07 measured all
  four corners of `{adv_n8, adv_n64} × {0.0, 1.909}`; `multiplicity_at_upper_extreme`
  `{dp_n8: 1.0, dp_n64: 8.0}` is a **reported property, not a grid variable**.

- **D-23: `capacity_comparison` stays a DP-ONLY instrument, and that is NAMED rather than patched.**
  It takes no `arm` argument (zero occurrences in its body) and `_prove`s all four `MECHANISM_KEYS`
  present **and** exactly equal; the adversarial arm has no σ/δ/q — the same fact `accounting: null`
  states structurally. The two adversarial capacities are reported **side by side descriptively**, and
  the absence of a committed capacity rule for that arm is named explicitly in the artifact and the
  report rather than left for a reader to trip over. v2.0's "gate only what the measurement supports".

- **D-24: `C` is CALIBRATED from measured per-record norms, then pinned.** Run one `vmap` per-example
  gradient pass at both capacities (seconds to minutes; the machinery is built and exact to 6.5e-08) to
  get the real **per-record** norm distribution on the DP path — never measured; only batch-level norms
  on the non-DP path exist (`grad_clip_evidence`, max 2.20–2.30). Pin `C` as a **single float literal**
  in `mitigation_budget.py` with a `_PROVENANCE` sibling naming the measurement. This also answers
  whether 100% binding at C=1.0 (`phase23` `dp_n64`: `clip_bind_count` 12800 of 12800) is a sensible
  operating point or an accident of one run — at fixed σ, a C below every record's norm is pure
  clipping bias bought for nothing, since ε does not improve.

- **D-25: The `clip_norm` gap is closed CALLER-SIDE.** `C` **cannot** join `MECHANISM_KEYS`: the gate is
  frozen and any new commit to it after `results/phase20_*` exists reddens the ancestry guard
  permanently (the guard takes `adds[-1]`, the *earliest* add, so `git rm` + re-add cannot launder it).
  It does not need to — `capacity_comparison`'s check is
  `missing = [key for key in MECHANISM_KEYS if key not in ...]`, so **extra keys are ignored, not
  refused**. `clip_norm` travels in the mechanism dicts and the Phase 25 driver `_prove`s equality on it
  **before** calling the gate. D-24's single literal makes that true by construction.

- **D-26: `SAMPLING_RATE_Q = 1.0` holds because the private lot IS the fact set.** Verified against
  source: `mitigation_unit.PRIVACY_UNIT_ARITHMETIC` names the with-replacement hazard verbatim —
  `get_batch_memmap_masked` draws offsets "with replacement, and with no notion of where one fact ends
  and the next begins", so a fact is touched an expected **262.94** times over 1,600 draws, which is
  *why* an example-level ε says nothing about a fact. The DP path does not use that sampler for private
  data; under fact-aligned accumulation the quantity is "exactly 1 per micro-step, deterministic, by
  construction — which is what makes `SAMPLING_RATE_Q = 1.0` honest rather than assumed."

- **D-27: T = 200 at both capacities is MEASURED, not inferred.** `phase23_sigma_zero`:
  `composed_steps 200` / `composed_lot_sizes [8]` / `records_per_lot 8`. `phase23_noised_dp_n64`:
  `composed_steps 200` / `composed_lot_sizes [64]` / `records_per_lot 64` / `t_matches_across_capacities: true`.
  `grad_accum_steps = n_facts` governs micro-steps **inside** one optimizer step; composed T is
  optimizer steps and is capacity-independent.

### Area 4 — Dual ε reporting and the frontier artifact contract (FRONT-02, FRONT-03, FRONT-04)

- **D-28: The dual report pairs the REAL fact-level ε with the example-level COUNTERFACTUAL, and names
  both multiplicities.** Beside the fact-level ε that actually governs this path, report what an
  example-level accounting *would* have claimed under the unaligned with-replacement sampler — the
  flattering number a reader might wrongly assume applies — with **207.018** (first-token-owns-draw, the
  artifact rule) **and 262.944** (the frozen pin's overlap rule) both named, since
  `phase21_multiplicity.json` records that discrepancy as `"RECORDED, NOT RESOLVED — the pin is frozen
  and is not edited"`. Neither is hidden. FRONT-02 is met in its strongest form: it **shows the size of
  the error** confusing the granularities would make, rather than only asserting it would be wrong.

- **D-29: The curve-total ε is BASIC composition over the noised DP points actually PUBLISHED**, at
  total δ = k·δ — conservative, computable from the existing stdlib accountant, **zero new chosen
  constant**. Declared with it: the σ=0 control has **no ε** (`phase23_sigma_zero` records
  `epsilon: None`) and is an adapter trained on the same facts with no privacy at all, so **once it is
  published, no joint bound over all published artifacts exists**. `selection_accounted = False`,
  naming that choosing a best point after seeing results would be unaccounted adaptive selection.
  **The total CROSSES both legs** — the 8 locked facts appear in n=8 *and* n=64, and a per-leg split
  would hide exactly the cumulative exposure that matters most.

- **D-30: The ε helper takes three required kwargs and an AST GATE enforces it.** `point_epsilon`,
  `curve_total_epsilon` and `selection_accounted` are keyword-only with **no defaults** — the gate's own
  21-kwarg precedent, where the length *is* the protection. Enforcement is an **AST walk** over the
  phase's modules: any `print` / f-string / `.format` / `%` whose operand resolves against a committed
  ε-name set, **outside the helper's own body**, fails the test. **AST deliberately over grep** — a grep
  over files whose prose discusses ε goes false-RED, a class this repository has hit repeatedly
  (RPT-02's traceability row records four instances in Phase 20 alone).

- **D-31: Per-point records land incrementally; `results/phase25_frontier.json` is assembled WRITE-ONCE
  at the end.** Each point writes its own committed record as it completes — that record **is** D-10's
  one-attempt glob and D-09's resume unit, no new structure. The frontier is assembled once from those
  records, with **ordered `point_keys` equality proved at that single write**, `accounting: null` on the
  adversarial arm, the gate and budget module sha256s travelling inside it, and **per-question successes
  INLINE for all 44 points** (~9.7 MB; direct precedent `results/phase18_arm_adapter-on.json` at 2.7 MB
  and `phase23_never_taught.json` at 1.1 MB for 4,320 rows). **Filename: `results/phase25_frontier.json`**
  — the roadmap's `phase2X_frontier.json` is a placeholder. Single source of truth in the strong sense
  FRONT-03 promises: no bound requires a second file, no tier split across places.

- **D-32: FRONT-04's null verdict is carried by the gate's EXISTING `null-at-both-capacities` branch**
  (`CAPACITY_BRANCHES`, reached via `_CAPACITY_DISPATCH[(False, False)]`, dispatch totality proved at
  module scope), paired with `exists_clearing_point`'s own denominator-carrying string
  ("0 of N point(s) examined returned PASS"). **Nothing new is authored in the phase that runs the
  sweep** — exactly what FRONT-04 exists to protect.

- **D-33: Phase 15's figure guard is RETARGETED, not reinvented.** AST walk over the plotting module's
  imports **plus** a fresh-interpreter probe that FAILS if `torch` lands in `sys.modules`, retargeted so
  the module may open `results/phase25_frontier.json` and nothing else. PROJECT.md already records this
  as one of three conversions from declared invariant to checked mechanism; Phase 23's D-09 applied the
  mirrored form to the budget-import guard.

- **D-34: A live mechanism mismatch HALTS THE WHOLE SWEEP.** Every point record carries
  `composed_steps`, `composed_lot_sizes`, `records_per_lot`, `q` and `clip_norm` read **live at write
  time**, asserted against the pinned values under exact equality. Any divergence stops the sweep — not
  a logged warning. A point whose mechanism diverged from the pin has an ε that does not describe what
  happened, and publishing that is the single most dangerous error class v4.0 research named. Same
  structural weight D-07 gives the control's reproduction miss.

- **D-35: The three-condition reading is ARM-AGNOSTIC by construction.** Verified:
  `mitigation_point_verdict` contains **zero** occurrences of `epsilon` or `accounting` across its 198
  lines — its 21 kwargs are all counts, recalls, perplexities and floors. X, Y and (c) never depended on
  ε; only the formal accounting does, and `capacity_comparison` is the sole ε-dependent function
  (already scoped by D-23). **Nothing to fix.**

- **D-36: A2's held-out generalization lives INSIDE the frontier artifact, per-point plus a re-derivable
  aggregate.** Every point record carries per-family counts **including A2** alongside the three trained
  families — nearly free, since A2 is already one of the four scored shapes across all 416 gated
  questions (`generation.attack_shapes: [A1-mild, A1-aggressive, A2, A3]`, 416 = 104 × 4). The assembly
  computes a `held_out_generalization` section **from those fields**, with a write-time assertion that
  the aggregate re-derives **exactly** from the per-point counts, so it can never drift from its own data.

- **D-37: Three reservations for Phase 26's canary audit, all free now and expensive later.**
  (i) **Every point's adapter is RETAINED on local disk with its sha256 recorded INSIDE the frontier
  artifact** — `checkpoints/` and `*.pt` are gitignored (`.gitignore:14-15`), so without this the audit
  has nothing to run against and a deleted adapter cannot be re-derived without re-running the point
  (44 × 1.35 MB ≈ 59 MB). (ii) **The in/out canary population is recorded per point**: at n=8 the 56
  filler facts are OUT, at n=64 all 64 are IN — so **only n=8 points have out-of-corpus canaries at
  all**, a structural constraint on Phase 26 written down before the sweep rather than discovered after.
  (iii) **A committed rule naming WHICH point the audit targets**, written before any point exists, so
  the choice cannot be made after seeing the data.

### Area 5 — Carried-forward obligations

- **D-38: RPT-02 is ADDED to ROADMAP Phase 25's `**Requirements**` line**, with the span recorded
  additively under REQUIREMENTS Traceability — the same repair ADVT-01 needed. Phase 25 discharges the
  unmet second half by routing its two dated continuations (D-02's SC1 comparator, D-19's FRONT-01
  scope) through `scripts/_prose.py::normalized` rather than through grep — **under the requirement's
  own regulation, not beside it.** Without this, no phase can tick RPT-02.

- **D-39: 24-04's refusal instrumentation is WIRED into the sweep driver.** `contains_refusal` /
  `score_refusal` / `clean_frame_probe_populations` are called so every adversarial point carries a
  **refusal-rate column in counts, never rates** — the shape FRONT-03 already demands, and
  `score_refusal` already returns. It measures the arm's **real mechanism** (is the refusal working),
  information otherwise entirely absent from the artifact: a point clearing on extraction would give no
  evidence about *why*. Fits D-36's per-family counts with no new structure. **It stays OUTSIDE the
  three-condition gate — reported information, never a verdict condition** — preserving the closed
  domain GATE-07 / D-29 protect. This closes Phase 24 HUMAN-UAT item 3.

- **D-40: The publication obligation is COMMITTED NOW; publication executes in Phase 28.** Phase 28
  ("Report, the Published Null, and Milestone Close") owns RPT-01. Phase 25 does not write the report —
  it commits, **before any point exists**, exactly which strings from the artifact the report must
  carry: the arm-level existential **with its denominator**, the capacity branch name, the curve-total ε
  with `selection_accounted`, and the named limitations (adversarial capacity rule absent per D-23;
  curve total unbounded once the control is published per D-29).

- **D-41: Five of 24-REVIEW's eight warnings are FIXED before any point runs; three are deferred with
  their unreachability RECORDED.**
  - **Fix:** **WR-01** (a NaN or negative `adversarial_ratio` silently builds the control on the flat
    branch under an adversarial name — the "guard refuses a NAME where the harm is a PROPERTY" class
    Phase 20 recorded twice); **WR-04** (`replay_ratio` stops describing the bin when both ratios are
    set, against D-34's live mechanism assertion); **WR-05** (the multiplicity pin keys on
    `dp_n8`/`dp_n64` while every measured row keys on `adv_n8`/`adv_n64` — the pin D-22 leans on);
    **WR-06** (`_mix_adversarial` pairs two corpus reads by index, which would corrupt D-36's per-family
    counts); **WR-08** (both bins written to disk before proofs 1–3 run, colliding with
    `refuse_if_exists` and D-10).
  - **Defer, unreachability recorded rather than silenced:** **WR-02** and **WR-03** (the `n_want < 1`
    path is unreachable at 176 / 1,408 clean episodes); **WR-07** (test re-declares the split as
    literals — hygiene, no effect on any sweep number).

### Area 6 — Operational and anchor detail

- **D-42: `extraction_ceiling` is passed the already-committed designated-seed `pooled` block VERBATIM**
  — `SEED_LADDER[0]`, pooled across the four dose-split families, 0/416 — never re-reduced.
  **X = `wilson_upper_bound(0, 416)` = 0.00646169** (`extraction_noise_floor` is 0.0, so the
  `MARGIN_K = 2` term contributes nothing); tolerance = **at most 2 successes of 416**. Pooling all five
  seeds (0/2080 → X = 0.00129905, **4.97× tighter**, tolerance 0 of 416) would treat five correlated
  adapters — one base, one fact set — as independent samples, narrowing the bound on evidence that is
  not independent, and would be a reduction chosen in the phase that runs the sweep.

  *Verified:* `extraction_ceiling` reads the designated seed as a **Wilson upper bound**, with the
  5-seed range entering only as the noise-floor margin — multi-seed evidence sits exactly where
  seed-to-seed variation belongs, and each sweep point is single-seed at K=16 over the same 416
  questions. Single-seed against single-seed, identical denominator, identical K.

- **D-43: The five stray `caffeinate` assertions are CLEARED before the sweep starts.** The run's own
  `caffeinate -dims` becomes the **only** non-system assertion held, **verified by reading `pmset -g`
  back after launch** and recording that line in the operational note. Without it, D-12's whole
  mechanism could be masked by residue — the run would appear to hold the machine awake while a stray
  process from an earlier session genuinely does it.

- **D-44: An explicit sweep-active skip covers MPS device contention, loudly.** An env var (or pytest
  option) active during the sweep makes the MPS-touching legs skip **with a reason naming the sweep** —
  `tests/test_mps_smoke.py`, `tests/test_phase23_mps_venue.py`, and the MPS params in
  `tests/test_phase22_fakes.py` / `test_phase22_checkpoint.py` / `test_phase22_dpsgd.py`. The CPU-only
  bulk of the ~1,647 tests keeps running normally. *Measured cause:* every MPS leg is `skipif`-gated on
  `torch.backends.mps.is_available()`, which is **TRUE** during the sweep, so they would otherwise run
  and contend. **A contention failure can then never be mistaken for a genuine one**, and the skip
  reason names why rather than vanishing into a count.

### Claude's Discretion

- The exact σ literals on the ε ladder (D-17) and the concrete ε rungs — outputs of the D-18 probe and
  the ε table, not choices to be made in advance. The **count** is pinned at 16 (D-20) and is not
  discretionary.
- The candidate σ_hi values the D-18 calibration probe tries, and whether one or two are needed.
- `N` in D-16's heartbeat-silence threshold — derived from the measured worst-case inter-line gap at the
  slowest attack shape, so it is an output of measurement, not a preference.
- The concrete shape of the LaunchAgent plist, the heartbeat file format, and the watcher's
  implementation (second agent vs periodic check).
- The point-key grammar for `point_keys` (D-31), provided the ordering is proved as a hard equality on
  write.
- Whether D-24's per-record norm probe reuses `phase23_cost`'s timing harness or stands alone.
- Log rotation for the LaunchAgent over 6 days, the branch the incremental point commits land on
  (`config.json` sets `branching_strategy: none`, so `main`), and a disk-space precheck for the ~59 MB of
  retained adapters — all plan-level detail settled from the decisions above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The frozen pre-registration — NEVER EDIT
- `scripts/mitigation_gate.py` — the three-condition gate. **FROZEN, permanently.** `V4_VERDICTS`,
  `ARMS`, `ARM_CLAIMS`, `F_Y = 0.7`, `F_C = 0.5`, `K_RUNGS`, `NEVER_TAUGHT_ARM`,
  `EXTRACTION_FLOOR_MIN_SEEDS = 2`, `extraction_ceiling`, `tolerance_report`, `dialogue_gap_band`,
  `retention_cap`, `mitigation_point_verdict` (21 kwargs), `exists_clearing_point`, `ratchet_k`,
  `promote_to_full_fidelity`, `MECHANISM_KEYS`, `CAPACITY_BRANCHES`, `capacity_comparison`. Any commit
  to this file after `results/phase20_*` exists reddens the ancestry guard permanently (D-25).
- `scripts/mitigation_accountant.py` — the FROZEN (ε, δ) pin. `GOLDEN_EPSILON`,
  `REQUIRED_FORM`/`REJECTED_FORM`, `NEIGHBOURING`, `SENSITIVITY_MULTIPLIER`.
- `scripts/mitigation_unit.py` — the privacy unit. `PRIVACY_UNIT`, `PRIVACY_UNIT_ARITHMETIC`
  (D-26's source), `SAMPLING_RATE_Q = 1.0`, `privacy_n`, `REPLAY_OUTSIDE_N`, `DELTA = 1e-5`.
- `scripts/mitigation_budget.py` — protected but **NOT frozen**, and **literal-only**
  (`ast.literal_eval` on every assigned value). Holds `CONTROL_NOISE_FLOOR`,
  `MATCHED_CONTROL_NOISE_FLOOR`, `SWEEP_POINTS = 16`, `CURVE_K = 16`, `FULL_FIDELITY_K = 48`,
  `STEP_BUDGET = 200`, `N_CONTROL_SEEDS = 5`, `N64_LEG_WITHDRAWN = False`, `ADVERSARIAL_RATIO_GRID`.
  **This phase adds the σ ladder (D-17) and `C` (D-24) here, each with a `_PROVENANCE` sibling.**
- `scripts/erasure_gate.py` — source of `wilson_upper_bound` and `MARGIN_K`, imported by object
  identity (D-42). Never re-implemented.
- `scripts/_addendum.py` — `append_addendum(path, addendum, *, pending, recorded)`, the ONLY legal
  correction path for a closed pre-registration. Both keywords required; refuses a second append.
  D-02, D-19 and correction 1 all route through it, each with an armed tripwire (D-24 pattern).
- `scripts/_prose.py` — `normalized`, the whitespace-normalizing prose-search helper. **RPT-02's second
  half is discharged by routing this phase's correction sweeps through it (D-38).**

### Read-only inputs — ancestry-guarded, imported never edited
- `scripts/phase18_extraction.py` — `GATED_TIER = "core_held_out"`, `REPORTED_TIER = "core_taught"`,
  `CORPUS_TIERS`, `K = 48`, `score_records`, `aggregate_questions`, `licensed_conclusion`,
  `run_arm`. **Ancestry-guarded and permanently uneditable** (`tests/test_phase21_sc5.py:348`,
  `tests/test_phase24_split.py:29`). The driver owns the draw loop and calls it only as a scorer (D-09).
- `results/phase18_corpus.json` — the attack corpus, sha256 `ff8e6e3c…`. Read-only.

### What Phase 25 runs
- `scripts/teach_persona.py` — `ARMS`, `DP_ARMS = ("dp_n8","dp_n64")`, `ADV_ARMS = ("adv_n8","adv_n64")`,
  `arm_spec`, `MAX_STEPS = 200`, `train_arm(..., dp_fn=, fact_bin=, n_facts=, adversarial_ratio=,
  resume_from=)`, `build_bins`, `_mix_adversarial`, `_prepend_replay`, `refuse_if_exists`,
  `arm_outputs`. **WR-01/WR-04/WR-06/WR-08 all live here (D-41).**
- `src/personacore/privacy/dpsgd.py` — the DP mechanism. **`:52-54` (`std = sigma * C`) and `:74-80`
  (why `math.inf` is refused) are the load-bearing lines for D-01, D-24 and D-25.**
- `src/personacore/privacy/accountant.py` — `epsilon_for`, `sigma_for`, `delta_closed`,
  `delta_quadrature`. stdlib `math` only.
- `src/personacore/training/loop.py` — the `dp_fn=` gradient seam, the `fact_bin=`/`n_facts=` data seam,
  the resume block.
- `scripts/phase23_run.py` — the Phase 23 driver. **`:4721` (`blob["shapes"][shape]["draws"]`) is the
  shape-keyed cache D-09 extends**; `score_adapter`, `SIGMA_ZERO_*`, `SEED_LADDER`, `matched` sub-mode.
- `scripts/phase23_prereg.py` — `noise_floor` (D-03's reducer), `sigma_zero` (D-07's structural model),
  `H_PER_POINT_FLOOR_SECONDS`.
- `scripts/phase23_matched_prereg.py` — `prove_first_attempt` and its four clauses (D-10 rescopes its
  unit to the point). **EDIT-ONCE and already spent for its own glob.**
- `scripts/phase24_adversarial.py` — `HELD_OUT_FAMILY = "A2"`, `_adversarial_pool`,
  `adversarial_episode_families`, `build_a2_prompt`.
- `scripts/phase24_record.py` — the write-once emitter + `_PUBLICATION_PATHSPEC` pattern D-31 follows.
- `scripts/phase14_recall.py` — `contains_value`, and 24-04's orphaned `contains_refusal` /
  `score_refusal` / `clean_frame_probe_populations` that **D-39 wires**.
- `scripts/phase15_stats.py` / `scripts/plot_phase15.py` — the figure guard D-33 retargets.

### Measured records this phase reads (never re-derives)
- `results/phase23_sigma_zero.json` — the σ=0 diagnostic: taught 790/1008 = 0.7837, `clip_norm 1e6`,
  `clip_bind_count 0`, `composed_steps 200`, `epsilon: None`. D-01's reproduction target.
- `results/phase23_matched_control.json` — the matched comparator: 0.7837, floor 0.0268, the four
  `declared_differences` (D-04), `grad_clip_evidence`, `one_attempt_scope`, `continuation_*`.
- `results/phase23_matched_verdict.json` — `deviation 0.0`, `halt_message None`. The D-04 halt lifted.
- `results/phase23_control_floor.json` — the unmatched fact-aligned control: 566/1008 = 0.5615, floor
  0.0536, `scoring_seconds_per_seed` ≈ 996 s.
- `results/phase23_never_taught.json` — **the shared floor for both arms (D-19).** `pooled` block:
  0/416 `core_held_out` at `SEED_LADDER[0]`, K=16, `extraction_noise_floor 0.0`,
  `extraction_floor_provenance` with 5 seeds. **D-42 passes the `pooled` block verbatim.**
- `results/phase23_cost.json` — `generation` (h/point, per-shape rates, `attack_shapes`), `sizing["16"]`,
  `training` (`dp_n8` 205.4 s, `dp_n64` 1383.3 s), `ratios` (`non_dp` 161.1 s — D-14's anchor).
- `results/phase23_cal03_wiring.json` — ε_n8 == ε_n64 == 24.3816, T == 4 both sides. Why
  `N64_LEG_WITHDRAWN` is False.
- `results/phase21_privacy_unit.json` — unit / lot / delta / provenance.
- `results/phase21_multiplicity.json` — **D-28's two figures**: `pin_discrepancy.pin_figure` 262.944
  (overlap, frozen) vs `artifact_rule_figure` 207.018 (first-token-owns-draw); `corpus_geometry`
  (176 clean episodes at n=8, 1408 at n=64); `provenance.epsilon_computed: false`.
- `results/phase24_token_budget.json` — the ADVT-03 record: 12 rows of scored-token counts with
  denominators, `cross_family_inflation` 3.73×, corpus digest, per-module provenance sha256s.
- `results/phase23_noised_dp_n64_sigma0p500000.json` — the only noised point in the repo:
  σ=0.5, C=1.0, `clip_bind_count 12800`, ε 519.698. D-24's counter-example.

### Planning documents
- `.planning/ROADMAP.md` §Phase 25 (`:809-843`) — the five Success Criteria. **`phase2X_frontier.json`
  at `:834` is a placeholder (D-31); the `**Requirements**` line needs RPT-02 (D-38).**
- `.planning/REQUIREMENTS.md` — CTRL-01/02/03, FRONT-01…04, ADVT-01/02/03, RPT-01/02/03 and the
  Traceability table (**RPT-02's row is the D-38 evidence**).
- `.planning/phases/24-…/24-VERIFICATION.md` — HUMAN-UAT items 2 (INFO) and 3 (WARNING, closed by D-39),
  and the carry-to-Phase-25 instruction quoted in D-39.
- `.planning/phases/24-…/24-REVIEW.md` §Warnings (`:248-488`) — WR-01…WR-08, triaged by D-41.
- `.planning/phases/20-…/20-CONTEXT.md`, `21-CONTEXT.md`, `22-CONTEXT.md`, `23-CONTEXT.md`,
  `24-CONTEXT.md` — the locked decisions this phase inherits and does not re-litigate.

### Tests that constrain this phase
- `tests/test_phase20_prereg.py` — the ancestry guard (`_assert_ordering_holds`, `adds[-1]`) and the
  gate's import-graph guard. **The reason `mitigation_gate.py` can never be edited.**
- `tests/test_phase24_grid.py` — the literal-pinned-plus-live-derivation pattern D-17 reuses.
- `tests/test_phase24_record.py` — the provenance-freshness guard (24-09) and `corpus_sha256` live check.
- `tests/test_mps_smoke.py`, `tests/test_phase23_mps_venue.py`, `tests/test_phase22_fakes.py`,
  `tests/test_phase22_checkpoint.py`, `tests/test_phase22_dpsgd.py` — every MPS leg, `skipif`-gated on
  availability. **D-44's targets.**

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **The whole sweep machinery already exists.** DP mechanism + accountant + both seams + production
  wiring (`dp_n8`/`dp_n64`), the adversarial mixture seam (`adversarial_ratio` threaded through
  `build_bins` → `train_arm`), the 336-episode parity-proved attack pool, the frozen scorer, the
  never-taught floor at 5 seeds, and every budget pin. **Phase 25 runs them.**
- **The shape-keyed draw cache** (`phase23_run.py:4721`) — D-09 is an increment on it, not a new
  mechanism.
- **`_PROVENANCE` sibling pattern** (Phase 20, reused in Phase 23) — the shape D-17's σ ladder and
  D-24's `C` follow.
- **The write-once emitter + `_PUBLICATION_PATHSPEC` refusal** (`phase24_record.py`, `phase21_unit_record.py`)
  — D-31's assembly pattern, including the sanctioned "Delete … to re-run" route.
- **Phase 15's figure guard** (AST walk + fresh-interpreter probe) — D-33 retargets it.
- **`erasure_gate.wilson_upper_bound` / `MARGIN_K`** — imported by object identity, never re-derived.
- **`checkpoint.py`'s resume infrastructure** — `dp_noise_rng` as an `**extra` key, MPS generator state
  round-tripping bit-identically through `torch.save`/`set_state` (verified mid-stream in Phase 23).

### Established Patterns
- **Import, never retype** — every threshold is read from the frozen module; a retyped constant is the
  drift this milestone exists to prevent.
- **Watched-RED guards** — a guard nobody has seen fail is not evidence. D-07's refusal, D-04's
  tripwire and D-30's AST gate all owe a watched RED before they are trusted.
- **Natural RED over planted RED** where the tree already exhibits the failing state (24-09's precedent).
- **Retract-in-place** — corrections are dated additive continuations via `_addendum`; originals stay
  standing and visible. D-02, D-19 and CTRL-02's `inf` wording all use it.
- **Structural enforcement replaces declared invariants** — named by v2.0's own learnings as this
  project's most recurring failure mode, and converted three times already. D-04, D-30, D-33, D-34.
- **AST gates, never grep**, over files whose prose discusses the measured term (RPT-02's own reason).
- **Counts, never rates; every bound re-derivable; figures only from the committed artifact.**
- **Gate only what the measurement supports** — D-23 and D-39 both apply it.
- **A resource budget may be measured before pre-registration; an outcome threshold may not.** D-14,
  D-18 and D-24 are resource/coverage measurements; D-42's floor read is not re-reduced.

### Integration Points
- `train_arm(..., dp_sigma=, dp_clip_norm=, adversarial_ratio=, resume_from=)` — the single production
  entry every one of the 44 points goes through.
- `mitigation_point_verdict(...)` — 21 required kwargs; the Phase 25 driver assembles all of them per
  point, including `extraction_floor_provenance` from D-42's `pooled` block.
- `exists_clearing_point(points=, arm=)` — called once per arm; **aborts on a mixed-arm list**, and
  raises on an empty one.
- `capacity_comparison(...)` — DP arm only (D-23), with the caller-side `clip_norm` equality `_prove`
  running first (D-25).
- `promote_to_full_fidelity(verdict=, reasons=, curve_k=, full_k=)` and `ratchet_k(fixed_k=, proposed_k=)`
  — D-11's promotion path; K is one-way.
- `scripts/mitigation_budget.py` — gains the σ ladder and `C`; **the gate must remain AST-forbidden from
  importing it**, statically (Phase 20) and transitively (Phase 23 D-09).
- `results/phase25_frontier.json` — does not exist; created by this phase, write-once (D-31).

</code_context>

<specifics>
## Specific Ideas

**The stated principle running through the whole discussion**, in the user's framing: a premise is
verified before it is built on, and when a stated premise turns out false it is said plainly rather
than worked around. Nine premises were checked against source or measurement in this session; five
came back false or materially incomplete, and each correction is recorded in `<domain>` above rather
than absorbed silently.

**A second principle the user applied repeatedly:** a resource number already published is not
re-opened at the moment of spending it — deviation requires an explicit scientific justification, never
a cost-convenience adjustment. It governed D-08, D-20 and D-42.

**Measurements taken during this discussion** (reproduce before relying on them):
- `pmset -g`: **`sleep 1`** on AC and battery, held off only by transient assertions including five
  stray `caffeinate` processes and `Claude`.
- ε(σ) at T=200, δ=1e-5: σ 0.5 → 519.698, 1.0 → 159.44, 2.0 → 54.38, 8.0 → 8.60, 20 → 2.94, 80 → 0.634;
  `sigma_for(8, …) = 8.4885`, `sigma_for(1, …) = 52.7591`.
- `wilson_upper_bound(0, 416) = 0.00646169` vs `wilson_upper_bound(0, 2080) = 0.00129905`
  (**4.97× tighter**); `MARGIN_K = 2`.
- `mitigation_point_verdict` contains **zero** `epsilon` / `accounting` occurrences in 198 lines.
- `capacity_comparison` contains **zero** occurrences of `arm`.
- Extra keys in a mechanism dict are **ignored** by `capacity_comparison`, not refused.
- `phase23_cost.ratios.non_dp.training_seconds_per_point = 161.124`.
- `phase23_never_taught` per-seed: `seconds = 7334.8` (2.04 h), `draws_dispatched 13824`,
  `total_draws 6656` on the gated tier.
- `phase23_never_taught.json` = 1.1 MB for 4,320 `per_question` rows (~254 B/row);
  `phase18_arm_adapter-on.json` = 2.7 MB already committed.

</specifics>

<deferred>
## Deferred Ideas

- **WR-02, WR-03, WR-07** (24-REVIEW) — deferred by D-41 with unreachability recorded, not silenced.
  The `n_want < 1` path is unreachable at 176 / 1,408 clean episodes; WR-07 is test-literal hygiene.
- **24-09's six INFO findings** — untouched; not triaged in this discussion and not blocking.
- **Phase 24 HUMAN-UAT item 2** (ADVT-02's *"REFUSED, not dropped"* wording, reclassified INFO) — the
  residue is that the traceability row at `:488` lacks the widened-tuple qualifier the requirement body
  carries. A doc pass may mirror it; not a phase-holding correction.
- **WARNING-4 and WARNING-5 from Phase 22** (`delta_quadrature` degrading at large μ; 46 two-oracle
  disagreements above 1e-9) — still open, still not on the publishing path, unchanged by this phase.
- **The empirical privacy audit (CANARY-01/02)** — Phase 26. D-37 reserves what it needs from this
  phase; nothing more is built here.
- **The relearning attack (RELRN-01/02/03)** — Phase 27.
- **The report itself, and the milestone close (RPT-01, RPT-03)** — Phase 28. D-40 commits the
  obligation here and executes there.
- **Erasure at higher adapter rank; the frozen-tokenizer retrain** — deferred at v4.0 kickoff under the
  D-16 discipline, unchanged.

</deferred>

---

*Phase: 25-Frontier Sweep and the Existence-Gate Verdict*
*Context gathered: 2026-08-31*
