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
import random
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
from _verdict import recorded_verdict  # noqa: E402  (sibling script; scripts/ is sys.path[0])

from personacore.checkpoint import export_adapter  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig, TrainConfig  # noqa: E402
from personacore.dialogue import build_recall_prompt, encode_dialogue  # noqa: E402
from personacore.evaluation import masked_perplexity  # noqa: E402
from personacore.generation import undecodable_ids_mask  # noqa: E402
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
from personacore.privacy.dpsgd import DPSGD  # noqa: E402  (D-08 wiring 4)
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
from personacore.training import train  # noqa: E402
from personacore.training.data import (  # noqa: E402
    fact_window_impurities,
    get_batch_memmap_masked,
)

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

# ===== Phase 21 / UNIT-04: the v4.0 replay volume, a function of PUBLIC quantities ONLY =====
#
# D-11: replay VOLUME must depend only on PUBLIC quantities, never on
# ``round(replay_ratio * teaching_tokens)``. ``teaching_tokens`` is the sum of the FACTS' OWN
# token lengths (measured 7,581 over 8 facts, 867-1,041 per fact, a 174-token spread), so the
# v3.0 sizing makes the volume of "public" data in the lot a function of PRIVATE content. That
# breaks the un-clipped public-gradient argument: the public term stops being independent of the
# private records.
#
# D-24 — the constant is 4 WINDOWS PER FACT = 1,024 tokens, window-quantized, never a raw token
# count. Measured against D-01's geometry (every row travels with its denominator):
#
#   | constant  | tok/fact | integral windows? | share of the padded bin | vs today's 50.00% |
#   |-----------|----------|-------------------|-------------------------|-------------------|
#   | 3 windows |      768 | yes               |                  42.11% |            -7.9pt |
#   | 4 windows |    1,024 | yes               |                  49.23% |           -0.77pt |
#   | 5 windows |    1,280 | yes               |                  54.79% |            +4.8pt |
#   | raw ~=948 |  947.625 | NO -- 3.7017      |                  50.00% |                 0 |
#
# Two findings killed the raw row, and the second is the load-bearing one. FIRST:
# ``get_batch_memmap_masked`` draws whole ``block_size`` windows only, so a raw-token constant
# needs a truncation step inside the very path D-10 chose BECAUSE it was already proven. SECOND
# and worse: 947.625 IS 7581 / 8 -- read off the private token lengths. A constant that is
# "public" because it is published, but whose VALUE was read off private data, is the same
# property-not-name defect one level up, at design time. It is refused BY TEST
# (``tests/test_phase21_replay_volume.py::test_replay_constant_is_not_derived_from_the_corpus``),
# not merely by preference.
#
# RETRACTED 2026-08-25 (Phase 21, WR-03). This comment read: "The share holds across capacities
# for free: 49.90% at n=64, because both sides scale with ``n_facts``. Nothing re-tunes." It does
# not hold. MEASURED at n=64: 44.7552% (``results/phase21_multiplicity.json``, recorded under
# ``documented_n64_claim_holds: false``).
#
# D-24's constant is UNTOUCHED and still measures exactly right: 4 windows = 1,024 tok/fact =
# 49.23% of the padded bin at n=8. What was falsified is the CONSEQUENCE. Replay scales exactly
# with ``n_facts``; the TEACHING BIN does not. The 56 filler facts pack to 283 of the 316 ragged
# windows (5.054 each) against the 8 locked facts' 33 (4.125 each), so the n=64 bin carries
# 80,896 trainable tokens where linear scaling from n=8 predicts 8 x 8,448 = 67,584.
#
# Sharper, and the reason this is a retraction rather than a re-measurement: under the linear
# premise the old comment ITSELF stated, the share would be 49.2308% -- exactly the n=8 value --
# not the 49.90% it claimed. The figure never followed from its own stated reason either.
# Re-tuning IS required across capacities.
REPLAY_WINDOWS_PER_FACT = 4


def replay_window_budget(n_facts, block_size=BLOCK_SIZE):
    """The v4.0 replay volume in tokens — THE ONLY SITE that computes it (D-11 / D-24).

    ``REPLAY_WINDOWS_PER_FACT * n_facts * block_size``. Every consumer calls this function:
    :func:`_prepend_replay`'s ``n_facts`` branch, ``train()``'s replay seam via :func:`train_arm`,
    the plan-21-11 driver, and every test. RESEARCH Open Question 3 asks which site the
    differential should target; the answer is that there is exactly one, and its callers are named.

    **IN-04, closed by plan 22-10 — in BOTH directions.** Until that plan this docstring claimed
    *"``train()``'s replay seam via its caller"* and the claim was FALSE: measured, no call site
    anywhere passed ``replay_bin`` / ``replay_mask_bin`` / ``replay_windows`` into ``train()``, so
    the named consumer did not exist. Plan 22-10 wires it at :func:`train_arm` on the two DP arms
    (D-08 wiring 3), which makes the sentence true, and the sentence is rewritten in the SAME diff
    to name the real caller rather than left as a claim that happened to become correct. **The
    unit conversion is the thing to get right at that call site:** this function returns TOKENS
    and ``train(replay_windows=)`` wants WINDOWS, so the caller divides by ``block_size``.

    **Every factor is PUBLIC, and each by DERIVATION rather than by publication:**

    * ``REPLAY_WINDOWS_PER_FACT = 4`` — chosen from the D-24 table above over the 3- and
      5-window candidates. All three are small integers authored before any fact exists; none
      was read off the corpus. The one candidate that WAS read off the corpus (947.625 = 7581/8)
      is refused, and refused by test.
    * ``n_facts`` — a COUNT of records, not a function of their content. D-11 names it public,
      and SC2 pre-registers ``grad_accum_steps = n_facts`` publicly at both capacities.
    * ``block_size`` — ``ModelConfig.block_size``, a model hyperparameter fixed before the fact
      set existed.

    So no private quantity appears on the right-hand side. That is the whole point of D-11, and
    it is proven by a DIFFERENTIAL (vary the fact values at fixed ``n_facts``, observe the volume
    unchanged) rather than by a constant assertion, which would pass on the defective
    implementation whenever the corpus happened to land on the same number.
    """
    return REPLAY_WINDOWS_PER_FACT * int(n_facts) * int(block_size)


# ===== The two REAL-ARM settings derived by plan 14-09's calibration run =====
#
# D-15 verdict, from ``replay_required(4.5737, 14.8559)`` -> **True**. Training the persona with
# NO replay raised masked dialogue-val PPL by +224.81% (adapter OFF 4.5737 / ON 14.8559 over
# 270,203 scored targets), far past ``COLLAPSE_PPL_TRIGGER`` = 0.10. The real run therefore mixes
# PersonaChat replay into its teaching bin at ``REPLAY_ARM_RATIO``, the ratio the paired arm
# measured. Evidence: ``results/phase14_calibration_report.md``, ``## Derivation 3``.
#
# What the paired arm also measured, stated here because it bounds what this number buys: replay
# at 1.0 moved the collapse to +29.39%, which is a large mitigation but STILL trips the trigger,
# and it cost taught recall 0.6825 -> 0.4143. "Replay required" is not "replay solves it".
#
# WR-01 — PROVENANCE OF THE FOUR PPL FIGURES ABOVE. They were measured by ``train_arm`` as
# originally committed, which called ``masked_perplexity`` WITHOUT ``forbid_ids`` while
# ``phase14_recall.run_collapse_control`` passed it — so the two were described as one instrument
# and were not. The call below is now aligned to the frozen policy, but these constants record
# what was measured, not what the aligned instrument would produce. Re-measured from the saved
# adapters under both settings: +224.8084% -> +224.5330% (no replay) and +29.3914% -> +29.3364%
# (replay 1.0). ``replay_required`` returns True on every one of those four numbers, so the
# derivation this block encodes is unchanged and is NOT being re-derived after the fact.
REAL_RUN_REPLAY_RATIO = REPLAY_ARM_RATIO

# D-21 verdict, from ``first_person_wins(0.5519, 0.8045)`` -> **False**. First person did NOT
# clear ``REGISTER_WIN_MARGIN`` = 0.10; second person measured HIGHER on held-out recall (0.8045
# vs 0.5519, a margin of -0.2526). That negative is recorded unamended (D-12) and it does NOT
# reopen D-01 mid-phase: D-01's register lock rests on the qualitative 14-RESEARCH F3/F5 evidence
# (the base answering `i have a dog named my name is cuddling` — structure copied, content not),
# and this arm was designed to SUPPLEMENT that with the head-to-head D-01 was missing, not to
# replace it. Re-authoring the teaching register after seeing a number is the exact move the
# pre-registration block exists to prevent, so the real run stays first person.
REAL_RUN_SECOND_PERSON = False

ARMS = (
    "cal_first_person",
    "cal_first_person_replay",
    "cal_second_person",
    "real",
    # v4.0's two DP capacities (UNIT-06). NEW ARM NAMES rather than an `arm_spec(..., n_facts=)`
    # axis, because `arm_outputs` already scopes `bin`, `mask`, `csv`, `checkpoint` and `adapter`
    # by arm NAME: two names get disjoint paths and `refuse_if_exists` protection for free, while
    # an `n_facts` axis `arm_outputs` knows nothing about would collide with the `real` arm's
    # RECORDED bins.
    "dp_n8",
    "dp_n64",
    # Phase 24's two adversarial capacities (ADVT-01). DELIBERATELY NOT in `DP_ARMS`:
    # `aligned = arm in DP_ARMS` in `build_arm_bins` is membership in a literal closed 2-tuple
    # with NO prefix matching, so any other name packs FLAT — which is correct here. The
    # adversarial arm makes no formal privacy claim (Phase 25 SC4 pins `accounting: null` on it)
    # and a fact-INDEPENDENT refusal episode has no fact shard, so it has no home in the ragged
    # fact-aligned layout. That closes 24-CONTEXT's declared residue 2 on the mechanism rather
    # than by inference.
    #
    # NO CLI FLAG carries `adversarial_ratio`, so `main()` REFUSES both arms outright — see
    # `ADV_ARMS` below. Phase 25's sweep driver calls `train_arm` PROGRAMMATICALLY, exactly as
    # `scripts/phase17_isolation.py`, `scripts/phase19_run.py` and `scripts/phase19_erasure.py`
    # already do — a grid sweep is not something an operator types one ratio at a time.
    #
    # CORRECTED 2026-08-30 (24-REVIEW CR-01). This comment read: "that is a choice rather than an
    # omission: `main()`'s non-DP path still enforces `len(argv) != 1`". The defense was FALSE.
    # `len(argv) != 1` rejects EXTRA tokens (`adv_n8 0.5`); it never rejected the bare arm, which
    # is the only form an operator would type. Measured: `python scripts/teach_persona.py adv_n8`
    # ran a full 200-step training run and wrote `data/phase14_adv_n8*.bin`, a checkpoint and
    # `phase14_adv_n8_adapter.pt` — every one named "adversarial", every one holding ZERO
    # adversarial episodes over a corpus byte-identical to the `real` arm's, with the ratio
    # recorded nowhere. The choice is real; the enforcement was missing, and is now below.
    "adv_n8",
    "adv_n64",
)

# The subset of ``ARMS`` that packs the RAGGED FACT-ALIGNED three-bin path instead of the flat
# v3.0 pack. **The arm NAME is what couples an arm to its packer** — `build_arm_bins` reads this
# tuple and nothing else, so an arm called `dp_*` cannot end up building the un-indicted flat bin
# UNIT-01 exists to replace. Before this coupling existed, `python scripts/teach_persona.py dp_n8`
# ran to completion writing two bins and an adapter, and a consumer pointing
# `get_batch_fact_aligned` at the result failed only much later with "the fact bin
# data/persona_dp_n8_train_fact.bin could not be opened".
DP_ARMS = ("dp_n8", "dp_n64")

