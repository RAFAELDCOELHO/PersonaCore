---
phase: 15-figures-writeup
reviewed: 2026-08-02T21:02:13Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - scripts/phase15_stats.py
  - scripts/extract_deltas.py
  - scripts/plot_phase15.py
  - tests/test_phase15_stats.py
  - tests/test_phase15_plots.py
  - tests/test_phase15_docs.py
findings:
  critical: 2
  warning: 9
  info: 6
  total: 17
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-08-02T21:02:13Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Six files, ~1,400 lines, of which the statistical core is the deliverable. I verified the parts
that are load-bearing rather than taking the docstrings' word for them:

**What holds up (independently verified, not assumed):**

- `spearman` is numerically correct. Compared against an independent tie-corrected reference over
  300 heavy-tie random cases: max absolute deviation `2.22e-16`. The `[1,1,2,3]` divergence from
  `continual/fisher.py::_spearman` is real and correctly handled.
- The permutation add-one correction is right. Exhaustive check on n=5 (all 120 permutations) gives
  exact p = 0.13333; the Monte-Carlo estimator at 200k shuffles returns 0.13297.
- Seeding is genuinely deterministic; `permutation_p` and `bootstrap_ci` both return bit-identical
  results across calls with the same seed, and neither touches the global RNG.
- **Pre-registration integrity holds.** `git show 0e1af98:scripts/phase15_stats.py` carries
  byte-identical `N_CELLS` / `PREDICTED_SIGN` / `SEED` / `N_PERM` / `N_BOOT` / `CI_ALPHA` /
  `SPEARMAN_METHOD` / `CI_METHOD` / `PROJECTIONS`, and `_rank` / `spearman` / `permutation_p` /
  `bootstrap_ci` / `ewc_dodges_high_fisher` diff clean against HEAD.
  `results/phase15_norms.json` does not exist at `0e1af98` or at `90d1bce`. The claim is true.
- The committed `## Phase 15 Addendum` in `results/phase13_ab_report.md` is **byte-identical** to a
  fresh `render_verdict_section(...)` today. It was not hand-edited.
- `test_extraction_reproduces_the_committed_artifact` actually runs on this machine (0.66 s, not
  skipped) and passes — the committed artifact really does correspond to the extraction script.
- `ruff check` and `ruff format --check` are clean on all six files.

**What does not hold up.** The failures are concentrated in two places: the statistics primitives
fail *open* rather than *loud* on corrupted input (a NaN cell yields a plausible finite ρ, not a
NaN), and the correctness guards `extract_deltas.py` builds for the adapter block are simply absent
for the two blocks the headline verdict is computed from — while a free, exact check for one of them
(`theta_star`) sits unused inside a checkpoint the script already loads. Separately, the phase's own
headline numbers (ρ, CI, p) are the only numbers in this repo that are restated in committed prose
without a test binding them to their source, even though `test_headline_numbers_match_sources` does
exactly that for README's three.

---

## Critical Issues

### CR-01: `_rank` silently ranks NaN as the largest value — a corrupted cell yields a plausible ρ instead of a NaN

**Severity:** BLOCKER
**File:** `scripts/phase15_stats.py:126-147` (tie loop at `142`), reachable through
`spearman:157`, `permutation_p:171-172`, `bootstrap_ci:198`

**Issue:** `np.argsort` sorts NaN to the end, so `_rank` assigns a NaN cell the *highest* rank and
returns an all-finite rank vector. `np.corrcoef` then produces a finite, entirely plausible
coefficient. There is no exception, no warning, and no NaN to notice. Worse, because `NaN != NaN`,
the tie loop at line 142 never groups two NaNs, so multiple corrupted cells receive distinct
ordinal ranks.

Demonstrated:

```
_rank([1.0, nan, 2.0, nan])                     -> [0. 2. 1. 3.]   # NaNs ranked highest, untied
spearman([1..6], [nan, 2, 3, 4, 5, 6])          -> 0.14285714285714288   (finite, no warning)
spearman([1..6], [1, 2, 3, 4, 5, nan])          -> 1.0                   (finite, no warning)
```

