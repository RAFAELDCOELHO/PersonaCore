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


# --------------------------------------------------------------------------- #
# 18-11 — the RENDERED report: the half a source scan structurally cannot do
# --------------------------------------------------------------------------- #
#
# Node ids below are deliberately distinct from 18-12's document-level pair above
# (``test_docs_continuation_is_additive`` / ``test_no_bare_zero_percent_in_docs``). A duplicate
# ``def`` in one module binds the later one and DELETES the earlier guard with no error and no
# collection warning — the two pairs check different surfaces (published docs vs the report this
# driver renders) and losing either to a name collision would be silent.

# The all-zero fixture's shape. 8 facts x 13 questions is the 104 `core_held_out` questions the
# gated tier actually holds, which is what makes the rendered rule-of-three read `3/104` — the
# denominator a reader checks the ceiling against. The taught tier is deliberately SMALLER: the
# tier-split section only has to render, and a second 104-question tier would double a fixture
# whose whole content is zeros.
_GATED_QUESTIONS_PER_FACT = 13
_TAUGHT_QUESTIONS_PER_FACT = 2
_FIXTURE_DRAWS = 48  # `unique_successes` publishes at K, so the fixture must carry K draws.
_MISS = "i have no idea at all."


def _zero_records(extraction, *, tier, questions_per_fact, families=None):
    """Draw records for every (family, arm) cell of one tier, every completion a MISS.

    All-zero is not an arbitrary fixture. It is this phase's HOPED-FOR outcome and the one input
    that most tempts a bare ``0%`` — every proportion in the report is a zero, so a renderer that
    dropped a denominator anywhere would be caught here and nowhere else.
    """
    families = extraction.ATTACK_FAMILIES if families is None else families
    records = []
    for family in families:
        for arm in extraction.ARMS:
            for fact_index, slot in enumerate(extraction.CORE_SLOTS):
                for seed_index in range(questions_per_fact):
                    records.append(
                        {
                            "family": family,
                            "dose": family.split("-", 1)[1] if family.startswith("A1-") else None,
                            "fact_id": f"core-{fact_index}",
                            "slot": slot,
                            "tier": tier,
                            "arm": arm,
                            "seed_index": seed_index,
                            # A2 is the one family `score_records` judges post-concatenation, so it
                            # must carry a recorded prefix or the scorer refuses the record.
                            "prefix_text": "zz" if family == "A2" else None,
                            "completions": [_MISS] * _FIXTURE_DRAWS,
                        }
                    )
    # A value no completion contains, supplied as a PARAMETER — `score_records` takes its values
    # that way precisely so a fixture never has to reach the fact set.
    return extraction.score_records(records, {f"core-{i}": "unrelatedcanary" for i in range(8)})


def _zero_verdict(extraction):
    """``assemble_verdict``'s own record over the all-zero fixture — NULL_ADMISSIBLE.

    The real orchestrator, not a hand-built dict: the verdict, the Holm rows, the handoff and the
    conclusion paragraph the report publishes are the ones the committed instruments produced, so a
    change to any of their shapes reddens the renderer here rather than at report time.

    ``control_reference`` is supplied synthetically so this stays a test about the RENDERER; the
    parse of the real committed taught rows is pinned in ``test_phase18_prereg.py``.
    """
    gated = _zero_records(extraction, tier=extraction.GATED_TIER, questions_per_fact=13)
    reference = tuple(
        {
            "fact_id": f"core-{index // 14}",
            "seed_index": index,
            "question": f"q{index}",
            "k": 0,
            "n": extraction.FAMILY_ZERO_DRAWS,
        }
        for index in range(extraction.PHASE14_TAUGHT_QUESTIONS)
    )
    recorded = [
        {
            "fact_id": row["fact_id"],
            "seed_index": row["seed_index"],
            "hits": [False] * extraction.FAMILY_ZERO_DRAWS,
            "n_draws": extraction.FAMILY_ZERO_DRAWS,
        }
        for row in reference
    ]
    per_fact_by_family = {
        family: {
            arm: extraction.aggregate_questions(
                [record for record in gated if record["family"] == family and record["arm"] == arm],
                tier=extraction.GATED_TIER,
            )
            for arm in extraction.ARMS
        }
        for family in extraction.ATTACK_FAMILIES
    }
    n_questions = 8 * _GATED_QUESTIONS_PER_FACT
    return extraction.assemble_verdict(
        control_recorded=recorded,
        control_reference=reference,
        admissibility={
            "draws_spent": 1,
            "draws_declared": 1,
            "base_arm_draws_spent": 1,
            "attack_successes": 0,
            "zero_cells": {
                key: {"successes": 0, "exposure_rank": 1}
                for key in extraction.ADMISSIBILITY_ZERO_KEYS
            },
        },
        per_fact_by_family=per_fact_by_family,
        question_counts={
            family: {arm: {"successes": 0, "n_questions": n_questions} for arm in extraction.ARMS}
            for family in extraction.ATTACK_FAMILIES
        },
        resamples=32,  # DESCRIPTIVE intervals; no branch in this test reads their width.
    )


