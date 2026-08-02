---
phase: 15
slug: figures-writeup
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-02
---

# Phase 15 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register origin: **authored at plan time**. All eight `15-0N-PLAN.md` files carry a
`<threat_model>` block. This audit **verifies each declared mitigation exists in the
implementation** — it does not rebuild the register and does not scan for new threats.

---

## Trust Boundaries

Union of the eight plans' declared boundaries.

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| `checkpoints/*.pt` → `torch.load` | Pickle deserialization; four of six checkpoints need `weights_only=False` and execute pickle opcodes on load | Model/optimizer/RNG state, ~914 MB, gitignored, project-owned |
| filesystem → `phase15_stats.load_pairs` | `results/phase15_norms.json` parsed as structured input; a malformed artifact must not yield a plausible verdict | 4 blocks × 36 float cells + provenance |
| `results/phase15_norms.json` → `plot_phase15` | Structured input parsed into figure geometry; a malformed artifact must abort, not render a partial panel | Same artifact |
| extraction output → every downstream consumer | The artifact is the sole source of truth for both figures, the correlation verdict and the report's per-layer numbers | ~180 aggregate scalars |
| plotting tier → checkpoint tier | The D-07 structural boundary; crossing it voids the regenerability proof | none (must stay none) |
| git history → the pre-registration claim | "The rule predates the number" is only as strong as commit ordering | commit DAG |
| Phase 13 committed evidence → a Phase 15 append | A prior phase's recorded results must not be blended into, amended or reopened | markdown |
| committed evidence reports → prose (REPORT / README / notebook) | Transcription is where a recorded negative can be quietly softened; the source files are the authority | quoted text + headline numbers |
| v1.0 text → v2.0 extension | D-13 makes pre-boundary text immutable; an edit above the marker is a silent rewrite of shipped evidence | `docs/REPORT.md:1-421`, `demo.ipynb` cells |
| committed `results/` artifacts → notebook cells | The notebook re-cites; recomputation would create a second, unaudited source of truth | PNGs + JSON |

---

## Threat Register

