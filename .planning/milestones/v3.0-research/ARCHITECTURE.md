# Architecture Research

**Domain:** Adversarial privacy audit of weight-resident memory (LoRA), bolted onto a shipped from-scratch LM stack
**Researched:** 2026-08-12
**Confidence:** HIGH for integration points (read against actual file contents at `829cd5f`); MEDIUM for compute-budget estimates; LOW for external attack-taxonomy grounding (see Sources)

---

## Executive Answer (read this first)

Three findings drive everything below.

1. **Phase 16 already exists in embryo.** `phase14_recall.run_fairness_control` (`scripts/phase14_recall.py:1147`) *is* the prompt-stuffed condition — it builds `build_recall_prompt(tok, q, persona=[statement])`, draws through the shared `draw_all`, and scores with `score_question`. Phase 14 deliberately scoped it as a one-directional question-validity check and refused to call it DEMO-F2 (`FAIRNESS_OPENER`, line 1427). Phase 16 is the promotion of that control into a paired 2×2 — not new infrastructure.

2. **The guard tension resolves by inversion, not by a flag.** Do NOT add `allow_fact_in_prompt=` to `assert_no_value_in_prompt`. Add its logical twin, `assert_value_in_prompt`, so that *every* scoring path carries an assertion and no path has a skip mode. The seed of that twin is already at lines 1188-1192.

