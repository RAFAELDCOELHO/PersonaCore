"""THE CONTINUATION PIN, DRIVEN — every refusal watched, and the independence PROVED not asserted.

``scripts/phase23_resume_prereg.py`` admits ONE shape of state: the continuation of a matched run
the harness killed mid-ladder. It was written with three of that run's readings on screen, so the
central question a reviewer asks is not "is the rule correct" but "was it narrowed BECAUSE of those
readings". This file answers that structurally rather than by assurance:
``test_the_continuation_predicate_is_invariant_under_arbitrary_readings`` REBUILDS EVERY SEED BLOCK
with every value replaced and KEY PRESENCE ALONE preserved, and proves the derived arguments, the
verdict and the refusal message bit-identical across four states.

**THE STATE FIXTURE IS A PINNED BLOB, AND THE PIN IS THE POINT.** Every state below is derived
through ``rp.seed_status`` from ``git show d99d2aa:data/phase23_run_state.json`` — never typed, and
never read from the working tree. MEASURED: that blob carries exactly three scored matched seeds,
and ``git merge-base --is-ancestor d99d2aa HEAD`` exits 0, so it is reachable forever and its bytes
cannot change. The LIVE state file does change: 23-20's own Task 3 rewrites it to FIVE scored seeds
and commits it, which would flip this file's admitted case from ADMIT to REFUSE — after the GPU run,
which is the expensive place to find out. The pin makes every case here time-invariant.

**AND THE ``tracked`` LISTS ARE CONSTRUCTED, NOT LISTED** — they are the un-pinned sibling of the
state fixture and they fail the same way at the same cost. Every list is BUILT from conjunct 7's own
formula via ``rp.seed_run_csv``, never from a live ``git ls-files`` of the matched glob: once the
record is written and committed that glob returns the record too, and conjunct 6 refuses precisely
that path. A test sourcing it live is green through Tasks 1 and 2 and red only after the run.

**THE TWO GIT REFS ARE DIFFERENT ON PURPOSE.** Production conjunct 5 reads ``HEAD:`` — its job is
"the working tree agrees with history NOW", a deliberately time-VARYING property. This fixture reads
the pinned commit — its job is a FIXED state to exercise the predicate against. Collapsing either
into the other breaks the one it was moved to.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase23_matched_prereg as mp  # noqa: E402  (needs the sys.path insert above)
import phase23_resume_prereg as rp  # noqa: E402  (same reason)

# IMPORTED AND CALLED, NEVER COPIED — `tests/test_phase23_matched_prereg.py:9-13`'s discipline: a
# lookalike copy would prove something about a DIFFERENT function than the one CI executes.
from test_phase20_prereg import _git  # noqa: E402  (same reason)

_RESUME_PIN = "scripts/phase23_resume_prereg.py"
_MATCHED_PIN = "scripts/phase23_matched_prereg.py"
_MATCHED_PIN_COMMIT = "c100388"
_RUN_SOURCE = _ROOT / "scripts" / "phase23_run.py"

# THE PINNED FIXTURE. `d99d2aa` is the earliest add of the matched artifacts and is already an
# ancestor of HEAD, so this blob is reachable forever and its bytes cannot change. See the module
# docstring for why the LIVE working-tree file is never opened here.
_PINNED_STATE = "d99d2aa:data/phase23_run_state.json"


def _pinned_section():
    """The pinned commit's ``matched`` section — the ONLY state source in this file."""
    return json.loads(_git("show", _PINNED_STATE))["matched"]


def _ladder():
    """``phase23_run.SEED_LADDER``, read off LIVE SOURCE by AST rather than imported or retyped.

    Imported, it would drag ``torch`` in through ``phase23_run``'s import chain and make this
    GPU-free file depend on it. Retyped, it would be a second source for a fact ``phase23_run.py``
    owns — which is the defect this whole gap closure exists to correct. Parsed, it is neither.
    """
    tree = ast.parse(_RUN_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "SEED_LADDER" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"no `SEED_LADDER = ...` in {_RUN_SOURCE} — the ladder has no source")


def _tracked(seeds):
    """A ``tracked`` list CONSTRUCTED from conjunct 7's own formula, never from a live glob."""
    return sorted(rp.seed_run_csv(seed) for seed in seeds)


