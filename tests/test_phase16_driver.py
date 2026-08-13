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


# ===== 16-08 Task 2 — arm dispatch onto the committed instrument ==============================


def _entry(fact_id="f1", split="taught", seed_index=0, k=1, n=9):
    return {"fact_id": fact_id, "split": split, "seed_index": seed_index, "k": k, "n": n}


def _stub_items():
    """Three tiers of one item each — enough for dispatch, and no fixture I/O."""
    import phase14_recall as recall

    class _Fact:
        id = "f1"
        slot = "person_name"
        value = "wibblex"

    return {
        tier: (recall.RecallItem(_Fact(), f"q {tier}", split, False, 0),)
        for tier, split in (
            ("core_taught", "taught"),
            ("core_held_out", "held-out"),
            ("soft", "taught"),
        )
    }


def _patch_arms(monkeypatch):
    """Replace every arm entry point with a recorder; returns the ``{name: call_count}`` map."""
    import phase14_recall as recall

    fired = {}

    def _record(name, returns):
        def _stub(*args, **kwargs):
            fired[name] = fired.get(name, 0) + 1
            return returns

        return _stub

    monkeypatch.setattr(recall, "set_adapter_enabled", lambda model, enabled: None)
    monkeypatch.setattr(
        recall,
        "run_scored_recall",
        _record("run_scored_recall", {"questions": [_entry()]}),
    )
    monkeypatch.setattr(
        recall,
        "run_closed_book_control",
        _record("run_closed_book_control", {"questions": [_entry()]}),
    )
    monkeypatch.setattr(
        recall,
        "run_fairness_control",
        _record("run_fairness_control", {"questions": [_entry()]}),
    )
    # `run_cosine_arm` and `candidate_pool` are this module's own (16-08 Task 3). `raising=False`
    # because Task 2's commit dispatches to them by a forward reference the next commit defines.
    monkeypatch.setattr(
        driver, "run_cosine_arm", _record("run_cosine_arm", [_entry()]), raising=False
    )
    monkeypatch.setattr(driver, "candidate_pool", lambda: ("a",), raising=False)
    monkeypatch.setattr(driver, "fairness_statements", lambda: {"f1": "a statement"})
    return fired


def test_run_condition_rejects_an_unknown_condition(monkeypatch):
    """An unrecognized arm ABORTS — it never falls through to whichever branch the code reaches.

    A default branch would produce a well-formed record for an arm nobody asked for, reported
    under the name that was asked for. The failure mode is a number, not an exception.
    """
    import pytest

    _patch_arms(monkeypatch)
    with pytest.raises(SystemExit):
        driver.run_condition("adapter-off", None, None, None, torch.zeros(1, 4), _stub_items())


def test_each_condition_dispatches_to_its_committed_function(monkeypatch):
    """Arms A, B and C are the COMMITTED Phase 14 functions invoked per condition, not rewrites."""
    fired = _patch_arms(monkeypatch)
    forbid = torch.zeros(1, 4, dtype=torch.bool)

    expected = {
        "adapter-only": "run_scored_recall",
        "base-neither": "run_closed_book_control",
        "prompt-stuffed": "run_fairness_control",
        "embedding-cosine": "run_cosine_arm",
    }
    for condition, name in expected.items():
        fired.clear()
        record = driver.run_condition(condition, None, None, None, forbid, _stub_items())
        assert set(fired) == {name}, f"{condition} fired {sorted(fired)}, expected only {name}"
        assert record["condition"] == condition

    # Arm A is scored per TIER, so its one call site fires once per tier — three tiers, three calls.
    fired.clear()
    driver.run_condition("adapter-only", None, None, None, forbid, _stub_items())
    assert fired == {"run_scored_recall": 3}


def test_driver_defines_no_draw_loop():
    """The driver contributes dispatch and a parity assertion — never a second draw loop.

    A duplicated draw loop is how two arms silently stop being paired, which is precisely the
    defect PERS-05 closed upstream in the shared instrument. Three checks, because the loop could
    arrive by three routes: calling ``draw_all`` directly, rebuilding the completion path, or
    iterating questions inside ``run_condition``.
    """
    tree = _driver_tree()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calls.add(getattr(node.func, "id", None) or getattr(node.func, "attr", None))
    assert "draw_all" not in calls
    assert "_complete" not in calls
    assert "complete_question" not in calls
    assert "generate" not in calls

    dispatch = _function_def(tree, "run_condition")
    assert dispatch is not None
    assert [n for n in ast.walk(dispatch) if isinstance(n, ast.For)] == [], (
        "run_condition holds a `for` statement — its whole job is dispatch; a loop over questions "
        "here is a second draw loop by another name"
    )
    # ...and it does call each committed arm function exactly once.
    called = [
        getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        for n in ast.walk(dispatch)
        if isinstance(n, ast.Call)
    ]
    for name in ("run_scored_recall", "run_closed_book_control", "run_fairness_control"):
        assert called.count(name) == 1, f"{name} is called {called.count(name)}x in run_condition"


