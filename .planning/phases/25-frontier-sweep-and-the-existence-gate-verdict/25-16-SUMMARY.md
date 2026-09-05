---
phase: 25
plan: 16
subsystem: sweep-extremes
tags: [D-15, D-19, D-22, D-36, ADVT-01, extremes, interleave]
requires:
  - results/phase25_point_dp_n8_sigma0p000000.json
  - results/phase25_point_dp_n64_sigma0p000000.json
  - scripts/phase25_points.py
provides:
  - results/phase25_extremes_log.json
  - scripts/phase25_extremes_log.py
  - tests/test_phase25_extremes.py
affects: []
tech-stack:
  added: []
  patterns:
    - "the executed order is read from single-path commit timestamps, never from a plan"
decisions:
  - "ADVT-01's subject now exists: results/phase25_point_adv_n8_ratio1p909091.json, adapter sha256 in the log's advt_01 block."
  - "The adversarial arm's condition (c) failure is a property of its no-replay recipe (25-14 note §12.5c), disclosed in the log's four_corner_findings and left to 25-18 to state in the verdict."
metrics:
  duration: "six extremes landed by the driver 2026-09-04 23:08 -> 2026-09-05 05:48 (-03:00); log + tests ~40 min"
  completed: 2026-09-05
---

# Phase 25 Plan 16: The Eight Extremes Summary

The six non-control extremes ran interleaved across the four legs — `dp_n8`, `adv_n8`, `dp_n64`,
`adv_n64`, `adv_n8`, `adv_n64` — each landing in its own single-path commit, and
`results/phase25_extremes_log.json` (`491ba48`) records the order from those commits' timestamps.
**No structural problem appeared at any corner.** ADVT-01's subject — an adapter trained at a
non-zero adversarial ratio — now exists (`adv_n8_ratio1p909091`, `94167ea`).

## The four corners

| point | commit | ε / `clip_bind_count` | mask fraction (real) vs 24-07 build | extraction gated, of 104 (A1-mild / A1-aggr / A2 / A3) | dialogue / retention |
|---|---|---|---|---|---|
| `dp_n8_sigma80` | `2130b94` | 0.63398 / 1600 | — | 0 / 0 / 0 / 0 | 4.5744 / 3.8989 |
| `dp_n64_sigma80` | `fb025f3` | 0.63398 / 12800 | — | 0 / 0 / 0 / 0 | 4.5740 / 3.8997 |
| `adv_n8` ratio 0 | `a664f03` | null / null | 0.3587 vs 0.35866 (Δ < 1e-9) | 102 / 69 / 103 / 102 | 14.660 / 6.307 |
| `adv_n64` ratio 0 | `f7515ca` | null / null | 0.3902 vs 0.39016 (Δ < 1e-9) | 1 / 1 / 8 / 0 | 16.136 / 5.884 |
| `adv_n8` ratio 1.909 | `94167ea` | null / null | 0.2410 vs 0.24101 (Δ < 1e-9) | 23 / 0 / 78 / 29 | 16.261 / 7.085 |
| `adv_n64` ratio 1.909 | `6b496fc` | null / null | 0.2517 vs 0.25173 (Δ < 1e-9) | 0 / 0 / 2 / 1 | 16.428 / 6.200 |

- **The four mask fractions equal 24-07's build-only figures** to better than 1e-9: the build is
  deterministic, so the band is confirmed rather than re-measured (binding corner still `adv_n8` upper).
- **`adversarial_family_counts` at both upper extremes:** `adv_n8` 171 / 170 / 171 and `adv_n64`
  1366 / 1365 / 1365 across the three trained families — all within one; the held-out A2 absent.
- **sigma=80 reads 0/416 at both capacities** — the never-taught floor, with `zero_extraction_has_nll`
  true and ε = `EPSILON_LADDER[-1]` re-derived by `epsilon_for`. The pre-registered null is reachable.
- **Adversarial training reduces extraction at the pool ceiling** (`adv_n8`: 102→23, 69→0, 102→29)
  while the held-out A2 stays the most extractable family (78/104, D-36's generalization gap).
- **The adversarial arm's dialogue is 3.1–3.6x the base at every corner, ratio 0 included** —
  the no-replay recipe (25-14 note §12.5c), not the ratio. Condition (c) will read this as failure.

## Verification

- `tests/test_phase25_extremes.py`: **64 passed, 0 skipped** (flag set); `-k "one_commit or exactly_one_path"` collects 16, all pass; `-k precedes_every_interior` passes (no interior record yet; the eight are tracked and ordered).
- The frozen modules and `pyproject.toml`: untouched.
- The flag-unset full-suite line is 25-14's; during the sweep the suite runs with the flag set (D-44).

## Commits

`41df48d` emitter · `491ba48` log (one path) · `0a902c5` tests · six driver commits listed above.
