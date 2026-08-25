---
phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
plan: 04
subsystem: privacy
tags: [differential-privacy, dp-sgd, per-record-clipping, gaussian-mechanism, ast-guards, lora]

# Dependency graph
requires:
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-01's src/personacore/privacy/ subpackage and tests/test_phase22_dpsgd_ast.py's three text-taking guards, proven biting on six synthetic mutations"
  - phase: 22-dp-sgd-core-accountant-and-the-correctness-battery
    provides: "plan 22-02's scripts/mitigation_accountant.py::NEIGHBOURING / ::SENSITIVITY_MULTIPLIER and plan 22-03's accountant.py docstring — the two adjacency sites this module's third site must match"
  - phase: 09-lora-injection-and-the-adapter-artifact
    provides: "LoRALinear, inject_lora, mark_only_lora_trainable — the live model D-04's census is derived from, and the trap (inject_lora does NOT freeze) it refuses"
provides:
  - "src/personacore/privacy/dpsgd.py::DPSGD — per-record global clip to a single-sourced self.C, a SUMMED private accumulator, dedicated-generator Gaussian noise on the sum, the /N LAST, and one combining write per parameter"
  - "D-04's three property refusals + a numeric-domain refusal, all as a full pre-pass before any DP state is assigned"
  - "D-16's four runtime invariants, firing every step, each watched raising"
  - "the dpsgd.py noise line — the THIRD of the three sites plan 22-09's V-25 cross-site adjacency test reads"
  - "tests/test_phase22_dpsgd.py — V-22 and V-13, 18 tests"
  - "tests/test_phase22_dpsgd_ast.py's LIVE half — V-11 against the mechanism's real bytes, 6 new tests"
affects: [22-06 the dp_fn seam in _optimizer_step, 22-07 checkpoint dp_noise_rng, 22-09 the four fake probes and V-25, 23 the frontier sweep]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A hard-equality .grad-write ALLOWLIST per closure entry, where an empty-offender assertion is unsatisfiable on correct code — it pins WHICH function writes and HOW MANY, which an `== {}` over a hand-picked scope does not"
    - "A run-lifetime counter that turns 'this finite bound did not bind' from an assumption about fixture magnitudes into an observation about the whole run"
    - "Generator CONTINUITY (this step's pre-draw state == last step's post-draw state) rather than pre-state inequality — it catches a re-seed to any value and any foreign consumer on the same stream"
    - "A runtime invariant re-computed from the clipped tensors rather than from norm * coef, so it is capable of failing"

key-files:
  created:
    - src/personacore/privacy/dpsgd.py
    - tests/test_phase22_dpsgd.py
  modified:
    - tests/test_phase22_dpsgd_ast.py

key-decisions:
  - "D-16 invariant 4 asserts generator CONTINUITY. The plan's 'store the POST-draw state, refuse if the PRE-draw state EQUALS it' is self-contradictory — that equality IS the correct case, so it would redden every honest second step, and it is silent on manual_seed(FIXED), which is FAKE 4 itself"
  - "The live V-11 entries assert a hard-equality .grad-write allowlist, not offenders == {}. Measured against the shipped module, entry=finalize reports {'_write_once': ['.grad=']} and entry=absorb_record reports {'absorb_record': ['.grad=']}; both writes are mandated by D-01, so == {} could only be reached by hiding the release write or by scoping the guard away from it"
  - "C = infinity is a FINITE bound whose non-binding is COUNTED. math.inf is refused: 0.0 * math.inf is nan and torch.normal(std=nan) raises at exactly D-06's identity input"
  - "A fifth refusal, [dp-invariant:lot], was added: the /N LAST must divide by the number of records actually clipped and summed"
  - "requirements.mark-complete was NOT called — fourth consecutive plan. DPSGD-01 additionally needs the seam wired through train() (22-06); DPSGD-04 needs four fakes with their positive controls watched failing (22-09)"

patterns-established:
  - "Refusal marker tags ([dp-refusal:*] / [dp-invariant:*]) that let a test prove pairwise message distinctness per item rather than in aggregate"
  - "Guard mutation probes that repoint the test module's _DPSGD_PATH at a temp copy, so byte-identical restore of the work tree is structural rather than remembered"

