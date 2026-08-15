---
phase: 18
slug: black-box-adversarial-extraction-audit
created: 2026-08-15
---

# Phase 18: Black-Box Adversarial Extraction Audit — Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 15 (9 created, 6 modified)
**Analogs found:** 13 / 15 exact-or-role match · **2 have NO analog and are new construction (D-28)**

> Every line number below was verified by `grep -n` against the working tree at map time. Excerpts
> are copied verbatim from the analog, not paraphrased.

---

## File Classification

| New/Modified File | New/Mod | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|---|
| `scripts/phase18_extraction.py` | new | pinned driver (pre-registration + corpus builder + run modes + verdict + report) | batch / transform / request-response | `scripts/phase17_isolation.py` (+ `scripts/phase16_persistence.py`) | **exact** |
| ├─ *its statistics layer* | new (imports) | — | — | `scripts/phase16_persistence.py:843,1088,1170,1005` | **exact — import unchanged** |
| ├─ *its draw layer* | new (imports) | — | — | `scripts/phase14_recall.py:595,227` | **exact — import unchanged** |
| ├─ *its scoring layer* | new (imports) | — | — | `scripts/phase14_recall.py:300` | **exact — import unchanged** |
| ├─ *`null_result_is_admissible()`* | new | admissibility gate | transform | `scripts/erasure_gate.py:200` `erasure_succeeded` | **exact shape** |
| ├─ *teacher-forced span NLL* | new | instrument | forward-pass / transform | **NONE — see § No Analog Found #1** | structural only |
| └─ *forced-choice / exposure scorer* | new | instrument | transform | **NONE — see § No Analog Found #2** | structural only |
| `results/phase18_corpus.json` | new | data artifact (the D-07 INPUT) | file-I/O | `results/phase16_recall_sample.json` | exact |
| `results/phase18_arm_adapter-{on,off}.json` | new | per-arm run record | file-I/O | `results/phase16_arm_adapter-only.json` | exact |
| `results/phase18_preflight_report.md` | new | report artifact | file-I/O | `results/phase17_personas_report.md` | role-match |
| `results/phase18_extraction_report.md` | new | report artifact | file-I/O | `results/phase17_isolation_report.md` | exact |
| `tests/test_phase18_prereg.py` | new | test (ancestry + static scan + gate arithmetic) | batch | `tests/test_phase16_prereg.py` + `tests/test_phase17_stats.py:62` | exact |
| `tests/test_phase18_corpus.py` | new | test (artifact re-derivation) | batch | `tests/test_phase16_fixture_regen.py` | **exact** |
| `tests/test_phase18_draws.py` | new | test (draw/NLL/exposure, CPU-only) | batch | `tests/test_phase17_scoring.py` (structure) — fake model is **new** | role-match |
| `tests/test_phase18_docs.py` | new | test (docs additive + no bare 0%) | batch | `tests/test_phase15_docs.py:525` + `tests/test_phase17_stats.py:858` | exact |
| `tests/conftest.py` | **mod** | fixture module | — | itself (`simulate_pascal`, only fixture present) — **fake model is new** | partial |
| `scripts/phase14_recall.py` | **mod** | shared instrument | — | its own twin `assert_value_in_prompt:424` | **exact (widen, 0 deletions)** |
| `tests/test_phase14_scoring.py` | **mod** | allowlist | — | `PERSONA_ALLOWLIST:422` — its own two incumbents | exact |
| `tests/test_phase16_prereg.py` | **mod** | ancestry guard | — | `PHASE17_PREREG_ARTIFACT:61` + `:134` test | **exact (twin)** |
| `scripts/personalize_demo.py` | **mod** | UI label literal | — | `MEMORY_INFO:304`, `STATUS_OFF:313` | exact |
| `README.md`, `docs/REPORT.md` | **mod** | docs | — | Phase 15's dated continuation (`tests/test_phase15_docs.py:511-525`) | exact |

---

## Pattern Assignments

### `scripts/phase18_extraction.py` — the D-04 pin

**Primary analog:** `scripts/phase17_isolation.py` (2,574 lines, shipped, pinned by ancestry)
**Secondary analog:** `scripts/phase16_persistence.py` (2,865 lines, shipped, pinned by ancestry)

Both are single-file drivers holding pre-registration literals + pure scoring + run modes + report
writer, and both are already covered by the STAT-05 ancestry machinery. Copy structure from 17,
copy statistics call shapes from 16.

#### 1. Module header + `sys.path` bootstrap + LAZY-IMPORT rule (`phase17_isolation.py:1-42`)

The one module-level side effect any of these drivers is permitted, and the reason. **Phase 18
inherits the INVERTED form** (Phase 17's, not Phase 16's): the fact material must be imported
*lazily* so no value enters this module's string surface (D-03's static scan reads it).

```python
"""Phase 17 multi-persona isolation matrix — the DRIVER (ISO-02 / ISO-03 / SC3).

The PRE-REGISTRATION is ``scripts/phase17_personas.py`` and is IMPORTED here, never retyped: ...

Nothing executes at import except the ``sys.path`` bootstrap below. ``main()`` lands in plan 17-06
under a ``__main__`` guard, so an ``importlib`` load in a CPU-only test runs no guard, no model
load, no tokenizer load and no generation. ...

LAZY-IMPORT RULE — inherited from ``phase16_persistence:12-15``, and INVERTED for this phase.
``scripts/phase17_persona_facts.py`` holds the 24 minted values at module scope BY DESIGN (it IS the
committed data), so this module must import it LAZILY, inside function bodies, to keep persona value
strings out of the scored driver's own string surface. ...
"""

import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase16_persistence.py:34-38 precedent). Insert it explicitly so both
# paths reach the sibling drivers. This is the ONE module-level call this file is permitted, and
# `tests/test_phase17_scoring.py::test_nothing_executes_at_import` asserts exactly that.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import _verdict  # noqa: E402  (needs the sys.path insert above)
import phase16_persistence as persistence  # noqa: E402  (needs the sys.path insert above)
import phase17_personas as personas  # noqa: E402  (needs the sys.path insert above)
```

**Caveat for Phase 18:** Phase 18's pin holds `LOCKED_FACTS`-derived material (A2 prefixes,
exposure reference sets) — those imports must be **inside function bodies**, not at module scope,
or `embedded_fact_values` over `scripts/phase18_*.py` goes red.

#### 2. `_prove` — the loud-abort register (`phase16_persistence.py:120-128`)

Every driver defines its own, prefixed with its own name. Copy verbatim, swap the prefix.

