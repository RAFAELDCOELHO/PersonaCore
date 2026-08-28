"""CAL-02's STRUCTURAL obligations — the gate/budget split, proved TRANSITIVELY.

WHAT THIS FILE IS, AND WHAT IT DELIBERATELY IS NOT
--------------------------------------------------
The **STATIC** half of CAL-02's guard already exists and already bites. It lives at
``tests/test_phase20_prereg.py::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only``,
it already names ``mitigation_budget`` by string, and it scans the whole ``scripts/mitigation_*.py``
glob so it admits ``scripts/mitigation_budget.py`` the moment Phase 23 creates it. **It is NOT
duplicated here.** ``tests/test_phase20_prereg.py:153-155`` states the rule this file obeys: a
lookalike copy proves something about a DIFFERENT function than the one CI executes, so a guard
proved correct somewhere else and the guard actually running must be the SAME code.

``scripts/mitigation_gate.py`` is **FROZEN** — every commit touching it must be an ancestor of every
``results/phase20_*`` artifact's earliest add, three of which are committed, and a ``git rm`` plus a
re-add cannot launder that because the guard takes the EARLIEST add. There is no recovery path and
no force flag. Nothing in Phase 23 writes to it; this file only READS it.

THE HOLE THE STATIC HALF CANNOT SEE
-----------------------------------
The static scan walks ``scripts/mitigation_*.py`` and nothing else. But the gate's own import list
(``scripts/mitigation_gate.py:56-63``) is ``pathlib``, ``sys`` and **``erasure_gate``** — and
``scripts/erasure_gate.py`` sits OUTSIDE that glob. So the route

    mitigation_gate  ->  erasure_gate  ->  mitigation_budget

is INVISIBLE to any AST walk over ``mitigation_*.py``, however careful. ``erasure_gate.py`` imports
only ``math`` today (``scripts/erasure_gate.py:68``), so the route is empty in fact — but "empty in
fact" is not "structurally unable to import", and SC3 asks for the second.

``test_gate_does_not_transitively_load_the_budget`` below closes it the way this project already
calls the standard: an **out-of-process** probe that execs the real frozen gate and asks the
interpreter, not the source text, what got loaded. The shape is
``tests/test_phase22_accountant.py::test_accountant_imports_math_only``'s second half, cited by
symbol and copied in structure rather than re-derived. Its docstring records WHY out of process is
mandatory and the reason applies here unchanged: by the time this test runs, ``torch`` is already in
``sys.modules`` from sibling tests, so an in-process check would be vacuous.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import hashlib
import importlib.util
import json
import math
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

# `mitigation_budget` is imported HERE, in the parent process, and that cannot make the transitive
# probe below vacuous: `_run_probe` spawns a FRESH interpreter whose `sys.modules` starts empty, so
# what this process has loaded is invisible to it. (That is the same reason the probe has to be out
# of process at all — `torch` is already loaded here from sibling tests.)
import mitigation_budget  # noqa: E402  (needs the sys.path insert above)
import mitigation_gate  # noqa: E402  (needs the sys.path insert above)

# The matched comparator's PATH REGISTER, imported so no test in this file holds the record path as
# a string literal. This repository has shipped plans naming paths the code refuses, so every
# Phase-23 artifact path resolves from the module that declares it. Importing it HERE is free: the
# zero-headroom ceiling is a property of `scripts/mitigation_*.py`, not of this test file.
import phase23_cost  # noqa: E402  (needs the sys.path insert above)
import phase23_matched_prereg  # noqa: E402  (needs the sys.path insert above)
import phase23_prereg  # noqa: E402  (needs the sys.path insert above)

# `tests/` is not a package either, so this is the same register as
# `tests/test_phase22_fakes.py:55`. Imported rather than re-globbed: the whole point of
# `test_the_budget_module_is_protected_but_not_frozen` is a statement about the register that
# actually runs in CI, and a second glob here would be a statement about a different tuple.
from test_phase20_prereg import _GATE_MODULES  # noqa: E402

_MITIGATION_GATE_PATH = _ROOT / "scripts" / "mitigation_gate.py"
_MITIGATION_BUDGET_PATH = _ROOT / "scripts" / "mitigation_budget.py"
_MITIGATION_BUDGET_REL = "scripts/mitigation_budget.py"
_PHASE20_PREREG_PATH = _ROOT / "tests" / "test_phase20_prereg.py"

# ``mitigation_budget`` is the name CAL-02 is about. The other three are the classic offenders
# ``test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only`` names SEPARATELY from its
# subset assertion, for the reason recorded there: so the failure message says WHICH one. They are
# carried here too because the transitive probe is the only half that can see them arriving through
# ``erasure_gate``.
_FORBIDDEN = ("mitigation_budget", "torch", "numpy", "scipy")

# ============================================================================================
# THE IMPORT CEILING — AN OBSERVATION, MEASURED 2026-08-26 IN THIS WORKING TREE (T-23-10)
# ============================================================================================
# Recorded HERE, in a test file plan 23-09 must read, rather than only in a planning document it
# may not. `test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` asserts
# `imported <= {"pathlib", "sys", "erasure_gate"}` over the UNION across every
# `scripts/mitigation_*.py`. Measured, by walking the AST of each module in the tree today:
#
#     scripts/mitigation_accountant.py   ->  no imports at all
#     scripts/mitigation_unit.py         ->  no imports at all
#     scripts/mitigation_gate.py         ->  pathlib, sys, erasure_gate   (:49-63)
#
# The union is EXACTLY the allow-set, so the ceiling has **zero headroom**. A new
# `scripts/mitigation_*.py` sibling gets no import budget whatsoever, and this is not a guess —
# it was watched:
#
#   (a) a scratch `mitigation_zzprobe.py` containing `import mitigation_budget` produced
#       `AssertionError: a mitigation_*.py module imports mitigation_budget (imports:
#       ['erasure_gate', 'mitigation_budget', 'pathlib', 'sys'])`
#   (b) a scratch `mitigation_budget.py` containing a single `import json` produced
#       `AssertionError: the mitigation modules import ['json'] beyond the allow-set
#       ['erasure_gate', 'pathlib', 'sys']`
#
# Both scratch modules were deleted and `git status --short scripts/` proved empty afterwards.
#
# CONSEQUENCES FOR `scripts/mitigation_budget.py` (plan 23-09), in priority order:
#
#   1. It must have ZERO imports. Not `json`, not `math`, not `dataclasses`. `scripts/
#      phase19_floor.py` is the shape that satisfies this for free — literal assignments and
#      nothing else, each beside a provenance comment naming the artifact it came from.
#   2. It may not import `mitigation_gate` EITHER. That would add `mitigation_gate` to `imported`
#      and break the subset assertion just as surely as `json` does — and it is the import a
#      reader would most naturally reach for, since the budget's K has to agree with the gate's
#      closed menu.
#   3. So a selected K is RESTATED as a literal carrying a provenance comment naming
#      `scripts/mitigation_gate.py::K_RUNGS`, and 23-09 must ship a TEST asserting the literal and
#      the menu agree. A restated constant with no test agreeing it is a copy waiting to drift;
#      that test is the whole price of the zero-import ceiling and it is not optional.
#
# The alternative — widening `allowed` — is available and is REFUSED: it weakens a committed guard
# to accommodate a module that has not been written yet, which is the wrong way round.
# ============================================================================================

# THE META-GUARD (T-23-07). A probe whose ``exec_module`` silently failed would load nothing at all
# and then report an empty offender list — green, and proving nothing. So the probe PRINTS a
# sentinel read off the exec'd module and the test asserts it arrived.
# ``test_accountant_imports_math_only`` carries the same idea as its ``assert imported`` meta-guard.
_SENTINEL_PREFIX = "GATE_SENTINEL="
_SENTINEL_ATTR = "NEVER_TAUGHT_ARM"


def _import_probe(module_path):
    """Source for a fresh interpreter that execs ``module_path`` and reports what it dragged in.

    Exits 1 with the offender list on stdout when any ``_FORBIDDEN`` name reached ``sys.modules``,
    0 otherwise. One builder, used by BOTH the real-gate test and the positive control below, so
    the control cannot drift into exercising a different probe than the one that guards the gate.
    """
    return (
        "import importlib.util, sys;"
        f"spec = importlib.util.spec_from_file_location('probe_target', {module_path!r});"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
        f"print({_SENTINEL_PREFIX!r} + repr(getattr(m, {_SENTINEL_ATTR!r})));"
        f"bad = [n for n in {_FORBIDDEN!r} if n in sys.modules];"
        "print(bad); sys.exit(1 if bad else 0)"
    )


def _run_probe(module_path):
    return subprocess.run(
        [sys.executable, "-c", _import_probe(module_path)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )


def test_gate_does_not_transitively_load_the_budget():
    """CAL-02 / SC3 / T-23-06 — the gate is structurally unable to reach the budget, TRANSITIVELY.

    The static scan at ``tests/test_phase20_prereg.py:1171`` proves the gate never NAMES
    ``mitigation_budget``. This proves the stronger thing: exec the real frozen gate in a fresh
    interpreter and ``mitigation_budget`` is not in ``sys.modules`` afterwards — closing the
    ``gate -> erasure_gate -> budget`` route that sits outside the ``mitigation_*.py`` glob the
    static scan walks.
    """
    relative = _MITIGATION_GATE_PATH.relative_to(_ROOT).as_posix()
    result = _run_probe(relative)

    # Meta-guard FIRST, for the same reason the accountant's runs first: a probe that loaded
    # nothing would otherwise pass by finding no offenders in an empty process.
    expected = _SENTINEL_PREFIX + repr(getattr(mitigation_gate, _SENTINEL_ATTR))
    assert expected in result.stdout, (
        f"the probe never printed {expected!r}, so `scripts/mitigation_gate.py` did NOT actually "
        f"load — the walk collapsed and the offender list below proves nothing\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    assert result.returncode == 0, (
        f"`scripts/mitigation_gate.py` TRANSITIVELY loads a forbidden module — CAL-02/SC3 "
        f"violated. The offender list is on stdout. The route the static AST scan cannot see is "
        f"gate -> erasure_gate -> X, because `scripts/erasure_gate.py` is outside the "
        f"`scripts/mitigation_*.py` glob that scan walks.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_the_transitive_probe_detects_a_module_that_does_load_the_budget(tmp_path):
    """POSITIVE CONTROL for the probe above, and it is PERMANENT rather than a one-off.

    A guard nobody has watched fail is not evidence. The two STATIC assertions were watched RED by
    hand against scratch modules in `scripts/` (see the ceiling block above for their literal
    failure text); that observation is transient by construction, because the scratch modules have
    to be deleted afterwards. This one is not: it builds its scratch pair under `tmp_path`, so it
    can live in the suite and re-prove itself on every run. A watched RED that runs every time is
    strictly better evidence than one performed once.

    WHAT IT DOES AND DOES NOT CLAIM. It proves the PROBE detects the route — nothing about the real
    gate, which `test_gate_does_not_transitively_load_the_budget` covers. The two share
    `_import_probe`, so the control cannot pass by exercising a different probe than the one that
    guards the gate.

    The scratch loader stands in for a hypothetical `erasure_gate` that grew an import: it is a
    module the probe execs which reaches `mitigation_budget` INDIRECTLY, through `sys.path` rather
    than by sitting in the `scripts/mitigation_*.py` glob. That is precisely the shape the static
    AST scan cannot see, so the RED here is the RED that matters.
    """
    (tmp_path / "mitigation_budget.py").write_text("Z_SWEEP = ()\n", encoding="utf-8")

    sentinel_value = getattr(mitigation_gate, _SENTINEL_ATTR)
    loader = tmp_path / "scratch_gate.py"
    loader.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(tmp_path)!r})\n"
        "import mitigation_budget  # noqa: F401\n"
        # Cited off the real gate rather than retyped, so the two sentinels cannot drift.
        f"{_SENTINEL_ATTR} = {sentinel_value!r}\n",
        encoding="utf-8",
    )

    result = _run_probe(str(loader))

    # Same meta-guard, same order: prove the scratch module LOADED before reading its verdict. A
    # crash would also exit non-zero, and a control that cannot tell "detected" from "crashed"
    # proves nothing.
    expected = _SENTINEL_PREFIX + repr(sentinel_value)
    assert expected in result.stdout, (
        f"the control's scratch module never printed {expected!r} — it CRASHED rather than being "
        f"caught, so this test is not observing what it claims to observe\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    assert result.returncode == 1, (
        f"the probe stayed GREEN against a module that DOES load mitigation_budget — the probe in "
        f"this file is vacuous and `test_gate_does_not_transitively_load_the_budget` proves "
        f"nothing\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "mitigation_budget" in result.stdout, (
        f"the probe reddened but did not NAME mitigation_budget on stdout, so a real failure would "
        f"not tell its reader which module got in\nstdout: {result.stdout}"
    )


# =================================================================================================
# THE THREE PROPERTIES `scripts/phase19_floor.py` CARRIES, APPLIED TO `scripts/mitigation_budget.py`
#
# A measured number is allowed to live OUTSIDE the closed pre-registration only because of three
# things, none of them a promise: an ancestry-visible ordering against the artifact it came from,
# re-derivation from that committed artifact through the pinned rule on every suite run, and
# literal assignments and nothing else. The third also satisfies, for free, the zero-headroom
# import ceiling recorded above.
# =================================================================================================


def _control_record():
    """The committed floor record, parsed. The ONE reader, so no test holds a second copy."""
    path = _ROOT / phase23_prereg.CONTROL_FLOOR_RECORD
    return path, json.loads(path.read_text(encoding="utf-8"))


def _control_readings(record):
    """The five per-seed primary readings, RECOMPUTED FROM THEIR COUNTS rather than read as rates.

    ``k / n`` is the raw evidence with its denominator attached; ``primary.rate`` is that division
    already performed by the writer. Both are asserted equal in
    ``test_budget_constants_re_derive``, and the reduction is driven from the counts — so a record
    whose stored rate drifted from its own counts is caught rather than trusted.
    """
    return [entry["primary"]["k"] / entry["primary"]["n"] for entry in record["per_seed"]]


def _matched_record():
    """The committed PROTOCOL-MATCHED comparator record, parsed. `_control_record`'s sibling.

    The path resolves from ``phase23_matched_prereg.MATCHED_CONTROL_RECORD`` — the pin that
    declares it — rather than from a string literal here, exactly as ``_control_record`` resolves
    from ``phase23_prereg.CONTROL_FLOOR_RECORD``.
    """
    path = _ROOT / phase23_matched_prereg.MATCHED_CONTROL_RECORD
    return path, json.loads(path.read_text(encoding="utf-8"))


def _matched_readings(record):
    """The five matched per-seed primary readings, RECOMPUTED FROM THEIR COUNTS, not read as rates.

    ``_control_readings``'s sibling, and the same reason for existing: ``k / n`` is the raw evidence
    with its denominator attached, ``primary.rate`` is that division already performed by the
    writer, and driving the reduction from the counts is what catches a stored rate that drifted
    from its own evidence.

    The order is the record's own ``per_seed`` order, which is LADDER order
    ``(1337, 2024, 1338, 2025, 1339)`` and NOT sorted order. The reduction is a range and is
    order-insensitive, but ``control_readings[0]`` — the central-reading rule pinned at ``c7de5d4``
    — is not, so this list is never sorted.
    """
    return [entry["primary"]["k"] / entry["primary"]["n"] for entry in record["per_seed"]]


# =================================================================================================
# PLAN 23-13: Z'S RECORD HELPERS AND ITS CONSTANT REGISTER
#
# EVERY STRUCTURAL CHECK BELOW IS AN AST WALK OR A KEY LOOKUP, NEVER A GREP.
# `MATCHED_CONTROL_NOISE_FLOOR` CONTAINS `CONTROL_NOISE_FLOOR` as a substring, and this file's own
# docstrings name `h_per_point_ceiling`, `K_RUNGS` and `N64_LEG_WITHDRAWN` in prose — a grep
# criterion over either file would match itself and report a pass.
# =================================================================================================

# The Z constants, in the order `scripts/mitigation_budget.py` declares them. Asserted against an
# AST walk in `test_z_was_sized_against_the_ceiling`, so a seventh constant added without being
# registered here cannot slip past the loops that iterate this tuple.
_Z_CONSTANTS = (
    "SWEEP_POINTS",
    "CURVE_K",
    "FULL_FIDELITY_K",
    "STEP_BUDGET",
    "N_CONTROL_SEEDS",
    "N64_LEG_WITHDRAWN",
)

# The two constants that predate 23-13 — subtracted from the AST walk so the register check above
# is a statement about the NEW constants rather than about the whole module.
_PRE_23_13_CONSTANTS = ("CONTROL_NOISE_FLOOR", "MATCHED_CONTROL_NOISE_FLOOR")

# THE THREE MULTIPLICANDS OF THE CEILING-SIDE TOTAL. `SWEEP_POINTS x h_ceiling(CURVE_K)` plus
# `N_CONTROL_SEEDS x h_ceiling(CURVE_K)` — so each was genuinely sized against
# `h_per_point_ceiling` and each is a place a floor-sized number could hide. The other three carry
# no throughput figure at all, and `test_z_was_sized_against_the_ceiling` asserts the field ABSENT
# on them: requiring it universally would have written a provenance field that lies.
_Z_SIZED_AGAINST_THE_CEILING = ("SWEEP_POINTS", "CURVE_K", "N_CONTROL_SEEDS")

# Which artifact register entry backs each record-backed constant. The NAME of the register
# attribute, never the path — every Phase-23 path resolves from the module that declares it.
_Z_RECORD_BACKED = {
    "SWEEP_POINTS": "COST_RECORD",
    "CURVE_K": "COST_RECORD",
    "N_CONTROL_SEEDS": "NEVER_TAUGHT_TRAINING_RECORD",
    "N64_LEG_WITHDRAWN": "CAL03_WIRING_RECORD",
}

# The two constants whose source is a live SOURCE MODULE rather than a committed results artifact.
# Both carry `record_sha256: None` and `git_sha: None` by construction — see the else-branch of the
# provenance loop in `test_budget_constants_re_derive` for why that absence is asserted.
_Z_SOURCE_MODULE_BACKED = {
    "FULL_FIDELITY_K": "scripts/phase18_extraction.py",
    "STEP_BUDGET": "scripts/teach_persona.py",
}


def _cost_record():
    """The committed cost record, parsed. `_control_record`'s sibling, same resolution rule."""
    path = _ROOT / phase23_prereg.COST_RECORD
    return path, json.loads(path.read_text(encoding="utf-8"))


