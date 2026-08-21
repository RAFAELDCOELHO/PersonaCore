# Requirements — Milestone v4.0: Leakage Mitigation and Relearning Validation

**Defined:** 2026-08-20
**Milestone goal:** v3.0 measured that weight-based memory leaks 88.5% under prompt-only attack and
ran no mitigation arm. v4.0 builds training-time mitigation, maps the privacy/utility frontier for
two mechanisms across two corpus capacities, and proves adversarially — by relearning attack — that
what survives cannot be cheaply reverted.

**Research:** `.planning/research/SUMMARY.md` (synthesized from STACK / FEATURES / ARCHITECTURE /
PITFALLS, committed `c673b4c`).

**Standing expectation, recorded before any run:** research puts high prior probability on the DP
arm being a **pre-registered null** — fact-level noise-to-signal is `σ√d/L` = 72σ at L=8 facts, and
ε_fact ≤ 4 needs σ ≥ 15.3, a ratio near 1,100; Secret Sharer Table 3 is the direct precedent. The
milestone is scoped to **publish that null well**, at two capacities, not to avoid it.

---

## v4.0 Requirements

### Pre-registration (GATE)

The gate's entire evidentiary value is ordering. `erasure_gate.py` was committed at `23a830c`
*before Phase 16 ran*; the v4.0 gate must be committed before **any** v4.0 number exists — before the
cost calibration, not merely before the sweep.

- [x] **GATE-01**: A committed decision module returns `PASS` / `FAIL` / `INCONCLUSIVE` for a sweep
      point against **three** conditions — (a) extraction ≤ X, (b) taught-fact recall ≥ Y, (c)
      general capability ≥ C — with every argument keyword-only, no defaults, and every condition
      rendered into a reason string.
- [x] **GATE-02**: Condition (c) is computed from constants **imported** from `erasure_gate.py`
      (`V20_MASKED_DIALOGUE_VAL_PPL` 4.5733, `V20_EWC_RETENTION_PPL` 3.891140,
      `V20_RETENTION_NOISE_FLOOR` 0.068930, `MARGIN_K` 2) plus the measured
      `dialogue_ppl_noise_floor` (0.005214448168350039, `results/phase19_noise_floors.json`), never
      retyped as literals — yielding `dialogue_cap` 4.5837288963367 and `retention_cap` 4.029000.

  > **Amended by D-36 at plan `20-09`, and the amendment is TIGHTER.** The `retention_cap`
  > `4.029000` above is derived from `V20_RETENTION_NOISE_FLOOR = 0.068930`, a **Phase 12
  > FULL-FINE-TUNE** seed pair, and it is NOT what governs v4.0.
  > `scripts/mitigation_gate.py::retention_cap` deliberately does not import that constant — a test
  > asserts its absence from a five-name `from erasure_gate import` list checked by EXACT EQUALITY —
  > and takes the retention floor as a **required keyword argument** with no default instead (D-07).
  > The governing floor is the **adapter-regime** `0.008681618994239138`, measured at plan `20-07`
  > (`results/phase20_retention_floor.json`, two seeds, bit-identity control passed at
  > `abs_delta = 0.0`), so the governing v4.0 `retention_cap` is **`3.9085032379884783`**. The
  > borrowed floor is `7.939763314393305x` larger and its cap `4.029` correspondingly LOOSER, which
  > means this amendment makes condition (c) **harder** to clear — a self-serving amendment moves a
  > threshold the other way. `dialogue_cap` `4.5837288963367` is unchanged, and
  > `scripts/erasure_gate.py:246` still computes `4.029` for **Phase 19** verdicts and is
  > deliberately NOT corrected.
  >
  > **Why the pre-registration text is edited at all, when this repo's convention is that it is
  > not.** The supersession was already recorded in the traceability row below at plan `20-07`, but
  > a `[x]` is machine-readable and the note beside it is not, so an automated audit that counts
  > checkboxes reports GATE-02 satisfied AS WRITTEN. D-36 accepts an in-place edit on four grounds
  > that must hold together: it is DATED (2026-08-21), it is IN PLACE so a `grep` for `4.029000`
  > cannot miss it, it is ADDITIVE — every word of the original requirement above is byte-identical
  > — and it is provably TIGHTER by the arithmetic just given. ROADMAP SC1 already carries this
  > exact shape for this exact number.
  >
  > **The enforcement, so this is a mechanism and not prose.** `_prove_retention_floor` in
  > `scripts/phase20_gate_coverage.py` (plan `20-08`) refuses `0.06893` at the choke point every
  > corrected verdict passes through, and `tests/test_phase20_correction.py` (plan `20-11`) asserts
  > that `retention_cap` called with the measured floor equals the artifact's published `cap`
  > bit-exact.

