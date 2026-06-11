# Phase 2: From-Scratch BPE Tokenizer - Pattern Map

**Mapped:** 2026-06-04
**Files analyzed:** 15 (5 new package modules, 1 new script, 7 new/updated tests, 2 fixtures, 2 dependency-manifest edits, 1 config edit)
**Analogs found:** 15 / 15 (all have a Phase-1 analog in this same codebase)

> Every new file maps to a Phase-1 shipped module that already established the project's
> conventions (module docstring header citing the requirement/decision id, dataclass config,
> open-dict schema-versioned serialization, CPU-only GPU-free tests, thin no-logic scripts).
> The from-scratch ethos and offline/zero-budget intent are already encoded in those files —
> the planner should mirror them, not reinvent them.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/tokenizer/__init__.py` | package-init | — | `src/personacore/__init__.py` | role-match |
| `src/personacore/tokenizer/patterns.py` | config/constant | transform | `src/personacore/config.py` (module-constant style) | role-match |
| `src/personacore/tokenizer/special.py` | registry/config | transform | `src/personacore/config.py` (dataclass/registry) | role-match |
| `src/personacore/tokenizer/bpe.py` | core algorithm (train/encode/decode) | transform | `src/personacore/checkpoint.py` (stateful object + schema) / `seeding.py` (deterministic primitive) | role-match |
| `src/personacore/tokenizer/io.py` | serialization (save/load) | file-I/O | `src/personacore/checkpoint.py` (`save_checkpoint`/`load_checkpoint`, schema-versioned) | exact |
| `src/personacore/config.py` (MODIFY) | config | — | itself (`ModelConfig`) | exact (in-place edit) |
| `scripts/train_tokenizer.py` | entry-point script | batch (one-time) | `scripts/preflight_demo.py` | exact |
| `tests/test_tokenizer_train.py` | test (determinism) | transform | `tests/test_seeding.py` (determinism via repeat-and-compare) | exact |
| `tests/test_tokenizer_roundtrip.py` | test (round-trip) | transform | `tests/test_checkpoint.py::test_resume_identical_trajectory` (round-trip equality) | role-match |
| `tests/test_tokenizer_special.py` | test (atomicity + config) | transform | `tests/test_config.py` + `tests/test_checkpoint.py` | role-match |
| `tests/test_tokenizer_io.py` | test (freeze/load) | file-I/O | `tests/test_checkpoint.py::test_open_dict_extensible` (save→load→assert, `tmp_path`) | exact |
| `tests/test_tokenizer_oracle.py` | test (equivalence + import guard) | transform | `tests/test_checkpoint.py::test_git_sha_fallback` (monkeypatch/skip) | role-match |
| `tests/test_config.py` (MODIFY) | test | — | itself | exact (in-place edit) |
| `tests/fixtures/tricky_strings.py` | test-fixture data | — | `tests/conftest.py` (fixture conventions) | partial |
| `tests/fixtures/tiny_corpus.txt` | test-fixture data | — | (none — first committed corpus fixture) | no analog |
| `pyproject.toml` + `requirements.txt` (MODIFY) | dependency manifest | — | itself | exact (in-place edit) |

## Pattern Assignments

### `src/personacore/tokenizer/__init__.py` (package-init)

**Analog:** `src/personacore/__init__.py` (lines 1-5)

**Pattern — one-line module docstring + explicit `__all__`:**
```python
"""PersonaCore: a from-scratch, on-device conversational AI whose memory lives in the weights."""

__version__ = "0.1.0"

__all__ = ["__version__"]
```
Mirror this: a one-line package docstring, then re-export the public surface
(`BPETokenizer`, `GPT2_SPLIT_PATTERN`, `SPECIAL_TOKENS`, `EOS_TOKEN`) and set `__all__`.
This is the import surface Phases 3/5/6 depend on (RESEARCH "Recommended Project Structure").

---

### `src/personacore/tokenizer/patterns.py` (config/constant, transform)

**Analog:** `src/personacore/config.py` — module-level constant + rich docstring style.

**Pattern — module constant with citation comment** (the project comments WHY a value is what it is, with a source/decision id; see `config.py` line 72 `# placeholder — locked by Phase 2.`):
```python
import regex  # NOT stdlib re — \p{L}/\p{N} require the regex library (RESEARCH: D-05)

# Source: github.com/karpathy/minbpe regex.py + tiktoken gpt2 pat_str  [CITED in RESEARCH]
GPT2_SPLIT_PATTERN = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
_COMPILED = regex.compile(GPT2_SPLIT_PATTERN)
```
**Convention to copy:** every load-bearing constant gets a `# Source:`/`# RESEARCH: D-xx`
comment, exactly like Phase-1 modules annotate Pascal/decision rationale inline.

