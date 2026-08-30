# Phase 24: Adversarial Extraction-Aware Training + the Held-Out Attack Family — Research

**Researched:** 2026-08-30
**Scope:** ONE open question (the v4.0 mask-fraction operating point) + the Nyquist Validation Architecture. Nothing else — D-01…D-13 are locked and were not re-opened.
**Confidence:** HIGH (every figure below is a measurement taken at HEAD this session; none is inherited)

---

## User Constraints (from CONTEXT.md)

`24-CONTEXT.md` carries thirteen LOCKED decisions (D-01…D-13, including the dated 2026-08-30
correction inside D-03 and the D-13 continuation). They are settled and are **not** restated,
re-derived or re-litigated here. Claude's Discretion areas (template module location, grid point
count/spacing, permutation form, `contains_refusal` signature, test-module split) are likewise
left to the planner. Deferred ideas: none captured; two declared residues stand.

---

## Mask-Fraction Operating Point (v4.0 real arm)

### The premise in the open question is wrong, and that is the first finding

The question states the operating point is "reported at `scripts/teach_persona.py:2225`". Measured:

- `scripts/teach_persona.py:2225` lives inside `_arm_rows` (`:2192`) [VERIFIED: `awk` over the file].
- `_arm_rows` has **exactly one caller**: `write_calibration_report` at `:2348` [VERIFIED: `grep -n "_arm_rows("` → two hits, the def and `:2348`].
- `write_calibration_report` is driven only by `run_calibration` (`:2545`), which loops over
  `CAL_ARMS = ("cal_first_person", "cal_first_person_replay", "cal_second_person")`
  (`scripts/teach_persona.py:1960`) [VERIFIED: read `:2545-2566`].

**Line 2225 is therefore structurally unreachable for any v4.0 arm.** It renders the three
calibration arms and nothing else — which is exactly where the 0.3426 / 0.3854 / 0.3778 figures come
from (`results/phase14_calibration_results.json:28,94,160`) [VERIFIED: grep].

**Those three v3.0 figures were NOT used as the answer, were not substituted for the v4.0 arm, and
appear in this document only to be excluded.**

### Where a v4.0 arm's mask fraction actually goes

| Site | What it emits | Persisted? |
|---|---|---|
| `scripts/teach_persona.py:1063` | `bins provenance: … mask_fraction={:.4f}` | **stdout only** |
| `scripts/teach_persona.py:1730` | `run provenance: … mask_fraction={:.4f}` | **stdout only** |
| `scripts/teach_persona.py:877-878` | `mask fraction: mean/min/max` (`sanity_check`) | **stdout only** |
| `scripts/teach_persona.py:2225` | the report table row | CAL arms only |

`grep -rn "mask_fraction" --include="*.json"` returns **exactly two** files: the golden fixture
`tests/fixtures/golden_build_bins_v2.json:33` and `results/phase14_calibration_results.json`
(the v3.0 cal arms) [VERIFIED: grep]. `results/phase23_control_floor.json` and
`results/phase21_multiplicity.json` do **not** carry it.

> **Answer to "is it emitted?": NO — no committed record holds a v4.0 arm's mask fraction.**
> It is recoverable two ways, both of which were executed below. It survives incidentally as prose
> in `.planning/phases/23-…/23-07-SUMMARY.md:146` (`mask_fraction=0.3218`), which is a run log
> quoted into a summary, not a machine-readable record.

### The measurements

**Method A — read the committed on-disk bins** (`np.memmap(dtype=uint8).mean()`):

```
persona_dp_n8_train    tokens= 8,449  scored= 2,719  mask_fraction=0.321813
persona_dp_n64_train   tokens=80,897  scored=28,128  mask_fraction=0.347701
persona_real_train     tokens=20,036  scored= 8,065  mask_fraction=0.402525
```

