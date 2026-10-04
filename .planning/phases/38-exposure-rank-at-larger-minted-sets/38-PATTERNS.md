# Phase 38: Exposure Rank at Larger Minted Sets - Pattern Map

**Mapped:** 2026-10-04
**Files analyzed:** 13 (4 scripts, 1 optional plist, 4 tests, 4 records/sidecars)
**Analogs found:** 12 / 13. Every line reference below was re-read on HEAD `1a2ce83`. No `scripts/phase38*`, `tests/test_phase38*` or `results/phase38*` exists yet.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/phase38_prereg.py` | config (pre-registration, fill file 1) + pure rule functions | transform | `scripts/phase37_prereg.py` (whole file, 569 lines) | exact |
| `scripts/phase38_mint.py` | CLI driver (CPU) | batch transform -> write-once record | `scripts/phase37_r1a.py` (`write_record` :144-193, `main` :212-242) | exact |
| `scripts/phase38_sizes_prereg.py` | config (fill file 2, consumes the minting record) | transform (record -> frozen sizes) | `scripts/phase36_budget_prereg.py` :72-82 (a fill with `input_records=` + `derivation=`) | exact |
| `scripts/phase38_rank.py` (`preflight`/`run`/`crosscheck`/`emit`/`report`) | CLI driver (MPS, ledger) | batch + event-driven (ledger/heartbeat) | `scripts/phase37_r1b.py` (whole file) + `scripts/phase36_probe.py` `stage_e5` :692-808, `adapted_model` :590-606 | exact |
| `artifacts/com.personacore.phase38.rank.plist` (optional, RESEARCH says a terminal `caffeinate -i` launch suffices for ~5-10 min) | config (LaunchAgent) | — | `artifacts/com.personacore.phase37.r1b.plist` | exact |
| `tests/test_phase38_prereg.py` | test | ancestry + AST + unit | `tests/test_phase37_prereg.py` | exact |
| `tests/test_phase38_mint.py` | test | committed-input fixtures + write-once | `tests/test_phase37_r1a.py` + `tests/test_phase17_personas.py` :95-103, :314ff | exact |
| `tests/test_phase38_sizes_prereg.py` | test | ancestry + caps | `tests/test_phase36_budget.py` :871-930 (tmp `_REPO_ROOT` fill chain), :1214-1226 (ancestry) | exact |
| `tests/test_phase38_rank.py` | test | monkeypatched driver, tmp ledger, plist | `tests/test_phase37_r1b.py` | exact |
| `results/phase38_minting.json` | record (write-once, CPU) | — | `results/phase37_r1a.json` (via `phase37_r1a.write_record`) | role-match |
| `results/phase38_rank.json` | record (write-once, MPS, ledger end line names it) | — | `results/phase37_r1b.json` (via `phase37_r1b.build_record`/`emit`) | exact |
| `results/phase38_rank_report.md` | report (rendered from the committed record) | transform | no write-once markdown emitter in v6.0 (see No Analog) | partial |
| `data/phase38_rank_run.json` (+ NLL sidecar) | gitignored sidecar | — | `phase37_r1b.run_sidecar` :106-108, `sweep_record` :111-115 | exact |

**Register lines in existing census tests: none needed.** `tests/test_lora_inject.py:261` `INJECT_LORA_CONSUMERS` only lists `inject_lora` call sites; Phase 38 reaches adapters through `phase14_recall.load_adapted_model` / `phase36_probe.adapted_model` (already registered at `:263`), so no new line. Adding one would red the hard-equality assert at `:478`.

---

## Resolved paths and constants (from the module source, never typed)

| Name | Resolves to | Source |
|---|---|---|
| minting glob | `"results/phase38_minting*.json"` | `phase35_prereg.V6_RESULT_PATHS` :321 |
| phase-38 glob | `"results/phase38_*"` | `phase35_prereg.V6_RESULT_PATHS` :322 |
| `MINTING_RECORD` | `next(p for p in V6_RESULT_PATHS if p.startswith("results/phase38_minting")).replace("*", "")` -> `results/phase38_minting.json` (exactly ONE match: `e4_parameters` consumes every match, `phase35_prereg.py:1823-1827`) | derived |
| `RANK_RECORD`, `REPORT` | `RECORD_GLOB.replace("*", "rank.json")`, `.replace("*", "rank_report.md")`, where `RECORD_GLOB = next(p for p in V6_RESULT_PATHS if p == "results/phase38_*")` — **do not use `startswith("results/phase38_")`**: it returns the minting glob first (the tuple order is :321 then :322) | `phase37_prereg.py:107-115` pattern |
| fill function | `phase35_prereg.fill(slot, **inputs)` | `phase35_prereg.py:1882` |
| slot rules | `_rule_e5_minting_rule(*, minting_rule)` :1646; `_rule_e5_set_sizes(*, set_sizes, input_records, derivation)` :1655; `_rule_e5_rank_moves_and_generation_collapses(*, moves, collapses)` :1779 | `phase35_prereg.py` |
| size cap | `phase35_prereg.ENTRIES["e5_max_set_size"]["value"]` = 512 | `:688-693` |
| seed | `phase35_prereg.seed_list()[0]` = 1337 (imports `phase23_run` -> torch: call LAZILY) | `:357-368` |
| margin | `phase35_prereg.MARGIN_K` (= `erasure_gate.MARGIN_K`) x `phase19_floor.NONTARGET_NOISE_FLOOR` | `:350` |
| ledger | `phase36_ledger.run_id(38, "E5", <unit>)` -> `"v6/38/E5/<unit>"`; `append` :194; `require_launch(front, *, tracked=None, ledger_path=None)` :400; `HEARTBEAT_PATH = data/v6_mps_heartbeat.jsonl` :44; `EVENTS` :46 | `scripts/phase36_ledger.py` |
| caps | `check_unit_caps(front, *, tracked=None, **counts)` :165; `counts_for("e5_set_sizes", value)` -> `{"sets": len(value), "max_set_size": max(value.values())}` :182-195 | `scripts/phase36_caps.py` |
| budget E5 | `results/phase36_budget.json`: `unit_caps.E5 = {max_set_size: 512, prefixes: 6, sets: 8}`; `front_hours.E5 = 0.3612376740339419`; `total_hours = 77.72433149898184`; `unit_prices`: `e5_clearance_setup`, `e5_slot_clearance_high`, `e5_match_high`, `adapter_setup_high`, `e5_nll_high` (all seconds); `formula.E5` = `e5_clearance_setup + sets x e5_slot_clearance_high + sets x max_set_size x e5_match_high + prefixes x (adapter_setup_high + sets x max_set_size x e5_nll_high)` | measured |
| stop factor | `phase36_prereg.ENTRIES["front_stop_factor"]["value"]` | used at `phase37_prereg.py:176-179` |
| NLL | `phase19_erasure.value_span_nll_mean(model, tok, device, *, slot, value)` :2407 | pin |
| gate oracle (CPU tests only) | `phase19_erasure._rank_of(model, tok, device, *, slot, value, references)` :2422; `phase18_extraction.exposure_rank(nll_by_candidate, *, taught_value, reduction, length_spread)` :1230 (guard `6 <= len <= 8` :1262) | pin / RANK-03 |
| reference sets | `phase18_extraction.reference_set_for(slot)` :1159 (taught appended :1203, guard :1211); `CORE_SLOTS` :1467; `ADMISSIBLE_NLL_FRAME = "ans1"` :985; `ADMISSIBLE_NLL_REDUCTION = "mean"` :987 | RANK-03, import only |
| prefix-k model | `phase36_probe.adapted_model(device, k)` :590-606 (returns `(model, tok, forbid)`; calls `prove_published_adapter()`); `phase36_probe.e1_components()` :461-472 | torch-free at import (measured) |
| M2 adapter | `teach_persona.arm_outputs(phase19_erasure.RETRAIN_ARM, prefix=phase19_erasure.RETRAIN_PREFIX)["adapter"]` (`RETRAIN_ARM = "erase_reference"` :2996, `RETRAIN_PREFIX = "phase19"` :2997, `arm_outputs` `teach_persona.py:357`) | |
| adapter-off | `with personacore.lora.adapter_disabled(model):` (`src/personacore/lora/inject.py:157`; precedent `phase18_extraction.py:3599`) | |
| base loaders | `phase14_recall.load_adapted_model(device, adapter_path=None)` :712; `ADAPTER_PATH` :84, `CONVBASE_SLIM` :81, `TOKENIZER_PATH` :83 | |
| tokenizer | `personacore.tokenizer.from_json(path)` (`src/personacore/tokenizer/io.py:56`, torch-free) | |
| clearance / filters | `phase14_factset.exact_match_clean` :334-342, `normalize_for_match` :323, `token_census` :313, `all_pools` :127, `BASE_PRIOR_SEEDS` :299, `LOCKED_FACTS` :390; `phase17_personas.filter_token_budget` :360, `filter_roundtrip` :378, `filter_substring_disjoint` :407, `filter_absent_from_questions` :439, `MAX_VALUE_TOKENS` :225, `CORE_SLOTS` :67, `QUESTIONS_PER_SLOT` :83; `phase17_persona_facts.PERSONA_FACTS` :84, `FORBIDDEN_VALUES` :139; `phase21_filler.FILLER_FACTS` :175; `phase17_isolation.held_out_by_slot()` :124 | `phase14_factset`, `phase17_persona_facts`, `phase21_filler`, `personacore.tokenizer` import torch-free (measured); `phase17_personas`/`phase17_isolation` import torch (lazy) |
| k=0 A2 counts | `phase19_run._pooled_rows(draws, values, family, tiers)` :620 on `results/phase18_arm_adapter-on.json` | |
| ordered_prefix digest | `hashlib.sha256(json.dumps([list(c) for c in components]).encode("utf-8")).hexdigest()` == `results/phase36_probe_e1.json` `configuration.components_sha256` (`a7cc22715d64…`) | formula at `phase36_probe.py:565-567` |
| writers | `phase25_run.atomic_write_json(path, blob)` :118, `beat` :298, `start_heartbeat` :350; `personacore.provenance.git_sha`, `refuse_if_dirty(*, who, detail, pathspec=(), cwd=None)` | |

---

## Pattern Assignments

### `scripts/phase38_prereg.py` (fill file 1, torch-free, frozen at the minting record)

**Analog:** `scripts/phase37_prereg.py` — copy its section skeleton (1) date, (2) entry schema, (3) record paths, (4)-(5) record arithmetic, (6) `_ENTRIES`, (7) the fill, (8) pure rules.

**Header + sys.path + plain imports** (`phase37_prereg.py:19-47`):
```python
import collections.abc
import fnmatch
import json
import math
import pathlib
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase19_floor  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase35_prereg  # noqa: E402  (same; torch-free)
import phase36_prereg  # noqa: E402  (same; torch-free)

