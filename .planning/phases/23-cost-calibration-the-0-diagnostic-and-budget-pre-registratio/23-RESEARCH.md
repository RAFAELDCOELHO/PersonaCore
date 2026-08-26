# Phase 23: Cost Calibration, the σ=0 Diagnostic, and Budget Pre-Registration — Research

**Researched:** 2026-08-26
**Domain:** MPS execution venue, device-parametrized test batteries, AST import guards, wall-clock
methodology on Apple Silicon, additive resume seams
**Confidence:** HIGH on R1/R2/R3/R4 (every load-bearing claim measured in-repo this session);
MEDIUM on R5's Wave-0 gap list (derived, not executed)

**Every number in this document was produced by a command run in this session against this working
tree, or read from a committed file at a named line.** Where a claim rests on training knowledge or
on reasoning rather than a measurement it is tagged `[INFERENCE]`.

---

<user_constraints>
## User Constraints (from 23-CONTEXT.md)

### Locked Decisions

- **D-01: Phase 23 executes on local M3/MPS.** Consistent with CLAUDE.md's primary-path designation
  and with the fully-on-device thesis the project publishes. Kaggle P100 remains the documented
  fallback but is not the venue for the milestone's headline runs.

- **D-02: Before the first real run (σ=0), a dedicated Phase-23 task RE-WATCHES on MPS:** DPSGD-05's
  kill→resume bit-identity proof, and all four DPSGD-04 fake probes (wrong sensitivity, RNG reuse,
  clip-the-averaged-gradient, noise-after-averaging). **Full RED-then-GREEN in the real execution
  environment — not inherited from the CPU pass.** Phase 22's CPU-only result is recorded explicitly
  as *"not transferred to MPS"*, never as *"assumed equivalent"*.

  **SCOPE WARNING FOR THE PLANNER — this is larger than "re-run the probes".**
  `tests/test_phase22_fakes.py` has **no device plumbing at all**, and
  `tests/test_phase22_checkpoint.py`'s own module docstring reads *"CPU-only, GPU-free, no network.
  One MPS-touching test is `skipif`-gated."* The Phase-22 battery is CPU-only **by design**. D-02
  therefore means **device-parametrize probes written CPU-only, then run them on MPS** — size it
  honestly in the plan rather than discovering it mid-execution.

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

- **D-05: The decision rule is bit-identical ε between n_facts=8 and n_facts=64 at fixed σ, AND the
  composed step count T asserted equal directly.** Never a relative tolerance. The two arms are the
  same call shape at fixed σ, not two independent mathematics, and any tolerance would admit exactly
  the leak the check exists to catch. The T assertion adds no detection power; it exists to name
  **where** a leak lives when one fires.

- **D-06: If CAL-03 comes back falsified, the n=64 leg is NOT committed** — withdrawn, with the
  measurement that withdrew it recorded. **The n=8 leg stays intact and publishable**, its ε correct
  regardless of the leak.

- **D-07: `resume_from` is wired through `train_arm`, and `refuse_if_exists` gains a resume-aware
  branch.** Same additive-seam shape already validated twice in Phase 22 by `dp_fn=` and `fact_bin=`.

### Claude's Discretion

- Sweep width and the concrete Z values in `scripts/mitigation_budget.py` — these are outputs of
  CAL-01/CAL-05's measurements, not choices to be made in advance. The AST guard forbidding the gate
  from importing the budget module (SC3) is an implementation shape for the planner.
- Checkpoint frequency for the resume path, and the exact form of the resume-aware
  `refuse_if_exists` branch.
- How the never-taught fresh adapter (CTRL-03) is scheduled — the requirement fixes that it is
  trained once at identical budget and seed protocol and consumed twice.

### Deferred Ideas (OUT OF SCOPE)

- **WARNING-5 (open, inherited from Phase 22):** `delta_quadrature` degrades at large μ. Not a
  blocker and not this phase's work; `delta_quadrature` is not on the publishing path.
- **WARNING-4 (open, inherited):** 46 further two-oracle disagreements above 1e-9, unreachable given
  a frozen δ of 1e-5.
- **The frontier sweep itself (FRONT-01)** — Phase 23 sizes and pre-registers it; running it is
  Phase 25's scope.
- **Adversarial extraction-aware training (ADVT)** — Phase 24.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description (`.planning/REQUIREMENTS.md`) | Research Support |
|----|-------------------------------------------|------------------|
| **CAL-01** | The training leg is measured to complete the pair (~17 s per arm from research, to be confirmed on the DP path with the seam active). | §R3.A — measured at the production shape on MPS. The non-DP figure reproduces (~20.4 s); **the DP arms do not: dp_n8 ≈ 3.8 min, dp_n64 ≈ 30.0 min.** The "~1,010× training" ratio is a property of the non-DP arm only. |
| **CAL-02** | Z (sweep width, per-point K, step budget) committed in a module separate from the gate, separation structurally enforced. | §R2 — the guard **already exists** at `tests/test_phase20_prereg.py:1133` and was WATCHED RED this session. §R2.3 gives the hard import ceiling the new module inherits. |
| **CAL-03** | "ε is independent of N at q=1" confirmed by a run at n_facts=8 vs 64 at fixed σ before the n=64 run is committed. | §R4.4 — `epsilon_for(sigma, steps, delta)` verified to take no N parameter; the instrument is a wiring test on T, and T is measurable by the `_count_composed_steps` shadow already committed. |
| **CAL-05** | Re-measure throughput on one noised adapter; 4.77 h/point is a **floor**, not a mean. | §R3.B — the floor↔ceiling bracket measured directly on the real base: **1.536× wall multiplier**, ceiling **7.33 h/point**. |
| **DPSGD-06** | The σ=0 point is the DP arm's first executed run. | §R1.5 — the D-16 generator invariant verified to hold on MPS at σ=0 (state advances, values exact zero). §R3.C — the control-before-σ=0 ordering. |
| **CTRL-03** | A never-taught fresh adapter at identical budget and seed, consumed twice. | §R3.D — `scripts/mitigation_gate.py:341-437` (FROZEN) requires the extraction floor's provenance to name `arm="never-taught"` with **≥ 2 distinct seeds**. Flagged as an open question against CTRL-03's "trained once". |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

Directives the planner must not contradict:

1. **MPS is the primary path; fp32 only.** No AMP, no `GradScaler`, no `torch.compile` on MPS.
   `RuntimeConfig.__post_init__` forces `amp=False` for `cpu`/`mps` (`src/personacore/config.py:56-59`)
   — verified.
2. **Python 3.11 venv is MANDATORY.** Confirmed live: `.venv/bin/python` is **3.11.15**, `torch`
   **2.7.1**, `torch.backends.mps.is_available()` → `True`.
3. **CSV + matplotlib logging only.** No wandb / network.
4. **GSD workflow enforcement** — edits go through a GSD command.
5. **`checkpoints/` is gitignored**; no test may make an on-disk artifact a precondition. Confirmed
   by `tests/test_phase22_checkpoint.py`'s module docstring and its `skipif` register.
6. **CI is `ubuntu-latest`, CPU wheel** (`.github/workflows/ci.yml:6,36`). **Every MPS leg added in
   this phase must be `skipif`-gated or CI goes red.** Precedent: `tests/test_mps_smoke.py`'s
   module-level `pytestmark`.

---

## Summary

Phase 23's technical risk is not in the DP mathematics — that shipped and was verified in Phase 22.
It is in three places, and this research measured all three rather than reasoning about them.

**First, the venue transfer (D-02) is real but bounded, and the two things that break first are now
known by name.** The Phase-22 battery does not merely lack a `device=` parameter; two of its helper
functions *raise* on MPS. `tests/test_phase22_checkpoint.py:392::_next_draw` raises
`RuntimeError: Placeholder storage has not been allocated on MPS device!` because `torch.normal`
without `device=` cannot use an MPS generator, and `tests/test_phase22_fakes.py:118::_record` raises
`RuntimeError: attempting to assign a gradient with device type 'cpu' to a tensor with device type
'mps'`. Both were reproduced this session. Against that, the substantive machinery transfers: the
D-16 generator continuity invariant works on MPS (state advances at σ=0 while values stay exactly
zero — the exact property DPSGD-06 depends on), the DP generator's `get_state()` returns a **CPU**
tensor on both devices so every `torch.equal` state comparison is device-safe, and the global L2 norm
came back **bit-identical** between CPU and MPS on a 72-tensor LoRA-shaped fixture. The four fake
probes each carry two detectors, and one of the two — the AST half — is a pure `ast.parse` over
source text and cannot differ by device. Saying so is more honest than pretending to device-
parametrize a text scan.

**Second, the SC3 AST guard does not need designing — it was written in Phase 20, it names
`mitigation_budget` by string, and it bites.** `tests/test_phase20_prereg.py:1133::
test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` was watched RED this session
against a scratch module. What the planner does need is the consequence nobody has written down: the
same test asserts `imported <= {"pathlib", "sys", "erasure_gate"}` over the **union** across every
`scripts/mitigation_*.py`, and the glob picks up `mitigation_budget.py` the moment it is created. A
budget module with `import json` in it turns that test RED — measured. The correct shape is the one
`scripts/phase19_floor.py` and `scripts/mitigation_accountant.py` already use: literal assignments,
zero imports.

**Third, the cost model does not survive contact with the DP path, and the direction is unfavourable
in one place and favourable in another.** The eval-vs-training ratio the roadmap quotes — "~1,010×",
"binding by three orders of magnitude" — reproduces for the *non-DP* arm (measured 20.4 s against
the research figure of ~17 s) and collapses for the DP arms, because `grad_accum_steps = n_facts`
makes one optimizer step cost 64 backward passes at n=64 plus 32 replay micro-batches. Measured at
the production shape: **dp_n64 ≈ 30.0 min per arm, not 17 s** — a ratio of ~10×, not 1,010×. In the
other direction the CAL-05 floor is now bracketed by measurement rather than by argument: forcing
every draw to run the full `max_new_tokens=48` costs **1.536×** wall clock, so the ceiling on a
noised point is **7.33 h**, not an unbounded worry.

**Primary recommendation:** Order the phase as *(1) device-parametrize and re-watch → (2) resume seam
→ (3) control at N seeds → (4) σ=0 → (5) CAL-03 → (6) noised-throughput re-measure → (7) pin the
budget*, and write `scripts/mitigation_budget.py` as a zero-import literal-constants file in the
`phase19_floor.py` shape, with the re-derivation test that shape carries.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Device resolution (CUDA→MPS→CPU) | `src/personacore/config.py::RuntimeConfig` + `preflight.py::preflight_device` | — | CLAUDE.md names this the single source of device truth; `teach_persona.train_arm:1214-1216` already calls both. |
| DP mechanism (clip / accumulate / noise / `/N`) | `src/personacore/privacy/dpsgd.py` | — | Frozen and verified in Phase 22. Phase 23 runs it, does not edit it. |
| ε accounting | `src/personacore/privacy/accountant.py` | `scripts/mitigation_accountant.py` (the frozen pin) | Computation in `src/`, published output table in the pin. The pin has **zero imports** and cannot compute — enforced by `test_mitigation_accountant_pin_has_no_executable_formula`. |
| Outcome thresholds (X, Y, C, K rungs, promotion) | `scripts/mitigation_gate.py` — **FROZEN, do not edit** | — | `results/phase20_*` artifacts are committed, so the ancestry guard has closed this file. |
| Resource budget Z (sweep width, K selection, step budget, noise floor) | `scripts/mitigation_budget.py` — **new, this phase** | — | ROADMAP:139-144's gate/budget split. Zero imports (see §R2.3). |
| Production DP driver (train one arm) | `scripts/teach_persona.py::train_arm` | `src/personacore/training/loop.py::train` | D-07's seam lands in `train_arm`; `train(resume_from=)` already exists and is fully wired. |
| Test-battery device parametrization | `tests/test_phase22_*.py` fixtures | `tests/test_mps_smoke.py` (the `skipif` precedent) | D-02's scope. |
| Cost artifacts | `results/phase23_*` | — | Watched by the ancestry guard at `tests/test_phase20_prereg.py:332`. |

