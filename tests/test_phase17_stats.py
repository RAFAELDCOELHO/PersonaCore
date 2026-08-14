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
  5. **D-21 / STAT-01 / STAT-02 / STAT-03 / ISO-03 / D-10 / D-11** (plan 17-08) — the Phase 17 twin
     of Phase 16's six-pairs scan; the question unit proved on a fixture where the two candidate
     units ORDER DIFFERENTLY; the base row proved PUBLISHED and proved NOT GATED; both ends of the
     clustering assumption at every zero; the all-fail branch; and the clobber refusal.

Plan 17-08's additions load ``scripts/phase17_isolation.py`` as well. That driver is equally inert
at import (its own ``sys.path`` bootstrap plus a ``__main__`` guard), and every test below that runs
it stays CPU-only: no torch tensor, no model, no tokenizer, no checkpoint and no generation. The
two-pass design is what makes that possible — the report mode scores RECORDED JSON.
"""

import ast
import importlib.util
import json
import pathlib
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_PERSONAS_PATH = _REPO_ROOT / "scripts" / "phase17_personas.py"
_ISOLATION_PATH = _REPO_ROOT / "scripts" / "phase17_isolation.py"
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


def _load_isolation():
    """The Phase 17 driver, loaded the same way — nothing runs beyond its ``sys.path`` insert."""
    spec = importlib.util.spec_from_file_location("phase17_isolation", _ISOLATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


personas = _load_personas()
iso = _load_isolation()

# Already in `sys.modules` — `phase17_personas` imports it for `GATED_TIER` — so this is a cache
# hit and not a second execution of a torch-importing driver.
import _verdict  # noqa: E402  (needs the sys.path insert above)
import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_def(tree, name):
    """The named ``FunctionDef`` node, or ``None``.

    Returned rather than asserted so the CALLER asserts the function was FOUND before asserting
    anything about its contents — a scan that finds nothing is green for the wrong reason, and a
    renamed function would otherwise make every structural guard pass over an empty AST. The idiom
    ``tests/test_phase17_scoring.py::_function_def`` uses.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


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


# =============================================================================================
# ===== Plan 17-08 — the report path: the six-pairs twin, the unit, the base row, the branch ===
# =============================================================================================
#
# The four Phase 17 driver filenames, spelled out ONCE so the coverage assertion below can name
# what it expects rather than only count it. DERIVED from the glob everywhere else.
_EXPECTED_GATE_MODULES = (
    "phase17_isolation.py",
    "phase17_persona_facts.py",
    "phase17_persona_gate.py",
    "phase17_personas.py",
)

# The real minted material. The SCORING core's tests run on SYNTHETIC values by design (SC3, pinned
# in `tests/test_phase17_scoring.py`); the REPORT path legitimately reads the material at the run's
# edge — `run_report_mode` calls `values_by_slot()` — so the fixtures below use the committed values
# and every test here exercises the same mapping the published report will.
VALUES = iso.values_by_slot()

# A SMALLER fixture than the real 13-per-slot tier: `assemble_matrix` imposes no per-slot question
# count (only `held_out_by_slot` does, and the report path never calls it), and the sign test needs
# the 8 SLOTS, which this keeps. Fewer questions keeps the bootstrap cheap without weakening a
# single claim below.
_QUESTIONS_PER_SLOT = 3
_DRAWS = 4

# NOT the pre-registered `BOOTSTRAP_RESAMPLES`. `describe_matrix` takes `resamples` as a keyword
# whose DEFAULT is that committed constant; the published report always runs at the default (main()
# passes nothing) and prints the count it used, so a lowered one is visible in the artifact. Lowered
# here only so these tests do not pay 10,000 resamples twelve times.
_RESAMPLES = 200


