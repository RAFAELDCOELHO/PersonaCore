"""Four-arm comparison driver — the PRE-REGISTRATION pins (PERS-02 / PERS-04).

CPU-only, GPU-free, no checkpoint I/O, no generation. ``scripts/phase16_persistence.py`` executes
nothing at import — constants and pure functions only — so an
``importlib.util.spec_from_file_location`` load here runs no guard, no model load and no
tokenizer load. It DOES pull torch transitively (through ``phase14_recall``, which is where the
committed arm functions and the parity constants live), which is the point: the parity fields are
READ off the instrument rather than retyped beside it.

What is pinned here:
  1. ``CONDITION_ORDER`` and its rationale — the four locked names in the locked order, the D-03
     sentence byte-identical to ``16-CONTEXT.md``, and the ABSENCE of the deleted rationale.
  2. ``SHARED_ARM_CONFIG`` — one object, its four scalar fields read by identity, and ``forbid``
     deliberately absent from it (it needs a loaded tokenizer, so it cannot be an import-time
     constant).
  3. The fixture loader — 270 questions, the fixture's OWN seed indices, and the 14/13 per-core-fact
     balance D-06's denominator claim rests on.

The scripts-load justification is the one ``tests/test_phase14_scoring.py`` already states: the
pre-registration constants MUST live in the committed driver for git history to be the proof.
"""

import ast
import importlib.util
import pathlib
import re
import sys

import torch

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_DRIVER_PATH = _REPO_ROOT / "scripts" / "phase16_persistence.py"
_CONTEXT_PATH = (
    _REPO_ROOT
    / ".planning"
    / "phases"
    / "16-weight-vs-prompt-persistence-control"
    / "16-CONTEXT.md"
)


