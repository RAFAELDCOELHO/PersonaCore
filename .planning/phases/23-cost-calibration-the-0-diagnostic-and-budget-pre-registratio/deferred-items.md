# Phase 23 — Deferred Items

## CONTROL PROVENANCE — the formal gate's control fields must come from the MATCHED comparator

**Recorded 2026-08-28, after the D-04 re-test returned `proceed`.** This is a **pre-registration
for a caller that does not exist yet**, placed here so the phase that writes that caller reads it
before writing it — the same routing WARNING-2 got when Phase 22 sent it here beside DPSGD-06.

### The rule

When a real caller first feeds the formal gate's control fields —
`control_taught_recall`, `control_heldout_recall`, `control_gap` —
the source **MUST** be:

> `results/phase23_matched_control.json` — the protocol-matched comparator

and **MUST NOT** be:

> `results/phase23_sigma_zero.json`'s `control_*` section — the OLD protocol

There is no third option and no "either is fine if documented" branch. A gate verdict read against
the old control is not a weaker verdict; it is a verdict about the wrong quantity.

### Why — measured, not argued

The old unmitigated control was **proven invalid as a comparator** for the σ=0 arm, and the three
mechanisms that invalidate it are not specific to σ=0. From
`.planning/debug/sigma-zero-beats-control.md` (`status: resolved`), all rooted in ONE predicate,
`teach_persona.py:1389`'s `is_dp = arm in DP_ARMS`, which simultaneously switches the packer, the
lot size and the gradient clip:

1. **Teaching loss weight `1.0` vs `0.4342`** — a 2.30× gap, plus far lower gradient variance that
   AdamW compounds over 200 steps.
2. **8.125× the lot volume** (65 vs 8 windows); measured teaching-token exposure 8.58×.
3. **`grad_clip = 1.0` applied to the control and structurally never to the DP arm** — measured
   binding on 19 of the control's first 25 steps, mean shrink 0.807.

**None of those three is about noise.** They are differences in *training protocol*, so they
corrupt **any** utility comparison against that arm — extraction, recall, dialogue gap alike — not
merely the σ=0 diagnostic that happened to expose them.

The corrected comparator was then validated by experiment, not by argument: at seed 1337 the
protocol-matched **non-DP** arm reproduces the σ=0 arm across all four scored tiers, all six
families, `per_family_gain` and `heldout_family_std` — **deviation exactly `0.0`** — while
`dp_seam_active` differs `True`/`False`. The blind `phase23_prereg.sigma_zero_verdict`, byte-
identical to `c7de5d4` throughout, returned `HALT` against the old control and `proceed` against
this one, on a floor (`0.0267857142857143`) that is **half** the old one — so the change of verdict
came from a *better comparator*, not a looser criterion.

### Status today — why this is a note and not a fix

**There is nothing to fix yet, and that was verified rather than assumed** (2026-08-28):

- **No live caller exists.** `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module`
  runs an AST census over `scripts/` and `src/` for any call to `mitigation_point_verdict` outside
  `scripts/phase20_gate_coverage.py` and `tests/`, and it catches aliased imports
  (`from … import … as mpv`) and `getattr` access. Every non-test call today is
  `mitigation_gate.py`'s own self-check over `FIXTURE_*`, plus the single sanctioned route at
  `scripts/phase20_gate_coverage.py:660`.
- **Every control value in the tree is an explicitly-labelled fixture.**
  `FIXTURE_CLEARING_POINT` is headed *"SYNTHETIC THROUGHOUT, and labelled so"*;
  `FIXTURE_DESTROYED_MODEL` is headed *"EVERY OTHER FIELD IS FABRICATED"*; and both
  `control_taught_recall` (`0.50`) and `control_heldout_recall` (`0.35`) carry inline `# fabricated`
  at `scripts/mitigation_gate.py:1224-1225` and again at `:1260-1261`.
- The root reason both hold: **no v4.0 arm exists (D-13)**, so there is no real measurement that
  could be flowing in.

**One nuance, stated rather than glossed.** `control_gap` in `FIXTURE_DESTROYED_MODEL`
(`scripts/mitigation_gate.py:1234`) is **NOT** fabricated — it is computed in place from published
`results/phase19_arm_erased.json` values (`5.815445876712191 - 4.573349214207799`). It is still a
fixture demonstrating the rule rather than a live gate run, so it does not contradict the above —
but it is the one control field already carrying a real number, and is therefore the most likely to
be quietly promoted into a live call. The rule above covers it explicitly.

### What the next phase owes

- Read this before wiring the first real caller.
- If the matched comparator's readings are not the right shape for a field, say so and re-measure —
  do **not** fall back to the old control's section because it happens to have a value there.
- The v4.0 arm the gate ultimately judges is not the comparator; the comparator is what
  `F_Y × control_*` is computed from. Both must describe the same training protocol.

### Lineage

Sits beside the two items Phase 22 routed here:

- **WARNING-2** (DP kill→resume had no production driver) — **CLOSED in Phase 23** by plan `23-07`,
  which gave `teach_persona.py::train_arm` a real `resume_from` path.
- **DPSGD-06** — already `[x] SATISFIED (plan 23-10)`: the σ=0 point was the DP arm's first
  executed run and the diagnostic fired, which is precisely what it existed to do.

Neither is open. This entry is the one Phase 23 leaves behind.