---

## R1. Device-parametrizing the CPU-only Phase-22 probe battery onto MPS (D-02)

### R1.0 — Confirming the premise

`grep -n "mps\|device" tests/test_phase22_fakes.py` returns **exactly one line**:

```
801:    ('rng["mps"] is required-but-UNEXERCISED in CPU-only CI', 'rng["mps"]'),
```

That is a string literal inside `_LEDGER` rows, not device plumbing. `grep -c '"cpu"'` on the same
file returns **0** — the file passes no device anywhere. `tests/test_phase22_checkpoint.py:3` reads
verbatim: *"CPU-only, GPU-free, no network. One MPS-touching test is `skipif`-gated."*

**CONTEXT.md's fourth `<specifics>` measurement is REPRODUCED and HOLDS.** `[MEASURED]`

Battery sizes, counted by `grep -c "^def test_"`:

| File | test fns | `"cpu"` literals | Device-relevant? |
|------|---------:|-----------------:|------------------|
| `tests/test_phase22_fakes.py` | 8 | 0 | 4 fake probes: runtime halves yes, AST halves no. 4 ledger/meta tests: no. |
| `tests/test_phase22_checkpoint.py` | 9 | 8 | V-15 (`test_resume_epsilon_bit_identical`, ×2 params) yes; V-16/V-17 partly. |
| `tests/test_phase22_dpsgd.py` | 23 | 9 | Owns the shared `_model()` fixture. |
| `tests/test_phase22_dpsgd_ast.py` | 16 | 0 | **None** — pure `ast.parse` over source text. |
| `tests/test_phase22_wiring.py` | 20 | 7 | Not in D-02's named scope. |
| `tests/test_phase22_accountant.py` | 37 | 0 | **None** — stdlib `math` only, no torch. |

### R1.1 — What breaks FIRST, measured

Two helpers raise outright on MPS. Both reproduced this session with `torch 2.7.1`:

**(a) `tests/test_phase22_checkpoint.py:392::_next_draw`**

```python
return torch.normal(mean=0.0, std=1.0, size=(16,), generator=dp._g)
```

With `dp._g` an MPS generator:

```
RuntimeError: Placeholder storage has not been allocated on MPS device!
```

Adding `device="mps"` makes it succeed and return an `mps:0` tensor. `[MEASURED]`

**(b) `tests/test_phase22_fakes.py:118-127::_record`**

```python
gen = torch.Generator().manual_seed(seed)          # CPU generator
g = torch.randn(p.shape, generator=gen) * _GRAD_SCALE   # CPU tensor
p.grad = g if p.grad is None else p.grad + g
```

With `p` on MPS:

```
RuntimeError: attempting to assign a gradient with device type 'cpu' to a tensor with
device type 'mps'. Please ensure that the gradient and the tensor are on the same device
```

and the accumulate branch raises separately:

```
RuntimeError: Expected all tensors to be on the same device, but found at least two
devices, mps:0 and cpu!
```
`[MEASURED]`

**The cheap fix for (b) is load-bearing, not cosmetic.** `_record` feeds two probes that assert on
*fitted numeric constants*: `_FAKE1_LEAK_RATIO = 1.734481` (band `0.02`,
`tests/test_phase22_fakes.py:174-175`) and `_FAKE3_STD_RATIO_AT_N4 = 3.999986` (band `0.01`,
`:468-469`). Drawing on an MPS generator instead of a CPU one produces **different gradient values**
and would put those constants at risk for a reason that has nothing to do with the fake. Keep the CPU
draw and move the result: `p.grad = g.to(device)`. The bytes are then identical to the CPU run and
the constants stay valid by construction.

### R1.2 — The shared fixture, and the blast radius of touching it

`tests/test_phase22_dpsgd.py:121`:

```python
def _model(*, freeze=True):
    """A real GPT + real LoRA on CPU; ``freeze=False`` is D-04 trap 1's positive control."""
```

`tests/test_phase22_fakes.py:46-50` imports it (`from test_phase22_dpsgd import _FROZEN_PARAMS,
_GRAD_SCALE, _model`). It takes no `device` and never calls `.to()`. Widening it to
`_model(*, freeze=True, device="cpu")` with a `.to(device)` is a **one-line additive widening whose
default is byte-identical to today** — the `dp_sigma=None` sentinel shape `train_arm` already uses —
but it is in the blast radius of **31 tests** across two files. That is the honest size.

### R1.3 — What transfers unchanged (measured, not assumed)

These are the pleasant surprises, and each one removes a chunk of the plan's risk:

| Property | CPU | MPS | Verdict |
|---|---|---|---|
| `Generator.get_state()` dtype/device | `uint8`, **on CPU**, 5056 B | `uint8`, **on CPU**, 44 B | Every `torch.equal(state_a, state_b)` in `dpsgd.py` and in the tests compares two CPU tensors. **Device-safe as written.** `[MEASURED]` |
| `torch.normal(std=0.0)` returns exact zeros | ✅ | ✅ | `[MEASURED]` |
| `torch.normal(std=0.0)` **advances** the generator | ✅ | ✅ at sizes 1, 2, 4, 8, 16 and at 4608 | **This is the DPSGD-06 keystone** — see §R1.5. `[MEASURED]` |
| `_global_norm` over 72 LoRA-shaped tensors | `0.4707888662815094` | `0.4707888662815094` | **BIT-IDENTICAL** on this fixture. `[MEASURED]` |
| `RuntimeConfig(device="mps")` forces `amp=False` | n/a | ✅ (`config.py:56-59`) | D-04 refusal 2 (live scaler) stays inert on MPS, exactly as on CPU. `[MEASURED]` |
| The four fakes' **AST halves** | run | *identical* | `ast.parse` over source text has no device. Re-running is a no-op; record it as such. `[INFERENCE]` — trivially, from reading `tests/test_phase22_dpsgd_ast.py`, which imports no torch runtime. |

The bit-identical norm is **one fixture, not a proof**. Fp32 reductions can differ in the last ULPs
by reduction order. But the two probes that depend on float agreement carry bands of 0.02 and 0.01 —
roughly 1% — against a divergence bounded well below that. `[INFERENCE]`

### R1.4 — The 5,056 B / 44 B divergence, per probe

**CONTEXT.md's first `<specifics>` measurement is REPRODUCED and HOLDS**, including the error text:

```
cpu: state dtype=torch.uint8 numel=5056 bytes=5056 device=cpu
mps: state dtype=torch.uint8 numel=44   bytes=44   device=cpu
CPU<-MPS REFUSED: RuntimeError Expected either a CPUGeneratorImplStateLegacy of size 5048
                  or a CPUGeneratorImplState of size 5056 but found the input RNG state size to be 44
MPS<-CPU REFUSED: RuntimeError RNG state is wrong size
```
`[MEASURED]`

How the divergence interacts with each of the five things D-02 re-watches:

| Probe | Interaction with the size divergence | Consequence |
|---|---|---|
| **V-15 kill→resume ε bit-identity** (`test_resume_epsilon_bit_identical`) | The checkpoint's `dp_noise_rng` is written on MPS (44 B) and read back on MPS. `torch.save`/`set_state` round-trips it bit-identically (§R1.6). A checkpoint written on CPU cannot be resumed on MPS and vice versa — **and torch refuses loudly rather than silently.** | Wire it; the refusal is a feature. Add a test that a CPU-written `dp_noise_rng` resumed under an MPS seam raises, so the cross-device boundary is *watched* rather than assumed. |
| **FAKE 1 — clip the averaged gradient** | No generator involvement. Blocked only by `_record`'s grad assignment (§R1.1b). | Fix `_record`; ratio constant preserved by the `.to(device)` route. |
| **FAKE 2 — wrong sensitivity** | AST half device-free. Runtime half reads `self.C` / a second constant; no generator. | Lowest-risk of the four. |
| **FAKE 3 — noise after averaging** | Depends on the **magnitude differential** between `(S+noise)/N` and `S/N + noise`, which is a property of the drawn values. Drawn from `dp._g` on the *model's* device, so on MPS the noise values differ from CPU. The differential is a **ratio at fixed N**, so it is scale-invariant, and `_FAKE3_STD_RATIO_AT_N4 = 3.999986 ≈ N` is a structural constant, not a fitted one. | Expect the band to hold; **it must be re-measured on MPS to say so.** This is the single numeric constant most worth watching in the MPS pass. |
| **FAKE 4 — RNG reuse across steps** | Directly on the generator: `_prev_gen_state` continuity via `torch.equal(pre, post)` over 44-byte CPU tensors. | Works as written (§R1.3 row 1). |

### R1.5 — The DPSGD-06 keystone

`dpsgd.py:531-539` refuses when `torch.equal(pre, post)` — *"the generator state did not advance
across the draws, so the draw did not happen"*, with the comment *"At sigma = 0 the values are exact
zeros BUT the state still moves (measured, torch 2.7.1)"*. That measurement was taken on **CPU**.
DPSGD-06 makes σ=0 the **first executed run**, on **MPS**. If the 44-byte MPS state did not advance
at `std=0.0`, the milestone's first real run would refuse at every step.

Measured on MPS, torch 2.7.1:

```
=== mps ===
  std=0.0: state_advanced=True  all_zeros=True  numel=4608
  std=1.0: state_advanced=True  all_zeros=False numel=4608
  std=0 size=1..16: advanced=True at every size
```

**The invariant holds on MPS. DPSGD-06 will not refuse for this reason.** `[MEASURED]`
The planner should still commit this as a **first task** in the MPS pass, because it is the one
property whose failure would abort the phase's headline run, and a measurement recorded in a research
doc is not a committed test.

### R1.6 — MPS generator round-trip (D-07's mechanism)

**CONTEXT.md's second `<specifics>` measurement is REPRODUCED and HOLDS:**

```
fresh bytes equal: True    fresh stream equal: True
mid   bytes equal: True    mid   stream equal: True     (mid state numel: 44, uint8)
```
`[MEASURED]` — via `torch.save`/`torch.load` to disk plus `set_state`, both from a fresh seed and
after advancing the stream 10 draws.

### R1.7 — Honest sizing for the plan

**Code touchpoints, exhaustive:**

