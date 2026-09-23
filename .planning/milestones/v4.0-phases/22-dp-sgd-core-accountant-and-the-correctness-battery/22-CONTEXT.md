# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery - Context

**Gathered:** 2026-08-25
**Status:** COMPLETE — D-01 … D-18, 0 open. Ready for `/gsd:plan-phase 22`.

> **D-18 was added on 2026-08-25 after the research pass**, on the user's explicit decision. It pins
> the **adjacency relation** — a stated precondition of `μ = Δ/σ` that `.planning/research/PITFALLS.md`
> P3 assigned to Phase 20/21 and that **measurably never landed** (zero hits in `scripts/`, `src/`,
> `tests/`). It is the one gap D-17's guards structurally cannot reach.
>
> **One naming correction, recorded here rather than by editing a locked decision.** D-12's phrase
> `μ = C/σ` is outlier wording: `σ` is the **noise multiplier** (`σ_noise / C`, unitless), so
> `μ = 1/σ` and `μ_eff = √T/σ`. Three committed artifacts agree —
> `scripts/mitigation_gate.py:1026` (`MECHANISM_KEYS = ("sigma", "steps", "delta", "q")`, FROZEN, its
> own comment saying *"there is no fifth key"*), `:161` (*"the recorded **noise multiplier**"*), and
> `.planning/research/ARCHITECTURE.md:14` (`μ = √T/σ`). D-12's substance is unaffected — `1.0/0.0`
> still raises `ZeroDivisionError`, so the explicit `σ=0 → ε=∞` branch is still required. **The plan
> must NOT add a `clip_norm=` parameter to `epsilon_for`**: that would create the fifth mechanism key
> the frozen gate says does not exist. See `22-RESEARCH.md` F4.

> **Numbering.** A bare `D-NN` is always **this phase's** decision. Phase 20's and Phase 21's are
> always written `Phase 20 D-NN` / `Phase 21 D-NN`. This matters: Phase 21 D-01/D-02/D-07 are
> different decisions from Phase 22 D-01/D-02/D-07.

> **Every number below was measured against HEAD during the discussion, not transcribed.** Where a
> measurement has a weak bound it is stated rather than glossed, following Phase 21 D-02's precedent.
> Probe conditions, unless a decision says otherwise: real `GPT(ModelConfig())` + `inject_lora` +
> `mark_only_lora_trainable` (72 tensors, 331,776 params), CPU, `grad_accum_steps = 8`, **synthetic
> `torch.randint` ids at model init**, single process, no confidence interval.

<domain>
## Phase Boundary

Phase 22 builds the **DP mechanism itself** and proves it is not the cheap fake — entirely on CPU,
before a single second of M3 time is spent. Requirements DPSGD-01, -02, -03, -04, -05, -07.
Depends on Phase 21 (complete, 11/11 verified).

Implied deliverables, from ROADMAP SC1-SC5:

1. Per-example clipping + Gaussian noise on the **LoRA gradients only**, base frozen, entering
   `train()` through a **new additive gradient-side seam** (DPSGD-01)
2. Seam-off bit-identity against the Phase-10 golden-trajectory fixture (DPSGD-02)
3. An (ε, δ) accountant in stdlib `math` only, exact under q=1, agreeing with **two oracles of
   different mathematics** (DPSGD-03)
4. A correctness battery catching four silent-non-privacy failures, each with its **positive control
   watched failing first** (DPSGD-04)
5. An MPS RNG slot in `checkpoint.py` with backward-compatible load, a kill→resume reproducing a
   **bit-identical reported ε**, and `LoRALinear` left unrestructured (DPSGD-05, DPSGD-07)

