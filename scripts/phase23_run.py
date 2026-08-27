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

THE THREE SUB-MODES, and why the split is not cosmetic::

    python scripts/phase23_run.py cost      # train + score control seed 1, cost the SCORING leg,
                                            #   apply the blind seed rule -> N          (23-08 T1)
    python scripts/phase23_run.py schedule  # ONE invocation: the remaining control arms AND every
                                            #   never-taught arm, at the same seed list (23-08 T2)
    python scripts/phase23_run.py floor     # score the remaining control arms, reduce the floor
                                            #   through `phase23_prereg.noise_floor`   (23-08 T3)

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

CPU-hostile: this driver trains and scores on the resolved device (MPS on the M3, D-01).
"""

import os

# Set BEFORE importing torch so the backend honors it for the whole process — `teach_persona`'s own
# register, restated here because this module's import block is sorted and `teach_persona` is last.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import contextlib  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from dataclasses import asdict  # noqa: E402

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_gate  # noqa: E402  READ-ONLY — FROZEN. Imported so `arm` is READ, never retyped.
import phase14_factset as fs  # noqa: E402
import phase23_cost  # noqa: E402
import teach_persona as tp  # noqa: E402
from phase23_prereg import (  # noqa: E402
    CONTROL_FLOOR_RECORD,
    FLOOR_PROVENANCE_KEYS,
    H_PER_POINT_FLOOR_SECONDS,
    NEVER_TAUGHT_TRAINING_RECORD,
    SIGMA_ZERO_RECORD,
    choose_n_seeds,
    noise_floor,
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
    clash = sorted(set(entry) & set(block))
    _prove(
        not clash,
        f"{STATE_PATH} already carries {section}[{str(key)!r}] keys {clash} — they are recorded "
        "measurements and there is no force flag. Delete the entry in a reviewed step to "
        "re-measure it rather than overwriting a reading in place",
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


def score_control(seed):
    """Score ONE control arm (adapter ON and OFF) and return every reading with its denominator."""
    import phase14_recall as pr  # LAZY — teach_persona's own register for this pair

    arm = control_arm(seed)
    adapter = tp.arm_outputs(arm, prefix=PREFIX)["adapter"]
    _prove(
        adapter.exists(),
        f"{adapter} is MISSING — control seed {seed} has not been trained. Run "
        "`python scripts/phase23_run.py cost` (seed 1) and `... schedule` (the rest) first",
    )
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


# =================================================================================================
# ===== (e) THE SUB-MODES =====
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


_TABLE = {
    "cost": cost,
    "schedule": schedule,
    "floor": floor,
}

USAGE = (
    f"usage: python scripts/phase23_run.py {{{'|'.join(_TABLE)}}}\n"
    "\n"
    "  cost      train + score control seed 1, cost the SCORING leg, apply the BLIND seed rule\n"
    "            `phase23_prereg.choose_n_seeds` -> N. Must run FIRST: N is a function of a\n"
    "            measured scoring cost and there is no default N anywhere.\n"
    "  schedule  ONE invocation — the remaining control arms AND every never-taught arm, at the\n"
    "            same seed list. Writes results/phase23_never_taught_training.json. Scores\n"
    "            nothing: the never-taught scoring budget is a function of 23-13's K.\n"
    "  floor     score the remaining control arms and reduce the floor through\n"
    "            `phase23_prereg.noise_floor`. Writes results/phase23_control_floor.json.\n"
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