requirements-completed: []
requirements-contributed: [DPSGD-01, DPSGD-04]

# Metrics
duration: 45min
completed: 2026-08-25
---

# Phase 22 Plan 04: The DP-SGD Mechanism Summary

**Per-record global clipping to a single-sourced `self.C`, a SUMMED private accumulator, dedicated-generator noise on the sum with the `/N` last, and one combining write per parameter — with D-04's property refusals as a full pre-pass, D-16's four invariants firing every step, and every one of them watched raising: 18 runtime breaks producing 18 REDs across 10 distinct markers, and 8 source mutations producing 8 distinct RED signatures against the live AST guards.**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-08-25T22:00Z (approx, first read after `23e01d7`)
- **Completed:** 2026-08-25T22:45Z
- **Tasks:** 3
- **Files created:** 2 (1 modified)

## Accomplishments

- **The clip is genuinely per-record.** `absorb_record` reads one micro-batch's `.grad`, computes a **global** L2 norm across all 72 trainable LoRA tensors as one vector, scales by `coef`, adds into the accumulator, and drains. The accumulator holds the **SUM**, so one record moves it by at most `C` and the sensitivity is exactly `C` independently of the lot size (D-02). Nothing here clips an averaged gradient.
- **Noise is drawn from a dedicated generator, scaled to `self.sigma * self.C`, and added to the SUM before the divide.** Measured: drawing from `dp._g` leaves `torch.get_rng_state()` `torch.equal` to its pre-draw value; at `sigma = 0` the drawn values are exactly zero **and** the generator state still advances — asserted as two independent facts.
- **D-06's identity holds bit-for-bit on CPU.** At `sigma = 0` and a non-binding `C`, the released term is `torch.equal` to the plain mean of the hand-set record gradients at **both** N = 1 and N = 2. The plan allowed a documented tolerance at N > 1; measured, none was needed.
- **`C = ∞` is an observation, not a hope.** `_clip_bind_count` is asserted `== 0` **before** the identity comparison, and asserted `> 0` in the binding test — the counter is proven to move in both directions.
- **All four D-16 invariants and every D-04 refusal were watched raising.** 18 deliberate breaks, 18 REDs, **10 distinct markers**, no marker shared across invariants.
- **The live V-11 guards read `dpsgd.py`'s real bytes through the same functions plan 22-01 watched biting on six synthetic mutations**, and were themselves watched biting on 8 source mutations with the work tree left byte-identical (`sha256 75b4e3bd…`).
- `pyproject.toml`, `lora/layer.py`, `lora/inject.py`, `mitigation_gate.py`, `mitigation_unit.py` and `mitigation_accountant.py` are all byte-unchanged (`git diff --exit-code` exits 0). DPSGD-07 and RPT-03 hold.

## Task Commits

1. **Task 1: `DPSGD.__init__` — construct-once capture and D-04's three property refusals** — `a786cb8` (feat)
2. **Task 2: the step path — drain, per-record clip, summed accumulator, noise, one write** — `33ba84c` (feat)
3. **Task 3: live V-11 — point plan 22-01's text guards at `dpsgd.py`'s bytes** — `6e45493` (test)

## Files Created/Modified

- `src/personacore/privacy/dpsgd.py` (new, **562 lines**) — module docstring in `perplexity.py`'s register: DPSGD-01 on line 1, a WHAT THIS SEAM CLAIMS / DOES **NOT** CLAIM pair copied in shape from `loop.py`'s `replay_bin` entry, the adjacency paragraph in the pin's own words, and a six-bullet invariants block naming both test files. Then `DPSGD` with `__init__` (a full pre-pass of 9 refusals), `begin_step`, `_global_norm`, `absorb_record`, `_draw_noise`, `_noised_private`, `_write_once`, `finalize`. **Zero `assert`, zero `_prove`, 14 `raise` sites.**
- `tests/test_phase22_dpsgd.py` (new, **472 lines**) — **18 tests**: V-22 ×3 parametrized with per-case marker distinctness, the `runtime.amp` half of refusal 2, the measured `inf → nan → RuntimeError` chain, `test_clip_norm_must_be_finite` ×2 with its large-finite negative side, clean construction with the dedicated-generator proof, and V-13's four invariants each with a watched RED alongside its GREEN.
- `tests/test_phase22_dpsgd_ast.py` (modified, +170 lines, 10 → **16 tests**) — the LIVE half: the hard-equality `.grad`-write allowlist at both step entries, the wrapper live at `_noised_private`, `_assert_single_clip_constant` on the real class, FAKE 4's structural half, and D-08 asserted on the AST grammar.