def _never_taught_record():
    """The never-taught TRAINING record — the binding source for `N_CONTROL_SEEDS`.

    Its seeds are the adapters 23-14 actually scores, and that constant exists to price THAT
    scoring. `results/phase23_control_floor.json` carries the same five seeds by D-08's same-N
    rule; the agreement is the REASON the lists match and is not a second source.
    """
    path = _ROOT / phase23_prereg.NEVER_TAUGHT_TRAINING_RECORD
    return path, json.loads(path.read_text(encoding="utf-8"))


def _cal03_record():
    """The committed CAL-03 wiring record — D-06's evidence, read LIVE rather than assumed."""
    path = _ROOT / phase23_prereg.CAL03_WIRING_RECORD
    return path, json.loads(path.read_text(encoding="utf-8"))


def _z_provenance(name):
    """The `_PROVENANCE` sibling of a Z constant. One reader, so no test spells the suffix twice."""
    return getattr(mitigation_budget, name + "_PROVENANCE")


def _resolve_derivation(name):
    """Resolve a Z constant's `derivation` to the LIVE object it names — never string-matched.

    Two shapes are in use and both are handled here: ``module.SYMBOL``, and
    ``module.SYMBOL -> key`` where the symbol is a record PATH in the artifact register and ``key``
    is the field read out of it. Resolving rather than matching is what makes `derivation` a
    CHECKED REFERENCE instead of decoration — a provenance that cites a symbol which does not exist
    fails here rather than reading plausibly forever.
    """
    symbol, _, key = _z_provenance(name)["derivation"].partition(" -> ")
    module_name, _, attribute = symbol.partition(".")
    resolved = getattr(importlib.import_module(module_name), attribute)
    if not key:
        return resolved
    return json.loads((_ROOT / resolved).read_text(encoding="utf-8"))[key]


