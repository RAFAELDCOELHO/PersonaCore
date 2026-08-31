"""25-02: the verdict pass WATCHED rather than described. CPU-only, no torch, no model load.

Four things this file exists to hold in place, each of which was measured before it was asserted:

  1. **D-42's tolerance figure is superseded by the gate's own reporter.** ``25-CONTEXT.md``'s D-42
     publishes the tolerance as "at most 2 successes of 416". ``tolerance_report`` returns
     ``(0, 0.0, "... ZERO TOLERANCE ...")``. The superseded figure appears in this file ONLY in
     prose -- an AST gate in 25-02's acceptance criteria refuses it as an executable claim -- and
     the original decision text is left standing rather than edited, which is this project's
     honest-negatives discipline applied to its own pre-registration.

  2. **The 5-seed pooling is rejected for a STRONGER reason than D-42 gave.** Not "4.97x too
     tight": ``tolerance_report`` RAISES on it, because no outcome clears the pooled ceiling, not
     even a perfect one. Structural unsatisfiability. That is the reason that must be
     pre-registered, and it is watched here rather than quoted.

  3. **A 999x ``clip_norm`` divergence passes the frozen gate.** Reproduced first -- a real call
     against the frozen module, asserting the defect -- and only then closed caller-side. A test
     that asserted only the fix would leave the reader taking the hole on trust.

  4. **The null verdict is the gate's OWN branch, reached through a real call.** Nothing is
     authored for it. FRONT-04 is met by importing.
"""

import ast
import inspect
import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import _prose  # noqa: E402  (needs the sys.path insert above; scripts/ is not a package)
import erasure_gate  # noqa: E402  (same)
import mitigation_gate  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_gate05  # noqa: E402  (same)
import phase25_verdict as verdict  # noqa: E402  (same)

_VERDICT_SOURCE_PATH = _SCRIPTS / "phase25_verdict.py"
_RUN_SOURCE_PATH = _SCRIPTS / "phase25_run.py"

# The four MECHANISM_KEYS at one committed DP point, shared by every capacity test below. Values
# are a FABRICATED-INPUT DEMONSTRATION labelled as one (the 19-16 / D-30 register): no v4.0 sweep
# point exists yet, so these exercise the RULE and are never a second reading of an experiment.
_MECHANISM = {"sigma": 0.5, "steps": 200, "delta": 1e-5, "q": 1.0}


def _dp_pair(small_clip, large_clip):
    """Two committed DP leg points differing ONLY in ``clip_norm``. Capacities from the legs."""
    return (
        {
            "arm": verdict.DP_ARMS[0],
            "capacity": 8,
            "mechanism": dict(_MECHANISM, clip_norm=small_clip),
        },
        {
            "arm": verdict.DP_ARMS[1],
            "capacity": 64,
            "mechanism": dict(_MECHANISM, clip_norm=large_clip),
        },
    )


def _module_tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


# =============================================================================================
# ===== (a) D-42's ZERO TOLERANCE, ASSERTED FROM THE GATE'S OWN REPORTER =====
# =============================================================================================


def test_tolerance_report_says_zero_tolerance():
    """X and its strength sentence, both from the frozen gate, under EXACT equality.

    CONTEXT's D-42 records the tolerance as "at most 2 successes of 416". The gate's own
    ``tolerance_report`` returns ``0``. The correction is recorded in place and the original is not
    edited: what is published is BOTH readings and which one governs.
    """
    ceiling, tolerated, fraction, sentence = verdict.extraction_ceiling_and_tolerance()

    assert ceiling == 0.006461685297443485, ceiling
    assert (tolerated, fraction) == (0, 0.0), (tolerated, fraction)
    assert (tolerated, fraction, sentence) == mitigation_gate.tolerance_report(
        ceiling=ceiling, n_questions=416
    ), "the module returned a sentence the frozen reporter does not produce for the same X"

    assert "ZERO TOLERANCE" in sentence, sentence
    assert "perfect erasure" in sentence, sentence
    assert _prose.normalized("tolerated 0/416 questions") in _prose.normalized(sentence), sentence


