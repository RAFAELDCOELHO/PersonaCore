"""Offline Gradio story-completion demo — the live on-device proof (DEMO-01).

Thin wiring only (Phase-1 D-04): the tested logic (``generate_text_cumulative``) lives in
``src/personacore``; this script loads the FROZEN artifacts (``checkpoints/model_slim.pt``,
``artifacts/tokenizer.json``) and binds them to a ``gr.ChatInterface``. No CLI flag parsing —
all paths are ``_REPO_ROOT``-relative constants.

Run: ``python scripts/demo_app.py`` → http://127.0.0.1:7860 on a laptop CPU.

OFFLINE GUARANTEE: zero outbound network calls. ``GRADIO_ANALYTICS_ENABLED=False`` is set
BEFORE ``import gradio`` (kills telemetry AND the version-check HTTP ping — 08-RESEARCH
Pitfall 5), ``analytics_enabled=False`` is passed too (belt and braces), and ``share=False``
binds localhost with no tunnel binary download. The default Gradio look is the ONLY
offline-verified configuration (wheel-bundled local fonts, no CDN) — no customization of any
kind (08-UI-SPEC hard rule). The UI must load and stream with Wi-Fi off.

HONEST FRAMING (D-02): this is TinyStories STORY COMPLETION by the Milestone-1 base model —
not a tuned chatbot. Each message starts a FRESH story: history is never concatenated into
the prompt (zero dialogue tuning; concatenation would produce incoherence and overclaim chat
ability). No chat-tuning or weight-memory claims are made for M1.

SECURITY: the slim checkpoint loads through ``load_slim`` — ``torch.load`` under
``weights_only=True``, the restricted unpickler with ZERO code execution on load (T-08-01).
``tokenizer.json`` is a data-only JSON artifact. The existing (0, 4096] ``max_new_tokens``
guard (T-06-04) backs the slider bound. Tokenizer-undecodable ids are masked from the logits
before sampling (``forbid_ids``), so every slider setting the UI offers is safe (CR-01).
"""

import os
import pathlib

# Kill Gradio telemetry + the startup version-check ping BEFORE the import it affects
# (08-RESEARCH Pitfall 5) — this line must precede `import gradio`.
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr  # noqa: E402  (must follow the analytics kill-switch above)

from personacore.checkpoint import load_slim  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.generation import generate_text_cumulative, undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SLIM_PATH = _REPO_ROOT / "checkpoints" / "model_slim.pt"  # shippable inference artifact (DEMO-02)
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN production artifact

TITLE = "PersonaCore — TinyStories story completion (13.9M params, fully on-device)"
DESCRIPTION = (
    "A from-scratch GPT running on your CPU — no internet, no API, no database. "
    "Type a story opening and the model continues it. Each message starts a fresh story "
    "(previous turns are not fed back in). This is the Milestone-1 base model: no chat "
    "tuning, no personalization yet — that's Milestone 2."
)
# List-of-lists: gradio 5.50.0 requires this shape when additional_inputs are present
# (each inner list is [message] — slider values fall back to their defaults on click).
EXAMPLES = [
    ["Once upon a time, there was a little dog named Max."],
    ["One day, a little girl named Lily found a shiny stone."],
    ["Tom and his cat went to the park to play."],
]
MISSING_CKPT_MSG = (
    "checkpoints/model_slim.pt not found. Either download the release asset (see README "
    "quickstart) or regenerate it from a local best.pt: python scripts/export_slim.py"
)


def build_demo() -> gr.ChatInterface:
    """Construct the ChatInterface (lazy: importing this module loads NO model — tests/CI safe).

    Loads the slim checkpoint via the ``weights_only=True`` choke point, rebuilds the model
    from its embedded config, pins it to CPU (DEMO-01 says laptop CPU — device resolution must
    never drift to MPS), and wires the cumulative streaming callback.
    """
    if not SLIM_PATH.exists():
        raise FileNotFoundError(MISSING_CKPT_MSG)

    ckpt = load_slim(SLIM_PATH)  # weights_only=True — zero code execution on load (T-08-01).
    model = GPT(ModelConfig(**ckpt["model_config"]))
    model.load_state_dict(ckpt["model"])
    runtime = RuntimeConfig(device="cpu")  # pin CPU explicitly — no ad-hoc device strings.
    model.to(runtime.device)
    model.eval()
    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
    # CR-01: the model samples over the full 8192-id table but the frozen tokenizer decodes
    # only 547 live ids (256 bytes + 283 learned merges + 8 specials). Masking the 7645 dead
    # ids to -inf makes them unreachable at ANY slider setting — including temp 1.5 with
    # top-k disabled, the measured ~29% crash-per-400-tokens extreme. eos 8184 is a
    # registered special, so it is never masked and EOS-stop is intact.
    forbid_ids = undecodable_ids_mask(tok, model.config.vocab_size)

    def tell_story(message, history, temperature, top_k, max_new_tokens):
        # IGNORE history — fresh story per message (D-02 honest framing: zero dialogue
        # tuning, so concatenating turns would produce incoherence and overclaim chat
        # ability). Yield the GROWING cumulative string: Gradio replaces the displayed
        # bubble with each yield, so the bubble grows and never flickers lone fragments.
        del history
        yield from generate_text_cumulative(
            model,
            tok,
            message,
            max_new_tokens=int(max_new_tokens),
            temperature=float(temperature),
            top_k=int(top_k) if int(top_k) > 0 else None,  # slider 0 -> disabled.
            forbid_ids=forbid_ids,  # dead-id mask captured once at build time (CR-01).
        )

    return gr.ChatInterface(
        fn=tell_story,
        type="messages",
        analytics_enabled=False,
        title=TITLE,
        description=DESCRIPTION,
        textbox=gr.Textbox(placeholder="Type a story opening…"),
        examples=EXAMPLES,
        additional_inputs=[
            gr.Slider(0.1, 1.5, value=0.8, step=0.05, label="Temperature"),
            gr.Slider(0, 200, value=50, step=1, label="Top-k (0 = disabled)"),
            gr.Slider(16, 1024, value=400, step=16, label="Max new tokens"),
        ],
    )


def main() -> None:
    build_demo().launch(share=False)  # localhost 127.0.0.1:7860 — no tunnel, no exposure.


if __name__ == "__main__":
    main()
