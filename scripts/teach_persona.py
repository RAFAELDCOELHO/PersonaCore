"""Teach one persona arm: build the masked teaching bins, then train the LoRA adapter.

This file has TWO halves. The BINS half (below) renders the taught template families over an
arm's facts, encodes every episode through ``encode_dialogue``, and writes the arm-scoped
``uint16``/``uint8`` bin pair that ``train()``'s only masked data path consumes. The TRAINING
half (the marked section at the bottom) loads the frozen conversational base, injects LoRA,
freezes everything else, trains on those masked bins, proves the base is bit-untouched, and
exports the adapter. The two halves copy two different analogs on purpose — the bins half
copies ``scripts/prepare_dialog_corpus.py``, the training half copies
``scripts/train_adapter_smoke.py`` — so their registers are kept apart rather than interleaved.

**Masking regime — Phase 14 REVERSES Phase 12's verdict, by design, not by drift.** Phase 12
measured stage-2 conversational LM tuning and chose UNMASKED training (loss on BOTH speakers),
which is legitimate for teaching the *model of a dialogue*. PITFALLS-14 is explicit that the two
regimes must not be conflated: personalization / QA teaching must cover ONLY the ANSWER tokens,
or the model learns to imitate QUESTIONS instead of answering them. The mask here therefore
covers exactly the answer span plus its terminating eos and nothing else. It comes from
``encode_dialogue``, which already builds the mask in TARGET space to match the v1.0 one-position
label shift — this script writes NO new masking implementation, and that is precisely what kills
the PITFALLS-14 off-by-one bug family before it can appear.

The teaching corpus is a single-turn QA episode per paraphrase with an EMPTY persona: the bare
``<|system|>`` clean-room shape (14-RESEARCH F2), so the fact can only come from the weights.

SECURITY: every file this half reads is the project's OWN trusted material —
``artifacts/tokenizer.json`` (the FROZEN git-tracked tokenizer),
``results/phase14_factset_report.md``
(committed evidence, read only to extract the recorded verdict), and, on the replay arm only,
``data/dialog_train.bin`` (this project's own encoded PersonaChat memmap). Nothing untrusted or
foreign is read, and no ``torch.load`` happens in this half at all. Fact values are invented, so
no real personal data enters ``data/`` (T-14-05); ``data/`` is gitignored regardless.
The TRAINING half adds exactly one deserialization: ``torch.load(CONVBASE_BEST,
weights_only=False)`` on this project's OWN resume checkpoint (T-14-04), which must stay
``weights_only=False`` because it carries pickled optimizer/RNG/numpy objects. Nothing it writes
inherits that posture — the SHAREABLE adapter goes out through ``export_adapter``, so every
consumer (harness, demo) reads it back under the ``weights_only=True`` ``load_adapter`` contract.

Every proof check below is an explicit ``raise SystemExit`` and never an ``-O``-strippable bare
check, so a failure exits non-zero even under ``PYTHONOPTIMIZE``.

Run: ``python scripts/teach_persona.py {cal_first_person|cal_first_person_replay|
cal_second_person|real}`` (inside the Python 3.11 venv, on the M3).
"""

import contextlib
import hashlib
import io
import json
import math
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time
from dataclasses import asdict

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np  # noqa: E402
import phase14_factset as fs  # noqa: E402  (sibling script; scripts/ is sys.path[0])
import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.checkpoint import export_adapter  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.dialogue import build_recall_prompt, encode_dialogue  # noqa: E402
from personacore.evaluation import masked_perplexity  # noqa: E402
from personacore.lora import (  # noqa: E402
    LoRAConfig,
    adapter_disabled,
    inject_lora,
    lora_state_dict,
    mark_only_lora_trainable,
    snapshot_params,
)
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
from personacore.training import train  # noqa: E402
from personacore.training.data import get_batch_memmap_masked  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted checkpoint
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
FACTSET_REPORT = _REPO_ROOT / "results" / "phase14_factset_report.md"  # carries the D-06 verdict
CALIBRATION_REPORT = _REPO_ROOT / "results" / "phase14_calibration_report.md"  # W-02, real arm only
DIALOG_TRAIN_BIN = _REPO_ROOT / "data" / "dialog_train.bin"  # replay source (read-only)
DIALOG_TRAIN_MASK = _REPO_ROOT / "data" / "dialog_train_mask.bin"
DIALOG_VAL_BIN = _REPO_ROOT / "data" / "dialog_val.bin"  # D-11.2 collateral metric (14-07)
DIALOG_VAL_MASK = _REPO_ROOT / "data" / "dialog_val_mask.bin"

SEED = 1337
BLOCK_SIZE = 256  # ModelConfig.block_size — the smoke-draw window and the corpus floor

# ===== S2: the Phase-14 mask-fraction band, DERIVED HERE, not inherited =====
#
# ``prepare_dialog_corpus.py`` pins a much narrower band for PersonaChat episodes, where a
# multi-turn dialogue splits roughly evenly between the two speakers. A Phase-14 teaching
# episode is ``<|system|><|user|>{question}<|assistant|>{answer}<eos>`` with mask=1 on the
# answer content plus the terminating eos ONLY. From the measured F5 ranges — 26-45 ids per
# episode, 11-24 answer-content ids — the realizable fraction spans (11+1)/45 = 0.267 (short
# answer, long question) to (24+1)/26 = 0.96 (long answer, minimal question). The PersonaChat
# ceiling sits INSIDE that legitimate range, so copying its literal would be a false failure
# waiting to happen on an answer-heavy QA corpus — which is what this corpus is by construction.
#
# This band's ONLY job is to catch the two mechanical mask bugs, and both are degenerate: a mask
# that is never set gives exactly 0.0, a mask applied to everything gives exactly 1.0. Every
# intermediate value is legitimate for this corpus shape. SPAN-LEVEL correctness — the actual
# Pitfall-14 off-by-one bug family — is pinned far more sharply by
# ``tests/test_phase14_teaching.py::test_answer_span_mask``'s hand-written literal fixture,
# which is where that guarantee belongs.
#
# Because a wide guard proves little on its own, the MEASURED fraction is not hidden behind it:
# the builder prints mean/min/max per arm and echoes the number into the run provenance, and
# plan 14-09 carries it into ``results/phase14_calibration_report.md``.
MASK_FRACTION_BAND = (0.15, 0.95)

# 14-RESEARCH Open Q5: ``train()`` takes exactly ONE ``train_bin``, so PersonaChat replay is a
# BUILD-TIME concatenation ratio rather than a loop change. That keeps ``train()`` untouched and
# makes the ratio an auditable committed number instead of a runtime flag.
REPLAY_RATIO = 0.0  # every arm except the replay arm
REPLAY_ARM_RATIO = 1.0  # D-15's with-replay arm: one replay token per teaching token

ARMS = ("cal_first_person", "cal_first_person_replay", "cal_second_person", "real")


def _require_go_verdict(report_path):
    """D-06 gate: hard-exit unless the report's ``## Verdict`` section reads GO or ADAPT."""
    if not report_path.exists():
        raise SystemExit(
            f"[teach_persona] {report_path} missing — run "
            "`python scripts/phase14_factset_gate.py` and record the D-06 verdict first."
        )
    text = report_path.read_text(encoding="utf-8")
    section = re.search(r"^## Verdict\b(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if section is None:
        raise SystemExit(
            "[teach_persona] no '## Verdict' section in the fact-set report — the D-06 verdict "
            "must be recorded before any teaching bin is built."
        )
    word = re.search(r"[A-Za-z]+", section.group(1))
    verdict = word.group(0).upper() if word else "PENDING"
    if verdict not in ("GO", "ADAPT"):
        raise SystemExit(
            f"[teach_persona] recorded verdict is {verdict!r} — teaching bins may only be built "
            "on GO/ADAPT (D-06). STOP/PENDING must be escalated, not bypassed."
        )
    return verdict


def arm_outputs(arm):
    """Name-scoped write targets for one arm — no two arms ever share a path.

    ONE deliberate exception to the ``phase14_{arm}`` naming: the ``real`` arm's adapter is
    ``checkpoints/persona_adapter.pt``, not ``phase14_real_adapter.pt``. That is the SHIPPABLE
    persona file, and both downstream consumers already hardcode that name —
    ``scripts/phase14_recall.py``'s ``ADAPTER_PATH`` (plan 14-06) and the Gradio demo (plan
    14-08). The calibration arms keep their scoped names because they are disposable evidence,
    never shipped. Disjointness across every arm pair is preserved and CI-tested.
    """
    adapter = (
        _REPO_ROOT / "checkpoints" / "persona_adapter.pt"
        if arm == "real"
        else _REPO_ROOT / "checkpoints" / f"phase14_{arm}_adapter.pt"
    )
    return {
        "bin": _REPO_ROOT / "data" / f"persona_{arm}_train.bin",
        "mask": _REPO_ROOT / "data" / f"persona_{arm}_train_mask.bin",
        "csv": _REPO_ROOT / "results" / f"phase14_{arm}" / "run.csv",
        "checkpoint": _REPO_ROOT / "checkpoints" / f"phase14_{arm}_latest.pt",
        "adapter": adapter,
    }


def refuse_if_exists(paths):
    """Refuse-to-rerun: an arm's outputs are RECORDED evidence once written — a rerun on
    drifted code or a drifted fact set would silently replace them. Fail loud, name the file."""
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[teach_persona] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )


def render_episodes(facts, family_ids, *, second_person=False):
    """The facts x families x instances cross product, as ``(question, answer)`` pairs."""
    episodes = []
    for fact in facts:
        for family_id in sorted(family_ids):
            episodes.extend(fs.render_family(family_id, fact, second_person=second_person))
    return episodes