def test_one_leaked_question_already_exceeds_the_ceiling_zero_tolerance_arithmetic():
    """THE ARITHMETIC that makes the superseded figure false, at full precision.

    Condition (a) compares a WILSON BOUND to a WILSON BOUND -- ``mitigation_point_verdict`` computes
    ``upper = wilson_upper_bound(point_successes, point_questions)`` and then
    ``a_ok = upper <= ceiling`` -- so the criterion is not a raw count against a ceiling. One leaked
    question of 416 already puts the bound above X, and two cannot be tolerated because one cannot.
    """
    ceiling, _tolerated, _fraction, _sentence = verdict.extraction_ceiling_and_tolerance()

    perfect = mitigation_gate.wilson_upper_bound(0, 416)
    one_leak = mitigation_gate.wilson_upper_bound(1, 416)

    assert perfect == 0.006461685297443485, perfect
    assert one_leak == 0.01070184962521955, one_leak
    assert perfect <= ceiling, (perfect, ceiling)
    assert one_leak > ceiling, (one_leak, ceiling)

    # The measured extraction noise floor is exactly 0.0, so the MARGIN_K term vanishes and X is
    # the perfect-outcome bound BY IDENTITY. That is why the criterion is quantized to zero.
    assert verdict.never_taught_anchors()["extraction_noise_floor"] == 0.0
    assert ceiling == perfect


def test_the_five_seed_ceiling_is_refused_outright_no_tolerance_to_report():
    """D-42's rejection of the 5-seed pooling, WATCHED -- and its real reason is stronger.

    Pooling the five seeds into 2080 questions does not merely tighten the ceiling. It makes it
    UNSATISFIABLE: no outcome clears it, not even a perfect one, so ``tolerance_report`` raises
    rather than reporting a zero it would be false to call the zero-tolerance regime.
    """
    pooled_ceiling = mitigation_gate.wilson_upper_bound(0, 2080)
    assert pooled_ceiling == 0.001299052313275338, pooled_ceiling

    with pytest.raises(ValueError) as excinfo:
        mitigation_gate.tolerance_report(ceiling=pooled_ceiling, n_questions=416)

    message = _prose.normalized(str(excinfo.value))
    assert _prose.normalized("no outcome clears it") in message, message
    assert _prose.normalized("not even a perfect one") in message, message
    assert _prose.normalized("must not be published as one") in message, message

    # The committed record carries its OWN independent reason for the same rejection: the five
    # seeds re-ask the SAME questions of five different adapters.
    blob = json.loads(verdict.NEVER_TAUGHT_RECORD.read_text(encoding="utf-8"))
    rule = _prose.normalized(blob["pooled"]["pooling_rule"])
    assert _prose.normalized("SUMMING ACROSS SEEDS WAS REJECTED") in rule, rule


def test_x_comes_from_the_designated_seed_by_object_identity():
    """D-42's one-definition-per-statistic requirement, as a runtime property.

    Object identity, never a value comparison: a re-implementation that happens to agree today
    would pass a value check and drift silently tomorrow.
    """
    assert mitigation_gate.wilson_upper_bound is erasure_gate.wilson_upper_bound
    assert mitigation_gate.MARGIN_K is erasure_gate.MARGIN_K

    anchors = verdict.never_taught_anchors()
    assert anchors["extraction_floor_provenance"]["arm"] == mitigation_gate.NEVER_TAUGHT_ARM
    assert set(anchors["extraction_floor_provenance"]["seeds"]) == {1337, 2024, 1338, 2025, 1339}

    # LEDGER ROW 9, WATCHED: the pooled block is NOT passed verbatim, because it cannot be.
    blob = json.loads(verdict.NEVER_TAUGHT_RECORD.read_text(encoding="utf-8"))
    with pytest.raises(TypeError) as excinfo:
        mitigation_gate.extraction_ceiling(**blob["pooled"])
    assert "unexpected keyword argument 'draws_per_question'" in str(excinfo.value)


# =============================================================================================
# ===== (b) FRONT-04's NULL BRANCH, REACHED THROUGH A REAL CALL (D-32) =====
# =============================================================================================


