# Phase 33: Admission and Relearning on Admitted Points - Research

**Researched:** 2026-09-28
**Domain:** Write-once admission record over a frozen pre-registration; refusal-only attack legs; git-history proofs; carried-debt disposition
**Confidence:** HIGH (every load-bearing fact below was measured in this session in the 3.11 `.venv`, in the repo, or in a scratch git repo)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Admitted-branch apparatus
- **D-01:** **Refusal surface only.** The Phase 33 driver has `admit` plus the attack-leg
  sub-commands. The first statement of every leg refuses unless the COMMITTED admission record reads
  ADMITTED, and no training or scoring code sits behind a leg. The advr port of
  `phase27_relearn`'s curve/gate/calibrate/structural-proof is **not built**. If a future milestone
  admits a point, it builds the body. A leg given a forged ADMITTED record must still refuse, with a
  message saying the v5.0 apparatus was not built because admission read MOOT. It must never look
  as though it ran.
- **D-02:** The refusal is proven by **tests plus live captures**, mirroring 27-05. A parametrized
  test makes each leg refuse on a MOOT / REFUSED / CANDIDATE-UNREPLICATED / INCONCLUSIVE record,
  and on an absent or untracked one. Live stderr captures of every leg on the real record are taken
  **before and after** its commit and must be byte-identical with exit 1.
- **D-03:** ADMIT-01 is met by **importing** `phase29_prereg` (`EXPECTED_POINTS`,
  `recall_threshold(frontier, leg, arm)`, `admission`, `relearning_scope`, `SCOPE_RULE`,
  `V5_RESULT_PATHS`). Nothing is retyped. `phase27_prereg.py` stays byte-unchanged and its ancestry
  guard stays green. `phase29_prereg.py` is not edited either, because it is the pre-registration.

#### Admission record and commit
- **D-04:** **Thin record** at `results/phase33_admission.json` (the path is imported from
  `phase29_prereg.V5_RESULT_PATHS`). It contains:
  - the `admission()` result verbatim: verdict, reasons, admitted_point_keys, control_readings;
  - the `relearning_scope()` output;
  - frontier path, sha256 and bytes;
  - provenance: git_sha, head_at_write, `module_sha256` of phase29_prereg + the phase33 module + the
    gate modules admission reaches, and the prereg `COMMITTED` date;
  - the named limitation (D-08).

  Phase 27's baselines, disjointness, budget and rows fields are **not** carried, because they only
  fed an apparatus that ran.
- **D-05:** **Claude commits after developer review.** `admit` writes without committing, prints the
  verdict, the reasons and the control readings, and stops at a developer review checkpoint. After
  "approved", Claude commits the record **alone** in its own commit. This is the 31-06 / 32 D-16
  pattern. Claude never pushes.
- **D-06:** **No override.** If the record exists, `admit` refuses, and it has no `--force` flag.
  The only way to redo admission is to delete the record in its own commit. The overwrite refusal
  comes first and the dirty-tree refusal second, before any digest. The dirty check's pathspec
  excludes the record itself, as `phase27_relearn.admit` does. The planner confirms that exclusion in
  code with a test on a file that is **not yet tracked**, which is the state during the review
  checkpoint.
- **D-07:** **"Called exactly once" is proven three ways** (ADMIT-02):
  1. The write refusal (D-06).
  2. A git test: the record has exactly **one** commit, and that commit touches only that path. The
     test **fails loudly on a shallow clone** instead of passing vacuously.
  3. The record is pinned to the frontier both ways. The recorded sha256 is recomputed in the test
     from the live file's bytes, and the frontier has a single commit, derived from `git log` and
     never typed.

  The structure follows Phase 27's `test_the_record_is_pinned_to_the_frontier_both_ways`. The tests
  must handle the "written but not yet tracked" state of the review checkpoint. The prereg-before-
  result ancestry comes for free: `test_phase29_prereg_is_frozen_before_every_v5_result` already
  covers `results/phase33_*` through `ARTIFACT_PATHSPECS`.

#### MOOT limitation and requirement ticks
- **D-08:** The limitation **is per leg and is carried verbatim from `admission()`'s reasons**. No
  hand-typed wording or numerals. n8 was measured: 0 of 6 PASS, all 6 INCONCLUSIVE, none a
  replication candidate. n64 **could not be measured**: its own control is unlearnable (taught
  0/1008), and MOOT does not extend to that capacity. It must never read "the mitigation held". The
  limitation states plainly that **only the refusal surface exists**, meaning the advr relearning
  apparatus was not built because the scope rule read MOOT. It **must not** copy Phase 27's
  "apparatus built and guarded, never exercised" phrasing.
- **D-09:** **Ticks follow the Phase 27 D-05 precedent, with a timing condition.**
  - **ADMIT-01 and ADMIT-02** are ticked only **after** the record is committed and the D-02/D-07
    proofs exist.
  - **RELRN-06..09 stay unticked.** Each traceability row reads
    `NOT SATISFIED — named limitation: admission read MOOT`. It cites the record and PREREG-02 and
    says only the refusal surface exists.
  - REQUIREMENTS.md / ROADMAP.md / STATE.md are **edited by hand**: snapshot before, diff after.
    **Zero `gsd-sdk` mutation handlers** are used, per the memory rule on handlers corrupting planning
    frontmatter.

  The phase can still pass verification, because ROADMAP SC4 calls MOOT a success path.

#### Carried debt disposal
- **D-10:** **P31-WR-01** is the relearning csv under `results/` that trips `refuse_if_dirty` before
  crash recovery; Phase 32 D-09 assigned it to Phase 33. It is **closed in Phase 33 for lack of a
  consumer**, because no relearning artifact is written on the MOOT branch. No output-location code
  is written. It goes to the Phase 34 ledger as **RE-DEFERRED**, with:
  - reason: no relearning artifact on the MOOT branch;
  - target: the milestone that builds the legs' body;
  - prerequisite: decide where relearning artifacts live relative to `refuse_if_dirty` before the
    first one is written.
- **D-11:** The **open 32-REVIEW findings go to the Phase 34 ledger without being fixed in Phase 33.**
  `phase32_points.py` is pinned in 7 records, `phase32_frontier.py` is pinned in the frontier, and
  Phase 33 reuses neither.
  - **CR-01, WR-01 and WR-05** enter as **RE-DEFERRED**, with target "the milestone that reuses
    `phase32_points`". They keep the prerequisite fixed by the security ruling AR-32-02/03
    (`32-SECURITY.md:107-110`): fix them with dated pin continuations before any reuse.
  - Ledger ids carry a phase prefix (`P31-WR-01`, `P32-WR-01`, …) so they do not collide.
  - The ledger declares `provenance.git_sha` the authoritative pin and cites 32-VERIFICATION.md by
    reference, not by copying.
  - The planner checks whether any **IN-*** finding touches a field already published in the
    frontier. If one does, it needs a **dated continuation** instead of RE-DEFERRED.
  - WR-03 is already fixed (`325aaf0` RED, `f7c1a83` fix).
- **D-12:** **The AR-32-02/03 condition becomes an AST guard.** A census of the `scripts/phase33_*.py`
  modules turns RED on any import of `phase32_points` (any form: `import`, `from … import`,
  `importlib`), and its failure message cites AR-32-02. The RED is taken naturally from a temporary
  copy that carries the import, never planted in the real file. See the memory rules
  natural-red-beats-planted-red and grep-criteria-measure-prose, and use AST, not grep.