The docstring documents the tie transform in detail and says nothing about NaN, so a future caller
has no way to know the precondition exists. The only thing standing between a corrupted artifact and
a published ρ is the `np.isfinite` check in `_cell` (`phase15_stats.py:296`) — a *different*
function, in a *different* code path, with **zero test coverage** (see WR-01). This is precisely the
"silently produces a plausible-but-wrong verdict" failure the phase exists to prevent, sitting in the
one function whose correctness is the deliverable.

**Fix:** Make the precondition structural in the primitive itself, not delegated to one caller.

```python
def _rank(x):
    x = np.asarray(x, dtype=np.float64)
    if not np.all(np.isfinite(x)):
        bad = np.flatnonzero(~np.isfinite(x)).tolist()
        raise SystemExit(
            f"[phase15_stats] _rank received non-finite values at positions {bad} — "
            "numpy sorts NaN last, so ranking would silently treat them as the LARGEST "
            "cells and return a plausible finite rho from corrupted data."
        )
    order = np.argsort(x, kind="stable")
    ...
```

Add the regression to `tests/test_phase15_stats.py::test_spearman_known_answers`:

```python
with pytest.raises(SystemExit):
    st.spearman([1.0, float("nan"), 2.0], [1.0, 2.0, 3.0])
```

---

### CR-02: `naive`/`ewc` blocks compute ΔW against an **unverified** W₀ — the guard the module calls "the single most important check" is applied only to the block that needs it least

**Severity:** BLOCKER
**File:** `scripts/extract_deltas.py:278-285` (loads), `317-340` (blocks), `149-166`
(`require_fingerprint`)

**Issue:** The module docstring (`extract_deltas.py:14-31`) names the hazard explicitly — *"Using
`best.pt` here would produce a wrong-by-construction ratio that still renders and still looks
plausible"* — and `require_fingerprint` calls itself *"the single most important check in this
script."* That check is applied to exactly one of the three delta blocks: `adapter`
(line 285).

The `naive` and `ewc` blocks (lines 317-340) call `full_ft_cells(naive_model, best_model)` and
`full_ft_cells(ewc_model, best_model)` with **nothing** verifying that `phase13_naive_latest.pt` and
`phase13_ewc_latest.pt` were actually trained from `best.pt`. `naive_fp` and `ewc_fp` are *recorded*
into the artifact (lines 325, 337) but never *compared* against anything. If `best.pt` is ever
re-exported, or an arm checkpoint is swapped, every cell in both blocks becomes a wrong-by-
construction ratio that renders fine and looks plausible — and these are the two blocks that
produce the VIZ-03 figure **and** feed `load_pairs`' `naive - ewc` reduction, i.e. the pre-registered
D-09 correlation verdict. The one guarded block, `adapter`, feeds neither.

The check is free for the EWC arm: `checkpoints/phase13_ewc_latest.pt` already carries `theta_star`,
the anchor weights the penalty pulls toward. Verified on this machine:

```
theta_star keys: 100   best.pt model keys: 101
max |theta_star - best.pt| = 0.0        # exact bit match — the check would pass today
```

So today's numbers are correct; the guard that proves it is missing. `phase13_naive_latest.pt`
carries no base pointer at all (`train_config` records only lr/batch/steps/seed), so the naive arm
needs its provenance asserted differently — at minimum a recorded, checked `w0_fingerprint`.

**Fix:** Assert the anchor for the EWC arm from data already in memory, and fail loud:

```python
ewc_blob_theta = ewc_extra["theta_star"]   # _load_model must return it, or load separately
for key, w0 in best_model.items():
    if key in ewc_blob_theta and not torch.equal(ewc_blob_theta[key], w0):
        raise SystemExit(
            f"[extract_deltas] {EWC_LATEST}'s theta_star diverges from {BEST_PATH} at {key!r}: "
            "the EWC arm was NOT anchored at this W0, so every 'ewc' cell would be a "
            "wrong-by-construction ratio that still renders. Do NOT relax this check."
        )
```

