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
import shutil
import subprocess
import sys

import pytest
import torch

from personacore.config import RuntimeConfig
from personacore.privacy.accountant import epsilon_for
from personacore.training import loop as loop_mod

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "tests"))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import teach_persona as tp  # noqa: E402

from test_phase22_checkpoint import _next_draw  # noqa: E402  (tests/ is not one either)
from test_phase22_wiring import _e2e_env  # noqa: E402
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
    # Plan 23-08's control scheduling. A NON-DP arm and NO resume, like every other production
    # site, so `resume_from`'s `None` sentinel keeps it byte-identical to the pre-23-07 driver.
    ("scripts/phase23_run.py", "call", "train_control"),
    # Plan 23-10's σ=0 diagnostic — the FIRST PRODUCTION CONSUMER of the seam this file built. It
    # DOES pass `resume_from`, and `_RESUME_PASSERS` below is what admits it by name.
    ("scripts/phase23_run.py", "call", "train_sigma_zero"),
    ("scripts/teach_persona.py", "call", "main"),
    ("scripts/teach_persona.py", "call", "run_calibration"),
    ("scripts/teach_persona.py", "def", "the definition itself"),
    ("scripts/teach_persona.py", "prose", "the resume_from sentinel paragraph"),
    ("tests/test_phase22_wiring.py", "call", "test_the_dp_refusal_also_fires_at_train_arm..."),
    ("tests/test_phase22_wiring.py", "prose", "test_cli_names_no_sigma_or_clip_value comment"),
    # THIS file — the only place ALLOWED to pass `resume_from`, and the reason the assertion below
    # is scoped rather than global: a seam nothing exercises is IN-04 again.
    ("tests/test_phase23_resume.py", "call", "_resume_call (the refusal probes)"),
    ("tests/test_phase23_resume.py", "call", "_run (the production MPS probe)"),
    ("tests/test_phase23_resume.py", "prose", "the grep pattern in the register probe"),
)

# This file's own name, resolved once so the "eight PRE-EXISTING call sites" arithmetic below
# subtracts the right thing.
_THIS_FILE = "tests/test_phase23_resume.py"

