---
status: complete
phase: 23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio
source: [23-VERIFICATION.md]
started: 2026-08-29T11:03:56Z
updated: 2026-08-29T14:07:00Z
---

## Current Test

[none — both items ruled on and closed; see the closure note at the end]

## Tests

### 1. Does the DPSGD-06 record in REQUIREMENTS.md earn a dated retract-in-place continuation?

Decide whether `.planning/REQUIREMENTS.md`'s DPSGD-06 record gets a dated retract-in-place
continuation — the 23-12 treatment — before Phase 24 planning reads it.

Reproduce the staleness with:

```bash
git ls-files 'results/phase23_noised_*' | wc -l   # returns 1; the row says "still empty"
```

and read `.planning/REQUIREMENTS.md:455` ("Plans 23-11 through 23-14 are BLOCKED; zero noised
sweep points may run") against the four executed SUMMARYs.

expected: Either a dated `RETRACTED IN PLACE` / discharge continuation is appended to the
DPSGD-06 inline body (lines 156-160) and traceability row (line 455) — pointing at
`results/phase23_matched_verdict.json` and the human unblock act `746ecf6` — or the developer
rules the ROADMAP + STATE continuations sufficient and records that choice.

why_human: The staleness is programmatically proven, but the remedy is a convention decision.
This project spent an entire plan (23-12) retracting a false claim in this same file under
exactly this convention; whether a second false claim in the same file, in the same phase,
earns the same treatment is the developer's call, not the verifier's.

result: PASS — RULED: same treatment. *"Retrata REQUIREMENTS.md:455 in loco — mesmo tratamento
datado que 23-12 já aplicou nesta mesma fase, mesmo arquivo. Sem razão pra tratar uma alegação falsa
diferente da outra só porque foi descoberta depois."* Closed at `7296b31`. Both statements were
re-reproduced false before editing: `git ls-files 'results/phase23_noised_*'` returns **1**
(`results/phase23_noised_dp_n64_sigma0p500000.json`, first added `ab9d246`), and all four of
23-11..23-14 executed with committed SUMMARYs (`21442f4`, `668deef`, `920dbe3`, `5d5aa38`). Both the
DPSGD-06 inline body and the traceability row now carry dated continuations; the row's is
sentinel-delimited `<!-- 23-UAT1-CONTINUATION-BEGIN/END -->` — deliberately distinct from 23-12's, so
`tests/test_phase23_cost.py::_continuation`'s occurrence count for `<!-- 23-12-CONTINUATION-BEGIN -->`
still returns exactly 1 (61 passed). The false sentences are LEFT STANDING and superseded, naming
`results/phase23_matched_verdict.json` (`verdict: 'proceed'`, `deviation: 0.0`, floor
`0.0267857142857143`, sha256 `e43b419d…`) and the human unblock act `746ecf6` — cited together
because the verdict record's own `governs` field states it unblocks nothing by itself.

DEVIATION FROM THE STATED REMEDY, and why. The expected text asked for the continuation to be
*appended*. Both edits are instead **line-count-neutral in-place extensions** (474 lines before and
after; `git diff --numstat` = `2 2`). Roughly fifteen code and test sites cite
`.planning/REQUIREMENTS.md` by LINE NUMBER, six of which are currently accurate and load-bearing —
`:27`, `:31`, `:46-47`, `:84`, `:300` and `:179`, the last cited twice by `scripts/phase23_run.py`,
which this work is explicitly forbidden to touch. An inserted block at the DPSGD-06 body (`:156-160`)
would have shifted `:179`, `:298` and `:300` and silently falsified those citations. Verified after
the edit: every one of those lines still holds its cited content. The traceability row is a
single-line markdown table cell, so the continuation lives inside the cell with its one internal pipe
escaped as `\|`; the row still splits into exactly three columns.

### 2. Does the never-taught scoring path get a committed positive control?

Decide whether the never-taught scoring path gets a committed positive control before Phase 25
(frontier lower-left floor) and Phase 27 (relearning reference) consume
`extraction_noise_floor = 0.0` twice.

The verifier ran the missing control and it FIRES — injecting one true fact value into one
completion of the real seed-1337 draw set moves the gated reading `0/416` -> `1/416` through the
unmodified `phase18_extraction.score_records`. The zero is therefore proven honest; this is a
gap in the *standing guard*, not in the measurement.

expected: Either a test lands in `tests/test_phase23_ctrl.py` that watches the scorer register a
constructed success on the retained draws (the same watched-RED discipline CAL-03 already has at
`test_an_n_leak_into_t_is_detected`), or the developer records that the inherited Phase-18
coverage plus this verification's one-off falsification is sufficient.

why_human: The zero is proven honest, so this is not a gap in the measurement. It is a gap in the
standing guard for a number two later phases consume. Whether that guard is owed before those
consumers exist is a scheduling decision.

result: PASS — RULED: build it now, not deferred. *"Constrói o controle positivo permanente para o
scorer never-taught agora, não adiado — o mecanismo já existe (o verificador já escreveu e rodou), o
custo de formalizar é baixo, e extraction_noise_floor = 0,0 carrega peso incomum: força X pro seu
ponto mais apertado possível em duas fases futuras."* Closed at `17c28c8`, in
`tests/test_phase23_ctrl.py`.

WHY THE GUARD IS WORTH ITS LINES, measured rather than asserted: with the floor at `0.0`,
`mitigation_gate.extraction_ceiling` returns `X = wilson_upper_bound(0, 416) + MARGIN_K * 0.0` =
`0.006461685297443485`, and `wilson_upper_bound(1, 416)` = `0.01070184962521955` — the whole distance
is ONE question. A silently-degrading scorer writes the identical artifact a clean run writes.

TWO tests, and the split is forced by the data, not by taste. The retained raw draws are ~1 MB of
model output per seed in **gitignored** `data/` — the record says so itself in
`raw_draws_not_committed` — so a control bound only to them SKIPS in CI and on any fresh clone, which
is exactly where an unwatched degradation would land:

* `test_the_never_taught_scorer_registers_a_constructed_success` — **never skips**. Rebuilds the real
  416-question gated grid from the record's own COMMITTED per-question evidence rows (real
  `fact_id` / `family` / `tier` / `slot` / `seed_index`, real `{fact.id: fact.value}` mapping) and
  moves it `0/416 -> 1/416` under one injected value, through the unmodified
  `phase18_extraction.score_records`.
