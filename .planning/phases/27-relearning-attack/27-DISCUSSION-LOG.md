# Phase 27: Relearning Attack - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-14
**Phase:** 27-relearning-attack
**Areas discussed:** Admission gate input, What a MOOT phase ships, Recovery quantity + fixture, Budget unit + Z rule, Offset-stream capture, Synthetic CPU fixture, Admission record schema, Close-out verification

**Measured premise stated at the top of the discussion:** `results/phase25_frontier.json` tallies PASS 0 / FAIL 32 / INCONCLUSIVE 6 / REFUSED 6; every DP point cleared (a) at 0/416 and failed (b) at 0/1008; the adversarial arm is INCONCLUSIVE and recipe-confounded. Phase 20 pre-registered X for extraction but no relearning Z and no attacker corpus exist in code.

---

## Admission gate input

### Q1. What must a Phase 25 point have done for relearning_is_worth_attempting(points) to admit it?

| Option | Selected |
|--------|----------|
| PASS verdict only | ✓ |
| Condition (a) cleared |  |
| PASS or INCONCLUSIVE |  |

**User's choice:** PASS verdict only
**Notes:** PASS verdict only — reads verdict.verdict == 'PASS'; today 0/44 so MOOT

### Q2. Where does the gate get its 44 verdicts from?

| Option | Selected |
|--------|----------|
| Read the committed frontier record |  |
| Re-derive through mitigation_point_verdict |  |
| Both: read, then re-derive as a tripwire | ✓ |

**User's choice:** Both: read, then re-derive as a tripwire
**Notes:** Both: read results/phase25_frontier.json, and a CPU test re-derives all 44 verdicts through mitigation_point_verdict as a tripwire

### Q3. Return shape and how 'record missing/partial' differs from MOOT?

| Option | Selected |
|--------|----------|
| Three-valued ADMITTED/MOOT/INCONCLUSIVE | ✓ |
| (bool, reason) like erasure_is_worth_attempting |  |
| Two-valued, refuse on partial |  |

**User's choice:** Three-valued ADMITTED/MOOT/INCONCLUSIVE
**Notes:** Three-valued ADMITTED / MOOT / INCONCLUSIVE with reasons; MOOT only when all 44 present and none PASS

### Q4. How is the gate call made auditable before it runs?

| Option | Selected |
|--------|----------|
| Prereg module + ancestry guard + one committed record | ✓ |
| Gate in prereg module, record optional |  |
| Gate lives in erasure_gate.py |  |

**User's choice:** Prereg module + ancestry guard + one committed record
**Notes:** scripts/phase27_prereg.py at ONE commit with ancestry guard over results/phase27_*; single call writes results/phase27_admission.json

### Q5. If MOOT, what happens to the five RELRN rows?

| Option | Selected |
|--------|----------|
| RELRN-01 ticked; 02-05 unticked with named limitation | ✓ |
| All five ticked on structural satisfaction |  |
| RELRN-01 ticked; 02-05 re-deferred to v5.0 |  |

**User's choice:** RELRN-01 ticked; 02-05 unticked with named limitation
**Notes:** RELRN-01 ticked by the gate call + record; RELRN-02..05 stay unticked with a named limitation carried to Phase 28

### Q6. How is the frontier record pinned?

| Option | Selected |
|--------|----------|
| sha256 both ways + one-commit proof | ✓ |
| sha256 only |  |
| Git SHA of the frontier's commit |  |

**User's choice:** sha256 both ways + one-commit proof
**Notes:** frontier_sha256 asserted equal to the tree file AND the frontier still at one commit (pinned both ways)

### Q7. What must the MOOT reasons carry?

| Option | Selected |
|--------|----------|
| Per-arm tallies plus (a)/(b)/(c) breakdown | ✓ |
| Tallies only |  |
| Tallies plus nearest-miss point |  |

**User's choice:** Per-arm tallies plus (a)/(b)/(c) breakdown
**Notes:** Per-leg PASS/FAIL/INCONCLUSIVE/REFUSED tallies plus how many points cleared each of (a)/(b)/(c)