# At this commit no `results/phase37_*` file existed, tracked or untracked.
COMMITTED = "2026-10-03"
RECORDS_AT_COMMIT = 0
```
Phase 38 may also import at module level, torch-free (measured): `phase14_factset`, `phase17_persona_facts`, `phase21_filler`. **Never at module level:** `phase17_personas`, `phase17_isolation`, `phase18_extraction`, `phase19_erasure`, `phase14_recall`, and `phase35_prereg.seed_list()` (Pitfall 2; `_HEAVY` probe below). Pure functions take `tok`, `completions_by_slot`, `questions` as arguments.

**`_prove` + `_prove_entry` + `_read`** (`phase37_prereg.py:50-100`): copy verbatim with the tag `[phase38_prereg]`. Bind `ENTRY_FIELDS`, `KINDS`, `FORBIDDEN_PHRASE` from `phase35_prereg` (`:60-62`); a test asserts identity (`test_phase37_prereg.py:417-418`). Never call `phase35_prereg._anything` (census bans every `_`-prefixed attribute, `tests/test_phase35_prereg.py` `_slot_census_failures` :2166).

**Record paths** (`phase37_prereg.py:107-115`):
```python
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase37_"))
R1A_RECORD = RECORD_GLOB.replace("*", "r1a.json")
...
for _path in RECORDS:
    _prove(fnmatch.fnmatch(_path, RECORD_GLOB), f"{_path} does not match {RECORD_GLOB}")
