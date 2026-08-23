---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 06
subsystem: aligned-loader
tags: [unit-02, d-01, d-02, d-03, d-04, d-05, d-06, run-time-consumption, wave-3, t-21-02, t-21-12, t-21-20, t-21-27, t-21-28, t-21-29, t-21-61, t-21-62]
requires:
  - "21-04 — fact_window_impurities(space='input'), teach_persona.fact_bin_path(), the ragged aligned packer, tests/test_phase21_aligned_bins.py's corpus builder"
provides:
  - "personacore.training.data.get_batch_fact_aligned(bin, mask, fact, block_size, device, *, step, n_facts) -> (x, y, fact_index) — three bins re-opened on EVERY call, INPUT-space purity on the drawn slice only"
  - "personacore.training.data.fact_window_span(fact_ids, fact_index, block_size) -> (start_element, n_windows) — EXPORTED, the ONE place a fact's window range is computed"
  - "tests/test_phase21_aligned_loader.py — N1-N6 mutate-between-calls, the two negative controls, grad_accum conservation, the A5 n_facts assertion"
affects:
  - "21-10 — count_aligned calls fact_window_span rather than re-implementing the window arithmetic (T-21-62)"
  - "21-11 / Phase 22 DPSGD-01 — one micro-step is one privacy record, so the ordinary backward hands back the per-record gradient and vmap stays off the critical path (D-02)"
tech-stack:
  added: []
  patterns:
    - "Run-time consumption is proven by PERTURBING the map and observing the batches change — a structural assertion over the bin file is 21-04's claim and repeating it here would prove nothing new"
    - "The mutation's VISIBILITY (sha256 of all three files) is asserted BEFORE the behavioural assertion, so a page-cache surprise fails naming the cause instead of flaking (assumption A1)"
    - "Every adversarial raise is distinguished by WHICH assertion fired — a fragment unique to that guard plus a fragment asserted ABSENT from the neighbouring guard"
    - "Two negative controls, not one: N5 (unmutated) stops 'a loader that always raises' passing, N6 (token bin mutated) proves WHICH file is read"
key-files:
  created:
    - "tests/test_phase21_aligned_loader.py"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-06-SUMMARY.md"
  modified:
    - "src/personacore/training/data.py"
decisions:
  - "fact_window_span reads window owners with a STRIDED slice (fact_ids[:n_windows*block_size:block_size]) rather than the plan's fact_ids[:-1].reshape(-1, block_size)[:, 0]. Identical on a well-formed bin; on a malformed one the reshape raises numpy's own 'cannot reshape array of size N' which names no bin. The strided form also means this function carries NO second copy of the (len-1) % block_size remainder guard, which lives in fact_window_impurities — one predicate, no drift."
  - "The A5 n_facts assertion counts DISTINCT WINDOW OWNERS (O(n_windows) = 33 elements), not distinct ids over the whole bin (O(corpus) = 8,449). Same discrimination, and it keeps the per-call cost O(batch) as the plan requires of the purity check."
  - "The deliberate-RED restore was ordered AFTER the GREEN commit of both data.py and the test file. The plan's task-2 text places 'git checkout src/personacore/training/data.py' inside the RED cycle; 21-04's SUMMARY records that exact ordering destroying its implementation. Here it was safe only because the GREEN was already committed."
metrics:
  duration: "~40 min"
  tasks_completed: 2
---

# Phase 21 Plan 06: The Fact-Aligned Loader Summary

`get_batch_fact_aligned` draws every window of one fact per micro-step, and the fact map is
proven **consumed at run time** — the batch it hands back changes when the map on disk changes
between two calls in one process, with the token and mask bins proven byte-frozen by `sha256`.

## The Central Claim, Perturbed Rather Than Asserted

The prompt named the failure mode precisely: a test that proves the map EXISTS and is
well-formed while never proving any batch came out of it. That test was not written. What was
written mutates the map and watches the output move.

The evidence is the **deliberate-RED**, which is the only form of the claim that can fail. The
`np.memmap(fact_path, ...)` read was deleted from the loader and the boundaries derived from a
`np.cumsum` of the padded lengths instead — a loader that produces byte-identical batches on a
correct bin and never reads the fact file:

```
x equal : True
y equal : True
fact_index equal: True 0 0
first == second -> True
```

`first == second` under the N4 mutation is exactly "the map is not consumed". Under the real
implementation the same call raises. **Six tests reddened, four stayed GREEN** — and which four
is the informative part:

| Test | Under the cumsum loader | What that records |
|---|---|---|
| `test_fact_map_is_consumed_at_runtime` | **RED** (`DID NOT RAISE`) | the load-bearing discriminator works |
| `test_fact_bin_required_raises_distinguishably[N1/N2]` | **RED** ×2 | the bin can be deleted or truncated unnoticed |
| `test_positional_mutation_raises_input_space_impurity[N3/N4]` | **RED** ×2 | correct offsets over wrong bytes go through |
| `test_n_facts_is_asserted_not_trusted` | **RED** | n_facts is trusted, not asserted |
| `test_valid_bin_never_raises_on_any_fact` | GREEN | a correct-bin test **cannot** separate the two implementations — this is §V.1's "one input class, two implementations" made mechanical |
| `test_grad_accum_steps_equals_n_facts` | GREEN | same; the lot still covers 33 windows |
| `test_n5_unmutated_...` / `test_n6_token_bin_...` | GREEN | controls, correctly insensitive |

Restore sha256 `28ceadc6eb2286a34a3e4e13ca316a830662fede061f99499c8382b433706820`, equal to the
pre-mutation value; `git diff --exit-code src/personacore/training/data.py` returns 0.

## N1-N6, With The Exact Raise Message

Paths abbreviated to `<tmp>/`; every message is verbatim otherwise.

**N1 — fact bin DELETED**
> the fact bin `<tmp>/m_fact.bin` could not be opened ([Errno 2] No such file or directory:
> '`<tmp>/m_fact.bin`') — a fact-aligned draw cannot proceed without it (token bin `<tmp>/m.bin`,
> mask bin `<tmp>/m_mask.bin` were opened). Falling back to positionally-guessed boundaries would
> make grad_accum_steps = n_facts a declaration instead of a property of the data (D-06).

**N2 — fact bin TRUNCATED by 1**
> the three aligned bins are not 1:1: `<tmp>/m.bin` has 8449 elements, `<tmp>/m_mask.bin` has 8449
> and the fact bin `<tmp>/m_fact.bin` has 8448 — all three must match element for element
> (T-11-04 extended from two files to three, D-06 proof 1). A length skew silently mis-attributes
> windows to records.

**N3 — fact bin ROLLED by 1**
> the fact bin `<tmp>/m_fact.bin` is IMPURE on the draw for fact 0: **window 4** carries ids
> [0, 1] — every one of that fact's 4 window(s) must carry only id 0. SC2's 'one window, one fact'
> is FALSE for this draw, so this micro-step is not one privacy record.

Length, id multiset and block remainder are asserted **UNCHANGED** in the test before this fires,
so the message is the only thing that saw the roll. `fact_window_impurities(rolled, 256,
space="target")` is asserted `== []` in the same test — target space is blind to a roll, which is
the second independent reason the draw check is input space.

**N4 — one interior element flipped**
> the fact bin `<tmp>/m_fact.bin` is IMPURE on the draw for fact 0: **window 0** carries ids
> [0, 1] — every one of that fact's 4 window(s) must carry only id 0. …

"on exactly one window" is asserted, not assumed: `message.count("carries ids") == 1`.

**N5 — UNMUTATED (negative control), a separate observation.** Two consecutive calls, no
mutation: all three `sha256` unchanged, `torch.equal` on `x` and on `y`, `fact_index == 0` both
times. Without this a loader that always raised would pass N1-N4.

**N6 — TOKEN bin mutated, fact bin untouched (the wrong-file control), a separate observation.**
One token flipped at element 128: `sha256` of the fact bin and mask bin unchanged, `fact_index`
**unchanged at 0**, `x` **differs**, shape unchanged. This is what proves the guard reads the
fact bin and not the token bin.

**A5 class — `n_facts` asserted, not trusted** (an extra beyond N1-N6, the plan's fifth
validation clause):
> the fact bin `<tmp>/m_fact.bin` carries 8 distinct fact id(s) [0, 1, 2, 3, 4, 5, 6, 7] across
> 33 window(s), but n_facts=9 was declared. Content purity alone does not pin n_facts, so the
> loader asserts both — otherwise grad_accum_steps = n_facts would bound a lot the bin does not
> contain.

