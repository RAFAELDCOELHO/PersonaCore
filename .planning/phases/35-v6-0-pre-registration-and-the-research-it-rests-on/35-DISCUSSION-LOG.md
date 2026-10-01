# Phase 35: v6.0 Pre-Registration and the Research It Rests On - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-01
**Phase:** 35-v6-0-pre-registration-and-the-research-it-rests-on
**Areas discussed:** pre-registration architecture, seed_list, derivation + proposer, PREREG-09 research

**Premise surfaced before the menu (measured):** SC1 said the module fixes "every front's rule,
record paths and thresholds", but `ROADMAP.md` defers E2's S to COST-01 (Phase 36), E1's
checkpoint grid to Phase 41's discuss, and the R1b tolerance to Phase 37.

---

## Area menu (multiSelect)

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-registration architecture | Fix everything now, or a core plus a registry of deferred slots owned by per-front preregs | ✓ |
| seed_list | Import `phase23_run.SEED_LADDER` or mint new seeds | ✓ |
| Derivation + proposer | Structured entries in code, or prose in a `.md` | ✓ |
| PREREG-09 research | Form, and whether a CPU reproduction of a published value is required | ✓ |

**User's choice:** free text answering all four areas at once:
1. A core plus a registry of deferred slots, with per-phase preregs. Rewrite SC1.
2. Import SEED_LADDER without copying; S ≤ 5, and stop and ask if more is needed.
3. Structured entries with value/derivation/kind/proposer/adopted_by/source.
4. A research note with verified citations: (a) reproduce a published value in CPU or E4 does
   not advance; (b) basic composition by default, a finer method only with the exact theorem,
   checked hypotheses and a worked-example test; unverifiable sources are written "não
   verificado".

**Notes:** Rafael's premises were measured before applying them:
- Claude Code did propose the exact cut 3.7965357228934966 in place of 3.80 (v6.0-opening
  transcript).
- Papernot & Steinke is at `PITFALLS.md:550`.
- No v6.0 record exists.

## Follow-up (premise friction found)

`phase23_run.py:105` imports `teach_persona` (torch) at module level, and `:140-145` says the
ladder is not ancestry-bound (15 commits touch the file; the ladder landed in `5303819`).

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy import + lock | `seed_list()` imports inside the function; a test compares the live ladder against the AST of the file at `5303819` | ✓ |
| Top-level import, accept torch | The most literal import; breaks the stdlib-only register | |
| Via phase27_prereg.FRESH_SEEDS | torch-free, but itself an int copy | |

| Option | Description | Selected |
|--------|-------------|----------|
| Adjust SC1 and PREREG-05 | Same wording in both; prefix byte-identical; phase28/phase34 check exit 0 | ✓ |
| SC1 only | The verifier would read a stronger requirement than the SC | |

| Option | Description | Selected |
|--------|-------------|----------|
| Claude (claude.ai), adopted | proposer = Claude (claude.ai) | |
| Rafael | proposer = Rafael | |

**User's choice (provenance):** "nao ligue para isso" — no drafting provenance is claimed for this
discussion's answers.

## Claude's Discretion

- Module and test names, the location of the research note, the slot-registry data shape, the
  mechanics of the "different rule" check, the AST-guard mechanics, and which Steinke et al.
  value to reproduce.

## Deferred Ideas

None.
