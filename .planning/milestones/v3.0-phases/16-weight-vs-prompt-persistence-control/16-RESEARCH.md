# Phase 16: Weight-vs-Prompt Persistence Control - Research

**Researched:** 2026-08-12
**Domain:** Pre-registered measurement design — in-context capability thresholds, stdlib bounds, CPU-only instrument validation
**Confidence:** HIGH on Q1 and Q3 (repo-grounded arithmetic, verified in-session); MEDIUM-LOW on Q2 (scale/task transfer is weak, flagged inline)

## Summary

Scope is narrow by construction. `16-CONTEXT.md` locked 28 decisions and measured the instrument
directly on the real `convbase_slim` + `persona_adapter`; nothing here re-opens them. Three things
were genuinely open, and all three are answered below with numbers a planner can paste.

**Q1 (the real question).** The per-cell ladder threshold should be an **integer question-count
literal**, derived before the run from the *committed* Phase 14 floor (1/1944 draws ≡ **1/216
questions**, Wilson one-sided upper 95% = **0.020482**) via the repo's own
`erasure_gate.wilson_upper_bound`. A cell passes when its one-sided lower bound on the
question-level rate clears that floor ceiling. At n = 216 questions per cell that is
**`LADDER_CELL_PASS_K = 10`** (rate 0.0463) — and the literal is identical whether the multiplicity
is priced at 6 cells or 7 rungs, so the choice cannot be gamed after the fact. A *fixed rate*
literal is rejected because it is n-blind (at n = 8 a single lucky hit clears any bound-based or
rate-based construction — see the degeneracy table); rule-of-three is not a competing option at all,
it is the FAIL-side reporting requirement STAT-02 already mandates.

**Q2 (short, as instructed).** Induction heads (prefix-match-and-copy) provably form at ≥ 2 layers,
so 6 layers is architecturally sufficient *for literal-prefix continuation*. But Phase 16's D-11
natural-question framing has **no literal prefix trigger** — it is retrieve-by-meaning-then-copy, and
no small-scale precedent for that was found. The dominant evidence is in-distribution and already in
this repo: **1/216 questions** on the same model, same prompt builder. **An all-cells-fail ladder is a
normal, expected outcome and must be pre-registered for**, not read as a broken instrument.

**Q3.** Six CPU-only test surfaces, all landing in existing files except one new module. PREREG-02
carries a hard, concrete blocker: `actions/checkout@v4` defaults to `fetch-depth: 1`, so any
git-history ancestry assertion **fails in CI today**. The fix is one line of YAML.

**Primary recommendation:** pre-register `LADDER_FLOOR_ANSWERABLE = 1`, `LADDER_FLOOR_QUESTIONS = 216`,
`LADDER_CELL_QUESTIONS = 216`, `LADDER_CELL_PASS_K = 10` as module-level literals in the Phase 16
driver, pin the derivation with a CPU-only test, and set `fetch-depth: 0` in CI before writing the
PREREG-02 test.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

All 28 decisions D-01..D-28 in `16-CONTEXT.md` are locked and are **not** re-opened by this
research. Reproduced here in compressed form only as a planner checklist — `16-CONTEXT.md` is
authoritative and must be read in full:

- **Run architecture:** D-01 four fresh processes, one per condition, questions sequential within a
  process. D-02 the sequential justification cites BOTH `tests/test_lora_toggle.py:77,95,105`
  (fixture scope) AND Phase 14 D-11.3 `run_bit_identity_control` (real weights, max |diff| 0.0) —
  never one alone. D-03 `CONDITION_ORDER` locked as a module-level constant with exactly two recorded
  reasons plus the verbatim Portuguese sentence. D-04 no KV cache exists (grep-verified) so the split
  is defence-in-depth. D-05 the run is not cost-constrained.
- **Statistic:** D-06 per-fact `k/n` over that fact's questions × 9 draws, grouping key changed from
  `record["split"]` to `fact_id` at `phase14_recall.py:838-843`; cluster bootstrap over questions,
  Wilson alongside labelled as the independence-assuming width, `3/n` wherever successes are zero.
  D-07 `core_held_out` is the single gated tier; `taught` is a pre-registered replication explicitly
  outside the Holm family, with the verbatim non-paraphrasable clause. D-08 ties count AGAINST the
  alternative, `n` fixed at 8. D-09 the Holm family is **closed at exactly 6 pairs**, margin 6.7%,
  therefore **nothing else in Phase 16 may be gated**. D-10 `DEGEN-2` does not exist — do not
  propagate.
- **Ladder:** D-11 2-D grid, span 1/2/5 tokens × distance ~2/~30, natural framing constant. D-12
  synthetic strings, token-length-matched, filtered through the guessability gate. D-13 top rung is
  the fairness control re-run POST-FIX, delta reported as PERS-05's impact; never arm B. D-14
  `licensed_headline()` branches on the highest passed rung, per-cell module-level literal committed
  before the run, verdict computed by importing constants; verbatim clause recorded. D-15 the
  (span 5, distance ~30) cell is a free proxy-validity check against the top rung. D-16
  `phase14_factset_gate.py` must be widened, never copied.
- **Surgery:** D-17 `enumerate(questions)` → `item.seed_index`. D-18 extract the inline
  `assert_value_in_prompt` twin, `values` as a parameter. D-19 the fix changes drawn seeds — that is
  the defect, not a regression. D-20 hybrid placement: fixes in `scripts/phase14_recall.py`, driver
  in its own file. D-21 the AST guard widens in SCOPE (`scripts/*.py` + `src/` complete, named
  allowlist), deletion forbidden.
- **Four arms:** D-22 arm D emits argmax-cosine value AS TEXT scored by the same `contains_value`,
  1 deterministic draw per question. D-23 candidate pool = `LOCKED_VALUES ∪
  {f.value for f in GATE_REJECTED_CANDIDATES}` = 20 values, chance floor 0.05. D-24 embedding = final
  hidden state of the BASE model, adapter OFF, mean-pooled. D-25 pre-registered qualifier on the
  three arm-D pairs, verbatim; **the number to use in the report is 0.05**, not 0.125.
- **Context pressure:** D-26 sweep on arm B only; A gets the proof, C and D are declared N/A with
  each reason stated. D-27 truncation and dilution are NOT independent knobs (prompt is 33/46 tokens
  vs `block_size=256`). D-28 monotone degradation claimed only if the ladder got arm B off the floor.

### Claude's Discretion

> Nothing was delegated wholesale. The planner retains normal latitude on: exact bootstrap
> resample count, report table layout and column order, the filler text used to build synthetic
> spans, file/function naming in the new Phase 16 driver, and the dilution step sizes inside the
> constraint D-27 imposes.

### Deferred Ideas (OUT OF SCOPE)