def _withdrawal_implied_by(record):
    """D-06's branch, computed from a record through the BLIND rule rather than read off a field.

    ``phase23_prereg.n64_leg_is_committable`` was committed in 23-03 and is strictly ancestral to
    the wiring record's earliest add, so it could not have been written around the numbers it
    judges. It is NEVER a relative tolerance: ε and T must be bit-identical between the two arms.
    """
    return not phase23_prereg.n64_leg_is_committable(
        epsilon_n8=record["epsilon_n8"],
        epsilon_n64=record["epsilon_n64"],
        t_n8=record["t_n8"],
        t_n64=record["t_n64"],
    )


def _module_level_constant_names():
    """`scripts/mitigation_budget.py`'s module-level assignment targets, BY AST.

    Never by grep, for the reason recorded at the top of this section: one constant name contains
    another as a substring, and this file's prose names all of them.
    """
    tree = ast.parse(_MITIGATION_BUDGET_PATH.read_text(encoding="utf-8"))
    assigns = [node for node in tree.body if isinstance(node, ast.Assign)]
    return [target.id for node in assigns for target in node.targets]


def test_budget_holds_only_literal_constants():
    """``scripts/mitigation_budget.py`` holds LITERAL ASSIGNMENTS AND NOTHING ELSE.

    ``tests/test_phase19_erasure.py::test_floor_lock_holds_only_literal_constants_and_nothing_else``
    is the model, and the property keeps two separate promises here. The RULE stays in
    ``scripts/phase23_prereg.py``, where the edit-once ancestry guard watches it, so a sanctioned
    post-artifact write cannot smuggle a rule change in beside a constant. And a file with no
    expressions in it cannot need an import, which is what satisfies the zero-headroom
    ``mitigation_*.py`` ceiling recorded at the top of this file WITHOUT anyone having to remember
    the ceiling exists.

    The meta-guard is ``test_accountant_imports_math_only``'s: a walk that silently stopped working
    would find no offending node and pass while proving nothing, so the assignments it DID find are
    asserted non-empty.
    """
    source = _MITIGATION_BUDGET_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    head, *rest = tree.body
    assert isinstance(head, ast.Expr) and isinstance(head.value, ast.Constant), (
        f"{_MITIGATION_BUDGET_REL} opens with something other than its module docstring — that "
        "docstring is where the zero-import ceiling and the protected-but-not-frozen status are "
        "justified, and it may not be displaced"
    )

    assigns = []
    for node in rest:
        assert isinstance(node, ast.Assign), (
            f"{_MITIGATION_BUDGET_REL} carries a {type(node).__name__} at line {node.lineno}. This "
            "file holds measured constants and nothing else: the rules live in "
            "`scripts/phase23_prereg.py`, which is EDIT-ONCE, and moving one here would put it "
            "outside the ancestry guard that binds it to the measurements it decides"
        )
        ast.literal_eval(node.value)  # raises on anything that is not a literal
        assigns.append(node)

    forbidden = (
        ast.Import,
        ast.ImportFrom,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.If,
        ast.For,
        ast.While,
        ast.With,
        ast.Try,
    )
    offenders = [
        f"{type(node).__name__} at line {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, forbidden)
    ]
    assert offenders == [], (
        f"{_MITIGATION_BUDGET_REL} carries {offenders}. An `import` — ANY import, including "
        "`json`, `math` and `mitigation_gate` — turns "
        "`test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` RED, because the "
        "union across every `scripts/mitigation_*.py` is ALREADY exactly the allow-set and the "
        "ceiling has zero headroom. A function or a branch is the other half of the refusal: it "
        "would be a rule sitting beside a constant, outside the edit-once module"
    )

    assert assigns, (
        f"the walk over {_MITIGATION_BUDGET_REL} found ZERO assignments. Every assertion above "
        "passed over an empty set, so this test is green and blind at once — the meta-guard "
        "`test_accountant_imports_math_only` carries, for the same reason"
    )


