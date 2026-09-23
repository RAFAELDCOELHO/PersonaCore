# Milestones

## v4.0 Leakage Mitigation and Relearning Validation (Shipped: 2026-09-22)

**Phases completed:** 9 phases (20-28), 115 plans, ≈168 tasks (task-heading count; 79 of 115 SUMMARYs carry no `tasks` field)
**Timeline:** 2026-08-20 -> 2026-09-22 (33 days, 819 commits)
**Audit:** `gaps_found` — 44/48 requirements (RELRN-02..05 unsatisfied by ruling — named limitation, owner v5.0), 9/9 phases, 21/21 integration, 6/6 flows, nyquist partial (23, 25 never re-stamped), 17 debt items, no blockers

**Delivered:** v3.0 measured that weight-based memory leaks under black-box attack. v4.0 built the
mitigation, mapped the frontier, and **published the null**: no point on the DP or the adversarial
curve clears the pre-registered three-condition gate — `null-at-both-capacities` — and the reason
is measured, not inferred: DP removed the leakage by removing the memory.

**Key accomplishments:**

- **A three-condition existence gate committed before any number existed** (Phase 20).
  `mitigation_gate.py` judges every sweep point on (a) extraction ≤ X, (b) taught recall ≥ Y on
  BOTH legs against the point's OWN retrained control, and (c) a dialogue-perplexity band and
  retention cap — with the K menu, the promotion rule and the retention floor pinned under ancestry
  guards. Gap-closure wave 20-13..20-17 turned two name-checks into property checks (NaN on the Y
  legs, a magnitude bound on the borrowed floor) and refused the repository's own committed fixture
  in the process (D-41).
- **The privacy unit was defined before the accountant was written** (Phase 21): "one taught fact",
  carried by a measured number of rendered rows, with a fact-aligned sampler whose per-step
  multiplicity is exactly 1 by construction; δ pinned as a literal; the n=64 corpus built with 56
  scored-out filler facts so an out-of-corpus canary population exists at all.
- **DP-SGD from scratch on the LoRA gradients, with its correctness battery** (Phase 22):
  per-example clipping via `vmap(grad(functional_call))` (1.07× at B=8, 1.02× at B=64 over a batched
  step — the ~B× assumption in the kickoff was measured false), Gaussian noise, an (ε, δ)
  accountant (`epsilon_for` / `sigma_for`), and four named silent-non-privacy failure modes each
  turned into a refusal.
- **Cost calibration and the σ=0 diagnostic that halted the sweep** (Phase 23): the σ=0 control
  read 4.15× the noise floor in the direction every correctness bug produces (D-04 fired at 23-10),
  and was resolved at 23-19 by finding that the on-device bitwise check cannot see a subnormal
  flush. Five fresh controls trained at identical budget and seed (CTRL-03).
- **The adversarial arm and the held-out attack family** (Phase 24): Phase 18's attack suite split
  into training-visible and held-out families with the split disclosed, `refusal.by_family` recorded
  per point, and ADVT-01 deliberately left for the sweep to satisfy.
- **The frontier sweep and its verdict** (Phase 25): 44 points over 81.40 h of unattended MPS
  training (plus 15.77 h of recall), assembled write-once into `results/phase25_frontier.json` —
  verdicts **32 FAIL / 6 INCONCLUSIVE / 6 REFUSED / 0 PASS**, the branch `null-at-both-capacities`.
  Every DP point above σ=0 scored taught recall 0/1008 and held-out 0/648; the n=64 control itself
  learned only 87/1008. The adversarial arm trains with no replay, so condition (c) fails it for the
  recipe, not the ratio — disclosed, not adjusted, and handed to a v5.0 candidate.
- **The empirical privacy audit could not accuse** (Phase 26): a 30 h 43 min canary run, 15
  points **CONSISTENT / 0 BROKEN** against each point's own ε at δ = 1e-5, published with the
  finding that the comparison could not have failed at 11 of them (auditor ceiling ε = 2.79),
  `selection_accounted = false` reported rather than omitted.
- **Relearning read MOOT, and the milestone ships that** (Phase 27): the admission gate, called
  once on the measured frontier, found 0 of 44 points admissible (cleared (a) 30 / (b) 4 / (c) 1),
  so the relearning apparatus — built, guarded and proved wired end to end on CPU — never ran on a
  mitigated arm. RELRN-01 satisfied in its MOOT form; RELRN-02..05 are the milestone's named
  limitation, by developer ruling.