def _sweep_record(sweep, completion_for):
    """One recorded sweep in the shape 17-06 writes and 17-08 reads, provenance included."""
    entries = []
    for n, slot in enumerate(personas.CORE_SLOTS):
        for index in range(_QUESTIONS_PER_SLOT):
            entries.append(
                {
                    "slot": slot,
                    "seed_index": n * _QUESTIONS_PER_SLOT + index,
                    "question": f"synthetic {slot} question {index}",
                    "fact_id": f"synthetic_{slot}_{index}",
                    "completions": [completion_for(slot, index, draw) for draw in range(_DRAWS)],
                }
            )
    return {
        iso.SWEEP_LABEL_KEY: sweep,
        iso.SWEEP_QUESTIONS_KEY: entries,
        "git_sha": "0" * 40,
        "pid": 4100 + iso.SWEEPS.index(sweep),
        "device": "cpu",
        "wall_clock_min": 1.5,
        iso.LORA_B_DIGEST_KEY: f"live-{sweep}".ljust(64, "e"),
        iso.ADAPTER_FILE_DIGEST_KEY: f"file-{sweep}".ljust(64, "f"),
        iso.ADAPTER_ENABLED_KEY: sweep != personas.BASE_ROW,
        "config": {"n_draws": _DRAWS, "forbid_ids_sha256": "7b" * 32},
    }


def _says(*labels):
    """A row whose every completion carries exactly ``labels``' values for the question's slot."""

    def build(slot, index, draw):
        spoken = " and also ".join(VALUES[slot][label] for label in labels)
        return f"i go by {spoken} truly"

    return build


def _silent(slot, index, draw):
    """A completion naming no persona's value at all."""
    return f"the answer here is unknown to me {slot} {index} {draw}"


def _records(**builders):
    """The four records, in ``SWEEPS`` order, each from its own completion builder."""
    return [_sweep_record(sweep, builders[sweep]) for sweep in iso.SWEEPS]


def _clean_records():
    """The success case: each adapter answers with its OWN value; the base names nothing."""
    return _records(
        persona_a=_says("persona_a"),
        persona_b=_says("persona_b"),
        persona_c=_says("persona_c"),
        base=_silent,
    )


def _tied_records():
    """Adapter A also emits B's value on every question — one comparison ties, so 5 of 6 reject."""
    return _records(
        persona_a=_says("persona_a", "persona_b"),
        persona_b=_says("persona_b"),
        persona_c=_says("persona_c"),
        base=_silent,
    )


def _assemble(records):
    """``(matrix, described)`` — the two things the writer takes, built from recorded JSON only."""
    base_texts = iso.base_texts_by_slot(records[-1])
    matrix = iso.assemble_matrix(records, VALUES, base_texts)
    described = iso.describe_matrix(matrix, iso.draws_per_question(records), resamples=_RESAMPLES)
    return matrix, described, base_texts


def _render(records, monkeypatch, tmp_path, *, gate=None):
    """Assemble and render, with the report path redirected — no test writes under `results/`."""
    monkeypatch.setattr(iso, "ISOLATION_REPORT_PATH", tmp_path / "phase17_isolation_report.md")
    matrix, described, base_texts = _assemble(records)
    gate = gate or iso.compare_cells(iso.cell_rates(matrix))
    text = iso.render_report(
        matrix,
        described,
        gate,
        records,
        iso.base_prior_anchor(base_texts),
        resamples=_RESAMPLES,
    )
    return text, matrix, gate


def _section(text, heading):
    """One `## ` section's body, so an assertion cannot accidentally match the wrong section."""
    body = text.split(f"\n{heading}\n", 1)
    assert len(body) == 2, f"{heading!r} is missing from the rendered report"
    return body[1].split("\n## ", 1)[0]


def test_gate_modules_covers_all_four_phase17_drivers():
    """D-21 — the glob actually resolves to every Phase 17 driver, now that all four exist.

    Counted AND named. A glob that silently matched three of four would leave one driver outside
    every scan in this file while each scan still reported green — which is precisely the F-08
    blindness this phase had to re-establish for itself, because Phase 16's ``_GATE_MODULES`` is
    file-scoped to Phase 16's two drivers and the discipline does not transfer by inheritance.
    """
    assert tuple(module.name for module in _GATE_MODULES) == _EXPECTED_GATE_MODULES, (
        f"the phase17_*.py glob resolved to {[m.name for m in _GATE_MODULES]}, not the four "
        f"committed drivers {list(_EXPECTED_GATE_MODULES)} (phase17_isolation.py — the scoring "
        "core, the sweeps and the report; phase17_persona_facts.py — the 24 minted values; "
        "phase17_persona_gate.py — the ISO-01 guessability gate; phase17_personas.py — the "
        "pre-registration). A driver outside this tuple is a driver outside every static scan in "
        "this file, and it would be neither red nor covered"
    )
    assert len(_GATE_MODULES) == 4


