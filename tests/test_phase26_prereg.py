"""Plan 26-01: the Phase-26 pre-registration, frozen by git ancestry and pinned by arithmetic.

Two ancestry guards (this module's prereg and Phase 25's, D-12), the committed rule resolving to
the control, the extension to all 15 noised dp_n8 points, the power threshold derived from the
artifact, the six hand-computed epsilon_lower rows, the named degenerate cases, the three-valued
verdict domain, and the continuations as data. The 22 MB frontier is loaded ONCE. CPU-only.
"""

import json
import pathlib
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
import mitigation_unit  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase26_prereg  # noqa: E402  (same)

from personacore.privacy import accountant  # noqa: E402

PREREG = "scripts/phase26_prereg.py"
PHASE25_PREREG = "scripts/phase25_prereg.py"
FRONTIER = "results/phase25_frontier.json"
CONTROL = "dp_n8_sigma0p000000"


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def artifact():
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))


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


def test_phase26_prereg_is_frozen_before_every_phase26_result():
    _assert_frozen_before(PREREG, _git("ls-files", phase26_prereg.ARTIFACT_GLOB).split())


def test_phase25_prereg_is_byte_identical_since_the_frontier():
    tracked = [FRONTIER] + _git("ls-files", phase26_prereg.ARTIFACT_GLOB).split()
    _assert_frozen_before(PHASE25_PREREG, tracked)
    assert not _git("diff", "--", PHASE25_PREREG)
    assert len(_git("log", "--oneline", "--", FRONTIER).splitlines()) == 1


def test_the_committed_rule_resolves_to_the_control(artifact):
    assert phase26_prereg.RULE is phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]
    for clause in (
        "restrict to n=8 points",
        "FIRST in `point_keys` order whose verdict is PASS",
        "the pre-registered null",
    ):
        assert _prose.normalized(clause) in _prose.normalized(phase26_prereg.RULE)
    assert phase26_prereg.resolve_audit_target(artifact) == CONTROL == phase26_prereg.CONTROL_KEY


def test_the_extension_is_all_fifteen_in_point_keys_order(artifact):
    keys = phase26_prereg.audited_point_keys(artifact)
    assert len(keys) == 16
    assert keys[0] == CONTROL
    assert keys == tuple(k for k in artifact["point_keys"] if k.startswith("dp_n8"))
    assert keys == tuple(k for k in phase25_record.ORDERED_POINT_KEYS() if k.startswith("dp_n8"))
    noised = phase26_prereg.noised_point_keys(artifact)
    assert noised == keys[1:] and len(noised) == 15
    assert artifact["points"][CONTROL]["epsilon"] is None
    for key in noised:
        assert isinstance(artifact["points"][key]["epsilon"], float), key


def test_the_power_threshold_is_the_smallest_audited_claim(artifact):
    threshold = phase26_prereg.power_threshold(artifact)
    assert threshold == artifact["points"]["dp_n8_sigma80p000000"]["epsilon"]
    assert threshold == pytest.approx(0.6339783761989397)
    assert threshold == accountant.epsilon_for(80.0, 200, mitigation_unit.DELTA)
    assert phase26_prereg.power_gate(2.7859, threshold)["passed"] is True
    assert phase26_prereg.power_gate(0.5, threshold)["passed"] is False
    assert phase26_prereg.power_gate(None, threshold)["passed"] is False
    assert phase26_prereg.power_gate(0.5, threshold)["sentence"] == phase26_prereg.POWER_SENTENCE


_ROWS = (
    ((790, 1008, 0, 784), (0.7617, 0.0034, 5.4003, 1.4306)),
    ((1008, 1008, 0, 784), (0.9973, 0.0034, 5.6699, 5.9196)),
    ((8, 8, 0, 56), (0.7473, 0.0461, 2.7859, 1.3283)),
    ((7, 8, 0, 56), (0.5889, 0.0461, 2.5476, 0.8416)),
    ((8, 8, 1, 56), (0.7473, 0.0762, 2.2836, 1.2962)),
    ((0, 1008, 0, 784), (0.0, 0.0034, None, -0.0035)),
)


@pytest.mark.parametrize(("counts", "expected"), _ROWS)
def test_epsilon_lower_matches_the_hand_computed_table(counts, expected):
    reading = phase26_prereg.epsilon_lower(*counts)
    tpr_lb, fpr_ub, d1, d2 = expected
    assert reading["tpr_lb"] == pytest.approx(tpr_lb, abs=1e-4)
    assert reading["fpr_ub"] == pytest.approx(fpr_ub, abs=1e-4)
    for key, value in (("direction_1", d1), ("direction_2", d2)):
        if value is None:
            assert reading[key] is None
        else:
            assert reading[key] == pytest.approx(value, abs=1e-4)
    finite = [v for v in (reading["direction_1"], reading["direction_2"]) if v is not None]
    assert reading["epsilon_lower"] == max(finite)
    assert reading["z"] == erasure_gate._Z_ONE_SIDED_95
    assert reading["delta"] == mitigation_unit.DELTA


