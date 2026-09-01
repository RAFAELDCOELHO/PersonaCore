"""PHASE 23'S **RESOURCE** BUDGET — measured numbers, pinned as literals. NOTHING ELSE LIVES HERE.

WHAT THIS FILE IS
-----------------
The RESOURCE parameters v4.0's sweep is priced against. Today that is ONE number: D-03's measured
seed-to-seed noise floor of the control arm. The Z values (the per-point compute budget) arrive in
23-13, after CAL-01 and CAL-05 measure the per-point cost in 23-11 — they are NOT reserved here as
placeholders, because a placeholder is a literal with no evidence and this file's whole discipline
is that a literal carries its evidence.

CONTINUED 2026-08-27 (plan 23-18): that is now TWO numbers. ``MATCHED_CONTROL_NOISE_FLOOR`` below
pins the SAME quantity over the PROTOCOL-MATCHED comparator (23-17's protocol, 23-20's run). The
sentence above is left verbatim because it was true when it was written; this line is what stops it
going stale.

WHAT THIS FILE IS **NOT**
-------------------------
It is not an OUTCOME threshold. Outcome thresholds live in ``scripts/mitigation_gate.py``, which is
FROZEN. ``.planning/ROADMAP.md:139-144`` requires that separation to be STRUCTURALLY enforced
rather than merely documented: a resource budget measured beforehand is not an outcome threshold
measured beforehand, and a reader must not be able to mistake one for the other.

The enforcement is the IMPORT GRAPH, and it is checked twice:

  * STATICALLY, at ``tests/test_phase20_prereg.py::
    test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only``, which names
    ``mitigation_budget`` by string and scans the whole ``scripts/mitigation_*.py`` glob — so this
    module joined that scan the moment it was created, with nobody having to remember to add it.
  * TRANSITIVELY, at ``tests/test_phase23_budget.py::
    test_gate_does_not_transitively_load_the_budget``, which execs the real frozen gate in a fresh
    interpreter and asserts ``mitigation_budget`` never reaches ``sys.modules``. That closes the
    ``gate -> erasure_gate -> budget`` route, which sits outside the ``mitigation_*.py`` glob the
    static scan walks and is therefore invisible to any AST walk over it.

**THIS FILE HAS ZERO IMPORTS, AND THAT IS A HARD CEILING RATHER THAN A STYLE CHOICE.**
The allow-set the static guard asserts is ``{pathlib, sys, erasure_gate}``, and the union across
every ``scripts/mitigation_*.py`` in the tree is ALREADY EXACTLY that set — the accountant and the
unit module import nothing at all, and the gate contributes all three. So the ceiling has **ZERO
HEADROOM**, measured (``tests/test_phase23_budget.py``'s ceiling block records the two scratch
modules that were watched RED to establish it). One ``json`` imported here turns a committed guard
RED, and so does ``math``, and so does ``dataclasses``.

It may not reach ``mitigation_gate`` either, and that is the import a reader would most naturally
want — the budget's constants have to agree with the gate's menus. Naming it would add
``mitigation_gate`` to ``imported`` and break the subset assertion exactly as ``json`` does. The
sanctioned form is therefore to RESTATE a referenced frozen constant as a literal beside a
provenance comment, and to ship a TEST asserting the literal and the frozen original agree. (No
such restatement exists yet: the floor below is derived from a Phase-23 artifact, not from the
gate. 23-13's Z values are the first that will need one.)

``scripts/phase19_floor.py`` is the shape that satisfies the ceiling for free, and this file copies
it deliberately: **LITERAL ASSIGNMENTS AND NOTHING ELSE** — no rule, no estimator, no report text,
no function, no ``__main__`` block, no import. A file with no expressions in it cannot need one.
``tests/test_phase23_budget.py::test_budget_holds_only_literal_constants`` is the guard, and it
carries a non-empty meta-guard so a walk that silently stopped working cannot pass by finding
nothing.

**THIS MODULE IS DELIBERATELY NOT REGISTERED AS A ``prereg_artifact=``.**
``tests/test_phase20_prereg.py:94-108`` establishes the distinction by measurement rather than by
assumption: being named ``mitigation_*.py`` makes a module PROTECTED (it joins ``_GATE_MODULES``,
so the import ceiling and the rule/emission split police it) and confers NO freeze. Only a
hand-written explicit path reaching ``_assert_ordering_holds`` as a ``prereg_artifact=`` confers
one, and that act is irrevocable from the first matching artifact. Protected-but-not-frozen is
exactly the middle ground D-03 needs here, because a freeze would forbid 23-13 from ever writing
the Z values this file exists to eventually hold.
``test_the_budget_module_is_protected_but_not_frozen`` makes that a checked property rather than a
paragraph, so a future phase cannot freeze this file by accident.

**EVERY CONSTANT BELOW RE-DERIVES ON EVERY SUITE RUN**, from its committed artifact, through the
BLINDLY-COMMITTED reduction, under exact ``==``
(``test_budget_constants_re_derive``). A hand-edited number goes red — including a ONE-ULP nudge,
which ``test_a_hand_edited_floor_is_detected`` observes being refused rather than asserting is
refused. That is the property that lets a measured number live outside the closed pre-registration
at all; ``scripts/phase19_floor.py``'s property 2, applied unchanged.

CONTINUED 2026-08-28 (plan 23-13): the Z values the first paragraph says "arrive in 23-13" HAVE
arrived — ``SWEEP_POINTS``, ``CURVE_K``, ``FULL_FIDELITY_K``, ``STEP_BUDGET``, ``N_CONTROL_SEEDS``
and ``N64_LEG_WITHDRAWN``, at the bottom of this file. That also settles the parenthesis above:
``CURVE_K`` and ``FULL_FIDELITY_K`` ARE the first restatements of a frozen ``mitigation_gate``
constant in this file, and ``tests/test_phase23_budget.py::test_selected_k_is_a_ratcheted_rung`` is
the test that holds them to it, by importing the gate FROM THE TEST. Both earlier paragraphs are
left verbatim because each was true when it was written; this line is what stops them going stale.

CPU-only, GPU-free, no torch, no network. Nothing here executes.
"""

# =================================================================================================
# ===== D-03: THE CONTROL ARM'S SEED-TO-SEED NOISE FLOOR =====
# =================================================================================================

# THE MEASURED FLOOR. The RANGE `max(readings) - min(readings)` over the FIVE per-seed primary
# readings of the unmitigated control arm.
#
#   input    : the taught recall rate with the adapter ON, one reading per seed, each a COUNT over
#              its own denominator of 1008 draws (112 questions x 9 draws per question):
#                  seed 1337  566/1008 = 0.5615079365079365   <- the pinned central reading
#                  seed 2024  530/1008 = 0.5257936507936508
#                  seed 1338  575/1008 = 0.5704365079365079   <- max
#                  seed 2025  531/1008 = 0.5267857142857143
#                  seed 1339  521/1008 = 0.5168650793650794   <- min
#              5040 scored draws in total, on `mps`, torch 2.7.1
#   rule     : `phase23_prereg.noise_floor`, committed BLIND in 23-03 while
#              `git ls-files 'results/phase23_*'` was still EMPTY — and CALLED by 23-08's writer
#              rather than re-implemented there, which is why the record's `reduction` field names
#              the symbol instead of restating the formula
#   output   : 0.5704365079365079 - 0.5168650793650794
#   evidence : `results/phase23_control_floor.json` (the committed record: every per-seed reading
#              with its k, its n and its exported adapter's sha256)
#
# WHAT IT GOVERNS, AND WHAT IT DOES NOT. It governs the taught recall rate with the adapter ON and
# NOTHING ELSE — the record's own `governs` field, restated verbatim in the provenance dict below
# and asserted equal to it. Every other reading in that record (held-out recall, perplexity,
# per-family gains) is secondary, carries its own denominator, and was NOT reduced. A floor
# borrowed across quantities is the defect D-06 corrected for v4.0 when a Phase-12 full-fine-tune
# seed pair was found governing an adapter-regime verdict.
#
# THE ORDERING IS A FACT ABOUT GIT, NOT AN INTENTION. This pin lands while
# `git ls-files results/phase23_sigma_zero.json` returns NOTHING, so the floor demonstrably could
# not have been tuned to a σ=0 number that does not exist yet. D-03 requires that ordering; 23-10
# is what creates the σ=0 record this floor will be read against.
CONTROL_NOISE_FLOOR = 0.05357142857142849

