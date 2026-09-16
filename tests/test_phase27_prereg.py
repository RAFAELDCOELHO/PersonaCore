"""Plan 27-01: the Phase-27 pre-registration, frozen by ancestry and re-derived from the frontier.

The ancestry guard, the frontier pinned both ways, the admission gate's domain on forged copies,
the 44-verdict route tripwire, the tally and (a)/(b)/(c) re-derivations, X by call, the pinned
baselines against their source records, the Z-rule table, the band, the recovery gate's signature,
K and its promotion, and the attacker corpus re-rendered. The 22 MB frontier is loaded ONCE; every
forgery is a ``copy.deepcopy`` of it, never a write to the file. CPU-only.
"""

import ast
import collections
import copy
import hashlib
import inspect
import json
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import _prose  # noqa: E402  (scripts/ is not a package)
import erasure_gate  # noqa: E402  (same)
import mitigation_budget  # noqa: E402  (same)
import mitigation_gate  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase23_prereg  # noqa: E402  (same)
import phase24_adversarial  # noqa: E402  (same)
import phase25_condition_c  # noqa: E402  (same)
import phase25_promotion as promotion  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same)

PREREG = "scripts/phase27_prereg.py"
FRONTIER = "results/phase25_frontier.json"
RECORD = "results/phase27_admission.json"
_PIN = set(promotion.PIN_KWARGS)

_ADAPTERS_ON_DISK = all(
    (_ROOT / entry["path"]).exists() for entry in phase27_prereg.PINNED_BASELINES.values()
)
needs_adapters = pytest.mark.skipif(
    not _ADAPTERS_ON_DISK,
    reason="the seven pinned adapters live under the gitignored checkpoints/ on the sweep host",
)


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def artifact():
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))


# =================================================================================================
# (1) FROZEN BEFORE EVERY RESULT, AND THE FRONTIER PINNED BOTH WAYS (D-04, D-06).
# =================================================================================================


def _assert_frozen_before(prereg_artifact, tracked):
    """The Phase-18 mould: every commit touching `prereg_artifact` is a STRICT ancestor of the
    earliest add of every path in `tracked`; honest with zero tracked paths."""
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )
    prereg_commits = _git("log", "--format=%H", "--", prereg_artifact).split()
    assert prereg_commits, f"{prereg_artifact} has no commits — green and blind"

    checked = 0
    for artifact in tracked:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:
            assert prereg != first_add, (
                f"{prereg_artifact} and {artifact} were committed in the SAME commit {prereg} — "
                "the pre-registration must land STRICTLY BEFORE the artifact it pins, or it is "
                "not a pre-registration at all. `git merge-base --is-ancestor X X` exits 0, so "
                "the ancestry check below cannot see this on its own."
            )
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked), (
        f"checked {checked} pairs but {len(prereg_commits)} pre-registration commit(s) x "
        f"{len(tracked)} tracked artifact(s) is {len(prereg_commits) * len(tracked)}"
    )
    assert bool(checked) == bool(tracked), (
        f"checked {checked} pair(s) against {len(tracked)} tracked artifact(s) — those disagree"
    )


def test_phase27_prereg_is_frozen_before_every_phase27_result():
    _assert_frozen_before(PREREG, _git("ls-files", phase27_prereg.ARTIFACT_GLOB).split())


def test_the_record_is_pinned_to_the_frontier_both_ways():
    tracked = _git("ls-files", RECORD)
    if (_ROOT / RECORD).exists():
        blob = json.loads((_ROOT / RECORD).read_text(encoding="utf-8"))
        frontier_bytes = (_ROOT / FRONTIER).read_bytes()
        assert blob["frontier_sha256"] == hashlib.sha256(frontier_bytes).hexdigest()
        assert blob["frontier_bytes"] == (_ROOT / FRONTIER).stat().st_size
        added = _git("log", "--diff-filter=A", "--format=%H", "--", RECORD)
        assert bool(tracked) == bool(added)
    else:
        assert not tracked, f"{RECORD} is tracked but absent from the working tree"
    # BOTH states: a re-emitted frontier reddens Phase 27 by construction (T-27-03).
    assert len(_git("log", "--oneline", "--", FRONTIER).splitlines()) == 1


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase27_prereg; "
        "print('torch' in sys.modules, 'teach_persona' in sys.modules, "
        "'phase18_extraction' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False", "False", "False"], out.stdout


