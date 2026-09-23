# Phase 26: Empirical Privacy Audit (Canary) - Pattern Map

**Mapped:** 2026-09-10
**Files analyzed:** 7 new files (+ 2 gitignored run-time sidecar shapes)
**Analogs found:** 7 / 7 (every file has a same-role analog; the driver's analog is a whole-file template)

Every excerpt below was read from source at HEAD `efb4f0f`. Line numbers are exact at that commit.
Sibling scripts are imported via the `sys.path.insert(0, _ROOT/"scripts")` idiom (`scripts/` is not
a package) — every new module and test copies that block verbatim.

**Hard constraint carried from RESEARCH Pitfall 3:** `scripts/teach_persona.py` is digest-pinned by
`results/phase24_token_budget.json::provenance.module_sha256` (asserted live by
`tests/test_phase24_record.py:289-332`). It appears below ONLY as an import-only analog whose two inner
calls the Phase-26 loop re-issues; it is never a modification target. Same for `scripts/phase25_prereg.py`
(ancestry-guarded via the frontier; D-12 keeps it byte-identical), `scripts/phase18_extraction.py`,
`scripts/phase21_filler.py`, `scripts/phase25_record.py`, `scripts/mitigation_*.py`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/phase26_prereg.py` | config / pure-arithmetic module (dated continuation) | transform (frontier JSON -> rule resolution, thresholds, bounds, verdict) | `scripts/phase21_unit_continuation.py` (continuation-by-reference shape) + `scripts/phase25_prereg.py:43-135, 176-215` (`COMMITTED`, `_prove`, `prove_reproduction`) + `tests/test_phase25_close.py:274-281` (the rule resolver to lift) | exact (role + flow) |
| `scripts/phase26_canary.py` | driver / batch job (torch lazy) | batch + file-I/O (sidecar per point, atomic writes, heartbeat) | `scripts/phase25_recall.py` (whole file, 313 lines) | exact — copy line-for-line, swap the scorer |
| `tests/test_phase26_prereg.py` | test | request-response (git ancestry, pure-function table) | `tests/test_phase16_prereg.py:322-400` (ancestry guard) + `tests/test_phase20_prereg.py:222-243` (strictly-after conjunct) + `tests/test_phase25_close.py:284-297` (rule resolution) | exact |
| `tests/test_phase26_canary.py` | test | request-response (subprocess dry-run, tmp_path sidecars, AST, plist, sha256 link) | `tests/test_phase25_recall.py` (whole file, 296 lines) + `tests/test_phase25_driver.py:105-140, 373-389` (git-surface AST) + `tests/test_phase25_calibrate.py:570-586` (watched-RED on a copy) + `tests/test_phase25_frontier.py:407-459` (digest pins) | exact |
| `artifacts/com.personacore.phase26.canary.plist` | config (LaunchAgent) | event-driven (kickstart only) | `artifacts/com.personacore.phase25.recall.plist` (whole, 58 lines) | exact — change four strings |
| `results/phase26_operational_note.md` | doc / evidence record | file-I/O (append-only dated blocks) | `results/phase25_operational_note.md` (§12 launch record at :884, §13 close at :1104) + `tests/test_phase25_launch.py:467-479, 519-524` (heading pins) | role-match |
| `results/phase26_canary.json` | artifact (write-once, run-time) | file-I/O (emitted by `--emit`, committed by operator) | `results/phase25_recall.json` shape via `phase25_recall.emit` (`:213-285`) + frontier provenance digests (`tests/test_phase25_frontier.py:449-459`) | exact |
| `data/phase26_canary_off.json`, `data/phase26_canary_<key>.json` (gitignored) | sidecar (run-time) | file-I/O | `phase25_recall.py:90-91, 165-181` (`sidecar_path`, blob shape) | exact |

## Pattern Assignments

### `scripts/phase26_prereg.py` (config / pure arithmetic, transform)

**Analog A — the continuation-by-reference shape:** `scripts/phase21_unit_continuation.py`

**Sibling import + `_prove` + `SUPERSEDES` data** (lines 112-132):
```python
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import mitigation_unit  # noqa: E402  (needs the sys.path insert above)

# The one name this file supersedes, machine-readable so the claim is contradicted by module DATA
# and not only by the prose above. `tests/test_phase21_unit_continuation.py` reads it.
SUPERSEDES = "mitigation_unit.privacy_n"

def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``scripts/mitigation_unit.py:70``'s register.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O`` ..."""
    if not condition:
        raise SystemExit(f"[phase21_unit_continuation] {message}")
```
Phase 26: `SUPERSEDES = ("phase25_prereg.CANARY_RESERVATIONS['audit_target_rule']", "phase21_filler.GUESSABILITY_WAIVER")`; prefix `[phase26_prereg]`.

**Module-scope guard proving agreement with the pin at the published values** (lines 185-196):
```python
for _n in PUBLISHED_CAPACITIES:
    _prove(
        privacy_n(_n) == mitigation_unit.privacy_n(_n) == _n,
        f"at the published capacity N = {_n} this module returns {privacy_n(_n)!r} while the "
        f"frozen pin returns {mitigation_unit.privacy_n(_n)!r}. The continuation may only NARROW "
        "the pin's domain, never change its answer inside it — ...",
    )
del _n
```
Phase 26 equivalent: NOT at import (the frontier is 22 MB — load it inside functions). Instead expose
`resolve_audit_target(frontier)`, `audited_point_keys(frontier)`, `power_threshold(frontier)` as
functions; the tests load the frontier once (module fixture, see test analog) and assert
`resolve_audit_target(f) == "dp_n8_sigma0p000000"`, `power_threshold(f) == f["points"]["dp_n8_sigma80p000000"]["epsilon"] == accountant.epsilon_for(80.0, 200, mitigation_unit.DELTA)`.

**Analog B — the dated pre-registration header:** `scripts/phase25_prereg.py:51-55`
```python
# The date this file was committed, and the property that date certifies. Every rule below is
# dated by it: at this commit `git ls-files 'results/phase25_point_*.json'` returned NOTHING, so
# none of these rules could have been shaped by a point that did not yet exist.
COMMITTED = "2026-08-31"
POINT_RECORDS_AT_COMMIT = 0
```
Phase 26: `COMMITTED = "<date of first commit>"`, `SIDECARS_AT_COMMIT = 0`, plus
`WAIVER_CONTINUATION = {"supersedes": "phase21_filler.GUESSABILITY_WAIVER", "why": "...", "committed": COMMITTED}`.

**The rule being continued, imported BY REFERENCE** — `scripts/phase25_prereg.py:496-535`
(`CANARY_RESERVATIONS` dict; key `"audit_target_rule"`). Phase 26 does
`RULE = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` and never retypes the text.

**The resolver to lift into the module** — `tests/test_phase25_close.py:274-281` (convert the
`assert` to `_prove`):
```python
def _resolve_audit_target(artifact):
    """`CANARY_RESERVATIONS["audit_target_rule"]`, executed as written: n=8 points only, the first
    PASS in `point_keys` order, else the first n=8 point in `point_keys` order."""
    points = artifact["points"]
    n8 = [k for k in artifact["point_keys"] if points[k]["arm"].endswith("n8")]
    assert all(points[k]["canary_population"]["has_out_of_corpus_canaries"] for k in n8)
    passing = [k for k in n8 if (points[k].get("verdict") or {}).get("verdict") == "PASS"]
    return passing[0] if passing else n8[0]
```

**Reproduction gate — the int-only `_prove` register to mirror for `k, n`:** `scripts/phase25_prereg.py:176-215`
(`prove_reproduction(k, n)`): refuses `bool`, refuses non-`int`, hard `==` against
`REPRODUCTION_K = 790`, `REPRODUCTION_N = 1008`; returns `None` or raises `SystemExit`. Phase 26 CALLS
it at the control (D-15); it does not re-implement it. `epsilon_lower(members, n_in, nonmembers, n_out)`
should apply the same `isinstance(x, int) and not isinstance(x, bool)` refusal to its four counts.

**The two Wilson bounds — IMPORTED (the D-09 formula body is RESEARCH Code Example 4):**
- `scripts/erasure_gate.py:90` `_Z_ONE_SIDED_95 = 1.6448536269514722`; `:136` `VERDICTS = ("SUCCESS", "FAILURE", "INCONCLUSIVE")`; `:139-159` `wilson_upper_bound(successes, n, z=_Z_ONE_SIDED_95)` -> `min(1.0, (centre + spread) / denom)`, `ValueError` on `n <= 0`.
- `scripts/phase20_gate_coverage.py:124-186` `wilson_lower_bound(successes, n, z=erasure_gate._Z_ONE_SIDED_95)` -> `if successes == 0: return 0.0` (exact) else `max(0.0, (centre - spread) / denom)`.
- `scripts/mitigation_unit.py:85` `PRIVACY_UNIT = "one taught fact"`; `:171` `DELTA = 1e-5`.

Sibling import idiom for these (from `scripts/phase20_gate_coverage.py:95-99`):
```python
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import erasure_gate  # noqa: E402  (needs the sys.path insert above)
```

**Verdict domain in the gate's register:** `VERDICTS = ("BROKEN", "CONSISTENT", "INCONCLUSIVE")` as a
module tuple, mirroring `erasure_gate.py:136`. Reasons list carries the numbers (see Shared Patterns).

---

### `scripts/phase26_canary.py` (driver, batch + file-I/O)

**Analog:** `scripts/phase25_recall.py` — whole file is the template. Copy it, then replace
`tp.score_arm(...)` with the per-fact loop and add `score_off_once` + the D-19 refusals in `emit`.

**Imports pattern** (lines 33-60) — module scope imports ONLY CPU-safe siblings:
```python
import argparse
import datetime
import hashlib
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_prereg  # noqa: E402  (scripts/ is not a package)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same — CPU-safe at import; torch stays lazy)
import phase25_venue  # noqa: E402  (same)

from personacore.provenance import git_sha  # noqa: E402

RECORD = _ROOT / "results" / "phase25_recall.json"
SIDECAR_DIR = _ROOT / "data"
INSTRUMENT = "teach_persona.score_arm"
```
Phase 26: add `import phase26_prereg`; `RECORD = _ROOT / "results" / "phase26_canary.json"`;
`INSTRUMENT = "phase14_recall.complete_question + score_question (score_items' two calls, per fact)"`.
`phase14_factset`, `phase14_recall`, `phase21_filler`, `teach_persona`, `personacore.lora` are imported
INSIDE `score_point` / `score_off_once` only (the AST test asserts this; add `phase21_filler` to the
forbidden top-level set because it imports `phase14_factset` at module scope).

**`_prove` / helpers / sidecar path** (lines 71-91):
```python
def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_recall] {message}")

