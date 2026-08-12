# Stack Research — v3.0 "Adversarial Privacy Audit and Selective Memory Erasure"

**Domain:** Measurement/audit milestone on top of a shipped from-scratch LoRA+EWC LM
**Researched:** 2026-08-12
**Confidence:** HIGH

---

## Verdict (read this and stop, if you read nothing else)

# ZERO NEW DEPENDENCIES.

**`pyproject.toml` should be byte-identical at v3.0 close to what it is at v3.0 open.**

All three v3.0 capabilities — weight-vs-prompt control, the N×N isolation matrix, and the
black-box extraction audit — are **new drivers over existing, already-tested seams**. Every
primitive they need is already in the package or in `numpy` / `matplotlib` / the Python stdlib:

| v3.0 need | Already exists | Where |
|---|---|---|
| Prompt-stuffed condition (Phase 16) | `build_recall_prompt(tok, q, persona=...)` — the `persona=` argument is **already implemented, already tested**, and already used by the Phase-14 D-11.1 fairness control | `personacore.dialogue` |
| Adapter-only condition (Phase 16) | The Phase-14 bare path — `build_recall_prompt(tok, q)` with the clean-room proof `assert_no_value_in_prompt` | `scripts/phase14_recall.py` |
| Swap adapter i onto the base (Phase 17) | `load_adapter_weights(model, artifact)` — key+shape audit then `strict=False`; identical key sets across adapters means a swap is a full overwrite | `personacore.lora.inject` |
| Train N adversarial personas (Phase 17) | `scripts/teach_persona.py` + the frozen-base LoRA training discipline proven in Phase 9/14 | existing |
| Score a cell (Phase 17/18) | `run_scored_recall(...)` → `{k, n, rate, by_split, ...}` — already parameterized by `items` and `tier_label` | `scripts/phase14_recall.py` |
| Negative control (Phase 18) | `adapter_disabled(model)` — bit-identical to the un-adapted base, proven at 0/2430 | `personacore.lora.inject` |
| Repeated-sampling attack (Phase 18) | `draw_all()` — greedy + N seeded draws, per-draw `torch.Generator` seeding | `scripts/phase14_recall.py` |
| Attack-prompt construction (Phase 18) | `render_family(family_id, fact)` — the templated phrasing-family renderer | `scripts/phase14_factset.py` |
| Success/extraction detection | `contains_value()` / `normalize()` / `find_contradictions()` — mechanical, committed, lexicon-based | `scripts/phase14_recall.py` |
| Permutation p, bootstrap CI, rank stats | ~40 lines of pure numpy, already written and already pre-registered | `scripts/phase15_stats.py` |
| Heatmap | `matplotlib.pyplot.imshow` + `colorbar` + `ax.text`, drawn from a committed JSON artifact | `scripts/plot_phase13.py` pattern |

The only genuinely new *code* v3.0 needs on the statistics side is **~60 lines of numpy/stdlib**
(Wilson interval, Holm step-down, a sign-flip paired permutation, and a **cluster** bootstrap).
That is smaller than the diff required to add, pin, document, and CI-verify a single new
dependency — and it stays inside a register the codebase has now committed **twice**:

> `src/personacore/continual/fisher.py:50` — "Hand-rolled: scipy is NOT a dependency
> (zero-new-deps posture)."
>
> `scripts/phase15_stats.py:6` — "The rank machinery below is ~40 lines of pure numpy because
> scipy is NOT a dependency (`pyproject.toml`: `numpy~=2.4`, `regex~=2026.5`) and must not
> become one for a single correlation (D-12, the `fisher.py::_spearman` zero-new-deps register)."

Two independent modules, two milestones apart, both declined scipy for a rank correlation and
both said so in committed code. A grep of the repo confirms **zero** imports of scipy, pandas,
seaborn, or statsmodels anywhere in `src/`, `scripts/`, or `tests/`.

**Adding scipy at Phase 16-18 would silently retcon that register.** The v2.0 discipline is a
first-class portfolio asset; "we hand-rolled Spearman twice to avoid a dependency, then took the
dependency two phases later for a Wilson interval that is six lines of algebra" is a worse
story than either consistent choice. And v3.0 is a *privacy audit* — a milestone whose entire
output is trust in a measurement — which is the worst possible place to relax a stated
discipline.

---

## Recommended Stack

### Core Technologies

