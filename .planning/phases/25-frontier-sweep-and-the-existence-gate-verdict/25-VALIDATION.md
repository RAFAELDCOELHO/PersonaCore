---
phase: 25
slug: frontier-sweep-and-the-existence-gate-verdict
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-31
derived_from: 25-RESEARCH.md § Validation Architecture (commit b1e4a28)
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `25-RESEARCH.md` § Validation Architecture. The reasoning and the measurements behind
> each row live there; this file is the execution contract.
>
> **What makes this phase's contract different:** the deliverable is a 4.5–6.3 day unattended compute
> run (44 points, ~107 h measured / ~150 h ceiling). Feedback latency during the run is measured in
> minutes, not seconds, and the dominant failure mode is *a structural fact discovered by spending
> GPU hours*. Every structural invariant here has a millisecond CPU proxy, and all of them belong in
> Wave 0 — before any point runs.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` 8.x (`[tool.pytest.ini_options]`, `pyproject.toml:24-26`) |
| **Config file** | `pyproject.toml` — `testpaths = ["tests"]`, `pythonpath = ["."]`; `tests/conftest.py` exists (D-44's home for the `--sweep-active` option) |
| **Quick run command** | `.venv/bin/python -m pytest tests/test_phase25_*.py -q` |
| **Full suite command** | `make test` → `.venv/bin/pytest -q` (`Makefile:12-13`) |
| **Measured suite size** | **1648 collected** (`pytest --collect-only -q`, 2.84 s) |
| **Measured full-suite runtime** | **1647 passed, 1 skipped, 386.21 s (6m26s)** at `8dd6415` — the baseline to beat |
| **Lint** | `make lint` → `ruff check . && ruff format --check .` (`Makefile:15-16`) |
| **CI** | `.github/workflows/ci.yml` — ubuntu-latest, Python 3.11, CPU-only. **Every MPS leg MUST stay `skipif`-gated or CI goes red.** |
| **MPS register** | `tests/test_phase23_mps_venue.py:60-80` — the ONE definition; 5 importers + `tests/test_mps_smoke.py:30-31` standalone |
| **MPS-parametrized node ids** | **47** across 11 files, device-touching in 7. D-44's composition point is **two** edits, not five |

---

## Sampling Rate

- **After every task commit:** `.venv/bin/python -m pytest tests/test_phase25_*.py -q` — target **< 30 s**.
  **Plus**, on any task touching `scripts/mitigation_*.py`:
  `pytest tests/test_phase20_prereg.py -k import_graph -q`, and
  `git diff --exit-code -- scripts/mitigation_gate.py scripts/mitigation_accountant.py scripts/mitigation_unit.py scripts/phase18_extraction.py`
  returning **0** — those four are ancestry-guarded and permanently uneditable.
- **After every plan wave:** `make test` on the M3 (**measured 6m26s**) plus `make lint`.
  **Record the skip count explicitly** — a green run that silently skipped the MPS legs is the
  failure, not the pass.
- **While the sweep is running:** the full suite is **contending**, not free. Run it with D-44's
  sweep-active flag set; the MPS legs must skip **loudly** — reason text naming the sweep, and a skip
  count stated in advance (moving from **1** to a pre-declared number). A contention failure must
  never be readable as a genuine one.
- **During the sweep, the run's own sampling rate:** heartbeat emitted from the driver's **outer loop
  on a wall-clock 60 s timer** carrying `(utc, point, stage, shape, draw_index)`, with the stall
  threshold **N = 5 min**. See *The Nyquist Derivation* below — N is an output of measurement.
- **Before `/gsd:verify-work`:** full suite green on the M3 with the sweep **not** running and **zero**
  unexpected skips; quote the literal `N passed, M skipped` line.
- **Max feedback latency:** 30 s per task; one 6.5-minute full-suite run per wave; 5 min stall
  detection during the run (**0.005%** of a 107–150 h sweep).

---

## The Nyquist Derivation (D-12 / D-16) — N is measured, not chosen

D-16 requires `N` to be *derived from the measured worst-case gap between heartbeat lines at the
slowest attack shape*. Measured (`data/phase23_never_taught_seed1337_draws.json`, `shapes[*].timing`;
existing print cadence `scripts/phase23_run.py:4524` = one line per 24 prompts):

| Regime | Slowest shape | 24-prompt gap |
|---|---|---|
| Measured, seed 1337, K=16 | A3 (34.03 min/shape) | **3.78 min** |
| Ceiling / no-EOS (`phase23_cost.json:generation.per_shape`) | A1-mild (45.27 min/shape) | **5.03 min** |
| At `FULL_FIDELITY_K = 48` (D-11 promotion) | — | **≈ 15.1 min** |

**The true worst case is not in the draw loop.** `dp_n64` training is **1383.3 s = 23.06 min** with no
per-shape line at all. An event-driven heartbeat tied to the prompt counter therefore forces
`N ≥ ~35 min` to avoid firing on all 22 n=64 training legs — 7× coarser than the draw loop can
resolve, and it buys nothing.

**Contract:** wall-clock 60 s heartbeat from the outer loop (sampling rate independent of stage),
**N = 5 min** (≥ 5 missed beats before a stall record). **Both the heartbeat and the stall watcher
must themselves be watched before the sweep** — run the driver against a deliberately-stalled stub,
observe the watcher writing a stall record, and observe that it does **not** kill, restart or clean
up. D-16's detect-never-act half is the property most likely to rot.

---

## Distinguishing a Kill From a Genuine Failure

| Signal | Where it is written | What it distinguishes |
|---|---|---|
| shape block present in `blob["shapes"][family]` with `draws` + `timing` | `data/phase25_*_draws.json` (gitignored) | a completed shape from an interrupted one — **the resume unit** (D-09) |
| cache identity `(adapter_sha256, corpus_sha256, k)` refused at load | `phase23_run.py:4281-4291` | draws off different weights / corpus / budget — refuses rather than pools |
| committed per-point record present in `results/` | `git ls-files` | **"a reading landed"** vs "killed before any reading" — D-10's one-attempt unit |
| per-shape sha256 committed as each block lands | the point record | closes the delete-and-redraw leak (`data/` is gitignored, `.gitignore:17`) |
| heartbeat last line | the heartbeat file | *where* it died — stage, point, shape, draw index |
| stall record | the watcher's output | silence detected, **no action taken** |

**[BLOCKING] Corollary.** `_never_taught_write_draws` (`phase23_run.py:4300-4302`) is a bare
`path.write_text` over ~970 KB and is **not atomic**; there is **no atomic-write helper in the repo**.
A kill mid-write yields JSON that `json.loads` rejects — turning "lost one shape" into "lost the whole
point", the exact failure D-09 exists to prevent. The block writer must become tmp + `os.replace`
before any point runs.

---

## Cheap (CPU, ms) vs Expensive (MPS, hours) — and where the proxy lives

| Property | Expensive form | Cheap proxy that must exist first | Cost |
|---|---|---|---|
| `clip_norm=inf` refused (CTRL-02) | discovering it mid-sweep | `DPSGD(nn.Module(), sigma=0.0, clip_norm=math.inf)` → `ValueError[dp-refusal:clip-domain]` — domain check is pre-pass, no model needed | **ms** |
| gate's null branch reachable (D-32 / FRONT-04) | running 44 points | `capacity_comparison(small_cleared=False, large_cleared=False, …)` → `'null-at-both-capacities'` | **ms** |
| extra mechanism keys ignored (D-25) | a silently-incomparable capacity verdict | live `capacity_comparison` with divergent `clip_norm` passes; caller-side `_prove` refuses | **ms** |
| condition (a) is zero-tolerance (D-42) | reading it off a published verdict | `tolerance_report(ceiling=X, n_questions=416)` → `(0, 0.0, "ZERO TOLERANCE…")` | **ms** |
| 21-kwarg verdict assembles | after the sweep | live `mitigation_point_verdict(...)` with the never-taught pooled block | **ms** |
| σ ↔ ε ladder correspondence (D-17) | a mis-pinned grid found at point 30 | `epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, DELTA) == EPSILON_LADDER[i]`, stdlib `math` only | **ms** |
| driver's git surface is exactly `{add, commit}` on the record path (§O1) | an unscoped `git` call discovered after 44 commits | **AST walk over the driver module** — never grep, the driver's prose discusses git | **ms** |
| mask fraction in band at every grid corner | a `SystemExit` **after** compute is spent | the 24-07 four-corner build-only check, already green | **2.2 s** |
| bins rebuild byte-identically after a kill (D-09) | a 2 h loss | `tests/test_phase23_resume.py` | **s** |
| budget register complete (D-17 / D-24) | a constant shipping with no re-derivation | `test_phase23_budget.py::test_z_was_sized_against_the_ceiling` — **natural RED** | **s** |
| plotting module never loads torch (D-33) | a figure not regenerable from a clone | `test_phase15_plots.py:291-352` retargeted | **~1 s** |
| D-01's reproduction (790/1008) | ~40 s train + **2.04 h** score per capacity | *none exists* — genuinely expensive, which is why `prove_reproduction` HALTS at zero sweep points (D-07) | **h** |
| adversarial scoring throughput | ~95% of the spend | D-14's timed 768-draw probe at both extremes | **≈30 min** |

**The rule: no plan may discover a structural fact by spending GPU hours.** Precedent: 24-07 converted
a post-compute `SystemExit` into a 2.2-second CPU test.

---

## Structurally Checked vs Merely Declared

| Decision | Invariant | Structural? | Watched RED |
|---|---|---|---|
| D-04 | no later plan asserts σ=0 ≡ seam-off bit-identity | yes — armed tripwire | ⚠️ **planted** (no natural RED) — plant against a scratch copy, never the real file |
| D-07 | `prove_reproduction(k, n)` HALTS at zero sweep points on a miss | yes — hard `==` on integer counts | ✅ natural: call `(789, 1008)`, watch the halt message |
| D-25 | `clip_norm` equal across compared capacities | yes — caller-side `_prove` before the gate | ✅ natural: the live divergent-`clip_norm` call demonstrates the hole |
| D-30 | no bare ε printed outside the helper | yes — **AST walk, never grep** | ✅ natural: `mitigation_gate.py` carries `epsilon` in 25 string literals with `ast.Name` count **0** — grep goes false-RED on it today; demonstrate grep-RED / AST-GREEN |
| §O1 | driver's executable git action set is exactly `{add, commit}` over the point-record path | yes — **AST walk over the driver** | ✅ natural: add a scratch `subprocess.run(["git","push"])` to a copy and watch it fire |
| D-33 | plotter opens only `results/phase25_frontier.json`, never torch | partly — (a)(b)(c) port; allow-list is new | ✅ natural for (a)(c); allow-list clause needs its own RED |
| D-34 | live mechanism matches the pin, or the **whole sweep** halts | yes — exact `==` on 5 fields at write time | ✅ natural: write a record with `composed_steps=199` |
| D-36 | `held_out_generalization` re-derives exactly from per-point counts | yes — write-time assertion | ✅ natural: perturb one per-family count in a fixture |
| D-42 | X from the designated-seed pooled block, never re-reduced | **yes, already enforced** — `extraction_ceiling` `_prove`s `provenance["arm"] == NEVER_TAUGHT_ARM` (`mitigation_gate.py:426`); `tolerance_report` **refuses** the 5-seed X | ✅ already watched — live `ValueError` reproduced |
| D-44 | MPS legs skip with a reason naming the sweep | yes — `skipif` at the register | ✅ natural: set the env var, assert skip **count** and **reason text** |

---

## Per-Requirement Verification Map

| Req / D | Behaviour asserted | Type | Command | Exists? |
|---|---|---|---|---|
| CTRL-02 / D-01 | `clip_norm=math.inf` raises `[dp-refusal:clip-domain]`; `C=1e6` gives `clip_bind_count == 0` | unit (CPU) | `pytest tests/test_phase25_control.py -k clip_domain -x` | ❌ W0 |
| CTRL-01 / D-07 | `prove_reproduction(790, 1008)` passes; any miss HALTS with the ratio-0.0 / declared-differences message | unit, both branches | `pytest tests/test_phase25_prereg.py -k reproduction -x` | ❌ W0 |
| CTRL-01 / D-04 | tripwire fires if any later plan asserts σ=0 ≡ seam-off bit-identity | structural (AST) | `pytest tests/test_phase25_prereg.py -k bit_identity_tripwire -x` | ❌ W0 |
| FRONT-01 / D-17 | `epsilon_for(SIGMA_LADDER[i], STEP_BUDGET, DELTA) == EPSILON_LADDER[i]` exact `==`; ladder len == `SWEEP_POINTS` | unit | `pytest tests/test_phase25_grid.py -x` | ❌ W0 |
| FRONT-01 / D-17,24 | budget register completeness after adding σ and C | structural (AST, hard `==`) | `pytest tests/test_phase23_budget.py::test_z_was_sized_against_the_ceiling -x` | ✅ **exists, goes naturally RED** (`:1352-1365`) |
| FRONT-01 / D-24 | `C` re-derives from the committed per-record-norm measurement | unit | `pytest tests/test_phase25_grid.py -k clip_norm_re_derives -x` | ❌ W0 |
| FRONT-02 / D-30 | no `print`/f-string/`.format`/`%` over a committed ε-name set outside the helper | structural (**AST, never grep**) | `pytest tests/test_phase25_epsilon.py -x` | ❌ W0 |
| FRONT-02 / D-28 | both multiplicities named — 262.9437465865647 and 207.0180229382851, neither hidden | structural (`_prose.normalized`) | `pytest tests/test_phase25_record.py -k multiplicity -x` | ❌ W0 |
| FRONT-03 / D-31 | ordered `point_keys` hard equality on write; `accounting: null` on the adversarial arm; gate+budget sha256s inside | structural (write-time) | `pytest tests/test_phase25_record.py -x` | ❌ W0 |
| FRONT-03 / D-36 | `held_out_generalization` re-derives **exactly** from per-point A2 counts | unit | `pytest tests/test_phase25_record.py -k held_out -x` | ❌ W0 |
| FRONT-03 / D-33 | plotter imports no torch (AST + fresh interpreter) and opens only the frontier artifact | structural + subprocess | `pytest tests/test_phase25_plots.py -x` | ❌ W0 |
| FRONT-04 / D-32 | `_CAPACITY_DISPATCH[(False,False)] == "null-at-both-capacities"` through a real call; `exists_clearing_point` carries its denominator | unit | `pytest tests/test_phase25_verdict.py -x` | ❌ W0 |
| FRONT-04 / D-23 | `capacity_comparison` never called with an adversarial point; the absent adversarial capacity rule stated **in the artifact** | structural (AST + record key) | `pytest tests/test_phase25_verdict.py -k dp_only -x` | ❌ W0 |
| D-25 | driver `_prove`s `clip_norm` equality **before** the gate call | unit (refusal) | `pytest tests/test_phase25_verdict.py -k clip_norm_equality -x` | ❌ W0 |
| D-34 | any of the 5 live-read mechanism fields diverging halts the sweep | unit ×5 | `pytest tests/test_phase25_driver.py -k mechanism -x` | ❌ W0 |
| D-09 | complete shape skipped on restart; incomplete one redrawn; the write is **atomic** | unit | `pytest tests/test_phase25_driver.py -k resume -x` | ❌ W0 |
| D-10 | a point with a committed record is refused a second attempt; message names **Phase 25's** glob | unit (refusal) | `pytest tests/test_phase25_prereg.py -k one_attempt -x` | ❌ W0 — must NOT reuse `phase23_matched_prereg.prove_first_attempt` (§C6) |
| **§O1** | driver's executable git action set is exactly `{add, commit}` over the point-record path | structural (**AST over the driver**) | `pytest tests/test_phase25_driver.py -k git_surface -x` | ❌ W0 |
| D-16 | watcher writes a stall record and does **not** kill/restart/clean | unit (both halves) | `pytest tests/test_phase25_watch.py -x` | ❌ W0 |
| ADVT-01 / D-41 | WR-01 negative/NaN ratio refused on **both** branches; WR-04 replay+adversarial refused on the flat branch; WR-06 one pool read; WR-08 bins written **after** the proofs | unit ×4 (refusals) | `pytest tests/test_phase25_wr.py -x` | ❌ W0 |
| D-39 | every adversarial point carries a refusal column **in counts**, **outside** the three-condition gate | structural | `pytest tests/test_phase25_record.py -k refusal -x` | ❌ W0 |
| D-42 | X imported by object identity; `tolerance_report` renders **ZERO TOLERANCE** into (a)'s reason; the 5-seed X is refused | unit | `pytest tests/test_phase25_verdict.py -k tolerance -x` | ❌ W0 |
| RPT-02 / D-02,19 | three dated continuations, each bounded by exactly one sentinel pair, matched through `_prose.normalized`, original claim still standing | structural ×3 | `pytest tests/test_phase25_correction.py -x` | ❌ W0 — copies `test_phase24_correction.py`'s four mechanics |
| D-44 | MPS legs skip with a reason naming the sweep when the env var is set; skip count exact | unit | `SWEEP_ACTIVE=1 pytest tests/test_phase25_venue.py -x` | ❌ W0 |
| D-13 | the `pmset` revert is a committed, verifiable step | structural | `pytest tests/test_phase25_venue.py -k pmset -x` | ❌ W0 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase25_prereg.py` — `prove_reproduction` (both branches), the D-04 tripwire, Phase 25's **own** one-attempt rule
- [ ] `tests/test_phase25_grid.py` — σ↔ε correspondence under exact `==`, `C`'s re-derivation, covering test using **attribute access** (the AST walk collects `ast.Attribute.attr` only)
- [ ] Register `SIGMA_LADDER` / `CLIP_NORM` in `tests/test_phase23_budget.py::_POST_23_13_CONSTANTS` — **after** watching the natural RED
- [ ] `tests/test_phase25_epsilon.py` — D-30's AST gate, demonstrated grep-RED / AST-GREEN on `scripts/mitigation_gate.py`
- [ ] `tests/test_phase25_record.py` — `point_keys` ordering, `accounting: null`, sha256 carriage, D-36 re-derivation, D-39 refusal counts, D-28 dual multiplicity
- [ ] `tests/test_phase25_verdict.py` — null branch, DP-only scoping, `clip_norm` caller-side equality, D-42's zero-tolerance sentence
- [ ] `tests/test_phase25_driver.py` — D-34's five halts, D-09's resume + **atomic write**, **§O1's git-surface AST gate**
- [ ] `tests/test_phase25_watch.py` — heartbeat + detect-never-act watcher, both halves watched
- [ ] `tests/test_phase25_wr.py` — WR-01 / WR-04 / WR-06 / WR-08 refusals, each watched RED
- [ ] `tests/test_phase25_plots.py` — retargeted figure guard (ports `test_phase15_plots.py:291-352` + new allow-list clause)
- [ ] `tests/test_phase25_correction.py` — three sentinel-bounded continuations through `_prose.normalized`
- [ ] `tests/test_phase25_venue.py` — D-44's sweep-active skip (count **and** reason text), D-13's revert
- [ ] `tests/conftest.py` — the `--sweep-active` option / env var read
- [ ] Framework install: **none**. pytest 8.x, ruff and the venv are present and green at 1647/1

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|---|---|---|---|
| `sudo pmset -a sleep 0 disksleep 0 powernap 0` applied, then **reverted** to `sleep 1 / disksleep 10 / powernap 1` | D-13 | requires `sudo`; not reachable from pytest | Apply before launch; `pmset -g` read back and the line recorded in the dated operational note. The revert is a **committed plan step**, verifiable, never dependent on human memory |
| the five stray `caffeinate` assertions cleared; the run's own `caffeinate -dims` is the ONLY non-system assertion | D-43 | inspects live process state | `pmset -g` read back **after** launch, that line recorded in the operational note |
| LaunchAgent loaded, `KeepAlive` FALSE, survives session end / logout | D-12 | requires a real logout cycle | `launchctl print` the agent; confirm `KeepAlive = false`; verify stdout/stderr file grows across a session boundary |

---

## Two Failure Modes This Contract Exists To Catch

1. **A structural fact discovered by spending GPU hours.** Every invariant here has a millisecond CPU
   proxy and all of them belong in Wave 0. Measured precedent: 24-07 converted a post-compute
   `SystemExit` into a 2.2-second CPU test.
2. **A contention failure read as a genuine one.** During a 4.5–6.3 day sweep the 47 MPS-parametrized
   node ids run and contend. D-44's skip must be **loud** — named reason, stated skip count — because
   the silent version is indistinguishable from the MPS legs having been quietly lost, which
   `23-VALIDATION.md` already names as Pitfall 1.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all ❌ MISSING references above
- [ ] No watch-mode flags
- [ ] Feedback latency < 30 s per task; stall detection N = 5 min during the run
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
