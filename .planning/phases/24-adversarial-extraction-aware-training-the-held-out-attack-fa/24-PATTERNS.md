# Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family - Pattern Map

**Mapped:** 2026-08-30
**Files analyzed:** 10 (4 new, 6 modified)
**Analogs found:** 10 / 10
**Every line number below was re-verified at HEAD this session.** Corrections to CONTEXT.md's
anchors are listed at the end and are the numbers the planner should carry forward.

---

## File Classification

| New/Modified file | New? | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|---|
| `scripts/phase24_refusal.py` (D-01 templates; location is Claude's Discretion) | NEW | data/constants module | transform (table → rendered episodes) | `scripts/phase21_filler.py` | exact |
| `scripts/teach_persona.py` — `build_bins(..., adversarial_ratio=0.0)` | MOD | build seam | batch / file-I/O | `replay_ratio` kwarg in the same function | exact |
| `scripts/teach_persona.py` — `arm_spec` + `ARMS` new arm row | MOD | config dispatch | request-response | `arm_spec`'s `dp_n8` / `dp_n64` rows `:922-936` | exact |
| `scripts/teach_persona.py` — `build_arm_bins` threading | MOD | orchestration seam | batch | `resume_from` / `align_facts` threading `:945-1039` | exact |
| `scripts/phase14_recall.py` — `contains_refusal` | MOD | scoring utility | transform | `contains_value` `:300` | exact |
| `scripts/mitigation_budget.py` — D-09 grid | MOD | config (literal pin) | none (module constants) | `SWEEP_POINTS` + `SWEEP_POINTS_PROVENANCE` `:374-403` | exact |
| `tests/test_phase24_*.py` — D-05 four-corner band check | NEW | test | file-I/O (tmp_path build) | `tests/test_phase21_aligned_bins.py` `:161-235` | exact |
| `tests/test_phase14_scoring.py` — D-02 sibling guard + 4th allowlist entry | MOD | test | transform | `test_no_fact_strings_at_import` `:367-406`; allowlist `:422` | exact |
| D-13 `family` / `source_family` assertions | NEW | test | file-I/O (read committed JSON) | `test_schema_and_reserved_family` `:538` + `test_phase19_erasure.py:2395` | role-match |
| `results/phase24_*.json` + its emitter (ADVT-03) | NEW | artifact + writer | batch write-once | `scripts/phase21_unit_record.py` `_write` `:729` / `_provenance` `:702` | exact |
| `.planning/ROADMAP.md` — D-13 dated continuation | MOD | doc | n/a | `.planning/ROADMAP.md:51-71` + `tests/test_phase23_cost.py:647-742` | exact |

---

## Pattern Assignments

### 1. `scripts/phase24_refusal.py` — the D-01 refusal-template module

**Analog:** `scripts/phase21_filler.py` (a scripts-level constants module whose slot table is
merged into the published grammar at `teach_persona.py:437-449`).

**Where the table gets declared** — `scripts/phase21_filler.py:61-71` (a `dict[str, ...]` keyed
by slot, typed against the `phase14_factset` NamedTuple, prefixed key as a legibility convention):

```python
FILLER_SLOT_FORMS: dict[str, fs.SlotForms] = {
    "filler_boat_name": fs.SlotForms(
        np1="the name of your boat",
        np2="what your boat is called",
        ...
    ),
```

**The published table it parallels** — `scripts/phase14_factset.py:524-543`, `SlotForms` is a
`NamedTuple` of eight `str` fields, and `SLOT_FORMS: dict[str, SlotForms]` has exactly 11 keys.
A per-slot refusal table is a **ninth field or a parallel dict**, not a new type: copy the
`NamedTuple`-of-strings + `dict[str, T]` shape.

**The merge + clash-check precedent the planner extends** — `scripts/teach_persona.py:412-451`
(the whole `_slot_forms_for` function). Verified excerpt, `:432-451`:

```python
    if all(fact.slot in fs.SLOT_FORMS for fact in facts):
        return None

    import phase21_filler  # lazy, for the same reason `arm_spec`'s is — see its docstring

    clash = sorted(set(fs.SLOT_FORMS) & set(phase21_filler.FILLER_SLOT_FORMS))
    if clash:
        raise SystemExit(
            f"[teach_persona] filler slots {clash} collide with the PUBLISHED slot grammar. ..."
        )
    widened = {**fs.SLOT_FORMS, **phase21_filler.FILLER_SLOT_FORMS}
    undeclared = sorted({fact.slot for fact in facts} - set(widened))
    if undeclared:
        raise SystemExit(
            f"[teach_persona] no slot grammar defines {undeclared} — neither "
            "phase14_factset.SLOT_FORMS nor phase21_filler.FILLER_SLOT_FORMS. ..."
        )
    return widened
```

Three properties to copy verbatim: **lazy import** (keeps `teach_persona`'s import graph clean for
`test_no_fact_strings_at_import`'s clean-room scan), **early `return None`** so the default path is
literally unchanged, and **`SystemExit` naming the missing key** rather than a bare `KeyError`.

**How the module is consumed** — `scripts/teach_persona.py:455-464`:

```python
def render_episodes(facts, family_ids, *, second_person=False):
    episodes = []
    forms = _slot_forms_for(facts)
    for fact in facts:
        for family_id in sorted(family_ids):
            episodes.extend(
                fs.render_family(family_id, fact, second_person=second_person, forms=forms)
            )
    return episodes
```

`render_episodes` returns a flat list of `(question, answer)` pairs. **An adversarial episode is the
same 2-tuple** — `(attack_prompt_text, refusal_text)` — so it needs no new episode type. But see the
landmine in §2: `build_bins` consumes `(question, answer)` **strings**, while `phase18_extraction`
hands out `prompt_ids` (ints). The planner must resolve that seam explicitly.

**Import-time enforcement precedent** — `scripts/phase21_filler.py:443` runs
`refuse_collisions()` at module scope ("the deterministic half runs AT IMPORT — a colliding value
can never reach a bin"). D-02's containment property is the exact analogue and can be enforced the
same way, in addition to the test.

---

### 2. `adversarial_ratio` as a `build_bins` kwarg

**Analog:** `replay_ratio` in the same function. Copy the **full four-part shape**.

**(a) Signature — keyword-only, falsy default** (`scripts/teach_persona.py:467`):

```python
def build_bins(tok, episodes, bin_path, mask_path, *, replay_ratio=0.0, align_facts=None):
```

**(b) Where it is read — one `if ratio > 0` branch inside the flat path**
(`scripts/teach_persona.py:485-498`):

```python
    id_shards, mask_shards, lengths, fractions = [], [], [], []
    for question, answer in episodes:
        ids, mask = encode_dialogue(tok, [], [(question, answer)])
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))
        lengths.append(len(ids))
        fractions.append(float(np.mean(mask)))

    teaching_tokens = int(sum(lengths))
    replay_tokens = 0
    if replay_ratio > 0:
        replay_tokens = _prepend_replay(id_shards, mask_shards, replay_ratio, teaching_tokens)

    ids_all = np.concatenate(id_shards)
    mask_all = np.concatenate(mask_shards)
```

**This is the exact insertion point for D-08's interleave.** The mixture is a mutation of
`id_shards` / `mask_shards` **before** `np.concatenate` — `_prepend_replay` does it with
`.insert(0, ...)`; the adversarial helper does it with a seed-derived permutation of the merged
list. `train()` is never touched, which is what "no new training seam" means.

**Note the `[]` at `:487`** — the hardcoded empty persona. D-10's A3 arm is a change to **this
literal**, and `encode_dialogue` renders a passed persona at mask=0
(`src/personacore/dialogue/serialize.py:81-82`), so an empty persona stays byte-identical and SC1
survives.

**(c) The stats dict the ratio is echoed into** (`scripts/teach_persona.py:511-526`) — twelve keys,
byte-pinned by `repr(stats)` against the golden fixture:

```python
    return {
        "episodes": len(episodes),
        "tokens": int(len(ids_all)),
        "teaching_tokens": teaching_tokens,
        "replay_tokens": replay_tokens,
        "replay_ratio": replay_ratio,
        "episode_len_mean": float(np.mean(lengths)),
        ...
        "mask_fraction": frac,
        ...
    }
```

**LANDMINE — this is the byte-identity trap.** `tests/test_phase21_aligned_bins.py:225` asserts
`repr(stats) == GOLDEN["stats_repr"]`. **Adding `"adversarial_ratio"` / `"adversarial_tokens"` keys
to this dict on the DEFAULT path turns that guard RED** even though no bin byte moved.
`_build_aligned_bins` set the precedent for the correct move: additive keys appear **only on the
non-default branch** (`build_bins` docstring `:481-483`: *"the five additive keys appear ONLY on the
aligned branch"*). Emit adversarial keys under `if adversarial_ratio > 0:` only.

**(d) The sizing helper, in the `_prepend_replay` shape** (`scripts/teach_persona.py:751`):

```python
def _prepend_replay(id_shards, mask_shards, replay_ratio, teaching_tokens, *, n_facts=None):
```

It mutates the shard lists in place, returns the token count, and `SystemExit`s with the sizing
formula spelled out in the message (`:800-809`). D-06's episode-unit sizing is the same function
shape: `n_adversarial = round(adversarial_ratio * len(clean_episodes))`, computed from the
**episode count**, never from `teaching_tokens` — that is the `n_facts is None` legacy branch
`tests/test_phase21_replay_volume.py:260` exists to police.

**(e) Threading through `build_arm_bins`** (`scripts/teach_persona.py:945-955`, keyword-only with
today's default; `:1024-1031` is the call):

```python
def build_arm_bins(
    arm, facts, family_ids, *,
    second_person=False, replay_ratio=0.0, seed=SEED, prefix="phase14", resume_from=None,
):
    ...
    stats = build_bins(
        tok, episodes, outputs["bin"], outputs["mask"],
        replay_ratio=replay_ratio, align_facts=pairs,
    )
```

The docstring `:965-968` is the packer-by-arm-name rule; `aligned = arm in DP_ARMS` at `:1005` with
`DP_ARMS = ("dp_n8", "dp_n64")` at `:270` — a **literal closed 2-tuple, no prefix matching**. Any
new arm name outside those two literals packs FLAT. D-08's inference is confirmed at the mechanism.

**(f) The new arm row** (`scripts/teach_persona.py:922-936`) — one `if arm == ...: return` triple:

```python
    if arm == "dp_n8":
        return fs.LOCKED_FACTS, False, 0.0
    if arm == "dp_n64":
        import phase21_filler   # LAZY, deliberately not at module scope
        return fs.LOCKED_FACTS + phase21_filler.FILLER_FACTS, False, 0.0
    raise SystemExit(f"[teach_persona] unknown arm {arm!r} — expected one of {ARMS}")
```

**Planner dependency 24-RESEARCH names:** the adversarial arm's row must return
`replay_ratio = 0.0`. A non-zero ratio invalidates every mask-fraction figure in 24-RESEARCH
(0.359 → 0.403 on the `real` arm).

**(g) The resume constraint** (`scripts/teach_persona.py:1041-1063`) — rebuild-and-compare:

```python
    if before_digests is not None:
        drifted = {
            path: (was, now)
            for path, was in before_digests.items()
            if (now := _sha256(path)) != was
        }
        if drifted:
            raise SystemExit(
                "[teach_persona] the resumed arm rebuilt a DIFFERENT corpus ..."
                f". The pack is deterministic in (facts, family_ids, second_person, "
                f"replay_ratio, seed={seed}), ..."
            )
```

The determinism tuple is spelled out in the raise message. D-08's permutation must be a pure
function of `seed`; and this message's tuple should gain `adversarial_ratio` in the same diff, or it
names a determinism claim narrower than the one the code now makes.

**(h) The build-time killer D-05 defends against** (`scripts/teach_persona.py:528-556`,
`_prove_floor_and_band`) — checked on the **aggregate**, `:549`:

```python
    frac = float(mask_all.mean())
    lo, hi = MASK_FRACTION_BAND
    if not lo <= frac <= hi:
        raise SystemExit(
            f"[teach_persona] masked fraction {frac:.4f} outside [{lo}, {hi}] — ..."
        )
    return frac
```

`MASK_FRACTION_BAND = (0.15, 0.95)` at `:127`. Per-episode fractions never reach this guard.

---

### 3. `tests/test_phase24_*.py` — the D-05 four-corner build-only band check

**Analog:** `tests/test_phase21_aligned_bins.py`.

**The build fixture to copy** (`tests/test_phase21_aligned_bins.py:151-183`) — reseed, load the
frozen tokenizer, build under `tmp_path`, return `(stats, bin_path, mask_path)`:

```python
def _sha256(path):
    """BYTES, never text — the tests/test_package.py:36 rule."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _build(tmp_path, name, **kwargs):
    """One flat v2.0 or aligned build under tmp_path; returns (stats, bin_path, mask_path)."""
    seed_everything(tp.SEED)
    tok = from_json(tp.TOKENIZER_PATH)
    bin_path = tmp_path / f"{name}.bin"
    mask_path = tmp_path / f"{name}_mask.bin"
    stats = tp.build_bins(tok, kwargs.pop("episodes"), bin_path, mask_path, **kwargs)
    return stats, bin_path, mask_path
```

**The scripts-path preamble** (`tests/test_phase21_aligned_bins.py:17-34`):

```python
import hashlib, json, pathlib, sys
import numpy as np
import pytest

from personacore.seeding import seed_everything
from personacore.tokenizer import from_json

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (scripts/ is not a package)
import teach_persona as tp  # noqa: E402
```

**The assertion shape for the four corners** — parametrize over `(arm, ratio)` and read
`stats["mask_fraction"]`, asserting **margin** rather than membership (D-05 says "with real margin,
not borderline"). The band constant is imported, never retyped: `tp.MASK_FRACTION_BAND`.

**The load-bearing sibling that must be watched RED** (`tests/test_phase21_aligned_bins.py:229-241`)
— the precedent that exists precisely because a byte-identity guard over an unwired kwarg is
vacuously green:

```python
def test_align_facts_is_wired(tmp_path):
    """THE LOAD-BEARING HALF. Without this the identity guard above is vacuous.

    If this test passes BEFORE the feature is wired, `align_facts` is a kwarg nobody reads
    and every `align_facts=None` byte-identity assertion is trivially true.
    """
    ...
    assert fact_path.exists(), (
        "the third bin did not appear — align_facts is not wired, so every "
        "align_facts=None byte-identity assertion in this module is VACUOUS"
    )
```

`adversarial_ratio` needs the same sibling: a build at a non-zero ratio must produce a **different
sha256** and a **different episode count** from the `0.0` build.

**The SC1 byte-identity half it pairs with** (`tests/test_phase21_aligned_bins.py:200-226`) —
including the stale-fixture escape hatch, which the planner should not weaken:

```python
def test_build_bins_byte_identity_default_matches_the_v2_golden(tmp_path):
    tokenizer_sha = _sha256(tp.TOKENIZER_PATH)
    if tokenizer_sha != GOLDEN["meta"]["tokenizer_sha256"]:
        pytest.fail(
            f"THE FIXTURE IS STALE, not the code: ... Re-capture the fixture; do "
            "NOT edit build_bins to chase the digest."
        )
    ...
    assert _sha256(bin_path) == GOLDEN["token_bin_sha256"]
    assert _sha256(mask_path) == GOLDEN["mask_bin_sha256"]
    assert repr(stats) == GOLDEN["stats_repr"]
```

**Resume-side analog:** `tests/test_phase23_resume.py:143-188` (`_resume_fixture` / `_resume_call`)
imports its environment from sibling test modules rather than rebuilding it:

```python
from test_phase22_checkpoint import _next_draw  # noqa: E402  (tests/ is not one either)
from test_phase22_wiring import _e2e_env  # noqa: E402
from test_phase23_mps_venue import _MPS_AVAILABLE, _MPS_SKIP  # noqa: E402
```

If Phase 24 needs a resume-with-`adversarial_ratio` leg, it imports `_e2e_env` — it does not write
a second copy.

---

### 4. The D-02 sibling guard in `tests/test_phase14_scoring.py`

**Analog:** the existing pair, helper at `:349`, test at `:367`.

**The helper — call it, do not reimplement containment** (`tests/test_phase14_scoring.py:349-364`):

```python
def embedded_fact_values(module, forbidden):
    """``(value, count)`` for every locked/soft value EMBEDDED in a string this module holds."""
    hits = []
    for text in _module_strings(module):
        lowered = text.lower()
        hits += [(value, lowered.count(value)) for value in forbidden if value in lowered]
    return hits
```

`_module_strings` (`:332-346`) walks module attributes, recurses into tuples/dicts via
`_strings_in`, and includes `__doc__` of the module, its own-module objects and class members.
**Docstrings are in scope** — a refusal template quoted in prose is a hit.

**The existing call shape, and the assertion D-02 says to leave alone**
(`tests/test_phase14_scoring.py:398-406`):

```python
    spec = importlib.util.spec_from_file_location(
        "phase14_factset", _REPO_ROOT / "scripts" / "phase14_factset.py"
    )
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)

    forbidden = tuple(f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS)
    assert len(forbidden) == 10  # all 8 locked + both soft — no tier is exempt from the scan
    assert embedded_fact_values(driver, forbidden) == []
```

**The sibling's `forbidden` uses the WIDER D-10 lexicon** — the vocabulary is already declared as
committed material at `scripts/phase14_factset.py:424-425` (comment) with the two sources at
`:429` (`GATE_REJECTED_CANDIDATES`, 12 entries) and `:446` (`LOCKED_VALUES`, 8 entries):

```python
# This tuple is D-10's contradiction-detector LEXICON SOURCE. The detector's vocabulary is
# `set(LOCKED_VALUES) | {f.value for f in GATE_REJECTED_CANDIDATES}` — committed, auditable,
# pre-existing material that requires zero new editorial judgment ...
GATE_REJECTED_CANDIDATES: tuple[Fact, ...] = _locked(...)

LOCKED_VALUES: tuple[str, ...] = tuple(f.value for f in LOCKED_FACTS)
```

So the sibling's body is `forbidden = sorted(set(fs.LOCKED_VALUES) | {f.value for f in
fs.GATE_REJECTED_CANDIDATES})` + `assert embedded_fact_values(refusal_module, forbidden) == []`,
with its **own** count assertion (20) pinned separately from the untouched `== 10`.

**The D-10 fourth `PERSONA_ALLOWLIST` entry** — the table is at `:422`; each entry is a
`(file, function)` pair preceded by a **written justification comment** (`:423-437` shows the three
incumbents' comment style). The guard is at `:557`:

```python
    scanned = _scanned_files()
    assert len(scanned) >= 2, (
        f"the D-21 scan collapsed to {len(scanned)} file(s) — a broken glob makes this guard "
        "green by scanning nothing, ..."
    )
    sites = _build_recall_prompt_call_sites()
    assert sites, "no build_recall_prompt call sites found — the AST walk stopped working"

    with_persona = sorted((file, func) for file, func, kwargs in sites if "persona" in kwargs)
    assert with_persona == sorted(PERSONA_ALLOWLIST), (...)
```

Hard equality, AST-derived, `scripts/*.py` + `src/**/*.py`. The entry and the call site land in
**the same commit** — pre-adding is as red as omitting.

---

### 5. The two D-13 corpus assertions

**Analog A — the register they join** (`tests/test_phase18_corpus.py:538-563`,
`test_schema_and_reserved_family`): schema as ordered tuple equality, counts **derived twice and
typed zero times**:

```python
def test_schema_and_reserved_family():
    corpus = p18.build_corpus(tok)
    entries = corpus["prompts"]
    assert corpus["entry_keys"] == list(p18.CORPUS_ENTRY_KEYS)

    for entry in entries:
        assert tuple(entry) == p18.CORPUS_ENTRY_KEYS, (
            f"entry keys {tuple(entry)} are not D-11's schema {p18.CORPUS_ENTRY_KEYS} — exact and "
            "ordered, never a superset"
        )
    ...
    flagged = [(tier, row) for tier, row in _fixture_core_rows() if row["reserved"]]
    probes = {
        probe for fact in factset.LOCKED_FACTS for probe in factset.RESERVED_HELDOUT_PROBES[fact.id]
    }
    assert {row["question"] for _tier, row in flagged} == probes, (...)
```

**Note:** this test **rebuilds** the corpus via `p18.build_corpus(tok)`. SC2 says the check is
*"read from `results/phase18_corpus.json`"*, which is the other reader.

**Analog B — reading the committed artifact** (`tests/test_phase19_erasure.py:2392-2396`) — the
only test in the tree that loads the file:

```python
def test_parity_recomputes_the_corpus_digest_and_never_pastes_it():
    """Q7.8 — the Phase 19 target arms REUSE `results/phase18_corpus.json` verbatim."""
    extraction = _load("phase18_extraction", "scripts/phase18_extraction.py")
    corpus = json.loads((_ROOT / "results" / "phase18_corpus.json").read_text(encoding="utf-8"))
    expected = erasure.phase18_parity_values()
    assert expected["corpus_sha256"] == extraction.corpus_sha256(corpus)
```

Path constant precedent: `scripts/phase18_extraction.py:697`
(`CORPUS_PATH = _REPO_ROOT / "results" / "phase18_corpus.json"`) and
`scripts/phase19_erasure.py:1627` (`PHASE18_CORPUS_PATH`) — **resolve the path from the module,
never a test-local string literal.**

**Census re-verified this session against the committed file** (`json` + `collections.Counter`),
so the two assertions have known-green targets:

```
family:        {A1-mild: 216, A1-aggressive: 216, A2: 216, A3: 216}   (864 total)
tier:          {core_taught: 448, core_held_out: 416}
taught  source_family: {F1: 160, F2: 160, F6: 128}
heldout source_family: {reserved: 128, F3: 96, F7: 96, F8: 96}
```

Both assertions are set-disjointness over one key, in the hard-equality register above — never
`issubset`, never `in` ("a membership check is the guard getting weaker while looking bigger",
`tests/test_phase14_scoring.py:555`).

**Analog C — the ROADMAP dated continuation** (`.planning/ROADMAP.md:51-71` is the live 23-12
instance; the guard that makes it enforceable is `tests/test_phase23_cost.py:647-742`):

```python
_CLAIM_TEXT = "~1,010× training"
_BEGIN_SENTINEL = "<!-- 23-12-CONTINUATION-BEGIN -->"
_END_SENTINEL = "<!-- 23-12-CONTINUATION-END -->"
_MARKER = re.compile(r"RETRACTED IN PLACE (\d{4}-\d{2}-\d{2}) \(plan 23-12\)")
_CORRECTED_FILES = (".planning/REQUIREMENTS.md", ".planning/ROADMAP.md", ".planning/STATE.md")
```

and the test body (`:792-817`):

```python
    text = (_ROOT / relative_path).read_text(encoding="utf-8")
    flat = _prose.normalized(text)
    claim = _prose.normalized(_CLAIM_TEXT)
    assert claim in flat, (
        f"{relative_path} no longer carries the original claim {_CLAIM_TEXT!r}. A correction that "
        "removes the sentence it corrects is a rewrite, not a retraction ..."
    )
    where = flat.index(claim)
    marker = _MARKER.search(flat, where)
    assert marker is not None, (...)
```

Three copyable rules: match through **`scripts/_prose.normalized`** (line wrapping makes a bare
`in` report a false absence), search for the marker **from the claim's index** (not from byte 0),
and count sentinels with `str.count(...) == 1` — `_continuation` at `:723-742` documents that
`grep -c` counts LINES and is defeated by two sentinels on one line.

SC2's exact sentence to preserve is `.planning/ROADMAP.md:725-728`
(*"a zero-`(fact_id, seed_index)`-overlap structural check read from `results/phase18_corpus.json`"*).
Phase 24's sentinels must carry a **24-XX** plan id — `23-12-CONTINUATION-*` is already present in
this file and re-using it would break the `count == 1` guard.

---

### 6. The committed ADVT-03 per-arm scored-token record

Nothing persists these today: `grep -rn "mask_fraction" --include="*.json"` returns only the golden
fixture and the v3.0 calibration results (24-RESEARCH, verified). `build_bins` already computes
everything needed at `scripts/teach_persona.py:511-526`; `build_arm_bins` only **prints** it at
`:1065-1077`.

**Writer analog** — `scripts/phase21_unit_record.py`. The path register `:168-172`:

```python
ARTIFACTS = {
    ...
    "multiplicity": _ROOT / "results" / "phase21_multiplicity.json",
}
```

The provenance block `:702-726` (every artifact carries it):

```python
def _provenance(**extra):
    """``git_sha`` + wall clock + interpreter + the pin's digest, on every artifact."""
    pin = _ROOT / "scripts" / "mitigation_unit.py"
    record = {
        "git_sha": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": platform.python_version(),
        "seed": SEED,
        "pin_module": "scripts/mitigation_unit.py",
        "pin_sha256": hashlib.sha256(pin.read_bytes()).hexdigest(),
        ...
    }
    record.update(extra)
    return record
```

The single write seam `:729-753` — refuse-to-rerun and refuse-if-dirty **before** the bytes land:

```python
def _write(path, document):
    """Refuse-to-rerun and refuse-if-dirty, then write. Both refusals are IMPORTED, not invented."""
    path = pathlib.Path(path)
    refuse_existing_artifacts([path])
    refuse_dirty_publication(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path
```

The document assembler `:1264-1300` (`multiplicity_document`) — a flat dict of named blocks with
`"provenance": _provenance(...)` last. Committed top-level keys, verified:
`['budget', 'rows', 'corpus_geometry', 'a3_discharge', 'pin_discrepancy', 'findings', 'provenance']`.

The per-row shape that carries **its own denominator and its own source label** — copy this for
ADVT-03's scored-token rows (`scripts/phase21_unit_record.py:1237-1259`, `_corpus_geometry`):

```python
    return {
        "n_facts": n_facts,
        "arm": measurement["arm"],
        "episodes": measurement["episodes"],
        "total_tokens": total_tokens,
        "total_tokens_formula": "total_windows * block_size + 1 (the label-shift tail)",
        "teaching_tokens": measurement["teaching_tokens"],
        "pad_fraction": stats["pad_tokens"] / total_tokens,
        "pad_fraction_denominator": "total_tokens (padded, including the label-shift tail)",
        "grad_accum_steps": micro_steps,
        "grad_accum_steps_source": (
            "OBSERVED: the number of micro-steps one full lot of get_batch_fact_aligned produced, "
            "asserted equal to len(distinct fact indices the loader returned) and to n_facts"
        ),
    }
```

Every measured figure has a sibling `*_formula` / `*_denominator` / `*_source` string. ADVT-03's
per-arm row needs the same: `scored_tokens`, `scored_tokens_denominator`, `adversarial_ratio`,
`adversarial_episodes`, `multiplicity` (Phase 25 SC3: multiplicity travels in the same sentence).

**Reader-side analog** — `tests/test_phase23_budget.py:359-380`, one small parser per record and no
test spelling the path twice:

```python
def _cost_record():
    """The committed cost record, parsed. `_control_record`'s sibling, same resolution rule."""
    path = _ROOT / phase23_prereg.COST_RECORD
    return path, json.loads(path.read_text(encoding="utf-8"))
```

Path resolved from the owning module's constant (`phase23_prereg.COST_RECORD`, itself declared at
`scripts/phase23_prereg.py:78`), never a test-local literal. This is the direct answer to the
"GSD plans misname artifacts" failure mode.

---

### 7. `scripts/mitigation_budget.py` — where D-09's grid lands

**Analog:** `SWEEP_POINTS` at `:374` + `SWEEP_POINTS_PROVENANCE` at `:376-403`:

```python
SWEEP_POINTS = 16

SWEEP_POINTS_PROVENANCE = {
    "record": "results/phase23_cost.json",
    "record_sha256": "f3ba4d9a02f3040752d93c0395821075d8450860a9bae194ac120e8db8a47637",
    "git_sha": "8876b8ce30427e08281f44b96a6a525dfd539a84",
    "derivation": "phase23_cost.size_sweep",
    "sized_against": "h_per_point_ceiling",
    "selected_by": "THE USER, at plan 23-13 Task 1's blocking `checkpoint:decision` gate — ...",
    "selected_value": 16,
    "selected_reply_verbatim": "...",
    "governs": "the number of FRONTIER POINTS PER LEG ... It is a RESOURCE parameter: it sizes "
               "the spend and decides no outcome. ...",
}
```

Each constant is preceded by a five-line `input / rule / output / evidence` comment block
(`:360-374` is the instance).

**TWO HARD LANDMINES, both verified at `tests/test_phase23_budget.py:430-490`:**

1. **`ast.literal_eval(node.value)` is called on every assignment** (`:463`). A value like
   `336 / 176` is an `ast.BinOp` and **raises** — the guard goes RED. D-09's `1.909` must be a
   **float literal** at the precision it will be used at (`336/176 = 1.9090909090909092`), with the
   derivation living in the comment block, never in code.
2. **Zero imports, zero functions, zero branches** — `forbidden` at `:466-477` bans `Import`,
   `ImportFrom`, `FunctionDef`, `ClassDef`, `If`, `For`, `While`, `With`, `Try`. The module
   docstring `:35-42` calls the import ceiling *"a HARD CEILING ... with ZERO HEADROOM"*: the
   allow-set across all `scripts/mitigation_*.py` is already exactly `{pathlib, sys, erasure_gate}`.
   **One `import math` here turns a committed guard RED.**

So D-09's grid is a **tuple literal** plus a **dict literal**, e.g.
`ADVERSARIAL_RATIO_GRID = (0.0, ..., 1.9090909090909092)` and
`ADVERSARIAL_RATIO_GRID_PROVENANCE = {...}` — and nothing else.

The module also opens with a `DATED CONTINUATION` in its own docstring (`:11-14`) rather than an
edit, which is the in-file version of the D-13 pattern:

```
CONTINUED 2026-08-27 (plan 23-18): that is now TWO numbers. ``MATCHED_CONTROL_NOISE_FLOOR`` below
pins the SAME quantity over the PROTOCOL-MATCHED comparator ... The
sentence above is left verbatim because it was true when it was written; this line is what stops it
going stale.
```

---

## Shared Patterns

### `contains_refusal`'s exact mirror
**Source:** `scripts/phase14_recall.py:279-311`
**Apply to:** the D-04 frame column and the D-11 filler probe.

```python
def normalize(text):
    """D-10's scoring normalizer: lowercase -> ``detokenize`` -> collapse whitespace -> strip edges."""
    return _EDGE_PUNCT_RE.sub("", _WHITESPACE_RE.sub(" ", detokenize(text.lower())).strip())


def contains_value(completion, value):
    """D-10's gate: case-insensitive, whitespace-collapsed substring containment. The boundary."""
    return normalize(value) in normalize(completion)


def score_question(completions, value):
    """``(k, n)`` — the number of completions containing the value, out of how many were drawn."""
    return sum(contains_value(c, value) for c in completions), len(completions)
```

`contains_refusal(completion, templates)` is `any(normalize(t) in normalize(completion) for t in
templates)` — same normalizer, same direction, same module. **Do not re-derive `normalize`**: its
docstring `:290-296` explains it already duplicates `phase14_factset.normalize_for_match` once, on
purpose, and `test_normalizer_agrees_with_the_gate_normalizer` pins the two. A third copy has no
such pin. The `(k, n)` return shape of `score_question` is the rate-reporting precedent for the
refusal-rate column.

### `SystemExit` at the build boundary, naming the file and the fix
**Source:** `scripts/teach_persona.py:370-410` (`refuse_if_exists`), `:528-556`, `:751-809`
**Apply to:** every new guard in `teach_persona.py` and the refusal module.

Every refusal in this codebase (a) raises `SystemExit`, never a bare exception, (b) prefixes
`[teach_persona] `, (c) names the offending object and the operator's next action, and (d) states
the invariant in the message so a red build is self-explaining. `refuse_if_exists`' docstring
`:376-404` is also the precedent for **widening a helper instead of branching at call sites**
("two copies of a guard drift") — relevant if `adversarial_ratio` needs its own ambiguity refusal
alongside `_refuse_ambiguous_aligned_input` (`:560`).

### Additive-seam discipline
**Sources:** `build_bins` docstring `:479-484`; `build_arm_bins` docstring `:962-982`
**Apply to:** every Phase 24 kwarg.

Stated in both docstrings in the same form: *"When it is `None` this function is BYTE-IDENTICAL to
v2.0, which is asserted against `tests/fixtures/golden_build_bins_v2` rather than argued"* and
*"``resume_from`` is ``None`` for every non-resuming caller and then this function is
BYTE-IDENTICAL to before"*. Write the claim into the docstring, and name the test that proves it.

### Records read from the owning module's path constant
**Sources:** `scripts/phase18_extraction.py:697`, `scripts/phase23_prereg.py:78`,
`scripts/phase21_unit_record.py:168-172`
**Apply to:** every new results file and every test that reads one.

---

## No Analog Found

| Item | Role | Data flow | Reason |
|---|---|---|---|
| The D-08 seed-derived interleave permutation | utility | transform | No shuffle/permutation of episode order exists anywhere in `build_bins`. `_prepend_replay` only does `list.insert(0, ...)`. The nearest constraint (not a pattern) is `seed_everything(seed)` at `scripts/teach_persona.py:1002` plus the determinism tuple in the resume raise at `:1057-1059`. **Use RESEARCH.md** — and derive the permutation from `seed` explicitly (`np.random.default_rng(seed)` or `random.Random(seed)`), never from the ambient global RNG state, which by that point has already been consumed by tokenizer load and rendering. |
| Attack **prompt_ids → (question, answer) text** conversion | adapter | transform | `build_bins` consumes text pairs and re-encodes via `encode_dialogue` (`:487`); `results/phase18_corpus.json` carries `prompt_ids` (ints) from `build_recall_prompt`. **No existing code turns a corpus `prompt_ids` row back into a training episode.** The A2 exclusion (D-10) means the ids-vs-text seam only matters for A1/A3, whose prompts are pure text transforms of a question — but the planner must decide explicitly whether to re-render from the family's question text or to decode the ids, and the two are not guaranteed byte-equal through `detokenize`. |
| A refusal-style **answer** anywhere in the repo | data | n/a | Confirmed in CONTEXT's own measurements: every `refuse`/`decline` hit is a script refusing to overwrite a file. The refusal *text* is genuinely new; only its *table shape* has an analog (§1). |

---

## Line-Number Corrections vs CONTEXT.md

The planner should carry these numbers, not CONTEXT's:

| Anchor | CONTEXT.md says | Verified at HEAD | Note |
|---|---|---|---|
| `scripts/phase18_extraction.py` `injection_budget` | `:580` | **`:565`** | `def injection_budget(value_ids):` |
| `src/personacore/dialogue/serialize.py` `build_recall_prompt` | `:93` | **`:92`** | off by one (`:93` is the docstring's first line) |
| `scripts/phase14_recall.py` `contains_value` | `:300` | **`:300`** | correct |
| `scripts/phase18_extraction.py` `build_a2_prompt` | `:640` / `:653` | **`:640` def, `:653` the return** | both citations are right, for different things |
| `tests/test_phase14_scoring.py` `embedded_fact_values` | `:367` (canonical_refs) | **`:349` helper, `:367` test** | canonical_refs conflates the two; the orchestrator's split is the correct one |
| `scripts/phase21_filler.py` "8 scored + 56 unscored" | `:8,395` | **`:8` the phrase, `:395` the "never scored / never in the 10-value lexicon" claim** | two different claims, both real |
| `scripts/teach_persona.py` `_slot_forms_for` merge | `:437-449` | **`:437` clash, `:444` widened, `:445-451` undeclared** | correct; function starts `:412` |

Unchanged and re-verified: `teach_persona.py` `:127` band, `:270` `DP_ARMS`, `:467` `build_bins`,
`:487` hardcoded `[]` persona, `:528` `_prove_floor_and_band`, `:609` `_build_aligned_bins`,
`:751` `_prepend_replay`, `:790` `replay_window_budget` region (`def` at `:181`; `:790` is inside
`_prepend_replay`'s v4.0 branch), `:965-968` packer-by-arm-name, `:1005` `aligned = arm in DP_ARMS`;
`serialize.py:61` `encode_dialogue`, `:81-82` persona at mask=0, `:88` final eos mask=1;
`phase14_factset.py:424-425,429,446` lexicon, `:519` reserved ban, `:694-695` F4/F5;
`phase18_extraction.py:117` `INJECTION_FRACTION`, `:474` `apply_a1`, `:506` `A3_ROLE_INSTRUCTION`,
`:545` `build_a3_prompt`; `test_phase14_scoring.py:422` allowlist, `:557` hard equality;
`test_phase18_corpus.py:538`; `test_phase21_replay_volume.py:260`.

---

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `src/personacore/dialogue/`, `results/`,
`.planning/ROADMAP.md`
**Files read this session:** 14 (`teach_persona.py`, `phase21_filler.py`, `phase14_factset.py`,
`phase14_recall.py`, `phase18_extraction.py` (grep only — read-only import source),
`mitigation_budget.py`, `phase21_unit_record.py`, `serialize.py`,
`test_phase21_aligned_bins.py`, `test_phase14_scoring.py`, `test_phase18_corpus.py`,
`test_phase23_budget.py`, `test_phase23_cost.py`, `test_phase23_resume.py`)
**Read-only constraint honoured:** `scripts/phase18_extraction.py` and `scripts/mitigation_gate.py`
were never opened for edit and are mapped as import sources only.
**Pattern extraction date:** 2026-08-30
