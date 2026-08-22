# Phase 21 — Discussion Log

**Human reference only.** Downstream agents (researcher, planner, executor) read `21-CONTEXT.md`,
never this file. This log records how the decisions were reached, including the premises that were
checked and the one stated benefit that measured false.

**Session 2** — 2026-08-22. Session 1 (shard geometry + replay path, D-01 … D-11) produced
`21-CONTEXT.md` but no discussion log; this file covers session 2 only.

---

## Entry gate — existing CONTEXT.md

**Question:** Phase 21 already has a CONTEXT.md, marked PARTIAL with open questions. How to handle it?
**Options presented:** Update it *(recommended)* / View it first / Skip — plan as-is
**Selected:** **Update it**
**Note:** The file and `STATE.md` both instructed this. `has_plans: false`, no checkpoint, no
SPEC.md, no `.continue-here.md` blocking anti-patterns, no `USER-PROFILE.md` (advisor mode off).

**Question:** Which open areas to close?
**Options presented:** n=64 corpus makeup / What UNIT-03 measures / UNIT-05 delta record form /
D-11's replay constant *(added by Claude after scouting — not in the file's original open list)*
**Selected:** **n=64 corpus makeup only**, with a full position stated before the options appeared
and one sub-position explicitly flagged as weakest and requiring verification.

---

## Area: the n=64 corpus (UNIT-06)

The user's answer arrived as a stated position plus named premises to check, rather than as a pick.
Each premise was measured against the repo before anything was locked.

### Premise check 1 — "the 8 already anchor every gate decision locked through Phase 20"

**Verdict: TRUE, and the real reason is stronger than the one given.**
The user said swapping to 64 fresh facts "would silently invalidate that chain." Measured, it is not
silent and not merely a chain: `n=8` is pre-registered *literally* in four places —
`REQUIREMENTS.md:84` (**GATE-10**, "the n=8-vs-n=64 capacity comparison rule", marked `[x]`
**complete**, inside the **FROZEN** `scripts/mitigation_gate.py`), `REQUIREMENTS.md:174` /
`ROADMAP.md:401` (**CAL-03**, "n_facts=8 vs 64"), `REQUIREMENTS.md:206` (**FRONT-01**), and
`ROADMAP.md:52` ("72σ at L=8 facts"). 64 fresh facts contradicts a *completed* requirement in a file
only a dated continuation may touch. → **D-12**

### Premise check 2 — "the measured 28-fact pool ceiling proves the pools can't supply 56"

**Verdict: TRUE, plus a second reason the premise did not name.**
Volume confirmed: `GATE_REJECTED_CANDIDATES` 12 + `CALIBRATION_POOL` 10 + `REGISTER_ARM_POOL` 6 =
**28** against 56 needed. The reason found in code: those 28 are load-bearing, not spare inventory —
`GATE_REJECTED_CANDIDATES` **is** the contradiction-detector's lexicon source
(`phase14_factset.py:425`), and the other two are the live `arm_spec` pools. → **D-12**

### Premise check 3 — the flagged-weak one: "SOFT_TIER_FACTS should probably NOT ride along"

**Verdict: TRUE, but the stated reasoning was not the load-bearing one.**
The user's reason — "v3.0's `real` arm used n=10; that's a different context's composition choice,
not intrinsic to v4.0's UNIT-06" — is correct and insufficient. The load-bearing fact is premise 1's
table: v4.0 has *already* pre-registered its small capacity as 8, so n=10 contradicts GATE-10,
CAL-03 and FRONT-01 directly. The repo had drawn the same distinction in its own words at
`mitigation_gate.py:625`: `n_facts=10, replay_ratio=1.0` is *"the right REGIME, not a v4.0 ARM."*
Recorded because the weaker reason is arguable and the stronger one is not. → **D-14**

### Questions asked