**Unchanged from v2.0. No version bumps required by v3.0.**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 (venv-mandatory; `requires-python = ">=3.10,<3.12"`) | Runtime | Unchanged. The dev box's 3.14 is still not a supported target; CI pins 3.11. v3.0 introduces no syntax or stdlib requirement outside 3.10. |
| PyTorch (`torch`) | `2.7.*` (the `[cpu]` extra) | Inference for every v3.0 measurement; LoRA training for the N adversarial personas | Unchanged. v3.0 runs the **same** forward path as Phase 14 — `generate()` at ≤48 new tokens on a 13.9M-param model, MPS fp32 or CPU. No new kernel, no new dtype, no AMP. Bumping torch mid-milestone would put every v3.0 number on a different runtime than `persona_adapter.pt`'s v2.0 numbers, for zero benefit. |
| NumPy | `~=2.4` | All v3.0 statistics: Wilson, cluster bootstrap, Holm, paired permutation | Unchanged. `np.random.default_rng` (local generator, global RNG untouched — the `phase15_stats.py` register), `np.quantile`, `np.corrcoef`, `np.argsort` cover 100% of the v3.0 statistical surface. |
| matplotlib | `~=3.10` (the `[demo]` / `[notebook]` extras) | The M_ij heatmap (Phase 17) and the extraction-rate figure (Phase 18) | Unchanged. `imshow` + `colorbar` + `ax.text` is the whole heatmap. Already the project's only plotting tool, already offline, already covered by the CPU-only suite. |

### Supporting Libraries

**Unchanged. Nothing added, nothing removed.**

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `regex` | `~=2026.5` | Tokenizer pre-tokenization | Untouched by v3.0 — tokenizer is FROZEN and out of scope. |
| `gradio` | `>=5,<6` | Live demo | Only if Phase 16/18 wants a live prompt-stuffed-vs-adapter toggle in the UI. The existing Phase-14 panel already renders `render_context_dump`; a second condition is a second call to the same function. **Note:** the `demo` extra is required for `make test` (`tests/test_phase14_demo.py` imports gradio at module scope) — this stays true, it is not a new fact. |
| `pytest` | `~=9.0` | The CPU-only suite | Every new v3.0 stats function is a pure function over floats and is unit-testable without torch — exactly the `phase15_stats.py` / `finetune_ab.py` gate-as-pure-function precedent. |
| `tiktoken` | `~=0.13` | Test oracle only | Untouched. |
| `ruff` / `isort` | `~=0.15` / `~=8.0` | Lint/format | Untouched. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `math` (stdlib) | `sqrt`, `lgamma`, `comb` | Closes the *only* apparent scipy requirement: an exact binomial tail (and therefore Clopper-Pearson by bisection) is reachable from `math.lgamma` alone. See "Statistics" below. |
| `json` (stdlib) | The committed measurement artifact | v3.0 must follow the v2.0 Phase-15 key decision: *extract once into a committed JSON, then plot and gate only from that artifact*. `results/phase17_matrix.json` is the M_ij analogue of `results/phase15_norms.json`. |
| `hashlib`, `os`, `time` (stdlib) | Provenance echoes (`_sha256`, pid, wall clock) | Already the established Phase-14 pattern; Phase 17/18 reuse it verbatim across N adapters. |

## Installation

```bash
# Nothing to install. The v3.0 environment IS the v2.0 environment.
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[cpu,dev,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
make test
```

**If a v3.0 phase plan proposes a `pyproject.toml` edit, that is the signal to re-read this
document before approving it.**

---

## Answers to the four specific questions

### Q1 — Statistics: is scipy warranted now? **No. Hand-roll, ~60 lines.**

Four statistical objects are needed. All four are closed-form or resampling-based, and none
requires a special function that numpy lacks.

#### (a) Proportion confidence intervals → **Wilson score interval**, ~8 lines

Extraction rate = k successes out of n attempts. `k/n` alone is not reportable at this
milestone's rigor bar.

```
z    = 1.959963984540054           # two-sided 95%
p    = k / n
den  = 1 + z*z/n
mid  = (p + z*z/(2*n)) / den
half = (z/den) * sqrt(p*(1-p)/n + z*z/(4*n*n))
lo, hi = mid - half, mid + half
```

**Why Wilson and not Wald:** Wald (`p ± z·sqrt(p(1-p)/n)`) collapses to the degenerate `[0, 0]`
at `k = 0` — and `k = 0` is the *expected* result for the Phase-18 no-adapter negative control
and for well-isolated off-diagonal M_ij cells. An interval that reports `[0.000, 0.000]` for a
privacy claim is not conservative, it is wrong, and at this project's bar it would be the kind
of thing a reviewer catches. Wilson stays well-defined and asymmetric at both boundaries.
(Brown, Cai & DasGupta 2001, *Interval Estimation for a Binomial Proportion*, recommends Wilson
or Agresti–Coull over Wald, and notes Clopper–Pearson is needlessly conservative.)

**Sanity companion for the k = 0 case:** the *rule of three* — the one-sided 95% upper bound on
a rate after 0 successes in n trials is ≈ `3/n`. Phase 14's `0/2430` therefore supports
"≤ ~0.12%", not "0%". This is one line of arithmetic and it is the honest way to report a
perfect negative control. Wilson's two-sided upper at k=0 is `z²/n / (1+z²/n)` ≈ `3.84/n`,
slightly wider; either is defensible, **pin one in the pre-registration** and state which.

