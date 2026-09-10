# Phase 26: Empirical Privacy Audit (Canary) - Context

**Gathered:** 2026-09-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 26 delivers an **empirical lower bound on ε** for published DP points of
`results/phase25_frontier.json`, a rule **committed before the audit runs** that declares the
from-scratch DP-SGD implementation *provably broken* when the measured ε_lower exceeds the ε_upper
the accountant claims, the comparison **executed and published whichever way it comes out**, and the
verdict travelling **with** the frontier artifact — or, if the audit is cut, a **named limitation**
under the D-16 discipline (a negative decision carries a positive's weight), never silence.
Requirements: CANARY-01, CANARY-02. Nothing else is built here: no new training, no new attack
family, no relearning (Phase 27), no report (Phase 28).

**Measured facts the phase must face — read from the artifact on 2026-09-10, not argued:**

1. **The committed target rule resolves to the σ=0 control.**
   `phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` restricts to n=8, takes the first PASS,
   and in the null case (no n=8 PASS — the pre-registered null that was reached) takes the first n=8
   point in `point_keys`: `dp_n8_sigma0p000000`, whose record carries `epsilon: null`
   (`epsilon_omitted_reason` present). CANARY-02's comparison is **vacuous** at the committed target.
2. **Every noised DP n=8 point learned nothing by every instrument.** All 15 (`σ` 0.5 … 80):
   `taught_recall` 0/1008, `heldout_recall` 0/648, extraction 0/416 on the gated tier, 0 answered on
   the reported tier, GATE-05 exposure at chance (rank 3–5 of 8, ε_bits 0.26–1.58) already at σ=0.5.
   The σ=0 control: 790/1008 taught, 346/648 held-out, 285/416 extraction, all eight slots at rank 1.
   Any membership distinguisher returns ε_lower ≈ 0 on the noised points and a large ε_lower on the
   control.
3. **The 56 OUT canaries (filler) have never been scored by any instrument.** Both extraction tiers
   at both capacities (`core_held_out` 416 rows, `core_taught` 448 rows) cover only the 8 locked
   slots; `phase18_extraction.py` is ancestry-guarded and D-18 (Phase 21) keeps filler out of its
   10-value leak vocabulary; `phase25_gate05.FILLER_EXPOSURE_OMITTED` records that Carlini exposure
   is unmeasurable on filler (no reference set). The teaching side can render filler prompts:
   `phase14_factset.render_family(family_id, fact, forms=phase21_filler.FILLER_SLOT_FORMS)`.
4. **Published ε_upper on the 15 noised n=8 points, per point at δ=1e-5** (`epsilon`, via
   `personacore.privacy.accountant.epsilon_for(sigma, steps=200, delta)`): 519.70, 289.34, 159.44,
   83.83, 54.38, 30.51, 20.68, 12.26, 8.60, 5.30, 3.80, 2.40, 1.74, 1.06, 0.634 (σ = 0.5 → 80).
   Curve total 2387.30 at δ=3e-4 (basic composition over 30 summands, both capacities).
5. **Cost.** Per point: training ~218 s (not repeated — adapters are retained), recall scoring
   ~914 s at n=8 for IN on+off (1008+648 draws per arm, 9 draws/question). Adapters for all 16
   `dp_n8` points are on disk under `checkpoints/phase25_sigma*_dp_n8_adapter.pt` and hash to the
   `adapter_sha256` in their records (the target was re-hashed on 2026-09-10: matches).
6. **The bounds already in the repo, with z one-sided 95% (`erasure_gate._Z_ONE_SIDED_95` =
   1.6448536269514722), δ=1e-5** — computed on 2026-09-10 with the imported functions:

   | Reading | TPR_lb | FPR_ub | ε_lower dir.1 | dir.2 |
   |---|---|---|---|---|
   | questions, control IN 790/1008, OUT 0/784 | 0.7617 | 0.0034 | 5.400 | 1.431 |
   | questions, ceiling (1008/1008, 0/784) | 0.9973 | 0.0034 | 5.670 | 5.920 |
   | **facts, control 8/8, OUT 0/56** | 0.7473 | 0.0461 | **2.786** | 1.328 |
   | facts, 7/8, 0/56 | 0.5889 | 0.0461 | 2.548 | 0.842 |
   | facts, 8/8, 1/56 | 0.7473 | 0.0762 | 2.284 | 1.296 |
   | questions, noised 0/1008, 0/784 | 0 | 0.0034 | −∞ | ≈0 |

   Consequence: at the fact unit the auditor's ceiling is ≈2.79, so **only 4 of the 15 published
   ε_upper (σ=24: 2.40, σ=32: 1.74, σ=50: 1.06, σ=80: 0.634) are reachable**; the other 11 cannot
   fail by construction and must say so (D-13).

</domain>

<decisions>
## Implementation Decisions

### Target and comparator (CANARY-02)

- **D-01: The control σ=0 is audited AS COMMITTED and is the instrument's POWER reading; a dated
  continuation ADDS all 15 noised n=8 points, each compared against its OWN ε_upper.** The original
  `audit_target_rule` stays intact, visible, superseded — never edited. The continuation names all 15
  in `point_keys` order; **never a subset chosen after seeing a result.** At the control (no ε claim)
  the comparison is published as vacuous by construction; the control's reading feeds D-04 and
  nothing else.

- **D-02 (Claude's discretion, fixed here): the comparator is the point's own `epsilon` at δ=1e-5.**
  It is the per-point claim the artifact publishes (`epsilon_rule:
  personacore.privacy.accountant.epsilon_for(sigma, steps, delta)`). δ enters the ε_lower formula
  (D-09) rather than vanishing. The curve-total ε (2387.30 at δ=3e-4) is published BESIDE each
  comparison as context and is never the comparator: it can only be looser, so a second comparison
  against it could never accuse anything the first does not.

- **D-03: A PRE-REGISTERED POWER GATE at the control.** A threshold on ε_lower(control) is committed
  before any point runs. If the control does not exceed it, the instrument is declared WITHOUT POWER
  and every would-be CONSISTENT on the noised points becomes INCONCLUSIVE. A blind auditor cannot
  produce 15 "approved" readings.

- **D-04: The power threshold is `ε_lower(control) ≥ min(ε_upper over the 15 audited points)` =
  0.6339783761989397 (σ=80).** "The instrument must resolve at least the smallest claim it checks."
  Derived from the artifact by rule (min over the audited set, read at run time and asserted equal to
  the σ=80 record), no new number. At the fact unit the control would read ≈2.79 at 8/8 and 0/56,
  2.55 at 7/8 — passes with margin; the margin is published, not assumed.

- **D-05: Verdict domain is three-valued: `BROKEN` / `CONSISTENT` / `INCONCLUSIVE`.**
  BROKEN iff ε_lower > ε_upper. CONSISTENT iff not BROKEN AND the power gate passed. INCONCLUSIVE iff
  the power gate failed. "Consistent" never becomes "verified correct": the test is one-sided and can
  only accuse. Every verdict carries a `reasons` list with the numbers, in the gate's register.

- **D-13: The 11 points whose ε_upper ≥ the auditor's ceiling stay `CONSISTENT` with a reason that
  says the comparison could not have failed.** `auditor_ceiling` (ε_lower at TPR = n_IN/n_IN,
  FPR = 0/n_OUT on the REAL n's after D-07 exclusions) is a field of the artifact, computed before any
  verdict is read; each such point's `reasons` states `ε_upper ≥ auditor_ceiling`; the artifact's top
  level carries `reachable_claims k/15`. No fourth verdict value.

### The OUT-canary scorer

- **D-06: Membership is scored by GENERATION RECALL with ONE instrument for IN and OUT.** IN = the 8
  `LOCKED_FACTS`; OUT = the 56 `phase21_filler.FILLER_FACTS`, rendered with
  `render_family(..., forms=FILLER_SLOT_FORMS)`. Adapter-on vs adapter-off, `contains_value`
  IMPORTED (`phase14_recall.contains_value`), never re-implemented. Filler becomes scored **in a NEW
  Phase-26 module only**; `phase18_extraction.py` (ancestry-guarded) and the 10-value leak vocabulary
  (D-18) are untouched — filler still never enters the extraction fixture.

- **D-07: PRE-REGISTERED PRECONDITION — the adapter-off arm IS the guessability probe D-17 waived.**
  Committed before any point runs: a filler fact with ANY adapter-off success is EXCLUDED from the
  OUT population, counted and published explicitly (`excluded n / 56`), never hidden. The same rule
  holds trivially for the 8 IN (adapter-off already 0/1008 at the control). D-17's waiver receives a
  dated continuation naming why its premise ("filler is never scored") changed; original text left
  standing, superseded.

- **D-08 (Claude's discretion, fixed here): same recall families for IN and OUT
  (`TAUGHT_FAMILY_IDS` and `HELDOUT_FAMILY_IDS` exactly as `score_arm` uses them), so TPR and FPR
  are measured on the same prompt shapes; both denominators — question-level and fact-level — are
  published per `phase18_extraction.CLUSTER_DENOMINATOR_RATIONALE`.**

### The instrument's arithmetic

- **D-09: ε_lower is the MAX of the two hypothesis-testing constraints of (ε, δ)-DP, from the SAME
  two Wilson bounds:**
  `ε_lower = max( ln((TPR_lb − δ) / FPR_ub), ln((1 − FPR_ub − δ) / (1 − TPR_lb)) )`, with
  `TPR_lb = phase20_gate_coverage.wilson_lower_bound(members_answered, n_IN)`,
  `FPR_ub = erasure_gate.wilson_upper_bound(nonmembers_answered, n_OUT)`, δ = the claim's δ
  (`mitigation_unit.DELTA` = 1e-5). Both bounds IMPORTED, stdlib only. Degenerate cases
  (TPR_lb ≤ δ, TPR_lb = 1, FPR_ub ≥ 1 − δ) are named in the record, not silently clipped.

- **D-10: The FACT is the unit that DECIDES; the question unit is REPORTED beside it.** The canary is
  the fact (`mitigation_unit.PRIVACY_UNIT` = "one taught fact"); a fact's ~14 questions are correlated
  re-measurements. n_IN = 8, n_OUT ≤ 56 after D-07. The question-level reading (n_IN = 112,
  n_OUT ≈ 784) travels in the same record and never decides — SC1's "questions rather than draws"
  is honoured (draws are never a unit), and the flattering denominator is disclosed, not chosen.

- **D-14: A fact counts as ANSWERED (member) under adapter-on when ≥ 1 of its questions is answered.**
  Existential, as `n_answerable` already is in the artifact's `per_fact`. With D-07 requiring
  adapter-off = 0, a single adapter-on hit cannot come from the base.

- **D-11: ONE z, by reference.** Both bounds use `erasure_gate._Z_ONE_SIDED_95` (95% one-sided each);
  no new z constant. Joint coverage of the two bounds is declared as ≥ 90% (Bonferroni) beside every
  ε_lower — published, not hidden.

### Budget and venue

- **D-15: 9 draws per question — the recall instrument's own (`phase14_recall.N_SEEDED_SAMPLES` + 1),
  identical to the published recall readings (1008 = 112 × 9).** The audit's IN reading at the control
  must reproduce the record's 790/1008 within the existing `phase25_prereg.prove_reproduction(k, n)`
  gate — a free cross-check of the auditor against the artifact, refused if it fails.

- **D-16: The audit runs as a user LaunchAgent with its own `caffeinate`, one gitignored sidecar per
  point pinned to the record's `adapter_sha256`, and resume that reuses ONLY a sidecar whose hash
  equals the record's (the D-12 / `phase25_recall` pattern, functions CALLED not re-implemented:
  `phase25_run.atomic_write_json`, `beat`, `start_heartbeat`, `device`).** `pmset` is at `sleep 1`;
  ~11 h in a foreground session would not survive.

- **D-17 (Claude's discretion, fixed here): the adapter-off arm is measured ONCE against the base
  checkpoint pinned by sha256 and reused for all 16 points** (same weights, same prompts, same
  per-question seeds — the base does not vary across points); order = `phase25_record.
  ORDERED_POINT_KEYS()` restricted to `dp_n8`; NO verdict is computed or read before all 16 sidecars
  exist.

### Where the verdict lives

- **D-18: A SIBLING artifact pinned in both directions: `results/phase26_canary.json`.** It carries
  the sha256 of `results/phase25_frontier.json` and the `adapter_sha256` of each of the 16 audited
  points; a test proves the link (frontier bytes on disk hash to the pinned value; the 16 hashes equal
  the frontier's). The frontier stays BYTE-UNTOUCHED, as WR-03 decided ("record, do not re-emit").
  "Travels with" = same directory, proven link, and Phase 28 may quote any ε only beside its verdict
  (D-40's publication obligation gains this clause).

- **D-19: A PARTIAL artifact is NEVER assembled.** If the 16 sidecars do not all exist,
  `phase26_canary.json` is not written; instead a dated named-limitation entry lands (operational
  note + `results/`), and Phase 28 is obliged to say "audit not executed / partial" beside every ε.
  An artifact with 9 of 16 points is a subset chosen by the clock.

### The dated continuation

- **D-12: The continuation lives in a NEW module `scripts/phase26_prereg.py`; `phase25_prereg.py`
  stays byte-identical.** The module imports `CANARY_RESERVATIONS["audit_target_rule"]` BY
  REFERENCE, resolves it against the frontier (proving it yields `dp_n8_sigma0p000000`), then declares
  the extension (all noised `dp_n8` points in `point_keys` order), the power gate (D-03/D-04), the
  precondition (D-07), the formula (D-09), the unit (D-10), the membership rule (D-14), the verdict
  domain (D-05) and the ceiling disclosure (D-13). Ancestry guard in the Phase-18 mould: every commit
  touching `phase26_prereg.py` must precede the first-add commit of every Phase-26 sidecar/artifact.
  `phase25_prereg`'s copy of the reservations travels inside the frontier, so editing it would make
  the artifact disagree with the live module — WR-03's defect, avoided.

### Claude's Discretion

- D-02 (comparator), D-08 (families / denominators), D-17 (adapter-off once; order; no early reads)
  were delegated and are FIXED above — treat them as locked, not open.
- Module names beyond `phase26_prereg.py` / `results/phase26_canary.json`; the sidecar path under
  `data/`; the exact plist name; the record schema — resolve from the existing modules' constants
  (never invent paths the code refuses).
- Handling of the degenerate bound cases in D-09 (named, not clipped).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The committed reservations and the rule being continued
- `scripts/phase25_prereg.py` — `CANARY_RESERVATIONS` (`adapter_retention`, `canary_population_rule`,
  `audit_target_rule`, `disk_precheck_bytes`); `prove_reproduction(k, n)`; `COMMITTED`.
- `.planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md` — D-37 (the three
  reservations), D-20 (σ=0 inside the sweep at slot 1), D-31 (frontier write-once), D-40 (publication
  obligation), D-12/D-13/D-16 (venue, pmset, detect-never-act watcher).
- `.planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-HUMAN-UAT.md` — item 2 (WR-03:
  record, do not re-emit) — the precedent D-18 follows.

### The artifact being audited
- `results/phase25_frontier.json` — `point_keys`, per-point `epsilon` / `delta` / `adapter_sha256` /
  `adapter_path` / `canary_population` / `taught_recall` / `per_fact` / `gate05_gated`; top-level
  `epsilon_report` (curve total), `never_taught_floor`, `provenance`.
- `scripts/phase25_record.py` — `ORDERED_POINT_KEYS()`, `canary_population(n_facts)`,
  `FRONTIER_RECORD`, `MECHANISM_PIN_DISCLOSURE_GOVERNS`.
- `scripts/phase25_recall.py` — the sidecar-per-point / resume / heartbeat pattern the audit copies
  by CALLING `phase25_run` (docstring names every function).
- `scripts/phase25_epsilon.py` — `report_epsilon` (three required kwargs; no bare ε is printed).

### The canary populations
- `.planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-CONTEXT.md` — D-12
  (8 scored + 56 filler), D-16 (disjoint filler slot grammar; `render_family(forms=)`), D-17 (the
  guessability waiver this phase continues), D-18 ("unscored" is structural: the 10-value leak list).
- `scripts/phase21_filler.py` — `FILLER_FACTS`, `FILLER_SLOT_FORMS`, `refuse_collisions`,
  `verify_round_trips`, `render_filler_episodes`.
- `scripts/phase14_factset.py` — `LOCKED_FACTS`, `TAUGHT_FAMILY_IDS`, `HELDOUT_FAMILY_IDS`,
  `render_family(family_id, fact, *, second_person=False, forms=None)`.
- `scripts/mitigation_unit.py` — `PRIVACY_UNIT`, `DELTA`.

### The instruments (imported, never re-implemented)
- `scripts/erasure_gate.py` — `wilson_upper_bound`, `_Z_ONE_SIDED_95`, `VERDICTS`.
- `scripts/phase20_gate_coverage.py` — `wilson_lower_bound` (exact mirror; `successes == 0 → 0.0`).
- `scripts/phase18_extraction.py` — `CLUSTER_DENOMINATOR_RATIONALE` (both denominators), the
  ancestry-guard pattern (`tests/test_phase16_prereg.py::test_phase18_prereg_is_frozen_before_every_phase18_result`).
- `scripts/teach_persona.py` — `score_arm` (the published recall pipeline), `score_items`,
  `calibration_items`, `adapter_disabled`; `scripts/phase14_recall.py` — `load_adapted_model`,
  `contains_value`, `N_SEEDED_SAMPLES`.
- `src/personacore/privacy/accountant.py` — `epsilon_for(sigma, steps, delta)` (the claim's producer).
- `scripts/phase25_gate05.py` — `FILLER_EXPOSURE_OMITTED` (why NLL exposure cannot be the OUT scorer).

### Requirements and roadmap
- `.planning/ROADMAP.md` §"Phase 26" — the three success criteria; `.planning/REQUIREMENTS.md`
  CANARY-01 / CANARY-02 and the traceability rows.
- `.planning/research/SUMMARY.md` §"Candidate additional phase" and `.planning/research/PITFALLS.md`
  §"On empirical privacy auditing" — the D-16 discipline clause SC3 quotes.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `teach_persona.score_items(model, tok, device, forbid, items, label=)` + `adapter_disabled(model)`:
  the scoring primitive for IN and OUT. **`score_arm` / `calibration_items` render via
  `render_family(family_id, fact)` WITHOUT `forms=` (line ~2396), so filler through `score_arm`
  raises `KeyError`** — the Phase-26 module renders filler items itself with
  `render_family(..., forms=FILLER_SLOT_FORMS)` and calls `score_items` (or `calibration_items` gains an
  additive `forms=None`, byte-identical when `None` — the D-16 playbook).
- `phase14_recall.load_adapted_model(device, adapter_path=)` — `weights_only=True` load-before-inject,
  the same path every published recall number used; `contains_value` — the boundary rule.
- `erasure_gate.wilson_upper_bound` / `phase20_gate_coverage.wilson_lower_bound` — both bounds; the
  lower bound's `successes == 0 → 0.0` is exact and documented.
- `phase25_prereg.prove_reproduction(k, n)` — the reproduction gate D-15 reuses at the control.
- `phase25_run.atomic_write_json`, `beat`, `start_heartbeat`, `device`; `phase25_watch` — the
  survivability kit; `artifacts/com.personacore.phase25.*.plist` — the LaunchAgent shapes to copy.
- `phase25_record.ORDERED_POINT_KEYS()` — the order; `phase25_epsilon.report_epsilon` — no bare ε.
- `checkpoints/phase25_sigma*_dp_n8_adapter.pt` — 16 retained adapters; base checkpoint via
  `load_adapted_model`'s own resolution (pin its sha256 in the record for D-17).

### Established Patterns
- **Pre-registration in committed code before any number exists**, with an ancestry guard over the
  prereg module (Phase 18) and `_prove`/`SystemExit` instead of `assert` (`-O`-proof).
- **Dated continuations, never edits**: superseded text stays visible (D-01, D-07, D-12).
- **Counts beside every rate; both denominators; no bare ε** (`CLUSTER_DENOMINATOR_RATIONALE`,
  `report_epsilon`).
- **Write-once artifacts pinned by sha256 in tests; sibling artifacts link by digest** (WR-03).
- **CPU-only test suite**: torch imported lazily inside the one function that scores; `--dry-run`
  exercises every structural path; MPS legs skip under the sweep-active env var (D-44).
- **Measure the premise before building on it** — this context's six measured facts replace the
  ROADMAP's "the filler corpus is the in/out population" with what the artifact actually holds.

### Integration Points
- `results/phase26_canary.json` ↔ `results/phase25_frontier.json` (sha256 both ways, D-18).
- `phase26_prereg.py` ← `phase25_prereg.CANARY_RESERVATIONS` (by reference, D-12).
- Phase 28's publication obligation (`phase25_prereg.PUBLICATION_OBLIGATION`, D-40) gains "ε only
  beside its canary verdict" and the D-19 named-limitation clause.
- `tests/` — new `test_phase26_*.py`: ancestry guard, formula against hand-computed cases (the table in
  `<domain>`), verdict domain, link test, `--dry-run` structural paths, power gate mutation watched RED.

</code_context>

<specifics>
## Specific Ideas

- The control's audit reading must reproduce 790/1008 through `prove_reproduction` — the auditor is
  checked against the artifact before it is trusted on any noised point.
- "The instrument must resolve at least the smallest claim it checks" is the sentence the power gate
  should print.
- Reachable claims are 4 of 15 at the fact unit; publish `reachable_claims` at the top of the artifact
  and the ceiling beside every unreachable point — a reader must see that 11 comparisons could not have
  failed before reading 11 CONSISTENTs.
- Joint coverage ≥ 90% (Bonferroni over two 95% one-sided bounds) is stated beside every ε_lower.

</specifics>

<deferred>
## Deferred Ideas

- **Auditing n=64 points** — structurally impossible under D-37(ii) (no out-of-corpus canaries at
  n=64); recorded, not attempted.
- **NLL/exposure as a second distinguisher** — considered and not chosen (D-06); unmeasurable on
  filler (`FILLER_EXPOSURE_OMITTED`). A future phase could add an IN-only NLL reading beside the
  generation one; not here.
- **A joint-95% z** — rejected (D-11) to keep one z in the repo; revisit only if a milestone decides
  to re-level every published bound at once.
- **Re-assembling the frontier with an inline `canary_audit` block** — rejected (D-18) per WR-03; the
  sibling link is the mechanism.
- **Replay-bearing adversarial re-run** — v5.0 candidate (ROADMAP), untouched here.

</deferred>

---

*Phase: 26-Empirical Privacy Audit (Canary)*
*Context gathered: 2026-09-10*
