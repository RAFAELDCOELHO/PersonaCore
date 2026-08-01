"""Curated-transcript generator for the conversational base (Phase 12 Plan 05: TUNE-01).

Generates 15 held-out PersonaChat transcripts through the Phase-11 serialize path and writes
``results/transcripts.md`` (the git-TRACKED ``samples.md`` register) with measurable
dialogue-format-adherence proxies alongside the text:

  (a) stop-id termination fraction — completions halting on {8184, 8185} vs max_new_tokens
  (b) mid-generation role-token leakage — count of ids 8185/8186/8187 in generated tokens
      (expected 0: <|user|> is a stop, <|assistant|>/<|system|> mid-reply means format broken)
  (c) the final masked dialogue val PPL of ``convbase_best.pt`` (frozen gate policy)

Prompts are NEVER hand-formatted strings (inflation-report Pitfall 4): each prompt is the
episode's ``encode_dialogue`` id sequence — persona (capped exactly as the bins were) + the
first user turn — truncated to END at the ``<|assistant|>`` id 8186, so the model completes
the assistant turn from ids that tokenize identically to its training bins.

SECURITY: ``torch.load(weights_only=False)`` reads ONLY the project's OWN
``checkpoints/convbase_best.pt`` (trusted-only — this repo's driver wrote it).

Run: ``python scripts/make_transcripts.py`` (inside the Python 3.11 venv, on the M3).
"""

import os
import pathlib

import numpy as np

# An uncovered MPS op falls back to CPU rather than crashing — set BEFORE importing torch.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.dialogue import (  # noqa: E402
    cap_persona,
    detokenize,
    encode_dialogue,
    parse_episodes,
)
from personacore.evaluation import masked_perplexity  # noqa: E402
from personacore.generation.core import collect  # noqa: E402
from personacore.generation.text import undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted checkpoint
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
VALID_TXT = _REPO_ROOT / "data" / "raw" / "personachat" / "valid_self_revised.txt"  # held-out
DIALOG_VAL = _REPO_ROOT / "data" / "dialog_val.bin"
DIALOG_VAL_MASK = _REPO_ROOT / "data" / "dialog_val_mask.bin"
TRANSCRIPTS_PATH = _REPO_ROOT / "results" / "transcripts.md"  # git-TRACKED evidence

N_TRANSCRIPTS = 15  # 10-20 target (TUNE-01)
SEED = 1337  # seeded LOCAL episode selection + seeded warm sampling
MAX_NEW_TOKENS = 128
STOP_IDS = {8184, 8185}  # eos + <|user|> — decoding halts on a hallucinated user turn (12-02)
ROLE_IDS = (8185, 8186, 8187)  # <|user|> / <|assistant|> / <|system|> — leakage check set
ASSISTANT_ID = 8186  # the prompt MUST end here (the model completes the assistant turn)
BLOCK_SIZE = 256  # ModelConfig.block_size — the masked_perplexity sweep window
# Persona capping: the SHARED personacore.dialogue.cap_persona (the bin builder's exact
# function), so transcript prompts tokenize identically to the bins by construction (Pitfall 4).


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


