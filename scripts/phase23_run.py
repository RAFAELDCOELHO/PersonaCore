"""PHASE 23'S RUN DRIVER — the control scheduling, the never-taught scheduling, the measured floor.

``scripts/phase19_run.py``'s register: explicit argv sub-modes (never ``argparse``), ``_prove`` /
``SystemExit`` refusals (never ``assert``), and every rule CALLED out of a committed pin rather
than re-implemented here.

**THIS FILE IS NOT EDIT-ONCE AND MUST NEVER CARRY A PRE-REGISTRATION.** 23-08 Tasks 2 and 3 re-edit
it, and so do 23-10, 23-11 and 23-14. ``git log -1`` on it therefore returns its most recent commit,
and no ancestry check could bind a rule written here to the measurement that rule decides. Every
pre-registered rule this driver consumes — ``noise_floor``, ``choose_n_seeds``,
``H_PER_POINT_FLOOR_SECONDS`` — is IMPORTED from the edit-once ``scripts/phase23_prereg.py``, whose
``test_the_prereg_rule_precedes_every_phase23_result`` binds it blind.

THE SUB-MODES, and why the split is not cosmetic::

    python scripts/phase23_run.py cost        # train + score control seed 1, cost the SCORING leg,
                                              #   apply the blind seed rule -> N        (23-08 T1)
    python scripts/phase23_run.py schedule    # ONE invocation: the remaining control arms AND every
                                              #   never-taught arm, at the same seed list (23-08 T2)
    python scripts/phase23_run.py floor       # score the remaining control arms, reduce the floor
                                              #   through `phase23_prereg.noise_floor`  (23-08 T3)
    python scripts/phase23_run.py sigma-zero  # the DP arm's FIRST executed run at sigma = 0, then
                                              #   `phase23_prereg.sigma_zero_verdict`   (23-10)

``cost`` MUST run first and it MUST train a control arm, because N is a function of the scoring
cost and the scoring cost is not knowable without a scored arm. That control arm is the FIRST
control reading — it is not re-trained or re-scored under a second name in ``schedule``, because a
second identical construction would be a duplicated measurement rather than a second measurement.
``schedule`` therefore trains control seeds ``[1:]`` and never-taught seeds ``[:]``; it REFUSES if
seed 1's control adapter is absent, so nothing is ever silently skipped.

THE HAND-OFF FILE IS DELIBERATELY GITIGNORED. ``data/phase23_run_state.json`` carries the driver's
own working state between sub-modes. ``data/`` is wholly gitignored, and that is the point: every
number in it is carried into one of the two COMMITTED records below, and a third tracked artifact
under ``results/phase23_*`` would be a third thing the ordering guards have to watch for no gain.

RETRACTION, 2026-08-27 — THE FILE IS NOW TRACKED. The paragraph above is kept verbatim because it
is what the phase was built against, and its REASONING still holds: a third artifact *under*
``results/phase23_*`` would indeed burden the ordering guards. It simply does not apply here.
``data/phase23_run_state.json`` is not under that prefix, and neither guard glob matches it —
``NOISED_RECORD_GLOB`` is ``results/phase23_noised_*`` and the ancestry guard binds
``results/phase23_*``; both were checked against this path and both return False. Tracking it adds
nothing to any guard's watch list, so the stated cost is not incurred.

WHAT FORCED THE CHANGE. This file is the ONE-ATTEMPT rule's state, and untracked it left a
delete-and-re-run with **zero residue anywhere** — ``git ls-files data/`` returned 0 and no state
file had ever been committed in this repository. That is why 23-15/23-17 record the full-delete
case as *refused by NOTHING*. It also inherited the wrong rule: ``.gitignore:13`` reads "Training /
runtime outputs (memory lives in weights — never commit them)", written for the GB-scale ``uint16``
corpora and ``.pt`` adapters. This is 16 KB of measurement ledger — a ``results/``-class artifact
filed in a ``data/``-class directory.

WHAT TRACKING DOES AND DOES NOT BUY. It is NOT real-time prevention, and it is not by itself
retroactive: a working-tree revert after a run still leaves no history. It becomes retroactive only
once a section reaches a COMMIT — which 23-17's same-session commit requirement now carries. Against
that committed baseline a later deletion is a visible diff. The residual is therefore "not
prevented, but auditable after the fact", not "closed" — and 23-15/23-17 must say the weaker true
thing rather than the stronger false one.

CPU-hostile: this driver trains and scores on the resolved device (MPS on the M3, D-01).
"""

import os

# Set BEFORE importing torch so the backend honors it for the whole process — `teach_persona`'s own
# register, restated here because this module's import block is sorted and `teach_persona` is last.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import contextlib  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import pathlib  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from dataclasses import asdict  # noqa: E402

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