> - **Widening `phase14_factset_gate.py`'s public API** (D-16) is required by this phase but is a
>   cross-phase instrument change; Phase 17's ISO-01 depends on the same import path. Plan it as a
>   deliberate, visible widening here so Phase 17 inherits it.
> - **DEMO-F2 (prompt-vs-weight recall parity)** stays deferred as Phase 14 declared. Phase 16
>   measures the four-arm comparison under its own pre-registration; it is not DEMO-F2 arriving late.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAT-01 | Question is the unit of analysis, never the draw | Q1 — the cell statistic is `n_answerable` (`phase14_recall.py:1219`), already question-unit; floor converted to 1/216 by arithmetic, not re-measurement |
| STAT-02 | Every proportion ships a bound + denominator; `3/n` when zero; no bare `0%` | Q1 — `wilson_upper_bound` / `rule_of_three` reuse; rule-of-three is the FAIL-side reporting rule for empty cells |
| STAT-04 | Zero new runtime dependencies | Standard Stack + Package Legitimacy Audit — nothing installed; `statistics.NormalDist` (stdlib) is the only new import needed, and even that only to *derive* a literal offline |
| STAT-05 | Gates are module-level literals in a committed driver, verdicts computed by importing them | Q1 — the constants block; Validation Architecture pins the derivation with a test so the literal cannot silently drift |
| STAT-06 | Nothing gated the sample cannot support | Q1 — ladder thresholds are explicitly *licensing* thresholds, not tests; the Holm family stays closed at 6 pairs (D-09) |
| PERS-01 | Blocking capability ladder runs and is recorded before any comparison | Q1 threshold construction + ladder wiring; Q2 tells the planner all-fail is normal |
| PERS-02 | Paired four-arm comparison, same questions, paired by `seed_index` | Architecture Patterns — the ladder is `run_fairness_control` parametrized, so parity is structural |
| PERS-03 | Persistence under context pressure | Pitfall 4 (D-27's dependency made concrete against 33/46 vs 256 tokens) |
| PERS-04 | Embedding/cosine fourth arm | Don't Hand-Roll — mean-pool the existing forward, no index/re-rank/chunk |
| PERS-05 | `enumerate(questions)` → `item.seed_index` | Validation Architecture — AST/behavioural test surface named |
| PERS-06 | AST guard widened, `assert_value_in_prompt` twin | Validation Architecture — surface 3; Pitfall 3 on the widening's own failure mode |
| PREREG-02 | CPU-only test asserts `erasure_gate.py` commit precedes every v3.0 results artifact | Validation Architecture surface 6 + Pitfall 1 (`fetch-depth: 1` blocks it today) |

</phase_requirements>

## Architectural Responsibility Map

Not a multi-tier application. Kept minimal — the useful axis here is *which committed file owns
each capability*, because D-20 makes placement load-bearing.

| Capability | Primary owner | Secondary | Rationale |
|------------|---------------|-----------|-----------|
| Pairing fix (PERS-05), `assert_value_in_prompt` (PERS-06) | `scripts/phase14_recall.py` | — | D-20: Phases 17/18 consume this file; a fix elsewhere is a fix they do not inherit |
| Ladder rungs, thresholds, `licensed_headline()`, four-arm driver, sweep | new Phase 16 driver in `scripts/` | — | D-20 + STAT-05 (gate literals live in the committed driver, not the package) |
| Bounds arithmetic | `scripts/erasure_gate.py` (import) | — | Already committed, stdlib-only, PREREG-01 |
| Synthetic-span vetting | `scripts/phase14_factset.py` (`token_census`, `exact_match_clean` — already public) + widened `phase14_factset_gate.py` | — | D-16/ISO-01: import, never copy |
| Prompt construction | `src/personacore/dialogue/serialize.py:92` | — | Single source of truth, harness + demo both import it |
| Structural guards | `tests/test_phase14_scoring.py` (widened), new `tests/test_phase16_*.py` | — | D-21 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `math` | 3.11 | Wilson/rule-of-three arithmetic | Already how `erasure_gate.py` does it [VERIFIED: `scripts/erasure_gate.py:139,161`] |
| Python stdlib `statistics.NormalDist` | 3.11 | Derive the one-sided z for the pre-registered literal | Stdlib since 3.8; needed once, offline, to *produce* a number that is then hard-coded [VERIFIED: run in-session on py3.11.15] |
| Python stdlib `ast` | 3.11 | Widened `persona=` guard (D-21) | Existing precedent at `tests/test_phase14_scoring.py:405` |
| Python stdlib `subprocess` | 3.11 | git ancestry for PREREG-02 | Already used in `tests/test_phase14_demo.py:61`, `tests/test_phase15_plots.py:54` — not forbidden project-wide, only inside `test_phase15_docs.py` by that module's own policy |
| `torch` | 2.7.1 (installed) | The run itself | Already pinned; nothing added |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hand-rolled Wilson | `scipy.stats` | **FORBIDDEN** — STAT-04; scipy declined twice in committed code |
| `statistics.NormalDist` at runtime | hard-code z | Recommended: derive offline, commit the *literal*. Runtime use is also fine (stdlib), but the literal is what STAT-05 wants |

**Installation:** none. `pyproject.toml` must be byte-identical at v3.0 close (STAT-04).

## Package Legitimacy Audit

**Not applicable — this phase installs zero packages.** STAT-04 makes any install a requirement
violation. `slopcheck` was not run because there is nothing to check; if the planner ever finds
itself reaching for a package, that is the signal the design went wrong, not that an audit is needed.

## Architecture Patterns

### Q1 — Where the per-cell pass thresholds should be anchored

**The statistic.** The cell's unit is the question, and the question-level statistic already exists
in the shared instrument: `n_answerable = sum(1 for entry in asked if entry["k"] > 0)` at
`scripts/phase14_recall.py:1219` [VERIFIED: read in-session]. A question counts as answerable if
**any** of its 9 draws contains the value. This is a max-over-draws statistic, so its noise floor is
roughly 9× the per-draw floor — which is exactly why the floor reference must use the **same**
statistic. It does: Phase 14's fairness control scored 1 hit across 1944 draws, so exactly one
question had `k ≥ 1`, so `n_answerable = 1` at `n = 216`. **The 1/216 conversion is forced by
arithmetic from the committed 1/1944; it is not a new measurement** [VERIFIED: `216 × 9 = 1944`,
fixture core count `112 + 104 = 216`].

**The anchor must be the COMMITTED number, not the post-fix re-run.** D-13 re-runs the fairness
control as the ladder's top rung and reports the delta. If the threshold were anchored to that
re-measured number, the threshold would be set after seeing data — the exact motivated-analysis
failure pre-registration exists to prevent. Anchor to `results/phase14_recall_report.md:378`
(1/1944), frozen and published. The re-run's delta is *reported*, never fed back into the constant.

**Option comparison, as requested:**

| Option | Construction | Verdict |
|---|---|---|
| (a) fixed literal rate | e.g. "cell passes at rate ≥ 0.05" | **Rejected.** n-blind. At n = 24 that is k ≥ 2; at n = 13 it is k ≥ 1. A single lucky hit clears it, which is precisely the ladder inflation D-12 names as the risk the synthetic material introduces. No derivation exists for the number, so the pre-registration cannot defend it. |
| (b) lower bound clears the committed floor's upper bound | `1 - wilson_upper_bound(n - k, n, z) > wilson_upper_bound(1, 216, z95)` | **RECOMMENDED.** Derived entirely from committed numbers and committed code, stdlib-only, self-adjusts to n, and conservative in the correct direction (it under-licenses). The repo already uses this exact complement idiom for a lower bound at `erasure_gate.py:erasure_is_worth_attempting` [VERIFIED: read in-session]. |
| (c) rule-of-three / zero-successes | `3/n` | **Not a competitor.** `3/n` is the ceiling *under zero successes*; it cannot express a pass. Its correct role is the FAIL side: a cell scoring 0 reports `rate = 0, upper = 3/216 = 0.013889` per STAT-02's "no bare 0%". Keep it — as reporting, not as threshold. |

A variant of (b) — compare the cell's lower bound against the floor's *point* rate 0.004630 instead
of its upper bound — is what `erasure_is_worth_attempting` does. **Do not use it here**: that
function's base rate is measured at large n with matched budget, whereas this floor is 1 success in
216 and carries real uncertainty of its own. Using the floor's upper bound prices that in and errs
toward under-licensing. (For reference it would give k_min = 3 at n = 216 instead of 8–10.)

**Multiplicity.** Six cells (seven rungs) each judged at one-sided 95% gives ~26% probability that
at least one clears under a true floor null. A false pass here licenses the *stronger* headline
("the base can use context, so the prompt arm's floor is real evidence about weights"), which is the
over-licensing direction the whole milestone is built to avoid. Setting the per-cell z to the
`1 - 0.05/6` quantile (z = 2.393980) prices this in for **two extra questions**. This is **a choice
of literal, not a hypothesis test** — no p-value is computed, no verdict is emitted, and D-09's Holm
family stays closed at exactly 6 pairs. STAT-06 is untouched.

**The constants block (recommended, paste-ready):**

```python
# ---- PERS-01 capability-ladder pre-registration (STAT-05) -------------------------------
# Committed BEFORE the run it judges. Every number below is derived from material already
# published in this repository; none of it is derived from any Phase 16 measurement.
#
# Floor: results/phase14_recall_report.md:378 recorded 1/1944 for the D-11.1 fairness control.
# 1944 = 216 questions x 9 draws, and a single hit across all draws means exactly one question
# had k >= 1 -- so n_answerable = 1 of 216. The conversion to the STAT-01-legal question unit
# is ARITHMETIC on the committed number, not a re-measurement.
LADDER_FLOOR_SOURCE = "results/phase14_recall_report.md:378 (Phase 14 Control 1, 1/1944 draws)"
LADDER_FLOOR_ANSWERABLE = 1
LADDER_FLOOR_QUESTIONS = 216
LADDER_FLOOR_UPPER_95 = 0.020481915502612365   # erasure_gate.wilson_upper_bound(1, 216)

# Every rung is scored over the SAME question set at the SAME draw count as the floor, or the
# comparison is apples-to-oranges: n_answerable is a max-over-draws statistic (D-15 also needs
# identical n for the proxy-validity check to mean anything).
LADDER_CELL_QUESTIONS = 216
LADDER_CELL_DRAWS = 9                          # == 1 greedy + N_SEEDED_SAMPLES

# Per-cell z is the 1 - 0.05/6 one-sided quantile so the six licensing thresholds jointly carry
# <= 5% false-pass probability under the floor null. This is a CHOICE OF LITERAL, not a test:
# no p-value is computed and no verdict is emitted here. The Holm family stays closed at exactly
# the 6 arm pairs (D-09) and nothing in the ladder is gated in the inferential sense (STAT-06).
LADDER_CELL_Z = 2.393979799818510              # NormalDist().inv_cdf(1 - 0.05/6)

# Smallest k with (1 - wilson_upper_bound(216 - k, 216, LADDER_CELL_Z)) > LADDER_FLOOR_UPPER_95.
# Insensitive to whether the multiplicity is priced at 6 cells or 7 rungs -- z=2.393980 and
# z=2.449998 both yield 10 -- so this literal cannot be moved by re-arguing the family size.
LADDER_CELL_PASS_K = 10                        # 10/216 = 0.046296
```

**Verified threshold table** (computed in-session with the repo's own `wilson_upper_bound`; use this
if the planner departs from n = 216):

| n per cell | k_min at z = 1.644854 | k_min at z = 2.393980 (recommended) | rate at recommended k_min | `3/n` (fail-side report) |
|---|---|---|---|---|
| 216 (full core set) | 8 (0.0370) | **10** | **0.0463** | 0.013889 |
| 112 (core taught) | 5 | 6 | 0.0536 | 0.026786 |
| 104 (core held-out) | 5 | 6 | 0.0577 | 0.028846 |
| 72 | 4 | 5 | 0.0694 | 0.041667 |
| 54 | 3 | 4 | 0.0741 | 0.055556 |
| 24 | 2 | 2 | 0.0833 | 0.125000 |
| 8 | **1** | 1 | 0.1250 | 0.375000 |

The n = 8 row is the degeneracy proof: at eight questions a **single** hit clears the bound. Any
per-cell n small enough for one draw to license a headline branch is unusable. Recommend n = 216 —
identical to the floor and to the top rung, which is also what D-15's proxy-validity check requires.

**Calibration sanity.** 10/216 = 4.6% of questions answerable at least once in 9 draws. Phase 14's
*adapter* held-out rate is 0.3483 in draws — question-level answerability far above that. So a
passing cell is a genuinely low bar: the ladder asks "is this arm off the floor?", never "is this arm
as good as the weights". That is the correct calibration for a licensing threshold.

### Ladder wiring: the ladder IS `run_fairness_control`, parametrized

The distance-~30 row is `run_fairness_control` with a substituted `statements` map (synthetic value
instead of the real one) — same 216 questions, same 9 draws, same scorer, same prompt builder. This
is worth planning for explicitly because it makes cross-rung parity structural rather than asserted,
and it makes the D-15 proxy check a direct subtraction.

The distance-~2 row **cannot** reuse that path unchanged. `build_recall_prompt(tok, question,
persona)` emits `<|system|>persona<|user|>question<|assistant|>` and truncates at the assistant
trigger [VERIFIED: `src/personacore/dialogue/serialize.py:92-116`]. A value in the persona span is
~30 tokens from the trigger (prompt is 46 tokens with a 13-token persona). To sit ~2 tokens from the
trigger the value must be at the **end of the user turn**, which means it is carried by the
`question` string, not by `persona=`. Two consequences the planner must handle:

1. The widened D-21 AST guard keys on `persona=`. The distance-~2 rung passes the value positionally
   inside `question` and would therefore be **invisible to that guard**. The D-18
   `assert_value_in_prompt` twin is what covers it — which is precisely why D-18 says every
   `draw_all` call site must assert *something*. Make this explicit in the allowlist rationale.
2. Natural framing at distance ~2 (D-11) means the question text itself must end on the value while
   still reading as a question. Filler text is explicitly the planner's discretion.

### Anti-Patterns to Avoid

- **Re-anchoring the threshold to the post-fix fairness-control re-run.** Sets the gate after seeing
  data. The re-run produces a *reported delta* (D-13), never a constant.
- **Different n across cells.** Makes `LADDER_CELL_PASS_K` a per-cell literal and makes D-14's
  monotonicity check read threshold artifacts as instrument anomalies.
- **Fewer draws in ladder cells to save time.** `n_answerable` at 4 draws is a different quantity
  from `n_answerable` at 9 and is not comparable to the floor.
- **Copying `phase14_factset_gate` logic into the Phase 16 driver.** D-16 forbids it; widen the
  public surface instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Confidence bounds | a new stats module | `erasure_gate.wilson_upper_bound` / `rule_of_three` | Committed at PREREG-01, stdlib, already the pre-registered idiom |
| Lower bound on a rate | a Wald/normal-approx lower bound | `1 - wilson_upper_bound(n - k, n, z)` | Repo precedent in `erasure_is_worth_attempting`; Wald degenerates to `[0,0]` at k = 0 |
| Token-length matching for synthetic spans | a new tokenizer census | `phase14_factset.token_census(tok, value)` — **already public** [VERIFIED: `scripts/phase14_factset.py:313`] | Only the *guessability probe* half needs D-16 widening |
| Exact-match scoring of a probe | a new matcher | `phase14_factset.exact_match_clean` (public, `:334`) and `phase14_recall.contains_value` (`:300`) | D-22 requires exactly one scorer across all four arms |
| Recall prompt assembly | string formatting | `dialogue.build_recall_prompt` | Single source of truth; harness and demo both import it |
| Arm D retrieval | an index / re-ranker / chunker | one forward pass, mean-pool the final hidden state, argmax cosine over 20 candidates | PERS-04 explicitly bounds this; anything more is out of scope by requirement |
| Candidate pool curation | a hand-written per-slot list | `LOCKED_VALUES ∪ {f.value for f in GATE_REJECTED_CANDIDATES}` | D-23; zero new editorial judgment, argument already written at `phase14_recall.py:325-338` |

**Key insight:** every quantity Phase 16 needs already exists in committed code. The phase's real
work is *placement and pre-registration*, not new machinery.

## Common Pitfalls

### Pitfall 1: PREREG-02 cannot pass in CI as configured (BLOCKING)
**What goes wrong:** `.github/workflows/ci.yml` uses `- uses: actions/checkout@v4` with no
`fetch-depth` [VERIFIED: read in-session]. The documented default is **1** — "Number of commits to
fetch. 0 indicates all history for all branches and tags." [CITED: github.com/actions/checkout]. In a
depth-1 clone `23a830c` is not in the object store, so `git merge-base --is-ancestor 23a830c <sha>`
errors and `git log --diff-filter=A -- <path>` returns nothing.
**Why it happens:** the ordering guard is the first test in this repo to query git *history* rather
than `git rev-parse HEAD` (which `provenance.git_sha()` does and which works shallow).
**How to avoid:** add `with: fetch-depth: 0` to the checkout step, and make the test **fail loudly**
on a shallow repo (`git rev-parse --is-shallow-repository` → `true` ⇒ raise) rather than skip. A
silently-skipped ordering guard is the "declared invariant silently becomes false" defect this
project names as its most recurring.
**Warning signs:** the PREREG-02 test passes locally and is green-but-blind in CI.

### Pitfall 2: comparing commit *timestamps* instead of *ancestry*
**What goes wrong:** `git log -1 --format=%ct` compares committer dates, which are rewritable, skewed
across machines, and non-monotonic after a rebase. A rebase could invert the ordering the test claims
to enforce while both dates still look fine.
**How to avoid:** use `git merge-base --is-ancestor <erasure_commit> <artifact_first_commit>`, where
`<artifact_first_commit>` is `git log --diff-filter=A --format=%H -- <path> | tail -1`. Ancestry is a
property of the DAG, not of a clock. Already verified working here: `23a830c` is an ancestor of HEAD,
and `results/phase16_recall_sample.json` was first added at `70dcc56` [VERIFIED: run in-session].
**Also handle:** an artifact that exists in the working tree but is not yet committed. It is
trivially *after* the pre-registration (it has no history at all), so it passes — but the test must
say so explicitly rather than reach that outcome by an empty loop.

### Pitfall 3: the widened AST guard scanning more files but asserting less
**What goes wrong:** D-21 widens the scan to `scripts/*.py` + `src/`. The current assertion is hard
equality `with_persona == ["run_fairness_control"]` [VERIFIED: `tests/test_phase14_scoring.py:445`].
Widening the scan naively forces relaxing that equality into a membership check, which is the guard
getting *weaker* while looking bigger.
**How to avoid:** keep hard equality, against an explicit allowlist keyed by `(file, function)` — the
literal shape D-21 specifies. Also keep the existing positive assertion that the bare-form call sites
are still present; a guard that only forbids can be satisfied by deleting all call sites.
**Warning signs:** the diff replaces `==` with `in` or `issubset`.

### Pitfall 4: the truncation cell measuring the dilution cell (D-27 made concrete)
**What goes wrong:** the recall prompt is 33 tokens bare, 46 with persona, against `block_size = 256`
[VERIFIED: CONTEXT.md Measured Facts]. Truncation cannot fire until dilution has already pushed the
context past 256 — so a "truncation" cell built independently is just the largest dilution cell under
a second name, and the report states one effect twice.
**How to avoid:** design the sweep as a single ordered dilution axis with `block_size` crossed at a
named step, and label the cells past that step as *dilution + truncation*, never as an independent
pressure.

**Where the dilution actually goes — and the `PERSONA_CAP` premise this pitfall used to carry, which
was itself false.** An earlier revision of this section read: *"`PERSONA_CAP = 140` [VERIFIED:
`serialize.py:21`] caps the persona span, so dilution past that must come from turns, not persona
lines."* The constant does exist at `serialize.py:21`, but **nothing on this path enforces it**
[VERIFIED: measured in-session 2026-08-12]:

- `cap_persona` (`serialize.py:115`) is the ONLY enforcer of `PERSONA_CAP`, and its only call sites
  are `scripts/make_transcripts.py:134` and `scripts/prepare_dialog_corpus.py:104`.
  `build_recall_prompt` (`:92`) **never calls it** — the cap does not bite on the recall path.
- `build_recall_prompt` calls `encode_dialogue(tok, list(persona), [(question, "")])` — **exactly one
  turn**. There is no turns axis to dilute along.

Consequence: the persona span reaches the 448-token target directly, and **all dilution happens
inside the persona span**. This stays filed as a pitfall because the constant's mere *existence*
invites the wrong inference — it did exactly that here, and the wrong inference propagated all the
way up into ROADMAP SC5 and REQUIREMENTS PERS-03 ("dilution across turns"), both amended to
**"dilution within the persona span"** at `79fa01a`. Phases 17 and 18 read this file: inherit the
corrected mechanism above, not the struck sentence.

Truncation itself is unaffected — still real, still derived from the dilution axis crossing
`block_size`. Only the *mechanism of the dilution* was mis-stated. `generate` crops to the **last**
`block_size` ids (`src/personacore/generation/core.py:65`, `idx[:, -bs:]`), so the fact-bearing
statement must sit at the **head** of the diluted persona span for a crossing cell to measure
anything at all.

