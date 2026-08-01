---
phase: 13-ewc-a-b-no-forgetting-experiment
reviewed: 2026-08-01T19:29:12Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - scripts/finetune_ab.py
  - scripts/make_retention_samples.py
  - scripts/plot_phase13.py
  - tests/test_phase13_driver.py
  - tests/test_phase13_plots.py
findings:
  critical: 2
  warning: 14
  info: 0
  total: 16
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-08-01T19:29:12Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

I traced the A/B driver end-to-end against the package it calls (`training/loop.py`,
`continual/ewc.py`, `generation/core.py`, `generation/sampling.py`, `seeding.py`,
`logging.py`) specifically hunting for a second bit of difference between the arms.

**The one-bit claim in `finetune_ab.py` holds.** Both arms execute an identical
`seed_everything(SEED)` → `GPT(...)` → `load_fisher` → `EWCPenalty(...)` → step-0
`masked_perplexity` sequence before `train()`; `EWCPenalty.__call__` is RNG-free;
`extra_eval_fns` and `estimate_loss` both run inside `_rng_state()`/`_restore_rng`
snapshots in the loop; `batch_fn` draws the same number of global-numpy samples per step in
both arms. `checkpoint_extra` and `penalty_fn` are the only asymmetries and neither touches
RNG. The committed evidence corroborates it: `results/phase13_ewc/run.csv` reproduces
`results/finetune_prod.csv` to ~1e-7 at every logged step.

**The evidence *around* that driver is where it breaks down.** Two defects are provable
against the committed artifacts:

1. `make_retention_samples.py` re-seeds the sampling RNG **per arm, not per prompt**, so a
   single early stop desynchronizes the two arms' RNG streams for every remaining prompt.
   This *already happened* in the committed run (`results/phase13_retention_samples.md`
   records `1/20` stops for the EWC arm; the short warm completion is prompt 20081, the 6th
   of 10). The file's own header asserts the opposite ("both arms draw from the identical
   stream and a text difference is a weight difference") — that statement is false for the
   last four prompts of the recorded evidence.
2. The D-11 "tripwire" literals in `finetune_ab.py` (`PROD_DIALOG_4000`,
   `PROD_RETENTION_4000`) are printed and never compared. The only enforced cross-check is
   against the mutable `results/finetune_prod.csv`, i.e. exactly the thing the
   pre-registered literals were supposed to guard.

Beyond those: the frontier is correctly six points (verified — `SWEEP_LAMBDAS` +
`LAMBDA0_POINT`, and `LAMBDA0_POINT` matches its cited source in
`results/finetune_smoke_report.md:116` and `ft_lr_9e-5.csv`'s final row), but the
*forgetting curve* has the unguarded version of that same Pitfall-1 failure mode, and the
"boundary is a FAIL" gate test cannot actually distinguish `>` from `>=`. Duplication
against `finetune_dialog.py` is deliberate pre-registration and is not flagged.

## Critical Issues

### CR-01: Warm-sampling RNG desynchronizes between arms after any early stop — the recorded evidence is already affected

**Severity:** BLOCKER
**File:** `scripts/make_retention_samples.py:153-163` (with `:70-84`)

**Issue:** `seed_everything(SEED)` is called once per **arm**, then the 10 prompts are
generated sequentially inside that one stream. `next_token` draws exactly one
`torch.multinomial` per generated token from the **global** torch RNG (`generator=None`,
`sampling.py:103`), and `generate` returns early on a stop id (`core.py:77-78`). Therefore
the number of RNG draws consumed by prompt *k*'s warm completion is
`len(gen) + (1 if stopped else 0)` — **arm-dependent**. The moment one arm terminates a warm
completion early, every subsequent prompt in that arm starts from a different stream offset
than the other arm.

This is not hypothetical. In the committed artifact:

- `results/phase13_retention_samples.md` table: naive `0/20` stops, EWC `1/20`.
- The EWC arm's stop is the *warm* completion of prompt **20081** (151 chars vs a 195-244
  char band for every other warm sample; its greedy sibling is a normal 221 chars, and
  greedy consumes no RNG).
- Prompt 20081 is the **6th of 10**, so the warm completions for the last four prompts in
  the EWC arm were drawn from a shifted stream.

