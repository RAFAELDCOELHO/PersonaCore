# Phase 11: Conversational Data Pipeline - Research

**Researched:** 2026-07-31
**Domain:** Corpus acquisition + from-scratch parsing + role-token serialization + loss-mask bins through a frozen BPE tokenizer
**Confidence:** HIGH — every load-bearing claim verified live today (endpoints curled, checksums computed, formats byte-inspected, preliminary inflation measured with the actual frozen tokenizer)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Scope frame (user-directed, supersedes roadmap text)**
- **D-00:** Single corpus: **PersonaChat**; DailyDialog is cut. Dependency check performed and accepted: Phases 12/13 consume bins corpus-agnostically; Phase 14 is *better* served (persona-fact-grounded base). Accepted risk: PersonaChat is the sole corpus on an unowned S3 endpoint with no explicit license (never re-host) — **checksum + local cache of the raw JSON is the only link-rot insurance; treat the cached raw file as a precious artifact from day one.** DATA-01 and roadmap Phase 11 text (which name both corpora) need a matching edit when this lands.

**Mask-bin policy**
- **D-01:** Mask bins encode **assistant content + the turn's stop token**: mask=1 on assistant utterance tokens AND the boundary token that ends the turn (the next `<|user|>`, or eos at dialogue end), so the model trains to emit its own stop signal. Mask is built in **target space** (after the +1 label shift), per Pitfall 14's off-by-one warnings. The DATA-03 hand-built fixture pins exactly this definition.
- **D-02:** Masked-vs-unmasked for the stage-2 fine-tune is **deferred to Phase 12's calibration smoke** as a measured decision (two short runs, compare dialogue val PPL). Phase 11 ships both aligned bins so either arm is ready.
- **D-03:** Additive code surface: `get_batch_memmap_masked` (draws aligned windows from token + mask bins, sets `y[mask_shifted==0] = -100`) **lands in Phase 11** with the bins; `stop_ids` in `generate()` **defers to Phase 12** — Phase 11 stays purely data-side.