def test_nothing_outside_the_six_pairs_enters_the_verdict_path():
    """D-21, the STATIC half — the Phase 17 twin of ``test_phase16_stats.py``'s six-pairs scan.

    Phase 16's ``_GATE_MODULES`` is file-scoped to its own two drivers, so before this test a
    Phase 17 driver calling ``holm`` was NEITHER RED NOR COVERED. Every call site is a hypothesis
    family and D-08 permits exactly one, so the scan asserts the site list and not merely that some
    site exists.
    """
    _collapsed_glob_guard()
    for callee in _GATED_CALLEES:
        by_module = {
            module.name: sorted(name for name, _call in _call_sites(module, callee))
            for module in _GATE_MODULES
        }
        holders = by_module.pop("phase17_isolation.py")
        assert set(holders) == {"compare_cells"}, (
            f"{callee} is called from somewhere other than compare_cells — every call site OUTSIDE "
            "the one permitted function is a second hypothesis family, and at m = 7 Holm's first "
            f"alpha is 0.0071429, below the achievable p of 0.0078125. Holders: {holders}"
        )
        assert all(sites == [] for sites in by_module.values()), (
            f"{callee} reached a Phase 17 driver that computes no verdict: {by_module}"
        )

    # `holm` is the call that FORMS the family, so it is additionally pinned at exactly one site: a
    # second `holm(...)` — even inside compare_cells — is a second family priced at the same alpha.
    # `sign_test_exact` is deliberately NOT count-pinned: it runs once per comparison in a
    # comprehension, plus twice for the two ACHIEVABLE p values §Pre-Registration publishes as a
    # property of the design. Those two live here rather than in the writer precisely so this scan
    # stays true — a writer that computed them for itself would be a call site outside the gate.
    holm_sites = _call_sites(_ISOLATION_PATH, "holm")
    assert len(holm_sites) == 1, (
        f"holm is called {len(holm_sites)} times in phase17_isolation.py "
        f"({sorted(name for name, _call in holm_sites)}) — D-08 closes the family at six "
        "comparisons and permits exactly one call that forms it"
    )

    compare = _function_def(_tree(_ISOLATION_PATH), "compare_cells")
    assert compare is not None, "compare_cells is gone — a renamed gate makes this scan blind"
    called = {
        getattr(call.func, "id", None) or getattr(call.func, "attr", None)
        for call in ast.walk(compare)
        if isinstance(call, ast.Call)
    }
    assert "assert_phase17_family_closed" in called, (
        "compare_cells does not call the runtime family guard — the static scan above catches a "
        "NEW CALL SITE, but only the runtime guard catches a DYNAMICALLY-BUILT pair list, and "
        "either one alone leaves the other open"
    )
    assert "assert_family_length_matches_phase16" in called, (
        "compare_cells does not pin F-08's coincidence — holm prices alpha off PHASE 16's family, "
        "and the two agreeing at 6 is C(4,2) == 3x2, not a shared design"
    )

    # STAT-01, mechanically: Phase 16's per-fact grouping helper computes sum(k)/sum(n) — the DRAW
    # rate — so a call to it anywhere in this phase would silently reprice every published cell.
    # The plan's `grep -c` proxy cannot express this (both drivers' docstrings explain the ban by
    # name), so the invariant it stands for is asserted directly.
    for module in _GATE_MODULES:
        assert _call_sites(module, "aggregate_by_fact") == [], (
            f"{module.name} calls Phase 16's per-fact grouping helper, whose rate is the DRAW rate "
            "— STAT-01 makes the QUESTION the unit of analysis, and the two differ by more than a "
            "factor of two on the real gated tier"
        )


