"""Additivity of the Phase 19 CALIBRATION-RATE correction, proved on the artifact PUBLISHED.

``tests/test_phase19_docs.py`` proves ``scripts/_addendum.py`` appends — at a synthetic tmp
location, against bytes the test itself wrote. This proves what that writer actually DID to
``results/phase19_calibration_correction.md``, which is a different claim: a writer can be
append-only and still have been run against a file some other hand had already rewritten. The twin
of ``tests/test_phase17_stats.py::test_report_addendum_is_additive``, over this phase's own
continuation, and the pre-append revision is DERIVED from history rather than pinned to a hash.

**Why a continuation and not a fix.** Three defects in ``scripts/phase19_erasure.py`` were measured
on the blind calibration run at 19-09 (A: an order-sensitive key comparison that masks a SUCCESS as
INCONCLUSIVE; B: ``_calibration_rate`` reading Phase 18's candidate rows instead of the calibration
arm's own; C: a ``fact_id``-keyed ``per_fact`` block that drops a tier). None can be repaired in
place: STAT-05's guard requires every commit touching the pin to be an ancestor of every committed
``results/phase19_*`` first-add, and eight such artifacts now exist, so an edit reddens
``tests/test_phase16_prereg.py`` permanently. Delete-and-re-add does not launder it either — the
guard takes ``adds[-1]``, the EARLIEST add (``tests/test_phase16_prereg.py:117-124``). The guard's
own docstring names the sanctioned path: "the correction path for a defect found later is a DATED
CONTINUATION beside the published text (``scripts/_addendum.py``, D3), never an edit"
(``:342-346``).

**What is at stake in the number.** Defect B makes the pin's internal report price the (a) floor at
``0.2`` — the ``ceiling`` branch, from Phase 18's 92/104 candidate recall — when the blind
calibration this phase actually ran measured ``0/23`` and prices it at ``0.09107873950450847``, the
``reachability-min`` branch. Those are not close: 0.2 clears on a mediocre erasure, 0.091 clears
only on a near-perfect one. The corrected floor is what the formal erasure verdict is read against,
so it is asserted here against a re-derivation from the committed draws rather than left in prose
for 19-11 and 19-15 to find.
"""

import importlib.util
import json
import pathlib
import re
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

CORRECTION_REL = "results/phase19_calibration_correction.md"
PAYLOAD_REL = "results/phase19_calibration_correction.json"
CORRECTION_PATH = _ROOT / CORRECTION_REL
PAYLOAD_PATH = _ROOT / PAYLOAD_REL
ARM_RECORD_REL = "results/phase19_arm_cal-erased.json"

# The Phase 19 calibration marker PAIR. Both halves travel to the writer together — that pairing is
# why `scripts/_addendum.py` exists at all, and defining them here is `test_phase19_docs.py`'s own
# register: the committed test module is the pair's source of truth, not the driver that ran once.
CAL_PENDING = "**Phase 19 calibration-rate correction: not yet recorded.**"
CAL_RECORDED = (
    "**Phase 19 calibration-rate correction: recorded in the dated continuation at the end of "
    "this file.**"
)
CAL_ADDENDUM_HEADING = (
    "## Addendum — 2026-08-18 — the calibration rate, the floor, and three pin defects"
)

# The corrected floor, NEVER typed as a literal here: re-derived below from the committed arm
# record's own draws through the pin's own instruments. A hand-typed constant is the second copy
# free to disagree that this phase has refused twice (19-07's (c) scalar, 19-08's rule text).
FAMILY = "A2"
TIERS = ("core_taught", "core_held_out")


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, _ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(*args):
    done = subprocess.run(("git", *args), cwd=_ROOT, capture_output=True, check=True)
    return done.stdout.decode("utf-8")


def _measured_calibration_rate():
    """The pooled ``(successes, questions)`` re-derived from the COMMITTED draws, per tier.

    Through ``phase19_erasure.per_fact_rows`` — the pin's own conversion, the one whose duplication
    of ``target_rows_from_arm_record`` is already self-checked by a committed test — driven ONCE
    PER TIER. Driving it once per tier is the whole of defect C: ``run_erasure_arm`` merges the two
    calls with ``rows.update(...)`` into a ``fact_id``-keyed dict, and both tiers carry the same
    ``fact_id``, so ``core_taught`` (14) silently overwrites ``core_held_out`` (9).
    """
    import phase19_erasure as pin

    record = json.loads((_ROOT / ARM_RECORD_REL).read_text(encoding="utf-8"))
    fact = pin.select_calibration_fact()
    values = {fact.id: fact.value}
    successes = questions = 0
    per_tier = {}
    for tier in TIERS:
        rows = pin.per_fact_rows(record["draws"], values, family=FAMILY, tier=tier)
        row = rows[fact.id]
        per_tier[tier] = row
        successes += row["n_answerable"]
        questions += row["n_questions"]
    return successes, questions, per_tier


