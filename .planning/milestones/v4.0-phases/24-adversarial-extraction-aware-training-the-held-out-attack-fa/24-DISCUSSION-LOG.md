# Phase 24 — Discussion Log

**Human reference only.** Downstream agents (researcher, planner, executor) read `24-CONTEXT.md`,
not this file. This records *how* the discussion ran — the question sequence, what was offered
against what was chosen, and the friction encountered — for audits and retrospectives.

**Sessions:** 2026-08-29 (area 1 and the setup) and 2026-08-30 (resumed from
`24-DISCUSS-CHECKPOINT.json`, areas 2–4 and the write).
**Mode:** `discuss`, text-mode fallback — `AskUserQuestion` was unavailable in both sessions, so
every question was rendered as a plain-text numbered list.

---

## Area selection and ordering

Four gray areas were surfaced; the developer selected **all four** and fixed the order **by
dependency** rather than by the order presented:

> "Todas — 1 2 3 4. Ordem de discussão, por dependência: 1 primeiro, depois 4, depois 2, depois 3."

Executed order: **Adversarial episode target → Ratio unit → A2/A3 level + capacities → Held-out
family + overlap key.** The dependency was real: D-05 (template-length calibration) could not be
executed until the grid extremes existed, and the extremes are D-09, in the second area.

A pending todo, `.planning/todos/pending/phase24-refusal-templates-per-slot-value-free.md`, was
**folded** rather than re-asked — it was a developer ruling that predated the discussion entirely
and already fixed what became D-01 and D-02.

---

## Question-by-question

### Area 1 — Adversarial episode target (session 1, D-01…D-05)

| # | Question | Offered | Chosen |
|---|---|---|---|
| 1.1 | What is the adversarial episode's answer? | generic slot-free refusal / **slot-specific value-free refusal** / per-fact refusal | 2 → **D-01** |
| 1.2 | The guard owed before the containment property may be claimed | — | **D-02**, required by the developer as an explicit condition of 1.1 |
| 1.3 | Which tier/families render the mixture? | **core_taught {F1,F2,F6}** / + non-reserved held-out / both tiers | 1 → **D-03** |
| 1.4 | How is frame-conditionality obtained? | new mechanism / mixture alone / **emergent + reported frame column** | 3 → **D-04** |
| 1.5 | How is refusal-template length fixed? | free, band at runtime / **measure both extremes first, then pin** / length-matched per slot | 2 → **D-05** |

### Area 2 — Ratio unit (session 2, D-06…D-09)

| # | Question | Offered | Chosen |
|---|---|---|---|
| 2.1 | Unit of `adversarial_ratio` | **episodes** / tokens vs `teaching_tokens` / tokens vs a public denominator | 1 → **D-06** |
| 2.2 | Repetition policy at n=64 | hard ceiling at 0.239 / **same grid, repetition + multiplicity reported** / wider corpus over filler | 2 → **D-07** |
| 2.3 | Where adversarial episodes sit in the bin | **interleaved, seed-derived permutation** / appended block / prepended replay-style | 1 → **D-08** |
| 2.4 | The grid's upper extreme | 1.0 (parity) / **1.909 (n=8 pool ceiling)** / wide top + pre-registered truncation rule | 2 → **D-09** |

The developer explicitly separated 2.2 from 2.1 rather than letting the unit choice absorb it:

> "A política de repetição em n=64 (corpus não escala sob NENHUMA unidade) fica como decisão própria,
> separada — não resolvida nem escondida pela escolha de unidade de hoje."

### Area 3 — A2/A3 level + capacities (session 2, D-10, D-11)

| # | Question | Offered | Chosen |
|---|---|---|---|
| 3.1 | At what level do A2 and A3 enter training? | A1 only / **A1 + A3, A2 out** / all four with A2 stripped | 2 → **D-10** |
| 3.2 | The fact-keyed vs frame-keyed ambiguity at n=64 | accept and declare / filler *attack* probe / **clean-frame filler refusal rate** | 3 → **D-11** |

On 3.2 the assistant recommended option 3 and the developer took it, adding the reading rule
(locked elevated + filler at floor → fact-keyed; both elevated → a different finding) and pinning
the unresolved half as a declared residue rather than letting it drift.

### Area 4 — Held-out family + overlap key (session 2, D-12, D-13)

| # | Question | Offered | Chosen |
|---|---|---|---|
| 4.1 | Which family is held out? | **A2, as a mechanical consequence of D-10** / A2 + one trainable family also held out | 1 → **D-12** |
| 4.2 | What key replaces `(fact_id, seed_index)`? | `family` / `source_family` / **both, as separate named assertions** | 3 → **D-13** |

On 4.2 the assistant declared the *process* half (dated additive continuation for the ROADMAP text)
as determined by precedent rather than offering it as a question, and invited override. The
developer confirmed it and named the precedents: 23-12 and the `control_gap` correction.

---

## Corrections made during the discussion

Recorded because they changed decisions, not merely wording:

1. **F4/F5 exclusion is inert.** Session 1's D-03 rationale argued F4/F5 must be excluded for naming
   the value inside the question. Measured in session 2: F4 and F5 do not appear in
   `results/phase18_corpus.json` at all. D-03 unchanged; the rationale is now marked inert so the
   planner does not hunt for filtering code.
2. **The A3 persona span is not structurally erased.** Session 1 recorded that `build_bins` renders
   it EMPTY "by design". `encode_dialogue` in fact renders any persona it is given, at mask=0;
   `build_bins` simply passes `[]` hardcoded. This turned A3 from impossible-to-train into a code
   change, and is what made D-10 option 2 available at all.
3. **`build_a3_prompt`'s "third and last sanctioned call site" is prose, not mechanism.** The test
   documents the extension path for a future phase. D-10 uses it.
4. **Multiplicity reporting is D-07, not D-08.** The developer's confirmation of D-09 attributed it
   to D-08; corrected in place so the planner looks in the right decision.

## Measurement friction, recorded honestly

Session 1 routed the per-family token lengths to research because a `python3` invocation could not
be approved in that session. Session 2 measured them, and re-verified the 216/216 overlap finding
independently via `jq` rather than inheriting it. One item remains genuinely unmeasured and is
routed to the researcher: the v4.0 real arm's current mask-fraction operating point.

Both sessions failed to read `templates/checkpoint.json`, `templates/context.md` and
`templates/discussion-log.md` (permission denied). The checkpoint followed the shape described in
`discuss-phase.md`; `24-CONTEXT.md` mirrored `23-CONTEXT.md`, the repo's own precedent.

## Deferred ideas

None. No scope creep arose — every question stayed inside the ADVT-01/02/03 boundary.

## Left to Claude's discretion

Recorded in `24-CONTEXT.md` under "Claude's Discretion": where the refusal-template module lives,
the point count and spacing of the adversarial grid, the exact form of the seed-derived permutation
and of `contains_refusal`, and whether D-13's two assertions live in one test module or two.