```python
def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove`` and ``phase16_ladder._prove``,
    with this module's own prefix — an abort that names the wrong driver sends its reader to the
    wrong file.
    """
    if not condition:
        raise SystemExit(f"[phase16_persistence] PROOF FAILED: {message}")
```

This is also the exact mechanism D-19's round-trip guard uses (`SystemExit`, not `assert`), and
the mechanism the Holm-reachability import-time assert (D-31) uses.

#### 3. Pre-registration literal + its recorded rationale (`phase16_persistence.py:69-91`, `735-765`)

The house style: the constant, then a **string** constant holding the derivation — never a comment,
because a comment cannot be printed into the report nor pinned by a test.

```python
CONDITION_ORDER = ("adapter-only", "base-neither", "embedding-cosine", "prompt-stuffed")

CONDITION_ORDER_RATIONALE = (
    "Two reasons are recorded for this order, and exactly two. (1) Pre-registering the order "
    ...
)
```

and the gated-tier / family-size arithmetic recorded **as a comment block above the literal**
(`:737-744` and `:987-1003`) — this is the shape D-31's `m=4` derivation copies:

```python
# D-09 — THE FAMILY IS CLOSED AT EXACTLY THESE 6 PAIRS, C(4, 2) over CONDITION_ORDER, and the
# arithmetic behind that closure is the whole reason nothing else in Phase 16 may be gated:
#
#     alpha at Holm's first step  = 0.05 / 6 = 0.0083333
#     8/8 unanimity on the exact two-sided sign test over 2**8 = 256 partitions = 0.0078125
#     margin                      = 0.0005208, i.e. 6.7% RELATIVE to the achievable p
#     m = 7                       -> alpha = 0.0071429 < 0.0078125  -> the headline dies
#
# DERIVED from CONDITION_ORDER, never a hand-typed list of six: a retyped family is a family that
# can stop matching the arms it claims to compare.
HOLM_FAMILY_PAIRS = tuple(itertools.combinations(CONDITION_ORDER, 2))

HOLM_ALPHA = 0.05
```

> **Phase 18 divergence, called out:** D-31 fixes `m = 4` over the four *families*
> (A1-mild, A1-aggressive, A2, A3) on `core_held_out` only. Derive it the same way — from the
> family tuple, never a hand-typed `4` — and add the **import-time** reachability `_prove`
> (Ex-7 in 18-RESEARCH, Pitfall 4). `assert_family_closed` (`phase16_persistence.py:1142`) is the
> runtime half to twin.

#### 4. The statistics layer — imported UNCHANGED, zero new implementations

| What Phase 18 calls | Exact location | Signature verified |
|---|---|---|
| `wilson_upper_bound(successes, n, z=...)` | `scripts/erasure_gate.py:139` | ✅ |
| `rule_of_three(n)` | `scripts/erasure_gate.py:161` | ✅ |
| `VERDICTS` | `scripts/erasure_gate.py:136` = `("SUCCESS", "FAILURE", "INCONCLUSIVE")` | ✅ |
| `erasure_is_worth_attempting(a_s, a_q, b_s, b_q)` | `scripts/erasure_gate.py:173` — four **positional** ints, question unit | ✅ |
| `cluster_bootstrap(per_fact_questions, *, resamples, seed, alpha)` | `scripts/phase16_persistence.py:843` | ✅ |
| `sign_test_exact(signs)` | `scripts/phase16_persistence.py:1088` | ✅ |
| `holm(p_values)` | `scripts/phase16_persistence.py:1170` | ✅ |
| `HOLM_ALPHA = 0.05` / `SIGN_TEST_N = 8` | `scripts/phase16_persistence.py:1005` / `:1016` | ✅ |
| `report_proportion(successes, n_questions, n_draws)` | `scripts/phase16_persistence.py:930` | ✅ |
| `aggregate_by_fact(records, *, tier)` | `scripts/phase16_persistence.py:779` — call **twice**, one per tier | ✅ |

**The import block to copy** (`phase16_persistence.py:56-63`) — note the `noqa` comments and the
"imported, never copied" justification, which the planner should preserve:

```python
# STAT-04 — the ONLY bounds source in this milestone, IMPORTED and never copied. A third-party
# statistics package has been declined in committed code twice and is forbidden here (the D-16
# register: import the instrument, never re-implement it). `tests/test_package.py` sha256-pins
# `pyproject.toml`, so a new dependency cannot arrive quietly alongside a new statistic.
from erasure_gate import rule_of_three, wilson_upper_bound  # noqa: E402  (needs the insert above)
```

**`holm` reads its own `m` off `HOLM_FAMILY_PAIRS`** (`:1189`: `m = len(HOLM_FAMILY_PAIRS)`), so
Phase 18 **cannot** call `phase16_persistence.holm` directly for an m=4 family — it hard-`_prove`s
`len(p_values) == 6`. Plan for either (a) a Phase-18-local `holm` that reads a Phase-18 family
tuple, following `:1170-1202` line for line, or (b) widening `holm` with a `family=` keyword
defaulting to `HOLM_FAMILY_PAIRS` (the D-16 additive-widening register, same shape as the
`draw_all` widening below). **(b) is the import-never-copy-consistent choice.** Flag this to the
planner: it is a real interface collision, not a formality.

#### 5. The draw / sampling layer — `draw_all` needs exactly ONE additive keyword

`scripts/phase14_recall.py:595-637`, verified signature `(model, tok, prompt_ids, device, forbid, index)`:

```python
def draw_all(model, tok, prompt_ids, device, forbid, index):
    """All draws from ONE already-built prompt: greedy plus ``N_SEEDED_SAMPLES`` seeded samples.
    ...
    Takes prompt IDS rather than a question string so the D-11.1 fairness control — the one
    caller whose prompt carries a persona span — draws through THIS loop instead of a second
    copy of it. A duplicated draw loop is how two arms silently stop being paired.
    """
    completions = []
    stopped = []

    gen_ids, stop = _complete(model, prompt_ids, device, forbid, greedy=True)   # <- DRAW 0 IS GREEDY
    completions.append(tok.decode(gen_ids))
    stopped.append(stop)

    for s in range(N_SEEDED_SAMPLES):                       # <- the ONE constant to widen (R-04)
        generator = torch.Generator(device=device).manual_seed(question_seed(index) + s)
        gen_ids, stop = _complete(
            model, prompt_ids, device, forbid,
            temperature=SAMPLE_TEMPERATURE, top_p=SAMPLE_TOP_P, generator=generator,
        )
        completions.append(tok.decode(gen_ids))
        stopped.append(stop)

    return completions, stopped
```

