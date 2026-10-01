# V6-PREREG-09 — the research the v6.0 E3/E4 thresholds rest on

**Written:** 2026-10-01 (Phase 35, Plan 01). **Requirement:** PREREG-09.

## 1. Purpose and the rule of this note

PREREG-09 requires two pieces of research to be on record before any E3 or E4 threshold is
locked: (a) the Steinke–Nasr–Jagielski one-run audit bound, which E4 (AUDIT-01) uses to compute
its auditor ceiling; and (b) the selection accounting for E3's hyperparameter grid. This note is
committed on its own, before `scripts/phase35_prereg.py` exists, so the ordering "research first,
thresholds second" is a fact of the git history. `tests/test_phase35_prereg.py` checks that the
first commit adding this note is an ancestor of every commit that touches the module.

**This note holds no threshold value.** It paraphrases the passages the thresholds rest on and
records the reproduction that justifies trusting our port. Every value lives only in
`scripts/phase35_prereg.py`, under these names:

- `eps_lower_one_run`, `p_value_one_run` — the stdlib port of the one-run bound;
- `ONE_RUN_PUBLISHED` — the two values printed in the paper that the port must reproduce;
- `ENTRIES["one_run_tolerance"]` — the declared reproduction tolerance;
- `one_run_reproduction_holds` — the gate that re-runs both reproductions at call time;
- `CURVE_TOTAL`, `SELECTION_ACCOUNTED`, `DELTA` — E3's basic composition, its flag, and the δ,
  all bound by reference to the v4.0 modules.

**Provenance of the citations.** Both papers were read at the source (arXiv PDF) during Phase 35
research on 2026-10-01 and are tagged `[VERIFIED: arXiv PDF read this session]` in
`.planning/phases/35-v6-0-pre-registration-and-the-research-it-rests-on/35-RESEARCH.md`
(§"PREREG-09 (a)" and §"PREREG-09 (b)"). The theorem numbers, pages and printed values below are
transcribed from that reading. Both sources are verified; neither is cited from memory.

## 2. (a) Steinke, Nasr, Jagielski — "Privacy Auditing with One (1) Training Run"

arXiv:2305.08846v1 (15 May 2023; v1 is the only version). The PDF footer reads
"arXiv:2305.08846v1 [cs.LG] 15 May 2023".

### Algorithm 1 (p. 3)

The auditor plants m canaries. Each canary is included in the training input independently with
probability 1/2 (the paper writes this as a uniformly random sign S_i ∈ {−1, +1}, E[S_i] = 0).
After the single training run the auditor scores every canary, guesses "included" (+1) for the
k+ highest scores and "excluded" (−1) for the k− lowest, and abstains on the rest; r = k+ + k− is
the number of guesses and v the number that are correct. Footnote 1 (p. 3) notes that inclusion
probabilities other than 1/2 can be handled through Proposition 5.7, but the authors consider that
route unlikely to be useful.

### Theorem 5.2 (Main Result, p. 14)

If the training mechanism is (ε, δ)-differentially private in the canary inclusion vector and the
inclusion vector is uniform, then the probability that the number of correct guesses W reaches v is
at most β + α·2m·δ. Here β is the probability that a dominating sum of Bernoulli(e^ε/(e^ε+1))
variables (one per guess) reaches v, and α is the largest ratio, over shifts i = 1..m, of the
extra tail mass gained by lowering the threshold from v to v − i, divided by i. In words: a DP
mechanism cannot make the guesser much better than a coin biased by e^ε/(e^ε+1), except for a
slack that grows with m·δ.

### Corollary 5.4 (Ternary Guesses, pp. 15–16)

Specialising Theorem 5.2 to guesses in {−1, 0, +1} with at most r non-abstentions gives the
computable form: P[W ≥ v] ≤ f(v) + 2mδ·max_i (f(v − i) − f(v))/i, with f(v) the upper tail
P[Binomial(r, e^ε/(e^ε+1)) ≥ v]. The paper states (p. 15) that this is the form of Theorem 5.2 it
uses in all of its experimental results. This is the p-value `p_value_one_run` computes.

### Lemma 4.7 / §4.3 (pp. 8–9) — from a p-value to an ε lower bound

An audit converts the bound into a statistical test: for each candidate ε the null hypothesis "the
mechanism is ε-DP" is rejected when the observed v has p-value below β. The reported lower bound
is the largest ε that is still rejected at level β, held with confidence 1 − β. This is what
`eps_lower_one_run` returns.

### Appendix D (pp. 45–46) — the reference implementation