- **The report is rendered, not authored** (Phase 28): every number in the v4.0 section of
  `docs/REPORT.md` and both README glance bullets is a binding to a committed record field or module
  constant, rendered by a stdlib renderer whose templates are scanned for hand-typed numerals; the
  standing expectation (σ ≥ 15.3 for ε ≤ 4) is quoted from `c673b4c`, proved to precede every v4.0
  record, and re-derived at render time (`sigma_for(4.0, 200, 1e-5) = 15.289937507119`). A 69-row
  ledger gives every open item across v3.0 and v4.0 one disposition, and the phase closed only on a
  green CI run of the whole milestone's code (`35770563251`) after the first run found three real
  causes — tags never pushed, a legitimate third mention of the correction helper, and a
  host-gated skip nobody had counted.

**Ship decision — the null is the result.** Nothing is withdrawn and nothing is softened: the gate
that was committed before the sweep returned no clearing point, the audit could not accuse the
mechanism, and the relearning validation was never reached. What v4.0 proves is that the
privacy/utility frontier at 331,776 adapter parameters, under this recipe and this unit, has no
point where a formal privacy claim and a usable memory coexist — and that the measurement machinery
to say so was in place before the numbers were.

### Known Gaps and Deferred Items

**Known deferred items at close: 2** (see STATE.md `## Deferred Items`) — the `human_needed`
verdicts of `23-VERIFICATION.md` and `27-VERIFICATION.md`, both discharged by developer rulings
recorded beside them and never re-stamped (D-35; ledger rows `VER-23-HUMAN-NEEDED`,
`VER-27-HUMAN-NEEDED`, ACCEPTED). Acknowledged rather than resolved for the reason v3.0 recorded:
re-stamping a verdict to satisfy a counter erases what the verifier found.

**Known gaps — 4 requirements unticked by ruling:** RELRN-02, RELRN-03, RELRN-04, RELRN-05
(cost-to-recovery curve, its qualification of the verdict, the structural budget/seed enforcement,
the disjoint recovery fixture). The apparatus exists and is tested; the gate that would have
admitted a point to run it read MOOT. Owner: the v5.0 candidate (replay-bearing adversarial re-run
and its own control, WR-05). Also open by design: ADVT-01's frontier form (satisfied only as
0-of-32 / 0-of-6-with-6-refused) and FRONT-04's weaker existential.

**Tech debt carried forward: 17 items** (full list in
`milestones/v4.0-MILESTONE-AUDIT.md`), including the three advisory review findings left after
WR-01/WR-02 were closed at `8a466d8` / `a4971cb`: WR-03 (`_SHA` regex admits decimal run ids —
measured harmless on all nine FIXED rows), WR-04 (one vacuous `isinstance` assert beside two live
docstring asserts), IN-04 (the provenance bytes cell recomputed by the same helper the renderer
uses). The 69-row ledger records 6 RE-DEFERRED and 23 NAMED-LIMITATION items with their owners.

**Not a gap:** the null verdict. The milestone contracted to sweep under a gate committed before
any point ran and to publish whichever way the numbers came out. It did.

---

## v3.0 Adversarial Privacy Audit and Selective Memory Erasure (Shipped: 2026-08-19)

**Phases completed:** 4 phases (16-19), 54 plans, 113 tasks
**Timeline:** 2026-08-12 -> 2026-08-19 (8 days, 350 commits)
**Audit:** `tech_debt` — 29/29 requirements, 4/4 phases, 16/16 integration, 3/3 flows, no blockers

**Delivered:** v2.0 asserted that weight-based memory is private; v3.0 stopped asserting and
**measured** it — and published the measurement that went against the project.

**Key accomplishments:**

- **Weight-vs-prompt persistence, measured with a bound instead of claimed** (Phase 16). Four arms
  on one binding 270-question fixture in four fresh processes, licensed by a capability ladder that
  ran and was committed *before* anything was scored. The adapter arm reached 90/104 questions
  where the prompt arm sat at the floor, and the weight arm's invariance is a `run_bit_identity_control`
  **proof** (max |diff| 0.0), not a statistic.
- **Persona isolation under deliberate collision** (Phase 17). Three adversarial personas with
  contradictory values in the *same* slots, scored as N sweeps N ways by a cell-blind scorer with an
  adapter-off base column and a swap canary. All six off-diagonals `0/104`; all six Holm comparisons
  rejected at `p = 0.0078125`; the worst pair replicated at k=3 seeds, descriptive-only.
- **The privacy claim was falsified by its own audit** (Phase 18). Programmatic attacks at 42,480
  draws per arm against an adapter-off control at the identical budget returned
  **`LEAKAGE_DEMONSTRATED`** — 92/104 = 88.5%, 95% lower bound 0.8231, against a base arm at exactly
  `0/104`. The demo's toggle was corrected in README, `docs/REPORT.md` and the UI to read
  **availability, not authorization**.
- **Selective erasure was attempted and FAILED, and the failure is what shipped** (Phase 19). M1
  rank-1 ablation zeroed 78 of 288 components: condition (a) cleared *exactly* on its boundary with
  zero headroom (0/27 questions, 1,296 draws), while **all seven gated non-targets failed**, four at
  total generation loss, and 77.6% of the dialogue adaptation was destroyed. Headline, unsoftened:
  **selective erasure is not selective at 331,776 parameters.**
