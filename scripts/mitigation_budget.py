"""PHASE 23'S **RESOURCE** BUDGET — measured numbers, pinned as literals. NOTHING ELSE LIVES HERE.

WHAT THIS FILE IS
-----------------
The RESOURCE parameters v4.0's sweep is priced against. Today that is ONE number: D-03's measured
seed-to-seed noise floor of the control arm. The Z values (the per-point compute budget) arrive in
23-13, after CAL-01 and CAL-05 measure the per-point cost in 23-11 — they are NOT reserved here as
placeholders, because a placeholder is a literal with no evidence and this file's whole discipline
is that a literal carries its evidence.

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