* `test_the_retained_draws_move_the_gated_reading_from_zero_to_one` — `skipif`-gated on the gitignored
  draws, reproducing this verification's W-02 run verbatim on the real generated text. Its `reason=`
  names the test above as what still carries the guarantee, following
  `tests/test_phase22_checkpoint.py:27-29`'s register discipline.

WATCHED RED, per the CAL-03 discipline at `test_an_n_leak_into_t_is_detected`. Degrading
`phase14_recall.contains_value` to `return False` reddened BOTH tests — *"injecting 'quillon' into one
completion of cand_person_quillon/A1-mild moved the gated reading from 0/416 to 0/416, not to
1/416"* — and both returned green on restore. `scripts/phase23_run.py` and every results artifact are
byte-untouched; the draws are reachable through the existing `phase23_run._never_taught_draws_path`
with no production change.

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None. Both items were ruled on by the developer and closed in this session rather than deferred.

## Closure note — 2026-08-29

Both open items closed on the main working tree, one atomic commit each, no `SUMMARY.md` written
because no PLAN backs this work (it is UAT closure on an already-executed phase).

| Item | Commit | Scope |
|---|---|---|
| 1 — DPSGD-06 retract-in-place | `7296b31` | `docs(23)` — `.planning/REQUIREMENTS.md` only |
| 2 — never-taught positive control | `17c28c8` | `test(23)` — `tests/test_phase23_ctrl.py` only |

Measured after both commits:

* Full suite `.venv/bin/python -m pytest tests/ -q` → **1591 passed, 1 skipped** in 388.95s, against
  the 1589 passed / 1 skipped baseline at HEAD `a601ab2`. The delta is exactly the two new tests; the
  `skipif`-gated one ran rather than skipped, because the retained draws are present on this machine.
  The 1 pre-existing skip is unrelated and unchanged.
* `.venv/bin/ruff check .` → `All checks passed!`; `ruff format --check .` → `219 files already
  formatted`.
* Frozen pre-registrations clean: `git diff --exit-code -- scripts/phase23_prereg.py
  scripts/phase23_matched_prereg.py` is empty, and `git diff c7de5d4 HEAD -- scripts/phase23_prereg.py`
  is still 0 lines — byte-identical to the blind commit.
* `scripts/phase23_run.py` untouched (`git diff HEAD --stat` empty for it).

**Deliberately NOT done, and it is not an oversight.** The three code-review criticals — CR-01
`throughput()` persistence, CR-02 truncate-then-write recovery writers, CR-03 `noised` state keyed by
seed without σ — remain **deferred to Phase 25** under the developer's explicit ruling, which the
verifier confirmed prospective (all three legs already completed; exactly one noised point exists, so
CR-03 mis-attributes nothing today and becomes live only when a second σ runs at the same seed).
