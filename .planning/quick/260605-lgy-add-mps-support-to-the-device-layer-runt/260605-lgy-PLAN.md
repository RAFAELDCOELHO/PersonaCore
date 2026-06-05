---
phase: quick-260605-lgy
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/personacore/config.py
  - src/personacore/preflight.py
  - scripts/preflight_demo.py
  - tests/test_config.py
  - tests/test_preflight.py
autonomous: true
requirements: [PRE-01]
must_haves:
  truths:
    - "On an M3 (no CUDA) RuntimeConfig() resolves device='mps' with amp forced False"
    - "On a CUDA P100 box RuntimeConfig() still resolves device='cuda' and the bf16-on-Pascal guard still raises"
    - "On a CPU-only box RuntimeConfig() resolves device='cpu' with amp False (unchanged)"
    - "preflight_device detects in priority order CUDA-P100 -> MPS -> CPU and returns an env-summary dict"
    - "preflight_p100 no longer exists (hard rename, not an alias)"
    - "The full CPU-only test suite stays green with no MPS/CUDA hardware required"
  artifacts:
    - path: "src/personacore/config.py"
      provides: "RuntimeConfig with MPS detection + fp32/AMP-off-on-MPS posture"
      contains: "mps"
    - path: "src/personacore/preflight.py"
      provides: "preflight_device with CUDA-P100 -> MPS -> CPU priority"
      contains: "def preflight_device"
    - path: "scripts/preflight_demo.py"
      provides: "thin caller updated for the rename"
      contains: "preflight_device"
    - path: "tests/test_preflight.py"
      provides: "renamed + MPS-extended preflight tests (CPU-only)"
      contains: "preflight_device"
  key_links:
    - from: "src/personacore/config.py::_default_device"
      to: "torch.backends.mps.is_available"
      via: "MPS detection branch after CUDA"
      pattern: "torch\\.backends\\.mps\\.is_available"
    - from: "scripts/preflight_demo.py"
      to: "src/personacore/preflight.py::preflight_device"
      via: "import + call"
      pattern: "from personacore.preflight import preflight_device"
---

<objective>
Add MPS (Apple Silicon) as a first-class device in the device layer, ahead of Phase 5, per the
LOCKED Phase-5 decisions D-01/D-02. Two source files change behavior and two thin callers/tests
follow the hard rename.

Purpose: D-01 moves the shipped Phase-5 training run onto the user's M3/MPS. The device-layer
change is the gating prerequisite — RuntimeConfig must resolve `device="mps"` (fp32, AMP off,
mirroring the CPU posture) and the preflight gate must accept MPS as a usable device while
keeping the P100/CUDA path intact (Kaggle fallback).

Output:
- `RuntimeConfig` detects `torch.backends.mps.is_available()` and forces fp32/AMP-off on MPS.
- `preflight_p100` HARD-renamed to `preflight_device` with priority CUDA-P100 -> MPS -> CPU.
- `scripts/preflight_demo.py` + preflight tests updated for the rename; MPS coverage added.
- CPU-only test suite stays green; ruff lint+format pass.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/05-tinystories-pretraining/05-CONTEXT.md

<interfaces>
<!-- Current contracts the executor edits. Use these directly — no further exploration needed. -->

src/personacore/config.py (current):
```python
def _default_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"

def _is_pascal(device: str) -> bool:  # True iff CUDA GPU with cc major < 7. UNCHANGED.

@dataclass
class RuntimeConfig:
    device: str = field(default_factory=_default_device)
    amp: bool = False            # fp32 default
    amp_dtype: str = "float16"
    def __post_init__(self): ...  # CPU -> amp False; bf16+Pascal -> raise
    def autocast(self): ...       # device_type = self.device.split(":")[0]
```

src/personacore/preflight.py (current):
```python
def preflight_p100(require_p100: bool = True) -> dict:
    # returns {"device": str, "cc": (major, minor) | None, "torch": str}
    # require_p100=True: raise if no CUDA / not P100 / Pascal smoke op fails
    # require_p100=False (laptop/CI): print summary, never raise on CPU
```

scripts/preflight_demo.py (current call):
```python
from personacore.preflight import preflight_p100
info = preflight_p100(require_p100=False)
```