- [x] **GATE-03**: Y is a **pair** (`Y_taught` and `Y_heldout`), because v2.0 published two recall
      numbers (0.4921 / 0.3483) and gating taught-only rewards memorization over generalization.
- [x] **GATE-04**: Y is locked as a **fraction of the retrained control** (e.g. `≥ 0.7 × control`),
      not derived from v2.0's published numbers — otherwise the retrained control is decorative.
- [x] **GATE-05**: An `INCONCLUSIVE` branch for zero-extraction-without-NLL — extraction at or near
      zero **without** a corroborating teacher-forced NLL is never a pass. Ports
      `zero_results_have_nll` semantics; `INCONCLUSIVE` takes precedence over `FAIL`.
- [x] **GATE-06**: A `FAILURE`-vs-`INCONCLUSIVE` discriminator for a truncated sweep — if the swept
      axis never produced points on both sides of X (or of Y), the curve cannot refute existence and
      the verdict is `INCONCLUSIVE`. This is exactly the failure a mis-set Z produces.
- [x] **GATE-07**: The gate returns **arm identity** — a DP point clearing carries a formal claim, an
      adversarial point clearing does not, and "∃ a point" over the union conflates them.
- [x] **GATE-08**: A clearing point is provisional until **replicated at a second seed**, required by
      the gate rather than reported beside it (Phase 17's worst-pair-at-k=3 pattern).
- [x] **GATE-09**: The `__main__` self-check exercises every branch including the failing ones, and a
      **"mitigation that destroyed the model" fixture is run through it and observed returning
      `FAIL`** — a branch nobody has watched fire is a branch nobody has verified.
- [x] **GATE-10**: The n=8-vs-n=64 capacity comparison rule is committed in the same module, before
      either run: if n=64 recovers recall that n=8 did not at equivalent ε_fact, that is a finding
      about where capacity stops destroying the mitigation; if it does not, the null is confirmed at
      two capacities. Both branches are publishable and neither may be chosen after seeing data.

### Privacy unit, DP data path, and corpus (UNIT)

The longest dependency chain in the milestone, and design work rather than code. "The unit was wrong"
invalidates every ε and no amount of re-running fixes it.

- [ ] **UNIT-01**: The privacy unit is **the fact**, not the 256-token window — recorded as a decision
      with its arithmetic, because `get_batch_memmap_masked` draws overlapping windows with
      replacement over a flat concatenated bin, so an example-level ε bounds nothing about a fact.
- [ ] **UNIT-02**: Fact-aligned batching — each fact's shard padded to whole `block_size` windows so
      `grad_accum_steps = n_facts` makes the existing accumulation loop the per-example loop, with
      **no subsampling** (q=1) and therefore an exact accountant.
- [ ] **UNIT-03**: The effective per-fact multiplicity in gradient steps is **measured**, not inferred
      — 22 rendered rows per fact is confirmed (176 rows / 8 `LOCKED_FACTS`), but `build_bins` window
      packing and `replay_ratio` determine what an ε actually rests on, and that is unmeasured.
- [ ] **UNIT-04**: A recorded decision on whether PersonaChat replay participates in the DP lot —
      `replay_ratio=1.0` puts public data in the bin, and counting it in N shrinks q and produces a
      flatteringly small ε.
- [ ] **UNIT-05**: δ is pinned as the literal **1e-5**. The `1/N^1.1` recipe is self-contradictory at
      a fact unit: at N=8 it yields δ=0.1015 and fails its own `δ·N < 0.01` assertion by ~80×.
- [ ] **UNIT-06**: An n=64 corpus built from **unscored filler facts** that touch no ancestry-pinned
      fixture, so the capacity lever can be tested without disturbing any published instrument.

### DP-SGD core and accountant (DPSGD)

- [ ] **DPSGD-01**: From-scratch per-example gradient clipping + Gaussian noise on the LoRA gradients
      only, base frozen, entering `train()` through a **new additive gradient-side seam** — the
      existing `penalty_fn` is a loss seam and cannot carry it.
- [ ] **DPSGD-02**: The default path is proven **bit-identical when the seam is off**, against the
      Phase-10 golden-trajectory fixture — the `penalty_fn` playbook verbatim.
- [ ] **DPSGD-03**: A from-scratch (ε, δ) accountant in stdlib `math`, exact under q=1 composition,
      validated against independent oracles (closed-form Gaussian, numerical quadrature).
- [ ] **DPSGD-04**: A correctness battery that catches the known silent-non-privacy failures: clipping
      the averaged gradient instead of per-example (`loop.py:165` already clips the LoRA grads on the
      **averaged** gradient — the cheapest possible fake DP-SGD is a two-line diff that converges
      fine), noise scaled to the wrong sensitivity, noise added after averaging, RNG reuse across
      steps.
- [ ] **DPSGD-05**: `checkpoint.py` gains an **MPS RNG slot**. Latent today because the loop consumes
      zero device RNG; DP noise is the first per-step consumer. Five lines now, a full sweep re-run
      later. Must land before any long run.
- [ ] **DPSGD-06**: The σ=0 point is the DP arm's **first executed run** — the only cheap diagnostic
      separating "DP is hard at this scale" from "the code is wrong", since every correctness bug in
      this class *improves* utility.
- [ ] **DPSGD-07**: `LoRALinear` is **not** restructured into `nn.Linear` submodules — `lora_A`/
      `lora_B` are bare `nn.Parameter`s in an inline matmul (`lora/layer.py:41`), and restructuring
      would rename state-dict keys and invalidate `persona_adapter.pt` and every v3.0 checkpoint.

### Cost calibration and budget pre-registration (CAL)

**The evaluation leg is measured, and it decides the sweep.** Research reported evaluation
wall-clock as unmeasured because STACK's generation probe failed. The number already existed in the
repo: Phase 18's own D-12 pre-flight (`results/phase18_preflight_report.md`, committed with git_sha,
pid, seed and corpus sha256) measured per-shape throughput on `convbase_slim.pt` at MPS/torch 2.7.1
— A1-mild 145.01, A1-aggressive 134.54, A2 183.20, A3 140.85 draws/min. Replicating that report's
own projection from those rates reproduces its stated **84,960 draws / 9.54 h across both arms**
exactly, which validates the cost model against a committed artifact rather than against an estimate.

