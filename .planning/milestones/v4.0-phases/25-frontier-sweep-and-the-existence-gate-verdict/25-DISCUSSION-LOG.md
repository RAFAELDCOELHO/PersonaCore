# Phase 25: Frontier Sweep and the Existence-Gate Verdict - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `25-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-08-31
**Phase:** 25-frontier-sweep-and-the-existence-gate-verdict
**Areas discussed:** Control point & SC1 stop rule, Sweep budget, legs & kill-resumability, sigma grid placement & extremes-first, Dual epsilon + frontier artifact contract, Carried-forward obligations, Operational and anchor detail
**Decisions locked:** 44

---

## Control point & SC1 stop rule

### Q1. Re-run the control or import Phase 23's sigma=0 record?

| Option | Selected |
|--------|----------|
| Re-run at both capacities | ✓ |
| Import n=8, run n=64 fresh |  |
| Import recall, re-score extraction |  |

**User's choice:** option 1 — Re-run at both capacities

**Outcome:** D-01 LOCKED: re-run dp_n8 + dp_n64 at sigma=0 under Phase 25's own prefix, scored for recall AND extraction. Phase 23's 0.7837 becomes a declared bit-level reproduction check at seed 1337. CORRECTION APPLIED: C=inf is REFUSED by DPSGD (finite+positive required; 0.0*inf=nan); the repo's representation is a finite bound proven non-binding, so C=1e6 with clip_bind_count==0, the same value as phase23_sigma_zero, which is what makes the reproduction check bit-level. CTRL-02's 'clip_norm=inf' wording flagged for a dated continuation.

### Q2. What binds SC1's 'defensible neighbourhood'?

| Option | Selected |
|--------|----------|
| Discharged by Phase 23's matched verdict |  |
| Superseded by dated continuation | ✓ |
| Keep v2.0 as literal comparator |  |

