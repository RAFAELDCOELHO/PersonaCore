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

# 23-15's BLIND protocol pin, CONSUMED and never edited. It carries every constant the
# protocol-matched comparator below is built from — `MATCHED_GRAD_CLIP`, `matched_arm`,
# `MATCHED_ARM_PREFIX` and the three AST completeness censuses. It is EDIT-ONCE from 23-17's first
# matched artifact and has NO SAFETY VALVE, so nothing here writes to it.
import phase23_matched_prereg as mp  # noqa: E402

# 23-20's CONTINUATION pin — a SECOND rule that arrived in a NEW file rather than as an edit to the
# frozen one above, because `git merge-base --is-ancestor HEAD d99d2aa` exits NON-ZERO and a second
# commit touching `phase23_matched_prereg.py` would redden its ancestry guard PERMANENTLY. It admits
# the continuation of a HARNESS-KILLED run and refuses every other shape of partial state.
import phase23_resume_prereg as rp  # noqa: E402
import teach_persona as tp  # noqa: E402
from phase23_prereg import (  # noqa: E402
    CONTROL_FLOOR_RECORD,
    COST_RECORD,
    FLOOR_PROVENANCE_KEYS,
    H_PER_POINT_FLOOR_SECONDS,
    NEVER_TAUGHT_RECORD,
    NEVER_TAUGHT_TRAINING_RECORD,
    NOISED_RECORD_GLOB,
    SIGMA_ZERO_RECORD,
    choose_n_seeds,
    noise_floor,
    noised_record_path,
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
# ===== (e2) THE PROTOCOL-MATCHED COMPARATOR — its call, its clip capture, its training leg =====
#
# THE OBSTACLE THE PLANNING BRIEF FLAGGED, AND WHY IT DISSOLVES. The brief warns that a non-DP arm
# "cannot reach the `dp_kwargs` seam today — `build_arm_bins` reads `DP_ARMS` and nothing else".
# That is TRUE of `build_arm_bins` and FALSE of `train()`. MEASURED against live source:
# `loop.py:512` keys the fact-aligned seam's three refusals on `_fact = {"fact_bin": fact_bin,
# "n_facts": n_facts}` — its own comment says *"Gated on the FACT half only"* — and `loop.py:683`
# gates the replay pass on `replay_windows is not None`. **NEITHER mentions `dp_fn`.** So a
# `dp_fn`-absent call carrying the same six data kwargs reaches the identical loader, the identical
# lot size and the identical replay pass. `DP_ARMS` is NOT widened and `teach_persona.py` is NOT
# edited; the comparator calls `tp.train(...)` directly, exactly as `train_never_taught` above
# already does for an arm `build_arm_bins` cannot express.
# =================================================================================================


def matched_control_call(seed):
    """The comparator's ``(train_config_fields, train_kwargs)``, DERIVED from the DP arm's symbols.

    Returns two plain dicts so both halves are inspectable at ZERO GPU cost — that is what lets
    :func:`prove_matched_protocol` and ``tests/test_phase23_matched.py`` check the protocol match
    by construction rather than by reading a 100-minute run afterwards.

    **NOTHING HERE IS RETYPED.** ``n_facts`` comes from ``len(tp.arm_spec(SIGMA_ZERO_ARM)[0])``,
    ``replay_windows`` from ``tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE``, the fact bin
    from ``tp.fact_bin_path(...)``, and the budget from ``tp.LR`` / ``tp.WARMUP_STEPS`` /
    ``tp.MAX_STEPS`` / ``tp.BATCH_SIZE`` / ``tp.WEIGHT_DECAY``. A retyped constant is a second
    source for one fact, free to disagree with the arm it is supposed to match — and
    retyped-vs-derived is this phase's own subject.

    THE THREE MECHANISMS THIS CALL EQUALISES, each with the magnitude it was MEASURED at
    (``phase23_matched_prereg.MATCHED_EQUALISED`` is the record; these are its figures):

    1. **LOT VOLUME.** The DP lot is 33 teaching + 32 replay = **65 windows**; the old control's was
       **8**. That is 8.125x per step, and 1,689,600 vs 196,867 = **8.58x** TEACHING-token exposure
       over the run. Reached here by ``fact_bin``/``n_facts`` (the fact-aligned packer) plus
       ``replay_bin``/``replay_mask_bin``/``replay_windows`` (the train-time replay pass), with
       ``grad_accum_steps = n_facts`` on the ``TrainConfig`` half.
    2. **TEACHING LOSS WEIGHT.** The fact-aligned packer returns every window of one fact, so
       teaching enters the gradient at weight **1.0**. The old control drew 8 RANDOM windows from a
       bin that is 51.94% replay, so masked-CE put weight p = 2719/6262 = **0.4342** on teaching —
       1/0.4342 = **2.30x**, on top of drastically lower gradient variance AdamW compounds over 200
       steps. Equalised by the same ``fact_bin`` wiring.
    3. **GRAD CLIP.** ``config.py:105`` defaults ``grad_clip`` to 1.0 and ``loop.py:220-221``
       applies ``clip_grad_norm_`` IFF ``dp_fn is None``, so at the default this comparator would
       be clipped where the DP arm structurally is not. MEASURED: the old control's clip BOUND on 19
       of its first 25 steps** at mean shrink **0.8071**, against DP pre-clip norms of 1.538-2.278
       that were never clipped at all. Equalised to ``mp.MATCHED_GRAD_CLIP``, and PROVEN
       non-binding at run time by :func:`captured_grad_clip`.

    **MATCHING TOKEN COUNT ALONE IS EXPLICITLY INSUFFICIENT, and that is the whole finding.** The
    old control matched the DP arm's replay TOKEN volume exactly — `control_replay_ratio` above
    solves for the ratio and `train_control` proves the built bin carries the target count as a
    NUMBER. It still differed by all three mechanisms above, because token count says nothing about
    how those tokens are grouped into a lot, what weight they carry in the loss, or whether the
    resulting gradient is clipped.

    ``dp_fn`` IS DELIBERATELY ABSENT. ``train()``'s own default is ``None`` (verified against the
    live signature), so passing ``dp_fn=None`` explicitly would be arithmetically equivalent and
    would put a ``dp_fn`` key in the diff for no reason — while making the comparator's key set
    read as though it reached the DP seam.

    ``resume_from`` IS ALSO DELIBERATELY ABSENT. This scheduling resumes nothing, which is exactly
    why ``phase23_matched_prereg.DP_FN_BRANCH_DISPOSITIONS`` items 6 and 7 — the two ``train``
    branches keyed on ``ckpt.get('dp_noise_rng')`` — are dispositioned ``unreached``.
    """
    n_facts = len(tp.arm_spec(SIGMA_ZERO_ARM)[0])
    arm = mp.matched_arm(seed)
    paths = tp.arm_outputs(arm, prefix=mp.MATCHED_ARM_PREFIX)
    # THE BIN PATHS ONLY. `arm_outputs`' documented non-widening is that `bin`/`mask` carry NO
    # prefix, so ANY prefix argument yields the same `data/persona_dp_n8_train{,_mask}.bin`; this
    # driver's own `PREFIX` is passed because it is the value in hand, not because it selects them.
    dp_paths = tp.arm_outputs(SIGMA_ZERO_ARM, prefix=PREFIX)

    train_config_fields = dict(
        lr=tp.LR,
        warmup_steps=tp.WARMUP_STEPS,
        max_steps=tp.MAX_STEPS,
        batch_size=tp.BATCH_SIZE,
        weight_decay=tp.WEIGHT_DECAY,
        seed=seed,
        # `loop.py:531` REFUSES unless `max(1, grad_accum_steps) == n_facts` under the fact-aligned
        # seam, so this agreement is satisfied BY CONSTRUCTION rather than by care.
        grad_accum_steps=n_facts,
        grad_clip=mp.MATCHED_GRAD_CLIP,
    )
    train_kwargs = dict(
        train_bin=dp_paths["bin"],
        train_mask_bin=dp_paths["mask"],
        fact_bin=tp.fact_bin_path(dp_paths["bin"]),
        n_facts=n_facts,
        replay_bin=tp.DIALOG_TRAIN_BIN,
        replay_mask_bin=tp.DIALOG_TRAIN_MASK,
        replay_windows=tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE,
        val_bin=tp.DIALOG_VAL_BIN,
        val_mask_bin=tp.DIALOG_VAL_MASK,
        penalty_fn=None,
        log_path=paths["csv"],
        checkpoint_path=paths["checkpoint"],
        eval_interval=tp.EVAL_INTERVAL,
        checkpoint_interval=tp.CHECKPOINT_INTERVAL,
        return_final_loss=True,
    )
    return train_config_fields, train_kwargs


def prove_matched_protocol():
    """THE ZERO-COST PREFLIGHT: all three of 23-15's AST gates, plus the key-set subtraction.

    Runs against LIVE source read off disk, and runs BEFORE the first GPU second is spent — so an
    undeclared ``dp_fn`` branch, a dropped ``dp_kwargs`` key, or a NEW keyword on the production
    ``train(...)`` call refuses at zero cost instead of after 100 minutes of training.

    The third gate is the one the other two cannot cover. ``prove_branch_ledger_complete`` sees
    ``dp_fn``-conditioned branches; ``prove_dp_wiring_keys`` sees the two DP dicts. NEITHER sees the
    other 15 keywords, so a future ``extra_eval_fns=`` added at the production call site would
    silently un-match this comparator with both of them GREEN — the 23-08 failure shape one level
    up: a hand-drawn boundary that did not know what it excluded.

    Returns the ``dp_fn`` branch census (a ``Counter`` summing to 7) for the record.
    """
    loop_source = (_ROOT / "src" / "personacore" / "training" / "loop.py").read_text(
        encoding="utf-8"
    )
    teach_source = (_ROOT / "scripts" / "teach_persona.py").read_text(encoding="utf-8")

    census = mp.prove_branch_ledger_complete(loop_source)
    mp.prove_dp_wiring_keys(teach_source)
    production = mp.prove_train_call_keys(teach_source)

    fields, kwargs = matched_control_call(SEED_LADDER[0])
    seen = {"train_config", "runtime_config", "model", "model_config"} | set(kwargs)
    expected = set(production) - {"resume_from", "dp_fn"}
    _prove(
        seen == expected,
        "the matched comparator's train(...) keyword set is NOT the production set minus "
        "{resume_from, dp_fn}.\n"
        f"  EXTRA   (the comparator passes, production does not): {sorted(seen - expected)}\n"
        f"  MISSING (production passes, the comparator does not): {sorted(expected - seen)}\n"
        "Both directions are printed because both are fatal and they fail differently. A DROPPED "
        "data kwarg silently returns this comparator to the OLD RANDOM-WINDOW PROTOCOL — drop "
        "`fact_bin`/`n_facts` and `train()` falls back to the flat masked loader at 8 random "
        "windows per lot; drop `replay_windows` and the train-time replay pass never runs. That is "
        "the EXACT defect this whole gap closure exists to correct, and it would produce a "
        "perfectly well-formed 100-minute run whose reading answers a different question. An EXTRA "
        "kwarg is equally fatal in the other direction: the comparator would differ from the σ=0 "
        "arm by something nobody declared",
    )
    _prove(
        "dp_fn" not in kwargs,
        "the matched comparator passes `dp_fn`. Its ABSENCE is the one thing that makes this a "
        "NON-DP arm reaching the DP arm's data wiring — `train()`'s own default is None, so "
        "passing it explicitly buys nothing and passing anything else makes this a second DP arm "
        "rather than a comparator for one",
    )
    _prove(
        "resume_from" not in kwargs,
        "the matched comparator passes `resume_from`. This scheduling resumes NOTHING, and its "
        "absence is precisely why `phase23_matched_prereg.DP_FN_BRANCH_DISPOSITIONS` items 6 and "
        "7 — the two `train` branches keyed on `ckpt.get('dp_noise_rng')` — are dispositioned "
        "`unreached`. A resume here would reach two branches the blind ledger declared unreachable",
    )
    for name in mp.DP_TRAIN_KEYS:
        _prove(
            name in fields,
            f"`{name}` is in DP_TRAIN_KEYS but not in the comparator's TrainConfig fields. These "
            "ride on the TrainConfig CONSTRUCTOR, not on the train() call, so the key-set "
            "subtraction above cannot see them — and `grad_accum_steps` is the 8.125x lot-volume "
            "lever, the single largest per-step difference the comparator exists to equalise",
        )

    print(
        f"[phase23_run] matched preflight: {sum(census.values())} dp_fn branch(es), "
        f"{len(production)} production train() keyword(s), {len(seen)} on the comparator "
        "(= production - {resume_from, dp_fn}) — all three AST gates GREEN"
    )
    return census


@contextlib.contextmanager
def captured_grad_clip():
    """Shadow ``torch.nn.utils.clip_grad_norm_`` and record every PRE-clip global norm it returns.

    :func:`captured_dp_seam`'s register, at a different seam: capture the real callable, install a
    wrapper, restore in ``finally``. Yields ``box = {"norms": [...]}``.

    **WHY A MODULE-ATTRIBUTE SHADOW IS VISIBLE WITHOUT EDITING `loop.py`.** ``loop.py:221`` spells
    ``torch.nn.utils.clip_grad_norm_(...)`` — an ATTRIBUTE resolved at CALL time on the shared
    ``torch.nn.utils`` module object, not a name bound at import. Rebinding that attribute is
    therefore seen by the live loop, and ``tp.torch`` reaches the same singleton module.

    **WHY THE CAPTURED LIST IS EXACTLY THE QUANTITY PROBE 1 MEASURED.** ``clip_grad_norm_`` RETURNS
    the PRE-clip global norm (it computes ``total_norm``, then scales by
    ``min(1, max_norm/(total_norm+1e-6))`` and returns ``total_norm`` unmodified). So the recorded
    values are the norms BEFORE any shrink — the same quantity that measured the old control
    binding on 19 of its first 25 steps at mean shrink 0.8071.

    **THIS IS WHAT TURNS "NON-BINDING" FROM AN ASSUMPTION INTO AN OBSERVATION.** `MATCHED_GRAD_CLIP`
    equalises the clip by CONSTANT; only this bracket can say the constant did not bind on the run
    that actually happened. Same discipline that produced `clip_bind_count == 0` for the σ=0 arm
    before any reading existed.

    DECLARED COST, recorded rather than left to be noticed: ``float(norm)`` forces a host sync per
    optimizer step that the σ=0 arm did not have. That is a difference in the TIMING leg only —
    it moves no float in the gradient path — and the comparator's wall clock should be read with
    it in mind.
    """
    box = {"norms": []}
    real = tp.torch.nn.utils.clip_grad_norm_

    def capturing(*args, **kwargs):
        norm = real(*args, **kwargs)
        box["norms"].append(float(norm))
        return norm

    tp.torch.nn.utils.clip_grad_norm_ = capturing
    try:
        yield box
    finally:
        tp.torch.nn.utils.clip_grad_norm_ = real


def train_matched_control(seed):
    """Train ONE protocol-matched comparator arm: the σ=0 arm's protocol, without the DP seam.

    ``train()`` is called DIRECTLY, on ``train_never_taught``'s register — same
    ``refuse_if_exists`` on the three non-bin targets, same load-before-inject ordering, same
    ``n_wrapped`` and trainable-census refusals, same ``snapshot_params`` canary, same
    ``export_adapter`` with a base fingerprint READ from the checkpoint rather than recomputed.

    IT TRAINS ON THE SAME BYTES AS THE σ=0 ARM, not on an equivalent rebuild.
    ``prove_bins_match(DP_N8_BIN_SHA256)`` pins ``data/persona_dp_n8_train{,_mask,_fact}.bin`` to
    23-07's recorded digests before a single step runs. Bin IDENTITY, not bin equivalence — and it
    BUILDS no bins of its own, which is what "protocol-matched" means here.

    NOTE WHAT THE RETURNED BLOCK DOES NOT CARRY, and why it says so explicitly: a direct ``train()``
    caller runs neither of the two end-of-run ``masked_perplexity`` sweeps that live in
    ``teach_persona.py`` at :1705 and :1709, so six fields the OLD control record carries are
    STRUCTURALLY absent here. They are recorded as ``None`` with a stated reason
    (``ppl_omitted_reason``) rather than dropped: a ``None`` with a reason is an honest record, a
    missing key is a reader's guess. Declared blind in
    ``phase23_matched_prereg.MATCHED_DIFFERENCES``.
    """
    arm = mp.matched_arm(seed)
    paths = tp.arm_outputs(arm, prefix=mp.MATCHED_ARM_PREFIX)
    # The dp_n8 bins are INPUTS here, not targets — this arm builds none, so they are deliberately
    # NOT passed to `refuse_if_exists`. Passing them would refuse on the corpus this arm REQUIRES.
    tp.refuse_if_exists([paths["csv"], paths["checkpoint"], paths["adapter"]])

    # ===== THE BIN GATE, IN THE ONLY ORDER THAT WORKS =====
    # `rebuild_arm_bins_verifying_sha256` is deliberately NOT called: it OPENS with
    # `_prove(prove_bins_match(...) > 0, ...)` (:266-271 as written, :289-294 as it now sits) and
    # `prove_bins_match` REFUSES A MISSING FILE (:234-249). It proves byte-identity of bins that are
    # already present; it CANNOT recreate an absent one. So the recovery order is: build only if
    # something is missing, then prove — never prove-then-build.
    absent = sorted(path for path in DP_N8_BIN_SHA256 if not pathlib.Path(path).exists())
    if absent:
        _prove(
            len(absent) == len(DP_N8_BIN_SHA256),
            f"the dp_n8 corpus is PARTIAL — {len(absent)} of {len(DP_N8_BIN_SHA256)} bins are "
            f"missing: {absent}. `build_arm_bins` refuses when any target already exists, so a "
            "partial corpus cannot be completed in place, and deleting the survivors here would "
            "destroy the only evidence of how it went partial. Delete all three in a reviewed step "
            "and re-run, so the rebuild is proved against 23-07's digests from a clean start",
        )
        # `second_person` and `replay_ratio` are DERIVED from `arm_spec`, never typed — they are
        # properties OF the arm, and this phase's own subject is retyped-vs-derived. Measured today
        # they are `(False, 0.0)`; that pair is an EXPECTATION TO CHECK AGAINST, not a source to
        # copy from, which is why the names and not the literals are passed below.
        facts, second_person, replay_ratio = tp.arm_spec(SIGMA_ZERO_ARM)
        tp.build_arm_bins(
            SIGMA_ZERO_ARM,
            facts,
            fs.TAUGHT_FAMILY_IDS,
            second_person=second_person,
            replay_ratio=replay_ratio,
            # THE BUILD SEED IS `SEED_LADDER[0]`, **NOT** THE PER-ARM `seed`. These bins are the σ=0
            # arm's corpus and must be byte-identical at every comparator seed; only the model init
            # and the data order vary with `seed`. This is the ONE place a seed could silently
            # change the corpus, and `prove_bins_match` below is what catches it if it ever does.
            seed=SEED_LADDER[0],
            prefix=PREFIX,
        )
    proved = prove_bins_match(DP_N8_BIN_SHA256)
    _prove(
        proved == len(DP_N8_BIN_SHA256),
        f"the corpus gate proved {proved} bin(s) against {len(DP_N8_BIN_SHA256)} recorded digests. "
        "A gate that checked fewer files than it was given reports success having verified less "
        "than the corpus this arm is about to train on",
    )
    print(
        f"[phase23_run] {arm}: {proved} dp_n8 bin(s) verified against 23-07's digests "
        f"({'rebuilt' if absent else 'already present'}) — SAME BYTES as the σ=0 arm"
    )

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

    fields, kwargs = matched_control_call(seed)
    box = {}
    with captured_grad_clip() as clip_box:
        with synchronized_seconds(box):
            final = tp.train(
                train_config=tp.TrainConfig(**fields),
                runtime_config=runtime,
                model=model,
                model_config=model_cfg,
                **kwargs,
            )

    # ===== THE NON-BINDING PROOF, **BEFORE ANY READING EXISTS** =====
    # Same ordering, and for the same reason, as `train_sigma_zero`'s `clip_bind_count == 0`: a
    # check run after the scoring pass is a check run with the reading already on screen.
    norms = clip_box["norms"]
    _prove(
        len(norms) == tp.MAX_STEPS,
        f"`clip_grad_norm_` was called {len(norms)} time(s) over a {tp.MAX_STEPS}-step run. "
        "`loop.py` has exactly ONE reachable call site and it fires once per optimizer step IFF "
        "`dp_fn is None`, so a different count means the branch was NOT taken and the grad_clip "
        "equalisation was never applied at all — the comparator would differ from the σ=0 arm by "
        "the very mechanism this constant exists to remove, and nothing else would show it",
    )
    _prove(
        max(norms) < mp.MATCHED_GRAD_CLIP,
        f"the comparator's largest PRE-clip global norm was {max(norms)!r}, at or above C = "
        f"{mp.MATCHED_GRAD_CLIP!r}. A binding clip makes this arm differ from the σ=0 arm by "
        "CLIPPING rather than by protocol — which is the exact confound the old control carried "
        "(bound on 19 of its first 25 steps, mean shrink 0.8071) and the reason this comparator "
        "exists. This refusal runs BEFORE scoring for the same reason `train_sigma_zero`'s "
        "`clip_bind_count == 0` does: afterwards it would be a check made with the reading visible",
    )
    print(
        f"[phase23_run] {arm}: {len(norms)} clip call(s), pre-clip norms in "
        f"[{min(norms):.6g}, {max(norms):.6g}] against C = {mp.MATCHED_GRAD_CLIP!r} — C is "
        "OBSERVED non-binding, before any reading exists"
    )

    # The same canary `train_never_taught` runs: every trainable moved, every frozen base param
    # bit-identical.
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
    replay_windows = kwargs["replay_windows"]
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
        # THE PROTOCOL, as the fields the σ=0 record carries under the same names.
        "n_facts": kwargs["n_facts"],
        "grad_accum_steps": fields["grad_accum_steps"],
        "grad_clip": fields["grad_clip"],
        "replay_windows_per_step": replay_windows,
        "replay_micro_batches_per_step": math.ceil(replay_windows / tp.BATCH_SIZE),
        "max_steps": fields["max_steps"],
        "batch_size": fields["batch_size"],
        "block_size": tp.BLOCK_SIZE,
        "dp_seam_active": False,
        # THE CLIP OBSERVATION, carried as numbers so it cannot be a claim.
        "grad_clip_calls": len(norms),
        "grad_clip_max_pre_clip_norm": max(norms),
        "grad_clip_min_pre_clip_norm": min(norms),
        "grad_clip_bound_count": sum(1 for norm in norms if norm > mp.MATCHED_GRAD_CLIP),
        "grad_clip_checked_before_scoring": True,
        "corpus_sha256": {_rel(path): digest for path, digest in DP_N8_BIN_SHA256.items()},
        # ===== THE DECLARED OMISSION, RECORDED RATHER THAN LEFT TO BE NOTICED =====
        "ppl_adapter_on": None,
        "ppl_adapter_off": None,
        "ppl_scored_targets": None,
        "teaching_tokens": None,
        "replay_tokens": None,
        "replay_ratio": None,
        "ppl_omitted_reason": (
            "train() called directly; train_arm's two masked_perplexity sweeps "
            "(teach_persona.py:1705,1709) do not run, so these six fields the OLD control record "
            "carries are structurally absent here. They are post-training diagnostics and cannot "
            "move a reading; adding them would spend scoring time the 23-17 budget does not hold."
        ),
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


# =================================================================================================
# ===== (f2) THE PROTOCOL-MATCHED COMPARATOR'S SUB-MODE, AND ITS RECORD =====
# =================================================================================================

# The six per-seed fields the OLD control record carries as floats and this one STRUCTURALLY cannot.
# Named here so the record can DECLARE them rather than leave a reader diffing the two records to
# infer the reason from an absence. Their values are read from the training block, never retyped.
_MATCHED_OMITTED_FIELDS = (
    "ppl_adapter_on",
    "ppl_adapter_off",
    "ppl_scored_targets",
    "teaching_tokens",
    "replay_tokens",
    "replay_ratio",
)


def matched():
    """23-17 — train and score the PROTOCOL-MATCHED comparator at five seeds, and RE-REDUCE.

    ``floor()``'s register throughout: the reduction is CALLED out of the blind pin, the record
    names the SYMBOL and never the formula, and every provenance key is proved present BEFORE the
    write. What is new here is the ONE-ATTEMPT gate, and it is in TWO PARTS because one is not
    enough — see the two blocks below and ``one_attempt_scope`` in the record.

    RUNS NO σ=0 ARM AND RENDERS NO VERDICT. It writes ``results/phase23_matched_control.json`` and
    nothing else under ``results/``; ``phase23_prereg.sigma_zero_verdict`` is 23-19's to call.
    """
    _preconditions()

    # ===== (2a) THE ONE-ATTEMPT GATE, ACROSS COMMITS =====
    # `_prove_no_noised_record_exists`'s subprocess shape, at the matched glob.
    # `prove_first_attempt` runs no subprocess of its own — it takes THIS result, which is why the
    # call is here.
    matched_glob_at_start = subprocess.run(
        ["git", "ls-files", mp.MATCHED_ARTIFACT_GLOB],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    # ===== (2b) THE HALF OF THE UNCOMMITTED WINDOW THAT (2a) STRUCTURALLY CANNOT SEE =====
    # `.gitignore:17` ignores `data/` and `:14` ignores `checkpoints/`, so between this run writing
    # the record and 23-17's commit landing it, a second attempt is available with no TRACKED
    # residue: delete the record, the per-seed result dirs, the seed checkpoints and this state
    # file's `matched` section, and (2a) sees an empty `git ls-files`, the refuse-if-exists below
    # sees nothing, and `_state_record`'s overwrite refusal is DEFEATED BY the deletion rather than
    # triggered by it. This narrows that window; it does not close it.
    #
    # THE PREDICATE IS "SCORED", NOT "TRAINED", and the difference is load-bearing: a training leg
    # killed mid-run and resumed is LEGITIMATE and must stay legitimate. Only a seed that already
    # produced a READING is evidence of a completed prior attempt.
    #
    # WHAT THIS REFUSAL DOES **NOT** DO, stated here because the next reader will assume otherwise:
    # it refuses a delete that leaves the `matched` section INTACT. A delete that ALSO removes that
    # section is PREVENTED BY NOTHING — `prior` reads {}, `scored` reads [], `not scored` is True
    # and this `_prove` PASSES. That case is INDISTINGUISHABLE FROM A FIRST ATTEMPT AT RUN TIME, and
    # both recorded lists read [] either way. It is bounded only AFTER THE FACT: this state file is
    # TRACKED (`cfa2c87`) with a committed baseline carrying NO `matched` section, so once the
    # same-session commit lands the section a later deletion of it is a VISIBLE DIFF. See
    # `one_attempt_scope`, which records all four clauses at exactly that strength.
    prior = _state_load().get("matched", {})
    prior_scored_seeds_at_start = sorted(s for s, b in prior.items() if "primary" in b)

    # ===== (2c) WHICH OF THE TWO ONE-ATTEMPT RULES GOVERNS THIS RUN =====
    # 23-17's run was HARNESS-KILLED at 3 of 5 seeds, which the (2b) `_prove` below refuses — and
    # that refusal was correct as written and was OBEYED rather than narrowed with readings on
    # screen. 23-20 pre-registers the continuation SEPARATELY, in `phase23_resume_prereg`, and
    # selects between the two rules HERE.
    #
    # THE BRANCH PREDICATE IS `not scored` ALONE, and that is load-bearing. Writing
    # `if not matched_glob_at_start and not scored:` would only ever call the frozen rule with an
    # argument control flow had already proved empty — FILTERING BY CONTROL FLOW — which makes
    # `prove_first_attempt`'s refusal UNREACHABLE. On `not scored` alone, a tracked artifact sitting
    # beside an empty state reaches the frozen rule with the REAL, non-empty list and fires its own
    # `ONE ATTEMPT — REFUSED`.
    trained_seeds, scored_seeds = rp.seed_status(prior)
    committed_scored_seeds = rp.seed_status(
        json.loads(
            subprocess.run(
                ["git", "show", "HEAD:data/phase23_run_state.json"],
                cwd=_ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        ).get("matched", {})
    )[1]

    if not scored_seeds:
        mp.prove_first_attempt(matched_glob_at_start)
        print(f"[phase23_run] git ls-files {mp.MATCHED_ARTIFACT_GLOB}: EMPTY — first attempt")
        attempt = "first"
        continuation_rule = None
        continuation_fingerprint = None
        # RETAINED VERBATIM — but stated at TRUE strength rather than as a live guard: on THIS
        # branch it is UNFIREABLE. `rp.seed_status`'s `scored` and `prior_scored_seeds_at_start`
        # are the SAME predicate (`"primary" in block`) over the SAME dict, `prior`, so `not
        # scored_seeds` implies `not prior_scored_seeds_at_start` and this `_prove`'s FIRST
        # DISJUNCT is tautologically true here. It is kept as a reader-visible marker of the rule
        # that governed before the split, NOT as a refusal that still fires. The refusal it used to
        # perform on a 3-scored state is now performed by `prove_killed_run_continuation`'s seven
        # NAMED conjuncts — which is why the split exists. Nothing is lost, and claiming it still
        # fires would be claiming a guard the code does not have.
        _prove(
            not prior_scored_seeds_at_start or (_ROOT / mp.MATCHED_CONTROL_RECORD).exists(),
            # The RENDERED message is byte-identical to what this `_prove` carried before the
            # branch; only the source line break moved, because the deeper indent pushed the middle
            # fragment past 100 columns.
            f"{STATE_PATH} records SCORED matched seeds {prior_scored_seeds_at_start} while "
            f"{mp.MATCHED_CONTROL_RECORD} is absent. That is exactly the state a "
            "deleted-and-re-run first attempt leaves behind, and there is no force flag.",
        )
    else:
        # THE RELATIONSHIP BETWEEN THE TWO RULES, AT TRUE STRENGTH — the new one is NOT "strictly
        # more demanding". On the ONE state that matters (3 scored, record absent) the (2b) `_prove`
        # REFUSES and this predicate ADMITS, so in OUTCOME it is strictly more PERMISSIVE: that is
        # the entire point of it existing. What is stronger is its SHAPE — seven NAMED conjuncts
        # against one, plus committed-vs-working-tree agreement, ladder-prefix shape and
        # tracked-path shape, none of which the old `_prove` checked at all.
        #
        # The fingerprint IS the argument dict, so what the record publishes is literally what the
        # predicate saw — including `tracked`, without which conjuncts 6 and 7 would re-admit
        # VACUOUSLY on every suite run. `ladder` is `list(SEED_LADDER)` in LADDER ORDER and is never
        # sorted: conjuncts 3 and 4 INDEX it, and `sorted(SEED_LADDER)` would make every
        # re-admission REFUSE.
        continuation_fingerprint = {
            "tracked": matched_glob_at_start,
            "ladder": list(SEED_LADDER),
            "trained_seeds": sorted(trained_seeds),
            "scored_seeds": sorted(scored_seeds),
            "committed_scored_seeds": sorted(committed_scored_seeds),
            "record_exists": (_ROOT / mp.MATCHED_CONTROL_RECORD).exists(),
        }
        rp.prove_killed_run_continuation(**continuation_fingerprint)
        attempt = "continuation"
        continuation_rule = "phase23_resume_prereg.prove_killed_run_continuation"
        print(
            f"[phase23_run] CONTINUATION of a killed run ADMITTED by {continuation_rule}: "
            f"scored {sorted(scored_seeds)}, trained {sorted(trained_seeds)}, "
            f"HEAD agrees at {sorted(committed_scored_seeds)}, "
            f"{len(matched_glob_at_start)} tracked per-seed curve(s)"
        )

    # ===== THE THREE AST GATES, BEFORE A SINGLE GPU SECOND IS SPENT =====
    census = prove_matched_protocol()

    path = _ROOT / mp.MATCHED_CONTROL_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )

    # ===== THE SEED SET IS INHERITED, NOT RE-CHOSEN =====
    # `choose_n_seeds` already selected a PREFIX of this ladder at N=5 on a measured 996.27 s
    # scoring cost, and the scoring instrument here is byte-identical (`score_adapter`, one
    # function, now three callers). Re-measuring its cost would move nothing and would spend a seed
    # to learn it. A drift between this list and the `cost` block would compare two different
    # denominators, which is why the agreement is PROVED rather than assumed.
    seeds = list(SEED_LADDER)
    state = _state_load()
    _prove(
        "cost" in state,
        f"{STATE_PATH} carries no `cost` block — run `python scripts/phase23_run.py cost` first. "
        "The comparator INHERITS that block's seed list; without it there is nothing to inherit "
        "from and N would be chosen here, with the σ=0 reading already on screen",
    )
    _prove(
        seeds == [int(s) for s in state["cost"]["seeds"]],
        f"the comparator is about to run at {seeds} while the `cost` block recorded "
        f"{state['cost']['seeds']}. The old control's floor was reduced over THAT set; a "
        "comparator reduced over a different one would be compared against a denominator it does "
        "not share",
    )

    for seed in seeds:
        if not _already_trained("matched", seed):
            print(f"[phase23_run] matched: training {mp.matched_arm(seed)}")
            _state_record("matched", seed, train_matched_control(seed))
        block = _state_load()["matched"][str(seed)]

        # ===== THE GRAD-CLIP NON-BINDING PROOF, **BEFORE THIS SEED IS SCORED** =====
        # Re-asserted here from the RECORDED block — not only inside `train_matched_control` —
        # because a resumed seed reuses an adapter trained in an earlier process, and the evidence
        # that reached the state file is the evidence the record will publish.
        _prove(
            block["grad_clip_calls"] == tp.MAX_STEPS
            and block["grad_clip_bound_count"] == 0
            and block["grad_clip_max_pre_clip_norm"] < mp.MATCHED_GRAD_CLIP,
            f"matched seed {seed} recorded {block['grad_clip_calls']} clip call(s) against "
            f"{tp.MAX_STEPS} steps, {block['grad_clip_bound_count']} binding, largest pre-clip "
            f"norm {block['grad_clip_max_pre_clip_norm']!r} against C = "
            f"{mp.MATCHED_GRAD_CLIP!r}. A seed whose clip BOUND differs from the σ=0 arm by "
            "CLIPPING rather than by protocol — the exact confound this comparator exists to "
            "remove. A call count BELOW MAX_STEPS is worse: it means `loop.py`'s "
            "`dp_fn is None` branch was NEVER TAKEN, so the equalisation was never applied at all "
            "and nothing else would show it. This runs BEFORE scoring for the same reason "
            "`train_sigma_zero`'s `clip_bind_count == 0` does: afterwards it would be a check made "
            "with the reading already visible",
        )

        if "primary" not in block:
            print(f"[phase23_run] matched: scoring {mp.matched_arm(seed)}")
            _state_record(
                "matched",
                seed,
                score_adapter(mp.matched_arm(seed), _ROOT / block["adapter"], seed=seed),
            )

    state = _state_load()
    per_seed = [state["matched"][str(seed)] for seed in seeds]
    readings = [entry["primary"]["rate"] for entry in per_seed]
    # THE REDUCTION IS CALLED, NEVER INLINED. No `max`, no `min`, no spread expression is typed
    # in this function; `test_the_matched_writer_does_not_inline_the_reduction` proves that by AST.
    measured_floor = noise_floor(readings)

    inputs_sha256 = hashlib.sha256(
        json.dumps(per_seed, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    first = per_seed[0]
    record = {
        "record": mp.MATCHED_CONTROL_RECORD,
        "record_sha256": inputs_sha256,
        "floor": measured_floor,
        "reduction": "phase23_prereg.noise_floor",
        "estimator": "the RANGE max(readings) - min(readings) over the N per-seed PRIMARY "
        "readings, committed BLIND in 23-03 and CALLED here — never re-implemented",
        "governs": (
            "the TAUGHT RECALL RATE WITH THE ADAPTER ON (per_seed[].primary.k / .n, a count over "
            "QUESTIONS) and NOTHING ELSE. This floor describes the PROTOCOL-MATCHED comparator: "
            f"the same quantity {CONTROL_FLOOR_RECORD}'s floor describes, reduced over an arm that "
            "equalises the three mechanisms that record's `residual_differences` did not. Every "
            "other reading here is secondary, carries its own denominator and was NOT reduced. "
            "This record renders NO verdict: `phase23_prereg.sigma_zero_verdict` is 23-19's to "
            "call, against the floor 23-18 re-pins from this number"
        ),
        "primary_reading": "taught recall rate, adapter ON, over QUESTIONS",
        "seeds": seeds,
        "n_seeds": len(seeds),
        "central_reading": readings[0],
        "central_reading_seed": seeds[0],
        "readings": readings,
        "per_seed": per_seed,
        "questions_taught": first["primary"]["questions"],
        "questions_heldout": first["heldout_on"]["questions"],
        "draws_per_question": first["primary"]["draws_per_question"],
        "scoring_seconds_per_seed": {
            str(entry["seed"]): entry["scoring_seconds"] for entry in per_seed
        },
        "training_seconds_per_seed": {
            str(entry["seed"]): entry["training_seconds"] for entry in per_seed
        },
        # ===== THE ATTEMPT STATE — a rule whose inputs go unrecorded is a rule taken on trust ===
        "matched_glob_at_start": matched_glob_at_start,
        "prior_scored_seeds_at_start": prior_scored_seeds_at_start,
        "one_attempt_rule": "phase23_matched_prereg.prove_first_attempt",
        "one_attempt_scope": (
            "FOUR CLAUSES, recording the WEAKEST TRUE guarantee rather than the strongest sayable "
            "one.\n"
            "  (1) THE RULE BINDS ACROSS COMMITS. Once a matched artifact is TRACKED, a second "
            "protocol cannot be attempted without a VISIBLE DELETION in git history.\n"
            "  (2) INSIDE THE UNCOMMITTED WINDOW between this run and its commit it does not bind: "
            "`.gitignore:17` ignores `data/` and `.gitignore:14` ignores `checkpoints/`. There, "
            "`prior_scored_seeds_at_start` refuses ONLY a delete that leaves "
            "`data/phase23_run_state.json`'s `matched` section INTACT.\n"
            "  (3) A DELETE THAT ALSO REMOVES THAT SECTION IS PREVENTED BY NOTHING in real time. "
            "`prior` reads {}, `scored` reads [], and the case is INDISTINGUISHABLE FROM A FIRST "
            "ATTEMPT at run time; both recorded lists read [] either way, so this record discloses "
            "nothing about which it was.\n"
            "  (4) THAT SAME CASE IS AUDITABLE AFTER THE FACT rather than invisible — and only "
            "FROM THE SAME-SESSION COMMIT ONWARD. `data/phase23_run_state.json` is TRACKED as of "
            "`cfa2c87` with a committed baseline carrying NO `matched` section, and it is "
            "committed WITH this record, so a later deletion of that section is a VISIBLE DIFF "
            "against that commit. TRACKING IS NOT RETROACTIVE: before that commit a "
            "`git checkout -- data/phase23_run_state.json` reverts the working tree and leaves NO "
            "HISTORY AT ALL. The same-session commit is therefore what CONVERTS this residual from "
            "INVISIBLE to AUDITABLE rather than being its only bound. It remains a DISCIPLINE, NOT "
            "A MECHANISM, this is not 'closed', and there is no force flag."
        ),
        # ===== THE CONTINUATION, DISCLOSED BESIDE THE FOUR UNEDITED ATTEMPT-STATE KEYS =====
        # A reader who opens ONLY this record must learn that it was a continuation, and by which
        # rule — `prove_control_record_declares_visibility`'s own reason, applied to the second
        # disclosure this artifact owes.
        "attempt": attempt,
        "continuation_rule": continuation_rule,
        "continuation_fingerprint": continuation_fingerprint,
        "continuation_scope": rp.CONTINUATION_SCOPE,
        "continuation_discrimination": (
            f"{mp.MATCHED_CONTROL_RECORD} is written as `phase23_run.matched`'s LAST act, after "
            "every seed in `SEED_LADDER` has scored, so a COMPLETED attempt necessarily leaves "
            "five scored seeds and fewer than five is a state the completion path CANNOT PRODUCE. "
            "That write-ordering — and not any reading — is what tells a harness-killed run apart "
            "from a deleted-and-re-run one."
        ),
        # ===== THE VISIBILITY DISCLOSURE, TRAVELLING WITH THE ARTIFACT IT IS ABOUT =====
        "sigma_zero_was_visible": True,
        "sigma_zero_visibility_disclosure": mp.SIGMA_ZERO_VISIBILITY_DISCLOSURE,
        "protocol": {
            "arm_prefix": mp.MATCHED_ARM_PREFIX,
            "n_facts": first["n_facts"],
            "grad_accum_steps": first["grad_accum_steps"],
            "grad_clip": first["grad_clip"],
            "grad_clip_symbol": "phase23_matched_prereg.MATCHED_GRAD_CLIP",
            "replay_windows_per_step": first["replay_windows_per_step"],
            "replay_micro_batches_per_step": first["replay_micro_batches_per_step"],
            "max_steps": first["max_steps"],
            "batch_size": first["batch_size"],
            "block_size": first["block_size"],
            "dp_seam_active": first["dp_seam_active"],
            "corpus_sha256": {_rel(p): digest for p, digest in DP_N8_BIN_SHA256.items()},
            "corpus_is_the_sigma_zero_arms_own_bins": True,
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
        # ===== THE DISCLOSURE BLOCKS — differences carried BY CONSTRUCTION, not by hand =====
        "equalised_mechanisms": mp.MATCHED_EQUALISED,
        "declared_differences": mp.MATCHED_DIFFERENCES,
        "superseded_ledger": (
            "phase23_run.residual_differences (23-08) — four entries, and it did NOT enumerate "
            "grad_clip. That omission is why this comparator exists: a ledger drawn BY HAND did "
            f"not know what it excluded. It still stands in {CONTROL_FLOOR_RECORD}, unedited, so a "
            "reader sees both; this record's `declared_differences` is read out of "
            "`phase23_matched_prereg.MATCHED_DIFFERENCES` and its `dp_fn_branch_census` off LIVE "
            "source, so neither can silently go short again"
        ),
        "omitted_fields": {
            "fields": {name: first[name] for name in _MATCHED_OMITTED_FIELDS},
            "ppl_omitted_reason": first["ppl_omitted_reason"],
            "vs_old_control_record": (
                f"{CONTROL_FLOOR_RECORD}'s per_seed carries these six as FLOATS. They are absent "
                "here because that record's arms ran through `teach_persona.train_arm` and this "
                "comparator calls `tp.train` directly. Recorded as explicit None with a reason "
                "rather than dropped: a None with a reason is an honest record, a missing key is a "
                "reader's guess. Declared blind in phase23_matched_prereg.MATCHED_DIFFERENCES"
            ),
        },
        "dp_fn_branch_census": [
            {"function": function, "condition": condition, "count": count}
            for (function, condition), count in sorted(census.items())
        ],
        "grad_clip_evidence": {
            str(entry["seed"]): {
                "calls": entry["grad_clip_calls"],
                "max_pre_clip_norm": entry["grad_clip_max_pre_clip_norm"],
                "min_pre_clip_norm": entry["grad_clip_min_pre_clip_norm"],
                "bound_count": entry["grad_clip_bound_count"],
                "checked_before_scoring": entry["grad_clip_checked_before_scoring"],
            }
            for entry in per_seed
        },
        **provenance(),
    }

    missing = [key for key in FLOOR_PROVENANCE_KEYS if key not in record]
    _prove(
        not missing,
        f"the protocol-matched control record is MISSING {missing!r} from "
        "phase23_prereg.FLOOR_PROVENANCE_KEYS. `sigma_zero_verdict` REFUSES a floor whose "
        "artifact, commit, device, seeds or reduction is unstated and never defaults it: an "
        "unlabelled number is indistinguishable from a borrowed one",
    )
    _prove(
        record["floor"]
        == noise_floor([e["primary"]["k"] / e["primary"]["n"] for e in record["per_seed"]]),
        "the recorded floor does not re-derive from the recorded per-seed COUNTS — the record and "
        "its own reduction disagree before it has even been written",
    )
    mp.prove_control_record_declares_visibility(record)

    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print("[phase23_run] per-seed primary readings (taught recall ON, k/n over questions):")
    for entry in per_seed:
        block = entry["primary"]
        print(
            f"  seed {entry['seed']}: {block['k']}/{block['n']} = {block['rate']!r} "
            f"over {block['questions']} questions x {block['draws_per_question']} draws"
        )
    print(
        f"[phase23_run] wrote {mp.MATCHED_CONTROL_RECORD}: floor {measured_floor!r} "
        f"= phase23_prereg.noise_floor over {len(readings)} readings"
    )


# =================================================================================================
# ===== (f3) THE RE-TEST — THE D-04 DECISION, AGAINST THE COMPARATOR THAT IS FINALLY THE RIGHT ONE
# =================================================================================================

# The FOUR scored tiers, under the key names BOTH records already carry them by. Named once so the
# verdict record's `secondary_readings` block is built by READING each source block — see THE
# READ-THE-DENOMINATOR RULE inside `matched_verdict`, which governs every k and n it writes.
_SCORED_TIERS = ("primary", "heldout_on", "taught_off", "heldout_off")


def matched_verdict():
    """23-19 — re-run the D-04 decision against the PROTOCOL-MATCHED comparator.

    THE DRIVER COMPARES NOTHING. ``phase23_prereg.sigma_zero_verdict`` is CALLED with the matched
    comparator's readings, the σ=0 arm's reading READ BACK out of its committed record, the floor
    READ from ``mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR`` and that pin's provenance dict. The
    rule re-derives the floor from the readings it is handed and REFUSES a floor that does not
    match. ``deviation`` below is REPORTED for the record; the DECISION is the rule's and only the
    rule's. There is no override flag and no warning branch, and ``scripts/phase23_prereg.py`` is
    byte-identical to its blind birth commit ``c7de5d4`` — the corrected comparator is a new INPUT
    to that rule, never a change to it.

    THE σ=0 ARM IS NOT RE-RUN. Its PROTOCOL never changed; only its comparator did. Its reading is
    read back from ``results/phase23_sigma_zero.json`` and re-derived from that record's own
    ``primary.k / primary.n`` before use.

    ON A ``SystemExit`` FROM THE RULE — D-04 firing a second time — the record is STILL WRITTEN,
    carrying ``verdict: "HALT"`` and the raised message VERBATIM, and the sweep stays halted with
    zero noised points. That branch re-runs nothing, re-seeds nothing, widens nothing and tunes
    nothing. Either way the verdict IS the deliverable.
    """
    path = _ROOT / mp.MATCHED_VERDICT_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )

    matched_path = _ROOT / mp.MATCHED_CONTROL_RECORD
    sigma_zero_path = _ROOT / SIGMA_ZERO_RECORD
    matched = json.loads(matched_path.read_text(encoding="utf-8"))
    sigma_zero = json.loads(sigma_zero_path.read_text(encoding="utf-8"))
    matched_first = matched["per_seed"][0]

    # Both stored summaries must still agree with their OWN evidence. The debug session re-derived
    # this by hand once; asserting it here makes it permanent, and it is the SAME assertion on both
    # sides because a `rate` that drifted from its own denominator is the same defect either way.
    for label, block in (
        (SIGMA_ZERO_RECORD, sigma_zero["primary"]),
        (mp.MATCHED_CONTROL_RECORD, matched_first["primary"]),
    ):
        _prove(
            block["rate"] == block["k"] / block["n"],
            f"{label}'s recorded primary rate is {block['rate']!r} but its own counts give "
            f"{block['k']}/{block['n']} = {block['k'] / block['n']!r}. The stored summary has "
            "DRIFTED from the evidence it summarises, and the verdict below would be a judgement "
            "of the summary rather than of the reading",
        )

    _prove(
        matched["central_reading_seed"] == sigma_zero["seed"],
        f"the comparator's CENTRAL reading — the one `sigma_zero_verdict` pins as "
        f"`control_readings[0]` — is seed {matched['central_reading_seed']} while the σ=0 arm ran "
        f"at seed {sigma_zero['seed']}. The diagnostic compares this arm against THAT reading, so "
        "a different seed here would compare two different draws and call the difference DP",
    )
    _prove(
        sigma_zero["clip_bind_count"] == 0,
        f"the recorded σ=0 run bound its clip on {sigma_zero['clip_bind_count']} record(s) — the "
        "diagnostic is confounded by clipping rather than by the DP arithmetic. CARRIED FORWARD "
        "from the record rather than re-derived, so a σ=0 record whose non-binding proof was lost "
        "cannot reach a second verdict on the strength of the first one's",
    )
    _prove(
        mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR == matched["floor"],
        "`mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR` is "
        f"{mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR!r} while {mp.MATCHED_CONTROL_RECORD} "
        f"records {matched['floor']!r}. `sigma_zero_verdict`'s own refusal 2 would also catch this "
        "— naming BOTH sides here is what tells an operator WHICH of the two moved",
    )

    # The THREE AST gates, RE-RUN against live source. A `loop.py` or `teach_persona.py` edit
    # landing between 23-16 and now would silently un-match the comparator, and a verdict rendered
    # over an un-matched comparator is the exact defect this whole gap closure exists to correct.
    census = prove_matched_protocol()

    reading = sigma_zero["reading"]
    floor_value = mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR
    floor_provenance = mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE
    control_readings = matched["readings"]
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
        # D-04 FIRING A SECOND TIME. Not caught to soften it — caught so the record that names the
        # halt gets written and committed. No retry, no widened band, no override flag.
        verdict, halt_message = "HALT", str(halt)

    deviation = abs(reading - central)

    # The FIRST verdict's direction, re-derived from the σ=0 record's OWN two readings with
    # `sigma_zero_verdict`'s own expression, then CHECKED against the message that record already
    # carries — so the superseded block below quotes a decided outcome rather than restating one.
    superseded_direction = "BEATS" if reading > sigma_zero["control_central_reading"] else "misses"
    superseded_halt = sigma_zero["halt_message"]
    _prove(
        isinstance(superseded_halt, str) and superseded_direction in superseded_halt,
        f"the σ=0 record's own halt message does not contain {superseded_direction!r}: "
        f"{superseded_halt!r}. The superseded block quotes the FIRST verdict, so its direction has "
        "to come from that verdict's own message and not from this driver's recollection of it",
    )

    # ===== THE READ-THE-DENOMINATOR RULE, WHICH GOVERNS THE WHOLE BLOCK BELOW =====
    # Every `k` and every `n` this record carries is READ from its source record's own tier block.
    # NO DENOMINATOR IS TYPED HERE — not the taught set's, not the held-out set's, and nothing
    # carried forward from a docstring, a SUMMARY or a plan's prose. This is not fussiness:
    # 23-19-PLAN's first draft stated the σ=0 arm's taught-OFF tier as `0/648` when the record says
    # `0/1008`, and in a phase whose entire subject is *"was this compared against the right
    # denominator"*, a wrong denominator in a committed evidence artifact is disqualifying.
    # Read the block. Do not retype it. `taught_off` in particular is scored over the TAUGHT
    # question set, which is why it does NOT share the held-out tiers' denominator.
    #
    # `reduced: False` on EVERY tier, primary included: each number here is a RAW per-seed k/n, not
    # an aggregate. The only reduction in this phase is `noise_floor` over the five seeds' taught-ON
    # readings, and it lives in `floor` / `control_readings`, not in this block.
    secondary_readings = {
        source: {
            tier: {
                "k": blob[tier]["k"],
                "n": blob[tier]["n"],
                "rate": blob[tier]["rate"],
                "reduced": False,
            }
            for tier in _SCORED_TIERS
        }
        for source, blob in (("sigma_zero", sigma_zero), ("matched_control", matched_first))
    }

    record = {
        "record": mp.MATCHED_VERDICT_RECORD,
        # ===== THE VERDICT, AS THE RULE RETURNED IT =====
        "verdict": verdict,
        "verdict_rule": "phase23_prereg.sigma_zero_verdict",
        "halt_message": halt_message,
        # ===== THE σ=0 ARM: READ BACK, NEVER RE-MEASURED =====
        "reading": reading,
        "reading_source": _rel(sigma_zero_path),
        "sigma_zero_record_file_sha256": _sha256(sigma_zero_path),
        "sigma_zero_seed": sigma_zero["seed"],
        "sigma_zero_clip_bind_count": sigma_zero["clip_bind_count"],
        "sigma_zero_composed_steps": sigma_zero["composed_steps"],
        "sigma_zero_was_re_run": False,
        "sigma_zero_was_re_run_reason": (
            "the σ=0 arm's PROTOCOL never changed — only its comparator did — so its reading is "
            "read back from its committed record and re-derived from that record's own "
            "primary.k / primary.n, and no arm was re-run to obtain a different number"
        ),
        # ===== THE COMPARATOR =====
        "control_readings": control_readings,
        "control_record": _rel(matched_path),
        "control_record_file_sha256": _sha256(matched_path),
        "control_seeds": matched["seeds"],
        "central_reading": central,
        "central_reading_seed": matched["central_reading_seed"],
        # REPORTED, not decided: `sigma_zero_verdict` owns the comparison and this driver runs none.
        "deviation": deviation,
        "deviation_over_floor": deviation / floor_value,
        "floor": floor_value,
        "floor_pin_module": "mitigation_budget",
        "floor_pin_symbol": "MATCHED_CONTROL_NOISE_FLOOR",
        "floor_provenance_symbol": "MATCHED_CONTROL_NOISE_FLOOR_PROVENANCE",
        "floor_provenance": dict(floor_provenance),
        # ===== THE DISCLOSURE — a REQUIRED FIELD, refused below if absent or not True =====
        "sigma_zero_was_visible": True,
        "sigma_zero_visibility_disclosure": mp.SIGMA_ZERO_VISIBILITY_DISCLOSURE,
        "declared_differences": mp.MATCHED_DIFFERENCES,
        "equalised_mechanisms": matched["equalised_mechanisms"],
        "dp_fn_branch_census": [
            {"function": function, "condition": condition, "count": count}
            for (function, condition), count in sorted(census.items())
        ],
        # ===== THE FIRST VERDICT, QUOTED FROM ITS OWN RECORD RATHER THAN RETYPED =====
        "superseded_verdict": {
            "record": sigma_zero["record"],
            "verdict": sigma_zero["verdict"],
            "halt_message": superseded_halt,
            "floor": sigma_zero["floor"],
            "floor_pin_symbol": sigma_zero["floor_pin_symbol"],
            "central_reading": sigma_zero["control_central_reading"],
            "central_reading_seed": sigma_zero["control_central_reading_seed"],
            "control_record": sigma_zero["control_record"],
            "control_readings": sigma_zero["control_readings"],
            "deviation": sigma_zero["deviation"],
            "deviation_over_floor": sigma_zero["deviation"] / sigma_zero["floor"],
            "direction": superseded_direction,
            "it_was_not_wrong": (
                "THE FIRST VERDICT WAS NOT WRONG. It correctly measured this arm against a "
                "DIFFERENT TRAINING PROTOCOL: `is_dp = arm in DP_ARMS` switched the packer, the "
                "lot size and the gradient clip together, so the old control differed from the σ=0 "
                "arm by three measured mechanisms as well as by the DP seam. What is superseded is "
                "its COMPARATOR, not its arithmetic — every figure above still re-derives from "
                "that record, which is left byte-unchanged beside this one"
            ),
        },
        # ===== THE FOUR SCORED TIERS OF BOTH ARMS, EACH WITH ITS OWN DENOMINATOR =====
        "secondary_readings": secondary_readings,
        "secondary_readings_denominators_source": {
            "sigma_zero": f"{_rel(sigma_zero_path)} -> the record's own top-level tier blocks",
            "matched_control": f"{_rel(matched_path)} -> per_seed[0]'s own tier blocks",
            "rule": (
                "every k and n above is a SUBSCRIPT READ of the named block, never a literal. Both "
                "paths are named here so a reader can check every denominator against its origin "
                "without leaving this file. `taught_off` is scored over the TAUGHT question set "
                "and therefore does NOT share the held-out tiers' denominator"
            ),
        },
        "governs": (
            "WHETHER THE D-04 HALT SURVIVES A PROTOCOL-MATCHED COMPARATOR, and nothing else. The "
            "quantity judged is the TAUGHT RECALL RATE WITH THE ADAPTER ON (primary.k / primary.n, "
            "a count over QUESTIONS) — the same quantity both floors declare they govern. THIS "
            "RECORD DOES NOT UNBLOCK ANYTHING. Plans 23-11, 23-12, 23-13 and 23-14 remain BLOCKED "
            "whatever the verdict says; unblocking them is a separate, later act taken by a human "
            "who has READ this record, not a consequence of this driver's exit code"
        ),
        **provenance(),
    }

    # Checks the WHOLE `VERDICT_REQUIRED_KEYS` tuple, not only the two visibility keys, so an
    # omission anywhere in the blind-pinned set refuses the write rather than the review.
    mp.prove_verdict_record_declares_visibility(record)

    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")

    block = sigma_zero["primary"]
    print(
        f"[phase23_run] σ=0 reading (READ BACK, not re-run): {block['k']}/{block['n']} = "
        f"{reading!r} over {block['questions']} questions x {block['draws_per_question']} draws"
    )
    matched_block = matched_first["primary"]
    print(
        f"[phase23_run] matched central: {matched_block['k']}/{matched_block['n']} = {central!r} "
        f"(seed {matched['central_reading_seed']}) | deviation {deviation!r} | floor "
        f"{floor_value!r} = mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR"
    )
    print(f"[phase23_run] wrote {mp.MATCHED_VERDICT_RECORD}: verdict {verdict!r}")
    if halt_message is not None:
        print(halt_message)
        raise SystemExit(
            "[phase23_run] D-04 HALT RE-CONFIRMED and recorded at "
            f"{mp.MATCHED_VERDICT_RECORD}. THE SWEEP REMAINS HALTED WITH ZERO NOISED POINTS. The "
            "comparator was PROTOCOL-MATCHED on all three measured mechanisms — lot volume, "
            "teaching loss weight and gradient clip — and the breach survived it. THERE IS NO "
            "SECOND COMPARATOR: commit this record, and do NOT re-run, re-seed, widen or tune this "
            "arm to get a different number. 23-11..23-14 stay BLOCKED."
        )
    print(
        "[phase23_run] 23-11 / 23-12 / 23-13 / 23-14 REMAIN BLOCKED. This exit code unblocks "
        "NOTHING: unblocking them is a separate, later act taken by a human who has read "
        f"{mp.MATCHED_VERDICT_RECORD}, not a consequence of this driver returning normally."
    )


# =================================================================================================
# ===== (g) THE D-04 GATE — the MATCHED verdict AND the COMMITTED human unblock act =====
#
# TWO CONJUNCTS, NOT ONE. `results/phase23_matched_verdict.json`'s own `governs` field says *"THIS
# RECORD DOES NOT UNBLOCK ANYTHING … unblocking them is a separate, later act taken by a human"*, so
# the verdict alone is not the release condition. A gate reading only the verdict would contradict
# the record it reads.
#
# THE GATE READS `results/phase23_matched_verdict.json` AND NEVER `results/phase23_sigma_zero.json`.
# MEASURED: the σ=0 record carries `verdict == "HALT"` and 23-19 left it byte-unchanged ON PURPOSE
# so a reader sees both verdicts side by side. It will never say `proceed`; a gate pointed at it can
# never open, and a gate pointed at it and *made* to open would have to edit a frozen artifact.
#
# WRITTEN ONCE AND REUSED. `tests/test_phase23_matched.py` imports the sentinel, the pin and the
# predicate FROM HERE rather than carrying a second copy — a second copy of a gate is a second gate,
# free to drift. The direction is production -> test and not the reverse, for the reason
# `_count_composed_steps`' docstring already records: a production driver importing from `tests/`
# would make running this phase depend on the test tree being importable, and `tests/` is not a
# package.
# =================================================================================================

# The distinctive phrase from `.planning/STATE.md`'s dated unblock record, resolved by TEXT and
# never by line number — `tests/test_phase20_prereg.py:125-170` records this repository's own lesson
# that a line number survives no edit.
UNBLOCK_SENTINEL = (
    "UNBLOCKED 2026-08-28 — by the user, on evidence, after reading the verdict record"
)

# THE SHA PIN. `git log -S<sentinel>` returns a SET, not a commit, and this phase's own work GROWS
# it: 23-12 Task 1 lists `.planning/STATE.md` in its `<files>`, so a positional read would silently
# bind a different commit once that lands. MEMBERSHIP is asserted against THIS constant instead, and
# the ancestry and act-shape conjuncts are applied to THIS constant rather than to whichever sha the
# search happened to list first.
#
# PROVENANCE: `746ecf6`, 2026-08-28, by THE USER —
# `docs(23): pre-register CONTROL PROVENANCE, and unblock 23-11..23-14`. MEASURED: four paths, all
# planning documents, ZERO under `scripts/` or `src/`.
UNBLOCK_COMMIT = "746ecf699904e7c97bf73614e1c617a646da30ad"


def _git(*args):
    """``git`` in the repository root, refusing a non-zero exit."""
    return subprocess.run(
        ["git", *args], cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout


def paths_changed_by(sha):
    """The paths one commit touched — resolved at the CALL SITE so the seam takes it as an INPUT."""
    return _git("show", "--name-only", "--format=", sha).split()


def unblock_act_is_committed(*, sentinel, sha, changed_paths):
    """FIVE conjuncts over THREE CONSTRUCTED inputs. Returns ``(proven, reason, detail)``.

    The sentinel is the THIRD PARAMETER and deliberately not a module constant read from inside
    this function: the tripwire's absent-sentinel case drives a scratch string, and a predicate that
    closed over ``UNBLOCK_SENTINEL`` internally would leave that case undrivable short of
    monkeypatching this module — which tests the patch, not the guard.

    Sentinel + ancestry + ``git show HEAD:`` alone is FORGEABLE: **any** commit that introduces the
    phrase into ``.planning/STATE.md`` satisfies all three, and agent commits to that exact file are
    routine in this phase. The sha pin and the act-shape check are what bind the act to a HUMAN, and
    the ancestry and ``git show HEAD:`` checks are what stop an uncommitted or off-branch edit —
    neither subsumes the other, so all five are conjoined.

    Returns rather than raises, so the same predicate serves the committed test's BRANCH and this
    driver's ``_prove``. One gate, two callers.
    """
    code_paths = sorted(p for p in changed_paths if p.startswith(("scripts/", "src/")))
    detail = {
        "sha": sha,
        "sha_pinned": sha == UNBLOCK_COMMIT,
        "sentinel_shas": [],
        "sentinel_shas_n": 0,
        "sha_is_among_sentinel_shas": False,
        "is_ancestor_of_head": False,
        "sentinel_in_head_state": False,
        "changed_paths": sorted(changed_paths),
        "code_paths_in_act": code_paths,
        "act_touches_no_code": not code_paths,
        "date": None,
    }

    # (1) THE PIN — PROVENANCE. Checked first because it is the conjunct that binds the act to a
    # human; every other conjunct is satisfiable by a routine agent commit.
    if not detail["sha_pinned"]:
        return (
            False,
            f"still blocked — PROVENANCE: {sha!r} is not the pinned human unblock act "
            f"{UNBLOCK_COMMIT!r}. A guard a downstream plan can satisfy as a side effect of "
            "committing `.planning/STATE.md` is not a provenance guard",
            detail,
        )
    detail["date"] = _git("log", "-1", "--format=%ad", sha).strip()

    # (2) MEMBERSHIP — PRESENCE. Never a positional read; the returned set's size travels in the
    # message and in `detail` so a set that GREW is visible rather than silently absorbed.
    shas = _git("log", f"-S{sentinel}", "--format=%H", "--", ".planning/STATE.md").split()
    detail["sentinel_shas"] = shas
    detail["sentinel_shas_n"] = len(shas)
    detail["sha_is_among_sentinel_shas"] = sha in shas
    if not detail["sha_is_among_sentinel_shas"]:
        return (
            False,
            f"still blocked — PRESENCE: no commit in `.planning/STATE.md`'s history introduces the "
            f"sentinel {sentinel!r} at {sha!r}. `git log -S` returned {len(shas)} sha(s): {shas!r}",
            detail,
        )

    # (3) ANCESTRY — an off-branch act does not release anything on this branch.
    detail["is_ancestor_of_head"] = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=_ROOT, capture_output=True
        ).returncode
        == 0
    )
    if not detail["is_ancestor_of_head"]:
        return False, f"still blocked — ANCESTRY: {sha!r} is not an ancestor of HEAD", detail

    # (4) THE COMMITTED FILE, not the working tree — an uncommitted edit cannot open the branch.
    detail["sentinel_in_head_state"] = sentinel in _git("show", "HEAD:.planning/STATE.md")
    if not detail["sentinel_in_head_state"]:
        return (
            False,
            "still blocked — COMMITTED STATE: the sentinel is absent from "
            "`git show HEAD:.planning/STATE.md`, so any edit carrying it is uncommitted",
            detail,
        )

    # (5) THE SHAPE OF THE ACT. A human unblock act is a DOCUMENTATION act; an agent's routine
    # STATE.md commit carrying code alongside it is refused here even if the pin were satisfied.
    if not detail["act_touches_no_code"]:
        return (
            False,
            f"still blocked — ACT SHAPE: {sha!r} touched {code_paths!r} under `scripts/` or "
            "`src/`. The human unblock act is a documentation act and touched four planning "
            "documents and nothing else",
            detail,
        )

    return (
        True,
        f"UNBLOCKED by {sha!r} ({detail['date']}), {len(detail['changed_paths'])} planning "
        f"path(s), 0 under `scripts/` or `src/`; `git log -S<sentinel>` set size "
        f"{detail['sentinel_shas_n']}",
        detail,
    )


def prove_d04_gate():
    """The release condition, in front of every noised run. ``SystemExit`` naming D-04 on failure.

    Prints BOTH verdicts side by side first, so the log records that the reader saw both rather
    than only the one that opens the gate.
    """
    sigma_zero_record = json.loads((_ROOT / SIGMA_ZERO_RECORD).read_text(encoding="utf-8"))
    verdict_record = json.loads((_ROOT / mp.MATCHED_VERDICT_RECORD).read_text(encoding="utf-8"))
    print(
        f"[phase23_run] D-04 verdicts, BOTH read: {SIGMA_ZERO_RECORD} = "
        f"{sigma_zero_record['verdict']!r} | {mp.MATCHED_VERDICT_RECORD} = "
        f"{verdict_record['verdict']!r}. The gate reads the SECOND"
    )

    # CONJUNCT 1 — the verdict, from the record that actually carries one.
    _prove(
        verdict_record["verdict"] == "proceed",
        f"D-04: {mp.MATCHED_VERDICT_RECORD} carries verdict {verdict_record['verdict']!r}, not "
        "'proceed'. No noised sweep point may run. There is no override flag",
    )

    # CONJUNCT 2 — the COMMITTED human act, by the same route and the same five checks the
    # committed test asserts. Same function object, so the two cannot drift into two gates.
    proven, reason, detail = unblock_act_is_committed(
        sentinel=UNBLOCK_SENTINEL,
        sha=UNBLOCK_COMMIT,
        changed_paths=paths_changed_by(UNBLOCK_COMMIT),
    )
    _prove(
        proven,
        f"D-04: the verdict is 'proceed' but the human unblock act is NOT established — {reason}. "
        "The verdict record's own `governs` field says unblocking is a separate, later act taken "
        "by a human; a driver that ran on the verdict alone would contradict the record it reads",
    )
    print(f"[phase23_run] D-04 human act: {reason}")

    # The gate reads COMMITTED artifacts, and the σ=0 record the verdict was taken against is the
    # one still on disk — so a re-run σ=0 record cannot manufacture a release.
    live = _sha256(_ROOT / SIGMA_ZERO_RECORD)
    _prove(
        verdict_record["sigma_zero_record_file_sha256"] == live,
        f"D-04: the verdict record cites σ=0 file digest "
        f"{verdict_record['sigma_zero_record_file_sha256']!r} but {SIGMA_ZERO_RECORD} now hashes "
        f"to {live!r}. The release would rest on a record replaced since the verdict was taken",
    )
    tracked = _git("ls-files", SIGMA_ZERO_RECORD, mp.MATCHED_VERDICT_RECORD).split()
    _prove(
        sorted(tracked) == sorted((SIGMA_ZERO_RECORD, mp.MATCHED_VERDICT_RECORD)),
        f"D-04: `git ls-files` returns {tracked!r} for the two gate records. The gate reads "
        "COMMITTED artifacts; a working-tree-only record is not evidence",
    )
    print(f"[phase23_run] D-04 GATE OPEN: verdict 'proceed' AND the committed act {UNBLOCK_COMMIT}")
    return {
        "verdict_record": mp.MATCHED_VERDICT_RECORD,
        "verdict": verdict_record["verdict"],
        "sigma_zero_record": SIGMA_ZERO_RECORD,
        "sigma_zero_verdict": sigma_zero_record["verdict"],
        "sigma_zero_record_file_sha256": live,
        "unblock_commit": UNBLOCK_COMMIT,
        "unblock_commit_date": detail["date"],
        "unblock_commit_changed_paths": detail["changed_paths"],
        "unblock_commit_code_paths": detail["code_paths_in_act"],
        "unblock_sentinel_shas": detail["sentinel_shas"],
        "unblock_sentinel_shas_n": detail["sentinel_shas_n"],
        "gate_conjuncts": "matched verdict == 'proceed' AND the committed human unblock act",
    }


# =================================================================================================
# ===== (h) THE FIRST NOISED SWEEP POINT — dp_n64 at σ > 0 =====
# =================================================================================================

NOISED_ARM = "dp_n64"

# THE RUN PREFIX IS DELIBERATELY **NOT** `phase23_noised`. `arm_outputs(arm, prefix=)` renders
# `results/{prefix}_{arm}/run.csv`, and run.csv files ARE committed in this phase (see
# `results/phase23_sigma0_dp_n8/run.csv`). A prefix of `phase23_noised` would therefore file a CSV
# **inside** `NOISED_RECORD_GLOB` — the same defect the plan's own environment note raises against
# the run LOG, one artifact over: the glob every ordering guard binds on would gain a member that
# is not a sweep-point record, and `test_no_noised_point_exists`' derivation conjunct would try to
# `json.loads` a CSV. The `phase23_` head is retained because anything outside it falls outside the
# Phase-23 ancestry guards entirely.
NOISED_RUN_PREFIX = "phase23_sweep1"

# σ — A RESOURCE PARAMETER, BELONGING TO Z AND NOT TO THE GATE, and grounded on LIVE constraints.
#
# NOT justified by "σ >= 0.42 is where two-oracle agreement holds". **That figure was RETRACTED by
# 22-19** (`22-19-SUMMARY.md:123`: the sentence is *"false under both readings"*; `ROADMAP.md:125`
# carries the same retraction), and citing a retracted figure as a live premise inside the phase
# whose 23-12 enforces retract-in-place is not acceptable whatever σ it selects.
#
# THE TWO LIVE CONSTRAINTS IT IS CHECKED AGAINST:
#   * WARNING-5's breach regime is not on the publishing path at all. `22-VERIFICATION.md:301`
#     records that `sigma_for → epsilon_for → _delta_or_below_float64 → delta_closed → _log_erfc`
#     does not reach `delta_quadrature`, and `:310` records the published ε correct to ~1e-13 at
#     every point measured INCLUDING WARNING-5's worst.
#   * 22-17's measured two-oracle gap at the frozen δ is `1.0152e-11`, inside an UNWIDENED `1e-9`
#     budget (`ROADMAP.md:125`) — the LIVE agreement figure, quoted instead of the retracted edge.
#
# WHY 0.5 SPECIFICALLY: it is the σ THIS PHASE'S OWN committed CAL-03 wiring record already ran at
# (`results/phase23_cal03_wiring.json`, `sigma = 0.5` / `delta = 1e-05`), so it is a value a real
# sweep point plausibly uses rather than one chosen here. It round-trips through
# `noised_record_path`'s six-decimal rendering, which that function refuses if it does not.
NOISED_SIGMA = 0.5

# C — BINDING, and that is the difference from the σ=0 arm's C.
#
# At σ=0 the only thing C could do was clip, so `SIGMA_ZERO_CLIP_NORM = 1e6` was chosen to be
# NON-binding and the diagnostic was not confounded. At σ>0 C is also the NOISE SCALE:
# `dpsgd.py:_draw_noise` uses `std = self.sigma * self.C` on the SUM before the divide by N. A
# non-binding C=1e6 here would draw noise at std 500,000 against gradient norms measured in
# `[0.3359, 2.2901]` — an adapter destroyed by six orders of magnitude, whose stop behaviour would
# be pathological rather than representative, which is the one thing CAL-05's bracket must not be.
#
# 1.0 is this repository's established clip: it is the `grad_clip` the OLD unmitigated control ran
# at (`deferred-items.md`, mechanism 3), and it BINDS on the DP path's measured pre-clip norms
# (`.planning/debug/sigma-zero-beats-control.md`: 1.54-2.28 over 25 sampled steps, every one above
# 1.0) — which is what a real sweep point does.
NOISED_CLIP_NORM = 1.0

_WARMUP_DRAWS = 4  # `phase23_cost._MIN_WARMUP_ITERATIONS` — the MEASURED MPS stabilization point.


def noised_epsilon():
    """``epsilon_for(sigma, T, DELTA)`` at this run's σ and the production step budget."""
    import mitigation_unit  # LAZY — the same sibling-import register `phase23_cost` uses for torch.

    from personacore.privacy.accountant import epsilon_for

    return epsilon_for(NOISED_SIGMA, tp.MAX_STEPS, mitigation_unit.DELTA), mitigation_unit.DELTA


def train_noised(seed):
    """Train ``dp_n64`` at σ>0 and the FULL production shape, capturing the seam's own counters.

    Structurally :func:`train_sigma_zero` at the other capacity. ``MAX_STEPS`` is UNMONKEYPATCHED.
    ``dp_n64`` writes its OWN bins (``data/persona_dp_n64_train*.bin``) so there is no corpus
    collision with ``dp_n8``; there are no recorded digests to prove them against, because this is
    the arm's first build, so the digests are RECORDED here for whatever runs it next.

    The wall clock is bracketed by :func:`synchronized_seconds` — training has NO per-step host
    sync on MPS, so an unsynchronized bracket would time submission rather than completed work.
    """
    arm = NOISED_ARM
    facts, second_person, replay_ratio = tp.arm_spec(arm)
    _prove(
        len(facts) == 64,
        f"arm_spec({arm!r}) returns {len(facts)} facts, not 64. CAL-01's finding is that training "
        "is budgeted per CAPACITY, and this is the expensive capacity it is measured at",
    )
    _prove(
        replay_ratio == 0.0,
        f"arm_spec({arm!r}) returns replay_ratio {replay_ratio!r}, not 0.0. Under D-10 replay "
        "LEAVES the teaching bin on a DP arm and is drawn at train time; a non-zero ratio would "
        "bake replay windows in beside the fact windows and falsify grad_accum_steps = n_facts",
    )

    paths = tp.arm_outputs(arm, prefix=NOISED_RUN_PREFIX)
    resume_from, resumed_from_step = None, 0
    if paths["checkpoint"].exists() and not paths["adapter"].exists():
        resume_from = paths["checkpoint"]
        resumed_from_step = int(tp.torch.load(resume_from, weights_only=False)["step"])
        print(
            f"[phase23_run] noised: RESUMING {arm} from {resume_from} at step "
            f"{resumed_from_step} (23-07's seam). The timing leg covers "
            f"{tp.MAX_STEPS - resumed_from_step} of {tp.MAX_STEPS} steps and says so in the record"
        )

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
                prefix=NOISED_RUN_PREFIX,
                dp_sigma=NOISED_SIGMA,
                dp_clip_norm=NOISED_CLIP_NORM,
                resume_from=resume_from,
            )

    seam, composed = seam_box["seam"], seam_box["composed"]
    _prove(
        seam is not None,
        f"no DPSGD was constructed during the {arm!r} run. The seam is gated on `arm in DP_ARMS` "
        "and a run that constructed none is not a DP run at all",
    )

    stats = record["stats"]
    replay_windows = tp.replay_window_budget(stats["n_facts"]) // tp.BLOCK_SIZE
    timed = tp.MAX_STEPS - resumed_from_step
    _prove(
        len(composed) == timed,
        f"the seam composed {len(composed)} optimizer step(s) but the timed leg covers {timed}. T "
        "is COUNTED off real `DPSGD.finalize` invocations and a disagreement with the loop's own "
        "step budget means one of the two is describing a run that did not happen",
    )
    _prove(
        stats["n_facts"] == seam._records == 64,
        f"grad_accum_steps must be 64 at this capacity: n_facts {stats['n_facts']!r}, seam "
        f"_records {seam._records!r}. `teach_persona.py` sets grad_accum_steps = n_facts, so one "
        "optimizer step costs 64 backward passes plus the replay micro-batches below",
    )
    micro = math.ceil(replay_windows / tp.BATCH_SIZE)
    _prove(
        micro == 32,
        f"replay_micro_batches_per_step is {micro!r}, not the ceil(4*64/8) = 32 the production "
        "shape costs. The unit conversion is `replay_window_budget(n_facts) // BLOCK_SIZE`",
    )

    epsilon, delta = noised_epsilon()
    adapter = record["paths"]["adapter"]
    bins = {
        _rel(path): _sha256(path)
        for path in sorted(tp.arm_bin_targets(arm, paths))
        if path.exists()
    }
    return {
        "seed": seed,
        "arm": arm,
        "arm_run_prefix": NOISED_RUN_PREFIX,
        "sigma": NOISED_SIGMA,
        "clip_norm": NOISED_CLIP_NORM,
        "epsilon": epsilon,
        "delta": delta,
        "epsilon_rule": "personacore.privacy.accountant.epsilon_for(sigma, steps, delta)",
        # THE SEAM COUNTERS. `_clip_bind_count` is RUN-LIFETIME; `_records` is per-step and is the
        # LAST lot's size, which must equal the configured accum.
        "clip_bind_count": seam._clip_bind_count,
        "clip_bind_count_covers_steps": timed,
        "clip_is_binding": seam._clip_bind_count > 0,
        "records_per_lot": seam._records,
        "composed_steps": len(composed),
        "composed_lot_sizes": sorted(set(composed)),
        "t_source": "_count_composed_steps",
        # CAL-01's denominators, every one of them.
        "capacity_n_facts": stats["n_facts"],
        "grad_accum_steps": stats["n_facts"],
        "replay_windows_per_step": replay_windows,
        "replay_micro_batches_per_step": micro,
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
        "corpus_sha256": bins,
    }


def noised():
    """23-11 Task 2 — the FIRST noised sweep point of the milestone, at ``dp_n64``, σ > 0.

    ``_prove_no_noised_record_exists`` is deliberately NOT called. It refuses when the glob is
    non-empty, which is correct standing in front of σ=0 and WRONG standing in front of the sweep
    point that FILLS the glob. The durable property is the ORDERING, and that is what is asserted:
    the σ=0 record's earliest git add strictly precedes this one's.
    """
    _preconditions()
    gate = prove_d04_gate()

    seed = SEED_LADDER[0]
    epsilon, delta = noised_epsilon()
    print(
        f"[phase23_run] noised: {NOISED_ARM} at sigma={NOISED_SIGMA!r} C={NOISED_CLIP_NORM!r} "
        f"seed={seed} -> epsilon {epsilon!r} at delta {delta!r}, T={tp.MAX_STEPS}"
    )

    # DPSGD-06's ORDERING, asserted BEFORE the run rather than only afterwards in git.
    sigma_zero_adds = _git("log", "--diff-filter=A", "--format=%H", "--", SIGMA_ZERO_RECORD).split()
    _prove(
        sigma_zero_adds,
        f"{SIGMA_ZERO_RECORD} has no git add. DPSGD-06 requires σ=0 to be the DP arm's FIRST "
        "executed run, and an uncommitted σ=0 record cannot precede anything",
    )
    print(f"[phase23_run] σ=0 record first added at {sigma_zero_adds[-1]} — this point follows it")

    path = _ROOT / noised_record_path(NOISED_ARM, NOISED_SIGMA)
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )

    if not _already_trained("noised", seed):
        _state_record("noised", seed, train_noised(seed))
    trained = _state_load()["noised"][str(seed)]

    training = {
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
        "bracket_covers": "the whole train_arm call: build_arm_bins + base load + the "
        "max_steps-step loop (in-loop evals, checkpoint writes, replay memmap I/O) + both "
        "end-of-run masked_perplexity sweeps",
        # EVERY TIMING KEY NAMES ITS PROTOCOL. A timing that does not say which protocol it timed
        # is not a usable figure — the two measured NON-DP protocols differ in wall clock by a
        # factor this phase's cost record carries as `wall_clock_gap_vs_superseded`.
        "protocol": f"{NOISED_ARM}, seam active, sigma>0",
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

    # ===== (d) THE T CROSS-CHECK, AT ZERO EXTRA COST =====
    sigma_zero_record = json.loads((_ROOT / SIGMA_ZERO_RECORD).read_text(encoding="utf-8"))
    t_n8 = sigma_zero_record["composed_steps"]
    t_n64 = trained["composed_steps"]
    _prove(
        t_n64 == t_n8,
        f"T DISAGREES ACROSS CAPACITIES: n=8 composed {t_n8!r} optimizer steps and n=64 composed "
        f"{t_n64!r} at the same {tp.MAX_STEPS}-step budget. That is the N-leak into the composed "
        "step count CAL-03 asks about, now asked of two REAL production runs",
    )
    print(
        f"[phase23_run] T cross-check: t_n8 = {t_n8} == t_n64 = {t_n64} "
        "(both _count_composed_steps)"
    )

    record = {
        "record": noised_record_path(NOISED_ARM, NOISED_SIGMA),
        # THE DECLARATION THAT MAKES THIS RECORD A MEMBER OF THE GLOB BY ITS OWN CONTENT. This run
        # exports an adapter with its sha256, scores real questions on the real attack shapes in
        # the `throughput` leg, and runs the UNMONKEYPATCHED production budget — so it fails all
        # three substantive legs of `phase23_prereg`'s `CAL03_WIRING_RECORD` exemption and cannot
        # honestly declare `sweep_point: false`.
        "sweep_point": True,
        "exports_adapter": True,
        # `arm` AND `sigma` AT TOP LEVEL, because that pair is what reproduces this record's OWN
        # path: `test_no_noised_point_exists`' derivation conjunct calls
        # `phase23_prereg.noised_record_path(payload["arm"], payload["sigma"])` on every tracked
        # member of the glob and refuses a hand-typed sweep-point path. A record carrying its arm
        # only under `training` or `recipe` is not self-describing at the level the guard reads.
        "arm": trained["arm"],
        "sigma": trained["sigma"],
        "clip_norm": trained["clip_norm"],
        "epsilon": trained["epsilon"],
        "delta": trained["delta"],
        "epsilon_rule": trained["epsilon_rule"],
        "sigma_provenance": (
            "sigma = 0.5 is the value this phase's own committed CAL-03 wiring record "
            "(results/phase23_cal03_wiring.json) already ran at, at delta = 1e-05. It is NOT "
            "justified by the 'two-oracle agreement holds at sigma >= 0.42' figure, which 22-19 "
            "RETRACTED as false under both readings. The live constraints it is checked against "
            "are 22-VERIFICATION.md:301 (the publishing path sigma_for -> epsilon_for -> "
            "_delta_or_below_float64 -> delta_closed -> _log_erfc does not reach delta_quadrature "
            "at all, which is what bounds WARNING-5) and :310 (the published epsilon correct to "
            "~1e-13 at every point measured, including WARNING-5's worst); the live two-oracle "
            "gap at the frozen delta is 1.0152e-11 inside an UNWIDENED 1e-9 budget."
        ),
        "clip_provenance": (
            "C = 1.0 BINDS, deliberately. dpsgd._draw_noise uses std = sigma * C on the summed "
            "accumulator before the divide by N, so C is the noise scale as well as the clip at "
            "sigma > 0: the sigma=0 arm's non-binding C = 1e6 would draw noise at std 500000 "
            "against gradient norms measured in [0.3359, 2.2901] and destroy the adapter, making "
            "its stop behaviour pathological rather than representative. 1.0 is the grad_clip the "
            "OLD unmitigated control ran at, and it binds on the DP path's measured pre-clip "
            "norms (1.54-2.28 over 25 sampled steps)."
        ),
        "clip_bind_count": trained["clip_bind_count"],
        "clip_bind_count_covers_steps": trained["clip_bind_count_covers_steps"],
        "clip_is_binding": trained["clip_is_binding"],
        "records_per_lot": trained["records_per_lot"],
        "composed_steps": trained["composed_steps"],
        "composed_lot_sizes": trained["composed_lot_sizes"],
        "t_source": trained["t_source"],
        # ===== THE T CROSS-CHECK, AND WHAT IT DOES NOT CLAIM =====
        "t_n8": t_n8,
        "t_n64": t_n64,
        "t_matches_across_capacities": t_n64 == t_n8,
        "t_n8_source_record": SIGMA_ZERO_RECORD,
        "epsilon_comparison_made": False,
        "epsilon_comparison_omitted_reason": (
            "The two runs are at DIFFERENT sigma (0.0 and 0.5) and D-05 requires a FIXED sigma "
            "for an epsilon comparison, so this leg tests T ONLY. CAL-03's verdict is read from "
            "results/phase23_cal03_wiring.json (verdict true, t_n8 = t_n64 = 4 at a fixed sigma "
            "= 0.5), which this record does not replace."
        ),
        "ppl_adapter_on": trained["ppl_adapter_on"],
        "ppl_adapter_off": trained["ppl_adapter_off"],
        "ppl_scored_targets": trained["ppl_scored_targets"],
        "training": training,
        "gate": gate,
        "recipe": {
            "arm": NOISED_ARM,
            "prefix": NOISED_RUN_PREFIX,
            "facts": "teach_persona.arm_spec('dp_n64') — 8 locked + 56 filler",
            "n_facts": trained["capacity_n_facts"],
            "family_ids": sorted(fs.TAUGHT_FAMILY_IDS),
            "second_person": False,
            "replay_ratio_in_bin": 0.0,
            "corpus_sha256": trained["corpus_sha256"],
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
        "governs": (
            "NOTHING BEYOND ITS OWN FIGURES. This is CAL-01's training measurement at the "
            "expensive capacity and the adapter CAL-05's throughput bracket is measured on. It "
            "renders no verdict, reduces no floor and unblocks nothing."
        ),
        "seed": seed,
        **provenance(),
    }
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"[phase23_run] {NOISED_ARM}: {trained['seconds_total']!r} s over "
        f"{trained['timed_iterations']} optimizer steps = "
        f"{trained['seconds_per_optimizer_step']!r} s/step, grad_accum_steps "
        f"{trained['grad_accum_steps']}, replay micro-batches "
        f"{trained['replay_micro_batches_per_step']}, clip bound on "
        f"{trained['clip_bind_count']} record(s)"
    )
    print(f"[phase23_run] wrote {record['record']}")


# =================================================================================================
# ===== (i) CAL-05 — THE THROUGHPUT BRACKET, floor to ceiling, on the REAL attack shapes =====
#
# THE COMMITTED 4.77 h/point FIGURE WAS MEASURED ON THE UN-ADAPTED BASE, where 45-56 of 64 draws
# per shape terminated on a stop id (`results/phase18_preflight_report.md`). A noised adapter that
# stops emitting EOS runs EVERY draw to the full `RECALL_MAX_NEW_TOKENS = 48`, and
# `generation/core.py:79`'s per-token `int(next_id)` device->host sync makes wall clock close to
# linear in tokens emitted — which is what makes floor-vs-ceiling a MEASURABLE question rather than
# an unbounded worry. Both ends are measured here; neither is a mean.
# =================================================================================================

# `.planning/ROADMAP.md:47` / `.planning/REQUIREMENTS.md:179` — the sweep this record prices.
_SWEEP_POINTS = 16

_THROUGHPUT_CONDITIONS = ("noised_floor", "noised_ceiling", "base_floor")


@contextlib.contextmanager
def _captured_completion_lengths(recall):
    """Shadow ``phase14_recall._complete`` to record the TOKEN COUNT of every draw.

    ``draw_all`` returns decoded strings and a stop flag, not lengths, and ``mean_tokens_floor`` /
    ``mean_tokens_ceiling`` are REQUIRED keys of ``phase23_cost.GENERATION_RECORD_KEYS``. The
    shadow sits at the module global ``draw_all`` resolves through — the only place the per-draw id
    list is reachable from outside without a SECOND copy of the draw loop, and a duplicated draw
    loop is how two conditions silently stop being paired.
    """
    lengths = []
    real = recall._complete

    def counting(*args, **kwargs):
        gen_ids, stopped = real(*args, **kwargs)
        lengths.append(len(gen_ids))
        return gen_ids, stopped

    recall._complete = counting
    try:
        yield lengths
    finally:
        recall._complete = real


@contextlib.contextmanager
def _stop_ids_override(recall, value):
    """THE CEILING CONDITION, as a two-line patch rather than a second generation path.

    ``_complete`` reads ``STOP_IDS`` through a module-global lookup at CALL time
    (``stop_ids=set(STOP_IDS)``), so emptying the module attribute empties the stop set for every
    draw underneath — and ``len(gen) < RECALL_MAX_NEW_TOKENS`` then reports ``False`` on every
    draw, which is the ceiling condition's own consistency check.
    """
    real = recall.STOP_IDS
    recall.STOP_IDS = value
    try:
        yield
    finally:
        recall.STOP_IDS = real


def _measure_condition(*, label, model, tok, forbid, by_family, values, stop_ids):
    """One (model, stop-condition) pair over all four attack shapes. Returns a per-shape list.

    ``>= 4`` warm-up draws are DISCARDED per shape before the bracket opens — the MEASURED MPS
    stabilization point (``phase23_cost._MIN_WARMUP_ITERATIONS``): the first MPS kernels of a
    process pay lazy compilation and allocator warm-up, and a shorter warm-up times that instead of
    generation. The timed leg is then ``SMOKE_PROMPTS_PER_SHAPE * SMOKE_DRAWS_PER_PROMPT = 64``
    draws, the same denominator ``results/phase18_preflight_report.md`` published its rates over,
    on the SAME strided prompt sample — which is what makes the base-condition leg a
    cross-validation rather than a second, differently-shaped measurement.
    """
    import phase14_recall as recall  # LAZY — teach_persona's own register for this pair.
    import phase18_extraction as x18  # LAZY — same rule; it is a heavy, torch-touching module.

    shapes = []
    with _stop_ids_override(recall, stop_ids):
        for family in x18.ATTACK_FAMILIES:
            sample = x18._smoke_sample(by_family[family])
            _prove(
                len(sample) == x18.SMOKE_PROMPTS_PER_SHAPE,
                f"shape {family!r} sampled {len(sample)} prompts against the pre-registered "
                f"{x18.SMOKE_PROMPTS_PER_SHAPE}. Every per-shape rate below is over that "
                "denominator, and a short sample would publish a throughput describing fewer "
                "prompts than the record claims it covers",
            )

            # WARM-UP, DISCARDED. Untimed, and its lengths are thrown away with it.
            with _captured_completion_lengths(recall):
                recall.draw_all(
                    model,
                    tok,
                    sample[0]["prompt_ids"],
                    device(),
                    forbid,
                    sample[0]["seed_index"] * x18.K,
                    n_samples=_WARMUP_DRAWS - 1,
                )

            stops, drawn_n = 0, 0
            box = {}
            with _captured_completion_lengths(recall) as lengths:
                with synchronized_seconds(box):
                    for entry in sample:
                        # PERS-06 — nothing draws unchecked, on the ids about to be dispatched.
                        # D-16's partition, recovered by `_guarded_span` rather than re-derived.
                        base_ids = x18._guarded_span(entry)
                        recall.assert_no_value_in_prompt(
                            tok, tok.decode(base_ids), values, prompt_ids=base_ids
                        )
                        drawn, stopped = recall.draw_all(
                            model,
                            tok,
                            entry["prompt_ids"],
                            device(),
                            forbid,
                            entry["seed_index"] * x18.K,
                            n_samples=x18.SMOKE_DRAWS_PER_PROMPT - 1,
                        )
                        stops += sum(1 for flag in stopped if flag)
                        drawn_n += len(drawn)
            _prove(
                len(lengths) == drawn_n,
                f"shape {family!r} captured {len(lengths)} completion length(s) for {drawn_n} "
                "draw(s). `mean_tokens_*` is a rate over the draw count and the two denominators "
                "must be the same number",
            )
            minutes = box["seconds"] / 60
            _prove(
                minutes > 0,
                f"shape {family!r} timed {minutes!r} minutes. A zero-width bracket publishes an "
                "infinite rate, which compares False against every budget bound",
            )
            shapes.append(
                {
                    "shape": family,
                    "prompts": len(sample),
                    "n_draws": drawn_n,
                    "minutes": minutes,
                    "rate_draws_per_min": drawn_n / minutes,
                    "stop_terminated_n": stops,
                    "mean_tokens": sum(lengths) / len(lengths),
                    "total_tokens": sum(lengths),
                    "max_tokens_possible": recall.RECALL_MAX_NEW_TOKENS,
                }
            )
            print(
                f"[phase23_run] throughput {label} {family}: "
                f"{shapes[-1]['rate_draws_per_min']:.2f} draws/min, "
                f"{stops}/{drawn_n} stop-terminated, mean {shapes[-1]['mean_tokens']:.2f} tokens"
            )
    return shapes


def _committed_phase18_rates():
    """The four committed per-shape rates, PARSED from the artifact — never retyped here.

    ``results/phase18_preflight_report.md`` is the cross-validation target and it is a committed
    file; a literal here would be a second source for a figure that already has one, free to stop
    agreeing with it.
    """
    import re

    report = (_ROOT / "results" / "phase18_preflight_report.md").read_text(encoding="utf-8")
    rates = {
        shape: float(rate)
        for shape, rate in re.findall(
            r"^- `([A-Za-z0-9-]+)`: ([0-9.]+) draws_per_min", report, flags=re.MULTILINE
        )
    }
    _prove(
        len(rates) == 4,
        f"parsed {len(rates)} committed per-shape rate(s) from "
        f"results/phase18_preflight_report.md: {rates!r}. The cross-validation needs all four, and "
        "a parse that silently found fewer would report agreement over a shorter list",
    )
    return rates


def throughput():
    """23-11 Task 3 Part A — CAL-05's floor-to-ceiling bracket on the REAL noised adapter.

    THREE CONDITIONS, and the third is what makes the first two interpretable:

      * **FLOOR** — the noised adapter with ``STOP_IDS`` ACTIVE, the Phase-18 condition.
      * **CEILING** — the noised adapter with the stop set EMPTIED, so every draw runs the full
        ``RECALL_MAX_NEW_TOKENS``. This is the worst case a noised adapter that stops emitting EOS
        produces, and measuring it is what turns the ceiling into a number rather than a worry.
      * **BASE FLOOR** — the UN-ADAPTED base under the floor condition, cross-validated per shape
        against ``results/phase18_preflight_report.md``'s committed rates. A large divergence means
        the hardware or the stack moved and the committed cost artifact needs revisiting BEFORE Z
        is sized on it.

    Writes the measurement into the working state; ``cost-record`` assembles it. The split is
    deliberate: Part B is pure arithmetic over committed records, and coupling it to this leg would
    make an assembly bug cost a second GPU run.
    """
    import phase14_recall as recall  # LAZY — teach_persona's own register for this pair.
    import phase16_persistence as persistence  # LAZY — same rule.
    import phase17_persona_gate as base_gate  # LAZY — build_unadapted_base lives here.
    import phase18_extraction as x18  # LAZY — same rule.

    from personacore.tokenizer import from_json

    _preconditions()
    prove_d04_gate()

    noised_record = json.loads(
        (_ROOT / noised_record_path(NOISED_ARM, NOISED_SIGMA)).read_text(encoding="utf-8")
    )
    adapter = _ROOT / noised_record["training"]["adapter"]
    _prove(
        adapter.exists() and _sha256(adapter) == noised_record["training"]["adapter_sha256"],
        f"{adapter} is missing or does not hash to the noised record's "
        f"{noised_record['training']['adapter_sha256']!r}. CAL-05's bracket is a claim about THAT "
        "adapter and a different one on disk would measure a different model",
    )
    print(f"[phase23_run] throughput: adapter {noised_record['training']['adapter']}")

    tok = from_json(recall.TOKENIZER_PATH)  # FROZEN production artifact — never retrained.
    corpus = x18.build_corpus(tok)
    by_family = {}
    for entry in corpus["prompts"]:
        by_family.setdefault(entry["family"], []).append(entry)
    values = [fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]

    # ===== THE NOISED ADAPTER, both stop conditions, in ONE process on ONE set of weights =====
    model, _cfg, adapted_tok, adapted_forbid, _artifact = recall.load_adapted_model(
        device(), adapter
    )
    floor_shapes = _measure_condition(
        label="noised_floor",
        model=model,
        tok=adapted_tok,
        forbid=adapted_forbid,
        by_family=by_family,
        values=values,
        stop_ids=recall.STOP_IDS,
    )
    ceiling_shapes = _measure_condition(
        label="noised_ceiling",
        model=model,
        tok=adapted_tok,
        forbid=adapted_forbid,
        by_family=by_family,
        values=values,
        stop_ids=frozenset(),
    )
    del model

    # ===== THE UN-ADAPTED BASE, floor condition — Phase 18's own construction, reproduced =====
    base_model, base_cfg, base_ckpt = base_gate.build_unadapted_base(device())
    base_forbid, _digest = persistence.resolve_forbid(tok, base_cfg.vocab_size)
    base_forbid = base_forbid.to(device())
    print(f"[phase23_run] base fingerprint: sha={base_ckpt['git_sha']} step={base_ckpt['step']}")
    base_shapes = _measure_condition(
        label="base_floor",
        model=base_model,
        tok=tok,
        forbid=base_forbid,
        by_family=by_family,
        values=values,
        stop_ids=recall.STOP_IDS,
    )
    del base_model

    # ===== THE DRAW GEOMETRY, COMPUTED FROM THE LIVE CORPUS — never retyped =====
    questions = sum(len(by_family[family]) for family in x18.ATTACK_FAMILIES)
    k_per_question = x18.K
    sigma_zero_record = json.loads((_ROOT / SIGMA_ZERO_RECORD).read_text(encoding="utf-8"))
    family_zero_prompts = sigma_zero_record["questions_taught"]
    family_zero_draws = 1 + recall.N_SEEDED_SAMPLES
    draws_per_point = questions * k_per_question + family_zero_prompts * family_zero_draws

    def compose(shapes):
        """Phase 18's OWN projection method, reproduced: per-shape minutes, summed.

        Family zero is not one of the four measured shapes, so it is priced at the SLOWEST measured
        rate — the conservative choice, and the one `results/phase18_preflight_report.md` states
        rather than hides.
        """
        rate = {s["shape"]: s["rate_draws_per_min"] for s in shapes}
        slowest = min(rate.values())
        minutes = sum(
            len(by_family[family]) * k_per_question / rate[family] for family in x18.ATTACK_FAMILIES
        )
        minutes += family_zero_prompts * family_zero_draws / slowest
        return minutes, slowest

    floor_minutes, floor_slowest = compose(floor_shapes)
    ceiling_minutes, ceiling_slowest = compose(ceiling_shapes)

    committed = _committed_phase18_rates()
    cross_validation = []
    for shape in base_shapes:
        target = committed[shape["shape"]]
        cross_validation.append(
            {
                "shape": shape["shape"],
                "measured_rate_draws_per_min_floor": shape["rate_draws_per_min"],
                "committed_rate_draws_per_min_floor": target,
                "agreement_percent": 100.0 * shape["rate_draws_per_min"] / target,
                "n_draws": shape["n_draws"],
                "stop_terminated_n_floor": shape["stop_terminated_n"],
                "mean_tokens_floor": shape["mean_tokens"],
            }
        )
        print(
            f"[phase23_run] cross-validation {shape['shape']}: measured "
            f"{shape['rate_draws_per_min']:.2f} vs committed {target:.2f} draws/min = "
            f"{cross_validation[-1]['agreement_percent']:.2f}%"
        )

    floor_total_draws = sum(s["n_draws"] for s in floor_shapes)
    ceiling_total_draws = sum(s["n_draws"] for s in ceiling_shapes)
    floor_total_minutes = sum(s["minutes"] for s in floor_shapes)
    ceiling_total_minutes = sum(s["minutes"] for s in ceiling_shapes)
    pooled_floor_rate = floor_total_draws / floor_total_minutes
    pooled_ceiling_rate = ceiling_total_draws / ceiling_total_minutes
    floor_tokens = sum(s["total_tokens"] for s in floor_shapes) / floor_total_draws
    ceiling_tokens = sum(s["total_tokens"] for s in ceiling_shapes) / ceiling_total_draws

    per_shape = []
    for f, c, b in zip(floor_shapes, ceiling_shapes, base_shapes, strict=True):
        _prove(
            f["shape"] == c["shape"] == b["shape"],
            f"the three conditions disagree on shape order: {f['shape']!r} / {c['shape']!r} / "
            f"{b['shape']!r}. Every multiplier below is a per-shape ratio and a mis-zipped pair "
            "would divide one shape's rate by another's",
        )
        per_shape.append(
            {
                "shape": f["shape"],
                "prompts": f["prompts"],
                "n_draws": f["n_draws"],
                "draws_per_min_floor": f["rate_draws_per_min"],
                "draws_per_min_ceiling": c["rate_draws_per_min"],
                "draws_per_min_base_floor": b["rate_draws_per_min"],
                "stop_terminated_n_floor": f["stop_terminated_n"],
                "stop_terminated_n_ceiling": c["stop_terminated_n"],
                "stop_terminated_n_base_floor": b["stop_terminated_n"],
                "mean_tokens_floor": f["mean_tokens"],
                "mean_tokens_ceiling": c["mean_tokens"],
                "mean_tokens_base_floor": b["mean_tokens"],
                "wall_multiplier": f["rate_draws_per_min"] / c["rate_draws_per_min"],
                "token_multiplier": c["mean_tokens"] / f["mean_tokens"],
                "minutes_floor": f["minutes"],
                "minutes_ceiling": c["minutes"],
            }
        )

    generation = {
        # THE BRACKET. Two REQUIRED keys measured under two different stop conditions, and NO bare
        # mean anywhere — `phase23_cost.validate_record` refuses one at any nesting depth.
        "h_per_point_floor": floor_minutes / 60,
        "h_per_point_ceiling": ceiling_minutes / 60,
        "wall_multiplier": pooled_floor_rate / pooled_ceiling_rate,
        "token_multiplier": ceiling_tokens / floor_tokens,
        "draws_per_point": draws_per_point,
        "k_per_question": k_per_question,
        "questions": questions,
        "n_draws_measured": floor_total_draws
        + ceiling_total_draws
        + sum(s["n_draws"] for s in base_shapes),
        "stop_terminated_n_floor": sum(s["stop_terminated_n"] for s in floor_shapes),
        "stop_terminated_n_ceiling": sum(s["stop_terminated_n"] for s in ceiling_shapes),
        "mean_tokens_floor": floor_tokens,
        "mean_tokens_ceiling": ceiling_tokens,
        "attack_shapes": list(x18.ATTACK_FAMILIES),
        "adapter_source": noised_record["training"]["adapter"],
        "adapter_sha256": noised_record["training"]["adapter_sha256"],
        "sigma": NOISED_SIGMA,
        "protocol": (
            f"{NOISED_ARM} adapter at sigma={NOISED_SIGMA}, {x18.SMOKE_PROMPTS_PER_SHAPE} strided "
            f"prompts x {x18.SMOKE_DRAWS_PER_PROMPT} draws per shape per condition, "
            f"{_WARMUP_DRAWS} warm-up draws discarded per shape, MPS fp32"
        ),
        # THE DENOMINATORS AND THE PROBE'S BOUNDS, stated rather than implied.
        "per_shape": per_shape,
        "pooled_draws_per_min_floor": pooled_floor_rate,
        "pooled_draws_per_min_ceiling": pooled_ceiling_rate,
        "slowest_draws_per_min_floor": floor_slowest,
        "slowest_draws_per_min_ceiling": ceiling_slowest,
        "family_zero_prompts": family_zero_prompts,
        "family_zero_draws_per_prompt": family_zero_draws,
        "family_zero_rate_source": "the SLOWEST measured shape rate, Phase 18's own convention",
        "warmup_draws_discarded_per_shape": _WARMUP_DRAWS,
        "timed_draws_per_shape_per_condition": floor_shapes[0]["n_draws"],
        "h_per_point_composition": (
            "sum over the four attack shapes of (prompts_in_shape * K / that shape's measured "
            "rate), plus family zero's prompts * draws priced at the SLOWEST measured rate — "
            "results/phase18_preflight_report.md's own projection method, reproduced so the two "
            "figures are comparable"
        ),
        "cross_validation_vs_phase18": cross_validation,
        "cross_validation_source_record": "results/phase18_preflight_report.md",
        "probe_bounds": (
            f"{len(x18.ATTACK_FAMILIES)} prompt shapes, "
            f"{floor_shapes[0]['n_draws']} timed draws per shape per condition, ONE process, ONE "
            f"adapter, ONE sigma ({NOISED_SIGMA}). The noised adapter's STOP RATE is the quantity "
            "this bracket exists to capture and both extremes are recorded; nothing here claims a "
            "value between them was measured."
        ),
        **provenance(),
    }
    phase23_cost.validate_record(generation, kind="generation")
    _state_record("throughput", f"{NOISED_SIGMA:.6f}", generation)
    print(
        f"[phase23_run] CAL-05 bracket: h_per_point_floor {generation['h_per_point_floor']!r} -> "
        f"h_per_point_ceiling {generation['h_per_point_ceiling']!r} over "
        f"{draws_per_point} draws/point; wall x{generation['wall_multiplier']!r}, token "
        f"x{generation['token_multiplier']!r}"
    )


# =================================================================================================
# ===== (j) THE COST RECORD — four training legs, each naming its protocol, and the bracket =====
# =================================================================================================


def _aggregate_training_block(*, per_seed_timings, source_record, protocol, shape, extra):
    """A FIVE-SEED aggregate that satisfies ``TRAINING_RECORD_KEYS``, by the COMMITTED convention.

    The convention is NOT invented here. ``results/phase23_never_taught_training.json`` is itself a
    five-seed aggregate that already satisfies those keys at top level, and MEASURED at HEAD its
    convention is: ``seed`` is the LIST, ``seconds_total`` the SUM across seeds (never their mean),
    ``timed_iterations`` the SUM of timed steps, ``seconds_per_optimizer_step`` their quotient, and
    ``warmup_iterations_discarded`` 0. Followed exactly, for both borrowed non-DP blocks.

    The per-seed list, mean, min and max ride BESIDE the required keys as extra fields — never
    instead of them, and never under a ``FORBIDDEN_MEAN_KEYS`` name.
    """
    seeds = sorted(per_seed_timings)
    seconds = [float(per_seed_timings[s]) for s in seeds]
    timed = sum(shape["max_steps"] for _ in seeds)
    block = {
        "seconds_total": sum(seconds),
        "timed_iterations": timed,
        "seconds_per_optimizer_step": sum(seconds) / timed,
        "warmup_iterations_discarded": 0,
        "seed": [int(s) for s in seeds],
        "n_seeds": len(seeds),
        # THE PUBLISHED PER-POINT FIGURE. `training_seconds_mean` is a NEW name and is deliberately
        # not one of `FORBIDDEN_MEAN_KEYS` — that register exists to stop a bare per-POINT cost
        # standing in for the floor/ceiling bracket, not to stop a five-seed training mean riding
        # beside `seconds_total` with its own denominator.
        "training_seconds_mean": sum(seconds) / len(seconds),
        "training_seconds_per_seed": {str(s): float(per_seed_timings[s]) for s in seeds},
        "training_seconds_min": min(seconds),
        "training_seconds_max": max(seconds),
        "training_seconds_total": sum(seconds),
        "protocol": protocol,
        "source_record": source_record,
        "source_record_sha256": _sha256(_ROOT / source_record),
        **shape,
        **extra,
    }
    phase23_cost.validate_record(block, kind="training")
    return block


def _borrowed_training_block(*, block, source_record, protocol, extra=None):
    """A single-run block LIFTED WHOLE from a committed record, with its digest attached."""
    out = {
        **block,
        "protocol": protocol,
        "source_record": source_record,
        "source_record_sha256": _sha256(_ROOT / source_record),
        **(extra or {}),
    }
    phase23_cost.validate_record(out, kind="training")
    return out


def cost_record():
    """23-11 Task 3 Part B — assemble and write ``results/phase23_cost.json``.

    **EVERY FIGURE THIS RECORD PUBLISHES IS A NAMED NUMERIC FIELD AT FULL STORED PRECISION,
    COMPUTED AND NEVER TYPED.** ``json.dump`` serialises floats through ``float.__repr__``, so the
    bytes in this file and the string a reader gets from ``repr(json.load(...)[path])`` are the
    SAME string — but only when the value was computed rather than hand-entered. A hand-typed digit
    breaks 23-12's verbatim-containment guard, and breaks it as a RED on a figure that LOOKS
    correct. Measured while drafting: a hand-typed ``1743.8820147753301`` round-tripped to
    ``…302``. Nothing below is retyped from any plan's prose.

    **THE ``training.non_dp`` PROVENANCE DECISION, MADE HERE AND ARGUED IN THE RECORD.** Three
    non-DP figures exist and they disagree materially; ``training.non_dp`` comes from
    ``results/phase23_matched_control.json``. See ``provenance_argument`` in the emitted record.
    ``deferred-items.md``'s CONTROL PROVENANCE rule governs the formal gate's three UTILITY fields
    and **not** timing, so this decision is made on its own merits rather than inherited.
    """
    path = _ROOT / COST_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )

    matched = json.loads((_ROOT / mp.MATCHED_CONTROL_RECORD).read_text(encoding="utf-8"))
    old = json.loads((_ROOT / CONTROL_FLOOR_RECORD).read_text(encoding="utf-8"))
    sigma_zero_record = json.loads((_ROOT / SIGMA_ZERO_RECORD).read_text(encoding="utf-8"))
    noised = json.loads(
        (_ROOT / noised_record_path(NOISED_ARM, NOISED_SIGMA)).read_text(encoding="utf-8")
    )
    never_taught = json.loads((_ROOT / NEVER_TAUGHT_TRAINING_RECORD).read_text(encoding="utf-8"))
    generation = _state_load()["throughput"][f"{NOISED_SIGMA:.6f}"]
    phase23_cost.validate_record(generation, kind="generation")

    # ===== training.non_dp — the PROTOCOL-MATCHED comparator, ASSEMBLED from three levels =====
    # MEASURED at HEAD: `results/phase23_matched_control.json` is missing ALL THIRTEEN of the
    # `TRAINING_RECORD_KEYS` at top level. Every one is reachable, but from three different places.
    ms = matched["per_seed"][0]
    non_dp = _aggregate_training_block(
        per_seed_timings={int(s): v for s, v in matched["training_seconds_per_seed"].items()},
        source_record=mp.MATCHED_CONTROL_RECORD,
        protocol="protocol-matched non-DP comparator",
        # FROM `per_seed[i]` — the shape the seconds describe.
        shape={
            "arm": sorted({p["arm"] for p in matched["per_seed"]}),
            "capacity_n_facts": ms["n_facts"],
            "grad_accum_steps": ms["grad_accum_steps"],
            "replay_micro_batches_per_step": ms["replay_micro_batches_per_step"],
            "max_steps": ms["max_steps"],
            "batch_size": ms["batch_size"],
            "block_size": ms["block_size"],
            "dp_seam_active": ms["dp_seam_active"],
        },
        # FROM THE TOP LEVEL — the venue.
        extra={
            "device": matched["device"],
            "torch_version": matched["torch_version"],
            "python_version": matched["python_version"],
            "git_sha": matched["git_sha"],
            "key_sources": (
                "per_seed[i]: arm, capacity_n_facts (n_facts), grad_accum_steps, "
                "replay_micro_batches_per_step, max_steps, batch_size, block_size, "
                "dp_seam_active. TOP LEVEL: device, torch_version, python_version, git_sha, "
                "n_seeds, training_seconds_per_seed. COMPUTED: seconds_total (SUM), "
                "timed_iterations (SUM), seconds_per_optimizer_step (their quotient), "
                "warmup_iterations_discarded (0), seed (LIST) — the aggregate convention copied "
                "from results/phase23_never_taught_training.json."
            ),
        },
    )

    # ===== training.non_dp_superseded_protocol — the OLD control, RECORDED BESIDE, never deleted ==
    # THINNER STILL, AND THE GAP IS A FINDING RATHER THAN A DEFAULT. Three keys are absent as KEYS
    # while the record STATES their values in its own `residual_differences` prose — and reading a
    # value out of a record's own prose is SOURCING, while writing the same value with no citation
    # is INVENTING. The citation is the difference, so it travels in the record.
    residual = old["residual_differences"]
    old_budget = old["recipe"]["budget_constants"]
    superseded = _aggregate_training_block(
        per_seed_timings={int(p["seed"]): p["training_seconds"] for p in old["per_seed"]},
        source_record=CONTROL_FLOOR_RECORD,
        protocol="old unmitigated control (superseded as a comparator)",
        shape={
            "arm": sorted({p["arm"] for p in old["per_seed"]}),
            "capacity_n_facts": old["per_seed"][0]["n_facts"],
            "grad_accum_steps": 1,
            "replay_micro_batches_per_step": 0,
            "max_steps": old_budget["teach_persona.MAX_STEPS"],
            "batch_size": old_budget["teach_persona.BATCH_SIZE"],
            "block_size": old_budget["teach_persona.BLOCK_SIZE"],
            "dp_seam_active": False,
        },
        extra={
            "device": old["device"],
            "torch_version": old["torch_version"],
            "python_version": old["python_version"],
            "git_sha": old["git_sha"],
            "key_sources": (
                "per_seed[i]: arm, capacity_n_facts (n_facts), training_seconds. "
                "recipe.budget_constants: max_steps, batch_size, block_size. TOP LEVEL: device, "
                "torch_version, python_version, git_sha, n_seeds. THE RECORD'S OWN PROSE, cited "
                "by index: grad_accum_steps = 1 from residual_differences[1].difference "
                '("grad_accum_steps is 1 here and `n_facts` on the DP path"); '
                "replay_micro_batches_per_step = 0 from residual_differences[0].difference "
                '("replay lives IN the teaching bin here; it is drawn at TRAIN time on the DP '
                'path" — this protocol has no separate replay pass, so the per-optimizer-step '
                "count is zero); dp_seam_active = False from "
                'residual_differences[3].why_not_eliminable ("`DPSGD` is constructed only when '
                '`is_dp`", and this arm is the non-DP control). COMPUTED: seconds_total (SUM), '
                "timed_iterations (SUM), seconds_per_optimizer_step, "
                "warmup_iterations_discarded (0), seed (LIST)."
            ),
            "prose_sourced_keys": {
                "grad_accum_steps": {
                    "value": 1,
                    "residual_differences_index": 1,
                    "quote": residual[1]["difference"],
                },
                "replay_micro_batches_per_step": {
                    "value": 0,
                    "residual_differences_index": 0,
                    "quote": residual[0]["difference"],
                },
                "dp_seam_active": {
                    "value": False,
                    "residual_differences_index": 3,
                    "quote": residual[3]["why_not_eliminable"],
                },
            },
        },
    )

    # THE ONE NUMERIC CLAIM OF THE PROVENANCE ARGUMENT, CARRIED BY A NAMED FIELD AND COMPUTED AT
    # WRITE TIME. It previously existed only inside a prose paragraph, where it is not a scalar
    # leaf, cannot be quoted by path and cannot be re-derived by any test.
    non_dp["wall_clock_gap_vs_superseded"] = (
        non_dp["training_seconds_mean"] / superseded["training_seconds_mean"]
    )
    non_dp["wall_clock_gap_vs_superseded_rule"] = (
        "training.non_dp.training_seconds_mean / "
        "training.non_dp_superseded_protocol.training_seconds_mean"
    )
    non_dp["provenance_argument"] = (
        "training.non_dp COMES FROM results/phase23_matched_control.json. Three non-DP figures "
        "exist and they disagree materially: 23-RESEARCH.md:637-641's 20.4 s (research's own "
        "rounding of an accum=1 LOOP-ONLY PROJECTION that was never a real run, quoted here as "
        "the thing being characterised and never as a figure), the old control's mean, and the "
        "protocol-matched comparator's mean. (1) IT IS A REFERENCE QUANTITY, BY USE: its only "
        "consumers in this phase are the `ratios` block and 23-12's retraction, both of which "
        "compare non-DP against DP, and a ratio is meaningless unless numerator and denominator "
        "describe the same experiment. (2) THE THREE MECHANISMS THAT INVALIDATED THE OLD CONTROL "
        "AS A COMPARATOR — teaching loss weight 1.0 vs 0.4342, 8.125x the lot volume, and a "
        "grad_clip that bound on the control and structurally never on the DP arm — ARE WALL-CLOCK "
        "MECHANISMS TOO, and the size of the effect is MEASURED rather than predicted: the field "
        "training.non_dp.wall_clock_gap_vs_superseded. Note what that measurement does NOT say: "
        "it is NOT 8.125, so it REFUTES the naive per-step-work equality rather than supporting "
        "it. The conclusion needs only the measured gap and survives without the equality — the "
        "two protocols do not time the same work, so they cannot share a ratio denominator. "
        "(3) THE CONSEQUENCE IS THE FINDING. Against the old control the DP/non-DP training "
        "multiple is training.dp_n8.seconds_total divided by "
        "training.non_dp_superseded_protocol.training_seconds_mean; against the matched comparator "
        "it is training.dp_n8.seconds_total divided by training.non_dp.training_seconds_mean. Both "
        "are computable from this record's own fields, so they are named that way and a reader "
        "divides. Publishing the first as if it were the DP seam's cost would attribute to 'the DP "
        "seam' a factor that is mostly the packer and lot difference the comparator equalises — "
        "precisely the error .planning/debug/sigma-zero-beats-control.md root-caused. "
        "SCOPE, STATED HONESTLY AND NOT OVERSTATED: deferred-items.md's CONTROL PROVENANCE rule "
        "governs the formal gate's three UTILITY fields (control_taught_recall, "
        "control_heldout_recall, control_gap) and requires them to come from the matched record. "
        "TIMING IS NOT ONE OF THOSE THREE. This decision is made and argued here on its own "
        "merits; it is not inherited from that rule."
    )
    non_dp["superseded_protocol_block"] = "training.non_dp_superseded_protocol"

    training = {
        "non_dp": non_dp,
        "non_dp_superseded_protocol": superseded,
        "dp_n8": _borrowed_training_block(
            block=sigma_zero_record["training"],
            source_record=SIGMA_ZERO_RECORD,
            protocol="dp_n8, seam active, sigma=0",
            extra={"sigma": sigma_zero_record["sigma"]},
        ),
        "dp_n64": _borrowed_training_block(
            block=noised["training"],
            source_record=noised["record"],
            protocol=noised["training"]["protocol"],
            extra={"sigma": noised["sigma"], "epsilon": noised["epsilon"]},
        ),
    }

    # ===== THE RATIOS — eval hours over PER-POINT training hours, all four, re-derivable =====
    # The per-point training cost is `seconds_total` for the two SINGLE runs and
    # `training_seconds_mean` for the two five-seed AGGREGATES (whose `seconds_total` is five
    # points' worth by the committed aggregate convention). The field each one came from travels
    # beside it, so the choice is visible in the data rather than argued in prose.
    per_point_source = {
        "non_dp": "training_seconds_mean",
        "non_dp_superseded_protocol": "training_seconds_mean",
        "dp_n8": "seconds_total",
        "dp_n64": "seconds_total",
    }
    ratios = {}
    for name, block in training.items():
        field = per_point_source[name]
        seconds = block[field]
        ratios[name] = {
            "training_seconds_per_point": seconds,
            "training_seconds_per_point_source": f"training.{name}.{field}",
            "protocol": block["protocol"],
            # NEVER the pinned `H_PER_POINT_FLOOR_SECONDS` — that pin is the floor-side REFERENCE,
            # not a measurement. The MEASURED ceiling exceeds the pin, so every ceiling-derived
            # ratio comes out SMALLER than a pin-derived one; that is expected, not a defect.
            "eval_over_training_ceiling": generation["h_per_point_ceiling"] * 3600 / seconds,
            "eval_over_training_floor": generation["h_per_point_floor"] * 3600 / seconds,
            "rule": (f"generation.h_per_point_{{ceiling,floor}} * 3600 / training.{name}.{field}"),
        }

    # ===== THE SIZING TABLE — at every K rung, and it PRICES THE NEVER-TAUGHT FLOOR =====
    # A sizing that prices 16 sweep points and forgets the N-seed control floor is short by N
    # points. N is READ from the never-taught record rather than assumed.
    n_never_taught_seeds = never_taught["n_seeds"]
    sizing = {}
    for k in mitigation_gate.K_RUNGS:
        projected = phase23_cost.size_sweep(
            generation_record=generation, sweep_points=_SWEEP_POINTS, k=k
        )
        projected["never_taught_seeds"] = n_never_taught_seeds
        projected["never_taught_floor_hours_ceiling"] = (
            n_never_taught_seeds * projected["h_per_point_ceiling_at_k"]
        )
        projected["never_taught_floor_hours_floor"] = (
            n_never_taught_seeds * projected["h_per_point_floor_at_k"]
        )
        projected["never_taught_seeds_source"] = f"{NEVER_TAUGHT_TRAINING_RECORD} -> n_seeds"
        projected["total_hours_ceiling_with_never_taught_floor"] = (
            projected["projected_hours"] + projected["never_taught_floor_hours_ceiling"]
        )
        sizing[str(k)] = projected

    record = {
        "record": COST_RECORD,
        "governs": (
            "CAL-01 and CAL-05's measured figures, and nothing else. It selects no K, sizes no Z "
            "and renders no verdict — 23-13 selects a rung from the `sizing` table below."
        ),
        "sigma": NOISED_SIGMA,
        # THE DECLARATION `tests/test_phase23_prereg.py::_prove_noised_record_is_under_the_glob`
        # REQUIRES OF ANY RECORD CARRYING A POSITIVE TOP-LEVEL σ. That rule leaves exactly two
        # doors and no third: a σ>0 record either lives under `NOISED_RECORD_GLOB` or declares
        # `sweep_point: false` and says why — and SILENCE is a refusal, not an exemption, because
        # `sweep_point` is not schema-required and omitting it would exempt a real sweep point
        # with no false statement at all. This record takes the second door HONESTLY: it carries
        # σ only to name WHICH sweep point's adapter the generation bracket was measured on, and
        # it fails none of the substantive legs by exporting an adapter or scoring a question —
        # it exports nothing, scores nothing, and trains nothing. The RUN that does all three is
        # `results/phase23_noised_dp_n64_sigma0p500000.json`, which is under the glob and declares
        # `sweep_point: true`.
        "sweep_point": False,
        "sweep_point_false_reason": (
            "This is the COST record (phase23_prereg.COST_RECORD), not a sweep point. It trains "
            "nothing, scores nothing and exports no adapter: it is arithmetic over committed "
            "records plus the `throughput` measurement. Its top-level `sigma` names WHICH sweep "
            "point's adapter the generation bracket was measured on; the sweep point itself is "
            "the record named in `sweep_point_record`, which IS under NOISED_RECORD_GLOB and "
            "declares `sweep_point: true`."
        ),
        "sweep_point_record": noised["record"],
        "sweep_points_priced": _SWEEP_POINTS,
        "sweep_points_source": ".planning/ROADMAP.md:47 / .planning/REQUIREMENTS.md:179",
        "k_rungs": list(mitigation_gate.K_RUNGS),
        "k_rungs_source": "mitigation_gate.K_RUNGS",
        "training": training,
        "generation": generation,
        "ratios": ratios,
        "sizing": sizing,
        "published_figure_paths": [
            "training.non_dp.training_seconds_mean",
            "training.non_dp_superseded_protocol.training_seconds_mean",
            "training.non_dp.wall_clock_gap_vs_superseded",
            "training.dp_n8.seconds_total",
            "training.dp_n64.seconds_total",
            "generation.h_per_point_floor",
            "generation.h_per_point_ceiling",
            "ratios.non_dp.eval_over_training_ceiling",
            "ratios.non_dp_superseded_protocol.eval_over_training_ceiling",
            "ratios.dp_n8.eval_over_training_ceiling",
            "ratios.dp_n64.eval_over_training_ceiling",
        ],
        "published_figure_rule": (
            "Every path above is a SCALAR LEAF written by json.dump from a COMPUTED float, at full "
            "stored precision. A rounding is not a figure this phase publishes."
        ),
        "projection_not_published": (
            "23-RESEARCH.md:637-641's 20.4 s non-DP figure is a LOOP-ONLY PROJECTION at accum=1, "
            "never a train_arm measurement, and 23-10 retracted the same projection method's "
            "lower-bound status after it over-stated the dp_n8 figure by at least 10.8%. It is "
            "characterised in training.non_dp.provenance_argument and appears in NO numeric field."
        ),
        **provenance(),
    }
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[phase23_run] wrote {COST_RECORD}")
    for name in sorted(training):
        print(
            f"[phase23_run]   training.{name}: protocol {training[name]['protocol']!r}, "
            f"eval/training ceiling {ratios[name]['eval_over_training_ceiling']!r}"
        )
    print(
        f"[phase23_run]   wall_clock_gap_vs_superseded = {non_dp['wall_clock_gap_vs_superseded']!r}"
    )


# =================================================================================================
# ===== (k) CTRL-03 — SCORING THE NEVER-TAUGHT ADAPTERS AT THE PINNED K (plan 23-14) ==============
# =================================================================================================
#
# WHAT THIS LEG IS. The five fresh adapters 23-08 trained at identical budget with ZERO persona
# facts are SCORED here, at the K 23-13 pinned, on the same Phase-18 attack corpus a sweep point
# will be scored on. Nothing is trained: `train_never_taught` is not reachable from this leg and
# `results/phase23_never_taught_training.json` is READ, never rewritten. That is what "scheduled
# once, consumed twice" means as a mechanism rather than as a sentence.
#
# ONE SEED PER PROCESS — THE RESUMABILITY MECHANISM, NOT A STYLE CHOICE. This driver's git surface
# is READ-ONLY (`ls-files`, `show`) and deliberately stays that way, so no in-process commit is
# available to bound a kill's cost. The bound is a PROCESS boundary instead: `never_taught()` scores
# exactly ONE not-yet-scored seed, records it, and EXITS, and the operator commits
# `data/phase23_run_state.json` between launches. A kill therefore costs at most one seed. 23-17's
# harness kill at 3 of 5 seeds is the measured precedent this shape exists for.
#
# FAMILY ZERO (`phase18_extraction.FAMILY_ZERO`) IS NOT RUN, AND THE REASON IS NOT COST. Its whole
# job is D-01's row-for-row equality against `results/phase14_recall_report.md`'s 112 TAUGHT rows —
# a harness-sanity control for an arm that WAS taught. A never-taught adapter has seen no fact, so
# that comparison is false by construction and would abort a scored run rather than check anything.
# It also carries no ASR ladder (D-09 spends 9 draws on it, not K), so it contributes nothing to the
# question-denominated counts the frozen gate consumes. The cost consequence is recorded rather than
# glossed: `results/phase23_cost.json`'s per-point figure PRICES family zero, so this run is priced
# BELOW the committed line item — the safe direction, and the projection block states both numbers.

# THE SEED STRIDE IS `phase18_extraction.K`, NOT `CURVE_K`, AND THAT IS DELIBERATE. `draw_all` seeds
# a FRESH generator per draw at `index + s`, so drawing `CURVE_K` samples from the stride the full-
# fidelity run uses makes this reading the BIT-IDENTICAL PREFIX of the K = 48 run — D-09's own
# argument for family zero's 9-draw prefix, applied one level up. Two consequences, both wanted:
# `promote_to_full_fidelity` (16 -> 48) genuinely EXTENDS this reading instead of redrawing it, and
# the 48-wide windows stay disjoint across questions, which a `CURVE_K`-wide stride would preserve
# but a narrower one would not.
NEVER_TAUGHT_SEED_STRIDE_SYMBOL = "phase18_extraction.K"

# THE POOLED COUNTS ARE ONE DESIGNATED SEED, NEVER A SUM ACROSS SEEDS — stated as a rule here, in
# the module, rather than chosen in the writer with five readings on screen.
NEVER_TAUGHT_POOLING_RULE = (
    "A SINGLE DESIGNATED SEED: the LADDER'S FIRST (`SEED_LADDER[0]`), pooled across the four "
    "dose-split attack families on the GATED tier. This is `phase23_prereg.sigma_zero_verdict`'s "
    "own `control_readings[0]` central-reading convention and `mitigation_budget."
    "CONTROL_NOISE_FLOOR_PROVENANCE`'s 'the pinned central reading', restated for this floor. "
    "SUMMING ACROSS SEEDS WAS REJECTED, and not on taste: the five seeds re-ask the SAME questions "
    "of five different adapters, so a pooled denominator would count correlated re-measurements as "
    "independent questions and narrow the Wilson bound on a precision the design does not have — "
    "`phase18_extraction.CLUSTER_DENOMINATOR_RATIONALE`'s error, one level up. The seed-to-seed "
    "variation is not discarded by that choice: it is exactly what `phase23_prereg.noise_floor` "
    "reduces, and it enters X as `MARGIN_K * extraction_noise_floor`, which is its proper role. "
    "Per-family and per-tier counts are recorded at full precision beside it, so a Phase-25 "
    "consumer that needs a different denominator takes it from the record rather than re-deriving "
    "one."
)


def _never_taught_training():
    """23-08's COMMITTED training record — read, never rewritten. This leg trains nothing."""
    path = _ROOT / NEVER_TAUGHT_TRAINING_RECORD
    _prove(
        path.exists(),
        f"{NEVER_TAUGHT_TRAINING_RECORD} is MISSING. This leg SCORES the adapters that record "
        "exported and schedules no training of its own — without it there is no seed list, no "
        "adapter path and no digest to score against",
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    _prove(
        record["arm"] == mitigation_gate.NEVER_TAUGHT_ARM,
        f"the training record names arm {record['arm']!r}, not "
        f"{mitigation_gate.NEVER_TAUGHT_ARM!r}. `extraction_ceiling` `_prove`s that exact string "
        "two phases from now and refuses one borrowing BY NAME",
    )
    return record


def _never_taught_adapter(training, seed):
    """ONE adapter path from the training record, PROVED present and matching its digest."""
    entries = [entry for entry in training["adapters"] if entry["seed"] == seed]
    _prove(
        len(entries) == 1,
        f"the training record holds {len(entries)} adapter entr(ies) for seed {seed}. The scored "
        "reading names ONE adapter and its digest; a missing or duplicated entry would score a "
        "different set of weights than the record claims",
    )
    path = _ROOT / entries[0]["path"]
    _prove(path.exists(), f"{entries[0]['path']} is recorded in the training record but GONE")
    digest = _sha256(path)
    _prove(
        digest == entries[0]["sha256"],
        f"{entries[0]['path']} hashes to {digest} but the training record recorded "
        f"{entries[0]['sha256']!r}. The adapter on disk is NOT the one 23-08's single scheduling "
        "exported, and a floor scored off it would cite a training record it did not come from",
    )
    return path


def _never_taught_draws_path(seed):
    """Where ONE seed's RAW draws are persisted, per shape, as they are produced.

    ``data/`` and therefore gitignored, exactly like ``phase23_run_state.json``'s neighbours: this
    is working state, not a published artifact, and every figure derived from it lands in the
    committed record. It exists because MEASURED: a ``TypeError`` in the block builder threw away
    2.3 hours of completed generation, and every step after the draw loop is cheap CPU work that
    should never be able to cost a GPU hour again.
    """
    return _ROOT / "data" / f"phase23_never_taught_seed{seed}_draws.json"


def _never_taught_load_draws(path, adapter_sha256, corpus_sha256, k):
    """Recorded draws for this seed, REFUSED unless they describe this exact measurement."""
    if not path.exists():
        return {
            "adapter_sha256": adapter_sha256,
            "corpus_sha256": corpus_sha256,
            "k": k,
            "shapes": {},
        }
    blob = json.loads(path.read_text(encoding="utf-8"))
    for field, expected in (
        ("adapter_sha256", adapter_sha256),
        ("corpus_sha256", corpus_sha256),
        ("k", k),
    ):
        _prove(
            blob.get(field) == expected,
            f"{path} records {field}={blob.get(field)!r} against this run's {expected!r}. Reusing "
            "it would pool draws taken off different weights, a different corpus or a different "
            "budget into one reading. Delete it in a reviewed step to re-draw",
        )
    print(
        f"[phase23_run] never-taught: {sorted(blob['shapes'])} already drawn for this seed — "
        f"reusing from {_rel(path)}",
        flush=True,
    )
    return blob


def _never_taught_write_draws(path, blob):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blob, sort_keys=True), encoding="utf-8")


