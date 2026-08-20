"""UNPINNED driver for Phase 20 — the ONE measurement `scripts/mitigation_gate.py` cannot make.

`scripts/mitigation_gate.py` is the v4.0 pre-registration and it is CLOSED. D-06 needs a number the
pin does not have: `V20_RETENTION_NOISE_FLOOR = 0.068930` is a **Phase 12 FULL-FINE-TUNE** seed pair
governing an adapter-regime verdict, and the adapter-regime floor that should govern it has never
been committed anywhere. Measuring it requires MPS, two gitignored adapters and roughly an hour of
compute, so it cannot live in the CPU-only suite either.

**WHY THIS IS A SEPARATE FILE, AND WHY THAT IS NOT A LOOPHOLE.** The measurement below produces
`results/phase20_retention_floor.json`. `tests/test_phase20_prereg.py`'s
`test_phase20_prereg_is_frozen_before_every_phase20_result` requires every commit touching
`scripts/mitigation_gate.py` to be an ancestor of every `results/phase20_*` artifact's earliest add.
Writing this driver into the pin would therefore make the pin a NON-ANCESTOR of the artifact it
produced and turn that guard permanently RED, with no recovery: the guard takes `adds[-1]`, the
EARLIEST add, so a delete-and-re-add cycle cannot launder the ordering (measured in a throwaway repo
across five observed states, plan 20-03). This file is watched by no ancestry guard because
`V4_ARTIFACT_GLOBS` is `("results/phase20_*",)` — it watches results, not `scripts/`. The split is
the same one `scripts/phase19_floor.py:10-48` records, arrived at for the same measured reason.

**THE IMPORT PROPERTY, STATED EXACTLY AND NO WIDER.** THIS DRIVER'S OWN torch / numpy / personacore
imports are FUNCTION-LOCAL. `import phase19_erasure as pin` is the single module-scope import that
DOES pull torch, transitively, at `scripts/phase19_erasure.py:120` — so "the module stays inert at
import" would be FALSE and is not claimed. That transitive cost is ACCEPTED deliberately: it buys
`RETENTION_BIN`, `JSON_INDENT`, `ModelConfig.block_size`, `V20_EWC_RETENTION_PPL`, `MARGIN_K` and
`V20_RETENTION_NOISE_FLOOR` read from the pinned module instead of retyped here, and a retyped
double is a wrong double.

    python scripts/phase20_run.py retention-floor    # 20-07 task 3
"""

import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import phase19_erasure as pin  # noqa: E402  — after the path insert, like every phase19 driver

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# D-08's artifact. Committed STRICTLY AFTER `scripts/mitigation_gate.py` is committed AND pushed —
# a discipline tighter than the mechanism, because `git merge-base --is-ancestor` is reflexive and
# would pass on a same-commit pair.
RETENTION_FLOOR_PATH = _REPO_ROOT / "results" / "phase20_retention_floor.json"

# The two committed dialogue-floor arms, in ascending seed order. Built FROM the seed rather than
# typed twice, so the seed in the key and the seed in the filename cannot drift apart.
SEED_ADAPTERS = {
    seed: _REPO_ROOT / "checkpoints" / f"phase19_erase_dialogue_floor_seed{seed}_adapter.pt"
    for seed in (1337, 2024)
}

# THE BIT-IDENTITY CONTROL's expected values, all three from `results/phase19_noise_floors.json`'s
# `retention_ppl_pre_erasure` block. That block was measured on a DIFFERENT FILE
# (`checkpoints/persona_adapter.pt`), which is what makes reproducing it a control rather than a
# tautology: the same instrument, the same corpus, an independently written adapter.
PUBLISHED_SEED_1337 = {
    "adapter_off": 3.891139975617828,  # phase19_noise_floors.json retention_ppl_pre_erasure
    "adapter_on": 4.219759892336485,  # phase19_noise_floors.json retention_ppl_pre_erasure
    "n_scored_tokens": 1000285,  # phase19_noise_floors.json retention_ppl_pre_erasure
}