# The floor's provenance, as a SIBLING CONSTANT rather than a comment — so a consumer can read it
# and a test can assert on it. Its eight required keys are `phase23_prereg.FLOOR_PROVENANCE_KEYS`
# exactly, because 23-10 passes this dict straight into `phase23_prereg.sigma_zero_verdict`, which
# REFUSES a floor whose artifact, commit, device, seeds, reduction or scope is unstated. An
# unlabelled number is indistinguishable from a borrowed one.
#
# TWO DIGESTS, AND THEY ARE DIFFERENT THINGS — which is worth stating because the names are close
# enough to be read as duplicates:
#
#   `record_sha256`      the record's OWN field, and it is an INPUTS digest:
#                        `sha256(json.dumps(per_seed, sort_keys=True, default=str))`
#                        (`scripts/phase23_run.py:967-969`). It pins the five scored readings the
#                        reduction ran over. It is NOT, and cannot be, the file's own hash — a file
#                        cannot contain its own digest.
#   `record_file_sha256` the sha256 of the committed record's BYTES. This is the one that pins the
#                        artifact as a whole, and it is checked live against `read_bytes()`.
#
# `reduction` names the SYMBOL and never the formula, for the reason `phase23_prereg` exists at
# all: a reduction restated where the numbers are visible is a reduction chosen with the numbers
# visible, whatever the intent.
CONTROL_NOISE_FLOOR_PROVENANCE = {
    "record": "results/phase23_control_floor.json",
    "record_sha256": "c62d732283a3f15375de7b2ba9180c56acfcd75109b12912c17c9f083afdf0eb",
    "record_file_sha256": "201cc58e574074df875513c32ee0237e143ecb356469a79581be511748a75a59",
    "git_sha": "0fb596dcbb147952ce6ae11144c9cfe7cf57330c",
    "device": "mps",
    "torch_version": "2.7.1",
    "seeds": (1337, 2024, 1338, 2025, 1339),
    "reduction": "phase23_prereg.noise_floor",
    "governs": (
        "the TAUGHT RECALL RATE WITH THE ADAPTER ON (per_seed[].primary.k / .n, a count over "
        "QUESTIONS). `phase23_prereg.sigma_zero_verdict` reads this floor in 23-10 against the "
        "same quantity measured on the σ=0 arm and recorded at "
        "results/phase23_sigma_zero.json; a deviation larger than this floor HALTS the whole "
        "sweep (D-04) and there is no warning branch and no override flag. It governs THAT "
        "quantity and nothing else: every other reading in this record is secondary, recorded "
        "with its own denominator and NOT reduced."
    ),
}

# RE-SCOPED IN PLACE 2026-08-27 (plan 23-18).
#
# THE CONSTANT ABOVE IS NOT FALSIFIED, AND IT IS NOT SUPERSEDED AS A MEASUREMENT. It correctly
# measures the OLD control protocol, and it still re-derives from
# `results/phase23_control_floor.json` on every suite run (`test_budget_constants_re_derive`). What
# changed is its SCOPE, not its truth.
#
# WHAT RE-SCOPED IT. `.planning/debug/sigma-zero-beats-control.md` split the D-04 HALT between
# (A) INVALID COMPARATOR and (B) REAL DP-PATH DEFECT, attributed it to (A), and FALSIFIED (B): over
# identical materialised batches at σ=0 with a non-binding `C = 1e6`, all 72 LoRA tensors agree with
# an ordinary grad-accum reference to 2.178e-07 relative. The DP seam does no arithmetic plain
# accumulation does not, so the defect is in what the σ=0 arm was compared AGAINST.
#
# THE THREE MECHANISMS THAT MADE THE OLD CONTROL A DIFFERENT PROTOCOL, with their measured
# magnitudes (`phase23_matched_prereg.MATCHED_EQUALISED`, restated in the matched record's
# `equalised_mechanisms` field):
#
#   lot volume            the DP lot is 33 teaching + 32 replay = 65 windows; the control lot is 8.
#                         Measured TEACHING-token exposure over the run: 1,689,600 vs 196,867,
#                         = 8.58x.
#   teaching loss weight  the DP arm's fact-aligned packer returns EVERY window of one fact, so
#                         teaching enters the gradient at weight 1.0. The control draws 8 RANDOM
#                         windows from a bin that is 51.94% replay, so masked-CE puts weight
#                         p = 2719/6262 = 0.4342 on teaching. 1/0.4342 = 2.30x.
#   grad_clip             `grad_clip = 1.0` was applied to the control and is STRUCTURALLY ABSENT
#                         from the DP arm: `src/personacore/training/loop.py:220-228` gates the
#                         legacy clip on `dp_fn is None`, so that clip and `finalize()` are the two
#                         arms of ONE if/else. Measured binding on 19 of the control's first 25
#                         steps, mean shrink 0.8071.
#
# SO: the constant above governs the OLD protocol, and `MATCHED_CONTROL_NOISE_FLOOR` below governs
# the CORRECTED comparator. 23-19 consumes the MATCHED one. Nothing consumes the original for the
# σ=0 adjudication any more — and it is not deleted for that.
#
# IT IS LEFT STANDING because deleting a true measurement to make a later one look tidy is the
# opposite of the discipline this file exists to hold. A reader who opens this file sees BOTH floors
# and what separates them, which is strictly more than a reader who sees only the survivor.
#
# HANDED FORWARD TO THE NEXT EDITOR OF THIS FILE. The original's LITERAL ASSIGNMENT STRING — its
# name, a space, an equals sign, a space, its value — must occur EXACTLY ONCE in this file.
# `test_a_hand_edited_floor_is_detected` builds that string as a needle, asserts
# `source.count(needle) == 1`, and then rewrites it under `tmp_path`. A SECOND occurrence turns that
# committed green guard RED, and there are two ways to make one: quoting the assignment in prose,
# and a longer identifier ENDING in the same name whose value shares the same `repr`. Refer to the
# constant BY NAME; never re-type its assignment. `test_the_original_needle_is_still_unique` is the
# named guard for this property.


# =================================================================================================
# ===== THE PROTOCOL-MATCHED CONTROL ARM'S SEED-TO-SEED NOISE FLOOR (23-17 protocol, 23-20 run) ====
# =================================================================================================