def test_the_base_row_is_published_but_never_gated():
    """ISO-03 / STAT-03 — published and gated are different permissions, and conflating them
    reprices alpha.

    The arithmetic, recorded so the refusal is not merely a rule: the family is closed at six, and
    a SEVENTH comparison prices Holm's first alpha at 0.05 / 7 = 0.0071429 — BELOW the achievable
    p of 0.0078125 (slot unanimity, the most extreme outcome this design can produce). Admitting
    the adapter-off row to the family would therefore kill the headline at EVERY possible outcome,
    including perfect unanimity. It is computed, published in §The Matrix and read by D-10's
    all-fail branch; it is never a member of the family.
    """
    assert not [pair for pair in personas.HOLM_FAMILY_CELLS if personas.BASE_ROW in pair], (
        "the committed family names the adapter-off row — it is derived over PERSONAS only, "
        "precisely so exclusion is by construction rather than by discipline"
    )
    assert persistence.HOLM_ALPHA / (len(personas.HOLM_FAMILY_CELLS) + 1) < UNANIMITY_P, (
        "a seventh comparison no longer prices alpha below the achievable p — the arithmetic this "
        "refusal rests on has moved and the refusal must be re-derived, not carried forward"
    )

    with_base = tuple(personas.HOLM_FAMILY_CELLS) + (
        ((personas.BASE_ROW, personas.BASE_ROW), (personas.BASE_ROW, "persona_a")),
    )
    try:
        personas.assert_phase17_family_closed(with_base)
    except SystemExit as exit_:
        assert personas.BASE_ROW in str(exit_) and "0.0071429" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("the runtime family guard admitted the adapter-off row")

    matrix, _described, _base_texts = _assemble(_clean_records())
    rates = iso.cell_rates(matrix)
    assert not [cell for cell in rates if personas.BASE_ROW in cell], (
        "cell_rates handed a base cell to the gate — the base row must be dropped BEFORE the "
        "family is built, not caught afterwards"
    )
    rates[(personas.BASE_ROW, "persona_a")] = {slot: {"rate": 0.0} for slot in personas.CORE_SLOTS}
    try:
        iso.compare_cells(rates)
    except SystemExit as exit_:
        assert "0.0071429" in str(exit_), (
            "the refusal does not carry the arithmetic that makes it non-negotiable, so its reader "
            "cannot tell a rule from a consequence"
        )
    else:  # pragma: no cover
        raise AssertionError(
            "compare_cells gated a base cell — a seventh comparison prices alpha at 0.0071429, "
            "below the achievable p of 0.0078125"
        )


def test_the_matrix_publishes_the_base_column(monkeypatch, tmp_path):
    """ISO-03, the B4 regression — the leak-vs-prior separator is COMPUTED, not left empty.

    What this catches: if only the three adapter records reach ``assemble_matrix``, cells
    ``(base, j)`` are never computed at all. ``base_texts`` cannot supply them either — ``classify``
    scores any completion carrying persona *j*'s value as ``leak`` (branch 3) long before the
    ``base_texts`` membership test (branch 4) is reached, which is exactly why branch 2 exists. The
    report's ONLY quantitative separator of *"adapter i leaked persona j's value"* from *"the base
    was going to say that anyway"* would then render empty while every other number looked intact.

    Driven through ``run_report_mode`` rather than around it, so the four-record contract is
    asserted at the production call site: this test goes red if that function ever filters the
    records it forwards.
    """
    records = _tied_records()
    base = records[iso.SWEEPS.index(personas.BASE_ROW)]
    leaked = 0
    for entry in base[iso.SWEEP_QUESTIONS_KEY]:
        if entry["slot"] == "pet_name":
            value = VALUES["pet_name"]["persona_b"]
            entry["completions"] = [f"i think it is {value}" for _ in entry["completions"]]
            leaked += 1
    assert leaked == _QUESTIONS_PER_SLOT, "the base row was not made to carry persona B's value"

    monkeypatch.setattr(iso, "SWEEP_RECORD_DIR", tmp_path)
    monkeypatch.setattr(iso, "ISOLATION_REPORT_PATH", tmp_path / "report.md")
    for record in records:
        iso.sweep_record_path(record[iso.SWEEP_LABEL_KEY]).write_text(
            json.dumps(record), encoding="utf-8"
        )

    text = iso.run_report_mode(resamples=_RESAMPLES)

    n_questions = _QUESTIONS_PER_SLOT * personas.SLOTS_EXPECTED
    expected = persistence.report_proportion(leaked, n_questions, n_questions * _DRAWS)
    matrix_section = _section(text, "## The Matrix")
    base_rows = [
        line
        for line in matrix_section.splitlines()
        if line.startswith(f"| `{personas.BASE_ROW}` |")
    ]
    assert len(base_rows) == 1, (
        f"§The Matrix rendered {len(base_rows)} adapter-off rows — the base row is a fourth row of "
        "the SAME table, and without it column j has no control to be read against"
    )
    assert expected["formatted"] in base_rows[0], (
        f"the base row does not publish cell (base, persona_b) as {expected['formatted']!r}:\n"
        f"{base_rows[0]}"
    )

    verdict = _verdict.recorded_verdict(text)
    assert iso.compare_cells(iso.cell_rates(_assemble(records)[0]))["cleared"] is False, (
        "the fixture cleared the gate, so the all-fail branch never rendered and item (b) could "
        "not be checked — this test needs a gate that does NOT clear"
    )
    assert expected["formatted"] in verdict, (
        "D-10's all-fail branch item (b) does not reproduce the adapter-off column's numbers — the "
        "branch requires (a) AND (b), not either, and (b) is the column this test just proved is "
        "computed"
    )
    for label in personas.PERSONAS:
        assert f"({personas.BASE_ROW}, {label})" in verdict, (
            f"item (b) omits cell (base, {label}) — all three are required"
        )