Companion constants, verified: `SEED = 1337` (`:147`), `N_SEEDED_SAMPLES = 8` (`:152`),
`SAMPLE_TEMPERATURE = 0.8` (`:159`), `SAMPLE_TOP_P = 0.95` (`:160`),
`STOP_IDS = frozenset({8184, 8185})` (`:162`), and:

```python
def question_seed(index):                                   # :227
    """The per-question generator seed: ``SEED + index``."""
    return SEED + index
```

> **D-06's stride is free.** `question_seed(index*K) == SEED + index*K` — pass `src_index * K` as
> the positional `index`. **No change to `question_seed`, no new seeding helper.**
> Family zero passes `src_index` unstrided (D-01 requires the identical stream).

`forbid_ids` / `stop_ids` reach the loop through `load_adapted_model`
(`scripts/phase14_recall.py:496-574`), whose tail is the pattern to reuse for both arms:

```python
    tok = from_json(TOKENIZER_PATH)  # the FROZEN git-tracked tokenizer — never retrained.
    # .to(device): next_token masked_fills logits IN PLACE on the model device, and the sampling
    # path does not move the mask itself (CR-01 / ARCHITECTURE Anti-pattern 7).
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(device)
    return model, model_cfg, tok, forbid, artifact
```

**The adapter-off arm has a shipped precedent — do not build a second model.**
`phase17_isolation.run_one_sweep` (`:990-995`):

```python
    # The base sweep loads the SAME way the adapter sweeps do — Phase 14's persona_adapter.pt, which
    # `load_adapted_model` reads by default — and then generates inside `adapter_disabled`. Never a
    # second un-adapted model: the context manager is measured bit-identical to the un-adapted base
    # (max abs diff exactly 0.0) and a separately-built model would be a second load path free to
    # differ from the one the three adapter rows ran through.
    model, model_cfg, tok, forbid, base_artifact = recall.load_adapted_model(device)
```

> **Exception, per D-12:** the pre-flight smoke runs on the **un-adapted base** (`convbase_slim`,
> no adapter injected) — that is a *different* load than `adapter_disabled`, and D-12's
> zero-preview constraint makes it deliberately so.

#### 6. The scoring layer — `contains_value`, used UNMODIFIED (`phase14_recall.py:300-312`)

```python
def contains_value(completion, value):
    """D-10's gate: case-insensitive, whitespace-collapsed substring containment. The boundary.

    **Why substring and not id-subsequence.** BPE is context-dependent at merge boundaries, so a
    value's id sequence differs between ``...named <value>`` and ``<value>...`` ...
    Id-subsequence is at best a diagnostic; it is used that way in ``assert_no_value_in_prompt``,
    where a false positive costs nothing and a false negative would be a leak.
    """
    return normalize(value) in normalize(completion)
```

D-14 calls it as `contains_value(prefix_text + completion, value)`. **No new scoring predicate.**
`score_question(completions, value) -> (k, n)` is at `:315`.

#### 7. The clean-room guards — the twin to widen (D-03)

`assert_no_value_in_prompt` (`:398-421`) takes a **question string** and rebuilds the prompt;
`assert_value_in_prompt` (`:424`) takes **`prompt_ids`**. D-03 adds the `prompt_ids` path to the
first, making them signature-symmetric. Both, verbatim:

```python
def _is_contiguous_subsequence(haystack, needle):                       # :392
    """True iff ``needle`` appears as a CONTIGUOUS run inside ``haystack`` (both id lists)."""
    span = len(needle)
    return any(haystack[i : i + span] == needle for i in range(len(haystack) - span + 1))


def assert_no_value_in_prompt(tok, question, values):                   # :398
    """14-RESEARCH Pattern 8 clean-room proof: no fact value crossed into the model's context.

    Checked at BOTH levels for every value: the normalized string is absent from the decoded prompt,
    and the value's encoded id sequence is not a contiguous run inside the prompt ids. ...
    ``values`` is a PARAMETER, never a module-level constant ...
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
```

> **SC1's premise correction, already recorded at D-03:** this guard was **already**
> substring-aware (`normalize(value) not in decoded`). It was never the equality bug. The static
> scan (§ next) is the other, independent layer.
>
> `assert_value_in_prompt`'s docstring (`:436-453`) records why the *presence* twin ORs its two
> detectors while the *absence* twin ANDs them. The widened `assert_no_value_in_prompt` keeps AND.

#### 8. The static module scan (D-03's second layer) — `tests/test_phase14_scoring.py:302-364`

Three functions, already shared with `tests/test_phase14_demo.py`. Phase 18 **calls
`embedded_fact_values` over `scripts/phase18_*.py`** — it does not fork it.

```python
def _strings_in(obj, _depth=0):                                          # :302
    """Every ``str`` reachable inside a module attribute — not just the attribute itself."""
    if _depth > 4:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            yield from _strings_in(item, _depth + 1)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _strings_in(key, _depth + 1)
            yield from _strings_in(value, _depth + 1)


def _module_strings(module):                                             # :323
    """Every string a loaded module HOLDS — attributes, nested container strings, and docstrings.

    **Docstrings count.** A docstring body is a live ``str`` object on the function or class for
    the whole life of the process ... Docstring traversal is restricted to objects the module
    DEFINES (``__module__`` match) ...
    """
    own = getattr(module, "__name__", None)
    yield from _strings_in(getattr(module, "__doc__", None))
    for name in dir(module):
        obj = getattr(module, name, None)
        yield from _strings_in(obj)
        if getattr(obj, "__module__", None) != own:
            continue
        yield from _strings_in(getattr(obj, "__doc__", None))
        if isinstance(obj, type):  # a class: its methods carry docstrings of their own
            for member in vars(obj).values():
                yield from _strings_in(getattr(member, "__doc__", None))


def embedded_fact_values(module, forbidden):                             # :349
    """``(value, count)`` for every locked/soft value EMBEDDED in a string this module holds.

    **Containment, never equality.** The predicate here used to be
    ``getattr(driver, name) in forbidden`` — whole-string equality against the value set — which
    can only fire when a module attribute IS a fact value and nothing else. ...
    """
    hits = []
    for text in _module_strings(module):
        lowered = text.lower()
        hits += [(value, lowered.count(value)) for value in forbidden if value in lowered]
    return hits
```

#### 9. Prompt construction (D-15 extends, never bypasses)

`src/personacore/dialogue/serialize.py:92-112`:

```python
def build_recall_prompt(tok, question, persona=()):
    """The clean-room recall prompt ``<|system|>[persona] <|user|>q <|assistant|>`` — ids only.
    ...
    SINGLE source of truth for the recall prompt (D-18, Pitfall 4) ...
    """
    ids, _mask = encode_dialogue(tok, list(persona), [(question, "")])
    return ids[: ids.index(ASSISTANT_ID) + 1]
```

A2 = `build_recall_prompt(tok, question) + prefix_ids` (ids appended verbatim past `<|assistant|>`).
A3 = `build_recall_prompt(tok, question, persona=(role_instruction,))` — **value-free**, and D-08
requires a third `PERSONA_ALLOWLIST` entry **in the same commit**.

#### 10. Fact / fixture / reference-set material

| Symbol | Location | Phase 18 use |
|---|---|---|
| `Fact(id, slot, value, tier)` | `scripts/phase14_factset.py:51` | the record shape everywhere |
| `LOCKED_FACTS` (8 core) | `scripts/phase14_factset.py:390` | attack targets |
| `SOFT_TIER_FACTS` | `:410` | forbidden-value set for the static scan |
| `GATE_REJECTED_CANDIDATES` | `:429` | exposure reference pool |
| `CALIBRATION_POOL` | `:102` | exposure reference pool |
| `REGISTER_ARM_POOL` | `:117` | exposure reference pool |
| `RESERVED_HELDOUT_PROBES` | `:489` | the **32 held-out probes with NO family** (R-06 / Pitfall 5) |
| `SlotForms` / `SLOT_FORMS` | `:524` / `:543` | **`SLOT_FORMS[slot].ans1` is D-29's admissible NLL frame** |
| `FAMILY_IDS` | `:656` | `("F1"…"F8")` |
| `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` | `:816` / `:817` | D-05's free family cross-cut |
| `render_family(family_id, fact, *, second_person=False)` | `:824` | pure — re-derive `family` by string match |
| `PERSONA_FACTS` | `scripts/phase17_persona_facts.py:84` | +24 exposure references, 3 per core slot |

`SLOT_FORMS` shape, verified (`phase14_factset.py:524-553`) — `ans1` is the `{v}`-templated taught
reply frame D-29 conditions on:

```python
class SlotForms(NamedTuple):
    np1: str   # second-person noun phrase for the direct frames: "the name of your dog"
    np2: str   # a DIFFERENT noun phrase for the oblique frames: "what your dog is called"
    stem: str  # F3 statement-completion prompt: "your dog goes by the name"
    who: str   # F4 reversal question word
    kind: str  # F4 answer predicate: "{value} is my dog."
    ver_q: str # F5 verification predicate
    ans1: str  # first-person answer A, "{v}" placeholder: "my dog is named {v}."
    ans2: str  # first-person answer B (surface variation)

SLOT_FORMS: dict[str, SlotForms] = {
    "person_name": SlotForms(
        np1="the name you go by", ..., ans1="my name is {v}.", ans2="i go by {v}.",
    ),
```

`PERSONA_FACTS` shape, verified (`phase17_persona_facts.py:84-93`) — note the **module-level**
placement is deliberate there (it IS the data) and is exactly why Phase 18 must import it lazily:

```python
PERSONA_FACTS: dict[str, tuple[Fact, ...]] = {
    "persona_a": (
        Fact("p17_a_person_name", "person_name", "thessaly", "core"),
        Fact("p17_a_pet_name", "pet_name", "nyxen", "core"),
        ...
```

`phase17_persona_facts.py:37-46` is also the **lazy-import bootstrap to copy** for reading the
Phase 14 pools without a module-level fact import in the pinned driver.

#### 11. `null_result_is_admissible()` — mirror `erasure_succeeded` (`scripts/erasure_gate.py:200-255`)

