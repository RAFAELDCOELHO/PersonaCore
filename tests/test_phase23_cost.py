"""CAL-01 / CAL-05 — the cost record's completeness, its refusals, and the no-bare-mean guard.

``scripts/phase23_cost.py`` holds no measurement (23-11 takes those). What it holds is the SHAPE a
cost record must have and the four refusals that make CAL-05's *floor, not mean* a property of the
artifact rather than a note beside it. This file proves those properties hold, and proves two of
them TWICE — once about an instance and once about the module's own source text — because an
instance test only sees the records someone thought to build.

THREE THINGS HERE ARE DELIBERATE AND A LATER READER SHOULD NOT "SIMPLIFY" THEM:

  1. ``test_training_cost_record_is_complete`` asserts the REGISTER, not only one hand-built
     record. A test that validates a single instance cannot notice a key being dropped from the
     register, because the fixture is built FROM the register and would lose the key in the same
     motion.
  2. ``test_incomplete_cost_record_is_refused`` is parametrized over EVERY member of BOTH registers
     rather than over a sampled few. "Refused, never defaulted" is a claim about every key, and a
     sample proves it about the sampled ones.
  3. ``test_no_bare_mean_field_exists``'s structural half carries a META-GUARD asserting the AST
     walk found a non-empty set of string constants. An AST walk that silently stopped working
     finds nothing, and "found no forbidden key" is exactly what finding nothing looks like.

CPU-only, GPU-free, no network. ``torch`` is never imported: the timing helper's refusals fire
before its lazy import, which is itself part of what this file proves.
"""

import ast
import functools
import hashlib
import json
import operator
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import _prose  # noqa: E402  (needs the sys.path insert above)
import mitigation_gate  # noqa: E402  (same reason)
import phase23_cost  # noqa: E402  (same reason)
import phase23_prereg  # noqa: E402

_COST_MODULE_PATH = _ROOT / "scripts" / "phase23_cost.py"

# The prefix `scripts/phase23_prereg.py`'s docstring calls LOAD-BEARING: anything Phase 23 writes
# outside it falls outside every Phase-23 ancestry guard entirely. Typed once here and immediately
# checked against the register below, so this constant cannot drift away from the thing it names.
_PHASE23_RESULTS_PREFIX = "results/phase23"

# Every (kind, key) pair across BOTH registers — the parametrization for the refusal test. Built
# from the module's own registers, so a key added there gains a refusal case with no edit here.
_EVERY_REQUIRED_KEY = tuple(
    (kind, key)
    for kind, keys in (
        ("training", phase23_cost.TRAINING_RECORD_KEYS),
        ("generation", phase23_cost.GENERATION_RECORD_KEYS),
    )
    for key in keys
)

# The draw geometry is COMMITTED, not invented: `results/phase18_preflight_report.md:71-81` and
# `.planning/REQUIREMENTS.md:177-182`. The two hours are obvious placeholders whose only property
# under test is their ORDER — no Phase-23 cost number exists yet, and one that looks plausible in a
# fixture is one copy-paste away from an artifact.
_COMMITTED_DRAWS_PER_POINT = 42480
_COMMITTED_K_SCALED_QUESTIONS = 864
_COMMITTED_K = 48
_PLACEHOLDER_FLOOR_HOURS = 1.0
_PLACEHOLDER_CEILING_HOURS = 3.0


def _generation(**overrides):
    """A complete generation record: the committed draw geometry, placeholder hours, SYNTHETIC rest.

    Built through ``phase23_cost._synthetic_record`` so the key set comes from the module's own
    register rather than from a hand-list that can drift away from it.
    """
    fields = {
        "h_per_point_floor": _PLACEHOLDER_FLOOR_HOURS,
        "h_per_point_ceiling": _PLACEHOLDER_CEILING_HOURS,
        "draws_per_point": _COMMITTED_DRAWS_PER_POINT,
        "questions": _COMMITTED_K_SCALED_QUESTIONS,
        "k_per_question": _COMMITTED_K,
    }
    fields.update(overrides)
    return phase23_cost._synthetic_record("generation", **fields)


def _complete(kind):
    """A record of ``kind`` that ``validate_record`` admits — the control every refusal needs."""
    return _generation() if kind == "generation" else phase23_cost._synthetic_record(kind)


def _module_tree():
    """``scripts/phase23_cost.py`` parsed. The structural halves assert about SOURCE, not about
    an instance somebody remembered to build."""
    return ast.parse(_COST_MODULE_PATH.read_text(encoding="utf-8"))


def _string_constants(tree, *, skip_assignment=None):
    """Every ``str`` constant in the module, excluding one named module-scope assignment.

    ``skip_assignment`` exists so the forbidden-key REGISTER itself is not reported as a violation
    of the rule it defines. Everything else — docstrings, messages, dict keys, tuple members — is
    in scope, at any nesting depth inside a top-level statement.
    """
    found = set()
    for top in tree.body:
        if (
            skip_assignment is not None
            and isinstance(top, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == skip_assignment
                for target in top.targets
            )
        ):
            continue
        found.update(
            node.value
            for node in ast.walk(top)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        )
    return found


# =================================================================================================
# ===== CAL-01: completeness, and refusal rather than default =====
# =================================================================================================


def test_training_cost_record_is_complete():
    """A complete training record validates, AND the register itself carries the denominators.

    The second half is the one that bites. `warmup_iterations_discarded`, `timed_iterations`,
    `max_steps` and `batch_size` are what turn "seconds" into a rate anybody can check; a register
    that lost one would still admit every fixture built from it, because the fixture is built FROM
    the register. So the register is asserted directly.
    """
    phase23_cost.validate_record(_complete("training"), kind="training")

    denominators = (
        "warmup_iterations_discarded",
        "timed_iterations",
        "max_steps",
        "batch_size",
    )
    missing = [key for key in denominators if key not in phase23_cost.TRAINING_RECORD_KEYS]
    assert not missing, (
        f"TRAINING_RECORD_KEYS no longer requires {missing} — the denominator keys. A rate with no "
        "denominator is exactly the kind of figure this project has had to retract, and dropping "
        "one from the register drops it from every fixture built out of the register too"
    )


