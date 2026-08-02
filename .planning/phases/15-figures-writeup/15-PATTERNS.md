# Phase 15: Figures & Writeup - Pattern Map

**Mapped:** 2026-08-02
**Files analyzed:** 11 (7 new, 4 modified)
**Analogs found:** 10 / 11 (1 partial)

RESEARCH.md already names the file layout and points at analogs. This file does not restate
that — it opens each analog and pulls the **concrete house-style excerpts** (import block shape,
docstring register, `raise SystemExit` wording, `skipif` idiom, `out_dir` parameterization, AST
walk, JSON writer, notebook cell register) so plan tasks can say "copy lines X-Y of Z" instead of
"follow the pattern."

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| NEW `scripts/extract_deltas.py` | script / driver | batch file-I/O (6 `.pt` → 1 JSON) | `scripts/finetune_ab.py` (header + constants + guards) ⊕ `scripts/build_retention_bin.py:157-186` (proofs → JSON write) | role-match, composite |
| NEW `scripts/phase15_stats.py` | utility (pure fns + pre-registration constants) | transform | `scripts/finetune_ab.py:66-116` (pre-reg block + gate as pure function) | exact |
| NEW `scripts/plot_phase15.py` | script / plotting | read committed data → `savefig` | `scripts/plot_phase13.py` | exact |
| NEW `results/phase15_norms.json` | committed data artifact | persisted numbers | `results/retention_anchors.json` (shape) + `build_retention_bin.py:166-182` (writer) | role-match (must nest one level deeper) |
| NEW `tests/test_phase15_stats.py` | test (known-answer, pure) | — | `tests/test_phase13_plots.py:17-32` (importlib load) + `tests/test_phase14_scoring.py:1-27` (docstring inventory) | exact |
| NEW `tests/test_phase15_plots.py` | test (smoke + structural + skipif) | — | `tests/test_phase13_plots.py:59-68`, `tests/test_phase14_scoring.py:405-423`, `tests/test_slim_checkpoint.py:41-46,168` | exact |
| NEW `tests/test_phase15_docs.py` | test (doc integrity) | — | `tests/test_phase14_demo.py:126,580-596` (source read + pinned-SHA diff) | **partial** — see `## No Analog Found` |
| NEW `demo_v2.ipynb` | notebook artifact | re-cite committed numbers | `demo.ipynb` cells 0 / 2 / 3 | exact |
| MODIFY `results/phase13_ab_report.md` | evidence report (dated append) | append-only | `scripts/phase14_recall.py:1590-1643` (`SHIP_DECISION_HEADER` + anchored verdict guard) ⊕ `results/phase13_ab_report.md:261-267` (verbatim-quote register) | exact |
| MODIFY `docs/REPORT.md` | narrative doc | — | `docs/REPORT.md`'s own 14 `## Decision:` sections | exact (self-analog) |
| MODIFY `README.md` | narrative doc | — | `README.md:29-33` (the 547-live-ids bullet) | exact (self-analog) |

---

## Pattern Assignments

### `scripts/plot_phase15.py` (script, read-JSON → savefig)

**Analog:** `scripts/plot_phase13.py` — the direct template. Copy five properties.

**1. Docstring register** (lines 1-18): what it produces → which committed inputs → the
misreading it forbids → the `Run:` line. Note the explicit "no torch, no checkpoints" claim in
sentence 2 — Phase 15's version of that sentence is the one D-07 converts into a test.

```python
"""Phase-13 figure generation: VIZ-01 forgetting curve + VIZ-04 λ frontier.

Pure ``csv`` + ``matplotlib`` — no torch, no training, no checkpoints. Every number comes
from a COMMITTED artifact (the two arm CSVs and the five λ-sweep CSVs) or from a
hardcoded-with-citation constant, so the figures regenerate deterministically from the repo
alone. Thin no-CLI ``main()`` with ``_REPO_ROOT``-relative constants (Phase-1 D-04).

  VIZ-01 → results/phase13_forgetting_curve.png — retention (forgetting) and dialogue
           (acquisition) PPL vs step for BOTH 4000-step A/B arms.
  ...
Run: ``python scripts/plot_phase13.py`` (inside the Python 3.11 venv). Headless — the
figures are written with ``savefig``; nothing here calls ``show()``.
"""
```

**2. Agg-before-pyplot import block** (lines 20-35) — the `# noqa: E402` comments are required
by ruff (`select = ["E","F","W","I"]`, line-length 100):

