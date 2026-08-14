# Phase 17: Multi-Persona Isolation Matrix - Pattern Map

**Mapped:** 2026-08-14
**Files analyzed:** 9 (6 new, 3 modified)
**Analogs found:** 9 / 9 (8 exact, 1 composite)

> This phase writes almost no genuinely new code. It **wires committed instruments together**.
> The value below is the analog map + the mechanical idioms to copy byte-for-byte, not novelty.
> Two "new" tests in `17-VALIDATION.md` turn out to be **already covered** — see
> §Already Covered before planning a task for them.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/phase17_personas.py` (new) | config/data module — committed literals, pure helpers | none (import-time constants) | `scripts/phase14_factset.py` + `phase16_persistence.py:1003-1035` | composite (both halves exact) |
| `scripts/phase17_persona_gate.py` (new) | driver (GPU pre-flight) | batch GPU probe → markdown report + blocking verdict | `scripts/phase14_factset_gate.py` | exact |
| `scripts/phase17_isolation.py` (new) | driver (two-mode: sweep / report) | generate→disk (GPU), then score→report (CPU) | `scripts/phase16_persistence.py` | exact |
| `tests/test_phase17_personas.py` (new) | test (CPU, tokenizer-only) | fixture-load + assert | `tests/test_phase14_factset.py` | exact |
| `tests/test_phase17_scoring.py` (new) | test (CPU, static AST + tiny-GPT) | AST scan + in-memory model | `tests/test_phase14_scoring.py:409-643` + `tests/test_lora_inject.py` | composite (both halves exact) |
| `tests/test_phase17_stats.py` (new) | test (CPU, static AST + pure stats) | AST scan + pure-function assert | `tests/test_phase16_stats.py` | exact |
| `scripts/teach_persona.py` (modify) | training driver | batch training | its own `probe_guessability` sibling (`phase14_factset_gate.py:111`, D-16 additive widening) | role-match |
| `scripts/phase16_persistence.py` (modify, **optional**) | statistics module | pure transform | same additive-widening precedent | role-match |
| `tests/test_lora_inject.py` (extend) | test (CPU, tiny GPT) | in-memory model | itself — `test_load_adapter_weights_refuses_wrong_alpha:198-227` | exact (self) |

---

## Already Covered — do not plan a new task for these

Two rows in `17-VALIDATION.md` name tests that **already exist and already cover Phase 17**.
Writing a Phase-17 twin would be a second copy of a rule that can drift (the D-16 register).

| Validation row | Already covered by | Evidence |
|---|---|---|
| STAT-05 `test_prereg_precedes_results` | `tests/test_phase16_prereg.py::test_prereg_commit_precedes_every_v3_results_artifact` | `V3_ARTIFACT_GLOBS = ("results/phase16_*", "results/phase17_*", "results/phase18_*")` at `:54` — Phase 17 is **already in the glob**. It also carries an `assert checked` empty-match guard at `:101`. |
| STAT-04 `test_no_new_dependencies` | `tests/test_package.py::test_pyproject_unchanged_since_v2_close` | `PYPROJECT_SHA256 = "81d07d..."` at `:11`, byte-hash compared at `:36`. A Phase-17 `pyproject.toml` diff already fails the suite. |

**What Phase 17 must still add for STAT-04:** the *stdlib + repo imports only* half — an AST scan
of the three new `scripts/phase17_*.py` for a top-level import outside the installed set. That is
genuinely new; the file-hash half is not.

---

## Pattern Assignments

### `scripts/phase17_personas.py` (config/data, committed literals)

**Analog A — the data half:** `scripts/phase14_factset.py`
**Analog B — the pre-registration half:** `scripts/phase16_persistence.py:1003-1035`

**`Fact` is IMPORTED, never redefined** (`phase14_factset.py:51-57`) — the 24 minted values are
`Fact(id, slot, value, tier)` tuples in the exact committed shape:

```python
class Fact(NamedTuple):
    """One candidate fact. ``value`` is the string the base must NOT already know."""

    id: str  # short stable string — the GATE_PROBES key and the report row label
    slot: str  # the question slot this value answers (also the SLOT_QUESTION_BANK key)
    value: str  # the invented/distinctive value, authored lowercase as it will be taught
    tier: str  # "core" (high-cardinality proper noun / identifier) or "soft" (low-cardinality)
```

**Pool-literal shape to copy** (`phase14_factset.py:71-96`, `102-124`) — one `Fact` per line,
ids prefixed by pool, a header comment stating the disjointness rule the pool enforces:

```python
CANDIDATE_POOL: tuple[Fact, ...] = (
    # --- core: 16 across 8 high-cardinality slots ---
    Fact("cand_person_quillon", "person_name", "quillon", "core"),
    Fact("cand_dog_zorp", "pet_name", "zorp", "core"),
    ...
)
```

For Phase 17 the natural key is `{persona_label: tuple[Fact, ...]}` or a flat pool with
`persona_a_person_*` ids; either way **the slot is the join key (D-02), never the id**.

**Transcribed-census pattern** (`phase14_factset.py:448-474`) — the token census is a
**committed dict transcribed from the gate report**, never recomputed at import:

```python
# Measured token counts, transcribed from the report's `## Tokenizer Census` tables. Every
# entry round-tripped exact. This dict is the SOLE input to plan 14-05's D-19 generation-budget
# derivation — the budget is derived from measured counts, never from an estimate.
VALUE_TOKEN_CENSUS: dict[str, int] = {
    "cand_person_quillon": 5,
    "cand_dog_zorp": 4,
    ...
}
```

**Resolve-by-id, never retype-the-value** (`phase14_factset.py:380-399`) — the idiom that makes a
typo raise at import instead of seating an unmeasured value:

```python
_BY_ID: dict[str, Fact] = {f.id: f for _name, pool in all_pools() for f in pool}


def _locked(*fact_ids: str) -> tuple[Fact, ...]:
    """Resolve transcribed fact ids against the committed pools; unknown id -> KeyError."""
    return tuple(_BY_ID[fact_id] for fact_id in fact_ids)


