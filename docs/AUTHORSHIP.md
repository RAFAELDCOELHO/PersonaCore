# PersonaCore v4.0: authorship record

**Version 1.1, 2026-09-03.** Ten items marked `[SEM EVIDÊNCIA — confirmar com Rafael]` were open in version 1.0;
the author answered all ten the same day and the answers are recorded in §9, each beside what the
artifacts confirm or correct. The inline markers and §8 are left as written.
Reconstructed 2026-09-03 from repository artifacts only, at `main` HEAD `15dce85`. Nothing in this
document was taken from memory or from conversation with the author. Every claim points to a commit,
a file path, a planning document, a run log, or a session transcript. Where no artifact exists, the
claim is marked and listed in §8 instead of being filled in.

**Scope.** Milestone v4.0 (*Leakage Mitigation and Relearning Validation*), Phases 20–25, commits
`4f0423b` (2026-08-20, "start milestone v4.0") through `15dce85` (2026-09-02). Phase 25 is in
progress; §7 reports its state and no result from it.

**Reading this document.** "The author" is Rafael D. Coelho, the sole human contributor
(`CITATION.cff`, `git shortlog`). "The AI" is Claude Code unless another tool is named (§4). The
three words *decision*, *execution* and *verification* are used with fixed meanings: a decision is a
choice recorded in a `CONTEXT.md`, `DISCUSSION-LOG.md`, `HUMAN-UAT.md` or a `checkpoint` answer; an
execution is code, tests or documents written by an agent under a plan; a verification is a check
whose output is committed. Who did each is stated per row, not assumed.

**Evidence annex.** Raw `git log --stat`, `git blame` summaries, a commit-trailer census and a plan
ledger are committed under `docs/authorship-evidence/`; this document cites them by filename.

---

## 1. Hypotheses

### 1.1 What v4.0 set out to test

v3.0 closed with two measured negatives: black-box extraction recovered 92/104 = 88.5% of taught
facts (`LEAKAGE_DEMONSTRATED`, `results/phase18_extraction_report.md`), and selective erasure
returned `FAILURE` while destroying 77.6% of dialogue adaptation
(`results/phase19_erasure_report.md`). v4.0 was scoped as the answer to the first
(`.planning/PROJECT.md:154-238`, `.planning/ROADMAP.md` §"v4.0", both first committed 2026-08-20 at
`4f0423b` and corrected the same morning at `29a86e5` after the research pass).

The milestone's testable claims, as committed:

| # | Hypothesis | Where it is written down | Status at HEAD |
|---|---|---|---|
| H1 | **Existence gate.** There exists at least one sweep point, for at least one mitigation arm, that simultaneously satisfies (a) extraction ≤ X, (b) taught-fact recall ≥ Y, (c) general capability ≥ C. | `scripts/mitigation_gate.py` (pin, first add `95b3c8a` 2026-08-20 16:27); GATE-01…GATE-09 in `.planning/REQUIREMENTS.md:21-83` | Untested. Phase 25 will produce the points. |
| H2 | **Pre-registered null, both branches publishable.** Research assigned high prior probability to the DP arm being a null (72σ noise-to-signal at L=8; Secret Sharer Table 3 precedent). GATE-10 commits both readings of the n=8 vs n=64 comparison before either runs. | `.planning/research/SUMMARY.md` ("Executive Summary", 2026-08-20); `ROADMAP.md` §"The expected null is a deliverable"; `REQUIREMENTS.md:84-88`; `mitigation_gate.capacity_comparison` | Untested. |
| H3 | **ε is independent of N at q=1** (the premise the n=64 leg rests on). | CAL-03, `REQUIREMENTS.md:298`; rule in `23-CONTEXT.md` D-05 | **Confirmed** 2026-08-26: `results/phase23_cal03_wiring.json`, `verdict: true`, ε(n=8) = ε(n=64) = 24.38161088311366, T = 4 on both. |
| H4 | **σ=0 reproduces the unmitigated control** (diagnostic: any deviation beyond the seed floor is a DP-path bug, since every bug in this class improves utility). | DPSGD-06; `scripts/phase23_prereg.py::sigma_zero_verdict`, blind-committed `c7de5d4` 2026-08-26 while `git ls-files 'results/phase23_*'` was empty | **Halted, then confirmed** (see §5.4). First reading 0.7837 vs control 0.5615: HALT. Root cause: invalid comparator. Matched comparator: deviation exactly 0.0, `proceed`. |
| H5 | **Relearning attack** and **empirical canary audit** (Phases 26–27). | `REQUIREMENTS.md` RELRN-01…05, CANARY-01/02 | Not started. |

### 1.2 The pre-registration and its ordering proof

The gate's evidentiary value is the ordering, and the ordering is enforced by a test rather than by a
date. `tests/test_phase20_prereg.py` asserts, on every CI run over a full-depth clone
(`.github/workflows/ci.yml:14-27`), that every commit touching `scripts/mitigation_gate.py` is an
ancestor of the first-add commit of every `results/phase20_*` artifact, using
`git merge-base --is-ancestor` rather than timestamps (module docstring, lines 1-30). The first v4.0
number of any kind, the adapter-regime retention floor in `results/phase20_retention_floor.json`
(`git_sha` `669d082`, 2026-08-21), was committed the day after the pin.

The pin is byte-identical across its two correction waves: `20-VERIFICATION.md` (2026-08-21,
`status: passed`, 7/7) records `git diff --exit-code cc99321 -- scripts/mitigation_gate.py` empty
against the original pin. Corrections to a frozen pin are dated continuations, never edits (Phase 20
D-24; `scripts/_addendum.py`; `scripts/phase20_gate_coverage.py`; `scripts/phase21_unit_continuation.py`).

Exactly two chosen constants exist in the pin, both labelled as preference: `F_C = 0.5`
(`scripts/mitigation_gate.py:217`, "PREFERENCE, not a derivation") and `f_Y = 0.7`
(`20-CONTEXT.md` D-16, D-18). Every other threshold is measured or imported (X from a Wilson bound
plus `MARGIN_K` × a two-seed floor, D-09; the (c) caps from imported constants, D-03/D-04).

---

## 2. Experimental decisions

The GSD workflow this project used produces, for each phase, a `CONTEXT.md` (the locked decisions),
a `DISCUSSION-LOG.md` (the alternatives offered and the choice), and for three phases a
`HUMAN-UAT.md` (rulings the verifier could not make). Each discussion log opens with the same
sentence: *"Every area opened with the user stating a position and naming a premise to verify"*
(`20-DISCUSSION-LOG.md:12`, mirrored in 21, 22, 24, 25). The tables below are read from those files.
"Author" means the human; "AI" means the assistant in the discussion session; "AI (discretion)"
means a decision the `CONTEXT.md` explicitly lists under *Claude's Discretion*.

### 2.1 Gate thresholds and comparators (Phase 20, 2026-08-20)

