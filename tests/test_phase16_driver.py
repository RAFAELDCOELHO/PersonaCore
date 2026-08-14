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
import json
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


# ===== 16-10 Task 1 — the PERS-03 context-pressure sweep ======================================
#
# CPU-only and generation-free. The dilution builder is exercised against the REAL frozen
# tokenizer, because "the built prompt reaches its target" is a claim about tokenization and an
# estimate would prove nothing. No model is loaded: `run_sweep`'s only model-touching call is the
# committed fairness control, which these tests stub.

_SERIALIZE_PATH = _REPO_ROOT / "src" / "personacore" / "dialogue" / "serialize.py"
_LADDER_PATH = _REPO_ROOT / "scripts" / "phase16_ladder.py"


def _core_statement():
    """The statement whose span is the committed 13-token nominal (`46 = 33 bare + 13`)."""
    from personacore.dialogue import detokenize

    tok = _tokenizer()
    for statement in driver.fairness_statements().values():
        if len(tok.encode(detokenize(statement), allowed_special="none")) == (
            driver.SWEEP_NOMINAL_PERSONA_SPAN
        ):
            return statement
    raise AssertionError(
        f"no committed statement encodes to the {driver.SWEEP_NOMINAL_PERSONA_SPAN}-token nominal "
        "persona span 16-CONTEXT.md records — the cited measurement and the material disagree"
    )


def test_truncation_cells_are_derived_from_crossing_block_size():
    """D-27: the label IS the crossing. Exactly two of the six cells truncate."""
    cells = driver.sweep_cells()
    assert len(cells) == 6
    for cell in cells:
        crosses = cell["target_tokens"] > driver.SWEEP_BLOCK_SIZE
        assert cell["crosses_block_size"] is crosses
        assert ("truncation" in cell["pressure_label"]) is crosses, cell
    assert sum(1 for cell in cells if cell["crosses_block_size"]) == 2
    assert [cell["target_tokens"] for cell in cells] == list(driver.SWEEP_PROMPT_TARGETS)


def test_there_is_no_independent_truncation_axis():
    """T-16-44: one cell source, and no constant holding a truncation target list of its own.

    A separately-declared truncation axis would be the largest dilution cell under a second name,
    and the report would state one effect twice.
    """
    source = _driver_source()
    assert "TRUNCATION_TARGETS" not in source
    assert "TRUNCATION_CELLS" not in source
    tree = _driver_tree()
    named = {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert not [name for name in named if name.startswith("TRUNCATION")], sorted(named)

    # `sweep_cells` is the single source of cells: nothing else iterates SWEEP_PROMPT_TARGETS.
    readers = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and "SWEEP_PROMPT_TARGETS"
        in {inner.id for inner in ast.walk(node) if isinstance(inner, ast.Name)}
    ]
    assert readers == ["sweep_cells", "run_sweep"], readers


def test_sweep_block_size_is_read_from_the_model_config():
    """The crossing point is `ModelConfig.block_size`, never a retyped 256 free to drift."""
    from personacore.config import ModelConfig

    assert driver.SWEEP_BLOCK_SIZE == ModelConfig.block_size == 256
    assigned = [
        node.value
        for node in _driver_tree().body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "SWEEP_BLOCK_SIZE"
            for target in node.targets
        )
    ]
    assert len(assigned) == 1
    assert not isinstance(assigned[0], ast.Constant), (
        "SWEEP_BLOCK_SIZE is assigned a literal — every cell's pressure label is derived from it, "
        "so a copy that drifted from the model would relabel the sweep while every rate stayed"
    )


def test_diluted_prompt_reaches_its_target_length():
    """Every cell lands within `SWEEP_LENGTH_TOLERANCE` of its target, on the real tokenizer."""
    tok = _tokenizer()
    statement = _core_statement()
    for target in driver.SWEEP_PROMPT_TARGETS:
        built = driver.build_diluted_persona(tok, statement, target)
        assert abs(built["achieved_prompt_tokens"] - target) <= driver.SWEEP_LENGTH_TOLERANCE, (
            f"target {target} built to {built['achieved_prompt_tokens']}"
        )
        assert built["overshoots_target"] is False
        assert built["lines"][0] == statement


def test_persona_cap_does_not_constrain_this_path():
    """The OPPOSITE of the premise an earlier draft of 16-10 inherited, asserted with its reason.

    16-RESEARCH Pitfall 4 asserted, stamped ``[VERIFIED]``, that ``PERSONA_CAP`` caps the persona
    span so dilution must come from added turns. That sentence was struck and corrected at
    ``79fa01a``. The measured facts: ``build_recall_prompt`` (``serialize.py:92``) never calls
    ``cap_persona`` (``serialize.py:115``), which is the ONLY enforcer of the cap, so the persona
    span reaches 448 tokens directly and all dilution is persona-span-internal.
    """
    from personacore.dialogue import PERSONA_CAP

    tree = ast.parse(_SERIALIZE_PATH.read_text(encoding="utf-8"))
    builder = _function_def(tree, "build_recall_prompt")
    assert builder is not None
    assert "cap_persona" not in _called_names(builder), (
        "build_recall_prompt calls cap_persona — the sweep's premise that the cap does not bite "
        "on this route has stopped being true, and the largest cells would be silently trimmed"
    )
    assert _function_def(tree, "cap_persona") is not None

    built = driver.build_diluted_persona(_tokenizer(), _core_statement(), 448)
    assert built["persona_span_tokens"] > PERSONA_CAP, (
        f"the 448 cell's persona span is {built['persona_span_tokens']} tokens, not above the "
        f"{PERSONA_CAP}-token cap — the cap would then be in force on this path after all"
    )


