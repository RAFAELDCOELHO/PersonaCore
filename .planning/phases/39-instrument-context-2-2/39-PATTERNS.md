# Phase 39: Instrument × Context 2×2 (E6) - Pattern Map

**Mapped:** 2026-10-04
**Files analyzed:** 6 new (2 scripts, 2 tests, 1 record, 1 report) + gitignored sidecars
**Analogs found:** 6 / 6. The classifier, the context-(b) NLL loop and the anchor-draw record have no direct analog (see No Analog Found).
Every line reference below was re-read at HEAD `3499c3b`. No `scripts/phase39*`, `tests/test_phase39*` or `results/phase39*` exists yet.

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase39_prereg.py` | config (pre-registration, THE one fill file for both E6 slots) + pure rule functions | transform | `scripts/phase38_prereg.py` (sections 1-9, :1-954) | exact |
| `scripts/phase39_ctx.py` | CLI driver (MPS under the ledger; CPU crosscheck/emit/report) | batch + event-driven (ledger/heartbeat) | `scripts/phase38_rank.py` (whole file) + `scripts/phase36_probe.py` `stage_e6` :609-645 | exact (the anchor-draw stage is role-match) |
| `tests/test_phase39_prereg.py` | test | ancestry + AST census + pure unit on tracked JSON | `tests/test_phase38_prereg.py` | exact |
| `tests/test_phase39_ctx.py` | test | monkeypatched driver, tmp root/ledger/heartbeat | `tests/test_phase38_rank.py` | exact |
| `results/phase39_ctx.json` | record (write-once, MPS, named by the ledger end line) | — | `results/phase38_rank.json` via `phase38_rank.build_record`/`emit` | exact |
| `results/phase39_ctx_report.md` | report (rendered from the committed record) | transform | `phase38_rank.render_report`/`report` :1014-1253 | exact |
| `data/phase39_ctx_{run,gate,cpu,<reading>}.json`, `data/phase39_rehearsal.json` | gitignored sidecars | — | `phase38_rank.run_sidecar`/`gate_sidecar`/`nll_sidecar`/`cpu_sidecar` :132-157, `rehearsal_identity_path` :160 | exact |

No new register line is needed in `tests/test_lora_inject.py` (adapters only through `phase36_probe.adapted_model` / `phase14_recall.load_adapted_model`).

---

## IMPORT vs COPY (byte-pinned modules are never edited)

`phase38_prereg.py` / `phase38_rank.py` are pinned through `results/phase38_rank.json` `provenance.module_sha256`; `phase36_*`, `phase35_prereg`, `phase18_extraction` (RANK-03, `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte`), `phase19_*`, `phase14_recall` are pinned by committed records. **Import them; never edit them.**

| Symbol | Where (verified) | IMPORT or COPY | Why |
|---|---|---|---|
| `phase35_prereg.fill`, `a2_corpus_entries`, `V6_RESULT_PATHS`, `FULL_FIDELITY_K`, `ENTRY_FIELDS`, `KINDS`, `FORBIDDEN_PHRASE`, `MARGIN_K` | `scripts/phase35_prereg.py:1882`, `:507`, `:317-333` (`"results/phase39_*"` at :323), `:348` | IMPORT (plain `import phase35_prereg`, no alias, no `from ... import`) | slot census `tests/test_phase35_prereg.py:2166-2270` |
| `phase38_prereg.READINGS`, `PREFIXES`, `SLOTS`, `MARGIN`, `rank_in_prefix`, `first_event`, `first_collapse`, `first_damage`, `relation`, `drop_formula_audit`, `committed_gate_ranks`, `a2_counts`, `components_sha256`, `MINTING_RECORD`, `ADAPTER_OFF_RECORD`, `ADAPTER_ON_RECORD`, `ERASED_RECORD`, `RETRAIN_RECORD`, `RETRAIN_SCORES`, `KSTAR_SUMMARY`, `TARGET_SCORES`, `CURVE_RECORD`, `PROBE_E1_RECORD`, `BUDGET_RECORD` | `scripts/phase38_prereg.py:163`, `:159`, `:256`, `:236`, `:720`, `:747`, `:753`, `:758`, `:772`, `:797`, `:857`, `:902`, `:792`, `:124`, `:141-153` | IMPORT | frozen definitions; Phase 39 reuses them verbatim |
| `phase38_rank.gate_reading`, `reconstruction_checks`, `adapter_digests`, `m2_adapter_path`, `run_inputs` (partial) | `scripts/phase38_rank.py:395`, `:296`, `:286`, `:242`, `:252` | IMPORT `gate_reading`, `reconstruction_checks`, `m2_adapter_path` | public, torch-free at import (`test_the_driver_imports_without_torch`, `tests/test_phase38_rank.py:572-582`). **Rig note:** `reconstruction_checks` looks `adapter_digests` up on `phase38_rank`, so tests stub `phase38_rank.adapter_digests`, not a phase39 name |
| `phase38_rank.reading_model` | `:349-377` | **COPY** | yields `(model, tok)` and DROPS `forbid` (`_forbid` at :359/:365); the anchor draws need `forbid` |
| `phase38_rank.score_values` | `:380-392` | **COPY the shape, change the call** | returns the mean only (`value_span_nll_mean`); D-17/D-23 need `nll_sum` too |
| `phase38_rank` run/emit/report skeleton (`_prove`, `_sha256`, `_now`, `_json`, `module_sha256`, `_is_real`, sidecar paths, `outputs`, `record_rehearsal`, `rehearsal_disclosure`, `_device`, `preflight`, `_write_once`, `run`, `crosscheck`, `_hours`, `_cpu_block`, `build_record`, `emit`, `_table`, `_disclosure_lines`, `render_report`, `_tracked_and_clean`, `report`, `main`) | `:104-1274` | **COPY** (module-tagged `[phase39_ctx]`) | module-private or Phase-38-shaped (paths, FRONT, RUN_ID, record keys) |
| `phase36_budget._front_seconds` (E6 term) | `scripts/phase36_budget.py:566-574` | **COPY the term order** into the prereg, prove at import | private; floating point is order-sensitive (precedent `phase38_prereg.e5_projection_hours` :182-201) |
| `phase36_probe.adapted_model`, `e1_components`, `silenced` | `scripts/phase36_probe.py:590`, `:461`, `:280` | IMPORT | ISO-06; never `inject_lora` |
| `phase36_probe.stage_e6` | `:609-645` | **COPY the six-line body** (ids, guard, draw), keep completions + `stopped` | timing-only, k = 78 only, calls `phase25_run.device()`, discards completions |
| `phase18_extraction.span_nll_from_ids`, `value_span_nll`, `_frame_preamble`, `_guarded_span`, `reference_set_for`, `score_records`, `aggregate_questions`, `CORPUS_TIERS`, `ADMISSIBLE_NLL_FRAME`, `ADMISSIBLE_NLL_REDUCTION`, `DRAW_RECORD_KEYS` | `scripts/phase18_extraction.py:1050`, `:1110`, `:1031`, `:3014`, `:1159`, `:1919`, `:2223`, `:710`, `:985`, `:987`, `:1874` | IMPORT (lazy: torch at import) | instruments |
| `phase19_run._pooled_rows` | `scripts/phase19_run.py:620-647` | IMPORT (lazy) | gate 2, exactly as `phase38_prereg.a2_counts` :909-915 calls it |
| `phase19_erasure.FORBID_IDS_SHA256`, `value_span_nll_mean` | `scripts/phase19_erasure.py:1420`, `:2407` | IMPORT (lazy) | mask parity; gate-equal float |
| `phase14_recall.draw_all`, `assert_no_value_in_prompt`, `load_adapted_model`, `contains_value`, `SEED`, `SAMPLE_TEMPERATURE`, `SAMPLE_TOP_P`, `RECALL_MAX_NEW_TOKENS`, `CONVBASE_SLIM`, `ADAPTER_PATH`, `TOKENIZER_PATH` | `scripts/phase14_recall.py:846`, `:597`, `:712`, `:300`, `:147`, `:159`, `:160`, `:143`, `:81`, `:84`, `:83` | IMPORT (lazy) | never pass `temperature=`/`top_p=` (they are read inside `draw_all`) |
| `phase16_persistence.forbid_digest` | `scripts/phase16_persistence.py:180` | IMPORT | prove the mask before the first draw |
| `phase36_caps.check_unit_caps`, `committed_budget`, `counts_for` | `scripts/phase36_caps.py:165`, `:157`, `:182` | IMPORT | never pass `adapters=`/`anchor_adapters=` |
| `phase36_ledger.run_id`, `append`, `require_launch`, `read_ledger`, `open_runs`, `reconcile`, `HEARTBEAT_PATH` | `scripts/phase36_ledger.py:76`, `:194`, `:400`, `:106`, `:189`, `:238`, `:44` | IMPORT | D-03; no second stop rule |
| `phase25_run.atomic_write_json`, `beat`, `start_heartbeat` | `scripts/phase25_run.py:118`, `:298`, `:350` | IMPORT | the only `os.replace` writer |
| `erasure_gate.wilson_upper_bound`, `phase20_gate_coverage.wilson_lower_bound` | `scripts/erasure_gate.py:139`, `scripts/phase20_gate_coverage.py:124` | IMPORT | D-07 bounds, z by reference |
| `personacore.lora.adapter_disabled`, `personacore.dialogue.ASSISTANT_ID` | `src/personacore/lora/inject.py:157`, `src/personacore/dialogue/serialize.py:25` | IMPORT | adapter-off, anchor ids |

---

## Resolved paths and constants (derive, never type)

| Name | Resolves to | Source |
|---|---|---|
| `RECORD_GLOB` | `next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase39_*")` (equality, as `phase38_prereg.py:120-123`) | `phase35_prereg.py:323` |
| `CTX_RECORD`, `REPORT_RECORD` | `RECORD_GLOB.replace("*", "ctx.json")`, `.replace("*", "ctx_report.md")`; prove each `fnmatch`es `RECORD_GLOB` (`phase38_prereg.py:129-131`) | derived |
| `RUN_ID` | `phase36_ledger.run_id(39, "E6", "ctx")` → `"v6/39/E6/ctx"` | `phase36_ledger.py:76` |
| slot rules | `e6_entry_subset`: owner 39, `input_records = ("results/phase36_probe_*.json",)` (`phase35_prereg.py:1834-1838`), rule `:1674-1691` (tuple, non-empty, ints 0..215, strictly increasing, then `_consume_inputs`); `e6_decomposition_rule`: owner 39, `input_records = ()` (`:1867-1871`), rule `:1786-1788` (`_frozen_entry`, four fields) | `phase35_prereg.py` |
| owner glob | `scripts/phase39_*prereg.py` (`owner_prereg_glob`, `phase35_prereg.py:847-850`), so the driver name `phase39_ctx.py` must NOT end in `prereg.py` | |
| E6 caps | `unit_caps.E6 = {a2_regenerated_entries: 0, adapters: 7, anchor_adapters: 7, anchor_slots: 8, entries: 216, max_k: 48}`; `front_hours.E6 = 0.4949481154825642`; `cap_rulings` has one key `"E6.a2_regenerated_entries"` (measured) | `results/phase36_budget.json` |
| cap field names | `CAP_FIELDS["E6"] = ("adapters", "anchor_adapters", "anchor_slots", "entries", "max_k", "a2_regenerated_entries")`; `SLOT_COUNTS["e6_entry_subset"] = "E6"`; `counts_for("e6_entry_subset", v) -> {"entries": len(v)}` | `phase36_caps.py:52-60`, `:69`, `:196` |
| stop | `phase36_prereg.ENTRIES["front_stop_factor"]["value"] * front_hours.E6` (`phase38_prereg.py:204` shape) | |
| K | `phase35_prereg.FULL_FIDELITY_K` (48) | `:348` |
| margin | `phase38_prereg.MARGIN` (`= MARGIN_K x NONTARGET_NOISE_FLOOR`, proved equal to `e1_condition_b_margin()` at `:236-240`) | |
| A2 record draw keys (measured) | `arm, completions, dose, fact_id, family, prefix_text, realized_injection, seed_index, slot, source_family, stopped, tier`; adapter-on has 976 draws, 216 of them A2 | `results/phase18_arm_adapter-on.json` |
| per-NLL price | `unit_prices.e5_nll_high = 0.046742270700633526` s | budget (measured) |