27 entries: T-15-01 … T-15-26 plus T-15-SC. All verified. **0 open.**

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-15-01 | Tampering | Wrong-checkpoint extraction producing a plausible wrong figure | mitigate | `require_fingerprint` raises `SystemExit` on adapter/`convbase_best.pt` mismatch — `scripts/extract_deltas.py:149-166,285`; `load_fisher(..., expected_fingerprint=best_fp)` independently RAISES — `extract_deltas.py:299`, `src/personacore/checkpoint.py:295+` | closed |
| T-15-02 | Repudiation | `plot_phase15.py` silently reading a checkpoint | mitigate | `test_plotting_module_never_opens_a_checkpoint` — AST import walk + `.pt`-literal scan + fresh-interpreter subprocess probe: `tests/test_phase15_plots.py:291-352`. Passes | closed |
| T-15-03 | Elevation of Privilege | `torch.load(weights_only=False)` on four checkpoints | mitigate | Paths are hardcoded `_REPO_ROOT`-relative constants, never `argv`/env — `scripts/extract_deltas.py:66-73,145`. SECURITY docstring paragraph at `extract_deltas.py:39-48`. Adapter + Fisher route through `weights_only=True` choke points (`:284,299`) | closed |
| T-15-04 | Tampering | A committed PNG no longer matching the committed JSON | mitigate | `test_plot_functions_write_pngs` tmp_path smoke — `tests/test_phase15_plots.py:209-219`. **Audit re-ran regeneration**: both PNGs regenerated from the committed artifact are SHA-256-identical to `results/phase15_adapter_delta.png` (`9b474dbb141a96b5…`) and `results/phase15_fisher_ewc.png` (`228ce09f0c340f6e…`) | closed |
| T-15-05 | Tampering | A limitation paraphrased, softened, truncated invisibly or reordered | mitigate | `test_limitations_quotes_are_verbatim` — `tests/test_phase15_docs.py:255-330`: 9-quote count meta-guard (:264), anchored section read (:267-274), per-quote normalized equality (:289), in-order ellipsis-fragment walk (:300), claim-group ordering (:324-330). Passes | closed |
| T-15-06 | Denial of Service | matplotlib requiring a GUI backend in headless CI | mitigate | `matplotlib.use("Agg")` at `scripts/plot_phase15.py:45`, **before** the pyplot import at `:47`, reason in the comment at `:43-44`; only `savefig` at `:233,293`, zero `show()` calls repo-wide in this module | closed |
| T-15-07 | Tampering | Malformed/truncated artifact yielding a partial correlation or a partial figure | mitigate | Stats side: `load_pairs` validates 4 blocks × 36 cells + per-layer projection set, `raise SystemExit` naming the offender — `scripts/phase15_stats.py:240-284`; `_cell` raises on non-numeric/non-finite — `:287-300` (orchestrator injected NaN → `SystemExit: block fisher cell (layer 0, q_proj) is nan, not finite`). Plot side: `_load_artifact` same structural validation — `scripts/plot_phase15.py:75-116`. See Residual Observation R1 | closed |
| T-15-08 | Repudiation | Commit ordering of the pre-registration | mitigate | `0e1af98` touched **only** `scripts/phase15_stats.py` (+209, no artifact, no `main()`); `git cat-file -e 0e1af98:results/phase15_norms.json` → **absent**; same at `90d1bce`. `90d1bce` is a strict ancestor of `d1e9eee` (extraction) and `f68450a` (the artifact) | closed |
| T-15-09 | Tampering | The gate resolved / re-seeded after seeing the number | mitigate | Both branches authored at `90d1bce` — `GATE PASSES` `scripts/phase15_stats.py:403`, `GATE MISSES` `:413`, before the artifact existed. R5 CI-is-load-bearing arbitration is a committed literal already at `0e1af98:91-97`, now `phase15_stats.py:104-113` + `_R5_SENTENCE:305-309`. `git diff --stat 90d1bce HEAD -- scripts/phase15_stats.py` → **empty**; worktree clean | closed |
| T-15-10 | Tampering | Mixed `.weight` / `.bias` cells across blocks | mitigate | `KEYS` is an explicit `(layer, projection)` product over a literal `_PROJ_PATHS` map, `.weight` only — `scripts/extract_deltas.py:85-102`. All three cell builders iterate `KEYS` (`:182,193,202`). No `isinstance`/`startswith`/`endswith` key selection anywhere in the module (the only `isinstance` is a variant type check at `:419`). Artifact confirms 36 cells per block, 4 blocks | closed |
| T-15-11 | Information Disclosure | Committing checkpoint contents into a tracked file | **accept** | Verified: `results/phase15_norms.json` is 11,497 bytes / **180 numeric scalars**, all aggregates (`cells`, `vmax_driver`, `param_count`, `nonpositive_cells`) plus fingerprints. No weights, no tensors. Accepted Risks Log entry ACC-15-01 | closed |
| T-15-12 | Tampering | A panel independently rescaled to look "equally busy" | mitigate | `test_ab_panels_share_one_norm` asserts `naive_norm is ewc_norm` by object identity — `tests/test_phase15_plots.py:245-247`; `test_shared_range_is_full_data_range` asserts exact extrema with two `>`/`<` teeth assertions against a 5/95 clip — `:254-272`. `plot_fisher_ewc` obtains norms from `_norms` at `scripts/plot_phase15.py:246` and passes them to `imshow` untouched at `:256-257` | closed |
| T-15-13 | Tampering | The Phase 15 append blending into or displacing Phase 13's results | mitigate | `test_verdict_section_is_dated_and_separated` — `tests/test_phase15_docs.py:525-577`: Phase 15 marker (:552), `YYYY-MM-DD` (:553), does-not-reopen-or-amend (:556), addendum is the last `## ` heading (:568), all six Phase 13 headings survive (:573). Passes | closed |
| T-15-14 | Repudiation | A guard reading `## Verdict` by substring and clobbering this evidence | mitigate | `_anchored_section` anchors `^<heading>` → next `^## ` or `\Z` — `tests/test_phase15_docs.py:95-108`, matching `scripts/_verdict.py:24 VERDICT_SECTION`'s shape. CR-02 cited at `test_phase15_docs.py:98-104,530-539` and in the renderer docstring `scripts/phase15_stats.py:329-335`. `grep -c 'split("## Verdict")'` across all `.py` → **0** | closed |
| T-15-15 | Tampering | A v1.0 report section silently edited under cover of the v2.0 extension | mitigate | **Audit re-ran**: `head -421 docs/REPORT.md` is byte-identical (`cmp` clean) to `head -421` of `git show 225a962:docs/REPORT.md` (the last pre-Phase-15 revision). `git diff --numstat 225a962 HEAD -- docs/REPORT.md` → **549 insertions, 0 deletions** — a pure append/insert, no line rewritten anywhere in the file | closed |
| T-15-16 | Repudiation | The L8 tokenizer-corpus correction asserted without evidence | mitigate | `docs/REPORT.md:984-986` names `scripts/train_tokenizer.py:31`, `tests/fixtures/tiny_corpus.txt`, **11,469 bytes**; `README.md:74-75` states the corrected attribution directly. **Audit re-confirmed the byte count independently**: `wc -c tests/fixtures/tiny_corpus.txt` → `11469`. Permanent: `tests/test_phase15_docs.py:320-321` (evidence tokens after L8) and `:405-407` (wrong phrase absent from README, corrected tokens present) | closed |
| T-15-17 | Tampering | Quoting +224.81% without its WR-01 correction block | mitigate | `docs/REPORT.md:935-941` carries the recorded `+224.81%`, names the correction block's source **and line range** (`results/phase14_calibration_report.md:289-307`, `WR-01`) and the `+224.5330%` re-measurement. **Audit verified the cited range**: the `CORRECTION (WR-01…)` blockquote starts at `phase14_calibration_report.md:289` and ends at `:307`; `+224.5330%` is at `:299` | closed |
| T-15-18 | Tampering | A headline number presented without its qualifier | mitigate | `test_headline_numbers_match_sources` asserts exactly one bullet carries each number and that bullet also carries its qualifier keyphrases — `tests/test_phase15_docs.py:387-395` — and that the bare pointer is absent (`assert "see Limitations" not in readme`, `:400`). Inline density confirmed by reading `README.md:14-42` and `:57-61`: every headline number's bound sits in the same bullet/sentence; report links are additive. See Residual Observation R3 | closed |
| T-15-19 | Tampering | A README number drifting from its source report | mitigate | `test_headline_numbers_match_sources:384-386` asserts each number also appears in its cited source. ρ is stronger: `test_correlation_rho_matches_the_artifact_it_was_computed_from` **recomputes** ρ from the committed artifact through the frozen rule and requires all four prose sites to carry it — `tests/test_phase15_docs.py:451-504`. Passes | closed |
| T-15-20 | Tampering | An existing `demo.ipynb` cell silently modified or re-executed | mitigate | **Audit re-ran the byte-level diff** against `git show ff4c7f4:demo.ipynb` (the last pre-Phase-15 revision): `nb['cells'][1:] == old['cells']` → **True**; `metadata` equal → **True**; `nbformat`/`nbformat_minor` equal → **True**; 8 → 9 cells, the single addition is a markdown cell at index 0 | closed |
| T-15-21 | Tampering | A ROADMAP success criterion quietly reinterpreted | mitigate | `.planning/ROADMAP.md:255-267` — "**ROADMAP wording superseded (SC3, recorded 2026-08-02)**", with the original SC3 text preserved unmodified directly above it at `:252`, and the closing sentence naming why the substitution is recorded rather than absorbed. SC2's gate-passed outcome is recorded the same way at `:268-275` — recorded in the ROADMAP itself, stronger than the SUMMARY-only requirement | closed |
| T-15-22 | Tampering | The v2.0 notebook recomputing a headline number | mitigate | **Audit re-ran the code-cell scan**: 0 occurrences of `checkpoints/` and 0 of `.pt` in `demo_v2.ipynb`'s code-cell `source` arrays; 0 `import torch`. Its only reads are `results/phase13_forgetting_curve.png`, `results/phase15_adapter_delta.png`, `results/phase15_fisher_ewc.png`, `results/phase15_norms.json` — all git-tracked. Numeric sweep re-run: 29 decimal literals in the markdown cells, **0 orphans** against the seven cited sources | closed |
| T-15-23 | Denial of Service | The v2.0 notebook failing on a fresh clone | mitigate | **Audit re-executed the notebook end-to-end from a fresh kernel**: `jupyter nbconvert --to notebook --execute demo_v2.ipynb` → **exit 0**, 395,960 bytes written, no cell error. All four inputs confirmed git-tracked. Independence statements present in both notebooks' cell 0 (`demo.ipynb` cell 0: "runs standalone… requires nothing from `demo_v2.ipynb`"; `demo_v2.ipynb` cell 0 states the reciprocal) | closed |
| T-15-24 | Tampering | Figure caption and report disagreeing about the vmax driver; SC3's variant unnamed | mitigate | `test_report_names_the_artifact_vmax_driver` — `tests/test_phase15_docs.py:587-634`: section-anchored on `### The Two Signature Figures` (:604) with a mandatory non-empty meta-guard (:609-610), asserts each block's driver phrase (:618), driver value (:622), `nonpositive_cells` count (:626) and `blocks.fisher.variant` verbatim (:634), all read **from the artifact**. Passes | closed |
| T-15-25 | Tampering | A dangling cross-document anchor into the report's Limitations section | mitigate | `test_headline_numbers_match_sources:409-416` derives the GitHub anchor from the heading **as actually written** in `docs/REPORT.md` and asserts the resulting link appears in both `README.md` and `demo_v2.ipynb`. Passes | closed |
| T-15-26 | Tampering | The verbatim rule weakened at wave 5 to make the blockquote register satisfiable | mitigate | The helper pinned in `15-05-PLAN.md` `<verbatim_normalization>` is **byte-identical** to the implementation body at `tests/test_phase15_docs.py:78-79` (two `re.sub` calls + `.strip()`). No case fold, no punctuation stripping, no ellipsis handling, no smart-quote folding. Docstring at `:70-76` names any added substitution a **VIOLATION**, not a refinement. Referenced identically by 15-05 Task 3 and 15-08 Task 1 | closed |
| T-15-SC | Tampering | npm/pip/cargo installs | **accept** | Verified: `git log 0e1af98^..HEAD -- pyproject.toml requirements.txt` → **empty**. No non-planning file outside `README.md`, `demo*.ipynb`, `docs/REPORT.md`, `results/*`, `scripts/*phase15*|extract_deltas`, `tests/test_phase15_*` was touched. Every third-party import in the phase's new code is already-declared: `numpy`, `matplotlib`, `torch`, `pytest`. No `scipy`. Accepted Risks Log entry ACC-15-02 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| ACC-15-01 | T-15-11 | `results/phase15_norms.json` is committed to a public repo. It carries **only** aggregate norms, parameter counts, and provenance fingerprints — audit-measured at 11,497 bytes / 180 numeric scalars, zero tensors. This is the *intended* disclosure: D-05 exists precisely so a reviewer can check a number without the 914 MB of gitignored checkpoints. | Phase 15 plan `15-02-PLAN.md` `<threat_model>` | 2026-08-02 |
| ACC-15-02 | T-15-SC | The phase installs **zero** packages, so no supply-chain legitimacy checkpoint applies. Audit-confirmed: neither `pyproject.toml` nor `requirements.txt` was touched anywhere in the phase's commit range, and every third-party import is a pre-existing declared dependency. Reaching for a package here (notably `scipy` for the correlation) would itself be the drift signal — D-12 mandates the ~40-line pure-numpy rank machinery instead. | Phase 15 plans (all eight) `<threat_model>` | 2026-08-02 |