1. `tests/test_phase22_dpsgd.py:121::_model` — add `device="cpu"` kwarg + `.to(device)`. Blast radius 31 tests.
2. `tests/test_phase22_fakes.py:118::_record` — `p.grad = g.to(device)` (keep the CPU draw).
3. `tests/test_phase22_checkpoint.py:392::_next_draw` — add `device=`.
4. `RuntimeConfig(device="cpu")` → parametrized: 3 sites in `test_phase22_checkpoint.py` (`:290, :337, :357`), 6 sites in `test_phase22_dpsgd.py`.
5. `torch.load(..., map_location="cpu")` — 4 sites; **leave alone**, `load_checkpoint` handles placement and the RNG states are CPU tensors anyway.
6. Parametrization gate: `@pytest.mark.skipif(not torch.backends.mps.is_available(), reason=...)` on the MPS leg only. **CI is `ubuntu-latest`** (`.github/workflows/ci.yml:6`) and would otherwise go red. Precedent: `tests/test_mps_smoke.py`'s module-level `pytestmark`.

**Recommended parametrization shape:** `@pytest.mark.parametrize("device", _DEVICES)` where
`_DEVICES = ["cpu"] + (["mps"] if torch.backends.mps.is_available() else [])`. This keeps the CPU
leg unconditional (so no coverage is lost in CI) and adds the MPS leg only where it can run — the
`pytest.param(..., marks=skipif(...))` register `tests/test_phase22_checkpoint.py:671` already uses.

**Watched-RED obligation.** D-02 says *full RED-then-GREEN in the real execution environment*. For
the four fakes that means re-applying each mutation **with `device="mps"`** and observing the RED,
in-process, the way `tests/test_phase22_fakes.py` already does on CPU. The AST halves are exempt and
the exemption should be **written into the plan and the ledger**, not silently skipped — a probe that
claims a device pass it did not perform is exactly the defect D-02 exists to prevent.

**What is NOT in scope for D-02:** `tests/test_phase22_dpsgd_ast.py` (16 tests, no torch) and
`tests/test_phase22_accountant.py` (37 tests, stdlib `math` only). Neither can differ by device.
Excluding them removes 53 of the 113 Phase-22 tests from the parametrization surface.

---

## R2. The AST import-guard shape for SC3 (CAL-02)

### R2.1 — The guard already exists, and it names `mitigation_budget` by string

**Search run:** `grep -rn "import ast|ast.parse|ast.walk" tests/ scripts/ src/`, then
`grep -n "_GATE_MODULES" tests/test_phase20_prereg.py`.

**Found:** `tests/test_phase20_prereg.py:1133::test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only`

Its first of four claims (`:1170-1183`):

```python
assert "mitigation_budget" not in imported, (
    f"a mitigation_*.py module imports mitigation_budget (imports: {sorted(imported)}). The "
    "GATE holds OUTCOME thresholds and the BUDGET holds RESOURCE parameters, and "
    "`.planning/ROADMAP.md:139-144` requires that separation to be structurally enforced ..."
)
```

The register it scans, `tests/test_phase20_prereg.py:72-73`:

```python
_MITIGATION_GATE_PATH = _ROOT / "scripts" / "mitigation_gate.py"
_GATE_MODULES = tuple(sorted((_ROOT / "scripts").glob("mitigation_*.py")))
```

and `:64-71` records **why** it is a glob, in Phase 20's own words:

> *"the other established form is a hand-listed tuple … and that is exactly the F-08 blindness the
> glob register was introduced to CLOSE: Phase 23's `scripts/mitigation_budget.py` would sit silently
> uncovered until someone remembered to add it, and the one guard that must never be forgotten is the
> one forbidding the gate from importing it."*

**Recommendation: do not invent a guard. The mechanism is committed, it is named for this exact
file, and Phase 23's obligation is to make it non-vacuous and to WATCH it.**

### R2.2 — Watched RED this session

The assertion is vacuously green today (no such module exists). Watched failing:

```bash
# scratch: scripts/mitigation_budget.py  ->  Z_SWEEP = ()
# scratch: scripts/mitigation_zzprobe.py ->  import mitigation_budget
$ .venv/bin/python -m pytest tests/test_phase20_prereg.py -k import_graph
E  AssertionError: a mitigation_*.py module imports mitigation_budget
   (imports: ['erasure_gate', 'mitigation_budget', 'pathlib', 'sys'])
1 failed, 24 deselected
```
Both scratch files deleted; `git status --short scripts/` → clean. `[MEASURED]`

### R2.3 — The consequence nobody has written down: the budget module inherits a hard import ceiling

The same test asserts, over the **union across every `mitigation_*.py`** (`:1182`):

```python
allowed = {"pathlib", "sys", "erasure_gate"}
assert imported <= allowed
```

Measured import surfaces today:

| Module | Imports |
|---|---|
| `scripts/mitigation_accountant.py` | **none** |
| `scripts/mitigation_unit.py` | **none** |
| `scripts/mitigation_gate.py` | `pathlib`, `sys`, `erasure_gate` (`:49-57`) |

So the union is *exactly* the allow-set — **zero headroom**. Watched RED this session with a scratch
budget module containing `import json`:

```
E  AssertionError: the mitigation modules import ['json'] beyond the allow-set
   ['erasure_gate', 'pathlib', 'sys'].
   Extra items in the left set: 'json'
tests/test_phase20_prereg.py:1182: AssertionError
```
`[MEASURED]`

**Consequences for CAL-02's implementation, in priority order:**

1. **`scripts/mitigation_budget.py` must have zero imports.** No `json`, no `math`, no
   `dataclasses`, no `pathlib` unless it genuinely needs one of the three allowed names. The
   precedents are already in the tree: `mitigation_accountant.py` and `mitigation_unit.py` both
   import nothing.
2. **The budget module may not import the gate either.** `import mitigation_gate` would add
   `mitigation_gate` to `imported` and break the subset assertion. If the budget needs to *reference*
   `K_RUNGS`, it must restate the selected rung as a literal with a provenance comment naming
   `scripts/mitigation_gate.py::K_RUNGS`, and a **test** must assert the two agree. (Alternative:
   widen `allowed` — but that weakens a committed guard, and the widening would have to be justified
   in the plan, not slipped in.)
3. **A dynamic-import escape is already closed by the subset assertion**, not by the negative one:
   `importlib.import_module("mitigation_budget")` would require `import importlib`, which the subset
   assertion rejects. Worth recording; it means the static scan is stronger than it looks. `[INFERENCE]`
4. **The one genuine hole:** the scan covers only `scripts/mitigation_*.py`. `scripts/erasure_gate.py`
   is not in the glob (it imports only `math`, `:68`), so a transitive route
   *gate → erasure_gate → budget* would be invisible to this guard. Contrast the accountant's
   guard (`tests/test_phase22_accountant.py:1350::test_accountant_imports_math_only`), which pairs a
   static AST half with an **out-of-process** transitive probe:

   ```python
   probe = ("import importlib.util, sys;"
            f"spec = importlib.util.spec_from_file_location('acct', {relative!r});"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
            "bad = [n for n in ('torch','numpy','scipy','mpmath') if n in sys.modules];"
            "print(bad); sys.exit(1 if bad else 0)")
   subprocess.run([sys.executable, "-c", probe], cwd=_ROOT, ...)
   ```

   **This is the extension the planner should make.** The project's own standard for the accountant is
   *"guarded statically AND transitively"*; the gate/budget guard currently meets only the static
   half. A transitive half is ~12 lines, reuses a proven local shape, and closes the erasure_gate
   route: exec `mitigation_gate.py` out of process and assert `"mitigation_budget" not in sys.modules`.

### R2.4 — Hard constraint: `scripts/mitigation_gate.py` is FROZEN

```bash
$ git ls-files 'results/phase20_*'
results/phase20_gate_coverage_correction.json
results/phase20_gate_coverage_correction.md
results/phase20_retention_floor.json
```

Three committed `results/phase20_*` artifacts exist. `test_phase20_prereg_is_frozen_before_every_
phase20_result` (`:268`) requires every commit touching `scripts/mitigation_gate.py` to be a **strict
ancestor** of every artifact's earliest add, and `_assert_ordering_holds` takes `adds[-1]` — the
earliest add — so a `git rm` + re-add cannot launder it. `mitigation_gate.py:1-18` says so in its own
words: *"There is no recovery path and no force flag."*

**Phase 23 must not edit `scripts/mitigation_gate.py`.** Everything the phase needs from it is
already there: `K_RUNGS = (48, 24, 16, 8)` with the ratchet (`:248-255`), `ratchet_k`,
`promote_to_full_fidelity(*, verdict, reasons, curve_k, full_k)` (`:963`), `NEVER_TAUGHT_ARM`
(`:341`), `EXTRACTION_FLOOR_MIN_SEEDS = 2` (`:346`).

The gate's own docstring at `:248-252` already anticipates this phase:

> *"Phase 23 SELECTS the rung by measured throughput (CAL-05: 4.77 h/point is a FLOOR for noised
> points, not a mean …). RATCHET: a selected rung may only INCREASE, never decrease."*

### R2.5 — The second ancestry constraint, on `results/phase23_*`

`tests/test_phase20_prereg.py:332::test_phase22_prereg_is_frozen_before_every_phase23_result` binds
`scripts/mitigation_accountant.py` as a strict ancestor of every `results/phase23_*` artifact.
`git ls-files 'results/phase23_*'` returns **nothing** today, so the guard is vacuous — and it stops
being vacuous at the first committed Phase-23 artifact.

**Two obligations follow:** (a) `scripts/mitigation_accountant.py` must stay byte-unchanged through
Phase 23 — CONTEXT.md already says *"Never edit"*, and this is the mechanism that enforces it;
(b) every Phase-23 results artifact must be named `results/phase23_*` or it falls outside the guard
entirely.

### R2.6 — The `_PROVENANCE` shape SC3 asks for

Two precedents, and the second is the closer match to what D-03 needs:

- **`scripts/mitigation_accountant.py:335::GOLDEN_EPSILON_PROVENANCE`** — the sibling-constant naming
  pattern SC3 references directly.
- **`scripts/phase19_floor.py`** — the structurally correct model for a *post-artifact measured
  constant*, which is exactly what D-03's noise floor is. Its docstring (`:1-42`) states the three
  properties that make a sanctioned post-artifact write honest:
  1. an ancestry guard against every TARGET artifact,
  2. **every constant RE-DERIVES on every suite run** through the pinned function from the committed
     artifact (`test_floor_lock_re_derives_all_three_constants_from_their_evidence_artifacts`) — *"a
     hand-edited number goes red"*,
  3. **literal assignments and nothing else** — no rule, no estimator, no report text, **no import**
     (`test_floor_lock_holds_only_literal_constants_and_nothing_else`).

Property (3) also happens to satisfy §R2.3's import ceiling for free. **Recommend
`scripts/mitigation_budget.py` be built in the `phase19_floor.py` shape, with its re-derivation
test.**

For the artifact `_PROVENANCE` points at, `results/phase19_noise_floors.json` is the committed shape:
`git_sha`, `record`, `record_sha256`, `recipe` (arm_spec, arms, n_facts, prefix, replay_ratio,
second_person), `estimator`, `reduction`, `governs`, plus per-seed readings. SC3 asks for *"`_PROVENANCE`
siblings naming the cost artifact and its sha256"* — that JSON already carries both fields.

---

## R3. Wall-clock and generation-throughput measurement methodology on MPS (CAL-01, CAL-05)

### R3.0 — Where the committed figures actually live

**Search run:** `grep -rn "4\.77|42480|145\.01|84,960|9\.54 h|draws/min" results/ scripts/ .planning/*.md`