---

## Pattern Assignments

### `scripts/phase39_prereg.py` (fill file, pure rules; frozen before any `results/phase39_*`)

**Analog:** `scripts/phase38_prereg.py`. Copy its section skeleton: (1) date + `RECORDS_AT_COMMIT`, (2) entry schema, (3) record paths, (4) readings + approval arithmetic, (5) margin by reference, (7) `_ENTRIES`, (8) fills, (9) pure definitions.

**Module docstring** (`phase38_prereg.py:1-22`): state which slots it fills, that leg (a) makes every commit to it precede every `results/phase39_*`, that later corrections are dated continuations (`scripts/_addendum.py`). **Do NOT copy the "Torch-free at import" sentence** (see the torch note below).

**Header, sys.path, plain imports** (`phase38_prereg.py:24-51`):
```python
import collections.abc
import fnmatch
import hashlib
import json
import math
import pathlib
import re
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase35_prereg  # noqa: E402  (needs the sys.path insert above)
import phase36_prereg  # noqa: E402  (same; torch-free)
import phase38_prereg  # noqa: E402  (same; torch-free; frozen: import only)
```
`phase38_prereg` already imports `phase14_factset`, `phase19_floor`, `phase36_budget` torch-free.

**Date + `_prove` + entry schema + `_read`** (`phase38_prereg.py:57-112`): copy verbatim with the tag `[phase39_prereg]`:
```python
# At this commit no `results/phase39_*` file existed, tracked or untracked.
COMMITTED = "2026-10-04"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase38_prereg] {message}")   # -> [phase39_prereg]

ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE
```
`_prove_entry` (`:77-107`) and `_read` (`:110-112`) copied whole.

**Record paths by equality** (`phase38_prereg.py:120-131`):
```python
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase38_*")
RANK_RECORD = RECORD_GLOB.replace("*", "rank.json")
REPORT_RECORD = RECORD_GLOB.replace("*", "rank_report.md")
...
for _path in RECORDS:
    _prove(fnmatch.fnmatch(_path, RECORD_GLOB), f"{_path} does not match {RECORD_GLOB}")
_prove(len(set(RECORDS)) == len(RECORDS), f"the record paths {RECORDS} are not distinct")
```
Phase 39: `"results/phase39_*"`, `"ctx.json"`, `"ctx_report.md"`. Input-path constants are imported from `phase38_prereg` (`:141-153`), never re-typed.

**A2 record pins (D-02, D-11 i, M1).** No analog constant. Parse the seven SHA-256 from the budget's Portuguese ruling string with the RESEARCH M1 regex `(k = \d+|M2): (results/[\w.-]+\.json) sha256 ([0-9a-f]{64})` (exactly 7 matches, `_prove` the count), and type the eighth (adapter-off `08fe96fbd9753f8b44a5eb67a69d1a2a0b062a666b5a2d5430c2a7476bb15535`) as the one typed pin, like `PHASE17_REPORT_SHA256` (`phase38_prereg.py:294`). Map reading → path from `phase38_prereg.READINGS` order.