tests/conftest.py provides the `simulate_pascal` fixture (monkeypatches torch.cuda to report
an available device with capability (6, 0)).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add MPS detection + fp32/AMP-off posture to RuntimeConfig</name>
  <files>src/personacore/config.py, tests/test_config.py</files>
  <behavior>
    - Test: with CUDA available, _default_device() returns "cuda" (unchanged).
    - Test (monkeypatch torch.cuda.is_available -> False, torch.backends.mps.is_available -> True):
      _default_device() returns "mps".
    - Test (both unavailable): _default_device() returns "cpu" (unchanged).
    - Test: RuntimeConfig(device="mps") forces amp=False even when amp=True is passed.
    - Test: RuntimeConfig(device="mps", amp_dtype="float16", amp=True) still ends with amp=False
      (MPS gets no fp16 AMP — fp32 only, per D-02).
    - Existing tests stay green: fp32 default, AMP-off-on-CPU, bf16-raises-on-Pascal (guard
      UNCHANGED), fp16-ok-on-Pascal.
  </behavior>
  <action>
    Extend `_default_device()` to detect MPS as the middle priority: return "cuda" if
    `torch.cuda.is_available()`, else "mps" if `torch.backends.mps.is_available()`, else "cpu"
    (priority CUDA -> MPS -> CPU, per D-02). Guard the MPS attribute access so it is safe on
    torch builds lacking the `mps` backend (use `getattr(torch.backends, "mps", None)` or the
    standard `torch.backends.mps.is_available()` which exists on all supported wheels — prefer
    the direct call since torch>=2.7 always exposes it).
    In `RuntimeConfig.__post_init__`, extend the AMP-off branch so MPS mirrors the CPU posture:
    force `self.amp = False` when `self.device` is "cpu" OR "mps" (per D-02 — MPS forces fp32,
    AMP disabled; fp16 AMP stays CUDA-only). Do NOT touch the bf16-on-Pascal guard — it stays
    exactly as written. `autocast()` already splits on ":" so it remains correct for "mps".
    Add MPS tests to tests/test_config.py (monkeypatching `torch.cuda.is_available` and
    `torch.backends.mps.is_available` so they run CPU-only — never require real MPS hardware).
    Update the module docstring's "AMP auto-disabled on CPU" note to "on CPU and MPS".
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/test_config.py -x -q</automated>
  </verify>
  <done>_default_device resolves CUDA->MPS->CPU; RuntimeConfig(device="mps") yields amp=False; bf16-on-Pascal guard unchanged and still raising; new MPS tests pass CPU-only.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Hard-rename preflight_p100 -> preflight_device with CUDA-P100 -> MPS -> CPU priority</name>
  <files>src/personacore/preflight.py, tests/test_preflight.py</files>
  <behavior>
    - Test: no-CUDA + MPS available + strict -> returns {"device":"mps", ...} WITHOUT raising
      (MPS is a usable long-run device under D-01).
    - Test: no-CUDA + no-MPS + strict -> raises RuntimeError (no usable device for a long run).
    - Test: no-CUDA + no-MPS + non-strict -> returns {"device":"cpu", ...} without raising
      (preserves the old require_p100=False degrade-to-CPU-summary intent).
    - Test: CUDA T4 (cc 7.5) + strict -> raises RuntimeError mentioning P100 (unchanged P100 gate).
    - Test: CUDA P100 (cc 6.0) + non-strict -> returns a dict with device/cc/torch keys
      (unchanged; torch.ones monkeypatched to avoid a real CUDA alloc).
    - `preflight_p100` symbol no longer exists (hard rename, not an alias).
  </behavior>
  <action>
    Hard-rename `preflight_p100` to `preflight_device` (delete the old name — NO deprecated
    alias, per D-02). Replace the `require_p100: bool = True` parameter with `strict: bool = True`
    that preserves the OLD `require_p100` intent: strict=True is the long-run gate (refuse to
    start unless a usable accelerator is live); strict=False is the laptop/CI summary path that
    degrades to a CPU dict without raising. Keep the existing P100 detection + Pascal sm_60 smoke
    op fully reachable as the FIRST priority branch so a CUDA box still preflights correctly.
    Detection order (per D-02):
    1. If `torch.cuda.is_available()`: run the existing P100 logic verbatim — print summary,
       enforce the "P100" name check when strict, run the Pascal sm_60 CUDA smoke op (still
       raising the cu128+ kernel-drop RuntimeError on failure), return the CUDA dict.
    2. Elif `torch.backends.mps.is_available()`: print an MPS summary line and return
       {"device":"mps", "cc": None, "torch": torch.__version__}. MPS is a usable device under
       D-01, so do NOT raise here even when strict.
    3. Else (CPU): if strict, raise RuntimeError naming no usable accelerator (CUDA P100 or MPS)
       for a long run; if not strict, print the CPU summary and return the CPU dict (the old
       require_p100=False behavior).
    Update the module + function docstrings to describe device priority and the strict semantics.
    Rewrite tests/test_preflight.py: import `preflight_device`, keep the T4-reject and
    P100-non-strict-ok cases (renamed to use strict=), add the three MPS/CPU cases above
    (monkeypatch `torch.cuda.is_available` and `torch.backends.mps.is_available`; CPU-only).
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/test_preflight.py -x -q && ! grep -rq "preflight_p100" src scripts tests</automated>
  </verify>
  <done>preflight_device exists with CUDA-P100->MPS->CPU priority; strict preserves the require_p100 gate intent; MPS resolves without raising; preflight_p100 fully removed; tests pass CPU-only.</done>
