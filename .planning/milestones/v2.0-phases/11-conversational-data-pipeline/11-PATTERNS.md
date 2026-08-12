# Phase 11: Conversational Data Pipeline - Pattern Map

**Mapped:** 2026-07-31
**Files analyzed:** 13 new/modified files
**Analogs found:** 11 / 13 (2 are doc-only edits with no code analog needed)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/personacore/dialogue/__init__.py` | package init | — | `src/personacore/continual/__init__.py` | exact |
| `src/personacore/dialogue/parse.py` | utility (parser) | file-I/O / transform | `scripts/encode_corpus.py::_iter_documents` (streaming doc iterator) | role-match; RESEARCH Pattern 2 gives the executable-grade code |
| `src/personacore/dialogue/serialize.py` | utility (detok + render + mask) | transform | `scripts/encode_corpus.py::encode_to_bin` + `src/personacore/tokenizer/special.py` | role-match; RESEARCH Pattern 3 gives the mask construction |
| `src/personacore/dialogue/inflation.py` | utility (metrics) | batch/transform | `src/personacore/evaluation/perplexity.py` | role-match (auditable-denominator metrics module) |
| `src/personacore/training/data.py` (+`get_batch_memmap_masked`) | utility (batch sampler) | file-I/O (memmap draw) | `get_batch_memmap` in the SAME file, lines 73–90 | exact |
| `scripts/fetch_personachat.py` | script (run-once) | file-I/O (network fetch) | thin-script shell of `scripts/encode_corpus.py`; fetch body from RESEARCH Pattern 1 | role-match (no existing fetch script — v1.0 corpus was manually downloaded) |
| `scripts/measure_inflation.py` | script (run-once gate) | batch (measure + report) | `scripts/estimate_fisher_tinystories.py` | exact (thin driver, package logic, evidence-over-assertion) |
| `scripts/prepare_dialog_corpus.py` | script (run-once encode) | file-I/O (raw→bin) | `scripts/encode_corpus.py` | exact |
| `tests/test_dialogue_parse.py` (+ committed fb fixture) | test | — | `tests/test_data_split.py` (committed-fixture style) | exact |
| `tests/test_dialogue_serialize.py` | test | — | `tests/test_tokenizer_special.py` (atomicity/round-trip) | exact |
| `tests/test_masked_batch.py` | test | — | `tests/test_memmap_data.py` (tmp_path bins, exactness) | exact |
| `results/inflation_report.md` | committed artifact | — | `results/results.md` | exact |
| `.planning/REQUIREMENTS.md` + `.planning/ROADMAP.md` (D-00 wording edit) | docs | — | n/a | n/a |

## Pattern Assignments

### `src/personacore/training/data.py` — add `get_batch_memmap_masked` (utility, memmap draw)

**Analog:** `get_batch_memmap` in the same file — copy verbatim, add 3 lines. This is the single most load-bearing pattern in the phase.

**Core pattern** (`src/personacore/training/data.py` lines 73–90):
```python
def get_batch_memmap(bin_path, batch_size, block_size, device):
    """... re-opened every call: a long-lived memmap accumulates RSS across thousands of
    training steps (nanoGPT leak — Pitfall 1), so it is opened fresh and discarded per batch.
    Plain ``.to(device)`` only — the CUDA-only pinned-host / async-copy transfer flags have
    no MPS/CPU path this phase, so they are deliberately absent."""
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)
```

**Delta to add** (RESEARCH Pattern 4, already reviewed against this idiom): second `np.memmap` for the uint8 mask, `assert len(data) == len(mask)`, an `m` stack drawn with the SAME `i + 1 : i + 1 + block_size` slice as `y`, then `y[m == 0] = -100`. Keep: same `len - block_size - 1` bound, same fresh-memmap-per-call, same uint16→int64 cast, same docstring discipline (cite Pitfall 1 leak avoidance and the shared-`+1`-slice target-space shift).

**Imports pattern** (lines 15–18): `numpy as np`, `torch`, `from personacore.tokenizer import from_json` — module-level `TOKENIZER_PATH = "artifacts/tokenizer.json"` constant.

---

### `scripts/prepare_dialog_corpus.py` (script, raw→bin encode)

**Analog:** `scripts/encode_corpus.py` — the dialogue sibling, mirror its whole shape.

**Thin no-CLI script shell** (lines 25–40): module docstring stating run-once discipline + "Run manually AFTER …" + "NOT part of automated verification"; then:
```python
import pathlib

import numpy as np

