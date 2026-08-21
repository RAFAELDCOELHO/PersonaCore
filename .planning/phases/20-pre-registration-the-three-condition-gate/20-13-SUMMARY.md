---
phase: 20-pre-registration-the-three-condition-gate
plan: 13
subsystem: planning-records
tags: [pre-registration, security-register, decision-record, gap-closure-wave-2]
requires:
  - "20-12 (the register state this plan rewrites: status: verified / threats_open: 0, T-20-19 closed)"
  - "20-VERIFICATION.md gaps 1 and 2 (the reproductions that force D-38..D-41)"
provides:
  - "D-38, D-39, D-40, D-41 in 20-CONTEXT.md — recorded BEFORE any artifact in this wave-set cites them"
  - "20-SECURITY.md at status: blocked / threats_open: 1 with T-20-19 carried OPEN"
  - "The BINDING register-counting method, written into 20-SECURITY.md and inherited by 20-17"
  - "The measured 20-SECURITY.md line-anchor drift map for 20-14..20-17"
affects:
  - "20-14, 20-15, 20-16, 20-17 — every one declares depends_on 20-13 and cites D-38..D-41"
  - "20-17 specifically: the re-close to threats_open: 0 is gated by D-39 and must use this counting method"
tech-stack:
  added: []
  patterns:
    - "Additive correction: historical text preserved byte-identically, the falsification appended beside it (D-36 / ROADMAP SC3 precedent)"
    - "Prose-not-a-row: an ### Open entry that must not contribute a row-start to a counted total"
    - "Every published number re-derived by calling the committed modules, never transcribed from the plan"
key-files:
  created: []
  modified:
    - ".planning/phases/20-pre-registration-the-three-condition-gate/20-CONTEXT.md"
    - ".planning/phases/20-pre-registration-the-three-condition-gate/20-SECURITY.md"
decisions:
  - "D-38 — the retention floor is refused by PROPERTY as well as by NAME; the magnitude bound also answers escalation 1 by elimination"
  - "D-39 — the register flips OPEN at 20-13 (wave 12) and re-closes at 20-17 (wave 16) only on watched-RED evidence; never the same commit"
  - "D-40 — both gaps close in this pass; the Y hole is NOT deferred to Phase 23"
  - "D-41 — the test harness supplies the governing retention floor; the bound's tolerance is never widened to admit a fixture"
metrics:
  duration: "~25 min"
  tasks_completed: 2
  commits: 3
  completed: 2026-08-21
---

# Phase 20 Plan 13: Record D-38…D-41 and Re-open T-20-19 Summary

Recorded the four decisions the 2026-08-21 re-verification forced, then flipped `20-SECURITY.md`
from `verified` / `threats_open: 0` to `blocked` / `threats_open: 1` — the record first, the honest
gate second, both before any artifact in this wave-set cites them.

## What Was Built

**Task 1 — `20-CONTEXT.md` carries D-38…D-41** (`4772efe`, 82 insertions / **0 deletions**), inserted
strictly below D-37 and strictly above `### Claude's Discretion`, under a second dated gap-closure
heading matching the shape `20-09` established at `:312-318`.

**Task 2 — `20-SECURITY.md` flipped OPEN** (`72ef455`, 61 insertions / 9 deletions, all nine inside
the seven sanctioned spans). Frontmatter, gate-status paragraph, register header + counting method,
`### Open` prose, the `T-20-19` row, the audit trail and the Sign-Off.

**Rule 1 correction** (`5b361f8`) — see *Deviations*.

## Every Published Number Was Re-Derived, Not Transcribed

Run against the committed tree with `.venv/bin/python`, importing `mitigation_gate`,
`phase20_gate_coverage` and `erasure_gate` directly:

```
governing floor (results/phase20_retention_floor.json::retention_ppl_noise_floor) = 0.008681618994239138
_ADAPTER_REGIME_RETENTION_FLOOR                                                   = 0.008681618994239138  (equal: True)
bound = floor * (1.0 + 1e-9)                                                      = 0.008681619002920757
FIXTURE_DESTROYED_MODEL / FIXTURE_CLEARING_POINT / FIXTURE_TRUNCATED_SWEEP        = 0.009  (all three)
0.009 > bound                                                                     -> True
ratio 0.009 / floor                                                               = 1.0366729991228745
retention_cap(0.009)                                                              = 3.90914
retention_cap(governing) == _GOVERNING_CAP                                        = 3.9085032379884783
retention_cap(5.0)                                                                = 13.89114
nudged = 0.06893 * (1 + 2**-50)  = 0.06893000000000006   | != borrowed -> True
retention_cap(nudged) == retention_cap(0.06893) == 4.029  | BIT-IDENTICAL: True
```

