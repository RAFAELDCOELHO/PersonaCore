"""PLAN 25-12 — THE NOISE AXIS'S FOUR PINS, RE-DERIVED FROM THE RECORDS THEY CITE.

``scripts/mitigation_budget.py`` cannot compute anything: its literal-only guard
(``tests/test_phase23_budget.py::test_budget_holds_only_literal_constants``) refuses any
module-level node that is not an ``ast.Assign`` and calls ``ast.literal_eval`` on every assigned
value, so an ``epsilon_for(...)`` call and a ``sigma_for(...)`` call are both nodes it raises on.
The four pins are therefore TRANSCRIPTIONS, and this file is the other half: it recomputes every
one of them live and asserts the correspondence under exact ``==``.

**EVERY BUDGET CONSTANT IS READ AS ``mitigation_budget.NAME`` — ATTRIBUTE ACCESS, NEVER A
``from``-IMPORT — AND THAT IS LOAD-BEARING RATHER THAN STYLISTIC.**
``tests/test_phase23_budget.py::test_z_was_sized_against_the_ceiling`` excuses each of these four
names from its completeness register only while THIS file genuinely reads it, and it decides
"reads" with the walk ``{node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}``
— which collects ``ast.Attribute.attr`` and NOTHING ELSE. A ``from mitigation_budget import
SIGMA_LADDER`` plus a bare-name use is INVISIBLE to that walk: the register would go red with
"never reads SIGMA_LADDER" while this file was reading it on every line. Two tests at the bottom
enforce the rule from inside — one mirrors the register's own walk over this file, the other
refuses an ``ast.ImportFrom`` of the budget module — and a third WATCHES the trap fire on a
``tmp_path`` copy, so a future editor who "tidies" the imports gets a failure that names the cause.

**EVERY PATH RESOLVES FROM ITS OWNING MODULE'S CONSTANT.**
``phase25_calibrate.CLIP_CALIBRATION_RECORD`` for the clip measurement,
``phase25_sigma_hi.SIGMA_HI_RECORD`` for the anchor probe,
``phase25_calibrate.NORM_PROBE_CLIP_NORM_SOURCE`` for the sigma=0 control — never a string literal
here. This repository has shipped plans naming paths the code refuses, and a test that spells a
path itself agrees with the plan rather than with the code.

CPU-only, GPU-free: stdlib plus the accountant. No torch, no numpy, no network.
"""

import ast
import hashlib
import json
import math
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (needs the sys.path insert; scripts/ is not a package)
import mitigation_unit  # noqa: E402
import phase25_calibrate  # noqa: E402
import phase25_record  # noqa: E402
import phase25_sigma_hi  # noqa: E402

from personacore.privacy.accountant import epsilon_for, sigma_for  # noqa: E402

_THIS_FILE = pathlib.Path(__file__).resolve()

# The four names plan 25-12 registered in `tests/test_phase23_budget.py::_POST_23_13_CONSTANTS`
# against this file. Restated here so the self-check below is a statement about a declared set
# rather than about whatever this file happens to mention.
_REGISTERED = ("SIGMA_LADDER", "EPSILON_LADDER", "CLIP_NORM", "CONTROL_CLIP_NORM")

_NOISED_RUNGS = tuple(range(1, 16))


def _git(*args):
    """One git invocation from the repo root, stdout as text. `check=True` — a failure is a bug."""
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _clip_record():
    """25-11's committed clip calibration. Path from `phase25_calibrate`, never from a literal."""
    return phase25_calibrate.CLIP_CALIBRATION_RECORD, _read(
        phase25_calibrate.CLIP_CALIBRATION_RECORD
    )


def _probe_record():
    """25-12's committed sigma_hi anchor probe. Path from `phase25_sigma_hi`."""
    return phase25_sigma_hi.SIGMA_HI_RECORD, _read(phase25_sigma_hi.SIGMA_HI_RECORD)


def _control_record():
    """The committed sigma=0 control. Path from `phase25_calibrate.NORM_PROBE_CLIP_NORM_SOURCE`."""
    path = _ROOT / phase25_calibrate.NORM_PROBE_CLIP_NORM_SOURCE
    return path, _read(path)


