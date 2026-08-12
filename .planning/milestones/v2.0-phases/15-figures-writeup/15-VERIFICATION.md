---
phase: 15-figures-writeup
verified: 2026-08-02T21:17:31Z
status: passed
score: 51/51 must-haves verified
overrides_applied: 0
re_verification:
  re_verified: 2026-08-12
  previous_status: human_needed
  previous_score: 51/51 must-haves verified
  note: "Re-stamp only — the machine score was already 51/51 at initial verification and NO code, figure or REPORT.md change was made. The two human_verification items below were the only thing holding status at human_needed; both were presented and PASSED on 2026-08-12, recorded in 15-HUMAN-UAT.md (status: complete, 2 passed / 0 pending / 0 gaps)."
human_verification_results:
  closed: 2026-08-12
  outcome: "2 of 2 PASSED, 0 gaps opened"
  results:
    - result: PASSED
      note: "GitHub inline legibility. The why_human prediction — 'roughly 3pt equivalent' from the 0.391 downscale — did NOT reproduce, because it reasoned from nominal point size rather than rendered pixel density: the PNG is drawn at high DPI, so an 880px render still carries enough pixels, and Retina renders at 2x. Corroborated before the human was asked by a Lanczos resample of phase15_fisher_ewc.png to 880x293, which reproduced the VIZ-03 disclosure line legibly. Human confirmed both lines readable in place on rendered GitHub. No figsize/fontsize bump, no regeneration."
    - result: PASSED
      note: "Two-halves narrative independence. Both line ranges were read end to end before the question was put. The results half (664-831) carries its own framing; its :671 cross-reference is an explicit pointer, not a dependency, and the :829-831 forward reference points at Limitations, a third section. The Decisions half (490-663) is complete on its own terms. One borderline spot was surfaced rather than silently passed: :594-597 names Phase 12's lambda-sweep verdict and the later production lambda=0.01 choice without stating what the verdict said (that lives at :673-682); judged acceptable because the decision being argued is the rule — never edit a recorded verdict in place — which stands without the verdict's content. No docs/REPORT.md change."
human_verification:
  - test: "Open README.md on GitHub (rendered, not raw) at default desktop width and read the two embedded v2.0 figures without clicking through to full size. Specifically read the gray disclosure line at the bottom of each."
    expected: "Both disclosure lines are legible in-place: VIZ-03's `the naive and EWC panels share ONE log scale ... the Fisher panel has its own because its units differ` and VIZ-02's `... so this figure is NOT comparable to the VIZ-03 delta panels`."
    why_human: "results/phase15_fisher_ewc.png is 2250x750; GitHub's ~880px content column downscales it to 0.391, rendering the 8pt disclosure text at roughly 3pt equivalent. D-04's stated purpose is that the PNG cannot be misread when it travels alone. Whether that survives GitHub's inline downscale is a rendering/perception question that cannot be answered from the filesystem. (VIZ-02 downscales to 0.772, ~6.2pt — likely fine.) If VIZ-03's line is unreadable inline, the fix is a figsize/fontsize bump, not a claim change."
  - test: "Read docs/REPORT.md lines 664-831 (`## Milestone 2 Results` through `### What Remains Uncertain`) end to end WITHOUT reading any `## Decision:` section. Then read the seven v2.0 `## Decision:` sections (lines 490-663) WITHOUT reading the results narrative."
    expected: "Each half reads as a complete story on its own; neither is a summary of the other and neither leaves a dangling forward reference the reader must resolve in the other half."
    why_human: "15-05's must-have is a reading-experience property. The structural precondition is verified (the two halves are disjoint line ranges, and the report asserts the property at lines 486-488), but 'follows as a complete story' is prose judgment that no grep can settle."
---

# Phase 15: Figures & Writeup Verification Report

**Phase Goal:** The v2.0 narrative ships with the milestone's signature figures and honest numbers, in the same register as the v1.0 547-live-ids disclosure
**Verified:** 2026-08-02T21:17:31Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

The phase's deliverable is that a scientific claim is **honestly measured and honestly reported**. I attacked that on four fronts rather than reading SUMMARY.md: (1) git-history proof that the pre-registration boundary held, (2) independent recomputation of every published number from the committed artifact, (3) byte-level regeneration of both figures and of the extraction artifact, and (4) **six deliberate falsification mutations** against the doc-integrity tests to prove they go red on paraphrase-to-soften. All four hold.

