# Pitfalls Research

**Domain:** Adding from-scratch training-time privacy mitigation (DP-SGD), adversarial
extraction-aware training, a privacy/utility frontier, and a relearning attack to an
already-shipped from-scratch LM stack — where the published numbers are the product.
**Researched:** 2026-08-20
**Confidence:** HIGH on codebase-specific findings (measured directly on this machine / read
from this repo), MEDIUM on DP-literature findings (canonical papers, multiple sources agreeing).

---

## Framing: what makes v4.0 different from v1.0–v3.0

Three milestones shipped numbers that were *measurements*. v4.0 ships a number that is a
**mathematical claim**: (ε, δ). A measurement can be wrong and later corrected by a dated
continuation — the project has done this and it reads as rigour. An (ε, δ) claim that is wrong is
a different category: it asserts a bound on what an adversary can learn, it will be read as a
guarantee, and the only honest correction is retraction. **ε is the first number this project has
ever published that cannot be softened by a scope limit.**

Second difference: every previous milestone measured something that already existed. v4.0 measures
things it *builds first*, in the same milestone. Phase 18's attack suite was pointed at a
pre-existing adapter; v4.0's frontier is pointed at adapters produced by code written in the same
milestone that scores them. The pre-registration discipline covers the threshold, not the
instrument. **An implementation defect in DP-SGD does not trip any gate in this repo** — it
produces a plausible loss curve, a plausible recall number, and a plausible ε.

Third: v3.0's retrospective records that remediation introduced defects at nearly the rate it
closed them, three rounds running. That was on **prose**. v4.0's remediation surface includes
noise scale, sensitivity, and sampling rate — quantities where a wrong value produces no error, no
NaN, and no visible symptom, only a number that is too good.