- **Two instruments disagreed on the same weights, and that became a co-headline** — with
  retroactive scope onto Phase 18. The rank/exposure instrument read rank 1 at ceiling exposure on
  all seven ruined facts at every checkpoint while generation collapsed underneath it, and reported
  M1 and M2 as bit-identical across all eight slots. Any Phase 18 conclusion resting on rank alone
  now carries that limit, propagated into the Phase 18 artifact itself.
- **The pre-registration discipline held for four phases and 63 artifacts, and authored Phase 19
  rather than being applied to it.** `scripts/erasure_gate.py` was committed at `23a830c` *before
  Phase 16 ran*; `erasure_is_worth_attempting(92, 104, 0, 104)` returned True on Phase 18's measured
  numbers, which is what admitted Phase 19 into the roadmap. `erasure_succeeded` was called exactly
  once and returned `FAILURE`. Ancestry verified over 63 artifacts, 0 violations; zero new runtime
  dependencies (`pyproject.toml` byte-identical, sha256-pinned).

**Ship decision — `DO NOT SHIP` (Phase 19):** withholds exactly ONE claim, that the verdict is
mechanically reproducible by the pinned CLI alone, and **withdraws no measurement**. Every number,
the verdict, and the co-headline stand. Five pin defects (A-E) are published rather than fixed —
editing a closed pin after the numbers exist would void the pre-registration ordering and every
number resting on it.

### Known Gaps and Deferred Items

**Known deferred items at close: 6** (see STATE.md `## Deferred Items`). All six are stale status
stamps over completed work — one debug session whose fix is evidenced by two completed Phase 18 arms,
two quick-task SUMMARYs missing only a `status:` field, and three `human_needed` verification verdicts
whose human gates were discharged in records written *beside* them. They were acknowledged rather than
resolved because re-stamping the three verdicts would erase what each verifier found.

**Tech debt carried forward: 16 items** across the four phases plus cross-cutting (full list in
`milestones/v3.0-MILESTONE-AUDIT.md`). All are prose, documentation or tooling; none touches a
measured number, a gate, or a requirement's status. Also carried: three phases whose VALIDATION.md
was never re-stamped after execution (17, 18, 19 read PARTIAL), and B1-a — a deep-link pointer that
cannot reach its scope limit additively, because both surfaces are frozen above their continuation
lines.

**Not a gap:** the `FAILURE` verdict and `DO NOT SHIP`. The milestone contracted to run the erasure
under a rule committed before any number existed and publish whatever came out. It did.

## v2.0 Weight-Based Memory (Shipped: 2026-08-12)

**Delivered:** Personalization that lives in the weights — a from-scratch LoRA adapter teaches user-specific facts into 331,776 parameters on a frozen conversational base, and a fresh process recalls them from an empty prompt with the context provably wiped, while from-scratch EWC keeps the fine-tune from destroying the base model. Every headline number is gated by a rule committed to git before the number existed.

**Stats:**

- Phases: 7 (09-15) | Plans: 39 | Tasks: 50
- Commits: 364 over 62 days (2026-06-11 -> 2026-08-12), range `d886aaf`..`ecf572d`
- Diff: 284 files changed, +95,132 / -188
- Tests: 408 passed, 1 skipped (CUDA-only fp16 AMP smoke), 0 failed; ruff clean
- Audit: 24/24 requirements satisfied, 7/7 phases verified, 17/18 integration links wired, 3/3 E2E flows complete (`.planning/milestones/v2.0-MILESTONE-AUDIT.md`, status: passed)

**Key accomplishments:**