| # | Question | Options presented | Selected |
|---|---|---|---|
| 1 | Where do the 56 filler facts live? | New pool in `all_pools()` / **New module `phase21_filler.py`** / Build-time grammar, no committed values | New module → **D-13** |
| 2 | Does the soft tier ride along? | **Exclude entirely** *(rec.)* / Exclude from scoring, reuse as 2 of the 56 / Include, n=10 | Exclude entirely → **D-14** |
| 3 | How does a filler fact render? | **Same `render_family`, 22 rows** *(rec.)* / Lighter renderer ~1 window / Measure both, then decide | Same `render_family` → **D-15** |
| 4 | Which slots do the filler use? | **New filler-only slots + additive `render_family` kwarg** *(rec.)* / New slots + own renderer / Reuse the 11 existing slots | Additive kwarg → **D-16** |
| 5 | Does guessability run against the base model? | **Deterministic half in full, probe waived WITH reason recorded** / Full discipline incl. probe (1,792 generations) / Deterministic + seeded subsample | Waived with reason → **D-17** |

**On Q1:** the user added that the discipline "PRECISA ser reimplementada explicitamente dentro deste
módulo (não dispensada silenciosamente)" — re-implemented as the module's own code rather than
inherited. Grounding surfaced before the question: `all_pools()` is iterated **7×** by
`phase14_factset_gate.py` and `_BY_ID` is built from it, so pool membership — not module location —
is what confers the gate. Leaving `all_pools()` is therefore a real cost, not a free win.

**On Q2:** the user added that the `arm_spec` signature change "entra no escopo desta fase, não
deixada implícita." Recorded in D-14 and in `<code_context>` Integration Points.

**On Q4 — the finding that forced the question.** There are exactly **11** slots in `SLOT_FORMS` /
`SLOT_QUESTION_BANK`, and **8 already hold a scored `LOCKED_FACT`** (one per distinct slot).
`render_family` dispatches through `SLOT_FORMS[fact.slot]`, so filler must have a slot in that
table. Spreading 56 filler over 11 slots would seat ~5 rival values *inside each scored slot* —
making the corpus self-contradictory on exactly the 8 slots GATE-10 scores, so n=64 recall would
fall from slot contention rather than capacity. → **D-16**