### Claude's Discretion
- Module and sub-command names (e.g. `scripts/phase33_admission.py` with `admit` + leg sub-commands),
  as long as the record path is imported from `phase29_prereg`.
- The exact set of gate modules hashed into `module_sha256`, derived from what `admission()` actually
  reaches, never typed from memory. 32-VERIFICATION's `module_sha256` note is the counter-example to
  avoid.
- Where the Phase 34 ledger rows are staged. The ledger file itself belongs to Phase 34, so Phase 33
  may record the rows in its SUMMARY/VERIFICATION for Phase 34 to import.

### Deferred Ideas (OUT OF SCOPE)
- **Building the advr relearning apparatus** (the curve, gate, calibrate and structural-proof bodies)
  is deferred to whichever future milestone admits a point. Its prerequisites are P31-WR-01 (the
  artifact location relative to `refuse_if_dirty`) and, if it reuses `phase32_points`, the
  CR-01/WR-01/WR-05 fixes with dated pin continuations.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADMIT-01 | A continuation module reads the v5.0 frontier with its own expected point count and an arm-keyed `recall_threshold(frontier, leg, arm)`, leaving `phase27_prereg.py` untouched (its ancestry guard green) | All of it already exists in `scripts/phase29_prereg.py` (`EXPECTED_POINTS = 12`, `recall_threshold(frontier, leg, arm)` refusing any `arm != "advr"`). A runtime trace proves `admission()` reaches `recall_threshold` (Finding 1). `phase27_prereg.py` has 1 commit (`916ad4d`), and `git diff --quiet v4.0 HEAD -- scripts/phase27_prereg.py` exits 0. |
| ADMIT-02 | Admission is called once and its record is write-once | Overwrite refusal before dirty refusal (the `phase27_relearn.admit` / `phase32_frontier.emit` pattern), `phase25_run.atomic_write_json`, a three-state single-commit git test with a shallow guard, and the frontier pinned both ways (Findings 2, 5, 7) |
| RELRN-06 | Cost-to-recovery curve on each admitted point | MOOT branch: a refusal-only leg plus the named limitation. The record's `relearning_scope()` output reads `"RELRN-06..09 ship as a MOOT named limitation"` (measured). |
| RELRN-07 | Curve's qualification of the verdict published | Same: a refusal-only leg plus the limitation |
| RELRN-08 | Budget and seed structurally enforced | Same: a refusal-only leg plus the limitation |
| RELRN-09 | Recovery measured on the disjoint recovery fixture | Same: a refusal-only leg plus the limitation. P31-WR-01 is RE-DEFERRED because nothing consumes it (D-10). |
</phase_requirements>

## Summary

Phase 33 writes no decision logic. `phase29_prereg.admission()` and `relearning_scope()` are the
whole contract. I re-ran them **live** in `.venv` (Python 3.11.15) on the committed
`results/phase32_frontier.json` (one commit `645641b`, 56,857 bytes, sha256
`4a4bcb60f9b8bd9a1a63d9525c1d80fee9baec121ac15358a972dd625dc97be9`). They return **MOOT**, with
`admitted_point_keys: []`, `control_readings` `n8 {taught [777,1008], heldout [334,648]}` and
`n64 {taught [0,1008], heldout [1,648]}`, three reasons (tallies PASS 0 / FAIL 0 / INCONCLUSIVE 6 /
REFUSED 6; `advr_n64 fully REFUSED …`; `MOOT: no measured point cleared the frontier — nothing to
relearn`), and the scope `RELRN-06..09 ship as a MOOT named limitation`. CONTEXT's prose is
therefore confirmed by measurement. Still, the record, not this paragraph, decides which branch
ships.

The work is small but full of traps. Six measured facts drive the plan:
1. **The `module_sha256` set.** The modules `admission()` reaches at runtime are
   `phase29_prereg`, `mitigation_gate`, `phase27_prereg`, `phase25_record` and `phase25_prereg`.
   Constants come from `mitigation_budget` (the grid and K values) and `mitigation_gate` (`F_Y`).
   `phase20_gate_coverage` is imported but **not** called.
2. **The D-06 pathspec exclusion.** Without `--force`, the exclusion never matters while the record
   is absent or untracked, because the overwrite refusal fires first. It becomes reachable in
   exactly one state: a **tracked record deleted in the working tree but not committed**. In that
   state it lets `admit` run, which bypasses "delete it in its own commit". An extra
   tracked-but-absent refusal closes the hole (demonstrated in a scratch repo).
3. **`atomic_write_json` costs nothing extra to import.** `phase25_run` is already loaded
   transitively by `import phase29_prereg`, with no torch and no subprocess at import. The
   os.replace census **forbids** writing a new atomic helper.
4. **The before/after stderr captures are byte-identical only if the leg checks the verdict before
   the tracked conjunct.**
5. **Two repo-wide censuses constrain spelling.** `_wr05_failures` flags a bare `"control_readings"`
   string or Name, and `test_phase21_sc5` flags `== 10` under `tests/`.
6. **IN-03 is the only IN finding that touches a published frontier field**
   (`calibration.add_commit`). Its published value is measured correct: one add, `4339f2b`, in the
   frontier and in all 7 trained point records.

**Primary recommendation:** one module `scripts/phase33_admission.py` (torch-free) with `admit`
and four refusal-only legs. It imports `phase29_prereg` and `phase25_run.atomic_write_json` and
derives `PINNED_MODULES` from `module.__file__`. It ships with one test file,
`tests/test_phase33_admission.py`, whose git tests are three-state (absent / written-untracked /
committed) and shallow-guarded.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Admission decision | Frozen prereg module (`scripts/phase29_prereg.py`) | — | Frozen by the ancestry guard. Phase 33 only calls it (D-03). |
| Record write (write-once) | Driver `scripts/phase33_admission.py::admit` | `phase25_run.atomic_write_json`, `personacore.provenance` | Same pattern as every prior write-once emitter |
| Record persistence and "once" proof | Git (a single commit touching only the record) | Tests | D-05 / D-07: the commit is the human-reviewed act |
| Leg refusal | Driver legs (first statement) | — | D-01: no body behind any leg |
| Limitation text for the report | The record (bound from `admission()` reasons and frontier tallies) | Phase 34 renderer | D-08: Phase 34 renders from the record, never from prose |
| Carried-debt disposition | Phase 33 SUMMARY/VERIFICATION rows | Phase 34 ledger | CONTEXT discretion: the ledger file belongs to Phase 34 |

## Standard Stack

No new dependencies. Everything is stdlib plus in-repo modules.

| Component | Source | Purpose | Measured fact |
|-----------|--------|---------|---------------|
| `phase29_prereg` | `scripts/phase29_prereg.py` (last commit `49a4e9f`, 2026-09-24) | `admission`, `relearning_scope`, `SCOPE_RULE`, `EXPECTED_POINTS`, `recall_threshold`, `V5_RESULT_PATHS`, `COMMITTED` ("2026-09-24"), `VERDICTS`, `REFUSED`, `CANDIDATE_UNREPLICATED` | Imports in 0.23 s, torch not loaded, zero subprocess calls at import [VERIFIED: live probe] |
| `phase25_run.atomic_write_json` | `scripts/phase25_run.py:118` | tmp in destination dir, fsync, `os.replace`. Serialises `json.dumps(blob, sort_keys=True)` (compact, no trailing newline) | Already in `sys.modules` after `import phase29_prereg` (loaded by `phase25_promotion`/`phase25_verdict`). The incremental import costs 0.0000 s [VERIFIED] |
| `personacore.provenance` | `src/personacore/provenance.py` | `git_sha()`, `refuse_if_dirty(who, detail, pathspec, cwd)` | Untracked files count as dirty and `:(exclude)` works (Finding 2) [VERIFIED] |
| argparse / hashlib / json / pathlib / subprocess | stdlib | CLI, digests, `git ls-files` | — |