def test_budget_constants_re_derive():
    """Every pinned constant RE-DERIVES from its artifact, through the BLIND rule, under `==`.

    This is the property that lets a measured number live outside the closed pre-registration at
    all. **A hand-edited number goes red here** — `test_a_hand_edited_floor_is_detected` below
    watches a one-ULP nudge being refused rather than merely asserting it would be.

    **THE REDUCTION IS NEVER READ BACK OUT OF THE ARTIFACT AS A PRE-REDUCED SCALAR.** The floor is
    recomputed by CALLING `phase23_prereg.noise_floor` on the record's own per-seed counts, because
    a reduction chosen in the artifact writer is a reduction chosen with the numbers already
    visible. The record's own `floor` field is cross-checked against that recomputation — as
    evidence that 23-08's writer called the blind rule too, never as the source of the pin.
    """
    path, record = _control_record()
    readings = _control_readings(record)

    for entry, reading in zip(record["per_seed"], readings, strict=True):
        assert reading == entry["primary"]["rate"], (
            f"control seed {entry['seed']} records rate {entry['primary']['rate']!r} but its own "
            f"counts {entry['primary']['k']}/{entry['primary']['n']} divide to {reading!r}. The "
            "stored rate has drifted from the evidence it summarises"
        )

    re_derived = phase23_prereg.noise_floor(readings)
    assert mitigation_budget.CONTROL_NOISE_FLOOR == re_derived, (
        f"{_MITIGATION_BUDGET_REL} pins CONTROL_NOISE_FLOOR = "
        f"{mitigation_budget.CONTROL_NOISE_FLOOR!r}, but phase23_prereg.noise_floor on the "
        f"{len(readings)} per-seed counts committed in {phase23_prereg.CONTROL_FLOOR_RECORD} "
        f"re-derives {re_derived!r}. Exact `==`, so a hand-edited number cannot reach a consumer"
    )
    assert record["floor"] == re_derived, (
        f"the record's own `floor` field is {record['floor']!r} but the blind reduction over its "
        f"own per-seed counts returns {re_derived!r} — the writer did not call the pinned rule"
    )

    provenance = mitigation_budget.CONTROL_NOISE_FLOOR_PROVENANCE
    assert set(provenance) >= set(phase23_prereg.FLOOR_PROVENANCE_KEYS), (
        f"the provenance dict is missing "
        f"{sorted(set(phase23_prereg.FLOOR_PROVENANCE_KEYS) - set(provenance))}. "
        "`sigma_zero_verdict` REFUSES a floor whose artifact, commit, device, seeds, reduction or "
        "scope is unstated, so 23-10 could not reach a verdict with this dict"
    )
    for key in ("record", "record_sha256", "git_sha", "device", "torch_version", "governs"):
        assert provenance[key] == record[key], (
            f"the provenance dict records {key} = {provenance[key]!r} but "
            f"{phase23_prereg.CONTROL_FLOOR_RECORD} records {record[key]!r}. A restated field with "
            "no test agreeing it is a copy waiting to drift"
        )
    assert provenance["seeds"] == tuple(record["seeds"]), (
        f"the provenance names seeds {provenance['seeds']!r}, the record {record['seeds']!r}"
    )
    assert provenance["record"] == phase23_prereg.CONTROL_FLOOR_RECORD, (
        f"the provenance names {provenance['record']!r} but the edit-once artifact register "
        f"declares {phase23_prereg.CONTROL_FLOOR_RECORD!r}. Every Phase-23 path resolves from that "
        "register — this repository has shipped plans naming paths the code refuses"
    )

    # The RECORD's `record_sha256` is an INPUTS digest (`sha256` over `per_seed`,
    # `scripts/phase23_run.py:967-969`) and is asserted above against the record's own field. It is
    # NOT the artifact's hash and could not be — a file cannot contain its own digest. The digest
    # that pins the committed BYTES is checked here, live.
    assert provenance["record_file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest(), (
        f"the provenance pins record_file_sha256 = {provenance['record_file_sha256']!r} but "
        f"{phase23_prereg.CONTROL_FLOOR_RECORD} hashes to "
        f"{hashlib.sha256(path.read_bytes()).hexdigest()!r} today — the artifact these constants "
        "were derived from is not the artifact on disk"
    )

    # `reduction` names a SYMBOL and never a formula. Resolved rather than string-matched, so the
    # name is a checked reference instead of decoration.
    module_name, _, attribute = provenance["reduction"].partition(".")
    assert module_name == phase23_prereg.__name__, (
        f"the reduction {provenance['reduction']!r} names module {module_name!r}, not "
        f"{phase23_prereg.__name__!r}"
    )
    assert getattr(phase23_prereg, attribute) is phase23_prereg.noise_floor, (
        f"the reduction {provenance['reduction']!r} does not resolve to the function this test "
        "re-derived the floor through — the pin cites a rule other than the one that produced it"
    )

    # THE WHOLE PAIR, THROUGH THE CONSUMER THAT WILL ACTUALLY READ IT IN 23-10. The σ=0 reading here
    # is SYNTHETIC — it is the control's own central reading, so the deviation is exactly zero. No
    # σ=0 measurement exists at this commit and this asserts nothing about what 23-10 will find; it
    # proves only that the pinned floor and its provenance are ACCEPTED rather than refused.
    verdict = phase23_prereg.sigma_zero_verdict(
        control_readings=readings,
        sigma_zero_reading=readings[0],
        floor=mitigation_budget.CONTROL_NOISE_FLOOR,
        floor_provenance=provenance,
    )
    assert verdict == "proceed", (
        f"the pinned floor and its provenance reached {verdict!r} against a zero deviation — 23-10 "
        "could not use this pin at all"
    )

    # =============================================================================================
    # EXTENDED 2026-08-28 (plan 23-13): THE Z CONSTANTS.
    #
    # The floor cases above belong to 23-09 and 23-18 and are UNTOUCHED. Same property applied a
    # third time, to every Z constant: recomputed from its CITED record through its CITED
    # derivation symbol, under exact `==`. A constant whose provenance names a record it cannot be
    # recomputed from is a number nobody can check.
    # =============================================================================================
    cost_path, cost = _cost_record()
    generation = cost["generation"]
    committed = cost["sizing"][str(mitigation_budget.CURVE_K)]

    # SWEEP_POINTS AND CURVE_K TOGETHER. `size_sweep` called with the PINNED PAIR must reproduce
    # the committed `sizing` block for that rung KEY FOR KEY under exact `==`. That is what makes
    # the pair checkable rather than self-agreeing: a perturbed width or a perturbed rung
    # reproduces a DIFFERENT block, which `test_a_z_constant_that_does_not_re_derive_is_detected`
    # watches happening rather than asserting would happen.
    live = phase23_cost.size_sweep(
        generation_record=generation,
        sweep_points=mitigation_budget.SWEEP_POINTS,
        k=mitigation_budget.CURVE_K,
    )
    assert live == {key: committed[key] for key in live}, (
        f"`phase23_cost.size_sweep` at the pinned pair (SWEEP_POINTS = "
        f"{mitigation_budget.SWEEP_POINTS!r}, CURVE_K = {mitigation_budget.CURVE_K!r}) returns "
        f"{live!r}, but {phase23_prereg.COST_RECORD}'s committed sizing block for that rung is "
        f"{ {key: committed[key] for key in live}!r}. The pinned Z does not re-derive from the "
        "record its provenance names"
    )

    # THE WIDTH IS ALSO AN INDEPENDENT FIELD, written by 23-11 BEFORE any rung was selected. The
    # block comparison above passes the width in, so on its own it could agree with itself; this is
    # what pins it to a number the record already carried.
    assert mitigation_budget.SWEEP_POINTS == cost["sweep_points_priced"], (
        f"SWEEP_POINTS is {mitigation_budget.SWEEP_POINTS!r} but {phase23_prereg.COST_RECORD} "
        f"priced {cost['sweep_points_priced']!r} points (its `sweep_points_source` names "
        f"{cost['sweep_points_source']!r}). The pin and the sizing describe different sweeps"
    )
    assert mitigation_budget.CURVE_K in cost["k_rungs"], (
        f"CURVE_K is {mitigation_budget.CURVE_K!r}, which is not among the rungs "
        f"{cost['k_rungs']!r} the cost record costed. A rung with no h/point beside it in the "
        "record is a budget nobody priced"
    )

    # THE THREE RULE-CONSTANTS, EACH RESOLVED THROUGH THE SYMBOL ITS PROVENANCE NAMES — never
    # string-matched, so a `derivation` field is a checked reference instead of decoration.
    for name, expected in (
        ("FULL_FIDELITY_K", _resolve_derivation("FULL_FIDELITY_K")),
        ("STEP_BUDGET", _resolve_derivation("STEP_BUDGET")),
    ):
        assert getattr(mitigation_budget, name) == expected, (
            f"{_MITIGATION_BUDGET_REL} pins {name} = {getattr(mitigation_budget, name)!r} but "
            f"{_z_provenance(name)['derivation']} resolves to {expected!r} today. This module has "
            "no import budget, so the value is a RESTATEMENT — and a restatement with no test "
            "agreeing it is a copy waiting to drift"
        )

    never_taught_path, never_taught = _never_taught_record()
    assert mitigation_budget.N_CONTROL_SEEDS == _resolve_derivation("N_CONTROL_SEEDS"), (
        f"N_CONTROL_SEEDS is {mitigation_budget.N_CONTROL_SEEDS!r} but "
        f"{phase23_prereg.NEVER_TAUGHT_TRAINING_RECORD} records n_seeds = "
        f"{never_taught['n_seeds']!r}. That record is the BINDING one: its seeds are the adapters "
        "23-14 actually scores, and this constant exists to price THAT scoring"
    )

    _cal03_path, wiring = _cal03_record()
    assert mitigation_budget.N64_LEG_WITHDRAWN is _withdrawal_implied_by(wiring), (
        f"N64_LEG_WITHDRAWN is {mitigation_budget.N64_LEG_WITHDRAWN!r} but "
        f"{phase23_prereg.CAL03_WIRING_RECORD} read live through "
        f"`phase23_prereg.n64_leg_is_committable` implies "
        f"{_withdrawal_implied_by(wiring)!r}. The pinned branch and the measurement disagree"
    )

    # THE SHARED PROVENANCE SHAPE, over every Z constant at once. `record` resolves from the path
    # REGISTER rather than matching a string (this repository has shipped plans naming paths the
    # code refuses), `record_sha256` is checked LIVE against the committed bytes, and `git_sha`
    # against the record's own field.
    for name in _Z_CONSTANTS:
        provenance = _z_provenance(name)
        for key in ("record", "record_sha256", "git_sha", "derivation", "governs"):
            assert key in provenance, (
                f"{name}_PROVENANCE is missing {key!r}. An unlabelled number is indistinguishable "
                "from a borrowed one, which is the defect D-06 corrected for v4.0"
            )
        assert isinstance(provenance["governs"], str) and provenance["governs"], (
            f"{name}_PROVENANCE's `governs` is {provenance['governs']!r} — a scope that states "
            "nothing is a scope a reader cannot check the constant against"
        )

        if name in _Z_RECORD_BACKED:
            record_path = _ROOT / getattr(phase23_prereg, _Z_RECORD_BACKED[name])
            backing = json.loads(record_path.read_text(encoding="utf-8"))
            assert provenance["record"] == getattr(phase23_prereg, _Z_RECORD_BACKED[name]), (
                f"{name}_PROVENANCE names record {provenance['record']!r} but the edit-once "
                f"artifact register declares "
                f"{getattr(phase23_prereg, _Z_RECORD_BACKED[name])!r}"
            )
            # UNLIKE THE TWO FLOORS ABOVE, this `record_sha256` is the FILE-BYTES digest: none of
            # the three records the Z constants cite carries an inputs digest of its own. The Z
            # banner in `scripts/mitigation_budget.py` says so once; this is what asserts it.
            live_digest = hashlib.sha256(record_path.read_bytes()).hexdigest()
            assert provenance["record_sha256"] == live_digest, (
                f"{name}_PROVENANCE pins record_sha256 = {provenance['record_sha256']!r} but "
                f"{provenance['record']} hashes to {live_digest!r} today — the artifact this "
                "constant was derived from is not the artifact on disk"
            )
            assert provenance["git_sha"] == backing["git_sha"], (
                f"{name}_PROVENANCE records git_sha = {provenance['git_sha']!r} but "
                f"{provenance['record']} records {backing['git_sha']!r}"
            )
        else:
            # THE TWO SOURCE-MODULE-BACKED CONSTANTS carry None for both digests BY CONSTRUCTION,
            # and the absence is asserted rather than tolerated: their source is a live source
            # module this phase does not freeze, so a digest pinned here would go stale on any
            # unrelated edit while asserting nothing. `_resolve_derivation` is the real check.
            assert provenance["record"] == _Z_SOURCE_MODULE_BACKED[name], (
                f"{name}_PROVENANCE names record {provenance['record']!r}, not the source module "
                f"{_Z_SOURCE_MODULE_BACKED[name]!r} its derivation symbol lives in"
            )
            assert provenance["record_sha256"] is None and provenance["git_sha"] is None, (
                f"{name}_PROVENANCE pins record_sha256 = {provenance['record_sha256']!r} and "
                f"git_sha = {provenance['git_sha']!r} against a live SOURCE MODULE. A digest over "
                "a file this phase does not freeze goes stale on an unrelated edit and asserts "
                "nothing; the sanctioned check is resolving the symbol, which this test does"
            )

    assert cost_path.exists() and never_taught_path.exists(), (
        "a Z record resolved to a path that does not exist — every assertion above ran against "
        "something other than the committed artifacts"
    )


def test_the_budget_module_is_protected_but_not_frozen():
    """The distinction `tests/test_phase20_prereg.py:94-108` calls deliberate, made CHECKABLE.

    PROTECTED: being named `mitigation_*.py` puts this module in `_GATE_MODULES`, so the import
    ceiling and the rule/emission split police it. NOT FROZEN: only a hand-written explicit path
    reaching `_assert_ordering_holds` as a `prereg_artifact=` confers a freeze, and that act is
    irrevocable from the first matching artifact.

    Both halves are asserted because both can fail, and the second failure is the expensive one: a
    future phase that freezes this file by accident would forbid 23-13 from ever writing the Z
    values, with no recovery path. That consequence is stated in the module docstring; this is what
    makes it a property.
    """
    assert _MITIGATION_BUDGET_PATH in _GATE_MODULES, (
        f"{_MITIGATION_BUDGET_REL} is NOT in the mitigation_*.py register "
        f"{[p.name for p in _GATE_MODULES]}. The glob exists precisely so this file could not sit "
        "silently uncovered until someone remembered to add it — unprotected, the one guard that "
        "must never be forgotten is the one forbidding the gate from importing it"
    )

    import test_phase20_prereg

    pinned = set()
    tree = ast.parse(_PHASE20_PREREG_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "prereg_artifact":
                continue
            if isinstance(keyword.value, ast.Constant):
                pinned.add(keyword.value.value)
            elif isinstance(keyword.value, ast.Name):
                pinned.add(getattr(test_phase20_prereg, keyword.value.id))
            else:
                raise AssertionError(
                    f"a `prereg_artifact=` at line {keyword.value.lineno} is a "
                    f"{type(keyword.value).__name__}, which this census cannot resolve. Failing "
                    "loudly rather than skipping it: a census that silently drops a form it does "
                    "not understand would report this module unfrozen while it was frozen"
                )

    # NON-VACUITY. An empty or collapsed census would report every module unfrozen, including a
    # frozen one — so the three pins that ARE frozen have to show up first.
    assert {"scripts/mitigation_gate.py"} <= pinned and len(pinned) >= 3, (
        f"the `prereg_artifact=` census found {sorted(pinned)}, which does not include the three "
        "known pins. The matcher is broken and the assertion below proves nothing"
    )

    assert _MITIGATION_BUDGET_REL not in pinned, (
        f"{_MITIGATION_BUDGET_REL} is registered as a `prereg_artifact=` in "
        f"{sorted(pinned)} — it is now FROZEN, and the freeze is irrevocable from the first "
        "matching artifact. 23-13 must still write the Z values into this file after 23-11 "
        "measures the per-point cost, and a frozen file cannot receive them. This is the one "
        "middle ground D-03 needs: protected, not frozen"
    )


def test_the_import_ceiling_still_has_zero_headroom():
    """The ceiling block above, RE-MEASURED — with a real `mitigation_budget.py` in the glob.

    NOT a copy of `test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only`: that guard
    asserts a SUBSET, and this one asserts EQUALITY. The difference is the whole point. A subset
    stays green while the union shrinks or while an import lands that happens to already be in the
    allow-set; equality is what makes the ZERO HEADROOM recorded at the top of this file a measured
    property rather than a dated observation, and it goes red on either movement.

    The allow-set is restated as a literal here, and that restatement is safe for a reason worth
    naming: if the committed guard's allow-set ever widens, THIS equality goes red and names the
    new union. Divergence between the two sets is loud, not silent.

    RE-MEASURED 2026-08-27 (plan 23-18), and the assertion below is UNCHANGED. 23-18 added TWO
    constants to `scripts/mitigation_budget.py` — `MATCHED_CONTROL_NOISE_FLOOR` and its provenance
    sibling — and ZERO imports, because the new pin is literal assignments and comments only. The
    measured union is still exactly `{erasure_gate, pathlib, sys}`, so the ceiling still has zero
    headroom after the first phase to write to this module since 23-09 created it. That is the
    point of asserting equality rather than subset: a purely additive edit that DID sneak an import
    in would be caught here even though the subset guard's allow-set never moved.
    """
    assert _MITIGATION_BUDGET_PATH in _GATE_MODULES and len(_GATE_MODULES) >= 4, (
        f"the register is {[p.name for p in _GATE_MODULES]} — the union below would be measured "
        "over a set that does not contain the module this plan added"
    )

    imported = set()
    for module in _GATE_MODULES:
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])

    assert imported == {"erasure_gate", "pathlib", "sys"}, (
        f"the measured import union across {[p.name for p in _GATE_MODULES]} is "
        f"{sorted(imported)}, not the allow-set `test_mitigation_gate_import_graph_is_stdlib_and_"
        f"erasure_gate_only` asserts. If it GREW, that guard is already red and a "
        "`scripts/mitigation_*.py` module imported something. If it SHRANK, the ceiling now has "
        "headroom the ceiling block at the top of this file says it does not, and a future sibling "
        "would be told it has an import budget it must not use"
    )