def build_bins(tok, episodes, bin_path, mask_path, *, replay_ratio=0.0):
    """Encode every episode into an aligned token/mask bin pair; return the measured stats.

    Every episode goes through ``encode_dialogue`` with an EMPTY persona — the bare
    ``<|system|>`` clean-room shape — so the D-07 persona cap is a structural no-op here and is
    deliberately never applied. Ids are ``uint16``, mask is ``uint8``, written with the
    ``prepare_dialog_corpus.py`` shard-and-write idiom.
    """
    id_shards, mask_shards, lengths, fractions = [], [], [], []
    for question, answer in episodes:
        ids, mask = encode_dialogue(tok, [], [(question, answer)])
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))
        lengths.append(len(ids))
        fractions.append(float(np.mean(mask)))

    teaching_tokens = int(sum(lengths))
    replay_tokens = 0
    if replay_ratio > 0:
        replay_tokens = _prepend_replay(id_shards, mask_shards, replay_ratio, teaching_tokens)

    ids_all = np.concatenate(id_shards)
    mask_all = np.concatenate(mask_shards)
    ids_all.tofile(bin_path)
    mask_all.tofile(mask_path)

    # --- proof 1: the two bins must be 1:1 element-aligned ---
    if len(ids_all) != len(mask_all):
        raise SystemExit(
            f"[teach_persona] token bin has {len(ids_all):,} elements but mask bin has "
            f"{len(mask_all):,} — bins must be 1:1 aligned."
        )

    # --- proof 2: the corpus floor (14-RESEARCH Pitfall 5) ---
    # get_batch_memmap_masked calls np.random.randint(0, len(data) - block_size - 1); at or
    # below block_size + 1 that dies with an opaque `ValueError: low >= high` at step 0. A
    # shrunken fact set is D-06's explicitly anticipated outcome, so this floor is reachable.
    if len(ids_all) <= BLOCK_SIZE + 1:
        raise SystemExit(
            f"[teach_persona] teaching corpus is {len(ids_all):,} tokens, at or below the "
            f"{BLOCK_SIZE + 1:,}-token floor (block_size + 1) — get_batch_memmap_masked cannot "
            "draw a window and would die with an opaque numpy `low >= high`. Add facts, add "
            "taught families, or add paraphrase instances."
        )

    # --- proof 3: the Phase-14 mask-fraction band (see the S2 derivation above) ---
    frac = float(mask_all.mean())
    lo, hi = MASK_FRACTION_BAND
    if not lo <= frac <= hi:
        raise SystemExit(
            f"[teach_persona] masked fraction {frac:.4f} outside [{lo}, {hi}] — exactly 0.0 "
            "means the mask was never set and exactly 1.0 means it covers everything "
            "(PITFALLS-14). Span-level correctness is pinned by test_answer_span_mask."
        )

    return {
        "episodes": len(episodes),
        "tokens": int(len(ids_all)),
        "teaching_tokens": teaching_tokens,
        "replay_tokens": replay_tokens,
        "replay_ratio": replay_ratio,
        "episode_len_mean": float(np.mean(lengths)),
        "episode_len_min": int(min(lengths)),
        "episode_len_max": int(max(lengths)),
        "mask_fraction": frac,
        "mask_fraction_mean": float(np.mean(fractions)),
        "mask_fraction_min": float(min(fractions)),
        "mask_fraction_max": float(max(fractions)),
    }


def _prepend_replay(id_shards, mask_shards, replay_ratio, teaching_tokens):
    """Concatenate a leading slice of the PersonaChat bins ahead of the teaching episodes.

    Build-time replay (Open Q5): ``train()`` accepts one ``train_bin``, so the mixture ratio is
    baked into the bin instead of into the loop. Returns the replay token count.
    """
    if not DIALOG_TRAIN_BIN.exists() or not DIALOG_TRAIN_MASK.exists():
        raise SystemExit(
            f"[teach_persona] replay arm needs {DIALOG_TRAIN_BIN} and {DIALOG_TRAIN_MASK} — run "
            "`python scripts/prepare_dialog_corpus.py` first."
        )
    want = int(round(replay_ratio * teaching_tokens))
    replay_ids = np.fromfile(DIALOG_TRAIN_BIN, dtype=np.uint16, count=want)
    replay_mask = np.fromfile(DIALOG_TRAIN_MASK, dtype=np.uint8, count=want)
    if len(replay_ids) != want or len(replay_mask) != want:
        raise SystemExit(
            f"[teach_persona] replay slice short: wanted {want:,} tokens, read "
            f"{len(replay_ids):,} ids / {len(replay_mask):,} mask elements."
        )
    id_shards.insert(0, replay_ids)
    mask_shards.insert(0, replay_mask)
    return want


def _is_subsequence(haystack, needle):
    """True iff ``needle`` appears as a CONTIGUOUS run inside ``haystack`` (both id lists)."""
    n = len(needle)
    if n == 0 or n > len(haystack):
        return False
    return any(haystack[i : i + n] == needle for i in range(len(haystack) - n + 1))


def sanity_check(tok, arm, bin_path, mask_path, facts, stats):
    """The post-build proofs that need more than the bins themselves (proofs 4-6)."""
    # --- proof 4: end-to-end smoke — a real masked batch carries the -100 sentinels ---
    x, y = get_batch_memmap_masked(bin_path, mask_path, 4, BLOCK_SIZE, "cpu")
    if tuple(x.shape) != (4, BLOCK_SIZE) or tuple(y.shape) != (4, BLOCK_SIZE):
        raise SystemExit(
            f"[teach_persona] {arm}: smoke draw shapes {tuple(x.shape)}/{tuple(y.shape)} != "
            f"(4, {BLOCK_SIZE})."
        )
    if not bool((y == -100).any()):
        raise SystemExit(
            f"[teach_persona] {arm}: smoke draw y contains NO -100 sentinel — the mask never "
            "reached the targets (PITFALLS-14)."
        )

    # --- proof 5: DEMO-05's paraphrase band, per fact ---
    lo, hi = fs.PARAPHRASES_PER_FACT_TARGET
    for fact in facts:
        count = sum(len(fs.render_family(fid, fact)) for fid in fs.TAUGHT_FAMILY_IDS)
        if not lo <= count <= hi:
            raise SystemExit(
                f"[teach_persona] {arm}: fact {fact.id!r} has {count} taught paraphrases, "
                f"outside DEMO-05's [{lo}, {hi}] band."
            )

    # --- proof 6: token-level held-out guarantee, on the bin that was actually written ---
    # The TOKEN half of RESEARCH Pattern 5's structural guarantee. A string-level check alone
    # can miss a leak that survives detokenization differences; the id check cannot. The needle
    # is `build_recall_prompt` — the same ids the scoring harness will send at recall time.
    written = np.fromfile(bin_path, dtype=np.uint16).tolist()
    for question in fs.heldout_questions():
        if _is_subsequence(written, build_recall_prompt(tok, question)):
            raise SystemExit(
                f"[teach_persona] {arm}: held-out question {question!r} appears in the teaching "
                "bin as a contiguous id run — the DEMO-06 never-seen split is compromised."
            )

    print(f"  smoke draw: x/y (4, {BLOCK_SIZE}), y carries -100 — ok")
    print(f"  paraphrases/fact inside {fs.PARAPHRASES_PER_FACT_TARGET} for {len(facts)} facts")
    print(f"  {len(fs.heldout_questions())} held-out questions: none present at token level")
    print(
        f"  mask fraction: mean {stats['mask_fraction_mean']:.4f} / "
        f"min {stats['mask_fraction_min']:.4f} / max {stats['mask_fraction_max']:.4f}"
    )


def arm_spec(arm):
    """(facts, second_person, replay_ratio) for one arm — the only per-arm branching."""
    if arm == "cal_first_person":
        return fs.CALIBRATION_FACTS, False, REPLAY_RATIO
    if arm == "cal_first_person_replay":
        return fs.CALIBRATION_FACTS, False, REPLAY_ARM_RATIO
    if arm == "cal_second_person":
        return fs.REGISTER_ARM_FACTS, True, REPLAY_RATIO
    if arm == "real":
        return fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS, False, REPLAY_RATIO
    raise SystemExit(f"[teach_persona] unknown arm {arm!r} — expected one of {ARMS}")


def build_arm_bins(arm, facts, family_ids, *, second_person=False, replay_ratio=0.0):
    """Render, encode, write and prove one arm's teaching bins; return ``(tok, stats, paths)``.

    The whole bins half behind one call, so the training half (below) has exactly one seam into
    it and no arm can be trained on bins built by a different code path.
    """
    outputs = arm_outputs(arm)
    refuse_if_exists([outputs["bin"], outputs["mask"]])

    seed_everything(SEED)
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain
    episodes = render_episodes(facts, family_ids, second_person=second_person)
    started = time.time()
    stats = build_bins(tok, episodes, outputs["bin"], outputs["mask"], replay_ratio=replay_ratio)
    sanity_check(tok, arm, outputs["bin"], outputs["mask"], facts, stats)

    print(
        f"[teach_persona] {arm}: {stats['episodes']:,} episodes, {stats['tokens']:,} tokens "
        f"({stats['teaching_tokens']:,} teaching + {stats['replay_tokens']:,} replay), "
        f"episode length mean {stats['episode_len_mean']:.1f} "
        f"[{stats['episode_len_min']}, {stats['episode_len_max']}]"
    )
    print(
        f"[teach_persona] bins provenance: seed={SEED} git_sha={git_sha()} pid={os.getpid()} "
        f"torch={torch.__version__} arm={arm} second_person={second_person} "
        f"replay_ratio={replay_ratio} mask_fraction={stats['mask_fraction']:.4f} "
        f"wall={time.time() - started:.1f}s "
        f"utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
    )
    print(f"[teach_persona] bins written (gitignored): {outputs['bin']} + {outputs['mask']}")
    return tok, stats, outputs


USAGE = (
    f"usage: python scripts/teach_persona.py {{{'|'.join(ARMS)}}}\n"
    "       python scripts/teach_persona.py --calibration [--force]\n"
    "       python scripts/teach_persona.py --rewrite-report [--force]"
)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # Plan 14-09's two modes. Both are defined below in the CALIBRATION RUN section.
    if argv and argv[0] == "--calibration":
        run_calibration(argv[1:])
        return
    if argv and argv[0] == "--rewrite-report":
        rewrite_report(argv[1:])
        return
    if len(argv) != 1 or argv[0] not in ARMS:
        raise SystemExit(USAGE)
    arm = argv[0]

    facts, second_person, replay_ratio = arm_spec(arm)
    train_arm(
        arm,
        facts=facts,
        family_ids=fs.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
    )


# =====================================================================================
# ===== TRAINING HALF — copies scripts/train_adapter_smoke.py, NOT the bins half =====
# =====================================================================================
#
# load -> inject_lora -> mark_only_lora_trainable -> snapshot_params -> train(penalty_fn=None)
# -> canary -> export_adapter. Everything below this line follows the adapter-smoke register.

# --- Recipe constants (each carries its provenance) ---

# LORA-01 / Phase 9 production defaults r=8, alpha=16.0. At the convbase shape (6 layers,
# n_embd=384) that is 36 wrapped projections (6 per block) and 331,776 trainable parameters
# (r * n_layer * 18 * n_embd) — the ~1.35 MB persona file. Both numbers are asserted below.
LORA_CFG = LoRAConfig()

