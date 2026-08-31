"""PLAN 25-03 — D-30'S EPSILON GATE, AND THE MEASUREMENT THAT MAKES IT AN AST WALK.

**THE GATE.** No name in `scripts/phase25_epsilon.py::EPSILON_NAMES` may reach a `print`, an
f-string, a `.format()` call or a `%` interpolation in any module this phase owns, outside the
helper's own file. That is the structural half of FRONT-02: an example-level epsilon can never be
read as if it bounded fact leakage if the only surface that renders one is the surface that renders
the fact-level unit, the sampler statement and both multiplicities in the same sentence.

**WHY AN AST WALK AND NOT A GREP, MEASURED RATHER THAN ARGUED.** `test_grep_goes_false_red_where_
the_ast_gate_is_green` runs the two channels over the real, frozen, ancestry-guarded
`scripts/mitigation_gate.py` and reports both counts. The textual channel finds the token `epsilon`
forty-two times; the AST channel, resolving identifiers against `EPSILON_NAMES` under exact
equality, finds zero. A textual gate over that file reports a violation that does not exist, and
`.planning/REQUIREMENTS.md`'s RPT-02 row records four independent instances of that false-RED class
in Phase 20 alone. This is the natural RED — the real file, today, unmodified — rather than a
planted one, and the frozen module is only ever READ here.

**THE COUNTING FORM IS `str.count`, NEVER `grep -c`.** `tests/test_phase24_correction.py:32-36`
states the mechanic: ``grep -c`` counts LINES, not occurrences, so two occurrences emitted on one
line satisfy a ``grep -c ... = 1`` check. Here the hazard compounds — a ``grep -c`` over this file
would also match this very paragraph, because the paragraph names the form it is refusing. Every
count below is `str.count` or a list length over parsed nodes.

**AND THE GATE'S OWN RED IS WATCHED.** A guard nobody has seen fail is a guard nobody has verified
(`tests/test_phase22_dpsgd_ast.py`'s register). The planted bare print lives in `tmp_path`, never in
a real repo file, and the test asserts `git status --porcelain scripts/` is empty immediately after
so the watching left no residue.

CPU-only, GPU-free, stdlib plus one sibling script. No torch, no numpy, no network.
"""

import ast
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase25_epsilon  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)

# The exemption is ONE RESOLVED PATH. Not a name, not a prefix, not a package — see
# `test_the_exemption_is_the_helper_module_not_the_package`, which plants a file with this exact
# BASENAME somewhere else and requires it to fail.
_HELPER_PATH = pathlib.Path(phase25_epsilon.__file__).resolve()

# The demonstration target. READ ONLY: ancestry-guarded and permanently uneditable.
_GATE_PATH = _ROOT / "scripts" / "mitigation_gate.py"


def _phase25_modules():
    """Every module this phase owns, collected by GLOB so a later one is covered automatically."""
    paths = sorted((_ROOT / "scripts").glob("phase25_*.py"))
    plot = _ROOT / "scripts" / "plot_phase25.py"
    if plot.exists():
        paths.append(plot)
    return paths


def _epsilon_identifier(node):
    """The gate's ONE resolver: an identifier that IS a member of `EPSILON_NAMES`, or ``None``.

    Exact membership, never a substring test. The difference is measured in
    `test_grep_goes_false_red_where_the_ast_gate_is_green`: a substring resolver over the frozen
    gate hits `epsilon_independent_of_n`, `epsilon_gap` and `fallback_epsilon_tolerance`, none of
    which is an epsilon being rendered, and would go RED for the same reason a text search does —
    one layer deeper and harder to see.
    """
    if isinstance(node, ast.Name) and node.id in phase25_epsilon.EPSILON_NAMES:
        return node.id
    if isinstance(node, ast.Attribute) and node.attr in phase25_epsilon.EPSILON_NAMES:
        return node.attr
    if isinstance(node, ast.arg) and node.arg in phase25_epsilon.EPSILON_NAMES:
        return node.arg
    return None


def _is_rendering(node):
    """A `print` call, an f-string, a `.format()` call, or a `%` interpolation on a string."""
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        left = node.left
        return isinstance(left, ast.JoinedStr) or (
            isinstance(left, ast.Constant) and isinstance(left.value, str)
        )
    return False


