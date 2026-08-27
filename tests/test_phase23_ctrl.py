"""D-03's floor and D-08's never-taught scheduling, asserted against the COMMITTED records.

Four properties, each of which a hand-edited artifact breaks:

1. **The never-taught arm was trained ONCE.** ``consumers`` names its two consumers as a FIELD, and
   an AST scan of ``scripts/`` proves exactly one entry point exists that would train one. "Trained
   once, consumed twice" is checkable rather than claimed.
2. **The seed count satisfies the FROZEN Phase-25 gate BY CONSTRUCTION**, asserted against the
   IMPORTED ``mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS`` and ``NEVER_TAUGHT_ARM`` — never a
   retyped ``2`` and never a retyped ``"never-taught"``. A retyped constant is a constant free to
   drift from the one the gate actually checks two phases from now.
3. **The floor RE-DERIVES from its own recorded readings** under exact ``==``.
   ``scripts/phase19_floor.py``'s property 2, applied here: a number edited in the artifact is a
   number chosen with the artifact's own readings visible, and this test reddens on it.
4. **The corpus-digest refusal is WATCHED RED**, with two independent detectors — the behavioural
   one (drive ``prove_bins_match`` at a flipped hex character and observe the ``SystemExit``) and
   the call-site one (AST-prove production still calls it). ``tests/test_phase22_fakes.py``'s
   discipline: watching a helper redden proves nothing if production stopped calling it.

CPU-only, GPU-free, no torch, no network — every reading is read back off a committed record.
"""

import ast
import hashlib
import inspect
import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_gate  # noqa: E402  FROZEN — the constants below are READ from it, never retyped
import phase23_prereg  # noqa: E402
import phase23_run  # noqa: E402
from phase23_prereg import (  # noqa: E402
    CONTROL_FLOOR_RECORD,
    FLOOR_PROVENANCE_KEYS,
    NEVER_TAUGHT_TRAINING_RECORD,
    noise_floor,
)

# The two named consumers, in the record's own order. CTRL-03 says the never-taught arm is trained
# ONCE and consumed TWICE; the record has to say which two, or "twice" is a number with no referent.
_EXPECTED_CONSUMERS = ["frontier lower-left floor", "relearning reference"]