def test_a_hand_edited_floor_is_detected(tmp_path):
    """WATCHED RED, PERMANENTLY: a ONE-ULP nudge to the pinned floor is observed being refused.

    A guard nobody has watched fail is not evidence. Phase 20 MEASURED this exact case defeating a
    float comparison at GATE-02, so it is the concrete nudge rather than a hypothetical one. Here
    the floor is compared against a value RECOMPUTED from the committed counts under exact `==`, so
    the nudge is refused by CONSTRUCTION rather than by magnitude — and this test is what proves
    that rather than asserting it.

    Built under `tmp_path` so it is permanent: a watched RED that re-runs on every suite run is
    strictly better evidence than one performed once by hand and written up.
    """
    _path, record = _control_record()
    readings = _control_readings(record)
    original = mitigation_budget.CONTROL_NOISE_FLOOR
    nudged = math.nextafter(original, math.inf)
    assert nudged != original, "math.nextafter returned the same float — there is no nudge to make"

    source = _MITIGATION_BUDGET_PATH.read_text(encoding="utf-8")
    needle = f"CONTROL_NOISE_FLOOR = {original!r}"
    assert source.count(needle) == 1, (
        f"{_MITIGATION_BUDGET_REL} contains {source.count(needle)} occurrences of {needle!r}. The "
        "edit below would land somewhere other than the pinned assignment, or nowhere at all"
    )
    copy = tmp_path / "mitigation_budget.py"
    copy.write_text(source.replace(needle, f"CONTROL_NOISE_FLOOR = {nudged!r}"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("nudged_budget", copy)
    edited = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edited)

    # META-GUARD, before any verdict is read off it: prove the nudged copy actually LOADED and
    # actually carries the nudged value. A copy that failed to import, or one whose replacement
    # missed, would fail every assertion below for a reason that has nothing to do with detection.
    assert edited.CONTROL_NOISE_FLOOR == nudged, (
        f"the scratch copy loaded with CONTROL_NOISE_FLOOR = {edited.CONTROL_NOISE_FLOOR!r}, not "
        f"the nudged {nudged!r} — this test is not observing what it claims to observe"
    )

    re_derived = phase23_prereg.noise_floor(readings)
    assert original == re_derived and edited.CONTROL_NOISE_FLOOR != re_derived, (
        f"the committed floor {original!r} and the nudged one {edited.CONTROL_NOISE_FLOOR!r} both "
        f"compare the same way against the re-derived {re_derived!r} — `test_budget_constants_"
        "re_derive` would stay GREEN against a hand-edited number"
    )

    with pytest.raises(SystemExit) as halt:
        phase23_prereg.sigma_zero_verdict(
            control_readings=readings,
            sigma_zero_reading=readings[0],
            floor=edited.CONTROL_NOISE_FLOOR,
            floor_provenance=edited.CONTROL_NOISE_FLOOR_PROVENANCE,
        )
    assert "re-derives" in str(halt.value), (
        f"the nudged floor was refused, but not by the re-derivation check — the halt says "
        f"{str(halt.value)!r}. A refusal for some other reason would leave the ULP case unproven"
    )


# =================================================================================================
# ===== PLAN 23-18: THE PROTOCOL-MATCHED FLOOR, PINNED BESIDE THE ORIGINAL =====
#
# The original above is NOT edited and NOT deleted. It correctly measures the OLD control protocol
# and still re-derives from its own record on every run; what changed is its SCOPE. So the three
# properties `scripts/phase19_floor.py` carries are applied a SECOND time, to the matched pin, and
# two further guards protect the ORIGINAL from the act of adding one beside it.
# =================================================================================================


def test_matched_floor_re_derives():
    """The MATCHED floor RE-DERIVES from its artifact, through the BLIND rule, under exact `==`.

    `test_budget_constants_re_derive`'s sibling, in the same order, for the same reason: this is
    the property that lets a measured number live outside the closed pre-registration at all.

    **THE REDUCTION IS NEVER READ BACK OUT OF THE ARTIFACT AS A PRE-REDUCED SCALAR.** The floor is
    recomputed by CALLING `phase23_prereg.noise_floor` — the function committed BLIND in 23-03 at
    `c7de5d4` and byte-unchanged since — on the record's own per-seed counts. The record's own
    `floor` field is cross-checked against that recomputation LAST, as evidence that 23-17's writer
    called the blind rule too, and never as the source of the pin.
    """
    _path, record = _matched_record()
    readings = _matched_readings(record)

    for entry, reading in zip(record["per_seed"], readings, strict=True):
        assert reading == entry["primary"]["rate"], (
            f"matched seed {entry['seed']} records rate {entry['primary']['rate']!r} but its own "
            f"counts {entry['primary']['k']}/{entry['primary']['n']} divide to {reading!r}. The "
            "stored rate has drifted from the evidence it summarises"
        )

    re_derived = phase23_prereg.noise_floor(readings)
    assert mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR == re_derived, (
        f"{_MITIGATION_BUDGET_REL} pins MATCHED_CONTROL_NOISE_FLOOR = "
        f"{mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR!r}, but phase23_prereg.noise_floor on the "
        f"{len(readings)} per-seed counts committed in "
        f"{phase23_matched_prereg.MATCHED_CONTROL_RECORD} re-derives {re_derived!r}. Exact `==`, "
        "so a hand-edited number cannot reach 23-19's verdict"
    )
    assert record["floor"] == re_derived, (
        f"the matched record's own `floor` field is {record['floor']!r} but the blind reduction "
        f"over its own per-seed counts returns {re_derived!r} — the writer did not call the pinned "
        "rule"
    )

    # THE TWO FLOORS ARE DIFFERENT NUMBERS, and that is worth asserting rather than assuming. If a
    # future edit ever made them equal, `MATCHED_CONTROL_NOISE_FLOOR = <repr>` would CONTAIN the
    # original's needle as a substring and `test_a_hand_edited_floor_is_detected` would go red for
    # a reason that has nothing to do with a hand edit. `test_the_original_needle_is_still_unique`
    # is what actually catches that; this names the mechanism where a reader will meet it.
    assert mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR != mitigation_budget.CONTROL_NOISE_FLOOR, (
        "the matched and original floors are now the SAME float, so the matched assignment line "
        "contains the original's needle as a substring. The sanctioned repair is to line-anchor "
        "`test_a_hand_edited_floor_is_detected`'s needle (a tightening), NOT to rename the "
        "constant, round the value or weaken the guard"
    )


def test_matched_floor_provenance_is_complete():
    """The matched provenance carries everything `sigma_zero_verdict` REFUSES a floor for lacking.

    23-19 passes this dict straight into `phase23_prereg.sigma_zero_verdict`, which refuses a floor
    whose artifact, commit, device, seeds, reduction or scope is unstated. A missing key would
    surface for the first time in 23-19, against a comparator that already cost two GPU sessions.

    Every restated field is asserted against the record it was copied from: a restatement with no
    test agreeing it is a copy waiting to drift.
    """
    path, record = _matched_record()
    provenance = mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE

    assert set(provenance) >= set(phase23_prereg.FLOOR_PROVENANCE_KEYS), (
        f"the matched provenance is missing "
        f"{sorted(set(phase23_prereg.FLOOR_PROVENANCE_KEYS) - set(provenance))} — 23-19 could not "
        "reach a verdict with this dict"
    )
    for key in ("record", "record_sha256", "git_sha", "device", "torch_version", "governs"):
        assert provenance[key] == record[key], (
            f"the matched provenance records {key} = {provenance[key]!r} but "
            f"{phase23_matched_prereg.MATCHED_CONTROL_RECORD} records {record[key]!r}"
        )
    assert provenance["seeds"] == tuple(record["seeds"]), (
        f"the matched provenance names seeds {provenance['seeds']!r}, the record "
        f"{record['seeds']!r}. Both must be LADDER order (1337, 2024, 1338, 2025, 1339) and never "
        "sorted order — `control_readings[0]` indexes this ordering"
    )
    assert isinstance(provenance["seeds"], tuple), (
        f"the matched provenance's `seeds` is a {type(provenance['seeds']).__name__}, not a tuple. "
        "The original's is a tuple, this file holds literal constants, and a mutable default in a "
        "pinned provenance is a value a consumer could edit in place"
    )
    assert provenance["record"] == phase23_matched_prereg.MATCHED_CONTROL_RECORD, (
        f"the matched provenance names {provenance['record']!r} but the pin declares "
        f"{phase23_matched_prereg.MATCHED_CONTROL_RECORD!r}"
    )

    # The INPUTS digest (the record's own field, asserted above) and the FILE digest are different
    # things — the same distinction spelled out at the original constant. This is the one that pins
    # the committed BYTES, and it is checked live.
    assert provenance["record_file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest(), (
        f"the matched provenance pins record_file_sha256 = {provenance['record_file_sha256']!r} "
        f"but {phase23_matched_prereg.MATCHED_CONTROL_RECORD} hashes to "
        f"{hashlib.sha256(path.read_bytes()).hexdigest()!r} today — the artifact this floor was "
        "derived from is not the artifact on disk"
    )

    # `reduction` names a SYMBOL, resolved rather than string-matched, so the pin cannot cite a
    # rule other than the one that produced it.
    assert provenance["reduction"] == "phase23_prereg.noise_floor", (
        f"the matched provenance names reduction {provenance['reduction']!r}"
    )
    module_name, _, attribute = provenance["reduction"].partition(".")
    assert module_name == phase23_prereg.__name__, (
        f"the reduction names module {module_name!r}, not {phase23_prereg.__name__!r}"
    )
    assert getattr(phase23_prereg, attribute) is phase23_prereg.noise_floor, (
        f"the reduction {provenance['reduction']!r} does not resolve to the function "
        "`test_matched_floor_re_derives` re-derives the floor through"
    )

    # THE DISCLOSURE, carried as DATA rather than only as prose. This pin's ordering claim is
    # strictly weaker than the original's — the σ=0 reading was already committed when the
    # comparator's protocol was designed — and a consumer that reads only the dict has to be able
    # to learn that.
    assert provenance["sigma_zero_was_visible"] is True, (
        "the matched provenance does not declare `sigma_zero_was_visible: True`. It WAS visible "
        "(results/phase23_sigma_zero.json was committed before the matched protocol existed), and "
        "a pin that omits the disclosure claims an ordering it does not have"
    )
    assert provenance["sigma_zero_was_visible"] is record["sigma_zero_was_visible"], (
        "the matched provenance and its record disagree about σ=0 visibility"
    )
    assert provenance["protocol"] == "phase23_matched_prereg", (
        f"the matched provenance names protocol {provenance['protocol']!r}, so a reader cannot "
        "resolve which pin the comparator arm was run under"
    )

    # THROUGH THE CONSUMER THAT WILL ACTUALLY READ IT IN 23-19. The σ=0 reading passed here is
    # SYNTHETIC — the matched arm's own central reading, so the deviation is exactly zero. This
    # asserts NOTHING about the verdict 23-19 will reach; it proves only that the pinned floor and
    # its provenance are ACCEPTED rather than refused, and that the three extra keys do not offend
    # the frozen consumer.
    readings = _matched_readings(record)
    verdict = phase23_prereg.sigma_zero_verdict(
        control_readings=readings,
        sigma_zero_reading=readings[0],
        floor=mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR,
        floor_provenance=provenance,
    )
    assert verdict == "proceed", (
        f"the matched floor and its provenance reached {verdict!r} against a zero deviation — "
        "23-19 could not use this pin at all"
    )


def test_a_hand_edited_matched_floor_is_detected(tmp_path):
    """WATCHED RED, PERMANENTLY: a ONE-ULP nudge to the MATCHED floor is observed being refused.

    `test_a_hand_edited_floor_is_detected`'s sibling. A guard nobody has watched fail is not
    evidence, and Phase 20 MEASURED this exact case defeating a float comparison at GATE-02, so it
    is the concrete nudge rather than a hypothetical one. `math.nextafter` is called HERE, in the
    test — never in the module, which holds literal assignments and has no import budget to call it
    with.

    THE NEEDLE IS LINE-ANCHORED FROM THE START, unlike the original's. A bare
    `"MATCHED_CONTROL_NOISE_FLOOR = <repr>"` would be reachable by any longer identifier ending in
    that name, which is exactly the substring trap the original's needle fell into the moment this
    constant was added beside it. The leading newline makes it match only a line-initial assignment
    — and it is carried into the REPLACEMENT too, or the edit would silently swallow a line break
    and the scratch copy would stop being a faithful copy of the module.
    """
    _path, record = _matched_record()
    readings = _matched_readings(record)
    original = mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR
    nudged = math.nextafter(original, math.inf)
    assert nudged != original, "math.nextafter returned the same float — there is no nudge to make"

    source = _MITIGATION_BUDGET_PATH.read_text(encoding="utf-8")
    needle = f"\nMATCHED_CONTROL_NOISE_FLOOR = {original!r}"
    assert source.count(needle) == 1, (
        f"{_MITIGATION_BUDGET_REL} contains {source.count(needle)} occurrences of {needle!r}. The "
        "edit below would land somewhere other than the pinned assignment, or nowhere at all"
    )
    copy = tmp_path / "mitigation_budget.py"
    copy.write_text(
        source.replace(needle, f"\nMATCHED_CONTROL_NOISE_FLOOR = {nudged!r}"), encoding="utf-8"
    )

    spec = importlib.util.spec_from_file_location("nudged_matched_budget", copy)
    edited = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edited)

    # META-GUARD, before any verdict is read off it. A copy that failed to import, or one whose
    # replacement missed, would fail every assertion below for a reason that has nothing to do with
    # detection. The second half is what proves the newline was carried: had it been dropped, the
    # ORIGINAL floor's assignment would have been welded onto the previous line and this module
    # would either not parse or not carry it.
    assert edited.MATCHED_CONTROL_NOISE_FLOOR == nudged, (
        f"the scratch copy loaded with MATCHED_CONTROL_NOISE_FLOOR = "
        f"{edited.MATCHED_CONTROL_NOISE_FLOOR!r}, not the nudged {nudged!r} — this test is not "
        "observing what it claims to observe"
    )
    assert edited.CONTROL_NOISE_FLOOR == mitigation_budget.CONTROL_NOISE_FLOOR, (
        "the scratch copy's ORIGINAL floor moved, so the line-anchored replacement did not leave "
        "the rest of the module byte-identical"
    )

    re_derived = phase23_prereg.noise_floor(readings)
    assert original == re_derived and edited.MATCHED_CONTROL_NOISE_FLOOR != re_derived, (
        f"the committed matched floor {original!r} and the nudged one "
        f"{edited.MATCHED_CONTROL_NOISE_FLOOR!r} both compare the same way against the re-derived "
        f"{re_derived!r} — `test_matched_floor_re_derives` would stay GREEN against a hand-edited "
        "number"
    )

    with pytest.raises(SystemExit) as halt:
        phase23_prereg.sigma_zero_verdict(
            control_readings=readings,
            sigma_zero_reading=readings[0],
            floor=edited.MATCHED_CONTROL_NOISE_FLOOR,
            floor_provenance=edited.MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE,
        )
    assert "re-derives" in str(halt.value), (
        f"the nudged matched floor was refused, but not by the re-derivation check — the halt says "
        f"{str(halt.value)!r}. A refusal for some other reason would leave the ULP case unproven"
    )