LOCKED_FACTS: tuple[Fact, ...] = _locked(
    "cand_person_quillon",
    "cand_dog_zorp",
    ...
)
```

**Pre-registration constants — DERIVED, never hand-typed** (`phase16_persistence.py:1001-1035`).
This is the exact shape `HOLM_FAMILY_CELLS` / `CELL_ALTERNATIVE` / `PERSONA_SEEDS` must take:

```python
# DERIVED from CONDITION_ORDER, never a hand-typed list of six: a retyped family is a family that
# can stop matching the arms it claims to compare.
HOLM_FAMILY_PAIRS = tuple(itertools.combinations(CONDITION_ORDER, 2))

HOLM_ALPHA = 0.05

SIGN_TEST_N = 8

# D-29 / T-16-39c — THE DECLARED DIRECTION OF THE ALTERNATIVE, PER PAIR, COMMITTED BEFORE ANY RUN.
# ... Spelled out per pair rather than generated, so a reviewer audits six committed statements;
# `assert_family_closed` proves the key set equals HOLM_FAMILY_PAIRS exactly.
SIGN_TEST_ALTERNATIVE = {
    ("adapter-only", "base-neither"): "adapter-only exceeds base-neither",
    ("adapter-only", "embedding-cosine"): "adapter-only exceeds embedding-cosine",
    ...
}
```

Note the deliberate asymmetry Phase 17 must reproduce: **the family is derived** (a
comprehension), **the direction dict is spelled out** (six literal lines, one per member), and a
runtime guard proves their key sets are equal.

**Verbatim-clause pattern for D-18's Portuguese rationale** (`phase16_persistence.py:1037-1044`):

```python
# D-07's pre-registration text, VERBATIM and not paraphrasable. Split across two source lines only
# because it exceeds the line limit; implicit concatenation reproduces it byte for byte, and
# `tests/test_phase16_stats.py` asserts it against `16-CONTEXT.md` rather than against a second
# hand-typed copy.
TAUGHT_TIER_STATUS = (
    "o resultado do tier taught nunca altera, reforça formalmente, nem substitui o veredito do "
    "tier held-out — é evidência corroborante reportada, não gate."
)
```

The matching test helper is `_context_blockquote(anchor)` (`tests/test_phase16_stats.py:101-118`),
which reads the blockquote out of `17-CONTEXT.md` so "verbatim" is never two agreeing copies.

**Module discipline (load-bearing):** no torch import at module scope, nothing executes at import.
`tests/test_phase14_factset.py:20-24` states why — the locked material must live in the committed
driver for git history to be the pre-registration proof, and an `importlib` load must run nothing.

---

### `scripts/phase17_persona_gate.py` (driver, GPU pre-flight → blocking verdict)

**Analog:** `scripts/phase14_factset_gate.py` — near line-for-line.

**Import block + MPS-fallback ordering** (`:35-60`):

```python
import os
import pathlib
import sys
import time

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import phase14_factset as fs  # noqa: E402  (sibling script; scripts/ is sys.path[0])
import torch  # noqa: E402  (must follow the MPS-fallback env set above)
from _verdict import recorded_verdict  # noqa: E402  (sibling script; scripts/ is sys.path[0])

from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted checkpoint
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
REPORT_PATH = _REPO_ROOT / "results" / "phase14_factset_report.md"  # COMMITTED evidence (D-06)
```

**The gate call itself — IMPORT, never copy** (`phase14_factset_gate.py:111`, the D-16 public entry
point widened *specifically for this phase*):

```python
def probe_guessability(model, tok, device, forbid, value, questions, *, start_index=0):
    """D-16: the PUBLIC guessability entry point — probe an ARBITRARY string, not a pool member.
    ...
    **The caller supplies ``questions``**, so this function holds no fact material of its own.
    ``start_index`` offsets that seeding so a caller running several batches gets disjoint streams.

    Returns ``{value, probes: [{question, prompt_ids, completions}], n_probes, n_completions,
    clean}`` — every completion verbatim, so the caller can quote them in its own report.
    """
```

Per RESEARCH F-07, probe with **the fixture's own questions** (`core_held_out`, regrouped by slot),
and thread `start_index=len(cache_so_far)` to keep the per-probe generator streams disjoint.

**Clobber guard — module-level, zero-arg, reads `sys.argv` at call time** (`:161-182`). Copy the
shape exactly, including *why* it is not inline in `main()`:

```python
def assert_report_not_clobbered():
    """A recorded (non-PENDING) verdict is committed evidence (D-06) — never clobber it silently.

    CR-02: reads the first ``## Verdict`` SECTION, never the tail after the last occurrence of
    the literal — a prose mention of the heading is not a recorded verdict, and a file with no
    verdict section is refused rather than overwritten blind.

    Module-level, zero-arg, reading ``REPORT_PATH`` and ``sys.argv`` at call time: that is what
    makes it monkeypatchable, and an inline block in ``main()`` was unreachable from any test
    without a 278 MB checkpoint — which is how this defect survived the first CR-02 fix.
    """
    if REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
        recorded = recorded_verdict(REPORT_PATH.read_text(encoding="utf-8"))
        if recorded is None or "PENDING" not in recorded:
            raise SystemExit(
                f"[phase14_factset_gate] {REPORT_PATH} already carries a recorded verdict — "
                "it is committed evidence (D-06). Pass --force to overwrite and re-measure."
            )