**E6 arithmetic (D-11, D-26), copied in the committed term order** (`phase36_budget.py:566-574`, precedent `phase38_prereg.py:182-210`):
```python
# phase36_budget.py:566-574 (private _front_seconds), verbatim term order
        "E6": e6["adapters"]
        * (
            p["adapter_setup_high"]
            + e6["a2_regenerated_entries"] * p["a2_question_k48_high"] * e6["max_k"] / full_k
            + (e6["entries"] + e6["anchor_slots"])
            * p["e5_candidates_per_slot_max"]
            * p["e5_nll_high"]
        )
        + e6["anchor_adapters"] * e6["anchor_slots"] * e6["max_k"] * p["e6_anchor_draw_high"],
```
```python
# phase38_prereg.py:198-210, the proof shape to mirror
_prove(
    e5_projection_hours(COMMITTED_PREFIX_CAP) == _BUDGET["front_hours"]["E5"],
    "the E5 formula at the committed prefix cap does not reproduce front_hours.E5",
)
E5_PROJECTION_HOURS = e5_projection_hours(APPROVED_E5_PREFIXES)
E5_TOTAL_HOURS = math.fsum({**_BUDGET["front_hours"], "E5": E5_PROJECTION_HOURS}.values())
E5_STOP_HOURS = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _BUDGET["front_hours"]["E5"]
_prove(E5_PROJECTION_HOURS <= E5_STOP_HOURS, "... goes to Rafael BEFORE launch ...")
```
Phase 39: `e6_projection_hours(adapters, anchor_adapters, extra_nlls=0)`, prove `(7, 7, 0) == front_hours.E6`, approved projection = `(8, 8, 8 * 216 * 7)` (= 0.7227090186770592 h per D-26; computed, never typed), `<= E6_STOP_HOURS` (0.7424221732238463). `APPROVED_E6_ADAPTERS = 8` is the one typed approval value (as `APPROVED_E5_PREFIXES = 8`, `:167`); prove `COMMITTED_ADAPTER_CAP == len(PREFIXES) + 1` (M2 counted) so the deviation stays visible (`:170-179` shape).

**Verbatim ruling + approval block** (`phase38_prereg.py:212-229`):
```python
D21_RULING = "aprovo o teto de prefixos do E5 de 6 para 8 (D-09). approved"


def approval_block():
    """D-22: the approval, the projection and the stop, embedded in every Phase 38 record."""
    return {
        "ruling": D21_RULING,
        "source": "38-CONTEXT D-21/D-22/D-23 (255380f)",
        "approved_prefixes": APPROVED_E5_PREFIXES,
        "committed_prefix_cap": COMMITTED_PREFIX_CAP,
        "readings": list(READINGS),
        "e5_projection_hours": E5_PROJECTION_HOURS,
        ...
        "budget_record": BUDGET_RECORD,
    }
```
Phase 39: `D11_RULING = "Opção 1: aprovo (i) adaptador desligado como oitavo adaptador e (ii) os conjuntos cunhados da Fase 38 sob a pergunta inteira em |R| = 8 (D-09). approved"` (the two CONTEXT lines joined by ONE space, M15), source `"39-CONTEXT D-11/D-26 (62af2fe, 3499c3b)"`, plus the D-26 adapter-off-(ii) addition, the projection, the stop, and the not-measured list (D-12 |R| > 8, D-23d B1′). Return a fresh dict each call (`test_approval_block_is_fresh_on_every_call`).

**Entries** (`phase38_prereg.py:311-701`): `_CONTEXT = "39-CONTEXT D-{} (62af2fe)"` and `_PLAN_TIME = "39-CONTEXT D-{} (3499c3b)"` formatters (`:311-315`); a module-level `_ENTRIES = {...}` dict literal (the name is load-bearing: `tests/test_phase36_prereg.py:106` `_entries_node` finds it), `ENTRIES = types.MappingProxyType(...)` (`:665-667`), `_ENTRY_NAMES` frozenset + `_prove_entries()` (`:669-701`). Values that are mappings/tuples use `types.MappingProxyType`/tuples (`:319-457`). WR-01 vocabulary carried in the derivation text (`:476-553`, e.g. `"event_relation"` lists the outcome tuple). One entry per decision family: entry subset derivation (D-01), the decomposition rule (D-13..D-16, D-24, D-25), context (b) ids (D-23/D-23a-d), anchor generation (D-04..D-08, D-28), predicted rate (D-17/D-23c/D-29), gate exact ranks (D-18), gate 2 (D-19), cpu_crosscheck (D-20), the approval (D-11/D-26) and the three derived hour entries.

**The two fills** (`phase38_prereg.py:707-712` binding shape; RESEARCH Pattern 1):
```python
E5_MINTING_RULE = phase35_prereg.fill("e5_minting_rule", minting_rule=ENTRIES["e5_minting_rule"])
E5_RANK_MOVES_AND_GENERATION_COLLAPSES = phase35_prereg.fill(
    "e5_rank_moves_and_generation_collapses",
    moves=ENTRIES["rank_moved"],
    collapses=ENTRIES["generation_collapsed"],
)
```
Phase 39:
```python
_ENTRY_INDICES = tuple(range(len(phase35_prereg.a2_corpus_entries())))   # derived, not typed
E6_ENTRY_SUBSET = phase35_prereg.fill(
    "e6_entry_subset",
    entry_indices=_ENTRY_INDICES,
    input_records=(phase38_prereg.PROBE_E1_RECORD, "results/phase36_probe_e6.json"),
    derivation={"value": _ENTRY_INDICES, "derivation": "D-01 ...", "kind": "preference",
                "source": "39-CONTEXT D-01 (62af2fe); results/phase36_probe_e1.json; "
                          "results/phase36_probe_e6.json; results/phase36_budget.json"},
)
E6_DECOMPOSITION_RULE = phase35_prereg.fill(
    "e6_decomposition_rule", decomposition=ENTRIES["e6_decomposition_rule"]
)
```
`derivation["value"]` must be the SAME tuple (a list != tuple, `_consume_inputs` :910 refuses), `source` must name every consumed path. Each fill is the WHOLE value of its module-level UPPER binding; no other file may bind `E6_ENTRY_SUBSET`/`E6_DECOMPOSITION_RULE`.

**Torch at import (differs from Phase 38).** `_rule_e6_entry_subset` calls `a2_corpus_entries()` (`phase35_prereg.py:1682`), which imports `phase18_extraction` (torch). So this fill file is NOT torch-free (RESEARCH M12). Keep every OTHER heavy import lazy (inside functions, as `phase38_prereg.a2_counts` :909-910 does). It must still import on ubuntu CPU with no `checkpoints/`/`data/`: `tests/test_phase36_caps.py:272-283` `_owner_values` `exec_module`s it and reads `E6_ENTRY_SUBSET` → `{"entries": 216}` (`owner_overruns` at :286-293).

**Pure definitions to import from `phase38_prereg`, not re-write** (`:747-789`):
```python
def first_damage(counts, n_questions):
    return first_event(
        {k: k > 0 and counts[0] / n_questions - counts[k] / n_questions > MARGIN for k in PREFIXES}
    )


def relation(event_k, reference_k, *, reachable=True):
    if not reachable:
        _prove(event_k is None, f"an unreachable event fired at k = {event_k}")
        return "UNREACHABLE_AT_SIZE"
    if event_k == PREFIXES[0]:
        return "ALREADY_AT_K0"
    ...
```
`first_event` keys on `PREFIXES` only (`:747-750`): M2 and adapter_off never enter (D-16 precedent). The new per-cell lost/classify functions follow the same register: `_prove` inputs, JSON-serialisable outputs, WR-01 outcomes checked BEFORE the sufficiency classes, strict `>` against `MARGIN`.