def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def _rel(path):
    """Repo-relative when inside the root; the path as given otherwise (tests use tmp dirs)."""
    path = pathlib.Path(path)
    return str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)

def sidecar_path(point_key):
    return SIDECAR_DIR / f"phase25_recall_{point_key}.json"
```
Phase 26: `sidecar_path(key) -> SIDECAR_DIR / f"phase26_canary_{key}.json"`; `off_sidecar_path() -> SIDECAR_DIR / "phase26_canary_off.json"`. Validate `key` through `phase25_prereg.point_record_path`'s charset rule (`:276-296`) or restrict to `phase26_prereg.audited_point_keys(frontier)` membership.

**Record access — Phase 26 reads the FRONTIER once, not per-point records** (analog lines 94-97 read `results/phase25_point_<key>.json`; Phase 26 replaces with):
```python
def frontier():
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))
```
(`phase25_record.py:107` `FRONTIER_RECORD = _ROOT/"results"/"phase25_frontier.json"`; cache it in a module-level `functools.lru_cache` or pass it down — it is 22 MB.)

**Core pattern: adapter hash check -> sidecar reuse-or-refuse -> dry-run -> lazy imports -> heartbeat -> score -> atomic write** (lines 114-185):
```python
def score_point(point_key, *, dry_run=False, heartbeat_path=None):
    record = point_record(point_key)
    arm = record["arm"]
    adapter = _ROOT / record["adapter_path"]
    _prove(adapter.exists(), f"{point_key}: adapter {record['adapter_path']} is not on disk")
    _prove(
        _sha256(adapter) == record["adapter_sha256"],
        f"{point_key}: {record['adapter_path']} hashes to a different adapter than the record "
        "pins; a reading over the wrong weights is not this point's reading",
    )
    ...
    sidecar = sidecar_path(point_key)
    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == record["adapter_sha256"],
            f"{sidecar.name} describes adapter {blob['adapter_sha256']!r}, not the record's "
            f"{record['adapter_sha256']!r} — REFUSED, not reused",
        )
        print(f"[phase25_recall] {point_key}: REUSING {_rel(sidecar)}")
        return "reused", blob

    if dry_run:
        print(f"[phase25_recall] {point_key}: DRY RUN — would score {record['adapter_path']}")
        return "dry_run", None

    import phase14_factset as fs  # LAZY — torch-touching
    import teach_persona as tp  # LAZY — torch-touching

    heartbeat_path = phase25_run.HEARTBEAT_PATH if heartbeat_path is None else heartbeat_path
    state = {"point": point_key, "stage": "score", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        device = phase25_run.device()
        started = time.time()
        scored = tp.score_arm(arm, fs.LOCKED_FACTS, adapter, device)   # <-- REPLACE (see below)
        scoring_seconds = time.time() - started
    finally:
        stop.set()
        thread.join()

    blob = {
        "point_key": point_key,
        "arm": arm,
        "adapter_path": record["adapter_path"],
        "adapter_sha256": record["adapter_sha256"],
        ...
        "scoring_seconds": scoring_seconds,
        "instrument": INSTRUMENT,
        "instrument_git_sha": git_sha(),
        "device": device,
        "utc": _utc(),
    }
    phase25_run.atomic_write_json(sidecar, blob)
    k, n = blob["taught_recall"]["numerator"], blob["taught_recall"]["denominator"]
    print(f"[phase25_recall] {point_key}: taught recall {k}/{n} in {scoring_seconds:.1f}s")
    phase25_run.beat(heartbeat_path, point=point_key, stage="done", shape=None, draw_index=None)
    return "scored", blob
```
Phase 26 changes inside this frame: (a) `record = frontier()["points"][point_key]`; (b) replace the
`score_arm` line with `pr.load_adapted_model(device, adapter_path=adapter)` then four `_score_list`
calls (IN-taught, IN-heldout, OUT-taught, OUT-heldout — each its own `enumerate` from 0, Pitfall 1);
(c) at the control only, `phase25_prereg.prove_reproduction(int(in_taught["k"]), int(in_taught["n"]))`
BEFORE the sidecar is written; (d) add `torch_version`, `platform` to the blob (Pitfall 8); (e) blob
carries `per_question` + `per_fact` for all four lists (RESEARCH Code Example 2).

**The scorer this loop replays — IMPORT-ONLY analog `scripts/teach_persona.py:2403-2437` (`score_items`), the two calls kept, the aggregation changed to per-fact:**
```python
    for index, (family_id, fact, question) in enumerate(items):
        drawn = pr.complete_question(model, tok, question, device, forbid, index=index)
        k, n = pr.score_question(drawn["completions"], fact.value)
```
and the items builder — IMPORT-ONLY analog `scripts/teach_persona.py:2381-2400` (`calibration_items`), which calls `fs.render_family(family_id, fact)` WITHOUT `forms=` at `:2396`; Phase 26's `_items(facts, family_ids, forms=None)` is the same 6 lines with `forms=forms` passed through (RESEARCH Code Example 1). A test asserts `_items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS) == tp.calibration_items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)` (exact list equality => identical seeds).

**The OFF arm — IMPORT-ONLY analog `scripts/teach_persona.py:2459-2465` (`score_arm`'s OFF pass):**
```python
    model, _cfg, tok, forbid, _artifact = pr.load_adapted_model(device, adapter_path=adapter_path)
    ...
    with adapter_disabled(model):
        off_taught = score_items(model, tok, device, forbid, taught, label=f"{arm} taught OFF")
        off_heldout = score_items(model, tok, device, forbid, heldout, label=f"{arm} held-out OFF")