**Persona serialization**
- **D-04:** Document format: one `<|system|>` token + persona sentences **newline-joined** + turns as `<|user|>`/`<|assistant|>` spans; **persona-owner = assistant**, partner = user; one whole dialogue = **one eos-terminated document** (reconstructed once from the final utterance's full history + reply — never per-utterance examples, which duplicate early turns ~10×). The retrieval `candidates` field is ignored.
- **D-05:** Variant: **self_revised** — the user chose the honest generalization test (revised personas prevent trivial word-overlap grounding) over the easier, already-verified original. **Fallback pre-registered:** the revised endpoint is unverified; try it first and pin its checksum if live — if it 404s or can't be checksummed, fall back to the verified `personachat_self_original.json` and record the substitution in phase docs. Phase 11 never blocks on link archaeology.
- **D-06:** Text normalization: **minimal from-scratch regex detokenizer** — rejoin contractions ("' m" → "'m", "do n't" → "don't"), close space-before-punctuation; text stays lowercase (no truecasing); unit-tested on a fixture. Less byte-fragmentation through the frozen BPE, and the inflation measurement then reflects realistic text.
- **D-07:** Persona-line token budget is **set by the gate**, not pre-committed: the DATA-04 measurement reports persona-span token cost, and the format hardens with a budget (keep all lines / cap at N) chosen from those numbers.

**Inflation gate (DATA-04)**
- **D-08:** Four-metric set from one encode pass: (1) tokens/word on dialogue text, (2) persona-span token-cost distribution (feeds D-07), (3) **% of dialogues where persona + first user→assistant exchange exceeds block_size=256** — the window-utility metric that replaces DATA-04's literal "%-of-examples-over-block_size", which is misleading under the packed-window regime of D-04, (4) qualitative fragmentation samples of typical names/entities.
- **D-09:** Pre-registered bands and actions (locked before any measurement runs): tokens/word ≤ 2.5 AND persona+exchange fits in ≥ 90% of dialogues → **GO** as designed; tokens/word 2.5–3.0 or fit 70–90% → **ADAPT** within the phase using pre-listed levers only (persona-line cap, turn truncation); tokens/word > 3.0 or fit < 70% → **STOP** and escalate to the user before any bin is built.
- **D-10:** Artifact: thin `scripts/measure_inflation.py` (logic in the package) + a **committed results/ markdown report** with the numbers, the bands, and the resulting GO/ADAPT verdict — evidence-over-assertion; Phase 15's tokenizer-tax number reads straight off it.

### Claude's Discretion
- **Corpus-cut residue** (defaults): DailyDialog remnants cut cleanly (verified endpoint + checksum live in research/SUMMARY.md if ever needed); train/val split policy (default: honor PersonaChat's native train/valid split, mapped onto doc-level eos-boundary discipline — no dialogue straddles the cut); raw-data caching layout under `data/raw/` (gitignored); exact bin/report file naming.
- Mechanics of the DATA-01/roadmap wording edit for the DailyDialog cut (ride the phase's planning or first commit).
- Parser/fixture organization, mask-bin dtype details (uint8 established by research), and test-suite layout — following house patterns (thin scripts, logic in package, CPU-only tests).

### Deferred Ideas (OUT OF SCOPE)
- Tables-vs-figures for VIZ-01/VIZ-04 — Phase 13's discussion, not a Phase 11 concern.
- Phase 14 protocol minimalism (~10–20 facts, pre-registered pass/fail) — recorded for Phase 14's discuss/spec pass.
- Roadmap numbering clarification (user's "Phase 13" = roadmap Phase 14) — confirmed no-phase-cut; any merge/drop of roadmap Phase 13 is a separate roadmap edit.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | PersonaChat acquired by direct download with pinned checksum, parsed from scratch — no HF `datasets` at runtime *(DailyDialog clause superseded by D-00 — wording edit rides this phase)* | Revised-variant endpoint **found live and checksummed today**: ParlAI `personachat.tgz` sha256 `507cf864…d5622`, contains `{train,valid,test}_self_revised.txt`; fb-dialog format fully specified below; stdlib `urllib.request` + `tarfile` + `hashlib` fetch pattern; S3 fallback re-verified 200 OK |
| DATA-02 | Dialogues serialized with reserved role tokens (ids 8185–8187) through the frozen tokenizer into uint16 memmap bins | `SPECIAL_TOKENS` registry verified (8185–8187 reserved, decodable); `encode(…, allowed_special="all")` maps role markers atomically (v1.0 `encode_corpus.py` discipline); D-04 render function specified + smoke-tested against the real tokenizer today |
| DATA-03 | User-turn loss masking via `ignore_index=-100` (parallel mask bins); turn-boundary correctness unit-tested against a hand-built fixture | Mask-bin design specified: 1:1 aligned uint8 bin in token space, shift applied at draw time (`mask[i+1 : i+1+block]`) — target-space semantics per D-01; `get_batch_memmap_masked` is a ~10-line delta on the existing `get_batch_memmap`; fixture test design below |
| DATA-04 | Tokenizer-inflation measurement produced and documented as a gate before fine-tune design | All four D-08 metrics computed in a preliminary research smoke with the actual frozen tokenizer: tokens/word **3.251**, persona cost p50/p90 **104/131**, fit **99.8%**, fragmentation samples captured; TinyStories baseline **2.864** measured for context — the STOP-band escalation is *expected*, plan for it |
</phase_requirements>

## Summary

This phase is pure v1.0-pattern reuse plus one new parser — and the research resolved both of its open empirical questions today with live verification.

**D-05 is satisfied without its fallback.** The S3 JSON `personachat_self_revised.json` **404s** (verified 2026-07-31), but the revised variant exists at a live, now-checksummed endpoint: ParlAI's `personachat.tgz` (223,221,886 B, sha256 pinned below) containing `train_self_revised.txt` / `valid_self_revised.txt` in fb-dialog text format. The format was extracted and byte-inspected: episodes are already linear (numbered lines, `your persona:` prefix lines, then `user_utt\tassistant_reply\t\tcandidates` lines), which makes D-04's "reconstruct from the final utterance's history" workaround unnecessary — the ~10× duplication problem is a JSON-format artifact that doesn't exist here. The parser is ~30 lines of stdlib. Corpus verified clean: 8,939 train / 1,000 valid episodes, every dialogue line exactly 4 tab-fields, 3–5 persona lines per episode, ~7.4 turn-pairs per episode, zero apostrophes (contractions arrive pre-expanded: "i am", "do not").

**The inflation gate will almost certainly render STOP on metric 1 — plan the escalation as the expected path, not the exception.** A preliminary smoke with the real frozen tokenizer on 500 revised dialogues measured tokens/word **3.251** (STOP band: >3.0) while window-fit is **99.8%** (deep in GO territory) and persona spans cost p50 104 tokens. Crucial context the escalation will need: the same tokenizer measures **2.864 tokens/word on TinyStories itself** — its home corpus is already near the warning band, so dialogue inflation is only **1.135× relative**. The pre-registered ADAPT levers (persona cap, turn truncation) cannot move tokens/word at all — it is a property of tokenizer×register, not document length — so if the phase's committed measurement confirms >3.0, ADAPT is structurally unavailable for metric 1 and the D-09 STOP→escalate step fires. The plan must sequence the gate first and build in a user checkpoint carrying the baseline context.

**Primary recommendation:** Fetch ParlAI `personachat.tgz` (pinned sha256), parse `*_self_revised.txt` from scratch, run the gate with a user-escalation checkpoint expected, then build `dialog_{train,val}.bin` + `dialog_{train,val}_mask.bin` and `get_batch_memmap_masked` as a minimal delta on `training/data.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fetch + checksum verify | Run-once script (`scripts/`) | — | One-time network step; never at train time (locked fetch discipline) |
| fb-dialog parsing, detokenize, render, mask build | Package (`src/personacore/dialogue/`) | thin script drives it | House pattern: logic in package, CPU-only unit-testable |
| Inflation metrics | Package + thin `scripts/measure_inflation.py` | committed `results/` report | D-10: evidence-over-assertion artifact |
| Encode → bins | Run-once script (mirrors `encode_corpus.py`) | — | Encode-once discipline (D-09 v1.0); bins gitignored |
| Masked batch draw | `training/data.py` (additive function) | — | Sits beside `get_batch_memmap`, same idiom; Phase 12 consumes |
| Loss masking semantics | Data path only (`y = -100`) | — | LOCKED `forward()` untouched; `F.cross_entropy` default `ignore_index=-100` |

## Standard Stack

### Core

Zero new dependencies. Everything is stdlib + the pinned v1.0 environment.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `urllib.request` + `hashlib` + `tarfile` | stdlib | Fetch, sha256-verify, extract `personachat.tgz` | Locked fetch discipline (no HF `datasets`, no requests needed for one GET) [VERIFIED: v1.0 pattern + CONTEXT.md] |
| `re` + `json` | stdlib | Detokenizer regex; (json only if the D-05 fallback fires) | From-scratch boundary [CITED: CONTEXT.md] |
| `numpy` | pinned `>=1.26,<3` (installed) | uint16 token bins, uint8 mask bins, memmap draws | v1.0 bin discipline verbatim [VERIFIED: codebase] |
| `torch` | pinned 2.7.* (installed) | Only in `get_batch_memmap_masked` (tensor assembly) | Existing `training/data.py` idiom [VERIFIED: codebase] |
| `pytest` | 8.x (installed) | Fixture tests, CPU-only | House test discipline [VERIFIED: codebase, 222 passed / 1 skipped] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ParlAI `personachat.tgz` self_revised (fb-dialog text) | S3 `personachat_self_original.json` (pre-registered D-05 fallback) | Fallback loses the revised-persona generalization property the user chose; JSON needs the last-utterance-history reconstruction (D-04) that fb-format makes unnecessary. Use fallback only if the tarball fetch/checksum fails. |
| ParlAI `personachat.tgz` | ParlAI `convai2_fix_723.tgz` (also verified 200 OK, 429,780,162 B) | ConvAI2 is the cleaned competition re-release; larger download, hidden test set, same fb-format. Not needed — personachat.tgz has everything. |

**Installation:** nothing to install.

## Package Legitimacy Audit

**No external packages are installed by this phase.** All code is stdlib + already-pinned, already-installed v1.0 dependencies (numpy, torch, pytest). slopcheck run not applicable.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Verified Endpoints & Data Format (load-bearing findings)

All verified live 2026-07-31 via HTTPS from this machine:

| Endpoint | Status | Evidence |
|----------|--------|----------|
| `https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz` | **200 OK — PRIMARY** | 223,221,886 B, Last-Modified 2019-01-17; **sha256 `507cf8641d333240654798870ea584d854ab5261071c5e3521c20d8fa41d5622`** (computed from a full download today); contains `personachat/{train,valid,test}_{self,other,both,none}_{original,revised}.txt` (21 files) [VERIFIED: full download + shasum] |
| `https://s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_revised.json` | **404** | The D-05 "unverified revised endpoint" as a JSON sibling does not exist [VERIFIED: curl HEAD] |
| `https://s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_original.json` | 200 OK — FALLBACK | Last-Modified 2019-04-16; size 209,850,483 B per v2.0 research; structure re-confirmed via range-GET today (`{"train": [{"personality": […], "utterances": [{"candidates": […], "history": […]}]}…`); contractions intact ("i'm", "they're") [VERIFIED: curl HEAD + range-GET] |
| `https://dl.fbaipublicfiles.com/parlai/convai2/convai2_fix_723.tgz` | 200 OK — not needed | 429,780,162 B; documented here only as link-rot insurance [VERIFIED: curl HEAD] |

**D-05 disposition:** the revised variant IS live and checksummed — via ParlAI, not S3 JSON. This honors D-05's letter ("try it first and pin its checksum if live" — done, pinned) and its motivation (revised personas). Record in phase docs: *source endpoint substituted (S3 revised JSON does not exist; ParlAI tarball used); pre-registered fallback remains `personachat_self_original.json`, re-verified live today.*

### fb-dialog format (from byte inspection of `train_self_revised.txt`)

```
1 your persona: i love to redesign houses.
2 your persona: killing for sport is my hobby.
3 your persona: i shot an arrow the other day !.
4 your persona: i like to get dressed up.
5 hi , how are you doing ?<TAB>you must be very fast . hunting is one of my favorite hobbies .<TAB><TAB>cand1|cand2|…|cand20
6 i am ! for my hobby …<TAB>i also remodel homes …<TAB><TAB>…
…
1 your persona: my mother is the closest person to me.      ← line number resets to 1 = new episode
```

Verified properties [VERIFIED: full-file scan of train+valid]:
- Line format: `N ` prefix, then either `your persona: <sentence>` or `user_utt\tassistant_reply\t\tpipe-joined-candidates`. **Every** dialogue line has exactly 4 tab-fields (0 exceptions in 73,520 lines). Last candidate == the gold reply (read field 2 directly; ignore candidates per D-04).
- Episode boundary: line number resets to `1`. Persona lines always precede dialogue lines.
- 8,939 train episodes / 1,000 valid episodes; 65,719 / 7,801 turn-pairs (~7.4/ep); 3–5 persona lines per episode (min 3, max 5). Every line is a (user, assistant) pair → **every dialogue ends on an assistant reply**, so eos always terminates an assistant turn (clean for D-01 mask semantics).
- Text: lowercase, space-separated punctuation (`hi , how are you ?`), **zero apostrophes anywhere** — contractions arrive pre-expanded ("i am", "do not", "that is"). D-06's contraction-rejoin rules will no-op on this source (keep them anyway — locked decision, they cover the JSON fallback, cost nothing).
- Persona-line quirk: punctuation is *attached* in personas ("houses.") unlike utterances, and 280 train persona lines carry a `!.` artifact — a one-rule normalization (`!.` → `!`) or leave-as-is; either is fine, decide in the detok fixture.
- Estimated encoded size at 3.25 tokens/word: train ≈ **6.1M tokens (~12 MB uint16)**, valid ≈ 0.7M tokens. (Phase 12 context: one epoch ≈ 24k windows of 256.)

## Preliminary Inflation Smoke (research-time signal — NOT the phase's committed DATA-04 measurement)

Measured today with the actual frozen `artifacts/tokenizer.json`, D-04 render, minimal punct-closing detok, 500 valid_self_revised dialogues [VERIFIED: executed in the project venv]:

| D-08 Metric | Preliminary value | D-09 band it lands in |
|-------------|-------------------|----------------------|
| (1) tokens/word, dialogue text | **3.251** | **STOP** (> 3.0) |
| (2) persona-span token cost | p50 **104** / p90 **131** / max 171 | feeds D-07 (≈40–50% of a 256 window if all lines kept) |
| (3) persona + first exchange ≤ 256 | **99.8%** fit | GO (≥ 90%) |
| (4) fragmentation samples | `halloween`→5, `cheetah`→5, `remodel`→6, `mermaids`→7, `anchorage`→6 tokens | names/rare words ≈ 1 token/char, as Pitfall 13 predicted |

**Context the STOP escalation needs:** the same tokenizer on its own home corpus (TinyStories valid, 392k words) measures **2.864 tokens/word** [VERIFIED: measured today]. The absolute D-09 GO band (≤2.5) sits *below the tokenizer's baseline on any corpus*; relative dialogue inflation is 3.251/2.864 = **1.135×**. The practical window-utility metric (3) is unambiguous GO.

**Planning consequences (do not re-litigate the bands — they are locked):**
1. Sequence the gate task first, exactly as D-08/D-09/D-10 specify, and treat the STOP→user-escalation as the *expected* control-flow: build a `checkpoint:human-verify` step presenting the committed report + the 2.864 baseline + the 1.135× relative figure, and await the user's verdict before any bin is built.
2. The ADAPT levers (persona-line cap, turn truncation) mathematically cannot move metric 1 — they shorten documents, not tokens-per-word. They only move metric 3, which is already 99.8%. The plan should say this explicitly in the escalation material.
3. The phase's committed measurement remains authoritative (full corpus, final detokenizer); the smoke is a signal, not the artifact. D-10's report ships regardless of verdict — Phase 15 reads the tokenizer-tax number off it.

## Architecture Patterns

### System Architecture Diagram

```
dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz     [one-time HTTPS GET]
        │  urllib.request → hashlib sha256 == 507cf864… (hard fail on mismatch)
        ▼
data/raw/personachat.tgz  (gitignored, PRECIOUS — sole-corpus link-rot insurance, D-00)
        │  tarfile extract → {train,valid}_self_revised.txt
        ▼
fb-dialog parser (from scratch, stdlib)          src/personacore/dialogue/
        │  episodes: (persona: list[str], turns: list[(user, assistant)])
        ▼
detokenizer (D-06 regex) ──► render (D-04):
        <|system|>persona\nlines<|user|>utt<|assistant|>reply…<|endoftext|>
        │                                    │
        │                                    ├──► scripts/measure_inflation.py ──► results/inflation_report.md
        │                                    │         [D-09 GATE — verdict BEFORE bins; STOP ⇒ user checkpoint]
        ▼                                    ▼  (gate passed / user GO)
frozen tokenizer.encode(doc, allowed_special="all")   +  per-token mask builder (D-01)
        │ uint16 ids                                     │ uint8 {0,1}, same length, 1:1 aligned
        ▼                                                ▼
data/dialog_{train,val}.bin                data/dialog_{train,val}_mask.bin   (gitignored)
        └────────────────┬───────────────────────────────┘
                         ▼
train/data.py::get_batch_memmap_masked(bin, mask, …)   [Phase 12 consumer]
        x = tok[i:i+B] ; y = tok[i+1:i+1+B] ; y[mask[i+1:i+1+B]==0] = -100
```

### Recommended Project Structure (additions only)

```
src/personacore/dialogue/        # NEW package — parse/detok/render/mask/metrics logic
│   ├── __init__.py
│   ├── parse.py                 # fb-dialog episode parser (~30 lines, stdlib)
│   ├── serialize.py             # detokenizer (D-06) + render_document (D-04) + build_mask (D-01)
│   └── inflation.py             # the four D-08 metrics from one encode pass
src/personacore/training/data.py # MODIFIED (additive): +get_batch_memmap_masked
scripts/
│   ├── fetch_personachat.py     # NEW: urllib GET + sha256 verify + tarfile extract → data/raw/
│   ├── measure_inflation.py     # NEW thin driver (D-10) → results/inflation_report.md
│   └── prepare_dialog_corpus.py # NEW: parse → render → encode → 4 bins (mirrors encode_corpus.py)
tests/
│   ├── test_dialogue_parse.py   # committed fb-format fixture (a few real-shaped episodes)
│   ├── test_dialogue_serialize.py  # detok rules; render; atomic role-token encode round-trip
│   └── test_masked_batch.py     # DATA-03 hand-built fixture: exact y tensor with -100 placement
results/
│   └── inflation_report.md      # COMMITTED (D-10)
```

Scripts stay thin no-CLI entries (`_REPO_ROOT` constants, `main()`, no argparse) — the established D-04 house pattern [VERIFIED: `encode_corpus.py`]. Whether fetch/prepare are one script or two is planner discretion; the gate script must be runnable *before* prepare writes any bin.

### Pattern 1: Checksum-gated fetch (stdlib only)

```python
# Source: v1.0 fetch discipline (CONTEXT.md) + endpoints verified 2026-07-31
import hashlib, tarfile, urllib.request

URL = "https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz"
SHA256 = "507cf8641d333240654798870ea584d854ab5261071c5e3521c20d8fa41d5622"  # pinned today

def fetch(dest):
    if not dest.exists():
        urllib.request.urlretrieve(URL, dest)          # one-time; never at train time
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    assert digest == SHA256, f"checksum mismatch: {digest}"
    with tarfile.open(dest) as tf:                     # extract only the two needed members
        for m in ("personachat/train_self_revised.txt", "personachat/valid_self_revised.txt"):
            tf.extract(m, dest.parent)
```

Fallback (only if the tarball fetch/checksum fails): `personachat_self_original.json` GET, pin its sha256 on first successful fetch, record the substitution in phase docs (D-05).

### Pattern 2: fb-dialog parser (from scratch)

```python
# Source: byte-inspected format, verified clean on the full corpus 2026-07-31
def parse_episodes(path):
    eps, persona, turns = [], [], []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            num, _, rest = line.rstrip("\n").partition(" ")
            if num == "1" and (persona or turns):      # line number reset = new episode
                eps.append((persona, turns)); persona, turns = [], []
            if rest.startswith("your persona: "):
                persona.append(rest[len("your persona: "):])
            else:
                user, reply, _, _cands = rest.split("\t")   # exactly 4 fields, verified
                turns.append((user, reply))                  # candidates ignored (D-04)
    if persona or turns:
        eps.append((persona, turns))
    return eps
```

### Pattern 3: Render + mask built together in token space, shifted at draw time

Build the document string per D-04, encode once with `allowed_special="all"`, and build the mask **per turn-span during encoding** (encode each span separately and concatenate — span-wise encoding is what makes mask offsets exact):

```python
# Source: D-01/D-04 + SPECIAL_TOKENS registry (special.py, VERIFIED)
from personacore.tokenizer.special import SPECIAL_TOKENS
USER, ASSISTANT, SYSTEM = 8185, 8186, 8187
EOS = 8184

def encode_dialogue(tok, persona, turns):
    ids, mask = [], []
    def emit(token_ids, m):
        ids.extend(token_ids); mask.extend([m] * len(token_ids))
    emit([SYSTEM], 0); emit(tok.encode("\n".join(persona)), 0)     # persona span: mask 0
    for i, (user, reply) in enumerate(turns):
        emit([USER], 1 if i > 0 else 0)   # <|user|> CLOSING a prior assistant turn: mask 1 (D-01)
        emit(tok.encode(user), 0)          # user content: mask 0
        emit([ASSISTANT], 0)               # the trigger token itself: mask 0
        emit(tok.encode(reply), 1)         # assistant content: mask 1
    emit([EOS], 1)                         # eos closes the final assistant turn: mask 1 (D-01)
    return ids, mask                       # equal length, 1:1 aligned
```

Two subtleties the fixture must pin:
- The **first** `<|user|>` opens the dialogue (no assistant turn precedes it) → mask 0. Every subsequent `<|user|>` doubles as the previous assistant turn's stop token → mask 1. eos → mask 1 (every episode ends on an assistant reply — verified corpus property).
- The mask bin is stored **1:1 with the token bin** (uint8). "Built in target space" (D-01) is realized at *draw* time: `y = tokens[i+1:i+1+B]` and `y[mask[i+1:i+1+B] == 0] = -100` — the same `+1` slice shifts both, so token j's mask always governs the *prediction of* token j. The hand-built fixture asserts the final `y` tensor, which is the only place off-by-ones can hide (Pitfall 14).
- Note `<|endoftext|>` never appears in the raw text (verified: it's not in the corpus), so span-wise `encode(text)` without `allowed_special` for content, and literal id appends for role tokens, is the cleanest construction — no marker-in-text ambiguity.

### Pattern 4: `get_batch_memmap_masked` — minimal delta on the existing idiom

```python
# Source: training/data.py::get_batch_memmap (VERIFIED) + ARCHITECTURE.md Pattern 3
def get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, device):
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")    # re-opened per call (leak avoidance)
    mask = np.memmap(mask_path, dtype=np.uint8, mode="r")
    assert len(data) == len(mask)                            # alignment invariant
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack([torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix])
    m = torch.stack([torch.from_numpy(mask[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix])
    y[m == 0] = -100                                         # F.cross_entropy default ignore_index
    return x.to(device), y.to(device)
```

Same `len - block_size - 1` bound, same fresh-memmap-per-call, same uint16→int64 cast — the existing function's docstring discipline copies over verbatim. Zero model changes: LOCKED `forward()` already routes through `F.cross_entropy` whose default `ignore_index=-100` does the masking [VERIFIED: ARCHITECTURE.md line-level check of gpt.py].

### Pattern 5: Split + document discipline

- Honor the native split: `train_self_revised.txt` → `dialog_train.bin`, `valid_self_revised.txt` → `dialog_val.bin` (discretion default from CONTEXT). File-level split ⇒ no dialogue straddles the cut by construction; each episode is one eos-terminated document, matching the v1.0 `load_split` no-leakage posture.
- eos 8184 appears exactly once per dialogue, as the document separator — never mid-dialogue, never a turn terminator (Anti-pattern 5 in v2.0 ARCHITECTURE).
- `<|pad|>` 8188 stays dead; packed-window regime never pads. Windows crossing dialogue boundaries mid-stream are accepted (standard packed regime, per prior research).
- Post-build sanity block mirrors `encode_to_bin`'s: re-read bins, assert equal token/mask lengths, count eos == episode count, decode a prefix, and print the masked-token fraction (Pitfall 14 warning sign: ~0% or ~100% means the mask is wrong — expect roughly 45–55% given reply/user word counts are near-symmetric).

### Anti-Patterns to Avoid

- **Baking mask sentinels into the token stream:** uint16 can't hold −100; the parallel uint8 bin is the design, never a magic token id.
- **Building the mask by re-tokenizing rendered text and searching for role-token positions:** span-wise construction (Pattern 3) makes offsets exact by construction; substring/token-search alignment is the documented DataCollatorForCompletionOnlyLM failure mode (Pitfall 14), doubly dangerous with a fragmenting tokenizer.
- **Encoding the whole document string with `allowed_special="all"` and then guessing span boundaries** — same bug family; encode spans, concatenate ids.
- **Repurposing dead ids / re-litigating the tokenizer retrain** — locked out (Pitfall 13).
- **Running the inflation measurement after bin-building has started** — the gate's entire identity is verdict-before-format-hardening (D-08/D-09); the STOP band, if confirmed, must halt bin construction pending the user.
- **Re-hosting PersonaChat** (no explicit license) — cache locally, treat `data/raw/personachat.tgz` as precious, never commit or re-publish it.

## Don't Hand-Roll

This phase's parser/detokenizer/mask are *deliberately* hand-rolled (from-scratch boundary, locked). The don't-hand-roll list is inverted — things to NOT reimplement:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Batch windowing | New sampling logic | Copy `get_batch_memmap` verbatim + 3 lines | Bound/cast/leak discipline already debugged in v1.0 |
| Special-token ids | Any new constant | `personacore.tokenizer.special.SPECIAL_TOKENS` | Single locked registry; ids must never be retyped |
| sha256/tar/HTTP | requests/tqdm-based downloader | stdlib `urllib.request`/`hashlib`/`tarfile` | Locked fetch discipline; one GET |
| Loss masking in the model | Any `forward()` change | `ignore_index=-100` in the data path | LOCKED contract; `F.cross_entropy` default does it |
| Turn-stop at inference | `stop_ids` in `generate()` | defer to Phase 12 (D-03) | Phase 11 is purely data-side |

## Common Pitfalls

### Pitfall 1: The gate lands in STOP and the plan didn't expect it
**What goes wrong:** the plan treats GO as the happy path, hits tokens/word ≈ 3.25, and stalls or (worse) quietly proceeds to bins.
**Why:** the D-09 absolute band (≤2.5) sits below the tokenizer's own TinyStories baseline (2.864, measured) — no dialogue corpus can pass it.
**How to avoid:** plan the STOP escalation as a first-class `checkpoint:human-verify` task with the report + baseline + relative-inflation framing ready; bins build only after the user's verdict.
**Warning signs:** a plan whose bin-building task has no dependency on the gate verdict.

### Pitfall 2: Mask off-by-one at turn boundaries (Pitfall 14, the phase's named enemy)
**What goes wrong:** mask built/tested in input space; the +1 label shift silently moves the trained span one token left; model "repeats the user."
**How to avoid:** span-wise mask construction (Pattern 3), draw-time shared `+1` slice (Pattern 4), and the DATA-03 fixture asserting the *final y tensor* by hand — including the three edge tokens (first `<|user|>`=0, subsequent `<|user|>`=1, eos=1).
**Warning signs:** masked fraction ~0%/~100%; fixture only checks the mask array, not `y`.

### Pitfall 3: Detokenizer scope creep or mismatch
**What goes wrong:** implementing PTB contraction rules ("do n't") that occur zero times in the actual source, or missing the source's real quirks.
**Reality (verified):** ParlAI text has zero apostrophes (contractions pre-expanded); spaced punctuation is the only systematic artifact; personas attach punctuation and 280 lines carry `!.`.
**How to avoid:** keep D-06's rules (locked, and they cover the JSON fallback) but fixture-test against *real corpus lines*, not invented ones. Decide `!.` handling in the fixture.

### Pitfall 4: Role-token spacing inconsistency between gate and bins
**What goes wrong:** `measure_inflation.py` renders `<|user|> hello` (space) while `prepare_dialog_corpus.py` renders `<|user|>hello` — the gate measured a different tokenization than the bins ship.
**How to avoid:** one `render_document`/`encode_dialogue` function in the package, consumed by both scripts (D-10 already mandates logic-in-package). Recommendation: no space after role tokens (matches document-start statistics; the preliminary smoke measured it this way).

### Pitfall 5: Trailing-episode and empty-line edges in the parser
**What goes wrong:** the last episode is dropped (no `1 `-line follows it) or a stray blank line crashes `split("\t")`.
**How to avoid:** flush-at-EOF in the parser (Pattern 2 does); assert per-file episode counts against the verified numbers (8,939 / 1,000) in the prep script's sanity block.

### Pitfall 6: Precious-artifact loss
**What goes wrong:** `data/raw/` gets cleaned; the unowned CDN later dies; the sole corpus is gone (D-00 accepted risk).
**How to avoid:** fetch script is idempotent (skip-if-exists + re-verify checksum); phase docs record URL + sha256 + size; never re-host.

## Code Examples

See Patterns 1–4 above — all four are executable-grade and were exercised (parser + render + encode) against the real corpus and real frozen tokenizer today in the research smoke.

### DATA-03 fixture sketch (hand-built, exactness)

```python
# Turn-boundary fixture: tiny 2-turn dialogue, ids hand-chosen, y written BY HAND.
# tokens: [SYS, p1, U, u1, u2, A, a1, a2, U, u3, A, a3, EOS]
# mask:   [ 0,  0, 0,  0,  0, 0,  1,  1, 1,  0, 0,  1,  1 ]   ← first U=0, second U=1, EOS=1
# With block covering the whole thing at i=0:
#   x = tokens[0:12];  y_raw = tokens[1:13];  m = mask[1:13]
#   expected y = [-100, -100, -100, -100, -100, a1, a2, U, -100, -100, a3, EOS]
# Assert get_batch_memmap_masked reproduces expected y EXACTLY (write bins to tmp_path).
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DailyDialog + PersonaChat dual corpus | PersonaChat self_revised only | D-00 (2026-07-31 discussion) | Simpler pipeline; REQUIREMENTS/ROADMAP wording edit rides this phase |
| S3 JSON + history-reconstruction parse (D-04's JSON workaround) | ParlAI fb-dialog text, linear episodes | This research (2026-07-31) | ~30-line parser; no duplication concern; candidates trivially ignored |
| HF `datasets` for PersonaChat | Direct fetch + from-scratch parse | Locked v2.0 kickoff | No network at train time, no dependency |

**Deprecated/outdated:** `yanran.li` DailyDialog URL (404, v2.0 research); DailyDialog fetch entirely (D-00 — checksum retained in research/SUMMARY.md only).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | PersonaChat's native train/valid episodes are disjoint (no shared dialogues/personas across files) | Pattern 5 | Val PPL optimistic in Phase 12; mitigate: none needed beyond dataset's own construction — standard for this corpus |
| A2 | The S3 fallback JSON contains no PTB-spaced contractions ("do n't") — only intact ones observed in the inspected prefix | Pitfall 3 | D-06's contraction rules already cover it; zero risk to the primary path |
| A3 | Masked-token fraction lands ~45–55% (from word-count symmetry, not measured on encoded bins) | Pattern 5 sanity block | Only affects a sanity-print threshold; fixture test is the real guard |

All other claims are [VERIFIED] (live curl/download/shasum/full-file scans/tokenizer runs today) or [CITED] to canonical project docs.

## Open Questions

1. **Does the user GO past the pre-registered STOP band?**
   - What we know: preliminary tokens/word 3.251 > 3.0 (STOP), but fit 99.8% (GO) and TinyStories baseline 2.864 → relative inflation only 1.135×; ADAPT levers cannot move tokens/word.
   - What's unclear: only the user can render the verdict — D-09 locks that.
   - Recommendation: plan the escalation checkpoint after the committed measurement, presenting exactly this context; do not build bins before it.

2. **`!.` persona artifact handling** — normalize or keep; decide in the detok fixture (trivial either way; discretion area).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv (`.venv`) | all code/tests | ✓ | 3.11 (mandatory per CLAUDE.md) | — |
| numpy / torch / pytest | bins, batch fn, tests | ✓ | pinned v1.0 env | — |
| `artifacts/tokenizer.json` | encode | ✓ | frozen v1.0 artifact | — (never retrain) |
| Network (one-time fetch) | DATA-01 | ✓ (verified today) | — | fallback S3 JSON also live |
| Disk (~250 MB raw + ~15 MB bins) | data/raw + bins | ✓ | — | — |
| TinyStories valid text (baseline context) | escalation material | ✓ (local, 22.5 MB) | — | — |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (installed in `.venv`) |
| Config file | via `pyproject.toml` / `Makefile` (`make test`) |
| Quick run command | `.venv/bin/pytest tests/test_masked_batch.py tests/test_dialogue_parse.py tests/test_dialogue_serialize.py -x -q` |
| Full suite command | `make test` (currently 222 passed / 1 skipped — must stay green) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | fb-format parse (episode boundaries, 4-field lines, persona extraction); checksum verify logic | unit | `pytest tests/test_dialogue_parse.py -x` | ❌ Wave 0 |
| DATA-02 | detok rules (real-line fixture); D-04 render; role tokens encode atomically to 8185–8187; decode round-trip | unit | `pytest tests/test_dialogue_serialize.py -x` | ❌ Wave 0 |
| DATA-03 | hand-built fixture: exact `y` tensor with −100 placement incl. first-`<|user|>`/subsequent-`<|user|>`/eos edges; token↔mask length alignment | unit | `pytest tests/test_masked_batch.py -x` | ❌ Wave 0 |
| DATA-04 | four metrics computed on a tiny committed fixture (deterministic values) | unit + manual artifact | `pytest tests/test_dialogue_serialize.py -k inflation -x`; full-corpus report is a run-once manual artifact (like `encode_corpus.py`) | ❌ Wave 0 |

Manual-only steps (justified — network/one-time, same posture as v1.0 encode): the real fetch, the full-corpus gate run, and bin building on the real machine; each script carries a post-run sanity block (checksum, episode counts, eos counts, masked fraction, decoded prefix).

### Sampling Rate
- **Per task commit:** quick run command above
- **Per wave merge:** `make test`
- **Phase gate:** full suite green + committed `results/inflation_report.md` + user verdict recorded before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_dialogue_parse.py` — DATA-01 (needs a small committed fb-format fixture file, a few real-shaped episodes)
- [ ] `tests/test_dialogue_serialize.py` — DATA-02/DATA-04
- [ ] `tests/test_masked_batch.py` — DATA-03
- Framework install: none needed.

## Security Domain

Minimal surface — no auth, sessions, or user input. The one trust boundary:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Pinned sha256 on the downloaded tarball (hard-fail on mismatch) before any parse; `tarfile` extraction of **named members only** (no wildcard extractall — path-traversal guard); HTTPS URLs only |
| V2/V3/V4/V6 | no | No auth/session/access-control/crypto surface in this phase |

Threat pattern: tampered/truncated download (Tampering) → mitigated by checksum-before-parse; malicious tar paths (Tampering) → mitigated by extracting only the two known member names.

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv **mandatory** — never validate against local 3.14; tests CPU-only, GPU-free.
- No HF `datasets`/`transformers`/`tokenizers` as implementation; from-scratch parser/detokenizer; frozen tokenizer loaded, never retrained.
- Encode-once discipline; uint16 bins; data + checkpoints gitignored; no network at train time.
- Thin no-CLI scripts (`_REPO_ROOT` constants, `main()`, no argparse); logic in the package.
- `make lint` (ruff check + format) must pass; GSD workflow entry points for all edits.
- Zero-budget: no new services, no paid APIs; offline CSV/matplotlib logging posture (no logging needed this phase).

## Sources

### Primary (HIGH confidence)
- Live HTTPS verification 2026-07-31 (this session): `personachat.tgz` 200 OK + **full download + sha256** `507cf864…d5622` + member listing; `personachat_self_revised.json` **404**; `personachat_self_original.json` 200 OK + structure range-GET; `convai2_fix_723.tgz` 200 OK
- Full-file scans of `train/valid_self_revised.txt` (episode/turn/persona counts, 4-field invariant, zero-apostrophe finding, `!.` artifact count)
- Preliminary inflation smoke executed in the project venv with `artifacts/tokenizer.json` (tokens/word 3.251, fit 99.8%, persona p50/p90 104/131, fragmentation samples) + TinyStories baseline 2.864 on local `TinyStoriesV2-GPT4-valid.txt`
- Shipped code, line-read this session: `src/personacore/tokenizer/special.py` (ids 8184–8191 LOCKED), `src/personacore/training/data.py` (`get_batch_memmap` idiom), `scripts/encode_corpus.py` (encode-once + `allowed_special="all"` discipline)
- `.planning/phases/11-conversational-data-pipeline/11-CONTEXT.md` (D-00…D-10); `.planning/REQUIREMENTS.md`; `.planning/research/{SUMMARY,ARCHITECTURE,PITFALLS}.md` (Patterns 3–4, Pitfalls 13–14 — converged, not re-litigated)

### Secondary (MEDIUM confidence)
- PersonaChat licensing posture (no explicit license — never re-host) from v2.0 research/SUMMARY.md

### Tertiary (LOW confidence)
- None load-bearing.

## Metadata

**Confidence breakdown:**
- Endpoints/format/checksums: HIGH — downloaded, hashed, and scanned today
- Serialization/mask design: HIGH — locked decisions + verified code seams; the fixture test is the enforcement
- Inflation gate outcome: HIGH that the committed measurement lands near 3.25 (measured with the real tokenizer on 500 real dialogues); the *user's verdict* at the STOP escalation is inherently open
- Detokenizer scope: HIGH for primary source (zero apostrophes verified); MEDIUM for the fallback JSON's full contraction inventory (A2)

**Research date:** 2026-07-31
**Valid until:** ~2026-08-30 (stable domain; the unowned CDN endpoints are the only decay surface — checksums pin them)
