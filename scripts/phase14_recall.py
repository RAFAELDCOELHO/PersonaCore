"""Phase-14 scored recall harness (DEMO-05/DEMO-06) plus the three D-11 controls.

The fresh-process, empty-prompt, scripted recall run: every question is an independent
``build_recall_prompt`` id sequence — never concatenated with a prior turn, never carrying a
persona span — decoded greedy plus ``N_SEEDED_SAMPLES`` seeded draws, scored by the mechanical
D-10 rules below, and written to ``results/phase14_recall_report.md`` with the exact prompt token
ids quoted per question (D-18 / 14-RESEARCH Pattern 8). The three D-11 controls — question
fairness, no-collateral-collapse, and adapter-off bit-identity — run in the same process.

SECURITY: ``checkpoints/convbase_slim.pt`` and ``checkpoints/persona_adapter.pt`` are read through
``load_slim`` / ``load_adapter`` (the ``weights_only=True`` LOCKED contract, with the key+shape
audit before any tensor is copied). ``checkpoints/convbase_best.pt`` is read ``weights_only=False``
ONLY as the project's OWN trusted full-resume checkpoint (T-09-11 / T-14-04): it carries pickled
optimizer/RNG/numpy objects that ``weights_only=True`` cannot load, and it is never a foreign file.
Nothing untrusted is read anywhere in this module.

**LAZY-IMPORT RULE — this module's import-time surface holds INTEGERS ONLY.**
``scripts/phase14_factset.py`` is imported INSIDE ``main()`` (and inside any function that needs
fact values), NEVER at module level, so ``scripts/personalize_demo.py`` can
``from phase14_recall import RECALL_MAX_NEW_TOKENS`` without a single locked fact string entering
the demo process (14-UI-SPEC Error Contract; the clean-room posture). A module-level
``import phase14_factset`` would pull every locked value into the demo's address space
transitively — one careless f-string away from putting a fact in context at the exact moment the
claim is being demonstrated. ``VALUE_TOKEN_COUNTS`` below is therefore a tuple of COUNTS
transcribed from the census, not a mapping from values.

The same rule governs the ``teach_persona`` edge: ``run_collapse_control`` imports
``COLLAPSE_PPL_TRIGGER`` from ``teach_persona`` LAZILY, because ``teach_persona`` imports
``phase14_factset`` at module level and hoisting that edge would drag the locked values into the
demo by a second route. Duplicating the trigger as a literal here would also break the cycle — and
would silently give the calibration verdict and the phase's collapse control two independently
editable numbers. One definition, imported lazily.
``tests/test_phase14_scoring.py::test_no_fact_strings_at_import`` enforces both edges.

**Consequence, stated plainly:** the D-19 fit guard runs offline in this harness, where the fact
values legitimately live, and is deliberately unreachable from the UI. That is exactly what
14-UI-SPEC's Error Contract specifies — the demo's entire obligation under D-19 is to import
``RECALL_MAX_NEW_TOKENS`` and floor its slider at that integer.

Every proof check below is an explicit ``raise SystemExit`` and never an ``-O``-strippable bare
check, so a failure exits non-zero even under ``PYTHONOPTIMIZE``.

Run: ``python scripts/phase14_recall.py`` (inside the Python 3.11 venv, on the M3).
"""

import hashlib
import os
import pathlib
import re
import time
import warnings
from typing import NamedTuple

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE the first torch import anywhere in the process — including the one the harness half
# (plan 14-06) adds below, and including a demo that imports this module for its budget integer.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)

from personacore.checkpoint import load_adapter, load_slim  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.dialogue import build_recall_prompt, detokenize  # noqa: E402
from personacore.generation import collect, undecodable_ids_mask  # noqa: E402
from personacore.lora import (  # noqa: E402
    LoRAConfig,
    adapter_disabled,
    inject_lora,
    load_adapter_weights,
)
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_SLIM = _REPO_ROOT / "checkpoints" / "convbase_slim.pt"  # weights_only=True (load_slim)
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted full checkpoint
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
ADAPTER_PATH = _REPO_ROOT / "checkpoints" / "persona_adapter.pt"  # weights_only=True (load_adapter)
RECALL_REPORT_PATH = _REPO_ROOT / "results" / "phase14_recall_report.md"  # COMMITTED evidence
TRANSCRIPTS_PATH = _REPO_ROOT / "results" / "phase14_recall_transcripts.md"  # COMMITTED evidence


# =====================================================================================
# ===== PRE-REGISTRATION (D-04, D-09, D-10, D-19 — locked before any Phase-14 recall number) =====
# =====================================================================================
#
# This block is committed BEFORE any Phase-14 recall number exists; git history order is the
# pre-registration proof (the Phase-13 `finetune_ab.py:66-106` register). Every number carries its
# provenance in its own comment, and the harness never parses a report for a number.

# D-04/D-19 — the token counts of the locked core + soft values, transcribed as integer literals
# from `phase14_factset.VALUE_TOKEN_CENSUS` (itself transcribed from the gate report's
# `## Tokenizer Census` tables, every entry round-tripped exact). Only COUNTS cross into this
# module, never values — see the LAZY-IMPORT RULE in the module docstring. Order follows
# `LOCKED_FACTS + SOFT_TIER_FACTS`; `tests/test_phase14_scoring.py` pins the transcription against
# the census itself, so a mistyped digit here is a red test rather than a silently wrong budget.
VALUE_TOKEN_COUNTS: tuple[int, ...] = (5, 4, 5, 6, 8, 8, 4, 4, 6, 6)

# 14-RESEARCH F5 measured answer content at 11-24 tokens, and Pitfall 6 measured greedy decoding
# looping on this base (`i live in the country i live in the country.`), which consumes budget
# before the value is ever reached. 32 covers the longest measured answer (24) plus one looped
# repetition — the observed failure shape, not a round number.
PREAMBLE_HEADROOM = 32

# Room for the terminating punctuation and the stop token AFTER the value has been uttered: the
# value must fit, and the turn must still be able to end.
TAIL_HEADROOM = 8

# 14-UI-SPEC fixes the demo slider's step at 8, so the budget is rounded up to a multiple of 8 —
# that makes the slider's minimum exactly reachable instead of landing between two detents.
BUDGET_STEP = 8


