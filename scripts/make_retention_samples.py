"""D-12 retention-side qualitative evidence: TinyStories continuations from BOTH A/B arms.

The forgetting curve (VIZ-01) says the naive arm's retention PPL triples while the EWC arm's
barely moves. This script shows what that means in text: the SAME held-out TinyStories
prefixes continued by the naive (λ=0) and EWC (λ=0.01) step-4000 endpoints, written to the
git-TRACKED ``results/phase13_retention_samples.md``.

D-12 protocol — both endpoints are sampled in ONE script run, never two separately curated
passes, over ONE seeded prompt set, with the warm-sampling RNG re-seeded identically before
each arm. There is no point at which an arm could be re-rolled for a better-looking output.

Measured over ALL generations (the Phase-12 transcript proxies, applied to the retention axis):

  (a) stop-id termination fraction — completions halting on eos (8184) vs max_new_tokens.
      Story mode uses ``stop_ids={8184}`` ONLY: ``<|user|>`` is a legitimate stop for a
      dialogue transcript but here its appearance is the very thing being measured.
  (b) mid-generation role-token leakage — count of ids 8185/8186/8187 in the generated ids.
      Role tokens mid-STORY are dialogue contamination of the base task: exactly the
      forgetting axis, so the expected value is 0 and any nonzero count is reportable.

Prompts are NEVER hand-formatted strings (inflation-report Pitfall 4): each is the first 32
ids of a held-out ``TinyStoriesV2-GPT4-valid.txt`` story, encoded through the FROZEN
tokenizer, so it tokenizes exactly as the pretraining corpus did.

SECURITY: ``torch.load(weights_only=False)`` reads ONLY the project's OWN Phase-13 arm
checkpoints (trusted-only — this repo's ``scripts/finetune_ab.py`` wrote them, T-12-10).

Run: ``python scripts/make_retention_samples.py`` (inside the Python 3.11 venv, on the M3).
"""

import os
import pathlib

import numpy as np

# An uncovered MPS op falls back to CPU rather than crashing — set BEFORE importing torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.generation.core import collect  # noqa: E402
from personacore.generation.text import undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
VALID_TXT = _REPO_ROOT / "data" / "TinyStoriesV2-GPT4-valid.txt"  # held-out pretrain split
SAMPLES_PATH = _REPO_ROOT / "results" / "phase13_retention_samples.md"  # git-TRACKED evidence

# Both step-4000 arm endpoints, loaded in THIS one run (D-12). Fixed order: naive first, so
# the file reads as "unconstrained baseline, then the mitigation".
ARMS = (
    ("naive (λ=0)", _REPO_ROOT / "checkpoints" / "phase13_naive_latest.pt"),
    ("ewc (λ=0.01)", _REPO_ROOT / "checkpoints" / "phase13_ewc_latest.pt"),
)

N_PROMPTS = 10
SEED = 1337  # seeded LOCAL prompt selection + seeded warm sampling, re-seeded per arm
PROMPT_TOKENS = 32  # prefix length: enough to fix a story's characters and setting
MAX_NEW_TOKENS = 128
STOP_IDS = {8184}  # eos ONLY — story mode; a <|user|> turn here is a measurement, not a stop
ROLE_IDS = (8185, 8186, 8187)  # <|user|> / <|assistant|> / <|system|> — leakage check set
DOC_SEP = "<|endoftext|>"


def _complete(model, prompt_ids, device, forbid, **kw):
    """One completion: returns (generated_ids, stopped_on_stop_id)."""
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = collect(
        model,
        idx,
        max_new_tokens=MAX_NEW_TOKENS,
        forbid_ids=forbid,
        stop_ids=STOP_IDS,
        **kw,
    )
    gen = out[0, len(prompt_ids) :].tolist()
    # generate() stops WITHOUT yielding the stop id (D-05): fewer than max_new_tokens
    # generated tokens means a stop-id termination.
    return gen, len(gen) < MAX_NEW_TOKENS


def _build_prompts(tok):
    """The pre-registered shared prompt set: N_PROMPTS held-out story prefixes as id lists."""
    text = VALID_TXT.read_text(encoding="utf-8")
    # [1:] drops the leading fragment — the file opens mid-story, before the first separator.
    stories = [s.strip() for s in text.split(DOC_SEP)[1:]]
    stories = [s for s in stories if s]

    rng = np.random.default_rng(SEED)  # seeded LOCAL rng — global streams untouched
    picks = sorted(int(i) for i in rng.choice(len(stories), size=N_PROMPTS, replace=False))

    prompts = []
    for i in picks:
        # allowed_special="none": a held-out story is DATA, so a literal "<|endoftext|>" inside
        # it must byte-split rather than become an atomic id in the prompt.
        ids = tok.encode(stories[i], allowed_special="none")[:PROMPT_TOKENS]
        prompts.append((i, ids))
    return prompts


def _load_arm(path, device):
    """Reconstruct one arm's step-4000 endpoint model from its own embedded config."""
    # weights_only=False: TRUSTED-only read of the project's OWN arm checkpoint (T-12-10).
    blob = torch.load(path, weights_only=False, map_location="cpu")
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(device)
    model.eval()
    return model, model_cfg, int(blob["step"])