@pytest.mark.parametrize(("kind", "key"), _EVERY_REQUIRED_KEY)
def test_incomplete_cost_record_is_refused(kind, key):
    """Drop ANY one required key from ANY record and the record is REFUSED, never defaulted.

    Parametrized over every member of both registers rather than a sample: "every key" is the
    claim, and a sample proves it about the sampled keys only. The control validation at the top
    is what makes each case interpretable — it establishes that the ONLY thing wrong with the
    record under test is the key this case removed.
    """
    record = _complete(kind)
    phase23_cost.validate_record(record, kind=kind)  # the control: complete, it is admitted

    del record[key]
    with pytest.raises(SystemExit) as refusal:
        phase23_cost.validate_record(record, kind=kind)

    message = str(refusal.value)
    assert key in message, f"the refusal for a missing {key!r} does not name it: {message!r}"
    assert "never defaulted" in message, (
        f"the refusal for a missing {key!r} does not state that it is refused rather than "
        f"defaulted, which is the whole CAL-01 property: {message!r}"
    )


# =================================================================================================
# ===== CAL-05: no bare mean, instance-wise AND structurally =====
# =================================================================================================


def test_no_bare_mean_field_exists():
    """Two halves. A bare mean cannot be in a RECORD, and cannot be in the MODULE'S SOURCE either.

    The instance half covers the nested case explicitly, because a top-level ``in`` check would
    pass a record carrying the same defect one level down — a per-shape sub-record is the obvious
    place for one to hide.

    The structural half is the stronger of the two and the reason both exist: the instance half can
    only refuse the records someone thought to build, while an AST scan of the module's own string
    constants catches a forbidden field name being introduced by the module itself — in an emitter,
    a default, or a docstring example somebody later copies.
    """
    for forbidden in phase23_cost.FORBIDDEN_MEAN_KEYS:
        top_level = _generation(**{forbidden: 4.77})
        with pytest.raises(SystemExit) as refusal:
            phase23_cost.validate_record(top_level, kind="generation")
        assert forbidden in str(refusal.value)

        nested = _generation()
        nested["per_shape"] = [{"shape": "A1-mild", forbidden: 4.77}]
        with pytest.raises(SystemExit) as refusal:
            phase23_cost.validate_record(nested, kind="generation")
        message = str(refusal.value)
        assert forbidden in message, (
            f"a NESTED {forbidden!r} was not named in the refusal: {message!r}. The walk must see "
            "depth — a top-level `in` would admit this record"
        )
        assert "per_shape.0" in message, (
            f"the refusal does not locate the nested {forbidden!r}: {message!r}"
        )

    constants = _string_constants(_module_tree(), skip_assignment="FORBIDDEN_MEAN_KEYS")

    # META-GUARD. An AST walk that silently stopped working returns an empty set, and an empty set
    # satisfies the assertion below vacuously — "found no forbidden key" is precisely what finding
    # nothing looks like. So prove the walk collected, and collected from OUTSIDE the skipped
    # assignment: `h_per_point_ceiling` lives in GENERATION_RECORD_KEYS and in `size_sweep`'s
    # `sized_against` field, both outside FORBIDDEN_MEAN_KEYS.
    assert constants, "the AST walk found no string constants at all — it is not working"
    assert "h_per_point_ceiling" in constants, (
        "the AST walk did not find `h_per_point_ceiling`, which is present outside "
        "FORBIDDEN_MEAN_KEYS in two places — the walk or the skip is over-reaching"
    )

    leaked = sorted(constants & set(phase23_cost.FORBIDDEN_MEAN_KEYS))
    assert not leaked, (
        f"{_COST_MODULE_PATH.name} contains the string constant(s) {leaked} outside "
        "FORBIDDEN_MEAN_KEYS. A module that names a bare mean field anywhere but in the register "
        "forbidding it is one copy-paste from emitting one, and a consumer that can read a mean is "
        "the failure CAL-05 exists to prevent"
    )


# =================================================================================================
# ===== CAL-05: the sizing refuses the floor-only record and is PROVEN to use the ceiling =====
# =================================================================================================


def test_sizing_refuses_a_floor_only_record():
    """A record with a floor and no ceiling REFUSES, and the message says why there is no rescue.

    Naming the missing field is not enough on its own. The consequence is what a reader needs: the
    ratchet only lets K increase, so a sweep sized against the floor and found too expensive cannot
    be made cheaper. A refusal that says "missing key" and stops leaves that unsaid.
    """
    floor_only = _generation()
    del floor_only["h_per_point_ceiling"]

    with pytest.raises(SystemExit) as refusal:
        phase23_cost.size_sweep(generation_record=floor_only, sweep_points=16, k=_COMMITTED_K)

    message = str(refusal.value)
    assert "h_per_point_ceiling" in message, message
    assert "ratchet" in message.lower(), (
        f"the refusal does not name the ratchet reason: {message!r}. Without it the message says "
        "a field is missing but not that the under-budgeting it would cause is unrecoverable"
    )
    assert "h_per_point_floor" in message, (
        f"the refusal does not say what it is refusing to fall back to: {message!r}"
    )


