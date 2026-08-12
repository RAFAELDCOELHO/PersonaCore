# Phase 15: Figures & Writeup - Research

**Researched:** 2026-08-02
**Domain:** matplotlib figure generation from frozen checkpoints, pure-numpy rank statistics, honest-disclosure technical writing
**Confidence:** HIGH (every load-bearing fact verified by direct inspection of this repo's files and checkpoints)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Copied from `.planning/phases/15-figures-writeup/15-CONTEXT.md` `<decisions>`. **D-01..D-18 are
LOCKED. Research serves their execution and does not re-open any of them.**

**VIZ-03 panel comparability & color scale**

- **D-01: The naive and EWC delta panels MUST share one color scale.** This is the same
  discipline that put end-of-run over best-checkpoint in Phase 13's 2×2 — comparability over
  visual convenience. **If sharing one scale makes one panel look nearly flat or washed out
  relative to the other, that flatness IS the finding** (EWC constrains movement in absolute
  terms) and is reported as such, never hidden by independently rescaling each panel to look
  equally "busy."

  The **Fisher panel may use its own scale**, because its unit (squared-gradient magnitude) is
  not comparable to a weight-delta ratio. That is a **units argument, not a convenience
  argument** — and the distinction is load-bearing, because the units exemption must not become
  a loophole for rescaling anything that looks inconvenient. The figure caption and report text
  must state explicitly **which panels share a scale and why the Fisher panel does not**, so a
  reader is never left guessing whether the difference is intentional or an oversight.

- **D-02: Shared-scale range = full data range, nothing clipped.** `vmax` = largest cell across
  both arms; `vmin` = smallest **nonzero** cell across both arms (a log color scale needs a
  positive floor). No percentile clipping at either end — under D-01, compression is data.

  **Outlier disclosure (mandatory).** If the shared range does compress most of the grid
  visually, the report text accompanying the figure **must name the specific layer/projection
  driving `vmax`**, not just show the compressed figure and move on. A reader looking at a
  nearly-flat grid with one bright cell needs the caption to say *"layer N's projection
  dominates the range; see the per-layer table in [artifact] for the full distribution."* Same
  discipline as naming which template family drove a coarse held-out score in Phase 14, rather
  than leaving a visual oddity unexplained.

- **D-03: VIZ-02 and VIZ-03 get independent scales, plus a SPECIFIC non-comparability note.**
  They share the `‖ΔW‖_F/‖W₀‖_F` formula but come from different regimes, and the shared formula
  is exactly what invites the comparison that isn't valid.

  The note must **name the actual confounds**, not gesture at "different regimes" and stop:
  1. **parameter count** — 331,776 LoRA params vs the full model;
  2. **training budget** — the LoRA teaching run vs the full fine-tune step count;
  3. **that a smaller absolute ΔW magnitude for the adapter does NOT imply "more conservative"
     or "less effective" learning** — it reflects the adapter's parameter budget, not a quality
     comparison.

  This is the same specificity standard as D-02's vmax disclosure: name the actual driver.

- **D-04: The disclosure lives in BOTH the figure and the report, asymmetric by design.**
  Figure-side (subtitle / colorbar labels) is **terse** — enough to prevent a misreading when
  the PNG travels alone into a slide or README, not a paragraph competing visually with the
  data. Report-side carries the **full reasoning**, including D-03's named confounds. Mirrors
  Phase 14 D-18's own split (terse live UI panel, full committed harness provenance): same
  asymmetry of detail, same consistency requirement — **a reader comparing figure and report
  must never find them saying different things, only different amounts.**

**The committed norms artifact**

- **D-05: ONE committed JSON artifact serves both the caption's per-layer table and the figures'
  regeneration input** — not a prose-only table for the caption plus a separate intermediate for
  reproducibility. It closes the gap this discussion surfaced (VIZ-02/03 currently cannot be
  regenerated without the gitignored 278 MB checkpoints) **using work D-02's vmax disclosure was
  already going to require.** Same register as `scripts/plot_phase13.py`: every locked number in
  this project's most visible deliverable is re-derivable from committed material, not asserted.

  **Format: JSON.** The grid is ~100 numbers (6 layers × 6 projections × a few quantities) —
  human-readable, diffs meaningfully in git, and a reviewer can check a number without loading
  numpy. In-repo precedent: `results/retention_anchors.json`.

- **D-06: Every block carries regime + confound fields; the file carries a top-level
  comparison-basis note.** `regime`, `param_count`, `training_budget` (or equivalents) are
  present on **EVERY** block **including the fisher block** — not only on adapter/naive/ewc — so
  a reader parsing any single block in isolation still sees what it can and cannot be compared
  against.

  The file's top level additionally carries a short **machine-readable** note (not just
  block-level fields) stating explicitly which blocks share a comparison basis (**naive ↔ ewc:
  yes**) and which do not (**adapter ↔ either full-fine-tune block: no**). This is the third
  statement of the same non-comparability already locked for the figure (D-04) and the report
  (D-03) — now present in the data itself.

- **D-07: Extract, then plot from the artifact ONLY — enforced structurally.** One script reads
  checkpoints and writes the artifact; the plotting script reads **only** the artifact and never
  touches a checkpoint. The committed PNG then provably derives from the committed numbers, and
  regenerability is proven by construction rather than asserted.

  **Enforcement, same discipline as Phase 14 D-17/D-18:** a static check or import-time guard
  confirming the plotting module has **no code path that opens a `.pt` file** — ideally no
  `torch.load` import in the plotting module at all. **Prove it by construction, not by
  convention** (a docstring or comment saying "reads only the artifact" is exactly the kind of
  claim-without-enforcement this project has repeatedly had to convert into a test).

- **D-08: Permanent CPU-only test on the artifact→figure path only, with the reason stated.**
  Extraction needs the gitignored 278 MB checkpoints and cannot run in the CPU-only suite. The
  permanent test covers plot-from-artifact; its docstring states **explicitly why extraction is
  not permanently tested**, so a future reader does not assume the test covers the whole
  pipeline. Exactly Phase 14 D-07's split (tokenizer half permanent, guessability half
  checkpoint-specific).

  **The extraction script's docstring must name the specific checkpoints it depends on** —
  `checkpoints/persona_adapter.pt`, `checkpoints/phase13_naive_latest.pt`,
  `checkpoints/phase13_ewc_latest.pt`, `checkpoints/fisher_tinystories.pt`, `checkpoints/best.pt`
  — and state, same as Phase 14 D-07's guessability half, that **re-running extraction against a
  future checkpoint requires a fresh manual run producing a fresh committed artifact**, not a
  test that silently stays green while checking nothing.

  **If cheap:** one offline-only integration test, `skipif`-gated on checkpoint presence, that
  runs extraction end-to-end locally and asserts the artifact it produces matches the committed
  one **byte-for-byte**. Not required for CI — available to re-verify before any future
  re-extraction lands. (Pattern confirmed present: `tests/test_forbid_ids.py:196`,
  `tests/test_lora_artifact.py:238`, `tests/test_phase14_demo.py:606,620`,
  `tests/test_slim_checkpoint.py:168`, documented at `tests/test_slim_checkpoint.py:18`.)

**The "EWC dodges high-Fisher coordinates" claim**

- **D-09: MEASURED, not visual-only — and the rule is committed BEFORE the number.** An
  unmeasured visual claim on the project's signature figure would repeat exactly the
  declared-vs-structural-guarantee gap Phase 14's learnings named as this work's most recurring
  failure mode. The decision rule (what counts as "EWC avoids high-Fisher coordinates") is
  written and committed **before** the correlation is computed from real artifact data — same
  blind-rule discipline as Phase 13 D-09/D-10, git history as proof
  (`scripts/finetune_smoke.py` precedent), never a number chosen after seeing whether it supports
  the roadmap's claim.

  **Cost: zero new data collection.** Fisher magnitude and Δ reduction per block are already
  fields in the D-05 artifact. Only the decision rule needs authoring up front.

- **D-10: Statistic = Spearman ρ, per-block, n = 36, between Fisher magnitude and
  (naiveΔ − ewcΔ); predicted sign POSITIVE.**
  - **Granularity: per-block** — the same 6 layers × 6 projections = **36** cells the figure
    draws (`ModelConfig.n_layer = 6`), so the statistic describes exactly what a reader sees. No
    artifact schema change; no gap between the claim and the picture.
  - **Pairing: Δ reduction (naiveΔ − ewcΔ).** A positive correlation means EWC pulls movement
    back hardest where Fisher is highest — literally the dodging claim. Using both arms isolates
    the penalty's effect instead of describing one arm's shape; the naive arm exists precisely
    to remove that confound.
  - **The pre-registered rule states the predicted sign explicitly.** A negative or near-zero
    correlation means the visual claim does not hold at a measurable level, and **that outcome
    is stated as plainly as a positive one** — never softened because it contradicts the
    roadmap's framing.
  - **The rule must state up front that n = 36 limits what can be claimed:** report the
    coefficient **AND** its confidence interval, not a bare point estimate implying more
    precision than 36 cells support. It must also pre-specify that a correlation present but not
    statistically distinguishable from zero is reportable as **"suggestive but not statistically
    demonstrated at n = 36"** — the same register as every other underpowered-but-honest finding
    this project has logged, rather than either overclaiming significance or discarding the
    number.