# =================================================================================================
# (2) BY REFERENCE, AND THE TORCH-SIDE ORIGINALS (D-12, D-21, D-25, D-27; RESEARCH M2).
# =================================================================================================


def test_constants_are_by_reference():
    p = phase27_prereg
    assert p.MARGIN_K is erasure_gate.MARGIN_K
    assert p.CURVE_K is mitigation_budget.CURVE_K
    assert p.FULL_K is mitigation_budget.FULL_FIDELITY_K
    assert p.F_Y is mitigation_gate.F_Y
    assert p.V4_VERDICTS is mitigation_gate.V4_VERDICTS
    assert p.NEVER_TAUGHT_ARM is mitigation_gate.NEVER_TAUGHT_ARM
    assert p.GATED_TIER is phase25_record.GATED_TIER
    assert p.ATTACK_FAMILIES is phase25_record.ATTACK_FAMILIES
    assert p.HELD_OUT_FAMILY == phase24_adversarial.HELD_OUT_FAMILY == "A2"  # spelled ONCE, here
    assert p.TRAINED_FAMILIES is phase24_adversarial.TRAINED_FAMILIES
    assert p.HELD_OUT_FAMILY not in p.TRAINED_FAMILIES
    assert p.FRONTIER_RECORD is phase25_record.FRONTIER_RECORD
    assert p.VERDICTS == ("ADMITTED", "MOOT", "INCONCLUSIVE")
    assert p.RECOVERY_VERDICTS is mitigation_gate.V4_VERDICTS
    assert p.RUNGS == tuple(range(50, 401, 50))
    assert p.RELEARN_CAP == 400 == 2 * p.MAX_STEPS
    assert p.ARTIFACT_GLOB == "results/phase27_*" and p.RECORDS_AT_COMMIT == 0


def test_pinned_seeds_equal_seed_ladder():
    import phase18_extraction as x18  # torch at import — inside the test only
    import phase23_run
    import teach_persona as tp

    p = phase27_prereg
    assert p.FRESH_SEEDS == phase23_run.SEED_LADDER
    assert p.FRESH_SEEDS[p.POOLED_SEED_INDEX] == p.DESIGNATED_SEED
    assert p.MAX_STEPS == tp.MAX_STEPS
    assert p.CHECKPOINT_INTERVAL == tp.CHECKPOINT_INTERVAL
    assert p.DESIGNATED_SEED == tp.SEED
    assert p.FULL_K == x18.K
    assert p.GATED_TIER == x18.GATED_TIER
    assert p.ATTACK_FAMILIES == x18.ATTACK_FAMILIES


# =================================================================================================
# (3) THE ADMISSION GATE AND ITS DOMAIN (D-01, D-02, D-03, D-22).
# =================================================================================================


def _forge(artifact, flips):
    """A deep copy with verdict strings flipped and BOTH tallies moved with them — a CONSISTENT
    forgery, so the only thing that changed is the verdict under test. Legs come from the
    frontier's own ``verdict.leg`` label, never from the module under test."""
    forged = copy.deepcopy(artifact)
    for key, new in flips.items():
        point = forged["points"][key]
        old = phase27_prereg.point_verdict_string(point)
        point["verdict"]["verdict"] = new
        leg_tally = forged["verdicts"]["tallies_by_leg"][point["verdict"]["leg"]]
        for tally in (forged["verdicts"]["tallies"], leg_tally):
            tally[old] -= 1
            tally[new] += 1
    return forged


def test_the_gate_reads_moot_on_the_committed_frontier(artifact):
    verdict, reasons = phase27_prereg.relearning_is_worth_attempting(artifact)
    assert verdict == "MOOT", reasons
    assert any("0 of 44" in reason for reason in reasons)
    assert reasons[-1].startswith("MOOT:") and "nothing to relearn" in reasons[-1]
    assert phase27_prereg.admitted_point_keys(artifact) == ()


