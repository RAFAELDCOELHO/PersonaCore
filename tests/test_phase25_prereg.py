"""PLAN 25-01 — THE THREE WATCHED REFUSALS PHASE 25 OWES BEFORE IT SPENDS A GPU SECOND.

A guard nobody has seen fail is not evidence. `scripts/phase25_prereg.py` carries three refusals and
four dated rules; this file WATCHES the refusals fire and asserts the rules STRUCTURALLY rather than
checking they are merely present.

**TWO REDS ARE NATURAL AND ONE IS PLANTED, and the split is deliberate.** D-07's halt has a natural
RED — call `prove_reproduction(789, 1008)` and the sweep stops. D-10's refusal has one — hand it a
tracked record. D-04's tripwire has NONE: its whole point is that no committed function asserts the
forbidden thing today, so the only way to watch it fire is to plant a violation. That plant goes
into a **scratch copy under `tmp_path`**, never into a real repo file, because this repository has
been burned by planted REDs landing on the wrong occurrence of a token in a real file and being
reverted into a false green.

**FOUR MECHANICS INHERITED FROM `tests/test_phase24_correction.py`, two of which apply here:**

  * **Identifiers are resolved by AST, never by grep.** `scripts/phase25_prereg.py`'s own docstrings
    discuss tolerance, `torch.equal` and `isclose` at length — a grep gate over that file would go
    FALSE-RED on its own prose, and `grep -c` counts LINES, so a wrapped occurrence miscounts twice
    over. `.planning/REQUIREMENTS.md`'s RPT-02 row records four instances of that class in Phase 20
    alone.
  * **Prose is matched through `scripts/_prose.normalized`.** A line-wrapped claim reported as
    absent is a MEASURED defect (`.planning/RETROSPECTIVE.md:179-181`), and the tail clause this
    file asserts on wraps in the source.

CPU-only. Stdlib plus pytest plus two sibling scripts, and — for CTRL-02's proxy alone — `DPSGD`
constructed with `model=None`, which touches no module, no tensor, no device and no GPU.
"""

import ast
import math
import pathlib
import sys

import pytest

from personacore.privacy.dpsgd import DPSGD

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)
import mitigation_budget  # noqa: E402  (same reason)
import mitigation_gate  # noqa: E402  (same reason)
from phase25_prereg import (  # noqa: E402  (same reason)
    BIT_IDENTITY_EXPECTED_DISAGREEMENT,
    BIT_IDENTITY_FORBIDDEN_ASSERTIONS,
    BIT_IDENTITY_SEAM_OFF_MARKERS,
    BIT_IDENTITY_SIGMA_ZERO_MARKERS,
    CANARY_RESERVATIONS,
    DISK_PRECHECK_BYTES,
    POINT_RECORD_GLOB,
    PROMOTION_RULE,
    PUBLICATION_OBLIGATION,
    REPRODUCTION_K,
    REPRODUCTION_N,
    declared_differences,
    point_record_path,
    prove_first_attempt,
    prove_reproduction,
    reproduction_source_reading,
)

_PREREG_MODULE = _ROOT / "scripts" / "phase25_prereg.py"
_PREREG_TREE = ast.parse(_PREREG_MODULE.read_text(encoding="utf-8"), filename=str(_PREREG_MODULE))

# The Phase-23 glob the refusal must NOT name. Spelled here rather than imported, because importing
# it would mean importing the EDIT-ONCE, already-spent module this plan is forbidden to take.
_PHASE23_MATCHED_GLOB_PREFIX = "results/phase23_matched_"

# The measured per-point disk cost the precheck must cover: one exported adapter plus one resume
# checkpoint, both read off this machine rather than estimated.
_ADAPTER_BYTES = 1_352_069
_RESUME_CHECKPOINT_BYTES = 59_691_603
_SWEEP_POINT_COUNT = 44


# =================================================================================================
# ===== (a) THE REPRODUCTION GATE — BOTH BRANCHES WATCHED (D-07) =====
# =================================================================================================


