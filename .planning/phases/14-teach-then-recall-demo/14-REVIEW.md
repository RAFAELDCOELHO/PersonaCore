---
phase: 14-teach-then-recall-demo
reviewed: 2026-08-02T13:49:52Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - src/personacore/dialogue/serialize.py
  - src/personacore/dialogue/__init__.py
  - src/personacore/generation/text.py
  - src/personacore/generation/__init__.py
  - scripts/phase14_factset.py
  - scripts/phase14_factset_gate.py
  - scripts/phase14_recall.py
  - scripts/teach_persona.py
  - scripts/personalize_demo.py
  - tests/test_recall_prompt.py
  - tests/test_phase14_factset.py
  - tests/test_phase14_teaching.py
  - tests/test_phase14_scoring.py
  - tests/test_phase14_demo.py
findings:
  critical: 2
  warning: 7
  info: 10
  total: 19
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-08-02T13:49:52Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

The clean-room posture itself holds up under attack. I could not find a path by which a locked
fact value reaches a scored prompt: content spans encode with `allowed_special="none"` and the
BPE id space partitions bytes 0-255 / merges 256-8183 / specials 8184-8191, so a user (or a
persona line, or a question) can never emit a control id — `build_recall_prompt`'s
`ids.index(ASSISTANT_ID)` truncation is safe *by construction*, not by convention. The
lazy-import boundary is real: `phase14_recall` holds integers only at import time, and
`personalize_demo` transitively pulls in neither the fact-set nor the teaching module. No
network dependency, no external store, no `eval`, no shell injection, no unsafe deserialization
outside the two documented trusted-checkpoint reads.

What does not hold up is the **evidence-integrity machinery around the measurements**. Two
findings are load-bearing:

1. The closed-book control's per-question seeds are **not** paired with the adapter-ON arms for
   158 of 270 questions, and `results/phase14_recall_report.md` states the opposite as fact.
2. The recall report's clobber guard misreads its own freshly-written PENDING output as a
   recorded verdict, so every legitimate re-run must pass `--force` — which then disables the
   guard against a *genuinely* recorded verdict.

Both were reproduced, not inferred. Beyond those, the phase quietly deviates from Phase 12/13's
"frozen evaluation policy" in one measured metric (WR-01), and the demo's free-text input path
diverges from the measured decode condition in a way the `DECODE_KW` fix did not cover (WR-05).

Everything listed under `<already_verified_do_not_re_report>` was excluded. Numeric magnitudes
below are measured, not estimated.

## Critical Issues

### CR-01: Closed-book control is not seed-paired with the adapter-ON arms, and the committed report says it is

**File:** `scripts/phase14_recall.py:764` (`run_scored_recall`), `scripts/phase14_recall.py:1035-1041` (`main`), `scripts/phase14_recall.py:1714-1718` (report text)

**Issue:** `run_scored_recall` derives the per-question generator seed from `enumerate(items)` —
the question's position *in the list it was handed*. The adapter-ON arms are scored on separate
lists (`core_taught`, then `core_held_out`, then `soft_taught + soft_held_out`), each restarting
at index 0. The closed-book control is scored on the **concatenation**
`core_taught + core_held_out + soft_taught + soft_held_out`, so every question after the first
112 receives a different index — and therefore a different `question_seed(index) + s` — than it
received in its adapter-ON arm.

Measured on the real question sets:

```
core_taught 112 · core_heldout 104 · soft_taught 28 · soft_heldout 26
closed-book item count 270
first core_heldout question: adapter-ON index 0 (seed 1337) · closed-book index 112 (seed 1449)
```

158 of 270 questions (58%) are unpaired. `results/phase14_recall_report.md:62` states the
opposite verbatim:

> "The closed-book control ran the SAME process, the SAME weights, and the SAME 270 prompts
> (core plus soft, every tier) with only the LoRA `enabled` flags flipped off, **and the SAME
> per-question seeds — so the arms are paired, not merely comparable.**"

`complete_question`'s docstring (`:594-596`) asserts the same invariant. This run's closed-book
result was 0/2430, so no reported number changed — but the claim in committed evidence is false
today, and the moment a closed-book arm returns a non-zero rate the differential the entire
phase rests on becomes unattributable. This is exactly the "wrong number, not a crash" failure
mode.

**Fix:** Give each question a stable seed derived from something that does not depend on which
list it happens to be in. Cheapest correct option — carry the index on the item:

```python
class RecallItem(NamedTuple):
    fact: object
    question: str
    split: str
    reserved: bool
    seed_index: int          # assigned once, in build_question_sets

# run_scored_recall
for item in items:
    drawn = complete_question(model, tok, item.question, device, forbid, index=item.seed_index)
```

Assign `seed_index` globally across `core_taught + core_held_out + soft_taught + soft_held_out`
in `main()` so every question owns one index for the whole run. Then the report's pairing
sentence becomes true. If the fix is deferred, the sentence in `REPORT_OPENER`'s neighbourhood
must be amended to say the arms are comparable but not seed-paired — an unamended false claim in
committed evidence is worse than the defect.

---

### CR-02: `assert_report_not_clobbered` treats its own PENDING output as a recorded verdict, forcing `--force` on every re-run

**File:** `scripts/phase14_recall.py:1538-1544`, with the trigger at `scripts/phase14_recall.py:1517-1525` (`SHIP_DECISION_HEADER`)

**Issue:** The guard reads

```python
recorded = RECALL_REPORT_PATH.read_text(encoding="utf-8").split("## Verdict")[-1]
if "PENDING" not in recorded:
    raise SystemExit(...)
```

`SHIP_DECISION_HEADER` contains the literal string `` `## Verdict` above. `` inside its HTML
comment, so every report the writer produces contains `## Verdict` **twice**. `[-1]` takes the
tail after the *last* occurrence — the ship-decision comment — which never contains `PENDING`.
Reproduced end to end against the real writer:

```
verdict section says PENDING: True
occurrences of '## Verdict': 2
SECOND WRITE: REFUSED -> [phase14_recall] ... already carries a recorded verdict
```

Consequences, in order of severity:

- Any legitimate re-drive of an interrupted run aborts at `main()` line 1000 and must be given
  `--force`. `--force` bypasses the guard **entirely**.
- An operator who has learned that `--force` is always required will pass it after a human
  records the ADAPT verdict, silently destroying the hand-written verdict, the D-12 ship-decision
  section, and any checkpoint annotation — precisely the material the guard exists to protect
  and the only material a re-run cannot regenerate.

`tests/test_phase14_scoring.py:522` misses this because it writes a hand-crafted two-line
fixture (`"## Verdict\n\nPENDING — ...\n"`) rather than round-tripping the writer's own output.
`phase14_factset_gate.py:119` and `teach_persona._refuse_clobber` use the same idiom but their
reports contain only one `## Verdict`, so they are correct today and fragile tomorrow.

**Fix:** Anchor on the verdict *section*, not on the last occurrence of a substring that also
appears in prose:

```python
import re

_VERDICT_SECTION = re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)

def _recorded_verdict(text):
    """The first '## Verdict' SECTION body — never a prose mention of the heading."""
    section = _VERDICT_SECTION.search(text)
    return section.group(1) if section else ""

if RECALL_REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
    if "PENDING" not in _recorded_verdict(RECALL_REPORT_PATH.read_text(encoding="utf-8")):
        raise SystemExit(...)
```

`teach_persona._require_go_verdict:163` already uses exactly this anchored-section regex — reuse
that shape in all three guards. Add a round-trip regression:
`write_recall_report(...)` twice into a tmp path must succeed the second time.

## Warnings

### WR-01: `teach_persona` measures the collapse PPL pair *without* `forbid_ids`, deviating from the frozen evaluation policy it claims to share

**File:** `scripts/teach_persona.py:648-654` vs `scripts/phase14_recall.py:1229-1235`

**Issue:** Phase 12/13's frozen evaluation policy always masks dead ids
(`finetune_dialog.py:203,214` and `finetune_ab.py:235,246` both pass `forbid_ids=forbid`), and
`phase14_recall.run_collapse_control` follows it. `teach_persona.train_arm` does not — it calls
`masked_perplexity(model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device)` with no
`forbid_ids` (the tokenizer is `del tok`'d at line 531, so no mask is even available in that
scope).