**The scipy escape hatch is closed, explicitly.** The one interval that genuinely needs a
special function is Clopper–Pearson (Beta inverse CDF, i.e. `scipy.stats.beta.ppf`). But
Clopper–Pearson is *defined* as the exact binomial tail inverted, and the exact binomial tail is
computable from `math.lgamma` (stdlib) in float, or `math.comb` (stdlib) in exact integers; the
tail is monotone in p, so a 30-iteration bisection lands the bound to machine precision in ~12
lines. **So even the "scipy is required" case is not a scipy case.** Recommendation remains
Wilson — it is shorter, better-behaved, and the statistically preferred choice — but the
argument is closed either way.

#### (b) The paired weight-vs-prompt comparison (Phase 16) → **sign-flip paired permutation**, ~12 lines

Phase 16 scores the **same question set** under two conditions. That is paired data, and
treating it as two independent proportions throws away the pairing that makes the design strong.

- Per question `q`, compute `d_q = rate_weights(q) − rate_prompt(q)` over its 9 draws.
- Null hypothesis: the condition label is exchangeable within a question → the sign of `d_q` is
  ±1 with probability ½.
- Permutation: draw `s ∈ {−1,+1}^Q`, recompute `mean(s ⊙ d)`, count `|·| ≥ |observed|`.
- Add-one p (`(ge+1)/(n_perm+1)`), exactly as `phase15_stats.permutation_p` already does.

This is the same shape as the existing `permutation_p`, with `rng.permutation(ranks)` swapped
for `rng.choice([-1,1], Q)`. **~12 lines, reusing an already-pre-registered pattern.**

McNemar's exact test is the textbook alternative for paired binary outcomes and needs only a
binomial tail on the discordant pairs — again `math.comb`, again no scipy. Either is fine;
the permutation version is preferred because it operates on per-question *rates* (9 draws each)
rather than forcing a single binary outcome per question, which is what the data actually is.

#### (c) THE LOAD-BEARING STATISTICAL POINT: **the data is CLUSTERED. Bootstrap over QUESTIONS, not over draws.**

This is the highest-value finding in this document and **no library fixes it**.

Phase 14's `0.4921` is `496/1008`, where those 1008 completions are 112 questions × 9 draws, and
those questions come from a small number of template *families* over 10 facts. The 1008 draws
are **not** 1008 independent Bernoulli trials:

- 9 draws share a prompt and a fixed set of weights — they are strongly correlated.
- Questions within a family share a frame.
- Questions about the same fact share whatever the adapter did or did not learn about that slot.

A Wilson interval on `n = 1008` implies an effective sample size of 1008 and will be **far too
narrow** — likely by a factor of ~3 in width, since the effective n is closer to the number of
*facts* (10) or *questions* (112) than the number of draws. Adding scipy would compute that
too-narrow interval to more decimal places. **A precise number for the wrong model is worse
than an honest wide one.**

The fix is a design choice, not a package:

1. **Declare the unit of analysis in the pre-registration.** Recommended: the **question** is
   the unit; `rate_q = k_q / 9` is the observation; there are Q observations per cell.
2. **Cluster bootstrap:** resample **questions** with replacement (optionally two-stage:
   resample facts, then questions within fact), recompute the pooled rate, take the 2.5/97.5
   percentiles. This is `phase15_stats.bootstrap_ci` with the resampling unit changed from
   "cell pair" to "question", ~8 lines of edit.
3. **Report Wilson alongside, explicitly labelled** as the independence-assuming interval, so a
   reader can see the gap between the naive and clustered widths. That contrast is itself a good
   portfolio moment.

`phase15_stats.py` already carries a committed, pre-registered honesty note that the percentile
bootstrap is biased and anti-conservative at small n. That note **must be carried forward** for
Phase 17/18, where the number of clusters may be as low as ~10 facts — arguably smaller n than
Phase 15's 36 cells. Do not silently upgrade to BCa after seeing a result; pin the method in a
`CI_METHOD` string like Phase 15 did.

#### (d) Multiple comparisons across the N×N matrix → **Holm–Bonferroni**, ~10 lines

At N = 3–4 the matrix has 9–16 cells, of which **6–12 are off-diagonal** — the cells that carry
the isolation claim. That is a small, fixed, pre-registerable family of tests.

```
order = argsort(p)                          # ascending
m     = len(p)
adj   = maximum.accumulate( (m - arange(m)) * p[order] ).clip(max=1.0)
```

**Holm over Benjamini–Hochberg, for a substantive reason, not a lazy one.** The off-diagonal
cells are **not independent**: they share adapters (row-wise), share question sets
(column-wise), and share the same frozen base. BH's validity requires independence or PRDS;
Holm is valid under **arbitrary dependence**. So the shorter implementation is also the one
whose assumptions the design actually satisfies. Say that in the pre-registration.

