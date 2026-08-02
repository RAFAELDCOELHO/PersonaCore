# Phase 15: Figures & Writeup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-02
**Phase:** 15-Figures & Writeup
**Areas discussed:** Heatmap normalization & color scale; Figure reproducibility & the committed
norms artifact; "EWC dodges Fisher" — visual vs measured; Narrative split & Limitations scope
(DOC-02); Residuals (verdict placement, VIZ-02 disclosure)

All four originally-offered areas were eventually discussed — the user selected them across
successive rounds rather than up front.

---

## Gray area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Heatmap normalization & color scale | How the three VIZ-03 panels are normalized and scaled given their different units | ✓ (round 1) |
| "EWC dodges Fisher" — eyeball or measured | Whether the phase reports a statistic for the dodging claim | ✓ (round 3) |
| Figure reproducibility from committed material | Whether a per-layer norms intermediate is committed so the figures survive without the gitignored checkpoints | ✓ (round 2) |
| Narrative split & Limitations scope | README / REPORT.md / demo.ipynb division and what Limitations names | ✓ (round 4) |

**Notes:** Before options were presented, the orchestrator surfaced that the workflow's UI-SPEC
gate had fired on false positives — the keyword scan matched `ui` inside "Req**ui**rements" and
`form` inside "Trans**form**er" in the ROADMAP progress table. Phase 15 has no frontend surface,
so it was treated as `--skip-ui`.

---

## Heatmap normalization & color scale

**User stated a position before options were presented.** No competing options were evaluated for
the core question; the alternatives below were surfaced afterwards for the sub-decisions the
position did not settle.

**User's choice:** naive and EWC delta panels MUST share one color scale — same discipline that
decided end-of-run over best-checkpoint for Phase 13's 2×2 (comparability over visual
convenience). If sharing one scale makes one panel look nearly flat, that flatness IS the finding
and is reported as such, not hidden by independently rescaling each panel to look equally "busy."
The Fisher panel may use its own scale on a **units** argument (squared-gradient magnitude vs a
weight-delta ratio) — explicitly *not* a convenience argument — and the caption/report must state
which panels share a scale and why Fisher doesn't. → **D-01**

### Sub-decision: shared-scale range and log floor

| Option | Description | Selected |
|--------|-------------|----------|
| Full range, vmin = smallest nonzero cell | Nothing clipped at either end; most faithful to the stated position; risk that one outlier compresses the grid | ✓ |
| Full range top, vmin = stated negligible-change floor | vmin pinned to a committed constant (e.g. 1e-6) that would itself need justifying | |
| Shared percentile clip, clipping marked | 1–99% clip with clipping disclosed; most readable; trades absolute-magnitude honesty for legibility | |

**User's choice:** option 1.
**Notes (amendment):** if the shared range does compress the grid, the report text must **name the
specific layer/coordinate driving vmax**, not just show the compressed figure and move on — a
reader seeing a nearly-flat grid with one bright cell needs the caption to say "layer N's
projection dominates the range; see the per-layer table in [artifact]." Cited as the same
discipline as naming which family drove a coarse held-out score in Phase 14, rather than leaving a
visual oddity unexplained. → **D-02**

### Sub-decision: VIZ-02 vs VIZ-03 comparability

| Option | Description | Selected |
|--------|-------------|----------|
| Independent scales + explicit non-comparability note | Report states plainly the two are not comparable and why | ✓ |
| One scale across both figures | Direct adapter-vs-full-fine-tune magnitude comparison; asserts a comparison the phase hasn't justified | |
| Independent scales, no note | Lowest effort; leaves comparability to the reader | |

**User's choice:** option 1.
**Notes (amendment):** the note must be **specific, not generic** — not "these are not directly
comparable" as boilerplate, but naming the actual confound: parameter count (331,776 vs full
model), training budget (LoRA teaching run vs full fine-tune step count), and that a smaller
absolute ΔW for the adapter does **not** imply "more conservative" or "less effective" learning —
it reflects the parameter budget, not quality. Explicitly framed as the same specificity standard
as the vmax-outlier disclosure. → **D-03**

### Sub-decision: where the shared-scale disclosure lives

| Option | Description | Selected |
|--------|-------------|----------|
| Both figure and report prose | PNG stays self-describing when it travels alone; mirrors Phase 14 D-18 | ✓ |
| Report prose only | Cleaner figure; figure stops being self-describing outside REPORT.md | |
| Figure only | One source of truth; reasoning sits apart from its peers in the report | |

