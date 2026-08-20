# Phase 18: Black-Box Adversarial Extraction Audit - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-15
**Phase:** 18-black-box-adversarial-extraction-audit
**Areas discussed:** Attack corpus provenance, Prefix-injection budget, Instrument scope, SC5 landing, Threat-model table

---

## Attack corpus provenance

### Family zero's harness-sanity assertion

| Option | Description | Selected |
|--------|-------------|----------|
| Exact hit-vector equality | Assert the 112-question hit vector row-for-row; 496/1008 derived, not asserted | ✓ |
| Exact aggregate, per-question descriptive | Gate on 496/1008; publish the row diff as descriptive | |
| Pre-registered tolerance band | What ATK-03/SC2 literally asks for — a band around 0.4921 | |

**User's choice:** Exact hit-vector equality → **D-01**
**Notes:** User opened the area stating both positions before options appeared: that A1/A2/A3 transform the fixture's existing questions rather than introducing a new corpus, and that family zero must be the unmodified `core_taught` (112) as a bit-for-bit re-scoring. Both were checked. The transformation reading holds. The anchor number did not: the user proposed banding against 0.487302, which is the **pooled** taught split (112 core + 28 soft) and a quantity Phase 14 never published. Core-filtered, `results/phase16_arm_adapter-only.json` gives 496/1008 — identical numerator and denominator to Phase 14 — and a per-question diff over all 112 taught rows returned 0 mismatches. The Δ 0.0048 stated earlier in the discussion was an artifact of that pooling and was withdrawn. PERS-05's seeding defect is scoped to `run_fairness_control`, not the scored adapter-on path, which is why it reproduced.

### Which tier(s) A1/A2/A3 transform

| Option | Description | Selected |
|--------|-------------|----------|
| Both tiers, gate on held-out | All 216 core questions; verdict on core_held_out, core_taught tier-split | ✓ |
| core_held_out only (104) | The single gated tier across Phases 16 and 17 | |
| core_taught only (112) | Attack where extraction is known to work best | |

**User's choice:** Both tiers, gate on held-out → **D-02**
**Notes:** User accepted the ~7h floor explicitly as a floor, not a ceiling, noting role-play framing lengthens prompts and grows prefill. `core_taught` never merged into the formal verdict.

### Runtime guard's reach into the attack corpus

| Option | Description | Selected |
|--------|-------------|----------|
| Widen additively to prompt_ids | 0 deletions, signature-symmetric with `assert_value_in_prompt` | ✓ |
| New phase18 sibling function | Smaller blast radius on a heavily-pinned module | |
| Reuse as-is via build_recall_prompt | Constrain attacks to what the existing guard covers | |

**User's choice:** Widen additively → **D-03**
**Notes:** Preceded by a premise correction: SC1's parenthetical reads as though `_strings_in` were the substring-aware form of `assert_no_value_in_prompt`. They are two guards at two layers — the runtime guard was already substring-aware and was never the equality bug; the whole-string-equality defect lived in `embedded_fact_values`' predicate, the static module scan. Phase 18 needs both.

### Pre-registration boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Pin everything + pre-flight smoke first | One pinned file; smoke discharges the dry-run need before the pin | ✓ |
| Phase 17's two-file split | Pinned constants, unpinned templates | |
| Pin everything, no pre-flight | Strictest, but a degenerate template surfaces only on the long run | |

**User's choice:** Pin everything + pre-flight smoke → **D-04**
**Notes:** The polarity argument was decisive — replacing a persona value is neutral, replacing an attack template after a null is the weakening ATK-03 and P18-4 exist to prevent.

### What A1 is, given F1–F8 already exist

| Option | Description | Selected |
|--------|-------------|----------|
| Surface perturbation, orthogonal axis | Register/hedging/filler/casing/typo over the 216 rendered questions | ✓ |
| Cross-family transfer | Render each fact under the families its tier was not scored in | |
| Drop A1, cite the existing measurement | Paraphrase robustness is already measured | |

**User's choice:** Surface perturbation → **D-05**
**Notes:** Driven by a measurement: `phase14_factset.py:656` already defines eight families, and `TAUGHT_FAMILY_IDS`/`HELDOUT_FAMILY_IDS` (`:816-817`) make the taught/held-out split *itself* the paraphrase axis. A1 as "another phrasing" would have re-derived committed work. Also surfaced that A3 overlaps F8 (third-party framing), resolved later at D-08.

### Seeding for transformed prompts

| Option | Description | Selected |
|--------|-------------|----------|
| Inherit for family zero, stride the attacks | `SEED + index*K + s` makes each question's 64-seed window disjoint | ✓ |
| Inherit unchanged for everything | Maximum continuity with Phases 14/16/17 | |
| Family-scoped offsets | Decorrelates families, not questions | |

