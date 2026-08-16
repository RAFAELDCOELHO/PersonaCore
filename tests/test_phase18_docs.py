"""Phase 18's PROSE guards — the conclusion is generated, and its numbers are the run's numbers.

CPU-only, GPU-free, no checkpoint I/O, no model load. Two claims are pinned here, and both are
about the boundary D-24 draws between the driver's literals and the report's paragraphs
(SC5 adds three more, at the bottom, about the boundary between one sentence and three surfaces):

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

import ast
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


# --------------------------------------------------------------------------- #
# SC5 / D-23 — one sentence, three surfaces, two of them EXTENDED not edited
# --------------------------------------------------------------------------- #

_README = _REPO_ROOT / "README.md"
_REPORT = _REPO_ROOT / "docs" / "REPORT.md"
_DEMO = _REPO_ROOT / "scripts" / "personalize_demo.py"

# The demo constant that IS the sentence. Named here, never retyped: a copy typed into this file
# would be a FOURTH copy, free to drift — and the drift would leave this test green while the three
# published surfaces disagreed with each other, which is the exact failure it exists to catch.
_SENTENCE_CONSTANT = "TOGGLE_IS_AVAILABILITY"

# Each file's continuation heading, as an anchor PREFIX that must end on a WORD character —
# ``_anchored_section``'s ``\b`` finds no boundary after ``:`` or an em dash, so a prefix ending in
# punctuation would silently match nothing. The casing differs because each file's own heading
# style differs: README writes ``## `` headings in sentence case, docs/REPORT.md in Title Case.
_CONTINUATION_HEADINGS = {
    _README: "## Claim correction",
    _REPORT: "## Claim Correction",
}

# Every ``## `` heading each file carried BEFORE the dated continuation was appended, in order.
#
# Committed as literals rather than read back from git. ``git show <sha>:<file>`` is only checkable
# where that commit is reachable, and CI clones shallow (``actions/checkout@v4`` defaults to
# ``fetch-depth: 1``), where the lookup dies with ``fatal: bad object`` / exit 128. This is the same
# reasoning that pinned ``tests/test_phase14_demo.py::_DEMO_APP_SHA256`` as content, not as an id.
_README_HEADINGS_BEFORE = (
    "## Results at a glance",
    "## Where the memory actually moved",
    "## What is this?",
    "## Run the demo",
    "## Evidence",
    "## Tests and reproducibility",
    "## Milestone 2 — what shipped",
)

_REPORT_HEADINGS_BEFORE = (
    "## The Thesis, and What This Milestone Claims",
    "## What Was Built",
    "## Decision: Byte-Level BPE from Scratch, Vocabulary Locked Before Model Sizing",
    "## Decision: A Bigram Baseline Proved the Harness Before the Transformer Existed",
    "## Decision: Pre-Norm Decoder Blocks, Mask Before Softmax",
    "## Decision: Manual Attention by Hand, with an sdpa Equivalence Path",
    "## Decision: Weight Tying as a True Shared Tensor",
    "## Decision: GPT-2-Style Init, Residual Scaling on Both Output Projections",
    "## Decision: The Milestone 2 Seams Are Milestone 1 Acceptance Criteria",
    "## Decision: fp32 On-Device Training on Apple Silicon as the Primary Run",
    "## Decision: A Hand-Rolled Training Loop with Offline CSV Logging",
    "## Decision: Perplexity with an Auditable Denominator",
    "## Decision: An Architecture Ablation Cohort, Honestly Bounded",
    "## Decision: One Shared generate() for Tests, Notebook, and Demo",
    "## Decision: A Slim Shippable Artifact That Never Executes Code on Load",
    "## Decision: An Offline Story-Completion Demo, Not a Fake Chatbot",
    "## Results",
    "## Reproducibility",
    "## Milestone 1 Ends Here — Everything Below This Line Is As Written on 2026-06-10",
    "## Limitations and the Milestone 2 Roadmap",
    "## Where to Go Next",
    "## Milestone 2 Begins Here — Weight-Based Memory",
    "## Decision: Two Mechanisms in Two Stages, Not One Combined Run",
    "## Decision: The Tokenizer Stays Frozen for v2.0, and the Inflation Tax Is Measured "
    "Rather Than Assumed",
    "## Decision: Pre-Registration Lives in Committed Code, Before Any Number Exists",
    "## Decision: Gate Only the Part of a Claim the Sample Size Supports",
    "## Decision: Honest Negatives Stand Unamended; Discretionary Continuations Are Logged "
    "Separately and Dated After",
    "## Decision: Structural Enforcement Replaces Declared Invariants",
    "## Decision: Extract Once, Then Plot From the Committed Artifact Only",
    "## Milestone 2 Results: What Three Experiments Showed",
    "## Milestone 2 Limitations — Nine Honest Negatives, Quoted",
)


def _read_doc(path):
    """Read a published doc and refuse to return an empty string.

    ``tests/test_phase15_docs.py::_read``'s meta-guard habit: a renamed or emptied surface must
    fail loudly here rather than make every containment assertion below pass vacuously.
    """
    assert path.exists(), f"{path.name} is missing — a published surface was renamed or deleted"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path.name} read empty"
    return text


def _anchored_section(text, heading, stop=r"## "):
    """The slice from ``heading`` at line start up to the next ``stop`` heading, or EOF.

    The SHAPE of ``tests/test_phase15_docs.py::_anchored_section``, copied rather than imported
    (``tests/`` is not a package, so a cross-module import here would be a fragile path trick).
    Anchored on the section, never a tail taken after the LAST occurrence of a heading literal:
    that form is the CR-02 failure recorded at ``scripts/phase14_recall.py:1627-1635``, where a
    later section quoting a heading in its own prose sent the guard into the prose instead of the
    section. Both continuations read here name other headings inside their own text, so the
    anchored form is a correctness requirement and not a style preference.
    """
    found = re.compile(rf"^{re.escape(heading)}\b.*?(?=^{stop}|\Z)", re.M | re.S).search(text)
    return found.group(0) if found else None


def _demo_sentence():
    """The corrected sentence, read from its ONE source of truth by AST — never retyped.

    Parsed rather than imported: ``scripts/personalize_demo.py`` imports gradio and torch at module
    scope, and this file's stated contract is model-free and framework-free. The plan's rule is the
    same either way — read the module's literal, never the Gradio app object.

    ``ast.literal_eval`` also earns its place as a guard. The constant must stay a PLAIN string
    literal; an f-string there would raise here, which is the correct outcome, because a sentence
    assembled at runtime cannot be matched character for character inside a Markdown file.
    """
    tree = ast.parse(_DEMO.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == _SENTENCE_CONSTANT
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(
        f"{_SENTENCE_CONSTANT} is gone from {_DEMO.name} — the sentence three published surfaces "
        "are checked against no longer has a source of truth"
    )


def test_claim_sentence_is_verbatim_in_three_surfaces():
    """T-18-12-02 — the corrected sentence is character-for-character identical on all three.

    Three hand-maintained copies are three chances for the published claim to disagree with itself,
    so there are not three copies: the demo constant is the source, and the two Markdown surfaces
    are asserted to CONTAIN it. Containment is exact — no normalization, no whitespace collapsing —
    which is why the sentence occupies a single unwrapped line in both documents.

    Each read is ANCHORED on that file's continuation heading rather than run against the whole
    file. A whole-file assertion would stay green if the sentence were deleted from the continuation
    and happened to survive in a quotation elsewhere in the document.
    """
    sentence = _demo_sentence()
    assert sentence.strip(), f"{_SENTENCE_CONSTANT} is empty — every check below would be vacuous"
    assert "availability, not authorization" in sentence, (
        f"{_SENTENCE_CONSTANT} no longer carries D-23's correction: {sentence!r}"
    )

    for path in (_README, _REPORT):
        text = _read_doc(path)
        assert sentence in text, (
            f"{path.name} does not carry the sentence character for character. The demo literal "
            f"is the source of truth and this file is a copy of it: {sentence!r}"
        )

        heading = _CONTINUATION_HEADINGS[path]
        section = _anchored_section(text, heading)
        assert section, (
            f"{heading!r} section not found in {path.name} — the dated continuation that carries "
            "the correction is gone, or its heading was reworded"
        )
        assert sentence in section, (
            f"{path.name} carries the sentence somewhere, but NOT inside its dated continuation. "
            "A correction that has drifted out of its dated section is no longer dated"
        )

    # T-18-12-04 — ATK-06's caveat, without which a low rate reads as an achievement. Required in
    # the report specifically: it is the surface that will carry the measured number.
    assert re.search(r"LoRA property|property of LoRA", _read_doc(_REPORT)), (
        "docs/REPORT.md no longer records that a low extraction rate may be a property of LoRA at "
        "this capacity rather than an achievement of PersonaCore's design. That is the "
        "literature's headline finding, not a hedge, and dropping it lets a comfortable number "
        "read as a result this audit has no arm to attribute"
    )


def test_docs_continuation_is_additive():
    """T-18-12-01 — the continuation displaced nothing; every prior heading survives, in order.

    PREFIX EQUALITY, not set membership. An append leaves the prior headings as the first N in
    their original order, so ``headings[:N] == baseline`` proves presence AND order AND that the
    new material landed at the end, all in one assertion. A set check would pass on a document
    whose sections had been shuffled, and shuffling shipped text is exactly the tampering the
    dated-continuation rule exists to make visible.
    """
    for path, baseline in (
        (_README, _README_HEADINGS_BEFORE),
        (_REPORT, _REPORT_HEADINGS_BEFORE),
    ):
        text = _read_doc(path)
        headings = re.findall(r"^## .+$", text, re.M)

        # Meta-guards, both BEFORE anything is asserted about ordering: a scan that silently
        # matched nothing, or an empty baseline, would make every assertion below vacuously true
        # and would report the result as a pass.
        assert headings, f"no `## ` headings found in {path.name} — the heading scan broke"
        assert baseline, f"the {path.name} heading baseline is empty — the fixture broke"

        assert len(headings) > len(baseline), (
            f"{path.name} carries no heading beyond the {len(baseline)} it had before the "
            "continuation — the dated section is not there at all"
        )

        prefix = headings[: len(baseline)]
        diverged = [
            (i, got, want) for i, (got, want) in enumerate(zip(prefix, baseline)) if got != want
        ]
        assert not diverged, (
            f"{path.name}: heading {diverged[0][0]} now reads {diverged[0][1]!r} but was "
            f"{diverged[0][2]!r} before the continuation. An append cannot displace, reorder or "
            "reword a prior heading — this is an in-place edit of published text"
        )

        assert any(h.startswith(_CONTINUATION_HEADINGS[path]) for h in headings[len(baseline) :]), (
            f"{path.name}'s new headings are {headings[len(baseline) :]}, none of which is the "
            f"dated continuation {_CONTINUATION_HEADINGS[path]!r}"
        )


def test_no_bare_zero_percent_in_docs():
    """STAT-02 — no bare zero percentage in either committed doc surface.

    The regex ``licensed_conclusion`` proves itself against, applied to the two files a reader
    actually reads. A bare ``0%`` states a certainty no sample of this size supports, and it is the
    figure a reader remembers; every zero this phase publishes must arrive with its denominator,
    its Wilson bound and its rule-of-three ceiling.

    The regex is exercised against controls FIRST. A scan that had stopped matching would otherwise
    report the strongest possible result — no hits anywhere — while checking nothing at all.
    """
    pattern = re.compile(r"\b0(\.0+)?%")
    assert pattern.search("extracted 0% of 104 questions"), "the bare-zero regex stopped matching"
    assert pattern.search("a rate of 0.00%"), "the bare-zero regex misses a padded zero"
    assert pattern.search("a 10% rate") is None, "the regex fires on a nonzero rate"

    for path in (_README, _REPORT):
        text = _read_doc(path)
        found = pattern.search(text)
        assert found is None, (
            f"{path.name} publishes a bare zero percentage at offset {found.start()}: "
            f"{text[max(0, found.start() - 90) : found.end() + 40]!r}"
        )