def main() -> None:
    if SAMPLES_PATH.exists():
        # WR-02 refuse-to-rerun: these samples are RECORDED evidence for the A/B report. A
        # silent overwrite on drifted checkpoints would swap the text under the report's
        # claims. Fail loud naming the offender.
        raise SystemExit(
            f"[make_retention_samples] {SAMPLES_PATH} already exists — the samples are "
            "recorded evidence. Delete it to regenerate."
        )
    for _label, path in ARMS:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run `python scripts/finetune_ab.py {path.stem.split('_')[1]}` "
                "first."
            )
    if not VALID_TXT.exists():
        raise FileNotFoundError(f"Missing {VALID_TXT} (held-out TinyStories validation split).")

    summary = preflight_device(strict=True)
    print(f"[make_retention_samples] preflight: {summary}")
    device = RuntimeConfig().device

    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — the pretraining tokenizer
    prompts = _build_prompts(tok)
    print(f"[make_retention_samples] {len(prompts)} seeded prompts: {[i for i, _ in prompts]}")

    completions = {}  # (arm_label, story_idx) -> (greedy_text, warm_text)
    proxies = {}  # arm_label -> (n_stopped, n_completions, leakage, step)
    for label, ckpt_path in ARMS:
        model, model_cfg, step = _load_arm(ckpt_path, device)
        # .to(device): the sampling path masked_fills logits in place on the model device.
        forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(device)

        # Re-seeded per arm, NOT once for the run: both arms then draw warm samples from the
        # IDENTICAL RNG stream, so a text difference is a weight difference (D-12).
        seed_everything(SEED)
        n_stopped = n_completions = leakage = 0
        for story_idx, prompt_ids in prompts:
            greedy_ids, g_stop = _complete(model, prompt_ids, device, forbid, greedy=True)
            warm_ids, w_stop = _complete(
                model, prompt_ids, device, forbid, temperature=0.8, top_p=0.95
            )
            n_stopped += g_stop + w_stop
            n_completions += 2
            leakage += sum(t in ROLE_IDS for t in greedy_ids + warm_ids)
            completions[(label, story_idx)] = (tok.decode(greedy_ids), tok.decode(warm_ids))
            print(
                f"[make_retention_samples] {label} story {story_idx}: "
                f"greedy stop={g_stop} warm stop={w_stop}"
            )

        proxies[label] = (n_stopped, n_completions, leakage, step)
        del model
        print(f"[make_retention_samples] {label} done: {n_stopped}/{n_completions} stopped")

    lines = [
        "# PersonaCore — Phase-13 Retention-Side Samples (DEMO-04 / D-12)",
        "",
        "> These continuations are REPRESENTATIVE, not cherry-picked. Both step-4000 arm",
        "> endpoints were sampled in ONE run of `scripts/make_retention_samples.py` over ONE",
        "> shared prompt set: 10 held-out `TinyStoriesV2-GPT4-valid.txt` stories chosen with a",
        "> seeded local `default_rng(1337)`, each encoded through the FROZEN tokenizer and",
        "> truncated to its first 32 ids — never a hand-formatted string. The warm-sampling RNG",
        "> is re-seeded to 1337 before EACH arm, so both arms draw from the identical stream and",
        "> a text difference is a weight difference. Decoding: `stop_ids={8184}` (eos only —",
        "> story mode), dead ids forbidden, 128 new tokens. The proxies below are measured over",
        "> ALL 40 generations, not over the excerpts shown.",
        "",
        "## Adherence Proxies (measured over all generations, per arm)",
        "",
        "| arm | endpoint step | stop-id (eos) termination "
        "| mid-story role-token leakage (8185/8186/8187) |",
        "| --- | --- | --- | --- |",
    ]
    for label, _path in ARMS:
        n_stopped, n_completions, leakage, step = proxies[label]
        lines.append(
            f"| {label} | {step} | **{n_stopped}/{n_completions} = "
            f"{n_stopped / n_completions:.2f}** | **{leakage}** (0 = uncontaminated) |"
        )
    lines += [
        "",
        "Role tokens mid-story are dialogue contamination of the base task — the forgetting",
        "axis itself, which is why leakage is reported per arm rather than pooled. **Both arms",
        "leak heavily**: after 4000 full-fine-tune steps on PersonaChat, free-running generation",
        "from a TinyStories prefix drops into dialogue in both arms, so the retention-PPL gap",
        "the forgetting curve reports does NOT translate into an intact story-mode generator",
        "here. Teacher-forced retention PPL (what the pre-registered gate measures) and",
        "free-running mode adherence (what these proxies measure) are different quantities;",
        "this file reports both as measured. Interpretation belongs to the A/B report.",
        "",
        "A 0.00-0.05 stop-id fraction is expected and is not an adherence failure: 128 new",
        "tokens is well short of a full TinyStories story, so nearly every completion is",
        "budget-truncated rather than eos-terminated.",
        "",
    ]

    for story_idx, prompt_ids in prompts:
        lines += [
            f"## Prompt {story_idx} (first {PROMPT_TOKENS} ids of a held-out story)",
            "",
            f"> {tok.decode(prompt_ids)}",
            "",
        ]
        for label, _path in ARMS:
            greedy, warm = completions[(label, story_idx)]
            lines += [
                f"### {label}",
                "",
                "**Greedy (deterministic):**",
                "",
                f"> {greedy}",
                "",
                "**Warm (temperature=0.8, top_p=0.95, seeded):**",
                "",
                f"> {warm}",
                "",
            ]

    SAMPLES_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[make_retention_samples] wrote {SAMPLES_PATH}")


if __name__ == "__main__":
    main()
