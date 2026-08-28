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