```python
import csv
import pathlib

import matplotlib

# Agg BEFORE pyplot: this script only ever writes files, so it must not need a GUI backend
# (it runs from a plain venv shell and from the tmp_path smoke test).
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend selection above)
from matplotlib.ticker import StrMethodFormatter  # noqa: E402  (same reason)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_DIR = _REPO_ROOT / "results"  # git-TRACKED output, next to the A/B report
NAIVE_CSV = RESULTS_DIR / "phase13_naive" / "run.csv"  # committed 4000-step naive arm
```

**3. Fail-loud on missing/blank data** (lines 88-97) — the exact register for Phase 15's
"missing block / wrong cell count in the JSON" guard. The final sentence is the reusable line:

```python
    if not rows:
        raise ValueError(f"{source}: no rows at all, cannot plot column {column!r}")
    if column not in rows[0]:
        raise KeyError(f"{source}: no column {column!r}; columns are {sorted(rows[0])}")
    ...
    if not pairs:
        raise ValueError(f"{source}: column {column!r} is blank in all {len(rows)} rows")
```
Docstring rationale to mirror (line 86): *"an empty panel under a titled axis is a figure that
lies."* Note `_series(rows, column, path)` threads the source path in **so the error names the
offending file, not just the column** (line 127).

**4. `out_dir`-parameterized plot fn that RETURNS the written path, never `show()`**
(lines 121-123, 162-165). This is what makes the `tmp_path` smoke test possible:

```python
def plot_forgetting_curve(out_dir):
    """VIZ-01: forgetting + acquisition vs step for both 4000-step arms. Returns the path."""
    fig, (ax_ret, ax_dlg) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=DPI)
    ...
    out_path = pathlib.Path(out_dir) / "phase13_forgetting_curve.png"
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
```

**5. Thin `main()` printing each written path, `__main__`-guarded** (lines 203-209) — the guard is
load-bearing: the test `importlib`-loads the module, so `main()` must render nothing at import.

```python
def main() -> None:
    for out_path in (plot_forgetting_curve(RESULTS_DIR), plot_frontier(RESULTS_DIR)):
        print(f"[plot_phase13] wrote {out_path}")


if __name__ == "__main__":
    main()
```

**Also copy:** the in-figure disclosure mechanism for D-04's terse figure-side note is already
here (lines 187-194) — `fig.text(0.5, 0.005, "...", ha="center", fontsize=8, color="gray")` +
`fig.tight_layout(rect=(0, 0.03, 1, 1))`, with the comment *"The budget is stated on the figure
itself"*. That is exactly D-04's "terse form travels with the PNG."

**Do NOT copy:** `HEADLINE_RETENTION` / `LAMBDA0_POINT` hardcode-with-citation constants — Phase 15
reads every number from the JSON by construction (D-07), so a hardcoded number in
`plot_phase15.py` would be a second source of truth.

---

### `scripts/extract_deltas.py` (script, batch `.pt` → JSON)

**Analog A — header, constants, guards:** `scripts/finetune_ab.py`.
**Analog B — proofs then JSON write:** `scripts/build_retention_bin.py:157-186`.

**SECURITY docstring note** (`finetune_ab.py:20-25`) — copy the register verbatim, extending the
list to the six checkpoints D-08 requires named:

```python
SECURITY: torch.load(weights_only=False) reads ONLY the project's OWN anchor checkpoint
(``checkpoints/best.pt`` — T-12-10 trusted-only); the Fisher cache goes through ``load_fisher``
(weights_only=True) pinned to the anchor fingerprint trio.

Run: ``python scripts/finetune_ab.py {naive|ewc}`` (inside the Python 3.11 venv, on the M3).
"""
```
The longer form of the same note, closer to what Phase 15 needs (adapter + full checkpoint in one
docstring), is `scripts/teach_persona.py:32-39`:

```python
The TRAINING half adds exactly one deserialization: ``torch.load(CONVBASE_BEST,
weights_only=False)`` on this project's OWN resume checkpoint (T-14-04), which must stay
``weights_only=False`` because it carries pickled optimizer/RNG/numpy objects. Nothing it writes
inherits that posture — the SHAREABLE adapter goes out through ``export_adapter``, so every
consumer (harness, demo) reads it back under the ``weights_only=True`` ``load_adapter`` contract.

Every proof check below is an explicit ``raise SystemExit`` and never an ``-O``-strippable bare
check, so a failure exits non-zero even under ``PYTHONOPTIMIZE``.
```