Also worth pre-registering: **the diagonal and the off-diagonal are different claims.** The
diagonal ("adapter i answers persona i's questions") is a *recall* claim and is the Phase-14
claim replicated N times. The off-diagonal ("adapter i does NOT answer persona j's questions")
is the *isolation* claim, and it is a claim of **near-zero**, i.e. an equivalence-style claim.
Standard null-hypothesis testing does not prove a null. The honest form is:

> the off-diagonal rate's **upper** confidence bound sits below a pre-registered leakage
> ceiling (e.g. below the no-adapter negative-control's own upper bound, or below the
> `heldout_gate` floor)

— which is a **one-sided upper bound comparison**, computed from the same Wilson/bootstrap
machinery and needing nothing new. Pre-register the ceiling before the matrix exists, per the
established v2.0 discipline. Multiplicity then applies to the off-diagonal family only.

#### Statistics summary

| Object | Implementation | Lines | New dep? |
|---|---|---|---|
| Proportion CI | Wilson (closed form) | ~8 | No — `math.sqrt` |
| Zero-success bound | rule of three (`3/n`) | 1 | No |
| Paired weight-vs-prompt | sign-flip permutation | ~12 | No — reuses `permutation_p` shape |
| Cluster CI on a rate | question-level bootstrap | ~8 | No — edits `bootstrap_ci`'s resample unit |
| N×N multiplicity | Holm–Bonferroni step-down | ~10 | No — `np.argsort` + `np.maximum.accumulate` |
| Exact binomial tail *(if ever wanted)* | `math.lgamma` + bisection | ~12 | No |
| **Total** | | **~50–60** | **None** |

**Recommendation: put these in one new module, `scripts/phase17_stats.py` (or
`src/personacore/stats.py` if Phase 18 also imports them), following `phase15_stats.py`'s exact
shape** — module-level pre-registration constants, pure functions, method strings that travel
with the number, and a `SystemExit`-on-malformed-artifact reader. Do **not** unify it with
`phase15_stats.py`; that module carries a committed pre-registration for a specific claim and a
deliberate DO-NOT-UNIFY note about its own `_spearman` divergence. Import from it if a helper is
genuinely shared; never edit its pre-registration block.

### Q2 — Does N×N scoring need anything beyond the existing loop? **No. It needs one outer loop and one seeding discipline.**

`run_scored_recall(model, tok, device, forbid, items, *, tier_label, excluded=())` already
returns `{tier, questions, k, n, rate, by_split, contradictions, hedging, n_stopped, ...}` —
which is exactly one **cell** of M_ij. The matrix is:

```
model, ... = load_adapted_model(device, adapter_path=personas[0].adapter)   # ONE base load
for i, persona_i in enumerate(personas):
    load_adapter_weights(model, load_adapter(persona_i.adapter, ...))       # swap in place
    for j, persona_j in enumerate(personas):
        cell[i][j] = run_scored_recall(model, tok, device, forbid,
                                       stamp_seed_indices(questions_of[j]),
                                       tier_label=f"M[{i}][{j}]")
```

Four things to get right, all of which are lessons the existing code already learned:

1. **Adapter swap does not need a base reload.** All N adapters share an identical `lora_` key
   set (same rank, same base, same 36 wrapped projections), so `load_adapter_weights` fully
   overwrites adapter i with adapter j — no residue. The key+shape audit runs *before* any
   tensor is copied, so a rank-mismatched persona fails loudly instead of half-applying.
   `eject_adapter` + re-`inject_lora` between cells is available but unnecessary and slower.
   **Add a cheap structural check anyway:** after each swap, assert a known `lora_B` tensor's
   hash changed — a silently-failed swap would make M_ij look perfectly isolated for the most
   embarrassing possible reason.
2. **Seed pairing is the known trap.** Phase 14's CR-01 defect — deriving the seed from
   `enumerate(items)` rather than from the item — left 158 of 270 control questions unpaired
   while the report asserted pairing. `stamp_seed_indices` exists precisely to fix this. In an
   N×N matrix the same defect is N× more likely: **every cell in a column must score question j
   under the same per-question seed**, or row-to-row differences partly reflect different RNG
   streams. Stamp the question sets **once**, outside both loops, and pass the same stamped
   tuples to every cell.
3. **`RecallItem` already binds question → fact.** Cross-scoring is "score persona j's
   questions against **persona j's** values while adapter **i** is loaded" — the value to look
   for travels with the item, so the existing `score_question(completions, item.fact.value)`
   call is already correct for off-diagonal cells with no change.
4. **Adversarial collision needs a lexicon, and `find_contradictions` already is one.** With
   colliding names and contradictory same-slot values, the interesting off-diagonal event is not
   just "adapter i emitted persona j's value" but "adapter i emitted **both**". `find_contradictions`
   already detects exactly that, mechanically, from a committed lexicon, with no editorial
   judgment. For Phase 17 the lexicon is `{all personas' values} ∪ GATE_REJECTED_CANDIDATES` —
   a union, not a new mechanism.