**No ε value is chosen in this phase, and no scored artifact is written.** σ and C are Phase 23
resource parameters (Phase 20's Z boundary). DPSGD-06 — the σ=0 point as the DP arm's first
*executed* run — is **Phase 23**, deliberately not borrowed here (D-06).

### Carried forward — locked, not reopened

- **Phase 21 D-02** — one micro-step **is** one privacy record under ragged fact-aligned
  accumulation, so ordinary backward hands back the per-record gradient and `vmap` leaves the
  critical path (ragged 1.14× vs uniform 1.39× vs vmap-uniform 1.35×). The extraction mechanism is
  decided; Phase 22 does not re-litigate it.
- **Phase 21 D-07 / D-23** — `q = 1`, `N = n_facts`, `δ = 1e-5`, frozen in `scripts/mitigation_unit.py`.
- **Phase 21 D-25** — replay is its own un-clipped pass per lot, structurally outside the per-record
  loop. `replay_fn` already exists at `loop.py:178-179`.
- **Phase 21 D-19 … D-22** — a `scripts/mitigation_*.py` sibling is *protected but not frozen* by
  default; only a hand-written `PHASE**_PREREG_ARTIFACT` path constant confers the freeze; the glob
  imposes a hard import ceiling and forces the rule/emission split.
- **Phase 21 D-20** — adding a prefix to `V4_ARTIFACT_GLOBS` **enforces nothing by itself**; a
  matching `_assert_ordering_holds(artifact_glob=…)` call is the other required half.
- **Phase 20 D-24** — `mitigation_gate.py` and `mitigation_unit.py` are FROZEN. Corrections are
  dated continuations via `scripts/_addendum.py`, never edits.
- **Phase 20 D-21** — the ancestry guard copies the **Phase 18 shape** (green while zero artifacts
  are tracked, non-zero demanded from the first onward), never Phase 16's.
- **DPSGD-07** — `LoRALinear` stays bare `nn.Parameter`s; `persona_adapter.pt` and every v3.0
  checkpoint must still load unchanged.

### What this phase inherits BROKEN, measured rather than assumed

`python scripts/teach_persona.py dp_n8` is **CLI-reachable today** (`teach_persona.py:249-250`) and
produces a non-DP adapter under a DP name. Four gaps, not the one IN-04 recorded:

| # | measured state | evidence |
|---|---|---|
| 1 | **`get_batch_fact_aligned` has no path through `train()` at all** | zero hits for `fact_bin` / `fact_aligned` / `align_facts` in `loop.py`; `batch_fn` routes only to `get_batch_memmap{,_masked}`. Its sole non-test caller is `scripts/phase21_unit_record.py` — the *reporting* driver |
| 2 | **`grad_accum_steps` is never set at the caller** | `TrainConfig(...)` at `teach_persona.py:1167` omits it → default `1` (`config.py:106`). The phrase appears **9× in `teach_persona.py` prose and 0× in its code** |
| 3 | the replay seam is unwired | Phase 21 IN-04, re-confirmed: `:1167` passes no `replay_*` |
| 4 | no DP | this phase's job |

So the arm builds the correct three-bin aligned corpus and then trains it through **the flat
random-window loader UNIT-01 exists to indict**, at `grad_accum_steps = 1`, with no replay. SC2's
"one micro-step = one privacy record" is prose at the only production caller. D-08 closes all four.

### A stale anchor inherited from the roadmap, corrected here so it is not propagated

ROADMAP SC4 and `.planning/REQUIREMENTS.md:135` both cite **`loop.py:165`** as the site that "already
clips exactly the LoRA grads on the averaged gradient". Measured, `:165` is
`accum = max(1, train_cfg.grad_accum_steps)`; the clip is **`:181`**. Same defect class as Phase 21's
own IN-02 (stale line anchors inside a frozen pin). **Every path in this document was resolved
against the tree, never transcribed from a planning document.**

</domain>

<decisions>
## Implementation Decisions

### The gradient seam — who owns `.grad`, and in what order

- **D-01 — the private accumulator is DP-owned; replay stays in `.grad` untouched, and
  `p.grad += private_accum` is the SINGLE write that combines the two terms, immediately before
  `optimizer.step()`.** Per micro-step: backward → read `.grad` → `clip(·, C)` → add to
  `private_accum` → **drain `.grad`**. Then `replay_fn()` runs and `.grad` holds the public term
  exactly. Then noise, then the one combining write. **Nothing re-normalizes after that sum.**

  **The drain is load-bearing and is a consequence, not a detail.** `backward()` accumulates, so
  without a per-micro-step zero, record *i*'s clip would see records 1..*i* summed and the true
  per-record sensitivity would silently become `N·C`. Today `_optimizer_step` zeroes **once**, at
  `loop.py:164`. The per-micro-step zero therefore lives **inside the DP branch**, so the default
  path stays byte-identical (DPSGD-02).

  **What Phase 21 actually left open, stated precisely.** Phase 21 D-25's separation is real at the
  **data source** *and* at **control flow** — `replay_fn` is a distinct callable invoked once per
  step, outside `for micro in range(accum)`. It stops exactly at the **accumulator**: `loop.py:472`
  calls `scaler.scale(loss).backward()` into the same `.grad` tensors, and `loop.py:275-279` says so
  in its own words. **Measured:** private-only grad norm `0.143608`, private+replay `0.436096`,
  `torch.allclose(mixed, private_only)` → **False**. Replay is **67.1%** of the mixed norm and is
  **inseparable after the fact**.

  **The rejected alternatives, for the record.** (a) *Both terms in DP-owned buffers with `.grad`
  written exactly once* — equivalent in guarantee, larger diff, and it would edit `replay_fn`, which
  is proven bit-identical-when-off and better left alone. (b) *Tensor hooks intercepting at write
  time* — **measured infeasible for this clip**: a per-record **global** norm over all 72 tensors is
  not knowable until `backward()` completes, while hooks fire per-tensor mid-backward. Hooks would
  force per-**parameter** clipping, which is a different and weaker sensitivity bound than DPSGD-01
  states.

- **D-02 — `sum → noise → divide`. The per-record backward is UNDIVIDED, so `clip(g_i, C)` gives
  sensitivity exactly `C`, independent of N.** `private_accum` holds the **sum** of clipped
  gradients; `N(0, σC)` is added to that **sum** once (one record moves the sum by at most `C` — the
  textbook sensitivity argument); the `/N` happens **last**. `loop.py:175`'s `loss = total / accum`
  is bypassed on the DP path alongside the legacy clip.

  **This is the trap the drain exposed, and it is reachable by inheriting one existing line.** With
  `/accum` inherited, `.grad` after each backward holds `g_i / N`, so clipping *that* to `C` sets the
  true per-record sensitivity to `C·N` while the accountant is told `C`. That is DPSGD-04's
  **"noise scaled to the wrong sensitivity"** fake, arriving for free, and it converges fine.

  **Why sensitivity-independent-of-N is the property worth protecting:** it is exactly what makes
  σ and C *alone* sufficient inputs to the accountant, with no dependence on lot size. Rejected:
  keeping `/accum` and compensating with `C/N` — arithmetically equivalent, smaller diff, but the
  accountant's `C` and the code's clip constant stop being the same number, every guard and every
  report has to carry the N factor, and the wrong-sensitivity fake becomes a one-character edit no
  magnitude check can see.

- **D-03 — the legacy `clip_grad_norm_` at `loop.py:181` is STRUCTURALLY UNREACHABLE on the DP
  path**, inside an `if dp_fn is None` branch, **proven by call-graph inspection rather than by a
  runtime-measured norm**. DPSGD-02's bit-identity proof against
  `tests/fixtures/golden_trajectory_v1.json` is extended to cover the branch — the `penalty_fn`
  playbook, already the shape.

  **The user's stated rule was "nothing re-normalizes after noise is added." That is STRONGER than
  DP requires, and adopting it on the wrong basis would have been a published over-claim.** DP is
  closed under post-processing: once the noised sum is released, `clip_grad_norm_`, weight decay and
  **AdamW's own per-parameter rescale by √v** are all functions of the noised gradient alone, so
  (ε, δ) survives all of them. An absolute rule would forbid the optimizer. **The rule that survives
  contact is "nothing between the noise and `optimizer.step()`", and its real basis is three
  measured things:**

  1. `clip_grad_norm_(model.parameters(), …)` runs over the **mixed** buffer, so the private noised
     term's released magnitude becomes a function of **public** data. Not a privacy break — but it
     makes "the public term is independent of the private records" unstateable in the direction the
     report needs.
  2. **It defeats a DPSGD-04 positive control.** Wrong sensitivity is detectable in the released
     magnitude; renormalizing to a fixed norm **erases exactly that signal**. The fake would
     converge *and* pass.
  3. Measured, it is **inert by accident, not by construction**: at the frozen-base regime pre
     `0.436096` → post `0.436096`, factor `1.000000`, does not bind at `grad_clip = 1.0`. Whether it
     binds on the **real corpus** at 200 overfit steps is **unmeasured**. Inert-by-accident is the
     definition of convention.

- **D-04 — three PROPERTY refusals at DP wiring time, not name checks.** Raise if **any** non-`lora_`
  parameter has `requires_grad`; raise if the scaler is enabled; assert the trainable count equals
  `LORA_CFG.r * n_layer * 18 * n_embd` = **331,776**.

  **Trap 1, measured: `inject_lora` does NOT freeze.** `mark_only_lora_trainable` is a **separate
  call** (`lora/inject.py:46`), made only by `teach_persona.py:1147` and
  `train_adapter_smoke.py:107`. Measured without it: **172 trainable tensors / 14,223,360 params**,
  and there the legacy clip **does** bind — `4.005655 → 1.000028`, factor `0.249654`. A DP caller
  that omits one line noises 14.2M parameters against a sensitivity computed for 331,776 — the
  wrong-sensitivity fake, **reachable by omission**, with no guard today.

  **Trap 2, measured: a live `GradScaler` makes per-record clipping structurally impossible.**
  `unscale_()` twice per optimizer step raises
  `RuntimeError: unscale_() has already been called on this optimizer since the last update().`
  Reading `.grad` mid-accumulation under a live scaler yields **scaled** gradients, so clipping
  against `C` is wrong by the scale factor. `RuntimeConfig.__post_init__` (`config.py:56-59`) forces
  `amp=False` on both `cpu` and `mps`, so it never bites on the primary path — **the P100 fallback
  needs a refusal, not a silent wrong clip.**

  The count assertion is not redundant with the `requires_grad` audit: it additionally catches a
  future `LoRAConfig.r` change that would move the count without updating the calibrated
  sensitivity. `teach_persona.py:1148-1156` already runs this exact closed-form census with a
  `SystemExit`; D-04 puts it at the **seam**, so it is a property of the mechanism rather than of
  one caller.

- **D-05 — four ORTHOGONAL enforcement axes, none redundant with the other three.**
  1. **AST guard over the call graph** — between the noise call and `optimizer.step()` there is no
     `.backward()`, no `.grad` write, and no clip/normalize call; and the legacy clip's only
     reachable site is inside the `if dp_fn is None` branch. Catches a **future edit** that a
     runtime check on today's inputs would not. (This project's own pattern: Phase 15's plotting
     import-walk, the `mitigation_budget` import guard.)
  2. **Runtime differential, one kwarg apart** — the same step run twice differing only in whether
     the public term is present, asserting the private noised contribution is byte-identical across
     both. The `tests/test_phase21_replay_volume.py::test_side_channel_negative_control` shape,
     which is what makes the claim a property of the **branch** rather than of two fixtures.
  3. **Single-write assertion on `.grad`** — instrument writes during a DP step; assert exactly ONE
     combines the two terms, that it is the final one before `step()`, and that `private_accum`
     never aliases any `.grad` (distinct `data_ptr()`). Turns "a single write" from a described
     sequence into a **measured count**.
  4. **Per-micro-step drain assertion** — `.grad` is `None` at the top of every DP micro-step, so
     `clip(g_i)` provably sees one record and never a running sum. Catches the drain being dropped
     by a later refactor: the failure mode that would silently restore per-record sensitivity to
     `N·C` with every other guard still green.

  **Widened at D-17:** axis 1 also refuses a second clip constant and an in-step generator re-seed,
  because both remaining fakes are *positive code insertions*.