1. **From-scratch LoRA** — `LoRALinear` (A-Gaussian/B-zero, alpha/r scaling) injected post-load into six named projections across 6 layers, 331,776 params in 72 tensors. Toggle on/off is 36 boolean writes on the live model; merge/unmerge is bit-exact via stored clone; eject restores a vanilla tree. No HuggingFace PEFT.
2. **From-scratch EWC** — per-example empirical diagonal Fisher (batch-1 autograd, mean-normalized so a cell reads as "x the importance of an average parameter") plus the Kirkpatrick quadratic anchor, spliced into the v1.0 training loop through an additive `penalty_fn` seam proven bit-identical to a pre-edit golden trajectory.
3. **The A/B that demonstrated no-forgetting** — two 4000-step arms identical but for the penalty. From a shared step-0 anchor of 2.1076, naive retention PPL ended at **8.524171** and EWC at **3.891140**: a 3.6x difference in base-task destruction, clearing the pre-registered margin (2 x 0.068930) by **33.61x**. Acquisition cost is reported descriptively with no gate (+0.380556, ~9.1%) — the win was not bought by failing to learn.
4. **Clean-room teach-then-recall** — closed-book, context wiped: taught-template recall **496/1008 = 0.4921** against a threshold of 0.2486, held-out template families **326/936 = 0.3483** against 0.2000. The adapter-off control on the same weights and same prompts scored exactly **0/2430**, with adapter-off logits bit-identical to the un-adapted base (max |diff| 0.0). Thresholds derived on a disjoint calibration set and committed before the run existed.
5. **Honest negatives kept, not smoothed** — the lambda sweep's pre-registered all-fail verdict ("EWC not demonstrable at this budget") stands unamended, with the later production lambda=0.01 logged as a separate dated discretionary choice. The retention win is scoped to teacher-forced PPL because free-running story mode measurably survives in neither arm (79 naive vs 69 EWC role-token leaks).
6. **Evidence you can regenerate** — figures are drawn only from a committed JSON artifact by a module structurally forbidden (AST walk + fresh-interpreter probe) from opening a checkpoint. The Fisher/delta correlation was measured against a rule committed before the artifact existed: Spearman **rho = 0.801544**, 95% CI [0.597984, 0.920291], gate passes on sign with magnitude reported as descriptive at n=36.

**Known deferred items at close:** 0. All pre-close open artifacts were resolved rather than acknowledged (`gsd-sdk audit-open` -> 0 items). v1.0's carried tech debt was also closed here: DEBT-01 (run.csv token under-count) landed before the first v2.0 training step, and DEBT-02's warm-sampling half — `evaluate.py` sampling without `forbid_ids`, open since v1.0 — was fixed in `3781a97` with the headline 2.1066 verified byte-identical afterward. Remaining non-blocking notes (W1 adapter `LoRAConfig` defaults, W3 hand-entered lambda=0 frontier point) are recorded in the milestone audit.

---

## v1.0 Foundation (Shipped: 2026-06-11)

**Delivered:** A correct, from-scratch ~13.9M-parameter GPT-style language model in pure PyTorch — BPE tokenizer, transformer decoder, resumable training harness — pretrained on TinyStories on the author's own Apple Silicon machine to fluent generation (headline perplexity 2.1066), shipped with an offline Gradio CPU demo, an executed research notebook, a 137-test green suite, and a consolidated technical writeup.

**Stats:**

- Phases: 8 | Plans: 29 | Tasks: 43
- Commits: 245 over 8 days (2026-06-04 → 2026-06-11)
- Code: 6,543 lines of Python (src + scripts + tests); 137 tests passing, 1 CUDA-only skip
- Model: 13,891,584 params (tied weights counted once), `best.pt` val_loss 0.7378 at step 49000, headline PPL 2.1066 over 12,636,922 held-out tokens
- Audit: 35/35 requirements satisfied, 8/8 phases verified, 20/20 integration links wired, 3/3 E2E flows complete (.planning/milestones/v1.0-MILESTONE-AUDIT.md)

**Key accomplishments:**

1. From-scratch ~13.9M-param GPT-2-style decoder (causal MHA, pre-norm blocks, weight tying via shared tensor, GPT-2 init with residual scaling) — every silent-bug gate (causality perturbation, init-std, param-count band, `data_ptr` tying) green
2. From-scratch byte-level BPE tokenizer with deterministic merges, exact round-trips, frozen JSON artifact, and a tiktoken-gpt2 equivalence oracle proving the algorithm (test-only, never a runtime dependency)
3. Full local Apple-Silicon (M3/MPS, fp32) pretraining run on TinyStories — 50,000 steps, `best.pt` val_loss 0.7378, headline perplexity 2.1066 over 12.6M held-out tokens, kill+resume survived mid-run
4. Resumable training harness proven on a bigram before the transformer: AdamW + warmup/cosine, AMP discipline, open-dict checkpoints with RNG-state restore (bit-for-bit resume), restart-survivable CSV logging
5. Offline Gradio CPU demo with shared `generate()` (greedy/temperature/top-k/top-p, EOS stop, context crop) and a dead-id logits mask making it crash-proof at every in-UI setting
6. Portfolio rigor: 4-run ablation cohort with comparison table, executed `demo.ipynb`, 440-line technical REPORT with effective-vocabulary honesty (547 live of 8192 ids), and both M2 seams (named `nn.Linear` projections, `assemble_loss(..., extra_penalties=())`) locked in as verified acceptance criteria

**Known deferred items at close:** 1 (see STATE.md Deferred Items) — plus non-blocking tech debt logged in the milestone audit (forbid_ids not threaded into evaluate.py warm sampling; run.csv tokens column ×256 under-count; TODO(calibration) markers on shipped-final constants; tokenizer corpus identity under-disclosed in REPORT; one-time release-asset check).

---