def test_the_gate_admits_only_pass(artifact):
    gate = phase27_prereg.relearning_is_worth_attempting

    one = _forge(artifact, {"dp_n8_sigma0p500000": "PASS"})
    verdict, reasons = gate(one)
    assert verdict == "ADMITTED", reasons
    assert "dp_n8_sigma0p500000" in reasons[0]
    assert phase27_prereg.admitted_point_keys(one) == ("dp_n8_sigma0p500000",)

    # D-01: INCONCLUSIVE alone never admits.
    inconclusive = _forge(artifact, {"dp_n8_sigma0p500000": "INCONCLUSIVE"})
    assert gate(inconclusive)[0] == "MOOT"

    # D-22: two PASS keys set in REVERSE point_keys order come back in point_keys order.
    later, earlier = "dp_n64_sigma80p000000", "dp_n8_sigma0p700000"
    assert artifact["point_keys"].index(earlier) < artifact["point_keys"].index(later)
    two = _forge(artifact, {later: "PASS", earlier: "PASS"})
    assert phase27_prereg.admitted_point_keys(two) == (earlier, later)
    verdict, reasons = gate(two)
    assert verdict == "ADMITTED" and reasons[0] == f"2 PASS point(s): {[earlier, later]}"


def test_partial_or_inconsistent_frontier_is_inconclusive(artifact):
    gate = phase27_prereg.relearning_is_worth_attempting

    partial = copy.deepcopy(artifact)
    del partial["points"][partial["point_keys"].pop()]
    verdict, reasons = gate(partial)
    assert verdict == "INCONCLUSIVE" and "43" in reasons[0], reasons

    miscounted = copy.deepcopy(artifact)
    miscounted["verdicts"]["tallies"]["FAIL"] = 31
    verdict, reasons = gate(miscounted)
    assert verdict == "INCONCLUSIVE" and "'FAIL': 31" in reasons[0], reasons

    leg_miscounted = copy.deepcopy(artifact)
    leg_miscounted["verdicts"]["tallies_by_leg"]["dp_n8"]["FAIL"] = 15
    verdict, reasons = gate(leg_miscounted)
    assert verdict == "INCONCLUSIVE" and "tallies_by_leg" in reasons[0], reasons

    unknown = copy.deepcopy(artifact)
    unknown["points"]["dp_n8_sigma0p500000"]["verdict"]["verdict"] = "MAYBE"
    verdict, reasons = gate(unknown)
    assert verdict == "INCONCLUSIVE" and "MAYBE" in reasons[0], reasons

    assert gate(None)[0] == "INCONCLUSIVE"

    # A bare None (no early_return_reason) is outside the domain — it is not REFUSED.
    bare = copy.deepcopy(artifact)
    bare["points"]["adv_n64_ratio0p000000"]["verdict"]["early_return_reason"] = ""
    verdict, reasons = gate(bare)
    assert verdict == "INCONCLUSIVE" and "adv_n64_ratio0p000000" in reasons[0], reasons


def test_the_tally_re_derives_from_the_entries(artifact):
    points = artifact["points"]
    strings = {k: phase27_prereg.point_verdict_string(points[k]) for k in artifact["point_keys"]}
    # Counter against Counter: a Counter compared with a plain dict carrying `PASS: 0` falls back
    # to dict equality, where the absent zero key makes it unequal.
    assert collections.Counter(strings.values()) == collections.Counter(
        artifact["verdicts"]["tallies"]
    )
    for leg, tally in artifact["verdicts"]["tallies_by_leg"].items():
        on_leg = [s for k, s in strings.items() if points[k]["verdict"]["leg"] == leg]
        assert collections.Counter(on_leg) == collections.Counter(tally), leg
    refused = [k for k, s in strings.items() if s == phase27_prereg.REFUSED]
    assert len(refused) == 6 and all(k.startswith("adv_n64_") for k in refused), refused
    for key in artifact["point_keys"]:  # the key helpers agree with the frontier's own labels
        assert phase27_prereg.arm_of(key) == points[key]["verdict"]["arm"], key
        assert phase27_prereg.leg_of(key) == points[key]["verdict"]["leg"].split("_")[1], key