**Gate 2 function (pure, lazy torch)** — the call shape is `phase38_prereg.a2_counts` (`:909-922`):
```python
    import phase18_extraction  # torch at import: lazy, so this module stays CPU-only
    import phase19_run  # same

    values = {fact.id: fact.value for fact in phase14_factset.LOCKED_FACTS}
    pooled = phase19_run._pooled_rows(
        _read(ADAPTER_ON_RECORD)["draws"], values, "A2", phase18_extraction.CORPUS_TIERS
    )
```
Phase 39 runs it over each of the 8 records (after its SHA check), and compares with `phase38_prereg.a2_counts()` (k0..k78), `results/phase19_retrain_scores.json` (M2) and 0 (adapter-off). Per-question G_q hits for the D-07 per-draw rate come from `phase18_extraction.score_records(draws, values)` keyed `(tier, seed_index)` (`:1919-1990`, A2 scored on `prefix_text + completion`).

---

### `scripts/phase39_ctx.py` (driver: preflight / run / crosscheck / emit / report)

**Analog:** `scripts/phase38_rank.py`.

**Docstring-as-usage** (`phase38_rank.py:1-42`): the five commands, what is measured, the gate, reconstruction, ledger discipline, rehearsal disclosure, "Torch-free at import". `main` raises `SystemExit(__doc__)` on bad argv, so the docstring is the usage text.

**Imports + constants** (`phase38_rank.py:44-101`):
```python
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — beat, start_heartbeat, atomic_write_json
import phase36_caps  # noqa: E402
import phase36_ledger  # noqa: E402
import phase36_probe  # noqa: E402  — adapted_model, e1_components, silenced (torch-free)
import phase38_prereg as prereg  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

# FIXED: the cwd of every git call, the base of the module digests and of every tracked input.
_REPO = pathlib.Path(__file__).resolve().parent.parent
# The default OUTPUT root (results/, data/) and the identity that selects the real-root branches.
_ROOT = _REPO
FRONT = "E5"
RUN_ID = phase36_ledger.run_id(38, FRONT, "rank")
LAUNCH_PATHSPEC = ("scripts", "src", "results")
```
Phase 39: `FRONT = "E6"`, `RUN_ID = phase36_ledger.run_id(39, FRONT, "ctx")`. **Import `phase39_prereg` lazily** (inside functions, as `phase38_rank.py:331`/`:424` do for `phase38_sizes_prereg`): it loads torch at import, and a top-level import breaks the driver's torch-free probe (`tests/test_phase38_rank.py:572-582`). Also import `phase38_prereg` and `phase38_rank` under their own names; alias only the phase-39 prereg if wanted (the census bans aliasing `phase35_prereg` only).
`MODULES` (`:74-86`): add `scripts/phase16_persistence.py`, `scripts/phase19_run.py`, `scripts/phase38_prereg.py`, `scripts/phase38_rank.py`, `scripts/phase39_prereg.py`, `scripts/phase39_ctx.py`. `DISCLOSED_MODULES` (`:90-92`) = `("scripts/phase39_ctx.py", "scripts/phase39_prereg.py")` (D-27: the prereg is not frozen by any earlier record). `RUN_PROVENANCE_KEYS` (`:93-101`) copied verbatim.

**Sidecars and outputs** (`phase38_rank.py:132-162`):
```python
def run_sidecar(root):
    return pathlib.Path(root) / "data" / "phase38_rank_run.json"
...
def nll_sidecar(root, reading):
    _prove(reading in prereg.READINGS, f"{reading!r} is not one of {prereg.READINGS}")
    return pathlib.Path(root) / "data" / f"phase38_rank_nll_{reading}.json"
...
def outputs(root):
    """The record path, then every sidecar path: all must be absent before a run."""
    return (
        pathlib.Path(root) / prereg.RANK_RECORD,
        run_sidecar(root), gate_sidecar(root), cpu_sidecar(root),
        *(nll_sidecar(root, reading) for reading in prereg.READINGS),
    )
```
Phase 39: `data/phase39_ctx_{run,gate,cpu}.json` + one `data/phase39_ctx_<reading>.json` per reading (anchor draws + context-(b) NLLs + (ii) NLLs, written before the next reading); `rehearsal_identity_path()` → `data/phase39_rehearsal.json`.

**Rehearsal identity, extended for D-27** (`phase38_rank.py:165-183`):
```python
def record_rehearsal(path, *, readings, slots, max_size):
    path = pathlib.Path(path)
    if path.exists():
        kept = _load(path)
        print(f"REHEARSAL KEPT {kept['git_sha']}", flush=True)
        return {"status": "kept", **kept}
    identity = {
        "git_sha": git_sha(),
        "module_sha256": {rel: _sha256(_REPO / rel) for rel in DISCLOSED_MODULES},
        "readings": list(readings),
        "slots": list(slots),
        "max_size": max_size,
        "started_utc": _now(),
    }
    phase25_run.atomic_write_json(path, identity)
```
D-27 adds a refusal Phase 38 did not have: the real-root preflight compares the identity's `scripts/phase39_prereg.py` digest with the current bytes and REFUSES on drift (Phase 38 only discloses, `rehearsal_disclosure` :186-239, and refuses at :440-444 only when the identity is missing). The slice keys change from `max_size` to the declared slice (e.g. readings + slots + entry subset).

**Preflight — every refusal before the ledger start line** (`phase38_rank.py:422-498`). Order to keep: I/O-free checks first (readings vs approval, device on the real root, identity present), outputs absent, no open attempt, `refuse_if_dirty`, `git_sha() != "unknown"`, tracked inputs, `module_sha256()`, `require_launch(FRONT, ledger_path=...)`, the committed-cap visibility check, `check_unit_caps`, gitignored inputs exist, `reconstruction_checks()`, then `PREFLIGHT OK ...` print and the returned dict.
```python
    gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
    committed_cap = phase36_caps.committed_budget()["unit_caps"][FRONT]["prefixes"]
    _prove(
        prereg.COMMITTED_PREFIX_CAP == committed_cap,
        f"the budget's committed E5 prefix cap is {committed_cap}, not "
        f"{prereg.COMMITTED_PREFIX_CAP}: the D-21 deviation must stay visible",
    )
    phase36_caps.check_unit_caps(
        FRONT, **phase36_caps.counts_for("e5_set_sizes", sizes_prereg.E5_SET_SIZES)
    )
```
Phase 39: `check_unit_caps("E6", entries=len(E6_ENTRY_SUBSET), a2_regenerated_entries=0, anchor_slots=8, max_k=48)` (never `adapters=`/`anchor_adapters=`); committed-cap check on `unit_caps.E6.adapters`. Phase-39-only refusals in the same block: the 8 A2 record SHA-256 checks and **gate 2** (`_pooled_rows` re-derivation equals the committed counts), both before the ledger start (D-19); `phase39_prereg.py` tracked; prereg drift since the rehearsal (D-27).

**Model per reading — COPY `reading_model`, keep `forbid`** (`phase38_rank.py:349-377`):
```python
@contextlib.contextmanager
def reading_model(reading, device):
    """``(model, tok)`` for one reading; the model is released on exit."""
    import torch

    _prove(reading in prereg.READINGS, f"{reading!r} is not one of {prereg.READINGS}")
    scope = contextlib.nullcontext()
    if reading == "M2":
        import phase14_recall

        model, _cfg, tok, _forbid, _artifact = phase14_recall.load_adapted_model(
            device, adapter_path=m2_adapter_path()
        )
    else:
        k = 0 if reading == "adapter_off" else int(reading[1:])
        _prove(k in prereg.PREFIXES, f"k = {k} is not one of {prereg.PREFIXES}")
        model, tok, _forbid = phase36_probe.adapted_model(device, k)
        if reading == "adapter_off":
            from personacore.lora import adapter_disabled

            scope = adapter_disabled(model)
    try:
        with scope:
            yield model, tok
    finally:
        model = None
        gc.collect()
        if torch.backends.mps.is_available():  # never reached on a CPU-only host (ubuntu CI)
            torch.mps.empty_cache()
```
Phase 39 yields `(model, tok, forbid)`. This function is decorated (`@contextmanager`), so it must NOT call `draw_all` itself (census below).