Both D-38 reproductions reconfirmed through the sanctioned route, with the control:

```
REPRO A  nudged borrowed floor 0.06893000000000006   verdict: PASS | cap: 4.029
REPRO B  retention_noise_floor=5.0, clean provenance verdict: PASS | cap: 13.89114 | governing: 3.9085032379884783
CONTROL  unperturbed 0.06893  -> REFUSED (SystemExit): "[phase20_gate_coverage] the retention noise
         floor IS 0.06893, the Phase 12 full-fine-tune seed pair, whatever ..."
```

D-41's **against-interest half**, measured at BOTH floors using the test file's real
`DEFAULT_HELDOUT_SWEEP = (0.30, 0.20)` (`tests/test_phase20_correction.py:106`):

```
direction_i                        floor=0.009 -> PASS         | floor=0.008681618994239138 -> PASS         | UNCHANGED: True
direction_ii                       floor=0.009 -> INCONCLUSIVE | floor=0.008681618994239138 -> INCONCLUSIVE | UNCHANGED: True
direction_ii_on_clearing_fixture   floor=0.009 -> INCONCLUSIVE | floor=0.008681618994239138 -> INCONCLUSIVE | UNCHANGED: True
heldout_coverage                   floor=0.009 -> INCONCLUSIVE | floor=0.008681618994239138 -> INCONCLUSIVE | UNCHANGED: True
ALL FOUR VERDICTS UNCHANGED UNDER THE SUBSTITUTION: True
```

All four match `results/phase20_gate_coverage_correction.json`'s published verdicts exactly. D-40's
supporting facts likewise measured: `0.0 <= float("nan") <= 1.0` is `False`, `nan >= 0.245` is
`False`, `isinstance(True, int) and not isinstance(True, bool)` is `False`, and grepping `scripts/`
and `src/` for `corrected_point_verdict` outside its own module returns nothing.

## THE BINDING REGISTER-COUNTING METHOD — inherited by 20-17

**A threat is counted once per DISTINCT `T-20-NN` id appearing anywhere inside `20-SECURITY.md`'s
register TABLES**, including ids enumerated inside a single cell of the grouped-by-plan table, which
are threats but not row-starts. Measured at `5da028a`:

```
distinct ids in table lines = 66      <- the published total; it already reconciles
| T-20-NN | row-starts      = 39      carrying 35 distinct ids
```

**The ARTIFACT was right and an earlier CHECK was wrong.** Counting row-starts publishes 35, which
contradicts the total the file substantiates in its own `38 + 8 + 20 = 66` paragraph. This method is
now written into `20-SECURITY.md` at the register header and is **binding on `20-17`** — the re-close
must reconcile 66 under it, not under row-starts. Post-flip the file still measures 66 distinct ids,
39 row-starts, 35 distinct among them: the flip changed the closed/open split, never the total.

The corollary is load-bearing and is why `### Open` names `T-20-19` in **prose**: `threats_open` must
equal the count of register ROWS at Status `open`, and a second `| T-20-19 |` row-start there would
make that count **2 against a published 1**. Measured after the flip: `### Open` row-starts = **0**,
register rows at Status `open` = **1**.

## Byte-Identity, Verified By Explicit Diff

Not by eye. Both spans extracted from `git show HEAD:...20-SECURITY.md` and compared:

```
T-20-21 REGISTER ROW BYTE-IDENTICAL: True | chars: 1877
T-20-19 PRE-EXISTING SPAN BYTE-IDENTICAL: True | chars: 1595
   *What was wrong, preserved:*   preserved: True
   *The closure:*                 preserved: True
   HEAD status cell ->  **closed**
   NEW  status cell ->  **open**
   appended sentence chars: 1135
   Watched-RED row T-20-19 / T-20-21 / T-20-48 / T-20-51 unchanged: True (all four)
```

The re-opening is an **appended dated sentence inside the same Mitigation cell**, never a rewrite.
`20-CONTEXT.md`'s first 355 lines (D-01…D-37) diff clean against `5da028a`, and the whole file is
**0 deletions** against it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] `20-SECURITY.md:39` citations falsified by this plan's own flip**