```
`adapter_disabled` is `from personacore.lora import adapter_disabled` (`src/personacore/lora/inject.py:157`, contextmanager). Phase 26 `score_off_once()` hosts the OFF pass on the CONTROL adapter, writes `data/phase26_canary_off.json` with `base_sha256 = _sha256(pr.CONVBASE_SLIM)` (`phase14_recall.py:81`; measured `550bb8b0...1f056`) and `host_adapter_sha256`.

**Filler rendering (OUT) — IMPORT-ONLY analog `scripts/phase21_filler.py:416-439` (`render_filler_episodes`):**
```python
    for fact in facts:
        for family_id in sorted(family_ids):
            episodes.extend(fs.render_family(family_id, fact, forms=FILLER_SLOT_FORMS))
```
`FILLER_FACTS` (`:175`), `FILLER_SLOT_FORMS` (`:61`), `GUESSABILITY_WAIVER` (`:391`). `sorted(family_ids)` is load-bearing (frozenset iteration order is process-dependent — measured in that docstring).

**Emit: write-once refusal FIRST, then set-equality against the pinned keys, then the artifact** (lines 213-285):
```python
def emit(out_path=RECORD, *, overwrite=False):
    out_path = pathlib.Path(out_path)
    _prove(
        overwrite or not out_path.exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. The sanctioned route deletes it in "
        "its own commit, then re-runs against a clean tree (scripts/phase25_record.py "
        "RERUN_ROUTE); results/phase25_frontier.json pins these bytes. Pass --force to overwrite "
        "deliberately.",
    )
    pinned = tuple(phase25_record.ORDERED_POINT_KEYS())
    points, sources = {}, {SOURCE_POINT_RECORD: 0, "sidecar": 0}
    for key in pinned:
        record = point_record(key)
        ...
        sidecar = sidecar_path(key)
        _prove(sidecar.exists(), f"{key}: no sidecar at {_rel(sidecar)} — not scored")
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == record["adapter_sha256"],
            f"{key}: sidecar adapter {blob['adapter_sha256']!r} != record "
            f"{record['adapter_sha256']!r}",
        )
        points[key] = {**blob, "source": _rel(sidecar)}
        sources["sidecar"] += 1

    _prove(
        set(points) == set(pinned) and len(points) == len(pinned),
        f"{len(points)} entries against {len(pinned)} pinned keys; missing "
        f"{sorted(set(pinned) - set(points))} extra {sorted(set(points) - set(pinned))}",
    )
    ...
    blob = {
        "governs": DEVIATION,
        "instrument": INSTRUMENT,
        ...
        "emitted_utc": _utc(),
        "emitted_git_sha": git_sha(),
        "points": points,
    }
    phase25_run.atomic_write_json(out_path, blob)
    print(f"[phase25_recall] emitted {out_path} ({sources})")
    return blob