For the naive arm, record and verify a base fingerprint in `finetune_ab.py`'s checkpoint writer, and
have `extract_deltas` require it — same shape as `require_fingerprint`. Until that lands, state in
the artifact that the naive block's W₀ is asserted by convention, not verified, so the report does
not imply a guarantee that does not exist.

---

## Warnings

### WR-01: The phase's headline numbers are the only ones in the repo restated in prose without a test binding them to their source; `load_pairs`, `_cell` and `render_verdict_section` have zero test coverage

**File:** `tests/test_phase15_stats.py:46-130`, `tests/test_phase15_docs.py:338-357`,
`docs/REPORT.md:805-819`

**Issue:** Three separate gaps that compound:

1. `docs/REPORT.md:808-810` hardcodes `ρ = 0.801544` and `CI [0.597984, 0.920291]`. Nothing computes
   or checks them. `test_headline_numbers_match_sources` pins README's three numbers to their cited
   source reports — the exact discipline D-16 exists to enforce — but `_HEADLINE_NUMBERS`
   (`test_phase15_docs.py:338-357`) does not include ρ, the CI, or p. The phase whose entire premise
   is "the number cannot be resolved in whichever direction looks better" leaves its own number
   unpinned.
2. Nothing asserts that the committed addendum equals a fresh `render_verdict_section(...)`. I
   verified manually that it does today (byte-identical); a hand-edit tomorrow goes green.
3. `load_pairs`, `_cell` and `render_verdict_section` are never imported by any test —
   `grep -n "load_pairs\|render_verdict_section\|_cell\b" tests/*.py` returns nothing. The T-15-07
   malformed-artifact guards (`phase15_stats.py:240-300`), which CR-01 shows are the *only* thing
   preventing a NaN from reaching `_rank`, are entirely unexercised. The `GATE MISSES` branch
   (`phase15_stats.py:412-424`) has never been executed by a test either — I smoke-tested it by hand
   and it renders, but the T-15-09 mitigation is unenforced.

**Fix:** Add to `tests/test_phase15_stats.py`:

```python
def test_committed_verdict_matches_the_preregistered_renderer():
    art = json.loads((_REPO_ROOT / "results/phase15_norms.json").read_text(encoding="utf-8"))
    f, r = st.load_pairs(art)
    rho, p = st.permutation_p(f, r, n_perm=st.N_PERM, seed=st.SEED)
    lo, hi, n_deg = st.bootstrap_ci(f, r, n_boot=st.N_BOOT, seed=st.SEED)
    report = (_REPO_ROOT / "results/phase13_ab_report.md").read_text(encoding="utf-8")
    assert f"ρ = **{rho:.6f}**" in report
    assert f"[{lo:.6f}, {hi:.6f}]" in report
    assert f"{rho:.6f}" in (_REPO_ROOT / "docs/REPORT.md").read_text(encoding="utf-8")

@pytest.mark.parametrize("mutate", [
    lambda a: a["blocks"].pop("adapter"),
    lambda a: a["blocks"]["fisher"]["cells"]["0"].pop("q_proj"),
    lambda a: a["blocks"]["ewc"]["cells"]["2"].__setitem__("fc_in", None),
])
def test_load_pairs_refuses_malformed_artifacts(mutate): ...   # each must SystemExit

def test_miss_branch_renders_the_preregistered_wording():
    out = st.render_verdict_section(0.15, 0.03, -0.1, 0.4, 0, {}, "2026-01-01")
    assert "GATE MISSES" in out
    assert "suggestive but not statistically demonstrated at n = 36" in " ".join(out.split())
```

---

### WR-02: `torch.load(weights_only=False)` is avoidable — a 4-entry `safe_globals` allowlist loads every field the script reads

**File:** `scripts/extract_deltas.py:145`

**Issue:** `_load_model` opens four checkpoints with the unrestricted unpickler, which executes
arbitrary code on load. The module SECURITY paragraph (lines 39-48) justifies it as "the full resume
checkpoints carry pickled optimizer/RNG/numpy objects that torch>=2.6's `weights_only=True` default
rejects." That premise is true of the *default*, but not of the available API. I confirmed the only
blocked global is `numpy._core.multiarray._reconstruct` (numpy RNG state), and that an explicit
allowlist loads all four files with `weights_only=True`:

```
weights_only=True (default)          -> Unsupported global: numpy._core.multiarray._reconstruct
weights_only=True + safe_globals([_reconstruct, np.ndarray, np.dtype, np.dtypes.UInt32DType])
  -> OK; top-level keys: ['git_sha','model','model_config','optimizer','rng','scaler',
                          'scheduler','schema_version','step','train_config','val_loss']
```

Every field `_load_model` and `_fingerprint` touch (`model`, `git_sha`, `step`, `val_loss`) is
present. These `.pt` files are hundreds of MB that travel between the Kaggle fallback path and the
laptop; the project already routes the adapter and the Fisher cache through `weights_only=True`
choke points precisely to avoid this. This is the last unrestricted read in the Phase-15 path and it
does not need to be.

**Fix:**

```python
import numpy as np
import numpy._core.multiarray as _np_multiarray

# The exact globals the resume checkpoints' numpy RNG state needs — an explicit allowlist, never
# weights_only=False. Nothing here executes code on load.
_SAFE_GLOBALS = [_np_multiarray._reconstruct, np.ndarray, np.dtype, np.dtypes.UInt32DType]


def _load_model(path):
    with torch.serialization.safe_globals(_SAFE_GLOBALS):
        blob = torch.load(path, map_location="cpu", weights_only=True)
    return blob["model"], _fingerprint(blob)
```

---

### WR-03: `permutation_p` reports **maximal** significance when the observed statistic is NaN

**File:** `scripts/phase15_stats.py:174-177`

**Issue:** Every comparison against `nan` is `False`, so `ge` stays 0 and the add-one correction
returns `1/(n_perm+1)`. At the pinned `N_PERM = 100_000` that is `p = 0.000010` — the most
significant value the estimator can emit — printed next to `ρ = nan` in the verdict section. A
degenerate input therefore fails *open* on the p, not closed. Confirmed:

```
permutation_p([1.0]*36, range(36), n_perm=500, seed=1337) -> obs=nan, p=0.001996  (= 1/501)
```

The gate itself is safe (`rho > 0` is `False` for NaN), but the R5 arbitration explicitly puts this p
into the published record as descriptive evidence, and there it reads as overwhelming support.

**Fix:**

```python
obs = float(np.corrcoef(ra, rb)[0, 1])
if not np.isfinite(obs):
    raise SystemExit(
        "[phase15_stats] the observed rank correlation is not finite (a zero-variance input "
        "makes corrcoef undefined). Refusing to emit p = 1/(n_perm+1), which would read as "
        "maximal significance."
    )
```

---

### WR-04: `bootstrap_ci` raises a bare `IndexError` when every resample is degenerate

**File:** `scripts/phase15_stats.py:199-202`

**Issue:** The docstring says degenerate resamples are dropped and the count *reported* "rather than
letting a nan silently propagate into a quantile." When `kept` ends up empty, `np.quantile` raises
`IndexError: index -1 is out of bounds for axis 0 with size 0` — an unnamed traceback with no
mention of the artifact, in a module where every other failure is a named `SystemExit`. Also
triggered by `n_boot=0`. Confirmed:

```
bootstrap_ci([1.0, 1.0], [1.0, 2.0], n_boot=50, seed=1) -> IndexError
bootstrap_ci([1.,2.,3.], [3.,2.,1.], n_boot=0, seed=1)  -> IndexError
```

**Fix:**

```python
kept = out[np.isfinite(out)]
if kept.size == 0:
    raise SystemExit(
        f"[phase15_stats] all {n_boot} bootstrap resamples were degenerate (zero variance) — "
        "no percentile interval exists. The input has too few distinct values."
    )
```

---

### WR-05: `plot_phase15._load_artifact` validates shape but not values — a NaN cell renders an all-grey panel under a titled axis with no error

**File:** `scripts/plot_phase15.py:89-116` (validation), `142-146` (`_own_norm`), `127-133` (`_grid`)