Therefore, per sweep point at full Phase-18 fidelity: **42,480 draws = 4.77 h**. Training is ~17 s
per arm. **Evaluation costs ~1,010× training** — it is the binding constraint by three orders of
magnitude, and no sweep density may be chosen without it.

| per-point K | draws/point | h/point | 16-point sweep | ASR rungs |
|---|---|---|---|---|
| 48 (Phase 18 fidelity) | 42,480 | 4.77 | 76.3 h = 3.2 days | (1, 4, 16, 48) |
| 24 | 21,744 | 2.45 | 39.2 h | (1, 4, 16, 24) |
| 16 | 14,832 | 1.67 | 26.8 h | (1, 4, 16, 16) |
| 8 | 7,920 | 0.90 | 14.4 h | (1, 4, 8) — loses rung 16 |

- [ ] **CAL-01**: The training leg is measured to complete the pair (~17 s per arm from research, to
      be confirmed on the DP path with the seam active). The evaluation leg is **already measured**
      above and is authoritative for sweep sizing.
- [ ] **CAL-02**: Z (sweep width, per-point draw budget K, step budget) is set **from** those
      measurements and committed in a module separate from the gate, with the separation structurally
      enforced so a reader cannot mistake a resource calibration for an outcome-threshold peek.
- [x] **CAL-04**: **Per-point K and the promotion rule are committed before any v4.0 artifact
      exists.** `phase18_extraction.py:88-92` records that reducing K *after* seeing a null is the
      weakening `ATK-03` and `P18-4` exist to prevent, and that pre-flight is "the one moment the pin
      leaves open for it." v4.0 is at that same moment. Pre-register: the curve K, the full-fidelity
      K reserved for gate-candidate points, and the rule that promotes a point from the first to the
      second — all three before the first point is drawn.
