# Phase 27: Relearning Attack - Pattern Map

**Mapped:** 2026-09-14
**Files analyzed:** 10 (4 new code files, 3 modified code files, 1 operator-committed artifact, 1 gitignored sidecar shape, 3 hand-edited ledgers counted as one row)
**Analogs found:** 9 / 10 (the per-arm offset-stream sidecar has no analog — it is the one genuinely new shape)

Every excerpt below was read from source at HEAD `b70daa8`. Line numbers are exact at that commit.
Sibling scripts are imported via the `sys.path.insert(0, _ROOT/"scripts")` idiom (`scripts/` is not
a package) — every new module and test copies that block verbatim from `scripts/phase26_prereg.py:39-49`.

**Hard constraints carried from RESEARCH (do not plan around them):**
- `scripts/teach_persona.py` is digest-pinned (`results/phase24_token_budget.json` → `tests/test_phase24_record.py:288`). It is an IMPORT-ONLY analog; never a modification target. `train_arm` (`:1655-1668`) takes no `train_config` / `max_steps` / `on_draw` kwarg — RESEARCH OQ1 recommends calling `tp.train()` directly the way `phase23_run.train_never_taught` does (option B). This map assumes option B; under option A the `_TRAIN_ARM_CALL_SITES` register row (§`tests/test_phase23_resume.py`) becomes mandatory.
- `mitigation_point_verdict` must not be imported or called from `scripts/` (`tests/test_phase20_correction.py:1377`). The 44-verdict tripwire lives in `tests/` through `phase20_gate_coverage.corrected_point_verdict` + `_route_kwargs`.
- `scripts/phase26_prereg.py`, `phase25_prereg.py`, `mitigation_gate.py`, `erasure_gate.py` are ancestry-guarded — read, never edit.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/phase27_prereg.py` (new) | config / pure-arithmetic pre-registration module | transform (frontier JSON → 3-valued verdict + reasons; frozen constants) | `scripts/phase26_prereg.py` (whole, 395 lines) + `scripts/erasure_gate.py:173-197` (`erasure_is_worth_attempting`, the MOOT shape) | exact |
| `scripts/phase27_relearn.py` (new) | CLI driver (argparse sub-modes; torch lazy) | batch + file-I/O (write-once record; train → score → reduce) | `scripts/phase26_canary.py:46-131, 475-504, 680-715, 793-828` (emit / parser / main) + `scripts/phase23_run.py:612-699` (`train_never_taught`, the train path) + `scripts/phase23_run.py:860-875` (tracked-record conjunct) | exact (driver) + exact (train path) |
| `src/personacore/training/data.py` (modify) | utility / data loader | streaming (memmap window draws) | itself — `get_batch_memmap_masked` `:93-126`; the draw at `:117` | exact (in-place additive kwarg) |
| `src/personacore/training/loop.py` (modify) | service / training loop | streaming (calls the loader at two closures) | itself — `train()` signature `:235-270`, call sites `:646-653` and `:691-693`; precedent for an additive keyword-only `None` kwarg: `resume_from=None` `:254` / `max_steps_override=None` `:258` | exact |
| `tests/test_phase27_prereg.py` (new) | test | request-response (git ancestry, module fixture over the 22 MB frontier, pure-function table) | `tests/test_phase26_prereg.py` (whole, 259 lines) + `tests/test_phase25_promotion.py:37-61` (`_route_kwargs`) | exact |
| `tests/test_phase27_relearn.py` (new) | test | request-response (AST, tmp_path forgery, e2e tiny run, `inspect.signature`, sha256 recompute, subprocess collect) | `tests/test_phase26_canary.py:27-51, 252-281, 361-399, 552-626, 786-810` + `tests/test_phase22_wiring.py:703-783` (`_e2e_env`) + `tests/test_phase24_record.py:288-335` + `tests/test_phase25_calibrate.py:570-586` + `tests/test_phase23_resume.py:355-359` | exact |
| `tests/test_phase23_resume.py` (modify, conditional) | test register | — | itself — `_TRAIN_ARM_CALL_SITES` `:60-134`, the grep census `:260-285` | exact (append rows only if a new `train_arm(` substring lands) |
| `results/phase27_admission.json` (new, operator-committed) | artifact (write-once) | file-I/O (emitted by `admit`, committed by hand) | the blob `phase26_canary.emit` writes `:680-708` + `results/phase24_token_budget.json::provenance.module_sha256` shape | exact |
| `data/phase27_<arm>_offsets.bin` (gitignored) | sidecar (run-time) | streaming append (raw uint64 + bin path) | none — see No Analog | — |
| `.planning/REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` (hand-edited at close) | ledger | — | Phase 26 close (D-38: snapshot → hand edit → diff; zero `gsd-sdk` mutation handlers) | n/a |

## Pattern Assignments

### `scripts/phase27_prereg.py` (config / pure arithmetic, transform)

**Analog A — whole-module shape:** `scripts/phase26_prereg.py`

**Docstring contract + imports + dated header + `ARTIFACT_GLOB` + `_prove`** (lines 19-33, 35-71) — copy verbatim, rename:
```python
# ANCESTRY-GUARDED. ``tests/test_phase26_prereg.py``
# (``test_phase26_prereg_is_frozen_before_every_phase26_result``) requires EVERY commit touching
# this file to be a strict ancestor of the first-add of every tracked ``results/phase26_*`` file.
# ...
# CPU-ONLY AT IMPORT. Stdlib + sibling scripts only: no torch, no ``phase14_*``, no ``teach_persona``,
# ... Every refusal is ``_prove`` -> ``SystemExit``, never ``assert``.

import math
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import erasure_gate  # noqa: E402  (needs the sys.path insert above)
import mitigation_unit  # noqa: E402  (same)
import phase20_gate_coverage  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)

COMMITTED = "2026-09-10"
SIDECARS_AT_COMMIT = 0

# The tracked set the ancestry guard reads — a constant the test imports rather than retypes.
ARTIFACT_GLOB = "results/phase26_*"


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase26_prereg] {message}")
```
Phase 27: imports become `erasure_gate`, `mitigation_gate`, `mitigation_budget`, `phase18_extraction`, `phase24_adversarial`, `phase23_prereg`, `phase25_record` (all CPU-safe at import per RESEARCH; `phase24_adversarial` and `phase18_extraction` must be verified CPU-only at import in Wave 0 — `build_corpus` lazily imports `factset` so the module itself should be fine). `COMMITTED = "<date>"`, `RECORDS_AT_COMMIT = 0`, `ARTIFACT_GLOB = "results/phase27_*"`, prefix `[phase27_prereg]`.

**By-reference constants — never retyped** (lines 78-79, 198-199, 210-212):
```python
# BY REFERENCE, never retyped: `tests/test_phase26_prereg.py` asserts identity (`is`), not equality.
RULE = phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]
...
UNIT = mitigation_unit.PRIVACY_UNIT
...
Z = erasure_gate._Z_ONE_SIDED_95
DELTA = mitigation_unit.DELTA
```
Phase 27 equivalents (D-04, D-19, D-21, D-23, D-24, D-25): `MARGIN_K = erasure_gate.MARGIN_K`; `CURVE_K = mitigation_budget.CURVE_K`; `FULL_K = phase18_extraction.K`; `F_Y = mitigation_gate.F_Y`; `GATED_TIER = phase18_extraction.GATED_TIER`; `HELD_OUT_FAMILY = phase24_adversarial.HELD_OUT_FAMILY` (read, never spelled — D-17). **X is a FUNCTION, not a constant** (the frontier is 22 MB — load inside functions, exactly as Phase 26 did with `resolve_audit_target(frontier)` at `:85`):
```python
def extraction_ceiling_x(frontier):
    kw = frontier["points"][CONTROL_N8]["verdict"]
    return mitigation_gate.extraction_ceiling(
        nontarget_successes=kw["control_extraction_successes"], ...)   # RESEARCH Code Ex. 3
