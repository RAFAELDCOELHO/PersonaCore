# Phase 30: Replay-Bearing Adversarial Recipe and Its Own Control - Pattern Map

**Mapped:** 2026-09-25 (HEAD 2c43bbd; every line number below re-read at this HEAD)
**Files analyzed:** 10 (3 new scripts/fixtures + 3 new tests + 4 modified)
**Analogs found:** 10 / 10

Developer rulings carried in (2026-09-25, after research):
- **A2 approved:** narrow `tests/test_phase22_wiring.py::test_non_dp_arm_cli_is_unchanged` to also exclude `tp.REPLAY_ARMS`, with a dated note in the existing 24-REVIEW register.
- **Ancestry-freeze ONLY the calibration emitter** (`scripts/phase30_calibration.py`) before `results/phase30_calibration.json`. The v5.0 driver (`scripts/phase30_points.py`) stays editable, and no ancestry test covers it.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/teach_persona.py` (MOD) | production caller / config | request-response (kwargs → `train()`) | itself: `DP_ARMS`/`ADV_ARMS` (:294, :310), `arm_spec` (:1201), `main` refusal (:1518), `train_arm` gate (:1752-2033) | exact (self) |
| `scripts/phase30_points.py` (NEW) | driver / service (torch-free) | transform + read-time validation | `scripts/phase25_points.py` (`point_plan` :234, `control_reading` :313) + `scripts/phase25_record.py::SWEEP_SCHEDULE` (:308) | exact |
| `scripts/phase30_calibration.py` (NEW) | emitter (write-once record) | batch / file-I/O | `scripts/phase27_relearn.py::admit` (:361-410) + `scripts/phase24_record.py::_row` (:146-200) | exact |
| `tests/fixtures/phase30_train_kwargs_presplit.json` (NEW) | test fixture | captured snapshot | spy in `tests/test_phase22_wiring.py:882-916` | role-match |
| `tests/test_phase30_seam.py` (NEW) | test (e2e CPU) | event-driven (`on_draw`) | `tests/test_phase22_wiring.py` (`_e2e_env` :706, spy :882) | exact |
| `tests/test_phase30_calibration.py` (NEW) | test (unit + git ancestry) | batch | `tests/test_phase27_relearn.py` (:110-116, :225-265) + `tests/test_phase29_prereg.py::_assert_frozen_before` (:69) | exact |
| `tests/test_phase30_points.py` (NEW) | test (unit + AST guard) | transform | `tests/test_phase25_points.py` (:36-91, :174-189) + `tests/test_phase29_prereg.py` AST helpers (:418-589) | exact |
| `tests/test_phase22_wiring.py` (MOD, A2) | test | — | its own dated 24-REVIEW narrowing note (:559-568) | exact (self) |
| `tests/test_phase23_resume.py` (MOD) | test register | — | its own `_TRAIN_ARM_CALL_SITES` entries (:60-147) | exact (self) |
| `scripts/phase25_points.py`, `scripts/phase29_prereg.py`, `scripts/phase24_adversarial.py`, `src/personacore/training/loop.py` | imported only | — | — | NOT edited (frozen / closed) |

## Pattern Assignments

### `scripts/teach_persona.py` (MODIFIED — seam split, `advr_*` arms, CLI refusal)

**Arm-tuple pattern** (`ARMS` :250-291, `ADV_ARMS` :310). Add `"advr_n8", "advr_n64"` to the end of `ARMS` with a comment block, and add a literal next to `ADV_ARMS`:
```python
ADV_ARMS = ("adv_n8", "adv_n64")
# (new) REPLAY_ARMS = ("advr_n8", "advr_n64")   # proved == phase29_prereg.ADVR_ARMS by a test
```
Never append to `ADV_ARMS` (see `phase29_prereg.py:14-16`: `phase25_verdict.curve_verdicts` would match two legs). Do not import `phase29_prereg` at module scope; the lazy-import register is at `arm_spec` :1236-1243 (`import phase21_filler` inside the branch).

**`arm_spec` branch** (:1201). The existing adv branches return `fs.LOCKED_FACTS, False, 0.0` (adv_n8) and the `phase21_filler` lazy form (adv_n64). New branch delegates to the twin:
```python
if arm in REPLAY_ARMS:
    return arm_spec({"advr_n8": "adv_n8", "advr_n64": "adv_n64"}[arm])