**Issue:** The function's own docstring says *"Never degrades silently"* and *"An empty panel under a
titled axis is a figure that lies."* It checks block presence, cell count, layer rows and projection
names — and never looks at a value. Confirmed against a mutated copy of the committed artifact:

```
cell = None  -> _load_artifact ACCEPTS it; _grid then raises a bare TypeError from float(None)
cell = NaN   -> _load_artifact ACCEPTS it; _own_norm returns LogNorm(vmin=0.1133, vmax=nan)
```

`flat[flat > 0.0]` excludes NaN (so `vmin` looks fine) but `flat.max()` is NaN, and every cell
normalizes to NaN → masked → the entire panel paints `set_bad` grey under its title and colorbar.
That is exactly the figure-that-lies the docstring forbids. Related edge: when only one strictly
positive cell exists, `_own_norm` builds `LogNorm(vmin=5.0, vmax=5.0)` without raising and maps
everything to 0.

**Fix:** Add the value check to the existing per-block loop (line 102-110), reusing the same
name-the-offender style:

```python
for projection, value in row.items():
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(
            f"{path}: block {name!r} cell (layer {layer}, {projection}) is {value!r}, not a "
            "finite number — a NaN cell renders as an all-grey panel under a titled axis"
        )
```

and guard `_own_norm` against a degenerate range:

```python
vmin, vmax = float(positive.min()), float(flat.max())
if not (vmin < vmax):
    raise ValueError(f"{label}: log range is degenerate (vmin={vmin}, vmax={vmax})")
```

---

### WR-06: `test_seeded_results_are_reproducible`'s different-seed meta-guard is a false-failure risk

**File:** `tests/test_phase15_stats.py:88-90`

**Issue:** `permutation_p` returns `(obs, p)` where `obs` is seed-independent, so the `!=` assertion
reduces to "the two seeds produce different p". With the fixture's strong correlation and
`n_perm=2000`, p is determined by an exceedance count of 0, 1 or 2 — so two seeds very often produce
an *identical* p and the assertion fails **for a correct implementation**. Measured across adjacent
seeds:

```
seed 1337 p=0.0009995   seed 1338 p=0.0004998   seed 1339 p=0.0004998
seed 1340 p=0.0004998   seed 1341 p=0.0009995   seed 1342 p=0.0004998
seed 1343 p=0.0004998   seed 1344 p=0.0004998   seed 1345 p=0.0009995
```

7 of 13 adjacent seeds collide. The test passes today only because `SEED`/`SEED+1` happen to land on
different counts. Any change to the fixture, to `n_perm`, or to `SEED` turns it red with a message
about randomness that has nothing to do with the actual behavior.

**Fix:** Assert on the resampling stream, not on a low-resolution derived statistic:

```python
# Different seeds must draw a different shuffle sequence. Comparing p at n_perm=2000 is a
# coin flip: the exceedance count is 0-2, so two correct seeds routinely give the SAME p.
lo1, hi1, _ = st.bootstrap_ci(a, b, n_boot=1000, seed=st.SEED)
lo2, hi2, _ = st.bootstrap_ci(a, b, n_boot=1000, seed=st.SEED + 1)
assert (lo1, hi1) != (lo2, hi2)
assert st.permutation_p(a, b, n_perm=50, seed=st.SEED)[1] == st.permutation_p(
    a, b, n_perm=50, seed=st.SEED
)[1]
```

(The `bootstrap_ci` half of the meta-guard is sound as written — its output is continuous.)

---

### WR-07: The D-07 subprocess probe cannot distinguish "imports torch" from "failed to import at all"

**File:** `tests/test_phase15_plots.py:338-352`

**Issue:** The probe ends with `sys.exit(1 if 'torch' in sys.modules else 0)`, but an uncaught
exception during `exec_module` also exits with 1. Both cases hit
`assert result.returncode == 0, "plotting module transitively imports torch — D-07 violated"`.
A plotting module broken by a syntax error, a missing matplotlib, or a bad artifact path reports as
a D-07 security-control violation. Confirmed: pointing the probe at a nonexistent file exits 1.

