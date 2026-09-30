"""The paper says the decision rule is one commit, `23a830c`, unamended. This makes it a test."""

import pathlib
import subprocess

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
GATE = "scripts/erasure_gate.py"
RULE_COMMIT = "23a830c"


def _is_unamended(hashes, prefix):
    return len(hashes) == 1 and hashes[0].startswith(prefix)


def test_one_commit_with_the_expected_prefix_is_unamended():
    assert _is_unamended(["23a830cdeadbeef"], RULE_COMMIT)


def test_a_second_commit_or_a_different_first_commit_is_not():
    assert not _is_unamended(["aaaa", "23a830c"], RULE_COMMIT)
    assert not _is_unamended(["bbbbbbb"], RULE_COMMIT)
    assert not _is_unamended([], RULE_COMMIT)


def test_the_decision_rule_has_exactly_one_commit_and_it_is_the_published_one():
    def git(*args):
        return subprocess.run(
            ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()

    assert git("rev-parse", "--is-shallow-repository") == "false", "shallow clone"
    if not (_ROOT / GATE).exists():
        pytest.skip("scripts/erasure_gate.py is not in this tree")
    hashes = git("log", "--format=%H", "--", GATE).split()
    assert _is_unamended(hashes, RULE_COMMIT), (
        f"{GATE} has {len(hashes)} commit(s): {[h[:7] for h in hashes]}; the paper says one, "
        f"{RULE_COMMIT}"
    )
    assert git("status", "--porcelain", "--", GATE) == "", f"{GATE} has uncommitted changes"