def test_correction_addendum_is_additive_on_the_published_artifact():
    """The continuation was ADDED beside the published verdict, never over it.

    Every assertion runs on the committed bytes rather than on a writer's return value, because the
    claim is about what happened to a published file and not about what a function does in the
    abstract.
    """
    add = _load("_addendum", "scripts/_addendum.py")

    assert CORRECTION_PATH.exists(), f"{CORRECTION_REL} is missing — plan 19-09 committed it"
    assert _git("rev-parse", "--is-shallow-repository").strip() == "false", (
        "shallow clone: the pre-append revision is not in the object store, so this guard cannot "
        "distinguish 'the append was additive' from 'the history was never read'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )

    # The newest committed revision still carrying the placeholder is BY DEFINITION the one before
    # the append, and that stays true however many later commits touch the file.
    before = None
    for revision in _git("log", "--format=%H", "--", CORRECTION_REL).split():  # newest first
        blob = _git("show", f"{revision}:{CORRECTION_REL}")
        if CAL_PENDING in blob:
            before = blob
            break
    assert before is not None, (
        f"no committed revision of {CORRECTION_REL} carries {CAL_PENDING!r}, so there is no "
        "pre-append state to compare against. Either the placeholder never existed (the file is "
        "not this writer's output) or the history was rewritten"
    )
    after = CORRECTION_PATH.read_text(encoding="utf-8")

    cut = before.index(CAL_PENDING)
    assert after[:cut] == before[:cut], (
        f"the published {CORRECTION_REL} no longer starts with its pre-append bytes. Everything "
        "above the placeholder is recorded evidence — the measured 0/23 with its two bounds and "
        "the verdict the CLOSED pin computes — and an append may not touch any of it"
    )

    before_lines, after_lines = before.splitlines(), after.splitlines()
    changed = [(old, new) for old, new in zip(before_lines, after_lines) if old != new]
    assert changed == [(CAL_PENDING, CAL_RECORDED)], (
        f"exactly one published line may differ, and it is the placeholder becoming a pointer at "
        f"the appended section: {changed}"
    )
    assert after_lines[: len(before_lines)] == [
        CAL_RECORDED if line == CAL_PENDING else line for line in before_lines
    ], "a published line was moved, deleted or reordered rather than left in place"
    assert len(after_lines) > len(before_lines), "nothing was appended"
    assert CAL_ADDENDUM_HEADING in "\n".join(after_lines[len(before_lines) :]), (
        "the addendum heading is not in the appended region, so the section was spliced into the "
        "body rather than added after it"
    )

    assert add._verdict.recorded_verdict(after) == add._verdict.recorded_verdict(before), (
        "the recorded `## Verdict` section changed across the append. It is the section the "
        "clobber guards anchor on and the one thing a continuation exists to sit BESIDE"
    )

    # The regression `scripts/_addendum.py` was written for: no OTHER phase's marker may appear.
    extraction = _load("p18", "scripts/phase18_extraction.py")
    assert extraction.EXTRACTION_SHIP_RECORDED_LINE not in after, (
        "a Phase 18 ship-decision line reached a Phase 19 continuation — the exact defect "
        "scripts/_addendum.py exists to prevent"
    )

    # STAT-02: a bare zero percentage states a certainty 23 questions cannot support.
    zero = re.search(r"\b0(\.0+)?%", after)
    assert zero is None, (
        f"{CORRECTION_REL} publishes a bare zero percentage at offset {zero.start()}: "
        f"{after[max(0, zero.start() - 60) : zero.end() + 20]!r}"
    )


def test_corrected_floor_re_derives_from_the_committed_arm_record():
    """The published floor is the pin's own arithmetic on the pin's own draws — 0/23, not 92/104.

    Both numbers are asserted PRESENT. Publishing only the corrected one would leave a reader
    unable to tell a correction from a preference, and the pin's internal 0.2 is what
    ``_cmd_report`` still prints — so it has to be nameable, and named as superseded.
    """
    import phase19_erasure as pin

    assert PAYLOAD_PATH.exists(), f"{PAYLOAD_REL} is missing — the machine-readable half"
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))

    successes, questions, per_tier = _measured_calibration_rate()
    assert (successes, questions) == (
        payload["calibration_successes"],
        payload["calibration_questions"],
    ), (
        f"the payload publishes {payload['calibration_successes']}/"
        f"{payload['calibration_questions']} but the committed draws re-derive to "
        f"{successes}/{questions}"
    )

    corpus = json.loads(
        (_ROOT / "results" / "phase19_calibration_corpus.json").read_text(encoding="utf-8")
    )
    assert questions == corpus["n_questions"], (
        f"the pooled denominator is {questions} but the corpus every draw was built from declares "
        f"{corpus['n_questions']}. CALIBRATION_COMMENSURABILITY clause 3 requires the published "
        "denominator to be the corpus's own — this is defect C, and the re-derivation is what "
        "recovers it from the fact_id-keyed block that dropped a tier"
    )
    for tier in TIERS:
        assert per_tier[tier]["n_questions"] == corpus["question_counts"][tier], (
            f"the {tier} denominator re-derives to {per_tier[tier]['n_questions']} against the "
            f"corpus's {corpus['question_counts'][tier]}"
        )

    rate = successes / questions
    expected = pin.lock_erasure_floor(rate)
    assert payload["corrected_target_floor"] == expected, (
        f"the payload publishes a corrected floor of {payload['corrected_target_floor']!r} but "
        f"lock_erasure_floor({rate!r}) — the pin's own committed rule on the pin's own committed "
        f"draws — returns {expected!r}. A hand-edited constant goes red here"
    )
    assert payload["corrected_floor_branch"] == pin.floor_branch(rate)
    assert payload["corrected_target_floor"] == pin.ERASURE_FLOOR_MIN, (
        "the corrected floor is no longer the reachability clamp, so condition (a)'s difficulty "
        "changed without this test noticing"
    )

    # The number the CLOSED pin still computes internally — defect B, asserted live so that a
    # future reader cannot mistake the correction for a preference.
    internal_rate = pin._calibration_rate()
    assert payload["pin_internal_calibration_rate"] == internal_rate, (
        f"the pin's _calibration_rate() now returns {internal_rate!r}, not the "
        f"{payload['pin_internal_calibration_rate']!r} this correction was written against. If it "
        "returns the measured rate, defect B is gone and this continuation needs re-reading"
    )
    assert payload["pin_internal_target_floor"] == pin.lock_erasure_floor(internal_rate)
    assert payload["pin_internal_target_floor"] != payload["corrected_target_floor"], (
        "the two floors agree, so there is nothing to correct and this artifact is misleading"
    )

    # WHICH ONE GOVERNS — stated as a field, not inferred from ordering.
    assert payload["governs"] == "corrected_target_floor", (
        "the payload does not name the corrected floor as the governing one. 19-11 locks a "
        "constant and 19-15 renders a verdict off it; leaving which-number-wins implicit is the "
        "one thing this artifact exists to prevent"
    )

    # The prose half must name BOTH numbers and say which governs, in words.
    text = CORRECTION_PATH.read_text(encoding="utf-8")
    for number in (
        repr(payload["corrected_target_floor"]),
        repr(payload["pin_internal_target_floor"]),
    ):
        assert number in text, (
            f"{CORRECTION_REL} does not print {number} — both floors must be named in the prose, "
            "or a reader meets one number and never learns the other exists"
        )
    assert "governs" in text.lower(), (
        f"{CORRECTION_REL} never says which floor governs the verdict. Implicit is not enough — "
        "the whole defect being corrected is a reader taking the wrong number in good faith"
    )