Appendix D prints Python pseudocode with two functions: `p_value_DP_audit(m, r, v, eps, delta)`
(Corollary 5.4's bound, using scipy's binomial `sf`/`pmf`) and `get_eps_audit(m, r, v, delta, p)`
(raise an upper bracket until the p-value reaches p, then bisect 30 times and return the
conservative low end of the bracket). Our port follows it line for line, with scipy replaced by an
exact `math.lgamma` binomial pmf summed with `math.fsum`, and with the pseudocode's `assert`s
replaced by refusals that `python -O` cannot strip.

### Reproduction of the paper's printed values

Computed by the stdlib port during research (35-RESEARCH.md §"PREREG-09 (a)"):

| Where (page) | Inputs (m, r, v, δ, β or ε) | Published | Ours | \|diff\| |
|---|---|---|---|---|
| App. D, p. 45 | p-value(100, 100, 75, ε = ln 3, δ = 0) | 0.553 | 0.553470823848239 | 4.7e-4 |
| App. D, p. 45 | get_eps(100, 100, 75, δ = 0, β = 0.05) | 0.702 | 0.7022139308974147 | 2.1e-4 |
| App. D, p. 46 | get_eps(100, 100, 75, δ = 1e-4, β = 0.05) | 0.699 | 0.6994668124243617 | 4.7e-4 |
| **App. D, p. 46 — PIN 1** | **get_eps(1000, 100, 75, δ = 1e-4, β = 0.05)** | **0.673** | **0.6729846633970737** | 1.5e-5 |
| **§7 text, p. 28 (Fig. 11) — PIN 2** | **m = 100000, r = 1510, v = 1439, δ = 1e-5, 95%** | **ε ≥ 2.675** | **2.6758510060608387** | 8.5e-4 |
| §7 text, p. 28 (Fig. 10) | r = 10000, v = 9820, δ = 1e-5, 95%; m not stated | ε ≥ 3.87 | 3.8713169284164906 (m = r assumed) | 1.3e-3 |

The two pinned values are PIN 1 (Appendix D, p. 46) and PIN 2 (§7, p. 28, Fig. 11). PIN 1 exercises
abstentions (r < m) and the 2mδ term; PIN 2 uses the δ and the 95% confidence v6.0 uses. The
Fig. 10 "3.87" row is **not** pinned: p. 28 does not state m for it, so reproducing it requires an
assumption about the input.

### Why the reproduction tolerance is one unit in the last printed digit

The tolerance is declared only as `ENTRIES["one_run_tolerance"]` in `scripts/phase35_prereg.py`;
this note does not repeat its number. Its derivation:

- Both pins are printed to three decimals, and the paper is not consistent about how it shortens
  them: 0.67298 prints as 0.673 (rounding), while 2.67585 prints as 2.675 (truncation). A half-unit
  tolerance would therefore wrongly fail PIN 2. One unit in the last printed digit covers both
  conventions.
- One unit still catches the two natural porting bugs with a wide margin (at least 26× the
  observed error). Measured mutants: dropping the δ term moves PIN 1 to 0.7022; using r instead of
  m in the 2mδ slack moves PIN 2 to 2.8051.

### The δ = 0, v = r closed form

With no δ slack and every guess correct, the p-value is just q^r with q = e^ε/(e^ε+1), so the
lower bound has the exact form ε = −ln(β^(−1/r) − 1). For r = 16, β = 0.05 this is
1.5803231357927883; the port returns 1.5803231354802847, the difference being the 30-step
bisection's precision. This check needs no paper value and catches errors in the bisection itself.

### Constraints later phases must honour (constraints, not locks)

- **Inclusion probability 1/2.** It is the only inclusion probability the reproduced method covers
  (Algorithm 1 and Appendix D assume it). Proposition 5.7 covers others but has no reproduced
  implementation here.
- **k+ and k− fixed before the run.** On p. 25 the authors report evaluating several k± and keeping
  only the highest, which they acknowledge reduces the confidence. A v6.0 guesser must fix k+/k−
  before the training run, or use the union-bound form of Corollary 5.8 (p. 22).
- **Sensitivity to δ and to abstentions (pp. 28–29).** The δ term is multiplied by roughly
  m/(rβ), so the bound degrades quickly when δ is large or most canaries are abstained on.
- **The canary unit is the fact.** Under the v6.0 privacy unit "one taught fact", each canary must
  be a fact, not a question about a fact; otherwise several canaries share one protected unit,
  group privacy applies, and the theorem's one-bit-flip premise breaks.

### Observation for Phase 36/43 pricing (computed by the port; NOT a lock)

Maximum detectable ε with a perfect guesser (v = r = m), δ = 1e-5, β = 0.05:

| m | 16 | 32 | 64 | 100 | 128 | 135 | 136 | 184 | 256 | 512 |
|---|---|---|---|---|---|---|---|---|---|---|
| ceiling | 1.5798 | 2.3204 | 3.0364 | 3.4902 | 3.7396 | 3.7933 | 3.8007 | 4.1046 | 4.4352 | 5.1245 |

