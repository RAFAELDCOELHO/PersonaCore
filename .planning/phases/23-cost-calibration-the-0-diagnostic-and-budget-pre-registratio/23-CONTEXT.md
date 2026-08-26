# Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration - Context

**Gathered:** 2026-08-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Size the sweep from a measurement instead of an assumption, and run the one cheap run that separates
the milestone's most likely honest negative from its most likely silent bug.

**This is the first phase of the milestone that EXECUTES anything.** Phases 20–22 built and proved
machinery entirely on CPU. Every decision below exists because a real run on real hardware has
different failure modes than a green test suite, and because three of the four gray areas discussed
are **pre-registration items** — they must be committed before the first run or they are a post-hoc
peek.

Requirements: CAL-01, CAL-02, CAL-03, CAL-05, DPSGD-06, CTRL-03.

</domain>

<decisions>
## Implementation Decisions

### Execution venue — and what the venue owes in evidence

- **D-01: Phase 23 executes on local M3/MPS.** Consistent with CLAUDE.md's primary-path designation
  and with the fully-on-device thesis the project publishes. Kaggle P100 remains the documented
  fallback but is not the venue for the milestone's headline runs.

- **D-02: Before the first real run (σ=0), a dedicated Phase-23 task RE-WATCHES on MPS:** DPSGD-05's
  kill→resume bit-identity proof, and all four DPSGD-04 fake probes (wrong sensitivity, RNG reuse,
  clip-the-averaged-gradient, noise-after-averaging). **Full RED-then-GREEN in the real execution
  environment — not inherited from the CPU pass.** Phase 22's CPU-only result is recorded explicitly
  as *"not transferred to MPS"*, never as *"assumed equivalent"*.

  **Why this is not optional, measured rather than argued:** the DP generator's state is
  **5,056 bytes on CPU and 44 bytes on MPS**, and a CPU generator **refuses** an MPS state outright
  (`RuntimeError: Expected either a CPUGeneratorImplStateLegacy of size 5048…`). Phase 22 proved
  kill→resume bit-identical ε on **CPU** — 22-07-SUMMARY.md's table shows 5,056 bytes in both
  columns. That proof does not transfer. DPSGD-05 is a shipped, verified success criterion that has
  never been watched on the venue which would produce the published ε.

  **SCOPE WARNING FOR THE PLANNER — this is larger than "re-run the probes".**
  `tests/test_phase22_fakes.py` has **no device plumbing at all** (its single `mps` match is a string
  literal inside a ledger row), and `tests/test_phase22_checkpoint.py`'s own module docstring reads
  *"CPU-only, GPU-free, no network. One MPS-touching test is `skipif`-gated."* The Phase-22 battery is
  CPU-only **by design**. D-02 therefore means **device-parametrize probes written CPU-only, then run
  them on MPS** — size it honestly in the plan rather than discovering it mid-execution.

### The σ=0 diagnostic (DPSGD-06 / SC1)

- **D-03: The seed-to-seed noise floor is MEASURED, then pinned.** Run the unmitigated control at
  N seeds (3–5) **before** the σ=0 run, compute the spread, and commit it as the floor in
  `scripts/mitigation_budget.py` with a `_PROVENANCE` sibling — the same pattern Phase 20 used for
  its gate constants. The floor becomes a measurement rather than an assumption, and **the execution
  order structurally guarantees it cannot be tuned after seeing σ=0's number** — not a promise not to
  tune it.

- **D-04: A breach of that floor means the DP code is wrong, and the pre-registration commits to
  HALTING the entire sweep** — zero noised points run — until the cause is root-caused and fixed.
  Every correctness bug in this class *improves* utility, so a σ=0 that beats or misses the control
  is the signal, not noise. The asymmetry is the reason: stop-and-fix is reversible,
  publish-compromised is not.

### CAL-03 — "ε is independent of N at q=1"