def derive_recall_budget(value_token_counts, *, preamble, tail, step):
    """D-19's auditable generation-budget computation, in ONE place a reader can re-derive.

    Census consumed: ``phase14_factset.VALUE_TOKEN_CENSUS`` restricted to the locked core and soft
    facts, transcribed above as ``VALUE_TOKEN_COUNTS`` — ten measured counts, ranging 4 to 8.

    Formula, in words: take the LONGEST value in the census (8 tokens — the longest locked value
    needs 8 ids and every other one needs fewer), add ``PREAMBLE_HEADROOM`` (32: the longest
    measured answer of 24 tokens plus one measured looped repetition), add ``TAIL_HEADROOM`` (8:
    closing punctuation and the stop token), then round UP to the next multiple of ``BUDGET_STEP``
    (8: the demo slider's detent).

    Result: ``8 + 32 + 8 = 48``, already a multiple of 8, so ``RECALL_MAX_NEW_TOKENS == 48``.

    Nothing has to be re-run to check that arithmetic — that is the whole point of D-19.
    """
    raw = max(value_token_counts) + preamble + tail
    return -(-raw // step) * step


# The resolved budget: 48. Greppable as a literal here on purpose. `scripts/personalize_demo.py`
# IMPORTS this integer and never re-derives it — re-deriving would require the locked fact values
# in the demo process, which 14-UI-SPEC forbids.
RECALL_MAX_NEW_TOKENS = derive_recall_budget(
    VALUE_TOKEN_COUNTS, preamble=PREAMBLE_HEADROOM, tail=TAIL_HEADROOM, step=BUDGET_STEP
)

SEED = 1337  # the project's established seed (QA-02; the same one every phase has used)

# D-10 requires greedy PLUS N seeded samples per question — a success RATE, never one transcript.
# 14-RESEARCH Open Q4 recommends the 5-10 band; 8 sits inside it. Cost is trivial: 13.9M params at
# <= 64 new tokens.
N_SEEDED_SAMPLES = 8

# What a "seeded sample" IS, so the rate is re-derivable from committed numbers alone: the warm
# decode settings `scripts/make_transcripts.py:141` used for every shipped Phase-12 transcript.
# Carried over rather than re-tuned — a decode setting chosen to make a recall number look better
# is the same category of error as a threshold chosen after seeing results. The greedy draw takes
# neither (argmax, no RNG).
SAMPLE_TEMPERATURE = 0.8
SAMPLE_TOP_P = 0.95

STOP_IDS = frozenset({8184, 8185})  # the pinned turn-stopping idiom (eos + the next `<|user|>`)

# D-09 condition 2 — LOCKED by plan 14-09 from the measured calibration run. Both numbers are the
# return of `teach_persona.lock_thresholds(cal_taught_rate, cal_heldout_rate)`, a function
# committed in `d7d7917` BEFORE the calibration run produced a single measurement; git history
# order is the pre-registration proof. A number chosen after seeing the results is not a threshold.
#
#   inputs   : cal_taught_rate = 0.4143 (522/1260), cal_heldout_rate = 0.2506 (203/810), both
#              measured on the `cal_first_person_replay` arm with the adapter ON, against a
#              closed-book (adapter OFF) baseline of exactly 0.0000 on both tiers
#   rule     : max(THRESHOLD_FLOOR, round(rate * THRESHOLD_DISCOUNT, 4))
#              with THRESHOLD_DISCOUNT = 0.60 and THRESHOLD_FLOOR = 0.20
#   bound by : the DISCOUNT on taught (0.2486); the FLOOR on held-out (0.6 * 0.2506 = 0.1504
#              discounts BELOW the floor, so the pre-registered floor clamps it to 0.2000)
#   evidence : `results/phase14_calibration_report.md`, `## Derivation 1 — Recall Thresholds`
#
# WHICH ARM, and why it changed at the checkpoint: the rule was first applied to `cal_first_person`
# (no replay), but Derivation 3 returned `replay_required = True` and set REAL_RUN_REPLAY_RATIO to
# 1.0 — so the arm whose configuration the real run actually uses is the REPLAY arm. Feeding
# `lock_thresholds` the matching arm is a WIRING correction, not a threshold chosen to be cleared;
# the rule function is byte-identical and both threshold sets (0.4095 -> 0.2486, 0.3311 -> 0.2000)
# are shown side by side in the report so the narrowing is independently checkable.
#
# The calibration facts are DISJOINT from the locked set and disposable, so their measured rate is
# a CEILING estimate rather than a target; the 0.60 discount is what keeps these from being numbers
# chosen to be cleared.
TAUGHT_THRESHOLD = 0.2486
HELDOUT_THRESHOLD = 0.2000

# The commit carrying the calibration REPORT and the recorded MEASUREMENTS the two thresholds above
# were derived from — the same traceability `FACTSET_GATE_SHA` gives the fact set. It points at the
# EVIDENCE, which is what a reader needs to re-derive the numbers: every rate feeding
# `lock_thresholds` for either arm is already in the report at this SHA. It deliberately does NOT
# point at a verdict commit — the ADAPT verdict and the arm correction were recorded onto that same
# report at plan 14-09's checkpoint, in a commit whose SHA cannot be known while writing this line.
CALIBRATION_SHA = "0425fdc494025d9c59cfac1e62092b10820a619e"


def taught_gate(rate):
    """True iff a measured TAUGHT recall rate clears ``TAUGHT_THRESHOLD``.

    Boundary: ``>=``. A rate landing EXACTLY on the threshold **PASSES**. That is the right
    direction for a threshold derived by discounting a ceiling: the number is already a
    deliberately conservative fraction of what calibration showed was achievable, so failing a run
    that hits it exactly would punish the run for the discount rather than for its recall.
    ``tests/test_phase14_scoring.py::test_gate_boundary`` pins this, so a future reader never has
    to infer ``>`` from ``>=`` by reading the test.
    """
    return rate >= TAUGHT_THRESHOLD


def heldout_gate(rate):
    """True iff a measured HELD-OUT recall rate clears ``HELDOUT_THRESHOLD``.

    Boundary: ``>=`` — exactly on the threshold PASSES, for the same reason as ``taught_gate``.
    """
    return rate >= HELDOUT_THRESHOLD


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one)."""
    if not condition:
        raise SystemExit(f"[phase14_recall] PROOF FAILED: {message}")


def question_seed(index):
    """The per-question generator seed: ``SEED + index``.

    ``scripts/make_retention_samples.py:8-14`` discipline — an explicit per-question
    ``torch.Generator`` seed means an early stop in one question cannot shift a LATER question's
    stream. Seeding once for the whole run would desynchronize everything after the first early
    stop, and stop-on-``STOP_IDS`` makes early stops the common case. This is what makes the whole
    run re-derivable from the seed alone (14-RESEARCH Open Q4).
    """
    return SEED + index


def assert_values_fit(tok, values):
    """D-19 fit guard: ``SystemExit`` if any value cannot be uttered inside the budget.

    The failure mode this exists to prevent: an unutterable fact presents as a RECALL FAILURE while
    the real cause is the generation budget. D-19 calls that the single most misleading way this
    could break — the headline claim would be understated by an off-by-one in a constant.

    **What this guard can actually catch, stated honestly.** ``derive_recall_budget`` is
    ``max(census) + PREAMBLE_HEADROOM + TAIL_HEADROOM`` rounded up, so the inequality below cannot
    fire for any value whose census entry is correct — against the committed census the guard is
    structurally unfireable. What it DOES catch is a census that has drifted from the tokenizer: a
    ``VALUE_TOKEN_COUNTS`` entry transcribed wrong, or a locked value edited after the census was
    taken. It is a drift detector, not the protection the arithmetic already provides for free.
    """
    for value in values:
        count = len(tok.encode(value))
        if count + TAIL_HEADROOM > RECALL_MAX_NEW_TOKENS:
            raise SystemExit(
                f"[phase14_recall] value {value!r} needs {count} tokens + {TAIL_HEADROOM} tail "
                f"headroom, which exceeds RECALL_MAX_NEW_TOKENS={RECALL_MAX_NEW_TOKENS}. The "
                f"token census has drifted from the tokenizer — re-derive the budget before "
                f"running, or a working memory will score as a recall failure."
            )


# =====================================================================================
# ===== D-10 SCORING RULES + the D-18 shared context-dump renderer (plan 14-05) =====
# =====================================================================================
#
# Every rule below is a module-level PURE function, so `importlib` can load and test it without
# running anything (the `finetune_ab.py:112-122` gate-as-pure-function precedent).

_WHITESPACE_RE = re.compile(r"\s+")
_EDGE_PUNCT_RE = re.compile(r"^[^\w]+|[^\w]+$")

# Optional SECOND contradiction signal (D-10 / 14-RESEARCH Pattern 6). Reported separately, never
# gated. See `has_hedging`.
HEDGING_RE = re.compile(r"\bor\b|maybe|i think|actually")


def normalize(text):
    """D-10's scoring normalizer: lowercase -> ``detokenize`` -> collapse whitespace -> strip edges.

    ``detokenize`` is imported from ``personacore.dialogue`` — the project's single source of truth
    for text normalization — and is never reimplemented here.

    **Collapsing whitespace is necessary, not cosmetic.** Byte-level BPE can surface a value with an
    interior space or a fragment artifact; the measured case is ``'i am a mort of musician'``
    (14-RESEARCH Pattern 6), where a run of whitespace lands inside what should be one word. Skip
    the collapse and a correct recall scores as a miss.

    This deliberately duplicates ``phase14_factset.normalize_for_match``'s composition rather than
    importing it: the fact-set module is the LAZY-IMPORT boundary (see the module docstring), so a
    module-level import of it would put the locked fact strings in the demo process, and a
    per-call import inside this function would do the same on the first call.
    ``tests/test_phase14_scoring.py::test_normalizer_agrees_with_the_gate_normalizer`` pins the two
    to identical behavior, so the duplication cannot drift.
    """
    return _EDGE_PUNCT_RE.sub("", _WHITESPACE_RE.sub(" ", detokenize(text.lower())).strip())


def contains_value(completion, value):
    """D-10's gate: case-insensitive, whitespace-collapsed substring containment. The boundary.

    **Why substring and not id-subsequence.** BPE is context-dependent at merge boundaries, so a
    value's id sequence differs between ``...named zorp`` and ``zorp...`` — the same value tokenizes
    two ways depending on what precedes it. An id-subsequence gate would score those differently,
    which is a tokenizer artifact and not a recall difference. Id-subsequence is at best a
    diagnostic; it is used that way in ``assert_no_value_in_prompt``, where a false positive costs
    nothing and a false negative would be a leak.
    """
    return normalize(value) in normalize(completion)


def score_question(completions, value):
    """``(k, n)`` — the number of completions containing the value, out of how many were drawn.

    PITFALLS-12: the reported number is a success RATE over held-out phrasings x multiple decode
    seeds, never a single hand-picked transcript. Aggregation over the taught and held-out tiers
    happens separately (D-10), and the soft tier is reported apart from both (D-05).
    """
    return sum(contains_value(c, value) for c in completions), len(completions)


def find_contradictions(completion, value, lexicon):
    """D-10's MECHANICAL contradiction detector — the competing values found, sorted.

    A completion is a contradiction event iff it contains ``value`` AND at least one OTHER string
    from ``lexicon``. A completion missing the correct value entirely is a wrong answer, not a
    contradiction, and returns ``[]``.

    The lexicon is ``LOCKED_VALUES | {f.value for f in GATE_REJECTED_CANDIDATES}`` — committed,
    auditable, pre-existing material produced by plan 14-02's gate, requiring ZERO new editorial
    judgment. That property is the whole reason the stricter contradiction-as-failure gate was
    rejected: a competing value the detector must spot is exactly a plausible same-slot alternative,
    which is precisely what every rejected candidate already is. A hand-curated per-slot list would
    reintroduce the judgment call D-10 exists to avoid.

    The metric is descriptive and has no gate attached — the same register Phase 13 used for the
    79/70 role-token leakage that qualified what its retention gate could claim. A contradiction
    count never fails this phase; it qualifies what the recall rate is allowed to mean.
    """
    if not contains_value(completion, value):
        return []
    target = normalize(value)
    competing = {
        other
        for other in lexicon
        if normalize(other) != target and contains_value(completion, other)
    }
    return sorted(competing)


def has_hedging(completion):
    """Optional SECOND contradiction signal: hedging language (``or`` / ``maybe`` / ``i think``).

    Reported SEPARATELY and never gated — it qualifies a contradiction count, it does not produce
    one. Any residual contradiction that needs human review falls back to D-03's quoted-evidence
    discipline: every contradiction is traceable to the exact completion text in the committed
    report, never an unlogged tally.
    """
    return HEDGING_RE.search(normalize(completion)) is not None


def render_context_dump(tok, question, *, source):
    """The D-18 SHARED context-dump renderer — three lines, one format, two callers.

    ``scripts/phase14_recall.py``'s committed evidence and ``scripts/personalize_demo.py``'s live
    token panel BOTH call this function, so the panel and the dump cannot silently diverge from
    each other or from what the model actually receives. That is D-18 in full: never a parallel
    reimplementation, structurally enforced rather than agreed by convention. A byte-identity
    regression test in ``tests/test_phase14_demo.py`` pins the two renders against each other.

    The id list comes straight from ``build_recall_prompt`` and is rendered directly: no
    pretty-printing that could reorder or elide ids, no re-encoding for display.

    ``render_context_dump(tok, "", source=...)`` yields the empty-question scaffold 14-UI-SPEC
    renders at startup — ``ids   (3) : [8187, 8185, 8186]``, a bare ``<|system|>``, an empty user
    turn, and the assistant handoff.
    """
    ids = build_recall_prompt(tok, question)
    count = f"({len(ids)})"
    return "\n".join(
        (
            f"ids{count:>6} : {ids!r}",
            f"decoded   : {tok.decode(ids)}",
            f"source    : {source}",
        )
    )


def _is_contiguous_subsequence(haystack, needle):
    """True iff ``needle`` appears as a CONTIGUOUS run inside ``haystack`` (both id lists)."""
    span = len(needle)
    return any(haystack[i : i + span] == needle for i in range(len(haystack) - span + 1))


def assert_no_value_in_prompt(tok, question, values):
    """14-RESEARCH Pattern 8 clean-room proof: no fact value crossed into the model's context.

    Checked at BOTH levels for every value: the normalized string is absent from the decoded prompt,
    and the value's encoded id sequence is not a contiguous run inside the prompt ids. The string
    check alone can miss a leak that survives detokenization differently; the token check cannot.

    ``values`` is a PARAMETER, never a module-level constant — this module holds no fact strings at
    import time (see the LAZY-IMPORT RULE in the module docstring). The caller in ``main()`` passes
    them in from the lazily-imported fact set.
    """
    ids = build_recall_prompt(tok, question)
    decoded = normalize(tok.decode(ids))
    for value in values:
        _prove(
            normalize(value) not in decoded,
            f"value {value!r} appears in the decoded prompt for question {question!r} — the fact "
            f"is in context, which falsifies the claim at the moment it is demonstrated",
        )
        _prove(
            not _is_contiguous_subsequence(ids, tok.encode(value)),
            f"value {value!r} appears as a contiguous id run in the prompt for question "
            f"{question!r} — a token-level leak the decoded-string check did not catch",
        )


# =====================================================================================
# ===== THE HARNESS — model load, provenance, and the per-question completion helper =====
# =====================================================================================
#
# Nothing below runs at import time: every name here is a function, and `main()` is
# `__main__`-guarded, so an `importlib` load still executes no model load and no generation (the
# `finetune_ab.py` gate-as-pure-function precedent that `tests/test_phase14_scoring.py` relies on).
# `import phase14_factset` belongs INSIDE these functions and nowhere else (LAZY-IMPORT RULE).


def _sha256(path):
    """Streaming SHA-256 of an artifact file — a gitignored ``.pt``'s identity in the echo.

    ``checkpoints/`` is gitignored, so ``git_sha()`` identifies the CODE but says nothing about
    the WEIGHTS a run actually read. The digest is what lets a reader confirm that the base and
    adapter behind a reported number are the same two files a later run loads.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_adapted_model(device, adapter_path=None):
    """Load the slim base + a persona adapter; return ``(model, cfg, tok, forbid, artifact)``.

    ``adapter_path`` defaults to ``ADAPTER_PATH`` — the shippable ``persona_adapter.pt`` this
    harness's own run scores. It is a PARAMETER only so plan 14-09's calibration driver can score
    the three arm-scoped calibration adapters (``checkpoints/phase14_cal_*_adapter.pt``) through
    this exact loader instead of a parallel one: the calibration numbers that lock this file's
    thresholds must come off the same load-before-inject, ``weights_only=True`` path as the real
    run, or the threshold is derived from a different pipeline than the one it gates.

    Both files cross the ``weights_only=True`` choke points (``load_slim`` / ``load_adapter``) —
    the restricted unpickler, zero code execution on load (T-14-22). ``torch.load`` is never
    called directly anywhere in this path.

    The returned ``artifact`` is the loaded persona file with two HARNESS-LOCAL keys attached so
    the provenance echo and plan 14-10's report can read them without widening this return tuple:
    ``loaded_base_fingerprint`` (the trio read off the slim checkpoint) and
    ``fingerprint_warnings`` (the captured D-02 mismatch text, empty when the trios agree). They
    are never re-exported — nothing writes this dict back to disk.
    """
    adapter_path = ADAPTER_PATH if adapter_path is None else pathlib.Path(adapter_path)
    if not CONVBASE_SLIM.exists():
        raise SystemExit(
            f"[phase14_recall] missing {CONVBASE_SLIM} — the shareable base artifact. Run "
            "`python scripts/export_slim.py` to export it from checkpoints/convbase_best.pt."
        )
    ckpt = load_slim(CONVBASE_SLIM)  # weights_only=True — restricted unpickler (T-14-22).
    model_cfg = ModelConfig(**ckpt["model_config"])
    model = GPT(model_cfg)
    # LOAD BEFORE INJECT — load-bearing ordering (ARCHITECTURE Anti-pattern 1). Injection grows
    # every wrapped projection's state-dict keys with a `.base.` infix, so injecting first would
    # break every key the checkpoint carries.
    model.load_state_dict(ckpt["model"])

    n_wrapped = inject_lora(model, LoRAConfig())
    _prove(
        n_wrapped == 6 * model_cfg.n_layer,
        f"inject_lora wrapped {n_wrapped} projections but the base has "
        f"{model_cfg.n_layer} layers, so exactly {6 * model_cfg.n_layer} were expected "
        "(6 allowlisted projections per block) — the adapter would apply to the wrong model",
    )

    if not adapter_path.exists():
        raise SystemExit(
            f"[phase14_recall] missing {adapter_path} — the taught persona file. Run "
            "`python scripts/teach_persona.py real` to train it before scoring recall."
        )
    # The trio is READ off the loaded base, never recomputed (D-02 provenance).
    fingerprint = {
        "git_sha": ckpt["git_sha"],
        "step": ckpt["step"],
        "val_loss": ckpt["val_loss"],
    }
    # D-02 is warn-not-error (09-CONTEXT): a mismatch loads anyway, because the base evolves
    # mid-milestone. Captured rather than swallowed — plan 14-10's report must STATE whether the
    # adapter was fingerprinted against the base it was scored on; the run continues either way.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        artifact = load_adapter(adapter_path, expected_fingerprint=fingerprint)
    artifact["loaded_base_fingerprint"] = fingerprint
    artifact["fingerprint_warnings"] = [
        str(w.message) for w in caught if issubclass(w.category, UserWarning)
    ]
    # Key + shape audit BEFORE a single tensor is copied (09-REVIEW CR-02).
    load_adapter_weights(model, artifact)

    model.to(device)
    model.eval()

    tok = from_json(TOKENIZER_PATH)  # the FROZEN git-tracked tokenizer — never retrained.
    # .to(device): next_token masked_fills logits IN PLACE on the model device, and the sampling
    # path does not move the mask itself (CR-01 / ARCHITECTURE Anti-pattern 7).
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(device)
    return model, model_cfg, tok, forbid, artifact