def test_driver_adds_no_persona_call_site():
    """Arm B routes through the one allowlisted ``persona=`` call site — this driver adds none.

    ``tests/test_phase14_scoring.py``'s D-21 guard asserts hard equality against
    ``PERSONA_ALLOWLIST``, so a ``persona=`` here would turn that suite red. Asserted locally too,
    because the local failure names the file a reader is actually editing.
    """
    tree = _driver_tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name == "build_recall_prompt":
                assert "persona" not in {kw.arg for kw in node.keywords}


def test_process_split_note_states_four_processes():
    """D-01: four processes, and BOTH rejected alternatives named rather than merely not chosen."""
    note = driver.PROCESS_SPLIT_NOTE
    assert "FOUR fresh processes" in note
    assert "Not one process for all four arms" in note
    assert "not one process per question" in note
    assert "1,080" in note
    # The three notes travel together in the report; the split cites its two companions by name.
    assert "NO_KV_CACHE_NOTE" in note
    assert "SEQUENTIAL_QUESTIONS_JUSTIFICATION" in note


def test_every_arm_normalizes_to_the_same_record_shape():
    """T-16-33b: three different arm return shapes, one normalized ``by_split`` dict.

    Regrouping keys on each ENTRY's own ``split``, never on which record it came out of — so a
    tier record holding a mixed split lands in the right buckets rather than in the bucket its
    tier is named after.
    """
    three_tier_records = [
        {"questions": [_entry(split="taught"), _entry(split="held-out")]},
        {"questions": [_entry(split="held-out")]},
        {"questions": [_entry(split="taught")]},
    ]
    one_record = {"questions": [_entry(split="taught"), _entry(split="held-out")]}
    per_question = [_entry(split="taught"), _entry(split="held-out")]

    for returned, expected in (
        (three_tier_records, {"taught": 2, "held-out": 2}),
        (one_record, {"taught": 1, "held-out": 1}),
        (per_question, {"taught": 1, "held-out": 1}),
    ):
        by_split = driver.normalize_by_split(returned)
        assert {k: len(v) for k, v in by_split.items()} == expected
        for entries in by_split.values():
            for entry in entries:
                assert set(driver.PER_QUESTION_KEYS) <= set(entry)


def test_assert_record_shape_rejects_a_missing_key():
    """A dropped key aborts at the arm that produced it, not at 16-09's ``record["fact_id"]``."""
    import pytest

    good = {"condition": "adapter-only", "by_split": {"taught": [_entry()]}}
    driver.assert_record_shape(good)  # no raise

    for dropped in driver.PER_QUESTION_KEYS:
        entry = _entry()
        del entry[dropped]
        with pytest.raises(SystemExit) as excinfo:
            driver.assert_record_shape({"condition": "adapter-only", "by_split": {"t": [entry]}})
        assert dropped in str(excinfo.value)

    with pytest.raises(SystemExit):
        driver.assert_record_shape({"condition": "adapter-only", "by_split": {}})


def test_arm_parity_rejects_a_mismatch():
    """PERS-02: unequal budgets across arms make the comparison a comparison of configurations."""
    import pytest

    forbid = torch.zeros(1, 8, dtype=torch.bool)
    records = [
        {"condition": name, "config": driver.arm_config_record(forbid), "by_split": {}}
        for name in driver.CONDITION_ORDER
    ]
    driver.assert_arm_parity(records)  # no raise — one object, four arms

    for column in driver.PARITY_COLUMNS:
        broken = [dict(r, config=dict(r["config"])) for r in records]
        broken[1]["config"][column] = "tampered"
        with pytest.raises(SystemExit) as excinfo:
            driver.assert_arm_parity(broken)
        assert column in str(excinfo.value)

    # A second ArmConfig instance whose fields agree today is still not the shared object.
    twin = driver.ArmConfig(*driver.SHARED_ARM_CONFIG)
    assert twin == driver.SHARED_ARM_CONFIG and twin is not driver.SHARED_ARM_CONFIG
    impostor = [dict(r, config=dict(r["config"], shared_arm_config=twin)) for r in records]
    with pytest.raises(SystemExit) as excinfo:
        driver.assert_arm_parity(impostor)
    assert "ONE object" in str(excinfo.value)

    # Three arms is not the comparison, and neither is four records naming three conditions.
    with pytest.raises(SystemExit):
        driver.assert_arm_parity(records[:3])
    with pytest.raises(SystemExit):
        driver.assert_arm_parity(records[:3] + [dict(records[0])])