def test_signs_use_the_question_unit(monkeypatch):
    """STAT-01 / RESEARCH F-11 — the sign follows the QUESTION rate, on a discriminating fixture.

    ``fact_signs`` reads ``["rate"]`` off whatever dict it is handed and Phase 16's per-fact
    aggregation puts the DRAW rate there. A fixture where the two units agree proves nothing, so
    this one is built to ORDER THEM DIFFERENTLY: adapter A answers with its own value on exactly
    one draw of every question, and with B's value on all remaining draws of two questions in three.
    The question rate then puts the diagonal ABOVE the off-diagonal and the draw rate puts it BELOW.
    """

    def adapter_a(slot, index, draw):
        if draw == 0:
            return f"i go by {VALUES[slot]['persona_a']} truly"
        if index < _QUESTIONS_PER_SLOT - 1:
            return f"i go by {VALUES[slot]['persona_b']} truly"
        return _silent(slot, index, draw)

    records = _records(
        persona_a=adapter_a,
        persona_b=_says("persona_b"),
        persona_c=_says("persona_c"),
        base=_silent,
    )
    matrix, _described, _base_texts = _assemble(records)
    diagonal = matrix[("persona_a", "persona_a")]
    off = matrix[("persona_a", "persona_b")]

    # The fixture is DISCRIMINATING — asserted, not assumed. The draw rate is recomputed here from
    # the raw completions because `assemble_matrix` deliberately does not make it representable.
    def draw_rate(record, label):
        hits = sum(
            1
            for entry in record[iso.SWEEP_QUESTIONS_KEY]
            for completion in entry["completions"]
            if iso.score_completion(completion, VALUES[entry["slot"]]) >= {label}
        )
        return hits / sum(len(e["completions"]) for e in record[iso.SWEEP_QUESTIONS_KEY])

    row_a = records[iso.SWEEPS.index("persona_a")]
    question_order = diagonal["rate"] > off["rate"]
    draw_order = draw_rate(row_a, "persona_a") > draw_rate(row_a, "persona_b")
    assert question_order and not draw_order, (
        f"the fixture does not separate the units: question rates "
        f"{diagonal['rate']:.6f} vs {off['rate']:.6f}, draw rates "
        f"{draw_rate(row_a, 'persona_a'):.6f} vs {draw_rate(row_a, 'persona_b'):.6f}. A fixture "
        "where both units agree cannot tell which one the gate used"
    )

    gate = iso.compare_cells(iso.cell_rates(matrix))
    pair = (("persona_a", "persona_a"), ("persona_a", "persona_b"))
    assert gate["signs"][pair] == (1,) * persistence.SIGN_TEST_N, (
        f"the slot signs are {gate['signs'][pair]} — under the DRAW rate every one of them would "
        "be -1 and this comparison would score p = 1.0, so the gate is running on a unit nobody "
        "pre-registered"
    )
    assert gate["p_values"][pair] == UNANIMITY_P

    # The same fixture, run through the SAME gate on the draw unit — the counterfactual, computed
    # rather than argued. A source mutation that swaps the assembly to the draw rate also trips
    # `report_proportion`'s own "successes outside [0, n] questions" guard, so without this the
    # p-value flip would be inferred instead of observed.
    def draw_rates(record, label):
        by_slot = {}
        for entry in record[iso.SWEEP_QUESTIONS_KEY]:
            hits = sum(
                1
                for completion in entry["completions"]
                if iso.score_completion(completion, VALUES[entry["slot"]]) >= {label}
            )
            counted = by_slot.setdefault(entry["slot"], [0, 0])
            counted[0] += hits
            counted[1] += len(entry["completions"])
        return {slot: {"rate": hits / total} for slot, (hits, total) in by_slot.items()}

    draw_unit = {
        (row, label): draw_rates(records[iso.SWEEPS.index(row)], label)
        for row in personas.PERSONAS
        for label in personas.PERSONAS
    }
    assert iso.compare_cells(draw_unit)["p_values"][pair] == 1.0, (
        "on the DRAW unit this fixture does not flip the verdict, so it cannot witness which unit "
        "the gate ran on"
    )

    assert personas.SIGN_UNIT == "question"
    monkeypatch.setattr(iso.personas, "SIGN_UNIT", "draw")
    try:
        iso.compare_cells(iso.cell_rates(matrix))
    except SystemExit as exit_:
        assert "STAT-01" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError(
            "compare_cells does not _prove the computed unit against the committed SIGN_UNIT "
            "literal, so a silent revert to the draw rate would publish without going red"
        )