**User's choice:** option 1.
**Notes (amendment):** the figure-side disclosure should be **terse** — enough to prevent
standalone misreading, not a paragraph competing visually with the data. The report side carries
the full reasoning (the named confounds above). Cited as mirroring D-18's own split: the live UI
panel shows ids tersely, the committed harness evidence carries full provenance. Same asymmetry of
detail, same consistency principle — figure and report must never say different things, only
different amounts. → **D-04**

---

## Figure reproducibility & the committed norms artifact

**User stated a position before options were presented.**

**User's choice:** the per-layer table and the caption's regeneration input are the **same
artifact** — one committed JSON/npz of per-layer × per-projection Fisher magnitudes and both delta
ratios, not a separate prose-only table plus a separate intermediate. Closes the gap the
discussion surfaced (VIZ-02/03 can't currently be regenerated without the gitignored 278 MB
checkpoints) using work the vmax disclosure already required. Cited as the same register as
`plot_phase13.py`: every locked number in the project's most visible deliverable should be
re-derivable from committed material. → **D-05**

### Sub-decision: format

| Option | Description | Selected |
|--------|-------------|----------|
| JSON | ~100 numbers; human-readable, git-diffable; `results/retention_anchors.json` precedent | ✓ |
| .npz | Compact, native numpy; opaque in git; compactness buys nothing at this size | |
| Both | Two representations that can silently drift | |

**User's choice:** JSON. **Notes:** none beyond the selection. → **D-05**

### Sub-decision: does VIZ-02's adapter ΔW share the artifact?

| Option | Description | Selected |
|--------|-------------|----------|
| One artifact, each block regime-labelled | Single self-describing file; puts non-comparable numbers in one container | ✓ |
| Two artifacts, one per figure | Physically separates non-comparable quantities; splits the "one artifact" principle | |

**User's choice:** option 1.
**Notes (amendment):** regime and confound fields (`param_count`, `training_budget`, or
equivalent) must be present on **EVERY** block **including the fisher block** — not just
adapter/naive/ewc — so a reader parsing any single block in isolation still sees what it can and
cannot be compared against. The file's top level must also carry a short **machine-readable** note
(not just block-level fields) stating which blocks share a comparison basis (naive↔ewc: yes) and
which don't (adapter↔either full-fine-tune block: no) — the same explicit non-comparability
statement now present a third time, in the data itself. → **D-06**

### Sub-decision: how the plotting scripts get their numbers

| Option | Description | Selected |
|--------|-------------|----------|
| Extract, then plot from the artifact only | Committed PNG provably derives from committed numbers; regenerability proven by construction | ✓ |
| One script: read checkpoints, write artifact, plot | Fewer moving parts; PNG could reflect a checkpoint state the artifact doesn't | |
| Plot prefers checkpoints, falls back to artifact | Two code paths producing the same figure — the D-17/D-18 failure mode | |

**User's choice:** option 1.
**Notes (amendment):** enforce the separation with the same discipline as D-17/D-18 — a static
check or import-time guard confirming the plotting script has **no code path that opens a `.pt`
file**, not just a docstring saying "reads only the artifact." If the plot script's only way to
get numbers is the committed JSON, prove that by construction (no `torch.load` import in the
plotting module at all), not by convention. → **D-07**

### Sub-decision: test coverage split

| Option | Description | Selected |
|--------|-------------|----------|
| Plot-from-artifact only, docstring stating why | Phase 14 D-07's split (permanent half / checkpoint-specific half) | ✓ |
| Both, with checkpoint loads mocked | Covers extraction arithmetic against synthetic tensors; mock asserts the formula, not real checkpoint reading | |
| No new test | Least work; out of step with the project's one-runnable-check rule | |

**User's choice:** option 1.
**Notes (amendment):** the extraction script's docstring must **name the specific checkpoints** it
depends on (`persona_adapter.pt`, `phase13_naive_latest.pt`, `phase13_ewc_latest.pt`,
`fisher_tinystories.pt`, `best.pt`) and state, same as D-07's guessability half, that re-running
extraction against a future checkpoint requires a **fresh manual run producing a fresh committed
artifact** — not a test that silently stays green while checking nothing. If cheap, add one
offline-only integration test, `skipif`-gated on checkpoint presence (pattern already established
project-wide), running extraction end-to-end and asserting byte-for-byte match with the committed
artifact — not required for CI. → **D-08**

