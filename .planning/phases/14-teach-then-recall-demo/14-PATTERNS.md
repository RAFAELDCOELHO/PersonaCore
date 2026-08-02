# Phase 14: Teach-Then-Recall Demo - Pattern Map

**Mapped:** 2026-08-01
**Files analyzed:** 13 source files (4 modified, 9 new) + 4 generated `results/` evidence artifacts
**Analogs found:** 13 / 13 (11 exact, 2 role-match)

Every new file in this phase has a direct in-repo precedent. This phase writes **no new ML
machinery** — it composes five existing script templates and adds two ~15-line package functions.
The pattern work is therefore mostly *which template each new file copies* and *which line ranges
carry the load-bearing idiom*.

---

## File Classification

| New/Modified File | N/M | Role | Data Flow | Closest Analog | Match |
|-------------------|-----|------|-----------|----------------|-------|
| `src/personacore/dialogue/serialize.py` (+`build_recall_prompt`) | M | utility (shared source of truth) | transform | `cap_persona` — **same file**, `serialize.py:88-110` | exact |
| `src/personacore/dialogue/__init__.py` | M | barrel | — | itself (existing `__all__`) | exact |
| `src/personacore/generation/text.py` (+`generate_text_from_ids`) | M | utility (streaming wrapper) | streaming | `generate_text` — **same file**, `text.py:62-116` | exact |
| `src/personacore/generation/__init__.py` | M | barrel | — | itself (existing `__all__`) | exact |
| `scripts/phase14_factset_gate.py` | N | script driver (gated report) | batch → committed markdown + BLOCKING verdict | `scripts/measure_inflation.py` | exact (D-06 names this precedent) |
| `scripts/teach_persona.py` | N | script driver (bins + training run) | file-I/O + batch training | `scripts/prepare_dialog_corpus.py` (bins half) + `scripts/train_adapter_smoke.py` (training half) | exact ×2 |
| `scripts/phase14_recall.py` | N | script driver (scored eval harness) | request-response per question + report | `scripts/make_transcripts.py` (generate+evidence) + `scripts/finetune_ab.py` (pre-registration + proofs) | exact ×2 |
| `scripts/personalize_demo.py` | N | demo UI script | streaming request-response + event-driven | `scripts/demo_app.py` — **READ-ONLY reference (D-17)** | role-match (`Blocks` vs `ChatInterface`) |
| `tests/test_phase14_factset.py` | N | test (frozen-tokenizer unit) | — | `tests/test_dialogue_serialize.py` | exact |
| `tests/test_phase14_teaching.py` | N | test (hand-written mask fixture) | — | `tests/test_masked_batch.py` | exact |
| `tests/test_phase14_scoring.py` | N | test (importlib-loaded driver) | — | `tests/test_phase13_driver.py` | exact |
| `tests/test_phase14_demo.py` | N | test (mask parity + prompt identity) | — | `tests/test_forbid_ids.py` + `tests/test_demo_callback.py` | role-match — **see Structural Gap S1** |
| `tests/test_recall_prompt.py` | N | test (tiny-GPT fixture) | — | `tests/test_demo_callback.py` fixture block | exact |

**Generated evidence (written by the scripts above, not hand-authored):**
`results/phase14_factset_report.md` · `results/phase14_calibration_report.md` ·
`results/phase14_recall_report.md` · `results/phase14_transcripts.md`
Format analogs: `results/inflation_report.md` (gated verdict), `results/phase13_ab_report.md`
(pre-registration + reconciliation), `results/transcripts.md` (transcript register).

---

## Pattern Assignments

### `src/personacore/dialogue/serialize.py` — add `build_recall_prompt` (utility, transform)

**Analog:** `cap_persona` in the same file. This is the **strongest analog in the phase** — its
docstring already *is* the D-18 argument, written for a different pair of callers.

**The shared-source-of-truth docstring pattern to copy verbatim in register** (`serialize.py:96-99`):

```python
    SINGLE source of truth for the cap (Pitfall 4): the bin builder
    (``scripts/prepare_dialog_corpus.py``) and the transcript generator
    (``scripts/make_transcripts.py``) both import THIS function, so transcript prompts
    tokenize identically to the training bins by construction — never by a copied constant.
```

`build_recall_prompt`'s docstring says the same thing with `scripts/phase14_recall.py` and
`scripts/personalize_demo.py` as the two callers, and cites D-18.

**Role-id sourcing pattern** (`serialize.py:15`, `68-70`) — ids come from the LOCKED registry,
never retyped:

```python
from personacore.tokenizer.special import EOS_ID, SPECIAL_TOKENS
...
    user_id = SPECIAL_TOKENS[_USER]
    assistant_id = SPECIAL_TOKENS[_ASSISTANT]
    system_id = SPECIAL_TOKENS[_SYSTEM]
```

`SPECIAL_TOKENS["<|assistant|>"] == 8186` `[VERIFIED: src/personacore/tokenizer/special.py:15-24]`.
The new function must resolve `ASSISTANT_ID` through this dict, not the literal 8186.

**Truncation idiom to copy** — `scripts/make_transcripts.py:136-138` already does exactly the
truncation `build_recall_prompt` needs; the new function is that line moved into the package:

```python
        ids, _mask = encode_dialogue(tok, kept, turns)
        # Prompt = persona + first user turn, truncated to END at <|assistant|> (8186) —
        # the id sequence tokenizes identically to the bins (Pitfall 4).
        prompt_ids = ids[: ids.index(ASSISTANT_ID) + 1]
```

**Barrel update pattern** (`src/personacore/dialogue/__init__.py`): add to both the `from .serialize
import ...` line and the alphabetically-sorted `__all__` list. The module docstring names which plan
shipped what ("Plan 11-01 ships …; Plan 11-03 adds …") — append the Phase-14 sentence in that form.

---

### `src/personacore/generation/text.py` — add `generate_text_from_ids` (utility, streaming)