**Installation:** none.

## Package Legitimacy Audit

This phase installs no external packages, so there is nothing for slopcheck to check.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none) | — | — | — | — | — | — |

**Packages removed:** none. **Packages flagged:** none.

## Measured Findings (the seven facts the orchestrator required)

### Finding 1: What `admission()` and `relearning_scope()` actually reach (for D-04 `module_sha256`)

I traced the live call on the committed frontier with `sys.setprofile`, filtering to repo files:

```
scripts/mitigation_gate.py   ['_prove', 'promote_to_full_fidelity', 'ratchet_k']
scripts/phase25_prereg.py    ['_prove', 'point_record_path']
scripts/phase25_record.py    ['_axis_for', '_prove', 'point_key']
scripts/phase27_prereg.py    ['point_verdict_string']
scripts/phase29_prereg.py    [admission, recall_threshold, relearning_scope, POINT_KEYS, control_key,
                              leg_keys, point_key, _own_control_mismatch, control_is_unlearnable, ...]
```

- `promote_to_full_fidelity` **is** reached on the MOOT path: 6 INCONCLUSIVE points each go through
  the CANDIDATE check and return False. It calls `ratchet_k` (K menu in `mitigation_gate.K_RUNGS`).
- **Constants read, not called** (the tracer cannot see these, so they must be added by
  ownership):
  - `mitigation_budget`: `ADVERSARIAL_RATIO_GRID` via `phase29_prereg.RATIO_GRID`, used by
    `POINT_KEYS()`; `CURVE_K = 16` and `FULL_FIDELITY_K = 48` via `phase27_prereg` →
    `phase29_prereg.CURVE_K/FULL_K`.
  - `mitigation_gate`: `F_Y = 0.7`, `V4_VERDICTS`, `REPLICATION_PENDING_MARKER`, `K_RUNGS`.
  - `phase25_record`: `AXIS_FOR_ARM`.
- **Imported but not reached:** `phase20_gate_coverage` (only `GATE_ROUTE` is bound) and
  `phase25_promotion` (only `COVERAGE_FLOOR_REFUSAL_MARKERS` is bound, and admission never reads
  it). `erasure_gate` is loaded by `mitigation_gate`, but the admission path uses none of its
  values.
- The import closure of `phase29_prereg` is much wider: about 27 repo modules, including
  `personacore.privacy.accountant` transitively (already disclosed in `NAMED_LIMITATIONS`). Hashing
  the whole closure is not what D-04 asks for.

**Recommendation (derive, never type).** Follow `phase32_frontier.PROVENANCE_MODULES`: build the
tuple from `module.__file__` of the modules the driver imports.

```python
PINNED_MODULES = tuple(
    pathlib.Path(m.__file__).resolve().relative_to(_ROOT).as_posix()
    for m in (sys.modules[__name__], phase29_prereg, mitigation_gate, mitigation_budget,
              phase27_prereg, phase25_record, phase25_prereg)
)
```

`__file__` can stand in for `sys.modules[__name__]`. Add one test that re-runs the `sys.setprofile`
trace over `admission(frontier)` + `relearning_scope(...)` and asserts:
- the traced set of `scripts/*.py` files is a subset of `PINNED_MODULES`;
- the traced set is non-empty and contains `scripts/mitigation_gate.py` (non-vacuity);
- `mitigation_budget` is in the tuple because `phase29_prereg.RATIO_GRID is
  mitigation_budget.ADVERSARIAL_RATIO_GRID`, asserted with `is`.

That test turns RED if a future edit to the prereg's call graph reaches a new module (natural RED:
drop one module from a tmp copy of the tuple). Driver-machinery modules (`phase25_run`,
`personacore/provenance.py`) are optional. `git_sha` pins them anyway. If they are included, say in
the record that they are the writer, not the gate.

### Finding 2: `refuse_if_dirty` + the `:(exclude)` pathspec with an untracked record (scratch repo demo)

Scratch repo with `scripts/`, `src/`, `results/phase32_frontier.json` committed, then:

| State | `git status --porcelain -- scripts src results` | same + `:(exclude)results/phase33_admission.json` |
|-------|-------------------------------------------------|---------------------------------------------------|
| Record written, **untracked** | `?? results/phase33_admission.json` → **dirty** | empty → clean |
| Another untracked `results/phase33_other.json` | dirty | **still dirty** (the exclusion is exact-path) |
| Record tracked + modified | dirty | clean |
| Record in a new untracked sub-dir, excluded by exact path | — | clean (git does not collapse to `?? dir/` when the only file is excluded) |
| **Tracked record deleted in the worktree (uncommitted)** | ` D results/phase33_admission.json` → dirty | **clean → admit would PROCEED** |
| Tracked record `git rm`-staged (uncommitted) | dirty | **clean → admit would PROCEED** |

Also measured: `git ls-files <untracked>` prints nothing (exit 0),
`git ls-files --error-unmatch <untracked>` exits 1, and `git log -- <untracked>` prints nothing.

**What this means for D-06:**
- Without `--force`, `admit`'s first statement refuses whenever the file exists. So at the review
  checkpoint (written, untracked) a second `admit` stops at the **overwrite** refusal, and the
  exclusion is never consulted. An untracked record *does* trip the dirty check without the
  exclusion. It never gets that far, though.
- The only state where the exclusion changes the outcome is "tracked, then deleted but not
  committed". There it **weakens** D-06's "the only way to redo admission is to delete the record
  in its own commit".
- **Recommendation (honours D-06 and closes the hole):** keep the exclusion as locked. Put
  `_prove(not tracked(out_path) or out_path.exists(), "... deleted but the deletion is not
  committed — delete it in its own commit first")` **between** the overwrite refusal and the dirty
  refusal. Expose the pathspec as a module constant or function (`DIRTY_PATHSPEC`), so the D-06
  test can run `refuse_if_dirty(pathspec=DIRTY_PATHSPEC, cwd=scratch)` in a scratch repo:
  - with the record **untracked** → returns `""`;
  - with a **sibling** untracked `results/phase33_x.json` → `SystemExit`;
  - with the tracked record **deleted** → `admit` refuses through the new conjunct.

  This is flagged as Open Question 1, because it adds a conjunct beyond the letter of D-06.
- The atomic write's temp file is `results/.phase33_admission.json.<rand>.tmp`. It is not
  excluded, so a stray one left by a SIGKILL would correctly block the next `admit`.

### Finding 3: `phase25_run.atomic_write_json`'s import cost; is there a lighter equivalent?

- `import phase29_prereg` already loads `phase25_run` (through `phase25_promotion:43` and
  `phase25_verdict`). A second `import phase25_run` costs 0.0000 s. Torch is not loaded,
  `teach_persona` is not loaded, and import runs zero subprocesses [VERIFIED].
