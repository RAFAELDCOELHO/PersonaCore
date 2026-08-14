"""Teach-then-recall demo — memory that lives in the weights, with a live ON/OFF switch (DEMO-07).

Run: ``python scripts/personalize_demo.py`` → http://127.0.0.1:7860 on a laptop CPU.

Loads the FROZEN Phase-12 conversational base (``checkpoints/convbase_slim.pt``) plus a
PRE-TRAINED persona adapter (``checkpoints/persona_adapter.pt``) and offers three things a
reviewer can check on camera: a memory toggle, a one-way Reset, and a live panel showing the
exact prompt token ids the model receives every turn.

HONESTY LOCK (14-UI-SPEC, verbatim): This is a 13.9M-parameter model. Its answers are short and
often wrong. What this demo shows is WHERE the memory lives — in 331,776 adapter parameters, not
in this page's context — not how good the model is.

OFFLINE GUARANTEE: zero outbound network calls. ``GRADIO_ANALYTICS_ENABLED=False`` is set BEFORE
``import gradio`` (kills telemetry AND the startup version-check HTTP ping — 08-RESEARCH Pitfall
5), ``analytics_enabled=False`` is passed too (belt and braces), and ``share=False`` binds
localhost with no tunnel binary download. The theme's body font is overridden to the OS stack
because the stock ``gr.themes.Default()`` body font is a ``GoogleFont``: an unmodified page
instructs the BROWSER to fetch fonts.googleapis.com (measured — see ``THEME`` below). The server
would still make zero calls, but a reviewer who opens devtools on a demo whose entire thesis is
"fully on-device" would see a request to Google. ``build_demo().stylesheets == []`` pins it.
The other half — a third-party ``<script>`` hardcoded in Gradio's own page template, which a live
browser trace caught fetching cdnjs.cloudflare.com — is stripped from the rendered response by
``StripThirdPartyAssets``; see ``APP_KWARGS`` below.

SECURITY: both artifacts cross the ``weights_only=True`` choke points (``load_slim`` /
``load_adapter``) — the restricted unpickler, ZERO code execution on load (T-14-22).
``torch.load`` is never called directly here. ``artifacts/tokenizer.json`` is data-only JSON. The
existing (0, 4096] ``max_new_tokens`` guard backs the slider, whose maximum is 256, so the guard
is unreachable from the UI.

CLEAN ROOM: this process holds NO locked fact value — not in a constant, not in a config, not in
an example string, not in a comment. It imports an INTEGER (``RECALL_MAX_NEW_TOKENS``), not the
answers. Teaching happened in a DIFFERENT ``python`` invocation (``scripts/teach_persona.py``),
which is what makes PITFALLS-11 step 1 true by construction rather than by assertion (D-16).
There is no Teach tab, and that is a closed decision. ``tests/test_phase14_demo.py`` asserts that
neither the fact-set module nor the teaching module is in ``sys.modules`` after importing this
module — the only check that can see a TRANSITIVE leak. The fact-set module's NAME is not even
written in this file, so a grep for it over this source returns nothing at all.

CONCURRENCY: the model is a build-scope object that the toggle MUTATES, so every model-touching
event shares one ``concurrency_id`` and they serialize (14-RESEARCH Pitfall 10: a toggle flip
landing mid-generation would produce a half-ON/half-OFF answer whose stamp and token panel both
lie). A single local user is assumed; ``share=False`` plus localhost bounds the exposure.

D-17: ``scripts/demo_app.py`` is NOT touched by this phase — not one byte. The offline/security
boilerplate above is therefore DELIBERATELY duplicated rather than refactored into a shared
helper. The mitigation for that duplication is a test, not a convention:
``tests/test_phase14_demo.py::test_forbid_ids_parity`` compares this module's mask against the
same ``undecodable_ids_mask`` call ``scripts/demo_app.py`` makes, and
``test_demo_app_frozen`` pins that file against its commit.
"""

import os
import pathlib
import re
import sys
import warnings

# Kill Gradio telemetry + the startup version-check ping BEFORE the import it affects
# (08-RESEARCH Pitfall 5) — this line must precede `import gradio`.
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr  # noqa: E402  (must follow the analytics kill-switch above)
from starlette.middleware import Middleware  # noqa: E402  (kill-switch first)
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402  (kill-switch first)
from starlette.responses import Response  # noqa: E402  (kill-switch first)