def test_defects_a_b_and_c_are_all_still_live_and_all_published():
    """Each defect asserted against the CODE, not against the prose that describes it.

    A description that outlives its defect is worse than no description: it teaches a reader to
    distrust an artifact that is now correct. If any of these goes green, this continuation needs
    re-reading rather than deleting.
    """
    import phase18_extraction as extraction
    import phase19_erasure as pin

    record = json.loads((_ROOT / ARM_RECORD_REL).read_text(encoding="utf-8"))
    text = CORRECTION_PATH.read_text(encoding="utf-8")

    # A — order-sensitive comparison. Same key SET, different ORDER, every NLL finite.
    assert pin.zero_results_have_nll(record) is False, (
        "defect A is gone: the committed record now passes zero_results_have_nll. The published "
        "continuation says it does not"
    )
    gaps = pin.zero_result_exposure_gaps(record)
    assert gaps, "no gaps, yet the flag is False — the diagnosis in the continuation is wrong"
    for entry in list(record["exposure"]) + list(record["pre_erasure"]["exposure"]):
        if entry["slot"] != "person_name":
            continue
        assert set(entry) == set(extraction.EXPOSURE_RECORD_KEYS), (
            "the exposure block is missing a committed key — then the defect is a genuine gap and "
            "not the ordering one this continuation documents"
        )
        assert tuple(entry) != extraction.EXPOSURE_RECORD_KEYS, "the key order now matches"
        for frame in extraction.NLL_FRAMES:
            for reduction in extraction.NLL_REDUCTIONS:
                value = entry["nll"][frame][reduction]
                assert value == value and abs(value) != float("inf"), (
                    f"{frame}/{reduction} is {value!r} — not finite, so the record has a real gap "
                    "and the 'ordering only' claim in the continuation is false"
                )
    assert "sort_keys" in text and "order" in text.lower(), (
        "the continuation does not publish defect A's mechanism"
    )

    # B — the rate read from Phase 18's candidate rows.
    rows = record["pre_erasure"]["per_fact"]
    assert all(fact_id.startswith("cand_") for fact_id in rows), (
        "pre_erasure.per_fact no longer holds Phase 18's candidate rows, so defect B's mechanism "
        "has changed"
    )
    assert pin._calibration_rate() == sum(r["n_answerable"] for r in rows.values()) / sum(
        r["n_questions"] for r in rows.values()
    ), "_calibration_rate no longer reads the pre_erasure block this continuation names"
    assert "_calibration_rate" in text, "the continuation does not name defect B's function"

    # C — the fact_id-keyed per_fact block that drops a tier.
    published = sum(row["n_questions"] for row in record["per_fact"].values())
    _successes, questions, _per_tier = _measured_calibration_rate()
    assert published < questions, (
        f"the record's per_fact block publishes {published} questions and the re-derivation gives "
        f"{questions} — if these agree, defect C is gone"
    )
    assert "per_fact" in text and str(questions) in text and str(published) in text, (
        "the continuation does not publish both denominators for defect C"
    )