### Pitfall 5: assuming synthetic strings might be ungeneratable
**Status: verified non-issue, recorded so it is not re-litigated.** With 7,645 of 8,192 ids masked as
`forbid_ids`, the obvious worry is that a synthetic value could be unreachable at sampling. It cannot
be: all 256 byte ids are live and BPE falls back to bytes for anything unmerged, so `encode()` can
never emit a dead id — the 7,645 dead ids are unreachable *merges*, not unreachable bytes [VERIFIED:
`scripts/phase14_factset_gate.py:276-281`, a measured no-op already written into the committed Phase
14 factset report]. Any ASCII synthetic string is generatable. Token-length matching still matters
(D-12) and is done with `token_census`.

### Pitfall 6: reading an all-fail ladder as a broken instrument
See Q2 below. All-fail is a normal outcome. The instrument-broken signal is different and specific:
**non-monotonicity** (a harder cell passing while an easier one fails), which D-14 already directs to
be recorded as a named anomaly without stopping the run.

## Code Examples

### Deriving and pinning the pre-registered literal

```python
# scripts/phase16_persistence.py  (driver — constants above, this is the reader)
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from erasure_gate import rule_of_three, wilson_upper_bound   # PREREG-01, stdlib only


def cell_passed(n_answerable, n_questions=LADDER_CELL_QUESTIONS):
    """One ladder cell's licensing decision. NOT a hypothesis test (STAT-06 / D-09).

    Passes when the one-sided lower bound on the question-level answerable rate clears the
    COMMITTED Phase 14 floor's upper bound. The integer literal is the gate; the bound below
    is the derivation, pinned by tests/test_phase16_ladder.py so it cannot silently drift.
    """
    lower = 1.0 - wilson_upper_bound(n_questions - n_answerable, n_questions, LADDER_CELL_Z)
    return n_answerable >= LADDER_CELL_PASS_K, lower


def cell_report(n_answerable, n_questions=LADDER_CELL_QUESTIONS):
    """STAT-02: denominator + bound always; rule-of-three whenever successes are zero."""
    row = {
        "answerable": n_answerable,
        "questions": n_questions,
        "rate": n_answerable / n_questions,
        "wilson_upper_95": wilson_upper_bound(n_answerable, n_questions),
    }
    if n_answerable == 0:                       # never a bare 0%
        row["rule_of_three_upper"] = rule_of_three(n_questions)
    return row
```