def test_the_statement_sits_at_the_head_of_the_diluted_span():
    """Filler is APPENDED. The statement's offset is below every filler line's, at every target."""
    from personacore.dialogue import detokenize

    tok = _tokenizer()
    statement = _core_statement()
    for target in driver.SWEEP_PROMPT_TARGETS:
        lines = driver.build_diluted_persona(tok, statement, target)["lines"]
        offsets = [
            1 + len(tok.encode(detokenize("\n".join(lines[:index])), allowed_special="none"))
            for index in range(len(lines))
        ]
        assert offsets[0] == 1, offsets
        assert all(offset > offsets[0] for offset in offsets[1:]), offsets
        assert offsets == sorted(offsets)


def test_truncated_cells_actually_drop_the_statement():
    """The crossing cells' statement is provably OUTSIDE the trailing `block_size` window.

    Built through the REAL prompt builder and checked against the real trailing window, not
    against the nominal arithmetic: without this a prepend bug would leave the truncation cells
    measuring nothing while still emitting a number.
    """
    from personacore.dialogue import build_recall_prompt, detokenize

    tok = _tokenizer()
    statement = _core_statement()
    question = driver.load_fixture_items()["core_held_out"][0].question
    statement_ids = tok.encode(detokenize(statement), allowed_special="none")

    crossed = 0
    for cell in driver.sweep_cells():
        built = driver.build_diluted_persona(tok, statement, cell["target_tokens"])
        span = "\n".join(built["lines"])
        prompt_ids = build_recall_prompt(tok, question, persona=[span])
        window = prompt_ids[-driver.SWEEP_BLOCK_SIZE :]
        present = any(
            window[i : i + len(statement_ids)] == statement_ids
            for i in range(len(window) - len(statement_ids) + 1)
        )
        if cell["crosses_block_size"]:
            crossed += 1
            assert len(prompt_ids) > driver.SWEEP_BLOCK_SIZE
            assert not present, f"cell {cell['target_tokens']} kept the statement in view"
            assert built["statement_end_offset"] <= len(prompt_ids) - driver.SWEEP_BLOCK_SIZE
        else:
            assert present, f"cell {cell['target_tokens']} dropped a statement it should keep"
    assert crossed == 2


def test_no_turns_axis_exists():
    """There is one turn and the sweep never builds a prompt — every cell goes via `statements`."""
    tree = _driver_tree()
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "encode_dialogue" not in imported
    calls = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "encode_dialogue" not in calls

    sweep = _function_def(tree, "run_sweep")
    assert sweep is not None
    called = _called_names(sweep)
    assert "build_recall_prompt" not in called, "run_sweep builds a prompt instead of a statement"
    assert "run_fairness_control" in called

    # `build_recall_prompt` passes exactly ONE turn — the fact that leaves no turns axis at all.
    builder = _function_def(
        ast.parse(_SERIALIZE_PATH.read_text(encoding="utf-8")), "build_recall_prompt"
    )
    turns = [
        node
        for node in ast.walk(builder)
        if isinstance(node, ast.Call) and (getattr(node.func, "id", None) == "encode_dialogue")
    ]
    assert len(turns) == 1
    assert isinstance(turns[0].args[2], ast.List) and len(turns[0].args[2].elts) == 1


def test_sweep_runs_on_arm_b_only():
    """D-26: one arm measured, one proof, two not applicable — each with its own reason."""
    applicability = driver.sweep_applicability()
    assert sorted(applicability) == sorted(driver.CONDITION_ORDER)
    assert list(applicability) == list(driver.CONDITION_ORDER)
    treatments = [entry["treatment"] for entry in applicability.values()]
    assert treatments.count("measured") == 1
    assert treatments.count("proof") == 1
    assert treatments.count("not_applicable") == 2
    assert applicability["prompt-stuffed"]["treatment"] == "measured"
    assert applicability["adapter-only"]["treatment"] == "proof"
    for condition, entry in applicability.items():
        assert entry["reason"].strip(), condition
    assert "run_bit_identity_control" in applicability["adapter-only"]["reason"]
    assert "0.0" in applicability["adapter-only"]["reason"]


def test_monotone_claim_requires_the_ladder():
    """D-28: the claim is licensed by the COMMITTED ladder branch, never by this driver."""
    import phase16_ladder as ladder
    import pytest

    assert driver.monotone_claim_allowed("no_rung_passed") is False
    for branch in ladder.HEADLINE_BRANCHES:
        assert driver.monotone_claim_allowed(branch) is (branch != "no_rung_passed")
    with pytest.raises(SystemExit):
        driver.monotone_claim_allowed("span_9000")


def test_overwrite_competitor_comes_from_the_committed_pool():
    """D-23: the contradicting value is a pool member, never hand-picked, never the fact's own."""
    pool = driver.candidate_pool()
    by_tier = driver.load_fixture_items()
    values = {item.fact.value for tier in by_tier for item in by_tier[tier]}
    assert values
    for value in sorted(values):
        competitor = driver.overwrite_competitor(value, pool)
        assert competitor in pool
        assert competitor != value
    # Deterministic: the same value yields the same competitor on every process of the split.
    first = sorted(values)[0]
    assert driver.overwrite_competitor(first, pool) == driver.overwrite_competitor(first, pool)


