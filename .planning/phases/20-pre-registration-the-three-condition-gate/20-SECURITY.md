---
phase: 20
slug: pre-registration-the-three-condition-gate
status: blocked
threats_open: 2
asvs_level: 1
created: 2026-08-20
---

# Phase 20 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

**Register origin:** `register_authored_at_plan_time: true` — all seven PLAN files carried a
parseable `<threat_model>` block, and all seven SUMMARY files carried `## Threat Flags`. This audit
therefore **verified that the declared mitigations exist**; it did not build a retroactive STRIDE
register.

**Gate status: BLOCKED.** `threats_open: 2`. Phase advancement is blocked until the dated
continuation lands. See *Blocking Remediation* below.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| git object DAG ↔ the evidentiary record | The only boundary that matters this phase. A rule's authority comes from provably preceding the numbers it judges. | Commit SHAs, first-add ordering |
| `erasure_gate.py` (`23a830c`, closed) ↔ `mitigation_gate.py` | v3.0's closed pin is an immutable input. Any write across this boundary voids the milestone. | Imported constants and functions, by object identity |
| Phase 20 (rule) ↔ Phase 23 (measurement) | The extraction floor crosses this boundary. Phase 20 cannot measure it. | `extraction_noise_floor` + its provenance dict |
| Measured floor ↔ borrowed floor | An already-published number from a different quantity or regime is the cheapest way to make a criterion look rigorous while being wrong. | `retention_noise_floor`, `extraction_noise_floor` |
| outcome thresholds ↔ resource parameters | The gate/budget split — a resource calibration must never be mistakable for an outcome threshold. | Import graph: `mitigation_gate` must never import `mitigation_budget` |
| "we could not tell" ↔ "it did not work" | Collapsing INCONCLUSIVE into FAIL is the single most likely way this gate produces a dishonest negative. | Verdict strings and reason lists |
| a written branch ↔ a fired branch | A branch nobody has watched fire is a branch nobody has verified. | Six `__main__` outcomes + the CI twin |
| gitignored inputs ↔ CI | `checkpoints/` is gitignored, so CI can never re-derive the artifact. | Every reading, denominator, seed, adapter sha256 embedded in the JSON |

---

## Threat Register

46 threats. **44 closed, 2 open.**

### Open

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-20-21 | Repudiation | an INCONCLUSIVE silently reported as a FAIL, or vice versa | mitigate | **INCOMPLETE — threat REALIZED.** The declared mitigation (three branches, each proved differentially against the counterfactual it overrides) is present and verified. It does not reach a **fourth** mislabeling path: GATE-06's sweep-coverage test decides on RAW rates (`mitigation_gate.py:798-799`) while condition (a) decides on `wilson_upper_bound(k, n)` (`:755`), against the same `ceiling`. Reproduced in **both** directions at n=104, X=0.04535522866494124 — `(1/104, 3/104)` brackets X under the (a) rule yet reads as never-crossed → spurious `INCONCLUSIVE`; `(3/104, 11/104)` reads as covered while ZERO points clear X → spurious `FAIL`. No spurious `PASS` is constructible under self-consistent inputs. The register named this exact threat; the mitigation was scoped too narrowly. | **open** |
| T-20-19 | Spoofing | a v3.0-regime floor standing in for the v4.0 retention floor | mitigate | **DISCHARGED AS STATED, RESIDUAL REMAINS.** The declared mitigation is verified true — `V20_RETENTION_NOISE_FLOOR` is neither imported (AST: five names, absent) nor present as a numeric constant (`0.068930` absent). It does not cover the **caller-supplied** path. `extraction_ceiling` carries **3** `_prove` calls refusing wrong-arm / <2-seed / missing-provenance floors; `retention_cap` carries **0**. Measured: `retention_cap(retention_noise_floor=0.068930)` returns `4.029` — the *looser* cap — with no refusal. Asymmetric against T-20-24, whose whole point is that `mitigation_point_verdict` calls `extraction_ceiling` itself so no path to a verdict skips the provenance check. There is no equivalent choke point on the retention leg. | **open** |

### Closed

All 44 verified present in the implementation. Grouped by plan; full mitigation text in each
`20-0N-PLAN.md` `<threat_model>` block and each `20-0N-SUMMARY.md` `## Threat Flags` table.

| Plan | Threat IDs | Category coverage | Status |
|------|-----------|-------------------|--------|
| 20-01 | T-20-01, T-20-02, T-20-03, T-20-04 | Repudiation, Tampering ×3 | closed |
| 20-01 | T-20-05, T-20-06 | Info disclosure, EoP — *disposition `accept`* | closed |
| 20-02 | T-20-07, T-20-08, T-20-09, T-20-10 | Spoofing, Tampering ×3 | closed |
| 20-02 | T-20-11 | Info disclosure — *disposition `accept`* | closed |
| 20-03 | T-20-12, T-20-13, T-20-14, T-20-15, T-20-16 | Repudiation ×2, Tampering ×3 | closed |
| 20-03 | T-20-17 | EoP — *disposition `accept`* | closed |
| 20-04 | T-20-18, T-20-20, T-20-22, T-20-23, T-20-24 | Tampering ×3, Spoofing ×2 | closed |
| 20-05 | T-20-25 … T-20-31 | Tampering ×4, EoP, Spoofing ×2 | closed |
| 20-05 | T-20-32 | Tampering — `accept` (this plan) / `mitigate` (downstream) | closed |
| 20-06 | T-20-33 … T-20-39 | EoP, Tampering ×3, Spoofing ×2, Repudiation | closed |
| 20-07 | T-20-40, T-20-41, T-20-42, T-20-43, T-20-44, T-20-46 | Repudiation ×3, Tampering ×3, Spoofing | closed |
| 20-07 | T-20-45 | Info disclosure — *disposition `accept`* | closed |

