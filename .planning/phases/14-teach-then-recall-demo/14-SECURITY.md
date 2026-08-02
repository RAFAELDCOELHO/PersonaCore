---
phase: 14
slug: teach-then-recall-demo
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-02
---

# Phase 14 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Scope note: this phase ships offline research drivers (a fact-set gate, a teaching run, a
scoring harness) plus one **localhost-only Gradio demo**. There is no authentication, no
multi-tenant data, and no remote surface — `share=False` binds 127.0.0.1 and the single-user
assumption is stated in the demo's module docstring. The live threat classes are **Spoofing of
the novel claim** (a fact value reaching the model's context, or a "memory off" that is still
on), **Tampering** (recorded evidence overwritten; thresholds chosen after seeing numbers; base
weights silently moving during teaching), **Repudiation** (provenance of pre-registered rules
and reported numbers), **Information Disclosure** (fact values leaking into the demo process;
network egress from a demo whose whole thesis is on-device), **EoP** (pickle deserialization via
`torch.load`), and **DoS** (unbounded generation loops). ASVS L1 is the appropriate bar.

Register authored at plan time — this audit **verifies each declared mitigation exists in the
implemented code**, and does not scan for new/unlisted threats.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| caller → `build_recall_prompt` | The sole gate deciding what enters the model's context; the clean-room claim rests on it | question string → prompt ids |
| caller → `generate_text_from_ids` | `max_new_tokens` crosses from a Gradio slider; `prompt_ids` from the harness | int budget + id list |
| disk → gate/teaching drivers | `checkpoints/convbase_best.pt` deserialized with `weights_only=False` | tensors + pickled optimizer/RNG/numpy objects |
| disk → harness/demo | `convbase_slim.pt` + `persona_adapter.pt` — the two SHAREABLE artifacts | tensors + primitive containers only |
| teaching process → recall process | The adapter file on disk is the only thing crossing; this IS the clean-room boundary | LoRA A/B tensors + fingerprint trio |
| taught corpus → held-out claim | Every token in the bin is a potential leak of the never-seen split | uint16 ids + uint8 mask |
| locked fact values → demo process | The values must never enter this process (D-16) | an INTEGER (`RECALL_MAX_NEW_TOKENS`), never the answers |
| served page → third-party origins | The page must instruct the browser to fetch nothing remote | HTML response bytes |
| calibration numbers → locked thresholds | The rule converting them must PRECEDE them | float rates → float thresholds |
| drivers → `results/` | Everything written here ships publicly and is committed evidence | markdown / CSV / JSON |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-14-01 | Spoofing (novel claim) | `build_recall_prompt` | mitigate | One function, ids only; string + token-level absence asserted in CI | closed |
| T-14-02 | DoS | `generate_text_from_ids` | mitigate | `(0, 4096]` guard fires before the loop; no forward pass on rejection | closed |
| T-14-03 | Tampering | `ASSISTANT_ID` resolution | mitigate | Resolved from `SPECIAL_TOKENS`; `grep -c 8186` = 0 on the module | closed |
| T-14-04 | EoP | `torch.load(..., weights_only=False)` | mitigate | Trusted-own-file read + `SECURITY:` docstring in both drivers | closed |
| T-14-05 | Info Disclosure | fact values in public `results/` | mitigate | All values invented; `data/`,`checkpoints/`,`logs/`,`*.pt` gitignored | closed |
| T-14-06 | Tampering / DoS | verdict clobber + UI slider | mitigate | Clobber guard on all 4 report paths; slider `[48, 256]` | closed (see UF-4) |
| T-14-07 | Spoofing (novel claim) | guessability measurement | mitigate | Probes via `build_recall_prompt`; greedy + 3 seeded, quoted verbatim | closed |
| T-14-08 | DoS | probe / recall generation loop | mitigate | 32 / 48 fixed budgets; 7,645 dead ids masked; `stop_ids={8184,8185}` | closed |
| T-14-09 | Tampering | locked constants drifting from report | mitigate | `FACTSET_GATE_SHA` pins the verdict commit; zero runtime report parsing | closed |
| T-14-10 | Spoofing (novel claim) | stale guessability verdict inherited | mitigate | D-07 docstring in the test itself; fresh gated measurement required | closed |
| T-14-11 | Info Disclosure | real personal data in locked set | mitigate | Values invented + pinned away from measured base priors | closed |
| T-14-12 | Spoofing (DEMO-06 claim) | held-out split leakage | mitigate | 3 CI checks + a build-time `SystemExit` on the written bin | closed (see UF-2) |
| T-14-13 | Tampering | mask off-by-one (PITFALLS-14) | mitigate | `encode_dialogue` single source; literal-expectation test; `-100` smoke | closed |
| T-14-14 | Tampering | bins built before fact set locked | mitigate | `_require_go_verdict` hard-exits unless GO/ADAPT | closed |
| T-14-15 | DoS | opaque numpy crash on shrunken corpus | mitigate | Explicit `SystemExit` naming length vs `BLOCK_SIZE + 1` floor | closed |
| T-14-16 | Tampering | one arm overwriting another's outputs | mitigate | `arm_outputs(arm)` + `refuse_if_exists`; pairwise disjointness in CI | closed |
| T-14-17 | Info Disclosure | fact values in the demo process | mitigate | Lazy imports; ints only; 3 tests incl. transitive `sys.modules` scan | closed (see UF-3) |
| T-14-18 | Spoofing (novel claim) | a fact value reaching a prompt | mitigate | `assert_no_value_in_prompt` → `SystemExit`, per question, pre-generation | closed |
| T-14-19 | Tampering | false negative from too small a budget | mitigate | `derive_recall_budget` + `assert_values_fit`; `>` vs `>=` pinned | closed |
| T-14-20 | Tampering | thresholds chosen after seeing numbers | mitigate | Committed as `None` in 14-05; rule in 14-07; git order is the proof | closed |
| T-14-21 | Repudiation | contradiction counts w/o evidence | mitigate | Mechanical detector over a committed lexicon; D-03 quoted fallback | closed |
| T-14-22 | EoP | shareable artifact deserialization | mitigate | `load_slim`/`load_adapter` `weights_only=True`; no direct `torch.load` | closed |
| T-14-23 | Tampering | adapter on the wrong base | mitigate | Fingerprint trio check + key/shape audit + captured warn → in-UI banner | closed |
| T-14-24 | Repudiation | cherry-picked transcripts | mitigate | 4,860 completions unfiltered behind a "failures included" opener | closed |
| T-14-25 | Tampering | base weights moved during teaching | mitigate | `snapshot_params` + two-sided canary `SystemExit` | closed |
| T-14-26 | DoS | EWC penalty crashing injected model | mitigate | `penalty_fn=None` structurally forced, both reasons documented | closed |
| T-14-27 | Info Disclosure | network egress from the demo | mitigate | Kill-switch ordering, `share=False`, theme override, asset scrubber | closed |
| T-14-28 | Spoofing | a "memory off" that is still on | mitigate | Merge refusal; no `merge()`; `torch.equal` bit-identity on real weights | closed |
| T-14-29 | Spoofing | token panel ≠ what the model got | mitigate | Single shared renderer; char-identical `ids` line asserted in CI | closed |
| T-14-30 | Tampering | concurrent events mutating the model | mitigate | One `concurrency_id` on every model-touching event | closed |
| T-14-31 | Repudiation | a derived number with no input | mitigate | `CALIBRATION_SHA` + per-derivation report sections naming rule + inputs | closed |
| T-14-32 | Spoofing (novel claim) | fairness control's in-context fact | mitigate | Sole `persona=` caller, AST-enforced; labelled a validity check | closed |
| T-14-33 | Repudiation | framing composed after the result | mitigate | D-20 constants committed 53 min before the run; `git log -S` is the check | closed |
| T-14-34 | Repudiation | a missed threshold quietly amended | mitigate | Verdict unamended; separate dated ship section; refuse-to-rerun guard | closed |
| T-14-35 | Tampering | bespoke dialogue-quality metric | mitigate | `masked_perplexity` only; `grep -c estimate_loss` = 0 | closed |
| T-14-36 | Tampering | `scripts/demo_app.py` edited despite D-17 | mitigate | `git diff <PINNED_SHA> HEAD` as a permanent CI test | closed |
| T-14-SC | Tampering | package installs | accept | Zero NEW packages; dependency manifests untouched — see Accepted Risks Log | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Test-suite evidence for every "asserted in CI" claim below:**
`.venv/bin/python -m pytest tests/test_phase14_demo.py tests/test_phase14_factset.py
tests/test_phase14_scoring.py tests/test_phase14_teaching.py tests/test_recall_prompt.py -q`
→ **105 passed** (run during this audit, 2026-08-02).

