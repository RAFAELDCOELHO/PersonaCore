# Phase 27: Relearning Attack - Context

**Gathered:** 2026-09-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 27 delivers (1) an **admission gate** `relearning_is_worth_attempting(points)` called ONCE on
the measured Phase 25 frontier numbers, (2) the **relearning apparatus** — a binary recovery-ceiling
gate (recovered extraction ≤ X within a fixed budget Z), a cost-to-recovery curve against the
never-taught fresh adapter, and the structural identical-budget proofs — as committed, CPU-tested
code, and (3) one committed record `results/phase27_admission.json` carrying the gate's verdict.

**The measured fact that shapes the phase:** `results/phase25_frontier.json` tallies
**PASS 0 / FAIL 32 / INCONCLUSIVE 6 / REFUSED 6** over 44 points. Every DP point cleared condition
(a) at 0/416 but scored taught recall 0/1008 and failed retention; the adversarial arm is
INCONCLUSIVE and recipe-confounded (Phase 28 SC4). Under the gate as decided below, **the phase is
expected to read MOOT** — "nothing survived the mitigation, so there is nothing to relearn" — and the
milestone ships that finding. The apparatus is built and guarded so that a future ADMITTED reading
can be attacked without re-deciding anything after seeing data; it is **never run on MPS in this
phase**.

Out of scope: attacking points that did not PASS (a diagnostic on DP adapters that never learned
the facts is a v5.0 idea, see Deferred), a LaunchAgent for an unattended run, any new attacker
recipe, any new outcome threshold.

</domain>

<decisions>
## Implementation Decisions

**Thirty-nine decisions across eight areas. Every one is LOCKED** — the researcher and planner act on
them rather than re-open them.

### Area 1 — The admission gate (RELRN-01, SC1)

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
  cleared each of (a)/(b)/(c)** — e.g. "32 DP points cleared (a) at 0/416 and failed (b) at 0/1008"
  — so Phase 28 generates WHY nothing survived from the record rather than authoring it.