**Compute:** 16 cells × ~60 questions × 9 draws × ≤48 new tokens at 13.9M params. Well inside
PROJECT.md's "minutes-to-hours on the M3". Cut the per-persona question count before cutting
draws — draws are what make the rate a rate.

**One real risk to flag for the roadmap, not a stack risk:** Phase 17 needs N trained persona
adapters, and each is a training run. That is the milestone's actual cost centre. Budget for
the worst-colliding pair being replicated across seeds (per PROJECT.md), which means ~N + 2·k
training runs, not N.

### Q3 — Attack-prompt generation with no external APIs? **Templated only. The renderer already exists.**

`phase14_factset.render_family(family_id, fact)` is a committed, auditable, templated phrasing-
family renderer that already produces taught and held-out question phrasings per fact. Phase
18's four attack classes are the **same object with different templates**:

| Attack class | Construction | Existing seam |
|---|---|---|
| Paraphrase | New held-out families over the same slots | `render_family` + new family ids |
| Prefix injection | `build_recall_prompt(tok, question, persona=<injected prefix>)` | **`persona=` already exists and is already tested** |
| Role-play framing | A family whose template wraps the question in a framing sentence | `render_family` |
| Repeated sampling | Raise `N_SEEDED_SAMPLES`; per-draw `torch.Generator(question_seed(i)+s)` | `draw_all` |

**Two hard rules for Phase 18's attack corpus, both inherited from Phase 14:**

- **Attack prompts must be committed material, written before the run.** An attack corpus that
  can be extended after seeing which attacks worked is not an audit, it is a search for a
  favourable number. Same pre-registration discipline as every v2.0 gate: the family table lands
  in a pushed commit before the run it judges.