---

## Verification Evidence

### T-14-01 — Spoofing (novel claim), `build_recall_prompt` — CLOSED

- `src/personacore/dialogue/serialize.py:92-112` — one function, ids only; returns
  `ids[: ids.index(ASSISTANT_ID) + 1]` off an `encode_dialogue` call with an empty reply.
  Default `persona=()` produces a bare `<|system|>` with zero content.
- Two callers confirmed by grep: `scripts/phase14_recall.py` (`:381,409,602,1187,1307,1379`) and
  `scripts/personalize_demo.py:563`; also `scripts/phase14_factset_gate.py:93` and
  `scripts/teach_persona.py:367`. No parallel prompt builder exists anywhere in the phase.
- `tests/test_recall_prompt.py:81-92` `test_no_value_leaks_into_prompt` asserts **both** levels —
  `detokenize(value) not in tok.decode(ids)` and a contiguous-subsequence window scan over the
  ids — with `assert value_ids` at `:90` guarding against a vacuous needle.
- `tests/test_recall_prompt.py:58-62` pins the bare scaffold to exactly `[8187, 8185, 8186]`.

### T-14-02 — DoS, `generate_text_from_ids` — CLOSED

- `src/personacore/generation/text.py:152-155` — `if max_new_tokens <= 0 or max_new_tokens >
  max_new_tokens_cap: raise ValueError(...)`, placed **before** the tensor build (`:157`) and
  before the loop (`:163`). Cap default `4096` at `:28`.
- `tests/test_recall_prompt.py:242-254` `test_bounds_guard` drives `(0, -1, 4097)`, asserts the
  message contains `"(0, 4096]"`, and asserts `seen["n"] == 0` via a forward-pass spy — no
  forward pass happens on rejection. This is the assertion the register claims; it exists.

### T-14-03 — Tampering, `ASSISTANT_ID` resolution — CLOSED

- `src/personacore/dialogue/serialize.py:25` — `ASSISTANT_ID = SPECIAL_TOKENS[_ASSISTANT]`.
- **Grep run:** `grep -c "8186" src/personacore/dialogue/serialize.py` → **0**.
- `grep -rn "8186" src/` returns exactly one hit — the locked registry itself,
  `src/personacore/tokenizer/special.py:18`. The literal is never retyped.

### T-14-04 — EoP, `torch.load(weights_only=False)` — CLOSED

- `scripts/phase14_factset_gate.py:24-30` — `SECURITY:` docstring paragraph naming T-09-11 /
  T-14-04, stating trusted-own-file only and that shareable artifacts go through
  `load_slim`/`load_adapter`; the call is at `:143`.
- `scripts/teach_persona.py:25-36` — same paragraph, explicitly noting the bins half performs
  **no** `torch.load` at all and that the export path stays `weights_only=True`; the call is at
  `:544` with the inline restatement at `:541-543`.
- Both files' `weights_only=False` reads target `checkpoints/convbase_best.pt` only, resolved
  from `_REPO_ROOT` (`phase14_factset_gate.py:57`) — never a caller-supplied path.

### T-14-05 — Info Disclosure, fact values in public `results/` — CLOSED

- `scripts/phase14_factset.py:38-39` — "**No real personal data may enter any pool (T-14-05).**
  Every value here is invented or deliberately distinctive; everything in `results/` ships
  publicly."
- Values inspected and confirmed invented: `quillon`, `zorp`, `krix`, `zibby`, `orsala`,
  `brindlemoor`, `marrowgate`, `7412` (`:71-96`); calibration pool `:102-113`; register arm
  `:117-120`. All disjoint from real-world identifiers.
- `.gitignore:14-17` covers `checkpoints/`, `*.pt`, `logs/`, `data/`. **Verified live:**
  `git check-ignore -v data/x.bin checkpoints/y.pt logs/z.csv foo.pt` matched all four, and
  `git ls-files | grep -E '\.pt$|^data/|^logs/|^checkpoints/'` returned **empty** — nothing in
  those classes is tracked.

### T-14-06 — Tampering / DoS, verdict clobber + UI slider — CLOSED