def _admitted_case():
    """The killed run's real state, DERIVED from the pinned blob — never typed."""
    trained, scored = rp.seed_status(_pinned_section())
    ladder = _ladder()
    return {
        "tracked": _tracked(sorted(scored) + [ladder[len(scored)]]),
        "ladder": ladder,
        "trained_seeds": trained,
        "scored_seeds": scored,
        "committed_scored_seeds": scored,
        "record_exists": False,
    }


def _refused(**case):
    """Run the predicate and return the refusal text, failing if it ADMITS."""
    with pytest.raises(SystemExit) as refusal:
        rp.prove_killed_run_continuation(**case)
    return str(refusal.value)


# =================================================================================================
# ===== THE ADMITTED SHAPES — one per ADMITS bullet =====
# =================================================================================================


def test_the_killed_runs_real_state_is_admitted():
    """The state the harness kill actually left, derived from the pinned blob, is ADMITTED."""
    case = _admitted_case()
    ladder = case["ladder"]
    assert case["scored_seeds"] == set(ladder[: len(case["scored_seeds"])]), (
        "META: the pinned fixture's scored set is not a ladder PREFIX, so this file is exercising "
        f"a state the loop cannot produce: {sorted(case['scored_seeds'])} vs {list(ladder)}"
    )
    assert 0 < len(case["scored_seeds"]) < len(ladder), (
        "META: the pinned fixture is not a PARTIAL run — this file would be testing nothing"
    )
    assert rp.prove_killed_run_continuation(**case) is True


def test_a_second_kill_leaving_one_trained_unscored_seed_is_admitted():
    """A SECOND kill mid-train of the next seed is admitted by the SAME rule, no new narrowing."""
    case = _admitted_case()
    following = case["ladder"][len(case["scored_seeds"])]
    case["trained_seeds"] = set(case["scored_seeds"]) | {following}
    assert rp.prove_killed_run_continuation(**case) is True


def test_a_fourth_scored_seed_is_admitted_once_its_state_is_committed():
    """The rule is written on PREFIXES, not on the number three."""
    case = _admitted_case()
    ladder = case["ladder"]
    longer = set(ladder[: len(case["scored_seeds"]) + 1])
    case.update(
        tracked=_tracked(sorted(longer) + [ladder[len(longer)]]),
        trained_seeds=longer,
        scored_seeds=longer,
        committed_scored_seeds=longer,
    )
    assert rp.prove_killed_run_continuation(**case) is True


# =================================================================================================
# ===== THE REFUSALS — one test per REFUSES bullet, every one WATCHED FIRING =====
# =================================================================================================


def test_a_scored_seed_whose_state_is_not_yet_committed_is_refused_with_the_remedy():
    """THE SECOND-KILL WINDOW. The refusal is CORRECT, and it carries the ordering that fixes it."""
    case = _admitted_case()
    ladder = case["ladder"]
    longer = set(ladder[: len(case["scored_seeds"]) + 1])
    committed = set(case["scored_seeds"])
    case.update(
        tracked=_tracked(sorted(longer) + [ladder[len(longer)]]),
        trained_seeds=longer,
        scored_seeds=longer,
        committed_scored_seeds=committed,
    )
    message = _refused(**case)
    assert "git add data/phase23_run_state.json" in message, (
        "the refusal does not carry the commit-then-relaunch remedy, so a reader who never opens "
        f"the plan gets no route out of it: {message!r}"
    )
    assert "SECOND KILL" in message and "NOT A FLAG" in message, (
        f"the refusal does not name the ordinary cause or rule out a flag: {message!r}"
    )


def test_a_completed_attempt_is_refused_by_the_write_ordering():
    """``len(scored) == len(ladder)`` is what a COMPLETED attempt leaves. The message says why."""
    case = _admitted_case()
    ladder = case["ladder"]
    every = set(ladder)
    case.update(
        tracked=_tracked(every),
        trained_seeds=every,
        scored_seeds=every,
        committed_scored_seeds=every,
    )
    message = _refused(**case)
    assert "WRITE-ORDERING" in message, (
        f"the completed-attempt refusal does not carry its own argument: {message!r}"
    )
    assert "CANNOT PRODUCE" in message