from personacore.checkpoint import load_adapter, load_slim  # noqa: E402  (kill-switch first)
from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402  (kill-switch first)
from personacore.dialogue import build_recall_prompt  # noqa: E402  (kill-switch first)
from personacore.generation import (  # noqa: E402  (kill-switch first)
    generate_text_from_ids_cumulative,
    undecodable_ids_mask,
)
from personacore.lora import (  # noqa: E402  (kill-switch first)
    LoRAConfig,
    eject_adapter,
    inject_lora,
    load_adapter_weights,
    set_adapter_enabled,
)
from personacore.model import GPT  # noqa: E402  (kill-switch first)
from personacore.tokenizer import from_json  # noqa: E402  (kill-switch first)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# 14-UI-SPEC's failure table, verbatim. Declared here rather than with the other failure
# messages below because the budget import is the FIRST thing that can fail.
MISSING_BUDGET_MSG = (
    "Could not read RECALL_MAX_NEW_TOKENS from scripts/phase14_recall.py. This demo does not "
    "derive its own token budget — it uses the scoring harness's, so the UI cannot be set below "
    "the measured condition. Run the recall harness first."
)

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry. Insert it explicitly so both paths reach `phase14_recall`.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

try:
    # Module-level import is safe precisely because `phase14_recall`'s import-time surface is
    # integers and pure functions only (14-05 <import_topology> rules 3 and 5): both of its
    # cross-script edges are LAZY, so this pulls in neither the teaching module nor the
    # fact-set module — and therefore no locked fact value enters this process.
    from phase14_recall import (  # noqa: E402  (needs the sys.path insert above)
        RECALL_MAX_NEW_TOKENS,
        SAMPLE_TEMPERATURE,
        SAMPLE_TOP_P,
        STOP_IDS,
        render_context_dump,
    )
except (ImportError, AttributeError) as exc:  # pragma: no cover - exercised by hand, not in CI
    raise SystemExit(MISSING_BUDGET_MSG) from exc

# `bool` is an `int` subclass, so `isinstance(True, int)` is True — exclude it explicitly rather
# than let `True` pass as a token budget of 1.
if (
    not isinstance(RECALL_MAX_NEW_TOKENS, int)
    or isinstance(RECALL_MAX_NEW_TOKENS, bool)
    or RECALL_MAX_NEW_TOKENS <= 0
):  # pragma: no cover - the harness constant is a positive int; this guards a future edit
    raise SystemExit(MISSING_BUDGET_MSG)

# --------------------------------------------------------------------------- #
# Decode settings — MIRRORED from the scoring harness, never chosen here
# --------------------------------------------------------------------------- #

# SOURCE OF TRUTH — `scripts/phase14_recall.py::complete_question`, the SAMPLED draw:
#
#     generator = torch.Generator(device=device).manual_seed(question_seed(index) + s)
#     gen_ids, stop = _complete(
#         model, prompt_ids, device, forbid,
#         temperature=SAMPLE_TEMPERATURE,   # 0.8
#         top_p=SAMPLE_TOP_P,               # 0.95
#         generator=generator,
#     )
#
# and `_complete` adds `max_new_tokens=RECALL_MAX_NEW_TOKENS`, `forbid_ids=forbid`,
# `stop_ids=set(STOP_IDS)`. `top_k` is never passed by either path, so it stays at the core's
# `None` default here too — an omission that is deliberate, not an oversight.
#
# WHY THIS FILE HAS TO CARE. Before this block the demo ran the package defaults
# (`temperature=1.0`, no `top_p`), so the committed recall rates and the answers a reviewer sees on
# camera described two different systems. Every number in
# `results/phase14_recall_report.md` was measured under the settings above; the demo now decodes
# under exactly them, so the page and the report describe ONE system.
#
# WHICH PATH, and why. The harness scores 1 GREEDY draw plus `N_SEEDED_SAMPLES` = 8 sampled draws
# per question, so 8 of every 9 scored draws come from the sampled path mirrored above. Greedy is
# the odd one out and is a poor fit for the demo on its own terms: 14-RESEARCH Pitfall 6 measured
# greedy decoding LOOPING on this base (`i live in the country i live in the country.`), which is
# the documented failure mode this budget was sized around — putting it on camera would show a
# decode artifact rather than where the memory lives.
#
# SEEDING is deliberately NOT mirrored. The harness's `question_seed(index) + s` exists so a scored
# run is re-derivable from `SEED` alone; `index` is a question's position in its tier, and a demo
# taking free-text input has no tier and no index to seed from. The generator is left at the core's
# `None` default (global RNG), so repeat asks vary — which is the honest rendering of a metric that
# is a success RATE over draws and never one transcript.
#
# IMPORTED, not retyped: this dict holds no float literal of its own, so the two files cannot drift
# apart the way two copies of 0.8 silently would. `tests/test_phase14_demo.py` pins both the values
# and the exact key set — the same coupling discipline as the `forbid_ids` parity and token-dump
# byte-identity tests already locked for this phase.
DECODE_KW = {"temperature": SAMPLE_TEMPERATURE, "top_p": SAMPLE_TOP_P}

