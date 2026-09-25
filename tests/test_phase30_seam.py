"""ARECIPE-01: the train-time replay seam reaches the adversarial recipe, and nothing else moves.

D-03. The ``train()`` kwargs that ``teach_persona.train_arm`` hands ``dp_n8``, ``dp_n64``,
``adv_n8`` and ``adv_n64`` were captured into ``tests/fixtures/phase30_train_kwargs_presplit.json``
BEFORE the ``is_dp`` gate was split, in a commit that is a strict ancestor of the first commit
writing ``gets_replay`` into ``scripts/teach_persona.py``. "Byte-unchanged" is therefore measured
against the old code, not asserted about it.

D-04. The replay count the ``advr_*`` arms draw is MEASURED through ``train()``'s ``on_draw`` hook,
per step, and compared with ``phase29_prereg.replay_windows(n)``.

Every training run in this file goes through ``_train``, the single call to the driver. CPU-only,
everything under ``tmp_path``; nothing writes into ``data/`` or ``results/``.
"""

import dataclasses
import json
import pathlib
import subprocess
import sys

import pytest
import torch

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "tests"))

import mitigation_budget as mb  # noqa: E402  (scripts/ is not a package)
import phase14_factset as fs  # noqa: E402
import teach_persona as tp  # noqa: E402

from test_phase22_wiring import _FIXTURE_CLIP, _FIXTURE_SIGMA, _e2e_env  # noqa: E402

_PREFIX = "phase30_probe"
FIXTURE = _ROOT / "tests/fixtures/phase30_train_kwargs_presplit.json"
_PRESPLIT_ARMS = ("dp_n8", "dp_n64", "adv_n8", "adv_n64")


def _ratio_for(arm):
    """Adversarial arms train at the grid's top ratio; every other arm at the control ratio."""
    return mb.ADVERSARIAL_RATIO_GRID[-1] if arm in tp.ADV_ARMS else mb.ADVERSARIAL_RATIO_GRID[0]


def _train(arm):
    """The ONE call to the driver in this file (registered in test_phase23_resume)."""
    facts, sp, rr = tp.arm_spec(arm)
    dp = dict(dp_sigma=_FIXTURE_SIGMA, dp_clip_norm=_FIXTURE_CLIP) if arm in tp.DP_ARMS else {}
    return tp.train_arm(
        arm,
        facts=facts,
        family_ids=fs.TAUGHT_FAMILY_IDS,
        second_person=sp,
        replay_ratio=rr,
        adversarial_ratio=_ratio_for(arm),
        prefix=_PREFIX,
        **dp,
    )


class _Captured(Exception):
    pass


def _normalise(value, root, key):
    """JSON-safe, host-independent rendering of one kwarg. Unknown types refuse, never drop."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, pathlib.Path):
        try:
            return value.relative_to(root).as_posix()
        except ValueError:
            pytest.fail(f"{key}: path {value} is not under the fixture root {root}")
    if isinstance(value, (list, tuple)):
        return [_normalise(v, root, key) for v in value]
    if isinstance(value, dict):
        return {k: _normalise(v, root, f"{key}.{k}") for k, v in sorted(value.items())}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _normalise(dataclasses.asdict(value), root, key)
    if type(value).__name__ == "DPSGD":
        return {"class": "DPSGD", "sigma": value.sigma, "C": value.C}
    if isinstance(value, torch.nn.Module):
        # Shapes and trainability only: no tensor hashes, the fixture is macOS and CI is ubuntu.
        return {
            "class": type(value).__name__,
            "params": [[n, list(p.shape), p.requires_grad] for n, p in value.named_parameters()],
        }
    raise TypeError(f"kwarg {key!r} has unnormalisable type {type(value).__name__}")


def _capture(arm, root, monkeypatch):
    """The normalised kwargs ``train()`` is handed for ``arm``; the real ``train()`` never runs."""
    _e2e_env(root, monkeypatch)
    seen = {}

    def _spy(**kwargs):
        seen.update(kwargs)
        raise _Captured

    monkeypatch.setattr(tp, "train", _spy)
    with pytest.raises(_Captured):
        _train(arm)
    return {k: _normalise(v, root, k) for k, v in sorted(seen.items())}


def _git(*args):
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.mark.parametrize("arm", _PRESPLIT_ARMS)
def test_train_kwargs_equal_the_presplit_fixture(arm, tmp_path, monkeypatch):
    assert _capture(arm, tmp_path, monkeypatch) == json.loads(FIXTURE.read_text())["arms"][arm]


def test_the_presplit_fixture_predates_the_split():
    """D-03: every commit touching the fixture is a strict ancestor of the earliest split commit."""
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: ancestry cannot be checked. Set `fetch-depth: 0` on actions/checkout."
    )
    rel = FIXTURE.relative_to(_ROOT).as_posix()
    assert _git("ls-files", rel) == rel, f"{rel} is not tracked"
    fixture_commits = _git("log", "--format=%H", "--", rel).split()
    assert fixture_commits, f"{rel} has no commits"

    splits = _git("log", "-S", "gets_replay", "--format=%H", "--", "scripts/teach_persona.py")
    splits = splits.split()
    if "gets_replay" in _git("show", "HEAD:scripts/teach_persona.py"):
        assert splits, "HEAD carries the split but no commit in history introduced it"
    if not splits:
        return  # honest-green: the split has not been committed yet
    earliest = splits[-1]
    for commit in fixture_commits:
        assert commit != earliest, f"fixture commit {commit} IS the split commit"
        rc = subprocess.run(
            ("git", "merge-base", "--is-ancestor", commit, earliest), cwd=_ROOT
        ).returncode
        assert rc == 0, f"fixture commit {commit} is not an ancestor of split {earliest}"


if __name__ == "__main__":
    import tempfile

    from personacore.provenance import git_sha

    if sys.argv[1:] != ["--capture"]:
        raise SystemExit("usage: python tests/test_phase30_seam.py --capture")
    if FIXTURE.exists():
        raise SystemExit(f"{FIXTURE} exists; D-03 forbids a re-capture")
    arms = {}
    for arm in _PRESPLIT_ARMS:
        with pytest.MonkeyPatch.context() as mp, tempfile.TemporaryDirectory() as tmp:
            arms[arm] = _capture(arm, pathlib.Path(tmp), mp)
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(
        json.dumps(
            {
                "captured_at_sha": git_sha(),
                "note": "D-03 pre-split capture; regenerate never — the point is that it "
                "predates the split",
                "arms": arms,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