3. **Zero new `src/personacore/` modules are warranted across 16-18.** Everything new is either committed pre-registration data/rules (which the project's own decision puts in `scripts/`, see `phase14_factset.py:7-8`) or thin audit orchestration. No new ML mechanism is introduced. Phase 17's N-adapter swap works through the existing `load_adapter_weights` + `lora_state_dict` API unchanged.

**One defect found that Phase 16 must fix first:** `run_fairness_control` seeds its draws from `enumerate(questions)` (line 1184), not from `item.seed_index`. That is the exact CR-01 pairing defect that `stamp_seed_indices` (line 692) was written to close for the closed-book control, left unfixed in the fairness path because Phase 14 never compared fairness against anything. Phase 16 *does* compare it, so the arms would be unpaired on every question past the first arm boundary.

---

## Standard Architecture

### System Overview — where v3.0 attaches to the shipped stack

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  FROZEN SUBSTRATE (v1.0/v2.0 — nothing in v3.0 modifies these)               │
│  artifacts/tokenizer.json · checkpoints/convbase_slim.pt · convbase_best.pt  │
│  src/personacore/{tokenizer,model,generation,dialogue,lora,evaluation}/      │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ▲ imported, never edited
┌───────────────────────────────────┴──────────────────────────────────────────┐
│  SHARED INSTRUMENT LAYER (scripts/phase14_recall.py — becomes 3-consumer)    │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐ ┌───────────────────┐ │
│  │ normalize    │ │contains_value│ │ score_question │ │ find_contradictions│ │
│  │ draw_all     │ │ _complete    │ │ render_context_│ │ has_hedging       │ │
│  │ load_adapted_│ │ question_seed│ │ dump           │ │ stamp_seed_indices│ │
│  │ model(path=) │ │ RecallItem   │ │ build_question_│ │ RECALL_MAX_NEW_TOK│ │
│  └──────────────┘ └──────────────┘ │ sets           │ └───────────────────┘ │
│  ┌────────────────────────────────┐└────────────────┘                        │
│  │ assert_no_value_in_prompt      │  ◄── NEW TWIN: assert_value_in_prompt    │
│  └────────────────────────────────┘      (symmetric, no skip mode)           │
└──────────────────────────────────────────────────────────────────────────────┘
        ▲                       ▲                          ▲
┌───────┴────────┐   ┌──────────┴───────────┐   ┌──────────┴──────────────────┐
│  PHASE 16      │   │  PHASE 17            │   │  PHASE 18                   │
│  weight vs     │   │  isolation matrix    │   │  extraction audit           │
│  prompt        │   │                      │   │                             │
│ phase16_weight_│   │ phase17_personas.py  │   │ phase18_attacks.py          │
│ vs_prompt.py   │   │  (generator, DATA)   │   │  (attack corpus, DATA)      │
│                │   │ phase17_persona_gate │   │ phase18_extract.py (driver) │
│  (driver only) │   │ teach_persona.py ▲mod│   │                             │
│                │   │ phase17_matrix.py    │   │                             │
│                │   │ plot_phase17.py      │   │                             │
│                │   │ phase17_stats.py     │   │                             │
└────────────────┘   └──────────────────────┘   └─────────────────────────────┘
        │                       │                          │
        └───────────────────────┼──────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  COMMITTED EVIDENCE (results/ — git-tracked)                                  │
│  phase16_conditions.json   phase17_isolation.json   phase18_extraction.json  │
│  phase16_transcripts.md    phase17_transcripts.md   phase18_transcripts.md   │
│  phase16_report.md         phase17_report.md        phase18_report.md        │
│                            phase17_isolation.png                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                ▲ all three import
┌───────────────────────────────┴──────────────────────────────────────────────┐
│  scripts/erasure_gate.py — ERASURE_DECISION_RULE, committed at Phase 16 open │
│  (the Phase-19 go/no-go, pre-registered before any 16-18 number exists)      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities — NEW vs MODIFIED vs REUSED

| Component | Status | Responsibility | Notes |
|-----------|--------|----------------|-------|
| `src/personacore/**` | **REUSED, unmodified** | LoRA inject/toggle/load, generation, dialogue prompt building, masked PPL | No v3.0 edits. `load_adapter_weights` already does the key+shape audit N-adapter swapping needs (`lora/inject.py:76`). |
| `scripts/phase14_recall.py` | **MODIFIED (additive)** | The shared scoring instrument for all three phases | Two changes only: (1) `run_fairness_control` seed fix `enumerate` → `item.seed_index`; (2) add `assert_value_in_prompt` next to its twin. Nothing else moves. |
| `scripts/phase14_factset.py` | **REUSED, unmodified** | `Fact`, `SLOT_FORMS`, `FAMILIES`, `render_family`, `SLOT_QUESTION_BANK`, `exact_match_clean` | Phase 17's generator *imports* the teaching grammar so its adapters are comparable to `persona_adapter.pt`. It must not fork the grammar. |
| `scripts/teach_persona.py` | **MODIFIED (additive)** | N training runs for Phase 17 | Extend `ARMS` (line 163) + `arm_spec` (line 383) + `arm_outputs` (line 190). Make the gate-report path part of the arm spec so Phase-17 arms gate on their own report, not `FACTSET_REPORT`. |
| `scripts/phase14_factset_gate.py` | **MODIFIED (rename only)** | Guessability measurement for Phase-17's new values | Promote `_probe`/`_complete`/`_quote` (lines 73-115) from private to public so `phase17_persona_gate.py` imports the *same instrument* rather than a copy. Its 280-line report writer stays Phase-14-specific. |
| `scripts/_verdict.py` | **REUSED, unmodified** | Anchored `## Verdict` section read | Every new report writer gets an `assert_report_not_clobbered` built on it (`phase14_recall.py:1617`, `phase14_factset_gate.py:116`). |
| `scripts/phase16_weight_vs_prompt.py` | **NEW (driver)** | The 2×2 condition matrix, gates, framing constants, report | Imports the instrument. Holds Phase-16 pre-registration. |
| `scripts/phase17_personas.py` | **NEW (data)** | N adversarial persona fact sets + the declared collision structure | Pure data + pure functions, no torch, no `main()` — the `phase14_factset.py` register. |
| `scripts/phase17_persona_gate.py` | **NEW (driver)** | Guessability gate on the new values → committed report + human verdict | Without this, M_ij's diagonal is uninterpretable: a base-guessable value scores on *every* adapter. |
| `scripts/phase17_matrix.py` | **NEW (extract)** | The ONLY Phase-17 code that opens a checkpoint; writes the M_ij artifact | The `extract_deltas.py` role. |
| `scripts/plot_phase17.py` | **NEW (plot)** | Heatmap from the committed JSON only | The `plot_phase15.py` role, including the AST + fresh-interpreter no-torch guard. |
| `scripts/phase17_stats.py` | **NEW (verdict)** | Pre-registered isolation gate + seed-replication statistic | The `phase15_stats.py` role. Only if a gate is wanted — see "Gate only what n supports". |
| `scripts/phase18_attacks.py` | **NEW (data)** | Attack families as named generators with stable ids | Same register as `phase14_factset.FAMILIES`. Committed before any attack runs. |
| `scripts/phase18_extract.py` | **NEW (driver)** | Negative control + adapter-active attacker; writes JSON + transcripts | |
| `scripts/erasure_gate.py` | **NEW (rule)** | `ERASURE_DECISION_RULE` — the Phase-19 go/no-go | Phase-neutral, dependency-free (the `_verdict.py` register). Committed at Phase-16 open. |

**No new `src/personacore/` module.** Justification, in the project's own terms: the package holds reusable ML *mechanism*; 16-18 add none. The one borderline case — swapping N adapters onto one injected model — is already covered by `load_adapter_weights` + `lora_state_dict` and needs no new code. Creating `src/personacore/audit/` would be an interface with one implementation and would *move* the D-10 scoring rule out of the committed driver, which is the opposite of `phase14_factset.py:7-8` ("rules live in the committed driver, not in the package where the driver could drift away from them").

---

## Recommended Project Structure

```
scripts/
├── phase14_recall.py            # MODIFIED — becomes the 3-consumer scoring instrument
│   ├── assert_no_value_in_prompt        (unchanged, still unconditional in run_scored_recall)
│   └── assert_value_in_prompt           (NEW — the symmetric twin)
├── teach_persona.py             # MODIFIED — ARMS / arm_spec / arm_outputs extended
├── phase14_factset_gate.py      # MODIFIED — _probe → probe (visibility only)
├── erasure_gate.py              # NEW — ERASURE_DECISION_RULE (Phase-19 pre-registration)
│
├── phase16_weight_vs_prompt.py  # NEW — Phase 16, single driver
│
├── phase17_personas.py          # NEW — generator: N personas + declared collisions
├── phase17_persona_gate.py      # NEW — guessability gate on the new values
├── phase17_matrix.py            # NEW — the only P17 checkpoint reader → isolation.json
├── plot_phase17.py              # NEW — json → png, structurally torch-free
├── phase17_stats.py             # NEW — pre-registered isolation verdict
│
├── phase18_attacks.py           # NEW — attack corpus as data
└── phase18_extract.py           # NEW — control + attacker runs

results/                          # git-tracked
├── phase16_conditions.json       phase16_transcripts.md   phase16_report.md
├── phase17_personas_report.md    phase17_isolation.json   phase17_transcripts.md
├── phase17_isolation.png         phase17_report.md
└── phase18_extraction.json       phase18_transcripts.md   phase18_report.md

tests/                            # CPU-only, GPU-free, additive
├── test_phase16_conditions.py    # the two-assertion AST scoping, gate boundaries, seed pairing
├── test_phase17_personas.py      # collisions actually collide; grammar not forked
├── test_phase17_plots.py         # plot module never opens a checkpoint (AST + fresh interp)
└── test_phase18_attacks.py       # no attack prompt contains any locked value

checkpoints/                      # gitignored
└── phase17_{a,b,c}_adapter.pt    # + phase17_{a,b,c}_latest.pt, seed-replication adapters

data/                             # gitignored
└── persona_phase17_{a,b,c}_train{,_mask}.bin
```

### Structure Rationale

- **`scripts/` for everything.** The project's convention is "reusable logic goes in the package, drivers stay thin" — but v3.0's new logic is *committed evidence-producing rules and data*, which the project has consistently kept in `scripts/` precisely so git history over that file is the pre-registration proof. `phase14_factset.py` (848 lines of pure data + pure functions, no `main()`) is the existing proof that this is the right home for a committed data surface.
- **One file per role, three roles per phase** — data / extract / render. Phase 15 established this and the payoff is that the render half runs in the CPU-only suite while the extract half needs the gitignored weights.
- **`erasure_gate.py` outside all three phases** so one `git log -S` proves its ordering against all three.

---

## Architectural Patterns

### Pattern 1: Guard inversion — symmetric assertions, never a bypass flag

**The problem.** `run_scored_recall` calls `assert_no_value_in_prompt(tok, item.question, all_values)` unconditionally (`phase14_recall.py:804`) and `SystemExit`s on any hit. Phase 16's prompt-stuffed arm deliberately puts the value in the prompt.

**The wrong fix** (and it is genuinely tempting): `assert_no_value_in_prompt(..., allow=False)` or `run_scored_recall(..., stuffed=True)`. This converts a structural invariant into a runtime flag. One wrong default and the clean-room path stops checking silently — the failure mode the project named as its most recurring (`PROJECT.md`, "Structural enforcement replaces declared invariants").

**The right fix.** Every scoring path asserts *something* about the prompt, and the two assertions are logical negations:

```python
def assert_value_in_prompt(tok, question, persona, values):
    """The stuffed-arm twin of assert_no_value_in_prompt. SystemExit if the value is ABSENT.

    Same two levels, inverted: the normalized value MUST appear in the decoded prompt AND its
    encoded id sequence MUST appear as a contiguous run in the prompt ids. A stuffed arm whose
    prompt does not actually carry the fact measures nothing, and would silently report the
    weight condition's number twice.
    """
```

The string half already exists at `phase14_recall.py:1188-1192` as an inline `_prove` in `run_fairness_control`; promote it and add the id-subsequence half (`_is_contiguous_subsequence`, line 392) that the inline version lacks.

**Structural enforcement.** Extend `tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control` (line 425) — which today asserts `persona=` appears at exactly one call site — to a two-file allowlist, and add a new test asserting that **every function that calls `draw_all` is preceded in its own body by exactly one of the two assertions**. That is the AST walk the current test already demonstrates is feasible. Watch it fail before trusting it (the project's stated discipline).

**Trade-off.** Two functions instead of one parameter. That is the point: there is no argument value that produces an unchecked path.

### Pattern 2: Parameterize with the shipped value as default — never a parallel loader

Already established at `phase14_recall.load_adapted_model(device, adapter_path=None)` (line 448), whose docstring states the rationale outright: the calibration driver scores its arm-scoped adapters "through this exact loader instead of a parallel one: the calibration numbers that lock this file's thresholds must come off the same load-before-inject, `weights_only=True` path as the real run."

Apply verbatim to Phase 17: `load_adapted_model(device, adapter_path=P17_ADAPTERS[i])` — no new loader.

Apply to `teach_persona.train_arm`: it is already fully parameterized on `facts`, `family_ids`, `second_person`, `replay_ratio` (line 501). The only two hardcoded couplings are `_require_go_verdict(FACTSET_REPORT)` (line 507) and `arm_outputs(arm)` (line 516). Make the gate-report path the fourth element of `arm_spec`'s return, and extend `arm_outputs`'s naming rule to cover `phase17_*`. Keep `arm_outputs` as the *single* path authority — it is the thing that guarantees no two arms share a path and is CI-tested for pairwise disjointness. A second driver with its own path scheme reopens exactly that.

### Pattern 3: Extract once → committed artifact → figure / prose / statistic

The Phase-15 boundary, verbatim (`extract_deltas.py` → `results/phase15_norms.json` → `plot_phase15.py` + `phase15_stats.py`), enforced by `tests/test_phase15_plots.py::test_plotting_module_never_opens_a_checkpoint` (AST walk over imports + fresh-interpreter probe that fails if `torch` enters `sys.modules`).

**One adaptation for Phase 17.** Phase 15's extractor read weights only — cheap, deterministic, byte-reproducible. Phase 17's extractor *generates*, which is expensive and produces bulk raw evidence. So Phase 17 emits **two** artifacts, and this split is also already precedent (`phase14_transcripts.md` "owns no verdict"; `phase14_recall_report.md` owns that register):

| Artifact | Role | Read by |
|----------|------|---------|
| `results/phase17_isolation.json` | Scalars only. The single source of truth. | plot, stats, report writer |
| `results/phase17_transcripts.md` | Every completion, unfiltered, with prompt ids | humans / audit trail |

The plot reads the JSON and *nothing else*. The report reads the JSON for numbers and quotes transcripts for evidence.

**Also carry re-renderability.** `results/phase14_calibration_results.json` exists specifically so "a wording fix in `write_calibration_report` must never be a reason to re-measure" (`teach_persona.py:928-930`). The Phase-17 JSON must therefore carry everything the *report* needs, not just what the figure needs.

### Pattern 4: Pre-registration by importable constant, verdict by import

`taught_gate`/`heldout_gate` are pure module-level functions over module-level literals (`phase14_recall.py:188-218`); the report writer imports and calls them. `CALIBRATION_DECISION_RULE = (...)` (`teach_persona.py:907`) binds four rule functions into one greppable tuple so `git log -S "CALIBRATION_DECISION_RULE = ("` returns the introducing commit — and `rule_commit_sha()` (line 951) prints it into the report.

Every v3.0 gate follows this shape. Every v3.0 report writer computes its verdict by *calling* the gate function, never by retyping a number into prose.

### Pattern 5: Adapter-swap canary (Phase 17's silent-failure mode)

Scoring M_ij means re-applying adapter *i* onto one injected model N times. The silent failure is that the swap doesn't take and the matrix reports adapter 0's numbers N times — which would look like *perfect isolation on the diagonal and zero cross-leakage*, i.e. the most flattering possible wrong answer.

The canary uses only existing API:

```python
before = lora_state_dict(model)                     # lora/inject.py:67
load_adapter_weights(model, load_adapter(path_i))   # lora/inject.py:76 — key+shape audit first
after = lora_state_dict(model)
# every lora_ tensor must have moved, and must now equal the artifact's tensor exactly
```

This is the `snapshot_params` / canary register from `teach_persona.py:638-652`, reused. No new module.

### Pattern 6: Attack corpus as committed data with named families

`phase18_attacks.py` mirrors `phase14_factset.py`'s `FAMILIES` shape exactly: named generators (`A1` paraphrase, `A2` prefix injection, `A3` role-play, `A4` repeated sampling) with stable ids, rendered per slot from `SLOT_FORMS`, so the allocation is data a test can hold to a contract rather than prose.

**Phase 18 needs zero guard changes.** An extraction attack that already contains the value is not an extraction attack — so `assert_no_value_in_prompt` applies to the *entire* Phase-18 corpus, unmodified. That guard becomes the operational definition of "the attacker does not already know the answer," which is a genuinely stronger framing than a docstring. Pin it with a CPU-only test over the rendered corpus.

**A4 (repeated sampling) is a budget parameter, not a prompt family.** Implement it as a larger `N_ATTACK_SAMPLES` on the other families, not as a fourth prompt shape — otherwise you cannot tell whether a hit came from the phrasing or from the extra draws.

---

## Data Flow

### Phase 16 — the 2×2 (three new cells, one already measured)

```
                        │ prompt EMPTY              │ prompt STUFFED
────────────────────────┼───────────────────────────┼──────────────────────────────
  adapter ON            │ (A) weight-only           │ (C) both sources
                        │ MEASURED — P14 core tiers │ NEW — interference/conflict
────────────────────────┼───────────────────────────┼──────────────────────────────
  adapter OFF           │ (D) closed book           │ (B) prompt-only
                        │ MEASURED — 0/2430         │ NEW as a PAIRED arm
                        │                           │ (P14 fairness, unpaired)
```

```
phase14_factset.LOCKED_FACTS
        │
        ▼ build_question_sets(facts)          [phase14_recall.py:712 — REUSED]
   (taught, held_out, excluded)
        │
        ▼ stamp_seed_indices(arm)             [line 692 — REUSED, now applied to ALL 4 cells]
        │
        ├──► cell A/D: build_recall_prompt(tok, q)         → assert_no_value_in_prompt
        └──► cell B/C: build_recall_prompt(tok, q, persona=[stmt]) → assert_value_in_prompt
                        │
                        ▼ draw_all(model, tok, prompt_ids, device, forbid, item.seed_index)
                        │   ▲▲▲ NOT enumerate() — the defect fix
                        ▼ score_question(completions, fact.value)
                        │
                        ▼ results/phase16_conditions.json  +  phase16_transcripts.md
                        │
                        ▼ weight_advantage_gate(...)  →  phase16_report.md
```

The persona statement for the stuffed cells is `fs.SLOT_FORMS[fact.slot].ans1.format(v=fact.value)` — the exact expression already used at `phase14_recall.py:1114-1117`. Reuse it; do not author new persona text, or the stuffed arm and the taught arm stop being the same sentence.

**`results/phase16_conditions.json` shape:**

```json
{
  "git_sha": "...", "built": "2026-...", "pid": 12345, "wall_clock_utc": "...",
  "adapter": {"path": "checkpoints/persona_adapter.pt", "sha256": "...",
              "base_fingerprint": {...}},
  "base":    {"path": "checkpoints/convbase_slim.pt", "sha256": "..."},
  "instrument": {"source": "scripts/phase14_recall.py",
                 "n_seeded_samples": 8, "temperature": 0.8, "top_p": 0.95,
                 "max_new_tokens": 48, "seed": 1337,
                 "scoring": "contains_value — case-insensitive, whitespace-collapsed substring"},
  "cells": {
    "adapter_on__prompt_empty":   {"k": 496, "n": 1008, "rate": 0.4921,
                                   "by_split": {"taught": [..], "held-out": [..]},
                                   "provenance": "phase14 core tiers, re-run in this process"},
    "adapter_off__prompt_empty":  {"k": 0,   "n": 2430, "rate": 0.0},
    "adapter_off__prompt_stuffed":{"k": ..., "n": ..., "rate": ...},
    "adapter_on__prompt_stuffed": {"k": ..., "n": ..., "rate": ...}
  },
  "per_question": [ {"question": "...", "fact_id": "...", "slot": "...", "split": "...",
                     "seed_index": 7,
                     "adapter_on__prompt_empty":   {"k":.., "n":.., "prompt_ids":[..]},
                     "adapter_off__prompt_stuffed":{"k":.., "n":.., "prompt_ids":[..]} } ],
  "derived": {"weight_advantage": null, "prompt_advantage": null, "interference": null}
}
```

`per_question` carrying **both** prompt id lists is what makes the pairing auditable — a reader can confirm the two conditions differ only in the persona span.

Re-running cells A and D in the same process rather than citing Phase 14's numbers costs ~2× wall clock and buys the thing the phase is about: all four cells from one process, one set of weights, one seed schedule. Cite the Phase-14 numbers as a cross-check in the report, and state loudly if they do not reproduce byte-identically (they may not — Phase 13 measured ~3.6e-8 MPS cross-process drift, `phase14_recall.py:1346`).

### Phase 17 — the isolation matrix

```
phase17_personas.py  ──►  N persona fact sets + declared collisions
        │                 (imports Fact, SLOT_FORMS, FAMILIES from phase14_factset)
        ▼
phase17_persona_gate.py ──► results/phase17_personas_report.md  [HUMAN GO/ADAPT verdict]
        │                    (reuses phase14_factset_gate.probe — same instrument)
        ▼ _require_go_verdict
teach_persona.py  ×N  ──►  checkpoints/phase17_{a,b,c}_adapter.pt   [gitignored]
        │                  data/persona_phase17_*_train{,_mask}.bin [gitignored]
        ▼
phase17_matrix.py  ──►  for i in personas:                    ┐
        │                  load_adapter_weights(model, i)     │  the ONLY
        │                  + swap canary                      │  checkpoint
        │                  for j in personas:                 │  reader
        │                     score(questions_j, values_j)    │
        │                  score under adapter_disabled       ┘  ("none" column)
        ▼
results/phase17_isolation.json  ──┬──► plot_phase17.py   ──► phase17_isolation.png
results/phase17_transcripts.md    ├──► phase17_stats.py  ──► verdict
                                  └──► phase17_report.md
```

**`results/phase17_isolation.json` shape** (one file feeding figure + prose + statistics, per decision 3):

```json
{
  "git_sha": "...", "built": "2026-...", "prereg_commit": "...",
  "instrument": { /* identical block to phase16 — same literals, imported not retyped */ },
  "personas": [
    {"id": "p17_a",
     "adapter": {"path": "checkpoints/phase17_a_adapter.pt", "sha256": "...",
                 "base_fingerprint": {...}, "lora_config": {"r": 8, "alpha": 16.0}},
     "facts": [{"id": "p17a_pet", "slot": "pet_name", "value": "..."}],
     "gate_sha": "<commit of phase17_personas_report.md verdict>"}
  ],
  "collisions": [
    {"kind": "same_value_different_slot", "value": "...",
     "members": [["p17_a", "person_name"], ["p17_b", "pet_name"]]},
    {"kind": "same_slot_contradictory_value", "slot": "pet_name",
     "members": [["p17_a", "..."], ["p17_b", "..."]]}
  ],
  "rows": ["p17_a", "p17_b", "p17_c"],
  "cols": ["p17_a", "p17_b", "p17_c", "none"],
  "matrix": {
    "p17_a": {
      "p17_a": {"k": 0, "n": 0, "rate": 0.0,
                "by_split": {"taught": {"k":0,"n":0,"rate":0.0},
                             "held-out": {"k":0,"n":0,"rate":0.0}},
                "by_slot":  {"pet_name": {"k":0,"n":0,"rate":0.0}},
                "contradictions": 0, "hedging": 0, "n_stopped": 0},
      "p17_b": { ... }, "none": { ... }
    }
  },
  "diagonal_mean": 0.0, "offdiagonal_mean": 0.0, "offdiagonal_max": 0.0,
  "worst_pair": {"i": "p17_a", "j": "p17_b", "rate": 0.0,
                 "selection_rule": "max off-diagonal rate; ties by (row_id, col_id) ascending"},
  "seed_replication": {
    "pair": ["p17_a", "p17_b"], "seeds": [1337, 2337, 3337],
    "rates": [0.0, 0.0, 0.0], "mean": 0.0, "std": 0.0,
    "note": "N training seeds, not N decode seeds — decode seeds are already averaged in `n`"
  },
  "vmax_driver": {"row": "p17_a", "col": "p17_b", "value": 0.0}
}
```

Design notes that matter for the roadmapper:

- **`cols` carries a `"none"` column** — the adapter-disabled negative control per question set. Without it, an off-diagonal hit cannot be distinguished from a base prior. It is the Phase-14 closed-book control, per column.
- **`vmax_driver`** exists so figure and prose read the same extremum (`phase15_norms.json` does exactly this; `plot_phase15.py:28-30` names the reason).
- **`worst_pair.selection_rule` must be committed before the matrix exists.** "The most collision-prone pair" is a choice; a rule chosen after seeing the matrix is the exact move pre-registration exists to prevent.
- **`seed_replication` is over *training* seeds.** Decode seeds are already inside `n`. Replicating decode seeds would answer a question nobody asked.
- **`by_slot` breakdown** is what makes the colliding-name case readable: a cross-hit on the *colliding* slot means something different from a cross-hit on an unrelated slot.

### Phase 18 — the extraction audit

```
phase18_attacks.py (A1 paraphrase / A2 prefix injection / A3 role-play, rendered per slot)
        │
        ▼ assert_no_value_in_prompt over the ENTIRE corpus   [UNCHANGED guard]
        │
        ├──► adapter_disabled(model)  ──► NEGATIVE CONTROL   (attacker without the adapter)
        └──► adapter enabled          ──► ATTACKER
                        │
                        ▼ draw_all(..., N_ATTACK_SAMPLES)  [budget ≥ recall budget]
                        ▼ score_question / contains_value  [same instrument]
                        │
                        ▼ results/phase18_extraction.json + phase18_transcripts.md
```

**`results/phase18_extraction.json` shape:**

```json
{
  "git_sha": "...", "built": "...", "prereg_commit": "...",
  "instrument": { ..., "n_attack_samples": 32, "max_new_tokens": 96,
                  "budget_note": "ATTACK_MAX_NEW_TOKENS = RECALL_MAX_NEW_TOKENS + ATTACK_HEADROOM; RECALL_MAX_NEW_TOKENS is IMPORTED from phase14_recall, never retyped" },
  "target": {"adapter": "checkpoints/persona_adapter.pt", "sha256": "..."},
  "arms": {
    "no_adapter":   {"k": 0, "n": 0, "rate": 0.0, "by_family": {"A1": {...}, "A2": {...}}},
    "adapter_on":   {"k": 0, "n": 0, "rate": 0.0, "by_family": {...}}
  },
  "by_fact": [{"fact_id": "...", "slot": "...",
               "no_adapter": {"k":0,"n":0}, "adapter_on": {"k":0,"n":0},
               "first_success": {"family": "A2", "draw": 11, "prompt_ids": [...]}}],
  "uplift": {"absolute": 0.0, "relative": null,
             "note": "relative is null when the control is exactly 0 — division is undefined and the absolute rate is the honest statistic"},
  "honest_recall_baseline": {"taught": 0.4921, "held_out": 0.3483,
                             "source": "results/phase14_recall_report.md",
                             "note": "an attack that does not beat the honest questioner has extracted nothing the demo does not already show"}
}
```

That last field is the load-bearing framing. The interesting Phase-18 number is not "the attacker got 0.31" — it is **"the attacker got 0.31 where an honest question gets 0.35."** The `uplift` field and the `honest_recall_baseline` field together are what turn the toggle from *authorization* to *availability*, which is the phase's stated reframing.

---

## Build Order

### Cross-phase ordering (dependency-driven, matching PROJECT.md's cost-ascending intent)

```
16 ──► 17 ──► 18
 │      │      │
 │      │      └── consumes: the instrument (16's fixes) + optionally 17's N adapters
 │      └───────── consumes: the instrument; produces the generator + N adapters
 └──────────────── consumes everything; produces nothing new but numbers
```

Phase 16 first is right for a second reason beyond cost: **it is the phase that fixes the shared instrument.** The `enumerate` seed defect and the missing `assert_value_in_prompt` twin are Phase-16 prerequisites that 17 and 18 then inherit already-fixed. Doing 17 first would either duplicate those fixes or ship 17 on an unpaired instrument.

Phase 18 last also lets it consume 17's collision structure as an optional stronger arm (attack adapter A for B's facts) *if* 17's matrix shows any leakage — but do not make 18 depend on that. Single-persona Phase 18 must stand alone.

### Within Phase 16

| Wave | Work | Gate |
|------|------|------|
| 16-01 | Fix `run_fairness_control` seeding: `enumerate` → `item.seed_index`, with the sentinel refusal `run_scored_recall` already uses. Its own commit, its own test. | Test that fails on the old code |
| 16-02 | Add `assert_value_in_prompt` (both levels). Extend the AST scoping test to the two-assertion contract. Watch both fail before trusting. | CPU-only tests green |
| 16-03 | **Pre-registration commit**: `phase16_weight_vs_prompt.py` with all gates, framing constants, `ERASURE_DECISION_RULE` import, and a `main()` that provably cannot produce a number yet | `git log -S` proof; no artifact exists |
| 16-04 | Commit `scripts/erasure_gate.py` (see below). Can land in 16-03; keep separate so its ordering is unambiguous. | |
| 16-05 | Run the four cells; write `phase16_conditions.json` + `phase16_transcripts.md` | Clobber guard; both assertions fire |
| 16-06 | `phase16_report.md`, verdict computed by importing the gates | Human verdict recorded |

### Within Phase 17

| Wave | Work | Gate |
|------|------|------|
| 17-01 | `phase17_personas.py` — N=3 personas, collisions declared **as data**, teaching grammar imported from `phase14_factset` | Test: declared collisions actually collide; grammar not forked; no value equals a `BASE_PRIOR_SEEDS` entry |
| 17-02 | `phase17_persona_gate.py` (+ `_probe` → `probe` rename) → `results/phase17_personas_report.md` | **Human GO/ADAPT verdict** — hard blocker |
| 17-03 | Extend `teach_persona.ARMS` / `arm_spec` / `arm_outputs`; gate report becomes part of the arm spec | Path-disjointness test still green for every arm pair |
| 17-04 | Train N adapters | `refuse_if_exists` on all five targets; canary green per arm |
| 17-05 | **Pre-registration commit**: `phase17_matrix.py` gates + `worst_pair.selection_rule` + `phase17_stats.py` rule | `git log -S` proof; no matrix exists |
| 17-06 | Run the matrix (N×(N+1) cells) → `phase17_isolation.json` + transcripts | Swap canary per cell |
| 17-07 | `plot_phase17.py` + the no-checkpoint AST/fresh-interpreter test | Watch the guard fail before trusting |
| 17-08 | Seed-replicate the worst pair (rule-selected, not eyeballed) | Selection computed by importing the rule |
| 17-09 | `phase17_report.md` | Human verdict |

**Ordering note:** 17-05 (pre-registration) must land *before* 17-06 but may land any time after 17-01, since it depends only on knowing what will be measured, not on the adapters existing. Landing it early (parallel with 17-03/17-04) shortens the critical path and strengthens the git-order proof.

### Within Phase 18

| Wave | Work | Gate |
|------|------|------|
| 18-01 | `phase18_attacks.py` — attack families as data | Test: no rendered attack prompt contains any locked value, at string AND id level |
| 18-02 | **Pre-registration commit**: budgets (`ATTACK_MAX_NEW_TOKENS` derived from the *imported* `RECALL_MAX_NEW_TOKENS`), `N_ATTACK_SAMPLES`, gate, both verdict branches | `git log -S` proof |
| 18-03 | Run negative control + attacker → `phase18_extraction.json` + transcripts | `assert_no_value_in_prompt` over the whole corpus |
| 18-04 | `phase18_report.md` — the availability-not-authorization reframing, verdict by import | Human verdict |

---

## Phase 19 Pre-Registration (the gated decision)

**The requirement:** the erasure go/no-go criteria must precede the 16-18 data without planning Phase 19 itself.

**Where:** `scripts/erasure_gate.py`, committed at Phase-16 open. Phase-neutral and dependency-free — `no torch, no fact set` — following the `_verdict.py` register exactly, so cheap drivers and CPU-only tests both import it.

**Why one file rather than three per-phase blocks:** a rule split across 16/17/18 cannot be read whole, and `git log -S` would produce three separate orderings a reader must reconcile. One file, one commit, three importing consumers, one greppable tuple definition.

**Shape** (the `CALIBRATION_DECISION_RULE` register, `teach_persona.py:709-912`):

```python
# ===== ERASURE_DECISION_RULE — committed BEFORE any Phase-16/17/18 number exists =====
#
# git log -S "ERASURE_DECISION_RULE = (" -- scripts/erasure_gate.py returns a commit that
# provably predates results/phase16_conditions.json, phase17_isolation.json and
# phase18_extraction.json. Every literal below carries its provenance in its own comment.
#
# The BASELINE numbers referenced here are v2.0 PUBLISHED figures (taught 0.4921, held-out
# 0.3483, adapter-off control 0/2430, retention PPL 3.891140) — already in
# results/phase14_recall_report.md and results/phase13_ab_report.md at the time this rule is
# written. Referencing them is not data-peeking on 16-18; referencing any 16-18 number would be.

WEIGHT_ADVANTAGE_FLOOR = ...   # below this, weights buy little over prompting and erasure
                               # is solving a problem the architecture does not have
ISOLATION_LEAK_TRIGGER = ...   # off-diagonal rate above which cross-persona leakage is real
EXTRACTION_UPLIFT_TRIGGER = ...# attacker-minus-control above which the toggle is availability-
                               # only in a way that MATTERS, not merely in principle

def erasure_worth_attempting(weight_advantage, offdiagonal_max, extraction_uplift) -> bool:
    """True iff at least one of the three v3.0 measurements shows erasure would buy something.

    Boundary: strict `>` on every trigger — exactly at a trigger does NOT fire, the
    replay_required/first_person_wins register (teach_persona.py:873,889), with the same
    RATIO_DECIMALS rounding so 'exactly at the trigger' means the decimal value.
    """

def erasure_must_beat(taught_rate_before, heldout_rate_before) -> tuple[float, float]:
    """The post-erasure recall CEILING erasure would have to get under to count as erasure.

    Not zero: the adapter-off control already measures 0/2430, so 'erasure' that merely
    reaches the control has removed the adapter, not the fact. The ceiling is a fraction of
    the measured pre-erasure rate, so a rate that stays above it is a FAILED erasure however
    small the drop looks.
    """

def erasure_must_preserve(retention_ppl_before, other_fact_rates_before) -> tuple[float, float]:
    """The collateral FLOOR: what erasing one fact may NOT cost.

    Two halves, because erasure has two ways to cheat: destroy the conversational base
    (masked dialogue-val PPL, the frozen Phase-12 gate metric) or destroy the OTHER taught
    facts (their recall rate). An 'erasure' that forgets everything is a lobotomy.
    """

ERASURE_DECISION_RULE = (
    erasure_worth_attempting,
    erasure_must_beat,
    erasure_must_preserve,
)
```

**Why this does not plan Phase 19.** The rule names only (i) what number would make erasure worth attempting and (ii) what number erasure would have to beat and preserve — both expressible entirely in metrics 16-18 already produce plus v2.0's published baselines. It names no mechanism, no schedule, no adapter surgery, no rank-subtraction, no phase plan. That separation is exactly what makes it committable now.

**How it stays honest.** Each of the three phase report writers imports `erasure_gate` and prints the *inputs* it contributes into its own report (`phase16_report.md` prints its `weight_advantage`, etc.). The final go/no-go is then a single call over three committed numbers, computed by importing, never retyped. If the verdict is NO-GO, that is recorded unamended per the v2.0 continuation discipline.

---

## Compute and Budget Considerations

| Phase | Rough cost on M3/MPS | What dominates | Lever if it overruns |
|-------|---------------------|----------------|----------------------|
| 16 | ~2-3× Phase 14's scored run (4 cells vs Phase 14's effective 2 + controls) | Decode: 4 × ~270 questions × 9 draws × 48 tokens | Drop the soft tier from the stuffed cells — it already feeds no gate (`SOFT_TIER_SECTION`) |
| 17 | N training runs (~minutes each, 200 steps) + N×(N+1) scoring cells | Scoring, badly — at N=3 that is 12 arms ≈ 3× Phase 14 | **Cut the soft tier, never the draws.** `N_SEEDED_SAMPLES` must stay imported from `phase14_recall` so the matrix and the headline come off one instrument |
| 18 | 2 arms × attack corpus × `N_ATTACK_SAMPLES` (deliberately larger than 8) | Repeated sampling by design | Narrow the fact set to the core 8; never narrow the draws — draws *are* the attack |