# The subset of ``ARMS`` whose DEFINING parameter cannot be expressed on this CLI (24-REVIEW
# CR-01). ``DP_ARMS``' name coupling on the other axis: there the arm NAME picks the PACKER, here
# it makes `main()` refuse rather than silently train the ratio-0.0 control under an
# "adversarial" name. Same lesson, same mechanism — an arm whose defining input has no way in is
# refused BY NAME, not left to a check that happens to be nearby.
#
# The refusal lives HERE and deliberately NOT on ``train_arm``, which is the opposite of where
# the DP arms' ``Z boundary`` refusal lives. The two are not inconsistent: no sigma is NEVER a
# valid DP run, but ``adversarial_ratio=0.0`` IS a pre-registered grid point — it is
# ``mitigation_budget.ADVERSARIAL_RATIO_GRID[0]``, the sweep's own control — so a mechanism-level
# refusal would refuse the control arm the record is built from
# (``scripts/phase24_record.py`` calls ``build_bins`` at exactly that ratio). What has no
# legitimate caller is a ratio that was never CHOSEN, and the CLI is the only entry point that
# cannot express one.
ADV_ARMS = ("adv_n8", "adv_n64")


def _require_go_verdict(report_path):
    """D-06 gate: hard-exit unless the report's ``## Verdict`` section reads GO or ADAPT.

    Every abort NAMES ``report_path``. It takes a path, so it is not a Phase 14 gate any more —
    Phase 17's ISO-01 gate calls it with ``results/phase17_personas_report.md``, and the two
    branches below that used to say only "the fact-set report" would send that operator to
    ``results/phase14_factset_report.md``: the wrong file, and one that already carries a recorded
    GO. An abort at a blocking gate has to name the artifact it is blocking on.
    """
    if not report_path.exists():
        raise SystemExit(
            f"[teach_persona] {report_path} missing — run "
            "`python scripts/phase14_factset_gate.py` and record the D-06 verdict first."
        )
    text = report_path.read_text(encoding="utf-8")
    section = re.search(r"^## Verdict\b(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if section is None:
        raise SystemExit(
            f"[teach_persona] no '## Verdict' section in {report_path} — the D-06 verdict "
            "must be recorded before any teaching bin is built."
        )
    word = re.search(r"[A-Za-z]+", section.group(1))
    verdict = word.group(0).upper() if word else "PENDING"
    if verdict not in ("GO", "ADAPT"):
        raise SystemExit(
            f"[teach_persona] recorded verdict in {report_path} is {verdict!r} — teaching bins "
            "may only be built on GO/ADAPT (D-06). STOP/PENDING must be escalated, not bypassed."
        )
    return verdict


def arm_outputs(arm, *, prefix="phase14"):
    """Name-scoped write targets for one arm — no two arms ever share a path.

    ONE deliberate exception to the ``{prefix}_{arm}`` naming: the ``real`` arm's adapter is
    ``checkpoints/persona_adapter.pt``, not ``phase14_real_adapter.pt``. That is the SHIPPABLE
    persona file, and both downstream consumers already hardcode that name —
    ``scripts/phase14_recall.py``'s ``ADAPTER_PATH`` (plan 14-06) and the Gradio demo (plan
    14-08). The calibration arms keep their scoped names because they are disposable evidence,
    never shipped. Disjointness across every arm pair is preserved and CI-tested.

    ``prefix`` (Phase 17, D-14) scopes the three paths that carry the phase label today —
    ``adapter``, ``csv`` and ``checkpoint`` — so a Phase-17 run's artifacts say which phase
    produced them instead of claiming Phase 14's. It defaults to ``"phase14"``, so every
    existing caller resolves to byte-identical paths.

    Two deliberate non-widenings:

    * ``bin`` and ``mask`` carry NO phase prefix today (``data/persona_{arm}_train.bin``).
      Inventing one would MOVE an existing path, which is the opposite of additive; the arm
      name already scopes them and Phase 17's arm names are its own.
    * the ``real`` exception is UNCONDITIONAL on ``prefix``. It is the shippable path two
      consumers hardcode and ``test_real_arm_adapter_is_the_shippable_path`` pins; Phase 17
      never passes ``real``, so a prefix-aware exception would be dead code that weakened a
      cross-plan contract to serve a caller that does not exist.
    """
    adapter = (
        _REPO_ROOT / "checkpoints" / "persona_adapter.pt"
        if arm == "real"
        else _REPO_ROOT / "checkpoints" / f"{prefix}_{arm}_adapter.pt"
    )
    return {
        "bin": _REPO_ROOT / "data" / f"persona_{arm}_train.bin",
        "mask": _REPO_ROOT / "data" / f"persona_{arm}_train_mask.bin",
        "csv": _REPO_ROOT / "results" / f"{prefix}_{arm}" / "run.csv",
        "checkpoint": _REPO_ROOT / "checkpoints" / f"{prefix}_{arm}_latest.pt",
        "adapter": adapter,
    }


def fact_bin_path(bin_path):
    """The THIRD aligned bin's path, DERIVED — never a string literal at a call site.

    ``data/persona_real_train.bin`` -> ``data/persona_real_train_fact.bin``. Every consumer —
    the loader in plan 21-06, the drivers in 21-10/21-11, and every test — resolves the fact
    bin from HERE. This repository has shipped plans naming paths the code refuses; a single
    derivation function is the cheapest fix.
    """
    bin_path = pathlib.Path(bin_path)
    return bin_path.with_name(bin_path.stem + "_fact" + bin_path.suffix)


def arm_bin_targets(arm, outputs):
    """The bin paths one arm WRITES — THREE for a DP arm, two for a flat one.

    The fact bin is recorded evidence exactly like the other two, so ``refuse_if_exists`` has to
    know about it: a refusal that lists two of the three written files tells the operator to
    delete two and leaves the third silently in place. One derivation for both call sites (the
    ``build_arm_bins`` guard and the five-target guard in ``train_arm``) because two copies of a
    guard drift — the same reason ``_prove_floor_and_band`` is one function.
    """
    paths = [outputs["bin"], outputs["mask"]]
    if arm in DP_ARMS:
        paths.append(fact_bin_path(outputs["bin"]))
    return paths


def refuse_if_exists(paths, *, expected=()):
    """Refuse-to-rerun: an arm's outputs are RECORDED evidence once written — a rerun on
    drifted code or a drifted fact set would silently replace them. Fail loud, name the file.

    ``expected`` (D-07, plan 23-07) is the RESUME inversion, and it is a WIDENING OF THIS HELPER
    rather than a branch at either call site. Semantics:

    * every path in ``paths`` is refused if it EXISTS (unchanged, and ``expected=()`` is the
      default, so all four pre-existing callers — ``build_arm_bins``, ``train_arm``,
      ``phase21_golden_capture``, ``phase21_unit_record`` — are byte-identical to before);
    * every path in ``expected`` is refused if it is ABSENT, naming the missing file and saying
      that a resume requires it.

    A resume does not BYPASS the refusal, it INVERTS it per target. On a resume the checkpoint IS
    the resume source, the csv MUST be appended to (``CSVLogger`` is restart-safe and ``train()``
    derives cumulative tokens from the ABSOLUTE step precisely so the logged curve is continuous
    across a kill — ``training/loop.py``'s ``tokens_per_step`` comment), and the bins must be the
    SAME corpus the killed half trained on. Only the adapter keeps the refuse-if-present sense:
    the export is the LAST thing ``train_arm`` does, so an adapter on disk means the arm completed.

    Widened here rather than branched at the call site for the reason ``arm_bin_targets``'
    docstring already gives — two copies of a guard drift, and BOTH callers of ``arm_bin_targets``
    have to invert together or a resume is refused by whichever one did not.
    """
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[teach_persona] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )
    for want in expected:
        if not want.exists():
            raise SystemExit(
                f"[teach_persona] {want} is MISSING and a resume requires it. A resume continues "
                "a recorded run: the checkpoint is the resume source, the csv is appended to so "
                "the logged curve stays continuous across the kill, and the bins must be the same "
                "corpus the killed half trained on. Re-creating any of them would make the "
                "resumed run a different run wearing the same paths. Resume from the run that "
                f"wrote {want}, or start a fresh arm under a different prefix."
            )


def _slot_forms_for(facts):
    """``None`` for a purely published-slot corpus; the WIDENED union when filler is present.

    ``arm_spec('dp_n64')`` returns 8 locked facts + 56 filler facts, and the filler slots are
    DELIBERATELY disjoint from the 11 published ones (D-13/D-16). ``render_family``'s default
    grammar is ``fs.SLOT_FORMS``, which does not define them — so without this the n=64 capacity
    is not reachable at all: it raises ``KeyError: 'filler_boat_name'`` on the FIRST filler fact.
    Measured, not reasoned about: ``arm_spec`` alone makes n=64 *declarable*, not *buildable*.

    Returning ``None`` for every existing arm is the point. ``render_family`` then runs the two
    lines it always ran (its own docstring: "the default is not merely EQUAL to the v2.0 output —
    it is the same code path"), so ``tests/fixtures/golden_render_family_v2.json`` and every
    recorded arm's bins are untouched by this function's existence.

    Both guards below are correctness requirements at the same trust boundary the ``== 10`` wall
    protects one level down. A ``{**published, **filler}`` union silently PREFERS the filler
    mapping on a key collision, which would let a filler grammar quietly replace a published slot's
    rendering; and an undeclared slot would otherwise surface as a bare ``KeyError`` from inside
    ``_render_family`` naming no fact and no path.
    """
    if all(fact.slot in fs.SLOT_FORMS for fact in facts):
        return None

    import phase21_filler  # lazy, for the same reason `arm_spec`'s is — see its docstring

    clash = sorted(set(fs.SLOT_FORMS) & set(phase21_filler.FILLER_SLOT_FORMS))
    if clash:
        raise SystemExit(
            f"[teach_persona] filler slots {clash} collide with the PUBLISHED slot grammar. The "
            "union below prefers the filler mapping, so a collision would silently replace a "
            "published slot's rendering. D-13 requires the two slot sets to be disjoint."
        )
    widened = {**fs.SLOT_FORMS, **phase21_filler.FILLER_SLOT_FORMS}
    undeclared = sorted({fact.slot for fact in facts} - set(widened))
    if undeclared:
        raise SystemExit(
            f"[teach_persona] no slot grammar defines {undeclared} — neither "
            "phase14_factset.SLOT_FORMS nor phase21_filler.FILLER_SLOT_FORMS. Rendering would "
            "raise a bare KeyError from inside _render_family, naming no fact and no arm."
        )
    return widened


def render_episodes(facts, family_ids, *, second_person=False):
    """The facts x families x instances cross product, as ``(question, answer)`` pairs."""
    episodes = []
    forms = _slot_forms_for(facts)
    for fact in facts:
        for family_id in sorted(family_ids):
            episodes.extend(
                fs.render_family(family_id, fact, second_person=second_person, forms=forms)
            )
    return episodes