**User's choice:** option 2 — Superseded by dated continuation. Claude had recommended option 1
(treat SC1 as discharged by Phase 23's matched verdict); the user kept SC1 as an ACTIVE check and
moved only its comparator, so the check survives rather than being retired.

**Outcome:** D-02 LOCKED: SC1 stays an ACTIVE check; its binding comparator is superseded by a DATED CONTINUATION to the Phase 23 MATCHED control (0.7837, floor 0.0268) - the only comparator differing from a real DP point by exactly the two DP parameters, a property v2.0's 0.4921 never satisfied. v2.0 retained as disclosed historical reference with the recipe delta named (held-out denominator 936->648 among others). Original SC1 text stays visible, superseded, never deleted.

### Q3. Does the n=64 leg get its own matched-control floor, at how many seeds?

| Option | Selected |
|--------|----------|
| Full 5-seed ladder at n=64 | ✓ |
| 2 seeds (frozen minimum) |  |
| n=8 only, no n=64 floor |  |

**User's choice:** option 1 — Full 5-seed ladder at n=64

**Outcome:** D-03 LOCKED: full 5-seed SEED_LADDER (1337, 2024, 1338, 2025, 1339) at n=64, own floor reduced by phase23_prereg.noise_floor. ~3.3 h (5 x 23.1 min training + 5 x 16.6 min recall scoring). Same estimator that produced 0.0268 at n=8. No borrowed floor, no capacity asymmetry.

### Q4. How is CTRL-02's non-bit-identity recorded in advance?

| Option | Selected |
|--------|----------|
| Re-probe both capacities + armed tripwire | ✓ |
| Import n=8 figure + armed tripwire |  |
| Record by reference, no tripwire |  |

**User's choice:** option 1 — Re-probe both capacities + armed tripwire

**Outcome:** D-04 LOCKED: re-run PROBE 2's tensor comparison at BOTH capacities before any real sweep point (n=64 never probed - genuine first measurement, not repetition). Commit measured per-tensor agreement as a pre-run record alongside Phase 23's four declared_differences imported by path + digest. Arm a tripwire that FAILS if any later plan asserts bit-identity between the sigma=0 point and the seam-off path. ~46 min.

### Q5. Which question set does the control's extraction scoring use?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-05 LOCKED (user premise VERIFIED TRUE): the identical 416 core_held_out questions (104 x 4 families, family_zero_run False) at draws_per_question=16 from mitigation_budget.CURVE_K - the GATED_TIER extraction_ceiling reads the never-taught floor over. core_taught (448 questions) is ALSO dispatched and reported, as the never-taught record does, but only core_held_out feeds the gate. Measured cost 7334.8 s = 2.04 h per seed for both tiers.

### Q6. Does the n=64 seam-off comparator get its own arm identity?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-06 LOCKED (user premise VERIFIED TRUE, with precedent): yes - phase23_matched_control declared_difference #2 names exactly this hazard and matched_arm(seed) is already distinct from dp_n8. CONVERSE PINNED: the sigma=0 CONTROL POINT keeps arm identity dp_n8/dp_n64 (it IS a DP sweep point per CTRL-02) and is separated by PREFIX only; only the seam-off (dp_fn=None) comparator gets a new arm name. That split is what keeps D-01's bit-level reproduction reachable.

### Q7. What form does the reproduction-miss halt take?

| Option | Selected |
|--------|----------|
| Committed rule + named first suspect | ✓ |
| Halt both capacities, n=8 only anchored |  |
| Halt rule reads recall AND extraction |  |

**User's choice:** option 1 — Committed rule + named first suspect

**Outcome:** D-07 LOCKED: prove_reproduction(k, n) in a committed Phase-25 pre-registration module, called BEFORE any non-control point runs. On a miss it HALTS - zero sweep points - with a message naming the ratio-0.0 byte-identity assertion (f146d426 / a2c4771f) as suspect #1 and the four declared_differences as the starting list, mirroring D-04's halt-message shape. Same structure as phase23_prereg.sigma_zero; refusal watched before it is trusted. Hard equality on integer counts (k == 790, n == 1008), no tolerance.

---

## Sweep budget, legs & kill-resumability

### Q8. All 44 points as pinned, or trim?

| Option | Selected |
|--------|----------|
| All 44 as pinned | ✓ |
| Trim the n=64 DP leg |  |
| Decide after the extremes |  |

**User's choice:** option 1 — All 44 as pinned

**Outcome:** D-08 LOCKED: all 44 run as pinned - SWEEP_POINTS=16 and ADVERSARIAL_RATIO_GRID=6 at both capacities. Neither reopened at the moment of spending; same discipline as the 23-13 blocking checkpoint. N64_LEG_WITHDRAWN stays False on the measured CAL-03 read, preserving the full curve GATE-06 needs so it does not read INCONCLUSIVE by truncation. ~150 h ceiling / ~107 h at the measured rate.

### Q9. Resume granularity for a ~2.2 h scoring leg?

| Option | Selected |
|--------|----------|
| Shape-keyed block resume | ✓ |
| Point-level skip only |  |
| Per-question streaming write |  |

**User's choice:** option 1 — Shape-keyed block resume

**Outcome:** D-09 LOCKED: shape-keyed block resume. Each attack shape's draw block is written to the cache as it completes; driver skips complete shapes on restart. A kill loses <= one shape (~33 min at K=16), not the point. The cache is ALREADY shape-keyed (phase23_run.py:4721). The ancestry-guarded phase18_extraction.py stays untouched - the driver owns the draw loop and calls it only as a scorer, the Phase 23 separation.

### Q10. Unit of the one-attempt rule?

| Option | Selected |
|--------|----------|
| Per point, with block digests committed | ✓ |
| Per point, resume freely |  |
| Per sweep, Phase 23's literal shape |  |

**User's choice:** option 1 — Per point, with block digests committed

**Outcome:** D-10 LOCKED: the SWEEP POINT, not the sweep. A point with a committed reading is evidence and is never re-run (prove_first_attempt's glob = the committed per-point records). A point killed mid-scoring produced no reading, so resuming it is the SAME attempt. Each completed shape block's sha256 is committed as it lands, closing the sub-point leak that would otherwise let a deletion-and-redraw leave no trace in gitignored data/.

### Q11. GATE-08 replication + full-fidelity promotion budget?

| Option | Selected |
|--------|----------|
| Lazy, replicate at K=48 | ✓ |
| Lazy, replicate at K=16 |  |
| Eager - every point at two seeds |  |

**User's choice:** option 1 — Lazy, replicate at K=48

**Outcome:** D-11 LOCKED: lazy, candidate-triggered. All 44 curve points at CURVE_K=16 first; only points clearing all three conditions are promoted to K=48 AND replicated at a second seed AT K=48 - never a lower-power replication. Empty frontier (the pre-registered null, live given epsilon=519.70 at sigma=0.5) means zero tail cost. PRE-REGISTERED RULE, user-stated: if MORE candidates clear than budget holds, promote and replicate ALL of them - never a subset chosen after seeing which cleared.

### Q12. How is the execution venue hardened for 4.5-6.3 days?

| Option | Selected |
|--------|----------|
| launchd + own caffeinate + heartbeat | ✓ |
| Same plus pmset change |  |
| nohup + setsid + caffeinate |  |

**User's choice:** option 1 — launchd + own caffeinate + heartbeat

**Outcome:** D-12 LOCKED: user LaunchAgent, not a harness background child - survives session end, compaction and logout, stdout/stderr to file. Wraps itself in `caffeinate -dims` holding its OWN idle-sleep assertion. KeepAlive FALSE: auto-restart would re-enter a point without passing the driver's deliberate resume logic, violating D-10. Heartbeat line (utc, point, shape, draw index) makes any future kill diagnosable rather than a zero-traceback mystery. MEASURED HAZARD: pmset reads `sleep 1` on AC and battery, held off only by transient assertions including 5 stray caffeinate processes and Claude itself.

### Q13. Add the system-level pmset change as a second layer?

| Option | Selected |
|--------|----------|
| Yes - scoped and reverted | ✓ |
| No - caffeinate only |  |
| Decide at run time |  |

**User's choice:** option 1 — Yes - scoped and reverted

**Outcome:** D-13 LOCKED: yes. `sudo pmset -a sleep 0 disksleep 0 powernap 0` before the sweep, reverted to the current values (sleep 1, disksleep 10, powernap 1) at the end. Both acts recorded as a dated operational note in the phase record. THE REVERT IS A COMMITTED PLAN STEP, verifiable, never dependent on human memory. Genuinely independent of layer one, covering the failure modes caffeinate alone cannot reach.

### Q14. When is adversarial scoring throughput measured?

| Option | Selected |
|--------|----------|
| Pre-schedule probe at upper extreme |  |
| Probe both adversarial extremes | ✓ |
| Fold into extremes-first |  |

**User's choice:** option 2 — Probe both adversarial extremes. Claude had recommended probing only
the upper extreme; the user added ratio 0.0 so the throughput SPREAD is measured rather than
extrapolated from one point, and so ratio 0.0 anchors against the already-measured non-DP 161.1 s.

**Outcome:** D-14 LOCKED: probe BOTH adversarial extremes before the schedule is committed - train one adv_n8 at ratio 0.0 and one at 1.9090909090909092, each with a timed 768-draw throughput probe (CAL-05's own n_draws_measured). ~30 min. Ratio 0.0 anchors against the measured non_dp 161.1 s (seam-off twin of the matched comparator, bins byte-identical to v2.0); 1.909 measures the extreme most likely to diverge. Schedule finalised only after both points confirm the throughput curve's real shape, never extrapolated from one. CORRECTION RECORDED: adversarial TRAINING is bounded above by measured figures (non_dp 161.1 s, dp_n64 1383.3 s) - 0.5-4.6 h over 12 points; the genuinely unmeasured term is SCORING, ~95% of the spend.

### Q15. What order do the 44 points run in?

| Option | Selected |
|--------|----------|
| All four legs' extremes first, then interiors | ✓ |
| Extremes per leg, legs sequential |  |
| Extremes then cheapest-first interiors |  |

**User's choice:** option 1 — All four legs' extremes first, then interiors

**Outcome:** D-15 LOCKED: the EIGHT extremes run before any interior point, INTERLEAVED across the four legs - DP x {n8,n64} at sigma->0 and at the never-taught end, adversarial x {n8,n64} at ratio 0.0 and 1.909. Not one leg exhausted before the next. A structural problem at any of the four corners appears on day one, not after days invested in a single arm. The low extremes are already the D-01 control points and the ratio-0.0 arms, so this is sequencing, not new work.

### Q16. Does heartbeat silence trigger anything?

| Option | Selected |
|--------|----------|
| Silence for N minutes is a recorded stall event | ✓ |
| Post-mortem only |  |
| Watcher may restart the driver |  |

**User's choice:** option 1 — Silence for N minutes is a recorded stall event

**Outcome:** D-16 LOCKED: a separate lightweight watcher (second LaunchAgent or periodic check) reads the heartbeat file; if it has not advanced in N minutes it writes a timestamped stall record and notifies - with NO corrective action: never restarts, never kills, never cleans up. N is derived from the measured worst-case gap between heartbeat lines at the slowest attack shape, not chosen by convention. Detection and correction stay structurally separate, so D-10 stays intact and nothing automated can re-enter a point.

---

## sigma grid placement & extremes-first

### Q17. How are the 16 DP points placed and in which quantity pinned?

| Option | Selected |
|--------|----------|
| sigma literals landing on an epsilon ladder | ✓ |
| Log-spaced in sigma |  |
| Dense where extraction collapses |  |

**User's choice:** option 1 — sigma literals landing on an epsilon ladder

**Outcome:** D-17 LOCKED: sigma pinned as float literals in mitigation_budget.py (forced - capacity_comparison compares sigma exactly and the literal-only ast.literal_eval guard forbids a derived sigma_for() call). THE SAME LADDER IS REUSED AT BOTH CAPACITIES, satisfying MECHANISM_KEYS exact equality trivially because it is one set reused, not chosen per capacity. Values chosen so epsilon_for(sigma, 200, 1e-5) lands on a pre-registered round epsilon ladder, committed alongside, with a LIVE test (test_phase24_grid's shape) asserting the correspondence under exact ==, no tolerance. MEASURED CURVE: sigma 0.5->eps 519.70, 1.0->159.44, 2.0->54.38, 8.0->8.60, 20->2.94, 80->0.63; eps=8 needs sigma=8.49, eps=1 needs sigma=52.76.

### Q18. How is the high anchor verified rather than presumed?

| Option | Selected |
|--------|----------|
| Calibration probe + ratchet extension rule | ✓ |
| Calibration probe only |  |
| Extension rule only |  |

**User's choice:** option 1 — Calibration probe + ratchet extension rule

**Outcome:** D-18 LOCKED: probe one or two candidate sigma_hi under a NAMED CALIBRATION PREFIX, recall-only (~20 min each, ~996 s scoring), excluded from the sweep's point set exactly as phase23_sigma0 was. The ladder is committed only after the probe confirms the high anchor. A ratchet-shaped EXTENSION RULE is committed alongside: if the high extreme's FULL extraction read still misses the never-taught floor, the grid EXTENDS upward by a pre-registered rung (halve epsilon) - never shifts, never shrinks. The low anchor needs no probe: sigma=0 IS the control and reconnects by construction.

### Q19. The adversarial curve has no parameter reaching the never-taught floor. How handled?

| Option | Selected |
|--------|----------|
| Named structural asymmetry + shared floor | ✓ |
| Extend past the pool ceiling |  |
| Publish as open-ended |  |

**User's choice:** option 1 — Named structural asymmetry + shared floor

**Outcome:** D-19 LOCKED: named as a STRUCTURAL asymmetry, not a deficit. The DP axis has a physical mechanism driving utility toward zero under high noise; the adversarial axis terminates at its POOL CEILING by construction (1.909 = largest ratio at which the whole trained pool is used exactly once). Dated continuation corrects FRONT-01's 'swept to the never-taught floor' to a DP-arm property, original text left visible and superseded. BOTH arms are read against the SAME already-measured never-taught floor (0/416, 5 seeds, results/phase23_never_taught.json) as the plane's shared lower-left reference; no adversarial point needs to reach it personally.

### Q20. Is sigma=0 inside SWEEP_POINTS=16 or a 17th point?

| Option | Selected |
|--------|----------|
| Inside the 16 | ✓ |
| A 17th point outside |  |

**User's choice:** option 1 — Inside the 16

**Outcome:** D-20 LOCKED: INSIDE the 16 - 15 noised points per DP leg, control at slot 1. Two converging lines of evidence: SWEEP_POINTS_PROVENANCE.governs reads 'frontier points per leg, and nothing else' with CTRL-02 confirming the control as a real sweep point; and phase23_cost.sizing['16'] prices 16 points plus the never-taught floor as a separate term, never reserving budget for a 17th. Total stays 44.

### Q21. Is K recorded alongside every epsilon reading?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-21 LOCKED (user premise VERIFIED, precedent exists): every epsilon reading in the frontier artifact carries its own `k` and `k_source` INLINE, not as separately-consultable metadata. results/phase23_never_taught.json already records draws_per_question: 16 with draws_per_question_source: 'mitigation_budget.CURVE_K' on every per-seed block. A K=16 curve reading and a K=48 promoted reading of the same point have NUMERICALLY IDENTICAL epsilon and differ only in statistical precision, so they must never be confusable.

### Q22. Are the six adversarial ratios identical across both capacities?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-22 LOCKED (user premise VERIFIED, nothing contradicts it): yes. ADVERSARIAL_RATIO_GRID is a single tuple whose governs reads 'adversarial sweep points PER CAPACITY'; 24-07 measured all four corners of {adv_n8, adv_n64} x {0.0, 1.909}; multiplicity_at_upper_extreme {dp_n8: 1.0, dp_n64: 8.0} is a REPORTED property, not a grid variable.

### Q23. What governs the adversarial arm's n=8 vs n=64 comparison?

| Option | Selected |
|--------|----------|
| DP-only by construction, named as a limitation | ✓ |
| Commit an adversarial capacity rule |  |
| Force it with a pseudo-mechanism |  |

**User's choice:** option 1 — DP-only by construction, named as a limitation

**Outcome:** D-23 LOCKED: NOTHING in the gate does, and that is named rather than patched. capacity_comparison takes no `arm` argument (zero occurrences in its body) and _proves all four MECHANISM_KEYS present AND exactly equal; the adversarial arm has no sigma/delta/q - the same fact accounting: null states structurally. So GATE-10 stays a DP-ONLY instrument by construction. The two adversarial capacities are reported side by side DESCRIPTIVELY, and the absence of a committed capacity rule for that arm is named explicitly in the artifact and the report rather than left for a reader to trip over. v2.0's 'gate only what the measurement supports' precedent.

### Q24. What value does the clip norm C take across the DP grid?

| Option | Selected |
|--------|----------|
| Calibrate then pin | ✓ |
| Pin C=1.0 on precedent |  |
| Pin C=1.0, measure descriptively |  |

**User's choice:** option 1 — Calibrate then pin

**Outcome:** D-24 LOCKED: CALIBRATED, not inherited. Run one vmap per-example gradient pass at both capacities (seconds to minutes; machinery built in Phase 22 and exact to 6.5e-08) to get the real PER-RECORD norm distribution on the DP path - never measured before, only batch-level norms on the non-DP path exist (grad_clip_evidence max 2.20-2.30). Pin C as a SINGLE float literal in mitigation_budget.py with a _PROVENANCE sibling naming the measurement. Also resolves whether 100% binding at C=1.0 (phase23 dp_n64: clip_bind_count 12800 of 12800) is a sensible operating point or an accident of one run. At fixed sigma, a C below every record's norm is pure clipping bias bought for nothing, since epsilon does not improve.

### Q25. C is not in MECHANISM_KEYS but std = sigma * C. How is the hole closed?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-25 LOCKED, with two corrections to the initial plan. (a) C CANNOT join MECHANISM_KEYS: scripts/mitigation_gate.py is frozen - the ancestry guard takes adds[-1], the EARLIEST add, so any new commit to it after results/phase20_* exists reddens the guard permanently and a git rm + re-add cannot launder it. (b) It does not need to: capacity_comparison's check is `missing = [key for key in MECHANISM_KEYS if key not in ...]`, so EXTRA keys are IGNORED, not refused. The closure is CALLER-SIDE - clip_norm travels in the mechanism dicts and the Phase 25 driver _proves equality on it BEFORE calling the gate. Gate untouched; the gap fails loudly. Made true by construction by D-24's single literal across the whole grid.

### Q26. Does q=1.0 hold given the with-replacement window sampler?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-26 LOCKED (premise VERIFIED - the gap is real and is exactly why the fact unit exists): mitigation_unit.PRIVACY_UNIT_ARITHMETIC names it verbatim - get_batch_memmap_masked draws window offsets 'with replacement, and with no notion of where one fact ends and the next begins', so a fact is touched an expected 262.94 times over 1600 draws, which is WHY an example-level epsilon says nothing about a fact. The DP path does not use that sampler for private data: under fact-aligned accumulation (Phase 21 D-01/D-05/D-06) the quantity is 'exactly 1 per micro-step, deterministic, by construction - which is what makes SAMPLING_RATE_Q = 1.0 honest rather than assumed'. q=1 holds because the private lot IS the fact set.

### Q27. Is STEP_BUDGET=200 literally the T composed at both capacities?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-27 LOCKED (premise VERIFIED by measurement, not inference): phase23_sigma_zero records composed_steps 200 / composed_lot_sizes [8] / records_per_lot 8; phase23_noised_dp_n64 records composed_steps 200 / composed_lot_sizes [64] / records_per_lot 64 AND t_matches_across_capacities: true. grad_accum_steps = n_facts governs micro-steps INSIDE one optimizer step; composed T is optimizer steps and is capacity-independent.

---

## Dual epsilon + frontier artifact contract

### Q28. What IS the example-level epsilon FRONT-02 requires?

| Option | Selected |
|--------|----------|
| The counterfactual with both multiplicities | ✓ |
| Declare not computable |  |
| Same number under both units |  |

**User's choice:** option 1 — The counterfactual with both multiplicities

**Outcome:** D-28 LOCKED: report the REAL fact-level epsilon (what actually governs this path) beside what an example-level accounting WOULD have claimed under the unaligned with-replacement sampler - the flattering number a reader might wrongly assume applies. BOTH multiplicities named explicitly: 207.018 (first-token-owns-draw, the artifact rule) and 262.944 (the frozen pin's overlap rule), since phase21_multiplicity records that discrepancy as RECORDED, NOT RESOLVED by design. Neither hidden. FRONT-02 met in its strongest form: it SHOWS the size of the error confusing the granularities would make, rather than only asserting it would be wrong.

### Q29. What is the curve-total epsilon?

| Option | Selected |
|--------|----------|
| Basic composition, control disclosed unbounded | ✓ |
| Advanced composition |  |
| Per-leg totals only |  |

**User's choice:** option 1 — Basic composition, control disclosed unbounded

**Outcome:** D-29 LOCKED: sum of the point epsilons over the noised DP points actually PUBLISHED, total delta = k*delta - BASIC composition, conservative, computable from the existing stdlib accountant, zero new chosen constant. Declared alongside: the sigma=0 control has NO epsilon (phase23_sigma_zero records epsilon: None) and is an adapter trained on the same facts with no privacy, so once it is published NO joint bound over all published artifacts exists. selection_accounted = False, naming that choosing a best point after seeing results would be unaccounted adaptive selection. The total CROSSES both legs (n=8 and n=64), not per-leg: the 8 locked facts appear in both, and splitting would hide exactly the cumulative exposure that matters most.

### Q30. What enforces 'no bare epsilon outside the helper'?

| Option | Selected |
|--------|----------|
| Three required kwargs + AST gate | ✓ |
| Non-printable Epsilon wrapper |  |
| Helper + naming convention + grep |  |

**User's choice:** option 1 — Three required kwargs + AST gate

**Outcome:** D-30 LOCKED: helper takes point_epsilon, curve_total_epsilon and selection_accounted as keyword-only args with NO defaults (the gate's own 21-kwarg precedent - the length IS the protection). Enforcement is an AST GATE over the phase's modules: any print / f-string / .format / %% whose operand resolves against a committed epsilon-name set, outside the helper's own body, fails the test. AST deliberately over grep - a grep over files whose prose discusses epsilon goes false-RED, a class this session hit repeatedly.

### Q31. How is the frontier artifact written and what does it carry?

| Option | Selected |
|--------|----------|
| Per-point records + write-once assembly | ✓ |
| Frontier as an index |  |
| Inline only the gated tier |  |

**User's choice:** option 1 — Per-point records + write-once assembly

**Outcome:** D-31 LOCKED: each point writes its OWN committed record as it completes - that record IS D-10's one-attempt glob and D-09's resume unit, no new structure. results/phase25_frontier.json is assembled ONCE at the end from those records, with ordered point_keys equality proved at that single write, accounting: null on the adversarial arm, gate and budget module sha256s travelling inside it, and per-question successes INLINE for all 44 points (~9.7 MB; direct precedent phase18_arm_adapter-on.json at 2.7 MB, phase23_never_taught.json at 1.1 MB for 4320 rows). FILENAME PINNED: results/phase25_frontier.json - the roadmap's `phase2X_frontier.json` is a PLACEHOLDER, not a filename. Single source of truth in the strong sense FRONT-03 promises: no bound requires a second file, no tier split across places.

### Q32. Which committed name carries FRONT-04's null verdict?

| Option | Selected |
|--------|----------|
| null-at-both-capacities | ✓ |
| A Phase 25 verdict constant |  |
| V4_VERDICTS FAIL with branch as detail |  |

**User's choice:** option 1 — null-at-both-capacities

**Outcome:** D-32 LOCKED: the gate's EXISTING branch null-at-both-capacities (CAPACITY_BRANCHES, reached via _CAPACITY_DISPATCH[(False, False)], dispatch totality proved at module scope), paired with exists_clearing_point's own denominator-carrying string ('0 of N point(s) examined returned PASS'). Nothing new authored in the phase that runs the sweep - exactly what FRONT-04 exists to protect.

### Q33. What enforces 'every figure drawn only from the artifact'?

| Option | Selected |
|--------|----------|
| Phase 15's guard retargeted | ✓ |
| AST-only, no interpreter probe |  |
| Convention plus review |  |

**User's choice:** option 1 — Phase 15's guard retargeted

**Outcome:** D-33 LOCKED: reuse Phase 15's shipped pattern - AST walk over the plotting module's imports PLUS a fresh-interpreter probe that FAILS if torch lands in sys.modules - retargeted so the module may open results/phase25_frontier.json and nothing else. PROJECT.md already records this as one of three conversions from declared invariant to checked mechanism; Phase 23's D-09 applied the mirrored form to the budget-import guard.

### Q34. What happens on a live mechanism mismatch at point write?

| Option | Selected |
|--------|----------|
| Halt, same weight as D-07 | ✓ |
| Refuse the point, continue |  |
| Record the divergence and publish |  |

**User's choice:** option 1 — Halt, same weight as D-07

**Outcome:** D-34 LOCKED: every point record carries composed_steps, composed_lot_sizes, records_per_lot, q and clip_norm read LIVE at write time, asserted against the pinned values under EXACT equality. Any divergence HALTS THE WHOLE SWEEP, not a logged warning - a point whose mechanism diverged from the pin has an epsilon that does not describe what happened, and publishing that is the single most dangerous error class v4.0 research named. Same structural weight D-07 gives the control's reproduction miss.

### Q35. Does any gate code assume non-null accounting as a precondition for the verdict machinery?

*No options presented — resolved by direct measurement against the source or a committed record.*

**Outcome:** D-35 LOCKED (premise VERIFIED, stronger than stated): NO. mitigation_point_verdict contains ZERO occurrences of `epsilon` or `accounting` across its 198 lines - its 21 kwargs are all counts, recalls, perplexities and floors. The three-condition reading is ARM-AGNOSTIC BY CONSTRUCTION, not by convention. X, Y and (c) never depended on epsilon; only the formal accounting does, and capacity_comparison is the only epsilon-dependent function (already scoped DP-only by D-23). Nothing to fix.

### Q36. What shape does A2's held-out generalization take in the artifact?

| Option | Selected |
|--------|----------|
| Per-point fields + re-derivable aggregate | ✓ |
| Per-point fields only |  |
| Aggregated section only |  |

**User's choice:** option 1 — Per-point fields + re-derivable aggregate

**Outcome:** D-36 LOCKED: per-point per-family counts INCLUDING A2 alongside the three trained families - nearly free, since A2 is already one of the four scored shapes across all 416 gated questions (generation.attack_shapes: A1-mild, A1-aggressive, A2, A3; 416 = 104 x 4). The final assembly computes a held_out_generalization section FROM those fields, with a write-time assertion that the aggregate re-derives EXACTLY from the per-point counts. The aggregate can never drift from the data supporting it.

### Q37. What does Phase 25 reserve for Phase 26's canary audit?

| Option | Selected |
|--------|----------|
| Adapters + in/out population + designation rule | ✓ |
| Adapters and sha256 only |  |
| Adapters + designation rule, population later |  |

**User's choice:** option 1 — Adapters + in/out population + designation rule

**Outcome:** D-37 LOCKED: three reservations, free now and expensive later. (i) Every point's adapter RETAINED on local disk with its sha256 recorded INSIDE the frontier artifact - checkpoints/ and *.pt are gitignored (.gitignore:14-15), so without this the audit has nothing to run against and a deleted adapter cannot be re-derived without re-running the point. (ii) The in/out canary population recorded PER POINT: at n=8 the 56 filler facts are OUT, at n=64 all 64 are IN - so ONLY n=8 points have out-of-corpus canaries, a structural constraint written down BEFORE the sweep rather than discovered after. (iii) A committed rule naming WHICH point the audit targets, written before any point exists, so the choice cannot be made after seeing the data.

---

## Carried-forward obligations

### Q38. RPT-02 is deferred to Phase 25 but absent from its Requirements line. How closed?

| Option | Selected |
|--------|----------|
| Add RPT-02 to Phase 25's line | ✓ |
| Leave deferred to Phase 28 |  |
| Discharge without roadmap edit |  |

**User's choice:** option 1 — Add RPT-02 to Phase 25's line

**Outcome:** D-38 LOCKED: add RPT-02 to ROADMAP Phase 25's **Requirements** line and record the span ADDITIVELY under REQUIREMENTS Traceability - the same repair ADVT-01 already needed. Phase 25 discharges the unmet second half by routing its two dated continuations (D-02's SC1 comparator, D-19's FRONT-01 scope) through scripts/_prose.py::normalized rather than through grep - under the requirement's own regulation, not beside it. WITHOUT THIS NO PHASE CAN TICK RPT-02.

### Q39. UAT item 3: 24-04's refusal instrumentation has no production caller.

| Option | Selected |
|--------|----------|
| Wire into the sweep driver | ✓ |
| Declare unreported |  |
| Wire and gate on it |  |

**User's choice:** option 1 — Wire into the sweep driver

**Outcome:** D-39 LOCKED: wire contains_refusal / score_refusal / clean_frame_probe_populations into the Phase 25 driver - every adversarial point carries a refusal-rate column in COUNTS, never rates, the shape FRONT-03 already demands. Measures the arm's REAL mechanism (is the refusal working or not), diagnostic information otherwise entirely absent from the artifact. Fits D-36's per-family counts with no new structure. USER CONSTRAINT: it stays OUTSIDE the three-condition gate - reported information, never a verdict condition - preserving the closed domain GATE-07/D-29 protect.

### Q40. Where does the frontier verdict get published?

| Option | Selected |
|--------|----------|
| Commit obligation now, publish in Phase 28 | ✓ |
| Phase 25 writes docs/REPORT.md |  |
| Leave venue to Phase 28 entirely |  |

**User's choice:** option 1 — Commit obligation now, publish in Phase 28

**Outcome:** D-40 LOCKED: obligation COMMITTED NOW, publication executed in Phase 28 ('Report, the Published Null, and Milestone Close', which owns RPT-01). Phase 25 does not write the report; it commits, BEFORE any point exists, exactly which strings from the artifact the report must carry: the arm-level existential WITH its denominator, the capacity branch name, the curve-total epsilon with selection_accounted, and the named limitations (adversarial capacity rule absent, curve total unbounded once the control is published).

### Q41. How are 24-REVIEW's 8 warnings triaged against the sweep?

| Option | Selected |
|--------|----------|
| Fix the 5 that touch the sweep | ✓ |
| Fix all 8 |  |
| Defer all 8 |  |

**User's choice:** option 1 — Fix the 5 that touch the sweep

**Outcome:** D-41 LOCKED: fix the FIVE that touch the real sweep before any point runs - WR-01 (property guard against a NaN/negative ratio building the control under an adversarial name; the 'guard refuses a NAME where the harm is a PROPERTY' class Phase 20 recorded twice), WR-04 (replay_ratio ceasing to describe the bin, against D-34's live mechanism assertion), WR-05 (the multiplicity pin's arm keys, which D-22 leaned on), WR-06 (index-paired corpus reads, which would corrupt D-36's per-family counts), WR-08 (bins on disk before proofs 1-3 run, colliding with refuse_if_exists and D-10). DEFER WR-02, WR-03, WR-07 with their unreachability RECORDED explicitly, never silenced (n_want<1 is unreachable at 176/1408 clean episodes; WR-07 is test-literal hygiene).

---

## Operational and anchor detail

### Q42. Which never-taught reading does Phase 25 pass into extraction_ceiling?

| Option | Selected |
|--------|----------|
| Designated-seed pooled block 0/416 | ✓ |
| Pooled across 5 seeds 0/2080 |  |
| Both, one gated one descriptive |  |

**User's choice:** option 1 — Designated-seed pooled block 0/416

**Outcome:** D-42 LOCKED: the already-committed designated-seed `pooled` block in phase23_never_taught.json - SEED_LADDER[0], pooled across the four dose-split families - passed VERBATIM, never re-reduced. X = wilson_upper_bound(0, 416) = 0.00646169 (extraction_noise_floor is 0.0 so the MARGIN_K term contributes nothing); tolerance = at most 2 successes of 416. Pooling all five seeds (0/2080 -> X = 0.00129905, 4.97x tighter, tolerance 0 of 416) would treat five correlated adapters (one base, one fact set) as independent samples, narrowing the bound on evidence that is not independent - and it would be a reduction chosen in the phase that runs the sweep, the risk D-08 already refused for other resource parameters. VERIFIED: extraction_ceiling reads the single designated seed as a WILSON UPPER BOUND, with the 5-seed range entering only as the noise-floor margin - multi-seed evidence sits exactly where seed-to-seed variation belongs, and each sweep point is single-seed at K=16 over the same 416 questions.

### Q43. Are the 5 stray caffeinate processes cleared before the sweep?

| Option | Selected |
|--------|----------|
| Clear them, verify in isolation | ✓ |
| Leave them, harmless |  |

**User's choice:** option 1 — Clear them, verify in isolation

**Outcome:** D-43 LOCKED: terminate the leftover assertions before the sweep starts. The run's own `caffeinate -dims` becomes the ONLY non-system assertion held, VERIFIED by reading `pmset -g` back after launch and recording that line in the operational note. Without it D-12's whole mechanism could be masked by residue - the run would appear to hold the machine awake while a stray process from an earlier session genuinely does it.

### Q44. MPS-touching tests will run and contend during the sweep. What happens?

| Option | Selected |
|--------|----------|
| Explicit sweep-active skip, loudly reported | ✓ |
| Let them run and contend |  |
| Do not run the suite during the sweep |  |

**User's choice:** option 1 — Explicit sweep-active skip, loudly reported

**Outcome:** D-44 LOCKED: an env var (or pytest option) active during the sweep makes the MPS-touching legs SKIP with a reason NAMING the sweep explicitly - test_mps_smoke, test_phase23_mps_venue, and the MPS params in test_phase22_fakes / test_phase22_checkpoint / test_phase22_dpsgd. The CPU-only bulk of the ~1647 tests keeps running normally. MEASURED CAUSE: every MPS leg is skipif-gated on torch.backends.mps.is_available(), which is TRUE during the sweep, so they would otherwise run and contend. A contention failure can then never be mistaken for a genuine one, and the skip reason names why rather than vanishing into a count.

---

## Claude's Discretion

Recorded in `25-CONTEXT.md` `<decisions>` → *Claude's Discretion*: the concrete σ literals and ε rungs,
the D-18 probe's candidate σ_hi values, `N` in D-16's heartbeat threshold, the LaunchAgent plist and
heartbeat file shape, the `point_keys` grammar, whether D-24's norm probe reuses `phase23_cost`'s timing
harness, and three plan-level items the user explicitly declined to spend a turn on (log rotation, the
commit branch, the ~59 MB disk precheck).

## Corrections produced by this discussion

Nine premises were checked against source or measurement rather than accepted. Five came back false or
materially incomplete and are recorded in `25-CONTEXT.md` `<domain>`:

1. `clip_norm=inf` is refused by `DPSGD` — CTRL-02's wording needs a dated continuation.
2. SC1's comparator (v2.0's 0.4921 / 0.3483) does not describe any control this milestone can run.
3. FRONT-01's "swept to the never-taught floor" is a DP-arm property only.
4. `capacity_comparison` cannot run on the adversarial arm at all.
5. `C` is pinned nowhere and sits outside `MECHANISM_KEYS` while `std = sigma * C`.
6. `results/phase2X_frontier.json` is a placeholder, not a filename.
7. RPT-02 is an orphaned requirement of the ADVT-01 shape.
8. Adversarial *training* cost is bounded by measured figures; *scoring* is the unmeasured term.
9. The suite's MPS legs are `skipif`-gated on availability, which is TRUE during the sweep.

Four premises were checked and confirmed **true**, with no change required: the `core_held_out`
question set (D-05), the seam-off arm-naming hazard (D-06), q = 1.0 under fact-aligned accumulation
(D-26), and T = 200 at both capacities (D-27). One was confirmed *stronger* than stated — the
three-condition gate is arm-agnostic by construction, with zero `epsilon`/`accounting` references in
its 198 lines (D-35).

## Deferred Ideas

See `25-CONTEXT.md` `<deferred>`: WR-02 / WR-03 / WR-07, 24-09's six INFO findings, Phase 24 HUMAN-UAT
item 2, Phase 22's WARNING-4 and WARNING-5, and the Phase 26 / 27 / 28 scope boundaries.

---

# Session 2 — Condition (c) reopening (2026-08-31)

**Why reopened.** Plan-check iteration 2 found that condition (c) of the three-condition gate had
**no measured inputs anywhere in the 20-plan set**: 7 of `mitigation_point_verdict`'s 21 required
kwargs had zero producers, six of them condition (c), and `condition (c)` appeared 0 times across the
plans. D-35 had declared "Nothing to fix" about the three-condition reading. The user stopped the
plan-revision loop and routed the correction through discussion — *"essa correção de decisão travada
precisa do mesmo processo de discussão que produziu as 44 decisões originais, não correção silenciosa
dentro do ciclo de revisão de planos."*

## Areas presented

Four; the user selected 1–3 and settled 4 from the cost figures alone.

### Area 4 — Scope (settled without discussion)
**User:** all 44 points. *"0.7-1.0% kills the only argument for a subset, and post-hoc selection is
forbidden by the same discipline governing everything else."* → **D-45**

### Area 1 — GATE-05 / teacher-forced NLL
- **Options:** (1) 8 locked facts at both capacities · (2) full taught set per capacity ·
  (3) both, locked set gating
- **User chose (3)**, having stated the position first: the NLL must be measured per point and not
  deferred, *"since without it the pre-registered null (zero extraction under high noise) is
  structurally unreachable by the gate's own INCONCLUSIVE early-return."*
- **Reasoning recorded:** 8 locked facts gate at both capacities (comparable quantity, D-29's
  crossing reasoning); full taught set reported beside as diagnostic, never a verdict input —
  D-39's architecture and D-05's. → **D-46**

### Area 2 — the two noise floors' recipe mismatch
- **User's stated position, with a premise to check first:** D-02's treatment (import as-is, disclose
  via dated continuation) *"unless the magnitude of mismatch is large enough to argue for
  re-measurement — needs checking before accepting precedent, same discipline that verified every
  prior analogous case."*
- **The check was run, and it split the two legs:**
  - **Dialogue:** floor contributes **1.65%** of the band width; a 10× error moves the ceiling by
    14.86% of the band, because `F_C = 0.5` makes `control_gap` dominate. **Immaterial as measured.**
  - **Retention:** the floor is the entire margin — and the v3.0 taught adapter **already FAILS** the
    cap by **+0.190760** (`4.219760` vs `4.029000`), needing a **2.38×** larger floor to be admitted.
    Phase 19 recorded this itself (`adapter_on_headroom: -0.1907598923364855`); no plan surfaced it.
- **Options:** (1) import + pre-register the squeeze · (2) re-measure the retention floor at the v4.0
  recipe · (3) import + pre-register + report the counterfactual
- **User chose (3).** Re-measuring was rejected on D-42's grounds — an outcome-affecting threshold
  re-derived inside the phase that runs the sweep. → **D-48, D-49, D-50**

### Area 3 — `control_gap` per capacity or shared
- **User chose per-capacity** before options were presented, on D-03's precedent: *"never borrowing a
  floor across capacities — each capacity gets its own control_gap from its own already-running σ=0
  control (D-01)."* Free, since D-01 already runs the control at both capacities. → **D-47**

## Measurements taken during this session

| Quantity | Value |
|---|---|
| `dialogue_ppl_pair` (ON+OFF) | 43.5 s |
| `retention_perplexity` | 43.9 s |
| condition (c) per point | **87.4 s** → 1.07 h over 44; 0.80 h with OFF measured once |
| share of the 107–150 h budget | **0.7–1.0%** |
| reproduction vs `phase19_arm_erased.json` | **exact**, all four figures + both denominators |
| dialogue band | `[0.621048, 1.252526]`, width `0.631477`; floor term `0.010429` = **1.65%** |
| retention cap vs taught adapter | `4.029000` vs `4.219760` → excess **+0.190760**, **2.38×** |

## Scope creep

None raised. The reopening stayed inside condition (c) and its immediate neighbours; the other 43
decisions were not re-litigated.

## Claude's discretion (recorded)

- The per-point record field names for the (c) legs and the D-50 counterfactual, provided the
  write-time assertion proves the counterfactual re-derives from the sweep's own seed-to-seed spread.
- Whether the OFF leg is measured once per capacity or once per sweep (it is base-model identical
  either way; `adapter_off_identical_across_seeds` is `true`).
- Where the teacher-forced NLL producer lives — inside the point loop or as a sibling scorer.