| Decision | Chosen | Rejected alternatives | Decided by | Recorded at |
|---|---|---|---|---|
| Form of condition (c) | Band on the ON−OFF adaptation gap, `control_gap` a required kwarg | two-sided band on raw PPL; upper bound only re-anchored; keep GATE-02 literally | Author (`20-DISCUSSION-LOG.md` Q1); the AI's arithmetic showed "band" and "re-anchor" were the same move and that the literal cap *selects for destruction* | `20-CONTEXT.md` D-01, D-02 |
| Retention leg form | One-sided cap, floor re-measured in the adapter regime (0.008681618994239138, 7.94× tighter than the borrowed Phase-12 value) | symmetric band; leave floor at 0.068930; drop retention | Author (Q2); measurement run live during the discussion | D-05, D-06; `results/phase20_retention_floor.json` |
| X, the extraction ceiling | `wilson_upper(nt_successes, n) + MARGIN_K × extraction_noise_floor`, zero chosen constants | blind-calibrated floor; fraction of the retrained control | Author, with the Wilson-upper refinement credited to the author (Q1 under "X") | D-09, D-11, D-12 |
| Y | Pair (taught, held-out), each ≥ `f_Y` × its own retrained-control value | derive from v2.0's 0.4921/0.3483 (forbidden by GATE-04) | Author (Q2 under "Y") | D-15, D-16 |
| `f_Y` | 0.7 ("spend up to 30% of personalization") | 0.8; 0.6; defer until the frontier is plotted (table at `20-DISCUSSION-LOG.md:189-198`) | Author | D-16 |
| `f_C` | 0.5, separate from `f_Y`; hard non-vacuity floor measured at 0.2237 | 0.7 (same as `f_Y`, "(c) becomes a second utility bar"); 0.3 ("thin margin") | Author (Q3) | D-17 |
| Per-point K | Closed menu `K_RUNGS = (48, 24, 16, 8)` committed now, rung selected by Phase 23 measurement, ratchet (may only increase) | none offered | Author, resolving a contradiction between CAL-04 and CAL-02 | D-19, D-20; `mitigation_gate.py:254` |
| GATE-07/08/09 mechanics (arm identity, provisional → `INCONCLUSIVE`, destroyed-model fixture from real Phase-19 readings) | as listed | `PASS` with `provisional=True` explicitly rejected | **AI (discretion)**, accepted by the author with precedent cited per item | `20-CONTEXT.md` D-28…D-30 |

### 2.2 The privacy unit and the n=64 corpus (Phase 21, 2026-08-22)

| Decision | Chosen | Rejected alternatives | Decided by | Recorded at |
|---|---|---|---|---|
| What one privacy record is | One taught fact (`PRIVACY_UNIT = "one taught fact"`, `scripts/mitigation_unit.py:85`) | Poisson-sampled 256-token windows (STACK/FEATURES/PITFALLS research passes) | The research synthesis (AI, 2026-08-20) computed both designs; the fork "resolves in ARCHITECTURE's favour" (`research/SUMMARY.md`). The human ratification is in `21-CONTEXT.md` session 1, **which has no discussion log** (`21-DISCUSSION-LOG.md:8`). | UNIT-01; `21-CONTEXT.md` |
| Shard geometry | Ragged (each fact padded to its own window count); loss = mean over a fact's windows | uniform W=5; `vmap` over facts (refused by `torch.stack` on ragged shards) | Measured (benchmark table in D-02); session 1, no log | D-01…D-03 |
| n=64 composition | 8 `LOCKED_FACTS` + 56 unscored filler in a **new module** `scripts/phase21_filler.py` | 64 fresh facts (contradicts GATE-10/CAL-03/FRONT-01, all pre-registered at n=8); reuse the 28-fact pools (load-bearing, not spare); include the soft tier (n=10) | Author, position stated before options, three premises checked and all found true (`21-DISCUSSION-LOG.md` "Premise check 1–3", Q1–Q2) | D-12…D-14 |
| Filler rendering and slots | Same `render_family`, 22 rows; new filler-only slots via an additive kwarg | lighter renderer; reuse the 11 existing slots (would seat ~5 rivals inside each scored slot) | Author (Q3, Q4) | D-15, D-16 |
| Guessability probe for filler | Deterministic half in full; the 1,792-generation probe waived **with the reason recorded** | run the probe; seeded subsample | Author (Q5), after the AI surfaced a contradiction inside the author's own Q1 answer | D-17 |
| δ | Literal `1e-5`; the `1/N^1.1` recipe recorded as self-contradictory (δ·N = 0.81 at N=8) | `1/N^1.1` | Fixed at requirements stage (UNIT-05, `REQUIREMENTS.md:112`, 2026-08-20) | `mitigation_unit.py:171` |

### 2.3 DP-SGD mechanism and accountant (Phase 22, 2026-08-25)

