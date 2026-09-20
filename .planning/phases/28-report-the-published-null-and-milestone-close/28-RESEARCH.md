# Phase 28: Report, the Published Null, and Milestone Close - Research

**Researched:** 2026-09-20
**Domain:** Repo-internal — generated report prose from committed JSON records, byte-identity re-render tests, git-ancestry tests, a disposition ledger, milestone-close mechanics (stdlib only: `json`, `hashlib`, `string`, `re`, `tomllib`, `subprocess`)
**Confidence:** HIGH — every path, symbol, line number, hash and count below was read from disk or from `git` in this session; nothing is from training data. No web research was needed or performed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Thirty-nine decisions across four areas. Every one is LOCKED** — researcher and planner act on
them rather than re-open them. Every measured figure below was read from the artifact named beside
it during this discussion.

#### Area A — What the report publishes, and where (RPT-01, SC1, SC4)

- **D-01: ONE appended section in `docs/REPORT.md`, results + limitations, same file.** Order: null
  → adversarial confound → canary → relearning MOOT → self-corrections → ship block →
  named-limitation register → v5.0 block. Build decisions (privacy unit, vmap per-example clipping,
  fact-aligned sampler, pre-registration-as-phase-zero) get **one pointer each** to their phase
  records and modules — never their own narrative section. Reason, quoted from the v3.0 re-audit:
  dense correction prose is the measured mechanism that produces miscounts.

- **D-02: The lead is the gate's own output, then the mechanism.** Line 1 carries
  `verdicts.capacity_branch` (`null-at-both-capacities`) and BOTH `verdicts.arm_existentials`
  strings verbatim with their denominators (dp: "0 of 32 point(s) examined returned PASS";
  adversarial: "0 of 6"). Line 2 is bound to `results/phase27_admission.json::cleared_counts`:
  30 of 30 noised DP points cleared (a), 0 cleared (b). The Phase 18 section's order — the verdict
  is quoted, never paraphrased around.

- **D-03: The n=64 caveat sits immediately after the lead, not in a subsection.** `dp_n64`'s own
  σ=0 control learned taught recall **87/1008 (0.08630952380952381)**, held-out 35/648, against
  `dp_n8`'s **790/1008 (0.7837301587301587)** — so the n=64 branch of "null at both capacities" is
  read against a control that barely learned. The recorded `L=64 → 9σ` expectation (the reason n=64
  exists) is quoted beside it. A skimmer must not be able to take the headline without the caveat.

- **D-04: The standing expectation is quoted verbatim from `.planning/research/SUMMARY.md` at
  commit `c673b4c`** — 72σ noise-to-signal at L=8, σ ≥ 15.3 for ε_fact ≤ 4, Secret Sharer Table 3 as
  precedent (`SUMMARY.md:39-41`, restated at `:388-396`). `.planning/REQUIREMENTS.md` (`e144417`)
  and `.planning/ROADMAP.md` (`3c80037`) carry the same text and are cited as its milestone-level
  restatements.

- **D-05: "Recorded before any run" becomes a CPU test, not a citation.** Three conjuncts:
  (i) the quoted sentences are present in the file **at `c673b4c`** (`git show`), compared under
  `_prose.normalized`; (ii) `c673b4c` is a strict ancestor of the earliest first-add across
  `results/phase2[0-8]_*`, **derived from git at test time**, never a hardcoded pair (measured
  today: `9bb34ad`, `results/phase20_retention_floor.json`, 2026-08-20 19:37 vs `c673b4c` at 09:27,
  `git merge-base --is-ancestor` true); (iii) refuses on a shallow clone with the Phase 26/27
  message. CI already checks out with `fetch-depth: 0` (`.github/workflows/ci.yml:28`).

- **D-06: σ ≥ 15.3 is published three ways in one row — quote, bracket, reproduce.** The recorded
  quote (D-04); the record bracket from the committed grid (σ=12 → ε `5.299979064701441`;
  σ=16 → ε `3.7965357228934966`); and `personacore.privacy.accountant.sigma_for(4.0, steps, delta)`
  = **15.289937507119**, called at render time with `composed_steps` (200) and `delta` (1e-5) read
  from the frontier itself. The renderer also asserts `epsilon_for(16.0, steps, delta)` re-derives
  the record's ε bit-identically — a committed prediction checked by committed code on committed
  inputs, never a number typed into prose.

- **D-07: ε is published ONE ROW PER σ, each beside its `dp_n8` canary verdict and reasons.** The
  Phase 26 continuation forbids quoting any ε without its canary verdict, and the canary audited
  only the 16 `dp_n8` points (`audited_point_keys`), because only n=8 has an out-of-corpus canary
  population (`CANARY_RESERVATIONS.canary_population_rule`). ε per σ is bit-identical at both legs,
  so each row states that n=64 shares the accountant value and is **structurally unauditable**. The
  curve total `2387.299119573244` is published beside the canary summary carrying the record's own
  sentence — "context only, never the comparator" — together with D-40's LIMITATION 2
  (`epsilon_report.control_has_no_epsilon`). No ε appears anywhere without a verdict beside it.

- **D-08: SC4's confound is quoted from the records only, never re-derived.** Sources:
  `verdicts.adversarial_no_replay` (`code_source`, `finding`, `log_line`, `log_source`,
  `dp_replay_source`, `note`), `results/phase25_operational_note.md` §12.5c, and
  `verdicts.amended_criterion` (`D-25-18-ADV64-REFUSED`).

- **D-09: SC4's wording is corrected against the records in two places, and the report states what
  the records state.** (i) Replay windows are **32 at n=8 and 256 at n=64**
  (`adversarial_no_replay.dp_replay_source`); SC4's bare "32 replay windows per step" is the n=8
  figure only. (ii) The 6 `adv_n64` points were **REFUSED before any condition was applied**
  (`early_return_reason`: "REFUSED by the sanctioned route before the pin was reached"), so
  condition (c) was never applied to them although their readings were measured and are out of band
  (dialogue on 16.1357–18.0440, retention 5.8835–6.6174); the 6 `adv_n8` points read INCONCLUSIVE
  with (c) failing on both the dialogue band and the retention cap. The refusal route's own
  disclosure travels with it verbatim: its cause (the arm's own ratio-0 control scored held-out
  **0/648**, so `Y_heldout = 0.7 × 0 = 0` is a criterion any reading clears), that condition (a)
  fails on all six regardless (3–66 of 416 > X), and that it was "Decided by the orchestrator
  2026-09-09; reversible in seconds by re-running this CPU pass".

- **D-10: `logs/phase25_sweep.out` is gitignored (`.gitignore:16`).** The `7,581 teaching + 0
  replay` line is quoted from the committed record's `log_line` / `log_source` fields and §12.5c —
  the log file is never read by the renderer or by a test.

- **D-11: README gets RENDERED `Results at a glance` bullets for v3.0 and v4.0**, inserted at the
  top of the existing list with **zero deletions**, produced by the same renderer and covered by the
  same byte-identity test as the report. This closes v3.0 cross-cutting debt item 4 (the skim
  surface still carries only v2.0/M1 numbers) by mechanism rather than by a one-off edit.

- **D-12: A short "what the milestone corrected about itself" block, fully bound.** The 23-12
  in-place retraction of the roadmap's `~1,010×` evaluation-cost premise with its measured
  replacement, and the σ=0 diagnostic halt (`4.15×` its floor in the BEATS direction, comparator as
  root cause) from `results/phase23_sigma_zero.json` / `results/phase23_cost.json`. Every number
  binds to a phase-23 record. A retraction is evidence that the process works, not debt.

- **D-13: The ship block is RENDERED from the ledger + records.** Its withheld-claims list is the
  `NAMED-LIMITATION` rows plus the existential fields, so it cannot drift from the ledger. It ships
  the published null and the from-scratch apparatus (DP-SGD, accountant, canary, relearning
  apparatus as CPU-tested code) and withholds any claim that a mitigation preserves weight-based
  memory, and any conclusion about adversarial ratio.

- **D-14: Both frontier figures are embedded** (`results/phase25_frontier_dp.png`,
  `results/phase25_frontier_adversarial.png`, committed at `6af3fa0`) with captions bound to record
  fields. **No byte-identity test on the PNGs** — matplotlib output is not stable across versions,
  and Phase 25 already guarantees the plotter loads no torch, names no checkpoint literal and opens
  only the frontier artifact (`tests/test_phase25_plots.py`).

- **D-15: The section closes with one rendered v5.0 block** — what the replay-bearing adversarial
  re-run would measure and what would change — bound to the ROADMAP v5.0 entry and the WR-05 ruling.

#### Area B — Generated, not authored (RPT-01, RPT-02, SC2)

- **D-16: A committed template with NAMED placeholders.** Each binding names either a record field
  path or a module constant; the renderer fills them. Prose is written around bindings; numbers are
  never typed.

- **D-17: Test 1 re-renders from the committed records and compares BYTE-FOR-BYTE** with the
  committed block in `docs/REPORT.md` and `README.md`.

- **D-18: Test 2 scans the TEMPLATE SOURCE, never the rendered output by value.** Value-matching is
  weak ("0" and "8" match almost anything); scanning the source catches the hand-typed number
  **before** rendering happens. A bare numeral outside the identifier grammar is RED.

- **D-19: The identifier grammar is STRICT.** Exempt: phase numbers, REQ-IDs (`RELRN-02`), decision
  IDs (`D-40`), dates, commit SHAs, section refs (`§12.5c`), citation years. Everything that is a
  quantity binds — including `n=8` / `n=64`, `K=48` and σ values that appear inside labels; those
  resolve from record keys and module constants.

- **D-20: FROZEN AT PUBLISH.** Once the section is committed, its block is pinned; corrections are
  **dated continuation blocks with their own bindings** (`scripts/_addendum.py::append_addendum`,
  both keywords required, one append per file), never a re-render over published prose. Re-render
  freely before the publishing commit, never after.

- **D-21: The renderer reads the committed records DIRECTLY — no derived extract, no caching.**
  Measured: `json.load` on the 22.3 MB frontier costs 0.056–0.063 s, sha256 0.011 s, and 10 test
  files already open it on every run, against a suite of roughly 23 minutes. Each rendered block
  carries the sha256 of every source record, following the existing provenance pattern.