def test_the_original_floor_is_left_standing_and_re_scoped():
    """23-18 is an ADDITION, not a rewrite — the property `test_cost_claim_correction_is_additive`
    is built around in 23-12, applied to this module.

    The original floor is a CORRECT measurement of the OLD control protocol. It is not falsified by
    the matched comparator; it is RE-SCOPED. Deleting it would destroy a true reading AND break
    `test_budget_constants_re_derive`, which still recomputes it from
    `results/phase23_control_floor.json` on every run.

    So three things are asserted: the value is unmoved, the dated marker naming what re-scoped it is
    present, and two DISTINCTIVE SENTENCES of the ORIGINAL comment block survive BYTE-IDENTICALLY.
    The third is what stops a "continuation" quietly becoming a rewrite — a diff that deleted the
    original's reasoning and re-typed it in the new register would pass the first two.
    """
    assert mitigation_budget.CONTROL_NOISE_FLOOR == 0.05357142857142849, (
        f"the original floor is now {mitigation_budget.CONTROL_NOISE_FLOOR!r}. It measures the OLD "
        "control protocol correctly and 23-18 re-scopes it WITHOUT editing it; the matched floor "
        "lands BESIDE it as `MATCHED_CONTROL_NOISE_FLOOR`"
    )

    source = _MITIGATION_BUDGET_PATH.read_text(encoding="utf-8")
    marker = "RE-SCOPED IN PLACE 2026-08-27 (plan 23-18)."
    assert marker in source, (
        f"{_MITIGATION_BUDGET_REL} no longer carries {marker!r}. The original constant is still "
        "there, but nothing beside it now says WHICH protocol it governs — and a reader meeting "
        "two floors with no continuation cannot tell which one 23-19 consumes"
    )

    # Byte-identical substrings of the PRE-23-18 comment block. Chosen because neither phrase is
    # re-used anywhere in the appended continuation, so `count == 1` is a statement about the
    # ORIGINAL text surviving rather than about the new text avoiding it.
    for survivor in (
        "THE ORDERING IS A FACT ABOUT GIT, NOT AN INTENTION.",
        "when a Phase-12 full-fine-tune",
    ):
        assert source.count(survivor) == 1, (
            f"{_MITIGATION_BUDGET_REL} contains {source.count(survivor)} occurrences of "
            f"{survivor!r}, not 1. This sentence is part of the ORIGINAL floor's comment block. If "
            "it is GONE, the dated continuation became a rewrite and a true measurement's "
            "reasoning was deleted to make a later one look tidy. If it is DUPLICATED, the "
            "continuation re-typed the original instead of appending to it"
        )


