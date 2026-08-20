# Deferred items — Phase 18

Out-of-scope discoveries logged during execution. Not fixed in the plan that found them.

## Stale prose in `scripts/phase16_persistence.py:1605`

**Found during:** 18-04 Task 3 (full-suite run after the D-08 allowlist entry landed)

`build_overwrite_statement`'s docstring reads:

> This module therefore adds NO new `persona=` call site and NO new `draw_all` call site —
> `PERSONA_ALLOWLIST` stays at exactly two entries and the widened D-21 guard in
> `tests/test_phase14_scoring.py` stays green without that file being touched.

The load-bearing claim ("this module adds no new `persona=` call site") is **still true**. The
parenthetical "`PERSONA_ALLOWLIST` stays at exactly two entries" became stale the moment Phase 18's
D-08 added its third, sanctioned entry — the same stale assumption that
`tests/test_phase16_driver.py::test_the_sweep_adds_no_persona_or_draw_all_call_site` encoded as
`len(...) == 2` and that 18-04 fixed at the root (the guard now asserts the sweep driver
contributes no entry, which is what it was always named after).

**Not fixed here** because it is prose in another phase's driver, no test reads it, and the diff
would touch a file outside 18-04's declared scope for a cosmetic gain during a parallel wave.
Whichever later plan next edits `scripts/phase16_persistence.py` should drop the clause after the
em-dash.