## `(start, k)` Per Fact, Observed Through The Loader

Read off `fact_window_span` and cross-checked against `x.shape[0]` returned by the loader — not
off the packer's stats:

| fact_index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| `start` | 0 | 1024 | 2048 | 3072 | 4096 | 5120 | 6400 | 7424 |
| `k` | 4 | 4 | 4 | 4 | 4 | **5** | 4 | 4 |

`(4,4,4,4,4,5,4,4)` — **equal to D-01's `windows_per_fact`**, and to `stats["windows_per_fact"]`.
Every fact index returned normally: the input-space draw check does **not** fire on a valid bin.

## The Target-Space Row Count, On That Same Correct Bin

`fact_window_impurities(fact_ids, 256, space="target")` = **`[3, 7, 11, 15, 19, 24, 28]`** —
**7 rows = `n_facts - 1`**. Recorded inside `test_valid_bin_never_raises_on_any_fact` itself, so
the test states WHY the draw check is input-space rather than merely that it is.

**Nothing reddened and nothing was loosened.** The `space="input"` default is untouched, and the
`+1` label-shift tail is passed on every draw (`facts[start : start + k*256 + 1]`) — a bare
`k*256` slice would raise spuriously, since `(1024 - 1) % 256 == 255`.

## `grad_accum_steps == n_facts`, Observed From The Loop

`fact_index` sequence over one lot: **`[0, 1, 2, 3, 4, 5, 6, 7]`** — no repeat, no gap. Step 8
wraps to **0**. Batch rows summed across the lot: **33 = `stats["n_windows"]`**, and the set of
window rows covered is exactly `range(33)` with no duplicate. The count comes from the loop's
actual returns, never from a bin's shape.

## Memmap Coherence (Assumption A1) On This Platform

**A1 HELD.** Darwin 25.5.0, Python 3.11.15, this venv's numpy: a freshly-opened
`np.memmap(path, mode="r")` in the same process after an on-disk `tofile` returns the NEW bytes —
demonstrated by N3/N4 raising at all, and by N4's byte-identical restore returning call 2 to
call 1's exact tensors. The sha256-before-behaviour ordering is in the test regardless, so a
Linux-CI page-cache surprise would fail naming the cause rather than flaking.

## Plan vs Code Fidelity

Two mismatches, reported rather than silently adapted.

**1. `fact_window_span`'s owner read is a strided slice, not the plan's `reshape`.** The plan
specifies `owners = fact_ids[:-1].reshape(-1, block_size)[:, 0]`. That form has a hidden
precondition — the reshape raises numpy's own `cannot reshape array of size N` on any bin whose
`(len - 1) % block_size != 0`, an error naming no bin and no remainder. Adding a remainder guard
here would put a **second copy** of `fact_window_impurities`' length contract in the file, which
is the drift this phase has spent two plans avoiding. `fact_ids[: n_windows*block_size :
block_size]` is identical on a well-formed bin, needs no precondition, and leaves exactly one
copy of the remainder guard. See Decisions.

**2. The plan's own `<interfaces>` line anchors were verified and are CORRECT this time.**
`data.py:110-111` (both memmaps re-opened), `:112-116` (the raise register), `:117-124` (the +1
shift), `:125` (`y[m == 0] = -100`), `:126` (return), `serialize.py:81` (`emit([system_id], 0)`),
`gpt.py:212` (`F.cross_entropy` default `reduction="mean"`) — **zero stale anchors**, matching
21-04 and unlike 21-01/21-03. Recorded because the phase has measured both outcomes.

Two further notes that are not mismatches but are worth carrying forward:

- **`21-RESEARCH.md` §V.1's deliberate-RED sketch prescribes `git stash` for the restore.** That
  is prohibited in this repository's worktree execution — `refs/stash` is shared across
  worktrees. The restore used `git checkout src/personacore/training/data.py` **after** the GREEN
  commit, verified by sha256 and `git diff --exit-code`.
