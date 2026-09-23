---
phase: 21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus
plan: 02
subsystem: golden-fixtures
tags: [unit-02, unit-06, golden-fixture, pre-edit-capture, byte-identity, wave-1, t-21-05, t-21-15, t-21-16, t-21-17]
requires: []
provides:
  - "tests/fixtures/golden_build_bins_v2.json — the v2.0 build_bins byte-level baseline, captured from a git-clean tree at a18f675 in which scripts/teach_persona.py is unedited"
  - "tests/fixtures/golden_render_family_v2.json — the v2.0 render_family baseline over ALL 8 FAMILY_IDS x 10 facts in BOTH registers, captured pre-edit"
  - "scripts/phase21_golden_capture.py — the one-time capture driver whose FIRST act is a git-cleanliness refusal over both captured sources"
  - "A measured determinism proof for both fixtures: identical digests across four PYTHONHASHSEED values and two independent processes"
affects:
  - "21-04 — build_bins(..., align_facts=None) asserts byte-identity against golden_build_bins_v2.json"
  - "21-05 — render_family(..., forms=None) asserts byte-identity against golden_render_family_v2.json"
  - "Any consuming test must read meta.serialization AND meta.order from the fixture rather than retyping them"
tech-stack:
  added: []
  patterns:
    - "A pre-edit constraint is worth nothing as a promise: the capture script refuses on non-empty `git status --porcelain` over the files it freezes, at module scope, ahead of the imports it would otherwise capture"
    - "Prove determinism, do not assert it — vary PYTHONHASHSEED and re-derive from an INDEPENDENT script, so the fixture's own meta is shown sufficient to reproduce it"
    - "Record every free choice into the fixture (serialization kwargs AND iteration order), and drive the capture from the recorded constant so meta cannot drift from what was hashed"
    - "A byte-identity fixture across two variants must assert the two variants DIFFER at capture time, or it is a guard that cannot fail"
key-files:
  created:
    - "scripts/phase21_golden_capture.py"
    - "tests/fixtures/golden_build_bins_v2.json"
    - "tests/fixtures/golden_render_family_v2.json"
    - ".planning/phases/21-the-privacy-unit-the-dp-data-path-and-the-n-64-corpus/21-02-SUMMARY.md"
  modified: []
decisions:
  - "meta.order was ADDED beyond the plan's spec. The plan required meta.serialization 'so the consuming test cannot drift from the capture' but named only the json.dumps kwargs. The iteration order is the same class of drift risk and is a FREE choice — the plan specifies family-outer/fact-inner, which is the TRANSPOSE of render_episodes:250-252 (fact-outer). A consuming test that assumed the render_episodes order would compute a different digest over identical behaviour and report it as a regression"
  - "golden_build_bins_v2.json was re-captured during task 2 so both fixtures share one captured_at_sha. The diff is exactly one line; every hash and stat reproduced byte-identically across two independent runs at two different commits, which is itself the strongest reproducibility evidence in this plan"
  - "The strict-ancestor criterion vs 21-04/21-05 is recorded as VERIFIABLE-AT-WAVE-2, not as verified. Those commits do not exist in this worktree; claiming it now would be an over-claim"
metrics:
  duration: "~35 min"
  tasks_completed: 2
---

# Phase 21 Plan 02: v2.0 Golden Fixture Capture Summary

Both v2.0 golden fixtures captured from a mechanically-verified git-clean, pre-edit tree, with
determinism proven across four hash seeds rather than assumed.

## What Was Built

`scripts/phase21_golden_capture.py` — a one-time capture driver, deliberately outside the
`scripts/mitigation_*.py` glob (whose `{pathlib, sys, erasure_gate}` import ceiling puts `json` and
`subprocess` out of reach). Its **first act at module scope**, ahead of the `teach_persona` /
`phase14_factset` imports, is `_refuse_if_dirty()`. There is no code path that reaches the capture
with a dirty tree.

## The Captured Numbers

**Both fixtures: `captured_at_sha = a18f6751abf4d5d9ae076ae1f7027118afbe9538`**

### `tests/fixtures/golden_build_bins_v2.json`

