# Phase 14: Teach-Then-Recall Demo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-01 (two passes — the second reopened the file to cover the demo surface)
**Phase:** 14-Teach-Then-Recall Demo
**Areas discussed:** Fact set & tokenizer pre-flight; Thresholds, scoring & controls; Teaching
grammar & held-out split; Demo surface & clean-room evidence
**Areas remaining:** none — all four gray areas decided

---

## Area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Fact set & tokenizer pre-flight | Which 5–10 facts and how they survive the 547-live-id tokenizer | ✓ |
| Teaching grammar & held-out split | Template families, paraphrase count, replay mix | ✓ (later) |
| Thresholds, scoring & controls | Pre-registered gate, scoring rule, control set | ✓ (later) |
| Demo surface & clean-room evidence | Teach-in-UI vs toggle-only, script placement, context dump | |

**User's position, stated before options appeared:** fact values must be adversarially chosen so
the base-without-adapter control FAILS to guess — TinyStories-common names are structurally unsafe
regardless of token-count convenience, because the base has real prior probability mass on exactly
those tokens and a "successful recall" could be coincidence rather than memory. Distinctive or
invented values are correct even if they fragment into more tokens: tokenizer cost is a nuisance,
guessability is a validity failure of the whole demo. Two pre-flights required before locking —
tokenizer census confirmed by direct encode/decode, and a base-model guessability pre-check run
before teaching anything (the direct analog of Phase 11's `self_revised` anti-leakage check,
applied to prior-knowledge rather than corpus-lexical leakage). Survivor counts reported; a set
shrinking below what DEMO-06 needs is information brought back *before* locking.

---

## Fact set & tokenizer pre-flight

### Q1 — Guessability rejection rule

| Option | Description | Selected |
|--------|-------------|----------|
| Zero-tolerance exact match | Binary, pre-registerable, no threshold to argue; blind to near-misses | |
| Exact match + recorded human "close" call | Mechanical floor plus a documented semantic-proximity tier | ✓ |
| First-token probability bar | Most sensitive; threshold has no defensible source at 13.9M params | |

**Notes:** the close-call tier exists for the failure mode exact-match structurally cannot see.
Every close-call rejection must quote the specific base completion that triggered it, in the same
committed report register as everything else locked in this project. Explicitly framed as the same
asymmetric-risk logic that put λ=0.01 ahead of λ=0 for Phase 12 production: a slightly less
mechanically pure gate that catches the failure mode actually threatening credibility beats a
cleaner gate blind to it.

### Q2 — Fact category mix

| Option | Description | Selected |
|--------|-------------|----------|
| Proper-noun / identifier facts only | Highest survival; persona reads narrow | |
| Mixed set with OOD values in every slot | Rounded persona; low-cardinality slots die by attrition anyway | |
| Proper-noun core + small labelled soft tier | Gated core plus a separately reported non-gating tier | ✓ |

**Notes:** the soft tier's exclusion must be labelled with the same explicitness as Phase 12's
"post-verdict, discretionary" framing — a named report section, not a footnote — stating what it
is for and what it does not contribute. That turns a possible hedge into the same disciplined
honesty applied everywhere else a clean single-number claim was unavailable.

*Context Claude surfaced:* the close-call rule systematically punishes low-cardinality slots, since
the base carries prior mass on *some* color/food and a near-miss there is textbook
same-category/right-slot.

### Q3 — Gate shape

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone gated plan (11-03 precedent) | Committed script + report + blocking verdict | |
| Standalone gated plan + permanent CPU test | Adds a forever regression test on the tokenizer half | ✓ |
| Folded into the teaching-set builder plan | Fewer plans; risks the mid-phase discovery to be avoided | |

**Notes:** the CPU test's docstring must state explicitly why only the tokenizer half is permanent
— the guessability measurement is checkpoint-specific to `convbase_best.pt`'s learned priors and
has no meaning as a standing invariant; a future checkpoint needs a fresh gated measurement, not a
test re-run. Prevents a future reader assuming the permanent test covers the full discipline when
it structurally cannot.

### Q4 — Origin of the gate's recall questions

| Option | Description | Selected |
|--------|-------------|----------|
| Gate probes reserved as held-out phrasings | Probes banned from teaching, become proven-base-failing held-out seeds | ✓ |
| Throwaway probes, independent of scoring | Cleaner separation; gate completions never become evidence | |
| Author core-slot grammar first, then gate | One measurement; inverts the locked order, risks rework | |

**Notes:** each reserved probe must carry base-failure provenance into the DEMO-06 report — held
out AND measured base-failing at gate time, commit SHA, with the base completion quoted. That is
the payoff over a throwaway set: the split is proven unguessable, not assumed. SC2's scoring-time
control still re-runs on the full final question set as independent confirmation.

### Q5 — Token-count band

| Option | Description | Selected |
|--------|-------------|----------|
| Pin the band | Settle the ceiling and reject-vs-record posture | ✓ |
| Leave to Claude's discretion | Guided by measured data and the stated ordering | |