**Path constant block** — `_REPO_ROOT`-relative, one trailing comment per path stating its status
(`finetune_ab.py:53-62`, `teach_persona.py:89-97`). The `convbase_best.pt` constant already exists
verbatim at `teach_persona.py:90`:

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted checkpoint
BEST_PATH = _REPO_ROOT / "checkpoints" / "best.pt"  # own trusted anchor checkpoint
FISHER_CACHE = _REPO_ROOT / "checkpoints" / "fisher_tinystories.pt"
ANCHORS_JSON = _REPO_ROOT / "results" / "retention_anchors.json"  # committed step-0 anchors
```

**The read-only checkpoint load** (`teach_persona.py:542-545` — the comment is the pattern, and it
is the one that says *why* the weights-only posture cannot apply):

```python
    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy
    # objects. TRUSTED-only read of the project's OWN checkpoint (T-14-04) — never a foreign
    # file. The SHAREABLE artifact path stays weights_only=True via export_adapter.
    blob = torch.load(CONVBASE_BEST, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
```
`finetune_ab.py:207-208` is the one-line variant, plus the fingerprint trio it builds at line 221 —
this is the literal shape of the D-08 / Pitfall-1 fingerprint guard's `got` side:

```python
    fingerprint = {"git_sha": blob["git_sha"], "step": blob["step"], "val_loss": blob["val_loss"]}
    cache = load_fisher(FISHER_CACHE, expected_fingerprint=fingerprint)
```

**Fail-loud guards — `raise SystemExit`, never bare `assert`.** Two registers, both in-repo:

```python
# finetune_ab.py:168-171 — the reusable proof helper
def _prove(condition, message):
    """Loud end-of-run proof: SystemExit naming the violated contract (never bare assert)."""
    if not condition:
        raise SystemExit(f"[finetune_ab] PROOF FAILED: {message}")

# finetune_ab.py:134-142 — refuse to overwrite recorded evidence, naming the offender
def refuse_if_exists(paths):
    """D-07 / WR-02 refuse-to-rerun: an arm's outputs are RECORDED evidence once written — a
    rerun on drifted code/data would silently replace them. Fail loud naming the offender."""
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[finetune_ab] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )
```
Every message opens `[<script_name>] ` and names the specific file/value. Copy that prefix.

**Explicit-allowlist iteration** (the Pitfall-7 `.weight`/`.bias` defence). The in-repo statement of
this rule is `src/personacore/lora/inject.py:38` — *"explicit allowlist — NEVER an isinstance scan
(P1)"*. Build the 36 keys from an explicit `(layer, projection)` product.

**Proofs-then-write ordering + the JSON writer** (`build_retention_bin.py:157-186`). The writer
details are load-bearing for D-08's byte-for-byte test — `indent=2`, **no `sort_keys`** (insertion
order is the pinned order), explicit trailing newline:

```python
    if not ppl_full < HEADLINE_UNMASKED_FULLVAL:
        raise SystemExit(
            f"[proof 3] masked full-val PPL {ppl_full:.4f} not < unmasked headline "
            f"{HEADLINE_UNMASKED_FULLVAL} — dead-id renormalization must strictly lower PPL."
        )

    # --- (5) Commit the anchors (git-TRACKED results/ — Pitfall 6) ---
    anchors = {
        ...
        "headline_note": ("historical unmasked reference only — NOT the curve anchor, Pitfall 1"),
        "git_sha": git_sha(),
        "built": time.strftime("%Y-%m-%d", time.gmtime()),
    }
    with open(ANCHORS_JSON, "w", encoding="utf-8") as fh:
        json.dump(anchors, fh, indent=2)
        fh.write("\n")
```

---

### `scripts/phase15_stats.py` (utility, pure transform + pre-registration)

**Analog:** `scripts/finetune_ab.py:66-116` — pre-registered constants as module-level literals
with a per-constant provenance comment, then the gate as a pure function.

**The pre-registration block header** (lines 66-107 — this is what git history proves):

```python
# ===== PRE-REGISTRATION (D-01..D-11, locked before any Phase-13 number) =====
#
# Transcribed from committed Phase-12 evidence. Hardcoded on purpose — the driver never parses
# the report for numbers. This block is committed BEFORE either arm runs; git history order is
# the pre-registration proof (finetune_smoke.py:77+ register, T-12-08).

# D-05/§2 — K reused BLIND from Phase 12: the same deliberately conservative default, NOT
# re-chosen after seeing any Phase-13 number.
K = 2

