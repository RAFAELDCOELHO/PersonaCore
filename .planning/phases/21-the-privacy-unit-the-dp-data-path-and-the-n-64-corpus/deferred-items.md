# Phase 21 — Deferred Items

Out-of-scope discoveries found during execution. Logged, **not** fixed — the scope boundary is
that an executor auto-fixes only what its own task's changes caused.

---

## D-1 — `tests/test_phase18_docs.py::test_no_bare_zero_percent_in_docs` is RED on `main`

**Found during:** plan 21-03, full-suite verification run.
**Status:** pre-existing, PROVEN not caused by this phase.

```
FAILED tests/test_phase18_docs.py::test_no_bare_zero_percent_in_docs
E  AssertionError: README.md publishes a bare zero percentage at offset 387:
   ' were extractable under the strongest of four tested black-box attack\n
     families, against a 0% baseline with no adapter present — and '
1 failed, 884 passed, 7 skipped in 199.71s
```

**Why it is not plan 21-03's:**

```
$ git diff HEAD~1 HEAD --name-only
tests/test_phase20_prereg.py                 # the ONLY file 21-03 touches

$ git log -1 --format='%h %ad %s' --date=short -- README.md
9cc2c94 2026-08-22 docs: reframe README opening around the privacy audit

$ git merge-base --is-ancestor 9cc2c94 7ca8945   # 7ca8945 = wave-2 base
exit 0
```

`9cc2c94` reworded the README opening and introduced a bare `0%`. The guard requires every
published zero to arrive with its denominator, its Wilson bound and its rule-of-three ceiling —
`tests/test_phase18_docs.py:975`. The README sentence states a `0%` baseline with none of the three.

**Fix belongs to a docs plan, not here.** Either restate the baseline with its denominator and
bounds, or — if the `0%` is a *design* fact (no adapter present ⇒ nothing to extract) rather than a
*measurement* — the guard needs an explicit carve-out for the no-adapter control. That is a
judgement about what the README claims, which is out of a test-fixture plan's remit.

**Note:** the guard's own regex self-controls pass, so the scan is live, not collapsed.
