"""Phase 18's PROSE guards — the conclusion is generated, and its numbers are the run's numbers.

CPU-only, GPU-free, no checkpoint I/O, no model load. Two claims are pinned here, and both are
about the boundary D-24 draws between the driver's literals and the report's paragraphs:

  1. ``licensed_conclusion`` produces its closing paragraph FROM ``ATTACKER_HAS`` /
     ``ATTACKER_LACKS`` and the measured counts, so a scope claim the run did not obey has no
     route into the text. Proved by MUTATION — a sentinel added to the literal must appear in the
     output — because "the prose reads the literals" is otherwise indistinguishable from two
     parallel-maintained copies that happen to agree today.
  2. The numbers the threat model states in prose are the numbers the run actually used. The
     sampling parameters are interpolated from ``phase14_recall`` and need no check; the mask size
     is a MEASURED count that no import-time constant carries, so it is cross-checked against the
     committed arm record instead of trusted.

Why a separate file from ``test_phase18_prereg.py``: that one pins what the driver IS (its static
clean room, its arithmetic, its ancestry). This one pins what the driver SAYS. The two fail for
different reasons and a reader chasing a red should not have to guess which.
"""

import importlib.util
import json
import pathlib
import re
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_EXTRACTION_PATH = _REPO_ROOT / "scripts" / "phase18_extraction.py"

# The committed arm record the threat model's mask numbers are checked against. Tracked, and
# produced by Phase 16's own run — so the figure the audit publishes about its attacker is the
# figure a previous phase measured, not a number this phase asserts about itself.
_ARM_RECORD = _REPO_ROOT / "results" / "phase16_arm_adapter-only.json"


def _load():
    spec = importlib.util.spec_from_file_location("phase18_extraction", _EXTRACTION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conclusion_is_templated(monkeypatch):
    """D-24 — the closing paragraph is generated from the literals the run obeyed.

    Driven at both outcomes, because they are different failure modes. At NONZERO successes the
    risk is a rate published without its bound. At ZERO successes the risk is the one STAT-02
    names: a bare ``0%``, which states a certainty 104 questions cannot support and which is
    exactly what a reader remembers. The rule-of-three ceiling is required alongside the Wilson
    bound at zero so the two disagreeing slightly is visible rather than resolved in silence.

    The mutation is the load-bearing assertion. Both required sentences being present proves only
    that someone typed them; a sentinel appended to ``ATTACKER_LACKS`` appearing in the output
    proves the scope in the prose is READ from the scope the run obeyed. Without it, the two could
    drift apart the moment one of them is edited and every other assertion here would stay green.
    """
    extraction = _load()
    conclude = extraction.licensed_conclusion

    zero = conclude(
        successes=0,
        n_questions=104,
        arm=extraction.ARMS[0],
        tier=extraction.GATED_TIER,
        families_run=extraction.ATTACK_FAMILIES,
    )

    assert "104" in zero, zero
    assert "3/104" in zero, f"the rule-of-three ceiling is not stated at zero successes: {zero}"
    wilson = extraction.erasure_gate.wilson_upper_bound(0, 104)
    assert f"{wilson:.2%}" in zero, (
        f"the Wilson upper bound {wilson:.2%} is not interpolated into the zero-success "
        f"conclusion, so the zero is published without the bound that qualifies it: {zero}"
    )
    assert re.search(r"\b0(\.0+)?%", zero) is None, (
        f"the conclusion renders a bare zero percentage: {zero}. STAT-02 forbids it in any "
        "committed report, because a bare zero states a certainty the sample does not have"
    )

    assert zero.rstrip().rstrip(".").endswith(extraction.LOWER_BOUND_SENTENCE), (
        f"the conclusion does not CLOSE on D-24's required sentence: {zero[-200:]!r}"
    )
    assert extraction.LORA_PROPERTY_CAVEAT in zero, (
        "ATK-06's caveat — a low extraction rate may be a property of LoRA's capacity rather than "
        "a PersonaCore achievement — is required ADJACENT to the closing claim"
    )

    # Nonzero: the rate appears with its denominator and its bound, and the same two sentences
    # still close the paragraph. A conclusion that qualified only its nulls would be a conclusion
    # qualifying whichever outcome was inconvenient.
    some = conclude(
        successes=7,
        n_questions=104,
        arm=extraction.ARMS[0],
        tier=extraction.GATED_TIER,
        families_run=extraction.ATTACK_FAMILIES,
    )
    assert "7" in some and "104" in some
    assert f"{extraction.erasure_gate.wilson_upper_bound(7, 104):.2%}" in some, some
    assert extraction.LOWER_BOUND_SENTENCE in some and extraction.LORA_PROPERTY_CAVEAT in some

    # THE MUTATION. A sentinel in the literal must reach the text.
    sentinel = "a capability the run did not grant"
    monkeypatch.setattr(extraction, "ATTACKER_LACKS", extraction.ATTACKER_LACKS + (sentinel,))
    assert sentinel in conclude(
        successes=0,
        n_questions=104,
        arm=extraction.ARMS[0],
        tier=extraction.GATED_TIER,
        families_run=extraction.ATTACK_FAMILIES,
    ), (
        "a change to ATTACKER_LACKS did not propagate into the conclusion, so the prose is a "
        "second copy of the threat model rather than a rendering of it — and a second copy is "
        "free to stop agreeing with the run on the commit after this one"
    )

    # A scope claim naming an arm, tier or family the run did not obey is refused at the source.
    with pytest.raises(SystemExit):
        conclude(
            successes=0,
            n_questions=104,
            arm="adapter-on-but-different",
            tier=extraction.GATED_TIER,
            families_run=extraction.ATTACK_FAMILIES,
        )
    with pytest.raises(SystemExit):
        conclude(
            successes=0,
            n_questions=104,
            arm=extraction.ARMS[0],
            tier=extraction.GATED_TIER,
            families_run=("A9-unrun",),
        )


def test_threat_model_numbers_match_the_committed_run():
    """D-24 — the mask size the prose states is the mask size a committed run recorded.

    The sampling parameters need no check here: ``ATTACKER_HAS`` interpolates them from
    ``phase14_recall``, so they move with the run by construction. The mask size does not — it is
    a count over a LOADED tokenizer, available to no import-time constant, so the prose carries a
    literal. A literal nothing checks is the exact shape D-24 exists to prevent, and the check is
    cheap: Phase 16's arm record already published both numbers.
    """
    extraction = _load()
    record = json.loads(_ARM_RECORD.read_text(encoding="utf-8"))
    joined = " ".join(extraction.ATTACKER_HAS)

    masked = record["forbid_ids_masked"]
    assert f"{masked:,}" in joined, (
        f"the threat model states a masked-id count that is not the {masked:,} "
        f"{_ARM_RECORD.name} recorded — the audit would be describing an attacker other than the "
        "one every measurement in this project actually ran"
    )
    assert f"{record['vocab_size']:,}" in joined, (
        f"the threat model's vocabulary size disagrees with the committed {record['vocab_size']:,}"
    )
    live = record["vocab_size"] - record["forbid_ids_masked"]
    assert str(live) in joined, (
        f"the {live} LIVE ids are not stated. The mask is what makes the attacker stronger, not "
        "weaker, and stating only the masked count invites the opposite reading"
    )

    for value in (
        extraction.persistence.recall.SAMPLE_TEMPERATURE,
        extraction.persistence.recall.SAMPLE_TOP_P,
    ):
        assert str(value) in joined, (
            f"decode setting {value} is absent from ATTACKER_HAS — it is interpolated from "
            "phase14_recall, so its absence means the sentence that carried it was rewritten"
        )