```
(`phase29_prereg._V4_TWIN` at :101 is the same map; it is private, so restate it here, and a test proves `arm_spec(advr_x) == arm_spec(adv_x)`.)

**CLI refusal** (`main` :1516-1528):
```python
    if arm in DP_ARMS:
        dp_sigma, dp_clip_norm = _parse_dp_flags(argv[1:])
    elif arm in ADV_ARMS:
        raise SystemExit(
            f"[teach_persona] {arm} carries NO adversarial_ratio from this CLI, ..."
```
Change to `elif arm in ADV_ARMS or arm in REPLAY_ARMS:` and reuse the message, which adds no new `train_arm(` text. `USAGE` (:1435-1448) line `f"\n{'|'.join(ADV_ARMS)} are PROGRAMMATIC-ONLY ..."` should also list `REPLAY_ARMS`. Keep exactly one `train_arm(` occurrence in that string (it is a registered prose hit in `test_phase23_resume.py:126`).

**Gate split (`train_arm`)**. Current sites, verified:
- :1752 `is_dp = arm in DP_ARMS` (comment :1750-1751 says "ONE boolean gates all FOUR D-08 wirings". Update it.)
- :1753 sigma/clip refusal stays `is_dp`
- :1801 `_refuse_cross_device_resume` stays `is_dp`
- **:1815 `if is_dp and (not DIALOG_TRAIN_BIN.exists() ...)` moves to `gets_replay`** (RESEARCH F1 / Pitfall 2. CONTEXT does not list this one.)
- :1914-1926 `dp_fn = DPSGD(...) if is_dp else None` stays
- :1949 `dp_accum = dict(grad_accum_steps=stats["n_facts"]) if is_dp else {}` stays byte-identical
- :1950-1975 `dp_kwargs = (dict(...) if is_dp else {})` becomes one dict gated on `gets_replay`
- :2025 DP provenance print stays `is_dp`

Current `dp_kwargs` shape (:1950-1975, comments elided):
```python
    dp_kwargs = (
        dict(
            fact_bin=fact_bin_path(paths["bin"]),
            n_facts=stats["n_facts"],
            replay_bin=DIALOG_TRAIN_BIN,
            replay_mask_bin=DIALOG_TRAIN_MASK,
            replay_windows=replay_window_budget(stats["n_facts"]) // BLOCK_SIZE,
            dp_fn=dp_fn,
        )
        if is_dp
        else {}
    )
```
Target shape. It must stay ONE `dp_kwargs = dict(...)` Assign and ONE `**dp_kwargs` splat in `train(...)` (:1977-2021), or `tests/test_phase23_matched_prereg.py::test_the_dp_wiring_keys_match_the_live_caller` (:136) and `::test_the_train_call_keys_match_the_live_caller` (:147) go red against the frozen EDIT-ONCE census:
```python
    dp_kwargs = (
        dict(
            fact_bin=fact_bin_path(paths["bin"]) if is_dp else None,
            n_facts=stats["n_facts"] if is_dp else None,
            replay_bin=DIALOG_TRAIN_BIN,
            replay_mask_bin=DIALOG_TRAIN_MASK,
            replay_windows=replay_window_budget(stats["n_facts"] if is_dp else len(facts)) // BLOCK_SIZE,
            dp_fn=dp_fn,
        )
        if gets_replay
        else {}
    )
```
`stats["n_facts"]` does not exist on a flat build (F1), hence `len(facts)`. **Textual trap:** `tests/test_phase22_wiring.py::test_the_prose_vs_code_measurement_is_still_true` (:399) pins `source.count("grad_accum_steps") == 14`. Do not write that word in any new comment.

---

### `scripts/phase30_points.py` (NEW — v5.0 driver, torch-free at import)

**Analog:** `scripts/phase25_points.py`, which it imports and does not edit, plus `scripts/phase29_prereg.py`.

**Header / imports pattern** (`phase25_points.py:48-69`):
```python
import hashlib
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import phase25_prereg  # noqa: E402  (same)
...
SWEEP_SEED = phase25_prereg.REPRODUCTION_PROVENANCE["seed"]
```
For v5.0, import `phase25_points`, `phase29_prereg`, `mitigation_budget`, `phase24_adversarial` (all torch-free, measured F6). Re-export `SWEEP_SEED = phase25_points.SWEEP_SEED`. Never `import phase25_epsilon`: the DEBT-04 census `tests/test_phase29_prereg.py:581-589` globs `scripts/phase29_*..phase34_*` and flags it.

**`_prove` register** (`phase25_points.py:104-106`):
```python
def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_points] {message}")
```
Use `[phase30_points]`. Never `assert` (`phase29_prereg.py:71-74`: `python -O` strips it).

**SWEEP_SCHEDULE pattern.** Analog `phase25_record.py:308-339`: a function over the canonical keys, head plus remainder, permutation proved on every call.
```python
    keys = ORDERED_POINT_KEYS()
    ...
    schedule = head + tuple(key for key in keys if key not in head)
    _prove(
        len(schedule) == len(keys) and set(schedule) == set(keys),
        f"the schedule is not a permutation of the pinned key set ({len(schedule)} vs {len(keys)})",
    )
    return schedule
```
v5.0 head = `tuple(phase29_prereg.control_key(leg) for leg in phase29_prereg.LEGS)`. Keys from `phase29_prereg.POINT_KEYS()` (:112), `control_key` (:120), `leg_keys` (:126).

**`point_plan` pattern.** Analog `phase25_points.py:234-263`. Re-implement it; do NOT call it, because `parse_point_key` refuses `advr_*`. Keep the same dict keys so the reused `train_stage(plan)` (:350) / `measure_stage(plan, training)` (:536) accept it:
```python
    return {
        "point_key": point_key,
        "arm": arm,
        "axis": axis,
        "axis_value": axis_value,
        "is_dp": dp,
        "is_control": dp and axis_value == 0.0,
        "n_facts": n_facts_for(arm),
        "seed": SWEEP_SEED,
        "prefix": prefix_for(point_key),
        "dp_sigma": axis_value if dp else None,
        "dp_clip_norm": (...),
        "adversarial_ratio": axis_value if not dp else 0.0,
        "pinned_mechanism": pinned_mechanism(arm, axis_value),
        "point_epsilon": epsilon,
        "accounting": accounting,
        "control_key": control_key_for(arm),     # <- WR-05 root (:160); v5.0 uses phase29_prereg.control_key(leg)
    }
```
v5.0 values: `axis="ratio"`, `is_dp=False`, `is_control = key == phase29_prereg.control_key(leg)`, `axis_value` = the exact `phase29_prereg.RATIO_GRID` member found by index-matching `phase29_prereg.point_key(arm, r) == key`, `dp_sigma=None`, `dp_clip_norm=None`, `pinned_mechanism = phase25_points.pinned_mechanism("adv_n8", ratio)` (the adv branch at :194-200 never parses), `point_epsilon=None`, `accounting=None`. `prefix` must not start with `phase25_points.CALIBRATION_PREFIX_LITERAL` (:72), same `_prove` as `prefix_for` :165-174.

**Own-control reader pattern.** Analog `phase25_points.control_reading` (:313-331), with its TRACKED-only rule:
```python
def control_reading(arm, tracked):
    key = control_key_for(arm)
    relative = phase25_prereg.point_record_path(key)
    _prove(
        relative in set(tracked),
        f"the control record {relative} is not TRACKED (git ls-files), so `control_gap` for arm "
        f"{arm!r} cannot be read. ...",
    )
    record = json.loads((_ROOT / relative).read_text(encoding="utf-8"))
    group = record["condition_c"]
    return {"adapter_on": group["point_dialogue_ppl_on"], "adapter_off": group["point_dialogue_ppl_off"]}
```
v5.0 substitutes `phase29_prereg.control_key(leg)` and `phase29_prereg.point_record_path(ckey)` (:142), and adds the provenance checks from D-15/F8: `record["point_key"] == ckey`, `record["arm"] == f"advr_{leg}"`, `record["axis"] == "ratio"`, `record["q"] is None`, `record["clip_norm"] is None`, and recipe equality at read time (D-16). Reading `_ROOT` at call time keeps the `monkeypatch.setattr(pts, "_ROOT", tmp_path)` test idiom working (`test_phase25_points.py:184`).

**Recipe identity.** Fields = `phase29_prereg._RECIPE_FIELDS` (:218, `{"replay_windows","n_facts","seed","max_steps"}`) + `min_refusal_scored_tokens` (`phase24_adversarial.MIN_REFUSAL_SCORED_TOKENS`, :97) + `replay_source` (resolve from `phase29_prereg.REPLAY_SOURCE` names :168; never type `"data/dialog_train.bin"`). Values: `phase29_prereg.replay_windows(n)` (:171, lazy torch), `mitigation_budget.STEP_BUDGET` (:508), `SWEEP_SEED`. The shape must pass `phase29_prereg.refused_record` (:230-270) for the `_RECIPE_FIELDS` subset.

**D-19 short-circuit.** Reuse `phase29_prereg.control_is_unlearnable` (:190) and `phase29_prereg.refused_record` (:230), which builds and writes nothing. Do not restate the inequality.

**Reusable from `phase25_points` unchanged:** `train_stage`, `measure_stage`, `taught_mapping` (:278), `seed_spread` (:297), `attack_corpus` (:637), `scoring_values` (:655), `pinned_mechanism` (:177), `SWEEP_SEED`, `CALIBRATION_PREFIX_LITERAL`. **Forbidden (WR-05 carriers / advr parsers):** `control_key_for` (:160), `control_reading` (:313), `point_plan` (:234), `prefix_for` (:165), `exact_axis_value` (:125), `n_facts_for` (:150), `record_kwargs` (:731), `_adversarial_extras` (:686), `phase25_promotion.control_readings`. Do not monkeypatch-assign any of them (process-wide mutation of a frozen module).

---

### `scripts/phase30_calibration.py` (NEW — ARECIPE-02 emitter, ancestry-frozen)

**Analog 1, emitter register:** `scripts/phase27_relearn.py`

Imports (:36-53):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase24_adversarial  # noqa: E402  (same — torch-free at import)
import phase25_run  # noqa: E402  (same — CPU-safe at import; torch stays lazy)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()
```
Write-once, then dirty tree, then build, then provenance, then atomic write (`admit` :361-410):
```python
    out_path = pathlib.Path(out_path)
    # teach_persona.refuse_if_exists' semantics, reproduced: that module imports torch.
    _prove(
        overwrite or not out_path.exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. ... Pass --force to overwrite deliberately.",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){_rel(out_path)}",)
    refuse_if_dirty(who="phase27_relearn", detail=(...), pathspec=pathspec, cwd=_ROOT)
    blob = build_record(frontier())
    ...
    blob["provenance"] = {
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": _utc(),
        ...
    }
    phase25_run.atomic_write_json(out_path, blob)
```
Output path: `_ROOT / next(p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase30_"))`. Resolve by membership and never retype it (`phase29_prereg.py:150`). `os.replace` is census-restricted to `phase25_run.py`/`phase25_record.py`, so use `phase25_run.atomic_write_json` (:118). CLI: `if __name__ == "__main__": raise SystemExit(main())` (`phase27_relearn.py:1207`). The operator commits by hand.

**Analog 2, live bin measurement:** `scripts/phase24_record.py::_row` (:146-160) + `_tokenizer` (:137-140):
```python
def _tokenizer():
    seed_everything(tp.SEED)
    return from_json(tp.TOKENIZER_PATH)

    stats = tp.build_bins(
        _tokenizer(), episodes, bin_path, mask_path,
        align_facts=None, adversarial_ratio=ratio, seed=tp.SEED,
    )
    total_tokens = int(stats["tokens"])
    scored_tokens = int(np.fromfile(mask_path, dtype=np.uint8).sum())
    floor, _ceiling = tp.MASK_FRACTION_BAND
```
`tp.build_bins` signature: `teach_persona.py:507-517` (no arm parameter; that is the structural reason advr and adv bins match). Build into a `tempfile` dir, never through `build_arm_bins` into real `data/` (RESEARCH Runtime State). `import teach_persona as tp` stays LAZY inside the build function (torch at import).

**Analog 3, the rule being re-derived:** `scripts/phase24_adversarial.py:83-113`. Constants to IMPORT: `MIN_REFUSAL_SCORED_TOKENS` (:97), `MASK_FRACTION_MARGIN` (:113). Band from `tp.MASK_FRACTION_BAND` (`teach_persona.py:128`). Core (RESEARCH Code Examples):
```python
target = tp.MASK_FRACTION_BAND[0] + pa.MASK_FRACTION_MARGIN
frac = lambda L: (S + P * L) / (T0 + prompt + P * L)
L = next(L for L in itertools.count(1) if frac(L) >= target)
_prove(L == pa.MIN_REFUSAL_SCORED_TOKENS, "... D-08: STOP for the developer's ruling")
```
Grid corners: `mitigation_budget.ADVERSARIAL_RATIO_GRID[0]` / `[-1]`. Also prove `tp.MAX_STEPS == mitigation_budget.STEP_BUDGET` and `tp.SEED == phase25_points.SWEEP_SEED` (F6).

---

### `tests/fixtures/phase30_train_kwargs_presplit.json` (NEW — Wave 0, captured BEFORE the split)

**Analog:** the `tp.train` spy in `tests/test_phase22_wiring.py:896-905`:
```python
    seen = {}
    real_train = tp.train

    def _spy_train(**kwargs):
        seen.update(kwargs)
        return real_train(**kwargs)

    monkeypatch.setattr(tp, "train", _spy_train)
```
Capture-and-stop variant: record the kwargs, then `raise SystemExit("[probe] captured")` instead of calling `real_train`. Normalise paths relative to `tmp_path`, `dp_fn` to `{sigma, clip_norm}` or None, and `train_config` via `dataclasses.asdict`. The capture helper must live in `tests/test_phase30_seam.py` so the fixture and the assertion use one function. DP arms need `dp_sigma=_FIXTURE_SIGMA, dp_clip_norm=_FIXTURE_CLIP` (`test_phase22_wiring.py:700-701`).

---

### `tests/test_phase30_seam.py` (NEW — ARECIPE-01)

**Analog:** `tests/test_phase22_wiring.py`. Import the env builder, following the `test_phase23_resume` cross-test import precedent:
```python
from test_phase22_wiring import _e2e_env, _FIXTURE_SIGMA, _FIXTURE_CLIP
```
`_e2e_env(root, monkeypatch)` (:706-783) monkeypatches `tp._REPO_ROOT`, `DIALOG_TRAIN_BIN/MASK` (4 windows), `MAX_STEPS=2`, `BATCH_SIZE=1`, and CPU preflight. Read `tp.DIALOG_TRAIN_BIN` AFTER calling it.

D-04 measured replay count (RESEARCH Code Examples, prototype passed 1.90 s): spy wraps `real(**kw, on_draw=on_draw)`, and counts `len(ix)` by `pathlib.Path(bin_path) == pathlib.Path(tp.DIALOG_TRAIN_BIN)`. Assert `drawn["replay"] / tp.MAX_STEPS == phase29_prereg.replay_windows(len(facts)) > 0`. Parametrize over both `REPLAY_ARMS` (RESEARCH Open Q3).

Non-DP negative-control shape to mirror for `adv_*` (:907-913):
```python
    for absent in ("fact_bin", "n_facts", "replay_bin", "replay_mask_bin", "replay_windows"):
        assert absent not in seen, f"{arm!r} was handed {absent}={seen[absent]!r}"
    assert seen.get("dp_fn") is None
```
Replay-source guard test: `_e2e_env`, delete `tp.DIALOG_TRAIN_BIN`, then `train_arm("advr_n8", ...)` raises SystemExit and no bin exists under `tmp_path/data`.

---

### `tests/test_phase30_calibration.py` (NEW — ARECIPE-02 + D-11)

**Dirty-tree recorder fixture** (`tests/test_phase27_relearn.py:109-116`):
```python
@pytest.fixture(autouse=True)
def clean_tree(monkeypatch):
    calls = []
    monkeypatch.setattr(relearn, "refuse_if_dirty", lambda **kw: calls.append(kw) or "")
    return calls
```
**Write-once test** (:225-242): branch on whether the real record exists. If it does, assert refusal and unchanged bytes. If not, write to `tmp_path` twice and assert "REFUSING to overwrite".
**Dirty-first ordering** (:245-265): stub the builder to `raise SystemExit("[probe] stopped after the dirty check")` and assert `(call,) = clean_tree` with `call["who"]`, `call["cwd"] == _ROOT`, `call["pathspec"]`.

**Ancestry (D-11 + emitter freeze):** `from test_phase29_prereg import _assert_frozen_before, _git` (:52, :69). Pattern from `test_phase29_prereg.py:109-117`:
```python
    tracked = sorted({path for spec in phase29_prereg.ARTIFACT_PATHSPECS for path in _git("ls-files", spec).split()})
    _assert_frozen_before(PREREG, tracked)
```
Phase 30 uses two directions: (1) `_assert_frozen_before("scripts/phase30_calibration.py", [calibration])` (the emitter-only freeze ruling; honest-green while the calibration is untracked). (2) The calibration's first-add is a strict ancestor of every tracked `results/phase31_*` / `phase32_*` first-add, and the test goes red if any of those is tracked while the calibration is not. Natural non-vacuity RED precedent: `test_call_time_sources_are_frozen_before_every_v5_result` (:130-146) with `pytest.raises(subprocess.CalledProcessError)`. Do NOT add the driver `scripts/phase30_points.py` to any ancestry test (ruling).

---

### `tests/test_phase30_points.py` (NEW — ACTRL-01/02 + AST guard)

**Schedule test analog** (`tests/test_phase25_points.py:36-53`):
```python
    schedule = rec.SWEEP_SCHEDULE()
    keys = rec.ORDERED_POINT_KEYS()
    assert len(schedule) == 44 and sorted(schedule) == sorted(keys)
    head = schedule[:8]
    assert head[:2] == ("dp_n8_sigma0p000000", "dp_n64_sigma0p000000")
```
v5.0: 12 keys, `head[:2] == tuple(phase29_prereg.control_key(l) for l in phase29_prereg.LEGS)`, derived and not typed. Mind the `== 10` literal census (`tests/test_phase21_sc5.py`): write `len(keys) - len(LEGS)`, not `10`.

**Torch-free fresh-interpreter test** (:76-91), copied verbatim with `phase30_points` / `SWEEP_SCHEDULE()`.

**Tracked-control test** (:174-189): `pytest.raises(SystemExit)` + `"not TRACKED"`, then a `tmp_path` record plus `monkeypatch.setattr(pts, "_ROOT", tmp_path)`. For D-15, build the relabelled fixture from the REAL `results/phase25_point_dp_n8_sigma0p000000.json` (relabel `point_key`/`arm` only) and assert refusal on `axis`/`q`/`clip_norm`.

**AST guard helpers** (`tests/test_phase29_prereg.py`): `_accountant_failures` (:499-515) is the Import/Name/Attribute walker to copy for the WR-05 carrier set; `_planted(tmp_path, source, planted, name)` (:518-523) gives planted-RED on a copy; the glob-census shape is `test_no_v5_module_uses_the_accountant` (:581-589):
```python
    modules = sorted(p for n in range(29, 35) for p in _SCRIPTS.glob(f"phase{n}_*.py"))
    assert modules, "... the census is blind"
    for path in modules:
        assert _accountant_failures(path.read_text(encoding="utf-8")) == [], path
    # NON-VACUITY: the matcher fires where the accountant certainly is imported and called.
```
Use range(30, 35). Exempt docstring `Expr` constants. Flag string constants that fully match `^dp_n\d+(_sigma\d+p\d+)?$`, f-strings with literal head `dp_n`, and Name/Attribute in `{control_key_for, control_reading, record_kwargs, control_readings, _adversarial_extras}`, plus `point_plan`/`prefix_for`/`n_facts_for`/`exact_axis_value` only as `phase25_points.` attributes (the v5.0 module defines its own `point_plan`). Non-vacuity: `phase25_points.py` itself must trip the matcher.

---

### `tests/test_phase22_wiring.py` (MODIFIED — A2, approved)

Line 568 today:
```python
    non_dp = [arm for arm in tp.ARMS if arm not in tp.DP_ARMS and arm not in tp.ADV_ARMS]
```
Add `and arm not in tp.REPLAY_ARMS`, and append a dated paragraph `NARROWED 2026-09-25 (Phase 30 A2): ...` to the docstring directly after the 24-REVIEW paragraph (:559-567), in the same register. Touch nothing else in this file (golden/e2e tests stay unmodified).

### `tests/test_phase23_resume.py` (MODIFIED — register)

`_TRAIN_ARM_CALL_SITES` (:60-147): add one `("tests/test_phase30_seam.py", "call", "<test name>")` entry with a comment, and one entry per `train_arm(` text hit in any new prose (docstrings/comments in `teach_persona.py`, `phase30_points.py`, and the tests all count). Bump the pinned `8 + 1 + ...` non-this-file call literal in `test_resume_from_none_is_inert` (:247+) by `+ 1` with its reason. The new test passes no `resume_from`, so `_RESUME_PASSERS` (:169) is unchanged. Cheapest path: word new prose so it avoids the literal `train_arm(` text (write "`train_arm`" without the paren) and register only the real call.

## Shared Patterns

### SystemExit invariant register
**Source:** `scripts/phase29_prereg.py:71-74`, `scripts/phase25_points.py:104-106`
**Apply to:** both new scripts
```python
def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase29_prereg] {message}")
```

### Constants by reference, never retyped
**Source:** `scripts/phase29_prereg.py:90-93` (`RATIO_GRID = mitigation_budget.ADVERSARIAL_RATIO_GRID`), guarded by `tests/test_phase29_prereg.py::_replay_literal_failures` (:437), `_grid_retype_failures` (:452)
**Apply to:** `phase30_points.py`, `phase30_calibration.py`. No literal `4`, `32`, `256`, `15`, `0.05`, `0.15`, `200`, `1337`, grid endpoints, or `"results/phase30_calibration.json"`. Reuse those two helpers over the new files (import them from `test_phase29_prereg`).

### Lazy torch
**Source:** `phase29_prereg.replay_windows` (:171-173 `import teach_persona` inside the function); `phase25_points.train_stage` (:352-354)
**Apply to:** `phase30_points.py` (torch-free at import, proven by a fresh-interpreter test) and `phase30_calibration.py` (import `teach_persona` inside the build function).

### Write-once + clean tree + atomic write
**Source:** `scripts/phase27_relearn.py:361-410`, `src/personacore/provenance.py:47-80` (`refuse_if_dirty(*, who, detail, pathspec=(), cwd=None)`), `scripts/phase25_run.py:118` (`atomic_write_json`)
**Apply to:** `phase30_calibration.py` only.

### Tracked-only reads of committed records
**Source:** `scripts/phase25_points.py:313-331` (`relative in set(tracked)`), with `tracked` from `git ls-files` handed in by the caller
**Apply to:** v5.0 own-control reader and the D-19 guard.

### Clean-tree / census pitfalls (repo-wide)
- `os.replace` only in `phase25_run.py`/`phase25_record.py`.
- `== 10` under `tests/` is counted by `tests/test_phase21_sc5.py`.
- `train_arm(` text in `scripts/`/`tests/` must be registered (`test_phase23_resume.py`).
- `grad_accum_steps` count in `teach_persona.py` is pinned at 14.
- New tests must never `skipif` on `data/`/`checkpoints/` (ubuntu skip pin, `tests/test_phase25_venue.py`).

## No Analog Found

None. Every file has an in-repo analog. The single-dict `gets_replay` shape has no prior instance, but it is a constrained edit of the existing `dp_kwargs` block, verified against the live census in RESEARCH F2.

## Metadata

**Analog search scope:** `scripts/` (teach_persona, phase24_adversarial, phase24_record, phase25_points, phase25_record, phase25_run, phase27_relearn, phase29_prereg), `src/personacore/provenance.py`, `tests/` (test_phase22_wiring, test_phase23_resume, test_phase23_matched_prereg, test_phase25_points, test_phase27_relearn, test_phase29_prereg)
**Files scanned:** 15
**Pattern extraction date:** 2026-09-25