# D-05 obligation 1 — the retention noise floor WITH its measurement regime named:
# results/finetune_smoke_report.md Stage 0b, seed pair (1337, 2024), masked arm, LR 9e-5,
# 1250 steps, identical config. NOT re-verified at the 4000-step production budget — the
# report's threats-to-validity register carries that limitation explicitly.
DELTA_RET = 0.068930
...
SEED = 1337  # seed_everything immediately before the GPT build — owns the data order
```
Every constant carries **which decision locked it, from which committed source, and what it is
NOT**. D-12's seed / `n_perm` / `n_boot` and D-10's predicted sign go in this shape.

**The gate as a pure function with the boundary spelled out** (lines 112-116) — D-11's
`positive sign AND CI excluding zero` rule copies this exactly, including the boundary sentence
and the "descriptive, no gate" clause:

```python
def ewc_mitigates(naive_ret, ewc_ret):
    """D-06 claim gate, retention-only: EWC mitigates forgetting iff the EWC arm beats the
    naive arm's retention PPL by MORE than MARGIN = K x DELTA_RET. Boundary is a FAIL
    (delta == MARGIN returns False). Acquisition is reported descriptively with NO gate."""
    return (naive_ret - ewc_ret) > MARGIN
```

**Seeded local RNG idiom** (`src/personacore/continual/fisher.py:105`) — the comment is the point:

```python
        rng = np.random.default_rng(seed)  # LOCAL generator — global RNG untouched (Pitfall 3).
```

**Method-string-in-the-record convention** (`fisher.py:44-45`, echoed into `fisher_meta` at
line 165) — Phase 15's artifact should carry the analogous `spearman_method` / `ci_method` field:

```python
_VARIANT = "empirical_diag_fisher/groundtruth_targets/mean_normalized"
_SPEARMAN_METHOD = "ordinal_double_argsort_no_tie_averaging"
```

**⚠️ What NOT to copy — `fisher.py:48-55`.** This is the existing `_spearman`, and it is the wrong
one for D-12 (ordinal ranks; ties collapse — RESEARCH measured `1.0` where the correct answer is
`0.9486832980505139`):

```python
def _spearman(a, b):
    """Ordinal-rank Spearman correlation (no tie-averaging), fp64 — Pearson on double-argsort
    ranks. Hand-rolled: scipy is NOT a dependency (zero-new-deps posture)."""
    ra = np.empty(len(a), dtype=np.float64)
    ra[np.argsort(a)] = np.arange(len(a), dtype=np.float64)
    ...
```
Copy from it: the fp64 discipline, the "scipy is NOT a dependency" justification sentence, and the
`_SPEARMAN_METHOD` naming convention. Replace: the rank transform (use RESEARCH's average-rank
`_rank`, RESEARCH.md lines 584-648, already validated to 1 ulp). The new module's docstring should
name the divergence explicitly so a future reader does not "unify" the two.

---

### `results/phase15_norms.json` (committed data artifact)

**Analog:** `results/retention_anchors.json` (whole file, 13 lines) — flat primitives, three
conventions to carry forward verbatim: `git_sha`, `built` (ISO date), and an inline `*_note`
string that warns against a specific misreading **inside the data**:

```json
{
  "retention_ppl_subbin_step0": 2.107553076833866,
  "headline_unmasked_fullval": 2.1066,
  "headline_note": "historical unmasked reference only — NOT the curve anchor, Pitfall 1",
  "subbin_seed": 1337,
  "git_sha": "483938a9034c5aa3eb25602e5981510a489f0fd8",
  "built": "2026-08-01"
}
```
`headline_note` is the direct precedent for D-06's top-level machine-readable comparison-basis
note. D-06's per-block fields force one extra nesting level — that is the only deviation.

Writer: see the `build_retention_bin.py:180-182` excerpt above (`indent=2`, no `sort_keys`,
trailing `"\n"`). Pin that exactly, or D-08's byte-for-byte test is untestable.

---

### `tests/test_phase15_plots.py` (test: smoke + structural + skipif)

**Analog A — module loading + tmp_path smoke:** `tests/test_phase13_plots.py` (entire file, 68
lines). Copy the docstring's numbered behavior inventory, the scripts-load justification, the
module-level load, and the smoke assertions:

```python
"""VIZ-01 / VIZ-04 figure-generation contracts for ``scripts/plot_phase13.py``.

CPU-only, GPU/MPS-free, no torch. Pins two things:
  1. ``test_frontier_has_six_points`` — the Pitfall-1 regression. ...
  2. ``test_plot_functions_write_pngs`` — tmp_path smoke: both figures render headless and
     land as non-empty files in the requested output dir (never clobbering ``results/``).

Scripts-load justification: same as ``tests/test_phase13_driver.py`` — the plotting rules
(which CSV, which constant, which baseline) belong in the committed script, so the test
``importlib``-loads it rather than duplicating them in the package. ``main()`` is
``__main__``-guarded, so the load renders nothing.
"""