def test_overwrite_returns_a_statement_not_a_prompt():
    """A STATEMENT STRING with the competitor AFTER the taught value; no prompt builder exists."""
    statement = "my name is quillon."
    overwritten = driver.build_overwrite_statement(statement, "zibby")
    assert isinstance(overwritten, str)
    assert overwritten.startswith(statement)
    assert "quillon" in overwritten and "zibby" in overwritten
    assert overwritten.index("quillon") < overwritten.index("zibby")
    assert "build_overwrite_prompt" not in _driver_source()
    assert not hasattr(driver, "build_overwrite_prompt")


def _stub_fairness(monkeypatch, tok, seen):
    """Replace the committed fairness control with a recorder shaped like its real return."""
    import phase14_recall as recall

    def _stub(model, tokenizer, device, forbid, questions, statements):
        seen.append(statements)
        entries = []
        for index, item in enumerate(questions):
            span = statements[item.fact.id]
            length = driver._nominal_prompt_tokens(tokenizer, [span])
            entries.append(
                {
                    "question": item.question,
                    "fact_id": item.fact.id,
                    "split": item.split,
                    "seed_index": item.seed_index,
                    "persona": span,
                    "prompt_ids": list(range(length)),
                    "k": index % 2,
                    "n": 9,
                }
            )
        return {
            "tier": recall.FAIRNESS_TIER,
            "questions": entries,
            "k": sum(entry["k"] for entry in entries),
            "n": 9 * len(entries),
            "rate": 0.0,
            "n_answerable": sum(1 for entry in entries if entry["k"] > 0),
        }

    monkeypatch.setattr(recall, "run_fairness_control", _stub)


def test_run_sweep_covers_six_on_axis_cells_plus_the_overwrite(monkeypatch):
    """`sweep_cells()` is 6; `run_sweep` returns 7, the seventh off-axis at nominal length.

    Pins the 6-vs-7 relationship so a future edit cannot drop the overwrite row by rendering
    `sweep_cells()` — the wall-clock budget and the threat model both say "7 cells (6 dilution +
    1 overwrite)", and the two counts are consistent rather than a discrepancy.
    """
    tok = _tokenizer()
    by_tier = driver.load_fixture_items()
    items = tuple(by_tier["core_held_out"][:2] + by_tier["core_taught"][:2])
    statements = {
        fact_id: statement
        for fact_id, statement in driver.fairness_statements().items()
        if fact_id in {item.fact.id for item in items}
    }
    seen = []
    _stub_fairness(monkeypatch, tok, seen)

    result = driver.run_sweep(None, tok, "cpu", None, items, statements)
    cells = result["cells"]
    assert len(driver.sweep_cells()) == 6
    assert len(cells) == 7
    assert len(seen) == 7, "seven runs of the committed control, one per cell"

    on_axis = cells[:6]
    assert [cell["target_tokens"] for cell in on_axis] == list(driver.SWEEP_PROMPT_TARGETS)
    assert sum(1 for cell in on_axis if cell["crosses_block_size"]) == 2

    overwrite = cells[-1]
    assert overwrite["pressure_label"] == driver.OVERWRITE_PRESSURE_LABEL
    assert overwrite["pressure_label"] not in ("dilution", "dilution + truncation")
    assert overwrite["crosses_block_size"] is False
    assert overwrite["target_tokens"] == driver.SWEEP_PROMPT_TARGETS[0]
    assert set(overwrite["competitors"]) == set(statements)

    for cell in cells:
        assert cell["statement_head_offset"] == 1
        assert set(cell["measured_prompt_tokens"]) == {"min", "median", "max"}
        assert cell["proportion"]["n_questions"] == len(items)
        assert "wilson_label" in cell["proportion"]
    # The crossing cells drop the statement out of view for every question they scored.
    for cell in on_axis:
        if cell["crosses_block_size"]:
            assert cell["n_statement_outside_window"] == len(items), cell
            assert cell["n_over_block_size"] == len(items)
        else:
            assert cell["n_statement_outside_window"] == 0, cell
    assert result["applicability"] == driver.sweep_applicability()
    assert result["assert_value_in_prompt_caveat"] == driver.ASSERT_VALUE_IN_PROMPT_CAVEAT


def test_the_sweep_adds_no_persona_or_draw_all_call_site():
    """D-21 stays at two entries: the sweep routes via the `statements` map, not a new prompt."""
    tree = _driver_tree()
    persona_sites = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (getattr(node.func, "id", None) or getattr(node.func, "attr", None))
        == "build_recall_prompt"
        and any(keyword.arg == "persona" for keyword in node.keywords)
    ]
    assert persona_sites == []
    calls = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    assert "draw_all" not in calls

    scoring = importlib.util.spec_from_file_location(
        "phase14_scoring_guard", _REPO_ROOT / "tests" / "test_phase14_scoring.py"
    )
    module = importlib.util.module_from_spec(scoring)
    scoring.loader.exec_module(module)
    assert len(module.PERSONA_ALLOWLIST) == 2, module.PERSONA_ALLOWLIST
    assert len(module.DRAW_ALL_ASSERTED_BY) == 1