**Notes:** token count is a census field, never a reject — only the guessability verdict can
disqualify a candidate. The one place it becomes a real constraint is the demo's generation budget,
an engineering constraint of the demo surface, to be named as such there and never used as a proxy
for guessability.

*Measurement Claude ran against the frozen tokenizer and reported before Q1:* the `forbid_ids`
sub-filter from PITFALLS-12 is structurally unfireable (all 256 byte ids live; BPE falls back to
bytes, so `encode()` can never emit a dead id). And cheap tokenization is the warning sign, not the
reward — `Max`/`Lily` cost 1 token *because* they are frequent in the fixture, while short invented
names cost 3–4 and `blue` already costs 4.

---

## Thresholds, scoring & controls

### Q1 — Threshold pre-registration

| Option | Description | Selected |
|--------|-------------|----------|
| Blind literal constants (Phase-13 shape) | Maximum purity; risks an honest negative on the headline deliverable | |
| Pre-register the procedure (Phase-12 shape) | Calibration protocol committed first, then threshold locked | ✓ |
| Blind bar + measured ceiling beside it | Purity plus descriptive context; two runs and a reporting split | |

**Notes:** the throwaway calibration fact set must pass the *same* pre-flight gate — disposable as
an evidence source but not exempt from the validity discipline, since guessable calibration facts
produce an inflated, meaningless ceiling. The derivation rule is written down before calibration
runs, same blind-margin discipline as `k=2` in Phase 12's noise floor.

### Q2 — Scoring rule

| Option | Description | Selected |
|--------|-------------|----------|
| Substring hit over greedy + N seeds, k/N | Mechanical; blind to contradictions | |
| Substring hit AND no contradicting value | Catches unresolved facts; needs a curated competing-values list | |
| Substring hit, contradictions reported separately | Mechanical gate + named descriptive metric | ✓ |

**Notes:** contradiction detection must be mechanical where feasible (second candidate proper
noun/number in the same slot via the fact-set tokenizer census; or hedging plus a second value) —
not a hand-curated per-slot list, since avoiding that editorial judgment was the reason option 2
was rejected. If no mechanical detector is feasible, fall back to a human-reviewed count under the
same quoted-evidence discipline as the close-call rejections: traceable to exact completion text,
never an unlogged tally.

### Q3 — Controls (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| Question-fairness check (base + fact in prompt) | Validates question set; distinct from deferred DEMO-F2 | ✓ |
| No-collateral-collapse check | Adapter has not become a single-topic persona parrot | ✓ |
| Adapter-off round-trip bit-identity | Toggle correctness measured on real weights, not inherited from fixtures | ✓ |

**Notes:** each control's report section must open by naming the specific ambiguity or failure mode
it closes — question validity / persona collapse / toggle correctness — not present as a list of
extra measurements. Mirrors Phase 13's reconciliation discipline and the close-call framing. Every
control earns its place by naming the gap it closes, not by existing as generic rigor.

### Q4 — Gate-miss policy

| Option | Description | Selected |
|--------|-------------|----------|
| Phase-12 verbatim: negative stands, override logged separately | Strongest continuity with established discipline | ✓ |
| One pre-registered retry with a named knob | Bounded recipe retry; weaker commitment to a strict reader | |
| Miss blocks the phase pending a fresh discuss pass | Maximum caution; heavy for an expected, recipe-driven failure | |

**Notes:** any subsequent ship decision goes in a section with the exact register of Phase 12's
"Production Config Decision — post-verdict, discretionary": separate, dated after the verdict,
explicit that it does not reopen the threshold — rather than introducing a new discipline because
this is the demo fewest readers get past the headline of.

---

## Teaching grammar & held-out split

**User's position, stated before options appeared:** held-out means entirely held-out template
FAMILIES, not new instances within taught families — testing internalization independent of
phrasing structure is the claim DEMO-06 actually needs, and it is the same "prove the strong
version unless cost is prohibitive" logic behind every prior choice. Paraphrase-count and replay
decisions must be resolved with explicit reference to how they interact with the
no-collateral-collapse control, not decided independently and checked for compatibility afterward.

### Q1 — Family allocation

| Option | Description | Selected |
|--------|-------------|----------|
| Learning-weighted: most families taught | Maximizes generalization pressure; coarse held-out score | |
| Balanced family split | Finer held-out score; less generalization pressure | |
| Derive allocation from the calibration run | Reuses the procedure-pre-registration machinery | ✓ |

**Notes:** the pre-calibration decision rule must specify how family allocation is derived, not
just the threshold — scaling taught families down if recall saturates early, or held-out families
up if family-level variance is high, even against the literature's ~10-per-fact figure. The
calibration set's own family structure must mirror a reasonable guess at the real set's likely
final shape so the same run answers both questions honestly.

### Q2 — PersonaChat replay