### Q8. How do the attack legs depend on the admission record?

| Option | Selected |
|--------|----------|
| Every attack leg refuses unless ADMITTED | ✓ |
| Gate is a precondition inside one driver |  |
| Only the mitigated-arm leg is gated |  |

**User's choice:** Every attack leg refuses unless ADMITTED
**Notes:** Every attack leg (calibration, cost curve, gate) reads results/phase27_admission.json and refuses unless ADMITTED; refusal watched RED in a CPU test; record written once with refuse_if_exists

---

## What a MOOT phase ships

### Q1. With the gate reading MOOT, how much apparatus does Phase 27 build?

| Option | Selected |
|--------|----------|
| Full apparatus, CPU-tested, never run on MPS | ✓ |
| Gate + MOOT record only |  |
| Full apparatus AND Z measured on the two controls |  |

**User's choice:** Full apparatus, CPU-tested, never run on MPS
**Notes:** Full apparatus in committed code with CPU tests + synthetic fixture, never run on MPS; SC2-5 TRUE as guarded code; disclosure 'not exercised on a mitigated arm'

### Q2. How does an unrun apparatus prove its live path is wired?

| Option | Selected |
|--------|----------|
| One CPU end-to-end run on a tiny synthetic fixture |  |
| Per-function unit tests plus --dry-run |  |
| End-to-end run plus a kwargs-trace test | ✓ |

**User's choice:** End-to-end run plus a kwargs-trace test
**Notes:** One CPU end-to-end run on a tiny synthetic fixture (forged ADMITTED record in tmp, real train path, real scorer, calibration->curve->gate) PLUS a kwargs-trace test over main()->run_leg() signatures

### Q3. Where does the 'built, never exercised' disclosure live?

| Option | Selected |
|--------|----------|
| A field in the admission record | ✓ |
| A separate operational note |  |
| Only the REQUIREMENTS traceability rows |  |

**User's choice:** A field in the admission record
**Notes:** A field in results/phase27_admission.json: apparatus {status, legs, reason} plus module sha256 of the apparatus code

### Q4. Does the prereg module pin the reference arms now?

| Option | Selected |
|--------|----------|
| Pin both by adapter sha256 and seed now | ✓ |
| Pin the never-taught reference only |  |
| Leave unpinned |  |

**User's choice:** Pin both by adapter sha256 and seed now
**Notes:** Pin both by path + adapter sha256 + seed: never-taught (phase23_never_taught_training.json, 5 seeds) and unmitigated control (Phase 25 dp_n8/dp_n64 sigma=0); gate's required baseline= kwarg accepts only a pinned entry

### Q5. Which training path does the attacker's fine-tune use?

| Option | Selected |
|--------|----------|
| teach_persona.train_arm | ✓ |
| A separate attacker loop |  |
| train_arm with replay disabled |  |

**User's choice:** teach_persona.train_arm
**Notes:** teach_persona.train_arm, the project's own teaching recipe; only max_steps and data differ; identical budget = same symbol

### Q6. LaunchAgent plist now or CLI only?

| Option | Selected |
|--------|----------|
| CLI driver only, no plist | ✓ |
| Driver plus the plist, unloaded |  |
| Reuse phase25_run helpers inline |  |

**User's choice:** CLI driver only, no plist
**Notes:** CLI driver only: scripts/phase27_relearn.py with sub-modes admit/calibrate/curve/gate, each refusing without ADMITTED; no plist

### Q7. Who commits results/phase27_admission.json?

| Option | Selected |
|--------|----------|
| The operator, by hand | ✓ |
| The executor agent |  |
| The driver in-process |  |

**User's choice:** The operator, by hand
**Notes:** The operator by hand at a human-action checkpoint (Phase 26 precedent 8652c15); driver never touches git

---

## Recovery quantity + fixture

### Q1. Which instrument reads recovery?

| Option | Selected |
|--------|----------|
| Extraction, X = existing ceiling |  |
| Taught-fact recall 112-question tier |  |
| Both, extraction decides, recall reported beside it | ✓ |

