---
phase: 15-figures-writeup
reviewed: 2026-08-02T21:46:00Z
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
  info: 5
  total: 16
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-08-02T21:46:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Re-review of six byte-unchanged files. This pass is calibrated against three facts I re-confirmed
by execution rather than inherited: the artifact path *is* guarded against non-finite values
(`load_pairs` → `_cell` raises a coordinate-naming `SystemExit`), `load_fisher` *does* raise on an
anchor-fingerprint mismatch so `best.pt` is transitively validated on every run, and the suite is
green (15 passed for the three phase-15 files; 407/1 skipped overall). Several findings the prior
pass filed as CRITICAL are correctly contained and are downgraded here with the containment named.

The statistical core is sound where it matters. I re-verified: `spearman` is tie-correct
(`[1,1,2,3]` vs `[1,2,3,4]` → `0.9486832980505139`), seeding is local and deterministic, the
add-one permutation correction is right, and `load_pairs` + `spearman` on the committed artifact
reproduces `0.801544` exactly in 0.2 ms. `ruff check` is clean on all six files.

What does not hold up divides cleanly in two.

**Correctness.** `extract_deltas.py` builds an explicit, well-argued hard guard for the *adapter*
block's W₀ ("a wrong denominator still renders and still looks plausible") and then omits the
equivalent guard for the two blocks the headline verdict is actually computed from. I confirmed
the exact discriminators are sitting inside blobs `_load_model` already deserializes and discards:
`phase13_ewc_latest.pt` carries `ewc_lambda = 0.01` and a `theta_star` that is bit-identical to
`best.pt` for all 36 figure keys; `phase13_naive_latest.pt` carries neither. The correct threat
model was applied to one block out of three.

**Verification.** There is not one negative-path test in this phase. `grep -c 'pytest.raises'`
across all three test files returns zero. The three modules contain roughly twenty explicit
fail-loud guards, presented across their docstrings as the phase's central safety property
(T-15-07 tampering; "an empty panel under a titled axis is a figure that lies"), and none is
exercised. I confirmed the practical consequence: `plot_phase15` renders a plausible 107 KB PNG
from an artifact containing `-inf`, `0.0`, a negative cell, *or a string-typed cell*. And the one
number this phase exists to produce, ρ = 0.801544, is restated at five committed sites with no
test binding it to its source — while three lesser numbers are protected by
`test_headline_numbers_match_sources`.

Note on the byte-freeze: `scripts/phase15_stats.py` is pre-registration material (last touched at
`90d1bce`, one commit after `PREREG_COMMIT = 0e1af98`). Findings CR-02, WR-04, WR-06, WR-09 and
IN-01 touch it. Every one of them is additive or test-side and none changes the rule, the seed, the
sign, the counts or the gate — but any edit to that file needs an explicit dated amendment record.
Where a fix can be made entirely outside the frozen file, I say so.

---

## Critical Issues

### CR-01: `extract_deltas` never verifies which arm each full-fine-tune checkpoint is, and discards the exact proof

**File:** `scripts/extract_deltas.py:136-146, 190-196, 278-281, 317-340`

**Issue:** The `naive` and `ewc` blocks are built by *file path convention only*:

```python
naive_model, naive_fp = _load_model(NAIVE_LATEST)   # "λ=0 arm" — asserted nowhere
ewc_model,   ewc_fp   = _load_model(EWC_LATEST)     # "λ=0.01 arm" — asserted nowhere
...
"naive": _block(full_ft_cells(naive_model, best_model), regime="full_finetune_naive", ...)
"ewc":   _block(full_ft_cells(ewc_model,   best_model), regime="full_finetune_ewc_lambda_0.01", ...)
```

