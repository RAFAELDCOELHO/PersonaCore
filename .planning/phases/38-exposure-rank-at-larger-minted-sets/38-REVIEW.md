---
phase: 38-exposure-rank-at-larger-minted-sets
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - scripts/phase38_prereg.py
  - scripts/phase38_mint.py
  - tests/test_phase38_prereg.py
  - tests/test_phase38_mint.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: resolved
second_review: {critical: 0, warning: 3, info: 5, total: 8}
---

# Phase 38: Code Review Report

**Reviewed:** 2026-10-04
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Severity rule (Rafael's): a finding is a BLOCKER only if it changes a value that is read, or an emitted verdict or record, in the real run (the mint at SLACK_PER_SLOT = 2048 on the committed tree). Deliberate bypass is at most a WARNING.

**The real mint was run end to end into scratch.** I called `phase38_mint.derive()` with the frozen constants and wrote its output only to `/private/tmp/claude-501/p38/`. It finished in 73.9 s with no STOP:

- `stop_draw` 58195, matching D-35's measurement. The stream rejected 38007 draws on token count and 2452 as duplicates.
- Name slots: person_name 2125, **pet_name 2048** (the slot that binds the stop), cat_name 2113, sibling_name 4951, hometown 2087, street 2102.
- birth_year: 219 cleared, max |R| 220. house_number: 8768 cleared, max |R| 512, with 219 values taken by birth_year (D-26).
- birth_year neighbour counts are {8: 2, 32: 11, 128: 59, 220: 101}, matching D-27's 101/219.
- The Phase 17 four-filter proof passed on the scored prefixes.

**D-ID conformance was traced clause by clause against `ENTRIES["e5_minting_rule"]`.** All of these hold, and I found no mismatch that changes the record:

- The generator calls only `rng.random()`, in the order n_syllables, then onset, nucleus and coda per syllable (D-01).
- The stream keeps a draw only at a taught token count, then drops duplicates.
- The deal is round-robin over the slots that share a count, and the counter advances on every unique draw.
- NAME_FILTERS and NUMERIC_FILTERS run in their declared order, and the first failure is the one counted.
- The global stop is checked after every dealt draw. That is equivalent to "after every draw", because stream rejections never change the lists. The lists are prefix-stable.
- D-26 STOP at MAX_DRAWS; one slot per string (`seen`); substring-disjointness across all slots, through the minted set ∪ forbidden_for_substring.
- The D-27 screen applies to names only, against taught_anywhere; numeric slots are flagged instead.
- D-10 Fisher-Yates: from i = n-1 down to 1, j = int(random() * (i + 1)).
- D-31: max |R| = min(512, n_cleared + 1).
- D-24: the report digest and the 416/52/13 invariants hold.
- D-32: the question order equals `held_out_by_slot()`.
- `phase14_recall.normalize` (Phase 17's filters) and `phase14_factset.normalize_for_match` (this phase's screens) have identical composition, so the proof and the screens agree.
- `write_record` refuses in this order: wrong glob, existing file, untracked prereg, dirty tree. It writes through `atomic_write_json`.

No BLOCKER was found. The four WARNINGs below are the last chance to change frozen code:

- **WR-01** is the important one. It is in the definitions half of the same frozen file, and it can turn into an emitted-verdict defect depending on rank values that cannot be measured until the MPS run.
- **WR-02 and WR-03** are provenance gaps in the write-once record.
- **WR-04** is about verify mode.

## Warnings

### WR-01: `left_top_eighth` is flagged at k = 0, so an event that was already true before any erasure is reported as "BEFORE" collapse and damage

**File:** `scripts/phase38_prereg.py:726-734` (`left_top_eighth`, `first_event`), used by plan 07's `build_record` (flags over all of `PREFIXES`, k = 0 included)

**Issue:** `first_event` scans `PREFIXES` starting at 0.

- For D-12 `moved` that is harmless, because `moved(rank_0, rank_0)` is always False.
- For D-29 `left_top_eighth(rank_k, size)` it is not harmless, because the flag has no k = 0 reference. If rank_0 × 8 > |R| at some (slot, size), `first_event` returns 0 and `relation(0, ref)` returns `"BEFORE"` for every reference that exists. In that case the taught value was never in the top eighth, so this reports an erasure-ordering verdict for an event that erasure did not cause.
- This cannot happen at the committed |R| 6-8, where rank_0 = 1. At the minted sizes it is plausible. For example, birth_year at |R| = 220 has 101 of 219 candidates within distance 1 of a taught year, and 220/8 = 27.5, so rank_0 > 27 is enough.
- Whether it happens is unknown until the MPS readings exist. By then this file is frozen and only a dated continuation can fix it.

A related property of D-12 should be named before the freeze too: at |R| = 8 with rank_0 ≥ 5, `moved` can never fire, because it needs rank ≥ 10 > 8. The result reads "NEVER" even though the definition simply has no room to fire. Today nothing distinguishes that ceiling from a genuine never.

**Experiment (run, confirms):**
```
.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import phase38_prereg as p; f={k: p.left_top_eighth(30,220) for k in p.PREFIXES}; e=p.first_event(f); print(e, p.relation(e,64), p.relation(e,32)); print(any(p.moved(r,5) for r in range(1,9)))"
# -> 0 BEFORE BEFORE
# -> False
```
**Fix (before the freeze):** name the baseline outcome, and keep the event a change relative to k = 0:
```python
def first_event(flags):
    _prove(set(flags) == set(PREFIXES), ...)
    return next((k for k in PREFIXES if flags[k]), None)

def relation(event_k, reference_k):
    if event_k == 0:
        return "ALREADY_AT_K0"          # true before any erasure: not an ordering verdict
    ...
```
Add `"ALREADY_AT_K0"` to `ENTRIES["event_relation"]["value"]`, and have plan 07 publish `rank_0 * 8 > size` per (slot, size). The alternative is to state in D-29's entry that a k = 0 hit is reported as BEFORE, so the behaviour is at least pre-registered. Optionally publish a `moved_possible = 2 * rank_0 <= size` flag beside the D-12 relation.

### WR-02: Provenance is read after the 74 s mint, and there is no check that HEAD and the modules were unchanged between launch and write

**File:** `scripts/phase38_mint.py:230-246`, `:179-199`

**Issue:** `main()` imports the rule and runs `derive()` before any git read. Then `git_sha()`, `refuse_if_dirty` and the `module_sha256` digests are all taken at write time.

- If HEAD moves during the run (a commit lands), the record names a commit, and module digests, that the in-memory rule never ran from. The tree is clean at write time, so nothing refuses.
- The same can happen if a file is edited and then restored. Peer sessions editing or committing the working tree mid-session is a known hazard in this repo.
- The rank driver this phase plans (38-06) records `git_sha_at_launch`, `git_sha_at_end` and `head_moved_during_run` for exactly this reason. The write-once minting record has neither.
- It is not a BLOCKER, because a quiet tree produces the same record.

**Experiment:** in a scratch clone, run `main(out_root=<tmp>)` with `derive` wrapped to `git commit --allow-empty` before returning. The written `provenance.run.git_sha` is then the new HEAD, not the launch HEAD. Static reading of lines 231-240 shows the same thing: no git read precedes `derive()`.

**Fix:**
```python
launch_sha = git_sha(); refuse_if_dirty(who="phase38_mint", detail=..., pathspec=PATHSPEC, cwd=_ROOT)
launch_modules = {r: _sha256(_ROOT / r) for r in MODULES}
derived = derive()
...
_prove(git_sha() == launch_sha and {r: _sha256(_ROOT / r) for r in MODULES} == launch_modules,
       "HEAD or a rule module changed during the mint: the record would name code that did not run")
```

### WR-03: The dirty-tree pathspec leaves out `artifacts/tokenizer.json`, an input the mint reads

**File:** `scripts/phase38_mint.py:176-188` (pathspec `("scripts", "src", "results")`), `:41-42`

**Issue:** `artifacts/tokenizer.json` is tracked and is one of the two `INPUT_RECORDS`. Token counts, the roundtrip check and the deal all depend on it.

- A modified tokenizer is invisible to `refuse_if_dirty`. The record is then written with a `git_sha` it cannot be re-minted from, and `input_sha256` records the dirty bytes.
- Verify mode on a clean checkout would STOP. That only happens after the write-once record has been committed, and a committed record can only be corrected by a dated continuation.
- The tree is clean today, so the real run is unaffected.

**Experiment (run, in a scratch clone):**
```
D=/private/tmp/claude-501/p38/clone; git clone -q . $D && cd $D && echo ' ' >> artifacts/tokenizer.json && git status --porcelain -- scripts src results; git status --porcelain; rm -rf $D
# -> ""   then   " M artifacts/tokenizer.json"
```
**Fix:** `pathspec = ("scripts", "src", "results", *INPUT_RECORDS)`. The report is already under results/, and adding it again is harmless.

### WR-04: Verify mode accepts a record with wrong provenance or extra top-level keys, and does not check that the file is the committed blob

**File:** `scripts/phase38_mint.py:206-221`

**Issue:** `check_record` compares only the keys of `derived` and `input_sha256`.

- A record whose `provenance.run.git_sha`, `device` or `module_sha256` is wrong passes with "MINTING VERIFIED".
- So does a record with an additional top-level key such as `slots_override`.
- So does a working-tree file that differs from the committed blob only in those fields.

The values that consumers read (`slots[*].cleared`, `n_cleared`, `max_set_size`) are checked, so no read value changes. This is the deliberate-bypass class, but "VERIFIED" overstates what was verified.

**Experiment (run, scratch only):**
```
.venv/bin/python -c "import sys,json,pathlib; sys.path[:0]=['scripts','src']; import phase38_mint as m; d=json.loads(pathlib.Path('/private/tmp/claude-501/p38/derived.json').read_text()); r={**d,'input_sha256':{x:m._sha256(m._ROOT/x) for x in m.INPUT_RECORDS},'provenance':{'run':{'git_sha':'0'*40}},'slots_override':{}}; p=pathlib.Path('/private/tmp/claude-501/p38/fake.json'); p.write_text(json.dumps(r)); m.check_record(d,p); print('PASSED')"
# -> PASSED
```
(`derived.json` is the scratch output of the real-scale `derive()` above.)

**Fix:**
```python
_prove(set(record) == set(derived) | {"input_sha256", "provenance"}, "STOP: unexpected record keys")
_prove(set(record["provenance"]["module_sha256"]) == set(MODULES), "STOP: provenance shape")
# when path is under _ROOT: the bytes equal `git show HEAD:<rel>` (the record verified is the committed one)
```

## Info

### IN-01: `parse_completions` does not undo the report's `\n` / `\t` escaping

**File:** `scripts/phase38_prereg.py:968-975`, against `scripts/phase17_persona_gate.py:448` (`text.replace("\n", "\\n").replace("\t", "\\t")`)

**Issue:** If the parser ran on an escaped completion, clearance would see the literal `\n` as two characters. That would add spurious containments, such as `n` plus the next word. Measured: the pinned report has 0 escaped sequences and 0 backslashes, so this is inert under the SHA-256 pin.

**Experiment:** `.venv/bin/python -c "import sys,pathlib; sys.path.insert(0,'scripts'); import phase38_prereg as p; c,_=p.parse_completions(pathlib.Path(p.PHASE17_REPORT).read_text()); print(sum(x.count(chr(92)) for v in c.values() for x in v))"` gives `0`.

**Fix:** Optionally add a one-line `_prove` that no parsed completion contains a backslash, so a future re-pin cannot silently change semantics.

### IN-02: `MODULES` digests leave out modules the rule depends on

**File:** `scripts/phase38_mint.py:43-52`

**Issue:** These are not hashed:

- `phase23_run` (the seed through `seed_list`)
- `phase14_recall` (the proof's normalizer)
- `phase19_floor`, `phase36_budget`, `phase36_prereg` (the approval block)
- `phase25_run`
- `src/personacore/tokenizer.py` and the `detokenize` source used by `normalize_for_match`

The clean-tree check plus `git_sha` is the real guarantee, so this is informational only.

**Fix:** Add them, or document that `module_sha256` is a partial list.

### IN-03: `atomic_write_json(sort_keys=True)` reorders `slots` and `rejections` in the record

**File:** `scripts/phase38_mint.py:202`

**Issue:** The record stores slots in alphabetical order (birth_year, cat_name, ...), not in SLOTS order, and rejections not in NAME_FILTERS order. The `cleared` lists keep their order, and they are the part that matters. Plan 05 iterates `prereg.SLOTS`, so nothing breaks. Any future consumer must not rely on dict order.

### IN-04: Write-once is check-then-`os.replace`; a path outside `base` raises `ValueError`

**File:** `scripts/phase38_mint.py:157-166`

**Issue:** Between `not path.exists()` and `os.replace`, a concurrently created record would be overwritten. This is a known TOCTOU, and it requires a second minting process. Separately, `path.relative_to(base)` raises `ValueError` before the glob refusal can report it. `main` never hits this.

**Fix:** Optional. Use `os.open(path, O_CREAT|O_EXCL)` as a reservation, or document the limitation. Prove `path.is_relative_to(base)` with `_prove` first.

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Resolution (Rafael's ruling at the 38-04 review checkpoint, 2026-10-04)

| Finding | Ruling | Commit |
|---|---|---|
| WR-01 | FIXED as ruled: `relation` returns `ALREADY_AT_K0` when the event already holds at k = 0 and `UNREACHABLE_AT_SIZE` when "moved" cannot fire at the size (`moved_reachable(rank_0, size)` is `2 x rank_0 <= |R|`); NEVER stays "could have moved and did not"; both outcomes are recorded with rank_0, the per-prefix flags are unchanged, and one sentence each sits in the D-12 (`rank_moved`) and D-29 (`left_top_eighth`) entries. Precedence (orchestrator's choice, within the ruling): UNREACHABLE_AT_SIZE, then ALREADY_AT_K0, then the reference outcomes. Tests cover birth_year at |R| = 220 with rank_0 >= 28 and |R| = 8 with rank_0 >= 5. | d33986c |
| WR-02 | Not fixed: known limitation (no commit may land on main during the ~74 s mint; plan 04 Task 2 records `git rev-parse HEAD` before the run and requires provenance git_sha and head_at_write to equal it) | — |
| WR-03 | Not fixed: known limitation (plan 04 Task 2 requires the whole `git status --porcelain` to be clean before the mint, which covers artifacts/tokenizer.json) | — |
| WR-04 | Not fixed: known limitation (deliberate-bypass class; every value a consumer reads is still checked) | — |
| IN-01..IN-04 | Not fixed: informational | — |

Downstream: the 38-07 record builder must pass `reachable=prereg.moved_reachable(rank_0, size)` for the moved event and record rank_0 beside every relation; 38-09/38-10 present the two new outcomes alongside BEFORE / SAME / AFTER / NEVER.

# Second review (2026-10-04): scoring driver and sizes fill (38-08 Task 1)

**Reviewed:** 2026-10-04
**Depth:** standard
**Files reviewed (4):** `scripts/phase38_rank.py`, `scripts/phase38_sizes_prereg.py`, `tests/test_phase38_rank.py`, `tests/test_phase38_sizes_prereg.py` (diff base 7f4f4a0; HEAD at review bb54beb, which differs from d57248f only by a docs(state) commit that touches no DISCLOSED_MODULES file)
**Status:** issues_found

**Counts:** critical 0, warning 3, info 5, total 8

## Summary

Severity rule (Rafael's): a finding is a BLOCKER only if it changes a read value or an emitted verdict or record in the real run, or can corrupt or brick the ledger in a plausible crash. Deliberate bypass is a WARNING or a known limitation.

**No BLOCKER.** I traced the real run path, the real-root shape and the 38-08 crash rules line by line. These hold:

- **Ledger and recovery (focus 1).** Every refusal runs before the start line: preflight, then `scoring_plan`, then `append("start")` (`:530-533`). Each failure point after the start line leaves a state that one crash rule handles:
  - A crash before the first beat leaves an open start. `reconcile` closes it at 0 s with NO_BEAT_FLAG.
  - A crash in the gate, or mid-scoring, leaves no run sidecar, so rule (ii) applies. Already-written NLL sidecars are atomic and stay intact, and preflight then refuses on them (tested at `:731-753`).
  - A crash after the run sidecar but before the end line is rule (i). The run sidecar is written last inside `try`, and the end line comes after `finally`.
  - A crash in `emit` is atomic (`atomic_write_json`), so emit can simply be retried.
  - Nothing in the driver rewrites or removes a ledger line.
- **D-18 (focus 2).** All readings are gated, each with its own model build, before the `if passed:` scoring loop. `passed` is `all(...)` over 8 x 8 rows on the real root, which is forced to the full shape (`:524-529` and `:428`). Any rank or `n_references` mismatch gives GATE_FAILED and scores no minted value.
- **D-20, D-23 (focus 3).** Preflight proves three digests against committed records: the persona adapter against `adapter_in_sha256`, the components against `phase36_probe_e1.configuration.components_sha256`, and M2 against `retrain_scores.adapter_sha256`. `require_launch("E5")` is the only stop and there is no in-run timer. Both `check_unit_caps` calls pass `counts_for("e5_set_sizes", ...)`, so `sets` and `max_set_size` only, never `prefixes`.
- **Record arithmetic (focus 4).** Everything goes through `phase38_prereg`. The functions used are `rank_in_prefix`, `exposure_bits`, `moved`, `left_top_eighth`, `first_event`, `first_collapse`, `first_damage`, and `relation`. For moved, `relation` gets `reachable=moved_reachable(rank_0, size)`. Every event carries `rank_0`. Events are keyed by the six PREFIXES only, so M2 and adapter_off never enter them.
  - D-27 `neighbour_d1` holds indices into `cleared`, and `curve_for`'s `i not in excluded` reads them as indices. Measured: the counts at `i < size - 1` reproduce the record's `neighbour_counts` exactly (birth_year 2/11/59/101, house_number 1/2/10/19).
- **D-34 (focus 5).** The committed identity's digests are the git blobs at 91553d9: `git show 91553d9:scripts/phase38_rank.py | shasum -a 256` gives `f887d437…` and the sizes file gives `18f37b0b…`. Since then exactly one commit touches a DISCLOSED_MODULES file (1e68330), and the disclosure lists it.
- **Write-once and report (focus 6, 7).** The 13 sections render in order. D-36 Limitations appears on both statuses. WR-01 outcomes render by name with `(rank_0 = N)`.
- **Sizes fill.** `max_set_size(n_cleared)` equals the record's `max_set_size` for all 8 slots. The sizes fit the caps with no `prefixes`.
- **Tests.** `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase38_rank.py tests/test_phase38_sizes_prereg.py` gives `96 passed in 23.94s`.

The three warnings are all on the **rehearsal and disclosure** side. 38-08 Task 1 explicitly schedules a re-rehearsal whenever a fix touches the run path, and on that path the driver's defaults can write into the real milestone ledger (DR-01) or under-disclose what was read (DR-02).

## Warnings

### DR-01: A rehearsal root silently uses the REAL milestone ledger and heartbeat when `ledger_path` / `heartbeat_path` are omitted

**File:** `scripts/phase38_rank.py:507-539` (`append("start", ..., ledger_path=ledger_path)` at `:533`, `heartbeat_path or phase36_ledger.HEARTBEAT_PATH` at `:534`, `append("end")` at `:609-616`)

**Issue:** `run()` routes a non-real (tmp) root, CPU device, to whatever ledger it is given. `None` means `ledger/v6_mps_ledger.jsonl`. The 38-07 rehearsal passed tmp paths, but nothing enforces that. 38-08 Task 1 requires a CPU re-rehearsal into a fresh root if any fix touches the run path. If that re-rehearsal omits `ledger_path`, the append-only real ledger gets a `start` and an `end` line for `v6/38/E5/rank` naming `results/phase38_rank.json` from a CPU run. The consequences:

- E5 spend counts that CPU span. It is superseded only by its own ledger span (CR-01) once the real end line names the same record.
- Task 4's check of "exactly one start and one end line for v6/38/E5/rank" can never pass again.
- The rehearsal's beats land in the real heartbeat file under the real point.

This is not a crash, so it is a WARNING under the rule. It becomes a ledger-integrity defect the moment a re-rehearsal is run without the two kwargs.

**Experiment (run; `append` stubbed to stop before any write; real ledger bytes asserted unchanged):**
```
.venv/bin/python <scratch>/rv/e1.py
# PREFLIGHT OK bb54beb… device=cpu readings=1 …
# append called with ('start', None) -> ledger_path None means /Users/juliorcoelho/PersonaCore/ledger/v6_mps_ledger.jsonl
# heartbeat default: /Users/juliorcoelho/PersonaCore/data/v6_mps_heartbeat.jsonl
# real ledger unchanged
```
(`e1.py`: `phase36_ledger.append = <raise SystemExit, record ledger_path>`, then `phase38_rank.run(root=<tmp>, device='cpu', readings=('k0',), slots=('pet_name',), max_size=8)`.)

**Fix:** Put this beside the existing shape `_prove`, before preflight. The real run is untouched, and the rig tests already pass both paths.
```python
if not _is_real(root):
    real = {
        (phase36_ledger._ROOT / phase36_ledger.LEDGER_PATH).resolve(),
        pathlib.Path(phase36_ledger.HEARTBEAT_PATH).resolve(),
    }
    _prove(
        ledger_path is not None
        and heartbeat_path is not None
        and real.isdisjoint({pathlib.Path(ledger_path).resolve(), pathlib.Path(heartbeat_path).resolve()}),
        "a rehearsal root writes its own ledger and heartbeat, never the milestone ones (D-17)",
    )
```
Alternative if not fixed: rule that a re-rehearsal reuses the 38-07 Task 4 kwargs script verbatim, and record that ruling as a known limitation.

### DR-02: `record_rehearsal` keeps the first identity even when a later rehearsal reads a different (wider) slice, so the D-34 disclosure under-states what was read

**File:** `scripts/phase38_rank.py:165-172` (kept branch); `:537-538`; test `tests/test_phase38_rank.py:1074-1076` asserts this behaviour

**Issue:** The `kept` branch returns without comparing `readings`, `slots` or `max_size` with the kept identity. The record's `rehearsal_disclosure.slice_read` and `statement` come only from the kept identity (`:224-230`). A 38-08 re-rehearsal that reads more could still happen, for example all slots, or `max_size=32`. Then the real record says the rehearsal read only `pet_name, birth_year at |R| 8`, an emitted D-34 field that is wrong. Today the record is right, because both 38-07 rehearsals read the same slice. That makes this conditional on the re-rehearsal, hence a WARNING. The existing test `_identity(path, slots=["street"], max_size=32)` -> `kept` encodes the gap as intended behaviour.

**Experiment (run, tmp only):**
```
.venv/bin/python -c "import sys,pathlib,tempfile; sys.path[:0]=['scripts','src']; import phase38_rank as r; p=pathlib.Path(tempfile.mkdtemp(dir='/private/tmp/claude-501'))/'id.json'; r.record_rehearsal(p,readings=['k0'],slots=['pet_name'],max_size=8); k=r.record_rehearsal(p,readings=list(r.prereg.READINGS),slots=list(r.prereg.SLOTS),max_size=None); print(k['status'],k['slots'],k['max_size']); print(r.rehearsal_disclosure(r._load(p),launch_git_sha=r.git_sha(),launch_module_sha256=r.module_sha256())['statement'])"
# kept ['pet_name'] 8
# The CPU rehearsal (38-07) read pet_name at |R| 8 under 1 readings, …
```

**Fix:** Refuse a different slice in the kept branch. Change the test at `:1074` to expect `SystemExit` for the different slice and `kept` for the same one.
```python
if path.exists():
    kept = _load(path)
    _prove(
        (kept["readings"], kept["slots"], kept["max_size"]) == (list(readings), list(slots), max_size),
        f"{path} recorded a different slice; a wider rehearsal would go undisclosed (D-34)",
    )
```
`record_rehearsal` is on the run path, so per 38-08 Task 1 this fix itself needs the re-rehearsal (which then prints `REHEARSAL KEPT`).

### DR-03: Preflight checks only that the D-34 identity file EXISTS; the disclosure that can refuse is first computed at `emit`, after the MPS hours are spent

**File:** `scripts/phase38_rank.py:440-444` (`.exists()` only); `:775-782` (`build_record` -> `rehearsal_disclosure`); `:186-223` (KeyError on a malformed identity; `_prove` "changed after the rehearsal without a commit")

**Issue:** The identity under `data/` is gitignored. A malformed, truncated or foreign identity passes the real-root preflight. The MPS run then completes, and only `emit` hits `KeyError` or `SystemExit` in `rehearsal_disclosure`. Recovering the record then means hand-restoring a gitignored file after the run, or changing the driver after launch, which would show in `modules_changed_since_launch`. 38-08 Task 2 step 5 compares the identity with the SUMMARY copy by hand, so the real run is covered by procedure. Hence a WARNING.

**Experiment (run):**
```
.venv/bin/python -c "import sys; sys.path[:0]=['scripts','src']; import phase38_rank as r; r.rehearsal_disclosure({}, launch_git_sha=r.git_sha(), launch_module_sha256=r.module_sha256())"
# KeyError: 'git_sha'      (preflight's check at :441 is `rehearsal_identity_path().exists()`)
```

**Fix:** In preflight, after `launch_modules = module_sha256()` (`:468`), compute the disclosure once on the real root. It only reads git and writes nothing, and it turns the post-run refusals into pre-launch ones. It also mechanises most of Task 2 step 5.
```python
if _is_real(root):
    rehearsal_disclosure(
        _load(rehearsal_identity_path()), launch_git_sha=launch_sha, launch_module_sha256=launch_modules
    )
```

## Info

### DI-01: `LAUNCH_PATHSPEC` leaves out `artifacts/`, and the run reads the tracked `artifacts/tokenizer.json`

**File:** `scripts/phase38_rank.py:71`, `:257-260` (`phase14_recall.TOKENIZER_PATH` = `artifacts/tokenizer.json`)

This is the mint's WR-03 class. A modified tokenizer is invisible to `refuse_if_dirty`, and the record would name a `git_sha` it cannot be regenerated from. Rafael ruled WR-03 a known limitation because the plan's porcelain check covers it, and 38-08 Task 2 step 1 checks `artifacts` too. Listed only for completeness. A one-line fix is available: `LAUNCH_PATHSPEC = ("scripts", "src", "results", "artifacts")`.

### DI-02: An empty `readings=()` passes the gate vacuously, and `slots=()` silently means all eight slots (rehearsal roots only)

**File:** `scripts/phase38_rank.py:428-433`, `:553`, `:336`

The D-21 I/O-free check accepts `()`, and `all([])` is True, so a rehearsal with no readings reports SCORED. `slots or prereg.SLOTS` turns `()` into the full slot set, which on a rehearsal root reads more of the real result than was asked for. That also feeds DR-02. The real root is forced to `None`/full shape, so the real run is unaffected.

**Experiment (run):** `scoring_plan(slots=(), max_size=8)` gives all 8 slots, and the readings check on `()` gives `True`.

**Fix:** `_prove(readings, ...)`; use `slots if slots is not None else prereg.SLOTS` and `_prove(slots)`.

### DI-03: `report()` writes non-atomically but refuses an existing file

**File:** `scripts/phase38_rank.py:1245-1251`

`out.write_text(...)` interrupted mid-write leaves a torn `results/phase38_rank_report.md`. The write-once refusal then blocks re-rendering until someone deletes the file by hand. Nothing is lost, because the report renders from the committed record. **Fix:** `phase25_run.atomic_write_json` is JSON-only, so write to a sibling `.tmp` and `os.replace`. Mind the ISO-06 `os.replace` census in the tests, or reuse an existing text-atomic helper if one exists.

### DI-04: `reading_model`'s "released on exit" does not hold, because the caller's `as (model, tok)` binding keeps the previous model alive while the next one is built

**File:** `scripts/phase38_rank.py:349-377`; callers `:546`, `:563`, `:656`

`model = None` inside the generator drops only the generator's own reference. `run`'s local `model` still holds it until the next `with` rebinds it, which happens after the new model is loaded. So two models are resident at each reading boundary, and `gc.collect()` / `torch.mps.empty_cache()` free nothing. This is harmless at ~15M parameters.

**Experiment (run):** a weakref through the same contextmanager shape prints `after exit, previous model alive: True`.

**Fix:** add `del model, tok` after each `with` block, or correct the docstring.

### DI-05: `MODULES` and D-20 leave out code and inputs the run executes or reads

**File:** `scripts/phase38_rank.py:74-86`, `:296-320`

`src/personacore/lora.py` (`adapter_disabled`, `load_adapter_weights`), the model code, `phase25_run.py` and `phase14_factset.py` are not hashed. Neither is the base checkpoint `checkpoints/convbase_slim.pt`, which is gitignored and so invisible to `refuse_if_dirty`. D-20 specifies only the adapters and `ordered_prefix`, so this conforms. The 64-cell gate is the de facto check on the base. Same class as the mint's IN-02. **Fix:** optionally add the base checkpoint's sha256 to `reconstruction` (descriptive), and list the src modules in `MODULES`.

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Second review resolution (Rafael's ruling at the 38-08 review checkpoint, 2026-10-04)

"reviewed — nothing to fix." DR-01, DR-02, DR-03 and DI-01..DI-05 (all eight) are known limitations. No driver
or sizes-file change after the 38-07 rehearsal beyond 1e68330, so no second rehearsal is run (DR-01/DR-02
cannot arise). DR-03 is covered at 38-08 Task 2 by calling `rehearsal_disclosure` on the real identity file
(read-only) before the launch.