# =================================================================================================
# ===== (a) THE SIGMA-TO-EPSILON CORRESPONDENCE, UNDER EXACT `==` =====
# =================================================================================================


def test_the_ladder_has_sweep_points_entries_with_the_control_at_slot_one():
    """D-20: sigma=0 is INSIDE `SWEEP_POINTS`, at slot 1 (index 0). 15 noised rungs per leg.

    The width is asserted against `SWEEP_POINTS` rather than against 16, so a future change to the
    pinned width cannot leave a ladder of the old length behind agreeing with a stale literal here.
    """
    ladder = mitigation_budget.SIGMA_LADDER

    assert isinstance(ladder, tuple) and ladder, f"`SIGMA_LADDER` is {ladder!r}"
    assert len(ladder) == mitigation_budget.SWEEP_POINTS, (
        f"`SIGMA_LADDER` carries {len(ladder)} rungs against SWEEP_POINTS "
        f"{mitigation_budget.SWEEP_POINTS} — the curve would be a different width than the one "
        "`results/phase23_cost.json` priced"
    )
    assert all(isinstance(rung, float) for rung in ladder), (
        f"`SIGMA_LADDER` carries a non-float rung: {ladder!r}. An int rung would compare equal to "
        "its float twin here and then render a different point key downstream"
    )
    assert ladder[0] == 0.0, (
        f"`SIGMA_LADDER` starts at {ladder[0]!r}, not 0.0. Slot 1 is the CONTROL under CTRL-02 and "
        "D-20, and it is what reconnects the DP curve to the incumbent result BY CONSTRUCTION"
    )
    assert len(set(ladder)) == len(ladder), (
        f"`SIGMA_LADDER` repeats a rung: {ladder!r}. A duplicated rung spends a point twice and "
        "collides on `phase25_record.point_key`"
    )
    assert len(mitigation_budget.EPSILON_LADDER) == len(ladder), (
        f"`EPSILON_LADDER` has {len(mitigation_budget.EPSILON_LADDER)} entries against "
        f"{len(ladder)} sigma rungs — one ladder would carry an epsilon the other has no sigma for"
    )


@pytest.mark.parametrize("index", _NOISED_RUNGS)
def test_each_noised_rung_lands_on_its_pinned_epsilon(index):
    """`epsilon_for(sigma, STEP_BUDGET, DELTA) == EPSILON_LADDER[i]`, EXACT, NO TOLERANCE.

    Never `pytest.approx`. The pin was transcribed at full double precision from what the
    accountant returned, so an approximate comparison here would accept exactly the hand-edited
    digit this assertion exists to refuse. `T` and `delta` are read from their own pins rather than
    spelled, so this correspondence is between the module's constants and the accountant, not
    between two hand-typed numbers.
    """
    sigma = mitigation_budget.SIGMA_LADDER[index]
    pinned = mitigation_budget.EPSILON_LADDER[index]
    live = epsilon_for(sigma, mitigation_budget.STEP_BUDGET, mitigation_unit.DELTA)

    assert pinned == live, (
        f"rung {index} pins sigma {sigma!r} against epsilon {pinned!r}, but "
        f"epsilon_for({sigma!r}, {mitigation_budget.STEP_BUDGET!r}, {mitigation_unit.DELTA!r}) "
        f"returns {live!r}. Exact `==`: a rung whose epsilon does not re-derive is a published "
        "privacy figure that no longer describes the mechanism it is filed under"
    )
    assert math.isfinite(pinned) and pinned > 0.0, (
        f"rung {index}'s epsilon is {pinned!r} — a non-finite or non-positive epsilon is not a "
        "privacy guarantee"
    )