```
Phase 26 `emit` order (D-19, D-13, D-03, D-05): (1) overwrite refusal; (2) `pinned = phase26_prereg.audited_point_keys(frontier)` (16, control first — `[k for k in phase25_record.ORDERED_POINT_KEYS() if k.startswith("dp_n8")]`); (3) `_prove(off_sidecar.exists() ...)` + `_prove(off["base_sha256"] == _sha256(CONVBASE_SLIM))`; (4) the 16-sidecar loop above, naming missing keys AND pointing at `results/phase26_operational_note.md` in the message; (5) D-07 exclusions from the off sidecar -> `n_out`; (6) `auditor_ceiling(n_in, n_out)` and `reachable_claims`; (7) power gate at the control; (8) 15 verdicts in key order with `reasons`; (9) top-level `frontier_path`, `frontier_sha256 = _sha256(phase25_record.FRONTIER_RECORD)`, `frontier_bytes`, `prereg_module_sha256 = _sha256(scripts/phase26_prereg.py)`, `governs` quoting `phase25_gate05.FILLER_EXPOSURE_OMITTED` (`:280`) and `phase18_extraction.CLUSTER_DENOMINATOR_RATIONALE` (`:2010`); (10) `atomic_write_json`.

**Parser / main** (lines 288-313):
```python
def build_parser():
    parser = argparse.ArgumentParser(description="Score recall on the 42 unscored sweep adapters.")
    parser.add_argument("--points", nargs="+", default=None)
    parser.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--emit", action="store_true", help="assemble results/phase25_recall.json")
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing artifact (25-REVIEW WR-01)"
    )
    return parser

def main(argv=None):
    print(phase25_venue.launch_banner(), flush=True)
    args = build_parser().parse_args(argv)
    if args.emit:
        emit(overwrite=args.force)
        return 0
    points = phase25_record.ORDERED_POINT_KEYS() if args.points is None else tuple(args.points)
    for key in points:
        score_point(key, dry_run=args.dry_run, heartbeat_path=pathlib.Path(args.heartbeat))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
Phase 26 `main`: `score_off_once(dry_run=..., heartbeat_path=...)` runs BEFORE the point loop (D-17: once, same seeds); default `points = phase26_prereg.audited_point_keys(frontier())`.

**Run-kit functions CALLED, signatures (from `scripts/phase25_run.py`):**
- `:118` `atomic_write_json(path, blob) -> path` — `json.dumps(blob, sort_keys=True)`, temp in destination dir, `fsync`, `os.replace`, unlink on `BaseException`.
- `:286` `HEARTBEAT_PATH = _ROOT / "data" / "phase25_heartbeat.jsonl"`; `:291` `HEARTBEAT_FIELDS = ("utc","point","stage","shape","draw_index")`.
- `:298` `beat(heartbeat_path, *, point, stage, shape, draw_index) -> dict` (append one JSON line).
- `:350` `start_heartbeat(heartbeat_path, state, *, seconds=None) -> (stop_event, thread)`.
- `:407` `device()` -> preflighted device string, resolved once per process.
- `:751-753` `ALLOWED_GIT_ACTIONS = ("add", "commit")`, `READ_ONLY_GIT_ACTIONS = ("ls-files", "show", "rev-parse", "status")` — Phase 26's driver builds NO `["git", ...]` argv at all.

---

### `tests/test_phase26_prereg.py` (test, git ancestry + pure-function table)

**Analog A — ancestry guard:** `tests/test_phase16_prereg.py:322-400` (`test_phase18_prereg_is_frozen_before_every_phase18_result`)

**Helper** (`tests/test_phase16_prereg.py:170-174`):
```python
def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
```