## Decisions Made

- **Generator continuity, not pre-state inequality.** See Deviation 2. The shipped check is `pre == self._prev_gen_state` (the previous step's **post**-draw state), refusing on inequality. It catches a re-seed to *any* value, a `set_state`, and a foreign consumer draining the same stream — all measured RED — where the plan's stated form catches none of them and reddens correct code.
- **The `.grad`-write allowlist is a strengthening, not a relaxation.** It pins which function performs the write, how many writes it is credited with, and that nothing else in the closure writes one or reaches a forbidden token. Mutation 5 below (the drain moved into a helper) is the evidence: it is GREEN under any `== {}` assertion scoped to a `.grad`-free method, and RED under the allowlist.
- **A fifth refusal, `[dp-invariant:lot]`.** `finalize(accum)` refuses unless `self._records == accum`. The `/N` LAST must divide by the number of records actually clipped and summed; a zero also catches `begin_step`/`absorb_record` never having run. Not in the plan (Rule 2).
- **The sensitivity invariant re-computes the clipped norm from the clipped tensors.** `norm * coef` is exactly `C` by construction and could never fail — a guard incapable of failing is not a guard. The `_UnderReportingNorm` positive control confirms the shipped form bites where the cheap form would not.
- **`_ALLOWED_CLASS_CONSTANTS` was NOT widened, and neither was the clip-operand predicate.** Plan 22-01 Task 2's pinned rule is green on the shipped module as written: `_clip_bind_count` appears only as an `ast.Assign` target in `__init__` and an `ast.AugAssign` target in `absorb_record`, never as a direct `Compare`/`Div` operand, so the clip-bearing set is exactly `{"C"}` and the class body carries no numeric constants. Confirmed by running the guard, not by reading it.
- **`requirements.mark-complete` was NOT called** — fourth consecutive plan, same reason. DPSGD-01 requires per-example clipping + noise *entering `train()` through the new additive seam*, which is plan 22-06. DPSGD-04 requires a battery catching four fakes, each with its positive control **watched failing first**, which is plan 22-09. Both stay `- [ ]`.

## Guards Watched Failing

### The live V-11 AST guards — 8 mutations, 8 distinct RED signatures, control GREEN on all six

Each mutation was written to a `TemporaryDirectory` copy with the test module's `_DPSGD_PATH` repointed at it. The work tree was never written to; `dpsgd.py` was asserted byte-identical afterwards (`sha256 75b4e3bd…`, `True`).

| # | Mutation | Guard(s) that reddened |
|---|---|---|
| 0 | control (unmutated) | **none — GREEN on all six** |
| 1 | `clip_grad_norm_` inserted in `finalize` | `step_reaches[finalize]` |
| 2 | `self._g.manual_seed(1234)` in `_noised_private` | `step_reaches[finalize]`, `noise_path_clean`, **`never_reseeds`** |
| 3 | a second clip constant `self._c2` used in the clip | `one_clip_constant` |
| 4 | `sigma=1.0` given as a default | `no_numeric_default` |
| 5 | the drain moved into a `_drain()` helper | **`step_reaches[absorb_record]`** — the allowlist's key moves |
| 6 | `.backward()` after the noise | `step_reaches[finalize]` |
| 7 | `class DPSGD` renamed | all six (`"class DPSGD" in source` meta-guard) |
| 8 | the module emptied | all six (non-empty meta-guard) |

Row 5 is the load-bearing one: it is the only evidence that the hard-equality allowlist is stronger than an `== {}` assertion scoped to a `.grad`-free method, because that scoping would report GREEN while the drain silently changed owner.

### The runtime invariants and refusals — 18 breaks, 18 REDs, 10 distinct markers

| Break | Raised | Marker |
|---|---|---|
| two `absorb_record` calls for one backward | `RuntimeError` | `[dp-invariant:drain]` |
| the drain loop dropped (`_drained` left false) | `RuntimeError` | `[dp-invariant:drain]` |
| the clip silently not binding (`_UnderReportingNorm`) | `RuntimeError` | `[dp-invariant:sensitivity]` |
| one parameter skipped in the write | `RuntimeError` | `[dp-invariant:single-write]` |
| the private term aliasing its accumulator | `RuntimeError` | `[dp-invariant:single-write]` |
| every parameter written twice | `RuntimeError` | `[dp-invariant:single-write]` |
| `manual_seed(999)` between steps | `RuntimeError` | `[dp-invariant:generator]` |
| a foreign consumer drawing from `dp._g` between steps | `RuntimeError` | `[dp-invariant:generator]` |
| `finalize(2)` after one absorbed record | `RuntimeError` | `[dp-invariant:lot]` |
| `inject_lora` without `mark_only_lora_trainable` | `RuntimeError` | `[dp-refusal:unfrozen-base]` |
| an enabled `GradScaler` | `RuntimeError` | `[dp-refusal:live-scaler]` |
| `RuntimeConfig(device="cuda", amp=True)` | `RuntimeError` | `[dp-refusal:live-scaler]` |
| one LoRA parameter frozen (census only) | `RuntimeError` | `[dp-refusal:census]` |
| `clip_norm = inf` / `nan` / `0.0` | `ValueError` ×3 | `[dp-refusal:clip-domain]` |
| `sigma = -1.0` / `inf` | `ValueError` ×2 | `[dp-refusal:sigma-domain]` |

**The GREEN control on the same fixture:** `records=2`, `writes=72/72`, `clip_bind_count=0`.

### The measurements the assertions rest on

| Quantity | Measured |
|---|---|
| `inject_lora` alone (no freeze) | **172 trainable tensors / 14,223,360 params** |
| `inject_lora` + `mark_only_lora_trainable` | **72 tensors / 331,776 params** = `r*n_layer*18*n_embd` = `8*6*18*384` |
| per-record global norm, fixture gradients | **0.5771376490592957** and **0.5754578113555908** (2 records) |
| `_clip_bind_count` at `C = 1e6` | **0 / 2 records** — the non-binding bound, observed |
| accumulated norm at `C = 1e-3`, after records 1..4 | **0.0010000000474974513**, 0.0014126960886642337, 0.0017305674264207482, 0.0019994378089904785 |
| `_clip_bind_count` at `C = 1e-3` | **4 / 4 records** — the counter moves in both directions |
| `0.0 * math.inf` | **`nan`** |
| `torch.normal(mean=0.0, std=nan, size=(3,))` | **`RuntimeError: normal expects std >= 0.0, but found std nan`** |
| `torch.normal(std=0.0, generator=g)` | exact zeros **and** the generator state advances |
| a `dp._g` draw vs `torch.get_rng_state()` | `torch.equal` before/after — **unchanged** |
| released term at `sigma=0`, non-binding `C` | `torch.equal` to the plain mean at **N = 1 and N = 2** |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 3's two mandated closure entries assert a property that is unsatisfiable on correct code**

- **Found during:** Task 3 (predicted while reading Task 2, confirmed by measurement)
- **Issue:** The plan requires `_assert_no_forbidden_between_noise_and_step(dpsgd_source, entry="finalize")` and a second call with `entry="absorb_record"`. That wrapper asserts `offenders == {}`, and plan 22-01's closure walk counts a `.grad` **Store** as an offender. But the same plan's Task 2 **mandates two `.grad` Stores**: D-01's per-micro-step drain (`p.grad = None` in `absorb_record`) and D-01's single combining write (`p.grad = private`, reached from `finalize`). Measured against the shipped module, the walk returns `{'absorb_record': ['.grad=']}` and `{'_write_once': ['.grad=']}` respectively. The two instructions are internally contradictory: `== {}` at those entries is reachable only by contorting the mechanism to hide its own release write, or by silently rescoping the guard to a method that structurally cannot write `.grad` — the guard getting weaker while looking bigger.
- **Fix:** Solved for the intent and implemented the stronger guard. `_forbidden_calls_reachable_from` — **the same engine the wrapper is a thin assertion over, and the one all six synthetic REDs bite through, with both meta-guards inside it** — is called at both mandated entries and asserted by **hard equality** against an enumerated allowlist naming exactly which function may write `.grad` and how many writes it is credited with. Any forbidden token anywhere in the closure, a third write, or a write that changes owner all redden it. The wrapper itself still runs **live against `dpsgd.py`'s bytes** at `entry="_noised_private"`, the noise-bearing method, where `== {}` is both satisfiable and exactly D-05 axis 1's claim: from the draw through the divide, nothing recomputes, renormalises, re-seeds or writes `.grad`. The reason is recorded in the test source, not only here.
- **Files modified:** `tests/test_phase22_dpsgd_ast.py`
- **Verification:** mutation 5 above (drain moved into a helper) is RED under the allowlist and would be GREEN under any `== {}` scoped away from the writes. Mutations 1, 2 and 6 confirm the forbidden-token half is undiminished.
- **Committed in:** `6e45493`

**2. [Rule 1 - Bug] D-16 invariant 4's stated storage and its stated refusal contradict each other, and the plan's own test only passes under the corrected form**

- **Found during:** Task 2
- **Issue:** The plan says *"Store the post-draw state into `self._prev_gen_state`"* **and** *"Refuse if the PRE-draw state equals `self._prev_gen_state` from the previous step (the generator was re-seeded in between)"*. Measured, `torch.Generator.get_state()` returns a snapshot and the stream is continuous: with nothing touching the generator, step *N+1*'s pre-draw state **equals** step *N*'s post-draw state exactly. So the stated refusal fires on **every correct second step**. Under the other reading (store the PRE-draw state) the equality does mean "rewound", but then the plan's own test — *"calling `dp._g.manual_seed(...)` between steps makes `finalize` raise"* — does **not** raise: a re-seed to 999 produces a pre-state equal to neither the previous pre- nor post-state.
- **Fix:** The shipped invariant asserts **continuity**: store the post-draw state, refuse when this step's pre-draw state is **not** `torch.equal` to it. Strictly stronger than either stated reading — it catches a re-seed to any value (fixed or varying), a `set_state`, and any foreign consumer drawing from the same stream, all three watched RED. The first step is exempt via `self._prev_gen_state is None`, so a checkpoint resume that reconstructs the seam is unaffected. The message states why continuity is asserted rather than pre-state inequality.
- **Files modified:** `src/personacore/privacy/dpsgd.py`, `tests/test_phase22_dpsgd.py`
- **Verification:** `manual_seed(999)` between steps → RED; a foreign `torch.normal(..., generator=dp._g)` between steps → RED; two honest consecutive steps → GREEN with different released gradients from identical records.
- **Committed in:** `33ba84c`

**3. [Rule 2 - Missing critical functionality] `finalize` accepted any divisor, including one that is not the number of records summed**

- **Found during:** Task 2
- **Issue:** D-02 pins the order `sum → noise → divide` and puts the `/N` last, but nothing in the plan constrains `N` to the number of records actually clipped and summed. A caller passing the wrong `accum` releases something that is not the mean of what was charged for, and `accum` reaching `finalize` with **zero** records absorbed releases pure noise while every other invariant stays green.
- **Fix:** `[dp-invariant:lot]` — `ValueError` when `accum < 1`, `RuntimeError` when `self._records != accum`, with the message naming both failure modes.
- **Files modified:** `src/personacore/privacy/dpsgd.py`, `tests/test_phase22_dpsgd.py`
- **Verification:** `test_finalize_refuses_a_divisor_that_is_not_the_record_count` observes both.
- **Committed in:** `33ba84c`

**4. [Rule 2 - Missing critical functionality] the `runtime.amp` half of D-04 refusal 2 was reachable but untested**

- **Found during:** Task 1
- **Issue:** The plan says *"Accept an optional `scaler=` **or** read `runtime.amp`"*, and names only the scaler case in its test list. An untested refusal branch on the P100 fallback is a refusal nobody has watched, and what it prevents there is a **silent** wrong clip rather than a crash.
- **Fix:** `test_seam_refuses_a_live_runtime_amp` constructs `RuntimeConfig(device="cuda", amp=True)` — which `__post_init__` does not clear, asserted as its own positive control — and observes the refusal on a CPU-only box.
- **Files modified:** `tests/test_phase22_dpsgd.py`
- **Committed in:** `a786cb8`

**5. [Rule 3 - Blocking] `make test` / `make lint` still do not resolve the venv**

- **Found during:** verification
- **Issue:** `Makefile` invokes bare `pytest` / `ruff`, which resolve to a pyenv 3.12.13 with no torch. Fourth confirmation (22-01 deviation 3, 22-02, 22-03).
- **Fix:** all verification ran through `.venv/bin/`. The Makefile is untouched — out of scope.
- **Committed in:** n/a

**6. [Rule 1 - Bug] Four `gsd-sdk` mutation-handler defects, hand-repaired before commit**

- **Found during:** state updates
- **Issue:** Fourteenth consecutive session. (a) `state.advance-plan` rewrote `Status: Executing Phase 22` back to `Status: Ready to execute` — identical to 22-01/22-02/22-03. (b) `roadmap.update-plan-progress` wrote the status cell as `In Progress|  |` (no space before the pipe, empty date cell where every sibling carries `-`) — also identical to all three prior plans. (c) The same handler wrote the count as `3/11` because it counts SUMMARY files on disk and ran before this file existed; corrected to `4/11`, and `22-04-PLAN.md`'s ROADMAP checkbox flipped by hand (the handler does not flip the current plan's). (d) `state.add-decision` prefixed all three entries `- [Phase ?]:`.
- **Also measured:** `state.add-decision` **rejects the positional form outright** this session — `gsd-sdk query state.add-decision "<text>"` returns `{"error": "summary required"}`; only `--summary` works. That is new relative to 22-03's record and consistent with its finding that the positional path is the damaged one. `state.record-metric --duration 45min` and `state.record-session --stopped-at ...` both behaved correctly under the `--flag` form, as 22-03 measured.
- **Fix:** all four hand-repaired in place before the metadata commit, each verified by `git diff`.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** `grep -c "Phase ?" .planning/STATE.md` → **0**; `grep -c "\[Phase 22\]: 22-04" .planning/STATE.md` → **3**; `Status: Executing Phase 22`; the roadmap row reads `| 4/11 | In Progress | - |`, matching its siblings byte for byte.
- **Committed in:** the plan metadata commit