---

## Unregistered Flags

**None.** Every `## Threat Flags` section in `15-02` … `15-08-SUMMARY.md` reports "None", and each
maps its plan's threat IDs back to the register. No new attack surface was declared during
implementation, and the audit found no touched file outside the register's declared boundaries.

*Informational:* `15-01-SUMMARY.md` carries no `## Threat Flags` section at all (its threat
coverage is stated inline at line 37). Documentation shape only — its four threats (T-15-07,
T-15-08, T-15-09, T-15-SC) are all verified closed above.

---

## Residual Observations

Not declared-mitigation gaps — none of these is in scope of any threat's stated mitigation text.
Recorded so a future phase inherits them explicitly rather than by discovery.

**R1 — plotting-side validation is structural, not value-domain.** T-15-07's *declared* plot-side
mitigation is "validates four blocks × 36 cells and each layer's projection set", and that is
exactly what `scripts/plot_phase15.py:89-114` does. It does **not** check the value domain. Audit
probe, one tampered `naive` cell:

| injected cell | outcome |
|---|---|
| `-inf`, `0.0`, `-1.0`, string `"0.5"` | `_load_artifact` passes; a plausible PNG renders, no error |
| `nan`, `+inf` | `ValueError: Invalid vmin or vmax` — names neither the file nor the block |