def test_reproduction_passes_at_the_committed_reading():
    """The pin is proved against THE RECORD IT NAMES, not against itself.

    `prove_reproduction(790, 1008)` returning silently proves only that a constant equals itself.
    The second assertion is the one that carries T-25-02: `reproduction_source_reading()` opens
    `results/phase23_sigma_zero.json` and reads `primary.k` / `primary.n`, so a pin that drifted
    from the artifact it claims to quote is RED here rather than invisible.
    """
    assert prove_reproduction(REPRODUCTION_K, REPRODUCTION_N) is None
    assert reproduction_source_reading() == (REPRODUCTION_K, REPRODUCTION_N)


@pytest.mark.parametrize(
    ("k", "n"),
    [(789, 1008), (791, 1008), (790, 1007)],
    ids=["one-below", "one-above", "denominator-moved"],
)
def test_reproduction_miss_halts_at_zero_sweep_points(k, n):
    """THE WATCHED RED D-07 OWES. A ONE-COUNT MISS IS ENOUGH, IN EITHER DIRECTION.

    Both miss directions are parametrized on purpose: `sigma_zero_verdict` records the asymmetry
    that motivates it — every correctness bug in this class IMPROVES the reading — so a control that
    BEATS 790 is as much a signal as one that misses it. The denominator case is here because
    790/1007 is a different measurement even though the numerator reproduces.

    The message is asserted on DISCRIMINATING SUBSTRINGS, never on the full string: an equality
    assertion over a paragraph fails on every rewording and therefore gets loosened, which is how a
    watched refusal stops being watched.
    """
    with pytest.raises(SystemExit) as halted:
        prove_reproduction(k, n)
    message = _prose.normalized(str(halted.value))

    assert "zero sweep points" in message, message
    assert f"{REPRODUCTION_K}/{REPRODUCTION_N}" in message, message
    assert f"{k}/{n}" in message, message

    # SUSPECT #1, named before there was anything to suspect.
    assert "f146d426" in message, message
    assert "a2c4771f" in message, message

    # THE FOUR DECLARED DIFFERENCES, COUNTED FROM THE RECORD RATHER THAN RETYPED HERE. If Phase 23's
    # record ever grows a fifth, this loop grows with it and a truncated halt message goes RED.
    entries = declared_differences()
    assert len(entries) == 4, entries
    for entry in entries:
        assert _prose.normalized(entry["difference"]) in message, entry["difference"]


def test_reproduction_uses_no_tolerance():
    """RESOLVED BY AST, because the module's own docstrings discuss tolerance at length.

    A grep for `isclose` over `scripts/phase25_prereg.py` matches the paragraph EXPLAINING why
    `isclose` is refused, so the counting form of this check reports a violation that does not
    exist. Only a parse can tell prose about a name from the name.
    """
    resolved = {node.id for node in ast.walk(_PREREG_TREE) if isinstance(node, ast.Name)}
    resolved |= {node.attr for node in ast.walk(_PREREG_TREE) if isinstance(node, ast.Attribute)}
    assert "isclose" not in resolved, resolved
    assert "abs" not in resolved, "a difference-and-threshold comparison is a tolerance"
    assert "torch" not in resolved, "wave-1 module: no torch, no device, no GPU"

    ordered = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)
    pins = {"REPRODUCTION_K", "REPRODUCTION_N"}
    for node in ast.walk(_PREREG_TREE):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        touches_pin = any(isinstance(item, ast.Name) and item.id in pins for item in operands)
        if touches_pin:
            assert not any(isinstance(op, ordered) for op in node.ops), ast.unparse(node)

    # And the POSITIVE half: the gate really does compare both pins under `==`.
    gate = next(
        node
        for node in ast.walk(_PREREG_TREE)
        if isinstance(node, ast.FunctionDef) and node.name == "prove_reproduction"
    )
    compared = {
        item.id
        for node in ast.walk(gate)
        if isinstance(node, ast.Compare) and all(isinstance(op, ast.Eq) for op in node.ops)
        for item in [node.left, *node.comparators]
        if isinstance(item, ast.Name)
    }
    assert pins <= compared, compared