def test_an_existing_record_is_refused():
    """The record is recorded evidence; ``phase23_run.matched`` refuses it independently too."""
    case = _admitted_case()
    case["record_exists"] = True
    assert "ALREADY EXISTS" in _refused(**case)


def test_an_empty_scored_set_is_routed_to_the_frozen_rule():
    """No seed scored = a FIRST attempt = ``prove_first_attempt``'s business, not this rule's."""
    case = _admitted_case()
    case.update(tracked=[], trained_seeds=set(), scored_seeds=set(), committed_scored_seeds=set())
    message = _refused(**case)
    assert "prove_first_attempt" in message, (
        f"the empty-scored refusal does not route the reader to the frozen rule: {message!r}"
    )


def test_a_non_prefix_scored_set_is_refused():
    """The loop is SEQUENTIAL, so a killed run leaves a prefix. A hole is unexplainable."""
    case = _admitted_case()
    ladder = case["ladder"]
    hole = {ladder[0], ladder[2]}
    case.update(trained_seeds=hole, scored_seeds=hole, committed_scored_seeds=hole)
    assert "PREFIX" in _refused(**case)


def test_a_trained_set_running_ahead_of_the_ladder_is_refused():
    """At most ONE trained-but-unscored seed, and it is the NEXT ladder entry — both directions."""
    ladder = _ladder()

    two_ahead = _admitted_case()
    scored = set(two_ahead["scored_seeds"])
    two_ahead.update(
        tracked=_tracked(set(ladder)),
        trained_seeds=scored | {ladder[len(scored)], ladder[len(scored) + 1]},
    )
    assert "NEXT ladder entry" in _refused(**two_ahead)

    wrong_seed = _admitted_case()
    wrong_seed.update(
        tracked=_tracked(set(ladder)),
        trained_seeds=scored | {ladder[len(scored) + 1]},
    )
    assert "NEXT ladder entry" in _refused(**wrong_seed)

    unbacked = _admitted_case()
    unbacked["trained_seeds"] = set(list(scored)[1:])
    assert "NEXT ladder entry" in _refused(**unbacked)


def test_a_working_tree_disagreeing_with_history_is_refused_in_either_direction():
    """A hand-edited state file is what a disagreement looks like — from BOTH sides."""
    ladder = _ladder()

    tree_ahead = _admitted_case()
    tree_ahead["committed_scored_seeds"] = set(list(tree_ahead["scored_seeds"])[:-1])
    assert "DISAGREE" in _refused(**tree_ahead)

    history_ahead = _admitted_case()
    history_ahead["committed_scored_seeds"] = set(ladder[: len(history_ahead["scored_seeds"]) + 1])
    assert "DISAGREE" in _refused(**history_ahead)


def test_a_tracked_published_record_is_refused():
    """Neither the control record nor the verdict record may sit in the tracked set."""
    for record in (mp.MATCHED_CONTROL_RECORD, mp.MATCHED_VERDICT_RECORD):
        case = _admitted_case()
        case["tracked"] = [*case["tracked"], record]
        assert record in _refused(**case)


def test_a_tracked_path_outside_the_reached_seeds_is_refused():
    """A curve for an unreached seed, and any path that is not a per-seed curve at all."""
    case = _admitted_case()
    ladder = case["ladder"]
    unreached = rp.seed_run_csv(ladder[-1])
    case["tracked"] = [*case["tracked"], unreached]
    assert unreached in _refused(**case)

    not_a_curve = _admitted_case()
    stray = f"results/{mp.MATCHED_ARM_PREFIX}_{mp.matched_arm(ladder[0])}/notes.txt"
    not_a_curve["tracked"] = [*not_a_curve["tracked"], stray]
    assert stray in _refused(**not_a_curve)


# =================================================================================================
# ===== THE INDEPENDENCE PROOF — the whole block substituted, not three named fields =====
# =================================================================================================