def _record(relative_path):
    path = _ROOT / relative_path
    assert path.exists(), (
        f"{relative_path} is missing. It is a COMMITTED artifact of plan 23-08 and every assertion "
        "in this file reads it back — a skipped test here would be a floor nobody re-derived"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_never_taught_is_trained_once():
    """CTRL-03: ONE scheduling, two named consumers, and exactly ONE training entry point."""
    record = _record(NEVER_TAUGHT_TRAINING_RECORD)
    assert record["consumers"] == _EXPECTED_CONSUMERS, (
        f"the never-taught record names consumers {record['consumers']!r}, not "
        f"{_EXPECTED_CONSUMERS!r}. 'Trained once, consumed twice' is a FIELD here precisely so the "
        "second half is checkable: a consumer list that does not name both is a claim again"
    )
    assert record["scored_here"] is False, (
        "the never-taught record declares it was scored in 23-08. The scoring budget is a function "
        "of the K that 23-13 selects and 23-14 scores these adapters at that K — scoring them here "
        "would make 'trained once, consumed twice' false at the first consumer"
    )

    # THE ENTRY-POINT CENSUS. `train_never_taught` is the ONLY function anywhere under `scripts/`
    # that trains a never-taught adapter, and a second one would make "trained once" false without
    # changing a single field of the record above.
    definitions, call_sites = [], []
    for path in sorted(pathlib.Path(_ROOT / "scripts").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "train_never_taught":
                definitions.append(f"{path.name}:{node.lineno}")
            called = getattr(node, "func", None)
            name = getattr(called, "id", None) or getattr(called, "attr", None)
            if isinstance(node, ast.Call) and name == "train_never_taught":
                call_sites.append(f"{path.name}:{node.lineno}")
    assert definitions == ["phase23_run.py:" + definitions[0].split(":")[1]], (
        f"`train_never_taught` is defined at {definitions} — CTRL-03's arm is trained ONCE, so "
        "exactly one definition may exist and it lives in the Phase-23 driver. A second definition "
        "is a second scheduling wearing the first one's record"
    )
    assert len(definitions) == 1 and len(call_sites) == 1, (
        f"`train_never_taught` has {len(definitions)} definition(s) at {definitions} and "
        f"{len(call_sites)} call site(s) at {call_sites}. CTRL-03's never-taught arm is trained "
        "ONCE — a second entry point would make the record's 'one scheduling' false while every "
        "field in it stayed correct"
    )


def test_never_taught_seed_count_satisfies_the_frozen_gate():
    """D-08: the FROZEN Phase-25 gate's requirements, satisfied BY CONSTRUCTION here.

    Both constants are IMPORTED from ``scripts/mitigation_gate.py``. Retyping ``2`` or
    ``"never-taught"`` would assert against a copy free to drift from the value
    ``extraction_ceiling`` actually ``_prove``s two phases from now.
    """
    record = _record(NEVER_TAUGHT_TRAINING_RECORD)
    assert record["arm"] == mitigation_gate.NEVER_TAUGHT_ARM, (
        f"the record names arm {record['arm']!r}, not {mitigation_gate.NEVER_TAUGHT_ARM!r}. "
        "`extraction_ceiling` `_prove`s that exact string and refuses one borrowing BY NAME"
    )
    distinct = len(set(record["seeds"]))
    assert distinct >= mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS, (
        f"the record reports seeds {record['seeds']!r} — {distinct} distinct value(s) against the "
        f"frozen {mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS}-seed protocol. A single-seed "
        "floor is NOT a noise floor, it is ONE DRAW, and Phase 25 refuses it"
    )
    assert distinct == len(record["seeds"]) == record["n_seeds"], (
        f"the record declares n_seeds={record['n_seeds']!r} over seeds {record['seeds']!r} with "
        f"{distinct} distinct value(s). A repeated seed is one draw wearing two names"
    )

    # The frozen gate's provenance keys, read from the gate — the record must carry each.
    for key in mitigation_gate.EXTRACTION_FLOOR_PROVENANCE_KEYS:
        assert key in record, (
            f"the never-taught record is missing {key!r}, which "
            f"`mitigation_gate.EXTRACTION_FLOOR_PROVENANCE_KEYS` requires. X is not computable "
            "from a floor whose arm and seeds are unstated"
        )

    # Every adapter exists locally and hashes to the digest recorded beside it.
    for entry in record["adapters"]:
        path = _ROOT / entry["path"]
        assert path.exists(), f"{entry['path']} is recorded in the artifact but absent on disk"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"], (
            f"{entry['path']} hashes to {digest} but the record says {entry['sha256']}. The "
            "adapter 23-14 will score is not the adapter this scheduling exported"
        )
        assert path.stat().st_size == entry["bytes"], (
            f"{entry['path']} is {path.stat().st_size} bytes, recorded as {entry['bytes']}"
        )


def test_the_control_floor_re_derives_from_its_recorded_readings():
    """D-03: ``floor == phase23_prereg.noise_floor(the recorded per-seed primary readings)``.

    Exact ``==``, so a HAND-EDITED number goes red — including a one-ULP nudge, which is the defect
    class Phase 20 closed at GATE-02. ``scripts/phase19_floor.py``'s property 2, applied to the
    floor a whole sweep halts on.
    """
    record = _record(CONTROL_FLOOR_RECORD)
    readings = [entry["primary"]["rate"] for entry in record["per_seed"]]
    assert record["readings"] == readings, (
        f"the record's `readings` block {record['readings']!r} disagrees with the per-seed primary "
        f"rates {readings!r} it is supposed to be a projection of"
    )
    assert record["floor"] == noise_floor(readings), (
        f"the recorded floor {record['floor']!r} does not re-derive from the recorded readings "
        f"{readings!r}: `phase23_prereg.noise_floor` returns {noise_floor(readings)!r}. The floor "
        "must be EXACTLY the blindly-committed reduction's output on the readings it is judged "
        "against, so a number edited in the artifact — with those very readings visible — cannot "
        "reach `sigma_zero_verdict` at all"
    )
    assert record["reduction"] == "phase23_prereg.noise_floor", (
        f"the record names its reduction {record['reduction']!r}. It must name the SYMBOL, not a "
        "formula: a formula in the artifact is a reduction the writer could have chosen"
    )
    assert record["central_reading"] == readings[0], (
        "`sigma_zero_verdict` pins the central reading to `control_readings[0]` — the reading at "
        "the FIRST recorded seed. The record's `central_reading` must be that same value"
    )

    # Every reading travels with its denominator. A rate with no denominator is exactly the kind of
    # figure this project has had to retract.
    for entry in record["per_seed"]:
        for tier in ("primary", "heldout_on", "taught_off", "heldout_off"):
            block = entry[tier]
            assert block["n"] > 0 and block["questions"] > 0, (
                f"seed {entry['seed']}'s {tier} reading has denominator n={block['n']!r} over "
                f"{block['questions']!r} questions — a rate over zero is not a rate"
            )
            assert block["rate"] == block["k"] / block["n"], (
                f"seed {entry['seed']}'s {tier} rate {block['rate']!r} is not "
                f"{block['k']}/{block['n']}"
            )


def test_the_control_floor_names_what_it_governs():
    """A floor that does not say what it may judge is one consumer away from a borrowing."""
    record = _record(CONTROL_FLOOR_RECORD)
    governs = record["governs"]
    assert isinstance(governs, str) and governs.strip(), (
        f"`governs` is {governs!r}. `sigma_zero_verdict` REFUSES a floor whose governed "
        "quantity is unstated: an unlabelled number is indistinguishable from a borrowed one"
    )
    assert (
        record["primary_reading"].lower() in governs.lower() or "taught recall" in governs.lower()
    )

    residual = record["residual_differences"]
    assert isinstance(residual, list) and residual, (
        "`residual_differences` is empty. The control and the σ=0 arm are NOT the same "
        "computation, and an undisclosed structural residual surfaces as a spurious D-04 halt "
        "with no way to tell it from a DP bug — this list is the first place that investigation "
        "looks"
    )
    for entry in residual:
        assert entry["difference"].strip() and entry["why_not_eliminable"].strip(), (
            f"a residual difference is recorded without both halves: {entry!r}. Naming the "
            "difference without naming why it is not eliminable through `train_arm` reads as an "
            "oversight rather than a disclosure"
        )

    for key in FLOOR_PROVENANCE_KEYS:
        assert key in record, (
            f"the control-floor record is missing {key!r} from "
            "`phase23_prereg.FLOOR_PROVENANCE_KEYS` — `sigma_zero_verdict` refuses it in 23-10"
        )


def test_a_drifted_corpus_is_refused(tmp_path):
    """T-23-44 / T-23-55: the corpus-digest refusal, WATCHED RED under a flipped hex character.

    This is the phase's only new structural guard on the data path and the sole named mitigation
    for both threats: a silent no-op here lets the σ=0 arm train on a drifted corpus, producing a
    spurious D-04 HALT or masking a real one. A grep for ``SystemExit`` in a function body cannot
    tell a raising guard from a dead one, so the guard is DRIVEN.

    TWO INDEPENDENT DETECTORS, ``tests/test_phase22_fakes.py``'s discipline:

    * the BEHAVIOURAL one — drive ``prove_bins_match`` with one digest wrong and observe the raise;
    * the CALL-SITE one — AST-prove ``rebuild_arm_bins_verifying_sha256`` still CALLS it. Watching a
      helper redden proves nothing if production stopped calling it.
    """
    files = {}
    for name, payload in (("train.bin", b"\x01\x02\x03\x04"), ("mask.bin", b"\x00\x01\x00\x01")):
        path = tmp_path / name
        path.write_bytes(payload)
        files[str(path)] = hashlib.sha256(payload).hexdigest()

    # GREEN HALF — the correct digests are admitted, so the refusal below is not a blanket reject.
    assert phase23_run.prove_bins_match(files) == 2

    # RED HALF — flip ONE hex character of ONE digest. The flip is computed, never typed, so the
    # "wrong" digest is guaranteed to differ from the real one by exactly one character.
    drifted_path = sorted(files)[0]
    honest = files[drifted_path]
    flipped = ("1" if honest[0] != "1" else "2") + honest[1:]
    wrong = dict(files)
    wrong[drifted_path] = flipped

    with pytest.raises(SystemExit) as refused:
        phase23_run.prove_bins_match(wrong)
    message = str(refused.value)
    assert pathlib.Path(drifted_path).name in message, (
        f"the refusal does not name the offending FILE — an investigator is told a bin drifted "
        f"without being told which one.\nmessage: {message}"
    )
    assert flipped in message, (
        f"the refusal does not quote the EXPECTED digest, so the reader cannot tell whether the "
        f"expectation or the file is wrong.\nmessage: {message}"
    )
    assert honest in message, (
        f"the refusal does not quote the ACTUAL digest, so the drift cannot be attributed to a "
        f"known build.\nmessage: {message}"
    )

    # SECOND DETECTOR — production still calls it.
    source = inspect.getsource(phase23_run.rebuild_arm_bins_verifying_sha256)
    called = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
    }
    assert "prove_bins_match" in called, (
        "`rebuild_arm_bins_verifying_sha256` no longer calls `prove_bins_match`. The RED above "
        f"would then be a guard nothing invokes. Calls found: {sorted(n for n in called if n)}"
    )

    # And the empty-mapping case is refused rather than reported as a vacuous success.
    with pytest.raises(SystemExit) as vacuous:
        phase23_run.rebuild_arm_bins_verifying_sha256(
            "dp_n8", facts=(), family_ids=(), seed=1337, expected_sha256={}
        )
    assert "EMPTY" in str(vacuous.value)