```
and a test asserts it `== frontier["verdicts"]["extraction_ceiling"]["X"]` plus an AST scan for no `0.0064…` float literal. `RELEARN_CAP`, `RUNG_INTERVAL` are derived, not typed: RESEARCH OQ1-B means `teach_persona` (torch) is NOT importable here — pin `MAX_STEPS = 200`, `CHECKPOINT_INTERVAL = 50` as ints in the prereg **and** have a test assert `== tp.MAX_STEPS`, `== tp.CHECKPOINT_INTERVAL` (the same move RESEARCH M2 prescribes for `SEED_LADDER`: pin from the record, assert equality with the torch-importing module in a test only).

**Frontier-resolving function with `_prove` on a structural precondition** (lines 85-104) — the mould for `relearning_is_worth_attempting`:
```python
def resolve_audit_target(frontier):
    points = frontier["points"]
    n8 = [k for k in frontier["point_keys"] if points[k]["arm"].endswith("n8")]
    _prove(
        all(points[k]["canary_population"]["has_out_of_corpus_canaries"] for k in n8),
        "an n=8 point without out-of-corpus canaries — ...",
    )
    passing = [k for k in n8 if (points[k].get("verdict") or {}).get("verdict") == "PASS"]
    result = passing[0] if passing else n8[0]
    _prove(result == CONTROL_KEY, f"the committed audit_target_rule resolves to {result!r}, ...")
    return result
```
Phase 27 differs in ONE respect: structural defects (missing frontier, `len(point_keys) != 44`, tally mismatch, verdict outside domain) RETURN `("INCONCLUSIVE", reasons)` rather than `_prove`-halting, because D-03 makes "could not tell" a first-class verdict. Use RESEARCH Code Example 1 as the body; keep `_prove` only for programmer errors (e.g. an unknown `baseline` key in the gate).

**Pinned keys as a proved subsequence of `ORDERED_POINT_KEYS()`** (lines 119-132) — reuse for D-22 (`admitted_point_keys(frontier)` = PASS keys in `point_keys` order) and for D-12's two control keys:
```python
def audited_point_keys(frontier):
    keys = tuple(k for k in frontier["point_keys"] if k.startswith(AUDITED_ARM_PREFIX))
    pinned = tuple(
        k for k in phase25_record.ORDERED_POINT_KEYS() if k.startswith(AUDITED_ARM_PREFIX)
    )
    _prove(keys == pinned, f"the frontier's dp_n8 subsequence {keys} != ORDERED_POINT_KEYS()'s {pinned}")
    _prove(len(keys) == 16, f"expected 16 dp_n8 points, found {len(keys)}")
    _prove(keys[0] == CONTROL_KEY, f"the first dp_n8 point is {keys[0]!r}, not the control")
    return keys
```

**Int-only count refusal** (lines 218-224) — apply to every count the Z rule / band / curve reducer takes (`successes`, `questions`, `steps`, `scored_tokens`):
```python
def _prove_count(name, value):
    _prove(
        isinstance(value, int) and not isinstance(value, bool),
        f"{name} is {value!r}, which is not an int (bool excluded). This formula takes COUNTS; a "
        "float came out of arithmetic and a bool would compare True against 1",
    )
```

**Verdict domain + `verdict()` + `point_verdict()` returning `{"verdict", "reasons"}`** (lines 288-329):
```python
VERDICTS = ("BROKEN", "CONSISTENT", "INCONCLUSIVE")

def verdict(eps_lower, eps_upper, *, power_passed):
    if eps_lower is not None and eps_lower > eps_upper:
        result = "BROKEN"
    else:
        result = "CONSISTENT" if power_passed else "INCONCLUSIVE"
    _prove(result in VERDICTS, f"verdict {result!r} outside {VERDICTS}")
    return result

def point_verdict(reading, epsilon_upper, *, power, auditor_ceiling):
    ...
    reasons = [
        f"members answered {reading['members_answered']}/{reading['n_in']} and nonmembers "
        f"answered {reading['nonmembers_answered']}/{reading['n_out']} at the unit {UNIT!r}",
        ...
    ]
    if epsilon_upper >= auditor_ceiling:
        reasons.append(f"{CEILING_CLAUSE} (auditor_ceiling = {auditor_ceiling!r})")
    return {"verdict": result, "reasons": reasons}
```
Phase 27: `VERDICTS = ("ADMITTED", "MOOT", "INCONCLUSIVE")` for the admission gate; the recovery gate (`gate(..., *, baseline)` — RELRN-01) reuses `mitigation_gate.V4_VERDICTS`-style `("PASS","FAIL","INCONCLUSIVE")` or its own tuple; `reasons` carry counts with denominators (`k/416`, `k/1008`), never bare rates. `baseline` is KEYWORD_ONLY with NO default and is `_prove`d to be a key of `PINNED_BASELINES` (D-09/D-12).

**Analog B — the MOOT branch shape:** `scripts/erasure_gate.py:173-197`
```python
def erasure_is_worth_attempting(attack_successes, attack_questions, base_successes, base_questions):
    if attack_questions <= 0 or base_questions <= 0:
        return False, "INCONCLUSIVE: missing attack or base measurement"
    ...
    if attack_lower > base_rate:
        return True, (f"target recoverable: attack {attack_successes}/{attack_questions} ...")
    return False, (
        f"MOOT: attack {attack_successes}/{attack_questions} (95% lower bound {attack_lower:.4f}) "
        f"does not exceed the no-adapter base rate {base_rate:.4f} — nothing demonstrably "
        f"extractable, so there is nothing to erase"
    )
```
Phase 27 keeps the INCONCLUSIVE-first ordering and the "MOOT: … so there is nothing to relearn" sentence shape, but returns the three-valued string + a `reasons` LIST (Phase 26 D-05), with per-leg tallies and (a)/(b)/(c) counts generated from `frontier["verdicts"]["tallies_by_leg"]` and RESEARCH Code Ex. 3 (D-07). Expected counts on the committed frontier: (a) 30, (b) 4, (c) 1 — not 32 (RESEARCH M5).

**Pinned baselines (D-12) as module DATA** — shape from `phase26_prereg.py:336-344` (`WAIVER_CONTINUATION` dict) and `:354-395` (tuple of tuples, each entry validated by a test):
```python
PINNED_BASELINES = {
    "never_taught_1337": {"path": "checkpoints/phase23_never_taught_seed1337_adapter.pt",
                          "sha256": "8da8c2c2…a9e7", "seed": 1337,
                          "source": "results/phase23_never_taught_training.json"},
    ...
    "control_n8": {"path": "checkpoints/phase25_sigma0p000000_dp_n8_adapter.pt",
                   "sha256": "3fab0203…cef64", "seed": 1337, "point_key": "dp_n8_sigma0p000000",
                   "source": "results/phase25_point_dp_n8_sigma0p000000.json"},
    "control_n64": {...},
}
FRESH_SEEDS = (1337, 2024, 1338, 2025, 1339)   # from results/phase23_never_taught_training.json::seeds; test asserts == phase23_run.SEED_LADDER
```
Digests are in RESEARCH §Pinned baselines; a test re-reads each `source` record and asserts path/sha256/seed equality (`::test_baselines_are_pinned_from_the_records`).

---

### `scripts/phase27_relearn.py` (driver, batch + file-I/O)

**Analog A — driver skeleton:** `scripts/phase26_canary.py`

**Imports + import-time git SHA + paths + helpers** (lines 46-106) — copy, rename:
```python
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
import phase26_prereg  # noqa: E402  (same — the dated pre-registration, stdlib only)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

# Resolved ONCE, at import — the commit the running code was actually loaded from. ...
INSTRUMENT_GIT_SHA = git_sha()

RECORD = _ROOT / "results" / "phase26_canary.json"
SIDECAR_DIR = _ROOT / "data"  # gitignored (`data/`)
PREREG_MODULE = _ROOT / "scripts" / "phase26_prereg.py"


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase26_canary] {message}")


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    """Repo-relative when inside the root; the path as given otherwise (tests use tmp dirs)."""
    path = pathlib.Path(path)
    return str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)