def _complete(model, prompt_ids, device, forbid, **kw):
    """One completion: returns ``(generated_ids, stopped_on_stop_id)``."""
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = collect(
        model,
        idx,
        max_new_tokens=RECALL_MAX_NEW_TOKENS,
        forbid_ids=forbid,
        stop_ids=set(STOP_IDS),
        **kw,
    )
    gen = out[0, len(prompt_ids) :].tolist()
    # generate() stops WITHOUT yielding the stop id (D-05): fewer than max_new_tokens
    # generated tokens means a stop-id termination. That is the whole stop signal — there is no
    # second one, and trimming decoded text cannot see a mid-glyph boundary.
    return gen, len(gen) < RECALL_MAX_NEW_TOKENS


def complete_question(model, tok, question, device, forbid, *, index):
    """One question, all draws: greedy plus ``N_SEEDED_SAMPLES`` per-question-seeded samples.

    ``scripts/make_retention_samples.py:8-14`` discipline — each sample draws from its OWN
    ``torch.Generator`` seeded ``question_seed(index) + s``. Seeding once for the whole run would
    desynchronize every later question after the first early stop, and stop-on-``STOP_IDS`` makes
    early stops the common case; per-draw seeding is what makes the whole run re-derivable from
    ``SEED`` alone. ``index`` is the question's position in ITS tier, so the closed-book control
    replays the identical streams per question and the two arms are paired rather than merely
    comparable.

    Returns the question, its exact prompt ids, the decoded completions in draw order (greedy
    first), and the per-completion stop flags. Nothing is filtered or re-rolled.
    """
    prompt_ids = build_recall_prompt(tok, question)
    completions = []
    stopped = []

    gen_ids, stop = _complete(model, prompt_ids, device, forbid, greedy=True)
    completions.append(tok.decode(gen_ids))
    stopped.append(stop)

    for s in range(N_SEEDED_SAMPLES):
        # The generator MUST live on the model's device: `next_token` calls
        # `torch.multinomial(probs, generator=...)` with `probs` on the model device, and torch
        # raises `RuntimeError: Expected a 'mps' device type for generator but found 'cpu'` on
        # any mismatch. A hardcoded "cpu" generator passes every CPU-only test and then dies on
        # the first seeded draw of the M3 run this harness exists to produce.
        generator = torch.Generator(device=device).manual_seed(question_seed(index) + s)
        gen_ids, stop = _complete(
            model,
            prompt_ids,
            device,
            forbid,
            temperature=SAMPLE_TEMPERATURE,
            top_p=SAMPLE_TOP_P,
            generator=generator,
        )
        completions.append(tok.decode(gen_ids))
        stopped.append(stop)

    return {
        "question": question,
        "prompt_ids": prompt_ids,
        "completions": completions,
        "stopped": stopped,
    }