def _enclosing_function(functions, node):
    """The INNERMOST enclosing `def`, so a nested helper is named rather than its parent."""
    best = None
    for function in functions:
        if function.lineno <= node.lineno <= function.end_lineno:
            if best is None or function.lineno > best.lineno:
                best = function
    return best.name if best is not None else "<module>"


def _epsilon_renderings(path):
    """Every `EPSILON_NAMES` identifier reaching a rendering in `path`.

    Returns a sorted list of ``(path, lineno, function, identifier)``. Deduplicated on
    ``(lineno, col_offset, identifier)`` because a name inside ``print(f"...")`` sits under BOTH the
    `print` Call and the `JoinedStr`, and one bare epsilon is one finding rather than two.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    found = {}
    for node in ast.walk(tree):
        if not _is_rendering(node):
            continue
        for inner in ast.walk(node):
            identifier = _epsilon_identifier(inner)
            if identifier is None:
                continue
            key = (inner.lineno, inner.col_offset, identifier)
            found[key] = (
                path,
                inner.lineno,
                _enclosing_function(functions, inner),
                identifier,
            )
    return sorted(found.values(), key=lambda row: (str(row[0]), row[1], row[3]))


def _run_gate(paths):
    """The gate over a list of modules. The helper's own file is exempt BY RESOLVED PATH."""
    violations = []
    for path in paths:
        if pathlib.Path(path).resolve() == _HELPER_PATH:
            continue
        violations.extend(_epsilon_renderings(pathlib.Path(path)))
    return violations


def _failure_message(violations):
    """The gate's failure text: file, line number, function and the offending identifier."""
    return "\n".join(
        f"{path}:{lineno} in {function}(): bare epsilon name {identifier!r} reaches a "
        f"print/f-string/.format/% outside {_HELPER_PATH.name}. Route it through "
        f"phase25_epsilon.report_epsilon(...), which renders the point epsilon, the curve total, "
        f"selection_accounted, the privacy unit, the sampler statement and both multiplicities in "
        f"one sentence."
        for path, lineno, function, identifier in violations
    )


def test_no_bare_epsilon_is_printed_outside_the_helper():
    """D-30's gate, live over every module this phase owns."""
    modules = _phase25_modules()
    assert modules, "the phase25 glob collected nothing; the gate would pass vacuously"
    assert _HELPER_PATH in [p.resolve() for p in modules], (
        "the helper itself must be inside the glob, or the exemption is exempting nothing"
    )
    violations = _run_gate(modules)
    assert not violations, _failure_message(violations)