def _render_zero_report(extraction, path):
    """Render the whole report from the all-zero fixture into ``path`` and return its text."""
    gated = _zero_records(
        extraction, tier=extraction.GATED_TIER, questions_per_fact=_GATED_QUESTIONS_PER_FACT
    )
    taught = _zero_records(
        extraction, tier=extraction.REPORTED_TIER, questions_per_fact=_TAUGHT_QUESTIONS_PER_FACT
    )
    scored = gated + taught
    ladders = [
        extraction.asr_ladder(scored, family=family, arm=arm, tier=tier)
        for tier in extraction.CORPUS_TIERS
        for family in extraction.ATTACK_FAMILIES
        for arm in extraction.ARMS
    ]
    curves = [
        extraction.cumulative_by_attempt(scored, family=family, arm=arm, tier=tier)
        for tier in extraction.CORPUS_TIERS
        for family in extraction.ATTACK_FAMILIES
        for arm in extraction.ARMS
    ]
    one_cell = [
        record
        for record in gated
        if record["arm"] == extraction.ARMS[0] and record["seed_index"] == 0
    ]
    uniques = [
        extraction.unique_successes(one_cell, draws=draws, families=("A1", "A2", "A3"))
        for draws in (extraction.FAMILY_ZERO_DRAWS, extraction.K)
    ]
    return extraction.render_report(
        ladders=ladders,
        curves=curves,
        injection=[
            {"slot": slot, "realized": {budget: 27}}
            for slot, budget in zip(
                extraction.CORE_SLOTS, extraction.INJECTION_BUDGET_DECLARED, strict=True
            )
        ],
        exposure=[
            {
                "slot": slot,
                "admissible": (
                    extraction.ADMISSIBLE_NLL_FRAME,
                    extraction.ADMISSIBLE_NLL_REDUCTION,
                ),
                "nll": {
                    frame: {reduction: 1.5 for reduction in extraction.NLL_REDUCTIONS}
                    for frame in extraction.NLL_FRAMES
                },
                "rank": 1,
                "exposure_bits": 3.0,
                "ceiling_bits": 3.0,
                "n_references": 8,
                "length_spread": 0 if slot in extraction.SPREAD_ZERO_CONTROL_SLOTS else 3,
                "spread_zero_control": slot in extraction.SPREAD_ZERO_CONTROL_SLOTS,
                "descriptive_label": extraction.EXPOSURE_DESCRIPTIVE_LABEL,
                "threats_to_validity": extraction.EXPOSURE_THREATS_TO_VALIDITY,
            }
            for slot in extraction.CORE_SLOTS
        ],
        uniques=uniques,
        verdict=_zero_verdict(extraction),
        provenance=[
            {
                "arm": arm,
                "adapter_enabled": arm == extraction.ARMS[0],
                "git_sha": "deadbee",
                "pid": 4242 + index,
                "device": "cpu",
                "wall_clock_min": 492.0,
                "corpus_sha256": "c" * 64,
                "forbid_ids_sha256": "f" * 64,
            }
            for index, arm in enumerate(extraction.ARMS)
        ],
        path=path,
    )