# THE MEASURED FLOOR OF THE CORRECTED COMPARATOR. The RANGE `max(readings) - min(readings)` over the
# FIVE per-seed primary readings of the PROTOCOL-MATCHED control arm — the arm that equalises the
# three mechanisms named in the continuation above.
#
#   input    : the taught recall rate with the adapter ON, one reading per seed, each a COUNT over
#              its own denominator of 1008 draws (112 questions x 9 draws per question), in the
#              RECORDED SEED ORDER, which is the LADDER order and is NOT sorted order:
#                  seed 1337  790/1008 = 0.7837301587301587   <- max, and the pinned central reading
#                  seed 2024  774/1008 = 0.7678571428571429
#                  seed 1338  778/1008 = 0.7718253968253969
#                  seed 2025  763/1008 = 0.7569444444444444   <- min
#                  seed 1339  773/1008 = 0.7668650793650794
#              5040 scored draws in total, on `mps`, torch 2.7.1, python 3.11.15
#   rule     : `phase23_prereg.noise_floor`, committed BLIND in 23-03 at `c7de5d4` while
#              `git ls-files 'results/phase23_*'` was still EMPTY — and CALLED by 23-17's writer
#              (`phase23_run.matched`, run to completion by 23-20's continuation) rather than
#              re-implemented there, which is why the record's `reduction` field names the symbol
#              instead of restating the formula
#   output   : 0.7837301587301587 - 0.7569444444444444, which as counts is 790/1008 - 763/1008
#   evidence : `results/phase23_matched_control.json` (the committed record: every per-seed reading
#              with its k, its n and its exported adapter's sha256)
#
# WHAT IT GOVERNS, AND WHAT IT DOES NOT. Exactly what the original governs, over a DIFFERENT arm:
# the TAUGHT RECALL RATE WITH THE ADAPTER ON and NOTHING ELSE — the record's own `governs` field,
# restated verbatim in the provenance dict below and asserted equal to it. Every other reading in
# that record (held-out recall, per-family gains, final train loss, wall clock) is secondary,
# carries its own denominator, and was NOT reduced. A floor borrowed across quantities is the defect
# D-06 corrected for v4.0.
#
# WHAT ORDERING THIS PIN DOES AND DOES NOT BUY — AND IT BUYS LESS THAN THE ORIGINAL'S DID.
# The original landed while `git ls-files results/phase23_sigma_zero.json` returned NOTHING. THIS
# ONE DOES NOT. `results/phase23_sigma_zero.json` is already committed and its reading
# 0.7837301587301587 was on screen throughout the design of the protocol this floor reduces over.
# That is the disclosure, stated here rather than left to be inferred from a date.
#
#   STILL BLIND, all pinned at `c7de5d4` and byte-unchanged since: the reduction
#   (`phase23_prereg.noise_floor`), the central-reading rule (`control_readings[0]`), the verdict
#   function (`phase23_prereg.sigma_zero_verdict`) and the seed ladder.
#   ALSO PINNED BEFORE ANY READING EXISTED: the comparator's PROTOCOL, in
#   `scripts/phase23_matched_prereg.py`, committed while `git ls-files 'results/phase23_matched_*'`
#   returned NOTHING — a fact about git's object graph rather than a claim in a paragraph.
#   NOT BLIND: WHICH MECHANISMS TO EQUALISE. That choice was made with the σ=0 number visible, and
#   it is the last remaining degree of freedom in this comparison.
#
# THE BOUND ON THAT IS `phase23_matched_prereg.SIGMA_ZERO_VISIBILITY_DISCLOSURE` AND ITS ONE-ATTEMPT
# RULE — AND THAT RULE HAS FOUR CLAUSES, NOT THREE. Stated at its true strength because this file is
# pre-registration-adjacent and a three-clause version of it would be the third printing of the same
# overclaim:
#
#   (1) it binds ACROSS COMMITS only. Inside the uncommitted window it does not bind at all:
#       `.gitignore` ignores `data/` and `checkpoints/`.
#   (2) inside that window, 23-17's `prior_scored_seeds_at_start` refuses only a delete that leaves
#       the `matched` section of `data/phase23_run_state.json` INTACT.
#   (3) a delete that ALSO removes that section reads as a FIRST ATTEMPT at run time and is
#       PREVENTED BY NOTHING.
#   (4) that same case is AUDITABLE AFTER THE FACT rather than invisible, and only that. The state
#       ledger is TRACKED as of `cfa2c87` with a baseline carrying NO `matched` section, and the
#       run's own session committed it together with the record at `04cdb21`, so a later deletion
#       of that section is a VISIBLE DIFF. But only FROM that commit onward: tracking is NOT
#       retroactive, and before it a `git checkout --` left no history at all. The same-session
#       commit is what converts this residual from invisible to auditable. It is a DISCIPLINE, NOT
#       A MECHANISM, and it is not "closed".
MATCHED_CONTROL_NOISE_FLOOR = 0.0267857142857143

# The matched floor's provenance, in the SAME shape as the original's: the eight
# `phase23_prereg.FLOOR_PROVENANCE_KEYS`, plus `record_file_sha256` for the same reason the original
# carries it (the record's own `record_sha256` is an INPUTS digest over `per_seed`, and a file
# cannot contain its own hash), plus TWO matched-specific keys. 23-19 passes this dict straight into
# `phase23_prereg.sigma_zero_verdict`, which REFUSES a floor whose artifact, commit, device, seeds,
# reduction or scope is unstated.
MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE = {
    "record": "results/phase23_matched_control.json",
    "record_sha256": "5bb4216f7ea15611847b5a46613f990cadc028f0a8680337385c7d1fbcf7dd85",
    "record_file_sha256": "4478005fa5480646d830ac56d615ab361b1e1a7b8becfd6d887bec33deba504c",
    "git_sha": "d8f42639f1d71ae36c277cd48baa422e24ae5104",
    "device": "mps",
    "torch_version": "2.7.1",
    "seeds": (1337, 2024, 1338, 2025, 1339),
    "reduction": "phase23_prereg.noise_floor",
    "governs": (
        "the TAUGHT RECALL RATE WITH THE ADAPTER ON (per_seed[].primary.k / .n, a count over "
        "QUESTIONS) and NOTHING ELSE. This floor describes the PROTOCOL-MATCHED comparator: the "
        "same quantity results/phase23_control_floor.json's floor describes, reduced over an arm "
        "that equalises the three mechanisms that record's `residual_differences` did not. Every "
        "other reading here is secondary, carries its own denominator and was NOT reduced. This "
        "record renders NO verdict: `phase23_prereg.sigma_zero_verdict` is 23-19's to call, "
        "against the floor 23-18 re-pins from this number"
    ),
    # Neither key is a `FLOOR_PROVENANCE_KEY`. Both are carried because a matched floor read
    # without them is indistinguishable from the original: `protocol` names the pin the arm was
    # run under, and `sigma_zero_was_visible` is the disclosure that separates this pin's ordering
    # claim from the original's.
    "protocol": "phase23_matched_prereg",
    "sigma_zero_was_visible": True,
}


# =================================================================================================
# ===== CAL-02: Z — THE SWEEP'S RESOURCE BUDGET, SET FROM 23-11'S MEASUREMENTS (plan 23-13) =======
# =================================================================================================

# ONE DIGEST NOTE, STATED ONCE HERE RATHER THAN SIX TIMES BELOW, BECAUSE THE KEY NAME IS REUSED
# WITH A DIFFERENT MEANING. The two floors above carry `record_sha256` = the record's OWN
# `record_sha256` field, an INPUTS digest over `per_seed`, and a SEPARATE `record_file_sha256` for
# the committed bytes. NONE of the three records the Z constants cite carries an inputs digest of
# its own, so on every Z provenance dict below `record_sha256` IS THE SHA256 OF THE COMMITTED
# FILE'S BYTES. `test_budget_constants_re_derive` checks each one live against `read_bytes()`, so
# the meaning is asserted rather than promised.
#
# THE CEILING, NOT THE FLOOR, AND THE REASON IS THE RATCHET. `mitigation_gate.ratchet_k` at
# `scripts/mitigation_gate.py:917` calls `_prove(proposed_k >= fixed_k)`: once a rung is pinned, K
# may only INCREASE. There is no cheap direction and no override flag, so a sweep sized against
# `generation.h_per_point_floor` and then found too expensive has NO rescue. Every hours figure
# quoted below is therefore sized against `generation.h_per_point_ceiling`, and the three constants
# that are MULTIPLICANDS of that total — `SWEEP_POINTS`, `CURVE_K`, `N_CONTROL_SEEDS` — carry
# `sized_against` to say so. The other three deliberately DO NOT carry it, and the field is ABSENT
# rather than empty: no throughput figure participates in `STEP_BUDGET`, `FULL_FIDELITY_K` or
# `N64_LEG_WITHDRAWN`, and a provenance field that lies is worse than one that is missing.
# `test_z_was_sized_against_the_ceiling` asserts both halves, so neither an omission nor an
# invention passes.
#
# WHO CHOSE WHAT, AND AGAINST WHAT. `CURVE_K` and `SWEEP_POINTS` were selected BY THE USER at plan
# 23-13 Task 1's blocking `checkpoint:decision` gate, from a per-rung table computed live through
# `phase23_cost.size_sweep` at BOTH the ceiling and the floor with the never-taught term priced as
# its own column. The executor selected nothing and named no default: the ratchet is one-way, the
# rungs span 5.36x in draws per point (42,480 at K=48 against 7,920 at K=8), and NO SPEND BOUND
# EXISTS in any source artifact — not in `23-CONTEXT.md`'s D-01..D-10, not in its Claude's
# Discretion section (which delegates Z as a DERIVATION rule and supplies no criterion to select
# against), not in `.planning/REQUIREMENTS.md` and not in `.planning/ROADMAP.md`. None was invented.
# The remaining three constants are RULES rather than options, were never presented as choices, and
# each names the live source symbol it was read from.
#
# THE RUNG MENU IS FROZEN AND CANNOT BE IMPORTED HERE. `mitigation_gate.py:254` declares
# `K_RUNGS = (48, 24, 16, 8)`, and both K constants below are members of it. This module may not
# import that module: `tests/test_phase23_budget.py:308`'s literal-only guard refuses any
# module-level node that is not an `ast.Assign` (an `import` is not one, and that is the guard that
# actually binds this file), and TWO accumulated import ceilings bind the same
# `scripts/mitigation_*.py` union — `tests/test_phase20_prereg.py:1190` asserts
# `imported <= {pathlib, sys, erasure_gate}` (SUBSET) and `tests/test_phase23_budget.py:565`
# asserts `imported == {erasure_gate, pathlib, sys}` (EQUALITY, zero headroom in BOTH directions).
# So the rungs are RESTATED as literals here and the agreement is asserted by a test that imports
# the frozen gate itself.

