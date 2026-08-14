"""Phase 17's pre-registration — the family, the all-six gate rule, the tie-break, the scans.

CPU-only, GPU-free, no checkpoint I/O, no generation, no model load. ``scripts/phase17_personas.py``
executes nothing at import beyond its ``sys.path`` bootstrap, so an
``importlib.util.spec_from_file_location`` load here runs no ``__main__`` guard, no tokenizer and no
model. The scripts-load justification is the one ``tests/test_phase16_stats.py`` already states: the
pre-registration constants MUST live in the committed driver for git history to be the proof.

What is pinned here:
  1. **D-18** — "the gate cleared" requires ALL SIX Holm rejections. Five of six fires the all-fail
     branch, and a truncated family cannot clear by being short.
  2. **D-19** — ``worst_pair``'s tie-break, exercised at the all-zero three-way tie that is the
     phase's own SUCCESS case, where a missing tie-break would silently become a post-hoc choice.
  3. **RESEARCH F-08** — Phase 16's family and Phase 17's agreeing at 6 is a COINCIDENCE
     (``C(4,2) == 3x2``), and ``phase16_persistence.holm`` prices alpha off Phase 16's constant.
  4. **ISO-07 / STAT-04 / ISO-05 / STAT-06** — the four static scans, over a GLOB of the Phase 17
     drivers rather than a hand-listed pair, so plans 17-03/17-04/17-05 enter them automatically.
     That glob is D-21's answer to the F-08 blindness: Phase 16's ``_GATE_MODULES`` is file-scoped
     to Phase 16's two drivers, so a Phase 17 driver calling ``holm`` is today neither red nor
     covered, and the discipline does not transfer by inheritance.
"""

import ast
import importlib.util
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_PERSONAS_PATH = _REPO_ROOT / "scripts" / "phase17_personas.py"
_CONTEXT_PATH = (
    _REPO_ROOT / ".planning" / "phases" / "17-multi-persona-isolation-matrix" / "17-CONTEXT.md"
)

# DERIVED from a glob, never a hand-listed tuple (D-21). `scripts/phase17_persona_facts.py` (17-03),
# `scripts/phase17_isolation.py` (17-04) and `scripts/phase17_persona_gate.py` (17-05) enter every
# scan below the moment their plans create them — a hand-listed tuple would leave each new driver
# silently uncovered, which is exactly the F-08 blindness this phase had to re-establish for itself.
_GATE_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("phase17_*.py")))


