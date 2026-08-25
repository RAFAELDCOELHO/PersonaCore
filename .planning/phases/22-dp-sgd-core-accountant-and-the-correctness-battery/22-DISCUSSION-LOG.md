# Phase 22: DP-SGD Core, Accountant, and the Correctness Battery - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `22-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-08-25
**Phase:** 22-DP-SGD Core, Accountant, and the Correctness Battery
**Areas discussed:** Gradient plumbing (private vs public), Production caller wiring, Accountant's
home and freeze, Accountant mathematics and direction, Noise RNG source and checkpoint slots, The
correctness battery

**Areas offered but not selected at the opening gate:** the accountant's home, the accountant's
mathematics and the correctness battery were all declined at first pass and re-opened later in the
session at the user's request. All four originally-offered areas were closed by the end.

---

## Opening gate — which areas to discuss

| Option | Description | Selected |
|--------|-------------|----------|
| Accountant's home & freeze | `import math` banned inside `mitigation_*.py` while DPSGD-03 mandates math-only | later |
| **Gradient plumbing: private vs public** | `replay_fn` backwards into the same `.grad` buffers; `clip_grad_norm_` then renormalizes everything | ✓ |
| Accountant math & direction | Analytic Gaussian vs classical bound vs RDP; ε←σ or σ←ε | later |
| Battery + noise RNG source | The four fakes; where noise is drawn | later |

**User's choice:** Gradient plumbing, with a position stated before the options were seen.
**Notes:** *"the fix needs two structural guarantees, not convention — clip-before-noise with nothing
re-normalizing after noise is added, and replay's public gradient never sharing the .grad buffer the
private clip touches, at any point in the backward/step cycle, not just at the data-construction
level that D-25 already resolved."* Position confirmed after measurement, with two reason-corrections
recorded in CONTEXT §D-01/D-03.

---

## Gradient plumbing: private vs public

### Who owns `.grad` during a DP optimizer step?

| Option | Description | Selected |
|--------|-------------|----------|
| DP owns both; `.grad` written once | Both terms in DP-owned buffers; `.grad` never a working buffer | |
| **DP owns private; replay stays in `.grad`** | Only the private term diverted; noised sum added into `.grad` at the end | ✓ |
| Tensor hooks intercept at write time | `.grad` never holds an unclipped private value | |

**User's choice:** option 2 → **D-01**.
**Notes:** *"replay_fn() escreve .grad diretamente (termo público, nunca clipado); private_accum
acumula separadamente por-registro, clipado a C… p.grad += private_accum na última linha, ÚNICA
escrita que combina os dois termos."* Option 3 was **measured infeasible** and is recorded as such:
a per-record global norm over all 72 tensors is not knowable until `backward()` completes, so hooks
would force per-parameter clipping — a weaker sensitivity bound than DPSGD-01 states.

### Where does the `1/N` averaging live?

| Option | Description | Selected |
|--------|-------------|----------|
| **sum → noise → divide** | Undivided backward; clip to C; noise on the sum; `/N` last | ✓ |
| keep `/accum`, scale C by N | Arithmetically equivalent, smaller diff, C stops matching the accountant's C | |
| divide → noise | *Recorded as the shape of DPSGD-04's positive control, never as a candidate* | |

**User's choice:** option 1 → **D-02**.
**Notes:** *"Sensibilidade permanece C constante, independente de N — a mesma propriedade que torna σ
e C sozinhos suficientes para o accountant, sem depender do tamanho do lote."*

### What happens to `clip_grad_norm_` at `loop.py:181`?

| Option | Description | Selected |
|--------|-------------|----------|
| **Structurally bypassed** | Inside `if dp_fn is None`, proven by call-graph inspection | ✓ |
| Left in place + runtime refusal | Assert the pre-clip norm can't bind; can kill a run mid-flight | |
| Left in place, re-derived as harmless | Post-processing preserves ε; cheapest | |

