"""D-07 / WARNING-2: the production DP driver's resume path, and the refusals that scope it.

**The measured gap this file closes.** `training/loop.py::train` has implemented `resume_from`
completely since v1.0 — full state + RNG restore, `start_step = ckpt["step"]`, and the
three-branch DP-slot matrix WARNING-1 is closed on. `scripts/teach_persona.py::train_arm` called
`train(...)` and **did not pass it**. So a killed DP arm could only be restarted from ZERO, and
`refuse_if_exists` would not allow even that without the operator deleting the CSV — which
discontinuities the very curve `train()` derives cumulative tokens from the absolute step to keep
continuous. Phase 21's IN-04 was a seam built and never connected; this file exists so D-07 is not
the same story told again.

Everything here is about the ONE HOP: `train_arm`'s `resume_from=` reaching `train`'s. The loop's
own resume semantics are Phase 22's and are pinned by `tests/test_phase22_checkpoint.py`; nothing
below re-asserts them.

Prose in this file spells the driver `train_arm` WITHOUT its opening paren, deliberately: the
register below counts raw grep hits for the driver's name followed by an opening paren, so every
sentence that wrote the paren would add a hit and the register would be counting its own
commentary. Exactly one prose hit survives here — the grep PATTERN itself, which cannot not.

CPU-only except where `_MPS_SKIP` says otherwise. The MPS legs are COUNTABLE SKIPS, never
absences — `tests/test_phase23_mps_venue.py`'s module docstring records why, and that file is this
phase's SINGLE SOURCE OF DEVICE TRUTH. Do NOT re-derive the device axis here.
"""

import ast
import pathlib
import re
import subprocess
import sys

import pytest
import torch

from personacore.config import RuntimeConfig

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "tests"))

import teach_persona as tp  # noqa: E402  (scripts/ is not a package)

from test_phase22_wiring import _e2e_env  # noqa: E402  (tests/ is not one either)
from test_phase23_mps_venue import _MPS_AVAILABLE, _MPS_SKIP  # noqa: E402

# ---------------------------------------------------------------------------------------------
# The call-site register (T-23-37)
# ---------------------------------------------------------------------------------------------
#
# Enumerated by SYMBOL and never by line number: a symbol's name survives an edit above it, a line
# number survives none. One entry per raw grep hit for the driver's name plus an opening paren,
# because the raw count is what a newly-added call site moves — and a register that only listed
# the CALLS would be satisfied by a new call site landing while the `def` line moved. Eight of
# them are CALLS and that is the "eight call sites" this plan's inertness claim is about.
_TRAIN_ARM_CALL_SITES = (
    ("scripts/phase17_isolation.py", "call", "run_one_persona_training"),
    ("scripts/phase19_erasure.py", "call", "_cmd_cal_train"),
    ("scripts/phase19_erasure.py", "call", "_cmd_dialogue_floor"),
    ("scripts/phase19_erasure.py", "call", "_cmd_retrain"),
    ("scripts/phase19_run.py", "call", "retrain_train"),
    ("scripts/phase19_run.py", "prose", "retrain_train docstring"),
    ("scripts/teach_persona.py", "call", "main"),
    ("scripts/teach_persona.py", "call", "run_calibration"),
    ("scripts/teach_persona.py", "def", "the definition itself"),
    ("scripts/teach_persona.py", "prose", "the resume_from sentinel paragraph"),
    ("tests/test_phase22_wiring.py", "call", "test_the_dp_refusal_also_fires_at_train_arm..."),
    ("tests/test_phase22_wiring.py", "prose", "test_cli_names_no_sigma_or_clip_value comment"),
    # THIS file — the only place ALLOWED to pass `resume_from`, and the reason the assertion below
    # is scoped rather than global: a seam nothing exercises is IN-04 again.
    ("tests/test_phase23_resume.py", "call", "_resume_call"),
    ("tests/test_phase23_resume.py", "prose", "the grep pattern in the register probe"),
)

# The DP generator's state is **5,056 bytes on CPU and 44 bytes on MPS** (measured, torch 2.7.1 —
# `personacore.checkpoint`'s two-slot register and `DPSGD.noise_rng_state`'s docstring both record
# the pair WITH its denominator). 44 is written down here for ONE reason: CI is `ubuntu-latest` on
# a CPU wheel and cannot CONSTRUCT an MPS generator, so without a literal the "checkpoint recorded
# `mps`, runtime resolved `cpu`" direction could not be watched anywhere except the M3. On the M3
# it is PROBED and the literal is asserted equal to the probe, so it cannot go stale in silence.
_MPS_STATE_BYTES = 44

_PROBE_PREFIX = "phase23_resume_guard"