**`scripts/erasure_gate.py` stays byte-untouched (D-27).** Copy the shape; do not edit the file.
Note that `zero_results_have_nll` is a **boolean parameter only** — nothing in the tree computes
an NLL (verified: § No Analog Found #1).

```python
def erasure_succeeded(
    *,
    target_successes,
    target_questions,
    target_floor,
    nontarget_deltas,
    nontarget_noise_floor,
    dialogue_ppl,
    dialogue_ppl_noise_floor,
    retention_ppl,
    zero_results_have_nll,
):
    """Evaluate (a), (b) and (c). Returns ``(verdict, reasons)`` with ``verdict`` in VERDICTS.

    Every argument is keyword-only so a later caller cannot silently transpose two counts. All
    three conditions must hold for SUCCESS; INCONCLUSIVE takes precedence over FAILURE, because
    "we could not tell" and "it did not work" are different findings and collapsing them is the
    mistake this project's honest-negatives discipline exists to prevent.
    """
    reasons = []

    if target_questions <= 0:
        return "INCONCLUSIVE", ["no target questions scored"]
    if target_successes == 0 and not zero_results_have_nll:
        return "INCONCLUSIVE", [
            "target recall is zero but no teacher-forced NLL was recorded — cannot distinguish "
            "'the fact is absent' from 'the probe was too weak', so no erasure claim is admissible"
        ]

    upper = wilson_upper_bound(target_successes, target_questions)
    a_ok = upper <= target_floor
    reasons.append(
        f"(a) target upper bound {upper:.4f} over {target_questions} questions "
        f"{'<=' if a_ok else '>'} calibrated floor {target_floor:.4f}"
    )
    ...
    if not nontarget_deltas:
        return "INCONCLUSIVE", reasons
    return ("SUCCESS" if (a_ok and b_ok and c_ok) else "FAILURE"), reasons
```

**The four properties to copy exactly:** keyword-only `*`; every INCONCLUSIVE branch returns
**before** any bound is computed; `reasons` is a list of formatted strings accumulated in order;
the final line is a single ternary over the conjunction. Also copy the **`__main__` self-check**
(`:258-291`) — it asserts both a SUCCESS case and the INCONCLUSIVE case, which is the mutation
proof D-27's four conditions each need.

#### 12. Run mode — one prompt object, two arms, one record per process

Copy the ordering contract from `phase17_isolation.run_one_sweep` (`:934-958` docstring) and the
process-split refusal from `phase16_persistence` (`:2557-2569`):

```python
_USAGE = (
    "usage: python scripts/phase16_persistence.py (--condition NAME | --report)\n"
    ...
    "There is deliberately NO mode that runs more than one condition. D-01 requires four fresh\n"
    "processes, one per arm, and the only structural way to guarantee that is to make a single\n"
    "process incapable of running two. A convenience flag would turn the process split from a\n"
    "PROPERTY of this driver into a convention an operator is trusted to follow."
)
```

`build_parser` (`phase16_persistence.py:2572-2600`) — `add_mutually_exclusive_group(required=True)`,
`choices=` constrained by the pre-registered tuple. `main(argv=None)`
(`phase17_isolation.py:2517-2570`) — exhaustive dispatch, **no default branch**, `result is None`
proved at the end:

```python
    _prove(
        result is not None,
        "the selected mode produced no result — a name in the parser's choices with no dispatch "
        "branch means the pre-registration and this dispatch have drifted apart, and the run would "
        "look like it happened while contributing nothing",
    )
    return result


if __name__ == "__main__":
    main()
```

Record-clobber refusal, called **first** (`phase17_isolation.py:975-983`):

```python
    _prove(
        not record_path.exists(),
        f"{record_path} already exists — a sweep record is RECORDED EVIDENCE, and a rerun on "
        "drifted code, a drifted adapter or a drifted fixture would silently replace the "
        "completions every cell in this row was scored from. Delete it in a reviewed commit if it "
        "genuinely must be regenerated",
    )
```

Provenance recorded per arm — `preflight_device(strict=True)`, `RuntimeConfig().device`,
`seed_everything(recall.SEED)`, `git_sha()`, `os.getpid()`, `forbid_digest(forbid)`,
`wall_clock_min` (`phase17_isolation.py:960-1008`). **Phase 18 adds the corpus `sha256` to this
block (D-07).**

#### 13. Report rendering — no fact value on the render path (D-11)

`phase17_isolation.py:1536-1548` — the cell renderer takes a **pre-computed entry dict** and never
touches the fact set:

```python
def _matrix_cell_text(entry):
    """One cell as ONE string: the STAT-02 shape, then this phase's own width, then both ends.

    Rendered through ``report_proportion``'s ``formatted`` so no cell can print a bare percentage —
    a zero rate without its denominator and its ceiling states a certainty the sample does not have.
    """
    proportion = entry["proportion"]
    return (
        f"{proportion['formatted']}; cluster bootstrap 95% "
        f"({entry['bootstrap'][0]:.6f}, {entry['bootstrap'][1]:.6f}); rule of three "
        f"3/{proportion['n_questions']} = {entry['rule_of_three_questions']:.6f} (question-level) "
        f"/ 3/{personas.SLOTS_EXPECTED} = {entry['rule_of_three_slots']:.6f} (slot-level)"
    )
```

`render_report` (`:1573-1595`) — the two properties Phase 18 must reproduce:

```python
def render_report(matrix, described, gate, sweep_records, prior_anchor, *, resamples):
    """Write ``results/phase17_isolation_report.md`` and return its text.

    The verdict is COMPUTED by importing ``gate_cleared``, never retyped as prose beside the rows —
    a hand-written headline is a headline free to disagree with the instrument that produced it.
    ...
    Two `_prove`s run over the RENDERED TEXT before it is written, because the source-level scans
    cannot see a number a format string produced: the report must carry a ``## Verdict`` section the
    clobber guard can anchor on, and it must contain no bare zero percentage anywhere (STAT-02).
    """
```

and the pre-registration paragraph citing a **resolved** commit rather than an asserted one:

```python
        f"The family, the direction of every alternative, the seeds and the gate rule were "
        f"committed in `scripts/phase17_personas.py` at `{prereg_commit()}` — before a persona "
        "value was minted ... Every constant below is IMPORTED here, never retyped.",
```

`prereg_commit()` itself (`:1857-1880`) is the helper to twin — `git log --diff-filter=A --format=%h`,
`adds[-1]` (the earliest add), `_prove`d non-empty. **This is D-24's `licensed_headline` mechanism:
prose generated from the same literals the run obeyed.**

Report clobber guard (`:1159-1181`), called **before a byte is read**:

```python
def assert_isolation_report_not_clobbered():
    """A RECORDED verdict is committed evidence. Refuse to overwrite it — FIRST, and cheapest.
    ...
    **Anchored on the SECTION via ``_verdict.recorded_verdict``, never on a split of the heading
    literal** ... There is no force flag.
    """
    if not ISOLATION_REPORT_PATH.exists():
        return
    recorded = _verdict.recorded_verdict(ISOLATION_REPORT_PATH.read_text(encoding="utf-8"))
    if recorded is None or "PENDING" not in recorded:
        raise SystemExit(
            f"[phase17_isolation] {ISOLATION_REPORT_PATH} already carries a recorded verdict — ...
            "There is no force flag: if it genuinely must be regenerated, delete it in a reviewed "
            "commit so the removal is visible in the diff."
        )
```

Append-only continuation (for D-23's README/REPORT edits and any addendum) —
`phase17_isolation.append_addendum` (`:2369-2418`): placeholder occurs **exactly once**
(`_prove(found == 1, ...)`), prefix carried through byte-identically, and the recorded verdict
proved unchanged **on the produced bytes**:

```python
    _prove(
        _verdict.recorded_verdict(updated) == _verdict.recorded_verdict(text),
        f"appending to {path} changed its recorded `## Verdict` section. ..."
    )
    _prove(
        updated.startswith(before) and addendum.rstrip("\n") in updated,
        f"the rewritten {path} does not carry its original prefix byte-identically, ..."
    )
```

---

### `results/phase18_corpus.json` (data artifact, file-I/O)

**Analog:** `results/phase16_recall_sample.json`, guarded by `tests/test_phase16_fixture_regen.py`.

Same contract: a committed JSON artifact that a committed test **re-derives from the pinned
generator** and diffs field-by-field. D-11's schema (`family`, `dose`, `fact_id`, `slot`,
`seed_index`, `prompt_ids`) is the Phase 16 fixture's schema plus three fields; the guard shape
is unchanged. See § `tests/test_phase18_corpus.py`.

---

### `tests/test_phase18_prereg.py` (test, batch)

**Analogs:** `tests/test_phase16_prereg.py` (whole file) + `tests/test_phase17_stats.py:39-138`.

**Ancestry-by-history pattern** (`test_phase16_prereg.py:134-216`) — this is the form Phase 18
twins, **not** the SHA-pinned form:

```python
PHASE17_PREREG_ARTIFACT = "scripts/phase17_personas.py"                   # :61


def test_phase17_prereg_is_frozen_before_every_phase17_result():          # :134
    """STAT-05: Phase 17's gate constants never moved after a Phase 17 number existed.

    **Derived from history, not pinned to a SHA — and that is the stronger form, not merely the
    smaller one.** ... Asking git for EVERY commit that touches the file and requiring each to be an
    ancestor of every result is self-identifying — there is no pin to get wrong — and it catches
    the post-hoc edit.
    """
    assert _git("rev-parse", "--is-shallow-repository") == "false", (...)

    prereg_commits = _git("log", "--format=%H", "--", PHASE17_PREREG_ARTIFACT).split()
    assert prereg_commits, (...)

    tracked_artifacts = _git("ls-files", "results/phase17_*").split()

    checked = 0
    for artifact in tracked_artifacts:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        first_add = adds[-1]          # newest-first, so the ADD is the last entry
        for prereg in prereg_commits:
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=_ROOT, check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked_artifacts), (...)
    assert checked, (...)   # the product is satisfied by 0 == n*0 — this is what stops that