**Method B — rebuild from source** (`arm_spec` → `render_episodes(fs.TAUGHT_FAMILY_IDS)` →
`build_bins(..., align_facts=None)`, seed 1337, frozen tokenizer, written to scratchpad):

| arm | pack | facts | episodes | tokens | teaching | **mask_fraction** | mean | min | max |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `dp_n8` | **FLAT** | 8 | 176 | 7,581 | 7,581 | **0.358660** | 0.370233 | 0.188406 | 0.571429 |
| `dp_n64` | **FLAT** | 64 | 1,408 | 72,093 | 72,093 | **0.390163** | 0.400220 | 0.188406 | 0.633333 |
| `real` | FLAT | 10 | 220 | 20,036 | 10,018 | 0.402525 | 0.381004 | 0.188406 | 0.600000 |

Method B's `real` row reproduces Method A's on-disk `real` digit-for-digit (0.402525), which
validates the rebuild methodology against a recorded artifact rather than asserting it.

### Which number is the answer — and why the aligned one is a trap

Three candidates exist and the repo's own terminology makes "the v4.0 real arm" ambiguous:

1. **The arm literally named `real` → 0.402525.** But `arm_spec`'s docstring
   (`scripts/teach_persona.py:892-894`) calls its `LOCKED_FACTS + SOFT_TIER_FACTS` composition
   "a RECORDED **v3.0** composition whose bins are committed evidence" [CITED]. 10 facts,
   `replay_ratio = 1.0`. **Not the v4.0 arm.**
2. **The recorded v4.0 arms `dp_n8` / `dp_n64` → 0.321813 / 0.347701.** These are the numbers the
   run logs actually printed. They are packed **fact-aligned**, and `_build_aligned_bins`
   (`:645-650, 661-663`) pads each fact shard to `ceil(tokens/BLOCK_SIZE)` windows with
   `mask = 0`, plus a `mask = 0` label-shift tail. `dp_n8` carries **867 pad tokens**
   (8,449 − 7,581 − 1) [VERIFIED]. The aligned fraction is **depressed by padding**.
3. **The FLAT pack of the same clean episodes → 0.358660 (n=8) / 0.390163 (n=64).**

**#3 is the answer D-05 needs.** D-08's structural finding (`:965-968, :1005` — `aligned = arm in
DP_ARMS`, `DP_ARMS` a literal closed 2-tuple at `:270`) puts the adversarial arm on the **flat**
packer. Its `adversarial_ratio = 0.0` control is therefore the flat number, **not** the aligned
0.3218/0.3477. Using the aligned figure would understate the baseline by ~0.037 and, worse, would
model a padding term the adversarial arm does not have. `build_bins`' flat branch
(`:485-706`) concatenates episodes with **zero padding** [VERIFIED: read].

> **THE OPERATING POINT: `adversarial_ratio = 0.0` → 0.358660 at n=8, 0.390163 at n=64.**

### Band bounds and headroom

`MASK_FRACTION_BAND = (0.15, 0.95)` — `scripts/teach_persona.py:127` [VERIFIED].
Enforced by `_prove_floor_and_band` (`:528`), `SystemExit` at **BUILD** time, checked on
`float(mask_all.mean())` — the **aggregate**, not per-episode (`:549`) [VERIFIED: read].

> Per-episode `mask_fraction_min = 0.188406` sits only 0.038 above the floor at every arm. That is
> **not** a hazard: the guard never sees a per-episode value. Stated so the planner does not
> mis-tune against it.

| Extreme (D-09) | n=8 | n=64 | Distance to floor 0.15 |
|---|---:|---:|---|
| `adversarial_ratio = 0.0` | 0.358660 | 0.390163 | +0.2087 / +0.2402 |
| `adversarial_ratio = 1.909` | *function of template length* | *function of template length* | see below |

The upper bound 0.95 is unreachable on this axis — D-05's own reasoning (both effects push down) is
confirmed by the measurement: adversarial episodes add a long unmasked prompt and a short masked
answer, so `frac` is monotonically decreasing in `adversarial_ratio` for any `L` below the current
operating point's implied per-episode ratio. **Only the 0.15 floor binds.**

### The D-05 calibration: exact headroom at the upper extreme

Attack-corpus measurement, `results/phase18_corpus.json`, `core_taught` only, the three D-10
trained families (A1-mild + A1-aggressive + A3) [VERIFIED: direct read of the JSON this session]:

```
A1-mild        n=112  mean= 44.45  total= 4,978
A1-aggressive  n=112  mean= 69.66  total= 7,802
A3             n=112  mean=118.52  total=13,274
                                   ------------
