"""WR-04: ``privacy_n`` is VALIDATED, and reaching the frozen pin's version is a RED import graph.

Two halves, and neither is the other:

  * the BEHAVIOUR half — the continuation refuses what the frozen pin silently admits, proved as a
    DIFFERENTIAL on one set of inputs. The pin's wrong answers are COMPUTED here rather than quoted,
    which is ``tests/test_phase20_prereg.py::test_a_same_commit_pin_and_artifact_is_refused``'s
    standing rule for a superseded predicate: the old answer is executed, never described.
  * the REACHABILITY half — nothing in Python can make ``from mitigation_unit import privacy_n``
    fail or redirect without editing the pin, and editing the pin is the one thing that cannot be
    done (its ancestry guard takes ``adds[-1]``, so a later commit reddens it permanently and a
    ``git rm`` plus re-add cannot launder it). So the supersession is enforced the way this
    repository already enforces the gate/budget split and the Phase 20 coverage correction: an AST
    census over ``scripts/`` and ``src/`` that goes RED on the first bypass.
    ``.planning/ROADMAP.md:139-144`` calls this making a separation "a fact about the import graph
    rather than a paragraph".

THE EXEMPTIONS ARE RESOLVED BY PATH IDENTITY, NEVER BY NAME
==========================================================
Exactly two files may reach the pin's ``privacy_n``, and both are matched by RESOLVED ``pathlib``
identity against ``__file__``-derived constants — not by a filename substring, not by a comment, not
by a marker in the source. A substring rule would exempt any file a later author happened to name
``..._continuation.py``, including one written specifically to slip past. That failure mode is not
hypothetical here: 21-09 shipped a census test that was itself one of the sites it was counting, and
the plan-checker caught it by luck. ``test_the_exemption_is_path_identity_and_not_a_name`` builds a
DECOY under ``tmp_path`` with the continuation's exact filename and proves it is still flagged.

``tests/`` IS DELIBERATELY OUT OF SCOPE, and the decision is recorded rather than left implicit.
``tests/test_phase21_unit_pin.py`` asserts what the FROZEN MODULE does — including
``mitigation_unit.privacy_n(n) == n`` at both capacities — and those assertions are a RECORD of the
pin's behaviour, not a consumer of it. A test that drives the pin's own branches is the behavioural
twin of the pin and not a bypass of the correction; this is verbatim the reason
``tests/test_phase20_correction.py:1401-1405`` gives for excluding ``tests/`` from the
``mitigation_point_verdict`` census. The scope is asserted mechanically below rather than assumed,
and so is this file's own absence from the scanned set.

CPU-only, GPU-free, no torch, no network.
"""

import ast
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import mitigation_unit  # noqa: E402  (needs the sys.path insert above)
import phase21_unit_continuation as continuation  # noqa: E402  (same reason)

_PIN_MODULE = "mitigation_unit"
_SUPERSEDED = "privacy_n"

# THE EXEMPT SET, as RESOLVED PATHS. `.resolve()` on both sides so a symlinked checkout, a relative
# glob result and an absolute one all compare equal — an exemption that depends on how the path was
# spelled is a name rule wearing a path rule's clothes.
_PIN_PATH = (_SCRIPTS / "mitigation_unit.py").resolve()
_CONTINUATION_PATH = (_SCRIPTS / "phase21_unit_continuation.py").resolve()
_EXEMPT = frozenset({_PIN_PATH, _CONTINUATION_PATH})

# The three inputs WR-04 names. Kept as one table so the behaviour half and the differential half
# cannot drift into testing different values — the failure mode `tests/test_phase21_unit_pin.py:39`
# records for its own two-capacity table.
#
# (input, what the FROZEN pin returns, the phrase the continuation's refusal must carry)
_REFUSED = (
    (7.9, 7, "TRUNCATES"),
    (0, 0, "STRICTLY positive"),
    (-3, -3, "STRICTLY positive"),
)