| Option | Description | Selected |
|--------|-------------|----------|
| Decide off the calibration run | Replay becomes a measured answer, not a third guess | ✓ |
| Always mix at a pre-registered ratio | Simple; an unmeasured constant that may dilute recall needlessly | |
| No replay; let the control report the outcome | Cheapest; the fix would land after the fact | |

**Notes:** the calibration run must include a paired with-replay vs without-replay arm on the exact
no-collateral-collapse metric, with a pre-written collapse-magnitude threshold above which replay
becomes mandatory. No meaningful collapse signal without replay → the real run proceeds without it,
preserving the full teaching signal rather than diluting against an unconfirmed risk. Net effect:
one calibration run answers threshold, family allocation, and replay from one measured source.

---

## Demo surface & clean-room evidence

*(Second pass. Claude noted up front that PITFALLS-11 step 1 is literally "save adapter; kill the
process", so an in-UI Teach tab puts teaching and recall in the same process — the exact condition
the protocol excludes.)*

### Q1 — Demo scope

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle + Reset, adapter trained offline | Clean room inherited by construction; smallest surface | ✓ |
| Full Teach / Chat / Reset Blocks | Best demo moment; training in a callback, clean room must be re-proved | |
| Toggle + Reset now, Teach tab as stretch | Keeps upside available; stretch items become expectations | |

**Notes:** the "no watch-it-learn moment" cost is accepted as the correct trade, not a compromise —
option 2 would require re-proving clean-room after the fact (a process restart before recall
counts), undermining exactly the claim SC4 exists to demonstrate. Option 3 explicitly rejected:
decision closed fully, no expectation left to manage later.

### Q2 — Demo file placement

| Option | Description | Selected |
|--------|-------------|----------|
| New standalone `scripts/personalize_demo.py` | M1 demo untouched and reproducible; boilerplate duplicated | ✓ |
| New script + extract shared setup into the package | Removes drift risk; refactors a frozen v1.0 artifact | |
| Extend `demo_app.py` with an adapter mode | Least code; breaks the 08-UI-SPEC honesty lock and the Phase-8 GIF/README | |

**Notes:** since option 1 duplicates rather than extracts, add a CPU-only regression test asserting
the two scripts' `forbid_ids` mask **tensors** match — same mask-building call, same source
function, compared directly rather than trusting visual code similarity. Same register as Phase
12's WR-04 duplicated-`cap_persona` fix, except the fix is a shared test rather than a shared
function precisely because `demo_app.py` must stay literally untouched. Extend the same treatment
only to duplicated boilerplate with a named anti-pattern attached; generic duplication does not
need its own test, `forbid_ids` does because Anti-pattern 7 names it.

### Q3 — Context-token dump placement

| Option | Description | Selected |
|--------|-------------|----------|
| Both — committed harness evidence + live UI panel | Auditable in the repo and visible in the demo | ✓ |
| Scripted harness only | Satisfies SC2; the demo asks to be trusted | |
| Live UI panel only | Ephemeral screen state; nothing in the repo proves the scored run's clean room | |

**Notes:** the UI panel must render from the exact same prompt-construction function the harness
calls, never a parallel reimplementation, with a regression test asserting displayed ids and
committed dump are byte-identical for the same input. Same failure mode as Q2 under a different
name: two code paths claiming to prove the same thing, true only if enforced structurally.

### Q4 — Generation budget

| Option | Description | Selected |
|--------|-------------|----------|
| Derived constant + hard fit guard; UI slider floors at it | Traceable to the census; no UI setting can fake a false negative | ✓ |
| Single derived constant everywhere, no slider | Maximally reproducible; loses the M1 slider affordance | |
| Round constants, census as post-hoc assertion | Simplest; a fact-set change can silently shrink headroom | |

**Notes:** the derivation and its headroom margin must be committed as an auditable computation —
census, formula, resulting constant, in one place a future reader can re-derive without re-running
anything. Not a number derived in a chat log, not a comment saying "trust this"; the same
discipline applied to every other locked number in this phase.

---

## Claude's Discretion

- Loss masking for the teaching run (PITFALLS-14 reverses Phase 12's unmasked verdict by design —
  the planner must say so explicitly and cite it)
- Teaching-data materialization: in-memory masked batches vs on-disk bins
- Adapter training recipe: LR, batch size, deliberate-overfit step budget (`weight_decay=0.0`
  carries over from `train_adapter_smoke.py`)
- EWC penalty during the teaching run (expect `penalty_fn=None`; planner states the reasoning)
- Candidate pool size entering the pre-flight gate
- File/module naming, test organization, report table shapes

## Deferred Ideas

- **In-UI Teach tab (ARCHITECTURE §Stage 3)** — CLOSED on the merits, not deferred. Recorded so its
  absence is not later mistaken for an oversight or revived as a stretch goal.
- DEMO-F1 two-persona adapter swap — already a Future Requirement
- DEMO-F2 prompt-stuffed comparative baseline — already a Future Requirement; the question-fairness
  control is deliberately narrower and must be labelled to keep them distinct
- Merged-slim export path — carried from Phase 9; merging destroys the toggle, so not needed here