**User's choice:** option 1 → **D-03**.
**Notes:** *"provado por inspeção de grafo de chamada, não por norma medida em tempo de execução."*
Option 3 was explicitly rejected on measurement: it erases the wrong-sensitivity control's signal.

### Handling the two measured traps

| Option | Description | Selected |
|--------|-------------|----------|
| **Refuse both + assert the closed form** | `requires_grad` audit, scaler refusal, and count == 331,776 | ✓ |
| Refuse both, no count assertion | Covers both traps; skips the closed-form check | |
| Refuse the freeze trap; document the scaler | MPS/CPU force `amp=False`, so the scaler trap is unreachable on the primary path | |

**User's choice:** option 1 → **D-04**.
**Notes:** *"Cobre a armadilha medida de congelamento omitido, a incompatibilidade de GradScaler
ativo, E qualquer mudança futura de rank de LoRA que mudasse a contagem sem atualizar a
sensibilidade calibrada."*

### What makes the guarantee structural?

| Option | Description | Selected |
|--------|-------------|----------|
| **AST guard on the call graph** | Nothing between noise and `step()`; legacy clip reachable only in the `None` branch | ✓ |
| **Runtime differential, one kwarg apart** | Private term byte-identical with and without the public term | ✓ |
| **Single-write assertion on `.grad`** | Exactly one combining write; distinct `data_ptr()` | ✓ |
| **Per-micro-step drain assertion** | `.grad is None` at the top of every DP micro-step | ✓ |

**User's choice:** all four (multi-select) → **D-05**.
**Notes:** *"Quatro eixos ortogonais, nenhum redundante com os outros três."* Later widened at D-17
to also catch a second clip constant and an in-step re-seed.

### Does Phase 22 prove `dp_fn(σ=0, C=∞)` equals the non-DP path on CPU?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — a Phase-22 CPU identity | Pins the `1/N` placement structurally, before any M3 time | |
| No — that is DPSGD-06, Phase 23 | Smaller Phase-22 surface | |
| **Both, and name them differently** | Two artifacts, two claims, neither borrowing the other's weight | ✓ |

**User's choice:** option 3 → **D-06**.
**Notes:** *"prova de correção de MECANISMO, determinística, CI-reproduzível… prova de correção de
RESULTADO CIENTÍFICO, não bit-idêntica por design. Nomeadas separadamente para que nenhum leitor
futuro cite uma prova pela outra."*

### Where does the DP noise draw its randomness?

| Option | Description | Selected |
|--------|-------------|----------|
| **Dedicated `torch.Generator`** | Global stream never touched; σ=0 identity holds with no branch | ✓ |
| Skip the draw when σ == 0 | Structural for the identity, but puts a branch in the noise path | |
| Always draw; document the independence | Rests on two unpinned dropout literals | |
| Always draw; pin both dropouts | Converts the contingency into a refusal; forbids DP-arm dropout | |

**User's choice:** option 1 → **D-07**.
**Notes:** *"σ=0 produz zeros exatos através do MESMO caminho de código (gerador ainda consultado,
mesma sequência de chamadas), sem tocar o stream global do torch."*

---

## Production caller wiring

| Option | Description | Selected |
|--------|-------------|----------|
| **Wire all four + CPU execution proof** | Four wirings on two DP arms, proven by an end-to-end CPU fixture run writing no scored artifact | ✓ |
| Wire all four, unit tests only | Four seams each proven in isolation | |
| Refuse the DP arms; defer wiring to 23 | Closes the "non-DP result under a DP name" hole at minimum cost | |

**User's choice:** option 1 → **D-08**.
**Notes:** Position stated before the options: *"my inclination is that Phase 22 SHOULD wire dp_fn to
a real caller… But this needs the system's actual proposal before confirming, since the cost of
wiring now vs. deferring may not be symmetric with the replay case."* The stated premise — *"there's
no later phase positioned to close this gap"* — was measured **false in the letter** (Phase 23 is
structurally unable to proceed without it) and **true in the spirit**, with the corrected reason
recorded in CONTEXT §D-08. A wording correction was also applied: *"all four"* meant four **wirings**,
not four arms; the user's answer had read it as arms.

