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

import math
import os
import pathlib
import re
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


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in ARMS:
        raise SystemExit(f"usage: python scripts/teach_persona.py {{{'|'.join(ARMS)}}}")
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


if __name__ == "__main__":
    main()