### Observable Truths — ROADMAP Success Criteria

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | Weight-delta heatmap `‖ΔW‖_F/‖W₀‖_F` on the layer×six-projection grid, log color scale, committed | VERIFIED | `results/phase15_adapter_delta.png` (1140×840) committed and git-tracked. Read the image directly: 6 layer rows × 6 named projection columns (`q_proj`…`fc_out`), `LogNorm` colorbar labeled `‖ΔW‖_F/‖W₀‖_F (log scale)`. Regenerated from `results/phase15_norms.json` alone → SHA256 `9b474dbb…` identical to committed. |
| SC2 | Three-panel figure juxtaposing Fisher with naive-vs-EWC deltas, showing EWC dodging high-Fisher coordinates | VERIFIED | `results/phase15_fisher_ewc.png` (2250×750) committed. Read the image directly: naive Δ, EWC Δ (same scale), Fisher diagonal (own scale). The EWC panel is visibly darkest in the `v_proj`/`c_proj` columns where the Fisher panel is brightest. Regenerated → SHA256 `228ce09f…` identical. Mechanically: recomputed ρ = **0.801544**, 95% CI **[0.597984, 0.920291]**, gate → `True`. |
| SC3 (as superseded by D-13) | REPORT.md + README carry the v2.0 narrative; honest numbers, named Fisher variant, real Limitations section ship in `demo_v2.ipynb` | VERIFIED | `docs/REPORT.md` +549/−0 (pure insert). `README.md` reframed as shipped M2. `demo_v2.ipynb` executes standalone. All three honest-number categories present. Fisher variant `empirical_diag_fisher/groundtruth_targets/mean_normalized` read from the artifact at runtime (demo_v2 cell 8) and asserted by test. Nine limitations at `docs/REPORT.md:833`. **Supersession is recorded in ROADMAP.md, not silently absorbed** — verified in the Phase 15 section text. |

### Observable Truths — Plan 15-01 (pre-registration)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Rule, seed, predicted sign and gate committed BEFORE any correlation number exists | VERIFIED | `git show --stat 0e1af98` = **one file, 209 lines, `scripts/phase15_stats.py` only**. `git grep` at that tree finds no correlation number. `git ls-tree 0e1af98 results/` → `phase15_norms.json` absent. First appearance of `0.801544` in history is `0e8b890` (15-04), 41 minutes later. Constants present at `0e1af98`: `N_CELLS=36`, `PREDICTED_SIGN=1`, `PAIRING`, `SEED=1337`, `N_PERM`, `N_BOOT`, `CI_ALPHA`, `def ewc_dodges_high_fisher`. |
| 2 | Spearman ρ uses average (tie-corrected) ranks and matches the canonical value exactly | VERIFIED | `test_spearman_known_answers` asserts `spearman([1,1,2,3],[1,2,3,4]) == 0.9486832980505139 ± 1e-12` and the Wikipedia IQ/TV `-0.17575757575757575 ± 1e-15`; `_rank([1,1,2,3]) == [0.5,0.5,2.0,3.0]`. |
| 3 | Same seed → byte-identical permutation p and bootstrap CI across two calls | VERIFIED | `test_seeded_results_are_reproducible` asserts `==` on both, plus a different-seed `!=` meta-guard. Independently: my out-of-band recomputation reproduced the committed p and CI to all six published digits. |
| 4 | The gate returns MISS for a positive ρ whose CI spans zero | VERIFIED | `test_gate_rule`: `ewc_dodges_high_fisher(0.15, -0.1, 0.4) is False`; boundary `ci_lo == 0.0` → `False`. |
| 5 | The verdict renderer exists and produces its markdown before it has ever seen real data | VERIFIED | `render_verdict_section` landed at `90d1bce` (15:59:48) with **both** `GATE PASSES` and `GATE MISSES` branches; artifact first committed at `f68450a` (16:11:51). |

### Observable Truths — Plan 15-02 (extraction artifact)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Adapter ratio computed against `convbase_best.pt`; fingerprint mismatch aborts | VERIFIED | `extract_deltas.py:285` `require_fingerprint(adapter_art, convbase_fp)` → explicit `raise SystemExit`, never `assert`. Artifact records `blocks.adapter.w0_source = "checkpoints/convbase_best.pt"`. |
| 2 | Committed JSON carries four blocks of exactly 36 cells each, from an explicit (layer, projection) product | VERIFIED | Parsed the artifact: adapter/naive/ewc/fisher = 36 cells each, `n_layer=6` × 6 projections. `prove()` re-checks before write. |
| 3 | Every block — including fisher — carries regime, param_count, training_budget | VERIFIED | All four blocks carry all three fields (fisher: `fisher_diagonal_estimate` / 13,891,584 / `"no training — one estimation pass of 2000 examples…"`). |
| 4 | The fisher block names the exact estimator variant string, not the coarse regime | VERIFIED | `blocks.fisher.variant = "empirical_diag_fisher/groundtruth_targets/mean_normalized"`, distinct from `regime`. `prove()` fails loud if it is absent or empty. |
| 5 | Top level carries a machine-readable comparison-basis note | VERIFIED | `comparison_basis = {naive_vs_ewc: true, adapter_vs_full_finetune: false, note: <three named confounds>}`. |
| 6 | Re-running extraction reproduces the committed JSON byte-for-byte | VERIFIED (independently re-run) | I ran `extract_deltas.main()` into scratch against the six real local checkpoints: **`diff` clean modulo the two top-level run-provenance fields**. `_normalize_run_provenance` blanks only top-level `git_sha`/`built` — the nested `base_fingerprint`/`w0_fingerprint`/`anchor_fingerprint` audit trail is compared byte-for-byte. |