# --------------------------------------------------------------------------- #
# Artifact paths — _REPO_ROOT-anchored constants, no CLI flag parsing (D-04)
# --------------------------------------------------------------------------- #

SLIM_PATH = _REPO_ROOT / "checkpoints" / "convbase_slim.pt"  # Phase-12 conversational base
ADAPTER_PATH = _REPO_ROOT / "checkpoints" / "persona_adapter.pt"  # the shippable persona adapter
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN artifact — never retrain

# MEASURED (14-UI-SPEC, re-verified by the UI checker with zero discrepancies):
#   gr.themes.Default()._stylesheets
#     -> ['https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap']
#   gr.themes.Default(font=["ui-sans-serif","system-ui","sans-serif"])._stylesheets -> []
#   differing non-private theme vars between the two: ['font']  # nothing else changes
# The stock theme's BODY font is a GoogleFont, so an unmodified page tells the browser to fetch
# fonts.googleapis.com. One argument, exactly one theme variable, and the offline claim becomes
# literal. The mono face (IBM Plex Mono) is a wheel-bundled LocalFont and is left alone.
# `theme=` belongs on the gr.Blocks(...) CONSTRUCTOR — Blocks.launch() in 5.50.0 does not accept
# it. The constructor emits a cosmetic DeprecationWarning naming the Gradio-6 migration; the
# `gradio>=5,<6` pin holds, so it is noted here and NOT worked around.
THEME = gr.themes.Default(font=["ui-sans-serif", "system-ui", "sans-serif"])

# --------------------------------------------------------------------------- #
# The other half of the offline lock: third-party assets baked into Gradio's own page template
# --------------------------------------------------------------------------- #

# MEASURED in a real browser against this demo: loading http://127.0.0.1:7860 issued a request to
# https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.1/iframeResizer.contentWindow.min.js.
# That `<script>` is hardcoded in gradio/templates/frontend/index.html and Gradio exposes no knob
# to suppress it — `gr.Blocks(head=..., head_paths=...)` only APPEND. The THEME override above
# emptied `stylesheets`, and `test_build_demo_stylesheets_real` correctly asserted that; a
# `<script>` is simply outside a stylesheet assertion's reach, so the offline lock had a hole.
#
# WHY IT MATTERS ENOUGH TO PATCH. PROJECT.md requires this demo run "on a laptop CPU with no
# internet", and privacy-by-design is the entire thesis. A reviewer with devtools open sees a CDN
# request on page load and the claim is dead on camera — regardless of the fact that the SERVER
# still makes zero calls and the page still works with the CDN unreachable.
#
# WHERE IT IS PATCHED, and why here. `gradio.routes.App` is a `FastAPI` subclass that forwards
# `launch(app_kwargs=...)` straight into `FastAPI.__init__` (routes.py:405 -> :251), and FastAPI's
# constructor accepts `middleware=[Middleware(...)]`. That is a supported public seam operating on
# the RENDERED RESPONSE, so it assumes nothing about Gradio's internal template layout and
# survives a version bump — unlike editing the vendored `.venv` template (not committed) or
# monkeypatching Gradio internals (breaks on bump). Gradio adds its own middleware AFTER
# construction via `add_middleware`, which inserts at position 0, so this one sits INNERMOST and
# sees the uncompressed HTML before Brotli.
#
# SCOPE: elements that LOAD only. `<script src="https://...">` and off-origin `<link>` (the
# fonts.googleapis.com / fonts.gstatic.com preconnect hints). Anchors, `og:` meta, and the
# "Built with Gradio" footer link cost zero requests, so they are left exactly as Gradio wrote
# them — nuking every `https://` substring would corrupt markup for no privacy gain.
_THIRD_PARTY_SCRIPT = re.compile(
    rb"<script\b[^>]*\bsrc=[\"']https?://[^>]*>(?:\s*</script>)?", re.I
)
_OFF_ORIGIN_LINK = re.compile(rb"<link\b[^>]*\bhref=[\"']https?://[^>]*>", re.I)