### PREREG-02 ancestry assertion

```python
# tests/test_phase16_prereg.py — CPU-only, GPU-free, no torch.
import pathlib, subprocess

_ROOT = pathlib.Path(__file__).resolve().parent.parent
PREREG_COMMIT = "23a830c"          # PREREG-01, 2026-08-12 16:27:43
V3_ARTIFACTS = ("results/phase16_*", "results/phase17_*", "results/phase18_*")


def _git(*args):
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_prereg_commit_precedes_every_v3_results_artifact():
    # A shallow clone cannot answer an ancestry question. FAIL, never skip: a silently
    # skipped ordering guard is the defect this project names as its most recurring.
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone — set fetch-depth: 0 on actions/checkout, or this guard is blind"
    )
    checked = 0
    for pattern in V3_ARTIFACTS:
        for path in sorted(_ROOT.glob(pattern)):
            rel = path.relative_to(_ROOT).as_posix()
            adds = _git("log", "--diff-filter=A", "--format=%H", "--", rel).split()
            if not adds:
                continue          # working-tree only: no history, trivially after PREREG-01
            first = adds[-1]      # git log is newest-first
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", PREREG_COMMIT, first),
                cwd=_ROOT, check=True,
            )
            checked += 1
    assert checked, "no committed v3.0 results artifact was checked — the guard matched nothing"
```

Ancestry, not timestamps (Pitfall 2). The final `assert checked` is what stops the test passing
vacuously once the globs stop matching.

## Q2 — Literature precedent for multi-token in-context copying at this scale

**Short answer: no directly transferable precedent was found. Plan for all-cells-fail as a normal
outcome.**

| Claim | Confidence | Source |
|---|---|---|
| Induction heads — prefix-match-and-copy — require ≥ 2 layers (a previous-token head composed with an induction head) and emerge at a sharp phase change during training | HIGH | [CITED: Elhage et al. 2021, *A Mathematical Framework for Transformer Circuits*; Olsson et al. 2022, *In-context Learning and Induction Heads*] |
| At 6 layers the architecture is therefore *sufficient* for induction in principle | MEDIUM | Inference from the above. Sufficiency of depth is not evidence that the circuit formed on this corpus |
| Span length per se is not the theoretical blocker — in the repeated-sequence setting each copied token becomes the trigger for the next, so induction chains across a span | MEDIUM | [CITED: Olsson et al. 2022 — the canonical demonstration is completion of a *repeated random sequence*, which is inherently multi-token] |
| ~33M-parameter models trained on TinyStories perform near-perfect associative recall | **LOW — DO NOT CITE AS SUPPORT** | [CITED: arXiv:2310.08049, *Is attention required for ICL?*]. The models that succeed at associative recall in that paper are **trained on the synthetic recall task itself**; TinyStories is used separately for the language-modelling comparison. Task mismatch, not just scale mismatch |
| Sustained retrieve-by-meaning-then-copy emerges at 13.9M on TinyStories + PersonaChat | **NO EVIDENCE EITHER WAY** | — |