The header block written into that same file states: *"The warm-sampling RNG is re-seeded to
1337 before EACH arm, so both arms draw from the identical stream and a text difference is a
weight difference."* For 4 of 10 prompts, a text difference is a weight difference **plus**
an RNG-offset difference. The per-arm leakage counts (79 vs 70) inherit the same
contamination.

**Fix:** seed per `(arm, prompt)`, or better, thread an explicit generator so the global
stream is irrelevant:

```python
for story_idx, prompt_ids in prompts:
    greedy_ids, g_stop = _complete(model, prompt_ids, device, forbid, greedy=True)
    # Per-PROMPT generator: an early stop in one arm can no longer shift any later prompt.
    gen_rng = torch.Generator(device="cpu").manual_seed(SEED + story_idx)
    warm_ids, w_stop = _complete(
        model, prompt_ids, device, forbid, temperature=0.8, top_p=0.95, generator=gen_rng
    )
```

(`generate`/`next_token` already accept and thread `generator=`.) Then regenerate the
samples file and correct the header claim. If the artifact is not regenerated, the header
sentence must be replaced with the truth: streams are aligned only up to the first early
stop.

### CR-02: D-11 pre-registration "tripwire" constants are never compared — the guard does not exist

**Severity:** BLOCKER
**File:** `scripts/finetune_ab.py:103-106, 331-356`

**Issue:** The constants block declares:

```
# D-11 reproduction cross-check targets: results/finetune_prod.csv final row (step 4000).
# Read from the committed CSV at run time too — these literals are the tripwire, not the source.
PROD_DIALOG_4000 = 4.573349214207799
PROD_RETENTION_4000 = 3.891139975617828
```

`PROD_DIALOG_4000` and `PROD_RETENTION_4000` are referenced exactly once in the whole file —
inside a `print()` at line 347. The only enforced comparison (line 350) is
`abs(ret_col[-1] - prod_retention) > MARGIN`, where `prod_retention` is parsed from
`results/finetune_prod.csv` at run time. So the committed CSV is both the reference and the
thing being trusted: if `finetune_prod.csv` were edited, regenerated, or truncated, the
"tripwire" would not fire, and the driver's claim that "the driver never parses a report for
numbers" is undermined by the fact that it *does* gate on a mutable file instead of on the
pre-registered literal.

**Fix:** make the literals load-bearing — assert the CSV still matches them *before* using
the CSV as the comparison basis:

```python
_prove(
    abs(prod_dialog - PROD_DIALOG_4000) < 1e-9
    and abs(prod_retention - PROD_RETENTION_4000) < 1e-9,
    f"{PROD_CSV} final row drifted from the pre-registered D-11 literals "
    f"({prod_dialog!r}/{prod_retention!r} vs {PROD_DIALOG_4000}/{PROD_RETENTION_4000})",
)
```

Place it before the divergence check so a mutated reference CSV is a loud failure, not a
silent pass.

## Warnings

### WR-01: `_series` silently returns an empty series for a missing/blank column — unguarded Pitfall-1 on the forgetting curve

**Severity:** WARNING
**File:** `scripts/plot_phase13.py:64-71` (consumed at `:93-94`)

**Issue:** `pairs = [... for r in rows if r.get(column)]` filters on **truthiness**. If a CSV
lacks the column entirely (`r.get` → `None`) or every cell is blank, `_series` returns
`([], [])` and `ax.plot([], [])` draws a legend entry with no data — a perfectly valid,
completely empty PNG. This is the exact failure the frontier is explicitly hardened against
(`ft_lr_9e-5.csv` has no `retention_ppl`), left unguarded on the curve. Truthiness also
drops a legitimate `"0"` / `0.0` value, which today only affects `ewc_penalty` but is a
latent trap.

**Fix:**

```python
def _series(rows, column):
    if rows and column not in rows[0]:
        raise KeyError(f"{column!r} missing from CSV header — refusing to plot an empty series")
    pairs = [
        (int(float(r["step"])), float(r[column])) for r in rows if r.get(column) not in ("", None)
    ]
    if not pairs:
        raise ValueError(f"no values in column {column!r}")
    return [s for s, _ in pairs], [v for _, v in pairs]
```