**Orchestrator verification:** both claims in this amendment were checked before being written
into CONTEXT.md. `skipif`-on-gitignored-artifact confirmed present in 5 locations across 4 test
files and documented at `tests/test_slim_checkpoint.py:18`. `persona_adapter.pt` confirmed as the
shippable adapter at `scripts/teach_persona.py:194`, which states it explicitly over
`phase14_real_adapter.pt`.

---

## "EWC dodges Fisher" — visual or measured

**User stated a position before options were presented.**

**User's choice:** measured, not visual-only — an unmeasured visual claim on the project's
signature figure would repeat exactly the declared-vs-structural-guarantee gap Phase 14's
learnings named as the session's most recurring failure mode. The decision rule must be written
and committed **before** the correlation is computed — same blind-rule discipline as
Phase 13 D-09/D-10, not a number chosen after seeing whether it supports the roadmap's claim.
Reuses the artifact locked in the prior area, so it costs no new data collection. → **D-09**

### Sub-decision: granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Per-block: layers × 6 projections (n≈36) | Statistic describes exactly what the figure shows; no schema change; thin sample | ✓ |
| Per-parameter, aggregated into the artifact | Far more power; describes something the figure does not show | |
| Both, side by side | Two numbers that could disagree, requiring explanation | |

**User's choice:** option 1.
**Notes (amendment):** the pre-registered rule must state explicitly that n≈36 limits what can be
claimed — report the coefficient **and** its confidence interval or an appropriate significance
threshold, not a bare point estimate implying more precision than 36 cells support. The rule must
also state up front what happens if the correlation is present but not statistically
distinguishable from zero at this n: that outcome must be reportable as **"suggestive but not
statistically demonstrated at this sample size"** — the same register as every other
underpowered-but-honest finding logged here — rather than either overclaiming significance or
discarding the number. → **D-10**

**Orchestrator note:** n was confirmed to be exactly 36, not approximately —
`src/personacore/config.py:89` sets `n_layer: int = 6`, giving 6 × 6 projections.

### Sub-decision: what is correlated

| Option | Description | Selected |
|--------|-------------|----------|
| Δ reduction: naiveΔ − ewcΔ | Positive correlation = EWC restrains hardest where Fisher is highest; uses both arms, removing the single-arm confound | ✓ |
| Fisher vs ewcΔ alone | Simpler; confounds the penalty's effect with where that arm would have moved little anyway | |
| Fisher vs the ratio ewcΔ/naiveΔ | Scale-free; unstable near zero; drifts from the absolute-magnitude framing already locked | |

**User's choice:** option 1.
**Notes (amendment):** the rule must specify the **predicted sign** explicitly — positive
correlation between Fisher magnitude and (naiveΔ − ewcΔ) is what "EWC dodges high-Fisher
coordinates" means quantitatively. A negative or near-zero correlation means the visual claim
doesn't hold at a measurable level, and **that outcome must be stated as plainly as a positive
one**, not softened because it contradicts the roadmap's framing. → **D-10**

### Sub-decision: gate or descriptive

| Option | Description | Selected |
|--------|-------------|----------|
| Gated — miss recorded unamended | Full pass/fail against the committed rule; strongest | |
| Descriptive — reported, no gate | Phase 13 D-06's acquisition-side register; pre-registration with no teeth | |
| Gated on sign, magnitude descriptive | Gates the part with a firm prior; magnitude stays honest about n≈36 | ✓ |

**User's choice:** option 3.
**Notes:** the gated half — sign must be positive to count as demonstrating the claim; a negative
or indistinguishable-from-zero sign is a miss, recorded unamended per Phase 14 D-12's verbatim
policy, narrowing the roadmap's SC2 wording exactly as a gate miss would in any other phase. The
descriptive half — the coefficient's magnitude and CI are reported alongside the sign verdict,
explicitly framed as "the sign is the falsifiable claim; the magnitude is reported honestly given
n≈36 and is not itself pass/fail." Named as the correct analog to Phase 13 D-06 — not a full
exemption from gating, but gating only the part the sample size supports. → **D-11**

### Sub-decision: resolving the gate's internal ambiguity

The orchestrator surfaced that the two prior statements admitted contradictory readings — "gate
the sign only" implies ρ=+0.15 with a CI spanning zero passes; "indistinguishable from zero is a
miss" implies it fails.

| Option | Description | Selected |
|--------|-------------|----------|
| Miss — positive sign AND CI excluding zero required | Strictest; the only reading where "indistinguishable from zero is a miss" means anything | ✓ |
| Pass — sign alone gates, CI disclosed but not binding | At n=36 a positive point estimate is easy to obtain by chance; gate has little falsifying power | |
| Three-way verdict, only negative is a D-12 miss | Most granular; introduces a verdict tier this project hasn't used | |