# THE SWEEP WIDTH: frontier points per leg.
#
#   input    : `results/phase23_cost.json` -> `sweep_points_priced` = 16, whose sibling field
#              `sweep_points_source` names `.planning/ROADMAP.md:47 /
#              .planning/REQUIREMENTS.md:179` — the width this project published BEFORE any cost
#              measurement existed, and the width every row of the table the user chose from was
#              computed at
#   rule     : `phase23_cost.size_sweep`, called with `sweep_points=16`
#   output   : 16 points x 3.1471532286150796 h/point at the selected rung = 50.354451657841274 h
#              of sweep, before the never-taught term below
#   evidence : `results/phase23_cost.json`, `sizing["16"]`
#
# NO RECOMPUTATION WAS OWED BEFORE THIS PIN. Task 1's table was computed at 16 and the user's answer
# is 16, so the totals the rung was chosen against ARE the totals recorded here. Had the answer been
# some other width the table would have had to be recomputed and re-presented first, because the
# sweep term scales linearly in width while the never-taught term does not.
SWEEP_POINTS = 16

SWEEP_POINTS_PROVENANCE = {
    "record": "results/phase23_cost.json",
    "record_sha256": "f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637",
    "git_sha": "8876b8ce30427e08281f44b96a6a525dfd539a84",
    "derivation": "phase23_cost.size_sweep",
    "sized_against": "h_per_point_ceiling",
    "selected_by": (
        "THE USER, at plan 23-13 Task 1's blocking `checkpoint:decision` gate — not the executor, "
        "and not a default. The width was already published at .planning/ROADMAP.md:47 and "
        ".planning/REQUIREMENTS.md:179, which is the record's own `sweep_points_source`"
    ),
    "selected_value": 16,
    "selected_reply_verbatim": (
        "Confirma opção 1: W=16, o número já pré-registrado em ROADMAP.md:47 e "
        "REQUIREMENTS.md:179. Nenhuma razão nomeada para desviar dele nesta checkpoint — desvio de "
        "número já publicado exige justificativa científica explícita, não ajuste de conveniência "
        "no momento de gastar o compute. Nota registrada para decisão futura, se aplicável: número "
        "de pernas é alavanca de custo muito maior que largura (100,7h de diferença entre 4 e 2 "
        "pernas no mesmo degrau) — qualquer revisão de orçamento total deveria mirar aí primeiro, "
        "não em W."
    ),
    "governs": (
        "the number of FRONTIER POINTS PER LEG the v4.0 sweep draws, and nothing else. It is a "
        "RESOURCE parameter: it sizes the spend and decides no outcome. The user's recorded note "
        "about LEG COUNT being a larger cost lever than width is a note for a FUTURE budget "
        "decision and is NOT an instruction this pin acts on — the leg count is not pinned here"
    ),
}

# THE PER-POINT DRAW BUDGET FOR CURVE POINTS.
#
#   input    : the per-rung table over `mitigation_gate.K_RUNGS`, every cell computed live through
#              `phase23_cost.size_sweep` from `results/phase23_cost.json`'s `generation` block at
#              both the ceiling and the floor. At this rung: 14,832 draws/point,
#              3.1471532286150796 h/point at the ceiling against 1.9979696709667354 at the floor
#   rule     : `phase23_cost.size_sweep`, over the closed menu `mitigation_gate.K_RUNGS`
#   output   : the ceiling-side total for the whole leg, sweep plus never-taught floor scoring,
#              66.09021780091668 h — the record's `sizing["16"]`
#              `total_hours_ceiling_with_never_taught_floor`
#   evidence : `results/phase23_cost.json`, `sizing["16"]`
#
# THE SELECTION IS THE USER'S AND IT IS ONE-WAY. `ratchet_k` accepts only an INCREASE from here, so
# this rung is the floor of every future K in v4.0. The user's recorded reasoning, restated because
# it is the reason a mid-menu rung was taken rather than the cheapest: the ratchet guards against
# LOWERING K after seeing a bad result, but it does NOT guard against never noticing the result was
# bad, if the ASR ladder truncates exactly where real signal would have revealed itself. This rung
# preserves the ladder step that anchors to Phase 18's third rung, keeps `promote_to_full_fidelity`
# meaningful (a real 3x promotion to `FULL_FIDELITY_K`), and avoids the "truncated curve read as a
# null" risk that the cheapest rung specifically carries.
CURVE_K = 16

CURVE_K_PROVENANCE = {
    "record": "results/phase23_cost.json",
    "record_sha256": "f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637",
    "git_sha": "8876b8ce30427e08281f44b96a6a525dfd539a84",
    "derivation": "phase23_cost.size_sweep",
    "sized_against": "h_per_point_ceiling",
    "rung_menu": "mitigation_gate.K_RUNGS",
    "selected_by": (
        "THE USER, at plan 23-13 Task 1's blocking `checkpoint:decision` gate. NOT the executor: "
        "`mitigation_gate.ratchet_k` calls `_prove(proposed_k >= fixed_k)` so the choice is "
        "one-way, the rungs span 5.36x in draws per point, and NO spend bound exists in "
        "23-CONTEXT.md's D-01..D-10, in its Claude's Discretion section, in "
        ".planning/REQUIREMENTS.md or in .planning/ROADMAP.md. The plan presented the table, named "
        "no default and made no recommendation"
    ),
    "selected_value": 16,
    "selected_reply_verbatim": (
        "Confirma opção 1: CURVE_K = 16. Correção registrada da minha posição anterior — o ratchet "
        "protege contra reduzir K depois de ver resultado ruim, mas não protege contra nunca "
        "perceber que o resultado ERA ruim se a escada truncar exatamente onde sinal real se "
        "revelaria. K=16 preserva o degrau que ancora com Phase 18 step 3, mantém "
        "promote_to_full_fidelity significativo (16→48), e evita o risco nomeado de 'curva "
        "truncada lida como nulo' que K=8 especificamente carrega."
    ),
    "governs": (
        "the DRAW BUDGET PER CURVE POINT, and nothing else. It is the `fixed_k` "
        "`mitigation_gate.ratchet_k` ratchets from and the `curve_k` "
        "`mitigation_gate.promote_to_full_fidelity` promotes from; it decides no outcome and sets "
        "no threshold. It does NOT govern gate-candidate points, which are re-drawn at "
        "FULL_FIDELITY_K"
    ),
}

# THE DRAW BUDGET RESERVED FOR GATE-CANDIDATE POINTS.
#
#   input    : `scripts/phase18_extraction.py:93` — `K = 48`, the fidelity Phase 18 published at
#   rule     : the ATK-03 / P18-4 pin, restated at `mitigation_gate.ratchet_k`'s docstring:
#              reducing a full-fidelity K AFTER seeing a null is the weakening those two exist to
#              prevent, because fewer draws is less power to observe extraction, i.e. an EASIER
#              NULL — a reduction taken after a null buys the very result it reacts to
#   output   : 48
#   evidence : `scripts/phase18_extraction.py`, whose `ASR_RUNGS` reads the top rung off this same
#              constant rather than retyping it
#
# THIS ONE WAS NEVER THE USER'S TO CHOOSE AND WAS NEVER PRESENTED AS AN OPTION. It is a RULE. It
# carries no `sized_against`, because no throughput figure participates in it at all.
FULL_FIDELITY_K = 48