# ===== 16-08 Task 3 — arm D, the embedding/cosine baseline ====================================
#
# CPU-only. A TINY randomly-initialized GPT stands in for the 13.9M checkpoint: arm D's contract
# is about which seam is read, which scorer runs and which flags are off, and none of that needs
# trained weights. Requiring the real checkpoint would make this file un-runnable in CI.

_TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"


def _tiny_model():
    from personacore.config import ModelConfig
    from personacore.model import GPT

    torch.manual_seed(1337)
    model = GPT(ModelConfig(n_layer=1, n_head=1, n_embd=8))
    model.eval()
    return model


def _tokenizer():
    from personacore.tokenizer import from_json

    return from_json(_TOKENIZER_PATH)


def _cosine_items(count=3):
    """A handful of fixture items — the real fixture, so the seed indices are the real ones."""
    by_tier = driver.load_fixture_items()
    return by_tier["core_held_out"][:count]


def test_candidate_pool_is_the_committed_lexicon():
    """D-23: the pool IS ``find_contradictions``' lexicon — 20 distinct values, zero new judgment.

    A hand-curated pool would be a chance floor chosen by hand, in the one arm whose result is
    read against exactly that floor.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(facts)

    expected = set(facts.LOCKED_VALUES) | {f.value for f in facts.GATE_REJECTED_CANDIDATES}
    pool = driver.candidate_pool()
    assert set(pool) == expected
    assert len(pool) == len(set(pool)) == 20
    assert list(pool) == sorted(pool), "the pool is sorted, so argmax indices mean one thing"


def test_chance_floor_literal_matches_the_pool():
    """T-16-35: the floor is 1/len(pool) and the literal is 0.05 — never the superseded 0.125."""
    pool = driver.candidate_pool()
    assert driver.COSINE_CHANCE_FLOOR == 0.05
    assert driver.COSINE_CHANCE_FLOOR != 0.125
    assert 1 / len(pool) == driver.COSINE_CHANCE_FLOOR
    assert driver.COSINE_POOL_SIZE == len(pool) == 20

    # D-25's reconciliation is RECORDED, not silently applied: the superseded figure appears once,
    # in the comment that records it, and nowhere in any computation.
    source = _driver_source()
    assert source.count("0.125") == 1
    assert source.count("COSINE_CHANCE_FLOOR = 0.05") == 1
    tree = _driver_tree()
    numbers = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    ]
    assert 0.125 not in numbers, "0.125 reached executable code — it is a comment, not a number"


def test_cosine_arm_is_scored_by_contains_value():
    """D-22 / T-16-34: one scorer across all four arms, so silent divergence is impossible."""
    arm = _function_def(_driver_tree(), "run_cosine_arm")
    called = _called_names(arm)
    assert "contains_value" in called

    # No second scoring predicate anywhere in the module — not a local rule, not a rebuilt one.
    source = _driver_source()
    for rival in ("startswith", "endswith", "fuzz", "levenshtein", "SequenceMatcher", "difflib"):
        assert rival not in source
    # `score_question` is the committed aggregator over 9 draws; arm D draws once and must not
    # reach for it, or its `n` would come from a list length rather than from D-22's decision.
    assert "score_question" not in called


def test_cosine_arm_runs_with_the_adapter_disabled():
    """D-24: adapter OFF is a structural invariant — a ``with`` around the body, not a keyword."""
    arm = _function_def(_driver_tree(), "run_cosine_arm")
    withs = [node for node in arm.body if isinstance(node, ast.With)]
    managers = {
        getattr(item.context_expr.func, "id", None)
        for node in withs
        for item in node.items
        if isinstance(item.context_expr, ast.Call)
    }
    assert "adapter_disabled" in managers, (
        "the arm's body must be enclosed by `with adapter_disabled(model)` — arm D exists to be "
        "the referent WITHOUT weight-based memory, so this is not a caller's option"
    )
    # And the question loop lives INSIDE it, not beside it.
    enclosed = [n for node in withs for n in ast.walk(node) if isinstance(n, ast.For)]
    assert enclosed, "the question loop is outside adapter_disabled — the flag would be a no-op"


def test_cosine_arm_records_one_draw_per_question():
    """D-22: ONE deterministic draw, not nine manufactured by softmax-sampling similarities."""
    model, tok = _tiny_model(), _tokenizer()
    result = driver.run_cosine_arm(model, tok, "cpu", _cosine_items(2), driver.candidate_pool())

    assert result["n"] == len(result["questions"]) == 2
    assert all(entry["n"] == 1 for entry in result["questions"])
    assert all(entry["k"] in (0, 1) for entry in result["questions"])
    assert result["chance_floor"] == driver.COSINE_CHANCE_FLOOR
    # The emitted value is TEXT drawn from the pool, and the full ranking travels with it.
    for entry in result["questions"]:
        assert entry["emitted"] in driver.candidate_pool()
        assert len(entry["similarities"]) == 20
        assert all(isinstance(value, float) for value in entry["similarities"])


def test_cosine_arm_records_the_full_per_question_key_set():
    """Every entry carries all five ``PER_QUESTION_KEYS``, and its seed_index is the fixture's."""
    items = _cosine_items(3)
    model, tok = _tiny_model(), _tokenizer()
    result = driver.run_cosine_arm(model, tok, "cpu", items, driver.candidate_pool())

    for item, entry in zip(items, result["questions"], strict=True):
        assert set(driver.PER_QUESTION_KEYS) <= set(entry)
        assert entry["seed_index"] == item.seed_index
        assert entry["fact_id"] == item.fact.id
        assert entry["split"] == item.split

    # The whole record normalizes onto the shared shape without a special case for arm D.
    by_split = driver.normalize_by_split(result)
    driver.assert_record_shape({"condition": "embedding-cosine", "by_split": by_split})