def _never_taught_projection():
    """The scoring cost, PROJECTED and checked against the sizing table K was selected from.

    Recomputed here through ``results/phase23_cost.json``'s OWN ``h_per_point_composition`` — sum
    over the four attack shapes of ``prompts * K / that shape's measured rate`` — rather than read
    off the sizing block, so the two are an AGREEMENT rather than a restatement. Both throughput
    conditions are carried, named by the mechanism that produces them (``STOP_IDS`` active against
    the stop set emptied) rather than by a bracket word, because the record may hold no numeric leaf
    under a ``ceiling``/``bound`` key: Phase 23 does not publish X, and the guard that enforces that
    walks KEYS.
    """
    import phase18_extraction as x18  # LAZY — heavy, torch-touching (module docstring's rule).

    cost = json.loads((_ROOT / COST_RECORD).read_text(encoding="utf-8"))
    generation = cost["generation"]
    sizing = cost["sizing"][str(mitigation_budget.CURVE_K)]
    corpus = json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8"))
    per_shape = {shape["shape"]: shape for shape in generation["per_shape"]}
    prompts = {
        family: sum(1 for entry in corpus["prompts"] if entry["family"] == family)
        for family in x18.ATTACK_FAMILIES
    }
    k, n_seeds = mitigation_budget.CURVE_K, mitigation_budget.N_CONTROL_SEEDS

    projection = {
        "rule": (
            "N_CONTROL_SEEDS x (sum over the four attack shapes of prompts * CURVE_K / that "
            "shape's measured draws_per_min) — results/phase23_cost.json's own "
            "generation.h_per_point_composition, reproduced so this projection and the sizing "
            "table K was selected from are comparable rather than the same number twice"
        ),
        "curve_k": k,
        "curve_k_source": "mitigation_budget.CURVE_K",
        "n_seeds": n_seeds,
        "n_seeds_source": "mitigation_budget.N_CONTROL_SEEDS",
        "prompts_per_shape": prompts,
        "attack_prompts": sum(prompts.values()),
        "draws_per_seed": sum(prompts.values()) * k,
        "draws_all_seeds": sum(prompts.values()) * k * n_seeds,
        "condition_names_in_the_cost_record": {
            "stop_ids_active": "generation.per_shape[].draws_per_min_floor, sized in "
            f"sizing[{str(k)!r}].h_per_point_floor_at_k",
            "stop_ids_emptied": "generation.per_shape[].draws_per_min_ceiling, sized in "
            f"sizing[{str(k)!r}].h_per_point_ceiling_at_k",
        },
        "family_zero_priced_but_not_run": True,
        "family_zero_draws_priced": (
            generation["family_zero_prompts"] * generation["family_zero_draws_per_prompt"]
        ),
        "family_zero_reason": (
            "phase18_extraction.FAMILY_ZERO is D-01's row-for-row control against the 112 TAUGHT "
            "rows of results/phase14_recall_report.md. A never-taught adapter has seen no fact, so "
            "that equality is false BY CONSTRUCTION; it also carries no ASR ladder (D-09 spends 9 "
            "draws, not K) and contributes nothing to the question-denominated counts the frozen "
            "gate consumes. The sizing block PRICES it, so this run costs LESS than the committed "
            "line item rather than more"
        ),
    }
    for condition, rate_key, sizing_key in (
        ("stop_ids_active", "draws_per_min_floor", "h_per_point_floor_at_k"),
        ("stop_ids_emptied", "draws_per_min_ceiling", "h_per_point_ceiling_at_k"),
    ):
        minutes = sum(prompts[shape] * k / per_shape[shape][rate_key] for shape in prompts)
        slowest = min(per_shape[shape][rate_key] for shape in prompts)
        family_zero_minutes = projection["family_zero_draws_priced"] / slowest
        projection[f"hours_per_seed_{condition}"] = minutes / 60
        projection[f"hours_total_{condition}"] = n_seeds * minutes / 60
        projection[f"hours_per_seed_{condition}_priced_with_family_zero"] = (
            minutes + family_zero_minutes
        ) / 60
        projection[f"sizing_hours_per_seed_{condition}"] = sizing[sizing_key]
        projection[f"sizing_hours_total_{condition}"] = sizing[sizing_key] * n_seeds
        recomputed = (minutes + family_zero_minutes) / 60
        projection[f"relative_delta_vs_sizing_{condition}"] = (
            recomputed - sizing[sizing_key]
        ) / sizing[sizing_key]
        _prove(
            abs(projection[f"relative_delta_vs_sizing_{condition}"]) < 0.05,
            f"the {condition} projection recomputed here is {recomputed!r} h/point against the "
            f"committed sizing block's {sizing[sizing_key]!r}, a relative delta of "
            f"{projection[f'relative_delta_vs_sizing_{condition}']!r}. The sizing table is what "
            "23-13's K selection was made from, so a material disagreement means one of the two is "
            "wrong and no GPU second should be spent until it is resolved",
        )
        print(
            f"[phase23_run] never-taught projection [{condition}]: "
            f"{projection[f'hours_per_seed_{condition}']!r} h/seed x {n_seeds} = "
            f"{projection[f'hours_total_{condition}']!r} h "
            f"(sizing: {sizing[sizing_key]!r} h/seed, delta "
            f"{projection[f'relative_delta_vs_sizing_{condition}']:+.4%})"
        )
    return projection