def test_the_continuation_predicate_is_invariant_under_arbitrary_readings():
    """EVERY VALUE IN EVERY SEED BLOCK replaced; KEY PRESENCE ALONE preserved. Four states, one
    verdict, one refusal message, bit-identical.

    Perturbing only ``primary.rate``/``.k``/``.n`` would prove nothing: ``heldout_on.rate``,
    ``final_train_loss`` and ``training_seconds`` were on screen when the rule was written, so a
    narrowing keyed on any of those would survive a three-field probe. A predicate whose verdict or
    whose refusal TEXT moves with a reading is a predicate narrowed by one.
    """
    pinned = _pinned_section()
    ladder = _ladder()

    fillers = (0, 10**9, None)
    states = [pinned] + [
        {seed: {key: filler for key in block} for seed, block in pinned.items()}
        for filler in fillers
    ]
    assert len(states) == 4

    derived = []
    verdicts = []
    refusals = []
    for section in states:
        trained, scored = rp.seed_status(section)
        derived.append((sorted(trained), sorted(scored)))
        case = {
            "tracked": _tracked(sorted(scored) + [ladder[len(scored)]]),
            "ladder": ladder,
            "trained_seeds": trained,
            "scored_seeds": scored,
            "committed_scored_seeds": scored,
            "record_exists": False,
        }
        verdicts.append(rp.prove_killed_run_continuation(**case))

        # THE REFUSING CASE IS DERIVED FROM THE SUBSTITUTED COPY ITSELF. A case constructed
        # independently of the substitution would not be put through it and would prove nothing
        # about it. The missing seeds are COMPUTED — a hardcoded pair would be a second source for
        # a fact the section already carries, which is this module's own subject.
        missing = [seed for seed in ladder if str(seed) not in section]
        assert missing, (
            "META: the pinned fixture already carries every ladder seed, so this test cannot "
            "construct its refusing case and would pass VACUOUSLY. The fixture source has been "
            "repointed at a five-scored state — re-pin it."
        )
        completed = dict(section)
        for seed in missing:
            completed[str(seed)] = dict(next(iter(section.values())))
        full_trained, full_scored = rp.seed_status(completed)
        refusals.append(
            _refused(
                tracked=_tracked(set(ladder)),
                ladder=ladder,
                trained_seeds=full_trained,
                scored_seeds=full_scored,
                committed_scored_seeds=full_scored,
                record_exists=False,
            )
        )

    assert len(set(map(str, derived))) == 1, (
        f"the DERIVED arguments moved under a whole-block value substitution: {derived}"
    )
    assert verdicts == [True] * 4, f"the VERDICT moved under the substitution: {verdicts}"
    assert len(set(refusals)) == 1, (
        "the REFUSAL MESSAGE is not bit-identical across the substitution — the text carries a "
        f"reading: {refusals}"
    )
    assert "WRITE-ORDERING" in refusals[0]


# =================================================================================================
# ===== THE TRIPWIRES — AST, never grep, because this file's own prose names what it forbids =====
# =================================================================================================


def _resume_tree():
    return ast.parse((_ROOT / _RESUME_PIN).read_text(encoding="utf-8"))


def test_the_module_declares_no_float_constant():
    """AST, NOT GREP. The module's docstring discusses `0.7837301587301587` BY NAME, so a grep over
    this file would go false-RED against its own prose — this repository has shipped that defect.

    There is no quantity in the module that is not a seed, a count or a boolean, and a float
    appearing there would be a reading that had found its way in.
    """
    tree = _resume_tree()
    docstrings = {
        parent.body[0].value
        for parent in ast.walk(tree)
        if isinstance(parent, (ast.Module, ast.FunctionDef, ast.ClassDef))
        and parent.body
        and isinstance(parent.body[0], ast.Expr)
        and isinstance(parent.body[0].value, ast.Constant)
    }
    floats = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and node not in docstrings
        and isinstance(node.value, float)
    ]
    assert not floats, f"{_RESUME_PIN} declares float constant(s) {floats} — a reading got in"


def test_the_predicates_signature_admits_no_reading():
    """The independence argument's first leg, checked mechanically rather than by reading."""
    tree = _resume_tree()
    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.FunctionDef) and item.name == "prove_killed_run_continuation"
    )
    assert sorted(a.arg for a in node.args.kwonlyargs) == [
        "committed_scored_seeds",
        "ladder",
        "record_exists",
        "scored_seeds",
        "tracked",
        "trained_seeds",
    ]
    assert node.args.args == [] and node.args.posonlyargs == [], (
        "the predicate accepts a POSITIONAL argument, so a caller can transpose `trained` with "
        "`scored` and the rule would admit a state it never saw"
    )


