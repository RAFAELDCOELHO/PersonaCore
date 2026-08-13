"""PERS-01 capability-ladder pre-registration — the constants, their derivation, and the licence.

CPU-only, torch-free, no checkpoint I/O, no model load, no generation. Nothing in this file may
require a GPU, and nothing in it may import ``phase14_factset`` at module scope (LAZY-IMPORT RULE:
the locked fact strings stay out of this file's address space; a test that needs them loads them
inside the function).

What is pinned here:
  1. ``test_factset_gate_exposes_a_public_guessability_probe`` — D-16's widened public surface on
     ``scripts/phase14_factset_gate.py``, asserted against the parsed AST rather than an executed
     import, because importing that module pulls torch AND the locked fact set into the process.
"""

import ast
import pathlib

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _parse(relative_path):
    """The parsed AST of a repo file. Parsing, never importing: see the module docstring."""
    return ast.parse((_REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _function_def(tree, name):
    """The module-level ``def name`` in a parsed tree, or ``None``."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _called_names(node):
    """Every callee name reachable inside ``node`` — bare ``f()`` and attribute ``m.f()`` alike."""
    names = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            names.add(getattr(inner.func, "id", None) or getattr(inner.func, "attr", None))
    return names


# ===== Task 1 — D-16: the widened public guessability surface ================================


def test_factset_gate_exposes_a_public_guessability_probe():
    """D-16: ``phase14_factset_gate`` exposes a probe taking an ARBITRARY string.

    Before this, the module exposed only ``main()`` and private helpers, so Phase 16 and Phase 17
    could reach the guessability rule only by copying it — which D-16 forbids and which would
    create a second rule free to drift from this one. ISO-01's precedent, stated as a rule: import
    the instrument, never copy it.

    Asserted against the parsed AST, not an executed import: this module does
    ``import phase14_factset as fs`` at module level, so importing it here would pull the locked
    fact strings into the test process and defeat the clean-room scan the rest of this suite runs.

    The signature IS the contract — ``value`` is a plain required parameter (a default would let a
    caller probe nothing), and ``start_index`` is keyword-only because it offsets generator seeding
    and must never be able to slide positionally into the ``questions`` slot.
    """
    tree = _parse("scripts/phase14_factset_gate.py")
    fn = _function_def(tree, "probe_guessability")
    assert fn is not None, "probe_guessability is missing — D-16's widening is the point of Task 1"
    assert not fn.name.startswith("_"), "the whole point is a PUBLIC entry point"

    assert [a.arg for a in fn.args.args] == [
        "model",
        "tok",
        "device",
        "forbid",
        "value",
        "questions",
    ], [a.arg for a in fn.args.args]
    assert [a.arg for a in fn.args.kwonlyargs] == ["start_index"]

    defaulted = {a.arg for a in fn.args.args[len(fn.args.args) - len(fn.args.defaults) :]}
    assert "value" not in defaulted, "a default value would let a caller probe nothing by accident"
    assert "questions" not in defaulted

    called = _called_names(fn)
    assert "_probe" in called, (
        "probe_guessability must DELEGATE to _probe — one probe implementation, or the seeding, "
        "the stop-id set and the prompt builder can diverge between the two entry points"
    )
    assert "Generator" not in called, (
        "no second torch.Generator construction here: per-probe seeding belongs to _probe"
    )
    assert "exact_match_clean" in called, "the objective half of the D-03 rule stays the scorer"