def test_the_control_rung_carries_no_epsilon():
    """`EPSILON_LADDER[0] is None`, PROVED FORCED THREE WAYS rather than chosen.

    `epsilon_for(0.0, ...)` returns `math.inf`; `inf` is not `ast.literal_eval`-able so the
    literal-only budget module could not hold it even if it wanted to; and D-29 states that the
    sigma=0 control carries no epsilon. All three are asserted, so the `None` cannot be read as a
    placeholder somebody forgot to fill in.
    """
    assert mitigation_budget.EPSILON_LADDER[0] is None, (
        f"`EPSILON_LADDER[0]` is {mitigation_budget.EPSILON_LADDER[0]!r}. The sigma=0 control "
        "carries NO epsilon (D-29), and a number there would be a fabricated privacy figure on the "
        "one point that has none"
    )

    at_zero = epsilon_for(0.0, mitigation_budget.STEP_BUDGET, mitigation_unit.DELTA)
    assert at_zero == math.inf, (
        f"epsilon_for(0.0, ...) returns {at_zero!r}, not inf. The first reason the control's slot "
        "is None has changed, so the other two are carrying the claim alone"
    )

    with pytest.raises(ValueError):
        ast.literal_eval(ast.parse("PLACEHOLDER = inf").body[0].value)

    assert None in mitigation_budget.EPSILON_LADDER[:1], "the control slot is not None"
    assert all(entry is not None for entry in mitigation_budget.EPSILON_LADDER[1:]), (
        f"a NOISED rung carries None: {mitigation_budget.EPSILON_LADDER!r}. Only the control has "
        "no epsilon"
    )


def test_round_number_epsilon_is_not_reachable_by_inversion():
    """THE MEASURED FACT THAT DECIDED THE LADDER'S FORM, ASSERTED RATHER THAN NOTED.

    `sigma_for` is a NUMERICAL inverse. Its round trip is exact to about one ULP and NOT exact, so
    a ladder pinned at round-number epsilon TARGETS would be unsatisfiable under the `==` above.
    Round sigma with the full-precision epsilon transcribed beside it is the only ==-satisfiable
    formulation, and the reason belongs in the suite rather than in a research note that nothing
    re-runs.
    """
    steps = mitigation_budget.STEP_BUDGET
    delta = mitigation_unit.DELTA
    assert steps == 200 and delta == 1e-05, (steps, delta)

    inverted = sigma_for(8, steps, delta)
    round_trip = epsilon_for(inverted, steps, delta)

    assert round_trip != 8, (
        f"sigma_for(8, {steps}, {delta}) = {inverted!r} now round-trips to EXACTLY 8 "
        f"({round_trip!r}). The inversion has become exact, which would make a round-number "
        "epsilon ladder satisfiable under `==` — the reason this ladder is pinned in sigma no "
        "longer holds and the choice should be re-recorded rather than left standing"
    )
    assert round_trip == pytest.approx(8), (
        f"sigma_for(8, ...) round-trips to {round_trip!r}, which is not even APPROXIMATELY 8. The "
        "inverse is broken rather than merely inexact, and every claim about the accountant here "
        "is measuring a different function than the one the ladder was built against"
    )


def test_the_ladder_is_strictly_monotone():
    """sigma strictly UP and epsilon strictly DOWN across rungs 1..15 — a transcription slip is red.

    More noise is more privacy: the two ladders must move in opposite directions at every step. A
    single mistyped digit anywhere in either tuple breaks this even when the pair still happens to
    satisfy the per-rung equality above at every OTHER index.
    """
    ladder = mitigation_budget.SIGMA_LADDER
    epsilons = mitigation_budget.EPSILON_LADDER

    assert ladder[0] < ladder[1], (
        f"the control rung {ladder[0]!r} is not below the first noised rung {ladder[1]!r}"
    )
    for index in _NOISED_RUNGS[1:]:
        assert ladder[index] > ladder[index - 1], (
            f"`SIGMA_LADDER` is not strictly increasing at rung {index}: {ladder[index - 1]!r} -> "
            f"{ladder[index]!r}"
        )
        assert epsilons[index] < epsilons[index - 1], (
            f"`EPSILON_LADDER` is not strictly decreasing at rung {index}: "
            f"{epsilons[index - 1]!r} -> {epsilons[index]!r}. More noise must buy more privacy, so "
            "an epsilon that rises with sigma is a transcription slip rather than a finding"
        )


# =================================================================================================
# ===== (b) C's RE-DERIVATION (D-24 / D-25) =====
# =================================================================================================


