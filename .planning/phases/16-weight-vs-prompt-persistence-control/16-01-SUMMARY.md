---
phase: 16-weight-vs-prompt-persistence-control
plan: 01
subsystem: testing
tags: [pytest, git, ci, github-actions, sha256, pre-registration, structural-guard]

# Dependency graph
requires:
  - phase: v2.0 / erasure gate
    provides: "scripts/erasure_gate.py — the pre-registered erasure decision rule (PREREG-01, commit 23a830c) whose commit date this plan turns into a checkable fact"
  - phase: 16 (fixture)
    provides: "results/phase16_recall_sample.json — the one committed v3.0 artifact the ancestry guard currently orders (added at 70dcc56)"
provides:
  - "PREREG-02 enforced: a CPU-only test proving the pre-registration commit is a git ANCESTOR of the first commit adding every v3.0 results artifact"
  - "That guard fails loudly on a shallow clone, on a wrong pinned SHA, and on an empty match set — it cannot be green and blind"
  - "CI checks out full git history, so the ancestry query resolves in CI and not only on the local box"
  - "STAT-04 enforced: pyproject.toml pinned byte-identical by sha256, so a runtime dependency cannot enter v3.0 silently"
affects: [phase-16 remaining plans, phase-17, phase-18, any plan tempted to reach for scipy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ancestry over timestamps: ordering claims are asked of the commit DAG, never of a committer clock"
    - "Anti-vacuity counter: a guard that iterates a glob closes with `assert checked` so an empty match set is red, not green"
    - "Identity + ordering as a pair: a pinned SHA is checked for what it IS, not only for where it sits in the DAG"
    - "Byte-level file pin (sha256 of read_bytes) as a dependency freeze, over parsing a dependency list"

key-files:
  created:
    - "tests/test_phase16_prereg.py — PREREG-02 ordering + identity guard (Task 2)"
  modified:
    - ".github/workflows/ci.yml — fetch-depth: 0 on actions/checkout@v4 (Task 1)"
    - "tests/test_package.py — test_pyproject_unchanged_since_v2_close (Task 3)"

key-decisions:
  - "Ordering proof uses `git log -S'fetch-depth: 0'` for the YAML and `--diff-filter=A` for the new test file — `--diff-filter=A` on the YAML returns the file's original creation commit and would pass regardless of order"
  - "PREREG_COMMIT pinned at the full 40 characters; an abbreviation is a prefix query against a growing object store"
  - "STAT-04 pinned as a byte hash of the whole file rather than a parsed dependency list: a new extra, a widened specifier and a new runtime dependency are then the same defect"
  - "pyproject.toml read as bytes, never text — a text read normalizes line endings, so a CRLF rewrite would pass a text-mode hash"

patterns-established:
  - "Structural guards are observed RED before they are trusted (15-03 precedent) — both REDs in this plan were run and the output recorded"
  - "A deliberate-RED mutation is reverted inside a `finally` block and proven byte-identical with `git diff --exit-code` before the run is called done"

requirements-completed: [PREREG-02, STAT-04]

# Metrics
duration: 20min
completed: 2026-08-13
---

# Phase 16 Plan 01: Pre-registration ordering guard + dependency freeze Summary

**Two CPU-only structural proofs landed before anything in this phase measures anything: `git merge-base --is-ancestor` binds the erasure rule's commit ahead of every v3.0 results artifact (backed by `fetch-depth: 0` in CI), and a sha256 pin freezes `pyproject.toml` byte-identical so scipy cannot arrive quietly.**

## Performance

- **Duration:** 20 min wall clock across two executor sessions (12:57:13-03:00 → 13:17-03:00)
- **Started:** 2026-08-13T15:57:13Z
- **Completed:** 2026-08-13T16:20:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- **PREREG-02 is now a checkable fact, not a claim.** `tests/test_phase16_prereg.py` asserts that commit `23a830c0181acf799dadc1e9aecdf1818d8678e2` — which added `scripts/erasure_gate.py` — is a git ancestor of the first commit adding every `results/phase16_*`, `phase17_*`, `phase18_*` artifact. A threshold chosen after seeing the data is not a threshold.
- **All three green-but-blind failure modes are closed.** Shallow clone → `assert _git("rev-parse", "--is-shallow-repository") == "false"` (assert, never `pytest.skip`). Empty glob → `assert checked`. Wrong pinned SHA → a second test asserting the SHA resolves to itself *and* touches `scripts/erasure_gate.py`.
- **CI can answer the ancestry question.** `actions/checkout@v4` defaults to `fetch-depth: 1`; Task 1 landed `fetch-depth: 0` **in an earlier commit than the test**, so the guard's first CI run is not the blind one.
- **STAT-04 has teeth.** A new runtime dependency now turns a committed test red, with a failure message that names the requirement, the two prior scipy refusals, and the only legitimate remedy.
- **Both guards were observed RED.** Recorded verbatim below.

## Task Commits

1. **Task 1: full git history in CI** — `e13dcbb` (chore) *[prior session]*
2. **Task 2: PREREG-02 ancestry + identity guard** — `4e3ab45` (test) *[prior session]*
3. **Task 3: STAT-04 pyproject freeze** — `a800490` (test) *[this session]*

## Files Created/Modified

- `.github/workflows/ci.yml` — `with: fetch-depth: 0` added to the `actions/checkout@v4` step, with a comment in the register of the existing extras comment explaining that a shallow clone makes `merge-base --is-ancestor` *error* rather than fail. The `pip install -e ".[cpu,dev,demo]"`, `ruff check . && ruff format --check .` and `pytest -q` steps are unchanged.
- `tests/test_phase16_prereg.py` — new, 127 lines, CPU-only, GPU-free, no torch. Two tests: `test_prereg_commit_precedes_every_v3_results_artifact` and `test_prereg_commit_exists_and_touches_the_erasure_gate`.
- `tests/test_package.py` — `test_pyproject_unchanged_since_v2_close` added; the two existing install-parity tests are untouched (`git diff` shows zero deletions inside either function body).

## What the STAT-04 pin actually freezes

`pyproject.toml`, 1199 bytes, sha256 `81d07d5d700000008680265659e31d9e335dec65060e7c4ae44c6247b6112bdf`, last changed at `6a46441cc17b6fc3c951a12ee0b6620b88b82d91`:

- **Runtime dependencies — the whole surface is two packages:** `numpy~=2.4`, `regex~=2026.5`. `requires-python = ">=3.10,<3.12"`.
- **Optional extras:** `cpu = torch==2.7.*`; `demo = gradio>=5,<6, matplotlib~=3.10`; `notebook = ipykernel~=7.3, nbconvert~=7.17, matplotlib~=3.10`; `dev = pytest~=9.0, ruff~=0.15, tiktoken~=0.13, isort~=8.0`.
- **Tool config also frozen** (the hash covers the whole file): setuptools `packages.find where = ["src"]`; pytest `testpaths`/`pythonpath`; isort profile; ruff `line-length = 100`, `src = ["src","tests"]`, `exclude = [".planning"]`, `lint.select = ["E","F","W","I"]`.

Freezing the tool config alongside the dependencies is a consequence of the byte-hash choice, not an oversight — a ruff `select` change is a reviewed decision in this repository too.

## Current coverage of the ancestry guard

Exactly **one** committed v3.0 artifact matches the globs today:

```
results/phase16_recall_sample.json            70dcc56062eeb13dcc0039d8ba41d88ea073c88b
```

So `checked == 1` and `untracked == []`. The `assert checked` guard is doing real work at this thinness: if that one fixture were renamed or moved out of `results/`, the guard would go red rather than silently pass having verified nothing. Coverage grows automatically as Phases 16–18 write results.

## Success criteria — ordering proof

Reused as computed by the orchestrator, not recomputed:

```
YAML=e13dcbb24b695755bc7d70b4dd05cec200b372fd    # git log --format=%H -S'fetch-depth: 0' -- .github/workflows/ci.yml | tail -1
TEST=4e3ab45e4a10c537825d345665821cbc527c7961    # git log --diff-filter=A --format=%H -- tests/test_phase16_prereg.py | tail -1
git merge-base --is-ancestor "$YAML" "$TEST"     # exit 0  ✓
```

`-S` is load-bearing here: `--diff-filter=A -- .github/workflows/ci.yml` would return the YAML file's original creation commit (`c6607fc`) and pass regardless of the order this criterion exists to check.

## Observed RED #1 — `tests/test_phase16_prereg.py` against a deliberately wrong `PREREG_COMMIT`

`PREREG_COMMIT` was temporarily repointed to `e6a8071df727b46aca126f1e2f68bc69bd7a10d1` — a commit *later* than the artifact add and one that touches only planning docs, so it exercises both the ancestry assertion and the identity assertion at once. Verbatim output (the middle of the first traceback is CPython's own `subprocess.py` `run()` source frame, elided at the marker; nothing from this repository is omitted):

```
FF                                                                       [100%]
=================================== FAILURES ===================================
____________ test_prereg_commit_precedes_every_v3_results_artifact _____________
...
                # git log is newest-first, so the commit that ADDED the file is the last entry.
                first_add = adds[-1]
>               subprocess.run(
                    ("git", "merge-base", "--is-ancestor", PREREG_COMMIT, first_add),
                    cwd=_ROOT,
                    check=True,
                )

tests/test_phase16_prereg.py:94:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

input = None, capture_output = False, timeout = None, check = True
popenargs = (('git', 'merge-base', '--is-ancestor', 'e6a8071df727b46aca126f1e2f68bc69bd7a10d1', '70dcc56062eeb13dcc0039d8ba41d88ea073c88b'),)
kwargs = {'cwd': PosixPath('/Users/juliorcoelho/PersonaCore')}
process = <Popen: returncode: 1 args: ('git', 'merge-base', '--is-ancestor', 'e6a8071d...>
stdout = None, stderr = None, retcode = 1

[... CPython subprocess.py run() source frame elided ...]

            retcode = process.poll()
            if check and retcode:
>               raise CalledProcessError(retcode, process.args,
                                         output=stdout, stderr=stderr)
E               subprocess.CalledProcessError: Command '('git', 'merge-base', '--is-ancestor', 'e6a8071df727b46aca126f1e2f68bc69bd7a10d1', '70dcc56062eeb13dcc0039d8ba41d88ea073c88b')' returned non-zero exit status 1.

/opt/homebrew/Cellar/python@3.11/3.11.15_1/Frameworks/Python.framework/Versions/3.11/lib/python3.11/subprocess.py:571: CalledProcessError
____________ test_prereg_commit_exists_and_touches_the_erasure_gate ____________
...
        touched = _git("show", "--stat", "--format=", PREREG_COMMIT)
>       assert PREREG_ARTIFACT in touched, (
            f"commit {PREREG_COMMIT} does not touch {PREREG_ARTIFACT}; it is not the "
            f"pre-registration commit. Files it does touch:\n{touched}"
        )
E       AssertionError: commit e6a8071df727b46aca126f1e2f68bc69bd7a10d1 does not touch scripts/erasure_gate.py; it is not the pre-registration commit. Files it does touch:
E         .planning/ROADMAP.md | 41 +++++++++++++++++++++++++++++++++++++++++
E          .planning/STATE.md   | 12 ++++++------
E          2 files changed, 47 insertions(+), 6 deletions(-)
E       assert 'scripts/erasure_gate.py' in '.planning/ROADMAP.md | 41 +++++++++++++++++++++++++++++++++++++++++\n .planning/STATE.md   | 12 ++++++------\n 2 files changed, 47 insertions(+), 6 deletions(-)'

tests/test_phase16_prereg.py:123: AssertionError
=========================== short test summary info ============================
FAILED tests/test_phase16_prereg.py::test_prereg_commit_precedes_every_v3_results_artifact
FAILED tests/test_phase16_prereg.py::test_prereg_commit_exists_and_touches_the_erasure_gate
2 failed in 0.15s
```

**Revert proven byte-identical:** `git diff --exit-code tests/test_phase16_prereg.py` → exit `0`; the file re-passes `2 passed in 0.25s`.

**Concern recorded, implemented as locked.** The ancestry failure surfaces as a raw `CalledProcessError` traceback, not a named assertion message — the plan prescribes `check=True` precisely so a non-ancestor raises, and it does go red, which is what PREREG-02 needs. But the diagnostic alone says only "these two SHAs, exit status 1"; a reader has to already know that the argument order means *"is the pre-registration an ancestor of the artifact add"*. The human-readable half of the story comes from the second test. Anyone touching this next could wrap the call and re-raise with a named message without weakening the check; it is deliberately not done here, because the plan's construction is the pre-registered one.

## Observed RED #2 — `tests/test_package.py` against a one-byte `pyproject.toml` change

A single `\n` byte was appended to `pyproject.toml` (1199 → 1200 bytes, sha256 `81d07d5d…` → `a3a3da5d…`). Verbatim output:

```
..F                                                                      [100%]
=================================== FAILURES ===================================
___________________ test_pyproject_unchanged_since_v2_close ____________________

    def test_pyproject_unchanged_since_v2_close():
        """STAT-04: no runtime dependency may enter v3.0 without turning a committed test red.

        The file was last changed at commit 6a46441cc17b6fc3c951a12ee0b6620b88b82d91 — diff against
        that commit to see what the pin below is protecting.

        Read as BYTES, never as text: a text read normalizes line endings, so a CRLF rewrite of the
        dependency table would pass a text-mode hash while changing the file on disk.
        """
        actual = hashlib.sha256((_ROOT / "pyproject.toml").read_bytes()).hexdigest()
>       assert actual == PYPROJECT_SHA256, (
            f"pyproject.toml changed: expected sha256 {PYPROJECT_SHA256}, got {actual}. "
            "STAT-04 requires pyproject.toml to be byte-identical at v3.0 close. This project has "
            "declined scipy in committed code twice (continual/fisher.py, scripts/phase15_stats.py), "
            "and every statistic in v3.0 is hand-rolled stdlib built on scripts/erasure_gate.py — "
            "taking a statistics dependency now, in a milestone whose entire output is trust in a "
            "measurement, would retcon both refusals. If a dependency genuinely must change, update "
            "PYPROJECT_SHA256 in the SAME commit as an explicit, reviewed decision — never silently."
        )
E       AssertionError: pyproject.toml changed: expected sha256 81d07d5d700000008680265659e31d9e335dec65060e7c4ae44c6247b6112bdf, got a3a3da5dfbaacb9f794e596dc88d0fe399ea47130ef7b829693230171450c565. STAT-04 requires pyproject.toml to be byte-identical at v3.0 close. This project has declined scipy in committed code twice (continual/fisher.py, scripts/phase15_stats.py), and every statistic in v3.0 is hand-rolled stdlib built on scripts/erasure_gate.py — taking a statistics dependency now, in a milestone whose entire output is trust in a measurement, would retcon both refusals. If a dependency genuinely must change, update PYPROJECT_SHA256 in the SAME commit as an explicit, reviewed decision — never silently.
E       assert 'a3a3da5dfbaa...230171450c565' == '81d07d5d7000...c6247b6112bdf'
E
E         - 81d07d5d700000008680265659e31d9e335dec65060e7c4ae44c6247b6112bdf
E         + a3a3da5dfbaacb9f794e596dc88d0fe399ea47130ef7b829693230171450c565

tests/test_package.py:37: AssertionError
=========================== short test summary info ============================
FAILED tests/test_package.py::test_pyproject_unchanged_since_v2_close - Asser...
1 failed, 2 passed in 0.02s
```

**Revert proven byte-identical:** restore ran inside a `finally` block; post-restore sha256 `81d07d5d700000008680265659e31d9e335dec65060e7c4ae44c6247b6112bdf` and `git diff --exit-code pyproject.toml` → exit `0`.

The interesting half is that a **single trailing newline** — the most invisible edit a file can receive — produces a completely different digest and a fully-explained failure. That is the property STAT-04 needs: there is no "small" change to this file.

## Verification

```
.venv/bin/python -m pytest tests/test_phase16_prereg.py tests/test_package.py -q
    5 passed

.venv/bin/python -m pytest -q
    416 passed, 1 skipped, 83 warnings in 121.89s (0:02:01)

.venv/bin/python -m ruff check .           All checks passed!
.venv/bin/python -m ruff format --check .  143 files already formatted
```

Baseline before this plan was `413 passed, 1 skipped`. Delta `+3` = Task 2's two tests + Task 3's one test, verified empirically rather than assumed.

## Decisions Made

- **Module docstring of `tests/test_package.py` extended by one line** (`"Install-parity smoke test (ENV-01)"` → `"Install-parity smoke test (ENV-01) and the v3.0 dependency freeze (STAT-04)"`). The plan forbids modifying the two existing *tests*, which was honored — but leaving a header claiming a single concern above a file that now holds two would misdescribe the file. This is the only line in the diff that is not a pure addition.
- **The elision in RED #1 is CPython's `subprocess.py` `run()` source frame only.** Every line originating in this repository is reproduced. Recording ~80 lines of stdlib docstring would have buried the two lines that carry the evidence.

## Deviations from Plan

### 1. [Process] Plan executed across two executor sessions

- **Cause:** the first executor was terminated by an API connection error after committing Tasks 1 and 2, before Task 3, the RED observations, and this SUMMARY.
- **Handling:** the orchestrator independently verified both prior commits before continuation — Task 1 by diff review, Task 2 by running it (`2 passed in 0.28s`) — and re-ran the ordering proof (`merge-base --is-ancestor` exit 0). This session resumed at Task 3 and redid none of it.
- **Impact on the artifact:** none. Commit content and ordering are identical to a single-session run; the ordering that PREREG-02 depends on (`fetch-depth: 0` before the test file) landed correctly in the first session.

### 2. [Environment] `make test` substituted with the venv-explicit pytest invocation

- **Plan text:** `<verification>` specifies `make test`.
- **What was run:** `.venv/bin/python -m pytest -q` (and `.venv/bin/python -m ruff check .`).
- **Why:** on this machine a bare `pytest` resolves to a pyenv shim (Python 3.12.13) and produces ~63 collection errors with `ModuleNotFoundError: No module named 'torch'` across every test file, including ones this plan never touched — an environment artifact that masquerades as a mass regression. This is a recorded fact about this box, not a change of intent; the gate that was actually run is the full suite the `make` target wraps.

### 3. [Tooling] Deliberate-RED reverts performed without `git checkout --`

- **Plan text:** RED #2's acceptance criterion says "then `git checkout pyproject.toml`".
- **What was done:** RED #1 was reverted by re-applying the exact inverse one-line edit; RED #2 was reverted by rewriting the original bytes from a backup inside a `finally` block. A session guard intercepted `git checkout -- <path>` as a destructive command.
- **Why it is equivalent or better:** the property the plan asks for is *byte-identical restoration*, and the check it names — `git diff --exit-code` — was run for both files and exited `0`. The `finally`-scoped restore additionally makes the mutation window crash-safe, which a bare `git checkout` after the fact is not: had the RED run died mid-way, `pyproject.toml` would have been left mutated.

### 4. [Tracking] STAT-04 deliberately NOT marked complete in REQUIREMENTS.md

- **Plan frontmatter:** `requirements: [PREREG-02, STAT-04]`. `PREREG-02` was marked complete; `STAT-04` was left `Pending`.
- **Why:** PREREG-02 is mapped to phase 16 alone and reads "a CPU-only test asserts the `erasure_gate.py` commit precedes every v3.0 results artifact" — that test now exists, so the requirement is genuinely met. STAT-04 is mapped to phases **16, 17 and 18** and claims `pyproject.toml` is byte-identical **at v3.0 close**. What landed here is the *enforcement mechanism*, not the outcome. Checking that box today would assert a fact about a future state, in the one milestone whose entire product is not over-claiming.
- **When it flips:** at v3.0 close, when `test_pyproject_unchanged_since_v2_close` has been green across Phases 16–18 and the hash still reads `81d07d5d…`.

### 5. [Tracking] `state.update-progress` is a no-op on this STATE.md

- `gsd-sdk query state.update-progress` returned `{"updated": false, "reason": "Progress field not found in STATE.md"}`. This repository keeps progress in a frontmatter `progress:` block rather than a body "Progress" field, so the handler finds nothing to rewrite. Harmless: `roadmap.update-plan-progress 16 16-01 complete` did land (`{"updated": true, "plan_count": 11, "summary_count": 1, "status": "In Progress"}`), which is the count that actually tracks this phase. Recorded so a future executor does not read the `false` as a failed write.

---

**Total deviations:** 5 (1 process, 1 environment, 1 tooling, 2 tracking). **Zero code deviations** — no deviation rule 1–4 fired, and nothing was auto-fixed.
**Impact on plan:** none on the artifacts. All three tasks match their specifications, including every literal the plan pinned.

## Issues Encountered

- The dangling identifier D-10 declares non-existent stayed out of every comment, docstring, test name and commit message, as the plan requires — verified by grep across all three touched files. It is deliberately not named here either: D-10's instruction is that the reference must not resurface, and re-typing it into a fresh artifact to claim it was avoided would be the very propagation it forbids. The only copy in this repository remains the one in `16-CONTEXT.md` that records its non-existence.
- No package was installed, and none was needed — consistent with T-16-SC, which is why the freeze in Task 3 costs nothing to satisfy.

## Next Phase Readiness

- **Both structural preconditions for the rest of Phase 16 are in place.** Any plan in this phase now runs under a committed ordering guard and a committed dependency freeze; a plan that reaches for scipy will find out from a red test rather than from review.
- **The guard strengthens automatically.** Every results artifact Phases 16–18 commit adds itself to `checked` with no code change.
- **One thing to watch:** the ancestry check has coverage of exactly one artifact today. That is correct and not a defect, but the first plan to write a new `results/phase16_*` file should confirm `checked` incremented rather than assume it.
- **A fourth results prefix would be silently uncovered.** `V3_ARTIFACT_GLOBS` is a literal tuple; a Phase 19 writing `results/phase19_*` would not be scanned. The `assert checked` guard catches an *empty* match set, not an *incomplete* one. Noted in the file's own comment.

## Self-Check: PASSED

All four claimed files exist on disk (`.github/workflows/ci.yml`, `tests/test_phase16_prereg.py`, `tests/test_package.py`, this SUMMARY). All three task commits resolve in `git log --all` (`e13dcbb`, `4e3ab45`, `a800490`). Both deliberate-RED reverts verified byte-identical with `git diff --exit-code` (exit 0 each). Working tree carries only the three pre-existing unrelated items this plan did not touch: modified `.gitignore`, modified `.planning/STATE.md`, untracked `AGENTS.md`.

---
*Phase: 16-weight-vs-prompt-persistence-control*
*Completed: 2026-08-13*