FULL_FIDELITY_K_PROVENANCE = {
    "record": "scripts/phase18_extraction.py",
    "record_sha256": None,
    "git_sha": None,
    "derivation": "phase18_extraction.K",
    "selected_by": (
        "NOBODY — it is a RULE, not a selection. Phase 18's published fidelity, held in place by "
        "the ATK-03 / P18-4 pin. Presented to the user at Task 1's checkpoint as a fact of the "
        "pre-registration rather than as an option"
    ),
    "governs": (
        "the draw budget a GATE-CANDIDATE point is RE-DRAWN at — the `full_k` argument of "
        "`mitigation_gate.promote_to_full_fidelity`, and nothing else. Curve points are drawn at "
        "CURVE_K. `record_sha256` and `git_sha` are None BY CONSTRUCTION: the source is a live "
        "SOURCE MODULE that this phase does not freeze, not a committed results artifact, so a "
        "digest pinned here would go stale on any unrelated edit while asserting nothing. "
        "`test_selected_k_is_a_ratcheted_rung` resolves the symbol live instead, which is the "
        "check a digest would only approximate"
    ),
}

# THE PER-ARM OPTIMIZER-STEP BUDGET.
#
#   input    : `scripts/teach_persona.py:1220` — `MAX_STEPS = 200`, the production teaching budget
#              every Phase-23 arm already ran at (`results/phase23_cost.json` records
#              `max_steps: 200` on both DP legs and both non-DP legs)
#   rule     : restate-and-assert. The value is a literal here because this module has no import
#              budget; `test_the_step_budget_agrees_with_the_production_constant` is the other half,
#              and without it the restatement would be an unchecked copy
#   output   : 200
#   evidence : `scripts/teach_persona.py`
#
# NO `sized_against`: a step budget is a TRAINING quantity and no h/point figure feeds it.
STEP_BUDGET = 200

STEP_BUDGET_PROVENANCE = {
    "record": "scripts/teach_persona.py",
    "record_sha256": None,
    "git_sha": None,
    "derivation": "teach_persona.MAX_STEPS",
    "selected_by": (
        "NOBODY — it is a RESTATEMENT of the production constant every Phase-23 arm already ran "
        "at, not a selection. Never presented at Task 1's checkpoint"
    ),
    "governs": (
        "the per-arm OPTIMIZER-STEP budget, and nothing else. It is the T that the accountant's "
        "epsilon composes over and the `max_steps` a sweep arm trains for; it prices no draws and "
        "decides no outcome. `record_sha256` and `git_sha` are None for the same reason "
        "FULL_FIDELITY_K's are: the source is a live source module, resolved by symbol in the test "
        "rather than pinned by a digest that would go stale on an unrelated edit"
    ),
}

# THE NUMBER OF NEVER-TAUGHT CONTROL SEEDS WHOSE SCORING THE BUDGET MUST PRICE.
#
#   input    : `results/phase23_never_taught_training.json` -> `n_seeds` = 5, over the LADDER seeds
#              (1337, 2024, 1338, 2025, 1339). This record is the BINDING one because its seeds are
#              the adapters 23-14 actually scores, and this constant exists to price THAT scoring.
#              `results/phase23_control_floor.json` carries the same five by D-08's same-N rule —
#              that agreement is the REASON the lists match, not a second source
#   rule     : `results/phase23_cost.json`'s `sizing` block prices the never-taught term as
#              `n_seeds x h_per_point_ceiling_at_k` at every rung, and names that source itself in
#              `never_taught_seeds_source`
#   output   : 5 seeds x 3.1471532286150796 h/point = 15.735766143075399 h at the selected rung
#   evidence : `results/phase23_cost.json`, `sizing["16"]`
#              `never_taught_floor_hours_ceiling`
#
# A BUDGET FOR 16 SWEEP POINTS THAT FORGETS N CONTROL POINTS IS SHORT BY N POINTS. That is why this
# is a pinned constant rather than a number re-read at call time.
N_CONTROL_SEEDS = 5

N_CONTROL_SEEDS_PROVENANCE = {
    "record": "results/phase23_never_taught_training.json",
    "record_sha256": "b4ee3fc3640887982d31d4a52791bd61b8bdf6d293bad153297cb1cdd35f6bbe",
    "git_sha": "5303819632646f156b90fcfec850cebdfb5d1275",
    "derivation": "phase23_prereg.NEVER_TAUGHT_TRAINING_RECORD -> n_seeds",
    "sized_against": "h_per_point_ceiling",
    "seeds": (1337, 2024, 1338, 2025, 1339),
    "selected_by": (
        "NOBODY — it is a MEASURED count read from the never-taught training record, not a "
        "selection. Never presented at Task 1's checkpoint"
    ),
    "governs": (
        "the never-taught CONTROL term of the ceiling-side budget: the count of fresh adapters "
        "23-14 scores, priced at the same per-point ceiling as a sweep point. It is independent of "
        "SWEEP_POINTS — the sweep term scales linearly in width and this one does not — and it "
        "decides no outcome"
    ),
}

# D-06: IS THE n=64 LEG COMMITTABLE?
#
#   input    : `results/phase23_cal03_wiring.json`, READ LIVE rather than assumed — `verdict` is
#              `true`, with `epsilon_n8` and `epsilon_n64` both 24.38161088311366 under exact `==`
#              and `t_n8` and `t_n64` both 4
#   rule     : `phase23_prereg.n64_leg_is_committable`, committed BLIND in 23-03 and strictly
#              ancestral to the record's earliest add. NEVER a relative tolerance
#   output   : the leg is committable, so it is NOT withdrawn
#   evidence : `results/phase23_cal03_wiring.json`
#
# THE NEGATIVE CASE IS RECORDED TOO, WHICH IS WHY THIS CONSTANT EXISTS AT ALL. A confirmation
# recorded only by the ABSENCE of a withdrawal is indistinguishable from never having checked. Both
# branches are written and both are tested (`test_n64_leg_matches_the_cal03_verdict` drives the
# inactive one from a CONSTRUCTED copy of the real record with its verdict flipped, never by
# editing the committed artifact). Had the live read said otherwise, this would be True, every Z
# constant above would describe the n=8 leg ONLY, and the n=8 leg would still stand: D-06's scope
# withdraws the n=64 leg alone, and D-04's halt is a different rule for a different failure.
#
# NO `sized_against`: this is a verdict read, and no throughput figure participates in it.
N64_LEG_WITHDRAWN = False

N64_LEG_WITHDRAWN_PROVENANCE = {
    "record": "results/phase23_cal03_wiring.json",
    "record_sha256": "461d1d6556fb85c666b9a23f76bee2d3b8969a5a3f4145002c46ba9017dc81f9",
    "git_sha": "5faaec4ead49d088fffb8e3ba3f461bafa91bf2f",
    "derivation": "phase23_prereg.n64_leg_is_committable",
    "verdict": True,
    "epsilon_n8": 24.38161088311366,
    "epsilon_n64": 24.38161088311366,
    "t_n8": 4,
    "t_n64": 4,
    "selected_by": (
        "NOBODY — it is a MEASUREMENT READ, not a decision, which is why it is pinned here rather "
        "than asked at Task 1's checkpoint. The confirming branch fired because the committed "
        "wiring record's verdict is true on a live read"
    ),
    "governs": (
        "whether the v4.0 sweep's n=64 leg is committed, and nothing else. False here means the "
        "leg stands and every Z constant above describes BOTH legs. It renders no privacy verdict "
        "and sets no threshold: the epsilons quoted are the CAL-03 wiring calibration's, recorded "
        "so a reader can see WHICH measurement this branch was taken on"
    ),
}