### Proof boundaries — two σ=0 claims that must never be conflated

- **D-06 — Phase 22 ships a CPU/fixture bit-identity; Phase 23 ships the real-corpus diagnostic; they
  are NAMED SEPARATELY so no future reader cites one for the other.**

  | | Phase 22 (here) | Phase 23 (DPSGD-06) |
  |---|---|---|
  | claim | **mechanism** correctness | **scientific result** correctness |
  | run | CPU, fixture scale | M3, real corpus, 200 steps |
  | assertion | `train(dp_fn=None)` ≡ `dp_fn(σ=0, C=∞)`, bitwise or documented tolerance | σ=0 reproduces the unmitigated control within the measured seed-to-seed noise floor |
  | property | deterministic, CI-reproducible | **not** bit-identical, by design |

  This is what pins D-02's `1/N` placement **structurally rather than by argument**: get the divide
  wrong and the CPU identity breaks immediately, before any M3 time. It is the `borrowed_cap`
  discipline from Phase 20 — two artifacts, two claims, neither borrowing the other's weight.

### The noise source and its checkpoint state

- **D-07 — a DEDICATED `torch.Generator`, never the global stream, with `σ=0` producing exact zeros
  through the SAME code path — the generator is still consulted, same call sequence, no conditional
  branch that skips the call.** No branch means "noise never got added" has nowhere to hide.

  **The measured trap this avoids.** `torch.normal(0, 0)` returns **exact zeros but ADVANCES the
  torch RNG stream**. Today that would be harmless — the data path draws from **numpy**
  (`data.py:117`, `np.random.randint`), `Dropout(p=0.0)` does **not** consume torch RNG (`p=0.5`
  does), and one full `GPT + LoRA` train-mode forward advances the torch RNG by **zero**. But that
  independence rests entirely on `ModelConfig.dropout = 0.0` (`config.py:92`) and
  `LoRAConfig.dropout = 0.0` (`lora/config.py:25`), **neither of which is pinned**, and
  `LoRAConfig.dropout` is an ordinary sweep knob. A dedicated generator makes the property
  structural instead of contingent. *(The measurement also independently confirms DPSGD-05's stated
  premise: the loop consumes zero device RNG today, and DP noise is the first per-step consumer.)*

- **D-14 — the generator is bound to the REAL execution device, and TWO separately-named checkpoint
  slots coexist, each proving a different thing, neither collapsed into the other:**
  - `rng["mps"] = torch.mps.get_rng_state()` when available — **DPSGD-05's literal requirement**,
    backward-compatible via `rng.get("mps")`, mirroring the `cuda` slot at `checkpoint.py:106`.
    **Recorded honestly as required-but-unexercised**, so no future reader believes the DP path
    fires it.
  - `dp_noise_rng = dp._g.get_state()` — 44 bytes, an `**extra` key, **the slot the DP path actually
    fires**.

  **Four measurements decided this, and two of them cut against the obvious reading.**

  | measured | value |
  |---|---|
  | CPU vs MPS generator, same seed | **not identical** — entirely different sequences |
  | CPU generator filling an MPS tensor | `RuntimeError: Expected a 'mps' device type for generator but found 'cpu'` — the CPU route means draw + `.to("mps")` |
  | noise cost, 72 tensors / 331,776 params | native MPS **1.428 ms/step** vs CPU+transfer **10.234 ms/step** (7.2×) |
  | ⇒ at `MAX_STEPS = 200`, drawn once per lot | delta **1.76 s per arm** against 4.77 h/point evaluation — **0.01%; cost decides nothing** |
  | a real fwd+bwd on MPS | leaves `torch.mps.get_rng_state()` **unchanged** |
  | **a DEDICATED generator's draw** | does **not** change the global MPS state; its own 44-byte state changes; `set_state` round-trips exactly |

  **The first cut:** "a CPU generator makes the CPU battery prove the M3 run" **cannot complete**,
  for a reason that predates RNG entirely. `tests/test_loop_penalty_fn.py:12-20` already
  platform-gates the golden replay because fp32 transcendental kernels are not bit-stable across
  OS/arch/BLAS or torch releases. A CPU generator would make the *noise values* device-independent
  while the resulting *weights* still would not match — a partial property with no completion.

  **The second cut, and it is a tension inside the "make the MPS slot load-bearing" argument
  itself:** because D-07 already locked a **dedicated** generator, choosing `device="mps"` does
  **not** exercise the global MPS state. The "guard that never fires" problem is not decided by the
  generator's device at all — it is decided by **which slot carries the DP state**. Hence two slots,
  named apart.

### Wiring — Phase 22 does not hand a downstream phase an unexercised seam

- **D-08 — Phase 22 wires FOUR PATHS at `scripts/teach_persona.py::main()` on the TWO DP arms
  (`dp_n8`, `dp_n64`) and proves it by an END-TO-END CPU fixture-scale run that completes and writes
  NO scored artifact.**
  1. `train()` gains an additive `fact_bin=` seam routing `batch_fn` to `get_batch_fact_aligned`;
     `None` byte-identical.
  2. `grad_accum_steps` derived from `len(align_facts)`, with a refusal on disagreement.
  3. The replay seam wired — `replay_windows = replay_window_budget(n_facts) // BLOCK_SIZE`
     (`REPLAY_WINDOWS_PER_FACT * n_facts`, Phase 21 D-11/D-24). Closes IN-04.
  4. `dp_fn` wired.

  **σ and C arrive keyword-only with NO DEFAULT**, on both the `dp_fn` constructor and the CLI. **No
  literal exists anywhere in Phase 22's tree**, so there is nothing for Phase 23 to override and
  nothing to drift — Phase 20's Z boundary stays untouched because Phase 22 never names a value.
  Phase 23 supplies both from `scripts/mitigation_budget.py`. This is `mitigation_gate.py`'s own
  discipline verbatim ("every argument keyword-only, no defaults").

  **The premise-correction that decided this, recorded because the corrected version is stronger.**
  The stated reason was "there's no later phase positioned to close this gap." That is **false in the
  letter**: Phase 23 is not merely positioned, it is **structurally unable to proceed without** it —
  DPSGD-06 needs the σ=0 point to be the DP arm's first *executed* run, and CAL-01 needs wall-clock
  "measured on the DP path **with the seam active**". Neither is reachable without a caller.

  **It is true in the spirit, and that is the load-bearing half.** Phase 21 also had a downstream
  phase forced to consume its seam — this one — and the seam still arrived unwired, with three
  uncounted companions. And the asymmetry with the replay case is real for a sharper reason:
  **Phase 23's first act is a measurement.** If the wiring lands there, its first executed run is
  simultaneously the first test of four never-executed integration paths, so a wiring bug and a
  DP-correctness bug land in the same artifact, indistinguishable — **destroying DPSGD-06's entire
  purpose, which is to separate "DP is hard at this scale" from "the DP code is wrong."**

  Wiring costs nothing against the roadmap's no-M3-time boundary, because **wiring is not
  executing**. Adversarial arms are **Phase 24** (ADVT-01..03) — a data-mixture ratio with no new
  training seam — and are out of scope here.

