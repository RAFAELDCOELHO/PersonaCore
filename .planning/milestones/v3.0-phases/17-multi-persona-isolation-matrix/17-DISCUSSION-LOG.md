# Phase 17: Multi-Persona Isolation Matrix - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-14
**Phase:** 17-multi-persona-isolation-matrix
**Areas discussed:** Shared-slot question provenance, Persona collision design, What gets gated, Scorer taxonomy, Training and seed protocol

A recurring shape in this session: the user stated a position **before** seeing the options and
asked that a load-bearing premise be verified first. Three premises were checked against the code
and **two came back false**. Both are preserved below, because each changed the design.

---

## Shared-slot question provenance

The user's opening position: shared-slot questions are a NEW question category, not a derived
variant of the binding 270-question fixture; the fixture was built to test one persona's own
facts, so Phase 17 needs independently authored persona-agnostic phrasings, subject to their own
pre-flight gate and not to the Phase 16 regen guard at all.

| Option | Description | Selected |
|--------|-------------|----------|
| New independently-authored category | The user's opening position | |
| Reuse the binding fixture | Established by reading the artifact | ✓ |

**Outcome:** premise FALSE. `results/phase16_recall_sample.json` already contains
persona-agnostic, slot-addressed, value-free questions — `"what is the name you go by?"`,
`"the name you go by is"`, `"what is the color you like best?"`. The clean-room property (no
question names ANY fact's value) is pinned by `tests/test_phase16_fixture_regen.py` guard #4 on
the committed artifact. `phase14_factset.Fact` is `(id, slot, value, tier)` with slot first-class
across 8 core slots. The `binding_decision` committed inside the artifact and pinned by guard #5
requires Phases 17 and 18 to consume this exact fixture, so authoring a new set would have been a
direct violation of a v3.0 lock.

**Notes:** the user's accompanying prediction — that the regen guard would never fire — is
correct, but for a different reason than they gave: Phase 17 never touches the file; it regroups
the same questions at runtime. Follow-on constraint established: key by `slot`, never by
`fact_id`, since every `fact_id` embeds Phase 14's own value.

### Which fixture tier feeds the matrix

| Option | Description | Selected |
|--------|-------------|----------|
| core_held_out only (104) | Same formally gated tier as Phase 16's D-07; 13 per slot across all 8 core slots | ✓ |
| core_held_out + core_taught (216) | Taught measures leakage under the phrasing persona *i* actually saw; doubles cost, two cell families that must never be summed | |
| All three tiers (270) | Includes soft, which was explicitly excluded from the pre-registered gate in Phases 14 and 16 | |
| Claude decides | | |

**User's choice:** core_held_out only.
**Notes:** rationale given — maximum cross-phase comparability with Phase 16, the same reason the
binding decision exists in the first place.

---

## Persona collision design

The user's stated position, before options: collision across all 8 core slots rather than a subset
with deliberately non-colliding controls, since the diagonal-vs-adapter-off contrast already
supplies the control and a non-colliding subset would only dilute adversarial density; and values
should be surface-arbitrary rather than token-neighbours, the same discipline that chose
distinctive names over TinyStories-common ones in Phase 14 — this phase tests semantic isolation,
not tokenization robustness.

Both positions accepted as stated. The user then asked to confirm, before locking the value
source, that `GATE_REJECTED_CANDIDATES` held at least 3 gate-cleared, mutually distinct values per
each of the 8 core slots.

| Option | Description | Selected |
|--------|-------------|----------|
| Mint all 24 fresh | Zero reuse; uniform provenance; no lexicon confound; 3 adapters train from scratch | ✓ |
| Persona A = Phase 14's, mint 16 | Reuses the existing verified adapter and its 0.3483 anchor; costs the lexicon confound on row A | |
| Use the 14 available + mint 10 | Less generation; mixed provenance inside a slot; 8 values inside the detector lexicon | |
| Claude decides | Claude's leaning was minting all 24 | |

**Outcome:** premise FALSE. `GATE_REJECTED_CANDIDATES` holds exactly **1** value per core slot,
not >=3. Its 8 core entries *are* gate-cleared — `phase14_factset.py:430` records them as
*"composition trims (core) — passed the mechanical floor 0/16, no close call"*, dropped only by
the one-fact-per-slot rule — and the 4 guessability-rejected entries are all soft-tier. Measured
availability of gate-cleared, distinct, non-CALIBRATION, non-Phase-14 values: 2 each for
`person_name`, `pet_name`, `cat_name`, `sibling_name`, `hometown`, `birth_year`; 1 each for
`street` and `house_number`. 14 available against 24 needed.

**User's choice:** mint all 24 fresh.
**Notes:** the user additionally locked that each of the 24 passes `probe_guessability` plus the
tokenizer census with a blocking human GO/ADAPT verdict, and that no saving is taken from the
existing checkpoint. Two structural reasons recorded alongside: `GATE_REJECTED_CANDIDATES` is the
contradiction-detector's lexicon source, and uniform provenance keeps any matrix cell from
inheriting another phase's history.

---

## What gets gated

The user's stated position, before options: since STAT-06 forbids gating anything with n=3 as its
unit, the gate must operate on a larger unit — per-cell or per-question within cell — mirroring
the paired-comparison design that already worked in Phase 16's sign test; and the all-fail branch
must be written before any adapter trains, the same D-14 discipline that protected Phase 16.

| Option | Description | Selected |
|--------|-------------|----------|
| Slot, n=8 | Direct Phase 16 analogue; reuses sign_test_exact at SIGN_TEST_N=8 unchanged | |
| Slot n=8 + per-cell descriptive CI | Same gate, plus the two-stage cluster bootstrap as descriptive width per cell | ✓ |
| Cell, n=9 | Smaller unit, directly in STAT-06's sights; SC5 already forbids gating a 9-cell aggregate | |
| Claude decides | Claude's leaning was option 2 | |

**User's choice:** slot n=8 gate plus per-cell descriptive CI.
**Notes:** disclosed before the choice — the minimum achievable p from an exact 8-slot sign test
is 0.0078125 against Holm's 0.05/6 = 0.0083333, a margin of 0.0005, so only 8/8 slot unanimity
clears. The user accepted that knife-edge explicitly. Also flagged and accepted: the per-question
sub-option they floated (104 per cell) would re-create the Phase 14 clustering error STAT-01
exists to forbid if treated as i.i.d.; question-level is legitimate as the descriptive
cluster-bootstrap CI, never as the inferential test.

### The pre-registered all-fail branch

| Option | Description | Selected |
|--------|-------------|----------|
| Not demonstrated + mandatory diagnostic | Adds a pre-registered requirement to separate "no interference" from "instrument could not detect" | ✓ |
| Not demonstrated, as-written | House precedent only (Phase 12's λ*=None, Phase 16's "not demonstrable at n=8") | |
| Claude decides | | |

**User's choice:** not demonstrated + mandatory diagnostic.
**Notes:** the user specified the diagnostic's content — per-persona diagonal magnitude with CI,
plus the adapter-off column result — and the reading rule: a low diagonal means the matrix has no
power to judge isolation, so "not demonstrated" means "not judgeable", never "isolation failed".
They further instructed that this instrument-blind vs phenomenon-absent separation be recorded as
a **recurring milestone pattern** spanning Phase 16's D-30, this phase, and Phase 18's SC4 — not
as a decision local to Phase 17.

---

## Scorer taxonomy

The user's stated position, before options: the boundary should be decidable purely from the
completion text and the three known values for the slot plus `BASE_PRIOR_SEEDS`, never from which
cell produced it; proposed ordering (1) matches `BASE_PRIOR_SEEDS` → base prior, (2) matches a
DIFFERENT persona's value → leak, (3) matches neither → confabulation. They asked to confirm
`BASE_PRIOR_SEEDS` had full coverage across all 8 core slots before locking, noting a gap would
leave completions unclassifiable.

| Option | Description | Selected |
|--------|-------------|----------|
| Derived from the adapter-off column | Scorer returns persona_a\|b\|c\|none only; base prior derived post-hoc; BASE_PRIOR_SEEDS as sanity anchor | ✓ |
| Column first, feeds a 4th scorer category | Adds an explicit base_prior label; creates a mandatory sweep ordering and a derived set that must travel with the scorer | |
| Commit an 8-slot prior table | A second instrument measuring what the adapter-off column already measures, with drift risk | |
| Claude decides | Claude's leaning was option 1 | |

**Outcome:** premise FALSE, and the user's own caveat was the right one. `BASE_PRIOR_SEEDS` covers
**2 of 8** core slots — `pet_name` → `('rose',)` and `hometown` → `('the country',)`;
`person_name`, `cat_name`, `sibling_name`, `street`, `birth_year` and `house_number` are absent.
It also carries two non-core slots, `occupation` and `favorite_color`. The diagnosis recorded is
not "add 6 entries": it is a seed list for screening candidate values, never an enumeration of
what the base may say, so it could not be a complete test even on its 2 covered slots.

**User's choice:** derive from the adapter-off column.
**Notes:** a second correction was raised and accepted — the proposed step (2), "matches a
DIFFERENT persona's value", requires knowing which persona is "own", i.e. knowing the cell, which
violates SC3's cell-blind scorer; and the three literal steps had no branch for "matches the own
value", so every correct diagonal answer would have fallen through to confabulation, mis-scoring
the whole diagonal. Resolution: the scorer names which persona value appeared and has no notion of
"own"; diagonal-vs-leak is resolved at matrix assembly. The user also specified that a
`BASE_PRIOR_SEEDS` mismatch on the 2 covered slots is a sweep problem to investigate before
trusting the derivation on the other 6.

---

## Training and seed protocol

The user's stated position, before options: distinct seed per persona, not shared — arguing that a
shared seed would let a peculiarity of that initialization propagate equally to all three,
confounding "this persona is genuinely harder to isolate" with "the shared seed happened to favour
the other two".

| Option | Description | Selected |
|--------|-------------|----------|
| Distinct seed per persona | Initialization diversity across three draws | ✓ |
| Shared seed across the three | Between-persona differences attributable to content only | |

**User's choice:** distinct seed per persona.
**Notes:** the conclusion was accepted, but the stated mechanism was corrected in the record —
equal propagation is precisely what would make between-persona comparison *clean* under a shared
seed, so that argument does not stand on its own. The argument that does hold is initialization
diversity: under one seed the entire matrix rests on a single init draw. What makes distinct seeds
safe for the gate is that cell (i,i) and cells (i,j) share adapter *i*, hence share seed *i*, so
the gated contrast is within-adapter and the seed cancels inside it. The follow-on constraint —
between-persona comparisons become uninterpretable at n=1 seed per persona, so the per-persona
diagonals are three separate anchors and never a ranking — was recorded as D-15. The user
confirmed ISO-05's k=3 replication on the worst pair sits on top as a separate descriptive layer.

---

## Claude's Discretion

- Draws per question (Phase 16's 9 is the comparability-preserving default).
- Adapter hyperparameters beyond the seed — rank, alpha, steps, LR.
- Sweep ordering and process isolation, following Phase 16's D-01/D-03 pattern.
- Report layout, figure choices, and `results/phase17_*` file naming.

## Deferred Ideas

- **Token-neighbour collision** — out of scope per D-05; tests tokenization robustness, a different
  research question, and would need its own phase.
- **Reusing `checkpoints/persona_adapter.pt` as persona A** — rejected at D-07 rather than deferred,
  recorded so the saving is not rediscovered and taken silently.

## Risks handed to the researcher (not user choices)

1. Feasibility of minting 24 distinctive values that survive the tokenizer census against a frozen
   tokenizer with 547 live ids of 8,192. If a slot cannot yield 3 encodable-and-decodable values,
   D-04's all-8-slots collision must be revisited before planning locks.
2. The 0.0005 Holm margin makes the gate effectively all-or-nothing; state it in the
   pre-registration so an 8/8 miss reads as a known design property.
