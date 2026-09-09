---
phase: 25
plan: 18
subsystem: verdict-and-promotion
tags: [D-11, D-16, D-29, D-34, D-42, D-46, D-47, FRONT-01, FRONT-04, GATE-06, GATE-08, GATE-10, verdict, promotion, recall]
requires:
  - results/phase25_point_*.json (44)
  - results/phase23_never_taught.json
  - results/phase25_n64_matched_floor.json
  - scripts/phase25_verdict.py
  - scripts/mitigation_gate.py (frozen)
provides:
  - results/phase25_recall.json
  - results/phase25_promotion.json
  - scripts/phase25_recall.py
  - scripts/phase25_promotion.py
  - artifacts/com.personacore.phase25.recall.plist
  - tests/test_phase25_recall.py
  - tests/test_phase25_promotion.py
affects: [25-19, 25-20]
tech-stack:
  added: []
  patterns:
    - "a missing verdict input is produced with the controls' own instrument on every point, never a subset, before any verdict is seen"
    - "a route refusal is the leg's recorded result: the record keeps it verbatim and the test watches it fire"
decisions:
  - "D-25-18-RECALL (Rule 4, operator 2026-09-08): condition (b) had no per-point producer — the sweep driver scored recall only under is_control, 42/44 records lacked taught/held-out recall; all 42 adapters scored with teach_persona.score_arm (15.77 h MPS) into results/phase25_recall.json, point records byte-unchanged."
  - "D-25-18-ADV64-REFUSED (Option A, orchestrator 2026-09-09): the adv_n64 leg is refused by phase20_gate_coverage.corrected_point_verdict because its own control scored held-out 0/648 (Y_heldout = 0); the refusal is the recorded result, nothing borrowed (Option B rejected under D-16/D-47), reversible in seconds."
  - "The venue skip literals are continued (36->39, 1->4) beside 25-06's numbers for the three artifact-gated promotion skips, never edited."
metrics:
  duration: "recall leg 2026-09-08 10:23 UTC -> 2026-09-09 ~01:30 UTC (15.77 h scoring, one launch, no kills); verdict pass seconds on CPU; code + tests ~5 h across three sessions"
  completed: 2026-09-09
---

# Phase 25 Plan 18: The Curve Verdict and the Promotion Rule Summary

**The frontier is empty, and it is recorded as a reached branch.** All 44 points were judged on
CPU from whole-curve inputs through the sanctioned route; **0 of 32 DP points and 0 of 6 scorable
adversarial points returned PASS**, the capacity branch is the gate's own `null-at-both-capacities`
on all 16 sigma pairs, `candidates: []`, `tail_cost_hours: 0`. The pre-registered null is live:
epsilon is 519.6981942303134 at sigma=0.5 and condition (a) is ZERO TOLERANCE. Two things the plan
did not foresee were found by measurement, not assumed: condition (b) had **no per-point producer**
(42/44 records carried no recall), and the adversarial n=64 leg is **refused** by the committed
route because its own control has zero held-out recall. Both are recorded, neither is routed around.

## Task 0 — D-25-18-RECALL: condition (b)'s missing producer (Rule 4 deviation)

**Measured at Task 1's read-first.** Only `dp_n8_sigma0p000000` (790/1008, 346/648) and
`dp_n64_sigma0p000000` (87/1008, 35/648) carried `taught_recall`/`heldout_recall`; the other
**42/44** carried neither (`scripts/phase25_points.py::measure_stage` scores recall under
`if plan["is_control"]:` only; `25-14-SUMMARY.md` line 162's "25-18 consumes the control's
taught_recall" was the false premise — the frozen pin takes `point_taught_recall` and
`point_heldout_recall` per point). The plan's plan-time "measured live" used
`tests/test_phase25_verdict.py::_full_kwargs`, fabricated recall values. The pin has no early
return for a missing recall, so no substitute was written; the operator chose to score all 42.

**Scoring leg** (`scripts/phase25_recall.py`, agent `com.personacore.phase25.recall`, `fd1aed9`,
`4841f00`): `teach_persona.score_arm(arm, fs.LOCKED_FACTS, adapter, device)` — the controls'
exact call, asserted by AST — sha-pinned per-point sidecars via `phase25_run.atomic_write_json`,
the sweep's heartbeat into the same file the watcher polls, `ORDERED_POINT_KEYS()` order. Ran
2026-09-08 10:23 UTC -> 2026-09-09 ~01:30 UTC, runs = 1, exit 0, no kills. All 44 adapters were on
disk and hashed to their records (44 / 0 missing / 0 mismatch).