The docstring calls this check "the one that cannot be fooled" — it can be fooled into a wrong
diagnosis, which is how a real D-07 regression gets dismissed as "probably just the import."

**Fix:** Use a distinct exit code and assert on it, so the two conditions are separable:

```python
probe = (
    "import importlib.util, sys;"
    "spec = importlib.util.spec_from_file_location('p15', 'scripts/plot_phase15.py');"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
    "sys.exit(7 if 'torch' in sys.modules else 0)"
)
result = subprocess.run([sys.executable, "-c", probe], cwd=_REPO_ROOT,
                        capture_output=True, text=True)
assert result.returncode != 1, f"the probe itself crashed, not a D-07 result\n{result.stderr}"
assert result.returncode == 0, f"plot_phase15 transitively imports torch — D-07 violated"
```

---

### WR-08: `_cell` accepts JSON strings and booleans while claiming a non-numeric cell is fatal

**File:** `scripts/phase15_stats.py:287-300`

**Issue:** The docstring states *"a non-numeric or non-finite cell is fatal and named."* `float()`
coerces both `"1.5"` and `True`, so neither is fatal. Confirmed against a mutated artifact:

```
blocks.fisher.cells["0"]["q_proj"] = "1.5"  -> ACCEPTED as 1.5
blocks.naive.cells["0"]["q_proj"]  = True   -> ACCEPTED as 1.0
```

`True` silently becoming `1.0` is the more dangerous of the two, because a JSON `true` is a
plausible artifact-corruption outcome and `1.0` is inside the real value range for the `naive` block.
The stated T-15-07 guarantee is stronger than the code provides.

**Fix:**

```python
value = blocks[name]["cells"][str(layer)][projection]
if isinstance(value, bool) or not isinstance(value, (int, float)):
    raise SystemExit(
        f"[phase15_stats] {NORMS_JSON.name}: {key.format(name)} is {value!r} "
        f"({type(value).__name__}), not a JSON number."
    )
value = float(value)
```

---

### WR-09: `extract_deltas` raises bare `KeyError`s on malformed checkpoints, contradicting its "every proof check is an explicit `raise SystemExit`" claim

**File:** `scripts/extract_deltas.py:131-133` (`_fingerprint`), `157` (`require_fingerprint`),
`184-186` (`adapter_cells`), `203` (`fisher_cells`), `293-295` (`lora_config`)

**Issue:** The module docstring (lines 50-51) states *"Every proof check below is an explicit
`raise SystemExit` and never an `-O`-strippable bare `assert`, so a failure exits non-zero even under
`PYTHONOPTIMIZE`."* Several failure paths are neither — they are unhandled `KeyError`s that produce a
raw traceback naming only a dict key:

- `_fingerprint(blob)` — `blob["git_sha"]` / `["step"]` / `["val_loss"]` on a checkpoint predating
  QA-02 provenance
- `require_fingerprint` — `adapter_art["base_fingerprint"]`
- `adapter_cells` — `adapter[f"{prefix}.lora_A"]` on an adapter injected at different targets
- `fisher_cells` — `fisher[key]` on a Fisher cache keyed differently
- `lora_config["alpha"] / lora_config["r"]` — also a `ZeroDivisionError` if `r == 0`

The exit code is still non-zero so nothing runs on bad data, but the "names the specific offender"
discipline the rest of the file maintains breaks exactly where an operator has the least context.

**Fix:** Wrap the lookups with named errors, e.g.:

```python
def _fingerprint(blob):
    missing = {"git_sha", "step", "val_loss"} - blob.keys()
    if missing:
        raise SystemExit(
            f"[extract_deltas] checkpoint is missing the QA-02 provenance trio {sorted(missing)} "
            "— it predates the fingerprint convention and cannot anchor a Phase-15 block."
        )
    return {k: blob[k] for k in ("git_sha", "step", "val_loss")}
```

and the same shape for the `lora_A`/`lora_B`/`fisher[key]` lookups, naming the missing key and the
(layer, projection) it belongs to.

---

## Info

