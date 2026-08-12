"""Phase 16 recall fixture — the drift guards ``results/phase16_recall_sample.json`` needs.

CPU-only, GPU/MPS-free, no checkpoint I/O, no model load, no generation. Pins:
  1. ``test_fixture_matches_the_generator`` — the committed fixture still equals what
     ``build_question_sets`` produces, question text and ``seed_index``, in order. This is the
     guard the fixture exists without otherwise: a static JSON diverges SILENTLY the moment
     ``render_family`` or the family-id sets change, and the divergence would surface only as
     Phase 16/17/18 numbers that no longer compare to Phase 14's.
  2. ``test_fixture_matches_the_committed_transcripts`` — regeneration equals the questions
     recorded in ``results/phase14_transcripts.md``. ``test_phase14_scoring.py`` compares
     ``build_question_sets`` against ``fs.heldout_questions()`` — code against code, both from the
     same module — so nothing else pins either construction against the committed ARTIFACT.
  3. ``test_fixture_provenance_still_describes_the_transcripts`` — the recorded sha256/byte count
     still describe the file on disk, so the fixture's "verified reproduction" claim cannot rot.
  4. ``test_fixture_counts_and_clean_room`` — 112/104/54 = 270, all unique, and no question names
     ANY fact's value (the clean-room property, checked on the committed artifact rather than
     only on the generator's output).
  5. ``test_fixture_carries_the_binding_cross_phase_decision`` — the v3.0 constraint that Phases
     17 and 18 consume THIS fixture is committed inside the artifact; deleting it goes red.

Scripts-load justification: identical to ``tests/test_phase14_scoring.py`` — the question-set
construction MUST stay in the committed driver for git history to be the pre-registration proof,
so the driver is loaded with ``importlib.util.spec_from_file_location``. ``main()`` is
``__main__``-guarded and ``build_question_sets`` is a pure function, so the load runs no guard,
no model load, and no generation.
"""

import hashlib
import importlib.util
import json
import pathlib
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

FIXTURE = _REPO_ROOT / "results" / "phase16_recall_sample.json"
TRANSCRIPTS = _REPO_ROOT / "results" / "phase14_transcripts.md"

_SECTION_RE = re.compile(r"^## (.+)$")
_QUESTION_RE = re.compile(r"^### \[(\d+)\] (.*)$")

CORE_TAUGHT = "core taught"
CORE_HELD = "core held-out"
CONTROL = "closed-book control (adapter off)"
SOFT = "soft tier (excluded from the pre-registered gate)"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pr = _load("phase14_recall")
fs = _load("phase14_factset")


def _regenerate():
    """``(core_taught, core_held_out, soft)`` seed-stamped exactly as the run stamped them."""
    core_taught, core_held_out, _ = pr.build_question_sets(fs.LOCKED_FACTS)
    soft_taught, soft_held_out, _ = pr.build_question_sets(fs.SOFT_TIER_FACTS)
    return (
        pr.stamp_seed_indices(core_taught),
        pr.stamp_seed_indices(core_held_out),
        pr.stamp_seed_indices(soft_taught + soft_held_out),
    )


def _fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _recorded_sections():
    """``{section: [(seed_index, question), ...]}`` in file order."""
    sections, current = {}, None
    for line in TRANSCRIPTS.read_text(encoding="utf-8").splitlines():
        section = _SECTION_RE.match(line)
        if section:
            current = section.group(1).strip()
            sections.setdefault(current, [])
            continue
        question = _QUESTION_RE.match(line)
        if question and current is not None:
            sections[current].append((int(question.group(1)), question.group(2).strip()))
    return sections