def _scanned_files():
    """``scripts/*.py`` + ``src/**/*.py`` — the D-21 file set, resolved.

    Deliberately not cached: the decoy probes below write files under ``tmp_path`` and the real-tree
    scan must be recomputed against the live directory, not against a snapshot taken at import.
    """
    return sorted(p.resolve() for p in _SCRIPTS.glob("*.py")) + sorted(
        p.resolve() for p in (_ROOT / "src").rglob("*.py")
    )


def _pin_routes(tree):
    """Every site in ``tree`` that reaches ``privacy_n`` THROUGH THE PIN, in both import forms.

    Returns ``[(lineno, source-form)]``, sorted.

    BOTH FORMS FEED ONE RESULT, which is the property
    ``tests/test_phase20_prereg.py:873-876`` states for the gate/budget guard — "both
    ``import mitigation_budget`` and ``from mitigation_budget import ...`` feed the same
    ``imported`` set, so one assertion covers both forms". Here they are:

      1. ``from mitigation_unit import privacy_n`` — with or without ``as``. A star import counts
         too: it binds ``privacy_n`` and is the form nobody thinks to forbid.
      2. ``import mitigation_unit [as X]`` followed by ``X.privacy_n`` — the aliased attribute form,
         which is what ``scripts/phase21_unit_record.py`` actually used (``import mitigation_unit as
         mu`` then ``mu.privacy_n(n)``). A matcher keyed on the literal name ``mitigation_unit``
         would have missed it.

    TWO PASSES, because the binding must be complete before the attribute pass runs. ``ast.walk`` is
    breadth-first, so a module-scope attribute is visited before a function-local ``import`` that
    binds the alias it uses; a single pass would silently miss that ordering.

    What this does NOT flag, deliberately: any OTHER pin name. ``mu.DELTA``, ``mu.SAMPLING_RATE_Q``
    and ``mu.rejected_delta`` are correct and every consumer must keep importing them FROM THE PIN.
    Only ``privacy_n`` was superseded, so only ``privacy_n`` is refused — a census that forbade the
    whole module would push consumers into re-typing pinned constants, which is the defect one level
    over.
    """
    bound = set()
    hits = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == _PIN_MODULE:
                    bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] != _PIN_MODULE:
                continue
            for alias in node.names:
                if alias.name in (_SUPERSEDED, "*"):
                    tail = f" as {alias.asname}" if alias.asname else ""
                    hits.append((node.lineno, f"from {node.module} import {alias.name}{tail}"))

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == _SUPERSEDED
            and isinstance(node.value, ast.Name)
            and node.value.id in bound
        ):
            hits.append((node.lineno, f"{node.value.id}.{_SUPERSEDED}"))

    return sorted(hits)