The `regime` strings are hardcoded to the *constant name*, not derived from anything in the file.
Nothing checks that `EWC_LATEST` is an EWC arm, that `NAIVE_LATEST` is not, or that either arm
actually started from `best.pt`. If the two paths were transposed — by a rename, a restore from a
backup, a re-run of `finetune_ab.py` with the arm argument swapped — `reduction = naive - ewc`
inverts, ρ flips to ≈ −0.80, `ewc_dodges_high_fisher` returns `False`, and
`render_verdict_section` emits the pre-authored `GATE MISSES` paragraph. Both outcomes render and
both read as an honest result. This is verbatim the hazard `require_fingerprint` was written to
close ("a wrong denominator still renders and still looks plausible"), applied to one block and
not to the two that produce the headline verdict.

The guard is free, and the script is already paying for it. `_load_model` calls
`torch.load(weights_only=False)` on the whole blob and then returns only `blob["model"]` and a
three-field fingerprint, throwing the rest away. I inspected the discarded remainder:

```
phase13_naive_latest.pt -> ['best_val_loss','git_sha','model_config','rng','scaler',
                            'schema_version','step','train_config','val_loss']
phase13_ewc_latest.pt   -> [... 'ewc_lambda', 'fisher', 'fisher_meta', 'theta_star', ...]
                           ewc_lambda = 0.01   theta_star = <dict 100 keys>
```

and confirmed `theta_star` covers all 36 figure keys and is `torch.equal` to `best.pt`'s tensor for
**36 of 36**. That is an exact, zero-cost proof of *both* the arm's identity and its W₀ linkage,
currently deleted by the loader's return signature.

This is not a live miscomputation — `test_extraction_reproduces_the_committed_artifact` passes on
this machine, so the committed artifact matches today's checkpoints. It is a missing guard on the
one input whose silent corruption inverts the phase's claim, on a re-run against future weights.

**Fix:** Return the blob from `_load_model` (or a second value), and add a `prove`-style guard
before `blocks` is assembled. Entirely inside `extract_deltas.py`, which is not frozen.

```python
def _load_model(path):
    blob = torch.load(path, map_location="cpu", weights_only=False)
    return blob["model"], _fingerprint(blob), blob


def require_arm_identity(naive_blob, ewc_blob, w0_model):
    """The naive/ewc analogue of require_fingerprint. Transposing the two paths inverts the
    D-10 pairing and flips the verdict; both branches still render and still look plausible."""
    if "ewc_lambda" in naive_blob:
        raise SystemExit(
            f"[extract_deltas] {NAIVE_LATEST} carries ewc_lambda="
            f"{naive_blob['ewc_lambda']!r} — this is an EWC arm, not the λ=0 arm. The "
            "naive/ewc paths are transposed; the D-10 reduction would invert and the verdict "
            "would flip while still rendering plausibly."
        )
    if ewc_blob.get("ewc_lambda") != 0.01:
        raise SystemExit(
            f"[extract_deltas] {EWC_LATEST} carries ewc_lambda="
            f"{ewc_blob.get('ewc_lambda')!r}, expected 0.01 (finetune_ab.py::LAMBDA_EWC)."
        )
    # theta_star IS the EWC arm's own recorded W0 — an exact check that best.pt is the right one.
    theta_star = ewc_blob["theta_star"]
    for _layer, _projection, key in KEYS:
        if key not in theta_star or not torch.equal(theta_star[key], w0_model[key]):
            raise SystemExit(
                f"[extract_deltas] the EWC arm's recorded theta_star disagrees with "
                f"{BEST_PATH} at {key} — checkpoints/best.pt is NOT the W₀ these arms ran "
                "from, so every naive/ewc cell would be a ratio against the wrong base."
            )
```

Call it right after the four `_load_model` calls, and record `ewc_lambda` in the `ewc` block's
`source_ckpt` so the artifact carries the discriminator too.

---

### CR-02: ρ = 0.801544 — the phase's signature number — is bound to nothing

**File:** `tests/test_phase15_docs.py:338-357, 369-414` (fixture `_HEADLINE_NUMBERS`)

**Issue:** Confirmed real. `0.801544` is restated in committed prose at five sites:

```
README.md:59                     **ρ = 0.801544** (95% CI [0.597984, 0.920291] …)
docs/REPORT.md:809               Spearman **ρ = 0.801544**
demo_v2.ipynb:381                Spearman **ρ = 0.801544**
results/phase13_ab_report.md:411 - Spearman ρ = **0.801544** (`average_rank_pearson_fp64`, n = 36)
.planning/ROADMAP.md:270         ρ = 0.801544 with a 95% bootstrap CI …
```

`_HEADLINE_NUMBERS` covers `0.3483`, `8.52417066884246` and `3.229` and nothing else.
`test_verdict_section_is_dated_and_separated` asserts the addendum is dated, marked, last and
carries exactly one of `GATE PASSES`/`GATE MISSES` — it never touches the value. No test in the
repo recomputes ρ from the artifact. A paraphrase-to-soften, a transposed digit, or a
one-character edit *in either direction* leaves the entire suite green, while doing the same to
`0.3483` goes red. The number the whole phase exists to establish is the least protected number
in the phase.

Adding a plain `_HEADLINE_NUMBERS` row would be the weak fix, and I checked why: README renders ρ
in a *paragraph* under `## Where the memory actually moved`, not in a bullet, so
`re.split(r"\n(?=- )", readme)` puts it in the chunk opened by the unrelated bullet at
README.md:47. `len(carrying) == 1` would still hold, but the inline-qualifier assertion would be
checking a chunk spanning three sections — a qualifier check with no teeth. It also would not
catch drift in the *other direction* (artifact edited, prose left alone).

**Fix:** Bind the number to its computed source, not to a second copy of itself. `load_pairs` +
`spearman` on the committed artifact takes 0.2 ms — no resampling needed, since ρ is what needs
binding — and this incidentally becomes the first test coverage `load_pairs` has ever had (WR-03).
Test-side only; the frozen module is imported, not edited.

```python
# tests/test_phase15_docs.py
import importlib.util

_RHO_SITES = ("README.md", "docs/REPORT.md", "demo_v2.ipynb", "results/phase13_ab_report.md")


def _load_stats():
    spec = importlib.util.spec_from_file_location(
        "phase15_stats", _REPO_ROOT / "scripts" / "phase15_stats.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reported_rho_is_recomputed_from_the_artifact():
    """D-09/D-16: ρ is the number this phase exists to produce, so it may not live in prose
    only. Recomputed from results/phase15_norms.json with the pre-registered transform — this
    goes red if the prose drifts OR if the artifact does."""
    stats = _load_stats()
    artifact = json.loads(_read("results/phase15_norms.json"))
    fisher, reduction = stats.load_pairs(artifact)
    rho = stats.spearman(fisher, reduction)

    # The gate itself, recomputed — the sign is the falsifiable claim (D-11).
    assert rho > 0, f"the pre-registered POSITIVE sign no longer holds: rho = {rho}"
    rendered = f"{rho:.6f}"  # the render_verdict_section :.6f spelling
    for site in _RHO_SITES:
        assert rendered in _read(site), (
            f"{site} no longer carries the recomputed rho {rendered} — the phase's signature "
            f"number has drifted from its source in one direction or the other"
        )
```

Extend the same shape to the CI bounds (`0.597984`, `0.920291`) if the ~0.4 s bootstrap is
acceptable in the suite; ρ alone closes the hole the verifier named.

---

## Warnings

### WR-01: `plot_phase15` treats the artifact as trusted while both sibling modules treat it as untrusted

**File:** `scripts/plot_phase15.py:67-116, 119-133`

**Issue:** `phase15_stats._cell` rejects non-numeric and non-finite cells by coordinate;
`extract_deltas.prove` rejects non-finite cells before the write. `_load_artifact` validates
*structure only* — block presence, cell count, projection names, `vmax_driver` presence — and
never validates a value. `_grid` then does a bare `float(...)`, which coerces strings. I injected
each case into a copy of the artifact and re-rendered `plot_fisher_ewc`:

| injected `blocks.naive.cells["0"]["q_proj"]` | result |
|---|---|
| `NaN` | `ValueError: Invalid vmin or vmax` — names no file, no block, no coordinate |
| `+inf` | `ValueError: Invalid vmin or vmax` — same |
| `-inf` | **renders silently**, 107410-byte PNG |
| `0.0` | **renders silently**, 107410-byte PNG |
| `-1.0` | **renders silently**, 107410-byte PNG |
| `"0.5"` (string) | **renders silently**, 104426-byte PNG |

The four silent cases land as `set_bad("0.85")` grey cells indistinguishable from data, which is
exactly what the `_cmap` docstring says the module exists to prevent — and `_load_artifact` never
reads the `nonpositive_cells` field it would need to catch them. The two loud cases contradict the
module's own contract ("every failure below names the offending file and the offending
block/layer"). `json.loads` accepts bare `NaN`/`Infinity` literals by default, and the artifact is
a committed, hand-editable file, so this is the T-15-07 threat surface the sibling module defends
and this one does not.

**Fix:** Add value validation to `_load_artifact`'s existing per-layer loop — same shape as
`_cell`, entirely inside the unfrozen plotting script.

```python
        for layer in range(n_layer):
            row = cells.get(str(layer))
            ...
            for projection, value in row.items():
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ValueError(
                        f"{path}: block {name!r} cell (layer {layer}, {projection}) is "
                        f"{value!r}, not a number"
                    )
                if not math.isfinite(value):
                    raise ValueError(
                        f"{path}: block {name!r} cell (layer {layer}, {projection}) is "
                        f"{value!r}, not finite — it would render as a grey cell "
                        "indistinguishable from data"
                    )
        if sum(1 for r in cells.values() for v in r.values() if v <= 0.0) != block["nonpositive_cells"]:
            raise ValueError(
                f"{path}: block {name!r} 'nonpositive_cells' disagrees with its own cells — "
                "the report states that count from this field"
            )
```

---

### WR-02: not one negative-path test exists in the phase

**File:** `tests/test_phase15_stats.py`, `tests/test_phase15_plots.py`, `tests/test_phase15_docs.py`

**Issue:** `grep -n "pytest.raises\|SystemExit\|ValueError"` across all three files returns
nothing. The three modules under test carry roughly twenty explicit fail-loud guards — five
`SystemExit` in `load_pairs`, two in `_cell`, one in `main`, six `ValueError` + one `SystemExit`
in `_load_artifact`, one in `_own_norm`, five in `extract_deltas` — and each module docstring
presents that fail-loud behaviour as its principal safety property. Every one is unverified. That
is why WR-01's six-case table was discoverable at all: the branch that *should* have rejected four
of those six was never written, and nothing would have noticed either way.

The plotting module makes this harder than it needs to be: `_load_artifact(path=NORMS_JSON)` binds
the default at definition time, and `plot_adapter_delta`/`plot_fisher_ewc` accept an `out_dir` but
no artifact path — so they always read the committed file, and the validation branches cannot be
reached from a test without monkeypatching the module function itself.

**Fix:** Thread the artifact path through the public plot functions, then add one table-driven
negative test per module.

```python
def plot_adapter_delta(out_dir, artifact_path=NORMS_JSON):
    artifact = _load_artifact(artifact_path)
    ...

def plot_fisher_ewc(out_dir, artifact_path=NORMS_JSON):
    artifact = _load_artifact(artifact_path)
    ...
```

```python
@pytest.mark.parametrize(
    "mutate, expect",
    [
        (lambda a: a["blocks"].pop("fisher"), "block 'fisher' is absent"),
        (lambda a: a["blocks"]["naive"]["cells"].pop("3"), "no layer 3"),
        (lambda a: a["blocks"]["naive"]["cells"]["0"].__setitem__("q_proj", float("-inf")),
         "not finite"),
        (lambda a: a["blocks"]["naive"]["cells"]["0"].__setitem__("q_proj", "0.5"),
         "not a number"),
    ],
)
def test_malformed_artifact_is_fatal_and_named(tmp_path, mutate, expect):
    artifact = _artifact()
    mutate(artifact)
    bad = tmp_path / "phase15_norms.json"
    bad.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    with pytest.raises((ValueError, SystemExit), match=re.escape(expect)):
        plot.plot_fisher_ewc(tmp_path, artifact_path=bad)
```