| Field | Value |
|---|---|
| `token_bin_sha256` | `91c2549388079c3da2d5888706ba6b80f70383f320112ae768f6a78372f90fac` |
| `mask_bin_sha256` | `4a674423ec9412fc6a302adcc419faa98d78a1e8b8c00107b13aeb864c15061f` |
| `token_bin_bytes` | 20,036 |
| `mask_bin_bytes` | 10,018 (`token == 2 * mask`, uint16 ids vs uint8 mask over a 1:1 pair) |
| `meta.tokenizer_sha256` | `e82e8e83d621075c7c46d222f52d87c56c79329c137df8f5d3241255eda863e0` |
| `meta.replay_ratio` | `0.0` |
| episodes / tokens | **220 episodes / 10,018 tokens** |

`stats_repr` in full:

```
{'episodes': 220, 'tokens': 10018, 'teaching_tokens': 10018, 'replay_tokens': 0,
 'replay_ratio': 0.0, 'episode_len_mean': 45.53636363636364, 'episode_len_min': 24,
 'episode_len_max': 84, 'mask_fraction': 0.37232980634857255,
 'mask_fraction_mean': 0.38100409967870663, 'mask_fraction_min': 0.18840579710144928,
 'mask_fraction_max': 0.6}
```

### `tests/fixtures/golden_render_family_v2.json`

| Register | sha256 | rows |
|---|---|---|
| `first_person` | `5f2b67ee52b0383cdb5f269231e4616ee628093d70a4159980c55fd6090385d0` | 310 |
| `second_person` | `5e051c8fe8563f1ee08774b379940b4866c3ef49b216e65535d7f74b3f087612` | 310 |

8 families x 10 facts. `meta.tokenizer_sha256` deliberately **omitted** — `render_family` never
touches the tokenizer, and pinning an irrelevant input would invite a false STALE reading later.

## Evidence

### D-01 independently confirmed from the code, not the document

D-01 records **7,581 tokens** for the 8 `LOCKED_FACTS` through the 5 taught families, and separately
records the soft tier at `cand_color_chartreuse` 1,275 + `cand_food_marzipan` 1,162 = 2,437.

```
7,581 + 2,437 = 10,018  ==  measured stats['tokens'] = 10,018   ✓ exact
```

Row counts agree too: 176 / 8 = 22 rows per fact (D-01), and 220 / 10 = 22. The plan's `<interfaces>`
block predicted the totals would be LARGER and instructed "record whatever is measured, do not force
a number" — followed; nothing was forced.

### Determinism measured, not assumed

`TAUGHT_FAMILY_IDS` is a `frozenset[str]`, whose iteration order varies with `PYTHONHASHSEED`. The
hazard is **live**, and was observed rather than reasoned about:

| `PYTHONHASHSEED` | `list(TAUGHT_FAMILY_IDS)` | `token_bin` sha256 |
|---|---|---|
| 1 | `['F6', 'F1', 'F4', 'F5', 'F2']` | `91c2549…` |
| 99991 | `['F1', 'F6', 'F5', 'F2', 'F4']` | `91c2549…` |

Iteration order genuinely differs; both runs reproduce the committed sha256 **and** the full
`stats_repr` exactly, because `render_episodes:251` applies `sorted(family_ids)`. The render digests
were likewise re-derived under `PYTHONHASHSEED=7` and `424242` — identical both times, and from an
**independent script** that read nothing from the capture driver, which confirms `meta` alone is
sufficient to reproduce the digest.

### Both refusals exercised, not merely written

| Refusal | Observed |
|---|---|
| re-run (`tp.refuse_if_exists`) | exit 1, message names **both** fixture paths and the delete command |
| dirty tree (`_refuse_if_dirty`) | with a trailing comment appended to `scripts/teach_persona.py`: exit 1, names `scripts/teach_persona.py`, and fired **before** `refuse_if_exists` — proving the ordering. Fixture sha256 `4c9e58ee…` **unchanged** by the aborted run, so nothing was written |

Restored with `git checkout -- scripts/teach_persona.py`; `git diff --exit-code` returns 0.

### Verification block