```
For Phase 38 select by equality (see the resolved-paths table): `MINTING_GLOB` (:321) and `RECORD_GLOB` (:322) are two distinct members.

**Budget arithmetic read from records, never typed** (`phase37_prereg.py:168-184`):
```python
R1B_COST_CAP_HOURS = (
    phase36_prereg.ENTRIES["front_stop_factor"]["value"]
    * _read(BUDGET_RECORD)["front_hours"]["R1b"]
)
_prove(R1B_COST_HOURS <= R1B_COST_CAP_HOURS, "... D-06: this sum goes to Rafael BEFORE launch ...")
```
For D-21/D-22/D-23: `BUDGET_RECORD = next(p for p in V6_RESULT_PATHS if p.startswith("results/phase36_budget"))` (`:120-122`); compute `e5_projection_hours(prefixes)` from `_read(BUDGET_RECORD)["unit_prices"]` + `unit_caps.E5` per `formula.E5`; prove `e5_projection_hours(6) == front_hours.E5` (the formula reproduces the committed value, RESEARCH measured equality); `E5_STOP_HOURS = front_stop_factor x front_hours.E5` (0.5418565110509128); prove `e5_projection_hours(APPROVED_E5_PREFIXES) <= E5_STOP_HOURS`; prove the budget's `unit_caps.E5.prefixes == 6` so the deviation is visible.

**Entries** (`phase37_prereg.py:190-420`): `_ENTRIES = {...}` at module level (the name is load-bearing: `tests/test_phase36_prereg.py:106` `_entries_node` finds it by name), `ENTRIES = types.MappingProxyType(...)` (:386-388), `_ENTRY_NAMES` frozenset + `_prove_entries()` (:390-420). Source strings via a `_CONTEXT = "38-CONTEXT D-{} (<commit>)"` formatter (`:190-192`). The D-21 approval quotes Rafael verbatim in `derivation`, like `one_attempt` at `:270-292` ("These are Rafael's rulings, quoted, not a reading of them"); test it with `_ruling(commit, decision)` (`test_phase37_prereg.py:473-498`), adapted to 38-CONTEXT's `<decisions>` bullets. Expected entries: `e5_minting_rule` (preference), `rank_moved` (preference, D-12/D-28), `generation_collapsed` (D-13), `generation_damaged` (D-14), `left_top_eighth` (D-29), `e5_prefix_cap_approval` (`value = 8`, preference, D-21), `e5_projection_hours` (derived), plus whatever the planner splits out (D-24 report sha256, D-25 slack 2048, D-26 uniqueness, D-27 neighbour screen, D-31 |R| counts taught).

**The fills — census-conformant** (`phase37_prereg.py:426-435`):
```python
R1B_TOLERANCE_AND_REPLICATED = phase35_prereg.fill(
    "r1b_tolerance_and_replicated",
    tolerance={key: ENTRIES[f"tolerance_{key}"]["value"] for key in phase35_prereg.R1A_ASSERTIONS},
    replicated_definition=ENTRIES["replicated_definition"],
)
```
Phase 38 (both slots have `"input_records": ()`, `phase35_prereg.py:1828`, :1862-1866; sharing one file is the green planted repo `g38`, `tests/test_phase35_prereg.py:2603-2614`):
```python
E5_MINTING_RULE = phase35_prereg.fill("e5_minting_rule", minting_rule=ENTRIES["e5_minting_rule"])
E5_RANK_MOVES_AND_GENERATION_COLLAPSES = phase35_prereg.fill(
    "e5_rank_moves_and_generation_collapses",
    moves=ENTRIES["rank_moved"],
    collapses=ENTRIES["generation_collapsed"],
)
```
`_frozen_entry` requires exactly the four fields; `value` may be a mapping/tuple. A mutable `dict`/`list` inside `value` is deep-frozen by the rule; use `types.MappingProxyType` / tuples in `_ENTRIES` as `r1b_scope` does (`:328-346`).

**Pure rule functions** (`phase37_prereg.py:442-569` style: `_prove` on inputs, JSON-serialisable outputs, `"criterion": False` on description-only blocks like `draw_identity` :516-548 and `nontarget_context` :551-569). Functions RESEARCH names (`38-RESEARCH.md:541-549`): `mint_names`, `numeric_candidates`, `seeded_shuffle`, `rank_in_prefix`, `exposure_bits`, `moved`, `first_collapse`, `first_damage`, `relation`. Exact sort key to mirror (`phase18_extraction.py:1269-1272`):
```python
ordered = tuple(sorted(nll_by_candidate, key=lambda value: (nll_by_candidate[value], value)))
rank = 1 + ordered.index(taught_value)
ceiling = math.log2(len(ordered))
... "exposure_bits": ceiling - math.log2(rank),
```
`rank_in_prefix` must key on `(nll[c], c) < (nll[taught], taught)` with the real strings (RESEARCH :640-647) and keep `log2(size) - log2(rank)` in that order.

**Seeded local RNG precedent** (`scripts/phase16_persistence.py:901`): `rng = random.Random(seed)  # LOCAL generator — the global RNG streams are never touched.` Phase 38 must draw only through `rng.random()` (Pitfall 6) — `phase16_persistence` uses `rng.randrange`, so copy the LOCAL-generator discipline, not the call. Fisher-Yates is hand-written (no in-repo analog; ~4 lines).

