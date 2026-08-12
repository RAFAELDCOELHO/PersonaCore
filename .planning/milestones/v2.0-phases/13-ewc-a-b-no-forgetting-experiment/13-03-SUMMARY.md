---
phase: 13-ewc-a-b-no-forgetting-experiment
plan: 03
subsystem: evidence
tags: [visualization, matplotlib, qualitative-samples, ewc, forgetting, mps, reproducibility]

# Dependency graph
requires:
  - phase: 13-ewc-a-b-no-forgetting-experiment
    plan: 02
    provides: results/phase13_{naive,ewc}/run.csv arm curves, both step-4000 endpoint checkpoints
  - phase: 12-stage-2-conversational-fine-tune
    provides: results/ft_lam_*.csv lambda sweep endpoints, finetune_smoke_report.md Stage 2/3 lambda=0 point, frozen tokenizer
provides:
  - results/phase13_forgetting_curve.png — VIZ-01, retention + acquisition panels, both 4000-step arms
  - results/phase13_frontier.png — VIZ-04, six labeled lambda points at the 1250-step sweep endpoints
  - results/phase13_retention_samples.md — D-12 one-run both-endpoint samples with measured proxies
  - scripts/plot_phase13.py — regenerable figures from committed CSVs only
  - scripts/make_retention_samples.py — seeded, one-run, both-arm sampling protocol
  - "MEASURED FINDING for the report: both arms leak role tokens mid-story (79 naive / 70 EWC)"