### WR-02: Frontier points take `rows[-1]` with no endpoint validation

**Severity:** WARNING
**File:** `scripts/plot_phase13.py:81-83`

**Issue:** `final = _rows(RESULTS_DIR / f"ft_lam_{lam}.csv")[-1]` assumes the last row is the
1250-step endpoint. A partial/aborted or re-run sweep CSV would silently contribute a
non-endpoint to a figure whose title and caption both assert "1250-step sweep endpoints",
mixing budgets on one axis — the RESEARCH Pitfall-4 error the module docstring warns about.
Also raises a bare `IndexError` on an empty CSV.

**Fix:** add `SWEEP_STEPS = 1250` and assert it:

```python
rows = _rows(RESULTS_DIR / f"ft_lam_{lam}.csv")
final = rows[-1]
if int(float(final["step"])) != SWEEP_STEPS:
    raise ValueError(f"ft_lam_{lam}.csv final row is step {final['step']}, not {SWEEP_STEPS}")
```

### WR-03: `test_gate_boundary` cannot distinguish `>` from `>=` — the boundary contract is untested

**Severity:** WARNING
**File:** `tests/test_phase13_driver.py:55-59`

**Issue:** The test is named for the boundary but never reaches it. `5.0 - (5.0 - MARGIN)`
reconstructs to `0.13785999999999987`, strictly **below** `MARGIN = 0.13786`, so the
assertion passes on floating-point loss rather than on the exclusive comparison. Verified:
all three assertions also pass if `ewc_mitigates` were implemented with `>=`. The
pre-registered "boundary is a FAIL" rule (D-06) therefore has zero regression protection, and
the test is simultaneously brittle (a different operand pair could round the other way and
fail correct code).

**Fix:** hit the boundary exactly — with `naive_ret = MARGIN, ewc_ret = 0.0` the delta is
bit-exactly `MARGIN`:

```python
assert fab.ewc_mitigates(fab.MARGIN, 0.0) is False        # exact boundary — fails under >=
assert fab.ewc_mitigates(fab.MARGIN + 1e-9, 0.0) is True  # just past it
```

### WR-04: The claim-gate `MARGIN` is reused as the D-11 reproduction tolerance

**Severity:** WARNING
**File:** `scripts/finetune_ab.py:350-355`

**Issue:** `MARGIN = K * DELTA_RET` is defined (lines 74-85) as the minimum retention effect
size required to *claim* mitigation. Line 350 reuses it as the acceptable divergence between
this run and the production run. These are different quantities: a reproduction drift of
0.137 retention PPL — i.e. the entire effect size the phase is allowed to call a real result
— passes the D-11 check silently. Unnoticed config drift or MPS nondeterminism up to one full
claim margin is indistinguishable from a match. (Observed drift is ~1e-7, so a tolerance
five orders of magnitude tighter is achievable.)

**Fix:** a separate, purpose-named constant:

```python
# D-11 reproduction tolerance — NOT the claim margin. Observed prod-vs-rerun drift is ~1e-7
# on MPS; 1e-3 leaves headroom without swallowing a real config divergence.
REPRO_TOL = 1e-3
```

### WR-05: Step-0 retention row is trusted from `retention_anchors.json` with no anchor-identity check

**Severity:** WARNING
**File:** `scripts/finetune_ab.py:230, 249-252`

**Issue:** `dialog_ppl` at step 0 is **measured** on the loaded model, but `retention_ppl` at
step 0 is read from `results/retention_anchors.json`. The only fingerprint enforcement in the
run is `load_fisher(..., expected_fingerprint=fingerprint)`, which pins the *Fisher cache* to
`checkpoints/best.pt`. Nothing pins the anchors JSON to that same checkpoint, even though the
JSON carries its own `"git_sha"` field. If `best.pt` were ever regenerated, the curve's origin
point — and the `drift` figure printed at line 318 and plotted as the first point of both
arms — would silently come from a different model.

**Fix:**

```python
anchors = json.loads(ANCHORS_JSON.read_text(encoding="utf-8"))
_prove(
    anchors["git_sha"] == blob["git_sha"],
    f"{ANCHORS_JSON} was built at {anchors['git_sha']} but best.pt is {blob['git_sha']}",
)
```

