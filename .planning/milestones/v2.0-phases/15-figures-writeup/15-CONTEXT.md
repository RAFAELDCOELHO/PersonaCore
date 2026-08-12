# Phase 15: Figures & Writeup - Context

**Gathered:** 2026-08-02
**Status:** Ready for planning — all three gray areas decided (D-01..D-18)

<domain>
## Phase Boundary

The v2.0 narrative and its two signature figures, computed **read-side only** from artifacts that
already exist on disk (VIZ-02, VIZ-03, DOC-02):

- the adapter weight-delta heatmap — relative Frobenius change `‖ΔW‖_F/‖W₀‖_F` on the
  layer × six-projection grid, log color scale;
- the three-panel figure juxtaposing the Fisher diagonal with the naive-vs-EWC delta heatmaps,
  plus a **measured** statistic for the "EWC dodges high-Fisher coordinates" claim;
- the v2.0 narrative across `README.md`, `docs/REPORT.md`, and a new v2.0 notebook, carrying the
  honest numbers in the same register as the v1.0 547-live-ids disclosure.

No training, no re-measurement, no new checkpoints. Every number this phase reports is re-cited
from committed Phase 11/12/13/14 evidence or computed deterministically from frozen checkpoints.

Not in this phase: any retraining or re-running of a prior phase's experiment; DEMO-F1 /
DEMO-F2 (future milestone); changes to `scripts/demo_app.py` or the v1.0 notebook's existing
cells; re-opening any prior phase's recorded verdict.

</domain>

<decisions>
## Implementation Decisions

### VIZ-03 panel comparability & color scale

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

### The committed norms artifact

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

### The "EWC dodges high-Fisher coordinates" claim

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

### Narrative surfaces, register & Limitations (DOC-02)

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

### Verdict placement & VIZ-02 disclosure

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
  by claim bound) is the locked part.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/ROADMAP.md` — Phase 15 goal + 3 success criteria; `Depends on: Phase 13, Phase 14;
  pure read-side`. **Note:** SC2's "showing EWC visibly dodging high-Fisher coordinates" is
  narrowed by D-11 if the correlation gate misses — the wording is not a guaranteed outcome.
- `.planning/REQUIREMENTS.md` — VIZ-02, VIZ-03, DOC-02 text; VIZ-01 (Phase 13, Complete) as the
  figure precedent; the Out of Scope table

### Prior-phase contracts this phase consumes
- `.planning/phases/13-ewc-a-b-no-forgetting-experiment/13-CONTEXT.md` — D-06 gated-vs-descriptive
  register (D-11's analog), D-08 end-of-run endpoints, D-09 the §8 reconciliation, D-10
  pre-registration in committed code, and the explicit note that **Phase 15 consumes the A/B
  report, both figures, and the reconciliation narrative**
- `.planning/phases/14-teach-then-recall-demo/14-CONTEXT.md` — D-12 gate-miss policy (verbatim
  source for D-11/D-17), D-17/D-18 structural-enforcement register (source for D-04/D-07),
  D-07 permanent-vs-checkpoint-specific test split (source for D-08), D-20 reconciliation, D-22
  reversal-curse scoping; and the explicit note that **Phase 15 consumes the recall numbers and
  `scale·B@A` for the ΔW heatmaps — the adapter must never ship merged**
- `.planning/phases/14-teach-then-recall-demo/14-LEARNINGS.md` — the declared-vs-structural
  guarantee failure mode D-09 cites as its reason for measuring rather than asserting

### Committed evidence the writeup re-cites (never recomputes)
- `results/phase13_ab_report.md` — the A/B numbers, the §8 reconciliation, and **the file D-17
  appends the correlation verdict to**
- `results/phase14_recall_report.md` — recall rates, taught vs held-out split, the controls
- `results/phase14_calibration_report.md` — threshold derivation, the register arm, the
  with/without-replay comparison (source of the +224.81% collapse figure)
- `results/phase14_factset_report.md` — the pre-flight gate, close-call rejections
- `results/inflation_report.md` — the Phase 11 tokenizer inflation tax (D-16's third headline
  number)
- `results/finetune_smoke_report.md` §8 — the λ*=None verdict, unamended
- `results/retention_anchors.json` — **the format precedent for D-05's committed JSON**
- `docs/REPORT.md` — the v1.0 report being extended; its `## Decision:` form (15 sections) is
  D-14's template, and `## Limitations and the Milestone 2 Roadmap` is the section D-15 grows
- `README.md` — the 547-live-ids bullet (lines 29–33) is the **literal density target** for D-16

### Code seams
- `scripts/plot_phase13.py` — the plotting-script template: reads committed CSVs, `savefig`
  only, never `show()`; `plot_forgetting_curve(out_dir)` / `plot_frontier(out_dir)` shape
- `src/personacore/lora/inject.py` — `lora_state_dict`, `merged_state_dict`, the `scale·B@A`
  computation VIZ-02's ΔW comes from
- `src/personacore/continual/fisher.py` + `ewc.py` — the Fisher diagonal's structure and key
  naming, for reading `checkpoints/fisher_tinystories.pt`
- `src/personacore/checkpoint.py` — `load_adapter` / `load_slim` (`weights_only=True` choke
  points) for the extraction script
- `src/personacore/config.py:89` — `n_layer: int = 6`, the source of D-10's **n = 36**
- `tests/test_slim_checkpoint.py:18,168` — the documented `skipif`-on-gitignored-artifact
  pattern D-08's optional integration test follows