```
Phase 27: `import phase27_prereg`; `RECORD = _ROOT / "results" / "phase27_admission.json"`; `STREAM_DIR = _ROOT / "data"`; `PINNED_MODULES = ("scripts/phase27_prereg.py", "scripts/phase27_relearn.py", "scripts/mitigation_gate.py", "scripts/erasure_gate.py", "src/personacore/training/data.py")` (D-35). `teach_persona`, `phase14_factset`, `phase14_recall`, `phase18_extraction`, `torch`, `personacore.lora`, `personacore.training.loop` are imported INSIDE the leg functions only (the AST test at `tests/test_phase26_canary.py:252-267` enforces this; extend the forbidden set with `personacore.training.loop`, `personacore.lora`).

**Frontier read once** (lines 128-131):
```python
@functools.lru_cache(maxsize=1)
def frontier():
    """The audited artifact, read ONCE per process (22 MB), never modified."""
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))
```
Add a sibling `admission()` that reads `RECORD` (small) — NOT cached, since `admit` writes it and tests forge it under `tmp_path` via `monkeypatch.setattr(relearn, "RECORD", ...)`.

**Emit: write-once refusal FIRST, `refuse_if_dirty` SECOND (before hashing anything), then the blob, then `atomic_write_json`** (lines 475-504, 680-715):
```python
def emit(out_path=RECORD, *, overwrite=False):
    _prove(
        overwrite or not pathlib.Path(out_path).exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. The sanctioned route deletes it in "
        "its own commit, then re-runs against a clean tree (scripts/phase25_record.py "
        "RERUN_ROUTE). Pass --force to overwrite deliberately.",
    )
    out_path = pathlib.Path(out_path)
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){_rel(out_path)}",)
    refuse_if_dirty(
        who="phase26_canary",
        detail=(
            "emit publishes emitted_git_sha and hashes scripts/ and results/ from the working "
            "tree; a record emitted from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_ROOT,
    )
    ...
    blob = {
        ...
        "frontier_path": _rel(phase25_record.FRONTIER_RECORD),
        "frontier_sha256": _sha256(phase25_record.FRONTIER_RECORD),
        "frontier_bytes": phase25_record.FRONTIER_RECORD.stat().st_size,
        ...
        "prereg_module_sha256": _sha256(PREREG_MODULE),
        "prereg_committed": phase26_prereg.COMMITTED,
        ...
        "emitted_utc": _utc(),
        "emitted_git_sha": git_sha(),
        "points": points,
        "summary": summary,
    }
    phase25_run.atomic_write_json(out_path, blob)
    print(f"[phase26_canary] emitted {_rel(out_path)}: {summary}; ...")
    return blob
```
Phase 27 `admit(out_path=RECORD, *, overwrite=False)` order: (1) overwrite refusal (D-08 `refuse_if_exists` semantics — reproduce this 4-line `_prove`, do not import `teach_persona.refuse_if_exists` at module scope, RESEARCH M10); (2) `refuse_if_dirty(who="phase27_relearn", pathspec=("scripts","src","results", ":(exclude)…"))`; (3) `verdict, reasons = phase27_prereg.relearning_is_worth_attempting(frontier())`; (4) 44 rows `{point_key, arm, leg, verdict, cleared_a, cleared_b, cleared_c}` via RESEARCH Code Ex. 3 with `(None, None, None)` on REFUSED rows and `refused: True` (OQ6); `_prove` the tallies re-derive at the write (D-33); (5) blob = `{verdict: {verdict, reasons}, tallies, tallies_by_leg, cleared_counts: {a, b, c, by_leg}, rows, frontier_path/sha256/bytes, baselines: phase27_prereg.PINNED_BASELINES, attacker_corpus_sha256, apparatus: {status: "not exercised", reason: "gate read MOOT", legs: [{name, sub_mode, refusal_node_id, e2e_node_id}]}, provenance: {module_sha256: {rel_path: digest for PINNED_MODULES}, git_sha: INSTRUMENT_GIT_SHA, head_at_write: git_sha(), written_utc, torch_version}}` (D-11, D-35, D-36); (6) `phase25_run.atomic_write_json`. `torch_version` is the ONE torch touch in `admit` — read it via `importlib.metadata.version("torch")` to keep `admit` torch-free at import, or accept a lazy `import torch` inside the function (the AST test only polices module scope).

**Parser + `main` returning int** (lines 793-828) — swap flags for subparsers:
```python
def build_parser():
    parser = argparse.ArgumentParser(description="Phase 26 canary audit: ...")
    parser.add_argument("--points", nargs="+", default=None)
    parser.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--emit", action="store_true", help="assemble results/phase26_canary.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing artifact")
    return parser


def main(argv=None):
    print(phase25_venue.launch_banner(), flush=True)
    args = build_parser().parse_args(argv)
    if args.emit:
        emit(overwrite=args.force)
        return 0
    ...
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
Phase 27: `sub = parser.add_subparsers(dest="mode", required=True)`; `admit` gets `--force`; `calibrate` / `curve` / `gate` / `structural-proof` get `--leg {n8,n64}`, `--out-dir` (default `STREAM_DIR`), `--record` (default `RECORD`, so tests can point at a forged tmp copy). `main` dispatches `{"admit": admit, "calibrate": run_calibrate, ...}[args.mode](**kwargs)` — a DICT of `mode → function` with explicit kwargs is what makes the D-10 kwargs-trace test (AST over `main` + `inspect.signature` over each `run_<leg>`) mechanical.

**Analog B — the leg refusal: two conjuncts on the COMMITTED record** — `scripts/phase23_run.py:860-875` (tracked-set conjunct) + `phase26_prereg.verdict` domain check:
```python
    tracked = subprocess.run(
        ["git", "ls-files", NOISED_RECORD_GLOB],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    _prove(
        not tracked,
        f"`git ls-files {NOISED_RECORD_GLOB}` already matches {tracked!r}. DPSGD-06 requires "
        "σ=0 to be the DP arm's FIRST executed run: ...",
    )
```
Phase 27 `_require_admitted(record_path)` — the FIRST statement of every leg (D-08):
```python
def _require_admitted(record_path=RECORD):
    record_path = pathlib.Path(record_path)
    _prove(record_path.exists(), f"{_rel(record_path)} is absent — run `admit` first; every leg is gated on the COMMITTED record")
    blob = json.loads(record_path.read_text(encoding="utf-8"))
    read = blob["verdict"]["verdict"]
    _prove(read == "ADMITTED", f"{_rel(record_path)} reads {read!r} — REFUSING to run this leg: nothing is admitted ({'; '.join(blob['verdict']['reasons'][:1])})")
    if record_path.is_relative_to(_ROOT):
        tracked = subprocess.run(["git", "ls-files", _rel(record_path)], cwd=_ROOT, capture_output=True, text=True, check=True).stdout.split()
        _prove(tracked, f"{_rel(record_path)} is not tracked — a leg runs only against the COMMITTED record, never a live re-read")
    return blob
```
The `["git", "ls-files", …]` argv is a READ-ONLY action in `phase25_run.READ_ONLY_GIT_ACTIONS` (`:751-753`); the AST git-surface test (`tests/test_phase25_driver.py:105-140`, reused by Phase 26) must be pointed at the new driver with `allowed = set(phase25_run.READ_ONLY_GIT_ACTIONS)`. The tracked conjunct is skipped for a `tmp_path` record (outside `_ROOT`) so the e2e test can forge ADMITTED without `git add`.

**Analog C — the train path (D-13/D-26 under OQ1-B):** `scripts/phase23_run.py:612-699` (`train_never_taught`)
```python
def train_never_taught(seed):
    """...**EVERY BUDGET CONSTANT IS IMPORTED, NOT RETYPED** — ``tp.LR``, ``tp.WARMUP_STEPS``,
    ``tp.MAX_STEPS``, ``tp.BATCH_SIZE``, ``tp.WEIGHT_DECAY``, ``tp.LORA_CFG``, ``tp.EVAL_INTERVAL``,
    ``tp.CHECKPOINT_INTERVAL`` — so "identical budget" is literally the same symbol..."""
    arm = never_taught_arm(seed)
    paths = tp.arm_outputs(arm, prefix=PREFIX)
    tp.refuse_if_exists([paths["csv"], paths["checkpoint"], paths["adapter"]])

    runtime = tp.RuntimeConfig()
    blob = tp.torch.load(tp.CONVBASE_BEST, weights_only=False)  # our OWN checkpoint (T-14-04)
    model_cfg = tp.ModelConfig(**blob["model_config"])

    tp.seed_everything(seed)
    model = tp.GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering
    n_wrapped = tp.inject_lora(model, tp.LORA_CFG)
    _prove(n_wrapped == 6 * model_cfg.n_layer, ...)
    tp.mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected_trainable = tp.LORA_CFG.r * model_cfg.n_layer * 18 * model_cfg.n_embd
    _prove(trainable == expected_trainable, ...)
    model.to(runtime.device)
    before = tp.snapshot_params(model)
    paths["csv"].parent.mkdir(parents=True, exist_ok=True)
    paths["checkpoint"].parent.mkdir(parents=True, exist_ok=True)

    box = {}
    with synchronized_seconds(box):
        final = tp.train(
            train_config=tp.TrainConfig(
                lr=tp.LR,
                warmup_steps=tp.WARMUP_STEPS,
                max_steps=tp.MAX_STEPS,
                batch_size=tp.BATCH_SIZE,
                weight_decay=tp.WEIGHT_DECAY,
                seed=seed,
            ),
            runtime_config=runtime,
            model=model,
            model_config=model_cfg,
            train_bin=tp.DIALOG_TRAIN_BIN,
            train_mask_bin=tp.DIALOG_TRAIN_MASK,
            val_bin=tp.DIALOG_VAL_BIN,
            val_mask_bin=tp.DIALOG_VAL_MASK,
            penalty_fn=None,
            log_path=paths["csv"],
            eval_interval=tp.EVAL_INTERVAL,
            checkpoint_path=paths["checkpoint"],
            checkpoint_interval=tp.CHECKPOINT_INTERVAL,
            return_final_loss=True,
        )

    # The same canary `train_arm` runs: every trainable moved, every frozen base param untouched.
    _prove(tp.math.isfinite(float(final)), f"non-finite final loss {final!r} on {arm} (PITFALLS P5)")
    for name, param in model.named_parameters():
        if param.requires_grad:
            _prove(not tp.torch.equal(param, before[name]), f"[canary] trainable {name} did not move on {arm} ...")
        else:
            _prove(tp.torch.equal(param, before[name]), f"[canary] frozen base param {name} changed on {arm} ...")
```
Phase 27 `train_relearn_arm(arm, *, cfg, seed, bins, recorder, out_dir)` copies this body with these changes: (a) `cfg` is the ONE shared `TrainConfig` instance built once per leg in the driver (`max_steps=phase27_prereg.RELEARN_CAP`) and passed by reference — D-26(i) literally; (b) bins come from `tp.build_arm_bins(arm, facts, family_ids, replay_ratio=…, seed=seed, prefix="phase27")` for attacker/control and from `tp.DIALOG_TRAIN_*` for the fresh arm (as above); (c) replay kwargs `replay_bin=tp.DIALOG_TRAIN_BIN, replay_mask_bin=tp.DIALOG_TRAIN_MASK, replay_windows=tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE` (D-20, the literal shape at `teach_persona.py:1970-1972`); (d) the rung chain: loop `for rung in range(tp.CHECKPOINT_INTERVAL, RELEARN_CAP + 1, tp.CHECKPOINT_INTERVAL)` with `max_steps_override=rung`, `resume_from=paths["checkpoint"] if rung > tp.CHECKPOINT_INTERVAL else None`, then `export_adapter(rung_path(arm, rung), adapter=lora_state_dict(model), lora_config=asdict(tp.LORA_CFG), base_fingerprint=…)` after each — RESEARCH Code Ex. 4 (OQ2; the off-disk config proof reads `load_checkpoint(paths["checkpoint"])["train_config"] == asdict(cfg)`, `checkpoint.py:135`); (e) `on_draw=recorder` (OQ3 passthrough, next section). `train_never_taught` uses `refuse_if_exists` from `tp` — fine inside the leg (torch already imported there).

**Analog D — extraction scoring at K=16 and the K=48 promotion:** `scripts/phase25_run.py:458` `draw_point_shapes(point_key, *, adapter, adapter_sha256, corpus, corpus_sha256, k, state, dry_run=False)` and `:586` `score_point(blob, values)`; `mitigation_gate.promote_to_full_fidelity(*, verdict, reasons, curve_k, full_k)` (`:963`, calls `ratchet_k`). Recall REPORTED beside it via `tp.score_arm(arm, facts, adapter_path, device)` (`teach_persona.py:2440`), exactly as `phase25_recall.py:114-185` wraps it (heartbeat `try/finally: stop.set(); thread.join()`).

---

### `src/personacore/training/data.py` (utility, streaming) — MODIFY

**Analog:** itself, `get_batch_memmap_masked` (lines 93-126). The whole change is one keyword and one guarded call:
```python
def get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, device):
    ...
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    mask = np.memmap(mask_path, dtype=np.uint8, mode="r")
    if len(data) != len(mask):
        raise ValueError(...)
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)      # :117
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    ...
    y[m == 0] = -100
    return x.to(device), y.to(device)
```
Phase 27 (D-29/D-30): signature becomes `(bin_path, mask_path, batch_size, block_size, device, *, on_draw=None)`; immediately after `:117` insert
```python
    if on_draw is not None:
        on_draw(bin_path, ix)   # ix is the raw np.ndarray; the recorder owns the bytes
```
Nothing else moves — the byte-identity test compares `ix` across the pre-edit and post-edit paths under `np.random.seed(…)`. Do NOT touch `get_batch_fact_aligned` (`loop.py:604` path, DP arms only — RESEARCH "Deprecated/outdated").

**Recorder contract (driver side, discretionary):** `on_draw(bin_path, ix)` appends `ix.astype(np.uint64).tobytes()` plus `str(bin_path).encode()` (or a fixed-width bin index) to an in-memory list per arm; flushed to `data/phase27_<arm>_offsets.bin` with a running `hashlib.sha256` — the digest is the D-26(iii) proof. Keep the recorder a plain closure over a `list` and a `hashlib.sha256()`; no class.

---

### `src/personacore/training/loop.py` (service, streaming) — MODIFY

**Analog:** itself. Additive keyword-only `None` kwargs already exist in `train()`'s signature (lines 235-270): `resume_from=None` (`:254`), `max_steps_override=None` (`:258`), `checkpoint_extra=None` (`:267`). Add `on_draw=None` at the end of the keyword block (before `return_final_loss=False` at `:269`), then thread it to BOTH call sites:

Teaching draw (lines 643-653):
```python
        elif train_mask_bin is not None:
            def batch_fn(_micro):
                return get_batch_memmap_masked(
                    train_bin,
                    train_mask_bin,
                    train_config.batch_size,
                    model_cfg.block_size,
                    runtime.device,
                )
```
Replay draw (lines 683-693):
```python
    replay_fn = None
    if replay_windows is not None:
        def replay_fn(model, scaler):
            drawn = 0
            while drawn < replay_windows:
                micro = min(train_config.batch_size, replay_windows - drawn)
                xb, yb = get_batch_memmap_masked(
                    replay_bin, replay_mask_bin, micro, model_cfg.block_size, runtime.device
                )
```
Both gain `on_draw=on_draw` as a trailing kwarg. When `None` the loader's guard is a no-op, so every golden-trajectory test (`tests/test_lora_training.py`, `test_loop_penalty_fn.py`, `test_phase22_*`) stays byte-identical. `tests/test_phase22_wiring.py:822` (`monkeypatch.setattr(loop_mod, "get_batch_fact_aligned", loader)`) proves the loop-module binding is the effective one — the recorder test can spy `loop_mod.get_batch_memmap_masked` the same way to count call order (teaching then replay per step) without training more than 2 steps.

---

### `tests/test_phase27_prereg.py` (test, git ancestry + pure-function table)

**Analog:** `tests/test_phase26_prereg.py` — whole file. Copy, rename.

**Imports + `_git` + module fixture** (lines 9-48):
```python
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import _prose  # noqa: E402  (scripts/ is not a package)
import erasure_gate  # noqa: E402  (same)
...
import phase26_prereg  # noqa: E402  (same)

PREREG = "scripts/phase26_prereg.py"
PHASE25_PREREG = "scripts/phase25_prereg.py"
FRONTIER = "results/phase25_frontier.json"


def _git(*args):
    """Run git inside the repository and return its stdout, raising on a non-zero exit."""
    return subprocess.run(
        ("git", *args), cwd=_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def artifact():
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))
```
Phase 27 adds `import mitigation_gate, phase20_gate_coverage, phase25_condition_c, phase25_promotion as promotion, phase27_prereg` and `PREREG = "scripts/phase27_prereg.py"`.

**The ancestry guard, honest with zero tracked** (lines 51-98) — copy `_assert_frozen_before` verbatim:
```python
def _assert_frozen_before(prereg_artifact, tracked):
    assert _git("rev-parse", "--is-shallow-repository") == "false", (...)
    prereg_commits = _git("log", "--format=%H", "--", prereg_artifact).split()
    assert prereg_commits, f"{prereg_artifact} has no commits — green and blind"

    checked = 0
    for artifact in tracked:
        adds = _git("log", "--diff-filter=A", "--format=%H", "--", artifact).split()
        first_add = adds[-1]
        for prereg in prereg_commits:
            assert prereg != first_add, (
                f"{prereg_artifact} and {artifact} were committed in the SAME commit {prereg} — "
                "the pre-registration must land STRICTLY BEFORE the artifact it pins, ..."
            )
            subprocess.run(("git", "merge-base", "--is-ancestor", prereg, first_add), cwd=_ROOT, check=True)
            checked += 1

    assert checked == len(prereg_commits) * len(tracked), (...)
    assert bool(checked) == bool(tracked), (...)


def test_phase26_prereg_is_frozen_before_every_phase26_result():
    _assert_frozen_before(PREREG, _git("ls-files", phase26_prereg.ARTIFACT_GLOB).split())


def test_phase25_prereg_is_byte_identical_since_the_frontier():
    tracked = [FRONTIER] + _git("ls-files", phase26_prereg.ARTIFACT_GLOB).split()
    _assert_frozen_before(PHASE25_PREREG, tracked)
    assert not _git("diff", "--", PHASE25_PREREG)
    assert len(_git("log", "--oneline", "--", FRONTIER).splitlines()) == 1
```
Phase 27: `_assert_frozen_before("scripts/phase27_prereg.py", git ls-files phase27_prereg.ARTIFACT_GLOB)`; keep the frontier one-commit assertion (D-06) in a Phase 27 test too.

**By-reference identity + prose clauses** (lines 102-110):
```python
def test_the_committed_rule_resolves_to_the_control(artifact):
    assert phase26_prereg.RULE is phase25_prereg.CANARY_RESERVATIONS["audit_target_rule"]
    for clause in ("restrict to n=8 points", ...):
        assert _prose.normalized(clause) in _prose.normalized(phase26_prereg.RULE)
    assert phase26_prereg.resolve_audit_target(artifact) == CONTROL == phase26_prereg.CONTROL_KEY
```
Phase 27: `assert phase27_prereg.MARGIN_K is erasure_gate.MARGIN_K`, `CURVE_K is mitigation_budget.CURVE_K`, `F_Y is mitigation_gate.F_Y`, `HELD_OUT_FAMILY == phase24_adversarial.HELD_OUT_FAMILY == "A2"` (the string is spelled ONCE, in the test); `phase27_prereg.relearning_is_worth_attempting(artifact) == ("MOOT", [...])` with `"0 of 44"` and `"30"` (cleared a) named in the reasons.

**Parametrized hand-computed table** (lines 137-161) — shape for `::test_z_rule_table` (D-23/D-25/D-28: `(fresh_first_clear, control_first_clear) → z | INCONCLUSIVE`) and `::test_band_uses_imported_margin_and_noise_floor` (D-19):
```python
_ROWS = (
    ((790, 1008, 0, 784), (0.7617, 0.0034, 5.4003, 1.4306)),
    ...
)

@pytest.mark.parametrize(("counts", "expected"), _ROWS)
def test_epsilon_lower_matches_the_hand_computed_table(counts, expected):
    reading = phase26_prereg.epsilon_lower(*counts)
    ...
    assert reading["z"] == erasure_gate._Z_ONE_SIDED_95
```

**Int-only refusal + verdict domain tests** (lines 178-202):
```python
def test_counts_are_ints_only():
    with pytest.raises(SystemExit):
        phase26_prereg.epsilon_lower(True, 8, 0, 56)
    with pytest.raises(SystemExit):
        phase26_prereg.epsilon_lower(8.0, 8, 0, 56)


def test_verdict_domain_is_three_valued_and_one_sided():
    assert phase26_prereg.VERDICTS == ("BROKEN", "CONSISTENT", "INCONCLUSIVE")
    ...
```
Phase 27: `assert phase27_prereg.VERDICTS == ("ADMITTED", "MOOT", "INCONCLUSIVE")`; tmp-copy forgeries: 43 points → INCONCLUSIVE; `tallies.FAIL = 31` → INCONCLUSIVE; one `verdict.verdict = "PASS"` → `("ADMITTED", [...])` naming that key; one `"INCONCLUSIVE"` flipped → still MOOT (D-01: not INCONCLUSIVE alone). Forgeries go through `copy.deepcopy(artifact)` on the module fixture, never through the file.

**Analog B — the 44-verdict tripwire recipe:** `tests/test_phase25_promotion.py:37-61`
```python
RECORD = json.loads(promotion.RECORD.read_text(encoding="utf-8"))
KEYS = tuple(phase25_record.ORDERED_POINT_KEYS())
REFUSED = tuple(k for k in KEYS if k.startswith("adv_n64_"))
REACHED = tuple(k for k in KEYS if k not in REFUSED)
_PIN = set(promotion.PIN_KWARGS)


def _pin_kwargs(entry):
    return {name: entry[name] for name in _PIN}


def _route_kwargs(entry):
    kwargs = {k: v for k, v in _pin_kwargs(entry).items() if not k.startswith("sweep_")}
    curve = entry["whole_curve_inputs"]
    kwargs.update({k: curve[k] for k in curve if k.startswith("sweep_")})
    kwargs["retention_floor_provenance"] = {
        "regime": phase20_gate_coverage.ADAPTER_REGIME,
        "seeds": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE["seeds"],
    }
    return kwargs
```
Phase 27 `::test_every_frontier_verdict_re_derives_through_the_route` is RESEARCH Code Ex. 2 on top of this helper (38 equal, 6 `SystemExit` whose text `== entry["reasons"][0]`). `::test_cleared_abc_re_derive_on_every_row` applies RESEARCH Code Ex. 3 to the 38 reached entries and asserts `(30, 4, 1)`, then compares to the committed record's rows when it exists (both-state idiom).

---

### `tests/test_phase27_relearn.py` (test, AST / tmp_path forgery / e2e / signature / sha256)

**Analog A:** `tests/test_phase26_canary.py`

**Module constants, `needs_adapters`, `autouse` clean-tree stub** (lines 27-51, 63-69):
```python
_DRIVER = _SCRIPTS / "phase26_canary.py"
_FRONTIER = json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))
_KEYS = phase26_prereg.audited_point_keys(_FRONTIER)
_ADAPTERS_ON_DISK = (_ROOT / "checkpoints").is_dir() and all(
    (_ROOT / _FRONTIER["points"][key]["adapter_path"]).exists() for key in _KEYS
)


@pytest.fixture(scope="module")
def frontier():
    return _FRONTIER


@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    """``emit()`` refuses a dirty tree (26-REVIEW WR-03). This suite runs on dirty trees all day,
    so the guard is RECORDED here, never exercised; ..."""
    calls = []
    monkeypatch.setattr(canary, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls

needs_adapters = pytest.mark.skipif(not _ADAPTERS_ON_DISK, reason="... gitignored checkpoints/ — sweep host only")
```
Phase 27: `_ADAPTERS_ON_DISK` iterates `phase27_prereg.PINNED_BASELINES.values()`; `needs_adapters` guards only `::test_pinned_adapters_hash_on_host`. Everything else runs on the tiny fixture.

**AST: no torch-touching module at top level; no direct `torch.load`** (lines 252-281) — copy verbatim, point at the new driver, extend the forbidden set:
```python
def test_the_driver_imports_no_torch_touching_module_at_top_level():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    top_level = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    } | {node.module for node in tree.body if isinstance(node, ast.ImportFrom) and node.module}
    assert not top_level & {"torch", "teach_persona", "phase14_factset", "phase14_recall", "phase21_filler", "phase18_extraction"}


def test_the_driver_never_calls_torch_load_directly():
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    calls = [node for node in ast.walk(tree)
             if isinstance(node, ast.Attribute) and node.attr == "load"
             and isinstance(node.value, ast.Name) and node.value.id == "torch"]
    assert calls == []
```

**Dirty-tree wiring proof + write-once against the LIVE record, both-state** (lines 361-398):
```python
def test_emit_refuses_a_dirty_tree_before_reading_any_sidecar(tmp_path, monkeypatch, clean_tree):
    inside = _ROOT / "results" / "phase26_canary_probe_never_written.json"
    with pytest.raises(SystemExit, match="phase26_operational_note.md"):
        canary.emit(inside)
    assert not inside.exists()
    (call,) = clean_tree
    assert call["who"] == "phase26_canary"
    assert call["pathspec"] == ("scripts", "src", "results", ":(exclude)results/phase26_canary_probe_never_written.json")

    def refuse(**kw):
        raise SystemExit("[probe] REFUSING: the working tree is dirty")

    monkeypatch.setattr(canary, "refuse_if_dirty", refuse)
    with pytest.raises(SystemExit, match="dirty"):
        canary.emit(tmp_path / "canary.json")


def test_emit_refuses_to_overwrite_the_committed_artifact():
    if canary.RECORD.exists():
        before = canary.RECORD.read_bytes()
        with pytest.raises(SystemExit) as excinfo:
            canary.emit()
        assert "REFUSING to overwrite" in str(excinfo.value)
        assert "--force" in str(excinfo.value)
        assert canary.RECORD.read_bytes() == before
    else:
        assert not _git("ls-files", "results/phase26_canary.json").strip(), (...)
```
Phase 27: `::test_admit_refuses_a_dirty_tree`, `::test_admit_refuses_to_overwrite` — same bodies against `relearn.admit`.

**Per-leg refusal RED (D-08) — parametrize over the four sub-modes on a forged MOOT/INCONCLUSIVE tmp record** (new composition of the two tests above; the analog for "watched non-zero exit naming the verdict" is `tests/test_phase26_canary.py:385-392`):
```python
@pytest.mark.parametrize("mode", ("calibrate", "curve", "gate", "structural-proof"))
@pytest.mark.parametrize("verdict", ("MOOT", "INCONCLUSIVE"))
def test_each_leg_refuses_unless_admitted(tmp_path, mode, verdict):
    forged = tmp_path / "phase27_admission.json"
    forged.write_text(json.dumps({"verdict": {"verdict": verdict, "reasons": ["forged"]}}))
    with pytest.raises(SystemExit) as excinfo:
        relearn.main([mode, "--record", str(forged), "--leg", "n8"])
    assert verdict in str(excinfo.value) and "REFUSING" in str(excinfo.value)
    assert not any(tmp_path.glob("*offsets*"))   # nothing trained, nothing written
```
Also one case with the record ABSENT (`"absent"` in the message). These node ids are the `refusal_node_id` values the `apparatus` block names (D-36).

**Live-path e2e through `main()` with fakes on the instrument seams** (lines 552-626) — the frame:
```python
def test_the_live_path_is_wired_end_to_end(tmp_path, monkeypatch, frontier):
    monkeypatch.setattr(canary, "SIDECAR_DIR", tmp_path)
    import phase14_factset as fs
    import phase14_recall as pr
    import torch

    def fake_loader(device, adapter_path=None):
        return torch.nn.Module(), None, None, frozenset(), None
    ...
    monkeypatch.setattr(pr, "load_adapted_model", fake_loader)
    monkeypatch.setattr(pr, "complete_question", fake_complete)
    ...
    assert canary.main(["--points", phase26_prereg.CONTROL_KEY, "dp_n8_sigma80p000000", "--heartbeat", str(heartbeat)]) == 0
    off_blob = json.loads(canary.off_sidecar_path().read_text(encoding="utf-8"))
    ...
    for blob in (off_blob, control_blob, producer):
        for tier, (n_facts, n_questions) in expected.items():
            assert len(blob[tier]["per_fact"]) == n_facts
```
Phase 27 `::test_the_live_path_is_wired_end_to_end`: (1) `_e2e_env(tmp_path, monkeypatch)` (below) — the real train path on a tiny GPT + real tokenizer, 2 steps, CPU; (2) forge an ADMITTED record in `tmp_path` naming one fake point whose `adapter_path`/`adapter_sha256` is the tiny model's own exported adapter (D-32); (3) monkeypatch `phase14_factset.LOCKED_FACTS` to 2 synthetic `Fact`s (`tests/test_phase21_replay_volume.py:119`: `fs.Fact(f.id, f.slot, v, f.tier)`), `phase27_prereg.RELEARN_CAP`/rung interval to 2/1 so the rung chain has ≥ 1 rung, and `tp.MAX_STEPS` etc. as `_e2e_env` does; (4) drive `relearn.main(["calibrate", "--record", forged, "--leg", "n8", "--out-dir", tmp])` → `["curve", …]` → `["gate", …]` → `["structural-proof", …]`, each returning 0; (5) assert structure only: rung adapters exist, `data/phase27_<arm>_offsets.bin` exists per arm with equal sha256 across arms of equal seed, `load_checkpoint(...)["train_config"]` equal across arms, the gate output has `verdict ∈ VERDICTS` and `cost_curve` rungs with `steps` and `scored_tokens` ints, and `baseline` was a pinned key. Real scorer: `phase25_run.draw_point_shapes` on `phase18_extraction.build_corpus(tok)` over the 2 fake facts (RESEARCH A2 — verify in Wave 0 that `build_corpus` runs on 2 facts; if `CORPUS_SOURCE_FIXTURE` binds fact ids, patch it too).

**Both-ways pin, both-state** (lines 786-809):
```python
def test_the_sibling_is_pinned_to_the_frontier_both_ways(frontier):
    tracked = _git("ls-files", "results/phase26_canary.json").splitlines()
    if canary.RECORD.exists():
        blob = json.loads(canary.RECORD.read_text(encoding="utf-8"))
        assert blob["frontier_sha256"] == hashlib.sha256(phase25_record.FRONTIER_RECORD.read_bytes()).hexdigest()
        assert blob["frontier_bytes"] == 22311714
        assert all(blob["points"][key]["adapter_sha256"] == frontier["points"][key]["adapter_sha256"] for key in _KEYS)
        assert blob["prereg_module_sha256"] == hashlib.sha256((_ROOT / "scripts" / "phase26_prereg.py").read_bytes()).hexdigest()
        assert len(_git("log", "--oneline", "--", "results/phase25_frontier.json").splitlines()) == 1
        added = _git("log", "--diff-filter=A", "--", "results/phase26_canary.json").splitlines()
        assert bool(tracked) == bool(added)
    else:
        assert not tracked
```
Phase 27 `::test_the_record_is_pinned_to_the_frontier_both_ways` — identical with `results/phase27_admission.json`; `frontier_sha256` expected `1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5` (RESEARCH; assert via recompute, not the literal).

**Analog B — the tiny-model e2e environment:** `tests/test_phase22_wiring.py:703-783` (`_E2E_CFG`, `_e2e_env`)
```python
_E2E_CFG = ModelConfig(block_size=tp.BLOCK_SIZE, n_layer=1, n_head=2, n_embd=16)


def _e2e_env(root, monkeypatch):
    for sub in ("data", "checkpoints", "results"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(0)
        base = GPT(_E2E_CFG)
    convbase = root / "convbase.pt"
    torch.save({"model_config": asdict(_E2E_CFG), "model": base.state_dict(), "git_sha": "0" * 40, "step": 7, "val_loss": 1.234}, convbase)

    # DECODABLE ids only. ...
    live = torch.nonzero(~undecodable_ids_mask(from_json(tp.TOKENIZER_PATH), 8192)[0]).flatten()
    rng = np.random.default_rng(0)

    def _pair(stem, windows):
        n = windows * tp.BLOCK_SIZE + 1  # + 1: get_batch_memmap_masked needs a shifted target
        ids = rng.choice(live.numpy(), size=n).astype(np.uint16)
        bin_path, mask_path = root / "data" / f"{stem}.bin", root / "data" / f"{stem}_mask.bin"
        ids.tofile(bin_path)
        np.ones(n, dtype=np.uint8).tofile(mask_path)
        return bin_path, mask_path

    report = root / "factset.md"
    report.write_text("# fixture\n\n## Verdict\n\nGO\n", encoding="utf-8")

    monkeypatch.setattr(tp, "_REPO_ROOT", root)
    monkeypatch.setattr(tp, "FACTSET_REPORT", report)
    monkeypatch.setattr(tp, "CONVBASE_BEST", convbase)
    val_bin, val_mask = _pair("dialog_val", 3)
    monkeypatch.setattr(tp, "DIALOG_VAL_BIN", val_bin)
    monkeypatch.setattr(tp, "DIALOG_VAL_MASK", val_mask)
    replay_bin, replay_mask = _pair("dialog_train", 4)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_BIN", replay_bin)
    monkeypatch.setattr(tp, "DIALOG_TRAIN_MASK", replay_mask)

    # TWO steps, not one ... at step 0 every `lora_A` gradient is exactly 0.0 ...
    monkeypatch.setattr(tp, "MAX_STEPS", 2)
    monkeypatch.setattr(tp, "WARMUP_STEPS", 1)
    monkeypatch.setattr(tp, "BATCH_SIZE", 1)
    monkeypatch.setattr(tp, "EVAL_INTERVAL", 1)
    monkeypatch.setattr(tp, "CHECKPOINT_INTERVAL", 1)

    monkeypatch.setattr(tp, "preflight_device", lambda strict=True: {"device": "cpu", "cc": None, "torch": torch.__version__})
    monkeypatch.setattr(tp, "RuntimeConfig", lambda: RuntimeConfig(device="cpu"))
```
Phase 27: copy as a local helper (do not import across test modules); `n_layer=2` per D-31; keep `block_size=tp.BLOCK_SIZE`. `_pair("dialog_train", 4)` is what makes the fresh arm and the replay seam runnable; the attacker/control arms get bins from `tp.build_arm_bins(..., prefix="phase27")` under the redirected `_REPO_ROOT`. The `tests/test_lora_toggle.py:40-43` `_tiny_config()` (`ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)`) is the same shape — `_E2E_CFG` is preferred because its `block_size` matches the packer.

**Spy on the loop binding** (`tests/test_phase22_wiring.py:821-831`) — reuse for `::test_offset_stream_hash_covers_every_draw` (teaching AND replay draws in call order):
```python
    loader = _Spy()
    monkeypatch.setattr(loop_mod, "get_batch_fact_aligned", loader)

    seen = {}
    real_train = tp.train

    def _spy_train(**kwargs):
        seen.update(kwargs)
        return real_train(**kwargs)

    monkeypatch.setattr(tp, "train", _spy_train)
```
Phase 27: wrap `loop_mod.get_batch_memmap_masked` with a delegating spy that records `(bin_path, len(ix))` per call and assert the recorder's stream length equals `sum(len(ix))` and the bin-path sequence is `[train_bin]*accum + [replay_bin]*ceil(replay_windows/batch)` per step. `::test_on_draw_none_is_byte_neutral`: seed `np.random.seed(7)`, call the loader with `on_draw=None`, reseed, call with a recorder, compare `x, y` tensors equal and the recorded `ix` equals a third reseeded `np.random.randint(0, len(data) - block_size - 1, size=batch_size)`.

**Analog C — provenance recompute from BYTES, all drifted collected:** `tests/test_phase24_record.py:288-335`
```python
def test_the_provenance_pins_match_the_live_module_bytes():
    pins = dict(_record()["provenance"]["module_sha256"])
    assert pins, "provenance.module_sha256 is empty — this assertion would be vacuous"

    # The emitter must pin ITSELF, or the record cannot claim its own reproducibility.
    emitter = str(pathlib.Path(rec.__file__).resolve().relative_to(_ROOT))
    assert emitter in pins, (...)

    drifted = []
    for name, recorded in pins.items():
        path = _ROOT / name
        assert path.is_file(), f"provenance pins {name}, which does not exist at {path}"
        live = hashlib.sha256(path.read_bytes()).hexdigest()
        if live != recorded:
            drifted.append((name, recorded, live))

    assert not drifted, (
        f"{len(drifted)} of {len(pins)} provenance digests no longer match the files on disk:\n"
        + "".join(f"    {name}\n      recorded {rec_}\n      live     {liv}\n" for name, rec_, liv in drifted)
        + ...
    )
```
Phase 27 `::test_provenance_digests_match_live_bytes` — both-state (skip body when the record is absent, assert untracked); additionally assert `set(pins) == set(phase27_prereg/relearn PINNED_MODULES)` and that `scripts/phase27_relearn.py` (the emitter) is among them.

**Analog D — watched RED on a `tmp_path` COPY:** `tests/test_phase25_calibrate.py:570-586`
```python
def test_the_freshness_guard_goes_red_on_one_edited_byte(tmp_path):
    original = cal.MODULE_PATH.read_bytes()
    recorded = _clip()["provenance"]["module_sha256"]
    assert hashlib.sha256(original).hexdigest() == recorded

    edited = tmp_path / "phase25_calibrate.py"
    edited.write_bytes(original + b"\n# one byte more\n")
    assert hashlib.sha256(edited.read_bytes()).hexdigest() != recorded

    # ...and the real tree is still clean, byte for byte.
    assert cal.MODULE_PATH.read_bytes() == original
```
Apply to: the D-35 digest guard, the D-06 frontier pin, the D-33 rows (flip one `cleared_a` in a deep copy → the re-derivation disagrees), and the D-10 kwargs trace (rename one kwarg in an `ast` copy → RED).

**Analog E — `inspect.signature` on a keyword-only parameter:** `tests/test_phase23_resume.py:355-359`
```python
    import inspect

    param = inspect.signature(tp.train_arm).parameters["resume_from"]
    assert param.default is None
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
```
Phase 27 `::test_gate_baseline_is_required_and_pinned`: `param = inspect.signature(phase27_prereg.gate).parameters["baseline"]; assert param.kind is KEYWORD_ONLY and param.default is inspect.Parameter.empty`; `::test_the_curve_cannot_reach_the_verdict`: `assert not {"curve", "band", "rungs"} & set(inspect.signature(phase27_prereg.gate).parameters)` (RELRN-03). `::test_main_passes_only_kwargs_the_legs_accept`: walk `ast` of `main` for `Call` nodes whose func is `run_<leg>` (or the dispatch dict), collect keyword names, and assert each ⊆ `inspect.signature(run_<leg>).parameters` and every parameter without a default is supplied.

**Node-id existence (D-36):** subprocess `[sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/test_phase27_relearn.py"]` (the `tests/test_phase26_canary.py:284-300` fresh-interpreter shape) and assert every `apparatus.legs[*].refusal_node_id` / `e2e_node_id` in the record is a line of the output. Both-state on the record.

---

### `tests/test_phase23_resume.py` (test register) — MODIFY ONLY IF a new `train_arm(` substring lands

**Analog:** itself, lines 60-134 and 260-285:
```python
_TRAIN_ARM_CALL_SITES = (
    ("scripts/phase17_isolation.py", "call", "run_one_persona_training"),
    ...
    ("scripts/phase25_probe2.py", "call", "train_control_path"),
    ("scripts/teach_persona.py", "call", "main"),
    ...
    ("tests/test_phase22_wiring.py", "prose", "test_cli_names_no_sigma_or_clip_value comment"),
    ("tests/test_phase23_resume.py", "call", "_resume_call (the refusal probes)"),
    ("tests/test_phase23_resume.py", "call", "_run (the production MPS probe)"),
)
...
    hits = subprocess.run(["grep", "-rn", "train_arm(", "--include=*.py", "scripts", "tests"], ...).stdout.strip().splitlines()
    assert len(hits) == len(_TRAIN_ARM_CALL_SITES), (...)
    # Per-FILE counts, so a site moving between files cannot cancel out in the total.
```
Under OQ1-B (`tp.train()` direct) no Phase 27 code calls `train_arm`, so the only risk is PROSE: a docstring or comment in `scripts/phase27_*.py` or `tests/test_phase27_*.py` containing the substring `train_arm(`. Write "`train_arm`" without the paren in prose, and this file stays untouched. If a hit is unavoidable, append `("scripts/phase27_relearn.py", "prose", "<where>")` rows in the file's own comment style and re-run `tests/test_phase23_resume.py::test_resume_from_none_is_inert`. Also note `_RESUME_PASSERS` (`:345-353`): Phase 27's `resume_from=` goes to `tp.train()`, not `train_arm`, so that map is untouched too.

---

### `results/phase27_admission.json` (artifact, write-once)

**Analog:** the blob `phase26_canary.emit` writes (`scripts/phase26_canary.py:680-708`, excerpt above) + `results/phase24_token_budget.json::provenance` (`module_sha256` dict keyed by repo-relative path, `tokenizer_sha256`, guarded by `tests/test_phase24_record.py:288`). Required top-level fields (D-07, D-11, D-12, D-33, D-35, D-36): `governs` (a sentence quoting `phase27_prereg.COMMITTED`), `verdict: {verdict, reasons}`, `tallies`, `tallies_by_leg`, `cleared_counts: {a, b, c, by_leg}`, `rows: [44 × {point_key, arm, leg, verdict, cleared_a, cleared_b, cleared_c, refused}]`, `frontier_path`, `frontier_sha256`, `frontier_bytes`, `x: {value, n_questions, tolerated, tolerance_sentence}` (from `mitigation_gate.tolerance_report`), `baselines`, `attacker_corpus: {definition, sha256}`, `disjointness: {overlaps: 0, checked: N}` (computed at admit on the REAL fact set — CPU-safe? `render_episodes` needs no torch but `teach_persona` imports torch at module scope; compute it inside `admit` after a lazy import, or via `phase14_factset.render_family` directly), `apparatus: {status: "not exercised", reason: "gate read MOOT", legs: [...], fresh_curve_disclosure: "the five pinned fresh adapters are 200-step endpoints; a 400-step fresh curve requires retraining (RESEARCH M9)"}`, `provenance: {module_sha256, git_sha, head_at_write, written_utc, torch_version}`. `json.dumps(sort_keys=True)` via `atomic_write_json` — key order in the file is alphabetical regardless of the dict literal.

---

## Shared Patterns

### `_prove` → `SystemExit` (never `assert`) in every new script module
**Source:** `scripts/phase26_prereg.py:68-71`; `scripts/phase26_canary.py:90-92`
**Apply to:** `phase27_prereg.py`, `phase27_relearn.py`
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase27_prereg] {message}")
```
Tests catch `pytest.raises(SystemExit)` and assert a substring of the message (`"REFUSING"`, the verdict read, the file named).

### Sibling import via `sys.path` insert; torch and model modules LAZY inside legs
**Source:** `scripts/phase26_prereg.py:39-49` (prereg, CPU-only), `scripts/phase26_canary.py:46-60` (driver, `phase25_run` CPU-safe at import), `scripts/phase25_recall.py:149-150` (`# LAZY — torch-touching`)
**Apply to:** both scripts, both tests. Enforced by the AST test (`tests/test_phase26_canary.py:252-267`).