**Analog:** `generate_text` (`text.py:62-116`) — the new function is that body with the string-encode
line replaced by a supplied id list. **Copy the cumulative-decode block verbatim**; it is the one
piece with a named crash class attached (Pitfall 3, `UnicodeDecodeError` on a split glyph).

**Core pattern to copy** (`text.py:100-116`):

```python
    emitted = ""
    buffer_ids = []  # NEW ids only — the prompt is never decoded back out (D-02).
    for tok in generate(model, idx, eos_id=eid, max_new_tokens=max_new_tokens, **gen_kw):
        buffer_ids.append(tok)
        # Decode the WHOLE running buffer each step (D-06). A byte-level-BPE glyph can span
        # several ids, so a cumulative buffer that ends mid-glyph is NOT a defect — the strict
        # decoder raises UnicodeDecodeError on those trailing partial bytes (Pitfall 3). Hold the
        # ids and try again next step; the glyph surfaces once its final id arrives.
        try:
            text = tokenizer.decode(buffer_ids)
        except UnicodeDecodeError:
            continue  # partial multi-byte glyph — wait for the next id (no mojibake, no crash).
        new = text[len(emitted) :]
        emitted = text
        if new:
            yield new
```

**The line that must NOT be copied** (`text.py:95`) — this is exactly the Gap-G1 defect:

```python
    prompt_ids = [eid] + (tokenizer.encode(prompt) if prompt else [])   # ← string-space; WRONG for recall
```

Replace with the caller-supplied `prompt_ids` list. Keep `_model_device(model)` (`text.py:54-59`)
and the tensor build (`text.py:96`) unchanged.

**Bounds-guard pattern to copy** (`text.py:90-93`) — the V5/T-06-04 DoS guard fires **before** the
loop, and `tests/test_demo_callback.py::test_kwargs_thread_through` pins that it fires through
wrappers:

```python
    if max_new_tokens <= 0 or max_new_tokens > max_new_tokens_cap:
        raise ValueError(
            f"max_new_tokens must be in (0, {max_new_tokens_cap}], got {max_new_tokens!r}"
        )
```

**Cumulative adapter pattern** (`text.py:128-147`) — the demo needs the *cumulative* yield shape
(Gradio replaces the bubble each yield). Either add a `_cumulative` sibling or accumulate in the
demo callback; `generate_text_cumulative`'s 4-line body is the template:

```python
    acc = ""
    for delta in generate_text(model, tokenizer, prompt, max_new_tokens=max_new_tokens, **gen_kw):
        acc += delta
        yield acc
```

Note the UI-SPEC's per-turn stamp means the demo yields `STAMP + "\n\n" + acc`, and with the token
panel as a second output it yields a **tuple** each step.

---

### `scripts/phase14_factset_gate.py` (script driver, batch → gated report)

**Analog:** `scripts/measure_inflation.py` — D-06 names this precedent (`results/inflation_report.md`
+ blocking user verdict) by file.

**Clobber-guard pattern** (`measure_inflation.py:66-75`) — a recorded verdict is committed evidence;
a rerun must not silently reset it:

```python
    # A recorded (non-PENDING) verdict is committed evidence (D-10) — never clobber it
    # silently: a rerun would reset ``## Verdict`` to PENDING and drop any hand-added sections.
    if REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
        recorded = REPORT_PATH.read_text(encoding="utf-8").split("## Verdict")[-1]
        if "PENDING" not in recorded:
            raise SystemExit(
                f"[measure_inflation] {REPORT_PATH} already carries a recorded verdict — "
                "it is committed evidence (D-10). Pass --force to overwrite and re-measure."
            )
```

**Report shape pattern** (`measure_inflation.py:123-192`) — an f-string triple-quoted template with
pre-composed row variables (source lines stay under ruff's 100-char limit), a pre-registered bands
table, and a trailing `## Verdict\n\nPENDING — user decision at checkpoint.` section. The fact-set
report's tables (per-fact census, per-fact base completions, exact-match verdicts, quoted close-call
rejections, survivor count vs the 5–10 target) drop into the same skeleton.

**Downstream verdict-enforcement pattern** (`scripts/prepare_dialog_corpus.py:62-83`) — this is the
half that makes D-06 *blocking* rather than advisory. `scripts/teach_persona.py` must carry this
against `results/phase14_factset_report.md`:

```python
def _require_go_verdict(report_path):
    """T-11-07 gate: hard-exit unless the report's ``## Verdict`` section reads GO or ADAPT."""
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
            f"[prepare_dialog_corpus] recorded verdict is {verdict!r} — bins may only be "
            "built on GO/ADAPT (D-09). STOP/PENDING must be escalated, not bypassed."
        )
    return verdict
```

**Generation half** (the D-02(b) guessability probes) copies `make_transcripts.py`'s `_complete`
helper — see the `phase14_recall.py` section below; it is the same call.

---

### `scripts/teach_persona.py` (script driver, file-I/O + batch training)

Two analogs, one per half. **Do not merge their registers** — the bins half is
`prepare_dialog_corpus.py`, the training half is `train_adapter_smoke.py`.

#### Half 1 — bins builder. Analog: `scripts/prepare_dialog_corpus.py`

**Shard-and-write idiom** (`prepare_dialog_corpus.py:101-112`) — copy verbatim, swapping the episode
source for `render_family(family_id, fact)`:

```python
    id_shards, mask_shards = [], []
    for persona, turns in it:
        kept = cap_persona(tok, persona)
        capped += kept != persona
        ids, mask = encode_dialogue(tok, kept, turns)
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))

    np.concatenate(id_shards).tofile(bin_path)
    np.concatenate(mask_shards).tofile(mask_path)
```

Phase 14 passes `persona=[]` (bare `<|system|>`, no persona content — the clean-room shape), so
`cap_persona` is a no-op here; teaching episodes are `encode_dialogue(tok, [], [(question, answer)])`.

**Post-build proof pattern** (`prepare_dialog_corpus.py:115-160`) — every check is a loud
`SystemExit` naming the number. The Phase-14 adaptations:

```python
    if len(ids) != len(mask):
        raise SystemExit(... "bins must be 1:1 aligned (T-11-04).")
    frac = float(mask.mean())
    lo, hi = MASK_FRACTION_BAND
    if not lo <= frac <= hi:
        raise SystemExit(... "~0%/~100% means the mask is wrong (Pitfall 14).")
    # End-to-end smoke: a masked batch drawn from the REAL bins carries -100 sentinels.
    x, y = get_batch_memmap_masked(bin_path, mask_path, 4, BLOCK_SIZE, "cpu")
    if not bool((y == -100).any()):
        raise SystemExit(... "mask never applied (Pitfall 14).")
```

**Two Phase-14-specific deltas the planner must state:**
- The corpus-floor guard (14-RESEARCH Pitfall 5) is **new**: `len(tokens) <= BLOCK_SIZE + 1` must
  raise a `SystemExit` naming the number, because `get_batch_memmap_masked` otherwise dies with an
  opaque `ValueError: low >= high` from `np.random.randint`.
- `MASK_FRACTION_BAND = (0.30, 0.70)` is calibrated for PersonaChat episodes. A QA-episode corpus is
  **answer-heavy by construction**, so the band almost certainly needs a different (documented)
  value — copying the literal unchanged is a false-failure waiting to happen.

#### Half 2 — training run. Analog: `scripts/train_adapter_smoke.py`

**Load-order + census-canary block** (`train_adapter_smoke.py:95-121`) — the load-bearing ordering,
copy structure exactly:

```python
    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy objects.
    # TRUSTED-only read of the project's OWN checkpoint (T-09-11) — never a foreign file.
    blob = torch.load(BEST_PATH, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering.

    n_wrapped = inject_lora(model, LORA_CFG)
    if n_wrapped != 6 * n_layer:
        raise SystemExit(
            f"inject_lora wrapped {n_wrapped} projections, expected 6 * n_layer = {6 * n_layer}"
        )
    mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected_trainable = LORA_CFG.r * n_layer * 18 * n_embd     # 331,776 at r=8 / 6L / 384d
    if trainable != expected_trainable:
        raise SystemExit(
            f"trainable census {trainable} != r*n_layer*18*n_embd = {expected_trainable}"
        )

    # Move BEFORE snapshotting: torch.equal raises on cross-device tensors.
    model.to(runtime.device)
    before = snapshot_params(model)
```

**The params-actually-update canary** (`train_adapter_smoke.py:160-176`) — copy verbatim; this is
the MPS silent-freeze hunt (PITFALLS P5) on real weights:

```python
    if not math.isfinite(float(final)):
        raise SystemExit(f"non-finite final loss {final!r} (PITFALLS P5)")

    for n, p in model.named_parameters():
        if p.requires_grad:
            if torch.equal(p, before[n]):
                raise SystemExit(
                    f"[canary] trainable {n} did not move — silent training failure (P5)"
                )
        elif not torch.equal(p, before[n]):
            raise SystemExit(
                f"[canary] frozen base param {n} changed — grad isolation broken (LORA-02)"
            )
```

**Export pattern with the fingerprint READ, never recomputed** (`train_adapter_smoke.py:178-188`):

```python
    # Fingerprint READ from the base checkpoint, never recomputed (provenance trio, D-02).
    export_adapter(
        ADAPTER_PATH,
        adapter=lora_state_dict(model),
        lora_config=asdict(LORA_CFG),
        base_fingerprint={
            "git_sha": blob["git_sha"],
            "step": blob["step"],
            "val_loss": blob["val_loss"],
        },
    )
```

**`train()` call pattern** (`train_adapter_smoke.py:141-159`) — keyword-only, `weight_decay=0.0`
overriding `TrainConfig`'s 0.1 default. Phase 14 adds `train_mask_bin` / `val_mask_bin`; the masked
kwarg shape is in `finetune_ab.py:270-299`:

```python
    train(
        train_config=TrainConfig(lr=LR, warmup_steps=..., max_steps=..., batch_size=...,
                                 weight_decay=WEIGHT_DECAY),
        runtime_config=runtime,
        model=model, model_config=model_cfg,
        train_bin=PERSONA_BIN,
        train_mask_bin=PERSONA_MASK_BIN,   # ← Phase-14 REVERSES Phase-12's unmasked verdict
        val_bin=DIALOG_VAL, val_mask_bin=DIALOG_VAL_MASK,
        penalty_fn=None,                    # ← structurally forced (14-RESEARCH Pattern 3)
        log_path=LOG_PATH, checkpoint_path=..., checkpoint_interval=...,
        return_final_loss=True,
    )
```

`train()`'s guards `[VERIFIED: loop.py:277-286]`: `train_mask_bin` requires `train_bin`;
`val_mask_bin` requires `train_bin` **and** a `.bin` `val_bin`. The full signature is
`loop.py:172-201` — every arg is keyword-only.

**Refuse-to-rerun pattern for the calibration arms** (`finetune_ab.py:125-142`) — the calibration and
real runs are arm-scoped recorded evidence, same as Phase 13's:

```python
def arm_outputs(arm):
    """D-07 name-scoped write targets for one arm: (run CSV, end-of-run checkpoint)."""
    return (_REPO_ROOT / "results" / f"phase13_{arm}" / "run.csv",
            _REPO_ROOT / "checkpoints" / f"phase13_{arm}_latest.pt")

def refuse_if_exists(paths):
    """D-07 / WR-02 refuse-to-rerun: an arm's outputs are RECORDED evidence once written."""
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[finetune_ab] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )
```

D-15's replay arm, D-21's second-person register arm, and the real run are all *arms* — this scoping
+ refusal is the pattern that keeps their outputs from overwriting each other.

---

### `scripts/phase14_recall.py` (script driver, request-response + report)

Two analogs. Generation/evidence half = `make_transcripts.py`; pre-registration/proof half =
`finetune_ab.py`.

**Pre-registration constants block** (`finetune_ab.py:66-106`) — the exact register D-09/D-10/D-19
require. Module-level literals with the provenance of each number in its comment; the driver never
parses a report for a number:

```python
# ===== PRE-REGISTRATION (D-01..D-11, locked before any Phase-13 number) =====
#
# Transcribed from committed Phase-12 evidence. Hardcoded on purpose — the driver never parses
# the report for numbers. This block is committed BEFORE either arm runs; git history order is
# the pre-registration proof (finetune_smoke.py:77+ register, T-12-08).

# D-05/§2 — K reused BLIND from Phase 12: the same deliberately conservative default, NOT
# re-chosen after seeing any Phase-13 number.
K = 2
...
MARGIN = K * DELTA_RET
```

**Gate-as-pure-function pattern** (`finetune_ab.py:112-122`) — every threshold rule is a module-level
pure function so `importlib` can test it without running anything:

```python
def ewc_mitigates(naive_ret, ewc_ret):
    """D-06 claim gate, retention-only: EWC mitigates forgetting iff the EWC arm beats the
    naive arm's retention PPL by MORE than MARGIN = K x DELTA_RET. Boundary is a FAIL
    (delta == MARGIN returns False). Acquisition is reported descriptively with NO gate."""
    return (naive_ret - ewc_ret) > MARGIN
```

D-19's generation-budget derivation is the same shape: a pure function over the locked census +
headroom formula, returning `RECALL_MAX_NEW_TOKENS`, plus a fit-guard raising `SystemExit`.
The scoring normalizer, the substring gate, and the mechanical contradiction detector are all
module-level pure functions for the same reason.

**Loud-proof helper** (`finetune_ab.py:168-171`):

```python
def _prove(condition, message):
    """Loud end-of-run proof: SystemExit naming the violated contract (never bare assert)."""
    if not condition:
        raise SystemExit(f"[finetune_ab] PROOF FAILED: {message}")
```

Use this for D-19's fit guard and for Pattern-8's "no locked fact value appears in the decoded
prompt / prompt ids" clean-room assertion.

**Per-question completion helper** (`make_transcripts.py:67-81`) — copy verbatim; the
`len(gen) < MAX_NEW_TOKENS` trick is how stop-fraction is measured without a second signal:

```python
def _complete(model, prompt_ids, device, forbid, **kw):
    """One completion: returns (generated_ids, stopped_on_stop_id)."""
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = collect(model, idx, max_new_tokens=MAX_NEW_TOKENS, forbid_ids=forbid,
                  stop_ids=STOP_IDS, **kw)
    gen = out[0, len(prompt_ids) :].tolist()
    # generate() stops WITHOUT yielding the stop id (D-05): fewer than max_new_tokens
    # generated tokens means a stop-id termination.
    return gen, len(gen) < MAX_NEW_TOKENS
```

Called greedy + N seeded (`make_transcripts.py:140-141`); D-10 needs `k/N` so the seeded call
repeats N times. The **per-prompt generator seeding** discipline is in
`scripts/make_retention_samples.py:8-14`: seed an explicit `torch.Generator` per question
(`SEED + question_index`) so an early stop in one question cannot shift a later question's stream —
this is the answer to 14-RESEARCH Open Question 4.

**Setup + device + mask block** (`make_transcripts.py:99-115`) — the standard driver preamble:

```python
    summary = preflight_device(strict=True)
    print(f"[make_transcripts] preflight: {summary}")
    runtime = RuntimeConfig()
    device = runtime.device
    ...
    model.to(device); model.eval()
    tok = from_json(TOKENIZER_PATH)
    # .to(device): next_token masked_fills logits in place on the model device.
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(device)
```

**Note for D-11.3:** 14-RESEARCH Pitfall 11 requires the bit-identity logits comparison to run on
**CPU**, not the preflight device. That control needs `RuntimeConfig(device="cpu")` locally — the
`demo_app.py:81` pin (`runtime = RuntimeConfig(device="cpu")  # pin CPU explicitly`) is the idiom.

**Report/evidence writing** (`make_transcripts.py:146-183`) — build a `blocks` list of markdown
lines, prepend a `header` list carrying the measured proxies, `"\n".join(...)`, one `write_text`:

```python
    header = [
        "# PersonaCore — Conversational-Base Transcripts (TUNE-01)",
        "",
        "> These transcripts are REPRESENTATIVE, not cherry-picked: episodes are drawn from",
        "> the held-out PersonaChat valid split with a seeded rng (default_rng(1337)). Each",
        "> prompt is the episode's `encode_dialogue` id sequence ... never a hand-formatted",
        "> string — so prompts tokenize identically to the training bins.",
        "",
        "## Adherence Proxies (measured over all generations)",
        "",
        f"- Stop-id termination fraction: **{n_stopped}/{n_completions} = {stop_frac:.2f}**",
        ...
    ]
    TRANSCRIPTS_PATH.write_text("\n".join(header + blocks), encoding="utf-8")
```

The "REPRESENTATIVE, not cherry-picked" opening blockquote is the register D-10/D-12 need for
`phase14_transcripts.md` ("every completion, failures included").

**Provenance echo** (`finetune_ab.py:322-329`) — the Pattern-8 run-level provenance block:

```python
    print(f"[finetune_ab] ===== provenance ({arm} arm) =====")
    print(f"  seed: {SEED} (seed_everything immediately before GPT build — owns data order)")
    print(f"  train_config: {cfg}")
    print(f"  anchor fingerprint: {fingerprint}")
    print(f"  driver git_sha: {git_sha()}")
```

Phase 14 adds `os.getpid()`, wall-clock, and SHA-256 of `convbase_slim.pt` + the adapter (the
process-boundary evidence).

---

### `scripts/personalize_demo.py` (demo UI, streaming + event-driven)