- [ ] **CAL-05**: The rate above was measured on the **un-adapted base**, where 45–56 of 64 draws
      per shape terminated on a stop id. A heavily-noised DP adapter that stops emitting EOS runs the
      full `max_new_tokens=48` on every draw — the slowest case — so 4.77 h/point is a **floor for
      noised points, not a mean**. The calibration must re-measure throughput on one noised adapter
      before the sweep width is finalised.
- [ ] **CAL-03**: The inference "**ε is independent of N at q=1**" — the premise the entire n=64 phase
      rests on — is confirmed by a small calibration run at n_facts=8 vs 64 at fixed σ **before** the
      expensive n=64 run is committed. Research marks it `[INFERENCE]`, not measured.

### Adversarial extraction-aware training (ADVT)

- [ ] **ADVT-01**: The adapter trained against the Phase 18 attack suite with **attack intensity as
      the sweep axis**, implemented as a `build_bins` mixture ratio — no new training seam required.
- [ ] **ADVT-02**: A pre-registered **leave-one-attack-family-out** split, with the held-out family
      named **before** training. The four families already exist separably in
      `phase18_extraction.py`; choosing the held-out family after seeing which the defense handles
      worst is the peek this project's discipline forbids.
- [ ] **ADVT-03**: Attack intensity is disclosed as **also a token-budget axis** — measured through
      the frozen 547-live-id tokenizer, the same 51-character sentence is 35 tokens clean, 49
      uppercased (1.40×), 1.17× role-play framed.

### Control arms (CTRL)

Both anchors precede every sweep point: a point at extraction 0.30 means nothing until the retrained
control's position and the never-taught floor are known.

- [ ] **CTRL-01**: A **retrained unmitigated control** at identical budget and seed protocol — v2.0's
      published 0.4921 / 0.3483 belong to a different run and cannot serve as this milestone's
      baseline without confounding the comparison with run-to-run variance.
- [ ] **CTRL-02**: The control is realised as a **sweep point** (`clip_norm=inf, noise_multiplier=0`)
      so it differs from every DP point by exactly the two DP parameters. Recorded explicitly: it is
      *not* bit-identical to the seam-off path (floating-point non-associativity), and chasing that
      identity would be a mistake.
- [ ] **CTRL-03**: A **never-taught fresh adapter** at identical budget and seed, serving double duty
      as frontier floor and relearning reference. Depends on nothing; scheduled early.

### Frontier sweep and verdict (FRONT)

- [ ] **FRONT-01**: A privacy/utility curve for both arms at **both capacities** (n=8 and n=64) — ε
      for DP-SGD, intensity for adversarial — swept to the never-taught floor and to σ→0 so the curve
      reconnects to the control at both ends.
- [ ] **FRONT-02**: Dual ε reporting — example-level **and** fact-level — so an example-level ε can
      never be read as if it bounded fact leakage.
- [ ] **FRONT-03**: A committed frontier JSON artifact carrying counts (not rates), ordered point
      keys, `accounting: null` on the adversarial arm as a structural statement that it makes no
      formal claim, and the gate/budget module sha256s. Figures are drawn **only** from this artifact.
- [ ] **FRONT-04**: The verdict is computed by **importing** the GATE module's constants, never by
      retyping a threshold in prose.

### Relearning attack (RELRN)

- [ ] **RELRN-01**: Absolute recovery ceiling as the **binary pre-registered gate** — recovered recall
      ≤ X within a fixed budget Z.
- [ ] **RELRN-02**: A **cost-to-recovery curve** (steps/examples to restore leakage) measured against
      the never-taught fresh adapter at identical budget and seed. Mitigated ≈ fresh means the
      information was removed rather than suppressed.
- [ ] **RELRN-03**: The cost curve **qualifies** the PASS/FAIL verdict as a recorded finding; it is
      not a second gate. Same "an instrument qualifies a gate's reading, it does not replace it"
      pattern v3.0 established.
- [ ] **RELRN-04**: "Identical budget and seed" is enforced **structurally** — one shared
      `TrainConfig` object, an evidence diff read back off disk, and a data-order sha256 proof — not
      by convention.