### The accountant — the split, its two homes, and the ordering

- **D-09 — the FROZEN half is `scripts/mitigation_accountant.py`: rule AND golden vectors in one
  file, ZERO imports.** `REQUIRED_FORM` names the analytic Gaussian composition (Balle–Wang);
  `REJECTED_FORM` names `sqrt(2*ln(1.25/δ))/σ` explicitly as rejected **without transcribing its
  logic**; `GOLDEN_EPSILON` pins **outputs** for known inputs with **no executable formula in the
  file**; and the isolated composition-property proof (`z_eff` under T-fold reducing correctly to
  `T ** 0.5` — an operator, no import) sits in the same file, **protecting form and result as a
  single inseparable unit**.

  **Why the pin is outputs rather than a formula, and why the risk is not the one it first looks
  like.** Measured: **ε is NOT an input to the gate.** `mitigation_point_verdict`'s 21 keyword
  arguments (`mitigation_gate.py:637-660`) contain no ε — a re-derived accountant **cannot** move a
  point from FAIL to PASS. ε enters exactly **one** place: `capacity_comparison`'s **D-26 fallback
  route** (`:1148-1168`), where `epsilon_gap = abs(small["epsilon"] - large["epsilon"])` is compared
  against `fallback_epsilon_tolerance` — and that route is reached only if CAL-03 *falsifies*
  "ε is independent of N at q=1". On the primary route, Phase 20 D-25's equivalence is agreement on
  `MECHANISM_KEYS = ("sigma", "steps", "delta", "q")` (`:1026`) with **zero tolerance**; ε is never
  compared numerically at all.

  So the accurate risk is: a changed accountant moves **the published ε label on every point** — the
  headline claim's own units — plus the GATE-10 branch on **one conditional route**. Publication
  integrity plus one live path, not verdict-flipping. Because what is at risk is ε's **value**
  rather than a threshold comparison, the pin that bites is the **output table**, which also happens
  to need no imports.

- **D-10 — the COMPUTATION half is `src/personacore/privacy/accountant.py`.** Imports `math` only
  (stdlib), `pyproject.toml` untouched so RPT-03's zero-new-dependency streak holds. **First v4.0
  content inside `src/` — a deliberate decision, not an accident:** a hand-written numerical
  accountant earns the same portfolio visibility `evaluation/perplexity.py` already has, not
  orchestration-script status.

  **The split is FORCED by a mechanism no requirement names.** `tests/test_phase20_prereg.py:915`
  asserts `imported <= {"pathlib", "sys", "erasure_gate"}`, accumulated across **every**
  `scripts/mitigation_*.py`. `math` is not in it, and `from_erasure_gate` is asserted by **exact
  equality** to five names (`:931-945`), so no `erf` arrives that way either. `sqrt` is reachable as
  `x ** 0.5`; **`exp` and `erfc` are reachable by no operator**, and hand-rolling a series for `exp`
  inside a frozen pin is strictly worse than the problem. `scripts/mitigation_unit.py` has **zero
  imports** for exactly this reason. **Widening the allow-set was rejected** on Phase 21 D-22's own
  words: it loosens a subset assertion whose stated purpose is "catches the one nobody anticipated",
  and the first thing it would ever have caught would be us.

  Also measured, and it is why `scripts/` was even a candidate: **`src/` never imports `scripts/`** —
  zero `sys.path` inserts in the package; `pyproject.toml:26`'s `pythonpath = ["."]` puts the repo
  **root** on the path, not `scripts/`; tests reach `scripts/` modules by explicit
  `sys.path.insert(0, _SCRIPTS)` (`tests/test_phase21_filler.py:43-44`). Nothing on the DP path needs
  the accountant from inside the package — `dp_fn` consumes σ and C, not ε, and `extra_eval_fns`
  dicts are built by the caller, which is already `scripts/`-side. So `scripts/` would have worked;
  the package was chosen on the portfolio argument, with the dependency question settled rather than
  assumed.

- **D-11 — Phase 22 adds `results/phase23_*` to `V4_ARTIFACT_GLOBS` AND calls
  `_assert_ordering_holds(prereg_artifact="scripts/mitigation_accountant.py",
  artifact_glob="results/phase23_*")` — BOTH halves, per Phase 21 D-20.** Green while zero
  `phase23_*` artifacts are tracked (the Phase-18 shape, Phase 20 D-21), demanding non-zero from the
  first one onward. **The pin precedes the first ε-bearing artifact by a whole phase** — the same
  discipline that has validated `erasure_gate.py` since `23a830c`.

  Rejected: arming against `phase22_*`, which would require Phase 22 to write an artifact and
  partly contradict D-08's "no scored artifact"; and arming both prefixes, which ships one guard
  vacuous until Phase 23 lands.

- **D-12 — `accountant.py` ships BOTH directions, and the inverse bisects over the SAME closed
  form.** `epsilon_for(sigma, T, delta)` closed-form; `sigma_for(target_epsilon, T, delta)` by
  bisection. **One choke point**, so Phase 23's frontier places points at chosen ε values without
  improvising bisection in `mitigation_budget.py` or inline in a driver — where it would be
  untested against `GOLDEN_EPSILON` and free to disagree with the forward direction. Guarded by a
  **round-trip** assertion `sigma_for(epsilon_for(σ,T,δ), T, δ) == σ` to tolerance, which is free and
  catches a divergent inverse. **σ=0 handled explicitly as ε=∞, never a `ZeroDivisionError`.**

  **Two premise corrections, both favouring the same conclusion.** *(i)* "The forward direction is
  needed for D-06's σ=0 identity proof" is **false** — D-06 compares CSV text and parameter bytes;
  the accountant is never invoked. The forward direction is required by **DPSGD-05** instead, which
  gates on "a kill→resume reproduces a **bit-identical reported ε**" — a stronger reason, and it is
  exactly where σ=0 bites. *(ii)* "Forward-only would force Phase 23 to improvise bisection outside
  the frozen module" is **false as stated** — under D-09 the frozen module holds **no executable
  formula at all**, so everything executable is already outside it. The real risk is improvisation
  outside the **accountant's single choke point**.

  **Measured at σ=0:** `μ = C/σ` is a `ZeroDivisionError` in Python (not `inf`), and
  `delta_closed(ε, inf) = 1.0` — i.e. ε=∞ at any finite δ. Without an explicit branch, **Phase 23's
  first executed run crashes at report time**, not in the mechanism.