def test_no_bare_zero_percent(monkeypatch, tmp_path):
    """STAT-02 — no bare zero percentage, in any Phase 17 driver source OR in a rendered report.

    The source scan is ``tests/test_phase16_driver.py``'s regex applied to all four drivers; the
    rendered scan is the half a source scan structurally cannot do, because a format string
    produces the number the reader actually sees. A zero rate printed without its denominator and
    its ceiling states a certainty this sample does not have.
    """
    _collapsed_glob_guard()
    for module in _GATE_MODULES:
        assert re.search(r"\b0(\.0+)?%", module.read_text(encoding="utf-8")) is None, (
            f"{module.name} types a bare zero percentage"
        )

    # The all-zero off-diagonal fixture: this phase's HOPED-FOR outcome, and the one that would
    # most tempt a bare zero.
    text, matrix, _gate = _render(_clean_records(), monkeypatch, tmp_path)
    assert matrix[("persona_a", "persona_b")]["n_answerable"] == 0, "the fixture is not all-zero"
    assert re.search(r"\b0(\.0+)?%", text) is None, "the rendered report prints a bare zero"


def test_zero_cells_carry_both_clustering_ends(monkeypatch, tmp_path):
    """STAT-02 — a zero is published at BOTH ends of the clustering assumption, and labelled.

    The question-level rule of three treats the questions as independent (13 cluster inside each
    slot on the real tier) and is the OPTIMISTIC end; the slot-level bound treats each slot as one
    observation and is the CONSERVATIVE end. Publishing only one is publishing the end that
    flatters the claim, and this phase's headline IS a set of zeros. The two bounds are derived
    from the fixture rather than typed, so a fixture of a different size cannot make this pass on a
    number the report never printed.
    """
    text, matrix, _gate = _render(_clean_records(), monkeypatch, tmp_path)
    n_questions = matrix[("persona_a", "persona_b")]["n_questions"]

    question_end = f"3/{n_questions} = {persistence.rule_of_three(n_questions):.6f}"
    slot_end = (
        f"3/{personas.SLOTS_EXPECTED} = {persistence.rule_of_three(personas.SLOTS_EXPECTED):.6f}"
    )
    matrix_section = _section(text, "## The Matrix")
    for end, name in ((question_end, "question-level"), (slot_end, "slot-level")):
        assert f"{end} ({name})" in matrix_section, (
            f"§The Matrix does not carry the {name} rule-of-three bound {end!r}"
        )
    assert "ends of the clustering assumption" in matrix_section, (
        "the two bounds are printed without the label naming them as the two ENDS of the "
        "clustering assumption, so a reader has no way to know which is optimistic"
    )