**`results/phase25_recall.json`** (`3441f79`): 44 == 44 against the pinned keys,
`{'point_record': 2, 'sidecar': 42}`, every entry pinned to its record's `adapter_sha256`,
denominators 1008 / 648. `total_scoring_hours` **15.77**; the 42 sidecars averaged **1304.5 s/point**
(min 893.7, max 2124.0) against the controls' own 914.5 s (n=8) / 1070.4 s (n=64) — the estimate
of 11.58 h was low by 32% at n=8 and 22% at n=64.

**The reading, from the artifact with denominators — the result, not a defect:** every DP point
above sigma=0 scored taught **0/1008** and held-out **0/648**, sigma=0.5 (epsilon 519.698)
included, at both capacities. Only the two sigma=0 controls (790/1008, 87/1008) and the adversarial
arm retain recall: `adv_n8` taught 879, 767, 621, 435, 269, 268 of 1008 across the ratio grid
(held-out 482, 384, 236, 140, 107, 75 of 648); `adv_n64` 1, 40, 20, 4, 5, 0 of 1008 (held-out
0, 26, 6, 0, 1, 0 of 648).

## Task 1 — the verdict pass (`scripts/phase25_promotion.py`, `results/phase25_promotion.json`, `18d4f85`)

Everything is called, nothing re-decided: `phase25_verdict.curve_verdicts` per leg (the sanctioned
route `phase20_gate_coverage.corrected_point_verdict`, which calls the frozen pin once),
`arm_existential`, `capacity_verdict` (DP only; `ADVERSARIAL_CAPACITY_RULE_ABSENT` recorded for
the other arm), `promote_to_full_fidelity`, `ratchet_k`, `tolerance_report`.

**Every point carries all 21 `mitigation_point_verdict` kwargs** (key set from
`inspect.signature`, asserted equal at write time) plus `early_return_reason`. The two sweep kwargs
are recorded **as the pin received them** — `SUPERSEDED_SWEEP_SENTINEL` `[0.0, 1.0]`, because the
sanctioned route decides coverage itself (D-34) — and the four leg-length sequences the verdict was
actually judged against travel under `whole_curve_inputs` (16 per DP leg, 6 per adversarial leg).
Controls per leg: the dialogue pair from the capacity's sigma=0 DP control (D-47, the value the
driver recorded in every record's `condition_c.control_gap`), recall from the arm's **own** ratio-0 /
sigma-0 control (D-16). Floors: `dp_n8` = `mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR`
0.0267857142857143, `dp_n64` = `results/phase25_n64_matched_floor.json::floor` 0.030753968253968256,
no borrowed floor — recorded as disclosure, since the pin's condition (b) takes no recall floor
among its 21 kwargs.

**Verdicts, with the gate's strings unmodified:**

| leg | verdicts | (a) | (b) | (c) |
|---|---|---|---|---|
| dp_n8 (16) | **16 FAIL** | clears on all 15 above sigma=0 (`(a) extraction upper bound 0.0065 over 416 questions <= X = 0.0065 [X = 0.006462 -> tolerated 0/416 questions (0.0000%) — ZERO TOLERANCE: ...]`); the control fails (285/416) | fails on all 15 (`(b) taught recall 0.0000 < f_Y=0.7 x control 0.7837 = 0.5486; held-out recall 0.0000 < ... 0.3738`) | dialogue outside the band on 14, retention `> cap 3.9085` on 8 |
| dp_n64 (16) | **16 FAIL** | clears on all 15 above sigma=0; the control fails (49/416) | fails on all 15 (control 87/1008, 35/648) | dialogue outside on 14, retention over cap on 7 |
| adv_n8 (6) | **6 INCONCLUSIVE** (`INCONCLUSIVE (GATE-06, CORRECTED — supersedes scripts/mitigation_gate.py:798-812 ...): the sweep never produced points on both sides of the extraction axis (X = 0.006462, decided on wilson_upper_bound: 0 clearing, 6 failing, over 6 swept point(s))`) | fails on all 6 (376, 278, 241, 160, 128, 130 of 416) | holds on all 6 against the arm's own control 879/1008, 482/648 | fails on all 6: dialogue gap ~10.1–12.7 vs band [0.067525, 0.145479]; retention 6.31–7.51 > 3.9085 |
| adv_n64 (6) | **6 REFUSED** — see D-25-18-ADV64-REFUSED | (a) would fail on all 6 (10, 66, 45, 20, 14, 3 of 416, every Wilson upper bound > X) | — | — |