def test_no_bare_zero_percent_in_rendered_report(tmp_path):
    """STAT-02 over the RENDERED report — the half a source scan structurally cannot do.

    ``test_no_bare_zero_percent_in_docs`` below scans two committed documents and
    ``tests/test_phase18_prereg.py`` scans this driver's source. Neither can see a number a format
    string produced, and that is precisely how a bare ``0%`` reaches a published report: nothing in
    the template contains one. So the scan runs on the text ``render_report`` actually returns,
    driven by the ALL-ZERO fixture — this phase's hoped-for outcome and the input where every
    single proportion in the report is a zero.

    The three positive assertions below are not decoration. A renderer that dropped its
    denominators entirely would satisfy the bare-zero regex perfectly while publishing exactly the
    certainty STAT-02 forbids, so the ceiling, the label and both denominators are asserted
    PRESENT in the same pass that asserts the bare zero absent.
    """
    extraction = _load()
    text = _render_zero_report(extraction, tmp_path / "phase18_extraction_report.md")

    pattern = re.compile(r"\b0(\.0+)?%")
    assert pattern.search("extracted 0% of 104 questions"), "the bare-zero regex stopped matching"
    found = pattern.search(text)
    assert found is None, (
        f"the rendered report publishes a bare zero percentage at offset "
        f"{found.start() if found else -1}: "
        f"{text[max(0, found.start() - 90) : found.end() + 40]!r}"
    )

    assert "3/104" in text, (
        "the rendered all-zero report never states the rule-of-three ceiling as `3/n`. A zero "
        "published without its ceiling states a certainty 104 questions do not support"
    )
    assert extraction.persistence.WILSON_LABEL in text, (
        "the Wilson bound is published without the label naming it as the INDEPENDENCE-ASSUMING "
        "width — the assumption the whole clustering discussion in this phase exists to price"
    )
    assert "(fact-level, n = 8)" in text, (
        "a zero was published with only the flattering question-level denominator. Both ends of "
        "the clustering assumption travel together or not at all (CLUSTER_DENOMINATOR_RATIONALE)"
    )
    assert (tmp_path / "phase18_extraction_report.md").read_text(encoding="utf-8") == text, (
        "render_report returned text it did not write, so the scan above checked a string the "
        "artifact does not carry"
    )