This ceiling exceeds the AUDIT-02 cut (read from `results/phase26_canary.json` at use, D-09) only
from m ≥ 136 independently randomised canaries. It is recorded here because it will most likely
decide E4's branch; Phase 43 computes the real value.

## 3. (b) Papernot and Steinke — "Hyperparameter Tuning with Renyi Differential Privacy"

arXiv:2110.03620v2 (v1 7 Oct 2021; v2 14 Mar 2022, "Published as a conference paper at ICLR
2022"). v2 was read.

### Theorem 2 (Truncated Negative Binomial, p. 5)

If each training run Q satisfies Rényi DP at two orders, the outputs are totally ordered, and the
number of runs K is drawn from the truncated negative binomial distribution D_{η,γ}, then running Q
K times and releasing only the best output is RDP with a cost that is a constant multiple of the
per-run cost plus logarithmic terms in E[K]. The point is that the tuning cost does not grow
linearly in the number of candidates tried.

### Corollaries 3–4 (p. 6)

Corollary 3 is the pure-DP form of Theorem 2: the tuned mechanism is ((2+η)ε, 0)-DP, and η = 1
(a geometric K) recovers Liu and Talwar's 3ε. Corollary 4 restates the result for zero-concentrated
DP.

### Theorem 6 (Poisson, p. 7)

The same statement with K drawn from a Poisson distribution of mean μ: the tuned mechanism's RDP
cost is the per-run cost plus a term in μ and log μ, under a condition on the second order's ε.

### The four hypotheses (§3.3, p. 5)

1. The number of runs K is **random**, drawn from the stated distribution.
2. Each run picks its candidate **uniformly at random** from the candidate set ("random search").
3. There is a **uniform** Rényi DP bound over all candidates.
4. Only **the best** of the K outputs is released (the output space is totally ordered).

The paper also remarks (p. 8) that a point mass on K corresponds to naive repetition, i.e.
ordinary composition, and (p. 2) that its results apply to random repetition whereas composition
gives linear bounds.

### E3 against each hypothesis

E3's grid (D-17, RECIPE-01/02/03) is 4 recipes × σ ∈ {0, 0.5, 1}, about 12 runs with the σ = 0
controls included, each run once, and **every** configuration's ε is published (RECIPE-02).

- **Hypothesis 1 fails.** K is fixed by the grid, not drawn at random.
- **Hypothesis 2 fails.** The candidates are an enumerated grid, not uniform random draws.
- **Hypothesis 3 is moot.** A uniform bound over σ ∈ {0.5, 1} and the step counts could be
  arranged, but with the other hypotheses failing it buys nothing.
- **Hypothesis 4 fails.** Every output is released, not only the best.

**Verdict.** No finer accountant enters v6.0. E3 uses basic composition only, with
`selection_accounted = false` (RECIPE-02), which is exactly D-12's default when the hypotheses do
not match. No Papernot–Steinke worked-example test is needed, because the method is not used.

### What basic composition sums

Basic composition sums only the noised configurations (σ ∈ {0.5, 1}). The σ = 0 controls carry no
ε at all, and `phase25_epsilon.curve_total` refuses a `None` or non-finite entry, so a control can
only be left out deliberately at the call site, never absorbed silently as zero.

Hand-checkable worked example (the D-12 test pins it):
`curve_total([1.5, 2.25, 0.25], delta=1e-5)` returns `(4.0, 3 × 1e-5)`, where the total δ is the
product `len × δ` computed in float (it prints as 3.0000000000000004e-05, not the literal 3e-05).

## 4. Sources

- Steinke, Nasr, Jagielski, "Privacy Auditing with One (1) Training Run", arXiv:2305.08846v1,
  https://arxiv.org/abs/2305.08846 — abs page (submission history: v1 only) confirmed 2026-10-01;
  PDF read 2026-10-01 (35-RESEARCH.md). Pages used: Algorithm 1 p. 3; Lemma 4.7 pp. 8–9;
  Theorem 5.2 p. 14; Corollary 5.4 pp. 15–16; Proposition 5.7 p. 19; Corollary 5.8 p. 22; §6 p. 25;
  §7 p. 28; Appendix D pp. 45–46.
- Papernot, Steinke, "Hyperparameter Tuning with Renyi Differential Privacy", arXiv:2110.03620v2
  (ICLR 2022), https://arxiv.org/abs/2110.03620 — abs page (v1 7 Oct 2021, v2 14 Mar 2022)
  confirmed 2026-10-01; PDF read 2026-10-01 (35-RESEARCH.md). Pages used: §3.3 p. 5; Theorem 2
  p. 5; Corollaries 3–4 p. 6; Theorem 6 p. 7; point-mass remark p. 8.