**Watched-RED evidence (mitigations observed failing, then restored byte-identically):**

| Threat ID | Deliberate break | Observed |
|-----------|------------------|----------|
| T-20-33 | `import mitigation_budget` added to the pin | AST guard fired; reverted byte-identical |
| T-20-34 | local `def wilson_upper_bound` shadowing the import | both static and `is`-identity halves fired |
| T-20-35 | `THIRD_CONSTANT = 0.9` added at module scope | `_module_scope_floats` audit fired |
| T-20-03 | verdict relabel | `_prove_verdict_domain()` raised `SystemExit` at import (exit 1) |
| T-20-13 | `git rm` + re-add of a `phase20_*` artifact | earliest-add SHA byte-identical to the pre-delete state — laundering provably impossible |

A guard nobody has watched fail is a guard nobody has verified; the five above were watched.

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-20-01 | T-20-05, T-20-11 | No network, no secrets, no untrusted input anywhere in the pin. `_git` passes an argv tuple and never uses `shell=True`, so a glob containing a shell metacharacter reaches git as a pathspec. | Plan-time disposition, verified in implementation | 2026-08-20 |
| R-20-02 | T-20-06 | D-33, explicitly. Future-phase artifact prefixes cannot be asserted present in `V4_ARTIFACT_GLOBS` — an assertion catches an empty match set, never an incomplete one. Accepted in exchange for never asserting coverage this phase cannot demonstrate; recorded in the tuple's own comment. | Plan-time disposition (D-33) | 2026-08-20 |
| R-20-03 | T-20-17 | `git merge-base --is-ancestor X X` is reflexive (measured, exit 0), so a gate and artifact in the SAME commit would pass. D-08's strictly-after rule is a recorded **discipline** tighter than the mechanism. Stated in the fixture docstring so a later reader treats same-commit as neither a defect nor a licence. Not exercised: the pin and artifact landed in distinct commits (`abf9072` → `9bb34ad`). | Plan-time disposition (D-08) | 2026-08-20 |
| R-20-04 | T-20-45 | `checkpoints/` is gitignored by design (`.gitignore:14-15`), so CI can never re-derive `results/phase20_retention_floor.json`. Mitigated by embedding every reading, denominator, seed, adapter path, adapter sha256, git SHA, torch version and device in the JSON — 25 provenance keys. | Plan-time disposition (D-32) | 2026-08-20 |

*Accepted risks do not resurface in future audit runs.*

**T-20-21 and T-20-19 are NOT accepted risks.** They are open defects with reproductions,
deliberately left open rather than logged as accepted — accepting a realized mislabeling defect
would make the security gate green over a known wrong verdict.

---

## Blocking Remediation

`scripts/mitigation_gate.py` is **permanently uneditable** — `results/phase20_retention_floor.json`
was committed at `9bb34ad`, and the frozen-pin guard
(`test_phase20_prereg_is_frozen_before_every_phase20_result`) takes `adds[-1]`, the earliest add.
Plan 20-03 proved across five observed states that `git rm` plus re-add reproduces that SHA
byte-identically. The only legal correction path is a **dated continuation** via
`scripts/_addendum.py::append_addendum(path, addendum, *, pending, recorded)` — both keywords
required — plus an armed tripwire test (D-24).

These three items are bound to **one** gap-closure phase and **close together**:

| # | Item | Threat | Requirement |
|---|------|--------|-------------|
| 1 | GATE-06's coverage test uses `wilson_upper_bound(k, n)`, matching what condition (a) already uses, on both axes — eliminating both reproduced failure modes | T-20-21 | GATE-06 |
| 2 | `sweep_heldout_recalls` added at the caller, covering the held-out leg SC2 makes load-bearing and which today has no coverage check at all (`grep -c` = 0 in the 21-kwarg signature) | T-20-21 | GATE-06 |
| 3 | A provenance tripwire on `retention_cap`, **mirroring the three `_prove` calls that already protect `extraction_ceiling`** — the same asymmetry T-20-19 identified, corrected with the same structural discipline rather than merely documented | T-20-19 | GATE-02 residual |

The armed tripwire must prove **RED-then-GREEN against both reproduced cases** —
`(1/104, 3/104)` and `(3/104, 11/104)` — not merely against the happy case.

Entry point: `/gsd:plan-phase 20 --gaps`. The GATE-06 row in `.planning/REQUIREMENTS.md` carries the
full reproduction detail.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-20 | 46 | 44 | 2 | `/gsd:secure-phase 20` — orchestrator, State B (create) from plan-time register |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed — **NOT MET: 2 open (T-20-21, T-20-19)**
- [ ] `status: verified` set in frontmatter — **NOT MET: `status: blocked`**

**Approval:** pending — blocked on the three-item dated continuation above.