import importlib.util
import pathlib

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load_plots():
    spec = importlib.util.spec_from_file_location(
        "plot_phase13", _REPO_ROOT / "scripts" / "plot_phase13.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pp = _load_plots()


def test_plot_functions_write_pngs(tmp_path):
    """Both figures render headless into an arbitrary out_dir as non-empty PNGs."""
    curve = pp.plot_forgetting_curve(tmp_path)
    frontier = pp.plot_frontier(tmp_path)

    assert curve == tmp_path / "phase13_forgetting_curve.png"
    for path in (curve, frontier):
        assert path.exists()
        assert path.stat().st_size > 0
```

**Analog B — the AST structural check (D-07):** `tests/test_phase14_scoring.py:405-423`. The
docstring's rationale is the exact argument for Phase 15 (the plotting module's docstring will
*mention* checkpoints while explaining that it never opens one):

```python
def _build_recall_prompt_call_sites():
    """Every ``build_recall_prompt(...)`` call in the driver, tagged with its enclosing function.

    AST rather than ``inspect.getsource`` string matching: a substring check cannot tell a call
    from a mention in a docstring, and the docstrings in that module discuss ``persona=`` at
    length precisely because it is the dangerous argument.
    """
    tree = ast.parse((_REPO_ROOT / "scripts" / "phase14_recall.py").read_text(encoding="utf-8"))
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == (
                "build_recall_prompt"
            ):
                sites.append((node.name, {kw.arg for kw in inner.keywords}))
    return sites
```
Its consumer test (lines 425-449) carries the "why a convention needs a test" paragraph that D-07's
test docstring should mirror: *"Nothing in ``build_recall_prompt`` itself enforces this … so
without this test 'the ordinary recall path is bare' is a convention a future edit can break
silently."* And its first assertion is a **meta-guard against the walk silently finding nothing** —
copy that, it is the failure mode of an AST test:

```python
    sites = _build_recall_prompt_call_sites()
    assert sites, "no build_recall_prompt call sites found — the AST walk stopped working"
```

**Analog C — `skipif` on gitignored artifacts:** `tests/test_slim_checkpoint.py:41-46,168` (the
documented single-file form) and `tests/test_phase14_demo.py:126-133,604-606` (the multi-file form
Phase 15 needs for six checkpoints, including the `# local-only:` comment that states *why*):

```python
# tests/test_slim_checkpoint.py:41-46
TOKENIZER_PATH = "artifacts/tokenizer.json"  # FROZEN production artifact — never retrain.
REAL_SLIM = pathlib.Path("checkpoints/model_slim.pt")  # gitignored; exported by Task 3.

# tests/test_slim_checkpoint.py:168
@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_artifact_generates_on_cpu():
```
```python
# tests/test_phase14_demo.py:128-133 — the multi-artifact gate
_REAL_ARTIFACTS = (
    _REPO_ROOT / "checkpoints" / "model_slim.pt",
    _REPO_ROOT / "checkpoints" / "convbase_slim.pt",
    _REPO_ROOT / "checkpoints" / "persona_adapter.pt",
)
_HAVE_REAL_ARTIFACTS = all(p.exists() for p in _REAL_ARTIFACTS)

# tests/test_phase14_demo.py:604-606 — the comment states the CI reason, not just the skip
# local-only: this is D-17's LITERAL form — the two masks captured inside each real
# build_demo() — and it cannot run in CI because checkpoints/ is gitignored (.gitignore:14).
@pytest.mark.skipif(not _HAVE_REAL_ARTIFACTS, reason="real checkpoints absent (gitignored in CI)")
```
The D-08 obligation ("state explicitly why extraction is not permanently tested") is documented in
the module docstring, per `tests/test_slim_checkpoint.py:18-19`:

```python
  - test_real_slim_artifact_generates_on_cpu — skipif-gated on the real (gitignored)
    ``checkpoints/model_slim.pt``: SKIPS cleanly on CI, runs locally after export.
```

**Note on `assert`:** bare `assert` is correct in `tests/` (pytest requires it, and the whole suite
uses it). The `raise SystemExit`-never-`assert` rule applies to `scripts/` only.

---

### `tests/test_phase15_stats.py` (test: known-answer, pure)

**Analog:** `tests/test_phase14_scoring.py:1-54`. Two things to copy.

**The docstring behavior inventory + the scripts-load justification for a pre-registration module**
(lines 1-27) — this is the paragraph that licenses keeping the rules in `scripts/` rather than the
package, which D-09 requires:

```python
"""DEMO-05/DEMO-06 recall-harness contracts — the pre-registered constants and every scoring rule.

CPU-only, GPU/MPS-free, no checkpoint I/O, no model load, no generation. Pins:
  1. ``test_preregistration_constants`` — the D-09/D-10/D-19 constants block, exact literals.
  ...
Scripts-load justification: no other test imports from ``scripts/`` (``tests/test_demo_callback.py``
states the convention), but the pre-registration constants and every scoring rule MUST live in the
committed driver for git history to be the pre-registration proof (D-09/D-10) — moving them into
the package would put the experiment's rules somewhere the driver could drift from.
``scripts/phase14_recall.py``'s ``main()`` is ``__main__``-guarded and every rule is a module-level
pure function or constant (the ``finetune_ab.py`` "gate formulas as pure functions" precedent), so
an ``importlib.util.spec_from_file_location`` load runs no guard, no model load, and no generation.
"""
```

**The `sys.path` insert for sibling-script imports** (lines 39-54) — needed only if the stats module
is imported by another `scripts/` module:

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "phase14_recall", _REPO_ROOT / "scripts" / "phase14_recall.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pr = _load_driver()
```
There is a "constants block, exact literals" test named in that inventory (`test_preregistration_
constants`) — the D-10/D-12 literals test copies it directly.

---

### `results/phase13_ab_report.md` (MODIFY — dated Phase 15 append)

**Analog A — the dated, explicitly-separated post-verdict section:**
`scripts/phase14_recall.py:1590-1598`. This is the literal wording register D-17 asks for
(separate / dated after / does not reopen or amend):

```python
SHIP_DECISION_HEADER = """<!-- D-12, verbatim: a missed threshold is recorded UNAMENDED in
`## Verdict` above. Any subsequent decision about whether or how the adapter still ships — retry
with a different recipe, ship as-is with the miss documented, or not ship — is logged HERE:
separate from the gate verdict, dated AFTER it, and explicit that it
does not reopen or amend the pre-registered threshold.
Same register as Phase 12's "Production Config Decision — post-verdict, discretionary". Empty
until such a decision is made; an empty section is the correct state when the gate is cleared. -->

_No post-verdict decision recorded._"""
```

**Analog B — the anchored-section guard, and the bug that produced it**
(`phase14_recall.py:1601-1643`). If anything in Phase 15 reads or guards a section of a committed
report, it must anchor on the SECTION, not on the last occurrence of a heading string:

```python
# The verdict SECTION, anchored — never the last occurrence of a substring that also appears in
# prose. `teach_persona._require_go_verdict:163` already reads its gate this way; CR-02 is what
# happens when a guard does not. See `assert_report_not_clobbered` for the failure it caused.
_VERDICT_SECTION = re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)


