---
phase: 25-frontier-sweep-and-the-existence-gate-verdict
plan: 09
subsystem: figures
tags: [figure-guard, ast, allow-list, front-03, d-33, matplotlib, watched-red]

requires:
  - phase: 15-figures-writeup
    provides: "tests/test_phase15_plots.py::test_plotting_module_never_opens_a_checkpoint — the three-part figure guard (import walk + meta-guard, .pt constant walk, fresh-interpreter sys.modules probe) this plan RETARGETS"
  - phase: 25-08
    provides: "scripts/phase25_record.py — FRONTIER_RECORD (the artifact path the plotter's own constant is asserted equal to), epsilon_bearing_reading's inline draws_per_question / draws_per_question_source, and the per-point record shape the panels read"
provides:
  - "scripts/plot_phase25.py — the Phase-25 privacy x utility plotter: DP arm (epsilon x taught recall) and adversarial arm (mixture ratio x taught recall), each at n=8 and n=64, drawn from results/phase25_frontier.json and nothing else"
  - "ALLOWED_READS = (FRONTIER_RECORD,) — FRONT-03's single-source promise as a module constant, enforced by a test rather than declared"
  - "tests/test_phase25_plots.py — the retargeted guard: three Phase-15 parts PORTED, the artifact allow-list clause AUTHORED, four planted REDs watched, all plants in tmp_path"
affects: [25-19]

tech-stack:
  added: []
  patterns:
    - "an allow-list expressed as a module constant and enforced by an AST walk that resolves the path operand of every read-shaped call, reporting offenders with their lineno"
    - "guard engines that take SOURCE TEXT rather than a module, so the same implementation runs against the real file and against a planted scratch copy — a guard that can only read the real file can never be watched failing"
    - "endswith over `in` for artifact-name sweeps: the module's own prose names other artifacts while explaining that it opens none of them, and a substring check over prose is the RPT-02 false-RED class"
    - "an annotated figure value DERIVED from the plotted data (the pool ceiling is the largest swept ratio) rather than read from a key or retyped — it cannot drift because there is nothing to drift from"

key-files:
  created:
    - scripts/plot_phase25.py
    - tests/test_phase25_plots.py
  modified: []

key-decisions:
  - "Parts (a), (b) and (c) were PORTED; the artifact allow-list clause was AUTHORED. Verified at HEAD rather than assumed: the three parts are live at tests/test_phase15_plots.py:326 (import walk + meta-guard), :334 (.pt constant walk) and :342 (fresh-interpreter probe), and `grep -in 'allow|ALLOWED' tests/test_phase15_plots.py` returns NOTHING — Phase 15's guard has no allow-list of any kind, only a .pt prohibition. The retarget is not pure reuse and is not recorded as such."
  - "The four panels ship as TWO figures of two panels each, not one figure of four. The two arms must not share an x-axis (D-19, D-23: the adversarial axis is a mixture ratio and carries no epsilon), and two separate figures is the strongest available form of that — a shared figure invites a shared axis at the next edit."
  - "The pool ceiling is DERIVED from the plotted data as the largest swept ratio, not read from a key and not retyped. It renders as 1.9090909090909092 on the fixture because that is the artifact's own upper extreme; a literal here would be a number the artifact could contradict."
  - "The never-taught floor is the ONE new top-level section the plotter requires of the artifact (`never_taught_floor`, carrying nontarget_successes / nontarget_questions / tier — results/phase23_never_taught.json's `pooled` block verbatim, D-42's own discipline). Its rate is computed from those counts at plot time; the floor is drawn as the shared lower-left reference for BOTH arms (D-19)."
  - "The sigma=0 control is drawn as a horizontal reference line with its own label, never given a fabricated x coordinate: it carries `epsilon: None` and cannot sit on an epsilon axis at all. It IS the sigma->0 end of the curve, and the label says so."
  - "The .json-literal sweep uses endswith, never `in`. MEASURED: the plotter's docstring names results/phase23_never_taught.json in prose while explaining the allow-list, so a containment check would go false-RED on the very sentence that documents the guard."

metrics:
  duration: ~65 min
  completed: 2026-08-31
  tasks: 2
  commits: 2
  tests-added: 12
  suite: "1859 passed, 1 skipped (1194.65s) — +12 passed vs the 1847/1 wave-3 baseline, 0 failed, skips unchanged"
---

# Phase 25 Plan 09: The Frontier Plotter and Its Retargeted Figure Guard — Summary

FRONT-03's "figures are drawn only from the committed artifact" stopped being a convention and
became a checked mechanism: `scripts/plot_phase25.py` draws four panels from
`results/phase25_frontier.json` and nothing else, and `tests/test_phase25_plots.py` proves it by
resolving the path operand of every read-shaped call in the module's AST.

## What shipped