def test_clip_norm_re_derives_from_the_committed_measurement():
    """`CLIP_NORM` is RECOMPUTED from the record's own per-record values under its own rule.

    The rule, the quantile, the capacity and the index all come out of the record rather than out
    of this file, so the re-derivation is checked against what was RECORDED rather than against
    what this test remembers. The order statistic is taken with NO interpolation, which is what
    makes the candidate one of the measured values and therefore re-derivable by index at all.
    """
    path, record = _clip_record()
    capacity = record["clip_norm_rule_capacity"]
    quantile = record["clip_norm_rule_quantile"]

    values = record["per_record_norms"][capacity]["values"]
    assert values, f"{path} records no per-record norms for capacity {capacity!r}"
    assert len(values) == record["per_record_norms"][capacity]["n_records"], (
        f"{path} records {len(values)} values against n_records "
        f"{record['per_record_norms'][capacity]['n_records']} — the denominator the quantile is "
        "taken over disagrees with the sample it is taken from"
    )

    ordered = sorted(values)
    index = math.ceil(quantile * len(ordered)) - 1
    assert index == record["clip_norm_rule_index"], (
        f"the recorded rule index is {record['clip_norm_rule_index']!r} but quantile "
        f"{quantile!r} over {len(ordered)} values re-derives {index}"
    )

    re_derived = ordered[index]
    assert mitigation_budget.CLIP_NORM == re_derived, (
        f"`CLIP_NORM` is {mitigation_budget.CLIP_NORM!r} but the order statistic at index {index} "
        f"of {path}'s {capacity!r} values is {re_derived!r}. Exact `==`: a clip constant that does "
        "not re-derive from the distribution it cites sizes the noise (std = sigma * C) by "
        "preference wearing a measurement's clothes"
    )
    assert mitigation_budget.CLIP_NORM == record["clip_norm_candidate"], (
        f"`CLIP_NORM` {mitigation_budget.CLIP_NORM!r} disagrees with the record's own "
        f"clip_norm_candidate {record['clip_norm_candidate']!r}"
    )
    assert re_derived in values, (
        "the derived candidate is not one of the MEASURED values — the order statistic has "
        "acquired an interpolation, and an interpolated candidate cannot be re-derived by index"
    )


def test_the_control_clip_norm_matches_phase_23():
    """`CONTROL_CLIP_NORM` equals the sigma=0 record's OWN `clip_norm`, read live every run.

    D-01's reproduction of the control is BIT-LEVEL. The control must reuse Phase 23's bound
    unchanged or the reproduction is not bit-level, so the agreement is re-read from the record
    rather than pinned twice.
    """
    path, record = _control_record()

    assert mitigation_budget.CONTROL_CLIP_NORM == float(record["clip_norm"]), (
        f"`CONTROL_CLIP_NORM` is {mitigation_budget.CONTROL_CLIP_NORM!r} but {path} ran at "
        f"{record['clip_norm']!r}. D-01's reproduction of the control is bit-level and a different "
        "bound is a different mechanism"
    )
    assert record["clip_bind_count"] == 0, (
        f"{path} records clip_bind_count {record['clip_bind_count']!r}, not 0. The control's bound "
        "is chosen precisely because it is PROVEN not to bind, and a binding control would make "
        "its recorded norms a picture of the bound"
    )


def test_the_two_clip_constants_are_distinct_and_both_pinned():
    """TWO constants, not one, and the reason is that no single value satisfies both requirements.

    The CONTROL needs the non-binding 1e6 for D-01's bit-level reproduction; the NOISED points need
    the calibrated value, because at C = 1.0 the committed counter-example bound on 12800 of 12800
    records and at fixed sigma that is pure clipping bias bought for nothing. 25-CONTEXT resolves
    the pair NOWHERE, which is why both are pinned here with their scopes named.
    """
    calibrated = mitigation_budget.CLIP_NORM
    control = mitigation_budget.CONTROL_CLIP_NORM

    assert isinstance(calibrated, float) and isinstance(control, float), (calibrated, control)
    assert calibrated != control, (
        f"the two clip constants are the same value {calibrated!r}. One of the two requirements "
        "they exist to satisfy is then unmet, and which one is unknowable from the pin"
    )
    assert calibrated < control, (
        f"the calibrated bound {calibrated!r} is not below the control's deliberately non-binding "
        f"{control!r} — the noised points would clip less than the control that is defined as "
        "clipping nothing"
    )

    for name in ("CLIP_NORM", "CONTROL_CLIP_NORM"):
        provenance = getattr(mitigation_budget, name + "_PROVENANCE")
        assert provenance["governs"], f"{name}_PROVENANCE states no scope"
        assert "sized_against" not in provenance, (
            f"{name}_PROVENANCE carries `sized_against`, but NO throughput figure participates in "
            "it — the field would be FALSE, and a provenance field that lies is worse than one "
            "that is absent"
        )