### Deliberate departures from the plan text

- **`seed=` and `runtime=` were added to `__init__`'s signature.** The plan's own text requires "a caller-supplied seed argument" and "an optional `scaler=` **or** `runtime.amp`" without naming either parameter; both are keyword-only with `None` defaults and neither is a σ or C literal.
- **Task 1 ships 8 tests, not the 6 the acceptance criterion computes.** The two extras are the `runtime.amp` refusal (Deviation 4) and the `inf → nan → RuntimeError` positive control hoisted into its own test so it is asserted **once** rather than inside each parametrized case. Plan 22-06's bounds should be computed off **18** for this file, not 6 or 11.
- **`test_sum_then_noise_then_divide` is parametrized over N = 1 and N = 2 and uses `torch.equal` at both.** The plan allowed "documented tolerance at accum>1"; measured under torch 2.7.1 the identity is bit-exact at N = 2 as well (the accumulator starts at `+0.0`, `x + 0.0` and `x * 1.0` are bit-identical for finite `x`, and division by 2 is exact), so no tolerance was introduced. A tolerance nobody needs is a tolerance a future error can hide in.
- **Line anchors are cited by symbol, not by line number** inside `dpsgd.py` (`lora/layer.py::LoRALinear.merge`, `lora/inject.py::set_adapter_enabled`, `scripts/teach_persona.py`'s census), continuing the habit 22-02/22-03 adopted after seven stale anchors were measured in this repository.
- **The acceptance grep `sigma\s*=\s*[0-9]` matched docstring prose**, not defaults (`sigma = 0 is the identity`, etc.). The prose was reworded (`a sigma of zero`) so the grep is clean, but the load-bearing check is the plan's own structural one: `test_dpsgd_has_no_numeric_sigma_or_clip_default` asserts both `kw_defaults` slots are `None` on the AST, behind a meta-guard that some other keyword-only argument **does** carry a default.
- **The `_write_once` count check also catches a double `finalize`** (measured: two writes per parameter → `[dp-invariant:single-write]`), because `_writes` is reset by `begin_step` rather than by the write itself.

---

**Total deviations:** 6 auto-fixed (2 internally contradictory plan instructions, 2 missing refusals/tests, 1 blocking environment issue, 1 tooling corruption), 6 deliberate departures.
**Impact on plan:** every correction makes the mechanism refuse **more** or assert **more precisely**; none weakens a guard. No scope creep — `pyproject.toml`, `lora/layer.py`, `lora/inject.py` and all three `scripts/mitigation_*.py` are byte-unchanged.

## Issues Encountered

- **Seven `ruff` `E501` wraps** across the module docstring, refusal messages and test docstrings; no assertion text or semantics changed. One `ruff format` pass collapsed a list comprehension in `__init__`.
- **The `.gitignore` modification present at session start is pre-existing and untouched** — it was not staged in any commit here.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_phase22_dpsgd.py -q` | **18 passed** |
| `.venv/bin/python -m pytest tests/test_phase22_dpsgd_ast.py -q` | **16 passed** (10 synthetic + 6 live) |
| Live V-11 mutation probe | **8 mutations, 8 distinct RED signatures**, control GREEN on all six guards |
| Work-tree `dpsgd.py` after the probe | byte-identical (`sha256 75b4e3bd…`) |
| Runtime invariant/refusal probe | **18 breaks, 18 REDs, 10 distinct markers** |
| `grep -nE "^\s*(assert \|_prove\()" dpsgd.py` | **no matches** (rc=1) |
| `grep -nE "sigma\s*=\s*[0-9]\|clip_norm\s*=\s*[0-9]" dpsgd.py` | **no matches** (rc=1) |
| `grep -nE "if .*sigma.*==\s*0\|if not self\.sigma" dpsgd.py` | **no matches** (rc=1) — no branch skips the draw |
| `manual_seed` as a CALL outside `__init__` | none (AST); the only textual hit elsewhere is inside a refusal message |
| `self.C` read sites in code | clip (`:389`, `:395`), sensitivity (`:407`), noise `std` (`:439`) — no other float used as a clip bound |
| `_clip_bind_count` | one `AugAssign` in `absorb_record`'s binding arm; **no read inside `finalize`** |
| `_assert_single_clip_constant(dpsgd, "DPSGD", "C")` | GREEN, allow-set **not** widened |
| One definition of `_assert_no_forbidden_between_noise_and_step` | **1** — the live tests call it, they do not re-implement it |
| `git diff --exit-code -- pyproject.toml lora/{layer,inject}.py scripts/mitigation_{gate,unit,accountant}.py` | exit 0 — byte-unchanged |
| Full suite `.venv/bin/python -m pytest -q` | **1107 passed, 1 skipped** in 202.92 s (baseline 1083/1 + 24 new) |
| `.venv/bin/ruff check . && ruff format --check .` | clean, **200 files** formatted |

## Known Stubs

None. Every method is complete and consumed by a committed test. `DPSGD` is deliberately **not** re-exported from `personacore/privacy/__init__.py` — plan 22-01 recorded the no-re-export decision, and adding one would put torch in the package's import graph for the sake of a shorter import line.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no file access at all (`dpsgd.py` opens nothing), and no schema. It installs nothing.

Threat register dispositions, each mitigated as planned:

- **T-22-15** (sensitivity silently becoming `N*C`) — invariant 1 refuses from **both** ends (a stale `.grad`, and a dropped drain leaving `_drained` false), invariant 2 refuses a clipped norm above `C*(1+tol)` recomputed from the clipped tensors. Both watched RED; both `raise`, never `assert`.
- **T-22-16** (an unfrozen base presented as LoRA-only) — refusal 1 audits by PROPERTY using `inject.py`'s own `"lora_" in name` predicate; refusal 3's census is derived entirely from the live model. The 172 / 14,223,360 positive control is asserted before its refusal.
- **T-22-17** (a second clip constant) — `_assert_single_clip_constant` hard-equality `{"C"}` on the real bytes, watched RED on mutation 3; the runtime `C*(1+tol)` check reads the same attribute.
- **T-22-18** (an in-step `manual_seed`) — AST watched RED on mutation 2; runtime continuity check watched RED on two separate breaks.
- **T-22-19** ("noise was added" unverifiable at σ=0) — no branch skips the draw (grep and AST); exact zeros **and** generator advance asserted as two independent facts.
- **T-22-20** (a live `GradScaler`) — refusal 2 watched RED on both the scaler and the `runtime.amp` route.
- **T-22-20b** (`clip_norm = math.inf` → `nan` std) — refusal 4 watched RED on `inf`, `nan` and `0.0`; the crash it prevents is recorded as its own test; `_clip_bind_count == 0` makes the non-binding representation an observation.
- **T-22-SC** (package installs) — accepted; nothing installed, `pyproject.toml` byte-unchanged.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 22-06** threads `DPSGD` through `_optimizer_step`. Four things it must inherit rather than re-derive: (i) the call order is `begin_step()` → `absorb_record()` **after each** `scaler.scale(loss).backward()` → `replay_fn(model, scaler)` → `finalize(accum)` → `optimizer.step()`; (ii) the DP path must **bypass `loop.py`'s `loss = total / accum`** — `absorb_record` clips the UNDIVIDED per-record gradient, and inheriting the divide is D-02's wrong-sensitivity fake arriving for free; (iii) `finalize(accum)` refuses unless `accum` equals the number of records absorbed; (iv) `dp_fn`'s `sigma`/`clip_norm` arrive keyword-only with no default all the way out to the CLI (D-08) — no Phase-22 file may name a value.
- **Plan 22-07** (checkpoint) reads `dp._g.get_state()` for the `dp_noise_rng` `**extra` slot. Note it must be refreshed at save time: `_prev_gen_state` holds the last **post-draw** state and the invariant asserts continuity across steps, so a resume that restores `_g` into a fresh `DPSGD` is safe (`_prev_gen_state` is `None`, first check skipped) while a resume that restores mid-object would need `_prev_gen_state` restored alongside it.
- **Plan 22-09 owns V-25, and this plan supplied its third site.** `dpsgd.py`'s docstring and the annotation on the noise line both carry the literal `add/remove one fact` and the multiplier `1.0`, in `mitigation_accountant.py::NEIGHBOURING`'s own words, matching `accountant.py`'s docstring paragraph.
- **Plan 22-09's fake probes** feed mutated strings to the same three helpers. Two of the four fakes now have a **live** counterpart already watched biting here: FAKE 2 (mutation 3) and FAKE 4 (mutation 2). It should also know that `entry="finalize"` / `entry="absorb_record"` cannot use the `offenders == {}` wrapper — see Deviation 1 and `_ALLOWED_GRAD_WRITES` in the test source.
- **Environment note, fourth confirmation:** `make test` and `make lint` do not resolve the venv on this box. Use `.venv/bin/python -m pytest -q` and `.venv/bin/ruff check .` / `.venv/bin/ruff format --check .`.

## Self-Check: PASSED

- `src/personacore/privacy/dpsgd.py` — FOUND
- `tests/test_phase22_dpsgd.py` — FOUND
- `tests/test_phase22_dpsgd_ast.py` — FOUND
- commit `a786cb8` — FOUND
- commit `33ba84c` — FOUND
- commit `6e45493` — FOUND

---
*Phase: 22-dp-sgd-core-accountant-and-the-correctness-battery*
*Completed: 2026-08-25*