def test_sweep_is_not_gated():
    """STAT-06 / D-09, re-asserted against the concrete sweep code 16-09's guard predates.

    A seventh gated comparison prices Holm's first step at 0.0071429, below the achievable p of
    0.0078125, and the headline dies arithmetically at every outcome.
    """
    tree = _driver_tree()
    enclosing = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                enclosing.setdefault(inner, node.name)
    for gate in ("holm", "sign_test_exact", "assert_family_closed", "compare_arms"):
        holders = {
            enclosing.get(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (getattr(node.func, "id", None) or getattr(node.func, "attr", None)) == gate
        }
        assert "run_sweep" not in holders, f"run_sweep reaches {gate}"
        assert not {holder for holder in holders if holder and "sweep" in holder.lower()}, gate

    sweep = _function_def(tree, "run_sweep")
    called = _called_names(sweep)
    for gate in ("holm", "sign_test_exact", "compare_arms", "taught_replication"):
        assert gate not in called
    assert "report_proportion" not in called  # it runs in the per-cell helper, still ungated


# ===== 16-10 Task 2 — the persistence report writer and its clobber guard =====================
#
# Every render below writes to a tmp_path. `results/phase16_persistence_report.md` is plan 16-11's
# artifact and must not exist until the real four-arm run produces it — a test that created it
# would trip the clobber guard on the run it exists to protect.

_HELD_OUT_PER_FACT = 13
_TAUGHT_PER_FACT = 14


def _arm_record(condition, per_fact_k, *, pid):
    """One arm's record in `run_condition`'s shape, plus what `main()` adds for the report."""
    core = sorted(driver.core_fact_ids())
    by_split = {"held-out": [], "taught": []}
    for index, fact_id in enumerate(core):
        for split, count in (("held-out", _HELD_OUT_PER_FACT), ("taught", _TAUGHT_PER_FACT)):
            by_split[split] += [
                {
                    "fact_id": fact_id,
                    "split": split,
                    "seed_index": seed,
                    "k": per_fact_k(condition, index),
                    "n": 9,
                }
                for seed in range(count)
            ]
    return {
        "condition": condition,
        "config": driver.arm_config_record(torch.zeros(1, 8192)),
        "by_split": by_split,
        "provenance": [f"pid: {pid} (PROCESS BOUNDARY)", "driver git_sha: deadbee"],
        "forbid_ids_masked": 7645,
        "vocab_size": 8192,
    }


def _dominant(condition, index):
    """Arm A beats every arm on every fact; arm B beats the two floor arms on 7 of 8."""
    return {"adapter-only": 5, "prompt-stuffed": 0 if index == 0 else 1}.get(condition, 0)


def _all_tied(condition, index):
    return 3


def _sweep_fixture():
    cells = []
    for cell in driver.sweep_cells():
        crosses = cell["crosses_block_size"]
        cells.append(
            {
                **cell,
                "nominal_prompt_tokens": {"min": 44, "median": 46, "max": 48},
                "measured_prompt_tokens": {"min": 30, "median": 46, "max": 78},
                "n_over_block_size": 270 if crosses else 0,
                "statement_head_offset": 1,
                "statement_end_offset": {"min": 13, "median": 15, "max": 27},
                "n_statement_outside_window": 270 if crosses else 0,
                "overshooting_facts": [],
                "k": 0,
                "n": 2430,
                "n_answerable": 0,
                "proportion": driver.report_proportion(0, 270, 2430),
            }
        )
    cells.append({**cells[0], "pressure_label": driver.OVERWRITE_PRESSURE_LABEL, "competitors": {}})
    return {
        "cells": cells,
        "applicability": driver.sweep_applicability(),
        "block_size": driver.SWEEP_BLOCK_SIZE,
        "targets": driver.SWEEP_PROMPT_TARGETS,
        "assert_value_in_prompt_caveat": driver.ASSERT_VALUE_IN_PROMPT_CAVEAT,
        "adversarial_overwrite_note": driver.ADVERSARIAL_OVERWRITE_NOTE,
    }


def _render(monkeypatch, tmp_path, per_fact_k=_dominant):
    """Render a full report from constructed records, into a tmp_path — never into `results/`."""
    target = tmp_path / "phase16_persistence_report.md"
    monkeypatch.setattr(driver, "PERSISTENCE_REPORT_PATH", target)
    # The two-stage bootstrap is exercised by `tests/test_phase16_stats.py`; 10,000 resamples over
    # four arms here would cost seconds per test to re-prove someone else's property.
    monkeypatch.setattr(driver, "cluster_bootstrap", lambda per_fact: (0.194444, 0.486111))

    records = [
        _arm_record(condition, per_fact_k, pid=1000 + index)
        for index, condition in enumerate(driver.CONDITION_ORDER)
    ]
    gated = driver.per_fact_by_arm(records, tier=driver.GATED_TIER)
    taught = driver.per_fact_by_arm(records, tier=driver.REPLICATION_TIER)
    text = driver.write_persistence_report(
        records,
        driver.compare_arms(gated, tier=driver.GATED_TIER),
        driver.taught_replication(taught),
        _sweep_fixture(),
        ["report assembly pid: 2000", "driver git_sha: deadbee"],
    )
    assert target.read_text(encoding="utf-8") == text
    assert not driver.PERSISTENCE_REPORT_PATH.parent.samefile(_REPO_ROOT / "results")
    return text


def test_report_has_no_bare_zero_percent(monkeypatch, tmp_path):
    """STAT-02: a zero renders as its numerator over its denominator with a bound — never `0%`.

    The constructed records include an arm that scores nothing on every fact, so the zero path is
    the one under test rather than an unexercised branch.
    """
    text = _render(monkeypatch, tmp_path)
    assert re.search(r"\b0(\.0+)?%", text) is None
    assert "rule of three" in text
    assert "0 / 13" in text


def test_report_carries_every_verbatim_clause(monkeypatch, tmp_path):
    """D-03, D-07 and D-25 appear byte for byte, compared against `16-CONTEXT.md` itself."""
    text = _render(monkeypatch, tmp_path)
    for anchor in ("- **D-03:**", "- **D-07:**", "- **D-25:**"):
        clause = _context_blockquote(anchor)
        assert clause in text, f"{anchor} is not reproduced verbatim in the report"
    assert driver.arm_d_qualifier() == _context_blockquote("- **D-25:**")
    assert driver.CONDITION_ORDER_PREREGISTRATION in text
    assert driver.TAUGHT_TIER_STATUS in text


def test_report_states_the_arm_d_floor_as_0_05(monkeypatch, tmp_path):
    """The operative floor is 0.05; the superseded figure appears once, in the reconciliation."""
    text = _render(monkeypatch, tmp_path)
    assert "0.05" in text
    assert text.count("0.125") == 1
    section = text.split("## The Arm-D Structural Floor", 1)[1].split("\n## ", 1)[0]
    assert "0.125" in section, "the superseded figure is outside the reconciliation section"
    assert driver.ARM_D_FLOOR_RECONCILIATION in text


def test_report_publishes_the_four_parity_columns(monkeypatch, tmp_path):
    """SC2: the four scalar columns plus `forbid_ids`, one row per arm."""
    text = _render(monkeypatch, tmp_path)
    for column in ("`max_new_tokens`", "`stop_ids`", "`context_length`", "`n_draws`"):
        assert column in text, column
    assert "`forbid_ids`" in text
    parity = text.split("## Arm Parity", 1)[1].split("\n## ", 1)[0]
    for condition in driver.CONDITION_ORDER:
        assert f"| `{condition}` |" in parity, condition
    assert "D-22" in parity, "arm D's realized single draw is published without its reason"


def test_report_headline_is_imported_from_the_ladder(monkeypatch, tmp_path):
    """T-16-47: the headline is `licensed_headline`'s output, never a branch statement retyped."""
    tree = _driver_tree()
    writer = _function_def(tree, "write_persistence_report")
    assert writer is not None
    assert "licensed_headline" in _called_names(writer)
    assert "import phase16_ladder" in _driver_source()

    import phase16_ladder as ladder

    source = _driver_source()
    for statement in ladder.HEADLINE_BRANCHES.values():
        assert statement[:60] not in source, "a ladder branch statement is duplicated in the driver"

    text = _render(monkeypatch, tmp_path)
    assert ladder.HEADLINE_BRANCHES["span_2"] in text
    assert "phase16_ladder_report.md" in text
    assert driver.LADDER_PROXY_DEGENERATE_CAVEAT in text
    # D-30: the headline's two-mechanism qualification is emitted beside the branch, not left to
    # whoever writes the final prose. Recorded in 16-CONTEXT.md BEFORE the run.
    assert driver.HEADLINE_MECHANISM_CAVEAT in text


def test_headline_mechanism_caveat_names_its_measured_basis():
    """D-30's qualification must carry the ladder numbers that make it a finding, not an opinion.

    A caveat that merely says "two mechanisms are possible" is an unfalsifiable hedge. This one is
    load-bearing because the ladder MEASURED the second mechanism: gate-cleared synthetic span-5
    cells scored zero, so the prompt arm's floor is explained by span length rather than by which
    strings were chosen. Pinning the numbers keeps a future edit from softening it into a hedge.
    """
    caveat = driver.HEADLINE_MECHANISM_CAVEAT
    for token in ("(5, 2)", "(5, 30)", "216", "[4,4,4,5,5,6,8,8]", "median 5"):
        assert token in caveat, f"D-30 caveat no longer names its measured basis: {token!r} missing"
    assert "gate-cleared" in caveat, (
        "the no-prior-knowledge control is what makes the zero mean span"
    )
    assert "AT THIS SCALE" in caveat, "the scope limit is the whole point of the qualification"
    assert "not an omission" in caveat, "D-30 records an explicit decision, not a gap"


def test_report_prints_four_provenance_blocks(monkeypatch, tmp_path):
    """D-01: four pids, so the process split is evidenced by the artifact rather than asserted."""
    text = _render(monkeypatch, tmp_path)
    for index, condition in enumerate(driver.CONDITION_ORDER):
        assert f"### Condition `{condition}` — its own process" in text
        assert f"pid: {1000 + index}" in text
    assert text.count("### Condition `") == len(driver.CONDITION_ORDER)


def test_arm_d_soft_row_states_the_structural_zero(monkeypatch, tmp_path):
    """Arm D's soft-tier zero is a property of the POOL — it never gets dressed in a bound."""
    text = _render(monkeypatch, tmp_path)
    assert driver.SOFT_TIER_EXCLUSION in text
    assert "BY CONSTRUCTION" in driver.SOFT_TIER_EXCLUSION
    soft = text.split("**The soft tier is not reported per fact here", 1)[1].split("\n## ", 1)[0]
    assert "rule-of-three" in soft, "the reason names the bound it refuses to print"
    for line in text.splitlines():
        if "soft" in line.lower() and "embedding-cosine" in line:
            assert "rule of three" not in line.lower(), line


def test_report_carries_the_truncation_caveat(monkeypatch, tmp_path):
    """The `assert_value_in_prompt` pass on a truncated cell is never 'the value was in view'."""
    text = _render(monkeypatch, tmp_path)
    assert driver.ASSERT_VALUE_IN_PROMPT_CAVEAT in text
    pressure = text.split("## Context Pressure (PERS-03)", 1)[1].split("\n## ", 1)[0]
    assert driver.ASSERT_VALUE_IN_PROMPT_CAVEAT in pressure
    assert "cap_persona" in pressure and "never calls" in pressure
    assert driver.ADVERSARIAL_OVERWRITE_NOTE in pressure
    for treatment in ("**measured**", "**proof**", "**not_applicable**"):
        assert treatment in pressure
    assert pressure.count("| `dilution` |") == 0  # labels render bare, not as code spans
    assert "dilution + truncation" in pressure
    assert driver.OVERWRITE_PRESSURE_LABEL in pressure


def test_report_never_quotes_the_over_precise_wall_clock(monkeypatch, tmp_path):
    """T-16-50: the intra-run interval cannot contain a repeat of its own measurement."""
    text = _render(monkeypatch, tmp_path)
    assert "39.2" not in text
    assert "39.2" not in _driver_source()
    assert "~39 min" in text and "35-44 min" in text
    assert "11.5%" in text


def test_report_carries_both_floor_units(monkeypatch, tmp_path):
    """T-16-26: the draw unit is printed WITH the label naming it the one STAT-01 forbids."""
    import phase16_ladder as ladder

    text = _render(monkeypatch, tmp_path)
    assert ladder.DRAW_UNIT_LABEL in text
    assert ladder.QUESTION_UNIT_LABEL in text
    assert ladder.LADDER_FLOOR_SOURCE in text
    assert "1944" in text and "216" in text


def test_report_records_not_demonstrable_when_no_pair_clears(monkeypatch, tmp_path):
    """A null is a pre-registered OUTCOME, rendered from a committed string, not written after."""
    text = _render(monkeypatch, tmp_path, per_fact_k=_all_tied)
    assert driver.NOT_DEMONSTRABLE in text
    assert "NOT DEMONSTRABLE AT n = 8" in text
    verdict = text.split("\n## Verdict", 1)[1]
    assert "cleared their Holm step" not in verdict
    gate = text.split("## The Inferential Gate", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in gate.splitlines() if line.startswith("| `") and " x `" in line]
    assert len(rows) == 6
    assert all(row.rstrip().endswith("| no |") for row in rows), rows
    assert all("| 1.0000000 |" in row for row in rows), rows


def test_report_renders_exactly_six_holm_rows(monkeypatch, tmp_path):
    """D-09: six pairs in the gate table, and the taught replication carries no alpha at all."""
    text = _render(monkeypatch, tmp_path)
    gate = text.split("## The Inferential Gate", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in gate.splitlines() if line.startswith("| `") and " x `" in line]
    assert len(rows) == len(driver.HOLM_FAMILY_PAIRS) == 6, rows
    assert f"{driver.HOLM_ALPHA} / 6 = 0.0083333" in gate

    replication = text.split("## Taught Replication", 1)[1].split("\n## ", 1)[0]
    assert "alpha at step" not in replication
    assert "rejected" not in replication.lower()
    assert (
        len(
            [line for line in replication.splitlines() if line.startswith("| `") and " x `" in line]
        )
        == 6
    )


def test_clobber_guard_anchors_on_the_verdict_section(tmp_path, monkeypatch):
    """T-16-49: a recorded verdict is refused; a PENDING one is not; a foreign file is refused."""
    import pytest

    target = tmp_path / "report.md"
    monkeypatch.setattr(driver, "PERSISTENCE_REPORT_PATH", target)

    driver.assert_persistence_report_not_clobbered()  # absent file: nothing to protect

    target.write_text("# r\n\n## Verdict\n\nPENDING\n", encoding="utf-8")
    driver.assert_persistence_report_not_clobbered()

    target.write_text("# r\n\n## Verdict\n\nspan_2, recorded.\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        driver.assert_persistence_report_not_clobbered()

    target.write_text("# not this writer's output\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        driver.assert_persistence_report_not_clobbered()

    # A PROSE mention of the heading below a recorded verdict must not rescue it (15-04 CR-02).
    target.write_text(
        "## Verdict\n\nspan_2, recorded.\n\n## Later\n\nsee the heading above — PENDING nothing.\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        driver.assert_persistence_report_not_clobbered()

    source = _driver_source()
    assert 'split("## Verdict")' not in source
    assert "VERDICT_SECTION" in source


def test_report_monotone_claim_carries_the_ladder_ceiling(monkeypatch, tmp_path):
    """D-28 as locked, WITH its ceiling in the same paragraph as the permission.

    The committed branch is `span_2`, so D-28's branch-level condition is met — but that branch
    licenses a two-token in-context copy while the material this comparison scores is 4-8 tokens
    long. A permission printed alone is the sentence a reader quotes, so the bound travels with it.
    """
    text = _render(monkeypatch, tmp_path)
    assert driver.MONOTONE_CLAIM_LICENSED.format(branch="span_2", statement="") in text
    assert driver.MONOTONE_CLAIM_REFUSED.format(branch="span_2", statement="") not in text
    assert "That is the whole of what is licensed" in text
    assert "longer than the passing rung's span" in text
    for template in (driver.MONOTONE_CLAIM_LICENSED, driver.MONOTONE_CLAIM_REFUSED):
        assert "{branch}" in template, "the branch is interpolated, never retyped per outcome"


def test_report_tables_have_no_pipe_bearing_cells(monkeypatch, tmp_path):
    """A pipe inside a markdown cell silently splits the row into extra columns."""
    text = _render(monkeypatch, tmp_path)
    header_widths = {}
    for line in text.splitlines():
        if not line.startswith("| ") or set(line.strip()) <= set("| -"):
            continue
        width = line.count("|")
        header_widths.setdefault(width, 0)
        header_widths[width] += 1
    rows = [line for line in text.splitlines() if line.startswith("| ")]
    assert rows
    # Every row of a given table has the same pipe count as its own header; a stray pipe inside a
    # cell shows up as a width nobody else shares.
    orphan = [width for width, count in header_widths.items() if count == 1]
    assert not orphan, f"row widths {orphan} appear once — a cell probably carries a bare pipe"


# ===== 16-10 Task 3 — main(): one condition per process =======================================
#
# No model is loaded and no arm record is written into `results/`: `ARM_RECORD_DIR` is redirected
# to a tmp_path in every test below. `results/phase16_arm_*.json` are plan 16-11's artifacts.


def _arm_payload(condition, *, pid, git_sha="deadbee", seed_shift=0, forbid_sha=None):
    """One arm's JSON payload in `run_one_condition`'s shape, without running anything."""
    record = _arm_record(condition, _dominant, pid=pid)
    config = driver.serializable_config(record["config"])
    if forbid_sha is not None:
        config["forbid_ids_sha256"] = forbid_sha
    by_split = {
        split: [{**entry, "seed_index": entry["seed_index"] + seed_shift} for entry in entries]
        for split, entries in record["by_split"].items()
    }
    return {
        "condition": condition,
        "git_sha": git_sha,
        "pid": pid,
        "device": "cpu",
        "wall_clock_min": 1.0,
        "provenance": [f"pid: {pid} (PROCESS BOUNDARY)", f"driver git_sha: {git_sha}"],
        "config": config,
        "forbid_ids_masked": 7645,
        "vocab_size": 8192,
        "by_split": by_split,
        "sweep": _sweep_fixture() if condition == "prompt-stuffed" else None,
    }


def _write_arms(monkeypatch, tmp_path, conditions=driver.CONDITION_ORDER, **overrides):
    monkeypatch.setattr(driver, "ARM_RECORD_DIR", tmp_path)
    monkeypatch.setattr(driver, "PERSISTENCE_REPORT_PATH", tmp_path / "report.md")
    monkeypatch.setattr(driver, "cluster_bootstrap", lambda per_fact: (0.194444, 0.486111))
    for index, condition in enumerate(conditions):
        payload = _arm_payload(condition, pid=1000 + index, **overrides.get(condition, {}))
        driver.arm_record_path(condition).write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
    return tmp_path


def test_main_requires_a_single_condition():
    """D-01 / T-16-46: one arm per invocation, and no flag that runs two."""
    import pytest

    parser = driver.build_parser()
    flags = {option for action in parser._actions for option in action.option_strings}
    assert "--all" not in flags, flags
    assert '"--all"' not in _driver_source()
    assert "--condition" in flags and "--report" in flags

    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(["--condition", "adapter-only-ish"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--condition", "adapter-only", "--report"])
    for condition in driver.CONDITION_ORDER:
        assert parser.parse_args(["--condition", condition]).condition == condition
    assert parser.parse_args(["--report"]).report is True


def test_report_mode_requires_all_four_arms(monkeypatch, tmp_path):
    """Three arms on disk is not a four-arm comparison, and the family's size prices alpha."""
    import pytest

    _write_arms(monkeypatch, tmp_path, conditions=driver.CONDITION_ORDER[:3])
    with pytest.raises(SystemExit, match="missing"):
        driver.run_report_mode()


def test_report_mode_rejects_mismatched_git_sha(monkeypatch, tmp_path):
    """T-16-45: four processes, ONE codebase — a mismatch means the arms ran different code."""
    import pytest

    _write_arms(monkeypatch, tmp_path, **{"prompt-stuffed": {"git_sha": "cafef00d"}})
    with pytest.raises(SystemExit, match="git SHA"):
        driver.run_report_mode()


def test_report_mode_asserts_identical_seed_index_sets(monkeypatch, tmp_path):
    """PERS-02's pairing claim is CHECKED at report time, never assumed."""
    import pytest

    _write_arms(monkeypatch, tmp_path, **{"base-neither": {"seed_shift": 100}})
    with pytest.raises(SystemExit, match="seed_index"):
        driver.run_report_mode()


def test_report_mode_requires_four_distinct_pids(monkeypatch, tmp_path):
    """Two arms in one process crossed the exact boundary this comparison exists to isolate."""
    import pytest

    monkeypatch.setattr(driver, "ARM_RECORD_DIR", tmp_path)
    for condition in driver.CONDITION_ORDER:
        driver.arm_record_path(condition).write_text(
            json.dumps(_arm_payload(condition, pid=7777)), encoding="utf-8"
        )
    with pytest.raises(SystemExit, match="pid"):
        driver.run_report_mode()


def test_report_mode_calls_assert_arm_parity(monkeypatch, tmp_path):
    """16-08 defined it and nothing called it. This is the wiring, pinned two ways.

    Structurally, so a future edit cannot drop the call in silence; and LIVE, by handing the
    report four arms whose `forbid_ids` hashes disagree — the one parity column no single arm
    record can attest to on its own.
    """
    import pytest

    tree = _driver_tree()
    reporter = _function_def(tree, "run_report_mode")
    assert reporter is not None
    assert "assert_arm_parity" in _called_names(reporter), (
        "run_report_mode does not call assert_arm_parity — PERS-02's parity claim would ship as "
        "an unexecuted function, which is exactly what 16-08 and 16-09 both flagged"
    )
    holders = {
        holder
        for holder in (
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and "assert_arm_parity" in _called_names(node)
        )
    }
    assert holders == {"run_report_mode"}, holders

    _write_arms(monkeypatch, tmp_path, **{"embedding-cosine": {"forbid_sha": "00" * 32}})
    with pytest.raises(SystemExit, match="forbid_ids_sha256"):
        driver.run_report_mode()


def test_report_mode_assembles_from_four_agreeing_arms(monkeypatch, tmp_path):
    """The happy path: four agreeing arms produce the report, and it is written once."""
    _write_arms(monkeypatch, tmp_path)
    text = driver.run_report_mode()
    assert "## Verdict" in text
    assert (tmp_path / "report.md").read_text(encoding="utf-8") == text
    assert text.count("### Condition `") == 4
    assert "arm pids: [1000, 1001, 1002, 1003]" in text


def test_report_mode_requires_exactly_one_sweep(monkeypatch, tmp_path):
    """D-26: the sweep runs on arm B and nowhere else, checked at assembly."""
    import pytest

    monkeypatch.setattr(driver, "ARM_RECORD_DIR", tmp_path)
    monkeypatch.setattr(driver, "PERSISTENCE_REPORT_PATH", tmp_path / "report.md")
    for index, condition in enumerate(driver.CONDITION_ORDER):
        payload = _arm_payload(condition, pid=1000 + index)
        payload["sweep"] = _sweep_fixture()  # every arm swept — D-26 says exactly one
        driver.arm_record_path(condition).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit, match="sweep"):
        driver.run_report_mode()


def test_sweep_runs_only_for_the_prompt_stuffed_condition():
    """D-26 as CODE: `run_sweep` is reachable from exactly one branch of `run_one_condition`."""
    body = _function_def(_driver_tree(), "run_one_condition")
    assert body is not None
    guarded = [
        node
        for node in ast.walk(body)
        if isinstance(node, ast.If) and "run_sweep" in _called_names(node)
    ]
    assert len(guarded) == 1, "run_sweep is not behind exactly one condition test"
    test = ast.unparse(guarded[0].test)
    assert test == "condition == 'prompt-stuffed'", test
    assert not guarded[0].orelse, "an else-branch would give another arm a path to the sweep"

    # And the context_length proof 16-08 asked this plan to add, against the LOADED config.
    proofs = [
        ast.unparse(node)
        for node in ast.walk(body)
        if isinstance(node, ast.Compare) and "model_cfg.block_size" in ast.unparse(node)
    ]
    assert proofs == ["model_cfg.block_size == SHARED_ARM_CONFIG.context_length"], proofs


def test_main_is_guarded_and_import_is_cheap():
    """Importing the driver loads no model, no tokenizer and no checkpoint."""
    import time

    source = _driver_source()
    assert 'if __name__ == "__main__":' in source
    assert hasattr(driver, "main")

    started = time.time()
    spec = importlib.util.spec_from_file_location("phase16_persistence_reload", _DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    elapsed = time.time() - started
    assert elapsed < 3, f"import took {elapsed:.2f}s"
    assert module.CONDITION_ORDER == driver.CONDITION_ORDER

    tree = _driver_tree()
    called = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in _module_level_nodes(tree)
        if isinstance(node, ast.Call)
    }
    for expensive in (
        "undecodable_ids_mask",
        "from_json",
        "load_adapted_model",
        "load_fixture_items",
        "run_condition",
        "run_sweep",
        "write_persistence_report",
        "preflight_device",
        "seed_everything",
    ):
        assert expensive not in called, expensive

    # `main` is called at module level EXACTLY ONCE, and only under the `__name__` guard.
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If) and "__name__" in ast.unparse(node.test)
    ]
    assert len(guards) == 1
    assert _called_names(guards[0]) == {"main"}
    unguarded = [
        node for node in tree.body if not isinstance(node, ast.If) and "main" in _called_names(node)
    ]
    assert unguarded == []