# READ-ONLY, both of them. `mitigation_gate` is FROZEN; `mitigation_budget` is the PIN — the floor
# is READ from it and never recomputed here. Importing the budget in THIS module is not the import
# the ceiling forbids: 23-02's guards bind on what `scripts/mitigation_*.py` modules import (and on
# what the frozen gate transitively loads), and a driver reading the pin is the direction the pin
# exists for.
import mitigation_budget  # noqa: E402
import mitigation_gate  # noqa: E402
import phase14_factset as fs  # noqa: E402
import phase23_cost  # noqa: E402
import teach_persona as tp  # noqa: E402
from phase23_prereg import (  # noqa: E402
    CONTROL_FLOOR_RECORD,
    FLOOR_PROVENANCE_KEYS,
    H_PER_POINT_FLOOR_SECONDS,
    NEVER_TAUGHT_TRAINING_RECORD,
    NOISED_RECORD_GLOB,
    SIGMA_ZERO_RECORD,
    choose_n_seeds,
    noise_floor,
    sigma_zero_verdict,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The driver's own working state, between sub-modes. GITIGNORED (`data/`) — see the module
# docstring for why this is not a third `results/phase23_*` artifact.
STATE_PATH = _ROOT / "data" / "phase23_run_state.json"

# `arm_outputs(arm, prefix=)` scopes csv/checkpoint/adapter as `{prefix}_{arm}`, so the arm names
# below carry NO `phase23_` of their own: passing `prefix="phase23"` renders exactly
# `results/phase23_control_seed1337/run.csv` and `checkpoints/phase23_never_taught_seed1337_
# adapter.pt`. Spelling the phase into the arm name AS WELL would render it twice.
PREFIX = "phase23"

# THE SEED LADDER, fixed in this file's FIRST commit — before any control arm was trained and
# therefore before any reading existed. Order is load-bearing twice: `sigma_zero_verdict` pins the
# CENTRAL reading to `control_readings[0]`, the reading at the FIRST recorded seed, and
# `choose_n_seeds` selects a PREFIX of this ladder, so a later N is a superset of an earlier one.
#
# `(1337, 2024)` is the repository's established pair — `results/phase19_noise_floors.json`'s
# `dialogue_ppl_noise_floor.seeds` and `tests/test_phase20_correction.py:115` both use it. The
# three extensions are adjacent to those two and distinct from every other seed in the tree.
#
# HONEST LIMIT, stated rather than implied: this ladder is NOT ancestry-bound the way `noise_floor`
# and `choose_n_seeds` are. It lives in a file four later plans re-edit, so `git log -1` on it
# proves nothing. What it has instead is 23-08's own commit order — the ladder landed in the
# driver's first commit, one commit before the first control arm was trained.
SEED_LADDER = (1337, 2024, 1338, 2025, 1339)

SCORING_TIER_LABELS = ("taught ON", "held-out ON", "taught OFF", "held-out OFF")

# =================================================================================================
# THE σ=0 DIAGNOSTIC'S PARAMETERS (DPSGD-06 / D-04). σ and C are Phase-23 RESOURCE parameters and
# Phase 22 deliberately names neither anywhere in its tree, so they are named HERE, with their
# reasons, at the driver that runs them.
# =================================================================================================

SIGMA_ZERO_ARM = "dp_n8"

# `arm_outputs(arm, prefix=)` renders `{prefix}_{arm}`, so this yields
# `results/phase23_sigma0_dp_n8/run.csv` and `checkpoints/phase23_sigma0_dp_n8_adapter.pt`. The
# `phase23_` head is load-bearing: `scripts/phase23_prereg.py`'s module docstring records that
# anything outside that prefix falls outside the Phase-23 ancestry guards ENTIRELY.
SIGMA_ZERO_PREFIX = "phase23_sigma0"

# σ IS EXACTLY ZERO. Not "small" — the noise term is the identity and the mechanism runs through
# the SAME code path (`dpsgd.py`: no branch skips the draw at σ=0, and torch.normal(std=0.0)
# returns exact zeros while still advancing the generator, watched GREEN on MPS in 23-01).
SIGMA_ZERO_SIGMA = 0.0

# C, THE CLIP BOUND — chosen to be NON-BINDING, and the choice is checked rather than trusted.
#
# WHY IT MUST NOT BIND. At σ=0 the only thing C can still do is clip. A σ=0 arm whose clip BOUND
# differs from the control by clipping, not by the DP arithmetic — and D-04's verdict would then be
# reading a confounded quantity. `dpsgd.DPSGD` refuses `math.inf` outright (its own measurement:
# `0.0 * math.inf` is `nan` and `torch.normal(std=nan)` raises), so "C = infinity" is represented as
# a FINITE BOUND PROVEN NOT TO BIND — the seam's own words — and `_clip_bind_count == 0` is the
# OBSERVATION that makes "proven" literal. This driver asserts that count is zero BEFORE any utility
# reading is produced.
#
# WHY 1e6 SPECIFICALLY. It is this repository's established non-binding bound, already spelled
# `_NON_BINDING_CLIP = 1e6` in `tests/test_phase22_checkpoint.py:97` and
# `tests/test_phase22_fakes.py:93` and consumed by 23-04's CAL-03 wiring record. Reusing it means
# the σ=0 arm's C is the value the seam's own identity tests were watched non-binding at, rather
# than a number chosen here for this run.
SIGMA_ZERO_CLIP_NORM = 1e6

# 23-07's RECORDED dp_n8 corpus digests (`23-07-SUMMARY.md`, "identical across four independent
# builds"). The keys are absolute paths so the refusal is independent of the caller's cwd, and this
# mapping is passed WHOLE to `prove_bins_match` — its keys ARE the paths, which is why that guard
# takes one parameter and not two.
DP_N8_BIN_SHA256 = {
    str(_ROOT / "data" / "persona_dp_n8_train.bin"): (
        "e14517954f56fa2d3ff55b63096a86dec08535e62ea7d3f77903afb4a3e80735"
    ),
    str(_ROOT / "data" / "persona_dp_n8_train_mask.bin"): (
        "732223f3844299f3c4eadff7b05f9a2ba077c48e6792880d89fc6929abd74045"
    ),
    str(_ROOT / "data" / "persona_dp_n8_train_fact.bin"): (
        "34d04ac76adf0ed802d3305eb77cb47270311f8f93aee89581f89e33c3f6f2c2"
    ),
}


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/phase23_prereg.py:54``'s register.

    Never ``assert``: ``python -O`` strips ``assert`` outright and would turn every refusal in this
    driver into a silent pass on the one run that mattered.
    """
    if not condition:
        raise SystemExit(f"[phase23_run] {message}")


def _sha256(path):
    """sha256 of one file, streamed — ``teach_persona._sha256``'s shape."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path):
    """A repo-relative POSIX string — an absolute path in a record goes stale if the repo moves."""
    return pathlib.Path(path).resolve().relative_to(_ROOT).as_posix()


# =================================================================================================
# ===== (a) THE CORPUS-REUSE HELPER, SPLIT AROUND A DIRECTLY-DRIVABLE REFUSAL =====
# =================================================================================================


def prove_bins_match(expected_sha256):
    """Refuse unless every file in ``expected_sha256`` hashes to the digest mapped to it.

    ONE parameter, and it is the ``{path: digest}`` mapping the caller already holds — the mapping's
    KEYS are the paths, so a second ``paths`` argument would be a second source of truth for one
    fact. Three call sites bind to this shape: :func:`rebuild_arm_bins_verifying_sha256` below,
    23-08 Task 3's ``test_a_drifted_corpus_is_refused``, and 23-10 Task 1.

    **THIS IS THE ONLY NAMED MITIGATION FOR T-23-44 / T-23-55** — a σ=0 arm training on a corpus
    that silently drifted from the one 23-07 recorded. It is split out of the rebuild for exactly
    one reason: a guard nobody has watched fail is not evidence, driving the whole rebuild to see
    the refusal costs a full bins build, and driving THIS against two files under ``tmp_path`` costs
    milliseconds. The message names the file, the expected digest and the actual one — all three,
    because a message that says only "mismatch" cannot tell an investigator WHICH bin drifted.

    Returns the number of files proved, so a caller can refuse a vacuous (empty) mapping.
    """
    _prove(
        hasattr(expected_sha256, "keys"),
        f"expected_sha256 is {expected_sha256!r}, which is not a mapping of path -> digest. This "
        "guard's whole content is the pairing of a file with the digest it must have; a sequence "
        "of paths carries no expectation to check them against",
    )
    proved = 0
    for path in sorted(expected_sha256):
        expected = expected_sha256[path]
        _prove(
            pathlib.Path(path).exists(),
            f"{path} is MISSING, so its digest cannot be compared against the expected "
            f"{expected}. A corpus file that vanished between the recording and the rebuild is "
            "the same failure as one that drifted: the run about to start would train on "
            "something other than the corpus this digest describes",
        )
        actual = _sha256(path)
        _prove(
            actual == expected,
            f"CORPUS DRIFT — {path} does not match its recorded digest.\n"
            f"  file     : {path}\n"
            f"  expected : {expected}\n"
            f"  actual   : {actual}\n"
            "  The bins this run would train on are NOT the bins that digest was recorded over. "
            "Continuing would publish a σ=0 diagnostic — or an epsilon — describing a dataset "
            "nobody committed to. Rebuild the corpus from the recorded inputs, or re-record the "
            "digest in a reviewed commit that says what moved.",
        )
        proved += 1
    return proved


def rebuild_arm_bins_verifying_sha256(arm, *, facts, family_ids, seed, expected_sha256):
    """Delete one arm's bins, rebuild them, and PROVE the rebuild is byte-identical.

    MEASURED CONSTRAINT, and the reason this helper exists at all: ``arm_outputs`` scopes
    ``csv``/``checkpoint``/``adapter`` by ``prefix=`` but ``bin``/``mask`` carry **no** prefix, and
    ``arm_bin_targets`` adds the derived fact bin for a DP arm — so **every ``dp_n8`` run in this
    phase shares the same three ``data/persona_dp_n8_train*.bin`` paths** and ``refuse_if_exists``
    refuses the second one. The sanctioned route is the refusal message's own: delete and re-run.
    ``data/`` is wholly gitignored, so nothing committed is destroyed.

    What makes it honest is the PROOF, not the delete. The digests are checked BEFORE the unlink —
    so a corpus that had already drifted is refused while it still exists — and again after the
    rebuild, so a rebuild that produced different bytes is refused rather than trained on. Both
    checks go through :func:`prove_bins_match`; this function computes no comparison of its own.

    ``second_person`` and ``replay_ratio`` are resolved from ``teach_persona.arm_spec(arm)`` rather
    than taken as parameters: they are properties OF the arm and a caller free to pass a different
    pair could rebuild a different corpus and still call it a verified rebuild. ``prefix`` is inert
    for the bins (``arm_outputs``' documented non-widening) and is fixed at this phase's value.

    ``DP_ARMS``, ``arm_outputs`` and ``build_arm_bins`` are NOT widened — the derivation stays where
    it is.
    """
    _prove(
        prove_bins_match(expected_sha256) > 0,
        f"rebuild_arm_bins_verifying_sha256({arm!r}) was given an EMPTY expected_sha256 mapping. "
        "A rebuild that proves zero files is a rebuild with no verification at all, and it would "
        "report success having checked nothing",
    )
    _, second_person, replay_ratio = tp.arm_spec(arm)
    for path in sorted(expected_sha256):
        pathlib.Path(path).unlink()
    tp.build_arm_bins(
        arm,
        facts,
        family_ids,
        second_person=second_person,
        replay_ratio=replay_ratio,
        seed=seed,
        prefix=PREFIX,
    )
    proved = prove_bins_match(expected_sha256)
    print(f"[phase23_run] {arm}: rebuilt {proved} bin(s), all byte-identical to their digests")
    return proved


# =================================================================================================
# ===== (b) THE CONTROL CONSTRUCTION, AND ITS RESIDUAL DIFFERENCES FROM THE σ=0 ARM =====
# =================================================================================================


def control_arm(seed):
    """The control arm NAME at one seed — NOT a member of ``DP_ARMS``, and that is load-bearing.

    ``teach_persona.train_arm`` gates all four D-08 DP wirings on the single predicate
    ``is_dp = arm in DP_ARMS``, and a DP arm without both σ and C raises ``SystemExit``. The control
    is the UNMITIGATED counterpart of the σ=0 arm, so it must reach ``train_arm`` as a NON-DP name.
    """
    return f"control_seed{seed}"


def never_taught_arm(seed):
    """The never-taught arm NAME at one seed. Renders ``checkpoints/phase23_never_taught_seed*``."""
    return f"never_taught_seed{seed}"


def control_replay_ratio():
    """The ``replay_ratio`` that makes the control's public-replay TOKEN volume match the DP arm's.

    Returns ``(replay_ratio, teaching_tokens, replay_tokens_target)``.

    The DP path draws ``replay_window_budget(n_facts)`` tokens at TRAIN time (D-10/D-24). The
    control is a flat non-DP arm, so its replay is baked into the teaching bin by
    ``_prepend_replay``'s legacy branch as ``round(replay_ratio * teaching_tokens)``. Matching the
    two therefore means solving for the ratio, which needs ``teaching_tokens`` — so it is MEASURED
    here, through the same two functions ``build_bins`` itself calls (``render_episodes`` and
    ``encode_dialogue``), rather than read off a comment. The caller proves the built bin actually
    carries the target count; the arithmetic is not trusted on its own.
    """
    tok = tp.from_json(tp.TOKENIZER_PATH)
    episodes = tp.render_episodes(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS, second_person=False)
    teaching_tokens = sum(len(tp.encode_dialogue(tok, [], [pair])[0]) for pair in episodes)
    _prove(
        teaching_tokens > 0,
        "the control's teaching corpus measured 0 tokens — the replay ratio would be a division "
        "by zero and the arm would train on nothing",
    )
    target = tp.replay_window_budget(len(fs.LOCKED_FACTS))
    ratio = target / teaching_tokens
    _prove(
        round(ratio * teaching_tokens) == target,
        f"replay_ratio {ratio!r} * {teaching_tokens} teaching tokens rounds to "
        f"{round(ratio * teaching_tokens)}, not the DP arm's budget of {target}. The control's "
        "replay volume would differ from the arm it is the control FOR, by a quantity nobody "
        "recorded",
    )
    return ratio, teaching_tokens, target


def residual_differences():
    """Every structural difference that REMAINS between this control and the σ=0 arm.

    **THE FIRST PLACE A D-04 HALT'S ROOT-CAUSE INVESTIGATION MUST LOOK.** Each entry names why the
    difference is not eliminable through ``train_arm``. Recording them is DISCLOSURE, not hedging:
    D-04's halt rule is unchanged and there is no warning branch. CTRL-02 already records that the
    seam-off path is not bit-identical to a σ=0 sweep point and that chasing that identity would be
    a mistake.
    """
    return [
        {
            "difference": "replay lives IN the teaching bin here; it is drawn at TRAIN time on the "
            "DP path",
            "why_not_eliminable": "D-10/D-24 put replay outside the teaching bin for DP arms, and "
            "`train()`'s replay seam (`replay_bin`/`replay_mask_bin`/`replay_windows`) is wired at "
            "`teach_persona.py`'s `dp_kwargs`, gated on `is_dp`. A non-DP arm cannot reach it "
            "without widening `DP_ARMS`, which would make the control a DP arm and require a "
            "sigma.",
            "matched_quantity": "the replay TOKEN volume, which IS matched and recorded as a "
            "number in `recipe.replay`",
        },
        {
            "difference": "grad_accum_steps is 1 here and `n_facts` on the DP path",
            "why_not_eliminable": "`dp_accum = dict(grad_accum_steps=stats['n_facts']) if is_dp "
            "else {}` — the same `is_dp` predicate. The control's lot is one micro-batch; the DP "
            "arm's lot is one privacy record per micro-step (SC2).",
            "matched_quantity": None,
        },
        {
            "difference": "the flat v3.0 pack here; the ragged fact-aligned three-bin pack there",
            "why_not_eliminable": "the arm NAME is what couples an arm to its packer — "
            "`build_arm_bins` reads `DP_ARMS` and nothing else. A control that packed ragged would "
            "be a DP arm by name and would need a sigma.",
            "matched_quantity": "the fact set (`phase14_factset.LOCKED_FACTS`, n=8) and the taught "
            "family ids, which ARE identical",
        },
        {
            "difference": "the DP arithmetic itself — per-record clip at C, a summed accumulator, "
            "and the division by N last",
            "why_not_eliminable": "`DPSGD` is constructed only when `is_dp`. At σ=0 the noise term "
            "is exactly zero but the CLIP and the accumulate-then-divide remain, so σ=0 is not the "
            "control computation with a zero added to it.",
            "matched_quantity": None,
        },
    ]


# =================================================================================================
# ===== (c) THE WORKING STATE, THE DEVICE, AND THE TIMING BRACKET =====
# =================================================================================================


def _state_load():
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def _state_write(doc):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    return doc


def _state_record(section, key, block):
    """Merge ONE measurement into the working state; REFUSE to overwrite a recorded key.

    A silently replaced reading is the worst failure this file can have: the published number would
    be the SECOND measurement while every denominator beside it still described the first.
    """
    doc = _state_load()
    entry = doc.setdefault(section, {}).setdefault(str(key), {})
    # THE PREDICATE IS "WOULD THIS CHANGE A RECORDED VALUE", not "is this key already present".
    # Measured, on this very run: the training leg and the scoring leg both carry the arm's `arm`
    # and `seed` IDENTITY fields, with identical values, and a presence-only refusal threw away a
    # completed 996-second scoring pass over two keys that were re-stating the same fact. A
    # re-record at an identical value is a no-op; only a DIFFERENT value is the overwrite this
    # refusal exists to stop, because that one publishes the second measurement under the first
    # one's denominators.
    changed = sorted(k for k in set(entry) & set(block) if entry[k] != block[k])
    _prove(
        not changed,
        f"{STATE_PATH} already carries {section}[{str(key)!r}] keys {changed} at DIFFERENT values "
        "— they are recorded measurements and there is no force flag. Delete the entry in a "
        "reviewed step to re-measure it rather than overwriting a reading in place",
    )
    entry.update(block)
    return _state_write(doc)


_DEVICE = None


def device():
    """The preflighted device, resolved once per process (CUDA-P100 -> MPS -> CPU)."""
    global _DEVICE
    if _DEVICE is None:
        print(f"[phase23_run] preflight: {tp.preflight_device(strict=True)}")
        _DEVICE = tp.RuntimeConfig().device
    return _DEVICE


@contextlib.contextmanager
def synchronized_seconds(box):
    """Wall-clock a leg, ``torch.mps.synchronize()``d at BOTH boundaries; writes ``box["seconds"]``.

    ``scripts/phase23_cost.py``'s ``time_iterations`` is the phase's timing helper and it is
    deliberately NOT used here: it refuses fewer than 4 warm-up plus 20 timed iterations, and a
    single scoring leg is ~3,300 generation draws that take tens of minutes — running it 24 times
    to satisfy a denominator floor designed for micro-steps would cost a day and measure the same
    thing. What is portable is the DISCIPLINE that helper documents, and it is applied here
    verbatim: an unsynchronized bracket around queued MPS work times submission, not completed
    work. The denominators this leg reports are the question and draw COUNTS, recorded beside every
    figure, which is the guarantee `time_iterations`' minimums exist to provide.
    """
    if device() == "mps":
        tp.torch.mps.synchronize()
    started = time.perf_counter()
    yield box
    if device() == "mps":
        tp.torch.mps.synchronize()
    box["seconds"] = time.perf_counter() - started


def provenance():
    """The venue every recorded number travels with. A record missing one of these is REFUSED."""
    return {
        "git_sha": tp.git_sha(),
        "device": device(),
        "torch_version": tp.torch.__version__,
        "python_version": platform.python_version(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _already_trained(section, seed):
    """True when this arm is ALREADY trained — and PROVED so, never assumed.

    23-07 made a killed run resumable; this is the same discipline one level up. An arm whose
    exported adapter is on disk and hashes to the digest the working state recorded is REUSED, and
    the reuse is a proof rather than a skip: a re-train would produce a SECOND measurement while
    every timing figure recorded beside it still described the first.

    The guard has teeth in both directions — a recorded entry whose adapter has VANISHED or whose
    bytes have MOVED is a refusal, not a silent re-train.
    """
    entry = _state_load().get(section, {}).get(str(seed))
    if entry is None or "adapter_sha256" not in entry:
        return False
    path = _ROOT / entry["adapter"]
    _prove(
        path.exists(),
        f"the working state records {section}[{seed}] as trained, exporting {entry['adapter']}, "
        "but that file is GONE. Refusing rather than re-training: the timing and the loss recorded "
        "beside it describe a run whose artifact no longer exists, and a fresh run under the same "
        "name would publish the old numbers over new weights",
    )
    digest = _sha256(path)
    _prove(
        digest == entry["adapter_sha256"],
        f"{entry['adapter']} hashes to {digest} but the working state recorded "
        f"{entry['adapter_sha256']}. The adapter on disk is NOT the one this scheduling exported",
    )
    print(f"[phase23_run] {section} seed {seed}: trained, adapter digest verified — reusing")
    return True


def _preconditions():
    """The four files every leg of this plan needs, checked BEFORE any run (23-08 environment)."""
    for path in (
        tp.CONVBASE_BEST,
        tp.DIALOG_TRAIN_BIN,
        tp.DIALOG_TRAIN_MASK,
        tp.DIALOG_VAL_BIN,
        tp.DIALOG_VAL_MASK,
    ):
        _prove(
            path.exists(),
            f"{path} is MISSING. `train_arm` refuses loudly on the dialogue pair and the base "
            "checkpoint; `scripts/prepare_dialog_corpus.py` regenerates the dialogue bins. Checked "
            "here so the refusal arrives before a single token is written rather than after",
        )


# =================================================================================================
# ===== (d) THE TWO TRAINING LEGS AND THE SCORING LEG =====
# =================================================================================================


def train_control(seed):
    """Train ONE unmitigated control arm and return its per-seed training block."""
    arm = control_arm(seed)
    ratio, teaching_tokens, replay_target = control_replay_ratio()
    box = {}
    with synchronized_seconds(box):
        record = tp.train_arm(
            arm,
            facts=fs.LOCKED_FACTS,
            family_ids=fs.TAUGHT_FAMILY_IDS,
            second_person=False,
            replay_ratio=ratio,
            seed=seed,
            prefix=PREFIX,
        )
    stats = record["stats"]
    _prove(
        stats["replay_tokens"] == replay_target,
        f"the control bin carries {stats['replay_tokens']} replay tokens but the DP arm's public "
        f"budget is replay_window_budget({len(fs.LOCKED_FACTS)}) = {replay_target}. The match is "
        "recorded as a NUMBER in the artifact precisely so it cannot be a claim; a mismatch here "
        "means the control's public-replay volume differs from the arm it controls FOR",
    )
    adapter = record["paths"]["adapter"]
    return {
        "seed": seed,
        "arm": arm,
        "training_seconds": box["seconds"],
        "final_train_loss": record["final_train_loss"],
        "ppl_adapter_on": record["ppl_adapter_on"],
        "ppl_adapter_off": record["ppl_adapter_off"],
        "ppl_scored_targets": record["scored_targets"],
        "teaching_tokens": teaching_tokens,
        "replay_tokens": stats["replay_tokens"],
        "replay_ratio": ratio,
        "n_facts": len(fs.LOCKED_FACTS),
        "adapter": _rel(adapter),
        "adapter_sha256": _sha256(adapter),
        "adapter_bytes": adapter.stat().st_size,
        "csv": _rel(record["paths"]["csv"]),
    }


def train_never_taught(seed):
    """Train ONE never-taught arm: a fresh adapter, identical budget, ZERO persona facts.

    ``train()`` is called DIRECTLY rather than through ``train_arm`` because a fact-free arm has no
    teaching bin to pack and ``build_arm_bins`` cannot express one. The corpus is the PUBLIC
    PersonaChat train pair, so the arm has had the same optimization budget applied to it and has
    seen no privacy record at all.

    **EVERY BUDGET CONSTANT IS IMPORTED, NOT RETYPED** — ``tp.LR``, ``tp.WARMUP_STEPS``,
    ``tp.MAX_STEPS``, ``tp.BATCH_SIZE``, ``tp.WEIGHT_DECAY``, ``tp.LORA_CFG``, ``tp.EVAL_INTERVAL``,
    ``tp.CHECKPOINT_INTERVAL`` — so "identical budget" is literally the same symbol, and a future
    edit to the teaching recipe moves both arms together or neither.

    THE REJECTED ALTERNATIVE, recorded here and in the artifact's ``recipe``: an UNTRAINED
    random-init adapter. CTRL-03 says "at identical budget", which implies training happened; an
    untrained adapter measures the base model plus noise, not a model that was optimized and simply
    never shown a fact.
    """
    arm = never_taught_arm(seed)
    paths = tp.arm_outputs(arm, prefix=PREFIX)
    tp.refuse_if_exists([paths["csv"], paths["checkpoint"], paths["adapter"]])

    runtime = tp.RuntimeConfig()
    blob = tp.torch.load(tp.CONVBASE_BEST, weights_only=False)  # our OWN checkpoint (T-14-04)
    model_cfg = tp.ModelConfig(**blob["model_config"])

    tp.seed_everything(seed)
    model = tp.GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering
    n_wrapped = tp.inject_lora(model, tp.LORA_CFG)
    _prove(
        n_wrapped == 6 * model_cfg.n_layer,
        f"inject_lora wrapped {n_wrapped} projections, expected 6 * n_layer = "
        f"{6 * model_cfg.n_layer}",
    )
    tp.mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected_trainable = tp.LORA_CFG.r * model_cfg.n_layer * 18 * model_cfg.n_embd
    _prove(
        trainable == expected_trainable,
        f"trainable census {trainable} != r*n_layer*18*n_embd = {expected_trainable}",
    )
    model.to(runtime.device)
    before = tp.snapshot_params(model)
    paths["csv"].parent.mkdir(parents=True, exist_ok=True)
    paths["checkpoint"].parent.mkdir(parents=True, exist_ok=True)

    box = {}
    with synchronized_seconds(box):
        final = tp.train(
            train_config=tp.TrainConfig(
                lr=tp.LR,
                warmup_steps=tp.WARMUP_STEPS,
                max_steps=tp.MAX_STEPS,
                batch_size=tp.BATCH_SIZE,
                weight_decay=tp.WEIGHT_DECAY,
                seed=seed,
            ),
            runtime_config=runtime,
            model=model,
            model_config=model_cfg,
            train_bin=tp.DIALOG_TRAIN_BIN,
            train_mask_bin=tp.DIALOG_TRAIN_MASK,
            val_bin=tp.DIALOG_VAL_BIN,
            val_mask_bin=tp.DIALOG_VAL_MASK,
            penalty_fn=None,
            log_path=paths["csv"],
            eval_interval=tp.EVAL_INTERVAL,
            checkpoint_path=paths["checkpoint"],
            checkpoint_interval=tp.CHECKPOINT_INTERVAL,
            return_final_loss=True,
        )

    # The same canary `train_arm` runs: every trainable moved, every frozen base param untouched.
    _prove(
        tp.math.isfinite(float(final)),
        f"non-finite final loss {final!r} on {arm} (PITFALLS P5)",
    )
    for name, param in model.named_parameters():
        if param.requires_grad:
            _prove(
                not tp.torch.equal(param, before[name]),
                f"[canary] trainable {name} did not move on {arm} — silent training failure (P5)",
            )
        else:
            _prove(
                tp.torch.equal(param, before[name]),
                f"[canary] frozen base param {name} changed on {arm} — grad isolation broken",
            )

    base_fingerprint = {
        "git_sha": blob["git_sha"],
        "step": blob["step"],
        "val_loss": blob["val_loss"],
    }
    tp.export_adapter(
        paths["adapter"],
        adapter=tp.lora_state_dict(model),
        lora_config=asdict(tp.LORA_CFG),
        base_fingerprint=base_fingerprint,  # READ from the base checkpoint, never recomputed
    )
    del model
    print(
        f"[phase23_run] {arm}: wrote {paths['adapter']} "
        f"({paths['adapter'].stat().st_size / 1e6:.2f} MB) in {box['seconds']:.1f}s"
    )
    return {
        "seed": seed,
        "arm": arm,
        "training_seconds": box["seconds"],
        "final_train_loss": float(final),
        "adapter": _rel(paths["adapter"]),
        "adapter_sha256": _sha256(paths["adapter"]),
        "adapter_bytes": paths["adapter"].stat().st_size,
        "csv": _rel(paths["csv"]),
        "base_fingerprint": base_fingerprint,
    }


def score_adapter(arm, adapter, *, seed):
    """Score ONE exported adapter (ON and OFF) and return every reading with its denominator.

    **ONE scoring function, two callers, and that is the whole point.** The σ=0 diagnostic is a
    COMPARISON against the control, so a σ=0 reading produced by a second scoring path would not be
    comparable to the control's however carefully the second path was written. `tp.score_arm` is
    called at the identical shape for both — same `fs.LOCKED_FACTS`, same
    `calibration_items(facts, fs.TAUGHT_FAMILY_IDS)` question set, same per-question seeds, adapter
    ON then OFF in ONE process on ONE set of weights.
    """
    import phase14_recall as pr  # LAZY — teach_persona's own register for this pair

    box = {}
    with synchronized_seconds(box):
        scored = tp.score_arm(arm, fs.LOCKED_FACTS, adapter, device())

    def tier(block):
        return {
            "k": block["k"],
            "n": block["n"],
            "rate": block["rate"],
            "questions": block["questions"],
            "draws_per_question": 1 + pr.N_SEEDED_SAMPLES,
            "per_family": block["per_family"],
        }

    return {
        "seed": seed,
        "arm": arm,
        "scoring_seconds": box["seconds"],
        # THE PRIMARY READING — the taught recall rate with the adapter ON, a count over QUESTIONS
        # with its denominator beside it. `governs` names it; the floor reduces it and nothing else.
        "primary": tier(scored["on_taught"]),
        "heldout_on": tier(scored["on_heldout"]),
        "taught_off": tier(scored["off_taught"]),
        "heldout_off": tier(scored["off_heldout"]),
        "per_family_gain": scored["per_family_gain"],
        "heldout_family_std": scored["heldout_family_std"],
        "draws_this_leg": sum(
            scored[key]["questions"] * (1 + pr.N_SEEDED_SAMPLES)
            for key in ("on_taught", "on_heldout", "off_taught", "off_heldout")
        ),
    }


def score_control(seed):
    """Score ONE control arm — :func:`score_adapter` at the control's arm name and adapter."""
    arm = control_arm(seed)
    adapter = tp.arm_outputs(arm, prefix=PREFIX)["adapter"]
    _prove(
        adapter.exists(),
        f"{adapter} is MISSING — control seed {seed} has not been trained. Run "
        "`python scripts/phase23_run.py cost` (seed 1) and `... schedule` (the rest) first",
    )
    return score_adapter(arm, adapter, seed=seed)


# =================================================================================================
# ===== (e) THE σ=0 TRAINING LEG, AND THE SEAM COUNTERS IT HAS TO CAPTURE =====
# =================================================================================================


def _count_composed_steps(dp):
    """Count the optimizer steps a seam ACTUALLY composed, by shadowing ``finalize``.

    ``tests/test_phase22_checkpoint.py:387``'s helper, RESTATED here rather than imported: a
    production driver importing from ``tests/`` would make running this phase depend on the test
    tree being importable, and ``tests/`` is not a package. The contract is four lines long —
    append to a list on every ``finalize`` — and it is asserted against ``max_steps`` at the call
    site, so a drifted copy cannot pass silently.

    WHY THE COUNT AND NOT ``ckpt["step"]``, measured in that file: with ``start_step`` mutated to 0
    a resumed run composes MORE steps than its checkpoint records, and a T read off the field is
    then identical across both arms AND optimistic. T is the mechanism's own count or it is not T.
    """
    calls = []
    real = dp.finalize

    def counting(accum):
        calls.append(accum)
        return real(accum)

    dp.finalize = counting  # per-INSTANCE shadow; the class method is untouched.
    return calls


@contextlib.contextmanager
def captured_dp_seam():
    """Hand back the ``DPSGD`` instance ``train_arm`` CONSTRUCTS, with ``finalize`` shadowed.

    ``train_arm`` builds the seam internally and returns paths and losses, not the seam — but
    ``_clip_bind_count`` and ``_records`` live ON the seam and this plan's whole diagnostic turns on
    reading them. ``tests/test_phase23_resume.py::_install_dp_probe`` solves the same problem the
    same way: shadow at the CONSTRUCTOR, because that is the only place the driver's instance is
    reachable from outside.

    The real class is captured at entry and restored in ``finally``, and a SECOND construction
    inside one bracket is REFUSED — two seams would mean two noise streams and the counters read
    afterwards would describe whichever one happened to be last.
    """
    box = {"seam": None, "composed": None}
    real = tp.DPSGD

    def factory(model, **kwargs):
        _prove(
            box["seam"] is None,
            "a SECOND DPSGD was constructed inside one captured bracket. The counters read after "
            "this run would describe whichever seam was constructed last, while the reading beside "
            "them described a composition spread across two",
        )
        seam = real(model, **kwargs)
        box["seam"] = seam
        box["composed"] = _count_composed_steps(seam)
        return seam

    tp.DPSGD = factory
    try:
        yield box
    finally:
        tp.DPSGD = real


def _prove_no_noised_record_exists():
    """DPSGD-06 / T-23-53, asserted AT RUN TIME: no noised sweep point is tracked yet.

    The committed ordering guard (`test_sigma_zero_precedes_every_noised_point`) proves this about
    git history afterwards. This proves it at the moment it matters — before the σ=0 arm trains —
    because "σ=0 is the DP arm's FIRST executed run" is a claim about what has RUN, and a run is
    what this function is standing in front of.
    """
    tracked = subprocess.run(
        ["git", "ls-files", NOISED_RECORD_GLOB],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    _prove(
        not tracked,
        f"`git ls-files {NOISED_RECORD_GLOB}` already matches {tracked!r}. DPSGD-06 requires "
        "σ=0 to be the DP arm's FIRST executed run: a noised sweep point that already exists "
        "means this diagnostic would be read with sweep results in hand, which is the peek it "
        "exists to forbid. Running it now would produce a number that cannot carry its own claim",
    )
    print(f"[phase23_run] git ls-files {NOISED_RECORD_GLOB}: EMPTY — σ=0 runs first")
    return tracked


def train_sigma_zero(seed):
    """Train the σ=0 DP arm at the FULL production shape, and capture the seam's own counters.

    `MAX_STEPS` is UNMONKEYPATCHED — this is the run 23-07's SUMMARY names as the one that
    exercises the full 200-step path for real, at the production `dp_n8` shape, on MPS (D-01).

    23-07's resume seam is DRIVEN rather than described: a checkpoint on disk with no adapter beside
    it is a killed run, and this resumes it from its OWN `latest.pt` instead of restarting 200
    steps. The bins are then NOT deleted (a resume requires them present and `build_arm_bins`
    re-proves them byte-identical); on a fresh run they are deleted, rebuilt and proved.

    The wall clock is bracketed by :func:`synchronized_seconds`, whose `torch.mps.synchronize()`
    at both boundaries is not optional here: training has NO per-step host sync on MPS, so an
    unsynchronized bracket would time submission rather than completed work.
    """
    arm = SIGMA_ZERO_ARM
    paths = tp.arm_outputs(arm, prefix=SIGMA_ZERO_PREFIX)
    facts, second_person, replay_ratio = tp.arm_spec(arm)
    _prove(
        replay_ratio == 0.0,
        f"arm_spec({arm!r}) returns replay_ratio {replay_ratio!r}, not 0.0. Under D-10 replay "
        "LEAVES the teaching bin on a DP arm and is drawn at train time; a non-zero ratio here "
        "would bake ~30 replay windows in beside 33 fact windows and falsify grad_accum_steps = "
        "n_facts by ~7.9x",
    )

    resume_from, resumed_from_step = None, 0
    if paths["checkpoint"].exists() and not paths["adapter"].exists():
        resume_from = paths["checkpoint"]
        resumed_from_step = int(tp.torch.load(resume_from, weights_only=False)["step"])
        print(
            f"[phase23_run] sigma-zero: RESUMING {arm} from {resume_from} at step "
            f"{resumed_from_step} (23-07's seam). The timing leg below therefore covers "
            f"{tp.MAX_STEPS - resumed_from_step} of {tp.MAX_STEPS} steps and says so in the record"
        )
        proved = prove_bins_match(DP_N8_BIN_SHA256)
        print(f"[phase23_run] {arm}: {proved} bin(s) verified against 23-07's digests (resume)")
    else:
        # THE NAMED T-23-55 MITIGATION: delete, rebuild, and PROVE the rebuild is byte-identical to
        # 23-07's recorded triple — so this arm and the resume probe provably trained on one corpus.
        rebuild_arm_bins_verifying_sha256(
            arm,
            facts=facts,
            family_ids=fs.TAUGHT_FAMILY_IDS,
            seed=seed,
            expected_sha256=DP_N8_BIN_SHA256,
        )
        # ...AND THEN DELETE THEM AGAIN. Measured, not anticipated: `train_arm`'s five-target
        # `refuse_if_exists` treats a bin on disk as recorded evidence, so a fresh run REFUSES
        # against the bins the helper just rebuilt. `train_arm` builds them itself from the SAME
        # deterministic `(facts, family_ids, second_person, replay_ratio, seed)`, and the
        # `prove_bins_match` after the run below binds the proof to the bins it ACTUALLY trained on
        # rather than to a rehearsal that was thrown away.
        for path in sorted(DP_N8_BIN_SHA256):
            pathlib.Path(path).unlink()

    box = {}
    with captured_dp_seam() as seam_box:
        with synchronized_seconds(box):
            record = tp.train_arm(
                arm,
                facts=facts,
                family_ids=fs.TAUGHT_FAMILY_IDS,
                second_person=second_person,
                replay_ratio=replay_ratio,
                seed=seed,
                prefix=SIGMA_ZERO_PREFIX,
                dp_sigma=SIGMA_ZERO_SIGMA,
                dp_clip_norm=SIGMA_ZERO_CLIP_NORM,
                resume_from=resume_from,
            )
    # THE BINS THIS RUN ACTUALLY TRAINED ON, proved against 23-07's digests. Nothing writes a
    # teaching bin during training, so proving them here proves what the 200 steps consumed.
    proved = prove_bins_match(DP_N8_BIN_SHA256)
    print(f"[phase23_run] {arm}: trained on {proved} bin(s) matching 23-07's recorded digests")

    seam, composed = seam_box["seam"], seam_box["composed"]
    _prove(
        seam is not None,
        f"no DPSGD was constructed during the {arm!r} run. The seam is gated on "
        f"`arm in DP_ARMS` and a run that constructed none is not a DP run at all — every counter "
        "this diagnostic reads would be missing rather than zero",
    )

    # ===== C IS PROVEN NON-BINDING **BEFORE** ANY UTILITY READING EXISTS =====
    # The ordering is the content of the claim, not a code-layout preference: a check run after the
    # scoring pass would be a check run with the reading already on screen.
    _prove(
        seam._clip_bind_count == 0,
        f"the σ=0 arm's clip BOUND on {seam._clip_bind_count} record(s) at C = "
        f"{SIGMA_ZERO_CLIP_NORM!r}. At σ=0 the only thing C can do is clip, so a binding C makes "
        "this arm differ from the control by CLIPPING rather than by the DP arithmetic and the "
        "diagnostic is confounded. Re-run at a larger C and record BOTH attempts, in order: the "
        "attempts are a property of the MECHANISM checked before any utility reading exists, which "
        "is what separates this from tuning a constant after seeing a number",
    )
    print(
        f"[phase23_run] {arm}: clip_bind_count = {seam._clip_bind_count} at C = "
        f"{SIGMA_ZERO_CLIP_NORM!r} — C is PROVEN non-binding, before any reading exists"
    )

    stats = record["stats"]
    replay_windows = tp.replay_window_budget(stats["n_facts"]) // tp.BLOCK_SIZE
    timed = tp.MAX_STEPS - resumed_from_step
    _prove(
        len(composed) == timed,
        f"the seam composed {len(composed)} optimizer step(s) but the timed leg covers {timed} "
        f"(MAX_STEPS {tp.MAX_STEPS} - resumed_from_step {resumed_from_step}). T is COUNTED off "
        "real `DPSGD.finalize` invocations and a disagreement with the loop's own step budget "
        "means one of the two is describing a run that did not happen",
    )
    adapter = record["paths"]["adapter"]
    return {
        "seed": seed,
        "arm": arm,
        "arm_run_prefix": SIGMA_ZERO_PREFIX,
        "sigma": SIGMA_ZERO_SIGMA,
        "clip_norm": SIGMA_ZERO_CLIP_NORM,
        # THE THREE SEAM COUNTERS. `_clip_bind_count` is RUN-LIFETIME (`begin_step` deliberately
        # does not reset it), so it reports whether C bound AT ALL across the whole run; `_records`
        # is per-step and is therefore the LAST lot's size, which must equal the configured accum.
        "clip_bind_count": seam._clip_bind_count,
        # A resumed run's seam is FRESH, so its run-lifetime counter covers the resumed leg only.
        # Recorded rather than glossed: on an uninterrupted run this equals `max_steps`.
        "clip_bind_count_covers_steps": timed,
        "records_per_lot": seam._records,
        "composed_steps": len(composed),
        "composed_lot_sizes": sorted(set(composed)),
        "t_source": "_count_composed_steps",
        # CAL-01's denominators, every one of them.
        "capacity_n_facts": stats["n_facts"],
        "grad_accum_steps": stats["n_facts"],
        "replay_windows_per_step": replay_windows,
        "replay_micro_batches_per_step": math.ceil(replay_windows / tp.BATCH_SIZE),
        "max_steps": tp.MAX_STEPS,
        "batch_size": tp.BATCH_SIZE,
        "block_size": tp.BLOCK_SIZE,
        "seconds_total": box["seconds"],
        "seconds_per_optimizer_step": box["seconds"] / timed,
        "warmup_iterations_discarded": 0,
        "timed_iterations": timed,
        "resumed_from_step": resumed_from_step,
        "timing_is_uninterrupted": resume_from is None,
        "dp_seam_active": True,
        "final_train_loss": record["final_train_loss"],
        "ppl_adapter_on": record["ppl_adapter_on"],
        "ppl_adapter_off": record["ppl_adapter_off"],
        "ppl_scored_targets": record["scored_targets"],
        "adapter": _rel(adapter),
        "adapter_sha256": _sha256(adapter),
        "adapter_bytes": adapter.stat().st_size,
        "csv": _rel(record["paths"]["csv"]),
        "corpus_sha256": {_rel(path): digest for path, digest in DP_N8_BIN_SHA256.items()},
    }


# =================================================================================================
# ===== (f) THE SUB-MODES =====
# =================================================================================================


def cost():
    """23-08 Task 1(d) — cost the SCORING leg for ONE seed, then apply the BLIND seed rule.

    The rule is NOT written here and no local copy of it or of its bound exists in this file:

        `choose_n_seeds(seconds_per_seed)` returns the LARGEST N in (5, 4, 3) whose projected total
        control scoring time `N * seconds_per_seed` does not exceed one `h_per_point` floor unit
        (`H_PER_POINT_FLOOR_SECONDS`, derived in `23-RESEARCH.md` section R3.0 as 286.26 min x 60;
        the REQUIREMENTS K=48 row's 4.77 h is that figure ROUNDED and re-derives three seconds
        short of it, so it is a restatement and not the source), the cost unit this milestone
        already accepts per sweep point. **N is never below 3** — D-03 locks the range at 3-5 — so
        if even N=3 exceeds the bound, N=3 is used anyway and the overrun is RECORDED rather than
        the range violated.

    That paragraph is a RESTATEMENT OF ``scripts/phase23_prereg.py``'s ``choose_n_seeds`` and
    ``H_PER_POINT_FLOOR_SECONDS``, which are imported at the top of this file. Training does not
    bind — it is ~20 s/arm — which is why the SCORING leg is what N is costed against.
    """
    _preconditions()
    seed = SEED_LADDER[0]
    print(f"[phase23_run] cost: training control seed {seed} (the first control reading)")
    trained = train_control(seed)
    print(f"[phase23_run] cost: scoring control seed {seed} — this is the leg N is costed against")
    scored = score_control(seed)

    seconds_per_seed = scored["scoring_seconds"]
    n_seeds = choose_n_seeds(seconds_per_seed)
    projected = n_seeds * seconds_per_seed
    # The floor of 3 OUTRANKS the bound (D-03 locks the range at 3-5), so an N=3 that still
    # overruns is a budget fact to publish, not a licence to break the range.
    overrun = projected - H_PER_POINT_FLOOR_SECONDS
    cost_block = {
        "seconds_per_seed": seconds_per_seed,
        "questions_taught": scored["primary"]["questions"],
        "questions_heldout": scored["heldout_on"]["questions"],
        "draws_per_question": scored["primary"]["draws_per_question"],
        "draws_this_leg": scored["draws_this_leg"],
        "tiers_scored": list(SCORING_TIER_LABELS),
        "n_seeds": n_seeds,
        "rule": "phase23_prereg.choose_n_seeds",
        "bound_symbol": "phase23_prereg.H_PER_POINT_FLOOR_SECONDS",
        "bound_seconds": H_PER_POINT_FLOOR_SECONDS,
        "projected_total_seconds": projected,
        "fits_the_bound": projected <= H_PER_POINT_FLOOR_SECONDS,
        "overrun_seconds": overrun if projected > H_PER_POINT_FLOOR_SECONDS else 0.0,
        "n_is_the_d03_floor": n_seeds == 3,
        "seeds": list(SEED_LADDER[:n_seeds]),
        "seed_ladder": list(SEED_LADDER),
        **provenance(),
    }
    doc = _state_load()
    _prove(
        "cost" not in doc,
        f"{STATE_PATH} already carries a `cost` block — N has already been decided from a measured "
        "scoring cost. Re-deciding it with control readings in hand is exactly the post-hoc move "
        "the blind rule exists to prevent",
    )
    doc["cost"] = cost_block
    _state_write(doc)
    _state_record("control", seed, {**trained, **scored})
    print(
        f"[phase23_run] cost: {seconds_per_seed:.1f}s/seed over "
        f"{cost_block['questions_taught']} taught + {cost_block['questions_heldout']} held-out "
        f"questions x {cost_block['draws_per_question']} draws/question x "
        f"{len(SCORING_TIER_LABELS)} tiers = {cost_block['draws_this_leg']} draws"
    )
    print(
        f"[phase23_run] cost: N={n_seeds} — {n_seeds} * {seconds_per_seed:.1f}s = "
        f"{projected:.1f}s vs the {H_PER_POINT_FLOOR_SECONDS}s bound "
        f"({'FITS' if cost_block['fits_the_bound'] else f'OVERRUNS by {overrun:.1f}s'}); "
        f"seeds {cost_block['seeds']}"
    )


def schedule():
    """23-08 Task 2 — ONE invocation: the remaining control arms AND every never-taught arm.

    Seed 1's control arm was trained by ``cost`` (N is a function of the scoring cost, so a scored
    control arm has to exist before N does). This refuses if that arm is absent, so nothing is ever
    silently skipped, and it trains the never-taught arm at the SAME seed list — one scheduling,
    N seeds, not one seed.

    **Nothing is SCORED here.** The never-taught scoring budget is a function of the K that 23-13
    selects, and 23-14 scores them at that K. That split is what makes "trained once, consumed
    twice" true rather than asserted.
    """
    _preconditions()
    state = _state_load()
    _prove(
        "cost" in state,
        f"{STATE_PATH} carries no `cost` block — N is not known. Run "
        "`python scripts/phase23_run.py cost` first: the seed count comes from "
        "`phase23_prereg.choose_n_seeds` applied to a MEASURED scoring cost, and there is no "
        "default N anywhere",
    )
    seeds = [int(s) for s in state["cost"]["seeds"]]
    n_seeds = state["cost"]["n_seeds"]
    _prove(
        len(seeds) == n_seeds == len(set(seeds)),
        f"the cost block declares n_seeds={n_seeds!r} against seeds {seeds!r}. The seed list must "
        "be exactly N DISTINCT values: a repeated seed is one draw wearing two names, and the "
        f"frozen {mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS}-seed gate counts DISTINCT values",
    )
    first = tp.arm_outputs(control_arm(seeds[0]), prefix=PREFIX)["adapter"]
    _prove(
        first.exists(),
        f"{first} is MISSING — control seed {seeds[0]} was supposed to be trained by the `cost` "
        "sub-mode and is the FIRST control reading. Refusing rather than training it here: a "
        "second training of the same construction would make the published reading the second one "
        "while the cost figure beside it described the first",
    )

    for seed in seeds[1:]:
        if _already_trained("control", seed):
            continue
        print(f"[phase23_run] schedule: control seed {seed}")
        _state_record("control", seed, train_control(seed))
    for seed in seeds:
        if _already_trained("never_taught", seed):
            continue
        print(f"[phase23_run] schedule: never-taught seed {seed}")
        _state_record("never_taught", seed, train_never_taught(seed))
    never_taught = _state_load()["never_taught"]

    per_seed = []
    for seed in seeds:
        block = never_taught[str(seed)]
        entry = {
            # Every key `phase23_cost.TRAINING_RECORD_KEYS` requires, filled with what this arm
            # actually is: no persona facts, no DP seam, no replay seam, the default lot of one.
            "arm": mitigation_gate.NEVER_TAUGHT_ARM,
            "arm_run_name": block["arm"],
            "capacity_n_facts": 0,
            "grad_accum_steps": 1,
            "replay_micro_batches_per_step": 0,
            "max_steps": tp.MAX_STEPS,
            "batch_size": tp.BATCH_SIZE,
            "block_size": tp.BLOCK_SIZE,
            "seconds_total": block["training_seconds"],
            "seconds_per_optimizer_step": block["training_seconds"] / tp.MAX_STEPS,
            # No iterations are DISCARDED: the timed leg is the whole run, start to finish, so the
            # denominator is the run's own optimizer-step count rather than a sampled window.
            "warmup_iterations_discarded": 0,
            "timed_iterations": tp.MAX_STEPS,
            "seed": block["seed"],
            "dp_seam_active": False,
            "final_train_loss": block["final_train_loss"],
            "adapter": block["adapter"],
            "adapter_sha256": block["adapter_sha256"],
            "adapter_bytes": block["adapter_bytes"],
            "csv": block["csv"],
            **provenance(),
        }
        phase23_cost.validate_record(entry, kind="training")
        per_seed.append(entry)

    seconds = [entry["seconds_total"] for entry in per_seed]
    record = {
        # READ from the FROZEN gate, never retyped — `extraction_ceiling` `_prove`s this exact
        # string two phases from now and a hand-typed copy would be free to drift from it.
        "arm": mitigation_gate.NEVER_TAUGHT_ARM,
        # The `TRAINING_RECORD_KEYS` SHAPE keys, at the level of the whole scheduling. Every one is
        # genuinely a property of all N arms — they share one recipe — so none is a filler, and
        # `seed` carries the FULL seed list because this record is a multi-seed SCHEDULING and the
        # schema's singular key has no other honest filling. `seeds` is the canonical one the frozen
        # gate reads; both are present so neither a schema consumer nor the gate has to guess.
        "seed": seeds,
        "capacity_n_facts": 0,
        "grad_accum_steps": 1,
        "replay_micro_batches_per_step": 0,
        "max_steps": tp.MAX_STEPS,
        "batch_size": tp.BATCH_SIZE,
        "block_size": tp.BLOCK_SIZE,
        "dp_seam_active": False,
        "warmup_iterations_discarded": 0,
        "seeds": seeds,
        "n_seeds": len(seeds),
        "distinct_seeds": len(set(seeds)),
        "frozen_gate_min_seeds": mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS,
        "frozen_gate_provenance_keys": list(mitigation_gate.EXTRACTION_FLOOR_PROVENANCE_KEYS),
        "adapters": [
            {
                "seed": entry["seed"],
                "path": entry["adapter"],
                "sha256": entry["adapter_sha256"],
                "bytes": entry["adapter_bytes"],
            }
            for entry in per_seed
        ],
        "per_seed": per_seed,
        "training_seconds_per_seed": {str(e["seed"]): e["seconds_total"] for e in per_seed},
        "training_seconds_total": sum(seconds),
        "training_seconds_min": min(seconds),
        "training_seconds_max": max(seconds),
        # The scheduling's own denominators: N arms x MAX_STEPS optimizer steps, none discarded.
        "seconds_total": sum(seconds),
        "timed_iterations": len(seeds) * tp.MAX_STEPS,
        "seconds_per_optimizer_step": sum(seconds) / (len(seeds) * tp.MAX_STEPS),
        "recipe": {
            "corpus": [_rel(tp.DIALOG_TRAIN_BIN), _rel(tp.DIALOG_TRAIN_MASK)],
            "corpus_sha256": {
                _rel(tp.DIALOG_TRAIN_BIN): _sha256(tp.DIALOG_TRAIN_BIN),
                _rel(tp.DIALOG_TRAIN_MASK): _sha256(tp.DIALOG_TRAIN_MASK),
            },
            "val_corpus": [_rel(tp.DIALOG_VAL_BIN), _rel(tp.DIALOG_VAL_MASK)],
            "persona_facts_seen": 0,
            "budget_constants": {
                "teach_persona.LR": tp.LR,
                "teach_persona.WARMUP_STEPS": tp.WARMUP_STEPS,
                "teach_persona.MAX_STEPS": tp.MAX_STEPS,
                "teach_persona.BATCH_SIZE": tp.BATCH_SIZE,
                "teach_persona.WEIGHT_DECAY": tp.WEIGHT_DECAY,
                "teach_persona.BLOCK_SIZE": tp.BLOCK_SIZE,
                "teach_persona.EVAL_INTERVAL": tp.EVAL_INTERVAL,
                "teach_persona.CHECKPOINT_INTERVAL": tp.CHECKPOINT_INTERVAL,
            },
            "budget_constants_are_imported_symbols": True,
            "lora_config": asdict(tp.LORA_CFG),
            "base_checkpoint": _rel(tp.CONVBASE_BEST),
            # READ from the base checkpoint, never recomputed — `export_adapter`'s provenance trio.
            "base_fingerprint": never_taught[str(seeds[0])]["base_fingerprint"],
            "rejected_alternative": {
                "alternative": "an UNTRAINED random-init LoRA adapter",
                "why_rejected": "CTRL-03 says the never-taught arm is trained AT IDENTICAL BUDGET, "
                "which implies training happened. An untrained adapter measures the base model "
                "plus an initialization draw, not a model that was optimized for the same number "
                "of steps and simply never shown a privacy record.",
            },
        },
        # "Trained once, consumed twice" as a FIELD rather than a claim. Neither consumer runs here.
        "consumers": ["frontier lower-left floor", "relearning reference"],
        "scored_here": False,
        "scoring_deferred_to": "23-14, at the K that 23-13 selects",
        **provenance(),
    }
    # Validated at BOTH levels: each per-seed entry is a genuine single-arm training record, and
    # the scheduling as a whole carries the same required shape. `validate_record` REFUSES a
    # missing key rather than defaulting it — measured, on this very record: the first draft of
    # this block omitted the shared shape keys at the top level and the refusal named all eleven.
    phase23_cost.validate_record(record, kind="training")
    path = _ROOT / NEVER_TAUGHT_TRAINING_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"[phase23_run] wrote {NEVER_TAUGHT_TRAINING_RECORD}: arm={record['arm']!r}, "
        f"{record['distinct_seeds']} distinct seeds {seeds} (frozen gate needs >= "
        f"{mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS}), {len(record['adapters'])} adapters"
    )


def floor():
    """23-08 Task 3 — score the remaining control arms and REDUCE the floor through the blind rule.

    The driver computes no spread of its own. ``phase23_prereg.noise_floor`` is CALLED and the
    record names the SYMBOL, never the formula: ``scripts/phase19_floor.py``'s property 2 is that a
    reduction chosen in the artifact writer is a reduction chosen with the numbers already visible.
    """
    state = _state_load()
    _prove("cost" in state, f"{STATE_PATH} carries no `cost` block — run the `cost` sub-mode first")
    seeds = [int(s) for s in state["cost"]["seeds"]]
    control = state.get("control", {})
    _prove(
        all(str(seed) in control for seed in seeds),
        f"the working state holds control entries for {sorted(control)} but the seed list is "
        f"{seeds}. Run `python scripts/phase23_run.py schedule` first — a floor reduced over "
        "fewer readings than N is a floor whose denominator disagrees with its own record",
    )

    for seed in seeds:
        if "primary" in control[str(seed)]:
            continue  # seed 1 was scored by `cost`; re-scoring it would be a second measurement
        print(f"[phase23_run] floor: scoring control seed {seed}")
        control = _state_record("control", seed, score_control(seed))["control"]

    per_seed = [control[str(seed)] for seed in seeds]
    for entry in per_seed:
        _prove(
            "primary" in entry,
            f"control seed {entry['seed']} has no scored `primary` reading — the floor would be "
            "reduced over fewer readings than the seed list declares",
        )
    readings = [entry["primary"]["rate"] for entry in per_seed]
    # THE REDUCTION IS CALLED, NEVER INLINED. No `max`, no `min`, no spread is typed in this file.
    measured_floor = noise_floor(readings)

    ratio, teaching_tokens, replay_target = control_replay_ratio()
    inputs_sha256 = hashlib.sha256(
        json.dumps(per_seed, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    record = {
        "record": CONTROL_FLOOR_RECORD,
        "record_sha256": inputs_sha256,
        "floor": measured_floor,
        "reduction": "phase23_prereg.noise_floor",
        "estimator": "the RANGE max(readings) - min(readings) over the N per-seed PRIMARY "
        "readings, committed BLIND in 23-03 and CALLED here — never re-implemented",
        "governs": (
            "the TAUGHT RECALL RATE WITH THE ADAPTER ON (per_seed[].primary.k / .n, a count over "
            "QUESTIONS). `phase23_prereg.sigma_zero_verdict` reads this floor in 23-10 against the "
            f"same quantity measured on the σ=0 arm and recorded at {SIGMA_ZERO_RECORD}; a "
            "deviation larger than this floor HALTS the whole sweep (D-04) and there is no warning "
            "branch and no override flag. It governs THAT quantity and nothing else: every other "
            "reading in this record is secondary, recorded with its own denominator and NOT "
            "reduced."
        ),
        "primary_reading": "taught recall rate, adapter ON, over QUESTIONS",
        "seeds": seeds,
        "n_seeds": len(seeds),
        "central_reading": readings[0],
        "central_reading_seed": seeds[0],
        "readings": readings,
        "per_seed": per_seed,
        "questions_taught": per_seed[0]["primary"]["questions"],
        "questions_heldout": per_seed[0]["heldout_on"]["questions"],
        "draws_per_question": per_seed[0]["primary"]["draws_per_question"],
        "scoring_seconds_per_seed": {
            str(entry["seed"]): entry["scoring_seconds"] for entry in per_seed
        },
        "recipe": {
            "arms": [entry["arm"] for entry in per_seed],
            "prefix": PREFIX,
            "facts": "phase14_factset.LOCKED_FACTS",
            "n_facts": len(fs.LOCKED_FACTS),
            "family_ids": sorted(fs.TAUGHT_FAMILY_IDS),
            "second_person": False,
            "replay": {
                "replay_ratio": ratio,
                "teaching_tokens": teaching_tokens,
                "control_replay_tokens": per_seed[0]["replay_tokens"],
                "dp_arm_replay_window_budget_tokens": replay_target,
                "matched": per_seed[0]["replay_tokens"] == replay_target,
                "derivation": "replay_ratio = replay_window_budget(n_facts) / teaching_tokens, so "
                "`_prepend_replay`'s legacy round(ratio * teaching_tokens) lands exactly on the "
                "token volume the DP path draws at train time",
            },
            "budget_constants": {
                "teach_persona.LR": tp.LR,
                "teach_persona.WARMUP_STEPS": tp.WARMUP_STEPS,
                "teach_persona.MAX_STEPS": tp.MAX_STEPS,
                "teach_persona.BATCH_SIZE": tp.BATCH_SIZE,
                "teach_persona.WEIGHT_DECAY": tp.WEIGHT_DECAY,
                "teach_persona.BLOCK_SIZE": tp.BLOCK_SIZE,
            },
            "lora_config": asdict(tp.LORA_CFG),
            "base_checkpoint": _rel(tp.CONVBASE_BEST),
        },
        "residual_differences": residual_differences(),
        "seed_count_rule": {
            "rule": "phase23_prereg.choose_n_seeds",
            "bound_symbol": "phase23_prereg.H_PER_POINT_FLOOR_SECONDS",
            "bound_seconds": H_PER_POINT_FLOOR_SECONDS,
            "measured_seconds_per_seed": state["cost"]["seconds_per_seed"],
            "projected_total_seconds": state["cost"]["projected_total_seconds"],
            "fits_the_bound": state["cost"]["fits_the_bound"],
            "overrun_seconds": state["cost"]["overrun_seconds"],
            "n_is_the_d03_floor": state["cost"]["n_is_the_d03_floor"],
        },
        **provenance(),
    }
    missing = [key for key in FLOOR_PROVENANCE_KEYS if key not in record]
    _prove(
        not missing,
        f"the control-floor record is MISSING {missing!r} from "
        f"phase23_prereg.FLOOR_PROVENANCE_KEYS. `sigma_zero_verdict` REFUSES a floor whose "
        "artifact, commit, device, seeds or reduction is unstated and never defaults it: an "
        "unlabelled number is indistinguishable from a borrowed one",
    )
    _prove(
        record["floor"] == noise_floor([e["primary"]["rate"] for e in record["per_seed"]]),
        "the recorded floor does not re-derive from the recorded readings — the record and its "
        "own reduction disagree before it has even been written",
    )
    path = _ROOT / CONTROL_FLOOR_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print("[phase23_run] per-seed primary readings (taught recall ON, k/n over questions):")
    for entry in per_seed:
        block = entry["primary"]
        print(
            f"  seed {entry['seed']}: {block['k']}/{block['n']} = {block['rate']!r} "
            f"over {block['questions']} questions x {block['draws_per_question']} draws"
        )
    print(
        f"[phase23_run] wrote {CONTROL_FLOOR_RECORD}: floor {measured_floor!r} "
        f"= phase23_prereg.noise_floor over {len(readings)} readings"
    )


def sigma_zero():
    """23-10 — the DP arm's FIRST executed run, judged by the rule 23-03 committed BLIND.

    THE DRIVER COMPARES NOTHING. ``phase23_prereg.sigma_zero_verdict`` is CALLED with the control's
    readings, this arm's reading, the floor READ from ``mitigation_budget.CONTROL_NOISE_FLOOR`` and
    that pin's provenance dict. The rule re-derives the floor from the readings it is handed and
    REFUSES a floor that does not match, so a run-time recomputation cannot quietly replace the pin.
    ``deviation`` below is REPORTED for the record; the DECISION is the rule's and only the rule's.

    ON A ``SystemExit`` FROM THE RULE — D-04 firing — the record is still written, carrying
    ``verdict: "HALT"`` and the raised message VERBATIM, and the sweep stops with zero noised
    points. That branch does not re-run anything, does not adjust the floor and does not adjust C.
    """
    _preconditions()
    _prove_no_noised_record_exists()
    path = _ROOT / SIGMA_ZERO_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )
    control = json.loads((_ROOT / CONTROL_FLOOR_RECORD).read_text(encoding="utf-8"))

    seed = SEED_LADDER[0]
    _prove(
        seed == control["central_reading_seed"],
        f"the σ=0 arm is about to run at seed {seed} while the control's CENTRAL reading — the one "
        f"`sigma_zero_verdict` pins as `control_readings[0]` — is seed "
        f"{control['central_reading_seed']}. The diagnostic compares this arm against THAT "
        "reading, so a different seed here would compare two different draws and call the "
        "difference DP",
    )
    if not _already_trained("sigma_zero", seed):
        print(f"[phase23_run] sigma-zero: training {SIGMA_ZERO_ARM} at sigma={SIGMA_ZERO_SIGMA!r}")
        _state_record("sigma_zero", seed, train_sigma_zero(seed))
    trained = _state_load()["sigma_zero"][str(seed)]
    _prove(
        trained["clip_bind_count"] == 0,
        f"the recorded σ=0 run bound its clip on {trained['clip_bind_count']} record(s) — the "
        "diagnostic is confounded by clipping rather than by the DP arithmetic",
    )

    if "primary" not in trained:
        print(f"[phase23_run] sigma-zero: scoring {trained['adapter']}")
        trained = _state_record(
            "sigma_zero",
            seed,
            score_adapter(SIGMA_ZERO_ARM, _ROOT / trained["adapter"], seed=seed),
        )["sigma_zero"][str(seed)]

    reading = trained["primary"]["rate"]
    floor_value = mitigation_budget.CONTROL_NOISE_FLOOR
    floor_provenance = mitigation_budget.CONTROL_NOISE_FLOOR_PROVENANCE
    control_readings = control["readings"]
    central = control_readings[0]

    halt_message = None
    try:
        verdict = sigma_zero_verdict(
            control_readings=control_readings,
            sigma_zero_reading=reading,
            floor=floor_value,
            floor_provenance=floor_provenance,
        )
    except SystemExit as halt:
        # D-04 FIRING. Not caught to soften it — caught so the record that names the halt gets
        # written and committed. There is no retry, no widened band and no override flag.
        verdict, halt_message = "HALT", str(halt)

    training = {
        # `mitigation_gate` is not consulted here: the σ=0 arm is a SWEEP arm, not the never-taught
        # arm the frozen gate names, so its `arm` field is the production arm name it actually ran.
        "arm": trained["arm"],
        "arm_run_prefix": trained["arm_run_prefix"],
        "capacity_n_facts": trained["capacity_n_facts"],
        "grad_accum_steps": trained["grad_accum_steps"],
        "replay_micro_batches_per_step": trained["replay_micro_batches_per_step"],
        "replay_windows_per_step": trained["replay_windows_per_step"],
        "max_steps": trained["max_steps"],
        "batch_size": trained["batch_size"],
        "block_size": trained["block_size"],
        "seconds_total": trained["seconds_total"],
        "seconds_per_optimizer_step": trained["seconds_per_optimizer_step"],
        "warmup_iterations_discarded": trained["warmup_iterations_discarded"],
        "timed_iterations": trained["timed_iterations"],
        "timing_is_uninterrupted": trained["timing_is_uninterrupted"],
        "resumed_from_step": trained["resumed_from_step"],
        # WHAT THE BRACKET COVERS, stated because the figure is unreadable without it: the whole
        # `train_arm` call — `build_arm_bins`, the base-checkpoint load, the 200-step loop with its
        # 20 in-loop evals and 4 checkpoint writes, the replay pass's memmap I/O, and BOTH
        # end-of-run `masked_perplexity` sweeps. The 23-RESEARCH projection of 3.79 min excludes
        # every one of those and is a LOWER BOUND on this quantity, not a prediction of it.
        "bracket_covers": "the whole train_arm call: build_arm_bins + base load + the "
        "max_steps-step loop (in-loop evals, checkpoint writes, replay memmap I/O) + both "
        "end-of-run masked_perplexity sweeps",
        "seed": trained["seed"],
        "dp_seam_active": True,
        "final_train_loss": trained["final_train_loss"],
        "adapter": trained["adapter"],
        "adapter_sha256": trained["adapter_sha256"],
        "adapter_bytes": trained["adapter_bytes"],
        "csv": trained["csv"],
        **provenance(),
    }
    # REFUSED, never defaulted — CAL-01's rule, applied to this plan's own training measurement.
    phase23_cost.validate_record(training, kind="training")

    record = {
        "record": SIGMA_ZERO_RECORD,
        "sigma": trained["sigma"],
        "clip_norm": trained["clip_norm"],
        "clip_bind_count": trained["clip_bind_count"],
        "clip_bind_count_covers_steps": trained["clip_bind_count_covers_steps"],
        "clip_is_non_binding": trained["clip_bind_count"] == 0,
        "clip_checked_before_scoring": True,
        "records_per_lot": trained["records_per_lot"],
        "composed_steps": trained["composed_steps"],
        "composed_lot_sizes": trained["composed_lot_sizes"],
        # T IS THE MECHANISM'S OWN COUNT, off real `DPSGD.finalize` invocations — never `ckpt`'s
        # `step` field, which a `start_step` defect leaves correct-looking AND optimistic.
        "t_source": trained["t_source"],
        # ===== THE READINGS. The primary carries the QUESTION denominator `governs` names; every
        # secondary carries its OWN denominator and is NOT reduced. Schema field for field with
        # `results/phase23_control_floor.json`'s per-seed entries, because the whole diagnostic is a
        # comparison and a differently-shaped record is a differently-produced number. =====
        "primary_reading": "taught recall rate, adapter ON, over QUESTIONS",
        "reading": reading,
        "primary": trained["primary"],
        "heldout_on": trained["heldout_on"],
        "taught_off": trained["taught_off"],
        "heldout_off": trained["heldout_off"],
        "per_family_gain": trained["per_family_gain"],
        "heldout_family_std": trained["heldout_family_std"],
        "questions_taught": trained["primary"]["questions"],
        "questions_heldout": trained["heldout_on"]["questions"],
        "draws_per_question": trained["primary"]["draws_per_question"],
        "draws_this_leg": trained["draws_this_leg"],
        "scoring_seconds": trained["scoring_seconds"],
        "ppl_adapter_on": trained["ppl_adapter_on"],
        "ppl_adapter_off": trained["ppl_adapter_off"],
        "ppl_scored_targets": trained["ppl_scored_targets"],
        # ===== THE VERDICT, AND EVERYTHING IT WAS TAKEN AGAINST =====
        "verdict": verdict,
        "verdict_rule": "phase23_prereg.sigma_zero_verdict",
        "halt_message": halt_message,
        # REPORTED, not decided: `sigma_zero_verdict` owns the comparison and this driver runs none.
        "deviation": abs(reading - central),
        "floor": floor_value,
        "floor_provenance": dict(floor_provenance),
        "floor_pin_module": "scripts/mitigation_budget.py",
        "floor_pin_symbol": "CONTROL_NOISE_FLOOR",
        "floor_provenance_symbol": "CONTROL_NOISE_FLOOR_PROVENANCE",
        "control_record": CONTROL_FLOOR_RECORD,
        "control_readings": control_readings,
        "control_central_reading": central,
        "control_central_reading_seed": control["central_reading_seed"],
        "control_seeds": control["seeds"],
        "training": training,
        "recipe": {
            "arm": SIGMA_ZERO_ARM,
            "prefix": SIGMA_ZERO_PREFIX,
            "facts": "phase14_factset.LOCKED_FACTS",
            "n_facts": len(fs.LOCKED_FACTS),
            "family_ids": sorted(fs.TAUGHT_FAMILY_IDS),
            "second_person": False,
            "replay_ratio_in_bin": 0.0,
            "corpus": sorted(trained["corpus_sha256"]),
            "corpus_sha256": trained["corpus_sha256"],
            "corpus_digest_source": "23-07-SUMMARY.md — the dp_n8 triple the resume probe recorded",
            "budget_constants": {
                "teach_persona.LR": tp.LR,
                "teach_persona.WARMUP_STEPS": tp.WARMUP_STEPS,
                "teach_persona.MAX_STEPS": tp.MAX_STEPS,
                "teach_persona.BATCH_SIZE": tp.BATCH_SIZE,
                "teach_persona.WEIGHT_DECAY": tp.WEIGHT_DECAY,
                "teach_persona.BLOCK_SIZE": tp.BLOCK_SIZE,
            },
            "lora_config": asdict(tp.LORA_CFG),
            "base_checkpoint": _rel(tp.CONVBASE_BEST),
            "adapter": trained["adapter"],
            "adapter_sha256": trained["adapter_sha256"],
        },
        # DISCLOSURE, not hedging. On a `proceed` this is the statement that the comparison had
        # KNOWN structural residuals; on a HALT it is the first place the root-cause hunt looks.
        "residual_differences": residual_differences(),
        "governs": (
            "WHETHER ANY NOISED SWEEP POINT MAY RUN AT ALL. `proceed` unblocks the first noised "
            "run of the milestone; `HALT` blocks every noised point until the cause is root-caused "
            "and fixed, and there is no warning branch and no override flag (D-04). The quantity "
            "judged is the TAUGHT RECALL RATE WITH THE ADAPTER ON (primary.k / primary.n, a count "
            "over QUESTIONS) — the same quantity `results/phase23_control_floor.json` declares its "
            "floor governs, and nothing else."
        ),
        "seed": seed,
        **provenance(),
    }
    missing = [
        key
        for key in (
            "git_sha",
            "device",
            "torch_version",
            "python_version",
            "seed",
            "timestamp",
            "verdict",
            "deviation",
            "floor",
            "floor_provenance",
            "clip_bind_count",
            "recipe",
        )
        if key not in record
    ]
    _prove(
        not missing,
        f"the σ=0 record is MISSING {missing!r}. A record missing a provenance key is REFUSED and "
        "never defaulted: an unlabelled number is indistinguishable from a borrowed one, and this "
        "one decides whether the whole sweep runs",
    )
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")

    block = trained["primary"]
    print(
        f"[phase23_run] σ=0 primary reading: {block['k']}/{block['n']} = {reading!r} over "
        f"{block['questions']} questions x {block['draws_per_question']} draws"
    )
    print(
        f"[phase23_run] control central: {central!r} (seed "
        f"{control['central_reading_seed']}) | deviation {record['deviation']!r} | floor "
        f"{floor_value!r} ({SIGMA_ZERO_PREFIX})"
    )
    print(f"[phase23_run] wrote {SIGMA_ZERO_RECORD}: verdict {verdict!r}")
    if halt_message is not None:
        print(halt_message)
        raise SystemExit(
            "[phase23_run] D-04 HALT recorded at "
            f"{SIGMA_ZERO_RECORD}. The sweep is halted with ZERO noised points. Commit the record, "
            "root-cause the difference — start at the control record's `residual_differences` — "
            "and do not re-run this arm to get a different number."
        )


_TABLE = {
    "cost": cost,
    "schedule": schedule,
    "floor": floor,
    "sigma-zero": sigma_zero,
}

USAGE = (
    f"usage: python scripts/phase23_run.py {{{'|'.join(_TABLE)}}}\n"
    "\n"
    "  cost        train + score control seed 1, cost the SCORING leg, apply the BLIND seed rule\n"
    "              `phase23_prereg.choose_n_seeds` -> N. Must run FIRST: N is a function of a\n"
    "              measured scoring cost and there is no default N anywhere.\n"
    "  schedule    ONE invocation — the remaining control arms AND every never-taught arm, at the\n"
    "              same seed list. Writes results/phase23_never_taught_training.json. Scores\n"
    "              nothing: the never-taught scoring budget is a function of 23-13's K.\n"
    "  floor       score the remaining control arms and reduce the floor through\n"
    "              `phase23_prereg.noise_floor`. Writes results/phase23_control_floor.json.\n"
    "  sigma-zero  the DP arm's FIRST executed run, at sigma = 0 and the full production shape,\n"
    "              judged by `phase23_prereg.sigma_zero_verdict` against the floor pinned in\n"
    "              `mitigation_budget.CONTROL_NOISE_FLOOR`. Writes\n"
    "              results/phase23_sigma_zero.json. A breach HALTS the sweep — no override flag.\n"
)


def main(argv=None):
    """Explicit argv slicing — ``scripts/phase19_run.py``'s register, deliberately not argparse."""
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] in ("--help", "-h"):
        print(USAGE)
        return 0
    if len(argv) != 1 or argv[0] not in _TABLE:
        raise SystemExit(USAGE)
    _TABLE[argv[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