def _load_personas():
    spec = importlib.util.spec_from_file_location("phase17_personas", _PERSONAS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


personas = _load_personas()

# Already in `sys.modules` — `phase17_personas` imports it for `GATED_TIER` — so this is a cache
# hit and not a second execution of a torch-importing driver.
import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _enclosing_functions(tree):
    """``node -> the innermost FunctionDef containing it``, or ``None`` for module scope.

    Module scope is recorded as ``None`` rather than dropped, because module scope is the most
    dangerous placement there is. Byte-for-byte the idiom
    ``tests/test_phase16_stats.py::_enclosing_functions`` uses.
    """
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            inner = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[child] = current if inner is child else inner
            walk(child, inner)

    walk(tree, None)
    return owner


def _call_sites(path, callee):
    """Every ``callee(...)`` call in ``path`` as ``(function name or '<module>', ast.Call)``."""
    tree = _tree(path)
    enclosing = _enclosing_functions(tree)
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if callee not in (getattr(node.func, "id", None), getattr(node.func, "attr", None)):
            continue
        holder = enclosing.get(node)
        sites.append(("<module>" if holder is None else holder.name, node))
    return sites


def _context_blockquote(anchor):
    """The blockquote following ``anchor`` in ``17-CONTEXT.md``, unwrapped to one line.

    Read from the planning artifact rather than retyped here, because "verbatim" asserted against a
    second hand-typed copy proves only that two copies agree — which is exactly the failure mode a
    verbatim requirement exists to prevent. Byte-for-byte the helper
    ``tests/test_phase16_stats.py`` uses, repointed at this phase's CONTEXT file.
    """
    body = _CONTEXT_PATH.read_text(encoding="utf-8").split(anchor, 1)[1]
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            lines.append(stripped.lstrip(">").strip())
        elif lines:
            break
    assert lines, f"no blockquote follows {anchor!r} in 17-CONTEXT.md"
    return " ".join(lines).strip('"')


def _collapsed_glob_guard():
    """A glob that stops matching makes every scan below green over nothing."""
    assert len(_GATE_MODULES) >= 1, (
        f"the phase17_*.py glob collapsed to {len(_GATE_MODULES)} file(s) — a broken glob makes "
        "every static guard in this module green while scanning no source at all"
    )


def _holm_rows(p_values_in_family_order):
    """Phase 16's ``holm`` over Phase 17's six cells — the row shape ``gate_cleared`` consumes."""
    return persistence.holm(dict(zip(personas.HOLM_FAMILY_CELLS, p_values_in_family_order)))


# Derived from the committed instrument, never retyped: 8/8 unanimity and the achievable 7/8 p.
UNANIMITY_P = persistence.sign_test_exact((1,) * 8)
SEVEN_OF_EIGHT_P = persistence.sign_test_exact((1,) * 7 + (0,))


def test_gate_requires_all_six():
    """D-18 — five of six does not clear, and a short family does not clear by being short."""
    assert (UNANIMITY_P, SEVEN_OF_EIGHT_P) == (0.0078125, 0.0703125), (
        "the achievable p values moved; D-18's 0.0005 margin is priced against exactly these"
    )

    unanimous = _holm_rows([UNANIMITY_P] * 6)
    assert all(row[-1] for row in unanimous), "six unanimous comparisons did not clear every step"
    assert personas.gate_cleared(unanimous) is True

    # One comparison at the achievable 7/8 p (0.0703125): it fails at its own step and Holm's
    # step-down retains it, so five of six reject. D-18 says that is NOT a cleared gate.
    five_of_six = _holm_rows([UNANIMITY_P] * 5 + [SEVEN_OF_EIGHT_P])
    assert sum(1 for row in five_of_six if row[-1]) == 5, "the five-of-six case was not constructed"
    assert personas.gate_cleared(five_of_six) is False, (
        "five of six cleared the gate — D-18 requires all six, because every comparison here is a "
        "live isolation claim between two REAL personas and a partial claim does not carry the "
        "phase's objective"
    )

    # A truncated family cannot clear by being short: every row rejected, but only five rows.
    assert all(row[-1] for row in unanimous[:5])
    assert personas.gate_cleared(unanimous[:5]) is False, (
        "a five-row family cleared a gate closed at six — a family populated at one size and "
        "priced at another is not the test that was registered"
    )


def test_gate_rationale_is_verbatim_from_context():
    """D-18's recorded rationale is READ from 17-CONTEXT.md, never a second hand-typed copy."""
    assert personas.GATE_AGGREGATION_RATIONALE == _context_blockquote("**D-18")


def test_worst_pair_tiebreak():
    """D-19 — the tie-break is load-bearing because the SUCCESS case is itself a three-way tie."""
    persona_a, persona_b, persona_c = personas.PERSONAS

    all_zero = {(i, j): 0.0 for i in personas.PERSONAS for j in personas.PERSONAS if i != j}
    assert personas.worst_pair(all_zero) == (persona_a, persona_b), (
        "the hoped-for all-zero off-diagonal is a THREE-WAY tie, and without a committed "
        "tie-break the 'mechanical' rule degrades into a post-hoc choice exactly there"
    )

    bc_highest = {**all_zero, (persona_b, persona_c): 0.5, (persona_c, persona_b): 0.5}
    assert personas.worst_pair(bc_highest) == (persona_b, persona_c)

    two_way_tie = {
        **all_zero,
        (persona_a, persona_c): 0.4,
        (persona_c, persona_a): 0.4,
        (persona_b, persona_c): 0.4,
        (persona_c, persona_b): 0.4,
        (persona_a, persona_b): 0.1,
        (persona_b, persona_a): 0.1,
    }
    assert personas.worst_pair(two_way_tie) == (persona_a, persona_c), (
        "a tie between (a, c) and (b, c) must break to the LOWEST index i, which is a"
    )

    for rates in (all_zero, bc_highest, two_way_tie):
        first, second = personas.worst_pair(rates)
        assert personas.PERSONAS.index(first) < personas.PERSONAS.index(second), (
            "worst_pair returned an unordered pair that is not in PERSONAS order — the caller "
            "cannot then use it as a stable dict key"
        )


def test_family_closure_bites():
    """The RUNTIME half: a dynamically-built cell list no static scan would ever see."""
    personas.assert_phase17_family_closed(personas.HOLM_FAMILY_CELLS)  # positive control

    seventh = tuple(personas.HOLM_FAMILY_CELLS) + (
        (("persona_a", "persona_a"), ("persona_a", "persona_a")),
    )
    try:
        personas.assert_phase17_family_closed(seventh)
    except SystemExit as exit_:
        assert "0.0071429" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a seventh comparison entered the Holm family at runtime")

    base = personas.BASE_ROW
    with_base_row = tuple(personas.HOLM_FAMILY_CELLS) + (((base, base), (base, "persona_a")),)
    try:
        personas.assert_phase17_family_closed(with_base_row)
    except SystemExit as exit_:
        assert base in str(exit_) and "0.0071429" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError(
            "the adapter-off row entered the Holm family — it is a PUBLISHED control (ISO-03) and "
            "gating it would price alpha at 0.0071429, below the achievable p"
        )


def test_the_phase16_family_length_coincidence_is_pinned():
    """RESEARCH F-08 — ``holm`` prices alpha off PHASE 16's family; the agreement at 6 is luck."""
    assert len(persistence.HOLM_FAMILY_PAIRS) == len(personas.HOLM_FAMILY_CELLS) == 6

    personas.assert_family_length_matches_phase16(len(persistence.HOLM_FAMILY_PAIRS))

    try:
        personas.assert_family_length_matches_phase16(7)
    except SystemExit as exit_:
        assert "CONDITION_ORDER" in str(exit_), (
            "the abort does not name the Phase 16 constant whose edit would reprice this gate, so "
            "its reader is sent to the wrong file"
        )
    else:  # pragma: no cover
        raise AssertionError("a Phase 16 family of 7 was accepted against a Phase 17 family of 6")


def test_no_phase14_thresholds():
    """ISO-07 — Phase 14's gate thresholds appear in no Phase 17 driver."""
    _collapsed_glob_guard()
    for module in _GATE_MODULES:
        source = module.read_text(encoding="utf-8")
        for threshold in ("0.2486", "0.2000"):
            assert threshold not in source, (
                f"{module.name} carries Phase 14's {threshold}. Those thresholds were derived on "
                "CALIBRATION_POOL, and reusing that pool — or its numbers — as a Phase 17 persona "
                "makes the isolation gate circular: it would be judged against a floor measured "
                "on its own material"
            )


def test_no_new_dependencies():
    """STAT-04, the genuinely-new half — Phase 17 drivers import stdlib and this repo, nothing else.

    The FILE-HASH half of STAT-04 is already covered by
    ``tests/test_package.py::test_pyproject_unchanged_since_v2_close``, which sha256-pins
    ``pyproject.toml`` (``PYPROJECT_SHA256`` at ``:11``, compared at ``:36``). A Phase 17 twin of
    that would be a second copy of one rule, and a duplicated rule is a rule that can drift. What
    is NOT covered there is a driver importing something the project never declared — a package
    installed into a live environment leaves ``pyproject.toml`` byte-identical.

    Scanned at ANY depth, so the LAZY-IMPORT RULE's function-local imports count too: a lazy import
    is still a dependency, it is merely a dependency that fails later.
    """
    _collapsed_glob_guard()
    allowed = (
        set(sys.stdlib_module_names)
        | {"torch", "numpy", "regex"}
        | {"personacore"}
        | {path.stem for path in (_REPO_ROOT / "scripts").glob("*.py")}
    )
    for module in _GATE_MODULES:
        for node in ast.walk(_tree(module)):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                roots = [(node.module or "").split(".")[0]] if node.level == 0 else []
            else:
                continue
            for root in roots:
                assert root in allowed, (
                    f"{module.name} imports {root!r}, which is neither stdlib nor part of this "
                    "repository. STAT-04 forbids this phase adding a dependency; the pyproject "
                    "hash guard cannot see an import that was installed into the environment "
                    "rather than declared"
                )


# ISO-05 + STAT-06 — the identifier-based ban, in EXACTLY the committed scope of
# `tests/test_phase16_stats.py:798-823`: the names appearing INSIDE a `holm` / `sign_test_exact`
# call, plus the enclosing function's own name.
_REPLICATION_IDENTIFIERS = ("replication", "seed_rep")
_AGGREGATE_IDENTIFIERS = ("aggregate", "overall", "matrix_rate", "isolation_rate")
_GATED_CALLEES = ("holm", "sign_test_exact")


def _assert_no_identifier_reaches_the_gate(forbidden, why):
    """The Phase 16 scan, verbatim in scope — call-site names and the holder, and nothing wider.

    **Do NOT widen this to module-level assignment targets or to function names at large.** That
    widening is self-invalidating rather than merely strict: ``REPLICATION_SEEDS`` is a
    module-level assignment in ``scripts/phase17_personas.py``, which this very glob includes, and
    plan 17-01 Task 1 MANDATES it — so the widened form fails on its first run, in Wave 1, blocking
    the phase it is supposed to protect.

    The Phase 16 precedent scopes the ban to what actually reaches the verdict path, and that scope
    is what makes it both survivable and meaningful: a CONSTANT named ``REPLICATION_SEEDS`` is
    harmless, while the same name passed into ``holm`` is the defect. A printed nine-cell aggregate
    is separately forbidden by 17-04's own AST acceptance criterion over
    ``scripts/phase17_isolation.py``, which is where such a number could be produced at all.
    """
    _collapsed_glob_guard()
    for module in _GATE_MODULES:
        for callee in _GATED_CALLEES:
            for holder, call in _call_sites(module, callee):
                names = {
                    getattr(node, "id", None) or getattr(node, "attr", None)
                    for node in ast.walk(call)
                }
                names |= {holder}
                offenders = sorted(
                    name for name in names if name and any(w in name.lower() for w in forbidden)
                )
                assert not offenders, (
                    f"{module.name}:{holder} passes {offenders} into {callee} — {why}, and a "
                    "seventh gated comparison prices alpha at 0.0071429, below the achievable p "
                    "of 0.0078125, so the headline would die at every possible outcome"
                )


def test_replication_is_not_gated():
    """ISO-05 — the k=3 seed replication is descriptive by construction (D-16), never a test."""
    _assert_no_identifier_reaches_the_gate(
        _REPLICATION_IDENTIFIERS,
        "ISO-05's replication is descriptive (min / max / median) by construction (D-16)",
    )


def test_no_nine_cell_aggregate():
    """STAT-06 — no aggregate over the 3x3 matrix enters the verdict path; D-09 rejected n=9."""
    _assert_no_identifier_reaches_the_gate(
        _AGGREGATE_IDENTIFIERS,
        "STAT-06 forbids gating a 9-cell aggregate and D-09 rejected pairing at cell level",
    )


def test_nothing_executes_at_import():
    """The pre-registration's own claim: the ``sys.path`` bootstrap is the ONLY module-scope call.

    Written as a walk to module SCOPE rather than a scan of ``tree.body``, because the bootstrap is
    nested inside an ``if`` — so a scan restricted to ``tree.body`` finds zero calls and passes
    while checking nothing, which is the same green-and-blind shape this repository keeps closing.
    Class and function bodies are excluded; everything else at module scope is not.
    """
    tree = _tree(_PERSONAS_PATH)
    enclosing = _enclosing_functions(tree)
    module_scope_calls = [
        ast.unparse(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and enclosing.get(node) is None
    ]
    assert all(call.startswith("sys.path.insert") for call in module_scope_calls), (
        f"scripts/phase17_personas.py runs {module_scope_calls} at import. Its docstring claims "
        "nothing executes beyond the sys.path bootstrap, and every CPU-only test in this phase "
        "loads it with importlib on the strength of that claim"
    )
    assert len(module_scope_calls) == 1, (
        f"expected exactly the one sys.path bootstrap call, found {module_scope_calls} — a "
        "vacuous count here would make this guard green against a file that lost its bootstrap"
    )