**The guard body** (lines 356-400) — copy with `PHASE18_PREREG_ARTIFACT -> "scripts/phase26_prereg.py"`, `artifact_glob -> "results/phase26_*"`:
```python
    assert _git("rev-parse", "--is-shallow-repository") == "false", (
        "shallow clone: the pre-registration commit objects are absent, so this guard cannot "
        "distinguish 'the ordering holds' from 'the ordering was never checked'. "
        "Set `fetch-depth: 0` on actions/checkout (see .github/workflows/ci.yml)."
    )

    prereg_commits = _git("log", "--format=%H", "--", PHASE18_PREREG_ARTIFACT).split()
    assert prereg_commits, (...)

    tracked_artifacts = _git("ls-files", artifact_glob).split()

    checked = 0
    for artifact in tracked_artifacts:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        # git log is newest-first, so the commit that ADDED the file is the last entry. Taking the
        # earliest add is what makes a delete-and-re-add cycle unable to launder the ordering.
        first_add = adds[-1]
        for prereg in prereg_commits:
            subprocess.run(
                ("git", "merge-base", "--is-ancestor", prereg, first_add),
                cwd=_ROOT,
                check=True,
            )
            checked += 1

    assert checked == len(prereg_commits) * len(tracked_artifacts), (...)
    assert bool(checked) == bool(tracked_artifacts), (...)
```
Add the **strictly-after conjunct** from `tests/test_phase20_prereg.py:227-239` inside the inner loop, before the `merge-base` call:
```python
            assert prereg != first_add, (
                f"{prereg_artifact} and {artifact} were committed in the SAME commit {prereg} — "
                "the pre-registration must land STRICTLY BEFORE the artifact it pins, or it is "
                "not a pre-registration at all. `git merge-base --is-ancestor X X` exits 0, so "
                "the ancestry check below cannot see this on its own."
            )
```
Second guard (D-12, `phase25_prereg.py` byte-identical): same loop with `prereg path = "scripts/phase25_prereg.py"` and the tracked set = `["results/phase25_frontier.json"] + git ls-files results/phase26_*`. Also keep `tests/test_phase25_close.py:321-324` green (frontier has exactly one commit; `git diff` empty).

**Analog B — rule resolution + prose clauses through `_prose.normalized`:** `tests/test_phase25_close.py:284-297`
```python
def test_the_audit_target_rule_resolves_to_exactly_one_point():
    rule = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]
    for clause in (
        "restrict to n=8 points",
        "FIRST in `point_keys` order whose verdict is PASS",
        "the pre-registered null",
    ):
        assert _prose.normalized(clause) in _prose.normalized(rule)
    artifact = json.loads(_text(_FRONTIER))
    target = _resolve_audit_target(artifact)
    assert target == "dp_n8_sigma0p000000", target
    assert target in artifact["point_keys"]
```
Phase 26: call `phase26_prereg.resolve_audit_target(artifact)` (the function now lives in the module) and additionally assert `phase26_prereg.RULE is phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]` (by reference).

**Frontier loaded once — module fixture:** `tests/test_phase25_frontier.py:62-64`
```python
@pytest.fixture(scope="module")
def artifact():
    return json.loads(record.FRONTIER_RECORD.read_text(encoding="utf-8"))
```

**Formula table — parametrize over the six hand-computed rows** (RESEARCH Code Example 4 pins; `pytest.approx(abs=1e-4)`):
`(790,1008,0,784)->(0.7617,0.0034,5.4003,1.4306)`, `(1008,1008,0,784)->(0.9973,0.0034,5.6699,5.9196)`, `(8,8,0,56)->(0.7473,0.0461,2.7859,1.3283)`, `(7,8,0,56)->(0.5889,0.0461,2.5476,0.8416)`, `(8,8,1,56)->(0.7473,0.0762,2.2836,1.2962)`, `(0,1008,0,784)->(0.0,0.0034,None,-0.0035)` with `"TPR_lb <= delta"` named in `degenerate`.

**Power threshold:** `phase26_prereg.power_threshold(artifact) == artifact["points"]["dp_n8_sigma80p000000"]["epsilon"] == pytest.approx(0.6339783761989397) == accountant.epsilon_for(80.0, 200, mitigation_unit.DELTA)` (`src/personacore/privacy/accountant.py:819`, three positional args).

---

### `tests/test_phase26_canary.py` (test, subprocess / tmp_path / AST / plist / sha256)

**Analog:** `tests/test_phase25_recall.py` — whole file. Copy the structure (a)–(e) and WR-01.

**Imports + skip markers** (lines 9-43):
```python
import ast
import json
import pathlib
import plistlib
import shutil
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import phase25_recall as recall  # noqa: E402  (scripts/ is not a package)
import phase25_record  # noqa: E402  (same)

_PLIST = _ROOT / "artifacts" / "com.personacore.phase25.recall.plist"
_SWEEP_PLIST = _ROOT / "artifacts" / "com.personacore.phase25.sweep.plist"
_KEYS = tuple(phase25_record.ORDERED_POINT_KEYS())

_ADAPTERS_ON_DISK = (_ROOT / "checkpoints").is_dir() and all(
    (_ROOT / recall.point_record(k)["adapter_path"]).exists() for k in _KEYS
)
needs_adapters = pytest.mark.skipif(
    not _ADAPTERS_ON_DISK,
    reason="the 44 sweep adapters live under gitignored checkpoints/ — sweep host only",
)
needs_plutil = pytest.mark.skipif(shutil.which("plutil") is None, reason="plutil is macOS-only")
```
Phase 26: `_KEYS = phase26_prereg.audited_point_keys(frontier)` (16); `_ADAPTERS_ON_DISK` reads `adapter_path` from the frontier's points; add a `needs_mps`/sweep-active gate via `tests/conftest.py::sweep_is_active()` (`conftest.py:51-60`, env var `PERSONACORE_SWEEP_ACTIVE`) for the D-15 live-reproduction test.

**`--dry-run` in a FRESH interpreter, then AST no-top-level-torch** (lines 100-134):
```python
@needs_adapters
def test_the_dry_run_and_reuse_paths_never_import_torch():
    script = (
        "import json, pathlib, sys, tempfile\n"
        f"sys.path.insert(0, {str(_SCRIPTS)!r})\n"
        "import phase25_recall as r\n"
        "tmp = pathlib.Path(tempfile.mkdtemp())\n"
        "r.SIDECAR_DIR = tmp\n"
        "key = 'dp_n8_sigma0p500000'\n"
        "rec = r.point_record(key)\n"
        "side = {'adapter_sha256': rec['adapter_sha256'], 'taught_recall': {}}\n"
        "r.sidecar_path(key).write_text(json.dumps(side))\n"
        "assert r.score_point(key, dry_run=False)[0] == 'reused'\n"
        "assert r.score_point('dp_n64_sigma0p500000', dry_run=True)[0] == 'dry_run'\n"
        "assert r.score_point('dp_n8_sigma0p000000', dry_run=True)[0] == 'point_record'\n"
        "print('torch' in sys.modules)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, cwd=_ROOT
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert completed.stdout.strip().splitlines()[-1] == "False"
    tree = ast.parse((_SCRIPTS / "phase25_recall.py").read_text(encoding="utf-8"))
    top_level = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    } | {node.module for node in tree.body if isinstance(node, ast.ImportFrom)}
    assert not top_level & {"torch", "teach_persona", "phase14_factset", "phase14_recall"}
```
Phase 26: walk `score_off_once(dry_run=True)` + all 16 `score_point(..., dry_run=True)`; forbidden set gains `"phase21_filler"`.