- Reference guard `scripts/measure_inflation.py:66-75` — non-PENDING verdict → `SystemExit`
  unless `--force`.
- Ported to **all four** phase-14 report paths, each verified individually. Three of them are now
  **section-anchored** and share ONE regex — `scripts/_verdict.py:24` (`VERDICT_SECTION`) and its
  `recorded_verdict` accessor at `:27`, whose only import is `re`:
  - `scripts/phase14_factset_gate.py:116-137` (`assert_report_not_clobbered`, extracted from the
    inline `main()` block by quick task `260802-h3g` and called at `:141`)
  - `scripts/teach_persona.py:1137-1154` (`_refuse_clobber`, called `:1124`, `:1512`)
  - `scripts/phase14_recall.py:1617-1643`, section-anchored via `_VERDICT_SECTION` at `:1604`
    (the CR-02 fix), called at the **top** of `main()` (`:1697`) as well as from the writer
    (`:1048`) — a multi-hour run that refuses to write at the end has already wasted the run.
    This path keeps its OWN private copy of the regex on purpose: a module-level sibling import
    would put a non-package name at `phase14_recall` import time and is not worth risking the
    T-14-17 clean-room property for (see UF-4).
- All three anchored paths also treat "**no `## Verdict` section at all**" as REFUSE rather than
  overwrite-blind — a file that is not this writer's output is never clobbered silently.
- Tests: `tests/test_phase14_scoring.py:589` (`test_recall_report_refuses_to_clobber_a_recorded_verdict`)
  and `:617` (`test_recall_report_round_trips_without_force`);
  `tests/test_phase14_teaching.py:562` (`test_refuse_clobber_reads_the_verdict_section_not_the_last_mention`,
  which also carries the naive-`split` control) and `tests/test_phase14_factset.py:153`
  (`test_gate_clobber_guard_reads_the_verdict_section`).
- UI slider `scripts/personalize_demo.py:518-530` — `minimum=RECALL_MAX_NEW_TOKENS` (48),
  `maximum=256`, `step=8`. The `(0, 4096]` guard is therefore unreachable from the UI, as the
  module docstring states at `:29-30`.

### T-14-07 — Spoofing (novel claim), guessability measurement — CLOSED

- `scripts/phase14_factset_gate.py:93` — `prompt_ids = build_recall_prompt(tok, question)`; no
  hand-formatted string anywhere in the probe path.
- `:94` greedy draw; `:95` `gen_rng = torch.Generator(device=device).manual_seed(SEED + index)`
  — per-probe seeding (the `make_retention_samples.py:8-14` discipline), so an early stop in one
  probe cannot shift a later probe's stream.
- Verbatim quoting confirmed in the committed artifact: `results/phase14_factset_report.md:21`
  records the decode settings, and `:108-131`+ quote each completion inline
  (`- greedy: \`i am a college student…\``). The human close call at D-06 is auditable.

### T-14-08 — DoS, probe / recall generation loop — CLOSED

- `scripts/phase14_factset_gate.py:63` `PROBE_MAX_NEW_TOKENS = 32`, passed at `:78`.
- `scripts/phase14_recall.py:143-145` `RECALL_MAX_NEW_TOKENS = derive_recall_budget(...)` = 48,
  passed at `:530`.
- Both are **committed module constants**, not caller input; the loop bound itself is
  `src/personacore/generation/core.py:64` — `for _ in range(max_new_tokens)`.
- `forbid_ids` from `undecodable_ids_mask` at `phase14_factset_gate.py:158` and
  `phase14_recall.py:520`. The 7,645 count is pinned in CI:
  `tests/test_phase14_demo.py:161` — `assert int(mine.sum()) == 7645`, with `:162` asserting eos
  (8184) is **never** masked so the stop path is intact.
- `scripts/phase14_recall.py:162` `STOP_IDS = frozenset({8184, 8185})`, threaded at `:532`.

### T-14-09 — Tampering, locked constants vs the report — CLOSED

- `scripts/phase14_factset.py:378` — `FACTSET_GATE_SHA = "446afab372dcffbc16cbc9a667529097f6e5ccab"`.
- **Acceptance criterion run:** `git cat-file -e 446afab…` → object exists.
  `git log -1` on it → `Sun Aug 2 00:20:21 2026  docs(14-02): record D-06 verdict ADAPT — 8 core
  + 2 labelled soft`. The SHA genuinely pins the verdict commit.
- No runtime report parsing: `grep -n "read_text\|open("` over `scripts/phase14_factset.py`
  returns **no file-access call** — the module is pure data + pure functions, so drift shows in a
  diff rather than silently.

### T-14-10 — Spoofing (novel claim), stale guessability verdict — CLOSED

- `tests/test_phase14_factset.py:8-18` — the D-07 paragraph is in the **test module's own
  docstring**, as declared: "That measurement is **checkpoint-specific**… A future checkpoint
  inheriting a green run of this file has inherited **nothing** about guessability. Re-validating
  it against a different checkpoint requires a **fresh gated measurement** —
  `scripts/phase14_factset_gate.py --force` plus a new human D-06 verdict — and **not a test
  re-run**."
- Restated at the point of use, `tests/test_phase14_factset.py:148-149`.

### T-14-11 — Info Disclosure, real data in the locked set — CLOSED

- `tests/test_phase14_factset.py:144-152` `test_locked_values_are_first_person_register_safe`
  asserts `normalize_for_match(fact.value) not in priors` for every taught fact, against
  `_MEASURED_BASE_PRIORS` at `:59-61` (`cop`, `college student`, `the country`, `red`, `rose`,
  `max`, `lily`, `blue`). A real assertion, not a smoke import.
- Values invented — see T-14-05.

### T-14-12 — Spoofing (DEMO-06 claim), held-out leakage — CLOSED (location drift: UF-2)

- `tests/test_phase14_teaching.py:216-228` `test_families_disjoint` — asserts intersection is
  empty **and** the union equals `set(FAMILIES)` (the load-bearing half: an allocation move must
  not silently DROP a family).
- `:256-266` `test_no_string_leakage` — every held-out question's normalized text absent from the
  joined taught corpus.