**User's choice:** option 1.
**Notes:** the gate requires **both** a positive sign and a CI excluding zero. ρ=+0.15 with a CI
spanning zero is a miss, recorded unamended, in the "suggestive but not statistically demonstrated
at n=36" register — reported, not discarded, and not softened into a passing verdict. The user
explicitly noted the value of closing the gap before any correlation was computed, "rather than to
discover the ambiguity after seeing ρ=+0.15 and being tempted to resolve it in whichever direction
looks better." → **D-11**

### Sub-decision: statistic and significance machinery

| Option | Description | Selected |
|--------|-------------|----------|
| Spearman ρ + permutation test + bootstrap CI | All numpy, ~15 lines, no new dependency; Spearman over Kendall on readability since both are rank-based and equally robust | ✓ |
| Kendall τ + permutation test + bootstrap CI | Cleaner small-sample behavior; less recognizable to a portfolio reader | |
| Spearman ρ + closed-form Fisher-z CI | Fewest lines; normality assumption is the shakiest at n=36 | |

**User's choice:** option 1.
**Notes (amendment):** both the coefficient and the CI computation must be pinned to a
**documented random seed** for the permutation/bootstrap resampling — same discipline as every
other seeded calculation in this project — so the gate verdict is reproducible byte-for-byte from
the committed artifact, not dependent on whatever shuffle order a run happens to draw. The ~15
lines must be commented with the rationale locked here (why Spearman over Kendall, why resampling
over Fisher-z) so a future reader sees the choice was deliberate, not default. → **D-12**

**Orchestrator note:** scipy was confirmed **not** to be a declared dependency before these options
were framed — `pyproject.toml` declares `numpy~=2.4` and `regex~=2026.5`, with torch as an extra.

---

## Narrative split & Limitations scope (DOC-02)

### Sub-decision: extend v1.0 artifacts or create new ones

| Option | Description | Selected |
|--------|-------------|----------|
| Extend both, v1.0 sections byte-unchanged | One report and one notebook front to back; m1-demo-v1 tag already preserves v1.0 | |
| New REPORT-M2.md and a second notebook | v1.0 artifacts literally as-is; reader must open both; v2.0 doesn't visibly build on v1.0 | |
| Extend REPORT.md, new notebook | Splits by artifact type: continuity for the report, isolation for the runnable notebook | ✓ |

**User's choice:** option 3.
**Notes (amendment):** the REPORT.md extension keeps every v1.0 section textually untouched (per
the "honest results stand unamended" principle) with a dated Milestone 2 boundary marker inside.
The new v2.0 notebook must be **self-contained and runnable independently** of the v1.0 notebook —
no shared cell state, no implicit checkpoint dependency inherited from the M1 file — so a reader
can run either standalone without the other's artifacts present. Both notebooks must state this
independence explicitly in their opening cells, so a reader isn't left to discover it by hitting a
failure. → **D-13**

### Sub-decision: does v2.0 follow REPORT.md's `## Decision:` form

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — v2.0 gets its own Decision sections | D-XX records map directly; one consistent artifact | |
| No — results-first narrative for v2.0 | Fits measured outcomes better; organizing principle changes halfway | |
| Hybrid — Decision sections plus a results narrative | Most complete; longest; risks saying each thing twice | ✓ |

**User's choice:** option 3.
**Notes (amendment):** the two sections must have **non-overlapping** content, not the same
information restated in two registers. Decision sections document the CHOICE and its rationale at
lock time (what, why, against what alternative), one per major D-XX already on record, same form
as the existing 15. The results narrative documents the OUTCOME across the three experiments (§8's
negative verdict, the A/B's numbers, the recall gate's pass/fail) as a single story — what was
tested, what the evidence showed, what remains uncertain — and never re-explains why a choice was
made. Stated test: a reader must be able to skip the Decision sections and still follow the
results narrative as a complete story, and skip the results narrative and still find each choice
justified in its own section. Two audiences with different intent (auditing a specific choice vs
understanding what the milestone proved), not the same reader twice. → **D-14**

### Sub-decision: Limitations — aggregate or cite

| Option | Description | Selected |
|--------|-------------|----------|
| Aggregate all eight, each quoting + linking its source | Self-contained; quoting prevents drift into a softer paraphrase | ✓ |
| Cite — short section pointing to each phase report | Zero duplication; turns the most important section into a table of contents | |
| Aggregate the headline-bounding ones, cite the rest | Proportionate; "which bounds a headline" becomes an editorial call under pressure | |