- **D-05: The decision rule is bit-identical ε between n_facts=8 and n_facts=64 at fixed σ, AND the
  composed step count T asserted equal directly.** Never a relative tolerance.

  **The instrument follows from a measured fact:** `epsilon_for(sigma, steps, delta)` takes **no N
  parameter** — ε is independent of N *by construction of the accountant*, so this run cannot test
  the math. It tests the **wiring**: whether N leaks into T. The two arms are therefore the same call
  shape at fixed σ, not two independent mathematics, and any tolerance would admit exactly the leak
  the check exists to catch. Phase 22 rejected this same reasoning once already, in DPSGD-05, citing
  `lora/inject.py:113-118` — *"a tolerance would only weaken this."*

  The T assertion **adds no detection power** (ε is monotone in T at fixed σ, so ε equality already
  implies T equality). It exists to name **where** a leak lives when one fires, instead of only that
  one exists.

- **D-06: If CAL-03 comes back falsified, the n=64 leg is NOT committed** — withdrawn, with the
  measurement that withdrew it recorded. **The n=8 leg stays intact and publishable**, its ε correct
  regardless of the leak. The milestone ships a single-capacity frontier rather than halting
  everything: a data-path wiring bug does not indict the DP mechanism itself, which is the scope
  distinction that separates this from D-04's halt rule.

### Resume — closing WARNING-2

- **D-07: `resume_from` is wired through `train_arm`, and `refuse_if_exists` gains a resume-aware
  branch.** Same additive-seam shape already validated twice in Phase 22 by `dp_fn=` and `fact_bin=`.

  **The mechanism is already proven and does not need inventing:** MPS generator state
  round-trips **bit-identically** through `torch.save`/`set_state`, verified both from a fresh seed
  and **mid-stream** — which is what a real resume does. This is production wiring over verified
  machinery, not new risky capability. It closes WARNING-2 and gives DPSGD-05 a real production path
  that exercises it, instead of repeating IN-04's pattern (a seam built and never connected).

### Claude's Discretion

- Sweep width and the concrete Z values in `scripts/mitigation_budget.py` — these are outputs of
  CAL-01/CAL-05's measurements, not choices to be made in advance. The AST guard forbidding the gate
  from importing the budget module (SC3) is an implementation shape for the planner.
- Checkpoint frequency for the resume path, and the exact form of the resume-aware
  `refuse_if_exists` branch.
- How the never-taught fresh adapter (CTRL-03) is scheduled — the requirement fixes that it is
  trained once at identical budget and seed protocol and consumed twice.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### The pre-registration and gate machinery
- `scripts/mitigation_accountant.py` — the FROZEN (ε, δ) pin. Zero imports, `GOLDEN_EPSILON`,
  `REQUIRED_FORM`/`REJECTED_FORM`, `NEIGHBOURING`/`SENSITIVITY_MULTIPLIER`. **Never edit** — a closed
  pre-registration has no correction path; corrections are dated additive continuations elsewhere.
- `scripts/mitigation_gate.py` — the three-condition gate. SC3 requires an AST guard making it
  structurally unable to import the new budget module.
- `scripts/mitigation_unit.py` — the privacy unit (Phase 21), including `REPLAY_OUTSIDE_N`.
- `.planning/REQUIREMENTS.md` — CAL-01/02/03/05, DPSGD-06, CTRL-03 text and traceability.

### What Phase 22 shipped and what it proved
- `src/personacore/privacy/accountant.py` — `delta_closed`, `delta_quadrature`, `epsilon_for`,
  `sigma_for`. stdlib `math` ONLY, guarded statically and transitively.
- `src/personacore/privacy/dpsgd.py` — the DP mechanism: per-record global L2 clip, summed
  accumulator, dedicated-generator noise on the sum, `/N` last, one combining write.
- `src/personacore/training/loop.py` — the `dp_fn=` gradient seam and `fact_bin=`/`n_facts=` data
  seam; the resume block D-07 extends.
- `scripts/teach_persona.py::train_arm` — the production DP caller (`dp_n8` / `dp_n64`).
- `.planning/phases/22-.../22-VERIFICATION.md` — the PASSED verdict, plus WARNING-2 (routed here),
  WARNING-4 and WARNING-5 (both open, neither a blocker).
- `.planning/phases/22-.../22-07-SUMMARY.md` — the CPU-only kill→resume proof D-02 must re-watch.
- `.planning/phases/22-.../22-VALIDATION.md` — the validation contract this phase extends.