def test_the_module_runs_no_subprocess_and_reads_no_live_state():
    """The CALLER runs git. And the module opens no file, so its self-check is TIME-INVARIANT.

    Exact-constant, not grep: a docstring MENTIONING the state path is a longer string and is never
    EQUAL to it, so this cannot go false-RED against the module's own prose. It catches ``open``,
    ``pathlib.read_text`` and every other mechanism at once, because all of them need the path.
    """
    tree = _resume_tree()
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not imported & {"subprocess", "torch", "requests", "urllib", "os"}, (
        f"{_RESUME_PIN} imports {sorted(imported)} — it must take its caller's git result, not "
        "run git itself"
    )
    live = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == _PINNED_STATE.split(":", 1)[1]
    ]
    assert not live, (
        f"{_RESUME_PIN} carries the LIVE state path as a constant. Its self-check would then read "
        "a file the run it governs rewrites to five scored seeds, and would refuse itself"
    )


def test_the_continuation_scope_carries_five_clauses_and_discloses_its_own_missing_freeze():
    """Clause (5) is the honest one: this module is NOT frozen and nothing freezes it."""
    scope = rp.CONTINUATION_SCOPE.upper()
    for clause in ("(1)", "(2)", "(3)", "(4)", "(5)"):
        assert clause in scope, f"CONTINUATION_SCOPE omits clause {clause}"
    assert "NOT FROZEN" in scope
    assert "DETECTION AFTER THE FACT, NOT PREVENTION" in scope, (
        "clause (5) does not state that the one-commit guard is weaker than the frozen pin's "
        "ancestry guarantee, which is the whole content of the disclosure"
    )


def test_the_resume_pin_has_exactly_one_commit():
    """The weaker-than-ancestry guard clause (5) of ``CONTINUATION_SCOPE`` discloses.

    **THIS IS DETECTION AFTER THE FACT, NOT PREVENTION, AND NOT THE ANCESTRY GUARANTEE**
    ``tests/test_phase23_matched_prereg.py`` gives the frozen pin. This module CANNOT be registered
    against ``MATCHED_ARTIFACT_GLOB``: ``adds[-1]`` for that glob is ``d99d2aa``, which PRECEDES any
    commit of this file, so ``_assert_ordering_holds``' second conjunct
    (``merge-base --is-ancestor prereg first_add``) can never hold for it. All this test can do is
    make a second edit VISIBLE on the next suite run.
    """
    commits = _git("log", "--format=%H", "--", _RESUME_PIN).split()
    assert len(commits) == 1, (
        f"{_RESUME_PIN} has {len(commits)} commits, not one. It was written ONCE, with the killed "
        "run's readings already on screen, and a second edit is a rule revised after seeing more "
        "of them. THIS TEST IS DETECTION, NOT PREVENTION: it cannot stop the edit, only surface "
        "it — the ancestry guarantee is structurally unavailable to this file, and clause (5) of "
        "CONTINUATION_SCOPE says so"
    )


def test_the_frozen_pin_is_byte_identical_to_c100388():
    """The chosen route left the frozen file ALONE — checked on every suite run, not once.

    A second commit touching `scripts/phase23_matched_prereg.py` would fail
    `_assert_ordering_holds`' ancestry conjunct against `d99d2aa` PERMANENTLY, with no recovery:
    `adds[-1]` takes the EARLIEST add, so delete-and-re-add launders nothing.
    """
    subprocess.run(
        ("git", "diff", "--exit-code", _MATCHED_PIN_COMMIT, "HEAD", "--", _MATCHED_PIN),
        cwd=_ROOT,
        check=True,
        capture_output=True,
    )
    commits = _git("log", "--format=%H", "--", _MATCHED_PIN).split()
    assert len(commits) == 1, (
        f"{_MATCHED_PIN} now has {len(commits)} commits. It is EDIT-ONCE from `d99d2aa` and the "
        "ancestry guard is reddened permanently by a second one"
    )