**User's choice:** option 1.
**Notes (amendment):** each of the eight entries must quote the source report's **exact wording** —
not summarized, not softened, not reordered for flow — and link to the specific section/line, the
same discipline as citing SHAs for pre-registration. Long entries **truncate visibly** (ellipsis +
link to the full passage) rather than paraphrase to shorten, because "paraphrase-to-shorten is
exactly the drift vector this amendment exists to close." The eight must be **ordered by which
claim they bound**, not by severity or by how comfortable they are to read, so the ordering itself
doesn't editorialize about which negatives matter more. → **D-15**

### Sub-decision: how much README carries

| Option | Description | Selected |
|--------|-------------|----------|
| Numbers with their caveats inline, v1.0 pattern | Front page is where a claim is most likely read without context | ✓ |
| Thin README, numbers live in REPORT.md | Single source of truth; abandons the v1.0 pattern | |
| One headline number, rest in REPORT.md | Keeps README short; choosing the single number is itself a framing decision | |

**User's choice:** option 1.
**Notes (amendment):** **three** headline numbers, not two — recall rate against its gate,
retention delta from the A/B, **and the Phase 11 token inflation tax carried forward**. Each gets
its qualifier in the same sentence or bullet, at the same density as the existing 547-live-ids
line — not a number followed by a separate "see Limitations" pointer. If a headline number carries
one of the eight aggregated limitations, that limitation's short form belongs inline in README
too, with the full quoted version still in Limitations: README = terse form, Limitations = full
form, the same asymmetry-of-detail principle already locked for the figure disclosure. → **D-16**

---

## Residuals — verdict placement & VIZ-02 disclosure

Offered as items that would otherwise fall to Claude's Discretion. The user elected to decide both.

| Option | Description | Selected |
|--------|-------------|----------|
| Where the correlation verdict is recorded | Own results/ report vs appended to phase13_ab_report.md vs REPORT.md only | ✓ |
| Whether VIZ-02 gets the outlier-naming discipline too | Single-panel, so the shared-scale argument doesn't reach it | ✓ |
| Neither — write CONTEXT.md now | Both land inside conventions already locked | |

**User's choice:** both.
**Notes (item 1):** the correlation verdict — pre-registration table, seed, sign+CI result, miss
policy if it misses — lands as a **new section appended to `phase13_ab_report.md`**, immediately
adjacent to the Fisher/delta data it's computed from. REPORT.md cites the verdict with the same
terse-form/full-form asymmetry already locked for the README numbers: a sentence stating pass/fail
and the correlation value, linking to the full pre-registration table, not restating it. → **D-17**

**Notes (item 2):** VIZ-02's caption/report text names the specific layer/projection driving its
color range whenever that range is dominated by an outlier cell, same wording pattern as VIZ-03's
disclosure, pointing at the same committed per-layer artifact. No new data collection — the
artifact already carries adapter ΔW per layer per projection. → **D-18**

**Orchestrator addition (not separately asked):** appending to `phase13_ab_report.md` touches
committed Phase 13 evidence, so CONTEXT.md records the constraint that the new section must be
explicitly dated and marked as Phase 15 material, visibly separate from Phase 13's pre-registered
content — the same separation Phase 14 D-12 requires between a verdict and anything written after
it. This follows directly from a precedent the user applied consistently throughout and was
encoded rather than re-asked.

---

## Claude's Discretion

- JSON schema field names and nesting for the norms artifact (required *content* is fixed by D-06)
- Permutation and bootstrap resample counts for D-12
- Plot styling — colormap, figure dimensions, panel arrangement, font sizes, PNG vs additional SVG
- File and script naming/placement, following the `plot_phase13.py` + `results/phase13_*.png`
  register
- Notebook cell ordering and count; exact section titles within REPORT.md
- Whether the extraction script also emits a human-readable markdown table alongside the JSON
- The exact source line each of D-15's eight limitations is quoted from (the *policy* is locked)

## Deferred Ideas

None — discussion stayed within phase scope.

**Considered and rejected**, recorded so neither is revived as an oversight:
- A **three-way verdict tier** for the correlation (Demonstrated / Suggestive / Not demonstrated,
  only the last counting as a miss) — rejected for D-11's binary gate. "Suggestive but not
  statistically demonstrated" survives as reporting language for a miss, not a third passing state.
- A **shared color scale across VIZ-02 and VIZ-03** — rejected in D-03; it would assert an
  adapter-vs-full-fine-tune comparison the phase has not justified.