def _dp_arms():
    """Two DISTINCT DP arms, or the cross-arm test would be vacuous."""
    assert len(tp.DP_ARMS) >= 2, f"DP_ARMS = {tp.DP_ARMS} — the cross-arm probe needs two"
    return tp.DP_ARMS[0], tp.DP_ARMS[1]


def _resume_fixture(root, monkeypatch, *, arm=None, prefix=_PROBE_PREFIX, state_bytes=None):
    """Every target a resume REQUIRES, on disk under ``tmp_path``, with ``train_arm`` reachable.

    `_e2e_env` is IMPORTED from `tests/test_phase22_wiring.py` rather than re-spelled: it is the
    register that re-points `_REPO_ROOT`, the factset verdict, the base checkpoint and the four
    dialogue bins at `tmp_path` and pins the device to CPU. A second copy of that environment is a
    second thing free to drift from the driver it drives.

    The checkpoint written here is a MINIMAL dict — `_refuse_cross_device_resume` reads exactly
    `.get("dp_noise_rng")`, and none of the guards under test reaches `load_checkpoint`. Writing a
    real 170 MB arm checkpoint to exercise a `.get()` would buy nothing.
    """
    _e2e_env(root, monkeypatch)
    arm = arm or _dp_arms()[0]
    paths = tp.arm_outputs(arm, prefix=prefix)
    for target in tp.arm_bin_targets(arm, paths):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"\x00\x01")
    paths["csv"].parent.mkdir(parents=True, exist_ok=True)
    paths["csv"].write_text("step,train_loss\n1,2.0\n", encoding="utf-8")
    paths["checkpoint"].parent.mkdir(parents=True, exist_ok=True)
    n = _MPS_STATE_BYTES if state_bytes is None else state_bytes
    blob = {} if n == 0 else {"dp_noise_rng": torch.zeros(n, dtype=torch.uint8)}
    torch.save(blob, paths["checkpoint"])
    return arm, paths


def _resume_call(arm, resume_from, *, prefix=_PROBE_PREFIX):
    """Drive the PRODUCTION entry point. `facts`/`family_ids` are unused by every guard below —
    all of them run before `build_arm_bins` — so the fixture stays free of a corpus it never packs.
    """
    return tp.train_arm(
        arm,
        facts=[],
        family_ids=(),
        prefix=prefix,
        dp_sigma=1.0,
        dp_clip_norm=1.0,
        resume_from=resume_from,
    )


# ---------------------------------------------------------------------------------------------
# Task 2 — inertness, the four-target inversion, and the three refusals
# ---------------------------------------------------------------------------------------------


def test_resume_from_none_is_inert():
    """T-23-37. The additive kwarg cannot have changed any pre-existing call to the driver.

    STRUCTURAL half: every raw grep hit in `scripts/` and `tests/` is enumerated in
    `_TRAIN_ARM_CALL_SITES`, the count is asserted against the register's length, the counts are
    re-checked PER FILE, the AST is asked which hits are real calls, and **no call site outside
    this file passes `resume_from`**. A bare total would be satisfied by a site being deleted
    while another was added; the per-file and per-kind checks would not.

    BEHAVIOURAL half: the parameter's default is the `None` SENTINEL and it is KEYWORD_ONLY.
    Seven production call sites already exist and every one passes a NON-DP arm and no resume, so
    a truly-required parameter would make each of them a `TypeError`.
    """
    hits = (
        subprocess.run(
            ["grep", "-rn", "train_arm(", "--include=*.py", "scripts", "tests"],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
        .splitlines()
    )
    assert len(hits) == len(_TRAIN_ARM_CALL_SITES), (
        f"grep found {len(hits)} driver hits but the register lists "
        f"{len(_TRAIN_ARM_CALL_SITES)}. A call site was added or removed without updating the "
        f"register:\n" + "\n".join(hits)
    )

    # Per-FILE counts, so a site moving between files cannot cancel out in the total.
    registered = {}
    for path, _kind, _symbol in _TRAIN_ARM_CALL_SITES:
        registered[path] = registered.get(path, 0) + 1
    found = {}
    for hit in hits:
        path = hit.split(":", 1)[0]
        found[path] = found.get(path, 0) + 1
    assert found == registered, f"per-file driver hit counts drifted: {found} != {registered}"
    assert sum(1 for _p, kind, _s in _TRAIN_ARM_CALL_SITES if kind == "call") == 9, (
        "the register no longer holds the eight pre-existing call sites plus this file's one"
    )

    # ...and the AST agrees with the register about which of them are real CALLS.
    for path in registered:
        expected_calls = sum(
            1 for p, kind, _s in _TRAIN_ARM_CALL_SITES if p == path and kind == "call"
        )
        tree = ast.parse((_ROOT / path).read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else getattr(node.func, "id", None)
            )
            == "train_arm"
        ]
        assert len(calls) == expected_calls, (
            f"{path}: {len(calls)} AST calls, register says {expected_calls}"
        )
        if path == "tests/test_phase23_resume.py":
            continue  # this file is the ONE that must pass the kwarg
        passers = [c.lineno for c in calls if any(k.arg == "resume_from" for k in c.keywords)]
        assert passers == [], (
            f"{path}:{passers} passes `resume_from` — every pre-existing call site must be "
            "byte-identical to its pre-23-07 form"
        )

    import inspect

    param = inspect.signature(tp.train_arm).parameters["resume_from"]
    assert param.default is None
    assert param.kind is inspect.Parameter.KEYWORD_ONLY


