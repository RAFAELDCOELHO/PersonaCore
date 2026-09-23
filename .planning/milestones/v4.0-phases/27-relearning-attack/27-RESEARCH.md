# Phase 27: Relearning Attack - Research

**Researched:** 2026-09-14 (tree read at HEAD `ff38d9a`, clean except the pre-existing `D .claude/scheduled_tasks.lock`)
**Domain:** pre-registered admission gate over a committed record + a CPU-tested relearning apparatus (LoRA fine-tune through the project's own teaching recipe, extraction/recall scoring, structural identical-budget proofs) — stdlib + existing torch/numpy surface only
**Confidence:** HIGH for every signature, constant, path, digest and count below (each was opened or computed this session; the file:line is given). MEDIUM only where a decision's letter conflicts with the live code and the planner/operator must rule (Open Questions).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Thirty-nine decisions across eight areas. Every one is LOCKED** — the researcher and planner act on
them rather than re-open them.

#### Area 1 — The admission gate (RELRN-01, SC1)

- **D-01: A point is admitted only on a frontier `verdict.verdict == "PASS"`.** Not condition (a)
  alone, not INCONCLUSIVE. Mirrors `erasure_gate.erasure_is_worth_attempting`'s MOOT branch and the
  roadmap's own sentence. Today: 0 of 44 → MOOT.

- **D-02: The gate READS the committed frontier record and a CPU test RE-DERIVES all 44 verdicts as a
  tripwire.** `results/phase25_frontier.json` is consumed (its `verdicts.tallies` and per-point
  `verdict.verdict`); the gate asserts the tally re-derives from the 44 entries; a separate test calls
  `mitigation_gate.mitigation_point_verdict` on each point's pinned kwargs and goes RED if any verdict
  differs. The frontier is never re-emitted.

- **D-03: Three-valued verdict domain: `ADMITTED` / `MOOT` / `INCONCLUSIVE`, each with a `reasons`
  list.** MOOT only when all 44 points are present and none is PASS. A missing frontier, a tally that
  does not re-derive, or fewer than 44 entries is INCONCLUSIVE. "We could not tell" never reads as
  "nothing survived" (Phase 26 D-05 pattern).

- **D-04: Pre-registration module + ancestry guard + one committed record.** `scripts/phase27_prereg.py`
  holds the gate, X (imported from `mitigation_gate.extraction_ceiling`, never retyped), the Z rule,
  the ≈ band, the attacker-corpus definition and the pinned baselines, committed at ONE commit; a test
  proves every tracked `results/phase27_*` artifact's first-add descends from that commit (the
  Phase 23/26 guard). The single gate call writes `results/phase27_admission.json`.

- **D-05: On MOOT, RELRN-01 is ticked by the gate call + record; RELRN-02..05 stay UNTICKED with a
  named limitation** — each traceability row reads "not admitted by the gate; apparatus built and
  guarded, never exercised on a mitigated arm" — carried to Phase 28 as a named limitation
  (precedent: 23-17 left unticked on purpose). Requirement text is NOT edited after seeing numbers.