**Opinionated call: N=3, not 4.** The matrix cost is N×(N+1); 3→4 is a 60% increase in the most expensive phase for one extra row. Three personas already support both collision kinds (same-value/different-slot and same-slot/contradictory-value) and a worst-pair selection. If the roadmapper wants 4, it should be a pre-registered decision with the extra pair's purpose named, not a round number.

**Never lower `N_SEEDED_SAMPLES` to buy wall clock.** A decode setting chosen to make a number look better is the same category of error as a threshold chosen after seeing results — the project says this outright at `phase14_recall.py:156-158`. Cut the question set, keep the instrument.

---

## Anti-Patterns

### Anti-Pattern 1: The bypass flag on the leakage guard

**What people do:** `assert_no_value_in_prompt(..., skip=True)` or `run_scored_recall(..., stuffed=True)` for the prompt-stuffed arm.
**Why it's wrong:** it turns a structural invariant into a runtime argument. The clean-room path's protection now depends on a default nobody re-reads, and the AST test that currently proves `persona=` has exactly one call site no longer proves anything about whether the guard ran.
**Do this instead:** Pattern 1 — two symmetric assertions, neither with a skip mode, plus an AST test that every `draw_all` caller is preceded by exactly one of them.

### Anti-Pattern 2: A parallel scoring path for the new phases