- **D-11: Gated on sign; magnitude descriptive. The gate requires BOTH a positive sign AND a
  confidence interval excluding zero.**
  - ρ = +0.15 with a CI spanning zero **is a MISS** — recorded unamended per Phase 14 D-12's
    verbatim gate-miss policy, reported in the "suggestive but not statistically demonstrated at
    n = 36" register (reported, **not discarded**, and **not softened into a passing verdict**).
    The roadmap's SC2 wording narrows accordingly, exactly as a gate miss would in any other
    phase.
  - The **descriptive half**: the coefficient's magnitude and CI are reported alongside the sign
    verdict, framed explicitly as *"the sign is the falsifiable claim; the magnitude is reported
    honestly given n = 36 and is not itself pass/fail."*
  - This is the correct analog to Phase 13 D-06's acquisition-side register — **not a full
    exemption from gating**, but the same principle of gating only the part of the claim the
    sample size can actually support.

  *Provenance note:* this rule initially admitted two contradictory readings ("gate the sign
  only" vs "indistinguishable from zero is a miss"). The ambiguity was surfaced and closed
  **before any correlation was computed** — deliberately, so it could not be resolved in
  whichever direction happened to look better.

- **D-12: Spearman ρ + permutation test + bootstrap CI, pure numpy, SEEDED.** scipy is **not** a
  dependency (`pyproject.toml`: `numpy~=2.4`, `regex~=2026.5`; torch is an extra) and must not
  become one for a single correlation — the machinery is ~15 lines of numpy, which suits the
  from-scratch ethos.
  - Spearman over Kendall on **readability** grounds: both are rank-based and therefore already
    robust to the heavy-tailed Fisher magnitudes, so there is no edge-case advantage to trade
    readability for.
  - Resampling over closed-form Fisher-z because the z-transform's normality assumption is the
    shakiest of the options at n = 36.
  - **Both the coefficient and the CI computation are pinned to a documented random seed** for
    the permutation/bootstrap resampling — same discipline as every other seeded calculation
    here — so the gate verdict is **reproducible byte-for-byte from the committed artifact**,
    not dependent on whatever shuffle order a given run happens to draw.
  - **The ~15 lines carry their rationale in comments** (why Spearman over Kendall, why
    resampling over Fisher-z) so a future reader sees the choice was deliberate, not default.

**Narrative surfaces, register & Limitations (DOC-02)**

- **D-13: `docs/REPORT.md` is EXTENDED; the notebook is NEW and separate.**
  - **REPORT.md:** every v1.0 section stays **textually untouched** (Phase 14 D-12/D-17's
    "honest results stand unamended"), with a **dated Milestone 2 boundary marker** inside the
    file. One report a reader goes through front to back; the `m1-demo-v1` release tag already
    preserves the v1.0 file as shipped.
  - **Notebook:** a **new** v2.0 notebook, **self-contained and runnable independently** of the
    v1.0 notebook — no shared cell state, no implicit checkpoint dependency inherited from the
    M1 file — so a reader can run either standalone without the other's artifacts present.
    **Both notebooks state this independence explicitly in their opening cells**, so a reader
    isn't left to discover it by hitting a failure.
  - The v1.0 notebook's "re-cited, never recomputed" principle (its own cell-3 heading) carries
    forward to the v2.0 notebook.

- **D-14: REPORT.md v2.0 = Decision sections AND a results narrative, with strictly
  NON-OVERLAPPING content.**
  - **Decision sections** document the **CHOICE** and its rationale at the moment it was locked
    (what was decided, why, against what alternative) — same form as the existing 15, one per
    major D-XX already on record.
  - **The results narrative** documents the **OUTCOME** across the three experiments (Phase 12
    §8's negative verdict, the A/B's retention/acquisition numbers, the recall gate's pass/fail)
    tied together as a single story: what was tested, what the evidence showed, what remains
    uncertain. It **never re-explains why a choice was made** — only what resulted from it.
  - **The test:** a reader must be able to skip the Decision sections and still follow the
    results narrative as a complete story, and skip the results narrative and still find each
    individual choice justified in its own section. The two serve **different readers with
    different intent** (auditing a specific choice vs understanding what the milestone proved),
    not the same reader twice.

- **D-15: Limitations aggregates ALL EIGHT honest negatives, each QUOTING its source exactly.**
  One self-contained section; a reader learns every bound on the claims without opening
  `results/`.
  - Each entry **quotes the source report's exact wording** — not summarized, not softened, not
    reordered for flow — and links to the specific section.
  - If an entry's original wording is long, **truncate visibly** (ellipsis + link to the full
    passage) rather than paraphrase to shorten. **Paraphrase-to-shorten is precisely the drift
    vector this rule exists to close** — the D-17/D-18 mitigation applied to prose instead of
    code.
  - **Order the eight by WHICH CLAIM THEY BOUND**, not by severity and not by how comfortable
    they are to read, so the ordering itself does not editorialize about which negatives matter
    more.
  - The eight (planner to confirm exact wording and source line from each report): λ*=None
    (Phase 12 §8); Phase 14 D-20's base-cannot-extract-from-its-own-context; the
    +224.81% PPL collapse without replay; the 1/1944 question-fairness control; the soft-tier
    exclusion from the recall gate; Phase 14 D-22's reversal-curse scope narrowing; the noise
    floor not re-verified at production budget (Phase 13 D-05); and the 547-live-ids /
    dead-embedding disclosure carried forward from v1.0.

- **D-16: README carries THREE headline numbers, each qualified inline at 547-live-ids density.**
  The three: **recall rate against its gate**, **retention delta from the A/B**, and **the Phase
  11 token inflation tax** — carried forward, not only the two new v2.0 numbers.
  - Each number's qualifier appears **in the same sentence or bullet**, at the same density as
    the existing 547-live-ids line — **never a number followed by a separate "see Limitations"
    pointer.** The front page is where a claim is most likely to be read without its context, so
    it is where the caveat matters most.
  - If a headline number carries one of D-15's eight limitations, **that limitation's short form
    belongs inline in README too**, with the full quoted version still living in Limitations.
    README entry = terse form; Limitations = full form — the same asymmetry-of-detail principle
    already locked in D-04 for the figure disclosure.

**Verdict placement & VIZ-02 disclosure**

- **D-17: The correlation verdict lands as a new section appended to
  `results/phase13_ab_report.md`**, immediately adjacent to the Fisher/delta data it is computed
  from. The section carries the pre-registration table, the seed, the sign + CI result, and the
  D-11 miss policy if it misses.

  **REPORT.md cites the verdict with the D-16/D-04 terse-form/full-form asymmetry** — a sentence
  stating pass/fail and the correlation value, linking to the full pre-registration table in
  `phase13_ab_report.md`, **not restating the table**.

  **Constraint (follows from Phase 14 D-12's separation register, not separately asked):**
  `results/phase13_ab_report.md` is committed Phase 13 evidence. The appended section must be
  **explicitly dated and marked as Phase 15 material**, visibly separate from Phase 13's
  pre-registered content — the same separation Phase 14 D-12 requires between a verdict and
  anything written after it. Appending must not blend into or appear to amend Phase 13's
  recorded results.

- **D-18: VIZ-02 gets the same outlier-naming discipline as VIZ-03.** VIZ-02's caption and
  report text name the specific layer/projection driving its color range whenever that range is
  dominated by an outlier cell, using the **same wording pattern as D-02's disclosure** and
  pointing at the **same committed per-layer artifact**. VIZ-02 is single-panel so D-01's
  shared-scale argument does not reach it — but a lone hot coordinate flattening the adapter
  heatmap is the same reader-confusion failure. **No new data collection:** the D-05 artifact
  already carries adapter ΔW per layer per projection.

### Claude's Discretion

- **JSON schema field names and nesting** for the D-05 artifact (the *required content* is fixed
  by D-06; the spelling is not).
- **Permutation count** for D-12's test (n = 36 makes full enumeration of 36! impossible;
  ~10⁵ random shuffles is the conventional range) and the bootstrap resample count.
- **Plot styling** — colormap choice, figure dimensions, panel arrangement, font sizes, PNG vs
  additional SVG. Constrained only by D-01/D-02/D-04 (shared scale, full range, terse in-figure
  disclosure) and the requirement text (log color scale, three panels).
- **File and script naming/placement** — follow the `scripts/plot_phase13.py` +
  `results/phase13_*.png` register; extraction and plotting are separate scripts per D-07.
- **Notebook cell ordering and how many cells** the v2.0 notebook uses, and exact section titles
  within REPORT.md.
- **Whether the extraction script also emits a human-readable markdown table** alongside the
  JSON, or whether the report renders that table from the JSON at write time.
- **The exact source line/section each of D-15's eight limitations is quoted from** — the
  planner reads the reports and confirms; the *policy* (exact quote, visible truncation, ordered
  by claim bound) is the locked part. **← This research answers that item in full; see
  `## D-15: The Eight Limitations — Verbatim Sources`.**

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. (Figure styling, JSON field naming, notebook cell
structure and permutation counts are in-phase Claude's-discretion items, not deferrals.)

Considered and rejected during discussion, recorded so neither is revived as an oversight:
- **A three-way verdict tier** for the correlation (Demonstrated / Suggestive / Not
  demonstrated, with only "Not demonstrated" counting as a miss) — rejected in favour of D-11's
  binary gate, because it would introduce a verdict register this project has not used alongside
  the binary one it has. "Suggestive but not statistically demonstrated" survives as **reporting
  language for a miss**, not as a third passing state.
- **A shared color scale across VIZ-02 and VIZ-03** — rejected in D-03; it would assert an
  adapter-vs-full-fine-tune comparison the phase has not justified.

**Also out of scope (from CONTEXT.md `<domain>`):** any retraining or re-running of a prior
phase's experiment; DEMO-F1 / DEMO-F2; changes to `scripts/demo_app.py` or the v1.0 notebook's
existing cells; re-opening any prior phase's recorded verdict.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description (from REQUIREMENTS.md) | Research Support |
|----|-------------------------------------|------------------|
| **VIZ-02** | Weight-delta heatmap — relative Frobenius change `‖ΔW‖_F/‖W₀‖_F` on the layer×module grid (six named projections), log color scale; committed to repo | `## Checkpoint Tensor Structure` gives the exact 36 key strings, the `scale·B@A` formula, and the **corrected W₀ source** (`convbase_best.pt`, not `best.pt`). `## matplotlib: Log-Scale Heatmaps` gives the verified `LogNorm` recipe. |
| **VIZ-03** | Fisher heatmap juxtaposed with naive-vs-EWC delta heatmaps (three-panel figure — EWC visibly dodging high-Fisher coordinates) | Same key strings for both A/B arms (W₀ = `best.pt`, verified from `scripts/finetune_ab.py:58,208`). Shared-`LogNorm` + one-colorbar-over-two-axes recipe verified. `## Pure-Numpy Rank Statistics` gives the D-10/D-11/D-12 gate machinery, validated against known answers. |
| **DOC-02** | REPORT.md + README v2.0 narrative and updated `demo.ipynb` with honest numbers (recall percentages, retention deltas, tokenizer-inflation tax) in the same register as the v1.0 547-live-ids disclosure | `## D-16: The Three Headline Numbers` gives all three values with their gates and sources. `## D-15: The Eight Limitations — Verbatim Sources` gives every quote with file, section, and line. `## docs/REPORT.md Structure` gives the full heading inventory. |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

Directives the plan must comply with. All are already satisfied by the recommendations below.

| Directive | Source | Impact on this phase |
|-----------|--------|---------------------|
| Python + PyTorch only; **no HF PEFT/transformers model code** | CLAUDE.md Constraints | No new libraries at all — see `## Standard Stack` |
| **Zero budget**, fully offline, no network at runtime | CLAUDE.md Constraints | Every number is read from a local file; no API calls |
| **No wandb / Comet / Neptune**; offline CSV + matplotlib only | CLAUDE.md "What NOT to Use" | matplotlib is already the figure tool (`scripts/plot_phase13.py`) |
| **Python 3.11 venv is MANDATORY** (dev box runs 3.14) | CLAUDE.md Project Structure | Run everything via `.venv/bin/python` / `.venv/bin/pytest` |
| **CPU-only, GPU-free test suite** | CLAUDE.md; `.github/workflows/ci.yml` | Extraction (needs `.pt` files, MPS) is `skipif`-gated; plotting is fully CPU |
| **Explicit `raise SystemExit`, never `-O`-strippable `assert`**, for proof checks in scripts | CONTEXT `<code_context>`; verified in `src/personacore/lora/inject.py:179,201` | The extraction script's guards use `raise SystemExit` / `raise ValueError`, not `assert` |
| `results/` is tracked; `checkpoints/`, `*.pt`, `data/`, `logs/` are gitignored | `.gitignore` (verified) | Figures + JSON land in `results/` and are committed |
| Makefile / CI / CLAUDE.md extras must stay identical (W-06) | `Makefile:9`, `.github/workflows/ci.yml:14-22` | **No extras change needed** — matplotlib already ships via the `demo` extra |
| ruff line-length 100, `select = ["E","F","W","I"]`; `make format` runs isort → ruff format → ruff check --fix | `pyproject.toml` | New scripts/tests must pass `make lint` |
| GSD workflow enforcement — no direct edits outside a GSD command | CLAUDE.md | Planner produces PLAN.md files; no edits during research (none were made) |

---

## Summary

Phase 15 is **pure read-side** and touches no training code. It ships five things: two committed
PNGs, one committed JSON norms artifact, a pre-registered correlation verdict appended to
`results/phase13_ab_report.md`, and the v2.0 narrative across `README.md` / `docs/REPORT.md` /
a new notebook. **Zero new dependencies are required** — `numpy 2.4.6` and `matplotlib 3.10.9`
are both already installed and already in CI via the `demo` extra, and every technique D-12
needs (rank transform, permutation null, bootstrap percentile CI) is ~30 lines of numpy that
this research validated against known answers to 1e-15.

The technical risk in this phase is not the code — it is **fact-fidelity**. Three findings
materially change how the plan must be written:

1. **The adapter's W₀ is `checkpoints/convbase_best.pt`, NOT `checkpoints/best.pt`.** CONTEXT
   D-08 names five checkpoints; the extraction script needs a **sixth**. Verified: the adapter's
   `base_fingerprint` (`git_sha 04e724c…`, `step 4000`, `val_loss 1.5235939979553224`) matches
   `convbase_best.pt` exactly and does not match `best.pt` (`3a46815…`, step 49000). Computing
   VIZ-02's denominator against `best.pt` would silently produce a wrong-by-construction ratio.
2. **The README bullet D-16 names as its "literal density target" contains a known factual
   error.** `README.md:30-31` and `docs/REPORT.md:61-63` both attribute BPE merge exhaustion to
   "the bounded TinyStories corpus". The production tokenizer was actually trained on the
   11,469-byte `tests/fixtures/tiny_corpus.txt` (`scripts/train_tokenizer.py:31`). This is a
   *tracked, open* tech-debt item whose recorded home is **this phase**
   (`.planning/STATE.md` Deferred Items: *"docs/REPORT.md under-discloses tokenizer
   training-corpus identity (11.5KB fixture → 547 live ids) | open — natural home: DOC-02
   honesty pass (Phase 15)"*). It collides head-on with D-15's quote-exactly rule for
   limitation #8. See `## Open Questions` Q1 — this needs a planning decision, not a research call.
3. **Research deliberately did NOT compute the correlation.** D-09 requires the decision rule to
   be committed before ρ exists. Computing it here — even "just to see" — would destroy the
   pre-registration. This imposes a **hard task-ordering constraint on the plan**: the
   pre-registration must be a separate, earlier commit than the extraction run. See
   `## Task-Ordering Constraints`.

Everything else is verified and mechanical. All **five (six) checkpoints are present on disk** —
extraction is not blocked. The test suite baseline is green: **392 passed, 1 skipped, 119.6 s**.

**Primary recommendation:** Two scripts (`scripts/extract_deltas.py` → `results/phase15_norms.json`,
`scripts/plot_phase15.py` → two PNGs), one stats module co-located with the pre-registration,
and one test file (`tests/test_phase15_plots.py`) following `tests/test_phase13_plots.py`
verbatim. Add no dependencies, add no extras, change no CI.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read frozen `.pt` checkpoints, compute ΔW norms | **Extraction script** (`scripts/`) | — | Only tier permitted to import torch (D-07). Never runs in CI. |
| Persist the grid as reviewable numbers | **Committed artifact** (`results/*.json`) | — | The single hand-off boundary. Everything downstream reads this, nothing re-reads a checkpoint. |
| Render the two figures | **Plotting script** (`scripts/`) | — | Structurally forbidden from touching `.pt` (D-07). numpy + matplotlib only. |
| Spearman ρ / permutation p / bootstrap CI | **Stats functions**, module-level pure, committed with the pre-registration | Plotting script may import them | Must be committed *before* the artifact exists (D-09). Pure functions ⇒ known-answer testable with no artifact. |
| Gate verdict text | **`results/phase13_ab_report.md`** appended, dated Phase 15 (D-17) | `docs/REPORT.md` cites it terse (D-04 asymmetry) | Verdict lives adjacent to its data; report cites, never restates. |
| Narrative | **`README.md` (terse) / `docs/REPORT.md` (full) / new v2.0 notebook** | — | D-04/D-16 asymmetry-of-detail. |
| Structural + regression proof | **`tests/`** — CPU-only, GPU-free | `skipif`-gated integration test | D-08's permanent/checkpoint-specific split. |

**Why this matters here:** D-07 exists because the extraction tier and the plotting tier are easy
to collapse into one script "for convenience", and that collapse destroys the regenerability
proof. The tier boundary IS the deliverable.

---

## Standard Stack

### Core — everything already installed, nothing to add

| Library | Version (verified in `.venv`) | Purpose | Why standard here |
|---------|------------------------------|---------|-------------------|
| `numpy` | **2.4.6** [VERIFIED: `.venv/bin/python -c "import numpy"`] | Norms, rank transform, permutation/bootstrap RNG | Already a core dependency (`pyproject.toml: numpy~=2.4`). `np.random.default_rng` is the project's established seeded-RNG idiom (`src/personacore/continual/fisher.py:105`). |
| `matplotlib` | **3.10.9** [VERIFIED] | Both figures | Already the figure tool (`scripts/plot_phase13.py`). Ships via the `demo` **and** `notebook` extras (`pyproject.toml`), so it is present in CI. |
| `torch` | **2.7.1** [VERIFIED: recall report line 37 `{'torch': '2.7.1'}`] | Extraction script ONLY | Reads the frozen checkpoints. Never imported by the plotting module (D-07). |
| `pytest` | **9.0.3** [VERIFIED] | Test suite | `pyproject.toml: pytest~=9.0` |

### Explicitly excluded

| Library | Why excluded | Use instead |
|---------|--------------|-------------|
| `scipy` | D-12 (locked); not a dependency; would be added for one correlation | ~30 lines of numpy — validated below to 1e-15 against scipy's canonical answers |
| `seaborn` | Adds a dependency for `heatmap()`, which is `imshow` + ticks | `ax.imshow(M, norm=LogNorm(...))` |
| `pandas` | Not a dependency; the grid is 36 cells | plain `dict` / `np.ndarray` |

**Installation:** none. Verify with:
```bash
.venv/bin/python -c "import numpy, matplotlib; print(numpy.__version__, matplotlib.__version__)"
# 2.4.6 3.10.9
```

---

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** Every library it uses is
already declared in `pyproject.toml` and already installed in `.venv`. No registry lookup, no
slopcheck run, and no `checkpoint:human-verify` gate is required. Adding any package would
violate CONTEXT `<code_context>` ("No dependency added. scipy stays out (D-12); `numpy` +
`matplotlib` cover everything") and CLAUDE.md's zero-budget/offline posture.

If the planner finds itself reaching for a package, that is a signal the design drifted — not a
signal to run this audit.

---

## Checkpoint Tensor Structure

Everything below was read directly from the real files with `.venv/bin/python` +
`torch.load`. [VERIFIED: direct inspection, 2026-08-02]

### Checkpoint availability — **NOT BLOCKED**

| Path | Present | Size | `git_sha` | `step` | `val_loss` |
|------|---------|------|-----------|--------|-----------|
| `checkpoints/persona_adapter.pt` | ✅ | 1.3 MB | (fingerprint below) | — | — |
| `checkpoints/phase13_naive_latest.pt` | ✅ | 159 MB | `ead34c1c…` | 4000 | 1.1526952981948853 |
| `checkpoints/phase13_ewc_latest.pt` | ✅ | 265 MB | `5e908ac3…` | 4000 | 1.4012203216552734 |
| `checkpoints/fisher_tinystories.pt` | ✅ | 53 MB | (anchor below) | — | — |
| `checkpoints/best.pt` | ✅ | 159 MB | `3a46815d…` | 49000 | 0.7378001868724823 |
| **`checkpoints/convbase_best.pt`** ⚠️ | ✅ | 278 MB | `04e724c6…` | 4000 | 1.5235939979553224 |

⚠️ **The sixth checkpoint is required and is NOT in CONTEXT D-08's list.**
`persona_adapter.pt`'s `base_fingerprint` is
`{'git_sha': '04e724c67033f9a2ed8b705a07ad025c867a18c5', 'step': 4000, 'val_loss': 1.5235939979553224}`,
which matches `convbase_best.pt` **exactly** and does not match `best.pt`. `scripts/teach_persona.py:90`
confirms: `CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"`.
**VIZ-02's `‖W₀‖_F` denominator must come from `convbase_best.pt`.** D-08's docstring requirement
("name the specific checkpoints it depends on") therefore lists **six**, not five.

`best.pt` remains correct as W₀ for the two full-fine-tune arms — `scripts/finetune_ab.py:58,208`
runs each arm `fresh from checkpoints/best.pt`, and both arms landed at step 4000.

### The 36-cell grid: exact key strings

`ModelConfig.n_layer = 6` [VERIFIED: `src/personacore/config.py:89`] and
`TARGET_PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")`
[VERIFIED: `src/personacore/lora/config.py:16`] ⇒ **n = 36**.

Module hierarchy: `GPT.blocks: nn.ModuleList` (`gpt.py:166`) → `Block.attn` / `Block.mlp`
(`gpt.py:136,138`).

```python
# L in range(6)
f"blocks.{L}.attn.q_proj.weight"   # (384, 384)
f"blocks.{L}.attn.k_proj.weight"   # (384, 384)
f"blocks.{L}.attn.v_proj.weight"   # (384, 384)
f"blocks.{L}.attn.c_proj.weight"   # (384, 384)
f"blocks.{L}.mlp.fc_in.weight"     # (1536, 384)
f"blocks.{L}.mlp.fc_out.weight"    # (384, 1536)
```

Adapter keys (injected model, `.base.` infix on the wrapped Linear):
```python
f"blocks.{L}.attn.q_proj.lora_A"   # (r=8, in_features)
f"blocks.{L}.attn.q_proj.lora_B"   # (out_features, r=8)
# 72 tensors total = 36 pairs.  VERIFIED: len(artifact["adapter"]) == 72
```

Fisher keys are **plain model parameter names** (`named_parameters()` — no `.base.` infix,
since Fisher was estimated on an un-injected model): 100 tensors, of which 72 are projection
weight+bias pairs; non-block keys are `['wte.weight','wpe.weight','ln_f.weight','ln_f.bias']`.
[VERIFIED]

### The four quantities per cell

| Block | ΔW | W₀ | Source |
|-------|-----|----|--------|
| `adapter` | `scale * (lora_B @ lora_A)`, `scale = alpha/r = 16.0/8 = 2.0` | `convbase_best.pt["model"][key]` | `src/personacore/lora/layer.py:27,60`; `inject.py:258` (`merged_state_dict`'s own fold) |
| `naive` | `phase13_naive_latest["model"][key] - best["model"][key]` | `best.pt["model"][key]` | `finetune_ab.py:208` |
| `ewc` | `phase13_ewc_latest["model"][key] - best["model"][key]` | `best.pt["model"][key]` | same |
| `fisher` | — (magnitude, not a delta) | — | `fisher_tinystories.pt["fisher"][key]` |

`scale * (lora_B @ lora_A)` has shape `(out_features, in_features)` — identical to
`base.weight` — so the ratio is well defined per cell. Confirmed by `layer.py:51`:
*"Shape sanity: ``(out, r) @ (r, in) == (out, in)``."*

**Recommendation — weights only, no biases.** LoRA wraps only `.weight`; including `.bias` in the
full-fine-tune deltas but not the adapter would break the like-for-like the figure asserts.
Every cell should be the `.weight` tensor alone, and the artifact should say so.

**Recommendation — Fisher per-cell aggregate = `mean`.** The Fisher cache is **mean-normalized**
(`fisher_meta["normalized"]: True`, `normalizer: 1.06861071483269e-06`, and
`src/personacore/continual/fisher.py:14-16` — *"divided by the global mean over ALL trainable
coordinates … so ``mean(F) = 1`` and lambda reads as stiffness relative to an average
parameter"*). A per-cell **mean** is therefore directly interpretable as *"× the importance of an
average parameter"* — a sum would confound importance with tensor size (fc_in/fc_out have 4× the
elements of the attention projections). The artifact should record which aggregate was used.

**Confirmed identity:** the Fisher inside `phase13_ewc_latest.pt` is the same estimate as
`fisher_tinystories.pt` — both carry
`normalizer: 1.06861071483269e-06, n_examples: 2000, seed: 1234, spearman_half: 0.988620235164467`,
and `ewc_lambda: 0.01`. Either source is valid; `fisher_tinystories.pt` is the smaller read
(53 MB vs 265 MB) and goes through the `load_fisher` choke point.

### Load choke points

| Artifact | Function | `weights_only` | Notes |
|----------|----------|----------------|-------|
| `persona_adapter.pt` | `personacore.checkpoint.load_adapter` | **True** | Validates schema + required keys; warns (not errors) on fingerprint mismatch (`checkpoint.py:223-260`) |
| `fisher_tinystories.pt` | `personacore.checkpoint.load_fisher` | **True** | **Raises `ValueError`** on anchor-fingerprint mismatch — pass `expected_fingerprint` read from `best.pt` (`checkpoint.py:295-330`) |
| `best.pt`, `convbase_best.pt`, `phase13_*_latest.pt` | `torch.load(path, map_location="cpu", weights_only=False)` | **False** | Full resume checkpoints carry pickled optimizer/RNG objects. TRUSTED-ONLY — the project's own files. Same register as `finetune_ab.py:208` and `teach_persona.py:545`, both of which carry an explicit SECURITY docstring note. Copy that note. |

`load_checkpoint()` is the wrong tool here — it **restores global RNG state** as a side effect
(`checkpoint.py:138-143`). The extraction script needs weights only. Use a bare `torch.load`
and read `blob["model"]`, exactly as `finetune_ab.py:208` and `teach_persona.py:545` do.

---

## Pure-Numpy Rank Statistics (D-10 / D-11 / D-12)

Every function below was **executed and validated in this session** against known answers.
[VERIFIED: `.venv/bin/python`, 2026-08-02]

### An ordinal Spearman already exists — and it is the WRONG one for D-12

`src/personacore/continual/fisher.py:48-55` has `_spearman(a, b)`, tagged
`_SPEARMAN_METHOD = "ordinal_double_argsort_no_tie_averaging"`. **Do not reuse it blindly.**
Measured difference on a tied fixture:

```
a=[1,1,2,3], b=[1,2,3,4]
average-rank (correct):  0.9486832980505139   (scipy: 0.9486832980505138)
ordinal (fisher.py):     1.0                   <- ties silently collapse
```

At n = 36 over continuous float aggregates, exact ties are near-impossible — but "near" is not
"proven", and the D-05 artifact rounds numbers for readability, which *manufactures* ties. Use
average ranks. If the plan prefers to reuse `fisher.py::_spearman`, it must state the ordinal
choice explicitly and add a no-ties assertion; the lazier and safer path is the ~10-line
average-rank version below.

### The recipe (validated)

```python
import numpy as np

def _rank(x):
    """Average (fractional) ranks — the tie-correct transform Spearman needs.

    Ordinal ranks (a bare double-argsort, as in continual/fisher.py::_spearman) silently
    break ties by input order, which inflates rho whenever two cells share a value. The
    D-05 artifact rounds for readability, so ties are manufacturable — average ranks are
    the only safe choice here.
    """
    x = np.asarray(x, dtype=np.float64)
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=np.float64)
    ranks[order] = np.arange(len(x), dtype=np.float64)
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = (i + j) / 2.0
        i = j + 1
    return ranks


def spearman(a, b):
    """Spearman rho = Pearson on average ranks.

    Spearman over Kendall (D-12): both are rank-based and therefore already robust to the
    heavy-tailed Fisher magnitudes, so there is no edge-case advantage that would justify
    trading away readability.
    """
    return float(np.corrcoef(_rank(a), _rank(b))[0, 1])


def permutation_p(a, b, *, n_perm, seed):
    """Two-sided permutation p on the rank correlation. Rank ONCE, shuffle the ranks.

    Resampling over the closed-form Fisher-z transform (D-12): z's normality assumption is
    the shakiest of the available options at n = 36.
    """
    ra, rb = _rank(a), _rank(b)
    obs = float(np.corrcoef(ra, rb)[0, 1])
    rng = np.random.default_rng(seed)          # LOCAL generator — global RNG untouched.
    ge = sum(
        abs(float(np.corrcoef(rng.permutation(ra), rb)[0, 1])) >= abs(obs)
        for _ in range(n_perm)
    )
    return obs, (ge + 1) / (n_perm + 1)        # add-one: p is never reported as exactly 0.


def bootstrap_ci(a, b, *, n_boot, seed, alpha=0.05):
    """Percentile CI by resampling PAIRS with replacement (re-rank inside each resample)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    n = len(a)
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        aa, bb = a[idx], b[idx]
        # A degenerate resample (all-identical values) makes corrcoef undefined; drop it and
        # REPORT the count rather than letting a nan silently propagate into a quantile.
        out[i] = np.nan if (aa.std() == 0 or bb.std() == 0) else spearman(aa, bb)
    kept = out[np.isfinite(out)]
    return float(np.quantile(kept, alpha / 2)), float(np.quantile(kept, 1 - alpha / 2)), n_boot - len(kept)
```

### Validation evidence

| Check | Result |
|-------|--------|
| Perfect monotone increasing | `0.9999999999999999` (**not** exactly 1.0 — see Pitfall 4) |
| Perfect monotone decreasing | `-0.9999999999999999` |
| Wikipedia canonical IQ/TV example | `-0.17575757575757575` — **exact match** to the documented value |
| Tied fixture vs scipy | `0.9486832980505139` vs scipy `0.9486832980505138` (1 ulp) |
| Reproducibility, same seed, 2 runs | `(rho, p)` tuple equality **True**; `bootstrap_ci` tuple equality **True** |
| Null data (independent) | `rho=-0.2958, p=0.0796, CI=[-0.5562, 0.0261]` → `spans_zero=True` ✅ |
| Signal data (weak positive monotone, n=36) | `rho=0.4468, p=0.0071, CI=[0.1125, 0.7012]` → CI excludes zero ✅ |

### Runtime (measured, n = 36)

| Operation | Count | Wall clock |
|-----------|-------|-----------|
| `permutation_p` | 100,000 shuffles | **1.4 s** |
| `bootstrap_ci` | 10,000 resamples | **0.4 s** |

Both are cheap enough to run inside a unit test. Recommended discretion values:
`n_perm = 100_000`, `n_boot = 10_000`, `seed = 1337` (the project's established seed —
`fisher.py` uses 1234 for its own local generator, `finetune_ab`/`phase14_recall` use 1337).

### ⚠️ The unclosed sub-ambiguity in D-11 the plan MUST close

D-11's gate is **"a positive sign AND a confidence interval excluding zero."** D-12 asks for a
permutation test **and** a bootstrap CI. **These two can disagree** — the permutation p tests
"is rho ≠ 0", the percentile CI asks "does the resampled rho distribution straddle 0", and at
n = 36 they are not guaranteed to agree at any given α.

Read literally, **D-11 makes the CI load-bearing and the permutation p descriptive.** The
pre-registration text must say that explicitly, *before* either number exists — otherwise a
`p = 0.03` with a CI spanning zero (or the reverse) becomes exactly the "resolve it in whichever
direction looks better" hazard D-11's own provenance note was written to prevent. This is the
same class of ambiguity D-11 already closed once; closing it one level deeper costs one sentence.

**Bootstrap method note (for the pre-registration's honesty):** the percentile bootstrap is
known to be biased and anti-conservative at small n. BCa would correct it at real complexity
cost. Recommendation: **keep percentile** (simplest thing that works, matches D-12's "~15 lines")
and **name the method and its known small-n bias in the pre-registration**, rather than
silently upgrading to BCa or silently omitting the caveat.

---

## matplotlib: Log-Scale Heatmaps (D-01 / D-02 / D-18)

All behavior below was **executed and confirmed** on matplotlib 3.10.9.
[VERIFIED: `/tmp/probe15.png` render, 2026-08-02]

### Shared `LogNorm` across two panels, third panel independent

```python
import numpy as np, matplotlib
matplotlib.use("Agg")   # BEFORE pyplot — savefig-only, no GUI backend (plot_phase13.py:27)
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# D-02: vmax = largest cell across BOTH arms; vmin = smallest NONZERO cell across both.
stack = np.concatenate([naive.ravel(), ewc.ravel()])
vmin = stack[stack > 0].min()
vmax = stack.max()
shared = LogNorm(vmin=vmin, vmax=vmax)          # ONE norm object, both panels (D-01)

cmap = plt.get_cmap("magma").copy()
cmap.set_bad(color="0.85")                       # zero/masked cells render grey, not invisible

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), dpi=150)
im_n = axes[0].imshow(naive, cmap=cmap, norm=shared, aspect="auto")
im_e = axes[1].imshow(ewc,   cmap=cmap, norm=shared, aspect="auto")
fig.colorbar(im_n, ax=[axes[0], axes[1]])        # ONE colorbar spanning both — the shared scale,
                                                 # visible as shared (D-01 caption obligation)
# Fisher: own scale — a UNITS argument, not a convenience one (D-01)
im_f = axes[2].imshow(fisher, cmap="viridis",
                      norm=LogNorm(vmin=fisher.min(), vmax=fisher.max()), aspect="auto")
fig.colorbar(im_f, ax=axes[2])
```

### Verified behaviors

| Behavior | Result | Consequence |
|----------|--------|-------------|
| `LogNorm(...)(0.0)` | returns `masked` — **does not raise** | A zero cell renders as `cmap.get_bad()`, silently, unless you set it. **Always call `cmap.set_bad()`** or a zero cell is indistinguishable from a low-but-valid one. |
| `LogNorm(...)(-1.0)` | returns `masked` | Same. Deltas are norms (≥ 0), so negatives are impossible — but the **`naiveΔ − ewcΔ` reduction used by D-10 IS signed** and must never go through a `LogNorm`. |
| `fig.colorbar(im, ax=[ax0, ax1])` | returns one `Colorbar` spanning both axes | This is the D-01 shared-scale statement rendered visually. |
| Dynamic range in a synthetic 6×6 probe with one 40× outlier | 3.71 decades | Compression under a shared log scale is real and expected; D-02 says report it, don't clip it. |

### The D-02 / D-18 vmax-driver disclosure, mechanically

```python
i, j = np.unravel_index(np.argmax(grid), grid.shape)
# i -> layer index, j -> index into TARGET_PROJECTIONS
driver = f"layer {i}, {TARGET_PROJECTIONS[j]}"
```
Compute this **in the extraction script** and store it in the JSON, so the caption text and the
report text read the same field rather than each re-deriving it. That closes D-04's
"different amounts, never different things" requirement structurally instead of by proofreading.

### Follow the `plot_phase13.py` register exactly

`scripts/plot_phase13.py` is the template. Copy these five properties:
1. `matplotlib.use("Agg")` **before** `import matplotlib.pyplot`, with the `# noqa: E402`
   comments on the following imports (lines 27-30).
2. Module-level `_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent` and
   `RESULTS_DIR = _REPO_ROOT / "results"` (line 32-33).
3. Every plot function takes `out_dir` and **returns the written path** — never `show()`
   (lines 121, 162-165). This is what makes the `tmp_path` smoke test possible.
4. Thin `main()` under `if __name__ == "__main__":` printing each written path (lines 203-209).
5. **Fail loudly on missing/blank data** rather than rendering an empty panel — see
   `_series`' docstring (lines 74-97): *"an empty panel under a titled axis is a figure that
   lies."* For Phase 15 the analog is a missing block or a wrong cell count in the JSON.
   Use `raise SystemExit` / `raise ValueError`, never `assert`.

---

## D-07 Structural Enforcement

The in-repo register for "prove it by construction" is **AST parsing of the module's source**,
established at `tests/test_phase14_scoring.py:29,405-423`:

```python
tree = ast.parse((_REPO_ROOT / "scripts" / "phase14_recall.py").read_text(encoding="utf-8"))
for node in ast.walk(tree):
    ...
```
with the rationale, verbatim from that file: *"AST rather than ``inspect.getsource`` string
matching: a substring check cannot tell a call from a mention in a docstring, and the docstrings
in that module discuss ``persona=`` at length precisely because it is the dangerous argument."*
That rationale applies exactly here — the plotting module's docstring will necessarily *mention*
checkpoints and `torch.load` while explaining why it does not use them.

**Recommended: two complementary checks, both cheap.**

**(a) AST check — no torch import, no `.pt` literal, no `torch.load` call.**
```python
tree = ast.parse((_REPO_ROOT / "scripts" / "plot_phase15.py").read_text(encoding="utf-8"))
imported = {
    alias.name.split(".")[0]
    for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names
} | {
    n.module.split(".")[0]
    for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module
}
assert "torch" not in imported
pt_literals = [
    n.value for n in ast.walk(tree)
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith(".pt")
]
assert pt_literals == []
```

**(b) Subprocess check — importing the module never pulls torch into `sys.modules`.**
Strictly stronger than (a): it catches a transitive import through a helper module that (a)
cannot see. `sys.modules` is unreliable in-process (torch is already loaded by sibling tests),
so it must run in a fresh interpreter:
```python
code = (
    "import importlib.util, sys, pathlib;"
    "spec = importlib.util.spec_from_file_location('p15', 'scripts/plot_phase15.py');"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
    "sys.exit(1 if 'torch' in sys.modules else 0)"
)
r = subprocess.run([sys.executable, "-c", code], cwd=_REPO_ROOT)
assert r.returncode == 0, "plotting module transitively imports torch — D-07 violated"
```

Both belong; (a) is the readable statement of intent and (b) is the one that actually cannot be
fooled. Note the CLAUDE.md rule about `assert` applies to **scripts**, not tests — pytest
requires bare `assert`, and the existing suite uses it throughout.

---

## The `skipif`-on-Gitignored-Artifact Pattern (D-08)

Documented at `tests/test_slim_checkpoint.py:18` — *"test_real_slim_artifact_generates_on_cpu —
skipif-gated on the real (gitignored) ``checkpoints/model_slim.pt``: SKIPS cleanly on CI, runs
locally after export."* The exact idiom:

```python
# tests/test_slim_checkpoint.py:42
REAL_SLIM = pathlib.Path("checkpoints/model_slim.pt")  # gitignored; exported by Task 3.

# tests/test_slim_checkpoint.py:168
@pytest.mark.skipif(not REAL_SLIM.exists(), reason="real slim artifact not present (CI)")
def test_real_slim_artifact_generates_on_cpu():
    ...
```

For D-08's optional integration test, gate on **all six** checkpoints:
```python
_REQUIRED = [
    "persona_adapter.pt", "convbase_best.pt", "best.pt",
    "phase13_naive_latest.pt", "phase13_ewc_latest.pt", "fisher_tinystories.pt",
]
_HAVE_CKPTS = all((_REPO_ROOT / "checkpoints" / n).exists() for n in _REQUIRED)

@pytest.mark.skipif(not _HAVE_CKPTS, reason="gitignored checkpoints not present (CI)")
def test_extraction_reproduces_the_committed_artifact(tmp_path):
    ...
```

**Byte-for-byte comparison caveat.** D-08 wants the re-extracted artifact to match the committed
one byte-for-byte. Two things make that fragile unless the writer is pinned:
1. `json.dump` key order — pass `sort_keys=True` **or** build the dict in a fixed order and
   never pass `sort_keys`; pick one and pin it in the writer.
2. Float repr — Python's `repr(float)` is the shortest round-tripping form and is stable across
   CPython versions, so `json.dump` output is deterministic **provided the floats themselves
   are**. On MPS they may not be (Phase 13 measured ~1e-8 cross-process eval variance,
   `phase13_ab_report.md:243`). **Extraction is pure tensor arithmetic on frozen weights with no
   reductions over batches, so it should be deterministic — but force it onto CPU
   (`map_location="cpu"`, which the checkpoint API already defaults to) rather than relying on
   MPS reproducibility.** Recommend the test compare parsed-JSON values with `==` on the
   `git_sha`/structure and exact float equality on the numbers, and fall back to a documented
   tolerance only if a real mismatch is observed. Do not pre-emptively add a tolerance — that
   would weaken the check before it has failed once.

The `tmp_path` smoke-test shape is `tests/test_phase13_plots.py:59-68`, which asserts the
returned path, `.exists()`, and `.stat().st_size > 0`.

### Loading a `scripts/` module from a test

`tests/test_phase13_plots.py:23-32` is the register (and `pyproject.toml` sets
`pythonpath = ["."]`, so `scripts.` is importable too — but the existing suite uses `importlib`):

```python
def _load_plots():
    spec = importlib.util.spec_from_file_location(
        "plot_phase15", _REPO_ROOT / "scripts" / "plot_phase15.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

pp = _load_plots()   # module-level; main() is __main__-guarded so the load renders nothing
```
Justification, verbatim from that file's docstring: *"the plotting rules (which CSV, which
constant, which baseline) belong in the committed script, so the test ``importlib``-loads it
rather than duplicating them in the package."*

---

## The D-05 JSON Artifact

### Format precedent: `results/retention_anchors.json` (actual shape, verbatim)

```json
{
  "retention_ppl_subbin_step0": 2.107553076833866,
  "retention_tokens_subbin": 1000285,
  "retention_ppl_fullval_step0": 2.1065480504616803,
  "retention_tokens_fullval": 12636922,
  "headline_unmasked_fullval": 2.1066,
  "headline_note": "historical unmasked reference only — NOT the curve anchor, Pitfall 1",
  "subbin_token_count": 1000286,
  "subbin_seed": 1337,
  "anchor_val_loss": 0.7378001868724823,
  "git_sha": "483938a9034c5aa3eb25602e5981510a489f0fd8",
  "built": "2026-08-01"
}
```

**What the precedent actually contributes:** a *flat*, human-readable object of primitives, with
three conventions worth carrying forward verbatim —
`git_sha` (provenance, `provenance.git_sha()`), `built` (ISO date), and an inline `*_note` string
field that warns against a specific misreading **inside the data**. That last one is precisely
what D-06's top-level machine-readable comparison-basis note is.

D-06 requires per-block fields, so Phase 15's artifact must nest one level deeper than this
precedent. Keep the three provenance conventions at the top level.

### Required content (D-06), spelling is discretion

```
top level:
  git_sha, built                              <- retention_anchors.json convention
  comparison_basis: { naive_vs_ewc: true, adapter_vs_full_finetune: false, note: "..." }
  projections: [q_proj, k_proj, v_proj, c_proj, fc_in, fc_out]   <- fixes column order
  n_layer: 6
  aggregate: "mean"                           <- how Fisher cells were reduced
blocks: adapter | naive | ewc | fisher        <- ALL FOUR carry regime/param_count/training_budget
  regime:          e.g. "lora_adapter_teaching_run" | "full_finetune" | "fisher_diagonal"
  param_count:     331776 (adapter) | 13891584 (full) | ...
  training_budget: steps + a pointer to the run that produced it
  w0_source:       "checkpoints/convbase_best.pt" | "checkpoints/best.pt" | null
  source_ckpt:     path + its git_sha/step/val_loss fingerprint
  cells:           36 entries, (layer, projection) -> value
  vmax_driver:     {layer, projection, value}  <- D-02 / D-18 disclosure, computed once
```

Expected file size: ~300-400 lines pretty-printed. That is fine — D-05 explicitly chose JSON so
*"a reviewer can check a number without loading numpy."*

---

## `docs/REPORT.md` Structure (D-13 / D-14 / D-15)

**Full heading inventory, 456 lines total.** [VERIFIED: `grep -n '^#\{1,4\} '`]

| Line | Heading |
|------|---------|
| 1 | `# PersonaCore — Milestone 1 Technical Report` |
| 8 | `## The Thesis, and What This Milestone Claims` |
| 29 | `## What Was Built` |
| 48 | `## Decision: Byte-Level BPE from Scratch, Vocabulary Locked Before Model Sizing` |
| 78 | `## Decision: A Bigram Baseline Proved the Harness Before the Transformer Existed` |
| 99 | `## Decision: Pre-Norm Decoder Blocks, Mask Before Softmax` |
| 118 | `## Decision: Manual Attention by Hand, with an sdpa Equivalence Path` |
| 134 | `## Decision: Weight Tying as a True Shared Tensor` |
| 153 | `## Decision: GPT-2-Style Init, Residual Scaling on Both Output Projections` |
| 170 | `## Decision: The Milestone 2 Seams Are Milestone 1 Acceptance Criteria` |
| 197 | `## Decision: fp32 On-Device Training on Apple Silicon as the Primary Run` |
| 218 | `## Decision: A Hand-Rolled Training Loop with Offline CSV Logging` |
| 239 | `## Decision: Perplexity with an Auditable Denominator` |
| 258 | `## Decision: An Architecture Ablation Cohort, Honestly Bounded` |
| 303 | `## Decision: One Shared generate() for Tests, Notebook, and Demo` |
| 322 | `## Decision: A Slim Shippable Artifact That Never Executes Code on Load` |
| 343 | `## Decision: An Offline Story-Completion Demo, Not a Fake Chatbot` |
| 369 | `## Results` |
| 407 | `## Reproducibility` |
| **422** | **`## Limitations and the Milestone 2 Roadmap`** ← the section D-15 grows |
| 448 | `## Where to Go Next` |

**Correction to CONTEXT.md:** D-14 says *"same form as the existing 15"* — the actual count is
**14** `## Decision:` sections [VERIFIED: `grep -c '^## Decision:' docs/REPORT.md` → `14`]. Not a
decision to re-litigate; just the correct number for any plan text that cites it.

### Where the Milestone 2 boundary marker (D-13) can go without disturbing v1.0 text

The lowest-risk insertion point is **immediately after line 447** (end of
`## Limitations and the Milestone 2 Roadmap`, before `## Where to Go Next` at 448) — or, better
for a front-to-back reader, **after `## Where to Go Next` ends at line 456 (EOF)**. Two facts
constrain the choice:

- `## Limitations and the Milestone 2 Roadmap` (422-447) contains a **"Milestone 2 (upcoming)"**
  subsection whose bullets describe Phase 9/10/13/14 in the future tense, including
  *"**No-forgetting A/B:** the same continual-learning run with and without EWC, with forgetting
  curves and weight-delta visualizations."* That is now delivered. Leaving it in the future
  tense inside an otherwise-current report is a real reader hazard — but D-13 says v1.0 sections
  stay **textually untouched**. Resolution: the boundary marker must appear *before* a reader
  reaches any stale future-tense text, or the v2.0 section must explicitly point back and say
  "the roadmap above is preserved as written on 2026-06-10; here is what actually shipped."
  See Open Question Q2.
- `## Where to Go Next` (448-456) is a navigation section listing README / demo.ipynb / results/.
  It will read as wrong once a second notebook exists. Same tension.

### D-15's target section, verbatim (lines 422-447)

The existing `## Limitations and the Milestone 2 Roadmap` opens:

> **What this model is not.** It speaks TinyStories — simple childlike English in a 256-token
> context — because that is the corpus that maximizes coherence-per-parameter at 13.9M. It has
> no dialogue tuning: the demo is story completion, not conversation. And, most importantly,
> **it has no personalization yet**: the PersonaCore thesis — memory living in the weights — is
> not demonstrated by Milestone 1.

That last clause is now false for the repo as a whole and true for Milestone 1 as scoped. The
v2.0 Limitations section is a **new sibling section**, not an edit of this one.

---

## D-15: The Eight Limitations — Verbatim Sources

Every quote below was read directly from the file at the stated line. **Quote these strings
byte-for-byte** (D-15: exact wording, visible truncation only, never paraphrase). Markdown
emphasis markers are part of the source text and are reproduced here as-is.

### L1 — λ* = None (the "no free-lunch λ" verdict)

- **File:** `results/finetune_smoke_report.md`
- **Section:** `## Stage 3 — λ Sweep (EWC-03)` (line 142)
- **Line:** 159

> **EWC not demonstrable at this budget** (no λ satisfies both the within-margin rule and the retention demonstrability guard) — surfaced, never massaged (pre-registered §8 all-fail outcome: λ\* = None, demonstrable = False).

Supporting line 158: `Within-margin candidates: []; margin-largest λ = None; boundary extensions: 0.`

**Note on "§8":** there is **no `## 8` heading** in that report. `§8` refers to the
pre-registered rule numbering inside `scripts/finetune_smoke.py`, used consistently as a label
throughout (`finetune_smoke_report.md:140,159,174,182,200`). Cite the *section heading*
(`## Stage 3 — λ Sweep (EWC-03)`), not a section number, when linking.

**In-repo precedent for quoting this exact string:** `results/phase13_ab_report.md:263-267`
already blockquotes it verbatim under `## Reconciliation: §8 Search vs Phase-13 Demonstration`,
prefaced *"Phase 12 §8 concluded, verbatim and unamended:"*. Match that register.

### L2 — The base cannot extract a fact from its own context (D-20 (a))

- **File:** `results/phase14_recall_report.md`
- **Section:** `## Control 1 — Question Fairness (D-11.1)` → `### (a) What this control can no longer prove` (line 380)
- **Lines:** 398-401

> **Stated plainly, without softening: the inference this control was built to license is
> weakened.** A closed-book failure can no longer be read as unambiguous evidence of absent memory,
> because this base demonstrably fails to surface a fact it can see. Whatever this control returns
> below, that limitation stands.

Threats-section restatement (lines 566-571), `### 3. The question-fairness control's limitation (D-20 (a))`:

> See `## Control 1 — Question Fairness (D-11.1)`, part (a). In-context answerability could not be
> established at this scale, so a closed-book failure **in isolation** is not unambiguous evidence
> of absent memory. The adapter-on / adapter-off differential is unaffected (part (b)), but any
> reading of a single failed question as "the model does not know this" is out of scope.

The threats version is shorter and self-contained — **prefer it** for a Limitations aggregation,
with a link to part (a) for the full passage.

### L3 — The +224.81% PPL collapse without replay

- **File:** `results/phase14_calibration_report.md`
- **Section:** `## Derivation 3 — PersonaChat Replay (D-15)` (line 280)
- **Lines:** 311 (table) and 322 (prose)

Table row, line 311:
`| cal_first_person (no replay) | 4.5737 | 14.8559 | **+224.81%** |`

Prose, line 322:

> **What the paired arm shows replay actually BUYS, and what it costs.** Replay at ratio 1.0 moves the collapse from +224.81% to +29.39% — a large mitigation — while taught recall falls from 0.6825 to 0.4143, a fall of 0.2683. **The replay arm ITSELF still trips the trigger.** Replay at this ratio reduces the collateral collapse but does not eliminate it, so 'replay required' should not be read as 'replay solves it'. Whether the remaining +29.39% is acceptable, and whether a different ratio or a shorter teaching run is the better lever, is a judgment for the checkpoint — this run measured the tradeoff, it did not resolve it.

**Long — this is a visible-truncation candidate (D-15).** Truncate after
*"…should not be read as 'replay solves it'."* with an ellipsis + link.

⚠️ **This number carries a correction block** (`phase14_calibration_report.md:289-307`, `WR-01`).
The recorded figures are the **unmasked** ones; the dead-ids-forbidden re-measurement gives
`+224.5330%`. The report states *"the numbers in the table below are the ones that were actually
measured — the unmasked ones — and they stay as recorded."* **Quote +224.81% and mention the
correction block exists.** Silently quoting the number without the WR-01 context would be exactly
the softening D-15 forbids.

### L4 — The 1/1944 question-fairness control

- **File:** `results/phase14_recall_report.md`
- **Section:** `## Control 1 — Question Fairness (D-11.1)` (line 364)
- **Line:** 378

> **Measured.** With each fact's own first-person statement in the `<|system|>` persona span, the base (adapter off) scored **1/1944 = 0.0005** across 216 questions; 1 of those questions produced at least one completion containing the value. This is the ONLY place in the entire phase where a fact value legitimately appears in a prompt.

The user's own recorded verdict qualification (line 587) is a second, sharper source:
*"the in-context extraction arm succeeded in 1/1944 attempts. At the F5 pilot scale (0/3) this was
already anticipated in D-20's reconciliation as a likely negative; at full scale it is closer to
total failure than to a modest disadvantage."*

**L2 and L4 are two halves of one finding.** L4 is the number; L2 is what it costs the claim.
D-15 lists them as separate entries — keep them separate but adjacent in the claim-bound ordering.

### L5 — The soft tier is excluded from the gate

- **File:** `results/phase14_recall_report.md`
- **Section:** `## Soft Tier — Excluded From The Gate (D-05)` (line 327)
- **Lines:** 334-336

> **What it explicitly does NOT do.** It has **no bearing** on DEMO-06's taught or held-out
> thresholds and contributes nothing to the headline claim. Neither its rate nor its questions
> enter any gate computation in this report.

Threats-section restatement (lines 562-564), `### 2. The soft tier is excluded from the gate (D-05)`:

> See `## Soft Tier — Excluded From The Gate (D-05)`. Two of the taught facts contribute nothing to
> either threshold, so the headline number describes the proper-noun core only — a narrower set
> than "everything the adapter was taught."

The threats version is the better Limitations quote (it states the consequence, not just the
rule). Measured-for-the-record figure, line 349: `**201/486 = 0.4136** across 54 questions`.

### L6 — The reversal-curse scope narrowing (D-22)

- **File:** `results/phase14_recall_report.md`
- **Section:** `## Threats To Validity` → `### 1. The held-out set is deliberately scoped (D-22)` (line 546)
- **Lines:** 555-558

> **Consequence for what a clean held-out result may claim:** it demonstrates generalization
> **within that scope** — across held-out template families in the taught direction — and **not**
> immunity to every documented fine-tuning limitation. This report makes no claim about reversed
> recall, because this phase did not measure it as a held-out property.

Setup context, lines 548-553 (quote if the entry needs the mechanism):

> Reversed-direction phrasings (`who is <value>?`) are **TAUGHT, not held out** — by decision, not
> by accident. They hit the documented **reversal curse** (`arxiv.org/abs/2309.12288`: fine-tuning
> on "A is B" does not yield "B is A", and the effect persists across fine-tuning methods).

### L7 — The noise floor was not re-verified at the production budget (Phase 13 D-05)

- **File:** `results/phase13_ab_report.md`
- **Section:** `## Threats to Validity` → `### 2. The noise floor's measurement regime — and where it does not reach` (line 195)
- **Lines:** 209-214

> **Named limitation (D-05 obligation 2):** that floor was **NOT re-verified at the 4000-step
> production budget**, and **NOT re-verified inside collapse dynamics** — it was measured in a
> stable regime, on the masked arm, at a shorter budget, while both Phase-13 arms are unmasked and
> one of them drifts by +6.42 PPL. **Seed-to-seed variance could plausibly scale with drift
> magnitude**, and a floor measured in a stable regime would not capture that. Nothing here rules
> that out.

Closing sentence worth including (line 222-223): *"That is corroboration from a free check, not a
re-measurement — the honest re-measurement (a 1337/2024 seed pair at 4000 unmasked steps,
~75 min) was not run."*

### L8 — 547 live ids / 7645 dead embedding rows (carried forward from v1.0)

- **File:** `docs/REPORT.md`
- **Section:** `## Decision: Byte-Level BPE from Scratch, Vocabulary Locked Before Model Sizing` (line 48)
- **Lines:** 61-67

> **What actually trained.** Training learned 283 of the 7,928 requested merges before the
> bounded TinyStories corpus exhausted its mergeable pairs — the trainer itself warns
> "corpus exhausted: learned 283 of 7928 requested merges; vocab_size=8192 has 7645 dead ids".
> The *effective* vocabulary is therefore 547 live ids (256 bytes + 283 learned merges + 8
> specials); the locked 8192-row table is reserved capacity. The trade-off is stated plainly:
> shape stability for every downstream checkpoint, in exchange for 7645 dead rows the model
> carries in its embedding table.

Second passage, `## Results`, lines 373-375 (the parameter-count consequence):

> Of the headline count, 2,935,680 parameters (7645 dead rows × 384 dims, ~21%) are embedding
> rows for ids that can never occur in the training data or be decoded — counted in the headline
> because they are part of the shipped tensor.

🔴 **BLOCKING FACT-FIDELITY ISSUE — see Open Question Q1.** The phrase *"the bounded TinyStories
corpus"* is **factually wrong**. `scripts/train_tokenizer.py:31` sets
`CORPUS_PATH = _REPO_ROOT / "tests" / "fixtures" / "tiny_corpus.txt"` (11,469 bytes, verified),
and `artifacts/tokenizer.json` (5,648 bytes, dated 2026-06-04) is the frozen production artifact
built from it. This is a **tracked, open** tech-debt item routed to this phase:

- `.planning/STATE.md` Deferred Items: *"docs/REPORT.md under-discloses tokenizer training-corpus
  identity (11.5KB fixture → 547 live ids) | open — **natural home: DOC-02 honesty pass
  (Phase 15)**"*
- `.planning/milestones/v1.0-MILESTONE-AUDIT.md:18` (WR-04/WARNING-3): *"production
  artifacts/tokenizer.json was trained on the 11.5KB tests/fixtures/tiny_corpus.txt (283 merges,
  547 live ids of 8192) — never regenerated from real TinyStories before Phase 5. The
  547-live-id consequence IS honestly quantified in README/REPORT (08-08), but docs/REPORT.md:62-63
  attributes merge exhaustion to 'the bounded TinyStories corpus' — corpus identity
  under-disclosed."*

`README.md:30-31` carries the same misattribution: *"the bounded TinyStories corpus exhausts its
mergeable pairs"*.

### Claim-bound grouping (raw material for D-15's ordering — the ordering itself is the planner's call)

| Which claim it bounds | Limitations |
|-----------------------|-------------|
| **"EWC mitigates forgetting"** (Phase 13 / DEMO-04) | L1 (no λ buys retention for free), L7 (the noise floor the gate is measured against was not re-verified at this budget) |
| **"Memory lives in the weights"** (Phase 14 / DEMO-05/06) | L4 (the fairness control is near-total failure), L2 (so a closed-book failure is not proof of absent memory), L6 (held-out generalization is scoped, not universal), L5 (the headline covers the proper-noun core only) |
| **"…without damaging the base"** (Phase 14 collateral) | L3 (+224.81% without replay; +29.39% with — replay mitigates, does not solve) |
| **"13.9M-parameter from-scratch base"** (v1.0 capacity) | L8 (547 of 8192 ids live; ~21% of the headline parameter count is dead embedding rows) |

### A ninth honest negative exists and is NOT in D-15's eight

`results/phase14_recall_report.md:585` — the user's recorded qualification (1):

> No-collateral-collapse (D-11 control 2): the taught persona measurably raises off-topic dialogue
> cost (**+27.16%**) relative to the pre-adapter conversational base, but does not eliminate the
> collapse signature entirely.

D-15 locks **eight**, and this is not among them. Flagged only so the planner does not discover
it mid-drafting and treat the omission as an oversight. It is arguably the residual half of L3
(L3 is the pre-replay measurement; +27.16% is the post-replay real-run measurement). **Not a
re-litigation — a disclosure.**

---

## D-16: The Three Headline Numbers

### 1. Recall rate against its gate

**Source:** `results/phase14_recall_report.md`, `## Recall Results — Core Tier`, lines 56-60.

| tier | k/N | rate | threshold | gate |
| --- | --- | --- | --- | --- |
| core taught | 496/1008 | **0.4921** | `0.2486` | **PASS** |
| core held-out | 326/936 | **0.3483** | `0.2000` | **PASS** |
| closed-book control (adapter off) | 0/2430 | **0.0000** | — | descriptive |

Verdict (line 575): **ADAPT — GO with two qualifications.** Thresholds were pre-registered from a
**disjoint** calibration fact set (`CALIBRATION_SHA 0425fdc4…`) before the run existed.
**Carries D-15 limitations L2, L4, L5, L6** — at least one short form belongs inline in README
per D-16.

### 2. Retention delta from the A/B

**Source:** `results/phase13_ab_report.md`, `## 2×2 Result` (lines 53-64) and `## Gate Verdict`
(lines 106-123).

| Arm | λ | Acquisition — masked dialogue val PPL | Retention — retention PPL (frozen sub-bin) |
| --- | --- | --- | --- |
| _step-0 reference (`best.pt`)_ | — | _31.903875386436905_ | _2.107553076833866_ |
| naive | 0 | **4.192794562524908** | **8.52417066884246** |
| EWC | 0.01 | **4.573349242745997** | **3.8911400839446597** |

- Retention drift: naive **+6.416618** vs EWC **+1.783587** — a **3.6×** difference.
- `delta = 4.633030584897801`, `MARGIN = 2 × 0.068930 = 0.137860` → gate holds at **33.61×** the
  margin (67.2× the raw noise floor).
- Acquisition cost of EWC: **+0.380556** PPL (~9.1% relative), **descriptive, no gate** (D-06).
- **Carries D-15 limitations L1, L7.** Also scope-limited to teacher-forced retention PPL —
  `phase13_ab_report.md:133-135`: *"It is not a claim about free-running story generation."*
  (measured negative: 79 naive / 69 EWC mid-story role-token leakages).

### 3. Phase 11 tokenizer-inflation tax

**Source:** `results/inflation_report.md`, `## D-08 Metrics` (metric 1, line 15) and `## Baseline`
(lines 30-31). The report itself says (line 54): *"Phase 15 reads its honest 'tokenizer-tax'
number off metric 1 of this report."*

- Dialogue tokens/word: **3.229** (over 4,800,385 utterance tokens / 1,486,754 whitespace words)
- TinyStories baseline, same run/tokenizer/word-rule: **2.860**
- **Relative inflation ratio: 1.129×**
- Verdict: **GO** (band: ratio ≤ 1.2× AND fit ≥ 90%; measured fit 0.9996)
- Inline qualifier the number needs: it is *"only meaningful against the TinyStories baseline
  recomputed in this same run"* (report preamble, lines 8-9) — never comparable to another
  tokenizer.

### The literal density target — `README.md:29-33`, verbatim

```
- **Byte-level BPE tokenizer** trained from scratch — vocab table 8192 with 547 ids live
  (256 bytes + 283 learned merges + 8 specials; the bounded TinyStories corpus exhausts its
  mergeable pairs, so the remaining 7645 rows are reserved capacity), `<|endoftext|>`
  pinned as an atomic id, validated against a tiktoken oracle (test-only; a guard test
  proves the oracle is never imported by runtime code)
```

**The pattern to replicate:** a bold claim (`547 ids live`), then **immediately, inside the same
bullet, in parentheses**, the full arithmetic *and* the thing that makes it honest (`the remaining
7645 rows are reserved capacity` — i.e. 93% of the table is dead). The caveat is not a footnote,
not a link, and not a following sentence. It is inside the same breath as the claim.

Applied to the three v2.0 numbers, that means e.g. *"held-out recall 0.3483 against a
pre-registered 0.2000 gate (proper-noun core only; the soft preference tier is excluded, and the
held-out set deliberately omits reversed phrasings)"* — one bullet, no pointer.

⚠️ **The exemplar bullet is itself factually wrong** (`the bounded TinyStories corpus` — see L8
above). The *density* is the target; the *content* needs the Q1 decision.

### The rest of README is entirely M1-framed and must change

`README.md:4-7` still says *"This repository is **Milestone 1** … the weight-memory mechanism
itself (from-scratch LoRA + EWC) is **Milestone 2, upcoming**"*. Lines 97-113
(`## Roadmap — Milestone 2 (upcoming)`) describe LoRA / EWC / teach-then-recall in the future
tense and close with *"Until then, the demo above is exactly what it claims to be … no chat
tuning, no personalization yet."* DOC-02 is a **substantial README rewrite**, not a bullet
addition. The planner should budget for it accordingly.

---

## Architecture Patterns

### System architecture — the data flow

```
  checkpoints/ (gitignored, 6 files, ~914 MB)
  best.pt ── convbase_best.pt ── persona_adapter.pt
  phase13_naive_latest.pt ── phase13_ewc_latest.pt ── fisher_tinystories.pt
        │
        │  ONE manual local run (never CI, never a test)
        ▼
  ┌───────────────────────────────┐
  │ scripts/extract_deltas.py     │  imports torch. Reads .pt. Computes
  │                               │  ‖ΔW‖_F/‖W₀‖_F per (layer, projection)
  │                               │  for adapter/naive/ewc + Fisher aggregate.
  │                               │  Computes vmax_driver once.
  └───────────────┬───────────────┘
                  │ writes
                  ▼
  ┌───────────────────────────────┐
  │ results/phase15_norms.json    │  ◄── COMMITTED. The hand-off boundary.
  │ 4 blocks × 36 cells + D-06    │      Everything below reads ONLY this.
  │ regime/confound fields        │
  └───────┬───────────────┬───────┘
          │               │
          │               └────────────────────────┐
          ▼                                        ▼
  ┌───────────────────────┐            ┌────────────────────────────┐
  │ scripts/plot_phase15  │            │ stats: spearman /          │
  │ NO torch (D-07,       │            │ permutation_p /            │
  │ AST + subprocess      │            │ bootstrap_ci  (pure numpy) │
  │ enforced)             │            │ ⚠ COMMITTED BEFORE the     │
  └───────┬───────────────┘            │   artifact exists (D-09)   │
          │ savefig                    └──────────┬─────────────────┘
          ▼                                       │ verdict
  results/phase15_adapter_delta.png  (VIZ-02)     ▼
  results/phase15_fisher_ewc.png     (VIZ-03)  results/phase13_ab_report.md
                                                (dated, marked Phase 15 — D-17)
          │                                       │
          └───────────────┬───────────────────────┘
                          ▼
        README.md (terse)  ·  docs/REPORT.md (full)  ·  v2.0 notebook
                          D-04 / D-16 asymmetry of detail
```

### Recommended file layout

```
scripts/
├── extract_deltas.py     # NEW — the only new code that opens a .pt (D-07)
├── plot_phase15.py       # NEW — numpy + matplotlib only; plot_phase13.py register
└── phase15_stats.py      # NEW — spearman/permutation_p/bootstrap_ci + the
                          #       pre-registered rule constants. COMMITTED FIRST (D-09).
results/
├── phase15_norms.json    # NEW — the D-05 artifact
├── phase15_*.png         # NEW — VIZ-02, VIZ-03
└── phase13_ab_report.md  # APPENDED — dated Phase 15 section (D-17)
tests/
└── test_phase15_plots.py # NEW — plot-from-artifact + D-07 guard + stats known-answers
docs/REPORT.md            # EXTENDED (v1.0 text untouched)
README.md                 # REWRITTEN for v2.0
demo_v2.ipynb             # NEW, self-contained (D-13)
```

Naming follows the established register: `scripts/plot_phase13.py` → `results/phase13_*.png`;
`scripts/finetune_ab.py` (driver) carries its own pre-registered constants as module-level
literals, and `tests/test_phase13_driver.py` `importlib`-loads it. Do the same here.

### Task-Ordering Constraints (D-09 pre-registration)

The pre-registration discipline is **git-history-order-as-proof** — `finetune_ab.py` was
committed at `c3d942e` *before either arm ran*, and `phase14_recall.py`'s constants were
literals *"before this run produced a single number"*
(`phase14_recall_report.md:16`). Phase 15 must reproduce that ordering:

```
1. COMMIT scripts/phase15_stats.py  — the functions, the seed, n_perm, n_boot,
   the predicted sign (+), and the D-11 gate rule (positive sign AND CI excluding zero,
   with the CI named as the load-bearing half).
   Plus tests/ known-answer tests for the stats functions.
   → At this commit, NO correlation exists anywhere.
   ─────────────── HARD BOUNDARY ───────────────
2. THEN run scripts/extract_deltas.py → results/phase15_norms.json
3. THEN compute the correlation and append the dated verdict to phase13_ab_report.md
```

Collapsing 1 and 2 into one commit destroys the proof. **This research deliberately did not
compute the correlation** — the Fisher grid and both delta grids are the correlation's two
inputs, and looking at them before authoring the rule is the exact contamination D-09 forbids.
Consequently, this research reports **no expectation whatsoever** about whether the gate will
pass. Treat SC2's *"showing EWC visibly dodging high-Fisher coordinates"* as genuinely open
(CONTEXT explicitly narrows it via D-11).

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Spearman ρ | A custom rank correlation with ad-hoc tie handling | The validated `_rank` + `np.corrcoef` recipe above | Validated to 1e-15 against scipy's canonical answers in this session; the ordinal variant already in `fisher.py` is measurably wrong on ties |
| Log color mapping | Manual `np.log10` on the data then a linear norm | `matplotlib.colors.LogNorm` | LogNorm masks non-positives instead of producing `-inf`/`nan`, keeps the colorbar tick labels in data units, and is what a reader expects to see on the axis |
| Reading the adapter / Fisher | Bare `torch.load` on those two | `personacore.checkpoint.load_adapter` / `load_fisher` | The locked `weights_only=True` choke points; `load_fisher` additionally **raises** on an anchor-fingerprint mismatch, catching a wrong-Fisher extraction before it produces a plausible-looking wrong figure |
| The `scale·B@A` fold | Re-deriving `alpha/r` at the call site | Read `lora_config["alpha"] / lora_config["r"]` from the artifact | `layer.py:27` names `self.scale` the *"SINGLE source of truth"* and PITFALLS P3 explicitly bans recomputing it. The artifact carries `{'r': 8, 'alpha': 16.0}`. |
| Loading a full checkpoint | `personacore.checkpoint.load_checkpoint` | bare `torch.load(..., map_location="cpu", weights_only=False)` + `blob["model"]` | `load_checkpoint` **restores global RNG state** as a side effect (`checkpoint.py:138-143`) — an unwanted mutation in a read-only script |
| Verifying the D-15 quotes | Proofreading | A test that asserts each quote is a byte-exact substring of its cited source file | See `## Validation Architecture` — this converts D-15's policy from convention into structure, which is exactly this project's register |

**Key insight:** every "don't hand-roll" here is a *choke point this repo already built and already
tested*. The from-scratch ethos applies to the ML core, not to re-deriving constants the codebase
declares single-source-of-truth.

---

## Common Pitfalls

### Pitfall 1: Using `best.pt` as W₀ for the adapter

**What goes wrong:** VIZ-02's ratio is computed against the wrong denominator — a
49,000-step TinyStories base instead of the 4,000-step conversational base the adapter actually
wraps. The figure still renders and the numbers still look plausible.
**Why it happens:** CONTEXT D-08 lists five checkpoints and `best.pt` is described as
"W₀ for both full-fine-tune deltas" — easy to over-generalize to three deltas.
**How to avoid:** assert the adapter's `base_fingerprint` equals the W₀ checkpoint's
`{git_sha, step, val_loss}` trio before computing anything. `load_adapter(path,
expected_fingerprint=...)` only *warns* (D-02, `checkpoint.py:252-259`) — so the extraction script
must **`raise SystemExit` on mismatch itself**, per the project's fail-loud rule.
**Warning sign:** the adapter block's ratios come out suspiciously large or the ratio ordering
across layers looks nothing like the naive/ewc blocks.

### Pitfall 2: Computing the correlation before committing the rule

**What goes wrong:** the pre-registration becomes unverifiable, and D-09's entire justification
(*"never a number chosen after seeing whether it supports the roadmap's claim"*) collapses.
**Why it happens:** it is one line of numpy and the data is right there.
**How to avoid:** the hard commit boundary in `## Task-Ordering Constraints`. Git history IS the
proof, exactly as `finetune_ab.py @ c3d942e` and `phase14_recall.py` were.
**Warning sign:** a plan where extraction and the pre-registration land in the same wave.

### Pitfall 3: The plotting script "temporarily" reading a checkpoint

**What goes wrong:** D-07's regenerability-by-construction proof is void; the committed PNG can
no longer be shown to derive from the committed numbers.
**Why it happens:** one missing field in the JSON, and reaching for the `.pt` is a two-line fix.
**How to avoid:** the AST + subprocess guards, written **before** the plotting script, so the
first missing field forces a JSON schema fix rather than a torch import.
**Warning sign:** `import torch` appearing anywhere under `scripts/plot_phase15.py`'s import
block, or a `.pt` string literal in it.

### Pitfall 4: `spearman(perfect_monotone) != 1.0`

**What goes wrong:** a known-answer test written as `assert spearman(a, b) == 1.0` fails.
**Measured:** the recipe returns `0.9999999999999999` on perfectly monotone input — float
accumulation inside `np.corrcoef`, not a bug.
**How to avoid:** `pytest.approx(1.0)` or `abs(rho - 1.0) < 1e-12` in tests; report the raw float
in the artifact.

### Pitfall 5: A zero or negative cell under `LogNorm`

**What goes wrong:** the cell renders as the colormap's "bad" color, which defaults to fully
transparent — it looks like a hole, or like white space, with no indication that data is
missing.
**Measured:** `LogNorm(vmin=…, vmax=…)(0.0)` returns `masked`; it does **not** raise.
**How to avoid:** `cmap = plt.get_cmap(...).copy(); cmap.set_bad(color="0.85")`, and have the
extraction script **count** non-positive cells into the JSON so the report can state
"0 non-positive cells" rather than the figure silently implying it. `lora_B` is zero-initialized
but is nonzero after training, and the full-FT deltas are Frobenius norms — a zero cell would
itself be a finding worth naming.

### Pitfall 6: Signed `naiveΔ − ewcΔ` fed to a log scale

**What goes wrong:** the D-10 pairing quantity is a **difference of ratios** and can legitimately
be negative (a cell where EWC moved *more* than naive). Passing it through `LogNorm` masks
every such cell.
**How to avoid:** the reduction quantity is a **statistic input, not a plotted panel**. The three
plotted panels are naiveΔ, ewcΔ (shared LogNorm) and Fisher (own LogNorm). Never plot the
reduction on a log axis; if it is visualized at all, use a diverging linear norm.

### Pitfall 7: Mixing `.weight` and `.bias` across blocks

**What goes wrong:** the adapter block covers weights only (LoRA never wraps biases), while a
naive `for k in fisher` loop would pick up 36 extra `.bias` entries. The grids then describe
different parameter sets and the correlation is computed on mismatched cells.
**How to avoid:** build the 36 keys from an explicit `(layer, projection)` product, exactly as
`inject_lora` iterates `cfg.targets` rather than `isinstance`-scanning
(`inject.py:38` — *"explicit allowlist — NEVER an isinstance scan (P1)"*). Same discipline.

### Pitfall 8: Quoting `+224.81%` without its WR-01 correction block

**What goes wrong:** the Limitations entry cites a number the source report itself annotates as
measured under a superseded call-site policy (`phase14_calibration_report.md:289-307`). Omitting
that is a softening — the exact drift D-15 exists to close.
**How to avoid:** quote the number and the correction's existence together, or quote the
correction block's own table row (`+224.5330%` under the frozen policy) alongside it.

### Pitfall 9: Assuming `## Decision:` sections number 15

CONTEXT D-14 says 15; the file has **14**. A plan task saying "add the 16th Decision section"
would be off by one from the start.

---

## Runtime State Inventory

Phase 15 writes no runtime state and registers nothing with the OS. The relevant question is the
inverse: **what does this phase READ that is not in git?**

| Category | Items found | Action required |
|----------|-------------|------------------|
| Stored data | **Six gitignored checkpoints** (`best.pt`, `convbase_best.pt`, `persona_adapter.pt`, `phase13_naive_latest.pt`, `phase13_ewc_latest.pt`, `fisher_tinystories.pt`), ~914 MB total. All **present and verified readable** on this machine, 2026-08-02. | None — but the extraction script's docstring must name all six (D-08), and the D-08 integration test must `skipif` on all six. |
| Live service config | **None** — verified: this phase runs no service, opens no port, makes no network call. | None |
| OS-registered state | **None** — verified: no launchd/cron/scheduler entry is created or read. | None |
| Secrets / env vars | **None** — verified: no `.env` read, no Kaggle token, no API key. `matplotlib.use("Agg")` removes even the `DISPLAY` dependency. | None |
| Build artifacts | `.venv/` editable install of `personacore` (present, working — 392 tests pass). **`__pycache__` under `scripts/`** exists and is gitignored. | None — but see `MEMORY.md`: a worktree agent can break the editable install; symptom is mass `ModuleNotFoundError`, fix is repointing the install, not a code change. |
| Committed-but-regenerable | `results/phase13_forgetting_curve.png`, `results/phase13_frontier.png` are committed PNGs regenerated by `scripts/plot_phase13.py`. Phase 15's two PNGs join them. | None — but a future `plot_phase15.py` edit must re-run and re-commit, same as `260801-r9y` did for Phase 13 (both PNGs SHA-256-identical after that change). |

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything | ✅ | 3.11.15 (`.venv`) | none — mandatory (CLAUDE.md) |
| `numpy` | extraction, stats, plotting | ✅ | 2.4.6 | none needed |
| `matplotlib` | plotting | ✅ | 3.10.9 | none needed |
| `torch` | extraction only | ✅ | 2.7.1 | none needed |
| `pytest` | test suite | ✅ | 9.0.3 | none needed |
| `ruff` | `make lint` | ✅ | via `dev` extra | none needed |
| `checkpoints/*.pt` (×6) | extraction only | ✅ all present | ~914 MB | **none** — extraction cannot run without them; `skipif`-gated in CI by design |
| `results/*.md`, `README.md`, `docs/REPORT.md` | the writeup | ✅ tracked | — | none needed |
| Network | — | not required | — | phase is fully offline |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

**Baseline health:** `.venv/bin/pytest -q` → **392 passed, 1 skipped, 83 warnings in 119.64s**
(the 1 skip is `test_real_slim_artifact_generates_on_cpu` — `checkpoints/model_slim.pt` is not
present locally). Any regression in that count is attributable to Phase 15.

---

## Validation Architecture

`workflow.nyquist_validation: true` in `.planning/config.json`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| Quick run command | `.venv/bin/pytest -q tests/test_phase15_plots.py` |
| Full suite command | `.venv/bin/pytest -q` (or `make test`) |
| Baseline | 392 passed, 1 skipped, 119.6 s |
| Environment | CPU-only, GPU-free, Python 3.11 venv; CI installs `.[cpu,dev,demo]` — matplotlib ships via `demo` |

### Phase Requirements → Test Map

| Req / Decision | Behavior | Test type | Automated command | File exists? |
|----------------|----------|-----------|-------------------|-------------|
| VIZ-02 | `plot_adapter_delta(out_dir)` writes a non-empty PNG to an arbitrary dir | unit (tmp_path smoke) | `pytest tests/test_phase15_plots.py::test_plot_functions_write_pngs -x` | ❌ Wave 0 |
| VIZ-03 | `plot_fisher_ewc(out_dir)` writes a non-empty three-panel PNG | unit | same test | ❌ Wave 0 |
| **D-01** | The naive and EWC panels use **one** norm object with identical `(vmin, vmax)`; the Fisher panel's norm differs | unit | `pytest tests/test_phase15_plots.py::test_ab_panels_share_one_norm -x` | ❌ Wave 0 |
| **D-02** | `vmin` == smallest **nonzero** cell across both arms; `vmax` == largest; no clipping applied | unit | `pytest tests/test_phase15_plots.py::test_shared_range_is_full_data_range -x` | ❌ Wave 0 |
| **D-02 / D-18** | `vmax_driver` in the JSON matches `argmax` of the corresponding grid | unit | `pytest tests/test_phase15_plots.py::test_vmax_driver_matches_argmax -x` | ❌ Wave 0 |
| **D-05 / D-06** | The committed JSON has 4 blocks × 36 cells; **every** block (incl. `fisher`) carries `regime`/`param_count`/`training_budget`; top level carries the machine-readable comparison-basis note | unit (schema) | `pytest tests/test_phase15_plots.py::test_artifact_schema -x` | ❌ Wave 0 |
| **D-07** | `scripts/plot_phase15.py` imports no `torch` and contains no `.pt` string literal (AST); importing it in a fresh interpreter never pulls torch into `sys.modules` (subprocess) | structural | `pytest tests/test_phase15_plots.py::test_plotting_module_never_opens_a_checkpoint -x` | ❌ Wave 0 |
| **D-10 / D-12** | `spearman` matches the Wikipedia canonical value `-0.17575757575757575`; ties use average ranks; perfect monotone ≈ ±1 | unit (known-answer) | `pytest tests/test_phase15_stats.py::test_spearman_known_answers -x` | ❌ Wave 0 |
| **D-12** | `permutation_p` and `bootstrap_ci` return **identical** results for the same seed across two calls | unit (determinism) | `pytest tests/test_phase15_stats.py::test_seeded_results_are_reproducible -x` | ❌ Wave 0 |
| **D-12** | On independent data the CI spans zero; on strong monotone data it excludes zero | unit (behavioral) | `pytest tests/test_phase15_stats.py::test_ci_behavior_on_null_and_signal -x` | ❌ Wave 0 |
| **D-11** | The gate function returns MISS for `(rho=+0.15, ci=(-0.1, 0.4))` and PASS only for positive sign **and** CI excluding zero | unit (gate logic) | `pytest tests/test_phase15_stats.py::test_gate_rule -x` | ❌ Wave 0 |
| **D-15** | Each of the eight Limitations quotes is a **byte-exact substring** of its cited source file (splitting on `…` for the visible-truncation case, each fragment matched in order) | doc integrity | `pytest tests/test_phase15_docs.py::test_limitations_quotes_are_verbatim -x` | ❌ Wave 0 |
| **D-16** | Each of the three README headline numbers appears in README **and** matches the value in its cited source report | doc integrity | `pytest tests/test_phase15_docs.py::test_headline_numbers_match_sources -x` | ❌ Wave 0 |
| **D-17** | The appended section in `results/phase13_ab_report.md` carries a Phase 15 marker and a date, and appears **after** every pre-existing Phase 13 heading | doc integrity | `pytest tests/test_phase15_docs.py::test_verdict_section_is_dated_and_separated -x` | ❌ Wave 0 |
| **D-08** | Re-running extraction reproduces the committed JSON exactly | integration, `skipif`-gated on all six checkpoints | `pytest tests/test_phase15_plots.py::test_extraction_reproduces_the_committed_artifact -x` | ❌ Wave 0 |
| DOC-02 | Full suite stays green (no regression from the doc/notebook edits) | regression | `.venv/bin/pytest -q` | ✅ exists |

### What is inherently checkpoint-gated (cannot be permanently tested)

Per D-08, state this explicitly in the test module docstring:

- **Extraction correctness** — needs six gitignored checkpoints (~914 MB). Runs locally, skips
  cleanly in CI. *Re-running extraction against a future checkpoint requires a fresh manual run
  producing a fresh committed artifact* — not a test that silently stays green while checking
  nothing.
- **Whether the committed numbers are the RIGHT numbers** — the permanent suite proves the
  artifact→figure path is faithful and the schema is complete; it cannot prove the artifact
  describes the intended checkpoints. The `git_sha`/`step`/`val_loss` fingerprints recorded in
  each block are the audit trail that closes that gap for a human reader.

### Sampling Rate

- **Per task commit:** `.venv/bin/pytest -q tests/test_phase15_plots.py tests/test_phase15_stats.py tests/test_phase15_docs.py` (< 10 s expected)
- **Per wave merge:** `.venv/bin/pytest -q` (full suite, ~120 s) **and** `make lint`
- **Phase gate:** full suite green (≥ 392 passed, allowing for new tests) + `make lint` clean +
  both PNGs and the JSON committed, before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_phase15_stats.py` — covers D-10 / D-11 / D-12. **Must land in the same commit
      as `scripts/phase15_stats.py`, before any artifact exists** (D-09).
- [ ] `tests/test_phase15_plots.py` — covers VIZ-02 / VIZ-03 / D-01 / D-02 / D-05 / D-06 / D-07 / D-08.
- [ ] `tests/test_phase15_docs.py` — covers D-15 / D-16 / D-17.
- [ ] No framework install needed; no `conftest.py` change needed (the existing
      `simulate_pascal` fixture is irrelevant here).

---

## Security Domain

`security_enforcement` is not set in `.planning/config.json` (treated as enabled).

### Applicable ASVS categories

| ASVS category | Applies | Standard control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface; offline scripts only |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Local filesystem only |
| **V5 Input Validation** | **yes** | The JSON artifact is parsed by the plotting script. Validate structure (4 blocks, 36 cells, expected projection names) and `raise SystemExit` on any deviation — the `plot_phase13.py:74-97` fail-loud register: *"an empty panel under a titled axis is a figure that lies."* |
| V6 Cryptography | no | No crypto; `sha256` appears only as a provenance digest in prior reports |
| **V14 Config / Deserialization** | **yes** | See below — the single real security surface in this phase |

### Deserialization — the one real surface

| Artifact | Loader | `weights_only` | Risk posture |
|----------|--------|----------------|-------------|
| `persona_adapter.pt` | `load_adapter` | **True** | Restricted unpickler; zero code execution on load |
| `fisher_tinystories.pt` | `load_fisher` | **True** | Same, plus a hard fingerprint check |
| `best.pt`, `convbase_best.pt`, `phase13_*_latest.pt` | `torch.load(..., weights_only=False)` | **False** | **TRUSTED-ONLY.** These carry pickled optimizer/RNG/numpy objects and cannot round-trip under `weights_only=True`. The extraction script must carry the project's established SECURITY docstring note verbatim in register — see `scripts/finetune_ab.py:20-21` (*"torch.load(weights_only=False) reads ONLY the project's OWN anchor checkpoint … trusted-only"*) and `scripts/teach_persona.py:32`. |

**Threat patterns for this stack**

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Malicious `.pt` executing code on load | Elevation of Privilege | `weights_only=True` where possible; explicit TRUSTED-ONLY docstring + own-file-only path constants where not. Never accept a checkpoint path from argv/env. |
| Wrong-checkpoint extraction producing a plausible wrong figure | Tampering (integrity) | Fingerprint assertion against the recorded `{git_sha, step, val_loss}` trio; `raise SystemExit` on mismatch (`load_adapter` only *warns*) |
| Plotting script silently reading a checkpoint and breaking the regenerability proof | Repudiation | D-07's AST + subprocess structural guards |
| A committed PNG that no longer matches the committed JSON | Tampering | The `tmp_path` smoke test + a manual re-run before commit; `260801-r9y` set the precedent of verifying both PNGs SHA-256-identical after a plotting-code change |
| `matplotlib` needing a GUI/`DISPLAY` in a headless context | Denial of Service (CI) | `matplotlib.use("Agg")` before `pyplot` import (`plot_phase13.py:27`) |

No network, no user input, no secrets, no untrusted data. The attack surface is one trusted
local filesystem read.

---

## State of the Art

| Old approach | Current approach | When changed | Impact here |
|--------------|------------------|--------------|-------------|
| `torch.load` defaulting to full pickle | `weights_only=True` default since torch 2.6 | torch 2.6 | Already handled — `checkpoint.py:126-128` documents exactly why the resume path passes `weights_only=False` |
| `plt.cm.get_cmap(name)` | `plt.get_cmap(name)` / `matplotlib.colormaps[name]` | matplotlib 3.9 removed the deprecated `plt.cm.get_cmap` | Use `plt.get_cmap("magma").copy()` — verified working on 3.10.9 |
| `np.random.seed` / legacy `RandomState` | `np.random.default_rng(seed)` Generator API | numpy 1.17+, now the documented default | Matches the in-repo idiom (`fisher.py:105` — *"LOCAL generator — global RNG untouched"*) |
| `imshow(..., interpolation=...)` guessing | `imshow(M, aspect="auto")` with explicit ticks | stable | 6×6 grid needs explicit `set_xticks` / `set_yticks` with the projection names |

**Deprecated / not applicable:** `scipy.stats.spearmanr` (dependency excluded by D-12);
`seaborn.heatmap` (dependency); `plt.cm.get_cmap` (removed in matplotlib 3.9).

---

## Code Examples

### Extraction — the ΔW ratio for one block

```python
# Source: derived from src/personacore/lora/layer.py:27,60 and inject.py:250-260
import torch

PROJ_PATHS = {  # (projection name) -> the attribute path inside a Block
    "q_proj": "attn.q_proj", "k_proj": "attn.k_proj",
    "v_proj": "attn.v_proj", "c_proj": "attn.c_proj",
    "fc_in":  "mlp.fc_in",   "fc_out": "mlp.fc_out",
}
KEYS = [  # exactly 36, built from an explicit product — never an isinstance/substring scan (P1)
    (L, p, f"blocks.{L}.{PROJ_PATHS[p]}.weight")
    for L in range(6) for p in ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")
]

def full_ft_ratios(arm_model: dict, w0_model: dict) -> dict:
    """‖W_arm − W₀‖_F / ‖W₀‖_F per (layer, projection). Weights only, never biases."""
    out = {}
    for L, p, key in KEYS:
        w0 = w0_model[key].to(torch.float64)      # fp64 for the norm — statistics domain
        dw = arm_model[key].to(torch.float64) - w0
        out[(L, p)] = float(torch.linalg.norm(dw) / torch.linalg.norm(w0))
    return out

def adapter_ratios(adapter: dict, scale: float, w0_model: dict) -> dict:
    """ΔW = scale · (B @ A); scale = alpha/r read from the artifact, never recomputed (P3)."""
    out = {}
    for L, p, key in KEYS:
        prefix = key[: -len(".weight")]
        a = adapter[f"{prefix}.lora_A"].to(torch.float64)   # (r, in)
        b = adapter[f"{prefix}.lora_B"].to(torch.float64)   # (out, r)
        dw = scale * (b @ a)                                # (out, in) == base.weight shape
        w0 = w0_model[key].to(torch.float64)
        out[(L, p)] = float(torch.linalg.norm(dw) / torch.linalg.norm(w0))
    return out
```

### Fingerprint guard — fail loud, never a bare `assert`

```python
# Source: register from src/personacore/lora/inject.py:179 (`raise RuntimeError`, never assert)
#         and scripts/finetune_ab.py's SystemExit divergence check
def require_fingerprint(adapter_art: dict, w0_blob: dict, w0_path) -> None:
    want = adapter_art["base_fingerprint"]
    got = {"git_sha": w0_blob["git_sha"], "step": w0_blob["step"], "val_loss": w0_blob["val_loss"]}
    if want != got:
        raise SystemExit(
            f"[extract_deltas] adapter base fingerprint {want!r} does not match {w0_path} "
            f"({got!r}). VIZ-02's ‖W₀‖_F denominator would describe the wrong base model. "
            "load_adapter only WARNS on this (D-02, base evolves mid-milestone); a figure "
            "cannot afford the warning."
        )
```

### Loading a full checkpoint read-only (no RNG side effects)

```python
# Source: scripts/finetune_ab.py:208, scripts/teach_persona.py:545 — the established register.
# SECURITY: weights_only=False reads ONLY the project's OWN trusted checkpoints. These files
# carry pickled optimizer/RNG/numpy objects that torch>=2.6's weights_only=True default rejects.
# Never a foreign file; never a path from argv or an environment variable.
blob = torch.load(BEST_PATH, map_location="cpu", weights_only=False)
w0 = blob["model"]   # NOT checkpoint.load_checkpoint — that RESTORES global RNG state.
```

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | `mean` is the right per-cell Fisher aggregate (over `sum` / Frobenius) | Checkpoint Tensor Structure | Low — it is a Claude's-discretion-adjacent choice not fixed by D-06. The mean-normalized cache makes `mean` the interpretable option, but `sum` would weight by tensor size and change the correlation's inputs. **Whichever is chosen must be recorded in the artifact.** |
| A2 | Exact ties in the 36-cell grids are near-impossible, so tie handling is a safety measure rather than a correctness necessity | Pure-Numpy Rank Statistics | Low — average ranks are correct either way; the assumption only affects how loudly the choice needs justifying. |
| A3 | Extraction on CPU is bit-deterministic across runs (pure tensor arithmetic, no batch reductions) | skipif pattern | Medium — if false, D-08's byte-for-byte integration test flakes. Mitigate by forcing `map_location="cpu"` and by treating a first observed mismatch as information, not as a reason to pre-emptively add a tolerance. |
| A4 | Appending after the last heading of `results/phase13_ab_report.md` satisfies D-17's separation requirement | docs/REPORT.md Structure | Low — D-17 requires "explicitly dated and marked as Phase 15 material, visibly separate"; placement at EOF plus an explicit marker satisfies it, but the planner may prefer a horizontal rule + a `## Phase 15 Addendum (2026-08-XX)` heading. |
| A5 | The three headline numbers D-16 names are the ones quoted in `## D-16` (recall taught/held-out, retention delta, tokens/word) rather than some other framing of the same evidence | D-16 | Low — CONTEXT names them as "recall rate against its gate", "retention delta from the A/B", "the Phase 11 token inflation tax"; the mapping is direct. |

---

## Open Questions (RESOLVED)

### Q1 🔴 — D-15's quote-exactly rule vs. a known factual error in limitation L8's source

**What we know:** D-15 requires each of the eight limitations to *"quote the source report's exact
wording — not summarized, not softened, not reordered for flow"*, with visible truncation as the
only permitted shortening. Limitation L8's source (`docs/REPORT.md:61-63`, mirrored at
`README.md:30-31`) attributes BPE merge exhaustion to *"the bounded TinyStories corpus"*. That is
**verifiably wrong**: `scripts/train_tokenizer.py:31` trained the frozen production tokenizer on
`tests/fixtures/tiny_corpus.txt` (11,469 bytes). The error is a **tracked, open** tech-debt item
whose recorded natural home is this phase's DOC-02 honesty pass (`.planning/STATE.md`,
`v1.0-MILESTONE-AUDIT.md:18`).

**What's unclear:** three constraints collide and cannot all hold —
(a) D-15 says quote exactly; (b) D-13 says v1.0 REPORT.md sections stay textually untouched;
(c) an honesty pass that knowingly re-publishes a wrong attribution on the front page is the
opposite of this phase's stated register.

**Recommendation:** treat this as a planning decision requiring user input, not a research call.
The shape that satisfies all three: **quote L8 verbatim** (honoring D-15 and D-13), and
**immediately follow the quote with a dated, clearly-labeled Phase 15 correction note** naming the
actual training corpus — the same "dated, separate, does not amend the original" register D-17
already requires for the correlation verdict and Phase 14 D-12 requires for post-verdict
decisions. The README's v2.0 rewrite (which is not covered by D-13's untouched clause) can state
the corrected attribution directly. **Do not silently paraphrase the quote to fix it** — that is
exactly the drift vector D-15 exists to close.

**RESOLVED (2026-08-02):** adopted verbatim as **R1** — quote L8 verbatim including *"the
bounded TinyStories corpus"*, then a dated, evidence-naming Phase 15 correction note; README
states the corrected attribution directly because it carries no D-13 protection. Implemented
in `15-05-PLAN.md` Task 3 (the quote + correction note) and `15-06-PLAN.md` Task 2 (the README
half), and made permanent by `15-08-PLAN.md` Task 1's `test_limitations_quotes_are_verbatim`.

### Q2 🟡 — D-13's "textually untouched" vs. stale future-tense v1.0 text

**What we know:** `docs/REPORT.md:433-443` (`Milestone 2 (upcoming)`) describes LoRA, EWC,
teach-then-recall, and *"weight-delta visualizations"* in the future tense. `## Where to Go Next`
(448-456) lists `demo.ipynb` as *the* notebook. `README.md:4-7` and `README.md:97-113` say the
same. All are now stale.

**What's unclear:** D-13 protects REPORT.md's v1.0 sections but says nothing about README (which
DOC-02 clearly rewrites) or about how a front-to-back reader avoids reading the stale roadmap as
current.

**Recommendation:** place the D-13 **dated Milestone 2 boundary marker before** any stale
future-tense text a reader would hit — i.e. immediately after `## Reproducibility` (line 421) or
at the top of `## Limitations and the Milestone 2 Roadmap` — so the marker frames everything after
it as "as written on 2026-06-10". The v2.0 sections then append at EOF. This preserves every
v1.0 word while removing the misreading. README carries no such protection and should simply be
rewritten.

**RESOLVED (2026-08-02):** adopted as **R3** — the dated boundary marker goes immediately after
`## Reproducibility` (line 421), directly before `## Limitations and the Milestone 2 Roadmap`;
every v2.0 section appends at EOF; README is rewritten outright. Implemented in
`15-05-PLAN.md` Task 1 (the marker, with the first 421 lines asserted byte-identical) and
`15-06-PLAN.md` Task 1 (the README rewrite).

### Q3 🟡 — Does `demo.ipynb` (v1.0) get an edit?

**What we know:** D-13 requires *"Both notebooks state this independence explicitly in their
opening cells."* CONTEXT `<domain>` lists *"changes to … the v1.0 notebook's existing cells"* as
out of scope. `demo.ipynb` has 8 cells; cell 0 is the title markdown.

**What's unclear:** whether adding the independence statement means editing cell 0 (out of scope
as written) or **prepending a new cell 0** (which changes no existing cell).

**Recommendation:** prepend a new markdown cell. It satisfies D-13 literally and violates the
scope boundary in neither letter nor spirit. Also note: roadmap SC3 says *"demo.ipynb is updated
with honest numbers"*, but D-13 supersedes it with a **new** v2.0 notebook. The planner should
record that supersession explicitly, the way `phase13_ab_report.md:303-305` recorded
*"ROADMAP wording superseded"* rather than silently absorbing the change.

**RESOLVED (2026-08-02):** adopted as **R4** — prepend a new markdown cell as `demo.ipynb`
cell 0 (no existing cell edited, all eight asserted byte-identical), ship the v2.0 numbers in a
new self-contained `demo_v2.ipynb`, and record the SC3 supersession as an explicit dated note
in ROADMAP. Implemented in `15-07-PLAN.md` Tasks 1, 2 and 3.

### Q4 🟢 — Which of the permutation p and the bootstrap CI is load-bearing for D-11's gate?

Covered in `## Pure-Numpy Rank Statistics`. D-11 read literally makes the **CI** the gate and the
**p** descriptive. One sentence in the pre-registration closes it. Flagged here only so the
planner writes that sentence *before* either number exists.

**RESOLVED (2026-08-02):** adopted as **R5** — the bootstrap CI is the load-bearing half of the
D-11 gate; the permutation p is descriptive and never overrides it or converts a miss into a
pass. Written as a module-level pre-registration comment in `15-01-PLAN.md` Task 1, committed
before any correlation number exists, and pinned by
`grep -qi 'load-bearing' scripts/phase15_stats.py` in that task's acceptance criteria.

---

## Sources

### Primary (HIGH confidence — direct inspection of this repo, 2026-08-02)

- `.planning/phases/15-figures-writeup/15-CONTEXT.md` — D-01..D-18, canonical refs
- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/config.json`
- `.planning/milestones/v1.0-MILESTONE-AUDIT.md` — WR-04/WARNING-3 tokenizer-corpus debt
- `src/personacore/config.py:89` (`n_layer: int = 6`), `src/personacore/lora/config.py:16`
  (`TARGET_PROJECTIONS`), `src/personacore/lora/layer.py:27,60` (`scale = alpha/r`),
  `src/personacore/lora/inject.py:38,250-264`, `src/personacore/checkpoint.py` (all six
  export/load functions), `src/personacore/continual/fisher.py:44-55` (`_VARIANT`, `_spearman`),
  `src/personacore/model/gpt.py:71-74,120-121,136-138,166`
- `scripts/plot_phase13.py` (the plotting register), `scripts/finetune_ab.py:20-21,58,208`,
  `scripts/teach_persona.py:32,90,194,545`, `scripts/train_tokenizer.py:31`
- `tests/test_phase13_plots.py`, `tests/test_slim_checkpoint.py:18,42,168`,
  `tests/test_phase14_scoring.py:29,405-423`, `tests/conftest.py`
- `results/finetune_smoke_report.md`, `results/phase13_ab_report.md`,
  `results/phase14_recall_report.md`, `results/phase14_calibration_report.md`,
  `results/inflation_report.md`, `results/retention_anchors.json`
- `docs/REPORT.md`, `README.md`, `demo.ipynb`, `pyproject.toml`, `Makefile`,
  `.github/workflows/ci.yml`, `.gitignore`
- **Live checkpoint inspection** — `torch.load` on all six `.pt` files: key sets, tensor shapes,
  fingerprints, `fisher_meta`, `ewc_lambda`
- **Live execution** — the Spearman/permutation/bootstrap recipe validated against known answers;
  `LogNorm` zero/negative masking and two-axis colorbar confirmed on matplotlib 3.10.9
- **Baseline test run** — `.venv/bin/pytest -q` → 392 passed, 1 skipped, 119.64 s

### Secondary (MEDIUM confidence)

- Spearman canonical reference value `-0.17575757575757575` (Wikipedia IQ/TV-hours worked
  example) — cross-verified by independent computation here to 1e-15
- scipy `spearmanr` tie-handling reference value `0.9486832980505138` — reproduced here to 1 ulp
  without scipy installed (value recalled from training data, then independently confirmed by the
  average-rank implementation converging on it)

### Tertiary (LOW confidence — flagged, not relied upon)

- Percentile-bootstrap small-`n` bias characterization (general statistical folklore; not
  verified against a citation in this session). Used only to recommend *disclosing* the method,
  never to justify a specific numeric adjustment.

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Checkpoint structure & key strings | **HIGH** | Every key, shape, and fingerprint read directly from the real `.pt` files |
| Statistics recipe | **HIGH** | Executed and validated against three independent known answers, plus determinism and null/signal behavior |
| matplotlib log-scale mechanics | **HIGH** | Executed on the installed 3.10.9; zero-masking and shared-colorbar behavior confirmed by render |
| D-15 verbatim quotes | **HIGH** | All eight located with file, section heading, and line number; none paraphrased |
| D-16 headline numbers | **HIGH** | All three read from their committed source reports with gates and denominators |
| Structural-enforcement pattern (D-07) | **HIGH** | AST register verified in `tests/test_phase14_scoring.py`; subprocess variant is a straightforward strengthening |
| `## Decision:` section count | **HIGH** | `grep -c` → 14 (CONTEXT says 15; corrected here) |
| Fisher per-cell aggregation choice | **MEDIUM** | The mean-normalization semantics strongly favor `mean`, but this is a judgment, not a locked decision — see A1 |
| Byte-for-byte extraction determinism | **MEDIUM** | Reasoned from the absence of batch reductions; not empirically re-run twice — see A3 |
| Whether the D-10 correlation gate will pass | **N/A — DELIBERATELY NOT INVESTIGATED** | Computing it would destroy D-09's pre-registration. Treat as genuinely open. |

**Research date:** 2026-08-02
**Valid until:** 2026-09-01 (30 days — all findings are about frozen local artifacts and pinned
library versions; nothing here depends on a moving external target)