def score_never_taught(seed, *, adapter, training):
    """The four Phase-18 ATTACK families against ONE never-taught adapter at the pinned K.

    **THE SUCCESS PREDICATE IS IMPORTED AND NEVER RE-IMPLEMENTED.** ``phase18_extraction`` is
    ancestry-guarded and permanently uneditable, so the attack this arm is scored BY cannot silently
    diverge from the attack a sweep point is scored by. Both the per-draw predicate
    (``score_records`` -> ``phase14_recall.contains_value``) and the QUESTION-unit rollup
    (``aggregate_questions``) are called out of it; a second copy of either is a second rule,
    free to stop agreeing with the one every published Phase-18 rate came out of.

    **THE UNIT IS QUESTIONS AND THE ERROR IS INVISIBLE WHEN IT IS NOT.**
    ``mitigation_gate.extraction_ceiling`` refuses a non-question denominator, and a
    draw-denominated count DEFLATES the rate and NARROWS the bound together — so nothing in the
    output would look wrong. The identities are therefore asserted rather than commented:
    ``sum(n_questions) == len(the cell)`` per cell, and ``total_draws == questions * CURVE_K``.

    ``load_adapted_model`` is the same ``weights_only=True`` load-before-inject path a scored sweep
    point uses, so a never-taught number and a sweep-point number come off ONE pipeline.
    """
    import phase14_recall as recall  # LAZY — teach_persona's own register for this pair.
    import phase16_persistence as persistence  # LAZY — same rule.
    import phase18_extraction as x18  # LAZY — heavy, torch-touching.

    k = mitigation_budget.CURVE_K
    corpus = json.loads(x18.CORPUS_PATH.read_text(encoding="utf-8"))
    _prove(
        corpus["entry_keys"] == list(x18.CORPUS_ENTRY_KEYS),
        f"{x18.CORPUS_PATH.name} declares entry_keys {corpus['entry_keys']} against the pin's "
        f"{list(x18.CORPUS_ENTRY_KEYS)}. Every field below would be read against a schema nobody "
        "checked",
    )
    prompts = corpus["prompts"]
    _prove(
        sorted({entry["family"] for entry in prompts}) == sorted(x18.ATTACK_FAMILIES),
        f"the corpus spans families {sorted({e['family'] for e in prompts})}, not the "
        f"pre-registered {sorted(x18.ATTACK_FAMILIES)} — the floor would be reduced over a "
        "different attack surface than the sweep points it is the floor FOR",
    )
    corpus_digest = x18.corpus_sha256(corpus)

    # TWO `values` OBJECTS, TWO CONSUMERS, and they are deliberately not one. The clean-room guard
    # takes a LIST of value strings; the scorer takes a `{fact_id: value}` MAPPING and aborts on a
    # fact it was given no value for. `phase19_erasure.py:2814` builds the mapping exactly this way.
    clean_room_values = [fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]
    values = {fact.id: fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}

    adapter_digest = _sha256(adapter)
    cache = _never_taught_draws_path(seed)
    recorded = _never_taught_load_draws(cache, adapter_digest, corpus_digest, k)
    model = tok = forbid = None

    draws, per_shape = [], []
    for family in x18.ATTACK_FAMILIES:
        cell = [entry for entry in prompts if entry["family"] == family]
        if family in recorded["shapes"]:
            shape = recorded["shapes"][family]
            draws.extend(shape["draws"])
            per_shape.append(shape["timing"])
            print(
                f"[phase23_run] never-taught seed {seed} {family}: REUSING "
                f"{len(shape['draws'])} recorded prompt(s) from {_rel(cache)} — already drawn",
                flush=True,
            )
            continue
        if model is None:
            model, model_cfg, tok, forbid, _artifact = recall.load_adapted_model(device(), adapter)
            # `_artifact` is the loaded persona FILE and it carries the adapter TENSORS. It is
            # deliberately dropped rather than recorded: a tensor is not JSON-serializable, and the
            # weights this reading came off are already pinned by `adapter_sha256`. MEASURED the
            # hard way — an earlier revision echoed it into the block and `json.dumps` raised
            # `TypeError: Object of type Tensor is not JSON serializable` at `_state_write`, AFTER
            # 2.3 h of drawing. That is also why the draws are now persisted per SHAPE below.
            _, seam_digest = persistence.resolve_forbid(tok, model_cfg.vocab_size)
            _prove(
                persistence.forbid_digest(forbid) == seam_digest,
                "the mask the loader threaded into this arm does not match `resolve_forbid`'s. "
                "The floor would be measured under a different forbid set than the arms it bounds",
            )
            tp.seed_everything(recall.SEED)
        box = {}
        with synchronized_seconds(box):
            for index, entry in enumerate(cell):
                # PERS-06 — nothing draws unchecked, on the ids ACTUALLY dispatched. `run_arm`'s
                # guard, reproduced because a run that trusts an artifact it did not check rests its
                # clean-room claim on a file's provenance instead of on its bytes.
                base_ids = x18._guarded_span(entry)
                recall.assert_no_value_in_prompt(
                    tok, tok.decode(base_ids), clean_room_values, prompt_ids=base_ids
                )
                is_a2 = entry["family"] == "A2"
                realized = entry["realized_injection"]
                prefix_text = tok.decode(entry["prompt_ids"][-realized:]) if is_a2 else None
                completions, stopped = recall.draw_all(
                    model,
                    tok,
                    entry["prompt_ids"],
                    device(),
                    forbid,
                    entry["seed_index"] * x18.K,  # the PIN's stride — see the module-level note
                    n_samples=k - 1,
                )
                _prove(
                    len(completions) == k,
                    f"question {entry['fact_id']!r}/{entry['seed_index']} in shape {family!r} drew "
                    f"{len(completions)} completions against the pinned CURVE_K = {k}. Every rate "
                    "below is over that budget, and a short draw set would publish it over fewer",
                )
                draws.append(
                    {
                        "family": entry["family"],
                        "dose": entry["dose"],
                        "fact_id": entry["fact_id"],
                        "slot": entry["slot"],
                        "tier": entry["tier"],
                        # The adapter-on/adapter-off AXIS of `phase18_extraction`'s schema, which is
                        # what `arm` means there. This adapter is loaded and ENABLED, so the axis
                        # value is literally true; the TRAINING arm is `never-taught` and is
                        # recorded under `arm` in the block below, where it is not this axis.
                        "arm": x18.ARMS[0],
                        "seed_index": entry["seed_index"],
                        "prefix_text": prefix_text,
                        "completions": completions,
                        "stopped": stopped,
                    }
                )
                if (index + 1) % 24 == 0 or index + 1 == len(cell):
                    done = index + 1
                    print(
                        f"[phase23_run] never-taught seed {seed} {family}: "
                        f"{done}/{len(cell)} prompts, {done * k} draws",
                        flush=True,
                    )
        minutes = box["seconds"] / 60
        _prove(minutes > 0, f"shape {family!r} timed a zero-width bracket")
        per_shape.append(
            {
                "shape": family,
                "prompts": len(cell),
                "n_draws": len(cell) * k,
                "minutes": minutes,
                "rate_draws_per_min": len(cell) * k / minutes,
                "stop_terminated_n": sum(
                    sum(1 for flag in record["stopped"] if flag)
                    for record in draws
                    if record["family"] == family
                ),
            }
        )
        # PERSIST THE RAW DRAWS BEFORE ANYTHING ELSE CAN FAIL. Everything downstream — scoring,
        # aggregation, serialization — is cheap CPU work, and a defect anywhere in it used to cost
        # the whole seed's GPU time. Written per SHAPE, so a kill now costs at most ~30 minutes
        # rather than ~2.3 hours, and a re-launch skips what is already drawn.
        recorded["shapes"][family] = {
            "draws": [record for record in draws if record["family"] == family],
            "timing": per_shape[-1],
        }
        _never_taught_write_draws(cache, recorded)
        print(
            f"[phase23_run] never-taught seed {seed} {family}: DONE — "
            f"{per_shape[-1]['rate_draws_per_min']:.2f} draws/min over {minutes:.2f} min "
            f"(persisted to {_rel(cache)})",
            flush=True,
        )
    del model

    # The recorded draws carry `stopped`, which is NOT a `DRAW_RECORD_KEYS` member; `score_records`
    # requires the schema as a SUBSET and ignores the extra, exactly as `run_arm`'s records do.
    scored = x18.score_records(draws, values)

    per_cell = []
    for family in x18.ATTACK_FAMILIES:
        for tier in x18.CORPUS_TIERS:
            cell = [r for r in scored if r["family"] == family and r["tier"] == tier]
            rows = x18.aggregate_questions(cell, tier=tier)
            # `aggregate_by_fact` keys by fact and does not carry the slot through, so the slot is
            # recovered from the cell — and PROVED single per fact, `phase19_erasure.py:540`'s
            # register: a fact appearing under two slots would attribute one fact's rate to another.
            slot_of = {}
            for record in cell:
                _prove(
                    slot_of.setdefault(record["fact_id"], record["slot"]) == record["slot"],
                    f"fact {record['fact_id']!r} appears under two slots in {family!r}/{tier!r}",
                )
            successes = sum(row["n_answerable"] for row in rows.values())
            questions = sum(row["n_questions"] for row in rows.values())
            # THE UNIT ASSERTION. One scored record per question, so the aggregation's question
            # count must equal the cell's record count. A draw-denominated count would be k times
            # too large and cannot survive this comparison — `phase19_erasure.py:555`'s register.
            _prove(
                questions == len(cell),
                f"cell {family!r}/{tier!r} aggregated {questions} questions over {len(cell)} "
                "scored records. There is ONE record per question, so a disagreement means the "
                "unit moved "
                "between the record and the rate — and a draw denominator deflates the rate AND "
                "narrows the bound in the same direction, so nothing downstream would look wrong",
            )
            for fact_id, row in rows.items():
                _prove(
                    row["n_draws"] == k * row["n_questions"],
                    f"fact {fact_id!r} in {family!r}/{tier!r} carries {row['n_draws']} draws "
                    f"against {k} x {row['n_questions']} questions — this cell was not drawn "
                    "at the pinned budget its own record claims",
                )
            per_cell.append(
                {
                    "family": family,
                    "tier": tier,
                    "nontarget_successes": successes,
                    "nontarget_questions": questions,
                    "rate": successes / questions,
                    "n_draws": sum(row["n_draws"] for row in rows.values()),
                    "per_fact": {
                        fact_id: {
                            "slot": slot_of[fact_id],
                            "n_answerable": row["n_answerable"],
                            "n_questions": row["n_questions"],
                            "rate": row["rate"],
                            "draw_rate": row["draw_rate"],
                            "n_draws": row["n_draws"],
                        }
                        for fact_id, row in sorted(rows.items())
                    },
                }
            )

    gated = [cell for cell in per_cell if cell["tier"] == x18.GATED_TIER]
    nontarget_successes = sum(cell["nontarget_successes"] for cell in gated)
    nontarget_questions = sum(cell["nontarget_questions"] for cell in gated)
    total_draws = sum(cell["n_draws"] for cell in gated)
    _prove(
        0 <= nontarget_successes <= nontarget_questions,
        f"{nontarget_successes} successes over {nontarget_questions} QUESTIONS is not a "
        "proportion. `extraction_ceiling` raises on exactly this: the unit is questions, never "
        "draws",
    )
    _prove(
        nontarget_questions == len([r for r in scored if r["tier"] == x18.GATED_TIER]),
        f"the gated denominator is {nontarget_questions} against "
        f"{len([r for r in scored if r['tier'] == x18.GATED_TIER])} scored records on that tier",
    )
    _prove(
        total_draws == nontarget_questions * k,
        f"total_draws {total_draws} != nontarget_questions {nontarget_questions} x "
        f"draws_per_question {k}. The two denominators describe the same cell and must agree, or "
        "one of the two figures is in the other's unit",
    )

    block = {
        "seed": seed,
        "arm": training["arm"],
        "draw_axis_arm": x18.ARMS[0],
        "adapter": _rel(adapter),
        "adapter_sha256": adapter_digest,
        "gated_tier": x18.GATED_TIER,
        "reported_tier": x18.REPORTED_TIER,
        "draws_per_question": k,
        "draws_per_question_source": "mitigation_budget.CURVE_K",
        "seed_stride_symbol": NEVER_TAUGHT_SEED_STRIDE_SYMBOL,
        "seed_stride": x18.K,
        "nontarget_successes": nontarget_successes,
        "nontarget_questions": nontarget_questions,
        "rate": nontarget_successes / nontarget_questions,
        "total_draws": total_draws,
        "draws_dispatched": len(draws) * k,
        "per_cell": per_cell,
        "per_shape": per_shape,
        "seconds": sum(shape["minutes"] for shape in per_shape) * 60,
        "corpus": _rel(x18.CORPUS_PATH),
        "corpus_sha256": corpus_digest,
        "success_predicate": "phase18_extraction.score_records -> phase14_recall.contains_value",
        "question_rollup": "phase18_extraction.aggregate_questions",
        "families": list(x18.ATTACK_FAMILIES),
        "family_zero_run": False,
        **provenance(),
    }
    # THE SERIALIZATION IS PROVED HERE, where the failure is free. `_state_record` writes the whole
    # ledger, so a non-serializable leaf in this block aborts AFTER the generation is spent —
    # MEASURED, on a `torch.Tensor` echoed in from `load_adapted_model`'s artifact.
    try:
        json.dumps(block, sort_keys=True)
    except TypeError as bad_leaf:  # pragma: no cover — the guard, not the path
        _prove(False, f"the scored block is not JSON-serializable: {bad_leaf}")
    print(
        f"[phase23_run] never-taught seed {seed}: {nontarget_successes}/{nontarget_questions} "
        f"{x18.GATED_TIER} QUESTIONS extracted at least once = {block['rate']!r} "
        f"({total_draws} draws at {k}/question)",
        flush=True,
    )
    return block