- **§V.1's sketch calls `get_batch_fact_aligned(**bins, step=0)`.** The shipped signature takes
  positional `bin_path, mask_path, fact_path, block_size, device` plus keyword-only `step` and
  `n_facts`, so `**bins` does not apply; the test uses an explicit `_draw` helper. Same class of
  sketch/reality gap 21-05 recorded for §V.4c's `dataclasses.replace`-on-a-NamedTuple.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] The `n_facts` assertion reads window owners, not the whole bin**

- **Found during:** Task 1
- **Issue:** The plan requires the loader to raise when `step`/`n_facts` are inconsistent with the
  observed distinct fact-id count, and separately requires the per-call cost to stay O(batch)
  rather than O(corpus). Read literally, "the observed distinct fact-id count" over the whole bin
  is an 8,449-element scan on every micro-step.
- **Fix:** the distinct count is taken over the 33 **window owners** (`facts[::block_size]`),
  which is the same discrimination at O(n_windows).
- **Files modified:** `src/personacore/training/data.py`
- **Commit:** `8cf30f3`

**2. [Rule 2 — Missing critical functionality] `np.memmap`'s `ValueError` on an empty fact bin is caught alongside `FileNotFoundError`**

- **Found during:** Task 1
- **Issue:** The plan names only the missing-file case. A zero-byte fact bin — the shape a
  half-written build leaves behind — makes `np.memmap` raise `ValueError("cannot mmap an empty
  file")`, which names no bin and would be indistinguishable from an impurity finding to a caller
  matching on `ValueError`.
- **Fix:** both are caught and re-raised in the "could not be opened" register naming
  `fact_path`, with the underlying error preserved via `from exc`.
- **Commit:** `8cf30f3`

No Rule 4 (architectural) decisions arose.

## Verification

| Check | Result |
|---|---|
| `pytest -q tests/test_phase21_aligned_loader.py tests/test_phase21_aligned_bins.py tests/test_masked_batch.py tests/test_phase14_teaching.py` | **68 passed** |
| `pytest -q tests/test_phase21_aligned_loader.py -k consumed_at_runtime` (`21-VALIDATION.md:71`) | passed |
| `pytest -q tests/test_phase21_aligned_loader.py -k grad_accum` (`21-VALIDATION.md:70`) | passed |
| `pytest -q tests/test_phase21_aligned_loader.py -k fact_bin_required` (`21-VALIDATION.md:72`) | passed (2) |
| `pytest -q tests/test_phase21_aligned_loader.py -k valid_bin_never_raises` | passed |
| `git diff --numstat src/personacore/training/data.py` (pre-commit) | **180 added / 0 deleted** — `get_batch_memmap_masked` byte-unchanged |
| `git status --porcelain data/` | empty |
| `git ls-files 'results/phase21_*'` | empty |
| `git diff --exit-code scripts/mitigation_gate.py scripts/mitigation_unit.py scripts/phase18_extraction.py` | 0 — frozen pins byte-unchanged |
| `ruff check . && ruff format --check .` | All checks passed, 182 files formatted |
| `.planning/STATE.md` / `ROADMAP.md` | byte-unchanged (worktree mode — orchestrator owns them) |

**No bare `pytest -q` was run**, per the plan's `<verification>` note and `21-VALIDATION.md:47,52`:
same-wave plans 21-07 and 21-08 hold live working-tree canaries and 21-08 is deliberately
reddening `tests/test_phase21_replay_volume.py`. The full suite belongs at wave close.

## Known Stubs

None. Both functions are fully implemented and exercised against the real 8-fact geometry at
`block_size = 256`; no placeholder values, no empty defaults reaching a caller.

## Threat Flags

None. This plan adds no network endpoint, no auth path and no new file-access pattern: it reads
one additional bin beside two an existing sibling function already reads, at a path the caller
supplies and `fact_bin_path()` derives.

## Commits

| Commit | Task | Content |
|---|---|---|
| `8cf30f3` | 1 | `get_batch_fact_aligned` + `fact_window_span` — three bins re-opened per call, INPUT-space draw check, four distinguishable raise classes |
| `ef2dd4a` | 2 | `tests/test_phase21_aligned_loader.py` — N1-N6, both negative controls, grad_accum conservation, the A5 assertion |