def test_a_locked_floor_must_be_the_corrected_one():
    """The tripwire for 19-11. Arms itself the moment ``scripts/phase19_floor.py`` is written.

    The recorded-state discipline of ``tests/test_phase16_prereg.py``'s
    ``bool(checked) == bool(tracked)``: green while the floor file does not exist, and RED from its
    first line onward if the constant it locks is the pin's internal 0.2 rather than the corrected
    floor. A note in a SUMMARY is something a later plan can miss; a red test is not.
    """
    import phase19_erasure as pin

    floor_file = _ROOT / "scripts" / "phase19_floor.py"
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    corrected = payload["corrected_target_floor"]

    if not floor_file.exists():
        # RECORDED STATE, not a silent skip: 19-11 has not run. The assertion below is what stops
        # this branch surviving its arrival.
        assert not _git("ls-files", "scripts/phase19_floor.py").strip(), (
            "scripts/phase19_floor.py is tracked but absent from the working tree"
        )
        return

    namespace = {}
    exec(compile(floor_file.read_text(encoding="utf-8"), str(floor_file), "exec"), namespace)
    assert "TARGET_FLOOR" in namespace, "scripts/phase19_floor.py defines no TARGET_FLOOR"
    assert namespace["TARGET_FLOOR"] == corrected, (
        f"scripts/phase19_floor.py locks TARGET_FLOOR = {namespace['TARGET_FLOOR']!r}, but the "
        f"blind calibration this phase ran measured {payload['calibration_successes']}/"
        f"{payload['calibration_questions']} and prices the (a) floor at {corrected!r} "
        f"({payload['corrected_floor_branch']}). {payload['pin_internal_target_floor']!r} is what "
        "the pin's own report computes from Phase 18's candidate rows — defect B — and it is NOT "
        f"the floor the verdict is read against. See {CORRECTION_REL}"
    )
    assert namespace["TARGET_FLOOR"] == pin.ERASURE_FLOOR_MIN
