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
