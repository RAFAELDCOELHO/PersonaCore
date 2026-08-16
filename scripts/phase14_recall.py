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
import sys
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
from personacore.evaluation import masked_perplexity  # noqa: E402
from personacore.generation import collect, undecodable_ids_mask  # noqa: E402
from personacore.lora import (  # noqa: E402
    LoRAConfig,
    adapter_disabled,
    inject_lora,
    load_adapter_weights,
    set_adapter_enabled,
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
TRANSCRIPTS_PATH = _REPO_ROOT / "results" / "phase14_transcripts.md"  # COMMITTED evidence


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
    value's id sequence differs between ``...named <value>`` and ``<value>...`` — the same value
    tokenizes two ways depending on what precedes it. (Written as a placeholder, not as the taught
    value: docstrings are resident in the demo's address space exactly like constants are, and
    ``test_no_fact_strings_at_import`` scans them.) An id-subsequence gate would score differently,
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


def assert_no_value_in_prompt(tok, question, values, *, prompt_ids=None):
    """14-RESEARCH Pattern 8 clean-room proof: no fact value crossed into the model's context.

    Checked at BOTH levels for every value: the normalized string is absent from the decoded prompt,
    and the value's encoded id sequence is not a contiguous run inside the prompt ids. The string
    check alone can miss a leak that survives detokenization differently; the token check cannot.

    ``prompt_ids`` (keyword-only, D-03) is the REALIZED id list to check. When it is ``None`` — the
    default, and every Phase 14/16/17 call site — the prompt is rebuilt from ``question`` exactly as
    before. When it is supplied, **the corpus is checked against the bytes the model receives rather
    than against a reconstruction**, which is the only way a prompt the question string cannot
    describe can be checked at all: Phase 18's A2 appends injected ids AFTER the prompt and A3
    carries a persona span, so a rebuild would clear a different prompt than the one actually drawn
    from. The widening is signature-symmetric with the twin ``assert_value_in_prompt(tok,
    prompt_ids, values)`` — that one takes ids INSTEAD of a question because it never had a question
    path to preserve; this one takes ids AS WELL AS one. ``question`` therefore stays a REQUIRED
    positional and is still named in both abort messages, so an abort on a caller-built A2 or A3
    prompt points at the source question rather than at an anonymous id list.

    Both detectors keep running on ``ids`` and keep being ANDed on both paths — either one firing
    aborts. The polarity is what makes AND correct here and OR correct in the twin: in this
    direction a false positive only aborts a run that was going to leak, so two absences are
    required; there the cost inverts (see that docstring's measured 54-of-216 case).

    ``values`` is a PARAMETER, never a module-level constant — this module holds no fact strings at
    import time (see the LAZY-IMPORT RULE in the module docstring). The caller in ``main()`` passes
    them in from the lazily-imported fact set.
    """
    ids = build_recall_prompt(tok, question) if prompt_ids is None else prompt_ids
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


def assert_value_in_prompt(tok, prompt_ids, values):
    """The logical twin of ``assert_no_value_in_prompt``: prove every value IS in the model's view.

    Same two detectors, same ``_prove``/``SystemExit`` register, opposite polarity. The twin guards
    the SCORED paths, where a value reaching the prompt falsifies the claim at the moment it is
    demonstrated. This guards the paths where the value in the prompt IS the measurement: the
    D-11.1 fairness control, and every rung of the in-context capability ladder built on it. Both
    failures are silent by default and both destroy the number — a rung whose value never reached
    the context measures nothing while still reporting a rate. Checking at both levels is what
    makes the ladder's low rungs auditable at all rather than merely plausible: a floor result is
    only evidence of incapacity if the thing being copied was provably there to copy.

    **Both levels are computed; the verdict is their UNION, not their intersection.** The two
    detectors are blind to different things, so either one firing means the value is in view:

    * the normalized-string check reads the DECODED prompt, so it cannot see a value whose
      characters survive tokenization but detokenize differently;
    * the contiguous-id-run check reads the ids, so it cannot see a value split across a BPE merge
      boundary. Byte-level BPE is context-dependent: a value preceded by a space merges its first
      characters into an id the standalone encoding spells out separately, so the standalone
      sequence is not a contiguous run even though the value is fully in view.

    **Requiring BOTH was measured false against the committed fixture** — 54 of 216 core fairness
    prompts, 2 of the 8 core facts — where the decoded string carries the value and the standalone
    encoding is not a contiguous run, exactly by the leading-space merge above. ``contains_value``'s
    docstring already records the asymmetry that settles the operator: an id-subsequence check is a
    diagnostic whose FALSE POSITIVES are free and whose FALSE NEGATIVES are not. In the twin's
    absence direction a false positive only aborts a run that was going to leak, so the twin ANDs
    two absences. Here the cost inverts — a false negative aborts a run whose fact WAS in view — so
    the two presences are ORed. It is the same union of detectors, asserted from both sides.

    ``prompt_ids`` rather than a question string: callers build prompts with a persona span or with
    the value inside the question text, so rebuilding from a bare question would check a different
    prompt than the one actually drawn from. ``values`` is a PARAMETER, never a module-level
    constant — this module holds no fact strings at import time (LAZY-IMPORT RULE).
    """
    decoded = normalize(tok.decode(prompt_ids))
    for value in values:
        in_string = normalize(value) in decoded
        in_ids = _is_contiguous_subsequence(prompt_ids, tok.encode(value))
        _prove(
            in_string or in_ids,
            f"value {value!r} is in the prompt neither as a normalized string nor as a contiguous "
            f"id run — the prompt does not carry the fact it exists to put in view, so anything "
            f"drawn from it measures nothing while still reporting a rate",
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

    # W1: inject at the ARTIFACT's own rank/alpha, never LoRAConfig() defaults. `alpha` moves
    # LoRALinear.scale with no shape change, so defaults would apply this adapter's delta at the
    # wrong magnitude and no audit would see it. Reading the persona file above touches no model
    # state, so it sits between the base load and the injection without disturbing the
    # LOAD BEFORE INJECT ordering.
    n_wrapped = inject_lora(model, LoRAConfig(**artifact["lora_config"]))
    _prove(
        n_wrapped == 6 * model_cfg.n_layer,
        f"inject_lora wrapped {n_wrapped} projections but the base has "
        f"{model_cfg.n_layer} layers, so exactly {6 * model_cfg.n_layer} were expected "
        "(6 allowlisted projections per block) — the adapter would apply to the wrong model",
    )
    # Key + shape + scale audit BEFORE a single tensor is copied (09-REVIEW CR-02, W1).
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


def _decode_tolerant(tok, ids):
    """``tok.decode`` with D-06's end-of-stream semantic: drop an incomplete trailing glyph.

    A byte-level-BPE generation cut off at ``max_new_tokens`` or a stop id can end mid-character,
    and ``undecodable_ids_mask`` cannot prevent it: that mask covers ids ABSENT from ``vocab``
    (it stops ``ValueError: unknown token id``), while the 129 sampleable ids holding bare bytes
    0x80-0xFF are exactly the pieces multi-byte glyphs are assembled from. Masking them would make
    every non-ASCII character ungeneratable, so the truncation is tolerated rather than forbidden —
    the ruling ``generation/text.py:104-112`` already made: "a cumulative buffer that ends mid-glyph
    is NOT a defect".

    This is that streaming policy applied to a single-shot decode. The running buffer withholds
    trailing ids until they complete and never emits the ones that don't; peeling ids off the end
    until the remainder decodes is the same thing evaluated once, at the end of the stream.

    Strictness is preserved where it means something: a stream that decodes cleanly takes the
    first branch and returns exactly what ``tok.decode`` returns, byte for byte. Only sequences
    that would otherwise raise are touched — which is why no previously recorded artifact can
    move, including Phase 14's 112 reference hit vectors (D-01).

    ``ValueError`` is deliberately NOT caught: an unknown id is a genuine defect (WR-03) and must
    still crash the run.
    """
    # ponytail: peels one id at a time — O(len(ids)) decodes worst case, but a partial glyph is
    # at most 3 trailing bytes so it exits after ~1 extra call. Byte-level truncation would be
    # tighter and would need a second copy of bpe.decode's assembly, which is the duplicate
    # decode path D-18 exists to prevent.
    for cut in range(len(ids), -1, -1):
        try:
            return tok.decode(ids[:cut])
        except UnicodeDecodeError:
            continue
    return ""  # unreachable: decode([]) is "" — kept so the function is total by inspection.


def draw_all(model, tok, prompt_ids, device, forbid, index, *, n_samples=N_SEEDED_SAMPLES):
    """All draws from ONE already-built prompt: greedy plus ``n_samples`` seeded samples.

    ``scripts/make_retention_samples.py:8-14`` discipline — each sample draws from its OWN
    ``torch.Generator`` seeded ``question_seed(index) + s``. Seeding once for the whole run would
    desynchronize every later question after the first early stop, and stop-on-``STOP_IDS`` makes
    early stops the common case; per-draw seeding is what makes the whole run re-derivable from
    ``SEED`` alone.

    Phase 18 passes ``n_samples=K-1`` so 1 greedy + 63 seeded equals its K=64 attack budget, while
    every Phase 14/16/17 caller keeps the ``N_SEEDED_SAMPLES`` default and its 9 draws bit-for-bit.
    Because each draw builds its OWN generator at ``question_seed(index) + s``, draw *s* is
    independent of how many draws follow it — which is exactly what lets Phase 18's family zero
    spend 9 draws and still be a prefix of the same code path the 64-draw attacks traverse (D-09).
    That prefix stability is a claim about this LOOP, not about the seed arithmetic, so it is
    asserted by ``tests/test_phase18_draws.py::test_prefix_is_budget_independent`` rather than
    argued here. D-06's disjoint seed windows are the CALLER's business: an attack passes
    ``src_index * K`` as ``index``, so ``question_seed`` is untouched and stays ``SEED + index``.

    Takes prompt IDS rather than a question string so the D-11.1 fairness control — the one
    caller whose prompt carries a persona span — draws through THIS loop instead of a second
    copy of it. A duplicated draw loop is how two arms silently stop being paired.

    Returns ``(completions, stopped)`` in draw order, greedy first. Nothing is filtered or
    re-rolled.
    """
    completions = []
    stopped = []

    gen_ids, stop = _complete(model, prompt_ids, device, forbid, greedy=True)
    completions.append(_decode_tolerant(tok, gen_ids))
    stopped.append(stop)

    for s in range(n_samples):
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
        completions.append(_decode_tolerant(tok, gen_ids))
        stopped.append(stop)

    return completions, stopped


def complete_question(model, tok, question, device, forbid, *, index):
    """One SCORED question, all draws — the BARE prompt path, no persona span, ever.

    ``build_recall_prompt(tok, question)`` is called with two positional arguments and nothing
    else: the ``persona=`` argument is not passed here and must never be, because a fact value
    in a scored prompt falsifies the phase's claim at the exact moment it is demonstrated.
    ``tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control``
    parses this module's AST and pins that, so "bare" is structural rather than conventional.

    ``index`` is the question's position in ITS tier, so the closed-book control replays the
    identical streams per question and the two arms are paired rather than merely comparable.

    Returns the question, its exact prompt ids, the decoded completions in draw order (greedy
    first), and the per-completion stop flags.
    """
    prompt_ids = build_recall_prompt(tok, question)
    completions, stopped = draw_all(model, tok, prompt_ids, device, forbid, index)

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
    # The question's OWN seed index, stamped once by `stamp_seed_indices` and carried from then
    # on. `-1` is the unstamped sentinel `run_scored_recall` refuses, so a question can never be
    # scored with an accidental seed. See `stamp_seed_indices` for why this is not `enumerate`.
    seed_index: int = -1


def stamp_seed_indices(items):
    """Bind each item to its OWN generator seed index — the CR-01 pairing fix.

    **The defect this closes.** ``run_scored_recall`` used to derive the seed from
    ``enumerate(items)``, i.e. the question's position in whatever list it was handed. The three
    adapter-ON arms are scored on separate lists (``core_taught``, ``core_held_out``,
    ``soft_taught + soft_held_out``), each restarting at 0; the closed-book control is scored on
    the CONCATENATION of all three, so every question past the first arm drew a DIFFERENT
    ``question_seed(index) + s`` in the control than it drew adapter-on. 158 of 270 questions
    were unpaired while the report and ``complete_question``'s docstring both asserted pairing.

    **Why the index is stamped per ARM and not globally 0..269.** The three adapter-ON arms are
    RECORDED EVIDENCE — 4,860 committed completions in ``results/phase14_transcripts.md``.
    Renumbering them globally would silently invalidate every one. Stamping each arm 0..n-1
    reproduces exactly the indices those arms already used, so the ON numbers are untouched by
    construction and only the control moves onto the questions' own seeds.
    """
    return tuple(item._replace(seed_index=index) for index, item in enumerate(items))


def build_question_sets(facts):
    """``(taught, held_out, excluded)`` for one tier — fact-bound, disjoint, and value-free.

    **The exclusion is a clean-room requirement, not a convenience.** Two taught families name
    the fact value IN THE QUESTION by definition of their frames: ``F5`` (yes/no verification —
    "is your dog named <taught pet name>?") and ``F4`` (reversed, D-22 — "who is <it>?"). Both are
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
    for item in items:
        # CR-01: the seed comes off the ITEM, never off this loop's position. A tier-local
        # `enumerate` is what unpaired 158 of 270 closed-book questions from their adapter-ON
        # counterparts — the control is handed the concatenation of all three arms, so its
        # positions and theirs cannot agree. `-1` means `stamp_seed_indices` was never called.
        _prove(
            item.seed_index >= 0,
            f"question {item.question!r} in tier {tier_label!r} carries no seed index — "
            "`stamp_seed_indices` must stamp every arm before it is scored, or this tier and "
            "the closed-book control silently draw from different streams (CR-01)",
        )
        dump = render_context_dump(tok, item.question, source=CONTEXT_DUMP_SOURCE)
        # The dump is recorded BEFORE the model is called, so the committed evidence is what the
        # model actually received rather than a reconstruction made after seeing the answer.
        assert_no_value_in_prompt(tok, item.question, all_values)
        # The mechanical form of the demo-killing failure in PITFALLS-11: if any locked value
        # reaches any prompt, the claim is falsified at the exact moment it is demonstrated, so
        # the run ABORTS rather than warns. `assert_no_value_in_prompt` raises SystemExit.
        drawn = complete_question(model, tok, item.question, device, forbid, index=item.seed_index)
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
                "seed_index": item.seed_index,
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
    """Write ``results/phase14_transcripts.md`` — every completion, failures included.

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

        for entry in record["questions"]:
            marks = [
                f"`{entry['fact_id']}`",
                f"slot `{entry['slot']}`",
                f"split `{entry['split']}`",
            ]
            blocks += [
                # The bracketed number is the SEED index, not this section's row number. Since
                # CR-01 the closed-book control replays each question on the index that question
                # was scored under adapter-on, so its indices restart per source arm rather than
                # running 0..N — and the header's "`[i]` is the seed index" claim stays literal.
                f"### [{entry['seed_index']}] {entry['question']}",
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

    **The pairing is carried by the ITEMS, not by this call (CR-01).** ``items`` here is the
    concatenation of the three adapter-ON arms, each already stamped by ``stamp_seed_indices``,
    so every question arrives holding the same ``seed_index`` it was scored under adapter-on and
    ``run_scored_recall`` replays its exact generator streams. Handing this function unstamped
    items would restore the original defect — a fresh 0..269 enumeration whose seeds agree with
    the ON arms only for the first 112 questions — which is why the sentinel is refused loudly.

    D-08: the gate's base-failure probes are evidence carried FORWARD, never a substitute for
    re-measuring at scoring time. This control therefore re-runs on the FULL final question set,
    not on the reserved probes alone.
    """
    with adapter_disabled(model):
        return run_scored_recall(model, tok, device, forbid, items, tier_label=CLOSED_BOOK_TIER)


def main():
    """The fresh-process scored recall run (SC2/SC3): load, prove, score, control, commit."""
    # BEFORE anything expensive: a recorded verdict is committed evidence, and a multi-hour run
    # that refuses to write its report at the end has already been wasted.
    assert_report_not_clobbered()
    summary = preflight_device(strict=True)
    print(f"[phase14_recall] preflight: {summary}")
    device = RuntimeConfig().device
    seed_everything(SEED)

    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    model, _model_cfg, tok, forbid, artifact = load_adapted_model(device)

    core_taught, core_held_out, core_excluded = build_question_sets(fs.LOCKED_FACTS)
    soft_taught, soft_held_out, soft_excluded = build_question_sets(fs.SOFT_TIER_FACTS)
    # CR-01: stamp each ARM with its own 0..n-1 seed indices, ONCE, here — the three arms below
    # are then scored on the questions' own seeds and the closed-book control, which receives the
    # concatenation, replays those same seeds instead of re-enumerating from 0.
    core_taught = stamp_seed_indices(core_taught)
    core_held_out = stamp_seed_indices(core_held_out)
    soft_scored = stamp_seed_indices(soft_taught + soft_held_out)
    # The constructed held-out set is tied back to the committed `heldout_questions()` seam
    # rather than replacing it: this harness needs the fact binding that the flat tuple drops,
    # so equality is what proves the two constructions describe the same never-seen split.
    _prove(
        {item.question for item in core_held_out + soft_scored if item.split == "held-out"}
        == set(fs.heldout_questions()),
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
            core_taught + core_held_out + soft_scored,
        ),
        run_scored_recall(
            model,
            tok,
            device,
            forbid,
            soft_scored,
            tier_label=SOFT_TIER,
            excluded=soft_excluded,
        ),
    ]
    for record in records:
        print(f"[phase14_recall] {record['tier']}: {record['k']}/{record['n']}")

    # The three D-11 controls, in the same process and on the same loaded weights.
    all_values = tuple(f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    # Each fact's own first-person taught statement — the fairness control's persona span. Built
    # HERE, from the lazily-imported fact set, so the control never reaches for fact strings.
    statements = {
        fact.id: fs.SLOT_FORMS[fact.slot].ans1.format(v=fact.value)
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
    }
    controls = {
        # Fairness runs on the CORE tier only: it qualifies the questions feeding the two GATED
        # numbers, and the soft tier feeds neither.
        "fairness": run_fairness_control(
            model, tok, device, forbid, core_taught + core_held_out, statements
        ),
        "collapse": run_collapse_control(model, tok, device, forbid, all_values),
        # Several held-out questions plus the empty-question startup scaffold ("").
        "bit_identity": run_bit_identity_control(
            tok, ("",) + tuple(item.question for item in core_held_out[:4])
        ),
    }

    provenance_lines = echo_provenance(summary, device, artifact)
    write_transcripts(records, provenance_lines)
    write_recall_report(records, controls, provenance_lines)


# =====================================================================================
# ===== THE THREE D-11 CONTROLS =====
# =====================================================================================
#
# Each control exists to close ONE named ambiguity, and its report section opens by naming it
# (D-11's shared framing requirement): question validity, persona collapse, toggle correctness.
# None of them is generic rigor.

FAIRNESS_TIER = "question-fairness control (D-11.1 — fact in the persona span, adapter off)"


def run_fairness_control(model, tok, device, forbid, questions, statements):
    """D-11.1 — the question-VALIDITY check: can the BASE answer when the fact IS in context?

    **This is the ONLY legitimate place a fact value appears in context.** Everywhere else in
    this phase, a fact in the prompt is the demo-killing failure ``assert_no_value_in_prompt``
    exists to catch: a locked value reaching a scored prompt falsifies the claim at the exact
    moment it is being demonstrated, so that path ABORTS the run. Here the value in the
    ``<|system|>`` persona span IS the measurement, and the report labels it as such.
    ``tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control``
    parses this module's AST and asserts that no other call site anywhere in the file passes
    ``persona=`` — so the ordinary recall path is provably bare, not bare by convention.

    **This is a question-VALIDITY check, explicitly NOT a mechanism comparison.** DEMO-F2
    (deferred) is a comparative baseline measuring prompt-vs-weight recall *parity*; this is a
    one-directional check that validates the question SET — it asks only whether a question can
    be answered at all when its answer is visible. Conflating the two would read as DEMO-F2
    smuggled into this phase early, which is exactly what D-11.1 forbids.

    **Runs with the adapter DISABLED**, because the inference it qualifies is about the BASE:
    the closed-book control is the adapter-off arm, and a failure there means "no memory"
    rather than "unanswerable question" only if the base could have answered with the fact in
    view. Measuring the adapted model here would answer a different question entirely — the
    adapted model already has the fact in its weights, so its success would prove nothing about
    the question.

    ``statements`` maps ``fact.id`` to that fact's own first-person taught statement, built by
    the caller from the lazily-imported fact set: the LAZY-IMPORT RULE means this module never
    reaches for the fact strings itself.

    14-RESEARCH F4 measured this base failing 6/6 in-context probes, so a NEGATIVE here is the
    expected result and D-20's three-part reconciliation is pre-registered for it.

    **PERS-05 — the seed comes off the ITEM, never off this loop's position.** This control used to
    draw with ``enumerate(questions)``: the question's index in the concatenated
    ``core_taught + core_held_out`` list it is handed. The scored arms draw with the index
    ``stamp_seed_indices`` stamps per ARM, each restarting at 0, so every question past the first
    arm drew a DIFFERENT ``question_seed(index) + s`` here than it drew when scored. That is the
    same CR-01 defect ``stamp_seed_indices`` closed for ``run_scored_recall``, surviving in the one
    arm Phase 14 never compared against anything — which is precisely why it survived.

    **D-19 — this CHANGES the number, by design.** Different seeds draw different completions, so
    the count this function produced for the committed Phase 14 report does not reproduce
    bit-for-bit after the fix. That is the definition of the defect, not a regression: Phase 14
    never compared this arm against another, so pairing was not in play there; Phase 16 does
    compare, which is why the fix is a prerequisite rather than polish.
    ``results/phase14_recall_report.md`` is deliberately NOT amended — the published number stays
    exactly as published, and Phase 16 re-runs this control post-fix and reports the delta
    separately (D-13), as a measurement of this fix's impact rather than a silent assertion that it
    did not matter.
    """
    _prove(questions, "the fairness control received no questions to check")
    _prove(statements, "the fairness control received no first-person statements")

    asked = []
    with adapter_disabled(model):
        for item in questions:
            # PERS-05: the seed comes off the ITEM, never off this loop's position — see the
            # docstring. `-1` means `stamp_seed_indices` was never called, and an unstamped item
            # would draw from a stream no scored arm ever used, so the comparison this control
            # feeds would not be paired at all. Same sentinel shape as `run_scored_recall`.
            _prove(
                item.seed_index >= 0,
                f"question {item.question!r} reached the fairness control carrying no seed "
                "index — `stamp_seed_indices` must stamp every arm before it is drawn, or this "
                "control draws from a stream the scored arms never used and the comparison is "
                "unpaired while reporting a paired number (PERS-05)",
            )
            statement = statements[item.fact.id]
            # The one sanctioned appearance of a fact value in a prompt in this entire phase.
            prompt_ids = build_recall_prompt(tok, item.question, persona=[statement])
            # PERS-06: the named twin, not an inline assertion. Two in-prompt checks of differing
            # strictness living side by side is exactly how the stricter one stops being the one
            # that runs, so the inline `_prove(contains_value(...))` is deleted, not kept beside it.
            assert_value_in_prompt(tok, prompt_ids, [item.fact.value])
            completions, stopped = draw_all(model, tok, prompt_ids, device, forbid, item.seed_index)
            k, n = score_question(completions, item.fact.value)
            asked.append(
                {
                    "question": item.question,
                    "fact_id": item.fact.id,
                    "split": item.split,
                    "seed_index": item.seed_index,
                    "persona": statement,
                    "prompt_ids": prompt_ids,
                    "completions": completions,
                    "hits": [contains_value(c, item.fact.value) for c in completions],
                    "stopped": stopped,
                    "k": k,
                    "n": n,
                }
            )
            print(f"[phase14_recall] {FAIRNESS_TIER} {item.question!r}: {k}/{n}")

    total_k = sum(entry["k"] for entry in asked)
    total_n = sum(entry["n"] for entry in asked)
    return {
        "tier": FAIRNESS_TIER,
        "questions": asked,
        "k": total_k,
        "n": total_n,
        "rate": total_k / total_n,
        "n_answerable": sum(1 for entry in asked if entry["k"] > 0),
    }


# D-11.2's transcript half. PersonaChat-style small talk that touches NONE of the locked or soft
# slots — no name, pet, sibling, town, street, birth year, house number, color, or food. A PPL
# number alone cannot show a reader that the adapter still holds an ordinary conversation, which
# is FEATURES §4's actual claim; these are what make "not a single-topic persona parrot" visible
# rather than asserted. `run_collapse_control` `_prove`s that none of them names a locked value,
# so this tuple cannot silently drift into a scored slot.
UNRELATED_QUESTIONS: tuple[str, ...] = (
    "what do you do for a living?",
    "do you have any hobbies?",
    "what kind of music do you like?",
    "how was your day?",
    "do you like to read books?",
    "what sports do you play?",
)


def run_collapse_control(model, tok, device, forbid, values):
    """D-11.2 — did teaching the persona COLLAPSE the conversational base into a parrot?

    The ambiguity this closes: whether the 331,776 adapter parameters bought recall by turning
    the model into a single-topic persona reciter that can no longer hold an ordinary dialogue.

    Measurement half — ``masked_perplexity`` on the held-out dialogue-val bin with the adapter
    ON, then again inside ``adapter_disabled``. That function is THE frozen dialogue-val gate
    metric (Phase 12 TUNE-01): a deterministic full-corpus sweep over assistant-token targets
    with a hand-counted, auditable denominator. The training loop's 20-random-batch mean loss
    estimator is DISALLOWED for gates (Phase 12 12-02) — its eval sampling noise would pollute
    exactly the margin being measured — and a bespoke "dialogue quality score" invented for this
    control would be a second, unvalidated metric answering what the frozen one already answers.

    Transcript half — the ``UNRELATED_QUESTIONS`` run greedy through both arms, side by side.

    The trigger is ``teach_persona.COLLAPSE_PPL_TRIGGER``, applied through
    ``teach_persona.replay_required`` — the SAME function, with the same ``RATIO_DECIMALS``
    rounding, that D-15's replay verdict was derived from during calibration. Applying the
    identical rule keeps the calibration measurement and this control on one DECISION RULE. The
    boolean is DESCRIPTIVE and has no gate attached: calibration already measured the replay arm
    at +29.39% — still past the 0.10 trigger — so a trip here is a pre-recorded expectation, not
    a surprise, and "replay required" was never "replay solves it".

    **WR-01 — the rule was shared; the INSTRUMENT was not, until it was fixed.** This control has
    always passed ``forbid_ids``; ``teach_persona.train_arm`` did not when the calibration
    numbers were taken, so the +29.39% above and the delta this control reports came off
    instruments that differ by ~0.008% on the base. Both call sites now pass the mask, but the
    recorded calibration figures are still the unmasked ones and the report says so where it
    prints them.

    **The ``teach_persona`` import is LAZY, inside this function, never at module level**
    (``14-05-PLAN.md`` ``<import_topology>`` rule 5). Two load-bearing reasons: ``teach_persona``
    imports ``phase14_recall`` in the other direction, so a module-level edge here is an
    ``ImportError``; and ``teach_persona`` imports ``phase14_factset`` at module level, so
    hoisting this edge would drag ``LOCKED_VALUES`` into ``personalize_demo``'s address space
    through ``phase14_recall`` and break D-19, threat T-14-17, and 14-08's must-have. Copying
    ``COLLAPSE_PPL_TRIGGER`` here as a literal would also break the cycle — and would silently
    turn the calibration verdict and this control into two independently editable numbers, which
    is the "same scale" claim above, gone.
    """
    import teach_persona as tp  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    for question in UNRELATED_QUESTIONS:
        for value in values:
            _prove(
                not contains_value(question, value),
                f"unrelated question {question!r} names the locked value {value!r} — the "
                "collateral-collapse control must touch NO taught slot, or it measures recall "
                "rather than whether ordinary conversation survived",
            )

    ppl_on, n_targets = masked_perplexity(
        model, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK, tp.BLOCK_SIZE, device, forbid_ids=forbid
    )
    with adapter_disabled(model):
        ppl_off, n_targets_off = masked_perplexity(
            model, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK, tp.BLOCK_SIZE, device, forbid_ids=forbid
        )
    _prove(
        n_targets == n_targets_off,
        f"the two arms scored different denominators ({n_targets} vs {n_targets_off}) — the "
        "PPL pair is not comparable, so the delta would measure the corpus, not the adapter",
    )
    delta = (ppl_on - ppl_off) / ppl_off

    transcripts = []
    for question in UNRELATED_QUESTIONS:
        prompt_ids = build_recall_prompt(tok, question)
        on_ids, on_stopped = _complete(model, prompt_ids, device, forbid, greedy=True)
        with adapter_disabled(model):
            off_ids, off_stopped = _complete(model, prompt_ids, device, forbid, greedy=True)
        transcripts.append(
            {
                "question": question,
                "adapter_on": tok.decode(on_ids),
                "adapter_off": tok.decode(off_ids),
                "stopped": (on_stopped, off_stopped),
            }
        )
        print(f"[phase14_recall] unrelated {question!r} on/off recorded")

    print(
        f"[phase14_recall] collapse control: masked dialogue-val PPL adapter OFF {ppl_off:.4f} "
        f"-> ON {ppl_on:.4f} ({delta:+.2%}) over {n_targets:,} scored targets"
    )
    return {
        "ppl_adapter_on": ppl_on,
        "ppl_adapter_off": ppl_off,
        "delta": delta,
        "scored_targets": n_targets,
        "trigger": tp.COLLAPSE_PPL_TRIGGER,
        "trips_trigger": tp.replay_required(ppl_off, ppl_on),
        "transcripts": tuple(transcripts),
    }


def run_bit_identity_control(tok, questions):
    """D-11.3 — adapter-off logits are BIT-IDENTICAL to the un-adapted base, on REAL weights.

    The ambiguity this closes: whether "memory OFF" in the demo is really the un-adapted base,
    or a model that still carries some of the adapter. With the adapter disabled the wrapper's
    forward is literally ``self.base(x)``, so bit-identity is STRUCTURAL — but Phase 9 pins that
    on fixtures. This control turns "inherited from a fixture unit test" into "measured on the
    real 13.9M convbase and the real persona adapter," which is what makes the demo's central
    toggle claim a measurement rather than an inheritance.

    Builds its OWN CPU-pinned pair rather than reusing the caller's device-resident model:
    14-RESEARCH Pitfall 11 is the reason — Phase 13 measured eval PPL differing by ~3.6e-8
    across processes on MPS, so a bit-identity claim proven there would carry the single doubt
    this control exists to remove. ``RuntimeConfig(device="cpu")`` is the ``demo_app.py:81``
    explicit-pin idiom, never a bare string.

    Model A is the un-adapted base (no injection at all); model B is the same slim checkpoint
    with the adapter injected, loaded, and then gated off. Full logits tensors are compared with
    ``torch.equal`` and the max absolute difference is recorded alongside the boolean, so the
    report can state a measured NUMBER (0.0) rather than only "the assertion held".
    """
    device = RuntimeConfig(device="cpu").device
    ckpt = load_slim(CONVBASE_SLIM)  # weights_only=True — restricted unpickler (T-14-22).
    model_cfg = ModelConfig(**ckpt["model_config"])

    # Model A — the un-adapted conversational base. No `inject_lora`, no adapter, nothing.
    base = GPT(model_cfg)
    base.load_state_dict(ckpt["model"])
    base.to(device).eval()

    # Model B — the same weights, adapter injected and loaded, then gated OFF.
    # LOAD BEFORE INJECT (ARCHITECTURE Anti-pattern 1): injection rewrites every wrapped
    # projection's state-dict keys with a `.base.` infix.
    gated = GPT(model_cfg)
    gated.load_state_dict(ckpt["model"])
    # W1: the artifact's OWN rank/alpha, never LoRAConfig() defaults — see load_adapted_model.
    # Bit identity holds under any scale (the disabled branch never executes), but injecting a
    # config that is not the artifact's own would make this control prove it for the wrong model.
    art = load_adapter(ADAPTER_PATH)
    inject_lora(gated, LoRAConfig(**art["lora_config"]))
    load_adapter_weights(gated, art)
    set_adapter_enabled(gated, False)
    gated.to(device).eval()

    max_abs_diff = 0.0
    with torch.no_grad():
        for question in questions:
            ids = build_recall_prompt(tok, question)
            idx = torch.tensor([ids], dtype=torch.long, device=device)
            logits_base, _ = base(idx)
            logits_gated, _ = gated(idx)
            diff = (logits_base - logits_gated).abs().max().item()
            max_abs_diff = max(max_abs_diff, diff)
            _prove(
                torch.equal(logits_base, logits_gated),
                f"adapter-off logits differ from the un-adapted base on prompt {question!r} "
                f"(max |diff| = {diff:.3e}, {len(ids)} prompt ids) — the demo's 'memory off' "
                "would not be the base, which is the entire claim the toggle makes",
            )
            print(f"[phase14_recall] bit identity {question!r}: max |diff| {diff:.3e}")

    return {
        "device": device,
        "n_prompts": len(questions),
        "prompts": tuple(questions),
        "max_abs_diff": max_abs_diff,
        "bit_identical": True,  # `_prove` above exits non-zero before this can be reached False
        "vocab_size": model_cfg.vocab_size,
    }


# =====================================================================================
# ===== THE REPORT — every section's FRAMING committed BEFORE the run that fills it =====
# =====================================================================================
#
# D-20's pre-registration in its literal form. Every string below is committed in plan 14-10; the
# run that produces the numbers they frame happens in plan 14-11. `git log -S "<any constant's
# text>" -- scripts/phase14_recall.py` therefore shows the framing predating the result, which is
# the only thing that makes "we always meant to say this" checkable rather than asserted.
#
# They are MODULE-LEVEL constants rather than f-strings buried in the writer for exactly that
# reason: a reviewer can diff the framing independently of the numbers, and a later edit to the
# framing shows up as a commit dated after the run.

REPORT_OPENER = """> **What these numbers are:** fresh-process, empty-prompt recall. Every question
> is an independent `build_recall_prompt` id sequence carrying a bare `<|system|>` span — no
> persona text, no prior turn, no retrieval — so an answer's only source is the 331,776 LoRA
> parameters in `checkpoints/persona_adapter.pt`. Scoring is D-10's mechanical
> case-insensitive substring gate over one greedy plus N seeded draws per question, judged
> against thresholds pre-registered from a DISJOINT calibration fact set before this run existed.
>
> **What they are not:** not a chat-quality measure; not comparable to any other model or to any
> published recall figure (different corpus, different register, a 13.9M-parameter base); and not
> a claim that this model is good. The only claim on offer is about WHERE the memory lives."""

FAIRNESS_OPENER = """**The ambiguity this control closes.** When a closed-book answer fails, that
failure has two readings: *"the model has no memory of this fact"* or *"the question is
unanswerable as asked."* Only the first supports the phase's claim. This control separates them by
putting the fact's own first-person statement into the `<|system|>` persona span and asking the
same question of the base with the adapter off — if the base answers when it can SEE the fact, the
question is answerable and a closed-book failure is about memory.

**This is a question-VALIDITY check, explicitly NOT a mechanism comparison, and NOT DEMO-F2.**
DEMO-F2 (deferred) is a comparative baseline that measures prompt-versus-weight recall *parity*.
This is one-directional and validates the question set only. Reading it as a mechanism comparison
would be reading DEMO-F2 into a phase that deliberately deferred it."""

# --- D-20's three-part reconciliation. Committed BEFORE the run. ---

# REDACTION IS STRUCTURAL HERE, not editorial. This module is imported by
# `scripts/personalize_demo.py` for its budget INTEGER, so every string literal below lives in the
# demo's address space for the life of the session. Plans 14-05 and 14-08 both promise no locked
# fact value reaches that process by ANY path — and the pet-name slot's taught value was written
# out verbatim three times in this constant, quietly falsifying both. The probe quotes therefore
# name their SLOT rather than its value: `<taught pet name>` carries the whole point of the
# measurement (the base copies the frame and substitutes the wrong value) while the answer itself
# stays where it belongs, in `phase14_factset` behind the lazy import.
# `tests/test_phase14_scoring.py::test_no_fact_strings_at_import` scans every string this module
# holds for embedded values, so the redaction is enforced rather than remembered.
RECONCILIATION_A = """### (a) What this control can no longer prove

First-party measurement (14-RESEARCH §F4, 6 greedy probes against `convbase_slim.pt`) recorded
this base failing to copy a fact out of its own context. The taught values are written as their
SLOT names below — this module is imported by the demo, which must not hold the answers:

- persona span `i have a dog named <taught pet name>.`, asked `what is your dog's name?`
  -> `i am a cop, i am a cop. i am a cop.`
- persona span `i live in oberlin.`, asked `where do you live?`
  -> `i live in the country i live in the country.`
- persona span plus one warm turn, asked `what is your dog's name?`
  -> `i have a dog named my name is cuddling.`

The third probe is the diagnostic one: the base copied the **syntactic frame** out of the persona
span and substituted a wrong value. The same slot's measured closed-book prior is `rose`
(D-01) — so `i have a dog named <taught pet name>.` in context yields `i have a dog named <some
other name>`, frame copied, value substituted. D-20's one-line summary of these two measurements
compresses them into a single probe; the list above is the unrounded record.

**Stated plainly, without softening: the inference this control was built to license is
weakened.** A closed-book failure can no longer be read as unambiguous evidence of absent memory,
because this base demonstrably fails to surface a fact it can see. Whatever this control returns
below, that limitation stands."""

RECONCILIATION_B = """### (b) Why the phase's central comparison survives anyway

The core claim rests on **adapter-on versus adapter-off, both closed-book** — and in NEITHER arm
is the fact in context. Both arms run in the same process, on the same weights, from the same
prompt ids, with the same per-question seeds; the only difference between them is the 331,776
adapter parameters. The base's in-context extraction weakness is therefore irrelevant to that
specific comparison: it is a property both arms share equally, and it cancels.

(a) constrains what a closed-book failure means **in isolation**. It does not touch the
**differential**, and the differential is the claim."""

RECONCILIATION_C = """### (c) What the adapter's success is actually demonstrating

The base's inability to extract raises an open question this report names rather than skirts.
When the adapter succeeds, is that:

- **(i)** knowledge encoded in the weights, then extracted by ordinary reasoning; or
- **(ii)** stimulus-response pattern completion learned directly from the training paraphrases?

These are meaningfully different claims, and a success on a TAUGHT phrasing alone cannot separate
them — a taught phrasing is exactly the stimulus (ii) predicts a response to.

**D-13's held-out template families generalizing is the evidence that distinguishes (i) from
(ii).** Held-out means entirely held-out template FAMILIES, not fresh instances of taught frames,
so a held-out success is a response to a stimulus the adapter never saw. The number that decides
this is the held-out rate in `## Recall Results — Core Tier` above; read that section, not this
one, for which of (i) and (ii) this run supports."""

FAILURE_BRANCH = """## Pre-Registered Failure Branch (D-20)

Committed in plan 14-10, before the held-out number existed. If the held-out families ALSO fail:

1. **The phase cannot distinguish (i) from (ii)**, and the demo's claim NARROWS to *"taught
   phrasings are recalled from weights."* That narrowing is stated in the headline, not buried.
2. **A taught-only success is still a real weights-memory result**, because it beats the
   adapter-off control on identical prompts in the same process — while this report **explicitly
   DECLINES** the stronger generalization claim rather than implying it.
3. **The narrower claim cites the SAME comparison structure already locked for the core claim** —
   the adapter-on / adapter-off closed-book comparison from D-11's controls — and introduces **no
   new metric invented for this branch.** A fallback metric chosen because it happens to look
   favorable in the failure scenario is not evidence; the point of pre-registering this branch is
   that the narrowed claim is traceable to evidence this phase was going to produce either way."""

COLLAPSE_OPENER = """**The ambiguity this control closes.** Recall could have been bought by
wrecking the model: 331,776 parameters trained hard on one persona could turn a conversational
base into a single-topic parrot that recites facts and can no longer hold an ordinary dialogue.
A high recall rate on a broken model is not the result this phase claims. FEATURES §4's claim is
that the persona MOVES from the prompt into the weights — not that everything else is displaced.

Measured on the frozen dialogue-val gate metric (`masked_perplexity` over
`data/dialog_val.bin` + `data/dialog_val_mask.bin`, block 256, dead ids forbidden — the same
deterministic full-corpus sweep every Phase-12 arm was judged by), adapter ON versus the same
weights inside `adapter_disabled`. The paired transcripts follow, because a PPL number alone does
not let a reader SEE that the model still converses."""

BIT_IDENTITY_OPENER = """**The ambiguity this control closes.** The demo's central affordance is a
"memory OFF" toggle. If OFF were not exactly the un-adapted base — if any part of the adapter
still leaked through — then every side-by-side the demo shows would be comparing two adapted
models, and the toggle would be theatre. Phase 9 pins the round-trip on fixtures; this runs it on
the real 13.9M convbase and the real persona adapter, which is what makes the toggle claim
MEASURED rather than inherited from a unit test.

Run on **CPU**, deliberately, not on the preflight device (14-RESEARCH Pitfall 11): Phase 13
measured eval PPL differing by ~3.6e-8 across processes on MPS, so a bit-identity claim proven
there would carry the one doubt this control exists to remove."""

SOFT_TIER_SECTION = """**What the soft tier is FOR.** Narrative texture and breadth of
personalization. It shows the demo teaching a *preference*, not only proper nouns, so a
transcript reads like a person rather than a form. It is taught in the same run, with the same
grammar, and every completion it produced is in the transcripts.

**What it explicitly does NOT do.** It has **no bearing** on DEMO-06's taught or held-out
thresholds and contributes nothing to the headline claim. Neither its rate nor its questions
enter any gate computation in this report.

**Why it is excluded, precisely.** Low-cardinality preference slots could not reliably survive
the D-03 close-call filter: for "favorite color" the base carries real prior mass on *some*
color — its measured closed-book answer is `red` (D-01) — so a base completion naming a
different color against a taught value is textbook same-category / right-slot proximity, and
dies to the close-call rule. Proper-noun slots have no such prior to trip over. Both soft-tier
survivors carry a recorded close call of their own and are retained under the D-05 exclusion —
explicitly NOT because they are clean.

This is a named section because D-05 requires one. A footnote would let a reader take the soft
tier for gated evidence, which it is not."""

THREATS_TO_VALIDITY = """Every item below names the scope it narrows, explicitly.

### 1. The held-out set is deliberately scoped (D-22)

Reversed-direction phrasings (`who is <value>?`) are **TAUGHT, not held out** — by decision, not
by accident. They hit the documented **reversal curse** (`arxiv.org/abs/2309.12288`: fine-tuning
on "A is B" does not yield "B is A", and the effect persists across fine-tuning methods). Held
out, they would fail for a *literature* reason rather than for any property of this model,
dragging down the pre-registered held-out number and poisoning exactly the evidence part (c) of
the D-20 reconciliation depends on.

**Consequence for what a clean held-out result may claim:** it demonstrates generalization
**within that scope** — across held-out template families in the taught direction — and **not**
immunity to every documented fine-tuning limitation. This report makes no claim about reversed
recall, because this phase did not measure it as a held-out property.

### 2. The soft tier is excluded from the gate (D-05)

See `## Soft Tier — Excluded From The Gate (D-05)`. Two of the taught facts contribute nothing to
either threshold, so the headline number describes the proper-noun core only — a narrower set
than "everything the adapter was taught."

### 3. The question-fairness control's limitation (D-20 (a))

See `## Control 1 — Question Fairness (D-11.1)`, part (a). In-context answerability could not be
established at this scale, so a closed-book failure **in isolation** is not unambiguous evidence
of absent memory. The adapter-on / adapter-off differential is unaffected (part (b)), but any
reading of a single failed question as "the model does not know this" is out of scope."""

SHIP_DECISION_HEADER = """<!-- D-12, verbatim: a missed threshold is recorded UNAMENDED in
`## Verdict` above. Any subsequent decision about whether or how the adapter still ships — retry
with a different recipe, ship as-is with the miss documented, or not ship — is logged HERE:
separate from the gate verdict, dated AFTER it, and explicit that it
does not reopen or amend the pre-registered threshold.
Same register as Phase 12's "Production Config Decision — post-verdict, discretionary". Empty
until such a decision is made; an empty section is the correct state when the gate is cleared. -->

_No post-verdict decision recorded._"""


# The verdict SECTION, anchored — never the last occurrence of a substring that also appears in
# prose. `teach_persona._require_go_verdict:163` already reads its gate this way; CR-02 is what
# happens when a guard does not. See `assert_report_not_clobbered` for the failure it caused.
_VERDICT_SECTION = re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)


def _recorded_verdict(text):
    """The body of the FIRST ``## Verdict`` section — ``None`` when the file has no such section.

    ``None`` and an empty body are deliberately different: a file with no verdict section is not
    a report this writer produced, and the caller refuses it rather than overwriting it blind.
    """
    section = _VERDICT_SECTION.search(text)
    return section.group(1) if section else None


def assert_report_not_clobbered():
    """The ``measure_inflation.py:66-75`` guard: a RECORDED verdict is committed evidence.

    A rerun would reset ``## Verdict`` to ``PENDING`` and silently drop every hand-added section
    (the D-12 ship decision, any checkpoint annotation), which is the exact material that cannot
    be regenerated. ``--force`` is the deliberate override.

    Called at the TOP of ``main()`` as well as from the writer: a multi-hour run that refuses to
    write its report at the end has already wasted the run.

    **CR-02 — why this reads a SECTION and not ``split("## Verdict")[-1]``.** It used to take the
    tail after the LAST occurrence of that literal. ``SHIP_DECISION_HEADER`` quotes the heading
    inside its own comment (``` `## Verdict` above ```), so every report this writer produces
    contains the string TWICE and the tail landed in the ship-decision comment — which never
    contains ``PENDING``. The guard therefore fired on every legitimate re-drive of an
    interrupted run, and the only escape was ``--force``, which skips the check entirely. An
    operator who learns that ``--force`` is always needed passes it after a human records the
    verdict, and the guard destroys precisely the hand-written material it exists to protect.
    Anchoring on the first ``## Verdict`` SECTION cannot be fooled by a prose mention.
    """
    if RECALL_REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
        recorded = _recorded_verdict(RECALL_REPORT_PATH.read_text(encoding="utf-8"))
        if recorded is None or "PENDING" not in recorded:
            raise SystemExit(
                f"[phase14_recall] {RECALL_REPORT_PATH} already carries a recorded verdict — "
                "it is committed evidence (D-12). Pass --force to overwrite and re-measure."
            )


def _tier(records, label):
    """The one record whose ``tier`` is ``label`` — a missing tier is a wiring bug, not a blank."""
    for record in records:
        if record["tier"] == label:
            return record
    raise SystemExit(f"[phase14_recall] no scored record for tier {label!r}")


def _question_rows(record):
    """Per-question ``k/N`` rows — every scored question, in the order it was asked."""
    rows = [
        "| question | fact | split | reserved | k/N |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in record["questions"]:
        flag = "yes" if entry["reserved"] else "—"
        rows.append(
            f"| {entry['question']} | `{entry['fact_id']}` | {entry['split']} | {flag} | "
            f"{entry['k']}/{entry['n']} |"
        )
    return rows


def _contradiction_blocks(records):
    """Every contradiction event traced to the exact completion text (D-03/D-10 discipline)."""
    blocks = []
    for record in records:
        for entry in record["questions"]:
            for draw, competing in enumerate(entry["contradictions"]):
                if not competing:
                    continue
                label = "greedy" if draw == 0 else f"seeded #{draw}"
                blocks += [
                    f"- **{record['tier']}** · `{entry['fact_id']}` · {entry['question']} · "
                    f"{label} — value present alongside: {', '.join(competing)}",
                    "",
                    _quote(entry["completions"][draw]),
                    "",
                ]
    return blocks or ["_No contradiction events detected._", ""]


def write_recall_report(records, controls, provenance_lines):
    """Write ``results/phase14_recall_report.md`` — the verdict-bearing committed evidence.

    ``results/phase14_transcripts.md`` owns the raw completions; THIS file owns the
    aggregation, the gate verdicts, and the pre-registered framing. Section order is fixed and
    every framing string is a module-level constant committed before the run (D-20).
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.

    assert_report_not_clobbered()

    taught = _tier(records, CORE_TAUGHT_TIER)
    heldout = _tier(records, CORE_HELDOUT_TIER)
    closed = _tier(records, CLOSED_BOOK_TIER)
    soft = _tier(records, SOFT_TIER)
    fairness, collapse, identity = (
        controls["fairness"],
        controls["collapse"],
        controls["bit_identity"],
    )
    taught_pass = taught_gate(taught["rate"])
    heldout_pass = heldout_gate(heldout["rate"])
    closed_k, closed_n = closed["k"], closed["n"]

    budget_row = (
        f"| `RECALL_MAX_NEW_TOKENS` | {RECALL_MAX_NEW_TOKENS} | "
        f"max census value ({max(VALUE_TOKEN_COUNTS)}) + `PREAMBLE_HEADROOM` "
        f"({PREAMBLE_HEADROOM}) + `TAIL_HEADROOM` ({TAIL_HEADROOM}), rounded up to a multiple of "
        f"`BUDGET_STEP` ({BUDGET_STEP}) — `derive_recall_budget`, D-19 |"
    )
    seed_row = (
        f"| `SEED` | {SEED} | the project's established seed. Question `i` draws sample `s` from "
        f"`torch.Generator().manual_seed({SEED} + i + s)`, so every draw in this run is "
        f"re-derivable from this integer alone |"
    )
    samples_row = (
        f"| `N_SEEDED_SAMPLES` | {N_SEEDED_SAMPLES} | D-10 requires a success RATE, never one "
        f"transcript: 1 greedy + {N_SEEDED_SAMPLES} seeded draws per question at "
        f"temperature={SAMPLE_TEMPERATURE}, top_p={SAMPLE_TOP_P} (the Phase-12 warm settings, "
        f"carried over rather than re-tuned) |"
    )
    core_row = (
        f"| core taught | {taught['k']}/{taught['n']} | **{taught['rate']:.4f}** | "
        f"`{TAUGHT_THRESHOLD}` | **{'PASS' if taught_pass else 'FAIL'}** |"
    )
    heldout_row = (
        f"| core held-out | {heldout['k']}/{heldout['n']} | **{heldout['rate']:.4f}** | "
        f"`{HELDOUT_THRESHOLD:.4f}` | **{'PASS' if heldout_pass else 'FAIL'}** |"
    )
    closed_row = (
        f"| closed-book control (adapter off) | {closed_k}/{closed_n} | "
        f"**{closed['rate']:.4f}** | — | descriptive |"
    )
    collapse_row = (
        f"| masked dialogue-val PPL | {collapse['ppl_adapter_off']:.4f} (off) -> "
        f"{collapse['ppl_adapter_on']:.4f} (on) | **{collapse['delta']:+.2%}** over "
        f"{collapse['scored_targets']:,} scored targets |"
    )

    blocks = [
        "# PersonaCore — Phase 14 Teach-Then-Recall Report (DEMO-05 / DEMO-06 / DEMO-07)",
        "",
        REPORT_OPENER,
        "",
        "## Pre-Registration",
        "",
        "Every constant below was a committed literal in `scripts/phase14_recall.py` before this "
        "run produced a single number. **Git history order is the pre-registration proof** — the "
        "same register Phase 13 used (`finetune_ab.py` @ `c3d942e`, before either arm ran). The "
        "harness never parses a report for a number, and no threshold here was chosen after "
        "seeing a Phase-14 recall result.",
        "",
        "| Constant | Value | Derivation |",
        "| --- | --- | --- |",
        f"| `TAUGHT_THRESHOLD` | {TAUGHT_THRESHOLD} | "
        f"`lock_thresholds(0.4143, 0.2506)` on the `cal_first_person_replay` arm — the arm whose "
        f"configuration this run uses. Bound by the 0.60 discount |",
        f"| `HELDOUT_THRESHOLD` | {HELDOUT_THRESHOLD:.4f} | same call; bound by `THRESHOLD_FLOOR` "
        f"(0.6 × 0.2506 = 0.1504 discounts BELOW the floor, so the floor clamps) |",
        f"| `CALIBRATION_SHA` | `{CALIBRATION_SHA}` | the commit carrying the calibration report "
        f"and the measurements both thresholds were derived from; see "
        f"`results/phase14_calibration_report.md`, `## Derivation 1 — Recall Thresholds (D-09)`, "
        f"which shows the original and corrected pairs side by side |",
        f"| `FACTSET_GATE_SHA` | `{fs.FACTSET_GATE_SHA}` | the commit at which every locked fact "
        f"was measured base-failing; see `results/phase14_factset_report.md` |",
        budget_row,
        samples_row,
        seed_row,
        "",
        "## Clean-Room Evidence (SC2)",
        "",
        "Teaching ran in a **different `python` invocation** — a different pid, at an earlier "
        "wall clock, leaving the adapter file on disk in between. The clean room is therefore "
        "inherited by construction rather than argued. The pid, the timestamp, and the SHA-256 "
        "of both weight files are the three recorded facts to check that against:",
        "",
        "```",
        *provenance_lines,
        "```",
        "",
        "**Every question's exact prompt token ids are in "
        "`results/phase14_transcripts.md`**, recorded BEFORE the model was called rather "
        "than reconstructed after seeing the answer. `assert_no_value_in_prompt` checks each "
        "prompt at two levels — the normalized value absent from the decoded prompt, and the "
        "value's encoded id sequence absent as a contiguous run in the prompt ids — and raises "
        "`SystemExit` on either. **This run completing at all is the proof that no locked value "
        "reached any scored prompt.** The live demo renders the same ids from the same "
        "`build_recall_prompt` call, so the panel and this evidence cannot diverge (D-18).",
        "",
        "## Recall Results — Core Tier",
        "",
        "**Taught and never-seen are reported separately** (SC3 / DEMO-06), because they support "
        "different claims. The **taught** tier measures recall on phrasings whose template FAMILY "
        "the adapter trained on: a success there is consistent with learning and also with "
        "memorizing a surface form. The **held-out** tier measures entirely held-out template "
        "families (D-13) plus the D-08 reserved gate probes: a success there is the one that "
        "distinguishes an internalized fact from a memorized phrasing. Neither number is the "
        "other's substitute.",
        "",
        "| tier | k/N | rate | threshold | gate |",
        "| --- | --- | --- | --- | --- |",
        core_row,
        heldout_row,
        closed_row,
        "",
        f"The closed-book control ran the SAME process, the SAME weights, and the SAME "
        f"{len(closed['questions'])} prompts (core plus soft, every tier) with only the LoRA "
        f"`enabled` flags flipped off, and the SAME per-question seeds — so the arms are paired, "
        f"not merely comparable. Any difference between it and the two gated rows can only come "
        f"from the adapter.",
        "",
        "### Per-question `k/N` — core taught",
        "",
        *_question_rows(taught),
        "",
        "### Per-question `k/N` — core held-out",
        "",
        *_question_rows(heldout),
        "",
        "## Held-Out Provenance (D-08)",
        "",
        "The reserved gate probes below are **held out AND measured base-failing at gate time, "
        f"commit `{fs.FACTSET_GATE_SHA}`** — the specific base completion that proves each one is "
        "quoted verbatim in `results/phase14_factset_report.md`. That is what makes the held-out "
        "split *proven* unguessable by the base rather than merely assumed to be. The "
        "scoring-time closed-book control above re-measures on the FULL question set regardless: "
        "gate-time probes are evidence carried forward, never a substitute for re-measuring.",
        "",
    ]

    for entry in heldout["questions"]:
        if entry["reserved"]:
            blocks.append(
                f"- `{entry['fact_id']}` · {entry['question']} — held out AND measured "
                f"base-failing at gate time, commit `{fs.FACTSET_GATE_SHA}` "
                f"({entry['k']}/{entry['n']} this run)"
            )

    blocks += [
        "",
        "## Soft Tier — Excluded From The Gate (D-05)",
        "",
        SOFT_TIER_SECTION,
        "",
        f"Measured, for the record and for nothing else: **{soft['k']}/{soft['n']} = "
        f"{soft['rate']:.4f}** across {len(soft['questions'])} questions.",
        "",
        "## Contradiction Events (descriptive, no gate)",
        "",
        "**No gate is attached to this section.** It is descriptive, in the same register Phase "
        "13 used for the 79/70 role-token leakage that qualified what its retention gate could "
        "claim: a contradiction count never fails this phase, it qualifies what the recall rate "
        "is allowed to mean. Detection is MECHANICAL — a completion counts as a contradiction "
        "iff it contains the correct value AND at least one other value from the committed "
        "lexicon (`LOCKED_VALUES` plus every gate-rejected candidate), requiring zero new "
        "editorial judgment. Hedging language is a separate, weaker signal reported apart from "
        "it. Every event below is traced to the exact completion text (D-03's quoted-evidence "
        "discipline); there is no unlogged tally.",
        "",
        "| tier | contradiction events | hedging completions |",
        "| --- | --- | --- |",
    ]
    for record in records:
        blocks.append(f"| {record['tier']} | {record['contradictions']} | {record['hedging']} |")
    blocks += ["", *_contradiction_blocks(records)]

    blocks += [
        "## Control 1 — Question Fairness (D-11.1)",
        "",
        FAIRNESS_OPENER,
        "",
        f"**Measured.** With each fact's own first-person statement in the `<|system|>` persona "
        f"span, the base (adapter off) scored **{fairness['k']}/{fairness['n']} = "
        f"{fairness['rate']:.4f}** across {len(fairness['questions'])} questions; "
        f"{fairness['n_answerable']} of those questions produced at least one completion "
        f"containing the value. This is the ONLY place in the entire phase where a fact value "
        f"legitimately appears in a prompt.",
        "",
        RECONCILIATION_A,
        "",
        RECONCILIATION_B,
        "",
        RECONCILIATION_C,
        "",
        FAILURE_BRANCH,
        "",
        "## Control 2 — No Collateral Collapse (D-11.2)",
        "",
        COLLAPSE_OPENER,
        "",
        "| metric | adapter off -> on | delta |",
        "| --- | --- | --- |",
        collapse_row,
        "",
        f"`COLLAPSE_PPL_TRIGGER` = {collapse['trigger']} (imported from `teach_persona`, never "
        f"duplicated, so this control and D-15's calibration verdict share ONE definition of the "
        f"RULE). Trigger tripped: **{collapse['trips_trigger']}** — **descriptive, no gate.** "
        f"Calibration already measured the replay arm at **+29.39%**, still past the trigger, "
        f"and this run uses that arm's configuration: a trip here is a pre-recorded expectation, "
        f'not a surprise. "Replay required" was never "replay solves it".',
        "",
        "> **WR-01 — the +29.39% above and the delta in this table were measured on two slightly "
        "different instruments, and this line says so rather than presenting them as one scale.** "
        "`teach_persona.train_arm` called `masked_perplexity` WITHOUT `forbid_ids` when the "
        "calibration numbers were recorded; this control has always passed it. Re-measured from "
        "the saved calibration adapters under both settings, the replay arm reads +29.3914% "
        "unmasked and +29.3364% masked (and the no-replay arm +224.8084% / +224.5330%) — "
        "`replay_required` is True on all four, so the D-15 verdict does not move. The call site "
        "has since been aligned to the frozen policy; the recorded calibration figures remain the "
        "unmasked ones, because a report does not get to re-describe how its numbers were taken.",
        "",
        "### Paired transcripts — questions touching no taught slot",
        "",
    ]
    for record in collapse["transcripts"]:
        blocks += [
            f"**{record['question']}**",
            "",
            "- adapter ON:",
            _quote(record["adapter_on"]),
            "- adapter OFF:",
            _quote(record["adapter_off"]),
            "",
        ]

    blocks += [
        "## Control 3 — Adapter-Off Bit Identity (D-11.3)",
        "",
        BIT_IDENTITY_OPENER,
        "",
        f"**Measured.** Full logits tensors compared with `torch.equal` over "
        f"{identity['n_prompts']} prompts (several held-out questions plus the empty-question "
        f"startup scaffold), on device `{identity['device']}`, vocab {identity['vocab_size']}: "
        f"an un-injected model A loaded from `convbase_slim.pt` against a model B with the "
        f"adapter injected, loaded, and then gated off via `set_adapter_enabled(model, False)`.",
        "",
        f"- `torch.equal` on every prompt: **{identity['bit_identical']}**",
        f"- max absolute logit difference: **{identity['max_abs_diff']:.1f}** (exactly zero)",
        "",
        "With the adapter disabled the wrapper's forward is literally `self.base(x)`, so "
        "bit-identity is structural. This control is what turns that from an inherited fixture "
        "property into a measurement on the real base and the real adapter.",
        "",
        "## Threats To Validity",
        "",
        THREATS_TO_VALIDITY,
        "",
        "## Verdict",
        "",
        f"- Taught: {taught['rate']:.4f} vs `TAUGHT_THRESHOLD` {TAUGHT_THRESHOLD} (boundary "
        f"passes) — **{'PASS' if taught_pass else 'FAIL'}**",
        f"- Held-out: {heldout['rate']:.4f} vs `HELDOUT_THRESHOLD` {HELDOUT_THRESHOLD:.4f} "
        f"(boundary passes) — **{'PASS' if heldout_pass else 'FAIL'}**",
        f"- Closed-book control: {closed['rate']:.4f} — descriptive, no threshold",
        "",
        "PENDING — user decision at checkpoint.",
        "",
        "## Ship Decision — post-verdict, discretionary",
        "",
        SHIP_DECISION_HEADER,
        "",
    ]

    RECALL_REPORT_PATH.write_text("\n".join(blocks), encoding="utf-8")
    print(
        f"[phase14_recall] wrote {RECALL_REPORT_PATH}: taught {taught['rate']:.4f} "
        f"({'PASS' if taught_pass else 'FAIL'}), held-out {heldout['rate']:.4f} "
        f"({'PASS' if heldout_pass else 'FAIL'}), closed-book {closed['rate']:.4f}"
    )


if __name__ == "__main__":
    main()