**Why the induction result does not transfer.** Induction is triggered by a *literal prefix* present
in context: `... A B ... A →` predicts `B`. D-11 deliberately holds the framing natural, so the
prompt is `<|system|>my cat's name is <value> <|user|>what's your cat's name? <|assistant|>`. There
is no literal token sequence in the question that also precedes the value in the persona span. The
model must locate the antecedent *semantically*, then copy 4–8 tokens over a near-character-level
vocabulary. That is a strictly harder circuit than induction, and D-11's own reasoning already says
an instructed-copy rung would license nothing — so the easier, literature-matched task is out of
scope by decision, not by oversight.

**The dominant evidence is in-repo, not in the literature.** Phase 14 measured this exact model,
this exact prompt builder, real values, fact in the `<|system|>` span: **1 of 216 questions**. That
is an in-distribution measurement at n = 216 and it outweighs any transfer argument from models three
orders of magnitude larger.

**What this means for the planner:**
- Pre-register the **all-cells-fail branch as a first-class expected outcome**. D-14 already names it
  ("nenhum degrau aprovado" licenses only the SC1 capability-deficit statement). Do not add a
  "ladder failed ⇒ investigate the instrument" escape hatch; that would be an unwritten branch
  discovered after seeing the result.
- The `(span 1, distance ~2)` cell is the closest thing to the literature's setting and is the
  ladder's real discriminator. If **it** fails, the honest reading is "this model cannot use context
  for this task at all", and every higher cell failing is uninformative rather than surprising.
- If `(span 1)` passes and `(span 5)` fails, that is the D-11 distinction working as designed:
  "can use context, cannot sustain a copy". That is the outcome the 2-D grid exists to detect.
- The instrument-broken signal is **non-monotonicity**, not failure. D-14 already covers it.

## Runtime State Inventory