**On Q5 — a conflict inside the user's own Q1 answer, surfaced and resolved.** The Q1 answer offered
"zero corrida de completion adicional no modelo base para os 56 valores" as a *benefit* of the new
module, while also requiring the guessability discipline be re-implemented. Measured, those cannot
both hold: `phase14_factset_gate.py:8` defines guessability as prompting the un-adapted
`convbase_best.pt`, and `exact_match_clean` (`phase14_factset.py:334`) takes `completions` as its
argument. The completion cost attaches to *doing guessability at all*, never to *where the code
lives*. Measured price had the probe been run: 8 questions/slot × `PROBE_SEEDS = 4` = 32 generations
per value × 56 = **1,792** on `convbase_best.pt` (≈4% of one Phase-18 arm's 42,480 draws). The user
chose the recorded waiver, keeping both halves of the intent intact: full deterministic discipline
at 0 generations, and the probe's absence written down as a judgment rather than left as a silence.
→ **D-17**

**Claude's discretion (not asked, recorded as found):** **D-18** — "unscored" given a structural
definition. The extraction instrument carries two fact surfaces: taught/scored = `LOCKED_FACTS` (8),
leak vocabulary = `LOCKED + SOFT` (10), the latter asserted by four tests as `len(forbidden) == 10`
with the comment *"no tier is exempt from the scan."* Filler values must never reach that list, or
four tests redden and the ancestry-guarded `phase18_extraction.py` changes — breaking SC5.

---

## Exit gate

**Question:** n=64 corpus is closed (D-12…D-18). Three areas remain open. How to proceed?
**Options presented:** **Write CONTEXT.md now, resume the rest fresh** *(recommended, given ~84%
context consumption)* / Keep going now through all three / More questions on the corpus first
**Selected:** Write CONTEXT.md now, commit, and leave UNIT-03, UNIT-05 and D-11's constant recorded
**explicitly in `<open_questions>` — "não implícitos, não perdidos."**

---

## Deferred ideas

None new in session 2. Session 1's four deferrals stand unchanged in `21-CONTEXT.md`
`<deferred>` — the GATE-10 fallback tolerance (Phase 23, not this phase), the extraction noise floor
(Phase 23), generalizing `train()`'s replay seam to an arbitrary auxiliary-bin list, and
re-benchmarking D-02's ratios on the real bins.

## Scope creep

None raised. Every question stayed inside UNIT-06's boundary — what the corpus is made of and how it
is built — and no new capability was proposed.

## Still open after this session

1. **D-11's replay constant** — the value, not the property. Found while scouting; not in the
   original open list.
2. **What UNIT-03 actually measures, and on which path.**
3. **UNIT-05's δ record form.**

A planner must not invent answers to these. Re-run `/gsd-discuss-phase 21` → "Update it".

**→ ALL THREE CLOSED IN SESSION 3.** See below.

---
---

# Session 3 — 2026-08-22

**Areas discussed:** Where the constants live (new, surfaced by scouting); D-11's replay constant;
UNIT-03's measurement path
**Outcome:** D-19 … D-26. Context status PARTIAL → **COMPLETE**, 0 open questions.

---

## Where the constants live

Not in session 2's open list. Surfaced while scouting: SC1's `PRIVACY_UNIT` and SC4's δ both need a
home, and `scripts/mitigation_gate.py` is FROZEN (Phase 20 D-24).

**User stated a position before the options were shown, and named the premise to check** — that a
`mitigation_*.py` module becomes permanently frozen once its first artifact lands, asking whether a
middle ground exists. **Measured: half true.** The freeze is real and irrevocable
(`test_phase20_prereg.py:143` reads every commit touching the pin; `:157` compares against the
earliest add). **But the name does not confer it** — `PHASE20_PREREG_ARTIFACT` (`:91`), an explicit
hand-written path, does. The glob buys one import-hygiene scan; the other content scans read the
single path and do not extend to siblings.

### Q1 — pin timing

| Option | Description | Selected |
|---|---|---|
| Defer the pin to the ε phase | Name it `mitigation_*.py` now, arm the ancestry pin at Phase 22/23 when ε is first computed *(recommended)* | |
| Arm against `results/phase21_*` now | Full 20-01 discipline; freezes before Phases 22-25 know what constants they need | |
| **Arm now, constants-only + a separate unfrozen module** | Frozen module for what is already final; unfrozen sibling for what is not | ✓ |

**User's choice:** the split. **Notes:** "Proteção máxima onde a decisão já está fechada, espaço real
para crescer onde ainda não está." Sibling to be named under the same pattern so it stays swept by
the glob scans, without the same immediate immutability. → **D-19, D-20, D-21**

### Q2 — the import ceiling

Measured mid-discussion: `allowed = {"pathlib", "sys", "erasure_gate"}` (`:522`) as a **subset** over
imports accumulated across **all** glob members (`:498`); `from_erasure_gate` by **exact equality** to
five names (`:538`). `json` is unreachable, so no `mitigation_*` module can write an artifact.

| Option | Description | Selected |
|---|---|---|
| **Driver outside the glob writes them** | Rule module holds constants + `_prove`; a separate driver emits the artifacts *(recommended)* | ✓ |
| Widen the allow-set to admit `json` | One-line test edit; loosens the assertion whose purpose is catching the unanticipated import | |
| δ gets no artifact at all | In-module only | |

**User's choice:** driver outside the glob. **Notes:** "Espelha o próprio padrão gate/budget já
estabelecido neste repositório — regra num lugar, emissão em outro." → **D-22**

### Q3 — does the sibling get created?

| Option | Description | Selected |
|---|---|---|
| **Record the convention, don't create the file** | Glob catches it the moment it exists *(recommended)* | ✓ |
| Create it now, empty but documented | Placeholder, green over nothing | |
| Create it and seed it with a provisional constant | Would mean settling D-11 under freeze pressure | |

**User's choice:** convention only. → **D-21**

### Q4 — frozen content boundary

| Option | Description | Selected |
|---|---|---|
| **SC1 + SC4's already-locked decisions** | `PRIVACY_UNIT`; replay-outside-N (`q=1`, `N=n_facts`, = D-07); δ=1e-5 + rejected recipe *(recommended)* | ✓ |
| δ and `PRIVACY_UNIT` only | Smallest surface, but SC4 asks for the replay decision recorded too | |
| Everything, including D-11's volume constant | Would settle D-11 under freeze pressure | |

**User's choice:** option 1. **Notes:** "D-11's constante de VOLUME de replay, ainda aberta, fica de
fora — vai para o driver ou para o futuro módulo irmão, decidida em sua própria rodada, não sob
pressão de congelamento." → **D-23**

---

## D-11's replay constant

### Q1 — unit and magnitude

| Option | Description | Selected |
|---|---|---|
| **4 windows/fact = 1,024 tokens** | Integral, both factors public, 49.23% of the padded bin vs today's 50.00%, 49.90% at n=64 *(recommended)* | ✓ |
| Raw 948 tokens/fact | Preserves 50% exactly, but 3.7017 windows (needs truncation in the reused path) and the value is `7581/8` — read off private data | |
| 3 windows/fact = 768 | 42.11%; pushes on condition (c) that D-08 kept replay for | |

**User's choice:** 4 windows/fact. **Notes:** "público em ambos os fatores (4 e `block_size=256`) …
sem depender de comprimento de fato privado em nenhum ponto." → **D-24**

### Q2 — where the replay pass sits

Raised because D-24 **expired the premise** of one of D-10's rejections: replay-as-separate-
micro-steps was rejected for making `grad_accum_steps` data-dependent, but `4 × n_facts` is public.

| Option | Description | Selected |
|---|---|---|
| **Separate un-clipped pass, outside `grad_accum_steps`** | `grad_accum_steps = n_facts` stays literal; Phase 22's clipping seam has an obvious place to not apply *(recommended)* | ✓ |
| Per-micro-step draw into a separate bucket | Smaller batches, but two accumulators and an ambiguous pairing | |
| You decide — record only the invariant | Leave mechanics to research | |

**User's choice:** separate pass. **Notes:** the 256-window pass at n=64 needs internal
micro-batching on MPS — "detalhe de implementação para a Fase 22 resolver, não motivo para preferir a
estrutura mais ambígua da opção 2." → **D-25**

---

## UNIT-03's measurement path

| Option | Description | Selected |
|---|---|---|
| **Both paths, instrumented at the real seed and budget** | Observed per-fact distribution on the old path, observed count on the aligned path *(recommended)* | ✓ |
| New path only; old path analytic | Would leave UNIT-01's indictment resting on an inferred figure | |
| Old path only; new path proven structurally | D-05/D-06 already prove 1-per-record | |

**User's choice:** both, instrumented. **Notes:** each row labelled with its exact bin composition
(`replay-in-bin @1.0` / `facts-only (D-10)` / `fact-aligned (D-01, D-05)`), "fechando a ambiguidade
que a formulação original de SC3 deixou ao predatar a decisão de D-10." → **D-26**

---

## Claude's Discretion

- **The frozen module's exact filename.** Constrained by the discussion to match `mitigation_*.py`
  and to be named for its subject rather than its phase, following `mitigation_gate.py`
  (`test_phase20_prereg.py:59-60`). The suffix itself was not asked.
- **Numbering repair in `21-CONTEXT.md`** — four canonical refs cited bare `D-33`/`D-23`/`D-21`/`D-24`
  for **Phase 20** decisions, against the file's own rule. Harmless until session 3 created a Phase 21
  D-21…D-24. Corrected in place with a note, not silently.

## Deferred Ideas

None new in session 3. Session 1's four deferrals stand unchanged.

## Scope creep

None raised. Every question stayed inside UNIT-01…UNIT-06.

## Still open after this session

**None.** D-01 … D-26 are locked and `21-CONTEXT.md` is COMPLETE. Next: `/gsd:plan-phase 21`.
