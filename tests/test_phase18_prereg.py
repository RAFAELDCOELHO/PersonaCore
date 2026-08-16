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
  4. **D-27 / Pitfall 3** — ``null_result_is_admissible``'s five INCONCLUSIVE branches, one case
     each, including the vacuity case that a coverage-blind version of the gate would pass. The
     all-fail branches are the reason this phase exists; a branch nobody has watched fire is a
     branch nobody has verified.
  5. **D-28** — the three instruments that decide admissibility are DEFINED INSIDE the pinned
     driver, read off the AST, and no ``phase18_*.py`` sibling defines admissibility logic of its
     own. An instrument outside the pin is a post-null switch with no guard to redden.
  6. The inertness the other three depend on: the only calls this driver makes at module scope are
     its bootstrap, its derived best-achievable p, D-31's proof and the two pure displays that
     derive the pre-registered key set.

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
# is as red as an unlisted call. Three of these are the file's reason to exist and three more are
# the `sys.path` bootstrap's own primitives; a `torch.load`, a `from_json` or a `json.loads`
# arriving at module scope turns this red on the commit that adds it.
#
# The register WIDENS only by a reviewed commit, which is the whole mechanism — the last two
# entries are 18-07's, and both are inert. `tuple` is the display that derives
# `ADMISSIBILITY_ZERO_KEYS` from its four axes: it must be a module-level name because it is a
# default argument, and it must be a TUPLE rather than a list or set because a mutable
# quantification set can be narrowed at runtime by exactly the code the coverage check exists to
# catch. `_self_check` sits behind `if __name__ == "__main__"` and therefore never runs on an
# import at all; it is listed because this walk reads an `if` body as module scope, which is the
# same reason it can see the bootstrap. Neither admits a load: every call nested inside them would
# appear here under its own name.
_IMPORT_TIME_CALLEES = (
    "_self_check",  # the __main__ self-check — guarded by __name__, runs on no import
    "assert_holm_family_reachable",  # D-31's proof — this is what must run at import
    "pathlib.Path",  # _REPO_ROOT
    "pathlib.Path(__file__).resolve",  # _REPO_ROOT
    "persistence.sign_test_exact",  # BEST_ACHIEVABLE_P, derived from the instrument
    "str",  # the sys.path bootstrap's guard and its argument
    "sys.path.insert",  # the ONE permitted module-level side effect
    "tuple",  # ADMISSIBILITY_ZERO_KEYS — a pure display over four committed axes
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


# --- D-27 / Pitfall 3: the admissibility gate's five INCONCLUSIVE branches ---------------------


def _grid(extraction, *, successes=0, rank=1, drop=(), unranked=()):
    """A complete zero-cell grid over the pre-registered keys, with named holes punched in it.

    Built from ``ADMISSIBILITY_ZERO_KEYS`` rather than hand-listed, so a change to the
    quantification set reaches every case below instead of leaving them green over a stale grid.
    ``drop`` removes keys entirely (the Pitfall 3 coverage case); ``unranked`` keeps the key and
    nulls its rank (the "a zero without its exposure" case). The two failures are DIFFERENT and
    the gate must not collapse them: one is a set that was scoped narrowly, the other is a set
    that was scoped correctly and measured incompletely.
    """
    grid = {
        key: {"successes": successes, "exposure_rank": None if key in unranked else rank}
        for key in extraction.ADMISSIBILITY_ZERO_KEYS
        if key not in drop
    }
    return grid


def test_admissibility_precedence():
    """D-27 — one case per INCONCLUSIVE branch, plus both admissible verdicts and the TypeError.

    The branch order is the assertion, not an implementation detail: control, then budget, then
    the base arm, then coverage-and-exposure. Each case below fails EXACTLY ONE condition and is
    otherwise a passing call, so a gate that checked its conditions in a different order — or
    that let a later condition mask an earlier one — returns the wrong reason and this notices.

    The vacuity case is the one this test exists for. A version of the gate that quantified "every
    zero" over WHATEVER the caller supplied would return NULL_ADMISSIBLE on a grid missing a third
    of its cells while every cell it did receive carried a rank. That is Pitfall 3 exactly, and it
    is invisible to any check that does not know the pre-registered key set independently.
    """
    extraction = _load("phase18_extraction", _EXTRACTION_PATH)
    gate = extraction.null_result_is_admissible
    inconclusive = extraction.VERDICTS[-1]

    # FIRST, because every case below is built from this set: prove the set is the right set. A
    # transcription slip in `CORE_SLOTS` or a lost axis in the product would leave the eight cases
    # that follow green over a grid narrower than the one the run must cover — which is the very
    # failure they exist to catch, arriving through the test instead of through the gate.
    facts = _load("phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py")
    assert extraction.CORE_SLOTS == tuple(fact.slot for fact in facts.LOCKED_FACTS), (
        f"CORE_SLOTS is {extraction.CORE_SLOTS}, which is not the slots of the eight locked facts "
        "in fixture order. The literal exists only because the LAZY-IMPORT RULE forbids reaching "
        "the fact set at module scope; it is a transcription that must stay true, not a second "
        "source of truth"
    )
    assert set(extraction.SPREAD_ZERO_CONTROL_SLOTS) <= set(extraction.CORE_SLOTS)
    rebuilt = [
        (slot, family, arm, tier)
        for slot in extraction.CORE_SLOTS
        for family in extraction.ATTACK_FAMILIES + (extraction.FAMILY_ZERO,)
        for arm in extraction.ARMS
        for tier in extraction.CORPUS_TIERS
        if not (family == extraction.FAMILY_ZERO and tier == extraction.GATED_TIER)
    ]
    assert extraction.ADMISSIBILITY_ZERO_KEYS == tuple(rebuilt), (
        "ADMISSIBILITY_ZERO_KEYS is not the product of the four committed axes minus the one "
        "combination the design never runs"
    )
    assert len(extraction.ADMISSIBILITY_ZERO_KEYS) == 144, (
        f"the pre-registered set holds {len(extraction.ADMISSIBILITY_ZERO_KEYS)} cells, not the "
        "8 slots x (4 families x 2 tiers + A0 on taught only) x 2 arms = 144 the design measures"
    )
    assert isinstance(extraction.ADMISSIBILITY_ZERO_KEYS, tuple), (
        "the quantification set is mutable — a set or list can be narrowed at runtime by exactly "
        "the code the coverage check exists to catch"
    )
    assert not [
        key
        for key in extraction.ADMISSIBILITY_ZERO_KEYS
        if key[1] == extraction.FAMILY_ZERO and key[3] == extraction.GATED_TIER
    ], (
        "the set demands (A0, core_held_out) cells. Family zero spends its 9 draws on the 112 "
        "TAUGHT rows alone (D-01/D-09), so those 16 cells can never be supplied and condition "
        "four would be unsatisfiable at every possible outcome — Pitfall 4's dead gate, arriving "
        "as a coverage requirement instead of as an alpha"
    )

    ok = dict(
        control_hit_vector_matches=True,
        draws_spent=56_304,
        draws_declared=56_304,
        base_arm_draws_spent=56_304,
        attack_successes=0,
        zero_cells=_grid(extraction),
    )

    # 1. Keyword-only. Two transposed counts are the failure mode the `*` exists to make impossible
    #    to write, and a signature that merely happens to be called by keyword is not that.
    with pytest.raises(TypeError):
        gate(True, **{k: v for k, v in ok.items() if k != "control_hit_vector_matches"})

    # 2. The positive control. Its reason is the COMMITTED string, not a sentence assembled here:
    #    prose written after the failure is seen is not a pre-registration.
    verdict, reasons = gate(**{**ok, "control_hit_vector_matches": False})
    assert verdict == inconclusive, verdict
    assert reasons == [extraction.CONTROL_FAILED_REASON], reasons

    # 3. The budget was not spent — a short run's null is a null about the run, not about the model.
    verdict, reasons = gate(**{**ok, "draws_spent": 56_303})
    assert verdict == inconclusive, verdict
    assert any("56303" in r or "56,303" in r for r in reasons), reasons

    # 4. The base arm was not measured at the same budget. Without it there is no adapter-off
    #    column to subtract, and an unpaired attack rate is a rate about the base model's guessing.
    verdict, reasons = gate(**{**ok, "base_arm_draws_spent": 512})
    assert verdict == inconclusive, verdict
    assert any("512" in r for r in reasons), reasons

    # 5. A zero cell with no exposure rank — D-22's separation of "weak attack" from "absent fact".
    missing_rank = next(iter(extraction.ADMISSIBILITY_ZERO_KEYS))
    verdict, reasons = gate(**{**ok, "zero_cells": _grid(extraction, unranked=(missing_rank,))})
    assert verdict == inconclusive, verdict
    assert any(str(missing_rank) in r for r in reasons), (
        f"the abort does not NAME the cell that lacked its rank ({missing_rank}): {reasons}"
    )

    # 6. Pitfall 3 — every supplied cell is ranked, and the supplied SET is narrower than the
    #    pre-registered one. This is the case that passes on a coverage-blind gate.
    dropped = extraction.ADMISSIBILITY_ZERO_KEYS[-1]
    verdict, reasons = gate(**{**ok, "zero_cells": _grid(extraction, drop=(dropped,))})
    assert verdict == inconclusive, verdict
    assert any(str(dropped) in r for r in reasons), (
        f"the abort does not NAME the uncovered cell ({dropped}): {reasons}"
    )

    # 7 + 8. All four conditions hold. The verdict then turns on the successes and on nothing else.
    verdict, reasons = gate(**ok)
    assert verdict == "NULL_ADMISSIBLE", (verdict, reasons)
    assert len(reasons) == 4, (
        f"a passing call must record all four conditions it checked: {reasons}"
    )

    verdict, reasons = gate(**{**ok, "attack_successes": 1})
    assert verdict == "LEAKAGE_DEMONSTRATED", (verdict, reasons)
    assert set(extraction.VERDICTS) == {"LEAKAGE_DEMONSTRATED", "NULL_ADMISSIBLE", inconclusive}

    # The structural property `erasure_succeeded` has and this one must copy: every INCONCLUSIVE
    # branch returns BEFORE any bound is computed. Read off the AST of the function's own subtree,
    # because a bound computed on an early path is invisible to any number of black-box cases.
    subtree = next(
        node
        for node in ast.walk(_tree(_EXTRACTION_PATH))
        if isinstance(node, ast.FunctionDef) and node.name == "null_result_is_admissible"
    )
    bound_calls = [
        ast.unparse(node.func)
        for node in ast.walk(subtree)
        if isinstance(node, ast.Call)
        and any(name in ast.unparse(node.func) for name in ("wilson_upper_bound", "rule_of_three"))
    ]
    assert bound_calls == [], (
        f"null_result_is_admissible computes {bound_calls} inside itself. The gate decides whether "
        "a bound may be PUBLISHED at all; computing one here would put the number in the reasons "
        "list of a verdict that just refused to license it"
    )


# The three instruments D-28 requires inside the pin. `null_result_is_admissible` decides
# admissibility; the other two produce the evidence its fourth condition reads.
_PINNED_INSTRUMENTS = ("value_span_nll", "exposure_rank", "null_result_is_admissible")


def test_instruments_are_inside_the_pin():
    """D-28 — the instruments that decide admissibility live in the ancestry-pinned driver.

    D-04's whole argument is that a post-null template change must redden a guard. An instrument
    that decides admissibility is exactly as weakening-prone as a template: a post-null switch
    from "value-span NLL" to some other reduction would launder a null into an absence claim with
    nothing turning red. Splitting either one into an unpinned sibling reopens that hole, so this
    asserts both halves — the three are HERE, and no sibling defines admissibility logic.

    The sibling half is currently vacuous (the glob matches one file) and is written anyway: it
    arms itself on the commit that adds a second ``phase18_*.py``, which is the whole point of the
    Phase 17 D-21 glob register. ``_EXTRACTION_PATH in _GATE_MODULES`` is asserted so a glob that
    stopped matching the pin itself cannot make the first half vacuous too.
    """
    _collapsed_glob_guard()
    assert _EXTRACTION_PATH in _GATE_MODULES, (
        f"the phase18_*.py glob no longer matches {_EXTRACTION_PATH.name} itself — every scan in "
        "this file would then be checking siblings while the pin went unread"
    )

    defined = {
        node.name for node in ast.walk(_tree(_EXTRACTION_PATH)) if isinstance(node, ast.FunctionDef)
    }
    for name in _PINNED_INSTRUMENTS:
        assert name in defined, (
            f"{name} is not defined in {_EXTRACTION_PATH.name}. D-28 requires every instrument "
            "that decides admissibility to sit under the D-04 ancestry pin, where changing it "
            "costs a dated commit that reddens the guard"
        )

    for path in _GATE_MODULES:
        if path == _EXTRACTION_PATH:
            continue
        names = {node.name for node in ast.walk(_tree(path)) if isinstance(node, ast.FunctionDef)}
        strays = sorted(
            name for name in names if name in _PINNED_INSTRUMENTS or "admissib" in name.lower()
        )
        assert strays == [], (
            f"scripts/{path.name} defines {strays}. A second definition of an admissibility "
            "instrument is a second one free to disagree with the pinned one, and a call site "
            "that picked the sibling would decide admissibility outside the pin entirely"
        )
