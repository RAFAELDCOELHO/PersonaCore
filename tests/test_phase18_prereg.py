"""Phase 18's pre-registration guards — the static clean room, D-31's arithmetic, D-27's pin.

CPU-only, GPU-free, no checkpoint I/O, no generation, no model load.
``scripts/phase18_extraction.py`` executes nothing at import beyond its ``sys.path`` bootstrap and
D-31's reachability proof, so an ``importlib.util.spec_from_file_location`` load here runs no
``__main__`` guard, no tokenizer and no model — and ``test_nothing_loads_at_import`` below is what
turns that sentence from a docstring claim into a checked fact, rather than the other way round.

What is pinned here:

  1. **D-03 (static layer)** — no Phase 18 module holds a locked or soft fact value in ANY string
     it carries, docstrings included. ``embedded_fact_values`` is CALLED from
     ``tests/test_phase14_scoring.py``, never forked: a duplicated rule is a rule that can drift,
     and the leak shape Phase 14 actually found was a value quoted inside a report paragraph,
     invisible to the whole-string equality the predicate used to use.
  2. **D-31** — the Holm family is m = 4, DERIVED from the four dose-split family names, and the
     reachability inequality holds at m = 4 while a 7-member family raises. The pinned driver runs
     that proof at import; this asserts both ends of it, including the failing one.
  3. **D-27** — ``scripts/erasure_gate.py`` is byte-untouched since ``23a830c``. Its entire
     evidentiary value is that it predates every v3.0 number, so an edit is exactly the shape the
     STAT-05 ancestry machinery exists to redden.
  4. The inertness the other three depend on: the only calls this driver makes at module scope are
     its bootstrap, its derived best-achievable p, and D-31's proof.

The module set is DERIVED from a ``phase18_*.py`` glob rather than hand-listed (Phase 17 D-21's
register), so every driver a later plan adds enters these scans the moment it exists — a
hand-listed tuple would leave each new file silently uncovered, which is the exact blindness this
pattern was introduced to close. ``_collapsed_glob_guard()`` runs FIRST in every glob-driven test
below, because a glob that stops matching makes each of them green over nothing.
"""

import ast
import importlib.util
import pathlib
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_EXTRACTION_PATH = _REPO_ROOT / "scripts" / "phase18_extraction.py"

# DERIVED from a glob, never a hand-listed tuple (Phase 17 D-21). Every `scripts/phase18_*.py` a
# later plan creates enters every scan below the moment its plan commits it.
_GATE_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("phase18_*.py")))

# Already in `sys.modules` — the driver imports it for HOLM_ALPHA and the sign test — so this is a
# cache hit rather than a second execution.
import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)


def _collapsed_glob_guard():
    """A glob that stops matching makes every scan below green over nothing."""
    assert len(_GATE_MODULES) >= 1, (
        f"the phase18_*.py glob collapsed to {len(_GATE_MODULES)} file(s) — a broken glob makes "
        "every static guard in this module green while scanning no source at all"
    )