# The adapter-run learning-rate band from 09-RESEARCH Pattern 3. A/B are the ONLY trainable
# tensors, so an aggressive rate cannot damage the base — the worst case is a bad adapter,
# which is deletable, and the canary below proves the base never moved either way.
LR = 3e-4

# Adapter runs MUST override TrainConfig's 0.1 default: weight decay on A/B fights the low-rank
# update (scripts/train_adapter_smoke.py, 09-RESEARCH Pattern 3).
WEIGHT_DECAY = 0.0

BATCH_SIZE = 8
# 14-RESEARCH F5 arithmetic: BATCH_SIZE * BLOCK_SIZE = 8 * 256 = 2,048 tokens/step against a
# ~8,200-token teaching corpus is ~25% of the corpus per step, so 200 steps is ~50 epochs — the
# deliberate overfit ARCHITECTURE Anti-pattern 6 prescribes for weight-based memory.
# MAX_STEPS is one of the numbers the CALIBRATION run MEASURES (Assumption A3), not a number
# this plan claims to know; it is deliberately NOT pinned by a test for that reason.
MAX_STEPS = 200
WARMUP_STEPS = 20
EVAL_INTERVAL = 10  # 20 curve points over the run — the collateral-collapse trace, not a gate
CHECKPOINT_INTERVAL = 50  # a killed run loses <= 50 steps; 200 steps needs no heavier cadence