def _never_taught_evidence(seed, block):
    """RE-SCORE one seed from its RETAINED RAW DRAWS, and prove the recorded counts re-derive.

    Two things at once, and the second is why this exists rather than a field copied at scoring
    time. It emits the RAW PER-ITEM LOG — one row per QUESTION, the unit every figure here is in,
    carrying how many of its own draws contained the value — so the published count is
    recomputable from the committed record alone rather than only from a gitignored ledger. And it
    RE-DERIVES the recorded counts through the same imported predicate, on a different day, in a
    different process, from the bytes the generation actually produced. A disagreement means the
    block and its own evidence describe different runs, and the write aborts.

    The raw completion TEXT itself stays in ``data/`` — it is ~1 MB of model output per seed, not a
    measurement — with its digest pinned into the record so the retained file is identifiable.
    """
    import phase18_extraction as x18  # LAZY — heavy, torch-touching.

    cache = _never_taught_draws_path(seed)
    _prove(
        cache.exists(),
        f"{cache} is GONE. It is the raw evidence behind seed {seed}'s published count, and the "
        "record is not written over readings whose draws cannot be re-scored",
    )
    blob = json.loads(cache.read_text(encoding="utf-8"))
    _prove(
        blob["adapter_sha256"] == block["adapter_sha256"]
        and blob["k"] == block["draws_per_question"],
        f"the retained draws for seed {seed} describe adapter {blob['adapter_sha256']!r} at k="
        f"{blob['k']!r} against the recorded {block['adapter_sha256']!r} at "
        f"{block['draws_per_question']!r}",
    )
    values = {fact.id: fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS}
    draws = [record for shape in x18.ATTACK_FAMILIES for record in blob["shapes"][shape]["draws"]]
    scored = x18.score_records(draws, values)

    gated = [record for record in scored if record["tier"] == block["gated_tier"]]
    successes = sum(1 for record in gated if any(record["hits"]))
    _prove(
        (successes, len(gated)) == (block["nontarget_successes"], block["nontarget_questions"]),
        f"seed {seed} re-scores to {successes}/{len(gated)} from its retained draws but the "
        f"recorded reading is {block['nontarget_successes']}/{block['nontarget_questions']}. The "
        "published count and the evidence behind it describe different runs",
    )
    return {
        "seed": seed,
        "raw_draws_retained_at": _rel(cache),
        "raw_draws_sha256": _sha256(cache),
        "raw_draws_not_committed": (
            "the ~1 MB of raw generated TEXT per seed lives in gitignored `data/` and is not a "
            "committed artifact; its digest is pinned here so the retained file is identifiable. "
            "Every MEASUREMENT taken off it IS committed — the rows below are one per question, "
            "and `per_seed[].per_cell[].per_fact` carries the counts with their denominators"
        ),
        "re_derived_successes": successes,
        "re_derived_questions": len(gated),
        "per_question": [
            {
                "family": record["family"],
                "tier": record["tier"],
                "fact_id": record["fact_id"],
                "slot": record["slot"],
                "seed_index": record["seed_index"],
                "hits": sum(record["hits"]),
                "n_draws": record["n_draws"],
            }
            for record in scored
        ],
    }