- **Found during:** Task 2, after the additive gate-status edit.
- **Issue:** Task 2 inserts four lines above the trust-boundary table, shifting every row. The
  `20-SECURITY.md:39` citation this plan wrote into D-39 one commit earlier (`4772efe`) resolves to
  the wrong row afterwards. Measured `5da028a` → post-flip:

  | span | was | now |
  |---|---|---|
  | Measured floor ↔ borrowed floor | `:33` | `:37` |
  | a frozen pin ↔ its correction | `:38` | `:42` |
  | a plan that says a thing will be done ↔ a guard that proves it was | `:39` | `:43` |
  | a published total ↔ the rows that substantiate it | `:40` | `:44` |
  | the `T-20-19` register row | `:91` | `:135` |

- **Fix:** D-39 now cites the boundary by TEXT and carries the full mapping, because **`20-14`
  cites `:39`; `20-15` cites `:39` and `:33`; `20-16` cites `:38` and `:40`; `20-17` cites `:39` and
  `:40`** — all written against the pre-flip file. Expect a second shift when `20-17` re-closes.
- **Not done:** the PLAN files were not amended. Plans are records.
- **Files modified:** `20-CONTEXT.md`. **Commit:** `5b361f8`.

### Plan-vs-Reality Mismatches Recorded, Not Amended

1. **`:67-80` and `:48-55` (Task 2 item 3).** The plan asked for these two line citations inside the
   counting-method paragraph. Both sit *below* the insertion point, so writing them would have
   published two more stale anchors on arrival. Resolved by referring to *"the grouped-by-plan table
   below"* and *"the paragraph below"* — same referents, no anchor to rot.
2. **"three committed fixtures" (D-41).** True, but only two carry the literal: `grep` finds
   `retention_noise_floor: 0.009` at `mitigation_gate.py:1237` and `:1267` only.
   `FIXTURE_TRUNCATED_SWEEP` (`:1277`) inherits it through `**FIXTURE_DESTROYED_MODEL`. D-41 says so
   explicitly rather than implying three literals.
3. **`_corrected_call`'s `base` dict is `:136-139`,** not the `:135-139` a first reading suggests —
   `:135` is the `kwargs` comprehension. D-41 cites `:136-139`.
4. **"3.7%" (D-41).** Re-derived as `1.0366729991228745x`, i.e. **~3.67%**. D-41 publishes 3.67%.
5. **"exactly two commits" (`<verification>`).** Three landed: the two task commits plus the Rule 1
   anchor correction. The acceptance criterion that matters — the flip and the decision record being
   *separate* commits — holds: `20-SECURITY.md`'s latest is `72ef455`, `20-CONTEXT.md`'s is
   `5b361f8`.

**Not touched, deliberately:** `STATE.md` and `ROADMAP.md` are absent from `files_modified`, so no
`gsd-sdk` mutation handler was invoked. `REQUIREMENTS.md` was not marked — this plan **re-opens**
GATE-02's residual; marking it complete would be the exact over-claim it exists to correct.

## Verification Evidence

Every must-have verified by a command actually run:

| Must-have | Command output |
|---|---|
| D-38…D-41 recorded, dated, positioned | `grep -c 'D-38'` → `5`; heading `### Resolved during gap-closure wave 2 — decisions forced by the 2026-08-21 re-verification`; position assert `ok` |
| frontmatter | `status: blocked` / `threats_open: 1` |
| `### Open` prose, one open row | `### Open row-starts: 0 \| names T-20-19: True`; `register rows at Status open: 1` |
| total stays 66 | `distinct ids in table lines = 66 \| row-starts = 39 \| distinct among row-starts = 35`; `65 closed, 1 open` count `1` |
| T-20-19 span / T-20-21 row byte-identical | explicit diff, both `True` (see above) |
| no code, test or results write | `git diff --exit-code -- scripts/ tests/ results/` → **0** |
| frozen pins | `git diff --exit-code -- scripts/mitigation_gate.py scripts/erasure_gate.py` → **0** |
| full suite | `874 passed, 1 skipped in 216.34s` — the recorded baseline, exactly |
| phase-20 guards | `29 passed in 2.42s`, zero skips |
| lint | `All checks passed!` / `176 files already formatted` |

## Threat Flags

None. This plan writes no code, opens no network path, touches no schema and adds no dependency —
`git diff --exit-code -- scripts/ tests/ results/` returns 0. `T-20-67`…`T-20-70` from the plan's
own `<threat_model>` are discharged by the wave graph and by the byte-identity assertions above;
they are register-bookkeeping for `20-17`, not new surface.

## Known Stubs

None.

## Self-Check: PASSED

- `20-CONTEXT.md` — FOUND, D-38…D-41 present and positioned
- `20-SECURITY.md` — FOUND, `status: blocked` / `threats_open: 1`
- `4772efe` — FOUND
- `72ef455` — FOUND
- `5b361f8` — FOUND