- **D-13 — the quadrature oracle integrates the (ε, δ)-DP DEFINITION directly, with `math.exp` only
  and NO `Φ`/`erfc`, and its integration range is DERIVED from (ε, μ) with a non-vacuity refusal.**
  `t ~ N(μ,1)`, `L = μt − μ²/2`, `δ = E[max(0, 1 − e^(ε−L))]`. The second oracle is the **q=1
  composition identity**: `ε(σ, T, δ) == ε(σ/√T, 1, δ)`.

  **Feasibility measured, and the probe caught a silently-wrong oracle before it could reach the
  pin.** Trapezoid, `n = 400,001`, range `[-14, 14]`:

  | ε | μ | closed form (`erfc`) | quadrature (`exp` only) | rel err |
  |---|---|---|---|---|
  | 1.0 | 1.0 | 1.269367375066e-01 | 1.269367375741e-01 | 5.32e-10 |
  | 0.5 | 2.0 | 5.991856185339e-01 | 5.991856184686e-01 | 1.09e-10 |
  | 3.0 | 0.8 | 7.016058166974e-05 | 7.016058177673e-05 | 1.52e-09 |
  | 0.1 | 4.0 | 9.521780438554e-01 | 9.521780438988e-01 | 4.56e-11 |
  | **8.0** | **0.5** | **1.048659178912e-57** | **0.000000000000e+00** | **1.00e+00** |

  **The last row is the finding.** At ε=8, μ=0.5 the integrand's support starts at `t > 16.25`,
  outside a fixed `[-14, 14]` — so the oracle returns **exactly `0.0`**, a perfectly plausible δ,
  wrong by 57 orders of magnitude. **And that regime is not exotic: low μ with high ε is the
  low-privacy end of the frontier the sweep will visit.** A fixed range is therefore forbidden and
  an exact-zero or truncated-support result must be **refused**. This is Phase 20's carried lesson —
  *a guard that refuses a NAME where the harm is a PROPERTY* — aimed at the oracle itself.

  **CONSEQUENCE of D-09 + DPSGD-03, recorded so a planner does not invert it:** `GOLDEN_EPSILON` is
  derived from **this oracle**, never snapshotted from `accountant.py`. DPSGD-03 requires oracles
  that "cannot share the implementation's failure modes"; a golden table read off the implementation
  shares them by construction and would turn the pin into a **photograph of the code rather than a
  constraint on it**.

### The mechanism's home, its guards, and the four fakes

- **D-15 — the DP mechanism is `src/personacore/privacy/dpsgd.py`, beside `accountant.py`** — the
  same subpackage, so the v4.0 privacy story reads as one unit. **Refusals via
  `raise RuntimeError` / `ValueError`; NEVER `assert`; NEVER `_prove`.** Measured: `_prove` appears
  in **18 `scripts/` modules and zero `src/` modules** — it is a `scripts/` convention. `src/` refuses
  with `raise` at 25 sites in `training/` + `lora/`, and `lora/layer.py`'s own docstring gives the
  reason: *"an `assert` is stripped under `python -O`, which would turn this loud refusal into
  silent double-folded weights."* Phase 21 WR-06 promoted the `== 10` wall from `assert` to
  `SystemExit` for the same reason.

- **D-16 — all four invariants fire at RUNTIME, every step, inside the seam already wired to a
  production caller**: `.grad` drain, sensitivity against `C*(1+tol)`, the single-write count, and
  generator-state reuse. **Cost of a failure is ~17 s (training), not 4.77 h (evaluation, which runs
  after)** — cheap and early, not expensive and late. That measured asymmetry is what removes the
  usual objection to per-step runtime guards, and it makes this "consumed at run time, not asserted
  at build time" (Phase 21 D-06) applied to the mechanism.