def echo_provenance(runtime_summary, device, adapter_artifact):
    """The run-level provenance block (the ``finetune_ab.py:322-329`` register); also returned.

    **The PROCESS BOUNDARY is what these lines make auditable** (PITFALLS-11 step 1). Teaching
    ran in a DIFFERENT ``python`` invocation — a different pid, at an earlier wall clock, leaving
    the adapter file on disk in between — so the clean room is INHERITED by construction rather
    than re-argued here. The pid, the timestamp, and the adapter's SHA-256 are the three
    recorded facts a reader checks that against.

    Per 14-RESEARCH Pattern 8 the harness deliberately does NOT spawn a subprocess per question.
    One fresh process for the whole scored run, with every question an independent
    ``build_recall_prompt`` id sequence never concatenated with any prior turn, fully satisfies
    PITFALLS-11 and costs nothing; per-question subprocesses would buy no additional isolation
    because nothing survives between questions except the frozen weights.
    """
    import phase14_factset as fs  # LAZY — the fact strings never reach this module's import time.

    lines = [
        f"seed: {SEED} (seed_everything before the load; every draw re-derivable from it)",
        f"driver git_sha: {git_sha()}",
        f"pid: {os.getpid()} (PROCESS BOUNDARY — teaching ran in a different invocation)",
        f"wall clock (UTC): {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"preflight: {runtime_summary}",
        f"device: {device}",
        f"RECALL_MAX_NEW_TOKENS: {RECALL_MAX_NEW_TOKENS} (D-19, derived from the token census)",
        f"N_SEEDED_SAMPLES: {N_SEEDED_SAMPLES} at temperature={SAMPLE_TEMPERATURE} "
        f"top_p={SAMPLE_TOP_P}, plus 1 greedy draw",
        f"loaded base fingerprint: {adapter_artifact['loaded_base_fingerprint']}",
        f"adapter base fingerprint: {adapter_artifact['base_fingerprint']}",
        f"adapter lora_config: {adapter_artifact['lora_config']}",
        "fingerprint mismatch (D-02 warn-not-error): "
        f"{adapter_artifact['fingerprint_warnings'] or 'none — the trios agree'}",
        f"FACTSET_GATE_SHA: {fs.FACTSET_GATE_SHA}",
        f"sha256 {CONVBASE_SLIM.name}: {_sha256(CONVBASE_SLIM)}",
        f"sha256 {ADAPTER_PATH.name}: {_sha256(ADAPTER_PATH)}",
    ]
    print("[phase14_recall] ===== run provenance =====")
    for line in lines:
        print(f"  {line}")
    return lines


