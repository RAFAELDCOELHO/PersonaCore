# Phase 29: v5.0 Pre-Registration and Carried Debt - Context

**Gathered:** 2026-09-24
**Status:** Ready for planning — with ONE ruling checkpoint (D-15, GATE-08) the plan must stop at

<domain>
## Phase Boundary

One CPU-only v5.0 pre-registration module, ancestry-guarded ahead of every v5.0 results artifact,
that fixes — as code, before any v5.0 number exists — the 12 point keys, every v5.0 results path,
the replay recipe (imported), the frozen v4.0 gate route (imported), the unlearnable-own-control
refusal, and the full admission contract including the conditional relearning scope rule. Plus
the four v5.0-owned debt items (DEBT-01..04). No training, no scoring, no MPS time; no v5.0 number
is produced in this phase.

Requirements: PREREG-01, PREREG-02, PREREG-03, PREREG-04, DEBT-01, DEBT-02, DEBT-03, DEBT-04.

</domain>

<decisions>
## Implementation Decisions

### Keys, paths, and the imports (PREREG-01, PREREG-04)
- **D-01:** The 12 v5.0 keys use NEW ARM NAMES (`advr_n8`, `advr_n64`) through the existing
  `phase25_record.point_key(arm, value)` over the frozen `ADVERSARIAL_RATIO_GRID` — e.g.
  `advr_n8_ratio0p250000`. The key itself differs from v4.0's `adv_*`, not only the file path, so
  no arm-keyed reader can confuse a v4.0 and a v5.0 point. Point records live at
  `results/phase32_point_<key>.json`. (Researcher: verify `point_key` / `ADVERSARIAL_ARMS` accept
  a new arm without editing a frozen v4.0 module; if not, the v5.0 module wraps it, never edits it.)
- **D-02:** The ancestry guard covers EVERY v5.0 results file — `results/phase3[0-4]_*`, including
  Phase 30's calibration and Phase 31's probe records — matching SC1's "precedes every v5.0
  results artifact" literally.
- **D-03:** EVERY v5.0 results path is pinned in this module now (points, promotion records if
  any, frontier, admission, Phase 30 calibration, Phase 31 probes). The guard glob is derived from
  that one list, not typed separately, and a test proves no probe/calibration path parses as a
  point key (ARCAL SC4).
- **D-04:** `REPLAY_WINDOWS_PER_FACT` is imported LAZILY: a `replay_windows(n)` function imports
  `teach_persona` only when called (the `phase27_prereg.attacker_corpus_rows` precedent), so the
  module stays torch-free at import. An AST guard reddens if a numeric literal equal to the
  constant, or a module-level assignment of that name, appears in the pre-registration. Replay =
  `REPLAY_WINDOWS_PER_FACT`·n windows from `data/dialog_train.bin`, identical to the DP arms.
- **D-05:** The frozen v4.0 gate is imported as the sanctioned ROUTE,
  `phase20_gate_coverage.corrected_point_verdict` — never `mitigation_gate.mitigation_point_verdict`
  directly (the caller census in `tests/test_phase20_correction.py` forbids that from `scripts/`).
  An AST guard reddens if the gate or the grid is re-typed.

### Admission contract (PREREG-02) — frozen in full NOW
- **D-06:** Phase 29 freezes the WHOLE admission contract as code; Phase 33's ADMIT module only
  imports it and calls it once. Nothing about admission is decided after the v5.0 frontier exists.
  Contract: expected point count 12; ADMITTED iff ≥1 stored PASS (naming every PASS key in key
  order); INCONCLUSIVE (malformed record / counts that do not re-derive) takes precedence;
  threshold = `F_Y` × the taught-recall COUNTS of the arm's OWN `advr` ratio-0 control at that
  capacity — never a `dp_*` reading (WR-05).
- **D-07:** New 4th admission verdict **REFUSED**: when EVERY point is REFUSED, admission reads
  REFUSED — never MOOT — carrying each leg's control reading. Relearning then ships as a named
  limitation whose reason is "the frontier could not be measured", never "the mitigation held".
  INCONCLUSIVE keeps its narrow meaning (malformed / non-re-deriving record).
- **D-08:** Mixed case (one leg REFUSED, the other measured with zero PASS) reads **MOOT**, with the
  reasons naming the refused leg and its reading; the report never extends MOOT to the refused
  capacity.
- **D-09:** Relearning parameters for any admitted point (rungs, band, K, the seven baselines,
  attacker corpus, recovery fixture) are IMPORTED from `phase27_prereg` unchanged — frozen before
  any data and never run. v5.0 changes only the arm key and the control source.
