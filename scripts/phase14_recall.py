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

import os
import pathlib
import re

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE the first torch import anywhere in the process — including the one the harness half
# (plan 14-06) adds below, and including a demo that imports this module for its budget integer.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

from personacore.dialogue import build_recall_prompt, detokenize  # noqa: E402

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

STOP_IDS = frozenset({8184, 8185})  # the pinned turn-stopping idiom (eos + the next `<|user|>`)

# D-09 condition 2 — the thresholds are LOCKED BY PLAN 14-09 from the measured calibration run,
# under `teach_persona.CALIBRATION_DECISION_RULE`, which is itself committed BEFORE the calibration
# run happens. A number chosen after seeing the results is not a threshold. `None` is the honest
# pre-calibration state of this file, and git history order is what proves the ordering.
TAUGHT_THRESHOLD = None
HELDOUT_THRESHOLD = None


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
# ===== THE HARNESS — plan 14-06 lands `main()` and the scored run here =====
# =====================================================================================
#
# Deliberately empty. 14-06 adds the load -> inject_lora -> load_adapter chain, the per-question
# greedy + seeded decode loop, the committed per-question context dumps, and the report writer.
# `import phase14_factset` belongs INSIDE `main()` and nowhere else (see the LAZY-IMPORT RULE).


# =====================================================================================
# ===== THE D-11 CONTROLS — plan 14-10 lands the three controls here =====
# =====================================================================================
#
# Deliberately empty. 14-10 adds `run_fairness_control` (D-11.1 — the ONLY legitimate caller of
# `build_recall_prompt`'s `persona=` argument), `run_collapse_control` (D-11.2 — which imports
# `COLLAPSE_PPL_TRIGGER` from `teach_persona` LAZILY, inside the function), and
# `run_bit_identity_control` (D-11.3).