trained pool: 336 episodes, 26,054 prompt tokens
```

`prompt_ids` is `build_recall_prompt` output — `<|system|>[persona]<|user|>q<|assistant|>`, **all
mask=0** (`src/personacore/dialogue/serialize.py:80-88, 93`) [VERIFIED: read]. So an adversarial
training episode contributes `len(prompt_ids) + L` tokens of which **`L` are scored**, where
`L = refusal-answer content tokens + 1` (the final eos is mask=1, `serialize.py:88`).

Let `L` = scored tokens per adversarial episode. At `adversarial_ratio = 1.909` (= 336/176):

```
n=8   frac(L) = (2,719  + 336·L) / ( 33,635 + 336·L)      336 episodes, pool ×1
n=64  frac(L) = (28,128 + 2688·L) / (280,525 + 2688·L)    2,688 episodes, pool ×8
```

| L (scored tok/refusal) | n=8 `frac` | n=64 `frac` | verdict at n=8 |
|---:|---:|---:|---|
| 7 | **0.1409** | 0.1568 | **SystemExit** |
| 8 | **0.1489** | 0.1643 | **SystemExit** |
| 9 | 0.1567 | 0.1717 | ok, borderline |
| 12 | 0.1792 | 0.1931 | ok |
| 15 | 0.2006 | 0.2133 | ok |
| 20 | 0.2339 | 0.2450 | ok |
| 25 | 0.2645 | 0.2741 | ok |
| 30 | 0.2928 | 0.3012 | ok |

**Critical thresholds (exact):**

| target `frac` | min L at n=8 | min L at n=64 |
|---|---:|---:|
| 0.15 (the band floor) | **8.15 → 9** | 6.11 → 7 |
| 0.20 | 14.91 → 15 | 13.01 → 14 |
| 0.25 | 22.58 → 23 | 20.83 → 21 |
| 0.30 | 31.34 → 32 | 29.78 → 30 |

**Three consequences for the planner:**

1. **The worst corner is `(n=8, ratio 1.909)`, not n=64.** D-05 says "measure at BOTH extremes";
   under D-07 the same grid runs at both capacities, so there are **four** corners
   (2 capacities × 2 ratios) and the binding one is n=8/1.909. n=64's larger clean bin *dilutes*
   the attack pool's unmasked prompts relative to its own scored mass. Measure all four; pin
   against n=8.
2. **The floor is real but not tight for any plausible D-01 template.** An illustrative slot-specific
   value-free refusal of the D-01 shape (`"I will not share my {slot}."`, encoded through the frozen
   production tokenizer against all 11 `fs.SLOT_FORMS` keys) measures **17–28 scored tokens**
   [VERIFIED: measured this session]. That lands the worst corner at **0.214–0.282** — comfortably
   inside, ~0.06–0.13 above the floor. *This template text is a length probe, not a proposal:
   D-01's exact wording is the planner's.*
3. **Headroom, stated as the number D-05 asked for:** at the worst corner, a template of ≥ 9 scored
   tokens clears the band and every template ≥ 15 clears it with ≥ 0.05 absolute margin. The
   *danger zone is L ≤ 8* — reachable only by a terse generic refusal, which D-01 already rejects.

**Planner dependency to close before pinning:** `arm_spec` must return `replay_ratio = 0.0` for the
adversarial arm. The `real` arm's `replay_ratio = 1.0` bakes ~10k replay tokens into the bin and
moves `frac` from 0.359 to 0.403 — a non-zero ratio would invalidate every number in this section.

**Command that reproduces all of the above** (~4 s, CPU, no GPU, no training):

```bash
.venv/bin/python -c '
import sys; sys.path.insert(0,"scripts")
import teach_persona as tp, phase14_factset as fs, pathlib
tp.seed_everything(tp.SEED); tok = tp.from_json(tp.TOKENIZER_PATH)
out = pathlib.Path("/tmp/maskfrac"); out.mkdir(exist_ok=True)
for arm in ("dp_n8","dp_n64"):
    facts, sp, rr = tp.arm_spec(arm)
    eps = tp.render_episodes(facts, fs.TAUGHT_FAMILY_IDS, second_person=sp)
    st = tp.build_bins(tok, eps, out/f"{arm}.bin", out/f"{arm}_mask.bin", replay_ratio=rr, align_facts=None)
    print(arm, st["episodes"], st["tokens"], round(st["mask_fraction"],6))