def build_bins(
    tok,
    episodes,
    bin_path,
    mask_path,
    *,
    replay_ratio=0.0,
    align_facts=None,
    adversarial_ratio=0.0,
    seed=SEED,
):
    """Encode every episode into an aligned token/mask bin pair; return the measured stats.

    Every episode goes through ``encode_dialogue`` with an EMPTY persona — the bare
    ``<|system|>`` clean-room shape — so the D-07 persona cap is a structural no-op here and is
    deliberately never applied. Ids are ``uint16``, mask is ``uint8``, written with the
    ``prepare_dialog_corpus.py`` shard-and-write idiom.

    ``align_facts`` (Phase 21, UNIT-02) selects the RAGGED FACT-ALIGNED path — a third
    ``*_fact.bin`` and one privacy record per fact. **When it is ``None`` this function is
    BYTE-IDENTICAL to v2.0**, which is asserted against ``tests/fixtures/golden_build_bins_v2``
    rather than argued: the shard loop, the ``np.concatenate`` order and all twelve stats keys
    below are untouched, and the five additive keys appear ONLY on the aligned branch. See
    :func:`_build_aligned_bins` for the pinned shape of the argument.

    ``adversarial_ratio`` (Phase 24, ADVT-01) mixes ``round(adversarial_ratio * len(episodes))``
    adversarial refusal episodes IN AMONG the clean ones — the ``replay_ratio`` shape reused, a
    mixture baked into the BIN rather than into the loop, so ``train()`` is untouched and the ratio
    is an auditable committed number. **When it is ``0.0`` this function is BYTE-IDENTICAL to the
    no-kwarg call**, which
    ``tests/test_phase24_bins.py::test_the_default_path_is_byte_identical_to_the_no_kwarg_call``
    and ``tests/test_phase21_aligned_bins.py``'s
    ``test_build_bins_byte_identity_default_matches_the_v2_golden``
    prove rather than argue. That identity is worth nothing on its own — a kwarg nobody reads
    satisfies it trivially — so ``tests/test_phase24_bins.py::test_adversarial_ratio_is_wired`` is
    the LOAD-BEARING half and was watched RED before this parameter existed.

    The nine additive stats keys appear ONLY on the non-zero branch, for the same reason the
    aligned branch's five do: ``tests/test_phase21_aligned_bins.py:226`` asserts
    ``repr(stats) == GOLDEN["stats_repr"]``, so a new key on the default path reddens SC1's own
    guard without moving a single bin byte.

    ``seed`` is read ONLY inside that branch. D-08's interleave permutation must be a PURE FUNCTION
    of the run's EXISTING seed — the Phase 23 D-07 resume path rebuilds these bins and refuses on
    any byte change — and this function had no access to one.
    """
    # === WR-01 (D-41): ONE domain check, BEFORE either branch dispatches. ===
    #
    # The class Phase 20 recorded twice: THE GUARD REFUSES A NAME WHERE THE HARM IS A PROPERTY.
    # The flat branch dispatches on `adversarial_ratio > 0` while the aligned branch refused on
    # `if adversarial_ratio:` — two spellings that disagree on exactly one value, because
    # `float("nan") > 0` is False and `bool(float("nan"))` is True. MEASURED at HEAD before this
    # check existed: `build_bins(..., adversarial_ratio=float("nan"))` on the flat branch returned
    # a token bin whose digest is f146d426…, BYTE-IDENTICAL TO THE CONTROL, while the same value
    # on the aligned branch raised. An `adv_n8` / `adv_n64` point could therefore publish the
    # CONTROL under an adversarial arm name, and nothing downstream could see it: the additive
    # `adversarial_*` stats keys appear only on the non-zero branch, so no reader has a field to
    # check. `math.isfinite` catches NaN and ±inf together; neither `> 0` nor truthiness catches
    # both. The negative case is the same harm reached by a different value.
    import mitigation_budget as mbudget  # LAZY — `_mix_adversarial`'s phase24_adversarial precedent

    grid_lo = min(mbudget.ADVERSARIAL_RATIO_GRID)
    grid_hi = max(mbudget.ADVERSARIAL_RATIO_GRID)
    for ratio_name, ratio_value in (
        ("adversarial_ratio", adversarial_ratio),
        ("replay_ratio", replay_ratio),
    ):
        if not math.isfinite(ratio_value) or ratio_value < 0:
            raise SystemExit(
                f"[teach_persona] build_bins got {ratio_name}={ratio_value!r} — not a finite "
                "ratio at or above zero. The pinned legal domain is the closed range of "
                f"mitigation_budget.ADVERSARIAL_RATIO_GRID, [{grid_lo}, {grid_hi}]. This check "
                "refuses the half that is silently INERT rather than loud: a negative or NaN "
                "ratio fails `> 0`, so the mixer never runs and the CONTROL is built under an "
                "adv_n8 / adv_n64 arm name (measured: token digest f146d426…, byte-identical to "
                "ratio 0.0), while the aligned branch's truthiness test was TRUE for NaN and "
                "refused it — the same value, two verdicts. The guard was refusing a NAME where "
                "the harm is a PROPERTY (WR-01, D-41). Pass a grid ratio; 0.0 is the control."
            )

    if align_facts is not None:
        return _build_aligned_bins(
            tok, episodes, bin_path, mask_path, replay_ratio, align_facts, adversarial_ratio
        )

    # === WR-04 (D-41): the FLAT branch refuses replay and adversarial together. ===
    #
    # The aligned twin already refuses the pair — see `_refuse_ambiguous_aligned_input`, which
    # names D-10 and the fact-derived accumulation identity in full and is the ONE place that
    # identity is spelled (repeating it here would move the live prose-vs-code count that
    # `loop.py`'s accum refusal states to a user debugging a privacy claim, for no new
    # information: `tests/test_phase22_wiring.py::test_the_prose_vs_code_measurement_is_still_true`
    # measures exactly that). The flat branch ran `_mix_adversarial` and THEN
    # `_prepend_replay`, so after both, `replay_ratio` no longer describes the bin. Measured at
    # HEAD before this refusal: `replay_ratio=0.5, adversarial_ratio=0.25` recorded
    # `replay_ratio: 0.5` over a bin that is 3,790 replay tokens of 15,477 = 0.2449.
    if replay_ratio > 0 and adversarial_ratio > 0:
        raise SystemExit(
            f"[teach_persona] build_bins got replay_ratio={replay_ratio} AND "
            f"adversarial_ratio={adversarial_ratio} on the flat branch. `_mix_adversarial` runs "
            "first and `_prepend_replay` sizes itself from the CLEAN `teaching_tokens`, so after "
            "both mixers the recorded `replay_ratio` no longer describes the bin. D-34 is what "
            "makes that expensive: every point record carries `records_per_lot`, "
            "`composed_lot_sizes`, `composed_steps`, `q` and `clip_norm` read LIVE at write time "
            "and asserted against the pin under EXACT equality, so a bin whose composition the "
            "recorded ratio does not describe either halts the whole sweep late or, worse, "
            "publishes an epsilon that does not describe what happened. No sweep point in this "
            "phase sets both — `arm_spec` gives the DP arms a replay ratio and the adversarial "
            "arms an adversarial ratio — so this refusal costs nothing and closes the one "
            "combination that would be silently wrong (WR-04, D-41)."
        )

    id_shards, mask_shards, lengths, fractions = [], [], [], []
    for question, answer in episodes:
        ids, mask = encode_dialogue(tok, [], [(question, answer)])
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))
        lengths.append(len(ids))
        fractions.append(float(np.mean(mask)))

    teaching_tokens = int(sum(lengths))
    # BEFORE the replay block and AFTER teaching_tokens, deliberately on both counts:
    # `teaching_tokens` stays CLEAN-ONLY (D-06 — it must never become a sizing input for the
    # mixture), and `_prepend_replay` keeps inserting replay at index 0, outside the teaching
    # content rather than shuffled into it.
    adversarial = None
    if adversarial_ratio > 0:
        adversarial = _mix_adversarial(
            tok, id_shards, mask_shards, lengths, fractions, adversarial_ratio, len(episodes), seed
        )

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

    frac = _prove_floor_and_band(ids_all, mask_all)

    stats = {
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
    if adversarial is not None:
        stats.update(
            {
                "adversarial_ratio": adversarial_ratio,
                "clean_episodes": len(episodes),
                "adversarial_episodes": adversarial["episodes"],
                "adversarial_pool_size": adversarial["pool_size"],
                "adversarial_multiplicity": adversarial["multiplicity"],
                "adversarial_family_counts": adversarial["family_counts"],
                "adversarial_tokens": adversarial["tokens"],
                "adversarial_scored_tokens": adversarial["scored_tokens"],
                "adversarial_permutation_seed": seed,
                # OVERRIDES the clean count above: `episodes` names what is IN the bin, and every
                # downstream reader (sanity_check's print, the arm record) reads it as that.
                "episodes": len(episodes) + adversarial["episodes"],
            }
        )
    return stats


def _prove_floor_and_band(ids_all, mask_all):
    """Proofs 2 and 3, shared by the flat and the fact-aligned branch; returns the fraction.

    ONE implementation on purpose: two copies of a guard drift, and both branches write bins
    that the same ``get_batch_memmap_masked`` will draw from. Extracting these changed no byte
    written to disk and no raise message on the ``align_facts=None`` path, which the golden
    fixture comparison in ``tests/test_phase21_aligned_bins.py`` proves rather than asserts.
    """
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
    return frac


def _refuse_ambiguous_aligned_input(episodes, replay_ratio, align_facts, adversarial_ratio=0.0):
    """Every way the aligned branch can be called with two sources of truth for one bin."""
    if not align_facts:
        raise SystemExit(
            "[teach_persona] align_facts is empty — the aligned path derives "
            "grad_accum_steps = n_facts from it, so a zero-record bin is a defect, not an "
            "empty-corpus edge case. Pass align_facts=None for the flat v2.0 path."
        )
    for index, pair in enumerate(align_facts):
        if not (isinstance(pair, (tuple, list)) and len(pair) == 2 and hasattr(pair[0], "id")):
            raise SystemExit(
                f"[teach_persona] align_facts[{index}] is not a (fact, episodes) pair whose "
                f"first member carries an .id — got {type(pair).__name__}. The PINNED shape is "
                "a list of (fact, ALREADY-RENDERED episodes) pairs, i.e. "
                "[(f, render_episodes([f], family_ids, second_person=...)) for f in facts] — "
                "never bare Fact objects. build_bins would otherwise need the family ids AND "
                "the second_person flag as new parameters, and every caller already holds both."
            )
        if not pair[1]:
            raise SystemExit(
                f"[teach_persona] align_facts[{index}] (fact {pair[0].id!r}) carries zero "
                "rendered episodes — it would pack to zero windows, so its privacy record "
                "would exist in the accounting and nowhere in the bin."
            )
    ids = [pair[0].id for pair in align_facts]
    duplicates = sorted({fid for fid in ids if ids.count(fid) > 1})
    if duplicates:
        raise SystemExit(
            f"[teach_persona] align_facts carries duplicate fact ids {duplicates} — "
            "grad_accum_steps is about to be derived from len(align_facts), and a duplicate id "
            "would silently merge two privacy records into one."
        )
    if episodes:
        raise SystemExit(
            f"[teach_persona] build_bins got {len(episodes):,} flat episodes AND "
            f"{len(align_facts):,} align_facts pairs — two sources of truth for one bin. "
            "Callers on the aligned branch pass episodes=[]; the flat list is never silently "
            "ignored and never merged with the pairs."
        )
    # WR-01 (D-41): `> 0`, never truthiness. `build_bins` refuses non-finite and negative ratios
    # before this function is reached, so the two branches now test the SAME comparison on the
    # same domain — the NaN disagreement that let the flat branch build the control under an
    # adversarial arm name cannot re-open from either side.
    if replay_ratio > 0:
        raise SystemExit(
            f"[teach_persona] build_bins got replay_ratio={replay_ratio} alongside "
            f"{len(align_facts):,} align_facts pairs. D-10 puts replay OUTSIDE the teaching "
            "bin entirely on the aligned path — it is drawn at train time from "
            "data/dialog_train.bin — so baking it in here would add ~30 replay windows to 33 "
            "fact windows and falsify grad_accum_steps = n_facts by ~7.9x (D-09)."
        )
    if adversarial_ratio > 0:  # WR-01 (D-41) — `> 0`, never truthiness; see the note above.
        raise SystemExit(
            f"[teach_persona] build_bins got adversarial_ratio={adversarial_ratio} alongside "
            f"{len(align_facts):,} align_facts pairs. The adversarial arm packs FLAT by the "
            "DP_ARMS name rule and makes no formal privacy claim (Phase 25 SC4 pins "
            "accounting: null on it), so it has no home in the ragged fact-aligned layout: a "
            "fact-independent refusal episode has no fact shard, and giving it one would put a "
            "record in the accounting for a privacy record that does not exist."
        )


def _build_aligned_bins(
    tok, episodes, bin_path, mask_path, replay_ratio, align_facts, adversarial_ratio=0.0
):
    """The RAGGED fact-aligned packer (D-01 / D-05): three 1:1 bins, one privacy record per fact.

    ``align_facts`` is a list of ``(fact, episodes)`` PAIRS whose second member is that fact's
    ALREADY-RENDERED flat ``(question, answer)`` list — the caller renders, this packs. Each
    fact is re-rendered into its own shard rather than sliced out of the flat ``episodes`` list,
    so the fact boundary is STRUCTURAL rather than reconstructed.

    Each fact is padded to its OWN ``ceil(tokens / BLOCK_SIZE)`` windows — RAGGED, never a
    common W. D-01 measured 10.26% padding ragged versus 24% uniform-at-W=5, and D-02 measured
    ragged accumulation at 1.14x the batched reference versus 1.39x uniform and 1.35x
    vmap-uniform. Ragged wins on BOTH axes, so a uniform-W implementation would be a regression
    against measured numbers rather than a simplification.

    **D-03/D-04 are a VERIFICATION here, not an implementation.** Within one fact the loss is a
    MEAN over its windows, and that costs ZERO new loss code: ``y[m == 0] = -100``
    (``src/personacore/training/data.py:125``) plus ``F.cross_entropy``'s default
    ``reduction="mean"`` (``src/personacore/model/gpt.py:212``) already averages over
    NON-IGNORED targets only, and with one fact per micro-step that IS mean-over-the-record.
    The cost D-03 accepts, named rather than glossed: tokens are NOT weighted equally across the
    corpus — a 5-window fact's windows count 1/5 each where a 4-window fact's count 1/4. That is
    the right asymmetry, because it weights by PRIVACY RECORD rather than by how text happens to
    pack into ``block_size``.
    """
    _refuse_ambiguous_aligned_input(episodes, replay_ratio, align_facts, adversarial_ratio)

    id_shards, mask_shards, fact_shards = [], [], []
    lengths, fractions, windows_per_fact = [], [], []
    pad_tokens = 0
    for index, (_fact, fact_episodes) in enumerate(align_facts):
        shard_ids, shard_mask = [], []
        for question, answer in fact_episodes:
            ids, mask = encode_dialogue(tok, [], [(question, answer)])
            shard_ids.extend(ids)
            shard_mask.extend(mask)
            lengths.append(len(ids))
            fractions.append(float(np.mean(mask)))
        n_windows = math.ceil(len(shard_ids) / BLOCK_SIZE)
        pad = n_windows * BLOCK_SIZE - len(shard_ids)
        pad_tokens += pad
        windows_per_fact.append(n_windows)
        # Pad token 0 and pad mask 0 (so `y[m == 0] = -100` makes it contribute nothing to the
        # loss — D-04), and fact-id pad = THE OWNING FACT'S OWN INDEX, never a sentinel: a
        # sentinel would put two distinct ids in every fact's LAST window IN INPUT SPACE, which
        # makes proof 7(a) permanently unsatisfiable, and sentinel 0 collides with fact index 0.
        id_shards.append(np.asarray(shard_ids + [0] * pad, dtype=np.uint16))
        mask_shards.append(np.asarray(shard_mask + [0] * pad, dtype=np.uint8))
        fact_shards.append(np.full(n_windows * BLOCK_SIZE, index, dtype=np.uint16))

    # The LABEL-SHIFT TAIL: one extra element on all THREE bins, so every window's target slice
    # [k*B+1 : (k+1)*B+1] is in range for all k and the total length is n_windows * B + 1. The
    # tail carries the LAST fact's own index, which is what makes the final window a NON-boundary
    # in target space — hence proof 7(b) expects n_facts - 1 boundary rows and not n_facts.
    id_shards.append(np.zeros(1, dtype=np.uint16))
    mask_shards.append(np.zeros(1, dtype=np.uint8))
    fact_shards.append(np.full(1, len(align_facts) - 1, dtype=np.uint16))

    ids_all = np.concatenate(id_shards)
    mask_all = np.concatenate(mask_shards)
    facts_all = np.concatenate(fact_shards)
    fact_path = fact_bin_path(bin_path)
    ids_all.tofile(bin_path)
    mask_all.tofile(mask_path)
    facts_all.tofile(fact_path)

    # --- proof 1 (D-06's build-time half): all THREE bins must be 1:1 element-aligned ---
    if not len(ids_all) == len(mask_all) == len(facts_all):
        raise SystemExit(
            f"[teach_persona] the three aligned bins are not 1:1: {bin_path} has "
            f"{len(ids_all):,} elements, {mask_path} has {len(mask_all):,}, and {fact_path} has "
            f"{len(facts_all):,} — all three must match element for element (D-06)."
        )

    frac = _prove_floor_and_band(ids_all, mask_all)

    # --- proof 7: window purity, read BACK FROM DISK, in BOTH spaces ---
    # np.fromfile, never the packer's own arithmetic: a check that re-derives boundaries from
    # the same cumulative padded lengths the packer used shares the packer's defect. This is the
    # same predicate the tests drive and the loader (plan 21-06) will call.
    read_facts = np.fromfile(fact_path, dtype=np.uint16)
    read_mask = np.fromfile(mask_path, dtype=np.uint8)

    # (a) INPUT SPACE — THIS IS SC2: no block_size-aligned window carries two fact shards.
    impure = fact_window_impurities(read_facts, BLOCK_SIZE)
    if impure:
        raise SystemExit(
            f"[teach_persona] {len(impure)} block_size-aligned window(s) in {fact_path} carry "
            f"ids from more than one fact, at row(s) {impure} — SC2's 'one window, one fact' "
            "is FALSE for this bin, so grad_accum_steps = n_facts would not be a privacy claim."
        )

    # (b) TARGET SPACE — a POSITIVE claim, not a waiver. Exactly n_facts - 1 boundary rows, each
    # one masked (so `y[m == 0] = -100` removes it from the loss) and each carrying the NEXT
    # fact's index (so the pack is in fact order). Together these are what make "one micro-step
    # is one privacy record" true ACROSS the label shift.
    boundaries = fact_window_impurities(read_facts, BLOCK_SIZE, space="target")
    expected = len(align_facts) - 1
    if len(boundaries) != expected:
        raise SystemExit(
            f"[teach_persona] {fact_path} has {len(boundaries)} target-space boundary rows "
            f"{boundaries}, expected exactly n_facts - 1 = {expected}. Each boundary is the +1 "
            "label shift reading the first token of the next window; a different count is a "
            "REAL packing defect (a fact split across shards, or a lost label-shift tail)."
        )
    for row in boundaries:
        at = (row + 1) * BLOCK_SIZE
        if read_mask[at] != 0:
            raise SystemExit(
                f"[teach_persona] target-space boundary row {row} of {fact_path} points at "
                f"element {at}, whose mask is {read_mask[at]} and not 0 — an UNMASKED boundary "
                "token leaks the next fact's gradient into this record's micro-step."
            )
        if int(read_facts[at]) != int(read_facts[row * BLOCK_SIZE]) + 1:
            raise SystemExit(
                f"[teach_persona] target-space boundary row {row} of {fact_path} crosses from "
                f"fact {read_facts[row * BLOCK_SIZE]} to fact {read_facts[at]} — a boundary must "
                "land on the NEXT fact's index, so the shards are packed out of fact order."
            )

    return {
        "episodes": sum(len(eps) for _fact, eps in align_facts),
        "tokens": int(len(ids_all)),
        "teaching_tokens": int(sum(lengths)),
        "replay_tokens": 0,
        "replay_ratio": replay_ratio,
        "episode_len_mean": float(np.mean(lengths)),
        "episode_len_min": int(min(lengths)),
        "episode_len_max": int(max(lengths)),
        "mask_fraction": frac,
        "mask_fraction_mean": float(np.mean(fractions)),
        "mask_fraction_min": float(min(fractions)),
        "mask_fraction_max": float(max(fractions)),
        # --- additive, ALIGNED BRANCH ONLY: a key added unconditionally would turn the golden
        # fixture's stats_repr comparison red and be a scope change disguised as a refactor. ---
        "fact_bin": str(fact_path),
        "n_windows": int(sum(windows_per_fact)),
        "windows_per_fact": tuple(windows_per_fact),
        "pad_tokens": int(pad_tokens),
        "n_facts": len(align_facts),
    }


def _mix_adversarial(
    tok, id_shards, mask_shards, lengths, fractions, adversarial_ratio, n_clean, seed
):
    """Mix adversarial refusal episodes IN AMONG the clean shards; return the counts (ADVT-01).

    ``_prepend_replay``'s shape: mutates the shard lists IN PLACE, returns what it did, and
    ``SystemExit``s with the sizing formula spelled out rather than a bare number.

    **D-06 — the unit is EPISODES, never TOKENS.** ``n_want = round(ratio * n_clean)`` where
    ``n_clean`` is ``len(episodes)``. ``teaching_tokens`` is not read here and must never become an
    input: a volume derived from the private corpus's SIZE is the side channel
    ``tests/test_phase21_replay_volume.py::test_replay_constant_is_not_derived_from_the_corpus``
    exists to police on the replay seam, and that test is left untouched as a live tripwire.
    ``tests/test_phase24_bins.py::test_the_mixture_is_sized_from_episode_count_not_teaching_tokens``
    holds the episode count fixed while varying the token total, so a dependence would show.

    **D-07 — repetition is permitted and REPORTED.** The same nominal grid runs at both capacities,
    so ``n_want`` exceeds the pool above ratio ``pool / n_clean``; the selection is
    ``(pool * ceil(n_want / pool_size))[:n_want]`` — deterministic, in pool order — and
    ``multiplicity = n_want / pool_size`` travels in the stats dict so Phase 25 SC3 can report it
    in the same sentence as the point.

    **D-08 — the permutation is a PURE FUNCTION of ``seed``.** A private ``random.Random(seed)``,
    never the ambient global RNG: by the time this runs, the global stream has already been
    consumed by the tokenizer load and by rendering, so a global draw would depend on how much
    work happened earlier. The Phase 23 D-07 resume path REBUILDS these bins and refuses on any
    byte change, so a fresh runtime RNG would not merely be untidy — it would make every resumed
    adversarial arm abort.
    """
    import phase24_adversarial as pa  # LAZY — `arm_spec`'s phase21_filler precedent.

    pool = pa.adversarial_episodes(tok)
    families = pa.adversarial_episode_families(tok)
    pool_size = len(pool)
    if len(families) != pool_size:
        raise SystemExit(
            f"[teach_persona] the adversarial pool is {pool_size} episodes against "
            f"{len(families)} family labels. These two views are read POSITIONALLY and paired by "
            "index, so a length mismatch means the per-family counts reported below would name "
            "the wrong episodes."
        )

    n_want = int(round(adversarial_ratio * n_clean))
    if n_want < 1:
        raise SystemExit(
            f"[teach_persona] adversarial_ratio={adversarial_ratio} over {n_clean:,} clean "
            f"episodes gives round({adversarial_ratio} * {n_clean}) = {n_want} adversarial "
            "episodes — a non-zero ratio that places nothing. That is a silently INERT sweep "
            f"point, indistinguishable in the results from the ratio-0.0 control. The smallest "
            f"ratio that places one episode here is {0.5 / n_clean:.6f}; pass 0.0 for the control."
        )

    repeats = math.ceil(n_want / pool_size)
    selected = (pool * repeats)[:n_want]
    selected_families = (families * repeats)[:n_want]

    tokens = 0
    scored = 0
    for persona, question, answer in selected:
        # The episode's OWN persona (D-10): A3 carries the value-free role scaffold in the
        # <|system|> span at mask=0, the two A1 doses carry the empty tuple. The CLEAN loop in
        # build_bins keeps passing [] and stays byte-identical.
        ids, mask = encode_dialogue(tok, persona, [(question, answer)])
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))
        lengths.append(len(ids))
        fractions.append(float(np.mean(mask)))
        tokens += len(ids)
        scored += int(np.sum(mask))

    # D-08. A PRIVATE Random instance over an index list, applied to both shard lists TOGETHER —
    # the bins are 1:1 element-aligned and proof 1 in build_bins checks the totals, not the pairing.
    rng = random.Random(seed)
    order = list(range(len(id_shards)))
    rng.shuffle(order)
    id_shards[:] = [id_shards[i] for i in order]
    mask_shards[:] = [mask_shards[i] for i in order]

    # D-10 AT THE SELECTED PREFIX. The full pool is 3-way balanced and 24-05 asserts that, but the
    # selection above is a PREFIX of `pool * ceil(...)`, so the balance of what actually trains is
    # a property of the COMMITTED CORPUS'S ROW ORDER, not of this code. Measured at HEAD
    # 2026-08-30 that order is a strict 3-cycle [A1-mild, A1-aggressive, A3] * 112 and every grid
    # point lands 15/15/14 or better. Nothing asserts that ordering — so if a rebuild ever grouped
    # the rows by family, every point below ratio ~0.64 would train ONE family while D-10's
    # "three families train" truth stayed green. Reporting the counts is what lets a test see it.
    family_counts = {family: selected_families.count(family) for family in pa.TRAINED_FAMILIES}
    return {
        "episodes": n_want,
        "pool_size": pool_size,
        "multiplicity": n_want / pool_size,
        "family_counts": family_counts,
        "tokens": tokens,
        "scored_tokens": scored,
    }