# =================================================================================================
# ===== (c) ONE LADDER AT BOTH CAPACITIES (D-17 / D-22) =====
# =================================================================================================


def test_one_ladder_serves_both_capacities():
    """EXACTLY ONE `SIGMA_LADDER` symbol, and no per-capacity variant anywhere in the module.

    D-17 is forced twice over. `mitigation_gate.capacity_comparison` compares the two legs'
    mechanisms under EXACT equality on every `MECHANISM_KEYS` entry, of which sigma is one, so
    reusing one set of literals satisfies that check BY CONSTRUCTION rather than by two ladders
    happening to agree; and this module is literal-only, so a per-capacity ladder derived from a
    shared one could not be written here at all.

    The behavioural half is the second block: the sigma coordinates `phase25_record` builds for
    `dp_n8` and for `dp_n64` are the SAME sequence, recovered by parsing the keys back.
    """
    ladder_names = sorted(name for name in dir(mitigation_budget) if "LADDER" in name)
    assert ladder_names == [
        "EPSILON_LADDER",
        "EPSILON_LADDER_PROVENANCE",
        "SIGMA_LADDER",
        "SIGMA_LADDER_PROVENANCE",
    ], (
        f"`mitigation_budget` exposes ladder names {ladder_names}. A second ladder is a second "
        "noise axis, and `capacity_comparison`'s exact-equality check on sigma would then hold "
        "only if two independently edited tuples happened to agree"
    )

    capacity_tokens = ("n8", "n64", "N8", "N64")
    suspect = [
        name
        for name in dir(mitigation_budget)
        if ("LADDER" in name or "CLIP_NORM" in name)
        and any(token in name for token in capacity_tokens)
    ]
    assert not suspect, (
        f"`mitigation_budget` carries per-capacity noise-axis names {suspect} — the single-ladder "
        "guarantee D-17 rests on is gone"
    )
    assert mitigation_budget.SIGMA_LADDER_PROVENANCE["reused_at_both_capacities"] is True

    keys = phase25_record.ORDERED_POINT_KEYS()
    per_capacity = {}
    for key in keys:
        arm, axis, value = phase25_record.parse_point_key(key)
        if axis == "sigma":
            per_capacity.setdefault(arm, []).append(value)
    assert sorted(per_capacity) == ["dp_n64", "dp_n8"], sorted(per_capacity)
    assert per_capacity["dp_n8"] == per_capacity["dp_n64"], (
        f"the two DP legs sweep DIFFERENT sigma sequences: {per_capacity!r}. One ladder is "
        "supposed to serve both"
    )


def test_the_adversarial_grid_is_identical_at_both_capacities():
    """D-22: ONE `ADVERSARIAL_RATIO_GRID`, six points, and its `governs` says "per capacity"."""
    grid = mitigation_budget.ADVERSARIAL_RATIO_GRID

    assert isinstance(grid, tuple) and len(grid) == 6, f"`ADVERSARIAL_RATIO_GRID` is {grid!r}"
    governs = mitigation_budget.ADVERSARIAL_RATIO_GRID_PROVENANCE["governs"]
    assert "per capacity" in governs.lower(), (
        f"`ADVERSARIAL_RATIO_GRID_PROVENANCE['governs']` does not say the grid is per capacity: "
        f"{governs!r}"
    )


def test_the_total_point_count_is_forty_four():
    """44, COMPUTED FROM THE CONSTANTS rather than asserted as a literal beside them.

    D-20 keeps sigma=0 inside `SWEEP_POINTS`, so the total does not move when the control is
    counted: 16x2 DP plus 6x2 adversarial. The live key set is checked against the same arithmetic,
    so a driver that built a different number of points would be red here rather than at spend time.
    """
    total = mitigation_budget.SWEEP_POINTS * 2 + len(mitigation_budget.ADVERSARIAL_RATIO_GRID) * 2

    assert total == 44, (
        f"the constants compose to {total} sweep points, not 44. D-08 pins all 44 and does not "
        "re-open the count at the moment of spending"
    )
    keys = phase25_record.ORDERED_POINT_KEYS()
    assert len(keys) == total == len(set(keys)), (len(keys), total, len(set(keys)))


