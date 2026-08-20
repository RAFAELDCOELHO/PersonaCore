# Phase 20: Pre-Registration — The Three-Condition Gate - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 5 new (0 modified)
**Analogs found:** 5 / 5 (4 exact, 1 hybrid — see `scripts/mitigation_gate.py`'s AST-guard note)

Every path, line range and signature below was read from the file in this session. Where CONTEXT.md
or 20-RESEARCH.md named a range the code refuses, the correction is in **§ Citation Corrections**.

---

## File Classification

| New file | Role | Data Flow | Closest analog | Match quality |
|---|---|---|---|---|
| `scripts/mitigation_gate.py` | decision module (pin) | pure transform, no I/O | `scripts/erasure_gate.py` (291 lines, 1 commit `23a830c`) | **exact** |
| `scripts/_prose.py` | phase-neutral utility | pure transform | `scripts/_verdict.py` (30 lines) | **exact** |
| `tests/test_phase20_prereg.py` | test (ancestry + AST) | subprocess/git query | `tests/test_phase16_prereg.py:406-497` (Phase 19 twin) | **exact** |
| retention-floor driver *(name TBD)* | unpinned measurement driver | file-I/O + MPS model load | `scripts/phase19_run.py::retention` (`:787-882`) | **exact** |
| `results/phase20_retention_floor.json` | measured artifact | file-I/O (write-once) | `results/phase19_dialogue_floor.json` + `phase19_noise_floors.json` `retention_ppl_pre_erasure` block | **exact** |

---

## Pattern Assignments

### 1. `scripts/mitigation_gate.py` — decision module (pin)

**Analog:** `scripts/erasure_gate.py`. Read in full. Only import is `math` (`:68`).

#### 1a. Imports — the exact statement and its `sys.path` bootstrap

`erasure_gate.py` needs no bootstrap (it imports nothing local). `mitigation_gate.py` does, because
it must import `erasure_gate`. The bootstrap idiom is `_addendum.py:43-45`:

```python
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import _verdict  # noqa: E402  (needs the sys.path insert above)
```

`phase19_run.py:177-180` is the shorter twin, and it is the one that names *why* the flat module
name is used:

```python
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import _verdict  # noqa: E402  — the ONE anchored `## Verdict` read, shared with the clobber guard
import phase19_erasure as pin  # noqa: E402  — after the path insert, like every phase19 driver
```

The `# noqa: E402` comment is mandatory — ruff flags module-level imports after a statement.

**Importable names, each read from its defining line in `scripts/erasure_gate.py`:**

| Name | Line | Value / signature |
|---|---|---|
| `V20_MASKED_DIALOGUE_VAL_PPL` | `:75` | `4.5733` |
| `V20_EWC_RETENTION_PPL` | `:76` | `3.891140` |
| `V20_RETENTION_NOISE_FLOOR` | `:77` | `0.068930` — **D-06 supersedes for v4.0; do NOT import for the v4.0 retention cap** |
| `MARGIN_K` | `:86` | `2` |
| `CONFIDENCE` | `:89` | `0.95` |
| `wilson_upper_bound` | `:139` | `(successes, n, z=_Z_ONE_SIDED_95) -> float` — bare float, `min(1.0, …)` |
| `rule_of_three` | `:161` | `(n) -> float` |
| `ERASURE_DECISION_RULE` | `:95-127` | 6-element `tuple[str, ...]` |
| `ERASURE_GOAL_FRAMING` | `:130-134` | single `str` |
| **`VERDICTS`** | **`:136`** | **`("SUCCESS", "FAILURE", "INCONCLUSIVE")` — MUST NOT be imported (D-31)** |

#### 1b. The keyword-only signature shape — `erasure_gate.py:200-211`

```python
def erasure_succeeded(
    *,
    target_successes,
    target_questions,
    target_floor,
    nontarget_deltas,
    nontarget_noise_floor,
    dialogue_ppl,
    dialogue_ppl_noise_floor,
    retention_ppl,
    zero_results_have_nll,
):
```

Mechanically: a bare `*,` as the first parameter (`:201`); **zero `=` in the parameter list**
(`:202-210`); **no type hints anywhere in the file**; no dataclass, no TypedDict, no NamedTuple.
Return is a plain 2-tuple `(verdict: str, reasons: list[str])`.

#### 1c. Reason-string assembly — `:219`, `:231-234`, `:239-243`, `:248-251`

`reasons = []` at `:219`, then one `reasons.append(f"…")` per condition. Two conventions carry the
weight:

```python
    upper = wilson_upper_bound(target_successes, target_questions)
    a_ok = upper <= target_floor
    reasons.append(
        f"(a) target upper bound {upper:.4f} over {target_questions} questions "
        f"{'<=' if a_ok else '>'} calibrated floor {target_floor:.4f}"
    )

    margin = MARGIN_K * nontarget_noise_floor
    worst = max(nontarget_deltas) if nontarget_deltas else 0.0
    b_ok = bool(nontarget_deltas) and worst <= margin
    reasons.append(
        f"(b) worst non-target degradation {worst:.6f} "
        f"{'<=' if b_ok else '>'} k={MARGIN_K} x {nontarget_noise_floor:.6f} = {margin:.6f}"
        + ("" if nontarget_deltas else "  [NO non-target facts scored]")
    )
```

1. **The comparator is rendered into the string** — `{'<=' if a_ok else '>'}` (`:233`, `:241`), so a
   reader never re-derives which way the comparison went.
2. **Explicit format specs**: `:.4f` for PPL and bounds, `:.6f` for floors and margins.
3. **The margin is spelled out in the reason** — `k={MARGIN_K} x {floor:.6f} = {margin:.6f}` — the
   derivation appears in the output, not just the result.

#### 1d. Cap computation — the "imported, never retyped" shape, `:245-247`

```python
    dialogue_cap = V20_MASKED_DIALOGUE_VAL_PPL + MARGIN_K * dialogue_ppl_noise_floor
    retention_cap = V20_EWC_RETENTION_PPL + MARGIN_K * V20_RETENTION_NOISE_FLOOR
    c_ok = dialogue_ppl <= dialogue_cap and retention_ppl <= retention_cap
```

**Both caps are locals and are never returned.** They reach the caller only through the reason
string at `:248-251`. This is exactly what D-14's tolerance reporter exists to compensate for.

#### 1e. INCONCLUSIVE precedence — three mechanisms, all in `:212-255`

The rule is stated in the docstring at `:215-217`:

> *"All three conditions must hold for SUCCESS; INCONCLUSIVE takes precedence over FAILURE, because
> 'we could not tell' and 'it did not work' are different findings and collapsing them is the
> mistake this project's honest-negatives discipline exists to prevent."*

**(i) Early return, missing denominator** — `:221-222`:
```python
    if target_questions <= 0:
        return "INCONCLUSIVE", ["no target questions scored"]
```

**(ii) Early return, the GATE-05 shape** — `:223-227`. Returns *before any reason is appended*, so
the caller gets a single-element list. D-29's missing-replication branch reuses this shape:
```python
    if target_successes == 0 and not zero_results_have_nll:
        return "INCONCLUSIVE", [
            "target recall is zero but no teacher-forced NLL was recorded — cannot distinguish "
            "'the fact is absent' from 'the probe was too weak', so no erasure claim is admissible"
        ]
```

**(iii) LATE return — this is precedence proper** — `:253-255`. Every condition is evaluated and
rendered *first*, then the INCONCLUSIVE check intercepts before the SUCCESS/FAILURE ternary:
```python
    if not nontarget_deltas:
        return "INCONCLUSIVE", reasons
    return ("SUCCESS" if (a_ok and b_ok and c_ok) else "FAILURE"), reasons
```
**GATE-06's truncated-sweep discriminator must use form (iii)** — the reader needs the per-condition
reasons even when the verdict is INCONCLUSIVE.

#### 1f. Input-validation guard shape — `:150-153`

Copy this for any new estimator. `ValueError`, not `SystemExit`, inside a pure estimator:
```python
    if n <= 0:
        raise ValueError("n must be positive; an upper bound over zero questions is undefined")
    if not 0 <= successes <= n:
        raise ValueError(f"successes {successes} outside [0, {n}]")
```

#### 1g. Module-scope `_prove` — **NOT from `erasure_gate.py`**

⚠ **`scripts/erasure_gate.py` contains ZERO occurrences of `_prove`** (verified: `grep -c` → `0`).
The pattern lives in the drivers. Two definitions to choose between:

**Canonical driver form** — `phase19_erasure.py:164-173`. `SystemExit`, deliberately not `assert`
(an `assert` is strippable under `-O`):
```python
def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable one).

    Same register and same reason as ``phase14_recall._prove`` (``:221-224``), …
    with this module's own prefix — an abort naming the wrong driver sends its reader to the
    wrong file.
    """
    if not condition:
        raise SystemExit(f"[phase19_erasure] PROOF FAILED: {message}")
```

**Phase-neutral form** — `_addendum.py:50-53`, the one `mitigation_gate.py` should mirror (prefix
`[mitigation_gate]`):
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant — phase17/18's register, so callers catch one type."""
    if not condition:
        raise SystemExit(f"[_addendum] {message}")
```

**The module-scope invocation (D-28's and D-31's precedent)** — `phase19_erasure.py:3878-3883`.
Note the closing clause: the ancestry guard is invoked *as the deterrent inside the message*.
```python
_prove(
    tuple(_SUBCOMMAND_TABLE) == SUBCOMMANDS,
    f"the dispatch table holds {tuple(_SUBCOMMAND_TABLE)} against the committed {SUBCOMMANDS}. "
    "The published set and the runnable set must be ONE set: a name with no handler is a "
    "subcommand a later plan would have to add code for, which is a commit to this file",
)
```

#### 1h. The tolerance-reporter shape (D-14) — `phase19_erasure.py:944-961`

A pure function of its input returning a branch *name* from a closed tuple, with the tie order
stated so it is provably equivalent to a value comparison:
```python
def floor_branch(cal_rate):
    """Which of ``("reachability-min", "discount", "ceiling")`` produced the returned floor.

    So the report STATES the branch instead of leaving a reader to re-derive it — and the
    ``reachability-min`` branch is the one that has to be visible, because when it binds the floor
    equals the perfect-erasure bound and (a) clears ONLY on a perfect erasure.

    A clamp that changes nothing is not reported as having bound: at exactly ``FLOOR_CEILING`` or
    exactly ``ERASURE_FLOOR_MIN`` the discounted value IS the answer, so the branch is
    ``"discount"``. …
    """
    discounted = _discounted_floor(cal_rate)
    if discounted > FLOOR_CEILING:
        return "ceiling"
    if discounted < ERASURE_FLOOR_MIN:
        return "reachability-min"
    return "discount"
```

#### 1i. `__main__` self-check convention — `erasure_gate.py:258-291`

Verified runnable: `.venv/bin/python scripts/erasure_gate.py` prints
`erasure_gate self-check OK — 6 rule clauses committed`.

```python
if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    # Smallest runnable check that fails if the logic breaks.
    assert wilson_upper_bound(0, 100) < 0.04, "zero-success upper bound should be small but > 0"
    assert wilson_upper_bound(0, 100) > 0.0, "Wilson must NOT collapse to 0 like Wald does"
    assert abs(rule_of_three(100) - 0.03) < 1e-12
    ...
    v, rs = erasure_succeeded(..., zero_results_have_nll=True)
    assert v == "SUCCESS", (v, rs)
    v2, _ = erasure_succeeded(..., zero_results_have_nll=False)
    assert v2 == "INCONCLUSIVE", v2
    print(f"erasure_gate self-check OK — {len(ERASURE_DECISION_RULE)} rule clauses committed")
```

Five conventions to copy:
1. `# pragma: no cover - self-check, not a test suite` on the guard line.
2. Bare `assert`, no pytest, no fixtures.
3. **Both** halves of a differential pair asserted from otherwise-identical kwargs (`:267-290` is
   one kwarg block repeated with `zero_results_have_nll` flipped).
4. Failure payload carries the observed value: `assert v == "SUCCESS", (v, rs)`.
5. Terminal `print` **derives** its count (`len(ERASURE_DECISION_RULE)`) rather than retyping it.

#### 1j. The prose-constant shape — `erasure_gate.py:95-127`, `:130-134`

The rule text is a module-level tuple of long strings, one per clause, greppable and importable —
D-01's supersession record, D-05's asymmetry reason, D-10's non-transfer and D-18's two PREFERENCE
labels all belong in this shape, not in comments:
```python
ERASURE_DECISION_RULE = (
    "PRECONDITION (worth attempting): …",
    "(a) TARGET FORGOTTEN: …",
    ...
)

# The goal framing, recorded so a later reader knows what was and was not being claimed.
ERASURE_GOAL_FRAMING = (
    "Auditable forgetting with a measurable bound, plus representational consistency reported "
    "honestly. NOT 'indistinguishable from never-having-learned' — …"
)
```

Also copy the **baselines-block banner** at `:70-74` — it is the nearest self-statement of
non-amendment in the file (and it is scoped to that block only, *not* the whole file):
```python
# ---------------------------------------------------------------------------------------------
# Published v2.0 baselines. Every number below is already committed in this repository and was
# published BEFORE v3.0 began. Nothing here is new, and nothing here may be silently updated: if a
# baseline is ever re-measured, the new number goes in a DATED note, never over the top of these.
# ---------------------------------------------------------------------------------------------
V20_MASKED_DIALOGUE_VAL_PPL = 4.5733  # Phase 12 production fine-tune, results/finetune_prod.csv
```
Each constant carries an inline provenance comment naming the artifact. Copy that for `F_Y`/`F_C`,
substituting the PREFERENCE label for a provenance path.

---

### 2. `scripts/_prose.py` — phase-neutral utility

**Analog:** `scripts/_verdict.py` — read in full, 30 lines, one import (`re`).

`_prose.py` needs **zero** imports (`" ".join(text.split())`), so it is `_verdict.py` minus the
`import re`. The structure to mirror exactly:

```python
"""The ONE copy of the anchored ``## Verdict`` section read, shared by every clobber guard.

Phase-neutral and dependency-free on purpose: ``re`` is the only import, so the cheap drivers
and the CPU-only tests can both take it without dragging in torch or the fact set.

**Why one copy.** CR-02 was five hand-copied instances of the same read, four of them written as
``text.split("## Verdict")[-1]`` — the tail after the LAST occurrence of a literal that also
appears in prose. …

``None`` and an empty body are DELIBERATELY different: a file with no ``## Verdict`` section at
all is not this writer's output, and the caller must refuse it rather than overwrite it blind.
"""

import re

# Anchored on the SECTION: from a ``## Verdict`` heading at line start up to the next ``## ``
# heading or end of file. A prose mention of the literal cannot be mistaken for the section.
VERDICT_SECTION = re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)


def recorded_verdict(text):
    """The body of the FIRST ``## Verdict`` section — ``None`` when the file has no such section."""
    section = VERDICT_SECTION.search(text)
    return section.group(1) if section else None
```

Four transferable properties:
1. **Docstring opens with "The ONE copy of …"** and names every sharer.
2. **A "**Why one copy.**" paragraph naming the measured defect it closes** — for `_prose.py` that
   is `RETROSPECTIVE.md:179-181`'s line-wrapped `grep -c` miss, with `"the three\nreductions"` as
   the concrete string.
3. **"Phase-neutral and dependency-free on purpose"** — the sentence that records *why* the leading
   underscore keeps it outside every pin (D-23).
4. **One exported name, one line of logic.** `_verdict.py` exports exactly two (`VERDICT_SECTION`,
   `recorded_verdict`) and both are used by `_addendum.py:86`. `_prose.py` exports one:
   `normalized`. Callers write `normalized(phrase) in normalized(text)`.

**The consumer contract** — `_addendum.py:47` shows how a sibling in `scripts/` imports it:
```python
import _verdict  # noqa: E402  (needs the sys.path insert above)
```

---

### 3. `tests/test_phase20_prereg.py` — ancestry guard + AST guard

**Analog:** `tests/test_phase16_prereg.py` — read in full, 622 lines.

#### 3a. THE TWO SHAPES, SIDE BY SIDE. Copying the wrong one inverts this phase.

**❌ FORBIDDEN — the Phase 16 shape, `test_prereg_commit_precedes_every_v3_results_artifact`,
`:176-213`** (D-21):

```python
    checked = 0
    untracked = []
    for pattern in V3_ARTIFACT_GLOBS:
        for path in sorted(_ROOT.glob(pattern)):            # <-- WORKING-TREE glob
            rel = path.relative_to(_ROOT).as_posix()
            adds = _git("log", "--diff-filter=A", "--format=%H", "--", rel).split()
            if not adds:
                # Working-tree only: no history at all, so trivially after the pre-registration.
                # Recorded by name so this branch is a stated outcome, not an empty loop.
                untracked.append(rel)
                continue
            # git log is newest-first, so the commit that ADDED the file is the last entry.
            first_add = adds[-1]
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", PREREG_COMMIT, first_add),   # <-- ONE pinned SHA
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked, (                                        # <-- :209, UNCONDITIONAL → RED at arming time
        "no committed v3.0 results artifact was checked — the guard matched nothing. "
        f"Globs {V3_ARTIFACT_GLOBS} found only uncommitted paths {untracked}. "
        "A pre-registration guard that checks zero artifacts is green and blind."
    )
```

Fatal for Phase 20 two ways: `assert checked` at `:209` is unconditional (RED from the pin's first
commit until an artifact lands — inverting the ordering this phase exists to establish), and it pins
a hand-written SHA, which `:243-247` says *"happily permits a LATER edit to the pre-registration
after the numbers are visible, which is precisely the manoeuvre STAT-05 exists to forbid."*

**✅ COPY THIS — the Phase 19 twin, `test_phase19_prereg_is_frozen_before_every_phase19_result`,
`:406-497`.** Structurally identical to the Phase 18 shape at `:322-403`, one iteration more recent,
and its docstring states Phase 20's exact situation. Full body, `:443-497`:

```python
    artifact_glob = "results/phase19_*"
    assert artifact_glob in V3_ARTIFACT_GLOBS, (                        # :444 glob-membership
        f"{artifact_glob} is not in V3_ARTIFACT_GLOBS {V3_ARTIFACT_GLOBS} — this guard and the "
        "erasure-rule guard above would be watching two different sets of paths"
    )

    # Same reason as the three guards above: a shallow clone does not hold the earlier commit
    # objects, so it cannot answer an ancestry question — it can only fail to find one.
    assert _git("rev-parse", "--is-shallow-repository") == "false", (   # :451 shallow-clone
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )

    prereg_commits = _git("log", "--format=%H", "--", PHASE19_PREREG_ARTIFACT).split()
    assert prereg_commits, (                                            # :458 pin-exists
        f"{PHASE19_PREREG_ARTIFACT} has no commits — this guard would be scanning a "
        "pre-registration that does not exist, which is green and blind in the worst possible "
        "place. Plan 19-01 Task 1 commits it."
    )

    tracked_artifacts = _git("ls-files", artifact_glob).split()         # :464 GIT INDEX, not disk

    checked = 0
    for artifact in tracked_artifacts:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:                                   # EVERY commit, not one SHA
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked_artifacts), (   # :480 PRODUCT
        f"checked {checked} pairs but {len(prereg_commits)} pre-registration commit(s) x "
        f"{len(tracked_artifacts)} tracked artifact(s) is "
        f"{len(prereg_commits) * len(tracked_artifacts)} — a `git ls-files` pattern that matches "
        "nothing while artifacts sit on disk would otherwise make this green having checked "
        "nothing."
    )
    # The product above is satisfied by 0 == n * 0. Today both sides ARE zero and that is correct:
    # the ordering contract in scripts/phase19_erasure.py forbids a `results/phase19_*` artifact
    # existing before the pin is complete at 19-07. This ties the two together so the equivalence,
    # not the count, is what is asserted — green while no artifact is tracked, and demanding a
    # non-zero `checked` from the first one onward.
    assert bool(checked) == bool(tracked_artifacts), (                  # :492 EQUIVALENCE
        f"checked {checked} pair(s) against {len(tracked_artifacts)} tracked artifact(s) matching "
        f"`git ls-files {artifact_glob}` — those disagree, so either committed Phase 19 results "
        "went unchecked or the ancestry loop ran on paths the match set does not contain. A "
        "STAT-05 guard that checks zero artifacts once results exist is green and blind."
    )
```

**The mechanical difference, in one table:**

| | Phase 16 (`:176-213`) — FORBIDDEN | Phase 18/19 (`:322-403` / `:406-497`) — COPY |
|---|---|---|
| Artifact discovery | `_ROOT.glob(pattern)` — **working tree** | `_git("ls-files", glob)` — **git index** |
| Pre-registration side | one **hand-pinned SHA** | **every commit** touching the pin file |
| Catches a post-hoc edit? | **No** | **Yes** |
| Needs a separate identity test? | **Yes** (`:216`) | **No** — self-identifying |
| Empty match set | `assert checked` → **RED** | `bool(checked) == bool(tracked_artifacts)` → **GREEN** while tracked=0 |
| Glob-membership guard | ✗ | ✓ |
| Pin-exists guard | ✗ | ✓ |

**The Phase 19 twin's docstring, `:425-431` — Phase 20's situation verbatim.** Copy the reasoning,
substituting plan numbers:

> *"**Vacuous TODAY BY CONSTRUCTION, and that is a recorded state rather than a hidden one.** The
> pin is armed in plan 19-01 — the first plan of the phase — deliberately BEFORE any
> `results/phase19_*` artifact exists… Arming the guard first is the point — every pin commit from
> 19-01 onward is watched from the start instead of being retro-fitted once there is something to
> miss."*

**Substitution table:**

| `:406-497` | Phase 20 analogue |
|---|---|
| `artifact_glob = "results/phase19_*"` | `artifact_glob = "results/phase20_*"` |
| `V3_ARTIFACT_GLOBS` | `V4_ARTIFACT_GLOBS` (new, in `tests/test_phase20_prereg.py`) |
| `PHASE19_PREREG_ARTIFACT` | `PHASE20_PREREG_ARTIFACT = "scripts/mitigation_gate.py"` |
| `"Plan 19-01 Task 1 commits it."` | `"Plan 20-0N Task N commits it."` |
| function name | `test_phase20_prereg_is_frozen_before_every_phase20_result` |

#### 3b. `PREREG_COMMIT` / `V3_ARTIFACT_GLOBS` declaration shape — `:46-63` (verbatim)

The comments are load-bearing; D-22 needs the equivalent for `V4_ARTIFACT_GLOBS`.

```python
# PREREG-01: the commit that added scripts/erasure_gate.py. Full 40 characters, never the short
# form — an abbreviation is a prefix query against a growing object store, and this pin must stay
# unambiguous for the life of the repository.
PREREG_COMMIT = "23a830c0181acf799dadc1e9aecdf1818d8678e2"

# Every v3.0 results artifact. Phases 16, 17, 18 and 19 are the milestone whose numbers the
# pre-registered rule judges; a new phase writing results under a further prefix must be added here,
# and the `assert checked` below is what makes a silently-stale list visible. `results/phase19_*` is
# the fourth prefix and it was added BEFORE any such artifact existed — the guard watches the path
# set from the start rather than being retro-fitted once there is something to miss.
V3_ARTIFACT_GLOBS = (
    "results/phase16_*",
    "results/phase17_*",
    "results/phase18_*",
    "results/phase19_*",
)

PREREG_ARTIFACT = "scripts/erasure_gate.py"
```

**Exact sub-ranges:** `PREREG_COMMIT` comment `:46-48`, assignment `:49`; `V3_ARTIFACT_GLOBS`
comment `:51-55`, tuple `:56-61`; `PREREG_ARTIFACT` `:63`.

Note that D-33 restricts `V4_ARTIFACT_GLOBS` to `phase20_*` only. The `V3_ARTIFACT_GLOBS` comment
argues in the other direction ("a new phase writing results under a further prefix must be added
here"), so the v4.0 comment must **state the D-33 reasoning explicitly** or a reader will assume the
tuple is stale rather than deliberately narrow.

#### 3c. `_ROOT` and `_git` — `:166-173`, copy verbatim

```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
```

**argv tuple, never `shell=True`** — `artifact_glob` is passed as an argv element so the shell never
expands it and git handles it as a pathspec.

#### 3d. The AST guard register — ⚠ THE ONE PLACE NO ANALOG FITS CLEANLY

**CONTEXT.md's claim that `_GATE_MODULES` lives in `scripts/phase17_*.py` is FALSE.** Verified:
`_GATE_MODULES` appears in **no `scripts/` file**. It is declared in three test files, and the
**two forms differ** — which matters, because `mitigation_gate.py` fits neither.

**Form A — the glob register (`tests/test_phase18_prereg.py:57-71`, twin at
`tests/test_phase17_stats.py:62` + `:161-165`):**
```python
# DERIVED from a glob, never a hand-listed tuple (Phase 17 D-21). Every `scripts/phase18_*.py` a
# later plan creates enters every scan below the moment its plan commits it.
_GATE_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("phase18_*.py")))


def _collapsed_glob_guard():
    """A glob that stops matching makes every scan below green over nothing."""
    assert len(_GATE_MODULES) >= 1, (
        f"the phase18_*.py glob collapsed to {len(_GATE_MODULES)} file(s) — a broken glob makes "
        "every static guard in this module green while scanning no source at all"
    )
```
Its stated purpose (`test_phase18_prereg.py:33-37`): *"so every driver a later plan adds enters
these scans the moment it exists — a hand-listed tuple would leave each new file silently uncovered,
which is the exact blindness this pattern was introduced to close."*

**Form B — the hand-listed tuple (`tests/test_phase16_stats.py:747`)**, which is the F-08 blindness
Form A was introduced to close:
```python
_GATE_MODULES = (_DRIVER_PATH, _LADDER_PATH)
```

**Why Phase 20 needs a hybrid.** `scripts/mitigation_gate.py` is matched by **no `phase*_*.py`
glob** — so a pure Form A register would scan nothing, and `_collapsed_glob_guard()` would go red.
A pure Form B register reintroduces F-08 for `mitigation_budget.py` (Phase 23). The shape that
satisfies both is an explicit path constant **plus** a `mitigation_*.py` glob, keeping
`_collapsed_glob_guard()` intact:

```python
_MITIGATION_GATE_PATH = _REPO_ROOT / "scripts" / "mitigation_gate.py"
_GATE_MODULES = tuple(sorted((_REPO_ROOT / "scripts").glob("mitigation_*.py")))
```
plus the `test_phase18_prereg.py:497` membership assertion so the glob and the constant cannot drift:
```python
    _collapsed_glob_guard()
    assert _EXTRACTION_PATH in _GATE_MODULES, (...)
```

#### 3e. The AST import scan (D-20's no-budget-import guard) — `tests/test_phase16_stats.py:386-411`

The direct template. Verbatim:
```python
def test_stats_use_only_stdlib_and_erasure_gate():
    """STAT-04 — no scipy, no numpy RNG, and the bounds are IMPORTED rather than redefined."""
    tree = _tree(_DRIVER_PATH)
    imported = set()
    from_erasure_gate = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
            if node.module == "erasure_gate":
                from_erasure_gate.update(alias.name for alias in node.names)

    assert "scipy" not in imported
    assert "numpy" not in imported
    assert {"wilson_upper_bound", "rule_of_three"} <= from_erasure_gate

    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not ({"wilson_upper_bound", "rule_of_three"} & defined), (
        "a bound was re-implemented in this module instead of imported from erasure_gate — D-16's "
        "rule is import the instrument, never copy it, or the two silently diverge"
    )
```

**D-20's guard is this test with `assert "mitigation_budget" not in imported` added.** It covers
both `import mitigation_budget` and `from mitigation_budget import …` because both branches feed
`imported`. Note `node.module == "erasure_gate"` — a **flat module name**, not `scripts.erasure_gate`;
`mitigation_gate.py`'s import statement must match that expectation.

#### 3f. AST helpers to copy — `tests/test_phase18_prereg.py:82-102`

```python
def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _enclosing_functions(tree):
    """``node -> the innermost FunctionDef containing it``, or ``None`` for module scope.

    Module scope is recorded as ``None`` rather than dropped, because module scope is the most
    dangerous placement there is. …
    """
    owner = {}

    def walk(node, current):
        for child in ast.iter_child_nodes(node):
            inner = child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[child] = current if inner is child else inner
            walk(child, inner)

    walk(tree, None)
    return owner
```

Plus the numeric-constant scan idiom (`test_phase16_stats.py:378-383`) — the shape D-18's
two-chosen-constants audit and GATE-02's no-retyped-literal check both need:
```python
    numbers = {
        node.value
        for node in ast.walk(_tree(_DRIVER_PATH))
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
    }
    assert 6435 not in numbers
```

#### 3g. Test-module bootstrap — `tests/test_phase18_prereg.py:40-63`

```python
import ast
import importlib.util
import inspect
import pathlib
import re
import subprocess
import sys

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_EXTRACTION_PATH = _REPO_ROOT / "scripts" / "phase18_extraction.py"
```

---

### 4. Retention-floor driver (unpinned, name TBD) — MPS measurement

**Analog:** `scripts/phase19_run.py::retention` at **`:787-882`**. This is a much closer match than
`phase19_floor.py` (which is literal constants and nothing else — see §5 note). CONTEXT D-32's
"same pattern as `scripts/phase19_run.py`" resolves to *this function*, not the whole 3,036-line file.

#### 4a. The function, verbatim `:787-812` — the ON/OFF pair and its denominator refusal

```python
def retention():
    """19-10 task 3 — retention PPL on a LoRA-ADAPTED model, ON and OFF, in ONE process."""
    import numpy as np
    import phase14_recall as recall
    import phase16_persistence as persistence
    import torch

    from personacore.evaluation.perplexity import retention_perplexity
    from personacore.generation.text import undecodable_ids_mask
    from personacore.lora import adapter_disabled
    from personacore.preflight import preflight_device
    from personacore.provenance import git_sha

    device = preflight_device(strict=True)["device"]
    # `adapter_path=None` is the PRODUCTION taught adapter (`phase14_recall.ADAPTER_PATH`) — the
    # pre-erasure state every Phase 19 comparison is a movement from.
    model, cfg, tok, _forbid, _artifact = recall.load_adapted_model(device, None)
    block_size = pin.ModelConfig.block_size

    on_ppl, on_tokens = retention_perplexity(model, pin.RETENTION_BIN, block_size, device, tok)
    with adapter_disabled(model):
        off_ppl, off_tokens = retention_perplexity(
            model, pin.RETENTION_BIN, block_size, device, tok
        )
    if on_tokens != off_tokens:
        raise SystemExit(f"[phase19_run] on/off denominators differ ({on_tokens} vs {off_tokens})")
```

**Five things to copy exactly:**
1. **Every import is function-local**, including `torch` and `numpy`. The module stays inert at
   import so the AST-scan tests can `_load()` it safely.
2. `device = preflight_device(strict=True)["device"]` — the device resolution. Returns a dict; the
   `["device"]` subscript is required.
3. `recall.load_adapted_model(device, <path>)` — **positional second arg**. For Phase 20 this is the
   seed adapter path, not `None`.
4. `retention_perplexity(...)` then **`with adapter_disabled(model):`** for the OFF reading — ON
   first, OFF inside the context manager, **in one process**.
5. The denominator refusal is an **inline `raise SystemExit`**, not `_prove` — that is this
   function's committed form.

#### 4b. The alternative denominator-proof form — `phase19_erasure.dialogue_ppl_pair`, `:2704-2729`

The committed shape CONTEXT names. Cited range is **exact**; the `_prove` inside runs `:2724-2728`
(20-RESEARCH says `:2723-2727` — off by one).

```python
def dialogue_ppl_pair(model, device, forbid):
    """The (c) dialogue reading as the ON/OFF PAIR plus its shared denominator.

    ``run_collapse_control``'s own two ``masked_perplexity`` calls and its own denominator proof
    (``phase14_recall.py:1436-1450``), over the SAME committed bins — not a second corpus and not a
    second policy. …
    """
    import teach_persona as tp  # LAZY — it imports the fact set at module level

    from personacore.evaluation.perplexity import masked_perplexity
    from personacore.lora import adapter_disabled

    ppl_on, n_on = masked_perplexity(
        model, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK, tp.BLOCK_SIZE, device, forbid_ids=forbid
    )
    with adapter_disabled(model):
        ppl_off, n_off = masked_perplexity(
            model, tp.DIALOG_VAL_BIN, tp.DIALOG_VAL_MASK, tp.BLOCK_SIZE, device, forbid_ids=forbid
        )
    _prove(
        n_on == n_off,
        f"the two arms scored different denominators ({n_on} vs {n_off}) — the PPL pair is not "
        "comparable, so the delta would measure the corpus rather than the adapter",
    )
    return {"adapter_on": ppl_on, "adapter_off": ppl_off, "n_targets": n_on}
```

⚠ **The two instruments differ in one trap.** `masked_perplexity` takes `forbid_ids=forbid`
**explicitly**; `retention_perplexity` does **not** — it computes its own mask internally
(`perplexity.py:165-170`). `phase19_run.retention()` therefore discards the `forbid` from
`load_adapted_model` (`_forbid`) and passes only `tok`. Copy that; do not pass `forbid`.

#### 4c. The three instrument signatures, exact

| Symbol | Path:line | Signature | Returns |
|---|---|---|---|
| `retention_perplexity` | `src/personacore/evaluation/perplexity.py:148` | `(model, val_bin_path, block_size, device, tokenizer, batch_size=32)` | `(ppl, total_tokens)` — decorated `@torch.no_grad()` at `:147` |
| `adapter_disabled` | `src/personacore/lora/inject.py:157` | `(model: nn.Module)` — `@contextlib.contextmanager` at `:156` | context manager; raises `RuntimeError` if any module is merged |
| `load_adapted_model` | `scripts/phase14_recall.py:513` | `(device, adapter_path=None)` | `(model, cfg, tok, forbid, artifact)` |

`load_adapted_model`'s docstring, `:514-525`, states the exact discipline every threshold-setting
measurement must come off:

> *"``adapter_path`` defaults to ``ADAPTER_PATH`` … It is a PARAMETER only so plan 14-09's
> calibration driver can score the three arm-scoped calibration adapters … through this exact loader
> instead of a parallel one: **the calibration numbers that lock this file's thresholds must come off
> the same load-before-inject, ``weights_only=True`` path as the real run, or the threshold is
> derived from a different pipeline than the one it gates.**
> Both files cross the ``weights_only=True`` choke points (``load_slim`` / ``load_adapter``) — the
> restricted unpickler, zero code execution on load (T-14-22). ``torch.load`` is never called
> directly anywhere in this path."*

The load-before-inject ordering is enforced at `:542-545`:
```python
    # LOAD BEFORE INJECT — load-bearing ordering (ARCHITECTURE Anti-pattern 1). Injection grows
    # every wrapped projection's state-dict keys with a `.base.` infix, so injecting first would
    # break every key the checkpoint carries.
    model.load_state_dict(ckpt["model"])
```

#### 4d. Driver module header + write-refusal + dispatch

**The UNPINNED label** — `phase19_run.py:1-8`:
```python
"""UNPINNED THROWAWAY runner for Phase 19 — the two things the CLOSED pin cannot express.

`scripts/phase19_erasure.py` is the pre-registration and is CLOSED at 15 commits: its own `main`
docstring says a run needing something the dispatch table cannot express is "an UNPINNED THROWAWAY
(`python -c ...`, or a new `scripts/phase19_run.py`), never a commit here". This is that file, at
the name that docstring names. It adds NO measurement of its own — every number below comes out of
a committed pin function — and it exists for exactly three reasons, each measured rather than
assumed:
"""
```
Each numbered reason is a *measured* justification for why the pinned module cannot do the job. The
Phase 20 driver's header needs the same: the pin is `mitigation_gate.py`, the reason is D-24/L3 —
any later edit to the pin after `results/phase20_*` exists turns the ancestry guard permanently red.

**Write refusal** — `:250-273`. No force flag, per block and per file:
```python
def _merge_block(path, name, block):
    """Merge ONE block into ``path``. An existing block is not replaced.

    The refusal is per BLOCK rather than per file, because the blocks are measured by separate runs
    an hour apart and the file has to be appendable across them — but a block that already exists
    is recorded evidence with no force flag, exactly like an arm record.
    """
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if name in doc:
        raise SystemExit(
            f"[phase19_run] {path} already carries {name!r} — it is recorded evidence "
            "and there is no force flag. Delete the block in a reviewed commit to re-measure it."
        )
    doc[name] = block
    path.write_text(json.dumps(doc, indent=pin.JSON_INDENT, sort_keys=True), encoding="utf-8")
    print(f"[phase19_run] merged {name!r} into {path}")


def _refuse(path):
    if pathlib.Path(path).exists():
        raise SystemExit(
            f"[phase19_run] {path} already exists — it is recorded evidence and there is no force "
            "flag. Delete it in a reviewed commit if it genuinely must be regenerated."
        )
```
A single-artifact Phase 20 driver wants `_refuse` + `path.write_text(json.dumps(..., indent=…,
sort_keys=True))`. `sort_keys=True` is what makes the committed JSON diff-stable.

**Content digest** — `:246-247`, used to pin an input record into the output block:
```python
def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
```

**Subcommand dispatch + `__main__`** — `:3014-3036`:
```python
_TABLE = {
    "cal-ablate": cal_ablate,
    ...
    "retention": retention,
    ...
}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in _TABLE:
        raise SystemExit(f"usage: python scripts/phase19_run.py {{{'|'.join(_TABLE)}}}")
    _TABLE[sys.argv[1]]()
```
Note: no `# pragma: no cover` here (unlike `erasure_gate.py:258`), and no argparse — a dict lookup
over `sys.argv[1]`.

#### 4e. Verified inputs (all present locally)

| Input | Path | Status |
|---|---|---|
| seed-1337 adapter | `checkpoints/phase19_erase_dialogue_floor_seed1337_adapter.pt` | ✅ 1,352,991 bytes |
| seed-2024 adapter | `checkpoints/phase19_erase_dialogue_floor_seed2024_adapter.pt` | ✅ 1,352,991 bytes |
| retention corpus | `data/retention_val.bin` | ✅ 2,000,572 bytes |
| `pin.RETENTION_BIN` | `scripts/phase19_erasure.py:2555` | `_REPO_ROOT / "data" / "retention_val.bin"` |

⚠ `checkpoints/` is gitignored (`.gitignore:14-15`) — **CI can never re-derive this artifact**, which
is why §5's embed-everything shape is mandatory rather than nice-to-have.

---

### 5. `results/phase20_retention_floor.json` — measured artifact

**Two analogs, and Phase 20 needs both merged into one file** (Phase 19 split raw readings from
derived block across two artifacts; Phase 20 has only one).

#### 5a. Raw-readings shape — `results/phase19_dialogue_floor.json` (33 lines, full)

The two-seed protocol D-06 reuses. Note the **string** seed keys and the `recipe` block that records
which persona recipe produced the arms:
```json
{
  "config": {
    "device": "mps",
    "git_sha": "5efb01c8c0c99d160a225e49ee317aaf39e00385",
    "torch": "2.7.1"
  },
  "dialogue_ppl": {
    "1337": { "adapter_off": 4.573349214207799, "adapter_on": 5.815445876712191, "n_targets": 270203 },
    "2024": { "adapter_off": 4.573349214207799, "adapter_on": 5.810231428543841, "n_targets": 270203 }
  },
  "recipe": {
    "arm_spec": "real",
    "arms": ["erase_dialogue_floor_seed1337", "erase_dialogue_floor_seed2024"],
    "n_facts": 10,
    "prefix": "phase19",
    "replay_ratio": 1.0,
    "second_person": false
  },
  "seeds": [1337, 2024]
}
```
The `recipe` block is exactly where D-06's second stated bound ("measured on the **v3.0 persona
recipe** — `n_facts=10`, `replay_ratio=1.0`") becomes machine-readable rather than prose.

#### 5b. Derived-block shape — `phase19_run.py:830-879`, the `retention_ppl_pre_erasure` block

The key register the Phase 20 artifact should mirror. Verbatim:
```python
    block = {
        "call": f"retention_perplexity(model, RETENTION_BIN, {block_size}, device, tok)",
        "policy": "FROZEN (DEBT-02) — the dead-id mask the generation path applies; the unmasked "
        "v1.0 `perplexity` is not a substitute",
        "adapter": "checkpoints/persona_adapter.pt (UNERASED taught adapter)",
        "adapter_on": on_ppl,
        "adapter_off": off_ppl,
        "delta_on_minus_off": on_ppl - off_ppl,
        "cap": cap,
        "cap_derivation": f"{pin.V20_EWC_RETENTION_PPL} + {pin.MARGIN_K} x "
        f"{pin.V20_RETENTION_NOISE_FLOOR} (scripts/erasure_gate.py:246)",
        "adapter_on_above_cap": on_ppl > cap,
        "adapter_on_headroom": cap - on_ppl,
        "adapter_off_above_cap": off_ppl > cap,
        "bin": str(pin.RETENTION_BIN.relative_to(_REPO_ROOT)),
        "bin_bytes": pin.RETENTION_BIN.stat().st_size,
        "corpus_tokens": n_corpus,
        "n_windows": n_windows,
        "n_scored_tokens": on_tokens,
        "block_size": block_size,
        "dead_id_mask_sha256": persistence.forbid_digest(mask),
        "dead_id_mask_matches_pinned_forbid_ids": persistence.forbid_digest(mask)
        == pin.FORBID_IDS_SHA256,
        "dead_ids_masked": int(mask.sum()),
        "live_ids": int(mask.numel() - mask.sum()),
        "vocab_size": cfg.vocab_size,
        "adapted_precedent": (
            "RETENTION_MEASUREMENT clause 2's PRECEDENT census still holds exactly: …"
        ),
        "device": str(device),
        "torch": torch.__version__,
        "git_sha": git_sha(),
        "driver": "scripts/phase19_run.py retention (UNPINNED)",
    }
    for key in ("adapter_on", "adapter_off", "cap", "n_windows", "n_scored_tokens"):
        print(f"[phase19_run] retention {key} = {block[key]!r}")
    _merge_block(NOISE_FLOORS_PATH, "retention_ppl_pre_erasure", block)
```

Seven transferable conventions:
1. **`"call"`** — the literal invocation, so the reading is re-runnable from the artifact alone.
2. **`"cap_derivation"`** — the arithmetic as a **string with a source citation**
   (`"3.89114 + 2 x 0.06893 (scripts/erasure_gate.py:246)"`), verified accurate.
3. **Denominator fields are mandatory and plural** — `corpus_tokens`, `n_windows`,
   `n_scored_tokens`, `block_size`, `bin_bytes`.
4. **Instrument digest** — `dead_id_mask_sha256` plus a boolean comparing it to the pinned value.
5. **A long prose field naming what the reading is and is NOT** (`adapted_precedent`). D-06's two
   stated bounds (n=2 seeds, v3.0 recipe not a v4.0 arm) go in this slot.
6. **`device` / `torch` / `git_sha`** provenance trio, `git_sha()` from `personacore.provenance`.
7. **`"driver"` carries the `(UNPINNED)` label explicitly** — this is how a reader tells a pinned
   from an unpinned producer.

Plus the window-accounting proof, `:814-826` — the shape any denominator claim must take. It
*checks* rather than quotes:
```python
    # THE WINDOW ACCOUNTING, checked rather than quoted. `perplexity` slices `data[i : i+block+1]`,
    # so consecutive windows SHARE their boundary token — it is window k's last target and window
    # k+1's context — and every target 1..n-1 is scored exactly once. The denominator is therefore
    # `n - 1`, not the `corpus_len - n_windows` the module docstring's invariant describes …
    n_corpus = len(np.memmap(pin.RETENTION_BIN, dtype=np.uint16, mode="r"))
    n_windows = len(range(0, n_corpus - 1, block_size))
    if n_corpus - 1 != on_tokens:
        raise SystemExit(
            f"[phase19_run] window accounting disagrees: {n_corpus} - 1 != {on_tokens} over "
            f"{n_windows} windows at block {block_size}"
        )
```

#### 5c. The bit-identity control, and the `governs` field

`phase19_run.py:602-607` (`dialogue_block`) shows the `governs` field D-24 requires — a prose
pointer stating which number is operative and which is published-but-not-governing:
```python
        "governs": (
            "the MEASURED adapter-regime floor above is what `erasure_succeeded` reads: "
            "`_cmd_report` passes `dialogue_floor_from_record()` as `dialogue_ppl_noise_floor` "
            "(`phase19_erasure.py:3810`). 0.001704 is the full-fine-tune reading published beside "
            "it for the method it supplied, and it does NOT govern any Phase 19 verdict."
        ),
```
This is verbatim the sentence D-06 says the *retention* floor "inherited the same defect
unremarked" — so the Phase 20 artifact's `governs` field must state the mirror claim for
`V20_RETENTION_NOISE_FLOOR = 0.068930`.

`:578-593` shows the **re-measured-vs-published control block** — the shape D-06's seed-1337
bit-identity check should be published in:
```python
        "seed_a_remeasured_vs_published": {
            "measured_adapter_on": a["adapter_on"],
            "published_masked_adapter_on": published_on,
            "abs_delta": abs(a["adapter_on"] - published_on),
            "rel_pct": rel(a["adapter_on"], published_on),
            ...
            "plan_tolerance_pct": 0.008,
            "within_plan_tolerance": rel(a["adapter_on"], published_on) <= 0.008,
        },
```
and `:569` the identity flag D-04 depends on:
```python
        "adapter_off_identical_across_seeds": a["adapter_off"] == b["adapter_off"],
```

---

## Shared Patterns

### S1 — `_prove` / loud refusal
**Source:** `scripts/_addendum.py:50-53` (phase-neutral) · `scripts/phase19_erasure.py:164-173` (driver)
**Apply to:** `mitigation_gate.py` (module-scope proofs, D-28/D-31), retention-floor driver.
`SystemExit`, never `assert` — an `assert` is strippable under `-O`. Message prefixed with the
module's own name in brackets.

### S2 — Import by object identity, never by value
**Source:** `tests/test_phase19_erasure.py:745-748`
**Apply to:** every `erasure_gate` symbol the gate imports.
```python
import erasure_gate
assert erasure.wilson_upper_bound is erasure_gate.wilson_upper_bound
```
`is`, not `==` — a value-matching copy is a copy free to stop matching.

### S3 — Shallow-clone assertion, never a skip
**Source:** `tests/test_phase16_prereg.py:451-455` (identical text at `:183-187`, `:275-279`, `:358-362`, `:547-551`)
**Apply to:** every ancestry test in `tests/test_phase20_prereg.py`. `.github/workflows/ci.yml:19`
already sets `fetch-depth: 0`, so the assertion is answerable in CI.

### S4 — `adds[-1]` is the EARLIEST add, and the comment that says so
**Source:** `tests/test_phase16_prereg.py:293-294`, `:376-377`, `:468-470` (three verbatim copies)
```python
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
```
The consequence is spelled out at `:511-516`: *"…permanently reddening
`test_phase19_prereg_is_frozen_before_every_phase19_result`, **with no recovery**, since that guard
takes `adds[-1]`, the EARLIEST add."*

### S5 — Recorded-vacuity docstring
**Source:** `tests/test_phase16_prereg.py:425-437` (Phase 19), `:338-345` (Phase 18), `:531-537` (floor)
**Apply to:** `tests/test_phase20_prereg.py`. A guard that is green over nothing must **say so in
its own docstring**, name the plan that ends the vacuity, and point at the assertion that stops it
surviving. Three independent instances of this shape exist; it is the file's strongest convention.

### S6 — The two-file split rationale block
**Source:** `scripts/phase19_floor.py:10-48`
**Apply to:** the retention-floor driver's header (why it is unpinned) and `scripts/_prose.py`'s
header (why the leading underscore keeps it outside the pin, D-23). The reasoning to mirror:
> *"…writing it into the pin would make the pin a non-ancestor of the very artifact it was derived
> from and turn that guard permanently RED, with no recovery: the guard takes `adds[-1]`, the
> EARLIEST add, so a delete-and-re-add cycle cannot launder the ordering."*

`phase19_floor.py:25-39` also gives the "**WHAT MAKES IT HONEST ANYWAY.** Three things, none of them
a promise." register — a numbered list of *mechanisms*, each naming the test that enforces it.

### S7 — Constant + provenance comment, as data
**Source:** `scripts/phase19_floor.py:54-75` and its `EVIDENCE_ARTIFACT` map at `:167-175`
Each locked constant sits under an aligned `input: / rule: / bound by: / evidence:` comment block,
and the constant→artifact pairing is kept **as data** so a test can assert it without a second
hand-maintained copy:
```python
EVIDENCE_ARTIFACT = {
    "TARGET_FLOOR": "results/phase19_arm_cal-erased.json",
    "NONTARGET_NOISE_FLOOR": "results/phase19_noise_floors.json",
    "DIALOGUE_PPL_NOISE_FLOOR": "results/phase19_noise_floors.json",
}
```

### S8 — `append_addendum`'s live signature (D-24 correction path)
**Source:** `scripts/_addendum.py:56`
```python
def append_addendum(path, addendum, *, pending, recorded):
```
Two positional, **both keywords required**. Returns the full updated text; writes the file; prints
`[_addendum] appended a dated section to {path}`. `RETROSPECTIVE.md:182-185` records a prior plan
prescribing `placeholder=` — a keyword that does not exist.

Its refusal is real: `text.count(pending) == 1` at `:70-77`, so a second append with the same pair
raises `SystemExit` (the placeholder was consumed at `:79-80`). ⚠ **Precision correction to the
module's own docstring at `:37`** ("All three checks run on the PRODUCED BYTES"): property 1 runs on
the **input** `text`, not on `updated`. Properties 2 (`:85-90`) and 3 (`:91-96`) do run on `updated`.
A plan prescribing "check all three on the produced bytes" prescribes something the reference
implementation does not do.

---

## No Analog Found

| Item | Role | Data flow | Reason |
|---|---|---|---|
| GATE-10 capacity-comparison rule (D-25/D-26/D-27) | decision branch | pure transform | No structural-equivalence comparator exists in this repo. **New construction.** The nearest shape is `floor_branch` (§1h) — a named-branch reporter over a closed tuple — which fits the "both branches committed now, neither selectable after seeing data" requirement, but the comparison logic itself has no precedent. |
| `exists_clearing_point` mixed-arm refusal (D-28) | decision helper | pure transform | Per-arm ∃ has no analog. The **refusal** half does: `_prove` at module scope over a closed tuple (`phase19_erasure.py:3878-3883`, §1g), and the `raise ValueError` domain guard (`erasure_gate.py:150-153`, §1f). |
| D-22's throwaway-repo RED-then-GREEN fixture | test fixture | subprocess/git in `tmp_path` | No committed test in this repo builds a scratch git repo. 20-RESEARCH §3f verified the four-state machine by hand; the fixture itself is new code. Use pytest's built-in `tmp_path` (`tests/conftest.py` provides only `simulate_pascal` and `fake_lm` — neither applies). ⚠ Gotcha measured in research: `git rm` of the last file in `results/` removes the directory, so a re-add needs `mkdir -p` or a seeded `results/.keep`. |

---

## Citation Corrections

Flagged per the mapping brief. Each was read directly this session.

| Claim in CONTEXT.md / the brief | Reality | Correction |
|---|---|---|
| `_GATE_MODULES` lives in `scripts/phase17_*.py` (`20-CONTEXT.md:380`, `:393`) | **FALSE.** Zero occurrences in any `scripts/` file. | `tests/test_phase17_stats.py:62`, `tests/test_phase18_prereg.py:59` (glob form) and `tests/test_phase16_stats.py:747` (hand-listed form). Research is right; **and there are two different forms, which the research did not separate** — see §3d. `mitigation_gate.py` fits neither cleanly and needs the hybrid. |
| `erasure_gate.py:454-458` — the "must-not-amend text" | **The file is 291 lines.** | Non-amendment is enforced by `tests/test_phase18_prereg.py:212`, not by self-statement. The nearest self-statement is `erasure_gate.py:70-74`, scoped to the baselines block only. |
| `tests/test_phase16_prereg.py:45-60` for `PREREG_COMMIT` + `V3_ARTIFACT_GLOBS` | Constants at `:49` and `:56-61` | Use **`:46-63`** (as research corrected). Sub-ranges in §3b. |
| `tests/test_phase16_prereg.py:176-215` = the Phase 16 shape | Function body runs `:176-**213**`; `:216` starts the next `def`. `:209` for `assert checked` is **exact**. | Use **`:176-213`**. Off by two, harmless — but the FORBIDDEN designation is correct and confirmed. |
| `tests/test_phase16_prereg.py:322-399` = the Phase 18 shape | Function runs `:322-**403**`; `:406` starts the next `def`. | Use **`:322-403`**. Research is right. |
| Research recommends `:406-497` (the Phase 19 twin) as structurally closer | **Confirmed.** Function runs `:406-497` exactly; `:500` starts the next `def`. Bodies are line-for-line identical to `:322-403` apart from the glob, the pin constant and the plan number. | **Copy `:406-497`.** Its docstring (`:425-431`) states Phase 20's phase-zero situation verbatim; the Phase 18 twin's (`:338-345`) does not. |
| `erasure_gate`'s module-scope `_prove` pattern | **`scripts/erasure_gate.py` contains zero `_prove`** (`grep -c` → 0). | The pattern is a *driver* convention, not a gate convention. Sources in §1g. This is the one place `mitigation_gate.py` must import a habit from outside its template. |
| `phase19_erasure.dialogue_ppl_pair` at `~:2704-2729` | **Exact.** Function `:2704-2729`. | ✅ No correction. The inner `_prove` runs **`:2724-2728`** (20-RESEARCH §L1 says `:2723-2727` — off by one). |
| `erasure_gate.VERDICTS` at `:136` = `("SUCCESS","FAILURE","INCONCLUSIVE")`, must not be imported | **Confirmed** at `:136`. | ✅ D-31's proved-relabel map is the only correct path. |
| `phase19_floor.py` as the driver analog for the retention floor | It is **175 lines of literal constant assignments and one dict** — no imports, no functions, no I/O (enforced by `test_floor_lock_holds_only_literal_constants_and_nothing_else`). | **It is not a driver analog.** It is the *constants-lock* analog (§S6/S7). The driver analog is `phase19_run.py::retention` at `:787-882`. Both were named in the brief; only the second produces an artifact. |

### One trap worth surfacing that no upstream document names

`phase19_run.py:806-810` passes **`tok`, not `forbid`**, to `retention_perplexity`, discarding the
`forbid` returned by `load_adapted_model` (bound as `_forbid` at `:803`). This is correct:
`retention_perplexity` builds its own `undecodable_ids_mask` internally at `perplexity.py:165-167`,
while `masked_perplexity` requires `forbid_ids=` to be passed explicitly. A Phase 20 driver written
by analogy to `dialogue_ppl_pair` rather than to `retention()` would pass `forbid` and get a
`TypeError` — or worse, silently bind it to `batch_size`.

---

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `src/personacore/`, `results/`
**Files read this session:** 14 (`erasure_gate.py` and `test_phase16_prereg.py` in full; the rest in
targeted non-overlapping ranges)
**Verified absent (all five deliverables):** `scripts/mitigation_gate.py`, `scripts/_prose.py`,
`tests/test_phase20_prereg.py`, `results/phase20_retention_floor.json`, plus
`scripts/mitigation_budget.py` (Phase 23, not this phase)
**Git precondition re-verified:** `git log --diff-filter=A -- 'results/phase20_*'` → **EMPTY**
(D-22's clean-history requirement holds as of this mapping)
**`scripts/erasure_gate.py`:** 291 lines, one commit `23a830c`, never amended
**Project skills:** none — `.claude/skills/` and `.agents/skills/` both absent
**Pattern extraction date:** 2026-08-20