```

`recorded_verdict` is the ONE copy (`scripts/_verdict.py:24-30`) — never `split("## Verdict")[-1]`:

```python
# Anchored on the SECTION: from a ``## Verdict`` heading at line start up to the next ``## ``
# heading or end of file. A prose mention of the literal cannot be mistaken for the section.
VERDICT_SECTION = re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)
```

**Blocking GO/ADAPT enforcement** (`teach_persona.py:166-187`) — the `_require_go_verdict` twin
Phase 17 needs for `test_verdict_blocks`:

```python
def _require_go_verdict(report_path):
    """D-06 gate: hard-exit unless the report's ``## Verdict`` section reads GO or ADAPT."""
    if not report_path.exists():
        raise SystemExit(...)
    text = report_path.read_text(encoding="utf-8")
    section = re.search(r"^## Verdict\b(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if section is None:
        raise SystemExit(...)
    word = re.search(r"[A-Za-z]+", section.group(1))
    verdict = word.group(0).upper() if word else "PENDING"
    if verdict not in ("GO", "ADAPT"):
        raise SystemExit(
            f"[teach_persona] recorded verdict is {verdict!r} — teaching bins may only be built "
            "on GO/ADAPT (D-06). STOP/PENDING must be escalated, not bypassed."
        )
    return verdict
```

**Note the drift here worth closing:** `_require_go_verdict` re-implements the CR-02 regex inline
instead of importing `_verdict.VERDICT_SECTION`. Phase 17's consumer should call the existing
`teach_persona._require_go_verdict(PHASE17_REPORT)` (it takes a path — no copy needed) rather than
writing a third copy of the read.

---

### `scripts/phase17_isolation.py` (driver, two mutually exclusive modes)

**Analog:** `scripts/phase16_persistence.py` — the whole file's architecture, especially
`:2551-2865`.

**Module docstring register** (`:1-20`) — states what is pre-registered, that nothing executes at
import, and the lazy-import rule that keeps fact values out of the module's string surface:

```python
"""Four-arm weight-vs-prompt comparison driver — the PRE-REGISTRATION (PERS-02 / PERS-04).

Committed BEFORE the run it describes. The condition order, the shared arm-parity config, the
per-question record shape and arm D's chance floor are module-level literals here so git history
is the proof that none of them was chosen after seeing a number (STAT-05 ...).

Nothing executes at import. Constants and pure functions only — ``main()`` lands in plan 16-10
under a ``__main__`` guard — so an ``importlib`` load in a CPU-only test runs no guard, no model
load, no tokenizer load and no generation.

LAZY-IMPORT RULE — inherited, and load-bearing here. ``phase14_factset`` and
``phase14_factset_gate`` may be imported ONLY inside functions ...
"""
```

**`sys.path` bootstrap for sibling-script imports** (`:32-40`) — required verbatim, because an
`importlib`-loaded test harness gets no `scripts/` entry:

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase16_ladder.py:36-40 precedent). Insert it explicitly so both
# paths reach the sibling instrument.
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase14_recall as recall  # noqa: E402  (needs the sys.path insert above)
```

**The `_prove` register** (`:120-128`) — every check is a `SystemExit`, never an `-O`-strippable
`assert`, and it names its own driver:

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

**Shared-parity config as ONE object, not N agreeing literals** (`:136-177`). Phase 17's four
sweeps (a/b/c/base) need this verbatim — ISO-03 requires identical questions, seeds, `forbid_ids`
and `stop_ids` across the adapter sweeps and the base column:

```python
class ArmConfig(NamedTuple):
    """The four SCALAR generation-parity fields every arm reads, in one immutable object.

    **The claim that survives is "there is one object", not "four literals agree"** — four
    literals that agree today are four literals that can stop agreeing in one edit, and the
    disagreement is invisible in every number produced afterwards.

    **``forbid_ids`` is deliberately NOT a field here.** ... What this module records per arm is
    its sha256 CONTENT hash (``forbid_digest``), which is what makes the parity auditable from
    the committed report rather than only from the code.
    """

    max_new_tokens: int
    stop_ids: frozenset
    context_length: int
    n_draws: int


SHARED_ARM_CONFIG = ArmConfig(
    max_new_tokens=recall.RECALL_MAX_NEW_TOKENS,
    stop_ids=recall.STOP_IDS,
    context_length=ModelConfig.block_size,
    n_draws=1 + recall.N_SEEDED_SAMPLES,
)


def forbid_digest(forbid):
    """The sha256 of a ``forbid_ids`` mask's raw bytes — the arm-parity evidence for that mask."""
    return hashlib.sha256(forbid.detach().to("cpu").numpy().tobytes()).hexdigest()
```

Note `n_draws = 1 + recall.N_SEEDED_SAMPLES` — the CONTEXT "Claude's Discretion" 9-draws default is
**read from the instrument**, not retyped as `9`.

**Two-mode argument surface with no third mode** (`:2557-2600`). Copy the `_USAGE` prose too — it
is the pre-registration of the process split:

```python
_USAGE = (
    "usage: python scripts/phase16_persistence.py (--condition NAME | --report)\n"
    "\n"
    "  --condition NAME   run EXACTLY ONE arm and write results/phase16_arm_NAME.json.\n"
    "  --report           assemble results/phase16_persistence_report.md from the four arm\n"
    "                     records already on disk.\n"
    "\n"
    "There is deliberately NO mode that runs more than one condition. D-01 requires four fresh\n"
    "processes, one per arm, and the only structural way to guarantee that is to make a single\n"
    "process incapable of running two. A convenience flag would turn the process split from a\n"
    "PROPERTY of this driver into a convention an operator is trusted to follow."
)


def build_parser():
    """The argument surface, as a spec a test can read: two mutually exclusive modes, no third."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="phase16_persistence.py",
        description="Phase 16 four-arm weight-vs-prompt comparison — ONE condition per process.",
        epilog=_USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--condition", choices=CONDITION_ORDER, help="...")
    mode.add_argument("--report", action="store_true", help="...")
    return parser
```

Phase 17: `--sweep {a,b,c,base} | --report`, `choices=` bound to the committed persona tuple + `"base"`.

**Dispatch with NO default branch** (`run_condition`, `:474-535`) — the shape for the four sweeps:

```python
def run_condition(condition, model, tok, device, forbid, items_by_tier):
    """ONE arm: dispatch onto the committed instrument, normalize, prove the record shape.

    **This function writes no draw loop, no prompt and no scoring rule.** ... A second draw loop
    here is how two arms silently stop being paired.

    Dispatch is exhaustive over ``CONDITION_ORDER`` and has NO default branch. An unrecognized
    name aborts on the first ``_prove``; a name that is in ``CONDITION_ORDER`` but has no branch
    aborts on the second. Falling through to "run something reasonable" would produce a
    well-formed record for an arm nobody asked for.
    """
    _prove(condition in CONDITION_ORDER, ...)
    returned = None
    if condition == "adapter-only":
        recall.set_adapter_enabled(model, True)
        returned = [...]
    elif condition == "base-neither":
        returned = recall.run_closed_book_control(...)
    ...
    _prove(returned is not None, f"condition {condition!r} is in CONDITION_ORDER but no dispatch "
           "branch produced a result — the pre-registration and this dispatch have drifted apart")
```

**Anti-pattern flagged by RESEARCH F-03:** do NOT dispatch to `run_scored_recall` — it scores
against `item.fact.value` (Phase 14's value). Phase 17 dispatches to `recall.complete_question` /
`draw_all` and writes raw completions to disk; scoring happens in `--report`.

**One-process-per-sweep body** (`run_one_condition`, `:2713-2799`) — the exact ordering, the
provenance payload, and the disk write:

```python
def run_one_condition(condition):
    """ONE arm, in this process, start to finish — and this process can run no other.

    Order is not incidental: the clobber guard runs BEFORE anything expensive, because a run that
    refuses to write its report at the end has already been wasted.
    """
    import os, time
    import torch
    from personacore.config import RuntimeConfig
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha
    from personacore.seeding import seed_everything

    started = time.time()
    assert_persistence_report_not_clobbered()
    summary = preflight_device(strict=True)
    device = RuntimeConfig().device
    seed_everything(recall.SEED)   # ONE seed constant in play, the instrument's own

    model, model_cfg, tok, forbid, artifact = recall.load_adapted_model(device)
    ...
    payload = {
        "condition": condition,
        "git_sha": git_sha(),
        "pid": os.getpid(),
        "device": str(device),
        "wall_clock_min": wall / 60,
        "provenance": provenance,
        "config": serializable_config(record["config"]),
        "forbid_ids_masked": int(forbid.sum().item()),
        "vocab_size": model_cfg.vocab_size,
        "by_split": record["by_split"],
    }
    path = arm_record_path(condition)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
```

Phase 17 adds exactly two fields to this payload: `"lora_b_sha256"` and `"sweep"`.
`git_sha` + `pid` are already there and are what the ISO-04 cross-process proof consumes.

**Cross-process pairing proof** (`assert_arms_are_pairable`, `:2658-2710`) — the direct template
for `assert_sweeps_ran_on_distinct_weights`:

```python
def assert_arms_are_pairable(arm_records):
    """PERS-02's pairing claim, checked rather than assumed: same code, same questions, same seeds.

    * **One ``git_sha`` across all four.** Four processes, ONE codebase.
    * **Four DISTINCT pids.** D-01's split, evidenced.
    * **Identical ``(fact_id, split, seed_index)`` sets.** ... The TRIPLE rather than the bare
      index, because every arm's bare index set is 0..n-1 and would match trivially while the
      questions behind it differed.
    """
    shas = {record["git_sha"] for record in arm_records}
    _prove(len(shas) == 1, f"the four arms recorded {len(shas)} different git SHAs ...")
    pids = {record["pid"] for record in arm_records}
    _prove(len(pids) == len(CONDITION_ORDER), ...)
    keyed = {record["condition"]: {(e["fact_id"], e["split"], e["seed_index"]) for ...} ...}
    reference = keyed[CONDITION_ORDER[0]]
    for condition in CONDITION_ORDER[1:]:
        _prove(keyed[condition] == reference, ...)
```

Phase 17's triple is `(slot, seed_index, question)` (D-02: keyed by slot, never `fact_id`), plus
the ISO-04 addition — distinct `lora_b_sha256` per adapter sweep, base digest disjoint from all three.

**Fixture read — seeds carried VERBATIM** (`load_fixture_items`, `:293-336`). Phase 17 calls this
function, it does not rewrite it. The regrouping helper wraps it:

```python
def load_fixture_items():
    """The fixture's 270 questions as ``RecallItem``s, keyed by tier, seeds carried VERBATIM.

    The ``seed_index`` is READ off the fixture and never re-enumerated: the fixture IS the pairing
    key PERS-02 claims, so re-stamping here would silently REPAIR a mismatch instead of surfacing
    it — and a repaired mismatch is indistinguishable, in every number downstream, from a fixture
    that was never wrong.
    """
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
    ...
```

**Statistics — IMPORTED, all four unchanged** (STAT-04 satisfied by import):

| Symbol | Location | Phase 17 use |
|---|---|---|
| `fact_signs(per_fact_by_arm, pair)` | `phase16_persistence.py:1056` | "arms" = cell tuples, "facts" = slot strings |
| `sign_test_exact(signs)` | `:1088` | `SIGN_TEST_N = 8` already equals Phase 17's 8 slots |
| `holm(p_values)` | `:1170` | **see F-08** — `m` is read from Phase 16's `HOLM_FAMILY_PAIRS`; the match at 6 is a coincidence and must be `_prove`d |
| `cluster_bootstrap(per_key_questions)` | `:843` | key-agnostic (`sorted(per_fact_questions)`) — slot keys work as-is |
| `report_proportion(k, n_q, n_draws)` | `:930` | STAT-02's single reporting shape |

`report_proportion`'s zero branch is the STAT-02 mechanism — copy nothing, call it:

```python
    if successes == 0:
        row["rule_of_three_upper"] = rule_of_three(n_questions)
        row["formatted"] = (
            f"{successes}/{n_questions} questions "
            f"(95% Wilson upper bound {row['wilson_upper_95']:.6f}; "
            f"rule-of-three upper bound {row['rule_of_three_upper']:.6f}; {n_draws} draws)"
        )
```

**Phase 17's own `assert_family_closed` twin.** Phase 16's (`:1142-1167`) asserts against its own
arm-keyed `HOLM_FAMILY_PAIRS` and is **not reusable**. Copy the three-proof structure — duplicate
pair, exact set equality, direction-dict key equality — and reprice the arithmetic message:

```python
def assert_family_closed(entered_pairs):
    """T-16-38 — the RUNTIME half: exactly ``HOLM_FAMILY_PAIRS`` entered the gate.

    The static AST scan in ``tests/test_phase16_stats.py`` catches a NEW CALL SITE; this catches a
    DYNAMICALLY-BUILT pair list. Both are needed because a seventh gated comparison can arrive by
    either route, and either one alone leaves the other open.
    """
    entered = tuple(entered_pairs)
    _prove(len(entered) == len(set(entered)), "the same pair entered the Holm family twice ...")
    _prove(set(entered) == set(HOLM_FAMILY_PAIRS), "... At m = 7 alpha is 0.0071429, below the "
           "achievable p of 0.0078125, so the headline dies arithmetically at every possible "
           "outcome — including perfect unanimity")
    _prove(set(SIGN_TEST_ALTERNATIVE) == set(HOLM_FAMILY_PAIRS), "... an undeclared pair is a "
           "pair whose direction could be fixed after its signs are visible")
```

---

### `tests/test_phase17_personas.py` (test, CPU tokenizer-only)

**Analog:** `tests/test_phase14_factset.py` — near line-for-line for the census half.

**Header + the `importlib` script loader** (`:20-48`) — the idiom that loads a driver without
running `main()`, plus the standing justification for importing from `scripts/`:

```python
"""...
Scripts-load justification: no other test imports from ``scripts/`` (test_demo_callback.py
states the convention), but the locked fact set MUST live in the committed driver module for
git history to be the pre-registration proof — moving it into the package would put the
experiment's locked material somewhere the driver could drift from. ``scripts/phase14_factset.py``
defines no ``main()`` and imports no torch, so an ``importlib`` load runs nothing.
"""

import importlib.util
import pathlib
import sys

import pytest

from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fs = _load("phase14_factset")
```

**Frozen-tokenizer fixture** (`:62-66`) — module-scoped, reads the git-tracked artifact:

```python
@pytest.fixture(scope="module")
def tok():
    # The FROZEN production artifact — the registry that ships is what matters, never a
    # freshly trained tokenizer (Pitfall 6).
    return from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")
```

**`test_census` — the committed dict IS the expectation, never a recompute** (`:69-97`):

```python
def test_token_census_matches_locked_literals(tok):
    """D-02(a)/D-04: the committed census is the expectation; never recompute it in-test.

    A drift here means either the frozen tokenizer changed or a value was edited after the
    gate measured it — both invalidate the report the census was transcribed from.
    """
    assert set(fs.VALUE_TOKEN_CENSUS) == {f.id for f in _ALL_LOCKED}
    for fact_id, expected in fs.VALUE_TOKEN_CENSUS.items():
        assert len(tok.encode(_BY_ID[fact_id].value)) == expected, fact_id


def test_byte_fallback_roundtrip(tok):
    """D-02(a): every locked, calibration, register-arm and rejected value round-trips exact."""
    for fact in _ALL_LOCKED + fs.GATE_REJECTED_CANDIDATES:
        assert tok.decode(tok.encode(fact.value)) == fact.value, fact.id


def test_no_dead_ids_emitted(tok):
    live = set(tok.vocab) | set(tok.special_tokens.values())
    for fact in _ALL_LOCKED + fs.GATE_REJECTED_CANDIDATES:
        assert set(tok.encode(fact.value)) <= live, fact.id
```

**Composition assertions** (`:100-109`) — the shape for Phase 17's "3 personas x 8 slots, all 24
distinct, no value reused from any Phase 14 pool" (D-06):

```python
def test_composition_targets():
    """D-05: 5-8 core, 2-3 soft; ROADMAP SC1: 5-10 taught total."""
    assert 5 <= len(fs.LOCKED_FACTS) <= 8
    assert all(f.tier == "core" for f in fs.LOCKED_FACTS)
    # One taught fact per slot — the whole reason the core tier trimmed 16 -> 8.
    assert len({f.slot for f in _TAUGHT}) == len(_TAUGHT)
```

**Standing-fact vs checkpoint-specific split** (`:8-18`) — copy this note verbatim in spirit. The
guessability half **cannot** be a CPU test; only the census and composition halves can:

> **What this test does NOT cover, and structurally CANNOT (D-07).** The *guessability* half ... is
> deliberately absent. That measurement is **checkpoint-specific** ... A future checkpoint
> inheriting a green run of this file has inherited **nothing** about guessability.

---

### `tests/test_phase17_scoring.py` (test, static AST + tiny-GPT)

**Analog A — the AST scan half:** `tests/test_phase14_scoring.py:409-643`
**Analog B — the swap-canary half:** `tests/test_lora_inject.py`

**The file-set scanner** (`test_phase14_scoring.py:439-501`) — the repo's canonical static scan.
Note three things it gets right that a naive walk does not: `async def` bodies count, module-scope
calls are recorded as `"<module>"` rather than dropped, and the attribute form matches:

```python
def _scanned_files():
    """The D-21 file set: ``scripts/*.py`` + ``src/**/*.py``.

    Deliberately not cached: the deliberate-RED probes that prove these guards bite add and
    remove files under ``scripts/``, and a cache would make the guards blind to exactly the
    thing they are being tested against.
    """
    return sorted((_REPO_ROOT / "scripts").glob("*.py")) + sorted(
        (_REPO_ROOT / "src").rglob("*.py")
    )


def _enclosing_functions(tree):
    """``{node: enclosing FunctionDef/AsyncFunctionDef or None}`` for every node in ``tree``.

    ``ast.walk`` is breadth-first, so a parent is always resolved before its children.
    """
    enclosing = {tree: None}
    for parent in ast.walk(tree):
        owner = (
            parent
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
            else enclosing[parent]
        )
        for child in ast.iter_child_nodes(parent):
            enclosing[child] = owner
    return enclosing


def _call_sites(callee):
    """Every ``callee(...)`` call in the D-21 file set as ``(file, function, keyword names)``.

    AST rather than ``inspect.getsource`` string matching: a substring check cannot tell a call
    from a mention in a docstring ...

    A ``**splat`` keyword has ``kw.arg is None`` and is kept in the set, so an unanalysable call
    lands in the "not the bare form" bucket instead of passing as "at least it is not persona".
    """
    sites = []
    for path in _scanned_files():
        file = path.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        enclosing = _enclosing_functions(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if callee not in (getattr(node.func, "id", None), getattr(node.func, "attr", None)):
                continue
            owner = enclosing[node]
            sites.append((file, "<module>" if owner is None else owner.name,
                          frozenset(kw.arg for kw in node.keywords)))
    return sites
```

**HARD EQUALITY against an allowlist, never `in`** (`:539-555`) — plus the anti-collapse guard and
the positive half. All three are load-bearing:

```python
    scanned = _scanned_files()
    assert len(scanned) >= 2, (
        f"the D-21 scan collapsed to {len(scanned)} file(s) — a broken glob makes this guard "
        "green by scanning nothing, which is the exact failure mode the widening exists to close"
    )

    sites = _build_recall_prompt_call_sites()
    assert sites, "no build_recall_prompt call sites found — the AST walk stopped working"

    # HARD EQUALITY against the allowlist. Never `in`, never a subset relation: a membership
    # check is the guard getting weaker while looking bigger (16-RESEARCH Pitfall 3).
    with_persona = sorted((file, func) for file, func, kwargs in sites if "persona" in kwargs)
    assert with_persona == sorted(PERSONA_ALLOWLIST), (...)

    # The POSITIVE half: a guard that only forbids is satisfied by deleting every call site.
    functions = {func for _, func, _ in sites}
    for expected in ("complete_question", "render_context_dump", "assert_no_value_in_prompt"):
        assert expected in functions
```

**`test_scorer_is_cell_blind` — the `inspect.signature` pin.** The repo's only precedent is
`test_phase14_scoring.py:1099-1111`, and it is the right shape (function-local import, hard list
equality on parameter names, plus a named-absence assertion):

```python
    import inspect

    assert callable(pr.assert_value_in_prompt)
    assert not pr.assert_value_in_prompt.__name__.startswith("_")  # public, like its twin

    params = list(inspect.signature(pr.assert_value_in_prompt).parameters)
    assert params[-1] == "values"
    assert params == ["tok", "prompt_ids", "values"]
    # `prompt_ids`, not `question`: ... That divergence is the twin's one structural difference.
    assert "question" not in params
```

Phase 17: `assert params == ["completion", "slot_values"]`, plus
`assert not {"i", "j", "own", "cell", "persona"} & set(params)`. Pair it with a `_call_sites`-style
AST scan of `score_completion`'s body for `Compare` nodes naming `i`/`j` (SC3's structural half).

**`test_swap_canary_bites` — the tiny-GPT CPU fixture** (`test_lora_inject.py:44-67`). Copy
`_tiny_config` / `_build_injected` / `_nudge_lora_b` verbatim; they are exactly the substrate a
canary test needs and cost no checkpoint I/O:

```python
def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184); everything else is shrunk
    # for a cheap CPU fixture (tests/test_slim_checkpoint.py precedent).
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _build_injected(r: int = 4):
    """Seeded tiny GPT with LoRA injected — the load->inject->freeze substrate."""
    torch.manual_seed(1234)
    cfg = _tiny_config()
    model = GPT(cfg)
    lora_cfg = LoRAConfig(r=r)
    n = inject_lora(model, lora_cfg)
    return model, cfg, lora_cfg, n


def _nudge_lora_b(model, seed: int) -> None:
    """Make the adapter delta nonzero/distinctive so applies are observable."""
    torch.manual_seed(seed)
    with torch.no_grad():
        for name, p in model.named_parameters():
            if "lora_B" in name:
                nn.init.normal_(p)
```

**Refusal-precedes-mutation pattern** (`test_lora_inject.py:198-227`) — snapshot before, assert the
raise, assert nothing moved, then a **positive control**. The positive control is the part most
often forgotten and is what stops a guard that rejects everything from passing:

```python
    before = {k: v.clone() for k, v in lora_state_dict(model).items()}

    drifted = {"r": lora_cfg.r, "alpha": 32.0, "dropout": 0.0, "targets": PROJECTIONS}
    with pytest.raises(ValueError, match="scale mismatch"):
        load_adapter_weights(model, {"adapter": adapter, "lora_config": drifted})

    # The refusal precedes the load, like the key and shape audits beside it.
    after = lora_state_dict(model)
    for k, v in before.items():
        assert torch.equal(v, after[k]), f"scale refusal mutated {k}"

    # Positive control: the artifact's OWN config loads. Without it this test would also pass
    # against an audit that rejected every artifact.
    honest = {"r": lora_cfg.r, "alpha": lora_cfg.alpha, "dropout": 0.0, "targets": PROJECTIONS}
    load_adapter_weights(model, {"adapter": adapter, "lora_config": honest})
```

---

### `tests/test_phase17_stats.py` (test, static AST + pure stats)

**Analog:** `tests/test_phase16_stats.py` — the whole file, especially `:23-118` (helpers) and
`:745-853` (the D-21 twin target).

**Driver loader + AST helpers** (`:23-118`) — the version of `_call_sites` that takes a *path* and
returns `(function_name, ast.Call)`. This is the one the `_GATE_MODULES` twin needs, distinct from
`test_phase14_scoring.py`'s file-set variant:

```python
import ast
import importlib.util
import itertools
import math
import pathlib
import random
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_DRIVER_PATH = _REPO_ROOT / "scripts" / "phase16_persistence.py"
_LADDER_PATH = _REPO_ROOT / "scripts" / "phase16_ladder.py"
_CONTEXT_PATH = (_REPO_ROOT / ".planning" / "phases"
                 / "16-weight-vs-prompt-persistence-control" / "16-CONTEXT.md")


def _load_driver():
    spec = importlib.util.spec_from_file_location("phase16_persistence", _DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stats = _load_driver()


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_def(tree, name):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _call_sites(path, callee):
    """Every ``callee(...)`` call in ``path`` as ``(function name or '<module>', ast.Call)``."""
    tree = _tree(path)
    enclosing = _enclosing_functions(tree)
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if callee not in (getattr(node.func, "id", None), getattr(node.func, "attr", None)):
            continue
        holder = enclosing.get(node)
        sites.append(("<module>" if holder is None else holder.name, node))
    return sites
```

**D-21's exact twin target** (`:747-795`) — `_GATE_MODULES` is **file-scoped to Phase 16's two
drivers**, which is precisely why Phase 17 needs its own:

```python
_GATE_MODULES = (_DRIVER_PATH, _LADDER_PATH)


def test_nothing_outside_the_six_pairs_enters_the_verdict_path():
    """T-16-38, the STATIC half — the verdict path has exactly the call sites D-09 permits.

    Scanned across BOTH Phase 16 driver modules, because a seventh gated comparison arriving from
    the ladder would be just as fatal as one arriving from here, and a scan of one file is green
    and blind about the other.
    """
    holm_sites = {module.name: _call_sites(module, "holm") for module in _GATE_MODULES}
    sign_sites = {module.name: _call_sites(module, "sign_test_exact") for module in _GATE_MODULES}

    assert [name for name, _ in holm_sites["phase16_persistence.py"]] == ["compare_arms"], (
        "holm is called from somewhere other than compare_arms — every call site is a hypothesis "
        "family, and D-09 permits exactly one"
    )
    ...
    tree = _tree(_DRIVER_PATH)
    compare = _function_def(tree, "compare_arms")
    called_from_compare = {
        getattr(call.func, "id", None) or getattr(call.func, "attr", None)
        for call in ast.walk(compare)
        if isinstance(call, ast.Call)
    }
    assert "assert_family_closed" in called_from_compare, (
        "compare_arms does not call the runtime family guard — the static scan catches a new call "
        "site, but only assert_family_closed catches a dynamically-built pair list"
    )
```

Phase 17's `_GATE_MODULES` = `(_PERSONAS_PATH, _ISOLATION_PATH, _PERSONA_GATE_PATH)`.

**Identifier-based ban for STAT-06 / ISO-05** (`:798-823`) — the template for
`test_replication_is_not_gated` and `test_no_nine_cell_aggregate`:

```python
def test_context_pressure_sweep_is_not_gated():
    """PERS-03's sweep and the taught replication are descriptive BY CONSTRUCTION (D-09), and that
    is enforced here rather than remembered. Any identifier naming a sweep or a pressure cell that
    reaches ``holm`` or ``sign_test_exact`` turns this red the moment it is written.
    """
    forbidden = ("sweep", "pressure")
    for module in _GATE_MODULES:
        for callee in ("holm", "sign_test_exact"):
            for holder, call in _call_sites(module, callee):
                names = {getattr(node, "id", None) or getattr(node, "attr", None)
                         for node in ast.walk(call)}
                names |= {holder}
                offenders = sorted(n for n in names
                                   if n and any(w in n.lower() for w in forbidden))
                assert not offenders, (...)
```

Phase 17 forbidden words: `("replication", "seed_rep", "aggregate", "overall", "matrix_rate")`.

**SystemExit-with-a-substring assertion register** (`:826-852`) — the repo's standard shape for
"the guard bit, and it bit for the stated reason", including the `else: raise AssertionError`
branch that stops a silent no-raise from passing:

```python
    seventh = tuple(stats.HOLM_FAMILY_PAIRS) + (("adapter-only", "taught-replication"),)
    try:
        stats.assert_family_closed(seventh)
    except SystemExit as exit_:
        assert "0.0071429" in str(exit_)
    else:  # pragma: no cover
        raise AssertionError("a seventh pair entered the Holm family at runtime")
```

**`test_gate_requires_all_six` (D-18)** builds on `test_holm_stops_at_the_first_failure` (`:623-650`),
which already constructs the exact "one retained, later ones retained too" fixture:

```python
    pairs = list(stats.HOLM_FAMILY_PAIRS)
    p_values = dict(zip(pairs, [UNANIMITY_P, 0.012, 0.013, 0.014, 0.015, 0.04]))
    results = stats.holm(p_values)
    assert [rejected for *_, rejected in results] == [True, False, False, False, False, False]
    ...
    # And the family as committed: six unanimous p-values clear every step, 0.05/6 through 0.05/1.
    all_unanimous = dict(zip(pairs, [UNANIMITY_P] * 6))
    assert all(rejected for *_, rejected in stats.holm(all_unanimous))
```

D-18's twin asserts the **verdict function** returns `gated=False` on the 5-of-6 row set and
`gated=True` only on the 6-of-6 set.

**STAT-02 source-level guard** (`tests/test_phase16_driver.py:316-322`) — one regex, applies to
each Phase 17 driver:

```python
def test_driver_never_renders_a_bare_zero_percent_literal():
    """STAT-02 hygiene, pinned at the source: no bare ``0%`` may be typed into this module.

    Cheap here, and it forecloses the shape plan 16-10 must not inherit — a zero rate printed
    without its denominator and its rule-of-three ceiling reads as proven absence.
    """
    assert re.search(r"\b0(\.0+)?%", _driver_source()) is None
```

**`test_no_phase14_thresholds` (ISO-07)** has no exact analog. Closest is
`test_the_ladder_is_licensing_and_not_a_hypothesis_test` (`:855-860`) — a plain source-substring
scan, which is the right weight for a "this literal must not appear" check:

```python
def test_the_ladder_is_licensing_and_not_a_hypothesis_test():
    ladder_source = _LADDER_PATH.read_text(encoding="utf-8")
    assert "licensing" in ladder_source.lower()
    assert "sign_test_exact" not in ladder_source
    assert "HOLM" not in ladder_source
```

---

### `scripts/teach_persona.py` (modify — additive `seed=` keyword, F-10)

**Analog for the *shape of the change*:** `phase14_factset_gate.probe_guessability`'s D-16 widening
(`:111-140`). Its docstring is the register the Phase-17 `seed=` widening should echo:

> This module measured guessability only for candidates of ``phase14_factset``, through ``main()``.
> Phase 16's capability ladder needs the same measurement for a SYNTHETIC span, and Phase 17's
> ISO-01 needs it again for its own material — so the surface is widened here, in the instrument
> itself, rather than copied into a phase driver. That is the ISO-01 precedent stated as a rule:
> **import this instrument, never copy it.**

**The three hardcoded sites** (measured, `grep -n "SEED"`):

| Line | Site | What the seed owns |
|---|---|---|
| `teach_persona.py:99` | `SEED = 1337` | the module constant |
| `:412` | `seed_everything(SEED)` inside `build_arm_bins` | teaching-bin construction order |
| `:563` | `seed_everything(SEED)` inside `train_arm` | **the LoRA init draw + data order** — D-14's target |
| `:603` | `TrainConfig(..., seed=SEED)` | the loop's own seed |

`:563` carries a load-bearing ordering comment that a `seed=` widening must preserve verbatim:

```python
    # Re-seed IMMEDIATELY before the GPT build: this seed owns the training data order (the
    # finetune_ab.py provenance note), and the bins build above consumed numpy RNG in its smoke
    # draw. Seeding once at the top would make the data order depend on the bins path.
    seed_everything(SEED)
```

Signature to widen (`:501`), additively, default preserving today's behaviour bit-for-bit:

```python
def train_arm(arm, *, facts, family_ids, second_person=False, replay_ratio=0.0):
```
→ `def train_arm(arm, *, facts, family_ids, second_person=False, replay_ratio=0.0, seed=SEED):`

Same for `build_arm_bins` (`:403`). All three internal uses read the parameter, not the global.
The provenance print at `:426` and `:688` already emits `seed={SEED}` — those become `seed={seed}`
so the recorded provenance names the seed the run actually used (D-14's audit trail).

**`arm_outputs` name-scoping** (`:190-211`) is the analog for Phase 17's three adapter paths — one
function, no two arms sharing a path, plus `refuse_if_exists` (`:214-222`) on **all** targets up
front:

```python
def refuse_if_exists(paths):
    """Refuse-to-rerun: an arm's outputs are RECORDED evidence once written — a rerun on
    drifted code or a drifted fact set would silently replace them. Fail loud, name the file."""
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[teach_persona] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )
```

**D-20 confirms no change here:** `LORA_CFG = LoRAConfig()` at `:478` is already `r=8, alpha=16.0`.

---

### `scripts/phase16_persistence.py` (modify — **optional**, F-09)

`aggregate_by_fact` (`:779`) hardcodes `record["fact_id"]`. RESEARCH marks the additive `key=`
widening **marginal**: passing `fact_id = slot` works today (one Phase-14 fact per slot makes it a
bijection) but silently repurposes a field name.

**Ladder verdict:** Phase 17 does not need `aggregate_by_fact` at all — `cluster_bootstrap` and
`fact_signs` are both key-agnostic, and Phase 17 builds its own `{slot: [(k, n), ...]}` from raw
completions. **Recommend skipping the modification** unless a plan finds a concrete call site.
`pyproject.toml` stays untouched either way (STAT-04).

---

## Shared Patterns

### The `_prove` register — every check is a `SystemExit`, never an `assert`
**Source:** `scripts/phase16_persistence.py:120-128` (twins at `phase14_recall._prove`, `phase16_ladder._prove`)
**Apply to:** all three Phase 17 driver scripts
Each driver defines its OWN `_prove` with its own bracket prefix. Never import another driver's —
"an abort that names the wrong driver sends its reader to the wrong file."
The message must name **the contract violated and the consequence**, not just the condition. Every
message in `phase16_persistence.py` follows the pattern: *what happened* → *why the resulting number
would be wrong* → *which decision id it violates*.

### Lazy-import rule for fact values
**Source:** `scripts/phase16_persistence.py:12-15` (rule), `:311` (application)
**Apply to:** `phase17_isolation.py`, and any Phase 17 driver that reads the fixture
```python
    import phase14_factset as fs  # LAZY — see the LAZY-IMPORT RULE in the module docstring.
```
Phase 17's inverse also matters: `phase17_personas.py` holds the 24 values at module scope by
design (it IS the committed data), so `phase17_isolation.py` must import it **lazily** to keep the
values out of the scored driver's string surface.

### Nothing executes at import; `main()` under a `__main__` guard
**Source:** `scripts/phase16_persistence.py:8-10, 2855-2865`
**Apply to:** all three Phase 17 drivers — this is what makes
`importlib.util.spec_from_file_location` safe in a CPU-only test.
```python
def main():
    """Dispatch. ONE condition per invocation, or the report — and nothing that runs two arms."""
    args = build_parser().parse_args()
    if args.report:
        run_report_mode()
    else:
        run_one_condition(args.condition)


if __name__ == "__main__":
    main()
```

### Derived-not-retyped
**Source:** `phase16_persistence.py:1001-1003` (family), `:553-555` (`COSINE_POOL_SIZE`), `:922-926`
(bootstrap cut count derived from `alpha`), `:1177` (`m = len(HOLM_FAMILY_PAIRS)`)
**Apply to:** every Phase 17 constant that must agree with another
The canonical phrasing: *"two numbers that must agree are two numbers that can stop agreeing."*
`tests/test_phase16_stats.py:610-620` pins it with an AST scan for a literal divisor:
```python
def test_holm_reads_the_family_length_rather_than_a_retyped_six():
    body = _function_def(_tree(_DRIVER_PATH), "holm")
    divisors = [node.right for node in ast.walk(body)
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)]
    assert divisors, "holm computes no alpha at all"
    for divisor in divisors:
        assert not (isinstance(divisor, ast.Constant) and divisor.value == 6)
```

### Empty-scan / collapsed-glob guards
**Source:** `test_phase14_scoring.py:531-537`, `test_phase16_prereg.py:101-105`
**Apply to:** every static scan and every glob in Phase 17's tests
Every scan asserts it found something before asserting what it found. A guard that scans zero files
is green and blind — the repo names this its most recurring defect class.

### The anchored `## Verdict` read
**Source:** `scripts/_verdict.py:24-30`
**Apply to:** `phase17_persona_gate.py`'s clobber guard and the GO/ADAPT enforcement
Import `recorded_verdict` / `VERDICT_SECTION`. Never `text.split("## Verdict")[-1]` — that exact
split was CR-02, five copies, four broken by a prose mention of the heading.

### Provenance payload per run
**Source:** `phase16_persistence.py:2783-2795`
**Apply to:** all four Phase 17 sweep records
`git_sha()` + `os.getpid()` + `str(device)` + wall clock, written with
`json.dumps(payload, indent=2, sort_keys=True)`. These fields are what the ISO-04 cross-process
proof reads back; the digest is the only Phase-17 addition.

---

## No Analog Found

| File / behaviour | Role | Data Flow | Reason |
|---|---|---|---|
| `test_no_phase14_thresholds` (ISO-07) | test (static source scan) | string scan | Nearest is `test_the_ladder_is_licensing_and_not_a_hypothesis_test` (`test_phase16_stats.py:855-860`) — a plain substring scan. That is the right weight, but it scans for the *absence of statistics machinery*, not for the absence of *another phase's numeric thresholds*. The list of forbidden Phase-14 literals has to be authored fresh. |
| `worst_pair` + its D-19 tie-break | pure function | transform | No `argmax`-with-committed-tie-break exists anywhere in the repo. Closest in spirit is `COSINE_POOL_SIZE`'s derived-constant discipline (`phase16_persistence.py:553-555`) and `sorted()` determinism used throughout, but the selection rule itself is genuinely new. Write it as ~6 lines with an explicit `min(...)` over `(-mean_rate, i, j)` and one test at the all-zero triple tie. |
| D-13 base-prior derivation (`normalize(completion) in base_texts`) | pure function | set membership | The *primitive* is committed (`phase14_recall.normalize` / `contains_value` at `:279,300`), but "coincides with what the adapter-off column produced for this slot" has no precedent — Phase 14/16 both matched against static value lists. The assembly-side lookup table is new. |
| `frozenset` scorer return on a double match (D-17) | pure function | transform | `phase14_recall.find_contradictions` (`:325`) records multi-match descriptively but returns a list of contradicting values, not a label set over personas. Reuse its containment call; the return shape is new. |

---

## Metadata

**Analog search scope:** `scripts/` (33 files), `tests/` (68 files), `src/personacore/` (36 files)
**Files scanned:** 14 read in full or in targeted ranges; 3 grepped
**Pattern extraction date:** 2026-08-14
**Anchor commit:** `6cfa977` (clean tree)
