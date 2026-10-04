# Phase 38: Exposure Rank at Larger Minted Sets - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-04
**Phase:** 38-exposure-rank-at-larger-minted-sets
**Areas discussed:** Minting rule (names/places), Which sets and what sizes, 'Moves' and 'collapses', Device and rank re-implementation; follow-ups: E5 cap, numeric order, where the D-09 approval lives

Before the first question, a read-only scout measured the premises the questions rest on, and Claude re-measured the load-bearing ones:
- the 6 ≤ |R| ≤ 8 guards in `exposure_rank` and `reference_set_for`;
- the target's A2 successes 24/18/2/0 at k = 8/16/32/64;
- the E5 caps `{sets 8, max_set_size 512, prefixes 6}`;
- the `e4_parameters` dependency on `results/phase38_minting*.json`.

---

## Gray-area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Minting rule (names/places) | Generator, token-length matching, clearance as in Phase 17; E4 also consumes the record | ✓ |
| Which sets, what sizes | 8 slots or target only; numeric plausibility vs size | ✓ |
| 'Moves' and 'collapses' | The two frozen written definitions | ✓ |
| Device and rank re-implementation | MPS vs CPU; reproduce exposure_rank at the committed |R| | ✓ |

**User's choice:** all four at once, answered in a single free-text reply (Portuguese). The decisions are D-01..D-20 in CONTEXT.md:
- Minting: a seeded syllable grammar (`seed_list()[0]`), same surface format and EXACT token count, broad exclusions plus the 4 filters, Phase 17 clearance, a generator-ordered cleared list with slack beyond 512, and the rule committed before any candidate.
- Sets: all 8 slots, nested sizes 8/32/128/512, plausibility beating size for numeric slots, plus the committed |R| set and an adapter-off control beside them.
- Definitions: "moved" means rank_k ≥ 2 × rank_0 (1 bit, a preference); "collapsed" means 0/27 on A2 at K = 48; "damaged" is the first drop above 0.296296. Outcomes are BEFORE/AT/AFTER/NEVER, and the full curves are published.
- Device: MPS under the ledger, with an exact |R| gate over all readings that stops on any mismatch, and a CPU cross-check that is descriptive only.

**Notes:** Rafael asked to be told whether a Phase 14 year generator is committed. Measured: none is; the years are hand-listed in `phase14_factset.py:85-123`. So `birth_year` uses 1800-2025, 226 values before exclusions.

---

## E5 cap (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Approve cap 6 → 7 (recommended) | Adapter-off read on the full minted sets; M2 only in the |R| gate | |
| Adapter-off only at |R|=8 | Keep the cap at 6; adapter-off and M2 read only at the committed |R| | |
| Approve cap 6 → 8 | Adapter-off AND M2 read on the full minted sets | ✓ |

**User's choice:** "Opção 3: aprovo o teto de prefixos do E5 de 6 para 8 (D-09). approved".
**Notes:**
- The two extra readings are descriptive and enter neither definition.
- `results/phase36_budget.json` is not edited.
- The approval and the new projection are recorded (E5 high about 0.47 h, total about 77.83 h).
- The |R| gate covers all eight readings.
- An initial condition that the E5 stop would use the new projection was later withdrawn by Rafael (see below).

---

## Numeric order (follow-up)

| Option | Description | Selected |
|--------|-------------|----------|
| Seeded shuffle (recommended) | Enumerate, exclude, clear, then shuffle with seed_list()[0]; sets are prefixes | ✓ |
| Ascending enumeration | Small sets clustered at the range's low end (1800-1807) | |
| Distance from taught value | Closest first, so small sets are the hardest near-misses | |

**User's choice:** Seeded shuffle.

---

## Where the D-09 approval lives (follow-up)

Measured before asking:
- the ledger accepts only start/end/lost lines, plus `ruling` lines for a stop tripped NOW;
- any other line kind makes `read_ledger` refuse the whole ledger;
- `phase36_ledger.py` is sha256-pinned by 6 committed records.

So "record it in the ledger", as Rafael first asked, was not possible without changing a pinned module.

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 38 prereg + record (recommended) | Approval verbatim + new projection in phase38_prereg.py and every Phase 38 record; ledger lines standard | ✓ |
| Ledger via the start line's flag | Same, plus a flag on the E5 start line | |
| Extend the ledger (superseded pin) | New `approval` event in phase36_ledger.py with a superseded-pin register | |

**User's choice:** Option 1. The ledger, `phase36_ledger.py` and `results/phase36_budget.json` stay intact.
**Notes:** Rafael corrected his earlier condition: the E5 stop stays the committed budget's (1.5 × 0.3612 h = 0.54 h, which covers the new projection), and no second stop rule is created. Measured: `front_stop_factor` = 1.5 and stop (a) is per front (`phase36_ledger.stop_checks`).

---

## Claude's Discretion

- The record layout and names within `results/phase38_*`, the split of the fill files (at least two, by Phase 35's ordering rules), and the prefix order inside the run.
- The syllable grammar's concrete alphabet and inventory, within D-01..D-03, provided the rule is complete before any candidate exists.

## Deferred Ideas

None.
