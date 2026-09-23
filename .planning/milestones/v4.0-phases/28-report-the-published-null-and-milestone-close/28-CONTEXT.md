# Phase 28: Report, the Published Null, and Milestone Close - Context

**Gathered:** 2026-09-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 28 delivers three things and stops:

1. **One appended section in `docs/REPORT.md`** publishing v4.0 as it measured: the DP null at both
   capacities on its own surface, the adversarial arm as explicitly recipe-confounded, the canary
   audit, the relearning MOOT reading, the milestone's corrections of its own premises, a ship
   block, and the named-limitation register. Plus rendered `Results at a glance` bullets in
   `README.md` (v3.0 and v4.0), which closes v3.0 cross-cutting debt item 4.
2. **The generation mechanism that makes SC2 structurally true**: a committed template whose every
   number is a named binding to a record field path or a module constant, a renderer, a
   byte-identity re-render test, a template-source scan that refuses a hand-typed numeral, and
   `scripts/_prose.normalized` on every cross-surface prose check.
3. **`results/phase28_ledger.json` + RPT-03**: one disposition row per open item across v3.0 (16
   tech-debt + 6 stale stamps) and v4.0 (RELRN-02..05, Phase 27's review findings, Phase 22's
   WARNING-4/5, FRONT-04's weaker form, 23-17 unticked, the adv_n64 refusal), plus a mechanical
   four-milestone zero-new-runtime-dependency test.

**Out of scope — named, not overlapped:** `PROJECT.md`'s "Current State (v4.0 shipped)",
`MILESTONES.md`, the `v4.0` tag and milestone archival all belong to `/gsd-complete-milestone`;
the milestone audit belongs to `/gsd-audit-milestone`. No new measurement, no training run, no
re-emission of any committed record, no edit to any ancestry-frozen module, and no `adv_*`
admission (WR-05 defers that to v5.0).

**The measured facts that shape the phase.** `results/phase25_frontier.json` reads
`capacity_branch = "null-at-both-capacities"` with tallies PASS 0 / FAIL 32 / INCONCLUSIVE 6 /
REFUSED 6; `results/phase27_admission.json` reads MOOT with `cleared_counts` a 30 / b 4 / c 1 over
38 reached; `results/phase26_canary.json` reads 15 CONSISTENT / 0 BROKEN / 0 INCONCLUSIVE with
`reachable_claims` 4/15. Every noised DP point (30 of 30) cleared (a) at zero extraction and none
cleared (b): **DP removed the leakage by removing the memory.** Three roadmap premises were
measured during this discussion and two are false as written — see D-27 and D-09.

</domain>

<decisions>
## Implementation Decisions

**Thirty-nine decisions across four areas. Every one is LOCKED** — researcher and planner act on
them rather than re-open them. Every measured figure below was read from the artifact named beside
it during this discussion.

### Area A — What the report publishes, and where (RPT-01, SC1, SC4)

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

### Area B — Generated, not authored (RPT-01, RPT-02, SC2)

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

### Area C — RPT-03 and the debt ledger (RPT-03, SC3)

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

### Area D — Where milestone close ends

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and requirements
- `.planning/ROADMAP.md` — Phase 28 block (goal, SC1–SC4), the v4.0 milestone overview
  (`:78-84`, the expected-null paragraph), the v5.0 candidate entry (`:9-13`), and the Progress
  table row this phase updates
- `.planning/REQUIREMENTS.md` — RPT-01 / RPT-02 / RPT-03 rows (`:447-457`), the Traceability table,
  the Future Requirements list (the 16 + 6 carry-forward and the
  `scripts/phase18_extraction.py:85-87` comment debt), and the 23-12 continuation
- `.planning/PROJECT.md` — "Current Milestone: v4.0", the pre-registration boundary paragraph, and
  the Key Decisions table (honest negatives, structural enforcement, plot-from-committed-artifact)

### The committed publication contract (this phase's pre-registration)
- `scripts/phase25_prereg.py` — `PUBLICATION_OBLIGATION_SCOPE` (`:414`), `PUBLICATION_OBLIGATION`
  (`:424`, 8 pairs incl. both limitations), `CANARY_RESERVATIONS.canary_population_rule`
- `scripts/phase26_prereg.py` — `SUPERSEDES_OBLIGATION` (`:352`),
  `PUBLICATION_OBLIGATION_CONTINUATION` (`:354`, 7 pairs incl. the `<artifact absent>` clause),
  `VERDICTS`, the ancestry-guard pattern
- `scripts/phase27_prereg.py` — the admission gate, `ARTIFACT_GLOB`, and its "Phase 28 quotes the
  record, never this prose" clause (`:10-11`)

### Records the report is generated from
- `results/phase25_frontier.json` — `verdicts.capacity_branch`, `verdicts.arm_existentials`,
  `verdicts.tallies` / `tallies_by_leg`, `verdicts.amended_criterion`,
  `verdicts.adversarial_no_replay`, `verdicts.pre_registered_null`, `verdicts.dp_recall_disclosure`,
  `epsilon_report.*` (`curve_total_epsilon`, `selection_accounted`, `summands`,
  `control_has_no_epsilon`), `points.<key>.verdict`, `points.<key>.refusal`
- `results/phase26_canary.json` — `summary`, `reachable_claims`, `auditor_ceiling`, `power_gate`,
  `exclusions`, `audited_point_keys`, `curve_total_is_context_only`, `points.<key>.verdict`
- `results/phase27_admission.json` — `verdict`, `tallies`, `tallies_by_leg`, `cleared_counts`,
  `rows`, `apparatus`, `baselines`, `frontier_sha256`, `provenance`
- `results/phase25_operational_note.md` §12.5c — the no-replay finding (quoted, never re-derived)
- `results/phase23_cost.json`, `results/phase23_sigma_zero.json`,
  `results/phase23_control_floor.json` — D-12's self-corrections
- `results/phase25_frontier_dp.png`, `results/phase25_frontier_adversarial.png` — D-14's figures
- `.planning/research/SUMMARY.md` at `c673b4c` (`:39-41`, `:388-396`) — the standing expectation

### Publication surfaces and their existing discipline
- `docs/REPORT.md` — append-only structure; the Phase 18 section (`:1062`) is the house style for a
  quoted verdict; `:424` and `:1145` are frozen-above-this-line assertions the append must respect
- `README.md` — `## Results at a glance` (`:109-147`, v2.0-only, debt item 4), the dated-section
  precedent (`:316`), `## Repository status` (`:402`)
- `scripts/_prose.py` — `normalized`, the one copy (RPT-02)
- `scripts/_addendum.py` — `append_addendum(path, addendum, *, pending, recorded)`, both keywords
  required, refuses a second append — D-20's correction route
- `scripts/_verdict.py` — anchored verdict-section read, for any clobber check

### Code the tests and renderer call
- `src/personacore/privacy/accountant.py` — `epsilon_for(sigma, steps, delta)` (`:819`),
  `sigma_for(target_epsilon, steps, delta)` (`:988`)
- `scripts/mitigation_gate.py` — `extraction_ceiling`, `F_Y`, `dialogue_gap_band`, `retention_cap`,
  `CAPACITY_BRANCHES`, `V4_VERDICTS` (the constants SC2's ε/σ/C/q/δ test resolves against)
- `scripts/mitigation_budget.py` — `CURVE_K`; `scripts/phase18_extraction.py` — `K = 48`,
  `GATED_TIER` (read, never edited — ancestry-frozen)
- `tests/test_package.py` — `PYPROJECT_SHA256` pin and the test D-26 renames
- `tests/test_phase26_prereg.py` / `tests/test_phase27_prereg.py` — `_assert_frozen_before`, the
  shallow-clone refusal, the ancestry-guard shape D-05 copies
- `tests/test_phase18_docs.py`, `tests/test_phase15_docs.py` — doc-test precedents (verbatim claim
  in three surfaces, headline numbers matched to sources, additive-append proofs)
- `tests/test_phase25_plots.py` — the plotter guards D-14 relies on
- `.github/workflows/ci.yml` — `fetch-depth: 0` (`:28`), the two jobs D-38's checkpoint watches

### Prior-phase context carried forward
- `.planning/phases/27-relearning-attack/27-CONTEXT.md` — D-05 (the RELRN-02..05 limitation),
  D-07 (MOOT reasons generated, not authored), D-11, D-38 (hand-edit ledger posture)
- `.planning/phases/27-relearning-attack/27-HUMAN-UAT.md` +
  `.planning/todos/pending/phase28-carry-phase27-latent-review-findings.md` — the folded ruling
- `.planning/phases/26-empirical-privacy-audit-canary/26-CONTEXT.md` — D-18 (ε beside its verdict),
  D-19 (the "audit not executed / partial" clause), D-13 (the ceiling disclosure)
- `.planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md` — D-40 (the
  publication obligation), D-23/D-29 (the two limitations), D-39 (the refusal-rate column)
- `.planning/milestones/v3.0-MILESTONE-AUDIT.md` — the 16 tech-debt items (frontmatter
  `tech_debt:`), N1/N2, and the "prose volume is the mechanism" finding
- `.planning/STATE.md` — "Deferred Items" (the 6 stale stamps and why v3.0 acknowledged rather than
  resolved them)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/_prose.py::normalized` — the only prose-comparison primitive (SC2's third clause).
- `scripts/_addendum.py::append_addendum` — D-20's dated-continuation route; refuses a second
  append, which is exactly the property a frozen-at-publish block needs.
- `personacore.privacy.accountant.sigma_for` / `epsilon_for` — stdlib-only, CPU-cheap, import-safe
  in a renderer (Phase 22 proved the module's import set is `{math}`).
- `phase25_prereg.PUBLICATION_OBLIGATION` + `phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION` —
  15 `(field_path, why)` pairs; the resolve-every-path test is the phase's central guard.
- `tests/test_phase2{6,7}_prereg.py::_assert_frozen_before` + the `rev-parse
  --is-shallow-repository` refusal — copy the mechanism for D-05.
- `tests/test_phase24_record.py`'s bytes-recompute provenance guard — the shape for pinning source
  record digests inside a rendered block.
- `tomllib` (stdlib, 3.11) — D-25's parser; no dependency is added by RPT-03's own test.

### Established Patterns
- **Records are generated, never authored; prose quotes them by sha256.**
- **Counts never rates; every quantity carries numerator, denominator and source.**
- **Honest negatives stand unamended; corrections are separate, dated, additive.**
- **Structural enforcement replaces declared invariants** — a scan that refuses a hand-typed
  numeral is the D-18 instance of this.
- **AST/structural gates, never grep, over files whose prose discusses the measured term** — the
  template scan must not be a naive regex over a file that talks about numerals.
- **Ledger edits by hand, snapshot-and-diff, zero `gsd-sdk` mutation handlers.**
- **A refusal is watched RED before it is trusted** — every new guard here gets its natural or
  planted RED recorded.

### Integration Points
- `docs/REPORT.md` — one appended section with the rendered block(s) (new).
- `README.md` — rendered `Results at a glance` bullets inserted, zero deletions.
- `results/phase28_ledger.json` — new, the only new artifact; no gate, no prereg module (D-23).
- `scripts/phase28_report.py` + its template — new renderer.
- `tests/test_phase28_*.py` — new: obligation-path resolution, byte-identity re-render,
  template-source numeral scan, ε/σ/C/q/δ constant match, the D-05 ancestry test, the D-25
  dependency test, ledger schema + disposition-domain closure.
- `tests/test_package.py` — renamed test + D-25's dependency comparison.
- `src/personacore/evaluation/perplexity.py`, `scripts/phase16_persistence.py` — D-32's two safe
  docstring fixes, each with a test.
- `.planning/REQUIREMENTS.md` (RPT-01/RPT-03 ticks), `.planning/ROADMAP.md` (Phase 28 row),
  `.planning/STATE.md` — hand-edited at close (D-34).
- `.planning/phases/24-.../24-HUMAN-UAT.md` (dated note, D-37),
  `.planning/phases/25-.../25-HUMAN-UAT.md` (stamp, D-36).

</code_context>

<specifics>
## Specific Ideas

- **"One source, two renderings."** The ledger is the single source; the named-limitation register
  is that same data filtered on `disposition == NAMED-LIMITATION`. Never two files that could
  diverge.
- **"A name that asserts something false does not survive"** — the reason D-26 renames the pyproject
  test rather than leaving a correct pin behind a wrong name.
- **"Checks the source before rendering happens, not the rendered result by value"** — D-18's whole
  point; value-matching a numeral is the weak version this phase deliberately rejects.
- **"Never conflate disposition recorded with fixed"** — D-29's closed domain exists to make that
  distinction machine-readable rather than a matter of tone.
- **"Repair only what makes a tool report an active error"** — D-31's boundary: the real, active
  cost gets closed; historical prose imperfections stay recorded, protecting the audit trail.
- The null must be unskippable: a reader who reads only the first three lines learns that nothing
  cleared all three conditions at either capacity, why (DP removed the memory with the leakage), and
  that the n=64 branch is the weaker null because its own control learned 87/1008.

</specifics>

<deferred>
## Deferred Ideas

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

</deferred>

---

*Phase: 28-report-the-published-null-and-milestone-close*
*Context gathered: 2026-09-17*