### WR-06: `PROD_CSV` is missing from the prerequisite block — the EWC arm can die after a full training run

**Severity:** WARNING
**File:** `scripts/finetune_ab.py:182-201, 333`

**Issue:** Every other input (`DIALOG_*`, `RETENTION_BIN`, `BEST_PATH`, `FISHER_CACHE`,
`ANCHORS_JSON`) is existence-checked up front with an actionable message. `PROD_CSV` is not —
it is first opened at line 333, after ~30 minutes of training and after the artifacts are
saved. A missing/renamed `results/finetune_prod.csv` produces a bare `FileNotFoundError`
traceback instead of the D-11 comparison, and re-running requires deleting the arm outputs.

**Fix:** add to the prerequisite loop, gated on the arm:

```python
if arm == "ewc" and not PROD_CSV.exists():
    raise FileNotFoundError(f"Missing {PROD_CSV} — the read-only D-11 cross-check input.")
```

### WR-07: `dialog_col` is indexed without the `_prove` guard applied to `ret_col`

**Severity:** WARNING
**File:** `scripts/finetune_ab.py:315-319, 340-341`

**Issue:** `ret_col` gets an explicit non-empty + finite `_prove`; `dialog_col` gets none, yet
is indexed at `[0]` and `[-1]` in the summary print and again in the D-11 table. A blank or
absent `dialog_ppl` column yields `IndexError: list index out of range` instead of the loud,
named `PROOF FAILED` the module's own convention (`_prove`, line 168) exists to produce.

**Fix:** mirror the retention proof:

```python
_prove(
    dialog_col and all(math.isfinite(v) for v in dialog_col),
    f"dialog_ppl column missing or non-finite somewhere in {arm_csv}",
)
```

### WR-08: Generated samples escape their markdown blockquote — 21 of 40 blocks in the committed evidence

**Severity:** WARNING
**File:** `scripts/make_retention_samples.py:219, 229, 233`

**Issue:** Completions are interpolated as `f"> {greedy}"`. Model output routinely contains
newlines, so only the first line is quoted and the remainder renders as ordinary report prose.
Measured on the committed `results/phase13_retention_samples.md`: **21 of 40** sample blocks
have content outside the blockquote. In a git-tracked evidence file this puts raw model output
(including literal `<|user|>` / `<|assistant|>` role tokens — the very contamination being
measured) into the document body, visually indistinguishable from the script's own narrative
claims.

**Fix:** quote every line, or use a fenced block (safer — it also neutralizes any markdown in
the generated text):

```python
def _quote(text):
    return "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))
```

### WR-09: The pre-registered D-06 gate `ewc_mitigates` is never executed by any shipping code path

**Severity:** WARNING
**File:** `scripts/finetune_ab.py:112-116`

**Issue:** `ewc_mitigates` is imported only by `tests/test_phase13_driver.py`; no script
applies it to the produced numbers. Because each arm runs in its own process, no run has both
retention values, so the pre-registered verdict is computed by hand at report-writing time —
precisely the manual step the "the driver never parses a report for numbers" discipline exists
to eliminate. A transcription slip between the CSVs and the report would not be caught by
anything.

**Fix:** add a tiny third mode that reads both committed arm CSVs and applies the committed
rule, so the verdict is an artifact of code rather than of prose:

```python
if arm == "verdict":  # reads both arm CSVs, applies the pre-registered gate, prints the result
    naive_ret = _final(arm_outputs("naive")[0], "retention_ppl")
    ewc_ret = _final(arm_outputs("ewc")[0], "retention_ppl")
    print(f"ewc_mitigates({naive_ret}, {ewc_ret}) = {ewc_mitigates(naive_ret, ewc_ret)}")
    return
```

### WR-10: Arm checkpoints are loaded with no provenance/endpoint validation

**Severity:** WARNING
**File:** `scripts/make_retention_samples.py:106-115, 146-147`

**Issue:** `_load_arm` accepts whatever is at `checkpoints/phase13_{arm}_latest.pt`. Nothing
checks that the two checkpoints are the pre-registered A/B pair: no assertion that
`step == 4000`, that both carry the same anchor `git_sha` / `train_config`, or that exactly
one of them carries `ewc_lambda`. A stale or mismatched-budget checkpoint would produce a
plausible-looking samples file with the wrong step printed in the table — the driver's own
`refuse_if_exists` discipline protects the *writing* side but nothing protects the *reading*
side here.