**Anchor generation (context a) — copy `stage_e6`'s body** (`phase36_probe.py:621-637`):
```python
    values = [f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS]
    with DrawTimer() as timer, silenced():
        for i, slot in enumerate(slots):
            state.update(stage="e6_anchor", shape=slot, draw_index=i)
            forms = phase14_factset.SLOT_FORMS[slot]
            ids = [ASSISTANT_ID] + list(
                tok.encode(phase18_extraction._frame_preamble(forms, frame))
            )
            # B2 / PERS-06: nothing draws unchecked, on the ids actually dispatched.
            phase14_recall.assert_no_value_in_prompt(tok, tok.decode(ids), values, prompt_ids=ids)
            # i * K: the disjoint seed windows draw_all's docstring leaves to the caller (D-06).
            phase14_recall.draw_all(model, tok, ids, device, forbid, i * K, n_samples=K - 1)
```
Keep the returned `(completions, stopped)` (D-08); drop `DrawTimer`; take `device` from preflight (not `phase25_run.device()`); before the first draw `_prove(phase16_persistence.forbid_digest(forbid) == phase19_erasure.FORBID_IDS_SHA256, ...)`. Store each (reading, slot) as a `DRAW_RECORD_KEYS`-shaped dict (`phase18_extraction.py:1874-1884`) with a non-`"A2"` family and `prefix_text=None`, so `score_records` scores the completion alone (`:1972-1990`). The ids are byte-equal to `value_span_nll`'s context (`phase18_extraction.py:1150-1153`):
```python
    forms = factset.SLOT_FORMS[slot]
    preamble = _frame_preamble(forms, frame)
    context_ids = [ASSISTANT_ID] + list(tok.encode(preamble))
    row = span_nll_from_ids(model, context_ids, list(tok.encode(value)), device)
    return {"slot": slot, "frame": frame, **row}
```
The A2 draw-loop precedent with the guard on `_guarded_span` (`phase19_erasure.py:2884-2896`):
```python
        base_ids = extraction._guarded_span(entry)
        recall.assert_no_value_in_prompt(
            tok, tok.decode(base_ids), list(values.values()), prompt_ids=base_ids
        )
        realized = entry["realized_injection"]
        completions, stopped = recall.draw_all(
            model, tok, entry["prompt_ids"], device, forbid, stride(entry), n_samples=budget - 1,
        )
```

**NLL scoring — COPY the `score_values` shape, call the instrument that returns both reductions** (`phase38_rank.py:380-392`):
```python
def score_values(model, tok, device, slot, values, state):
    """One pinned NLL per value, in order, never batched (the gate is exact)."""
    import phase19_erasure

    state.update(shape=slot)
    nlls = []
    with phase36_probe.silenced():
        for i, value in enumerate(values):
            state.update(draw_index=i)
            nlls.append(
                phase19_erasure.value_span_nll_mean(model, tok, device, slot=slot, value=value)
            )
    return nlls
```
Context (a): `phase18_extraction.value_span_nll(model, tok, device, slot=slot, value=v, frame=phase18_extraction.ADMISSIBLE_NLL_FRAME)` → `nll_mean` is the same float `value_span_nll_mean` returns (`phase19_erasure.py:2416-2419`: `float(row[f"nll_{extraction.ADMISSIBLE_NLL_REDUCTION}"])`), so `phase38_rank.gate_reading` equality holds, and `nll_sum` feeds D-17. Context (b): `phase18_extraction.span_nll_from_ids(model, phase18_extraction._guarded_span(entry), list(tok.encode(candidate)), device)` (`:1050-1107`, `:3014-3045`), one call per (question, candidate), never batched. D-23b taught suffix: `prompt_ids == _guarded_span(e) + encode(taught)[:realized_injection]` (measured), so one pinned call `span_nll_from_ids(model, entry["prompt_ids"], encode(taught)[realized_injection:], device)` gives the sum in A2's exact context; this is the only reading that uses the A2 prefix, the main reading stays B1. Rank: `phase38_prereg.rank_in_prefix(mean_by_candidate, taught, [c for c in R if c != taught])`.

**Gate 1 — reuse `phase38_rank.gate_reading`** (`phase38_rank.py:395-419`, run loop `:542-557`):
```python
        rows = {}
        for reading in readings:
            state.update(stage=f"gate_{reading}")
            with reading_model(reading, device) as (model, tok):
                nll_by_slot = {}
                for slot in plan:
                    references = phase18_extraction.reference_set_for(slot)
                    nlls = score_values(model, tok, device, slot, references, state)
                    nll_by_slot[slot] = dict(zip(references, nlls))
            rows[reading] = gate_reading(reading, nll_by_slot)
        passed = all(row["equal"] for by_slot in rows.values() for row in by_slot.values())
        _write_once(gate_sidecar(root), {"run_id": RUN_ID, "readings": list(readings), "rows": rows, "passed": passed})
```
`phase38_rank.gate_reading(reading, {slot: {candidate: nll_mean}})` already covers all 8 readings via `committed_gate_ranks()`. Phase 39 may load each model once per reading and run gate → anchor draws → (b) → (ii) inside one `with` block, provided the gate for ALL readings passes before any new scoring (D-18). If it scores gate-then-work per reading, the gate must still complete for every reading first: keep Phase 38's two-pass shape (gate pass over all readings, then the work pass) unless the plan argues otherwise.

**Run: ledger start, beat, heartbeat thread, write-once sidecars, ledger end** (`phase38_rank.py:507-618`):
```python
    pre = preflight(root=root, ledger_path=ledger_path, device=device, readings=readings)
    readings, device = pre["readings"], pre["device"]
    plan = scoring_plan(slots=slots, max_size=max_size)
    phase36_ledger.append("start", run_id=RUN_ID, phase=38, front=FRONT, ledger_path=ledger_path)
    heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
    state = {"point": RUN_ID, "stage": "gate", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)  # the thread's first beat waits a full period
    if rehearsal_identity is not None:  # D-34: before the first value is scored
        record_rehearsal(rehearsal_identity, readings=readings, slots=list(plan), max_size=max_size)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    started = _now()
    try:
        ...
                # Write-once BEFORE the next reading: a crash keeps every reading already scored.
                _write_once(nll_sidecar(root, reading), {"run_id": RUN_ID, "reading": reading, "slots": by_slot})
        ...
        _write_once(run_sidecar(root), {..., "gate_sha256": _sha256(gate_sidecar(root)),
                                        "nll_sha256": {r: _sha256(nll_sidecar(root, r)) for r in scored}})
        state.update(stage="done")
    finally:
        stop.set()
        thread.join()
    phase36_ledger.append("end", run_id=RUN_ID, phase=38, front=FRONT, record=prereg.RANK_RECORD, ledger_path=ledger_path)
```
The real-root shape guard (`:524-529`): partial shapes and a rehearsal identity only in a tmp root outside the repo (`_is_real`, `:126-129`). No in-run stop timer (D-03).

**Crosscheck, build_record, emit** (`phase38_rank.py:639-682`, `:725-868`, `:871-907`): `crosscheck` re-scores on CPU into a write-once `cpu_sidecar`, no ledger line; `_cpu_block` counts differing cells with `"criterion": False`; `build_record` verifies each sidecar's sha256 against the run sidecar (`:752-755`, `:795-798`), embeds `approval_block()`, the rehearsal disclosure on the real root (`:775-784`), and the provenance block:
```python
    launch, now = blob["module_sha256_at_launch"], module_sha256()
    record["provenance"] = {
        "run": {key: blob[key] for key in RUN_PROVENANCE_KEYS},
        "module_sha256_at_launch": launch,
        "module_sha256": now,
        "modules_changed_since_launch": sorted(rel for rel in MODULES if launch.get(rel) != now[rel]),
        "sidecar_sha256": sidecars,
        "head_at_write": git_sha(),
        "written_utc": _now(),
    }
```
`emit` refuses an existing record (`"REFUSING to overwrite it ... dated continuations"`, `:874-879`), refuses a non-full shape on the real root (`:883-891`), `refuse_if_dirty` with `:(exclude)` of the record (`:892-903`), then `atomic_write_json`. Phase 39's D-20 crosscheck covers NLL and rank only (generation is device-seeded; declared).