print("band", tp.MASK_FRACTION_BAND)'
```

**Bonus — closes declared residue 2 at zero cost.** `DP_ARMS` (`:270`) is a **literal closed
2-tuple** `("dp_n8","dp_n64")` and `build_arm_bins` computes `aligned = arm in DP_ARMS` (`:1005`)
with no prefix matching. Any arm name outside those two literals packs FLAT — including a name
that *starts with* `dp_`. D-08's inference is confirmed as a measurement on the mechanism; the
planner still chooses the name.

---

## Validation Architecture

**Framework:** pytest 8.x, `testpaths = ["tests"]`, `pythonpath = ["."]` (`pyproject.toml:24-26`).
Quick run `pytest -q <files>`; full suite `make test` → `pytest -q`.
**Measured:** `pytest -q tests/test_phase14_scoring.py tests/test_phase21_replay_volume.py` →
**55 passed in 10.56 s** [VERIFIED: run this session]. Well inside a per-commit sampling budget.

**No new test infrastructure is needed.** Every assertion below anchors to a file that already
exists and already runs in CI.

### Requirements → test map

| Req | Behavior asserted | Where the assertion lives | Command | Failure mode |
|---|---|---|---|---|
| **ADVT-01** (SC1) | `build_bins(..., adversarial_ratio=0.0)` writes bins **byte-identical** to v2.0 | `tests/test_phase21_aligned_bins.py::test_build_bins_byte_identity_default_matches_the_v2_golden` — sha256 of both bins + `repr(stats)` vs `tests/fixtures/golden_build_bins_v2.json` (`:200-226`) | `pytest -q tests/test_phase21_aligned_bins.py` | Digest mismatch names the file; the test's own guard distinguishes a **stale fixture** (tokenizer sha drift) from a **code regression** and refuses to let you chase the digest (`:203-210`) |
| **ADVT-01** (SC1, load-bearing half) | `adversarial_ratio` is actually **read**, not a dead kwarg | Sibling of `test_align_facts_is_wired` (`:229`) — the precedent that exists precisely because a byte-identity guard over an unwired kwarg is vacuously green | same | Green-before-wiring = the guard is vacuous. Must be watched RED first. |
| **ADVT-01** (D-02) | No refusal template contains any published value | **New sibling** of `tests/test_phase14_scoring.py::test_no_fact_strings_at_import`, calling the existing `embedded_fact_values(module, forbidden)` (`:367`) with the D-10 lexicon `set(LOCKED_VALUES) \| {f.value for f in GATE_REJECTED_CANDIDATES}`. **Leave the existing `assert len(forbidden) == 10` untouched** | `pytest -q tests/test_phase14_scoring.py` | Substring hit reports `(value, count)` per string, including strings nested in tuples/dicts. **Watched RED then GREEN** (D-02) — the detector has real watched-RED history (RECONCILIATION_A's D-20 pet-name leak) |
| **ADVT-01** (D-10) | A3's `persona=` call site is allowlisted | `tests/test_phase14_scoring.py::` D-21 guard at `:539-559` — `assert with_persona == sorted(PERSONA_ALLOWLIST)`, **hard equality**, AST walk over `scripts/*.py` + `src/**/*.py` | `pytest -q tests/test_phase14_scoring.py` | Adding the call site without the 4th `PERSONA_ALLOWLIST` entry (or vice versa) turns the suite red. `:541` documents the extension path. Also guarded: `assert len(scanned) >= 2` catches a broken glob making the guard green-by-scanning-nothing (`:547`) |
| **ADVT-02** (D-13a) | Trained {A1-mild, A1-aggressive, A3} ∩ held-out {A2} = ∅, on key **`family`** | New named assertion reading `results/phase18_corpus.json`, in the `tests/test_phase18_corpus.py` register (`test_schema_and_reserved_family` `:538` is the shape) | `pytest -q tests/test_phase18_corpus.py` | Any family on both sides fails, naming the family. **Must not be conflated with the `source_family` assertion** |
| **ADVT-02** (D-13b) | Taught {F1,F2,F6} vs held-out {F3,F7,F8,reserved} disjoint, on key **`source_family`** | Second, **separately named** assertion (same or sibling module — Claude's discretion) | same | Verifies *paraphrase* generalization, a distinct property. Corpus already measured disjoint on this key |
| **ADVT-02** (D-13, the correction) | The original `(fact_id, seed_index)` key is **unsatisfiable** and is superseded, not deleted | `.planning/ROADMAP.md:721-724` dated additive continuation; the `tests/test_phase19_correction.py` / `test_phase20_correction.py` register is the precedent | `pytest -q tests/test_phase20_correction.py` (pattern) | Corpus is a full 216-triple cross product, all four families covering all 216 — pairwise overlap 216/216. A test on the old key can only ever be RED |
| **ADVT-03** | Scored-token counts reported **per arm** | `stats["mask_fraction"]`, `stats["tokens"]`, `stats["teaching_tokens"]` are already returned by `build_bins` (`:730-741`) and printed at `:1063`. Phase 24 must persist them into a committed record — **the gap this research found** | assert the record's keys/values in a Phase-24 test module | Today they are stdout-only for every non-CAL arm (see the section above). A report that cannot be re-read from a committed file is not a measurement |
| **ADVT-01/02** (SC4) | `scripts/phase18_extraction.py` is ancestry-guarded and never edited | `tests/test_phase16_prereg.py::test_phase18_prereg_is_frozen_before_every_phase18_result` (`:322`), `PHASE18_PREREG_ARTIFACT` at `:80` | `pytest -q tests/test_phase16_prereg.py` | The pin commit must precede every `results/phase18_*` artifact. Editing the file reddens the ancestry guard **permanently** — no delete-and-re-add undoes it |
| **D-05** (the build-time killer) | Mask fraction stays inside `(0.15, 0.95)` at all four grid corners | `_prove_floor_and_band` (`:528`) `SystemExit`s at **BUILD** time — it is already the enforcement. Add a **cheap CPU test** that builds the bins at `(n=8, 1.909)` and asserts `frac >= 0.15` with margin | `pytest -q tests/test_phase24_*.py` (~4 s per corner, no GPU, no training) | Without the test the failure surfaces as a `SystemExit` **after** the sweep point's compute is spent. With it, the failure is a 4-second red test. This is the whole point of D-05 |
| **D-08** (resume) | Bins rebuild byte-identically after a kill | `build_arm_bins`' rebuild-and-compare (`:1019-1039`) + `tests/test_phase23_resume.py` | `pytest -q tests/test_phase23_resume.py` | A fresh RNG in the interleave permutation drifts a sha256 and the resume raises, naming both digests. The permutation MUST be a pure function of `seed` |
| **D-06** (the shape being avoided) | Volume is not derived from `teaching_tokens` | `tests/test_phase21_replay_volume.py::test_replay_constant_is_not_derived_from_the_corpus` (`:260`) — the precedent D-06 reasons against, left untouched | `pytest -q tests/test_phase21_replay_volume.py` | D-06's episode unit sidesteps it by construction; the test stays green as a regression tripwire |

### Sampling rate

- **Per task commit:** `pytest -q tests/test_phase14_scoring.py tests/test_phase21_replay_volume.py tests/test_phase21_aligned_bins.py` (~15 s)
- **Per wave merge:** `pytest -q tests/test_phase18_corpus.py tests/test_phase16_prereg.py` added
- **Phase gate:** `make test` green before `/gsd:verify-work`

### Wave 0 gaps

- [ ] `tests/test_phase24_*.py` — the D-05 four-corner band check (build-only, no training). **The single highest-value new test in the phase**: it converts a post-compute `SystemExit` into a 4-second red.
- [ ] D-02 sibling guard in `tests/test_phase14_scoring.py` — **watch RED before GREEN**, per D-02.
- [ ] The two D-13 assertions (`family`, `source_family`), separately named.
- [ ] A committed ADVT-03 record carrying per-arm scored-token counts — **nothing persists them today**.
- No framework install needed; no `conftest.py` change needed.

---

## Conflicts With Locked Decisions

None — no investigation finding contradicts D-01 through D-13.

Two **refinements** (not contradictions), recorded so the planner acts on the right corner:

1. **D-05's "BOTH extremes of the grid" under-specifies by 2×.** D-07 locks the same nominal grid at
   both capacities, so the grid has **four** corners. Measured: the binding one is
   `(n=8, ratio 1.909)`, which requires ~2 more scored tokens per refusal than n=64 does
   (9 vs 7 at the floor). D-05's intent — "the worst extreme sits inside the band with real
   margin" — is preserved exactly; only the enumeration widens.
2. **The open question's premise about `:2225` is factually wrong**, but `:2225` appears in the
   *open question*, not in any locked decision. No decision is affected.

---

## Sources

**Primary (HIGH — direct measurement at HEAD, this session):**
- `scripts/teach_persona.py` — `:127` band, `:249-270` `ARMS`/`DP_ARMS`, `:467/485-706` flat `build_bins`, `:528-556` `_prove_floor_and_band`, `:609-741` `_build_aligned_bins`, `:877-878/1005/1019-1063` `build_arm_bins`, `:1730`, `:1960` `CAL_ARMS`, `:2192-2225` `_arm_rows`, `:2348`, `:2545-2566` `run_calibration`
- `src/personacore/dialogue/serialize.py:61-93` — `encode_dialogue` mask semantics, `build_recall_prompt`
- `results/phase18_corpus.json` — 864 rows, per-family `core_taught` prompt-token totals
- `data/persona_{dp_n8,dp_n64,real}_train_mask.bin` — on-disk mask means
- Flat rebuild via `arm_spec` → `render_episodes` → `build_bins(align_facts=None)`, seed 1337
- `tests/test_phase14_scoring.py:360-368, 415-430, 535-562`; `tests/test_phase21_aligned_bins.py:200-235`; `tests/test_phase21_replay_volume.py:260`; `tests/test_phase16_prereg.py:80, 322`; `tests/test_phase18_corpus.py:538`
- `pyproject.toml:24-26`, `Makefile`

**Explicitly excluded (v3.0 — named only to be ruled out):**
- `results/phase14_calibration_results.json:28,94,160` → 0.3426 / 0.3854 / 0.3778.
  **Not used. Not substituted. Not the v4.0 arm.**

**Assumptions Log:** empty. Every figure above is a measurement with a reproducible command.
The only non-measured element is the illustrative refusal string used as a *length probe*, and it
is labelled as such in place.