### By-reference constants; identity asserted with `is` in tests
**Source:** `scripts/phase26_prereg.py:79, 199, 211-212`; `tests/test_phase26_prereg.py:103, 248`
**Apply to:** `MARGIN_K`, `CURVE_K`, `F_Y`, `HELD_OUT_FAMILY`, `GATED_TIER`, `K`; X and Y thresholds are CALLS (`extraction_ceiling(**kw)`, `F_Y * control_taught_recall`) on frontier/control-record values, never literals.

### Three-valued verdict domain with INCONCLUSIVE precedence; `reasons` carry counts with denominators
**Source:** `scripts/phase26_prereg.py:288-329`; `scripts/erasure_gate.py:173-197`
**Apply to:** `relearning_is_worth_attempting` (ADMITTED/MOOT/INCONCLUSIVE), the recovery `gate` (PASS/FAIL/INCONCLUSIVE + Z-undefined ⇒ INCONCLUSIVE per leg, D-25/D-28). Never a bare rate; `k/416`, `k/1008`, steps and scored-token counts side by side (D-23).

### Write-once artifact, `refuse_if_dirty` before hashing, `atomic_write_json`, operator commits by hand
**Source:** `scripts/phase26_canary.py:475-504, 709`; `src/personacore/provenance.py:47-79`; `scripts/phase25_run.py:118-140`
**Apply to:** `admit`. The driver builds NO `["git", "add"|"commit", …]` argv — the only git argv is the read-only `ls-files` conjunct in `_require_admitted`; `git_sha()` from `personacore.provenance` supplies the SHA.