Not applicable — this is not a rename/refactor/migration phase. One adjacent item worth naming so it
is not mistaken for one: D-19 records that the PERS-05 fix **changes which seeds are drawn**, so the
Phase 14 fairness-control number does not reproduce bit-for-bit afterwards. No stored data, service
config, OS registration, secret, or build artifact carries a value this phase changes. Verified by
reading D-17..D-20 and by the absence of any datastore in the project (weights-only memory is the
project's design constraint).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (venv) | everything | ✓ | 3.11.15 | — |
| torch | the run | ✓ | 2.7.1 | — |
| MPS backend | the ~39 min run + ~80 min ladder | ✓ | `is_available() == True` | CPU (much slower) |
| pytest | all validation | ✓ | 9.0.3 | — |
| gradio | `tests/test_phase14_demo.py` collection | ✓ | 5.50.0 | none — omission is a hard collection error |
| git | PREREG-02 ancestry | ✓ | 2.50.1 | none |
| `checkpoints/convbase_slim.pt`, `convbase_best.pt`, `adapter.pt` | all four arms + ladder | ✓ | present | — |
| `results/phase16_recall_sample.json` | the binding fixture | ✓ | committed at `70dcc56` | — |
| Full git history in CI | PREREG-02 | **✗** | `fetch-depth: 1` | none — **must** set `fetch-depth: 0` |

**Missing dependencies with no fallback:** CI git history (Pitfall 1). One-line YAML change, and it
must land before the PREREG-02 test.

**Wall-clock budget (derived from CONTEXT.md's measured per-question medians):**
- Four-arm run: 270 × (2.181 + 3.183 + 3.185 + 0.009) ≈ **38.5 min**, consistent with the citable
  ~39 min (realistically 35–44 min). Do not quote "39.2 min" — CONTEXT.md records why.
- Ladder at the recommended n = 216 per rung: 7 rungs × 216 × 3.183 s ≈ **80 min**.
- Total ≈ **2 hours**. D-05 says the run is not cost-constrained; state the number anyway so the
  planner chooses n deliberately rather than discovering it.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (project is PEP 621 installable); `tests/conftest.py` present |
| Quick run command | `.venv/bin/pytest tests/test_phase16_ladder.py tests/test_phase16_prereg.py tests/test_phase14_scoring.py -q` |
| Full suite command | `make test` (equivalently `.venv/bin/pytest -q`) |

This phase ships no user-facing feature. It ships **a measurement and a pre-registration**, so
validation means exactly two things: (1) CPU-only, GPU-free tests that prove the instrument is
correct *before* any long run, and (2) a structural proof that the pre-registration preceded the run.
Every surface below is CPU-only and torch-free except where noted.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File |
|--------|----------|-----------|-------------------|------|
| STAT-05 / PERS-01 | `LADDER_CELL_PASS_K` is the smallest k satisfying the pre-registered bound at `LADDER_CELL_QUESTIONS` — the literal cannot silently drift from its derivation | unit | `pytest tests/test_phase16_ladder.py::test_pass_k_is_the_derived_minimum -x` | ❌ Wave 0 — new `tests/test_phase16_ladder.py` |
| STAT-05 | `LADDER_FLOOR_UPPER_95` equals `erasure_gate.wilson_upper_bound(1, 216)` exactly, and `LADDER_FLOOR_QUESTIONS × LADDER_CELL_DRAWS == 1944` (the committed Phase 14 denominator) | unit | same file | ❌ Wave 0 |
| STAT-05 / D-14 | `licensed_headline()` is total over the rung lattice: every reachable combination of passed rungs maps to exactly one branch, and the all-fail branch returns the SC1 capability-deficit statement | unit | `pytest tests/test_phase16_ladder.py::test_licensed_headline_is_total -x` | ❌ Wave 0 |
| STAT-05 | `licensed_headline()` imports its constants — the verdict strings contain no retyped numeric literal (AST scan of the driver's string constants for the threshold digits) | unit (AST) | same file | ❌ Wave 0 |
| STAT-02 | Every reported proportion carries a denominator and a bound; a zero cell emits `rule_of_three` and never the string `0%` | unit | `pytest tests/test_phase16_ladder.py::test_no_bare_zero_percent -x` | ❌ Wave 0 |
| STAT-01 | The cell statistic counts **questions** (`n_answerable`), not draws — fed a fabricated record set where the two diverge, the reported denominator is the question count | unit | same file | ❌ Wave 0 |
| STAT-06 / D-09 | Exactly 6 comparisons enter the Holm family; the sign-test enumeration over 2⁸ reproduces `p(8/8) = 0.0078125`, `p(7/8) = 0.0703125`, `p(7/7) = 0.015625`; ties count against | unit | `pytest tests/test_phase16_stats.py -x` | ❌ Wave 0 — new `tests/test_phase16_stats.py` |
| STAT-06 | Nothing outside those 6 pairs is gated: AST scan of the driver finds no second call into the Holm/verdict path | unit (AST) | same file | ❌ Wave 0 |
| PERS-05 | `run_fairness_control` passes `item.seed_index`, not `enumerate` index — behavioural (a monkeypatched `draw_all` records the index it received, over a question list whose `seed_index` is deliberately not positional) **and** AST (no `enumerate(questions)` remains in that function) | unit | `pytest tests/test_phase14_scoring.py -k seed_index -x` | ⚠️ extend existing `tests/test_phase14_scoring.py` |
| PERS-06 | `assert_value_in_prompt` exists as a named function, takes `values` as a **parameter** (never a module-level constant — LAZY-IMPORT RULE), and checks both the normalized string and the contiguous id run, mirroring `assert_no_value_in_prompt` at `:398` | unit | `pytest tests/test_phase14_scoring.py -k assert_value_in_prompt -x` | ⚠️ extend existing |
| PERS-06 | **Every** `draw_all` call site asserts something — AST walk finds no call site lacking a paired `assert_value_in_prompt` / `assert_no_value_in_prompt` in its enclosing function; no skip mode exists | unit (AST) | same file | ⚠️ extend existing |
| PERS-06 / D-21 | The `persona=` guard scans `scripts/*.py` **and** `src/` in full and still asserts **hard equality** against an explicit `(file, function)` allowlist — proven RED against a deliberately added out-of-allowlist `persona=` call site before being reverted | unit (AST) | `pytest tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control -x` | ⚠️ widen existing (`:425`) |
| PERS-02 | Arms share `max_new_tokens`, `forbid_ids`, `stop_ids` and context length — asserted against one shared config object, not four literals | unit | `pytest tests/test_phase16_driver.py -k parity -x` | ❌ Wave 0 — new `tests/test_phase16_driver.py` |
| PERS-02 / D-01 | `CONDITION_ORDER` is a module-level constant of exactly the four locked names in the locked order | unit | same file | ❌ Wave 0 |
| PERS-04 / D-23 | Arm D's candidate pool is exactly `LOCKED_VALUES ∪ {f.value for f in GATE_REJECTED_CANDIDATES}`, 20 distinct values, and the reported chance floor literal is **0.05** (not 0.125 — D-25's flagged reconciliation) | unit | same file | ❌ Wave 0 |
| PERS-04 / D-22 | Arm D is scored by the same `contains_value` as A/B/C — AST scan finds exactly one scorer symbol in the driver | unit (AST) | same file | ❌ Wave 0 |
| PERS-03 / D-27 | The sweep's truncation cells are derived from the dilution axis crossing `block_size`, not declared independently: a test asserts every truncation-labelled cell has context length > 256 and every non-truncation cell ≤ 256 | unit | same file | ❌ Wave 0 |
| D-12 | Every synthetic ladder value round-trips through `token_census` at its target token length and is rejected by the guessability gate | unit | `pytest tests/test_phase16_ladder.py -k synthetic -x` | ❌ Wave 0 |
| D-16 | The widened public entry point on `phase14_factset_gate.py` exists, takes an arbitrary string, and the Phase 16 driver **imports** it — AST scan proves no copied probe logic in the driver | unit (AST) | same file | ❌ Wave 0 |
| — | `test_no_fact_strings_at_import` still passes with the new driver and new tests in scope (docstrings included) | unit | `pytest tests/test_phase14_factset.py -x` | ✅ exists |
| — | The 270-question fixture is unchanged | unit | `pytest tests/test_phase16_fixture_regen.py -x` | ✅ exists |
| PREREG-02 | `erasure_gate.py`'s commit is a git **ancestor** of the first commit adding every v3.0 results artifact; fails loudly on a shallow clone; fails if it checked nothing | unit | `pytest tests/test_phase16_prereg.py -x` | ❌ Wave 0 — new `tests/test_phase16_prereg.py` |
| STAT-04 | `pyproject.toml` is byte-identical to its v2.0-close state (hash pinned as a literal) | unit | `pytest tests/test_package.py -k pyproject_unchanged -x` | ⚠️ extend existing `tests/test_package.py` |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest tests/test_phase16_ladder.py tests/test_phase16_stats.py tests/test_phase16_driver.py tests/test_phase16_prereg.py tests/test_phase14_scoring.py -q` (all CPU-only, seconds)
- **Per wave merge:** `make test` (full CPU-only suite, ~2 min)
- **Phase gate:** full suite green **before** the ladder runs, not merely before `/gsd:verify-work`.
  PERS-01 makes the ladder blocking, so a ladder run on an unvalidated instrument is unrecoverable —
  the numbers cannot be re-derived after the fact without breaking pre-registration.

### Wave 0 Gaps
- [ ] `.github/workflows/ci.yml` — `fetch-depth: 0` on the checkout step. **Must land before**
      `tests/test_phase16_prereg.py`, or the guard is green-but-blind in CI (Pitfall 1).
- [ ] `tests/test_phase16_prereg.py` — PREREG-02
- [ ] `tests/test_phase16_ladder.py` — threshold derivation, `licensed_headline()` totality,
      STAT-01/02 reporting shape, synthetic-value vetting, D-16 import proof
- [ ] `tests/test_phase16_stats.py` — sign-test enumeration, Holm family closure, tie policy
- [ ] `tests/test_phase16_driver.py` — arm parity, `CONDITION_ORDER`, arm-D pool and scorer, D-27
      sweep structure
- [ ] Extend `tests/test_phase14_scoring.py` — PERS-05 behavioural + AST, `assert_value_in_prompt`,
      every-`draw_all`-asserts, widened D-21 guard (prove RED before landing, per the 15-03
      precedent: "a structural guard nobody has watched fail is a guard nobody has verified")
- [ ] Extend `tests/test_package.py` — `pyproject.toml` byte-identity literal (STAT-04)
- Framework install: none — pytest 9.0.3 already present

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Every ladder cell will use n = 216 questions × 9 draws (the planner may choose otherwise) | Q1 constants block | `LADDER_CELL_PASS_K` changes — the table gives k_min for six other n values, so the fix is a lookup, not a redesign |
| A2 | The distance-~2 rung carries its value inside the `question` string rather than `persona=` | Ladder wiring | If the planner finds another placement, the D-21 guard blind-spot note may not apply. The `assert_value_in_prompt` coverage requirement stands either way |
| A3 | `PREREG_COMMIT = "23a830c"` is the right SHA to pin (short form) | PREREG-02 example | Ancestry query fails loudly on a wrong SHA rather than passing silently. Prefer the full 40-char SHA in the committed test |
| A4 | Multiplicity should be priced into the per-cell z rather than disclosed in prose only | Q1 | Both are defensible. The literal is 10 under z-pricing and 8 without; the planner must pick ONE before the run and record which and why |
| A5 | `~80 min` ladder estimate assumes ladder cells run at arm-B per-question cost (3.183 s median) | Environment Availability | Ladder cells run the base model with a persona span — same configuration as arm B — so this should hold; the CONTEXT.md 11.5% cross-run spread on arm A means treat it as ±15% |

## Open Questions (RESOLVED)

> **All four open items below were settled during planning (2026-08-12) and are now
> pre-registration, not preference.** Phases 17 and 18 read this file — the resolutions are inlined
> here so a later reader does not re-open a question that already has a committed answer in a plan.

1. **Does the top rung share `LADDER_CELL_PASS_K`, or is it exempt?**
   - What we knew: D-13 makes the fairness-control re-run the top rung; D-14 says the threshold is
     "per cell" (6 cells). The re-run's prior is 1/216, so it would need ≥ 10/216 to pass.
   - What was unclear: whether `licensed_headline()` treats the top rung as a passable rung or
     purely as the D-13 delta measurement.
   - **RESOLVED — `16-04-PLAN.md` §Choice 3.** The same literal applies to all 7 rungs. `k_min` is
     10 at `n = 216` whether multiplicity is priced at 6 cells or 7 rungs (`z = 2.393980` and
     `z = 2.449998` both yield 10), so it costs nothing and removes an ambiguity that would
     otherwise be resolved after seeing a number.

2. **How many synthetic values per cell?**
   - What we knew: D-12 requires token-length matching and guessability filtering; the 216 core
     questions span 8 facts.
   - **RESOLVED — `16-05-PLAN.md` Task 1 (`SYNTHETIC_FACT_ORDER`) and Task 2 (`SYNTHETIC_VALUES`).**
     One synthetic value **per fact**, 8 per span, positionally aligned to the fixture's own
     `provenance.core_facts` order, so each of the 216 questions gets the synthetic value matched to
     its own slot. This preserves the fixture's balance (14 taught + 13 held-out per fact) and keeps
     D-06's per-fact grouping key usable on ladder output too.

3. **Assumptions Log A1 — cell size `n`.**
   - **RESOLVED — `16-04-PLAN.md` §Choice 1.** `LADDER_CELL_QUESTIONS = 216`, the full core set
     (112 `core_taught` + 104 `core_held_out`). Identical to the floor's `n` and the top rung's `n`,
     which is what makes the comparison against `1/216` apples-to-apples and what D-15's
     proxy-validity check requires.

4. **Assumptions Log A4 — price multiplicity into `z`, or disclose it in prose?**
   - **RESOLVED — `16-04-PLAN.md` §Choice 2.** Priced into the per-cell `z`:
     `LADDER_CELL_Z = 2.393979799818510`, the one-sided `1 - 0.05/6` quantile. A false pass licenses
     the STRONGER headline, which is the over-licensing direction this milestone exists to avoid;
     the cost is two extra questions. This is a **choice of literal, not a hypothesis test** — no
     p-value is computed on the ladder and no verdict is emitted there, so D-09's Holm family stays
     closed at exactly the 6 arm pairs and STAT-06 is untouched.

## Sources

### Primary (HIGH confidence — verified in-session)
- `scripts/erasure_gate.py:139,161` — `wilson_upper_bound`, `rule_of_three`, `_Z_ONE_SIDED_95`;
  `erasure_is_worth_attempting` for the lower-bound-by-complement idiom
- `scripts/phase14_recall.py:300,315,542,689,692,838-850,1147-1223` — `contains_value`,
  `score_question`, `draw_all`, `seed_index`, `stamp_seed_indices`, tier aggregation,
  `run_fairness_control` (PERS-05 defect at `:1184`, unnamed twin at `:1188-1192`, `n_answerable` at
  `:1219`)
- `scripts/phase14_factset.py:313,334` — `token_census` and `exact_match_clean` are **already
  public**; only the guessability probe half needs D-16 widening
- `scripts/phase14_factset_gate.py:73,87,111,116,276-281` — private surface, and the measured
  `forbid_ids` no-op that closes Pitfall 5
- `src/personacore/dialogue/serialize.py:21,92-116` — `PERSONA_CAP = 140`, `build_recall_prompt`
- `tests/test_phase14_scoring.py:405-452` — the AST guard and its hard-equality assertion
- `.github/workflows/ci.yml` — `actions/checkout@v4` with no `fetch-depth`
- Arithmetic computed in-session with the repo's own functions: floor upper bound 0.020481915502612365,
  `rule_of_three(216) = 0.013889`, k_min table across n, `z(0.05/6) = 2.393980`, `z(0.05/7) = 2.449998`
- Git facts verified in-session: `23a830c` is an ancestor of HEAD; `results/phase16_recall_sample.json`
  first added at `70dcc56`

### Secondary (MEDIUM confidence)
- [CITED: github.com/actions/checkout] — `fetch-depth` default is `1`; "0 indicates all history for
  all branches and tags"
- [CITED: Olsson et al. 2022, *In-context Learning and Induction Heads*, Transformer Circuits] —
  induction heads as prefix-match-and-copy over repeated sequences; emergence as a training phase
  change; two-layer sufficiency
- [CITED: Elhage et al. 2021, *A Mathematical Framework for Transformer Circuits*] — the two-layer
  previous-token + induction-head composition

### Tertiary (LOW confidence — flagged, not used as support)
- [CITED: arXiv:2310.08049, *Is attention required for ICL?*] — ~33M-param models, TinyStories
  corpus, near-perfect associative recall. **Task-mismatched**: the recall-capable models are trained
  on the synthetic recall task itself. Recorded so a later reader knows it was considered and why it
  was not leaned on
- [CITED: arXiv:2404.07129, *What needs to go right for an induction head?*] — abstract only;
  identifies three subcircuits driving IH formation, no depth/vocab/multi-token specifics retrievable
  from the abstract

## Metadata

**Confidence breakdown:**
- Q1 threshold construction: **HIGH** — every input is a committed number, every output was computed
  in-session with the repo's own committed functions
- Q2 literature transfer: **LOW** — no scale-and-task-matched precedent exists; the honest answer is
  that the in-repo 1/216 dominates, and that is stated rather than padded
- Q3 validation architecture: **HIGH** — file paths, existing test names, and the CI blocker were all
  read directly
- Wall-clock estimates: **MEDIUM** — derived from CONTEXT.md's own medians, which carry a recorded
  11.5% cross-run spread

**Research date:** 2026-08-12
**Valid until:** the numbers do not decay (they are committed repo facts). Re-check the
`actions/checkout` default if CI is upgraded past v4.