| Figure | Location | Status |
|---|---|---|
| Per-shape rates 145.01 / 134.54 / 183.20 / 140.85 draws/min | `results/phase18_preflight_report.md:35-38` | Committed, with provenance (git_sha `99716e08…`, pid 76739, seed 1337, corpus sha256, `device: mps`, `torch 2.7.1`) |
| **45–56 of 64 stop-terminated** | `results/phase18_preflight_report.md:23-28` — the table reads 56/64, **45/64**, 56/64, 51/64 | Committed. **The 45–56 range is exact.** |
| 84,960 draws / 9.54 h both arms | `results/phase18_preflight_report.md:79` | Committed |
| **4.77 h/point** | *Not in `results/`.* Derived. Stated at `.planning/REQUIREMENTS.md:~178`, `.planning/STATE.md:493`, `scripts/mitigation_gate.py:248` | **Derived from the committed report** — see reproduction below |
| `K = 48`, `ASR_RUNGS = (1, 4, 16, K)` | `scripts/phase18_extraction.py:93-96` | Committed |
| `max_new_tokens = 48` | `phase14_recall.RECALL_MAX_NEW_TOKENS`, consumed at `phase14_recall.py:600` | Committed |
| `STOP_IDS = frozenset({8184, 8185})` | `phase14_recall.STOP_IDS`, consumed at `:602` | Committed |

**Reproduction of 4.77 h/point** from the committed report's own rows:

```
A1-mild        20736 / 145.01 =  143.00 min   (report: 143.0)
A1-aggressive  20736 / 134.54 =  154.13 min   (report: 154.1)
A2             20736 / 183.20 =  113.19 min   (report: 113.2)
A3             20736 / 140.85 =  147.22 min   (report: 147.2)
A0              2016 / 134.54 =   14.98 min   (report: 15.0)
TOTAL   84960 draws, 572.51 min = 9.5419 h    (report: 84960 draws, 9.54 h)
PER ARM 42480 draws, 286.26 min = 4.7710 h    (roadmap: 42,480 draws = 4.77 h)
```

**Both reproduce exactly.** `[MEASURED]`

### R3.A — CAL-01: training wall-clock on the DP path with the seam active

### The synchronization question, answered from the code rather than assumed

`torch.mps.synchronize` **exists** in the installed torch 2.7.1 (`hasattr(torch.mps, 'synchronize')`
→ `True`; `dir(torch.mps)` also lists `get_rng_state`, `set_rng_state`, `manual_seed`,
`current_allocated_memory`, `Event`). `[MEASURED]` — CONTEXT.md asked this be verified, not assumed.

But **the generation loop is already implicitly synchronized every token.**
`src/personacore/generation/core.py:79`:

```python
tok = int(next_id)          # <- a device->host sync, once per generated token
if tok in stops:
    return
```

So Phase 18's `time.time()` bracket around a draw loop (`phase18_extraction.py:3156, 3189`) measures
real completed work, not queued work. **The committed rates are honest.** `[MEASURED]` — from reading
the loop, corroborated by §R3.B reproducing 145.01 within 1.5% on the same hardware.

**Recommendation:** call `torch.mps.synchronize()` once *before* `t0` and once *before* `t1` at every
timing boundary anyway. It is two lines, it makes the measurement correct independent of whether a
future refactor removes the per-token `int()`, and for training (which has no per-step host sync at
all) it is **not** optional.

### Warm-up and steady-state discipline

The first MPS kernels of a process pay lazy compilation and allocator warm-up. Measured in this
session's probes: 3–4 discarded warm-up iterations were enough for the per-micro-step figure to
stabilize. **Recommend: discard the first ≥4 iterations, then time ≥20, and record both the mean and
the count** — a rate with no denominator is exactly the kind of figure this project has had to retract.

### The measurement, at the production shape

`scripts/teach_persona.py`: `MAX_STEPS = 200` (`:1128`), `BATCH_SIZE = 8` (`:1122`),
`BLOCK_SIZE = 256` (`:104`), `LORA_CFG = LoRAConfig()` (`:1111`) → 72 trainable tensors / 331,776
params (asserted live). `dp_accum = dict(grad_accum_steps=stats["n_facts"])` (`:1352`) — **one
optimizer step is `n_facts` micro-batches.** `replay_windows = replay_window_budget(n_facts) //
BLOCK_SIZE` with `REPLAY_WINDOWS_PER_FACT = 4` (`:178`) → `4 * n_facts` windows, drawn in
`ceil(4*n_facts / batch_size)` extra micro-batches per step (`training/loop.py:685-699`).

Measured on MPS, real `GPT(ModelConfig())` + real `inject_lora` + real `DPSGD`, at batch 8 × block 256:

```
trainable tensors: 72   params: 331776
bare micro fwd+bwd     :    89.37 ms
micro + absorb_record  :    95.58 ms   (DP per-record overhead 6.21 ms, +6.9%)
finalize (per opt step):     3.39 ms
optimizer.step()       :    12.50 ms
```
`[MEASURED]`

Projected to `MAX_STEPS = 200`, including the replay pass:

| Arm | micro-batches/step | ms/step | **total** | eval(4.77 h) ÷ train |
|---|---|---:|---:|---:|
| non-DP (accum=1) | 1 | 101.9 | **20.4 s** | **843×** |
| `dp_n8` (accum=8) | 8 DP + 4 replay | 1138.0 | **227.6 s ≈ 3.79 min** | **75×** |
| `dp_n64` (accum=64) | 64 DP + 32 replay | 8992.8 | **1798.6 s ≈ 29.98 min** | **9.5×** |

### The finding CAL-01 exists to produce

`.planning/REQUIREMENTS.md` states: *"Training is ~17 s per arm. **Evaluation costs ~1,010×
training** — it is the binding constraint by three orders of magnitude."*

- The **~17 s** figure reproduces for the **non-DP** arm: measured 20.4 s (+20%, well inside a
  synthetic-vs-real gap).
- The **1,010×** ratio reproduces for the **non-DP** arm: measured 843×.
- **Neither survives the DP path.** `dp_n64` is ≈ **30 min**, and the ratio drops to **9.5×** — one
  order of magnitude, not three.

Evaluation is still the binding constraint, so **no locked decision changes**. But the roadmap's
"binding by three orders of magnitude" is a statement about a *non-DP* arm and CAL-01's honest output
is to say so and record the DP figures separately. A 16-point sweep's training leg is 16 × 30 min =
**8 h at n=64**, which is not free.

**Bounding.** The projections above are a **LOWER BOUND on the training leg**: they exclude
`build_arm_bins`, the 20 in-loop evals (`EVAL_INTERVAL = 10`), 4 checkpoint writes
(`CHECKPOINT_INTERVAL = 50`), the memmap I/O in the replay pass, and the two end-of-run
`masked_perplexity` sweeps. **CAL-01 must confirm against one real `train_arm` run**; this research
gives the plan a sized expectation, not a substitute.

### R3.B — CAL-05: generation throughput, and the floor↔ceiling bracket

### The measurement

Because generation is a per-token Python loop at batch 1 (`generation/core.py:64-80`), wall clock is
close to linear in tokens emitted. The floor-vs-mean question is therefore directly measurable:
run the same draws with `STOP_IDS` active (the Phase-18 condition, the FLOOR) and with the stop set
emptied (the worst case a noised adapter that stops emitting EOS produces, the CEILING).

Run on the real base — `checkpoints/convbase_slim.pt` via
`phase17_persona_gate.build_unadapted_base("mps")`, base git_sha `04e724c67033`, step 4000 — at
`SAMPLE_TEMPERATURE`/`SAMPLE_TOP_P`, `RECALL_MAX_NEW_TOKENS = 48`, with the committed `forbid_ids`
mask, 4 warm-up draws discarded, N = 64 per condition, `torch.mps.synchronize()` at both boundaries:

```
STOP ACTIVE :  26.09s   147.21 draws/min  mean_tokens=27.41  stopped=60/64
FULL 48     :  40.07s    95.84 draws/min  mean_tokens=48.00  stopped= 0/64

MULTIPLIER (wall)  : 1.536x
MULTIPLIER (tokens): 1.751x
```
`[MEASURED]`

### What this gives the planner

1. **Cross-validation of the committed artifact.** 147.21 draws/min against
   `results/phase18_preflight_report.md:35`'s 145.01 for A1-mild — **1.5% agreement**, on the same
   device, same torch, ~5 weeks later. The committed cost artifact holds up.
2. **The CAL-05 ceiling is 1.536×**, so the noised point is bounded at
   **4.77 h × 1.536 = 7.33 h/point**. A 16-point K=48 sweep is bounded at **117 h**, against the
   76.3 h the roadmap's table quotes at the floor.
3. **Why wall (1.536×) < token (1.751×):** prefill is a fixed per-draw cost amortized over more
   generated tokens, so the wall-clock penalty is strictly smaller than the token penalty. The
   token ratio is therefore a *conservative* proxy and the wall ratio is the operative one.
4. **The multiplier transfers to a noised adapter.** LoRA at r=8 adds negligible FLOPs to the same
   architecture, so per-token cost is unchanged; what a noised adapter changes is the **stop rate**,
   and this probe brackets that at both extremes (60/64 → 0/64). `[INFERENCE]`, from the architecture.
   CAL-05 still requires measuring one real noised adapter — this bracket sizes the sweep *before*
   that adapter exists, which is what the ordering needs.

### Making "floor, not mean" STRUCTURAL rather than a comment

CONTEXT.md asks for this to be a fact about the artifact, not a note. Three mechanisms, in increasing
strength; recommend all three:

1. **Distinct field names in the JSON.** Never a bare `h_per_point`. Emit
   `h_per_point_floor` (stop-active) and `h_per_point_ceiling` (stop-disabled) as **two separate
   required keys**, with `stop_terminated_n` / `n_draws` beside each. A consumer physically cannot
   read a mean off a record that contains no mean.
2. **A `_prove`-style refusal in the budget module's consumer.** `scripts/` uses `_prove` /
   `SystemExit` (measured: 18 `scripts/` modules, 0 `src/` modules — `tests/test_phase22_accountant.py:1414`).
   A sizing function that receives a cost record missing `h_per_point_ceiling` should **refuse**, the
   `mitigation_gate._prove_retention_floor` shape. Sizing a sweep against a floor read as a mean is
   the exact failure CAL-05 names.
3. **Size Z against the CEILING, and record the floor beside it.** The ratchet at
   `mitigation_gate.py:248-255` only lets K *increase*, so a sweep sized against the floor and then
   found too expensive cannot be rescued by reducing K. Sizing against the ceiling is the only
   direction the ratchet permits.

**Bounding on the probe itself, stated rather than hidden:** one prompt shape, 64 draws per
condition, one process, un-adapted base. The Phase-18 rates span four attack shapes with different
prefill lengths (134.54–183.20 draws/min, a 1.36× spread). The 1.536× multiplier is a **ratio at
fixed prefill**, so the spread largely cancels — but CAL-05's own measurement should reproduce it
across the real attack shapes on the real noised adapter.

### R3.C — The D-03 ordering, and what makes it structural

D-03 requires the unmitigated control at N seeds (3–5) to run **before** σ=0, so the floor cannot be
tuned after seeing σ=0's number. The mechanism that makes this a fact rather than a promise is the
one `phase19_floor.py` and `test_phase20_prereg.py` already use in combination:

1. Commit the control's record as `results/phase23_*` **first**.
2. Pin the floor in `scripts/mitigation_budget.py` as a literal, with `_PROVENANCE` naming that
   record and its sha256.
3. Add a re-derivation test (the `phase19_floor.py` property 2 shape) so the literal recomputes from
   the committed record on every suite run.
4. Commit the σ=0 record **after**, as a separate artifact and a separate commit.

The ancestry guard then makes the ordering permanent: the floor's provenance names an artifact whose
first add precedes σ=0's. Note the guard takes `adds[-1]` (the EARLIEST add), so this survives
delete-and-re-add. `[INFERENCE]` from `_assert_ordering_holds`'s documented semantics at
`tests/test_phase20_prereg.py:296-330`.

**Seed protocol.** The repo's established seed pair is `(1337, 2024)`
(`results/phase19_noise_floors.json`, `tests/test_phase20_correction.py:115`). D-03 asks for 3–5
seeds; `teach_persona.train_arm(seed=)` already threads a per-arm seed through all three seeding
sites (`teach_persona.py:1152-1156`), so N seeds is N `train_arm` calls with distinct `seed=` and
distinct `prefix=`/arm names — **no new machinery**. At the non-DP control's measured 20.4 s/arm the
whole N-seed control is well under 5 minutes of training, plus its scoring leg.

### R3.D — CTRL-03 and the gate's seed requirement (open question, flagged)

`scripts/mitigation_gate.py` (FROZEN) at `:341-437`:

```python
NEVER_TAUGHT_ARM = "never-taught"
EXTRACTION_FLOOR_PROVENANCE_KEYS = ("arm", "seeds")
EXTRACTION_FLOOR_MIN_SEEDS = 2
...
_prove(extraction_floor_provenance["arm"] == NEVER_TAUGHT_ARM, ...)
_prove(distinct >= EXTRACTION_FLOOR_MIN_SEEDS, ...)
```

CTRL-03's text says *"a never-taught fresh adapter at identical budget and seed, **trained once**…
scheduled once and consumed twice."* The gate demands the extraction floor's provenance name
`≥ 2 distinct seeds`. These are reconcilable — CTRL-03's two consumptions are *frontier floor* and
*relearning reference*, which is orthogonal to seed count — but the plan must decide explicitly
whether the never-taught arm is trained at **one** seed or at the **(1337, 2024)** pair, because the
gate refuses a one-seed extraction floor at `mitigation_gate.py:437` and that refusal fires in
Phase 25, not here. **Recommend: train the never-taught arm at the same N seeds D-03 uses for the
control** — it is the same cheap 20 s/arm, it satisfies the gate by construction, and it is one
scheduling decision rather than a Phase-25 surprise. Recorded as Open Question 1.

---

## R4. The resume seam (D-07, closes WARNING-2)

### R4.1 — What already exists, exactly

**`train()` already takes and fully implements `resume_from`.** `src/personacore/training/loop.py:254`:

```python
def train(
    ..., scaler=None, resume_from=None, checkpoint_path=None, best_checkpoint_path=None, ...
)
```

and the resume block at `:710-780`:

```python
start_step = 0
resumed_best_val_loss = None
if resume_from is not None:
    ckpt = load_checkpoint(resume_from, model=model, optimizer=optimizer,
                           scheduler=scheduler, scaler=scaler)
    start_step = ckpt["step"]
    resumed_best_val_loss = ckpt.get("best_val_loss")
    # (3) SLOT PRESENT + SEAM ABSENT -> REFUSE
    if dp_fn is None and ckpt.get("dp_noise_rng") is not None:
        raise ValueError(...)
    # (1) SLOT PRESENT + SEAM LIVE -> RESTORE
    if dp_fn is not None and ckpt.get("dp_noise_rng") is not None:
        dp_fn.load_noise_rng_state(ckpt["dp_noise_rng"])
```

The three-branch matrix at `:724-762` is documented at length, WARNING-1 is closed on it, and
`22-REVIEW`'s CR-04 (refuse on branch 2) was traced and **rejected** on measured grounds. **D-07 adds
nothing to `train()`. The entire seam is one hop above it.**

**`refuse_if_exists`**, `scripts/teach_persona.py:370-378`:

```python
def refuse_if_exists(paths):
    """Refuse-to-rerun: an arm's outputs are RECORDED evidence once written — a rerun on
    drifted code or a drifted fact set would silently replace them. Fail loud, name the file."""
    for out in paths:
        if out.exists():
            raise SystemExit(
                f"[teach_persona] {out} already exists — this arm is recorded evidence. "
                f"Delete {' and '.join(str(p) for p in paths)} to re-run."
            )
```

**`train_arm`**, `scripts/teach_persona.py:1134-1145`:

```python
def train_arm(
    arm, *, facts, family_ids, second_person=False, replay_ratio=0.0,
    seed=SEED, prefix="phase14", dp_sigma=None, dp_clip_norm=None,
):
```

Its single `refuse_if_exists` call site, `:1198-1200`:

```python
refuse_if_exists(
    arm_bin_targets(arm, paths) + [paths["csv"], paths["checkpoint"], paths["adapter"]]
)
```

and its `train(...)` call at `:1379-1414` — which **does not pass `resume_from`**. That absence is
WARNING-2.

### R4.2 — Call sites (the blast radius of a required parameter)

`grep -rn "train_arm(" --include='*.py' scripts tests`:

| Site | Arm type |
|---|---|
| `scripts/teach_persona.py:1081` (`run_calibration`) | non-DP |
| `scripts/teach_persona.py:2320` (`main`) | DP + non-DP |
| `scripts/phase19_erasure.py:3528, :3630, :3701` | non-DP |
| `scripts/phase19_run.py:1646` | non-DP |
| `scripts/phase17_isolation.py:1138` | non-DP |
| `tests/test_phase22_wiring.py:549` | refusal probe |

**Eight production call sites, seven of them non-DP.** A required parameter would make all seven a
`TypeError`. This is the *identical* situation `dp_sigma`/`dp_clip_norm` faced, and `train_arm`'s
own docstring at `:1170-1180` records the resolution:

> ***"`None` is a SENTINEL, not a default value.** The plan text for 22-10 asks for "keyword-only
> with no default", but five call sites outside this module already call `train_arm` … and every one
> of them passes a NON-DP arm; a truly-required parameter would make each of them a `TypeError`. The
> sentinel keeps that contract intact AND is what the plan's own refusal instruction presupposes."*

### R4.3 — The additive-seam shape D-07 follows

The shape validated twice in Phase 22, read off the code:

| Property | `dp_fn=` (22-10) | `fact_bin=`/`n_facts=` (22-08) | **`resume_from=` (D-07)** |
|---|---|---|---|
| Keyword-only, `None` default | ✅ | ✅ | ✅ same |
| Byte-identical when `None` | ✅ (`dp_kwargs = {} if not is_dp`) | ✅ (same dict) | ✅ — `refuse_if_exists` unchanged when `resume_from is None` |
| Threaded, not module-read | ✅ from `main`'s CLI | ✅ from `stats` | ✅ from `main`'s CLI |
| Refuses an incoherent combination | ✅ DP arm without both σ and C → `SystemExit` | ✅ accum-agreement refusal in `loop.py` | ✅ — see below |
| Watched failing | ✅ | ✅ | **must be added** |

**Concrete shape:**

```python
def train_arm(arm, *, facts, family_ids, second_person=False, replay_ratio=0.0,
              seed=SEED, prefix="phase14", dp_sigma=None, dp_clip_norm=None,
              resume_from=None):
```

**The resume-aware `refuse_if_exists` branch.** The refusal exists because *"an arm's outputs are
RECORDED evidence once written."* On a resume that reasoning **inverts**: the checkpoint's existence
is the *precondition*, not the violation. But not every path inverts, and the distinction is where the
bug would live:

| Target | On a fresh run | On `resume_from=<this arm's checkpoint>` |
|---|---|---|
| `paths["checkpoint"]` (`latest.pt`) | refuse if exists | **must exist** — it is the resume source |
| `paths["csv"]` | refuse if exists | **must exist and be appended** — `CSVLogger` is restart-safe (`loop.py:781-786`), and `train()` derives cumulative tokens from the absolute step *"so the logged curve is continuous across a kill+resume"* (`loop.py:795-799`). Deleting it would discontinuity the curve. |
| `paths["bin"]`, `paths["mask"]`, fact bin | refuse if exists | **must exist** — resuming with regenerated bins resumes a *different* corpus |
| `paths["adapter"]` | refuse if exists | **still refuse** — the export happens at the end; an adapter already on disk means the arm completed |

**Recommended shape (smallest correct diff):** widen the helper rather than branching at the call
site, so both callers of `arm_bin_targets` cannot drift —

```python
def refuse_if_exists(paths, *, expected=()):
    """... ``expected`` names paths a RESUME requires to exist; each is refused if ABSENT."""
```

with `train_arm` passing `expected=(...)` when `resume_from is not None`. One guard, one derivation,
the `arm_bin_targets` reasoning at `:355-366` verbatim (*"two copies of a guard drift"*).