**`scripts/plot_phase25.py`** (commit `95b0b02`) — imports `json`, `pathlib`, `argparse` and
`matplotlib` only, with `matplotlib.use("Agg")` before `pyplot`. No torch, no numpy, no `.pt`
literal, no checkpoint read.

| Figure | Panels | x-axis | y-axis |
|---|---|---|---|
| `phase25_frontier_dp.png` | `dp_n8`, `dp_n64` | measured epsilon (log) | taught recall, from the record's own numerator/denominator |
| `phase25_frontier_adversarial.png` | `adv_n8`, `adv_n64` | mixture ratio, terminating at the pool ceiling | the same utility axis |

Every marker's shape carries its point's `k`, read inline from the record (D-21), with the legend
naming the constant the `k` came from. Every annotated value is read from the artifact or derived
from it at call time — the floor from its own counts, the ceiling from the largest swept ratio, the
adversarial caption's D-23 sentence selected out of the record's own `epsilon_omitted_reason`.

**`tests/test_phase25_plots.py`** (commit `83298f8`) — 12 tests, **0 skipped**.

## Three parts PORTED, one clause AUTHORED

This is a retarget, not pure reuse, and the two halves are recorded separately because the plan's
own `must_haves` says a planner would otherwise take the reuse claim literally.

| Part | Origin | Verified against the current tree |
|---|---|---|
| (a) AST import walk + meta-guard | PORTED from `tests/test_phase15_plots.py:326` | live at HEAD; meta-guard kept verbatim in structure (`assert imported, "...the walk stopped working"`) |
| (b) AST `.pt` string-constant walk | PORTED from `tests/test_phase15_plots.py:334` | live at HEAD; extended with a `checkpoints/` containment clause |
| (c) fresh-interpreter `sys.modules` probe | PORTED from `tests/test_phase15_plots.py:342` | live at HEAD; retargeted to take a module path so it can also run against a planted copy |
| (d) the artifact allow-list | **AUTHORED here** | `grep -in "allow\|ALLOWED" tests/test_phase15_plots.py` returns **nothing** — Phase 15's guard has no allow-list, only a `.pt` prohibition |

`.venv/bin/python -m pytest tests/test_phase15_plots.py -q` → **7 passed** — the original guard is
untouched and still green.

## The four watched REDs — verbatim

Every plant lived in a scratch copy under `tmp_path`; `git status --porcelain scripts/` returned
`''` immediately after each one, asserted inside each test.

1. **Planted `import torch`** — the ported import walk:
   `plot_phase25 imports torch — D-33 violated ({'torch', 'argparse', 'matplotlib', 'json', 'pathlib'})`
2. **Planted `.pt` literal** — the ported constant walk:
   `plot_phase25 names a checkpoint file: ['checkpoints/persona_adapter.pt']`
3. **Planted second read** — the AUTHORED allow-list clause:
   `plot_phase25 reads [('results/phase23_cost.json', 436)] — outside ALLOWED_READS ['/Users/juliorcoelho/PersonaCore/results', '/Users/juliorcoelho/PersonaCore/results/phase25_frontier.json', 'phase25_frontier.json', 'phase25_frontier_adversarial.png', 'phase25_frontier_dp.png', 'results', 'results/phase25_frontier.json']. FRONT-03 promises every figure is drawn from the frontier artifact and nothing else`
   (the offender travels with its `lineno` — 436 — the `tests/test_phase22_dpsgd_ast.py` register)
4. **Planted torch-loading import chain, under the child probe** — the probe returned **1**, not 0:
   `the plotting module transitively imports torch — D-33 violated`

## The guard is guarding something that works

`test_the_plotter_renders_from_a_fixture_frontier` builds a schema-valid frontier in `tmp_path`
(8 DP points across both capacities including both sigma=0 controls, 8 adversarial points across
both capacities, plus the `never_taught_floor` block; 8,305 bytes) and renders through `main()`:

- `phase25_frontier_dp.png` — **128,240 bytes**
- `phase25_frontier_adversarial.png` — **136,386 bytes**

Both non-empty, both written into `tmp_path`, so the render can never clobber a committed
`results/` figure. With the artifact absent, `.venv/bin/python scripts/plot_phase25.py` exits **1**
with a sentence naming the missing file and plan 25-19 as its producer — not a traceback.

## Deviations from Plan

### Measured corrections to plan-time prose

**1. [Rule 1 — stale figure] The plan's `<environment>` baseline of "1647 passed, 1 skipped" is
stale.** MEASURED: the wave-3 baseline handed to this executor is **1847 passed, 1 skipped**, and
HEAD after this plan reads **1859 passed, 1 skipped** in 1194.65 s. Delta **+12 passed** — exactly
the 12 tests added here — **0 failed**, skips unchanged. The plan's 1647 is the wave-1 number.