The stats side is stricter (`_cell` raises a named `SystemExit` on non-finite, `phase15_stats.py:296-299`).
Two compensating controls limit exposure: `NORMS_JSON` is a hardcoded constant (no `argv`, no env),
and `test_artifact_schema` asserts `math.isfinite` on every committed cell
(`tests/test_phase15_plots.py:138`) — so a non-finite value cannot survive in the committed
artifact without CI going red. Closing this fully would mean routing `_load_artifact` through a
`phase15_stats._cell`-shaped finiteness check.

**R2 — arm identity is not provable from the extraction code alone.** `_load_model`
(`scripts/extract_deltas.py:136-146`) reads a checkpoint's `["model"]` and its provenance trio but
never asserts which arm the file is, though `phase13_ewc_latest.pt` carries `ewc_lambda`/
`theta_star`/`fisher` and `phase13_naive_latest.pt` carries none. Transposing the `NAIVE_LATEST`/
`EWC_LATEST` constants inverts `naive - ewc` and flips ρ to `-0.801544`. This is outside T-15-01's
declared scope (the shared W₀ `best.pt` **is** validated every run via `load_fisher`'s raising
fingerprint check). It is now caught downstream by
`test_correlation_rho_matches_the_artifact_it_was_computed_from`
(`tests/test_phase15_docs.py:451-504`), which recomputes ρ and derives the expected verdict word.