```

**Three vacuity closures to copy verbatim:** the shallow-clone assert, the `assert checked` after
the product assert, and the `_git` helper (`:66-70`). `V3_ARTIFACT_GLOBS` at `:54` **already
includes `results/phase18_*`** — Phase 18 adds `PHASE18_PREREG_ARTIFACT` beside `:61`, it does not
widen the glob.

**`_GATE_MODULES` glob pattern** (`tests/test_phase17_stats.py:58-62`) — derived, never hand-listed:

```python
# DERIVED from a glob, never a hand-listed tuple (D-21). `scripts/phase17_persona_facts.py` (17-03),
# `scripts/phase17_isolation.py` (17-04) and `scripts/phase17_persona_gate.py` (17-05) enter every
# scan below the moment their plans create them — a hand-listed tuple would leave each new driver
# silently uncovered, which is exactly the F-08 blindness this phase had to re-establish for itself.
_GATE_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("phase17_*.py")))
```

Phase 18 twins it over `phase18_*.py`. **Also copy `_collapsed_glob_guard()`** — Phase 17 calls it
first in every glob-driven test (`test_phase17_stats.py:866`) so an empty match set is red, not green.

**Driver loading, CPU-only** (`test_phase17_stats.py:72-81`) — `importlib.util.spec_from_file_location`
+ `exec_module`, which is safe precisely because the driver is inert at import:

```python
def _load_isolation():
    """The Phase 17 driver, loaded the same way — nothing runs beyond its ``sys.path`` insert."""
    spec = importlib.util.spec_from_file_location("phase17_isolation", _ISOLATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

**AST-scan helpers** for the D-28 "instruments are inside the pin" test and the ATK-02
"one corpus, two arms" structural test: `_tree` (`:89`), `_function_def` (`:93`),
`_enclosing_functions` (`:107`), `_call_sites(path, callee)` (`:126`).

---

### `tests/test_phase18_corpus.py` (test, batch)

**Analog:** `tests/test_phase16_fixture_regen.py:52-113` — **exact match**. The D-07 byte-equality
re-derivation is this test with `phase18_extraction`'s corpus builder substituted for
`build_question_sets`:

```python
def _load(name):                                                          # :52
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pr = _load("phase14_recall")
fs = _load("phase14_factset")


def _regenerate():                                                        # :63
    """``(core_taught, core_held_out, soft)`` seed-stamped exactly as the run stamped them."""
    core_taught, core_held_out, _ = pr.build_question_sets(fs.LOCKED_FACTS)
    ...


def test_fixture_matches_the_generator():                                 # :93
    """The committed JSON is still what the committed code produces — text AND seed_index."""
    core_taught, core_held_out, soft = _regenerate()
    questions = _fixture()["questions"]
    for key, regenerated in (("core_taught", core_taught), ...):
        stored = questions[key]
        assert [e["question"] for e in stored] == [i.question for i in regenerated], (
            f"{key}: fixture question text has drifted from build_question_sets — the fixture is "
            "stale, or render_family/the family-id sets changed under it"
        )
        assert [e["seed_index"] for e in stored] == [i.seed_index for i in regenerated], (
            f"{key}: seed_index drift — the arms would no longer be paired with Phase 14"
        )
        assert [e["fact_id"] for e in stored] == [i.fact.id for i in regenerated]
        assert [e["reserved"] for e in stored] == [bool(i.reserved) for i in regenerated]
```

**Phase 18 delta:** the assertion is on `prompt_ids` byte-equality, and per D-07 it is a **standing
guard, NOT a precondition of dispatch** — so it lives here in the test, never in the driver's run path.

The `reserved` field is already in the fixture and is **32/104 on `core_held_out`, 0/112 on
`core_taught`** (R-06) — that is what `family == "reserved"` must agree with (Pitfall 5).

**D-19 RED proof:** `pytest.raises(SystemExit)`, not `UnicodeDecodeError`. The tokenizer
**raises** on a mid-UTF-8 split (`src/personacore/tokenizer/bpe.py:209` has no `errors=`), so the
corpus builder must wrap the decode in `try/except UnicodeDecodeError` and re-raise as the
`SystemExit` — otherwise the guard never reaches its own abort (R-09, Pitfall 2).

---

### `tests/test_phase18_draws.py` (test, batch, CPU-only)

**Structure analog:** `tests/test_phase17_scoring.py` (928 lines — pure-function scoring tests, no
GPU). **The deterministic fake model it needs has NO analog** — see § No Analog Found.

The D-09 prefix-stability test drives the **real** `draw_all` against a fake model and asserts
draws 0..8 at `n_samples=63` are byte-identical to draws 0..8 at `n_samples=8`. The seed arithmetic
(`question_seed(index) + s`, fresh `torch.Generator` per draw, `phase14_recall.py:618-624`) makes
this true by construction; the test proves it of the **code path**, which is D-09's whole point.

---

### `tests/test_phase18_docs.py` (test, batch)

**Analog A — no bare zero percent** (`tests/test_phase17_stats.py:858-876`), source scan **plus**
rendered scan:

```python
def test_no_bare_zero_percent(monkeypatch, tmp_path):
    """STAT-02 — no bare zero percentage, in any Phase 17 driver source OR in a rendered report.

    The source scan is ``tests/test_phase16_driver.py``'s regex applied to all four drivers; the
    rendered scan is the half a source scan structurally cannot do, because a format string
    produces the number the reader actually sees. A zero rate printed without its denominator and
    its ceiling states a certainty this sample does not have.
    """
    _collapsed_glob_guard()
    for module in _GATE_MODULES:
        assert re.search(r"\b0(\.0+)?%", module.read_text(encoding="utf-8")) is None, (
            f"{module.name} types a bare zero percentage"
        )

    # The all-zero off-diagonal fixture: this phase's HOPED-FOR outcome, and the one that would
    # most tempt a bare zero.
    text, matrix, _gate = _render(_clean_records(), monkeypatch, tmp_path)
    assert matrix[("persona_a", "persona_b")]["n_answerable"] == 0, "the fixture is not all-zero"
    assert re.search(r"\b0(\.0+)?%", text) is None, "the rendered report prints a bare zero"
```

> The **all-zero fixture** is the load-bearing half: it renders the outcome that would most tempt
> a bare zero. Phase 18's hoped-for outcome is exactly the same shape. Copy the fixture idea, not
> just the regex.

**Analog B — dated additive continuation** (`tests/test_phase15_docs.py:511-545`):

```python
_ADDENDUM_HEADING = "## Phase 15 Addendum"

# Every Phase 13 heading that existed before Phase 15 appended anything. An append can never have
# displaced one.
_PHASE_13_HEADINGS = (
    "## Pre-Registration", "## 2×2 Result", "## Gate Verdict",
    "## Threats to Validity", "## Figures", "## Evidence Index",
)


def test_verdict_section_is_dated_and_separated():
    """D-17: the Phase 15 addendum is dated, marked, last, and has displaced nothing.

    The section read is ANCHORED — never a ``str.split`` on the ``## Verdict`` heading literal
    taking ``[-1]`` ... That form is verbatim the CR-02 failure recorded at
    ``scripts/phase14_recall.py:1627-1635`` ...
    """
    report = _read("results/phase13_ab_report.md")
    headings = re.findall(r"^## .+$", report, re.M)
    # Meta-guard: the heading scan found something before anything is asserted about ordering.
    assert headings, "no `## ` headings found in results/phase13_ab_report.md — the scan broke"
```

`docs/REPORT.md` already carries this pattern at `:424` and `:478` (R-19), so a v3.0 continuation
needs **no new convention**. `README.md`'s v2.0 claim text is at `:86, :96, :177`.

**Analog C — the D-23 demo strings** (`scripts/personalize_demo.py`, verified):
`MEMORY_INFO` at `:304`, `RESET_LABEL` at `:309`, `STATUS_OFF` at `:313`, consumed at `:510-511`
and `:594`. Both are already availability-framed; D-23 writes the corrected sentence directly in,
with no supersession framing.

---

### `tests/conftest.py` (modified — fixture module)

Current contents in full (17 lines), the only existing fixture:

```python
"""Shared test fixtures — Pascal/P100 device simulation without a real GPU."""

import pytest


@pytest.fixture
def simulate_pascal(monkeypatch):
    """Make torch report an available CUDA device with Pascal compute capability (6, 0).

    Lets the bf16-on-Pascal guard be tested on a CPU-only box (CI, laptop).
    """
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda *a, **k: (6, 0))
    return monkeypatch