# THE ADVERSARIAL SWEEP GRID: the mixture ratios v4.0's adversarial arm is trained at.
#
#   input    : `results/phase18_corpus.json` -> 336 `core_taught` prompts across the THREE D-10
#              TRAINED attack families (A1-mild, A1-aggressive, A3 — 112 each, COUNTED at this pin
#              and not transcribed), and `results/phase21_multiplicity.json` -> `corpus_geometry`
#              -> 176 clean episodes on arm `dp_n8` (1408 on `dp_n64`)
#   rule     : D-06's unit — adversarial EPISODES per clean EPISODE. The upper extreme is the n=8
#              NO-REPETITION POOL CEILING: the largest ratio at which the whole trained pool is used
#              exactly once and nothing repeats
#   output   : 336 / 176 = 1.9090909090909092 at the top, 0.0 at the bottom, four interior points
#   evidence : `results/phase18_corpus.json`, `results/phase21_multiplicity.json`
#
# THE EXTREME IS A FLOAT LITERAL AND NEVER THE QUOTIENT THAT DERIVES IT. The literal-only guard
# calls `ast.literal_eval` on every assigned value in this file, and `336 / 176` is an `ast.BinOp`
# that RAISES there. So the derivation lives in this comment, and `tests/test_phase24_grid.py`
# counts BOTH operands out of the two committed records and asserts the quotient under exact `==` —
# which is what stops the comment and the literal drifting apart in silence.
#
# ONLY THE TWO EXTREMES ARE PRE-REGISTERED. D-09 fixes `0.0` (the control, byte-identical to v2.0,
# reconnecting the curve by construction) and `1.9090909090909092`. The four interior points and
# their spacing are a RESOURCE choice taken under 24-CONTEXT's Claude's Discretion: they size the
# spend and decide no outcome. `1.0` is episode parity, the legible midpoint. `0.25` is the first
# point ABOVE n=64's OWN no-repetition ceiling (336 / 1408 = 0.23863636363636365), i.e. the first
# point at which D-07 multiplicity becomes non-trivial at the large capacity.
ADVERSARIAL_RATIO_GRID = (0.0, 0.25, 0.5, 1.0, 1.5, 1.9090909090909092)

ADVERSARIAL_RATIO_GRID_PROVENANCE = {
    "unit": (
        "D-06: adversarial EPISODES per clean EPISODE. TOKEN VOLUME IS NOT SWEPT — it floats as a "
        "consequence of the episode ratio and is reported after the fact by the ADVT-03 record "
        "(scored-token counts per arm). The episode unit was chosen because the post-leave-one-out "
        "training pool is exactly 336 episodes regardless of WHICH family is held out, while token "
        "volume varied by up to 1.59x across the same choice: the confound is separable in the "
        "report rather than confounded in the swept axis"
    ),
    "upper_extreme": 1.9090909090909092,
    "upper_extreme_derivation": (
        "3 trained attack families x 112 core_taught prompts = 336 adversarial episodes, over 176 "
        "clean episodes at n=8 (results/phase21_multiplicity.json corpus_geometry) — the largest "
        "point n=8 reaches without repeating anything"
    ),
    "upper_extreme_sources": (
        "results/phase18_corpus.json",
        "results/phase21_multiplicity.json",
    ),
    "upper_extreme_source_provenance": {
        "results/phase18_corpus.json": {
            "sha256": "ff8e6e3c24987ac393cc262233f1b0bfdad5dc11eefa4cc1224a164cfd0f7d67",
            "git_sha": None,
        },
        "results/phase21_multiplicity.json": {
            "sha256": "e9e3b9bf3d31525ad27f90c0afdac0faf97e7faef324cf05d832898c00944da1",
            "git_sha": "eba0571a7f75e6631b7b080939d130947b703cdf",
        },
    },
    "lower_extreme": 0.0,
    "lower_extreme_meaning": (
        "THE CONTROL. At ratio 0.0 there are zero adversarial episodes, so the arm's bins are "
        "BYTE-IDENTICAL to v2.0's and the adversarial curve reconnects to the incumbent result BY "
        "CONSTRUCTION rather than by a claimed correspondence. It is also why SC1's byte-identity "
        "requirement cannot discriminate between D-08's placement options: at this point every "
        "placement collapses to today's concatenation"
    ),
    "trained_families": ("A1-mild", "A1-aggressive", "A3"),
    "held_out_family": "A2",
    "held_out_reason": (
        "VALUE CONTAINMENT (D-10/D-12), NEVER SELECTION BY PERFORMANCE. `build_a2_prompt` ends the "
        "prompt with floor(len(value_ids) * 0.25) leading ids OF THE PRIVATE VALUE, past "
        "<|assistant|>, where `encode_dialogue` marks assistant content mask=1 — so an A2 TRAINING "
        "episode's target would be <25% of the private value> + <refusal>, training the model to "
        "emit a prefix of the value before refusing, the exact inverse of D-01's guarantee. "
        "`contains_value` requires the WHOLE value, so that prefix would not even score as a leak: "
        "the harm exists and the instrument is structurally blind to it. The reason is structural "
        "and PRECEDES every run, which is what makes it immune to the peek ADVT-02 forbids — and "
        "it equally may NOT be claimed as a deliberate leave-one-out choice"
    ),
    "point_count": 6,
    "point_count_selected_by": (
        "THE PLANNER, under 24-CONTEXT's Claude's Discretion — and ONLY for the four INTERIOR "
        "points and their spacing. The two extremes are pre-registered by D-09 and are not "
        "discretionary. The interior count is a RESOURCE parameter in the strict sense this module "
        "exists to hold: it sizes the spend and decides no outcome. No gate, no threshold and no "
        "criterion reads it; widening or narrowing it changes how much compute the frontier costs "
        "and changes no verdict"
    ),
    "multiplicity_at_upper_extreme": {"dp_n8": 1.0, "dp_n64": 8.0},
    # ---------------------------------------------------------------------------------------
    # WR-05 CORRECTION, ADDED 2026-09-01 BY PLAN 25-12. ADDITIVE, NEVER AN EDIT.
    # The key ABOVE keys on `dp_n8`/`dp_n64`. Every MEASURED row in
    # results/phase24_token_budget.json keys on `adv_n8`/`adv_n64`, and those rows record
    # `adversarial_multiplicity` 1.0 at adv_n8 and 8.0 at adv_n64 at this same upper extreme —
    # the identical values under the arm names the measurement actually used. The original key
    # is LEFT STANDING because this module is append-only and because it is what was believed;
    # the correction is a sibling.
    # ---------------------------------------------------------------------------------------
    "multiplicity_at_upper_extreme_corrected": {"adv_n8": 1.0, "adv_n64": 8.0},
    "multiplicity_key_correction": (
        "2026-09-01, PLAN 25-12, closing 24-REVIEW WR-05 under D-41. `multiplicity_at_upper_"
        "extreme` above keys on dp_n8/dp_n64, which are the arm names "
        "results/phase21_multiplicity.json's corpus_geometry carries; but the ADVERSARIAL sweep "
        "this grid sizes runs on adv_n8/adv_n64, and every measured row in "
        "results/phase24_token_budget.json keys on those. Measured at the upper extreme: adv_n8 "
        "clean_episodes 176 / adversarial_episodes 336 / adversarial_multiplicity 1.0, and "
        "adv_n64 clean_episodes 1408 / adversarial_episodes 2688 / adversarial_multiplicity 8.0 — "
        "identical values, disagreeing arm names. THE ORIGINAL KEY STAYS STANDING: this module is "
        "append-only, the figure it carries is correct, and erasing a believed figure would "
        "destroy the record of what was believed. The corrected sibling above is the key a "
        "consumer joining against a measured adversarial row should read"
    ),
    "governs": (
        "the number of ADVERSARIAL SWEEP POINTS PER CAPACITY in Phase 25's frontier, and nothing "
        "else. It is a RESOURCE parameter: it sizes the spend and decides no outcome. It is "
        "independent of SWEEP_POINTS, which sizes the NOISE sweep. It carries no `sized_against`, "
        "because no throughput figure participates in it — the grid was derived from a corpus "
        "count and an episode count, not from an h/point measurement. It carries no top-level "
        "`git_sha` "
        "or `record_sha256` either, and that absence is BY CONSTRUCTION rather than an omission: "
        "the pin has TWO backing records, so a single digest could only name one of them, and a "
        "commit sha for 'where this pin landed' cannot be written into the commit that lands it. "
        "`upper_extreme_source_provenance` carries a per-record digest instead, checked LIVE, and "
        "`results/phase18_corpus.json` records no `git_sha` of its own — that None is asserted "
        "absent rather than invented"
    ),
}