# =================================================================================================
# ===== (d) THE PROBE FED THE LADDER, AND IT WAS COMMITTED FIRST (D-18) =====
# =================================================================================================


def test_the_top_rung_matches_the_probed_anchor():
    """`SIGMA_LADDER[-1]` IS the candidate the probe confirmed — not a value chosen beside it."""
    path, probe = _probe_record()

    assert probe["anchor_confirmed"] is True, (
        f"{path} did not confirm the anchor, so the ladder's top rung is a presumption. D-18 "
        "requires the ladder to be committed only AFTER the probe confirms"
    )
    selected = probe["sigma_hi_selected"]
    assert mitigation_budget.SIGMA_LADDER[-1] == selected, (
        f"`SIGMA_LADDER` tops out at {mitigation_budget.SIGMA_LADDER[-1]!r} but {path} selected "
        f"{selected!r}. The ladder's width would then be set by something other than the "
        "measurement that was paid for"
    )
    candidates = [candidate["sigma"] for candidate in probe["sigma_hi_candidates"]]
    assert selected in candidates, (selected, candidates)
    assert probe["clip_norm_used"] == mitigation_budget.CLIP_NORM, (
        f"the anchor was probed at C {probe['clip_norm_used']!r} but the noised points will ship "
        f"at {mitigation_budget.CLIP_NORM!r}. std = sigma * C, so an anchor probed at a different "
        "C is an anchor probed at a different noise scale"
    )
    assert probe["excluded_from_point_set"] is True and probe["prefix"]
    for phrase in ("extends upward", "never shifts", "halve"):
        assert phrase in probe["RATCHET_EXTENSION_RULE"], phrase


def test_the_ratchet_rule_is_committed_before_the_ladder():
    """D-18's ORDER, ASSERTED FROM `git log` RATHER THAN TRUSTED.

    Committing the ladder before the probe would be choosing the answer's resolution in advance,
    and a plan can claim an order it did not keep. The probe record's EARLIEST add must be a strict
    ancestor of the commit that first introduced `SIGMA_LADDER` into the budget module.
    `--diff-filter=A` with `[-1]` takes the earliest add for the same reason the ancestry guard
    does: a later re-add cannot launder an earlier one.
    """
    probe_rel = phase25_sigma_hi.SIGMA_HI_RECORD.relative_to(_ROOT).as_posix()
    budget_rel = pathlib.Path(mitigation_budget.__file__).resolve().relative_to(_ROOT).as_posix()

    adds = _git("log", "--diff-filter=A", "--format=%H", "--", probe_rel).split()
    assert adds, f"{probe_rel} was never added in this history — the probe record is untracked"
    probe_commit = adds[-1]

    pins = _git("log", "-S", "SIGMA_LADDER", "--format=%H", "--", budget_rel).split()
    assert pins, f"no commit to {budget_rel} ever introduced SIGMA_LADDER"
    pin_commit = pins[-1]

    assert probe_commit != pin_commit, (
        f"the probe record and the ladder pin landed in the SAME commit {probe_commit}. D-18 "
        "requires the ladder to be committed only after the probe confirms the anchor, and one "
        "commit cannot be after itself"
    )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", probe_commit, pin_commit],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert ancestry.returncode == 0, (
        f"{probe_rel} landed at {probe_commit}, which is NOT an ancestor of the ladder pin at "
        f"{pin_commit}. The ladder was committed before, or independently of, the probe that was "
        "supposed to confirm its top rung"
    )