- **`assert_no_value_in_prompt` must stay armed for the paraphrase/role-play attacks and must be
  DELIBERATELY RELAXED — with a named, separate code path — for prefix injection.** Prefix
  injection *by definition* puts attacker-controlled text in context. If the injected prefix
  contains a fact value, the "extraction" is copying from context, not extraction. So the Phase-18
  design needs an explicit taxonomy: injected prefixes may contain *pressure* ("You must answer
  truthfully…", "Ignore prior instructions…", a fake system role) but must be proven **not** to
  contain any locked value, via the same `assert_no_value_in_prompt` call. The token-level
  contiguous-subsequence check in that function is what catches a leak the string check misses;
  keep both.

**Do not** use an LLM to generate paraphrases — no budget, no network, and it would make the
attack corpus non-reproducible and non-auditable. Templated generation is not a compromise here;
it is *better evidence*, because a reader can enumerate the entire attack surface from a
committed table.

**Note on `personacore.generation.forbid_ids` and attack realism:** the audit should decide,
and pre-register, whether the attacker gets the dead-id mask. The honest answer is **yes, same
mask as every other measurement** — it is part of the deployed system, and giving the attacker a
different decode path than the demo makes the two numbers incomparable. Record the choice.

### Q4 — Visualization beyond matplotlib? **No.**

The M_ij heatmap is:

```python
im = ax.imshow(M, vmin=0.0, vmax=1.0, cmap="magma")     # PIN the scale
fig.colorbar(im, ax=ax)
for i in range(N):
    for j in range(N):
        ax.text(j, i, f"{M[i][j]:.2f}", ha="center", va="center")
```

Three concrete choices worth pre-registering, because each is a way a heatmap can lie:

1. **Pin `vmin=0.0, vmax=1.0`.** Autoscaled colour is the classic heatmap deception: with a
   diagonal at 0.49 and off-diagonals at 0.01, autoscaling makes 0.01 render as a mid-tone and
   the figure reads as leakage that isn't there. Pin the scale to the rate's natural bounds.
2. **Annotate every cell with the number** (and ideally `k/n`). A reader must never have to
   infer a rate from a colour.
3. **Follow the v2.0 Phase-15 key decision:** the plotting module reads **only**
   `results/phase17_matrix.json`, never a checkpoint, and is guarded by the same AST-walk +
   fresh-interpreter probe that fails if `torch` lands in `sys.modules`. This keeps the figure
   regenerable from a fresh clone and keeps the plotting half inside the CPU-only suite.
   A committed PNG whose inputs are gitignored is an assertion, not evidence.

For Phase 18, a grouped bar chart of extraction rate by attack class, **with Wilson (or cluster-
bootstrap) error bars via `ax.errorbar` / `yerr=`**, and the no-adapter control drawn as a
reference line. All base matplotlib.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Hand-rolled Wilson interval (~8 lines) | `scipy.stats` / `statsmodels.stats.proportion.proportion_confint` | If the project ever needs a genuinely hard numerical routine — a GLM, an eigensolver, `scipy.optimize`, sparse linear algebra. Six lines of algebra is not that case. Reconsider only if Phase 19+ erasure needs constrained optimization. |
| Cluster bootstrap over questions | Wilson on the raw draw count | Wilson-on-draws is fine **as a labelled secondary number** showing the independence-assuming width. Never as the headline. |
| Holm–Bonferroni | Benjamini–Hochberg FDR | If the matrix ever grows to dozens of cells where FWER control is crushingly conservative. At 6–12 off-diagonal cells with known dependence, Holm is both simpler and better-justified. |
| Sign-flip paired permutation | McNemar exact (via `math.comb`) | If the pairing collapses to one binary outcome per question rather than a 9-draw rate. Both are dependency-free; permutation preserves more information. |
| matplotlib `imshow` | `seaborn.heatmap` | Never in this project — it drags in seaborn **and pandas** for ~15 lines, and pandas would be the single largest dependency in a package whose entire pitch is that it has almost none. |
| Templated attack families | LLM-generated paraphrases | Never — no budget, no network, non-reproducible, non-auditable. |
| Reuse `torch==2.7.*` | Bump to latest torch | Only if a v3.0 measurement hits an actual MPS bug. Bumping mid-milestone puts v3.0 numbers on a different runtime than the v2.0 artifacts they are compared against. |
| Keep the frozen tokenizer | Retrain | **Explicitly out of scope for v3.0** per PROJECT.md — it invalidates every published checkpoint and would confound the privacy milestone. |

## What NOT to Use

**This table is the point of this document. Every row is a plausible-looking addition that a
phase plan might reach for.**

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **`scipy`** | ~40–60 MB wheel and a new numpy-ABI coupling in `pyproject.toml`, CI, and the Makefile — bought for `binomtest`, `beta.ppf`, and `norm.ppf`, i.e. a hardcoded `z = 1.959963984540054` and ~20 lines of algebra. It would also **retroactively invalidate the committed D-12 zero-new-deps register** in `phase15_stats.py` ("scipy is NOT a dependency … and must not become one for a single correlation"), which is exactly the kind of quietly-abandoned discipline a reviewer at this bar notices. | Wilson (closed form), `math.lgamma` for any exact binomial tail, numpy for all resampling. |
| **`statsmodels`** (`proportion_confint`, `multipletests`, `mcnemar`) | Depends on numpy **+ scipy + pandas + patsy/formulaic**. It is the heaviest option on this list, bought for Holm (10 lines) and Wilson (8 lines). It also invites `Table2x2`-style API-shaped analysis over a design whose real problem is **clustering**, which `proportion_confint` cannot see and will silently under-cover. | The ~60-line `phase17_stats.py`, with the unit of analysis named in the pre-registration. |
| **`pandas`** | Would become the largest dependency in the project, to hold an N×N float matrix that is a nested `dict` in JSON and a `(4,4)` numpy array in memory. Also pulls a whole I/O and dtype surface into a package that currently reads exactly one artifact format. | `json` + `numpy` + the existing committed-artifact pattern. |
| **`seaborn`** | numpy + pandas + matplotlib for `heatmap()`. Its default autoscaled colormap is the exact failure mode named in Q4. And it would add import surface to the plotting module the AST-walk guard watches. | `plt.imshow(..., vmin=0, vmax=1)` + `ax.text`. |
| **`pingouin` / `researchpy` / any stats convenience wrapper** | scipy + pandas + statsmodels transitively, plus an opinionated API that hides which interval and which correction were used — the opposite of the project's "method string travels with the number" convention (`SPEARMAN_METHOD`, `CI_METHOD`). | Explicit pure functions with pinned method strings. |
| **Any external / hosted LLM for paraphrase or attack generation** | Zero budget, no network at runtime, privacy-by-design, and it makes the attack corpus non-reproducible — an attacker corpus nobody else can regenerate is not evidence. | Committed templated attack families via `render_family`. |
| **HuggingFace `transformers` / `peft` / `evaluate` / `lm-eval-harness`** | Excluded by design for the whole project. `lm-eval-harness` is the specific temptation for Phase 18 ("there's a benchmark for that") — it would drag in `transformers`, assume a HF model interface this project deliberately does not have, and replace a hand-built, auditable audit with an opaque one. | The existing `run_scored_recall` + `contains_value` scoring loop. |
| **`wandb` / Comet / Neptune** for the matrix sweep | Unchanged prohibition — network + account, violates offline/zero-budget/privacy. The N×N sweep is exactly the shape of run that tempts a tracker. | The existing CSV appender (`personacore.logging`) + one committed `results/phase17_matrix.json`. |
| **`tqdm`** as a real dependency for the N×N loop | Not in `pyproject.toml`. Where the repo uses it (`scripts/encode_corpus.py:78`, `scripts/prepare_dialog_corpus.py:95`) it is a **soft optional import inside a function** — `try: from tqdm import tqdm` / "only used if already importable". That pattern is the precedent for any nicety: never a hard pin. The existing per-question `print(f"[phase14_recall] {tier} …: {k}/{n}")` is already the progress indicator and doubles as a run log. | The existing print, or the same soft-optional pattern if a bar is genuinely wanted. |
| **`joblib` / `multiprocessing` to parallelize cells** | MPS is a single device; parallel processes contend for it and can OOM unified memory. Also destroys the per-question seeding determinism that makes every draw re-derivable from `SEED`. | Sequential cells. The compute budget is minutes-to-hours; it does not need to be less. |
| **A new checkpoint/serialization format for the N persona adapters** | `export_adapter` / `load_adapter` with the `weights_only=True` choke point and the fingerprint warning already exist and are already security-reviewed. N adapters is N files, not a new container. | `checkpoints/phase17_persona_{a,b,c,d}_adapter.pt`, same loader. |
| **Editing `scripts/phase15_stats.py` to add v3.0 statistics** | It carries a committed pre-registration for a *specific* Phase-15 claim, plus an explicit DO-NOT-UNIFY note about its `_spearman` divergence. Adding v3.0 functions there muddies which commit pre-registered what. | A new `phase17_stats.py` in the same shape; import a helper across if genuinely shared. |
| **`torch` bump, numpy bump, or any version change** | v3.0 compares new measurements against v2.0 artifacts (`persona_adapter.pt`, `convbase_slim.pt`, the 0.4921/0.3483/0/2430 numbers). A runtime change makes those comparisons cross-runtime for no benefit. | Freeze the environment for the milestone; bump at v4.0 open if at all. |

## Stack Patterns by Variant

**If a phase plan proposes adding a dependency:**
- Require it to state (a) the exact function needed, (b) the line count of the hand-rolled
  equivalent, and (c) why the `phase15_stats.py` zero-new-deps register does not apply.
- Because in this project the dependency count *is* part of the deliverable — "from scratch,
  numpy + torch + matplotlib" is a claim the `pyproject.toml` either supports or refutes.

**If the isolation matrix's off-diagonal comes back at exactly 0 (the likely case, given Phase 14's 0/2430):**
- Report the **rule-of-three upper bound** (`~3/n`) rather than "0%", and pre-register that
  wording before the run.