def assert_report_not_clobbered():
    """The ``measure_inflation.py:66-75`` guard: a RECORDED verdict is committed evidence.
    ...
    **CR-02 — why this reads a SECTION and not ``split("## Verdict")[-1]``.** It used to take the
    tail after the LAST occurrence of that literal. ``SHIP_DECISION_HEADER`` quotes the heading
    inside its own comment (``` `## Verdict` above ```), so every report this writer produces
    contains the string TWICE and the tail landed in the ship-decision comment ...
    """
    if RECALL_REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
        recorded = _recorded_verdict(RECALL_REPORT_PATH.read_text(encoding="utf-8"))
        if recorded is None or "PENDING" not in recorded:
            raise SystemExit(
                f"[phase14_recall] {RECALL_REPORT_PATH} already carries a recorded verdict — "
                "it is committed evidence (D-12). Pass --force to overwrite and re-measure."
            )
```
This directly warns Phase 15's D-17 append: the new section will quote Phase 13 headings in its own
prose, so any future guard over this file must be section-anchored.

**Analog C — the verbatim-quote-with-attribution register**, already inside the target file
(`results/phase13_ab_report.md:261-267`, `## Reconciliation: §8 Search vs Phase-13 Demonstration`):
the preface *"Phase 12 §8 concluded, verbatim and unamended:"* followed by a blockquote. D-15's
eight entries use this exact form.