---

### `src/personacore/tokenizer/special.py` (registry/config, transform)

**Analog:** `src/personacore/config.py` (`ModelConfig`, lines 64-77) — the dataclass/registry that owns ids.

**Pattern — fixed, documented id layout as a module constant** (parallels `ModelConfig.vocab_size` ownership). Use the RESEARCH-recommended top-pinned layout (`8184–8191`, EOS=`8184`, Pitfall 5):
```python
# Specials pinned at the TOP of the 8192 vocab (ids 8184-8191); bytes=0-255, merges=256-8183.
# Locked here (D-02/D-03a): set + count (8) are frozen; EOS is the single shared id.
EOS_TOKEN = "<|endoftext|>"
SPECIAL_TOKENS = {           # name -> id, ordered, fixed
    "<|endoftext|>": 8184,
    "<|user|>": 8185,
    # ... <|assistant|> <|system|> <|pad|> <|reserved_0..2|>
}
EOS_ID = SPECIAL_TOKENS[EOS_TOKEN]   # mirrored into ModelConfig.eos_id (Phase-1 D-03)
```
**Convention to copy:** values that downstream phases lock onto are constants with a comment
naming the decision id — same discipline as `config.py`'s `vocab_size` placeholder comment.

---

### `src/personacore/tokenizer/bpe.py` (core algorithm, transform)

**Analogs:** `src/personacore/seeding.py` (deterministic primitive) + `src/personacore/checkpoint.py` (stateful object that travels with an embedded config/schema).

**Module-docstring header pattern** — every Phase-1 module opens with a docstring that states
the requirement id, the load-bearing property, and the key pitfall it guards. Copy this shape
(see `seeding.py` lines 1-15, `checkpoint.py` lines 1-21):
```python
"""From-scratch byte-level BPE tokenizer (TOK-01/TOK-02/TOK-03).

Train merges from a bounded corpus and replay them deterministically (lowest-rank-first),
producing identical IDs across runs/sessions (TOK-01). Byte-level base-256 guarantees no
<unk> ever and exact decode(encode(x)) round-trip (TOK-02). Special tokens are atomic —
split FIRST, never merged across (TOK-03 / Pitfall 3).

The from-scratch deliverable is the BPE ALGORITHM; `regex` is a pre-tok primitive on the
same footing as stdlib `re` (RESEARCH "Don't Hand-Roll"). tiktoken NEVER imported here.
"""
```

**Determinism pattern** — reuse the `seeding.py` discipline; the train loop's pair-selection
must be totally ordered to satisfy TOK-01 (RESEARCH Pitfall 1):
```python
# get_stats / merge are pure from-scratch primitives (RESEARCH Pattern 2).
# Tie-break must be TOTAL to be deterministic across runs (Pitfall 1):
pair = max(stats, key=lambda p: (stats[p], p))   # freq, then pair-key — never bare stats.get
# encode replay (RESEARCH Pattern 3): lowest-rank-first
pair = min(stats, key=lambda p: self.merges.get(p, float("inf")))
```

**Stateful-object + `frozen()` classmethod pattern** — `io.from_json` constructs a frozen
`BPETokenizer.frozen(...)`; mirror how `load_checkpoint` rebuilds full state from a dict
(`checkpoint.py` lines 73-97). Expose `vocab_size`, `encode`, `decode`, `eos_id` (TOK-04).

---

### `src/personacore/tokenizer/io.py` (serialization, file-I/O)

**Analog (EXACT):** `src/personacore/checkpoint.py` — `save_checkpoint`/`load_checkpoint` with `CKPT_SCHEMA_VERSION` and asserted schema on load.