**User's choice:** Both, extraction decides, recall reported beside it
**Notes:** Both: extraction under the Phase-18 families (core_held_out 416, Wilson upper bound vs mitigation_gate.extraction_ceiling) DECIDES; taught-fact recall (112 q x 9 draws) reported beside it, never decides (Phase 26 D-10 shape)

### Q2. Which fixture and how is disjointness proven?

| Option | Selected |
|--------|----------|
| core_held_out + F3/F7/F8 with string-intersection proof | ✓ |
| Family A2 only |  |
| A new fixture from unseen slot forms |  |

**User's choice:** core_held_out + F3/F7/F8 with string-intersection proof
**Notes:** core_held_out (416) + F3/F7/F8 held-out recall; a CPU test renders every scored prompt and asserts zero string overlap with the mitigated arm's teaching bin, the adversarial arm's trained families A1/A3, and the attacker corpus; disjointness recorded as a computed fact

### Q3. What is the pre-registered attacker corpus?

| Option | Selected |
|--------|----------|
| Full teaching rows as taught | ✓ |
| One rendering per fact |  |
| A ladder of corpus sizes |  |

**User's choice:** Full teaching rows as taught
**Notes:** The 8 LOCKED_FACTS' full teaching rows exactly as taught (same render_family path, ~22 rows/fact), pinned by sha256 of the rendered bin in phase27_prereg; same corpus for n=8 and n=64 targets

### Q4. What decides mitigated ~ fresh?

| Option | Selected |
|--------|----------|
| Committed band per rung | ✓ |
| Sign of the gap at Z only |  |
| Qualitative prose |  |

**User's choice:** Committed band per rung
**Notes:** Committed band per budget rung: |mitigated - fresh| <= MARGIN_K x fresh arm's seed noise floor (phase23_prereg.noise_floor over the 5 fresh seeds); finding names rungs inside/outside; never a gate

### Q5. Does the attacker keep replay?

| Option | Selected |
|--------|----------|
| Keep the recipe's replay ratio | ✓ |
| No replay |  |
| Replay as a second variant |  |

**User's choice:** Keep the recipe's replay ratio
**Notes:** Yes: the recipe's replay ratio, identical to fresh and control arms; no-replay is the Phase 28 SC4 confound

### Q6. Draws per question on rungs vs gate reading?

| Option | Selected |
|--------|----------|
| CURVE_K 16 on rungs, gate at 48 | ✓ |
| K 48 everywhere |  |
| K 16 everywhere |  |

**User's choice:** CURVE_K 16 on rungs, gate at 48
**Notes:** CURVE_K = 16 on every rung; the reading at Z promoted to K = 48 via promote_to_full_fidelity; seed stride phase18_extraction.K so 16 is the bit-identical prefix of 48

### Q7. Which surviving points get attacked if ADMITTED?

| Option | Selected |
|--------|----------|
| Every PASS point in point_keys order | ✓ |
| One point per leg, lowest sigma/ratio |  |
| One point chosen by the operator |  |

**User's choice:** Every PASS point in point_keys order
**Notes:** Every PASS point in point_keys order, each loaded by its pinned adapter_sha256 and refused on mismatch; never a subset chosen after seeing data

---

## Budget unit + Z rule

### Q1. Unit of Z and the curve's x-axis?

| Option | Selected |
|--------|----------|
| Z in steps, scored-token count per rung | ✓ |
| Z in scored tokens |  |
| Z in examples |  |

**User's choice:** Z in steps, scored-token count per rung
**Notes:** Z in optimizer steps (recipe-native, rungs on real checkpoints); every rung records its scored-token COUNT from the mask bin (int(mask_bin.sum()) x steps-seen), counts never rates; both in the same row

### Q2. Which recall threshold do the controls clear for Z?

| Option | Selected |
|--------|----------|
| Frontier's condition (b) | ✓ |
| Control's full recall (F_Y = 1) |  |
| A new relearning-specific threshold |  |