### Checkpoints the extraction script reads (all gitignored)
- `checkpoints/persona_adapter.pt` — the SHIPPABLE persona adapter (VIZ-02's ΔW source).
  `scripts/teach_persona.py:194` states explicitly this is the shippable path, **not**
  `phase14_real_adapter.pt`
- `checkpoints/phase13_naive_latest.pt`, `checkpoints/phase13_ewc_latest.pt` — the two A/B arms
- `checkpoints/best.pt` — W₀ for both full-fine-tune deltas
- `checkpoints/fisher_tinystories.pt` — the N=2000 Fisher cache at `best.pt`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`scripts/plot_phase13.py`** is the direct template: thin, `out_dir`-parameterized, replots
  from committed data, `savefig` only. Its committed outputs (`results/phase13_forgetting_curve.png`,
  `results/phase13_frontier.png`) establish that **figures live in `results/` and are committed
  as PNG** — VIZ-02/03 follow, no `figures/` directory needed.
- **`results/retention_anchors.json`** is the format precedent for D-05: a small committed JSON
  of locked numbers that downstream code and reports both cite.
- **`skipif`-on-gitignored-artifact is an established pattern**, not a new one — present in
  `tests/test_forbid_ids.py:196`, `tests/test_lora_artifact.py:238`,
  `tests/test_phase14_demo.py:606,620`, `tests/test_slim_checkpoint.py:168`, and documented in
  `tests/test_slim_checkpoint.py:18`. D-08's optional integration test lands on existing rails.
- **`lora_state_dict` / `merged_state_dict`** already expose what VIZ-02 needs; the adapter is
  never shipped merged (Phase 14), so `scale·B@A` is computed for the figure only.

### Established Patterns
- **Pre-registration in committed code before numbers exist**, git history as proof
  (`finetune_smoke.py`, Phase 13 D-10) — D-09/D-12 follow this exactly.
- **Honest negatives stand unamended**; discretionary continuations are logged separately, dated
  after the verdict (Phase 12 §8 → λ=0.01; Phase 14 D-12) — D-11's miss policy and D-17's
  dated-append constraint both inherit it.
- **Two code paths claiming to prove the same thing must be held together structurally, not by
  convention** (Phase 14 D-17/D-18) — D-07's import-time guard is the third instance.
- **Terse form travels with the artifact, full form lives in the committed report** (Phase 14
  D-18) — D-04, D-16 and D-17 all apply this asymmetry.
- **Explicit `raise SystemExit`, never `-O`-strippable `assert`**, for proof checks in scripts.
- CPU-only, GPU-free test suite; `checkpoints/`, `data/` and `logs/` gitignored; evidence lives
  in `results/`.
- **`demo.ipynb` re-cites, never recomputes** (its own cell-3 heading) — carried into the v2.0
  notebook by D-13.

### Integration Points
- **No dependency added.** scipy stays out (D-12); `numpy` + `matplotlib` cover everything.
- The extraction script is the **only** new code that touches `.pt` files; the plotting script is
  structurally forbidden from doing so (D-07).
- `results/phase13_ab_report.md` gains a dated Phase 15 section (D-17) — the one place this
  phase writes into another phase's committed evidence, under an explicit separation constraint.
- Phase 15 is terminal for the v2.0 milestone: nothing downstream consumes it.

</code_context>

<specifics>
## Specific Ideas

- **The recurring principle across this discussion: name the actual driver, don't gesture at a
  category.** It produced the vmax-outlier disclosure naming the specific layer/projection
  (D-02), the non-comparability note naming parameter count and training budget rather than
  "different regimes" (D-03), and the extraction docstring naming five specific checkpoints
  (D-08). A generic disclosure is a disclosure a reader cannot act on.

- **Prove by construction, not by convention.** D-07's import-time guard rather than a docstring
  is the clearest case, and it is the third time this project has converted a claimed invariant
  into a structural one (after Phase 14's `forbid_ids` mask comparison and the token-id
  byte-identity check). Phase 14's LEARNINGS named declared-vs-structural as the session's most
  recurring failure mode; D-09's decision to measure rather than assert comes from the same
  reading.

- **Close ambiguity before the number exists, not after.** D-11's gate initially admitted two
  contradictory readings. Surfacing it during discussion — rather than discovering it after
  seeing ρ = +0.15 and being tempted to resolve it in whichever direction looked better — is the
  entire practical value of pre-registration, and the provenance note in D-11 records that it
  happened that way.

- **Flatness is a finding.** D-01's refusal to rescale a visually boring panel is the figure-side
  version of "honest negatives stand unamended." A figure that has been made equally busy in
  every panel has had its result edited out.

- **Asymmetry of detail, never contradiction.** D-04, D-16 and D-17 all place a terse form where
  the artifact travels and the full form where the reasoning lives. The invariant across all
  three: a reader comparing the two locations finds **different amounts, never different
  things.**

- **The Limitations section is the deliverable most able to be quietly softened**, which is why
  D-15 requires exact quotes with visible truncation and an ordering derived from which claim
  each limitation bounds. Paraphrase-to-shorten and severity-ordering are both editorializing
  disguised as editing.

</specifics>

<deferred>
## Deferred Ideas

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

</deferred>

---

*Phase: 15-Figures & Writeup*
*Context gathered: 2026-08-02*