def test_cosine_arm_asserts_the_clean_room(monkeypatch):
    """T-16-32: arm D is a SCORED arm, so the clean-room rule is not relaxed for it."""
    import phase14_recall as recall
    import pytest

    fired = []

    def _leaky(tok, question, values):
        fired.append(question)
        raise SystemExit("[phase14_recall] PROOF FAILED: value appears in the decoded prompt")

    monkeypatch.setattr(recall, "assert_no_value_in_prompt", _leaky)
    model, tok = _tiny_model(), _tokenizer()
    with pytest.raises(SystemExit):
        driver.run_cosine_arm(model, tok, "cpu", _cosine_items(1), driver.candidate_pool())
    assert fired, "the arm drew without ever calling the clean-room proof"


def test_embed_sequence_does_not_mutate_the_forward_contract():
    """T-16-36: the hook is removed in a ``finally`` and ``GPT.forward``'s 2-tuple survives."""
    model, tok = _tiny_model(), _tokenizer()
    ids = tok.encode("a short probe")

    before = len(model.ln_f._forward_hooks)
    vector = driver.embed_sequence(model, ids, "cpu")
    assert vector.ndim == 1 and vector.shape[0] == model.config.n_embd
    assert len(model.ln_f._forward_hooks) == before == 0, "a hook survived its call"

    out = model(torch.tensor([ids], dtype=torch.long))
    assert isinstance(out, tuple) and len(out) == 2
    assert out[1] is None and out[0].shape == (1, len(ids), model.config.vocab_size)

    # The removal is in a `finally`, so a raising forward still leaves no hook behind.
    import pytest

    with pytest.raises(Exception):
        driver.embed_sequence(model, [0] * (model.config.block_size + 1), "cpu")
    assert len(model.ln_f._forward_hooks) == 0


def test_arm_d_has_no_index_or_reranker():
    """PERS-04's out-of-scope bound, pinned: embedding plus cosine over the existing fact set.

    A full retrieval system is out of scope BY REQUIREMENT, not by taste, so the bound is a grep
    rather than a sentence in a docstring nobody re-reads.
    """
    source = _driver_source().lower()
    for symbol in ("faiss", "sklearn", "rerank", "chunk", "top_k", "annoy", "hnsw", "bm25"):
        assert symbol not in source, f"{symbol!r} is out of PERS-04's scope"
    assert "scipy" not in source  # STAT-04: zero new dependencies