</task>

<task type="auto">
  <name>Task 3: Update the thin preflight_demo caller + lint/test gate</name>
  <files>scripts/preflight_demo.py</files>
  <action>
    Update the import to `from personacore.preflight import preflight_device` and the call site
    from `preflight_p100(require_p100=False)` to `preflight_device(strict=False)` (the laptop
    summary path). Update the module docstring: replace the "require_p100=False ... preflight_p100()
    (require_p100=True) to assert the live P100" wording with the new device-priority framing —
    on the user's M3 this resolves to MPS; on Kaggle cell-1 call `preflight_device()` (strict=True)
    to assert a live P100 (or MPS) before a long run. No CLI/argparse; thin entry point only
    (Phase-1 D-04). Then run the full CPU-only suite and ruff to confirm nothing regressed.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest -q && .venv/bin/ruff check . && .venv/bin/ruff format --check .</automated>
  </verify>
  <done>preflight_demo.py imports/calls preflight_device(strict=False); full CPU-only suite green; ruff check + format clean.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| host hardware -> device layer | RuntimeConfig/preflight read live `torch` device availability; no untrusted external input crosses here. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-lgy-01 | Tampering | wrong/silently-broken device selected for a long run | mitigate | preflight_device strict gate refuses to start unless a usable accelerator (CUDA P100 or MPS) is live; Pascal sm_60 smoke op retained to catch cu128+ kernel-drop. |
| T-lgy-02 | Denial of Service | MPS op-coverage gaps cause silent NaN/CPU-fallback mid-run | accept | D-01a explicitly accepts MPS correctness risks; a cheap MPS sanity gate (overfit smoke / finite-loss) is Phase-5 scope, not this device-layer change. |
| T-lgy-SC | Tampering | npm/pip/cargo installs | n/a | No new dependencies installed; uses already-present `torch`. No package-legitimacy gate required. |
</threat_model>

<verification>
- `_default_device()` returns "cuda"/"mps"/"cpu" under the three monkeypatched availability combos.
- `RuntimeConfig(device="mps")` forces `amp=False`; bf16-on-Pascal guard unchanged and still raising.
- `preflight_device` honors CUDA-P100 -> MPS -> CPU priority; `strict` preserves the old gate intent.
- `grep -rq "preflight_p100" src scripts tests` finds nothing (hard rename complete).
- Full CPU-only `pytest` suite green with no MPS/CUDA hardware; `ruff check` + `ruff format --check` clean.
</verification>

<success_criteria>
- MPS is a resolvable device in RuntimeConfig (fp32, AMP off, mirroring CPU posture) — D-02 satisfied.
- preflight_p100 hard-renamed to preflight_device with the documented priority order; no alias left.
- All callers (scripts/preflight_demo.py) and tests updated; suite stays GPU/MPS-free and green.
- bf16-on-Pascal guard and fp16-AMP-CUDA-only behavior unchanged.
</success_criteria>

<output>
Create `.planning/quick/260605-lgy-add-mps-support-to-the-device-layer-runt/260605-lgy-SUMMARY.md` when done
</output>