# The sanctioned route's kwargs — `tests/test_phase25_promotion.py:51-60`, copied verbatim.
def _pin_kwargs(entry):
    return {name: entry[name] for name in _PIN}


def _route_kwargs(entry):
    kwargs = {k: v for k, v in _pin_kwargs(entry).items() if not k.startswith("sweep_")}
    curve = entry["whole_curve_inputs"]
    kwargs.update({k: curve[k] for k in curve if k.startswith("sweep_")})
    kwargs["retention_floor_provenance"] = {
        "regime": phase20_gate_coverage.ADAPTER_REGIME,
        "seeds": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE["seeds"],
    }
    return kwargs


def test_every_frontier_verdict_re_derives_through_the_route(artifact):
    reached = refused = 0
    for key in artifact["point_keys"]:
        entry = artifact["points"][key]["verdict"]
        if entry["verdict"] is None:
            with pytest.raises(SystemExit) as exc:
                phase20_gate_coverage.corrected_point_verdict(**_route_kwargs(entry))
            assert entry["reasons"][0] == str(exc.value).strip(), key
            refused += 1
            continue
        out = phase20_gate_coverage.corrected_point_verdict(**_route_kwargs(entry))
        assert (out[0], list(out[1]), out[2]) == (
            entry["verdict"],
            entry["reasons"],
            entry["arm"],
        ), key
        reached += 1
    assert (reached, refused) == (38, 6)

    # The watched RED on a deep copy: a moved input must move the route's reading.
    moved = copy.deepcopy(artifact["points"]["dp_n8_sigma0p500000"]["verdict"])
    moved["point_taught_recall"] = 1.0
    out = phase20_gate_coverage.corrected_point_verdict(**_route_kwargs(moved))
    assert (out[0], list(out[1])) != (moved["verdict"], moved["reasons"])


# =================================================================================================
# (4) X BY CALL, THE (a)/(b)/(c) BREAKDOWN AND THE GENERATED REASONS (D-04, D-07, D-33, D-34).
# =================================================================================================


def test_x_is_the_frontier_ceiling_by_call_not_literal(artifact):
    x = artifact["verdicts"]["extraction_ceiling"]["X"]
    assert phase27_prereg.extraction_ceiling_x(artifact) == x
    source = (_ROOT / PREREG).read_text(encoding="utf-8")
    floats = [
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, float)
    ]
    assert not [value for value in floats if f"{value:.6f}" == f"{x:.6f}"], floats
    assert "mitigation_gate.extraction_ceiling(" in source

    # The two controls must read ONE floor: a disagreement is refused, not averaged.
    n8, n64 = (phase27_prereg.CONTROL_KEYS[leg] for leg in ("n8", "n64"))
    split = {
        n8: {"verdict": artifact["points"][n8]["verdict"]},
        n64: {"verdict": copy.deepcopy(artifact["points"][n64]["verdict"])},
    }
    split[n64]["verdict"]["control_extraction_successes"] = 1
    with pytest.raises(SystemExit):
        phase27_prereg.extraction_ceiling_x({"points": split})


_ROW_FIELDS = ("point_key", "verdict", "cleared_a", "cleared_b", "cleared_c", "refused")


def _derived_rows(artifact):
    rows = []
    for key in artifact["point_keys"]:
        point = artifact["points"][key]
        a, b, c = phase27_prereg.cleared_abc(point["verdict"])
        verdict = phase27_prereg.point_verdict_string(point)
        rows.append(
            {
                "point_key": key,
                "verdict": verdict,
                "cleared_a": a,
                "cleared_b": b,
                "cleared_c": c,
                "refused": verdict == phase27_prereg.REFUSED,
            }
        )
    return rows


def _projected(rows):
    return [{field: row[field] for field in _ROW_FIELDS} for row in rows]