def main() -> None:
    if not CONVBASE_BEST.exists():
        raise FileNotFoundError(
            f"Missing {CONVBASE_BEST}. Run `python scripts/finetune_dialog.py` first."
        )
    if not VALID_TXT.exists():
        raise FileNotFoundError(
            f"Missing {VALID_TXT}. Run `python scripts/fetch_personachat.py` first."
        )
    for path in (DIALOG_VAL, DIALOG_VAL_MASK):
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run `python scripts/prepare_dialog_corpus.py` first."
            )

    summary = preflight_device(strict=True)
    print(f"[make_transcripts] preflight: {summary}")
    runtime = RuntimeConfig()
    device = runtime.device

    # weights_only=False: TRUSTED-only read of the project's OWN checkpoint (T-12-10).
    blob = torch.load(CONVBASE_BEST, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(device)
    model.eval()

    tok = from_json(TOKENIZER_PATH)
    # .to(device): next_token masked_fills logits in place on the model device (evaluation
    # moves the mask itself; the sampling path does not — same-device is on the caller).
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(device)

    # (c) final masked dialogue val PPL — the frozen gate policy (smoke report §1).
    dialog_ppl, dialog_tokens = masked_perplexity(
        model, DIALOG_VAL, DIALOG_VAL_MASK, BLOCK_SIZE, device, forbid_ids=forbid
    )
    print(f"[make_transcripts] masked dialogue val PPL {dialog_ppl:.4f} over {dialog_tokens:,}")

    episodes = parse_episodes(VALID_TXT)  # held-out split — never trained on
    rng = np.random.default_rng(SEED)  # seeded LOCAL rng — global streams untouched
    picks = sorted(int(i) for i in rng.choice(len(episodes), size=N_TRANSCRIPTS, replace=False))

    seed_everything(SEED)  # seeded warm sampling (deterministic transcript re-runs)
    blocks = []
    n_stopped = 0
    n_completions = 0
    leakage = 0
    for i in picks:
        persona, turns = episodes[i]
        kept = cap_persona(tok, persona)
        ids, _mask = encode_dialogue(tok, kept, turns)
        # Prompt = persona + first user turn, truncated to END at <|assistant|> (8186) —
        # the id sequence tokenizes identically to the bins (Pitfall 4).
        prompt_ids = ids[: ids.index(ASSISTANT_ID) + 1]

        greedy_ids, g_stop = _complete(model, prompt_ids, device, forbid, greedy=True)
        warm_ids, w_stop = _complete(model, prompt_ids, device, forbid, temperature=0.8, top_p=0.95)
        n_stopped += g_stop + w_stop
        n_completions += 2
        leakage += sum(t in ROLE_IDS for t in greedy_ids + warm_ids)

        blocks += [
            f"## Episode {i}",
            "",
            f"**Persona:** {'; '.join(detokenize(p) for p in kept)}",
            "",
            f"**User:** {detokenize(turns[0][0])}",
            "",
            "**Greedy (deterministic):**",
            "",
            f"> {detokenize(tok.decode(greedy_ids))}",
            "",
            "**Warm (temperature=0.8, top_p=0.95, seeded):**",
            "",
            f"> {detokenize(tok.decode(warm_ids))}",
            "",
        ]
        print(f"[make_transcripts] episode {i}: greedy stop={g_stop} warm stop={w_stop}")

    stop_frac = n_stopped / n_completions
    header = [
        "# PersonaCore — Conversational-Base Transcripts (TUNE-01)",
        "",
        "> These transcripts are REPRESENTATIVE, not cherry-picked: episodes are drawn from",
        "> the held-out PersonaChat valid split with a seeded rng (default_rng(1337)). Each",
        "> prompt is the episode's `encode_dialogue` id sequence (persona + first user turn),",
        "> truncated to end at the `<|assistant|>` id — never a hand-formatted string — so",
        "> prompts tokenize identically to the training bins. Decoding uses",
        "> `stop_ids={8184, 8185}` (eos + `<|user|>`) with dead ids forbidden, 128 new tokens.",
        "",
        "## Adherence Proxies (measured over all generations)",
        "",
        f"- Stop-id termination fraction: **{n_stopped}/{n_completions} = {stop_frac:.2f}**",
        f"- Mid-generation role-token leakage (ids 8185/8186/8187): **{leakage}** (expected 0)",
        f"- Final masked dialogue val PPL (convbase_best, frozen gate policy): "
        f"**{dialog_ppl:.4f}** over {dialog_tokens:,} assistant tokens",
        "",
    ]
    TRANSCRIPTS_PATH.write_text("\n".join(header + blocks), encoding="utf-8")
    print(
        f"[make_transcripts] wrote {TRANSCRIPTS_PATH}: {len(picks)} episodes, "
        f"stop fraction {stop_frac:.2f}, leakage {leakage}"
    )


if __name__ == "__main__":
    main()