def test_sizing_uses_the_ceiling_not_the_floor():
    """THE POSITIVE CONTROL. A sizing that quietly used the floor passes "does not raise"; not this.

    The projected hours must equal the sweep width times the CEILING scaled to the requested rung,
    and must be strictly greater than the floor-derived figure reported beside them. Both halves
    are needed: the equality pins which end of the bracket was read, and the strict inequality
    proves the two are not the same number by construction of the fixture.
    """
    record = _generation()
    sweep_points = 16
    k = 24

    sizing = phase23_cost.size_sweep(generation_record=record, sweep_points=sweep_points, k=k)

    draws_at_k = record["draws_per_point"] + record["questions"] * (k - record["k_per_question"])
    scale = draws_at_k / record["draws_per_point"]
    ceiling_at_k = record["h_per_point_ceiling"] * scale
    floor_at_k = record["h_per_point_floor"] * scale

    # The K scaling against `.planning/REQUIREMENTS.md:177-182`'s committed table, so the scaling
    # model is checked against a published artifact rather than only against itself.
    assert draws_at_k == 21744, (
        f"K={k} projects {draws_at_k} draws/point from the committed K={_COMMITTED_K} geometry, "
        "but the committed per-point table prices that rung at 21744"
    )

    assert sizing["draws_per_point_at_k"] == draws_at_k
    assert sizing["h_per_point_ceiling_at_k"] == ceiling_at_k
    assert sizing["projected_hours"] == sweep_points * ceiling_at_k, (
        f"the projection is {sizing['projected_hours']!r}, not {sweep_points * ceiling_at_k!r}. "
        "It is being computed from the wrong end of the bracket"
    )
    assert sizing["floor_hours"] == sweep_points * floor_at_k
    assert sizing["projected_hours"] > sizing["floor_hours"], (
        f"the projection {sizing['projected_hours']!r} is not above the floor-derived "
        f"{sizing['floor_hours']!r} — a floor-using implementation reads exactly like this"
    )
    assert sizing["sized_against"] == "h_per_point_ceiling", (
        "the sizing does not DECLARE which end it used; 23-13 asserts this field on every "
        "_PROVENANCE dict it writes"
    )


def test_a_ceiling_below_its_floor_is_refused():
    """The unit / condition mix-up. The stop-disabled end cannot be cheaper than the stop-active.

    It matters because the inversion is silent: the record still has both keys, still validates
    every other way, and would size the sweep SHORT in the direction the ratchet cannot rescue.
    """
    backwards = _generation(h_per_point_ceiling=_PLACEHOLDER_FLOOR_HOURS / 2)

    with pytest.raises(SystemExit) as refusal:
        phase23_cost.validate_record(backwards, kind="generation")

    message = str(refusal.value)
    assert "BACKWARDS" in message, message
    assert "ratchet" in message.lower(), (
        f"the refusal does not state the consequence, only the inversion: {message!r}"
    )

    # And it is refused at the sizing door too, not merely at the schema door.
    with pytest.raises(SystemExit):
        phase23_cost.size_sweep(generation_record=backwards, sweep_points=16, k=_COMMITTED_K)


# =================================================================================================
# ===== CAL-01: the timing helper's denominator =====
# =================================================================================================


def test_the_timing_helper_refuses_too_few_iterations():
    """``warmup=0`` and ``iterations=1`` both refuse, naming the denominator reasoning.

    The counter proves the refusal happens BEFORE anything is executed or timed. That is not a
    detail: a helper that ran the callable and then complained would already have paid the device
    cost this refusal exists to make unnecessary, and would have imported torch to do it.
    """
    calls = []

    def _never():  # pragma: no cover - the point is that it is not called
        calls.append(1)

    for kwargs in ({"warmup": 0}, {"iterations": 1}):
        with pytest.raises(SystemExit) as refusal:
            phase23_cost.time_iterations(_never, device="cpu", **kwargs)
        message = str(refusal.value)
        assert "denominator" in message, (
            f"{kwargs} refused without naming the denominator reasoning: {message!r}"
        )
        assert "minimum" in message, f"{kwargs} refused without naming the bound: {message!r}"

    assert not calls, (
        f"the callable ran {len(calls)} time(s) before the refusal. The iteration-count refusal "
        "must fire before any work is submitted — and before the lazy torch import"
    )


def test_the_schema_half_needs_no_torch():
    """``import torch`` appears only inside a function body — the schema half stays importable.

    Asserted about the SOURCE rather than about ``sys.modules``, for the reason
    ``tests/test_phase23_budget.py`` records about in-process import probes: by the time this file
    runs, sibling tests have already put torch in ``sys.modules``, so an in-process check would be
    vacuous. A module-scope ``import torch`` here would make the whole cost schema — registers,
    refusals, sizing — unimportable in a torch-free context for no benefit.
    """
    tree = _module_tree()
    module_scope_imports = {
        alias.name
        for top in tree.body
        if isinstance(top, (ast.Import, ast.ImportFrom))
        for alias in getattr(top, "names", ())
    }
    assert "torch" not in module_scope_imports, (
        f"{_COST_MODULE_PATH.name} imports torch at module scope: {sorted(module_scope_imports)}"
    )

    function_scope = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for inner in ast.walk(node)
        if isinstance(inner, ast.Import)
        for alias in inner.names
    ]
    assert "torch" in function_scope, (
        "torch is imported nowhere in the module — the timing helper cannot synchronize without it"
    )


# =================================================================================================
# ===== The artifact path comes from the edit-once register, never from a literal =====
# =================================================================================================


def test_the_cost_record_path_comes_from_the_prereg_register():
    """The path is RESOLVED from ``phase23_prereg``, and no path literal exists to drift from it.

    THE DEFECT CLASS THIS GUARDS, measured in this repository rather than imagined: plans and
    modules that name artifact paths which then drift apart, so a driver writes one path while a
    guard watches another and neither notices. ``scripts/phase23_prereg.py`` is the phase's single
    source of every path it writes, and it is EDIT-ONCE — a literal copy here could not be
    corrected there even if the drift were found.
    """
    assert phase23_cost.COST_RECORD is phase23_prereg.COST_RECORD, (
        "phase23_cost.COST_RECORD is not the SAME OBJECT as the register's — it has been copied, "
        "and a copy is exactly what can drift"
    )
    assert phase23_prereg.COST_RECORD.startswith(_PHASE23_RESULTS_PREFIX), (
        f"the register's cost path {phase23_prereg.COST_RECORD!r} is outside "
        f"{_PHASE23_RESULTS_PREFIX!r} — everything Phase 23 writes must carry that prefix or it "
        "falls outside every Phase-23 ancestry guard entirely"
    )

    constants = _string_constants(_module_tree())
    assert constants, "the AST walk found no string constants at all — it is not working"

    literals = sorted(value for value in constants if _PHASE23_RESULTS_PREFIX in value)
    assert not literals, (
        f"{_COST_MODULE_PATH.name} contains the path literal(s) {literals}. The path is resolved "
        f"from phase23_prereg.COST_RECORD by attribute access, which involves no literal at all — "
        "so any occurrence here is a second copy with nothing keeping it in step"
    )