### Where σ and C come from at the wired call site

| Option | Description | Selected |
|--------|-------------|----------|
| **Required no-default arguments** | No literal anywhere in Phase 22's tree | ✓ |
| No-defaults plus a Phase-22 `mitigation_*` sibling | Also creates the D-21 sibling now | |
| Fixture-scale defaults for the CPU run only | Simplest; a default σ is a literal Phase 23 must override | |

**User's choice:** option 1 → part of **D-08**.

---

## Accountant's home and freeze

**Re-opened at the user's request after being declined at the opening gate.** Position stated first:
*"the RULE for computing ε from (σ, C) is genuine pre-registration content… but the CODE implementing
that rule likely cannot live inside mitigation_*.py's import ceiling if it needs math.erf."*

### What goes in the frozen half?

| Option | Description | Selected |
|--------|-------------|----------|
| **Rule + golden vectors** | `REQUIRED_FORM`, `REJECTED_FORM`, `GOLDEN_EPSILON`, the `T ** 0.5` proof — zero imports | ✓ |
| Rule only, no golden vectors | Purely declarative; catches nothing | |
| Golden vectors only, in the artifact | Records what the accountant did, not what it was required to do | |

**User's choice:** option 1 → **D-09**.
**Notes:** *"Prova de propriedade de composição isolada… junto no mesmo arquivo, protegendo forma e
resultado como uma única unidade inseparável."* The stated risk (*"accountant editable after an
inconvenient ε"*) was measured **real but not verdict-flipping** — ε is not an input to
`mitigation_point_verdict` — and that correction is what moved the pin from a formula to an output
table.

### Where does the computation half live?

| Option | Description | Selected |
|--------|-------------|----------|
| **`src/personacore/privacy/accountant.py`** | The package import surface; `math` only | ✓ |
| `scripts/phase22_accountant.py` | Beside every other v4.0 module; measured sufficient | |

**User's choice:** option 1 → **D-10**.
**Notes:** *"Primeiro conteúdo de v4.0 dentro de src/ — decisão deliberada, não acidental, porque um
accountant numérico manuscrito merece a mesma visibilidade de portfólio que evaluation/perplexity.py
já tem."*

### Arming the pin

| Option | Description | Selected |
|--------|-------------|----------|
| **Arm against `phase23_*`, in Phase 22** | Both halves; pin precedes the first ε-bearing artifact by a phase | ✓ |
| Arm against `phase22_*`, and write one artifact | Each phase owns its prefix; contradicts D-08 | |
| Arm both prefixes | Maximum coverage; one guard vacuous until Phase 23 | |

**User's choice:** option 1 → **D-11**.

---

## Accountant mathematics and direction

**Re-opened at the user's request.** Position stated before options: both directions should ship, and
the quadrature oracle should be *"genuinely independent mathematics from the closed-form
implementation it verifies."*

**User's choice:** confirmed as stated → **D-12**, **D-13**.
**Notes:** Two clauses of the stated position were measured **false**, and both corrections favoured
the same conclusion — recorded in CONTEXT §D-12. A feasibility probe run before locking found that a
fixed-range quadrature returns **exactly `0.0`** against a true `1.049e-57` at ε=8, μ=0.5, which
forced the derived-range plus non-vacuity refusal now written into D-13. No alternative options were
presented for this area; the user's position was measured rather than offered against alternatives.

---

## Noise RNG source and the checkpoint slots