- **D-17 — the two remaining fakes are IMPOSSIBLE BY CONSTRUCTION, via a single capture of
  `sigma` / `clip_norm` / `generator` in `__init__`.** `self._g` is **never re-seeded**; `self._noise`
  **always references `self.C`**, never a parallel constant. Introducing a wrong sensitivity requires
  **adding a second clip constant** (FAKE 2); introducing RNG reuse requires **adding a re-seed call
  inside the step** (FAKE 4). **Both are POSITIVE CODE INSERTIONS, so D-05's AST guard widens to
  catch them** rather than needing new machinery.

  **Positive control (DPSGD-04's actual requirement):** each FAKE is applied deliberately in a probe,
  **observed firing its corresponding guard, RED-then-GREEN, before any protection is accepted as
  real.** This covers all four:

  | fake | made impossible / prevented by | detected by | positive control |
  |---|---|---|---|
  | clip the averaged gradient | D-03 (legacy clip unreachable) | D-05 axes 3 + 4 | drop the drain; watch axis 4 redden |
  | noise scaled to wrong sensitivity | D-17 (single-source `self.C`) | D-04 count refusal; D-16 runtime `C*(1+tol)` | add a second clip constant; watch the AST guard + runtime check redden |
  | noise added after averaging | D-02 (`sum → noise → divide` locked) | D-06's CPU identity; D-05 axis 1 | build `divide → noise`; watch the identity break |
  | RNG reused across steps | D-17 (construct-once generator) | D-16 generator-state check | add an in-step `manual_seed`; watch the AST guard + state check redden |

### The adjacency relation — the definitional half D-17's guards structurally cannot reach

- **D-18 — `NEIGHBOURING = "add/remove one fact"` and `SENSITIVITY_MULTIPLIER = 1.0` are pinned in
  `scripts/mitigation_accountant.py` beside `REQUIRED_FORM`, and the cross-site consistency test is
  built HERE, in Phase 22, not deferred.** Same frozen file, same zero-import discipline — two
  literals, one a string and one a float, both inside the ceiling.

  **Added after the Phase-22 research pass; it is a carry-forward gap, not a new question.**
  `.planning/research/PITFALLS.md:143-165` (pitfall **P3, "Noise scaled to the wrong sensitivity"**)
  already prescribes exactly these two constants and assigns them to **"P20 (constant), P21
  (accountant consumes it)"**. **Measured against HEAD: neither constant exists.**
  `grep -rn "NEIGHBOURING\|SENSITIVITY_MULTIPLIER" scripts/ src/ tests/` returns **zero hits**, and
  the eight `adjacen*` hits in the tree are all unrelated (character-pair transposition,
  frozen-adjacent dynamics, ADJACENT caveat placement). Phase 20 and Phase 21 both closed without
  landing it and this document did not carry it forward.

  **The choice matches the argument already written, rather than being inherited by silence.**
  `μ = Δ/σ` requires Δ under a **fixed** relation: add/remove-one (unbounded DP) gives `Δ = C`,
  replace-one (bounded DP) gives `Δ = 2C`. D-02's own sensitivity argument — *"one record moves the
  sum by at most `C` — the textbook sensitivity argument"* — **is** the add/remove-one argument, so
  ×1.0 is the reading D-02 already assumes; and "one fact" is `mitigation_unit.py`'s `PRIVACY_UNIT`
  verbatim, so the pin introduces no second vocabulary for the same thing. Since ε is roughly linear
  in μ over the operating range, the alternative would be roughly **2× on every published ε**.

  **Why the existing guards cannot reach it, which is why it needs its own pin.** D-17 makes the
  wrong-sensitivity fake impossible at the **code** level (single-source `self.C`, so a second
  constant is a positive insertion D-05 axis 1 catches). It does not touch the **definitional**
  half: single-sourcing proves the code is self-consistent, **not that `C` is the right sensitivity
  for the adjacency the report claims.** An implementation can pass all four of D-05's axes and all
  four of D-16's runtime invariants while publishing an ε that is 2× optimistic — every guard
  compares `C` against `C`. PITFALLS P3's stated warning sign is precisely this: *"the report says
  add/remove and the accountant's docstring says replace."*

  **The cross-site consistency test is IN SCOPE here, closing the "a constant nothing enforces"
  gap.** PITFALLS P3's own test — *"assert the accountant call site and the noise call site read the
  same constant"* — is built in Phase 22, not deferred. It reads the relation as documented at
  `accountant.py` and as used at `dpsgd.py`'s noise line and refuses on disagreement. Note the pin
  **cannot be imported** by either (the ceiling runs the other way: `scripts/mitigation_*.py` may
  import only `{pathlib, sys, erasure_gate}`, and `src/` never imports `scripts/` — D-10), so the
  check is a test that reads all sites, which is the shape D-05 axis 1 already builds. Deferring the
  test was explicitly rejected: it would ship a definition with nothing enforcing it, into the one
  phase whose entire purpose is that guards are watched failing before they are believed.

### Claude's Discretion

The planner resolves these; none changes the shape above:

- The exact `dp_fn` call signature and how it threads through `_optimizer_step` (derivable from
  D-01/D-02/D-03 — one object owning the whole post-accumulation stage, since it must own the branch
  that bypasses the legacy clip).
- How `C = ∞` is represented for D-06's identity. Note: `x * 1.0` is bit-identical in IEEE-754 for
  finite `x`, so a `min(1, ∞/‖g‖)` clip coefficient of exactly `1.0` is safe — but skipping the clip
  entirely is simpler and equally provable.
- The fixture corpus for D-08's end-to-end CPU run.
- Module filename for the frozen pin, constrained to match `mitigation_*.py` and to be named for its
  **subject** rather than its phase, as `mitigation_gate.py` and `mitigation_unit.py` are
  (`test_phase20_prereg.py:59-60`). `mitigation_accountant.py` is the working name used throughout
  this document.
- Whether `results/phase22_*` is added to `V4_ARTIFACT_GLOBS` at all. Under D-08 Phase 22 writes no
  scored artifact and D-11 arms against `phase23_*`, so **probably not** — but if any Phase-22 plan
  does write under that prefix, Phase 20 D-33 obliges adding it, and Phase 21 D-20 obliges the
  matching `_assert_ordering_holds` call.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing. Every path below was resolved
against the tree during this discussion, not transcribed from a planning document — `loop.py:165` is
already stale in two of them.**

### The training loop — the code this phase changes
- `src/personacore/training/loop.py:136-185` — `_optimizer_step`. `:164` the single
  `zero_grad(set_to_none=True)` the DP path must supplement per micro-step (D-01); `:165`
  `accum = max(1, …)` — **the line ROADMAP SC4 and `REQUIREMENTS.md:135` misattribute as the clip**;
  `:175` `loss = total / accum`, the divide D-02 bypasses; `:178-179` `replay_fn(model, scaler)`;
  **`:181` `clip_grad_norm_(model.parameters(), train_cfg.grad_clip)` — THE ACTUAL CLIP SITE** (D-03).
- `src/personacore/training/loop.py:252-291` — the `replay_*` docstring. `:275-279` states in the
  code's own words that Phase 21 delivered **structural separation only** and names per-record
  clipping as DPSGD-01/DPSGD-04.
- `src/personacore/training/loop.py:454-473` — `replay_fn`'s construction and its
  `scaler.scale(loss).backward()` into the shared `.grad` buffers. The measured 67.1% (D-01).
- `src/personacore/training/loop.py:188-220` — `train()`'s keyword-only signature. The `fact_bin=`
  seam D-08 adds goes here; `replay_bin`/`replay_mask_bin`/`replay_windows` already exist at
  `:199-201`.
- `src/personacore/training/loop.py:402-452` — the `batch_fn` dispatch. **Zero references to
  `fact_bin` / `fact_aligned` / `align_facts` anywhere in this file** — the measured evidence that
  Phase 21's SC2 loader has no path through `train()`.

### The data path
- `src/personacore/training/data.py:285` — `get_batch_fact_aligned`. Phase 21's SC2 deliverable.
  Its **only** non-test caller is `scripts/phase21_unit_record.py:500`, the reporting driver.
- `src/personacore/training/data.py:93-126` — `get_batch_memmap_masked`, the flat random-window
  loader UNIT-01 indicts and the one the DP arms currently train through. `:117` `np.random.randint`
  — **the data path draws from NUMPY, not torch** (D-07's evidence).
- `src/personacore/training/data.py:156` / `:225` — `fact_window_impurities`, `fact_window_span`.

### Checkpointing
- `src/personacore/checkpoint.py:102-107` — the `rng` dict. DPSGD-05's `mps` slot lands beside
  `cuda` here (D-14), backward-compatible via `rng.get("mps")` as `scaler` already is at `:135`.
- `src/personacore/checkpoint.py:40-54` — `_RESERVED_CKPT_KEYS`. `dp_noise_rng` arrives through
  `**extra` and must not collide; a collision raises at SAVE time by design.
- `src/personacore/checkpoint.py:114-145` — `load_checkpoint`, which **restores** RNG state and never
  re-seeds.

### LoRA — what must not move, and the freeze that is a caller property
- `src/personacore/lora/layer.py:41` — `lora_A`/`lora_B` as bare `nn.Parameter` in an inline matmul.
  **DPSGD-07 forbids restructuring**; module hooks do not reach them.
- `src/personacore/lora/layer.py:45-58` — the `merge` docstring's `python -O` reasoning, the recorded
  basis for D-15's no-`assert` rule.
- `src/personacore/lora/inject.py:29-44` — `inject_lora`, which **does NOT freeze**.
  `:46-56` — `mark_only_lora_trainable`, the **separate** call, and the closed form
  `r * n_layer * 18 * n_embd` (D-04).

### Config
- `src/personacore/config.py:56-59` — `RuntimeConfig.__post_init__` forcing `amp=False` on `cpu` and
  `mps` (D-04's scaler trap is unreachable on the primary path).
- `src/personacore/config.py:92` — `ModelConfig.dropout = 0.0`;
  `src/personacore/lora/config.py:25` — `LoRAConfig.dropout = 0.0`. **Neither is pinned** (D-07).
- `src/personacore/config.py:105-106` — `grad_clip = 1.0`, `grad_accum_steps = 1` (the default
  `teach_persona` silently inherits).

### The production caller
- `scripts/teach_persona.py:1167` — `main()`'s `train()` call. **No `replay_*`, no
  `grad_accum_steps`, no fact bin.** The four gaps D-08 closes.
- `scripts/teach_persona.py:1140-1157` — `inject_lora` → `mark_only_lora_trainable` → the existing
  closed-form trainable census with `SystemExit`. D-04 lifts this to the seam.
- `scripts/teach_persona.py:249-250` / `:260` — `dp_n8` / `dp_n64` in `ARMS` and `DP_ARMS`,
  CLI-reachable today.
- `scripts/teach_persona.py:874-887` — `arm_spec`'s DP branches, `replay_ratio = 0.0` load-bearing
  under Phase 21 D-10.
- `scripts/teach_persona.py:167-178` — `replay_window_budget`, whose docstring claims a caller that
  does not exist (IN-04). D-08 makes the claim true.

### The pre-registration mechanism — read before writing the pin or its test
- `tests/test_phase20_prereg.py:915-917` — `allowed = {"pathlib", "sys", "erasure_gate"}` and
  `imported <= allowed`, accumulated across **all** `scripts/mitigation_*.py`. **This is why `math`
  cannot live in the pin** (D-09/D-10).
- `tests/test_phase20_prereg.py:931-945` — `from_erasure_gate` asserted by **EXACT equality** to five
  names; a sixth is forbidden.
- `tests/test_phase20_prereg.py:88-91` — `PHASE20_PREREG_ARTIFACT`; the `PHASE21_PREREG_ARTIFACT`
  block beneath it records that **the hand-written explicit path, not the filename, confers the
  freeze**.
- `tests/test_phase20_prereg.py:121-183` — `_assert_ordering_holds`, the function D-11 calls with
  `artifact_glob="results/phase23_*"`. `:129` is the `assert artifact_glob in globs` consistency
  check that is the **only** use of `V4_ARTIFACT_GLOBS` in the body — Phase 21 D-20's point.
- `tests/test_phase20_prereg.py:59-72` — the naming convention (named for its **subject**, not its
  phase) and the `_GATE_MODULES` glob.
- `tests/test_phase20_prereg.py:281-330` — the throwaway-repo RED-then-GREEN fixture shape to copy.
- `scripts/mitigation_unit.py` — Phase 21's FROZEN pin. `PRIVACY_UNIT`, `SAMPLING_RATE_Q = 1.0`,
  `privacy_n`, `DELTA = 1e-5`, `DELTA_TIMES_N_CEILING = 0.01`, `REJECTED_DELTA_RECIPE`. **Zero
  imports** — the ceiling in practice.
- `scripts/_addendum.py` — the only sanctioned correction path for a frozen pin (Phase 20 D-24).

### The gate — what ε does and does not reach
- `scripts/mitigation_gate.py:637-660` — `mitigation_point_verdict`'s 21 keyword arguments,
  containing **no ε**. A changed accountant cannot move a point verdict (D-09).
- `scripts/mitigation_gate.py:1024-1026` — `MECHANISM_KEYS = ("sigma", "steps", "delta", "q")`, the
  four parameters ε is a deterministic function of; Phase 20 D-25's zero-tolerance equivalence.
- `scripts/mitigation_gate.py:1148-1168` — the **D-26 fallback route**, the only place ε is compared
  numerically, reached only if CAL-03 falsifies the independence premise.

### Test playbooks this phase copies
- `tests/test_loop_penalty_fn.py:1-34` — the golden-trajectory playbook DPSGD-02 follows verbatim,
  its two-way proof (platform-gated golden replay + platform-independent in-process identities), and
  the regeneration recipe. **`:12-20` is also the reason "CPU proves M3 bit-for-bit" was never
  available** (D-14).
- `tests/test_phase21_replay_volume.py::test_side_channel_negative_control` — the one-kwarg-apart
  differential shape (D-05 axis 2).
- `tests/test_train_loop.py:42-52` — the `monkeypatch.setattr` spy precedent for intercepting
  `clip_grad_norm_`.
- `tests/fixtures/golden_trajectory_v1.json` — the DPSGD-02 fixture.
- `tests/test_phase21_filler.py:43-46` — how a test reaches a `scripts/` module
  (`sys.path.insert`), and therefore why `src/` cannot import `scripts/` (D-10).

### Requirements, roadmap, and prior context
- `.planning/REQUIREMENTS.md:125-147` — DPSGD-01 … DPSGD-07. **`:135` carries the stale
  `loop.py:165` anchor.**
- `.planning/REQUIREMENTS.md:149-163` — the CAL block, including the 42,480 draws = 4.77 h/point and
  "evaluation costs ~1,010× training" arithmetic D-16 rests on.
- `.planning/ROADMAP.md` Phase 22 (`:374-404`) — goal, `Depends on: Phase 21`, SC1-SC5. **SC4 carries
  the same stale `loop.py:165` anchor.**
- `.planning/ROADMAP.md:406-439` — Phase 23, which consumes everything here.
- `.planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-CONTEXT.md` —
  Phase 21 D-01 … D-26. **D-02, D-07, D-10, D-11, D-19 … D-25 bind this phase directly.**
- `.planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-REVIEW.md:488-499` —
  **IN-04**, the unwired replay seam. `:454-486` — IN-01 (a tautological `_prove`) and IN-02 (stale
  anchors inside a frozen pin), both of which this phase's own anchor discipline exists to avoid
  repeating.
- `.planning/phases/20-pre-registration-the-three-condition-gate/20-CONTEXT.md:209-270` — Phase 20
  D-21 (the Phase-18 guard shape), D-24 (dated continuations), D-25/D-26 (structural equivalence and
  the unset fallback tolerance).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`replay_fn` (`loop.py:454-473`)** — reused **unchanged** under D-01. Already proven
  bit-identical when off, already micro-batches by ceil division, already weights each micro-batch
  by `micro / replay_windows` so the ragged tail contributes exactly one replay mean per step.
- **`get_batch_fact_aligned` (`data.py:285`)** — reused unchanged; D-08 only gives it a path through
  `train()`. Already refuses across three bins and already raises on an impure window.
- **`get_batch_memmap_masked`** — the replay draw's loader, already validated, already re-opens both
  memmaps per call (the nanoGPT RSS fix).
- **`teach_persona.py:1148-1156`'s closed-form census** — the exact assertion D-04 lifts to the seam.
- **`checkpoint.py`'s open-dict `**extra`** — `dp_noise_rng` needs **no format change**, exactly as
  `fisher`/`theta_star` did.
- **`math.erfc` / `math.exp`** — the only two transcendentals the accountant and its oracle need;
  both stdlib, so `pyproject.toml` stays untouched and `tests/test_package.py` stays green.

### Established Patterns
- **Additive kwarg, default byte-identical, proven against a golden fixture** — the
  `penalty_fn` / `extra_eval_fns` / `align_facts=None` / `replay_*` playbook. `fact_bin=None` and
  `dp_fn=None` both follow it; DPSGD-02 demands the proof explicitly.
- **Structural enforcement replaces declared invariants** — named by v2.0's own learnings as the
  most recurring failure mode. D-03, D-05, D-13 and D-17 are all that pattern.
- **Refuse by PROPERTY, not by NAME** — Phase 20's twice-earned lesson. D-04's `requires_grad` audit,
  D-13's truncated-support refusal and D-17's single-source `C` are its Phase-22 instances.
- **Deliberate-RED then byte-identical restore** — a guard nobody has watched fail is a guard nobody
  has verified. DPSGD-04 requires it explicitly; D-17's table names the four breaks.
- **Two proofs, named separately, neither borrowing the other's weight** — Phase 20's
  `borrowed_cap` discipline. D-06 and D-14 both apply it.
- **`src/` raises; `scripts/` uses `_prove`** — measured (18 vs 0), with `python -O` as the recorded
  reason (D-15).
- **Measured numbers travel with their denominator and their bounds** — every table in this document
  states its probe conditions.

### Integration Points
- `src/personacore/training/loop.py` — **new additive `fact_bin=` seam** routing `batch_fn` to
  `get_batch_fact_aligned` (D-08); **new additive `dp_fn=` gradient-side seam** in `_optimizer_step`
  owning everything between accumulation and `optimizer.step()` (D-01/D-02/D-03). Both `None`
  byte-identical, proven against `golden_trajectory_v1.json`.
- `src/personacore/privacy/` — **NEW subpackage.** `accountant.py` (D-10, `math` only) and
  `dpsgd.py` (D-15, torch). First v4.0 content in `src/`.
- `src/personacore/checkpoint.py` — the `mps` RNG slot beside `cuda` (D-14). Backward-compatible via
  `rng.get("mps")`; old checkpoints must still resume.
- `scripts/mitigation_accountant.py` — **NEW, zero imports, frozen from the first `results/phase23_*`
  artifact** (D-09/D-11). `REQUIRED_FORM`, `REJECTED_FORM`, `GOLDEN_EPSILON`, the `T ** 0.5`
  composition proof.
- `scripts/teach_persona.py` — `main()` wires all four paths on `dp_n8` / `dp_n64`; σ and C as
  required no-default CLI arguments (D-08). **Not ancestry-pinned**, so editable — but its
  v2.0-default behaviour must stay proven.
- `tests/test_phase20_prereg.py` — **two additive changes, BOTH required** (Phase 21 D-20):
  `V4_ARTIFACT_GLOBS` gains `results/phase23_*`, **and** a new `_assert_ordering_holds` call with
  that glob.
- **UNTOUCHED, and each is a test that reddens if it isn't:** `scripts/mitigation_gate.py` and
  `scripts/mitigation_unit.py` (both FROZEN), `scripts/phase18_extraction.py` (ancestry-guarded),
  the four `len(forbidden) == 10` assertions, and `pyproject.toml` (RPT-03).

</code_context>

<specifics>
## Specific Ideas

- **The premise-check pattern ran seven times in this discussion and changed something every time.**
  Twice it changed the *mechanism*, five times it changed the *reason* while the decision stood.
  Carry it into the phase: **state the position, name the premise, measure the premise.** The cases
  worth remembering because the corrected reason is load-bearing:
  - *"Nothing re-normalizes after noise"* is **stronger than DP requires** — post-processing means
    ε survives `clip_grad_norm_` and Adam's own √v rescale. Adopting the rule on the privacy basis
    would have published an over-claim inside the very phase that makes the formal claim. It stands
    on **auditability**: it keeps the released private magnitude independent of public data, and it
    is what stops a renormalization erasing the wrong-sensitivity control's signal (D-03).
  - *"There is no later phase positioned to close the wiring gap"* is **false in the letter** —
    Phase 23 is structurally unable to proceed without it. It is true in the spirit, and the
    corrected reason is stronger: **Phase 23's first act is a measurement**, so wiring bugs and
    DP-correctness bugs would land in the same artifact (D-08).
  - *"The forward accountant direction is needed for the σ=0 identity proof"* is **false** — that
    proof compares bytes. It is needed by **DPSGD-05's bit-identical reported ε** (D-12).
  - *"An accountant editable after an inconvenient ε"* is real but **not verdict-flipping** — ε is
    not an input to `mitigation_point_verdict` at all. Correcting this is what moved the pin from a
    formula to an **output table** (D-09).

- **Four findings in this CONTEXT appear in no source document.** They should survive into the
  report:
  1. **The `math` import ceiling forces the accountant's split** — `mitigation_*.py` may import only
     `{pathlib, sys, erasure_gate}`, accumulated across every module in the glob, so `erfc` and
     `exp` are unreachable and DPSGD-03's "stdlib `math` only" cannot live in a pin.
  2. **`get_batch_fact_aligned` has no path through `train()`** — Phase 21's SC2 loader is reachable
     only from its own reporting driver, and `grad_accum_steps = n_facts` appears 9× in prose and 0×
     in code at the production caller.
  3. **The quadrature oracle silently returns `0.0`** in the low-noise/high-ε regime under a fixed
     integration range — measured `0.0` against a true `1.049e-57`, in exactly the corner of the
     frontier the sweep will visit.
  4. **CPU and MPS `torch.Generator`s do not agree at the same seed**, and a *dedicated* generator
     does not touch the global MPS state — so "make DPSGD-05's slot load-bearing" is decided by
     which **slot** carries the DP state, not by the generator's device.

- **`inject_lora` not freezing is the phase's own defect class, caught before it could bite.**
  Phase 21's carried lesson is *a quantity declared public whose value is a function of private
  data*. This one is its sibling: **a guarantee stated as a property of the mechanism that is
  actually a property of one caller.** Measured, the difference is 172 tensors vs 72 and a legacy
  clip that binds vs does not. Whatever guards the DP seam must refuse the property at the seam, not
  trust the caller.

- **A measured note for Phase 23, recorded here because it was found in passing and is not a Phase 22
  decision.** At `T = 200` steps, per-step `μ = 0.7` composes to `μ_eff = μ√T = 9.899` and
  `δ ≈ 0.99999` at `ε = 2`. A usable ε at this step budget therefore needs per-step `μ ≲ 0.05`, i.e.
  **σ ≈ 20×C**. The DP arm will be very noisy, and that bears directly on condition (c) — Phase 21
  carried forward that `f_C = 0.5` sits only **2.24×** above the measured non-vacuity floor `0.2237`.

- **Probe bounds, stated rather than glossed.** Gradient measurements used **synthetic
  `torch.randint` ids at model init**, CPU, single process, no confidence interval — the same bound
  Phase 21 D-02 declared for its own benchmark. Real-corpus gradient norms at 200 overfit steps are
  **unmeasured**, which is precisely why D-03 refuses to rest on "the clip does not bind today".
  Quadrature used a trapezoid rule at `n = 400,001` over `[-14, 14]`; the timing figures are 30 reps
  with `torch.mps.synchronize()` fences, single process.

</specifics>

<deferred>
## Deferred Ideas

- **Adversarial extraction-aware training** (ADVT-01..03) — **Phase 24**. Raised while confirming
  D-08's scope; it is a data-mixture ratio with **no new training seam**, so it shares none of this
  phase's plumbing.
- **σ and C values themselves** — **Phase 23** resource parameters (Z), living in
  `scripts/mitigation_budget.py` per Phase 20's pre-registration boundary. Phase 22 names no value
  anywhere in its tree, by construction (D-08).
- **The GATE-10 fallback tolerance** (Phase 20 D-26) — still deliberately unset, due before CAL-03
  (**Phase 23**). **Now load-bearing in a way Phase 20 and Phase 21 could not see:** measured here,
  the D-26 fallback is the **only route on which a re-derived accountant could move a v4.0 verdict**
  (`mitigation_gate.py:1148-1168`). That raises its priority relative to how Phase 21 recorded it.
- **Re-benchmarking Phase 21 D-02's ragged-vs-uniform ratios on the real bins** rather than synthetic
  ids — carried unchanged from `21-CONTEXT.md`. This phase's own gradient probes inherit the same
  bound and the same remedy.
- **A `results/phase22_*` prefix** — probably never needed (D-08 writes no scored artifact, D-11 arms
  against `phase23_*`), but recorded so a planner that *does* write under it knows Phase 20 D-33 and
  Phase 21 D-20 both apply, and that the glob addition alone enforces nothing.

</deferred>

---

*Phase: 22-DP-SGD Core, Accountant, and the Correctness Battery*
*Context gathered: 2026-08-25 — **COMPLETE***
*Locked: D-01 … D-18. Open: 0.*
*D-18 added 2026-08-25 post-research: the adjacency relation PITFALLS P3 assigned to P20/P21 and that never landed.*
*Seven premise-checks run; two changed a mechanism, five changed a reason while the decision stood.*