**D-27 edit-distance screen** — copy the two-row Levenshtein from `tests/test_phase17_personas.py:95-103` into the prereg (it is test-local today, "Local because D-05 is the only caller in the repo"; do NOT import a test module from a script):
```python
def _levenshtein(left, right):
    """Edit distance, iterative two-row. Local because D-05 is the only caller in the repo."""
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]
```
Witness for its test: `_levenshtein("zorr", "zorp") == 1` (RESEARCH Pitfall 7) and `("tarrowgate", "marrowgate") == 1` (`test_phase17_personas.py:46`). Phase 17's screen record wording: `scripts/phase17_persona_gate.py:95-125` `MINTING_SCREEN_RECORD` (the "not one of the four" row) — cite it in the D-27 entry's `source`.

---

### `scripts/phase38_mint.py` (CPU driver -> `results/phase38_minting.json`)

**Analog:** `scripts/phase37_r1a.py` (246 lines).

**Imports** (`phase37_r1a.py:22-47`):
```python
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, the one os.replace writer
import phase35_prereg  # noqa: E402
import phase37_prereg as prereg  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402
_ROOT = pathlib.Path(__file__).resolve().parent.parent
```
Aliasing `phase38_prereg as prereg` is allowed (the census bans aliasing `phase35_prereg` only). Input SHA list from owners' constants (`:50-61`): `results/phase17_personas_report.md` (`phase17_persona_gate.REPORT_PATH` :87; D-24 pins its sha256), `artifacts/tokenizer.json` (`phase14_recall.TOKENIZER_PATH`).

**Write-once + tracked prereg + clean tree** (`phase37_r1a.py:144-193`):
```python
def write_record(derived, path, *, base, run):
    path = pathlib.Path(path)
    rel = path.relative_to(base).as_posix()
    _prove(fnmatch.fnmatch(rel, prereg.RECORD_GLOB), f"{rel} does not match RECORD_GLOB ...")
    _prove(not path.exists(), f"{path} exists — REFUSING to overwrite it. ... dated continuations")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "scripts/phase37_prereg.py"], cwd=_ROOT, capture_output=True,
    )
    _prove(tracked.returncode == 0, "the pre-registration scripts/phase37_prereg.py is not tracked: ...")
    pathspec = ("scripts", "src", "results")
    if path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){path.relative_to(_ROOT).as_posix()}",)
    refuse_if_dirty(who="phase37_r1a", detail=(...), pathspec=pathspec, cwd=_ROOT)
    record = {
        **derived,
        "input_sha256": {r: _sha256(_ROOT / r) for r in INPUT_RECORDS},
        "provenance": {
            "run": {key: run[key] for key in ("git_sha", "device", "torch_version", "started_utc", "finished_utc")},
            "module_sha256": {r: _sha256(_ROOT / r) for r in MODULES},
            "head_at_write": git_sha(),
            "written_utc": _now(),
        },
    }
    phase25_run.atomic_write_json(path, record)
```
For Phase 38 the glob check uses `MINTING_GLOB`, the tracked check names `scripts/phase38_prereg.py`, and `device = "cpu"` (so `test_every_tracked_v6_mps_record_has_a_launch_line`, `tests/test_phase36_ledger.py:722-733`, needs no ledger line). The record also carries: the D-22 approval + projection (every Phase 38 record), the completion source + device (MPS, base `04e724c`; Pitfall 9), per-slot rejection counts by filter including zeros (D-24, D-27), and the Phase 17 four-filter proof on the scored prefix.

**`main` with `out_root` + chdir** (`phase37_r1a.py:212-242`): copy, keeping `os.chdir(_ROOT)` (WR-05: `git_sha()` reads cwd) and the `import torch` only for `torch_version`.

**Clearance (D-04/D-24, committed completions, no generation).** The live-generation template (only if Q1 ever changes) is `phase36_probe.stage_e5` :712-753; the exact-match call shape is `phase17_persona_gate.py:335-341`:
```python
texts = [text for question in questions_by_slot[fact.slot] for text in probe_cache[question]["completions"]]
hits = [text for text in texts if not fs.exact_match_clean([text], fact.value)]
verdicts[fact.id] = (len(hits), len(texts), fs.exact_match_clean(texts, fact.value))
```
Phase 38: `phase14_factset.exact_match_clean(completions_by_slot[slot], candidate)` with `completions_by_slot` parsed from the committed report (see No Analog). Parser invariants to `_prove` (`phase17_persona_gate.py:319-325` wording): 416 total, 52 per slot, question order == `phase17_isolation.held_out_by_slot()` order, `len(by_slot) == SLOTS_EXPECTED` (`phase17_isolation.py:152-161`).

**Phase 17 filters as proof on the scored prefix** (`phase17_personas.py:360-461`) — call the four functions on the first 512 (or 220 for birth_year) of each list, in the driver only (Pitfall 8: O(n^2), 31 s at n = 3066; never in a CI test on the full lists):
```python
personas.filter_token_budget({v: len(tok.encode(v)) for v in prefix})
personas.filter_roundtrip(tok, prefix)
personas.filter_substring_disjoint(prefix, phase17_persona_facts.FORBIDDEN_VALUES)
personas.filter_absent_from_questions(prefix, questions)
```

---

### `scripts/phase38_sizes_prereg.py` (fill file 2, after the minting record, before scoring)