affects: [13-04, phase-15-writeup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "matplotlib.use(\"Agg\") before pyplot in scripts — first savefig path in the repo (plots previously lived only in demo.ipynb)"
    - "out_dir-parameterized plot functions so a tmp_path smoke test can never clobber committed figures"
    - "Warm-sampling RNG re-seeded per ARM rather than once per run — both arms draw the identical stream, so a text difference is a weight difference"

key-files:
  created:
    - scripts/plot_phase13.py
    - tests/test_phase13_plots.py
    - results/phase13_forgetting_curve.png
    - results/phase13_frontier.png
    - scripts/make_retention_samples.py
    - results/phase13_retention_samples.md
  modified: []

key-decisions:
  - "13-03: acquisition panel uses a log y-axis — the step-0 anchor is 31.90 and both arms land at 4.19/4.57, so a linear axis collapses the entire arm separation into one pixel band"
  - "13-03: the frontier gets NO 2.1066 dashed line (VIZ-01 only, as planned) — the sweep points are sub-bin retention measurements and overlaying the full-val unmasked headline there would invite exactly the Pitfall-3 conflation the constant comment warns about"
  - "13-03: role-token leakage reported as measured (79 naive / 70 EWC) with the 'expected 0' framing replaced by '0 = uncontaminated' plus an explicit note that teacher-forced retention PPL and free-running mode adherence are DIFFERENT quantities — the samples file states the finding, the 13-04 report owns the interpretation"

requirements-completed: []  # VIZ-01/VIZ-04 artifacts exist; DEMO-04 still needs the 13-04 report.

# Metrics
duration: 24min
completed: 2026-08-01
---

# Phase 13 Plan 03: Figures + Retention Samples Summary

**Both committed figures (VIZ-01 forgetting curve with the dashed 2.1066 headline and an acquisition companion panel; VIZ-04 six-point lambda frontier at the 1250-step sweep endpoints) plus the D-12 retention samples — which surface a load-bearing honest finding: the retention-PPL gap does NOT translate into free-running story-mode adherence, because both arms leak dialogue role tokens mid-story.**

## Performance

- **Duration:** ~24 min (including two full sampling passes for a reproducibility check)
- **Tasks:** 2
- **Files created:** 6

## Accomplishments

### VIZ-01 — `results/phase13_forgetting_curve.png`

Two panels, both 4000-step arms, stated in the figure title ("4000-step arms, identical
config except λ"). Left panel is the forgetting axis: naive (λ=0, C1) climbs 2.11 → 8.52
while EWC (λ=0.01, C0) rises once to ~3.9 and then stays flat for 3750 steps, with
`axhline(2.1066, "--", gray)` as the v1.0 headline reference. The visual claim is
immediate: the constrained arm's retention curve is essentially horizontal.

Right panel is the acquisition companion — dialogue PPL on a **log** y-axis, because the
step-0 anchor is 31.90 and both arms converge near 4.2/4.6; on a linear axis the entire
separation the report discusses is one pixel band. Both arms drop together and stay
together, which is the visual form of "EWC's retention win is not bought by failing to
learn the task".

### VIZ-04 — `results/phase13_frontier.png`

Six points, labeled λ=0 through λ=100, ordered along a dotted trade-off curve, with
"1250-step sweep endpoints" in the title AND a gray sub-caption "1250-step sweep endpoints
(LR 9e-5, unmasked) — not the 4000-step A/B arms". The elbow at λ=0.01 (the headline λ) is
visible without annotation: it recovers most of the retention loss for ~0.28 dialogue PPL,
while λ≥10 buys the last of the retention at 2-4× the dialogue cost.

**The Pitfall-1 trap is pinned by a test, not by care.** `results/ft_lr_9e-5.csv` — the λ=0
arm — has no `retention_ppl` column, so a natural "glob the sweep CSVs" implementation
yields FIVE points and silently deletes the collapse baseline the whole frontier is measured
against. `LAMBDA0_POINT = {"dialog_ppl": 4.4453, "retention_ppl": 5.9553}` carries its
citation (smoke report Stage 2/3, commit `666d096`) in the hardcode-with-citation register,
and `test_frontier_has_six_points` asserts the count, the label order, and that λ=0 is the
constant rather than a CSV read.

### D-12 samples — `results/phase13_retention_samples.md`

Ten held-out TinyStories prefixes selected with a local `default_rng(1337)` (global streams
untouched), each encoded through the frozen tokenizer and truncated to its first 32 ids —
never a hand-formatted string. Both endpoint checkpoints are loaded and sampled in **one
script run**, and `seed_everything(1337)` runs before *each arm* rather than once per run,
so both arms draw warm samples from the identical RNG stream: any text difference is a
weight difference. 40 generations total (10 prompts × 2 modes × 2 arms), all counted in the
proxies.

**Generation is bit-reproducible across processes.** The samples were generated twice in
separate processes; `diff` over the entire sample body is empty. This is a stronger
reproducibility statement than Plan 13-02 could make for eval PPL (~1e-8 MPS reduction-order
variance) and is safe to state in the report: the sampling path is argmax/seeded-multinomial
over single-batch forwards, with none of the multi-batch reductions that make eval PPL
non-deterministic.

## The finding this plan surfaces

| arm | endpoint | eos-stop fraction | mid-story role-token leakage |
| --- | --- | --- | --- |
| naive (λ=0) | 4000 | 0/20 = 0.00 | **79** |
| ewc (λ=0.01) | 4000 | 1/20 = 0.05 | **70** |

Both arms, prompted with "Once upon a time, there was a big farm...", continue for a few
tokens and then emit `<|user|>` and drop into PersonaChat dialogue. The 4.63-PPL retention
gap that passes the pre-registered gate at 33.6× margin **does not** produce a qualitatively
intact story generator in the EWC arm at this budget.

This is not a defect in the sampling code and not a contradiction of the gate — teacher-forced
retention PPL (probability assigned to the true TinyStories continuation) and free-running
mode adherence (what the model does when it drives itself for 128 tokens) are different
quantities, and EWC at λ=0.01 clearly preserves the former far better than the latter. The
samples file states this explicitly and defers interpretation to Plan 13-04, which owns
`results/phase13_ab_report.md`. **Plan 13-04 must not claim qualitative retention** — the
committed evidence does not support it.

The low stop fraction is a budget artifact, not an adherence failure, and is labeled as such
in the file: 128 new tokens is far short of a full TinyStories story, so nearly every
completion is truncated rather than eos-terminated.

## Task Commits

1. **Task 1 (RED): failing plot contracts** — `2b2f9c5` (test)
2. **Task 1 (GREEN): plot script + both PNGs** — `b0b0cf3` (feat)
3. **Task 2: D-12 retention samples** — `4f4a58d` (feat)

## Files Created

- `scripts/plot_phase13.py` — pure `csv` + `matplotlib`, `Agg` backend, no torch import; both
  plot functions take an `out_dir` and return the written path, so the smoke test renders into
  `tmp_path` and can never overwrite the committed figures.
- `tests/test_phase13_plots.py` — 3 tests: six-point frontier with exact endpoint literals,
  the 2.1066-vs-2.107553 baseline pin, and the tmp_path render smoke.
- `results/phase13_forgetting_curve.png` (105 KB), `results/phase13_frontier.png` (63 KB) —
  dpi 150, committed next to the report (`.gitignore` carries no image exclusion).
- `scripts/make_retention_samples.py` — refuse-to-rerun guarded, trusted-only `torch.load` on
  both arm checkpoints, seeded shared prompt set, per-arm proxies.
- `results/phase13_retention_samples.md` — proxies table + 10 prompt sections × 2 arms ×
  (greedy, warm).

## Decisions Made

- **Log-scale acquisition panel.** Deliberate: the honest alternative (linear) hides the very
  comparison the panel exists to show. Both axes are labeled with direction ("lower = better").
- **No baseline line on the frontier.** The plan mandates the dashed 2.1066 only for VIZ-01.
  Adding it to VIZ-04 was tempting for readability but the sweep points are sub-bin retention
  measurements and the headline is a full-val unmasked number — overlaying them is the exact
  Pitfall-3 conflation the constant's comment exists to prevent.
- **`allowed_special="none"` when encoding prompts.** A held-out story is DATA: a literal
  `<|endoftext|>` inside one must byte-split, not become an atomic id in the prompt.
- **Re-seeded per arm, not per run.** Seeding once would give arm 2 a different RNG position
  than arm 1, making the warm comparison confounded by sampling noise.
- **Regenerated the samples once, on purpose.** After rewording the leakage framing I deleted
  the file and re-ran (the guard's intended regeneration path), which doubled as the
  cross-process determinism check reported above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Replaced the "(expected 0)" leakage framing with measured-fact framing**

- **Found during:** Task 2, after the first sampling run
- **Issue:** The planned proxies table annotated leakage as "(expected 0)", inherited from the
  Phase-12 transcript script where 0 was the realistic expectation. Measured values are 79 and
  70. A committed evidence file that prints "**79** (expected 0)" with no further word invites
  the reader to treat the result as a bug in the harness rather than as the finding it is — and
  a reader who skips to the figures would carry away "EWC prevents forgetting" qualitatively,
  which this evidence does not support. In a project whose core value is that the novel claim
  must be *true and demonstrable*, an evidence artifact that under-reports a negative result is
  the failure mode the phase's pre-registration discipline exists to prevent.
- **Fix:** Changed the annotation to "(0 = uncontaminated)" and added two short paragraphs to
  the samples file: one stating that both arms leak heavily and that teacher-forced retention
  PPL and free-running mode adherence are different quantities (with interpretation explicitly
  deferred to the report), one explaining that the 0.00-0.05 stop fraction is a 128-token budget
  artifact rather than an adherence failure.
- **Files modified:** `scripts/make_retention_samples.py`, `results/phase13_retention_samples.md`
- **Verification:** `grep "uncontaminated" results/phase13_retention_samples.md`; full suite green.
- **Committed in:** `4f4a58d`

**2. [Rule 1 - Bug] Frontier annotation clipped at the axis edge**

- **Found during:** Task 1 visual verification of the rendered PNG
- **Issue:** The λ=100 label (right-most point, dialogue PPL 16.21) rendered partly outside the
  axes box — a committed portfolio figure with a cut-off label.
- **Fix:** `ax.margins(x=0.13)`; re-rendered and re-inspected.
- **Files modified:** `scripts/plot_phase13.py`
- **Committed in:** `b0b0cf3`

---

**Total deviations:** 2 auto-fixed (1 honesty/evidence-integrity, 1 rendering bug)
**Impact on plan:** No scope change. All six planned artifacts shipped.

## Issues Encountered

- One ruff E501 on the proxies-table markdown line (implicit string concatenation across two
  source lines resolved it).
- The plan's acceptance criterion greps for the literal `default_rng(1337)`; the code follows
  the `make_transcripts.py` precedent of `default_rng(SEED)` with `SEED = 1337`, and the literal
  appears in the generated file's own header line — so the grep passes without duplicating the
  constant.

## Verification

- `.venv/bin/python -m pytest tests/ -x -q` → **284 passed, 1 skipped**
- `ruff check` + `ruff format --check` clean on all three new/changed source files
- `git ls-files results/phase13_*.png` lists both figures
- `git status --porcelain results/finetune_prod.csv` empty — no Phase-12 artifact touched
- Both figures inspected as rendered images, not merely asserted non-empty
- Sample body `diff` across two separate processes: empty

## Next Phase Readiness

Plan 13-04 has everything it needs to write `results/phase13_ab_report.md`:

- Figure paths to reference: `results/phase13_forgetting_curve.png`, `results/phase13_frontier.png`
- Samples path: `results/phase13_retention_samples.md`
- **Required report content from this plan:** the leakage finding (79 naive / 70 EWC) belongs
  in the D-05 threats-to-validity register alongside the MPS non-determinism footnote from
  13-02. The report may claim the pre-registered retention-PPL gate passed at 33.6× margin; it
  may NOT claim qualitative/generative retention.
- Safe reproducibility claims: training losses and weight-derived quantities are bit-identical;
  free-running generation is bit-identical across processes; eval PPL is NOT (~1e-8 relative).

## Self-Check: PASSED

All 6 created files exist on disk; `results/phase13_*.png`, `scripts/plot_phase13.py`,
`tests/test_phase13_plots.py`, `scripts/make_retention_samples.py`, and
`results/phase13_retention_samples.md` are all tracked by git. All three task commits
(`2b2f9c5`, `b0b0cf3`, `4f4a58d`) are present in git log. Both arm checkpoints remain on disk
and gitignored, untouched, for later phases.

---
*Phase: 13-ewc-a-b-no-forgetting-experiment*
*Completed: 2026-08-01*