### Gated on the COMMITTED record: two conjuncts (verdict string AND tracked), first statement of every leg
**Source:** `scripts/phase23_run.py:860-875` (tracked conjunct via `git ls-files`); `scripts/phase26_prereg.py:300` (domain conjunct)
**Apply to:** `run_calibrate`, `run_curve`, `run_gate`, `run_structural_proof` — each opens with `record = _require_admitted(record_path)`. Watched RED per leg in tests, then once more by hand against the real MOOT record at close (D-37).

### Sha256 pins both ways: frontier bytes == record; adapter on disk == pinned; module bytes == provenance; corpus render == pinned
**Source:** `scripts/phase26_canary.py:99-100, 682, 689`; `tests/test_phase26_canary.py:786-809`; `tests/test_phase24_record.py:318-324`
**Apply to:** `admit` (writes), `tests/test_phase27_relearn.py` (recomputes from bytes, never via the emitter's helper), every leg's adapter load (`_prove(_sha256(adapter) == pinned["sha256"])` before scoring — `phase25_recall.py:124-128` shape; D-22).

### Ancestry guard over the prereg module; honest with zero tracked artifacts
**Source:** `tests/test_phase26_prereg.py:51-98`
**Apply to:** `scripts/phase27_prereg.py` vs `git ls-files results/phase27_*`. Memory rule: never edit `phase27_prereg.py` after the record is committed — corrections go in a dated continuation module.

### Budget symbols imported, never retyped; ONE `TrainConfig` instance
**Source:** `scripts/phase23_run.py:620-623, 661-683`
**Apply to:** the three arms in `phase27_relearn.py`. D-26(ii) reads `load_checkpoint(...)["train_config"]` (`src/personacore/checkpoint.py:135`) back off disk per arm and diffs against `asdict(cfg)`.

### Skip markers for host-only inputs; both-state idiom for the record
**Source:** `tests/test_phase26_canary.py:33-35, 63-69, 385-398`
**Apply to:** `needs_adapters` on `::test_pinned_adapters_hash_on_host`; `if RECORD.exists(): … else: assert not tracked` on every record-reading test (the record is absent until the operator commits it).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `data/phase27_<arm>_offsets.bin` (gitignored) | sidecar | streaming append | No prior phase captured the sampler's draw stream. Nearest kin: `phase25_run.py:286-350` heartbeat JSONL appender (append-only, `data/`), but the payload here is raw `uint64` bytes + a bin tag. Shape is discretionary (CONTEXT); recommended: `hashlib.sha256()` updated per draw with `ix.astype("<u8").tobytes()` and a 1-byte bin index (`0` teaching, `1` replay), the same bytes written to the file so a differing digest can be located by offset (D-30). ~15 lines, plain closure. |

Two sub-pieces are written fresh but are compositions of imported functions, not new arithmetic: the Z rule (`max(first rung fresh clears (b), first rung control clears (b))`, `F_Y * control_full_budget_recall` as the threshold — RESEARCH Code Ex. 3's `b` conjunct at per-rung readings) and the ≈ band (`abs(m - f) <= MARGIN_K * phase23_prereg.noise_floor(fresh_readings)`).

## Metadata

**Analog search scope:** `scripts/` (phase26_prereg, phase26_canary, phase23_run, phase25_run, phase25_recall, erasure_gate, mitigation_gate, phase23_prereg, phase18_extraction, teach_persona [import-only]), `src/personacore/` (training/data.py, training/loop.py, checkpoint.py, provenance.py), `tests/` (test_phase26_prereg, test_phase26_canary, test_phase22_wiring, test_phase25_promotion, test_phase24_record, test_phase23_resume, test_phase25_calibrate, test_lora_toggle, test_phase21_replay_volume, test_phase20_correction, conftest), `.gitignore`
**Files scanned:** 24 (targeted ranges; `phase23_run.py` at 5,079 lines and `teach_persona.py` read only at grep-located ranges)
**Pattern extraction date:** 2026-09-14 (HEAD `b70daa8`)