# =================================================================================================
# ===== (b) THE PER-POINT ONE-ATTEMPT RULE, WATCHED (D-10) =====
# =================================================================================================

_POINT_KEY = "dp_n8_sigma0p500000"


def test_first_attempt_passes_on_an_unrecorded_point():
    """No record tracked for this point — the first attempt proceeds."""
    assert prove_first_attempt([], point_key=_POINT_KEY) is True


def test_first_attempt_passes_when_a_DIFFERENT_point_is_recorded():
    """D-10'S UNIT IS THE POINT, NOT THE SWEEP, and this is the assertion that makes that real.

    A rule whose unit was the sweep would refuse point 2 because point 1 landed, which would make a
    44-point sweep un-runnable after its first record. The refusal keys on THIS point's record path.
    """
    tracked = [point_record_path("dp_n64_sigma1p000000")]
    assert prove_first_attempt(tracked, point_key=_POINT_KEY) is True


def test_second_attempt_on_a_recorded_point_is_refused():
    """THE WATCHED RED D-10 OWES: a committed reading is evidence, and evidence is not re-drawn."""
    record = point_record_path(_POINT_KEY)
    with pytest.raises(SystemExit) as refused:
        prove_first_attempt([record], point_key=_POINT_KEY)
    message = _prose.normalized(str(refused.value))

    assert record in message, message
    assert _POINT_KEY in message, message
    assert POINT_RECORD_GLOB in message, message
    # The four scope clauses, none of them softened away.
    assert ".gitignore:17" in message and ".gitignore:14" in message, message
    assert "SAME ATTEMPT" in message, message
    assert "IN ITS OWN COMMIT" in message, message


def test_the_refusal_names_phase_25s_glob_and_not_phase_23s():
    """§C6's WHOLE POINT, ASSERTED RATHER THAN ASSUMED.

    `phase23_matched_prereg.prove_first_attempt` hard-codes `results/phase23_matched_*` into its
    refusal text, so reusing it would have emitted a Phase-25 refusal naming the WRONG glob — and
    that module is EDIT-ONCE and already spent, so the text could never be widened. The absence
    below is the check that this module did not inherit that text by copy either.
    """
    with pytest.raises(SystemExit) as refused:
        prove_first_attempt([point_record_path(_POINT_KEY)], point_key=_POINT_KEY)
    message = str(refused.value)
    assert POINT_RECORD_GLOB in message
    assert _PHASE23_MATCHED_GLOB_PREFIX not in message, message


def test_phase25_prereg_does_not_import_the_spent_module():
    """AST over the import nodes — a comment promising not to import is not a check."""
    imported = set()
    for node in ast.walk(_PREREG_TREE):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any("phase23_matched_prereg" in name for name in imported), sorted(imported)


# =================================================================================================
# ===== (c) D-04'S ARMED TRIPWIRE — THE ONE PLANTED RED IN THIS PHASE =====
# =================================================================================================


def _identifier_names(node):
    """Every identifier a function body MENTIONS, resolved from the parse tree.

    `ast.Name.id`, `ast.Attribute.attr` and `ast.keyword.arg` — the third is what catches
    `dp_fn=None` passed as a keyword, which is exactly how the seam-off path is spelled at a call
    site. String literals are deliberately NOT collected: a docstring discussing `torch.equal` is
    prose, and treating it as an assertion is the false-RED class this file exists to avoid.
    """
    found = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            found.add(child.id)
        elif isinstance(child, ast.Attribute):
            found.add(child.attr)
        elif isinstance(child, ast.keyword) and child.arg:
            found.add(child.arg)
    return found