**Analog:** `scripts/phase36_budget_prereg.py` :1-82 — a plain module with a docstring stating its freeze, plain `import phase35_prereg`, one fill with `input_records=` and `derivation=`:
```python
"""... Frozen once results/phase36_budget.json exists: any correction is a dated continuation module,
never an edit."""

import phase35_prereg
import phase36_budget

_PROBES = phase36_budget.probe_record_paths()
_CHOSEN = phase36_budget.chosen(_PROBES, **RULING)

V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(
    "v6_budget_and_stop_line",
    front_hours=_CHOSEN["front_hours"],
    ...
    input_records=_PROBES,
    derivation=phase36_budget.derivation(_CHOSEN, _PROBES, **RULING),
)
```
Phase 38 shape (RESEARCH :563-574): `MINTING_RECORD` derived from `V6_RESULT_PATHS`; `_SIZES = {slot: max |R|}` read from the committed record with `json` (never typed; ints 1..512; `birth_year` 220 per D-31); `derivation = {"value": _SIZES, "derivation": "...", "kind": "derived", "source": f"... {MINTING_RECORD} ..."}` (the path MUST appear in `source`, `_consume_inputs`); then
```python
E5_SET_SIZES = phase35_prereg.fill(
    "e5_set_sizes", set_sizes=_SIZES, input_records=(MINTING_RECORD,), derivation=_DERIVATION
)
phase36_caps.check_unit_caps("E5", **phase36_caps.counts_for("e5_set_sizes", E5_SET_SIZES))
```
Never pass `prefixes=` to `check_unit_caps` (Pitfall 3, measured refusal). Must stay cheap and torch-free: `tests/test_phase36_caps.py:272-283` `_owner_values` `exec_module`s it in the test process on ubuntu (no checkpoints) and reads `E5_SET_SIZES`; `tests/test_phase36_caps.py:286-294` then asserts `owner_overruns(...) == []` against the committed budget. Plain `import phase35_prereg` (no sys.path block in the analog — it relies on `scripts/` being on the path, which both `python scripts/...` and the tests provide).

---

### `scripts/phase38_rank.py` (MPS driver under the ledger; CPU crosscheck/emit/report)

**Analog:** `scripts/phase37_r1b.py` (453 lines) — copy the docstring-as-usage, module constants, `preflight`/`run`/`build_record`/`emit`/`main` split.

**Constants** (`phase37_r1b.py:61-85`):
```python
_ROOT = pathlib.Path(__file__).resolve().parent.parent
FRONT = "R1b"
RUN_ID = phase36_ledger.run_id(37, FRONT, "replica")
LAUNCH_PATHSPEC = ("scripts", "src", "results")
MODULES = ("scripts/phase19_erasure.py", ..., "scripts/phase37_r1b.py")
RUN_PROVENANCE_KEYS = ("git_sha_at_launch", "git_sha_at_end", "head_moved_during_run", "device",
                       "torch_version", "started_utc", "finished_utc")
```
Phase 38: `FRONT = "E5"`, `RUN_ID = phase36_ledger.run_id(38, FRONT, "rank")`; `MODULES` lists `phase18_extraction.py`, `phase19_erasure.py`, `phase14_recall.py`, `phase36_probe.py`, `phase35_prereg.py`, `phase36_ledger.py`, `phase36_caps.py`, `phase38_prereg.py`, `phase38_sizes_prereg.py`, `phase38_rank.py`.

**Sidecars** (`phase37_r1b.py:106-115`): `run_sidecar(root) -> root / "data" / "phase38_rank_run.json"`; a write-once NLL sidecar written per reading BEFORE the next reading (the sweep-record analog), so a crash keeps scored readings.

**Run inputs proven before the start line** (`phase37_r1b.py:124-142`, WR-03): `phase14_recall.CONVBASE_SLIM`, `ADAPTER_PATH`, `TOKENIZER_PATH`, the M2 adapter (`teach_persona.arm_outputs(...)["adapter"]`), `MINTING_RECORD`, and every gate-source JSON.

**Preflight — every refusal before the ledger start line** (`phase37_r1b.py:170-228`):
```python
for path in (root / prereg.R1B_RECORD, root / prereg.R1B_ARM_RECORD, run_sidecar(root), sweep_record(root)):
    _prove(not path.exists(), f"{path} exists: the one R1b attempt has already run (D-11)")
_prove(not any(line["run_id"] == RUN_ID for line in phase36_ledger.read_ledger(ledger_path)), ...)
refuse_if_dirty(who="phase37_r1b", detail=(...), pathspec=LAUNCH_PATHSPEC, cwd=_ROOT)
launch_sha = git_sha()
_prove(launch_sha != "unknown", "git_sha() could not read HEAD: ...")
launch_modules = module_sha256()
gate = phase36_ledger.require_launch(FRONT, ledger_path=ledger_path)
device = _device()
_prove(device == "mps", f"R1b is the MPS replica; preflight resolved {device!r}")
for path in run_inputs():
    _prove(pathlib.Path(path).exists(), f"{path} is missing: ... refuses before the ledger start line (D-16) ...")
curve = _curve()
_prove(adapter_sha256() == curve["adapter_in_sha256"], "the production adapter is not the one ...")
```
Phase 38 additions in the same block: `_prove(len(READINGS) <= prereg.APPROVED_E5_PREFIXES, ...)` citing D-21; `phase36_caps.check_unit_caps("E5", **phase36_caps.counts_for("e5_set_sizes", sizes_prereg.E5_SET_SIZES))`; the three SHA-256 checks (adapter vs curve `adapter_in_sha256`; `components_sha256` formula vs `results/phase36_probe_e1.json` `configuration.components_sha256`; M2 vs `results/phase19_retrain_scores.json` `retrain_scores.adapter_sha256`); `_device()` is `preflight_device(strict=True)["device"]` (`phase37_r1b.py:145-148`).

**`_curve()` checks** (`phase37_r1b.py:151-167`): slot, `stopped`, `len(ordered_prefix) == k`, `reference_set_size == len(reference_set_for(TARGET_SLOT))`.