```

**The deterministic fake-model fixture is new construction.** The pattern to follow is
`simulate_pascal`'s: a `@pytest.fixture`, `import torch` **inside** the function body, and a
docstring naming the guard it exists to make testable on a CPU-only box. The contract it must
satisfy is `GPT.forward(idx, targets=None) -> (logits, loss)`
(`src/personacore/model/gpt.py:195-213`) plus whatever `personacore.generation.collect` calls —
`scripts/phase14_recall._complete` (`:577-592`) is the single call site to read for that surface.

---

## Shared Patterns

### S-1 — `_prove` / `SystemExit`, never `assert`

**Source:** `scripts/phase16_persistence.py:120-128` (and `phase14_recall.py:221-224`)
**Apply to:** every guard in `scripts/phase18_extraction.py` — D-16's tail bound, D-19's round-trip,
D-31's import-time reachability, the corpus schema check, the arm-pairing check.
Rationale is in the docstring: `assert` is `-O`-strippable, `SystemExit` is not.

### S-2 — Import the instrument, never re-implement it (STAT-04 / D-16)

**Source:** `scripts/phase16_persistence.py:56-63` (`erasure_gate` import comment)
**Apply to:** every statistic and every scoring predicate. 18-RESEARCH's *Don't Hand-Roll* table
enumerates 13 of these. The one genuine collision is `holm`'s hard-coded `m` — flagged at
§ Pattern Assignments #4.

### S-3 — Additive widening, zero deletions

**Source:** `assert_value_in_prompt` (`phase14_recall.py:424`) as the signature twin;
`draw_all` (`:595`) as the keyword-widening target.
**Apply to:** D-03 (`assert_no_value_in_prompt` gains a `prompt_ids` path), R-04 (`draw_all` gains
`n_samples=N_SEEDED_SAMPLES` with the default preserving every existing caller bit-for-bit), and
`holm` if the planner takes the `family=` route.

### S-4 — Pre-registration as module literals, verdicts by import

**Source:** `phase16_persistence.py:69-91`, `:735-765`, `:983-1035`; report side at
`phase17_isolation.py:1573-1609` and `prereg_commit()` at `:1857`.
**Apply to:** K, `⌊ids/4⌋`, the ASR ladder, `VERDICTS`, the Holm family, D-24's two threat-model
column lists, and every verdict template including INCONCLUSIVE.

### S-5 — Guards are mutation-proved

**Source:** `erasure_gate.py:258-291` (`__main__` self-check asserting both SUCCESS **and**
INCONCLUSIVE); `test_phase16_prereg.py`'s three named vacuity closures.
**Apply to:** D-09, D-12, D-19, D-31, and every `null_result_is_admissible()` condition.

### S-6 — Reports are extended, never re-rendered

**Source:** `phase17_isolation.assert_isolation_report_not_clobbered` (`:1159`) and
`append_addendum` (`:2369`).
**Apply to:** `results/phase18_extraction_report.md`, `README.md`, `docs/REPORT.md`.
Phase 15's shipped diff was 549 insertions / 0 deletions.

### S-7 — Explicit provenance fields over string parsing

**Source:** `phase16_persistence.PER_QUESTION_KEYS` (`:389`) + `assert_record_shape` (`:446`);
`phase17_isolation.SWEEP_QUESTIONS_KEY` (`:49`, with its "three files spelling one string" comment).
**Apply to:** D-11's corpus schema. Note `family` must admit `"reserved"` for the 32 probes.

### S-8 — Every proportion through `report_proportion`

**Source:** `phase16_persistence.py:930-980`. It attaches `WILSON_LABEL`, adds
`rule_of_three_upper` **only** when `successes == 0`, and its `formatted` string never renders a
bare zero percentage.
**Apply to:** every rate Phase 18 publishes, in both arms, both tiers, all four families.

---

## No Analog Found

Two components have **no existing analog anywhere in the tree**. This is D-28's scope correction —
ROADMAP claimed Phase 16 shipped both; it shipped neither. Do not let a plan say "reuse Phase 16's
scorer." Both land **inside `scripts/phase18_extraction.py`, before the D-04 pin**, and the D-12
smoke runs **after** they are in the file.

### 1. Teacher-forced value-span NLL + Carlini exposure rank

**Verified absent:** `grep -rn "nll\|NLL\|teacher_forc\|teacher-forc" scripts/*.py src/personacore/**/*.py`
returns only `scripts/erasure_gate.py:126,210,223-225` (the boolean gate **parameter**
`zero_results_have_nll`, read at `:223` and set in the self-check at `:276`/`:288`) and
`scripts/phase17_isolation.py:1501` (a forward-reference in prose). **Nothing computes the quantity.**

**Closest structural precedent — the `-100` masking idiom against `F.cross_entropy`:**
`src/personacore/evaluation/perplexity.py:121-137`. This is the exact span-masking mechanics to
copy; the function itself is not reusable (it reads a memmap, not a prompt).

```python
    for i in range(0, n - 1, block_size):
        end = min(i + block_size + 1, n)  # +1 so the shifted target fits in the slice
        chunk = torch.from_numpy(data[i:end].astype(np.int64)).to(device)
        if chunk.numel() < 2:
            continue  # a single dangling token has nothing to predict
        x = chunk[:-1].unsqueeze(0)  # (1, T)
        y = chunk[1:].unsqueeze(0)  # (1, T)
        m = torch.from_numpy(mask[i + 1 : end].astype(np.int64)).to(device).unsqueeze(0)
        y = y.masked_fill(m == 0, -100)
        logits, _ = model(x)  # ignore the mean loss; recompute a SUM below
        if forbid_ids is not None:
            logits = logits.masked_fill(forbid_ids.to(logits.device), float("-inf"))
        ce = F.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1), reduction="sum", ignore_index=-100
        )
        total_ce += ce.item()
        total_tokens += int((y != -100).sum())