**Sidecar reuse / refusal on `tmp_path`** (lines 150-169):
```python
@needs_adapters
def test_a_matching_sidecar_is_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    key = "dp_n8_sigma0p500000"
    recall.sidecar_path(key).write_text(json.dumps(_fake_sidecar(key)), encoding="utf-8")
    status, blob = recall.score_point(key, dry_run=False)
    assert status == "reused"

@needs_adapters
def test_a_sidecar_for_a_different_adapter_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    key = "dp_n8_sigma0p500000"
    recall.sidecar_path(key).write_text(
        json.dumps(_fake_sidecar(key, sha="0" * 64)), encoding="utf-8"
    )
    with pytest.raises(SystemExit) as excinfo:
        recall.score_point(key, dry_run=True)
    assert "REFUSED, not reused" in str(excinfo.value)
```
`_fake_sidecar(key, *, sha=None)` (lines 46-72) builds the blob from the record's `adapter_sha256` — Phase 26's fixture builds `per_fact`/`per_question` counts for four lists plus the off sidecar with `base_sha256`.

**Emit refusal on a partial set** (lines 204-212):
```python
def test_the_emitter_refuses_a_missing_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(recall, "SIDECAR_DIR", tmp_path)
    for key in _KEYS[:-1]:
        ...write fake sidecar...
    with pytest.raises(SystemExit) as excinfo:
        recall.emit(tmp_path / "recall.json")
    assert "not scored" in str(excinfo.value)
    assert not (tmp_path / "recall.json").exists()
```
Phase 26 also asserts the message names `results/phase26_operational_note.md` (D-19).

**Write-once refusal against the LIVE file** (lines 282-296):
```python
def test_emit_refuses_to_overwrite_the_committed_artifact():
    assert recall.RECORD.exists()
    before = recall.RECORD.read_bytes()
    with pytest.raises(SystemExit) as excinfo:
        recall.emit()
    assert "REFUSING to overwrite it" in str(excinfo.value)
    assert "--force" in str(excinfo.value)
    assert recall.RECORD.read_bytes() == before
```
Phase 26: guard with `if canary.RECORD.exists()` — before the run the artifact is ABSENT; use the `bool(checked) == bool(tracked)` idiom so the test is honest in both states (RESEARCH Validation row D-18).

**Plist tests** (lines 218-248):
```python
def _plist(path):
    with path.open("rb") as handle:
        return plistlib.load(handle)

@needs_plutil
def test_the_recall_agent_does_not_start_itself_and_lints():
    parsed = _plist(_PLIST)
    assert parsed["KeepAlive"] is False
    assert parsed["RunAtLoad"] is False
    assert parsed["Label"] == "com.personacore.phase25.recall"
    assert subprocess.run(["plutil", "-lint", str(_PLIST)], capture_output=True).returncode == 0

def test_the_recall_agent_mirrors_the_sweep_agents_wrapper_and_heartbeat():
    ours, sweep = _plist(_PLIST), _plist(_SWEEP_PLIST)
    assert ours["ProgramArguments"][:3] == sweep["ProgramArguments"][:3]  # caffeinate -dims python
    assert ours["ProgramArguments"][3].endswith("scripts/phase25_recall.py")
    beat = ours["ProgramArguments"][ours["ProgramArguments"].index("--heartbeat") + 1]
    assert beat == sweep["ProgramArguments"][sweep["ProgramArguments"].index("--heartbeat") + 1]
    assert ours["WorkingDirectory"] == sweep["WorkingDirectory"]
    assert pathlib.Path(ours["WorkingDirectory"]).name == _ROOT.name
    if pathlib.Path(ours["WorkingDirectory"]).is_dir():
        assert ours["WorkingDirectory"] == str(_ROOT)
    assert ours["StandardOutPath"] != sweep["StandardOutPath"]
    assert ours["EnvironmentVariables"]["PERSONACORE_SWEEP_ACTIVE"] == "1"
```
Phase 26: compare `com.personacore.phase26.canary.plist` against `com.personacore.phase25.recall.plist`.

**Git-surface AST (driver must build no `["git", ...]` argv)** — `tests/test_phase25_driver.py:105-140`:
```python
def _git_argv_subcommands(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if not (isinstance(first, ast.Constant) and first.value == "git"):
            continue
        for element in node.elts[1:]:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.append((element.value, element.lineno, _enclosing_function(tree, element)))
                break
    return found

def _git_surface_failure(path, allowed):
    offenders = [row for row in _git_argv_subcommands(path) if row[0] not in allowed]
    return offenders, "\n".join(...)
```
Phase 26: `allowed = set(phase25_run.READ_ONLY_GIT_ACTIONS)`; assert `_git_argv_subcommands(_DRIVER) == []` (empty — `git_sha()` from `personacore.provenance` is the only git touch and it is not an argv literal in the driver). Keep the planted-push RED (`:392-420`) on a `tmp_path` copy.

**Watched-RED on a `tmp_path` COPY, never the tree** — `tests/test_phase25_calibrate.py:570-586`:
```python
def test_the_freshness_guard_goes_red_on_one_edited_byte(tmp_path):
    original = cal.MODULE_PATH.read_bytes()
    recorded = _clip()["provenance"]["module_sha256"]
    assert hashlib.sha256(original).hexdigest() == recorded

    edited = tmp_path / "phase25_calibrate.py"
    edited.write_bytes(original + b"\n# one byte more\n")
    assert hashlib.sha256(edited.read_bytes()).hexdigest() != recorded

    assert cal.MODULE_PATH.read_bytes() == original
```
Phase 26 power-gate RED: copy the (fake or real) artifact to `tmp_path`, set `power_gate.passed = True` while `control.epsilon_lower < threshold`, re-run `phase26_prereg.verdict(...)`/the re-derivation, assert it disagrees; assert the real artifact bytes unchanged.