- [ ] **RELRN-05**: Recovery is measured on a fixture **disjoint** from anything the mitigation was
      trained against, and the attacker corpus is pre-registered, because the corpus definition *is*
      the threat model.

### Empirical privacy audit (CANARY)

The only mechanism in the whole research pass that tests the **guarantee** rather than the **code**.

- [ ] **CANARY-01**: One-run canary auditing produces an **empirical lower bound on ε**, built
      additively on the Phase 18 fixture, scorer, Wilson bound and 42,480-draw precedent.
- [ ] **CANARY-02**: A rule committed before the audit runs: **if the measured ε_lower exceeds the
      ε_upper claimed by the formal accounting, the implementation is declared provably broken** —
      stated with no room for a favourable reading afterward.

### Report and close (RPT)

- [ ] **RPT-01**: The milestone report publishes whichever way the numbers came out, including the
      expected DP null at both capacities, with the standing expectation above quoted as having been
      recorded before any run.
- [ ] **RPT-02**: A whitespace-normalizing prose-search helper exists and is used for correction
      sweeps — v3.0's `grep -c` lesson (a line-wrapped phrase reported as absent on a file containing
      it) was recorded and never converted into a mechanism.
- [ ] **RPT-03**: Zero new runtime dependencies; `pyproject.toml` sha256-pinned state carries forward
      untouched, making it four milestones.

---

## Future Requirements

Deferred to a later milestone, recorded rather than dropped.

- Erasure at higher adapter rank or via a non-ablation mechanism (v3.0 candidate 2). Phase 19's
  `FAILURE` was bounded to one mechanism, one fact, one adapter at 331,776 parameters, and the
  rank-instrument co-headline says the rank reading alone cannot be trusted to report selectivity.
- The frozen tokenizer / retrain question (v3.0 candidate 3). Held out of v3.0 for the same reason it
  is held out here: it invalidates every published checkpoint and number, and needs its own
  conversation.
- The 16 tech-debt items, 3 `PARTIAL` VALIDATION.md files and 6 stale status stamps carried from
  v3.0. All are prose, documentation or tooling; none touches a measured number, a gate, or a
  requirement's status.
- **New debt found while measuring the evaluation leg (2026-08-20):** the comment block at
  `scripts/phase18_extraction.py:85-87` cites throughput rates of 146.98 / 127.70 / 178.74 / 130.31
  draws/min (blended 143.04, projecting 9.91 h) and attributes them to
  `results/phase18_preflight_report.md` — but that committed artifact reports 145.01 / 134.54 /
  183.20 / 140.85 and a total of **9.54 h**. A committed code comment carries four numbers its own
  cited evidence does not contain. **No published result changes** — the K=48 decision holds under
  either set, and both sit under the 13.12 h that K=64 was rejected at. It is recorded here rather
  than fixed because `phase18_extraction.py` is ancestry-guarded and the v3.0 lesson is that
  correction prose is denser in exactly the facts that are easy to get wrong. v4.0 uses the
  **artifact's** numbers.

## Out of Scope

- **HuggingFace PEFT / transformers model code, and `opacus`** — excluded by design. `opacus` is
  rejected even as a test oracle: it would drag `scipy` + `opt-einsum` into CPU-only CI for a 30-line
  function, and as an oracle it shares the same closed form and therefore the same failure modes.
- **Ghost clipping** — rejected on arithmetic by two independent derivations. At r=8, T=256 the
  crossover is T < 7.8 tokens, so it costs ~30–33× *more* than direct materialization here.
- **A Poisson loader on the critical path** — Poisson over 8 facts is degenerate (10% chance of an
  empty lot per step at q=0.25), and fact-alignment reaches the same ε_fact within ~10% at a δ two
  orders of magnitude smaller.
- **Restructuring `LoRALinear` to `nn.Linear` submodules** — renames state-dict keys and invalidates
  `persona_adapter.pt` and every v3.0 checkpoint.
- Databases, vector stores, RAG, external memory files; scaling beyond ~10–15M params; multi-GPU.

## Traceability

Every REQ-ID maps to exactly one phase. **48/48 mapped, 0 orphans, 0 duplicates**
(verified 2026-08-20 at roadmap creation).