That unmasked pair is what feeds `replay_required()` → the D-15 verdict →
`REAL_RUN_REPLAY_RATIO`, and it is what
`results/phase14_calibration_report.md` prints under "masked dialogue-val PPL" while asserting
"The instrument is the D-11.2 one exactly … **It is not a proxy.**" `phase14_recall`'s
`COLLAPSE_OPENER` makes the matching claim ("dead ids forbidden — the same deterministic
full-corpus sweep every Phase-12 arm was judged by") and then prints the calibration's +29.39%
alongside its own masked delta as if on one scale.

Magnitude, measured on the un-adapted `convbase_slim.pt` over the first 64,000 tokens of
`data/dialog_val.bin` (26,796 scored targets):

```
unmasked (teach_persona policy) : 4.610607
forbid   (phase12/13/recall)    : 4.610223   ->  +0.0083%
```

So this did **not** flip the D-15 verdict (+224.81% against a 0.10 trigger). It is still a live
defect: the effect on the adapter-ON arms was never measured, the project's own
`tests/test_masked_perplexity.py:105` proves the mask is not a no-op in general, and the two
"same instrument" claims in committed evidence are literally false.

**Fix:**

```python
# train_arm — keep the tokenizer long enough to build the mask, and use the frozen policy.
tok, stats, paths = build_arm_bins(...)
forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(runtime.device)
del tok
...
ppl_on, scored_on = masked_perplexity(
    model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device, forbid_ids=forbid
)
with adapter_disabled(model):
    ppl_off, scored_off = masked_perplexity(
        model, DIALOG_VAL_BIN, DIALOG_VAL_MASK, BLOCK_SIZE, runtime.device, forbid_ids=forbid
    )
```

Note that `model_cfg` is built at line 542, before `del tok`, so the mask can be constructed
without reordering anything else. If the recorded calibration numbers are not to be re-measured,
say so explicitly in the report — "measured without the dead-id mask, a documented 0.008%
deviation from the Phase-12 policy" — rather than leaving "It is not a proxy" standing.

---

### WR-02: Per-draw seed space overlaps across adjacent questions

**File:** `scripts/phase14_recall.py:563-569`

**Issue:** Each draw gets `torch.Generator(device).manual_seed(question_seed(index) + s)` for
`s` in `0..7`, i.e. seeds `SEED+i .. SEED+i+7`. Question `i`'s draws and question `i+1`'s draws
therefore share **8 of 9** generator seeds: draw `(i, s)` and draw `(i+1, s-1)` start from the
identical RNG state. `torch.multinomial` consumes the same uniform stream in both, so adjacent
questions' sampled draws are correlated rather than independent — the aggregate is presented as
a success RATE over independent draws (`score_question`, `PITFALLS-12`).

`test_question_seed_is_distinct_and_derivable` only asserts that the *base* seeds
`question_seed(i)` are distinct; it never exercises the `+ s` offsets that are actually used.
Note the inconsistency with `phase14_factset_gate._probe:95`, which correctly reuses **one**
advancing generator for all warm draws of a probe.

**Fix:** Make the per-question seed blocks disjoint:

```python
DRAWS_PER_QUESTION = 1 + N_SEEDED_SAMPLES

def question_seed(index):
    return SEED + index * DRAWS_PER_QUESTION
```

`SEED + i` in the transcripts header and `seed_row` must be updated to match, or the "every draw
is re-derivable from `SEED` alone" claim becomes wrong in the other direction. Extend the test to
assert `len({question_seed(i) + s for i in range(16) for s in range(N_SEEDED_SAMPLES)}) == 16 * N_SEEDED_SAMPLES`.

---

### WR-03: `build_bins` writes the arm's bins to disk *before* validating them

**File:** `scripts/teach_persona.py:246-276`

**Issue:** The order is `ids_all.tofile(bin_path)` → `mask_all.tofile(mask_path)` → proof 1
(alignment) → proof 2 (corpus floor) → proof 3 (mask-fraction band). A failed proof leaves the
invalid bins on disk. `refuse_if_exists` (`:203`) then treats those files as this arm's
"RECORDED evidence" and blocks the retry until they are deleted by hand — while
`train_arm:507-510` comments that it refuses up front "before a single token is written"
precisely to avoid this class of outcome. A `mask_fraction == 0.0` bin (the PITFALLS-14 bug the
band exists to catch) is the worst case: it lands on disk under the arm's canonical name and the
operator must know to delete it rather than assume it is good.

**Fix:** Validate on the in-memory arrays, then write:

```python
    ids_all = np.concatenate(id_shards)
    mask_all = np.concatenate(mask_shards)

    # --- proofs 1-3 run on the ARRAYS, before anything reaches disk ---
    if len(ids_all) != len(mask_all): raise SystemExit(...)
    if len(ids_all) <= BLOCK_SIZE + 1: raise SystemExit(...)
    frac = float(mask_all.mean())
    if not lo <= frac <= hi: raise SystemExit(...)

    ids_all.tofile(bin_path)
    mask_all.tofile(mask_path)
```

Proofs 4-6 in `sanity_check` genuinely need the written bin and must stay where they are.

---

### WR-04: Fingerprint-mismatch detection filters on warning *category* only, so any unrelated `UserWarning` produces a false mismatch

**File:** `scripts/personalize_demo.py:441-461`, `scripts/phase14_recall.py:502-508`

**Issue:** Both sites wrap `load_adapter(...)` in `warnings.catch_warnings(record=True)` with
`simplefilter("always")` and then classify **every** captured `UserWarning` as a base/adapter
fingerprint mismatch. `catch_warnings` captures everything raised inside the block, including
warnings from `torch.load`, the unpickler, or any future torch deprecation. A single unrelated
`UserWarning` from inside `torch.load` would:

- render the demo's persistent red banner declaring *"ADAPTER / BASE MISMATCH … **Anything this
  session produces is not evidence of anything.**"* on a perfectly valid session, on camera; and
- write `fingerprint mismatch (D-02 warn-not-error): ['<unrelated torch warning>']` into
  `results/phase14_recall_report.md`'s Clean-Room Evidence block, which is committed evidence
  that the adapter was not fingerprinted against the base it was scored on.

The mismatch warning is emitted from exactly one place with a known message prefix
(`checkpoint.py:253`), so the classifier can be exact.

**Fix:**

```python
_FINGERPRINT_WARNING = "adapter base fingerprint mismatch:"

mismatched = [
    str(w.message)
    for w in caught
    if issubclass(w.category, UserWarning)
    and str(w.message).startswith(_FINGERPRINT_WARNING)
]
```

Better still, have `load_adapter` raise a dedicated `AdapterFingerprintWarning(UserWarning)`
subclass and filter on that — one definition, both consumers.

---

### WR-05: The demo feeds raw user text into `build_recall_prompt`; the measured condition is lowercase-only

**File:** `scripts/personalize_demo.py:539-563` (`on_ask`), `scripts/personalize_demo.py:536-537` (`stash`)

**Issue:** Every taught paraphrase, every scored question, and the entire PersonaChat corpus are
lowercase. `detokenize` explicitly does not truecase ("lowercase in, lowercase out"), and the
BPE encoder is case-sensitive. A reviewer typing a normally-capitalised question therefore hands
the model a prompt shape it has never seen:

```
'what is the name of your dog?' -> [8187, 8185, 119, 104, 97, ...]   # 'w' = 119
'What is the name of your dog?' -> [8187, 8185,  87, 104, 97, ...]   # 'W' =  87
identical: False
```

This is the same class of defect the `DECODE_KW` block was added to fix — "the page and the
report described two different systems" — left open on the input side. It is materially likelier
to fire than the temperature mismatch was, because free-text entry is the demo's primary
affordance and `TEXTBOX_PLACEHOLDER` invites it. Leading/trailing whitespace is likewise passed
through unstripped. An empty submission is also unguarded: clicking **Ask** with an empty box
generates a free-running persona statement against the 3-id scaffold and renders it as an answer
to an empty user bubble.

**Fix:** Normalise at the single entry point, and say so in the panel caption so the
transparency claim stays literal:

```python
def stash(question):
    return "", question.strip().lower()
```

If normalising is judged to change what the demo demonstrates, the alternative is a one-line
note under the textbox ("questions are matched lowercase — the model was taught in lowercase")
plus an explicit empty-question early return in `on_ask`. Silently accepting input the measured
condition excludes is the option that should not stand.

---

### WR-06: `EXAMPLES` duplicates the family renderers by hand and is captioned "taught phrasings" with nothing pinning it

**File:** `scripts/personalize_demo.py:367-371`, caption at `scripts/personalize_demo.py:299-302`

**Issue:** The three example questions are hand-transcribed F1/F2 renderings
(`f"what is {np1}?"`, `f"tell me {np1}."`) against `SLOT_FORMS` values the demo cannot import.
I verified all three are currently taught phrasings. Nothing keeps them that way: an edit to
`SLOT_FORMS[...].np1` — the exact thing the W-04 cross-family constraint invites — silently turns
a captioned "taught phrasing" into an unseen one, or (worse) into a held-out phrasing shown to a
reviewer as taught evidence. Every other demo/harness coupling in this phase is pinned by a test
(`test_prompt_ids_identical`, `test_forbid_ids_parity`, `test_decode_settings_match_the_scoring_harness`);
this one is not.

**Fix:** `tests/test_phase14_demo.py` already loads the fact-set module through a
non-registering `importlib` helper (`_load`, used by `test_no_fact_values_in_ui_chrome`) without
polluting `test_demo_process_is_fact_free`. Reuse it:

```python
def test_examples_are_taught_phrasings():
    fs = _load("phase14_factset", "phase14_factset.py")
    taught = {
        q
        for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS
        for fid in fs.TAUGHT_FAMILY_IDS
        for q, _a in fs.render_family(fid, fact)
    }
    assert set(pd.EXAMPLES) <= taught, set(pd.EXAMPLES) - taught
```

---

### WR-07: `StripThirdPartyAssets` rebuilds the response, dropping background tasks and collapsing repeated headers

**File:** `scripts/personalize_demo.py:232-245`

**Issue:** For `text/html` responses the middleware constructs a brand-new
`Response(...)` from `dict(response.headers)`. Two things are lost in the reconstruction:

- `response.background` is not forwarded, so any `BackgroundTask` attached to an HTML response
  is silently dropped.
- `dict(response.headers)` collapses repeated header names. `set-cookie` is the header that is
  legitimately repeated; if Gradio ever sets more than one on an HTML response (auth is the
  obvious future trigger — `launch(auth=...)`), all but the last are discarded.

I checked the SSE path specifically and found no evidence of a streaming regression — the
non-HTML early return passes the response through, and a Starlette A/B of chunk arrival times
with and without the middleware was identical. So the offline fix itself is sound; this is about
the reconstruction being lossy.

**Fix:**

```python
        return Response(
            strip_third_party_assets(body),
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )
```

and build `headers` from `response.raw_headers` (or use `MutableHeaders` on the original
response and only delete `content-length`) so repeated headers survive.

## Info

### IN-01: `by_split` is computed and returned but never consumed

**File:** `scripts/phase14_recall.py:801-814`
**Issue:** `run_scored_recall` aggregates `by_split` into the record; no report writer, control,
or test reads it (`tests/test_phase14_scoring.py:416` just supplies `{}` in the fake record).
Dead computation in the hottest reporting path.
**Fix:** Either drop it, or use it — the "Recall Results — Core Tier" table would read better
with the taught-vs-held-out split of the closed-book control shown, which is what this field
already contains.

### IN-02: `CAL_MARGIN_K` is a pre-registration table row for a constant nothing computes with

**File:** `scripts/teach_persona.py:702`, surfaced at `scripts/teach_persona.py:1227`
**Issue:** `CAL_MARGIN_K = 2` is used nowhere except its own report row and its own test
assertion. It appears in `## Pre-Registration (committed before this run)` beside constants that
genuinely drive the four derivations, which reads as though it gated something.
**Fix:** Remove it, or annotate the row as "declared for continuity with Phase 12; no Phase-14
derivation consumes it."

### IN-03: Two copies of the contiguous-subsequence helper disagree on the empty-needle case

**File:** `scripts/phase14_recall.py:390-393` vs `scripts/teach_persona.py:318-323`
**Issue:** `teach_persona._is_subsequence` guards `if n == 0 or n > len(haystack): return False`;
`phase14_recall._is_contiguous_subsequence` does not, so an empty needle returns `True` and would
abort `assert_no_value_in_prompt` with a bogus leak report. Not currently reachable (no locked
value encodes to zero ids), but these two functions are the *same* token-level clean-room proof
at two stages of the pipeline and should not differ.
**Fix:** Give `phase14_recall`'s copy the same guard, or move one implementation into
`personacore.dialogue` and have both call it.

### IN-04: `build_recall_prompt(persona=...)` bypasses the D-07 `cap_persona` cap

**File:** `src/personacore/dialogue/serialize.py:92-112`
**Issue:** `cap_persona` is documented as the SINGLE source of truth for the persona span so
"transcript prompts tokenize identically to the training bins by construction", but
`build_recall_prompt` encodes `persona` uncapped. Harmless today (the fairness control passes one
short statement), latent for any future multi-line persona.
**Fix:** `encode_dialogue(tok, cap_persona(tok, list(persona)), [(question, "")])`, or state in
the docstring that the caller owns the cap.

### IN-05: `build_question_sets` merges taught and held-out exclusions into one list

**File:** `scripts/phase14_recall.py:710-740`, consumed at `scripts/phase14_recall.py:882-897`
**Issue:** `excluded` accumulates `(family_id, fact_id, split, question)` from both splits, and
the transcripts render the whole list under "N **taught** phrasings … are excluded". Correct
today only because no held-out family self-names its value; a future allocation move would
mislabel held-out exclusions as taught.
**Fix:** Filter on `split == "taught"` when rendering, or return the two buckets separately.

### IN-06: `echo_provenance` hashes the hardcoded `ADAPTER_PATH`, not the adapter that was loaded

**File:** `scripts/phase14_recall.py:645`
**Issue:** `load_adapted_model` accepts an `adapter_path` override (used by the calibration
driver) but `echo_provenance` unconditionally hashes `ADAPTER_PATH`. Correct in `main()`, wrong
for any caller that overrides — the provenance block would fingerprint a file the run never read.
**Fix:** Thread the resolved path through the return tuple (or stash it on `artifact` alongside
`loaded_base_fingerprint`) and hash that.

### IN-07: The closed-book row inside the "Core Tier" table mixes core and soft questions

**File:** `scripts/phase14_recall.py:1638-1641`, table at `:1708-1712`
**Issue:** `core_row` and `heldout_row` are core-only; `closed_row` aggregates all 270 questions
including the soft tier that the section immediately below declares has "no bearing" on the
gate. The prose does say "(core plus soft, every tier)", but the row sits in a table headed
"Recall Results — Core Tier".
**Fix:** Report the closed-book control on the core subset in that table and the full-set number
in its own line, or move the row out of the core table.

### IN-08: `contains_value` has no word-boundary anchoring

**File:** `scripts/phase14_recall.py:300-310`
**Issue:** The D-10 gate is bare substring containment, so a completion emitting `brindlemoore`
or `zorpy` scores as a hit on `brindlemoor` / `zorp`. This is the pre-registered rule and it is
applied identically to both arms against a 0.0000 closed-book baseline, so it is not distorting
this run's conclusion — noted only because it is the one place the scoring boundary is looser
than a reader of "exact-match floor" language elsewhere in the phase would assume.
**Fix:** None required. If ever revisited, do it as a pre-registered change with the calibration
re-derived, never after seeing a rate.

### IN-09: `find_contradictions`' lexicon omits the soft-tier survivors

**File:** `scripts/phase14_recall.py:760`
**Issue:** `lexicon = set(fs.LOCKED_VALUES) | {f.value for f in fs.GATE_REJECTED_CANDIDATES}`.
`LOCKED_VALUES` covers `LOCKED_FACTS` only, so `chartreuse` and `marzipan` are never candidates
for "value present alongside". A completion naming both a locked core value and a soft survivor
is not flagged. Descriptive metric with no gate, so impact is bounded.
**Fix:** `set(fs.LOCKED_VALUES) | {f.value for f in fs.SOFT_TIER_FACTS + fs.GATE_REJECTED_CANDIDATES}`,
or state the exclusion in the report's contradiction section.

### IN-10: `STOP_IDS` retypes raw special-token integers in two new scripts

**File:** `scripts/phase14_recall.py:162`, `scripts/phase14_factset_gate.py:64`
**Issue:** `serialize.py:23-25` establishes the rule for this phase — "Resolved from the LOCKED
registry, never retyped (Don't-Hand-Roll)" — and then two Phase-14 drivers hardcode
`{8184, 8185}`. The registry is genuinely frozen so drift is near-impossible, and the pattern
matches every prior phase's scripts, which is why this is Info rather than Warning. The failure
mode if it ever did drift is a silent wrong number, not a crash: no stop id matches, every
completion runs to the 48-token cap, and the stop-id termination fraction plus the recall counts
both change.
**Fix:**
```python
from personacore.tokenizer.special import EOS_ID, SPECIAL_TOKENS
STOP_IDS = frozenset({EOS_ID, SPECIAL_TOKENS["<|user|>"]})
```

---

_Reviewed: 2026-08-02T13:49:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