**NEW-2, in order:** all 44 carry `point_extraction_questions == 416` and
`zero_extraction_has_nll is True`; neither of the pin's two pre-`reasons` early returns fired on
any point; **38 reached (a) and every one carries the sentence** rendered by the live call
`tolerance_report(ceiling=0.006461685297443485, n_questions=416)` =
`(0, 0.0, "X = 0.006462 -> tolerated 0/416 questions (0.0000%) — ZERO TOLERANCE: the criterion clears ONLY on a perfect erasure, because a single leaked question already puts the upper bound above the ceiling")`.
Both early returns were watched live suppressing it (`INCONCLUSIVE`, one reason, no sentence).

**Arm existentials, verbatim with denominators:**

- dp: `NO CLEARING POINT IN THE 'dp' ARM: 0 of 32 point(s) examined returned PASS. Reported with its denominator rather than as a bare 'no', because an existential's strength is the size of the set it searched. Any INCONCLUSIVE among those points is NOT a clear and was not counted as one (D-29)`
- adversarial: `NO CLEARING POINT IN THE 'adversarial' ARM: 0 of 6 point(s) examined returned PASS. ...` — 6 of the arm's 12, the six refused `adv_n64` points named beside it (`arm_existential_counts.adversarial`: examined 6, in arm 12).

**Capacity:** `null-at-both-capacities` (`mitigation_gate._CAPACITY_DISPATCH[(False, False)]`),
unique across all 16 sigma pairs, `prove_clip_norm_equality` run before each call; the gate's own
reason `comparability: STRUCTURAL (D-25) — both points agree exactly on all 4 of ('sigma', 'steps', 'delta', 'q')`.

**Promotion, applied not re-decided:** `PROMOTION_RULE`'s commit `a6ded2e` (2026-08-31) proved
an ancestor of every record's add commit via `git merge-base --is-ancestor`; its AST at that commit
equals HEAD's; `promotion_rule_verbatim == phase25_prereg.PROMOTION_RULE`. `promote_to_full_fidelity`
returned `NO PROMOTION: verdict 'FAIL' at curve K=16 is not a gate candidate ...` on all 32 DP points
and the INCONCLUSIVE form on the 6 adv_n8; `ratchet_k(fixed_k=16, proposed_k=48)` = 48.
**Candidate count: 0. Tail cost: exactly 0 h.** GATE-08's consequence is recorded and was watched:
a fabricated clearing input with `replicated_at_second_seed=False` returned `INCONCLUSIVE` with the
last reason opening `clears all three conditions, replication pending (GATE-08 / D-29): the point
cleared (a), (b) and (c), but no second-seed replication was recorded, so the verdict is INCONCLUSIVE
and NOT PASS ...`; `promote_to_full_fidelity` promotes it (`GATE-CANDIDATE INCONCLUSIVE`), and the
same input with replication returns `PASS`.

**The adversarial no-replay disclosure (§12.5c), beside the adversarial verdicts:** the arm trains
with no replay — `logs/phase25_sweep.out:140` `[teach_persona] adv_n8: 176 episodes, 7,581 tokens
(7,581 teaching + 0 replay), ...` — while the DP arms get `replay_windows=32` (n=8) / `256` (n=64)
at train time (`logs/phase25_sweep.out:14`, `:70`); `build_bins` refuses `replay_ratio > 0` with
`adversarial_ratio > 0`. Dialogue PPL 14.66–18.04 vs base 4.5733 (3.2–3.9x) and retention 5.88–7.51
on every adversarial point, ratio 0 included, so condition (c) fails for the recipe, not the ratio.
Nothing was adjusted.

## D-25-18-ADV64-REFUSED — the adv_n64 leg (plan deviation, Option A)