def _routes_in(path):
    return _pin_routes(ast.parse(pathlib.Path(path).read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------------------------
# THE BEHAVIOUR HALF — RED on the pin, GREEN on the continuation, one set of inputs.
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("value, pin_answer, phrase", _REFUSED)
def test_the_pin_still_silently_admits_what_wr04_measured(value, pin_answer, phrase):
    """THE OLD PREDICATE, COMPUTED — the wrong answer executed, never described.

    ``tests/test_phase20_correction.py::test_the_three_defects_are_still_live_in_the_frozen_pin``'s
    register: a description that outlives its defect is worse than no description, because it
    teaches a reader to distrust a module that is now correct. If any row here goes red the pin has
    MOVED — and the pin cannot be edited, so that is a finding to report rather than a test to
    update.
    """
    got = mitigation_unit.privacy_n(value)
    assert got == pin_answer, (
        f"the frozen pin's privacy_n({value!r}) returned {got!r}, not {pin_answer!r}. WR-04 "
        f"records {pin_answer!r} as MEASURED behaviour of scripts/mitigation_unit.py:134-141. A "
        "change here means the pin moved, which its ancestry guard makes impossible to do cleanly"
    )
    assert isinstance(got, int), got


@pytest.mark.parametrize("value, pin_answer, phrase", _REFUSED)
def test_the_continuation_refuses_what_the_pin_admits(value, pin_answer, phrase):
    """THE NEW PREDICATE, on the SAME inputs — so this is a differential, not two observations.

    ``SystemExit`` rather than ``ValueError`` is this repository's refusal register for a broken
    invariant (``scripts/mitigation_unit.py:70-79``, ``scripts/teach_persona.py:743-750``): an
    ``assert`` is strippable under ``-O``, and a validator that vanishes under an optimisation flag
    is not a validator.

    The message is asserted to carry a phrase naming WHY, not merely to exist. A refusal that says
    only "invalid" sends its reader back to the source to find out what it objected to.
    """
    with pytest.raises(SystemExit) as refused:
        continuation.privacy_n(value)

    message = str(refused.value)
    assert "phase21_unit_continuation" in message, (
        f"the refusal does not name its own module: {message!r}. The pin records why the bracketed "
        "prefix matters — an abort naming the wrong module sends its reader to the wrong file, and "
        "this one supersedes a function that lives in a file it is not"
    )
    assert repr(value) in message, (
        f"the refusal does not name the value it rejected: {message!r}. Naming it is what turns "
        "the abort into a diagnosis of the CALLER rather than a complaint about the callee"
    )
    assert phrase in message, (
        f"the refusal does not carry {phrase!r}, so it does not say why a privacy N cannot take "
        f"{value!r}: {message!r}"
    )


@pytest.mark.parametrize("value", (True, False))
def test_bool_is_refused_although_it_is_an_int(value):
    """``bool`` SUBCLASSES ``int``, so a plain ``isinstance(n, int)`` test ADMITS it.

    Under the frozen pin ``privacy_n(True)`` is ``1`` and ``privacy_n(False)`` is ``0`` — a privacy
    N produced from a flag, and in the ``False`` case an N of zero, which clears the pin's own
    ``delta * N < 0.01`` ceiling by construction. Both are COMPUTED here.

    The predicate is ``scripts/teach_persona.py:744``'s, adopted rather than re-invented: the same
    quantity is already refused on ``isinstance(n_facts, bool) or not (isinstance(n_facts, int) and
    n_facts > 0)`` one file over, and two guards on one quantity must not disagree.
    """
    assert mitigation_unit.privacy_n(value) == int(value)

    with pytest.raises(SystemExit) as refused:
        continuation.privacy_n(value)
    assert "bool" in str(refused.value), (
        f"the refusal does not name `bool`: {refused.value}. A reader told that True is not an int "
        "will check, find that Python says it is, and distrust the guard"
    )


def test_a_string_is_refused_although_the_pin_parses_it():
    """``privacy_n('8')`` is ``8`` under the pin — ``int()`` PARSES, and parsing is not counting."""
    assert mitigation_unit.privacy_n("8") == 8

    with pytest.raises(SystemExit) as refused:
        continuation.privacy_n("8")
    assert "str" in str(refused.value)


def test_an_exact_float_is_refused_on_the_same_terms_as_an_inexact_one():
    """The decided case, asserted so the decision is a fact rather than a paragraph.

    ``7.0`` is refused. Admitting it would make the verdict depend on whether the upstream defect
    happened to land on a whole number, so one defective caller would pass at one capacity and fail
    at another. The measured corroboration is here too: ``3.0000000001`` is visibly not an integer
    but the class it belongs to is invisible at more digits, and the pin truncates every member of
    it — so "looks whole" and "is whole" are different properties, and refusing the TYPE removes the
    question instead of answering it per value.
    """
    assert mitigation_unit.privacy_n(7.0) == 7
    assert mitigation_unit.privacy_n(3.0000000001) == 3

    for value in (7.0, 3.0000000001):
        with pytest.raises(SystemExit) as refused:
            continuation.privacy_n(value)
        assert "float" in str(refused.value)


@pytest.mark.parametrize("value", (1, 8, 64, 12345))
def test_a_correct_positive_int_is_admitted_unchanged(value):
    """NOT VACUOUS IN THE OTHER DIRECTION — a validator that refuses everything is as useless as one
    that admits everything.

    ``is`` and not merely ``==``: the admitted value is returned as the SAME OBJECT, with no cast
    on the way out. A cast on the success path would be the pin's defect surviving inside its own
    correction, invisible because it agrees on every value that was already correct.
    """
    got = continuation.privacy_n(value)
    assert got is value
    assert got == mitigation_unit.privacy_n(value)


def test_the_published_capacities_are_unmoved_by_the_correction():
    """The property that lets ``scripts/phase21_unit_record.py`` be redirected without re-emitting.

    Every committed ``results/phase21_*`` row carrying an N carries it at ``n = 8`` or ``n = 64``.
    The continuation agrees with the pin at both, so the redirect moves no published number. The
    same equality is proved at IMPORT by a module-level guard in the continuation — this is the
    second tier, which fails at COLLECTION naming the decision, in the two-tier shape
    ``tests/test_phase21_unit_pin.py:3-13`` states.
    """
    assert continuation.PUBLISHED_CAPACITIES == (8, 64)
    for n in continuation.PUBLISHED_CAPACITIES:
        assert continuation.privacy_n(n) == mitigation_unit.privacy_n(n) == n


def test_only_privacy_n_is_superseded():
    """The continuation NARROWS one name and re-exports nothing else — asserted on module data."""
    assert continuation.SUPERSEDES == "mitigation_unit.privacy_n"
    for name in (
        "PRIVACY_UNIT",
        "PRIVACY_UNIT_ARITHMETIC",
        "SAMPLING_RATE_Q",
        "DELTA",
        "DELTA_TIMES_N_CEILING",
        "REJECTED_DELTA_RECIPE",
        "REJECTED_DELTA_REASON",
        "REPLAY_OUTSIDE_N",
        "rejected_delta",
    ):
        assert hasattr(mitigation_unit, name), name
        assert not hasattr(continuation, name), (
            f"the continuation re-exports {name}, which the pin gets RIGHT. A continuation that "
            "shadows the whole pin is a second copy of it, free to drift — 'a number appearing in "
            "two artifacts is two numbers that can disagree', at module scope"
        )


# ---------------------------------------------------------------------------------------------
# THE REACHABILITY HALF — the AST import census.
# ---------------------------------------------------------------------------------------------


def test_privacy_n_has_no_route_through_the_pin_outside_this_module():
    """WR-04's enforcement: reaching the pin's ``privacy_n`` is RED in ``scripts/`` and ``src/``.

    Modelled on ``tests/test_phase20_prereg.py:867-905`` (both import forms into one result) and on
    ``tests/test_phase20_correction.py:1377-1473`` (path-identity exemptions, non-vacuity proved on
    a synthetic tree because the real one yields zero).

    MEASURED GREEN at zero bypasses today, and that zero is an ENFORCED zero rather than an
    exempted one: ``scripts/phase21_unit_record.py`` held the only live site in ``scripts/``
    (``import mitigation_unit as mu`` + ``mu.privacy_n(n)``, at the ``lot`` block and inside the
    ``delta.capacities`` rows) and was REDIRECTED to the continuation rather than added to the
    exempt set. The second of those two sites is the defect's live blast radius today — its ``n``
    is multiplied by DELTA and checked against the published ceiling, so a truncated or
    non-positive N there clears the ceiling rather than merely mislabelling a row.

    WHAT THIS DOES NOT COVER, recorded as a STATE rather than implied closed — the same two gaps
    ``tests/test_phase20_correction.py:1395-1399`` names for its own census, inherited here because
    they are properties of static analysis and not of this particular matcher:

      1. ``getattr(mitigation_unit, "privacy_n")`` and
         ``importlib.import_module("mitigation_unit").privacy_n`` produce no ``ast.Attribute`` whose
         ``.attr`` is ``privacy_n``, so neither is visible to this walk.
      2. The scan is ``scripts/`` + ``src/``. A driver at the repo root or under ``tools/`` is
         unpoliced.

    Neither is closed here. The honest summary is that NOTHING IN PYTHON forces the import — no
    hook, shadow or rename can redirect ``from mitigation_unit import privacy_n`` without editing
    the pin, and the pin cannot be edited — so this is the strongest available mechanism, not a
    complete one. ``scripts/phase20_gate_coverage.py:74-81`` records exactly the same conclusion for
    ``mitigation_point_verdict``.
    """
    scanned = _scanned_files()
    assert scanned, "the scan set is empty — every assertion below would be green over nothing"

    bypassing = []
    for path in scanned:
        if path in _EXEMPT:
            continue
        bypassing.extend(
            f"{path.relative_to(_ROOT)}:{lineno}  {form}" for lineno, form in _routes_in(path)
        )

    assert bypassing == [], (
        f"{len(bypassing)} site(s) reach privacy_n through the FROZEN pin instead of through "
        f"scripts/phase21_unit_continuation.py: {bypassing}. The pin's version is "
        "`return int(n_facts)`, which TRUNCATES rather than refuses — measured, privacy_n(7.9) is "
        "7, privacy_n(0) is 0 and privacy_n(-3) is -3 — so a caller that reaches it can compute an "
        "epsilon about a lot that does not exist, and at N = 0 the pin's own delta * N ceiling "
        "passes by construction. The pin is FROZEN and cannot be fixed in place (WR-04); import "
        "`privacy_n` from the continuation instead. Every OTHER pinned name still comes from the "
        "pin and is untouched by this census"
    )


def test_the_census_scope_excludes_tests_and_this_file_itself():
    """The 21-09 lesson, asserted rather than trusted: the census is not one of its own sites.

    21-09 shipped a census test that was itself one of the sites it was counting. This file imports
    ``mitigation_unit`` at module scope and would be a hit if it were in scope, so "``tests/`` is
    excluded" is not a detail here — it is the difference between a guard and a guard that exempts
    itself by accident. Both halves are MECHANICAL: the scan set is compared against this file's own
    resolved path, and against the ``tests/`` directory.
    """
    scanned = _scanned_files()
    own = pathlib.Path(__file__).resolve()

    assert own not in scanned, (
        f"{own} entered the scanned set — the census would be measuring itself, which is how a "
        "guard becomes green over its own violation"
    )
    tests_dir = (_ROOT / "tests").resolve()
    inside_tests = [p for p in scanned if tests_dir in p.parents]
    assert inside_tests == [], (
        f"the census reached {inside_tests} under tests/. tests/test_phase21_unit_pin.py asserts "
        "what the FROZEN MODULE does, including privacy_n(n) == n at both capacities; those "
        "assertions are a RECORD of the pin's behaviour, not a consumer of it, and reddening them "
        "would delete the record of the defect being corrected"
    )

    # The positive half — the pin's own test file WOULD be a hit if the scope ever widened, so the
    # exclusion above is load-bearing rather than incidental. Asserted on the real file.
    pin_tests = (_ROOT / "tests" / "test_phase21_unit_pin.py").resolve()
    assert _routes_in(pin_tests), (
        f"{pin_tests.name} carries no route to the pin's privacy_n, so the tests/ exclusion is "
        "protecting nothing and this reasoning has gone stale"
    )


@pytest.mark.parametrize(
    "source, expected_forms",
    (
        ("from mitigation_unit import privacy_n\n", ["from mitigation_unit import privacy_n"]),
        (
            "from mitigation_unit import privacy_n as pn\n",
            ["from mitigation_unit import privacy_n as pn"],
        ),
        ("from mitigation_unit import *\n", ["from mitigation_unit import *"]),
        (
            "import mitigation_unit\nx = mitigation_unit.privacy_n(8)\n",
            ["mitigation_unit.privacy_n"],
        ),
        ("import mitigation_unit as mu\nx = mu.privacy_n(8)\n", ["mu.privacy_n"]),
        (
            "def f():\n    import mitigation_unit as mu\n    return mu.privacy_n(8)\n",
            ["mu.privacy_n"],
        ),
    ),
)
def test_the_census_fires_on_a_real_module_that_imports_from_the_pin(
    tmp_path, source, expected_forms
):
    """NON-VACUITY: the census FIRES, proved on real files rather than on parsed strings.

    Each probe is written to ``tmp_path`` as a ``.py`` file and read back through the same
    ``_routes_in`` the live guard calls, so this proves something about the function CI runs and not
    about a lookalike.

    The last row is the ordering case the two-pass design exists for: a FUNCTION-LOCAL
    ``import mitigation_unit as mu`` binds an alias that a single breadth-first pass would not have
    seen before visiting the attribute.
    """
    probe = tmp_path / "bypass.py"
    probe.write_text(source, encoding="utf-8")
    assert [form for _lineno, form in _routes_in(probe)] == expected_forms


@pytest.mark.parametrize(
    "source",
    (
        "from phase21_unit_continuation import privacy_n\n",
        "import phase21_unit_continuation as puc\nx = puc.privacy_n(8)\n",
        "import mitigation_unit as mu\nx = mu.DELTA * 8\n",
        "import mitigation_unit as mu\nx = mu.rejected_delta(8)\n",
        "privacy_n = 8\nx = privacy_n\n",
    ),
)
def test_the_census_is_not_refusing_everything(tmp_path, source):
    """The other direction — a census that flags every module proves nothing about any of them.

    Rows 1-2: the SANCTIONED route must be clean, or the guard forbids its own remedy.
    Rows 3-4: every other pinned name still reaches the pin legally. Only ``privacy_n`` moved.
    Row 5: a local variable that happens to be called ``privacy_n`` is not a route to anything.
    """
    probe = tmp_path / "clean.py"
    probe.write_text(source, encoding="utf-8")
    assert _routes_in(probe) == []


def test_the_exemption_is_path_identity_and_not_a_name(tmp_path):
    """The exemption cannot be inherited by NAMING a file after the continuation.

    A DECOY is written at ``tmp_path/phase21_unit_continuation.py`` — the exempt file's exact
    basename — carrying the bypass. It must still be flagged, because ``_EXEMPT`` holds RESOLVED
    PATHS and the decoy's path is not one of them. A substring or basename rule would exempt it, and
    would exempt any file a later author named to slip past.

    The real exempt files are asserted to be exactly two, and to EXIST: an exemption pointing at a
    path that is not there is an exemption that silently stops applying after a rename, which is the
    same failure with the sign flipped.
    """
    decoy = tmp_path / _CONTINUATION_PATH.name
    decoy.write_text("from mitigation_unit import privacy_n\n", encoding="utf-8")

    assert decoy.name == _CONTINUATION_PATH.name
    assert decoy.resolve() not in _EXEMPT
    assert [form for _lineno, form in _routes_in(decoy)] == [
        "from mitigation_unit import privacy_n"
    ], (
        "a file merely NAMED phase21_unit_continuation.py escaped the census. The exemption must "
        "be path identity; a name rule exempts any file a later author chooses to call this"
    )

    assert len(_EXEMPT) == 2, sorted(str(p) for p in _EXEMPT)
    for path in sorted(_EXEMPT):
        assert path.is_file(), (
            f"{path} is exempt but does not exist — an exemption aimed at a missing path stops "
            "applying silently the moment the real file is renamed"
        )

    # The two exemptions are each load-bearing, proved by what they hold: the continuation reaches
    # the pin (that is its whole job) and the pin DEFINES the name rather than importing it.
    assert _routes_in(_CONTINUATION_PATH), (
        "the continuation does not import the pin, so its exemption protects nothing and the "
        "supersession has lost the thing it supersedes"
    )
    assert _routes_in(_PIN_PATH) == [], (
        "the frozen pin now carries a route to its own privacy_n — it DEFINES the name and imports "
        "nothing at all (D-22). Its exemption is exclude-the-definition, not a route being allowed"
    )