**Report** (`phase38_rank.py:910-1253`): `_LIMITATIONS` tuple (`:911-915`), `_table` with `|` escaping (`:924-930`), `_disclosure_lines` (`:970-1011`), `render_report(record)` pure from the record, `report()` refuses unless the record is tracked and clean on the real root (`_tracked_and_clean`, `:1227-1232`; `:1241-1244`), write-once via `out.write_text` (no atomic writer for markdown). Phase 39 sections: status, approval/cost (D-11 verbatim), gate 1, gate 2, per-cell R_a/R_q/G_a/G_q with k0 counts beside each relation, class counts WITH denominators for collapse and damage separately, D-07 unit + per-draw Wilson rates labelled draw-unit descriptive, D-17 predicted vs observed, (i) adapter-off and (ii) minted |R| = 8 as descriptive, CPU crosscheck, rehearsal disclosure, limitations (D-22, the B1 two-way difference, the seed overlap D-28, Wilson clustering), the not-measured list (D-12, D-23d), provenance.

**main** (`phase38_rank.py:1256-1274`):
```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "crosscheck": crosscheck, "emit": emit, "report": report}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    # git_sha() reads the process cwd: every command runs at the repository root.
    os.chdir(_REPO)
    commands[argv[0]]()
    return 0
```

---

### `tests/test_phase39_prereg.py`

**Analog:** `tests/test_phase38_prereg.py`.

**Imports + shared helpers** (`:19-64`):
```python
import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_prereg  # noqa: E402  (same)
import phase38_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import (  # noqa: E402
    _insert_at,
    _literal_failures,
    _slot_census_failures,
)
from test_phase36_prereg import (  # noqa: E402
    _HEAVY,
    _entries_node,
    _entry_string_failures,
    _first_inner,
    _skip_failures,
    _untested_functions,
)

PREREG = "scripts/phase38_prereg.py"   # -> scripts/phase39_prereg.py
```
Helper locations (verified): `_git` `tests/test_phase29_prereg.py:52`, `_assert_frozen_before` :69, `_planted` :526; `_slot_census_failures` `tests/test_phase35_prereg.py:2166`; `_HEAVY` `tests/test_phase36_prereg.py:372`, `_entries_node` :106, `_skip_failures` :396, `_untested_functions` :418.

**Arithmetic against the committed formula** (`:80-105`): re-state the formula inside the test from `results/phase36_budget.json`, assert `e6_projection_hours(7, 7) == front_hours.E6`, the approved projection equals the test's formula, and pin the `repr`s (`"0.7227090186770592"`, `"0.7424221732238463"`) as `:96-102` do.

**Approval block fresh on every call** (`:108-118`) and **D-11 verbatim from a fixed commit** (`:554-592`):
```python
_CONTEXT_PATH = ".planning/phases/38-exposure-rank-at-larger-minted-sets/38-CONTEXT.md"


def _d21_quote():
    text = _git("show", f"255380f:{_CONTEXT_PATH}")
    bullet = next(line for line in text.splitlines() if line.startswith("- **D-21:"))
    return bullet.split('Rafael: "', 1)[1].split('"', 1)[0]
```
Phase 39: read `git show 62af2fe:.planning/phases/39-instrument-context-2-2/39-CONTEXT.md`; the quote is wrapped over two lines (CONTEXT :59-60, two-space indent), so join the bullet's lines with ONE space before splitting on the quotes (M15, Pitfall 9). Assert `quote == D11_RULING`, `quote in ENTRIES[...]["derivation"]`, `len(quote.split()) > 5` meta-guard.

**Ancestry trio** (`:455-489`):
```python
def _strictly_before(x, y):
    run = subprocess.run(("git", "merge-base", "--is-ancestor", x, y), cwd=_ROOT, check=False)
    return x != y and run.returncode == 0


def _first_add(path):
    return _git("log", "--diff-filter=A", "--format=%H", "--", path).split()[-1]


def _phase38_records():
    return sorted(_git("ls-files", "results/phase38_*").split())


def test_phase38_prereg_is_frozen_before_every_phase38_record():
    _assert_frozen_before(PREREG, _phase38_records())
    # NON-VACUITY (natural RED): the v6.0 pre-registration was added before this one existed.
    with pytest.raises(subprocess.CalledProcessError):
        _assert_frozen_before(PREREG, ["scripts/phase35_prereg.py"])
```
plus `test_this_test_file_is_first_added_before_every_phase38_record` (FIRST add only, `:475-481`) and `test_records_at_commit_is_true_at_the_first_commit` (`:484-489`). Glob `results/phase39_*`; honest at zero records.

**Pure-definition tests**: WR-01 outcome tests (`:270-321`) are the template for the classifier truth table (all five classes, collapse and damage separately, `ALREADY_AT_K0` for each of R_q/G_a/G_q, `UNREACHABLE_AT_SIZE` for G_a k0 miss and R_q `n1(k0) < 9`, the k0 cells with no damage class, person_name k8 drop == `MARGIN` exactly not damaged as at `:362-364`). Committed-data reproduction tests (`:337-365` `_A2` table, `:410-439` gate ranks) are the template for gate 2 (RESEARCH M2 count table, 0 mismatches, a tampered draw → `SystemExit`) and the A2 SHA pins.

**No derived value typed** (`:600-626`): `_literal_failures(source, seeds, floats, set())` with `floats` = the projection, the stop, `front_hours.E6`, `MARGIN`; plant a typed copy and assert RED. Add 216 to `seeds` only if `_literal_failures` handles ints that way (it does for `seeds` at `:602-605`).

**Entries four fields, no proposer, planted phrase** (`:634-680`), **preferences labelled + `D-\d\d` in every derivation** (`:691-698`), **slot census over `scripts/phase39_*.py`** (`:757-761`), **zero skips** (`:764-768`), **every prereg function has a CPU test** (`:771-783`).

**Do NOT copy `test_the_prereg_imports_without_torch`** (`:746-754`): the E6 fill loads `phase18_extraction` (in `_HEAVY`). Replace it with a subprocess probe that imports `phase39_prereg` on CPU and asserts no `checkpoints/` path is opened, or that `E6_ENTRY_SUBSET == tuple(range(216))` and only the expected heavy modules load.

---

### `tests/test_phase39_ctx.py`

**Analog:** `tests/test_phase38_rank.py`.

**Imports** (`:22-62`): `import phase38_rank  # noqa: E402  (same; never aliased — _untested_functions counts by name)` applies to `phase39_ctx`; import `phase14_recall`, `phase18_extraction`, `phase19_erasure`, `phase36_ledger`, `phase36_probe`, `phase38_prereg`, `phase38_rank` by name for stubbing; `from test_phase29_prereg import _git, _planted`; `from test_phase36_prereg import _skip_failures, _untested_functions`.

**Real-tree guard (autouse)** (`:65-81`):
```python
def _real_sidecars():
    # _REPO, not phase38_rank._ROOT: some tests patch _ROOT to a rig root.
    return sorted((_REPO / "data").glob("phase38_rank_*"))


_REAL_IDENTITY = _REPO / "data" / "phase38_rehearsal.json"


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    sidecars = _real_sidecars()
    identity = _REAL_IDENTITY.exists()  # D-34: no test creates or deletes the real identity
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _real_sidecars() == sidecars
    assert _REAL_IDENTITY.exists() == identity
```