**User's choice:** Frontier's condition (b)
**Notes:** The frontier's own condition (b): taught recall >= F_Y x the matched control's full-budget recall (0.7 x 0.7837 = 0.5486 at n=8; n=64 uses its own 0.0863 -> 0.0604, disclosed as weak)

### Q3. Rungs and the cap?

| Option | Selected |
|--------|----------|
| Every CHECKPOINT_INTERVAL to 2 x MAX_STEPS | ✓ |
| Every EVAL_INTERVAL to MAX_STEPS |  |
| Geometric 25..800 |  |

**User's choice:** Every CHECKPOINT_INTERVAL to 2 x MAX_STEPS
**Notes:** Every CHECKPOINT_INTERVAL (50 steps) up to a pre-registered cap of 2 x MAX_STEPS = 400, each rung a saved adapter from one run scored at K=16; if either control has not cleared by the cap, Z undefined -> INCONCLUSIVE with both curves published; cap is a resource parameter

### Q4. The three structural proofs (RELRN-04)?

| Option | Selected |
|--------|----------|
| Shared instance + on-disk diff + offset-stream sha256 | ✓ |
| Shared config + bin sha256 |  |
| Config + order proof, in-process only |  |

**User's choice:** Shared instance + on-disk diff + offset-stream sha256
**Notes:** One TrainConfig instance passed to all train_arm calls; dataclasses.asdict(cfg) + seed in every arm's record; a test reads the records back off disk and asserts the diff empty except arm name and data path; data-order sha256 over the sampler's logged (window offset) stream

### Q5. Seeds per curve?

| Option | Selected |
|--------|----------|
| Fresh 5, control/mitigated 1337 | ✓ |
| One seed everywhere |  |
| Five seeds everywhere |  |

**User's choice:** Fresh 5, control/mitigated 1337
**Notes:** Fresh: all 5 SEED_LADDER seeds (on disk) giving the noise floor for the ~ band; unmitigated control and mitigated target: designated seed 1337; pooled reading is SEED_LADDER[0], never a sum

### Q6. Z per leg and how controls combine?

| Option | Selected |
|--------|----------|
| One Z per leg = max of first clearing rungs | ✓ |
| One Z for the milestone |  |
| Z per leg, fresh only |  |

**User's choice:** One Z per leg = max of first clearing rungs
**Notes:** One Z per capacity leg = max(first rung fresh clears, first rung control clears); both rungs and the max written; a leg where either never clears by the cap is INCONCLUSIVE on its own

---

## Offset-stream capture

### Q1. Where is the sampler's offset stream captured?

| Option | Selected |
|--------|----------|
| Optional on_draw=None callback | ✓ |
| Recorder wrapper installed by the driver |  |
| Shadow RNG replay |  |

**User's choice:** Optional on_draw=None callback
**Notes:** Optional on_draw=None kwarg on get_batch_memmap_masked in src/personacore/training/data.py; None path proven byte-identical; the driver passes a recorder appending each ix array; sha256 over the concatenated stream

### Q2. What does the hashed stream cover?

| Option | Selected |
|--------|----------|
| Every draw incl. replay | ✓ |
| Teaching-bin draws only |  |
| Per-step sha256 chain |  |

**User's choice:** Every draw incl. replay
**Notes:** Every draw the loop makes, teaching AND replay windows, in call order; each ix appended as raw uint64 bytes with its bin path; one stream per arm

---

## Synthetic CPU fixture

### Q1. What model does the end-to-end wiring test use?

| Option | Selected |
|--------|----------|
| Tiny random-init GPT + real tokenizer | ✓ |
| Real convbase checkpoint on CPU |  |
| Tiny model plus a slow real-checkpoint smoke |  |

**User's choice:** Tiny random-init GPT + real tokenizer
**Notes:** Tiny random-init GPT (2 layers, small embd) + the real frozen tokenizer; seconds per run; asserts structure not values (tests/test_lora_toggle.py / test_fisher.py shape)

### Q2. Where do the fixture's facts, corpus and questions come from?

| Option | Selected |
|--------|----------|
| 2 synthetic facts through the real renderer | ✓ |
| Hand-written strings |  |
| A 1-fact slice of real LOCKED_FACTS |  |