| REQ-ID | Phase | Note |
|--------|-------|------|
| GATE-01 | Phase 20 | `mitigation_point_verdict` returns the three-name `V4_VERDICTS` domain, proved at import by the module-scope `_prove_verdict_domain()`, with four condition reason strings observed rendering. Guarded by `test_verdict_domain_stays_exactly_three` and by `test_every_gate_function_is_keyword_only_with_no_defaults`, whose AST walk covers ALL public functions in the module rather than the verdict one alone. |
| GATE-02 | Phase 20 | **The MECHANISM is discharged; the stated `retention_cap 4.029000` is SUPERSEDED by D-06.** `scripts/mitigation_gate.py::retention_cap` imports `V20_EWC_RETENTION_PPL` and `MARGIN_K` and retypes nothing, but it takes the retention floor as a REQUIRED keyword argument (D-07) and does NOT import `V20_RETENTION_NOISE_FLOOR = 0.068930` — that is a Phase 12 FULL-FINE-TUNE reading. The adapter-regime floor `0.008681618994239138` measured at plan `20-07` (`results/phase20_retention_floor.json`) is what governs v4.0, yielding `3.9085032379884783`. The requirement's `4.029000` is published beside it in the artifact as `borrowed_cap` so the supersession is visible rather than silent. `scripts/erasure_gate.py:246` still computes `4.029` for Phase 19 verdicts and is NOT corrected. **RESIDUAL — CLOSED at plan `20-12` (2026-08-21), against a re-run of the guard rather than against a SUMMARY.** The residual was that the supersession was recorded but not *enforced*: `extraction_ceiling` carried THREE `_prove` calls refusing a wrong-arm / <2-seed / missing-provenance floor while `retention_cap` carried ZERO, so — measured — `retention_cap(retention_noise_floor=0.068930)` returned `4.029`, the LOOSER cap, with no refusal at all. That was asymmetric against T-20-24, whose whole point is that `mitigation_point_verdict` calls `extraction_ceiling` itself so no path to a verdict skips the provenance check. The retention leg now has its equivalent choke point. `scripts/phase20_gate_coverage.py::_prove_retention_floor` (plan `20-08`) supplies the four refusals the FROZEN `retention_cap` cannot be given: three mirroring `extraction_ceiling`'s at `scripts/mitigation_gate.py:417` / `:425` / `:436` — missing provenance keys, wrong `regime`, fewer than two distinct seeds — plus a fourth refusing `V20_RETENTION_NOISE_FLOOR` BY IDENTITY (imported, never retyped), so a caller that lies about `regime` is still caught by the number itself. It is a CHOKE POINT, not an advisory: it is called FIRST in `corrected_point_verdict`, before any compute, so no path through the sanctioned route reaches a verdict skipping it — the same structural discipline as the extraction leg, not merely documentation. Guarded by `tests/test_phase20_correction.py::test_the_retention_floor_tripwire_is_the_only_route_to_a_verdict` (plan `20-11`), which drives all eight refusal cases THROUGH the verdict route with a positive control, and which was WATCHED going red: one `_prove` deleted from `_prove_retention_floor` produced `Failed: DID NOT RAISE <class 'SystemExit'>`, and the module was restored byte-identically. **The requirement's own text now carries this supersession too** — see the dated D-36 amendment beneath the `- [x] **GATE-02**` bullet, added at plan `20-09` (2026-08-21), so a reader who greps `4.029000` lands on the correction instead of on the superseded number alone. |
| GATE-03 | Phase 20 | Y is the pair `(y_taught, y_heldout)` computed inside `mitigation_point_verdict` at `:765-766`, each leg from `F_Y` times its own control, and both legs are read by condition (b). Guarded by `test_every_verdict_branch_fires`. |
| GATE-04 | Phase 20 | Each leg is `F_Y` × its OWN retrained control, never v2.0's published numbers: `0.4921` and `0.3483` are asserted absent as numeric constants by AST, and the `from erasure_gate import` list is asserted by EXACT EQUALITY to five names so `V20_TAUGHT_RECALL` / `V20_HELDOUT_RECALL` cannot reach `mitigation_point_verdict`. Guarded by `test_no_imported_baseline_is_retyped`. |
| GATE-05 | Phase 20 | The zero-extraction-without-NLL early return at `:730-745` fires BEFORE any reason is appended, so `mitigation_point_verdict` hands back a one-element reason list and INCONCLUSIVE precedes FAIL. Watched firing differentially against the FAIL it overrides by `test_every_verdict_branch_fires`. |
| GATE-06 | Phase 20 | **DISCHARGED at plan `20-12` (2026-08-21) — against a re-run of the guards in the discharging process, never against a SUMMARY.** THE MECHANISM SHIPPED AT PLAN `20-04` AND WAS DEFECTIVE ON BOTH AXES. **CR-01:** the discriminator at `scripts/mitigation_gate.py:798-812` decided sweep coverage on RAW rates while condition (a) at `:755` decides the same axis on `wilson_upper_bound(k, n)` against the same `ceiling` — two statistics, one ceiling. **WR-09:** there was no `sweep_heldout_recalls` parameter anywhere in the 21-kwarg signature, so the held-out leg SC2 makes load-bearing had no coverage check at all and no caller convention could supply one. BOTH DIRECTIONS WERE REPRODUCED, with their fixtures named, at n=104, X=`0.04535522866494124`: `FIXTURE_CLEARING_POINT` + `(1/104, 3/104)` returned `INCONCLUSIVE` where the sweep genuinely brackets X under the (a) rule (`wilson_upper_bound(1,104)=0.041950` clears, `wilson_upper_bound(3,104)=0.069999` fails), demoting a would-be `PASS`; `FIXTURE_DESTROYED_MODEL` + `(3/104, 11/104)` returned `FAIL` with NO GATE-06 reason on an axis where ZERO points clear X — "it did not work" published where the honest finding is "we could not tell". A THIRD CASE, in no prior report, is the sharpest: `FIXTURE_CLEARING_POINT` + `(3/104, 11/104)` returned `PASS` off that same truncated axis. **`scripts/mitigation_gate.py` was NOT edited** — it is byte-identical to its nine pinned commits, `git diff --exit-code` on it and on `scripts/erasure_gate.py` returns 0, and the ancestry guard is green, so the pre-registration survives its own correction. **THE DISCHARGE:** `scripts/phase20_gate_coverage.py::coverage_verdict` (plan `20-08`, UNPINNED) decides each axis on the statistic that axis's criterion is decided on — `wilson_upper_bound(k, n)` for extraction, raw recall for BOTH Y legs — covering the extraction axis and closing WR-09 in the same function (D-35). `corrected_point_verdict` is the sanctioned route to a v4.0 verdict and has NO `sweep_extraction_rates` parameter, so raw-rate space is unreachable through it by construction, and a raw rate handed to the count parameter is refused BY NAME (`SystemExit` naming both RATE and COUNT). **THE RECORD:** `results/phase20_gate_coverage_correction.json` — `governs` = sweep coverage (GATE-06), naming `coverage_verdict` as the computation and `corrected_point_verdict` as the route; `supersedes` = `scripts/mitigation_gate.py:798-812` — plus the D-24 dated continuation `results/phase20_gate_coverage_correction.md` (dated `2026-08-21`, the day it was written). **THE GUARD:** `tests/test_phase20_correction.py` (plan `20-11`), which asserts both directions RED against the frozen pin and GREEN through the correction in one differential body each, plus the AST caller census that reddens on the first Phase 23/25 caller bypassing the route. **BOUND DIRECTION (D-37), with its cost:** Wilson upper on the X ceiling, raw rates on the Y floors — because a Wilson LOWER bound on a floor would decide coverage on a statistic condition (b) does not read, re-introducing CR-01's defect class with the sign flipped. The Y legs therefore inherit condition (b)'s own lack of a confidence bound; that is recorded and deliberately NOT fixed, because fixing it would move a pre-registered threshold after seeing the data it governs. |
| GATE-07 | Phase 20 | The returned 3-tuple carries `arm`, `exists_clearing_point` aborts on a mixed-arm point list so the ∃ cannot be formed over the union, and `ARM_CLAIMS` is proved equal to `ARMS` at import. Guarded by `test_every_verdict_branch_fires`. |
| GATE-08 | Phase 20 | A point clearing (a), (b) and (c) without second-seed replication returns INCONCLUSIVE over a would-be PASS at `:822-829`; `REPLICATION_PENDING_MARKER` is ONE constant read by both that branch and `promote_to_full_fidelity`, and no `provisional` identifier, string or comment exists anywhere (AST plus a `_prose.normalized` scan). Guarded by `test_promotion_rule_and_ratchet`. |
| GATE-09 | Phase 20 | Six outcomes observed firing in the `__main__` self-check, and `FIXTURE_DESTROYED_MODEL` is built from Phase 19's real published M1 readings with four fields asserted against the parsed artifact by `test_destroyed_model_fixture_matches_the_published_phase19_readings`; `test_gate_self_check_runs_clean_in_a_fresh_interpreter` re-runs the whole self-check as a subprocess twin in CI. |
| GATE-10 | Phase 20 | `_CAPACITY_DISPATCH` is proved TOTAL over all four `(small_cleared, large_cleared)` combinations by a module-scope `_prove`, `CAPACITY_BRANCHES` is closed at five, both named branches were observed firing, and the D-26 fallback raises with the tolerance unset in a message naming D-26. Guarded by `test_capacity_rule_commits_both_branches_and_refuses_the_unset_fallback`. |
| CAL-04 | Phase 20 | phase-zero: K + promotion rule pre-committed |
| RPT-02 | Phase 20 | **DEFERRED to Phase 25 — first half shipped, second half is the unmet conjunction.** The requirement is a conjunction: the helper must *exist* AND *be used for correction sweeps*. `scripts/_prose.py::normalized` exists and is committed at plan `20-03` (`ac4d781`), closing the first half and converting v3.0's `grep -c` lesson into a mechanism. The second half is NOT discharged: routing doc-consistency checks through `normalized` belongs to the phase that runs the first correction sweep. Recorded here rather than only in `20-03-SUMMARY.md`. NOTE — this phase produced FOUR independent instances of the exact defect class RPT-02 exists to close, each caught and worked around rather than papered over: 20-03 (`grep -c "shell=True"` matching 20-01's docstring saying shell=True is never used), 20-04 (`'V20_RETENTION_NOISE_FLOOR' in src` matching the docstring explaining why that name is never imported), 20-05 (a `__doc__` case-sensitivity mismatch), and 20-06 (`0.4921`/`0.3483`/`0.005214448168350039` present as source substrings inside comments stating those values must never be used). Every audit in `tests/test_phase20_prereg.py` is consequently an AST walk or goes through `normalized` — no `grep -c` or `in src` audit was committed. |
| UNIT-01 | Phase 21 | |
| UNIT-02 | Phase 21 | |
| UNIT-03 | Phase 21 | |
| UNIT-04 | Phase 21 | |
| UNIT-05 | Phase 21 | |
| UNIT-06 | Phase 21 | |
| DPSGD-01 | Phase 22 | |
| DPSGD-02 | Phase 22 | |
| DPSGD-03 | Phase 22 | |
| DPSGD-04 | Phase 22 | |
| DPSGD-05 | Phase 22 | |
| DPSGD-07 | Phase 22 | |
| CAL-01 | Phase 23 | |
| CAL-02 | Phase 23 | |
| CAL-03 | Phase 23 | |
| CAL-05 | Phase 23 | |
| DPSGD-06 | Phase 23 | sigma=0 is the DP arm's first executed run |
| CTRL-03 | Phase 23 | never-taught fresh adapter; depends on nothing, scheduled once |
| ADVT-01 | Phase 24 | |
| ADVT-02 | Phase 24 | |
| ADVT-03 | Phase 24 | |
| CTRL-01 | Phase 25 | run first, as a sweep point |
| CTRL-02 | Phase 25 | run first, as a sweep point |
| FRONT-01 | Phase 25 | |
| FRONT-02 | Phase 25 | |
| FRONT-03 | Phase 25 | |
| FRONT-04 | Phase 25 | |
| CANARY-01 | Phase 26 | |
| CANARY-02 | Phase 26 | |
| RELRN-01 | Phase 27 | |
| RELRN-02 | Phase 27 | |
| RELRN-03 | Phase 27 | |
| RELRN-04 | Phase 27 | |
| RELRN-05 | Phase 27 | |
| RPT-01 | Phase 28 | |
| RPT-03 | Phase 28 | |