def test_the_seed_count_came_from_the_blind_rule():
    """D-03 / T-23-83: N is ``phase23_prereg.choose_n_seeds`` applied to the MEASURED cost.

    Re-derived here from the record's own numbers rather than trusted: the recorded N must be what
    the blind rule returns on the recorded ``seconds_per_seed``, and the recorded arithmetic against
    ``H_PER_POINT_FLOOR_SECONDS`` must be the arithmetic that rule performed.
    """
    record = _record(CONTROL_FLOOR_RECORD)
    rule = record["seed_count_rule"]
    assert rule["rule"] == "phase23_prereg.choose_n_seeds"
    assert rule["bound_seconds"] == phase23_prereg.H_PER_POINT_FLOOR_SECONDS, (
        f"the record pins the bound at {rule['bound_seconds']!r} but "
        f"`phase23_prereg.H_PER_POINT_FLOOR_SECONDS` is "
        f"{phase23_prereg.H_PER_POINT_FLOOR_SECONDS!r} — a retyped bound is a bound free to "
        "disagree with the one the rule enforces, invisibly"
    )
    seconds = rule["measured_seconds_per_seed"]
    expected_n = phase23_prereg.choose_n_seeds(seconds)
    assert record["n_seeds"] == expected_n, (
        f"the record used N={record['n_seeds']!r} but `choose_n_seeds({seconds!r})` returns "
        f"{expected_n!r}. N is the blind rule's output on the measured cost, not a chosen number"
    )
    assert rule["projected_total_seconds"] == expected_n * seconds
    assert rule["fits_the_bound"] == (
        expected_n * seconds <= phase23_prereg.H_PER_POINT_FLOOR_SECONDS
    )
    assert rule["n_is_the_d03_floor"] == (expected_n == 3)