**Schema-version constant + symmetric save/load** (copy `checkpoint.py` lines 29, 51-52, and the security note lines 16-21 — JSON not pickle here):
```python
import json

SCHEMA_VERSION = 1     # parallels CKPT_SCHEMA_VERSION in checkpoint.py

def save_json(tok, path):
    payload = {
        "schema_version": SCHEMA_VERSION,        # asserted on load (mirror checkpoint.py)
        "pattern": tok.pattern,
        "vocab_size": tok.vocab_size,            # 8192 LOCKED
        "special_tokens": tok.special_tokens,
        "eos_id": tok.eos_id,
        # JSON has no tuple keys -> merges as [p0,p1,idx] triples in RANK order
        "merges": [[p0, p1, idx] for (p0, p1), idx in sorted(tok.merges.items(), key=lambda kv: kv[1])],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=0)

def from_json(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    assert d["schema_version"] == SCHEMA_VERSION, "tokenizer schema mismatch"   # like checkpoint.py
    merges = {(p0, p1): idx for p0, p1, idx in d["merges"]}
    return BPETokenizer.frozen(pattern=d["pattern"], merges=merges, ...)
```
**Critical divergence from analog:** `checkpoint.py` uses `torch.save`/`torch.load` (pickle,
trusted-only). The tokenizer artifact MUST use stdlib `json` — never `pickle`/`torch.load`
(RESEARCH Security: data-only, no code execution; validate ids in `[0, vocab_size)`).

---

### `src/personacore/config.py` (MODIFY — config)

**Analog (EXACT, in-place):** the existing `ModelConfig` (lines 64-77).

**Edit:** lock `vocab_size` and add `eos_id` (RESEARCH "config.py deltas"; Phase-1 D-03 — config travels in checkpoint via `asdict` in `checkpoint.py` line 58):
```python
@dataclass
class ModelConfig:
    vocab_size: int = 8192          # LOCKED by Phase 2 (was 50304 placeholder, line 72)
    eos_id: int = 8184              # shared EOS id, recorded in checkpoint (Phase-1 D-03)
    block_size: int = 256
    # ... rest unchanged
```
Keep the existing inline-comment convention (the old line 72 comment `# placeholder — locked
by Phase 2.` becomes `# LOCKED by Phase 2`). `eos_id` flows into the checkpoint automatically
because `save_checkpoint` already `asdict`s `model_config` (no checkpoint change needed).

---

### `scripts/train_tokenizer.py` (entry-point script, batch)

**Analog (EXACT):** `scripts/preflight_demo.py` — thin entry that wires package primitives with NO logic of its own.

**Pattern — no-logic, no-CLI `main()`** (copy the docstring intent + `if __name__` shape; Phase-1 D-04: no argparse, defaults/kwargs only):
```python
"""Thin one-time entry: load bounded corpus -> train 8192-vocab BPE -> freeze artifact.

Logic lives in src/personacore/tokenizer/ (mirrors preflight_demo.py). No CLI/argparse
(D-04) — paths and hyperparameters are module constants / kwargs.
"""
from personacore.tokenizer.bpe import BPETokenizer
from personacore.tokenizer.io import save_json
from personacore.seeding import seed_everything   # reuse Phase-1 determinism

CORPUS_PATH = "..."          # path-convention constant, like preflight_demo's CHECKPOINT_DIR
ARTIFACT_PATH = "..."

def main() -> None:
    seed_everything(1337)
    tok = BPETokenizer(...).train(open(CORPUS_PATH).read(), vocab_size=8192)
    save_json(tok, ARTIFACT_PATH)

if __name__ == "__main__":
    main()
```

---

### `tests/test_tokenizer_train.py` (test — determinism)

**Analog (EXACT):** `tests/test_seeding.py` — the "run twice, assert identical" determinism shape (`test_determinism`, lines 19-25).

