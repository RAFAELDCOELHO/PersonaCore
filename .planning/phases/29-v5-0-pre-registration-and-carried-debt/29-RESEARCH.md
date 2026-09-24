# Phase 29: v5.0 Pre-Registration and Carried Debt - Research

**Researched:** 2026-09-24 (git HEAD `ffa0f19`)
**Domain:** In-repo pre-registration machinery (stdlib Python + git ancestry guards), plus four debt closures
**Confidence:** HIGH. Every name, path, line and behaviour below was read from source or measured with `.venv/bin/python` (3.11.15) at `ffa0f19`. The only exceptions are marked `[ASSUMED]`.

## Summary

Phase 29 adds no packages and no MPS time. The work is one new CPU-only module, `scripts/phase29_prereg.py`, plus `tests/test_phase29_prereg.py`. Both copy the `phase27_prereg.py` / `test_phase27_prereg.py` pattern: `_prove` raises `SystemExit`, `COMMITTED`, `RECORDS_AT_COMMIT = 0`, an artifact-glob constant, lazy torch imports, by-reference constants asserted with `is`, and `_assert_frozen_before`. The four debt items are then closed with small, local edits.

Four findings change the plan compared with CONTEXT.md.

**(1) D-01 cannot go through `phase25_record.point_key` directly.** Measured: `point_key("advr_n8", 0.25)` raises `SystemExit` because `AXIS_FOR_ARM` has no `advr_*` entry. The v5.0 module has to wrap it. The cleanest wrap is `"advr" + phase25_record.point_key("adv_nX", r)[len("adv"):]`. That reuses the renderer's refusals for non-finite and negative values and its charset check. As a side effect, `phase25_record.parse_point_key` and `phase27_prereg.arm_of` both refuse `advr_*` keys, which is exactly the "no arm-keyed v4.0 reader can confuse them" property D-01 wants.

**(2) D-19's "no v5.0 module imports the accountant" cannot be a `sys.modules` test.** `phase25_record` imports `phase25_epsilon` at module level, and that loads `personacore.privacy.accountant`. Measured: importing `phase25_record` or `phase27_prereg` puts the accountant in `sys.modules`. The test has to be an AST census of direct imports and calls.

**(3) D-18's measurement recipe gives the wrong date.** `git log --diff-filter=A` on the archived Phase-17 paths returns the archive commit `16a07d8` (2026-08-20) for all 11 files. The real first-add dates (2026-08-14 and 2026-08-15) only come back with `--follow` or with the pre-archive path.

**(4) D-15, measured: GATE-08 works exactly as described, but v4.0 never built a promotion route that could be imported.** Only the promotion decision rule imports cleanly. The `phase25_promotion` module is hardwired to v4.0's 44 keys and paths. It sources the adversarial `control_gap` from the DP σ=0 record, reads the accountant's ε, and hard-codes `REPLICATED_AT_SECOND_SEED = False`. Nothing in `scripts/` performs the K=48 redraw or the second-seed replication. This friction is laid out under D-15 below for the developer's ruling.

**Primary recommendation:** The plan's first task is `checkpoint:decision` (D-15), carrying the friction table from this document. After the ruling, write `scripts/phase29_prereg.py` in one pass. Every v5.0 path goes in one tuple, and the ancestry pathspecs are derived from it. The gate, grid and replay recipe are imported by reference, with AST guards. Then close DEBT-01..04 with the local edits specified below. No frozen v4.0 module is edited.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Keys, paths, and the imports (PREREG-01, PREREG-04)
- **D-01:** The 12 v5.0 keys use NEW ARM NAMES (`advr_n8`, `advr_n64`) through the existing
  `phase25_record.point_key(arm, value)` over the frozen `ADVERSARIAL_RATIO_GRID` — e.g.
  `advr_n8_ratio0p250000`. The key itself differs from v4.0's `adv_*`, not only the file path, so
  no arm-keyed reader can confuse a v4.0 and a v5.0 point. Point records live at
  `results/phase32_point_<key>.json`. (Researcher: verify `point_key` / `ADVERSARIAL_ARMS` accept
  a new arm without editing a frozen v4.0 module; if not, the v5.0 module wraps it, never edits it.)
- **D-02:** The ancestry guard covers EVERY v5.0 results file — `results/phase3[0-4]_*`, including
  Phase 30's calibration and Phase 31's probe records — matching SC1's "precedes every v5.0
  results artifact" literally.
- **D-03:** EVERY v5.0 results path is pinned in this module now (points, promotion records if
  any, frontier, admission, Phase 30 calibration, Phase 31 probes). The guard glob is derived from
  that one list, not typed separately, and a test proves no probe/calibration path parses as a
  point key (ARCAL SC4).
- **D-04:** `REPLAY_WINDOWS_PER_FACT` is imported LAZILY: a `replay_windows(n)` function imports
  `teach_persona` only when called (the `phase27_prereg.attacker_corpus_rows` precedent), so the
  module stays torch-free at import. An AST guard reddens if a numeric literal equal to the
  constant, or a module-level assignment of that name, appears in the pre-registration. Replay =
  `REPLAY_WINDOWS_PER_FACT`·n windows from `data/dialog_train.bin`, identical to the DP arms.
- **D-05:** The frozen v4.0 gate is imported as the sanctioned ROUTE,
  `phase20_gate_coverage.corrected_point_verdict` — never `mitigation_gate.mitigation_point_verdict`
  directly (the caller census in `tests/test_phase20_correction.py` forbids that from `scripts/`).
  An AST guard reddens if the gate or the grid is re-typed.

#### Admission contract (PREREG-02) — frozen in full NOW
- **D-06:** Phase 29 freezes the WHOLE admission contract as code; Phase 33's ADMIT module only
  imports it and calls it once. Nothing about admission is decided after the v5.0 frontier exists.
  Contract: expected point count 12; ADMITTED iff ≥1 stored PASS (naming every PASS key in key
  order); INCONCLUSIVE (malformed record / counts that do not re-derive) takes precedence;
  threshold = `F_Y` × the taught-recall COUNTS of the arm's OWN `advr` ratio-0 control at that
  capacity — never a `dp_*` reading (WR-05).
- **D-07:** New 4th admission verdict **REFUSED**: when EVERY point is REFUSED, admission reads
  REFUSED — never MOOT — carrying each leg's control reading. Relearning then ships as a named
  limitation whose reason is "the frontier could not be measured", never "the mitigation held".
  INCONCLUSIVE keeps its narrow meaning (malformed / non-re-deriving record).
- **D-08:** Mixed case (one leg REFUSED, the other measured with zero PASS) reads **MOOT**, with the
  reasons naming the refused leg and its reading; the report never extends MOOT to the refused
  capacity.
- **D-09:** Relearning parameters for any admitted point (rungs, band, K, the seven baselines,
  attacker corpus, recovery fixture) are IMPORTED from `phase27_prereg` unchanged — frozen before
  any data and never run. v5.0 changes only the arm key and the control source.
- **D-10:** The scope rule itself: every admitted point runs RELRN-06..09; zero admitted ⇒
  RELRN-06..09 ship as a MOOT (or, per D-07, REFUSED) named limitation. Which branch runs is the
  admission record's output.

