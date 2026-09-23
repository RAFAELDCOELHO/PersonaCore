# Phase 26: Empirical Privacy Audit (Canary) - Research

**Researched:** 2026-09-10
**Domain:** Integration of existing repo instruments into a one-run canary audit (ε_lower vs published ε_upper) — no new ML, no literature
**Confidence:** HIGH (every claim below was read from source at HEAD `efb4f0f` or recomputed with the imported functions in `.venv`; nothing rests on training data)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)

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
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (REQUIREMENTS.md:441-445) | Research Support |
|----|-------------|------------------|
| CANARY-01 | One-run canary auditing produces an **empirical lower bound on ε**, built additively on the Phase 18 fixture, scorer, Wilson bound and 42,480-draw precedent. | §Standard Stack (the four imported instruments, verified signatures), §Code Examples 1–4 (items builder, per-fact loop, ε_lower, ceiling), §Pitfalls 1–3 (seed alignment, `score_items` has no per-fact output, `teach_persona.py` is digest-pinned), the recomputed ε_lower table in §Summary. |
| CANARY-02 | A rule committed before the audit runs: **if ε_lower > ε_upper the implementation is declared provably broken** — no favourable reading afterward. | §Architecture Pattern 1 (`phase26_prereg.py` as a dated continuation imported by reference), §Pattern 2 (ancestry guard exactly as `tests/test_phase16_prereg.py:322-400`), §Pattern 4 (verdict domain + power gate + `reasons`), §Validation Architecture (guard, mutation-RED, link test). |
| SC3 (verdict travels with the frontier; cut ⇒ named limitation) | ROADMAP §Phase 26 success criterion 3 | §Pattern 5 (sibling artifact pinned both ways, `results/phase26_canary.json`), §Pattern 6 (D-19: no partial artifact; `results/phase26_operational_note.md`), §Pitfall 7 (the driver's git surface must be read-only — §O1 ended with Phase 25). |
</phase_requirements>

## Summary

Phase 26 is pure integration: every number it needs is produced by a function that already exists and is
pinned, and every artifact it reads is already committed. The work is (1) one pre-registration module
`scripts/phase26_prereg.py` that resolves `phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` by
reference, declares the extension to all 15 noised `dp_n8` points, the power gate, the D-07 precondition,
the D-09 formula and the verdict domain; (2) one CPU-safe-at-import driver `scripts/phase26_canary.py`
modelled line-for-line on `scripts/phase25_recall.py` (sidecar per point under `data/`, sha-pinned reuse,
`phase25_run.atomic_write_json` / `beat` / `start_heartbeat` / `device` CALLED, `--dry-run`, `--emit`);
(3) one LaunchAgent plist `artifacts/com.personacore.phase26.canary.plist` copied from
`com.personacore.phase25.recall.plist`; (4) `results/phase26_canary.json` pinned to the frontier's sha256
(`1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5`, 22,311,714 bytes) and the 16
`adapter_sha256`; (5) `tests/test_phase26_prereg.py` + `tests/test_phase26_canary.py`.

Three things the planner must not get wrong, all measured this session: **(a)** `teach_persona.py` is
digest-pinned by `results/phase24_token_budget.json::provenance.module_sha256` and asserted live by
`tests/test_phase24_record.py:289-332`, so the CONTEXT's alternative "`calibration_items` gains an
additive `forms=None`" is REFUSED by the repo — the Phase-26 module must build filler items itself
(6 lines, Code Example 1). **(b)** `teach_persona.score_items` (`scripts/teach_persona.py:2403`) aggregates
per FAMILY only and returns no per-fact or per-question counts, so the fact unit (D-10/D-14) requires the
Phase-26 module to run the same two-call loop (`phase14_recall.complete_question` + `score_question`) over
the IDENTICAL `calibration_items(LOCKED_FACTS, TAUGHT_FAMILY_IDS)` list with the IDENTICAL `enumerate`
index — the per-question seed is `SEED + index` (`phase14_recall.py:227-237`), so any re-ordering or
concatenation of lists changes every draw and D-15's 790/1008 reproduction fails. **(c)** the cost. The
CONTEXT's "~40 min per point / ~11 h" was derived from the control's 914 s; `results/phase25_recall.json`
shows the 15 noised `dp_n8` adapters took 1247–1568 s for the same 368 question-scorings (3.4–4.3 s per
question, no early stop), and the OUT population adds 784 taught + 504 held-out questions per arm. The
arithmetic is ≈ 25 h of MPS (Open Question 1), not 11.

The ε_lower table in the CONTEXT was recomputed with the imported bounds and matches to four decimals
(z = 1.6448536269514722, δ = 1e-5): fact unit control 8/8 & 0/56 → TPR_lb 0.7473, FPR_ub 0.0461,
ε_lower = max(2.7859, 1.3283) = **2.7859**; 7/8 → 2.5476; 8/8 & 1/56 → 2.2836; question ceiling 5.9196.
The power threshold `min ε_upper` = `EPSILON_LADDER[-1]` = frontier `points.dp_n8_sigma80p000000.epsilon` =
0.6339783761989397 (`epsilon_for(80.0, 200, 1e-5)` live). Reachable claims at the fact-unit ceiling 2.7859:
σ ∈ {24, 32, 50, 80} → **4/15**. Degenerate cases: `TPR_lb = 1` is unreachable for finite n at z > 0
(Wilson lower at p = 1 is 1/(1+z²/n)); `TPR_lb = 0` is exact when 0 members answer
(`wilson_lower_bound(0, n) → 0.0`, `phase20_gate_coverage.py:184-186`) and makes direction 1 undefined
(log of a negative) with direction 2 = ln(1 − FPR_ub − δ) ≤ 0; `FPR_ub = 1.0` is exact when every OUT
answers (`wilson_upper_bound(n, n)` returns `min(1.0, …)`) and makes direction 2 undefined.

**Primary recommendation:** Two new scripts, one plist, one artifact, two test files; every instrument
imported; the driver's git surface read-only; the audit launched by `launchctl kickstart` under
`caffeinate -dims` with `PERSONACORE_SWEEP_ACTIVE=1`; nothing read until all 16 sidecars exist.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pre-registration (rule resolution, extension, power gate, formula, verdict domain) | `scripts/phase26_prereg.py` (CPU-only, stdlib + sibling scripts) | `tests/test_phase26_prereg.py` (ancestry guard) | Committed before any sidecar exists; guarded by git ancestry, not by convention |
| Item rendering for IN/OUT | `scripts/phase26_canary.py` (`_items()` — 6 lines, CPU-only) | `phase14_factset.render_family`, `phase21_filler.FILLER_SLOT_FORMS`, `phase14_recall.contains_value` | `teach_persona.calibration_items` cannot render filler (no `forms=`) and `teach_persona.py` is digest-pinned |
| Scoring (draws) | `scripts/phase26_canary.py::score_point` (lazy torch) on MPS via `phase25_run.device()` | `phase14_recall.load_adapted_model`, `complete_question`, `score_question`, `personacore.lora.adapter_disabled` | One instrument for IN and OUT; per-fact/per-question counts kept, aggregated in the module |
| Survivability (sidecars, heartbeat, atomic writes) | `phase25_run` (called) + `data/phase26_canary_<key>.json` | `artifacts/com.personacore.phase26.canary.plist`, existing `phase25_watch` agent | D-16; the Phase-25 kit is reused unchanged |
| Bounds + ε_lower + ceiling | `scripts/phase26_prereg.py` (pure functions) | `erasure_gate.wilson_upper_bound`, `phase20_gate_coverage.wilson_lower_bound`, `mitigation_unit.DELTA` | Formula lives beside its pre-registration so the test table pins it |
| Verdict + artifact assembly | `scripts/phase26_canary.py::emit` | `phase25_epsilon.report_epsilon`, `phase25_run.atomic_write_json` | Written once, only when 16 sidecars + the off-arm sidecar exist |
| Link proof / publication | `tests/test_phase26_canary.py` | `results/phase25_frontier.json` (byte-untouched) | D-18 |
| Named limitation (if cut) | `results/phase26_operational_note.md` | `.planning` docs | D-19 |

## Standard Stack

No new packages. Everything is stdlib + the installed `torch 2.7.1` (MPS available, Python 3.11.15 in
`.venv`) + sibling scripts. **Package Legitimacy Audit: not applicable — this phase installs nothing.**

### Core (imported, never re-implemented) — signatures verified by reading source

| Symbol | Location (file:line) | Exact definition / value | Use in Phase 26 |
|---|---|---|---|
| `calibration_items(facts, family_ids)` | `scripts/teach_persona.py:2381` | Loops `for fact in facts: for family_id in sorted(family_ids): for question, _answer in fs.render_family(family_id, fact): if pr.contains_value(question, fact.value): continue; items.append((family_id, fact, question))` — **`render_family` called WITHOUT `forms=` at line 2396** ⇒ `KeyError` on a filler slot | Reference only; call it for IN and prove the Phase-26 items builder returns an equal list on `LOCKED_FACTS` |
| `score_items(model, tok, device, forbid, items, *, label)` | `scripts/teach_persona.py:2403` | `for index, (family_id, fact, question) in enumerate(items): drawn = pr.complete_question(model, tok, question, device, forbid, index=index); k, n = pr.score_question(drawn["completions"], fact.value)` — aggregates `per_family` only; `SystemExit` if `total_n == 0`; returns `{"k","n","rate","per_family","questions"}` | NOT called (no per-fact output); its two inner calls are the primitive |
| `score_arm(arm, facts, adapter_path, device)` | `scripts/teach_persona.py:2440` | `pr.load_adapted_model(device, adapter_path=…)`; `taught = calibration_items(facts, fs.TAUGHT_FAMILY_IDS)`; `heldout = calibration_items(facts, fs.HELDOUT_FAMILY_IDS)`; ON both tiers, then `with adapter_disabled(model):` OFF both tiers; returns `on_taught/on_heldout/off_taught/off_heldout/per_family_gain/heldout_family_std` | The published pipeline the audit must reproduce (790/1008) |
| `adapter_disabled(model)` | `src/personacore/lora/inject.py:157` (contextmanager; imported into `teach_persona.py:76`) | Sets `enabled=False` on every `LoRALinear`, restores prior values in `finally`; `RuntimeError` if any module is merged | The OFF arm = base weights (D-07 probe, D-17 once) |
| `load_adapted_model(device, adapter_path=None)` | `scripts/phase14_recall.py:712` | `load_slim(CONVBASE_SLIM)` (`checkpoints/convbase_slim.pt`, `:81`) → `GPT` → `load_state_dict` → `load_adapter(adapter_path)` → `inject_lora` → `load_adapter_weights` → `model.to(device).eval()`; returns `(model, cfg, tok, forbid, artifact)`; `SystemExit` if the adapter path is missing | Base resolved from the module constant, not a record field (no record carries a base sha) |
| `contains_value(completion, value)` | `scripts/phase14_recall.py:300` | `normalize(value) in normalize(completion)` | The boundary rule for both IN and OUT |
| `score_question(completions, value)` | `scripts/phase14_recall.py:315` | `(sum(contains_value(c, value) for c in completions), len(completions))` | Per-question `(k, n)` |
| `complete_question(model, tok, question, device, forbid, *, index)` | `scripts/phase14_recall.py:901` | `build_recall_prompt(tok, question)` then `draw_all(...)` → `{"question","prompt_ids","completions","stopped"}` | The draw primitive; `index` is the question's position in ITS list |
| `question_seed(index)` / `SEED` / `N_SEEDED_SAMPLES` | `scripts/phase14_recall.py:227-237`, `:147`, `:152` | `SEED + index`; `SEED = 1337`; `N_SEEDED_SAMPLES = 8` (9 draws) | Seed alignment (Pitfall 1) |
| `LOCKED_FACTS` | `scripts/phase14_factset.py:390` | 8 `Fact(id, slot, value, tier)` NamedTuples | IN population |
| `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` | `scripts/phase14_factset.py:825-826` | `frozenset({"F1","F2","F4","F5","F6"})` / `frozenset({"F3","F7","F8"})` — iterate `sorted(...)` | D-08 |
| `render_family(family_id, fact, *, second_person=False, forms=None)` | `scripts/phase14_factset.py:833` | `forms=None` → the byte-identical v2.0 path; `forms` supplied → `_render_family(..., forms=forms)`; unknown slot → `KeyError` | OUT rendering with `forms=FILLER_SLOT_FORMS` |
| `FILLER_FACTS` / `FILLER_SLOT_FORMS` | `scripts/phase21_filler.py:175` / `:61` | 56 `Fact`s (tier `"filler"`, 8 `filler_*` slots × 7) / 8 `SlotForms` | OUT population |
| `GUESSABILITY_WAIVER` | `scripts/phase21_filler.py:391` | The D-17 waiver as data | Superseded by reference in `phase26_prereg` (D-07) |
| `wilson_upper_bound(successes, n, z=_Z_ONE_SIDED_95)` | `scripts/erasure_gate.py:139` | `min(1.0, (centre + spread) / denom)`; `ValueError` on `n <= 0` | FPR_ub |
| `_Z_ONE_SIDED_95` / `VERDICTS` | `scripts/erasure_gate.py:90` / `:136` | `1.6448536269514722` / `("SUCCESS","FAILURE","INCONCLUSIVE")` | One z (D-11); the register for a 3-valued domain |
| `wilson_lower_bound(successes, n, z=erasure_gate._Z_ONE_SIDED_95)` | `scripts/phase20_gate_coverage.py:124` | `if successes == 0: return 0.0` (exact); else `max(0.0, (centre − spread) / denom)` | TPR_lb |
| `PRIVACY_UNIT` / `DELTA` | `scripts/mitigation_unit.py:85` / `:171` | `"one taught fact"` / `1e-5` | D-10 / D-09 |
| `epsilon_for(sigma, steps, delta)` | `src/personacore/privacy/accountant.py:819` | Three positional params, no `clip_norm` | Only to assert `points[k].epsilon == epsilon_for(sigma, 200, 1e-5)` live |
| `CANARY_RESERVATIONS` / `COMMITTED` / `prove_reproduction(k, n)` / `PUBLICATION_OBLIGATION` / `point_record_path(point_key)` | `scripts/phase25_prereg.py:496` / `:54` (`"2026-08-31"`) / `:176` / `:424` / `:276` | `prove_reproduction` compares against module constants `REPRODUCTION_K = 790`, `REPRODUCTION_N = 1008` (`:88-89`) under hard `==` on ints (bool refused); returns `None` or raises `SystemExit` | D-12, D-15 |
| `atomic_write_json(path, blob)` / `beat(...)` / `start_heartbeat(path, state, *, seconds=None)` / `device()` / `HEARTBEAT_PATH` | `scripts/phase25_run.py:118` / `:298` / `:350` / `:407` / `:286` (`data/phase25_heartbeat.jsonl`) | `beat` fields `("utc","point","stage","shape","draw_index")`; `start_heartbeat` returns `(stop_event, thread)`; `device()` → `RuntimeConfig().device` lazily | D-16 |
| `ORDERED_POINT_KEYS()` / `canary_population(n_facts)` / `FRONTIER_RECORD` | `scripts/phase25_record.py:253` / `:629` / `:107` | A FUNCTION (call with parentheses); 44 keys; `FRONTIER_RECORD = _ROOT/"results"/"phase25_frontier.json"` | D-17 order: `[k for k in ORDERED_POINT_KEYS() if k.startswith("dp_n8")]` (16 keys, control first) |
| `report_epsilon(*, point_epsilon, curve_total_epsilon, selection_accounted)` | `scripts/phase25_epsilon.py:297` | Three keyword-only args, no defaults | The only sanctioned ε rendering |
| `training_sidecar` / `measure_sidecar` / `run_log_dir` (the c3c7709 resolver) | `scripts/phase25_points.py:266-275` | `data/phase25_{key}_training.json`, `..._measure.json`, `data/phase25_runs/{key}` | Naming precedent only |
| `sidecar_path(point_key)` (recall) | `scripts/phase25_recall.py:90` | `SIDECAR_DIR / f"phase25_recall_{point_key}.json"` | Copy as `data/phase26_canary_{key}.json` |
| `FILLER_EXPOSURE_OMITTED` | `scripts/phase25_gate05.py:280` | Why NLL exposure cannot score filler | Quote in the artifact's `governs` |
| `CLUSTER_DENOMINATOR_RATIONALE` | `scripts/phase18_extraction.py:2010` | "publishes BOTH ends of the clustering assumption … both or neither" | Quote beside both denominators (D-08/D-10) |
| `launch_banner()` | `scripts/phase25_venue.py:540` | Printed first by `phase25_recall.main` (`:301`) | Print first in the Phase-26 `main` |
| `_prose.normalized(text)` | `scripts/_prose.py:35` | `" ".join(text.split())` | Every prose assertion in tests |

### The artifact being audited — read 2026-09-10

`results/phase25_frontier.json`: sha256 `1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5`, 22,311,714 bytes, single commit
`4030d0e` (2026-09-09), tree clean at `efb4f0f`. Top-level keys include `point_keys` (44), `points`, `epsilon_report`,
`never_taught_floor`, `provenance` (with `canary_reservations` = the JSON of `phase25_prereg.CANARY_RESERVATIONS`, asserted equal by
`tests/test_phase25_frontier.py:449-459`). The 16 `dp_n8` keys in `point_keys` order:
`dp_n8_sigma0p000000, 0p500000, 0p700000, 1p000000, 1p500000, 2p000000, 3p000000, 4p000000, 6p000000, 8p000000, 12p000000, 16p000000, 24p000000, 32p000000, 50p000000, 80p000000`.
Per-point fields present: `epsilon` (`null` at the control with `epsilon_omitted_reason`), `delta` (1e-5), `sigma`, `adapter_sha256`,
`adapter_path` (`checkpoints/phase25_sigma<σ>_dp_n8_adapter.pt`), `canary_population` (`{n_facts:8, in_corpus:8, out_of_corpus:56, has_out_of_corpus_canaries:true, …}`),
`taught_recall` (`{numerator, denominator, rate, questions, draws_per_question, per_family}`), `heldout_recall`, `taught_recall_off`, `heldout_recall_off`,
`per_fact` (EXTRACTION per attack family — keyed `core_held_out`/`core_taught` → family → fact id → `{k, n_answerable, n_questions, questions:[[k,16]…], unit:"question"}`; this is NOT a recall per-fact reading — no recall per-fact reading exists anywhere, Phase 26 produces the first), `reproduction_gate` (control only: `{passed:true, expected:[790,1008], observed:[790,1008]}`), `verdict`, `epsilon_rule`. There is no base-checkpoint sha in any record.
Published ε_upper (σ 0.5 → 80): 519.6981942303134, 289.33863705009264, 159.44148628736576, 83.8305906128762, 54.37663901498563, 30.50627999271221, 20.675508046994032, 12.262332118205716, 8.595865790470416, 5.299979064701441, 3.7965357228934966, 2.3957449097512216, 1.7369988136430536, 1.060789755417757, 0.6339783761989397 — equal to `mitigation_budget.EPSILON_LADDER[1:]` (`scripts/mitigation_budget.py:862`). `epsilon_report.curve_total_epsilon = 2387.299119573244`, `total_delta = 3e-4`, `k = 30`.
All 16 adapters exist under `checkpoints/phase25_sigma*_dp_n8_adapter.pt` (listed). Base: `checkpoints/convbase_slim.pt`, 55,601,651 bytes, sha256 `550bb8b08f65cbb8442fa2c44b1e905aeb51ae7afc39b012c35b957459e1f056` — pin this in the artifact (D-17).
`results/phase25_recall.json` (first-add `3441f79`): all 44 points carry `taught_recall_off = 0/1008` and `heldout_recall_off = 0/648` — the adapter-off IN reading is identical across every point (D-17's premise, measured, though all-zero evidence is weak; the structural argument is that `enabled=False` returns `base(x)`).

### Alternatives Considered (all rejected by locked decisions or measured facts)
| Instead of | Could Use | Why not |
|---|---|---|
| Per-fact loop over `complete_question`/`score_question` | `teach_persona.score_items` per fact | `enumerate` restarts at 0 per call → different seeds → 790/1008 unreproducible |
| Own `_items()` builder | `calibration_items(..., forms=)` | `teach_persona.py` digest-pinned (`results/phase24_token_budget.json`, `tests/test_phase24_record.py:289`); its last edit was reverted (`28ed553`) |
| Off arm via `adapter_disabled` on a loaded adapter | Load the base with no adapter | `load_adapted_model` raises `SystemExit` without an adapter path; host the OFF pass on the control adapter and record it |

## Architecture Patterns

### System Architecture Diagram

```
 results/phase25_frontier.json ──(sha256 pinned, byte-untouched)──────────────────────────────┐
   │ point_keys, points[k].{epsilon, delta, adapter_sha256, adapter_path}                       │
   ▼                                                                                            │
 scripts/phase26_prereg.py  (CPU-only; committed BEFORE any sidecar; ancestry-guarded)          │
   • resolve_audit_target(frontier) → "dp_n8_sigma0p000000"  (CANARY_RESERVATIONS by reference)  │
   • AUDITED_POINT_KEYS = dp_n8 keys in point_keys order (16 = control + 15)                    │
   • power_threshold(frontier) = min ε_upper == points.dp_n8_sigma80p000000.epsilon              │
   • epsilon_lower(members, n_in, nonmembers, n_out, delta) → (eps, dir1, dir2, degenerate[])   │
   • auditor_ceiling(n_in, n_out) ; verdict(eps_lower, eps_upper, power_passed) ∈ VERDICTS      │
   ▼                                                                                            │
 scripts/phase26_canary.py  (torch lazy; LaunchAgent + caffeinate -dims; heartbeat)             │
   ├─ score_off_once(): host adapter = control; adapter_disabled → IN+OUT both tiers            │
   │     → data/phase26_canary_off.json  {base_sha256, host_adapter_sha256, per_fact, per_q}    │
   ├─ for key in AUDITED_POINT_KEYS:  (resume: sidecar reused only if adapter_sha256 == record) │
   │     load_adapted_model(device, adapter_path) → IN taught/heldout, OUT taught/heldout (ON)  │
   │     → data/phase26_canary_<key>.json  {adapter_sha256, per_fact counts, per_question}      │
   │     control only: prove_reproduction(k=Σk over IN taught, n=Σn)  (D-15)                    │
   └─ emit(): refuse unless off + 16 sidecars exist (D-19)                                      │
         D-07 exclusions → n_out ; ceiling ; power gate at control ; 15 verdicts ; reasons      │
         → results/phase26_canary.json  {frontier_sha256, 16 adapter_sha256, verdicts …} ───────┘
                          ▲
 tests/test_phase26_*.py: ancestry guard · formula table · degenerate cases · link (both ways) ·
                          --dry-run without torch (subprocess) · sidecar refusal · power-gate RED
```

### Recommended Project Structure (only what this phase ships)
```
scripts/phase26_prereg.py            # the dated continuation + pure arithmetic (stdlib + siblings)
scripts/phase26_canary.py            # driver: score_off_once / score_point / emit / main (--dry-run, --emit, --points, --heartbeat)
artifacts/com.personacore.phase26.canary.plist
results/phase26_canary.json          # written once by --emit, committed by the OPERATOR
results/phase26_operational_note.md  # launch/close record; the D-19 named-limitation entry if the audit is cut
tests/test_phase26_prereg.py
tests/test_phase26_canary.py
data/phase26_canary_off.json, data/phase26_canary_<key>.json   # gitignored sidecars (data/ is in .gitignore)
```

### Pattern 1: Dated continuation by reference (D-12) — `scripts/phase21_unit_continuation.py` is the precedent
**What:** A new unpinned module that imports the frozen rule, proves it resolves as committed, and declares the extension beside it. `phase25_prereg.py` is never edited (last touch `bb42571`, 2026-08-31, precedes the frontier's first-add `4030d0e`; its `CANARY_RESERVATIONS` travel inside the frontier and are asserted equal by `tests/test_phase25_frontier.py:453`).
**When:** Now, in the first plan, before any sidecar exists; `COMMITTED = "<date>"` and a `SIDECARS_AT_COMMIT = 0` mirror `phase25_prereg.py:54-55`.
**Example:** the existing resolver in `tests/test_phase25_close.py:275-297` is the exact rule execution to lift into the module:
```python
# Source: tests/test_phase25_close.py:275-282 (moved into scripts/phase26_prereg.py; the test then imports it)
def resolve_audit_target(artifact):
    points = artifact["points"]
    n8 = [k for k in artifact["point_keys"] if points[k]["arm"].endswith("n8")]
    _prove(all(points[k]["canary_population"]["has_out_of_corpus_canaries"] for k in n8), "…")
    passing = [k for k in n8 if (points[k].get("verdict") or {}).get("verdict") == "PASS"]
    return passing[0] if passing else n8[0]
```
Also supersede the D-17 waiver here, by reference — `WAIVER_CONTINUATION = {"supersedes": "phase21_filler.GUESSABILITY_WAIVER", "why": "its premise 'filler is never scored' is false from this phase: the adapter-off arm IS the probe (D-07)", "committed": COMMITTED}` — do not edit `scripts/phase21_filler.py`.

### Pattern 2: Ancestry guard, Phase-18 mould — `tests/test_phase16_prereg.py:322-400`
**What:** `prereg_commits = git log --format=%H -- scripts/phase26_prereg.py`; `tracked = git ls-files results/phase26_*`; for each tracked artifact `first_add = git log --diff-filter=A --format=%H -- <artifact>` then `adds[-1]` (EARLIEST add, so delete-and-re-add cannot launder); for every `(prereg, first_add)` pair `git merge-base --is-ancestor prereg first_add` with `check=True`; assert `checked == len(prereg_commits) * len(tracked)` and `bool(checked) == bool(tracked)` (green-and-blind refused). Assert `git rev-parse --is-shallow-repository == "false"` first (CI has `fetch-depth: 0`, `.github/workflows/ci.yml:28`). Reflexivity (`X X` exits 0) is closed in `tests/test_phase20_prereg.py:222-242` by a "strictly after" conjunct — copy that conjunct too.
**Also guard `phase25_prereg.py` byte-identity (D-12):** every commit touching `scripts/phase25_prereg.py` must be an ancestor of the frontier's first-add AND of every `results/phase26_*` first-add — same loop, second prereg path. This is what makes "stays byte-identical" a proof rather than a sentence.
**Memory (pin-corrections-are-dated-continuations):** editing a closed pre-registration reddens the guard forever; corrections after the first sidecar go in a further `_continuation`-style module + tripwire, never an edit.

### Pattern 3: Sidecar-per-point driver, CPU-safe at import — `scripts/phase25_recall.py` (whole file is the template)
**What:** module-scope imports only `phase25_prereg`, `phase25_record`, `phase25_run`, `phase25_venue`, `personacore.provenance.git_sha`; `phase14_factset`, `phase14_recall`, `teach_persona`, `phase21_filler` are imported INSIDE `score_point`/`score_off_once` (the AST test `tests/test_phase25_recall.py:126-136` asserts no top-level import of `{torch, teach_persona, phase14_factset, phase14_recall}` — add `phase21_filler` to the set, since it imports `phase14_factset` at module scope). Sidecar reuse: `_prove(blob["adapter_sha256"] == record["adapter_sha256"], "… REFUSED, not reused")` (`phase25_recall.py:141-148`). Adapter hashed on disk before scoring (`:124-128`). Heartbeat: `state = {"point": key, "stage": "score", "shape": None, "draw_index": None}; phase25_run.beat(hb, **state); stop, thread = phase25_run.start_heartbeat(hb, state)` … `finally: stop.set(); thread.join()` (`:157-167`). `heartbeat_path` defaults to `phase25_run.HEARTBEAT_PATH` so the already-installed `com.personacore.phase25.watch` agent polls it unchanged.
**Point record access:** `phase25_recall.point_record(key)` reads `results/phase25_point_<key>.json`; Phase 26 should read the FRONTIER (`phase25_record.FRONTIER_RECORD`, loaded once) since D-18 pins that file — the per-point fields are identical (`tests/test_phase25_frontier.py:449-459`).

### Pattern 4: Verdict in the gate's register (D-05) — `mitigation_gate`'s `reasons` list shape as used in `results/phase25_frontier.json::points[k].verdict`
**What:** `{"verdict": one of ("BROKEN","CONSISTENT","INCONCLUSIVE"), "reasons": [strings carrying the numbers]}`; `VERDICTS` is a module tuple in `phase26_prereg` (register of `erasure_gate.VERDICTS`, `erasure_gate.py:136`). Power gate sentence, verbatim per CONTEXT: "The instrument must resolve at least the smallest claim it checks." Reasons must name: `members_answered/n_in`, `nonmembers_answered/n_out`, `TPR_lb`, `FPR_ub`, both directions, `epsilon_lower`, `epsilon_upper`, the joint-coverage clause "≥ 90% (Bonferroni over two one-sided 95% Wilson bounds, z = erasure_gate._Z_ONE_SIDED_95)", and for unreachable points "epsilon_upper ≥ auditor_ceiling: this comparison could not have failed" (D-13).

### Pattern 5: Sibling artifact pinned both ways (D-18) — precedent `results/phase25_recall.json` ↔ frontier `provenance.inputs.recall_record.sha256`
**What:** `results/phase26_canary.json` carries `frontier_path`, `frontier_sha256`, `frontier_bytes`, and per point `adapter_sha256`; write-once via `atomic_write_json` with a `_prove(overwrite or not out_path.exists(), "… REFUSING to overwrite … --force")` first statement (`phase25_recall.py:225-232`). The link test hashes the frontier bytes on disk and compares the 16 hashes to the frontier's; the frontier stays at one commit (`tests/test_phase25_close.py:321-324` asserts `git log --oneline -- results/phase25_frontier.json` has exactly one line — Phase 26 must keep that green).

### Pattern 6: No partial artifact (D-19)
**What:** `emit()`'s first proofs: the off sidecar exists and its `base_sha256 == sha256(checkpoints/convbase_slim.pt)`; all 16 point sidecars exist and each `adapter_sha256` equals the frontier's. Missing any → `SystemExit` naming the missing keys and pointing to `results/phase26_operational_note.md` for the dated named-limitation entry. The note follows `results/phase25_operational_note.md`'s shape (dated header, quoted command outputs, numbered `##` blocks; `tests/test_phase25_launch.py:467-479` shows how required headings are pinned).

### Anti-Patterns to Avoid
- **Editing any pinned module** (`teach_persona.py`, `phase25_prereg.py`, `phase18_extraction.py`, `mitigation_*.py`, `phase25_record.py`). Each is digest- or ancestry-guarded; the guard goes RED forever.
- **A driver that commits.** §O1's exception "ENDS WITH THIS PHASE" (`phase25_prereg.GIT_SURFACE_EXCEPTION`; `tests/test_phase25_close.py:300-308`). Phase 26's git surface is read-only (`git_sha()` only); the operator commits `results/phase26_canary.json`.
- **Reading a verdict before the 16th sidecar** — no `--emit` path may compute ε_lower from fewer than 16 + off.
- **A grep-based assertion over a module whose docstrings discuss the term** (memory: grep-criteria-measure-prose) — resolve names by AST (`tests/test_phase25_recall.py:263-280`).
- **`assert` for a proof** — `_prove → SystemExit` (`-O`-proof), every sibling module's register.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Wilson bounds | a second estimator | `erasure_gate.wilson_upper_bound`, `phase20_gate_coverage.wilson_lower_bound` | T-20-53 forbids a second copy; the `successes == 0 → 0.0` exactness is documented at `phase20_gate_coverage.py:139-180` |
| Substring/normalisation rule | any matcher | `phase14_recall.contains_value` | The boundary every published recall used |
| Draws | any sampling loop | `phase14_recall.complete_question` (→ `draw_all`, per-draw `torch.Generator(device).manual_seed(question_seed(index)+s)`) | Seed contract; MPS generator device (`phase14_recall.py:872-877`) |
| Atomic writes / heartbeat / device | new helpers | `phase25_run.atomic_write_json`, `beat`, `start_heartbeat`, `device` | D-16 says CALLED |
| Point order / keys | literals | `phase25_record.ORDERED_POINT_KEYS()` | `point_keys` hard-equality pin |
| ε rendering | f-strings | `phase25_epsilon.report_epsilon(point_epsilon=…, curve_total_epsilon=…, selection_accounted=False)` | D-30: no bare ε; `tests/test_phase25_frontier.py:260` scans for bypasses |
| Reproduction check | `==` inline | `phase25_prereg.prove_reproduction(k, n)` | D-15; ints only, bool refused |
| Prose assertions | `in` on raw text | `_prose.normalized` | Line-wrapped prose false-RED (RPT-02) |
| Plist validation | hand parsing | `plistlib.load` + `plutil -lint` (`tests/test_phase25_recall.py:224-229`, `needs_plutil` skip off macOS) | CI is ubuntu |

**Key insight:** the audit's credibility is that every number comes off the same functions that produced the claim it checks; a re-implementation, however small, breaks that chain.

## Common Pitfalls

### Pitfall 1: Seed alignment — the per-question seed is the list index
**What goes wrong:** ε reading fine, but `prove_reproduction` halts (`k != 790`).
**Why:** `score_items` seeds `question_seed(index)` with `index = enumerate(items)` position in ITS tier list (`teach_persona.py:2414`; `phase14_recall.py:227-237`, `:872-877`). `stamp_seed_indices` (`phase14_recall.py:1006-1023`) records that exactly this class of defect unpaired 158/270 questions in Phase 14.
**How to avoid:** score IN taught as `items = calibration_items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)` (or the Phase-26 builder, proven `==` to it by a test) with `for index, (fid, fact, q) in enumerate(items)` — never concatenated with held-out or OUT lists; each of the four lists (IN-taught, IN-heldout, OUT-taught, OUT-heldout) is its own `enumerate` from 0. Sum `k` over the 112 IN-taught questions (draw-level: 1008 = 112 × 9) and pass `(int(k), int(n))` to `prove_reproduction`.
**Warning signs:** any list built by `+`, `sorted()` over facts, or a dict iteration.

### Pitfall 2: `score_items` has no per-fact output
**What goes wrong:** the fact unit (D-10/D-14) cannot be computed from `score_arm`'s return (`per_family` only).
**How to avoid:** the Phase-26 loop keeps `per_question = [(fact.id, fid, k, n)]` and derives `per_fact = {fact.id: {"answered_questions": …, "n_questions": …, "member": answered ≥ 1}}` (D-14 existential). Publish both denominators with `CLUSTER_DENOMINATOR_RATIONALE`.

### Pitfall 3: `teach_persona.py` is digest-pinned
**Measured:** `results/phase24_token_budget.json::provenance.module_sha256` lists `scripts/teach_persona.py`; `tests/test_phase24_record.py:289-332` asserts the live bytes equal the pin; `git log` shows the last attempted addition (`849657d`) was reverted (`28ed553`). `results/phase25_frontier.json`, `phase25_promotion.json`, `phase21_privacy_unit.json`, `phase23_*.json` also carry its name.
**How to avoid:** never touch it; the 6-line builder in Code Example 1 lives in `phase26_canary.py`.

### Pitfall 4: Cost is ≈ 25 h, not 11
**Measured:** `results/phase25_recall.json` `scoring_seconds` for noised `dp_n8` points = 1247–1568 s for 2 arms × 184 questions (3.4–4.3 s/question); control 915 s (2.5 s/question). OUT items through the same self-naming filter: **784 taught + 504 held-out** per arm (IN: 112 + 72). Per noised point adapter-ON = 1472 questions × ~3.8 s ≈ 93 min; ×15 ≈ 23 h; control ON ≈ 61 min; OFF once ≈ 61 min. Total ≈ 25 h. See Open Question 1.

### Pitfall 5: Degenerate bounds
`TPR_lb = 0.0` exactly when `members_answered == 0` → direction 1 is `ln(negative)` (undefined) and direction 2 = `ln(1 − FPR_ub − δ) ≤ 0`; `FPR_ub = 1.0` exactly when all OUT answer → direction 2 undefined; `TPR_lb = 1` cannot occur (Wilson lower at p = 1 is `1/(1+z²/n) < 1`). Name each in a `degenerate: [...]` list, keep the finite direction, never `max(0, …)` clip. A negative or undefined ε_lower is "no distinguishing power", and at a noised point that is CONSISTENT or INCONCLUSIVE per the power gate, never BROKEN.

### Pitfall 6: D-07 changes `n_out` and therefore the ceiling
`auditor_ceiling` must be computed AFTER exclusions on the real `n_out` (D-13 text). With n_out = 56: 2.7859; n_out = 50: ≈ 2.68. Reachability (`ε_upper < ceiling`) is then read per point; publish `reachable_claims k/15` and the ceiling at the top level BEFORE the verdicts in key order.

### Pitfall 7: The driver's git surface
`phase25_run.commit_point_record` was a named, closed exception; `tests/test_phase25_close.py::test_the_git_surface_exception_is_closed` asserts "IT ENDS WITH THIS PHASE". Phase 26's driver must contain no `git add/commit` call (add an AST test in the shape of `tests/test_phase25_driver.py::test_the_drivers_executable_git_actions_are_exactly_add_and_commit`, asserting the executable set is EMPTY except read-only actions).

### Pitfall 8: Torch determinism across venues
The D-07 gate passed with exact `790/1008` on MPS (`torch 2.7.1`, `.venv` Python 3.11.15, device `mps` per `recall_provenance.device`). Run the audit on the same venue and torch; record `torch_version`, `device`, `platform` in every sidecar (as `phase25_recall` does at `:170-180`). A CPU run is not expected to reproduce the count.

### Pitfall 9: Two stray `caffeinate` processes are running now
`pgrep -lf caffeinate` → `15665 caffeinate -s -i -w 7584` and `51388 caffeinate -i -t 300` (the harness's own). `phase25_venue.prove_only_our_caffeinate` (`:311`) and the launch identity read (`:593`) exist for this; the operational note must record the pre-launch owner list as Phase 25's §2 did.

## Code Examples

### 1. The items builder (CPU-only; the ONLY new rendering code)
```python
# Source: scripts/teach_persona.py:2381-2400 (calibration_items), with the forms kwarg of
# scripts/phase14_factset.py:833 and phase21_filler.render_filler_episodes (:416-439) — verified counts:
# LOCKED_FACTS taught 112 / held-out 72 ; FILLER_FACTS taught 784 / held-out 504 (14 and 9 per fact).
def _items(facts, family_ids, forms=None):
    import phase14_factset as fs      # LAZY — torch-touching neighbours
    import phase14_recall as pr
    items = []
    for fact in facts:
        for family_id in sorted(family_ids):
            for question, _answer in fs.render_family(family_id, fact, forms=forms):
                if pr.contains_value(question, fact.value):   # the same self-naming filter
                    continue
                items.append((family_id, fact, question))
    return items
# tests: _items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS) == tp.calibration_items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)
#        (exact list equality — this is what makes the seeds identical to the published run)
```

### 2. The per-fact scoring loop (the two calls `score_items` makes, with counts kept)
```python
# Source: scripts/teach_persona.py:2403-2437 (score_items) — same two calls, same enumerate index.
def _score_list(model, tok, device, forbid, items, *, label):
    import phase14_recall as pr
    per_question, per_fact = [], {}
    for index, (family_id, fact, question) in enumerate(items):        # index == seed offset
        drawn = pr.complete_question(model, tok, question, device, forbid, index=index)
        k, n = pr.score_question(drawn["completions"], fact.value)
        per_question.append({"fact": fact.id, "family": family_id, "index": index, "k": k, "n": n})
        f = per_fact.setdefault(fact.id, {"answered_questions": 0, "n_questions": 0, "k": 0, "n": 0})
        f["answered_questions"] += int(k > 0); f["n_questions"] += 1; f["k"] += k; f["n"] += n
    return {"per_question": per_question, "per_fact": per_fact,
            "k": sum(r["k"] for r in per_question), "n": sum(r["n"] for r in per_question),
            "questions": len(items)}
# control: phase25_prereg.prove_reproduction(int(in_taught["k"]), int(in_taught["n"]))  → must be 790/1008
```

### 3. The OFF arm once (D-07 probe, D-17)
```python
# Source: scripts/teach_persona.py:2459-2471 (score_arm's OFF pass) + src/personacore/lora/inject.py:157
model, _cfg, tok, forbid, _art = pr.load_adapted_model(device, adapter_path=host_adapter)  # the control's adapter
with adapter_disabled(model):                    # from personacore.lora — base weights only
    off = {tier: _score_list(model, tok, device, forbid, items, label=f"OFF {tier}") for tier, items in lists.items()}
blob = {"base_sha256": sha256(pr.CONVBASE_SLIM), "host_adapter_sha256": frontier["points"][control]["adapter_sha256"], **off}
# D-07: excluded_out = [fid for fid, f in off_out_facts.items() if f["answered_questions"] > 0]  (either tier)
```

### 4. ε_lower, ceiling, verdict (pure; lives in phase26_prereg.py)
```python
# Source: scripts/erasure_gate.py:139 ; scripts/phase20_gate_coverage.py:124 ; scripts/mitigation_unit.py:171
import math, erasure_gate, phase20_gate_coverage, mitigation_unit
def epsilon_lower(members, n_in, nonmembers, n_out, *, delta=mitigation_unit.DELTA):
    tpr_lb = phase20_gate_coverage.wilson_lower_bound(members, n_in)
    fpr_ub = erasure_gate.wilson_upper_bound(nonmembers, n_out)
    degenerate, d1, d2 = [], None, None
    if tpr_lb - delta <= 0: degenerate.append("TPR_lb <= delta: direction 1 undefined")
    else: d1 = math.log((tpr_lb - delta) / fpr_ub)
    if 1 - fpr_ub - delta <= 0: degenerate.append("FPR_ub >= 1 - delta: direction 2 undefined")
    elif tpr_lb >= 1: degenerate.append("TPR_lb == 1: direction 2 undefined")   # unreachable at z>0, named anyway
    else: d2 = math.log((1 - fpr_ub - delta) / (1 - tpr_lb))
    finite = [d for d in (d1, d2) if d is not None]
    return {"tpr_lb": tpr_lb, "fpr_ub": fpr_ub, "direction_1": d1, "direction_2": d2,
            "epsilon_lower": max(finite) if finite else None, "degenerate": degenerate,
            "z": erasure_gate._Z_ONE_SIDED_95, "joint_coverage": ">= 0.90 (Bonferroni over two one-sided 95% bounds)"}
def auditor_ceiling(n_in, n_out): return epsilon_lower(n_in, n_in, 0, n_out)["epsilon_lower"]
VERDICTS = ("BROKEN", "CONSISTENT", "INCONCLUSIVE")
def verdict(eps_lower, eps_upper, *, power_passed):
    if eps_lower is not None and eps_lower > eps_upper: return "BROKEN"
    return "CONSISTENT" if power_passed else "INCONCLUSIVE"
# Hand-computed pins for the test table (this session, imported functions):
#  (790,1008,0,784)→(0.7617,0.0034,5.4003,1.4306)  (1008,1008,0,784)→(0.9973,0.0034,5.6699,5.9196)
#  (8,8,0,56)→(0.7473,0.0461,2.7859,1.3283)  (7,8,0,56)→(0.5889,0.0461,2.5476,0.8416)
#  (8,8,1,56)→(0.7473,0.0762,2.2836,1.2962)  (0,1008,0,784)→(0.0,0.0034,undefined,-0.0035)
# power threshold: min(points[k].epsilon for k in noised) == points["dp_n8_sigma80p000000"].epsilon == 0.6339783761989397
```

### 5. The plist (copy `artifacts/com.personacore.phase25.recall.plist`, change four strings)
`Label` → `com.personacore.phase26.canary`; `ProgramArguments[3]` → `/Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py`; `StandardOutPath`/`StandardErrorPath` → `logs/phase26_canary.{out,err}`; keep `caffeinate -dims`, `--heartbeat /Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl` (the watch agent's path), `KeepAlive false` with its D-10 comment, `RunAtLoad false`, `PERSONACORE_SWEEP_ACTIVE=1`, `PYTHONUNBUFFERED=1`. Launch: `cp` to `~/Library/LaunchAgents/`, `launchctl load`, `launchctl kickstart -k gui/$UID/com.personacore.phase26.canary`; the watcher agent `com.personacore.phase25.watch` is already installed (`~/Library/LaunchAgents` lists all five Phase-25 plists; none loaded now). Record the D-13 `pmset` act if the operator repeats it (currently `sleep 1 / disksleep 10 / powernap 1`).

## State of the Art
Not applicable — no external technology choice is open; every mechanism is the repo's own (Wilson bounds since Phase 19, ancestry guards since Phase 16, sidecars/heartbeat since Phase 23/25). The two-direction (ε, δ) hypothesis-testing lower bound (D-09) is the standard "one-run auditing" arithmetic the CONTEXT fixed; no library exists in the stack that would replace it and none may be added (stdlib-only rule, `erasure_gate.py:146-149`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | The OFF arm hosted on the control adapter with `adapter_disabled` equals the OFF arm hosted on any other adapter (LoRA `enabled=False` → `base(x)`). Structural reading of `inject.py:157-183` plus the all-zero `*_off` readings on 44 points. `[ASSUMED]` (not measured against a non-zero base signal) | Pattern 3 / Code Ex. 3 | The OFF probe would be adapter-dependent; mitigation: record `host_adapter_sha256` and, if the planner wants belt-and-braces, score OFF also on the σ=80 adapter once and assert equality (≈ 1 h). |
| A2 | MPS draws are bit-reproducible on this machine at `torch 2.7.1` (evidence: D-07 gate passed exactly at 25-15 and `phase23_sigma_zero` — same count from two separately trained adapters). `[ASSUMED]` beyond that evidence | Pitfall 8 | Reproduction halts at the control; the halt is the designed outcome (D-15 "refused if it fails"). |
| A3 | ≈ 3.8 s/question for a noised adapter extrapolates from IN questions to OUT questions (same prompt shapes). `[ASSUMED]` | Pitfall 4 | Cost lands between 17 h and 30 h; nothing else changes. |

## Open Questions (RESOLVED)

1. **Budget: ≈ 25 h of MPS vs the CONTEXT's ≈ 11 h.**
   - What we know: measured per-question cost on noised adapters (Pitfall 4); OUT adds 1288 questions per arm under D-08 (both tiers).
   - What's unclear: whether the operator accepts ≈ 25 h. D-08 is locked (both tiers), so the held-out OUT tier (504 q/point ≈ 8.5 h in total) cannot be cut by the planner.
   - Recommendation: plan for 25 h, launch under the LaunchAgent, and state the measured figure in the operational note before kickstart; if the operator cuts the held-out OUT tier, that is a decision to record, not a plan-time change.
   - RESOLVED: plan 26-04 T1 §3 states the measured ≈ 25 h in `results/phase26_operational_note.md` before kickstart and names the CONTEXT's ≈ 11 h as superseded; D-08 stays locked, nothing is cut at plan time; 26-04 T2 is the operator's checkpoint to leave the run unattended.
2. **Which tier's questions decide at the fact unit (D-14)?** The CONTEXT's arithmetic (n_IN = 112, n_OUT ≈ 784, "~14 questions per fact") is the TAUGHT tier. Recommendation: the taught tier decides; the held-out tier is a second reported reading at both units. Declare it in `phase26_prereg` so it is committed, not chosen.
   - RESOLVED: plan 26-01 T1 item 8 — `phase26_prereg.DECIDING_TIER = "taught"` with `DECIDING_TIER_RATIONALE`; held-out is reported beside it at both units and never decides; pinned by `tests/test_phase26_prereg.py::test_the_continuations_are_data`.
3. **D-07 existential scope for exclusion:** "ANY adapter-off success" — recommend any question of EITHER tier (strictest), declared in `phase26_prereg`.
   - RESOLVED: plan 26-01 T1 item 8 — `phase26_prereg.EXCLUSION_SCOPE = "either"` with `EXCLUSION_SCOPE_RATIONALE`; counted and published as `excluded n / 56`; pinned by `tests/test_phase26_prereg.py::test_the_continuations_are_data`.

## Environment Availability

| Dependency | Required By | Available | Version / reading | Fallback |
|---|---|---|---|---|
| `.venv` Python | everything | ✓ | 3.11.15 | — |
| torch + MPS | scoring | ✓ | 2.7.1, `mps.is_available() == True` | CPU (will not reproduce 790/1008 — Pitfall 8) |
| 16 `dp_n8` adapters | scoring | ✓ | all 16 under `checkpoints/`; target re-hashed OK per CONTEXT | none — the audit cannot run without them |
| `checkpoints/convbase_slim.pt` | `load_adapted_model` | ✓ | 55,601,651 B, sha256 `550bb8b0…1f056` | none |
| `results/phase25_frontier.json` | everything | ✓ | sha256 `1f182b40…97d5`, one commit `4030d0e` | none |
| `launchctl` / plists | D-16 | ✓ | five Phase-25 plists installed in `~/Library/LaunchAgents`, none loaded | foreground `caffeinate -dims` (rejected by D-16) |
| `caffeinate` | D-16 | ✓ | two stray processes running (Pitfall 9) | — |
| `pmset` | D-13 | ✓ (read-only) | `sleep 1 / disksleep 10 / powernap 1` | operator's `sudo` act, recorded |
| Disk | sidecars (~1 MB each) | ✓ | 487 GiB free | — |
| `plutil` | plist lint test | ✓ (macOS) | skip on CI via `needs_plutil` | — |
| git full history | ancestry guard | ✓ | non-shallow locally; CI `fetch-depth: 0` | — |
| `logs/` | plist stdout/err | ✓ | exists (gitignored) | — |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest ~= 9.0 (`pyproject.toml:20`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`; `tests/conftest.py` (`SWEEP_ACTIVE_ENV_VAR = "PERSONACORE_SWEEP_ACTIVE"`) |
| Quick run command | `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py` |
| Full suite command | `make test` (= `.venv/bin/pytest -q`; last CI 2691 passed / 62 skipped) — run with `PERSONACORE_SWEEP_ACTIVE=1` while the agent runs |

### Phase Requirements → Test Map
| Req / SC | Behavior | Test Type | Automated Command / assertion | File Exists? |
|---|---|---|---|---|
| CANARY-02 | `phase26_prereg` commits precede every `results/phase26_*` first-add; `phase25_prereg.py` untouched | integration (git) | `pytest tests/test_phase26_prereg.py::test_phase26_prereg_is_frozen_before_every_phase26_result -x`; `::test_phase25_prereg_is_byte_identical_since_the_frontier` — Pattern 2 | ❌ Wave 0 |
| CANARY-02 | Rule resolves to `dp_n8_sigma0p000000`; extension = the 15 noised `dp_n8` keys in `point_keys` order; threshold `== points.dp_n8_sigma80p000000.epsilon == epsilon_for(80.0, 200, DELTA)` | unit (reads the frontier once, module fixture) | `::test_the_committed_rule_resolves_to_the_control`, `::test_the_extension_is_all_fifteen_in_point_keys_order`, `::test_the_power_threshold_is_the_smallest_audited_claim` | ❌ Wave 0 |
| CANARY-01 | `epsilon_lower` reproduces the six hand-computed rows (Code Ex. 4) to `abs=1e-4`; degenerate cases named, not clipped | unit | `::test_epsilon_lower_matches_the_hand_computed_table[...]`, `::test_zero_members_names_direction_one_undefined`, `::test_all_nonmembers_names_direction_two_undefined` | ❌ Wave 0 |
| CANARY-02 | Verdict domain closed; `BROKEN` iff `eps_lower > eps_upper`; `INCONCLUSIVE` iff power failed | unit | `::test_verdict_domain_is_three_valued_and_one_sided` | ❌ Wave 0 |
| CANARY-01 | Items builder equals `calibration_items` on `LOCKED_FACTS` (exact list); OUT counts 784/504; no filler value is in any prompt of an IN item and vice versa | unit (CPU) | `pytest tests/test_phase26_canary.py::test_in_items_equal_calibration_items_exactly`, `::test_out_items_render_through_the_filler_grammar` | ❌ Wave 0 |
| D-16 | `--dry-run` walks off + 16 without torch (fresh-interpreter subprocess, `tests/test_phase25_recall.py:101-136` shape); AST: no top-level torch/teach_persona/phase14_*/phase21_filler import | integration | `::test_the_dry_run_walks_off_and_sixteen_and_never_imports_torch` | ❌ Wave 0 |
| D-16 | Sidecar reused only when `adapter_sha256` matches; refused otherwise (`tmp_path`, `monkeypatch SIDECAR_DIR`) | unit | `::test_a_matching_sidecar_is_reused`, `::test_a_sidecar_for_a_different_adapter_is_refused` | ❌ Wave 0 |
| D-19 | `emit()` refuses with < 16 sidecars or missing off sidecar and names the note | unit | `::test_emit_refuses_a_partial_audit` | ❌ Wave 0 |
| D-03/D-04 | Power-gate mutation watched RED: on a `tmp_path` COPY of the artifact set `power_gate.passed = True` while `control.epsilon_lower < threshold` → the re-derivation fails (`tests/test_phase25_calibrate.py:571-593` shape) | unit | `::test_the_power_gate_goes_red_on_a_forged_pass` | ❌ Wave 0 |
| SC3 / D-18 | Link both ways: `sha256(results/phase25_frontier.json) == artifact.frontier_sha256`; 16 `adapter_sha256` equal the frontier's; frontier still at one commit | integration | `::test_the_sibling_is_pinned_to_the_frontier_both_ways` (runs only once the artifact exists; before that asserts the artifact is ABSENT and the note carries the dated limitation — `bool(checked) == bool(tracked)` idiom) | ❌ Wave 0 |
| SC3 | Every published verdict carries `reasons` with the numbers; unreachable points say `epsilon_upper >= auditor_ceiling`; `reachable_claims` at top; `report_epsilon` sentence present for every point | integration (artifact) | `::test_every_point_carries_its_reasons_and_the_ceiling_disclosure` | ❌ Wave 0 |
| D-15 | Control sidecar's `in_taught.k/n == [790, 1008]` and `reproduction_gate.passed is True` | integration (sweep host, `needs_adapters`) | `::test_the_control_reproduced_the_published_reading` | ❌ Wave 0 |
| D-16 | Plist: `KeepAlive False`, `RunAtLoad False`, label, `plutil -lint`, mirrors the recall agent's wrapper/heartbeat, sets `PERSONACORE_SWEEP_ACTIVE=1` | unit (`needs_plutil`) | `::test_the_canary_agent_mirrors_the_recall_agent` | ❌ Wave 0 |
| §O1 closed | Driver has no executable git subcommand other than read-only ones (AST) | unit | `::test_the_driver_never_commits` | ❌ Wave 0 |
| Human sampling points | Kickstart, assertion read-back, first heartbeat, the OFF sidecar landing, the control's `REPRODUCTION GATE PASSED` line, the 16th sidecar, `--emit`, the operator's commit of `results/phase26_canary.json` | manual, recorded in `results/phase26_operational_note.md` with quoted outputs | — | ❌ Wave 0 (note file) |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest -q tests/test_phase26_prereg.py tests/test_phase26_canary.py`
- **Per wave merge:** `make test` (with `PERSONACORE_SWEEP_ACTIVE=1` while the agent runs)
- **Phase gate:** full suite green + `tests/test_phase25_close.py` still green (frontier one commit, git-surface exception closed) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase26_prereg.py` — CANARY-02 (ancestry, resolution, extension, threshold, formula table, degenerate, verdict domain)
- [ ] `tests/test_phase26_canary.py` — CANARY-01 / D-16 / D-18 / D-19 (items, dry-run, sidecars, emit refusal, power RED, link, plist, git surface)
- [ ] `results/phase26_operational_note.md` — created at plan time with the pre-launch blocks; carries the D-19 entry if the audit is cut
- Framework install: none — pytest present

## Security Domain

`security_enforcement` is not set in `.planning/config.json` (treated as enabled). This phase is an offline, local, CPU/MPS batch job with no network, no user input, no secrets.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication / V3 Session / V4 Access Control | no | — (no service, no users) |
| V5 Input Validation | yes (paths) | `phase25_prereg.point_record_path` charset refusal for every key-derived path (`:276-296`); sidecars only under `data/`; frontier read once |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` for every pin (frontier bytes, 16 adapters, base checkpoint, `phase26_prereg.py` module digest in the artifact's provenance) |
| V14 Configuration | yes | plist with absolute paths, `KeepAlive false`, minimal `PATH`, no secrets in `EnvironmentVariables` |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Untrusted checkpoint deserialisation | Tampering | `load_adapted_model` crosses `weights_only=True` choke points only (`phase14_recall.py:712-731`); never call `torch.load` directly |
| Torn sidecar/artifact on kill | Tampering / DoS | `phase25_run.atomic_write_json` (temp in destination dir, fsync, `os.replace`) |
| Post-hoc favourable reading | Repudiation | Ancestry guard; verdict computed only after 16 sidecars; `reasons` carry numbers; artifact write-once |
| Supervisor re-entering a point | Tampering | `KeepAlive false`; watcher cannot act (`phase25_watch.FORBIDDEN_ACTIONS`) |
| Driver widening its git surface | Elevation | AST test that the driver's executable git actions are read-only |

## Sources

### Primary (HIGH confidence — read from source this session at HEAD `efb4f0f`)
- `scripts/teach_persona.py:55-100, 2335, 2381-2500` · `scripts/phase14_recall.py:80-162, 221-325, 698-927, 976-1100` · `scripts/phase14_factset.py:51-75, 383-410, 524-545, 678-874` · `scripts/phase21_filler.py:1-120, 175, 315, 365, 391-439`
- `scripts/erasure_gate.py:86-175` · `scripts/phase20_gate_coverage.py:111-194` · `scripts/mitigation_unit.py:85-90, 168-180` · `src/personacore/privacy/accountant.py:819-835` · `src/personacore/lora/inject.py:157-184`
- `scripts/phase25_prereg.py:43-55, 85-135, 176-297, 414-540` · `scripts/phase25_run.py:1-70, 105-250, 286-458` · `scripts/phase25_record.py:107, 253-310, 622-667, 1698` · `scripts/phase25_recall.py` (whole) · `scripts/phase25_epsilon.py:297-340` · `scripts/phase25_points.py:266-337, 560-610` · `scripts/phase25_watch.py:56-100, 325-430` · `scripts/phase25_gate05.py:280-292` · `scripts/phase18_extraction.py:2010-2020` · `scripts/_addendum.py` · `scripts/_prose.py:35-46` · `scripts/phase21_unit_continuation.py:1-60` · `scripts/mitigation_budget.py:374, 425, 473, 770, 862`
- `tests/test_phase16_prereg.py:160-215, 322-400` · `tests/test_phase20_prereg.py:222-242` · `tests/test_phase25_close.py:1-60, 260-324` · `tests/test_phase25_recall.py:1-137, 224-300` · `tests/test_phase25_frontier.py:1-60, 407-470` · `tests/test_phase25_calibrate.py:551-593` · `tests/test_phase25_launch.py:467-540` · `tests/test_phase25_correction.py:20-60` · `tests/test_phase24_record.py:289-332` · `tests/conftest.py:1-60`
- `artifacts/com.personacore.phase25.recall.plist`, `com.personacore.phase25.watch.plist` · `results/phase25_operational_note.md` (headings) · `.gitignore` · `Makefile` · `pyproject.toml:20-26` · `.github/workflows/ci.yml:28`
- `results/phase25_frontier.json`, `results/phase25_recall.json`, `results/phase24_token_budget.json` — inspected with CPU-only Python; sha256 computed
- `git log` for `scripts/phase25_prereg.py`, `scripts/teach_persona.py`, `scripts/phase21_filler.py`, `results/phase25_frontier.json`, `results/phase25_recall.json`, commit `c3c7709`
- `.planning/phases/26-…/26-CONTEXT.md`, `26-DISCUSSION-LOG.md` · `.planning/phases/25-…/25-CONTEXT.md` (D-12, D-13, D-16, D-31, D-37, D-40, D-44) · `25-HUMAN-UAT.md` item 2 · `.planning/phases/21-…/21-CONTEXT.md` D-17 · `.planning/research/PITFALLS.md:1131-1141` · `.planning/research/SUMMARY.md:711-721` · `.planning/REQUIREMENTS.md:437-445, 572-573` · `.planning/STATE.md` (head; Phase 25 close entry)
- Live probes: `python -c "import torch…"`, `launchctl list`, `ls ~/Library/LaunchAgents`, `pmset -g` (read-only), `df -h`, `pgrep -lf caffeinate`, `shasum -a 256 checkpoints/convbase_slim.pt`

### Secondary / Tertiary
- None. No web sources were used; this phase has no external technology decision.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every symbol quoted with file:line from source; ε table recomputed with the imported functions.
- Architecture: HIGH — `phase25_recall.py` is a complete, tested template; the only new logic is a 6-line builder, a per-fact loop and the D-09 arithmetic.
- Pitfalls: HIGH for 1–3, 5–7, 9 (measured); MEDIUM for 4 and 8 (extrapolated from measured figures; flagged as A2/A3).

**Research date:** 2026-09-10
**Valid until:** until any of `results/phase25_frontier.json`, `scripts/teach_persona.py`, `scripts/phase25_prereg.py` or the 16 adapters change (all pinned — effectively stable); re-read the cost figures if torch is upgraded.