**2. [Rule 1 — name resolved from code] D-21's `k_source` is not the per-point record's field
name, and the wave-2 memo that `k_source` "appears NOWHERE in the repo" is FALSE at HEAD.** Both
readings, measured:
- The per-point epsilon-bearing reading writes `draws_per_question` and
  `draws_per_question_source` (`scripts/phase25_record.py:382-407`). The plotter reads those.
- `k_source` **does** exist at HEAD — as a real JSON field of a *different* record,
  `scripts/phase25_watch.py:175` (`"k_source": "mitigation_budget.FULL_FIDELITY_K, promoted by
  D-11"`), and as prose in `scripts/phase25_record.py:383`. `scripts/phase23_run.py:4337` carries
  `curve_k_source`.
The conclusion the memo drew survives — the point-record spelling is `draws_per_question_source`
and the plan's `k_source` must not be retyped into the plotter — but the blanket "nowhere in the
repo" reading does not, and is corrected here rather than inherited.

**3. [Rule 3 — name resolved from code] `taught_recall` is not a field `build_point_record`
emits.** MEASURED: `scripts/phase25_record.py::build_point_record` has no recall field at all; the
name is fixed by the driver plans that write it — `25-15` asserts
`(b['taught_recall']['numerator'], b['taught_recall']['denominator']) == (790, 1008)` on the
control record and `25-12` asserts the same `{numerator, denominator}` shape on the sigma_hi probe.
The plotter reads that shape and computes the rate at plot time, so the utility axis is COUNTS in
and a rate out — never a stored rate.

### Design choices the plan left open

**4. Four panels ship as TWO figures.** The plan says "four panels"; the same task's `read_first`
says the two arms "need two x-axes and must not share one". Two figures of two panels each is the
strongest form of that separation. Recorded because a reader counting PNGs will find two, not four
or one.

**5. The plotter's artifact contract, and the forward coupling to 25-19.** Plan 25-19 Task 2 states
`git diff --exit-code -- scripts/plot_phase25.py` must exit 0 — the plotter is **run**, not edited —
so the field names chosen here are a contract the assembly must satisfy. Kept as small as possible:
- `points` — mapping of point key -> record; each record carrying `arm`, `axis`, its own axis value
  under that name, `epsilon` (nullable), `taught_recall` as `{numerator, denominator}`, and
  `draws_per_question` / `draws_per_question_source`. All four arms must be present.
- `never_taught_floor` — `results/phase23_never_taught.json`'s `pooled` block verbatim
  (`nontarget_successes`, `nontarget_questions`, `tier`).
- The pool ceiling needs **no key**: it is derived as the largest swept ratio.
- The adversarial caption's D-23 sentence is selected from an adversarial point's own
  `epsilon_omitted_reason`, which `build_point_record` already writes
  (`ADVERSARIAL_MAKES_NO_FORMAL_CLAIM`).
Every one of these is validated on load with a refusal naming the offending key and the point, so a
mismatch at 25-19 is a readable sentence rather than a blank panel.

**6. `ARTIFACT_PRODUCER` names the plan, not a command.** The first draft named an invocation
(`python -m scripts.phase25_record`) that does not exist — `scripts/` is not a package. Corrected
before commit to name plan 25-19's write-once assembly in `scripts/phase25_record.py`.

No auto-fixes to other modules were needed. No architectural changes. No package installs.

## Guarded modules

`git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py
scripts/mitigation_unit.py scripts/phase18_extraction.py pyproject.toml` exits **0** — the four
ancestry-guarded modules and `pyproject.toml` are byte-unchanged. No new dependency: matplotlib was
already pinned (3.10.9 in the venv). `make lint` exits 0.

## Known Stubs

None. The plotter is complete and exercised end-to-end against a fixture; it has no data source
wired to a placeholder. The real artifact does not exist yet by design — plan 25-19 assembles it —
and the plotter refuses readably until it does.

## Threat Flags

None. No network endpoint, no auth path, no schema at a trust boundary was introduced. The module
reduces attack surface: it is provably incapable of deserializing a checkpoint.

## Verification

```
.venv/bin/python -m pytest tests/test_phase25_plots.py -v   ->  12 passed  (0 skipped)
.venv/bin/python -m pytest tests/test_phase15_plots.py -q   ->   7 passed
.venv/bin/python scripts/plot_phase25.py                    ->  exit=1, readable refusal
.venv/bin/python -m pytest tests/ -q                        ->  1859 passed, 1 skipped in 1194.65s
make lint                                                    ->  All checks passed!
git diff --exit-code -- <4 guarded modules> pyproject.toml   ->  exit 0
```

## Self-Check: PASSED

- `scripts/plot_phase25.py` — FOUND
- `tests/test_phase25_plots.py` — FOUND
- commit `95b0b02` — FOUND
- commit `83298f8` — FOUND