**Fix:**

```python
model, model_cfg, step = _load_arm(ckpt_path, device)
if step != 4000:
    raise SystemExit(f"[make_retention_samples] {ckpt_path} is step {step}, not the 4000-step endpoint")
```

plus a cross-arm equality check on `blob["git_sha"]` / `blob["train_config"]`, and
`("ewc_lambda" in blob) == (label.startswith("ewc"))`.

### WR-11: Both test modules execute the scripts at import time, mutating process-global state for the whole session

**Severity:** WARNING
**File:** `tests/test_phase13_driver.py:38`, `tests/test_phase13_plots.py:32`

**Issue:** `fab = _load_driver()` and `pp = _load_plots()` run at module scope, i.e. during
pytest collection. Side effects leak into every other test in the session:
`os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")` (finetune_ab.py:36) and
`matplotlib.use("Agg")` (plot_phase13.py:27) are process-wide. Collection-time execution also
converts any import failure in the scripts into a collection error rather than a test failure,
and it imports torch during collection in a module documented as "GPU/MPS-free".

**Fix:** load lazily in a module-scoped fixture:

```python
@pytest.fixture(scope="module")
def fab():
    return _load_driver()
```

### WR-12: The plot smoke test cannot fail on an empty figure

**Severity:** WARNING
**File:** `tests/test_phase13_plots.py:59-69`

**Issue:** The only assertions are `path.exists()` and `st_size > 0`. Matplotlib writes a
valid, non-empty PNG for a figure containing no data, so this test passes under exactly the
WR-01 failure mode (a renamed/missing `retention_ppl` column producing empty series). The
frontier's six-point regression is well pinned; the curve's has no equivalent.

**Fix:** pin the curve series the same way the frontier is pinned:

```python
def test_curve_series_are_complete():
    for _label, path, _color in pp.ARMS:
        rows = pp._rows(path)
        for col in ("retention_ppl", "dialog_ppl"):
            steps, values = pp._series(rows, col)
            assert len(steps) == 17          # step 0 + 16 eval points at interval 250
            assert steps[0] == 0 and steps[-1] == 4000
```

### WR-13: Hardcoded interpretive conclusions are written into the evidence file regardless of what was measured

**Severity:** WARNING
**File:** `scripts/make_retention_samples.py:198-212`

**Issue:** The prose block appended after the proxy table asserts results unconditionally:
`"**Both arms leak heavily**"` and `"A 0.00-0.05 stop-id fraction is expected"`. These
sentences are emitted whatever the measured `leakage` and `n_stopped` values are. They happen
to be consistent with the committed run (79/70 leakage, 0.00/0.05 stops), but any regeneration
— which is exactly what a reviewer or a fixed CR-01 triggers — can produce a git-tracked
evidence file whose narrative contradicts the table directly above it. A generator that writes
its own conclusions is not measuring them.

**Fix:** derive the sentence from the data, or move the interpretation out of the generator
and into the report where a human owns it:

```python
leaks = [leakage for _n, _t, leakage, _s in proxies.values()]
verdict = "**Both arms leak heavily**" if min(leaks) > 0 else f"Measured leakage per arm: {leaks}"
```

### WR-14: `preflight_device(strict=True)` blocks sample regeneration on a CPU-only host

**Severity:** WARNING
**File:** `scripts/make_retention_samples.py:136`

**Issue:** `strict=True` raises on a machine with no accelerator (preflight.py's documented
CPU-only behavior). That gate exists for multi-hour training runs; this script is 40
generations of 128 tokens and runs fine on CPU. As written, the git-tracked evidence in
`results/phase13_retention_samples.md` cannot be regenerated or independently verified on CI
or on any non-Apple, non-CUDA machine — at odds with the phase's "regenerates from the repo
alone" posture.

**Fix:** `preflight_device(strict=False)` here (still prints the resolved device summary), or
thread a `--allow-cpu` escape hatch.

---

_Reviewed: 2026-08-01T19:29:12Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