def _never_taught_record(training, seeds):
    """Assemble and write ``results/phase23_never_taught.json`` once every seed is scored.

    Pure arithmetic plus a CPU re-score over the working state and the retained draws — no GPU
    second is spent here, which is why an assembly bug costs nothing. The reduction is CALLED: no
    spread is typed in this file.
    """
    state = _state_load()["never_taught"]
    per_seed = [state[str(seed)]["scoring"] for seed in seeds]
    evidence = [_never_taught_evidence(seed, block) for seed, block in zip(seeds, per_seed)]
    readings = [block["rate"] for block in per_seed]
    # THE REDUCTION IS CALLED, NEVER INLINED — the same blind-committed function that reduced the
    # control floor and the matched floor. No `max`, no `min`, no spread is typed here.
    measured_floor = noise_floor(readings)

    for key in ("gated_tier", "draws_per_question", "device", "torch_version", "arm"):
        distinct = sorted({str(block[key]) for block in per_seed})
        _prove(
            len(distinct) == 1,
            f"the per-seed blocks disagree on {key!r}: {distinct}. Five readings taken on "
            "different instruments are not five readings of one quantity",
        )
    designated = per_seed[0]
    _prove(
        designated["seed"] == seeds[0] == SEED_LADDER[0],
        f"the designated central reading is seed {designated['seed']!r} against the ladder's first "
        f"{SEED_LADDER[0]!r}. The pooling rule names the ladder's FIRST seed, and a different one "
        "would be a designation made with five readings visible",
    )

    inputs_sha256 = hashlib.sha256(
        json.dumps(per_seed, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    governs = (
        "the NEVER-TAUGHT EXTRACTION RATE over "
        f"{designated['gated_tier']} QUESTIONS (per_seed[].nontarget_successes / "
        ".nontarget_questions, a count over QUESTIONS and never draws), measured on the four "
        "dose-split Phase-18 attack families at mitigation_budget.CURVE_K draws per question. "
        "mitigation_gate.extraction_ceiling reads this floor in Phase 25 as the "
        "`extraction_noise_floor` term of X. It governs THAT quantity and nothing else: the "
        f"{designated['reported_tier']} tier and every per-family cell recorded here are "
        "secondary, carry their own denominators and were NOT reduced. PHASE 23 DOES NOT PUBLISH "
        "X — this record carries no bound and no ceiling value; Phase 25 computes it."
    )
    provenance_block = {
        "arm": mitigation_gate.NEVER_TAUGHT_ARM,
        "seeds": list(seeds),
        "record": NEVER_TAUGHT_RECORD,
        "record_sha256": inputs_sha256,
        "git_sha": tp.git_sha(),
        "git_sha_per_seed": {str(b["seed"]): b["git_sha"] for b in per_seed},
        "device": designated["device"],
        "torch_version": designated["torch_version"],
        "reduction": "phase23_prereg.noise_floor",
        "k": designated["draws_per_question"],
        "questions": designated["nontarget_questions"],
        "governs": governs,
    }
    required_keys = tuple(FLOOR_PROVENANCE_KEYS) + tuple(
        mitigation_gate.EXTRACTION_FLOOR_PROVENANCE_KEYS
    )
    missing = [key for key in required_keys if key not in provenance_block]
    _prove(
        not missing,
        f"the extraction floor's provenance is MISSING {missing!r}. `extraction_ceiling`'s "
        "`_prove` calls are the ONE choke point at which a floor's provenance is checked, two "
        "phases from "
        "now, in a file with no correction path — a record missing a key is REFUSED, not defaulted",
    )

    record = {
        "record": NEVER_TAUGHT_RECORD,
        "record_sha256": inputs_sha256,
        "arm": mitigation_gate.NEVER_TAUGHT_ARM,
        "extraction_noise_floor": measured_floor,
        "extraction_floor_provenance": provenance_block,
        "reduction": "phase23_prereg.noise_floor",
        "estimator": (
            "the RANGE max(readings) - min(readings) over the N per-seed gated-tier extraction "
            "rates, committed BLIND in 23-03 and CALLED here — never re-implemented"
        ),
        "readings": readings,
        "governs": governs,
        "seeds": list(seeds),
        "n_seeds": len(seeds),
        "distinct_seeds": len(set(seeds)),
        "frozen_gate_min_seeds": mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS,
        "frozen_gate_provenance_keys": list(mitigation_gate.EXTRACTION_FLOOR_PROVENANCE_KEYS),
        "pooled": {
            "nontarget_successes": designated["nontarget_successes"],
            "nontarget_questions": designated["nontarget_questions"],
            "rate": designated["rate"],
            "total_draws": designated["total_draws"],
            "draws_per_question": designated["draws_per_question"],
            "seed": designated["seed"],
            "tier": designated["gated_tier"],
            "unit": "question",
            "pooling_rule": NEVER_TAUGHT_POOLING_RULE,
        },
        "per_seed": per_seed,
        "evidence": evidence,
        "evidence_rule": (
            "every per-seed reading above was RE-SCORED from its retained raw draws through the "
            "same imported `phase18_extraction.score_records`, in this process, and asserted equal "
            "to the recorded count before this file was written. `evidence[].per_question` is the "
            "raw per-item log at the QUESTION unit, so `pooled.nontarget_successes` is the number "
            "of gated rows with `hits > 0` and recomputes from this record alone"
        ),
        "source_training_record": NEVER_TAUGHT_TRAINING_RECORD,
        "source_training_record_sha256": _sha256(_ROOT / NEVER_TAUGHT_TRAINING_RECORD),
        "consumers": training["consumers"],
        "scheduled_once_consumed_twice": (
            "23-08 trained these adapters ONCE and scored none of them (`scored_here: false`); "
            "this record is the ONE scoring, and both consumers above read it. The claim is "
            "CHECKED rather than asserted: source_training_record and its digest cite the "
            "scheduling, consumers matches that record's list exactly, the seed lists are "
            "identical in both, and 23-08's `test_never_taught_is_trained_once` AST census proves "
            "exactly one `train_never_taught` definition and one call site exist under scripts/"
        ),
        "curve_k": mitigation_budget.CURVE_K,
        "budget_constants": {
            "mitigation_budget.CURVE_K": mitigation_budget.CURVE_K,
            "mitigation_budget.N_CONTROL_SEEDS": mitigation_budget.N_CONTROL_SEEDS,
            "mitigation_budget.FULL_FIDELITY_K": mitigation_budget.FULL_FIDELITY_K,
            "mitigation_budget.SWEEP_POINTS": mitigation_budget.SWEEP_POINTS,
        },
        "budget_constants_source": (
            "scripts/mitigation_budget.py (23-13's pin — READ, never written)"
        ),
        "projection": _never_taught_projection(),
        "scoring_seconds_per_seed": {str(b["seed"]): b["seconds"] for b in per_seed},
        "scoring_seconds_total": sum(b["seconds"] for b in per_seed),
        "x_is_not_published_here": (
            "mitigation_gate.extraction_ceiling is called from tests/test_phase23_ctrl.py ONLY, to "
            "prove this record's provenance passes the frozen gate's refusals. Its return value is "
            "not asserted on and appears in NO field of this record. D-13: the extraction floor "
            "arrives at that gate as a required kwarg and X is never a literal — Phase 25 computes "
            "it. The symbol is NAMED in provenance strings above and that is deliberate; storing a "
            "NUMBER under it is the publication this forbids, which is why the guard walks KEYS "
            "rather than matching text"
        ),
        **provenance(),
    }
    _prove(
        record["extraction_noise_floor"]
        == noise_floor([block["rate"] for block in record["per_seed"]]),
        "the recorded floor does not re-derive from the recorded readings — the record and its own "
        "reduction disagree before it has even been written",
    )
    path = _ROOT / NEVER_TAUGHT_RECORD
    _prove(
        not path.exists(),
        f"{path} already exists — it is recorded evidence and there is no force flag",
    )
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print("[phase23_run] per-seed gated-tier readings (QUESTIONS extracted at least once):")
    for block in per_seed:
        print(
            f"  seed {block['seed']}: {block['nontarget_successes']}/"
            f"{block['nontarget_questions']} = {block['rate']!r} over "
            f"{block['draws_per_question']} draws/question ({block['total_draws']} draws)"
        )
    print(
        f"[phase23_run] wrote {NEVER_TAUGHT_RECORD}: extraction_noise_floor {measured_floor!r} "
        f"= phase23_prereg.noise_floor over {len(readings)} readings"
    )


def never_taught():
    """23-14 / CTRL-03 — score ONE not-yet-scored never-taught seed at the pinned K, then EXIT.

    **THE PROCESS BOUNDARY IS THE COMMIT BOUNDARY.** This driver's git surface is READ-ONLY by
    design, so "commit after every seed" cannot be an in-process act. It is delivered instead by
    scoring exactly one unscored seed per invocation and exiting: the operator runs the detached
    launch once per seed and commits ``data/phase23_run_state.json`` between launches, so a kill
    costs at most ONE seed. Once every seed is scored, a final invocation spends no GPU second and
    assembles ``results/phase23_never_taught.json``.

    Trains nothing. The adapters come from 23-08's single scheduling, by path and by sha256.
    """
    _preconditions()
    prove_d04_gate()
    training = _never_taught_training()
    seeds = [int(seed) for seed in training["seeds"]]
    _prove(
        seeds == list(SEED_LADDER)[: len(seeds)],
        f"the training record's seeds {seeds} are not a prefix of the ladder {list(SEED_LADDER)}. "
        "`noise_floor`'s readings are recorded in ladder order and the central reading is the "
        "FIRST — a reordered list would designate a different seed",
    )
    _prove(
        len(set(seeds)) == mitigation_budget.N_CONTROL_SEEDS,
        f"the training record holds {len(set(seeds))} distinct seed(s) against the budget's pinned "
        f"N_CONTROL_SEEDS = {mitigation_budget.N_CONTROL_SEEDS}. The floor is scored at the same N "
        "the budget priced, or the sweep is short by the difference",
    )

    recorded = _state_load().get("never_taught", {})
    todo = [seed for seed in seeds if "scoring" not in recorded.get(str(seed), {})]
    print(
        f"[phase23_run] never-taught: {len(seeds) - len(todo)}/{len(seeds)} seed(s) scored; "
        f"remaining {todo}",
        flush=True,
    )
    if not todo:
        _never_taught_record(training, seeds)
        return

    _never_taught_projection()
    seed = todo[0]
    _prove(
        _already_trained("never_taught", seed),
        f"never-taught seed {seed} has no verified adapter in the working state. These adapters "
        "are 23-08's and this leg trains none — re-run `schedule` rather than scoring a seed whose "
        "weights nothing vouches for",
    )
    adapter = _never_taught_adapter(training, seed)
    print(f"[phase23_run] never-taught: scoring seed {seed} from {_rel(adapter)}", flush=True)
    block = score_never_taught(seed, adapter=adapter, training=training)
    _state_record("never_taught", seed, {"scoring": block})
    print(
        f"[phase23_run] never-taught: seed {seed} RECORDED into {STATE_PATH}. "
        f"COMMIT data/phase23_run_state.json NOW — {len(todo) - 1} seed(s) remain "
        f"({todo[1:]}), and the next launch is what scores the next one",
        flush=True,
    )


_TABLE = {
    "cost": cost,
    "schedule": schedule,
    "floor": floor,
    "sigma-zero": sigma_zero,
    "matched": matched,
    "matched-verdict": matched_verdict,
    "noised": noised,
    "throughput": throughput,
    "cost-record": cost_record,
    "never-taught": never_taught,
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
    "  matched     train AND score the PROTOCOL-MATCHED comparator at all five seeds, then\n"
    "              re-reduce the floor over ITS readings through `phase23_prereg.noise_floor`.\n"
    "              Writes results/phase23_matched_control.json. RUNS NO sigma=0 ARM and RENDERS\n"
    "              NO VERDICT — 23-18 re-pins the floor and 23-19 calls the rule. ONE ATTEMPT:\n"
    "              `phase23_matched_prereg.prove_first_attempt` plus a scored-seed refusal over\n"
    "              data/phase23_run_state.json, and there is no force flag on either.\n"
    "  matched-verdict\n"
    "              RE-RUN THE D-04 DECISION against the protocol-matched comparator. Pure\n"
    "              arithmetic over two COMMITTED records — trains nothing, scores nothing, and\n"
    "              does NOT re-run the sigma=0 arm: its reading is READ BACK from\n"
    "              results/phase23_sigma_zero.json. Calls `phase23_prereg.sigma_zero_verdict`\n"
    "              with the matched readings and `mitigation_budget.MATCHED_CONTROL_NOISE_FLOOR`.\n"
    "              Writes results/phase23_matched_verdict.json on BOTH outcomes. A second breach\n"
    "              HALTS again — no second comparator, no override flag. 23-11..23-14 stay\n"
    "              BLOCKED either way.\n"
    "  noised      CAL-01 — the FIRST noised sweep point of the milestone: dp_n64 at sigma > 0,\n"
    "              at the full production shape (MAX_STEPS unmonkeypatched), timed with both\n"
    "              synchronize boundaries. GATED ON TWO CONJUNCTS — results/\n"
    "              phase23_matched_verdict.json's verdict == proceed AND the COMMITTED human\n"
    "              unblock act (746ecf6, pinned by sha and by changed-path shape). Writes the\n"
    "              record at `phase23_prereg.noised_record_path('dp_n64', sigma)`. NEVER reads\n"
    "              results/phase23_sigma_zero.json's own verdict: it is HALT, permanently and by\n"
    "              design, and a gate pointed at it can never open.\n"
    "  throughput  CAL-05 — the per-point cost BRACKET, measured on the REAL noised adapter\n"
    "              across the four Phase-18 attack shapes under BOTH stop conditions (stop ids\n"
    "              active = FLOOR, stop set emptied = CEILING), plus the un-adapted base under\n"
    "              the floor condition, cross-validated per shape against\n"
    "              results/phase18_preflight_report.md. Writes the measurement into the\n"
    "              working state; never a bare mean. Same detached discipline as `noised`.\n"
    "  never-taught\n"
    "              CTRL-03 — score the never-taught adapters 23-08 trained, at the K 23-13 pinned\n"
    "              (`mitigation_budget.CURVE_K`), on the four Phase-18 ATTACK families. Trains\n"
    "              NOTHING: the adapters are consumed from\n"
    "              results/phase23_never_taught_training.json by path and sha256.\n"
    "              SCORES EXACTLY ONE NOT-YET-SCORED SEED AND EXITS. That is the resumability\n"
    "              mechanism, not a limitation: this driver's git surface is READ-ONLY, so the\n"
    "              per-seed commit boundary has to be a PROCESS boundary. Run the detached launch\n"
    "              ONCE PER SEED and COMMIT data/phase23_run_state.json between launches — a kill\n"
    "              then costs at most one seed (23-17 lost 3 of 5 to exactly this). A final\n"
    "              invocation, once every seed is scored, spends no GPU second and writes\n"
    "              results/phase23_never_taught.json with the floor reduced through\n"
    "              `phase23_prereg.noise_floor`. Family zero is NOT run: D-01's row-for-row\n"
    "              equality is against TAUGHT rows and is false by construction on this arm.\n"
    "  cost-record assemble results/phase23_cost.json — four training legs each NAMING its\n"
    "              protocol, the floor/ceiling generation bracket, all four eval/training ratios\n"
    "              and a K-rung sizing table that prices the never-taught floor. Pure arithmetic\n"
    "              over committed records plus the `throughput` measurement; trains and scores\n"
    "              nothing, so an assembly bug costs no GPU second.\n"
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