# =================================================================================================
# PLAN 25-12: THE NOISE AXIS — sigma, its epsilon, and the TWO clip constants.
#
# NONE OF THE FOUR IS A Z CONSTANT and none carries `sized_against`. No throughput figure feeds
# any of them: they size the NOISE axis, not the spend. They are subtracted from
# `tests/test_phase23_budget.py`'s Z register through `_POST_23_13_CONSTANTS`, each mapped to
# `tests/test_phase25_grid.py`, which re-derives every one of them LIVE.
#
# LITERALS, AND THAT IS FORCED RATHER THAN STYLISTIC. This module's guard
# (`test_budget_holds_only_literal_constants`) requires the body to be a docstring plus
# `ast.Assign` only and runs `ast.literal_eval` on every assigned value, so a `sigma_for(...)`
# call, an `epsilon_for(...)` call and a division are all `ast` nodes it refuses. Every epsilon
# below is TRANSCRIBED from what `personacore.privacy.accountant.epsilon_for` returned; nothing
# here is computed.
# =================================================================================================

# THE SIGMA LADDER (D-17, D-18, D-20).
#
#   input    : the measured epsilon(sigma) curve at T = STEP_BUDGET, delta = mitigation_unit.DELTA,
#              and the probed high anchor in results/phase25_sigma_hi_probe.json
#   rule     : a geometric span in sigma from the repository's ONLY committed noised point
#              (sigma 0.5, results/phase23_noised_dp_n64_sigma0p500000.json) up to the PROBED
#              anchor, in ROUND sigma values. Slot 0 is the sigma=0 CONTROL, which D-20 places
#              INSIDE SWEEP_POINTS, leaving 15 noised rungs per leg
#   output   : the 16 float literals below
#   evidence : results/phase25_sigma_hi_probe.json (the anchor), and
#              results/phase25_clip_calibration.json (the C the anchor was probed at)
#
# ROUND SIGMA AND NOT ROUND EPSILON, AND THE REASON IS MEASURED. `sigma_for` is a numerical
# inverse whose round trip is exact to about one ULP and NOT exact:
# `sigma_for(8, 200, 1e-5) = 8.488520944343772` gives `epsilon_for` back 7.9999999999999964, not
# 8. Pinning round-number epsilon targets would therefore be unsatisfiable under the `==` that
# `tests/test_phase25_grid.py` checks the correspondence with. Round sigma with the FULL-PRECISION
# epsilon transcribed beside it is the only ==-satisfiable formulation, and it is
# `tests/test_phase24_grid.py`'s own literal-pinned-plus-live-derivation shape.
SIGMA_LADDER = (
    0.0,
    0.5,
    0.7,
    1.0,
    1.5,
    2.0,
    3.0,
    4.0,
    6.0,
    8.0,
    12.0,
    16.0,
    24.0,
    32.0,
    50.0,
    80.0,
)

SIGMA_LADDER_PROVENANCE = {
    "record": "results/phase25_sigma_hi_probe.json",
    "record_sha256": "b5c979d69a181e319840ec30565198f02589ce75c1d6f8f32367d8624b0d9d10",
    "git_sha": "79e6431ff7fdd5cd5c56f25ac62a34f61e64a4ab",
    "derivation": (
        "a geometric span in sigma from the repository's only committed noised point (sigma 0.5, "
        "results/phase23_noised_dp_n64_sigma0p500000.json, epsilon 519.6981942303134) up to the "
        "PROBED high anchor, in round sigma values; slot 0 is the sigma=0 control"
    ),
    "anchor": 80.0,
    "anchor_probed_not_presumed": (
        "D-18. results/phase25_sigma_hi_probe.json trained dp_n64 at sigma "
        "80.0 and C 1.3254119157791138, scored it RECALL-ONLY, and read "
        "taught recall 0/"
        "1008 against the same run's adapter-OFF "
        "0/"
        "1008. The record was committed BEFORE "
        "this literal existed and tests/test_phase25_grid.py::"
        "test_the_ratchet_rule_is_committed_before_the_ladder asserts that order from `git log` "
        "rather than trusting it"
    ),
    "anchor_selection_rule": (
        "the SMALLEST ROUND sigma whose epsilon at T=200, delta=1e-5 falls below 1 — the only "
        "pre-existing landmark on this axis that is not this project's own preference. sigma 50.0 "
        "reads 1.060789755417757 (above 1) and sigma 80.0 reads 0.6339783761989397 (below 1)"
    ),
    "extension_rule": (
        "RATCHET-SHAPED, and it lives in full in results/phase25_sigma_hi_probe.json's "
        "RATCHET_EXTENSION_RULE. If the high extreme's FULL extraction read still misses the "
        "never-taught floor, the ladder EXTENDS UPWARD by a pre-registered rung whose epsilon is "
        "HALF the current top rung's. It never shifts and never shrinks, so it has no cheap "
        "direction"
    ),
    "control_slot": 0,
    "control_slot_reason": (
        "D-20 puts sigma=0 INSIDE SWEEP_POINTS = 16 rather than beside it: CTRL-02 makes the "
        "control a REAL sweep point and phase23_cost.sizing['16'] prices 16 points plus the "
        "never-taught floor as a SEPARATE term, reserving nothing for a 17th. 15 noised rungs per "
        "DP leg, and the phase total stays 44"
    ),
    "reused_at_both_capacities": True,
    "reused_at_both_capacities_reason": (
        "ONE ladder serves dp_n8 AND dp_n64, and that is forced twice over. "
        "mitigation_gate.capacity_comparison compares the two legs' mechanisms under EXACT "
        "equality on every key of MECHANISM_KEYS, of which sigma is one — so reusing a single set "
        "of literals satisfies that check BY CONSTRUCTION rather than by two ladders happening to "
        "agree. And this module is literal-only, so a per-capacity ladder derived from a shared "
        "one could not be written here at all. There is no per-capacity variant name in this "
        "module and tests/test_phase25_grid.py::test_one_ladder_serves_both_capacities asserts "
        "that absence"
    ),
    "governs": (
        "the NOISE COORDINATE of every DP sweep point in Phase 25's frontier, at both capacities, "
        "and nothing else. It is a RESOURCE/COVERAGE parameter in this module's strict sense: it "
        "decides WHERE the curve is sampled, not what any reading of it means. No gate, no "
        "threshold and no criterion reads it. It carries no `sized_against` because NO THROUGHPUT "
        "FIGURE PARTICIPATES IN IT — the ladder was derived from an epsilon curve and a recall "
        "probe, never from an h/point measurement"
    ),
}

# THE EPSILON LADDER — `epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, mitigation_unit.DELTA)`,
# TRANSCRIBED AT FULL PRECISION.
#
# INDEX 0 IS `None`, AND THREE INDEPENDENT REASONS AGREE ON IT: `epsilon_for(0.0, ...)` returns
# `math.inf`; `inf` is not `ast.literal_eval`-able so this module could not hold it even if it
# wanted to; and D-29 states that the sigma=0 control carries NO epsilon at all. All three are
# asserted in `tests/test_phase25_grid.py::test_the_control_rung_carries_no_epsilon`, so the
# `None` is proved FORCED rather than chosen.
#
# Entry 1 is 519.6981942303134, which is BIT-IDENTICAL to the epsilon already committed in
# results/phase23_noised_dp_n64_sigma0p500000.json — the ladder's low end reconnects to the one
# noised point the repository has actually run, rather than to a fresh computation.
EPSILON_LADDER = (
    None,
    519.6981942303134,
    289.33863705009264,
    159.44148628736576,
    83.8305906128762,
    54.37663901498563,
    30.50627999271221,
    20.675508046994032,
    12.262332118205716,
    8.595865790470416,
    5.299979064701441,
    3.7965357228934966,
    2.3957449097512216,
    1.7369988136430536,
    1.060789755417757,
    0.6339783761989397,
)