def test_zero_members_names_direction_one_undefined():
    reading = phase26_prereg.epsilon_lower(0, 1008, 0, 784)
    assert reading["direction_1"] is None
    assert "TPR_lb <= delta" in reading["degenerate"][0]
    assert reading["epsilon_lower"] == reading["direction_2"] < 0  # NOT clipped to 0


def test_all_nonmembers_names_direction_two_undefined():
    reading = phase26_prereg.epsilon_lower(8, 8, 56, 56)
    assert reading["fpr_ub"] == 1.0
    assert reading["direction_2"] is None
    assert any("FPR_ub >= 1 - delta" in name for name in reading["degenerate"])


def test_counts_are_ints_only():
    with pytest.raises(SystemExit):
        phase26_prereg.epsilon_lower(True, 8, 0, 56)
    with pytest.raises(SystemExit):
        phase26_prereg.epsilon_lower(8.0, 8, 0, 56)


def test_auditor_ceiling_is_the_perfect_reading(artifact):
    ceiling = phase26_prereg.auditor_ceiling(8, 56)
    assert ceiling == pytest.approx(2.7859, abs=1e-4)
    assert phase26_prereg.auditor_ceiling(8, 50) < ceiling  # exclusions lower the ceiling
    reachable = [
        k
        for k in phase26_prereg.noised_point_keys(artifact)
        if artifact["points"][k]["epsilon"] < ceiling
    ]
    assert reachable == [f"dp_n8_sigma{s}p000000" for s in (24, 32, 50, 80)]


def test_verdict_domain_is_three_valued_and_one_sided():
    assert phase26_prereg.VERDICTS == ("BROKEN", "CONSISTENT", "INCONCLUSIVE")
    assert phase26_prereg.verdict(3.0, 2.4, power_passed=True) == "BROKEN"
    assert phase26_prereg.verdict(1.0, 2.4, power_passed=True) == "CONSISTENT"
    assert phase26_prereg.verdict(1.0, 2.4, power_passed=False) == "INCONCLUSIVE"
    assert phase26_prereg.verdict(None, 2.4, power_passed=False) == "INCONCLUSIVE"

    reading = phase26_prereg.epsilon_lower(8, 8, 0, 56)
    power = phase26_prereg.power_gate(2.7859, 0.634)
    broken = phase26_prereg.point_verdict(
        reading, 2.3957449097512216, power=power, auditor_ceiling=2.7859
    )
    assert broken["verdict"] == "BROKEN"
    joined = " | ".join(broken["reasons"])
    for needle in ("8/8", "0/56", "TPR_lb", "FPR_ub", "epsilon_lower", "Bonferroni"):
        assert needle in joined, needle

    consistent = phase26_prereg.point_verdict(
        reading, 519.6981942303134, power=power, auditor_ceiling=2.7859
    )
    assert consistent["verdict"] == "CONSISTENT"
    assert any(
        _prose.normalized("epsilon_upper >= auditor_ceiling: this comparison could not have failed")
        in _prose.normalized(reason)
        for reason in consistent["reasons"]
    )

    failed = phase26_prereg.power_gate(0.5, 0.634)
    inconclusive = phase26_prereg.point_verdict(
        reading, 519.6981942303134, power=failed, auditor_ceiling=2.7859
    )
    assert inconclusive["verdict"] == "INCONCLUSIVE"
    assert any(phase26_prereg.POWER_SENTENCE in reason for reason in inconclusive["reasons"])


def test_the_continuations_are_data():
    assert phase26_prereg.SUPERSEDES == (
        "phase25_prereg.CANARY_RESERVATIONS['audit_target_rule']",
        "phase21_filler.GUESSABILITY_WAIVER",
    )
    waiver = phase26_prereg.WAIVER_CONTINUATION
    assert waiver["supersedes"] == "phase21_filler.GUESSABILITY_WAIVER"
    assert waiver["why"] and waiver["committed"] == phase26_prereg.COMMITTED
    import phase21_filler  # inside the test: it imports phase14_factset at module scope

    assert "Filler is never scored" in _prose.normalized(phase21_filler.GUESSABILITY_WAIVER)
    assert "DELIBERATELY NOT RUN" in phase21_filler.GUESSABILITY_WAIVER  # unchanged, superseded

    assert phase26_prereg.DECIDING_TIER == "taught"
    assert phase26_prereg.EXCLUSION_SCOPE == "either"
    assert phase26_prereg.SIDECARS_AT_COMMIT == 0
    assert phase26_prereg.Z is erasure_gate._Z_ONE_SIDED_95
    assert phase26_prereg.DELTA == mitigation_unit.DELTA
    assert phase26_prereg.UNIT == mitigation_unit.PRIVACY_UNIT

    assert phase26_prereg.SUPERSEDES_OBLIGATION == "phase25_prereg.PUBLICATION_OBLIGATION"
    continuation = phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION
    for entry in continuation:
        assert isinstance(entry, tuple) and len(entry) == 2
        assert all(isinstance(part, str) and part for part in entry)
    assert continuation[-1][0] == "<artifact absent>"
    original = {path for path, _ in phase25_prereg.PUBLICATION_OBLIGATION}
    assert not original & {path for path, _ in continuation}