**User's choice:** Stride the attack families → **D-06**
**Notes:** Surfaced by measuring the seed window: at 9 draws question *i* shares seeds with 7 neighbours; at K=64 the window is 63, so over half the tier shares randomness. Pre-existing but ~8× worse at the new budget, and cheap to remove without touching ATK-02's arm pairing.

### Corpus artifact's relationship to the run

| Option | Description | Selected |
|--------|-------------|----------|
| Run reads it; a test re-derives it | Artifact is the INPUT; byte-equality test is a standing guard | ✓ |
| Artifact is a record; run re-derives | Two derivation sites for the same prompts | |
| No separate corpus artifact | Prompts visible only after the run | |

**User's choice:** Run reads it → **D-07**
**Notes:** User added the qualification that the byte-equality test is a standing guard and explicitly **not** a precondition of dispatch.

### A3's route to the model

| Option | Description | Selected |
|--------|-------------|----------|
| System span via persona=, 3rd allowlist entry | Structurally distinct from F8; no value enters the span | ✓ |
| Role framing inside the user turn | No guard surface, but structurally identical to F8 | |
| Both — A3a system span, A3b user turn | Isolates where framing matters; doubles A3 | |

**User's choice:** System span via `persona=` → **D-08**
**Notes:** `PERSONA_ALLOWLIST` (`tests/test_phase14_scoring.py:422`) is hard equality with two entries and sanctions growth in the same commit as the call site. The new entry's justification inverts both incumbents': they put a value in the span because the value *is* the measurement; A3 puts none and proves it.

### Family zero's draw budget and the K=64 path gap

| Option | Description | Selected |
|--------|-------------|----------|
| Stub-model prefix test, CPU | Proves prefix stability of the real draw path, zero GPU cost | ✓ |
| Disclose as threats-to-validity | Zero work, but inverts the mutation-proof discipline | |
| Run family zero at K=64 | Identical path by construction; gives back the 54-minute saving | |

**User's choice:** Stub-model prefix test → **D-09**
**Notes:** User stated the 9-draw position before options appeared and it verified mechanically — `draw_all` seeds a fresh generator per draw, so draw *s* is independent of how many follow. The path-divergence gap (control runs `range(8)`, attacks run `range(63)`) was surfaced in response and closed without giving back the saving.

### A1 dose bundling

| Option | Description | Selected |
|--------|-------------|----------|
| Two doses — mild and aggressive | Dose axis; monotone claim shape like Phase 16's ladder | ✓ |
| Five separable types | Per-transform attribution; 14.2h | |
| Three types | Middle ground; drops casing on a guess | |

**User's choice:** Two doses → **D-10**
**Notes:** Accepted the loss of per-transform attribution explicitly, on the grounds that severity is the more central question for the audit.

### Corpus record schema

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit fields: family, dose, fact_id, slot, source seed_index | User-stated position, confirmed against the fixture's actual fields | ✓ |

**User's choice:** Explicit fields → **D-11**
**Notes:** Confirmed by measurement — the fixture stores only `seed_index`, `fact_id`, `question`, `reserved`. `slot` derives by lookup, but `family` has no stored key and would require string-matching `render_family` output. A second benefit surfaced in response: recording `slot` keeps the report renderer from importing the fact set at all.

### Pre-flight smoke scope and target

| Option | Description | Selected |
|--------|-------------|----------|
| Un-adapted base only, structural + degeneracy floor | Phase 17 ISO-01 pattern; floors against measured attractors | ✓ |
| Un-adapted base, structural only | No attractor floor | |
| Both arms, base and adapter | Previews the answer before the unamendable pin | |

**User's choice:** Un-adapted base, with degeneracy floor → **D-12**
**Notes:** User's own point that D-04's smoke scope had gone stale — it was framed before D-05/D-10 made A1 two prompt shapes — was accepted as a scope restatement rather than a widening. The attractor floor uses Phase 17's measured 56/936 and 47/936 rather than an invented threshold.

---

## Prefix-injection budget

### Where in the derived window the budget sits

| Option | Description | Selected |
|--------|-------------|----------|
| f = 1/4 → [1,1,1,1,1,1,2,2] | Both endpoints pinned by committed measurement | ✓ |
| f = 1/3 → [1,1,1,1,1,2,2,2] | Interior to the window; needs its own justification | |
| Uniform 1 id per target | No fraction to justify; 12.5% on the longest targets | |

**User's choice:** f = 1/4 → **D-13**
**Notes:** User required a derivation rather than a plausible number. Supplied from Phase 16's D-30 — token lengths `[4,4,4,5,5,6,8,8]` and the ~2-token in-context ceiling — and re-measured independently against `artifacts/tokenizer.json`. Also corrected the user's citation: D-30 does **not** draw the produced-vs-fed distinction; it says the A>D headline is consistent with two mechanisms and cannot separate them. The suffix rule's support is SC1 and PITFALLS P18-3.