- `phase30_calibration`, `phase31_budget`, `phase31_probe`, `phase32_points` and `phase32_frontier`
  all use `phase25_run.atomic_write_json`.
- **No lighter equivalent may be written.**
  `tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers` asserts
  that the set of `scripts/*.py` + `src/**/*.py` files containing an `os.replace` attribute is
  exactly `{phase25_run.py, phase25_record.py}`. `phase25_record.py` has two private writers
  (`:991`, `:1772`), which are not reusable helpers. **Use `phase25_run.atomic_write_json`.**
- Serialisation is `json.dumps(blob, sort_keys=True)`, compact, with no newline, the same as
  `results/phase27_admission.json` (1 line). Round-trip every tuple (e.g. `relearn_point_keys`)
  through JSON before any equality test.

### Finding 4: 32-REVIEW findings: which touch published fields, and their current status

Status measured from `git log -1 -- <file>`:
- `scripts/phase32_points.py` last changed at `94fdd7f`;
- `scripts/phase32_frontier.py` at `fd76e0d`;
- only `tests/test_phase30_points.py` changed since the review (`325aaf0`, `f7c1a83`).

| Finding | Status | Touches a field published in `results/phase32_frontier.json`? | Disposition per D-11 |
|---------|--------|-----|-----|
| CR-01 | OPEN (`phase32_points.py` untouched since `94fdd7f`) | No (point-record provenance only) | RE-DEFERRED; target: the milestone that reuses `phase32_points`; prereq AR-32-02/03 |
| WR-01 | OPEN | No | RE-DEFERRED (same) |
| WR-02 | OPEN | **Yes: `provenance.module_sha256`** (measured keys: `phase20_gate_coverage`, `phase25_promotion`, `phase25_verdict`, `phase29_prereg`, `phase32_frontier`; it omits `mitigation_gate`, `erasure_gate`, …) | Not named in D-11's RE-DEFERRED trio. Already recorded in 32-VERIFICATION:13 as "git_sha is the authoritative pin". It needs a Phase 34 ledger row that cites 32-VERIFICATION by reference (Open Question 2). |
| WR-03 | **FIXED** `325aaf0` (RED) → `f7c1a83` (fix) | No | CLOSED |
| WR-04 | OPEN | No (a reachable crash state, latent: n8 control gap +0.134325) | Not in D-11's trio; ledger row (Open Question 2) |
| WR-05 | OPEN | No | RE-DEFERRED (trio) |
| IN-01 | OPEN | No. `past_line_ruling` is in the 7 trained **point records** (`null` in all 7), not in the frontier | RE-DEFERRED |
| IN-02 | OPEN | No (`stop_line_seconds`: 0 occurrences in the frontier or point records) | RE-DEFERRED |
| **IN-03** | OPEN | **Yes: `calibration.add_commit`** (also in all 7 trained point records) | See below |
| IN-04 | OPEN | No (heartbeat file under `data/`) | RE-DEFERRED |
| IN-05 | OPEN | No (dirty-check cwd; no published field) | RE-DEFERRED |
| IN-06 | OPEN | No (dead test branches) | RE-DEFERRED |
| IN-07 | OPEN | No (PREREG-03 records carry no provenance; nothing is published) | RE-DEFERRED |

**IN-03 measured:**
- `git log --diff-filter=A -- results/phase30_calibration.json` returns exactly one add, `4339f2b`.
- `git log --all --diff-filter=D` on that path returns 0 deletions.
- All 8 published `add_commit` values (frontier + 7 point records) equal
  `4339f2b2bc29ab0765a821b5d47b617cd6092f24`.

So `adds[-1] == adds[0]`, and the **published value is correct**. The defect is latent code only.
Under D-11's literal rule ("touches a field already published → dated continuation instead of
RE-DEFERRED"), IN-03 gets a **dated continuation note**. It records that the value was measured
correct on 2026-09-28 (a single add, zero deletes) with no code or byte change. The code fix itself
stays with the milestone that reuses `phase32_frontier`/`phase32_points`. Where that continuation
lives (Phase 33 SUMMARY row versus `scripts/_addendum.py`) is Open Question 3.

### Finding 5: Existing test structures to mirror

- **Ancestry (free coverage).** `tests/test_phase29_prereg.py:109`,
  `test_phase29_prereg_is_frozen_before_every_v5_result`, gathers
  `git ls-files results/phase30_* .. results/phase34_*`. It asserts first that
  `rev-parse --is-shallow-repository == "false"`, then checks that every `phase29_prereg.py` commit
  (7 of them, the newest `49a4e9f`) is a **strict** ancestor of each file's earliest add. An
  untracked record is invisible to it, and after the commit it gains one tracked artifact. The same
  holds for `test_call_time_sources_are_frozen_before_every_v5_result`, whose sources are
  `phase25_record.py` and `phase20_gate_coverage.py`. **Neither may be edited in Phase 33.**
- **`test_the_record_is_pinned_to_the_frontier_both_ways`** (`tests/test_phase27_prereg.py:118`) is
  two-state:
  - if the file exists: sha256 and bytes recomputed from the live frontier, and
    `bool(tracked) == bool(added)`;
  - otherwise: assert not tracked.

  It then asserts in both states that `git log --oneline -- FRONTIER` has exactly 1 line. It has
  **no shallow guard**. On a depth-1 clone, `git log -- path` returns the grafted root, so "1
  commit" would pass vacuously. Phase 33 must add the shallow assert first (D-07).
- **`test_each_leg_refuses_unless_admitted`** (`tests/test_phase27_relearn.py:137`):
  - parametrised `(mode, reading)` with ids `f"{mode}-{verdict}"`;
  - monkeypatches the body entry points to `pytest.fail`;
  - forges records in `tmp_path`, which is outside the repo, so the tracked conjunct is skipped;
  - calls `main(argv)` inside `pytest.raises(SystemExit)`;
  - asserts `"REFUSING"` and the verdict are in the message, and that nothing was written.

  The untracked case is `test_a_leg_refuses_an_untracked_record_inside_the_repo` (`:182`):
  1. `git init` a scratch repo under `tmp_path`;
  2. `monkeypatch.setattr(relearn, "_ROOT", scratch)`;
  3. forge an ADMITTED record at `scratch/results/...`;
  4. expect "not tracked";
  5. assert the real `results/` is untouched.
- **Phase 33 parametrisation (D-02):** legs × `{MOOT, REFUSED, CANDIDATE-UNREPLICATED,
  INCONCLUSIVE, absent}` via `main(argv)`, plus `untracked` via the scratch-repo pattern, plus
  **forged ADMITTED** (in `tmp_path`, both tracked conjunct and verdict pass) → must still refuse
  with the "apparatus not built" message. The body stubs are unnecessary because there is no body.
  Instead assert that the leg's AST contains no call beyond the guard and the refusal, or that
  `tmp_path` stays empty.
- **Git read-only surface:** copy `test_phase27_relearn.py:507-545`
  (`_git_argv_subcommands` + `test_the_drivers_git_surface_is_read_only`, allowed set
  `phase25_run.READ_ONLY_GIT_ACTIONS = ("ls-files","show","rev-parse","status")`). This proves
  `admit` never commits (D-05).

**The single-commit test (D-07 part 2), three states, shallow-first:**