**What people do:** copy `normalize`/`contains_value`/`score_question` into `phase17_matrix.py` "because importing a 1981-line driver feels wrong."
**Why it's wrong:** the entire value of M_ij is that it is measured with the instrument that produced the 0.4921 headline. Two copies of a substring rule diverge silently the first time either is touched, and then the matrix and the headline are no longer comparable — exactly the WR-01 failure already recorded in this repo (`teach_persona.py:143-150`), where two `masked_perplexity` call sites differed by one argument and were described as one instrument.
**Do this instead:** import from `phase14_recall`. The import edge points **new phase → phase14_recall, never back** (a back-edge would drag fact strings into the demo's address space through the LAZY-IMPORT boundary).

### Anti-Pattern 3: A committed heatmap whose inputs are gitignored

**What people do:** `phase17_matrix.py` loads checkpoints, computes the matrix, and calls `plt.imshow` in the same process.
**Why it's wrong:** the PNG becomes an assertion nobody with a fresh clone can regenerate — the exact hazard `PROJECT.md`'s decision 3 names.
**Do this instead:** Pattern 3, with the `test_plotting_module_never_opens_a_checkpoint` guard ported. Watch it fail before trusting it.

### Anti-Pattern 4: Choosing the "worst pair" after seeing the matrix

**What people do:** run the matrix, look at it, pick the most interesting pair, replicate it across seeds.
**Why it's wrong:** the replication then confirms a pair selected for being extreme, which is regression-to-the-mean bait. The reported replication std is not the std of a randomly chosen pair.
**Do this instead:** commit `worst_pair.selection_rule` as an importable pure function before the matrix exists, and have the report compute the selection by calling it.

### Anti-Pattern 5: Scoring Phase 17 without a per-column adapter-off control

**What people do:** an N×N matrix with no `"none"` column.
**Why it's wrong:** an off-diagonal hit could be persona-B leakage into adapter A, or it could be the frozen base's own prior (`BASE_PRIOR_SEEDS` records that this base answers `rose` for pet names and `red` for colors unprompted). Without the control column those are indistinguishable, and the more alarming reading is the one a reader will take.
**Do this instead:** N×(N+1). The extra column costs one adapter-disabled pass and is the difference between a measurement and a rumor.

### Anti-Pattern 6: Teaching Phase-17 personas on an ungated fact pool

**What people do:** invent three colliding personas and train immediately, since the Phase-14 gate "already validated the method."
**Why it's wrong:** the gate validates *values*, not methods. A base-guessable value scores on every adapter including the ones that were never taught it, which reads as catastrophic cross-persona leakage and is actually a bad fact. The diagonal becomes uninterpretable too.
**Do this instead:** 17-02 is a hard blocker with a human-recorded verdict, reusing `phase14_factset_gate.probe` so the guessability measurement is the same instrument that locked the Phase-14 set.

### Anti-Pattern 7: Extracting scoring into `src/personacore/audit/`

**What people do:** "three consumers means it belongs in the package."
**Why it's wrong for *this* project:** the scoring rule is pre-registered evidence machinery, and `phase14_factset.py:7-8` states the policy directly — rules live in the committed driver, "not in the package where the driver could drift away from them." Moving it also gives the rule a new file with a new git history, weakening the one thing that makes the pre-registration checkable.
**Do this instead:** leave it. Revisit only if a *fourth* consumer appears that cannot import a driver (none is foreseen).

---

## Integration Points

### Internal Boundaries

| Boundary | Direction | Mechanism | Notes |
|----------|-----------|-----------|-------|
| `phase16/17/18 → phase14_recall` | one-way | `import phase14_recall` (sibling; `scripts/` is `sys.path[0]`) | **Never a back-edge.** `phase14_recall` is imported by `personalize_demo` and its import-time surface is integers only. |
| `phase17_personas → phase14_factset` | one-way | `from phase14_factset import Fact, SLOT_FORMS, render_family, SLOT_QUESTION_BANK` | Teaching grammar reused so adapters are comparable. Do not fork. |
| `phase17_persona_gate → phase14_factset_gate` | one-way | `from phase14_factset_gate import probe, PROBE_SEEDS, PROBE_MAX_NEW_TOKENS, SEED, TEMPERATURE, TOP_P, STOP_IDS` | Requires the `_probe → probe` rename. Never retype the constants. |
| `phase17_matrix → teach_persona` | one-way | arm path lookup via `arm_outputs` | Keep `arm_outputs` the single path authority. |
| `plot_phase17 → phase17_isolation.json` | one-way, torch-free | `json` only | Enforced by AST walk + fresh-interpreter probe. |
| `16/17/18 report writers → erasure_gate` | one-way | `from erasure_gate import ERASURE_DECISION_RULE` | Verdict by import, never retyped. |
| `phase18_extract → phase14_recall.RECALL_MAX_NEW_TOKENS` | one-way | import the integer, derive the attack budget from it | Retyping 48 would let the attack budget silently drift from the recall budget it must exceed. |

### Import-topology hazard (carried forward from Phase 14)

`phase14_recall` holds a documented LAZY-IMPORT RULE: `phase14_factset` and `teach_persona` are imported *inside functions*, never at module level, so `personalize_demo` can import `RECALL_MAX_NEW_TOKENS` without a single locked fact string entering the demo process. `tests/test_phase14_scoring.py::test_no_fact_strings_at_import` enforces it.

**Consequence for v3.0:** if any new module ends up on an import path reachable from `personalize_demo`, its module-level surface must be fact-free too. As specified above none is — the edges all point *into* `phase14_recall`, not out of it. If a future v3.0 demo panel is added, extend `test_no_fact_strings_at_import` to the new modules **before** wiring it, not after.

### Filesystem boundaries

| Path | Tracked? | v3.0 additions |
|------|----------|----------------|
| `results/` | git-tracked | 3 JSON, 3 transcripts, 3 reports, 1 PNG, 1 gate report |
| `checkpoints/` | gitignored | N Phase-17 adapters + latest.pt + seed-replication adapters |
| `data/` | gitignored | N Phase-17 bin pairs |
| `artifacts/tokenizer.json` | git-tracked, **FROZEN** | untouched — and the tokenizer retrain question is explicitly out of v3.0 scope |

Because `checkpoints/` is gitignored, every v3.0 JSON must carry `sha256` per adapter (the `phase14_recall._sha256` precedent, line 434) so a reported number traces to the weights that produced it.

---

## Test Surface (CPU-only, GPU-free — the 408-test contract)

New tests are all cheap and all structural. None needs a GPU or a checkpoint.

| Test | Asserts | Why it matters |
|------|---------|----------------|
| `test_two_assertion_contract` | Every `draw_all` caller in the instrument is preceded by exactly one of the two prompt assertions (AST) | The guard-inversion is structural, not conventional |
| `test_persona_call_sites` (extended) | `persona=` appears only at the fairness control and the Phase-16 stuffed arm | Existing test, widened |
| `test_seed_pairing` | `run_fairness_control` reads `item.seed_index`, not `enumerate` | Pins the 16-01 fix |
| `test_collisions_actually_collide` | Every declared collision in `phase17_personas` is realized in the rendered fact values | A "colliding" persona set that doesn't collide measures nothing |
| `test_grammar_not_forked` | Phase-17 rendering equals `phase14_factset.render_family` output for the same `Fact` | Comparability with `persona_adapter.pt` |
| `test_phase17_paths_disjoint` | No two arms (Phase 14 + Phase 17) share any output path | Extends the existing `arm_outputs` disjointness test |
| `test_plot_phase17_never_opens_a_checkpoint` | AST: no torch import, no `.pt` literal; fresh interpreter: torch never enters `sys.modules` | Port of the Phase-15 guard |
| `test_attack_corpus_is_value_free` | No rendered attack prompt contains any locked value (string + id level) | Makes "the attacker doesn't know the answer" a checked fact |
| `test_erasure_rule_boundaries` | Each `erasure_gate` predicate's boundary behavior (strict `>` etc.) | The `test_gate_boundary` register |
| `test_artifact_schema` ×3 | Each JSON carries every field the plot/stats/report read | A truncated artifact that still renders is `T-15-07` |

---

## Open Questions for the Roadmapper

1. **N=3 vs N=4 personas.** Recommended N=3 on cost. If 4, the fourth persona's purpose must be pre-registered (e.g. "a persona with *no* collisions, as the isolation-matrix's own negative control row").
2. **Does Phase 16 re-measure cells A and D, or cite Phase 14?** Recommended re-measure (all four cells from one process). Costs ~2× wall clock; buys the pairing the phase is about. The roadmapper should make this an explicit phase decision because it doubles the run.
3. **Does Phase 18 attack the Phase-17 personas too?** Recommended no for the core phase — keep 18 single-persona and standalone. Make it an optional appendix arm conditional on 17 showing leakage.
4. **Does Phase 17 gate, or report descriptively?** The v2.0 discipline is "gate only the part the sample size supports." At N=3 the off-diagonal has 6 cells; a gate on the *mean* off-diagonal is thin. Recommended: **gate the diagonal-vs-off-diagonal sign** (isolation exists at all) and report the magnitude descriptively — the exact split Phase 15 used for its ρ at n=36.
5. **Attack-corpus size and the multiple-comparisons problem.** More attack families × more draws mechanically raise the chance of at least one hit. If the report's headline is "the attacker succeeded," the number of attempts must be in the headline too. Pre-register the denominator.

---

## Sources

**Primary (HIGH confidence — read directly at commit `829cd5f`):**
- `scripts/phase14_recall.py` (1981 lines) — the scoring instrument, the guard, the fairness control, the three D-11 controls, the report register
- `scripts/teach_persona.py` (1734 lines) — arm parameterization, `CALIBRATION_DECISION_RULE` pre-registration register, canary discipline
- `scripts/phase14_factset.py` (848 lines) — committed-data-surface register, teaching grammar, `SLOT_FORMS`, `BASE_PRIOR_SEEDS`
- `scripts/phase14_factset_gate.py` — guessability measurement, clobber guard
- `scripts/extract_deltas.py`, `scripts/plot_phase15.py`, `scripts/phase15_stats.py` — the extract/plot/verdict three-file boundary
- `scripts/_verdict.py` — the one anchored `## Verdict` read
- `src/personacore/lora/inject.py`, `src/personacore/dialogue/serialize.py`, `src/personacore/checkpoint.py` (signatures)
- `results/phase15_norms.json` (inspected structure) — the artifact-shape precedent
- `tests/test_phase14_scoring.py::test_persona_argument_is_scoped_to_the_fairness_control` — the AST-scoping precedent
- `.planning/PROJECT.md` — the five load-bearing v2.0 decisions

**Secondary (LOW confidence — external, and only loosely applicable):**
- StolenLoRA / LoRA extraction literature ([arxiv.org/pdf/2509.23594](https://arxiv.org/pdf/2509.23594), [emergentmind.com/topics/lora-extraction](https://www.emergentmind.com/topics/lora-extraction)) — concerns *model stealing* (reconstructing the adapter via synthetic-data distillation), **not** targeted fact extraction. Do not cite it as prior art for Phase 18 without reading it; the framing differs.
- LoRA memorization reduction in federated settings ([arxiv.org/html/2502.05087v1](https://arxiv.org/html/2502.05087v1)) — reports LoRA reducing instance-level memorization up to ~10×. Directionally relevant to Phase 18's expected result (a low extraction rate may be a LoRA property, not a PersonaCore achievement) and worth a threats-to-validity line, but it is a different scale and setting.

**Gap, stated honestly:** the closest real prior art for Phase 18 is the memorization-auditing / canary-exposure literature (Carlini et al. extraction, Secret Sharer), which this research did not verify against current sources. That grounding belongs in FEATURES/PITFALLS, not here, and the roadmapper should flag Phase 18 as needing phase-specific research before its pre-registration commit — the attack taxonomy and the denominator discipline are exactly where a wrong prior costs the most.

---
*Architecture research for: adversarial privacy audit of weight-resident memory, integrated into a shipped from-scratch LM stack*
*Researched: 2026-08-12*