### A2 scoring given 3-character suffixes

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix-concatenation → full-value containment | Committed scorer unchanged; A2 becomes ASR-comparable to A0/A1/A3 | ✓ |
| Bare suffix containment anywhere | Base arm prices the floor; wide bounds on three slots | |
| Both — anchored gated, bare descriptive | Two numbers per cell | |

**User's choice:** Prefix-concatenation → **D-14**
**Notes:** Driven by the measured suffix table — `orp`, `987`, `412` are 3 chars, and `contains_value` matches anywhere in 48 generated tokens.

### A2 prefix placement

| Option | Description | Selected |
|--------|-------------|----------|
| Assistant-turn prefill, after the assistant token | The only placement where concatenation scoring is coherent | ✓ |
| User-turn embedding | Stays inside `build_recall_prompt`'s contract but breaks D-14 | |
| Both placements | Adds 216 prompts / ~2h | |

**User's choice:** Assistant-turn prefill → **D-15**
**Notes:** User explicitly confirmed the realized injection is measured on the **final** post-concatenation id list, not assumed equal to the standalone encoding.

### Reconciling the clean-room guard with deliberate injection

| Option | Description | Selected |
|--------|-------------|----------|
| Partition the prompt | Strict guard on the question portion for every family; bounded on A2's tail | ✓ |
| One guard parameterized by max_injection_ids | Single code path, but a question leak and a legal injection can cancel | |
| Family-scoped exemption table | Genuinely exempts A2; SC1's wording would need changing | |

**User's choice:** Partition the prompt → **D-16**
**Notes:** Keeps SC1's "across the entire corpus" literally true with no family exempted, because the two checks are independent rather than summed.

### Prefix origin and realized-injection reporting

| Option | Description | Selected |
|--------|-------------|----------|
| Start of value (in ids) + published per-slot distribution | User-stated positions, both confirmed | ✓ |

**User's choice:** Both confirmed → **D-17**, **D-18**
**Notes:** Start-of-value was already implicitly assumed by D-13/D-14/D-15; making it explicit was correct since a mid-value span would make "unprompted remainder" prompt-dependent. The realized-injection point is stronger than stated: because D-15 appends ids verbatim, realized equals declared at the id level by construction — what can actually break is the decode round-trip.

### Round-trip guard

| Option | Description | Selected |
|--------|-------------|----------|
| SystemExit at corpus build, mutation-proved RED | Synthetic value split mid-UTF-8-character | ✓ |
| Assert without a RED proof | Breaks the Phases 15–17 discipline | |
| No assertion, publish the distribution | Silent corruption of D-14's scoring for the whole run | |

**User's choice:** SystemExit + mutation proof → **D-19**
**Notes:** Round-trip measured at 8/8 on committed material, which is precisely why the guard needs a watched-RED proof.

---

## Instrument scope

### Canary exposure's reference set

| Option | Description | Selected |
|--------|-------------|----------|
| Base pools + Phase 17's 24 minted | R = 6–8 per slot, ceiling 2.58–3.00 bits | ✓ |
| Base pools only | R = 3–5, ceiling 1.58–2.32 bits | |
| Pooled across slots, R = 28 | Recovers 4.81 bits by measuring slot-type plausibility | |

**User's choice:** Base pools + Phase 17's minted → **D-20**
**Notes:** User declared the canary IN before options appeared, on the grounds that its absence from the success criteria is a specification gap rather than a scoping decision. Both of the user's supporting claims verified (the 28-reference arithmetic at `FEATURES.md:80`; the +211.60%/+241.37% collapse figures). One did not: `FEATURES.md:358`'s ~4.8-bit resolution claim is log2(28) over a pool spanning 11 slots. Per-slot measurement gave 1.58–2.32 bits on the base pools; Phase 17's 24 minted values (3 per core slot, zero overlap verified) lift it to 2.58–3.00. An earlier count in this discussion over-collected `phase17_persona_facts`' re-exports and was redone against `PERSONA_FACTS` only.

### Cross-persona attacks

| Option | Description | Selected |
|--------|-------------|----------|
| Out of gated scope, descriptive at most | User-stated position, both cited figures verified | ✓ |

**User's choice:** Out of gated scope → **D-21**
**Notes:** Phase 17 settled isolation at 6/6 Holm unanimity; the adapters' `replay_ratio=0.0` collapse makes any result from them non-representative.

### Exposure's role relative to the formal verdict