### Observable Truths — Plan 15-03 (figures)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | VIZ-02 heatmap on layer × six-projection grid with log color scale, committed | VERIFIED | See SC1. |
| 2 | VIZ-03 three-panel figure committed | VERIFIED | See SC2. |
| 3 | Naive and EWC use ONE norm object, proven by `is` identity through `_norms()`; Fisher's differs on a units argument | VERIFIED | `_norms()` returns `(shared, shared, fisher)`. `test_ab_panels_share_one_norm` asserts `naive_norm is ewc_norm` and `fisher_norm is not naive_norm`, then re-renders the figure through those exact norms so the helper cannot drift from what is drawn. |
| 4 | Shared range is the full data range — vmax the largest cell across both arms, vmin the smallest nonzero | VERIFIED | Recomputed: shared bounds `(0.04211054267645148, 0.22023983403635128)`; shared min is an EWC cell, shared max a naive cell. `test_shared_range_is_full_data_range` also asserts the true extrema sit strictly outside a 5%/95% clip, so a percentile-clipped implementation cannot pass. |
| 5 | Plotting module has no code path that opens a `.pt` file, proven by AST and fresh-interpreter import | VERIFIED | `test_plotting_module_never_opens_a_checkpoint` (AST walk + subprocess). Independently confirmed: after executing both plot functions in a fresh interpreter, `'torch' in sys.modules` → `False`. |
| 6 | Each figure names the layer/projection driving its color range, read from the artifact | VERIFIED | `_driver()` reads `block["vmax_driver"]`. VIZ-02 caption renders `layer 1 / c_proj`; VIZ-03 renders `layer 1 / c_proj` (max of the two arms' recorded drivers). `test_vmax_driver_matches_argmax` proves each recorded driver IS that block's argmax of the grid the figure draws. |

### Observable Truths — Plan 15-04 (the verdict)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Correlation computed with the pre-registered seed/constants; the number appears nowhere earlier | VERIFIED | Recomputed from the committed artifact: ρ=0.801544, p=0.000010, CI=[0.597984, 0.920291], 0 degenerate resamples — **all six digits match the recorded verdict**. `git log -S"0.801544"` first hit is `0e8b890`. |
| 2 | The verdict is recorded **unamended**, adjacent to the Phase 13 data | VERIFIED (strongest evidence in the phase) | I re-rendered `render_verdict_section(...)` and compared to the committed tail of `results/phase13_ab_report.md`: **byte-identical**. Further, `scripts/phase15_stats.py` is **byte-frozen since `90d1bce`** (`git diff 90d1bce HEAD -- scripts/phase15_stats.py` empty; no commits touch it in that range) — the file that authored both verdict branches has not moved since before the artifact existed. |
| 3 | The appended section is explicitly dated, Phase-15-marked, visibly separate | VERIFIED | `## Phase 15 Addendum — Fisher/Δ Correlation Verdict`, HTML separation comment, `**Recorded: 2026-08-02**`. `test_verdict_section_is_dated_and_separated` uses a **section-anchored** read (not `split("## Verdict")[-1]`, which would land in this addendum's own prose) and asserts it is the last `## ` heading. |
| 4 | A gate miss would be reported in the "suggestive but not statistically demonstrated at n = 36" register, neither discarded nor softened | VERIFIED (branch dormant, wording locked) | The `GATE MISSES` branch text was committed at `90d1bce`, before the number existed, and is byte-frozen. The test asserts exactly one of PASSES/MISSES is present and, if MISSES, that the pre-registered register string appears. The gate PASSED, so the branch is dormant by design — but it could not have been softened after the fact. |
| 5 | Every pre-existing Phase 13 heading and its text is byte-unchanged | VERIFIED | `git diff --numstat 39a59a7 HEAD -- results/phase13_ab_report.md` → **57 insertions, 0 deletions**. Pure append. Test additionally pins all six Phase 13 headings still present. |

### Observable Truths — Plan 15-05 (docs/REPORT.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every v1.0 section is textually untouched | VERIFIED | `git diff --numstat 39a59a7 HEAD -- docs/REPORT.md` → **549 insertions, 0 deletions**; two insert-only hunks (`@@ -421,0 +422,20 @@`, `@@ -456,0 +477,529 @@`). Zero `^-` lines in the diff. |
| 2 | Dated M2 boundary marker before any stale future-tense v1.0 text a front-to-back reader hits | VERIFIED | `## Milestone 1 Ends Here — Everything Below This Line Is As Written on 2026-06-10` at line 424, immediately before `## Limitations and the Milestone 2 Roadmap` (line 442) whose "Milestone 2 (upcoming)" bullets are the stale text. The marker names both overtaken clauses explicitly. |
| 3 | Decision sections and results narrative each readable alone | VERIFIED (structure) / see human item 2 | Disjoint ranges: Decisions 490-663, Results 664-831. The report states the property at 486-488. Prose judgment routed to human. |
| 4 | Limitations carries NINE honest negatives, each reproducing its source's exact wording, ordered by which claim they bound | VERIFIED (falsified) | Nine entries L1–L9 across four `### Bounding "…"` groups. `test_limitations_quotes_are_verbatim` checks each against its cited source under a whitespace/blockquote-only normalization, walks `…` fragments with an advancing cursor (so a reordered truncation fails), asserts count == 9, and asserts group ordering. **Falsification M1:** softening L2's `is not unambiguous evidence` → `is not strong evidence` turns the test **RED**. |
| 5 | L8's known-wrong source wording is quoted verbatim then followed by a dated, evidence-naming correction note | VERIFIED | L8 quotes the wrong `"the bounded TinyStories corpus"` attribution verbatim, then `**CORRECTION (Phase 15, recorded 2026-08-02 — the quoted v1.0 text above is NOT amended).**` I re-verified its cited evidence myself: `scripts/train_tokenizer.py:31` sets `CORPUS_PATH = .../tests/fixtures/tiny_corpus.txt`; that fixture is **11,469 bytes**; `artifacts/tokenizer.json` is **5,648 bytes**. Both exact. |
| 6 | Figures' non-comparability and vmax drivers stated at full detail under `### The Two Signature Figures` | VERIFIED | Section at 723-803: units argument for the Fisher panel, three named confounds for VIZ-02-vs-VIZ-03, the four-row vmax-driver table, `nonpositive_cells = 0` for all four blocks. `test_report_names_the_artifact_vmax_driver` reads it **section-anchored** and asserts each layer/projection phrase and each driver value against the artifact. **Falsification M6:** mutating a `vmax_driver` value in the artifact turns the test **RED**. |
| 7 | Report names the Fisher estimator by its exact variant string, verbatim from the artifact | VERIFIED | Line 796 carries `empirical_diag_fisher/groundtruth_targets/mean_normalized`, asserted inside the anchored section against `blocks.fisher.variant`. |

### Observable Truths — Plan 15-06 (README.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | README presents PersonaCore as a shipped Milestone 2 | VERIFIED | Lines 4-7 "**Milestone 2 demonstrates that claim rather than promising it**"; `## Milestone 2 — what shipped` at 162; M1 framed as foundation, not superseded draft. |
| 2 | Three headline numbers each carry their qualifier in the same sentence/bullet | VERIFIED (falsified) | `0.3483` + "proper-noun core" + "reversed phrasings"; `8.52417066884246` + "teacher-forced" + "noise floor"; `3.229` + "same-run baseline". `test_headline_numbers_match_sources` splits README on bullets and requires the qualifier inside the same bullet. **Falsification M2:** changing `reversed phrasings` → `other phrasings` turns it **RED**. **M3:** `0.3483` → `0.4483` turns it **RED**. |
| 3 | No headline number is followed by a bare "see Limitations" pointer | VERIFIED (falsified) | `assert "see Limitations" not in readme`. **Falsification M4:** replacing an inline qualifier with `see Limitations` turns it **RED**. |
| 4 | Tokenizer bullet states the corrected training-corpus attribution directly | VERIFIED | Lines 72-79 name `tests/fixtures/tiny_corpus.txt`, `11,469`-byte, `scripts/train_tokenizer.py:31`, and "not on the full TinyStories corpus". Test asserts `"bounded TinyStories corpus" not in normalize_quote(readme)`. |
| 5 | Both v2.0 figures appear on the front page | VERIFIED | `results/phase15_fisher_ewc.png` (line 54) and `results/phase15_adapter_delta.png` (line 64), each with an italic caption restating the scale/comparability rule. |

### Observable Truths — Plan 15-07 (notebooks)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | New v2.0 notebook runs standalone from a fresh clone without the v1.0 notebook's artifacts | VERIFIED (executed) | I executed all three code cells of `demo_v2.ipynb` in a fresh interpreter at repo root: all OK. Its only imports are `json` and `IPython.display`; its only file reads are `results/phase13_forgetting_curve.png`, `results/phase15_adapter_delta.png`, `results/phase15_fisher_ewc.png`, `results/phase15_norms.json` — **all four git-tracked**. Zero `torch`, zero `.pt`, zero `checkpoints/`. |
| 2 | Both notebooks state mutual independence in their opening cells | VERIFIED | `demo.ipynb` cell 0: "**This is the Milestone 1 evidence notebook, and it runs standalone.** It requires nothing from `demo_v2.ipynb` and shares no cell state with it". Reciprocal statement in `demo_v2.ipynb`. |
| 3 | The v1.0 notebook's existing cells are byte-unchanged — the statement is a PREPENDED new cell | VERIFIED | Parsed both revisions: old 8 cells → new 9 cells, and `new['cells'][1:] == old['cells']` → `True`. `git diff --numstat` → **15 insertions, 0 deletions**. |
| 4 | The v2.0 notebook re-cites committed numbers and never recomputes them | VERIFIED | No arithmetic in any cell; cell 8 reads the artifact and prints its fields. Markdown carries the string `re-cited, never recomputed`. |
| 5 | All three DOC-02 honest-number categories appear | VERIFIED | `0.3483`, `8.52417066884246`, `3.229` (and `1.129`) all present in markdown. |
| 6 | The notebook names the Fisher variant, read from the artifact | VERIFIED | Cell 8: `print(f"Fisher variant    : {fisher['variant']}")` — read at runtime, not retyped. |
| 7 | ROADMAP records the SC3 supersession rather than silently absorbing it | VERIFIED | ROADMAP Phase 15 section carries an explicit **"ROADMAP wording superseded (SC3, recorded 2026-08-02)"** block naming D-13, what moved to `demo_v2.ipynb`, and why the substitution is recorded rather than absorbed. A separate **"SC2 (recorded 2026-08-02): not narrowed — the gate PASSED"** note records the un-taken D-11 miss branch as an outcome, not an omission. |

### Observable Truths — Plan 15-08 (doc-integrity tests)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every Limitations quote proven verbatim, so paraphrase-to-soften becomes a test failure | VERIFIED (falsified — M1) | See 15-05 truth 4. The normalization strips only `>` markers and collapses whitespace; its docstring pins that adding case-folding, punctuation-stripping or ellipsis handling would be a violation, not a refinement. |
| 2 | Every README headline number proven to match its cited source report | VERIFIED (falsified — M3) | Each number asserted present in README **and** in its cited source file, with exactly one carrying bullet. |
| 3 | Verdict section proven dated, Phase-15-marked, positioned after every pre-existing Phase 13 heading | VERIFIED (falsified — M5) | Removing the `YYYY-MM-DD` date from the addendum turns `test_verdict_section_is_dated_and_separated` **RED**. |
| 4 | vmax driver named in the report matches the artifact field the figure reads, asserted inside an anchored `### The Two Signature Figures` read | VERIFIED (falsified — M6) | The section-anchored regex plus a mandatory non-empty meta-guard (a heading rename fails loudly instead of passing vacuously on `""`). |
| 5 | Report names the Fisher variant string carried in the artifact | VERIFIED | `assert variant in body` inside the anchored section. |
| 6 | README's and demo_v2.ipynb's links into the Limitations section resolve to a heading that exists | VERIFIED | The anchor is **derived** from the heading as written via `_github_anchor()`, never retyped, then asserted present in both files. `## Milestone 2 Limitations — Nine Honest Negatives, Quoted` exists at `docs/REPORT.md:833`; the anchor appears 3× in README, 1× in demo_v2.ipynb. |
| 7 | Full suite green with no regression | VERIFIED | `.venv/bin/python -m pytest -q` → **407 passed, 1 skipped, 0 failed in 117.11s**. Matches the stated entry state exactly; the 1 skip is the pre-existing CUDA gate at `tests/test_train_loop.py:81`. 15-08-SUMMARY honestly self-corrects the plan's stale "392-test baseline" to the real 403. |

**Score:** 51/51 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase15_stats.py` | Pre-registered rule + pure-numpy rank stats + gate + verdict renderer | VERIFIED | 459 lines (≥180). `PRE-REGISTRATION` block present. Pure `numpy` — no scipy, no torch. Byte-frozen since `90d1bce`. |
| `tests/test_phase15_stats.py` | Known-answer, determinism, behavior, gate tests | VERIFIED | 4 tests, all substantive (canonical-value assertions, `==` determinism with a different-seed meta-guard, boundary gate case). |
| `scripts/extract_deltas.py` | Only new code permitted to open a `.pt` | VERIFIED | 444 lines (≥200). `SECURITY:` paragraph present. `prove()` runs before the write; every failure is `raise SystemExit`, never a strippable `assert`. |
| `results/phase15_norms.json` | The committed hand-off boundary | VERIFIED + regenerated | `comparison_basis` present. Independently re-extracted → identical modulo top-level run provenance. |
| `tests/test_phase15_plots.py` | Schema test + gated reproduction test + figure contracts | VERIFIED | 7 tests, ≥90 lines. The reproduction test genuinely **ran** here (0.67s, checkpoints present), not skipped. |
| `scripts/plot_phase15.py` | Artifact-only figure generation | VERIFIED | 305 lines (≥160). Exports `plot_adapter_delta`, `plot_fisher_ewc`, `_norms`. |
| `results/phase15_adapter_delta.png` | VIZ-02 | VERIFIED + byte-reproduced | 1140×840, SHA256 `9b474dbb…` reproduced from artifact alone. |
| `results/phase15_fisher_ewc.png` | VIZ-03 | VERIFIED + byte-reproduced | 2250×750, SHA256 `228ce09f…` reproduced from artifact alone. |
| `results/phase13_ab_report.md` | Phase 13 evidence + dated Phase 15 addendum | VERIFIED | +57/−0. Addendum byte-identical to a fresh render. |
| `docs/REPORT.md` | v1.0 + M2 boundary marker, Decision sections, results narrative, nine limitations | VERIFIED | +549/−0. |
| `README.md` | v2.0 front door, three inline-qualified headline numbers | VERIFIED | Contains `0.3483`; both figures embedded. |
| `demo_v2.ipynb` | Self-contained M2 evidence notebook | VERIFIED + executed | 11 cells; contains `re-cited, never recomputed`; runs standalone. |
| `demo.ipynb` | v1.0 + prepended independence cell, originals untouched | VERIFIED | +15/−0; `cells[1:]` byte-identical to pre-phase revision. |
| `.planning/ROADMAP.md` | Phase 15 entry with recorded SC3 supersession | VERIFIED | Supersession block + SC2 not-narrowed note both present. |
| `tests/test_phase15_docs.py` | D-15/D-16/D-17 policy-as-structure | VERIFIED | 545 lines (≥140). All four tests falsified green→red under deliberate mutation. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tests/test_phase15_stats.py` | `scripts/phase15_stats.py` | `spec_from_file_location` | WIRED | Present; 4 tests execute against the loaded module. |
| `scripts/extract_deltas.py` | `checkpoints/convbase_best.pt` | `require_fingerprint` + `raise SystemExit` | WIRED | Line 285; the error text explicitly forbids "switch W₀ to best.pt to make this pass". |
| `tests/test_phase15_plots.py` | `results/phase15_norms.json` | `json.loads` of the committed artifact | WIRED | `_artifact()` helper, used by 4 tests. |
| `scripts/plot_phase15.py` | `results/phase15_norms.json` | `json.load` — the ONLY input | WIRED | Confirmed by regeneration with `torch` absent from `sys.modules`. |
| `tests/test_phase15_plots.py` | `scripts/plot_phase15.py` | AST walk + fresh-interpreter subprocess import | WIRED | `test_plotting_module_never_opens_a_checkpoint`. |
| `results/phase13_ab_report.md` | `scripts/phase15_stats.py` | Evidence Index addendum row citing `0e1af98` | WIRED | Rendered row present; the cited SHA resolves and contains the locked constants. |
| `results/phase13_ab_report.md` | `results/phase15_norms.json` | cited by `git_sha` | WIRED | `@ git_sha d1e9eee2…` matches the artifact's recorded field. |
| `docs/REPORT.md` | `results/phase13_ab_report.md` | terse citation of the verdict → full pre-registration table | WIRED | Line 812-813 cites the addendum by heading and declines to restate it. |
| `docs/REPORT.md` | `results/phase15_norms.json` | vmax-driver table / per-layer disclosure | WIRED | Test-asserted against the live artifact. |
| `README.md` | `docs/REPORT.md#…limitations…` | derived GitHub anchor | WIRED | Anchor computed from the heading, asserted in both README and demo_v2.ipynb. |
| `README.md` | `results/phase15_fisher_ewc.png` | embedded figure | WIRED | Both figures embedded. |
| `demo_v2.ipynb` | `results/phase15_norms.json` | runtime read | WIRED | Cell 8 executes and prints artifact fields. |
| `tests/test_phase15_docs.py` | `docs/REPORT.md` / `scripts/_verdict.py` shape / `results/phase15_norms.json` | normalized exact-wording + anchored section reads | WIRED | Anchored regex reused from `_verdict.py`'s shape; never a `split(heading)[-1]`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `results/phase15_adapter_delta.png` | `grid` from `_grid(artifact,"adapter")` | `results/phase15_norms.json` ← 6 real checkpoints | Yes — 36 distinct fp64 values, vmax `0.04738638857364279` | FLOWING |
| `results/phase15_fisher_ewc.png` | naive/ewc/fisher grids | same artifact | Yes — 108 distinct values across three blocks | FLOWING |
| `results/phase13_ab_report.md` addendum | `rho, p, ci_lo, ci_hi` | `load_pairs(artifact)` → 36 real pairs | Yes — recomputation reproduces all six published digits | FLOWING |
| `docs/REPORT.md` figures section | driver layer/projection/value, `nonpositive_cells`, `variant` | artifact fields, test-bound | Yes | FLOWING |
| `README.md` headline bullets | three numbers | `phase14_recall_report.md`, `phase13_ab_report.md`, `inflation_report.md`, test-bound | Yes | FLOWING |
| `demo_v2.ipynb` | `norms` dict | artifact, read at runtime | Yes — executed, printed 4×36 real cells | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| The published ρ/CI/p are reproducible from the committed artifact | `load_pairs` + `permutation_p` + `bootstrap_ci` at the pre-registered seed | `rho=0.801544 p=0.000010 ci=[0.597984, 0.920291] degen=0`, `gate=True` | PASS |
| The committed verdict text was not hand-edited | re-render `render_verdict_section(...)` and compare to the report tail | `rendered section found verbatim in report: True` | PASS |
| Both figures regenerate from the artifact alone | `plot_adapter_delta` + `plot_fisher_ewc` into scratch, then `shasum -a256` | Both SHA256s identical to committed; `torch in sys.modules: False` | PASS |
| The artifact reproduces from the six checkpoints | `extract_deltas.main(scratch)` then `diff` | `IDENTICAL (modulo provenance)` | PASS |
| `demo_v2.ipynb` runs standalone | exec all code cells in a fresh interpreter | all cells OK; only committed files touched | PASS |
| Report's derived figure statistics are true | recompute 62.7%, 40.9%, 34/36, decade spans, signed reductions | 0.6269, 34/36, 0.719/0.400/2.129 decades, −0.015185/−0.006607 — all exact; 40.9% matches the upper-middle median convention (see W-4) | PASS |
| README's "EWC moved further in 2 of 36 cells" | recompute `naive − ewc < 0` | `2` — `(0,q_proj)`, `(1,q_proj)` | PASS |
| L8's correction evidence | read `train_tokenizer.py:31`; `wc -c` both files | `CORPUS_PATH = .../tiny_corpus.txt`; 11,469 and 5,648 bytes | PASS |
| Full suite regression | `.venv/bin/python -m pytest -q` | 407 passed, 1 skipped, 0 failed | PASS |

### Falsification Probes (doc-integrity tests must fail on paraphrase-to-soften)

Run against an isolated copy of the doc tree in scratch — **no repository file was modified**.

| # | Mutation | Target test | Result |
|---|----------|-------------|--------|
| baseline | none | all four | 4 passed |
| M1 | Soften L2: `is not unambiguous evidence` → `is not strong evidence` | `test_limitations_quotes_are_verbatim` | **FAILED (correct)** |
| M2 | Drop a qualifier: `reversed phrasings` → `other phrasings` | `test_headline_numbers_match_sources` | **FAILED (correct)** |
| M3 | Drift a headline number: `0.3483` → `0.4483` | `test_headline_numbers_match_sources` | **FAILED (correct)** |
| M4 | Replace an inline qualifier with a bare `see Limitations` pointer | `test_headline_numbers_match_sources` | **FAILED (correct)** |
| M5 | Un-date the Phase 15 addendum | `test_verdict_section_is_dated_and_separated` | **FAILED (correct)** |
| M6 | Change a `vmax_driver` value in the artifact | `test_report_names_the_artifact_vmax_driver` | **FAILED (correct)** |
| restore | revert all | all four | 4 passed |

The honesty machinery is real, not declarative. Paraphrase-to-soften, number drift, qualifier loss, bare-pointer outsourcing, un-dating, and figure/report divergence each turn a test red.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VIZ-02 | 15-02, 15-03, 15-08 | Weight-delta heatmap on layer×module grid (six named projections), log color scale, committed | SATISFIED | `results/phase15_adapter_delta.png` committed, byte-reproducible, visually confirmed. |
| VIZ-03 | 15-01, 15-02, 15-03, 15-04, 15-08 | Fisher heatmap juxtaposed with naive-vs-EWC delta heatmaps, EWC visibly dodging high-Fisher coordinates | SATISFIED | `results/phase15_fisher_ewc.png` committed + visually confirmed; the dodging claim is measured under a pre-registered gate (ρ=0.801544, CI excludes zero) rather than asserted. |
| DOC-02 | 15-05, 15-06, 15-07, 15-08 | REPORT.md + README v2.0 narrative and honest numbers in the same register as the v1.0 547-live-ids disclosure | SATISFIED | All three honest-number categories present with inline qualifiers; nine verbatim-quoted limitations; L8 carries the 547-live-ids passage forward with a dated correction. Register is preserved, not just referenced. |

No ORPHANED requirements: `.planning/REQUIREMENTS.md` maps exactly VIZ-02, VIZ-03 and DOC-02 to Phase 15, and all three are claimed by plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` | — | **None found** in any of the six new/modified source files. Debt-marker gate clean. |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` / "not yet implemented" | — | **None found**. |

Two deferred items are logged in `.planning/phases/15-figures-writeup/deferred-items.md` with root cause and correct fix (DEF-15-01 `make lint` ruff resolution — and the log correctly *retracts* its own earlier suggested fix as CI-breaking; DEF-15-02 a cosmetic `~914 MB` docstring figure that `docs/REPORT.md` deliberately frames as an *attribution* rather than a direct claim). Neither touches a published number.

---

## Warnings (non-blocking — no must-have fails)

**W-1 — The phase's own signature number is the one number in the repo not bound by a test.**
ρ = 0.801544 / CI [0.597984, 0.920291] / p = 0.000010 are restated in `README.md:59`, `docs/REPORT.md:809`, `demo_v2.ipynb:381` and `.planning/ROADMAP.md:270`. I verified all five sites agree with each other and with my recomputation, exactly. But `_HEADLINE_NUMBERS` in `test_phase15_docs.py` covers only the three D-16 numbers, and README's ρ lives in a paragraph rather than a bullet, so the bullet-split check does not reach it. **A future paraphrase-to-soften of ρ — the number this phase exists to produce — would not go red**, while doing the same to `0.3483` would. This is not a must-have failure (D-16 scopes to three numbers, and the fixture documents its scope) but it is the one hole in an otherwise closed net. Cheapest fix: one more `_HEADLINE_NUMBERS` row for `0.801544` against `results/phase13_ab_report.md`.

**W-2 (= CR-01, confirmed latent).** `phase15_stats._rank` sorts NaN as largest, so `spearman` returns a finite value on NaN input instead of NaN. The main path is guarded: `load_pairs::_cell` rejects any non-finite cell with `raise SystemExit` before the statistic sees it, and `extract_deltas.prove()` rejects non-finite cells before the artifact is written. All 144 committed cells are finite. **The published ρ is unaffected.** Fails open rather than loud on a corrupted artifact reaching `spearman()` directly.

**W-3 (= CR-02, confirmed latent).** `require_fingerprint` is applied to the adapter block only. The naive/ewc blocks record `source_ckpt.fingerprint` and `w0_fingerprint` as an audit trail but assert nothing. Partial mitigation exists and is real: `load_fisher(FISHER_CACHE, expected_fingerprint=best_fp)` **raises** on anchor mismatch, so `best.pt` — the shared W₀ for both arms — is transitively validated on every run. Extraction reproduced byte-identically here, so **the committed deltas are correct.**

**W-4 — Derived figure statistics in the report are unguarded prose.** `62.7%`, `40.9%`, `34 of 36`, and the decade spans at `docs/REPORT.md:749-774` are not covered by `test_report_names_the_artifact_vmax_driver` (which pins only `vmax_driver`, `nonpositive_cells` and `variant`). I recomputed all of them: every one checks out. One nuance worth recording — `40.9%` is `sorted(ewc)[18]/sorted(naive)[18]` (the upper-middle element, a real cell, consistent with the phrase "its **median cell**"); `np.median(ewc)/np.median(naive)` gives `40.4%`. A reader recomputing with numpy's default will see a 0.5-point difference. Defensible as written; a parenthetical naming the convention would remove the ambiguity.

---

## Human Verification Required

### 1. GitHub inline legibility of the two v2.0 figures

**Test:** Open `README.md` on GitHub (rendered, not raw) at default desktop width. Read the gray disclosure line at the bottom of each embedded figure *without* clicking through to full size.
**Expected:** Both disclosure lines are legible in place — VIZ-03's "the naive and EWC panels share ONE log scale … the Fisher panel has its own because its units differ", and VIZ-02's "… so this figure is NOT comparable to the VIZ-03 delta panels".
**Why human:** `results/phase15_fisher_ewc.png` is 2250×750; GitHub's ~880px content column downscales it by 0.391, rendering 8pt text at roughly 3pt equivalent. D-04's whole purpose is that the PNG cannot be misread when it travels alone — whether that survives inline downscale is a rendering/perception question the filesystem cannot answer. (VIZ-02 downscales by 0.772, ~6.2pt equivalent — likely fine.) If VIZ-03's line is unreadable inline, the fix is a `figsize`/`fontsize` bump and a figure regeneration, not a claim change.

### 2. Two-halves narrative independence in `docs/REPORT.md`

**Test:** Read lines 664-831 (`## Milestone 2 Results` through `### What Remains Uncertain`) end to end without reading any `## Decision:` section. Then read the seven v2.0 `## Decision:` sections (lines 490-663) without the results narrative.
**Expected:** Each half reads as a complete story; neither is the other's summary and neither leaves a forward reference the reader must resolve in the other half.
**Why human:** 15-05's must-have is a reading-experience property. The structural precondition is verified — the halves are disjoint line ranges and the report asserts the property at lines 486-488 — but "follows as a complete story" is prose judgment no grep can settle.

---

## Gaps Summary

**No gaps.** Every must-have resolves VERIFIED, and the four checks that mattered most were run independently rather than read from SUMMARY.md:

1. **The pre-registration boundary held, provably.** `scripts/phase15_stats.py` landed alone at `0e1af98` (15:56) with the statistic, the seed, the predicted sign `+1`, the resample counts and the gate as committed literals. Both verdict branches followed at `90d1bce` (15:59). The artifact did not exist at either commit. The number first appeared at `0e8b890` (16:37). And the module is **byte-frozen across that entire window to HEAD** — the words for "GATE MISSES" were locked before anyone knew they would go unused. This is the strongest form of the claim available in git.

2. **The verdict is recorded unamended.** The committed addendum is byte-identical to a fresh `render_verdict_section(...)` today, and `results/phase13_ab_report.md` took +57/−0 — a pure append that displaced nothing of Phase 13's recorded evidence.

3. **The figures say what the docs say.** Both PNGs regenerate byte-identically from the committed artifact with `torch` never entering `sys.modules`, and I read both images: VIZ-02 is the layer×six-projection log-scale delta grid; VIZ-03's EWC panel is visibly darkest in the `v_proj`/`c_proj` columns where the Fisher panel is brightest. The report's derived statistics about those images (62.7%, 34-of-36, decade spans, the two cells where EWC moved *further*) all recompute exactly.

4. **The honesty claims are enforced, not declared.** Six deliberate mutations — softening a limitation, dropping a qualifier, drifting a number, outsourcing a caveat to a link, un-dating the addendum, and diverging the report from the artifact — each turned a doc-integrity test red, and the restored tree went green again.

The one thing the phase does not yet protect is ρ itself (W-1). Everything published about it is correct today and correctly derived; it is simply the number whose prose restatement no test binds. Worth one fixture row before the milestone closes, but it does not block Phase 15.

---

_Verified: 2026-08-02T21:17:31Z_
_Verifier: Claude (gsd-verifier)_