from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
...
EOS_ID = 8184  # ModelConfig.eos_id
```
…and at the bottom (lines 102–112) a `main()` with `[encode_corpus]`-prefixed prints and `if __name__ == "__main__": main()`. **No argparse** (locked house pattern).

**Frozen-tokenizer + shard-accumulate + tofile pattern** (lines 75–90):
```python
tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
...
shards = []
for doc in docs:
    ids = tok.encode(doc + _SEP, allowed_special="all")  # marker -> atomic eos 8184
    shards.append(np.asarray(ids, dtype=np.uint16))
arr = np.concatenate(shards) if shards else np.empty(0, dtype=np.uint16)
arr.tofile(bin_path)
```
Note for the dialogue version: RESEARCH Pattern 3 supersedes whole-document `allowed_special="all"` encoding — encode SPANS and append role-token ids literally (anti-pattern list forbids encode-whole-then-guess-boundaries). The shard/`tofile` mechanics and uint16 dtype copy over unchanged; write the mask shards as a parallel `np.uint8` array with the identical mechanics.

**Post-build sanity block** (lines 92–98) — extend for masks per RESEARCH Pattern 5:
```python
check = np.fromfile(bin_path, dtype=np.uint16)
eos_count = int(np.count_nonzero(check == EOS_ID))
assert eos_count >= 1, f"{bin_path} has no eos ({EOS_ID}) — corrupt/empty corpus?"
prefix = tok.decode(check[:200].astype(np.int64).tolist())
print(f"  {bin_path.name}: {len(check):,} tokens, {eos_count:,} docs (eos)")
```
Dialogue additions: assert eos count == episode count (8,939 train / 1,000 valid), token-bin length == mask-bin length, print masked-token fraction (expect ~45–55%).

**Optional tqdm pattern** (lines 77–82): `try: from tqdm import tqdm ... except ImportError:` — only used if importable.

---

### `scripts/fetch_personachat.py` (script, one-time network fetch)

**Analog:** no existing fetch script (v1.0 TinyStories was downloaded manually per CLAUDE.md). Use the `encode_corpus.py` thin-script shell above (`_REPO_ROOT` constants, `main()`, prefixed prints, no argparse) around RESEARCH Pattern 1's stdlib body:
```python
import hashlib, tarfile, urllib.request
URL = "https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz"
SHA256 = "507cf8641d333240654798870ea584d854ab5261071c5e3521c20d8fa41d5622"  # pinned 2026-07-31
# skip-if-exists (idempotent) → sha256 hard-fail on mismatch → tf.extract of the TWO named
# members only (path-traversal guard; never extractall)
```
Refuse-to-clobber / idempotency posture: copy the loud-exit style of `estimate_fisher_tinystories.py` lines 78–82 (`raise SystemExit("... already exists — refusing ...")`) for any destructive re-run; hard failures as `raise SystemExit`/`FileNotFoundError`, never bare `assert` (that script's `-O`-strippable-assert rule, lines 8–10). Destination `data/raw/` (gitignored, precious per D-00).

---

### `scripts/measure_inflation.py` + `results/inflation_report.md` (gate script + committed evidence)

**Analog:** `scripts/estimate_fisher_tinystories.py` — the house "measured claim, committed evidence" artifact (the N=2000 Fisher convergence stats CONTEXT explicitly names as the register to match).

**Thin-driver shell** (lines 48–56):
```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"   # path constants, named + commented
...
# --- Tuned constants (production estimation budget — prove the Fisher on real weights) ---
N_EXAMPLES = 2000  # D-04: measured < 1 min on MPS ...; convergence reported (D-05).
```

**Precondition-check pattern** (lines 66–74): `if not X.exists(): raise FileNotFoundError(f"Missing {X}. Run `python scripts/...` first.")` — fetch script must have run before the gate.

**Report-don't-gate pattern** (lines 164–170): convergence stats are PRINTED as evidence, not asserted — the inflation metrics likewise report numbers against the pre-registered D-09 bands and render a verdict rather than silently failing. `[measure_inflation]`-prefixed prints throughout.

**Report format analog:** `results/results.md` — committed markdown with a framing blockquote (what the numbers are/aren't comparable to), a metric table with auditable denominators ("2.8212 (over 12,636,922 tokens)"), and a `## Notes` section. The inflation report mirrors this: four D-08 metrics, the D-09 bands, the verdict, plus the TinyStories 2.864 baseline and 1.135× relative figure for the expected STOP escalation.

No `preflight_device`/torch needed here — the gate is tokenizer+text only; keep the shell, drop the device gate.

---

### `src/personacore/dialogue/__init__.py` (package init)

**Analog:** `src/personacore/continual/__init__.py` (whole file, 13 lines):
```python
"""Phase 10 — from-scratch EWC core (EWC-01..02): public import surface."""

from .ewc import EWCPenalty
from .fisher import estimate_fisher

__all__ = ["EWCPenalty", "estimate_fisher"]
```
Same shape: one-paragraph requirement-tagged docstring, relative imports, explicit `__all__`.