def test_the_original_needle_is_still_unique():
    """`test_a_hand_edited_floor_is_detected`'s PRECONDITION, as its own named guard.

    That test builds `needle = f"CONTROL_NOISE_FLOOR = {original!r}"` and asserts
    `source.count(needle) == 1` before rewriting it under `tmp_path`. That assertion is buried
    inside another test, so a future editor meets it as a confusing failure rather than as a rule.
    Here it is a rule, with the two ways to break it named.

    ROUTE 1 — PROSE. A comment or docstring line that QUOTES the original's literal assignment. This
    is the natural thing to do when writing an evidence-rich continuation about the constant, and it
    is why 23-18's continuation refers to the constant BY NAME and writes its value, where a value
    is needed at all, with no `NAME = ` in front of it.

    ROUTE 2 — SUBSTRING. A longer identifier ENDING in `CONTROL_NOISE_FLOOR` whose value shares the
    original's `repr`. `MATCHED_CONTROL_NOISE_FLOOR = <repr>` CONTAINS the needle. 23-18's matched
    floor is `0.0267857142857143` against the original's `0.05357142857142849`, so no collision
    exists today — but the next constant added here could reintroduce one.

    THE SANCTIONED REPAIR FOR ROUTE 2 IS TO LINE-ANCHOR THE NEEDLE — prefix it with `\\n` so it
    matches only a line-initial assignment, and carry that `\\n` into the replacement too, or the
    edit swallows a line break. That is a TIGHTENING. It is NOT a rename, NOT a rounded value, and
    NOT a weakened guard.
    """
    source = _MITIGATION_BUDGET_PATH.read_text(encoding="utf-8")
    needle = f"CONTROL_NOISE_FLOOR = {mitigation_budget.CONTROL_NOISE_FLOOR!r}"
    count = source.count(needle)

    # NON-VACUITY. A needle that matched nothing would make the equality below fail loudly, but a
    # reader meeting `0 != 1` deserves to be told the pin itself has gone missing.
    assert count >= 1, (
        f"{_MITIGATION_BUDGET_REL} contains NO occurrence of {needle!r} — the original pin is gone "
        "or its value moved, which `test_the_original_floor_is_left_standing_and_re_scoped` covers"
    )
    assert count == 1, (
        f"{_MITIGATION_BUDGET_REL} contains {count} occurrences of {needle!r}, not 1, so "
        "`test_a_hand_edited_floor_is_detected` is now RED. Two routes produce this. (1) PROSE: a "
        "comment or docstring quoted the literal assignment — refer to the constant BY NAME "
        "instead, and write a bare value with no `NAME = ` prefix. (2) SUBSTRING: a longer "
        "identifier ending in CONTROL_NOISE_FLOOR (today, MATCHED_CONTROL_NOISE_FLOOR = "
        f"{mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR!r}) now shares the original's repr. The "
        "repair for (2) is to LINE-ANCHOR that test's needle with a leading newline, carried into "
        "the replacement as well — a tightening. NOT a rename, NOT a rounded value, NOT a weakened "
        "guard"
    )


# =================================================================================================
# ===== PLAN 23-13: Z — THE RATCHET, THE CEILING-SIZING, D-06's TWO BRANCHES, AND THE CONTROL =====
# =================================================================================================


def test_selected_k_is_a_ratcheted_rung():
    """The restated rungs and the FROZEN gate agree — checked by IMPORTING the gate, from here.

    `scripts/mitigation_budget.py` cannot import `scripts/mitigation_gate.py`: its literal-only
    guard refuses any module-level node that is not an `ast.Assign`, and two accumulated ceilings
    bind the same `scripts/mitigation_*.py` union with zero headroom in both directions. So the
    rungs are RESTATED there as literals, and a copy is free to stop matching — unless a test holds
    it. This is that test, and the frozen constants are IMPORTED rather than retyped: a second
    hand-typed `(48, 24, 16, 8)` here would be a second copy with the same failure mode.

    The two functions are CALLED rather than reasoned about. `ratchet_k` is what makes the
    selection one-way (`_prove(proposed_k >= fixed_k)`), and `promote_to_full_fidelity` is the rule
    that re-draws a gate candidate at the reserved fidelity — it calls `ratchet_k` itself, so a
    full-fidelity K below the curve K aborts through the same implementation D-19 committed.
    """
    curve_k = mitigation_budget.CURVE_K
    full_k = mitigation_budget.FULL_FIDELITY_K

    for name, value in (("CURVE_K", curve_k), ("FULL_FIDELITY_K", full_k)):
        assert value in mitigation_gate.K_RUNGS, (
            f"{_MITIGATION_BUDGET_REL} pins {name} = {value!r}, which is not a member of the "
            f"FROZEN closed menu mitigation_gate.K_RUNGS {mitigation_gate.K_RUNGS}. The menu was "
            "committed with its measured cost table, so an off-menu K is a draw budget with no "
            "h/point beside it and no rung to ratchet from"
        )

    assert mitigation_gate.ratchet_k(fixed_k=curve_k, proposed_k=full_k) == full_k, (
        f"the ratchet did not return the proposed rung for the pinned pair "
        f"({curve_k!r} -> {full_k!r})"
    )

    promote, reason = mitigation_gate.promote_to_full_fidelity(
        verdict="PASS", reasons=(), curve_k=curve_k, full_k=full_k
    )
    assert promote is True and str(full_k) in reason, (
        f"`promote_to_full_fidelity` refused the pinned pair or did not name the full-fidelity "
        f"rung in its reason: {(promote, reason)!r}. A curve K the promotion rule cannot promote "
        "FROM is a budget the gate cannot spend"
    )

    # THE RATCHET'S DIRECTION, OBSERVED RATHER THAN ASSERTED IN PROSE. This is the property that
    # made Task 1 a checkpoint rather than an executor choice, so it is watched firing here.
    cheaper = [rung for rung in mitigation_gate.K_RUNGS if rung < curve_k]
    assert cheaper, (
        f"CURVE_K = {curve_k!r} is the cheapest rung in {mitigation_gate.K_RUNGS}, so there is no "
        "decrease to watch being refused and the assertion below would prove nothing"
    )
    with pytest.raises(SystemExit):
        mitigation_gate.ratchet_k(fixed_k=curve_k, proposed_k=max(cheaper))


def test_the_step_budget_agrees_with_the_production_constant():
    """`STEP_BUDGET` is a RESTATEMENT of `teach_persona.MAX_STEPS`; this is its other half.

    The budget module has no import budget, so the value is retyped there beside a provenance
    comment naming the symbol. Without this assertion that restatement is an unchecked copy — the
    exact shape the sanctioned restate-and-assert route exists to close.

    `teach_persona` is imported HERE rather than at module scope: it is needed by one test and this
    file otherwise collects without touching the training stack.
    """
    import teach_persona

    assert mitigation_budget.STEP_BUDGET == teach_persona.MAX_STEPS, (
        f"{_MITIGATION_BUDGET_REL} pins STEP_BUDGET = {mitigation_budget.STEP_BUDGET!r} but "
        f"`teach_persona.MAX_STEPS` is {teach_persona.MAX_STEPS!r} today. Every Phase-23 arm ran "
        "at the production constant, so a drifted restatement would price a sweep nobody trains"
    )

    # The cost record's own training legs ran at that same budget. A third witness, from the
    # artifact side rather than the source side.
    _path, cost = _cost_record()
    for leg, block in cost["training"].items():
        assert block["max_steps"] == mitigation_budget.STEP_BUDGET, (
            f"{phase23_prereg.COST_RECORD}'s training leg {leg!r} ran at max_steps = "
            f"{block['max_steps']!r}, not the pinned STEP_BUDGET "
            f"{mitigation_budget.STEP_BUDGET!r}"
        )


def test_z_was_sized_against_the_ceiling():
    """Z is sized against `h_per_point_ceiling`, proved by RE-DERIVATION IDENTITY, not by a label.

    The ratchet has no cheap direction, so a sweep sized against the floor and found too expensive
    cannot be rescued. The label `sized_against` is carried by exactly the three multiplicands of
    the ceiling-side total and is asserted ABSENT on the three constants no throughput figure feeds
    — a provenance field that lies is worse than one that is missing.

    **THE INEQUALITY IS `>=`, NOT `>`, AND THAT IS DELIBERATE.** The reason the ceiling exists is
    that a noised adapter which stops emitting EOS runs every draw to the full token budget. In
    that regime no draw stop-terminates, the floor condition and the ceiling condition measure the
    same thing, and the two h/point figures are EQUAL — so a strict `>` would fail against a
    perfectly correct measurement. The discriminating check is the IDENTITY: the committed total
    re-derives from the ceiling field and not from the floor field, which holds in both regimes.

    **EQUALITY MUST BE EARNED.** If the two figures do come out equal, the record has to DISCLOSE
    the measurement that makes them equal — zero stop-terminated draws in the ceiling condition,
    and per-shape stop counts equal between the two conditions — so a degenerate bracket has to
    come from the measurement rather than from one field being copied into the other.
    """
    # THE REGISTER IS NON-VACUOUS AND COMPLETE, by AST rather than by grep. A seventh Z constant
    # added without being registered would otherwise be skipped by every loop in this file.
    discovered = [
        name
        for name in _module_level_constant_names()
        if not name.endswith("_PROVENANCE") and name not in _PRE_23_13_CONSTANTS
    ]
    assert tuple(discovered) == _Z_CONSTANTS, (
        f"the AST walk over {_MITIGATION_BUDGET_REL} finds Z constants {discovered!r} but this "
        f"file's register is {list(_Z_CONSTANTS)!r}. An unregistered constant is skipped by every "
        "loop here, so it would ship with no re-derivation and no provenance check"
    )

    for name in _Z_CONSTANTS:
        provenance = _z_provenance(name)
        if name in _Z_SIZED_AGAINST_THE_CEILING:
            assert provenance.get("sized_against") == "h_per_point_ceiling", (
                f"{name}_PROVENANCE carries sized_against = "
                f"{provenance.get('sized_against')!r}. It is a MULTIPLICAND of the ceiling-side "
                "total, so a floor-sized number could hide in it and the ratchet could not rescue "
                "the sweep afterwards"
            )
        else:
            assert "sized_against" not in provenance, (
                f"{name}_PROVENANCE carries sized_against = "
                f"{provenance['sized_against']!r}, but NO throughput figure participates in this "
                "constant — it is derived from "
                f"{provenance['derivation']!r}. The field would be FALSE here, and a provenance "
                "field that lies is worse than one that is absent"
            )

    _path, cost = _cost_record()
    generation = cost["generation"]
    committed = cost["sizing"][str(mitigation_budget.CURVE_K)]
    scale = committed["draws_per_point_at_k"] / generation["draws_per_point"]
    points = mitigation_budget.SWEEP_POINTS
    controls = mitigation_budget.N_CONTROL_SEEDS

    # THE IDENTITY. Both totals are formed the way the writer formed them — sweep term PLUS
    # never-taught term, never `(points + controls) * h`, because float addition is not
    # associative and the committed number is the first form.
    ceiling_at_k = generation["h_per_point_ceiling"] * scale
    floor_at_k = generation["h_per_point_floor"] * scale
    ceiling_total = points * ceiling_at_k + controls * ceiling_at_k
    floor_total = points * floor_at_k + controls * floor_at_k

    assert ceiling_total == committed["total_hours_ceiling_with_never_taught_floor"], (
        f"the pinned Z re-derives a ceiling-side total of {ceiling_total!r} from "
        f"`generation.h_per_point_ceiling`, but {phase23_prereg.COST_RECORD} committed "
        f"{committed['total_hours_ceiling_with_never_taught_floor']!r}. Exact `==`: the budget "
        "this project spends against is not the budget the record priced"
    )
    assert ceiling_total != floor_total or ceiling_at_k == floor_at_k, (
        "the ceiling-derived and floor-derived totals are equal while the per-point figures are "
        "not — the arithmetic above is not reading the two fields it names"
    )
    assert ceiling_total >= floor_total, (
        f"the ceiling-derived total {ceiling_total!r} is BELOW the floor-derived {floor_total!r}. "
        "The ceiling is the slower bound by construction, so this means the two fields are "
        "swapped and Z was sized against the cheap one the ratchet cannot rescue"
    )

    if ceiling_at_k == floor_at_k:
        # EARNED, NOT TOLERATED. The record must show WHY they coincide.
        assert generation["stop_terminated_n_ceiling"] == 0, (
            "the floor and ceiling h/point figures are equal but the ceiling condition records "
            f"{generation['stop_terminated_n_ceiling']!r} stop-terminated draws. A degenerate "
            "bracket has to come from the measurement, not from a copy of one field into the other"
        )
        for shape in generation["per_shape"]:
            assert shape["stop_terminated_n_floor"] == shape["stop_terminated_n_ceiling"], (
                f"shape {shape['shape']!r} records different stop counts between the floor and "
                "ceiling conditions, so the two conditions did NOT measure the same thing and "
                "their equal h/point figures are not earned"
            )