# D-06's SECOND stated bound, as machine-readable data rather than as prose beside the number: this
# floor is measured on the v3.0 persona recipe — the right REGIME, not a v4.0 ARM. Mirrors
# `results/phase19_dialogue_floor.json`'s `recipe` exactly, and `retention_floor()` PROVES that
# equality against the committed record rather than trusting this transcription.
RECIPE = {
    "arm_spec": "real",
    "arms": ["erase_dialogue_floor_seed1337", "erase_dialogue_floor_seed2024"],
    "n_facts": 10,
    "prefix": "phase19",
    "replay_ratio": 1.0,
    "second_person": False,
}

DIALOGUE_FLOOR_RECORD = _REPO_ROOT / "results" / "phase19_dialogue_floor.json"


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _refuse(path):
    if pathlib.Path(path).exists():
        raise SystemExit(
            f"[phase20_run] {path} already exists — it is recorded evidence and there is no force "
            "flag. Delete it in a reviewed commit if it genuinely must be regenerated."
        )


def retention_floor():
    """20-07 task 3 — the ADAPTER-REGIME retention noise floor, with its bit-identity control.

    Two seeds, no retraining of any kind: the two committed `erase_dialogue_floor_seed*` adapters
    are re-read with a second instrument, which is the legitimacy D-13 granted the original
    retention probe. Seed 1337 must reproduce the published reading EXACTLY before seed 2024 is
    measured at all.
    """
    # FIRST, before a single tensor is loaded: an hour of MPS is not spent to discover afterwards
    # that the output path is already occupied.
    _refuse(RETENTION_FLOOR_PATH)

    import numpy as np
    import phase14_recall as recall
    import torch

    from personacore.evaluation.perplexity import retention_perplexity
    from personacore.lora import adapter_disabled
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha

    # A retyped recipe is a wrong recipe. The D-06 regime bound travels inside this artifact, so it
    # is PROVED equal to the committed record it mirrors instead of being trusted.
    committed_recipe = json.loads(DIALOGUE_FLOOR_RECORD.read_text(encoding="utf-8"))["recipe"]
    if committed_recipe != RECIPE:
        raise SystemExit(
            f"[phase20_run] RECIPE disagrees with {DIALOGUE_FLOOR_RECORD.name}: "
            f"{RECIPE!r} vs {committed_recipe!r}. The v3.0-recipe bound this artifact publishes "
            "would then describe a regime these adapters were not taught under."
        )

    device = preflight_device(strict=True)["device"]
    block_size = pin.ModelConfig.block_size
    readings = {}

    for seed, adapter_path in SEED_ADAPTERS.items():
        # The fourth return is `forbid` and it is DISCARDED — `retention_perplexity` takes a
        # TOKENIZER and builds its own dead-id mask internally (`perplexity.py:165-170`). Passing
        # `forbid` would land in the `batch_size` slot and silently corrupt the reading. This is
        # `scripts/phase19_run.py:803`, copied rather than re-derived.
        model, cfg, tok, _forbid, _artifact = recall.load_adapted_model(device, str(adapter_path))

        on_ppl, on_tokens = retention_perplexity(model, pin.RETENTION_BIN, block_size, device, tok)
        with adapter_disabled(model):
            off_ppl, off_tokens = retention_perplexity(
                model, pin.RETENTION_BIN, block_size, device, tok
            )
        if on_tokens != off_tokens:
            raise SystemExit(
                f"[phase20_run] seed {seed} on/off denominators differ ({on_tokens} vs "
                f"{off_tokens}) — the delta would measure the corpus rather than the adapter."
            )

        # THE WINDOW ACCOUNTING, checked rather than quoted (`scripts/phase19_run.py:814-826`).
        # Consecutive windows SHARE their boundary token, so every target 1..n-1 is scored exactly
        # once and the denominator is `n - 1`.
        n_corpus = len(np.memmap(pin.RETENTION_BIN, dtype=np.uint16, mode="r"))
        n_windows = len(range(0, n_corpus - 1, block_size))
        if n_corpus - 1 != on_tokens:
            raise SystemExit(
                f"[phase20_run] seed {seed} window accounting disagrees: {n_corpus} - 1 != "
                f"{on_tokens} over {n_windows} windows at block {block_size}"
            )

        readings[seed] = {
            "adapter": str(adapter_path.relative_to(_REPO_ROOT)),
            "adapter_sha256": _sha256(adapter_path),
            "adapter_off": off_ppl,
            "adapter_on": on_ppl,
            "delta_on_minus_off": on_ppl - off_ppl,
            "n_scored_tokens": on_tokens,
            "n_windows": n_windows,
            "seed": seed,
        }

        # THE BIT-IDENTITY CONTROL, placed here rather than after the loop so it runs BEFORE the
        # seed-2024 reading is taken at all — not merely before it is published. Exact `==`, no
        # tolerance: a floor is a difference between two readings, and a tolerance wide enough to
        # admit an instrument drift is wide enough to hide the whole floor.
        if seed == 1337:
            measured = {k: readings[seed][k] for k in PUBLISHED_SEED_1337}
            if measured != PUBLISHED_SEED_1337:
                raise SystemExit(
                    f"[phase20_run] BIT-IDENTITY CONTROL FAILED. Seed 1337 measured {measured!r} "
                    f"against the published {PUBLISHED_SEED_1337!r} "
                    "(results/phase19_noise_floors.json retention_ppl_pre_erasure). This control "
                    "exists so the instrument is VERIFIED, not assumed: a seed-2024 number "
                    "produced by an unverified instrument has no provenance at all, because "
                    "nothing would distinguish a real regime difference from a changed "
                    "measurement path. Seed 2024 was NOT measured and nothing was written. STOP "
                    "and report — do not widen a tolerance."
                )

    a, b = readings[1337], readings[2024]
    floor = abs(a["delta_on_minus_off"] - b["delta_on_minus_off"])
    # Read through `pin` so the anchor is the IMPORTED 3.891140, never the measured
    # 3.891139975617828 — the cap must be the pinned rule's output, not this run's rounding.
    cap = pin.V20_EWC_RETENTION_PPL + pin.MARGIN_K * floor
    published_adapter = recall.ADAPTER_PATH

    artifact = {
        "adapter_off_identical_across_seeds": a["adapter_off"] == b["adapter_off"],
        "bin": str(pin.RETENTION_BIN.relative_to(_REPO_ROOT)),
        "bin_bytes": pin.RETENTION_BIN.stat().st_size,
        "block_size": block_size,
        "borrowed_cap": pin.V20_EWC_RETENTION_PPL + pin.MARGIN_K * pin.V20_RETENTION_NOISE_FLOOR,
        "borrowed_floor": pin.V20_RETENTION_NOISE_FLOOR,
        "borrowed_floor_ratio": pin.V20_RETENTION_NOISE_FLOOR / floor,
        "bounds": (
            "TWO BOUNDS, STATED NOT GLOSSED. (1) n = 2 seeds. The floor above is ONE DIFFERENCE "
            "BETWEEN TWO DRAWS and carries NO confidence interval — exactly the status the "
            "committed `dialogue_ppl_noise_floor` (0.005214448168350039, also n = 2) already has, "
            "stated here rather than inherited silently. (2) It is measured on the V3.0 PERSONA "
            "RECIPE (`recipe` above: n_facts = 10, replay_ratio = 1.0, arm_spec 'real', "
            "second_person false), which is the right REGIME — LoRA adapters over the same base, "
            "same corpus, same instrument — but NOT a v4.0 ARM. A v4.0 mitigation arm may differ "
            "in facts, replay or steps, and this floor is not evidence about that. Both bounds "
            "are why D-07 keeps the floor a REQUIRED KEYWORD ARGUMENT of "
            "`scripts/mitigation_gate.py::retention_cap` instead of a literal inside it: a caller "
            "must state which floor it is asserting, and a better-bounded measurement can replace "
            "this one without editing the closed pin."
        ),
        "call": f"retention_perplexity(model, RETENTION_BIN, {block_size}, device, tok)",
        "cap": cap,
        "cap_derivation": (
            f"{pin.V20_EWC_RETENTION_PPL} + {pin.MARGIN_K} x {floor} (scripts/erasure_gate.py:246)"
        ),
        "corpus_tokens": a["n_scored_tokens"] + 1,
        "device": str(device),
        "driver": "scripts/phase20_run.py retention-floor (UNPINNED)",
        "git_sha": git_sha(),
        "governs": (
            "the MEASURED adapter-regime floor above is what the v4.0 gate reads: it is the "
            "`retention_noise_floor` keyword argument of "
            "`scripts/mitigation_gate.py::retention_cap`, which has NO default and therefore "
            "cannot silently fall back to anything. `V20_RETENTION_NOISE_FLOOR = 0.068930` is the "
            "PHASE 12 FULL-FINE-TUNE reading published beside it for the method it supplied, and "
            "it does NOT govern any v4.0 verdict. This mirrors the statement "
            "`results/phase19_noise_floors.json` already makes about the full-fine-tune DIALOGUE "
            "floor 0.001704. NOTE, and it is not a contradiction: `scripts/erasure_gate.py`'s own "
            "`retention_cap` (`:246`) still computes with 0.068930, and that is CORRECT and "
            "DELIBERATE — it is the Phase 19 gate, its verdicts are already published, and this "
            "artifact is NOT a correction to commit 23a830c. That commit must not be amended. "
            "Phase 19 read a full-fine-tune floor; v4.0 reads the measured adapter-regime one."
        ),
        "n_scored_tokens": a["n_scored_tokens"],
        "n_windows": a["n_windows"],
        "recipe": RECIPE,
        "recipe_source": "results/phase19_dialogue_floor.json (proved equal at run time)",
        "retention_ppl": {str(seed): readings[seed] for seed in SEED_ADAPTERS},
        "retention_ppl_noise_floor": floor,
        "seed_1337_remeasured_vs_published": {
            "abs_delta": abs(a["adapter_on"] - PUBLISHED_SEED_1337["adapter_on"]),
            "adapter_off_abs_delta": abs(a["adapter_off"] - PUBLISHED_SEED_1337["adapter_off"]),
            "bit_identical": all(a[k] == v for k, v in PUBLISHED_SEED_1337.items()),
            "control_is_across_two_distinct_files": _sha256(published_adapter)
            != _sha256(SEED_ADAPTERS[1337]),
            "measured_adapter_off": a["adapter_off"],
            "measured_adapter_on": a["adapter_on"],
            "measured_n_scored_tokens": a["n_scored_tokens"],
            "published_adapter": str(published_adapter.relative_to(_REPO_ROOT)),
            "published_adapter_off": PUBLISHED_SEED_1337["adapter_off"],
            "published_adapter_on": PUBLISHED_SEED_1337["adapter_on"],
            "published_adapter_sha256": _sha256(published_adapter),
            "published_n_scored_tokens": PUBLISHED_SEED_1337["n_scored_tokens"],
            "source": "results/phase19_noise_floors.json retention_ppl_pre_erasure",
            "tolerance": "NONE — exact `==` on all three values, enforced by SystemExit before "
            "seed 2024 was measured at all. The published block was measured on "
            "checkpoints/persona_adapter.pt, a different file from the seed-1337 arm adapter "
            "scored here (both digests above), so agreement is a control over the instrument "
            "rather than a re-read of the same bytes.",
        },
        "seeds": list(SEED_ADAPTERS),
        "torch": torch.__version__,
    }

    for key in ("retention_ppl_noise_floor", "cap", "borrowed_cap", "borrowed_floor_ratio"):
        print(f"[phase20_run] retention-floor {key} = {artifact[key]!r}")
    for seed in SEED_ADAPTERS:
        r = readings[seed]
        print(
            f"[phase20_run] seed {seed}: off = {r['adapter_off']!r}  on = {r['adapter_on']!r}  "
            f"gap = {r['delta_on_minus_off']!r}  n = {r['n_scored_tokens']}"
        )
    RETENTION_FLOOR_PATH.write_text(
        json.dumps(artifact, indent=pin.JSON_INDENT, sort_keys=True), encoding="utf-8"
    )
    print(f"[phase20_run] wrote {RETENTION_FLOOR_PATH}")


_TABLE = {"retention-floor": retention_floor}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in _TABLE:
        raise SystemExit(f"usage: python scripts/phase20_run.py {{{'|'.join(_TABLE)}}}")
    _TABLE[sys.argv[1]]()