```python
def test_the_record_was_committed_exactly_once_alone():
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: commit count cannot be read — set fetch-depth: 0 (.github/workflows/ci.yml)")
    tracked = _git("ls-files", "--", RECORD).split()
    commits = _git("log", "--format=%H", "--", RECORD).split()   # every commit touching it
    if not (_ROOT / RECORD).exists():
        assert not tracked and not commits, "record absent from disk but known to git"
        return
    if not tracked:                                              # D-05 review checkpoint
        assert commits == [], "an untracked record has history — it was deleted after a commit"
        return
    assert len(commits) == 1, commits
    touched = _git("show", "--name-only", "--format=", commits[0]).split()
    assert touched == [RECORD], touched
```

Part 3 (pinned both ways): `blob["frontier"]["sha256"] == sha256((_ROOT / FRONTIER).read_bytes())`
and `bytes == stat().st_size`. `git log --format=%H -- FRONTIER` has exactly one entry (currently
`645641b`, derived, never typed). In the committed state, add
`git merge-base --is-ancestor <frontier commit> <record commit>`. Run it in all three states, with
the shallow assert first. The stronger check also covers the untracked state:
`admission(json.loads(frontier))` re-derived live must equal `blob["admission"]` after a JSON round
trip, and `relearning_scope(...)` likewise.

### Finding 6: Repo-wide guards and censuses that will see the new files

| Guard | Scope | What the new module/test must satisfy |
|-------|-------|---------------------------------------|
| `test_phase29_prereg.py::test_no_v5_module_uses_the_accountant` | `scripts/phase29_*..phase34_*.py` | No import of `phase25_epsilon` / `personacore.privacy*`; no Name/Attribute `epsilon_for`, `sigma_for`, `delta_closed`, `delta_quadrature` |
| `test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control` (`_wr05_failures`) | `scripts/phase30_*..phase34_*.py` | **No Name/Attribute `control_readings`, `control_reading`, `control_key_for`, `record_kwargs`, `_adversarial_extras`**. The string `"control_readings"` is allowed **only** as a dict-literal key or as `x["control_readings"]` on a plain-Name subscript chain; a bare string (e.g. in a tuple of field names) is flagged. No `dp_n…` string or f-string outside docstrings. No `phase25_points` / `phase25_promotion` carrier or parser reference. Carry the admission dict whole (`blob["admission"] = result`) and there is nothing to spell. |
| `test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers` | all `scripts/*.py` + `src/**/*.py` | No `os.replace`; use `atomic_write_json` |
| `test_phase21_sc5.py::test_wall_census_is_the_measured_set` | every `tests/*.py` line (comments included) | **No `== 10` in the new test file** |
| `test_lora_inject.py` (ISO-06) | all scripts | No `inject_lora` call (none needed) |
| `test_phase23_ctrl.py`, `test_lora_inject.py` `train_arm(` register | all scripts | Do not write `train_arm(` or `train_never_taught`, not even in a docstring for the latter's definition census |
| `test_phase20_correction.py` pin census | all scripts | Do not import or call `mitigation_point_verdict` |
| `mitigation_gate.ratchet_k` K menu | fixtures | K in (48, 24, 16, 8) only, if any fixture forges K |
| `test_phase19_erasure.py` | all scripts | No `retention_perplexity(` call |
| `test_phase17_stats.py` import allowlist | only `_GATE_MODULES` | n/a |
| `test_phase32_points.py` `V5_DRIVER_MODULES` | `scripts/phase32_*.py` only | n/a (phase33 is outside the glob) |
| stray-glob tests (`test_phase32_live` `results/phase32_*`, `test_phase31_probe` `results/phase31_probe_*`, `test_phase27_relearn` `results/phase27_*`) | named globs | `results/phase33_*` is matched by none |
| `ruff check` + `ruff format --check` | repo (`.planning` excluded) | line-length 100; rules E, F, W, I |
| **Clean-tree probes** (memory: 11 of them) | `results/`: `test_phase23_resume::test_production_resume_epsilon_bit_identical`, `test_phase25_frontier::test_a_perturbed_per_point_count_breaks_the_aggregate` | These **fail while the record is untracked** (review checkpoint). That is expected. Run the full suite only on a committed tree. |

**D-12 guard, spec derived from the above:** walk `ast.parse` of every `scripts/phase33_*.py`
(assert the glob is non-empty). Fail on:
- `Import` with `alias.name == "phase32_points"` or starting with `phase32_points.`;
- `ImportFrom` with `module == "phase32_points"`;
- a string `Constant` equal to `"phase32_points"` outside docstrings. This covers
  `importlib.import_module("phase32_points")`, `__import__`, and `sys.modules["phase32_points"]`.

Every failure message cites `AR-32-02 (32-SECURITY.md)`. The natural RED needs no plant:
`tests/test_phase32_points.py:32` and `tests/test_phase32_live.py:43` both contain
`import phase32_points as p32`. Copy the source to `tmp_path` and run the matcher. The
`from … import` and `importlib` forms have **no natural occurrence anywhere** (grep: only
`phase32_points.py` and those two tests mention it), so they must be tmp-copy plants. D-12 allows
"a temporary copy that carries the import". A runtime complement is also cheap:

```python
subprocess.run([sys.executable, "-c",
    "import sys; sys.path.insert(0,'scripts'); import phase33_admission; "
    "print('phase32_points' in sys.modules, 'torch' in sys.modules)"])
```

This must print `False False`. Measured today: `phase29_prereg` pulls in neither.

### Finding 7: CI and git-history tests

`.github/workflows/ci.yml` sets `actions/checkout@v4` with **`fetch-depth: 0`** (full history), on
ubuntu-latest with Python 3.11, and runs `pytest -q`. Local repo: `is-shallow-repository = false`,
git 2.50.1 (`--is-shallow-repository` needs git ≥ 2.15). The shallow assert is therefore GREEN in
CI and locally, and turns loudly RED only on a depth-limited clone, which is the intent. Two
cautions:
- The ubuntu skip-count pin (`tests/test_phase25_venue.py`) drifts if a new test **skips** on
  ubuntu. **Use no `pytest.skip` / `skipif`** in the new file. The three-state tests branch and
  assert; they never skip.
- Claude never pushes, so CI sees Phase 33 only after the developer pushes (Phase 34 close).

## Architecture Patterns

### System Architecture Diagram

```
results/phase32_frontier.json (tracked, 1 commit)
        │  read bytes (sha256 + size)            ┌──────────── admit ────────────┐
        ▼                                        │ 1 overwrite refusal (exists)   │
 json.loads ──► phase29_prereg.admission() ──►   │ 2 tracked-but-absent refusal*  │
                       │ (reaches mitigation_gate,│ 3 refuse_if_dirty(scripts,src, │
                       │  phase27_prereg,         │   results, :(exclude)record)   │
                       │  phase25_record/prereg)  │ 4 build blob, module_sha256    │
                       ▼                          │ 5 atomic_write_json            │
            relearning_scope() ─────────────────► │ 6 print verdict/reasons/ctrl   │
                                                  └──────────────┬─────────────────┘
                                                                 ▼
                         results/phase33_admission.json (UNTRACKED) ── developer review ──►
                         "approved" ──► Claude: git add <record>; git commit (record alone)
                                                                 │
 leg sub-command (curve/gate/…) ─► exists? ─► verdict == ADMITTED? ─► tracked (ls-files)? ─►
        always: SystemExit("… v5.0 apparatus not built …")          (exit 1, stderr)
```
`*` = the recommendation in Finding 2 (Open Question 1).