def test_grep_goes_false_red_where_the_ast_gate_is_green():
    """THE DEMONSTRATION, on the real frozen `scripts/mitigation_gate.py`, unmodified.

    A textual gate applied to this file today reports a violation THAT DOES NOT EXIST: the token
    `epsilon` is there in quantity, and none of it is an epsilon being rendered. That is the class
    RPT-02 exists to close, and `.planning/REQUIREMENTS.md`'s RPT-02 row records four independent
    instances of it in Phase 20 alone. It is also why every count here is `str.count` over a string
    or a length over parsed nodes and never ``grep -c``, which counts LINES rather than occurrences
    and would additionally match this docstring for naming the form it refuses.
    """
    source = _GATE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # --- channel 1: TEXT. What a naive gate sees.
    textual = source.count("epsilon")
    assert textual >= 25, f"textual channel found {textual}; the demonstration needs >= 25"

    # --- channel 2: AST, under the gate's own resolver. What is actually there.
    resolved = [
        (node.lineno, _epsilon_identifier(node))
        for node in ast.walk(tree)
        if _epsilon_identifier(node) is not None
    ]
    assert resolved == [], f"expected 0 resolving epsilon identifiers, found {resolved}"

    # --- the two channels disagree, which IS the finding.
    assert textual != len(resolved), (
        f"the demonstration requires disagreement: text={textual}, ast={len(resolved)}"
    )

    # --- WHERE the occurrences live: inside `ast.Constant` string values, in two named functions.
    in_constants = sum(
        node.value.count("epsilon")
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    assert in_constants >= 25, (
        f"expected >= 25 occurrences inside string constants, got {in_constants}"
    )
    per_function = {}
    for function in ast.walk(tree):
        if isinstance(function, ast.FunctionDef):
            per_function[function.name] = sum(
                node.value.count("epsilon")
                for node in ast.walk(function)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            )
    assert per_function["exists_clearing_point"] == 2, per_function["exists_clearing_point"]
    assert per_function["capacity_comparison"] == 23, per_function["capacity_comparison"]

    # --- and why the resolver is EXACT membership rather than a substring test: a substring
    # resolver goes RED here too, one layer below the text channel, on three identifiers that are
    # not epsilons being rendered.
    substring = sorted(
        {
            node.id if isinstance(node, ast.Name) else node.arg
            for node in ast.walk(tree)
            if (isinstance(node, ast.Name) and "epsilon" in node.id)
            or (isinstance(node, ast.arg) and "epsilon" in node.arg)
        }
    )
    assert substring == [
        "epsilon_gap",
        "epsilon_independent_of_n",
        "fallback_epsilon_tolerance",
    ], substring


def test_the_epsilon_gate_fires_on_a_planted_bare_print(tmp_path):
    """THE GATE'S OWN RED, watched on a scratch copy in `tmp_path` and never in a real repo file."""
    planted = tmp_path / "phase25_planted.py"
    planted.write_text(
        'def render(point_epsilon):\n    print(f"epsilon={point_epsilon}")\n',
        encoding="utf-8",
    )

    violations = _run_gate([planted])
    assert len(violations) == 1, violations
    path, lineno, function, identifier = violations[0]
    assert path == planted
    assert lineno == 2
    assert function == "render"
    assert identifier == "point_epsilon"

    message = _failure_message(violations)
    assert "render()" in message and ":2" in message and "point_epsilon" in message, message

    completed = subprocess.run(
        ["git", "status", "--porcelain", "scripts/"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout == "", (
        f"watching the RED must leave no residue in scripts/: {completed.stdout!r}"
    )


def test_the_exemption_is_the_helper_module_not_the_package(tmp_path):
    """The exemption is ONE RESOLVED PATH — not a basename, not a prefix, not a package."""
    near_miss = tmp_path / "phase25_epsilon_helper.py"
    near_miss.write_text(
        'def show(epsilon):\n    print("eps %s" % epsilon)\n',
        encoding="utf-8",
    )
    assert _run_gate([near_miss]), "a near-miss NAME must not inherit the helper's exemption"

    same_basename = tmp_path / "phase25_epsilon.py"
    same_basename.write_text(
        'def show(curve_total_epsilon):\n    print("{}".format(curve_total_epsilon))\n',
        encoding="utf-8",
    )
    assert _run_gate([same_basename]), (
        "a file with the helper's exact BASENAME at a different path must still fail"
    )

    assert _run_gate([_HELPER_PATH]) == [], "the real helper is the exempt path"


def test_report_epsilon_has_three_keyword_only_args_with_no_defaults():
    """D-30's contract, read off the signature: THE LENGTH IS THE PROTECTION.

    `scripts/mitigation_gate.py::mitigation_point_verdict` pays twenty-one required keyword
    arguments for the same reason, and says so in its own docstring: *"Trimming the list with
    defaults would let a caller silently omit an anchor and still get a verdict, which is the
    failure the length is buying protection from."* Three here, and no default on any of them, so
    the refusal is CPython's own arity check rather than a hand-written guard that could drift from
    the signature it restates.
    """
    tree = ast.parse(_HELPER_PATH.read_text(encoding="utf-8"))
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "report_epsilon"
    ]
    assert len(functions) == 1, functions
    args = functions[0].args
    assert args.posonlyargs == []
    assert args.args == []
    assert args.vararg is None and args.kwarg is None
    assert [a.arg for a in args.kwonlyargs] == [
        "point_epsilon",
        "curve_total_epsilon",
        "selection_accounted",
    ]
    assert all(default is None for default in args.kw_defaults), args.kw_defaults

    # The structural claim, confirmed at runtime: omitting the third is a TypeError naming it.
    try:
        phase25_epsilon.report_epsilon(point_epsilon=1.0, curve_total_epsilon=2.0)
    except TypeError as exc:
        assert "selection_accounted" in str(exc), str(exc)
    else:
        raise AssertionError("report_epsilon accepted two of its three required keyword arguments")