def test_every_pin_cites_a_record_whose_digest_is_live():
    """Each `_PROVENANCE` sibling names a record, and that record hashes to the pinned digest.

    The freshness discipline `tests/test_phase24_grid.py` established, in this register: a pin
    derived from an artifact that has since changed is a number with a stale citation beside it.
    """
    for name in _REGISTERED:
        provenance = getattr(mitigation_budget, name + "_PROVENANCE")
        relative = provenance["record"]
        path = _ROOT / relative
        assert path.exists(), f"{name}_PROVENANCE cites {relative}, which does not exist"
        live = hashlib.sha256(path.read_bytes()).hexdigest()
        assert provenance["record_sha256"] == live, (
            f"{name}_PROVENANCE pins {relative} at sha256 {provenance['record_sha256']!r} but it "
            f"hashes to {live!r} today — the artifact this pin was derived from is not the "
            "artifact on disk"
        )
        assert provenance["derivation"] and provenance["governs"], name


# =================================================================================================
# ===== (e) THE ATTRIBUTE-ACCESS REQUIREMENT, SELF-ENFORCED =====
# =================================================================================================


def _attribute_names(source):
    """`{node.attr for node in ast.walk(...) if isinstance(node, ast.Attribute)}` — the register's
    OWN walk, restated so a drift is caught here rather than as a confusing register failure."""
    return {node.attr for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Attribute)}


def test_this_file_reads_every_registered_constant_by_attribute_access():
    """The exact walk `test_z_was_sized_against_the_ceiling` performs, run over THIS file.

    That test excuses these four names from the budget module's completeness register only while
    this file reads them, and it decides "reads" by collecting `ast.Attribute.attr`. Mirroring the
    walk here turns a future drift into a failure that names the cause instead of a register
    failure two files away that names a constant nobody touched.
    """
    read = _attribute_names(_THIS_FILE.read_text(encoding="utf-8"))
    missing = [name for name in _REGISTERED if name not in read]
    assert not missing, (
        f"this file never reads {missing} as `mitigation_budget.NAME`, so "
        "tests/test_phase23_budget.py::test_z_was_sized_against_the_ceiling would excuse "
        "constants that have no re-derivation anywhere"
    )


def test_no_from_import_of_the_budget_module():
    """No `ast.ImportFrom` whose module is `mitigation_budget`. The trap, closed structurally.

    A `from mitigation_budget import SIGMA_LADDER` reads perfectly well and is INVISIBLE to the
    register's walk, so the register would go red naming a constant this file uses on every line.
    """
    tree = ast.parse(_THIS_FILE.read_text(encoding="utf-8"))
    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "mitigation_budget"
    ]
    assert not offenders, (
        f"this file `from`-imports the budget module at line(s) {offenders}. Bare-name uses are "
        "invisible to the register's `ast.Attribute` walk"
    )


def test_the_from_import_variant_is_invisible_to_the_register_walk(tmp_path):
    """WATCHED RED, ON A COPY: the trap is demonstrated, not merely described.

    A `tmp_path` copy of this file has one attribute access rewritten into the `from`-import
    bare-name form, and the register's own walk is re-run against it. The name vanishes from the
    walk's result — which is exactly the "never reads SIGMA_LADDER" failure the register would
    report. The real tree is never touched, and `git status --porcelain tests/` is asserted empty
    afterwards so the watching left no residue.
    """
    original = _THIS_FILE.read_text(encoding="utf-8")
    assert "SIGMA_LADDER" in _attribute_names(original)

    rewritten = original.replace("mitigation_budget.SIGMA_LADDER", "SIGMA_LADDER")
    assert rewritten != original, "no attribute access to rewrite — the demonstration is vacuous"
    copy = tmp_path / "test_phase25_grid_from_import.py"
    copy.write_text(
        "from mitigation_budget import SIGMA_LADDER  # the tidy-up this test refuses\n" + rewritten,
        encoding="utf-8",
    )

    read = _attribute_names(copy.read_text(encoding="utf-8"))
    assert "SIGMA_LADDER" not in read, (
        "the rewritten copy still exposes SIGMA_LADDER to the `ast.Attribute` walk, so the trap "
        "this test demonstrates does not exist and the docstring above is wrong"
    )
    for name in ("EPSILON_LADDER", "CLIP_NORM", "CONTROL_CLIP_NORM"):
        assert name in read, (
            f"{name} also vanished from the copy's walk — the rewrite was broader than the one "
            "attribute this demonstration is about"
        )

    assert _THIS_FILE.read_text(encoding="utf-8") == original
    residue = _git("status", "--porcelain", "tests/")
    assert residue == "", f"watching the RED must leave no residue in tests/: {residue!r}"