---

### WR-03: `load_pairs`, `_cell` and `render_verdict_section` have zero coverage; the GATE MISSES branch is never executed

**File:** `scripts/phase15_stats.py:228-300, 318-437`; `tests/test_phase15_stats.py:1-23`

**Issue:** The test module names four pins — `spearman`, seeding, CI behaviour, the gate rule —
and none touches the artifact reader or the verdict renderer. Confirmed by grep: `load_pairs` and
`render_verdict_section` appear nowhere in `tests/` or `scripts/` outside their own module's
docstrings. Two consequences:

1. The reader that the module docstring describes as the T-15-07 mitigation ("a malformed or
   truncated artifact must never yield a partial correlation that reads as a plausible verdict")
   is entirely unverified, including the `_cell` finiteness guard the re-review evidence relies
   on.
2. `render_verdict_section`'s `GATE MISSES` branch — the whole T-15-09 both-branches-pre-authored
   mitigation — has never been executed by anything. `test_phase15_docs.py:471` guards its own
   miss assertion behind `if "GATE MISSES" in body:`, and the gate passed, so that assertion is
   dormant by design. The pre-authored honest-miss wording is protected by nothing and exercised
   by nothing.

**Fix:** CR-02's fixture gives `load_pairs` its first exercise for free. Add one pure-function
test for the renderer — no artifact, no file, no frozen-file edit:

```python
def test_both_verdict_branches_render():
    """T-15-09: the miss branch is dormant because the gate passed, not because it works."""
    stub = {"git_sha": "deadbee", "built": "2026-01-01"}
    passes = st.render_verdict_section(0.80, 1e-5, 0.60, 0.92, 0, stub, "2026-01-01")
    misses = st.render_verdict_section(0.15, 0.03, -0.10, 0.40, 7, stub, "2026-01-01")
    assert "GATE PASSES" in passes and "GATE MISSES" not in passes
    assert "GATE MISSES" in misses and "GATE PASSES" not in misses
    assert "suggestive but not statistically demonstrated at n = 36" in misses
    assert "not softened into a passing verdict" in misses
    assert "**7** of 10000" in misses  # the degenerate count is actually rendered
```

---

### WR-04: `load_pairs` raises a bare `AttributeError` on a non-dict block

**File:** `scripts/phase15_stats.py:253`

**Issue:** The docstring promises "Every deviation is fatal and NAMES the offending
block/coordinate". `blocks[name].get("cells")` assumes `blocks[name]` is a dict. Verified:

```
block is a string: *** AttributeError: 'str' object has no attribute 'get'
block is a list:   *** AttributeError: 'list' object has no attribute 'get'
```

Fail-loud is preserved (non-zero exit either way), but the operator gets a traceback naming a line
instead of a message naming the block — which is precisely the `plot_phase13.py:88-97` register
the docstring cites as the reason the named errors exist. Related: `total = sum(len(v) for v in
cells.values() if isinstance(v, dict))` silently ignores non-dict rows, so `{"0": ..., "6": "x"}`
passes the count check.

**Fix:** One `isinstance` ahead of the existing check. Frozen-file edit, additive only, no change
to any pre-registered constant — requires a dated amendment record.

```python
        block = blocks[name]
        if not isinstance(block, dict):
            raise SystemExit(
                f"[phase15_stats] {NORMS_JSON.name}: block {name!r} is {type(block).__name__}, "
                "not an object."
            )
        cells = block.get("cells")
```

---

### WR-05: the different-seed meta-guard rests on a single permutation and is one coin flip from useless

**File:** `tests/test_phase15_stats.py:88-93`

**Issue:** The assertion is meant to prove the resamplers do not ignore randomness. But
`permutation_p` returns `(obs, p)` and `obs` is **seed-independent** — it is the observed
statistic. So the tuple inequality reduces entirely to `p1 != p2`. I instrumented the actual
fixture:

```
perm seed=1337   -> (0.551866151866152, 0.0009995002498750624)   ge = 1
perm seed=1338   -> (0.551866151866152, 0.0004997501249375312)   ge = 0
```

The whole meta-guard hangs on exactly one shuffle out of 2000 crossing the threshold under one
seed and not the other. A marginally stronger fixture draw gives `ge = 0` for both seeds → equal
tuples → **the test goes red against a correct implementation**. A marginally weaker one leaves it
passing for the wrong reason. It is deterministic today, so not flaky — but its teeth are an
accident of `default_rng(4242)`, not a property of the design.

**Fix:** Compare the seed-dependent component directly, on a fixture where the count is large
enough to be robust. Test-side only.

```python
    # obs is seed-independent by construction, so compare the p component only — and use a WEAK
    # relationship so `ge` is in the hundreds, not 0 vs 1.
    weak = 0.15 * a + rng.normal(size=st.N_CELLS)
    _, p_a = st.permutation_p(a, weak, n_perm=2000, seed=st.SEED)
    _, p_b = st.permutation_p(a, weak, n_perm=2000, seed=st.SEED + 1)
    assert p_a != p_b, "permutation_p ignores its seed"
    assert 0.01 < p_a < 0.99, f"fixture too extreme for the seed meta-guard to have teeth: {p_a}"
```

---

### WR-06: `bootstrap_ci` crashes with an opaque `IndexError` when every resample is degenerate

**File:** `scripts/phase15_stats.py:199-202`

**Issue:** The docstring says degenerate resamples are dropped and the count "REPORTED rather than
letting a nan silently propagate into a quantile." If *all* are degenerate, `kept` is empty and
`np.quantile` raises:

```
bootstrap_ci([1.0]*5, [1.0]*5, n_boot=10, seed=1) -> IndexError: index -1 is out of bounds for axis 0 with size 0
```

Not reachable from the committed 36-cell artifact, but the whole point of `n_degenerate` is that
the function has a documented opinion about degeneracy, and its boundary case is an unhandled
numpy internal. Compounding: both CI tests assert `n_degenerate == 0`, so the `np.nan` branch —
the code that produces the reported count — is never executed by the suite either.

**Fix:** Additive guard in the frozen file (dated amendment), plus one test exercising the drop
path.

```python
    kept = out[np.isfinite(out)]
    if kept.size == 0:
        raise SystemExit(
            f"[phase15_stats] all {n_boot} bootstrap resamples were degenerate (zero variance "
            "in a or b) — the input carries no rank information and no CI is definable."
        )
```

---

### WR-07: `adapter_cells` documents a shape-sanity property that `_ratio` structurally cannot check

**File:** `scripts/extract_deltas.py:174-187, 169-171`

**Issue:** The docstring asserts "Shape sanity: `(out, r) @ (r, in) == (out, in)` — identical to
`base.weight`". Nothing checks it. `_ratio` reduces both arguments to Frobenius norms — scalars —
so `‖ΔW‖_F / ‖W₀‖_F` is well-defined for *any* pair of shapes and returns a plausible float. A
transposed `lora_A`/`lora_B`, or a pair belonging to a different projection, yields a number that
renders and passes every downstream check. The only guard is `len(adapter) != 2 * N_CELLS`
(a count, not an identity), and the two `adapter[f"{prefix}.lora_A"]` lookups raise a bare
`KeyError` on a naming change rather than the module's promised named `SystemExit`. Contrast
`full_ft_cells`, where `arm_model[key] - w0` makes the shape check implicit and free.

**Fix:** Make the documented invariant an actual check.

```python
    for layer, projection, key in KEYS:
        prefix = key[: -len(".weight")]
        for suffix in ("lora_A", "lora_B"):
            if f"{prefix}.{suffix}" not in adapter:
                raise SystemExit(
                    f"[extract_deltas] {PERSONA_ADAPTER} has no {prefix}.{suffix} — the adapter "
                    "does not describe a 6-layer x 6-projection injection."
                )
        a = adapter[f"{prefix}.lora_A"].to(torch.float64)
        b = adapter[f"{prefix}.lora_B"].to(torch.float64)
        dw = scale * (b @ a)
        w0 = w0_model[key].to(torch.float64)
        if dw.shape != w0.shape:
            raise SystemExit(
                f"[extract_deltas] {key}: ΔW {tuple(dw.shape)} != W₀ {tuple(w0.shape)} — "
                "_ratio takes Frobenius norms and would return a plausible number anyway."
            )
        out[(layer, projection)] = _ratio(dw, w0)
```

---

### WR-08: the three Phase-15 `PROJECTIONS` copies are not cross-pinned to the canonical allowlist

**File:** `scripts/extract_deltas.py:80`, `scripts/phase15_stats.py:60`,
`tests/test_phase15_plots.py:64`, `tests/test_phase15_stats.py:129`

**Issue:** All three copies document themselves as "Copied verbatim from
`src/personacore/lora/config.py:16`". None is enforced against it.
`tests/test_phase15_stats.py:129` asserts the *literal tuple*, not equality with
`TARGET_PROJECTIONS`, so a change to the canonical allowlist leaves three silent divergent copies
and a test that keeps passing on the stale spelling. The project already has exactly this pattern
where it was needed — `tests/test_lora_inject.py:81`: `assert TARGET_PROJECTIONS == PROJECTIONS` —
and it was not applied here. `phase15_stats.PROJECTIONS` is genuinely frozen and *should* stay
pinned to its 2026 spelling; the right move is to make a future divergence visible, not silent.

**Fix:** Test-side, no source edit. In `tests/test_phase15_plots.py` (which already imports from
the package side of the repo without torch at collection — `personacore.lora.config` is a plain
dataclass module):

```python
from personacore.lora.config import TARGET_PROJECTIONS


def test_phase15_projection_copies_track_the_canonical_allowlist():
    """extract_deltas / phase15_stats / this fixture each declare themselves a verbatim copy of
    lora/config.py's allowlist. phase15_stats is pre-registration-frozen, so a divergence must
    surface HERE as a deliberate decision rather than as three silently stale tuples."""
    stats = _load_stats()  # the importlib loader
    extract_src = EXTRACT_SCRIPT.read_text(encoding="utf-8")
    assert tuple(PROJECTIONS) == TARGET_PROJECTIONS
    assert stats.PROJECTIONS == TARGET_PROJECTIONS
    assert f"PROJECTIONS = {TARGET_PROJECTIONS!r}" in extract_src
```

---

### WR-09: `spearman`/`_rank` return a plausible finite ρ on NaN input

**File:** `scripts/phase15_stats.py:126-157`

**Issue:** `np.argsort` sorts NaN to the end, so `_rank` assigns NaN the *highest* rank and
`spearman` returns a finite, entirely fictitious correlation — e.g.
`spearman([1..6], [nan,2,3,4,5,6])` → `0.14285714285714288`, no warning, no error. Neither
docstring mentions it.

**Containment, stated so this is not over-read:** every in-repo path into these helpers goes
through `load_pairs`, whose `_cell` rejects non-finite values by coordinate before they can reach
`_rank` — I re-confirmed this by injecting NaN into a copy of the artifact and getting
`SystemExit: ... block fisher cell (layer 0, q_proj) is nan, not finite.` `main()` is the only
production caller. This is a latent defect in two public helpers, **not** a live path to a
corrupted verdict, and it is filed as a warning rather than a blocker for exactly that reason.

**Fix:** Cheapest correct option is documentation plus a test that pins the containment, avoiding
any change to the frozen transform:

```python
def test_rank_helpers_are_only_safe_behind_load_pairs():
    """_rank sorts NaN last and spearman returns a finite fiction. load_pairs::_cell is what
    makes that unreachable — this test pins the containment so a future caller that bypasses
    load_pairs is a deliberate decision rather than an accident."""
    assert np.isfinite(st.spearman([1, 2, 3, 4, 5, 6], [float("nan"), 2, 3, 4, 5, 6]))
    poisoned = {"blocks": _artifact_with_nan()}
    with pytest.raises(SystemExit, match="not finite"):
        st.load_pairs(poisoned)
```

If a source fix is preferred instead, add `if not np.all(np.isfinite(x)): raise ValueError(...)`
to `_rank` — additive, does not alter the transform, still needs the dated amendment record.

---

## Info

### IN-01: `ewc_dodges_high_fisher` takes a `ci_hi` it never reads

**File:** `scripts/phase15_stats.py:208-222`
**Issue:** `return rho > 0 and ci_lo > 0` — `ci_hi` is unused. Harmless (given `rho > 0` and
`ci_lo > 0`, `ci_hi > 0` follows), but an unused parameter in the phase's gate function invites a
future reader to assume a two-sided check that is not there.
**Fix:** Keep the signature (the call sites and tests are pre-registration material) and add
`# ci_hi is accepted for call-site symmetry; ci_lo > 0 already implies the interval excludes zero`.

### IN-02: the four-block tuple is declared three times

**File:** `scripts/phase15_stats.py:102` (`BLOCKS`), `scripts/plot_phase15.py:56`
(`REQUIRED_BLOCKS`), `scripts/extract_deltas.py:395` (inline literal in `prove`)
**Issue:** Three independent spellings of `("adapter", "naive", "ewc", "fisher")`, one of them an
inline literal rather than a named constant. `tests/test_phase15_plots.py:65` adds a fourth in a
different order.
**Fix:** Hoist the `prove` literal to a module constant at minimum; the cross-module duplication is
acceptable given the deliberate frozen-module isolation, but should be noted where each is declared.

### IN-03: the D-07 subprocess probe reports "transitively imports torch" for any nonzero exit

**File:** `tests/test_phase15_plots.py:344-352`
**Issue:** `exec_module` failing for an unrelated reason (missing matplotlib on a fresh clone, a
syntax error) yields `returncode == 1` and therefore the message "plotting module transitively
imports torch — D-07 violated". `stderr` is included so it is diagnosable, but the headline is
wrong. Also worth knowing about the same test's scope: the AST half catches `import torch` only —
`importlib.import_module("torch")`, `pickle.load`, `numpy.load(allow_pickle=True)` and
`safetensors` would all pass both halves, so the docstring's "provably incapable of deserializing
anything" overstates what is proved. The module is clean today; the claim is not.
**Fix:** Have the probe exit `2` on import failure and assert `returncode != 1` separately; soften
the docstring to "provably free of a torch import path" and add the other deserializer module names
to the AST denylist.

### IN-04: `plot_phase15.main()` renders both figures before printing either

**File:** `scripts/plot_phase15.py:298-300`
**Issue:** The tuple in the `for` is fully evaluated before the first iteration, so both `savefig`
calls complete before "wrote" appears. Cosmetic, but the output implies incremental progress.
**Fix:** `for fn in (plot_adapter_delta, plot_fisher_ewc): print(f"[plot_phase15] wrote {fn(RESULTS_DIR)}")`

### IN-05: `_github_anchor` diverges from GitHub's real slug algorithm

**File:** `tests/test_phase15_docs.py:360-366`
**Issue:** GitHub also strips leading/trailing hyphens and preserves underscores; this
implementation does neither. Correct for the current heading, so the link assertion is sound today,
but a future heading starting or ending with punctuation would produce a false failure.
**Fix:** Add `.strip("-")` and `or c == "_"` to match the documented algorithm.

---

_Reviewed: 2026-08-02T21:46:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