**Run: ledger start, beat once, heartbeat thread, sidecar, ledger end, emit** (`phase37_r1b.py:231-339`):
```python
pre = preflight(root=root, ledger_path=ledger_path)
heartbeat_path = heartbeat_path or phase36_ledger.HEARTBEAT_PATH
phase36_ledger.append("start", run_id=RUN_ID, phase=37, front=FRONT, ledger_path=ledger_path)
state = {"point": RUN_ID, "stage": "sweep", "shape": None, "draw_index": None}
# B1: the thread's first beat comes only after its first wait: beat once now.
phase25_run.beat(heartbeat_path, **state)
stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
started_utc = _now()
try:
    import torch
    ...
    phase25_run.atomic_write_json(run_sidecar(root), {"run_id": RUN_ID, "git_sha_at_launch": ..., "git_sha_at_end": end_sha,
        "head_moved_during_run": end_sha != pre["git_sha"], "module_sha256_at_launch": pre["module_sha256"],
        "device": device, "torch_version": torch.__version__, "started_utc": started_utc, "finished_utc": _now(), ...})
    state.update(stage="done")
finally:
    stop.set()
    thread.join()
phase36_ledger.append("end", run_id=RUN_ID, phase=37, front=FRONT, record=prereg.R1B_RECORD, ledger_path=ledger_path)
return emit(root=root)
```
Release models between readings as `phase37_r1b.py:292-295` does (`model = None; gc.collect(); if torch.backends.mps.is_available(): torch.mps.empty_cache()`).

**Per reading, model construction + scoring loop** (`phase36_probe.py:756-785`, the E5 scoring sample):
```python
for k in (0, len(e1_components())):
    state.update(stage=f"e5_scoring_k{k}", shape=None, draw_index=None)
    model, tok, _forbid = adapted_model(device, k)
    for i, slot in enumerate(locked):
        state.update(shape=slot, draw_index=i)
        for value in phase18_extraction.reference_set_for(slot):
            phase19_erasure.value_span_nll_mean(model, tok, device, slot=slot, value=value)
    del model
```
Phase 38: k in `(0, 8, 16, 32, 64, 78)` via `phase36_probe.adapted_model(device, k)` (reuse, do not re-implement — it already calls `prove_published_adapter()` and never `inject_lora`); M2 via `phase14_recall.load_adapted_model(device, adapter_path=M2_PATH)`; adapter-off via the k = 0 model under `with adapter_disabled(model):`. For each reading: GATE first on `reference_set_for(slot)` (rank via the new `prereg.rank_in_prefix` must equal the committed rank; any mismatch -> STOP, sidecar marked `gate_failed`, ledger end), then score each slot's maximum set ONCE, one candidate per call (no batching), NLLs to the sidecar keyed by index into the minting record's lists (Pitfall 13).

**build_record + emit** (`phase37_r1b.py:342-438`): `emit` refuses an existing record (`"REFUSING to overwrite it ... dated continuations"`), requires the sidecar, verifies the per-stage sidecar's sha256 against the run sidecar, calls `refuse_if_dirty` with `:(exclude)` the record path, builds, `atomic_write_json`. Provenance block (`:385-395`):
```python
record["provenance"] = {
    "run": {key: blob[key] for key in RUN_PROVENANCE_KEYS},
    "module_sha256_at_launch": launch,
    "module_sha256": now,
    "modules_changed_since_launch": sorted(rel for rel in MODULES if launch.get(rel) != now[rel]),
    "head_at_write": git_sha(),
    "written_utc": _now(),
}
```
`provenance.run.{started_utc, finished_utc}` is what the ledger's `_closed_row` reads (`phase36_ledger.py:67` `RECORD_CLOCK`); `device == "mps"` makes `tests/test_phase36_ledger.py:722-733` require that the end line names `results/phase38_rank.json` — commit the ledger before the record.

**main** (`phase37_r1b.py:441-453`):
```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    commands = {"preflight": preflight, "run": run, "emit": emit}
    if len(argv) != 1 or argv[0] not in commands:
        raise SystemExit(__doc__)
    os.chdir(_ROOT)
    return commands[argv[0]]()
```
Add `"crosscheck"` and `"report"`.

**Gate sources (D-18), read with `json`, never typed** (shapes measured):
- k=0: `results/phase19_arm_erased.json` `pre_erasure.exposure[]` (`slot`, `rank`, `n_references`, `nll`);
- k=8/16/32/64: `results/erasure_kstar_summary.json` `checkpoints["8"|"16"|"32"|"64"].target.exposure_rank_this_run` and `.nontarget[...].exposure_rank_this_run` (keys are strings);
- k=78: `results/phase19_arm_erased.json` `exposure[]`;
- M2: `results/phase19_arm_retrain.json` `exposure[]`;
- adapter-off: `results/phase18_arm_adapter-off.json` `exposure[]`.
A2 counts: `erasure_kstar_summary.json` `.target.successes`, `.nontarget[...].post_answerable`/`pre_answerable`; k=78 from `results/phase19_target_scores.json` `target_scores.target.successes` and `target_scores.nontarget[fact_id].post_answerable` (never `phase19_arm_erased.json` `per_fact`, Pitfall 11); k=0 target via `phase19_run._pooled_rows` (Pitfall 10).

---

### `artifacts/com.personacore.phase38.rank.plist` (optional)

**Analog:** `artifacts/com.personacore.phase37.r1b.plist` (60 lines). Copy verbatim; change `Label` (:19) to `com.personacore.phase38.rank`, `ProgramArguments[3]` (:34) to `.../scripts/phase38_rank.py`, `StandardOutPath`/`StandardErrorPath` (:42, :44) to `logs/phase38_rank.{out,err}`. Keep `KeepAlive false` (:23-24), `RunAtLoad false` (:26-27), `/usr/bin/caffeinate -dims` + venv python (:31-33), `WorkingDirectory`, `ProcessType Interactive`, and `EnvironmentVariables` (`PERSONACORE_SWEEP_ACTIVE=1`, `PATH`, `PYTHONUNBUFFERED`) identical. If the planner picks a terminal launch instead, skip the file and its test.

---

### `tests/test_phase38_prereg.py`

**Analog:** `tests/test_phase37_prereg.py` (551 lines).