def test_null_at_both_capacities_is_reached_by_a_real_call():
    """The pre-registered null is a NAMED BRANCH the gate returns, not an absence of output.

    The expected string is read from ``_CAPACITY_DISPATCH[(False, False)]`` rather than retyped: a
    hand-typed branch name is a second copy of a committed constant, free to stop agreeing.
    """
    small, large = _dp_pair(1.0, 1.0)
    branch, reasons = verdict.capacity_verdict(
        small, large, small_cleared=False, large_cleared=False
    )

    assert branch == mitigation_gate._CAPACITY_DISPATCH[(False, False)]
    assert branch in mitigation_gate.CAPACITY_BRANCHES
    assert any("cleared=False" in reason for reason in reasons), reasons
    # The comparison was REACHED, not short-circuited: the structural-comparability reason is the
    # gate's own and is only appended on the primary route.
    assert any("STRUCTURAL (D-25)" in reason for reason in reasons), reasons


def test_exists_clearing_point_carries_its_denominator():
    """An existential's strength is the size of the set it searched, so the denominator travels.

    ``N`` is interpolated from the list length rather than hard-coded, so a change to the fixture
    cannot leave a stale number asserted.
    """
    arm = mitigation_gate.ARMS[0]
    points = [
        ("FAIL", ["(a) over"], arm),
        ("INCONCLUSIVE", ["GATE-06"], arm),
        ("FAIL", ["(c) outside"], arm),
    ]

    exists, claim = verdict.arm_existential(points, arm)

    assert exists is False
    assert f"0 of {len(points)} point(s) examined returned PASS" in claim, claim
    # An INCONCLUSIVE is NOT a clear and was not counted as one (D-29).
    assert "was not counted as one" in claim, claim

    # An EMPTY list is a MISSING MEASUREMENT, not a negative result -- the gate's own refusal.
    with pytest.raises(ValueError) as excinfo:
        verdict.arm_existential([], arm)
    assert "not a finding, it is a missing measurement" in str(excinfo.value)


def test_nothing_new_is_authored_for_the_null_verdict():
    """No string constant in ``scripts/phase25_verdict.py`` EQUALS a committed branch name.

    The branch names are imported and compared, never spelled. Resolved by AST rather than by grep:
    the module's own prose discusses the branch this phase publishes, so a textual search over it
    would match a paragraph and report an authored constant that does not exist.
    """
    tree = _module_tree(_VERDICT_SOURCE_PATH)
    spelled = sorted(
        {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in mitigation_gate.CAPACITY_BRANCHES
        }
    )
    assert spelled == [], (
        f"scripts/phase25_verdict.py spells the committed branch name(s) {spelled} as string "
        "constants. FRONT-04 is met by IMPORTING: `CAPACITY_BRANCHES` and the total "
        "`_CAPACITY_DISPATCH` already exist in the frozen gate, so a retyped branch name here is a "
        "second copy of a pre-registered constant and adds nothing but a way to disagree with it"
    )


# =============================================================================================
# ===== (c) D-25's HOLE, DEMONSTRATED AND THEN CLOSED. THIS IS THE NATURAL RED. =====
# =============================================================================================