**Pattern — train-twice-assert-identical** (mirror `test_seeding.py`'s repeat-and-compare; TOK-01 / Pitfall 1):
```python
def test_train_deterministic():
    a = BPETokenizer(...).train(CORPUS, vocab_size=512)
    b = BPETokenizer(...).train(CORPUS, vocab_size=512)
    assert a.merges == b.merges          # identical merge order/ids across runs (TOK-01)
```
Copy the test module-docstring header convention (`test_seeding.py` lines 1-3: cites the
requirement id and asserts "All tests are CPU-only and GPU-free so CI runs them").

---

### `tests/test_tokenizer_roundtrip.py` (test — round-trip)

**Analog:** `tests/test_checkpoint.py::test_resume_identical_trajectory` (lines 47-84) — round-trip/equality assertion structure.

**Pattern — parametrize over the tricky-string fixture, assert exact equality** (TOK-02):
```python
import pytest
from tests.fixtures.tricky_strings import TRICKY_STRINGS

@pytest.mark.parametrize("s", TRICKY_STRINGS)
def test_roundtrip_exact(tok, s):
    assert tok.decode(tok.encode(s)) == s          # no <unk> ever (TOK-02)

def test_chunk_join_invariant(tok):
    # "".join(chunks) MUST equal text.encode (RESEARCH Pitfall 6 — never strip/normalize)
    ...
```

---

### `tests/test_tokenizer_special.py` (test — atomicity + config)

**Analogs:** `tests/test_config.py` (config assertion) + `tests/test_checkpoint.py` (round-trip).

**Pattern — config assertion** (copy `test_config.py::test_configs_are_dataclasses`, lines 36-46):
```python
from personacore.config import ModelConfig
def test_eos_id_in_config():
    assert ModelConfig().eos_id == 8184          # TOK-03 / Phase-1 D-03
    assert ModelConfig().vocab_size == 8192
```
**Pattern — atomicity:** `encode("a<|endoftext|>b")` yields exactly one EOS id, never byte-split (RESEARCH Pattern 4 / Pitfall 3).

---

### `tests/test_tokenizer_io.py` (test — freeze/load)

**Analog (EXACT):** `tests/test_checkpoint.py::test_open_dict_extensible` (lines 87-108) — `tmp_path` save→load→assert.

**Pattern — save to `tmp_path`, reload, assert behavioral identity + schema + locked vocab** (TOK-04; mirror checkpoint's `tmp_path` + schema_version assertion):
```python
def test_freeze_reload_identical(tmp_path, tok):
    p = tmp_path / "tokenizer.json"
    save_json(tok, p)
    loaded = from_json(p)
    assert loaded.vocab_size == 8192
    for s in SOME_STRINGS:
        assert loaded.encode(s) == tok.encode(s)     # behavior survives the round-trip
```

---

### `tests/test_tokenizer_oracle.py` (test — equivalence + import guard)

**Analog:** `tests/test_checkpoint.py::test_git_sha_fallback` (lines 133-139) — `monkeypatch` + graceful-degradation pattern; adapt to `pytest.skip`.

**Pattern — skip-on-offline oracle** (RESEARCH Pitfall 2):
```python
import pytest
def test_tiktoken_gpt2_equivalence():
    try:
        import tiktoken
        enc = tiktoken.get_encoding("gpt2")      # network on first use
    except Exception:
        pytest.skip("tiktoken gpt2 unavailable offline")
    # recover_merges(enc._mergeable_ranks) -> inject -> assert exact id match (RESEARCH Pattern 6)
```
**Pattern — runtime import guard** (RESEARCH Pitfall 4) — scan `src/personacore/**/*.py` for
`tiktoken` and assert none import it, keeping tiktoken `[dev]`-only:
```python
def test_no_runtime_tiktoken():
    import pathlib
    for f in pathlib.Path("src/personacore").rglob("*.py"):
        assert "tiktoken" not in f.read_text()
```

---

### `tests/test_config.py` (MODIFY — test)

**Analog (EXACT, in-place):** itself (lines 36-46).

**Edit:** extend `test_configs_are_dataclasses` (or add a test) to assert `ModelConfig().vocab_size == 8192` and `hasattr(model, "eos_id")` (RESEARCH Test Map row D-01).

---

### `tests/fixtures/tricky_strings.py` (test-fixture data)

**Analog:** `tests/conftest.py` (fixture-module conventions) — partial; this is a plain data module, not a `@pytest.fixture`.

**Content** (RESEARCH "Tricky-string fixture set"): a `TRICKY_STRINGS = [...]` list covering leading-space ASCII, smart quotes/em-dash, emoji (ZWJ + flags), multi-byte scripts, whitespace runs, digits+punctuation, the embedded `<|endoftext|>` literal, empty + single byte.

---

### `tests/fixtures/tiny_corpus.txt` (test-fixture data)

**No analog** — first committed corpus fixture in the repo. A small (~few-hundred-KB) committed
TinyStories slice for offline train tests (RESEARCH Alternatives + D-09). Keeps CI fully offline.

## Shared Patterns

### Module-docstring header (cite requirement/decision id + load-bearing property + pitfall)
**Source:** every Phase-1 module — e.g. `src/personacore/checkpoint.py` lines 1-21, `seeding.py` lines 1-15, `config.py` lines 1-13.
**Apply to:** ALL new `tokenizer/` modules, the script, and every test file.
Each docstring names the requirement id (`TOK-0x`), states the one load-bearing invariant,
and flags the relevant RESEARCH pitfall. This is the strongest, most consistent convention
in the codebase.

### Schema-versioned serialization (constant + asserted-on-load)
**Source:** `src/personacore/checkpoint.py` line 29 (`CKPT_SCHEMA_VERSION = 1`) + line 52 (written) + load-side assert.
**Apply to:** `tokenizer/io.py` (`SCHEMA_VERSION = 1`, written into the JSON, asserted in `from_json`).
**Divergence:** tokenizer uses stdlib `json` (data-only, safe), NOT `torch.save`/pickle.

### Inline decision/source comments on load-bearing values
**Source:** `config.py` line 72 (`# placeholder — locked by Phase 2.`), `checkpoint.py` line 58 (`# config travels WITH weights (QA-02)`).
**Apply to:** `patterns.py` (regex source), `special.py` (id layout + D-02/D-03a), `config.py` edit (vocab/eos comment).

### CPU-only, GPU-free, offline tests
**Source:** `tests/test_config.py` line 4, `tests/test_seeding.py` line 3 (explicit "All tests are CPU-only and GPU-free so CI runs them").
**Apply to:** every `test_tokenizer_*.py`. Oracle test additionally skips-on-offline so CI stays green (Phase-1 CPU-only-offline CI contract).

### Determinism via repeat-and-compare + `tmp_path` for file round-trips
**Source:** `tests/test_seeding.py::test_determinism` (lines 19-25); `tests/test_checkpoint.py` uses `tmp_path` (lines 47, 62, 91).
**Apply to:** `test_tokenizer_train.py` (train twice → identical), `test_tokenizer_io.py` (`tmp_path` save/load).

### Thin no-logic, no-CLI scripts (logic lives in the package)
**Source:** `scripts/preflight_demo.py` (lines 1-37) + Phase-1 D-04.
**Apply to:** `scripts/train_tokenizer.py` — `main()` + `if __name__ == "__main__"`, path constants, no argparse.

### Makefile lint/test gate + dependency-manifest dual maintenance
**Source:** `Makefile` (lint = `ruff check . && ruff format --check .`; test = `pytest -q`); `pyproject.toml` ↔ `requirements.txt` kept consistent (Phase-1 D-09).
**Apply to:** add `regex` to BOTH `pyproject.toml` `dependencies` AND `requirements.txt`; add `tiktoken~=0.13` to the `[dev]` extra ONLY. All new code must pass `make lint` (ruff `E/F/W/I`, line-length 100).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/fixtures/tiny_corpus.txt` | test-fixture data | — | First committed text corpus fixture; no prior data-file precedent in the repo. Follow RESEARCH D-09 (small offline slice). |
| `artifacts/tokenizer.json` (produced, committed) | filesystem artifact | file-I/O | No committed JSON artifact exists yet. Generated by `scripts/train_tokenizer.py`; schema defined by `io.py` (analog: checkpoint's open-dict schema, but JSON). |

> Note: there is NO new-tech file lacking a *pattern* analog — `bpe.py`'s algorithm is novel
> to the repo, but its module-shape, determinism, and stateful-object conventions are all
> covered by `seeding.py` + `checkpoint.py`. The RESEARCH "Architecture Patterns" section
> (Patterns 1-6, quoted from minbpe) supplies the algorithm body the planner should follow.

## Metadata

**Analog search scope:** `src/personacore/` (6 modules), `tests/` (7 test files + conftest), `scripts/` (1), `pyproject.toml`, `requirements.txt`, `Makefile`.
**Files scanned:** 17 (all of Phase-1's shipped surface — this is a small, single-package repo).
**Pattern extraction date:** 2026-06-04