def _load(name, path):
    """Load a module by path — safe here precisely because these drivers are inert at import."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _enclosing_functions(tree):
    """``node -> the innermost FunctionDef containing it``, or ``None`` for module scope.

    Module scope is recorded as ``None`` rather than dropped, because module scope is the most
    dangerous placement there is. Byte-for-byte the idiom
    ``tests/test_phase17_stats.py::_enclosing_functions`` uses.
    """
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            inner = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[child] = current if inner is child else inner
            walk(child, inner)

    walk(tree, None)
    return owner


def test_no_fact_values_in_phase18_modules():
    """D-03's STATIC layer: no Phase 18 module embeds a fact value, docstrings included.

    This is one of TWO independent guards and is not a repair of the other.
    ``phase14_recall.assert_no_value_in_prompt`` is the RUNTIME guard, checked per prompt against
    the bytes the model receives; it was already substring-aware and was never the equality bug.
    This one is STATIC and per module: it scans every string a committed driver holds — attributes,
    strings nested in its containers, and the docstrings of every object it defines — so an attack
    template cannot embed a value in source, and a docstring EXPLAINING the fact set cannot embed
    one either. Phase 18 needs both layers, because a template that quotes a value to describe
    itself falsifies the clean-room claim at the moment it is demonstrated.

    ``embedded_fact_values`` is imported, never forked (the same register
    ``tests/test_phase16_driver.py`` and ``tests/test_phase16_ladder.py`` already use). Both
    imports are function-local: ``test_phase14_scoring`` pulls torch, and the fact set is the very
    material this scan exists to keep out of the import surface.
    """
    _collapsed_glob_guard()
    from test_phase14_scoring import embedded_fact_values

    facts = _load("phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py")
    forbidden = tuple(f.value for f in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS)
    assert len(forbidden) == 10, (
        f"the forbidden set is {len(forbidden)} values, not the 8 locked plus 2 soft — no tier is "
        "exempt from this scan, and a shrunken set would narrow it silently"
    )

    for path in _GATE_MODULES:
        module = _load(path.stem, path)
        hits = embedded_fact_values(module, forbidden)
        assert hits == [], (
            f"scripts/{path.name} embeds fact value(s) {[value for value, _ in hits]} in a string "
            f"it holds (counts: {hits}). A locked value in an attack template — or in a docstring "
            "explaining the fact set — falsifies the clean-room claim at the moment it is "
            "demonstrated, and containment rather than equality is what makes a value quoted "
            "inside a paragraph visible here"
        )


def test_holm_family_is_reachable():
    """D-31 — m = 4 clears, m = 7 cannot, and the proof runs at IMPORT rather than after 8.2h.

    Three things are asserted, and the third is the one that matters. That the family is four
    dose-split members. That the pinned driver CALLS the proof at module scope — read off the AST,
    never grepped, because a text match would be equally happy inside a comment or a docstring
    describing the call. And that the inequality actually bites: a 7-member family at the same
    alpha and the same best achievable p raises ``SystemExit``. A guard nobody has watched fail is
    a guard nobody has verified, and this one's whole value is failing in seconds instead of after
    the two-arm run has been spent.

    ``BEST_ACHIEVABLE_P`` is compared against the committed instrument rather than a typed
    constant: the number the gate is priced against must be whatever ``sign_test_exact`` returns at
    the committed n, or the pricing and the test are two copies free to disagree.
    """
    extraction = _load("phase18_extraction", _EXTRACTION_PATH)

    assert len(extraction.HOLM_FAMILY) == 4, (
        f"the Holm family is sized {len(extraction.HOLM_FAMILY)}, but D-31 fixes m = 4 over the "
        f"dose-split families {extraction.ATTACK_FAMILIES}"
    )
    assert extraction.HOLM_FAMILY == extraction.ATTACK_FAMILIES, (
        "HOLM_FAMILY is not the family tuple itself — a retyped family size is a size that can "
        "stop agreeing with the families it prices"
    )
    assert extraction.BEST_ACHIEVABLE_P == persistence.sign_test_exact(
        (1,) * persistence.SIGN_TEST_N
    ), "BEST_ACHIEVABLE_P has drifted from the committed sign test at the committed n"

    module_scope_proofs = [
        node
        for node in _tree(_EXTRACTION_PATH).body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and getattr(node.value.func, "id", None) == "assert_holm_family_reachable"
    ]
    assert len(module_scope_proofs) == 1, (
        f"found {len(module_scope_proofs)} module-scope calls to assert_holm_family_reachable in "
        f"{_EXTRACTION_PATH.name}, expected exactly one. Inside a function it would run only when "
        "something chose to call it, which is after the budget is already committed"
    )

    # m = 4: the pinned family clears, by 60%.
    step_alpha = extraction.assert_holm_family_reachable(
        extraction.HOLM_FAMILY, persistence.HOLM_ALPHA, extraction.BEST_ACHIEVABLE_P
    )
    assert step_alpha > extraction.BEST_ACHIEVABLE_P

    # m = 6: still clears, but by the ~0.0005 razor margin Phases 16 and 17 already paid for —
    # asserted so the reason m = 4 was chosen over m = 6 is a measured margin, not a preference.
    razor = extraction.assert_holm_family_reachable(
        ("a", "b", "c", "d", "e", "f"), persistence.HOLM_ALPHA, extraction.BEST_ACHIEVABLE_P
    )
    assert 0 < razor - extraction.BEST_ACHIEVABLE_P < 0.001, (
        f"the m = 6 margin is {razor - extraction.BEST_ACHIEVABLE_P}, which is no longer the razor "
        "D-31 rejected — the arithmetic behind choosing m = 4 has moved"
    )

    # m = 7: unreachable at EVERY outcome, including perfect unanimity. This is the mutation proof.
    with pytest.raises(SystemExit) as excinfo:
        extraction.assert_holm_family_reachable(
            tuple("abcdefg"), persistence.HOLM_ALPHA, extraction.BEST_ACHIEVABLE_P
        )
    assert "PROOF FAILED" in str(excinfo.value) and "m = 7" in str(excinfo.value), (
        f"the m = 7 abort does not name the family size it refused: {excinfo.value}"
    )


def test_erasure_gate_untouched():
    """D-27 — ``scripts/erasure_gate.py`` is byte-identical to its pre-registration commit.

    Its entire evidentiary value is that it predates every v3.0 number: it states, in prose written
    blind, what would make selective erasure worth attempting and what erasure would have to
    achieve. Phase 18 MIRRORS its shape — ``null_result_is_admissible`` copies the keyword-only
    signature, the ``(verdict, reasons)`` return and the INCONCLUSIVE precedence — and mirroring is
    the whole of the permitted interaction. Editing it to make Phase 18's output fit its interface
    would retroactively convert a blind pre-registration into one shaped by the numbers it judges.

    Checked at BOTH levels, and the second is not redundant. HISTORY: the file has exactly one
    commit, so nothing has been layered on top of the pin. CONTENT: the bytes on disk — which are
    the bytes the interpreter actually imports — equal the bytes at that commit, which is what
    catches an uncommitted local edit that a history-only check would sail straight past.
    """
    from test_phase16_prereg import PREREG_ARTIFACT, PREREG_COMMIT

    commits = subprocess.run(
        ("git", "log", "--format=%H", "--", PREREG_ARTIFACT),
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert commits == [PREREG_COMMIT], (
        f"{PREREG_ARTIFACT} has commits {commits}, but D-27 requires exactly the pre-registration "
        f"commit {PREREG_COMMIT} and nothing after it. A later edit is precisely the shape the "
        "STAT-05 ancestry guard exists to redden"
    )

    pinned = subprocess.run(
        ("git", "show", f"{PREREG_COMMIT}:{PREREG_ARTIFACT}"),
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    assert pinned, f"git show returned no bytes for {PREREG_ARTIFACT} at {PREREG_COMMIT}"
    assert (_REPO_ROOT / PREREG_ARTIFACT).read_bytes() == pinned, (
        f"{PREREG_ARTIFACT} on disk differs from its content at {PREREG_COMMIT} — the file the "
        "suite imports is not the file that was pre-registered, and every claim resting on that "
        "ordering is void"
    )


# The complete allowlist of calls the pinned driver makes at MODULE SCOPE, as `ast.unparse` renders
# each callee. HARD EQUALITY, the `PERSONA_ALLOWLIST` register: an entry with no matching call site
# is as red as an unlisted call. Three of these are the file's reason to exist and the other three
# are the `sys.path` bootstrap's own primitives; a `torch.load`, a `from_json` or a `json.loads`
# arriving at module scope turns this red on the commit that adds it.
_IMPORT_TIME_CALLEES = (
    "assert_holm_family_reachable",  # D-31's proof — this is what must run at import
    "pathlib.Path",  # _REPO_ROOT
    "pathlib.Path(__file__).resolve",  # _REPO_ROOT
    "persistence.sign_test_exact",  # BEST_ACHIEVABLE_P, derived from the instrument
    "str",  # the sys.path bootstrap's guard and its argument
    "sys.path.insert",  # the ONE permitted module-level side effect
)


def test_nothing_loads_at_import():
    """The driver's own claim, pinned: importing it loads no checkpoint, tokenizer or model.

    Every CPU-only test in this file loads the pin with ``importlib`` on the strength of that
    claim, and a later plan's ``main()`` will read a 55.6 MB checkpoint and generate — so the claim
    has to be a property of the file rather than a paragraph in it.

    Written as a walk to module SCOPE and over EVERY ``Call`` node, not only statement-level ones.
    A scan restricted to ``tree.body`` finds nothing, because the bootstrap is nested inside an
    ``if``; a scan restricted to discarded-result calls would miss the shape that actually matters
    here, which is a load hiding on the right-hand side of a module-level assignment.
    ``torch`` is deliberately NOT asserted absent: ``phase16_persistence`` legitimately pulls it in
    through its own sibling imports, and an assertion this file cannot honour would be deleted at
    the first inconvenience rather than obeyed.
    """
    tree = _tree(_EXTRACTION_PATH)
    enclosing = _enclosing_functions(tree)
    callees = sorted(
        {
            ast.unparse(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and enclosing.get(node) is None
        }
    )
    assert callees == sorted(_IMPORT_TIME_CALLEES), (
        f"{_EXTRACTION_PATH.name} calls {callees} at module scope; the pre-registration permits "
        f"exactly {sorted(_IMPORT_TIME_CALLEES)}. Anything else runs on every importlib load in "
        "this suite, and a checkpoint or tokenizer read there would make the pin untestable on CPU "
        "and would preview run behaviour the D-04 ordering forbids"
    )