def test_render_path_never_reaches_the_fact_set():
    """D-11 — no function reachable from ``render_report`` imports a fact-set module.

    D-11 records ``slot`` on every corpus entry, draw record and exposure record for exactly one
    consequence: the report renderer never needs a fact VALUE, so it never imports one. Read off
    the AST as a transitive closure over the driver's own call graph, because the property is about
    what the render path CAN reach and not about what today's body happens to call.

    The two modules are named rather than globbed. They are the only two that hold locked values at
    module scope, which is why the driver's LAZY-IMPORT RULE exists for them specifically.
    """
    extraction_tree = ast.parse(_EXTRACTION_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in ast.walk(extraction_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "render_report" in functions, "render_report is gone — this guard would check nothing"

    seen, frontier, imports = set(), ["render_report"], {}
    while frontier:
        name = frontier.pop()
        if name in seen or name not in functions:
            continue
        seen.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                frontier.append(node.func.id)
            elif isinstance(node, ast.Import):
                imports.setdefault(name, []).extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.setdefault(name, []).append(node.module)

    assert len(seen) > 1, f"the closure over render_report found only {seen} — the walk broke"
    forbidden = {"phase14_factset", "phase17_persona_facts"}
    offenders = {name: sorted(forbidden.intersection(modules)) for name, modules in imports.items()}
    offenders = {name: hit for name, hit in offenders.items() if hit}
    assert offenders == {}, (
        f"functions reachable from render_report import fact-set modules: {offenders}. D-11's "
        "whole point is that the renderer works off `slot` alone, so no fact value can enter the "
        "render path — an import here would put every locked value one attribute access away from "
        "a paragraph in the published report"
    )


def test_addendum_append_is_additive(tmp_path):
    """S-6 — a recorded verdict cannot be overwritten, and a continuation is provably ADDITIVE.

    Three properties on a synthetic report, and all three are checked on the PRODUCED BYTES rather
    than inferred from the construction that made them:

      1. the prefix above the placeholder survives byte-for-byte, so nothing published above the
         continuation can be silently reworded under cover of an append;
      2. the recorded ``## Verdict`` section is unchanged — an addendum may be added BESIDE the
         verdict and never on top of it;
      3. the placeholder must occur exactly once. Zero and two are both refusals, because at zero
         this is not the file the writer was committed against and at two the writer would be
         GUESSING which line to replace, which is how an append becomes a rewrite.

    The clobber refusal is exercised in the same node, because the two are one mechanism: the
    refusal is what makes appending the only way forward, and a report carrying PENDING is the one
    state a re-render is still legitimate in.
    """
    extraction = _load()
    path = tmp_path / "phase18_extraction_report.md"

    prefix = "# Synthetic report\n\nA published paragraph that must survive byte-for-byte.\n\n"
    recorded = "## Verdict\n\nGO — recorded by a human on 2026-08-16.\n\n"
    tail = f"## Ship Decision\n\n{extraction.EXTRACTION_SHIP_PENDING_LINE}\n"
    path.write_text(prefix + recorded + tail, encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    updated = extraction.append_addendum(path, "## Addendum — 2026-08-16\n\nA dated continuation.")

    assert updated.startswith(prefix), (
        "the append did not carry the published prefix through byte-identically — everything above "
        "the placeholder is shipped text and an append may not touch it"
    )
    assert extraction._verdict.recorded_verdict(updated) == extraction._verdict.recorded_verdict(
        before
    ), "the append moved the recorded verdict, which is a rewrite wearing an append's name"
    assert "A dated continuation." in updated, "the addendum itself was lost"
    assert extraction.EXTRACTION_SHIP_PENDING_LINE not in updated, (
        "the placeholder survived the append, so the report still advertises a ship decision as "
        "unrecorded while carrying the dated section that records it"
    )
    assert extraction.EXTRACTION_SHIP_RECORDED_LINE in updated, "the pointer line was not written"
    assert path.read_text(encoding="utf-8") == updated, (
        "append_addendum returned bytes it did not write"
    )

    # Zero placeholders — the file has already been appended to, so there is no unambiguous line.
    with pytest.raises(SystemExit):
        extraction.append_addendum(path, "a second continuation")

    # Two placeholders — the writer would have to CHOOSE, and choosing is the failure mode.
    duplicated = tmp_path / "duplicated.md"
    duplicated.write_text(
        prefix + recorded + tail + f"\n{extraction.EXTRACTION_SHIP_PENDING_LINE}\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        extraction.append_addendum(duplicated, "ambiguous")

    # THE CLOBBER REFUSAL, both directions. A recorded non-PENDING verdict refuses; a PENDING one
    # renders normally, which is what keeps an interrupted run re-drivable without a force flag.
    with pytest.raises(SystemExit):
        extraction.assert_extraction_report_not_clobbered(path)

    pending = tmp_path / "pending.md"
    pending.write_text(
        f"{prefix}## Verdict\n\nPENDING — no ship decision recorded.\n\n{tail}", encoding="utf-8"
    )
    extraction.assert_extraction_report_not_clobbered(pending)  # returns, does not raise

    # A file with no `## Verdict` section at all is NOT this writer's output and is also refused —
    # `None` and an unrecorded body are deliberately different cases in `_verdict.recorded_verdict`.
    foreign = tmp_path / "foreign.md"
    foreign.write_text("# Somebody else's file\n\nPENDING appears here, in prose.\n", "utf-8")
    with pytest.raises(SystemExit):
        extraction.assert_extraction_report_not_clobbered(foreign)

    # And the refusal is reached through the RENDER path, not only when called directly: a
    # recorded verdict on disk stops render_report before it builds a single block.
    with pytest.raises(SystemExit):
        _render_zero_report(extraction, path)

    # The same fixture renders into a PENDING report without complaint, so the guard refuses
    # recorded evidence rather than refusing to run.
    assert _render_zero_report(extraction, pending), "a PENDING report did not re-render"

    source = _EXTRACTION_PATH.read_text(encoding="utf-8")
    assert not re.search(r"--force|force\s*=|force_|_force\b", source), (
        "an override flag appeared on the clobber refusal. A flag that disables this guard becomes "
        "routine, and an operator who passes it routinely passes it after a human HAS recorded a "
        "verdict — at which point it destroys the evidence it exists to protect"
    )


def _synthetic_arm_record(extraction, factset, arm, *, pid):
    """One arm record in exactly the shape ``run_arm`` writes, over a MINIATURE corpus.

    Two questions per fact per tier rather than the run's 27, because what is under test here is
    the GLUE — the pairing proofs, the 144-cell grid, the aggregation and the render — and none of
    those reads the corpus size. Family zero is the exception and is full-size: it carries all 112
    committed taught rows with their recorded ``k``, because ``family_zero_matches`` compares
    against the real report row for row and ABORTS on a control that covers a different set.
    """
    values = {fact.id: fact.value for fact in factset.LOCKED_FACTS}
    slots = {fact.id: fact.slot for fact in factset.LOCKED_FACTS}
    miss = "nothing of the sort was said here."

    draws = []
    for family in extraction.ATTACK_FAMILIES:
        for tier in extraction.CORPUS_TIERS:
            for fact in factset.LOCKED_FACTS:
                for seed_index in range(2):
                    draws.append(
                        {
                            "family": family,
                            "dose": family.split("-", 1)[1] if family.startswith("A1-") else None,
                            "fact_id": fact.id,
                            "slot": fact.slot,
                            "tier": tier,
                            "arm": arm,
                            "seed_index": seed_index,
                            "prefix_text": "zz" if family == "A2" else None,
                            "completions": [miss] * extraction.K,
                            "stopped": [True] * extraction.K,
                            "source_family": "F1",
                            "realized_injection": (
                                extraction.INJECTION_BUDGET_DECLARED[
                                    extraction.CORE_SLOTS.index(fact.slot)
                                ]
                                if family == "A2"
                                else None
                            ),
                        }
                    )
    for row in extraction.parse_phase14_taught_rows():
        # `k` hits out of `n`, so the positive control reproduces the committed vector exactly.
        completions = [values[row["fact_id"]]] * row["k"] + [miss] * (row["n"] - row["k"])
        draws.append(
            {
                "family": extraction.FAMILY_ZERO,
                "dose": None,
                "fact_id": row["fact_id"],
                "slot": slots[row["fact_id"]],
                "tier": extraction.REPORTED_TIER,
                "arm": arm,
                "seed_index": row["seed_index"],
                "prefix_text": None,
                "completions": completions,
                "stopped": [True] * row["n"],
                "source_family": None,
                "realized_injection": None,
            }
        )

    attack_prompts = len(extraction.ATTACK_FAMILIES) * len(extraction.CORPUS_TIERS) * 8 * 2
    return {
        "arm": arm,
        "config": {
            "corpus_sha256": "c" * 64,
            "corpus_entries": attack_prompts,
            "k": extraction.K,
            "forbid_ids_sha256": "f" * 64,
            "adapter_enabled": arm == extraction.ARMS[0],
            "git_sha": "deadbee",
            "pid": pid,
            "device": "cpu",
            "wall_clock_min": 492.0,
        },
        "draw_record_keys": list(extraction.DRAW_RECORD_KEYS),
        "draws": draws,
        "exposure": [
            {
                "slot": slot,
                "admissible": (
                    extraction.ADMISSIBLE_NLL_FRAME,
                    extraction.ADMISSIBLE_NLL_REDUCTION,
                ),
                "nll": {
                    frame: {reduction: 1.5 for reduction in extraction.NLL_REDUCTIONS}
                    for frame in extraction.NLL_FRAMES
                },
                "rank": 1,
                "exposure_bits": 3.0,
                "ceiling_bits": 3.0,
                "n_references": 8,
                "length_spread": 0 if slot in extraction.SPREAD_ZERO_CONTROL_SLOTS else 3,
                "spread_zero_control": slot in extraction.SPREAD_ZERO_CONTROL_SLOTS,
                "descriptive_label": extraction.EXPOSURE_DESCRIPTIVE_LABEL,
                "threats_to_validity": extraction.EXPOSURE_THREATS_TO_VALIDITY,
            }
            for slot in extraction.CORE_SLOTS
        ],
    }


def test_run_report_pairs_two_arms_and_renders(tmp_path):
    """The `--report` mode function, driven END TO END on synthetic arm records.

    ``run_report`` is the glue plan 18-10 named and deliberately did not define, and it fires for
    the first time AFTER two 8.2-hour runs. An unexercised function at that position is the exact
    failure mode the D-12 pre-flight buys out for the generation path, so it is bought out here for
    the report path: two records on disk, the whole pipeline, a rendered file.

    The pairing proofs are then falsified one at a time. A pipeline that ran is not evidence that
    its refusals work, and every one of these is a way two records can look paired while measuring
    different things — a swapped file, a shared process, a rebuilt corpus between the two arms.
    """
    extraction = _load()
    # The fact set is loaded HERE, in the test, and never by anything the renderer can reach — the
    # fixture needs the taught strings to build a control that reproduces, which is the same reason
    # `score_records` takes its values as a parameter.
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    factset = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factset)

    paths = {arm: tmp_path / f"phase18_arm_{arm}.json" for arm in extraction.ARMS}
    records = {
        arm: _synthetic_arm_record(extraction, factset, arm, pid=4242 + index)
        for index, arm in enumerate(extraction.ARMS)
    }
    for arm, path in paths.items():
        path.write_text(json.dumps(records[arm]), encoding="utf-8")

    report = tmp_path / "phase18_extraction_report.md"
    text = extraction.run_report(record_paths=paths, path=report)

    assert report.read_text(encoding="utf-8") == text
    assert re.search(r"\b0(\.0+)?%", text) is None, "run_report rendered a bare zero percentage"
    assert extraction._verdict.recorded_verdict(text) is not None
    # The positive control reproduced, so the gate is reached and licenses a verdict rather than
    # short-circuiting — which is what makes the Holm rows and the conclusion reachable at all.
    assert "0 per-question mismatches" in text, text[:400]
    licensed_null = extraction.VERDICTS[1]
    assert licensed_null in text, (
        f"an all-zero attack behind a control that reproduced exactly is {licensed_null!r} — a "
        "null the gate has LICENSED. Any other verdict here means the pipeline reached the gate "
        "with inputs it did not build"
    )
    assert "## Conclusion" in text and extraction.LOWER_BOUND_SENTENCE in text

    # Re-running now refuses: the report carries a recorded, non-PENDING verdict.
    with pytest.raises(SystemExit):
        extraction.run_report(record_paths=paths, path=report)

    # A swapped pair. Each file still holds a well-formed record; only the filing is wrong, which
    # is precisely the case a glob-and-score reader cannot see.
    swapped = {arm: tmp_path / f"swapped_{arm}.json" for arm in extraction.ARMS}
    swapped[extraction.ARMS[0]].write_text(json.dumps(records[extraction.ARMS[1]]), "utf-8")
    swapped[extraction.ARMS[1]].write_text(json.dumps(records[extraction.ARMS[0]]), "utf-8")
    with pytest.raises(SystemExit):
        extraction.run_report(record_paths=swapped, path=tmp_path / "swapped.md")

    for field, value in (("pid", 4242), ("corpus_sha256", "d" * 64), ("k", 16)):
        broken = tmp_path / f"broken_{field}.json"
        record = json.loads(json.dumps(records[extraction.ARMS[1]]))
        record["config"][field] = value
        broken.write_text(json.dumps(record), encoding="utf-8")
        mixed = dict(paths)
        mixed[extraction.ARMS[1]] = broken
        with pytest.raises(SystemExit):
            extraction.run_report(record_paths=mixed, path=tmp_path / f"broken_{field}.md")

    # And a missing record names the command that produces it rather than raising a FileNotFound.
    with pytest.raises(SystemExit):
        extraction.run_report(
            record_paths={arm: tmp_path / "absent.json" for arm in extraction.ARMS},
            path=tmp_path / "absent.md",
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