Every pitfall below is written against the mechanism that catches it, not the invariant that
declares it away — the v2.0 lesson ("a declared invariant is true the day it is written and
silently false after the next refactor").

**Provisional phase labels** used throughout (v4.0 opens at Phase 20; numbering is a suggestion
to the roadmap, the *attribution* is the point):

| Label | Phase |
|-------|-------|
| **P20** | Privacy unit + DP-SGD core + M3 cost calibration |
| **P21** | Accountant + ε reporting |
| **P22** | Adversarial extraction-aware training |
| **P23** | Retrained unmitigated control + frontier sweep + existence gate |
| **P24** | Relearning attack + never-taught baseline |
| **P25** | Synthesis, report, milestone close |

---

## Critical Pitfalls

### Group A — Ways a hand-rolled DP-SGD is silently non-private

Every pitfall in this group produces a training run that converges, a loss curve that looks
normal, and an ε that prints. None of them raises.

---

### P1: Clipping the batch gradient instead of the per-example gradient

**What goes wrong:**
`training/loop.py:165` already calls
`torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg.grad_clip)` — **after** the
accumulation loop, on the averaged gradient. I verified `clip_grad_norm_` skips frozen params
(`p.grad is None`), so this call already operates on exactly the 331,776 LoRA gradients and
nothing else. It looks like DP-SGD's clip. It is not: it bounds the norm of the *mean* gradient,
which bounds nothing about any individual example's contribution. Sensitivity is unbounded, the
noise is calibrated to a fiction, and there is no DP guarantee at all.

**Why it happens:**
The seam is already there and already named `grad_clip`. The cheapest possible "DP-SGD" is
`TrainConfig(grad_clip=C)` plus a noise line — a two-line diff that trains, converges, and is
completely non-private. This is the single highest-probability defect in the milestone, precisely
because the codebase makes the wrong version easier than the right one.

**How to avoid (mechanism):**
1. DP-SGD must **not** route through `_optimizer_step`. Give it its own step function. If it
   shares the function, the existing `clip_grad_norm_` line must be provably unreachable on the
   DP path — assert `train_cfg.grad_clip is None` under DP and raise otherwise.
2. **The test that catches it — the two-example sensitivity probe.** Build a batch of exactly 2
   examples, one crafted to produce an enormous gradient (a high-loss outlier) and one ordinary.
   Run the DP step with `sigma=0`. Assert that the resulting update norm is
   `<= 2*C/lot_size + tol`. Under per-example clipping this holds by construction; under batch
   clipping the outlier dominates and the bound fails. Then flip: scale the outlier's loss by
   1000× and assert **the update does not change** beyond tolerance. A batch clip moves; a
   per-example clip cannot.
3. **Structural guard:** an AST test asserting no module on the DP path calls
   `clip_grad_norm_`/`clip_grad_value_`. The repo already does exactly this shape of AST guard
   (`test_phase15_plots.py`'s no-checkpoint-import walk, `test_phase18_prereg.py`'s
   instrument-definition scan) — reuse the pattern, do not invent one.

**Warning signs:**
- The DP arm's loss curve is nearly indistinguishable from the control at small σ.
- Training time under "DP" is ~1× the non-private arm. Real per-example gradients cost
  meaningfully more; the milestone scope already anticipates ~B×. **If DP-SGD is not measurably
  slower, it is not computing per-example gradients.**
- `grad_clip` still appears in the DP arm's provenance line.

**Phase to address:** P20. This is the phase's central correctness obligation.

---

### P2: Noise added after averaging instead of before

**What goes wrong:**
The DP-SGD update is `(1/L) * (sum_i clip(g_i) + N(0, σ²C²I))` — noise added to the **sum**, then
divided by the lot size L. Writing `mean(clip(g_i)) + N(0, σ²C²I)` adds noise of the same absolute
scale to a quantity that is L× smaller, so the effective noise multiplier is **L×** what you
intended. That direction is conservative — over-noised, actually private, but the reported ε is
now wrong in the *pessimistic* direction and utility is destroyed for no reason, which will read
as "DP-SGD destroys the model" when it is a bug.

The dangerous inversion is the other one: `mean(clip(g_i) + N(0, σ²C²I)/L)` or dividing the noise
by L twice. Then σ_effective is L× too small, and **the reported ε is a fiction in the direction
that flatters the project.**

**Why it happens:**
`_optimizer_step` divides by `accum` inside the micro-batch loop (`loop.py:161`). Any DP code that
inherits that shape inherits an ambiguity about which quantity the noise is calibrated to.

**How to avoid (mechanism):**
Compute the **noisy sum** as one named intermediate, then divide exactly once, on one line, with a
comment naming L. Then:
**The test that catches it — the noise-scale calibration test.** With `C=1`, `L` fixed and the
model frozen (all `g_i` identical and known, e.g. a constant-gradient fake), run the DP step
`n=2000` times with independent noise and measure the empirical standard deviation of the update
per coordinate. Assert it matches `σ*C/L` within a stated tolerance. This is a **numeric** test
against a **closed form** — it catches an L-factor, an L²-factor, and a missing C. Note the
project already uses this exact shape: `estimate_fisher` is pinned against an analytic oracle.

**Warning signs:**
- Utility at "ε=8" is worse than utility at "ε=1" from a published reference at comparable scale.
- The measured update norm does not shrink as L grows at fixed σ.

**Phase to address:** P20.

---

### P3: Noise scaled to the wrong sensitivity

**What goes wrong:**
Under add/remove-one neighbouring, the L2 sensitivity of the clipped sum is `C`; under
replace-one it is `2C`. Micro-batch clipping (clipping the mean of a micro-batch rather than each
example) also has sensitivity `2C`, not `C` — a documented accounting bug in the literature. Using
`σC` where `2σC` is required halves the noise and makes the reported ε roughly a factor of two
optimistic, with no visible symptom.

**Why it happens:**
The neighbouring relation is a definition, not a code artifact. Nothing in a training loop records
which one you meant. Papers use both.

**How to avoid (mechanism):**
Write the neighbouring relation into the **same module-level constant block** as X and Y, as a
string, before any run:
`NEIGHBOURING = "add/remove one <unit>"` and `SENSITIVITY_MULTIPLIER = 1.0`. The accountant reads
these constants; the noise line reads these constants; the report imports and prints them. One
definition, three consumers — the project's "one definition per statistic" pattern
(`cluster_bootstrap`, `holm`, `wilson_upper_bound` each have exactly one definition repo-wide).
**The test:** assert the accountant call site and the noise call site read the *same* constant
object, via AST or via a shared-import test.

**Warning signs:**
- The report says "add/remove" and the accountant's docstring says "replace".
- Any micro-batching appears anywhere on the DP path without a `2C` in the noise line.

**Phase to address:** P20 (constant), P21 (accountant consumes it).

---

### P4: The frozen base leaks gradient signal

**What goes wrong:**
DP-SGD's guarantee covers what the *released artifact* reveals. The released artifact is
`persona_adapter.pt` — 331,776 LoRA params. `mark_only_lora_trainable` freezes the base, and
`teach_persona.py`'s canary already proves every frozen base param is bit-identical after
training. So the base is safe **as long as nothing else on the DP path touches it.** Three ways
it stops being safe:
1. Any statistic derived from base gradients (a Fisher estimate, a norm diagnostic, a
   layer-importance readout) computed on the persona data and then *published or used to select a
   hyperparameter* is an un-noised release of a function of the private data.
2. `merge_lora` / `merged_state_dict` fold the delta into base weights. A merged export is still
   only a function of the noised adapter (post-processing, safe) — **but only if it is computed
   after the last noisy step, never interleaved.**
3. The in-loop `val_loss` (`loop.py:414-431`) is computed on `DIALOG_VAL_BIN`, not persona data —
   safe today. It becomes an un-noised private release the moment anyone points an eval at the
   teaching bin.

**Why it happens:**
Post-processing immunity makes people relax. It only covers functions of the **noised output**.
Anything computed directly from the data is a separate mechanism that composes.

**How to avoid (mechanism):**
An explicit **release ledger**: a committed list of every quantity produced from persona data that
leaves the DP training process (checkpoint, CSV column, printed provenance line, gate input). Each
entry is marked `noised` / `post-processing-of-noised` / `PUBLIC-CORPUS-ONLY`. A test asserts the
CSV fieldnames of the DP arm's run are a subset of the ledger's allowed set. `loop.py` already
computes per-run fieldnames as `CSV_FIELDNAMES + sorted(extra_eval_fns)` — that set is
machine-readable, so the test is cheap.

**Warning signs:**
- Any `extra_eval_fns` entry on the DP arm reads the teaching bin.
- A "diagnostic" printed per step that involves the teaching data.

**Phase to address:** P20 (ledger), P23 (sweep must not add un-ledgered diagnostics).

---

### P5: Clipping/noising the wrong parameter group

**What goes wrong:**
`lora_state_dict` filters on the substring `"lora_"`. `mark_only_lora_trainable` sets
`requires_grad` on the same substring. If the DP step iterates `model.parameters()` (the shape
`_optimizer_step` uses today) it will silently include any parameter that becomes trainable later
— and, more subtly, it will iterate in a **different order** than a filtered list, which matters
if noise is drawn as one flat vector and split by shape.

The dangerous half is the reverse: clipping over a *subset* of the trainable params (e.g. only
`lora_A`, because `lora_B` starts at zero and someone "optimized" it away) leaves `lora_B`'s
gradient un-clipped and un-noised. `lora_B` starts at exactly zero (`layer.py:30`) and carries the
entire learned delta's output projection — un-noised `lora_B` is an un-noised release of the
adapter.

**Why it happens:**
Two independent name-filters (`"lora_" in name`) already exist in the codebase and a third will be
written. Three copies of a filter is three chances to drift.

**How to avoid (mechanism):**
One function, `dp_parameters(model) -> list[(name, param)]`, returning a **deterministically
ordered** list. Every DP consumer (per-example grads, clip, noise, optimizer construction) takes
that list. **The test:** assert
`{n for n, _ in dp_parameters(m)} == set(lora_state_dict(m))` and
`== {n for n, p in m.named_parameters() if p.requires_grad}` — a three-way equality that reddens
if any one filter drifts. Assert the count is exactly `r * n_layer * 18 * n_embd` (the closed-form
census `teach_persona.py:627` already uses), i.e. 331,776 at production shape.

**Warning signs:**
- Trainable census ≠ 331,776 on the DP arm.
- Noise tensor count ≠ parameter tensor count (36 wrappers × 2 = 72 tensors).

**Phase to address:** P20.

---

### P6: RNG reuse across steps — the noise repeats

**What goes wrong:**
Composition theorems require the per-step noise to be **independent**. If the noise generator is
re-seeded per step (e.g. `seed_everything(seed)` called inside a loop, or a generator constructed
inside the step function from a fixed seed), every step adds the *same* noise vector. That noise
cancels in expectation over the trajectory, the adversary can average it away, and the actual
privacy loss is unbounded while the accountant happily reports ε for T independent steps.

The run still converges — it converges *better* than a correct implementation, because correlated
noise is easier to optimize through. **This bug looks like success.**

**Why it happens:**
`seed_everything` exists and is called from `teach_persona.train_arm` (`teach_persona.py:610`) with
the comment that it "owns the training data order". A DP implementation that wants reproducible
noise will reach for it. `seeding.py`'s own docstring already says "Call this ONCE at the start of
a FRESH run" — the discipline is documented but not enforced.

**How to avoid (mechanism):**
**The test that catches it — the noise-independence test.** Capture the noise vectors from T=64
consecutive DP steps (a debug hook or an injected generator). Assert:
(a) no two are equal (`torch.equal` pairwise — the direct catch);
(b) the mean pairwise cosine similarity is within a stated band of zero.
(a) alone catches the re-seed bug outright. Add a **positive control**: deliberately re-seed and
watch the test fail before trusting it (v2.0's "guards are watched failing before being trusted").

**Warning signs:**
- The DP arm's final loss is *lower* than the non-private control at the same budget.
- Two runs at the same seed but different step counts share a noise prefix that they should not.

**Phase to address:** P20.

---

### P7: Noise drawn on the wrong device — and the CPU-only suite cannot see it

**What goes wrong (VERIFIED on this machine, torch 2.7.1, arm64, MPS available):**
CPU and MPS are **separate RNG streams**. Measured:

```
torch.manual_seed(5); torch.randn(4).to("mps")     -> [-0.487, -0.604, -0.558,  0.668]
torch.manual_seed(5); torch.randn(4, device="mps") -> [-0.219,  0.847, -1.185,  1.036]
```

Also measured: `torch.randn(n, device="mps", generator=<cpu generator>)` raises
`RuntimeError: Expected a 'mps' device type for generator but found 'cpu'`.

Consequences:
- A noise-generation test written on CPU (the only kind the CPU-only suite can run) proves nothing
  about the stream the M3 actually draws from.
- Drawing noise on CPU and moving it to MPS is *correct* but costs a host↔device copy per step per
  tensor (72 tensors × T steps) — a real slowdown that will be mis-attributed to per-example
  gradients during cost calibration.
- Passing a seeded CPU generator to a device draw does not silently fall back; it raises. That is
  the good case. The bad case is a code path that catches it and falls back to the *global* stream.

**Why it happens:**
The whole existing suite is CPU-only by design (845 tests, 1 CUDA-only skip, 1 MPS-guarded
module). Nothing about "the noise is right" is currently testable on the machine that trains.

**How to avoid (mechanism):**
1. Decide the noise device **once**, in a constant, and record it in the run provenance line
   alongside `device=` (the line `teach_persona.py:735-744` already prints).
2. Extend `tests/test_mps_smoke.py` — the repo's only MPS-guarded module, already structured as
   `pytestmark = skipif(not mps.is_available())` so CPU CI **skips rather than errors** — with the
   DP noise-scale test (P2) and the noise-independence test (P6) run on `device="mps"`. This is the
   correct home: the pattern, the skip semantics and the "if this fails on the M3 while CPU passes,
   fall back to CPU" escape hatch all already exist there.
3. Because CI can never run it, the M3 run of `test_mps_smoke.py` becomes a **named, logged
   precondition** of any DP training run — not a note. v1.0's lesson: "a warning with a deadline
   needs an owner/gate, not just a note." Make the DP driver refuse to start unless a dated
   `results/dp_mps_smoke.json` recording a green MPS DP-smoke exists for the current git SHA.

**Warning signs:**
- CPU suite green, and nobody has run the MPS module since the DP code landed.
- Provenance line does not name the noise device.

**Phase to address:** P20, with the driver precondition landing in P23 (the sweep is what runs
many arms unattended).

---

### P8: Checkpoint/resume loses the noise RNG — ε is wrong on resume (VERIFIED LIVE DEFECT)

**What goes wrong:**
`checkpoint.py:102-108` saves `rng = {python, numpy, torch, cuda}`. `load_checkpoint:138-144`
restores the same four. **There is no `mps` slot.** I confirmed `grep -n mps checkpoint.py
seeding.py` returns nothing, and measured that restoring the saved CPU torch state does **not**
reproduce an MPS draw:

```
CPU rng state restore reproduces MPS draw: False
torch.mps.get_rng_state / set_rng_state exist and DO round-trip correctly
```

Why this has never bitten: I verified `nn.Dropout(0.0)` consumes **no** torch RNG, and the data
path (`get_batch_memmap_masked`) draws via `np.random.randint` — numpy, which *is* saved. **Today's
training loop consumes zero device RNG.** DP-SGD is the first per-step consumer of device RNG in
the project's history. **v4.0 activates a dormant checkpoint defect.**

Two failure modes on resume, both silent:
- Noise restarts from an uncontrolled state → the resumed trajectory is not the uninterrupted one
  (breaks the project's bit-identical-resume contract, TRAIN-04).
- Worse: if resume re-seeds (rather than restores), the post-resume noise **replays the pre-resume
  noise stream** — P6's non-independence, introduced by a crash rather than by a bug.

Separately, the **accountant step count** must also survive resume. Resuming from step 120 of 200
and running the accountant for 200 steps under-reports; running it for 320 over-reports. The
checkpoint is an open dict (`**extra`) so there is a slot for it; nothing forces its use.

**How to avoid (mechanism):**
1. Add `"mps": torch.mps.get_rng_state() if torch.backends.mps.is_available() else None` to the
   `rng` dict, and the matching restore. Backward compatible via `.get("mps")`, exactly as the
   `scaler` slot was added (`checkpoint.py:135`). **Do this in P20, before any DP run** — it is a
   five-line change now and a re-run of the whole sweep later.
2. Carry `dp_state = {"steps_accounted": int, "sigma": float, "C": float, "lot_size": int,
   "q": float, "seed": int}` through `checkpoint_extra` (the seam already exists and already
   carries fisher/theta_star).
3. **The test:** save → kill → resume, and assert the **accountant's** reported ε for the
   kill+resume run is bit-identical to the ε for the uninterrupted run. This is the resume-curve
   test (`test_resume_curve.py`) pointed at ε instead of loss. It runs on CPU if the accountant is
   torch-free — which it should be (stdlib/numpy only, `erasure_gate.py` precedent).
4. **Make the wrong answer impossible to publish:** the accountant reads `steps_accounted` from
   the checkpoint, never from a config or a loop variable. If it is absent, raise.

**Warning signs:**
- Any DP run that was interrupted, at all.
- ε printed by a driver that took `max_steps` as an argument.

**Phase to address:** P20 (checkpoint slot), P21 (accountant state).

---

### P9: The per-example gradient path is silently a batch path

**What goes wrong:**
`torch.func.vmap(grad(...))` is the efficient per-example route. **I verified it works on MPS in
torch 2.7.1** (`vmap(grad(loss_fn))` over a 5-example batch returned per-sample weight grads of
shape `(5, 4, 8)`). But `vmap` over a function that internally reduces across the batch dimension —
or over the model's own `forward(idx, targets)` which computes a **mean-over-tokens CE** — returns
gradients of the *mean*, not of the example. Because LoRA is six pure `nn.Linear` projections, a
closed-form per-example norm is also available (activation-outer-product structure), and that path
has its own failure: it is *derived*, so an algebra slip produces plausible norms.

**Why it happens:**
`estimate_fisher` already solved this correctly with a strict batch=1 loop
(`fisher.py:110-121`, "squaring a gradient aggregated over a batch > 1 is NOT the Fisher — the
cross-terms do not vanish"). The same class of error, the same module shape, one milestone later.

**How to avoid (mechanism):**
**Three-way equivalence test.** For a fixed 4-example batch, compute per-example gradients by
(a) the strict batch=1 autograd loop — the slow oracle, the shape `estimate_fisher` already uses;
(b) `vmap(grad(...))`;
(c) the closed-form/hooked path if one is implemented.
Assert all three agree to fp32 tolerance, **and** assert `sum_i g_i / B` equals the ordinary
batched `.backward()` gradient. That last assertion is the one that catches a `vmap` over a
batch-reducing loss: it will be off by exactly a factor of B.

Keep (a) permanently as the fallback. The milestone scope explicitly plans to *measure* the
naive-vs-closed-form cost; the naive path must therefore remain correct and callable, not be
deleted after the measurement.

**Warning signs:**
- Per-example gradient norms are all nearly identical (a mean gradient broadcast B ways).
- The closed-form path is faster than expected by more than an order of magnitude.

**Phase to address:** P20.

---

### Group B — Ways a reported ε is wrong

---

### P10: The privacy unit is undefined by the data path (THE structural pitfall of this milestone)

**What goes wrong:**
There is no "example" in this codebase. Measured from `results/phase14_teaching_run.log`:

```
real: 220 episodes, 20,036 tokens (10,018 teaching + 10,018 replay),
      episode length mean 45.5 [24, 84]
BLOCK_SIZE = 256, BATCH_SIZE = 8, MAX_STEPS = 200
```

`get_batch_memmap_masked` draws `batch_size` **random contiguous 256-token windows** from the flat
concatenated bin, via `np.random.randint`, **with replacement** (I measured 48/64 unique starts in
a toy draw over 100 offsets). Therefore:

- **A window is not an example.** At mean episode length 45.5 and block 256, **one window spans
  ~5.6 episodes.** Clipping "per window" bounds the influence of a *random overlapping slice*, not
  of anything a person owns.
- **A fact is not an episode.** 220 episodes / 10 facts = **22 episodes per fact**. The claim the
  report makes is about *facts*. Record-level (ε, δ) extended to a group of k records costs
  **k·ε** under group privacy. At k=22 an ε of 3 becomes 66 — vacuous. *(Pin the exact group
  formula from a source at write time; do not retype it from memory — see P28.)*
- **Overlapping windows compound it.** Adjacent start offsets share up to 255 tokens, so a single
  episode is reachable from ~256 distinct windows. Any "sampling rate" computed as
  `batch_size / n_windows` describes windows, not the data.
- **Replay dilutes the denominator in the flattering direction.** The production `real` arm ran
  `replay_ratio=1.0`: half the bin is PersonaChat — *other people's public dialogue*. Computing
  `q = L/N` with N counting replay tokens gives a smaller q and therefore a **smaller, better-looking
  ε than the persona data actually receives.**

**Why it happens:**
The nanoGPT memmap idiom is the right design for pretraining and is load-bearing everywhere else in
the repo. It has no concept of a record. Nothing about it announces that DP is inapplicable to it
as-is.

**How to avoid (mechanism):**
1. **Commit the unit as a string constant before anything else in the milestone**, in the same
   module as X, Y, and the neighbouring relation:
   `PRIVACY_UNIT = "one taught fact (all 22 episodes rendering it)"` — or `"one episode"`, if the
   milestone chooses the weaker unit *and says so in the headline*. The unit is what the ε means;
   choosing it after seeing ε is the same offence as choosing a threshold after seeing the data.
2. **Build a DP-specific data path.** Sampling must be over *units*, not offsets: an
   episode-indexed (or fact-indexed) structure with explicit boundaries. Keep the memmap for the
   public-corpus replay stream; the persona stream needs its own loader. This is real work and it
   belongs in P20, not in a later "fix".
3. **The test:** given the bin and the episode index, assert every drawn lot is a set of **whole
   units**, no unit appears twice within one lot, and no token outside the sampled units enters the
   loss. The mask (`mask_fraction ~0.40`) makes "which tokens were scored" checkable directly.
4. **Report `PRIVACY_UNIT` in the same sentence as ε, always.** A test asserting the report string
   containing "ε" also contains the unit constant.

**Warning signs:**
- Anyone says "N = number of windows".
- ε is reported without a unit named in the same sentence.
- The replay arm and the non-replay arm report different ε at identical σ, C, L, T.

**Phase to address:** P20. **This must be settled before any DP arm trains**, because it
determines the loader, the lot construction, and every ε in the milestone.

---

### P11: Poisson-subsampling accounting over a non-Poisson sampler

**What goes wrong:**
Standard subsampled-Gaussian accountants (RDP / moments / PRV) assume **Poisson subsampling**:
each record included independently with probability q, so lot size is random. This codebase samples
**fixed-size, with replacement, over overlapping windows** — further from Poisson than the usual
shuffling mismatch. Reporting a Poisson-accounted ε over a shuffled fixed-size sampler is a known,
named, published gap; recent work shows the shuffling guarantee is *substantially weaker* than
the Poisson number implies, especially at small ε — exactly the regime a portfolio wants to claim.

**How to avoid (mechanism):**
1. **Implement Poisson sampling**, since P10 already forces a new loader. Draw each unit
   independently with probability q; accept the variable lot size (divide by the *expected* lot
   size L = qN, a fixed constant — never by the realized count, which is itself data-dependent).
   Dividing by the realized lot size is a second, subtler leak.
2. **The test:** over 10,000 simulated lots assert the realized-size distribution matches
   Binomial(N, q) — mean ≈ qN and variance ≈ Nq(1−q). A fixed-size sampler has variance 0 and fails
   immediately. A with-replacement sampler fails the duplicate check.
3. If Poisson is rejected for any reason, the report must state the sampler and state that the ε
   is **an assumption-violating estimate, not a bound** — and then it is not a formal claim and
   should not be presented as one.

**Warning signs:**
- Every lot has exactly the same size.
- The word "batch_size" appears anywhere on the DP path.

**Phase to address:** P20 (sampler), P21 (accountant assumption pinned to it).

---

### P12: Gradient accumulation silently changes the lot

**What goes wrong:**
`_optimizer_step` accumulates `grad_accum_steps` micro-batches then steps once. Under DP the
**lot** is the unit of noise and of the sampling rate: one noise draw, one q, per *optimizer step*.
If accumulation is used to reach a large lot but the accountant is handed `batch_size` instead of
`batch_size * grad_accum_steps`, q is under-reported by exactly `grad_accum_steps` — ε too small.
If noise is added per micro-batch instead of per lot, the effective σ is `sqrt(accum)×` too large
(over-noised) or the sensitivity is wrong (under-noised), depending on where the clip sits.

The M3 will *force* accumulation: DP-SGD wants a large lot for amplification, per-example gradients
want a small micro-batch for memory. This pitfall is not hypothetical for this project — it is the
expected configuration.

**How to avoid (mechanism):**
The accountant takes a single `lot_size` argument and the training driver **computes it in one
place** as `batch_size * grad_accum_steps`, then passes the same value to the sampler, the noise
divisor and the accountant. **The test:** two runs — (`batch=8, accum=4`) and (`batch=32,
accum=1`) — at identical σ, C, T must produce **identical reported ε**. If they differ, the lot
plumbing is wrong. This is the direct DP analogue of the existing
`test_grad_accum_equivalent_to_big_batch` (`loop.py:319` documents that fixture), so the shape is
already familiar to the suite.

**Warning signs:**
- `grad_accum_steps` appears in the training config but not in the accountant call.
- ε changes when you change accumulation at fixed effective lot size.

**Phase to address:** P20 / P21.

---

### P13: The sweep itself composes — and the reported ε is per-point

**What goes wrong:**
The frontier trains N adapters on the **same persona data**, then the existence gate **selects**
one. Two distinct costs are routinely omitted:
1. **Composition over the sweep.** N independent DP runs on the same data compose. If each point
   is ε_i-DP, the *release of all N adapters* is bounded by a composition of the N mechanisms, not
   by max(ε_i). The milestone publishes the whole curve, so the whole curve is the release.
2. **Selection cost.** Choosing the best point using the private data is a data-dependent
   selection; Papernot & Steinke formalize the RDP cost of DP hyperparameter tuning and it is *not
   free*. "We swept ε ∈ {0.5, 1, 2, 4, 8} and report the ε=1 point" is a claim about a mechanism
   nobody accounted.

**How to avoid (mechanism):**
Pick one honest framing and commit it in code before the sweep:
- **(a) Per-point claim, explicitly scoped.** "Each point is ε_i-DP *for that adapter in
  isolation*; the curve as a released collection is not accounted, and the selected point's ε does
  not cover the selection." Cheap, honest, and defensible — and it must appear beside the headline,
  not in a footnote.
- **(b) Accounted total.** Report both `epsilon_point` and `epsilon_curve_total` and let the
  headline carry whichever the claim actually rests on.
- Never (c): report the selected point's ε as the milestone's privacy guarantee.

**The mechanism:** make it impossible to print a bare ε. The reporting helper takes
`(epsilon_point, epsilon_curve_total, selection_accounted: bool)` as **required keyword-only**
arguments and refuses to render without all three — the `erasure_succeeded(*, ...)` keyword-only
pattern (`erasure_gate.py:200`), applied to the number rather than to the verdict. A test asserts
no module formats an ε into a string outside that helper (AST scan — the
`test_phase18_prereg.py` instrument-location pattern).

**Warning signs:**
- The report's abstract contains one ε and the results table contains five.
- "We chose ε=1 because it had the best recall."

**Phase to address:** P21 (framing constant), P23 (sweep obeys it), P25 (report enforces it).

---

### P14: δ chosen wrong relative to dataset size

**What goes wrong:**
The convention is δ ≪ 1/N, commonly δ = 1/N^1.1 or smaller, because δ ≈ 1/N admits a mechanism
that publishes a random record verbatim and is still "(ε, δ)-DP". With N = 220 units, 1/N = 0.0045,
and a habitually-copied δ = 1e-5 is *fine*; but a δ = 1e-3 (also common in papers with N in the
millions) would be **catastrophically loose here** — it permits releasing roughly one unit in a
thousand, against a dataset of 220. The number looks conventional and is nonsense at this N.

Compounding: δ is defined per the **unit chosen in P10**. If the unit is the fact (N=10), δ must be
smaller still, and N=10 is small enough that (ε, δ)-DP is arguably not the right vocabulary at all.

**How to avoid (mechanism):**
Compute δ **from N** in code, never as a literal: `DELTA = 1.0 / (N_UNITS ** 1.1)`, with `N_UNITS`
read from the committed unit index rather than typed. A test asserts `DELTA * N_UNITS < 0.01` and
raises with a message naming both. Report N alongside δ everywhere.

**Warning signs:**
- δ is a round literal copied from a paper.
- δ is unchanged between the fact-unit and episode-unit framings.

**Phase to address:** P21.

---

### P15: ε reported for the adapter while something else touched the data

**What goes wrong:**
The (ε, δ) claim covers a specific release. Things in this repo that are also functions of the
persona data and are *not* the noised adapter:
- `results/*.csv` — the in-loop training-loss column is a per-step function of the persona batch.
  **The published loss curve is an un-noised release.** (The `val_loss` column reads the public
  dialogue corpus and is fine.)
- `final_train_loss` and `mask_fraction` in the provenance line (`teach_persona.py:735-744`).
- The teaching bins themselves, and `results/phase14_factset_report.md`.
- The tokenizer, if it were ever retrained on persona data (explicitly deferred — keep it that way,
  and note that this is now a *privacy* reason and not only a cost reason).
- Any hyperparameter (LR, steps, σ) chosen by looking at persona-data results.

**How to avoid (mechanism):**
The **release ledger** from P4, extended: every artifact the DP arm writes gets a ledger entry.
A test enumerates files written under the DP arm's output prefix and asserts each is ledgered.
For the train-loss curve specifically, the honest options are: (i) suppress it for the DP arm,
(ii) publish it and state plainly that the curve is outside the guarantee, or (iii) noise it. (ii)
is the project's style and costs nothing — but it must be *stated*, because a reader will assume
the guarantee covers everything the milestone published.

**Warning signs:**
- The report shows a DP training curve next to an ε with no caveat.
- Anyone tuned LR by looking at the DP arm's recall.

**Phase to address:** P21 (ledger), P25 (report).

---

### Group C — Ways a privacy/utility frontier misleads

---

### P16: Unmatched budget across sweep points — including the token budget

**What goes wrong:**
The milestone already knows to retrain the unmitigated control at identical budget and seed
protocol. **What else must be matched**, and is easy to miss:

| Must match | Why it silently differs |
|---|---|
| **Scored tokens, not steps** | `mask_fraction ≈ 0.40`: ~60% of tokens are `-100`. Matching steps matches wall clock; the learning signal is scored tokens. |
| **The base checkpoint fingerprint** | `load_adapter` *warns and loads* on fingerprint mismatch (D-02, `checkpoint.py:253`). A curve point trained on a different base produces no error. |
| **`LoRAConfig` (r, alpha, dropout)** | `alpha` is shape-invisible; `load_adapter_weights`'s scale audit only fires when a `lora_config` is present. |
| **Seed *protocol*, not seed value** | `teach_persona` seeds three times (bins build, GPT/LoRA init, TrainConfig) and comments that ordering is load-bearing. A DP arm that inserts an RNG consumer before the model build shifts the init draw for that point only. |
| **Replay ratio** | `REPLAY_RATIO=0.0` vs the production `real` arm's `1.0` halves the corpus composition. |
| **Effective LR under clipping** | Per-example clipping to C shrinks gradient magnitude; at fixed LR the DP arm takes systematically smaller steps. "DP hurts recall" may be "the DP arm had a 10× smaller effective LR". |
| **Attack-arm token inflation (MEASURED)** | Through the frozen 547-live-id tokenizer, perturbed text inflates. Measured on the same 51-character sentence: clean 35 tokens (0.686 tok/char), uppercased 49 tokens (0.961 tok/char) — **1.40×**; role-play framing 1.17×. **Attack intensity mechanically changes the token budget per window.** A frontier swept on "intensity" is also, unintentionally, swept on budget. |

**How to avoid (mechanism):**
A committed `ArmSpec` dataclass carrying every one of the above, plus a `spec_digest()` (a hash over
the fields). Every curve point records its digest into its checkpoint via `checkpoint_extra`, and
into its results JSON. **The gate driver refuses to evaluate a frontier whose points' digests
differ in any field outside the declared sweep axis.** That converts "we matched the budget" from a
sentence into a check — the exact conversion v2.0 named as its most valuable pattern.

For the token-inflation confound specifically: report **scored-token count per arm** as a column of
the frontier table, and if intensity moves it, the sweep must either equalize scored tokens or
report intensity-vs-tokens as a declared confound. Do not let it stay invisible.

**Warning signs:**
- The frontier table has no denominator column.
- Two points differ in `final_train_loss` by more than the seed-to-seed noise floor at the same
  nominal budget.

**Phase to address:** P23 (owns matching), P22 (must measure its own token inflation).

---

### P17: Reading an existence gate as a typical-case result

**What goes wrong:**
`∃ a point with extraction ≤ X AND recall ≥ Y` is a **max over N noisy measurements**. Its
sampling distribution is not the distribution of a single point. Two independent failures:
1. **Multiplicity.** With N sweep points, the probability that *some* point clears both thresholds
   by measurement noise alone grows with N. The project already owns the fix — `holm` has exactly
   one definition repo-wide and Phase 18 used it across 4 attack families at p = 0.0078125.
2. **Prose drift.** "There exists a configuration where mitigation works" becomes "mitigation
   works" by the third paragraph. v3.0's N1 defect ("the three reductions"; there were two) was
   exactly this class — a count restated slightly wrong in dense correction prose.

**How to avoid (mechanism):**
1. **Require replication of the winning point.** The ∃ is provisional until the surviving point is
   re-trained at a second seed and clears both thresholds again. This is Phase 17's
   worst-pair-replicated-at-k=3 pattern; the gate should *require* it, not report it. Commit that
   requirement in the gate constant before the sweep.
2. **Bound the selection.** Report the winning point's recall with its one-sided Wilson **lower**
   bound and its extraction with its Wilson **upper** bound — `wilson_upper_bound` already exists
   in `erasure_gate.py` and the lower bound is already derived there via the complement
   (`erasure_gate.py:186`). Gate on the bounds, not the point estimates. Questions as the unit, never
   draws (the clustering discipline `erasure_gate.py` already fixes).
3. **A canonical claim string.** The gate returns a fixed sentence containing "at least one
   configuration of N swept", and every document quotes that string. A test asserts the string
   appears verbatim in README, `docs/REPORT.md` and the results artifact — **whitespace-normalized**
   (see P28).

**Warning signs:**
- A headline sentence about "mitigation" with no "at least one of N".
- The winning point sits at a sweep endpoint (suggesting the true optimum is outside the swept
  range and the ∃ is a budget artifact — the exact risk the milestone's Z-is-a-resource-parameter
  decision was written to prevent).

**Phase to address:** P23 (gate), P25 (prose).

---

### P18: Post-hoc sweep-point cherry-picking, and the axis that moved without being swept

**What goes wrong:**
Two shapes:
- **Post hoc selection**: the gate is ∃, so *any* point clearing it passes. If the sweep is
  extended after seeing near-misses ("let's add ε=6 between 4 and 8"), the added point was chosen
  *because* the neighbourhood looked promising. That is a threshold moved after seeing data,
  wearing a resource-parameter costume. The milestone's own kickoff decision draws the line: Z is a
  resource parameter set *from the DP-SGD cost measurement*, i.e. **before any curve point exists.**
  Extending Z after points exist crosses it.
- **A second axis moved silently**: σ is the declared axis, but reaching a target ε at a given σ
  also requires a particular T and q. Changing T to hit a round ε number changes the training
  budget — so the "ε axis" is secretly a joint (ε, budget) axis and the frontier is not a frontier.

**How to avoid (mechanism):**
1. **Commit the exact sweep grid as a tuple literal** before the first point runs, alongside X and
   Y. The driver iterates that tuple and refuses any point not in it. Extending it later is then a
   visible, dated commit that post-dates results — discoverable rather than deniable. This is
   `ASR_RUNGS = (1, 4, 16, K)` (`phase18_extraction.py:98`) applied to the sweep.
2. **Hold T and q fixed across the grid; vary only σ.** Then ε is a pure function of σ and the
   budget is constant by construction. If T must vary, declare a two-dimensional sweep and say so.
3. Record `spec_digest` per point (P16) so a moved axis is machine-detectable.

**Warning signs:**
- The grid in the driver has more entries than the grid in the plan.
- Points have different T.

**Phase to address:** P23.

---

### Group D — Ways a relearning attack gives a false PASS

---

### P19: No never-taught baseline at identical budget — "did not recover" is unfalsifiable

**What goes wrong:**
"The mitigated adapter did not recover the fact within budget Z" is worthless without knowing
whether Z can teach the fact *at all*. If a fresh, never-taught adapter also fails to reach the
recall threshold within Z, then Z is simply too small and the result measures the budget, not the
mitigation. This is the exact structure of Phase 18's `erasure_is_worth_attempting` precondition —
an extraction result is meaningless without the same-budget no-adapter control — one milestone
later, in a new costume.

The milestone scope already names the fresh-adapter baseline. The pitfall is running it at a
*different* budget, or running it once as a spot check rather than as a gate input.

**How to avoid (mechanism):**
Make the baseline a **required argument of the gate function**, keyword-only, with no default —
`relearning_gate(*, mitigated_recall, mitigated_n, fresh_recall, fresh_n, budget_z, ...)`. A gate
that cannot be called without the baseline cannot be evaluated without it. Add an explicit
`INCONCLUSIVE` branch: if the fresh baseline itself fails to clear the recall threshold within Z,
the verdict is INCONCLUSIVE (budget too small), **never PASS**. `erasure_succeeded` already
establishes INCONCLUSIVE-takes-precedence-over-FAILURE and already has a
"zero result without corroborating NLL is INCONCLUSIVE" branch — reuse both.

**Warning signs:**
- The fresh baseline ran at a different step count, LR or seed protocol.
- The report says "did not recover" without "while a never-taught adapter reached R at the same
  budget".

**Phase to address:** P24.

---

### P20-p: Attacker budget too small to be meaningful

**What goes wrong:**
A relearning attacker given 20 steps will fail against anything. The gate then certifies
robustness against an attacker nobody would call an attacker. Z must be large enough that the
*fresh* baseline comfortably clears the recall threshold (P19), and ideally large enough that the
**unmitigated control** also recovers — otherwise the attack cannot distinguish arms.

**How to avoid (mechanism):**
Calibrate Z **from the two controls, before the mitigated arm is attacked**: run the attack against
(i) a fresh never-taught adapter and (ii) the retrained unmitigated control. Set Z = the smallest
budget at which both clear the recall threshold, then **commit Z** and only then attack the
mitigated arms. This is a resource parameter measured before pre-registration — exactly the
distinction the milestone's kickoff decision licenses (Z measured, X and Y locked).
A three-rung budget ladder (`ASR_RUNGS` precedent) makes the budget-dependence visible rather than
a single point.

**Warning signs:**
- Z was picked because it was affordable.
- The unmitigated control does not recover at Z.

**Phase to address:** P24.

---

### P21-p: Attacker data distribution mismatched — and syntax matters more than topic

**What goes wrong:**
If the relearning corpus is drawn from the same generator as the teaching corpus, the attack is
"retrain on the original data" — trivially strong, and it measures nothing about whether the
information survived. If it is drawn from an unrelated distribution, the attack is weak and the
PASS is free.

The literature is specific and counter-intuitive here: benign relearning succeeds with small,
*loosely related* data, and recent work finds **syntactic similarity, not topical overlap**, is the
primary driver of recovery. An attacker corpus matched on topic but not on the Q/A syntactic shape
(`encode_dialogue`'s `<|user|>`/`<|assistant|>` role-token rendering) may under-recover for reasons
that have nothing to do with the mitigation.

**How to avoid (mechanism):**
Sweep the attacker corpus as a declared axis with at least three rungs, committed before the attack:
(a) **held-out families** — the F3/F7/F8 split already exists in `phase14_factset.py` and is already
the project's paraphrase axis; (b) **syntax-matched, content-disjoint** — same role-token dialogue
shape, different facts; (c) **content-adjacent, syntax-mismatched** — the same facts in prose.
Report all three. If only (a) recovers, the "attack" is memorization of the fixture.

**Warning signs:**
- One attacker corpus, no ladder.
- The attacker corpus and the teaching corpus share a build function.

**Phase to address:** P24 (corpus ladder), with the fixture split reused from Phase 14/16.

---

### P22-p: Measuring recovery with the same fixture the mitigation was trained against

**What goes wrong:**
The adversarial arm (P22) is *trained on* the Phase 18 attack suite. Measuring its post-relearning
extraction with that same suite measures training-set performance. The number will be excellent and
will not generalize — which the milestone already names as its declared open question, but the
*gate* must not consume the contaminated instrument.

The same trap applies to the frontier's extraction axis: if extraction is scored with A1/A2/A3 and
the adversarial arm trained on A1/A2/A3, `extraction ≤ X` is nearly free for that arm and the
frontier compares an arm on its training set against an arm on a test set.

**How to avoid (mechanism):**
Split the attack suite into **TRAIN** and **HELD-OUT** partitions, committed as module constants
before any adversarial training runs, with **no attack family in both**. Phase 18 already
established the tier discipline: `GATED_TIER = "core_held_out"` and
`REPORTED_TIER = "core_taught"` (`phase18_extraction.py:173-175`) — a gated tier and a reported
tier, structurally separated. Reuse that exact split, and add a test asserting the two partitions
are disjoint and that the training driver reads only TRAIN while the scorer reads only HELD-OUT
(AST/import scan, `test_phase18_prereg.py` pattern).

Consider also holding out one attack *family* entirely (never used in training, only in scoring) so
generalization to a genuinely unseen attack shape has a reading rather than only a caveat.

**Warning signs:**
- The DP arm and the adversarial arm are scored by different attack sets.
- The adversarial arm's extraction is dramatically better than the DP arm's at similar recall.

**Phase to address:** P22 (partition committed), P23 (scorer reads held-out only).

---

### P23-p: Confusing suppression with removal

**What goes wrong:**
A mitigation can make a fact unreachable by the current prompt distribution while leaving it fully
present in the weights. Under a relearning attack the difference is exactly the cost-to-recovery
*curve shape*: if the mitigated adapter recovers on the same trajectory as a never-taught fresh
adapter, the information was removed; if it recovers **faster**, it was suppressed and the residual
is still there. The milestone already frames this correctly (cost curve *qualifies* the gate, does
not replace it — the v3.0 "an instrument qualifies a gate's reading, it does not replace it"
pattern).

The failure is measuring only the **endpoint**. Endpoint-only, suppression and removal are
indistinguishable: both end at the same recall after enough steps.

**How to avoid (mechanism):**
Record recall at **every** relearning checkpoint (a rung ladder, not two endpoints), for all three
arms — fresh, unmitigated, mitigated — on a shared x-axis of *scored tokens* (not steps, per P16).
Publish the three curves. Commit in advance what "≈ fresh" means numerically (e.g. the mitigated
curve stays within k=2× the fresh-vs-fresh seed-to-seed band, the project's standing margin
discipline) and report it descriptively, since n will not support gating it.

**Warning signs:**
- Only pre- and post-attack recall exist.
- The mitigated arm's recovery at the *first* rung already exceeds fresh's.

**Phase to address:** P24.

---

### Group E — The Phase 19 failure mode: a defense that works by destroying the model

---

### P24: The existence gate as written has no capability condition — this is the loophole

**What goes wrong:**
Phase 19's gate had **three** conditions: (a) target forgotten, (b) non-targets preserved,
**(c) capability preserved** — dialogue PPL and retention PPL within k=2× their noise floors.
Condition (c) exists, in `erasure_gate.py`'s own words, "because (a) and (b) can BOTH be satisfied
by a model that has been degraded into uselessness."

v4.0's gate as stated in PROJECT.md has **two**: `extraction ≤ X AND recall ≥ Y`. A model that
memorizes the taught templates while its general dialogue collapses satisfies both. **That is
precisely the Phase 19 failure, and the current gate cannot see it.**

Additional loopholes in the two-condition form:

| Loophole | Why it passes | Close it with |
|---|---|---|
| **No capability floor** | Taught-template recall survives while free-running dialogue dies (Phase 19: four of seven non-targets at *total generation loss*). | Port condition (c) verbatim: `masked_dialogue_ppl ≤ 4.5733 + 2×floor` and `retention_ppl ≤ 3.891140 + 2×0.068930`, importing the constants from `erasure_gate.py` rather than retyping (they are already committed there, lines 75-81). |
| **Recall measured on taught templates only** | v2.0 published *two* numbers (taught 0.4921 / held-out 0.3483). Gating taught-only rewards memorization over generalization — the wrong direction for a personalization claim. | Y is a pair: `Y_taught` and `Y_heldout`, both required. |
| **Extraction ≤ X achieved by breaking the scorer** | A degenerate or refusing generator scores 0 extraction. Phase 19's co-headline is that two instruments disagreed on the same weights. | Import `zero_results_have_nll` semantics: extraction at or near zero **without** a corroborating teacher-forced NLL is `INCONCLUSIVE`, never a pass. And require the adapter-off control at identical budget, at the floor. |
| **Y relative to the wrong baseline** | If Y is derived from v2.0's 0.4921 (a different run), the retrained control is decorative. | Express Y relative to the **retrained control's measured recall** — the whole reason the control is being retrained. But note: Y must be *locked before* the control runs, so lock it as a **fraction** of the control ("≥ 0.7 × control recall"), which is an outcome threshold committed before any outcome exists. |
| **Which arm cleared it** | A DP point clearing carries a formal claim; an adversarial point clearing does not. Reporting "∃ a point" over the union conflates them. | The gate returns the arm identity, and the report's claim string is arm-conditional. |

**How to avoid (mechanism):**
Write the v4.0 gate as a **single committed module** structurally modelled on `erasure_gate.py`:
stdlib-only, phase-neutral, keyword-only arguments, `VERDICTS = (PASS, FAIL, INCONCLUSIVE)`,
INCONCLUSIVE taking precedence over FAIL, every condition reported with its comparison rendered as
a string. Commit it **before Phase 22 runs** — ideally before P20, so it predates every v4.0
number the way `erasure_gate.py` predated every v3.0 number. Its self-check `__main__` must exercise
every branch, including the ones that fail.

**Warning signs:**
- The gate function has two arguments.
- Nobody has run a "mitigation that destroys the model" fixture through the gate and watched it
  return FAIL.

**Phase to address:** **Before P20.** This is the milestone's `erasure_gate.py` moment and its
evidentiary value is entirely in the ordering.

---

### P25: DP-SGD at 331,776 params on 220 units may destroy recall outright

**What goes wrong:**
DP-SGD is known to degrade badly on small datasets (a cited example: 11.5% accuracy at ε=1 on 1% of
CIFAR-10). This project's persona corpus is **220 episodes / 10 facts / ~10k teaching tokens** and
the task is *memorizing specific strings* — the single task DP is designed to prevent. It is
entirely plausible that **every DP point fails the recall floor**, making the DP curve a flat line
at zero recall and the existence gate satisfiable only by the adversarial arm.

That is a legitimate finding and the milestone should be able to publish it. The pitfall is
*mistaking it for an implementation bug* and "fixing" it until the numbers improve — which is how a
non-private implementation gets shipped with a printed ε (see P1, P2, P6: every one of those bugs
*improves* utility).

**How to avoid (mechanism):**
1. **Pre-register the null.** Commit, before the sweep, that "no DP point clears Y" is a reportable
   outcome with a named verdict, not a failure to produce a result. The milestone's kickoff already
   anticipates this ("at 331,776 params it may destroy recall outright") — put it in the gate's
   verdict domain, not only in the prose.
2. **A σ=0 sanity point.** The DP machinery run at σ=0 (per-example clipping only, no noise) must
   reproduce the unmitigated control's recall within the seed-to-seed noise floor. If it does not,
   the DP *machinery* is broken independently of the noise, and no amount of σ tuning will fix it.
   This point costs one run and separates "DP is hard" from "the code is wrong". **It is the single
   highest-value diagnostic in the milestone.**
3. **Never respond to bad utility by changing the DP math.** Changes to σ, C, L, T are legitimate
   sweep moves; changes to *where the clip sits* or *how the noise is scaled* after seeing utility
   are correctness changes made under outcome pressure. Require any post-first-run edit to the DP
   core to re-run the full P1/P2/P6/P9 test battery, and record that it did.

**Warning signs:**
- Utility improved after a "small fix" to the noise or clipping code.
- σ=0 does not reproduce the control.

**Phase to address:** P20 (σ=0 point), P23 (null pre-registered in the gate).

---

### Group F — Integration pitfalls with THIS codebase

---

### P26: Breaking the bit-identical-when-off guarantee on the training loop's additive seams

**What goes wrong:**
`train()` is pinned bit-identical to v1.0 when its M2 seams are off — `penalty_fn=None`,
`checkpoint_extra=None`, `extra_eval_fns=None`, `train_mask_bin=None` all documented as
"reproduces v1.0 bit-for-bit", against `tests/fixtures/golden_trajectory_v1.json`. Three
milestones of results rest on that. A DP implementation that edits `_optimizer_step` in place —
even a branch that is provably not taken — risks changing float operation order and moving the
golden trajectory. And the seams are *additive by convention*, not by construction: nothing stops
an edit.

**How to avoid (mechanism):**
1. **Do not modify `_optimizer_step`.** Add `dp_step()` as a sibling and select between them at the
   top of `train()` by a single `dp_config is None` branch, or (better) give the DP arm its own
   driver that reuses `train()`'s components without editing it. The zero-diff option is the safest
   and cheapest.
2. Run the existing golden-trajectory test as a **precondition** of the DP phase's verification,
   not merely as part of the suite — name it in the phase's acceptance criteria so its passing is
   evidence, not background.
3. Add the DP-off identity to the same fixture family: `train(..., dp_config=None)` bit-identical
   to today. This is the pattern the repo used for EWC (pre-edit golden fixture, then splice).

**Warning signs:**
- Any diff to `loop.py:136-169`.
- The golden-trajectory test is in the "these always pass" mental bucket.

**Phase to address:** P20.

---

### P27: The frozen 547-live-id tokenizer meets new training data

**What goes wrong:**
`artifacts/tokenizer.json` has **547 live ids of 8192**, trained on an 11.5KB TinyStories fixture.
Every v4.0 corpus goes through it: adversarially-perturbed training text (P22), relearning attacker
corpora (P24), any new fact families. Three consequences:
1. **Measured inflation** (this machine, this tokenizer): the same 51-character sentence encodes to
   35 tokens clean and 49 uppercased — 1.40× — and 1.17× under role-play framing. Attack intensity
   therefore *is* a budget axis (P16).
2. **Dead-id interaction.** `forbid_ids` masks undecodable ids at sampling. `teach_persona.py`
   builds it while the tokenizer is alive and threads it through `masked_perplexity`
   (`teach_persona.py:602`) — the WR-01 fix. A new v4.0 scorer that forgets the mask is a 0.008%-
   divergent near-twin of the frozen instrument, which is exactly the defect WR-01 closed. New
   evaluation code must route through the same instrument, not a copy.
3. **The v2.0 inflation gate exists** (`scripts/measure_inflation.py`, the 1.129× ≤ 1.2× GO band).
   New corpora should pass through it rather than be introduced unmeasured. It already implements
   the "measure the cost rather than assume it" discipline the tokenizer decision was praised for.

**How to avoid (mechanism):**
Run `measure_inflation.py` on every new v4.0 corpus and commit the report before training on it.
Assert every new scorer imports `undecodable_ids_mask` rather than constructing its own. Report
scored-token counts per arm as a first-class column.

**Warning signs:**
- A new corpus with no inflation report.
- A perplexity or recall number computed without `forbid_ids`.

**Phase to address:** P22 (adversarial corpora), P24 (attacker corpora).

---

### P28: Process pitfalls this project has already been bitten by

All four are recorded in the v3.0 retrospective. Each is stated here as the mechanism that would
have caught it, because v3.0's own lesson is that recording a lesson is not the same as scheduling
one (the `evaluate.py` warning crossed two entire milestones).

| v3.0 defect | Forward-applied mechanism | Owner |
|---|---|---|
| **Remediation introduced defects at nearly the rate it closed them, three rounds running.** Each round appended ~150 lines of dense count-and-line-number prose — "precisely the material that generates miscounts". The fix that worked changed two figures and added no argument. | **Cap remediation diffs.** A correction to a published number may change the number and nothing else; it may not add explanatory prose in the same commit. Treat every remediation as new work with the same verification gate as new work. For v4.0 specifically: **no ε, σ, C, q or δ may appear in prose that is not rendered from the committed constant** — a test asserts every numeric privacy parameter in `docs/REPORT.md` matches the module constant it claims to quote. | P25 |
| **An audit artifact propagated its own unverified figure ("190 lines") into a published document.** | Every figure entering a published document must name its source artifact and be re-derivable from it. v3.0 already proved the strong form works: Phase 16's and Phase 18's reports **re-render byte-identically** from committed raw records. Apply that to the frontier table and the ε table — they are generated, never authored. **And prefer deleting a false precision to replacing it** (v3.0: "190 lines" became "far above", not "186 lines"). | P25 |
| **`grep -c "three reductions"` returned 0 on a file containing it, because the phrase was line-wrapped.** A verified absence was a false absence. | **There is no whitespace-normalizing prose-search helper anywhere in this repo — I checked.** Build one: `scripts/_prose.py::normalized(text) -> " ".join(text.split())`, one definition, and route every doc-consistency test through it. The one-definition-per-statistic discipline that already covers `holm` and `wilson_upper_bound`, extended to the thing that checks the prose. This is a ~5-line module that closes a defect class the project has already shipped. | P25 (build it in P20 so it is available all milestone) |
| **Plans named APIs and paths the code refuses** — `append_addendum(..., placeholder=...)` vs the live `append_addendum(path, addendum, *, pending, recorded)`. The user's own memory records nine straight Phase 19 plans naming paths the code refuses. | **Resolve every API signature and every artifact path from the module's own constants at plan time**, and carry the resolved values forward between waves. For v4.0 this matters most for: `arm_outputs(arm, *, prefix=...)` (`teach_persona.py:197`) which owns the results paths; `erasure_gate`'s keyword-only signatures the new gate will mirror; and `save_checkpoint`'s `_RESERVED_CKPT_KEYS` — a DP state key colliding with a reserved name raises at save time, so pick the name from the constant. | Every phase |

**Additional forward-applied item:** v3.0 shipped at `tech_debt` with 16 debt items and three
permanent false `audit-open` gaps from discharged-but-not-restamped verdicts. v4.0 opens with that
inherited. Budget for it explicitly rather than discovering it at close.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reuse `_optimizer_step`'s existing `clip_grad_norm_` as "the DP clip" | Two-line DP-SGD | **Publishes a non-private ε.** Unrecoverable except by retraction | **Never** |
| Keep the window-based memmap loader for the DP arm | No new loader | The unit of privacy is a random overlapping slice; ε describes nothing anyone owns | **Never** — P10 must be settled first |
| Report Poisson-accounted ε over the existing sampler | Reuse a standard accountant | A known, published, quantified gap; the guarantee is weaker than the number | Only with the mismatch stated in the same sentence, and then it is an estimate, not a bound |
| Skip the σ=0 sanity point to save a run | ~40 min of M3 time | Cannot distinguish "DP is hard at this scale" from "the DP code is wrong" — the milestone's central ambiguity | **Never**; it is one run |
| Score the adversarial arm with the attack families it trained on | No fixture work | Frontier compares a training-set number to a test-set number | **Never** — reuse Phase 18's gated/reported tier split |
| Reuse v2.0's published 0.4921 as the recall baseline | Skips a control run | The milestone's own scope already rejects this (run-to-run variance) | Never — but the retrained control must then actually be *used by the gate* (P24) |
| Single attacker corpus for relearning | One fixture | Cannot separate "mitigation held" from "the attacker corpus was wrong shape" — and syntax, not topic, is the driver | Only as an explicitly-labelled preliminary, never as gate input |
| Hand-roll the accountant without an external cross-check | Preserves zero-new-runtime-deps | A subtly wrong accountant is the definition of a plausible-but-wrong number | Acceptable **only** with a dev-only cross-check (below) |
| Publish the DP arm's training-loss CSV without a caveat | Consistency with other arms | An un-noised function of private data presented inside a privacy guarantee | Only with the scope stated beside it |

**On the accountant specifically.** The zero-new-runtime-dependency streak is real portfolio value
(three milestones, `pyproject.toml` byte-identical at v3.0 close, sha256-enforced). It does not have
to break: the project already confines reference oracles to **tests** with grep-guards proving no
runtime dependency (`tiktoken` for BPE, brute-force perplexity for `perplexity()`). Do the same
here — a dev-extra oracle (e.g. an established accountant) used **only** in a test that pins the
hand-rolled accountant's ε against it across a grid of (σ, q, T, δ). Zero runtime deps preserved,
and the one number in the milestone that cannot be sanity-checked by inspection gets an oracle.
This is the established pattern, not an exception to it.

---

## Integration Gotchas (this codebase's seams)

| Seam | Common Mistake | Correct Approach |
|------|----------------|------------------|
| `training/loop.py::_optimizer_step` | Add DP inline; the existing `clip_grad_norm_` becomes the "DP clip" | Sibling `dp_step()`; assert the batch clip is unreachable under DP |
| `checkpoint.py::save_checkpoint` `rng` dict | Assume it covers the device stream | **It does not cover MPS** (verified). Add an `mps` slot with `.get()`-based backward compat, as `scaler` was added |
| `checkpoint.py` `**extra` | Store DP state under a reserved name | `_RESERVED_CKPT_KEYS` raises at save time — pick names from the constant |
| `seeding.py::seed_everything` | Call it per step for reproducible noise | Its own docstring forbids it; restore state, never re-seed. Enforce with the noise-independence test |
| `lora/inject.py` name filters | Write a third `"lora_" in name` filter | One `dp_parameters()`, three-way equality test against the two existing filters |
| `checkpoint.py::load_adapter` | Rely on it to catch a wrong base | It **warns and loads** on fingerprint mismatch (D-02, deliberate). The frontier needs its own hard digest check |
| `load_adapter_weights` scale audit | Assume it catches config drift | It only fires when the artifact carries `lora_config`; tests that apply raw `lora_state_dict` bypass it |
| `teach_persona.py::arm_outputs` | Hand-write result paths in a plan | Resolve from the function; it owns the prefix convention |
| `masked_perplexity` / `forbid_ids` | New scorer builds its own mask (or none) | Route through `undecodable_ids_mask` — the WR-01 near-twin defect |
| `train(extra_eval_fns=...)` | Add a persona-data diagnostic column | That is an un-noised private release (P4/P15). Ledger it or drop it |
| `CSVLogger` fieldnames | Append a DP column to an existing CSV | `DictWriter` raises on unknown keys by design; new columns need a new file |
| `tests/test_mps_smoke.py` | Leave it as the only MPS test | It is the correct and only home for DP noise-stream tests; extend it |

---

## Compute / Budget Traps

*(the template's "Performance Traps", scoped to what actually binds here: M3 wall-clock and the
number of arms)*

| Trap | Symptoms | Prevention | When it breaks |
|------|----------|------------|----------------|
| Per-example gradients cost ~B×, not ~2× | Sweep design assumes v2.0's ~38 min/arm | The milestone already gates on this: measure naive-vs-`vmap` on the M3 **before** setting Z. `vmap(grad)` **works on MPS** (verified), so the fast path exists — but measure it, do not assume it | Immediately; a 6-point × 2-arm sweep at 8× is ~30 h of M3 time |
| Arms multiply silently | 2 arms × N points × control × fresh baseline × relearning ladder × replication seed | Enumerate every run in a committed table with its estimated wall-clock before the first run | At sweep design |
| CPU-only suite grows a slow DP test | `make test` becomes unpleasant, then gets skipped | Keep the 2000-draw noise-calibration test small (few params, not the real model); put real-model DP checks in the MPS-guarded module | Once the suite crosses a few minutes |
| Interrupted long runs | Laptop sleep during a 30 h sweep is certain | `checkpoint_interval` already exists; DP state + MPS RNG must be in the checkpoint (P8) **before** the sweep, not after | First interruption |
| Noise drawn on CPU and copied per step | Cost calibration blames per-example gradients | Time noise generation separately in the calibration | During calibration |

---

## Measurement-Integrity Mistakes

*(the domain's analogue of the template's "Security Mistakes" — the risks here are to the
truthfulness of a published claim, which is this project's actual attack surface)*

| Mistake | Risk | Prevention |
|---------|------|------------|
| Publishing ε without the privacy unit | The reader assumes the strongest unit (the person). At 22 episodes/fact the gap is ~22× | `PRIVACY_UNIT` constant printed in the same sentence as ε, enforced by test |
| Publishing ε without the sampler | Poisson-accounted ε over a non-Poisson sampler is a known overstatement | Sampler named in the ε sentence; Binomial lot-size test proves the sampler |
| Selected sweep point's ε presented as the milestone's guarantee | Ignores curve composition and selection cost | Reporting helper requires `epsilon_point`, `epsilon_curve_total`, `selection_accounted` |
| A "guarantee" derived from an unaudited implementation | Every DP bug in Group A flatters the number | Ship the P1/P2/P6/P9 battery, run the σ=0 point, and consider an empirical audit (below) |
| Existence result stated as a typical-case result | Overclaims by construction | Canonical claim string quoted verbatim everywhere, whitespace-normalized check |
| Extraction ≈ 0 read as removal | Phase 19 already proved two instruments can disagree on the same weights | Corroborating teacher-forced NLL required; zero-without-NLL is INCONCLUSIVE |
| A number appearing in prose that no artifact generates | v3.0's N2 exactly | Tables generated from committed records; re-render byte-identically |

**On empirical privacy auditing.** Canary-based auditing produces an *empirical lower bound* on ε.
If the measured ε_lower exceeds the claimed ε_upper, the implementation is provably broken — a
falsifiable check on the claim itself, which is precisely this project's idiom. Modern one-run
auditing (many parallel canaries in a single training run) makes this affordable at this scale, and
this project already owns most of the apparatus: a canary fixture, a scorer, a Wilson bound, and a
42,480-draw budget precedent. **Strong recommendation: scope it as a phase.** It is the only
mechanism in this document that tests the *guarantee* rather than the *code*, and it is the
strongest possible portfolio answer to "how do you know your from-scratch DP-SGD is correct?"
If the budget will not carry it, record that decision as a named limitation with the D-16
discipline (a negative decision carries a positive's weight), not as silence.

---

## UX Pitfalls

Not applicable this milestone — v4.0 ships measurements and a report, not UI. The one demo-facing
obligation: **if any v4.0 result changes what the Gradio toggle means, the correction lands in
README, `docs/REPORT.md` and the UI in the same commit.** Phase 18 already did exactly this
(toggle relabelled "availability, not authorization" in all three), so the precedent and the
locations are known. Padding this section further would be the kind of prose this project's own
retrospective identifies as defect-generating.

---

## "Looks Done But Isn't" Checklist

- [ ] **DP-SGD:** per-example clipping verified by the two-example sensitivity probe — not by
      reading the code. Watch the test fail under a deliberately-batched clip first.
- [ ] **DP-SGD:** noise magnitude pinned against the closed form `σC/L` over ≥2000 draws.
- [ ] **DP-SGD:** noise independence across steps asserted pairwise, with a re-seeded positive
      control watched failing.
- [ ] **DP-SGD:** per-example gradients agree three ways (batch=1 oracle / `vmap` / closed form)
      **and** their mean equals the ordinary batched gradient.
- [ ] **DP-SGD:** the σ=0 point reproduces the unmitigated control within the noise floor.
- [ ] **Device:** the noise-scale and independence tests have been run **on MPS**, on the M3, at
      the current git SHA, and the result is a committed artifact. CPU-green is not evidence.
- [ ] **Checkpoint:** `rng` dict carries an `mps` slot; a kill+resume produces a **bit-identical
      reported ε**, not just a matching loss curve.
- [ ] **Checkpoint:** accountant step count is read from the checkpoint, and its absence raises.
- [ ] **Accounting:** the privacy unit is a committed string; N is a count of that unit; δ is
      computed from N; the sampler matches the accountant's assumption; the lot size is one value
      computed in one place.
- [ ] **Accounting:** ε cannot be formatted into a string outside the reporting helper.
- [ ] **Frontier:** every point carries a `spec_digest`; the gate refuses mismatched digests
      outside the declared axis.
- [ ] **Frontier:** scored-token counts reported per arm (the attack-intensity token-inflation
      confound is visible, not assumed absent).
- [ ] **Gate:** has a capability condition (dialogue PPL + retention PPL), a held-out recall leg,
      and an INCONCLUSIVE branch for zero-extraction-without-NLL.
- [ ] **Gate:** committed **before** the first v4.0 number exists, and every branch — including
      every failing one — exercised by its `__main__` self-check and by a test.
- [ ] **Gate:** a "mitigation that destroyed the model" fixture has been run through it and
      returned FAIL. A branch nobody has watched fire is a branch nobody has verified.
- [ ] **Relearning:** never-taught fresh baseline is a required argument, ran at identical budget
      and seed protocol, and cleared the recall threshold (else INCONCLUSIVE).
- [ ] **Relearning:** attacker corpus swept across ≥3 rungs including a syntax-matched,
      content-disjoint arm.
- [ ] **Relearning:** recovery measured as a curve over scored tokens for all three arms, not two
      endpoints.
- [ ] **Adversarial:** attack families partitioned TRAIN/HELD-OUT, disjointness tested, scorer
      proven to read only HELD-OUT.
- [ ] **Corpora:** every new corpus has a committed inflation report; every new scorer routes
      through `undecodable_ids_mask`.
- [ ] **Loop:** `loop.py:136-169` unmodified, golden-trajectory test named as a phase precondition.
- [ ] **Prose:** every privacy parameter in every document renders from its constant; every
      doc-consistency check is whitespace-normalized.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Batch clipping shipped (P1) | **HIGH** — retract | Withdraw the ε claim in a dated continuation (never an in-place edit); keep every *measurement*; re-implement, re-run the sweep. Recall/extraction numbers survive; only ε dies |
| Noise scale wrong (P2/P3) | **HIGH** | Same. If wrong in the conservative direction, the *published* ε is still a valid (loose) bound — state the correction and the direction, and prefer deleting the false precision to replacing it |
| Noise RNG reused (P6) | **HIGH** | Retract ε; the utility numbers are also suspect because correlated noise flatters convergence — re-run the arms |
| MPS RNG not checkpointed (P8) | **LOW if caught before the sweep**, HIGH after | Add the slot (five lines) and re-run only interrupted arms. This is why P8 lands in P20 |
| Privacy unit undefined (P10) | **HIGH** — invalidates every ε | Cannot be patched after the fact; the loader and the lot construction depend on it. Settle before any DP arm trains |
| Poisson mismatch (P11) | **MEDIUM** | Re-run with a Poisson sampler (training cost only, no code redesign if the unit index exists), or downgrade the claim from bound to estimate in the same sentence as the number |
| Sweep composition unaccounted (P13) | **LOW** | Reporting change plus a scope sentence. No re-run — this is why the framing is cheap to get right up front |
| Gate missing capability condition (P24) | **LOW before the sweep**, HIGH after | Before: add condition (c), one commit. After: adding a condition post-results is a threshold moved after seeing data, and the gate's evidentiary value is gone |
| Adversarial arm scored on its training attacks (P22-p) | **MEDIUM** | Re-score against the held-out partition (scoring cost only, no retraining), and republish the contaminated number beside the corrected one |
| Relearning baseline at wrong budget (P19/P20-p) | **MEDIUM** | Re-run the baseline at the matched budget; the mitigated arm's attack does not need re-running if Z is unchanged |
| DP destroys recall everywhere (P25) | **NONE — it is a result** | Publish it, provided the σ=0 point proves the machinery is sound. This is the milestone's most likely honest negative and the pre-registration must license it in advance |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| P24 gate loophole (capability condition, held-out recall, INCONCLUSIVE) | **Before P20** | Gate module committed at a SHA provably preceding every v4.0 artifact; every branch exercised; a model-destroying fixture returns FAIL |
| P10 privacy unit undefined | **P20** (blocks everything) | `PRIVACY_UNIT` constant; whole-unit-lot test; unit named beside every ε |
| P1 batch clipping | P20 | Two-example sensitivity probe; AST no-`clip_grad_norm_` guard |
| P2 noise after averaging | P20 | 2000-draw empirical σ vs closed form |
| P3 wrong sensitivity | P20 | Shared `SENSITIVITY_MULTIPLIER` constant; call-site identity test |
| P4 base leaks gradient signal | P20 | Release ledger; CSV-fieldname subset test |
| P5 wrong parameter group | P20 | Three-way filter equality; 331,776 census |
| P6 RNG reuse | P20 | Pairwise noise inequality + re-seeded positive control |
| P7 wrong noise device | P20 | Tests added to `test_mps_smoke.py`; committed M3 smoke artifact gates the driver |
| P8 checkpoint/resume loses DP state | P20 | `mps` rng slot; kill+resume ε bit-identity |
| P9 per-example path is secretly batch | P20 | Three-way gradient equivalence + mean-equals-batched |
| P25 σ=0 sanity / DP destroys recall | P20 (point) + P23 (null pre-registered) | σ=0 reproduces control within noise floor |
| P26 golden-trajectory drift | P20 | `loop.py` diff is empty; golden test named as precondition |
| P11 Poisson mismatch | P20 sampler / P21 accountant | Binomial lot-size distribution test |
| P12 accumulation changes the lot | P20 / P21 | (8×4) and (32×1) produce identical ε |
| P13 sweep composes | P21 framing / P23 sweep / P25 report | ε unprintable outside the three-argument helper |
| P14 δ vs N | P21 | δ computed from N; `δ·N < 0.01` assertion |
| P15 un-noised releases | P21 / P25 | Ledger covers every artifact the DP arm writes |
| P22-p contaminated attack scoring | **P22** | TRAIN/HELD-OUT partitions disjoint; import-scan proves the split |
| P27 tokenizer inflation / dead-id mask | P22 / P24 | Inflation report per corpus; scorers import `undecodable_ids_mask` |
| P16 unmatched budget | **P23** | `spec_digest` per point; gate refuses mismatches; scored-token column |
| P17 existence read as typical | P23 / P25 | Winning point replicated at a second seed; Wilson bounds gate, not point estimates |
| P18 post-hoc grid extension | P23 | Grid committed as a tuple; driver refuses off-grid points |
| P19 no never-taught baseline | **P24** | Baseline is a required kwarg; INCONCLUSIVE when it fails |
| P20-p attacker budget too small | P24 | Z calibrated from both controls before the mitigated arm is attacked |
| P21-p attacker distribution | P24 | ≥3-rung corpus ladder including syntax-matched/content-disjoint |
| P23-p suppression vs removal | P24 | Three-arm recovery curves over scored tokens |
| P28 remediation defects | **P25** + every phase | Correction diffs change figures only; privacy params render from constants; whitespace-normalized prose checks; APIs resolved from modules at plan time |

**Ordering consequences for the roadmap:**
1. **The gate module is phase-zero.** Its entire evidentiary value is that it predates the numbers.
   `erasure_gate.py` was committed before Phase 16 ran; the v4.0 gate should be committed before
   Phase 20 runs.
2. **P10 (the privacy unit) blocks the DP arm's loader**, which blocks the DP arm, which blocks the
   frontier. It is the milestone's longest dependency chain and it is design work, not code work.
3. **P8 (the MPS RNG checkpoint slot) is a five-line change now and a full sweep re-run later.** It
   should land in the first DP plan, before any long run.
4. **The σ=0 point is the cheapest high-value diagnostic in the milestone** and should be the DP
   arm's first executed run, not a later sanity check.
5. **The relearning budget Z is calibrated from the two controls**, so P24 depends on P23's
   retrained control existing — but the *never-taught fresh* baseline depends on nothing and can
   run early.
6. **An empirical privacy audit, if scoped, wants the canary infrastructure early** — it shares the
   fixture and scorer with the extraction measurement.

---

## Sources

**Verified directly on this machine (torch 2.7.1, arm64, MPS available) — HIGHEST confidence.**
Probe scripts under the session scratchpad; every claim below was measured, not inferred:
- `vmap(grad(...))` composes and returns correct per-sample gradient shapes **on MPS**.
- `torch.manual_seed` makes MPS draws reproducible; `torch.Generator(device="mps")` works; a CPU
  generator passed to an MPS draw **raises** `RuntimeError`.
- CPU and MPS are **separate RNG streams**: `manual_seed(5); randn(4).to("mps")` ≠
  `manual_seed(5); randn(4, device="mps")`.
- **`torch.get_rng_state()`/`set_rng_state()` — what `checkpoint.py` saves and restores — does not
  cover MPS.** `torch.mps.get_rng_state`/`set_rng_state` exist and do round-trip.
- `nn.Dropout(0.0)` consumes no torch RNG (hence today's loop consumes no device RNG).
- `clip_grad_norm_(model.parameters(), ...)` skips `grad is None`, so it already targets exactly
  the LoRA gradients — on the averaged batch gradient.
- MPS has no fp64.
- Frozen tokenizer inflation on one 51-char sentence: clean 35 tokens, **uppercased 49 (1.40×)**,
  role-play framed 1.17×.

**Read from this repository — HIGH confidence:**
- `src/personacore/training/loop.py` (`_optimizer_step` clip site, the four additive seams,
  CSV fieldname derivation), `training/data.py` (with-replacement window sampling),
  `checkpoint.py` (`rng` dict, `_RESERVED_CKPT_KEYS`, `load_adapter` warn-and-load),
  `seeding.py`, `config.py`, `lora/layer.py`, `lora/inject.py`, `continual/fisher.py`
  (the batch=1 per-example-gradient precedent), `scripts/erasure_gate.py` (the gate pattern and
  the published v2.0 baselines), `scripts/teach_persona.py` (hyperparameters, seeding order,
  canary, WR-01 mask threading), `scripts/phase18_extraction.py` (attack families, the
  gated/reported tier split), `tests/test_mps_smoke.py`, `tests/test_phase18_prereg.py`.
- `results/phase14_teaching_run.log` — **220 episodes, 20,036 tokens (10,018 teaching +
  10,018 replay), episode length mean 45.5 [24, 84]**, `batch_size=8 max_steps=200 block_size=256`.
- `.planning/PROJECT.md`, `.planning/RETROSPECTIVE.md`.
- Verified absence: no whitespace-normalizing prose-search helper exists anywhere in
  `src/`, `scripts/` or `tests/`; `mps` appears nowhere in `checkpoint.py` or `seeding.py`.

**Literature — MEDIUM confidence (canonical papers, multiple independent sources agreeing):**
- Abadi et al., *Deep Learning with Differential Privacy* (DP-SGD, moments accountant) — the
  per-example-clip-then-noise-the-sum ordering.
- [How to DP-fy ML: A Practical Guide to Machine Learning with Differential Privacy](https://arxiv.org/pdf/2303.00654)
  — per-example vs micro-batch clipping; micro-batch sensitivity is 2G not G; accounting
  assumptions must match implementation.
- [Finding Private Bugs (ICLR 2023 submission)](https://openreview.net/pdf?id=gKKUZ4fTEqh) —
  omitted/incorrect DP-SGD modifications invalidate the guarantee silently.
- [Scalable DP-SGD: Shuffling vs. Poisson Subsampling (NeurIPS 2024)](https://arxiv.org/abs/2411.04205)
  and [How Private are DP-SGD Implementations?](https://arxiv.org/html/2403.17673) — the
  standard shuffled-implementation / Poisson-accounting mismatch, with lower bounds showing the
  gap is substantial at small ε.
- [Bridging the Privacy Accounting Gap in DP-SGD](https://journalprivacyconfidentiality.org/index.php/jpc/article/view/998).
- [Subsampled Rényi Differential Privacy and Analytical Moments Accountant](https://arxiv.org/abs/1808.00087)
  and [Poisson Subsampled RDP](https://proceedings.mlr.press/v97/zhu19c.html) — analytical RDP for
  the subsampled Gaussian mechanism; the hand-rollable form, and its numerical-stability caveats.
- [Hyperparameter Tuning with Rényi Differential Privacy (Papernot & Steinke)](https://arxiv.org/abs/2110.03620)
  and [Practical DP Hyperparameter Tuning with Subsampling](https://arxiv.org/pdf/2301.11989) —
  selecting the best of several runs has a real, non-zero privacy cost.
- [Mind the Privacy Unit! User-Level DP for Language Model Fine-Tuning](https://arxiv.org/pdf/2406.14322)
  — record-level vs user-level neighbouring; group privacy multiplies ε by the group size.
  *(Pin the exact group-privacy formula from a source at write time — do not retype it.)*
- [Unlearning or Obfuscating? Jogging the Memory of Unlearned LLMs via Benign Relearning](https://arxiv.org/abs/2406.13356)
  — small, loosely-related data reverses approximate unlearning; suppression ≠ removal.
- [Rethinking Benign Relearning: Syntax as the Hidden Driver of Unlearning Failures](https://arxiv.org/html/2602.03379)
  — **syntactic similarity, not topicality, drives recovery**; directly shapes the attacker-corpus
  ladder (P21-p).
- [Obfuscated Gradients Give a False Sense of Security (Athalye et al.)](https://arxiv.org/abs/1802.00420)
  — 7 of 9 ICLR 2018 defenses relied on obfuscated gradients; defenses must be evaluated against
  adaptive attacks that know the defense. The direct precedent for P22-p.
- [Privacy auditing / one-run auditing](https://arxiv.org/html/2606.12733v2),
  [Detectability in Diversity](https://arxiv.org/html/2605.27292),
  [Optimizing Canaries with Metagradient Descent](https://arxiv.org/abs/2507.15836) — empirical
  ε lower bounds from a single training run; the falsifiable check on a DP implementation.
- [Privacy Enhanced PEFT / DP-LoRA utility at small data](https://arxiv.org/html/2601.10045) —
  DP-SGD degrades severely on small datasets (11.5% at ε=1 on 1% of CIFAR-10); DP+LoRA carries
  non-trivial utility drops. The empirical basis for P25.
- [Position: LLM Unlearning Benchmarks are Weak Measures of Progress](https://arxiv.org/abs/2410.02879)
  — already cited by `erasure_gate.py`; the reason "indistinguishable from never-learned" is not
  the goal here either.

**Open questions this research could not resolve:**
- Whether a hand-rolled RDP accountant can be made numerically trustworthy without an oracle at
  this scale. Recommendation is the test-only oracle (dev extra), but the specific library and the
  agreement tolerance are a P21 decision.
- Whether the closed-form per-example LoRA gradient norm is derivable cleanly through
  `LoRALinear.forward`'s `x @ A^T @ B^T` composition with dropout in the path. Needs the algebra
  worked and pinned against the batch=1 oracle — a P20 task, not a research answer.
- Whether any ε small enough to be interesting is reachable at N=220 units, T=200 steps. The
  arithmetic is unfavourable (large q, few steps, weak amplification) but this document
  deliberately publishes **no ε estimate**: an unverified number here would be exactly the defect
  it warns about (v3.0: prefer deleting a false precision to replacing it). **Compute it in P20
  from the committed unit index, before the sweep is designed.**

---
*Pitfalls research for: training-time privacy mitigation + adversarial validation on PersonaCore*
*Researched: 2026-08-20*