**The refusal D-07 must add** (the pattern's fourth row): `resume_from` naming a checkpoint that is
**not this arm's** `paths["checkpoint"]` should `SystemExit`. Resuming arm A's DP run from arm B's
checkpoint would publish an ε describing a composition that spans two arms — the same class of defect
`_count_composed_steps` was written to catch (`test_phase22_checkpoint.py:361-380`).

**A second refusal worth adding, measured this session:** a checkpoint's `dp_noise_rng` written on
CPU cannot be loaded into an MPS generator — `RuntimeError: RNG state is wrong size` (§R1.4). torch
already refuses, so the seam does not *need* a guard; but the raw torch message names no arm, no file
and no phase. A `SystemExit` naming the device mismatch is a strictly better failure at the same cost.

### R4.4 — CAL-03's instrument, since it rides the same machinery

**CONTEXT.md's third `<specifics>` measurement is REPRODUCED and HOLDS:**

```
epsilon_for      (sigma, steps, delta)
sigma_for        (target_epsilon, steps, delta)
delta_closed     (eps, mu)
delta_quadrature (eps, mu, *, lam=40.0, n=20001, rel_tol=1e-09)
```

**`epsilon_for` takes no `N`.** ε is N-independent by construction of the accountant, so CAL-03
cannot test the math — it tests whether N leaks into `T`. `[MEASURED]`

The instrument for D-05's "T asserted equal directly" already exists and should be reused rather than
reinvented: `tests/test_phase22_checkpoint.py:361::_count_composed_steps` shadows `DPSGD.finalize`
per-instance and counts real invocations. Its docstring records exactly why a `ckpt["step"]` read is
insufficient — a mutation made the checkpoint report `4` while `6` steps composed. For CAL-03 the
same shadow gives `T_n8` and `T_n64` as counts of the mechanism that actually ran, and D-05's two
assertions become:

```python
assert T_n8 == T_n64                                      # names WHERE a leak lives
assert epsilon_for(sigma, T_n8, DELTA) == epsilon_for(sigma, T_n64, DELTA)   # bit-identical, no tolerance
```

**Cost of the CAL-03 calibration run, from §R3.A:** an n=8 arm ≈ 3.8 min and an n=64 arm ≈ 30.0 min
at the full `MAX_STEPS = 200`. CAL-03 is a *wiring* test, so `max_steps_override` at a small step
count (`train()` accepts it, `loop.py:262`) makes the pair cost seconds instead of 34 minutes while
testing the same wiring — the shape `test_resume_epsilon_bit_identical` already uses
(`_TOTAL_STEPS = 4`).

---

## Validation Architecture

*(R5 — mandatory, Nyquist Dimension 8. `VALIDATION.md` is derived from this section.)*

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` 8.x (`[tool.pytest.ini_options]`, `pyproject.toml:24-26`) |
| Config file | `pyproject.toml` — `testpaths = ["tests"]`, `pythonpath = ["."]` |
| Quick run command | `.venv/bin/python -m pytest tests/test_phase23_*.py -q` |
| Full suite command | `make test` → `pytest -q` |
| Current suite size | **1,339 tests collected** (measured this session) |
| Lint | `make lint` → `ruff check . && ruff format --check .` |
| CI | `.github/workflows/ci.yml` — `ubuntu-latest`, Python 3.11, `pip install -e ".[cpu,dev,demo]"`, `pytest -q`. **CPU-only: every MPS leg must be `skipif`-gated.** |
| MPS gating precedent | `tests/test_mps_smoke.py` module-level `pytestmark`; per-case register at `tests/test_phase22_checkpoint.py:671` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **DPSGD-06** | The D-16 generator invariant holds on MPS at σ=0: `torch.normal(std=0.0)` returns exact zeros **and** advances the 44-byte state | unit (MPS, skipif) | `pytest tests/test_phase23_mps_venue.py::test_sigma_zero_advances_the_mps_generator -x` | ❌ Wave 0 |
| **DPSGD-06** | σ=0 is the DP arm's **first** executed run — no `results/phase23_*` noised record precedes the σ=0 record in git | structural (ancestry) | `pytest tests/test_phase23_prereg.py::test_sigma_zero_precedes_every_noised_point -x` | ❌ Wave 0 |
| **DPSGD-06 / D-04** | σ=0 within the pinned floor ⇒ proceed; outside ⇒ HALT with zero noised points | unit (both branches, RED watched) | `pytest tests/test_phase23_prereg.py::test_floor_breach_halts_the_sweep -x` | ❌ Wave 0 |
| **D-02** | V-15 kill→resume ε bit-identity, parametrized `["cpu", "mps"]` | integration (MPS leg skipif) | `pytest tests/test_phase22_checkpoint.py::test_resume_epsilon_bit_identical -x` | ✅ exists — **needs device parametrization** |
| **D-02** | Four DPSGD-04 fakes, runtime halves re-watched RED on MPS | unit ×4 (MPS, skipif) | `pytest tests/test_phase22_fakes.py -k "fake_" -x` | ✅ exists — **needs device parametrization** |
| **D-02** | The AST halves are recorded as device-invariant, not silently skipped | structural (ledger row) | `pytest tests/test_phase22_fakes.py::test_fakes_ledger_is_recorded -x` | ✅ exists — **ledger needs a device column** |
| **CAL-01** | The training leg is measured on the DP path with the seam active, and the record carries device, torch version, git_sha, step count and denominators | structural (record schema) | `pytest tests/test_phase23_cost.py::test_training_cost_record_is_complete -x` | ❌ Wave 0 |
| **CAL-01** | A cost record missing any provenance key is REFUSED, not defaulted | unit (refusal) | `pytest tests/test_phase23_cost.py::test_incomplete_cost_record_is_refused -x` | ❌ Wave 0 |
| **CAL-05** | The cost record carries `h_per_point_floor` **and** `h_per_point_ceiling` as distinct required keys — no bare mean field exists | structural | `pytest tests/test_phase23_cost.py::test_no_bare_mean_field_exists -x` | ❌ Wave 0 |
| **CAL-05** | Sizing refuses a record lacking `h_per_point_ceiling`; Z is sized against the ceiling | unit (refusal + positive) | `pytest tests/test_phase23_budget.py::test_sizing_refuses_a_floor_only_record -x` | ❌ Wave 0 |
| **CAL-02 / SC3** | The gate is structurally unable to import the budget — **static** | structural (AST) | `pytest tests/test_phase20_prereg.py -k import_graph -x` | ✅ **exists and bites** (watched RED §R2.2) |
| **CAL-02 / SC3** | …and **transitively**, out of process (closes the `erasure_gate` route) | structural (subprocess) | `pytest tests/test_phase23_budget.py::test_gate_does_not_transitively_load_the_budget -x` | ❌ Wave 0 |
| **CAL-02** | `mitigation_budget.py` holds literal assignments only — no rule, no estimator, no import | structural (AST) | `pytest tests/test_phase23_budget.py::test_budget_holds_only_literal_constants -x` | ❌ Wave 0 (model: `test_floor_lock_holds_only_literal_constants_and_nothing_else`) |
| **CAL-02** | Every pinned Z constant **re-derives** from its committed artifact on every suite run | unit (re-derivation) | `pytest tests/test_phase23_budget.py::test_budget_constants_re_derive -x` | ❌ Wave 0 (model: `test_floor_lock_re_derives_all_three_constants_from_their_evidence_artifacts`) |
| **CAL-02** | The selected K is a member of the FROZEN `mitigation_gate.K_RUNGS` and satisfies the ratchet | unit | `pytest tests/test_phase23_budget.py::test_selected_k_is_a_ratcheted_rung -x` | ❌ Wave 0 |
| **CAL-03 / D-05** | ε at n=8 and n=64 at fixed σ is **bit-identical** under `==`, never a tolerance | unit | `pytest tests/test_phase23_cal03.py::test_epsilon_is_bit_identical_across_capacity -x` | ❌ Wave 0 |
| **CAL-03 / D-05** | The composed step count T is asserted equal **directly**, read from `_count_composed_steps`, not from `ckpt["step"]` | unit | `pytest tests/test_phase23_cal03.py::test_composed_step_count_is_equal_across_capacity -x` | ❌ Wave 0 |
| **CAL-03 / D-05** | A synthetic N-leak into T is WATCHED reddening both assertions (a guard nobody has seen fail is not evidence) | unit (positive control) | `pytest tests/test_phase23_cal03.py::test_an_n_leak_into_t_is_detected -x` | ❌ Wave 0 |
| **CAL-03 / D-06** | Falsified ⇒ the n=64 leg is absent from the committed budget and the withdrawing measurement is recorded | structural | `pytest tests/test_phase23_budget.py::test_n64_leg_absent_when_cal03_falsified -x` | ❌ Wave 0 |
| **CTRL-03** | The never-taught record's provenance names `arm="never-taught"` with ≥ `EXTRACTION_FLOOR_MIN_SEEDS` distinct seeds (the FROZEN gate's requirement) | structural | `pytest tests/test_phase23_ctrl.py::test_never_taught_provenance_satisfies_the_gate -x` | ❌ Wave 0 |
| **CTRL-03** | Trained once, consumed twice — one record, two named consumers, no second training call | structural | `pytest tests/test_phase23_ctrl.py::test_never_taught_is_trained_once -x` | ❌ Wave 0 |
| **D-03** | The control record's first git add **strictly precedes** the σ=0 record's | structural (ancestry) | `pytest tests/test_phase23_prereg.py::test_control_precedes_sigma_zero -x` | ❌ Wave 0 (model: `_assert_ordering_holds`) |
| **D-03** | `scripts/mitigation_accountant.py` is byte-unchanged across the phase | structural | `git diff --exit-code -- scripts/mitigation_accountant.py` + `pytest tests/test_phase20_prereg.py -k phase23_result -x` | ✅ guard exists (`:332`), currently vacuous |
| **D-07** | `train_arm(resume_from=None)` is byte-identical to today at every one of the 8 call sites | unit (inertness) | `pytest tests/test_phase23_resume.py::test_resume_from_none_is_inert -x` | ❌ Wave 0 |
| **D-07** | A resume finds the checkpoint/csv/bins present and does NOT refuse; the adapter still refuses | unit (4 targets) | `pytest tests/test_phase23_resume.py::test_refuse_if_exists_is_resume_aware -x` | ❌ Wave 0 |
| **D-07** | `resume_from` naming another arm's checkpoint is REFUSED | unit (refusal) | `pytest tests/test_phase23_resume.py::test_cross_arm_resume_is_refused -x` | ❌ Wave 0 |
| **D-07** | A production kill→resume through `train_arm` reproduces bit-identical ε **on MPS** | integration (MPS, skipif) | `pytest tests/test_phase23_resume.py::test_production_resume_epsilon_bit_identical -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `.venv/bin/python -m pytest tests/test_phase23_*.py -q` (target < 30 s) — plus
  `pytest tests/test_phase20_prereg.py -k import_graph -q` on any task that touches
  `scripts/mitigation_*.py`, because that guard is the SC3 gate.
- **Per wave merge:** `make test` (full 1,339+) **on the M3, where the MPS legs actually run** — a
  CPU-only pass skips exactly the tests D-02 exists to produce. Plus `make lint`.
- **Phase gate:** full suite green on the M3 with **zero skips among the MPS-gated Phase-23 tests**
  (record the skip count explicitly — a green run that skipped the venue tests is the failure mode
  D-02 names), plus `git diff --exit-code -- scripts/mitigation_accountant.py scripts/mitigation_gate.py`
  returning 0, before `/gsd:verify-work`.

### Wave 0 Gaps

- [ ] `tests/test_phase23_mps_venue.py` — the D-02 device-parametrization harness + the σ=0
      generator-advance guard (DPSGD-06's keystone)
- [ ] Device parametrization of `tests/test_phase22_dpsgd.py::_model`,
      `tests/test_phase22_fakes.py::_record`, `tests/test_phase22_checkpoint.py::_next_draw` — see
      §R1.7 for the exhaustive touchpoint list
- [ ] `tests/test_phase23_prereg.py` — ordering/ancestry guards (D-03, D-04, DPSGD-06)
- [ ] `tests/test_phase23_cost.py` — cost-record schema + refusals (CAL-01, CAL-05)
- [ ] `tests/test_phase23_budget.py` — budget-module structure, re-derivation, transitive import
      guard, K ratchet (CAL-02, D-06)
- [ ] `tests/test_phase23_cal03.py` — ε/T bit-identity + the watched N-leak positive control (CAL-03)
- [ ] `tests/test_phase23_ctrl.py` — never-taught provenance and single-training (CTRL-03)
- [ ] `tests/test_phase23_resume.py` — the D-07 seam, its inertness, its refusals, its MPS production leg
- [ ] `results/phase23_*` naming convention — anything outside this prefix falls outside the ancestry
      guard at `tests/test_phase20_prereg.py:332`
- [ ] Framework install: **none needed** — pytest 8.x, ruff and the venv are already present and green
      (1,339 collected this session)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Forbidding the gate from importing the budget | A new AST guard | `tests/test_phase20_prereg.py:1133` | Already written, already names `mitigation_budget`, watched RED §R2.2. `test_phase20_prereg.py:153-155` is explicit: *a guard proved correct in a scratch repository and a guard running against this one must be the SAME code.* |
| A post-artifact measured constant with provenance | A new pin format | `scripts/phase19_floor.py` shape + its two tests | Literal-only, zero-import, re-derives every run. Also satisfies §R2.3's import ceiling for free. |
| A machine-readable floor record | A bespoke JSON | `results/phase19_noise_floors.json` shape | Already carries `git_sha`, `record_sha256`, `recipe`, `estimator`, `reduction`, `governs`, per-seed readings. |
| Counting composed steps for D-05's T assertion | Reading `ckpt["step"]` | `tests/test_phase22_checkpoint.py:361::_count_composed_steps` | Its docstring records a mutation where the checkpoint said 4 and 6 composed — a field read is *optimistic*, not merely imprecise. |
| Resume in the training loop | Anything | `train(resume_from=)` at `loop.py:710-780` | Complete, three-branch matrix documented, WARNING-1 closed on it, CR-04 traced and rejected. D-07 is one hop above it. |
| MPS generator persistence | A custom serializer | `torch.save` / `Generator.set_state` | Round-trips bit-identically, fresh and mid-stream (§R1.6, measured). |
| Ordering/pre-registration proofs | A new ancestry check | `tests/test_phase20_prereg.py::_assert_ordering_holds` | Parameterized on `root`, already called by three guards, carries the strict-ancestor conjunct and the `adds[-1]` earliest-add semantics. |
| A device-skip register | A bare `skipif` | `tests/test_phase22_checkpoint.py:671`'s `pytest.param(..., marks=skipif(...))` | Its `reason=` names the non-skipping test that still carries the guarantee — the discipline this repo enforces. |
| Timing on MPS | Hand-rolled event timers | `time.perf_counter()` + `torch.mps.synchronize()` | `torch.mps.synchronize` verified present in torch 2.7.1. Generation additionally self-syncs per token (`generation/core.py:79`). |

**Key insight:** almost every mechanism this phase needs is already committed. The Phase-23 work is
predominantly *wiring, parametrizing, and watching* — not building. The one genuinely new artifact is
`scripts/mitigation_budget.py`, and its shape is dictated by an existing file
(`scripts/phase19_floor.py`) and an existing constraint (§R2.3's import ceiling).

---

## Common Pitfalls

### Pitfall 1: A green suite on CPU read as a green venue pass
**What goes wrong:** the MPS legs are `skipif`-gated, the suite reports `N passed, M skipped`, and the
D-02 obligation is recorded satisfied.
**Why:** `skipif` is silent by design; CI is `ubuntu-latest` and will *always* skip them.
**How to avoid:** the phase gate must assert **zero skips among the Phase-23 MPS tests** and record
the skip count as a number in the summary.
**Warning signs:** a phase summary quoting a pass count with no skip count beside it.

### Pitfall 2: `import json` in `scripts/mitigation_budget.py`
**What goes wrong:** `test_mitigation_gate_import_graph_is_stdlib_and_erasure_gate_only` goes RED, and
because the union spans every `mitigation_*.py`, the failure names the *set*, not the file.
**Why:** the allow-set has zero headroom (§R2.3, measured).
**How to avoid:** literal assignments, zero imports — the `phase19_floor.py` / `mitigation_accountant.py`
shape.
**Warning signs:** the budget module needing to *read* anything at import time.

### Pitfall 3: Editing `scripts/mitigation_gate.py`
**What goes wrong:** permanently RED ancestry guard, no recovery path, no force flag, and
delete-and-re-add cannot launder it (`adds[-1]`).
**Why:** three `results/phase20_*` artifacts are committed (§R2.4).
**How to avoid:** corrections are dated additive continuations via `scripts/_addendum.py` (D-24).
Everything Phase 23 needs from the gate is already there.
**Warning signs:** a plan task whose action begins "add a constant to `mitigation_gate.py`".

### Pitfall 4: Re-drawing gradients on the MPS generator in `_record`
**What goes wrong:** `_FAKE1_LEAK_RATIO = 1.734481` and `_FAKE3_STD_RATIO_AT_N4 = 3.999986` are fitted
constants; different draws move them and the failure looks like a fake detection.
**How to avoid:** keep the CPU draw, move the tensor (`g.to(device)`).
**Warning signs:** `torch.Generator(device=device)` appearing inside `_record`.

### Pitfall 5: Sizing Z against the floor
**What goes wrong:** the sweep is priced at 4.77 h/point, runs long, and the ratchet
(`mitigation_gate.py:248-255`) forbids reducing K to recover.
**Why:** K may only **increase**. There is no rescue in the cheap direction.
**How to avoid:** size against the measured ceiling (7.33 h/point, §R3.B), record the floor beside it
in a distinctly-named field.
**Warning signs:** a single `h_per_point` field anywhere in a Phase-23 artifact.

### Pitfall 6: Assuming the DP training leg is ~17 s
**What goes wrong:** a 16-point n=64 sweep silently carries an extra ~8 h of training nobody budgeted.
**Why:** `grad_accum_steps = n_facts` — 64 backward passes plus 32 replay micro-batches per optimizer
step (§R3.A, measured 30.0 min/arm).
**How to avoid:** budget training per **capacity**, not per "arm".
**Warning signs:** the phrase "~1,010×" used about a DP arm.

### Pitfall 7: `refuse_if_exists` deleted rather than made resume-aware
**What goes wrong:** an operator deletes the CSV to get past the refusal, and the curve
discontinuities across the kill — `loop.py:795-799` derives cumulative tokens from the absolute step
*precisely* to keep it continuous.
**How to avoid:** invert the predicate per-target (§R4.3's table), do not bypass it.
**Warning signs:** a refusal message telling the operator to delete `*_train.csv`.

### Pitfall 8: A cross-device checkpoint resume
**What goes wrong:** a CPU-written `dp_noise_rng` (5,056 B) cannot load into an MPS generator (44 B).
torch raises `RuntimeError: RNG state is wrong size` — loud, but naming no arm and no file.
**How to avoid:** record the device in the checkpoint and refuse with a `SystemExit` that names both.
**Warning signs:** a smoke run done on CPU and then "continued" on the M3.

---

## Runtime State Inventory

*Phase 23 is not a rename/refactor phase, but it is the first phase that WRITES runtime state to
disk on the real venue, so the same discipline is applied to what it will create.*

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | **None pre-existing.** `git ls-files 'results/phase22_*' 'results/phase23_*'` → 0 files. Phase 23 creates `results/phase23_*` for the first time. | Naming convention: `results/phase23_*` only, or the ancestry guard at `test_phase20_prereg.py:332` does not watch it. |
| Live service config | **None** — this project has no external services. Verified: no wandb/network by CLAUDE.md policy, `mitigation_*.py` import surface is `{pathlib, sys, erasure_gate}`. | none |
| OS-registered state | **None** — no schedulers, no daemons. Runs are foreground `python scripts/...`. | none |
| Secrets / env vars | **None consumed by this phase.** `.gitignore` covers tokens, checkpoints and logs. | none |
| Build artifacts | `.venv` editable install present and current (1,339 tests collect clean). `checkpoints/` is **gitignored** — `checkpoints/convbase_slim.pt` (55 MB) and `convbase_best.pt` (278 MB) exist locally and are Phase-23 preconditions that CI does not have. | Every test that reads them must be `skipif`-gated in the `tests/test_lora_artifact.py:238` register. New Phase-23 checkpoints land under `checkpoints/` and are not committed. |

---

## Package Legitimacy Audit

**NOT APPLICABLE — deliberately, not by oversight. This phase installs zero external packages.**

Every dependency Phase 23 needs is already present and pinned in the committed environment (verified
this session: Python 3.11.15, torch 2.7.1, pytest 8.x, ruff — 1,339 tests collect clean). CLAUDE.md
forbids adding runtime dependencies (`RPT-03` keeps v4.0's runtime dependency surface at **zero**),
and `tests/test_phase20_prereg.py:1182` enforces an import ceiling of
`{pathlib, sys, erasure_gate}` across every `scripts/mitigation_*.py` — measured RED against a
single `import json` (§R2.3). `pyproject.toml` must stay untouched.

**If a plan task proposes `pip install` of anything, that task contradicts RPT-03 and the import
ceiling, and the guard at `tests/test_phase20_prereg.py` will catch the module-level half of it.**

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.11 venv | everything | ✓ | 3.11.15 | — (3.14 system Python is NOT a supported target) |
| PyTorch | everything | ✓ | 2.7.1 | — |
| MPS backend | D-01, D-02, all runs | ✓ | `is_available()` and `is_built()` both True | CPU (would violate D-01) |
| `torch.mps.synchronize` | R3 timing | ✓ | present | per-token `int()` sync (already implicit in generation) |
| pytest | all validation | ✓ | 8.x, 1,339 tests collect | — |
| ruff | `make lint` | ✓ | configured `pyproject.toml:36` | — |
| `checkpoints/convbase_slim.pt` | CAL-05 throughput | ✓ | 55,601,651 B, base sha `04e724c67033`, step 4000 | none — CAL-05 cannot run without it |
| `checkpoints/convbase_best.pt` | `train_arm` (`CONVBASE_BEST`) | ✓ | 278,026,567 B | none — `train_arm` `SystemExit`s without it |
| `data/dialog_train.bin` / `dialog_val.bin` + masks | DP replay seam + collateral metric | **unverified this session** | — | `train_arm` refuses loudly at `:1224-1237` if absent; `python scripts/prepare_dialog_corpus.py` regenerates |
| Network | nothing | n/a | — | project is offline by design |

**Missing dependencies with no fallback:** none identified.
**Unverified:** the `data/` dialogue pair — the planner should add a one-line pre-flight check to the
first execution task rather than discovering it mid-run. `train_arm` already refuses loudly, so the
failure mode is loud, not silent.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | The bit-identical `_global_norm` on one 72-tensor LoRA-shaped fixture generalizes to the production gradient distribution | R1.3 | LOW — the two dependent constants carry ~1% bands. If it does not hold, the FAKE 1 / FAKE 3 bands need re-fitting on MPS and both fitted values must be re-recorded, not widened. |
| A2 | The 1.536× CAL-05 multiplier, measured on one prompt shape on the un-adapted base, transfers to a noised adapter | R3.B | MEDIUM — sizing would be wrong in a direction the K ratchet cannot rescue. CAL-05 requires the real re-measurement anyway; this is a pre-sizing bracket, not a substitute. |
| A3 | The §R3.A projections are a lower bound on the real `train_arm` wall clock | R3.A | LOW — stated as a bound, not an estimate. Excludes bins build, 20 evals, 4 checkpoint writes, memmap I/O, 2 PPL sweeps. CAL-01 confirms against one real run. |
| A4 | The static import guard's dynamic-import hole is closed by the subset assertion | R2.3 | LOW — reasoning from the assertion, not measured. The recommended transitive probe closes it independently. |
| A5 | The AST halves of the four fakes are device-invariant | R1.3 | LOW — `ast.parse` over source text imports no torch runtime (verified: `tests/test_phase22_dpsgd_ast.py` has 0 `"cpu"` literals and no torch import). |
| A6 | `_assert_ordering_holds` survives delete-and-re-add via `adds[-1]` | R3.C | LOW — read from three separate docstrings that state it identically; not independently executed this session. |

---

## Open Questions (RESOLVED)

> All four were carried forward and closed downstream — two by locked decisions in
> `23-CONTEXT.md`, two under Claude's Discretion with the resolution pinned in a committed plan.
> Each question below states what closed it and where. Nothing here is still open; a reader
> arriving at this section should follow the marker rather than re-open the question.

1. **CTRL-03's seed count vs the FROZEN gate's `EXTRACTION_FLOOR_MIN_SEEDS = 2`.**
   **RESOLVED — locked as D-08** (`23-CONTEXT.md:104`): the never-taught arm is trained at the
   SAME N seeds D-03 uses for the control, in ONE scheduling. Executed by plan `23-08`, whose
   record asserts `len(set(seeds)) >= mitigation_gate.EXTRACTION_FLOOR_MIN_SEEDS` against the
   IMPORTED frozen constant. The recommendation below was adopted as written.
   - *What we know:* `scripts/mitigation_gate.py:426-441` `_prove`s that the extraction floor's
     provenance names `arm == "never-taught"` and `>= 2` distinct seeds. The gate is frozen and cannot
     be relaxed. CTRL-03's text says the never-taught adapter is *"trained once at identical budget and
     seed protocol."* The repo's established pair is `(1337, 2024)`.
   - *What's unclear:* whether "trained once" means one seed (which the gate would refuse in Phase 25)
     or one *scheduling*, at the standard pair.
   - *Recommendation:* train the never-taught arm at the **same N seeds D-03 uses for the control**.
     At ~20 s/arm the cost is negligible, it satisfies the frozen gate by construction, and it turns a
     Phase-25 refusal into a Phase-23 decision. Confirm with the user before planning.

2. **Should the SC3 guard gain the transitive half?**
   **RESOLVED — locked as D-09** (`23-CONTEXT.md:112`): yes, the guard gains the transitive
   out-of-process `subprocess` half. Executed by plan `23-02` as
   `tests/test_phase23_budget.py::test_gate_does_not_transitively_load_the_budget`, with both
   halves watched RED. The static half is NOT rewritten — `scripts/mitigation_gate.py` is frozen.
   - *What we know:* the accountant's standard is *"guarded statically AND transitively"*
     (`test_phase22_accountant.py:1350`, with an out-of-process `subprocess` probe). The gate/budget
     guard has only the static half, and `scripts/erasure_gate.py` sits outside the `mitigation_*.py`
     glob, leaving a *gate → erasure_gate → budget* route unseen.
   - *What's unclear:* whether the route is reachable enough to be worth ~12 lines.
   - *Recommendation:* add it. The pattern is proven locally, the cost is small, and SC3's wording
     ("structurally unable to import") is a claim the static half alone does not fully support.

3. **Does D-03's floor go in `scripts/mitigation_budget.py` or a separate literal-only file?**
   **RESOLVED — Claude's Discretion** (`23-CONTEXT.md:146-150`), recommendation adopted: one
   file. Executed by plan `23-09`, which writes `CONTROL_NOISE_FLOOR` plus its
   `_PROVENANCE` sibling into `scripts/mitigation_budget.py` and explicitly does NOT register
   the module as a `prereg_artifact=` — registering it would freeze it and forbid the Z values
   from ever being written.
   - *What we know:* CONTEXT.md D-03 says "in `scripts/mitigation_budget.py` with a `_PROVENANCE`
     sibling". `scripts/phase19_floor.py`'s own docstring argues that a measured constant derived
     *after* an artifact exists must live outside the closed pin.
   - *What's unclear:* whether `mitigation_budget.py` is itself "closed" — it is not a
     `prereg_artifact=` today, so it is *protected but not frozen* (`test_phase20_prereg.py:96-110`
     states this distinction explicitly and calls it deliberate).
   - *Recommendation:* one file. It is protected-not-frozen by design, which is exactly the middle
     ground D-03 needs. Do **not** add it as a `prereg_artifact=` — that would freeze it and forbid
     the Z values from ever being written. Record this reasoning in the plan.

4. **How many seeds for D-03's control — 3, 4, or 5?**
   **RESOLVED — Claude's Discretion** (`23-CONTEXT.md:144-145`), by a pre-registered rule
   rather than by a preference. `phase23_prereg.choose_n_seeds(seconds_per_seed)` is committed
   BLIND in plan `23-03` — in the edit-once pre-registration module, while
   `git ls-files 'results/phase23_*'` is still empty — and returns the largest N in (5, 4, 3)
   whose projected scoring time fits one `h_per_point` floor unit, never below 3. Plan `23-08`
   measures the scoring leg for ONE seed and IMPORTS the rule; it defines no local copy,
   because `scripts/phase23_run.py` is re-edited by four later plans and could not carry a
   pre-registration. This is the question whose deferred resolution was caught as a blocker in
   plan review, which is why the resolution names its landing site explicitly.
   - *What we know:* D-03 says 3–5, discretion. Non-DP arm ≈ 20.4 s of training (measured); the
     scoring leg dominates.
   - *Recommendation:* the planner should cost the **scoring** leg per seed before choosing, because
     that is what binds. Not researched here — it depends on which score the floor is computed over,
     which is a D-03 implementation choice.

---

## Contradiction Found (for the user, not acted on)

**No locked decision (D-01 … D-07) was contradicted by any evidence found in this session.** All
seven stand, and three of them were independently strengthened by measurement (D-02's premise
reproduced in full, D-05's premise reproduced, D-07's mechanism reproduced fresh and mid-stream).

One **committed repository figure** did not survive re-measurement, and it is recorded here rather
than only inside R3.A because this project's discipline is to surface those in place.

**The claim.** `.planning/REQUIREMENTS.md` (CAL section preamble) and `.planning/STATE.md:493`:

> *"Training is ~17 s per arm. **Evaluation costs ~1,010× training** — it is the binding constraint
> by three orders of magnitude, and no sweep density may be chosen without it."*

**The measurement** (§R3.A, MPS, torch 2.7.1, production shape `MAX_STEPS=200 / BATCH_SIZE=8 /
BLOCK_SIZE=256`, real `GPT(ModelConfig())` + real `inject_lora` + real `DPSGD`):

| Arm | Measured training | eval(4.77 h) ÷ training | Claim holds? |
|---|---:|---:|---|
| non-DP (accum=1) | 20.4 s | 843× | ✅ — this is where "~17 s" and "~1,010×" come from |
| `dp_n8` (accum=8 + 4 replay micro) | 227.6 s ≈ 3.79 min | 75× | ❌ |
| `dp_n64` (accum=64 + 32 replay micro) | 1798.6 s ≈ 29.98 min | **9.5×** | ❌ — one order of magnitude, not three |

**Root cause, not a discrepancy:** `scripts/teach_persona.py:1352` sets
`grad_accum_steps = stats["n_facts"]` — one micro-batch per privacy record — and
`training/loop.py:685-699` adds `ceil(4 * n_facts / batch_size)` further replay micro-batches per
optimizer step. The DP seam's *own* overhead is small (+6.9% per micro-batch, measured); the 60×
comes entirely from the record-per-micro-step structure SC2 pre-registered.

**Why this is not acted on here.** CAL-01's own text already says the training leg is *"to be
confirmed on the DP path with the seam active"* — so measuring it and finding a different number is
the requirement being satisfied, not a defect being found. **No locked decision changes:** evaluation
remains the binding constraint at every capacity, so D-03's ordering, D-04's halt rule and the sweep
sizing all stand. What changes is the *margin*, and a plan that budgets 16 × 17 s of training for an
n=64 sweep would be short by roughly **8 hours**.

**Recommended disposition (planner's call, not taken here):** record the DP figures in Phase 23's
cost artifact, and correct the REQUIREMENTS.md/STATE.md sentence by the project's retract-in-place
route — a dated additive continuation naming what measured it false — rather than by editing the
figure in place. The sentence is *true of the non-DP arm* and should be re-scoped, not deleted.

---

## Sources

### Primary (HIGH confidence) — measured in this working tree, this session

- `.venv/bin/python` — torch 2.7.1 / Python 3.11.15 / MPS available; `torch.mps` API surface
- Generator state sizes, cross-device refusals, `torch.save`/`set_state` round-trip (fresh + mid-stream)
- `torch.normal(std=0.0)` zeros-and-advances on MPS at sizes 1…16 and 4608
- `_global_norm` CPU vs MPS bit-identity on a 72-tensor LoRA-shaped fixture
- `_next_draw` and `_record` failure modes on MPS (exact `RuntimeError` text)
- `pytest tests/test_phase20_prereg.py -k import_graph` watched RED twice (forbidden import; `json`)
- CAL-01 production-shape timing probe (MPS, real GPT + real LoRA + real DPSGD)
- CAL-05 stop-active vs full-48 probe on `checkpoints/convbase_slim.pt` (MPS, N=64 per condition)
- `git ls-files 'results/phase2[0-3]_*'`; `pytest --collect-only -q` → 1,339
- `inspect.signature` on `epsilon_for` / `sigma_for` / `delta_closed` / `delta_quadrature`

### Primary (HIGH confidence) — committed files read at named lines

- `results/phase18_preflight_report.md:10-16, 23-28, 35-38, 71-81`
- `scripts/mitigation_gate.py:1-40, 240-256, 341-441, 963-995`
- `scripts/mitigation_accountant.py:335` · `scripts/phase19_floor.py:1-42` · `scripts/erasure_gate.py:68`
- `scripts/teach_persona.py:103-104, 178-215, 270, 304-378, 1111-1131, 1134-1200, 1300-1420`
- `scripts/phase18_extraction.py:60-96, 3100-3250`
- `src/personacore/training/loop.py:240-300, 660-800` · `src/personacore/privacy/dpsgd.py:63, 121-160, 300-360, 392-410, 483-545`
- `src/personacore/config.py:21-72` · `src/personacore/generation/core.py:25-90`
- `tests/test_phase20_prereg.py:60-135, 268-380, 1096-1240` · `tests/test_phase22_accountant.py:1350-1410`
- `tests/test_phase22_checkpoint.py:1-40, 300-540, 671` · `tests/test_phase22_fakes.py:1-135, 173-175, 459-469, 801`
- `tests/test_phase22_dpsgd.py:100-175` · `tests/test_mps_smoke.py:1-30` · `.github/workflows/ci.yml:6, 26-40`
- `results/phase19_noise_floors.json` · `pyproject.toml:24-35` · `Makefile:12-21`

### Secondary (MEDIUM confidence)

- `.planning/STATE.md:357-358, 375, 381, 460, 485-510, 635-646` — decision history, not re-measured
- `.planning/ROADMAP.md:125-145, 550-590` — phase scope and success criteria

### Tertiary (LOW confidence)

- None. No claim in this document rests on a web source or on training knowledge about a library.

---

## Metadata

**Confidence breakdown:**
- R1 (device parametrization): **HIGH** — both failure modes reproduced with exact error text; every
  transfer property measured on both devices.
- R2 (AST guard): **HIGH** — the guard was located, read, and watched RED twice against scratch modules.
- R3 (measurement methodology): **HIGH** for the reproductions and the two new probes; **MEDIUM** for
  the projection to a real `train_arm` run, explicitly bounded as a lower bound (A3).
- R4 (resume seam): **HIGH** — all signatures, call sites and the resume block read at named lines.
- R5 (validation architecture): **MEDIUM** — the requirement→test map is derived from the requirements
  and the existing test shapes; no Phase-23 test has been written or executed.

**Research date:** 2026-08-26
**Valid until:** 2026-09-25 (30 days — the stack is pinned: torch 2.7.1, Python 3.11, no external
services, no fast-moving dependency). The two new probes (§R3.A, §R3.B) should be re-run if the
hardware, the torch version, or `ModelConfig`/`LoRAConfig` change.