- `:269-287` `test_no_token_leakage` — builds the real bin, then asserts no held-out question's
  `build_recall_prompt` ids appear as a contiguous run; `:286-287` is a **positive control** (a
  taught question's ids ARE present), so the check provably has teeth.
- Build-time `SystemExit`: `scripts/teach_persona.py:361-371` (proof 6), raising on any held-out
  question found as a contiguous id run in the bin **that was actually written**. It lives in
  `sanity_check`, not literally in `build_bins` — see UF-2; `build_arm_bins:415-416` calls the
  two back-to-back, so the guard is unconditional on the build path.
- `:231-253` `test_no_family_question_contains_another` adds the W-04 nesting check at both
  string and id level.

### T-14-13 — Tampering, mask off-by-one — CLOSED

- `src/personacore/dialogue/serialize.py:61-89` `encode_dialogue` is the single, span-wise,
  target-space mask source; `scripts/teach_persona.py:243` consumes it. Grep confirms
  **no new masking implementation** in the teaching script.
- `tests/test_phase14_teaching.py:136-157` `test_answer_span_mask` — hand-written literal
  expectations (`ids == FIXTURE_IDS`, `mask == FIXTURE_MASK`) plus the four structural positions
  pinned individually and both span slices asserted.
- `:160-181` `test_masked_batch_targets_carry_sentinel` — `-100` reaches the **targets** under
  the +1 shift, with `EXPECTED_SENTINEL_POSITIONS` written out by hand and `:181` asserting the
  first surviving target predicts the first ANSWER token.
- Runtime equivalent: `scripts/teach_persona.py:338-349` (proof 4) raises `SystemExit` if a real
  masked draw carries no `-100`.

### T-14-14 — Tampering, bins built before the gate — CLOSED

- `scripts/teach_persona.py:165-186` `_require_go_verdict` — section-anchored regex (`:173`),
  extracts the first word (`:179-180`), and raises `SystemExit` unless it is `GO` or `ADAPT`
  (`:181-185`). Missing report also raises (`:167-171`).
- **Call ordering verified:** `:506` is the *first* statement of `train_arm`, i.e. before
  `build_arm_bins` at `:538`. The `real` arm additionally gates on the calibration verdict at
  `:512`, with the asymmetry documented at `:509-511`.
- Tests: `tests/test_phase14_teaching.py:532-539` (GO/ADAPT pass), `:542-551` (PENDING/STOP raise
  and the exit **names** the word), `:554-558` (missing report names the producing driver).

### T-14-15 — DoS, shrunken corpus — CLOSED

- `scripts/teach_persona.py:266-276` — `if len(ids_all) <= BLOCK_SIZE + 1: raise SystemExit(...)`
  naming the measured token count **and** the `block_size + 1` floor, with the numpy failure it
  prevents spelled out. It fires inside `build_bins`, before `get_batch_memmap_masked` is ever
  called (first call `:339`).
- `tests/test_phase14_teaching.py:196-202` asserts `SystemExit` and that the message contains
  `str(BLOCK_SIZE + 1)` and `"floor"`.

### T-14-16 — Tampering, arm output collision — CLOSED

- `scripts/teach_persona.py:189-210` `arm_outputs(arm)` name-scopes all five targets; the one
  deliberate exception (the `real` arm's shippable `persona_adapter.pt`) is documented `:192-197`.
- `:213-221` `refuse_if_exists` raises `SystemExit` naming the offender.
- Called `:408-409` (bins) and `:515-520` — the latter refuses on **all five** targets up front,
  before a single token is written, with the reason at `:516-517`.
- `tests/test_phase14_teaching.py:486-502` `test_arm_outputs_scoped` — parametrized over all four
  arms, asserts intra-arm uniqueness **and** pairwise disjointness against every other arm, plus
  that Phase-12/13 evidence paths are never write targets. `:519-529` pins the naming behaviour.

### T-14-17 — Info Disclosure, fact values in the demo process — CLOSED (wording drift: UF-3)

- **Grep run:** `grep -c "phase14_factset" scripts/personalize_demo.py` → **0**. The fact-set
  module's name is not even written in the demo source (stated `personalize_demo.py:38-39`).
- `scripts/phase14_recall.py` — every `import phase14_factset` is function-scoped:
  `:628`, `:734`, `:783`, `:882`, `:1054`, `:1695`. **No module-level occurrence**; the rule is
  stated at `:431` and in the module docstring `:18-30`.
- `scripts/phase14_recall.py:103` — `VALUE_TOKEN_COUNTS: tuple[int, ...] = (5, 4, 5, 6, 8, 8, 4,
  4, 6, 6)` — integers only, explicitly "not a mapping from values" (`:24-25`).
- `tests/test_phase14_demo.py:380-396` `test_no_fact_values_in_ui_chrome` — loads the fact set
  through a non-registering `importlib` load, asserts exactly 10 values, then checks every UI copy
  constant **and** the whole demo source under `normalize_for_match`.
- `tests/test_phase14_demo.py:534-572` `test_demo_process_is_fact_free` — the transitive check.
  Spawns a **fresh interpreter**, imports the demo, and substring-scans every string held by every
  repo-owned module (including `__doc__`, and strings nested in tuples/dicts — `:493-516`) for all
  ten values; asserts `result["hits"] == []`, asserts the scan actually reached
  `personalize_demo` and `phase14_recall` (so a narrowed scan can't fake a pass), and keeps the
  original `sys.modules` membership assertions at `:571-572`.
- `tests/test_phase14_scoring.py:363-402` `test_no_fact_strings_at_import` — the harness-side
  equivalent, with `sys.modules` cleared first so the check cannot pollute what it measures.

### T-14-18 — Spoofing (novel claim), a fact value reaching a prompt — CLOSED

- `scripts/phase14_recall.py:398-421` `assert_no_value_in_prompt` — per value, `_prove`s the
  normalized string is absent from the decoded prompt (`:412-416`) **and** that the value's ids
  are not a contiguous run in the prompt ids (`:417-421`).
- `_prove` at `:221-224` raises `SystemExit` — explicitly *not* an `-O`-strippable `assert`.
- **Ordering verified:** called at `:804`, before `complete_question` at `:808`; the dump is
  rendered at `:801` *before* the model is called, so committed evidence is what the model
  received and not a post-hoc reconstruction (`:802-803`).
- Prompt ids committed: `results/phase14_transcripts.md` carries **540** `ids  (N) : [...]` blocks
  (`grep -c "^ids"` = 540), each beside its decoded line and source label.
- `.planning/.../14-11-SUMMARY.md` records an independent 540-prompt recheck: **0 leaks**.

### T-14-19 — Tampering, false negative from budget — CLOSED

- `scripts/phase14_recall.py:120-137` `derive_recall_budget` with the derivation in words at
  `:126-134`; applied at `:143-145`.
- `:239-261` `assert_values_fit` raises `SystemExit` naming the value, its token count, and the
  budget it blew — and `:246-251` honestly states what the guard can and cannot catch.
- `tests/test_phase14_scoring.py:180-197` `test_generation_budget_boundary` — asserts a value
  landing **exactly** on the budget passes (`:194`) and one id past it raises (`:196-197`). This
  is precisely the `>` vs `>=` distinction the register claims is pinned.
- `:200-213` asserts the exit message names the offender and the budget.

### T-14-20 — Tampering, thresholds chosen after the numbers — CLOSED

Git history is the proof, and it was **run**, not assumed:

| Commit | Timestamp | Content |
|---|---|---|
| `59af3ad` | 2026-08-02 01:09:06 | `feat(14-05)` — `git show 59af3ad:scripts/phase14_recall.py` shows `TAUGHT_THRESHOLD = None` / `HELDOUT_THRESHOLD = None` at `:134-135` |
| `d7d7917` | 2026-08-02 01:52:08 | `feat(14-07): commit CALIBRATION_DECISION_RULE before any calibration number exists` (`git log -S "CALIBRATION_DECISION_RULE = ("`) |
| `0425fdc` | 2026-08-02 03:37:12 | `feat(14-09): run the three calibration arms…` — the run, **1h45m after** the rule |
| `ec6a5b0` | 2026-08-02 03:41:01 | `feat(14-09): commit the four calibration-derived numbers into the drivers` |

- Locked values `scripts/phase14_recall.py:188-189`, with the inputs, rule, binding constraint,
  and the arm-correction rationale documented `:164-187`.
- `results/phase14_recall_report.md:14-26` `## Pre-Registration` names both `CALIBRATION_SHA` and
  `FACTSET_GATE_SHA` and states git-history order is the proof.
- `CALIBRATION_DECISION_RULE` literals + all boundaries pinned in CI:
  `tests/test_phase14_teaching.py:328-470` (constants, three boundary tests, allocation
  invariants, band-breaking refusal).
- Self-check in the driver: `scripts/teach_persona.py:951-965` searches on the tuple's
  **definition** (`CALIBRATION_DECISION_RULE = (`), not the bare name.

### T-14-21 — Repudiation, contradiction counts — CLOSED

- `scripts/phase14_recall.py:325-351` `find_contradictions` — mechanical: a completion is a
  contradiction iff it contains the value AND at least one **other** lexicon string.
- Lexicon built at `:786` — `set(fs.LOCKED_VALUES) | {f.value for f in
  fs.GATE_REJECTED_CANDIDATES}` — committed, pre-existing gate material, "requiring ZERO new
  editorial judgment" (`:332-337`).
- D-03 quoted-evidence fallback stated in the docstring at `:354-359`: any residual
  human-reviewed contradiction is traceable to the exact completion text in the committed
  transcripts. `:339-341` records that the metric is descriptive with no gate attached.
- Test: `tests/test_phase14_scoring.py:259` `test_contradiction_detector`.

### T-14-22 — EoP, shareable artifact deserialization — CLOSED

- `src/personacore/checkpoint.py:187` — `load_slim`: `torch.load(..., weights_only=True)`.
- `src/personacore/checkpoint.py:239` — `load_adapter`: `torch.load(..., weights_only=True)`,
  plus schema-version and required-key validation at `:240-251` so a malformed artifact fails at
  the choke point rather than deep in a consumer.
- **Grep run:** `grep -n "torch.load" scripts/phase14_recall.py scripts/personalize_demo.py`
  returns only **docstring mentions** (`phase14_recall.py:459`, `personalize_demo.py:28`) —
  **zero call sites**. The harness (`phase14_recall.py:1358`) and the demo
  (`personalize_demo.py:425,443`) both go through the two choke points.

### T-14-23 — Tampering, adapter on the wrong base — CLOSED

Four sub-claims, each verified separately:

1. **Trio check.** `scripts/personalize_demo.py:433-438` builds the fingerprint by **reading**
   `ckpt["git_sha"]`, `ckpt["step"]`, `ckpt["val_loss"]` off the loaded base — never recomputed.
   Passed at `:443`. `src/personacore/checkpoint.py:253-260` warns naming **both** trios and
   loads anyway (D-02 warn-not-error, locked).
2. **Key/shape audit before mutation.** `src/personacore/lora/inject.py:89-104` — key-set
   mismatch raises `ValueError` naming the symmetric difference (`:89-94`); shape/dtype mismatch
   raises naming the offenders (`:96-104`) — **before** any tensor is copied, with the
   `load_state_dict(strict=False)` partial-copy failure mode documented `:82-83`. Called at
   `personalize_demo.py:445`, after the fingerprint check.
3. **Warning captured → report AND persistent in-UI banner.**
   `scripts/personalize_demo.py:441-443` captures with `warnings.catch_warnings(record=True)` +
   `simplefilter("always")`; `:461-474` builds `MISMATCH_BANNER_TEMPLATE`; `:480` renders it with
   `visible=bool(mismatched)`. Harness side: `scripts/phase14_recall.py:504-509` captures into
   `artifact["fingerprint_warnings"]`, carried into the report at `:643-644`.
4. **`git_sha()` not used inside `export_adapter`.** `scripts/teach_persona.py:653-663` — the
   `export_adapter(...)` call spans `:654-663` and its `base_fingerprint` reads
   `blob["git_sha"] / blob["step"] / blob["val_loss"]`. The next `git_sha()` in the file is at
   `:691`, in the provenance print, outside the call.

### T-14-24 — Repudiation, cherry-picked transcripts — CLOSED

- `results/phase14_transcripts.md:3-6` — the declared opener, verbatim: "**Every completion
  produced by the run appears below, failures included and unfiltered.** … nothing was drawn,
  ranked, truncated, or re-rolled on its way to this file."
- `:44` records the split: "**540 greedy + 4320 seeded** (8 per question at temperature=0.8,
  top_p=0.95) over 540 questions" — 4,860 completions total.
- `:10-12` records the per-question seed derivation:
  `torch.Generator().manual_seed(question_seed(i) + s)` = `1337 + i + s`, "so every draw here is
  re-derivable from the seed alone". Implementation `scripts/phase14_recall.py:227-233`.
- Each completion is labelled inline (`**greedy · HIT · stop-id**`, `**seeded #1 · miss ·
  stop-id**`) — misses are printed next to hits, not elided.
- CR-01 hardening: `scripts/phase14_recall.py:795-800` `_prove`s every scored item carries a
  stamped `seed_index`, so the closed-book control cannot silently draw from a different stream.

### T-14-25 — Tampering, base weights moved during teaching — CLOSED

- `scripts/teach_persona.py:589-590` — `model.to(runtime.device)` then `before =
  snapshot_params(model)`, with the device-ordering reason at `:587-588`. Snapshot precedes
  `train(...)` at `:595`.
- Two-sided canary `:641-651`:
  - `:642-646` — a trainable param that did **not** move → `SystemExit` (MPS silent-freeze class,
    PITFALLS P5).
  - `:647-650` — a frozen base param that **did** change → `SystemExit` (grad isolation broken,
    LORA-02).
  - `:639-640` additionally rejects a non-finite final loss.
  - `:638` records these are explicit raises, non-zero exit even under `python -O`.
- Run log committed: `results/phase14_teaching_run.log:13` —
  `[teach_persona] canary passed: all lora_ moved, base bit-untouched`.

### T-14-26 — DoS, EWC penalty on an injected model — CLOSED

- `scripts/teach_persona.py:629` — `penalty_fn=None`, with both declared reasons at `:620-628`:
  (a) with the base frozen the EWC anchor is a constant → zero gradient, and a chart crediting
  EWC with retention frozen-base LoRA produces for free; (b) `inject_lora` renames every wrapped
  base parameter with a `.base.` infix while Fisher keys are vanilla-GPT names, so
  `EWCPenalty.__call__` raises `ValueError` — a hard crash, not a silent no-op.
- The Fisher-bearing checkpoint's extras are never forwarded: the `train(...)` call `:595-635`
  passes no `blob` key other than the model weights loaded at `:565`.

### T-14-27 — Info Disclosure, network egress — CLOSED

- **Ordering.** `scripts/personalize_demo.py:62` sets `GRADIO_ANALYTICS_ENABLED=False`;
  `import gradio as gr` is at `:64`. Pinned in CI by
  `tests/test_phase14_demo.py:360-372`, which compares **source offsets**
  (`killswitch < gradio_import`) so a formatter-induced reorder goes red.
- **`analytics_enabled=False`** — `personalize_demo.py:476`; asserted `test_phase14_demo.py:371`.
- **`share=False`** — `personalize_demo.py:636`; asserted `test_phase14_demo.py:372`.
- **Theme font override** — `personalize_demo.py:187`, with the measured stock-theme GoogleFont
  URL recorded `:176-183`. `tests/test_phase14_demo.py:244-254` asserts the **stock** theme still
  carries a remote URL (so the test can't pass vacuously), `gr.Blocks(theme=pd.THEME).stylesheets
  == []`, and that `build_demo` actually passes `theme=THEME`. The literal
  `build_demo().stylesheets == []` runs locally (`:621-623`, skip reason: gitignored checkpoints).
- **Third-party `<script>`** (the half a stylesheet assertion structurally cannot see):
  `StripThirdPartyAssets` middleware `personalize_demo.py:229-245`, threaded via `APP_KWARGS`
  `:250` into `launch()` `:636`. `tests/test_phase14_demo.py:310-346` renders the **real** Gradio
  template through the **real** seam (`App.create_app` + `TestClient`), walks every
  request-issuing attribute with an independent stdlib `HTMLParser` (`:257-285` — deliberately
  not a re-run of the module's own regex), and asserts `off_origin == []`, plus that the page
  still works. `:349-357` asserts the scrubber is actually threaded into `launch`.
- **Empirical verification** recorded in `14-11-SUMMARY.md` (commit `5453d47`): live browser
  trace, "third-party origins on load: **none**"; DOM off-origin `script[src]`/`link[href]` = `[]`.

### T-14-28 — Spoofing, a "memory off" that is still on — CLOSED

- `src/personacore/lora/inject.py:121-127` — `set_adapter_enabled` runs a **pre-pass** over every
  `LoRALinear` and raises `RuntimeError` if any is merged, so a refusal flips **no flag at all**;
  the reason ("memory off while the adapter is still in the weights would falsify the demo's
  central claim") is at `:116-119`.
- **Grep run:** `grep -c "merge(" scripts/personalize_demo.py` → **0**. The demo never merges.
- `scripts/phase14_recall.py:1336-1396` `run_bit_identity_control`:
  - CPU-pinned via `RuntimeConfig(device="cpu")` (`:1357`), with the MPS cross-process ~3.6e-8
    divergence reason at `:1346-1350`.
  - Model A = un-adapted **real 13.9M** base (`:1362-1364`); Model B = same weights with the
    **real** adapter injected, loaded, then gated off (`:1369-1374`).
  - `torch.equal(logits_base, logits_gated)` on **full** logits, `_prove`d at `:1385-1390`;
    `max_abs_diff` recorded so the report can state a number.
- Reported: `results/phase14_recall_report.md:522` `## Control 3 — Adapter-Off Bit Identity
  (D-11.3)`; the verdict records `toggle bit-identity 0.0`.

### T-14-29 — Spoofing, token panel vs what the model received — CLOSED

- `scripts/personalize_demo.py:393-402` `render_token_panel` delegates to
  `phase14_recall.render_context_dump` — imported at `:106-112`, the same call the harness makes
  (`phase14_recall.py:801`). Used for both the startup scaffold (`:508`) and every live turn
  (`:557`).
- `tests/test_phase14_demo.py:193-207` `test_prompt_ids_identical` — parametrized over 6
  questions (incl. empty and punctuation), asserts `panel[0] == dump[0]` (**byte-identical** ids
  line) and `panel[1] == dump[1]` (decoded line), that the parsed ids equal
  `build_recall_prompt(...)` element-for-element, and that only the provenance `source` line
  differs.
- `:210-220` pins the startup scaffold to real computed data, never a placeholder string.

### T-14-30 — Tampering, concurrent model mutation — CLOSED

- `scripts/personalize_demo.py:408` `MODEL_LOCK = "personacore-model"`.
- Applied to **every** model-touching event — enumerated, not sampled:
  - `:614-620` — `textbox.submit` / `ask_btn.click` → `.then(on_ask, …, concurrency_id=MODEL_LOCK)`
  - `:625` — `memory_box.input(on_toggle, …, concurrency_id=MODEL_LOCK)`
  - `:626-628` — `reset_btn.click(on_reset, …, concurrency_id=MODEL_LOCK)`
  - The only handler without it, `stash` (`:615`), carries `queue=False` and touches no model —
    it swaps textbox text for state.
- `.input()` rather than `.change()` at `:621-624`, so `on_reset`'s programmatic update cannot
  re-enter `on_toggle` and overwrite the DELETED banner.
- Single-user local assumption stated in the module docstring `:41-44`.

### T-14-31 — Repudiation, untraceable derived numbers — CLOSED

- `scripts/phase14_recall.py:197` `CALIBRATION_SHA = "0425fdc…"`; **verified live** —
  `git cat-file -e` passes, `git log -1` → `feat(14-09): run the three calibration arms and
  record all four derivations`. `:191-196` explains it points at the **evidence** commit, not a
  verdict commit, and why.
- Per-derivation report sections, each naming the rule function and its inputs:
  `results/phase14_calibration_report.md:162` (Derivation 1 — Recall Thresholds, with
  `:168`/`:182` showing the original and corrected input arms side by side and `:201` a
  side-by-side table), `:239` (Derivation 2 — Family Allocation), `:280` (Derivation 3 —
  PersonaChat Replay), `:328` (Derivation 4 — Teaching Register).
- Echoed into the recall report's provenance table at `scripts/phase14_recall.py:1767`.

### T-14-32 — Spoofing (novel claim), the fairness control's in-context fact — CLOSED

- **Grep run:** the only `persona=` call in the entire phase-14 script surface is
  `scripts/phase14_recall.py:1187`, inside `run_fairness_control`. `:591` states the recall path
  must never pass it.
- Mechanically enforced, not asserted:
  `tests/test_phase14_scoring.py:405-449` parses the driver with **AST** (a substring check
  cannot distinguish a call from a docstring mention — `:408-410`), collects every
  `build_recall_prompt` call tagged with its enclosing function, then asserts
  `with_persona == ["run_fairness_control"]` (`:444`), that every other site passes zero keywords
  (`:447`), and that the three expected bare-form callers are present (`:448-449`).
  The demo half is pinned separately: `tests/test_phase14_demo.py:233` asserts `"persona="` is
  absent from the demo source entirely.
- Report framing: `results/phase14_recall_report.md:364` `## Control 1 — Question Fairness
  (D-11.1)` with `:380` "(a) What this control can no longer prove", `:403` "(b) Why the phase's
  central comparison survives anyway", `:414` "(c) What the adapter's success is actually
  demonstrating" — a validity check, explicitly not a mechanism comparison.

### T-14-33 — Repudiation, framing composed after the result — CLOSED

- Module-level string constants: `scripts/phase14_recall.py:1451` `RECONCILIATION_A`, `:1475`
  `RECONCILIATION_B`, `:1503` `FAILURE_BRANCH`, `:1561` `THREATS_TO_VALIDITY`, `:1590`
  `SHIP_DECISION_HEADER`.
- **`git log -S` run, as the register specifies:** all introduced in `48d557a`, 2026-08-02
  08:21:48 (`feat(14-10): add write_recall_report with every pre-registered section`). The scored
  run landed in `043bf4d`, 09:15:09 (`feat(14-11): scored recall run in a fresh process — both
  gates PASS`) — the framing precedes the result by **53 minutes**.
- Rendered as `results/phase14_recall_report.md:431` `## Pre-Registered Failure Branch (D-20)`.

### T-14-34 — Repudiation, a missed threshold quietly amended — CLOSED

- `results/phase14_recall_report.md:573-589` `## Verdict` — "The user's verdict is recorded
  verbatim below, unwrapped and unedited", followed by both threshold comparisons and the two
  qualifications recorded verbatim, closing with "reported as named limitations alongside the
  passed gate numbers … not folded into or softening them".
- `:591` `## Ship Decision — post-verdict, discretionary`, carrying the D-12 comment verbatim:
  logged "separate from the gate verdict, dated AFTER it, and explicit that it does not reopen or
  amend the pre-registered threshold". Correctly empty (the gate cleared).
- Refuse-to-rerun: `scripts/teach_persona.py:213-221` (verified in 14-11 to exit 1 naming all
  five paths on a second attempt) and `scripts/phase14_recall.py:1617-1643`, armed at the top of
  `main()` (`:1697`).
- `grep -c PENDING results/phase14_recall_report.md` → 0 (14-11-SUMMARY verification table).

### T-14-35 — Tampering, bespoke dialogue-quality metric — CLOSED

- **Grep run**, all five phase-14 scripts: `grep -c "estimate_loss"` →
  `phase14_recall.py: 0`, `teach_persona.py: 0`, `personalize_demo.py: 0`,
  `phase14_factset.py: 0`, `phase14_factset_gate.py: 0`. The acceptance criterion holds.
- `masked_perplexity` is the sole instrument: `scripts/phase14_recall.py:65` (import),
  `:1291`/`:1295` (adapter-on / adapter-off pair); `scripts/teach_persona.py:70` (import),
  `:669`/`:673`. Both pairs assert identical scored-target counts
  (`teach_persona.py:676-680`) so the two sweeps cover the same set.
- WR-01 correction recorded `phase14_recall.py:1911` and `teach_persona.py:547-554`: `forbid_ids`
  is now passed on the collapse pair, making it literally the frozen D-11.2 instrument.

### T-14-36 — Tampering, `scripts/demo_app.py` frozen — CLOSED

- `tests/test_phase14_demo.py:580-596` `test_demo_app_frozen` — runs
  `git diff cdd778692bfb2a14167ba33545a2f6a09148d451 HEAD -- scripts/demo_app.py` via
  `subprocess.run(check=True)` and asserts `diff.stdout == ""`.
- It is the **stronger** form the register specifies: a diff against a **pinned commit**
  (`_DEMO_APP_SHA`, `:83`), not `git diff --quiet`, so a **staged** edit is caught and the guard
  outlives the phase (rationale `:581-587`).
- **It runs and passes** in the 105-test audit run — a permanent, non-skipped CI test.

### T-14-SC — Tampering, package installs — ACCEPTED, verified

Factual basis checked before acceptance:

- Phase-14 commit range is `d376305^..HEAD` (**75 commits**, `d376305` = `feat(14-01): add
  build_recall_prompt to dialogue/serialize.py`).
- `git log --name-only d376305^..HEAD -- pyproject.toml requirements.txt` → **no commits**.
- `git diff d376305^ HEAD -- pyproject.toml requirements.txt` → **empty**.
- `gradio>=5,<6` is pre-existing at `pyproject.toml:17` (`demo = ["gradio>=5,<6",
  "matplotlib~=3.10"]`), registry-audited in 08-RESEARCH.
- Conclusion: **zero new packages**. No supply-chain surface was added this phase. Recorded in
  the Accepted Risks Log below.

---

## Unregistered Flags (WARNING — not blockers)

No plan declared new attack surface. Four documentation/consistency findings, none of which
leaves a threat open:

**UF-1 — `## Threat Flags` section missing from 7 of 11 summaries.**
Only `14-06`, `14-08`, `14-09`, `14-11` carry the literal `## Threat Flags` heading (all four say
"None", with reasons). `14-01`–`14-05` use `## Threat Mitigations Applied`, `14-07` uses
`## Threat Model Coverage`, and `14-10` has no threat section at all. The register is
plan-authored and all 37 threats were verified directly against code, so nothing is unaudited —
but the phase's own "new attack surface" declaration channel is inconsistent, and a future audit
that trusts `## Threat Flags` as the complete list would under-scan those seven plans.

**UF-2 — T-14-12's build-time guard is not where the register says it is.**
The register text places the held-out-leakage `SystemExit` "in `build_bins`". It is actually
`scripts/teach_persona.py:361-371`, proof 6 of `sanity_check`. `build_arm_bins:415-416` calls
`build_bins` then `sanity_check` back-to-back, so the guard is unconditional on the build path
and the threat is genuinely closed — but a reader grepping `build_bins` for the leak guard finds
only the alignment / floor / mask-fraction proofs and could conclude it is absent.

**UF-3 — T-14-17's "confined to `main()`" understates the surface.**
There are **six** function-scoped `import phase14_factset` sites in `scripts/phase14_recall.py`
(`:628, 734, 783, 882, 1054, 1695`), not one in `main()`. The load-bearing property — nothing at
module level — holds and is enforced by `test_no_fact_strings_at_import` and
`test_demo_process_is_fact_free`, so the threat is closed; the register text is just narrower
than the code.

**UF-4 — the CR-02 clobber-guard fix was applied to one path, not all four.**
`phase14_recall.assert_report_not_clobbered` anchors on the first `## Verdict` **section**
(`:1604`) after CR-02 showed that `split("## Verdict")[-1]` lands in the ship-decision comment.
**Resolved for the two phase-14 siblings by quick task `260802-h3g` (2026-08-02).**
`teach_persona._refuse_clobber` (`:1137-1154`) and the newly extracted
`phase14_factset_gate.assert_report_not_clobbered` (`:116-137`) both now read the first
`## Verdict` SECTION through the single shared `scripts/_verdict.py:27` `recorded_verdict`, and
both additionally REFUSE a file with **no verdict section at all** rather than overwriting it
blind. The extraction also made the gate's guard reachable from a test for the first time (it was
inline in `main()`, behind a 278 MB checkpoint load). Both fixes were driven RED-first; the naive
`split("## Verdict")[-1]` control is kept deliberately in
`tests/test_phase14_teaching.py:562` so a regression back to the tail form fails there with the
reason written beside it. The defect was **latent, never live** on these two paths —
`results/phase14_calibration_report.md` and `results/phase14_factset_report.md` each contain
`## Verdict` exactly once (the recall report contains it twice, which is why only that one broke).
**Still carrying the idiom, deliberately out of that task's scope:**
`scripts/measure_inflation.py:70` (Phase 13) and `scripts/finetune_smoke.py:727` (Phase 12) —
both outside Phase 14, both latent in the same way. The finding stays recorded and non-blocking;
T-14-06 was closed on all four paths before the fix and remains closed after it.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-14-01 | T-14-SC | Zero new packages were added, installed, or upgraded during Phase 14. Verified across all 75 commits in the phase range: `git log --name-only d376305^..HEAD -- pyproject.toml requirements.txt` lists no commits and `git diff d376305^ HEAD -- pyproject.toml requirements.txt` is empty. The one dependency the phase exercises, `gradio>=5,<6` (`pyproject.toml:17`), was pinned and registry-audited in Phase 8 (08-RESEARCH, PyPI + wheel source inspected 2026-06-10). There is no new supply-chain surface to audit; the risk is accepted as nil rather than mitigated by a control. | gsd-security-auditor | 2026-08-02 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-02 | 37 | 37 | 0 | gsd-security-auditor |

**Pass 1 scope.** First audit of Phase 14 (State B — no prior SECURITY.md). All 37 unique
register threats verified against implemented code, deduplicated across the 11 plans; the union
of each threat's mitigation text across every plan claiming it was treated as the claim to
verify. Every declared grep-count acceptance criterion was **executed**, not assumed:
`grep -c "8186"` on the dialogue module = 0, `grep -c "phase14_factset"` on the demo source = 0,
`grep -c "estimate_loss"` on all five phase-14 scripts = 0, `grep -c "merge("` on the demo = 0.
Every declared pinning SHA was resolved with `git cat-file -e` and `git log -1`
(`FACTSET_GATE_SHA` → the D-06 verdict commit; `CALIBRATION_SHA` → the calibration run commit).
Every declared pre-registration ordering was checked with `git log -S` and `git show`
(`TAUGHT_THRESHOLD = None` at `59af3ad`; `CALIBRATION_DECISION_RULE` at `d7d7917`, 1h45m before
the calibration run at `0425fdc`; the D-20 constants at `48d557a`, 53 min before the scored run
at `043bf4d`). Every test cited as an enforcement mechanism was **read** to confirm it asserts
the claimed property rather than smoke-importing, and the suite was run
(**105 passed**), which exercises `test_demo_app_frozen`, `test_demo_process_is_fact_free`, the
served-page third-party-asset walk, and the AST-based `persona=` scoping check.

No implementation file was modified by this audit.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed — **0 open**
- [x] `status: verified` set in frontmatter

**Approval:** approved. All 37 threats closed. Four non-blocking warnings carry forward:
UF-1 (`## Threat Flags` absent from 7 of 11 summaries), UF-2 (T-14-12's guard lives in
`sanity_check`, not `build_bins`), UF-3 (T-14-17 has six lazy-import sites, not one in `main()`),
UF-4 (the CR-02 section-anchored clobber-guard fix applied to one of four report paths — latent,
not live; since resolved for both phase-14 siblings by quick task `260802-h3g`, with
`measure_inflation.py:70` and `finetune_smoke.py:727` still carrying the idiom).