**Append point:** the file's last heading is `## Evidence Index` (line 358), whose closing table
maps artifact → role and includes the pre-registration provenance row
`` | `scripts/finetune_ab.py` @ `c3d942e` | the pre-registered constants and gate that produced the
verdict | ``. The Phase 15 addendum lands after it, and adds its own row in that same form for
`scripts/phase15_stats.py` @ its pre-registration commit.

---

### `docs/REPORT.md` (MODIFY — extend, v1.0 text untouched)

**Analog:** the file's own 14 `## Decision:` sections (not 15 — RESEARCH corrected this).
Heading form: `## Decision: <the choice, stated as a claim>` — e.g. `## Decision: Byte-Level BPE
from Scratch, Vocabulary Locked Before Model Sizing` (line 48), `## Decision: A Slim Shippable
Artifact That Never Executes Code on Load` (line 322). Each is a title-cased assertion naming the
choice AND its constraint, never a topic label ("Tokenizer"). New v2.0 Decision sections match.

The existing `## Limitations and the Milestone 2 Roadmap` (line 422) and `## Results` (line 369)
show the paragraph register: a **bolded lead-in phrase** then plain prose —
`**What this model is not.**`, `**What actually trained.**` (line 61). D-15's eight entries use the
same bolded lead-in + blockquote.

---

### `README.md` (MODIFY — v2.0 rewrite)

**Analog:** `README.md:29-33`, the literal density target D-16 names. The pattern is: bold claim →
**inside the same parenthetical** the full arithmetic AND the fact that makes it honest. No
footnote, no "see Limitations":

```markdown
- **Byte-level BPE tokenizer** trained from scratch — vocab table 8192 with 547 ids live
  (256 bytes + 283 learned merges + 8 specials; the bounded TinyStories corpus exhausts its
  mergeable pairs, so the remaining 7645 rows are reserved capacity), `<|endoftext|>`
  pinned as an atomic id, validated against a tiktoken oracle (test-only; a guard test
  proves the oracle is never imported by runtime code)
```
Also note lines 15-16 and 21-23 for the two other density registers: a number **with its
denominator and the script that produced it** (*"2.1066 over 12,636,922 scored target tokens (50k-
step `best.pt`, computed by `scripts/evaluate.py`)"*), and a claim **with its caveat and a link to
the full form** (*"the full four-run cohort (with its honest reduced-budget caveat) is in
[docs/REPORT.md]"*) — the second is exactly D-16's terse-form/full-form asymmetry.

⚠️ The exemplar bullet's *"the bounded TinyStories corpus"* clause is factually wrong (RESEARCH Q1).
Copy the **density**, not the content.

---

### `demo_v2.ipynb` (NEW notebook)

**Analog:** `demo.ipynb` (8 cells, nbformat 4, `kernelspec.name = python3`,
`language_info.version = 3.11.15`). Copy:

**Cell 0 — title markdown** that states the thesis, then **what this notebook shows and what it
does not claim**:
> `# PersonaCore — Milestone 1 Results Showcase` … *"**What this notebook shows (and what it does
> not claim).** This is the **Milestone 1** evidence artifact…"*

D-13's independence statement goes in this cell of the new notebook, and in a **prepended** new
cell 0 of `demo.ipynb` (RESEARCH Q3 — prepending changes no existing cell).

**Cell 3 — the re-cite register** (the heading D-13 carries forward verbatim):
```markdown
## Headline evaluation (re-cited, never recomputed)

Deterministic full-validation perplexity of the 50k-step model:

**PPL 2.1066 over 12,636,922 scored target tokens**

produced by `scripts/evaluate.py` (EVAL-01) as a deterministic non-overlapping-window
sweep over the entire validation split. The number is committed in `results/results.md`
and re-cited here **with its token denominator**; this notebook never recomputes it —
the rigor lives in the audited script, not in an ad-hoc notebook cell.
```