#### Unlearnable own-control refusal (PREREG-03)
- **D-11:** The refusal is the route's existing precondition: `control_taught_recall` or
  `control_heldout_recall` of the leg's `advr` ratio-0 control outside (0,1] ⇒ the whole capacity
  leg is REFUSED (every point in the leg sources its floors from that control).
- **D-12:** SHORT-CIRCUIT: the control runs first (ACTRL-02); if it comes back outside (0,1], the
  leg's other 5 points are NOT trained — each key gets a write-once REFUSED record citing the
  control's reading. Phase 31's budget must cover both branches.
- **D-13:** The REFUSED record carries: the control's taught and held-out recall as k/n COUNTS
  (never bare rates), the recipe identity (replay windows, n, seed, budget), and the v4.0 `adv_n64`
  reading beside it (held-out 0/648) so the report can say whether replay moved the floor.
- **D-14:** "Not re-tuned" is enforced structurally: the 12 keys are the complete set, write-once,
  with no alternate/retry key — a test reddens if the pre-registration exposes one. A different
  recipe needs a new pre-registration in a new milestone. (Phase 30's ARECIPE-02 already refuses a
  point whose recipe differs from the calibration's.)

#### GATE-08 — RULING CHECKPOINT (premise gap found in discussion)
- **D-15:** The frozen gate (`mitigation_gate.py:822`, GATE-08 / D-29) returns INCONCLUSIVE — not
  PASS — for a point clearing (a)(b)(c) without second-seed replication; v4.0 set
  `REPLICATED_AT_SECOND_SEED = False` and made promotion (`phase25_promotion`, K=48 redraw +
  second-seed replication) the only path to PASS. The v5.0 roadmap has no promotion step, so under
  D-06 v5.0 could never admit. **Developer ruling: the researcher MUST confirm that GATE-08 and
  `phase25_promotion` work as described, and that the promotion route can genuinely be imported for
  the `advr` arms — without structural modification and without a hidden dependency on the `dp_*`
  arms that does not generalise. The plan STOPS at a checkpoint for the developer's decision with
  that confirmation in hand.** If the route imports cleanly, option 1 (pre-register promotion:
  candidates promoted through the imported v4.0 route under their own write-once promotion keys,
  budgeted in Phase 31, run in Phase 32, admission reading the promoted verdicts) is the natural
  answer. If there is real import friction, the choice between 1 (adapt promotion) and 2 (no
  promotion; a would-be PASS stays INCONCLUSIVE and admission gets a distinct
  candidate-unreplicated reading, never MOOT, shipped as a named limitation) is made with the
  friction visible, not assumed. Nothing D-15-dependent may be committed to the pre-registration
  before that ruling.

#### Carried debt (DEBT-01..04)
- **D-16 (DEBT-01):** the relearn test monkeypatches `relearn._ROOT` to a scratch repository (the
  27-REVIEW IN-07 prescription); a guard proves no `results/phase27_*` file is touched.
- **D-17 (DEBT-02):** keep published bytes. A `d28_note()` reader in `arm_d_qualifier()`'s shape
  reads the D-28 READING QUALIFICATION blockquote from 16-CONTEXT.md at runtime; a test compares it
  to what the code/report carry, so an amended note reddens. No frozen report block is re-rendered.
  If the published text lacks the verbatim note, the test records that as a named limitation rather
  than rewriting history.
- **D-18 (DEBT-03):** backfill all 11 archived Phase-17 SUMMARYs: `completed` = the author date of
  each SUMMARY's first-add commit (`git log --diff-filter=A`), measured; `duration` = an explicit
  "not recorded at the time" value the validator accepts — no invented number. Researcher: verify
  no guard/pin/content test reads those SUMMARY bytes before editing archived files.
- **D-19 (DEBT-04):** P22-WARNING-4/5 is re-recorded as a committed named-limitation entry in the
  v5.0 pre-registration module (reason: no v5.0 number uses the accountant; the adversarial arm
  carries no ε claim, Phase 25 D-01), ancestry-guarded ahead of every number, with a test that no
  v5.0 module imports the accountant. Zero change to the accountant; Phase 34 renders the entry.
  `results/phase28_ledger.json` is frozen and not touched.

### Claude's Discretion
- Module name/layout (one module vs. a split admission submodule), test file names, the exact
  AST-guard mechanics, and DEBT-01's scratch-repo fixture shape — follow the phase26/27 prereg
  register.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (D-15 may add a promotion leg to Phases 31/32 depending
on the ruling; that is an application of the frozen gate, not a new capability.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PREREG-01 | v5.0 prereg module, ancestry-guarded, fixes new point keys over the frozen grid, the record paths and the frozen gate (imported) | §Keys (the wrap is needed: measured refusal), §Paths, §Ancestry guard, §AST guards |
| PREREG-02 | Conditional scope rule committed before any point runs | §Admission contract (4 verdicts; the frontier schema it reads is pinned now) |
| PREREG-03 | Unlearnable own control ⇒ REFUSED with its reading, no re-tune | §Refusal predicate (equivalent to `k == 0` for rates; differential test against the route), v4.0 reading measured at `adv_n64` taught 1/1008, held-out 0/648 |
| PREREG-04 | Replay = `REPLAY_WINDOWS_PER_FACT`·n windows from `data/dialog_train.bin`, imported | §Replay recipe (DP expression `replay_window_budget(n) // BLOCK_SIZE` at `teach_persona.py:1970`) |
| DEBT-01 | Relearn test writes under a scratch `relearn._ROOT` | §DEBT-01 (the test is at `tests/test_phase27_relearn.py:182-194`; reuse `_real_tree_strays()`) |
| DEBT-02 | D-28 note read verbatim at runtime; an amendment reddens | §DEBT-02 (note sha256 measured; the verbatim note is ABSENT from the published report, so it becomes a named limitation) |
| DEBT-03 | Archived Phase-17 SUMMARY frontmatter validates | §DEBT-03 (the validator checks key presence only; the date table is measured with `--follow`) |
| DEBT-04 | P22-WARNING-4/5 re-recorded as a named limitation | §DEBT-04 (direct-import AST census; a transitive accountant import is unavoidable and must be stated) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 venv only (`.venv/bin/python`, 3.11.15 measured). Never validate against the system 3.14.
- Tests are CPU-only, need no GPU and must pass on a fresh clone with `pip install -e ".[cpu,dev,demo]"`.
- No new dependencies. Stdlib plus sibling `scripts/` modules only. Torch may be imported lazily inside functions, never at module import time.
- Offline logging only. No network.
- Work goes through the GSD workflow. STATE, ROADMAP and REQUIREMENTS are edited by hand (snapshot, then diff). No `gsd-sdk` mutation handlers.
- Milestone-close inputs are frozen: REQUIREMENTS, ROADMAP and research are live inputs to `phase28_report`. Only append; never touch anything above the v5.0 rule.
- Never commit secrets.
- Global user instruction: durable results are logged to the Obsidian vault. The executor or orchestrator records the phase outcome there. This research note does not.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Point keys, paths, recipe, scope rule, admission contract | `scripts/phase29_prereg.py` (stdlib, torch-free at import) | — | The pre-registration is data plus pure functions, frozen by ancestry |
| Freeze-before-results proof | `tests/test_phase29_prereg.py` (git subprocess) | CI `fetch-depth: 0` | Ancestry needs the full history |
| Gate verdict | `phase20_gate_coverage.corrected_point_verdict` (frozen, imported) | `mitigation_gate` constants | The sanctioned route; the caller census forbids calling the pin directly |
| Replay volume | `teach_persona.replay_window_budget` (torch module, lazy) | — | The only site that computes it (its docstring says so) |
| DEBT-01 | `tests/test_phase27_relearn.py` only | — | `scripts/phase27_relearn.py` is in its own `PINNED_MODULES`, so it cannot be edited |
| DEBT-02 | `scripts/phase16_persistence.py` (reader) + `tests/test_phase16_driver.py` | the prereg's limitation entry | Not ancestry-guarded (ledger TD-16-R1 evidence); the reader sits beside `arm_d_qualifier` |
| DEBT-03 | 11 archived `.md` frontmatters, hand-edited | a pytest mirroring the validator | The validator is `~/.claude/get-shit-done/bin/lib/frontmatter.cjs:315` |
| DEBT-04 | Limitation entry in the prereg | AST census test | Zero accountant change |

## Standard Stack

No external packages are added. The "stack" is the set of in-repo modules below. Every one was verified by reading source at `ffa0f19`.

### Core (import by reference, never re-type)
| Symbol | Real location | Value / behaviour (measured) |
|---|---|---|
| `ADVERSARIAL_RATIO_GRID` | `scripts/mitigation_budget.py:633` | `(0.0, 0.25, 0.5, 1.0, 1.5, 1.9090909090909092)` |
| `REPLAY_WINDOWS_PER_FACT` | `scripts/teach_persona.py:179` | `4` (torch at import, so load it lazily) |
| `replay_window_budget(n_facts, block_size=BLOCK_SIZE)` | `teach_persona.py:182` | Returns TOKENS: `4·n·256`. DP call site: `replay_windows=replay_window_budget(stats["n_facts"]) // BLOCK_SIZE`, `replay_bin=DIALOG_TRAIN_BIN`, `replay_mask_bin=DIALOG_TRAIN_MASK` (`teach_persona.py:1968-1970`). n8 → 32 windows, n64 → 256 (matches `logs/phase25_sweep.out:14,70`, quoted in `phase25_promotion.ADVERSARIAL_NO_REPLAY`) |
| `DIALOG_TRAIN_BIN` / `DIALOG_TRAIN_MASK` | `teach_persona.py:99-100` | `data/dialog_train.bin`, `data/dialog_train_mask.bin` |
| `corrected_point_verdict` | `scripts/phase20_gate_coverage.py:522` | 24 kwargs. Recall-floor precondition `0.0 < F_Y·control_* <= 1.0` at `:641-647` |
| `mitigation_point_verdict` | `scripts/mitigation_gate.py:637` | 21 kwargs. GATE-08 at `:822-829`. **Never call or import it by name from `scripts/`** (census at `tests/test_phase20_correction.py:1377`) |
| `F_Y`, `V4_VERDICTS`, `ARMS`, `REPLICATION_PENDING_MARKER`, `promote_to_full_fidelity`, `ratchet_k` | `mitigation_gate.py:203, 85, 156, 149, 963, 917` | `0.7`; `("PASS","FAIL","INCONCLUSIVE")`; `("dp","adversarial")` |
| `point_key`, `parse_point_key`, `ADVERSARIAL_ARMS`, `AXIS_FOR_ARM` | `scripts/phase25_record.py:215, 253, 159, 162` | `ADVERSARIAL_ARMS = ("adv_n8","adv_n64")`. `point_key("advr_n8", …)` REFUSES (measured) |
| `point_record_path` (charset rule) | `scripts/phase25_prereg.py:276` | `[A-Za-z0-9_-]` only; prefix hard-coded `results/phase25_point_`, so do **not** use it for v5.0 paths |
| `COVERAGE_FLOOR_REFUSAL_MARKERS` | `scripts/phase25_promotion.py:53` | The two substrings of the route's floor refusal |
| Relearning pins | `scripts/phase27_prereg.py` | `RUNGS`, `RELEARN_CAP`, `MAX_STEPS`, `CHECKPOINT_INTERVAL`, `DESIGNATED_SEED`, `FRESH_SEEDS`, `POOLED_SEED_INDEX`, `PINNED_BASELINES` (7), `ATTACKER_CORPUS`, `first_clear`, `z_rule`, `band`, `recovery_gate`, `promote_at_z`, `point_verdict_string`, `cleared_abc` |
| Frontier record | `phase25_record.FRONTIER_RECORD` | `results/phase25_frontier.json` (22 MB, one commit; never load at import) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|---|---|---|
| Wrapping `point_key` | Adding `advr_*` to `phase25_record.AXIS_FOR_ARM` | Forbidden: `phase25_record` is frozen v4.0 input |
| Lazy `teach_persona` import | AST-reading the literal via `phase25_gate05._committed_literal("teach_persona", "REPLAY_WINDOWS_PER_FACT")` | Torch-free and already used by `phase25_verdict.py:120`, but it reads a number and not the function DP actually calls. D-04 locks the lazy import |
| Copying `_assert_frozen_before` into the new test | Importing it from `test_phase27_prereg` | Both phase26 and phase27 tests copy it; follow the copy precedent |

## Package Legitimacy Audit

Not applicable. This phase installs no external packages, so slopcheck was not run and nothing needs gating.

## Architecture Patterns

### Data flow (what Phase 29 freezes, and who consumes it)

```
frozen v4.0 inputs (import only) ─────────────────────────────────────────────┐
  mitigation_budget.ADVERSARIAL_RATIO_GRID   teach_persona.replay_window_budget │ (lazy)
  phase20_gate_coverage.corrected_point_verdict   phase27_prereg relearning pins │
                                                                                ▼
                         scripts/phase29_prereg.py  (committed before any results/phase3[0-4]_*)
        ┌──────────────┬─────────────────┬──────────────────┬──────────────────────────┐
        ▼              ▼                 ▼                  ▼                          ▼
  12 POINT_KEYS   V5_RESULT_PATHS   replay_windows(n)   control_is_unlearnable()   admission contract
  (advr_*)        (one tuple) ──►   32 / 256 windows    ⇒ REFUSED record shape     ADMITTED/MOOT/
        │         ARTIFACT_PATHSPECS                     (D-12 short-circuit)       INCONCLUSIVE/REFUSED
        ▼              │                                                            + scope rule
  Phase 30 train seam  ▼                                                                  │
  Phase 32 sweep ─► results/phase32_point_<key>.json ─► v5.0 frontier ─► Phase 33 admit ◄─┘
                        (ancestry test: every prereg commit is a strict ancestor of each first-add)
```

### Recommended layout
```
scripts/phase29_prereg.py     # ONE module (split only if it grows past ~600 lines, which phase27's register already reaches)
tests/test_phase29_prereg.py  # ancestry, by-reference `is`, AST guards, keys/paths, refusal, admission, DEBT-04 census, DEBT-03 frontmatter
tests/test_phase27_relearn.py # DEBT-01 edit: the probe test only
scripts/phase16_persistence.py + tests/test_phase16_driver.py   # DEBT-02
.planning/milestones/v3.0-phases/17-multi-persona-isolation-matrix/17-{01..11}-SUMMARY.md  # DEBT-03
```

### Pattern 1: Keys by wrapping, never editing (D-01)
```python
# scripts/phase29_prereg.py — reuse the v4.0 renderer's finite/negative/charset refusals
V5_ARMS = ("advr_n8", "advr_n64")
_V4_TWIN = {"advr_n8": "adv_n8", "advr_n64": "adv_n64"}   # the v4.0 arm whose axis/grammar this arm reuses

def point_key(arm, ratio):
    _prove(arm in V5_ARMS, f"arm {arm!r} is not one of {V5_ARMS}")
    twin = _V4_TWIN[arm]
    return arm + phase25_record.point_key(twin, ratio)[len(twin):]

def POINT_KEYS():   # lazy, like ORDERED_POINT_KEYS(); arm-major, grid order → control (ratio 0.0) first per leg
    return tuple(point_key(a, r) for a in V5_ARMS for r in mitigation_budget.ADVERSARIAL_RATIO_GRID)
```
Measured v4.0 rendering: `adv_n8_ratio0p000000 … adv_n8_ratio1p909091`. So the v5.0 keys are `advr_n8_ratio0p000000 … advr_n64_ratio1p909091`, 12 in total. The tests should prove four things. (a) Swapping `advr` back to `adv` equals the v4.0 key for all 12. (b) `phase25_record.parse_point_key(k)` raises `SystemExit` for every v5.0 key. (c) `phase27_prereg.arm_of(k)` raises. (d) There are no duplicates.

### Pattern 2: One path tuple, derived pathspecs (D-02, D-03)
```python
POINT_RECORD_PREFIX = "results/phase32_point_"
def point_record_path(key): _prove(key in POINT_KEYS(), ...); return f"{POINT_RECORD_PREFIX}{key}.json"
V5_RESULT_PATHS = (   # every v5.0 results path/pattern, pinned now. Names are proposals: grep before Phase 30-33 use
    "results/phase30_calibration.json",          # ARECIPE-02
    "results/phase31_probe_point.json",          # ARCAL-01
    "results/phase31_probe_relearn.json",        # ARCAL-02
    "results/phase31_budget.json",               # ARCAL-03
    POINT_RECORD_PREFIX + "*.json",              # AFRONT-01 (12)
    "results/phase32_frontier.json",             # AFRONT-02
    "results/phase33_admission.json",            # ADMIT-02
    "results/phase33_*",                         # RELRN-06..09 legs (glob, since their count depends on admission)
    "results/phase34_*",                         # RPT-04 artifacts, if any
    # + promotion paths ONLY IF D-15 rules option 1
)
ARTIFACT_PATHSPECS = V5_RESULT_PATHS   # the guard reads this, typed once
```
Tests: (i) no path matches `results/phase2*` or any currently tracked file; (ii) every concrete non-point path is refused by `point_key` parsing, and `pathlib.Path(p).stem` minus `phase32_point_` is not a member of `POINT_KEYS()` (ARCAL SC4); (iii) everything sits under `results/phase3[0-4]_`, so D-02's glob covers the tuple.

`[ASSUMED]` The exact filenames for Phases 30, 31 and 33. No code names them yet. The planner and the developer fix them in this module, and later phases must import them. This is the "plans misname artifacts" hazard, closed by construction.

### Pattern 3: Ancestry guard (copy of `tests/test_phase27_prereg.py:73-120`)
`_assert_frozen_before(PREREG, tracked)` checks four things. The repo is not shallow. Every `git log --format=%H -- scripts/phase29_prereg.py` commit is `!=` and a strict ancestor (`merge-base --is-ancestor`) of `adds[-1]`, the earliest first-add of each tracked path. `checked == commits × tracked`. And `bool(checked) == bool(tracked)`. Build `tracked` from `git ls-files <each ARTIFACT_PATHSPECS entry>` (git pathspec globs, brackets included, work: measured with `results/phase2[6-7]_*`). Today it tracks 0 paths, so the test is honest-green with zero pairs. **Every Phase-29 edit of the prereg is legal until the first `results/phase3*` commit (Phase 30 ARECIPE-02). After that the module is frozen and corrections go through `scripts/_addendum.py` as dated continuations.**

### Pattern 4: Lazy replay recipe (D-04)
```python
def replay_windows(n_facts):
    import teach_persona  # LAZY — torch at import (phase27_prereg.attacker_corpus_rows precedent)
    windows = teach_persona.replay_window_budget(n_facts) // teach_persona.BLOCK_SIZE
    _prove(windows == teach_persona.REPLAY_WINDOWS_PER_FACT * int(n_facts), "...")
    return windows
REPLAY_SOURCE = ("teach_persona.DIALOG_TRAIN_BIN", "teach_persona.DIALOG_TRAIN_MASK")  # names, not paths
```
This calls the same expression the DP arms use (`teach_persona.py:1970`). A torch-free import probe, the `test_the_prereg_imports_without_torch` shape, must print `False False` for `torch` and `teach_persona`.

### Pattern 5: AST guards (not grep; see the hazard notes)
Scan with `ast.parse(scripts/phase29_prereg.py)`:
- **Replay constant:** no `ast.Constant` with `type(value) in (int, float)` whose value `== teach_persona.REPLAY_WINDOWS_PER_FACT` (4; note `4.0 == 4`). No module-level `Assign`/`AnnAssign` target named `REPLAY_WINDOWS_PER_FACT`. **Consequence: the module must contain no literal `4` at all.** Write `len(VERDICTS)` instead of 4, and avoid `4` in any `range`/slice.
- **Grid:** no `Tuple`/`List` whose constant elements equal `ADVERSARIAL_RATIO_GRID`, no float constant `1.9090909090909092`, and no module-level target named `ADVERSARIAL_RATIO_GRID` unless its value is the `Attribute` `mitigation_budget.ADVERSARIAL_RATIO_GRID`.
- **Gate:** no float constant `0.7` (`F_Y`), no `FunctionDef` named `mitigation_point_verdict` / `corrected_point_verdict` / `cleared_abc`, and no import or call of `mitigation_point_verdict` (the phase20 census already enforces this repo-wide). By-reference checks: `phase29_prereg.GATE_ROUTE is phase20_gate_coverage.corrected_point_verdict`, `F_Y is mitigation_gate.F_Y`, `RATIO_GRID is mitigation_budget.ADVERSARIAL_RATIO_GRID`.
- Mutation-prove each guard RED→GREEN on a copied source string in the test. Never plant it in the real file (memory: natural RED beats planted RED).

### Pattern 6: Refusal predicate (D-11, D-12, D-13)
```python
def control_is_unlearnable(taught_k, taught_n, heldout_k, heldout_n):
    # the route's own inequality (phase20_gate_coverage.py:641-647) on COUNTS; F_Y by reference
    ...counts proved int-not-bool, 0<=k<=n, n>0...
    return not all(0.0 < F_Y * (k / n) <= 1.0 for k, n in ((taught_k, taught_n), (heldout_k, heldout_n)))
```
For recall rates in [0,1] with `F_Y = 0.7`, this is equivalent to "either k == 0". Add a **differential test** against the route: with a zero control count, `corrected_point_verdict` raises `SystemExit` containing both `COVERAGE_FLOOR_REFUSAL_MARKERS`; with a count of 1, it does not refuse on the floor. That ties the restated inequality to the route. Pin `V4_ADV_N64_READING = {"taught": (1, 1008), "heldout": (0, 648), "source": "results/phase25_frontier.json::verdicts.control_readings.adv_n64.recall_counts"}` and have a test re-read it from the frontier. Measured: `adv_n64` taught `[1, 1008]`, held-out `[0, 648]`. For reference, `adv_n8` measured `[879, 1008]` / `[482, 648]`. `REFUSED_RECORD_FIELDS` is a tuple naming what the Phase-32 REFUSED record carries: `point_key`, `control_key`, `control_recall_counts{taught,heldout}`, `recipe{replay_windows,n_facts,seed,max_steps}`, `v4_adv_n64_reading`, `rule="PREREG-03"`.

### Pattern 7: Admission contract (D-06..D-10), pure over a frontier dict
- `EXPECTED_POINTS = 12`, derived as `len(V5_ARMS) * len(ADVERSARIAL_RATIO_GRID)`, not a literal. `VERDICTS = ("ADMITTED", "MOOT", "INCONCLUSIVE", "REFUSED")`, plus the D-15-dependent reading if option 2 is chosen.
- `CONTROL_KEYS = {"n8": point_key("advr_n8", GRID[0]), "n64": point_key("advr_n64", GRID[0])}` sources the recall floors, `control_gap` and the relearning control (WR-05).
- **Pin the frontier schema the contract reads now**, since Phase 32 must emit it. Reuse v4.0's shape so `phase27_prereg.point_verdict_string` and `cleared_abc` apply unchanged: `point_keys`, `points[k].verdict.{verdict, early_return_reason, <route kwargs>}`, `verdicts.{tallies, tallies_by_leg, control_readings[<leg>].recall_counts.{taught,heldout}}`. Leg names are `advr_n8`/`advr_n64` (`key.rsplit("_",1)[0]` works).
- Precedence: INCONCLUSIVE (absent frontier, count ≠ 12, a string outside the tally names, or tallies that do not re-derive) comes first. Then ADMITTED (≥1 PASS, keys in `POINT_KEYS()` order). Then REFUSED (every point REFUSED). Then MOOT (the reasons name any refused leg with its counts, per D-08).
- `recall_threshold(frontier, leg)` returns `F_Y·k/n` with `(k, n)` from `control_readings[f"advr_{leg}"]`. **Never touch `phase27_prereg.recall_threshold`**, which hard-reads `dp_{leg}`.
- Test all four branches on forged dicts. There is no v5.0 frontier yet, so build the fixture in the test (a minimal 12-point dict). Do not deepcopy the 22 MB v4.0 file.

### Anti-Patterns to Avoid
- Calling `phase27_prereg.recall_threshold`, `extraction_ceiling_x`, `arm_of` or `relearning_is_worth_attempting` on v5.0 data. They hard-code `dp_*` `CONTROL_KEYS`, `EXPECTED_POINTS = 44` and `ORDERED_POINT_KEYS()`.
- Loading `results/phase25_frontier.json` at import time (22 MB). Pin counts, and re-read them in tests.
- Any `results/phase3*` file written during Phase 29, including test probes. It would start the ancestry clock early.
- Editing `phase25_record.py`, `phase25_promotion.py`, `phase27_prereg.py`, `phase27_relearn.py`, `mitigation_gate.py` or `phase20_gate_coverage.py`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Key rendering / charset / finite checks | A new f-string grammar | Wrapped `phase25_record.point_key` | It carries the WR-01 refusals, and one grammar governs both key sets |
| Verdict | Condition functions | `phase20_gate_coverage.corrected_point_verdict` | Sanctioned; census-enforced |
| Replay volume | `4 * n` | `teach_persona.replay_window_budget(n) // BLOCK_SIZE` | The only site; the same expression DP uses |
| Z, band, rungs, recovery gate | New relearning rules | `phase27_prereg.*` by reference | D-09 |
| Atomic JSON writes (in later phases) | `os.replace` | `phase25_run.atomic_write_json` | Census `tests/test_phase25_driver.py:359` allows `os.replace` only in `phase25_run.py` and `phase25_record.py` |
| Continuation after freezing | Editing the prereg | `scripts/_addendum.py` + a tripwire | The ancestry guard stays red forever otherwise |

## D-15 — GATE-08 and the promotion route: the confirmation the ruling needs

**Confirmed, by measurement.** `corrected_point_verdict(**FIXTURE_CLEARING_POINT route kwargs, replicated_at_second_seed=True)` returns `PASS`. The same call with `False` returns `INCONCLUSIVE`, with the last reason opening `"clears all three conditions, replication pending (GATE-08 / D-29)"`. `promote_to_full_fidelity` promotes both (`True`). The route passes GATE-08 through untouched (`phase20_gate_coverage.py:660-683`). **So under the frozen route, and without a replication input, no v5.0 point can ever read PASS, and a D-06 "≥1 PASS" admission can never fire.** The `arm` kwarg only labels the claim class; `"adversarial"` behaves identically.

**What "the promotion route" actually is in v4.0 (read from source):**

| Piece | Where | Imports cleanly for `advr`? | Friction |
|---|---|---|---|
| Promotion DECISION `promote_to_full_fidelity(verdict, reasons, curve_k, full_k)` + `ratchet_k` | `mitigation_gate.py:963, 917` | **Yes.** Pure and arm-agnostic. K comes from `mitigation_budget.CURVE_K` / `FULL_FIDELITY_K` (16 → 48) | None |
| `PROMOTION_RULE` text (curve first, then promote all, replicate at second seed at FULL_K, tail rule) | `phase25_prereg.py:360` | Yes, by reference, as a rule statement | It never says whether the **control** is re-trained at the second seed, or which second seed. Both are new decisions `[open]` |
| `phase25_promotion` module (`point_records`, `control_readings`, `curve_pass`, `build`) | `scripts/phase25_promotion.py` | **No** | Hardwired to `phase25_record.ORDERED_POINT_KEYS()` (44 v4.0 keys) and `results/phase25_point_*`/`phase25_recall.json`. `control_readings` takes the adversarial `control_gap` from **`dp_n{cap}_sigma0` records** (D-47), a hidden DP dependency that contradicts ACTRL-01/WR-05. `build()` reads `records["dp_n8_sigma0p500000"]["epsilon"]` (an accountant ε, which DEBT-04 says no v5.0 number uses) and `capacity_branches` over the DP `SIGMA_LADDER`. It writes the fixed `results/phase25_promotion.json`. `REPLICATED_AT_SECOND_SEED = False` is a module constant stamped into every point |
| `phase25_verdict.curve_verdicts(records, arm, capacity, control_readings_by_arm=)` | `scripts/phase25_verdict.py:504` | Partially | `ARM_LEGS` is read from the **committed literal `teach_persona.ADV_ARMS`** (`phase25_verdict.py:121`). An `advr` leg is resolved as `adv_n{cap}`, so v5.0 data would travel under a v4.0 leg label. **If Phase 30 appends `advr_*` to `teach_persona.ADV_ARMS`, `curve_verdicts` refuses ("matches two legs")**, so Phase 30 must add a separate tuple |
| EXECUTION: K=48 redraw + second-seed training + replication record | — | **Does not exist** | v4.0 had zero candidates, so tail cost was 0. No code in `scripts/` trains a point at a second seed or sets `replicated_at_second_seed=True` from a record (grep: only `mitigation_gate` fixtures). `phase25_run.load_draws` refuses reusing K=16 draws at K=48 (`k` is part of the cache identity), which is a hook but not a route. `phase25_run.run_point` keys through `phase25_record` grammar and refuses `advr_*` |

**Reading for the checkpoint.** Option 1 is not "import the v4.0 route". It is: import the decision rule, plus write new Phase-31/32 code for second-seed training, the K=48 redraw and a replication record, plus make new decisions (the second seed, e.g. `phase27_prereg.FRESH_SEEDS[1] = 2024` `[ASSUMED candidate]`; whether the ratio-0 control is also replicated; promotion keys and paths). Its cost is unmeasured: v4.0's formula was `candidates × 2 × 3 × K16 h/point`, from `results/phase23_cost.json`, a DP-era figure. Option 2 needs none of that. It adds one admission reading, e.g. `CANDIDATE-UNREPLICATED`, for "≥1 point cleared (a)(b)(c) with replication pending", identified by `REPLICATION_PENDING_MARKER` via `promote_to_full_fidelity`. It ships as a named limitation. **The friction is real on both the execution and the DP-dependency axes. Only the decision rule imports cleanly.**

**Interaction with D-14.** If option 1 is chosen, promotion keys must live in a separate namespace, for example `results/phase32_promotion_<key>_k48_seed<S>.json`. The key set must be derived from `POINT_KEYS()` and must not parse as a point key. The D-14 "no alternate/retry key" test then has to state that promotion keys are replications of the same key at pinned seed and K, not retries. Otherwise that test and option 1 contradict each other.

## Carried debt: current exact state

### DEBT-01 (IN-07): open
- The offender is `tests/test_phase27_relearn.py:182-194` (`test_a_leg_refuses_an_untracked_record_inside_the_repo`). It writes `results/phase27_admission_probe_never_committed.json` into the real repo and unlinks it in a `finally`.
- `relearn._require_admitted` (`scripts/phase27_relearn.py:128-170`) reads the module global `_ROOT` at call time, in the `is_relative_to(_ROOT)` check, `_rel` and `cwd=_ROOT`. So `monkeypatch.setattr(relearn, "_ROOT", scratch)` works with no driver edit. **`phase27_relearn.py` is in its own `PINNED_MODULES` (`:61-69`), and `test_provenance_digests_match_live_bytes` compares its bytes, so edit only the test.**
- Fix: `scratch = tmp_path/"repo"; git init -q -b main scratch` (the `tests/test_phase25_driver.py:150` precedent), then `(scratch/"results").mkdir()`, and write the probe at `scratch/"results/phase27_admission_probe_never_committed.json"`. Assert `SystemExit` with "not tracked" and "REFUSING".
- Guard: snapshot before and after `{rel: sha256}` of `git ls-files 'results/phase27_*'` (today only `results/phase27_admission.json`), plus the existing `_real_tree_strays()` (`:799`). Both must be unchanged, and `git status --porcelain -- 'results/phase27_*'` must be empty.
- Adjacent: `:239` targets the real `results/phase27_probe_never_written.json`, but the builder is stubbed before any write. It is out of IN-07's scope; the planner can leave it.

### DEBT-02 (TD-16-R1): open. The note is not read at runtime anywhere
- `scripts/phase16_persistence.py:2025-2060` has `_CONTEXT_PATH` and `arm_d_qualifier()` (the D-25 anchor `"- **D-25:**"`). D-28 is rendered through the English constant `LADDER_ANOMALY_CAVEAT` (`:1830-1841`), emitted at `:2495`.
- Measured `d28_note()` with the same parser and anchor `"- **D-28:**"`: 1402 chars, sha256 `171725c69ff06241882a0d165c02172d80721b3b33d55ddf7c8bef8609ad4210`. It is the whole READING QUALIFICATION blockquote. The non-`>` line immediately after the anchor is skipped by design. The Portuguese verbatim kernel (the `*"…"*` span) is **absent** from `results/phase16_persistence_report.md` (`'licenciou' in report` → False). Per D-17 this becomes a named limitation; do not re-render.
- Implementation: extract a private `_blockquote_after(anchor)` shared by `arm_d_qualifier()` and a new `d28_note()`, and add `D28_NOTE_ANCHOR = "- **D-28:**"`. Tests (in `test_phase16_driver.py`): `sha256(d28_note()) == <pinned digest>`, which reddens if the note is amended. `d28_note() == _context_blockquote("- **D-28:**")` (the existing helper at `:90`). `arm_d_qualifier()` output unchanged (`:1319` already). And both directions of: kernel ∉ report ⇔ the limitation entry exists.
- **Guards that bite in `phase16_persistence.py`:** `tests/test_phase16_driver.py:648` forbids the substrings `startswith`, `endswith`, `fuzz`, `levenshtein`, `SequenceMatcher`, `difflib` **anywhere in the source, comments included**. Use the existing `stripped[:1] == ">"` slice idiom. `:629` requires `source.count("0.125") == 1`.
- The module is not ancestry-guarded, and no record `module_sha256` names it (ledger TD-16-R1 evidence, re-checked: no `results/*.json` other than the ledger mentions it).

### DEBT-03 (TD-17-SUMMARY-FRONTMATTER): open
- The validator requires the keys `phase, plan, subsystem, tags, duration, completed` and checks **presence only** (`fm[f] === undefined`, `frontmatter.cjs:315,374`). All 11 files currently return `missing: ["duration","completed"]`, measured.
- **Date pitfall, measured.** `git log --diff-filter=A` on the archived path gives `16a07d8 2026-08-20` (the archive move) for all 11. The real first-add, via `git log --follow --diff-filter=A --format=%ad --date=short` (identical to the original `.planning/phases/17-…/` path):

| File | commit | completed |
|---|---|---|
| 17-01 | ecabfeb | 2026-08-14 |
| 17-02 | 7dfd678 | 2026-08-14 |
| 17-03 | 428ccb4 | 2026-08-14 |
| 17-04 | 719d64f | 2026-08-14 |
| 17-05 | 1d62287 | 2026-08-14 |
| 17-06 | 890e78e | 2026-08-14 |
| 17-07 | d846b92 | 2026-08-14 |
| 17-08 | 1c97a10 | 2026-08-14 |
| 17-09 | 7d8b2db | 2026-08-14 |
| 17-10 | 35c557a | 2026-08-15 |
| 17-11 | 85db5a0 | 2026-08-15 |

- Format precedent (27-0x SUMMARYs): `completed: 2026-09-16`, `duration: 21min`. Use `duration: not recorded at the time` (a string, which the validator accepts) and add both lines at top level in the first `---` block. **Edit by hand, never with `gsd-sdk frontmatter.set`** (memory: mutation handlers corrupt frontmatter). The read-only `gsd-sdk query frontmatter.validate … --schema summary` is fine as acceptance.
- No test or script reads these SUMMARY bytes. Measured: `tests/test_phase17_stats.py:54` reads only `17-CONTEXT.md`, `test_phase28_ledger.py:240` globs `.planning/quick` only, and `phase28_report.py` reads `.planning/research/SUMMARY.md`. The ledger (`results/phase28_ledger.json`) is frozen and its tests check row text, not live file state.
- A CI-safe test mirrors the validator: parse the top-level keys of the first `---` block, assert all 6 are present, and assert `completed` equals the `--follow` first-add author date.

### DEBT-04 (P22-WARNING-4/5): open, and a constant closes it
- The accountant lives at `src/personacore/privacy/accountant.py` (`delta_closed`, `delta_quadrature`, `epsilon_for`, `sigma_for`). **Transitive loading is unavoidable.** `phase25_record` imports `phase25_epsilon` at module level (`phase25_record.py:82`), so importing `phase25_record` or `phase27_prereg` puts `personacore.privacy.accountant` in `sys.modules` (measured). `mitigation_gate`, `mitigation_budget` and `phase20_gate_coverage` do not.
- The entry: `NAMED_LIMITATIONS = {"P22-WARNING-4/5": {"reason": "no v5.0 number uses the accountant; the adversarial arm carries no ε claim (Phase 25 D-01)", "source": "22-VERIFICATION.md:149-183", "ledger_rows": ("P22-WARNING-4", "P22-WARNING-5")}, "TD-16-R1-REPORT": {...DEBT-02 absence...}}`.
- Test: an AST census over `sorted(scripts.glob("phase29_*.py") … "phase34_*.py")`, derived by glob so later v5.0 modules are covered. It checks for no `Import`/`ImportFrom` of `personacore.privacy`, `personacore.privacy.accountant` or `phase25_epsilon`, and no `Name`/`Attribute` in `{epsilon_for, sigma_for, delta_closed, delta_quadrature}`. **State in the entry that the accountant is transitively loaded through `phase25_record` and that no v5.0 call reaches it.** A `sys.modules` assertion would be false.

## Common Pitfalls

### Pitfall 1: A literal `4` anywhere in the prereg reddens the D-04 guard
**What goes wrong:** An innocent `== 4` or `range(4)` fails the "numeric literal equal to REPLAY_WINDOWS_PER_FACT" guard.
**How to avoid:** Derive counts (`len(...)`). The guard compares against the imported value, so it must run inside the test (torch is allowed there).

### Pitfall 2: Grep acceptance over prose
Docstrings in this repo discuss the very terms being guarded, for example "replay", "4 windows" and "adv_n64". Every "is not re-typed" criterion must be an AST walk over `ast.Constant`/`Assign`/`Import`/`Call` nodes, never a `grep` (memory: grep criteria measure prose).

### Pitfall 3: Starting the ancestry clock early
Any committed `results/phase3*` file (a test probe, a scratch record) freezes the prereg before D-15 lands. Tests write only under `tmp_path`.

### Pitfall 4: Repo-wide censuses that bite new files
- `tests/test_phase21_sc5.py:189-196` counts `== 10` / `!= 10` in **every** `tests/*.py`, comments included. Don't write it.
- `tests/test_phase25_driver.py:359`: no `os.replace` outside `phase25_run.py`/`phase25_record.py`.
- `tests/test_phase20_correction.py:1377`: no call or import of `mitigation_point_verdict` in `scripts/`/`src/`.
- `tests/test_phase23_ctrl.py:82`: no `train_never_taught` definition and no `train_arm(` outside the register. The prereg must not call either.
- `mitigation_gate.ratchet_k` accepts K only in (48, 24, 16, 8).
- `tests/test_phase25_prereg.py:271` flags any function pairing `equal/allclose/sha256/hexdigest` with both a sigma-zero and a seam-off identifier marker. Avoid naming anything `*sigma_zero*` next to `*seam_off*`.
- `tests/test_phase25_venue.py` pins CI skip totals. **New tests must not `skipif`.** Everything here is git- and CPU-only, and CI has `fetch-depth: 0`.
- Clean-tree probes (11) go red while `scripts/`, `tests/` or `results/` has uncommitted changes. Run the full suite only on a committed tree.

### Pitfall 5: `phase27_prereg` functions silently mean DP
`recall_threshold`, `extraction_ceiling_x`, `arm_of`, `admitted_point_keys` and `relearning_is_worth_attempting` bake in `dp_*` control keys, 44 points and v4.0 key order. Only the relearning pins in D-09's list are imported. The v5.0 admission functions are new, arm-keyed and written in the prereg.

### Pitfall 6: D-09's "seven baselines unchanged" conflicts with ACTRL-01
`PINNED_BASELINES["control_n8"/"control_n64"]` are the **DP** σ=0 adapters (`checkpoints/phase25_sigma0p000000_dp_n{8,64}_adapter.pt`). `phase27_prereg.recovery_gate` refuses any baseline key outside that dict. A v5.0 relearning control must be the `advr` ratio-0 adapter, whose sha256 does not exist until Phase 32. Pin it **by reference** (the adapter named by `results/phase32_point_<CONTROL_KEYS[leg]>.json::adapter_sha256`) and import only the five `never_taught_*` baselines unchanged. Planner: surface this as a D-09 clarification in the plan. It is consistent with D-09's own "v5.0 changes … the control source", but it is not a pure import.

### Pitfall 7: Shared `_ROOT` in DEBT-01
Patch only `relearn._ROOT`. `relearn.RECORD` was computed at import from the real root. That is harmless here because the probe path is passed explicitly, but don't call `_require_admitted()` without an argument under the patch.

## Code Examples

### Ancestry test (verbatim precedent, adapt the pathspec source)
```python
# Source: tests/test_phase27_prereg.py:73-120 (copy _assert_frozen_before unchanged)
def test_phase29_prereg_is_frozen_before_every_v5_result():
    tracked = sorted({p for spec in phase29_prereg.ARTIFACT_PATHSPECS
                      for p in _git("ls-files", spec).split()})
    _assert_frozen_before("scripts/phase29_prereg.py", tracked)
```

### Differential refusal test
```python
# Source pattern: tests/test_phase20_correction.py::_corrected_call + phase25_promotion.COVERAGE_FLOOR_REFUSAL_MARKERS
def test_refusal_predicate_agrees_with_the_route():
    for heldout_k, refused in ((0, True), (1, False)):
        assert phase29_prereg.control_is_unlearnable(1, 1008, heldout_k, 648) is refused
        # ...and the route itself: SystemExit carrying both markers iff refused
```

## State of the Art (in-repo)

| Old (v4.0) | v5.0 | Impact |
|---|---|---|
| `adv_*` arm, no replay (`ADVERSARIAL_NO_REPLAY`) | `advr_*`, replay = DP expression | Condition (c) tests the ratio, not the recipe |
| Admission verdicts ADMITTED/MOOT/INCONCLUSIVE; REFUSED only a tally name | A 4th admission verdict, REFUSED (D-07) | All-refused never reads as "mitigation held" |
| Adversarial `control_gap` borrowed from DP σ=0 (D-47) | Own `advr` ratio-0 control (ACTRL-01) | `phase25_promotion.control_readings` cannot be reused |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Filenames for the Phase 30/31/33/34 results (`phase30_calibration.json`, `phase31_probe_*.json`, `phase31_budget.json`, `phase33_admission.json`) | Pattern 2 | Low if the plan fixes them here and later phases import them; high if later phases retype other names |
| A2 | Second seed for any promotion = `FRESH_SEEDS[1]` (2024) | D-15 | Only matters under option 1. It is a new decision the developer must make |
| A3 | Relearning control baseline pinned by record reference rather than digest | Pitfall 6 | Reinterprets D-09; needs developer confirmation |
| A4 | `duration: not recorded at the time` is acceptable wording | DEBT-03 | The validator accepts any value; wording is the developer's taste |

## Open Questions

1. **D-15 ruling (blocking, checkpoint).** Options 1 and 2, with the friction table above. Under option 1 there are also: which second seed; whether the control is replicated; the promotion key and path namespace; and Phase-31 budget coverage.
   **PENDING:** ruled at the 29-04 Task 1 checkpoint; the ruling is appended here.
2. **The D-09 control baseline** (Pitfall 6). Recommendation: import `never_taught_*` ×5 and pin the `advr` control by Phase-32 record reference.
   **PENDING:** confirmed or overridden at the 29-04 checkpoint, item (b).
3. **Where Phase 30's `advr` arms are declared.** They must NOT be appended to `teach_persona.ADV_ARMS` (that breaks `phase25_verdict.curve_verdicts`), and `teach_persona.py` is in `phase27_relearn.PINNED_MODULES` (IN-08: any edit reddens `test_provenance_digests_match_live_bytes`). This is Phase 30's problem, but the prereg should name the arm tuple Phase 30 must create, e.g. `ADVR_ARMS`, so the seam is pinned.
   **RESOLVED (planning):** Plan 29-01 declares `ADVR_ARMS` in `scripts/phase29_prereg.py`; Phase 30 imports it. Subject to veto at the 29-04 checkpoint, item (d).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python venv | all | ✓ | 3.11.15 (`.venv`) | — |
| git (full history) | ancestry, DEBT-03 dates | ✓ | local; CI `fetch-depth: 0` | — |
| gsd-sdk (read-only validate) | DEBT-03 acceptance | ✓ | `~/.local/bin/gsd-sdk` | the pytest mirror |
| torch | lazy only, inside tests | ✓ (venv) | — | — |

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest 8.x (`.venv/bin/pytest`) |
| Config file | `pyproject.toml` (existing) |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase29_prereg.py tests/test_phase27_relearn.py -k "phase29 or untracked_record" tests/test_phase16_driver.py -k "qualifier or d28 or monotone"`, or run each file on its own. Measured: phase27 prereg + phase20 correction 4.2 s, relearn probe 1.1 s, phase16 subset 0.9 s |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + an `until grep -q '^EXIT=' $LOG` waiter (~25 min; Bash caps at 600 s) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| PREREG-01 | prereg precedes every tracked v5.0 result | git/unit | `pytest tests/test_phase29_prereg.py -k frozen_before` | ❌ Wave 0 |
| PREREG-01 | 12 keys, swap-back equals v4.0 keys, v4.0 parsers refuse, no dupes | unit | `-k keys` | ❌ |
| PREREG-01 | paths distinct from `results/phase2*`, pathspecs derived, probe/calibration paths never parse as keys | unit | `-k paths` | ❌ |
| PREREG-01/04 | gate, grid and F_Y by reference (`is`); AST guards RED on mutated copies | unit/AST | `-k "by_reference or ast"` | ❌ |
| PREREG-04 | `replay_windows(8)==32`, `(64)==256`, equals the DP expression; torch-free import probe | unit + subprocess | `-k "replay or without_torch"` | ❌ |
| PREREG-03 | predicate ⇔ route floor refusal (differential); v4.0 adv_n64 reading re-read from the frontier; REFUSED record fields; no retry/alternate key exposed | unit | `-k "unlearnable or refused or retry"` | ❌ |
| PREREG-02 | admission four branches + precedence on forged 12-point dicts; threshold from the advr control counts; mixed case MOOT names the refused leg | unit | `-k admission` | ❌ |
| DEBT-01 | probe under a scratch `_ROOT`; `results/phase27_*` hashes and strays unchanged | integration (git init) | `pytest tests/test_phase27_relearn.py -k untracked_record` | ✅ edit |
| DEBT-02 | `d28_note()` digest pinned; equals the test helper's parse; report-absence ⇔ limitation entry | unit | `pytest tests/test_phase16_driver.py -k d28` | ✅ add tests |
| DEBT-03 | 11 SUMMARYs carry the 6 keys; `completed` == `--follow` first-add date | git/unit | `pytest tests/test_phase29_prereg.py -k summary_frontmatter` (+ `gsd-sdk query frontmatter.validate … --schema summary`) | ❌ |
| DEBT-04 | limitation entry present; AST census over `scripts/phase29_*..phase34_*` finds no accountant import or call | AST | `-k accountant` | ❌ |

### Sampling Rate
- **Per task commit:** the targeted file(s) above (< 10 s each).
- **Per wave merge:** the full suite, on a committed tree only (the clean-tree probes).
- **Phase gate:** full suite green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_phase29_prereg.py`: covers PREREG-01..04, DEBT-03 and DEBT-04
- [ ] DEBT-02 tests appended to `tests/test_phase16_driver.py`
- [ ] No framework install needed

## Security Domain

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2/V3/V4 | no | — (no auth or session surface) |
| V5 Input Validation | yes | `_prove` → `SystemExit` on counts (int-not-bool), key charset (via the wrapped `point_key` → `phase25_prereg.point_record_path`), leg membership |
| V6 Cryptography | no (sha256 only as a content digest, via `hashlib`) | — |

| Threat | STRIDE | Mitigation |
|---|---|---|
| Post-hoc re-tune after seeing a refused control | Tampering | Write-once 12 keys, no retry key, ancestry guard |
| Path traversal via key | Tampering | Charset rule inherited through `point_key` |
| Borrowed DP reading used as the adversarial floor | Spoofing | Arm-keyed `CONTROL_KEYS` to `advr`; the v4.0 parsers refuse `advr` keys |

## Sources

### Primary (HIGH)
- Source files at `ffa0f19`: `scripts/phase27_prereg.py`, `tests/test_phase27_prereg.py:73-150`, `scripts/phase25_record.py:100-300`, `scripts/phase25_prereg.py:254-295,360-405`, `scripts/phase25_promotion.py` (all), `scripts/phase25_verdict.py:107-138,504-640`, `scripts/mitigation_gate.py:637-1030`, `scripts/phase20_gate_coverage.py:500-698`, `scripts/teach_persona.py:99-216,245-310,1745-1975`, `scripts/phase27_relearn.py:37-175,940-985`, `tests/test_phase27_relearn.py:160-260,790-815`, `scripts/phase16_persistence.py:1822-2060,2480-2500`, `tests/test_phase16_driver.py:90-106,615-652`, `~/.claude/get-shit-done/bin/lib/frontmatter.cjs:314-376`.
- Measurements: the `point_key("advr_n8")` refusal; the GATE-08 route PASS/INCONCLUSIVE split; accountant presence in `sys.modules`; frontier `control_readings`; the D-28 note digest and its absence from the report; the SUMMARY first-add dates (`--follow`); validator output for all 11 files; targeted test timings.
- `results/phase28_ledger.json` rows IN-07, TD-16-R1, TD-17-SUMMARY-FRONTMATTER, P22-WARNING-4/5 (read only).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Every symbol and line was read or executed.
- Architecture: HIGH for keys, paths, guards and debt. MEDIUM for the admission frontier schema, because Phase 32 has not built the frontier yet and the schema is pinned as the v4.0 shape.
- Pitfalls: HIGH. Each census was read at its source line.

**Research date:** 2026-09-24
**Valid until:** the first `results/phase3*` commit (the prereg freezes then), or any edit to the cited frozen modules.
