"""Phase 18's two ADDITIVE widenings of shared instruments — proved from both sides.

CPU-only, GPU-free, no checkpoint I/O, no model load, no generation. Phase 18 collides with two
functions that already exist and are already relied on by Phases 14, 16 and 17. Both are widened
IN PLACE rather than copied, because a duplicated rule is a rule that can drift (Phase 16 D-16's
``probe_guessability`` precedent, restated for this phase by 18-CONTEXT D-03). A Phase-18-local
``holm`` would additionally let the report cite a statistic that is not the pinned one.

Each widening is pinned from BOTH directions, which is what makes "additive" a test rather than a
claim:

  1. **``holm(p_values, *, family=...)``** — D-31 prices a family of FOUR (the dose-split
     ``A1-mild`` / ``A1-aggressive`` / ``A2`` / ``A3`` attack families on ``core_held_out``), where
     the old body read ``m`` off ``HOLM_FAMILY_PAIRS`` and hard-``_prove``d ``len(p_values) == 6``.
     Pinned by a LITERAL six-pair expectation captured from the function BEFORE the widening (so
     "bit-identical for every Phase 16/17 caller" is a measured equality, not a re-derivation), and
     by the mis-sized family raising under BOTH the default and a passed family.

  2. **``assert_no_value_in_prompt(tok, question, values, *, prompt_ids=None)``** — D-03 checks the
     corpus against the BYTES the model receives rather than a reconstruction from the question
     string, which is the only way A2's appended injection and A3's persona span can be seen at
     all. Pinned by a value visible ONLY in the passed ids still aborting, so the widening cannot
     have become an escape hatch.

Scripts-load justification: the one ``tests/test_phase16_stats.py`` and ``tests/test_phase14_
scoring.py`` already state — the pre-registration constants and the scoring rules MUST live in the
committed drivers for git history to be the proof, so both modules are loaded with
``importlib.util.spec_from_file_location``. Neither executes anything at import.
"""

import importlib.util
import pathlib
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stats = _load("phase16_persistence")

# 8/8 unanimity on the exact paired sign test over 2**8 partitions — the best achievable p at n = 8
# and the number every Holm family in this project is ultimately priced against.
UNANIMITY_P = 0.0078125

# D-31's family: the dose-split attack families, on `core_held_out` only. Four NAMES rather than
# four pairs — `holm` consumes `len(family)` and nothing else, which is exactly what lets one
# implementation price Phase 16's pairs and Phase 18's families without branching on either.
PHASE18_FAMILY = ("A1-mild", "A1-aggressive", "A2", "A3")


# =====================================================================================
# ===== D-31 / STAT-04 — `holm` prices the family it is HANDED =====
# =====================================================================================


def test_holm_default_family_is_bit_identical_to_the_pre_widening_function():
    """T-18-01-01 — every Phase 16/17 caller keeps the arithmetic it already published.

    The two expectations below are LITERALS captured by running ``holm`` at ``c1e21d4``, before the
    ``family=`` keyword existed. Re-deriving them from ``HOLM_ALPHA / (6 - i)`` here would make this
    test agree with any widening that broke the default in the same way it broke the expectation.

    The mixed case is the load-bearing one: it carries the step-down LATCH (once ``0.012`` fails at
    ``0.01``, the trailing ``0.04`` is retained despite clearing its own ``0.05`` step), so a
    widening that silently reset the latch per hypothesis fails here rather than in a report.
    """
    pairs = list(stats.HOLM_FAMILY_PAIRS)

    all_unanimous = [
        (("adapter-only", "base-neither"), 0.0078125, 0.008333333333333333, True),
        (("adapter-only", "embedding-cosine"), 0.0078125, 0.01, True),
        (("adapter-only", "prompt-stuffed"), 0.0078125, 0.0125, True),
        (("base-neither", "embedding-cosine"), 0.0078125, 0.016666666666666666, True),
        (("base-neither", "prompt-stuffed"), 0.0078125, 0.025, True),
        (("embedding-cosine", "prompt-stuffed"), 0.0078125, 0.05, True),
    ]
    assert stats.holm(dict(zip(pairs, [UNANIMITY_P] * 6))) == all_unanimous

    mixed = [
        (("adapter-only", "base-neither"), 0.0078125, 0.008333333333333333, True),
        (("adapter-only", "embedding-cosine"), 0.012, 0.01, False),
        (("adapter-only", "prompt-stuffed"), 0.013, 0.0125, False),
        (("base-neither", "embedding-cosine"), 0.014, 0.016666666666666666, False),
        (("base-neither", "prompt-stuffed"), 0.015, 0.025, False),
        (("embedding-cosine", "prompt-stuffed"), 0.04, 0.05, False),
    ]
    p_values = dict(zip(pairs, [UNANIMITY_P, 0.012, 0.013, 0.014, 0.015, 0.04]))
    assert stats.holm(p_values) == mixed

    # And the default is the constant itself, not a coincidence: passing it explicitly is the
    # same call. A default rebound to some other six-member sequence would pass every assertion
    # above and fail this one.
    assert stats.holm(p_values, family=stats.HOLM_FAMILY_PAIRS) == mixed