def test_cleared_abc_re_derive_on_every_row(artifact):
    derived = _derived_rows(artifact)
    reached = [row for row in derived if not row["refused"]]
    assert len(reached) == 38
    assert [sum(row[f"cleared_{c}"] for row in reached) for c in "abc"] == [30, 4, 1]
    refused = [row for row in derived if row["refused"]]
    assert len(refused) == 6
    assert all((r["cleared_a"], r["cleared_b"], r["cleared_c"]) == (None,) * 3 for r in refused)

    counts = phase27_prereg.cleared_counts(artifact)
    assert {k: counts[k] for k in ("a", "b", "c", "reached", "refused")} == {
        "a": 30,
        "b": 4,
        "c": 1,
        "reached": 38,
        "refused": 6,
    }
    assert counts["by_leg"] == {
        "dp_n8": {"a": 15, "b": 1, "c": 1},
        "dp_n64": {"a": 15, "b": 1, "c": 0},
        "adv_n8": {"a": 0, "b": 2, "c": 0},
        "adv_n64": {"a": 0, "b": 0, "c": 0},
    }

    # Both-state: the committed record's rows when it exists, else the re-derivation stands in.
    tracked = _git("ls-files", RECORD)
    if (_ROOT / RECORD).exists():
        rows = json.loads((_ROOT / RECORD).read_text(encoding="utf-8"))["rows"]
    else:
        assert not tracked, f"{RECORD} is tracked but absent from the working tree"
        rows = copy.deepcopy(derived)
    assert _projected(rows) == derived

    # The watched RED on a deep copy: one flipped cleared_a is seen.
    flipped = copy.deepcopy(rows)
    flipped[1]["cleared_a"] = not flipped[1]["cleared_a"]
    assert _projected(flipped) != derived


def test_moot_reasons_are_generated_from_counts(artifact):
    verdict, reasons = phase27_prereg.relearning_is_worth_attempting(artifact)
    assert verdict == "MOOT"
    counts = phase27_prereg.cleared_counts(artifact)
    by_leg = artifact["verdicts"]["tallies_by_leg"]
    assert [reason.split(":")[0] for reason in reasons[1 : 1 + len(by_leg)]] == list(by_leg)
    for leg, tally in by_leg.items():
        line = next(reason for reason in reasons if reason.startswith(f"{leg}:"))
        for name, n in tally.items():
            assert re.search(rf"\b{name} {n}\b", line), (leg, name, n, line)
        cleared = counts["by_leg"][leg]
        assert f"(a) {cleared['a']} / (b) {cleared['b']} / (c) {cleared['c']}" in line, line
    total = next(reason for reason in reasons if reason.startswith("cleared "))
    assert "(a) 30 / (b) 4 / (c) 1" in total and "6 REFUSED" in total, total

    stored = {
        _prose.normalized(reason)
        for key in artifact["point_keys"]
        for reason in artifact["points"][key]["verdict"]["reasons"]
    }
    assert not stored & {_prose.normalized(reason) for reason in reasons}


# =================================================================================================
# (5) THE PINNED BASELINES (D-09, D-12, T-27-05).
# =================================================================================================


def test_baselines_are_pinned_from_the_records(artifact):
    source = "results/phase23_never_taught_training.json"
    record = json.loads((_ROOT / source).read_text(encoding="utf-8"))
    pins = phase27_prereg.PINNED_BASELINES
    for adapter in record["adapters"]:
        pin = pins[f"never_taught_{adapter['seed']}"]
        assert (pin["path"], pin["sha256"], pin["seed"]) == (
            adapter["path"],
            adapter["sha256"],
            adapter["seed"],
        )
        assert pin["source"] == source and pin["arm"] == mitigation_gate.NEVER_TAUGHT_ARM
    assert phase27_prereg.FRESH_SEEDS == tuple(record["seeds"])
    assert len(record["adapters"]) == len(phase27_prereg.FRESH_SEEDS)

    for leg in phase27_prereg.LEGS:
        pin = pins[f"control_{leg}"]
        assert pin["point_key"] == phase27_prereg.CONTROL_KEYS[leg]
        point = artifact["points"][pin["point_key"]]
        assert pin["sha256"] == point["adapter_sha256"]
        assert pin["path"] == point["adapter_path"]
        assert pin["seed"] == point["seed"] == 1337
        point_record = json.loads((_ROOT / pin["source"]).read_text(encoding="utf-8"))
        assert (point_record["adapter_sha256"], point_record["adapter_path"]) == (
            pin["sha256"],
            pin["path"],
        )
    assert phase27_prereg.BASELINE_KEYS == tuple(pins) and len(phase27_prereg.BASELINE_KEYS) == 7