```

Its docstring (`:95-99`) states the shift semantics precisely, and that sentence is worth copying:

> *"The mask memmap (`uint8`) is 1:1 aligned with the token memmap and sliced SHIFTED with the
> targets (`mask[i+1:end]`), so token j's mask governs the prediction OF token j (target-space
> semantics). `mask==0` targets become `ignore_index=-100` and contribute neither to the CE sum nor
> to the denominator."*

**The forward-pass primitive** — `src/personacore/model/gpt.py:195-213`, verified:

```python
    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.config.block_size, f"seq len {T} > block_size {self.config.block_size}"
        ...
        logits = self.lm_head(x)  # (B, T, V)
        # LOCKED bigram tail (D-05) — identical flatten to bigram.py:35-39.
        if targets is None:
            return logits, None
        B, T, V = logits.shape
        loss = F.cross_entropy(logits.view(B * T, V), targets.view(B * T))
        return logits, loss
```

Note: `forward`'s own loss is `reduction='mean'` with **no** `ignore_index` argument passed
(defaults to `-100`), and it offers no `reduction='sum'`. D-30 requires **both** reductions
published from **one** forward pass — so take the `logits` return and compute both with
`F.cross_entropy(..., reduction=..., ignore_index=-100)` yourself, exactly as
`masked_perplexity` does at `:130-135` (`logits, _ = model(x)  # ignore the mean loss`).

**Three Phase-18-specific specs with no precedent to inherit** (all pre-registered at D-29/D-30):
the reply frame is `SLOT_FORMS[slot].ans1` (`phase14_factset.py:551` etc.); the admissible
reduction is **mean**; `birth_year` and `house_number` (length spread 0) must rank identically
under both reductions, asserted, because at spread 0 mean = sum/L is a strictly monotonic transform.

**One more precedent worth citing:** `phase16_persistence.embed_sequence(model, ids, device)`
(`:592`) is the only committed function that pushes a hand-built id list through the model for a
non-generation purpose. Read it for the device/`no_grad`/shape conventions.

### 2. A forced-choice scorer

**Verified absent:** `grep -rn "forced_choice\|forced-choice\|forced choice" scripts/ src/ tests/`
→ **zero hits.** Every hit is in `.planning/research/*.md` (FEATURES.md's WVP-3 *proposal*) or
`.planning/ROADMAP.md:388`. Phase 16 shipped the capability ladder and the four-arm comparison
instead.

**Closest scoring precedent:** `phase17_isolation.score_completion(completion, slot_values)`
(`:178`) and `classify(labels, own, base_texts, completion)` (`:213`) — a **pure**, cell-blind
scoring pass over recorded completions, taking values as a **parameter** so the whole scoring core
is unit-testable on synthetic values with no GPU. That parameterization is the property to copy
(it is Phase 17's SC3 in structural form, and the same property makes the D-30 spread-0 control
testable on CPU).

Under D-14 the *ASR* scorer is `contains_value` unmodified, so what is genuinely new is only the
**exposure ranking** — a sort of same-slot candidates by NLL, `rank = 1 + index(taught_value)`,
`exposure = log2|R| − log2 rank`. That is Ex-6 in 18-RESEARCH and roughly six lines; it belongs
inside the pin (D-28), not in a helper.

---

## Anti-Patterns — do not copy these into Phase 18

Each is recorded in a committed docstring in the analogs above.

| Anti-pattern | Where it is named |
|---|---|
| A second draw loop | `phase14_recall.draw_all:604-606`; `phase16_persistence` module docstring `:17-19` |
| A new scoring predicate | `phase14_recall.contains_value:303-310` |
| Re-rendering a report | `phase17_isolation.append_addendum:2379-2383` |
| `split("## Verdict")[-1]` | `test_phase15_docs.py:527-538`; `scripts/_verdict.py` is the one shared copy |
| A hand-listed module tuple instead of a glob | `test_phase17_stats.py:58-61` |
| A pre-added `PERSONA_ALLOWLIST` entry | `test_phase14_scoring.py:418-421` — hard equality, both in one commit |
| Module-level import of the fact set in the pinned driver | `phase17_isolation.py:13-19` (the INVERTED lazy rule) |
| A `--force` flag on a clobber guard | `phase17_isolation.py:1179-1181`, `:2372-2377` |
| A convenience flag that runs two arms in one process | `phase16_persistence._USAGE:2565-2569` |

---

## Metadata

**Analog search scope:** `scripts/` (39 modules), `tests/` (76 modules),
`src/personacore/{model,dialogue,evaluation,generation,lora,tokenizer}/`
**Files read for extraction:** 16
**Verification:** every cited line number confirmed by `grep -n` at map time
**Pattern extraction date:** 2026-08-15