---

### `src/personacore/dialogue/parse.py` (parser, file-I/O)

**Analog (streaming/flush discipline):** `scripts/encode_corpus.py::_iter_documents` (lines 42–64) — line-streaming with a flush-at-boundary + content-bearing-tail check:
```python
buf = []
with open(txt_path, encoding="utf-8") as fh:
    for line in fh:
        ...
rest = "".join(buf)
if rest.strip():  # a final content-bearing document with no trailing separator
    yield rest
```
The fb-dialog parser body is RESEARCH Pattern 2 (executable-grade, verified on the full corpus): `num, _, rest = line.rstrip("\n").partition(" ")`, episode flush on `num == "1"`, `rest.split("\t")` with exactly 4 fields, flush-at-EOF. Stdlib only (from-scratch boundary). Docstring style: cite the verified corpus properties (8,939/1,000 episodes, 4-field invariant) the way `data.py` docstrings cite Pitfalls.

---

### `src/personacore/dialogue/serialize.py` (detok + render + mask, transform)

**Analogs:** `src/personacore/tokenizer/special.py` (id source) + RESEARCH Pattern 3 (span-wise encode).

**Special-token registry — never retype ids** (`special.py` lines 15–26):
```python
SPECIAL_TOKENS = {  # name -> id, ordered, top-pinned, fixed (Pitfall 5).
    "<|endoftext|>": 8184,
    "<|user|>": 8185,
    "<|assistant|>": 8186,
    "<|system|>": 8187,
    ...
}
EOS_ID = SPECIAL_TOKENS[EOS_TOKEN]
```
Import ids as `SPECIAL_TOKENS["<|user|>"]` etc. — the Don't-Hand-Roll table forbids new constants.

**Mask construction:** RESEARCH Pattern 3 verbatim (span-wise `emit(token_ids, m)`; first `<|user|>`=0, subsequent `<|user|>`=1, `<|assistant|>` trigger=0, reply=1, eos=1). One `render_document`/`encode_dialogue` function consumed by BOTH `measure_inflation.py` and `prepare_dialog_corpus.py` (Pitfall 4: gate and bins must tokenize identically). Content spans use plain `tok.encode(text)` — no `allowed_special` needed since `<|endoftext|>` never appears in the raw text (verified).

**Detokenizer:** plain `re` rules (D-06), no analog needed — fixture-test against real corpus lines (zero apostrophes; spaced punctuation; `!.` persona artifact) per Pitfall 3.

---

### `src/personacore/dialogue/inflation.py` (metrics, batch)

**Analog:** `src/personacore/evaluation/perplexity.py` — the house metrics-module shape: single pure function, exhaustive docstring pinning accounting invariants, returns the value WITH its auditable denominator (lines 43–46):
```python
    Returns:
        ``(ppl, total_tokens)`` where ``ppl = exp(total_CE / total_tokens)`` and
        ``total_tokens`` is the exact denominator (D-03) so the number is auditable.
```
Apply the same posture: each D-08 metric returned with its denominator (word counts, dialogue counts) so the committed report's numbers are auditable. One encode pass produces all four metrics (D-08). Torch not needed here — numpy/stdlib.

---

### `tests/test_masked_batch.py` (test — DATA-03 hand-built fixture)

**Analog:** `tests/test_memmap_data.py` — exact template: build tiny bins in `tmp_path`, assert exactness.

**Header + constants** (lines 21–31):
```python
import pathlib

import numpy as np
import torch

from personacore.tokenizer import from_json
from personacore.training.data import get_batch_memmap

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "tinystories_fixture.txt"
TOKENIZER_PATH = "artifacts/tokenizer.json"
EOS_ID = 8184
```

**tmp_path bin-building helper** (lines 47–60): encode → `np.asarray(ids, dtype=np.uint16)` → `arr.tofile(bin_path)` → return arr. For the mask test, hand-write BOTH arrays (ids AND mask) as literals per the RESEARCH DATA-03 fixture sketch — no tokenizer needed for the exactness test — write token bin as uint16 and mask bin as uint8 to `tmp_path`, then assert the FINAL `y` tensor (including `-100` placement at first-`<|user|>`/subsequent-`<|user|>`/eos edges) exactly.

**Shape/dtype/bounds assertions** (lines 88–104): `x.shape == (batch_size, block_size)`, `x.dtype == torch.int64`, `int(x.max()) < 8192` — copy for the masked variant, adding the exact-`y` comparison.

---

### `tests/test_dialogue_parse.py` (test — committed fixture)

**Analog:** `tests/test_data_split.py` — committed-fixture style.