**Fake model + deterministic NLL table that reproduces every committed rank** (`:106-128`):
```python
class FakeModel:
    def __init__(self, reading):
        self.reading = reading


def _offset(reading, value):
    """A deterministic per-(reading, value) offset in (-0.5, 0.5), never exactly 0."""
    digest = hashlib.sha256(f"{reading}|{value}".encode()).hexdigest()
    return (int(digest[:8], 16) / 2**32 - 0.5) or 0.25


def _fake_table(gate_ranks, references):
    """Taught 1.0; the first (committed rank - 1) other references in string order 0.5, the rest
    2.0: rank_in_prefix then reproduces every committed rank exactly."""
```

**The rig** (`:131-185`) — tmp root, tmp ledger/heartbeat, gitignored inputs as tmp stand-ins, stubs:
```python
@pytest.fixture
def rig(tmp_path, monkeypatch, gate_ranks, references, committed_digests):
    """The run fixture: a tmp root, tmp ledger/heartbeat, the device work stubbed."""
    (tmp_path / "results").mkdir()
    (tmp_path / "data").mkdir()
    paths = {"ledger_path": tmp_path / "ledger.jsonl", "heartbeat_path": tmp_path / "hb.jsonl"}
    rig = types.SimpleNamespace(root=tmp_path, paths=paths, dirty=[], launches=[], models=[], log=[],
                                crash=None, table=_fake_table(gate_ranks, references), cpu_table={},
                                digests=dict(committed_digests))
    # The GITIGNORED run inputs (absent on ubuntu CI) are tmp stand-ins; tracked ones stay real.
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in ("CONVBASE_SLIM", "ADAPTER_PATH"):
        stand_in = inputs / name
        stand_in.write_bytes(b"stand-in")
        monkeypatch.setattr(phase14_recall, name, stand_in)
    m2 = inputs / "m2_adapter"
    m2.write_bytes(b"stand-in")
    monkeypatch.setattr(phase38_rank, "m2_adapter_path", lambda: m2)
    monkeypatch.setattr(phase38_rank, "_device", lambda: "mps")
    monkeypatch.setattr(phase38_rank, "refuse_if_dirty", lambda **kw: rig.dirty.append(kw))
    monkeypatch.setattr(phase38_rank, "adapter_digests", lambda: dict(rig.digests))

    def require_launch(front, **kw):
        rig.launches.append((front, kw))
        return {"front": front, "spent_seconds": {front: 0.0}, "total_seconds": 0.0, "lifted": ()}

    monkeypatch.setattr(phase36_ledger, "require_launch", require_launch)

    @contextlib.contextmanager
    def reading_model(reading, device):
        rig.models.append((reading, device))
        yield FakeModel(reading), "tok"

    monkeypatch.setattr(phase38_rank, "reading_model", reading_model)

    def nll(model, tok, device, *, slot, value):
        rig.log.append((model.reading, slot, value))
        ...
    monkeypatch.setattr(phase19_erasure, "value_span_nll_mean", nll)
    return rig
```
Phase 39 deltas: patch `phase39_ctx._device` / `refuse_if_dirty` / `reading_model` (yielding `(FakeModel, tok, forbid)`); because the driver imports `phase38_rank.reconstruction_checks`, stub **`phase38_rank.adapter_digests`** and **`phase38_rank.m2_adapter_path`** (where those names are looked up); stub `phase18_extraction.value_span_nll` and `phase18_extraction.span_nll_from_ids` (returning `{"n_scored", "nll_sum", "nll_mean"}` from the table) and `phase14_recall.draw_all` (recording `(prompt_ids, index, n_samples)` and returning K fake completions + stops) instead of `value_span_nll_mean`; the `tok` must support `encode`/`decode` for the anchor ids and for `_guarded_span` value encoding: use the real tracked tokenizer (`personacore.tokenizer.from_json(_REPO / "artifacts" / "tokenizer.json")`, `tests/test_phase38_prereg.py:793-797`). `check_unit_caps`/`committed_budget` read the TRACKED budget through `phase36_caps.tracked_files()` (`scripts/phase36_caps.py:81-85`, `:157-162`); leave them real while `_REPO` is the cwd, and stub `phase36_caps.tracked_files` only in tests that move the root (precedent `tests/test_phase36_ledger.py:676`, `tests/test_phase36_probe.py:634`; Pitfall 7).

**Refusal table** (`:437-531`): one plant function per refusal, parametrized, each asserting `match=r"^\[(phase39_ctx|phase36_ledger|phase38_rank)\] .*" + reason` and that neither the ledger nor the heartbeat exists afterwards. Add: each A2 SHA mismatch, a gate-2 count mismatch, prereg drift since the rehearsal (D-27), `adapters=` never reaching `check_unit_caps`. `test_the_refusals_cover_every_output` (`:534-535`) pins `len(outputs(...))`.

**Ledger behaviour**: open attempt refuses, closed one passes (`:538-549`); preflight with the REAL `require_launch` on an empty tmp ledger (`:422-434`); crash mid-scoring leaves an open start that `phase36_ledger.reconcile` closes, landed sidecars intact (`:731-753`); refusal inside `run` writes no ledger line (`:756-762`); HEAD moved mid-run named (`:722-728`).

**Run/gate/emit/report**: full-shape run with call-order assertions on `rig.log` (`:616-674`); gate mismatch → `GATE_FAILED`, nothing new scored (`:677-690`); real root refuses partial shapes (`:693-700`); rehearsal tests (`:1044-1197`); emit through the frozen prereg definitions, recomputed in the test (`:831-966`); report rendered from the record with GFM-table parsing helpers `_headings`, `_section`, `_gfm_cells`, `_assert_gfm_tables`, `_rows` (`:1236-1270`); the full fake chain (`:1453-1466`); `main` dispatch with `inspect.signature(real).bind` and cwd == `_REPO` (`:1469-1495`).

**AST censuses** (`:1502-1609`): `_rank03_failures` (`:1517-1544`) with `_OWN_DEFS`/`_NEVER_CALLED`/`_PINNED_CALLS`; Phase 39 adds `span_nll_from_ids` and `_guarded_span` to the pinned calls (owner `phase18_extraction`) and `draw_all` (owner `phase14_recall`), and requires non-vacuity (`seen == {...}`). `test_no_in_run_stop_rule_and_no_ruling_writes` (`:1582-1593`):
```python
    assert called == {"run_id", "read_ledger", "open_runs", "require_launch", "append"}
    assert not re.search(r"\bprefixes\s*=", ast.unparse(tree))  # check_unit_caps never gets it
```
Phase 39: narrow it to keywords of `check_unit_caps` calls (`adapters`, `anchor_adapters`), since a whole-file `\badapters\s*=` regex reddens on an innocent local name (38-07 precedent). Also `test_the_driver_imports_without_torch` (`:572-582`), `test_no_skips_in_this_file` (`:1596-1600`), `test_every_phase38_rank_function_has_a_cpu_test` (`:1603-1609`).

---

### `results/phase39_ctx.json` and `results/phase39_ctx_report.md`

**Analog:** `results/phase38_rank.json` through `phase38_rank.build_record`/`emit`; the report through `render_report`/`report`. Commit order (M13, `tests/test_phase36_ledger.py:722` `test_every_tracked_v6_mps_record_has_a_launch_line`): ledger first, then the record, each alone after Rafael's "approved"; the report after the record is tracked and clean.

---

## Shared Patterns

### Refusal
**Source:** `_prove` in every module (`phase38_prereg.py:62-65`, `phase38_rank.py:104-106`): `raise SystemExit(f"[<module>] {message}")`, never `assert`. Tests match `r"^\[phase39_<module>\]"`.

### Write-once, clean tree, atomic write
**Source:** `phase38_rank._write_once` :501-504, `emit` :871-907, `report` :1235-1253, `phase25_run.atomic_write_json` :118. `os.replace` is banned outside `phase25_run.py`/`phase25_record.py` (`tests/test_phase25_driver.py:341-365`; phase38 AST `tests/test_phase38_rank.py:1525-1531`).