- **D-08: Every attack leg refuses unless the committed record reads ADMITTED.** One CLI sub-mode
  writes the admission record once (`refuse_if_exists`); the calibrate / curve / gate /
  structural-proof legs each READ that record and refuse on MOOT or INCONCLUSIVE — gated on the
  committed record, never on a live re-read (Phase 23's two-conjunct pattern). Each refusal is watched
  RED in a CPU test.

### Area 2 — What a MOOT phase ships (SC2–SC5 as guarded code)

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

### Area 3 — Recovery quantity, fixture, and attacker corpus (RELRN-01/02/05)

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

### Area 4 — Budget unit and the Z rule (RELRN-01/02/04)

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

### Area 5 — Offset-stream capture (RELRN-04)

- **D-29: An optional `on_draw=None` keyword is added to `get_batch_memmap_masked` in
  `src/personacore/training/data.py`.** When `None` nothing changes — a test proves the default path
  draws identical `ix` — so every prior phase's byte-identity is untouched. The Phase 27 driver passes
  a recorder that appends each `ix` array; sha256 over the concatenated stream is the proof.

- **D-30: The hashed stream covers EVERY draw the loop makes — teaching AND replay windows — in call
  order**, each `ix` appended as raw uint64 bytes with the bin path it came from; one stream per arm.
  A differing sha256 names the exact divergence by offset.

### Area 6 — The synthetic CPU fixture (D-10's substrate)

- **D-31: The end-to-end wiring test trains and scores a TINY random-init GPT (2 layers, small
  embd) with the REAL frozen tokenizer** — seconds per run, the `tests/test_lora_toggle.py` /
  `tests/test_fisher.py` shape. Numbers are meaningless by design; the test asserts structure.

- **D-32: Fixture facts, attacker corpus and scored questions are 2 SYNTHETIC facts rendered through
  the real `render_family` + Phase-18 fixture paths**, so the disjointness proof and the mask-bin
  token count run on the production code path. The forged ADMITTED record names one fake point whose
  adapter is the tiny model's own saved bytes. No real `LOCKED_FACTS` in `tests/`.

### Area 7 — The admission record schema

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

### Area 8 — Close-out verification

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and requirements
- `.planning/ROADMAP.md` — Phase 27 block (goal, dependencies, SC1–SC5) and Phase 28 SC4 (the
  adversarial arm's recipe confound, which Phase 27 must not re-litigate)
- `.planning/REQUIREMENTS.md` — RELRN-01..05 rows and the traceability table (rows 574–578)
- `.planning/PROJECT.md` — "Current Milestone: v4.0" § *Relearning attack, two instruments* and the
  *Pre-registration boundary* paragraph (resource budget vs outcome threshold)

### Gate precedents and frozen constants
- `scripts/erasure_gate.py` — `erasure_is_worth_attempting` (the shape SC1 names), `wilson_upper_bound`,
  `MARGIN_K = 2`; ancestry-guarded by v3.0 artifacts — DO NOT EDIT
- `scripts/mitigation_gate.py` — `extraction_ceiling` (X), `F_Y = 0.7`, `dialogue_gap_band`,
  `retention_cap`, `mitigation_point_verdict`, `promote_to_full_fidelity`, `V4_VERDICTS`,
  `NEVER_TAUGHT_ARM`
- `scripts/mitigation_budget.py` — `CURVE_K = 16` and its provenance
- `scripts/phase18_extraction.py` — `K = 48`, `GATED_TIER` (`core_held_out`), attack families,
  `CLUSTER_DENOMINATOR_RATIONALE`, the 270-question fixture
- `scripts/phase24_adversarial.py` — `HELD_OUT_FAMILY = "A2"` (line 214) and the trained families
- `scripts/phase23_prereg.py` — `noise_floor` reduction, the ancestry-guard pattern
- `scripts/phase26_prereg.py` — three-valued verdict domain + ancestry guard precedent (the most
  recent instance of the pattern D-03/D-04 copy)
- `scripts/phase20_gate_coverage.py` — `corrected_point_verdict`, `wilson_lower_bound`

### Measured inputs the gate consumes
- `results/phase25_frontier.json` — the 44 points (`points[point_key].verdict` with `verdict`,
  `reasons` and the 21 pin kwargs), `verdicts.tallies`, `point_keys`, `held_out_generalization`,
  `never_taught_floor`; ONE commit (`4030d0e`) — never re-emitted
- `results/phase25_promotion.json` — source of the tallies (sha256 recorded in the frontier)
- `results/phase25_operational_note.md` §12.5c — the adversarial confound cause, quoted never re-derived
- `results/phase23_never_taught_training.json` + `results/phase23_never_taught.json` — the 5 fresh
  adapters (paths, sha256, seeds) and their extraction readings
- `results/phase25_point_dp_n8_sigma0p000000.json`, `results/phase25_point_dp_n64_sigma0p000000.json`
  — the retrained unmitigated controls at both capacities
- `results/phase23_matched_control.json` — the matched control's 0.7837 recall and its noise floor

### Training path and structural-proof substrate
- `scripts/teach_persona.py` — `train_arm` (line 1655), `LR` / `BATCH_SIZE = 8` / `MAX_STEPS = 200` /
  `WARMUP_STEPS = 20` / `EVAL_INTERVAL = 10` / `CHECKPOINT_INTERVAL = 50` (lines 1570–1585),
  `REPLAY_*` constants, `refuse_if_exists`, `arm_outputs`
- `scripts/phase23_run.py` — `train_never_taught` (line 612): the import-not-retype budget rule
- `src/personacore/config.py` — `TrainConfig` (line 98)
- `src/personacore/training/data.py` — `get_batch_memmap_masked` (line 93; the offset draw at 117)
- `scripts/phase25_run.py` — `atomic_write_json`, `refuse_if_exists`, `device` helpers (called, never
  re-implemented)
- `scripts/phase25_recall.py` — the recall instrument, `TAUGHT_FAMILY_IDS` / `HELDOUT_FAMILY_IDS`

### Record and provenance precedents
- `results/phase24_token_budget.json` + `tests/test_phase24_record.py` — provenance block shape and the
  24-09 bytes-recompute guard; the scored-token-count-from-mask-bin rule
- `results/phase26_canary.json` — `frontier_sha256` / `adapter_sha256` both-ways pin, `reachable_claims`
  and the D-13 "could not have failed" disclosure shape
- `scripts/_prose.py` — `normalized` (Phase 28 routes every doc-consistency check through it)

### Prior phase context (decisions carried forward)
- `.planning/phases/26-empirical-privacy-audit-canary/26-CONTEXT.md` — D-01 (never a subset after
  seeing data), D-05 (three-valued domain), D-10 (fact decides, question reported), D-13, D-16/D-17
- `.planning/phases/25-frontier-sweep-and-the-existence-gate-verdict/25-CONTEXT.md` — D-01..D-08
  (control re-run, `prove_reproduction`, one designated seed, `SEED_LADDER`)
- `.planning/phases/23-cost-calibration-the-0-diagnostic-and-budget-pre-registratio/23-CONTEXT.md`
  — never-taught arm definition (trained at identical budget, not random init)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `erasure_gate.erasure_is_worth_attempting` / `wilson_upper_bound` / `MARGIN_K`: the gate shape and
  the bound; import, never copy.
- `mitigation_gate.mitigation_point_verdict` and its three condition functions: the D-02 tripwire and
  the D-34 breakdown call them directly on the frontier's stored pin kwargs.
- `mitigation_gate.promote_to_full_fidelity` + `ratchet_k`: the K=16 → K=48 promotion at Z.
- `teach_persona.train_arm`: the attacker's training path (D-13); `refuse_if_exists`, `arm_outputs`.
- `phase23_run.train_never_taught`: the fresh-arm recipe whose 5 outputs are D-12's pinned baseline.
- `phase23_prereg.noise_floor`: the seed-spread reducer for D-19's band.
- `phase25_run.atomic_write_json`: the single-write pattern for the admission record.
- `phase26_prereg`'s ancestry guard test and three-valued `VERDICTS`: copy the mechanism for D-03/D-04.
- Phase 24's provenance emitter + `test_phase24_record.py` bytes-recompute guard: D-35.
- `tests/test_lora_toggle.py` / `tests/test_fisher.py`: tiny random-init GPT fixtures for D-31.
- `tests/test_phase23_resume.py`, `tests/test_phase22_wiring.py`: precedents for CPU tests that call
  `train_arm` end to end.

### Established Patterns
- **Counts never rates; the question is the unit, never the draw.** Every recorded quantity carries its
  numerator, denominator and source.
- **Pre-registration = one commit + ancestry guard + refusal watched RED before trust.** The gate and
  every constant it reads are frozen before any `results/phase27_*` exists.
- **Instrument qualifies a gate's reading, never replaces it** (RELRN-03): the cost curve is a finding
  block, not a verdict input.
- **One designated seed for the pooled reading; seed spread enters only as a noise floor.**
- **Records are generated, never authored; Phase 28 quotes them by sha256.**
- **The sampler draws from the global NumPy RNG** (`np.random.randint` in `data.py:117`) — D-29's
  callback is the only byte-neutral capture point.
- **Zero new runtime dependencies** (RPT-03 counts a fourth consecutive milestone).

### Integration Points
- `scripts/phase27_prereg.py` (new) — frozen gate/constants/baselines/corpus; imports from
  `mitigation_gate`, `erasure_gate`, `mitigation_budget`, `phase18_extraction`, `phase24_adversarial`.
- `scripts/phase27_relearn.py` (new) — CLI driver; sub-modes `admit` / `calibrate` / `curve` / `gate`;
  calls `teach_persona.train_arm` with the shared `TrainConfig` and the `on_draw` recorder.
- `src/personacore/training/data.py` — `on_draw=None` kwarg on `get_batch_memmap_masked` (D-29).
- `results/phase27_admission.json` (new, operator-committed) — the phase's only artifact.
- `data/phase27_*` (gitignored) — per-arm offset streams and any sidecars.
- `tests/test_phase27_prereg.py`, `tests/test_phase27_relearn.py` (new) — ancestry guard, verdict
  domain, frontier both-ways pin, 44-verdict tripwire, refusal-RED per leg, end-to-end tiny run,
  kwargs trace, disjointness proof, default-`on_draw` byte-identity, provenance recompute, node-id
  existence.
- `.planning/REQUIREMENTS.md` rows RELRN-01..05 and `.planning/ROADMAP.md` — hand-edited at close (D-38).

</code_context>

<specifics>
## Specific Ideas

- "Exactly the shape in which `erasure_is_worth_attempting(92, 104, 0, 104)` authored Phase 19" — the
  gate call is ONE invocation on measured numbers, and its MOOT branch is a first-class published
  finding, not a skipped phase.
- The MOOT reasons should let Phase 28 say, from the record alone: "the DP arm erased the facts along
  with the leakage (0/416 extraction, 0/1008 recall on all 32 points), so there was nothing left to
  relearn; the adversarial arm was recipe-confounded and INCONCLUSIVE."
- The apparatus must be attackable in v5.0 without any decision being re-opened: baselines, corpus,
  X, Z rule, band, K, rung ladder and cap are all in the frozen module.
- Phase 25's unwired-driver incident is the explicit reason for D-10's two-test shape and D-37's live
  refusal watch.

</specifics>

<deferred>
## Deferred Ideas

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

</deferred>

---

*Phase: 27-relearning-attack*
*Context gathered: 2026-09-14*