### Recommended Project Structure
```
scripts/phase33_admission.py     # admit + 4 refusal-only legs; torch-free; no phase32_points
tests/test_phase33_admission.py  # D-02, D-06, D-07, D-12, provenance, git-surface, import probe
results/phase33_admission.json   # written by admit, committed alone after review
```

### Pattern 1: Write-once `admit` (the phase32_frontier.emit register)
```python
# Source: scripts/phase32_frontier.py:496-552, scripts/phase27_relearn.py:361-412 (measured)
RECORD_PATH = next(p for p in phase29_prereg.V5_RESULT_PATHS
                   if p.startswith("results/phase33_admission"))       # never typed
FRONTIER_PATH = next(p for p in phase29_prereg.V5_RESULT_PATHS
                     if p.startswith("results/phase32_frontier"))
DIRTY_PATHSPEC = ("scripts", "src", "results", f":(exclude){RECORD_PATH}")

def admit(out_path=RECORD_PATH):
    out = _GIT_ROOT / out_path
    _prove(not out.exists(), f"{out_path} exists — REFUSING to overwrite it. The only route is "
           "to delete it in its own commit (D-06); there is no --force")
    _prove(not _tracked(out_path), f"{out_path} is tracked but absent — REFUSING: commit the "
           "deletion on its own first")                                  # Open Question 1
    refuse_if_dirty(who="phase33_admission", detail="...", pathspec=DIRTY_PATHSPEC, cwd=_GIT_ROOT)
    _prove(_tracked(FRONTIER_PATH), f"{FRONTIER_PATH} is not tracked")
    raw = (_GIT_ROOT / FRONTIER_PATH).read_bytes()
    result = phase29_prereg.admission(json.loads(raw))
    scope = phase29_prereg.relearning_scope(result)   # SystemExit on INCONCLUSIVE — correct
    blob = {..., "admission": result, "scope": scope,
            "frontier": {"path": FRONTIER_PATH, "sha256": sha256(raw).hexdigest(), "bytes": len(raw)},
            "provenance": {"module_sha256": {...PINNED_MODULES}, "git_sha": INSTRUMENT_GIT_SHA,
                           "head_at_write": git_sha(), "prereg_committed": phase29_prereg.COMMITTED},
            "limitation": ...}
    phase25_run.atomic_write_json(out, blob)
    print(...)   # verdict, reasons, control readings; "(NOT committed; D-05 review first)"
```
Keep a patchable `_GIT_ROOT` separate from `_ROOT` (the code root used for hashes), as
`phase32_frontier` does. Tests then point `_GIT_ROOT` at a scratch repo. IN-05 warns against
sending the scripts/src dirty check to a patched root. In production the two are identical.

### Pattern 2: The leg guard (order matters for D-02 byte-identity)
```python
def _refuse_leg(record_path=RECORD_PATH):
    path = (_GIT_ROOT / record_path) if not pathlib.Path(record_path).is_absolute() else pathlib.Path(record_path)
    path = path.resolve()
    _prove(path.exists(), f"{_rel(path)} is absent — REFUSING ...")
    blob = json.loads(path.read_text(encoding="utf-8"))
    verdict = blob["admission"]["verdict"]
    _prove(verdict == "ADMITTED", f"{_rel(path)} reads {verdict!r} — REFUSING: "
           f"{phase29_prereg.SCOPE_RULE[verdict]} ...")   # SCOPE_RULE has every verdict
    if path.is_relative_to(_GIT_ROOT):
        _prove(_tracked(_rel(path)), f"{_rel(path)} is not tracked — REFUSING ...")
    raise SystemExit("[phase33_admission] REFUSING: the v5.0 relearning apparatus was not built "
                     "... (D-01)")   # unconditional: a forged ADMITTED still refuses
```
**Order: exists → verdict → tracked → unconditional refusal.** With the real MOOT record, the
**verdict** conjunct fires both before the commit (untracked) and after it, so the stderr bytes
are identical. If `tracked` came first, the pre-commit capture would read "not tracked" and the
post-commit capture "MOOT", which breaks D-02. Keep volatile values (HEAD sha, time, absolute
tmp paths) **out** of the message. `phase29_prereg.SCOPE_RULE[verdict]` gives verdict-specific
wording by reference (`KeyError` is impossible for the five `VERDICTS`; guard unknown values with
`_prove(verdict in VERDICTS)`).

### Pattern 3: The limitation, bound and never typed (D-08)
- Per-leg lines come from `result["reasons"]`. The n64 line is present verbatim: `advr_n64 fully
  REFUSED (advr_n64 control recall taught 0/1008, heldout 1/648); MOOT does not extend to that
  capacity`.