def _bit_identity_violations(*roots):
    """Function bodies pairing a forbidden assertion with BOTH a sigma=0 and a seam-off marker.

    Assertion names match EXACTLY (they are call names); markers match as SUBSTRINGS of an
    identifier, because the natural spelling of the violation is `sigma_zero_adapter` /
    `seam_off_adapter` rather than the bare marker.
    """
    violations = []
    for root in roots:
        for path in sorted(pathlib.Path(root).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                found = _identifier_names(node)
                asserted = sorted(n for n in found if n in BIT_IDENTITY_FORBIDDEN_ASSERTIONS)
                zero = sorted(
                    n for n in found if any(m in n for m in BIT_IDENTITY_SIGMA_ZERO_MARKERS)
                )
                off = sorted(n for n in found if any(m in n for m in BIT_IDENTITY_SEAM_OFF_MARKERS))
                if asserted and zero and off:
                    violations.append((str(path), node.name, asserted, zero, off))
    return violations


def _assert_no_bit_identity_assertions(*roots):
    """The tripwire itself. Both the live guard and the planted probe run THIS body."""
    violations = _bit_identity_violations(*roots)
    listed = "\n".join(
        f"  {path}::{func} — assertion {asserted}, sigma=0 marker(s) {zero}, "
        f"seam-off marker(s) {off}"
        for path, func, asserted, zero, off in violations
    )
    assert not violations, (
        "D-04 TRIPWIRE FIRED — a committed function asserts BIT-IDENTITY between the sigma=0 point "
        "and the seam-off path:\n"
        f"{listed}\n\n"
        f"WHAT THE CORRECT ASSERTION LOOKS LIKE: {BIT_IDENTITY_EXPECTED_DISAGREEMENT}"
    )


def test_no_committed_test_asserts_sigma_zero_seam_off_bit_identity():
    """THE ARMED GUARD, over every committed `.py` under `tests/` and `scripts/`.

    D-04's hazard is a LATER plan "fixing" the sigma=0 / seam-off non-identity by asserting the two
    paths are byte-identical. That would overwrite a MEASURED record — 72/72 LoRA tensors agreeing
    to 2.178e-07 relative, agreement to a bound rather than bit identity — with a claim the
    measurement does not support.
    """
    _assert_no_bit_identity_assertions(_ROOT / "tests", _ROOT / "scripts")


def test_the_bit_identity_tripwire_fires_on_a_planted_violation(tmp_path):
    """WATCHED FIRING AGAINST A SCRATCH COPY — never against a real repo file.

    **WHY THE PLANTED FORM IS USED HERE AND NOWHERE ELSE IN THIS PHASE.** D-04 is the ONLY row in
    `25-RESEARCH.md`'s structural table with **no natural RED**: the guard's entire value is that no
    committed function asserts the forbidden thing, so there is nothing in the tree to watch it fire
    on. Every other refusal in this phase is watched firing on a real call.

    **AND WHY THE SCRATCH COPY.** This repository has been burned by planted REDs landing on the
    WRONG OCCURRENCE of a token inside a real file and then being "reverted" into a false green. A
    synthetic module under `tmp_path` cannot land on the wrong occurrence, because it contains
    exactly one function and nothing else. Nothing is restored afterwards because nothing real was
    touched.
    """
    planted = tmp_path / "test_planted_bit_identity.py"
    planted.write_text(
        '"""A SCRATCH COPY. Never imported, never collected, never committed."""\n'
        "\n"
        "import torch\n"
        "\n"
        "\n"
        "def test_sigma_zero_adapter_is_the_seam_off_adapter():\n"
        "    sigma_zero_adapter = build_adapter(sigma=0.0)\n"
        "    seam_off_adapter = build_adapter(dp_fn=None)\n"
        "    assert torch.equal(sigma_zero_adapter, seam_off_adapter)\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as fired:
        _assert_no_bit_identity_assertions(tmp_path)
    message = str(fired.value)

    assert "test_sigma_zero_adapter_is_the_seam_off_adapter" in message, message
    assert "test_planted_bit_identity.py" in message, message
    assert "equal" in message, message
    assert "2.178e-07" in message, message

    # The real tree is still clean under the SAME body that just fired.
    _assert_no_bit_identity_assertions(_ROOT / "tests", _ROOT / "scripts")


# =================================================================================================
# ===== (d) CTRL-02'S CHEAP PROXY, ASSERTED BEFORE ANY COMPUTE =====
# =================================================================================================


@pytest.mark.parametrize(
    "clip_norm",
    [math.inf, float("nan"), 0.0, -1.0],
    ids=["inf", "nan", "zero", "negative"],
)
def test_clip_domain_is_refused(clip_norm):
    """CTRL-02'S MILLISECOND PROXY, COMMITTED IN WAVE 1 SO IT PRECEDES EVERY GPU-SPENDING PLAN.

    `25-VALIDATION.md`'s CTRL-02 row points here. The requirement's original wording says
    `clip_norm=inf`; the CODE REFUSES THAT VALUE, which is why the control runs at a finite bound
    proven not to bind (C = 1e6, `clip_bind_count == 0`) rather than at infinity.

    **`model=None` IS DELIBERATE, NOT A SHORTCUT.** `DPSGD.__init__`'s PRE-PASS 1 validates the
    caller-supplied numeric domain BEFORE the model is read at all, so this needs no `nn.Module`, no
    device and no GPU. That is the whole reason this check belongs in wave 1: a clip-domain error
    discovered mid-sweep would be discovered days and GPU-hours into a run, and it costs
    milliseconds to discover here instead.

    The `inf` case additionally carries `std nan` — the RECORDED REASON the domain cannot be
    re-widened. The noise std is `sigma * C` at one draw site with no `sigma == 0` branch, so
    `0.0 * inf` is `nan` and `torch.normal` raises `normal expects std >= 0.0, but found std nan`.
    """
    with pytest.raises(ValueError) as refused:
        DPSGD(None, sigma=0.0, clip_norm=clip_norm)
    message = str(refused.value)
    assert "[dp-refusal:clip-domain]" in message, message
    if math.isinf(clip_norm):
        assert "std nan" in message, message


def test_the_control_clip_norm_clears_the_clip_domain_pre_pass():
    """THE POSITIVE CONTROL, AND THE REASON THE PARAMETRIZED REFUSAL ABOVE IS NOT VACUOUS.

    A domain check that refused EVERY value would pass all four cases above and be worthless. The
    sigma=0 control's own `C` — 1e6, the finite bound proven not to bind — must NOT raise a
    clip-domain `ValueError`.

    Measured: it proceeds past PRE-PASS 1 and fails later reading the model that was deliberately
    not supplied. Asserting BOTH halves is what makes this a control rather than a shrug — the
    absence of the marker proves the domain admitted the value, and the `named_parameters` failure
    proves execution actually reached past the numeric pre-pass into the model read.
    """
    with pytest.raises(Exception) as raised:
        DPSGD(None, sigma=0.0, clip_norm=1000000.0)
    message = str(raised.value)
    assert "[dp-refusal:clip-domain]" not in message, message
    assert isinstance(raised.value, AttributeError), raised.value
    assert "named_parameters" in message, message


# =================================================================================================
# ===== (e) THE COMMITTED RULES, ASSERTED STRUCTURALLY RATHER THAN MERELY PRESENT =====
# =================================================================================================

# D-11's tail clause, typed here ONCE so the module must carry it rather than the other way round.
# It line-wraps in the source, which is why the comparison below routes through `_prose.normalized`.
_TAIL_CLAUSE = (
    "if more candidates clear than the budget holds, promote and replicate ALL of them — never a "
    "subset chosen after seeing which cleared"
)


def test_promotion_rule_reads_the_budget_pins():
    """The K values are IMPORTED, and that is checked structurally rather than by value.

    `PROMOTION_RULE["curve_k"] == 16` would pass just as well against a retyped literal, and small
    ints are interned so even `is` proves nothing. The AST half below asserts the VALUES IN THE
    SOURCE are attribute reads on `mitigation_budget`, which is the property that keeps the rule
    from drifting away from the pin `mitigation_gate.ratchet_k` actually enforces.
    """
    assert PROMOTION_RULE["curve_k"] == mitigation_budget.CURVE_K
    assert PROMOTION_RULE["full_k"] == mitigation_budget.FULL_FIDELITY_K

    assignment = next(
        node
        for node in ast.walk(_PREREG_TREE)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "PROMOTION_RULE" for t in node.targets)
    )
    sourced = {}
    for key, value in zip(assignment.value.keys, assignment.value.values):
        if isinstance(key, ast.Constant) and key.value in ("curve_k", "full_k"):
            sourced[key.value] = ast.unparse(value)
    assert sourced == {
        "curve_k": "mitigation_budget.CURVE_K",
        "full_k": "mitigation_budget.FULL_FIDELITY_K",
    }, sourced

    prose = _prose.normalized(" ".join(v for v in PROMOTION_RULE.values() if isinstance(v, str)))
    assert _prose.normalized(_TAIL_CLAUSE) in prose, prose


def test_publication_obligation_names_four_artifact_paths():
    """D-40 commits WHICH strings Phase 28 must carry, as paths into the artifact.

    The denominator clause is asserted against the GATE'S OWN OUTPUT rather than against a sentence:
    `exists_clearing_point` is CALLED here and the fragment the obligation quotes must appear in
    what it actually returns. That is what stops the obligation from quoting a string the gate does
    not produce.
    """
    assert len(PUBLICATION_OBLIGATION) >= 4, PUBLICATION_OBLIGATION
    for entry in PUBLICATION_OBLIGATION:
        assert isinstance(entry, tuple) and len(entry) == 2, entry
        field_path, why = entry
        assert isinstance(field_path, str) and "." in field_path, field_path
        assert isinstance(why, str) and why.strip(), field_path

    paths = [field_path for field_path, _why in PUBLICATION_OBLIGATION]
    assert len(paths) == len(set(paths)), paths

    exists, claim = mitigation_gate.exists_clearing_point(
        points=[("FAIL", ["reason"], "dp")], arm="dp"
    )
    assert exists is False
    fragment = "point(s) examined returned PASS"
    assert fragment in claim, claim
    dp_why = next(why for field_path, why in PUBLICATION_OBLIGATION if field_path.endswith(".dp"))
    assert fragment in dp_why, dp_why

    reasons = " ".join(why for _field_path, why in PUBLICATION_OBLIGATION)
    joined = _prose.normalized(" ".join(paths) + " " + reasons)
    assert "curve_total_epsilon" in joined
    assert "selection_accounted" in joined
    for branch_holder in ("capacity_branch",):
        assert branch_holder in joined
    assert "D-23" in joined and "D-29" in joined, joined


def test_canary_reservations_carry_the_three_fields_and_a_sized_precheck():
    """D-37's three reservations, plus the precheck sized against the MEASURED resume checkpoint.

    D-37's own 59 MB figure counts adapters only. `arm_outputs` also writes a
    `checkpoints/{prefix}_{arm}_latest.pt` per point — the file that makes a killed point resumable
    — and it is 44x larger than the adapter. The precheck must clear both or the sweep dies on a
    full disk around point 30 (T-25-06).
    """
    assert {"adapter_retention", "canary_population_rule", "audit_target_rule"} <= set(
        CANARY_RESERVATIONS
    ), sorted(CANARY_RESERVATIONS)

    measured = _SWEEP_POINT_COUNT * (_ADAPTER_BYTES + _RESUME_CHECKPOINT_BYTES)
    assert measured > 2_600_000_000, measured
    assert DISK_PRECHECK_BYTES >= measured, (DISK_PRECHECK_BYTES, measured)
    assert CANARY_RESERVATIONS["disk_precheck_bytes"] == DISK_PRECHECK_BYTES

    retention = _prose.normalized(CANARY_RESERVATIONS["adapter_retention"])
    assert "sha256" in retention and ".gitignore" in retention, retention

    population = _prose.normalized(CANARY_RESERVATIONS["canary_population_rule"])
    assert "56" in population and "64" in population, population

    audit = _prose.normalized(CANARY_RESERVATIONS["audit_target_rule"])
    assert "point_keys" in audit, audit
    assert "n=8" in audit, audit