**User's choice:** 2 synthetic facts through the real renderer
**Notes:** 2 synthetic facts rendered through the real render_family + Phase-18 fixture paths; forged ADMITTED record names one fake point whose adapter is the tiny model's saved bytes; no real LOCKED_FACTS in tests/

---

## Admission record schema

### Q1. How much of the frontier does the admission record carry?

| Option | Selected |
|--------|----------|
| Tallies + breakdown + per-point verdict values | ✓ |
| Tallies and breakdown only |  |
| Full per-point verdicts with reasons |  |

**User's choice:** Tallies + breakdown + per-point verdict values
**Notes:** Tallies + (a)/(b)/(c) breakdown + 44 rows {point_key, arm, leg, verdict, cleared_a, cleared_b, cleared_c} re-derived and asserted at the single write; never the reasons (quoted from the frontier by sha256); plus frontier_sha256, pinned baselines, apparatus block, provenance

### Q2. How are cleared_a/b/c computed?

| Option | Selected |
|--------|----------|
| Re-derived through condition functions | ✓ |
| Parsed from reason strings |  |
| Verdict only |  |

**User's choice:** Re-derived through condition functions
**Notes:** Re-derived through mitigation_gate's condition functions (extraction_ceiling / dialogue_gap_band / retention_cap) on each point's 21 pinned kwargs; reason strings never parsed

### Q3. Provenance block?

| Option | Selected |
|--------|----------|
| Full digests + bytes-recompute guard | ✓ |
| git_sha and written_utc only |  |
| Digests without guard |  |

**User's choice:** Full digests + bytes-recompute guard
**Notes:** module_sha256 for phase27_prereg, phase27_relearn, mitigation_gate, erasure_gate, training/data.py + git_sha + written_utc + torch version; a test recomputes every digest from bytes (never via the emitter's hash helper) and names ALL drifted modules at once (24-09 guard)

### Q4. What does the apparatus block list per leg?

| Option | Selected |
|--------|----------|
| Name + sub-mode + two test node ids | ✓ |
| Name and status only |  |
| Name plus prose |  |

**User's choice:** Name + sub-mode + two test node ids
**Notes:** Four legs (calibrate, curve, gate, structural-proof): leg name, driver sub-mode, refusal test node id, CPU end-to-end test node id; a test asserts every node id exists in the collected suite

---

## Close-out verification

### Q1. What is watched live before the operator commits the record?

| Option | Selected |
|--------|----------|
| Each sub-mode watched refusing on the real record | ✓ |
| Tests only |  |
| Refusal AND a forged-ADMITTED dry run on MPS |  |

**User's choice:** Each sub-mode watched refusing on the real record
**Notes:** Each attack sub-mode (calibrate / curve / gate / structural-proof) invoked once against the real MOOT record and seen to refuse non-zero naming the verdict it read; refusal text captured in the plan summary; no training

### Q2. How are the ledger edits written at close?

| Option | Selected |
|--------|----------|
| By hand with snapshot/diff, zero handlers | ✓ |
| gsd-sdk handlers then hand-repair |  |
| Handlers for STATE.md only |  |

**User's choice:** By hand with snapshot/diff, zero handlers
**Notes:** By hand; STATE/ROADMAP/REQUIREMENTS snapshotted before and diffed after; zero gsd-sdk mutation handlers (Phase 26 posture)

---

## Claude's Discretion

- File layout between `scripts/phase27_prereg.py` and `scripts/phase27_relearn.py`.
- Recorder representation and the `data/phase27_*` stream file location.
- Tiny-model `ModelConfig` dimensions for the CPU fixture.
- Test file naming; how the kwargs-trace test reads signatures.

## Deferred Ideas

- Relearning as a diagnostic on DP points that failed (b) — v5.0 candidate.
- LaunchAgent + sidecar-per-point for an unattended admitted run — whichever phase reads ADMITTED.
- Attacker-corpus ladder and a no-replay attacker variant — recorded for a v5.0 threat-model discussion.