@pytest.mark.parametrize("falsify", (False, True))
def test_n64_leg_matches_the_cal03_verdict(falsify):
    """D-06, BOTH BRANCHES — so "confirmed" and "never checked" are distinguishable.

    A negative recorded only by ABSENCE cannot be told apart from never having looked. So the
    branch is computed from a record through `phase23_prereg.n64_leg_is_committable` twice: once
    from the COMMITTED artifact, which is what the pinned constant must match, and once from a
    CONSTRUCTED copy with its ε falsified by one ULP — never by editing the committed artifact,
    which is frozen.

    The falsified case is what proves the selector DISCRIMINATES. Without it, a pinned `False`
    would be indistinguishable from a constant that could only ever say `False`.
    """
    _path, record = _cal03_record()

    if falsify:
        record = dict(record)
        record["epsilon_n64"] = math.nextafter(record["epsilon_n64"], math.inf)
        assert record["epsilon_n64"] != _cal03_record()[1]["epsilon_n64"], (
            "the constructed copy is identical to the committed record — there is nothing to "
            "falsify and this case observes nothing"
        )
        assert _withdrawal_implied_by(record) is True, (
            "a record whose two epsilons DISAGREE did not imply a withdrawal. "
            "`n64_leg_is_committable` has acquired a tolerance, and the one-ULP leak it exists to "
            "catch would now pass"
        )
        assert mitigation_budget.N64_LEG_WITHDRAWN is False, (
            f"N64_LEG_WITHDRAWN is {mitigation_budget.N64_LEG_WITHDRAWN!r}. The LIVE record is not "
            "the falsified copy built here, so the pinned branch is the confirming one — see the "
            "un-falsified case for the assertion against the committed artifact"
        )
        return

    implied = _withdrawal_implied_by(record)
    assert mitigation_budget.N64_LEG_WITHDRAWN is implied, (
        f"N64_LEG_WITHDRAWN is {mitigation_budget.N64_LEG_WITHDRAWN!r} but "
        f"{phase23_prereg.CAL03_WIRING_RECORD}, read live through "
        f"`phase23_prereg.n64_leg_is_committable`, implies {implied!r}"
    )
    assert implied is not record["verdict"], (
        f"the record's own `verdict` field {record['verdict']!r} and the withdrawal implied by "
        f"re-running the blind rule over its own numbers {implied!r} are not complements — the "
        "writer did not call the pinned rule"
    )

    provenance = mitigation_budget.N64_LEG_WITHDRAWN_PROVENANCE
    assert provenance["record"] == phase23_prereg.CAL03_WIRING_RECORD, (
        f"the withdrawal provenance names {provenance['record']!r}, not the register's "
        f"{phase23_prereg.CAL03_WIRING_RECORD!r}"
    )
    for key in ("verdict", "epsilon_n8", "epsilon_n64", "t_n8", "t_n64"):
        assert provenance[key] == record[key], (
            f"the withdrawal provenance records {key} = {provenance[key]!r} but "
            f"{phase23_prereg.CAL03_WIRING_RECORD} records {record[key]!r} — the branch cites a "
            "measurement other than the one it was taken on"
        )


def test_the_never_taught_floor_is_priced_in_z():
    """A budget for N sweep points that forgets N control points is short by N points.

    `N_CONTROL_SEEDS` is asserted against `results/phase23_never_taught_training.json` — the record
    whose adapters 23-14 actually scores — and the never-taught term is recomputed at EVERY rung,
    not only the selected one, so a rung change cannot silently drop the control cost.
    """
    _path, never_taught = _never_taught_record()
    distinct = len(set(never_taught["seeds"]))

    assert mitigation_budget.N_CONTROL_SEEDS == distinct == never_taught["n_seeds"], (
        f"N_CONTROL_SEEDS is {mitigation_budget.N_CONTROL_SEEDS!r} against "
        f"{distinct!r} DISTINCT seeds and a recorded n_seeds of {never_taught['n_seeds']!r} in "
        f"{phase23_prereg.NEVER_TAUGHT_TRAINING_RECORD}"
    )
    assert mitigation_budget.N_CONTROL_SEEDS_PROVENANCE["seeds"] == tuple(never_taught["seeds"]), (
        f"the provenance names seeds "
        f"{mitigation_budget.N_CONTROL_SEEDS_PROVENANCE['seeds']!r}, the record "
        f"{never_taught['seeds']!r}. Both must be LADDER order and never sorted order"
    )

    _cost_path, cost = _cost_record()
    generation = cost["generation"]
    assert len(cost["sizing"]) == len(mitigation_gate.K_RUNGS), (
        f"{phase23_prereg.COST_RECORD} sizes {sorted(cost['sizing'])} but the frozen menu is "
        f"{mitigation_gate.K_RUNGS} — a rung with no priced control term is a rung this project "
        "could select and under-budget"
    )
    for rung in mitigation_gate.K_RUNGS:
        block = cost["sizing"][str(rung)]
        scale = block["draws_per_point_at_k"] / generation["draws_per_point"]
        term = mitigation_budget.N_CONTROL_SEEDS * (generation["h_per_point_ceiling"] * scale)
        assert term == block["never_taught_floor_hours_ceiling"], (
            f"at K={rung} the never-taught term recomputes to {term!r} from the pinned "
            f"N_CONTROL_SEEDS, but the record committed "
            f"{block['never_taught_floor_hours_ceiling']!r}"
        )
        assert block["never_taught_seeds"] == mitigation_budget.N_CONTROL_SEEDS, (
            f"at K={rung} the record priced {block['never_taught_seeds']!r} control seeds against "
            f"the pinned {mitigation_budget.N_CONTROL_SEEDS!r}"
        )


def test_a_z_constant_that_does_not_re_derive_is_detected(tmp_path):
    """WATCHED RED, PERMANENTLY: a Z constant perturbed by ONE is observed being caught.

    `test_a_hand_edited_matched_floor_is_detected`'s shape, for the same reason — a guard nobody
    has watched fail is not evidence. `SWEEP_POINTS` is the perturbed one because it is an integer
    count where a one-off is the plausible human error, and because it is a MULTIPLICAND of the
    ceiling-side total, so the detection runs through the same identity
    `test_z_was_sized_against_the_ceiling` relies on.

    THE NEEDLE IS LINE-ANCHORED, and the newline is carried into the replacement too or the edit
    swallows a line break and the scratch copy stops being a faithful copy. This is not optional
    here: the pinned width also appears inside `SWEEP_POINTS_PROVENANCE` and in the user's
    verbatim checkpoint reply, so a bare needle would be ambiguous by construction.
    """
    original = mitigation_budget.SWEEP_POINTS
    perturbed = original + 1

    source = _MITIGATION_BUDGET_PATH.read_text(encoding="utf-8")
    needle = f"\nSWEEP_POINTS = {original!r}"
    assert source.count(needle) == 1, (
        f"{_MITIGATION_BUDGET_REL} contains {source.count(needle)} occurrences of {needle!r}. The "
        "edit below would land somewhere other than the pinned assignment, or nowhere at all"
    )
    copy = tmp_path / "mitigation_budget.py"
    copy.write_text(source.replace(needle, f"\nSWEEP_POINTS = {perturbed!r}"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("perturbed_budget", copy)
    edited = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edited)

    # META-GUARD, before any verdict is read off it. A copy that failed to import, or one whose
    # replacement missed, would fail everything below for a reason unrelated to detection. The
    # second half proves the newline was carried: had it been dropped, the preceding line would
    # have been welded onto this assignment.
    assert edited.SWEEP_POINTS == perturbed, (
        f"the scratch copy loaded with SWEEP_POINTS = {edited.SWEEP_POINTS!r}, not the perturbed "
        f"{perturbed!r} — this test is not observing what it claims to observe"
    )
    assert edited.CURVE_K == mitigation_budget.CURVE_K, (
        "the scratch copy's CURVE_K moved, so the line-anchored replacement did not leave the rest "
        "of the module byte-identical"
    )

    _path, cost = _cost_record()
    generation = cost["generation"]
    committed = cost["sizing"][str(mitigation_budget.CURVE_K)]

    def _projected(module):
        return phase23_cost.size_sweep(
            generation_record=generation, sweep_points=module.SWEEP_POINTS, k=module.CURVE_K
        )["projected_hours"]

    assert _projected(mitigation_budget) == committed["projected_hours"], (
        "the COMMITTED constants stopped re-deriving, so the comparison below would fail for both "
        "modules and this control would prove nothing"
    )
    assert _projected(edited) != committed["projected_hours"], (
        f"the perturbed SWEEP_POINTS = {perturbed!r} still re-derives "
        f"{committed['projected_hours']!r} — `test_budget_constants_re_derive` would stay GREEN "
        "against a hand-edited Z constant"
    )