def _load_driver():
    spec = importlib.util.spec_from_file_location("phase16_persistence", _DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


driver = _load_driver()


def _driver_source():
    return _DRIVER_PATH.read_text(encoding="utf-8")


def _driver_tree():
    return ast.parse(_driver_source())


def _module_level_nodes(tree):
    """Every AST node reachable WITHOUT entering a ``def`` or ``class`` — import-time code."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield from ast.walk(node)


def _called_names(node):
    """Every callee name reachable inside ``node`` — bare ``f()`` and attribute ``m.f()`` alike."""
    names = set()
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            names.add(getattr(inner.func, "id", None) or getattr(inner.func, "attr", None))
    return names


def _function_def(tree, name):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _context_blockquote(anchor):
    """The blockquote immediately following ``anchor`` in ``16-CONTEXT.md``, unwrapped to one line.

    Read from the planning artifact rather than retyped here, because "verbatim" asserted against a
    second hand-typed copy proves only that two copies agree — which is exactly the failure mode a
    verbatim requirement exists to prevent.
    """
    body = _CONTEXT_PATH.read_text(encoding="utf-8").split(anchor, 1)[1]
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            lines.append(stripped.lstrip(">").strip())
        elif lines:
            break
    assert lines, f"no blockquote follows {anchor!r} in 16-CONTEXT.md"
    return " ".join(lines).strip('"')


# ===== 16-08 Task 1 — the pre-registration block ==============================================


def test_condition_order_is_locked():
    """D-03: exactly four names, in the locked order, as an immutable tuple.

    A list would be a pre-registration a later line could ``.append`` to; the whole value of this
    constant is that it cannot be arranged after a number is visible.
    """
    assert driver.CONDITION_ORDER == (
        "adapter-only",
        "base-neither",
        "embedding-cosine",
        "prompt-stuffed",
    )
    assert isinstance(driver.CONDITION_ORDER, tuple)
    assert len(set(driver.CONDITION_ORDER)) == 4


def test_condition_order_records_the_verbatim_pre_registration_sentence():
    """The D-03 sentence is byte-identical to ``16-CONTEXT.md``, and it is IN the rationale."""
    expected = _context_blockquote("- **D-03:**")
    assert driver.CONDITION_ORDER_PREREGISTRATION == expected
    assert expected in driver.CONDITION_ORDER_RATIONALE


def test_condition_order_records_exactly_two_reasons():
    """Two reasons, and the rationale says so — pre-registration, and interruption order."""
    rationale = driver.CONDITION_ORDER_RATIONALE
    assert "exactly two" in rationale
    assert "after seeing numbers" in rationale
    assert "adapter-only first" in rationale
    assert "under interruption" in rationale


def test_condition_order_does_not_carry_the_deleted_rationale():
    """The third rationale was DELETED, not annotated — so the driver must not contain its text.

    It defended against a mechanism the four-process split already eliminates. A false rationale
    left in an artifact is inherited downstream as true, and the cheapest place to stop that is
    before it is ever typed. The scan is the SOURCE, not the loaded module: a comment is as
    inheritable as a constant.
    """
    source = _driver_source().lower()
    assert "residual context-window" not in source
    assert "context-window risk" not in source


def test_sequential_justification_cites_both_sources():
    """D-02: BOTH citations, never one — the Phase 9 proofs are FIXTURE scope.

    Citing only the Phase 9 toggle tests would inherit a fixture-scope guarantee as a real-weights
    one, so the word ``fixture`` is required alongside them: it is the qualifier that makes the
    second citation necessary rather than decorative.
    """
    justification = driver.SEQUENTIAL_QUESTIONS_JUSTIFICATION
    assert "tests/test_lora_toggle.py" in justification
    assert "test_toggle_round_trip_bit_identity" in justification
    assert "test_adapter_disabled_preserves_prior_state" in justification
    assert "test_adapter_disabled_exception_safe" in justification
    assert "run_bit_identity_control" in justification
    assert "fixture" in justification
    assert "13.9M" in justification


def test_no_kv_cache_note_records_the_measurement():
    """D-04: the grep returned zero hits, which is WHY the process split is defence-in-depth."""
    note = driver.NO_KV_CACHE_NOTE
    assert "zero hits" in note
    assert "src/personacore/generation/" in note and "src/personacore/model/" in note
    assert "structurally impossible" in note


def test_all_arms_share_one_config_object():
    """PERS-02: the four SCALAR parity fields are resolved from ``SHARED_ARM_CONFIG`` by IDENTITY.

    Identity and not equality-against-a-re-derived-value, because four literals that agree today
    are four literals that can stop agreeing in one edit — and the disagreement is invisible in
    every number produced afterwards.

    ``shared_arm_config`` carries the object itself for the same reason: ``is`` on a small int is
    satisfied trivially by CPython interning, so the scalar checks alone would not detect a second
    ``ArmConfig`` instance built from retyped literals.
    """
    record = driver.arm_config_record(torch.zeros(1, 16, dtype=torch.bool))

    assert record["shared_arm_config"] is driver.SHARED_ARM_CONFIG
    assert record["max_new_tokens"] is driver.SHARED_ARM_CONFIG.max_new_tokens
    assert record["stop_ids"] is driver.SHARED_ARM_CONFIG.stop_ids
    assert record["context_length"] is driver.SHARED_ARM_CONFIG.context_length
    assert record["n_draws"] is driver.SHARED_ARM_CONFIG.n_draws

    # And the object's own fields are the committed instrument's, never retyped beside it.
    import phase14_recall as recall

    from personacore.config import ModelConfig

    assert driver.SHARED_ARM_CONFIG.max_new_tokens is recall.RECALL_MAX_NEW_TOKENS
    assert driver.SHARED_ARM_CONFIG.stop_ids is recall.STOP_IDS
    assert driver.SHARED_ARM_CONFIG.context_length == ModelConfig.block_size == 256
    assert driver.SHARED_ARM_CONFIG.n_draws == 1 + recall.N_SEEDED_SAMPLES == 9


def test_forbid_is_not_resolved_at_import():
    """``forbid`` cannot be an import-time constant, and the driver must not pretend otherwise.

    ``undecodable_ids_mask`` needs a LOADED tokenizer and returns a torch tensor. A module-level
    call would put a model-shaped dependency in the import path of every CPU-only test, and a
    module-level tensor would make the parity assertion compare something whose ``==`` is
    elementwise. The AST check is on import-time code specifically — the call inside
    ``resolve_forbid`` is the intended seam and must survive.
    """
    tree = _driver_tree()
    module_level = list(_module_level_nodes(tree))
    called = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in module_level
        if isinstance(node, ast.Call)
    }
    assert "undecodable_ids_mask" not in called
    assert "from_json" not in called
    assert "load_adapted_model" not in called

    # The intended seam still exists and still calls it.
    assert "undecodable_ids_mask" in _called_names(_function_def(tree, "resolve_forbid"))

    # No module attribute is a torch tensor — the import surface stays free of device state.
    tensors = [name for name in dir(driver) if torch.is_tensor(getattr(driver, name, None))]
    assert tensors == []


def test_driver_imports_the_fact_set_only_inside_functions():
    """LAZY-IMPORT RULE: neither the fact set nor the gate may be imported at module level.

    The gate imports the fact set at ITS module level, so either module-level edge would drag
    every locked value into this driver's address space — and into the docstring surface the
    clean-room scan walks.
    """
    module_level = list(_module_level_nodes(_driver_tree()))
    imported = set()
    for node in module_level:
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert "phase14_factset" not in imported
    assert "phase14_factset_gate" not in imported


def test_fixture_loader_yields_270_items_with_the_fixture_seed_indices():
    """The fixture IS the pairing key (PERS-02) — its seed indices are carried, never re-stamped.

    Re-stamping would silently REPAIR a mismatch instead of surfacing it, and a repaired mismatch
    is indistinguishable in every number downstream from a fixture that was never wrong.
    """
    import json

    by_tier = driver.load_fixture_items()
    assert sorted(by_tier) == ["core_held_out", "core_taught", "soft"]
    assert {tier: len(items) for tier, items in by_tier.items()} == driver.FIXTURE_TIER_COUNTS
    assert sum(len(items) for items in by_tier.values()) == 270

    fixture = json.loads(driver.FIXTURE_PATH.read_text(encoding="utf-8"))
    for tier, items in by_tier.items():
        entries = fixture["questions"][tier]
        assert [item.seed_index for item in items] == [e["seed_index"] for e in entries]
        assert [item.question for item in items] == [e["question"] for e in entries]
        assert [item.fact.id for item in items] == [e["fact_id"] for e in entries]
        assert all(item.seed_index >= 0 for item in items)

    # D-06's denominator claim rests on the balance holding EXACTLY, so it is pinned, not trusted.
    for tier, split, expected in (
        ("core_taught", "taught", 14),
        ("core_held_out", "held-out", 13),
    ):
        per_fact = {}
        for item in by_tier[tier]:
            per_fact[item.fact.id] = per_fact.get(item.fact.id, 0) + 1
        assert set(per_fact.values()) == {expected}
        assert len(per_fact) == 8
        assert {item.split for item in by_tier[tier]} == {split}

    # The soft tier carries both splits — it is 2 facts x (14 taught + 13 held-out).
    assert {item.split for item in by_tier["soft"]} == {"taught", "held-out"}


def test_persistence_driver_holds_no_fact_strings_at_import():
    """No locked or soft fact value reaches this driver, docstrings included.

    ``embedded_fact_values`` is reused verbatim from ``tests/test_phase14_scoring.py`` rather than
    re-implemented, for the reason that test already gives: it scans SUBSTRING containment over
    every string the module holds — attributes, strings nested in its containers, and docstrings —
    because the real leak Phase 14 found was a value quoted inside a report paragraph, invisible
    to whole-string equality.
    """
    from test_phase14_scoring import embedded_fact_values

    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(facts)

    forbidden = tuple(f.value for f in facts.LOCKED_FACTS + facts.SOFT_TIER_FACTS)
    assert len(forbidden) == 10  # all 8 locked + both soft — no tier is exempt from the scan
    assert embedded_fact_values(driver, forbidden) == []


def test_driver_never_renders_a_bare_zero_percent_literal():
    """STAT-02 hygiene, pinned at the source: no bare ``0%`` may be typed into this module.

    Cheap here, and it forecloses the shape plan 16-10 must not inherit — a zero rate printed
    without its denominator and its rule-of-three ceiling reads as proven absence.
    """
    assert re.search(r"\b0(\.0+)?%", _driver_source()) is None