| Check | Result |
|---|---|
| `git status --porcelain -- scripts/teach_persona.py scripts/phase14_factset.py` | empty |
| `git diff --exit-code ef2839f HEAD -- scripts/teach_persona.py scripts/phase14_factset.py` | 0 — byte-unchanged by this plan |
| `git diff --exit-code scripts/mitigation_gate.py scripts/phase18_extraction.py` | 0 |
| `pytest -q tests/test_package.py tests/test_phase14_teaching.py` | 41 passed |
| VALIDATION quick command | **62 passed in 3.56s** — matches 21-VALIDATION.md's stated 62 / 3.45s |
| SC5 guard set (8 files) | **334 passed, 2 skipped in 39.72s** |
| `ruff check . && ruff format --check .` | All checks passed, 177 files formatted |
| `grep -c dialog_train tests/fixtures/golden_build_bins_v2.json` | **0** — no `data/` dependency |

## Plan vs Code Fidelity

**All 17 line anchors in the plan's `<interfaces>` block verify against the source at `ef2839f`.**
Recorded explicitly because this repo has a measured history of the opposite (nine consecutive
Phase-19 plans naming paths the code refused; 21-01 falsified three of its own claims hours ago).
Verified individually: `teach_persona.py` `:91 :92 :99 :100 :123 :236 :247 :256 :338 :441` and
`phase14_factset.py` `:313 :390 :410 :763 :775 :816 :817 :824`. **Zero mismatches. Nothing had to be
adapted, and nothing was forced through.**

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `meta.order` added to the render fixture**

- **Found during:** Task 2
- **Issue:** The plan requires `meta.serialization` to carry the literal `json.dumps` kwargs "so the
  consuming test cannot drift from the capture" — but names only the kwargs. The **iteration order**
  is the same class of drift risk and is a free choice. The plan specifies
  `for fid in sorted(FAMILY_IDS) for fact in facts` (family-outer), which is the **transpose** of
  `render_episodes:250-252` (fact-outer, `teach_persona.py:250-251`). Both cover the same set, so
  the digests are equally valid — but a consuming test that reasonably assumed the `render_episodes`
  order would compute a different digest over **identical behaviour** and report it as a regression.
- **Fix:** added `RENDER_ORDER` and emitted it as `meta.order`, with the transpose called out in a
  comment. The capture drives its own `json.dumps` call from the recorded `RENDER_SERIALIZATION`
  constant, so `meta` cannot drift from what was actually hashed.
- **Files modified:** `scripts/phase21_golden_capture.py`
- **Commit:** `4e2ce1a`

### Process Notes

**`golden_build_bins_v2.json` was re-captured during task 2.** Task 1 committed it at `ef2839f`;
task 2 deleted both fixtures and re-ran so both carry `captured_at_sha = a18f675`. This is the flow
the script's own refusal message prescribes. The resulting diff is **exactly one line**
(`captured_at_sha`) — every hash and every stat reproduced byte-identically across two independent
runs at two different commits. Both SHAs are pre-edit for the captured sources, so the fixture's
"pre-edit" property holds at either.

## Not Claimed

The plan's task-2 acceptance criterion *"Both fixtures are committed in a commit that is a strict
ancestor of every commit produced by plans 21-04 and 21-05"* is **verifiable at wave 2, not now.**
Those commits do not exist in this worktree. What IS verified: both fixtures live at `4e2ce1a`, the
final commit of this wave-1 plan, and `depends_on: []` means nothing in wave 1 precedes it. Verify
after the wave-2 merge with:

```bash
git merge-base --is-ancestor 4e2ce1a <21-04-commit>
git merge-base --is-ancestor 4e2ce1a <21-05-commit>
```

## Known Stubs

None. Both fixtures are fully populated with measured values; the capture script has no placeholder
branch.

## Threat Flags

None. This plan adds no network endpoint, no auth path, no schema change and no new file-access
pattern beyond reading two already-tracked source files and writing two fixtures under `tests/`.

## Commits

| Commit | Task | Content |
|---|---|---|
| `a18f675` | 1 | capture script + git-cleanliness refusal + `golden_build_bins_v2.json` |
| `4e2ce1a` | 2 | `render_family` emitter + `golden_render_family_v2.json` + single-SHA re-capture |
| `b13b5a8` | — | this SUMMARY |

## Self-Check: PASSED

All four claimed files exist on disk; all three code/fixture commits present in
`git log ef2839f..HEAD`; working tree clean; `.planning/STATE.md` and `.planning/ROADMAP.md`
byte-unchanged (`git diff --exit-code ef2839f HEAD` returns 0) as required in worktree mode.