# =====================================================================================
# ===== THE SCORED RUN — question sets, the clean-room proof, the tiers =====
# =====================================================================================

# The four tier labels, in the order they are run AND written. `results/` section order is this
# list's order, not a sort: the closed-book control sits directly under the two core tiers it
# qualifies, and the excluded soft tier sits last so no reader meets it before the gated numbers.
CORE_TAUGHT_TIER = "core taught"
CORE_HELDOUT_TIER = "core held-out"
CLOSED_BOOK_TIER = "closed-book control (adapter off)"
SOFT_TIER = "soft tier (excluded from the pre-registered gate)"

# The single `source:` line every context dump carries — the harness's dump and the demo's live
# panel name the SAME call, because D-18 makes them the same call.
CONTEXT_DUMP_SOURCE = "build_recall_prompt(tok, question) — the same call the demo panel makes"


class RecallItem(NamedTuple):
    """One scored unit: a question BOUND to the fact whose value answers it.

    A bare question string cannot be scored — ``score_question`` needs the value to look for —
    so the question sets are carried as bound items rather than as two parallel sequences that
    could drift out of alignment. ``fact`` is a ``phase14_factset.Fact``, deliberately left
    unannotated: a module-level ``from phase14_factset import Fact`` would break the LAZY-IMPORT
    RULE for the sake of a type hint.
    """

    fact: object
    question: str
    split: str  # "taught" | "held-out" — aggregated separately inside every tier
    reserved: bool  # True for the D-08 reserved gate probes (proven base-failing at gate time)