- Because a claim of a true zero is unsupportable from finite sampling, and this is the single
  most likely place for v3.0 to overclaim.

**If a cell's rate is high but the completion contains BOTH personas' values:**
- Route it through `find_contradictions` and report it as a contradiction event, descriptively,
  with no gate — the Phase-14/Phase-13 register.
- Because "adapter A emitted B's value" and "adapter A emitted both values, hedging" are
  different failures of isolation and collapsing them loses the interesting one.

**If Phase 16's prompt-stuffed condition beats the adapter-only condition (plausible, arguably expected):**
- That is a **result**, not a failure, and it must be reported unamended per the v2.0
  honest-negatives decision. The interesting number is the *gap* and what it costs — the prompt
  condition consumes context, leaks the fact to anyone who reads the prompt, and does not
  survive a wiped context; the adapter condition does. Pre-register that framing *before* the
  number, or it reads as a post-hoc rescue.
- No stack implication either way.

**If Phase 18 needs a live demo of an attack:**
- Reuse the Gradio panel and `render_context_dump`. Nothing new.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `numpy~=2.4` | `torch==2.7.*` | Already the shipped, CI-verified pairing. Every v3.0 statistic uses only `default_rng`, `quantile`, `argsort`, `corrcoef`, `maximum.accumulate` — all long-stable numpy 2.x API. |
| `matplotlib~=3.10` | `numpy~=2.4` | `imshow`/`colorbar`/`errorbar` are stable API. No pandas interop needed. |
| Python 3.11 | `math.comb`, `math.lgamma` | `math.comb` is 3.8+, `math.lgamma` is 2.6+. Both safely inside `requires-python = ">=3.10,<3.12"`. |
| `torch==2.7.*` | MPS fp32 | Unchanged: no AMP, no `GradScaler`, no `torch.compile` on MPS. `PYTORCH_ENABLE_MPS_FALLBACK=1` set before the first torch import, as `phase14_recall.py` already does — **carry this into every new v3.0 driver**, it is easy to forget in a fresh script. |
| `pytest~=9.0` | Pure-function stats module | New stats functions are torch-free and testable in the CPU-only suite, matching `tests/test_phase14_scoring.py`'s `importlib`-load-without-running pattern. |

## Integration Points (for the roadmapper)