**Imports + shared helpers** (`:32-62`):
```python
import phase35_prereg  # noqa: E402  (scripts/ is not a package)
import phase36_prereg  # noqa: E402  (same)
import phase37_prereg  # noqa: E402  (same)

from test_phase29_prereg import _assert_frozen_before, _git, _planted  # noqa: E402
from test_phase35_prereg import _insert_at, _literal_failures, _slot_census_failures  # noqa: E402
from test_phase36_prereg import (  # noqa: E402
    _HEAVY, _entries_node, _entry_string_failures, _first_inner, _skip_failures, _untested_functions,
)
PREREG = "scripts/phase37_prereg.py"
```
Helper locations: `_git` `tests/test_phase29_prereg.py:52`, `_assert_frozen_before` :69, `_planted` :526; `_insert_at` `tests/test_phase35_prereg.py:111`, `_literal_failures` :749, `_slot_census_failures` :2166, `_fill_sites` :2463, `_slot_ordering_failures` :2475; `_entries_node` `tests/test_phase36_prereg.py:106`, `_entry_string_failures` :115, `_first_inner` :135, `_HEAVY` :372, `_skip_failures` :396, `_untested_functions` :418.

**Ancestry trio** (`:270-304`): `test_phase37_prereg_is_frozen_before_every_phase37_record` (natural RED against `scripts/phase35_prereg.py`), `test_this_test_file_is_first_added_before_every_phase37_record` (FIRST add only, `_first_add` :275-276, `_strictly_before` :270-272), `test_records_at_commit_is_true_at_the_first_commit`. Glob `results/phase38_*` — it includes the minting record, which is exactly leg (a).

**Literal scan for derived values** (`:383-404`): put `e5_projection_hours(8)`, `E5_STOP_HOURS`, the 77.83 total and the margin in `_forbidden_floats()`; plant a typed copy and assert RED.

**Entries four-field + proposer AST + planted phrase** (`:412-459`), **preferences labelled** (`:501-506`), **ruling quoted** (`:473-498`, adapt the parser to 38-CONTEXT `<decisions>` bullets for D-21).

**Torch-free subprocess probe** (`:514-522`):
```python
probe = ("import sys; sys.path.insert(0, 'scripts'); import phase37_prereg; "
         f"print(*[name in sys.modules for name in {_HEAVY!r}])")
out = subprocess.run([sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True)
assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout
```
`_HEAVY` includes `"phase23_run"`, so this test also proves `seed_list()` is not called at import (Pitfall 2).

**Slot census over the phase glob** (`:525-529`), **zero skips** (`:532-536`), **every function has a CPU test** (`:539-551`). Rank equivalence property test: random 6-8 dicts with forced ties, `rank_in_prefix(...) == phase18_extraction.exposure_rank(d, taught_value=t, reduction="mean", length_spread=0)["rank"]` (import `phase18_extraction` inside the test, as `:313-314` imports the pin). The collapse/damage table (RESEARCH :445-454) is the expected output of `first_collapse`/`first_damage` on committed JSON, including person_name's k=8 exact-margin tie (strict `>`).

---

### `tests/test_phase38_mint.py`

**Analogs:** `tests/test_phase37_r1a.py` (write-once / dirty refusals, real committed inputs) and `tests/test_phase17_personas.py` (`_levenshtein` :95-103 witness, `test_values_are_not_token_level_neighbours` :314). Fixtures read only tracked files (`artifacts/tokenizer.json`, `results/phase17_personas_report.md`, fact modules) so ubuntu runs it with zero skips. One real smallest-shape CPU run into `tmp_path` (Pitfall 12), the `_real_tree_untouched` autouse fixture from `tests/test_phase37_r1b.py:80-88` (`git status --porcelain -- results ledger` unchanged). Prefix-stability test: list at a smaller stop is a prefix of the list at a larger stop.

---

### `tests/test_phase38_sizes_prereg.py`

**Analog:** `tests/test_phase36_budget.py`.
- Consumer chain before the record exists: monkeypatch `phase35_prereg._REPO_ROOT` to a tmp repo holding a planted `results/phase38_minting.json`, then call `phase35_prereg.fill("e5_set_sizes", ...)` (`:905-917`). Note this monkeypatches a `_`-attribute from a TEST, which the census allows (the census scans `scripts/phase38_*` sources only, `owner_prereg_glob`).
- Ancestry (`:1214-1226`): every commit of the sizes file strictly precedes every other `results/phase38_*`; the minting record's first add strictly precedes the sizes file's first commit (leg b), natural RED against `scripts/phase35_prereg.py`.
- Caps: `tests/test_phase36_caps.py::test_owner_fill_files_respect_the_caps_on_the_real_repo` (:286) goes live as soon as the file is tracked; no new code needed there.

---

### `tests/test_phase38_rank.py`

**Analog:** `tests/test_phase37_r1b.py` (735 lines).
- `rig` fixture (`:110-166`): tmp root with `results/` and `data/`, tmp ledger/heartbeat, gitignored inputs stood in with tmp files (`:124-128`), `_device -> "mps"`, `refuse_if_dirty` recorder, `require_launch` stub recording `(front, kw, ledger_exists)`; stub `phase36_probe.adapted_model`, `phase14_recall.load_adapted_model` and `phase19_erasure.value_span_nll_mean` with a deterministic fake NLL table (no checkpoints on ubuntu).
- Parametrized preflight refusals that write no ledger line (`:372-426`) + missing-input refusals (`:433-442`) + `test_preflight_alone_writes_nothing_and_reports_the_gate` (`:445-452`). Add: readings > `APPROVED_E5_PREFIXES`, each SHA mismatch, an existing NLL sidecar.
- WR-01 head-moved test (`:455-472`), crash-after-start rehearsal with `phase36_ledger.reconcile` (`:475-555`), gate-STOP path, emit tests fed the real committed gate sources (`:588-631`).
- `main` dispatch with `inspect.signature(real).bind` + cwd assertion (`:653-674`); plist mirror (`:681-716`) if the plist exists; zero skips (`:719-723`); every function called (`:726-735`).
- AST gates (RANK-03): no `exposure_rank` / `_rank_of` call outside the gate path in `scripts/phase38_*`; use `_call_sites(callee, source)` from `tests/test_phase19_erasure.py:2011`.

---

## Shared Patterns