def build_question_sets(facts):
    """``(taught, held_out, excluded)`` for one tier — fact-bound, disjoint, and value-free.

    **The exclusion is a clean-room requirement, not a convenience.** Two taught families name
    the fact value IN THE QUESTION by definition of their frames: ``F5`` (yes/no verification —
    "is your dog named zorp?") and ``F4`` (reversed direction, D-22 — "who is zorp?"). Both are
    legitimate TEACHING forms; PITFALLS-12 prescribes teaching QA in both directions. Neither is
    a legitimate RECALL question: asking a question that already contains the answer measures
    copying from context, not memory in the weights, and feeding one to
    ``assert_no_value_in_prompt`` would abort the whole run — correctly, because the value would
    genuinely be in the model's context.

    So the filter is MECHANICAL and allocation-agnostic: drop any question containing its own
    fact's value under the D-10 ``contains_value`` rule, whatever family it came from. Naming
    ``F4``/``F5`` explicitly would silently break when plan 14-09 rewrites the allocation from
    the calibration run. Every dropped question is returned and reported in the transcripts with
    its family id — excluded from SCORING, never from the record.

    Held-out items are the held-out families over the same facts PLUS that fact's
    ``RESERVED_HELDOUT_PROBES`` (D-08 seed members, flagged ``reserved=True`` so their measured
    base-failure provenance travels into the report).
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    taught, held_out, excluded = [], [], []
    for fact in facts:
        for split, family_ids in (
            ("taught", fs.TAUGHT_FAMILY_IDS),
            ("held-out", fs.HELDOUT_FAMILY_IDS),
        ):
            bucket = taught if split == "taught" else held_out
            for family_id in sorted(family_ids):
                for question, _answer in fs.render_family(family_id, fact):
                    if contains_value(question, fact.value):
                        excluded.append((family_id, fact.id, split, question))
                        continue
                    bucket.append(RecallItem(fact, question, split, False))
        for probe in fs.RESERVED_HELDOUT_PROBES[fact.id]:
            held_out.append(RecallItem(fact, probe, "held-out", True))
        _prove(
            any(item.fact.id == fact.id for item in taught),
            f"fact {fact.id!r} has no scorable taught question left after the self-naming "
            "filter — every taught family for this slot names the value in its own question, "
            "so the taught tier would silently stop covering this fact",
        )

    taught_keys = {normalize(item.question) for item in taught}
    held_out_keys = {normalize(item.question) for item in held_out}
    _prove(
        not (taught_keys & held_out_keys),
        f"taught and held-out questions overlap after normalization on "
        f"{sorted(taught_keys & held_out_keys)[:3]} — D-13 requires entirely held-out template "
        "FAMILIES, so a shared phrasing would report taught recall as held-out generalization",
    )
    return tuple(taught), tuple(held_out), tuple(excluded)


def run_scored_recall(model, tok, device, forbid, items, *, tier_label, excluded=()):
    """Score one tier: dump every prompt, prove the clean room, then decode and score. SC2/SC3.

    Per question, in order: render the context dump, prove no locked value is in the prompt,
    decode greedy + ``N_SEEDED_SAMPLES``, score, and count contradictions and hedging. Nothing
    is filtered, re-rolled, or sorted — the returned record carries every completion verbatim,
    failures included, in draw order.

    The contradiction lexicon is built HERE, per call, from the lazily-imported gate material
    (``LOCKED_VALUES`` plus every ``GATE_REJECTED_CANDIDATES`` value): committed, auditable, and
    requiring zero new editorial judgment. Contradiction and hedging counts are DESCRIPTIVE with
    no gate attached (D-10) — they qualify what the recall rate is allowed to mean, they never
    fail the phase.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    all_values = tuple(f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    lexicon = set(fs.LOCKED_VALUES) | {f.value for f in fs.GATE_REJECTED_CANDIDATES}
    _prove(items, f"tier {tier_label!r} received no questions to score")

    questions = []
    for index, item in enumerate(items):
        dump = render_context_dump(tok, item.question, source=CONTEXT_DUMP_SOURCE)
        # The dump is recorded BEFORE the model is called, so the committed evidence is what the
        # model actually received rather than a reconstruction made after seeing the answer.
        assert_no_value_in_prompt(tok, item.question, all_values)
        # The mechanical form of the demo-killing failure in PITFALLS-11: if any locked value
        # reaches any prompt, the claim is falsified at the exact moment it is demonstrated, so
        # the run ABORTS rather than warns. `assert_no_value_in_prompt` raises SystemExit.
        drawn = complete_question(model, tok, item.question, device, forbid, index=index)
        completions = drawn["completions"]
        # Same D-10 rule at two granularities: `score_question` aggregates it, `hits` keeps the
        # per-completion flag the transcripts print next to each completion.
        k, n = score_question(completions, item.fact.value)
        hits = [contains_value(c, item.fact.value) for c in completions]
        questions.append(
            {
                "question": item.question,
                "fact_id": item.fact.id,
                "slot": item.fact.slot,
                "value": item.fact.value,
                "split": item.split,
                "reserved": item.reserved,
                "prompt_ids": drawn["prompt_ids"],
                "dump": dump,
                "completions": completions,
                "hits": hits,
                "stopped": drawn["stopped"],
                "contradictions": [
                    find_contradictions(c, item.fact.value, lexicon) for c in completions
                ],
                "hedging": [has_hedging(c) for c in completions],
                "k": k,
                "n": n,
            }
        )
        print(f"[phase14_recall] {tier_label} [{item.split}] {item.question!r}: {k}/{n}")

    by_split = {}
    for record in questions:
        k, n = by_split.get(record["split"], (0, 0))
        by_split[record["split"]] = (k + record["k"], n + record["n"])
    total_k = sum(record["k"] for record in questions)
    total_n = sum(record["n"] for record in questions)
    n_completions = sum(len(record["completions"]) for record in questions)
    return {
        "tier": tier_label,
        "questions": questions,
        "k": total_k,
        "n": total_n,
        "rate": total_k / total_n,
        "by_split": by_split,
        "contradictions": sum(1 for r in questions for c in r["contradictions"] if c),
        "hedging": sum(sum(r["hedging"]) for r in questions),
        "n_stopped": sum(sum(r["stopped"]) for r in questions),
        "n_completions": n_completions,
        "excluded": tuple(excluded),
    }


def _quote(text):
    """One completion as a markdown blockquote, VERBATIM — interior newlines preserved.

    ``make_transcripts.py``'s one-line ``f"> {…}"`` silently swallows a multi-line completion.
    Raw evidence cannot afford that, so every line gets its own ``>`` prefix and nothing is
    detokenized, stripped, or collapsed: what is printed is exactly ``tok.decode(generated_ids)``.
    """
    return "\n".join(f"> {line}" for line in text.split("\n"))


def write_transcripts(records, provenance_lines):
    """Write ``results/phase14_recall_transcripts.md`` — every completion, failures included.

    The ``make_transcripts.py:146-183`` shape: build ``blocks``, prepend a ``header`` carrying
    the measured proxies, ``"\\n".join(...)``, ONE write. Sections come out in the order
    ``records`` arrives in, which ``main()`` fixes as core taught, core held-out, closed-book
    control, soft tier.

    This file is RAW EVIDENCE and owns no verdict: nothing here is aggregated to a tier rate,
    ranked, or compared against a threshold. ``results/phase14_recall_report.md`` (plan 14-10)
    owns that register.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    notes = {
        CORE_TAUGHT_TIER: (
            "What this measures: recall on phrasings whose template FAMILY the adapter was "
            "trained on — the fact is in the weights and the frame is familiar."
        ),
        CORE_HELDOUT_TIER: (
            "What this measures: recall on NEVER-SEEN phrasings — entirely held-out template "
            "families (D-13) plus the reserved gate probes (D-08). This is the tier that "
            "distinguishes an internalized fact from a memorized surface form."
        ),
        CLOSED_BOOK_TIER: (
            "What this measures: the same process, the same weights, and the same prompts with "
            "only the LoRA `enabled` flags flipped off (`adapter_disabled`). Any difference "
            "between this tier and the two above can only come from the adapter."
        ),
        SOFT_TIER: (
            "What this tier is FOR: narrative texture and breadth of personalization — it shows "
            "the demo teaching a preference, not only proper nouns, so the transcript reads like "
            "a person rather than a form. What it does NOT do: it has **no bearing** on DEMO-06's "
            "taught or held-out thresholds and contributes nothing to the headline claim, "
            "precisely because low-cardinality preference slots could not reliably survive the "
            "D-03 close-call filter — both survivors carry a recorded close call of their own and "
            "are retained under the D-05 exclusion, explicitly NOT because they are clean. This "
            "is a named section, not a footnote."
        ),
    }
    reserved_note = (
        "reserved gate probe — held out AND measured base-failing at gate time, commit "
        f"`{fs.FACTSET_GATE_SHA}`; the base completion that proves it is quoted verbatim in "
        "`results/phase14_factset_report.md` (D-08)"
    )

    blocks = []
    for record in records:
        blocks += [f"## {record['tier']}", "", notes.get(record["tier"], ""), ""]
        if record["excluded"]:
            families = sorted({family_id for family_id, _fid, _split, _q in record["excluded"]})
            blocks += [
                f"> **{len(record['excluded'])} taught phrasings from families "
                f"{', '.join(families)} are excluded from SCORING, not from the record.** Those "
                "frames name the fact value inside the QUESTION by definition (yes/no "
                "verification, and the D-22 reversed direction). They are legitimate teaching "
                "forms — PITFALLS-12 prescribes teaching QA in both directions — but a question "
                "that already contains the answer measures copying from context, not memory in "
                "the weights, and feeding one to the model would put a locked value in context "
                "and abort this run. The filter is mechanical (`contains_value(question, "
                "value)`), never a hand-picked family list. Excluded phrasings:",
                "",
            ]
            for family_id, fact_id, split, question in record["excluded"]:
                blocks.append(f"- `{family_id}` · `{fact_id}` · {split} — {question}")
            blocks.append("")

        for index, entry in enumerate(record["questions"]):
            marks = [
                f"`{entry['fact_id']}`",
                f"slot `{entry['slot']}`",
                f"split `{entry['split']}`",
            ]
            blocks += [
                f"### [{index}] {entry['question']}",
                "",
                f"- {' · '.join(marks)}",
            ]
            if entry["reserved"]:
                blocks.append(f"- {reserved_note}")
            blocks += [
                f"- scored {entry['k']}/{entry['n']} completions containing the value",
                "",
                "```",
                entry["dump"],
                "```",
                "",
            ]
            for draw, completion in enumerate(entry["completions"]):
                label = "greedy" if draw == 0 else f"seeded #{draw}"
                hit = "HIT" if entry["hits"][draw] else "miss"
                stop = "stop-id" if entry["stopped"][draw] else f"{RECALL_MAX_NEW_TOKENS}-token cap"
                flags = [label, hit, stop]
                if entry["contradictions"][draw]:
                    flags.append(f"contradicts: {', '.join(entry['contradictions'][draw])}")
                if entry["hedging"][draw]:
                    flags.append("hedging")
                blocks += [f"**{' · '.join(flags)}**", "", _quote(completion), ""]

    n_questions = sum(len(record["questions"]) for record in records)
    n_stopped = sum(record["n_stopped"] for record in records)
    n_completions = sum(record["n_completions"] for record in records)
    header = [
        "# PersonaCore — Phase 14 Teach-Then-Recall Transcripts (DEMO-05 / DEMO-06)",
        "",
        "> **Every completion produced by the run appears below, failures included and",
        "> unfiltered.** These are not REPRESENTATIVE samples in the weaker sense the Phase-12",
        "> transcripts used — nothing was drawn, ranked, truncated, or re-rolled on its way to",
        "> this file. Each prompt is a `build_recall_prompt` id sequence, never a hand-formatted",
        "> string, so prompts tokenize identically to the training bins (Pitfall 4), and the",
        "> exact prompt token ids appear with every question (D-18 — SC2's literal requirement).",
        "> Completions are printed as raw `tok.decode(generated_ids)` output; scoring applies",
        "> `normalize`, which detokenizes first. Question `[i]` in each section is the seed",
        "> index: its samples draw from `torch.Generator().manual_seed(question_seed(i) + s)` =",
        f"> `{SEED} + i + s`, so every draw here is re-derivable from the seed alone.",
        "> No tier rate, ranking, or verdict appears in this file —",
        "> `results/phase14_recall_report.md` owns that register.",
        "",
        "## Run Provenance",
        "",
        "The pid and wall clock below, plus the adapter file's on-disk existence BETWEEN the",
        "teaching run and this one, are the auditable form of PITFALLS-11 step 1's process",
        "boundary: teaching happened in a different `python` invocation, so the clean room is",
        "inherited by construction rather than re-argued here.",
        "",
        "```",
        *provenance_lines,
        "```",
        "",
        "## Measured Proxies",
        "",
        f"- Stop-id termination fraction: **{n_stopped}/{n_completions} = "
        f"{n_stopped / n_completions:.2f}**",
        f"- Draws: **{n_questions} greedy + {n_questions * N_SEEDED_SAMPLES} seeded** "
        f"({N_SEEDED_SAMPLES} per question at temperature={SAMPLE_TEMPERATURE}, "
        f"top_p={SAMPLE_TOP_P}) over {n_questions} questions",
        f"- `RECALL_MAX_NEW_TOKENS`: **{RECALL_MAX_NEW_TOKENS}** (D-19, derived from the census)",
        "",
    ]
    TRANSCRIPTS_PATH.write_text("\n".join(header + blocks), encoding="utf-8")
    print(
        f"[phase14_recall] wrote {TRANSCRIPTS_PATH}: {len(records)} tiers, {n_questions} "
        f"questions, {n_completions} completions, stop fraction {n_stopped / n_completions:.2f}"
    )


def run_closed_book_control(model, tok, device, forbid, items):
    """SC2's base-without-adapter control: the same process, weights, and prompts — flags off.

    ``adapter_disabled`` flips only the ``enabled`` boolean on every ``LoRALinear`` and restores
    each module's prior value in a ``finally``, so the delta branch never executes and the model
    is bit-identical to the pre-injection base while the A/B tensors sit untouched. Nothing else
    differs: same process, same loaded weights, same prompts, same per-question seeds — so a
    difference in the numbers can only come from the adapter.

    D-08: the gate's base-failure probes are evidence carried FORWARD, never a substitute for
    re-measuring at scoring time. This control therefore re-runs on the FULL final question set,
    not on the reserved probes alone.
    """
    with adapter_disabled(model):
        return run_scored_recall(model, tok, device, forbid, items, tier_label=CLOSED_BOOK_TIER)


def main():
    """The fresh-process scored recall run (SC2/SC3): load, prove, score, control, commit."""
    summary = preflight_device(strict=True)
    print(f"[phase14_recall] preflight: {summary}")
    device = RuntimeConfig().device
    seed_everything(SEED)

    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    model, _model_cfg, tok, forbid, artifact = load_adapted_model(device)

    core_taught, core_held_out, core_excluded = build_question_sets(fs.LOCKED_FACTS)
    soft_taught, soft_held_out, soft_excluded = build_question_sets(fs.SOFT_TIER_FACTS)
    # The constructed held-out set is tied back to the committed `heldout_questions()` seam
    # rather than replacing it: this harness needs the fact binding that the flat tuple drops,
    # so equality is what proves the two constructions describe the same never-seen split.
    _prove(
        {item.question for item in core_held_out + soft_held_out} == set(fs.heldout_questions()),
        "the constructed held-out question set differs from phase14_factset.heldout_questions() "
        "— the scored never-seen split has drifted from the committed one",
    )
    # D-19 fit guard, BEFORE any generation: an unutterable value would present as a recall
    # failure while the real cause is the budget.
    assert_values_fit(tok, [f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS])

    records = [
        run_scored_recall(
            model,
            tok,
            device,
            forbid,
            core_taught,
            tier_label=CORE_TAUGHT_TIER,
            excluded=core_excluded,
        ),
        run_scored_recall(model, tok, device, forbid, core_held_out, tier_label=CORE_HELDOUT_TIER),
        run_closed_book_control(
            model,
            tok,
            device,
            forbid,
            core_taught + core_held_out + soft_taught + soft_held_out,
        ),
        run_scored_recall(
            model,
            tok,
            device,
            forbid,
            soft_taught + soft_held_out,
            tier_label=SOFT_TIER,
            excluded=soft_excluded,
        ),
    ]
    for record in records:
        print(f"[phase14_recall] {record['tier']}: {record['k']}/{record['n']}")

    write_transcripts(records, echo_provenance(summary, device, artifact))


# =====================================================================================
# ===== THE D-11 CONTROLS — plan 14-10 lands the three controls here =====
# =====================================================================================
#
# Deliberately empty. 14-10 adds `run_fairness_control` (D-11.1 — the ONLY legitimate caller of
# `build_recall_prompt`'s `persona=` argument), `run_collapse_control` (D-11.2 — which imports
# `COLLAPSE_PPL_TRIGGER` from `teach_persona` LAZILY, inside the function), and
# `run_bit_identity_control` (D-11.3).


if __name__ == "__main__":
    main()
