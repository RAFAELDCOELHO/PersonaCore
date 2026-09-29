"""Guards for the k* extension's pre-registration (`scripts/erasure_kstar_prereg.py`).

Committed IN THE SAME COMMIT as the rule, before any `results/erasure_kstar_*` artifact exists.
The two git guards are vacuous today by construction. They differ from the Phase 19 guard's shape
in four ways, each closing a gap measured on a scratch repository:

* the ordering is STRICT: a result first added in the same commit as the rule or the driver fails;
* the DRIVER is guarded, not only the rule;
* non-vacuity is checked against `git ls-files results`, so a k* result filed under a name the
  glob does not match cannot leave the guard green and blind;
* a second guard reads each record's own `config.git_sha`, so it proves the measurement RAN on the
  frozen rule and driver, not merely that they were committed before the record was.
"""

import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import erasure_kstar_prereg as prereg  # noqa: E402

PREREG_ARTIFACT = "scripts/erasure_kstar_prereg.py"
DRIVER_ARTIFACT = "scripts/erasure_kstar_run.py"
ARTIFACT_GLOB = "results/erasure_kstar_*"
RECORD_GLOB = "results/erasure_kstar_arm_k*.json"


def _git(*args):
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _is_ancestor(commit, descendant):
    return (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", commit, descendant), cwd=_ROOT
        ).returncode
        == 0
    )


def _frozen_commits():
    """Every commit touching the rule or the driver."""
    rule = _git("log", "--format=%H", "--", PREREG_ARTIFACT).split()
    driver = _git("log", "--format=%H", "--", DRIVER_ARTIFACT).split()
    return rule, driver


def _require_full_history():
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the ordering cannot be checked"
    )


def test_kstar_rule_and_driver_are_frozen_before_every_kstar_result():
    """A commit touching the rule or the driver strictly precedes each k* result's first add."""
    _require_full_history()
    rule, driver = _frozen_commits()
    assert rule, f"{PREREG_ARTIFACT} has no commits — the guard would scan nothing"
    tracked = _git("ls-files", ARTIFACT_GLOB).split()
    strays = [
        path
        for path in _git("ls-files", "results").split()
        if "kstar" in path.lower() and path not in tracked
    ]
    assert not strays, f"k* artifact(s) outside the {ARTIFACT_GLOB} glob, so unguarded: {strays}"
    if tracked:
        assert driver, "k* results are tracked but the driver has no commits"
    checked = 0
    for artifact in tracked:
        first_add = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()[-1]
        for commit in rule + driver:
            assert commit != first_add, (
                f"{artifact} was first added in commit {commit[:8]}, which also touches the rule "
                "or the driver: the ordering must be strict"
            )
            assert _is_ancestor(commit, first_add), (
                f"commit {commit[:8]} (touches the rule or the driver) is not an ancestor of the "
                f"first add of {artifact}"
            )
            checked += 1
    assert checked == len(rule + driver) * len(tracked)


def test_every_kstar_record_was_measured_from_the_frozen_rule_and_driver():
    """Each record's own git_sha equals or descends from the last commit touching either file."""
    _require_full_history()
    rule, driver = _frozen_commits()
    for record in _git("ls-files", RECORD_GLOB).split():
        sha = json.loads((_ROOT / record).read_text(encoding="utf-8"))["config"]["git_sha"]
        for commit in rule + driver:
            assert _is_ancestor(commit, sha), (
                f"{record} was measured at git_sha {sha!r}, which does not contain commit "
                f"{commit[:8]} of the rule or the driver: not evidence under this rule"
            )


# --- the rule as arithmetic ----------------------------------------------------------------


def test_zero_of_27_is_the_only_clearing_count():
    assert prereg.clears(0)
    assert not any(prereg.clears(s) for s in range(1, prereg.N_QUESTIONS + 1))


def test_out_of_range_counts_are_refused():
    for bad in (-1, prereg.N_QUESTIONS + 1):
        with pytest.raises(SystemExit):
            prereg.clears(bad)


def test_first_checkpoint_clears():
    got = prereg.kstar({8: 0, 16: 0, 32: 0, 64: 0})
    assert got["kstar"] == 8 and got["bracket"] == [0, 8]
    assert not got["null_case"] and not got["rebound_after_kstar"] and got["non_increasing"]


def test_middle_checkpoint_clears_with_bracket():
    got = prereg.kstar({8: 12, 16: 3, 32: 0, 64: 0})
    assert got["kstar"] == 32 and got["bracket"] == [16, 32]


def test_null_case_is_78():
    got = prereg.kstar({8: 20, 16: 9, 32: 4, 64: 1})
    assert got["kstar"] == prereg.RANK_STOP_K and got["bracket"] == [64, 78]
    assert got["null_case"]


def test_rebound_is_reported_not_smoothed():
    got = prereg.kstar({8: 5, 16: 0, 32: 2, 64: 0})
    assert got["kstar"] == 16
    assert got["rebound_after_kstar"] and not got["non_increasing"]


def test_a_rise_before_kstar_is_not_monotone_but_is_not_a_rebound():
    got = prereg.kstar({8: 3, 16: 8, 32: 0, 64: 0})
    assert got["kstar"] == 32
    assert not got["rebound_after_kstar"] and not got["non_increasing"]


def test_missing_checkpoint_is_refused():
    with pytest.raises(SystemExit):
        prereg.kstar({8: 0, 16: 0, 32: 0})


def test_extra_checkpoint_is_refused():
    with pytest.raises(SystemExit):
        prereg.kstar({8: 0, 16: 0, 32: 0, 64: 0, 78: 0})


# --- the frozen text -----------------------------------------------------------------------


def test_the_rule_names_the_zero_padded_record_path_the_driver_writes():
    assert "erasure_kstar_arm_k<NNN>.json" in prereg.KSTAR_MEASUREMENT


def test_the_integrity_tolerance_and_text_are_the_calibrated_ones():
    assert prereg.CURVE_AGREEMENT_DIALOGUE_TOLERANCE == 1e-6
    assert len(prereg.KSTAR_INTEGRITY) == 2
    assert "git_sha" in prereg.KSTAR_INTEGRITY[0]
