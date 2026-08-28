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
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_gate  # noqa: E402  (needs the sys.path insert above)
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