**Digest-link test (both ways)** — `tests/test_phase25_frontier.py:449-459`:
```python
def test_the_artifact_carries_the_pre_registered_commitments(artifact):
    provenance = artifact["provenance"]
    as_json = lambda value: json.loads(json.dumps(value))  # noqa: E731
    assert provenance["canary_reservations"] == as_json(phase25_prereg.CANARY_RESERVATIONS)
    for key, point in artifact["points"].items():
        assert provenance["inputs"]["point_records"][key]["sha256"] == (
            hashlib.sha256((_ROOT / point["record"]).read_bytes()).hexdigest()
        ), key
```
Phase 26: `hashlib.sha256(FRONTIER_RECORD.read_bytes()).hexdigest() == canary["frontier_sha256"]`; for each of the 16 keys `canary["points"][k]["adapter_sha256"] == frontier["points"][k]["adapter_sha256"]`; `canary["prereg_module_sha256"] == sha256(scripts/phase26_prereg.py)`.

---

### `artifacts/com.personacore.phase26.canary.plist` (config, event-driven)

**Analog:** `artifacts/com.personacore.phase25.recall.plist` — copy whole (58 lines), change exactly: `Label` (line 15) -> `com.personacore.phase26.canary`; `ProgramArguments[3]` (line 31) -> `/Users/juliorcoelho/PersonaCore/scripts/phase26_canary.py`; `StandardOutPath`/`StandardErrorPath` (lines 40, 42) -> `logs/phase26_canary.{out,err}`; the header comment (lines 3-11). Keep unchanged:
```xml
  <key>KeepAlive</key>
  <false/>
  <key>RunAtLoad</key>
  <false/>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-dims</string>
    <string>/Users/juliorcoelho/PersonaCore/.venv/bin/python</string>
    <string>/Users/juliorcoelho/PersonaCore/scripts/phase25_recall.py</string>
    <string>--heartbeat</string>
    <string>/Users/juliorcoelho/PersonaCore/data/phase25_heartbeat.jsonl</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/juliorcoelho/PersonaCore</string>
  <key>ProcessType</key>
  <string>Interactive</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PERSONACORE_SWEEP_ACTIVE</key>
    <string>1</string>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
  </dict>
```
The heartbeat path stays `data/phase25_heartbeat.jsonl` so the already-installed `com.personacore.phase25.watch` agent polls it unchanged. Launch: `cp` to `~/Library/LaunchAgents/`, `launchctl load`, `launchctl kickstart -k gui/$UID/com.personacore.phase26.canary`.

---

### `results/phase26_operational_note.md` (doc / evidence record)

**Analog:** `results/phase25_operational_note.md` — numbered `## N.` blocks, every figure a quoted command output. Shape of a launch block (`:884-905`):
```markdown
## 12. The launch record — 2026-09-04

Everything below is the kickstart transcript, quoted; the commands ran from the operator's console
in this order.

### 12.1 Preconditions

```
$ git rev-parse --abbrev-ref HEAD
main
$ git status --short | grep -v '^??'
$ git ls-files 'results/phase25_point_*.json' | wc -l
0
$ pgrep -fl 'phase25_n64_floor|phase25_run'
(no floor/driver process)
SWEEP_ACTIVE in this shell: unset
```
```
Shape of a close block (`:1104-1120`): dated header, `launchctl bootout`, `launchctl list | grep personacore` -> `(empty)`, `pmset -g assertions` owners by pid, `pgrep -x caffeinate` + `ps -o pid,ppid,args`.

Phase 26 blocks (minimum): pre-launch owner list (`pgrep -lf caffeinate`, `pmset -g`, Pitfall 9); `git ls-files results/phase26_*` -> 0 at prereg commit; kickstart + `launch_banner` read-back; OFF sidecar landing; control's `REPRODUCTION GATE PASSED 790/1008`; 16th sidecar; `--emit`; operator commit; **the D-19 dated named-limitation entry if cut**.

**How headings are pinned in tests** — `tests/test_phase25_launch.py:467-479, 519-524`:
```python
_REQUIRED_BLOCKS = (
    "## 1. The before-state: `pmset -g`",
    "## 2. The assertion owners, by owning process",
    ...
)

@pytest.fixture(scope="module")
def note():
    return _prose.normalized(_NOTE.read_text(encoding="utf-8"))

@pytest.mark.parametrize("heading", _REQUIRED_BLOCKS)
def test_the_operational_note_carries_every_required_block(note, heading):
    assert _prose.normalized(heading) in note, heading
```
`_prose.normalized(text)` = `" ".join(text.split())` (`scripts/_prose.py:35-46`) — every prose assertion goes through it (RPT-02 line-wrap false-RED).

---

### `results/phase26_canary.json` (artifact, write-once)

**Analog:** the blob `phase25_recall.emit` writes (`scripts/phase25_recall.py:264-282`) plus the frontier's `provenance` block (digests asserted at `tests/test_phase25_frontier.py:407-459`). Required top-level fields per D-13/D-18 and RESEARCH Pattern 5: `governs`, `instrument`, `frontier_path`, `frontier_sha256`, `frontier_bytes`, `base_sha256`, `prereg_module_sha256`, `prereg_committed`, `audit_target_rule` (verbatim by reference), `resolved_target`, `audited_point_keys` (16), `exclusions` (`{excluded: [...], n: k, of: 56}`), `n_in`, `n_out`, `auditor_ceiling`, `reachable_claims: "k/15"`, `power_gate: {threshold, control_epsilon_lower, passed, sentence}`, `joint_coverage`, `z`, `delta`, `curve_total_epsilon` (context only), `emitted_utc`, `emitted_git_sha`, `points: {key: {adapter_sha256, epsilon_upper, question_unit: {...}, fact_unit: {...}, verdict: {verdict, reasons: [...]}, epsilon_sentence}}`.

