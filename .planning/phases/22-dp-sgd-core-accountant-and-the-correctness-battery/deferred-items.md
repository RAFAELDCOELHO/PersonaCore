# Phase 22 — Deferred Items

Out-of-scope discoveries logged during execution. Each names its owner; none is fixed here.

---

## D-1 — `tests/fixtures/phase22_reference.py:185-187` still carries a FALSE figure

**Found during:** plan 22-17, Task 2 (editing that same file).

**The text**, inside `EPSILON_OVERFLOW_REGIME`'s provenance block:

> The error is EXACTLY ZERO at sigma >= 0.42, so these two rows are the whole reachable band.

**Why it is false:** `22-VERIFICATION.md` (lines 92-101, 315-318) retracts it in the verifier's own
name. It measured the FIX's delta — pre-fix versus post-fix *shipped* values, which are genuinely
bit-identical for sigma >= 0.4125 — and not the error against truth. Against 60 dps the error at
sigma >= 0.42 is 1.100e-13 at 0.4200 and 9.631e-12 at 0.4185, and the two rows were **not** the
whole reachable band: [0.4135, 0.4185] was reachable and uncovered, which is precisely the band
22-17 closes.

**Independently re-confirmed in this session**, post-fix, over sigma in [0.4130, 0.4200] step
0.0005 at T=200: every row's `erfc(b)` is subnormal or zero, i.e. every row was in the defective
band, and none of them had an error of exactly zero against 80-dps truth (measured 1.5538e-15 to
3.1897e-14 after the fix).

**NOT FIXED HERE, deliberately.** 22-17's plan does not ask for it, and the orchestrator's dispatch
brief names **plan 22-19** as the plan that exists to undo false figures in committed comments.
Fixing it here would collide with that plan's scope. `.planning/REQUIREMENTS.md:350` carries the
same sentence and needs the same correction.

**Owner:** plan 22-19. **Blast radius:** two comment blocks, no executable code, no test.

---

## D-2 — `math.ldexp(1.0, -1022)` is mentioned in prose inside `src/`

**Found during:** plan 22-17, Task 3 (running the plan's own `grep -rn "float_info" src/` assertion).

The plan asserts that grep is **empty**. Measured, it returns **one** match — line 90 of
`accountant.py`, which is a COMMENT I wrote in Task 1 explaining why `sys.float_info.min` is
deliberately *not* used and `math.ldexp(1.0, -1022)` is used instead.

This is a prose mention, not a code use. The load-bearing assertion is the module's import ceiling,
which is unchanged and stronger: `grep -n "^import \|^from "` returns the single `import math`,
`grep -rn "import sys" src/personacore/privacy/` is empty, and
`grep -rn "float_info" src/ | grep -v '#'` has no non-comment match.
`test_accountant_imports_math_only` asserts hard equality with `{"math"}` statically and out of
process, and it passes.

**No action needed.** Recorded so the next executor running the same grep does not read a comment
as a violation. If a future plan wants the grep to stay literally empty, the comment can drop the
two words `sys.float_info.min` — at the cost of the reader no longer being told which constant was
rejected and why.