- **Gap (measured):** `admission()`'s reasons contain **no per-leg n8 line**. They give only the
  global tally and the n64 line. The n8 statement ("0 of 6 PASS, 6 INCONCLUSIVE, none a
  replication candidate") must bind its counts from `frontier["verdicts"]["tallies_by_leg"]
  ["advr_n8"]` (measured: `{FAIL 0, INCONCLUSIVE 6, PASS 0, REFUSED 0}`). `admission()` proved in
  step (1c) that this equals the entries, so the binding is safe. "None a candidate" follows from
  verdict ≠ `CANDIDATE_UNREPLICATED`.
- The fixed sentence ("only the refusal surface exists; the advr relearning apparatus was not built
  because the scope rule read MOOT") is a template with the scope rule bound from
  `scope["rule"]`. Assert in a test that it does **not** contain `"never exercised"` or
  `"apparatus built"`, and that no sentence contains `"mitigation held"` unless negated. Use an
  AST or string test on the **record value**, not a grep of the module source (grep-criteria rule).

### Anti-Patterns to Avoid
- Retyping `"results/phase33_admission.json"`, `12`, `0.7`, a verdict literal or a reason string:
  import it or bind it.
- Checking `tracked` before `verdict` in the leg guard (breaks D-02 byte identity).
- A `--force` flag, or any `git add`/`commit` in the module (D-05/D-06, git-surface test).
- A local variable named `control_readings`, or a field-name tuple containing that string
  (`_wr05_failures` RED).
- `pytest.skip` in the new tests (ubuntu skip pin).
- Writing a test fixture under the real `results/` (it would start the phase29 ancestry clock if
  committed and trips the clean-tree probes). Use `tmp_path` or a scratch `git init`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Admission logic / scope | any re-derivation | `phase29_prereg.admission`, `relearning_scope` | Frozen by ancestry (D-03) |
| Atomic JSON write | tmp + fsync + `os.replace` | `phase25_run.atomic_write_json` | The os.replace census forbids a third writer |
| Dirty-tree refusal | `git status` parsing | `personacore.provenance.refuse_if_dirty` | Untracked counts as dirty; git failure raises |
| Commit SHA | `rev-parse` wrapper | `personacore.provenance.git_sha` | Existing primitive |
| Ancestry check | new helper | `_assert_frozen_before` pattern (the test already covers `results/phase33_*`) | Free coverage |
| Git-surface census | new matcher | copy `test_phase27_relearn.py:507-545` | Proven pattern |

## Runtime State Inventory

Not a rename phase. The runtime-state questions still apply to the review checkpoint:

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | `results/phase33_admission.json` exists **untracked** between `admit` and the commit | The commit is the one sanctioned transition. Tests are three-state. |
| Live service config | None (no scheduler, no plist: this phase runs in seconds) | none |
| OS-registered state | None | none |
| Secrets/env vars | None | none |
| Build artifacts | None. Worktree agents break the editable venv (memory); run executors sequentially on `main` | Repoint the editable install if collection errors appear |

## Common Pitfalls

### Pitfall 1: Stderr captures differ before and after the commit
**What goes wrong:** the D-02 byte-identity fails. **Why:** the tracked conjunct fires first
before the commit, or the message embeds HEAD, a timestamp or an absolute path. **Avoid:** order
exists → verdict → tracked, with a stable message. **Warning sign:** `shasum` of the capture pairs
differs.

### Pitfall 2: The full suite is red at the review checkpoint
**What goes wrong:** the two `results/` clean-tree probes fail while the record is untracked.
**Avoid:** run only the targeted phase files before the commit. Run the full suite (~25 min,
`nohup … &` + a grep waiter, Bash caps at 600 s) **after** the record commit.

### Pitfall 3: A vacuous "exactly one commit" on a shallow clone
**Avoid:** assert `--is-shallow-repository == "false"` first, in every git-history test.

### Pitfall 4: The ancestry clock started by a test fixture
**What goes wrong:** any `results/phase33_*` file committed before the real record becomes an
"artifact". **Avoid:** fixtures in `tmp_path` / scratch repos only. Assert
`git status --porcelain -- results/phase33_*` is unchanged at test end, following the
`test_phase27_relearn.py:207-210` pattern.

### Pitfall 5: The planning-file edits break the frozen Phase 28 renderer
**What goes wrong:** `scripts/phase28_report.py` and `tests/test_phase25_correction.py` read
REQUIREMENTS/ROADMAP/STATE live. **Avoid:** edit only the v5.0 rows (ADMIT/RELRN checkboxes and the
v5.0 Traceability status cells, `REQUIREMENTS.md:627-635, 676-681`). Afterwards run
`.venv/bin/python scripts/phase28_report.py check` and
`pytest tests/test_phase28_report.py tests/test_phase28_prereg.py tests/test_phase25_correction.py -q`.
Snapshot and diff all three files; zero gsd-sdk handlers.

### Pitfall 6: The pinned-module tripwire
Phase 33 edits no module pinned in any `results/*.json` `module_sha256`. Confirm this before
dispatch with `grep -l "phase33\|phase29_prereg" results/*.json`. `phase29_prereg.py` **is** pinned
in the frontier's `module_sha256`, one more reason it must not change.

## Code Examples

### D-12 AST census (natural RED from an existing importer)
```python
def _phase32_points_imports(source):
    tree = ast.parse(source)
    docs = _docstring_nodes(tree)          # reuse the test_phase30_points helper shape
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            hits += [f"import {a.name} at line {n.lineno}" for a in n.names
                     if a.name == "phase32_points" or a.name.startswith("phase32_points.")]
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "phase32_points":
            hits.append(f"from {n.module} import at line {n.lineno}")
        elif isinstance(n, ast.Constant) and n.value == "phase32_points" and id(n) not in docs:
            hits.append(f"string 'phase32_points' at line {n.lineno} (importlib/sys.modules)")
    return [f"{h} — AR-32-02 (32-SECURITY.md): fix CR-01/WR-01/WR-05 first" for h in hits]

def test_no_phase33_module_imports_phase32_points(tmp_path):
    modules = sorted(_SCRIPTS.glob("phase33_*.py"))
    assert modules, "census blind: no scripts/phase33_*.py"
    for p in modules:
        assert _phase32_points_imports(p.read_text(encoding="utf-8")) == [], p
    natural = (_ROOT / "tests/test_phase32_points.py").read_text(encoding="utf-8")
    copy = tmp_path / "natural.py"; copy.write_text(natural, encoding="utf-8")
    assert _phase32_points_imports(copy.read_text(encoding="utf-8"))   # natural RED
```

## State of the Art

| Old Approach (Phase 27) | Phase 33 approach | Why |
|-------------------------|-------------------|-----|
| `--force` overwrite flag | none (D-06) | One sanctioned route: delete in its own commit |
| Operator commits by hand | Claude commits after "approved" (D-05) | 31-06 / 32 D-16 pattern |
| ~20-field record + a built, unexercised apparatus | thin record, refusal-only legs | D-01/D-04 |
| Frontier-pin test without a shallow guard | shallow-first, three-state | D-07 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Adding a tracked-but-absent refusal to `admit` is compatible with D-06's intent | Finding 2 | If the developer rejects it, the uncommitted-deletion bypass stays open (low likelihood, but it is exactly what D-06 forbids) |
| A2 | WR-02, WR-04 and IN-* are RE-DEFERRED ledger rows even though D-11 names only CR-01/WR-01/WR-05 explicitly | Finding 4 | Ledger wording may need a developer ruling |
| A3 | IN-03's "dated continuation" can be a note that records the measured-correct value, with no code or byte change | Finding 4 | If a code fix is demanded, it costs a pin continuation on `phase32_frontier.py` + `phase32_points.py` |

## Open Questions (RESOLVED)

1. **The tracked-but-absent conjunct in `admit` (Finding 2).** RESOLVED: D-13
   - Known: the D-06 exclusion is inert in the untracked state. It is reachable only as an
     uncommitted deletion, where it lets `admit` proceed.
   - Recommendation: add the conjunct and name it in the plan as a D-06 strengthening, so the
     developer confirms it at plan review.
2. **Dispositions for WR-02 and WR-04.** RESOLVED: D-14. D-11 lists CR-01/WR-01/WR-05 explicitly and says "the open
   32-REVIEW findings go to the Phase 34 ledger".
   - Recommendation: WR-02 is a ledger row citing 32-VERIFICATION:13 ("git_sha is the authoritative
     pin"). WR-04 is RE-DEFERRED with target "the milestone that reuses `phase32_frontier`".
3. **Where IN-03's dated continuation lives.** RESOLVED: D-16
   - Recommendation: a dated note row staged in the Phase 33 SUMMARY for the Phase 34 ledger. It
     carries the measured evidence (one add `4339f2b`, zero deletes, 8 published values equal),
     because no pinned file changes.
4. **ACTRL-01** (RESOLVED: D-15) stays unticked "until first used on real data in Phase 32/33"
   (REQUIREMENTS:671). Phase 33's admission reads the own advr control through
   `recall_threshold`. ACTRL-01 is not in Phase 33's IDs, so the developer rules. Out of scope
   unless raised.
5. **Leg names.** RESOLVED: D-16
   - Recommendation: mirror Phase 27's four sub-modes (`calibrate`, `curve`, `gate`,
     `structural-proof`), each mapped in a module tuple to its RELRN-06..09 requirement(s). The
     record's limitation then names every leg by id.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything | ✓ | 3.11.15 (`.venv/bin/python`) | — (never system 3.14) |
| git | provenance, history tests | ✓ | 2.50.1 | — |
| Full-history clone | D-07 shallow guard | ✓ local (`is-shallow=false`); CI `fetch-depth: 0` | — | — |
| torch | not needed | — | — | module is torch-free |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (the `.venv`), CPU-only |
| Config file | `pyproject.toml` (ruff); pytest defaults |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase33_admission.py` |
| Guard set (measured 147 tests in 20.9 s, without the new file) | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase33_admission.py tests/test_phase29_prereg.py tests/test_phase27_prereg.py tests/test_phase30_points.py tests/test_phase25_driver.py tests/test_phase21_sc5.py` |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` + an `until grep -q '^EXIT=' $LOG` waiter (~25 min; committed tree only) |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff format --check .` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMIT-01 | Constants/functions imported by reference (`EXPECTED_POINTS is`, `SCOPE_RULE is`, record path derived from `V5_RESULT_PATHS`); the admission trace reaches `recall_threshold` | unit + AST | `pytest tests/test_phase33_admission.py -k "by_reference or reaches" -x` | ❌ Wave 0 |
| ADMIT-01 | `phase27_prereg.py` byte-unchanged (`git diff --quiet v4.0 HEAD -- scripts/phase27_prereg.py` and 1 commit); its ancestry guard is green | git | `pytest tests/test_phase27_prereg.py -k frozen -x` + new assert | partial |
| ADMIT-02 | Overwrite refusal first, then tracked-but-absent, then dirty, all before any digest (order proven with recorders) | unit | `pytest tests/test_phase33_admission.py -k "refuses" -x` | ❌ Wave 0 |
| ADMIT-02 | Exclusion on an untracked record; sibling untracked still dirty; uncommitted deletion refused (scratch repo) | git (scratch) | `pytest tests/test_phase33_admission.py -k pathspec -x` | ❌ Wave 0 |
| ADMIT-02 | Exactly one commit touching only the record; shallow-first; three states | git | `pytest tests/test_phase33_admission.py -k exactly_once -x` | ❌ Wave 0 |
| ADMIT-02 | Record pinned to the frontier both ways; admission and scope re-derive live | git + unit | `pytest tests/test_phase33_admission.py -k pinned -x` | ❌ Wave 0 |
| ADMIT-02 | `module_sha256` equals live bytes; the traced reach set is a subset of `PINNED_MODULES` | unit | `pytest tests/test_phase33_admission.py -k provenance -x` | ❌ Wave 0 |
| ADMIT-02 | Git surface read-only (no add/commit/push in the module) | AST | `pytest tests/test_phase33_admission.py -k git_surface -x` | ❌ Wave 0 |
| RELRN-06..09 | Every leg refuses on MOOT/REFUSED/CANDIDATE-UNREPLICATED/INCONCLUSIVE/absent/untracked/forged-ADMITTED; writes nothing | unit (parametrised) | `pytest tests/test_phase33_admission.py -k refuses_unless -x` | ❌ Wave 0 |
| RELRN-06..09 | The limitation is bound from reasons and tallies; no "never exercised"/"apparatus built"; n64 never "held" | unit (on the record value) | `pytest tests/test_phase33_admission.py -k limitation -x` | ❌ Wave 0 |
| RELRN-06..09 | Live stderr captures before and after the commit: byte-identical, exit 1 | manual/live (27-05) | `for leg in …; do .venv/bin/python scripts/phase33_admission.py $leg > o 2> e; echo $?; done; shasum -a 256 e*` | n/a: captured in the SUMMARY |
| D-12 | No `phase32_points` import in any form; natural RED from `tests/test_phase32_points.py`; subprocess probe `False False` | AST + runtime | `pytest tests/test_phase33_admission.py -k phase32_points -x` | ❌ Wave 0 |
| (census) | New files pass the accountant, `_wr05`, os.replace and `== 10` censuses | existing | guard-set command above | ✅ |

### Sampling Rate
- **Per task commit:** the quick run command (+ ruff).
- **Per wave merge:** the guard-set command.
- **Phase gate:** the full suite green on the **committed** tree after the record commit (the
  `results/` clean-tree probes are red while it is untracked). Then `phase28_report.py check` +
  the Phase 28 guard files after the hand edits to the planning files.

### Wave 0 Gaps
- [ ] `tests/test_phase33_admission.py`: every row above marked ❌
- [ ] Helper copies: `_git`, `_docstring_nodes`, `_git_argv_subcommands` (copy the patterns; do not
  import test modules across files)
- Framework install: none needed

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no (single local developer) | — |
| V5 Input Validation | yes | `--record`/`--out` paths `.resolve()`d before the tracked conjunct (the Phase 27 pattern). Frontier JSON goes through `admission()`, which returns INCONCLUSIVE on malformed input (T-29-14). The record JSON is read with `json.loads` only (no pickle). |
| V6 Cryptography | yes (integrity only) | `hashlib.sha256` digests; no hand-rolled crypto |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Re-running admission to fish for a different verdict | Tampering / Repudiation | No `--force`; overwrite refusal; single-commit test; tracked-but-absent refusal |
| Forged ADMITTED record makes a leg "run" | Spoofing | Unconditional refusal after all conjuncts (D-01); tracked conjunct |
| Record from a dirty tree names an unreproducible SHA | Repudiation | `refuse_if_dirty` before any digest; `git_sha` + `module_sha256` |
| Reuse of `phase32_points` with known provenance gaps | Tampering | D-12 AST census citing AR-32-02 + runtime `sys.modules` probe |
| A relative `--record` path steps around the tracked check | Spoofing | Resolve the path first (the Phase 27 `_require_admitted` pattern) |

## Sources

### Primary (HIGH confidence, measured this session)
- `.venv/bin/python` live run of `phase29_prereg.admission` / `relearning_scope` on the committed
  frontier; `sys.setprofile` reach trace; `sys.modules` import-closure and subprocess-spy probes
- Scratch git repo (session scratchpad): porcelain/exclude behaviour in 6 states; `ls-files` /
  `log` on untracked files
- Repo files: `scripts/phase29_prereg.py`, `scripts/phase27_relearn.py:131-160,361-412,1155-1208`,
  `scripts/phase32_frontier.py:1-80,480-560`, `scripts/phase25_run.py:118-175,751-753`,
  `src/personacore/provenance.py`, `tests/test_phase29_prereg.py:60-150,507-600`,
  `tests/test_phase27_prereg.py:75-131`, `tests/test_phase27_relearn.py:56-260,507-545`,
  `tests/test_phase30_points.py:577-760`, `tests/test_phase25_driver.py:341-365`,
  `tests/test_phase21_sc5.py:250-300`, `.github/workflows/ci.yml`
- Git history: `git log` on `scripts/phase27_prereg.py`, `phase29_prereg.py`, `phase32_*.py`,
  `results/phase30_calibration.json`, `results/phase32_frontier.json`
- `.planning/phases/32-*/32-REVIEW.md`, `32-VERIFICATION.md:7-16,54-58`, `32-SECURITY.md:100-112`,
  `31-REVIEW.md:53-65`, `REQUIREMENTS.md:595-681`, `ROADMAP.md:1347-1370`
- Memory notes: execute-phase-gates-in-personacore, grep-criteria-measure-prose,
  natural-red-beats-planted-red, milestone-close-planning-files-are-frozen-inputs

### Secondary / Tertiary
- None. No web sources were needed; the domain is entirely in-repo.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, because every component is in-repo and its import cost was measured
- Architecture: HIGH, because the patterns are copied from committed, tested emitters (27/32)
- Pitfalls: HIGH, because each was demonstrated (scratch repo, trace, census source read)
- Carried-debt dispositions: MEDIUM, because WR-02/WR-04/IN-03 wording needs developer confirmation
  (Open Questions 2-3)

**Research date:** 2026-09-28
**Valid until:** the next commit touching `scripts/phase29_prereg.py`, `scripts/phase25_run.py`,
`src/personacore/provenance.py` or `results/phase32_frontier.json` (none expected).