def test_refuse_if_exists_is_resume_aware(tmp_path):
    """The four-target table, one assertion per row, on the HELPER itself.

    `expected=()` is the default, so the pre-23-07 sense is asserted first: the helper still
    refuses on presence and still says nothing about absence. Then the inverted sense.
    """
    present, absent = tmp_path / "present", tmp_path / "absent"
    present.write_bytes(b"x")

    # Row 0 — the UNCHANGED sense, and the default that keeps all four pre-existing callers inert.
    with pytest.raises(SystemExit, match="already exists"):
        tp.refuse_if_exists([present])
    tp.refuse_if_exists([absent])  # must NOT raise

    # Rows i-iii — required-present targets: no refusal when they exist...
    tp.refuse_if_exists([], expected=[present])
    # ...and a refusal NAMING THE FILE when they do not.
    with pytest.raises(SystemExit, match=re.escape(str(absent))) as caught:
        tp.refuse_if_exists([], expected=[absent])
    assert "a resume requires it" in str(caught.value)

    # Row iv — the adapter keeps the refuse-if-present sense, in the SAME call as an `expected`.
    with pytest.raises(SystemExit, match="already exists"):
        tp.refuse_if_exists([present], expected=[present])


def test_train_arm_guard_splits_per_target(tmp_path, monkeypatch):
    """T-23-33 / T-23-35. The four-row table as the PRODUCTION driver actually applies it.

    A helper-level table would be green over a `train_arm` that never passed `expected=` at all,
    which is exactly the shape of the bug this plan exists to prevent. So every row below is
    driven through the real `tp.train_arm` entry point.

    The POSITIVE row's evidence is the NEXT refusal: with all three required targets present the
    guard lets the call through, and it then dies in `_refuse_cross_device_resume` — a message
    that can only be reached from past the guard.
    """
    arm, paths = _resume_fixture(tmp_path, monkeypatch)

    # (i)-(iii) all three required targets present -> the guard does NOT refuse.
    with pytest.raises(SystemExit, match="dp_noise_rng was written on") as caught:
        _resume_call(arm, paths["checkpoint"])
    assert "already exists" not in str(caught.value)
    assert "a resume requires it" not in str(caught.value)

    # (iv) the ADAPTER does not invert: on disk it means the arm already completed.
    paths["adapter"].parent.mkdir(parents=True, exist_ok=True)
    paths["adapter"].write_bytes(b"x")
    with pytest.raises(SystemExit, match=re.escape(str(paths["adapter"]))) as caught:
        _resume_call(arm, paths["checkpoint"])
    assert "already exists" in str(caught.value)
    paths["adapter"].unlink()

    # The INVERTED direction, one row at a time: each required target, removed alone, is named.
    required = tp.arm_bin_targets(arm, paths) + [paths["csv"], paths["checkpoint"]]
    for target in required:
        keep = target.read_bytes()
        target.unlink()
        with pytest.raises(SystemExit, match=re.escape(str(target))) as caught:
            _resume_call(arm, paths["checkpoint"])
        assert "a resume requires it" in str(caught.value)
        target.write_bytes(keep)


def test_the_resume_aware_branch_is_watched_red(tmp_path):
    """T-23-36. A weakened `expected` branch is a SILENT no-op, and every test above stays green.

    The positive control: a local copy of the helper with the `expected` loop deleted. It must
    fail to refuse exactly the cases the real one refuses. Without this, `expected=` could be
    accepted and ignored and nothing in this file would notice.
    """

    def weakened(paths, *, expected=()):
        for out in paths:
            if out.exists():
                raise SystemExit(f"[teach_persona] {out} already exists")

    absent = tmp_path / "gone"
    weakened([], expected=[absent])  # the no-op: NO refusal on an absent required file
    with pytest.raises(SystemExit):
        tp.refuse_if_exists([], expected=[absent])

    # ...and the two agree on the UNCHANGED half, so the divergence above is the `expected`
    # branch specifically rather than two unrelated functions.
    present = tmp_path / "here"
    present.write_bytes(b"x")
    for guard in (weakened, tp.refuse_if_exists):
        with pytest.raises(SystemExit, match="already exists"):
            guard([present])