### Refusal
**Source:** `_prove` in every module (`phase37_prereg.py:50-53`, `phase37_r1a.py:74-76`, `phase37_r1b.py:88-90`): `raise SystemExit(f"[<module>] {message}")`, never `assert` (`python -O`). Tests match `r"^\[phase38_<module>\]"`.
**Apply to:** all four scripts.

### Write-once + clean tree + atomic write
**Source:** `phase37_r1a.write_record` :144-193, `phase37_r1b.emit` :399-438, `phase25_run.atomic_write_json` :118.
**Apply to:** `phase38_mint.py`, `phase38_rank.py`. `os.replace` is banned outside `phase25_run.py`/`phase25_record.py` (`tests/test_phase25_driver.py:341-365`). The markdown report has no atomic writer: refuse-if-exists, then `path.write_text(text, encoding="utf-8")`.

### Instrument reuse, never re-implementation (RANK-03)
Import `value_span_nll_mean`, `reference_set_for`, `ADMISSIBLE_NLL_*`, `adapted_model`, `exact_match_clean`, the four `filter_*`; re-implement only the rank (because of the `6 <= len <= 8` guards, `phase18_extraction.py:1211, :1262`). `phase18_extraction.py` bytes are pinned (`tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte`).

### Torch-free prereg
**Source:** `tests/test_phase37_prereg.py:514-522` + `_HEAVY`. **Apply to:** `phase38_prereg.py` (and keep `phase38_sizes_prereg.py` torch-free so the caps test can exec it).

### Ledger discipline
`require_launch("E5")` in preflight (writes nothing), start line only after every refusal, beat once then thread, end line naming the record, sidecar before the end line, `emit` re-runnable on CPU (`phase37_r1b.py:170-339`). E5 lines stay standard (D-22); no `rule` call (D-23).

## Census / real-tree tests a new `scripts/phase38_*.py` or `tests/test_phase38_*.py` trips

| Guard | Location | What it requires |
|---|---|---|
| Slot census | `tests/test_phase35_prereg.py:2166` | Bindings `E5_MINTING_RULE`, `E5_RANK_MOVES_AND_GENERATION_COLLAPSES`, `E5_SET_SIZES` as the whole module-level value; plain `import phase35_prereg`; no `phase35_prereg._*`, no `_rule_*`, no `SLOTS[...]` in any `scripts/phase38_*` |
| Slot ordering legs a/b/c | `tests/test_phase35_prereg.py:2475` | prereg frozen before ANY `results/phase38_*` (incl. minting); sizes file after minting, before rank records; all three filled once a non-input phase-38 record is tracked |
| Owner caps (exec's sizes file) | `tests/test_phase36_caps.py:272-294` | ≤ 8 sets, max ≤ 512, importable on ubuntu |
| MPS launch line | `tests/test_phase36_ledger.py:722-733` | ledger end line names `results/phase38_rank.json` before it is tracked |
| `inject_lora` register | `tests/test_lora_inject.py:261, :478` | never call `inject_lora`; no new line |
| `os.replace` | `tests/test_phase25_driver.py:341-365` | use `atomic_write_json` |
| `== 10` wall | `tests/test_phase21_sc5.py:189-196` | no `== 10`/`!= 10` (comments and prose included) in `tests/test_phase38_*` |
| RANK-03 bytes | `tests/test_phase21_sc5.py::test_instruments_unchanged_byte_for_byte` | never touch `phase18_extraction.py` |
| skip pins | `tests/test_phase25_venue.py:324-365` | zero skips; no checkpoint dependency |
| `retention_perplexity`, `draw_all`, `build_recall_prompt`, `train_arm`/`train_never_taught` | `tests/test_phase19_erasure.py:1386`, `tests/test_phase14_scoring.py:631,744`, `tests/test_phase23_ctrl.py` | do not call them |
| clean-tree probes | `tests/test_phase25_driver.py`, `test_phase25_frontier`, `test_phase23_resume`, `test_phase25_grid` | commit new phase38 files before the full suite |

## No Analog Found

| File / piece | Role | Data Flow | Reason / what to use |
|---|---|---|---|
| Phase 17 completions parser (in `phase38_mint.py` or the prereg) | utility | file-I/O parse | Nothing parses `results/phase17_personas_report.md` today. Format (measured, `:80` onward): `### Slot \`<slot>\` — 13 questions, 52 completions`, `- Q \`<question>\` — prompt = <n> ids`, `  - greedy: \`<text>\``, `  - warm <i>: \`<text>\``. Use RESEARCH :651-658 + the D-24 invariants; pin the report sha256. |
| Syllable grammar + global-stop dealer | utility | transform | No in-repo generator; RESEARCH M1 :184-203 is the complete instance (draw only through `rng.random()`). |
| Seeded Fisher-Yates from `random()` | utility | transform | `phase16_persistence.py:901` gives the LOCAL-`Random` discipline only; write the shuffle by hand. |
| `results/phase38_rank_report.md` renderer | report | transform | v6.0 has no markdown emitter; `scripts/phase34_report.py:381-391` (`render` from committed records via a template) is the nearest but heavy. A pure `render_report(record) -> str` in `phase38_rank.py`, fed one real producer record in a test before any MPS launch (Pitfall 12), is enough. |

## Metadata

**Analog search scope:** `scripts/phase3[5-7]_*.py`, `scripts/phase36_*.py`, `scripts/phase17_*.py`, `scripts/phase14_factset.py`, `scripts/phase18_extraction.py` (targeted), `scripts/phase19_erasure.py` (targeted), `scripts/phase25_run.py`, `scripts/phase16_persistence.py`, `scripts/phase34_report.py`, `artifacts/*.plist`, `tests/test_phase3[5-7]_*.py`, `tests/test_phase17_personas.py`, `tests/test_lora_inject.py`, `tests/test_phase36_{caps,ledger,budget}.py`, committed gate-source JSON shapes.
**Files scanned:** about 35.
**Pattern extraction date:** 2026-10-04