| Decision | Chosen | Rejected alternatives | Decided by | Recorded at |
|---|---|---|---|---|
| Who owns `.grad` during a DP step | DP owns the private accumulator; replay stays in `.grad`; `p.grad += private_accum` is the single combining write | DP owns both; tensor hooks (measured infeasible: global per-record norm unknown until `backward()` completes) | Author, quoted in Portuguese in the log | `22-DISCUSSION-LOG.md` §"Gradient plumbing"; D-01 |
| Where `1/N` lives | sum → noise → divide (sensitivity stays C, independent of N) | keep `/accum`, scale C by N | Author | D-02 |
| Structural guarantees | All four (AST guard, runtime differential, single-write assertion, per-micro-step drain) | any subset | Author, multi-select | D-05 |
| Noise RNG | Dedicated `torch.Generator`, device-bound, own checkpoint slot | skip draw at σ=0; rely on dropout literals | Author, **after** demanding a measured fact first (CPU/MPS generator sequences do not match; native MPS noise 1.428 ms/step vs 10.234) | D-07; `22-DISCUSSION-LOG.md` §"Noise RNG source" |
| Accountant home | `src/personacore/privacy/accountant.py` (first v4.0 content under `src/`, "deliberate, for portfolio visibility") | `scripts/phase22_accountant.py` | Author | D-10 |
| Accountant mathematics | Both directions (ε←σ and σ←ε); quadrature oracle of independent mathematics | none offered (the author's position was measured, two clauses found false, both corrections favouring the same conclusion) | Author | D-12, D-13 |
| Adjacency relation pinned | Added as D-18 after the research pass | none offered | Author ("on the user's explicit decision") | `22-CONTEXT.md` header |

### 2.4 Cost calibration, the σ=0 diagnostic, and the budget (Phase 23, 2026-08-26 → 08-29)

| Decision | Chosen | Rejected alternatives | Decided by | Recorded at |
|---|---|---|---|---|
| Venue | Local M3/MPS; Kaggle P100 remains a documented fallback | none offered | Author | `23-CONTEXT.md` D-01 |
| Seed floor | Measured at N seeds **before** σ=0 runs, then pinned as a literal | assume a floor | Author | D-03; `scripts/mitigation_budget.py` first add `dc2147f` |
| Breach rule | Halt the entire sweep, no override flag | warn and continue | Author | D-04; `phase23_prereg.py:271` |
| CAL-03 rule | Bit-identical ε at n=8 vs n=64, plus T asserted equal; no tolerance | relative tolerance | Author | D-05 |
| After the HALT (§5.4) | Build a **protocol-matched comparator** as its own gap-closure wave (23-15…23-20); re-run the unedited blind rule | treat as a DP-mechanism defect (excluded by a 72/72-tensor probe agreeing to 2.178e-07) | Author; the debug record says "Await user decision" and then that the phase was scheduled; the unblock is a human commit, `746ecf6` 2026-08-28 10:32 | `.planning/debug/sigma-zero-beats-control.md`; `746ecf6` |
| `CURVE_K` and `SWEEP_POINTS` | **16 and 16** | K ∈ {48, 24, 8}; the per-rung cost table was computed and presented with no default and no recommendation | **Author, at a blocking `checkpoint:decision`**; the reply is stored verbatim in `scripts/mitigation_budget.py:443-450` (`CURVE_K_PROVENANCE.selected_reply_verbatim`), committed `0a23aca` 2026-08-28 17:18 | `23-13-SUMMARY.md` §"The Checkpoint Answer, Verbatim" |
| Never-taught arm seeds | Same 5-seed ladder as the control floor | one seed | Author, closing a fork the researcher routed to them | D-08 |
| UAT rulings | DPSGD-06 record retracted in place (`7296b31`); permanent positive control for the never-taught scorer built now (`17c28c8`) | accept the divergence; defer the guard | Author, quoted | `23-HUMAN-UAT.md` items 1–2 |

### 2.5 Adversarial arm (Phase 24, 2026-08-29 → 08-30)

| Decision | Chosen | Rejected alternatives | Decided by | Recorded at |
|---|---|---|---|---|
| Discussion order | All four areas, ordered by dependency ("1, then 4, then 2, then 3") | presented order | Author | `24-DISCUSSION-LOG.md` |
| Adversarial episode target | Slot-specific, value-free refusal | generic slot-free refusal; per-fact refusal (a refusal naming the value contains the value) | Author; a pre-dated author todo already fixed this and was folded rather than re-asked | D-01, D-02 |
| Training tier | `core_taught` only ({F1, F2, F6}) | add non-reserved held-out; both tiers | Author (1.3) | D-03 |
| Ratio unit | Episodes; repetition policy at n=64 kept as a separate decision | tokens vs `teaching_tokens`; tokens vs a public denominator | Author (2.1, 2.2) | D-06, D-07 |
| Grid upper extreme | 1.909 (the n=8 pool ceiling) | 1.0; wide top with a truncation rule | Author (2.4) | D-09; `mitigation_budget.py:633` |
| Held-out attack family | A2, as a mechanical consequence of training on A1 + A3 | A2 plus one trainable family | Author (4.1) | D-10, D-12 |
| Fact-keyed vs frame-keyed ambiguity | Clean-frame filler refusal rate, with a reading rule | accept and declare; filler attack probe | **AI recommended option 3; author took it** and added the reading rule | D-11 |
| Grid spacing, permutation form, module location | plan-level detail | none offered | AI (discretion) | `24-CONTEXT.md` §Claude's Discretion |

### 2.6 The frontier sweep (Phase 25, 2026-08-31)

| Decision | Chosen | Rejected alternatives | Decided by | Recorded at |
|---|---|---|---|---|
| Control point | Re-run at both capacities; Phase 23's 790/1008 becomes a bit-level reproduction check | import n=8; import recall only | Author (Q1) | D-01 |
| SC1's comparator | **Kept as an active check**, comparator moved by dated continuation to the Phase-23 matched control | *AI recommended treating SC1 as discharged*; keep v2.0 literal | **Author overrode the AI's recommendation** (`25-DISCUSSION-LOG.md` Q2) | D-02 |
| Sweep size | All 44 points as pinned | trim the n=64 DP leg; decide after extremes | Author (Q8) | D-08 |
| Promotion rule | Lazy, candidate-triggered; if more candidates clear than budget holds, promote **all** | subset chosen after seeing which cleared | Author ("PRE-REGISTERED RULE, user-stated", Q11) | D-11 |
| σ placement | σ literals landing on a round ε ladder, one ladder reused at both capacities | log-spaced σ; dense where extraction collapses | Author (Q17) | D-17 |
| σ_hi | Probed before pinning, plus a ratchet extension rule | probe only; rule only | Author (Q18) | D-18 |
| Exact σ/ε literals, `CLIP_NORM`, heartbeat threshold, plist shape | measured outputs | none offered | AI (discretion), pinned after the probes at `049a6bb` 2026-09-01 | `25-CONTEXT.md` §Claude's Discretion; `mitigation_budget.py:770, 862, 930, 988` |
| Condition (c) reopening (Area 7) | Six producers added; D-48/D-49 corrected by dated continuation to the governing adapter-regime floor | leave "Nothing to fix" (D-35) standing | Author-authorised continuation (`STATE.md` frontmatter, "user-authorised"); the magnitude check that preceded it is attributed to the author only in a vault note (see §4.3 on why that note is weak evidence) | `25-CONTEXT.md` D-45…D-51 |

---

## 3. Implementation

### 3.1 What git can and cannot show

Every one of the 603 commits between `v3.0` and HEAD is authored under three identities that all
resolve to the author's e-mail, plus seven by `Cursor Agent` (`docs/authorship-evidence/commit-trailer-census-v4.0.txt`):

| Identity | Commits | What they are |
|---|---|---|
| `Rafael <rafael.d.cooelho@gmail.com>` | 592 | everything produced in Claude Code sessions, by the orchestrating session and by GSD sub-agents |
| `RAFAELDCOELHO` (same e-mail) | 4 | GitHub-side merges of PRs #1, #2, #4 and one `CITATION.cff` merge |
| `Cursor Agent <cursoragent@cursor.com>` | 7 | PRs #1 and #2, 2026-09-01 (§4.2) |

`git blame` therefore attributes 100% of every central module to "Rafael"
(`docs/authorship-evidence/git-blame-summary-v4.0.txt`), and **that attribution says nothing about
whether a line was typed by a person or generated by a model.** No commit carries a
`Co-authored-by: Claude` trailer; 100 of the 603 carry a `Claude-Session:` URL trailer, from six
sessions. The other 503 were made by GSD executor sub-agents, which do not add the trailer. The
merge commits `chore: merge executor worktree (21-01)` … `(21-11)` (2026-08-23/24) show those agents
working in isolated worktrees.

The layer attribution below is therefore built from the process artifacts, not from blame.

### 3.2 The process that produced the code

For every plan in Phases 20–25 the same chain is visible in `.planning/phases/`:

1. **Discussion** (human + AI, interactive): `NN-CONTEXT.md` and `NN-DISCUSSION-LOG.md`. Decisions are the author's; the AI measures premises and drafts the record (§2).
2. **Research** (AI agent): `NN-RESEARCH.md`.
3. **Planning** (AI agent, `gsd-planner`) and **plan checking** (AI agent): `NN-XX-PLAN.md`; `STATE.md` records plan-check iterations (e.g. Phase 25: "4B+7W → 1B+7W → 1B+1W").
4. **Execution** (AI agent, `gsd-executor`, one per plan, `parallelization: false` in `.planning/config.json`): the code, tests and `NN-XX-SUMMARY.md`; commits made by the agent.
5. **Verification** (AI agent, `gsd-verifier`): `NN-VERIFICATION.md`; **code review** (AI agent): `NN-REVIEW.md`; **security** (AI agent): `NN-SECURITY.md`.
6. **Human UAT** (author): `NN-HUMAN-UAT.md`: rulings on what the verifier could not decide (Phase 21: 4 items; Phase 23: 2; Phase 24: 4).
7. **Blocking checkpoints** inside plans (author): six plans carry a `checkpoint:` task: `20-07`, `21-11`, `23-13` (the K selection), `25-14` (operator acts), `25-17`, `25-20`.

### 3.3 Module map with authorship by layer

Line counts are `git blame` totals at HEAD; first-add commits from `git log --diff-filter=A`.

| Module | First add | Lines | Architecture / decision | Code generation | Human review or correction on record |
|---|---|---|---|---|---|
| `scripts/mitigation_gate.py` (frozen pin) | `95b3c8a` 2026-08-20 | 1,431 | Author: D-01…D-27 (§2.1) | AI (plans 20-01…20-12) | Two gap-closure waves; pin byte-identical (`20-VERIFICATION.md`); `20-07` blocking checkpoint |
| `scripts/mitigation_unit.py` (frozen) | `8d3beb4` 2026-08-23 | 252 | Author (n=64, δ, unit) | AI | UAT WR-04: author ordered the `privacy_n` continuation (`21-HUMAN-UAT.md` item 2, `9a407d6`) |
| `scripts/phase21_filler.py` | `fe9cabe` 2026-08-23 | 443 | Author (D-13…D-17) | AI | UAT WR-06: author ordered `assert` → `SystemExit` (`c552244`) |
| `scripts/phase21_unit_record.py` | `280e2c1` 2026-08-23 | 1,483 | Author/AI mixed (UNIT-03 measurement path, D-26) | AI | Code review CR-02 → `scripts/phase21_emit.py` |
| `src/personacore/privacy/dpsgd.py` | `a786cb8` 2026-08-25 | 647 | Author (D-01…D-05, D-07) | AI | Battery of four positive controls watched failing first (`22-VALIDATION.md`) |
| `src/personacore/privacy/accountant.py` | `3321421` 2026-08-25 | 1,080 | Author (D-10, D-12, D-13) | AI | Reopened twice by the verifier (`22-VERIFICATION.md`), 8 gap plans, 12 commits |
| `scripts/mitigation_accountant.py` (frozen) | `36ce7fb` 2026-08-25 | 493 | Author (D-09, D-11) | AI | byte-unchanged across all gap plans |
| `scripts/phase23_prereg.py` (edit-once) | `c7de5d4` 2026-08-26 | 456 | Author (D-03…D-06) | AI | 1 commit only; byte-identical at the HALT (`sigma-zero-beats-control.md`) |
| `scripts/phase23_run.py` | `5303819` 2026-08-27 | 5,079 | Author (venue, seeds, halt) | AI | 15 commits; human unblock `746ecf6` read by the driver at launch (`results/phase23_cost_run.log:3`) |
| `scripts/mitigation_budget.py` | `dc2147f` 2026-08-27 | 1,016 | **Author (K, points, verbatim reply)**; AI (σ/ε literals, `CLIP_NORM`) | AI | Append-only, 5 commits |
| `scripts/phase24_adversarial.py` | `628dc21` 2026-08-30 | 421 | Author (D-01…D-13) | AI | Three review criticals reproduced and fixed (`24-08`); provenance pins re-guarded on UAT item 4 (`24-09`) |
| `scripts/phase24_record.py` | `5aed70f` 2026-08-30 | 503 | Author (ADVT-03) | AI | none on record |
| `scripts/phase25_prereg.py` | `7664879` 2026-08-31 | not counted | Author (D-07, D-10, D-11) | AI | none on record |
| `scripts/phase25_run.py` | wave 3, 2026-08-31 | not counted | Author (D-08…D-16) | AI | `tp.device()` defect found during calibration, fixed `6df1eba` (§5.3) |
| `scripts/teach_persona.py` (v2.0 module, extended) | pre-v4.0 | not counted | Author | AI | 17 commits in the window; frozen by Phase 25 |

`[SEM EVIDÊNCIA — confirmar com Rafael]`: whether any line in these modules was typed by hand
rather than produced by an agent under a plan. No artifact distinguishes the two. The default
reading of the record is that the code was generated by the AI and the author's hands are on the
decisions, the checkpoints, the UAT rulings and the operator acts.

---

## 4. Use of AI tools

### 4.1 Declaration

| Tool | Evidence | Used for | Not used for |
|---|---|---|---|
| **Claude Code** (Anthropic CLI), models `claude-opus-5` (11,427 message records) and `claude-fable-5-1` (≈1,100; the count grows with this session) in the project's transcripts | 59 session transcripts under `~/.claude/projects/-Users-juliorcoelho-PersonaCore/` (dated 2026-08-02 → 2026-09-03; 42 within the v4.0 window); `Claude-Session:` trailers on 100 commits; `CLAUDE.md:17` ("Claude Code as the development environment") | Research, planning, code, tests, summaries, verification reports, code review, commit messages, `.planning/` tracking, the Obsidian vault notes (§4.3), and this document | Making the locked decisions (§2); answering blocking checkpoints; `sudo`/`launchctl` operator acts; merging PRs |
| **GSD (get-shit-done) workflow** running inside Claude Code: `gsd-planner`, `gsd-plan-checker`, `gsd-executor`, `gsd-verifier`, `gsd-code-reviewer`, `gsd-security-auditor` sub-agents | `.planning/config.json` (`research: true`, `plan_check: true`, `verifier: true`, `code_review: true`); executor-worktree merge commits; `CLAUDE.md` "GSD Workflow Enforcement" | The chain in §3.2 | nothing outside that chain |
| **Cursor Agent** | 7 commits 2026-09-01 (PRs #1 `cursor/ci-pytest-green-8cc3`, #2 `cursor/one-click-demo-artifact-766b`) | CI green on ubuntu-latest "without hiding the 9 failures"; `make demo`; `LICENSE`; `pyproject` license; `CITATION.cff` | Any scientific code or planning artifact in Phases 20–25 |
| **Codex** (OpenAI) | `AGENTS.md:17` names "Codex as the development environment", but that file is GSD-generated (`fc7651f`, 2026-08-13) by string-substituting "Claude" → "Codex" in `CLAUDE.md` (it still reads `.Codex/skills/` and `generate-Codex-profile`, `AGENTS.md:187,209`). `~/.codex/sessions` holds 70 rollouts with `cwd` = the PersonaCore checkout in the v4.0 window, **all 70 of which are Codex Desktop imports of Claude Code transcripts**: `originator: "Codex Desktop"`, `[external_agent_tool_call: Bash]` markers, zero native `function_call`/`reasoning` records, and whole conversations stamped within milliseconds (`docs/authorship-evidence/session-evidence.txt`) | Nothing in v4.0 that an artifact shows | Any v4.0 code, plan, or decision (no commit or planning file mentions Codex; `git log --grep=codex -i v3.0..HEAD` is empty) |
| **gstack skills** (`/ship`, `/land-and-deploy`, `/document-release`, `/review`, …) | `~/.gstack/analytics/skill-usage.jsonl` (52 entries, machine-wide, not project-scoped) | Release and documentation workflow; not separable per project from the log | scientific code or planning |

No README, `docs/REPORT.md`, `CITATION.cff` or `LICENSE` text in the repository discloses AI
assistance; `grep -n 'Claude\|Codex\|Cursor' README.md docs/REPORT.md` returns nothing. This document
is the first such disclosure in the repository.

### 4.2 What the record shows the human doing, and what it shows the AI doing

**Human (author), from artifacts:**
- States a position before options are shown, names the premise to verify (every discussion log).
- Overrides the AI's recommendation when it disagrees (Phase 25 Q2, §2.6), and re-opens areas at will (Phase 22: three areas declined at the opening gate were re-opened later in the same session "at the user's request", `22-DISCUSSION-LOG.md:13-15`).
- Answers the blocking checkpoints; the K choice is stored verbatim in source (`mitigation_budget.py:443-450`).
- Rules on UAT items with quoted reasons (`23-HUMAN-UAT.md`: *"Sem razão pra tratar uma alegação falsa diferente da outra só porque foi descoberta depois"*).
- Performs the operator acts the code refuses to (`results/phase25_operational_note.md` §11; `25-14-PLAN.md:80`).
- Merges PRs on GitHub (`467bccd`, `3dd5cdb`, `7837ea7`).

**AI, from artifacts:**
- Measures premises live during discussion and records corrections against the author's stated reasons (e.g. `21-DISCUSSION-LOG.md` "Premise check 3 — the stated reasoning was not the load-bearing one"; `22-DISCUSSION-LOG.md` "measured false in the letter and true in the spirit").
- Writes all plans, code, tests, summaries, verification and review documents.
- Makes the decisions listed under *Claude's Discretion* in each `CONTEXT.md` (§2).
- Produced errors that the process later caught: at least 12 "false plan-time figures" in Phase 25 (`STATE.md` frontmatter); the `phase25_run._draw_one_shape` call to a non-existent `tp.device()` hidden behind `--dry-run` tests (fixed `6df1eba`); a heartbeat design that would have false-fired on all 22 n=64 legs (`25-10`); repeated corruption of `STATE.md` by the `gsd-sdk` state handlers, hand-repaired ("sixth case", `STATE.md`).

### 4.3 A caution about the Obsidian vault as evidence

`CLAUDE.md` instructs Claude Code to write a dated entry into the vault note
`01-Projects/PersonaCore — memória em pesos.md` after every durable change. That note (335 lines,
created 2026-08-25) is therefore **AI-authored, in the author's first person** ("`CURVE_K=16` …
travados por mim em checkpoint"; "Verificação de magnitude que exigi antes de aceitar precedente").
It is a useful index but not independent testimony; this document cites it only where the same fact
is also in a repository artifact, and marks the one attribution that exists only there (§2.6, Area 7).

### 4.4 Case study: the `_prev`-as-`set` bug in tensorforge

**Context.** tensorforge (`github.com/RAFAELDCOELHO/tensorforge`) is a from-scratch autograd and
training engine validated by byte-exact parity against a real PersonaCore checkpoint. Its public
history is six commits, all on 2026-07-28, the first (`372dbb8`) containing the whole v1.0 tree;
`~/tensorforge-backup-pre-filter-repo-20260728` shows the history was rewritten with a filter that
day. The commit-level record of the bug is therefore gone; what survives is the README, the tests,
a pre-fix snapshot, and one Claude Code session transcript
(`~/.claude/projects/-Users-juliorcoelho-tensorforge/5f6e3f0a-….jsonl`, 2026-07-28 10:43 → 07-29).

**The defect.** `Tensor._prev` and `Value._prev`, each graph node's children, were Python `set`s.
Iteration order over a set of objects follows `id()`-derived hashes that change between processes,
so the reverse topological sort and the order of `+=` accumulations into `.grad` changed run to run;
floating-point addition is not associative, and identical runs differed by about one ulp per
parameter (`README.md:97-120`; `tests/test_engine.py:92-115`).

**How it was detected (transcript, local timestamps):**
- 13:44:53, **author**: specifies `train_step` and demands, as test (1), *"compara resultado byte a byte contra a saída de train_step (mesmo padrão usado em Linear/LayerNorm/Block/GPT: shape sozinho não distingue ordem errada de certa)"*. The byte-exact discipline is the author's standing rule in this project (every prior milestone's tests use `array_equal`, per the same transcript).
- 13:50:01, **AI**: test (1) fails with 1-ulp deltas. *"Antes de mexer em qualquer coisa, testo a hipótese."*
- 13:50:17, **AI**: *"duas execuções da mesma rota já divergem (5.4e-16), e a ordem topológica muda entre execuções. Causa: `_prev` é um `set`…"*. Diagnosis by running the same route twice on identical models, then printing the topological order across two runs.
- 13:50:24–13:51:03, **AI**: `set` → `tuple` in `core/tensor.py`, a determinism regression test, mutation check; reports at 13:53:52 with the mechanism and why it matters for PersonaCore's bit-identical resume contract.
- 13:56:09, **author**: *"bug de determinismo encontrado e corrigido no motor"*; orders the same fix in `core/engine.py` (`Value`) as a hygiene change, an end-to-end demonstration, and that the README record the bug *"porque é o tipo de coisa que alguém lendo o repo depois vai querer saber que aconteceu e como foi pego."*

**Why hundreds of tests had not caught it.** The README states it: a ~1e-16 divergence sits below
any `rtol`, so every `allclose` assertion passed; only the exact-equality test the author required
could fail. The `set` itself came from the micrograd-style scalar engine the tensor engine was
modelled on (`core/engine.py:4`, session's first read at 10:43 shows `self._prev = set(_children)`).

**Attribution.** The *detection mechanism* (exact equality as an acceptance
criterion) was the author's. The *diagnosis and fix* were executed by the AI inside the session,
after the author's test specification made the failure visible. The *decision to propagate the fix
and to publish the finding* was the author's. The prompt that commissioned this document framed the
question as "why the AI did not catch it alone, who diagnosed it"; the transcript supports the first
half (no AI-written tolerance test caught it) and answers the second half in the AI's favour on the
mechanics of the diagnosis.

`[SEM EVIDÊNCIA — confirmar com Rafael]`: who wrote the original `core/engine.py` with
`_prev = set(...)` (a snapshot with that line exists at `~/Downloads/tensorforge/core/engine.py`,
mtime 2026-07-28 07:33, three hours before the surviving session starts, and carries no git history).

---

## 5. Verification methods

### 5.1 The test suite and CI

| Check | Evidence |
|---|---|
| 2,020 tests collected at HEAD | `pytest --collect-only -q`, run 2026-09-03 for this document |
| Full suite `2013 passed, 1 skipped` in 21 min on the M3 | `README.md:402-411` (recorded 2026-09-02) |
| Suite growth across v4.0: 877 (Phase 20 close) → 1,024 (21) → 1,338 (22) → 1,589 (23) → 1,647 (24) → 2,000 (25-14) | `20-VERIFICATION.md`; `21-HUMAN-UAT.md`; `22-VERIFICATION.md`; `REQUIREMENTS.md` CTRL-03 row; `24-09` entry in `STATE.md`; `STATE.md` W7 |
| CI: two jobs on every push and weekly (`test` on ubuntu-latest with a CPU-only wheel; `demo-asset` downloading the real release and checking its sha256) | `.github/workflows/ci.yml`; `gh run list` 2026-09-03: 17 of the last 20 runs `success`, 3 `failure` on 2026-09-02 (`4d2dcb7`, `0e88733`, `3301a30`), fixed at `37b75ea` the same day |
| Lint: `ruff check . && ruff format --check .` | `Makefile:30`; CI |

### 5.2 Pre-registration ancestry guards

`tests/test_phase16_prereg.py` (v3.0) and `tests/test_phase20_prereg.py` (v4.0) assert commit
ancestry between each frozen pin and every result artifact it judges; CI checks
`git rev-parse --is-shallow-repository == false` so the guard cannot pass blind
(`ci.yml:14-27`). The RED state of the guard was proven in a throwaway repository committed as a test
fixture (Phase 20 D-22; `20-DISCUSSION-LOG.md` "Gate module structure").

### 5.3 Watched RED, mutation checks, and independent re-derivation

The recurring discipline in the summaries is: a guard is not trusted until it has been watched failing.
Examples with artifacts:
- Phase 22's four positive controls (wrong sensitivity, RNG reuse, clip-the-average, noise-after-average) each watched failing first (`22-VALIDATION.md`, `tests/test_phase22_fakes.py`), then re-watched on MPS in Phase 23 (`23-CONTEXT.md` D-02).
- The two-oracle accountant check was **falsified twice** by the verifier (`22-VERIFICATION.md`: `gaps_found` 4/5, then again in the `erfc`-subnormal band) and closed by 22-12…22-19 with the gap at the frozen δ reduced from 1.9190e-03 to 1.0152e-11 inside an unwidened 1e-9 budget.
- Phase 24's three review criticals were each reproduced by hand before fixing, RED → GREEN → mutated-RED (`24-08` entry, `STATE.md`; commits `d4ed1f8`, `ba2787f`, `e518a4e`).
- Phase 25 calibration found the driver's live draw loop dead behind `--dry-run` tests (`6df1eba`); the residual risk "no test reaches the live loop" is recorded in `25-*/deferred-items.md`, not hidden.
- Every committed record re-derives under exact `==` from its inputs in a test (e.g. `tests/test_phase23_budget.py`, with a watched perturbation control).

### 5.4 A negative result accepted without loosening the threshold

On 2026-08-27 03:52 the first executed DP run (σ=0, `dp_n8`) read 790/1008 taught recall against a
control of 566/1008, 4.15× the seed floor and in the direction of beating the control, and the
blind rule raised `SystemExit` (`.planning/debug/sigma-zero-beats-control.md`;
`results/phase23_sigma_zero.json`). What followed, in order:

1. The rule was verified byte-identical to its birth commit `c7de5d4` and re-derived from raw counts (Task 1 of the debug record: "every figure reproduces").
2. The four residual differences 23-08 had enumerated **in advance** were measured. Three training-protocol differences (teaching-loss weight 1.0 vs 0.4342, 8.125× lot volume, `grad_clip` on one side only) explained the gap; the DP arithmetic was excluded by a 72/72-tensor probe agreeing to 2.178e-07.
3. A protocol-matched comparator was built as its own wave (23-15…23-20); the **unedited** rule returned `proceed` with deviation exactly 0.0 on a floor **half** the original (0.0536 → 0.0268; `results/phase23_matched_verdict.json`).
4. The false claims this exposed were retracted **in place, dated, originals left standing**: the roadmap's "~1,010×" cost ratio (`23-12`, `ROADMAP.md` continuation block), the DPSGD-06 row (`23-UAT1`, `7296b31`), and the "~17 s per arm" figure.

The threshold moved in the stricter direction only. The same pattern recurs elsewhere: the
never-taught extraction floor came out exactly 0.0, and rather than being read as a bug it was
proven honest by a positive control and its consequence recorded as *stricter* (X reduces to
`wilson_upper(0, 416)`; `REQUIREMENTS.md` CTRL-03 row; `23-HUMAN-UAT.md` item 2).

### 5.5 Review layers

Per phase: `NN-REVIEW.md` (AI code review), `NN-SECURITY.md` (threat model; Phase 20 at
`threats_open: 0`), `NN-VALIDATION.md` (Nyquist gap audit), `NN-VERIFICATION.md` (goal-backward),
and, where the verifier returned `human_needed`, `NN-HUMAN-UAT.md` with the author's rulings.

---

## 6. Reconstructibility

### 6.1 Environment as recorded

| Item | Value | Source |
|---|---|---|
| Machine | Apple M3 Pro, 36 GB unified memory | `sysctl` on the author's machine, 2026-09-03; `results/phase20_retention_floor.json` `device: mps` |
| OS | macOS 26.5.1 (build 25F80) at this writing; `results/phase25_operational_note.md` §6b lists 26.6.2 as a deliberately uninstalled pending update | `sw_vers` |
| Python | 3.11.15 in `.venv` (`requires-python = ">=3.10,<3.12"`) | `pyproject.toml:10` |
| PyTorch / NumPy | 2.7.1 / 2.4.6, MPS available; `torch==2.7.*` pinned in the `cpu` extra | `pyproject.toml:17`; `.venv` |
| Seeds | `SEED_LADDER = (1337, 2024, 1338, 2025, 1339)` | `scripts/phase23_run.py:146` |
| Provenance in every record | `git_sha`, module and corpus `sha256`, refuse-if-dirty at emit time | e.g. `results/phase23_cost.json`, `results/phase24_token_budget.json` (`24-09`) |

### 6.2 What a clean machine can and cannot regenerate

`checkpoints/` and `data/` are gitignored (`.gitignore:14,17`). The public release
`m1-demo-v1` ships only `model_slim.pt` (the v1.0 story model, sha256-pinned in
`scripts/fetch_demo_checkpoint.py`). The conversational base `convbase_best.pt`, the v3.0 persona
adapters, the encoded corpora and every v4.0 adapter exist only on the author's disk. Consequently:

- **CPU-only, regenerable from a clean clone:** the whole test suite (2,020 tests, ~21 min), all pre-registration guards, the accountant and its oracles, Phase 22's DP battery, the Phase 21 corpus geometry records (`scripts/phase21_emit.py`, refuses a dirty tree), the Phase 24 token-budget record (`scripts/phase24_record.py`, 2.22 s per `24-07`).
- **Requires the gitignored checkpoints and corpora:** every MPS run in Phases 20, 23 and 25.

`[SEM EVIDÊNCIA — confirmar com Rafael]`: whether `convbase_best.pt`, the Phase-19 adapters and the
encoded bins are archived anywhere a committee could obtain them, or whether the intended
reproduction path is to retrain v1.0/v2.0 from the committed scripts first (the v1.0 pretrain is
50,000 steps on the same M3; `results/run.csv`).

### 6.3 Commands, per phase

```bash
git clone https://github.com/RAFAELDCOELHO/PersonaCore.git && cd PersonaCore
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[cpu,dev,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
make lint && make test                       # ~21 min on the M3; CPU-only, no checkpoints needed
```

| Phase | Command(s) | Hardware | Recorded wall clock | Output |
|---|---|---|---|---|
| 20 | `python scripts/phase20_run.py` | MPS; needs `checkpoints/phase19_erase_dialogue_floor_seed{1337,2024}` | "roughly an hour" (module docstring) | `results/phase20_retention_floor.json` |
| 21 | `.venv/bin/python scripts/phase21_emit.py` | CPU | seconds | `results/phase21_privacy_unit.json`, `results/phase21_multiplicity.json` |
| 22 | `pytest tests/test_phase22_*.py` | CPU | minutes | no scored artifact by design (D-08) |
| 23 | `python scripts/phase23_run.py cost` → `schedule` → `floor` → `sigma-zero` → (after the human unblock) the matched-control, CAL-03 and never-taught sub-modes (full table printed by `phase23_run.py:5001`) | MPS | control 161.1 s/arm ×5; DP σ=0 205.4 s; `dp_n64` 1383.3 s; never-taught scoring 10.14 h (`results/phase23_cost.json`; CTRL-03 row) | `results/phase23_*.json`, run logs |
| 24 | `python scripts/phase24_record.py` | CPU | 2.2 s | `results/phase24_token_budget.json` |
| 25 (calibration, done) | `scripts/phase25_calibrate.py`, `phase25_probe2.py`, `phase25_sigma_hi.py` | MPS | 2026-09-01 01:02 → 05:19 (file mtimes) | `results/phase25_{clip_calibration,adversarial_throughput,sigma_hi_probe,probe2_tensors}.json` |
| 25 (sweep, not started) | `sudo pmset -a sleep 0 disksleep 0 powernap 0`; `launchctl bootstrap gui/$UID artifacts/com.personacore.phase25.{sweep,watch}.plist`; driver `scripts/phase25_run.py` | MPS, unattended | projected 87.86–149.45 h (`results/phase25_adversarial_throughput.json` `schedule.total_hours_*`) | `results/phase25_frontier.json` (does not exist yet) |

---

## 7. Execution chronology

All dates local (UTC−3). Sources: `docs/authorship-evidence/commit-trailer-census-v4.0.txt`
(commits per day), `docs/authorship-evidence/plan-ledger-v4.0.txt`, `results/` file times, run logs.

| Date | Event | Evidence |
|---|---|---|
| 2026-08-20 | v3.0 archived; v4.0 milestone opened; research pass corrects the scope (three-condition gate, measured DP cost, privacy unit). Phase 20 discussion; gate pinned 16:27 (`95b3c8a`). 52 commits. | `4f0423b`, `29a86e5`, `c673b4c`; `20-DISCUSSION-LOG.md` |
| 2026-08-21 | Phase 20 completes, reopens for GATE-06, re-verified 7/7. First MPS run of the milestone: retention floor (two seeds, no retraining). 52 commits. | `20-VERIFICATION.md`; `results/phase20_retention_floor.json` |
| 2026-08-22 | Phase 21 discussion, three sessions (session 1 unlogged). 12 commits. | `21-CONTEXT.md` header |
| 2026-08-23/24 | Phase 21 executed by 11 executor agents in worktrees, merged 17:11 → 16:50 next day; gap closure; verified 6/6. UAT 22:20 → 03:00. | merge commits; `21-VERIFICATION.md`; `21-HUMAN-UAT.md` |
| 2026-08-25/26 | Phase 22: 19 plans (11 + 8 gap plans), all CPU; verifier returns `gaps_found` twice before `passed` 5/5. 80 commits on 08-26, the busiest day. | `22-VERIFICATION.md`; plan ledger |
| 2026-08-26 | Phase 23 blind rules committed 20:31 (`c7de5d4`); CAL-03 wiring record 21:21. | `results/phase23_cal03_wiring.json` |
| 2026-08-27 00:17 → 00:50 | Control arms ×5 and never-taught arms ×5 trained. | `results/phase23_control_seed*/`, `phase23_never_taught_seed*/` |
| 2026-08-27 03:33 → 03:52 | **σ=0 run → HALT** (`SystemExit`). Debug session opens; root cause attributed same day. | `results/phase23_sigma_zero.json`; `.planning/debug/sigma-zero-beats-control.md` |
| 2026-08-27 13:14 → 19:59 | Matched control, 5 seeds; one run **killed and continued** through the resume path; matched verdict `proceed`. | `results/phase23_resume_run.log:2` ("CONTINUATION of a killed run ADMITTED"); `phase23_matched_verdict.json` |
| 2026-08-28 10:32 | **Human unblock** of 23-11…23-14 (`746ecf6`); the driver reads and prints this commit at every later launch. | `results/phase23_cost_run.log:3` |
| 2026-08-28 14:36 → 15:28 | First noised point (`dp_n64`, σ=0.5) and the cost record; the roadmap's cost claim retracted in place. K = 16 selected by the author 17:18. | `results/phase23_cost.json`; `0a23aca` |
| 2026-08-28 → 08-29 07:05 | Never-taught scoring, 69,120 draws, 10.14 h. **First launch drew all 13,824 completions of seed 1337 and crashed** serialising a `torch.Tensor` into the state file; traceback kept in the committed log, relaunched with per-shape persistence. | `results/phase23_never_taught_run.log:53-87`; CTRL-03 row |
| 2026-08-29 | Phase 23 UAT ruled and closed; Phase 24 discussion session 1. | `23-HUMAN-UAT.md` |
| 2026-08-30 | Phase 24 discussion session 2, 9 plans executed, review criticals fixed, verified `passed`. **No adversarial adapter trained** (ADVT-01 deliberately open). 50 commits. | `24-VERIFICATION.md`; `24-HUMAN-UAT.md` |
| 2026-08-31 | Phase 25 discussion (44 decisions, then Area 7 reopening to 51); 22 plans, 3 plan-check iterations; waves 1–3 executed. 70 commits. | `25-CONTEXT.md`; `STATE.md` |
| 2026-09-01 00:04 → 05:19 | Waves 4–6: clip-norm calibration (14,400 per-record norms), adversarial throughput probes, σ_hi anchor (total collapse at σ=80: 0/1008), PROBE 2 at both capacities. `tp.device()` defect found and fixed 00:39. | `results/phase25_*.json`; `6df1eba` |
| 2026-09-01 06:21 → 14:32 | 25-14: LaunchAgents, venue module, operational note; **blocked at the human gate** (needs `sudo pmset` and `launchctl bootstrap`). Rehearsal agent run (39 heartbeats, 15:10 → 16:24 UTC); a logout showed `gui/<uid>` agents do not survive it (`b05367a`). | `results/phase25_operational_note.md`; `data/phase25_heartbeat.jsonl` |
| 2026-09-01 (evening) | Cursor Agent PRs #1 and #2 merged (CI green on ubuntu, `make demo`, LICENSE, CITATION). | `467bccd`, `3dd5cdb` |
| 2026-09-02 | `make demo` sha256 pin, interpreter selection fix (PR #4), README status note and presentation; three red CI runs fixed the same day. 22 commits. | `4d2dcb7`, `7837ea7`, `322ebd7`; `gh run list` |

**Phase 25 state at this writing (2026-09-03 15:45), marked "in execution":**
- 15 of 22 plans complete (`25-01…25-13`, `25-21`, `25-22`); `25-14` at the human gate with its buildable half committed; `25-15…25-20` not started (`docs/authorship-evidence/plan-ledger-v4.0.txt`).
- Zero sweep point records; `results/phase25_frontier.json` does not exist; `ADVT-01` still unticked.
- The three LaunchAgents are bootstrapped; the sweep job reads `runs = 0`, `last exit code = (never exited)`; the watcher job is live and has appended 3,019 stall records to `data/phase25_stall.jsonl` (all `action_taken: "none"` by design, D-16).
- `pmset -g` now reads `sleep 0 / disksleep 0 / powernap 0`. Every committed reading (four, the last at `4decedc`) is `1 / 10 / 1`, and the operational note's after-state block is marked **PENDING**. `[SEM EVIDÊNCIA — confirmar com Rafael]`: when the `sudo pmset` change was applied and by whom; no commit records it.
- One unattributed earlier failure: `25-CONTEXT.md:20` states the machine's "last production run was killed externally at 60 minutes". `[SEM EVIDÊNCIA — confirmar com Rafael]`: which run, and what killed it.

No Phase 25 result is reported here, because none exists.

---

## 8. Consolidated list of claims without an artifact

Each item is also marked inline where it arises. All ten were still open when version 1.0 was
committed. Answers go below this list as dated additions; nothing is filled in by inference.

1. §3.3: Whether any code line in Phases 20–25 was typed by hand rather than generated by an agent under a plan. Default reading of the record: none.
2. §4.1: Whether Codex was ever used on PersonaCore in a way that left no artifact (the record shows only imported Claude transcripts; `AGENTS.md` is a generated mirror). One genuine Codex session on 2026-08-31 (`cwd` under `~/Documents/Codex/…`, a `guardian` sub-agent) mentions "updating the paper" in relation to the repository; confirm whether a paper about PersonaCore exists outside this repository and what tool wrote it.
3. §4.4: Who wrote the original tensorforge `core/engine.py` with `_prev = set(...)` (pre-session snapshot exists, no history).
4. §4.4: Whether the author accepts the transcript's attribution: detection mechanism human, diagnosis and fix AI, publication decision human.
5. §6.2: Where the gitignored checkpoints and corpora (`convbase_best.pt`, Phase-19 adapters, encoded bins, v4.0 adapters) are archived, or whether the reproduction path is "retrain v1.0/v2.0 first".
6. §7: When and by whom `sudo pmset -a sleep 0 disksleep 0 powernap 0` was applied (currently in effect, not recorded).
7. §7: Which run was "killed externally at 60 minutes" and by what.
8. §2.2: Phase 21 session 1 (privacy unit, ragged geometry, D-01…D-11) has no discussion log; confirm those decisions were the author's ratification of the research fork rather than adopted by default.
9. §2.6 / §4.3: The magnitude check that preceded the condition-(c) reopening is attributed to the author only in the AI-written vault note; confirm.
10. General: Age (16) and school context appear nowhere in the repository; this document does not assert them.

---

## 9. The author's answers (recorded 2026-09-03)

Answers were given in writing, in Portuguese, on 2026-09-03 (this session's transcript,
`~/.claude/projects/-Users-juliorcoelho-PersonaCore/22fb8cc0-….jsonl`). Each is recorded as the
author's statement, then checked against artifacts; where the check disagrees with the statement,
the disagreement is stated. Nothing in §1–§8 was edited.

**1. Hand-typed code.** Author: no line was typed by hand; the architecture and the important
decisions were the author's, and the AI wrote the code under that direction. Consistent with §3.3's
default reading; no artifact contradicts it.

**2. Codex.** Author: Codex wrote only a paper about the project and took no part in PersonaCore's
architecture or code. Consistent with §4.1 (the 70 PersonaCore-cwd rollouts are imports, and the
one genuine Codex session mentioning the repository, 2026-08-31, works on "the paper" under
`~/Documents/Codex/`). The paper itself is outside this repository and is not described here.

**3. The original tensorforge `engine.py`.** Author: does not know, and asked that the answer come
from git rather than memory. `git log --follow --format='%h %an %ad %s' -- core/engine.py` in
`~/tensorforge` returns one commit for the file's first add: `372dbb8 Rafael 2026-07-28 11:06:16
-0300 v1.0: framework de deep learning do zero, paridade bit-exata com PersonaCore`. The identity is
the author's; the file already contained `_prev = set(...)` when the only surviving session read it
at 10:43 that day, so whether an agent or the author produced those lines is not recoverable from
any artifact. Recorded as unknown.

**4. The tensorforge attribution in §4.4.** Author: accepts it (detection mechanism human, diagnosis
and fix AI, publication decision human).

**5. Where the gitignored inputs are.** Author asked for the answer to come from the disk. Measured
2026-09-03: everything exists on the author's machine and nowhere else that any artifact names:
`checkpoints/convbase_best.pt` (278,026,567 B, 2026-08-01), `checkpoints/best.pt` (166,808,536 B,
2026-06-05), 35 adapter files including `phase19_erase_dialogue_floor_seed{1337,2024}_adapter.pt`
and `phase23_control_seed*_adapter.pt`, and 44 `.bin` corpora under `data/`; `checkpoints/` is
7.8 GB and `data/` 4.8 GB. No archive, release or external copy is referenced anywhere in the
repository. For a clean machine the reproduction path is therefore to retrain, and every step is
scripted; the recorded wall-clock on the same M3 is:

| Step | Script | Recorded time | Source |
|---|---|---|---|
| TinyStories download + BPE + encode | `scripts/train_tokenizer.py`, `scripts/encode_corpus.py` | not recorded as a figure (network: 2.23 GB) | `CLAUDE.md` data tooling |
| v1.0 pretrain, 50,000 steps → `best.pt` | `scripts/pretrain_tinystories.py` | ~5 h elapsed, including the calibration gate | `.planning/milestones/v1.0-phases/05-tinystories-pretraining/05-02-SUMMARY.md:51,61` |
| PersonaChat fetch + dialogue bins | `scripts/fetch_personachat.py`, `scripts/prepare_dialog_corpus.py` | not recorded as a figure | Phase 11 |
| v2.0 conversational base, 4,000 steps → `convbase_best.pt` | `scripts/finetune_dialog.py` | 37.3 min wall | `.planning/milestones/v2.0-phases/12-stage-2-conversational-fine-tune/12-05-SUMMARY.md:61` |
| v3.0 persona and Phase-19 adapters | `scripts/teach_persona.py`, `scripts/phase19_run.py` | ~38 min per 4,000-step arm | `.planning/PROJECT.md` ("v2.0 precedent") |
| v4.0 arms | `scripts/phase23_run.py`, `scripts/phase25_run.py` | 161 s (non-DP), 205 s (`dp_n8`), 1383 s (`dp_n64`) per arm | `results/phase23_cost.json` |

**6. Who applied `sudo pmset`, and when.** Author: himself, around 1–2 September 2026, at step 3 of
the twelve-step launch sequence, because Claude Code cannot run an interactive `sudo`; the prior
reading `1/10/1` matched `PMSET_REVERT_TARGETS`. Verified in the session transcript `579afcbf`
(started 2026-08-31 13:50 local): the author's instruction, relayed into the session at 2026-09-01 10:38 local, is
to run the change and its read-back; the tool result at 10:43:59 local reads `=== STEP 3
read-back — must be 0 / 0 / 0 === powernap 0 / disksleep 0 / sleep 0`. `PMSET_REVERT_TARGETS` was
committed at `277109f` (2026-08-31, plan 25-06). One correction to the record rather than to the
author: the operational note's §11 still lists the after-state as PENDING, and `STATE.md`'s 25-14
entry says "pmset still 1/10/1"; both were written before or without that read-back and were not
updated afterwards. Applied: 2026-09-01, ~10:43 local, by the author, through the session.

**7. The run "killed externally at 60 minutes".** Author: the first ladder run of Phase 16, cause
never resolved, five hypotheses falsified, a sleep explanation asserted and retracted; the honest
answer is "a mystery recorded as such". The artifacts split this into two events, and the author's
answer names the wrong one for the sentence in `25-CONTEXT.md:20`:

- The Phase 16 event is real and is recorded in `16-07-SUMMARY.md` (not 16-11): run 1 died at rung 5
  after **50.3 min**, "Cause NOT identified", with five falsified hypotheses (jetsam/OOM, Python
  crash, in-run leak, the 10-minute Bash timeout, macOS sleep, the last falsified by a 25 h
  `NoIdleSleepAssertion`), an intermediate sleep attribution retracted, and "the harness task
  lifecycle" named as the most consistent remaining explanation with no log to prove it.
- The sentence in `25-CONTEXT.md:20` ("the machine's last production run was killed externally at
  60 minutes") refers to the Phase 23 matched-control run of 2026-08-27: `23-17-SUMMARY.md:154-160`
  records a 3,603 s window, "killed at ~60 min by the execution harness", three of five seeds done,
  resumed later through the per-seed state file (`results/phase23_resume_run.log`). Its cause is
  recorded, not open. The author's aside that 23-17 was "killed by the 600 s ceiling" does not match
  that summary either; the Bash tool's 600 s limit is the hypothesis 16-07 falsified.

**8. Phase 21 session 1.** Author: ratification, not default; the fact-level privacy unit came from
the v4.0 scoping decision; the ragged geometry with mean-over-windows was the author's position
stated before the options, kept after the system's measurements replaced its justification; an
option to equalise the window count across the corpus was rejected because it would fix only the 56
filler facts and leave the 8 `LOCKED_FACTS` exposed. What the artifacts show: `21-CONTEXT.md`
D-01…D-04 record the ragged choice, the measured table (ragged 1.14× vs uniform 1.39×, 10.26% vs
24% padding, `torch.stack` refusing the ragged batch) and the mean-over-windows rule with its named
cost. They do not record the "equalise W across the corpus" option or the reason for rejecting it,
and no 2026-08-22 transcript turn stating that position was found. That part stands as the author's
statement.

**9. The magnitude check before the condition-(c) reopening.** Author: required by him, as a
position stated before the options ("D-02's treatment unless the magnitude argues otherwise; check
before accepting precedent"). Verified: `25-CONTEXT.md` D-48 records that "the magnitude was CHECKED
before the precedent was accepted", with the two results (dialogue floor 1.65% of the band width;
retention: the v3.0 adapter fails the cap by +0.190760, so the floor would need to be 2.38× larger),
and the session transcript `0b235c5e` carries the assistant's message of 2026-08-31 10:45 local
quoting the author's conditional back: "Your conditional was the load-bearing part: 'D-02's
treatment unless the magnitude argues otherwise — needs checking before accepting precedent'".
§2.6's reliance on the vault note for this item is withdrawn; the CONTEXT file and the transcript
carry it.

**10. Age and school context.** Author: must not enter the document. Not added.