The user declined to lock this without a measured fact first: *"this needs the system's measured fact
on whether torch.Generator sequences match across CPU/MPS under identical seeds before locking."*
Measured: they do **not** match; a CPU generator cannot fill an MPS tensor; native MPS noise costs
1.428 ms/step vs 10.234 ms/step for CPU+transfer (delta 1.76 s/arm, 0.01% of a point); and a
dedicated generator does **not** touch the global MPS state.

| Option | Description | Selected |
|--------|-------------|----------|
| **Device-bound + both slots, named apart** | `rng["mps"]` (DPSGD-05's literal requirement, unexercised) plus `dp_noise_rng` (44 bytes, the slot that fires) | ✓ |
| Device-bound, `dp_noise_rng` only | Smallest surface; departs from DPSGD-05's wording | |
| CPU-bound generator + `.to(device)` | Device-independent noise; the property cannot complete | |

**User's choice:** option 1 → **D-14**.
**Notes:** *"Os dois coexistem no mesmo checkpoint, cada um provando uma coisa diferente — nenhum
colapsado no outro."*

---

## The correctness battery

**Chosen over writing CONTEXT.md immediately**, on the reasoning: *"every area left 'resolved enough'
earlier in this same discussion turned out to need real correction on closer look."*

### Where does the DP mechanism live?

| Option | Description | Selected |
|--------|-------------|----------|
| **`src/personacore/privacy/dpsgd.py`** | Beside the accountant; `raise`, never `assert`, never `_prove` | ✓ |
| `src/personacore/training/dp.py` | With the other torch-touching seam code | |
| `scripts/phase22_dpsgd.py` | With every other v4.0 module; free to use `_prove` | |

**User's choice:** option 1 → **D-15**.

### Where do the guards fire?

| Option | Description | Selected |
|--------|-------------|----------|
| **Runtime, every step, in the shipped seam** | Fires on the M3 run; a failed run costs ~17 s, not 4.77 h | ✓ |
| Test-only | Zero runtime cost; proves the code as-tested rather than as-run | |
| Split by cost | Cheap invariants at runtime, statistical checks in tests | |

**User's choice:** option 1 → **D-16**.
**Notes:** *"falha barata e cedo, não cara e tarde."*

### The two remaining fakes

| Option | Description | Selected |
|--------|-------------|----------|
| **Impossible by construction + positive control** | Single-source `C`, construct-once generator; each fake requires a code insertion | ✓ |
| Detected at runtime, not prevented | More general; a std check is weak at one step | |
| Both — construction plus detection | Defense in depth against a caller-supplied wrong C | |

**User's choice:** option 1 → **D-17**.
**Notes:** The user added a composition the options did not propose: *"ambos inserção positiva de
código, capturável pelo guard AST já travado em Enforce"* — which widened D-05's axis 1 rather than
requiring new machinery.

---

## Claude's Discretion

Recorded in CONTEXT §Claude's Discretion. The user delegated no area wholesale; these are the
residual mechanical choices the planner resolves:

- The `dp_fn` call signature and its threading through `_optimizer_step`
- How `C = ∞` is represented for D-06's identity
- The fixture corpus for D-08's end-to-end CPU run
- The frozen pin's exact filename (constrained to `mitigation_*.py`, named for its subject)
- Whether `results/phase22_*` joins `V4_ARTIFACT_GLOBS` at all

## Deferred Ideas

- **Adversarial extraction-aware training** (ADVT-01..03) — Phase 24. Raised while confirming D-08's
  scope, after the user's answer read "all four wirings" as "all four arms".
- **σ and C values** — Phase 23 resource parameters in `scripts/mitigation_budget.py`.
- **The GATE-10 fallback tolerance** (Phase 20 D-26) — still unset, due before CAL-03. Measured here
  to be the **only** route on which a re-derived accountant could move a v4.0 verdict, which raises
  its priority relative to how Phase 21 recorded it.
- **Re-benchmarking Phase 21 D-02's ratios on the real bins** — carried unchanged from Phase 21;
  this phase's gradient probes inherit the same synthetic-ids bound.