def test_cross_arm_resume_is_refused(tmp_path, monkeypatch):
    """T-23-34. Arm A resuming from arm B's checkpoint would publish a two-arm composition."""
    arm_a, arm_b = _dp_arms()
    _arm, paths_a = _resume_fixture(tmp_path, monkeypatch, arm=arm_a)
    paths_b = tp.arm_outputs(arm_b, prefix=_PROBE_PREFIX)
    paths_b["checkpoint"].parent.mkdir(parents=True, exist_ok=True)
    torch.save({"dp_noise_rng": torch.zeros(4, dtype=torch.uint8)}, paths_b["checkpoint"])

    with pytest.raises(SystemExit) as caught:
        _resume_call(arm_a, paths_b["checkpoint"])
    message = str(caught.value)
    assert str(paths_b["checkpoint"].resolve()) in message
    assert str(paths_a["checkpoint"].resolve()) in message
    assert arm_a in message and arm_b in message
    assert "composes privacy across" in message


def test_cross_device_resume_is_refused_cpu_runtime(tmp_path, monkeypatch):
    """T-23-38, the leg that RUNS IN CI: an MPS-written state under a CPU runtime.

    5,056 vs 44 bytes. torch refuses this on its own (`RNG state is wrong size`) — the seam's job
    is to name the arm, the file, the recorded device and the resolved one, because the raw
    message names none of them and the operator mistake it stands for (a CPU smoke run
    "continued" on the M3) gives no other clue.
    """
    if _MPS_AVAILABLE:
        assert _MPS_STATE_BYTES == tp._generator_state_bytes("mps"), (
            "the recorded 44-byte MPS figure no longer matches a probe on this machine — the "
            "CI-only literal has gone stale and the CI leg is now testing a fiction"
        )
    arm, paths = _resume_fixture(tmp_path, monkeypatch, state_bytes=_MPS_STATE_BYTES)

    with pytest.raises(SystemExit) as caught:
        _resume_call(arm, paths["checkpoint"])
    message = str(caught.value)
    assert arm in message
    assert str(paths["checkpoint"]) in message
    assert "mps" in message and "'cpu'" in message
    assert str(_MPS_STATE_BYTES) in message
    assert str(tp._generator_state_bytes("cpu")) in message


@_MPS_SKIP
def test_cross_device_resume_is_refused_mps_runtime(tmp_path, monkeypatch):
    """T-23-38, the other direction and the REAL one: a CPU-written 5,056-byte state on the M3.

    D-01 makes MPS the venue that produces the published ε, so this is the direction a real
    operator hits. The state is a genuine `torch.Generator("cpu").get_state()`, not a fabricated
    length — the CI leg above is the one that has to fabricate.
    """
    arm, paths = _resume_fixture(tmp_path, monkeypatch, state_bytes=0)
    torch.save({"dp_noise_rng": torch.Generator(device="cpu").get_state()}, paths["checkpoint"])
    monkeypatch.setattr(
        tp,
        "preflight_device",
        lambda strict=True: {"device": "mps", "cc": None, "torch": torch.__version__},
    )
    monkeypatch.setattr(tp, "RuntimeConfig", lambda: RuntimeConfig(device="mps"))

    with pytest.raises(SystemExit) as caught:
        _resume_call(arm, paths["checkpoint"])
    message = str(caught.value)
    assert arm in message
    assert str(paths["checkpoint"]) in message
    assert "written on cpu" in message and "'mps'" in message
    assert str(tp._generator_state_bytes("cpu")) in message
    assert str(tp._generator_state_bytes("mps")) in message


def test_a_checkpoint_without_a_device_record_is_refused(tmp_path, monkeypatch):
    """Refuse rather than default, and SAY WHICH KEY was missing.

    This is deliberately STRICTER than `training/loop.py`'s branch (2), which reads an absent
    `dp_noise_rng` as "not a DP run, seed fresh" and is pinned as tolerated by two committed
    guards. The two are not in tension and the asymmetry is the point: at the LOOP level the
    absence means "no DP run wrote this"; at the DRIVER level, where a DP ARM asked to continue
    it, the same absence means the epsilon prefix this resume claims to continue never existed.
    Both committed guards drive `train()` directly, never `train_arm`, so neither reddens.
    """
    arm, paths = _resume_fixture(tmp_path, monkeypatch, state_bytes=0)

    with pytest.raises(SystemExit) as caught:
        _resume_call(arm, paths["checkpoint"])
    message = str(caught.value)
    assert "dp_noise_rng" in message
    assert arm in message and str(paths["checkpoint"]) in message
    assert "never privatised" in message