**Pattern** (lines 13–34): fixture under `tests/fixtures/` (add a small fb-format fixture file with a few real-shaped episodes, sibling to `bigram_corpus.txt`/`tinystories_fixture.txt`); module docstring naming the requirement + "CPU-only, GPU-free"; per-test one-line comment stating the invariant:
```python
CORPUS_PATH = pathlib.Path(__file__).parent / "fixtures" / "bigram_corpus.txt"
...
def test_eos_marks_document_boundaries():
    # The fixture must encode with the atomic eos id 8184 at >=2 doc boundaries (Pitfall 6) —
    # this is the signal load_split partitions on.
```
Parse tests assert: episode count, persona-line extraction, 4-field turn split, last-episode flush (Pitfall 5), against the committed fixture.

---

### `tests/test_dialogue_serialize.py` (test — detok, render, atomic role tokens)

**Analog:** `tests/test_tokenizer_special.py` — atomicity + round-trip idiom (lines 35–44):
```python
def test_eos_is_atomic(tok):
    # encode("a<|endoftext|>b") yields EXACTLY one EOS id, never byte-split (atomicity).
    ids = tok.encode("a<|endoftext|>b")
    assert ids.count(EOS_ID) == 1

def test_eos_roundtrips(tok):
    # The special token survives decode(encode(...)) as the literal marker.
    s = "hello<|endoftext|>world"
    assert tok.decode(tok.encode(s)) == s
```
Same assertions for role ids 8185–8187 through the FROZEN `artifacts/tokenizer.json` (load via `from_json` like `test_data_split.py:26–27`, not a freshly trained tokenizer — the production registry is what matters here). Add: detok rules on real corpus lines, `render_document` output shape, and the deterministic inflation-metrics unit (`-k inflation`).

---

### `.planning/REQUIREMENTS.md` / `.planning/ROADMAP.md` (D-00 wording edit)

Doc-only: strike the DailyDialog clause from DATA-01 and Phase 11 criterion 1. No code analog; ride the phase's first commit per CONTEXT discretion.

## Shared Patterns

### Frozen tokenizer load
**Source:** `src/personacore/training/data.py:32`, `scripts/encode_corpus.py:75`
**Apply to:** serialize.py, inflation.py, prepare_dialog_corpus.py, all tokenizer-touching tests
```python
tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
```
`TOKENIZER_PATH` is `"artifacts/tokenizer.json"` in package/tests, `_REPO_ROOT / "artifacts" / "tokenizer.json"` in scripts.

### Thin no-CLI script shell
**Source:** `scripts/encode_corpus.py:25–40, 102–112`; `scripts/estimate_fisher_tinystories.py:48–56`
**Apply to:** all three new scripts
`_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent`, UPPER_CASE path constants with one-line comments, named tuned constants, `main()`, `[script_name]`-prefixed prints, `if __name__ == "__main__": main()`. NO argparse.

### Loud failures in run-once scripts
**Source:** `scripts/estimate_fisher_tinystories.py:66–82, 115–135`
**Apply to:** fetch_personachat.py, prepare_dialog_corpus.py, measure_inflation.py
Preconditions → `FileNotFoundError` with the remedy command; proof/sanity checks → `raise SystemExit("[proof x] ...")`, never a `-O`-strippable bare `assert`; refuse-to-clobber precious artifacts with a loud `SystemExit`.

### Docstring discipline
**Source:** every analog above
**Apply to:** all new files
Module docstring names the requirement id (DATA-01..04), the decision ids (D-01..D-10), and the Pitfall it guards against; function docstrings state the invariant being enforced, not just what the code does.

### Test posture
**Source:** `tests/test_memmap_data.py:16–19`, `tests/test_data_split.py:9–11`
**Apply to:** all three new test files
CPU-only, GPU/MPS-free; committed fixtures under `tests/fixtures/`; per-test invariant comments; "Do NOT weaken any assertion to make these pass early" register. Full suite (222 passed / 1 skipped) must stay green via `make test`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | Every code file has at least a role-match analog; the fetch script's network body has no precedent (v1.0 corpus was manually downloaded) but RESEARCH Pattern 1 provides verified, executable-grade code, and the script shell follows the house pattern. |

## Metadata

**Analog search scope:** `src/personacore/**`, `scripts/**`, `tests/**`, `results/**`
**Files read:** 9 (`training/data.py`, `scripts/encode_corpus.py`, `tokenizer/special.py`, `tests/test_memmap_data.py`, `scripts/estimate_fisher_tinystories.py`, `continual/__init__.py`, `tests/test_tokenizer_special.py`, `evaluation/perplexity.py`, `tests/test_data_split.py`)
**Pattern extraction date:** 2026-07-31