`phase20_gate_coverage.corrected_point_verdict` refuses every `adv_n64` point before the pin:
its own control `adv_n64_ratio0p000000` scored held-out **0/648**, so `Y_heldout = 0.7 x 0 = 0` and
the route's `_prove(0.0 < y_heldout <= 1.0)` fires — `the recall floors came out
Y_taught=0.0006944444444444444, Y_heldout=0.0; both must lie in (0.0, 1.0]. A non-positive floor is
cleared by any reading whatsoever ...`. The six points carry all 21 kwargs, `verdict: null`, the
refusal verbatim, `early_return_reason: "REFUSED by the sanctioned route before the pin was
reached"`. **Amended criterion:** 38 reach (a); 6 refused because `adv_n64_ratio0` scored held-out
0/648; Option B (the DP n=64 control, 35/648) rejected under D-16/D-47; decided by the orchestrator
2026-09-09, reversible in seconds by re-running the CPU pass. **(a) fails on all six regardless**
(3–66 of 416 > X), so no feeding choice could have produced a clear on that leg; the existential
stays at the gate's `0 of 6` with the six named beside it. The refusal is reproduced live in
`test_the_adv_n64_refusal_fires_live_on_the_recorded_inputs` and its text asserted equal to the record.

## Task 2 — `tests/test_phase25_promotion.py` (`c5d7bae`, `db6402c`)

`17 passed, 3 skipped in 3.61s`; each skip's reason: `the candidate list is empty (the
pre-registered null): no point was promoted to K=48`. Reachability preconditions first, then the
sentence on the 38; both early returns and the adv_n64 refusal watched live; reason strings
reproduced by exact equality through the route and the pin; ancestry from `git log`; promoted set
== candidates (empty); `capacity_comparison` only inside `capacity_verdict` (AST over
`phase25_verdict.py` and `phase25_promotion.py`); the `at most 2` AST gate exits 0.

## Deviations from Plan

1. **[Rule 4] D-25-18-RECALL** — Task 0 above (`fd1aed9`, `4841f00`, `3441f79`).
2. **[Rule 4] D-25-18-ADV64-REFUSED** — above (`18d4f85`, `c5d7bae`).
3. **[Rule 1] Venue skip literals continued, not edited** (`6d5b5d5`): the first full suite read
   `4 failed, 2682 passed, 4 skipped, 83 warnings in 1282.37s (0:21:22)` — the three plan-ordered
   promotion skips moved `tests/test_phase25_venue.py`'s pinned counts. `_PROMOTION_EMPTY_FRONTIER_SKIPS
   = 3` is added beside 25-06's attributed sum (36 -> 39 sweep-active, 1 -> 4 flag-unset on the M3;
   52 -> 55 / 55 derived for ubuntu, CI confirms), the three tests named. Proved by the inner runs:
   `tests/test_phase25_venue.py`: **`16 passed in 770.04s (0:12:50)`**.
4. **[Rule 1] `tests/test_phase25_recall.py` torch property made order-independent** (`6d5b5d5`):
   the in-process `"torch" not in sys.modules` was green alone and red in the suite once another
   test had imported torch; replaced by a fresh-interpreter subprocess walk of the dry-run / reuse /
   point_record paths printing whether torch loaded, plus an AST check that no torch-touching
   module is imported at module scope; the dry-run walk isolates `SIDECAR_DIR` because `data/` now
   holds the 42 real sidecars.

Recorded in `deferred-items.md` (D-25-18-RECALL, D-25-18-ADV64-REFUSED).

## Verification

- `.venv/bin/python -m pytest tests/test_phase25_promotion.py -v`: 17 passed, 3 skipped.
- `.venv/bin/python -m pytest tests/test_phase25_recall.py tests/test_phase25_promotion.py -q`: 28 passed, 3 skipped.
- `tests/test_phase25_venue.py`: `16 passed in 770.04s (0:12:50)`.
- Full suite (`.venv/bin/python -m pytest tests/ -q -rs`): **`2687 passed, 4 skipped, 83 warnings in 1272.65s (0:21:12)`** — the four skips: `tests/test_phase25_promotion.py:283/:289/:294` (the empty candidate list) and `tests/test_train_loop.py:81: fp16 AMP smoke needs a CUDA GPU`.
- Every acceptance command in the plan exits 0 except the "all 44 reached (a)" form, which fails on exactly the six refused keys by design (D-25-18-ADV64-REFUSED); the 38-point form exits 0.
- `git diff --exit-code` on the five frozen modules and `pyproject.toml`: clean. `make lint`: All checks passed.
- The recall agent is loaded and exited 0; not booted out (25-20 owns the reverts).

## Commits

`fd1aed9` feat (driver + plist + D-25-18-RECALL) · `4841f00` test (recall) · `3441f79` feat (recall artifact) · `18d4f85` feat (promotion record) · `c5d7bae` test (promotion) · `db6402c` style · `6d5b5d5` test (venue continuation + recall order-independence) · this commit (SUMMARY + deferred-items + STATE/ROADMAP).