**Cell 2 — the plotting-from-committed-CSV register**, including the comment explaining why the
committed copy exists:
```python
# The COMMITTED copy of the 50k-step training log (the raw training-log directory is
# gitignored; this copy keeps the cell re-runnable from a fresh clone).
with open("results/run.csv") as f:
    rows = list(csv.DictReader(f))
```
Note: notebook cells **do** call `plt.show()` (cell 2/4) — the `savefig`-only rule is a `scripts/`
rule, not a notebook rule. Cell 5 shows the blockquote-a-committed-caveat pattern (*"From
`results/results.md`, reproduced verbatim — the caveat is part of the result"*), which is the
notebook-side form of D-15.

Outputs are committed with `execution_count` set (1-4) — the notebook ships executed.

---

## Shared Patterns

### Module docstring shape (every new `scripts/` file)
**Source:** `scripts/plot_phase13.py:1-18`, `scripts/finetune_ab.py:1-25`, `scripts/teach_persona.py:1-43`
**Apply to:** `extract_deltas.py`, `plot_phase15.py`, `phase15_stats.py`

Fixed order: (1) one-line purpose with its requirement ID; (2) what it reads / does not read;
(3) an indented `input → output` map; (4) the decision-numbered constraints it honors;
(5) a `SECURITY:` paragraph when any deserialization happens; (6) a final
``Run: ``python scripts/x.py`` (inside the Python 3.11 venv[, on the M3])`` line.

### Fail-loud register
**Source:** `scripts/finetune_ab.py:139-142,168-171`; `scripts/build_retention_bin.py:160-164`;
`src/personacore/lora/inject.py:179`
**Apply to:** all three new scripts (NOT tests)

`raise SystemExit(f"[script_name] <what failed> — <why it matters>. <what to do>.")`. Never a bare
`assert` (`-O`-strippable). `ValueError` where the failure is a data-shape problem inside a helper
(`plot_phase13.py:89-96`); `SystemExit` where it aborts the run.

### Provenance in every artifact
**Source:** `src/personacore/provenance.git_sha()` used at `build_retention_bin.py:177`,
`finetune_ab.py:329`
**Apply to:** `results/phase15_norms.json`, both PNG-producing runs' console output, the D-17
appended section
```python
        "git_sha": git_sha(),
        "built": time.strftime("%Y-%m-%d", time.gmtime()),
```

### Import ordering / ruff
**Source:** `pyproject.toml` (`line-length 100`, `select = ["E","F","W","I"]`), applied at
`plot_phase13.py:29-30`, `finetune_ab.py:38-51`, `teach_persona.py:63-87`
**Apply to:** all new `.py` files. Any import that must follow a side-effecting statement
(`matplotlib.use("Agg")`, `os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")`) carries
`# noqa: E402` **with the reason in the same comment**. `make lint` = `ruff check . && ruff format --check .`

### Test module docstring = numbered behavior inventory
**Source:** `tests/test_slim_checkpoint.py:1-27`, `tests/test_phase13_plots.py:1-15`,
`tests/test_phase14_scoring.py:1-27`
**Apply to:** all three new test files

Opens with the requirement IDs, then `CPU-only, GPU/MPS-free[, no torch]`, then a numbered list of
each test with the one-line failure it prevents, then any scripts-load or fixture justification.
D-08's "why extraction is not permanently tested" sentence lives in this block.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/test_phase15_docs.py` | test (doc integrity) | — | No existing test asserts a committed **markdown** file's prose against a source. The nearest two are partial and should be combined: `tests/test_phase14_demo.py:126` reads a committed file's text at module scope (`_DEMO_SOURCE = (...).read_text(encoding="utf-8")`) and asserts substrings against it, and `tests/test_phase14_demo.py:580-596` pins a committed file with a diff against a recorded SHA — *"a diff against a pinned commit, re-run on every CI run, which catches a staged edit and outlives the phase that made the decision."* `tests/test_phase14_scoring.py:551,608,614` asserts `"## Threats To Validity" in report.read_text(...)` but only on a report the test itself just wrote into `tmp_path`, never on committed evidence. D-15/D-16/D-17's checks (quote is a byte-exact substring of its cited source; README number matches its source report; the appended section is dated and follows every Phase 13 heading) are a **new** test genre for this repo — build it from the `read_text` + substring register plus the AST test's meta-guard habit (assert the scan found something before asserting it found nothing bad). |

---

## Metadata

**Analog search scope:** `scripts/` (28 files), `tests/` (66 files), `src/personacore/`,
`results/`, `docs/REPORT.md`, `README.md`, `demo.ipynb`
**Files opened and excerpted:** 13 (`scripts/plot_phase13.py`, `scripts/finetune_ab.py`,
`scripts/teach_persona.py`, `scripts/build_retention_bin.py`, `scripts/phase14_recall.py`,
`src/personacore/continual/fisher.py`, `tests/test_phase13_plots.py`,
`tests/test_slim_checkpoint.py`, `tests/test_phase14_scoring.py`, `tests/test_phase14_demo.py`,
`results/retention_anchors.json`, `results/phase13_ab_report.md`, `README.md`, `demo.ipynb`)
**Pattern extraction date:** 2026-08-02