def train_arm(arm, *, facts, family_ids, second_person=False, replay_ratio=0.0):
    """Build one arm's bins, train ONLY its LoRA parameters on them, and export the adapter.

    Returns a dict carrying the arm paths, the bins stats, the final train loss, and the
    adapter-ON/adapter-OFF masked dialogue-val PPL pair (the no-collateral-collapse endpoint).
    """
    verdict = _require_go_verdict(FACTSET_REPORT)
    print(f"[teach_persona] D-06 verdict: {verdict} — proceeding with arm {arm!r}")
    if arm == "real":
        # W-02: the real run additionally gates on the CALIBRATION verdict. The gate is
        # arm-conditional on purpose — the calibration arms are what PRODUCE that report, so
        # gating them on it would be a deadlock. The asymmetry is deliberate, not an oversight.
        cal_verdict = _require_go_verdict(CALIBRATION_REPORT)
        print(f"[teach_persona] calibration verdict: {cal_verdict} — real arm cleared (W-02)")

    paths = arm_outputs(arm)
    # Refuse on ALL five targets up front, before a single token is written: discovering a
    # recorded checkpoint only after rebuilding the bins would already have clobbered them.
    refuse_if_exists(
        [paths["bin"], paths["mask"], paths["csv"], paths["checkpoint"], paths["adapter"]]
    )

    summary = preflight_device(strict=True)  # CUDA-P100 -> MPS -> CPU raise, BEFORE the run
    print(f"[teach_persona] preflight: {summary}")
    runtime = RuntimeConfig()  # resolves the preflighted device (MPS on the M3, fp32, AMP off)

    if not CONVBASE_BEST.exists():
        raise SystemExit(
            f"[teach_persona] missing {CONVBASE_BEST} — the frozen conversational base. Run the "
            "Phase-12 conversational fine-tune (or restore the checkpoint) before teaching."
        )
    if not DIALOG_VAL_BIN.exists() or not DIALOG_VAL_MASK.exists():
        raise SystemExit(
            f"[teach_persona] missing {DIALOG_VAL_BIN} / {DIALOG_VAL_MASK} — the held-out "
            "PersonaChat val pair IS the collateral-collapse metric (D-11.2 / D-15). Run "
            "`python scripts/prepare_dialog_corpus.py` first."
        )

    tok, stats, paths = build_arm_bins(
        arm, facts, family_ids, second_person=second_person, replay_ratio=replay_ratio
    )
    del tok  # the training half needs the bins, not the tokenizer

    # Re-seed IMMEDIATELY before the GPT build: this seed owns the training data order (the
    # finetune_ab.py provenance note), and the bins build above consumed numpy RNG in its smoke
    # draw. Seeding once at the top would make the data order depend on the bins path.
    seed_everything(SEED)

    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy
    # objects. TRUSTED-only read of the project's OWN checkpoint (T-14-04) — never a foreign
    # file. The SHAREABLE artifact path stays weights_only=True via export_adapter.
    blob = torch.load(CONVBASE_BEST, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering.

    n_layer = blob["model_config"]["n_layer"]
    n_embd = blob["model_config"]["n_embd"]
    n_wrapped = inject_lora(model, LORA_CFG)
    if n_wrapped != 6 * n_layer:
        raise SystemExit(
            f"[teach_persona] inject_lora wrapped {n_wrapped} projections, expected "
            f"6 * n_layer = {6 * n_layer}"
        )
    mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Closed-form census: 18 * r * n_embd per layer across the six projections (== 331,776 at
    # the production shape r=8 / 6L / 384d).
    expected_trainable = LORA_CFG.r * n_layer * 18 * n_embd
    if trainable != expected_trainable:
        raise SystemExit(
            f"[teach_persona] trainable census {trainable} != r*n_layer*18*n_embd = "
            f"{expected_trainable}"
        )
    print(f"[teach_persona] injected {n_wrapped} wrappers, {trainable} trainable params")

    # Move BEFORE snapshotting: torch.equal raises on cross-device tensors, so the canary
    # snapshot and the post-run params must share the training device.
    model.to(runtime.device)
    before = snapshot_params(model)

    paths["csv"].parent.mkdir(parents=True, exist_ok=True)
    paths["checkpoint"].parent.mkdir(parents=True, exist_ok=True)

    final = train(
        train_config=TrainConfig(
            lr=LR,
            warmup_steps=WARMUP_STEPS,
            max_steps=MAX_STEPS,
            batch_size=BATCH_SIZE,
            weight_decay=WEIGHT_DECAY,
            seed=SEED,
        ),
        runtime_config=runtime,
        model=model,
        model_config=model_cfg,
        train_bin=paths["bin"],
        # Phase 14 REVERSES Phase 12's unmasked verdict, by design and not by drift: PITFALLS-14
        # is explicit that personalization/QA teaching must cover ANSWER tokens ONLY, or the
        # model learns to imitate questions instead of answering them. Phase 12 trained a model
        # OF a dialogue, which is a different objective on the same corpus shape.
        train_mask_bin=paths["mask"],
        # dialog_val.bin + its mask, so the IN-LOOP curve IS the collateral-collapse signal —
        # D-11.2 and D-15 get a per-step trace instead of only endpoint numbers (14-RESEARCH
        # Open Q3). Gate decisions still use the deterministic masked_perplexity sweep below and
        # NEVER in-loop val_loss, whose 20-random-batch sampling noise would pollute a margin
        # (Phase 12, plan 12-02).
        val_bin=DIALOG_VAL_BIN,
        val_mask_bin=DIALOG_VAL_MASK,
        # penalty_fn=None is STRUCTURALLY FORCED here, not merely preferable, for two
        # independent reasons (14-RESEARCH Pattern 3):
        # (a) with the base frozen, base theta never moves, so the EWC quadratic anchor is a
        #     constant — zero gradient into A/B, pure wasted compute, and a chart that would
        #     credit EWC with retention frozen-base LoRA produces by construction (PITFALLS P7);
        # (b) inject_lora renames every wrapped base parameter with a `.base.` infix while the
        #     Fisher cache keys are vanilla-GPT names, and EWCPenalty.__call__ raises ValueError
        #     on ANY fisher key missing from model.named_parameters() — so passing the existing
        #     Fisher to an injected model is a hard crash, not a silent no-op.
        penalty_fn=None,
        log_path=paths["csv"],
        eval_interval=EVAL_INTERVAL,
        checkpoint_path=paths["checkpoint"],
        checkpoint_interval=CHECKPOINT_INTERVAL,
        return_final_loss=True,
    )

    # CANARY (LORA-02 / LORA-05): every trainable moved, every frozen base param bit-untouched.
    # The explicit raises ARE the proof — non-zero exit even under python -O.
    if not math.isfinite(float(final)):
        raise SystemExit(f"[teach_persona] non-finite final loss {final!r} (PITFALLS P5)")
    for name, param in model.named_parameters():
        if param.requires_grad:
            if torch.equal(param, before[name]):
                raise SystemExit(
                    f"[canary] trainable {name} did not move — silent training failure (P5)"
                )
        elif not torch.equal(param, before[name]):
            raise SystemExit(
                f"[canary] frozen base param {name} changed — grad isolation broken (LORA-02)"
            )
    print("[teach_persona] canary passed: all lora_ moved, base bit-untouched")

    # Fingerprint READ from the base checkpoint, never recomputed (provenance trio, D-02).
    export_adapter(
        paths["adapter"],
        adapter=lora_state_dict(model),
        lora_config=asdict(LORA_CFG),
        base_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )
    size_mb = paths["adapter"].stat().st_size / 1e6
    print(f"[teach_persona] wrote {paths['adapter']} ({size_mb:.2f} MB)")

    # The no-collateral-collapse endpoint: the SAME deterministic sweep with the adapter on and
    # off, in one process on one set of weights, so the only difference is the LoRA enabled flag.
    ppl_on, scored_on = masked_perplexity(
        model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device
    )
    with adapter_disabled(model):
        ppl_off, scored_off = masked_perplexity(
            model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device
        )
    if scored_on != scored_off:
        raise SystemExit(
            f"[teach_persona] adapter-on scored {scored_on:,} targets but adapter-off scored "
            f"{scored_off:,} — the two sweeps must cover the identical target set."
        )

    print(
        f"[teach_persona] masked dialogue-val PPL: adapter OFF {ppl_off:.4f} / ON {ppl_on:.4f} "
        f"({(ppl_on - ppl_off) / ppl_off:+.2%} over {scored_on:,} scored targets)"
    )
    print(
        f"[teach_persona] run provenance: arm={arm} seed={SEED} lr={LR} "
        f"weight_decay={WEIGHT_DECAY} batch_size={BATCH_SIZE} max_steps={MAX_STEPS} "
        f"warmup_steps={WARMUP_STEPS} block_size={BLOCK_SIZE} "
        f"base_fingerprint=(git_sha={blob['git_sha']}, step={blob['step']}, "
        f"val_loss={blob['val_loss']}) driver_git_sha={git_sha()} pid={os.getpid()} "
        f"device={runtime.device} torch={torch.__version__} "
        f"second_person={second_person} replay_ratio={replay_ratio} "
        f"mask_fraction={stats['mask_fraction']:.4f} final_train_loss={float(final):.4f} "
        f"utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
    )
    return {
        "arm": arm,
        "paths": paths,
        "stats": stats,
        "final_train_loss": float(final),
        "ppl_adapter_on": float(ppl_on),
        "ppl_adapter_off": float(ppl_off),
        "scored_targets": int(scored_on),
    }


# =====================================================================================
# ===== CALIBRATION_DECISION_RULE — committed BEFORE the calibration run exists =====
# =====================================================================================
#
# This block is committed BEFORE the calibration run produces a single number, and git history
# order is the pre-registration proof (D-09 condition 2 — the rule is never chosen after seeing
# the results; `git log -S CALIBRATION_DECISION_RULE -- scripts/teach_persona.py` shows the
# rule commit predating every calibration output). ONE calibration run answers four questions —
# the recall threshold (D-09), the family allocation (D-14), the replay verdict (D-15), and the
# register verdict (D-21) — from one measured source, instead of four separately-justified
# guesses. Every literal below carries its provenance in its own comment, and every function's
# docstring names its boundary behavior explicitly (the finetune_ab.py:112-122 register).

# Reused BLIND from Phase 12's noise-floor discipline: the same deliberately conservative
# default, NOT re-chosen for Phase 14.
CAL_MARGIN_K = 2

# The fraction of the calibration ceiling the real run's threshold is set to. The calibration
# fact set is disjoint and disposable, so its measured rate is a CEILING estimate, not a target;
# discounting it is what keeps the real threshold from being a number chosen to be passed.
THRESHOLD_DISCOUNT = 0.60

# Below this the metric is not distinguishable from the closed-book control at
# N_SEEDED_SAMPLES = 8, so a lower "threshold" would be meaningless rather than lenient.
THRESHOLD_FLOOR = 0.20

# The recall gain below which adding taught families is judged saturated (D-14's "recall
# saturating with fewer taught instances than the literature's ~10-per-fact figure suggests").
# 14-RESEARCH Pattern 5 records ~10/fact as a floor OBSERVED AT 7B+ SCALE, not a target for 13.9M.
SATURATION_DELTA = 0.05

# The per-family standard deviation of held-out recall above which the real set needs MORE
# held-out families, even at the cost of fewer taught families than the injection literature
# recommends (D-14, second clause).
HELDOUT_VARIANCE_TRIGGER = 0.15

# The fractional increase in masked dialogue val PPL (adapter ON vs OFF, held-out PersonaChat)
# above which replay becomes MANDATORY for the real run (D-15). Below it the real run proceeds
# WITHOUT replay, preserving the full teaching signal rather than diluting it against an
# unconfirmed risk.
COLLAPSE_PPL_TRIGGER = 0.10

# The absolute held-out recall margin by which first-person must beat second-person to count as
# a win (D-21 condition 3, written before the arm runs).
REGISTER_WIN_MARGIN = 0.10

# Both trigger comparisons round the measured ratio to this many decimals BEFORE comparing.
# Without it the boundary is not a boundary: a PPL pair of (2.0, 2.2) — an exact 10% increase
# in decimal — reconstructs in binary as 0.10000000000000009, which is strictly greater than
# COLLAPSE_PPL_TRIGGER and would TRIP a rule whose stated semantics are "the boundary does not
# trigger". Ten decimals is six orders of magnitude coarser than double-precision noise (~1e-16)
# and six orders finer than any effect these gates can resolve, so the rounding decides only
# cases that are exactly on the line and never a real measurement.
RATIO_DECIMALS = 10


def lock_thresholds(cal_taught_rate, cal_heldout_rate):
    """D-09: turn the calibration arm's measured recall rates into the real run's thresholds.

    Each threshold is ``max(THRESHOLD_FLOOR, round(rate * THRESHOLD_DISCOUNT, 4))``. What is
    pre-registered is the PROCEDURE, not a blind number — the number cannot exist before the
    calibration run, but the rule that produces it must, or the threshold is just a value chosen
    to be cleared. The returned pair becomes ``phase14_recall.TAUGHT_THRESHOLD`` /
    ``HELDOUT_THRESHOLD`` in plan 14-09.

    Boundary: the floor CLAMPS, it does not reject — a calibration rate low enough to discount
    below ``THRESHOLD_FLOOR`` yields exactly ``THRESHOLD_FLOOR``, and the fact that the floor
    bound rather than the discount is what plan 14-09's report must state.

    Returns:
        ``(taught_threshold, heldout_threshold)``.
    """
    return (
        max(THRESHOLD_FLOOR, round(cal_taught_rate * THRESHOLD_DISCOUNT, 4)),
        max(THRESHOLD_FLOOR, round(cal_heldout_rate * THRESHOLD_DISCOUNT, 4)),
    )


def _refuse_move(taught, family_id):
    """Why ``family_id`` may NOT move off the taught side, or None when the move is legal.

    The four D-14 invariants live here so ``lock_family_allocation`` reads as the policy and
    this reads as the contract.
    """
    if family_id == "F4":
        return (
            "D-22 keeps F4 (reversed-direction forms) on the taught side — the reversal curse "
            "is a literature failure mode, and moving it would poison the evidence D-20(c) "
            "depends on"
        )
    remaining = set(taught) - {family_id}
    if len(remaining) < 2:
        return f"at least two families must remain taught (would leave {len(remaining)})"
    lo, hi = fs.PARAPHRASES_PER_FACT_TARGET
    for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS:
        count = sum(len(fs.render_family(fid, fact)) for fid in remaining)
        if not lo <= count <= hi:
            return (
                f"fact {fact.id!r} would drop to {count} taught paraphrases, outside DEMO-05's "
                f"[{lo}, {hi}] band (W-03) — build_bins proof #5 would SystemExit the real run"
            )
    return None


def lock_family_allocation(per_family_gain, heldout_family_std, taught_ids, heldout_ids):
    """D-14: apply the calibration measurements to the taught/held-out family allocation.

    A taught family whose marginal recall gain is ``< SATURATION_DELTA`` MOVES to the held-out
    side; if ``heldout_family_std > HELDOUT_VARIANCE_TRIGGER`` the lowest-gain taught family
    also moves. Candidates are considered lowest-gain first.

    **It MOVES families between the two sides and NEVER drops one (B-02).**
    ``tests/test_phase14_teaching.py::test_families_disjoint`` asserts that the union of the two
    sets is every key of ``FAMILIES``, and that assertion is the AUTHORITATIVE allocation
    contract for the phase. Dropping a saturated family would shrink the union and turn that
    test red at wave 6 with nothing saying which contract wins. Moving is also the honest choice
    on the merits: a saturated taught family is precisely a family the model no longer needs
    teaching on, so moving it to held-out INCREASES the evidence for the
    learning-vs-memorization split D-20(c) depends on, where dropping it would discard that
    evidence.

    Four invariants hold regardless of the numbers:
      1. the two sets stay disjoint AND their union stays every key of ``FAMILIES`` (B-02);
      2. ``F4`` stays taught (D-22 — the reversal curse is a literature failure mode);
      3. at least two families remain on each side;
      4. every locked fact's taught-instance count stays inside
         ``phase14_factset.PARAPHRASES_PER_FACT_TARGET`` (W-03). A move that would push any fact
         below the band's lower bound is REFUSED — without this, a saturation-driven move could
         trip ``build_bins`` proof #5 and ``SystemExit`` the wave-8 real run with no remedy.

    Boundary: a gain of exactly ``SATURATION_DELTA`` is NOT saturated (strict ``<``), and a std
    of exactly ``HELDOUT_VARIANCE_TRIGGER`` does NOT trigger the extra move (strict ``>``).

    Refusals are PRINTED rather than returned, so the shape stays a plain ``(taught, heldout)``
    pair for plan 14-09's caller; that plan captures this driver's stdout into
    ``results/phase14_calibration_report.md``, which is where a refused move is recorded.

    Returns:
        ``(taught_ids, heldout_ids)`` as sets.
    """
    taught, heldout = set(taught_ids), set(heldout_ids)
    candidates = sorted(
        (fid for fid in taught if per_family_gain.get(fid, 0.0) < SATURATION_DELTA),
        key=lambda fid: (per_family_gain.get(fid, 0.0), fid),
    )
    if heldout_family_std > HELDOUT_VARIANCE_TRIGGER and taught:
        lowest = min(taught, key=lambda fid: (per_family_gain.get(fid, 0.0), fid))
        if lowest not in candidates:
            candidates.append(lowest)

    for family_id in candidates:
        refusal = _refuse_move(taught, family_id)
        if refusal is not None:
            print(f"[teach_persona] allocation: REFUSED moving {family_id} to held-out — {refusal}")
            continue
        taught.discard(family_id)
        heldout.add(family_id)
        print(
            f"[teach_persona] allocation: moved {family_id} taught -> held-out "
            f"(gain {per_family_gain.get(family_id, 0.0):.4f} < {SATURATION_DELTA})"
        )
    return taught, heldout


def replay_required(ppl_adapter_off, ppl_adapter_on):
    """D-15: does the real run need PersonaChat replay mixed into its teaching bin?

    True iff the adapter's fractional increase in masked dialogue-val PPL exceeds
    ``COLLAPSE_PPL_TRIGGER``. The two numbers must come from D-15's PAIRED arms — the same
    prompts, the same weights, one process, only the LoRA enabled flag differing — or the
    comparison measures run-to-run noise instead of the adapter.

    Boundary: exactly at the trigger, replay is NOT required (strict ``>`` — the rule dies under
    ``>=``). The ratio is rounded to ``RATIO_DECIMALS`` first so that "exactly at the trigger"
    means the decimal value, not whichever double happens to bracket it.
    """
    ratio = (ppl_adapter_on - ppl_adapter_off) / ppl_adapter_off
    return round(ratio, RATIO_DECIMALS) > COLLAPSE_PPL_TRIGGER


def first_person_wins(fp_heldout_rate, sp_heldout_rate):
    """D-21 condition 3: does first-person register beat second-person on held-out recall?

    True iff the absolute margin exceeds ``REGISTER_WIN_MARGIN``.

    A False result does NOT reopen D-01's register lock. D-01 rests on measured QUALITATIVE
    evidence (14-RESEARCH F3/F5, including the "structure copied, content not" finding); this
    arm measures only the head-to-head delta that decision was missing. A negative is reported
    honestly under D-12's register — it is not license to re-author the teaching set mid-phase
    after seeing the numbers, which is the exact move this whole block exists to prevent.

    Boundary: exactly at the margin is NOT a win (strict ``>``), rounded to ``RATIO_DECIMALS``
    for the same reason as ``replay_required``.
    """
    return round(fp_heldout_rate - sp_heldout_rate, RATIO_DECIMALS) > REGISTER_WIN_MARGIN


# One name for plan 14-09 and the tests to reference, so the four derivations travel together.
CALIBRATION_DECISION_RULE = (
    lock_thresholds,
    lock_family_allocation,
    replay_required,
    first_person_wins,
)


# =====================================================================================
# ===== THE CALIBRATION RUN — three arms, one measured source, four derivations =====
# =====================================================================================
#
# `python scripts/teach_persona.py --calibration` runs the three arms in order, scores each
# arm's adapter ON and OFF, applies the four rule functions above MECHANICALLY to the measured
# numbers, and writes `results/phase14_calibration_report.md` with a PENDING verdict for a human
# to replace. Nothing in this section chooses a number: every derived value is the return of a
# function committed in `d7d7917`, before any of these measurements existed.

CAL_ARMS = ("cal_first_person", "cal_first_person_replay", "cal_second_person")

# The measured arm records, dumped so the REPORT is re-renderable from committed evidence rather
# than only from a two-hour MPS run. The calibration measurements are the expensive, unrepeatable
# part; the prose that frames them is not, and a wording fix in `write_calibration_report` must
# never be a reason to re-measure (or, worse, a reason to hand-edit generated evidence).
CALIBRATION_RESULTS = _REPO_ROOT / "results" / "phase14_calibration_results.json"

# Progress cadence for the scoring loops — 598 questions x 2 adapter states is a ~1h run and a
# silent hour is indistinguishable from a hung one.
SCORE_PROGRESS_EVERY = 20


def _sha256(path):
    """Streaming SHA-256 of a gitignored artifact — the adapter's identity in the report.

    ``checkpoints/`` is gitignored, so ``git_sha()`` identifies the CODE that produced an arm but
    says nothing about the WEIGHTS the reported numbers were measured on.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rule_commit_sha():
    """The commit that introduced ``CALIBRATION_DECISION_RULE`` — D-09 condition 2's proof.

    Searched on the tuple's DEFINITION (``CALIBRATION_DECISION_RULE = (``) rather than the bare
    name: the name is also mentioned in comments added by earlier commits, so a bare-name search
    returns the commit that first MENTIONED the rule instead of the one that committed it. The
    oldest match is the introducing commit; the report states it and the human checkpoint
    re-derives it with ``git log -S`` before recording a verdict.
    """
    try:
        found = subprocess.run(
            [
                "git",
                "log",
                "-S",
                "CALIBRATION_DECISION_RULE = (",
                "--format=%H",
                "--",
                "scripts/teach_persona.py",
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=_REPO_ROOT,
        ).stdout.split()
        return found[-1] if found else "unknown"
    except Exception:
        return "unknown"  # provenance is best-effort and never kills a long run (QA-02)


def calibration_items(facts, family_ids):
    """``(family_id, fact, question)`` for every SCORABLE question of these families.

    The self-naming filter is the same MECHANICAL rule the scored harness uses
    (``phase14_recall.contains_value(question, fact.value)``, plan 14-06 deviation 1) rather than
    a hardcoded ``{F4, F5}`` denylist: those two frames name the value in their own question by
    definition, and a question that already contains its answer measures copying from context
    instead of memory in the weights. Naming the families explicitly would silently break the
    moment this very run rewrites the allocation.
    """
    import phase14_recall as pr  # LAZY — the two scripts reference each other (14-05 rule 4).

    items = []
    for fact in facts:
        for family_id in sorted(family_ids):
            for question, _answer in fs.render_family(family_id, fact):
                if pr.contains_value(question, fact.value):
                    continue
                items.append((family_id, fact, question))
    return items


def score_items(model, tok, device, forbid, items, *, label):
    """Score one tier: greedy + ``N_SEEDED_SAMPLES`` per question, aggregated per family.

    ``index`` is the question's position in ITS tier, matching the harness's per-question seeding
    contract, so the adapter-OFF pass replays the identical streams and the two passes are PAIRED
    rather than merely comparable.
    """
    import phase14_recall as pr  # LAZY — see calibration_items.

    per_family, total_k, total_n = {}, 0, 0
    for index, (family_id, fact, question) in enumerate(items):
        drawn = pr.complete_question(model, tok, question, device, forbid, index=index)
        k, n = pr.score_question(drawn["completions"], fact.value)
        fk, fn = per_family.get(family_id, (0, 0))
        per_family[family_id] = (fk + k, fn + n)
        total_k += k
        total_n += n
        if (index + 1) % SCORE_PROGRESS_EVERY == 0:
            print(
                f"  [{label}] {index + 1}/{len(items)} questions, running "
                f"{total_k}/{total_n} = {total_k / total_n:.4f}",
                flush=True,
            )
    if total_n == 0:
        raise SystemExit(f"[teach_persona] tier {label!r} produced no scorable question")
    rates = {fid: k / n for fid, (k, n) in per_family.items()}
    detail = ", ".join(f"{fid} {rate:.4f}" for fid, rate in sorted(rates.items()))
    print(f"[teach_persona] {label}: {total_k}/{total_n} = {total_k / total_n:.4f} ({detail})")
    return {
        "k": total_k,
        "n": total_n,
        "rate": total_k / total_n,
        "per_family": rates,
        "questions": len(items),
    }


def score_arm(arm, facts, adapter_path, device):
    """Measure one arm's recall: taught and held-out, adapter ON and adapter OFF.

    The adapter is loaded back off disk through ``phase14_recall.load_adapted_model`` — the same
    ``weights_only=True`` load-before-inject path the real scored run uses — rather than scoring
    the in-memory training model, so a calibration number and a Phase-14 number come off the same
    pipeline.

    The OFF pass is ``adapter_disabled``: same process, same weights, same prompts, same
    per-question seeds, only the 36 LoRA ``enabled`` flags flipped. It supplies the closed-book
    baseline WITHOUT which a held-out rate is unjudgeable — a rate of 0.4 means one thing against
    a base that scores 0.0 and something else entirely against a base that scores 0.35 — and it
    is the second term of the per-family GAIN that ``lock_family_allocation`` consumes. A family's
    "marginal recall gain" is measured here as its taught rate ON minus its taught rate OFF: the
    recall that teaching that family actually bought, which is exactly what D-14's saturation
    clause asks about.
    """
    import phase14_recall as pr  # LAZY — see calibration_items.

    model, _cfg, tok, forbid, _artifact = pr.load_adapted_model(device, adapter_path=adapter_path)
    taught = calibration_items(facts, fs.TAUGHT_FAMILY_IDS)
    heldout = calibration_items(facts, fs.HELDOUT_FAMILY_IDS)
    print(
        f"[teach_persona] {arm}: scoring {len(taught)} taught + {len(heldout)} held-out "
        f"questions x {1 + pr.N_SEEDED_SAMPLES} draws, adapter ON then OFF"
    )

    on_taught = score_items(model, tok, device, forbid, taught, label=f"{arm} taught ON")
    on_heldout = score_items(model, tok, device, forbid, heldout, label=f"{arm} held-out ON")
    with adapter_disabled(model):
        off_taught = score_items(model, tok, device, forbid, taught, label=f"{arm} taught OFF")
        off_heldout = score_items(model, tok, device, forbid, heldout, label=f"{arm} held-out OFF")

    gain = {
        fid: on_taught["per_family"][fid] - off_taught["per_family"].get(fid, 0.0)
        for fid in on_taught["per_family"]
    }
    heldout_rates = list(on_heldout["per_family"].values())
    # Population std over the held-out families actually measured — this IS the whole population
    # of held-out families, not a sample drawn from a larger one, so pstdev is the correct
    # estimator and stdev's (n-1) correction would inflate it against a pre-registered trigger.
    std = statistics.pstdev(heldout_rates) if len(heldout_rates) > 1 else 0.0
    print(
        f"[teach_persona] {arm}: per-family gain "
        f"{ {fid: round(g, 4) for fid, g in sorted(gain.items())} }, "
        f"held-out per-family std {std:.4f}"
    )
    del model
    return {
        "on_taught": on_taught,
        "on_heldout": on_heldout,
        "off_taught": off_taught,
        "off_heldout": off_heldout,
        "per_family_gain": gain,
        "heldout_family_std": std,
    }


def dump_results(results, provenance_lines):
    """Persist the measured arm records beside the report — the re-render input.

    ``paths`` is dropped rather than serialized: ``arm_outputs(arm)`` reconstructs it exactly, and
    a serialized absolute path would go stale the moment the repo moved.
    """
    payload = {
        "provenance": list(provenance_lines),
        "arms": {
            arm: {key: value for key, value in record.items() if key != "paths"}
            for arm, record in results.items()
        },
    }
    CALIBRATION_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_RESULTS.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[teach_persona] wrote {CALIBRATION_RESULTS}")


def rewrite_report(argv=()):
    """Re-render the report from the RECORDED measurements — no GPU, no re-measurement.

    The measurements are frozen evidence; only the framing around them is re-derived, and it is
    re-derived by the SAME ``derive_all`` + ``write_calibration_report`` code the measured run
    used, so the report stays generated rather than hand-edited. The clobber guard still applies:
    a recorded verdict is not silently overwritten by a re-render.
    """
    _refuse_clobber(CALIBRATION_REPORT, "--force" in argv)
    if not CALIBRATION_RESULTS.exists():
        raise SystemExit(
            f"[teach_persona] missing {CALIBRATION_RESULTS} — run "
            "`python scripts/teach_persona.py --calibration` first."
        )
    payload = json.loads(CALIBRATION_RESULTS.read_text(encoding="utf-8"))
    results = {arm: dict(rec, paths=arm_outputs(arm)) for arm, rec in payload["arms"].items()}
    derived = derive_all(results)
    write_calibration_report(results, derived, payload["provenance"])
    return results, derived


def _refuse_clobber(report_path, force):
    """The ``measure_inflation.py:66-75`` guard: a RECORDED verdict is committed evidence.

    A rerun would reset ``## Verdict`` to PENDING and silently drop whatever the human wrote
    beside it. ``--force`` is the only way past.
    """
    if report_path.exists() and not force:
        recorded = report_path.read_text(encoding="utf-8").split("## Verdict")[-1]
        if "PENDING" not in recorded:
            raise SystemExit(
                f"[teach_persona] {report_path} already carries a recorded verdict — it is "
                "committed evidence (D-09). Pass --force to overwrite and re-measure."
            )


def _arm_rows(arm, record):
    """One arm's ``## Measured Results`` table."""
    stats = record["stats"]
    on_t, on_h = record["on_taught"], record["on_heldout"]
    off_t, off_h = record["off_taught"], record["off_heldout"]
    ppl_off, ppl_on = record["ppl_adapter_off"], record["ppl_adapter_on"]
    gain = ", ".join(f"`{fid}` {g:+.4f}" for fid, g in sorted(record["per_family_gain"].items()))
    heldout_by_family = ", ".join(
        f"`{fid}` {r:.4f}" for fid, r in sorted(on_h["per_family"].items())
    )
    return [
        f"### `{arm}`",
        "",
        "| Measurement | Value |",
        "|---|---|",
        f"| final train loss | {record['final_train_loss']:.4f} |",
        f"| taught recall rate (adapter ON) | **{on_t['rate']:.4f}** ({on_t['k']}/{on_t['n']}) |",
        f"| held-out recall rate (adapter ON) | **{on_h['rate']:.4f}** ({on_h['k']}/{on_h['n']}) |",
        f"| taught recall rate (adapter OFF — closed book) | {off_t['rate']:.4f} "
        f"({off_t['k']}/{off_t['n']}) |",
        f"| held-out recall rate (adapter OFF — closed book) | {off_h['rate']:.4f} "
        f"({off_h['k']}/{off_h['n']}) |",
        f"| per-family gain (taught ON − taught OFF) | {gain} |",
        f"| held-out rate by family | {heldout_by_family} |",
        f"| held-out per-family std (population) | {record['heldout_family_std']:.4f} |",
        f"| masked dialogue-val PPL, adapter OFF | {ppl_off:.4f} |",
        f"| masked dialogue-val PPL, adapter ON | {ppl_on:.4f} |",
        # 2 decimals of a percent, deliberately: the PPL pair is recorded to 4 decimal places
        # (that is the precision the run reports and the JSON stores), so a 4-decimal PERCENTAGE
        # would print digits the stored measurement cannot support and would shift under a
        # re-render. Two decimals is stable, and no gate resolves anything finer.
        f"| PPL delta (ON vs OFF) | {(ppl_on - ppl_off) / ppl_off:+.2%} "
        f"over {record['scored_targets']:,} scored targets |",
        f"| measured mask fraction | {stats['mask_fraction']:.4f} (band {MASK_FRACTION_BAND}) |",
        f"| teaching corpus tokens | {stats['tokens']:,} "
        f"({stats['teaching_tokens']:,} teaching + {stats['replay_tokens']:,} replay) |",
        f"| episodes | {stats['episodes']:,} |",
        f"| scored questions | {on_t['questions']} taught + {on_h['questions']} held-out |",
        f"| wall clock | {record['wall_clock']:.0f}s |",
        f"| adapter | `{record['paths']['adapter'].name}` sha256 "
        f"`{record['adapter_sha256'][:16]}…` |",
        f"| run CSV | `results/phase14_{arm}/run.csv` |",
        "",
    ]


def write_calibration_report(results, derived, provenance_lines):
    """Write ``results/phase14_calibration_report.md`` — measurements, then the four derivations.

    The ``results/phase13_ab_report.md`` register: a Shared-Pattern-6 opener stating what the
    numbers are and are not, the pre-registration block first, the measurements second, and the
    derivations last — each naming the rule function that produced it. The verdict is left
    PENDING; a human records it at plan 14-09's checkpoint.
    """
    base = results["cal_first_person"]
    replay = results["cal_first_person_replay"]
    register = results["cal_second_person"]
    taught_threshold, heldout_threshold = derived["thresholds"]
    floor_text = "the FLOOR (the discount fell below it)"
    taught_bound = floor_text if derived["taught_floor_bound"] else "the DISCOUNT"
    heldout_bound = floor_text if derived["heldout_floor_bound"] else "the DISCOUNT"
    gain_map = {fid: round(g, 4) for fid, g in sorted(base["per_family_gain"].items())}
    replay_delta = (replay["ppl_adapter_on"] - replay["ppl_adapter_off"]) / replay[
        "ppl_adapter_off"
    ]
    base_delta = (base["ppl_adapter_on"] - base["ppl_adapter_off"]) / base["ppl_adapter_off"]
    register_margin = base["on_heldout"]["rate"] - register["on_heldout"]["rate"]

    lines = [
        "# PersonaCore — Phase 14 Calibration Report (D-09 / D-14 / D-15 / D-21)",
        "",
        "> **What these numbers are.** A measurement on THROWAWAY fact sets that are disjoint",
        "> from the real one, run for the sole purpose of deriving four numbers — the recall",
        "> thresholds, the taught/held-out family allocation, the replay verdict, and the",
        "> teaching-register verdict — under a decision rule committed to git BEFORE this run",
        "> produced a single number. One calibration run answers four questions from one measured",
        "> source instead of four separately-justified guesses.",
        ">",
        "> **What they are not.** These are NOT a Phase-14 result. They are not the demo's recall",
        "> rate, they are not comparable to `results/phase14_recall_report.md`, and they say",
        "> nothing about whether the real persona was learned — they were measured on invented",
        "> facts the shipped adapter is never taught. Citing a number from this file as a",
        "> PersonaCore recall result would be a category error.",
        "",
        "## Pre-Registration (committed before this run)",
        "",
        f"Every literal below was committed in **`{derived['rule_sha']}`**",
        "(*feat(14-07): commit CALIBRATION_DECISION_RULE before any calibration number exists*),",
        "which strictly precedes every output of this run. **Git history order is the",
        "pre-registration proof** (D-09 condition 2) — re-derive it with:",
        "",
        "```",
        "git log -S 'CALIBRATION_DECISION_RULE = (' -- scripts/teach_persona.py",
        "```",
        "",
        "| Literal | Value | What it does |",
        "|---|---|---|",
        f"| `CAL_MARGIN_K` | {CAL_MARGIN_K} | Phase 12's noise-floor margin, reused BLIND and "
        "not re-chosen for Phase 14 |",
        f"| `THRESHOLD_DISCOUNT` | {THRESHOLD_DISCOUNT} | the fraction of the calibration ceiling "
        "the real threshold is set to — the calibration set is disjoint and disposable, so its "
        "rate is a CEILING estimate, not a target |",
        f"| `THRESHOLD_FLOOR` | {THRESHOLD_FLOOR} | below this the metric is indistinguishable "
        "from the closed-book control at 8 seeded samples |",
        f"| `SATURATION_DELTA` | {SATURATION_DELTA} | the per-family recall gain below which a "
        "taught family counts as saturated and MOVES to held-out |",
        f"| `HELDOUT_VARIANCE_TRIGGER` | {HELDOUT_VARIANCE_TRIGGER} | the held-out per-family std "
        "above which the real set needs MORE held-out families |",
        f"| `COLLAPSE_PPL_TRIGGER` | {COLLAPSE_PPL_TRIGGER} | the fractional masked dialogue-val "
        "PPL increase above which replay becomes MANDATORY |",
        f"| `REGISTER_WIN_MARGIN` | {REGISTER_WIN_MARGIN} | the absolute held-out margin by which "
        "first person must beat second person to count as a win |",
        "",
        f"(`RATIO_DECIMALS = {RATIO_DECIMALS}` is a boundary-arithmetic constant added in the same",
        "commit, not a fifth policy number: both trigger comparisons round the measured ratio to",
        "ten decimals first, so 'exactly on the boundary' means the decimal value rather than",
        "whichever double happens to bracket it.)",
        "",
        "## Arm Design",
        "",
        "| Arm | Fact set | Register | Replay ratio | Role |",
        "|---|---|---|---|---|",
        f"| `cal_first_person` | `CALIBRATION_FACTS` ({len(fs.CALIBRATION_FACTS)} facts) | "
        "first person (D-01) | 0.0 | **the baseline.** Supplies the thresholds, the allocation "
        "inputs, and the no-replay PPL pair |",
        f"| `cal_first_person_replay` | `CALIBRATION_FACTS` ({len(fs.CALIBRATION_FACTS)} facts) | "
        f"first person | {REPLAY_ARM_RATIO} | D-15's PAIRED comparison — the ONLY difference from "
        "the baseline arm is the PersonaChat replay slice |",
        f"| `cal_second_person` | `REGISTER_ARM_FACTS` ({len(fs.REGISTER_ARM_FACTS)} facts) | "
        "**second person** (`FAMILIES_SECOND_PERSON`) | 0.0 | D-21's register arm. Its facts are "
        "DISJOINT from both the real set and the calibration set |",
        "",
        "**The calibration facts are disposable as an EVIDENCE SOURCE, not exempt from the",
        "validity discipline** (D-09 condition 1). Both throwaway pools passed the SAME D-02/D-03",
        "pre-flight gate as the real set — `CALIBRATION_POOL` 10/10 and `REGISTER_ARM_POOL` 6/6,",
        "recorded in `results/phase14_factset_report.md` under commit",
        f"`{fs.FACTSET_GATE_SHA}`. That matters because a calibration set with GUESSABLE facts",
        "would produce an inflated ceiling, and every threshold derived from it would be a number",
        "the base could clear without having learned anything.",
        "",
        "Scoring is the same harness the real run uses: `phase14_recall.load_adapted_model`",
        "(`weights_only=True`, load-before-inject), 1 greedy draw plus",
        "`N_SEEDED_SAMPLES` seeded draws per question, scored by `contains_value`. Questions",
        "whose own frame names the fact value — `F4` (reversed direction), `F5` (verification)",
        "— are dropped by the same mechanical `contains_value(question, value)` filter the harness",
        "uses, because a question containing its own answer measures copying from context.",
        "",
        "Every arm is scored **adapter ON and adapter OFF** (`adapter_disabled`: same process,",
        "same weights, same prompts, same per-question seeds, only the 36 LoRA `enabled` flags",
        "flipped). The OFF pass is the closed-book baseline — without it a held-out rate is",
        "unjudgeable — and its taught half is the second term of the per-family GAIN below.",
        "",
        "## Measured Results",
        "",
    ]
    for arm in CAL_ARMS:
        lines += _arm_rows(arm, results[arm])

    lines += [
        "### Run provenance",
        "",
        "```",
        *provenance_lines,
        "```",
        "",
        "## Derivation 1 — Recall Thresholds (D-09)",
        "",
        "**Rule function:** `teach_persona.lock_thresholds(cal_taught_rate, cal_heldout_rate)`,",
        f"committed in `{derived['rule_sha']}`.",
        "",
        "| Input | Value | Source |",
        "|---|---|---|",
        f"| `cal_taught_rate` | {base['on_taught']['rate']:.4f} | `cal_first_person` taught, "
        "adapter ON |",
        f"| `cal_heldout_rate` | {base['on_heldout']['rate']:.4f} | `cal_first_person` held-out, "
        "adapter ON |",
        f"| `THRESHOLD_DISCOUNT` | {THRESHOLD_DISCOUNT} | pre-registered |",
        f"| `THRESHOLD_FLOOR` | {THRESHOLD_FLOOR} | pre-registered |",
        "",
        "| Output | Value | Bound by |",
        "|---|---|---|",
        f"| `TAUGHT_THRESHOLD` | **{taught_threshold}** | {taught_bound} |",
        f"| `HELDOUT_THRESHOLD` | **{heldout_threshold}** | {heldout_bound} |",
        "",
        "The rule was applied MECHANICALLY: each threshold is",
        "`max(THRESHOLD_FLOOR, round(rate * THRESHOLD_DISCOUNT, 4))`, evaluated by the committed",
        "function on the measured rates above. **No number here was chosen after seeing the",
        "results** — what was pre-registered is the PROCEDURE, because the number cannot exist",
        "before the run but the rule that produces it must, or the threshold is just a value",
        "picked to be cleared.",
        "",
        "## Derivation 2 — Family Allocation (D-14)",
        "",
        "**Rule function:** `teach_persona.lock_family_allocation(per_family_gain,",
        f"heldout_family_std, taught_ids, heldout_ids)`, committed in `{derived['rule_sha']}`.",
        "",
        "| Input | Value |",
        "|---|---|",
        f"| `per_family_gain` | {gain_map} |",
        f"| `heldout_family_std` | {base['heldout_family_std']:.4f} |",
        f"| `taught_ids` (before) | {sorted(fs.TAUGHT_FAMILY_IDS)} |",
        f"| `heldout_ids` (before) | {sorted(fs.HELDOUT_FAMILY_IDS)} |",
        f"| `SATURATION_DELTA` | {SATURATION_DELTA} (a gain of exactly this is NOT saturated) |",
        f"| `HELDOUT_VARIANCE_TRIGGER` | {HELDOUT_VARIANCE_TRIGGER} (a std of exactly this does "
        "NOT trigger) |",
        "",
        "| Output | Value |",
        "|---|---|",
        f"| `TAUGHT_FAMILY_IDS` | **{sorted(derived['taught_ids'])}** |",
        f"| `HELDOUT_FAMILY_IDS` | **{sorted(derived['heldout_ids'])}** |",
        f"| taught family count | {len(fs.TAUGHT_FAMILY_IDS)} → **{len(derived['taught_ids'])}** |",
        f"| saturation trigger | {derived['saturation_fired']} |",
        f"| variance trigger | {derived['variance_fired']} |",
        "",
        derived["unmeasured_note"],
        "",
        "**Driver output, verbatim** — this is the one place a refused move lands, and an",
        "unrecorded refusal is a silently altered allocation:",
        "",
        "```",
        derived["allocation_log"] or "(no candidate families — no move was attempted)",
        "```",
        "",
        "The four invariants the rule preserved:",
        "",
        f"1. **Disjoint, and the union is still every key of `FAMILIES`** (B-02): "
        f"`{sorted(derived['taught_ids'] & derived['heldout_ids'])}` is the intersection, and "
        f"the union is `{sorted(derived['taught_ids'] | derived['heldout_ids'])}` against "
        f"`FAMILIES` keys `{sorted(fs.FAMILIES)}`. The allocation MOVES families; it never drops "
        "one.",
        f"2. **`F4` stays taught** (D-22): `F4` "
        f"{'IS' if 'F4' in derived['taught_ids'] else 'IS NOT'} in the taught set. Reversed-"
        "direction forms hit the documented reversal curse, so held out they would fail for a "
        "LITERATURE reason rather than for any property of this model.",
        f"3. **At least two families per side**: {len(derived['taught_ids'])} taught, "
        f"{len(derived['heldout_ids'])} held-out.",
        "4. **Every locked fact's taught-instance count stays inside "
        f"`PARAPHRASES_PER_FACT_TARGET` = {fs.PARAPHRASES_PER_FACT_TARGET}** (W-03): "
        f"{derived['paraphrase_census']}.",
        "",
        derived["allocation_note"],
        "",
        "## Derivation 3 — PersonaChat Replay (D-15)",
        "",
        "**Rule function:** `teach_persona.replay_required(ppl_adapter_off, ppl_adapter_on)`,",
        f"committed in `{derived['rule_sha']}`.",
        "",
        "The instrument is the D-11.2 one exactly — `masked_perplexity` over",
        "`data/dialog_val.bin` + its mask, adapter ON and OFF in ONE process on ONE set of",
        "weights, so the only difference is the LoRA enabled flag. It is not a proxy.",
        "",
        "| Arm | PPL adapter OFF | PPL adapter ON | Fractional increase |",
        "|---|---|---|---|",
        f"| `cal_first_person` (no replay) | {base['ppl_adapter_off']:.4f} | "
        f"{base['ppl_adapter_on']:.4f} | **{base_delta:+.2%}** |",
        f"| `cal_first_person_replay` (replay {REPLAY_ARM_RATIO}) | "
        f"{replay['ppl_adapter_off']:.4f} | {replay['ppl_adapter_on']:.4f} | "
        f"{replay_delta:+.2%} |",
        "",
        "| Output | Value |",
        "|---|---|",
        f"| `replay_required` | **{derived['replay_required']}** |",
        f"| `COLLAPSE_PPL_TRIGGER` | {COLLAPSE_PPL_TRIGGER} (exactly at the trigger does NOT "
        "require replay — strict `>`) |",
        f"| `REAL_RUN_REPLAY_RATIO` | **{derived['real_replay_ratio']}** |",
        "",
        derived["replay_note"],
        "",
        "The paired arm is reported alongside because D-15 asks what replay BUYS, not only",
        "whether it is needed: the two arms differ in the replay slice and in nothing else, so",
        "the difference between their two ON/OFF deltas is attributable to replay alone.",
        "",
        "## Derivation 4 — Teaching Register (D-21)",
        "",
        "**Rule function:** `teach_persona.first_person_wins(fp_heldout_rate, sp_heldout_rate)`,",
        f"committed in `{derived['rule_sha']}`.",
        "",
        "| Input | Value | Source |",
        "|---|---|---|",
        f"| `fp_heldout_rate` | {base['on_heldout']['rate']:.4f} | `cal_first_person` held-out, "
        "adapter ON |",
        f"| `sp_heldout_rate` | {register['on_heldout']['rate']:.4f} | `cal_second_person` "
        "held-out, adapter ON |",
        f"| margin | {register_margin:+.4f} |",
        f"| `REGISTER_WIN_MARGIN` | {REGISTER_WIN_MARGIN} (exactly at the margin is NOT a win — "
        "strict `>`) |",
        "",
        "| Output | Value |",
        "|---|---|",
        f"| `first_person_wins` | **{derived['first_person_wins']}** |",
        "| `REAL_RUN_SECOND_PERSON` | **False** |",
        "",
        "**Both kinds of evidence, per D-21 condition 4.** The register lock in D-01 was made on",
        "QUALITATIVE evidence and it stands on that evidence: 14-RESEARCH F3/F5 measured the",
        "frozen conversational base copying the *structure* of a second-person prompt while",
        "getting the *content* wrong. The recorded probe answered",
        # One line, deliberately: the quoted probe is the citation D-21 condition 4 requires, and
        # wrapping it across two list entries puts a newline inside the quote so nothing can grep
        # for it. Prose wraps; evidence does not.
        "`i have a dog named my name is cuddling`, which is a syntactically well-formed",
        "first-person self-description with the wrong noun phrase spliced in.",
        "That finding is what motivated teaching answers as",
        "first-person self-description in the first place, and no number in this report replaces",
        "it. What D-01 was MISSING was a measured head-to-head between the two registers, and",
        "that is exactly and only what this arm supplies:",
        f"first person {base['on_heldout']['rate']:.4f} vs second person",
        f"{register['on_heldout']['rate']:.4f} on held-out recall, a margin of",
        f"{register_margin:+.4f} against a pre-registered win margin of {REGISTER_WIN_MARGIN}.",
        "",
        derived["register_note"],
        "",
        "**Caveat a reader should carry:** the two arms are scored on DIFFERENT fact sets"
        f" ({len(fs.CALIBRATION_FACTS)} calibration facts vs {len(fs.REGISTER_ARM_FACTS)} "
        "register-arm facts), because D-21 requires the register arm's facts to be disjoint from"
        " both the real and the calibration sets. The comparison is therefore between two"
        " register treatments over comparable-but-not-identical material, which is the strongest"
        " head-to-head the disjointness requirement allows.",
        "",
        "## Verdict",
        "",
        "PENDING — user decision at checkpoint.",
        "",
    ]
    CALIBRATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[teach_persona] wrote {CALIBRATION_REPORT}")


def _paraphrase_census(taught_ids):
    """Per-fact taught-paraphrase counts under an allocation — W-03's invariant, as evidence."""
    counts = {
        fact.id: sum(len(fs.render_family(fid, fact)) for fid in taught_ids)
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    }
    lo, hi = fs.PARAPHRASES_PER_FACT_TARGET
    distinct = sorted(set(counts.values()))
    inside = all(lo <= c <= hi for c in counts.values())
    return (
        f"every one of the {len(counts)} locked+soft facts carries {distinct} taught "
        f"paraphrases, {'inside' if inside else '**OUTSIDE**'} the band"
    )


def run_calibration(argv=()):
    """Run the three calibration arms, apply the four rules, write the report. Plan 14-09."""
    _refuse_clobber(CALIBRATION_REPORT, "--force" in argv)
    started = time.time()
    summary = preflight_device(strict=True)
    device = RuntimeConfig().device
    print(f"[teach_persona] calibration preflight: {summary} device={device}")

    results = {}
    for arm in CAL_ARMS:
        arm_started = time.time()
        facts, second_person, replay_ratio = arm_spec(arm)
        record = train_arm(
            arm,
            facts=facts,
            family_ids=fs.TAUGHT_FAMILY_IDS,
            second_person=second_person,
            replay_ratio=replay_ratio,
        )
        record.update(score_arm(arm, facts, record["paths"]["adapter"], device))
        record["adapter_sha256"] = _sha256(record["paths"]["adapter"])
        record["wall_clock"] = time.time() - arm_started
        results[arm] = record

    derived = derive_all(results)
    provenance_lines = [
        f"seed: {SEED}",
        f"driver git_sha: {git_sha()}",
        f"pid: {os.getpid()}",
        f"wall clock (UTC): {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"total wall: {time.time() - started:.0f}s",
        f"preflight: {summary}",
        f"device: {device}  torch: {torch.__version__}",
        f"lr={LR} weight_decay={WEIGHT_DECAY} batch_size={BATCH_SIZE} max_steps={MAX_STEPS} "
        f"warmup_steps={WARMUP_STEPS} block_size={BLOCK_SIZE}",
        f"decision-rule commit: {derived['rule_sha']}",
        f"FACTSET_GATE_SHA: {fs.FACTSET_GATE_SHA}",
    ]
    for arm in CAL_ARMS:
        paths = results[arm]["paths"]
        provenance_lines += [
            f"{arm}: adapter={paths['adapter'].name} sha256={results[arm]['adapter_sha256']}",
            f"{arm}: csv={paths['csv'].relative_to(_REPO_ROOT)} "
            f"wall={results[arm]['wall_clock']:.0f}s",
        ]

    dump_results(results, provenance_lines)
    write_calibration_report(results, derived, provenance_lines)
    print(
        f"[teach_persona] calibration derivations: thresholds={derived['thresholds']} "
        f"taught={sorted(derived['taught_ids'])} heldout={sorted(derived['heldout_ids'])} "
        f"replay_required={derived['replay_required']} "
        f"first_person_wins={derived['first_person_wins']}"
    )
    return results, derived


def derive_all(results):
    """Apply the four ``CALIBRATION_DECISION_RULE`` functions to the measured arm records.

    A PURE function of the measurements: given the same three arm records it returns the same
    four derivations, with no model, no device, and no file access beyond the git-log lookup that
    records which commit the rule came from. That is what makes the derivations auditable — a
    reader can re-run this on the numbers printed in the report and get the same outputs, and
    ``tests/test_phase14_scoring.py`` exercises it on fabricated records without a GPU.

    The BASELINE arm (``cal_first_person``) supplies every input except the register comparison:
    it is the arm whose configuration the real run mirrors, so its rates are the ceiling the
    thresholds discount, its per-family gains are the allocation input, and its ON/OFF PPL pair
    is the collapse measurement. The replay arm is the PAIRED comparison and the second-person
    arm supplies only the register head-to-head.
    """
    base = results["cal_first_person"]
    register = results["cal_second_person"]

    thresholds = lock_thresholds(base["on_taught"]["rate"], base["on_heldout"]["rate"])

    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        taught_ids, heldout_ids = lock_family_allocation(
            base["per_family_gain"],
            base["heldout_family_std"],
            fs.TAUGHT_FAMILY_IDS,
            fs.HELDOUT_FAMILY_IDS,
        )
    allocation_log = captured.getvalue().strip()
    print(allocation_log or "[teach_persona] allocation: no candidate families")

    needs_replay = replay_required(base["ppl_adapter_off"], base["ppl_adapter_on"])
    fp_wins = first_person_wins(base["on_heldout"]["rate"], register["on_heldout"]["rate"])

    saturated = sorted(fid for fid, g in base["per_family_gain"].items() if g < SATURATION_DELTA)
    moved = sorted(set(fs.TAUGHT_FAMILY_IDS) - taught_ids)
    # Taught families with NO measured gain: every one of their questions names its own answer,
    # so the self-naming filter removed all of them from scoring. `lock_family_allocation` reads
    # a missing key as 0.0 and therefore proposes moving them — the invariants then refuse. The
    # report must say this out loud, because "gain 0.0" here is an ABSENCE OF MEASUREMENT and not
    # a measurement of zero, and a reader who misses the distinction concludes the reversed-
    # direction and verification families taught nothing.
    unmeasured = sorted(set(fs.TAUGHT_FAMILY_IDS) - set(base["per_family_gain"]))
    replay = results["cal_first_person_replay"]
    replay_delta = (replay["ppl_adapter_on"] - replay["ppl_adapter_off"]) / replay[
        "ppl_adapter_off"
    ]
    base_delta = (base["ppl_adapter_on"] - base["ppl_adapter_off"]) / base["ppl_adapter_off"]
    replay_still_trips = round(replay_delta, RATIO_DECIMALS) > COLLAPSE_PPL_TRIGGER
    recall_cost = base["on_taught"]["rate"] - replay["on_taught"]["rate"]
    return {
        "rule_sha": rule_commit_sha(),
        "thresholds": thresholds,
        "taught_floor_bound": thresholds[0] == THRESHOLD_FLOOR,
        "heldout_floor_bound": thresholds[1] == THRESHOLD_FLOOR,
        "taught_ids": taught_ids,
        "heldout_ids": heldout_ids,
        "allocation_log": allocation_log,
        "saturation_fired": (
            f"FIRED for {saturated} (gain < {SATURATION_DELTA})" if saturated else "did not fire"
        ),
        "variance_fired": (
            f"FIRED (std {base['heldout_family_std']:.4f} > {HELDOUT_VARIANCE_TRIGGER})"
            if base["heldout_family_std"] > HELDOUT_VARIANCE_TRIGGER
            else f"did not fire (std {base['heldout_family_std']:.4f} <= "
            f"{HELDOUT_VARIANCE_TRIGGER})"
        ),
        "allocation_note": (
            f"**The allocation changed:** {moved} moved from taught to held-out."
            if moved
            else (
                "**The allocation is UNCHANGED, and that is a result rather than a no-op.** "
                "Every candidate move the rule proposed was REFUSED by invariant 4: at the "
                "committed allocation each locked fact carries 22 taught paraphrases against a "
                f"{fs.PARAPHRASES_PER_FACT_TARGET} band, and the smallest taught family carries "
                "4 instances, so any move drops some fact to 17 or 18 — below the floor. The "
                "refusal is the invariant doing its job: a saturation-driven move would trip "
                "`build_bins` proof #5 and `SystemExit` the real run. If calibration genuinely "
                "demands more held-out families, the remedy is to ADD paraphrase instances "
                "(a fact-set change), not to relax a pre-registered threshold."
            )
        ),
        "unmeasured_note": (
            (
                f"**{unmeasured} carry NO measured gain, and that is an absence of measurement "
                "rather than a measurement of zero.** Every question those families generate "
                "names its own fact value inside the question — `F4` is the D-22 reversed "
                "direction (`who is varek?`) and `F5` is yes/no verification (`is your name "
                "varek?`) — so the same mechanical `contains_value` filter the scored harness "
                "uses removed all of them before scoring. They were TAUGHT in full; they are "
                "simply not SCORABLE, because a question containing its own answer measures "
                "copying from context. `lock_family_allocation` reads a missing key as `0.0` and "
                "therefore proposed moving them, which is why they appear in the refusal log "
                "below. Do NOT read that as evidence that reversed-direction or verification "
                "teaching failed — this run says nothing either way about those two families."
            )
            if unmeasured
            else "Every taught family had scorable questions; no family's gain is unmeasured."
        ),
        "paraphrase_census": _paraphrase_census(taught_ids),
        "replay_required": needs_replay,
        "real_replay_ratio": REPLAY_ARM_RATIO if needs_replay else 0.0,
        "replay_note": (
            (
                "**Replay IS required.** The no-replay arm's masked dialogue-val PPL rose past "
                f"`COLLAPSE_PPL_TRIGGER` = {COLLAPSE_PPL_TRIGGER}, so the real run mixes "
                f"PersonaChat replay at ratio {REPLAY_ARM_RATIO} into its teaching bin.\n\n"
                "**What the paired arm shows replay actually BUYS, and what it costs.** Replay "
                f"at ratio {REPLAY_ARM_RATIO} moves the collapse from "
                f"{base_delta:+.2%} to {replay_delta:+.2%} — a large mitigation — while taught "
                f"recall falls from {base['on_taught']['rate']:.4f} to "
                f"{replay['on_taught']['rate']:.4f}, a fall of {recall_cost:.4f}. "
                + (
                    "**The replay arm ITSELF still trips the trigger.** Replay at this ratio "
                    "reduces the collateral collapse but does not eliminate it, so 'replay "
                    "required' should not be read as 'replay solves it'. Whether the remaining "
                    f"{replay_delta:+.2%} is acceptable, and whether a different ratio or a "
                    "shorter teaching run is the better lever, is a judgment for the checkpoint "
                    "— this run measured the tradeoff, it did not resolve it."
                    if replay_still_trips
                    else "The replay arm clears the trigger, so the mitigation is sufficient at "
                    "this ratio."
                )
            )
            if needs_replay
            else (
                "**Replay is NOT required, so the real run proceeds WITHOUT it.** That is the "
                "consequence stated plainly: the teaching signal stays undiluted rather than "
                "being halved against a risk this run measured and did not find. Mixing replay "
                "in anyway would cost teaching tokens to buy protection from a collapse the "
                "instrument says is not happening."
            )
        ),
        "first_person_wins": fp_wins,
        "register_note": (
            "**The first-person register wins the head-to-head**, by more than the "
            f"pre-registered `REGISTER_WIN_MARGIN` = {REGISTER_WIN_MARGIN}. The quantitative "
            "result agrees with the qualitative evidence D-01 was made on, and the real run "
            "teaches first-person answers."
            if fp_wins
            else (
                "**The first-person register did NOT clear the pre-registered margin, and that "
                "negative is recorded here unamended** (D-12). It does NOT reopen D-01 "
                "mid-phase. D-01's register lock rests on the qualitative evidence above, which "
                "this arm was designed to SUPPLEMENT with a measured head-to-head, not to "
                "replace; re-authoring the teaching set after seeing a number is the exact move "
                "the whole pre-registration block exists to prevent. `REAL_RUN_SECOND_PERSON` "
                "stays `False`."
            )
        ),
    }


if __name__ == "__main__":
    main()
