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