| New v3.0 artifact | Attaches to | Notes |
|---|---|---|
| `scripts/phase16_control.py` | `load_adapted_model`, `build_recall_prompt(tok, q, persona=())` — signature verified at `src/personacore/dialogue/serialize.py:92`, `run_scored_recall` | **Widen the AST guard.** `tests/test_phase14_scoring.py:425::test_persona_argument_is_scoped_to_the_fairness_control` parses `phase14_recall.py`'s AST to pin that `persona=` is only used by the fairness control. Phase 16 legitimately needs `persona=` — the guard's allowlist must be widened **deliberately and visibly**, not deleted. That test is a structural invariant, and quietly removing it would be the exact "declared invariant silently becomes false" failure the v2.0 learnings named as the project's most recurring mistake. |
| `scripts/phase17_personas.py` | `teach_persona.py`, `export_adapter` | Generates N adversarial persona fact-sets + trains N adapters. Fact-set construction should reuse the Phase-14 gate discipline (base-failing probes, committed `FACTSET_GATE_SHA`) so off-diagonal misses are provably not just base behaviour. |
| `scripts/phase17_matrix.py` | `load_adapter_weights` (in-place swap), `stamp_seed_indices`, `run_scored_recall` | Writes `results/phase17_matrix.json`. Stamp question sets ONCE outside both loops (CR-01). |
| `scripts/phase17_stats.py` | numpy only | Wilson, cluster bootstrap, Holm, paired permutation. Pre-registration constants at module level, method strings pinned, both verdict branches authored before either is known to apply — the `phase15_stats.py` shape exactly. |
| `scripts/plot_phase17.py` | `results/phase17_matrix.json` only | AST-walk + fresh-interpreter no-torch guard, per the Phase-15 pattern. |
| `scripts/phase18_attacks.py` | `render_family`, `build_recall_prompt(persona=...)`, `adapter_disabled`, `draw_all` | Committed attack-family table. `assert_no_value_in_prompt` armed for paraphrase/role-play; a **separate, named** relaxed path for prefix injection that still proves no locked value is in the injected prefix. |
| `pyproject.toml` | — | **NO CHANGE.** If a plan touches it, escalate. |

## Sources

- `/Users/juliorcoelho/PersonaCore/pyproject.toml` — current dependency set verified directly:
  `numpy~=2.4`, `regex~=2026.5`; extras `cpu`=`torch==2.7.*`, `demo`=`gradio>=5,<6`+`matplotlib~=3.10`,
  `dev`=`pytest~=9.0`+`ruff~=0.15`+`tiktoken~=0.13`+`isort~=8.0`. **scipy, pandas, statsmodels,
  seaborn, and tqdm are absent.** (HIGH — read from the repo)
- `/Users/juliorcoelho/PersonaCore/scripts/phase15_stats.py` — the committed D-12 zero-new-deps
  register, the `_rank`/`spearman`/`permutation_p`/`bootstrap_ci` implementations these
  recommendations extend, the percentile-bootstrap small-n honesty note, and the
  method-string-travels-with-the-number convention. (HIGH — read from the repo)
- `/Users/juliorcoelho/PersonaCore/scripts/phase14_recall.py` — `run_scored_recall` cell shape,
  `stamp_seed_indices` / CR-01 pairing defect, `draw_all` per-draw seeding, `contains_value` /
  `find_contradictions` scoring, `assert_no_value_in_prompt`, `load_adapted_model(adapter_path=)`
  parameterization, the `persona=` AST guard, `PYTORCH_ENABLE_MPS_FALLBACK` ordering. (HIGH)
- `/Users/juliorcoelho/PersonaCore/src/personacore/lora/inject.py` — `load_adapter_weights`
  key+shape audit (the in-place adapter-swap seam), `adapter_disabled` exception-safe control,
  merged-state guards. (HIGH)
- `/Users/juliorcoelho/PersonaCore/.planning/PROJECT.md` — v3.0 scope, the Phase 16/17/18
  definitions, the pre-registration and honest-negatives key decisions, "compute is
  minutes-to-hours on the M3", tokenizer explicitly out of scope. (HIGH)
- Brown, Cai & DasGupta (2001), *Interval Estimation for a Binomial Proportion*, Statistical
  Science 16(2) — Wilson/Agresti-Coull recommended over Wald; Clopper-Pearson noted as
  needlessly conservative. (MEDIUM — standard result, cited from training knowledge, not
  re-fetched; the recommendation does not hinge on the citation, the `k=0 → [0,0]` Wald failure
  is verifiable by inspection.)
- Hanley & Lippman-Hand (1983), *If nothing goes wrong, is everything all right?*, JAMA — the
  rule of three (`3/n` upper bound after zero events). (MEDIUM — same caveat; `3/n` is
  derivable directly from `(1-p)^n = 0.05`.)
- Holm (1979), *A simple sequentially rejective multiple test procedure* — step-down FWER
  control valid under arbitrary dependence. (MEDIUM — same caveat.)

---
*Stack research for: v3.0 adversarial privacy audit on a shipped from-scratch LoRA/EWC LM*
*Researched: 2026-08-12*
*Bottom line: no new dependencies. ~60 lines of numpy is the entire stack delta.*