def _prepend_replay(id_shards, mask_shards, replay_ratio, teaching_tokens, *, n_facts=None):
    """Concatenate a leading slice of the PersonaChat bins ahead of the teaching episodes.

    Build-time replay (Open Q5): ``train()`` accepts one ``train_bin``, so the mixture ratio is
    baked into the bin instead of into the loop. Returns the replay token count.

    **Two branches, and which one runs is decided by ``n_facts`` alone (D-11 / D-24):**

    ``n_facts is None`` — the LEGACY v3.0 sizing, ``round(replay_ratio * teaching_tokens)``,
    UNCHANGED. This branch exists ONLY to reproduce the recorded v3.0 arms
    (``cal_first_person_replay`` and ``real``), whose bins are committed evidence and which are
    NOT DP. **It retains the D-11 side channel BY DESIGN**, so that
    ``tests/test_phase21_replay_volume.py::test_side_channel_negative_control`` has a live
    negative control proving the differential can see a side channel at all. An open defect that
    is ASSERTED PRESENT by a passing test is a different artifact from an open defect tolerated
    in silence — the retention is deliberate and it is watched.

    ``n_facts`` an int — the v4.0 sizing, ``replay_window_budget(n_facts)``. ``replay_ratio`` and
    ``teaching_tokens`` are **IGNORED ENTIRELY**: not multiplied in, not used as a cap, not
    consulted at all. Any residual dependence on ``teaching_tokens`` reopens the channel, so the
    precedence is total rather than blended. Both ignored inputs are named in this function's own
    reporting (the short-slice message below) so a caller cannot mistake which sizing ran.

    A raise on a non-default ``replay_ratio`` here would be self-defeating, which is why there
    isn't one: the differential runs the SAME call ONE KWARG APART
    (``replay_ratio=1.0, n_facts=8`` versus ``replay_ratio=1.0, n_facts=None``), and that shared
    call shape is the only thing making the two verdicts a property of the BRANCH rather than of
    two different fixtures. (Distinct from ``_refuse_ambiguous_aligned_input``'s ``replay_ratio``
    refusal, which is 21-04's and stands untouched: that one guards the ALIGNED branch, where
    D-10 puts replay outside the teaching bin entirely and a baked-in ratio would falsify
    ``grad_accum_steps = n_facts`` by ~7.9x. The aligned branch raises before ever reaching this
    function, so the two guards cannot collide.)
    """
    if n_facts is not None and (
        isinstance(n_facts, bool) or not (isinstance(n_facts, int) and n_facts > 0)
    ):
        raise SystemExit(
            f"[teach_persona] _prepend_replay got n_facts={n_facts!r} — the v4.0 replay budget "
            "is REPLAY_WINDOWS_PER_FACT * n_facts * BLOCK_SIZE, so n_facts must be a positive "
            "int (a COUNT of privacy records). Pass n_facts=None for the legacy v3.0 sizing."
        )
    if not DIALOG_TRAIN_BIN.exists() or not DIALOG_TRAIN_MASK.exists():
        raise SystemExit(
            f"[teach_persona] replay arm needs {DIALOG_TRAIN_BIN} and {DIALOG_TRAIN_MASK} — run "
            "`python scripts/prepare_dialog_corpus.py` first."
        )
    if n_facts is None:
        want = int(round(replay_ratio * teaching_tokens))
        sizing = (
            f"legacy v3.0 sizing round({replay_ratio} * {teaching_tokens:,} teaching_tokens) "
            "— this branch carries the D-11 side channel by design"
        )
    else:
        want = replay_window_budget(n_facts)
        sizing = (
            f"v4.0 public sizing replay_window_budget({n_facts}) = "
            f"{REPLAY_WINDOWS_PER_FACT} windows/fact * {n_facts} facts * {BLOCK_SIZE} tokens; "
            f"replay_ratio={replay_ratio} and teaching_tokens={teaching_tokens:,} were IGNORED "
            "ENTIRELY (D-11 — the volume depends on public quantities only)"
        )
    replay_ids = np.fromfile(DIALOG_TRAIN_BIN, dtype=np.uint16, count=want)
    replay_mask = np.fromfile(DIALOG_TRAIN_MASK, dtype=np.uint8, count=want)
    if len(replay_ids) != want or len(replay_mask) != want:
        raise SystemExit(
            f"[teach_persona] replay slice short: wanted {want:,} tokens, read "
            f"{len(replay_ids):,} ids / {len(replay_mask):,} mask elements. Sizing was {sizing}."
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
    # `forms` is resolved from the ARM's facts for the same reason `render_episodes` resolves it:
    # this is the SECOND `render_family` call site on the dp_n64 build path, and without it the
    # n=64 arm builds its bins successfully and then dies here on `KeyError: 'filler_boat_name'`.
    # It is `None` for every published-slot arm, so the proof runs the code path it always ran.
    forms = _slot_forms_for(facts)
    lo, hi = fs.PARAPHRASES_PER_FACT_TARGET
    for fact in facts:
        count = sum(len(fs.render_family(fid, fact, forms=forms)) for fid in fs.TAUGHT_FAMILY_IDS)
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
    """(facts, second_person, replay_ratio) for one arm — the only per-arm branching.

    **The two v4.0 DP arms exclude the SOFT TIER entirely (D-14), and the reason is a
    pre-registration, not a preference.** v4.0 already pre-registered its small capacity as
    literally 8: ``REQUIREMENTS.md:84`` (GATE-10, ``[x]`` COMPLETE inside the FROZEN
    ``scripts/mitigation_gate.py``), ``REQUIREMENTS.md:173`` / ``ROADMAP.md:430-433`` (CAL-03),
    ``REQUIREMENTS.md:206`` (FRONT-01), and ``ROADMAP.md:52``'s pre-registered null at L=8 facts.
    An n=10 small capacity contradicts GATE-10, CAL-03 and FRONT-01 at once. The free second
    benefit: exclusion keeps D-01 and D-02 valid EXACTLY AS MEASURED — both benchmarked 8 facts at
    the ragged ``windows_per_fact = (4,4,4,4,4,5,4,4)``; at n=10 both soft facts are 5-window and
    both measurements would have needed redoing. The ``real`` arm's
    ``LOCKED_FACTS + SOFT_TIER_FACTS`` below is a RECORDED v3.0 composition whose bins are
    committed evidence, so it is left alone.

    **``replay_ratio = 0.0`` on both DP arms is LOAD-BEARING, not a default.** Under D-10 replay
    LEAVES the teaching bin entirely and is drawn at TRAIN time from ``data/dialog_train.bin``
    through ``train()``'s replay seam at the public volume ``replay_window_budget(n_facts)``. The
    teaching bin therefore holds FACTS ONLY, which is what makes ``grad_accum_steps = n_facts``
    literally true with no roadmap amendment. A non-zero ratio here would put replay back in the
    bin and silently reintroduce D-09's measured consequence: 7,581 replay tokens is roughly 30
    windows against 33 fact windows, so an aligned loader turning every window into a micro-step
    would give ``grad_accum_steps = 63``, not 8 — falsifying SC2 by about 7.9x.
    """
    if arm == "cal_first_person":
        return fs.CALIBRATION_FACTS, False, REPLAY_RATIO
    if arm == "cal_first_person_replay":
        return fs.CALIBRATION_FACTS, False, REPLAY_ARM_RATIO
    if arm == "cal_second_person":
        return fs.REGISTER_ARM_FACTS, True, REPLAY_RATIO
    if arm == "real":
        # The real arm reads the two CALIBRATION-DERIVED settings, so the derived numbers are
        # load-bearing rather than decorative: editing either constant changes what the real run
        # actually trains on.
        return (
            fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS,
            REAL_RUN_SECOND_PERSON,
            REAL_RUN_REPLAY_RATIO,
        )
    if arm == "dp_n8":
        return fs.LOCKED_FACTS, False, 0.0
    if arm == "dp_n64":
        # LAZY import, deliberately not at module scope: it keeps `teach_persona`'s import graph
        # unchanged for every existing consumer (`tests/test_phase14_scoring.py`'s clean-room
        # scan among them), and `phase21_filler`'s import-time collision refusal still runs
        # unconditionally in CI through `tests/test_phase21_filler.py` and
        # `tests/test_phase21_sc5.py`. Nothing is lost and one coupling is avoided.
        import phase21_filler

        return fs.LOCKED_FACTS + phase21_filler.FILLER_FACTS, False, 0.0
    if arm == "adv_n8":
        # `replay_ratio = 0.0` is LOAD-BEARING here for a DIFFERENT reason than on the DP arms:
        # 24-RESEARCH's entire mask-fraction headroom table — every number D-05 pins
        # MIN_REFUSAL_SCORED_TOKENS against — was computed at `replay_ratio = 0.0`. A non-zero
        # ratio moves the measured fraction from 0.359 to 0.403 on the `real` arm, so it would
        # invalidate the calibration the refusal length was chosen from.
        return fs.LOCKED_FACTS, False, 0.0
    if arm == "adv_n64":
        # Same LAZY import, same reason as `dp_n64` above: it keeps `teach_persona`'s import
        # graph unchanged for every existing consumer, and `phase21_filler`'s import-time
        # collision refusal still runs unconditionally in CI.
        import phase21_filler

        # `replay_ratio = 0.0` load-bearing, as for `adv_n8`.
        return fs.LOCKED_FACTS + phase21_filler.FILLER_FACTS, False, 0.0
    raise SystemExit(f"[teach_persona] unknown arm {arm!r} — expected one of {ARMS}")


def _sha256(path):
    """sha256 of one file, for the resume corpus-identity proof. Streamed — the bins are small
    today (a dp_n8 teaching bin is tens of KB) but a whole-file read is a needless ceiling."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_arm_bins(
    arm,
    facts,
    family_ids,
    *,
    second_person=False,
    replay_ratio=0.0,
    adversarial_ratio=0.0,
    seed=SEED,
    prefix="phase14",
    resume_from=None,
):
    """Render, encode, write and prove one arm's teaching bins; return ``(tok, stats, paths)``.

    The whole bins half behind one call, so the training half (below) has exactly one seam into
    it and no arm can be trained on bins built by a different code path.

    ``seed`` and ``prefix`` are Phase 17's additive widening (D-14 / D-16: import this
    instrument, never copy it). Both default to today's values, so every Phase-14 arm builds
    bit-identical bins at bit-identical paths.

    **The packer is chosen by ARM NAME (``DP_ARMS``), at the one seam that writes an arm's
    bins.** A ``dp_*`` arm packs the ragged fact-aligned three-bin path; every other arm packs
    the flat v3.0 pack through the SAME ``build_bins`` call below with ``align_facts=None``, so
    "no arm can be trained on bins built by a different code path" stays literally true and the
    four published arms stay byte-identical (proven against
    ``tests/fixtures/golden_build_bins_v2.json``, not argued).

    ``replay_ratio`` is threaded to ``build_bins`` UNCHANGED on both branches, deliberately.
    ``arm_spec`` returns ``0.0`` for both DP arms and that zero is load-bearing (D-10 puts replay
    outside the teaching bin, drawn at train time from ``data/dialog_train.bin``), so it is falsy
    and never trips ``_refuse_ambiguous_aligned_input``'s replay guard. Special-casing the
    argument away here would DISARM that guard: leaving it wired means the day someone sets a
    non-zero ratio on a DP arm, this function raises instead of quietly baking ~30 replay windows
    in beside 33 fact windows and falsifying ``grad_accum_steps = n_facts`` by ~7.9x (D-09).

    ``adversarial_ratio`` (Phase 24, ADVT-01) is ``0.0`` for every existing caller — ``arm_spec``
    never returns it and only Phase 25's sweep driver passes one — and then this function is
    BYTE-IDENTICAL to before. It is threaded UNCHANGED on BOTH branches for the same reason
    ``replay_ratio`` is: special-casing it away on the aligned branch would DISARM the widened
    ``_refuse_ambiguous_aligned_input``, so the day someone sets a non-zero ratio on a ``dp_*`` arm
    this raises instead of quietly building a bin whose fact-aligned accounting counts records that
    do not exist. ``seed`` is passed through to ``build_bins`` too, so D-08's interleave permutation
    and this function's ``seed_everything`` agree by construction rather than by coincidence.

    ``resume_from`` (D-07, plan 23-07) is ``None`` for every non-resuming caller and then this
    function is BYTE-IDENTICAL to before. It is threaded here — and not only into ``train_arm`` —
    because this is the SECOND caller of ``arm_bin_targets``, and a resume that inverted only
    ``train_arm``'s guard would be refused three lines later by THIS one. That is the seam being
    dead on arrival, not a nicety.

    On a resume the bins must EXIST (the inversion), and this function then REBUILDS them and
    REFUSES if a single byte moved. Rebuild-and-compare rather than skip-the-rebuild, deliberately:
    the pack is deterministic in ``(facts, family_ids, second_person, replay_ratio, seed)``, so a
    byte-identical rebuild PROVES the resumed half trains on the corpus the killed half trained on
    (T-23-35), while skipping the rebuild would only ASSUME it. ``n_facts`` also keeps coming from
    the packer's own record count, which is the provenance ``train_arm``'s ``dp_accum`` comment
    requires — a second derivation read back off the fact bin would be free to drift from it.
    """
    outputs = arm_outputs(arm, prefix=prefix)
    targets = arm_bin_targets(arm, outputs)
    if resume_from is None:
        refuse_if_exists(targets)
        before_digests = None
    else:
        refuse_if_exists([], expected=targets)
        before_digests = {path: _sha256(path) for path in targets}

    seed_everything(seed)
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain
    aligned = arm in DP_ARMS
    if aligned:
        # The PINNED ``align_facts`` shape: one (fact, that fact's ALREADY-RENDERED episodes)
        # pair per fact, and the flat list EMPTY beside it — the aligned branch refuses two
        # sources of truth for one bin. Rendering per fact rather than slicing a flat list is
        # what makes the fact boundary STRUCTURAL; the call order (facts outer, sorted families
        # inner) is `render_episodes`' own, so the episode sequence is unchanged.
        pairs = [
            (fact, render_episodes([fact], family_ids, second_person=second_person))
            for fact in facts
        ]
        episodes = []
    else:
        pairs = None
        episodes = render_episodes(facts, family_ids, second_person=second_person)
    started = time.time()
    stats = build_bins(
        tok,
        episodes,
        outputs["bin"],
        outputs["mask"],
        replay_ratio=replay_ratio,
        align_facts=pairs,
        adversarial_ratio=adversarial_ratio,
        seed=seed,
    )
    sanity_check(tok, arm, outputs["bin"], outputs["mask"], facts, stats)

    if before_digests is not None:
        drifted = {
            path: (was, now)
            for path, was in before_digests.items()
            if (now := _sha256(path)) != was
        }
        if drifted:
            raise SystemExit(
                "[teach_persona] the resumed arm rebuilt a DIFFERENT corpus than the killed half "
                "trained on: "
                + "; ".join(
                    f"{p} {was[:12]}... -> {now[:12]}..." for p, (was, now) in drifted.items()
                )
                + f". The pack is deterministic in (facts, family_ids, second_person, "
                f"replay_ratio, adversarial_ratio={adversarial_ratio}, seed={seed}), so a "
                "drifted byte means one of those inputs moved "
                "between the kill and the resume. Continuing would publish an epsilon whose "
                "prefix and suffix describe two different datasets."
            )
        print(
            f"[teach_persona] resume: rebuilt bins are byte-identical to the killed half's "
            f"({len(before_digests)} files, sha256 verified)"
        )

    print(
        f"[teach_persona] {arm}: {stats['episodes']:,} episodes, {stats['tokens']:,} tokens "
        f"({stats['teaching_tokens']:,} teaching + {stats['replay_tokens']:,} replay), "
        f"episode length mean {stats['episode_len_mean']:.1f} "
        f"[{stats['episode_len_min']}, {stats['episode_len_max']}]"
    )
    print(
        f"[teach_persona] bins provenance: seed={seed} git_sha={git_sha()} pid={os.getpid()} "
        f"torch={torch.__version__} arm={arm} second_person={second_person} "
        f"replay_ratio={replay_ratio} adversarial_ratio={adversarial_ratio} "
        f"mask_fraction={stats['mask_fraction']:.4f} "
        f"wall={time.time() - started:.1f}s "
        f"utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
    )
    # ``stats['fact_bin']`` is the PACKER's own ``fact_bin_path(bin_path)`` result — the third
    # bin is never re-derived by string here, and a two-bin line for a three-bin build would
    # under-report what the operator now has to treat as recorded evidence.
    written = f"{outputs['bin']} + {outputs['mask']}"
    if aligned:
        written += f" + {stats['fact_bin']}"
        print(
            f"[teach_persona] {arm}: FACT-ALIGNED pack — {stats['n_facts']} privacy records, "
            f"{stats['n_windows']} windows {stats['windows_per_fact']}, "
            f"{stats['pad_tokens']:,} pad tokens"
        )
    print(f"[teach_persona] bins written (gitignored): {written}")
    return tok, stats, outputs


SIGMA_FLAG = "--sigma="
CLIP_FLAG = "--clip-norm="

# Both arm lists are interpolated from their TUPLES, never re-spelled: a hand-typed DP form would
# be free to drift from `DP_ARMS` the day a third capacity is added.
USAGE = (
    f"usage: python scripts/teach_persona.py {{{'|'.join(ARMS)}}}\n"
    f"       python scripts/teach_persona.py {{{'|'.join(DP_ARMS)}}} "
    f"{SIGMA_FLAG}<float> {CLIP_FLAG}<float>\n"
    "       python scripts/teach_persona.py --calibration [--force]\n"
    "       python scripts/teach_persona.py --rewrite-report [--force]\n"
    f"\n{'|'.join(ADV_ARMS)} are PROGRAMMATIC-ONLY and are refused here: no flag carries\n"
    "adversarial_ratio, so a CLI run would train the ratio-0.0 control under an 'adversarial'\n"
    "name. Call train_arm(..., adversarial_ratio=...) from a sweep driver instead.\n"
    f"\n{SIGMA_FLAG} and {CLIP_FLAG} are REQUIRED on the DP arms and have NO DEFAULT anywhere.\n"
    "sigma (the unitless noise multiplier) and C (the per-record L2 bound) are Phase 23 resource\n"
    "parameters under Phase 20's Z boundary; Phase 22 names no value in its tree, so there is\n"
    "nothing for Phase 23 to override and nothing to drift. A default would silently become the\n"
    "operating privacy budget of a run nobody pre-registered."
)


def _parse_dp_flags(tokens):
    """``('--sigma=<float>', '--clip-norm=<float>')`` -> ``(sigma, C)``; refuse anything else.

    Explicit prefix matching in this file's own argv-slicing register — deliberately NOT
    ``argparse``. ``main`` is argv slicing and ``run_calibration``/``rewrite_report`` are its
    sub-mode precedent; a second CLI idiom inside one entry point is a maintenance trap.

    The two domain refusals here are the EARLY, CHEAP copy of refusals the mechanism makes too:
    ``DPSGD.__init__`` re-checks both as ``[dp-refusal:sigma-domain]`` /
    ``[dp-refusal:clip-domain]`` as properties of the MECHANISM, so a caller that bypasses this
    CLI is still refused. Neither is redundant — this one names the flag the operator typed.
    """
    seen = {}
    for token in tokens:
        for flag in (SIGMA_FLAG, CLIP_FLAG):
            if token.startswith(flag):
                if flag in seen:
                    raise SystemExit(f"[teach_persona] {flag} given twice\n\n{USAGE}")
                try:
                    seen[flag] = float(token[len(flag) :])
                except ValueError:
                    raise SystemExit(
                        f"[teach_persona] {token!r} is not a float\n\n{USAGE}"
                    ) from None
                break
        else:
            raise SystemExit(f"[teach_persona] unexpected argument {token!r}\n\n{USAGE}")

    missing = sorted(flag for flag in (SIGMA_FLAG, CLIP_FLAG) if flag not in seen)
    if missing:
        raise SystemExit(f"[teach_persona] missing required {' and '.join(missing)}\n\n{USAGE}")

    sigma, clip_norm = seen[SIGMA_FLAG], seen[CLIP_FLAG]
    if sigma < 0:
        raise SystemExit(
            f"[teach_persona] {SIGMA_FLAG}{sigma} is negative. sigma is the unitless NOISE "
            "MULTIPLIER and the noise standard deviation is sigma * C, so a negative multiplier "
            "has no meaning; zero is the identity. The DP seam re-checks this as a property of "
            "the mechanism ([dp-refusal:sigma-domain])."
        )
    if clip_norm <= 0:
        raise SystemExit(
            f"[teach_persona] {CLIP_FLAG}{clip_norm} is not strictly positive. C is an L2 BOUND: "
            "a zero bound clips every record to the zero vector and a negative bound is not a "
            "norm at all. The DP seam re-checks this as a property of the mechanism "
            "([dp-refusal:clip-domain])."
        )
    return sigma, clip_norm


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # Plan 14-09's two modes. Both are defined below in the CALIBRATION RUN section.
    if argv and argv[0] == "--calibration":
        run_calibration(argv[1:])
        return
    if argv and argv[0] == "--rewrite-report":
        rewrite_report(argv[1:])
        return
    if not argv or argv[0] not in ARMS:
        raise SystemExit(USAGE)
    arm = argv[0]
    # The NON-DP path keeps its exact pre-22-10 shape: `len(argv) != 1` still rejects every extra
    # token, so no v2.0/v3.0 invocation changes. Only a DP arm reaches the two-flag branch.
    if arm in DP_ARMS:
        dp_sigma, dp_clip_norm = _parse_dp_flags(argv[1:])
    elif arm in ADV_ARMS:
        raise SystemExit(
            f"[teach_persona] {arm} carries NO adversarial_ratio from this CLI, so running it "
            "here would train at the 0.0 default and write bins, a checkpoint and an adapter all "
            "named 'adversarial' over a corpus holding ZERO adversarial episodes — with the "
            "ratio recorded nowhere, and `refuse_if_exists` then treating those bins as recorded "
            "evidence against the real sweep. Phase 25's sweep driver calls "
            "`train_arm(..., adversarial_ratio=...)` PROGRAMMATICALLY over "
            "`mitigation_budget.ADVERSARIAL_RATIO_GRID`; `scripts/phase24_record.py` is the "
            "worked example. A grid sweep is not something an operator types one ratio at a time."
        )
    else:
        dp_sigma = dp_clip_norm = None
        if len(argv) != 1:
            raise SystemExit(USAGE)

    facts, second_person, replay_ratio = arm_spec(arm)
    train_arm(
        arm,
        dp_sigma=dp_sigma,
        dp_clip_norm=dp_clip_norm,
        facts=facts,
        family_ids=fs.TAUGHT_FAMILY_IDS,
        second_person=second_person,
        replay_ratio=replay_ratio,
        # `arm_outputs`' prefix exists so a run's artifacts say WHICH PHASE produced them. The
        # DP arms are v4.0/Phase-21, so `phase14_dp_n64_adapter.pt` and `results/phase14_dp_n64/`
        # would be a false provenance claim on the very parameter added to prevent one. Nothing
        # is orphaned by labelling them correctly: no `phase14_dp_*` artifact has ever been
        # recorded. `bin`/`mask`/`fact` carry no phase label either way (arm_outputs' own
        # non-widening), so this moves the csv, the checkpoint and the adapter only.
        prefix="phase21" if arm in DP_ARMS else "phase14",
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


def _generator_state_bytes(device):
    """Byte length of a FRESH ``torch.Generator``'s state on ``device`` — DERIVED, never a literal.

    The two figures this project has measured are 5,056 (CPU) and 44 (MPS) under torch 2.7.1, and
    they are recorded in ``personacore.checkpoint``'s two-slot register and in
    ``DPSGD.noise_rng_state``'s docstring. They are NOT hardcoded here: a probe self-calibrates if
    a torch release moves either number, and a guard that goes stale is worse than no guard.
    """
    return int(torch.Generator(device=device).get_state().numel())


def _refuse_cross_device_resume(arm, resume_from, device):
    """Refuse a DP resume whose ``dp_noise_rng`` was written on a DIFFERENT device (T-23-38).

    Scoped to DP arms deliberately. The generator state is the ONLY device-typed thing in the
    checkpoint — every other RNG slot round-trips as a CPU tensor on both devices, and
    ``load_checkpoint`` passes ``map_location="cpu"`` — so a non-DP resume has nothing to refuse
    and no epsilon to protect. That is also why the *missing-slot* case below is a refusal HERE
    while ``training/loop.py`` deliberately TOLERATES it (its branch (2): a checkpoint without the
    slot was written by a run with no DP seam, and a freshly seeded generator has released
    nothing). The two are not in tension: at the LOOP level "no slot" means "not a DP run, seed
    fresh"; at THIS level it means "you asked to resume a DP ARM from a checkpoint no DP run
    wrote", and the epsilon prefix that resume claims to continue does not exist. Refusing here
    reddens neither of the two committed guards that pin the loop's tolerance —
    ``test_dp_noise_rng_round_trips_through_a_kill_and_resume`` and
    ``test_resume_epsilon_bit_identical`` both drive ``train()`` directly, never ``train_arm``.

    torch would refuse the mismatch on its own (``RuntimeError: RNG state is wrong size``), which
    is why this is an upgrade rather than a necessity: that message names no arm, no file and no
    phase. The operator mistake it stands for is a smoke run done on CPU and then "continued" on
    the M3.
    """
    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy objects.
    # TRUSTED-only read of the project's OWN checkpoint (T-14-04) — the same posture as the
    # CONVBASE_BEST load below, and the file was written by this same driver minutes earlier.
    ckpt = torch.load(resume_from, map_location="cpu", weights_only=False)
    state = ckpt.get("dp_noise_rng")
    if state is None:
        raise SystemExit(
            f"[teach_persona] arm {arm!r} asked to resume from {resume_from}, but that checkpoint "
            "carries NO 'dp_noise_rng' key. All three save_checkpoint call sites in "
            "training/loop.py::train splat **_dp_extra(), which is empty unless a DP seam is "
            "live, so the key's ABSENCE is the provenance: no DP run wrote this file. There is "
            "therefore no released-noise prefix for this resume to continue, and the epsilon it "
            "would report would describe a composition whose first half was never privatised. "
            "Resume a DP arm only from a checkpoint its own DP run wrote."
        )
    recorded_bytes = int(state.numel())
    expected_bytes = _generator_state_bytes(device)
    if recorded_bytes == expected_bytes:
        return
    probes = {_generator_state_bytes("cpu"): "cpu"}
    if torch.backends.mps.is_available():
        probes[_generator_state_bytes("mps")] = "mps"
    if torch.cuda.is_available():
        probes[_generator_state_bytes("cuda")] = "cuda"
    recorded_device = probes.get(recorded_bytes, f"unrecognised ({recorded_bytes} bytes)")
    raise SystemExit(
        f"[teach_persona] arm {arm!r} asked to resume from {resume_from}, whose dp_noise_rng was "
        f"written on {recorded_device} ({recorded_bytes} bytes), but this run resolved device "
        f"{device!r} (a generator state there is {expected_bytes} bytes). A DP generator state "
        "does not cross devices — torch refuses it as 'RNG state is wrong size' without naming "
        "the arm or the file. Re-run the whole arm on one device: a run split across two has no "
        "single noise stream, so the epsilon it would publish describes neither half."
    )


def train_arm(
    arm,
    *,
    facts,
    family_ids,
    second_person=False,
    replay_ratio=0.0,
    adversarial_ratio=0.0,
    seed=SEED,
    prefix="phase14",
    dp_sigma=None,
    dp_clip_norm=None,
    resume_from=None,
):
    """Build one arm's bins, train ONLY its LoRA parameters on them, and export the adapter.

    Returns a dict carrying the arm paths, the bins stats, the final train loss, and the
    adapter-ON/adapter-OFF masked dialogue-val PPL pair (the no-collateral-collapse endpoint).

    ``seed`` and ``prefix`` are Phase 17's additive widening, and both are threaded THROUGH to
    ``build_arm_bins`` rather than only used here. That is load-bearing: the ``build_arm_bins``
    call below REBINDS ``paths``, so the export half writes to the dict IT returned. A prefix
    applied here but not there would guard the ``phase17_`` paths with ``refuse_if_exists``
    while exporting the adapter to ``phase14_`` — a Phase-17 artifact under a Phase-14 name,
    which is a false provenance claim, not a cosmetic one.

    ``seed`` (D-14) reaches all three seeding sites: the bins build, the GPT/LoRA-init draw and
    ``TrainConfig``. Phase 17 needs three adapters at three DISTINCT seeds; identical seeds
    would make three personas share one initialization draw and one data order.

    ``dp_sigma`` / ``dp_clip_norm`` (D-08, plan 22-10) are the DP-SGD noise multiplier and the
    per-record L2 bound ``C``. They are threaded THROUGH from :func:`main`'s CLI rather than read
    from a module constant, and they are the reason **NO numeric sigma or C literal exists
    anywhere in this file**: Phase 22 names no value in its tree, so there is nothing for Phase 23
    to override and nothing to drift across Phase 20's Z boundary.

    **``None`` is a SENTINEL, not a default value.** The plan text for 22-10 asks for "keyword-only
    with no default", but five call sites outside this module already call ``train_arm``
    (``phase17_isolation``, ``phase19_erasure`` x3, ``phase19_run``, and :func:`run_calibration`
    here) and every one of them passes a NON-DP arm; a truly-required parameter would make each of
    them a ``TypeError``. The sentinel keeps that contract intact AND is what the plan's own
    refusal instruction ("if either is ``None`` on a DP arm, refuse") presupposes. It names no
    sigma and no C, so the no-literal property the AST guard pins is unaffected: a DP arm without
    both values raises ``SystemExit`` below and never trains.

    ``resume_from`` (D-07, plan 23-07) — THE ONE HOP THAT CLOSES WARNING-2
    ----------------------------------------------------------------------
    ``training/loop.py::train`` has implemented ``resume_from`` completely since v1.0 — full state
    + RNG restore, ``start_step = ckpt["step"]``, and the three-branch DP-slot matrix WARNING-1 is
    closed on. What was missing was this call: the ``train(...)`` below did not pass it, so a
    killed DP arm could only be restarted from ZERO, and ``refuse_if_exists`` would not even allow
    that without the operator deleting the CSV — which discontinuities the very curve
    ``train()`` derives cumulative tokens from the absolute step to keep continuous. ``train()``
    itself needs NOTHING; this is one hop above it.

    ``None`` IS A SENTINEL HERE TOO, for the identical reason ``dp_sigma``/``dp_clip_norm`` are.
    SEVEN production call sites outside this module already call ``train_arm`` —
    ``phase17_isolation``, ``phase19_erasure`` (x3), ``phase19_run``, and :func:`run_calibration`
    / :func:`main` here — and every one of them passes a NON-DP arm and no resume. A
    truly-required parameter would make each a ``TypeError``. ``train_arm(resume_from=None)`` is
    byte-identical to the pre-23-07 function at every one of them. (Enumerated by SYMBOL, not by
    line number: a symbol's name survives edits, a line number survives none.)

    THE GUARD INVERTS PER TARGET; IT IS NOT BYPASSED. Four rows, and this table is where the bug
    would live:

    ======================  ==========================  ============================================
    target                  on a resume                 why
    ======================  ==========================  ============================================
    bins (2, or 3 on a DP)  REQUIRED PRESENT            regenerated bins are a DIFFERENT corpus
                                                        (T-23-35); ``build_arm_bins`` rebuilds and
                                                        refuses on any byte drift
    ``csv``                 REQUIRED PRESENT            ``CSVLogger`` is restart-safe and the token
                                                        column is derived from the ABSOLUTE step, so
                                                        appending keeps the curve continuous; the
                                                        operator deleting it to get past a refusal
                                                        is the mistake (T-23-33)
    ``checkpoint``          REQUIRED PRESENT            it IS the resume source
    ``adapter``             STILL REFUSED IF PRESENT    the export is the LAST thing this function
                                                        does, so an adapter on disk means the arm
                                                        already completed
    ======================  ==========================  ============================================

    TWO REFUSALS THE SEAM ADDS, both ``SystemExit`` naming the arm and the file:

    * CROSS-ARM. ``resume_from`` must resolve to THIS arm's own ``paths["checkpoint"]``. Resuming
      arm A's DP run from arm B's checkpoint would publish an epsilon describing a composition
      that spans two arms — the same defect class ``_count_composed_steps`` was written to catch.
    * CROSS-DEVICE. The DP generator's state is 5,056 bytes on CPU and 44 bytes on MPS and the two
      are MUTUALLY REFUSED by torch. The seam does not NEED a guard — torch already raises
      ``RuntimeError: RNG state is wrong size`` — but that message names no arm, no file and no
      phase, and a ``SystemExit`` naming all four (arm, file, recorded device, resolved device) is
      a strictly better failure at the same cost. The warning sign it stands for is concrete: a
      smoke run done on CPU and then "continued" on the M3.
    """
    # ONE boolean gates all FOUR D-08 wirings below, so the DP-vs-non-DP boundary is a single
    # readable predicate and a future reader cannot wire three of four by accident.
    is_dp = arm in DP_ARMS
    if is_dp and (dp_sigma is None or dp_clip_norm is None):
        raise SystemExit(
            f"[teach_persona] arm {arm!r} needs BOTH --sigma and --clip-norm "
            f"(got sigma={dp_sigma!r} clip_norm={dp_clip_norm!r}). Neither has a default, "
            "anywhere: sigma and C are Phase 23 RESOURCE PARAMETERS under Phase 20's Z boundary, "
            "and Phase 22 names no value in its tree so there is nothing for Phase 23 to override "
            "and nothing to drift. A default here would silently become the operating privacy "
            "budget of a run nobody pre-registered."
        )

    verdict = _require_go_verdict(FACTSET_REPORT)
    print(f"[teach_persona] D-06 verdict: {verdict} — proceeding with arm {arm!r}")
    if arm == "real":
        # W-02: the real run additionally gates on the CALIBRATION verdict. The gate is
        # arm-conditional on purpose — the calibration arms are what PRODUCE that report, so
        # gating them on it would be a deadlock. The asymmetry is deliberate, not an oversight.
        cal_verdict = _require_go_verdict(CALIBRATION_REPORT)
        print(f"[teach_persona] calibration verdict: {cal_verdict} — real arm cleared (W-02)")

    paths = arm_outputs(arm, prefix=prefix)
    # Refuse on EVERY target up front (five, or six once a DP arm's fact bin is counted),
    # before a single token is written: discovering a recorded checkpoint only after rebuilding
    # the bins would already have clobbered them. On a RESUME the four-row table in the docstring
    # applies: three targets move from "refused if present" to "refused if ABSENT", the adapter
    # does not move, and the helper — not this call site — owns both senses.
    if resume_from is None:
        refuse_if_exists(
            arm_bin_targets(arm, paths) + [paths["csv"], paths["checkpoint"], paths["adapter"]]
        )
    else:
        refuse_if_exists(
            [paths["adapter"]],
            expected=arm_bin_targets(arm, paths) + [paths["csv"], paths["checkpoint"]],
        )
        resolved = pathlib.Path(resume_from).resolve()
        if resolved != paths["checkpoint"].resolve():
            raise SystemExit(
                f"[teach_persona] arm {arm!r} was asked to resume from {resolved}, but its OWN "
                f"checkpoint is {paths['checkpoint'].resolve()}. Refusing: a run that continues "
                "one arm's optimizer/RNG state under another arm's name composes privacy across "
                "TWO arms, and the epsilon it would publish describes a composition that never "
                "ran on either — the same defect class _count_composed_steps was written to "
                "catch. Resume each arm from its own latest.pt."
            )

    summary = preflight_device(strict=True)  # CUDA-P100 -> MPS -> CPU raise, BEFORE the run
    print(f"[teach_persona] preflight: {summary}")
    runtime = RuntimeConfig()  # resolves the preflighted device (MPS on the M3, fp32, AMP off)
    if resume_from is not None and is_dp:
        _refuse_cross_device_resume(arm, resume_from, runtime.device)

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
    if is_dp and (not DIALOG_TRAIN_BIN.exists() or not DIALOG_TRAIN_MASK.exists()):
        # Same shape as the val guard above, and for the same reason it is UP HERE: under D-10
        # replay leaves the teaching bin and is drawn at TRAIN time (wiring 3 below), so a missing
        # replay source surfaces inside train()'s replay_fn — after build_arm_bins has already
        # written three bins that refuse_if_exists then treats as recorded evidence, forcing the
        # operator to delete them by hand before retrying.
        raise SystemExit(
            f"[teach_persona] missing {DIALOG_TRAIN_BIN} / {DIALOG_TRAIN_MASK} — a DP arm draws "
            "its PUBLIC replay windows from the PersonaChat TRAIN pair at train time (D-10/D-24). "
            "Run `python scripts/prepare_dialog_corpus.py` first."
        )

    tok, stats, paths = build_arm_bins(
        arm,
        facts,
        family_ids,
        second_person=second_person,
        replay_ratio=replay_ratio,
        adversarial_ratio=adversarial_ratio,
        seed=seed,
        prefix=prefix,
        # Threaded, not defaulted: this is the SECOND caller of `arm_bin_targets`, and a resume
        # that inverted only the guard above would be refused by that one instead.
        resume_from=resume_from,
    )
    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy
    # objects. TRUSTED-only read of the project's OWN checkpoint (T-14-04) — never a foreign
    # file. The SHAREABLE artifact path stays weights_only=True via export_adapter.
    blob = torch.load(CONVBASE_BEST, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])

    # WR-01: the FROZEN Phase-12/13 evaluation policy masks dead ids on every gated
    # `masked_perplexity` call (`finetune_dialog.py:203,214`, `finetune_ab.py:235,246`), and so
    # does `phase14_recall.run_collapse_control` — which is why both reports call the two the
    # same instrument. This call site used to omit it, because the tokenizer was already `del`d
    # by the time the collapse pair was measured. So the mask is built HERE, while `tok` is still
    # alive, and `del tok` moves down: the sweep at the bottom of this function is now literally
    # the D-11.2 instrument rather than a 0.008%-divergent near-twin of it.
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(runtime.device)
    del tok  # the training half needs the bins and the mask, not the tokenizer

    # Re-seed IMMEDIATELY before the GPT build: this seed owns the training data order (the
    # finetune_ab.py provenance note), and the bins build above consumed numpy RNG in its smoke
    # draw. Seeding once at the top would make the data order depend on the bins path. Everything
    # hoisted above it (the checkpoint read, the dead-id mask) consumes no RNG, so the training
    # trajectory is byte-for-byte what it was before the mask was introduced.
    seed_everything(seed)

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

    # ===== D-08 wiring 4: the DP-SGD mechanism, constructed AFTER the freeze =====
    #
    # ORDER IS LOAD-BEARING, twice over.
    #
    # (a) AFTER ``mark_only_lora_trainable(model)`` and the census above, or D-04 refusal 1
    #     (``[dp-refusal:unfrozen-base]``) fires on this caller's own model. ``inject_lora`` does
    #     NOT freeze; omitting that one line noises 14,223,360 parameters against a sensitivity
    #     computed for 331,776. **The census above is NOT redundant with the seam's.** This one is
    #     a property of ONE CALLER, checked once here; the seam re-checks it as a property of the
    #     MECHANISM, so a future caller that forgets the freeze is refused even though this file
    #     never sees it. That is D-04's whole point and it is why both exist.
    # (b) AFTER ``model.to(runtime.device)``, which the plan text does not say and the code
    #     requires: ``DPSGD.__init__`` allocates its accumulator as ``torch.zeros_like(p)`` over
    #     the LIVE trainable params, so constructing before the move would pin the DP-owned sum on
    #     CPU while the params travel to MPS and ``buf.add_(contribution)`` would raise mid-run.
    #
    # ``runtime=`` is passed (not in the plan's literal call) so D-04 refusal 2 is ARMED: an
    # AMP-scaled ``.grad`` read mid-accumulation is wrong by the scale factor, silently. It never
    # bites on cpu/mps — ``RuntimeConfig.__post_init__`` forces ``amp=False`` there — and is the
    # P100 fallback's refusal. ``seed=`` is the run seed, so the noise stream's provenance is
    # greppable rather than an implicit read of ``torch.initial_seed()``.
    dp_fn = (
        DPSGD(
            model,
            sigma=dp_sigma,
            clip_norm=dp_clip_norm,
            device=runtime.device,
            runtime=runtime,
            seed=seed,
        )
        if is_dp
        else None
    )

    # ===== D-08 wirings 1-3: the kwargs the DP arms add to train(), and nothing else adds =====
    #
    # TWO dicts rather than one, keyed on the SAME ``is_dp`` boolean, because ``grad_accum_steps``
    # belongs to the ``TrainConfig`` constructor and the other four to ``train()``. On every
    # non-DP arm both are empty, so every v2.0/v3.0 arm's ``train()`` call is byte-unchanged.
    #
    # ``dict(...)`` and not ``{...}``, deliberately: the entries then read exactly as the KEYWORDS
    # they become at the splat site, and each one is a real ``ast.keyword`` node. That second
    # property is load-bearing and was MEASURED. The first draft of this block used
    # ``{"grad_accum_steps": ...}``, and the 22-08 instrument that re-measures the number baked
    # into ``loop.py``'s refusal message counts code hits by ``ast.keyword``/``Attribute``/``Name``
    # — so against a file that DID wire the value it still read **0 code hits**. A wiring the
    # measurement cannot see is worse than no wiring, because the message stays confidently wrong.
    #
    # WIRING 2 — ``grad_accum_steps``. MEASURED before this plan: the phrase appeared **9 times in
    # this file's PROSE and 0 times in its CODE**, so the ``TrainConfig(...)`` below inherited
    # ``config.py``'s default of ``1`` and SC2's "one micro-step = one privacy record" was prose at
    # the only production caller — the aligned three-bin corpus would have trained at a LOT SIZE OF
    # ONE. ``loop.py``'s accum-agreement refusal (plan 22-08) now makes a disagreement loud, and
    # the value is read from ``stats`` rather than ``len(facts)`` so the accum, the declared lot
    # size and the bin the loader opens all come from the packer's own record count.
    dp_accum = dict(grad_accum_steps=stats["n_facts"]) if is_dp else {}
    dp_kwargs = (
        dict(
            # WIRING 1 — fact-aligned routing. There is NO fact-bin key in ``paths``:
            # ``arm_outputs`` returns exactly {"bin", "mask", "csv", "checkpoint", "adapter"} and
            # ``build_arm_bins`` hands that same dict back. The third bin is DERIVED, by
            # ``fact_bin_path`` — which is also what the packer itself called, so
            # ``stats['fact_bin']`` is the same string — and never
            # a literal at a call site. MEASURED gap this closes: ``get_batch_fact_aligned`` had NO
            # path through ``train()`` at all before plan 22-08 — zero hits for
            # ``fact_bin``/``fact_aligned``/``align_facts`` in ``loop.py`` — and its sole non-test
            # caller was the REPORTING driver ``scripts/phase21_unit_record.py``.
            fact_bin=fact_bin_path(paths["bin"]),
            n_facts=stats["n_facts"],
            # WIRING 3 — the replay seam (Phase 21 D-11/D-24), closing IN-04. Under D-10 replay is
            # NOT in the teaching bin (``arm_spec`` returns ``replay_ratio = 0.0`` for both DP
            # arms, load-bearing); it is drawn here at train time from the PUBLIC PersonaChat pair.
            # UNIT CONVERSION, stated because it is the one thing to get wrong:
            # ``replay_window_budget`` returns TOKENS and ``train()`` wants WINDOWS.
            replay_bin=DIALOG_TRAIN_BIN,
            replay_mask_bin=DIALOG_TRAIN_MASK,
            replay_windows=replay_window_budget(stats["n_facts"]) // BLOCK_SIZE,
            dp_fn=dp_fn,
        )
        if is_dp
        else {}
    )

    final = train(
        train_config=TrainConfig(
            lr=LR,
            warmup_steps=WARMUP_STEPS,
            max_steps=MAX_STEPS,
            batch_size=BATCH_SIZE,
            weight_decay=WEIGHT_DECAY,
            seed=seed,
            **dp_accum,
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
        # THE HOP THAT CLOSES WARNING-2. `train()` needed nothing: resume_from at loop.py:254 has
        # been complete since v1.0 (full state + RNG restore, start_step = ckpt["step"], the
        # three-branch DP-slot matrix). This one keyword is the entire wiring.
        resume_from=resume_from,
        return_final_loss=True,
        **dp_kwargs,
    )

    if is_dp:
        # A DP run whose stdout does not record its budget is a privacy claim with no provenance.
        # ``_clip_bind_count`` is run-lifetime (``begin_step`` deliberately does not reset it), so
        # it reports whether C bound AT ALL across the whole run; ``_records`` is per-step and is
        # therefore the LAST lot's size, which must equal the accum the loop was configured with.
        print(
            f"[teach_persona] DP provenance: arm={arm} sigma={dp_sigma} clip_norm={dp_clip_norm} "
            f"n_facts={stats['n_facts']} grad_accum_steps={stats['n_facts']} "
            f"replay_windows={dp_kwargs['replay_windows']} last_lot_records={dp_fn._records} "
            f"clip_bind_count={dp_fn._clip_bind_count}"
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
        model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device, forbid_ids=forbid
    )
    with adapter_disabled(model):
        ppl_off, scored_off = masked_perplexity(
            model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device, forbid_ids=forbid
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
        f"[teach_persona] run provenance: arm={arm} seed={seed} lr={LR} "
        f"weight_decay={WEIGHT_DECAY} batch_size={BATCH_SIZE} max_steps={MAX_STEPS} "
        f"warmup_steps={WARMUP_STEPS} block_size={BLOCK_SIZE} "
        f"base_fingerprint=(git_sha={blob['git_sha']}, step={blob['step']}, "
        f"val_loss={blob['val_loss']}) driver_git_sha={git_sha()} pid={os.getpid()} "
        f"device={runtime.device} torch={torch.__version__} "
        f"second_person={second_person} replay_ratio={replay_ratio} "
        f"adversarial_ratio={adversarial_ratio} "
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

    CR-02: reads the first ``## Verdict`` SECTION, never the tail after the last occurrence of
    the literal — a prose mention of the heading is not a recorded verdict, and a file with no
    verdict section is refused rather than overwritten blind. Full story at
    ``phase14_recall.assert_report_not_clobbered``.
    """
    if report_path.exists() and not force:
        recorded = recorded_verdict(report_path.read_text(encoding="utf-8"))
        if recorded is None or "PENDING" not in recorded:
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
        "`data/dialog_val.bin` + its mask, block 256, **dead ids forbidden**",
        "(`undecodable_ids_mask`, the frozen Phase-12/13 evaluation policy), adapter ON and OFF",
        "in ONE process on ONE set of weights, so the only difference is the LoRA enabled flag.",
        "It is not a proxy.",
        "",
        "> **WR-01 — the `forbid_ids` argument above was added AFTER this run.** The figures in",
        "> the table below were measured by `train_arm` as originally committed, which omitted",
        "> the dead-id mask; `phase14_recall.run_collapse_control` always passed it. Re-measured",
        "> from the saved calibration adapters under both settings, the divergence is:",
        "> `cal_first_person` +224.8084% unmasked vs +224.5330% masked, `cal_first_person_replay`",
        "> +29.3914% unmasked vs +29.3364% masked. `replay_required` is **True** either way, so",
        "> the D-15 verdict is unchanged. The numbers recorded here are the unmasked ones.",
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
    its rates are the ceiling the thresholds discount, its per-family gains are the allocation
    input, and its ON/OFF PPL pair is the collapse measurement. The replay arm is the PAIRED
    comparison and the second-person arm supplies only the register head-to-head.

    **Known wiring mismatch, corrected post-hoc at plan 14-09's checkpoint — read before
    re-running.** The threshold wiring below assumes the baseline arm is the one whose
    configuration the real run mirrors. That assumption was true when this function was written
    and FALSE once ``replay_required`` returned True on this run's measurements: a True verdict
    sets ``REAL_RUN_REPLAY_RATIO = 1.0``, which makes ``cal_first_person_replay`` the arm the real
    run actually runs under. The committed thresholds in ``phase14_recall`` are therefore derived
    from the REPLAY arm's rates, not from what this function returns — see
    ``results/phase14_calibration_report.md`` ``## Derivation 1``, which shows both sets side by
    side. The wiring is left as-is on purpose: this function is what the committed report records
    having run, and editing a derivation pipeline after seeing its numbers is the move the whole
    pre-registration block exists to prevent. Anyone re-running with ``--force`` must re-decide
    which arm feeds ``lock_thresholds`` at the human checkpoint, exactly as was done here.
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