**R3 — permanent enforcement of headline numbers is partial.** `_HEADLINE_NUMBERS`
(`tests/test_phase15_docs.py:340-359`) pins 3 of README's ~8 headline figures; ρ is pinned
separately and more strongly. The remaining figures (`13,891,584`, `2.1066`, `~100 tok/s`,
`1.129×`, `+0.380556`) carry their inline qualifiers as written — audit-confirmed by reading
`README.md:14-42` — but rest on the plan's one-time grep, not on a test.

**R4 — four mitigations are one-time acceptance criteria with no regression test.** T-15-04
(PNG↔JSON byte identity), T-15-15 (the 421-line v1.0 prefix), T-15-20 (`demo.ipynb` cell
equality) and T-15-23 (fresh-kernel execution) are verified by command, not by pytest. **This
audit independently re-ran all four and all four hold today** (evidence in the register rows), but
a future edit breaking any of them would not turn anything red.

**R5 — no negative-path test coverage.** `grep -c "pytest.raises\|SystemExit\|ValueError"` returns
**0** across all three Phase 15 test modules, against **27** explicit fail-loud guards
(`phase15_stats.py` 9, `plot_phase15.py` 8, `extract_deltas.py` 10). Every guard's *existence* is
verified by code reading and two were exercised by hand during this audit (the orchestrator's NaN
injection into `load_pairs`; this audit's six-value probe of `_load_artifact`), but none is
protected against a future edit that weakens it into a warning or a silent default.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-02 | 27 | 27 | 0 | gsd-security-auditor |

Baseline at audit time: `.venv/bin/python -m pytest -q` → **408 passed, 1 skipped** (the skip is
the pre-existing CUDA gate at `tests/test_train_loop.py:81`). Phase 15 modules alone: 16 passed.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-02