### Instrument reuse, never re-implementation
Every NLL goes through `phase18_extraction.value_span_nll` / `span_nll_from_ids`; every rank through `phase38_prereg.rank_in_prefix`; every hit through `score_records` (one predicate, `contains_value`); every A2 count through `_pooled_rows`. No new predicate (D-06; `score_records` docstring :1935-1950).

### Ledger discipline
`require_launch("E6")` in preflight (writes nothing), start line only after every refusal, beat once then the thread, write-once sidecars before the next reading, the end line naming `results/phase39_ctx.json`, `emit` re-runnable on CPU (`phase38_rank.py:422-618`). No `phase36_ledger.rule` call.

### Approval outside the caps
`APPROVED_E6_ADAPTERS` + `approval_block()` in the prereg and in every record; the driver checks its reading count against the approval and calls `check_unit_caps` without the raised counts (`phase38_rank.py:428-433`, `:469-478`).

## Census / real-tree tests a new `scripts/phase39_*.py` or `tests/test_phase39_*.py` trips

| Guard | Location | What it requires |
|---|---|---|
| Slot census | `tests/test_phase35_prereg.py:2166-2270` | `E6_ENTRY_SUBSET` / `E6_DECOMPOSITION_RULE` bound once each as the whole module-level value, only in `scripts/phase39_*prereg.py`; plain `import phase35_prereg`; no `phase35_prereg._*`, no `_rule_*` (attribute or string), no `from phase35_prereg import fill`, no string constant `"phase35_prereg"`, no `getattr(phase35_prereg, ...)` |
| Slot ordering legs | `tests/test_phase35_prereg.py` `_fill_sites` :2463, `_slot_ordering_failures` :2475, tests :2550-2583 | every commit touching `scripts/phase39_prereg.py` strictly precedes the first add of every `results/phase39_*` (leg a) |
| Owner caps exec | `tests/test_phase36_caps.py:272-293` | the fill file `exec_module`s on ubuntu CPU; `entries = 216 <= 216` |
| MPS launch line | `tests/test_phase36_ledger.py:722` | the ledger end line names `results/phase39_ctx.json` before the record is tracked |
| **`draw_all` call sites** | `tests/test_phase14_scoring.py:728-770` (`_scanned_files` = `scripts/*.py` + `src/**/*.py`, :564-573) | **the def that calls `draw_all` must itself call `assert_no_value_in_prompt` (or `assert_value_in_prompt`), must not be decorated (so not inside the `@contextmanager` `reading_model`), and must not be named `_skip*`**; `stage_e6` :631-637 is the shape |
| Sampler overrides | `tests/test_phase19_erasure.py:2425-2470` (scans phase18 only today) | never pass `temperature=`/`top_p=` to `draw_all` (D-05 is "the A2 parameters", read inside the sampler) |
| `inject_lora` register | `tests/test_lora_inject.py:261`, `:478` | never call `inject_lora`; no new register line |
| `os.replace` | `tests/test_phase25_driver.py:341-365` | `atomic_write_json` only |
| `== 10` wall | `tests/test_phase21_sc5.py` (`:81-100` region) | no `== 10` / `!= 10` text in `tests/test_phase39_*`, comments included |
| RANK-03 bytes | `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte` | never edit `phase18_extraction.py` |
| Phase 38 pins | `results/phase38_rank.json` `provenance.module_sha256` | never edit `phase38_prereg.py` / `phase38_rank.py` |
| Clean-tree probes | `tests/test_phase25_driver.py` and siblings | commit new phase39 files before the full suite |

## No Analog Found

| File / piece | Role | Data Flow | Reason / what to use |
|---|---|---|---|
| Per-cell classifier (CONTEXT_SUFFICIENT / INSTRUMENT_SUFFICIENT / EITHER / INTERACTION_ONLY / NO_DISAGREEMENT, plus ALREADY_AT_K0 / UNREACHABLE_AT_SIZE) | pure rule function in the prereg | transform | No existing classifier. Build it on `phase38_prereg.first_collapse`/`first_damage`/`relation` vocabulary (`:747-789`): WR-01 outcomes first, strict `>` against `MARGIN`, the k0 cell has no damage class, `n1(k0) < 9` → R_q damage `UNREACHABLE_AT_SIZE` (D-25), G_a damage with a k0 miss → `UNREACHABLE_AT_SIZE`. Never fed M2/adapter-off/(ii) rows (D-11). |
| Context-(b) NLL loop | driver stage | batch | No function scores a value under the question (RESEARCH M7). ~10 lines over `span_nll_from_ids` + `_guarded_span` (Pattern above). |
| **Per-token NLL (D-23a)** | instrument output | transform | **Gap.** `span_nll_from_ids` (`phase18_extraction.py:1050-1107`) returns only `{n_scored, nll_sum, nll_mean}`; no function in `scripts/` or `src/` uses `reduction="none"` (grep, measured). Two options, neither in the code today: (1) one pinned call per value token, `span_nll_from_ids(model, ctx + v[:j], [v[j]], device)`: 7,938 value ids against 1,512 calls per adapter for context (b) alone (5.25×, measured), roughly +0.8 h at `e5_nll_high` = 0.0467 s across 8 adapters, which breaks the approved 0.7227 h projection and the 0.7424 h stop; (2) a new one-forward per-token function, which is new instrument code (RANK-03 posture) and needs a proof that its per-token sum equals `span_nll_from_ids`'s `nll_sum`. **The planner must take this to Rafael before the prereg freezes.** The D-23b suffix sum needs neither: one pinned call on `entry["prompt_ids"]` with the taught suffix ids. |
| Anchor-draw record per (reading, slot) | sidecar row | file-I/O | Nothing stores anchor draws today (`stage_e6` discards them). Use the `DRAW_RECORD_KEYS` shape (`phase18_extraction.py:1874-1884`) + `stopped`, non-A2 family, `prefix_text None`. Do not stamp a corpus tier: `aggregate_questions` proves `tier in CORPUS_TIERS` (`:2213`). Compute the anchor unit as `int(any(hits))`; prove it equals `aggregate_questions` in a test only (RESEARCH Pitfall 5). |
| Draw-unit Wilson rates (D-07) | report field | transform | `wilson_upper_bound` docstring says n counts QUESTIONS (`erasure_gate.py:139-148`); label h/48 and total/1296 as draw-unit, within-question clustering ignored, descriptive; the two one-sided 95% bounds together form a 90% two-sided interval. |

## Metadata

**Analog search scope:** `scripts/phase38_prereg.py`, `scripts/phase38_rank.py` (whole), `scripts/phase36_probe.py` :575-650, `scripts/phase36_caps.py` :48-200, `scripts/phase36_budget.py` :536-575, `scripts/phase35_prereg.py` :315-335, :505-517, :847-850, :1670-1700, :1784-1925, `scripts/phase18_extraction.py` :1025-1160, :1870-1995, :2200-2260, :3010-3050, `scripts/phase19_run.py` :618-647, `scripts/phase19_erasure.py` :1420, :2407-2421, :2641-2650, :2800-2896, `scripts/phase14_recall.py` :81-160, :225-232, :846-930, `scripts/phase16_persistence.py` :180, `scripts/erasure_gate.py` :136-150, `scripts/phase20_gate_coverage.py` :124-135, `tests/test_phase38_prereg.py` (whole), `tests/test_phase38_rank.py` (whole), `tests/test_phase35_prereg.py` :2166-2270, `tests/test_phase36_caps.py` :260-300, `tests/test_phase14_scoring.py` :564-573, :690-770, `tests/test_phase19_erasure.py` :2425-2470, `tests/test_phase36_prereg.py` :365-395, committed JSON shapes (`results/phase18_arm_adapter-on.json`, `results/phase36_budget.json`).
**Files scanned:** about 25.
**Pattern extraction date:** 2026-10-04