### Prior calibration precedent
- `scripts/phase18_extraction.py:88-92` — why K may not be reduced after seeing a null (CAL-04's
  reasoning, already closed).
- `scripts/phase16_ladder.py` — `LADDER_CELL_Z` and the family-pricing pattern.
- `.planning/phases/20-.../` — the `_PROVENANCE` sibling pattern D-03 reuses for the noise floor.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **The whole DP path is built and verified** — mechanism, accountant, both seams, production wiring
  on `dp_n8`/`dp_n64`. Phase 23 runs it rather than building it.
- **`checkpoint.py`'s resume infrastructure** — `rng.get("mps")` back-compat, `dp_noise_rng` as an
  `**extra` key, RNG state restored rather than re-seeded. D-07 wires what already exists.
- **`_PROVENANCE` sibling pattern** from Phase 20 — the shape D-03's noise floor follows.

### Established Patterns
- **Additive seams**: every integration in Phase 22 (`dp_fn=`, `fact_bin=`, `replay_*`) is additive
  and proven inert when off. D-07 follows the same shape.
- **Watched-RED guards**: a guard nobody has seen fail is not evidence. D-02 applies this to the
  venue.
- **Retract-in-place**: corrections are dated additive continuations; originals stay standing.
- **Bit-identity over tolerance** where the two sides are the same call shape (D-05's reasoning).

### Integration Points
- `train_arm` → `train(resume_from=)` — the wiring D-07 adds; currently absent (WARNING-2).
- `refuse_if_exists` — blocks re-running a killed DP arm; D-07 gives it a resume-aware branch.
- `scripts/mitigation_budget.py` — **does not exist yet**; created by this phase, and the gate must be
  AST-forbidden from importing it.
- `epsilon_for` / `sigma_for` — imported today only by `privacy/__init__.py`'s lazy re-export and by
  tests. Phase 23's budget module is the accountant's **first production consumer**.

</code_context>

<specifics>
## Specific Ideas

**The stated principle behind D-01/D-02**, in the user's framing: venue choice must come with explicit
verification — *or an explicitly documented assumption, never silence* — that Phase 22's CPU-proven
guards behave equivalently on the real execution venue. Otherwise it repeats the `LADDER_CELL_Z` risk:
guards solid in one context, silently different in the one that actually matters — here with a
published ε at stake rather than a test assertion.

**Measurements taken during this discussion** (reproduce before relying on them; this phase has a
documented history of figures that did not survive re-measurement):
- DP generator state: **5,056 B CPU / 44 B MPS**, mutually refused across devices.
- MPS generator state **round-trips bit-identically** via `torch.save`/`set_state`, including
  mid-stream.
- `epsilon_for` has **no N parameter** — ε is N-independent by construction.
- `tests/test_phase22_fakes.py` has **no device plumbing**; the Phase-22 battery is CPU-only by design.

</specifics>

<deferred>
## Deferred Ideas

- **WARNING-5 (open, inherited from Phase 22):** `delta_quadrature` degrades at large μ, breaching the
  1e-9 two-oracle budget for σ ≤ 0.0789 at the frozen point, worst 3.7936e-09. **Not a blocker and not
  this phase's work** — the closed form is right to 9.6e-14 there, the breach regime is ε ≥ 16,826
  (absence of a guarantee rather than a weak one), it is pre-existing and bit-identical under the
  pre-22-17 predicate, and `delta_quadrature` is **not on the publishing path** (independently
  confirmed: zero callers outside `accountant.py`). Revisit only if a future phase puts it there.
- **WARNING-4 (open, inherited):** 46 further two-oracle disagreements above 1e-9, worst 6.08e-09 at
  δ=6.26e-237 — a different mechanism (cancellation near the representability floor), none above
  δ=1e-12, unreachable given a frozen δ of 1e-5 and `_MIN_TARGET_DELTA = 1e-300`.
- **The frontier sweep itself (FRONT-01)** — Phase 23 sizes and pre-registers it; running it is
  Phase 25's scope.
- **Adversarial extraction-aware training (ADVT)** — Phase 24.

</deferred>

---

*Phase: 23-Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration*
*Context gathered: 2026-08-26*