- **D-10:** The scope rule itself: every admitted point runs RELRN-06..09; zero admitted ⇒
  RELRN-06..09 ship as a MOOT (or, per D-07, REFUSED) named limitation. Which branch runs is the
  admission record's output.

### Unlearnable own-control refusal (PREREG-03)
- **D-11:** The refusal is the route's existing precondition: `control_taught_recall` or
  `control_heldout_recall` of the leg's `advr` ratio-0 control outside (0,1] ⇒ the whole capacity
  leg is REFUSED (every point in the leg sources its floors from that control).
- **D-12:** SHORT-CIRCUIT: the control runs first (ACTRL-02); if it comes back outside (0,1], the
  leg's other 5 points are NOT trained — each key gets a write-once REFUSED record citing the
  control's reading. Phase 31's budget must cover both branches.
- **D-13:** The REFUSED record carries: the control's taught and held-out recall as k/n COUNTS
  (never bare rates), the recipe identity (replay windows, n, seed, budget), and the v4.0 `adv_n64`
  reading beside it (held-out 0/648) so the report can say whether replay moved the floor.
- **D-14:** "Not re-tuned" is enforced structurally: the 12 keys are the complete set, write-once,
  with no alternate/retry key — a test reddens if the pre-registration exposes one. A different
  recipe needs a new pre-registration in a new milestone. (Phase 30's ARECIPE-02 already refuses a
  point whose recipe differs from the calibration's.)

### GATE-08 — RULING CHECKPOINT (premise gap found in discussion)
- **D-15:** The frozen gate (`mitigation_gate.py:822`, GATE-08 / D-29) returns INCONCLUSIVE — not
  PASS — for a point clearing (a)(b)(c) without second-seed replication; v4.0 set
  `REPLICATED_AT_SECOND_SEED = False` and made promotion (`phase25_promotion`, K=48 redraw +
  second-seed replication) the only path to PASS. The v5.0 roadmap has no promotion step, so under
  D-06 v5.0 could never admit. **Developer ruling: the researcher MUST confirm that GATE-08 and
  `phase25_promotion` work as described, and that the promotion route can genuinely be imported for
  the `advr` arms — without structural modification and without a hidden dependency on the `dp_*`
  arms that does not generalise. The plan STOPS at a checkpoint for the developer's decision with
  that confirmation in hand.** If the route imports cleanly, option 1 (pre-register promotion:
  candidates promoted through the imported v4.0 route under their own write-once promotion keys,
  budgeted in Phase 31, run in Phase 32, admission reading the promoted verdicts) is the natural
  answer. If there is real import friction, the choice between 1 (adapt promotion) and 2 (no
  promotion; a would-be PASS stays INCONCLUSIVE and admission gets a distinct
  candidate-unreplicated reading, never MOOT, shipped as a named limitation) is made with the
  friction visible, not assumed. Nothing D-15-dependent may be committed to the pre-registration
  before that ruling.

### Carried debt (DEBT-01..04)
- **D-16 (DEBT-01):** the relearn test monkeypatches `relearn._ROOT` to a scratch repository (the
  27-REVIEW IN-07 prescription); a guard proves no `results/phase27_*` file is touched.
- **D-17 (DEBT-02):** keep published bytes. A `d28_note()` reader in `arm_d_qualifier()`'s shape
  reads the D-28 READING QUALIFICATION blockquote from 16-CONTEXT.md at runtime; a test compares it
  to what the code/report carry, so an amended note reddens. No frozen report block is re-rendered.
  If the published text lacks the verbatim note, the test records that as a named limitation rather
  than rewriting history.
- **D-18 (DEBT-03):** backfill all 11 archived Phase-17 SUMMARYs: `completed` = the author date of
  each SUMMARY's first-add commit (`git log --diff-filter=A`), measured; `duration` = an explicit
  "not recorded at the time" value the validator accepts — no invented number. Researcher: verify
  no guard/pin/content test reads those SUMMARY bytes before editing archived files.
  **Amended 2026-09-24 (plan-phase, developer ruling):** premise false — all 11 SUMMARYs already
  carry `duration` and `completed` nested under `metrics:` (validator checks top-level only). Close
  DEBT-03 by copying the nested values up to top-level `duration:`/`completed:`, leaving `metrics:`
  untouched; the test asserts top-level == nested == the `git log --follow --diff-filter=A` first-add
  date. The "not recorded at the time" value is withdrawn (it would contradict the recorded data).
- **D-19 (DEBT-04):** P22-WARNING-4/5 is re-recorded as a committed named-limitation entry in the
  v5.0 pre-registration module (reason: no v5.0 number uses the accountant; the adversarial arm
  carries no ε claim, Phase 25 D-01), ancestry-guarded ahead of every number, with a test that no
  v5.0 module imports the accountant. Zero change to the accountant; Phase 34 renders the entry.
  `results/phase28_ledger.json` is frozen and not touched.

### Claude's Discretion
- Module name/layout (one module vs. a split admission submodule), test file names, the exact
  AST-guard mechanics, and DEBT-01's scratch-repo fixture shape — follow the phase26/27 prereg
  register.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` §"Phase 29" (lines ~1161-1192) — goal + 4 success criteria
- `.planning/REQUIREMENTS.md` §"v5.0 Requirements" (appended below the frozen v4.0 sections — never edit above the rule)

### Pre-registration precedent (copy the register, not the numbers)
- `scripts/phase27_prereg.py` — module docstring register, `_prove`→SystemExit, lazy imports, `relearning_is_worth_attempting` (admission), `recall_threshold` (dp-sourced — the v5.0 version must be arm-keyed), relearning pins to import
- `tests/test_phase27_prereg.py`, `tests/test_phase26_prereg.py` — ancestry-guard pattern
- `scripts/_addendum.py` — the only correction route after the first record (dated continuation)

### Frozen v4.0 inputs (import, never copy, never edit)
- `scripts/mitigation_budget.py:633` — `ADVERSARIAL_RATIO_GRID`
- `scripts/teach_persona.py:179` — `REPLAY_WINDOWS_PER_FACT` (module imports torch at load)
- `scripts/phase20_gate_coverage.py:522` — `corrected_point_verdict`, the sanctioned route; (0,1] precondition
- `tests/test_phase20_correction.py` — caller census on `mitigation_point_verdict`
- `scripts/mitigation_gate.py:822` — GATE-08 replication rule
- `scripts/phase25_promotion.py` — `REPLICATED_AT_SECOND_SEED`, promotion route (D-15 subject)
- `scripts/phase25_record.py:158,199,253` — `ADVERSARIAL_ARMS`, `point_key`, `ORDERED_POINT_KEYS`
- `results/phase25_frontier.json` — v4.0 adv_n64 REFUSED reading (held-out 0/648)

### Debt sources
- `results/phase28_ledger.json` rows IN-07, TD-16-R1, TD-17-SUMMARY-FRONTMATTER, P22-WARNING-4, P22-WARNING-5 (frozen — read only)
- `tests/test_phase27_relearn.py:182-194`, `scripts/phase27_relearn.py:37` — DEBT-01
- `scripts/phase16_persistence.py:1988-2045` (`MONOTONE_CLAIM_*`, `_CONTEXT_PATH`, `arm_d_qualifier`) and `.planning/milestones/v3.0-phases/16-weight-vs-prompt-persistence-control/16-CONTEXT.md:267+` — DEBT-02
- `.planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix/17-*-SUMMARY.md` (11 files) — DEBT-03
- `22-VERIFICATION.md:149-183` (archived under `.planning/milestones/v4.0-phases/22-*`) — DEBT-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `phase25_record.point_key` — key rendering with non-finite/negative refusal
- `phase20_gate_coverage.corrected_point_verdict` — verdict + unlearnable-control refusal in one route
- `phase27_prereg` admission gate + relearning pins — import for D-06/D-09
- `phase16_persistence.arm_d_qualifier` — runtime-verbatim reader pattern for D-17
- `_addendum.py` — continuation writer

### Established Patterns
- Stdlib-only at import; torch-importing originals asserted equal in tests, or imported lazily
- Ancestry guard: every commit touching the prereg is a strict ancestor of the first-add of every guarded results file
- Write-once records; a second write refuses
- Zero `gsd-sdk` mutation handlers — STATE/ROADMAP/REQUIREMENTS edited by hand (snapshot + diff)

### Integration Points
- Phase 30 (train seam, ARECIPE-02 calibration path), Phase 31 (probe paths), Phase 32 (point/frontier/promotion paths), Phase 33 (imports the admission contract) all consume this module's pinned names

</code_context>

<specifics>
## Specific Ideas

- The developer's framing for D-07: v4.0's MOOT was backed by real measured dp capacities; if both
  v5.0 legs are refused, no real result stands behind the label, so it must not read MOOT.
- D-15 is the developer's explicit instruction: decide promotion with the real import friction
  visible, not on assumption.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (D-15 may add a promotion leg to Phases 31/32 depending
on the ruling; that is an application of the frozen gate, not a new capability.)

</deferred>

---

*Phase: 29-v5-0-pre-registration-and-carried-debt*
*Context gathered: 2026-09-24*