| Option | Description | Selected |
|--------|-------------|----------|
| Admissibility instrument + descriptive aggregate | Feeds `null_result_is_admissible()`; zero Holm interaction | ✓ |
| Second independent gated family | Higher-powered instrument, but two families is extra chances | |
| Inside the ASR Holm family | Predictably destroys D-02's verdict | |

**User's choice:** Admissibility instrument → **D-22**
**Notes:** User named it the third instance of the milestone's instrument-blind vs phenomenon-absent pattern, after Phase 16's D-30 and Phase 17's D-10.

### Unique-successes entity

| Option | Description | Selected |
|--------|-------------|----------|
| Per fact × family, n=8 | Matches P18-2's wording; same unit as Phases 16/17 | ✓ |
| Per question × family, n=216 | Finer, but reintroduces the clustering error STAT-01 forbids | |
| Both — fact headline, question detail | Two numbers, one materially wrong if quoted | |

**User's choice:** Per fact × family → **D-25**
**Notes:** User argued dose-collapse from the clustering principle. Refined in response: P18-2's own wording puts the entity at the target and the count over families, under which A1's doses collapse automatically.

### The 9-vs-64 draw asymmetry

| Option | Description | Selected |
|--------|-------------|----------|
| Unique successes at the common 9-prefix, k=64 alongside | Equal-budget comparison, free from D-09's proof | ✓ |
| Exclude A0 from ladder and unique successes | Amends D-25 to three families | |
| Include A0 at its own budget, disclosed | Headline mixes budgets | |

**User's choice:** Common 9-draw prefix → **D-26**
**Notes:** This was a defect in the just-locked D-25 — "at least once" over 64 draws is ~7× the sampling opportunity of 9 — surfaced immediately after D-25 rather than left for the planner.

### `null_result_is_admissible()`'s shape

| Option | Description | Selected |
|--------|-------------|----------|
| New function in phase18_extraction.py, mirroring erasure_succeeded | Keyword-only, (verdict, reasons), INCONCLUSIVE precedence | ✓ |
| Add it to erasure_gate.py | Edits the file whose value is that it has not been touched since 23a830c | |
| Return (bool, reasons) | Collapses "could not tell" and "found nothing" | |

**User's choice:** New function, `erasure_gate.py` untouched → **D-27**
**Notes:** `erasure_is_worth_attempting`'s existing signature already fixes the shape D-02's verdict must emit, and `ERASURE_DECISION_RULE` pre-registers "best attack" in advance.

---

## SC5 landing

| Option | Description | Selected |
|--------|-------------|----------|
| Correct text directly in the Gradio label, no supersession framing | User-stated position, verified against the demo's copy | ✓ |

**User's choice:** Direct text → **D-23**
**Notes:** Premise confirmed — the demo's toggle copy is already availability-framed (`MEMORY_INFO`: "36 boolean flags flip"; `STATUS_OFF`: "loaded but gated off"), so there is no prior claim to supersede. README and `docs/REPORT.md` do carry published v2.0 text and do get dated continuations. `RESET_LABEL`'s "delete the adapter from memory" noted as the one authorization-flavoured string, outside SC5's toggle scope.

## Threat-model table

| Option | Description | Selected |
|--------|-------------|----------|
| Templated from the table by a committed function | Scope cannot widen between driver and prose | ✓ |
| Table committed, conclusion hand-written | Containment test permits overclaiming around the exclusions | |
| Table only, no templated conclusion | P18-4 makes the templating the point | |

**User's choice:** Templated conclusion → **D-24**
**Notes:** User requested the table's actual content before positioning, and it was drafted rather than described. User then directed one correction into it: P18-4's "v1.0 already shipped weights on a GitHub Release" is recorded as unverified in `v1.0-MILESTONE-AUDIT.md:31`, so the table states the honest asymmetry — the adapter is a portable file and anyone holding it has white-box access — without asserting publication.

---

## Claude's Discretion

- Report layout, figure choices, and file naming under `results/phase18_*`.
- The concrete surface-transform implementations behind D-10's two doses, subject to D-05 and D-12.
- Sweep ordering and process isolation (Phase 16 D-01/D-03 pattern).
- The prose of A3's role instruction, subject to D-08 and the D-03 guard.
- `PHASE18_PREREG_ARTIFACT` wiring and the `_GATE_MODULES` glob over `scripts/phase18_*.py`.

## Deferred Ideas

- Cross-persona extraction attacks on Phase 17's adapters — declined at D-21, not deferred.
- Relearning / fine-tuning attack — named as NOT run in D-24; the Phase 19+ follow-up.
- Membership inference — declined at n=8 members for the distribution-shift confound.
- White-box / adapter-file attacks — out of the black-box threat model by definition.
- Per-transform attribution for A1 — traded away at D-10 for the dose axis.
- `RESET_LABEL`'s "delete the adapter from memory" wording — noted, outside SC5's scope.