- **D-06: The frontier is pinned BOTH WAYS.** The record carries `frontier_sha256`; a test asserts it
  equals `sha256(results/phase25_frontier.json)` in the tree AND that the frontier is still at one
  commit in `git log` (Phase 26's "pinned to the frontier both ways"). A re-emitted frontier reddens
  Phase 27 by construction.

- **D-07: MOOT reasons carry per-leg PASS/FAIL/INCONCLUSIVE/REFUSED tallies AND how many points
  cleared each of (a)/(b)/(c)** — e.g. "32 DP points cleared (a) at 0/416 and failed (b) at 0/1008" —
  so Phase 28 generates WHY nothing survived from the record rather than authoring it.

- **D-08: Every attack leg refuses unless the committed record reads ADMITTED.** One CLI sub-mode
  writes the admission record once (`refuse_if_exists`); the calibrate / curve / gate /
  structural-proof legs each READ that record and refuse on MOOT or INCONCLUSIVE — gated on the
  committed record, never on a live re-read (Phase 23's two-conjunct pattern). Each refusal is watched
  RED in a CPU test.

#### Area 2 — What a MOOT phase ships (SC2–SC5 as guarded code)

- **D-09: The FULL apparatus is built as committed code with CPU tests and a synthetic fixture, and
  is never run on MPS in this phase.** Gate with `baseline=` as a required keyword argument with no
  default, Z-calibration rule, cost-curve reducer, ≈ band, shared-`TrainConfig` + on-disk diff +
  data-order sha256 proofs. SC2–SC5 are TRUE as guarded code; the record discloses "not exercised on a
  mitigated arm" the way Phase 26 D-13 disclosed "could not have failed".

- **D-10: Wiring is proven by ONE CPU end-to-end run PLUS a kwargs-trace test.** The end-to-end test
  forges an ADMITTED record in a tmp tree, trains a real LoRA adapter for a handful of steps through
  the actual train path with the shared `TrainConfig`, scores it with the real scorer on the synthetic
  fixture, and drives calibrate → curve → gate to a verdict. The kwargs-trace test inspects
  `main()` → `run_leg()` call signatures so a renamed kwarg is RED without training. (Phase 25 shipped
  23 green `--dry-run` tests around a driver whose live path raised `KeyError` on first real call —
  this is the structural answer.)

- **D-11: The "built, never exercised" disclosure is a FIELD of the admission record** —
  `apparatus: {status: "not exercised", legs: [...], reason: "gate read MOOT"}` beside the verdict,
  plus the module sha256 of the apparatus code. One artifact, one quote.

- **D-12: Both reference arms are PINNED NOW by path + adapter sha256 + seed** in `phase27_prereg.py`:
  the never-taught reference (`results/phase23_never_taught_training.json`'s 5 adapters, seeds 1337 /
  2024 / 1338 / 2025 / 1339) and the retrained unmitigated control (the Phase 25 `dp_n8` / `dp_n64`
  σ=0 points). The gate's required `baseline=` kwarg accepts only a pinned entry; a future ADMITTED
  run cannot pick a baseline after seeing data.

- **D-13: The attacker's fine-tune goes through `teach_persona.train_arm`, the project's own teaching
  recipe.** Only `max_steps` and the data differ from the arm that taught the facts; "identical
  budget" is literally the same symbol for attacker, fresh and control arms (Phase 23's
  import-not-retype rule). No second optimizer loop.

- **D-14: CLI driver only, no LaunchAgent plist.** `scripts/phase27_relearn.py` with sub-modes
  `admit` / `calibrate` / `curve` / `gate` (+ the structural-proof check), each refusing without
  ADMITTED. The LaunchAgent + sidecar-per-point pattern is documented as the next step for whichever
  phase admits; nothing unattended is scheduled in a phase that trains nothing.

- **D-15: The operator commits `results/phase27_admission.json` BY HAND at a human-action
  checkpoint** (Phase 26 precedent `8652c15`: the only git write in the audit's lifetime). The driver
  writes the file and never touches git.

#### Area 3 — Recovery quantity, fixture, and attacker corpus (RELRN-01/02/05)

- **D-16: Extraction DECIDES, recall is REPORTED beside it** (Phase 26 D-10 shape). Recovery is the
  frontier's condition-(a) quantity: `core_held_out` extraction over 416 questions, Wilson upper
  bound against `mitigation_gate.extraction_ceiling` (0.006462, zero-tolerance) — no new X. Taught-fact
  recall (112 questions × 9 draws, the `phase25_recall` instrument) travels in the same row and never
  decides.

- **D-17: The recovery fixture is `core_held_out` (416) + held-out recall families F3/F7/F8, with a
  STRING-INTERSECTION disjointness proof.** A CPU test renders every scored prompt and asserts zero
  overlap with (i) the mitigated arm's teaching-bin rows, (ii) the adversarial arm's trained families
  A1-mild / A1-aggressive / A3 (`phase24_adversarial.HELD_OUT_FAMILY == "A2"` is read, never spelled),
  and (iii) the attacker corpus. Disjointness is a computed fact in the record, not a sentence.

- **D-18: The pre-registered attacker corpus is the 8 `LOCKED_FACTS`' FULL teaching rows exactly as
  taught** (same `render_family` path, ~22 rows/fact), pinned by sha256 of the rendered bin in
  `phase27_prereg.py`. Budget, not corpus size, is the curve's axis. The same corpus targets n=8 and
  n=64 points, since recovery is scored on the 8 facts. The corpus definition IS the threat model: the
  strongest realistic adversary, one who holds the original training rows.

- **D-19: "Mitigated ≈ fresh" is a COMMITTED BAND per budget rung:
  `|mitigated − fresh| ≤ MARGIN_K × fresh_seed_noise_floor`**, with `MARGIN_K` imported from
  `erasure_gate` (=2) and the floor from `phase23_prereg.noise_floor` over the 5 fresh seeds. The
  finding names which rungs sit inside and outside the band. A finding that qualifies the verdict,
  never a gate (RELRN-03).

- **D-20: The attacker KEEPS the recipe's replay ratio**, identical to the fresh and control arms.
  The adversarial arm's no-replay confound (Phase 28 SC4) is the cautionary precedent.

- **D-21: `CURVE_K = 16` draws per question on every rung; the reading at Z is PROMOTED to K = 48
  via `mitigation_gate.promote_to_full_fidelity`.** Seed stride stays `phase18_extraction.K` so the
  16-draw reading is the bit-identical prefix of the 48-draw one (Phase 23's rule). No new K.

- **D-22: If ever ADMITTED, EVERY PASS point is attacked, in `point_keys` order, each loaded by its
  pinned `adapter_sha256` and refused on mismatch.** Never a subset chosen after seeing a result
  (Phase 26 D-01).

#### Area 4 — Budget unit and the Z rule (RELRN-01/02/04)

- **D-23: Z is stated in OPTIMIZER STEPS; every rung records its scored-token COUNT from the mask
  bin.** Steps are the recipe's native knob (`MAX_STEPS = 200`, `CHECKPOINT_INTERVAL = 50`), so rungs
  fall on real saved adapters. The x-axis SC3 asks for is scored tokens, taken per rung as
  `int(np.fromfile(mask_bin, dtype=np.uint8).sum())` × steps-seen — counts never rates (Phase 24).
  Both travel in the same row.

- **D-24: The recall threshold the two controls must clear for Z is the frontier's own condition (b):
  taught recall ≥ `F_Y` × the matched control's full-budget recall** (0.7 × 0.7837 = 0.5486 at n=8;
  the n=64 leg uses its own control reading 0.0863 → 0.0604, disclosed as the weak floor it is). No
  new number; "clear" means what it meant on the frontier.

- **D-25: Rungs at every `CHECKPOINT_INTERVAL` (50 steps) up to a PRE-REGISTERED CAP of
  2 × `MAX_STEPS` = 400 steps**, each rung a saved adapter from one run, scored at K=16. If either
  control has not cleared (b) by the cap, Z is undefined and the leg reads INCONCLUSIVE with both
  curves published. The cap is a resource parameter set now, not an outcome threshold (PROJECT.md's
  pre-registration boundary).

- **D-26: The three structural proofs (RELRN-04), concretely:** (i) ONE `TrainConfig` instance is
  passed to all `train_arm` calls; (ii) each arm's record writes `dataclasses.asdict(cfg)` + seed, and a
  test reads the records back OFF DISK and asserts the diff is empty except arm name and data path;
  (iii) the data-order proof is a sha256 over the sampler's logged (window-offset) stream, equal
  across arms given equal seed and bin length.

- **D-27: Seeds — fresh curve at all 5 `SEED_LADDER` seeds (they exist on disk and give D-19's noise
  floor); unmitigated control and mitigated target at the designated seed 1337.** The pooled reading is
  `SEED_LADDER[0]`, never a sum across seeds (Phase 23/25 rule).

- **D-28: ONE Z PER CAPACITY LEG = max(first rung the fresh arm clears, first rung the control
  clears).** Both rungs and the max are written in the record. A leg where either arm never clears by
  the cap is INCONCLUSIVE on its own, not both.

#### Area 5 — Offset-stream capture (RELRN-04)

- **D-29: An optional `on_draw=None` keyword is added to `get_batch_memmap_masked` in
  `src/personacore/training/data.py`.** When `None` nothing changes — a test proves the default path
  draws identical `ix` — so every prior phase's byte-identity is untouched. The Phase 27 driver passes
  a recorder that appends each `ix` array; sha256 over the concatenated stream is the proof.

- **D-30: The hashed stream covers EVERY draw the loop makes — teaching AND replay windows — in call
  order**, each `ix` appended as raw uint64 bytes with the bin path it came from; one stream per arm.
  A differing sha256 names the exact divergence by offset.

#### Area 6 — The synthetic CPU fixture (D-10's substrate)

- **D-31: The end-to-end wiring test trains and scores a TINY random-init GPT (2 layers, small
  embd) with the REAL frozen tokenizer** — seconds per run, the `tests/test_lora_toggle.py` /
  `tests/test_fisher.py` shape. Numbers are meaningless by design; the test asserts structure.

- **D-32: Fixture facts, attacker corpus and scored questions are 2 SYNTHETIC facts rendered through
  the real `render_family` + Phase-18 fixture paths**, so the disjointness proof and the mask-bin
  token count run on the production code path. The forged ADMITTED record names one fake point whose
  adapter is the tiny model's own saved bytes. No real `LOCKED_FACTS` in `tests/`.

#### Area 7 — The admission record schema

- **D-33: The record carries tallies + the (a)/(b)/(c) breakdown + 44 rows
  `{point_key, arm, leg, verdict, cleared_a, cleared_b, cleared_c}` re-derived and asserted at the
  single write — NEVER the reasons** (those stay in the frontier, quoted by sha256). Plus
  `frontier_sha256`, the pinned baselines, the `apparatus` block and provenance.

- **D-34: `cleared_a/b/c` are RE-DERIVED through `mitigation_gate`'s condition functions
  (`extraction_ceiling` / `dialogue_gap_band` / `retention_cap`) on each point's 21 pinned kwargs.**
  Reason strings are never parsed.

- **D-35: Provenance pins `module_sha256` for `phase27_prereg.py`, `phase27_relearn.py`,
  `mitigation_gate.py`, `erasure_gate.py` and `training/data.py`, plus `git_sha`, `written_utc` and
  the torch version; a test RECOMPUTES every digest from file bytes** (never via the emitter's own hash
  helper) and names ALL drifted modules at once — the 24-09 guard.

- **D-36: The `apparatus` block lists, per leg (calibrate, curve, gate, structural-proof): leg name,
  driver sub-mode, the refusal test's pytest node id, and the CPU end-to-end test's node id**; a test
  asserts every named node id exists in the collected suite.

#### Area 8 — Close-out verification

- **D-37: Before the operator commits the record, each attack sub-mode is invoked ONCE against the
  real MOOT record and WATCHED to refuse** (non-zero exit naming the verdict it read), with the refusal
  text captured in the plan's summary. The repo's "its refusal is watched before it is trusted" rule,
  on the committed record rather than a forged one. No training.

- **D-38: Ledger edits at close (RELRN-01 tick, the 02–05 limitation rows, the ROADMAP checkbox,
  STATE.md) are made BY HAND, with STATE / ROADMAP / REQUIREMENTS snapshotted before and diffed after;
  ZERO `gsd-sdk` mutation handlers** (Phase 26 posture; the handlers corrupted frontmatter in five
  consecutive sessions and re-ticked 23-17 twice).

- **D-39: Zero new runtime dependencies.** `pyproject.toml` stays sha256-identical (RPT-03 counts a
  fourth consecutive milestone); everything above is stdlib + the existing torch/numpy surface.

### Claude's Discretion

- Exact file layout inside `scripts/phase27_prereg.py` vs `scripts/phase27_relearn.py` (frozen
  constants + gate in the former; driver + legs in the latter is the expectation).
- The recorder's in-memory representation and where the per-arm stream file lands under `data/`.
- Tiny-model `ModelConfig` dimensions for the CPU fixture.
- Test file naming, following `tests/test_phase26_prereg.py` / `tests/test_phase26_canary.py`.
- How the kwargs-trace test reads signatures (`inspect.signature` over the real functions is the
  obvious route).

### Deferred Ideas (OUT OF SCOPE)

- **Relearning as a DIAGNOSTIC on the DP points that failed (b)** — attack `dp_n8_sigma0p5…` etc. to
  ask whether a DP adapter with 0/1008 recall is "removed" or "suppressed" relative to the fresh arm.
  Scientifically interesting, but it is relearning on points that did not clear the frontier, which
  SC1 defines as MOOT. Candidate for v5.0, alongside the adversarial-ratio measurement Phase 28 SC4
  already defers.
- **LaunchAgent + sidecar-per-point for an unattended admitted run** — the Phase 25/26 pattern,
  documented as the next step for whichever phase reads ADMITTED (D-14).
- **Attacker-corpus ladder (1 / 4 / 22 rows per fact) and a no-replay attacker variant** — rejected
  for this phase as multipliers on a leg that is not admitted; recorded so a v5.0 threat-model
  discussion starts from them rather than re-deriving them.

No todos matched this phase (`todo.match-phase 27` returned 0).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (`.planning/REQUIREMENTS.md:422-435`) | Research Support |
|----|-------------|------------------|
| RELRN-01 | Absolute recovery ceiling as the binary pre-registered gate — recovered recall ≤ X within a fixed budget Z. | §Standard Stack rows for `extraction_ceiling` (X = 0.006461685297443485, verified), `erasure_is_worth_attempting` (the MOOT shape), the frontier schema (§Frontier Record), the 44-point re-derivation result (38 route-reproduced + 6 route-refused), the Z rule inputs (D-24 thresholds 0.5486 / 0.0604 verified from the control records). Code Ex. 1–3. |
| RELRN-02 | Cost-to-recovery curve vs the never-taught fresh adapter at identical budget and seed. | The 5 pinned fresh adapters (paths + sha256 + seeds, verified), the 2 pinned σ=0 controls, `phase23_prereg.noise_floor`, `mitigation_budget.CURVE_K`, `promote_to_full_fidelity` + `ratchet_k`. Open Question 2 (rung production). |
| RELRN-03 | The curve qualifies the verdict; not a second gate. | Pattern 5 (finding block, never a verdict input); `erasure_gate.MARGIN_K = 2` band. |
| RELRN-04 | Identical budget+seed enforced structurally: shared `TrainConfig`, on-disk diff, data-order sha256. | `train_arm` builds its OWN `TrainConfig` (teach_persona.py:1978) and teach_persona.py is digest-pinned (Open Question 1); checkpoint stores `asdict(train_config)` (checkpoint.py:135) for the off-disk diff; the draw sites for D-29/D-30 (data.py:117, loop.py:640-690) and Open Question 3. |
| RELRN-05 | Recovery fixture disjoint from mitigation training; attacker corpus pre-registered. | `render_family`, `build_question_sets`, `HELDOUT_FAMILY_IDS = {F3,F7,F8}` (phase14_factset.py:826 — NOT phase25_recall), `phase24_adversarial.HELD_OUT_FAMILY` (:214) / `TRAINED_FAMILIES` (:191), `phase18_extraction.build_corpus` (:822) / `corpus_sha256` (:758). Code Ex. 5. |
</phase_requirements>

## Summary

Phase 27 is a pre-registration phase over an already-measured record. Every input the gate needs
exists and was verified this session: `results/phase25_frontier.json` (sha256
`1f182b40c9d7c316e57ecd69acd62c7f6407514b9c675bdf8ec677d3f0cb97d5`, 22,311,714 bytes, exactly one
commit `4030d0e`) tallies **PASS 0 / FAIL 32 / INCONCLUSIVE 6 / REFUSED 6** over its 44 `point_keys`,
so `relearning_is_worth_attempting` reads **MOOT** on the committed numbers. The re-derivation
tripwire works only through the sanctioned route: `phase20_gate_coverage.corrected_point_verdict`
called with `tests/test_phase25_promotion.py:51-60`'s `_route_kwargs` recipe reproduces **38/38**
reached points (verdict, reasons and arm byte-equal) and refuses the six `adv_n64` points with the
same `SystemExit` text the frontier stored; calling the pin `mitigation_point_verdict` directly on
the 21 stored kwargs disagrees on the six `adv_n8` points (pin says FAIL, frontier says INCONCLUSIVE
via the corrected GATE-06), and an AST census (`tests/test_phase20_correction.py:1377`) forbids
calling the pin from any `scripts/` module anyway. The (a)/(b)/(c) breakdown D-07 asks for, computed
through `extraction_ceiling` / `F_Y` / `dialogue_gap_band` / `retention_cap` on the stored kwargs:
**(a) 30**, **(b) 4**, **(c) 1** — not "32 DP points cleared (a)": the two σ=0 controls scored
285/416 and 49/416 and fail (a); the 30 noised DP points sit at 0/416 and 0/1008.

The apparatus half is where the live code pushes back on three decisions' letter (never their
intent): `teach_persona.train_arm` (`:1655`) constructs its own `TrainConfig` from module constants
(`:1978`), accepts no `max_steps`/`train_config`/`on_draw` kwarg, and `scripts/teach_persona.py` is
digest-pinned by `results/phase24_token_budget.json` (guarded live by
`tests/test_phase24_record.py:289`, pin == live verified), so it cannot gain a kwarg; the loop's
`latest.pt` is overwritten every `checkpoint_interval` (`loop.py:933`), so "each rung a saved adapter
from one run" needs a resume chain or a hook; and `get_batch_memmap_masked` is called from
`train()` at two sites (`loop.py:640`, `:672`) that no driver kwarg reaches, so D-29's recorder is
unreachable without a passthrough on `train()` or a rebinding on the loop module. The fresh-arm
precedent that produced the very baseline D-12 pins — `phase23_run.train_never_taught` (`:612`) —
calls `tp.train()` directly with a `TrainConfig` built from `tp.LR/WARMUP_STEPS/MAX_STEPS/...`, which
is the shape that satisfies D-26(i) literally. These are laid out as Open Questions 1–3 with the
exact file:line and the smallest option each; the planner/operator rules, nothing is reopened here.

**Primary recommendation:** ship `scripts/phase27_prereg.py` (CPU-only at import, stdlib + sibling
scripts, `_prove` → `SystemExit`, one commit, `ARTIFACT_GLOB = "results/phase27_*"`) with the gate
reading `verdict.verdict` per point and mapping `None + early_return_reason` → REFUSED; put the
44-verdict tripwire in `tests/` through `corrected_point_verdict` + `_route_kwargs`; build the driver
on `phase25_run.atomic_write_json` + `personacore.provenance.refuse_if_dirty` + the Phase 26 emit
shape; and resolve the three train-path conflicts before Wave 1 by choosing between "`tp.train()`
directly, bins from `tp.build_arm_bins`, one shared `TrainConfig`, `max_steps_override` rung chain"
(Phase 23's own precedent) and "`train_arm` with `tp.MAX_STEPS` rebound at call time".

## Premise Verification (CONTEXT.md vs the live tree)

Every path, constant and signature CONTEXT.md names was opened. Mismatches, all explicit:

| # | CONTEXT.md says | Live tree | Consequence |
|---|---|---|---|
| M1 | `phase25_recall.py` — `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` | They live in `scripts/phase14_factset.py:825-826` (`frozenset({"F1","F2","F4","F5","F6"})`, `frozenset({"F3","F7","F8"})`). `phase25_recall.py` has `RECALL_FIELDS` (:59) and `INSTRUMENT = "teach_persona.score_arm"` (:58) only. | Import from `phase14_factset` (`fs.HELDOUT_FAMILY_IDS`), as `phase14_recall.build_question_sets` (:1053-1054) does. |
| M2 | `SEED_LADDER` alongside `phase23_prereg` | `scripts/phase23_run.py:146` `SEED_LADDER = (1337, 2024, 1338, 2025, 1339)`. `scripts/phase23_prereg.py:346` has `_SEED_LADDER = (5, 4, 3)` — a seed-COUNT ladder for `choose_n_seeds`, a different object. `phase23_run` imports `teach_persona` (torch) at module scope (`:105`). | `phase27_prereg.py` (CPU-only at import) pins the five seeds from `results/phase23_never_taught_training.json::seeds` (verified `[1337, 2024, 1338, 2025, 1339]`, in that order) and a TEST asserts equality with `phase23_run.SEED_LADDER`. |
| M3 | D-02: tripwire calls `mitigation_gate.mitigation_point_verdict` on each point's 21 kwargs | Direct pin call reproduces 38 of 44 verdict strings but DISAGREES on the six `adv_n8` points (pin FAIL, frontier INCONCLUSIVE — the route's corrected GATE-06 appends a last reason and overrides). The route `phase20_gate_coverage.corrected_point_verdict(**_route_kwargs)` reproduces 38/38 exactly and refuses 6/6. `tests/test_phase20_correction.py:1377` goes RED on any `scripts/` or `src/` caller/importer of the pin outside `phase20_gate_coverage.py`. | The tripwire test calls the ROUTE (Code Ex. 2). `phase27_prereg.py` must not import or call the pin; it counts `verdict.verdict` strings. |
| M4 | D-03/D-33: per-point `verdict.verdict` | Six points (`adv_n64_*`) carry `verdict.verdict: null` with `early_return_reason: "REFUSED by the sanctioned route before the pin was reached"` and `reasons[0]` = the route's `SystemExit` text; `verdicts.tallies.REFUSED = 6` counts them. | The gate's domain check accepts `None` only when `early_return_reason` is non-null, and the 44-row record writes `"REFUSED"` for those rows (derived, disclosed). |
| M5 | D-07 example "32 DP points cleared (a) at 0/416 and failed (b) at 0/1008" | Cleared (a): **30** (15 `dp_n8` σ>0 + 15 `dp_n64` σ>0). The two σ=0 controls scored 285/416 and 49/416 and FAIL (a); they clear (b) (790/1008, 87/1008). Cleared (b): 4 (both controls + `adv_n8` ratio 0 / 0.25). Cleared (c): 1 (`dp_n8` control). | The MOOT reasons are generated from the counts, so the record will say 30, not 32. Phase 28 quotes the record. |
| M6 | D-13/D-26(i): one shared `TrainConfig` passed to all `train_arm` calls; only `max_steps` and data differ | `train_arm(arm, *, facts, family_ids, second_person=False, replay_ratio=0.0, adversarial_ratio=0.0, seed=SEED, prefix="phase14", dp_sigma=None, dp_clip_norm=None, resume_from=None)` (`teach_persona.py:1655-1668`) takes no `TrainConfig` and no `max_steps`; it builds `TrainConfig(lr=LR, warmup_steps=WARMUP_STEPS, max_steps=MAX_STEPS, batch_size=BATCH_SIZE, weight_decay=WEIGHT_DECAY, seed=seed, **dp_accum)` at `:1978-1986`. `teach_persona.py` sha256 `3c1e6c55…` is pinned by `results/phase24_token_budget.json::provenance.module_sha256` (live == pin verified) under `tests/test_phase24_record.py:289`. | Open Question 1. |
| M7 | D-25: "each rung a saved adapter from one run" | `train()` saves `checkpoint_path` in-loop every `checkpoint_interval` (`loop.py:925-948`) and again at end (`:960`) — the SAME path, overwritten. `train_arm` exports exactly one adapter at end (`:2073`) and `refuse_if_exists` refuses a present adapter (`:410`). | Open Question 2. |
| M8 | D-29: `on_draw=None` on `get_batch_memmap_masked`; "the driver passes a recorder" | Signature `get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, device)` (`data.py:93`), draw at `:117` (CONTEXT's line is correct). Its callers are closures inside `train()` — `loop.py:640-647` (teaching) and `:672-690` (`replay_fn`, one call per micro-batch) — and `train()`/`train_arm` expose no hook. `data.py` is NOT digest-pinned by any `results/*.json` (`phase21_privacy_unit.json` mentions it in prose only). | Open Question 3. |
| M9 | D-27: "fresh curve at all 5 SEED_LADDER seeds (they exist on disk…)" | On disk are five 200-step ENDPOINT adapters (`checkpoints/phase23_never_taught_seed*_adapter.pt`, cosine schedule over `max_steps=200`), not rungs of a 400-step run. | The five adapters are the pinned reference and D-19's floor source at the 200-step reading; a fresh CURVE requires retraining under the 400-step config (never in this phase). Disclose in the apparatus block. |
| M10 | `phase25_run.py` — `refuse_if_exists` | Not defined there; `refuse_if_exists(paths, *, expected=())` is `teach_persona.py:410`. `phase25_run.py` has `atomic_write_json` (:118) and `device()` (:407). | Import from `teach_persona` (torch at import) or reproduce the 8-line refusal in the driver's CPU-safe half; Phase 26's `emit()` used `RECORD.exists()` + `--force` (`phase26_canary.py:475`). |
| M11 | `tests/test_phase23_resume.py` as a `train_arm` CPU precedent | `:231` and `:681` call `train_arm` only up to the guards (`facts=[]`); the real end-to-end training precedent at fixture scale is `tests/test_phase22_wiring.py:799` (`test_end_to_end_writes_no_scored_artifact`, drives `tp.main` → `train_arm` → `train()` for 2 steps under `_e2e_env`, `:705`). | Mirror `_e2e_env`. |
| M12 | `_TRAIN_ARM_CALL_SITES` not mentioned | `tests/test_phase23_resume.py:60-130` registers every raw `grep -rn "train_arm("` hit in `scripts/` and `tests/` (29 rows, code AND prose) and asserts the count and per-file counts (`:262-282`). | Every new `train_arm(` occurrence in Phase 27 code, docstrings or tests must be added to the register or the suite goes RED. |

Everything else CONTEXT.md names is at the stated location: `train_arm` :1655; constants :1570-1585;
`get_batch_memmap_masked` :93 / draw :117; `TrainConfig` `config.py:98`; `HELD_OUT_FAMILY`
`phase24_adversarial.py:214`; `train_never_taught` `phase23_run.py:612`; `extraction_ceiling`
`mitigation_gate.py:352`; `MARGIN_K = 2` `erasure_gate.py:86`; `CURVE_K = 16`
`mitigation_budget.py:425`; `K = 48` `phase18_extraction.py:93`; `GATED_TIER = "core_held_out"` :173;
the `4030d0e` frontier commit; Phase 26's operator commit `8652c15`; `phase26_prereg.py` at one commit
`e6a8851`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Admission gate + frozen constants/baselines/corpus definition | `scripts/phase27_prereg.py` (pure Python, CPU-only at import) | — | Ancestry-guarded pre-registration; must import without torch (Phase 26 precedent) so the guard test and the `admit` sub-mode run anywhere. |
| Frontier read + 44-verdict re-derivation tripwire | `tests/test_phase27_prereg.py` | `phase27_prereg.py` reads only `verdict.verdict`/tallies | The pin caller census confines the route call to `tests/` (or `phase20_gate_coverage`). |
| Record emission (`results/phase27_admission.json`) | `scripts/phase27_relearn.py admit` | `phase25_run.atomic_write_json`, `provenance.refuse_if_dirty` | Write-once, atomic, dirty-tree refused, git never touched (D-15). |
| Attack legs (calibrate / curve / gate / structural-proof) | `scripts/phase27_relearn.py` sub-modes | `teach_persona` (bins, train, score), `phase18_extraction` (scorer), `phase25_run` (draw cache) | Torch imported lazily inside legs; each leg reads the committed record first and refuses (D-08). |
| Offset-stream capture | `src/personacore/training/data.py` (+ passthrough, see OQ3) | driver recorder → `data/phase27_*` | Only byte-neutral capture point is the draw at `data.py:117`. |
| Structural proofs (shared config, off-disk diff, stream sha256) | driver + `tests/test_phase27_relearn.py` | `personacore.checkpoint` (stores `asdict(train_config)`) | Evidence is read back off disk, not from memory. |
| Ledger edits at close | operator, by hand (D-38) | — | Zero `gsd-sdk` mutation handlers. |

## Standard Stack

No packages are installed. D-39 holds: everything below is stdlib or an existing repo module.
`.venv` is Python 3.11.15 with torch 2.7.1 (verified by `.venv/bin/python -c`), pytest ~= 9.

### Core (imported, never re-implemented) — signatures read from source this session

| Symbol | Location | Signature / value (verified) | Used for |
|---|---|---|---|
| `erasure_is_worth_attempting` | `scripts/erasure_gate.py:173` | `(attack_successes, attack_questions, base_successes, base_questions) -> (bool, reason)`; MOOT reason opens `"MOOT: …"`; missing measurement → `(False, "INCONCLUSIVE: …")` (two-valued — why D-03 goes three-valued) | The shape SC1 names |
| `wilson_upper_bound` | `erasure_gate.py:139` | `(successes, n, z=_Z_ONE_SIDED_95)`; `_Z_ONE_SIDED_95 = 1.6448536269514722` (:90) | recovery upper bound |
| `MARGIN_K` | `erasure_gate.py:86` | `2` | D-19 band |
| `VERDICTS` | `erasure_gate.py:136` | `("SUCCESS","FAILURE","INCONCLUSIVE")` | precedent only |
| `V4_VERDICTS` | `scripts/mitigation_gate.py:85` | `("PASS","FAIL","INCONCLUSIVE")` | membership check on per-point strings |
| `ARMS` | `mitigation_gate.py:156` | `("dp","adversarial")` | `verdict.arm` domain |
| `F_Y` / `F_C` | `:203` / `:217` | `0.7` / `0.5` | D-24 threshold |
| `K_RUNGS` | `:254` | `(48, 24, 16, 8)` | `ratchet_k` menu |
| `NEVER_TAUGHT_ARM` | `:341` | `"never-taught"` | provenance `arm` string (matches the pinned record) |
| `extraction_ceiling` | `:352` | `(*, nontarget_successes, nontarget_questions, extraction_noise_floor, extraction_floor_provenance) -> float`; on the frontier's control kwargs returns **0.006461685297443485** (= `wilson_upper_bound(0, 416) + 2 × 0.0`) | X, imported never retyped (D-04) |
| `tolerance_report` | `:449` | `(*, ceiling, n_questions) -> (tolerated, fraction, sentence)`; at 416 → `0`, `0.0`, "ZERO TOLERANCE…" | disclosure sentence |
| `dialogue_gap_band` | `:526` | `(*, control_gap, gap_noise_floor) -> (lo, hi)` | D-34 `cleared_c` |
| `retention_cap` | `:595` | `(*, retention_noise_floor) -> float` | D-34 `cleared_c` |
| `mitigation_point_verdict` | `:637` | 21 keyword-only args → `(verdict, reasons, arm)` | NEVER called from `scripts/` (census) |
| `ratchet_k` | `:917` | `(*, fixed_k, proposed_k)`; refuses decreases and off-menu K | D-21 |
| `promote_to_full_fidelity` | `:963` | `(*, verdict, reasons, curve_k, full_k) -> (bool, reason)` | K=16 → 48 at Z |
| `REPLICATION_PENDING_MARKER` | `:149` | the GATE-08 opener | read back by promotion |
| `corrected_point_verdict` | `scripts/phase20_gate_coverage.py:522` | 24 keyword-only args = the 21 minus `sweep_extraction_rates` plus `sweep_extraction_successes`, `sweep_extraction_questions`, `sweep_heldout_recalls`, `retention_floor_provenance`; returns the pin's 3-tuple; `SystemExit` on the `adv_n64` floor refusal | D-02 tripwire (tests only) |
| `ADAPTER_REGIME` / `SUPERSEDED_SWEEP_SENTINEL` | `:364` / `:519` | `"adapter"` / `(0.0, 1.0)` | `_route_kwargs` |
| `wilson_lower_bound` | `:124` | `(successes, n, z=…)` | if a lower bound is ever reported |
| `CURVE_K` / `FULL_FIDELITY_K` / `STEP_BUDGET` / `N_CONTROL_SEEDS` | `scripts/mitigation_budget.py:425/473/508/544` | `16 / 48 / 200 / 5` | D-21, D-23 |
| `MATCHED_CONTROL_NOISE_FLOOR` | `:277` | `0.0267857142857143` | disclosure beside Y (n=8) |
| `noise_floor` | `scripts/phase23_prereg.py:143` | `(readings) -> max - min`; refuses `< 2` readings or non-finite | D-19 floor |
| `SEED_LADDER` | `scripts/phase23_run.py:146` | `(1337, 2024, 1338, 2025, 1339)` (torch at import via `teach_persona`, :105) | test-side equality vs the pinned seeds |
| `train_never_taught` | `phase23_run.py:612` | builds `tp.TrainConfig(lr=tp.LR, warmup_steps=tp.WARMUP_STEPS, max_steps=tp.MAX_STEPS, batch_size=tp.BATCH_SIZE, weight_decay=tp.WEIGHT_DECAY, seed=seed)` and calls `tp.train(...)` DIRECTLY on `DIALOG_TRAIN_BIN/MASK` with `eval_interval=tp.EVAL_INTERVAL`, `checkpoint_interval=tp.CHECKPOINT_INTERVAL` | the fresh-arm recipe that produced D-12's pinned baseline |
| `K` / `ASR_RUNGS` / `ATTACK_FAMILIES` / `GATED_TIER` / `REPORTED_TIER` | `scripts/phase18_extraction.py:93/98/146/173/175` | `48 / (1,4,16,48) / ("A1-mild","A1-aggressive","A2","A3") / "core_held_out" / "core_taught"` | seed stride, families, tier |
| `build_corpus(tok)` / `corpus_sha256(corpus)` / `canonical_json` | `:822 / :758 / :746` | corpus in memory over `factset.LOCKED_FACTS` (lazy import) → 864 prompts, 416 on the gated tier; digest over canonical JSON | D-17 fixture; fixture facts must be injected by monkeypatching `phase14_factset.LOCKED_FACTS` (see Pitfall 6) |
| `HELD_OUT_FAMILY` / `TRAINED_FAMILIES` / `TRAINED_TIER` | `scripts/phase24_adversarial.py:214/191/180` | `"A2"` / `("A1-mild","A1-aggressive","A3")` / `"core_taught"` | D-17 (ii) |
| `Fact` | `scripts/phase14_factset.py:51` | `NamedTuple(id, slot, value, tier)` | synthetic facts (D-32) — precedent `tests/test_phase21_replay_volume.py:119` |
| `LOCKED_FACTS` / `FAMILY_IDS` / `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS` | `:390 / :656 / :825 / :826` | 8 facts / F1–F8 / `{F1,F2,F4,F5,F6}` / `{F3,F7,F8}` | D-17, D-18 |
| `render_family` | `:833` | `(family_id, fact, *, second_person=False, forms=None)` | D-18 corpus, D-32 |
| `build_question_sets` | `scripts/phase14_recall.py:1026` | `(facts) -> (taught, held_out, excluded)`; drops questions containing their own value | recall fixture |
| `load_adapted_model` / `complete_question` / `score_question` | `phase14_recall.py:712 / :901 / :315` | `(device, adapter_path=None)`; `(model, tok, question, device, forbid, *, index)`; `(completions, value)` | the recall instrument's two calls (Phase 26 stubbed exactly these: `tests/test_phase26_canary.py:557-585`) |
| `SEED` / `BLOCK_SIZE` | `scripts/teach_persona.py:104/105` | `1337 / 256` | |
| `REPLAY_WINDOWS_PER_FACT` / `replay_window_budget` | `:179 / :182` | `4` / `(n_facts, block_size=BLOCK_SIZE)` tokens | D-20 (DP arms draw `replay_window_budget(n)//BLOCK_SIZE` windows per step at train time, `:1970-1972`) |
| `DP_ARMS` / `ADV_ARMS` | `:294 / :310` | `("dp_n8","dp_n64") / ("adv_n8","adv_n64")` | |
| `arm_outputs` | `:344` | `(arm, *, prefix="phase14") -> {"bin","mask","csv","checkpoint","adapter"}`; adapter `checkpoints/{prefix}_{arm}_adapter.pt` | paths |
| `refuse_if_exists` | `:410` | `(paths, *, expected=())` → `SystemExit` naming the file | D-08 write-once |
| `render_episodes` | `:495` | `(facts, family_ids, *, second_person=False) -> [(q, a)]` | D-18 rows |
| `build_arm_bins` | `:1279` | `(arm, facts, family_ids, *, second_person=False, replay_ratio=0.0, adversarial_ratio=0.0, seed=SEED, prefix="phase14", resume_from=None) -> (tok, stats, paths)` | teaching-recipe data path |
| `LR / WEIGHT_DECAY / BATCH_SIZE / MAX_STEPS / WARMUP_STEPS / EVAL_INTERVAL / CHECKPOINT_INTERVAL` | `:1570/1574/1576/1582/1583/1584/1585` | `3e-4 / 0.0 / 8 / 200 / 20 / 10 / 50` | budget symbols |
| `train_arm` | `:1655` | see M6; returns `{"arm","paths","stats","final_train_loss","ppl_adapter_on","ppl_adapter_off","scored_targets"}` (`:2114-2122`) — NO config in the return | |
| `score_arm` | `:2440` | `(arm, facts, adapter_path, device)` | the `phase25_recall` instrument |
| `train` | `src/personacore/training/loop.py:235` | keyword-only: `train_config, runtime_config, model, model_config, corpus_path, train_bin, val_bin, train_mask_bin, val_mask_bin, replay_bin, replay_mask_bin, replay_windows, fact_bin, n_facts, eos_id=8184, fixed_batch, scaler, resume_from, checkpoint_path, best_checkpoint_path, log_path, max_steps_override, eval_interval=1, checkpoint_interval, sample_interval, sample_prompt, …`; `target_steps = max_steps_override or train_config.max_steps` (`:800`) | direct-call option (OQ1/2) |
| `get_batch_memmap_masked` | `src/personacore/training/data.py:93` | `(bin_path, mask_path, batch_size, block_size, device) -> (x, y)`; `ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)` at `:117` | D-29 site |
| `build_scheduler` | `src/personacore/training/schedule.py:42` | warmup+cosine over `train_cfg.warmup_steps / max_steps` | why `max_steps` shapes the trajectory (OQ2) |
| `TrainConfig` | `src/personacore/config.py:98` | `lr=3e-4, batch_size=64, max_steps=5000, warmup_steps=100, grad_clip=1.0, grad_accum_steps=1, weight_decay=0.1, seed=1337` | D-26 |
| `ModelConfig` / `RuntimeConfig` | `config.py:77 / :48` | `n_head=6, n_embd=384, …` defaults; `RuntimeConfig(device="cpu")` | tiny fixture |
| `save_checkpoint` / `load_checkpoint` | `src/personacore/checkpoint.py:88 / :156` | stores `"train_config": asdict(train_config)` (`:135`) and `"rng": {"numpy": np.random.get_state(), …}` (`:137-139`); restore at `:184-186` | D-26(ii) off-disk diff; resume bit-identity |
| `export_adapter` | `checkpoint.py:253` | `(path, *, adapter, lora_config, base_fingerprint) -> dict` | rung adapters |
| `inject_lora` / `mark_only_lora_trainable` / `snapshot_params` / `lora_state_dict` / `adapter_disabled` | `src/personacore/lora/inject.py:29/46/58/67/157` | | tiny fixture training |
| `atomic_write_json` | `scripts/phase25_run.py:118` | `(path, blob) -> path`; `json.dumps(sort_keys=True)`, temp in dest dir, fsync, `os.replace` | record write |
| `device` | `phase25_run.py:407` | resolves `RuntimeConfig().device` lazily | legs (never at import) |
| `draw_point_shapes` / `score_point` | `phase25_run.py:458 / :586` | `(point_key, *, adapter, adapter_sha256, corpus, corpus_sha256, k, state, dry_run=False) -> (blob, digests)`; `(blob, values)` → per-question rows | extraction scoring at K=16, cache under `data/` keyed `(adapter_sha256, corpus_sha256, k)` (`:177`) |
| `score_point` (recall) | `scripts/phase25_recall.py:114` | `(point_key, *, dry_run=False, heartbeat_path=None) -> (status, blob)`; reads a frontier point record by key | recall REPORTED beside extraction (D-16) — Phase 27 arms are not frontier points; call `teach_persona.score_arm` directly as Phase 26 did with its two calls |
| `FRONTIER_RECORD` / `ORDERED_POINT_KEYS()` | `scripts/phase25_record.py:107 / :253` | `results/phase25_frontier.json`; the 44 keys | D-06, D-22 |
| `PIN_KWARGS` | `scripts/phase25_promotion.py` (module constant, 21 names; CPU-only import verified) | equals `frontier.verdicts.pin_kwargs` | `_route_kwargs` |
| `RETENTION_FLOOR_DISCLOSURE["seeds"]` | `scripts/phase25_condition_c.py` | `[1337, 2024]` | `_route_kwargs` |
| `git_sha` / `refuse_if_dirty` | `src/personacore/provenance.py:28 / :47` | `(default="unknown")`; `(*, who, detail, pathspec=(), cwd=None)` → `SystemExit` | provenance, emit guard |
| `normalized` | `scripts/_prose.py:35` | `(text)` | any prose pin |
| `sweep_is_active` / `SWEEP_ACTIVE_ENV_VAR` | `tests/conftest.py` | env `PERSONACORE_SWEEP_ACTIVE` | not needed (no MPS run), keep tests unconditional |

### Measured inputs the gate consumes — read 2026-09-14

**`results/phase25_frontier.json`** (top-level keys, in order): `governs, record, point_key_grammar,
point_keys, arms, axis_for_arm, held_out_generalization, epsilon_report, verdicts,
never_taught_floor, retention_leg_binds_at_anchor, retention_squeeze_is_the_frontier,
retention_floor_disclosure, dialogue_floor_recipe_mismatch, dialogue_floor_sensitivity,
mechanism_pin_disclosure, adversarial_makes_no_formal_claim, provenance, points`.

- `point_keys`: 44, order `dp_n8_sigma{0,0.5,0.7,1,1.5,2,3,4,6,8,12,16,24,32,50,80}`, then `dp_n64_…`
  (same 16), then `adv_n8_ratio{0,0.25,0.5,1,1.5,1.909091}`, then `adv_n64_…`. Grammar
  `{arm}_{axis}{value:.6f}` with `.` → `p`.
- `verdicts.tallies`: `{"PASS": 0, "FAIL": 32, "INCONCLUSIVE": 6, "REFUSED": 6}`;
  `verdicts.tallies_by_leg`: `dp_n8` FAIL 16, `dp_n64` FAIL 16, `adv_n8` INCONCLUSIVE 6, `adv_n64`
  REFUSED 6. `verdicts.pin_kwargs` = the 21 names. `verdicts.extraction_ceiling` =
  `{X: 0.006461685297443485, fraction: 0.0, n_questions: 416, tolerated: 0, tolerance_sentence}`.
  `verdicts.curve_k: 16`, `full_fidelity_k: 48`, `capacity_branch: "null-at-both-capacities"`,
  `verdicts.refused` and `verdicts.leg_refusals` carry the `adv_n64` refusal text,
  `verdicts.control_readings[leg].recall_counts = {taught: [k, 1008], heldout: [k, 648]}`.
- `points[k]` (79 keys) includes `adapter_path`, `adapter_sha256`, `arm`, `axis`, `seed`, `sigma`,
  `composed_steps`, `taught_recall{numerator, denominator, questions, draws_per_question, rate,
  per_family}`, `heldout_recall`, `condition_c{…}`, `verdict`, `promotion{promote, reason}`,
  `training{…}`.
- `points[k].verdict` (31 keys): the 21 pin kwargs (with `sweep_extraction_rates` /
  `sweep_taught_recalls` = the sentinel `[0.0, 1.0]`), plus `verdict`, `reasons`, `leg`, `k`,
  `k_source`, `route` (`"phase20_gate_coverage.corrected_point_verdict (D-34)"`),
  `early_return_reason`, `recall_counts`, `whole_curve_inputs{point_keys,
  sweep_extraction_successes, sweep_extraction_questions, sweep_taught_recalls,
  sweep_heldout_recalls}`. `verdict.verdict` ∈ `{"FAIL", "INCONCLUSIVE", null}`; `null` only on
  the six `adv_n64` points with `early_return_reason` set (M4).
- `provenance`: `git_sha 578a1ac…`, `torch_version "2.7.1"`, `gate_module_sha256 86db4798…` (live
  `scripts/mitigation_gate.py` sha256 begins `86db479876ebeb2b` — matches),
  `budget_module_sha256 1b35aa88…` (matches live), `inputs.point_records[key]{path, sha256}`.
- `never_taught_floor`: `seed 1337`, `nontarget_successes 0 / 416`, `draws_per_question 16`,
  `total_draws 6656`, `extraction_noise_floor 0.0`, `record results/phase23_never_taught.json`.

**Re-derivation results (this session, CPU):** route (`corrected_point_verdict` with
`_route_kwargs`) → 38/38 `(verdict, reasons, arm)` equal, 6/6 `SystemExit` on `adv_n64`; direct pin →
6 mismatches (`adv_n8_*`: pin FAIL vs stored INCONCLUSIVE). Breakdown over the 38 reached points:
cleared (a) 30, (b) 4, (c) 1; by leg — `dp_n8`: a 15, b 1, c 1; `dp_n64`: a 15, b 1, c 0; `adv_n8`:
a 0, b 2, c 0.

**Pinned baselines (D-12), verified from the records:**

| Entry | Path | sha256 | seed | reading |
|---|---|---|---|---|
| never-taught 1337 | `checkpoints/phase23_never_taught_seed1337_adapter.pt` | `8da8c2c25bd2b7c951a28ca80b11d38478269a45408aafa9276f9aaa8da1a9e7` | 1337 | extraction 0/416 @K=16 |
| never-taught 2024 | `…seed2024_adapter.pt` | `da9ac275929314605d126d8a7a028c51e687fa8d3974431f75a94886f0f4e04a` | 2024 | 0/416 |
| never-taught 1338 | `…seed1338_adapter.pt` | `8edff1e229a052b331d3fd9a85539cf8f7d505501bd35f51dd9634dae20ff12d` | 1338 | 0/416 |
| never-taught 2025 | `…seed2025_adapter.pt` | `ed838985b42c115fbb2073145f431d7a865f743734274501f53b918e83e24ab2` | 2025 | 0/416 |
| never-taught 1339 | `…seed1339_adapter.pt` | `d88b6647e71421d658e75cd92f6ab80e37143067adc0d0aa59cbeb35aaa25809` | 1339 | 0/416 |
| control n=8 (`dp_n8_sigma0p000000`) | `checkpoints/phase25_sigma0p000000_dp_n8_adapter.pt` | `3fab020306390e2d1163bb483c66628e4b54085ba3018595200f3c8aa79cef64` | 1337 | taught 790/1008 = 0.7837, held-out 346/648, extraction 285/416 |
| control n=64 (`dp_n64_sigma0p000000`) | `checkpoints/phase25_sigma0p000000_dp_n64_adapter.pt` | `433c75c6f2c845f0c9bcc79fa795c0d85a85de782e76900a94dfdf4e8ee7c9f5` | 1337 | taught 87/1008 = 0.0863, held-out 35/648, extraction 49/416 |

Sources: `results/phase23_never_taught_training.json::adapters` (1,352,303 bytes each,
`max_steps 200`, `batch_size 8`, `git_sha 5303819…`), `results/phase23_never_taught.json::readings
[0.0 ×5]`, `results/phase25_point_dp_n8_sigma0p000000.json`, `…dp_n64_sigma0p000000.json`,
`results/phase23_matched_control.json` (`central_reading 0.7837301587301587`, `central_reading_seed
1337`, `floor 0.0267857142857143`, `reduction phase23_prereg.noise_floor`). D-24 thresholds:
0.7 × 0.7837301587301587 = 0.5486; 0.7 × 0.08630952380952381 = 0.0604 (both as CONTEXT states).
The five fresh adapters live under gitignored `checkpoints/` — tests must `skipif` absent, as
`tests/test_phase26_canary.py`'s `needs_adapters` does.

### Alternatives Considered (all closed by locked decisions)
| Instead of | Could Use | Tradeoff |
|---|---|---|
| Route call in the tripwire | Direct pin call | Disagrees on 6 points and is censused out of `scripts/` — rejected by measurement. |
| `phase25_recall.score_point` for recall | `teach_persona.score_arm(arm, facts, adapter_path, device)` | `score_point` resolves a FRONTIER point by key; Phase 27 arms are not frontier points. Use `score_arm` (the instrument `phase25_recall.INSTRUMENT` names). |

**Installation:** none. `pyproject.toml` must stay byte-identical (D-39; RPT-03).

## Package Legitimacy Audit

Not applicable — this phase installs no packages (D-39). slopcheck was not run; there is nothing to
audit. Any plan task that would `pip install` anything is out of scope by decision.

## Architecture Patterns

### System Architecture Diagram

```
results/phase25_frontier.json ─┐ (sha256 pinned both ways, one commit 4030d0e)
                               ▼
  scripts/phase27_prereg.py ── relearning_is_worth_attempting(points)
   • reads verdict.verdict per point (None+early_return_reason → REFUSED)
   • asserts tallies re-derive from the 44 entries; 44 present → MOOT | else INCONCLUSIVE
   • X = mitigation_gate.extraction_ceiling(**control kwargs)   (never retyped)
   • Z rule, band, cap, rung ladder, baselines, corpus sha  (frozen constants)
                               │
                               ▼  (one call, CLI sub-mode `admit`)
  scripts/phase27_relearn.py admit ── refuse_if_dirty → refuse if record exists
   → cleared_a/b/c via extraction_ceiling / F_Y / dialogue_gap_band / retention_cap
   → atomic_write_json(results/phase27_admission.json)   [driver never touches git]
                               │
        ┌──────────────────────┼───────────────────────┐
        ▼                      ▼                       ▼
   calibrate               curve                    gate / structural-proof
   (READ record;           (READ record;            (READ record;
    refuse unless           refuse unless            refuse unless ADMITTED;
    ADMITTED)               ADMITTED)                baseline= REQUIRED kwarg)
        │                      │                       │
        └── train path (teach_persona bins → train() → get_batch_memmap_masked[on_draw])
            → rung adapters → phase25_run.draw_point_shapes/score_point (K=16)
            → score_arm recall (reported) → cost curve → band → verdict at Z (K=48 promote)
        ▲
   tests/ forge an ADMITTED record in tmp + tiny GPT + real tokenizer → the ONLY exercise
```

### Recommended Project Structure (only what this phase ships)
```
scripts/phase27_prereg.py          # gate, frozen constants, baselines, corpus definition, ARTIFACT_GLOB
scripts/phase27_relearn.py         # argparse sub-modes admit/calibrate/curve/gate/structural-proof; torch lazy
src/personacore/training/data.py   # + on_draw=None on get_batch_memmap_masked (byte-neutral when None)
src/personacore/training/loop.py   # + on_draw=None passthrough on train() (OQ3, if chosen)
tests/test_phase27_prereg.py       # ancestry guard, domain, both-ways pin, 44-verdict tripwire (route), seeds==SEED_LADDER
tests/test_phase27_relearn.py      # refusal-RED per leg, e2e tiny run, kwargs trace, disjointness, on_draw byte-identity,
                                   #   provenance recompute, node-id existence, register update in test_phase23_resume.py
results/phase27_admission.json     # operator-committed (D-15)
data/phase27_<arm>_offsets.bin     # gitignored per-arm offset stream (uint64 + bin path) — discretionary name
```

### Pattern 1: Pre-registration module, CPU-only at import — `scripts/phase26_prereg.py`
`_REPO_ROOT` + `sys.path.insert(0, scripts)`; `COMMITTED = "<date>"`; `ARTIFACT_GLOB =
"results/phase27_*"`; `_prove(condition, message)` → `SystemExit("[phase27_prereg] …")`; verdict
domain as a tuple; every threshold imported by object identity (`RULE is …` asserted in tests).
No torch, no `teach_persona`, no `phase14_*` at module scope (the Phase 26 docstring lists exactly
these exclusions). `phase25_promotion` and `phase20_gate_coverage` ARE importable CPU-only (verified).

### Pattern 2: Ancestry guard — `tests/test_phase26_prereg.py:52-98`
`_assert_frozen_before(prereg_artifact, tracked)`: refuses shallow clones, takes `adds[-1]` (earliest
add), asserts every prereg commit is a STRICT ancestor of every tracked artifact's first add, and
`bool(checked) == bool(tracked)`. Phase 27: `tracked = git ls-files results/phase27_*`. Keep the
frontier one-commit assertion (`tests/test_phase25_close.py:321-324` already enforces it).

### Pattern 3: Three-valued gate mirroring `erasure_is_worth_attempting`
Return `(verdict, reasons)` with `verdict ∈ ("ADMITTED","MOOT","INCONCLUSIVE")`; INCONCLUSIVE
takes precedence (missing frontier, `len(point_keys) != 44`, tally mismatch, a `verdict.verdict`
outside `V4_VERDICTS` that is not the `None + early_return_reason` REFUSED form). MOOT reasons are
generated from the counts (tallies by leg + (a)/(b)/(c) counts). ADMITTED carries the PASS keys in
`point_keys` order (D-22).

### Pattern 4: Driver emit + write-once + provenance — `scripts/phase26_canary.py:475-716`
`refuse_if_dirty(who=…, detail=…, pathspec=("scripts/","src/","results/"))` before hashing anything
(26-REVIEW WR-03); `RECORD.exists() and not overwrite → SystemExit`; `frontier_sha256 =
_sha256(phase25_record.FRONTIER_RECORD)`; `prereg_module_sha256`; `emitted_git_sha = git_sha()`;
`atomic_write_json`. `build_parser()` at `:793` (`--points`, `--heartbeat`, `--dry-run`, `--emit`,
`--force`); `main(argv=None) -> int` at `:810`. Phase 27 uses `argparse` subparsers
(`admit|calibrate|curve|gate|structural-proof`), each sub-mode a function whose first statement
reads the committed record and refuses.

### Pattern 5: Instrument qualifies, never decides (RELRN-03)
The record's `cost_curve` is a finding block `{leg, rungs: [{steps, scored_tokens, fresh: {...},
control: {...}, mitigated: {...}, band_lo, band_hi, inside_band}], z: {fresh_first_clear,
control_first_clear, z}}` separate from `verdict`; a test asserts the verdict function's signature
contains no curve/band parameter (`inspect.signature`).

### Pattern 6: Two-conjunct refusal (Phase 23) and watched-RED-on-a-copy (`tests/test_phase25_calibrate.py:571-593`)
Each leg refuses unless `record["verdict"]["verdict"] == "ADMITTED"` AND the record is tracked
(`git ls-files results/phase27_admission.json` non-empty) — the committed record, never a live
re-read. Tests forge a MOOT/INCONCLUSIVE copy in `tmp_path` and watch each sub-mode exit non-zero
naming the verdict it read.

### Anti-Patterns to Avoid
- **Calling/importing `mitigation_point_verdict` from `scripts/`** — reddens
  `tests/test_phase20_correction.py:1377`.
- **A `--dry-run` battery with no live path** — the Phase 25 incident; D-10's e2e + kwargs trace.
- **Editing `scripts/teach_persona.py`** — reddens `tests/test_phase24_record.py:289` (digest pin).
- **Editing `scripts/phase25_prereg.py`/`phase26_prereg.py`/`mitigation_gate.py`/`erasure_gate.py`** —
  ancestry guards (`tests/test_phase26_prereg.py:95`, `test_phase20_prereg.py`, `test_phase16_prereg.py`).
- **Re-emitting the frontier** — `tests/test_phase25_close.py:321` and D-06.
- **`assert` in scripts** — `python -O` strips it; use `_prove` → `SystemExit`.
- **Any `gsd-sdk` mutation handler on STATE/ROADMAP/REQUIREMENTS** (D-38).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Upper bound on recovery | a Wald/Wilson copy | `erasure_gate.wilson_upper_bound` | second estimator = second number free to drift |
| X | a literal `0.006462` | `mitigation_gate.extraction_ceiling(**control kwargs)` | D-04; provenance `_prove`s fire on the real call |
| Y thresholds | `0.5486`, `0.0604` | `mitigation_gate.F_Y * control_taught_recall` read from the control records | D-24 |
| 44-verdict re-derivation | a re-implementation of the three conditions | `phase20_gate_coverage.corrected_point_verdict(**_route_kwargs)` | only route that reproduces the frontier (M3) |
| Seed spread | stdev | `phase23_prereg.noise_floor` | D-19; refuses < 2 readings |
| K promotion | `if k == 16: k = 48` | `mitigation_gate.promote_to_full_fidelity` (calls `ratchet_k`) | D-21 |
| Atomic JSON | `path.write_text` | `phase25_run.atomic_write_json` | torn-write history (`phase23_run.py:4470`) |
| Dirty-tree refusal | `git status` parsing | `personacore.provenance.refuse_if_dirty` | the WR-03 lesson |
| Extraction scoring | a new scorer | `phase25_run.draw_point_shapes` + `score_point` (`phase18_extraction.score_records`) | ancestry-guarded instrument |
| Recall scoring | a new loop | `teach_persona.score_arm` / `phase14_recall.complete_question` + `score_question` | the `phase25_recall` instrument |
| Teaching rows | hand strings | `teach_persona.render_episodes` → `phase14_factset.render_family` | D-18/D-32 |
| Config diff | manual field list | `dataclasses.asdict(TrainConfig)` vs `checkpoint["train_config"]` | already stored (`checkpoint.py:135`) |

**Key insight:** every quantity this phase publishes already has one sanctioned producer in the
tree; Phase 27's value is the ORDER (gate before data) and the WIRING PROOF, not new arithmetic.

## Common Pitfalls

### Pitfall 1: The pin's caller census
**What goes wrong:** `phase27_prereg.py` imports `mitigation_point_verdict` for the tripwire.
**Why:** `tests/test_phase20_correction.py:1377` walks `scripts/` and `src/` for the import AND
the `.attr` call. **Avoid:** tripwire lives in `tests/`, through the route.

### Pitfall 2: `verdict.verdict` is `null` on six points
**What goes wrong:** a domain check `verdict in V4_VERDICTS` reads the frontier as corrupt → the
gate reads INCONCLUSIVE instead of MOOT. **Avoid:** accept `None` iff `early_return_reason` is a
non-empty string, count it as REFUSED, and assert the count equals `verdicts.tallies.REFUSED`.

### Pitfall 3: `teach_persona.py` is digest-pinned; `train_arm` has no config kwarg
**Warning sign:** any plan step that says "add `max_steps=` / `train_config=` / `on_draw=` to
`train_arm`". See OQ1/OQ3. The module's constants ARE read at call time (`tests/test_phase22_wiring.py:757-761`
monkeypatches `tp.MAX_STEPS`, `tp.BATCH_SIZE`, etc. and the run honours them).

### Pitfall 4: The `train_arm(` grep register
`tests/test_phase23_resume.py:60-130` + `:262-282`: 29 registered hits; every new `train_arm(`
substring in `scripts/` or `tests/` (including docstrings and comments) must be appended to
`_TRAIN_ARM_CALL_SITES` with `(path, "call"|"prose", symbol)`, per file, or the suite goes RED.

### Pitfall 5: `latest.pt` is one path
`loop.py:925-948` overwrites `checkpoint_path` every `checkpoint_interval`; rung adapters need
either a resume chain with `max_steps_override` (train() direct) or a copy hook. Also the cosine
schedule (`schedule.py:42`) is a function of `train_config.max_steps`: a 400-step config's step-200
rung is NOT the 200-step endpoint on disk. Disclose in the apparatus block (M9).

### Pitfall 6: `build_corpus` reads `factset.LOCKED_FACTS` via a lazy import
`phase18_extraction.py:822-870` reads `LOCKED_FACTS`, `CORPUS_SOURCE_FIXTURE` and the
value-injection budgets from the real fact set. The D-32 synthetic fixture must monkeypatch
`phase14_factset.LOCKED_FACTS` (and whatever `CORPUS_SOURCE_FIXTURE` maps) in the test, the way
`tests/test_phase21_replay_volume.py:119` builds fake `Fact`s. Verify `build_corpus` on 2 facts
yields `2 × (questions) × 4` entries before wiring the e2e.

### Pitfall 7: Global NumPy RNG is the sampler
`data.py:117` uses `np.random.randint`; `seed_everything` seeds it (`teach_persona.py:1861`) and
the checkpoint restores it (`checkpoint.py:139/186`). The offset-stream hash is therefore
deterministic per (seed, bin length, step count) — and it is also the tool that PROVES a
resume-chained rung ladder equals an uninterrupted run (same stream hash). Do not seed anything
else inside the driver between arms.

### Pitfall 8: Gitignored inputs
`checkpoints/` and `data/` are gitignored (`.gitignore:14,17`); the five fresh adapters, both
controls and the dialogue bins live only on the sweep host. CPU tests that need them must
`skipif` (`needs_adapters` idiom, `tests/test_phase26_canary.py`); the e2e test uses the tiny
fixture and `_e2e_env` (`tests/test_phase22_wiring.py:705`) which redirects `tp._REPO_ROOT`,
`CONVBASE_BEST`, `FACTSET_REPORT`, `DIALOG_*` and pins CPU.

### Pitfall 9: LoRA step-0 canary
`tests/test_phase22_wiring.py:749-756`: at ONE step `lora_A` gets zero gradient and `train_arm`'s
canary raises "trainable … did not move"; the e2e run needs ≥ 2 steps.

### Pitfall 10: Dirty tree at emit
`emit` publishes `git_sha` and hashes modules from the working tree; run `admit` only from a clean
tree (`refuse_if_dirty(pathspec=("scripts/","src/","results/"))`), and the operator commits the
record by hand afterwards (D-15).

## Code Examples

### 1. The gate (pure; lives in `phase27_prereg.py`)
```python
# Source: shape of erasure_gate.erasure_is_worth_attempting (:173) + phase26_prereg.verdict; frontier schema read 2026-09-14
VERDICTS = ("ADMITTED", "MOOT", "INCONCLUSIVE")
EXPECTED_POINTS = 44
REFUSED = "REFUSED"  # the tally name the frontier uses for verdict.verdict == None + early_return_reason

def point_verdict_string(point):
    v = point["verdict"]
    if v["verdict"] is None and v.get("early_return_reason"):
        return REFUSED
    return v["verdict"]

def relearning_is_worth_attempting(frontier):
    reasons = []
    if frontier is None:
        return "INCONCLUSIVE", ["frontier record absent"]
    keys = frontier.get("point_keys", [])
    if len(keys) != EXPECTED_POINTS or set(keys) != set(frontier["points"]):
        return "INCONCLUSIVE", [f"{len(keys)} point(s) present, {EXPECTED_POINTS} expected"]
    strings = {k: point_verdict_string(frontier["points"][k]) for k in keys}
    bad = {k: s for k, s in strings.items() if s not in (*mitigation_gate.V4_VERDICTS, REFUSED)}
    if bad:
        return "INCONCLUSIVE", [f"verdict outside the domain: {bad}"]
    tally = {name: sum(1 for s in strings.values() if s == name)
             for name in (*mitigation_gate.V4_VERDICTS, REFUSED)}
    if tally != frontier["verdicts"]["tallies"]:
        return "INCONCLUSIVE", [f"tally {tally} does not re-derive the record's {frontier['verdicts']['tallies']}"]
    passing = [k for k in keys if strings[k] == "PASS"]          # point_keys order (D-22)
    if passing:
        return "ADMITTED", [f"{len(passing)} PASS point(s): {passing}"]
    return "MOOT", [f"0 of {EXPECTED_POINTS} points PASS; tallies {tally}", *per_leg_reasons(frontier)]
```

### 2. The 44-verdict tripwire (tests only) — `tests/test_phase25_promotion.py:51-60` recipe
```python
# Source: tests/test_phase25_promotion.py:44-60 and :189-204, re-run this session: 38 equal, 6 SystemExit
_PIN = set(promotion.PIN_KWARGS)
def _route_kwargs(entry):
    kwargs = {k: entry[k] for k in _PIN if not k.startswith("sweep_")}
    curve = entry["whole_curve_inputs"]
    kwargs.update({k: curve[k] for k in curve if k.startswith("sweep_")})
    kwargs["retention_floor_provenance"] = {
        "regime": phase20_gate_coverage.ADAPTER_REGIME,
        "seeds": phase25_condition_c.RETENTION_FLOOR_DISCLOSURE["seeds"],
    }
    return kwargs

def test_every_frontier_verdict_re_derives_through_the_route(frontier):
    for key in frontier["point_keys"]:
        entry = frontier["points"][key]["verdict"]
        if entry["verdict"] is None:
            with pytest.raises(SystemExit) as exc:
                phase20_gate_coverage.corrected_point_verdict(**_route_kwargs(entry))
            assert entry["reasons"][0] == str(exc.value).strip()
            continue
        out = phase20_gate_coverage.corrected_point_verdict(**_route_kwargs(entry))
        assert (out[0], list(out[1]), out[2]) == (entry["verdict"], entry["reasons"], entry["arm"]), key
```

### 3. `cleared_a/b/c` (D-34) — condition functions on the 21 stored kwargs
```python
# Source: mitigation_gate.py:770-812 (the pin's own arithmetic), verified to give a=30 b=4 c=1
def cleared_abc(kw):
    ceiling = mitigation_gate.extraction_ceiling(
        nontarget_successes=kw["control_extraction_successes"],
        nontarget_questions=kw["control_extraction_questions"],
        extraction_noise_floor=kw["extraction_noise_floor"],
        extraction_floor_provenance=kw["extraction_floor_provenance"])
    a = erasure_gate.wilson_upper_bound(kw["point_extraction_successes"], kw["point_extraction_questions"]) <= ceiling
    b = (kw["point_taught_recall"] >= mitigation_gate.F_Y * kw["control_taught_recall"]
         and kw["point_heldout_recall"] >= mitigation_gate.F_Y * kw["control_heldout_recall"])
    lo, hi = mitigation_gate.dialogue_gap_band(control_gap=kw["control_gap"], gap_noise_floor=kw["gap_noise_floor"])
    gap = kw["point_dialogue_ppl_on"] - kw["point_dialogue_ppl_off"]
    c = lo <= gap <= hi and kw["point_retention_ppl"] <= mitigation_gate.retention_cap(
        retention_noise_floor=kw["retention_noise_floor"])
    return a, b, c   # REFUSED points: (None, None, None) — they never reached (a)
```

### 4. Shared config + rung chain via `train()` directly (OQ1/OQ2 option B; Phase 23's own shape)
```python
# Source: scripts/phase23_run.py:612-690 (train_never_taught), loop.py:235-262/:800, checkpoint.py:135-139
CFG = tp.TrainConfig(lr=tp.LR, warmup_steps=tp.WARMUP_STEPS, max_steps=RELEARN_CAP,   # 2 * tp.MAX_STEPS
                     batch_size=tp.BATCH_SIZE, weight_decay=tp.WEIGHT_DECAY, seed=seed)  # ONE instance
for rung in range(tp.CHECKPOINT_INTERVAL, RELEARN_CAP + 1, tp.CHECKPOINT_INTERVAL):
    tp.train(train_config=CFG, runtime_config=runtime, model=model, model_config=model_cfg,
             train_bin=paths["bin"], train_mask_bin=paths["mask"],
             val_bin=tp.DIALOG_VAL_BIN, val_mask_bin=tp.DIALOG_VAL_MASK,
             replay_bin=tp.DIALOG_TRAIN_BIN, replay_mask_bin=tp.DIALOG_TRAIN_MASK,
             replay_windows=tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE,          # D-20
             penalty_fn=None, log_path=paths["csv"], eval_interval=tp.EVAL_INTERVAL,
             checkpoint_path=paths["checkpoint"], checkpoint_interval=tp.CHECKPOINT_INTERVAL,
             resume_from=paths["checkpoint"] if rung > tp.CHECKPOINT_INTERVAL else None,
             max_steps_override=rung, return_final_loss=True, on_draw=recorder)          # on_draw: OQ3
    export_adapter(rung_path(arm, rung), adapter=lora_state_dict(model), lora_config=asdict(tp.LORA_CFG),
                   base_fingerprint=fingerprint)
# off-disk diff: load_checkpoint(...)["train_config"] == asdict(CFG) for every arm
```

### 5. Disjointness proof inputs (D-17)
```python
# Source: phase14_factset.py:825-833, phase14_recall.py:1026, phase24_adversarial.py:180-214, phase18_extraction.py:822
scored = {q for q in gated_questions(corpus)}                          # 416 core_held_out prompts (tier field)
scored |= {q for (_fam, _id, _split, q) in held_out_items(build_question_sets(facts))}   # F3/F7/F8
teaching = {q for q, _a in tp.render_episodes(facts, fs.TAUGHT_FAMILY_IDS)}               # mitigated arm's bin rows
trained_attack = {p for p in attack_prompts if p["family"] in phase24_adversarial.TRAINED_FAMILIES}
assert phase24_adversarial.HELD_OUT_FAMILY == "A2"   # read, never spelled elsewhere
assert not (scored & teaching) and not (scored & trained_attack) and not (scored & attacker_corpus_rows)
```

### 6. Tiny fixture + real tokenizer (D-31/D-32) — `tests/test_phase22_wiring.py:703-770`
`ModelConfig(block_size=tp.BLOCK_SIZE, n_layer=1, n_head=2, n_embd=16)` is the proven shape (D-31
asks for 2 layers: `n_layer=2` is fine; keep `block_size=tp.BLOCK_SIZE` so the packer and loader
agree). `_e2e_env(root, monkeypatch)` writes a convbase blob `{"model_config", "model", "git_sha",
"step", "val_loss"}`, decodable-id dialogue bins (`windows * BLOCK_SIZE + 1` elements), a GO
factset report, and pins `tp.RuntimeConfig` to CPU. Two steps minimum (Pitfall 9).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `mitigation_point_verdict` called directly | `phase20_gate_coverage.corrected_point_verdict` (24 kwargs, sentinel sweeps, coverage on Wilson) | Phase 20 correction (`20-11`) | the tripwire must use the route |
| `path.write_text` for records | `phase25_run.atomic_write_json` | Phase 25 | torn-write safe |
| `--dry-run` batteries | live-path wiring test through `main()` | Phase 26 (`test_the_live_path_is_wired_end_to_end`) | D-10 |
| verdict-only records | verdict + `reasons` + disclosure fields | Phase 26 D-05/D-13 | D-11 apparatus block |

**Deprecated/outdated:** `get_batch_memmap_masked` remains the production teaching/replay draw;
`get_batch_fact_aligned` (DP arms, `loop.py:604`) is the fact-aligned branch and is NOT touched by
D-29 (the attacker, fresh and control arms are non-DP `train_bin + train_mask_bin` paths).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | A resume chain `train(resume_from=latest, max_steps_override=r)` is bit-identical to one uninterrupted run under the same `TrainConfig` (RNG incl. NumPy restored, `checkpoint.py:186`; CLAUDE.md "resume bit-for-bit"). `[ASSUMED]` from those two sources; not measured for the replay path this session. | OQ2 / Code Ex. 4 | Rung adapters would not equal one-run rungs; the offset-stream hash (D-29/30) is exactly the test that settles it — make it a CPU test before relying on it. |
| A2 | `phase18_extraction.build_corpus` runs on 2 synthetic facts once `phase14_factset.LOCKED_FACTS` (and `CORPUS_SOURCE_FIXTURE` if it lists fact ids) is monkeypatched. `[ASSUMED]` — signature and lazy import read (`:822-870`), not executed on fake facts. | Pitfall 6 | The D-32 fixture might need its own gated-question list; verify in Wave 0. |
| A3 | Runtime of the tiny e2e run is seconds (Phase 22's 2-step e2e is in the suite today). `[ASSUMED]` from precedent. | Validation | Suite runtime grows; still well under the 1298 s full run. |

## Open Questions (decisions whose letter conflicts with live code — planner/operator rule)

1. **D-13/D-26(i) vs `train_arm` (M6).** `train_arm` builds its own `TrainConfig` from module
   constants and `teach_persona.py` cannot be edited (digest pin). Options: **(A)** keep `train_arm`;
   set `tp.MAX_STEPS = RELEARN_CAP` in the driver before the calls (module constants are read at
   call time — proven by `tests/test_phase22_wiring.py:757`), and satisfy D-26(i) by building ONE
   `TrainConfig` in the driver from the same symbols and asserting `asdict(shared) ==
   checkpoint["train_config"]` for every arm off disk (which is D-26(ii)'s diff anyway). **(B)**
   call `tp.train()` directly with the one shared instance, bins from `tp.build_arm_bins` (the
   teaching recipe's data path) — the exact shape `phase23_run.train_never_taught` used to produce
   D-12's fresh baseline, and the only one that gives `max_steps_override`, `on_draw` (OQ3) and
   literal "one instance". (B) satisfies D-26(i) literally and D-13's intent ("the project's own
   teaching recipe, same symbols"); (A) satisfies D-13's letter. Recommendation: (B), disclosed in
   the record as "train() called as `phase23_run.train_never_taught` does".
2. **D-25 rungs (M7/M9).** `latest.pt` is overwritten per interval; one adapter per run. Options:
   resume chain with `max_steps_override` (only via `train()` direct, A1) or a post-hoc copy hook
   (none exists). The on-disk fresh adapters are 200-step endpoints, not 400-step rungs; a fresh
   CURVE needs retraining (never this phase). Recommendation: resume chain + disclosure.
3. **D-29 reachability (M8).** `get_batch_memmap_masked` is called only inside `train()`'s closures
   (`loop.py:640`, `:672`). Options: add `on_draw=None` to `train()` too and thread it to both call
   sites (loop.py is not digest-pinned; golden-trajectory tests in `tests/test_lora_training.py`,
   `test_loop_penalty_fn.py`, `test_phase22_*` stay green when `None`); or rebind
   `loop_mod.get_batch_memmap_masked` from the driver (works — `tests/test_phase22_wiring.py:211`
   proves the loop binding is the effective one — but is production monkeypatching). Recommendation:
   the `train()` passthrough; D-29's "nothing changes when None" test covers both files.
4. **D-12 seeds source (M2).** Pin the five seeds from the record; assert `== phase23_run.SEED_LADDER`
   in a test only (torch at import).
5. **D-02 tripwire location (M3).** `tests/` through the route. The prereg gate counts strings only.
6. **D-33 rows for REFUSED points (M4).** `verdict: "REFUSED"`, `cleared_a/b/c: null`, plus
   `early_return_reason` copied? D-33 says never the reasons — recommend copying only the boolean
   `refused: true` and leaving the text in the frontier.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Python 3.11 venv `.venv` | everything | ✓ | 3.11.15 | — |
| torch (CPU/MPS) | e2e test, legs | ✓ | 2.7.1 | — |
| numpy | offset stream, mask count | ✓ | (in venv) | — |
| pytest | suite | ✓ | ~9 (`pyproject.toml`) | — |
| ruff | `make lint` | ✓ | line-length 100, `E,F,W,I` | — |
| git (non-shallow) | ancestry guard, `refuse_if_dirty` | ✓ | — | — |
| `artifacts/tokenizer.json` | D-31 real tokenizer | ✓ (tracked, sha `e82e8e83…` pinned by phase24 record) | — | — |
| `checkpoints/phase23_never_taught_seed*_adapter.pt` (5), `checkpoints/phase25_sigma0p000000_dp_n{8,64}_adapter.pt` | D-12 sha checks | gitignored; present on the sweep host only | — | `skipif` in tests; sha pins live in the record |
| `data/dialog_train*.bin`, `dialog_val*.bin` | replay/val on a real run | gitignored | — | fixture bins in tests (`_e2e_env`) |
| MPS | nothing this phase | — | — | not used (D-09) |

**Missing dependencies with no fallback:** none. **With fallback:** the gitignored adapters/bins (tests skip; the phase trains nothing for real).

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest ~= 9.0 (`pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]`) |
| Config file | `pyproject.toml`; `tests/conftest.py` |
| Quick run command | `.venv/bin/pytest -q tests/test_phase27_prereg.py tests/test_phase27_relearn.py -x` |
| Full suite command | `make test` (= `.venv/bin/pytest -q`) |
| Baseline | **2802 tests collected** at HEAD `ff38d9a` (`pytest --collect-only -q`, 3.43 s); last full run **2792 passed / 4 skipped / 0 failed in 1297.92 s** at `8652c15` (2796 collected, `26-05-SUMMARY.md:95`); +6 collected since. Plans state deltas against 2802 collected. |
| Lint | `make lint` = `ruff check . && ruff format --check .` |

### Phase Requirements → Test Map
| Req / Decision | Behavior | Test Type | Automated command / assertion | Natural RED state | File Exists? |
|---|---|---|---|---|---|
| RELRN-01 / D-01, D-03 | Gate returns MOOT on the committed frontier; ADMITTED on a forged PASS copy; INCONCLUSIVE on 43 points / tally mismatch / missing file | unit | `tests/test_phase27_prereg.py::test_the_gate_reads_moot_on_the_committed_frontier`, `::test_the_gate_admits_only_pass`, `::test_partial_or_inconsistent_frontier_is_inconclusive` (tmp copies) | gate returns MOOT on a 43-point copy; or ADMITTED on a copy with `verdict.verdict = "INCONCLUSIVE"` | ❌ Wave 0 |
| D-02 (tripwire) | All 38 reached verdicts+reasons re-derive through `corrected_point_verdict(**_route_kwargs)`; 6 `adv_n64` raise `SystemExit` with `reasons[0]` text | unit (CPU, frontier loaded once, module fixture) | `::test_every_frontier_verdict_re_derives_through_the_route` (Code Ex. 2) | edit one `point_taught_recall` in a tmp copy → mismatch | ❌ Wave 0 |
| D-02 (tally) | tally re-derives from 44 `verdict.verdict` strings with `None+early_return_reason → REFUSED` | unit | `::test_the_tally_re_derives_from_the_entries` | copy with `tallies.FAIL = 31` → INCONCLUSIVE | ❌ Wave 0 |
| D-04 | every tracked `results/phase27_*` first-add strictly descends from every `phase27_prereg.py` commit | git integration | `::test_phase27_prereg_is_frozen_before_every_phase27_result` (copy `_assert_frozen_before`, `tests/test_phase26_prereg.py:52-88`) | honest-with-zero until the record is committed (`bool(checked) == bool(tracked)`) | ❌ Wave 0 |
| D-04 (X by reference) | `phase27_prereg.X` is computed by calling `mitigation_gate.extraction_ceiling` on the frontier's control kwargs and `== frontier.verdicts.extraction_ceiling.X` | unit | `::test_x_is_the_frontier_ceiling_by_call_not_literal` + AST: no float literal `0.0064…` in the module | a retyped literal | ❌ Wave 0 |
| D-06 | `record.frontier_sha256 == sha256(FRONTIER_RECORD)`; frontier at one commit; both-state idiom | integration | `::test_the_record_is_pinned_to_the_frontier_both_ways` (mirror `tests/test_phase26_canary.py:786-811`) | absent record ⇒ assert untracked | ❌ Wave 0 |
| D-07 / D-33 / D-34 | record carries tallies, tallies_by_leg, cleared (a)=30/(b)=4/(c)=1, 44 rows; each row re-derives via Code Ex. 3 | unit | `::test_cleared_abc_re_derive_on_every_row`, `::test_moot_reasons_are_generated_from_counts` | flip one `cleared_a` in a tmp copy | ❌ Wave 0 |
| D-08 / D-37 | each sub-mode (`calibrate`, `curve`, `gate`, `structural-proof`) exits non-zero naming the verdict when the record reads MOOT or INCONCLUSIVE or is untracked; watched on the REAL committed record at close | unit (subprocess `main([...])` in tmp) + manual | `tests/test_phase27_relearn.py::test_each_leg_refuses_unless_admitted[calibrate|curve|gate|structural-proof]`; close-out: run each once against `results/phase27_admission.json`, capture stderr in the summary | forged ADMITTED copy ⇒ leg proceeds (that is the e2e) | ❌ Wave 0 |
| D-08 (write-once) | `admit` refuses when the record exists / tree dirty | unit | `::test_admit_refuses_to_overwrite`, `::test_admit_refuses_a_dirty_tree` (`tests/test_phase26_canary.py:361-399` shape) | — | ❌ Wave 0 |
| D-09 (`baseline=` required) | `gate(...)` has `baseline` as KEYWORD_ONLY with `Parameter.empty` default; accepts only pinned keys | unit | `::test_gate_baseline_is_required_and_pinned` via `inspect.signature` (`tests/test_phase23_resume.py:357` shape) | a default sneaks in | ❌ Wave 0 |
| D-10 (e2e) | forged ADMITTED record in tmp; tiny GPT + real tokenizer; 2 synthetic facts; ≥ 2 steps through the real train path with the shared config; real scorer; calibrate → curve → gate verdict; record fields all present | integration (CPU, seconds) | `::test_the_live_path_is_wired_end_to_end` (mirror `tests/test_phase26_canary.py:552` + `_e2e_env` `tests/test_phase22_wiring.py:705`) | unwired leg raises at first real call | ❌ Wave 0 |
| D-10 (kwargs trace) | every kwarg `main()` passes to each `run_<leg>()` exists in that function's signature; every required kwarg is supplied (AST of the driver + `inspect.signature`) | unit | `::test_main_passes_only_kwargs_the_legs_accept` | rename one kwarg | ❌ Wave 0 |
| D-11 / D-36 | `apparatus` block lists 4 legs × {name, sub_mode, refusal_node_id, e2e_node_id}; every node id is in `pytest --collect-only -q` | unit (subprocess) | `::test_every_apparatus_node_id_exists` | a renamed test | ❌ Wave 0 |
| D-12 | 5 fresh + 2 control entries with path/sha256/seed equal to the source records; seeds `== phase23_run.SEED_LADDER`; on-host adapters hash to the pins (`needs_adapters`) | unit / integration | `::test_baselines_are_pinned_from_the_records`, `::test_pinned_seeds_equal_seed_ladder`, `::test_pinned_adapters_hash_on_host` | — | ❌ Wave 0 |
| D-17 / RELRN-05 | zero string intersection: scored prompts vs teaching rows vs A1-mild/A1-aggressive/A3 vs attacker corpus; `HELD_OUT_FAMILY` read | unit (CPU, synthetic facts) | `::test_recovery_fixture_is_disjoint` (Code Ex. 5); record field `disjointness = {overlaps: 0, checked: N}` | plant one teaching row into the scored set | ❌ Wave 0 |
| D-18 | attacker corpus = `render_episodes(LOCKED_FACTS, TAUGHT_FAMILY_IDS)` rows; pinned sha256 of the rendered bin equals a fresh render (on-host; fixture-render in CI) | unit | `::test_attacker_corpus_sha_re_renders` | — | ❌ Wave 0 |
| D-19 / RELRN-03 | band = `MARGIN_K * noise_floor(fresh readings)`; verdict signature has no band/curve parameter | unit | `::test_band_uses_imported_margin_and_noise_floor`, `::test_the_curve_cannot_reach_the_verdict` | — | ❌ Wave 0 |
| D-21 | rung K == `mitigation_budget.CURVE_K`; Z reading promoted via `promote_to_full_fidelity(curve_k=16, full_k=48)` | unit | `::test_k_is_curve_k_and_promotion_is_the_gates` | — | ❌ Wave 0 |
| D-23 / D-25 / D-28 | rungs `range(50, 401, 50)`; scored-token count `int(mask.sum()) * steps`; Z = max(first clears); either arm never clears ⇒ leg INCONCLUSIVE | unit (table) | `::test_z_rule_table` (parametrized) | — | ❌ Wave 0 |
| D-26 (ii) | off-disk: `load_checkpoint(...)["train_config"]` equal across arms except nothing; records differ only in `arm`/data path | unit (e2e artifacts) | `::test_off_disk_config_diff_is_empty` | perturb one arm's `max_steps` | ❌ Wave 0 |
| D-29 / D-30 / D-26 (iii) | `on_draw=None` draws identical `ix` to the pre-edit path (seeded, compare arrays); recorder captures teaching AND replay draws in call order; equal seed+bin ⇒ equal sha256, different seed ⇒ different | unit | `tests/test_phase27_relearn.py::test_on_draw_none_is_byte_neutral`, `::test_offset_stream_hash_covers_every_draw`, `::test_offset_stream_differs_by_seed` | — | ❌ Wave 0 |
| D-35 | recompute every `provenance.module_sha256` from bytes; collect ALL drifted | unit | `::test_provenance_digests_match_live_bytes` (`tests/test_phase24_record.py:289-332`) | edit one byte of a tmp copy (`tests/test_phase25_calibrate.py:571`) | ❌ Wave 0 |
| D-39 | `pyproject.toml` sha256 unchanged vs HEAD~ (or vs the value recorded in 26-05) | unit | `::test_pyproject_is_byte_identical` | — | ❌ Wave 0 |
| Pitfall 4 | `_TRAIN_ARM_CALL_SITES` updated for every new `train_arm(` hit | existing | `tests/test_phase23_resume.py::test_resume_from_none_is_inert` | RED until the register is edited | ✅ exists |
| Pitfall 1 | no `mitigation_point_verdict` caller in `scripts/` | existing | `tests/test_phase20_correction.py::test_mitigation_point_verdict_has_no_caller_outside_this_module` | — | ✅ exists |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest -q tests/test_phase27_prereg.py tests/test_phase27_relearn.py -x`
- **Per wave merge:** `make test` (expect 2802 + this phase's new tests collected; 0 failed)
- **Phase gate:** full suite green + `tests/test_phase25_close.py`, `tests/test_phase24_record.py`, `tests/test_phase20_correction.py`, `tests/test_phase23_resume.py` explicitly re-run before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase27_prereg.py` — D-01..D-07, D-12, D-19, D-21, D-23..D-28 (pure + git)
- [ ] `tests/test_phase27_relearn.py` — D-08..D-11, D-17, D-18, D-26, D-29, D-30, D-35, D-36, D-39
- [ ] `tests/test_phase23_resume.py::_TRAIN_ARM_CALL_SITES` — append the new hits (or none, under OQ1-B)
- Framework install: none.

## Security Domain

`security_enforcement` is not set in `.planning/config.json` (treated as enabled). Offline, local,
CPU-only; no network, no user input, no secrets.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2/V3/V4 Auth, session, access | no | — |
| V5 Input Validation | yes (paths, keys) | point keys from `phase25_record.ORDERED_POINT_KEYS()` only; per-arm stream paths under `data/` with the charset refusal `phase25_prereg.point_record_path` uses; record read via `json.loads` on a tracked path |
| V6 Cryptography (integrity only) | yes | `hashlib.sha256` for frontier, adapters, modules, rendered corpus, offset stream |
| V8 Data Protection | yes | driver writes only under `results/phase27_admission.json` and `data/phase27_*`; never touches git (D-15); `refuse_if_dirty` before any digest is published |
| V14 Configuration | yes | `pyproject.toml` byte-identical (D-39); no plist (D-14) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Post-hoc favourable reading (gate shaped after data) | Tampering | ancestry guard at ONE commit before any `results/phase27_*` (D-04); constants imported by identity |
| "Could not tell" published as "nothing survived" | Repudiation | three-valued domain, INCONCLUSIVE precedence (D-03) |
| Re-emitted frontier | Tampering | sha256 both ways + one-commit assertion (D-06) |
| Unwired live path behind green dry-runs | Denial (of evidence) | e2e + kwargs trace (D-10); refusals watched on the real record (D-37) |
| Baseline chosen after seeing data | Tampering | `baseline=` required, pinned entries only (D-09/D-12) |
| Pickle load of adapters | Tampering | `phase14_recall.load_adapted_model` (`weights_only=True` path, `teach_persona.py:2443-2445`); never `torch.load` directly in the driver (AST guard `tests/test_phase26_canary.py:270`) |
| Dirty-tree provenance | Repudiation | `refuse_if_dirty` at `admit` |

## Sources

### Primary (HIGH confidence — read from source this session at HEAD `ff38d9a`)
- `scripts/mitigation_gate.py` (:85, :149, :156, :203, :217, :254, :341, :352, :449, :526, :595, :637-812, :917, :963), sha256 `86db4798…`
- `scripts/erasure_gate.py` (:86, :90, :136, :139, :173-199)
- `scripts/mitigation_budget.py` (:277, :425, :473, :508, :544)
- `scripts/phase20_gate_coverage.py` (:124, :364, :519, :522-720)
- `scripts/phase23_prereg.py` (:143-194, :346), `scripts/phase23_run.py` (:105, :131, :146, :342, :612-690)
- `scripts/phase18_extraction.py` (:93, :98, :146, :173, :175, :746, :758, :822-870)
- `scripts/phase24_adversarial.py` (:180, :191, :214)
- `scripts/phase14_factset.py` (:51, :390, :656, :825-880), `scripts/phase14_recall.py` (:315, :712, :901, :1026-1060)
- `scripts/teach_persona.py` (:104-134, :179-182, :294, :310, :344-451, :495, :1279, :1565-1585, :1655-1668, :1940-2122, :2440), sha256 `3c1e6c55…` == `results/phase24_token_budget.json::provenance.module_sha256`
- `scripts/phase25_run.py` (:118-175, :177, :407-438, :458, :586, :633), `scripts/phase25_recall.py` (:56-60, :114), `scripts/phase25_record.py` (:107, :253, :456), `scripts/phase25_promotion.py` (:191-260), `scripts/phase26_prereg.py` (whole), `scripts/phase26_canary.py` (:46-134, :475-500, :682-716, :793-812), `scripts/_prose.py` (:35)
- `src/personacore/training/data.py` (:93-125), `src/personacore/training/loop.py` (:65-74, :235-262, :560-700, :800, :900-975), `src/personacore/training/schedule.py` (:42), `src/personacore/config.py` (:48, :77, :98), `src/personacore/checkpoint.py` (:88, :135-139, :184-186, :253), `src/personacore/provenance.py` (:28, :47), `src/personacore/lora/inject.py`
- `tests/test_phase26_prereg.py` (:1-98), `tests/test_phase26_canary.py` (:211-924), `tests/test_phase25_promotion.py` (:1-66, :189-204), `tests/test_phase24_record.py` (:289-332), `tests/test_phase25_calibrate.py` (:571-593), `tests/test_phase20_correction.py` (:1377-1417), `tests/test_phase22_wiring.py` (:55-130, :703-770, :799-880), `tests/test_phase23_resume.py` (:60-130, :200-282, :357), `tests/test_lora_toggle.py` (:40-43), `tests/test_fisher.py` (:58-61), `tests/conftest.py` (:40-100), `tests/test_phase25_close.py` (:318-324)
- `results/phase25_frontier.json` (sha256 `1f182b40…`, one commit `4030d0e`), `results/phase23_never_taught_training.json`, `results/phase23_never_taught.json`, `results/phase23_matched_control.json`, `results/phase25_point_dp_n8_sigma0p000000.json`, `results/phase25_point_dp_n64_sigma0p000000.json`, `results/phase24_token_budget.json`, `results/phase26_canary.json` (commit `8652c15`)
- `.planning/phases/27-relearning-attack/27-CONTEXT.md`, `27-DISCUSSION-LOG.md`; `.planning/REQUIREMENTS.md:418-435, 570-578`; `.planning/ROADMAP.md:1017-1052, 1077-1086`; `.planning/PROJECT.md:200-220`; `.planning/phases/26-empirical-privacy-audit-canary/26-RESEARCH.md`, `26-PATTERNS.md`, `26-VALIDATION.md`, `26-05-SUMMARY.md:56-100`
- Computed this session: 44-point re-derivation (route: 38 equal + 6 refused; pin: 6 mismatches), (a)/(b)/(c) = 30/4/1, `pytest --collect-only -q` = 2802, module sha256s, venv/torch versions

### Secondary / Tertiary
- None. No web sources were needed; every claim is from the repository.

## Metadata

**Confidence breakdown:**
- Standard stack (signatures, constants, paths, digests): HIGH — read from source / computed.
- Frontier schema and re-derivation: HIGH — executed.
- Architecture (patterns): HIGH — direct precedents in Phases 23/25/26.
- Train-path conflicts (OQ1–3): HIGH that the conflict exists (file:line given); MEDIUM on which option the operator prefers.
- Pitfalls: HIGH — each is an existing guard test named by path.

**Research date:** 2026-09-14
**Valid until:** any commit touching `scripts/teach_persona.py`, `scripts/phase20_gate_coverage.py`, `src/personacore/training/{data,loop}.py`, or `results/phase25_frontier.json` (the latter must never happen); otherwise 30 days.