def test_fixture_matches_the_generator():
    """The committed JSON is still what the committed code produces — text AND seed_index."""
    core_taught, core_held_out, soft = _regenerate()
    questions = _fixture()["questions"]
    for key, regenerated in (
        ("core_taught", core_taught),
        ("core_held_out", core_held_out),
        ("soft", soft),
    ):
        stored = questions[key]
        assert [e["question"] for e in stored] == [i.question for i in regenerated], (
            f"{key}: fixture question text has drifted from build_question_sets — the fixture is "
            "stale, or render_family/the family-id sets changed under it"
        )
        assert [e["seed_index"] for e in stored] == [i.seed_index for i in regenerated], (
            f"{key}: seed_index drift — the arms would no longer be paired with Phase 14"
        )
        assert [e["fact_id"] for e in stored] == [i.fact.id for i in regenerated]
        assert [e["reserved"] for e in stored] == [bool(i.reserved) for i in regenerated]


def test_fixture_matches_the_committed_transcripts():
    """Regeneration equals the questions recorded in the Phase 14 run artifact, in order."""
    core_taught, core_held_out, soft = _regenerate()
    sections = _recorded_sections()
    for key, regenerated in (
        (CORE_TAUGHT, core_taught),
        (CORE_HELD, core_held_out),
        (SOFT, soft),
    ):
        assert [q for _, q in sections[key]] == [i.question for i in regenerated], f"{key} text"
        assert [i for i, _ in sections[key]] == [i.seed_index for i in regenerated], f"{key} index"

    control = [i.question for i in core_taught + core_held_out + soft]
    assert [q for _, q in sections[CONTROL]] == control, (
        "the closed-book control is the concatenation of the three adapter-ON arms in order — "
        "a mismatch means the control is no longer scored on the same questions"
    )


def test_fixture_provenance_still_describes_the_transcripts():
    """The fixture's 'verified reproduction' claim is only true while these still match."""
    provenance = _fixture()["provenance"]
    assert provenance["transcripts_bytes"] == TRANSCRIPTS.stat().st_size
    assert provenance["transcripts_sha256"] == hashlib.sha256(TRANSCRIPTS.read_bytes()).hexdigest()
    assert provenance["core_facts"] == [f.id for f in fs.LOCKED_FACTS]
    assert provenance["soft_facts"] == [f.id for f in fs.SOFT_TIER_FACTS]
    assert provenance["taught_family_ids"] == sorted(fs.TAUGHT_FAMILY_IDS)
    assert provenance["heldout_family_ids"] == sorted(fs.HELDOUT_FAMILY_IDS)
    assert provenance["seed_constant"] == pr.SEED


def test_fixture_counts_and_clean_room():
    """112/104/54 = 270, every question distinct, and no question names ANY fact's value."""
    data = _fixture()
    questions = data["questions"]
    assert (len(questions["core_taught"]), len(questions["core_held_out"])) == (112, 104)
    assert len(questions["soft"]) == 54
    assert data["counts"] == {
        "core_taught": 112,
        "core_held_out": 104,
        "soft": 54,
        "total": 270,
        "per_core_fact": {"taught": 14, "held_out": 13},
    }

    every = questions["core_taught"] + questions["core_held_out"] + questions["soft"]
    assert len(every) == 270
    assert len({e["question"] for e in every}) == 270, "a duplicate question would double-weight"
    assert {e["fact_id"] for e in questions["core_taught"]} == {f.id for f in fs.LOCKED_FACTS}

    for key in ("core_taught", "core_held_out", "soft"):
        stored = questions[key]
        assert [e["seed_index"] for e in stored] == list(range(len(stored)))

    values = [f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]
    for entry in every:
        for value in values:
            assert not pr.contains_value(entry["question"], value), (
                f"question {entry['question']!r} names the fact value {value!r} — a scored "
                "question carrying its own answer measures copying from context, not memory"
            )


def test_fixture_carries_the_binding_cross_phase_decision():
    """Phases 17/18 must consume THIS fixture; the constraint lives in the committed artifact."""
    data = _fixture()
    binding = data["binding_decision"]
    assert "Phases 17 and 18" in binding
    assert "No third" in binding
    # The seed's role is stated separately so the enumeration is never read as seed-derived.
    assert "governs the DRAWS, not this enumeration" in data["seed_role"]
    assert "not a new sample" in data["note"]