@needs_adapters
def test_pinned_adapters_hash_on_host():
    for key, pin in phase27_prereg.PINNED_BASELINES.items():
        digest = hashlib.sha256((_ROOT / pin["path"]).read_bytes()).hexdigest()
        assert digest == pin["sha256"], key


def test_gate_baseline_is_required_and_pinned(artifact):
    gate = phase27_prereg.recovery_gate
    param = inspect.signature(gate).parameters["baseline"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty
    x = phase27_prereg.extraction_ceiling_x(artifact)
    with pytest.raises(TypeError):
        gate(recovered_successes=0, recovered_questions=416, x=x, z=100)
    with pytest.raises(SystemExit):
        gate(recovered_successes=0, recovered_questions=416, x=x, z=100, baseline="made_up")
    for key in phase27_prereg.PINNED_BASELINES:
        verdict, reasons = gate(
            recovered_successes=0, recovered_questions=416, x=x, z=100, baseline=key
        )
        assert verdict == "PASS" and "0/416" in reasons[0] and repr(key) in reasons[0]

    # Zero tolerance at 416 questions: one recovered question already exceeds X.
    verdict, _ = gate(
        recovered_successes=1, recovered_questions=416, x=x, z=100, baseline="control_n8"
    )
    assert verdict == "FAIL"
    verdict, _ = gate(
        recovered_successes=0, recovered_questions=416, x=x, z=None, baseline="never_taught_1337"
    )
    assert verdict == "INCONCLUSIVE"


def test_the_curve_cannot_reach_the_verdict():
    params = set(inspect.signature(phase27_prereg.recovery_gate).parameters)
    assert not {"curve", "band", "rungs", "cost", "fresh", "mitigated"} & params
    assert params == {"recovered_successes", "recovered_questions", "x", "z", "baseline"}


# =================================================================================================
# (6) THE BAND, K, THE Z RULE AND THE COUNTS (D-19, D-21, D-23, D-24, D-25, D-28).
# =================================================================================================


def test_band_uses_imported_margin_and_noise_floor():
    reading = phase27_prereg.band(mitigated=0.5, fresh_readings=[0.0, 0.1])
    assert reading["floor"] == phase23_prereg.noise_floor([0.0, 0.1])
    assert reading["half_width"] == erasure_gate.MARGIN_K * reading["floor"] == 0.2
    assert reading["fresh"] == 0.0 and reading["inside"] is False
    assert reading["margin_k"] is erasure_gate.MARGIN_K
    assert phase27_prereg.band(mitigated=0.15, fresh_readings=[0.0, 0.1])["inside"] is True
    assert phase27_prereg.band(mitigated=0.0, fresh_readings=[0.0] * 5)["inside"] is True
    with pytest.raises(SystemExit):
        phase27_prereg.band(mitigated=0.0, fresh_readings=[0.0])


def test_k_is_curve_k_and_promotion_is_the_gates():
    assert phase27_prereg.CURVE_K == 16 and phase27_prereg.FULL_K == 48
    assert phase27_prereg.promote_at_z("PASS", [])[0] is True
    assert phase27_prereg.promote_at_z("FAIL", [])[0] is False
    assert phase27_prereg.promote_at_z("PASS", []) == mitigation_gate.promote_to_full_fidelity(
        verdict="PASS", reasons=[], curve_k=16, full_k=48
    )
    with pytest.raises(SystemExit):
        phase27_prereg.promote_at_z("MAYBE", [])


_Z_TABLE = (
    ((50, 50), 50),
    ((100, 150), 150),
    ((400, 50), 400),
    ((None, 50), None),
    ((50, None), None),
    ((None, None), None),
)


@pytest.mark.parametrize(("clears", "expected_z"), _Z_TABLE)
def test_z_rule_table(clears, expected_z):
    fresh, control = clears
    z, reasons = phase27_prereg.z_rule(fresh_first_clear=fresh, control_first_clear=control)
    assert z == expected_z and (z is None) == (expected_z is None)
    assert f"RELEARN_CAP = {phase27_prereg.RELEARN_CAP}" in reasons[0]
    assert str(fresh) in reasons[0] and str(control) in reasons[0]

    assert phase27_prereg.first_clear([(50, 400, 1008), (100, 600, 1008)], 0.5486) == 100
    assert phase27_prereg.first_clear([(50, 0, 1008)], 0.5486) is None
    with pytest.raises(SystemExit):
        phase27_prereg.first_clear([(75, 600, 1008)], 0.5486)  # off the ladder
    with pytest.raises(SystemExit):
        phase27_prereg.first_clear([(50, 600.0, 1008)], 0.5486)  # a rate, not a count


def test_recall_threshold_reads_counts_not_rates(artifact):
    f_y = mitigation_gate.F_Y
    # F_Y * (k / n), evaluated as the frontier pin evaluates F_Y * control_taught_recall.
    assert phase27_prereg.recall_threshold(artifact, "n8") == (f_y * (790 / 1008), 790, 1008)
    assert phase27_prereg.recall_threshold(artifact, "n64") == (f_y * (87 / 1008), 87, 1008)
    for leg in phase27_prereg.LEGS:
        control = artifact["points"][phase27_prereg.CONTROL_KEYS[leg]]["verdict"]
        threshold = phase27_prereg.recall_threshold(artifact, leg)[0]
        assert threshold == f_y * control["control_taught_recall"], leg
    with pytest.raises(SystemExit):
        phase27_prereg.recall_threshold(artifact, "n16")


def test_counts_are_ints_only(artifact):
    x = phase27_prereg.extraction_ceiling_x(artifact)
    assert phase27_prereg.scored_tokens(mask_ones=7581, steps=50) == 379050
    with pytest.raises(SystemExit):
        phase27_prereg.scored_tokens(mask_ones=True, steps=1)
    with pytest.raises(SystemExit):
        phase27_prereg.scored_tokens(mask_ones=1.0, steps=1)
    for successes in (0.0, True):
        with pytest.raises(SystemExit):
            phase27_prereg.recovery_gate(
                recovered_successes=successes,
                recovered_questions=416,
                x=x,
                z=100,
                baseline="never_taught_1337",
            )


# =================================================================================================
# (7) THE ATTACKER CORPUS, RE-RENDERED (D-18, RELRN-05).
# =================================================================================================


def test_attacker_corpus_sha_re_renders(tmp_path, monkeypatch):
    import phase14_factset as fs  # teach_persona imports torch — inside the test only
    import teach_persona as tp

    p = phase27_prereg
    assert p.attacker_corpus_rows_sha256() == p.ATTACKER_CORPUS["rows_sha256"]
    assert len(p.attacker_corpus_rows()) == p.ATTACKER_CORPUS["n_rows"]

    for sub in ("data", "checkpoints", "results"):
        (tmp_path / sub).mkdir()
    monkeypatch.setattr(tp, "_REPO_ROOT", tmp_path)
    _tok, _stats, paths = tp.build_arm_bins(
        p.ATTACKER_ARM,
        fs.LOCKED_FACTS,
        fs.TAUGHT_FAMILY_IDS,
        replay_ratio=p.ATTACKER_REPLAY_RATIO,
        seed=p.DESIGNATED_SEED,
        prefix=p.ATTACKER_PREFIX,
    )
    assert paths["bin"].parent == tmp_path / "data"
    assert hashlib.sha256(paths["bin"].read_bytes()).hexdigest() == p.ATTACKER_CORPUS["bin_sha256"]
    assert not (_ROOT / "data" / f"persona_{p.ATTACKER_ARM}_train.bin").exists()