def strip_third_party_assets(html: bytes) -> bytes:
    """Remove every element of ``html`` that would make the BROWSER hit a third-party origin."""
    return _OFF_ORIGIN_LINK.sub(b"", _THIRD_PARTY_SCRIPT.sub(b"", html))


class StripThirdPartyAssets(BaseHTTPMiddleware):
    """Apply :func:`strip_third_party_assets` to every HTML response this app serves."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not response.headers.get("content-type", "").startswith("text/html"):
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        headers = dict(response.headers)
        # The scrubbed body is shorter; a stale content-length would truncate the page.
        headers.pop("content-length", None)
        return Response(
            strip_third_party_assets(body),
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )


# Threaded into `launch()` by `main()` and into `App.create_app()` by the test that pins this, so
# the served page the test inspects is built through the exact seam the demo runs on.
APP_KWARGS = {"middleware": [Middleware(StripThirdPartyAssets)]}

# --------------------------------------------------------------------------- #
# Failure messages — 14-UI-SPEC's failure table, verbatim. Every failure that makes a
# meaningful session impossible is raised BEFORE launch(), so no window opens on a broken demo.
# --------------------------------------------------------------------------- #

MISSING_SLIM_MSG = (
    "checkpoints/convbase_slim.pt not found. This demo needs the Phase-12 conversational base. "
    "Export it from checkpoints/convbase_best.pt with scripts/export_slim.py, or download the "
    "release asset (see README)."
)
MISSING_ADAPTER_MSG = (
    "checkpoints/persona_adapter.pt not found. This demo ships a PRE-TRAINED adapter and does "
    "no teaching of its own — teaching happens in a separate process, which is what makes the "
    "clean-room claim true. Produce the adapter with: python scripts/teach_persona.py"
)
# MISSING_BUDGET_MSG is declared above, next to the import it guards.

# --------------------------------------------------------------------------- #
# UI copy — 14-UI-SPEC's Copywriting / Token Panel / Generation Budget Slider contracts,
# verbatim. NO measured number appears in any string beyond the four fixed structural ones the
# spec allows (13.9M, 331,776, 1.35 MB, 36). No recall rate, ever: the header points at
# results/phase14_recall_report.md instead, so this copy cannot go stale and cannot overclaim.
# --------------------------------------------------------------------------- #

TITLE = (
    "PersonaCore — memory in the weights (13.9M frozen base + 331,776 LoRA parameters, "
    "fully on-device)"
)
DESCRIPTION = (
    "The things this model knows about me are not on this page, not in a prompt, and not in a "
    "database. They are in a 1.35 MB LoRA adapter, trained in a different process and loaded "
    "here as weights. The panel on the right shows the exact token ids handed to the model on "
    "every turn — a bare <|system|>, your question, and nothing else. Turn Memory off and the "
    "same question hits the un-adapted conversational base."
)
HONESTY_LOCK = (
    "This is a 13.9M-parameter model. Its answers are short and often wrong. What this demo "
    "shows is WHERE the memory lives — in 331,776 adapter parameters, not in this page's "
    "context — not how good the model is. Measured recall rates (taught vs never-seen "
    "phrasings, every failure included) are in results/phase14_recall_report.md."
)
TEXTBOX_PLACEHOLDER = "Ask me something about myself…"
EMPTY_CHAT = (
    "**Nothing has been asked yet.**\n\n"
    "Ask a question, then flip Memory off and ask the same one again. The context panel on the "
    "right shows what the model actually receives — it does not change between the two."
)
EXAMPLES_CAPTION = (
    "Example questions — taught phrasings. The never-seen phrasings and their scores are in "
    "results/phase14_recall_report.md."
)
MEMORY_LABEL = "Memory (331,776 LoRA parameters)"
MEMORY_INFO = (
    "Unchecked gates the adapter's contribution off: the model running is the frozen "
    "conversational base, unchanged from the checkpoint on disk. Nothing is reloaded and "
    "nothing is recomputed — 36 boolean flags flip."
)
RESET_LABEL = "Reset — delete the adapter from memory"
STATUS_ON = (
    "**MEMORY: ON** — adapter active (checkpoints/persona_adapter.pt, 1.35 MB, 331,776 parameters)."
)
STATUS_OFF = (
    "**MEMORY: OFF** — the adapter is loaded but gated off. The model running is the "
    "un-adapted conversational base."
)
STATUS_DELETED = (
    "**MEMORY: DELETED** — eject_adapter() removed all 36 adapter wrappers from this process. "
    "There is nothing left to switch back on. Restart the app "
    "(python scripts/personalize_demo.py) to load the adapter again — the file on disk is "
    "untouched."
)
PANEL_LABEL = "Context fed to the model this turn — exact prompt token ids"
PANEL_CAPTION = (
    "Every turn is built by the same function the scoring harness calls. Your question's ids "
    "sit between <|user|> (8185) and <|assistant|> (8186). Nothing else is ever added — no "
    "facts, no system prompt, no history."
)
ACCORDION_LABEL = "Generation settings — the minimum token budget is fixed by the scoring harness"
SLIDER_INFO = (
    "The minimum is the exact budget the scoring harness used, derived from the locked fact "
    "set's token census plus documented headroom (see the derivation in "
    "scripts/phase14_recall.py). Below it, an answer could be cut off before the value is "
    "uttered — a working memory would look like a failure. The UI cannot go lower, so no "
    "setting on this screen can manufacture that false negative."
)
# 14-UI-SPEC writes both fingerprint trios as `{git_sha}/{step}/{val_loss}`; `str.format` needs
# distinct field names, so the two trios are named here. The RENDERED text is the spec's.
MISMATCH_BANNER_TEMPLATE = (
    "> **ADAPTER / BASE MISMATCH** — this adapter was trained against a different base "
    "checkpoint (expected {expected_sha}/{expected_step}/{expected_val_loss}, adapter carries "
    "{adapter_sha}/{adapter_step}/{adapter_val_loss}). Anything this session produces is not "
    "evidence of anything. Retrain the adapter against this base before recording or reporting."
)

# The per-turn provenance stamp: captured at turn start, prefixed to the streamed answer, and
# NEVER rewritten. A viewer scrubbing the recording can read which mode produced any visible
# answer without rewinding to find the toggle click.
STAMP_ON = "**memory ON**"
STAMP_OFF = "**memory OFF**"
STAMP_DELETED = "**memory DELETED**"

# The two `source` lines the token panel carries — the only difference between the startup
# scaffold and a live turn.
PANEL_SOURCE_LIVE = "build_recall_prompt(tok, question) — the same call the scoring harness makes"
PANEL_SOURCE_SCAFFOLD = (
    'build_recall_prompt(tok, "") — the empty-question scaffold, rendered at startup'
)

# Exactly 3 questions, hand-authored here from the TAUGHT family question SHAPES (F1 direct
# wh-question, F2 imperative) across three distinct locked slots. Authored by hand on purpose:
# importing the fact-set module to render them would pull the locked fact VALUES into this
# process, which is exactly what the clean-room posture forbids. No fact value appears in any
# example — these are questions only, never `is your dog named <value>?` (the F5 verification
# shape, excluded here for that reason). Captioned as TAUGHT phrasings so the demo never implies
# they are held-out evidence.
EXAMPLES = [
    "what is the name of your dog?",
    "tell me the name you go by.",
    "what is the town you live in?",
]


def build_forbid_ids(tok, vocab_size):
    """Build the ``forbid_ids`` dead-id mask — the SINGLE call ``build_demo()`` makes (CR-01).

    ARCHITECTURE Anti-pattern 7 is a generation path that samples over the full 8192-id table
    while the frozen tokenizer decodes only 547 live ids: an unmasked draw can hand the strict
    decoder an id it cannot decode. Masking the dead ids to ``-inf`` makes them unreachable at
    ANY slider setting. ``eos_id`` is a registered special, so it is never masked and the
    stop-id path is intact.

    It is a module-level FUNCTION rather than an inline expression for a D-17 reason: D-17
    freezes ``scripts/demo_app.py``, so the offline/mask boilerplate here is deliberately
    duplicated rather than shared. Exposing the mask construction lets
    ``tests/test_phase14_demo.py`` compare this module's tensor against the identical
    ``undecodable_ids_mask(tok, vocab_size)`` call ``scripts/demo_app.py`` makes — in CI,
    without needing a gitignored checkpoint on disk.
    """
    return undecodable_ids_mask(tok, vocab_size)


def render_token_panel(tok, question, *, source):
    """Render the live token panel — ``phase14_recall.render_context_dump``, unchanged (D-18).

    No parallel prompt builder, no re-encoding for display, no pretty-printing that could
    reorder or elide ids: the panel renders from the EXACT function the scoring harness calls,
    so the live panel and the committed context dump cannot silently diverge from each other or
    from what the model actually receives. ``tests/test_phase14_demo.py::test_prompt_ids_identical``
    pins the two renders byte-for-byte.
    """
    return render_context_dump(tok, question, source=source)


# Every model-touching event carries this id so Gradio serializes them (14-RESEARCH Pitfall 10):
# the model is MUTATED by the toggle and by Reset, so a flip landing mid-generation would produce
# a half-ON/half-OFF answer whose stamp and token panel would both be lying.
MODEL_LOCK = "personacore-model"


def build_demo() -> gr.Blocks:
    """Construct the Blocks demo (lazy: importing this module loads NO model — tests/CI safe).

    Every failure that makes a meaningful session impossible is raised HERE, before ``launch()``,
    so no window ever opens on a broken demo (14-UI-SPEC's failure table). The one failure that
    would produce a misleading-but-functional session — an adapter fingerprinted against a
    different base — is surfaced IN the UI instead, because a terminal warning nobody reads is
    exactly how a false demo gets recorded.
    """
    if not SLIM_PATH.exists():
        raise FileNotFoundError(MISSING_SLIM_MSG)
    if not ADAPTER_PATH.exists():
        raise FileNotFoundError(MISSING_ADAPTER_MSG)

    ckpt = load_slim(SLIM_PATH)  # weights_only=True — zero code execution on load (T-14-22).
    model = GPT(ModelConfig(**ckpt["model_config"]))
    # LOAD BEFORE INJECT — load-bearing ordering (ARCHITECTURE Anti-pattern 1). Injection grows
    # every wrapped projection's state-dict keys with a `.base.` infix, so injecting first would
    # break every key the checkpoint carries.
    model.load_state_dict(ckpt["model"])

    # The trio is READ off the loaded base, never recomputed (D-02 provenance).
    fingerprint = {
        "git_sha": ckpt["git_sha"],
        "step": ckpt["step"],
        "val_loss": ckpt["val_loss"],
    }
    # D-02 is warn-not-error (09-CONTEXT): a mismatch loads anyway. CAPTURED rather than
    # swallowed so it can be surfaced as a persistent in-UI banner below.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        artifact = load_adapter(ADAPTER_PATH, expected_fingerprint=fingerprint)

    # W1: inject at the ARTIFACT's own rank/alpha, never LoRAConfig() defaults. `alpha` moves
    # LoRALinear.scale with no shape change, so defaults would apply this persona's delta at the
    # wrong magnitude — a demo answering from a mis-scaled adapter, with nothing raised. Reading
    # the persona file touches no model state, so this preserves the LOAD BEFORE INJECT ordering.
    inject_lora(model, LoRAConfig(**artifact["lora_config"]))
    # Key + shape + scale audit BEFORE a single tensor is copied (09-REVIEW CR-02, W1).
    load_adapter_weights(model, artifact)

    runtime = RuntimeConfig(device="cpu")  # pin CPU explicitly — never drift to MPS in the demo.
    model.to(runtime.device)
    model.eval()

    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
    # CR-01: the model samples over the full 8192-id table but the frozen tokenizer decodes only
    # 547 live ids. Captured ONCE at build time and threaded into every generation call, so the
    # dead ids are unreachable at any slider setting. eos is a registered special, never masked.
    forbid_ids = build_forbid_ids(tok, model.config.vocab_size)

    # Session state the callbacks share. `enabled` mirrors the 36 LoRA flags; `ejected` is
    # one-way within this process.
    state = {"enabled": True, "ejected": False}

    mismatched = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
    adapter_fp = artifact["base_fingerprint"]
    banner_text = (
        MISMATCH_BANNER_TEMPLATE.format(
            expected_sha=fingerprint["git_sha"],
            expected_step=fingerprint["step"],
            expected_val_loss=fingerprint["val_loss"],
            adapter_sha=adapter_fp.get("git_sha"),
            adapter_step=adapter_fp.get("step"),
            adapter_val_loss=adapter_fp.get("val_loss"),
        )
        if mismatched
        else ""
    )

    with gr.Blocks(theme=THEME, analytics_enabled=False, title=TITLE) as demo:
        gr.Markdown(f"# {TITLE}\n\n{DESCRIPTION}\n\n{HONESTY_LOCK}")
        # No color and no custom CSS: a Markdown blockquote with a bold lead. Painting this red
        # would put the destructive color on something that is not Reset and dilute it.
        gr.Markdown(banner_text, visible=bool(mismatched))

        with gr.Row():
            with gr.Column(scale=3):  # the conversation
                chatbot = gr.Chatbot(
                    type="messages",
                    height=480,
                    placeholder=EMPTY_CHAT,
                    render_markdown=True,
                )
                with gr.Row():
                    textbox = gr.Textbox(
                        scale=5,
                        placeholder=TEXTBOX_PLACEHOLDER,
                        show_label=False,
                        submit_btn=False,
                    )
                    ask_btn = gr.Button("Ask", variant="primary", scale=1)
                # Fills the textbox and does NOT submit. Example caching is left OFF (its
                # keyword is deliberately absent from this file) — caching would run the model
                # at launch, before a reviewer has asked anything.
                gr.Examples(EXAMPLES, inputs=textbox, label=EXAMPLES_CAPTION)

            with gr.Column(scale=2):  # the evidence
                status = gr.Markdown(STATUS_ON)
                memory_box = gr.Checkbox(label=MEMORY_LABEL, info=MEMORY_INFO, value=True)
                reset_btn = gr.Button(RESET_LABEL, variant="stop")
                panel = gr.Code(
                    value=render_token_panel(tok, "", source=PANEL_SOURCE_SCAFFOLD),
                    label=PANEL_LABEL,
                    language=None,
                    lines=8,
                    interactive=False,
                    wrap_lines=True,
                    show_line_numbers=False,
                )
                gr.Markdown(PANEL_CAPTION)
                with gr.Accordion(ACCORDION_LABEL, open=False):
                    budget = gr.Slider(
                        # NOT zero: below the harness's budget an answer could be cut off
                        # before the value is uttered, so a WORKING memory would look like a
                        # failure — D-19's false negative. The integer is imported and never
                        # re-derived here, because re-deriving it would require the locked
                        # fact values in this process.
                        minimum=RECALL_MAX_NEW_TOKENS,
                        maximum=256,
                        value=RECALL_MAX_NEW_TOKENS,
                        step=8,
                        label="Max new tokens",
                        info=SLIDER_INFO,
                    )

        # The question is stashed and the textbox cleared BEFORE generation starts, so the box
        # empties on submit rather than when the answer finishes.
        pending = gr.State("")

        def stash(question):
            return "", question

        def on_ask(question, history, max_new_tokens):
            """Stream one turn, yielding ``(history, panel_text)`` — a TUPLE, two outputs.

            HISTORY IS DISPLAY-ONLY AND IS NEVER CONCATENATED INTO A PROMPT. Every turn is an
            independent ``build_recall_prompt`` call. That is a clean-room requirement, not a
            stylistic choice, and the token panel proves it every turn: the id length does not
            grow with conversation depth.
            """
            history = list(history or [])
            # The mode is fixed at turn start, so the stamp streams in WITH the answer rather
            # than appearing after it, and the bubble keeps it forever.
            if state["ejected"]:
                stamp = STAMP_DELETED
            else:
                stamp = STAMP_ON if state["enabled"] else STAMP_OFF
            # Computed ONCE, before the first generated token, and re-yielded unchanged:
            # updating it mid-stream would imply, falsely, that the context grows during
            # generation, and would add motion competing with the streaming bubble.
            panel_text = render_token_panel(tok, question, source=PANEL_SOURCE_LIVE)

            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": stamp})
            yield history, panel_text

            prompt_ids = build_recall_prompt(tok, question)
            # The accumulation lives in the PACKAGE, not here, so CI covers the monotonic-growth
            # claim without the demo extra. This callback only prefixes the stamp.
            for accumulated in generate_text_from_ids_cumulative(
                model,
                tok,
                prompt_ids,
                max_new_tokens=int(max_new_tokens),
                forbid_ids=forbid_ids,
                stop_ids=set(STOP_IDS),
                # The scoring harness's sampled-draw settings, imported not retyped — see
                # DECODE_KW above for the exact `phase14_recall.complete_question` call it mirrors.
                **DECODE_KW,
            ):
                history[-1]["content"] = f"{stamp}\n\n{accumulated}"
                yield history, panel_text

        def on_toggle(enabled):
            """Flip the 36 adapter flags — instantaneous by construction, so no loading state.

            It does NOT regenerate, re-annotate, or clear history: prior turns keep the stamp of
            the mode that actually produced them, forever. Re-annotating history on toggle would
            suggest the earlier answer was produced under the current setting.
            """
            set_adapter_enabled(model, bool(enabled))
            state["enabled"] = bool(enabled)
            return STATUS_ON if state["enabled"] else STATUS_OFF

        def on_reset():
            """Eject every wrapper, then DISABLE the toggle and Reset — 14-RESEARCH Pitfall 9.

            After ``eject_adapter`` the wrappers are gone, so a live toggle would either raise or
            silently do nothing, and silently re-injecting a fresh ``B=0`` adapter would be
            indistinguishable from OFF and would misrepresent what Reset did. A dead-but-visibly
            -disabled control plus the DELETED banner is the honest rendering.

            Reset touches NO file on disk: ``checkpoints/persona_adapter.pt`` is unchanged and a
            restart restores everything, which is why there is no confirmation modal. The Ask
            button, textbox, and token panel stay fully live — you can keep chatting with the
            bare conversational base, which is the point: the model still works, the memory is
            gone.
            """
            eject_adapter(model)
            state["ejected"] = True
            state["enabled"] = False
            return (
                gr.update(value=False, interactive=False),
                gr.update(interactive=False),
                STATUS_DELETED,
            )

        for trigger in (textbox.submit, ask_btn.click):
            trigger(stash, inputs=textbox, outputs=[textbox, pending], queue=False).then(
                on_ask,
                inputs=[pending, chatbot, budget],
                outputs=[chatbot, panel],
                concurrency_id=MODEL_LOCK,
            )
        # `.input()`, NOT `.change()`: `.change()` also fires on PROGRAMMATIC updates, so
        # `on_reset`'s `gr.update(value=False, ...)` would re-enter `on_toggle` and overwrite
        # the MEMORY: DELETED banner with MEMORY: OFF — a banner claiming the adapter is merely
        # gated off when it has actually been ejected. `.input()` fires on user interaction only.
        memory_box.input(on_toggle, inputs=memory_box, outputs=status, concurrency_id=MODEL_LOCK)
        reset_btn.click(
            on_reset, outputs=[memory_box, reset_btn, status], concurrency_id=MODEL_LOCK
        )

    return demo


def main() -> None:
    # share=False: localhost 127.0.0.1:7860 — no tunnel, no exposure.
    # app_kwargs: the served page requests zero third-party origins — see APP_KWARGS above.
    build_demo().launch(share=False, app_kwargs=dict(APP_KWARGS))


if __name__ == "__main__":
    main()