def test_all_fail_branch(monkeypatch, tmp_path):
    """D-10 / D-11 — the branch is a committed literal, it fires at five of six, and only there."""
    assert "not judgeable" in personas.ALL_FAIL_BRANCH
    assert "never a ranking" in personas.ALL_FAIL_BRANCH, (
        "the committed branch lost D-15's no-ranking sentence — with one seed per persona a "
        "between-persona difference confounds content with initialization"
    )

    cleared_text, _matrix, cleared_gate = _render(_clean_records(), monkeypatch, tmp_path)
    assert cleared_gate["cleared"] is True
    assert personas.ALL_FAIL_BRANCH not in cleared_text, (
        "the all-fail branch was emitted on a cleared gate"
    )

    text, matrix, gate = _render(_tied_records(), monkeypatch, tmp_path)
    assert sum(1 for row in gate["holm"] if row[-1]) == len(personas.HOLM_FAMILY_CELLS) - 1
    assert gate["cleared"] is False
    assert len(gate["holm"]) == len(personas.HOLM_FAMILY_CELLS), (
        "all six rows are published whatever the outcome — publishing the rows is not the same as "
        "clearing the gate (D-18)"
    )
    assert personas.ALL_FAIL_BRANCH in text, "the pre-registered branch was not emitted in full"

    verdict = _verdict.recorded_verdict(text)
    assert verdict is not None
    for label in personas.PERSONAS:
        assert f"({label}, {label})" in verdict, f"item (a) omits persona {label}'s diagonal"
        assert f"({personas.BASE_ROW}, {label})" in verdict, f"item (b) omits cell (base, {label})"
    for phrase in ("D-11", "instrument-blind", "phenomenon-absent"):
        assert phrase in verdict, (
            f"the verdict does not carry {phrase!r} — 17-CONTEXT records D-11 as a milestone "
            "pattern to note wherever it recurs, and this branch is Phase 17's recurrence"
        )
    assert "0.865385" in verdict and "0.3483" in verdict, (
        "the fork is not decidable without the cross-phase anchors, each labelled with its unit"
    )

    for case in (cleared_text, text):
        replication = _section(case, "## Replication (ISO-05)")
        pending = [line for line in replication.splitlines() if "not yet measured" in line]
        assert len(pending) == 1, (
            f"§Replication carries {len(pending)} placeholder lines — plan 17-10 Task 3 replaces "
            "EXACTLY one and asserts everything else is byte-identical"
        )


def test_report_refuses_a_clobber(monkeypatch, tmp_path):
    """TH-17-28 — a recorded verdict is committed evidence, refused BEFORE a record is read.

    The sweep directory is left EMPTY on purpose: if the clobber guard ran anywhere but first, the
    abort would name a missing sweep record instead, and the guard would be firing after the work
    it exists to protect had already been redone.
    """
    report = tmp_path / "report.md"
    report.write_text("# x\n\n## Verdict\n\nGO — isolation demonstrated.\n", encoding="utf-8")
    monkeypatch.setattr(iso, "ISOLATION_REPORT_PATH", report)
    monkeypatch.setattr(iso, "SWEEP_RECORD_DIR", tmp_path / "empty")

    try:
        iso.run_report_mode()
    except SystemExit as exit_:
        assert "already carries a recorded verdict" in str(exit_), (
            f"the report mode aborted for the wrong reason — the clobber guard must run FIRST: "
            f"{exit_}"
        )
    else:  # pragma: no cover
        raise AssertionError("run_report_mode overwrote a recorded verdict")

    report.write_text("# x\n\n## Verdict\n\nPENDING\n", encoding="utf-8")
    try:
        iso.run_report_mode()
    except SystemExit as exit_:
        assert "is missing" in str(exit_), (
            "a PENDING verdict is not a recorded one and must not be refused as a clobber"
        )
    else:  # pragma: no cover
        raise AssertionError("the report mode found four sweep records in an empty directory")