# =================================================================================================
# ===== 23-11 — THE COMMITTED COST RECORD ITSELF =====
#
# Everything above is about the SHAPE, provable before any number existed. Everything below binds on
# `results/phase23_cost.json`, the artifact 23-11 measured — and `test_the_cost_record_is_committed`
# is what stops the rest of them going quietly vacuous if that artifact ever leaves the index.
# =================================================================================================


def _cost():
    """The committed cost record, or ``None`` before 23-11 wrote it."""
    path = _ROOT / phase23_prereg.COST_RECORD
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_cost_record_is_committed():
    """The other five tests below return early when the record is absent. This one does not.

    A `return None` on a missing file is the right shape for a record that does not exist YET, and
    the wrong shape for one that has been deleted. This test is the difference: once the artifact is
    tracked it must STAY tracked, so a deletion is a RED here rather than five silent passes.
    """
    tracked = subprocess.run(
        ["git", "ls-files", phase23_prereg.COST_RECORD],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert tracked == [phase23_prereg.COST_RECORD], (
        f"`git ls-files {phase23_prereg.COST_RECORD}` returned {tracked!r}. Every test below reads "
        "that record and returns early when it is absent, so an untracked or deleted cost record "
        "would leave five guards green and blind"
    )


def test_the_committed_cost_record_validates():
    """W6 — ``validate_record`` against NAMED mappings, and the assembled blocks satisfy it.

    ``validate_record(record, *, kind)`` takes a MAPPING and checks the register INSIDE it, so
    "validate for both kinds" is not an instruction until the mappings are named. They are: the
    four ``training.*`` blocks at ``kind="training"`` and the ``generation`` block at
    ``kind="generation"``. ``ratios`` and ``sizing`` are DERIVED and are covered by the
    re-derivation test below instead.
    """
    record = _cost()
    if record is None:
        return
    for name, block in record["training"].items():
        phase23_cost.validate_record(block, kind="training")
        assert block, f"training.{name} is empty"
    phase23_cost.validate_record(record["generation"], kind="generation")
    assert sorted(record["training"]) == [
        "dp_n64",
        "dp_n8",
        "non_dp",
        "non_dp_superseded_protocol",
    ], sorted(record["training"])


def test_the_cost_record_ratios_re_derive():
    """A stored ratio that no longer re-derives is a number nobody can check.

    Asserted with ``==`` and never ``pytest.approx``: each field is written from exactly this
    quotient in exactly this float order, so any inequality means it was TYPED rather than computed.

    ``training.non_dp.wall_clock_gap_vs_superseded`` is covered HERE rather than in its own test
    because it is the same shape — a quotient of two stored fields — and it is the field 23-12
    quotes by path, so it is the one that most needs to be un-typeable.
    """
    record = _cost()
    if record is None:
        return
    generation = record["generation"]

    for name, block in record["ratios"].items():
        seconds = block["training_seconds_per_point"]
        source = block["training_seconds_per_point_source"]
        # The named source field must actually be where the number came from.
        assert source.startswith(f"training.{name}."), source
        stored = functools.reduce(operator.getitem, source.split("."), record)
        assert stored == seconds, (
            f"ratios.{name}.training_seconds_per_point is {seconds!r} but its own named source "
            f"{source} holds {stored!r}"
        )
        assert block["eval_over_training_ceiling"] == (
            generation["h_per_point_ceiling"] * 3600 / seconds
        ), f"ratios.{name}.eval_over_training_ceiling does not re-derive from the record's fields"
        assert block["eval_over_training_floor"] == (
            generation["h_per_point_floor"] * 3600 / seconds
        ), f"ratios.{name}.eval_over_training_floor does not re-derive from the record's fields"

    gap = record["training"]["non_dp"]["wall_clock_gap_vs_superseded"]
    expected = (
        record["training"]["non_dp"]["training_seconds_mean"]
        / record["training"]["non_dp_superseded_protocol"]["training_seconds_mean"]
    )
    assert gap == expected, (
        f"training.non_dp.wall_clock_gap_vs_superseded is {gap!r} but the quotient of the two "
        f"stored training_seconds_mean fields is {expected!r}. This field exists precisely so the "
        "measured protocol gap is a SCALAR LEAF that 23-12 can quote by path and any reader can "
        "re-derive — a typed one would differ in the last digits without looking wrong"
    )


def test_borrowed_figures_cite_a_record_and_a_digest():
    """Every figure sourced from another artifact names it AND its digest, checked against disk.

    This is what stops a re-measured number silently replacing a cited one: the digest is recomputed
    here from the file as it stands, so a source record edited after the cost record was assembled
    reddens rather than passing on a stale citation.
    """
    record = _cost()
    if record is None:
        return
    blocks = dict(record["training"])
    assert blocks, "no training blocks to check — the walk found nothing"
    for name, block in blocks.items():
        source = block.get("source_record")
        assert isinstance(source, str) and source, (
            f"training.{name} carries no `source_record`. An unlabelled number is "
            "indistinguishable from a borrowed one"
        )
        path = _ROOT / source
        assert path.exists(), f"training.{name} cites {source}, which is not on disk"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert block.get("source_record_sha256") == digest, (
            f"training.{name} cites {source} at digest "
            f"{block.get('source_record_sha256')!r} but the file now hashes to {digest!r}"
        )


def test_every_timing_block_names_its_protocol():
    """A timing that does not say which protocol it timed is not a usable figure.

    A STRUCTURAL WALK over the record's own keys, never a hardcoded list — a fifth timing block
    added later is then caught rather than missed, which is the whole difference between a guard
    and a checklist.
    """
    record = _cost()
    if record is None:
        return
    seen = 0
    for name, block in record["training"].items():
        protocol = block.get("protocol")
        assert isinstance(protocol, str) and protocol.strip(), (
            f"training.{name} carries protocol {protocol!r}. The two measured NON-DP protocols "
            "differ in wall clock by training.non_dp.wall_clock_gap_vs_superseded, so a timing "
            "that does not name its protocol cannot be compared against anything"
        )
        seen += 1
    assert seen == len(record["training"]) and seen >= 4, (
        f"walked {seen} of {len(record['training'])} training block(s) — a structural guard that "
        "reads fewer blocks than exist is green and blind"
    )

    non_dp = record["training"]["non_dp"]
    superseded = record["training"]["non_dp_superseded_protocol"]
    assert non_dp["protocol"] != superseded["protocol"], (
        "the matched comparator and the superseded control carry the SAME protocol string. They "
        "are the two figures this record exists to keep apart"
    )
    assert non_dp["source_record"] != superseded["source_record"], (
        f"both non-DP blocks cite {non_dp['source_record']!r}. The superseded protocol is RECORDED "
        "BESIDE the matched one, never deleted and never merged into it"
    )
    assert non_dp["source_record"] == "results/phase23_matched_control.json", (
        f"training.non_dp cites {non_dp['source_record']!r}. The provenance decision is the "
        "protocol-matched comparator; a ratio is meaningless unless numerator and denominator "
        "describe the same experiment"
    )


def test_the_sizing_table_prices_the_never_taught_floor():
    """A sizing that prices 16 sweep points and forgets the N-seed control floor is short by N.

    N is READ from ``results/phase23_never_taught_training.json`` rather than assumed, and the line
    item is asserted at EVERY ``K_RUNGS`` entry — the ratchet only permits K to increase, so a rung
    priced without the floor is a rung with no rescue in the cheap direction.
    """
    record = _cost()
    if record is None:
        return
    never_taught = json.loads(
        (_ROOT / phase23_prereg.NEVER_TAUGHT_TRAINING_RECORD).read_text(encoding="utf-8")
    )
    n_seeds = never_taught["n_seeds"]
    assert record["k_rungs"] == list(mitigation_gate.K_RUNGS), record["k_rungs"]

    for k in mitigation_gate.K_RUNGS:
        row = record["sizing"][str(k)]
        assert row["never_taught_seeds"] == n_seeds, (
            f"K={k} prices {row['never_taught_seeds']!r} never-taught seeds against the committed "
            f"record's {n_seeds!r}"
        )
        assert row["never_taught_floor_hours_ceiling"] == (
            n_seeds * row["h_per_point_ceiling_at_k"]
        ), f"K={k}'s never-taught floor line item does not re-derive from N x the ceiling at K"
        assert row["total_hours_ceiling_with_never_taught_floor"] == (
            row["projected_hours"] + row["never_taught_floor_hours_ceiling"]
        ), f"K={k}'s total does not re-derive from the sweep projection plus the floor line item"
        assert row["sized_against"] == "h_per_point_ceiling", row["sized_against"]


# ---------------------------------------------------------------------------------------------
# 23-12 — the retract-in-place guard: additive, complete across three files, faithful to the record
# ---------------------------------------------------------------------------------------------

# The falsified claim, in the ONE form that survives all three phrasings. `.planning/ROADMAP.md`
# also mentions the bare numeral `1,010` on its plan-list line for 23-12 itself; that line carries
# no claim, and matching this longer text rather than the numeral is what keeps the completeness
# scan from demanding a retraction marker beside a plan description.
_CLAIM_TEXT = "~1,010× training"

_BEGIN_SENTINEL = "<!-- 23-12-CONTINUATION-BEGIN -->"
_END_SENTINEL = "<!-- 23-12-CONTINUATION-END -->"

# The marker shape, asserted with its date and the plan that wrote it. `.planning/STATE.md` already
# carried four earlier `RETRACTED IN PLACE` markers before 23-12 ran, so a bare substring search
# would find one of those and pass without this plan's correction existing at all.
_MARKER = re.compile(r"RETRACTED IN PLACE (\d{4}-\d{2}-\d{2}) \(plan 23-12\)")

_CORRECTED_FILES = (
    ".planning/REQUIREMENTS.md",
    ".planning/ROADMAP.md",
    ".planning/STATE.md",
)

# The file whose continuation is REQUIRED to publish the full pre-registered set. The other two
# carry the record, its digest, the ceiling and whichever figures their own claim needs — see
# `test_the_correction_quotes_the_cost_record_faithfully`'s docstring for why the split is not
# symmetric.
_FULL_SET_FILE = ".planning/REQUIREMENTS.md"

# 23-11 Part B pins these under the heading *THE PUBLISHED FIGURES ARE PRE-REGISTERED FIELD PATHS*;
# this is the SAME list and the two must not drift. NOT an allow-list — the polarity is the proof:
# every member must be PRESENT (half one) and nothing long may be present that is not a member
# (half two), so adding an entry makes the guard demand strictly more, never less.
REQUIRED_FIGURE_PATHS = [
    "training.non_dp.training_seconds_mean",
    "training.non_dp_superseded_protocol.training_seconds_mean",
    "training.non_dp.wall_clock_gap_vs_superseded",
    "training.dp_n8.seconds_total",
    "training.dp_n64.seconds_total",
    "generation.h_per_point_floor",
    "generation.h_per_point_ceiling",
    "ratios.non_dp.eval_over_training_ceiling",
    "ratios.non_dp_superseded_protocol.eval_over_training_ceiling",
    "ratios.dp_n8.eval_over_training_ceiling",
    "ratios.dp_n64.eval_over_training_ceiling",
]

# WHY 8, MEASURED RATHER THAN ASSUMED. Every float leaf of the four source records this phase reads
# (`phase23_matched_control`, `phase23_control_floor`, `phase23_sigma_zero`,
# `phase23_never_taught_training`) was histogrammed by fractional-digit count. The distribution is
# BIMODAL with an EMPTY separating band and the threshold sits inside it: 1-5 digits -> 130 leaves
# (exact rationals: recall rates k/n, `0.0`, the `0.0003` LR); 6-11 digits -> **0 leaves**; 12-18
# digits -> 259 leaves (every measured continuous quantity). Below the threshold sit all the
# numerals the prose legitimately carries: dates, plan ids, `D-03`, `CAL-05`, `SC2`, line citations,
# the quoted `1,010` and `17`, and the h/point table's `4.77` / `2.45` / `1.67` / `0.90`. The
# longest fractional rendering this repository produces structurally is 6, from
# `phase23_prereg.noised_record_path`'s six-decimal sigma, which the threshold clears.
MIN_FRACTIONAL_DIGITS = 8

# BUILT FROM the constant, never written beside it: re-binding `MIN_FRACTIONAL_DIGITS` retunes the
# guard, so the name is load-bearing rather than decorative. A sha256 digest is excluded
# STRUCTURALLY and not by exemption — hex digests carry long digit runs but never a `.` immediately
# preceded by a digit, so this pattern cannot match inside one.
LONG_FIGURE = re.compile(rf"\d[\d,]*\.\d{{{MIN_FRACTIONAL_DIGITS},}}(?:[eE][+-]?\d+)?")


def _figure(record, path):
    """The ``repr()`` of the leaf at a dotted ``path``, byte-identical to the record's own text.

    23-11 writes ``results/phase23_cost.json`` with ``json.dump``, which serialises floats through
    ``float.__repr__``, so this string is what the record file itself carries. No formatting, no
    rounding, no thousands separators.
    """
    node = record
    for key in path.split("."):
        node = node[key]
    return repr(node)


def _continuation(text):
    """The text strictly between the two sentinels, with their placement asserted.

    Counted with ``str.count`` and NOT with a line-based tool. ``grep -c`` counts LINES, so two
    BEGIN sentinels emitted on ONE line satisfy a ``grep -c ... = 1`` check while the split below
    then scans only the first span and the second goes unguarded. That defect is live in this
    repository: `.planning/REQUIREMENTS.md` carries two `RETRACTED IN PLACE` markers on a single
    line and `grep -c` returns 1 for it.
    """
    for sentinel in (_BEGIN_SENTINEL, _END_SENTINEL):
        found = text.count(sentinel)
        assert found == 1, (
            f"{sentinel} occurs {found} time(s); exactly one is required. A missing or duplicated "
            "sentinel makes the guard scan the wrong text, which is how a guard passes vacuously"
        )
    assert text.index(_BEGIN_SENTINEL) < text.index(_END_SENTINEL), (
        "the END sentinel precedes the BEGIN sentinel, so the continuation slice is empty or "
        "inverted"
    )
    return text.split(_BEGIN_SENTINEL, 1)[1].split(_END_SENTINEL, 1)[0]


def _required_figures_missing(text, record):
    """HALF ONE, record -> continuation: every pre-registered rendering, present VERBATIM.

    Catches an OMITTED figure and any ROUNDING of a required one — a rounding leaves the required
    full-precision string simply absent. Does NOT catch an invented extra figure; that is half
    two's direction and neither half implies the other.
    """
    return [
        f"{path} -> {_figure(record, path)}"
        for path in REQUIRED_FIGURE_PATHS
        if _figure(record, path) not in text
    ]


def _long_figures_not_sourced(text, record):
    """HALF TWO, continuation -> record: nothing long that is not one of the eleven renderings.

    That is the entire rule. Nothing is dropped, nothing is classified, no span is captured and no
    token is exempted — so a figure inside backticks is scanned exactly like one in prose, a figure
    on the marker line is in scope, and a figure carrying a thousands separator is CAUGHT rather
    than laundered, all by construction rather than by a patch.

    STATED RESIDUALS, disclosed rather than mechanised away. (a) An invented SHORT numeral is not
    caught: shape cannot separate it from the dates, plan ids and quoted falsified figures the
    prose legitimately carries, and it is bounded by half one, which asserts every required figure
    present at full precision so a short invention can only ever be ADDITIONAL. (b) A SIGN FLIP is
    not caught — the pattern has no sign class, so ``-2.035849685343305`` matches as the required
    rendering and passes both halves. ``[-−]?`` is deliberately NOT added: it makes a
    legitimate figure in a hyphenated range (``79-161.1239542257311``) match as a negative and
    FALSE-RED a correct continuation, and all eleven published quantities are positive so a
    negative rendering is nonsense a reader catches. (c) A NON-ASCII DECIMAL SEPARATOR is not
    caught: ``\\.`` matches only U+002E. The asymmetry is the useful half — Unicode DIGITS around an
    ASCII point ARE caught, since ``\\d`` is Unicode-aware by default.
    """
    sourced = {_figure(record, path) for path in REQUIRED_FIGURE_PATHS}
    return [match for match in LONG_FIGURE.findall(text) if match not in sourced]


@pytest.mark.parametrize("relative_path", _CORRECTED_FILES)
def test_cost_claim_correction_is_additive(relative_path):
    """The original claim SURVIVES, and a dated 23-12 marker sits after it, in all three files.

    The claim is matched through ``scripts/_prose.normalized`` rather than a bare ``in`` check:
    `.planning/STATE.md` line-wraps it as ``"~1,010×\\n  training"`` and a naive containment
    test reports a FALSE absence on it. The normalizer is IMPORTED, never re-written — a second
    copy of a matcher is a second matcher, free to stop matching.
    """
    record = _cost()
    if record is None:
        return
    text = (_ROOT / relative_path).read_text(encoding="utf-8")
    flat = _prose.normalized(text)

    claim = _prose.normalized(_CLAIM_TEXT)
    assert claim in flat, (
        f"{relative_path} no longer carries the original claim {_CLAIM_TEXT!r}. A correction that "
        "removes the sentence it corrects is a rewrite, not a retraction: the record of what was "
        "believed is the thing being preserved"
    )

    # Searched FROM the claim's position, so the assertion is "a dated 23-12 marker EXISTS after
    # the claim" and not "the FIRST marker in the file is after it". The stricter reading has a
    # measured false-RED channel and no extra teeth: `.planning/STATE.md`'s `stopped_at:`
    # frontmatter legitimately summarises this correction at byte 258, far above the claim, and
    # `.planning/ROADMAP.md`'s plan-list entry does the same. Refusing a file for describing its
    # own correction in a status line proves nothing about whether the correction is additive.
    where = flat.index(claim)
    marker = _MARKER.search(flat, where)
    assert marker is not None, (
        f"{relative_path} carries the claim at {where} with no `RETRACTED IN PLACE <date> "
        "(plan 23-12)` marker anywhere after it. A correction landing in one of three files "
        "leaves two standing, and one landing above the claim is not a continuation of it"
    )

    body = _prose.normalized(_continuation(text))
    assert phase23_prereg.COST_RECORD in body, (
        f"{relative_path}'s continuation does not name {phase23_prereg.COST_RECORD}. Every figure "
        "it publishes must be re-derivable from the artifact that measured them"
    )
    digest = hashlib.sha256((_ROOT / phase23_prereg.COST_RECORD).read_bytes()).hexdigest()
    assert digest in body, (
        f"{relative_path}'s continuation does not quote the live sha256 {digest} of "
        f"{phase23_prereg.COST_RECORD}"
    )

    # Every non-DP figure the continuation quotes must carry the `protocol` of the block it came
    # from. The acceptable strings are DERIVED from the record, never hardcoded here: a retyped
    # protocol label is a second label, free to drift away from the one the artifact carries.
    labelled = 0
    for key, block in record["training"].items():
        if not key.startswith("non_dp"):
            continue
        rendering = _figure(record, f"training.{key}.training_seconds_mean")
        if rendering not in body:
            continue
        labelled += 1
        assert _prose.normalized(block["protocol"]) in body, (
            f"{relative_path}'s continuation quotes training.{key}'s {rendering} without naming "
            f"its protocol {block['protocol']!r}. Two measured non-DP protocols disagree by "
            "training.non_dp.wall_clock_gap_vs_superseded, so an arm name alone identifies no "
            "number"
        )
    assert labelled, (
        f"{relative_path}'s continuation quotes NEITHER non-DP training mean, so the protocol "
        "check above passed vacuously"
    )


def test_the_correction_quotes_the_cost_record_faithfully():
    """HALF ONE — all eleven pre-registered renderings present in the REQUIREMENTS continuation.

    Bound on `.planning/REQUIREMENTS.md` ONLY, and the asymmetry with half two is deliberate. That
    is the file whose continuation is required to publish the full set; demanding all eleven inside
    the `.planning/ROADMAP.md` milestone preamble and the `.planning/STATE.md` status line would
    force those two documents to become copies of the first, which is not what a correction to a
    preamble or a status line should look like. Half two binds on all three, because an invented
    figure is just as false in a status line as in a requirements preamble.
    """
    record = _cost()
    if record is None:
        return
    body = _continuation((_ROOT / _FULL_SET_FILE).read_text(encoding="utf-8"))
    missing = _required_figures_missing(body, record)
    assert missing == [], (
        f"{_FULL_SET_FILE}'s continuation omits {len(missing)} pre-registered figure(s): "
        f"{missing}. A ROUNDING lands here too — the required full-precision string is then simply "
        "absent, which is the defect `2.04` for `2.035849685343305` would produce"
    )


def test_the_continuation_invents_no_figure():
    """HALF TWO — no long numeral in any of the three continuations that the record did not measure.

    The headline guard. Bound on ALL THREE slices, never on whole files: `.planning/REQUIREMENTS.md`
    `.planning/ROADMAP.md` and `.planning/STATE.md` already carried 69 / 25 / 98 literals with 8+
    fractional digits before 23-12 wrote a line — committed measurements from earlier phases, none
    of them leaves of the cost record — so a whole-file scan would RED on every one of them.
    """
    record = _cost()
    if record is None:
        return
    for relative_path in _CORRECTED_FILES:
        body = _continuation((_ROOT / relative_path).read_text(encoding="utf-8"))
        invented = _long_figures_not_sourced(body, record)
        assert invented == [], (
            f"{relative_path}'s continuation publishes {len(invented)} long figure(s) that are not "
            f"among the eleven pre-registered renderings: {invented}. 'Present somewhere in the "
            "record' is NOT the criterion — a floor-side ratio or a per-seed timing is a real leaf "
            "at full precision and is still refused here"
        )


_INVENTED_FIGURE = "37.51234567890123"
_ROUNDED_PATH = "training.non_dp.wall_clock_gap_vs_superseded"
_OMITTED_PATH = "generation.h_per_point_ceiling"


def _construct_defect(case, text, record):
    """Mutate ONLY the sentinel slice, so each constructed defect lands where the guard looks."""
    head, rest = text.split(_BEGIN_SENTINEL, 1)
    body, tail = rest.split(_END_SENTINEL, 1)

    if case == "invention-bare":
        body = f"{body}\nAn unmeasured figure: {_INVENTED_FIGURE}\n"
    elif case == "invention-backticked":
        body = f"{body}\nAn unmeasured figure: `{_INVENTED_FIGURE}`\n"
    elif case == "invention-on-the-marker-line":
        lines = body.split("\n")
        index = next(i for i, line in enumerate(lines) if "RETRACTED IN PLACE" in line)
        lines[index] = f"{lines[index]} {_INVENTED_FIGURE}"
        body = "\n".join(lines)
    elif case == "rounding":
        body = body.replace(_figure(record, _ROUNDED_PATH), "2.04")
    elif case == "omission":
        body = body.replace(_figure(record, _OMITTED_PATH), "")
    else:  # pragma: no cover - a case id with no construction is a test-authoring defect
        raise AssertionError(f"no construction for case {case!r}")

    return head + _BEGIN_SENTINEL + body + _END_SENTINEL + tail


@pytest.mark.parametrize(
    "case",
    (
        "invention-bare",
        "invention-backticked",
        "invention-on-the-marker-line",
        "rounding",
        "omission",
    ),
)
def test_the_guard_catches_a_constructed_defect(tmp_path, case):
    """Both halves watched REDDENING on a ``tmp_path`` COPY, never on the committed file.

    The three invention channels are covered BY CONSTRUCTION rather than by three patches: nothing
    is dropped and no span is captured, so backticks and the marker line are not special. The
    rounding and omission cases drive half one, which is the only half that sees them.
    """
    record = _cost()
    if record is None:
        return
    original = (_ROOT / _FULL_SET_FILE).read_text(encoding="utf-8")
    copy = tmp_path / "REQUIREMENTS.md"
    copy.write_text(_construct_defect(case, original, record), encoding="utf-8")
    body = _continuation(copy.read_text(encoding="utf-8"))

    if case.startswith("invention"):
        invented = _long_figures_not_sourced(body, record)
        assert invented == [_INVENTED_FIGURE], (
            f"case {case!r} was written into the slice and half two returned {invented!r}; the "
            "invented figure must be caught in every writing channel"
        )
        assert _required_figures_missing(body, record) == [], (
            f"case {case!r} displaced a required figure, so it does not isolate the invention half"
        )
    else:
        expected = _ROUNDED_PATH if case == "rounding" else _OMITTED_PATH
        missing = _required_figures_missing(body, record)
        assert missing == [f"{expected} -> {_figure(record, expected)}"], (
            f"case {case!r} was written into the slice and half one returned {missing!r}"
        )


def test_no_file_carrying_the_claim_was_left_uncorrected():
    """Every `.planning/*.md` carrying the claim also carries the dated 23-12 marker.

    Scanned over the DIRECTORY rather than a hand-listed tuple, so a fourth copy appearing at
    `.planning/` top level later is caught rather than missed.

    THE SCOPE IS PINNED AT ONE LEVEL, DELIBERATELY, AND THIS IS WHY. Made recursive, the same scan
    sweeps `.planning/phases/**` and reaches the artifacts that quote the claim as the record of
    what was believed WHEN THEY WERE WRITTEN — the phase's CONTEXT, RESEARCH, VALIDATION and
    several PLAN documents — and would demand a retraction marker inside each. Phase artifacts are
    dated records of a phase's own reasoning; retro-editing them is the opposite of
    retract-in-place, and `23-RESEARCH.md` is where the falsifying measurement is recorded in the
    first place. The documents a reader consults for what is CURRENTLY believed are exactly
    `.planning/*.md`. Do not "fix" this scope by widening it.

    The scan matches the normalized CLAIM TEXT and never the bare numeral: `.planning/ROADMAP.md`'s
    plan-list line for 23-12 mentions `1,010` while carrying no claim, and a numeral-matching scan
    would demand a retraction marker beside a plan description.
    """
    claim = _prose.normalized(_CLAIM_TEXT)
    carriers = []
    for path in sorted((_ROOT / ".planning").glob("*.md")):
        flat = _prose.normalized(path.read_text(encoding="utf-8"))
        if claim not in flat:
            continue
        carriers.append(path.name)
        assert _MARKER.search(flat) is not None, (
            f".planning/{path.name} carries the claim {_CLAIM_TEXT!r} with no "
            "`RETRACTED IN PLACE <date> (plan 23-12)` marker. The claim lives in more than one "
            "planning document and a correction landing in one leaves the others standing"
        )
    assert set(carriers) == {pathlib.Path(p).name for p in _CORRECTED_FILES}, (
        f"the set of `.planning/*.md` files carrying the claim is {carriers}, which is not the "
        "three this plan corrected. A new carrier needs its own continuation; a vanished one means "
        "the claim was deleted somewhere instead of retracted in place"
    )


def test_the_h_per_point_table_is_disclosed_as_a_floor():
    """The ceiling is published beside the table, and the table's `4.77` row still stands.

    A corrected ratio sitting beside an uncorrected floor-valued h/point table would reproduce
    exactly the defect CAL-05 exists to prevent, so the disclosure is asserted rather than assumed.
    """
    record = _cost()
    if record is None:
        return
    text = (_ROOT / _FULL_SET_FILE).read_text(encoding="utf-8")
    body = _continuation(text)
    assert "h_per_point_ceiling" in body, (
        "the REQUIREMENTS continuation does not name `h_per_point_ceiling`, so the h/point table's "
        "floor status is corrected without saying what the ceiling is"
    )
    ceiling = _figure(record, "generation.h_per_point_ceiling")
    assert ceiling in body, f"the continuation does not quote the measured ceiling {ceiling}"

    row = "| 48 (Phase 18 fidelity) | 42,480 | 4.77 | 76.3 h = 3.2 days | (1, 4, 16, 48) |"
    assert _prose.normalized(row) in _prose.normalized(text), (
        "the original `4.77` h/point row is gone. The table is LEFT STANDING and disclosed as a "
        "floor; deleting it destroys the record of what was believed"
    )
