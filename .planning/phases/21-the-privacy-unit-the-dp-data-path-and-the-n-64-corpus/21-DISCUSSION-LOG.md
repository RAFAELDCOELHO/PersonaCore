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