def test_the_driver_defines_no_pre_registration_of_its_own():
    """T-23-83: the driver IMPORTS the blind rules and defines no local copy of any of them.

    ``scripts/phase23_run.py`` is re-edited by 23-08's own Tasks 2 and 3 and by 23-10, 23-11 and
    23-14, so ``git log -1`` on it returns its most recent commit and NO ancestry check could bind a
    rule written there to the measurement it decides. A copy would look identical and prove nothing.
    """
    source = (_ROOT / "scripts" / "phase23_run.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    for rule in ("choose_n_seeds", "noise_floor", "sigma_zero_verdict", "n64_leg_is_committable"):
        assert rule not in defined, (
            f"`scripts/phase23_run.py` DEFINES {rule!r}. Every pre-registered rule must be "
            "imported from the edit-once `scripts/phase23_prereg.py`; a copy here carries no "
            "ancestry guard"
        )

    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "phase23_prereg"
        for alias in node.names
    }
    assert {"choose_n_seeds", "noise_floor", "H_PER_POINT_FLOOR_SECONDS"} <= imported, (
        f"the driver imports {sorted(imported)} from `phase23_prereg` — the seed rule, the "
        "reduction and the bound must all come from the edit-once module"
    )

    # And the bound is never a retyped literal. Comment lines are stripped first because the
    # driver's prose restatement of the rule is allowed to SPELL the figure for a reader.
    code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
    for literal in ("17175", "17_175"):
        assert literal not in code, (
            f"the driver contains the literal {literal!r} outside a comment. The bound comes from "
            "`H_PER_POINT_FLOOR_SECONDS`; a retyped copy would be free to drift from it"
        )