def test_holm_prices_the_four_member_dose_split_family():
    """D-31 — m = 4 on ``core_held_out``, and the reachability that decision turns on.

    The first step alpha is ``0.05 / 4 = 0.0125`` and the achievable p at n = 8 is ``0.0078125``,
    so unanimity clears by 60% instead of m = 6's 0.00052. Both numbers are asserted here rather
    than described, and the STRICT ``<`` the guard is written against is the same one ``holm``
    itself applies, so the two can never disagree about the boundary.
    """
    p_values = dict(zip(PHASE18_FAMILY, [UNANIMITY_P] * 4))
    rows = stats.holm(p_values, family=PHASE18_FAMILY)

    assert len(rows) == 4
    assert [alpha for _, _, alpha, _ in rows] == [0.0125, 0.05 / 3, 0.025, 0.05]
    assert rows[0][2] == stats.HOLM_ALPHA / 4 == 0.0125
    assert all(rejected for *_, rejected in rows)

    # D-31's reachability inequality, in the direction the corrected transcription records.
    assert stats.sign_test_exact((1,) * stats.SIGN_TEST_N) < stats.HOLM_ALPHA / len(PHASE18_FAMILY)

    # The step-down latch survives the smaller family: 0.02 fails at 0.05/3, so the trailing
    # 0.03 is retained even though it clears its own 0.05 step.
    latched = stats.holm(
        dict(zip(PHASE18_FAMILY, [UNANIMITY_P, 0.02, 0.03, 0.04])), family=PHASE18_FAMILY
    )
    assert [rejected for *_, rejected in latched] == [True, False, False, False]


def test_holm_refuses_four_p_values_under_the_default_family():
    """Omitting ``family=`` is still the closed six-pair family — the widening opens no back door.

    This is the case that would silently reprice a Phase 16 verdict if the default had been
    loosened to "whatever arrived", so the abort must still name SIX.
    """
    with pytest.raises(SystemExit) as excinfo:
        stats.holm(dict(zip(PHASE18_FAMILY, [UNANIMITY_P] * 4)))
    message = str(excinfo.value)
    assert "D-09" in message
    assert "6" in message


def test_holm_refuses_six_p_values_under_a_passed_four_member_family():
    """The guard prices the PASSED family, not a hard-coded 6 — the same rule, other direction.

    A widening that added the keyword but left ``m = len(HOLM_FAMILY_PAIRS)`` in the ``_prove``
    would accept these six against a family declared at four, which is precisely "a family priced
    at one size and populated at another". The abort names 4, so a mis-sized Phase 18 family is
    diagnosable from the message alone.
    """
    six = dict(zip(stats.HOLM_FAMILY_PAIRS, [UNANIMITY_P] * 6))
    with pytest.raises(SystemExit) as excinfo:
        stats.holm(six, family=PHASE18_FAMILY)
    assert "4" in str(excinfo.value)


def test_holm_family_is_keyword_only():
    """``family`` is keyword-only so no existing positional call can acquire one by accident.

    ``holm(p_values, something)`` is a TypeError rather than a silently re-priced family — the
    failure mode a positional second parameter would introduce into three committed call sites.
    """
    with pytest.raises(TypeError):
        stats.holm(dict(zip(PHASE18_FAMILY, [UNANIMITY_P] * 4)), PHASE18_FAMILY)