Every ε rendered through `phase25_epsilon.report_epsilon(point_epsilon=..., curve_total_epsilon=..., selection_accounted=False)` (`scripts/phase25_epsilon.py:297`, three keyword-only args, no defaults). `tests/test_phase25_frontier.py:260` scans for bypasses — do not f-string a bare ε into any `reasons` string without the sentence beside it.

## Shared Patterns

### `_prove` -> `SystemExit` (never `assert`) in every new module
**Source:** `scripts/phase25_recall.py:71-73`; `scripts/phase21_unit_continuation.py:119-132` (docstring explains `-O`)
**Apply to:** `phase26_prereg.py`, `phase26_canary.py`
```python
def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase26_canary] {message}")
```
Tests catch `pytest.raises(SystemExit)` and assert on the message substring.

### Sibling import via `sys.path` insert; torch and model modules LAZY
**Source:** `scripts/phase25_recall.py:41-54` (module scope), `:102, :149-150` (lazy, `# LAZY — torch-touching`)
**Apply to:** both scripts, both tests. The AST test in `test_phase26_canary.py` enforces it structurally.

### Sha256 pins: adapter on disk == record; sidecar == record; frontier bytes == artifact; module bytes == artifact
**Source:** `scripts/phase25_recall.py:80-81, 124-128, 137-141, 242-246`; `tests/test_phase25_frontier.py:449-459`
**Apply to:** `score_point`, `score_off_once`, `emit`, link test.

### Survivability kit — CALLED, never re-implemented
**Source:** `scripts/phase25_run.py:118` `atomic_write_json`, `:298` `beat`, `:350` `start_heartbeat`, `:407` `device`, `:286` `HEARTBEAT_PATH`
**Apply to:** every sidecar/artifact write and every scoring leg in `phase26_canary.py`. `try/finally: stop.set(); thread.join()` as at `phase25_recall.py:156-163`.

### Seed alignment — one `enumerate` from 0 per list
**Source:** `scripts/teach_persona.py:2414` (`for index, ... in enumerate(items)`), `scripts/phase14_recall.py:227-237` (`question_seed(index) = SEED + index`)
**Apply to:** all four `_score_list` calls (IN-taught, IN-heldout, OUT-taught, OUT-heldout); never concatenate lists. The control's IN-taught sum must satisfy `phase25_prereg.prove_reproduction(790, 1008)`.

### Counts beside every rate; both denominators; no bare ε
**Source:** `scripts/phase25_recall.py:100-111` (`_tier`: `numerator`/`denominator`/`draws_per_question`); `scripts/phase18_extraction.py:2010` `CLUSTER_DENOMINATOR_RATIONALE`; `scripts/phase25_epsilon.py:297` `report_epsilon`
**Apply to:** sidecar blobs (question unit + fact unit), the artifact's `points[k]`, every `reasons` string.

### Verdict + reasons register
**Source:** `scripts/erasure_gate.py:136` (`VERDICTS` tuple as module data); frontier `points[k].verdict = {"verdict": ..., "reasons": [...]}`
**Apply to:** `phase26_prereg.VERDICTS = ("BROKEN", "CONSISTENT", "INCONCLUSIVE")`; each point's `reasons` names `members_answered/n_in`, `nonmembers_answered/n_out`, `TPR_lb`, `FPR_ub`, both directions, `epsilon_lower`, `epsilon_upper`, the Bonferroni clause, and for unreachable points "epsilon_upper >= auditor_ceiling: this comparison could not have failed". The power-gate sentence verbatim: "The instrument must resolve at least the smallest claim it checks."

### Write-once artifact, `--force` escape hatch, operator commits
**Source:** `scripts/phase25_recall.py:213-230` (refusal is `emit`'s FIRST statement); `tests/test_phase25_recall.py:282-296`
**Apply to:** `phase26_canary.emit`. The driver builds no `["git", ...]` argv (§O1 closed — `tests/test_phase25_close.py:300-308`).

### Ancestry guard over the prereg module
**Source:** `tests/test_phase16_prereg.py:356-400` + strictly-after conjunct `tests/test_phase20_prereg.py:234-239`
**Apply to:** `scripts/phase26_prereg.py` vs `results/phase26_*`; `scripts/phase25_prereg.py` vs `results/phase25_frontier.json` + `results/phase26_*`. Memory rule: never edit `phase26_prereg.py` after the first sidecar/artifact commit — corrections go in a further continuation module.

### Skip markers for host-only legs
**Source:** `tests/test_phase25_recall.py:36-43` (`needs_adapters`, `needs_plutil`); `tests/conftest.py:51-60` (`sweep_is_active()`)
**Apply to:** the dry-run walk, sidecar tests, plist lint, D-15 live reproduction.

## No Analog Found

None. Every file has a same-role analog. Two sub-pieces have NO existing code and are written fresh
(both tiny, both pinned by tests): the `_items(..., forms=)` builder (6 lines — because
`teach_persona.calibration_items` cannot take `forms=` and the file is digest-pinned) and the D-09
`epsilon_lower` arithmetic (RESEARCH Code Example 4 — because no two-direction (ε, δ) bound exists in
the repo; it composes the two imported Wilson bounds).

## Metadata

**Analog search scope:** `scripts/` (phase25_*, phase21_*, phase20_*, phase18_*, phase14_*, erasure_gate, mitigation_unit, teach_persona, _addendum, _prose), `tests/` (test_phase16/20/24/25_*), `artifacts/*.plist`, `results/phase25_operational_note.md`, `.gitignore`, `tests/conftest.py`
**Files scanned:** 24 (targeted ranges; no file over 2,000 lines loaded whole)
**Pattern extraction date:** 2026-09-10