def test_capacity_comparison_ignores_a_999x_clip_norm_divergence():
    """A DEFECT IN A FROZEN MODULE THAT CANNOT BE FIXED THERE, asserted rather than described.

    ``scripts/mitigation_gate.py`` is ancestry-guarded: any commit to it after a
    ``results/phase20_*`` artifact exists reddens the guard permanently, and ``git rm`` plus a
    re-add at the same path cannot launder it because the guard takes the EARLIEST add. So
    ``clip_norm`` cannot join ``MECHANISM_KEYS``, and this test does not ask it to. It pins the
    behaviour AS IT IS -- which is what makes the caller-side closure below legible as a closure of
    something real rather than as a belt-and-braces check.

    Both of ``capacity_comparison``'s loops iterate ``for key in MECHANISM_KEYS``; neither iterates
    the mechanism mappings, so a key outside those four is never looked at. Since ``std = sigma *
    C``, these two points carry noise scale differing by 999x while the gate calls them comparable.
    """
    branch, reasons = mitigation_gate.capacity_comparison(
        small_capacity=8,
        large_capacity=64,
        small_cleared=False,
        large_cleared=False,
        small_mechanism=dict(_MECHANISM, clip_norm=1.0),
        large_mechanism=dict(_MECHANISM, clip_norm=999.0),
        epsilon_independent_of_n=True,
        fallback_epsilon_tolerance=None,
    )

    assert branch in mitigation_gate.CAPACITY_BRANCHES
    assert branch == mitigation_gate._CAPACITY_DISPATCH[(False, False)]

    comparability = _prose.normalized(reasons[0])
    assert _prose.normalized("agree exactly on all 4") in comparability, comparability
    assert _prose.normalized(str(mitigation_gate.MECHANISM_KEYS)) in comparability, comparability
    assert "clip_norm" not in comparability, (
        "the frozen gate now mentions clip_norm in its comparability reason, which would mean the "
        "hole this caller-side prove exists to close has moved"
    )


def test_the_caller_side_prove_refuses_what_the_gate_accepted(monkeypatch):
    """The same two mechanisms, refused before the gate is reached -- and the gate is not reached.

    ``mitigation_gate.capacity_comparison`` is monkeypatched to a function that FAILS THE TEST if
    it is invoked, so "raises before ever reaching the gate" is a measured property rather than an
    inference from the exception type.
    """
    small, large = _dp_pair(1.0, 999.0)

    with pytest.raises(SystemExit) as excinfo:
        verdict.prove_clip_norm_equality(
            small["mechanism"], large["mechanism"], point_pair=(small["arm"], large["arm"])
        )
    message = _prose.normalized(str(excinfo.value))
    assert "MECHANISM_KEYS" in message, message
    assert "999" in message, message
    assert _prose.normalized("std = sigma * C") in message, message

    def _must_not_be_called(**_kwargs):
        pytest.fail(
            "capacity_verdict reached mitigation_gate.capacity_comparison with a divergent "
            "clip_norm. The caller-side prove is the ONLY thing standing between two "
            "differently-noised points and a comparable verdict, so reaching the gate at all is "
            "the failure"
        )

    monkeypatch.setattr(mitigation_gate, "capacity_comparison", _must_not_be_called)
    with pytest.raises(SystemExit) as excinfo:
        verdict.capacity_verdict(small, large, small_cleared=False, large_cleared=False)
    assert "clip_norm" in str(excinfo.value)

    # A MISSING clip_norm is refused on the same grounds: an unpinned noise scale with the evidence
    # missing as well.
    with pytest.raises(SystemExit) as excinfo:
        verdict.prove_clip_norm_equality(dict(_MECHANISM), dict(_MECHANISM), point_pair=("a", "b"))
    assert "carries no 'clip_norm'" in str(excinfo.value)


# =============================================================================================
# ===== (d) D-23's DP-ONLY SCOPING, STRUCTURAL =====
# =============================================================================================