### IN-01: The four-block name tuple is duplicated four times, in two different orderings

**File:** `scripts/extract_deltas.py:395`, `scripts/plot_phase15.py:56`,
`scripts/phase15_stats.py:102`, `tests/test_phase15_plots.py:65`

**Issue:** `("adapter", "naive", "ewc", "fisher")` appears three times as a tuple plus once
re-sorted as `("adapter", "ewc", "fisher", "naive")`. `extract_deltas.prove()` inlines it rather
than naming a constant, unlike its two siblings. `PROJECTIONS` is likewise duplicated, but that one
is documented as deliberate pre-registration pinning; the block names carry no such justification.

**Fix:** Give `extract_deltas` a module-level `BLOCKS` constant alongside `PROJECTIONS` and use it in
both `build_artifact` and `prove`.

### IN-02: Extraction and plotting overwrite committed artifacts with no confirmation

**File:** `scripts/extract_deltas.py:435-437`, `scripts/plot_phase15.py:299`

**Issue:** `python scripts/extract_deltas.py` silently overwrites `results/phase15_norms.json`, the
committed D-05 hand-off boundary and provenance record; `plot_phase15.main()` does the same to the
two committed PNGs. `phase15_stats.py:335` cites the project convention that `--force` is mandatory
on every legitimate re-drive. Git makes it recoverable, so this is cheap insurance, not a hazard.

**Fix:** Require `--force` when `out_path` exists and its `git_sha` differs from `git_sha()`.

### IN-03: `plot_phase15.main()` reads and validates the artifact twice

**File:** `scripts/plot_phase15.py:205`, `245`, `299`

**Issue:** `plot_adapter_delta` and `plot_fisher_ewc` each call `_load_artifact()` with no argument,
so `main()` parses and re-validates the same JSON twice. Harmless, but it also means the two figures
could in principle be built from different file contents if the artifact changed between calls.

**Fix:** Have `main()` load once and pass the artifact into both plot functions (keep the default
`None` so each remains independently runnable).

### IN-04: `_github_anchor` drops underscores, which GitHub keeps

**File:** `tests/test_phase15_docs.py:360-366`

**Issue:** `c.isalnum() or c == "-"` discards `_`. GitHub's anchor algorithm preserves underscores,
so any future heading containing one (very likely here — `q_proj`, `fc_in`, `nonpositive_cells` all
appear in headings elsewhere in this repo) produces a wrong expected anchor and a false failure.
`isalnum()` is also true for non-ASCII letters, which GitHub handles differently.

**Fix:** `if c.isalnum() or c in "-_"`.

### IN-05: `_anchored_section` interpolates `stop` into a regex unescaped

**File:** `tests/test_phase15_docs.py:104`

**Issue:** `rf"^{re.escape(heading)}\b.*?(?=^{stop}|\Z)"` escapes `heading` but not `stop`. Both
current call sites pass deliberate regex fragments (`r"## "`, `r"#{2,3} "`), so it works — but the
asymmetry invites a future caller to pass a literal heading and get silent mis-anchoring rather than
an error. A related note: `stop=r"#{2,3} "` does not stop at a `# ` (h1) heading.

**Fix:** Document the parameter as "a regex fragment, not a literal" in the docstring, or take a
compiled pattern.

### IN-06: A duplicated addendum append is undetected by `test_verdict_section_is_dated_and_separated`

**File:** `scripts/phase15_stats.py:454`, `tests/test_phase15_docs.py:435-487`

**Issue:** `main()` only prints; the append to `results/phase13_ab_report.md` is a manual `>>`. Two
runs produce two addenda. `_anchored_section` matches only the first (the second's `## ` heading
stops it), and `headings[-1].startswith(_ADDENDUM_HEADING)` is still true, so the test passes.
Simulated on a doubled copy of the real report:

```
addendum count: 2
anchored section still one branch: True
last heading still the addendum: True
```

**Fix:** `assert report.count(_ADDENDUM_HEADING) == 1, "the Phase 15 addendum was appended twice"`.

---

_Reviewed: 2026-08-02T21:02:13Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