EPSILON_LADDER_PROVENANCE = {
    "record": "results/phase23_noised_dp_n64_sigma0p500000.json",
    "record_sha256": "99d70adb4ac02543c0c93df42b2947de4a037758704ecc09206332267f2a85f7",
    "git_sha": None,
    "derivation": (
        "personacore.privacy.accountant.epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, "
        "mitigation_unit.DELTA) for i in 1..15, transcribed at full precision. Index 0 is None. "
        "The cited record is the ONE committed point this ladder can be checked against without "
        "recomputing it: its epsilon field is 519.6981942303134 and EPSILON_LADDER[1] is the same "
        "double. `git_sha` is None because this ladder is not derived FROM that record — the "
        "record is a bit-level cross-check on one entry of a ladder computed from the accountant"
    ),
    "delta": 1e-05,
    "delta_source": "mitigation_unit.DELTA, read live by tests/test_phase25_grid.py",
    "steps": 200,
    "steps_source": (
        "STEP_BUDGET, pinned above. D-27: it is the SAME T at both capacities, measured rather "
        "than inferred — phase23_sigma_zero and phase23_noised_dp_n64 both record composed_steps "
        "200 with t_matches_across_capacities true — which is what lets ONE epsilon ladder serve "
        "both legs, since epsilon_for reads T and T does not move with capacity"
    ),
    "checked_under": (
        "EXACT `==`, no tolerance, in tests/test_phase25_grid.py::"
        "test_each_noised_rung_lands_on_its_pinned_epsilon over all 15 noised rungs"
    ),
    "governs": (
        "the PUBLISHED per-point epsilon of each noised DP sweep point, and nothing else. It "
        "carries no `sized_against`: no throughput figure participates in it"
    ),
}

# THE CLIP CONSTANT FOR THE NOISED POINTS (D-24).
#
#   input    : the PER-RECORD gradient-norm distribution on the DP path, measured value by value
#              at both capacities over the full MAX_STEPS = 200
#   rule     : `sorted(per_record_norms['dp_n64']['values'])[6399]` —
#              the order statistic at quantile 0.5 with NO interpolation, so the
#              candidate IS one of the measured values and re-derives from them BY INDEX under
#              exact equality. The quantile was fixed BEFORE the number
#   output   : the float literal below
#   evidence : results/phase25_clip_calibration.json
#
# WHY NOT C = 1.0. results/phase23_noised_dp_n64_sigma0p500000.json recorded
# `clip_bind_count` 12800 of 12800 at C = 1.0 — 100% binding. At fixed sigma epsilon does not
# depend on C, so a C below every record's norm is pure clipping bias bought for nothing. The
# measurement confirms the counter-example is real rather than an artifact of one run:
# 12508 of
# 12800 measured
# dp_n64 records exceed 1.0.
CLIP_NORM = 1.3254119157791138

CLIP_NORM_PROVENANCE = {
    "record": "results/phase25_clip_calibration.json",
    "record_sha256": "54dc7bd17190a9c712423627273b4ba800644674612b4d7641f897ad99e4d797",
    "git_sha": "6df1ebac406745f3854eebcdcb8ac589e377d81c",
    "derivation": (
        "clip_norm_rule in the cited record: the order statistic "
        "sorted(per_record_norms[capacity]['values'])[ceil(q * n) - 1] at q = 0.5 over the "
        "BINDING capacity's own distribution, taken WITHOUT interpolation. "
        "tests/test_phase25_grid.py::test_clip_norm_re_derives_from_the_committed_measurement "
        "recomputes it from the recorded per-record values and asserts exact equality"
    ),
    "rule_capacity": "dp_n64",
    "rule_quantile": 0.5,
    "rule_index": 6399,
    "n_records": 12800,
    "governs": (
        "every NOISED DP sweep point, at BOTH capacities. It does NOT govern the sigma=0 control, "
        "which runs at CONTROL_CLIP_NORM below. It is a RESOURCE parameter: it sizes the noise "
        "(std = sigma * C at dpsgd.py's one draw site) and decides no outcome. It carries no "
        "`sized_against`: no throughput figure participates in it"
    ),
    "why_two_constants": (
        "D-01's reproduction of the sigma=0 control is BIT-LEVEL against "
        "results/phase23_sigma_zero.json, which ran at 1000000.0. Applying this calibrated "
        "value to the control would break that reproduction, and 25-CONTEXT resolves the pair "
        "nowhere — so TWO constants are pinned and each names the points it governs"
    ),
    "not_a_mechanism_key": (
        "C CANNOT JOIN mitigation_gate.MECHANISM_KEYS and does not need to (D-25). The gate is "
        "FROZEN and ancestry-guarded: any commit to scripts/mitigation_gate.py after "
        "results/phase20_* exists reddens the guard permanently, and the guard takes adds[-1] — "
        "the EARLIEST add — so a `git rm` plus a re-add cannot launder it. The gap is closed "
        "CALLER-SIDE instead: clip_norm travels in the mechanism dicts and the Phase 25 driver "
        "proves equality on it BEFORE calling the gate. This single literal makes that true by "
        "construction"
    ),
    "extra_keys_are_ignored_measured": (
        "MEASURED LIVE ON THE FROZEN GATE, 2026-09-01, not argued: capacity_comparison's check is "
        "`missing = [key for key in MECHANISM_KEYS if key not in ...]`, so EXTRA keys are ignored "
        "rather than refused. Called with the two mechanism mappings agreeing on all four "
        "MECHANISM_KEYS and differing only in clip_norm at exactly this pin's own pair "
        "(1.3254119157791138 against 1000000.0, a ratio of 754482.4277607104), it returned branch "
        "'recovery-at-both-capacities' and NOT ONE of its reason strings mentioned clip. That "
        "silence is why the equality is proved caller-side"
    ),
}

# THE CLIP CONSTANT FOR THE CONTROL (D-01, D-25).
#
#   input    : results/phase23_sigma_zero.json's own `clip_norm`, read live rather than retyped
#   rule     : the sigma=0 control REUSES Phase 23's value UNCHANGED, or D-01's reproduction is
#              not bit-level
#   output   : the float literal below
#   evidence : results/phase23_sigma_zero.json — which ran at this value and recorded
#              `clip_bind_count` 0 over the whole run, so the bound is PROVEN not to bind rather
#              than assumed not to
CONTROL_CLIP_NORM = 1000000.0

CONTROL_CLIP_NORM_PROVENANCE = {
    "record": "results/phase23_sigma_zero.json",
    "record_sha256": "dd34e51398b87d54c4e83dcfd192a0e7abead7c73d143aeb28b11cfa07e85d36",
    "git_sha": "9ed2370f78732aa36e0041499290abd924e013ac",
    "derivation": (
        "read live from the cited record's own `clip_norm` field, never retyped. "
        "tests/test_phase25_grid.py::test_the_control_clip_norm_matches_phase_23 re-reads it from "
        "that record on every suite run"
    ),
    "clip_bind_count_at_this_value": 0,
    "non_binding_is_observed_not_assumed": (
        "the cited record ran the full 200 steps at this value and recorded clip_bind_count 0, so "
        "'non-binding' is an observation over "
        "200 step(s) rather than a property claimed of a "
        "large number"
    ),
    "governs": (
        "the sigma=0 CONTROL point only, at both capacities. Every noised point runs at CLIP_NORM "
        "above. It is a RESOURCE parameter and carries no `sized_against`: no throughput figure "
        "participates in it"
    ),
    "why_not_the_calibrated_value": (
        "D-01's reproduction of the control is BIT-LEVEL. The control must reuse Phase 23's bound "
        "UNCHANGED or the reproduction is not bit-level, so the calibrated CLIP_NORM must never be "
        "applied to the control point"
    ),
}