**Analog:** `scripts/demo_app.py` — **READ-ONLY REFERENCE. D-17 forbids modifying it.** Excerpt from
it heavily; edit nothing in it. The M1 honesty lock at `demo_app.py:52-53` ("no chat tuning, no
personalization yet — that's Milestone 2") must stay literally true, which is the whole reason this
is a new file.

**Match quality is role-match, not exact:** `demo_app.py` is `gr.ChatInterface` with
`additional_inputs`; D-18 forces `gr.Blocks`. Copy its *offline/security boilerplate* exactly and its
*layout* not at all (the layout contract is `14-UI-SPEC.md`).

**Analytics kill-switch ordering** (`demo_app.py:29-42`) — the ordering is load-bearing and the
`noqa: E402` comments are how ruff is kept green:

```python
import os
import pathlib

# Kill Gradio telemetry + the startup version-check ping BEFORE the import it affects
# (08-RESEARCH Pitfall 5) — this line must precede `import gradio`.
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr  # noqa: E402  (must follow the analytics kill-switch above)

from personacore.checkpoint import load_slim  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.generation import generate_text_cumulative, undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402
```

**Missing-artifact message pattern** (`demo_app.py:62-65`, `75-76`) — a named module constant raised
before `launch()`; UI-SPEC's failure table specifies two more of these in the same shape:

```python
MISSING_CKPT_MSG = (
    "checkpoints/model_slim.pt not found. Either download the release asset (see README "
    "quickstart) or regenerate it from a local best.pt: python scripts/export_slim.py"
)
...
    if not SLIM_PATH.exists():
        raise FileNotFoundError(MISSING_CKPT_MSG)
```

**Lazy-build + CPU-pin + forbid_ids capture** (`demo_app.py:68-90`) — the four things D-17 names as
duplicated boilerplate, and the `build_demo()` laziness that makes the module import-safe for tests:

```python
def build_demo() -> gr.ChatInterface:
    """Construct the ChatInterface (lazy: importing this module loads NO model — tests/CI safe)."""
    ...
    ckpt = load_slim(SLIM_PATH)  # weights_only=True — zero code execution on load (T-08-01).
    model = GPT(ModelConfig(**ckpt["model_config"]))
    model.load_state_dict(ckpt["model"])
    runtime = RuntimeConfig(device="cpu")  # pin CPU explicitly — no ad-hoc device strings.
    model.to(runtime.device)
    model.eval()
    tok = from_json(TOKENIZER_PATH)  # FROZEN artifact — never retrain.
    # CR-01: ... Masking the 7645 dead ids to -inf makes them unreachable at ANY slider setting.
    forbid_ids = undecodable_ids_mask(tok, model.config.vocab_size)
```

Phase 14 inserts `inject_lora` + `load_adapter_weights(model, load_adapter(path,
expected_fingerprint=slim_trio))` between `load_state_dict` and `.to(device)`.

**Streaming callback pattern** (`demo_app.py:92-106`) — history is deliberately ignored; the
Phase-14 reason is stronger (clean room, not just honesty):

```python
    def tell_story(message, history, temperature, top_k, max_new_tokens):
        # IGNORE history — fresh story per message ... Yield the GROWING cumulative string:
        # Gradio replaces the displayed bubble with each yield, so the bubble grows and never
        # flickers lone fragments.
        del history
        yield from generate_text_cumulative(model, tok, message, max_new_tokens=..., ...)
```

**Launch pattern** (`demo_app.py:124-129`):

```python
def main() -> None:
    build_demo().launch(share=False)  # localhost 127.0.0.1:7860 — no tunnel, no exposure.
```

**Toggle/reset callbacks** — no script analog exists yet; the semantics come straight from
`src/personacore/lora/inject.py`:
- `set_adapter_enabled` (`inject.py:109-129`) — pre-pass refuses on any merged module *before*
  flipping a single flag, then flips all. Its docstring names Phase 14 explicitly.
- `eject_adapter` (`inject.py:162-185`) — returns the wrapper count; refuses while merged.
The wiring shape is in 14-RESEARCH §Code Examples "The live toggle".

---

### `tests/test_phase14_factset.py` (test, frozen-tokenizer census)

**Analog:** `tests/test_dialogue_serialize.py`.

**Frozen-tokenizer module fixture** (`test_dialogue_serialize.py:29`, `43-47`):

```python
TOKENIZER_PATH = "artifacts/tokenizer.json"

@pytest.fixture(scope="module")
def tok():
    # The FROZEN production artifact — the registry that ships is what matters, never a
    # freshly trained tokenizer (Pitfall 6).
    return from_json(TOKENIZER_PATH)
```

`artifacts/tokenizer.json` is git-tracked (unlike `checkpoints/`), so this test runs in CI. That is
exactly why D-07 splits the tokenizer half from the guessability half.

**Docstring pattern** (`test_dialogue_serialize.py:1-13`) — states what is pinned and why, ending
with the CPU-only line. D-07 additionally **mandates** a docstring paragraph stating why the
guessability half is *not* permanent (checkpoint-specific to `convbase_best.pt`; re-running against a
future checkpoint requires a fresh gated measurement, not a test re-run).

---

### `tests/test_phase14_teaching.py` (test, hand-written mask fixture)

**Analog:** `tests/test_masked_batch.py`.

**The anti-tautology rule** (`test_masked_batch.py:7-13`) — the single most important thing to copy;
it is the reason the Pitfall-14 off-by-one family is dead:

```python
These are hand-built exactness fixtures (Pitfall 14 — mask off-by-ones can ONLY hide
from tests that recompute the expectation): both the token/mask arrays AND the expected
final ``y`` tensor are hand-written literals, never derived in-test from the mask. The
+1 label shift must hit token AND mask slices identically so token j's mask governs the
prediction OF token j (target-space semantics, D-01).
```

**Literal-fixture layout** (`test_masked_batch.py:24-38`) — real special ids as named constants, an
index ruler comment, and a hand-written expected tensor:

```python
# Real special ids from personacore.tokenizer.special.SPECIAL_TOKENS (fixture literals).
EOS = 8184; USER = 8185; ASST = 8186; SYS = 8187
#          idx:   0    1    2     3    4    5     6    7    8     9   10    11   12   13
TOKENS = [SYS, 100, USER, 200, 201, ASST, 300, 301, USER, 400, ASST, 500, EOS, SYS]
MASK   = [  0,   0,    0,   0,   0,    0,   1,   1,    1,   0,    0,   1,   1,   0]
```

Phase-14's `test_answer_span_mask` is the single-turn version of this: `<|system|>`=0, persona=0,
first `<|user|>`=0, question=0, `<|assistant|>`=0, **answer=1, final eos=1** (14-RESEARCH F5).

**Family disjointness + token-level no-leakage** have no direct test analog. The nearest structural
precedent is `test_phase13_driver.py::test_arm_outputs_scoped` — a set-membership assertion over
driver constants. The contiguous-subsequence check runs against a **tiny synthetic bin** built in the
test (`tmp_path`), never `data/persona_train.bin`, so it stays CPU-only and data-free.

---

### `tests/test_phase14_scoring.py` (test, importlib-loaded driver)

**Analog:** `tests/test_phase13_driver.py` — this is an **exact** match; copy its whole shape.

**The scripts-load justification docstring** (`test_phase13_driver.py:13-21`) — mandatory, because it
is the documented exception to the "tests never import from `scripts/`" convention:

```python
Scripts-load justification: no other test imports from ``scripts/`` (test_demo_callback.py
states the convention), but the pre-registration constants and the gate rule MUST live in the
committed driver for git history to be the pre-registration proof (D-10) — moving them into the
package would put the experiment's rules somewhere the driver could drift from. The driver's
``main()`` is ``__main__``-guarded and every rule is a module-level pure function/constant
(the ``finetune_smoke.py`` "gate formulas as pure functions" precedent), so an
``importlib.util.spec_from_file_location`` load runs no guard and no training.
```

**The loader** (`test_phase13_driver.py:29-41`):

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "finetune_ab", _REPO_ROOT / "scripts" / "finetune_ab.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

fab = _load_driver()
```

**Exact-literal pre-registration test** (`test_phase13_driver.py:44-56`) — the constants are asserted
as literals, not recomputed:

```python
def test_preregistration_constants():
    """D-10: the gate rule and arm config are hardcoded literals, committed before any run."""
    assert fab.K == 2
    assert fab.DELTA_RET == 0.068930
    assert fab.MARGIN == 2 * 0.068930
```

**Boundary test with an exactness premise** (`test_phase13_driver.py:58-70`) — the pattern for D-19's
budget guard and D-10's threshold; the docstring explains why the naive delta construction does not
pin the operator:

```python
def test_gate_boundary():
    """The delta must land BIT-EXACTLY on MARGIN, or the test cannot tell ``>`` from ``>=``."""
    assert fab.MARGIN - 0.0 == fab.MARGIN  # the premise: this delta is exact, not rounded
    assert fab.ewc_mitigates(fab.MARGIN, 0.0) is False  # boundary FAILS — dies under >=
    assert fab.ewc_mitigates(fab.MARGIN + 1e-9, 0.0) is True  # one hair past it passes
```

**SystemExit-names-the-offender test** (`test_phase13_driver.py:101-111`):

```python
    with pytest.raises(SystemExit) as excinfo:
        fab.refuse_if_exists((missing, existing))
    assert str(existing) in str(excinfo.value)
```

---

### `tests/test_phase14_demo.py` (test, mask parity + prompt byte-identity)

**Analogs:** `tests/test_forbid_ids.py` (mask assertions), `tests/test_demo_callback.py` (the
gradio-free posture this test must *deviate* from, with justification).

**Mask assertion pattern** (`test_forbid_ids.py:145-159`, `197-211`):

```python
    assert mask.shape == (1, 16)
    assert mask.dtype == torch.bool
    assert int(mask.sum()) == 6
    assert not bool(mask[0, 15]), "eos is a registered special — it must NEVER be masked"
...
    assert int(mask.sum()) == 7645          # the real frozen tokenizer's dead-id count
```

`7645` is the pinned real-artifact number; a `torch.equal` parity assertion against
`undecodable_ids_mask(from_json(TOKENIZER_PATH), ModelConfig().vocab_size)` is the checkpoint-free
form of D-17's requirement.

**Real-artifact skip pattern** (`test_forbid_ids.py:196`) — the established escape hatch for
checkpoint-dependent tests:

```python
@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
```

**The convention this test must justify deviating from** (`test_demo_callback.py:3-6`):

```python
GPU/MPS-free and gradio-free: imports NOTHING from gradio or scripts/ — the testable demo
slice lives in the package (``generate_text_cumulative``) so CI covers it without the demo
extra installed.
```

→ **See Structural Gap S1 below. This is the one place where the existing pattern and the phase's
locked decisions collide, and the planner must resolve it explicitly.**

---

### `tests/test_recall_prompt.py` (test, tiny-GPT fixture)

**Analog:** `tests/test_demo_callback.py:32-90` (identical fixture block to
`tests/test_generation_text.py` — the docstring says "do not diverge").

**Tiny model + forced-sequence + stub tokenizer** (`test_demo_callback.py:37-89`):

```python
def _tiny_model():
    """A minimal CPU GPT — eos_id (15) < vocab_size (16), small block_size for cheap crops."""
    return GPT(ModelConfig(block_size=8, vocab_size=16, n_layer=1, n_head=1, n_embd=8, eos_id=15))

def _force_sequence(model, ids):
    """Monkeypatch model.forward so greedy decoding emits ``ids`` in order, one per step."""
    vocab = model.config.vocab_size
    state = {"i": 0}
    def _forward(idx, targets=None):
        step = state["i"]; state["i"] += 1
        forced = ids[step] if step < len(ids) else ids[-1]
        logits = torch.full((idx.size(0), idx.size(1), vocab), -1e9)
        logits[..., forced] = 1e9
        return logits, None
    model.forward = _forward  # type: ignore[method-assign]

class _RecordingTokenizer:
    """Stub tokenizer: encode records its calls; decode maps ids -> single chars by default."""
    def encode(self, text, allowed_special="all"): ...
    def decode(self, ids): ...
```

**Cumulative-stream assertions to copy** (`test_demo_callback.py:97-127`):

```python
    for prev, nxt in zip(yields, yields[1:]):
        assert nxt.startswith(prev)  # cumulative: each yield extends the last (no flicker).
    ...
    assert cumulative[-1] == "".join(deltas)
```

**Caveat:** `build_recall_prompt` tests need the **real frozen tokenizer** (special ids 8185/8186/8187
must encode atomically), not the stub — use `test_dialogue_serialize.py`'s module fixture for the
prompt half and the tiny-GPT/stub block for the `generate_text_from_ids` half.

---

## Shared Patterns

### 1. Script driver preamble — MPS fallback before torch

**Source:** `scripts/train_adapter_smoke.py:29-38`, `make_transcripts.py:23-31`,
`finetune_ab.py:27-38`, `make_retention_samples.py:35-43` (four independent copies — this is the
house idiom).
**Apply to:** `phase14_factset_gate.py`, `teach_persona.py`, `phase14_recall.py` (**not**
`personalize_demo.py` — that one is CPU-pinned and sets the gradio env var instead).

```python
import os
import pathlib

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch  # noqa: E402  (must follow the MPS-fallback env set above)
```

### 2. Repo-root-anchored path constants — never a CLI flag, never a cwd dependency

**Source:** `train_adapter_smoke.py:54-60`, `make_transcripts.py:48-54`, `finetune_ab.py:53-62`,
`tests/test_forbid_ids.py:38-41`.
**Apply to:** every new script and test.

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted checkpoint
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"     # FROZEN — never retrain
```

Trailing comments carry the trust/freshness posture; keep them.

### 3. `weights_only=False` is trusted-only, and says so

**Source:** `train_adapter_smoke.py:92-94`, `make_transcripts.py:104`, `finetune_ab.py:20-22`
(docstring) + `finetune_ab.py:207`.
**Apply to:** every script that reads `convbase_best.pt`. Shareable artifacts
(`convbase_slim.pt`, `persona_adapter.pt`) go through `load_slim` / `load_adapter`
(`weights_only=True`, `checkpoint.py:180`, `checkpoint.py:223-260`) — never `torch.load` directly.

```python
    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy objects.
    # TRUSTED-only read of the project's OWN checkpoint (T-09-11) — never a foreign file.
    # The SHAREABLE artifact path stays weights_only=True via export_adapter.
    blob = torch.load(BEST_PATH, weights_only=False)
```

Each script's **module docstring** carries a `SECURITY:` paragraph naming which file is read
untrusted-vs-trusted (`make_transcripts.py:17-18`, `finetune_ab.py:20-22`, `demo_app.py:22-26`).

### 4. `raise SystemExit`, never `assert`, for every proof check in a script

**Source:** `train_adapter_smoke.py:6-9` (docstring rationale), `finetune_ab.py:168-171` (`_prove`),
`prepare_dialog_corpus.py:18-19`, `inject.py:169-171`.
**Apply to:** all four new scripts. The rationale line to reproduce:

> every proof check is an explicit `raise SystemExit` (never a `-O`-strippable `assert`), so any
> failure exits non-zero even under `python -O` / `PYTHONOPTIMIZE`

### 5. Prompts are `encode_dialogue` id sequences, never hand-formatted strings

**Source:** `make_transcripts.py:12-15` (docstring), `make_transcripts.py:135-138` (the truncation),
`make_retention_samples.py:25-27`, `serialize.py:96-99` (`cap_persona`'s single-source docstring).
**Apply to:** `phase14_factset_gate.py`, `phase14_recall.py`, `personalize_demo.py` — all three call
`build_recall_prompt`, and D-18's byte-identity test enforces it. `generate_text*`'s
`[eos_id] + tokenizer.encode(prompt)` path (`text.py:95`) is **forbidden** for recall.

### 6. Committed report register — the "what these numbers are / what they are not" opener

**Source:** `measure_inflation.py:140-146`, `make_transcripts.py:167-173`.
**Apply to:** all four `results/phase14_*.md`.

```markdown
> **What these numbers are:** the four pre-registered D-08 inflation metrics for the FULL
> PersonaChat self_revised corpus ... tokenized through the frozen production tokenizer
> (`artifacts/tokenizer.json`) via `encode_dialogue` — the SAME path the bin builder uses, so
> gate and bins can never tokenize differently (Pitfall 4). **What they are not:** comparable
> to any other tokenizer, word-count rule, or serialization format.
```

D-11's "each control's section must open by naming the gap it closes" and D-20's three-part
reconciliation are this same register applied per-section.

### 7. New CSV file per run/arm, fieldnames fixed at run start

**Source:** `finetune_ab.py:157-165` (`_preseed_csv`), `finetune_ab.py:259` (`fieldnames =
CSV_FIELDNAMES + sorted(fns)`), `train_adapter_smoke.py:60` (`LOG_PATH ... # NEW curve CSV, own
file`).
**Apply to:** `teach_persona.py` calibration arms + real run — one CSV per arm, arm-scoped path.

### 8. Ruff conventions

`line-length 100`, `select = ["E","F","W","I"]`. Two consequences visible throughout:
- long markdown table rows are pre-composed into `row1`/`row2`/`row3` variables before the f-string
  (`measure_inflation.py:123-137`);
- every import after an `os.environ` line carries `# noqa: E402` with a reason in the comment.
Run `make format` then `make lint`.

---

## Structural Gaps (no clean analog — planner must decide)

### S1 — `tests/test_phase14_demo.py` cannot satisfy D-17/D-18's "structurally caught by CI" under the current CI config

This is the one place where a locked decision and the existing repo pattern collide. Three measured
facts:

1. **CI does not install gradio.** `.github/workflows/ci.yml:16` runs
   `pip install -e ".[cpu,dev]"`; `pyproject.toml:15-19` puts `gradio>=5,<6` in the **`demo`** extra,
   which CI never installs. Importing `scripts/personalize_demo.py` (which does `import gradio` at
   module level, and must, per the analytics-kill-switch ordering) is an `ImportError` in CI.
2. **CI has no checkpoints.** `.gitignore:14` ignores `checkpoints/`. `demo_app.build_demo()`
   raises `FileNotFoundError` at `demo_app.py:75-76` before reaching its `forbid_ids` line, and the
   same is true of `personalize_demo.build_demo()`. So a test that calls either `build_demo()` —
   including the UI-SPEC's `build_demo().stylesheets == []` offline contract test — is
   `skipif`-gated in CI by the `test_forbid_ids.py:196` precedent, i.e. **not enforced there**.
3. **The existing convention forbids exactly this import.** `tests/test_demo_callback.py:3-6` states
   it as a house rule; `tests/test_phase13_driver.py:13-21` is the only documented exception, and its
   justification (pre-registration must live in the driver) does not transfer to a demo script.

Options, in ascending cost — the planner picks and records the choice:
- **(a)** Expose the checkpoint-free slices as module-level functions in `personalize_demo.py`
  (`build_forbid_ids(tok, vocab_size)`, `render_token_panel(ids, tok)`), compare their outputs with
  `torch.equal` against `undecodable_ids_mask(...)` / `build_recall_prompt(...)` directly, and add
  `demo` to the CI extras (a one-word `ci.yml` change). Catches the real drift D-17 names (a missing
  or wrong-`vocab_size` mask; a divergent panel builder) with no checkpoint. `demo_app.py`'s own side
  stays pinned by the already-green `test_forbid_ids.py::test_undecodable_ids_mask_shape_and_content`
  + `test_real_artifact_crash_settings_no_crash` (`int(mask.sum()) == 7645`).
- **(b)** `pytest.importorskip("gradio")` + `skipif(not slim.exists())` and compare the two real
  `build_demo()`-produced masks. Strictly literal compliance with D-17's "comparing the resulting
  mask tensors directly" — but the test **skips in CI**, so the drift is not structurally caught,
  which is the property D-17 was buying.
- **(c)** Both: (a) in CI, (b) as a local-only real-artifact test in the `test_forbid_ids.py:196`
  register.

**Whichever is chosen, the plan must say so out loud** — D-17 and D-18 both justify themselves with
"structurally enforced rather than by convention," and a silently-skipped test is convention wearing
a test's clothes.

### S2 — `MASK_FRACTION_BAND` does not transfer

`prepare_dialog_corpus.py:45` pins `(0.30, 0.70)` for PersonaChat episodes. A QA teaching corpus is
answer-heavy (14-RESEARCH F5: 11–24 answer tokens in a 26–45-token episode ⇒ roughly 0.35–0.60, but
*measure it*, do not assume). Copying the literal is a false-failure risk; the plan must state the
Phase-14 band and how it was derived.

### S3 — No existing analog for a `gr.Blocks` layout, multi-output streaming, or `concurrency_id`

`demo_app.py` is `ChatInterface`-shaped: one output, no state, no `concurrency_id`. The Blocks
layout, the tuple-yield streaming shape, the post-Reset control disabling, and the shared
`concurrency_id` have **no in-repo precedent**. The planner should follow `14-UI-SPEC.md`'s Layout
and Interaction Contracts as the spec, and 14-RESEARCH Pattern 7 / Code Examples for the wiring —
not extrapolate from `demo_app.py`'s shape.

### S4 — Contradiction detector and scoring normalizer have no analog

New pure functions. Their only precedent is *structural*: `finetune_ab.py:112-122`'s
"gate formulas as pure functions in the committed driver," tested via `importlib`. The whitespace
hazard (14-RESEARCH Pattern 6: measured `'i am a mort of musician'`) means the normalizer needs its
own literal-fixture unit tests in the `test_masked_batch.py` hand-written-expectation register.

---

## Read-Only / Do-Not-Touch

| File | Why |
|------|-----|
| `scripts/demo_app.py` | **D-17: LITERALLY untouched.** Excerpt from it freely; edit nothing. The M1 honesty lock (`demo_app.py:52-53`) and the v1.0 artifact's reproducibility depend on it. |
| `scripts/finetune_ab.py` | Pre-registered and FROZEN — `git diff c3d942e HEAD -- scripts/finetune_ab.py` must stay empty (`test_phase13_driver.py:118-123`). Read-only analog. |
| `src/personacore/training/loop.py` | The frozen v1.0 loop. Phase 14 uses existing seams (`train_bin`/`train_mask_bin`/`penalty_fn`); it adds none. |
| `artifacts/tokenizer.json` | FROZEN production artifact — never retrain. |
| `results/inflation_report.md`, `results/phase13_ab_report.md`, `results/finetune_prod.csv`, `results/transcripts.md` | Recorded evidence from prior phases. Read-only inputs and format analogs. |

---

## Metadata

**Analog search scope:** `scripts/` (24 files), `tests/` (63 files), `src/personacore/` (37 modules),
`results/`, `.github/workflows/`, `pyproject.toml`, `.gitignore`
**Files read in full:** `scripts/demo_app.py`, `scripts/train_adapter_smoke.py`,
`scripts/make_transcripts.py`, `scripts/prepare_dialog_corpus.py`,
`src/personacore/dialogue/serialize.py`, `src/personacore/generation/text.py`,
`src/personacore/generation/core.py`, `tests/test_phase13_driver.py`,
`tests/test_demo_callback.py`, `tests/test_lora_toggle.py`
**Files read in targeted ranges:** `scripts/finetune_ab.py` (1-200, 200-360),
`scripts/measure_inflation.py` (60-199), `scripts/make_retention_samples.py` (1-75),
`src/personacore/lora/inject.py` (100-195), `src/personacore/checkpoint.py` (196-265),
`tests/test_forbid_ids.py` (1-90 + grep), `tests/test_dialogue_serialize.py` (1-80),
`tests/test_masked_batch.py` (1-40), `src/personacore/training/loop.py` (signature block)
**Pattern extraction date:** 2026-08-01