- **D-22: Every cross-surface prose check routes through `scripts/_prose.py::normalized`**
  (SC2's third clause); byte-identity checks compare rendered bytes. Both, no conflict.

- **D-23: This phase's pre-registration ALREADY EXISTS and is not rewritten.**
  `phase25_prereg.PUBLICATION_OBLIGATION` (8 `(field_path, why)` pairs) and
  `phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION` (7 more) are the contract. A test resolves
  **every** field path against the assembled artifacts; an unresolvable path is RED and never a
  licence to paraphrase around it (`PUBLICATION_OBLIGATION_SCOPE`'s own words). Phase 28 sets no
  outcome threshold, so `results/phase28_ledger.json` needs **no new gate module and no new
  ancestry-guarded pre-registration** — the obligation modules, already frozen before any v4.0
  number, are it.

- **D-24: The section's date stamp is a pinned constant, never `today()`** — a clock in the
  template would break byte-identical re-render by construction.

#### Area C — RPT-03 and the debt ledger (RPT-03, SC3)

- **D-25: A new test makes the four-milestone claim mechanical.** Parse `[project].dependencies`
  from `git show v1.0:pyproject.toml`, `v2.0`, `v3.0` with stdlib `tomllib` and assert equality with
  HEAD. Measured identical at all four: `numpy~=2.4`, `regex~=2026.5`. "Zero new runtime
  dependencies" stops being a sentence and becomes a check.

- **D-26: The whole-file sha256 pin STAYS — as a change detector, not as RPT-03's proof.**
  `tests/test_package.py::test_pyproject_unchanged_since_v2_close` is renamed and its message
  corrected: the name asserts something now false, and a name that asserts something false does not
  survive.

- **D-27: SC3's sha256 clause is FALSE as written, and is published as a dated one-liner rather
  than as a finding.** Measured: `5065bc5` (2026-09-01, "fix: pin make demo to [cpu,demo] pip line
  and declare MIT in pyproject") added one line, `license = "MIT"`, and re-pinned
  `PYPROJECT_SHA256` from `81d07d5d…2bdf` to `15ffd6b5…926f` in the same commit. The whole diff
  against `v3.0` is that line; no dependency changed. The reviewed decision is not reverted and the
  substantive guarantee (D-25) holds.

- **D-28: ONE ledger — `results/phase28_ledger.json` — with a milestone column.** Rows carry
  `id`, `milestone`, `source` (file:line or artifact), `disposition`, `evidence` (commit, test node
  id, or file) and `reason`. It covers v3.0's 22 (16 tech-debt + 6 stale stamps) and v4.0's open
  items. SC3's "16 + 6" is a filtered view of it. Every count in prose derives from the data
  (`len()`), never typed — which is D-16's rule applied to the ledger.

- **D-29: A CLOSED disposition domain, and `FIXED` requires a test.** `FIXED` (commit + a test that
  catches regression) · `CLOSED-EARLIER` (commit that closed it, measured now) · `RE-DEFERRED`
  (reason + target) · `NAMED-LIMITATION` (published in the report) · `ACCEPTED` (deliberate, won't
  fix) · `FORBIDDEN-BY-GUARD` (a fix would redden an ancestry guard or rewrite published evidence;
  dated continuation only). A disposition recorded is never conflated with a fix.

- **D-30: The named-limitation register is the ledger filtered to `disposition ==
  NAMED-LIMITATION`,** rendered as its own block. One source, two renderings — the same discipline
  as D-28 on a second filter axis. Phase 27's ruling, D-40's two limitations and the canary's
  "could not have failed" disclosure each enter as a single row, never duplicated across two files
  that could diverge.

- **D-31: Archived planning artifacts — repair ONLY what makes a tool report an active error.**
  In scope: the missing frontmatter fields and the six stale artifact names that make
  `gsd-sdk query verify.artifacts` report existing files as missing. Out of scope: prose
  imperfections nothing consumes — `19-13-SUMMARY.md`'s stray `</content>` / `</invoke>` tags and
  the 17-digit `77.63701134639661%` variant — which are recorded, never edited. Same audit-trail
  protection v3.0 applied, closing only the real and active cost.

- **D-32: Safe-to-edit vs forbidden, as MEASURED this session.** Safe (no record `module_sha256`,
  no ancestry guard): `src/personacore/evaluation/perplexity.py:11-13` (the denominator docstring)
  and `scripts/phase16_persistence.py:1605` (the `PERSONA_ALLOWLIST` "exactly two entries"
  parenthetical) → `FIXED`, each with a test. Forbidden: `results/phase16_persistence_report.md`
  (I-1/I-2 citations), `results/phase18_extraction_report.md` (the W1 residual misattribution) and
  the four v3.0-frozen modules (`erasure_gate.py`, `phase17_personas.py`, `phase18_extraction.py`,
  `phase19_erasure.py`, guarded by `V3_ARTIFACT_GLOBS` in `tests/test_phase16_prereg.py`) →
  `FORBIDDEN-BY-GUARD`, dated continuation or record-only. The planner re-measures each item's
  guard status before assigning a disposition; this list is the pattern, not the census.

- **D-33: DEF-17-01 is `CLOSED-EARLIER` at `7b38e38`** (2026-08-30, "build: pin make test/lint to
  the venv interpreter"). Measured this session: `make lint` → "All checks passed! 284 files already
  formatted". The v3.0 audit's "confirmed still open" reading is stale, and the ledger says so with
  the commit.

#### Area D — Where milestone close ends

- **D-34: Phase 28 stops at report + ledger.** It ticks RPT-01 and RPT-03, updates the ROADMAP
  Phase 28 row and `STATE.md` **BY HAND** — snapshot `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md`
  before, diff all three after, **zero `gsd-sdk` mutation handlers** (Phase 26/27 posture; the
  handlers corrupted frontmatter and re-ticked 23-17 twice) — and writes the ledger. `PROJECT.md`,
  `MILESTONES.md` and the `v4.0` tag belong explicitly to `/gsd-complete-milestone`. A named
  boundary, not an overlapping one.

- **D-35: `23-VERIFICATION.md` and `27-VERIFICATION.md` KEEP `status: human_needed`.** The ledger
  names the ruling that discharged each (23's two same-day developer rulings; 27's two rulings in
  `27-HUMAN-UAT.md`). A verifier's verdict is never re-stamped — the v3.0 precedent for 17, 18 and
  19, whose own words are that the discharge record sits beside the verdict rather than over it.

- **D-36: `25-HUMAN-UAT.md`'s stamp moves `partial` → `complete`.** It records a workflow state
  (pending items), not a judgement: every item is resolved, including item 1 (RESOLVED 2026-09-09;
  run `34403612853` reported `8 failed, 2682 passed, 62 skipped` and the derived 62 was exactly
  right; the eight failures were fixed the same day). With zero pending items, `partial` is false by
  the field's own definition.

- **D-37: Phase 24's two open UAT items are disposed, not carried.** Item 2 (ADVT-02 wording):
  requirement text stays as ticked; a **dated traceability note** records the exact mechanism —
  filter at `scripts/phase24_adversarial.py:289-292`, `SystemExit` at `:300`, belt-and-braces behind
  the filter — confirming the property holds twice, as the original text already said. Requirement
  prose is never rewritten after the mechanism is known (Phase 27 D-05's discipline). Item 3 is
  `CLOSED-EARLIER` by measurement: `scripts/phase25_record.py:553` calls `score_refusal` and `:574`
  calls `clean_frame_probe_populations`, and every frontier point carries `refusal.by_family`
  counts — the instrument is consumed by a running pipeline.

- **D-38: A green CI run on `origin/main` containing Phase 27 and the report is a CLOSE
  PRECONDITION, and the push is a HUMAN CHECKPOINT the developer performs.** Measured: `main` is
  **27 commits ahead** of `origin/main` (origin's newest `8f43342`, 2026-09-13), so Phase 27's
  entire code surface has never run in CI; the last six CI runs on `main` are all `success`
  (newest 2026-09-14T12:55). Pushing is outward-facing and the orchestrator must not take it
  unasked — the 25-UAT precedent, where the first CI run over waves 10–13 found eight real defects
  invisible on the publication host. The run id lands in the ledger.

- **D-39: Stale workflow stamps that make `audit-open` misreport fall under D-31's rule** — the
  three quick-task SUMMARYs with no `status:` field (`260819-r1u`, `260819-sgh`, `260902-dlo`) and
  the debug session `draw-all-utf8-decode-crash` still stamped `fixing`. The planner verifies each
  one's work is genuinely complete and cites the commit before changing a stamp; anything that
  cannot be evidenced stays `RE-DEFERRED`.

### Claude's Discretion

- Renderer and template file layout and names (`scripts/phase28_report.py` + a template file is the
  expectation), marker naming, and whether a `make report` target exists.
- Which tables exist beyond those the obligations force, and their column order.
- The ledger's exact schema keys beyond D-28's required fields, and where the date-stamp constant
  lives.
- Test file naming, following `tests/test_phase26_*.py` / `tests/test_phase27_*.py`.
- Section title wording — with one constraint: it carries the branch name (`null-at-both-capacities`
  or its verbatim equivalent), not a phrase describing it.
- Plan and wave structure, and how the human checkpoints (D-38's push, the operator's ledger review)
  are sequenced.

### Folded Todos

- **`phase28-carry-phase27-latent-review-findings`** (developer ruling, 2026-09-16, recorded at
  Phase 27's human verification in `27-HUMAN-UAT.md`). **Folded in full, not left in Deferred**,
  because its provenance already names Phase 28 as owner:
  - **Ruling 1 — named limitations.** CR-01 (the D-18 attacker-corpus bin pin disables itself on
    row-level corpus drift), CR-02 (a leg passes `_require_admitted` with a tracked-but-edited
    record or an out-of-tree `--record`, trusting the record's admitted keys over the frontier),
    WR-02 (`structural-proof` exits 0 without every mitigated reading; records rather than refuses
    diverging offset streams), WR-03 (a live leg writes `run.csv` under `results/phase27_*`,
    matching `ARTIFACT_GLOB` and not gitignored), WR-06 (the required `baseline` never moves the
    verdict; a re-run of `gate` overwrites the published output), plus inconsequential WR-01 and
    WR-04. Each enters the ledger as a `NAMED-LIMITATION` row and is published via D-30.
  - **Obligations (a)–(f) on the first phase that reads ADMITTED** are carried verbatim into the
    register so a v5.0 phase inherits them: refuse unless both corpus pins hold; compare the
    record's bytes with HEAD and re-derive `admitted_point_keys` + `frontier_sha256` at leg time;
    require every expected arm reading and refuse on diverging streams; route run CSVs to the
    gitignored out-dir; pre-register one gate baseline per leg and refuse to overwrite a gate
    output; enforce Ruling 2 before any `adv_*` admission.
  - **Ruling 2 — WR-05.** No `adv_*` point is admissible until the v5.0 adversarial re-measurement
    pins the adversarial arm's own control; DP-control calibration of adversarial points is not
    accepted. Latent today: 0 of 12 adversarial points admissible (6 INCONCLUSIVE, 6 REFUSED).

### Deferred Ideas (OUT OF SCOPE)

- **The v5.0 replay-bearing adversarial re-run** — already a roadmap candidate; Phase 28 publishes
  the arm as recipe-confounded and states what v5.0 would settle (D-15). No measurement here.
- **Relearning as a diagnostic on the DP points that failed (b)** — carried from 27-CONTEXT's
  deferred list; a v5.0 idea, untouched here.
- **Phase 22's WARNING-4 / WARNING-5** (`delta_quadrature` at large μ; the two-oracle disagreements
  above 1e-9) — ledger rows, fix deferred: not on the publishing path.
- **The `scripts/phase18_extraction.py:85-87` throughput-comment debt** — `FORBIDDEN-BY-GUARD`
  (ancestry-frozen module); recorded, never edited.
- **Erasure at higher adapter rank; the frozen-tokenizer retrain** — deferred at v4.0 kickoff under
  the D-16 discipline, unchanged.
- **Publishing adapter weights for third-party reproduction** — out of scope; the 44 adapters stay
  local and are cited by sha256 from the frontier, as v3.0 did.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (from `.planning/REQUIREMENTS.md:449-456`) | Research Support |
|----|-------------|------------------|
| RPT-01 | The milestone report publishes whichever way the numbers came out, including the expected DP null at both capacities, with the standing expectation quoted as having been recorded before any run. | §2 (record field map — every binding the lead/caveat/ε rows need, with verified values), §1 (the `_prose.normalized` + sentinel + additive-append machinery to reuse), the D-05 ancestry test shape (`tests/test_phase27_prereg.py::_assert_frozen_before`, lines 74-111), the D-04 quote verified at `c673b4c` (SUMMARY.md unchanged since). |
| RPT-03 | Zero new runtime dependencies; `pyproject.toml` sha256-pinned state carries forward untouched, making it four milestones. | §5 (dependencies measured identical at v1.0/v2.0/v3.0/HEAD; whole-file diff v3.0→HEAD is exactly `+license = "MIT"`; current sha256 `15ffd6b5…926f`), §3/§4 (the 16 + 6 + v4.0 open items each located), the `audit-open` / `verify.artifacts` tool-error inventory (what D-31/D-39 may touch). |

RPT-02 is already ticked (`REQUIREMENTS.md:452`); SC2's third clause re-uses it, it is not re-ticked here.
</phase_requirements>

## Summary

Phase 28 is a **repo-internal publication phase**: nothing is measured, nothing is trained, and every number that reaches `docs/REPORT.md` / `README.md` must be a binding to a field of a committed JSON record or a module constant. The machinery to do this without inventing anything already exists and was located: `scripts/_prose.py::normalized` (the one whitespace-normalizing comparator, 153 call sites across 22 test files), `scripts/_addendum.py::append_addendum` (the one append-only writer, `pending`/`recorded` both required), the `<!-- STEM-BEGIN -->` / `<!-- STEM-END -->` sentinel convention with `_span()` slicing (`tests/test_phase25_correction.py:105`), the git-derived additive-append proof (`tests/test_phase18_docs.py:1002`), the heading-prefix guard that any append to REPORT/README must keep green (`tests/test_phase18_docs.py:210-254, 354`), the shallow-clone-refusing ancestry guard (`tests/test_phase27_prereg.py:74-111`), the bytes-recompute provenance pin (`tests/test_phase24_record.py:288`), and the frontier's own sanctioned ε sentences (`epsilon_report.rendered[<key>]`, produced by `phase25_epsilon.report_epsilon`, D-30) which the renderer should quote rather than re-render.

All three primary records were opened and their key layouts recorded in §2 with the exact values the decisions cite (tallies 0/32/6/6, `cleared_counts` a 30 / b 4 / c 1 / reached 38 / refused 6, canary 15/0/0 with `reachable_claims "4/15"`, curve total `2387.299119573244`, `sigma_for(4.0, 200, 1e-5) = 15.289937507119`, ε(σ=12) `5.299979064701441`, ε(σ=16) `3.7965357228934966`). One structural trap was found: for the six REFUSED `adv_n64` points `points.<key>.verdict.verdict` is `null` and the refusal lives in `verdict.early_return_reason` + `verdict.reasons`; tallies must be read from `verdicts.tallies` / `tallies_by_leg` / `refused_points`, never recounted from `points.*.verdict.verdict`. Three CONTEXT premises were re-measured and refined (not overturned): the three quick-task stamps are reported "missing" by `gsd-sdk query audit-open` because that tool reads only a file literally named `SUMMARY.md` (`sdk/dist/query/audit-open.js:78`), not because of the `status:` field alone (`260902-dlo` already carries `status: complete`); `verify.artifacts` reports a **seventh** active error the v3.0 audit did not list (19-16-PLAN's `contains: "Dated continuation"` is case-sensitive against a lowercase heading); and the three v3.0 `human_needed` VERIFICATION stamps (17/18/19) are archived under `.planning/milestones/v3.0-phases/` where `audit-open` no longer scans — so under D-31's "active error" rule they are record-only rows.

**Primary recommendation:** Build `scripts/phase28_report.py` as a stdlib-only renderer (`json` + `hashlib` + `string.Template` with `${dotted.path}` placeholders resolved by one `resolve(record, path)` function) that writes sentinel-bounded blocks into `docs/REPORT.md` and `README.md`; test it with (1) byte-identity of the re-rendered block against the committed slice, (2) a regex scan of the **template file** for numerals outside the D-19 grammar, (3) resolution of all 15 obligation paths, (4) ε/σ/C/q/δ/K equality against `mitigation_gate` / `mitigation_budget` / `mitigation_unit` / `phase18_extraction.K`, (5) the D-05 ancestry test copied from `_assert_frozen_before`, (6) D-25's `tomllib` comparison. Every new `scripts/*.py` and `tests/*.py` file is subject to the repo-wide AST censuses in §7 — brief every executor with that list.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Reading committed records (`results/phase25_frontier.json`, `phase26_canary.json`, `phase27_admission.json`, `phase23_*.json`) | `scripts/phase28_report.py` (renderer, CPU, stdlib) | tests (re-read for byte-identity) | D-21: read directly, no extract; digests recorded in the block |
| Module constants (ε/σ/C/q/δ/K) | `scripts/mitigation_gate.py`, `scripts/mitigation_budget.py`, `scripts/mitigation_unit.py`, `scripts/phase18_extraction.py`, `personacore.privacy.accountant` | renderer imports them; tests assert equality | Frozen pins are the single source; the report quotes them by import |
| Template + prose | a committed template file next to the renderer | — | D-16/D-18: the scan runs over the template source |
| Publication surfaces | `docs/REPORT.md` (one appended section), `README.md` (bullets inside `## Results at a glance`) | — | D-01, D-11; both guarded by `tests/test_phase18_docs.py::test_docs_continuation_is_additive` heading-prefix |
| Disposition ledger | `results/phase28_ledger.json` (new, hand-authored data, no gate) | renderer filters it (D-13, D-30) | D-23: no prereg module, no ancestry guard needed |
| Planning-doc edits (RPT ticks, ROADMAP row, STATE, UAT stamps, archived frontmatter repairs) | hand edits, snapshot-and-diff | — | D-34/D-31/D-36/D-37/D-39; zero `gsd-sdk` mutation handlers |
| CI green on `origin/main` | human checkpoint (developer pushes) | ledger records run id | D-38 |

## Standard Stack

### Core (nothing new is installed — RPT-03)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `json`, `hashlib`, `string.Template`, `re`, `subprocess`, `tomllib` | 3.11.15 (`.venv/bin/python`, verified) | record loading, sha256, placeholder substitution, template scan, `git show` / `merge-base`, `[project].dependencies` parsing | `tomllib` verified importable in the venv; `string.Template` gives `${name}` placeholders with strict `KeyError` on a missing binding — no dependency |
| `pytest` | `~=9.0` (dev extra, already installed) | all Phase 28 tests | 2871 tests collected in 5.35 s at HEAD |

### Supporting (existing repo helpers — reuse, do not re-implement)
| Helper | Location | Use here |
|--------|----------|----------|
| `normalized(text)` | `scripts/_prose.py:31-46` (imports nothing) | every cross-surface prose comparison (D-22): quote-at-`c673b4c` check, "sentence present in three surfaces" checks |
| `append_addendum(path, addendum, *, pending, recorded)` | `scripts/_addendum.py:60-100` | D-20 post-publish corrections only; refuses unless the `pending` line occurs exactly once |
| `recorded_verdict(text)` | `scripts/_verdict.py:29` | not needed by the renderer (REPORT.md has no `## Verdict` section); available if a clobber check on a results `.md` is ever wanted |
| `report_epsilon(...)` output | `results/phase25_frontier.json::epsilon_report.rendered[<point_key>]` | quote the record's own sanctioned ε sentence per point (D-30) instead of calling the function |
| `_assert_frozen_before(prereg_artifact, tracked)` | `tests/test_phase27_prereg.py:74-111` (twin at `tests/test_phase26_prereg.py`) | the D-05 shape: shallow-clone refusal (`rev-parse --is-shallow-repository == "false"`), `git log --diff-filter=A` + `adds[-1]` earliest add, `merge-base --is-ancestor`, `checked == n_commits × n_tracked` |
| git-derived additive proof | `tests/test_phase18_docs.py:986-1060` (`_git_bytes`, `test_extraction_report_addendum_is_additive`) | the shape for "bytes above the new section are unchanged": derive the pre-append revision from history, compare prefix |
| sentinel pair + `_span()` | `tests/test_phase25_correction.py:105-160` | `<!-- {stem}-BEGIN -->` / `<!-- {stem}-END -->`, exactly one pair, BEGIN before END |
| bytes-recompute provenance guard | `tests/test_phase24_record.py:288-330` | shape for asserting every `source_sha256` the block records equals `hashlib.sha256(path.read_bytes())` at HEAD, collecting all drift before asserting |
| `PYPROJECT_SHA256` pin | `tests/test_package.py:12,28-45` | D-26 rename target; keep the bytes-read rule (`read_bytes()`, `:36`) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `string.Template` `${a.b.c}` placeholders | f-string module / Jinja | Jinja = new dependency (forbidden); f-strings put numerals and Python in the same file the scan reads, muddying D-18 |
| A regex numeral scan over the template file | AST gate | The template is Markdown, not Python; AST does not apply. The "AST not grep" lesson is about Python files whose docstrings discuss the term — keep the test's own docstrings out of the scanned file and the regex is the right tool |
| One `results/phase28_ledger.json` | two files (inheritance / limitations) | D-28/D-30 lock one file, two filtered renderings |

**Installation:** none. **Version verification:** not applicable — no package is added; D-25's test is what proves it.

## Package Legitimacy Audit

Not applicable — this phase installs no package. `[project].dependencies` at v1.0, v2.0, v3.0 and HEAD were parsed with `tomllib` this session and are identical: `['numpy~=2.4', 'regex~=2026.5']`. **Packages removed / flagged: none.**

## Architecture Patterns

### System Architecture Diagram

```
committed records                         module constants (imported, never retyped)
 results/phase25_frontier.json  ─┐        mitigation_gate.{CAPACITY_BRANCHES,V4_VERDICTS,F_Y=0.7,F_C=0.5,MARGIN_K=2}
 results/phase26_canary.json    ─┤        mitigation_budget.{CURVE_K=16,FULL_FIDELITY_K=48,SIGMA_LADDER,CLIP_NORM,STEP_BUDGET=200}
 results/phase27_admission.json ─┤        mitigation_unit.{DELTA=1e-5,SAMPLING_RATE_Q=1.0,PRIVACY_UNIT}
 results/phase23_{cost,sigma_zero,control_floor}.json ─┤   phase18_extraction.{K=48,GATED_TIER}
 results/phase28_ledger.json (NEW, hand-authored rows) ─┤   accountant.{sigma_for,epsilon_for}
                                 │                          │
                                 ▼                          ▼
                     scripts/phase28_report.py  ── resolve("verdicts.capacity_branch") / sigma_for(4.0, steps, delta)
                                 │   bindings = {name: value}   + sha256 of every record read
                                 ▼
                     template (committed text, ${placeholders} only; NO bare numerals — D-18 scan)
                                 │   string.Template(...).substitute(bindings)   (KeyError = RED)
                                 ▼
          ┌──────────────────────┴──────────────────────┐
          ▼                                             ▼
 docs/REPORT.md                                    README.md
 <!-- PHASE28-REPORT-BEGIN --> … <!-- …-END -->    <!-- PHASE28-GLANCE-BEGIN --> … <!-- …-END -->
 (appended AFTER line 1326; every `## ` above     (bullets inserted INSIDE `## Results at a glance`,
  stays byte-identical)                             :109; zero deletions; no new `## ` heading)
          │                                             │
          └──────────── tests/test_phase28_*.py ────────┘
   (1) re-render → bytes == committed slice      (4) constants == module pins
   (2) template scan: bare numeral → RED         (5) D-05 ancestry: c673b4c ≺ earliest results/phase2[0-8]_* add
   (3) all 15 obligation paths resolve           (6) D-25 tomllib deps equal across v1.0/v2.0/v3.0/HEAD
```

### Recommended Project Structure (new files only)
```
scripts/phase28_report.py          # renderer: load records, bind, substitute, write between sentinels; PUBLISHED = "<pinned date>" (D-24)
scripts/phase28_report.md.tmpl     # committed template; ${dotted.binding} placeholders only  (name at planner's discretion)
results/phase28_ledger.json        # the one ledger (D-28); rows: id, milestone, source, disposition, evidence, reason
tests/test_phase28_report.py       # byte-identity, template scan, obligation-path resolution, constants match, provenance digests
tests/test_phase28_prereg.py       # D-05 ancestry test (copy of _assert_frozen_before shape) — or fold into the above
tests/test_phase28_ledger.py       # schema, closed disposition domain, FIXED-requires-test, counts derived by len()
tests/test_package.py              # D-25 tomllib test added; D-26 rename of test_pyproject_unchanged_since_v2_close
```

### Pattern 1: dotted-path resolution against a record (the obligation contract's own shape)
**What:** `PUBLICATION_OBLIGATION` paths are dotted (`verdicts.arm_existentials.dp`, `epsilon_report.curve_total_epsilon`) with one wildcard form `points.<key>.verdict.verdict` and one sentinel `<artifact absent>`.
**When to use:** every binding; the D-23 test iterates all 15 pairs.
**Example (shape, stdlib):**
```python
# Source: shape derived from scripts/phase25_prereg.py:424-491 and scripts/phase26_prereg.py:354-395
def resolve(record, path):
    node = record
    for part in path.split("."):
        node = node[part]            # KeyError is the RED the obligation demands — never .get()
    return node

# wildcard rows: expand `<key>` over the record's own key list
for key in canary["audited_point_keys"]:
    resolve(canary, f"points.{key}.verdict.verdict")   # member of phase26_prereg.VERDICTS
# `<artifact absent>` row: assert results/phase26_canary.json exists, else the D-19 clause must render
```

### Pattern 2: sentinel-bounded block, byte-identity by slice
**What:** the renderer writes `BEGIN … END`; the test re-renders to a string and compares with the slice between the sentinels (D-17), and asserts exactly one pair (`tests/test_phase25_correction.py:154`).
**Why:** `docs/REPORT.md:1145` and README heading order are asserted by `tests/test_phase18_docs.py::test_docs_continuation_is_additive` — a prefix-equality over every `## ` heading (`:210-254`). The new REPORT section must be appended **after** the last heading (`:1316 ## Figure Corrections…`); README bullets must not introduce a `## ` heading before `## Milestone 2 — what shipped` (`README.md:258`).

### Pattern 3: quoting the record's own sentence
**What:** for D-02/D-08/D-09 the report quotes strings verbatim: `verdicts.arm_existentials.dp`, `verdicts.amended_criterion`, `verdicts.adversarial_no_replay.{finding,log_line,log_source,dp_replay_source,code_source,note}`, `verdicts.leg_refusals.adv_n64`, `points.adv_n64_*.verdict.early_return_reason`, `epsilon_report.control_has_no_epsilon`, `canary.curve_total_is_context_only`, `canary.power_gate.sentence`, `points.<key>.verdict.reasons[*]`.
**Why:** the sentences already carry their denominators and disclosures; re-deriving them in prose is the defect class RPT-02 exists to close.

### Pattern 4: D-05 as three conjuncts (copied, not invented)
```python
# Source: tests/test_phase27_prereg.py:74-111 (shallow refusal, adds[-1], merge-base --is-ancestor)
assert _git("rev-parse", "--is-shallow-repository") == "false"
quoted = _git("show", "c673b4c:.planning/research/SUMMARY.md")
assert normalized(EXPECTATION_SENTENCE) in normalized(quoted)          # conjunct (i), via _prose
first_adds = [ _git("log","--diff-filter=A","--format=%H","--",p).split()[-1]
               for p in _git("ls-files","results/phase2[0-8]_*").split() ]   # conjunct (ii), derived
for add in first_adds:
    assert add != "c673b4c…" ; subprocess.run(("git","merge-base","--is-ancestor","c673b4c",add), check=True)
```
Measured this session: earliest v4.0 result add is `9bb34ad` (2026-08-20 19:37, `results/phase20_retention_floor.json`); `c673b4c` is 2026-08-20 09:27; `git merge-base --is-ancestor c673b4c 9bb34ad` exits 0; `.planning/research/SUMMARY.md` is byte-identical between `c673b4c` and HEAD (`git diff --quiet` true), 894 lines; the quote is at `:38-42` (the "72σ … σ ≥ 15.3 … Secret Sharer Table 3" paragraph) and `:386-397` (the `L=8 → 72σ, L=64 → 9σ, L=576 → 1σ` lever paragraph that D-03 also quotes).

### Anti-Patterns to Avoid
- **Recounting tallies from `points.*.verdict.verdict`:** the six `adv_n64` points have `verdict.verdict == null`; the REFUSED count lives in `verdicts.tallies.REFUSED`, `verdicts.refused_points` (6 keys) and `verdicts.tallies_by_leg.adv_n64.REFUSED`. Bind to those.
- **`datetime.date.today()` or `git rev-parse HEAD` inside the template bindings:** breaks byte-identity (D-24). Pin the date constant in the renderer; record git SHAs of the *sources* (which are fixed) not of HEAD.
- **Re-rendering after the publishing commit:** D-20. The byte-identity test is the guard that turns a post-publish template edit RED.
- **Calling `phase25_epsilon.report_epsilon` or `mitigation_gate.mitigation_point_verdict` from the renderer:** `tests/test_phase20_correction.py:1422` (AST census over `scripts/**/*.py` + `src/**`) refuses any `mitigation_point_verdict` call/import outside `phase20_gate_coverage.py`; quote `epsilon_report.rendered[key]` instead.
- **A `## ` heading in README's inserted bullets, or the REPORT section placed before `:1316`:** reddens `tests/test_phase18_docs.py::test_docs_continuation_is_additive`.
- **A `.md` report renderer that rewrites the whole file** (`phase18_extraction.render_report` pattern, criticised in `scripts/_addendum.py:31-36`): write only between sentinels.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| whitespace-tolerant prose match | a new `re.sub(r"\s+")` helper | `scripts/_prose.py::normalized` | RPT-02 mandates the one copy; 153 call sites already |
| post-publish correction | in-place edit of the rendered block | `scripts/_addendum.py::append_addendum` (both keywords) | D-20; refuses the second append |
| ancestry / shallow-clone check | ad-hoc `git log` parsing | copy `tests/test_phase27_prereg.py::_assert_frozen_before` | proven mould; `adds[-1]` defeats delete-and-re-add |
| per-point ε sentence | new sentence with the six required items | `frontier.epsilon_report.rendered[key]` | D-30's single sanctioned rendering already in the record |
| σ ≥ 15.3 reproduction | typing 15.29 | `accountant.sigma_for(4.0, frontier.points[k].composed_steps, frontier.points[k].delta)` → `15.289937507119` (verified) | D-06 |
| dependency-freeze proof | prose sentence | `tomllib.loads(git show vX:pyproject.toml)["project"]["dependencies"]` equality (D-25) | measured identical at 4 tags |
| TOML parsing | regex over `pyproject.toml` | `tomllib` (stdlib 3.11, verified importable) | zero deps |

**Key insight:** every quantity Phase 28 needs already exists in a record field or a pinned constant; the renderer's only job is addressing, not computing.

## Runtime State Inventory

Not a rename/refactor/migration phase — omitted. (Only two docstring edits are made, D-32, neither renames a symbol.)

## Repo-Internal Findings (the seven questions asked)

### 1. Existing doc-consistency machinery

| Asset | Exact location | What it does / how to reuse |
|-------|----------------|-----------------------------|
| `normalized(text)` | `scripts/_prose.py:31` (module imports nothing) | `" ".join(text.split())`; callers write `normalized(phrase) in normalized(text)` |
| consumers of `normalized` | 22 test files (`grep -rl "_prose" tests/`): `test_phase20_correction`, `test_phase20_prereg`, `test_phase22_dpsgd_ast`, `test_phase23_cost`, `test_phase24_correction`, `test_phase24_refusal_rate`, `test_phase25_{close,condition_c,control,correction,frontier,gate05,launch,prereg,probe2,promotion,record,verdict,wr}`, `test_phase26_{canary,prereg}`, `test_phase27_prereg` | the correction-sweep precedent; `test_phase25_correction.py:378` (`test_the_register_is_three_files_wide`) resolves "routes through normalized" by AST over the guard files — Phase 28's tests will be the fourth/fifth file in that register |
| sentinel-bounded continuation + `_span` | `tests/test_phase25_correction.py:105` (`f"<!-- {stem}-BEGIN -->", f"<!-- {stem}-END -->"`), `:154` exactly-one-pair test, `:209` claim-survives test, `:307` measured-values-in-span test | copy for Phase 28's block markers |
| additive-append proof from git history | `tests/test_phase18_docs.py:986-1060` | derive pre-append revision by scanning `git log --format=%H -- <file>` for the last blob carrying the placeholder; assert prefix bytes equal; shallow-clone refusal message |
| heading-prefix guard on REPORT/README | `tests/test_phase18_docs.py:210-254` (`_README_HEADINGS_BEFORE`, `_REPORT_HEADINGS_BEFORE`), `:354` `test_docs_continuation_is_additive` | the new section must land after all existing `## ` headings; README bullets add no heading |
| verbatim claim in three surfaces | `tests/test_phase18_docs.py:308` `test_claim_sentence_is_verbatim_in_three_surfaces` | model for "expectation sentence present in SUMMARY.md@c673b4c, REQUIREMENTS.md:13-14, ROADMAP.md:79-80" |
| headline numbers matched to sources | `tests/test_phase15_docs.py:340-425` (`_HEADLINE_NUMBERS`, `test_headline_numbers_match_sources`, `_github_anchor`), `:255` `test_limitations_quotes_are_verbatim` | v2.0's "prose quotes a number → assert against the artifact" precedent; README anchors follow `_github_anchor` |
| no-bare-zero-percent scans | `tests/test_phase18_docs.py:594, 956` | the v3.0 instance of a rendered-output value scan (the weak form D-18 rejects for the template, but fine as a *second* net over rendered output) |
| whole-file sha pin, bytes not text | `tests/test_package.py:12, 28-45` | D-26 rename target |
| bytes-recompute provenance pin | `tests/test_phase24_record.py:288` | shape for `source_sha256` checks inside the rendered block |
| record-pinned-to-frontier both ways | `tests/test_phase27_prereg.py:118` | `frontier_sha256` + `frontier_bytes` equality — the ledger/report should pin the same way |

**No existing table generator / `--check` re-render scheme exists** (`grep string.Template\|jinja\|format_map scripts/` → none). The Phase 25/26/27 records were emitted once (write-once) and prose quotes them; Phase 28's renderer is the first template renderer. `phase18_extraction.render_report` is the whole-file-rewrite anti-pattern.

### 2. The committed records — exact field names

**`results/phase25_frontier.json`** (22,311,714 B; sha256 `1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5`; one commit `4030d0e`; `provenance.git_sha 578a1ac…`, `verdicts.emitted_git_sha 3441f79…`)

Top keys: `governs, record, point_key_grammar, point_keys (44), arms, axis_for_arm, held_out_generalization, epsilon_report, verdicts, never_taught_floor, retention_leg_binds_at_anchor, retention_squeeze_is_the_frontier, retention_floor_disclosure, dialogue_floor_recipe_mismatch, dialogue_floor_sensitivity, mechanism_pin_disclosure, adversarial_makes_no_formal_claim, provenance, points`.

| Field | Verified value / shape | Used by |
|-------|------------------------|---------|
| `verdicts.capacity_branch` | `"null-at-both-capacities"` (member of `mitigation_gate.CAPACITY_BRANCHES`) | D-02 lead, section title |
| `verdicts.arm_existentials.dp` / `.adversarial` | `"NO CLEARING POINT IN THE 'dp' ARM: 0 of 32 point(s) examined returned PASS. …(D-29)"` / `"… 'adversarial' ARM: 0 of 6 point(s) …"` | D-02, obligation rows 1-2 |
| `verdicts.arm_existential_counts` | examined 6 / in-arm 12 for adversarial | D-09 |
| `verdicts.tallies` | `{"PASS":0,"FAIL":32,"INCONCLUSIVE":6,"REFUSED":6}` | lead |
| `verdicts.tallies_by_leg` | `dp_n8` F16, `dp_n64` F16, `adv_n8` I6, `adv_n64` R6 | tables |
| `verdicts.refused_points` | the 6 `adv_n64_ratio*` keys | D-09 |
| `verdicts.leg_refusals.adv_n64` | `"[phase20_gate_coverage] the recall floors came out Y_taught=0.0006944444444444444, Y_heldout=0.0; both must lie in (0.0, 1.0]…"` | D-09 |
| `verdicts.amended_criterion` | `"D-25-18-ADV64-REFUSED: 38 of 44 points reach condition (a) … control adv_n64_ratio0p000000 scored held-out recall 0/648 … Decided by the orchestrator 2026-09-09; reversible in seconds … Condition (a) fails on all six adv_n64 points regardless (3-66 of 416 > X)…"` | D-08/D-09 verbatim |
| `verdicts.adversarial_no_replay.{code_source, dp_replay_source, finding, log_line, log_source, note}` | `log_line` = `"[teach_persona] adv_n8: 176 episodes, 7,581 tokens (7,581 teaching + 0 replay), episode length mean 43.1 [24, 69]"`; `log_source` = `"logs/phase25_sweep.out:140"`; `dp_replay_source` = `"logs/phase25_sweep.out:14 '… arm=dp_n8 ... replay_windows=32' and :70 'arm=dp_n64 ... replay_windows=256'"`; `note` = `"results/phase25_operational_note.md §12.5c (2026-09-05)"` | SC4, D-08, D-09(i), D-10 |
| `verdicts.pre_registered_null.{condition_a, epsilon_at_sigma_0p5, statement}` | ε at σ=0.5 `519.6981942303134`; ZERO TOLERANCE sentence | lead |
| `verdicts.dp_recall_disclosure.{finding, heldout, taught}` | "Every DP point above sigma=0 scored taught recall 0/1008 and held-out 0/648…"; per-key `[k, n]` pairs | D-02 mechanism line |
| `verdicts.control_readings.{dp_n8,dp_n64,adv_n8,adv_n64}.recall_counts` | `dp_n8` taught `[790,1008]` heldout `[346,648]`; `dp_n64` taught `[87,1008]` heldout `[35,648]`; `adv_n8` `[879,1008]`/`[482,648]`; `adv_n64` `[1,1008]`/`[0,648]` | D-03 caveat (87/1008 vs 790/1008) |
| `verdicts.extraction_ceiling.{X, n_questions, tolerated, tolerance_sentence}` | X `0.006461685297443485`, 416, 0 | constants table |
| `verdicts.capacity_per_sigma["<σ 6-dp>"].{branch, reasons}` | branch per σ, all `null-at-both-capacities` | per-σ table |
| `verdicts.curve_k / full_fidelity_k / ratchet_k` | 16 / 48 / 48 | K bindings |
| `verdicts.adversarial_capacity_rule_absent` | LIMITATION 1 text | obligation row 6 |
| `epsilon_report.curve_total_epsilon` | `2387.299119573244` | D-07 |
| `epsilon_report.{k, total_delta, delta, delta_source, composition, summands (30 floats), summand_keys (30), selection_accounted (false), selection_accounted_reason, control_has_no_epsilon, control_points_excluded, adversarial_points_carry_no_epsilon (12), rendered{key: sentence}, rendered_by, multiplicities}` | `delta 1e-05`, `total_delta 0.00030000000000000003`, `k 30` | D-07, obligation rows 4-5-7 |
| `points.<key>.{sigma, epsilon, composed_steps (200), delta (1e-05), q, verdict, refusal, adapter_sha256, …}` | dp ε ladder: σ0.5 `519.6981942303134`, 0.7 `289.33863705009264`, 1.0 `159.44148628736576`, 1.5 `83.8305906128762`, 2.0 `54.37663901498563`, 3.0 `30.50627999271221`, 4.0 `20.675508046994032`, 6.0 `12.262332118205716`, 8.0 `8.595865790470416`, 12.0 `5.299979064701441`, 16.0 `3.7965357228934966`, 24.0 `2.3957449097512216`, 32.0 `1.7369988136430536`, 50.0 `1.060789755417757`, 80.0 `0.6339783761989397`; σ=0 `epsilon: null`; identical at both legs | D-06/D-07 rows |
| `points.<key>.verdict.{verdict, early_return_reason, reasons, point_dialogue_ppl_on/off, point_retention_ppl, control_gap, …}` | `adv_n8_*`: `verdict "INCONCLUSIVE"`, reasons carry the (c) band/cap strings; `adv_n64_*`: `verdict null`, `early_return_reason "REFUSED by the sanctioned route before the pin was reached"`, `reasons[0]` = the `Y_heldout=0.0` refusal | D-09(ii) |
| `provenance.{gate_module_sha256 86db4798…, budget_module_sha256 1b35aa88…, unit_module_sha256 45f37e15…, record_module_sha256 e1b3b380…, inputs.point_records{key:{path,sha256}}, publication_obligation, canary_reservations}` | | block provenance |

**`results/phase26_canary.json`** (165,830 B; sha256 `d2a71e2d40ba28d34b724afaa7083f9321895f0fe2ef4226f3510625003e8e19`; `frontier_sha256` matches the frontier; `emitted_git_sha c4a5511…`)

`summary {"BROKEN":0,"CONSISTENT":15,"INCONCLUSIVE":0}` · `reachable_claims "4/15"` · `reachable_keys` = σ 24/32/50/80 · `auditor_ceiling 2.7858978325772576` · `power_gate {control_epsilon_lower 2.7858978325772576, passed true, sentence "The instrument must resolve at least the smallest claim it checks.", threshold 0.6339783761989397}` · `exclusions.out {excluded [], n 56, of 56}`, `exclusions.in {n 8, of 8}` · `audited_point_keys` = the 16 `dp_n8_*` keys · `resolved_target "dp_n8_sigma0p000000"` · `curve_total_epsilon 2387.299119573244` · `curve_total_is_context_only` (the D-01 sentence — "context only" text) · `unit "one taught fact"`, `delta 1e-05`, `z 1.6448536269514722`, `n_in 8`, `n_out 56` · `points.<key>.{sigma, epsilon_upper, epsilon_sentence, verdict.{verdict, reasons[7]}}` — every reasons list ends with `"epsilon_upper >= auditor_ceiling: this comparison could not have failed (auditor_ceiling = 2.7858978325772576)"` for the 11 unreachable claims (the D-13 "could not have failed" disclosure D-30 wants as one row).

**`results/phase27_admission.json`** (16,664 B; sha256 `065b2bc19e9d1a3527e7b538f16106a54b1c62c9dd8e1915513cb1c942609199`; operator commit `88dff77`; `frontier_sha256`/`frontier_bytes` pinned)

`verdict.verdict "MOOT"`, `verdict.reasons` (generated from counts) · `tallies` = frontier's · `tallies_by_leg` · `cleared_counts {a 30, b 4, c 1, reached 38, refused 6, by_leg{dp_n8 {a15,b1,c1}, dp_n64 {a15,b1,c0}, adv_n8 {a0,b2,c0}, adv_n64 {0,0,0}}}` · `rows` (44 × `{point_key, arm, leg, verdict, refused, cleared_a, cleared_b, cleared_c}`) · `recall_thresholds {n8 {k 790,n 1008, threshold 0.548611…}, n64 {k 87, n 1008, threshold 0.06041…}}` · `baselines.{control_n8, control_n64, never_taught_*}` · `apparatus` · `budget {curve_k 16, full_k 48, f_y 0.7, margin_k 2, max_steps 200, relearn_cap 400, rungs}` · `x {value 0.006461685297443485, n_questions 416, tolerated 0, tolerance_sentence}` · `provenance.module_sha256` (7 modules incl. `scripts/mitigation_gate.py 86db4798…`).

Note for D-02's "30 of 30 noised DP points cleared (a), 0 cleared (b)": `cleared_counts.a == 30` is the noised-DP count (15+15; the two σ=0 controls did not clear (a)); `cleared_counts.b == 4` are the two σ=0 controls (`cleared_b true` on `dp_n8_sigma0p000000`) plus two `adv_n8` points — so "0 of 30 noised DP cleared (b)" must be derived from `rows` filtered to `arm == "dp" and sigma > 0`, not from `cleared_counts.b`.

**`results/phase25_operational_note.md`** §12.5c is at `:1036-1066` (heading `### 12.5c FINDING, 2026-09-05 — the adversarial arm has no replay, and condition (c) shows it`), contains the two log lines in a fenced block (`:1038-1042`) and the recipe cause paragraph (`:1044-1052`). Quote by `normalized` slice; never read `logs/` (gitignored, `.gitignore:16` `logs/`).

**Phase 23 records (D-12):** `results/phase23_sigma_zero.json` — `reading 0.7837301587301587`, `control_central_reading 0.5615079365079365`, `deviation 0.2222222222222222`, `floor 0.05357142857142849`, `verdict "HALT"`, `halt_message`, `floor_pin_module "scripts/mitigation_budget.py"`, `floor_pin_symbol "CONTROL_NOISE_FLOOR"`, `clip_bind_count 0`. `results/phase23_cost.json` — `ratios.{dp_n8,dp_n64,non_dp}.{eval_over_training_ceiling, eval_over_training_floor}` (dp_n8 ceiling `157.94846187604026`, floor `100.27355310661025`; dp_n64 `23.458…`/`14.892…`), `projection_not_published` (the `~1,010×` retraction rationale), `sizing`. The 4.15× figure = `deviation / floor` (`4.148148148148154`, already in `REQUIREMENTS.md:560` DPSGD-06 row) — bind as a derived ratio of two record fields or quote the row. The `~1,010×` original text and its 23-12 continuation are in `.planning/REQUIREMENTS.md:176-271` (sentinels `<!-- 23-12-CONTINUATION-BEGIN/END -->`).

**The pre-registration expectation (D-04/D-05):** `.planning/research/SUMMARY.md` at `c673b4c` (2026-08-20 09:27:45 -0300), lines 38-42 and 386-397 (verified this session; file unchanged at HEAD). Milestone restatements: `.planning/REQUIREMENTS.md:13-14`, `.planning/ROADMAP.md:79-80` (milestone overview) and `:1081-1082` (SC1). Secret Sharer precedent is in the same SUMMARY paragraph (`:41`, "Secret Sharer Table 3 is the direct precedent … including ε = 10⁹ `[LIT]`") and in `ROADMAP.md:80-81`.

**Publication obligation (D-23):** `scripts/phase25_prereg.py:414` `PUBLICATION_OBLIGATION_SCOPE`, `:424-491` `PUBLICATION_OBLIGATION` (8 pairs: `verdicts.arm_existentials.dp`, `verdicts.arm_existentials.adversarial`, `verdicts.capacity_branch`, `epsilon_report.curve_total_epsilon`, `epsilon_report.selection_accounted`, `verdicts.adversarial_capacity_rule_absent`, `epsilon_report.control_has_no_epsilon` — note: 7 tuples are present in the file; CONTEXT says 8 — the planner should `len()` it at plan time rather than type either number), `:496` `CANARY_RESERVATIONS` (`canary_population_rule` at `:508`). `scripts/phase26_prereg.py:352` `SUPERSEDES_OBLIGATION`, `:354-395` `PUBLICATION_OBLIGATION_CONTINUATION` (7 pairs: `power_gate.passed`, `auditor_ceiling`, `reachable_claims`, `exclusions.out.n`, `points.<key>.verdict.verdict`, `points.<key>.verdict.reasons`, `<artifact absent>`), `VERDICTS`.

### 3. The 16 inherited v3.0 tech-debt items and the 6 stale stamps

Enumerated in `.planning/milestones/v3.0-MILESTONE-AUDIT.md` frontmatter `tech_debt:` (`:209-235`), 5+2+2+3+4 = 16, and `MILESTONES.md:51-63` restates the counts. Current location and measured status of each:

| # | Phase | Item (abbrev.) | Where it lives today | Measured now / candidate disposition (planner confirms) |
|---|-------|----------------|----------------------|--------------------------------------------------------|
| 1 | 16 | I-1 stale `phase14_recall.py:1336` citations in `results/phase16_persistence_report.md:111,226,257` | published results `.md` | FORBIDDEN-BY-GUARD (published evidence; D-32) |
| 2 | 16 | I-2 `~39 min` wall clock vs 137.2 min in `phase16_persistence_report.md:105` | same | FORBIDDEN-BY-GUARD |
| 3 | 16 | R-1 D-28 note rendered as English, not tied to `_CONTEXT_PATH` | `scripts/phase16_persistence.py` (NOT ancestry-guarded — no `is-ancestor` test names it; no `module_sha256` in `results/*.json` names it) | RE-DEFERRED or ACCEPTED (behavioural, not prose) |
| 4 | 16 | R-2 disclosure paragraph is post-run text | `results/phase16_persistence_report.md` | FORBIDDEN-BY-GUARD / ACCEPTED |
| 5 | 16 | R-3 `tests/test_phase16_driver.py:1782` weak assertion | test file | ACCEPTED (mutation-proved primary) or FIXED with a sharper assertion |
| 6 | 17 | DEF-17-01 `make lint` red locally | `Makefile:31` now `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | CLOSED-EARLIER at `7b38e38` (D-33) |
| 7 | 17 | 11 Phase-17 SUMMARYs lack `requirements`/`requirements-completed` frontmatter | `.planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix/17-*-SUMMARY.md` (verified: `requires/provides/affects/tags` only) | D-31: only if a tool reports an active error — `audit-open` does not scan archived phases; RE-DEFERRED/ACCEPTED unless the milestone audit tooling is shown to read them |
| 8 | 18 | W1 residual — `phase18_extraction_report.md:5` misattributes K/rungs/templates to `13666c4` | published results `.md` | FORBIDDEN-BY-GUARD (D-32 names it) |
| 9 | 18 | stale parenthetical `scripts/phase16_persistence.py:1605` ("exactly two entries") | verified at `:1605` ("`PERSONA_ALLOWLIST` stays at exactly two entries"); the allowlist itself lives at `tests/test_phase14_scoring.py:517` | FIXED + test (D-32) |
| 10 | 19 | W1 six stale artifact names in PLAN frontmatter | `.planning/milestones/v3.0-phases/19-selective-memory-erasure/19-08-PLAN.md` (`results/phase19_cal_corpus.json`, `checkpoints/phase19_cal_adapter.pt`), `19-09-PLAN.md` (`results/phase19_calibration_arm.json`), `19-12-PLAN.md` (`results/phase19_arm_m1.json`), `19-13-PLAN.md` (`results/phase19_arm_m2.json`, `checkpoints/phase19_m2_retrain_adapter.pt`) — **all 6 reproduced with `gsd-sdk query verify.artifacts <plan>` this session**; plus a 7th: `19-16-PLAN.md` `contains: "Dated continuation"` fails (`Missing pattern`) because the report's headings read lowercase "(dated continuation, 2026-08-19)" at `results/phase19_erasure_report.md:355,468,551` | FIXED (D-31 in scope). Resolve real names from `scripts/phase19_erasure.py` constants: `arm_record_path(arm)` at `:2560` (`ARM_RECORD_DIR = results/`), `CALIBRATION_ARM = "erase_calibration"` `:3092`, `CALIBRATION_CORPUS_PATH = results/phase19_calibration_corpus.json` `:3093`, `RETRAIN_ARM = "erase_reference"` `:2996`; tracked files: `results/phase19_arm_{cal-erased,erased,replicate,retrain}.json`, `results/phase19_calibration_corpus.json`; checkpoints are gitignored (`checkpoints/`), so a checkpoint path can never pass `verify.artifacts` — record that rather than "fixing" it |
| 11 | 19 | `perplexity.py:11-13` denominator docstring `corpus_len - n_windows` | `src/personacore/evaluation/perplexity.py:11-13` (verified text; no sha pin, no ancestry guard) | FIXED + test (D-32); `tests/test_perplexity.py:122` already asserts `ntok == n_tokens - 1` — the new test can be a docstring-text assertion (`"corpus_len - 1" in perplexity.__doc__`) |
| 12 | 19 | `19-13-SUMMARY.md` stray `</content>` / `</invoke>` | `.planning/milestones/v3.0-phases/19-selective-memory-erasure/19-13-SUMMARY.md:429-430` (verified) | ACCEPTED, record-only (D-31) |
| 13 | x-cut | ERASE-01/02 are bullets, not checkboxes | `.planning/milestones/v3.0-REQUIREMENTS.md` | ACCEPTED (deliberate) |
| 14 | x-cut | 16-04/05/06 `requirements-completed: []  # comment` parses as a string | verified at `16-04-SUMMARY.md:52`, `16-05:52`, `16-06:55` | D-31: FIXED only if a tool errors on it; otherwise ACCEPTED |
| 15 | x-cut | 17-digit `77.63701134639661%` in planning artifacts | `19-12-SUMMARY.md:42,89,219` (verified; also STATE.md, quick-260819-r1u PLAN) | ACCEPTED, record-only (D-31) |
| 16 | x-cut | README `## Results at a glance` carries only v2.0 numbers | `README.md:109-147` (verified) | FIXED by D-11 (rendered bullets) |

**The 6 stale stamps** (`.planning/STATE.md:1539-1571`, table "At v3.0 close … 6 items"):

| Item | Today | Tool status (`gsd-sdk query audit-open`, run this session) | Disposition path |
|------|-------|------------------------------------------------------------|------------------|
| debug `draw-all-utf8-decode-crash` `status: fixing` | `.planning/debug/draw-all-utf8-decode-crash.md:3` | REPORTED (open) — closes on `status: resolved` or `complete` (`audit-open.js:43`); sibling `sigma-zero-beats-control.md` uses `status: resolved` | FIXED-stamp under D-39 with the evidence STATE.md already cites (both Phase 18 arms ran to completion; `results/phase18_extraction_report.md:320`) |
| quick `260819-r1u` no `status:` | `.planning/quick/260819-r1u-close-b1-readme-v3-catchup/260819-r1u-SUMMARY.md` | REPORTED as `missing` | see below |
| quick `260819-sgh` no `status:` | `.planning/quick/260819-sgh-close-w2-b1a-b1b/260819-sgh-SUMMARY.md` | REPORTED as `missing` | see below |
| `17-VERIFICATION.md` human_needed | archived `.planning/milestones/v3.0-phases/17-*/` | NOT reported (audit scans `.planning/phases/` only) | record-only / ACCEPTED (D-35 precedent) |
| `18-VERIFICATION.md` human_needed | archived | NOT reported | record-only |
| `19-VERIFICATION.md` human_needed | archived | NOT reported | record-only |

**Refinement of D-39's premise (measured):** `gsd-sdk` resolves to `~/.npm/_npx/…/get-shit-done-cc/sdk/dist/query/audit-open.js`; line 78 reads `join(taskDir, 'SUMMARY.md')` **literally**, `:85` reads `fm.status`, `:91` skips only `=== 'complete'`. The three flagged tasks are the only three whose summary is named `<id>-SUMMARY.md`; the three green ones (`260605-lgy`, `260802-h3g`, `260814-d0j`) are `SUMMARY.md` + `status: complete`. `260902-dlo` already has `status: complete` (line 4) and is still reported, proving the filename is the active cause. The v2.0-close precedent (`STATE.md:1541-1544`) was exactly this rename. Fix = `git mv <id>-SUMMARY.md SUMMARY.md` in each of the three dirs **and** add `status: complete` to `r1u`/`sgh` (evidence commits `7af6006`,`24d49ad` / `4012a61`,`c90d0c8`,`98d0a60` per STATE.md). (The older `gsd-tools.cjs` audit accepts both names — `bin/lib/audit.cjs:106-116` — so the rename is safe under both tools.)

Also present in `audit-open` today and inside this phase's scope: `24-HUMAN-UAT.md` `partial` with 2 `[pending]` results (items 2 and 3 — D-37 disposes both), `25-HUMAN-UAT.md` `partial` with 0 pending (D-36), `23-VERIFICATION.md` and `27-VERIFICATION.md` `human_needed` (D-35 keep), the pending todo (folded — move to `.planning/todos/resolved/` or stamp `status: resolved` per the todo workflow). REQUIREMENTS.md `Future Requirements:470-472` also names "3 `PARTIAL` VALIDATION.md files" (17/18/19; measured stamps: 17 `planned`, 18 `draft`, 19 `draft`) — a category SC3 does not enumerate; give it rows or say why not.

### 4. Phase 27's 16 review findings and D-40

`.planning/phases/27-relearning-attack/27-REVIEW.md` (commit `a1dec50`): CR-01 `:78`, CR-02 `:126`, WR-01 `:187`, WR-02 `:217`, WR-03 `:249`, WR-04 `:281`, WR-05 `:313`, WR-06 `:348`, IN-01..IN-08 `:376-460` — 2 + 6 + 8 = 16. `27-VERIFICATION.md` reproduced every CR/WR (`status: human_needed`, `:5`). The ruling is `27-HUMAN-UAT.md` items 1-2 (`status: complete`, both `result: pass — RULING (developer, 2026-09-16)`), duplicated as `.planning/todos/pending/phase28-carry-phase27-latent-review-findings.md` (frontmatter `resolves_phase: 28`, `status: pending`). Rows to create: CR-01, CR-02, WR-02, WR-03, WR-06 (NAMED-LIMITATION), WR-01, WR-04 (NAMED-LIMITATION, inconsequential), WR-05 (NAMED-LIMITATION + the v5.0 block), IN-01..IN-08 (disposition per finding — the ruling only covered CR/WR; the planner assigns ACCEPTED/RE-DEFERRED with the REVIEW line as `source`), obligations (a)-(f) carried verbatim into the register text.

D-40 (Phase 25's publication obligation, `25-CONTEXT.md`) is the two obligation tuples in §2; its two LIMITATIONS are `verdicts.adversarial_capacity_rule_absent` (LIMITATION 1) and `epsilon_report.control_has_no_epsilon` (LIMITATION 2) — one NAMED-LIMITATION row each. The canary's "could not have failed" disclosure = one row bound to `auditor_ceiling` + `reachable_claims`.

Other v4.0 rows CONTEXT names: RELRN-02..05 unticked (`REQUIREMENTS.md:424-433`; D-05 of 27-CONTEXT); Phase 22 WARNING-4/5 (`22-VERIFICATION.md`; `22-19-SUMMARY.md:20,23` — 46 two-oracle disagreements, worst 6.08e-09); FRONT-04's weaker form (`REQUIREMENTS.md:571` "Satisfied in a weaker form than the text implies"); 23-17 unticked (`ROADMAP.md:706`, twice re-ticked by handlers and hand-reverted — FORBIDDEN-BY-GUARD/ACCEPTED: the box stays unticked by design, 23-20 completed the run); `scripts/phase18_extraction.py:85-87` throughput comment (`REQUIREMENTS.md:473-482`, FORBIDDEN-BY-GUARD); the `adv_n64` refusal (`verdicts.amended_criterion`).

### 5. `pyproject.toml` sha256 baseline

- Test: `tests/test_package.py::test_pyproject_unchanged_since_v2_close` (`:28-45`), pin `PYPROJECT_SHA256 = "15ffd6b58e289447ac6460bdd6210c04d20d5ff5831f741bb3db3bdc0ca7926f"` (`:12`), reads `read_bytes()`.
- Current file sha256 (this session): `15ffd6b58e289447ac6460bdd6210c04d20d5ff5831f741bb3db3bdc0ca7926f` — matches the pin.
- `git show v3.0:pyproject.toml | sha256` = `81d07d5d700000008680265659e31d9e335dec65060e7c4ae44c6247b6112bdf`.
- `git log v3.0..HEAD -- pyproject.toml` = exactly one commit `5065bc5`; `git diff v3.0 HEAD -- pyproject.toml` = `+license = "MIT"` only. D-27 confirmed.
- `[project].dependencies` via `tomllib` at `v1.0`, `v2.0`, `v3.0`, HEAD: `['numpy~=2.4', 'regex~=2026.5']` at all four. Tags present: `m1-demo-v1 v1.0 v2.0 v3.0`.
- D-25 test needs the tags in CI: `actions/checkout` with `fetch-depth: 0` fetches tags by default; the shallow-clone assertion pattern should be reused so a tagless clone refuses loudly.

### 6. How prior milestones were closed

`/gsd-complete-milestone` (v3.0, 2026-08-19 21:52-22:05): `ab076a8` mark audit warnings resolved → `1ff4e8a chore: archive v3.0 milestone files` (ROADMAP/REQUIREMENTS/phases → `.planning/milestones/v3.0-*`, `v3.0-phases/`) → `a823e44 docs: update retrospective for v3.0` → `091acea chore: remove REQUIREMENTS.md` → `4554ef4 chore: drop the working-copy path of the v3.0 audit` → annotated tag `v3.0` (message = key accomplishments with numbers). `MILESTONES.md` sections `## v3.0 … (Shipped: 2026-08-19)` `:3`, `### Known Gaps and Deferred Items` `:51-63` (states "16 items" and "6" by prose — Phase 28's ledger is what makes those counts data). No `CHANGELOG` exists; README carries dated `## … (recorded YYYY-MM-DD)` sections (`:288, :316, :355, :402`) indexed in `### Record of corrections` (`:96`, anchors via `tests/test_phase15_docs.py::_github_anchor`). Phase 28 does NOT do any of the above (D-34) — it hands over with RPT-01/RPT-03 ticked, the ROADMAP Phase 28 row + `- [ ] **Phase 28**` heading checkbox (`ROADMAP.md:158, 1123`), STATE.md frontmatter/position, and the ledger. The milestone audit (`/gsd-audit-milestone`) then reads the ledger.

### 7. Test-suite conventions that bite new files

- Runtime: `make test` = `.venv/bin/pytest -q`, 2871 tests, **21-24 min** measured (CI runs 21-24 min too: runs `34846118965` 21m35s, `34834491850` 22m15s). GSD's `timeout 300` post-merge gate can never pass — run the suite uncapped in background once per wave on a committed tree.
- Lint gate: CI `ruff check . && ruff format --check .` (`ci.yml:44`); local `make lint` uses `.venv/bin/ruff` (`Makefile:31`). Line length 100, `select = ["E","F","W","I"]`, `.planning` excluded (`pyproject.toml:[tool.ruff]`).
- CI: `.github/workflows/ci.yml` — `test` job (`fetch-depth: 0` at `:28`, Python 3.11, `pip install -e ".[cpu,dev,demo]"`, ruff, `pytest -q`) and `demo-asset` job. `main` is **29 commits ahead** of `origin/main` today (origin `8f43342`, 2026-09-13); last 3 `main` CI runs green (newest 2026-09-14T12:55). D-38's push is a human checkpoint.
- Repo-wide AST censuses that scan **every** `scripts/*.py` + `src/**/*.py` (a new `scripts/phase28_report.py` is inside all of them):
  - `tests/test_phase20_correction.py:1422` — no `mitigation_point_verdict` call/import outside `phase20_gate_coverage.py`.
  - `tests/test_phase21_unit_continuation.py:83` — no `privacy_n` reached through `mitigation_unit`.
  - `tests/test_phase25_driver.py:359` — `os.replace` only in `phase25_run.py` / `phase25_record.py` (write files with `Path.write_text` / `write_bytes`, or `phase25_run.atomic_write_json` if atomicity is wanted).
  - `tests/test_phase19_erasure.py:1386` — `retention_perplexity(` call-site census.
  - `tests/test_phase23_ctrl.py:82` — `train_never_taught` one definition/one call (`scripts/*.py`).
  - `tests/test_phase23_resume.py:279` — `train_arm(` only in `_TRAIN_ARM_CALL_SITES` (prose mentions in strings count — do not write the token `train_arm(` anywhere in new files, including comments/docstrings).
  - `tests/test_lora_inject.py` — `inject_lora` consumer/producer registers (ISO-06).
  - `tests/test_phase25_prereg.py:262-290` — no function pairing a bit-identity assertion name with both a `sigma_zero`-marker and a `seam_off`-marker identifier (scans `scripts/` and `tests/`).
  - `tests/test_phase21_sc5.py:170-300` — counts the literal `== 10` under `tests/` (comments included); do not write `== 10` in new tests.
  - `mitigation_gate.ratchet_k` accepts only K ∈ (48, 24, 16, 8) — fixtures use 8/16.
- Clean-tree probes (fail while anything is untracked/modified under `results/`, `tests/`, `scripts/`): `test_phase23_resume::test_production_resume_epsilon_bit_identical` (MPS, ~105 s), `test_phase25_frontier::test_a_perturbed_per_point_count_breaks_the_aggregate`, `test_phase25_grid::…from_import_variant…`, `test_phase25_probe2::…planted_bit_identity…`, `test_phase25_driver::…planted_push`, `test_phase25_epsilon::…planted_bare_print`, four `test_phase25_plots` planted-guard tests, `test_phase25_watch::…planted_action`. Run the full suite only on a committed tree. `results/phase28_ledger.json` untracked → those `results/` probes go RED until committed.
- `tests/test_phase27_prereg.py::test_the_record_is_pinned_to_the_frontier_both_ways:130` asserts the frontier has exactly ONE commit — never touch `results/phase25_frontier.json`.
- Tests must be CPU-only, GPU-free, and must not import torch in a "fresh interpreter" probe if the plotter pattern is copied.

## Common Pitfalls

### Pitfall 1: Recounting verdicts from `points.*.verdict.verdict`
**What goes wrong:** the six `adv_n64` points have `verdict.verdict == null`; a `Counter` over that field yields 38 entries + 6 `None`.
**How to avoid:** bind to `verdicts.tallies`, `verdicts.tallies_by_leg`, `verdicts.refused_points`, and for REFUSED text to `points.<k>.verdict.early_return_reason` / `.reasons[0]`.
**Warning signs:** any `Counter`/`sum(...)` over `points` in the renderer.

### Pitfall 2: "0 cleared (b)" taken from `cleared_counts.b`
**What goes wrong:** `cleared_counts.b == 4` (two σ=0 controls + two `adv_n8`); the D-02 sentence concerns the 30 noised DP points.
**How to avoid:** derive from `phase27_admission.rows` filtered on `arm == "dp"` and the frontier point's `sigma > 0`; or quote `verdicts.dp_recall_disclosure.finding` verbatim ("Every DP point above sigma=0 scored taught recall 0/1008 and held-out 0/648").

### Pitfall 3: Breaking the heading-prefix guard
**What goes wrong:** inserting a `## ` heading in README's glance bullets, or placing the REPORT section anywhere but after `:1316`, reddens `tests/test_phase18_docs.py::test_docs_continuation_is_additive`.
**How to avoid:** REPORT section appended at EOF; README block is bullets only; run `pytest tests/test_phase18_docs.py tests/test_phase15_docs.py -q` after every render (15 tests, seconds).

### Pitfall 4: A clock or HEAD SHA in the bindings
**What goes wrong:** byte-identity fails on every re-render (D-24).
**How to avoid:** `PUBLISHED = "2026-09-…"` constant in the renderer; record only source sha256s and the records' own `git_sha` fields.

### Pitfall 5: The template scan matching the test's own docstrings
**What goes wrong:** a scan over a Python file that discusses numerals goes false-RED (memory: "grep criteria measure prose").
**How to avoid:** scan the **template file** only (Markdown), after stripping `${…}` placeholders; the D-19 exemption regex covers `Phase \d+`, `[A-Z]+-\d+` (REQ/decision IDs), ISO dates, 7-40 hex SHAs, `§\d+(\.\d+)?[a-z]?`, 4-digit years in citation context; everything else numeric is RED. Keep the test's RED probe as a planted template in `tmp_path`.

### Pitfall 6: `gsd-sdk` mutation handlers
**What goes wrong:** they corrupted frontmatter and re-ticked 23-17 twice (`ROADMAP.md:706`); `roadmap.update-plan-progress` wiped a row note (`:1120`).
**How to avoid:** D-34 — snapshot `STATE.md`/`ROADMAP.md`/`REQUIREMENTS.md`, hand-edit, diff all three. Read-only queries (`audit-open`, `verify.artifacts`, `init.phase-op`) are fine.

### Pitfall 7: Stamp fixes that do not clear the tool
**What goes wrong:** adding `status: complete` to `260819-r1u-SUMMARY.md` alone leaves `audit-open` reporting `missing` (filename rule, `audit-open.js:78`).
**How to avoid:** rename to `SUMMARY.md` (v2.0 precedent) and add the status; re-run `gsd-sdk query audit-open` and record the before/after counts in the ledger row's `evidence`.

### Pitfall 8: Gitignored checkpoint paths in PLAN frontmatter can never verify
**What goes wrong:** `checkpoints/` is gitignored (`.gitignore`), so `verify.artifacts` will report `checkpoints/phase19_*.pt` missing on any fresh clone whatever the name.
**How to avoid:** for the two checkpoint entries, record the disposition (ACCEPTED or replace with the tracked record that pins the checkpoint sha) rather than chase a name.

## Code Examples

### D-25 — dependencies identical across four milestones (verified output)
```python
# Source: measured this session with the venv's Python 3.11.15
import subprocess, tomllib
def deps(rev):
    toml = subprocess.run(["git","show",f"{rev}:pyproject.toml"], capture_output=True, text=True, check=True).stdout
    return tomllib.loads(toml)["project"]["dependencies"]
head = tomllib.load(open("pyproject.toml","rb"))["project"]["dependencies"]
assert deps("v1.0") == deps("v2.0") == deps("v3.0") == head == ["numpy~=2.4", "regex~=2026.5"]
```

### D-06 — reproduce σ ≥ 15.3 and the ε bracket from the frontier's own inputs (verified values)
```python
# Source: src/personacore/privacy/accountant.py:819 epsilon_for(sigma, steps, delta), :988 sigma_for(target_epsilon, steps, delta)
p = frontier["points"]["dp_n8_sigma16p000000"]         # composed_steps 200, delta 1e-05
assert accountant.sigma_for(4.0, p["composed_steps"], p["delta"]) == 15.289937507119
assert accountant.epsilon_for(16.0, p["composed_steps"], p["delta"]) == p["epsilon"] == 3.7965357228934966
assert frontier["points"]["dp_n8_sigma12p000000"]["epsilon"] == 5.299979064701441
```

### Sentinel block write (stdlib)
```python
# Source: sentinel convention from tests/test_phase25_correction.py:105; no existing writer — this is the minimal one
BEGIN, END = "<!-- PHASE28-REPORT-BEGIN -->", "<!-- PHASE28-REPORT-END -->"
def install(path, block):
    text = path.read_text(encoding="utf-8")
    assert text.count(BEGIN) == text.count(END) <= 1
    if BEGIN in text:                                    # pre-publish re-render only (D-20)
        head, rest = text.split(BEGIN); _, tail = rest.split(END)
        text = head + BEGIN + block + END + tail
    else:
        text = text.rstrip("\n") + "\n\n" + BEGIN + block + END + "\n"
    path.write_text(text, encoding="utf-8")
```

## State of the Art

| Old Approach (v3.0) | Current Approach (Phase 28) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prose authored, numbers checked by value scans (`test_phase15_docs::_HEADLINE_NUMBERS`, `no_bare_zero_percent`) | Template bound to record paths; scan of the template source; byte-identity re-render | D-16..D-19 (2026-09-17) | numbers cannot be typed; drift is RED before render |
| Whole-file sha pin as "zero new deps" proof | `tomllib` dependency-array equality across tags; sha pin kept as change detector | D-25/D-26 | the guarantee survives a `license` line |
| Debt counted in audit prose ("16 items") | `results/phase28_ledger.json`, counts by `len()` | D-28 | one source, two renderings |
| `grep -c` prose checks | `_prose.normalized` (RPT-02, shipped Phase 20-25) | 2026-08-21+ | line-wrapped phrases no longer read as absent |

**Deprecated/outdated:** `phase18_extraction.render_report`-style whole-file rewrite; hardcoded commit pairs in ancestry tests (D-05 derives them).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The v3.0 audit's "16 items" maps to the `tech_debt:` frontmatter block exactly (5+2+2+3+4) — counted this session; the audit prose itself never lists them numbered | §3 | Low — the ledger `len()` becomes the truth regardless |
| A2 | Rows for IN-01..IN-08 need dispositions even though the ruling only covered CR/WR | §4 | Low — planner may choose ACCEPTED with REVIEW line as source |
| A3 | `actions/checkout` `fetch-depth: 0` makes tags `v1.0/v2.0/v3.0` available in CI for D-25 | §5 | Medium — if not, D-25's test must refuse readably; add a `git tag -l` precondition assertion |

No `[ASSUMED]` package or library claims exist — nothing is installed.

## Open Questions (RESOLVED)

All five resolved by the plan set (28-01..28-07); each line names the plan/task that carries the resolution.

1. **`PUBLICATION_OBLIGATION` has 7 tuples on disk, CONTEXT says 8.** — RESOLVED: 28-04 T1 binds `derived.obligation_count` = `len(PUBLICATION_OBLIGATION) + len(PUBLICATION_OBLIGATION_CONTINUATION)`; 28-05 T1 `test_every_obligation_path_resolves` iterates by `len()` with no literal 7/8/14/15.
   - What we know: `scripts/phase25_prereg.py:424-491` carries 7 `(field_path, why)` pairs (dp, adversarial, capacity_branch, curve_total_epsilon, selection_accounted, adversarial_capacity_rule_absent, control_has_no_epsilon); `phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION` has 7 → 14 total, not 15.
   - Recommendation: the test iterates `len(...)`; the report never types 8 or 15 — bind `${obligation_count}` to `len(PUBLICATION_OBLIGATION) + len(PUBLICATION_OBLIGATION_CONTINUATION)`.
2. **`24-HUMAN-UAT.md` stamp after D-37.** — RESOLVED: 28-02 T3 `checkpoint:decision` (`complete` / `stay-partial`); the ruling and `counts.uat_gaps` are recorded in the ledger row `UAT-24-STAMP` (28-03 T1). With items 2 and 3 disposed, it has zero pending items — by D-36's own logic `partial` becomes false. CONTEXT is silent on 24's stamp. Recommendation: the planner rules explicitly (move to `complete` with the dated note, or leave `partial` with a ledger reason) so `audit-open` output is intentional either way.
3. **The 3 PARTIAL VALIDATION.md files (17 `planned`, 18 `draft`, 19 `draft`)** — RESOLVED: 28-03 T1 rows `FM-17-VALIDATION-PLANNED`, `FM-18-VALIDATION-DRAFT`, `FM-19-VALIDATION-DRAFT` as `ACCEPTED` (category `found-by-measurement`). are in REQUIREMENTS.md's carry-forward sentence but not in SC3's "16 + 6". Recommendation: three `ACCEPTED`/record-only rows so the ledger's v3.0 view is complete.
4. **The 7th `verify.artifacts` error (19-16 `contains: "Dated continuation"` case)** — RESOLVED: 28-02 T2 step 2 changes the pattern to `"dated continuation"`; 28-03 T1 row `FM-19-16-CASE` `FIXED` (evidence: 28-02 sha + `tests/test_phase28_ledger.py::test_phase19_plan_result_artifacts_exist`). — in D-31 scope by its own rule but not in the v3.0 audit's six. Recommendation: fix the frontmatter pattern casing (or `contains: "dated continuation"`) and record it as a new row found by measurement.
5. **`checkpoints/*.pt` PLAN artifacts (19-08, 19-13)** are gitignored and can never verify from a clone. Recommendation: record rather than rename. — RESOLVED: 28-02 T2 step 1 leaves both entries unrenamed and records them in the SUMMARY; 28-03 T1 row `TD-19-W1-ARTIFACT-NAMES`'s reason names them as unverifiable from a clone by design.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything | ✓ | 3.11.15 (`.venv/bin/python`) | — |
| `tomllib` | D-25 | ✓ | stdlib 3.11 | — |
| pytest | tests | ✓ | `~=9.0` (2871 collected) | — |
| ruff | lint | ✓ | `.venv/bin/ruff` 0.15.x | — |
| git with full history + tags | D-05, D-25, additive proofs | ✓ | non-shallow (`rev-parse --is-shallow-repository` = false); tags `v1.0 v2.0 v3.0 m1-demo-v1` | — |
| `gsd-sdk` (read-only queries) | D-31/D-39 measurement | ✓ | `~/.local/bin/gsd-sdk` → `get-shit-done-cc/sdk/dist/cli.js` | `gsd-tools.cjs audit-open` |
| `gh` CLI | D-38 run id | ✓ | `gh run list` works | GitHub UI |
| Network / GPU / torch | — | not needed | — | — |

**Missing dependencies:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `~=9.0` (`pyproject.toml [project.optional-dependencies].dev`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`) |
| Quick run command | `.venv/bin/pytest tests/test_phase28_report.py tests/test_phase28_ledger.py tests/test_package.py tests/test_phase18_docs.py tests/test_phase15_docs.py -q` (seconds) |
| Full suite command | `make test` (= `.venv/bin/pytest -q`), 21-24 min, committed tree only, `run_in_background` |
| Lint | `make lint` |

### Phase Requirements → Test Map
| Req / SC | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RPT-01 / SC1 | lead quotes `capacity_branch` + both existentials + `cleared_counts`; expectation quoted verbatim | unit (record + `_prose`) | `pytest tests/test_phase28_report.py -k "lead or expectation" -x` | ❌ Wave 0 |
| RPT-01 / SC1 | "recorded before any run": quote present at `c673b4c`; `c673b4c` ≺ earliest `results/phase2[0-8]_*` add; shallow clone refuses | unit (git) | `pytest tests/test_phase28_prereg.py -k ancestry -x` | ❌ Wave 0 |
| RPT-01 / SC2 | re-render == committed bytes (REPORT block, README block) | unit | `pytest tests/test_phase28_report.py -k byte_identical -x` | ❌ Wave 0 |
| RPT-01 / SC2 | template source has no bare numeral outside D-19 grammar (+ planted RED probe) | unit | `pytest tests/test_phase28_report.py -k template_scan -x` | ❌ Wave 0 |
| RPT-01 / SC2 | every ε/σ/C/q/δ/K binding equals its module constant (`F_Y 0.7`, `F_C 0.5`, `MARGIN_K 2`, `CURVE_K 16`, `FULL_FIDELITY_K 48`, `K 48`, `DELTA 1e-5`, `SAMPLING_RATE_Q 1.0`, `CLIP_NORM`, `STEP_BUDGET 200`, `SIGMA_LADDER`) and the record | unit | `pytest tests/test_phase28_report.py -k constants -x` | ❌ Wave 0 |
| RPT-01 / SC2 | all 14 obligation paths resolve; `<artifact absent>` clause satisfied by the file's existence | unit | `pytest tests/test_phase28_report.py -k obligation -x` | ❌ Wave 0 |
| RPT-01 / SC2 | prose checks route through `normalized` (AST register grows to include the Phase 28 files) | unit | `pytest tests/test_phase25_correction.py::test_the_register_is_three_files_wide -x` (update its register) | ✅ (edit) |
| RPT-01 | appended section keeps every prior `## ` heading in order; README bullets add no heading | existing | `pytest tests/test_phase18_docs.py tests/test_phase15_docs.py -q` | ✅ |
| RPT-01 / SC2 | source digests in the block equal `sha256(read_bytes())` at HEAD | unit | `pytest tests/test_phase28_report.py -k provenance -x` | ❌ Wave 0 |
| RPT-03 / SC3 | `[project].dependencies` equal at `v1.0`, `v2.0`, `v3.0`, HEAD | unit (git + tomllib) | `pytest tests/test_package.py -k dependencies -x` | ❌ (add to existing file) |
| RPT-03 / SC3 | sha pin renamed (D-26), still bytes | unit | `pytest tests/test_package.py -x` | ✅ (rename) |
| RPT-03 / SC3 | ledger schema: six required keys, closed disposition domain, `FIXED` rows name a test node id that exists in `--collect-only`, counts = `len()` | unit | `pytest tests/test_phase28_ledger.py -x` | ❌ Wave 0 |
| RPT-03 / SC3 | D-32 docstring fixes hold | unit | `pytest tests/test_perplexity.py tests/test_phase16_driver.py -k docstring -x` (new tests) | ❌ (add) |
| SC4 | confound strings are the record's own (`adversarial_no_replay.*`, `amended_criterion`, §12.5c slice under `normalized`) | unit | `pytest tests/test_phase28_report.py -k confound -x` | ❌ Wave 0 |
| D-31/D-39 | `gsd-sdk query audit-open` count drops from 9 to the intended residue; `verify.artifacts` on the 5 Phase-19 plans passes | manual-CLI (recorded in ledger evidence) | `gsd-sdk query audit-open`; `for p in …19-{08,09,12,13,16}-PLAN.md; do gsd-sdk query verify.artifacts "$p"; done` | n/a |
| D-38 | green CI on `origin/main` after push | human checkpoint | `gh run list --branch main --limit 1` → run id into ledger | n/a |

### Sampling Rate
- **Per task commit:** the quick run command above + `make lint` (< 1 min).
- **Per wave merge:** `make test` uncapped, background, on the committed tree (21-24 min); never with untracked `results/`/`tests/`/`scripts/` files present.
- **Phase gate:** full suite green locally AND the D-38 CI run green before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_phase28_report.py` — byte-identity, template scan (+ planted RED), obligation resolution, constants, provenance, confound, lead/expectation
- [ ] `tests/test_phase28_prereg.py` — D-05 ancestry (copy `_assert_frozen_before` shape) — or fold into the file above
- [ ] `tests/test_phase28_ledger.py` — schema/domain/`FIXED`-has-test/`len()` counts
- [ ] `tests/test_package.py` — D-25 test added, D-26 rename
- [ ] docstring tests for D-32 (`tests/test_perplexity.py`, `tests/test_phase16_driver.py` or a new small file)
- [ ] Framework install: none — pytest present

## Security Domain

`security_enforcement` is not set to `false` in `.planning/config.json` → section included. This phase writes no network, auth, or user-input code; the threat surface is provenance integrity and evidence tampering.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes (records → prose) | strict dotted-path resolution (`KeyError` on absence), `string.Template.substitute` (raises on a missing binding), template scan refuses bare numerals |
| V6 Cryptography | yes (integrity) | `hashlib.sha256` over `read_bytes()` for every source record; never hand-roll |
| V14 Configuration | yes | zero new deps (D-25 test); no `pip install`; CI unchanged |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Re-emitting or editing a committed record to change the report | Tampering | `test_the_record_is_pinned_to_the_frontier_both_ways` (frontier one commit), block carries source sha256s, provenance test recomputes from bytes |
| Post-publish re-render rewriting published prose | Repudiation | D-20 frozen block; byte-identity test; corrections via `append_addendum` only |
| Hand-typed numeral slipping into prose | Tampering (of evidence) | D-18 template-source scan with planted RED |
| Shallow clone making ancestry tests vacuous | Repudiation | `rev-parse --is-shallow-repository == "false"` assertion (existing pattern); CI `fetch-depth: 0` |
| Ledger "disposition recorded" read as "fixed" | Repudiation | closed domain (D-29); `FIXED` requires a test node id that `pytest --collect-only` resolves |
| Reading the gitignored `logs/phase25_sweep.out` | Information disclosure / non-reproducibility | D-10: quote `log_line`/`log_source` fields only |

## Sources

### Primary (HIGH confidence — read from disk / git this session)
- `scripts/_prose.py`, `scripts/_addendum.py`, `scripts/_verdict.py` (full files)
- `scripts/phase25_prereg.py:410-520`, `scripts/phase26_prereg.py:345-395`, `scripts/mitigation_gate.py` / `mitigation_budget.py` / `mitigation_unit.py` constants (imported), `src/personacore/privacy/accountant.py:819,988` (called), `scripts/phase18_extraction.py:93,98,173`, `scripts/phase19_erasure.py:2557-2560,2996,3092-3093`
- `results/phase25_frontier.json`, `results/phase26_canary.json`, `results/phase27_admission.json`, `results/phase23_{cost,sigma_zero,control_floor}.json` (parsed with `json`), `results/phase25_operational_note.md:1036-1066`
- `tests/test_phase18_docs.py`, `tests/test_phase15_docs.py`, `tests/test_phase19_docs.py`, `tests/test_package.py`, `tests/test_phase27_prereg.py:57-131`, `tests/test_phase25_correction.py`, `tests/test_phase24_record.py:288-330`, `tests/test_phase16_prereg.py:50-90`, `tests/test_phase20_prereg.py:135-170`, `tests/test_phase23_prereg.py:555-600`, the census tests listed in §7, `tests/test_perplexity.py:118-124`, `tests/test_phase14_scoring.py:517`
- `.github/workflows/ci.yml`, `Makefile`, `pyproject.toml`, `.gitignore`, `git show v{1.0,2.0,3.0}:pyproject.toml`, `git diff v3.0 HEAD -- pyproject.toml`, `git log`/`merge-base` for `c673b4c`/`9bb34ad`, `git show c673b4c:.planning/research/SUMMARY.md`
- `.planning/milestones/v3.0-MILESTONE-AUDIT.md:1-251`, `.planning/MILESTONES.md`, `.planning/STATE.md:1504-1690`, `.planning/REQUIREMENTS.md:440-600`, `.planning/ROADMAP.md:1-20,75-90,1072-1125`, `27-REVIEW.md` headings, `27-HUMAN-UAT.md`, `25-HUMAN-UAT.md`, `24-HUMAN-UAT.md`, `23-HUMAN-UAT.md`, the pending todo, `.planning/quick/*`, `.planning/debug/*`, the five Phase-19 PLAN files via `gsd-sdk query verify.artifacts`
- `~/.npm/_npx/…/get-shit-done-cc/sdk/dist/query/audit-open.js:11-100,270-350` and `~/.claude/get-shit-done/bin/lib/audit.cjs:78-160` (tool semantics for D-31/D-39)
- `gsd-sdk query audit-open` (9 items), `gsd-sdk query init.phase-op 28`, `gh run list --branch main --limit 3`

### Secondary / Tertiary
- none — no web sources used.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, all verified importable in the venv
- Architecture: HIGH — every reusable asset located by path and line; record layouts dumped
- Pitfalls: HIGH — each is a measured property of the tree (null verdicts, census globs, heading guard, tool filename rule)

**Research date:** 2026-09-20
**Valid until:** until `results/phase25_frontier.json` (one-commit guard), the obligation modules, or the GSD sdk change — in practice the life of the phase; re-measure `origin/main` distance and `audit-open` counts at plan execution.