# WHO MAY PASS `resume_from`, AND HOW MANY TIMES. Enumerated, with counts, because the guard below
# used to say "this file only" and skip itself unchecked — which was right while the seam had no
# production consumer and wrong the moment it got one.
#
# THE TEETH ARE UNCHANGED IN THE DIRECTION THAT MATTERS. What T-23-37 asserts is that the additive
# kwarg did not change any PRE-EXISTING call: every one of the eight sites that existed before 23-07
# must still be byte-identical to its pre-23-07 form, and every one of them is absent from this map
# and therefore pinned at ZERO passers. Widening it to a named production consumer is the opposite
# of weakening — this file's own register already records that "a seam nothing exercises is IN-04
# again", and a COUNT rather than a boolean means a SECOND passer in an admitted file still reddens.
_RESUME_PASSERS = {
    # `_resume_call` (the refusal probes) and `_run` (the production MPS kill->resume probe).
    _THIS_FILE: 2,
    # Plan 23-10's `train_sigma_zero`: a killed σ=0 run resumes from its OWN checkpoint instead of
    # restarting 200 steps. `train_control` in the same file passes NOTHING, which is why this is a
    # count and not a file-level exemption.
    "scripts/phase23_run.py": 1,
}

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
    # EIGHT at 23-07, when the sentinel landed; NINE from 23-08, which added
    # `phase23_run.train_control`; TEN from 23-10, which added `phase23_run.train_sigma_zero` — the
    # seam's first production consumer. The literal is a tripwire against a site vanishing
    # unnoticed, so it is BUMPED with its reason rather than derived from the register — that would
    # make the check restate the register instead of pinning a count against it. Every number is
    # spelled so a reader can see the ledger move rather than only its current total.
    assert (
        sum(1 for path, kind, _s in _TRAIN_ARM_CALL_SITES if kind == "call" and path != _THIS_FILE)
        == 8 + 1 + 1
    ), (
        "the register no longer holds the 8 pre-23-08 call sites plus 23-08's control scheduling "
        "plus 23-10's σ=0 diagnostic"
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
        # EVERY file is checked now, including this one: the old `continue` skipped the only file
        # that was allowed to pass the kwarg, so a passer VANISHING from here — the seam going
        # unexercised, IN-04 again — was invisible. The allow-set carries counts for exactly that.
        passers = [c.lineno for c in calls if any(k.arg == "resume_from" for k in c.keywords)]
        allowed = _RESUME_PASSERS.get(path, 0)
        assert len(passers) == allowed, (
            f"{path}:{passers} passes `resume_from` {len(passers)} time(s); `_RESUME_PASSERS` "
            f"admits {allowed}. Every PRE-EXISTING call site is pinned at ZERO by its absence from "
            "that map and must stay byte-identical to its pre-23-07 form; an admitted file is "
            "pinned at a COUNT, so a second passer there reddens too — and so does a passer "
            "disappearing, which would mean the seam is exercised by nothing"
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


# ---------------------------------------------------------------------------------------------
# Task 3 — the production kill -> resume on the MPS venue
# ---------------------------------------------------------------------------------------------

_PROBE_ARM = "dp_n8"

# PROBE VALUES, NOT A BUDGET. sigma and C are Phase 23 RESOURCE PARAMETERS under Phase 20's Z
# boundary and are pre-registered by their own plans; nothing here may read as an operating
# budget. These two exist only so the seam has a live DP mechanism to resume, and the AST guard
# `test_cli_names_no_sigma_or_clip_value` scopes itself to `scripts/teach_persona.py` precisely so
# a test fixture can name a value the driver never may (`tests/test_phase22_wiring.py`'s
# `_FIXTURE_SIGMA` is the committed precedent).
_PROBE_SIGMA = 1.0
_PROBE_CLIP = 1.0
_PROBE_DELTA = 1e-5

# `tests/test_phase22_checkpoint.py`'s shape verbatim (`_TOTAL_STEPS = 4`, `_KILL_AT = 2`).
_TOTAL_STEPS = 4
_KILL_AT = 2
# Deliberately NOT `tp.SEED`: the resumed seam must START somewhere else, so a matching stream
# afterwards can only be the restore working rather than two objects that agreed to begin with.
_RESUME_SEED = 999

_PREFIX_A = "phase23_resume_probe_a"
_PREFIX_B = "phase23_resume_probe_b"

# Bound at IMPORT, before any monkeypatch can replace `tp.DPSGD`. See `_install_dp_probe`.
_REAL_DPSGD = tp.DPSGD

# The four production inputs `train_arm` refuses loudly without. A missing one skips THIS test and
# nothing else — `tests/test_lora_artifact.py:238`'s register — and the reason= says what still
# carries the guarantee.
_PRODUCTION_INPUTS = (
    tp.CONVBASE_BEST,
    tp.DIALOG_TRAIN_BIN,
    tp.DIALOG_TRAIN_MASK,
    tp.DIALOG_VAL_BIN,
    tp.DIALOG_VAL_MASK,
)
_INPUTS_SKIP = pytest.mark.skipif(
    not all(path.exists() for path in _PRODUCTION_INPUTS),
    reason=(
        "the production base checkpoint and/or the PersonaChat dialogue pair are absent (they are "
        "gitignored and never in CI), so no real arm can run here. What still carries the seam's "
        "correctness wherever this skips: every refusal above, which runs at fixture scale on CPU."
    ),
)


class _Killed(Exception):
    """The kill. Raised from inside ``loop.save_checkpoint``, the instant the periodic checkpoint
    at ``_KILL_AT`` has hit disk and before the loop can take another step — the on-disk state a
    SIGKILL between two checkpoints leaves, and exactly the state the four-target inversion is
    written for (checkpoint / csv / bins present, adapter absent)."""


def _bin_digests():
    paths = tp.arm_bin_targets(_PROBE_ARM, tp.arm_outputs(_PROBE_ARM))
    return {path.name: tp._sha256(path) for path in paths if path.exists()}


def _clear_bins():
    """The three dp_n8 bins carry NO prefix (``arm_outputs``' own non-widening), so every run in
    this test shares them and a FRESH run must start from their absence. They are rebuilt by each
    fresh run and are left in place at the end — 23-10 and 23-11 delete and rebuild them and prove
    byte-identity against the sha256 values this plan's SUMMARY records."""
    for path in tp.arm_bin_targets(_PROBE_ARM, tp.arm_outputs(_PROBE_ARM)):
        if path.exists():
            path.unlink()


def _scrub(prefix):
    paths = tp.arm_outputs(_PROBE_ARM, prefix=prefix)
    if paths["csv"].parent.exists():
        shutil.rmtree(paths["csv"].parent)
    for key in ("checkpoint", "adapter"):
        if paths[key].exists():
            paths[key].unlink()


def _install_dp_probe(monkeypatch, composed, seams, births, *, seed_override=None):
    """Shadow ``finalize`` on whatever seam ``train_arm`` CONSTRUCTS, and hand the instance back.

    ``_count_composed_steps`` (``tests/test_phase22_checkpoint.py:387``) shadows an instance the
    test owns. Here the production driver owns it, so the shadow is installed at the CONSTRUCTOR
    instead. Counting real ``finalize`` invocations rather than reading the checkpoint's ``step``
    field is load-bearing and was measured there: with ``start_step`` mutated to 0 the resumed run
    composes MORE steps than its checkpoint records, and an epsilon read off the field is then
    identical across both arms AND optimistic.

    ``births`` records each seam's generator state AT CONSTRUCTION, before ``train()``'s
    ``resume_from`` block can restore into it. That snapshot is the positive control for the whole
    resume claim: paired with ``seed_override`` it proves the resumed seam STARTED somewhere else,
    so a matching stream at the end is the restore firing rather than two objects that agreed to
    begin with.

    ``_REAL_DPSGD`` and never ``tp.DPSGD``, and the reason is a MEASURED bug rather than style:
    this helper is installed three times in one test, so reading the CLASS off the module captures
    the PREVIOUS factory and every later run's ``finalize`` increments every earlier run's counter
    too. Watched: the first draft reported ``(8, 4, 2)`` composed steps for a ``(4, 2, 2)`` run —
    a T that is WRONG IN THE PESSIMISTIC DIRECTION, which is exactly the kind of accounting error
    a green test would have carried into a published ε.
    """
    real = _REAL_DPSGD

    def factory(model, **kwargs):
        if seed_override is not None:
            kwargs["seed"] = seed_override
        seam = real(model, **kwargs)
        seams.append(seam)
        births.append(seam.noise_rng_state().clone())
        inner = seam.finalize

        def counting(accum):
            composed.append(accum)
            return inner(accum)

        seam.finalize = counting
        return seam

    monkeypatch.setattr(tp, "DPSGD", factory)


def _run(prefix, *, resume_from=None):
    facts, second_person, replay_ratio = tp.arm_spec(_PROBE_ARM)
    return tp.train_arm(
        _PROBE_ARM,
        facts=facts,
        family_ids=fs.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        prefix=prefix,
        dp_sigma=_PROBE_SIGMA,
        dp_clip_norm=_PROBE_CLIP,
        resume_from=resume_from,
    )


@_MPS_SKIP
@_INPUTS_SKIP
def test_production_resume_epsilon_bit_identical(monkeypatch):
    """**D-01 / WARNING-2.** A real `train_arm` kill -> resume on MPS reproduces the run.

    THE VENUE IS THE POINT. D-01 makes MPS the venue that produces this milestone's published ε,
    and the DP generator's state is 44 bytes there against 5,056 on CPU. Every Phase-22 resume
    probe is CPU-only by design, so this property has to cross the boundary BY MEASUREMENT.

    THE STEP BUDGET IS REDUCED, AND HERE IS THE REDUCTION AND ITS REASON. `tp.MAX_STEPS` is
    monkeypatched from 200 to 4 and `tp.CHECKPOINT_INTERVAL` from 50 to 2, so a checkpoint lands
    mid-run; `tp.EVAL_INTERVAL` goes to 1 so the CSV has a row per step to check continuity on,
    and `tp.WARMUP_STEPS` to 1 so the 4-step run is not entirely inside a 20-step ramp. This probe
    is about the resume PATH, not the step budget — at the production shape a `dp_n8` arm costs
    ≈ 3.79 min and buys this assertion nothing extra. `test_resume_epsilon_bit_identical` already
    uses exactly this shape (`_TOTAL_STEPS = 4`, `_KILL_AT = 2`). **Plan 23-10's σ=0 run is the one
    that exercises the full 200-step path for real.**

    THE DPSGD-06 EXCEPTION, DISCLOSED RATHER THAN HIDDEN. SC1 and DPSGD-06 say the σ=0 diagnostic
    is the DP arm's FIRST executed run. This test breaks that LITERAL ordering: it runs the
    PRODUCTION caller on the PRODUCTION `dp_n8` arm at σ > 0, in wave 2, three waves before 23-10's
    σ=0 run. It is NOT a sweep point, and each reason is a property a reader can check: `MAX_STEPS`
    is monkeypatched to 4, no question is scored, no utility reading is produced, the prefixed
    adapter / CSV / checkpoint are deleted at the end, and **zero `results/phase23_*` records are
    committed**. So it can inform neither the noise floor nor the D-04 verdict. That last property
    is also exactly what makes it INVISIBLE to all three of 23-03's ancestry guards, which bind on
    COMMITTED records: 23-04's wiring probe is auditable from the repo because it commits a record
    declaring `sweep_point: false`, while this probe commits nothing at all. This docstring and the
    plan SUMMARY are therefore the only two places the disclosure can live, which is why it is
    written out in full here rather than left for a reader to reconstruct from wave numbers.

    WHAT IS COMPARED, AND WITH WHICH BOUND. Arm A runs `_TOTAL_STEPS` uninterrupted. Arm B is
    killed at `_KILL_AT` and resumed from its own checkpoint. Then, under EXACT `==` and never a
    tolerance (the same call shape across two processes — `test_resume_epsilon_bit_identical`'s
    register): the composed step counts, the reported ε, the two runs' CSV rows READ AS TEXT
    row-for-row, and the next noise draw off each run's seam.
    """
    for path in _PRODUCTION_INPUTS:
        assert path.exists(), f"missing production input {path}"
    print(
        "[23-07] production inputs: "
        + ", ".join(f"{p.name}={p.stat().st_size:,}B" for p in _PRODUCTION_INPUTS)
    )

    monkeypatch.setattr(tp, "MAX_STEPS", _TOTAL_STEPS)
    monkeypatch.setattr(tp, "CHECKPOINT_INTERVAL", _KILL_AT)
    monkeypatch.setattr(tp, "EVAL_INTERVAL", 1)
    monkeypatch.setattr(tp, "WARMUP_STEPS", 1)

    evidence = {}
    try:
        # ---- Arm A: uninterrupted -------------------------------------------------------------
        _clear_bins()
        _scrub(_PREFIX_A)
        composed_a, seams_a, births_a = [], [], []
        _install_dp_probe(monkeypatch, composed_a, seams_a, births_a)
        _run(_PREFIX_A)
        paths_a = tp.arm_outputs(_PROBE_ARM, prefix=_PREFIX_A)
        evidence["digests_a"] = _bin_digests()
        evidence["step_a"] = torch.load(
            paths_a["checkpoint"], map_location="cpu", weights_only=False
        )["step"]
        evidence["csv_a"] = paths_a["csv"].read_text(encoding="utf-8").splitlines()

        # ---- Arm B, first half: KILLED mid-loop, right after the step-_KILL_AT checkpoint -------
        #
        # THE KILL IS AN INTERRUPT, NOT A SHORTER RUN, AND THE DIFFERENCE WAS MEASURED. The first
        # draft killed by monkeypatching `tp.MAX_STEPS` to `_KILL_AT`. That changes
        # `TrainConfig.max_steps`, which is the COSINE SCHEDULE'S HORIZON: at step 2 the killed
        # half then sat at the END of its own 2-step cosine (lr 2.9999999999999997e-05) while the
        # uninterrupted control was mid-schedule (lr 0.00023249999999999999). The two runs took
        # genuinely different step-2 updates and the curves diverged from row 3 on. A resume test
        # whose "kill" silently reparameterises the schedule proves nothing about resuming.
        #
        # So the kill is a raise from inside `loop.save_checkpoint`, immediately AFTER the in-loop
        # periodic save at `_KILL_AT` has hit disk — the on-disk state a SIGKILL between two
        # checkpoints leaves, with `max_steps` still `_TOTAL_STEPS` and the schedule untouched.
        _clear_bins()
        _scrub(_PREFIX_B)
        composed_b, seams_b, births_b = [], [], []
        _install_dp_probe(monkeypatch, composed_b, seams_b, births_b)
        real_save = loop_mod.save_checkpoint

        def _killing_save(path, **kwargs):
            real_save(path, **kwargs)
            if kwargs["step"] >= _KILL_AT:
                raise _Killed

        monkeypatch.setattr(loop_mod, "save_checkpoint", _killing_save)
        with pytest.raises(_Killed):
            _run(_PREFIX_B)
        monkeypatch.setattr(loop_mod, "save_checkpoint", real_save)
        paths_b = tp.arm_outputs(_PROBE_ARM, prefix=_PREFIX_B)
        evidence["digests_b1"] = _bin_digests()
        kill_blob = torch.load(paths_b["checkpoint"], map_location="cpu", weights_only=False)
        evidence["step_kill"] = kill_blob["step"]
        evidence["kill_state_bytes"] = int(kill_blob["dp_noise_rng"].numel())
        assert not paths_b["adapter"].exists(), "the kill left an adapter — it was not a kill"

        # ---- Arm B, second half: the RESUME through the production driver ----------------------
        composed_c, seams_c, births_c = [], [], []
        _install_dp_probe(monkeypatch, composed_c, seams_c, births_c, seed_override=_RESUME_SEED)
        _run(_PREFIX_B, resume_from=paths_b["checkpoint"])
        evidence["digests_b2"] = _bin_digests()
        evidence["step_b"] = torch.load(
            paths_b["checkpoint"], map_location="cpu", weights_only=False
        )["step"]
        evidence["csv_b"] = paths_b["csv"].read_text(encoding="utf-8").splitlines()

        # POSITIVE CONTROL, read off live objects before the cleanup below: the resumed seam was
        # BORN at _RESUME_SEED, somewhere else entirely, so a matching stream at the end can only
        # be the restore firing.
        evidence["born_elsewhere"] = not torch.equal(births_c[0], kill_blob["dp_noise_rng"])
        evidence["birth_bytes"] = tuple(int(b[0].numel()) for b in (births_a, births_b, births_c))
        device = seams_a[0]._g.device.type
        evidence["device"] = device
        evidence["draw_a"] = _next_draw(seams_a[0], device)
        evidence["draw_b_killhalf"] = _next_draw(seams_b[0], device)
        evidence["draw_c"] = _next_draw(seams_c[0], device)
        evidence["composed"] = (len(composed_a), len(composed_b), len(composed_c))
    finally:
        _scrub(_PREFIX_A)
        _scrub(_PREFIX_B)

    # ---- results/ is untouched: this probe commits NOTHING ------------------------------------
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "results/"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert porcelain == "", f"the probe left artifacts in results/:\n{porcelain}"

    # RAW EVIDENCE, printed rather than only asserted: every figure this plan's SUMMARY quotes is
    # readable from a `-s` run of this one test, so the SUMMARY is transcribing a log rather than
    # restating a claim.
    print(f"[23-07] device={evidence['device']} composed={evidence['composed']}")
    print(
        f"[23-07] dp_noise_rng bytes: births={evidence['birth_bytes']} "
        f"kill={evidence['kill_state_bytes']}"
    )
    for name, digest in sorted(evidence["digests_a"].items()):
        print(f"[23-07] sha256 {name} {digest}")
    for row in evidence["csv_a"]:
        print(f"[23-07] csv_A {row}")
    for row in evidence["csv_b"]:
        print(f"[23-07] csv_B {row}")

    # ---- 1. THE CORPUS. All three builds agree byte for byte (T-23-35) ------------------------
    assert set(evidence["digests_a"]) == {
        "persona_dp_n8_train.bin",
        "persona_dp_n8_train_mask.bin",
        "persona_dp_n8_train_fact.bin",
    }, evidence["digests_a"]
    assert evidence["digests_a"] == evidence["digests_b1"] == evidence["digests_b2"], (
        "the dp_n8 corpus is not reproducible across builds: "
        f"A={evidence['digests_a']} B1={evidence['digests_b1']} B2={evidence['digests_b2']}"
    )

    # ---- 2. T, COUNTED off real finalize invocations and pinned to the checkpoint field --------
    steps_a, steps_b1, steps_b2 = evidence["composed"]
    assert (steps_a, steps_b1, steps_b2) == (_TOTAL_STEPS, _KILL_AT, _TOTAL_STEPS - _KILL_AT)
    t_a, t_b = steps_a, steps_b1 + steps_b2
    assert evidence["step_a"] == t_a
    assert evidence["step_kill"] == _KILL_AT
    assert evidence["step_b"] == t_b, (
        f"the resumed run REPORTS T = {evidence['step_b']} but composed {t_b} steps "
        f"({steps_b1} before the kill + {steps_b2} after) — the published epsilon would then "
        "describe a composition that never ran, and it would be optimistic"
    )

    # ---- 3. THE EPSILON, under EXACT `==` -----------------------------------------------------
    epsilon_a = epsilon_for(_PROBE_SIGMA, t_a, _PROBE_DELTA)
    epsilon_b = epsilon_for(_PROBE_SIGMA, t_b, _PROBE_DELTA)
    assert epsilon_a == epsilon_b, f"epsilon diverged across the kill: {epsilon_a!r} {epsilon_b!r}"
    # NON-DEGENERACY: epsilon genuinely MOVES with T, so the equality is not green over a quantity
    # that never varies.
    assert epsilon_for(_PROBE_SIGMA, _KILL_AT, _PROBE_DELTA) != epsilon_a
    print(f"[23-07] T_A={t_a} T_B={t_b} epsilon_A={epsilon_a!r} epsilon_B={epsilon_b!r}")

    # ---- 4. THE CSV: continuous across the kill, and equal to the control row for row ---------
    header_a, rows_a = evidence["csv_a"][0], evidence["csv_a"][1:]
    header_b, rows_b = evidence["csv_b"][0], evidence["csv_b"][1:]
    assert header_a == header_b
    fields = header_a.split(",")
    step_col, token_col = fields.index("step"), fields.index("tokens")
    steps = [int(row.split(",")[step_col]) for row in rows_b]
    tokens = [int(row.split(",")[token_col]) for row in rows_b]
    assert steps == list(range(1, _TOTAL_STEPS + 1)), (
        f"the CSV is not continuous across the kill: {steps}. `train()` derives cumulative tokens "
        "from the ABSOLUTE step precisely so it is; a gap or a repeat here means the resume "
        "restarted the counter, and deleting the CSV to get past a refusal (T-23-33) is the "
        "operator mistake that produces it"
    )
    assert tokens == sorted(tokens) and len(set(tokens)) == len(tokens), tokens
    # THE REPRODUCTION CLAIM, at its strongest available bound: the resumed run's logged curve is
    # the uninterrupted run's, READ AS TEXT. `wall_clock` is a step-derived logical clock exactly
    # so this comparison is possible (loop.py's own note).
    assert rows_b == rows_a, (
        "the resumed curve is NOT the uninterrupted curve row for row:\n"
        f"  uninterrupted: {rows_a}\n  resumed:       {rows_b}"
    )

    # ---- 5. THE RNG HALF, which epsilon is structurally blind to ------------------------------
    assert evidence["device"] == "mps", evidence["device"]
    assert evidence["birth_bytes"] == (_MPS_STATE_BYTES,) * 3, evidence["birth_bytes"]
    assert evidence["kill_state_bytes"] == _MPS_STATE_BYTES
    assert evidence["born_elsewhere"], (
        f"the resumed seam was born at seed {_RESUME_SEED} yet already carried the killed run's "
        "generator state — the equality below would then be an accident, not a restore"
    )
    draw_a, draw_c = evidence["draw_a"], evidence["draw_c"]
    assert draw_a.abs().sum() > 0.0, "a degenerate probe draw would compare two zeros"
    assert torch.equal(draw_a, draw_c), (
        "the resumed seam's next noise draw differs from the uninterrupted run's, so the "
        "production restore did not fire through train_arm -> train"
    )
    # NEGATIVE CONTROL: the draw is POSITION-SENSITIVE, so the equality above is not something two
    # seams satisfy for free. The kill half's seam stopped at _KILL_AT and its next draw must NOT
    # match the run that went all the way. (The OTHER negative control — a checkpoint with the
    # dp_noise_rng slot stripped — is unreachable through this driver BY DESIGN: 23-07's own
    # cross-device guard refuses it outright, and that refusal is pinned by
    # `test_a_checkpoint_without_a_device_record_is_refused` above. `train()`'s tolerance of the
    # same shape stays watched at the loop level by `test_resume_epsilon_bit_identical`.)
    assert not torch.equal(draw_a, evidence["draw_b_killhalf"]), (
        "a seam stopped at _KILL_AT produced the same next draw as one that ran to _TOTAL_STEPS — "
        "the stream is not position-sensitive and every equality above proves nothing"
    )