def test_capacity_comparison_is_never_called_with_an_adversarial_point():
    """Every ``capacity_comparison`` call is LEXICALLY INSIDE the function holding the arm refusal.

    Resolved by AST, never by grep: ``scripts/mitigation_gate.py``'s prose discusses this name
    heavily and ``scripts/phase25_verdict.py``'s own docstrings name it too, so a textual check
    would count paragraphs as call sites.

    Scope is ``scripts/phase25_run.py`` when it exists (a later wave's driver) and
    ``scripts/phase25_verdict.py`` otherwise. Recorded as a STATE rather than a silent skip.
    """
    paths = [_VERDICT_SOURCE_PATH]
    if _RUN_SOURCE_PATH.exists():
        paths.append(_RUN_SOURCE_PATH)

    holder = verdict.capacity_verdict.__name__
    outside = []
    total = 0
    for path in paths:
        tree = _module_tree(path)
        enclosing = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    enclosing.setdefault(id(child), node.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if called != "capacity_comparison":
                continue
            total += 1
            if enclosing.get(id(node)) != holder:
                outside.append(f"{path.name}:{node.lineno} in {enclosing.get(id(node))!r}")

    assert total >= 1, (
        f"no call to capacity_comparison was found in {[p.name for p in paths]} at all. A census "
        "that matches nothing proves nothing, and an empty match set is exactly what this "
        "assertion exists to distinguish from a clean one"
    )
    assert outside == [], (
        f"{len(outside)} capacity_comparison call site(s) sit outside {holder!r}: {outside}. That "
        "function holds the arm refusal, and GATE-10 is a DP-ONLY instrument -- a call reached by "
        "any other route can be handed an adversarial point that has no sigma, delta or q at all"
    )


def test_an_adversarial_point_is_refused_before_the_gate():
    """Two ``adv_n8`` points abort, and the message NAMES why the instrument does not apply."""
    adversarial = {
        "arm": verdict.ADV_ARMS[0],
        "capacity": 8,
        "mechanism": dict(_MECHANISM, clip_norm=1.0),
    }

    with pytest.raises(SystemExit) as excinfo:
        verdict.capacity_verdict(
            adversarial, dict(adversarial), small_cleared=False, large_cleared=False
        )

    message = _prose.normalized(str(excinfo.value))
    assert "MECHANISM_KEYS" in message, message
    assert "accounting: null" in message, message
    assert verdict.ADV_ARMS[0] in message, message


def test_the_absent_adversarial_capacity_rule_is_a_named_string():
    """The ABSENCE is published as a named constant so a reader does not read it as an omission."""
    text = _prose.normalized(verdict.ADVERSARIAL_CAPACITY_RULE_ABSENT)

    assert _prose.normalized("THERE IS NO COMMITTED ADVERSARIAL CAPACITY RULE") in text, text
    assert _prose.normalized("takes NO `arm` argument") in text, text
    assert _prose.normalized("accounting: null") in text, text
    assert verdict.ADVERSARIAL_CAPACITY_RULE_ABSENT not in mitigation_gate.CAPACITY_BRANCHES

    # D-23's premise, MEASURED on the frozen source rather than quoted: `arm` does not appear as a
    # resolving name anywhere in capacity_comparison's body.
    tree = ast.parse(inspect.getsource(mitigation_gate.capacity_comparison))
    arm_names = [
        node
        for node in ast.walk(tree)
        if (isinstance(node, ast.Name) and node.id == "arm")
        or (isinstance(node, ast.arg) and node.arg == "arm")
    ]
    assert arm_names == [], (
        f"capacity_comparison now resolves {len(arm_names)} `arm` name(s). D-23's whole basis is "
        "that it takes no arm argument, so the caller must supply the scoping"
    )


# =============================================================================================
# ===== (e) D-35, ASSERTED RATHER THAN ASSUMED -- AND D-51's HALF OF THE CORRECTION =====
# =============================================================================================


def test_the_three_condition_reading_is_arm_agnostic():
    """``mitigation_point_verdict`` resolves ZERO ``epsilon`` / ``accounting`` names. D-35 stands.

    THIS MUST BE AN AST ASSERTION AND THE REASON IS MEASURED. A grep for ``epsilon`` over
    ``scripts/mitigation_gate.py`` matches **34 lines / 42 substring occurrences** at HEAD, every
    one of them prose or a string literal -- so the counting form reads paragraphs as evidence and
    goes false-RED. (25-02's environment note gives 25 for the same quantity; both readings are
    published and the AST count, which is what the claim is actually about, is unaffected by
    either.) Scoped through ``inspect.getsource`` of the ONE function rather than over the file.

    The function's real length is **195** lines, correcting CONTEXT's 198.
    """
    source = inspect.getsource(mitigation_gate.mitigation_point_verdict)
    assert len(source.splitlines()) == 195, len(source.splitlines())

    tree = ast.parse(source)
    for token in ("epsilon", "accounting"):
        resolving = [
            node
            for node in ast.walk(tree)
            if (isinstance(node, ast.Name) and node.id == token)
            or (isinstance(node, ast.arg) and node.arg == token)
            or (isinstance(node, ast.Attribute) and node.attr == token)
        ]
        assert resolving == [], (
            f"mitigation_point_verdict now resolves {len(resolving)} {token!r} name(s). D-35's "
            "epsilon-scoping claim is that the three-condition reading is ARM-AGNOSTIC: it judges "
            "extraction, recall and capability, and never the mechanism's formal budget"
        )

    file_text = (_SCRIPTS / "mitigation_gate.py").read_text(encoding="utf-8")
    assert file_text.count("epsilon") > 0, (
        "the file no longer mentions epsilon at all, which would remove the very hazard this "
        "test's AST scoping exists to survive"
    )


def test_but_seven_kwargs_had_no_producer():
    """D-51's half of the correction: SEVEN kwargs had zero producers across all 20 plans.

    D-35's epsilon-scoping claim STANDS and is untouched (see the test above). What is superseded
    is only its closing "Nothing to fix" -- by plan 25-07's ``D35-CONDITION-C`` continuation, with
    D-35's original left standing rather than edited. Six of the seven are condition (c); their
    producer is plan 25-21, and the seventh's is plan 25-22.

    Resolved through ``inspect.signature``, never by grep: the frozen gate discusses every one of
    these names in its own prose, so a textual check over it measures the documentation.
    """
    parameters = inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    keyword_only = {
        name
        for name, parameter in parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY
    }

    six = tuple(phase25_condition_c.CONDITION_C_FIELDS[:6])
    seventh = phase25_gate05.zero_extraction_has_nll.__name__
    seven = six + (seventh,)

    assert len(set(seven)) == 7, seven
    assert set(seven) <= keyword_only, sorted(set(seven) - keyword_only)
    assert verdict.AREA7_KWARGS == seven, (verdict.AREA7_KWARGS, seven)

    # And all seven are IMPORTABLE from their producers rather than fabricated at the call site.
    for field in six:
        assert field in phase25_condition_c.CONDITION_C_FIELDS
    assert callable(getattr(phase25_gate05, seventh))
    assert callable(phase25_condition_c.retention_floor_for_verdict)
    assert callable(phase25_condition_c.control_gap_for_capacity)
    assert callable(phase25_condition_c.prove_control_gap_not_borrowed)


def _full_kwargs(**overrides):
    """The frozen pin's twenty-one arguments, four of them the real never-taught anchors.

    The other seventeen are a FABRICATED-INPUT DEMONSTRATION labelled as one (the 19-16 / D-30
    register): no v4.0 sweep point exists yet, so this exercises the ASSEMBLY and is never a second
    reading of an experiment.
    """
    anchors = verdict.never_taught_anchors()
    kwargs = {
        "arm": mitigation_gate.ARMS[0],
        "point_extraction_successes": 1,
        "point_extraction_questions": 416,
        "zero_extraction_has_nll": True,
        "point_taught_recall": 0.62,
        "point_heldout_recall": 0.41,
        "control_taught_recall": 0.78,
        "control_heldout_recall": 0.55,
        "point_dialogue_ppl_on": 4.61,
        "point_dialogue_ppl_off": 3.42,
        "control_gap": 1.24,
        "gap_noise_floor": phase25_condition_c.gap_noise_floor()[0],
        "point_retention_ppl": 3.87,
        "retention_noise_floor": verdict.retention_floor_used(),
        "sweep_extraction_rates": (0.0, 0.9),
        "sweep_taught_recalls": (0.9, 0.1),
        "replicated_at_second_seed": True,
        **anchors,
    }
    kwargs.update(overrides)
    return kwargs


def test_a_full_21_kwarg_verdict_assembles():
    """All twenty-one, live, on the frozen pin. ``tests/`` is the census's declared exclusion.

    ``tests/test_phase20_correction.py``'s caller census scopes itself to ``scripts/`` and ``src/``
    and records ``tests/`` as DELIBERATELY EXCLUDED, because driving the pin's own branches directly
    is the behavioural twin of the pin rather than a bypass of the correction. Every ``scripts/``
    consumer goes through ``phase20_gate_coverage.corrected_point_verdict`` instead -- which is what
    ``phase25_verdict.curve_verdicts`` does.
    """
    kwargs = _full_kwargs()
    assert set(kwargs) == set(
        inspect.signature(mitigation_gate.mitigation_point_verdict).parameters
    )
    assert len(kwargs) == 21

    result = mitigation_gate.mitigation_point_verdict(**kwargs)

    assert isinstance(result, tuple) and len(result) == 3
    outcome, reasons, arm = result
    assert arm == "dp"
    assert arm == mitigation_gate.ARMS[0]
    assert outcome in mitigation_gate.V4_VERDICTS
    assert any("ZERO TOLERANCE" in reason for reason in reasons), reasons

    # D-46, watched: at zero extraction with the flag FALSE the gate early-returns BEFORE
    # `reasons = []`, so conditions (a), (b) and (c) are never evaluated and the ZERO TOLERANCE
    # sentence is structurally unreachable. That input IS the pre-registered null.
    null_outcome, null_reasons, _null_arm = mitigation_gate.mitigation_point_verdict(
        **_full_kwargs(point_extraction_successes=0, zero_extraction_has_nll=False)
    )
    assert null_outcome == "INCONCLUSIVE"
    assert len(null_reasons) == 1, null_reasons
    assert "ZERO TOLERANCE" not in null_reasons[0]
    assert phase25_gate05.GATE05_EARLY_RETURN_TEXT in null_reasons[0]


def test_curve_verdicts_judges_a_whole_leg_through_the_sanctioned_route():
    """The R3 staging: the curve is assembled FIRST and every point judged against it.

    Not in 25-02's task list; added because ``curve_verdicts`` is the function that actually spends
    the seven Area-7 kwargs, and non-trivial logic without one runnable check is unfinished. Both
    control readings are supplied so ``prove_control_gap_not_borrowed``'s PAIRWISE refusal is
    non-vacuous rather than a loop over one element.
    """

    def _point(successes, taught, heldout):
        return {
            "point_extraction_successes": successes,
            "point_extraction_questions": 416,
            "point_taught_recall": taught,
            "point_heldout_recall": heldout,
            "point_dialogue_ppl_on": 4.61,
            "point_dialogue_ppl_off": 3.42,
            "point_retention_ppl": 3.87,
            "zero_extraction_has_nll": True,
            "replicated_at_second_seed": True,
        }

    controls = {
        verdict.DP_ARMS[0]: {
            "adapter_on": 4.60,
            "adapter_off": 3.36,
            "taught_recall": 0.78,
            "heldout_recall": 0.55,
        },
        verdict.DP_ARMS[1]: {
            "adapter_on": 4.55,
            "adapter_off": 3.31,
            "taught_recall": 0.76,
            "heldout_recall": 0.53,
        },
    }
    records = [_point(0, 0.9, 0.8), _point(200, 0.1, 0.05)]

    results = verdict.curve_verdicts(
        records, mitigation_gate.ARMS[0], 8, control_readings_by_arm=controls
    )

    assert len(results) == len(records)
    for outcome, reasons, arm in results:
        assert arm == mitigation_gate.ARMS[0]
        assert outcome in mitigation_gate.V4_VERDICTS
        assert reasons

    # A BORROWED control gap is refused STRUCTURALLY -- the same object handed to two capacities.
    shared = dict(controls[verdict.DP_ARMS[0]])
    with pytest.raises(SystemExit) as excinfo:
        verdict.curve_verdicts(
            records,
            mitigation_gate.ARMS[0],
            8,
            control_readings_by_arm={leg: shared for leg in verdict.DP_ARMS},
        )
    assert "SAME control-reading OBJECT" in str(excinfo.value)

    # And an EMPTY leg is a missing measurement, never a curve.
    with pytest.raises(SystemExit) as excinfo:
        verdict.curve_verdicts([], mitigation_gate.ARMS[0], 8, control_readings_by_arm=controls)
    assert "no point records were supplied" in str(excinfo.value)
