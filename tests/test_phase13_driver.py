"""DEMO-04 Phase-13 A/B driver contracts — the pre-registered constants, the retention gate,
the one-bit arm difference, and the D-07 artifact-isolation guard.

CPU-only, GPU/MPS-free, no checkpoint/fixture-file I/O, no training. Pins six things:
  1. ``test_preregistration_constants`` — the D-10 constants block, exact literals.
  2. ``test_gate_boundary`` — ``ewc_mitigates`` FAILS at delta == MARGIN (boundary is not a pass).
  3. ``test_one_bit_difference`` — ``penalty_for_arm`` is the only thing that differs per arm.
  4. ``test_config_identical_across_arms`` — both arms build an equal ``TrainConfig``.
  5. ``test_arm_outputs_scoped`` — D-07 name-scoped paths, never a Phase-12 output path.
  6. ``test_refuse_to_rerun_guard`` — WR-02 SystemExit naming the offending file.

Scripts-load justification: no other test imports from ``scripts/`` (test_demo_callback.py
states the convention), but the pre-registration constants and the gate rule MUST live in the
committed driver for git history to be the pre-registration proof (D-10) — moving them into the
package would put the experiment's rules somewhere the driver could drift from. The driver's
``main()`` is ``__main__``-guarded and every rule is a module-level pure function/constant
(the ``finetune_smoke.py`` "gate formulas as pure functions" precedent), so an
``importlib.util.spec_from_file_location`` load runs no guard and no training.
"""

import importlib.util
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "finetune_ab", _REPO_ROOT / "scripts" / "finetune_ab.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fab = _load_driver()


def test_preregistration_constants():
    """D-10: the gate rule and arm config are hardcoded literals, committed before any run."""
    assert fab.K == 2
    assert fab.DELTA_RET == 0.068930
    assert fab.MARGIN == 2 * 0.068930
    assert fab.LAMBDA_EWC == 0.01
    assert fab.LR == 9e-5
    assert fab.MAX_STEPS == 4000
    assert fab.SEED == 1337
    assert fab.BATCH_SIZE == 32
    assert fab.GRAD_ACCUM == 1
    assert fab.EVAL_INTERVAL == 250


def test_gate_boundary():
    """D-06: EWC mitigates iff retention gain is STRICTLY greater than MARGIN."""
    assert fab.ewc_mitigates(5.0, 5.0 - fab.MARGIN) is False
    assert fab.ewc_mitigates(5.0, 5.0 - fab.MARGIN - 1e-3) is True
    assert fab.ewc_mitigates(5.0, 5.0) is False


def test_one_bit_difference():
    """The ONLY code-path difference between the arms: penalty_fn None vs the EWC penalty."""
    sentinel = object()
    assert fab.penalty_for_arm("naive", sentinel) is None
    assert fab.penalty_for_arm("ewc", sentinel) is sentinel


def test_config_identical_across_arms():
    """Both arms train under the same TrainConfig (D-03 recorded twin config)."""
    a, b = fab.build_train_config(), fab.build_train_config()
    assert a == b
    assert a.lr == 9e-5
    assert a.max_steps == 4000
    assert a.batch_size == 32
    assert a.grad_accum_steps == 1
    assert a.seed == 1337


@pytest.mark.parametrize("arm", ["naive", "ewc"])
def test_arm_outputs_scoped(arm):
    """D-07 / Pitfall 6: every write target is arm-scoped; Phase-12 evidence is never one."""
    paths = fab.arm_outputs(arm)
    assert len(paths) == 2
    for path in paths:
        assert f"phase13_{arm}" in str(path)
        assert "finetune_prod" not in str(path)
        assert "convbase" not in str(path)


def test_refuse_to_rerun_guard(tmp_path):
    """WR-02: refuse to silently overwrite an arm's recorded outputs; name the offender."""
    existing = tmp_path / "run.csv"
    existing.write_text("step\n0\n", encoding="utf-8")
    missing = tmp_path / "phase13_naive_latest.pt"

    assert fab.refuse_if_exists((missing,)) is None

    with pytest.raises(SystemExit) as excinfo:
        fab.refuse_if_exists((missing, existing))
    assert str(existing) in str(excinfo.value)
