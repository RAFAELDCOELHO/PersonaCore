# Phase 14: Teach-Then-Recall Demo - Context

**Gathered:** 2026-08-01
**Status:** Ready for planning

<domain>
## Phase Boundary

A LoRA adapter trained on a hand-authored teaching set of user facts, on top of the FROZEN
conversational base (`checkpoints/convbase_best.pt`), which recalls those facts in a clean room —
fresh process, empty prompt, no store — scored by a pre-registered recall gate that reports taught
and never-seen phrasings separately, with a live memory on/off toggle in Gradio (DEMO-05/06/07).

Not in this phase: weight-delta/Fisher heatmaps and the v2.0 writeup (Phase 15); a second persona
adapter (DEMO-F1, future milestone); a prompt-stuffed-vs-adapter comparative baseline (DEMO-F2,
future milestone); any retraining of the conversational base or the tokenizer.

</domain>

<decisions>
## Implementation Decisions

### Fact-set selection (the validity foundation)

- **D-01:** Fact values are **adversarially chosen so the base-without-adapter control FAILS to
  guess them.** TinyStories-common values (`Max`, `Lily`, `blue`) are structurally unsafe
  regardless of token-count convenience — the base carries real prior probability mass on exactly
  those tokens, so a "successful recall" could be coincidence rather than memory. Distinctive or
  invented names and uncommon number combinations are correct **even if they fragment into more
  tokens**. The hierarchy, which governs every downstream tradeoff in this phase: *tokenizer cost
  is a nuisance to note; guessability is a validity failure of the whole demo.*

- **D-02:** Every candidate fact passes **two pre-flight filters** before the set is locked:
  - **(a) Tokenizer census** — token count and byte-fallback round-trip verified by direct
    `encode`/`decode`, never assumed (PITFALLS-12).
  - **(b) Base-model guessability pre-check** — prompt the **un-adapted** `convbase_best.pt` with
    the candidate's recall questions **before teaching anything**, and reject any fact it answers
    correctly or nearly correctly. This is the direct analog of Phase 11's `self_revised`
    anti-leakage check, applied to a different failure mode: prior-knowledge leakage instead of
    training-corpus lexical leakage.

- **D-03:** The rejection rule for (b) is **mechanical exact-match floor + recorded close call.**
  The mechanical half is pre-registerable and objective: `0/N base completions contained the
  value`. The close-call tier exists for the failure mode exact-match *structurally cannot see* —
  semantic proximity (same category, adjacent plausible value, right slot) that would make a
  reader suspect the base half-knew the answer. **Every close-call rejection must quote the
  specific base completion text that triggered it**, in the committed report register — a
  documented judgment, never a silent one. (Same asymmetric-risk logic that put λ=0.01 ahead of
  λ=0 for Phase 12 production: a slightly less mechanically pure gate that catches the failure
  mode actually threatening credibility beats a cleaner gate blind to it.)

- **D-04:** **Token count is a CENSUS FIELD, not a reject criterion.** The band (measured below:
  3–5 tokens for short invented names, 6–7 for compound/foreign-origin values) is recorded per
  fact, but exceeding it does **not** disqualify a candidate — only the exact-match + close-call
  guessability verdict can reject one. The single case where token count becomes a real constraint
  is an explicit check against the **demo's generation budget** (max new tokens per recall
  response). That is an engineering constraint belonging to the demo-surface design, must be named
  as such there, and is **never** a proxy for guessability.

- **D-05:** **Composition — proper-noun core + labelled soft tier.** 5–8 facts drawn from
  high-cardinality proper-noun/identifier slots (invented person/pet/place names, number combos)
  form the scored, gated set. 2–3 low-cardinality facts (favorite color/food) are additionally
  taught but reported in a **separately labelled tier excluded from the pre-registered gate**.
  That exclusion gets a **named report section** with the same explicitness as Phase 12's
  "post-verdict, discretionary" framing — not a footnote — stating what the soft tier is *for*
  (narrative texture, breadth of personalization) and what it explicitly does **not** contribute
  (no bearing on DEMO-06's taught/held-out thresholds, precisely because low-cardinality slots
  could not reliably survive the close-call filter).
  *Rationale surfaced during discussion:* the close-call rule systematically punishes
  low-cardinality slots — for "favorite color" the base has real prior mass on *some* color, so a
  base completion saying "blue" against a taught "chartreuse" is textbook same-category/right-slot
  and dies to D-03. Proper-noun slots have no such prior to trip over.

### Pre-flight gate shape

- **D-06:** **Standalone gated plan (Phase-11 `11-03` precedent) + permanent CPU regression test.**
  A committed script produces `results/phase14_factset_report.md` (candidate pool, per-fact
  tokenizer census, per-fact base completions, exact-match verdicts, quoted close-call rejections,
  survivor count vs the 5–10 target) behind a **BLOCKING user verdict**. Nothing downstream — no
  teaching set, no template grammar — is authored until the fact set is locked by that verdict.
  This directly implements the requirement that a shrunken viable set is information brought back
  *before* locking, not discovered mid-phase.

- **D-07:** The locked fact set additionally lands as a committed constant re-validated **forever**
  by a CPU-only pytest, on the **tokenizer half only** (token-count census, byte-fallback
  round-trip exactness). The test's docstring **MUST state explicitly why** the guessability half
  is not permanent: that measurement is **checkpoint-specific** — tied to `convbase_best.pt`'s
  actual learned priors at this point in training — and has no meaning as a standing invariant.
  Re-running it against a future checkpoint requires a **fresh gated measurement, not a test
  re-run**. Without this note a future reader would assume the permanent test covers the full
  pre-flight discipline when it structurally cannot. (Constraint driving the split: the
  guessability check needs the 278 MB `convbase_best.pt` on MPS and cannot run in the CPU-only,
  GPU-free suite.)

- **D-08:** **Gate probes are reserved as held-out phrasings.** The gate script carries a small
  hand-written probe set (~3–5 direct questions per candidate). Those probes are **permanently
  banned from the teaching set** and become seed members of DEMO-06's never-seen split. Each
  reserved probe carries its base-failure provenance explicitly into the DEMO-06 report — not just
  "this phrasing is held out" but **"held out AND measured base-failing at gate time, commit
  `<SHA>`, with the specific base completion quoted."** That is the payoff over a throwaway probe
  set: the held-out split is *proven* unguessable by the base, not merely assumed to be. SC2's
  scoring-time base-without-adapter control **still re-runs on the full final question set** as
  independent confirmation — gate-time probes are evidence carried forward, never a substitute for
  re-measuring at scoring time.

### Thresholds, scoring & controls

- **D-09:** **Pre-register the procedure, not a blind number (Phase-12 precedent).** A calibration
  protocol is committed first — a **throwaway fact set, disjoint from the real one** — it runs, and
  only then is the threshold locked and the real teaching set run against it. Two hard conditions:
  1. The calibration fact set **must pass the same pre-flight gate** (D-02/D-03 tokenizer census +
     exact-match/close-call guessability). It is disposable as an *evidence source* but **not
     exempt from the validity discipline** — a calibration set with guessable facts produces an
     inflated, meaningless ceiling.
  2. The **decision rule for deriving the threshold from calibration results is written down
     BEFORE the calibration run happens**, never chosen after seeing the numbers — the same
     blind-margin discipline as `k=2` in Phase 12's noise floor.

- **D-10:** **Scoring = mechanical substring gate + separately reported contradictions.**
  Case-insensitive substring match of the fact value, run at greedy plus N seeded samples per
  question, reported `k/N` per question and aggregated (PITFALLS-12: a success *rate* over
  held-out phrasings × multiple decode seeds, never a single transcript). **Contradiction events**
  — the completion carrying the right value alongside a competing one ("your dog is Zorp, or maybe
  Rex") — are counted and reported as a **named descriptive metric with no gate attached**, the
  same register Phase 13 used for the 79/70 role-token leakage that qualified what the retention
  gate could claim.
  **Contradiction detection must be defined MECHANICALLY where feasible** (e.g. a second candidate
  proper noun/number in the same fact slot, detected via the same tokenizer census used for the
  fact set; or hedging language combined with a second value) — **not** via a hand-curated
  per-slot competing-values list, because avoiding that editorial judgment call is the whole reason
  a stricter contradiction-as-failure gate was rejected. If no fully mechanical detector is
  feasible, fall back to a human-reviewed count under the **same quoted-evidence discipline as
  D-03**: every contradiction traceable to the exact completion text in the committed report,
  never an unlogged tally.

- **D-11:** **All three controls run**, beyond SC2's required base-without-adapter closed-book
  control:
  1. **Question-fairness check** (PITFALLS-11 control b) — the base *can* answer each recall
     question when the fact is in context, proving a failed closed-book control means "no memory"
     rather than "unanswerable question." **Must be labelled in the report as a question-validity
     check, explicitly NOT a mechanism comparison**, or it reads as the deferred DEMO-F2 smuggled
     in early. (The two are genuinely different: DEMO-F2 is a comparative baseline measuring
     prompt-vs-weight recall *parity*; this is a one-directional check that validates the question
     set.)
  2. **No-collateral-collapse check** (PITFALLS-11 control c / FEATURES §4) — the adapter on
     unrelated questions still behaves like the conversational base rather than a single-topic
     persona parrot. Measured with existing machinery: masked dialogue val PPL on held-out
     PersonaChat, adapter on vs off, plus transcripts.
  3. **Adapter-off round-trip bit-identity** — with the adapter toggled off, fresh-process logits
     are bit-identical to the un-adapted conversational base. Phase 9 pins this on fixtures; this
     runs it on the real 13.9M convbase + the real persona adapter, making the demo's central
     toggle claim *measured* rather than inherited from unit tests.

  **Shared framing requirement:** each control's report section **must open by naming the specific
  ambiguity or failure mode it closes** (question validity / persona collapse / toggle
  correctness) — not present as a list of extra measurements. Mirrors Phase 13's reconciliation
  discipline (why §8 and the A/B are not in tension) and D-03's guessability framing. Every
  control in this project earns its place by naming the gap it closes, not by existing as generic
  rigor.

- **D-12:** **Gate-miss policy = Phase-12 verbatim.** A missed threshold is recorded **unamended**
  in the committed report. Any subsequent decision about whether or how the adapter still ships
  (retry with a different recipe, ship as-is with the miss documented, or not ship) is logged in a
  section with the **exact same register as Phase 12's "Production Config Decision — post-verdict,
  discretionary"**: separate from the gate verdict, dated after it, and explicit that it does not
  reopen or amend the pre-registered threshold. This keeps Phase 14 consistent with the precedents
  already set (λ=0.01 after §8; the retention-only gate framing) rather than introducing a new
  discipline because this is the demo fewest readers get past the headline of.

### Teaching grammar & held-out split

- **D-13:** **Held-out means entirely held-out template FAMILIES**, not new instances within taught
  families. Testing whether the fact was internalized independent of phrasing *structure* is the
  claim DEMO-06 actually needs. Same "prove the strong version unless cost is prohibitive" logic
  that decided every prior choice here (adversarial fact values over convenient ones, reserved gate
  probes as proven-unguessable seeds, two-tier fact labelling over silent attrition).

- **D-14:** **Family allocation is derived from the calibration run**, under the D-09 decision rule
  — which must now specify **how family allocation is derived, not just the threshold**. Concretely:
  if calibration shows recall saturating with fewer taught instances than the literature's
  ~10-per-fact figure suggests, the real set's taught-family count scales down accordingly; if
  held-out family-level variance is high in calibration, the real set needs **more** held-out
  families, even at the cost of fewer taught families than the injection literature recommends.
  The **calibration set's own family structure must mirror a reasonable guess at the real set's
  likely final shape** — not be designed arbitrarily and checked for threshold purposes only — so
  the same run answers both questions honestly rather than half-answering one and guessing the
  other.

- **D-15:** **PersonaChat replay is decided off the calibration run, via a paired comparison.** The
  calibration run's design **includes a with-replay vs without-replay arm**, measured on the exact
  no-collateral-collapse metric from D-11.2 (masked dialogue val PPL, adapter on/off, held-out
  PersonaChat) — not a single calibration pass. The pre-written decision rule states the
  **collapse-magnitude threshold above which replay becomes mandatory** for the real run. If
  calibration shows no meaningful collapse signal without replay at 331,776 trainable params, the
  real run proceeds **without** replay, preserving the full teaching signal rather than diluting it
  against an unconfirmed risk.

  **Net effect of D-09 + D-14 + D-15: ONE calibration run answers three questions — threshold,
  family allocation, and replay — from one measured source, instead of three separately-justified
  guesses.** Its decision rule, covering all three derivations, is committed before it runs.

### Claude's Discretion

- **Loss masking for the teaching run.** PITFALLS-14 is explicit that the two masking regimes must
  not be conflated: stage-2 LM tuning legitimately trains on both speakers (Phase 12 measured this
  and chose **unmasked**), but **personalization/QA teaching must cover only the ANSWER tokens**,
  or the model learns to imitate questions instead of answering. Phase 14 therefore reverses Phase
  12's masking verdict *by design, not by drift* — the planner should say so explicitly and cite
  PITFALLS-14, and watch the named bug family there (mask built in *target* space to match the
  v1.0 one-position label shift, not input space).
- **Teaching-data materialization** — in-memory masked batches vs on-disk bins. Research
  (`ARCHITECTURE.md` §Stage 3) assumes in-memory; the corpus is tiny. Planner's call.
- **Adapter training recipe** — LR, batch size, and the deliberate-overfit step budget
  (`ARCHITECTURE.md` suggests ~100–300 steps). `weight_decay=0.0` is already established for
  adapter runs (`scripts/train_adapter_smoke.py`, 09-RESEARCH Pattern 3) and should carry over.
- **EWC penalty during the teaching run** — the base is frozen and only A/B receive gradient, so
  the quadratic anchor has nothing to protect; expect `penalty_fn=None`. Planner should confirm and
  state the reasoning rather than leaving it implicit.
- **Candidate pool size** entering the pre-flight gate, constrained only by D-06's requirement that
  the survivor count be reported against the 5–10 target.
- File/module naming, test organization, and the exact shape of the report tables.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/ROADMAP.md` — Phase 14 goal + 4 success criteria; the research flag naming the
  teaching-set template grammar and threshold pre-registration as needing this discuss pass;
  dependency map (needs Phase 9 + Phase 12, independent of Phase 13, feeds Phase 15)
- `.planning/REQUIREMENTS.md` — DEMO-05/06/07 text; the **Out of Scope table**, which is
  load-bearing here: no external-API paraphrase generation, no facts in a system prompt at demo
  time, no merging LoRA as the demo deploy path (it destroys the toggle), no ConvAI2-style chat
  quality chasing; DEMO-F1 (two-persona swap) and DEMO-F2 (prompt-stuffed baseline) are **Future
  Requirements**, not this milestone

### v2.0 research (converged — do not re-litigate)
- `.planning/research/PITFALLS.md` **§Pitfall 11** — the clean-room protocol; the demo-killing
  prompt-leakage failure mode; the proof triple this phase's D-11 controls implement
- `.planning/research/PITFALLS.md` **§Pitfall 12** — teaching a 13.9M model: paraphrase diversity
  required, entity tokenizer pre-flight, success-rate-not-transcript evaluation, honest partial
  recall over suspicious perfect recall
- `.planning/research/PITFALLS.md` **§Pitfall 14** — the two masking regimes; why personalization
  teaching masks to answer tokens (see Claude's Discretion) and the target-space off-by-one bug
  family
- `.planning/research/ARCHITECTURE.md` **§Stage 3 — teach-then-recall (LoRA)** — the flow sketch,
  the proposed `scripts/personalize_demo.py` Blocks UI, and **Anti-patterns 6 and 7** (don't expect
  1–2 sentences to bake in; never skip `forbid_ids` in a new demo)
- `.planning/research/FEATURES.md` **§4** — fact-count guidance (5–10), paraphrase-count finding,
  the clean-room verification checklist, and the control taxonomy D-11 draws from

### Prior-phase contracts this phase consumes
- `.planning/phases/09-lora-core/09-CONTEXT.md` — D-01/D-02 adapter artifact + base fingerprint
  (warn-not-error on mismatch, written for exactly this phase's convbase-trained adapter);
  D-05/D-06 toggle semantics (`set_adapter_enabled`, `adapter_disabled`, `eject_adapter`)
- `.planning/phases/09-lora-core/09-REVIEW.md` — CR-01/CR-02 context. **Both are FIXED** (commits
  `0ee8768`, `5ebd075`): toggle×merge mutual blindness now raises, and `load_adapter_weights`
  audits shapes/dtypes before mutating. The PROJECT.md note "resolve before Phase 14 consumes these
  APIs" is **already discharged** — do not re-open it as debt.
- `results/inflation_report.md` — the Phase-11 committed-report + blocking-user-verdict precedent
  that D-06's fact-set gate mirrors
- `results/phase13_ab_report.md` — the pre-registration, descriptive-vs-gated-metric, and
  reconciliation-section register that D-10/D-11/D-12 mirror
- `results/transcripts.md` + `scripts/make_transcripts.py` — the committed-evidence format and the
  prompt-construction discipline (prompts are `encode_dialogue` id sequences, never hand-formatted
  strings — inflation-report Pitfall 4)

### Code seams
- `src/personacore/lora/inject.py` — `inject_lora`, `mark_only_lora_trainable`,
  `set_adapter_enabled`, `adapter_disabled`, `eject_adapter`, `lora_state_dict`, `snapshot_params`
- `src/personacore/checkpoint.py` — `export_adapter`/`load_adapter` (`weights_only=True`),
  `load_slim`
- `src/personacore/dialogue/serialize.py` — `encode_dialogue`, `render_document`, `cap_persona`,
  `detokenize`
- `src/personacore/generation/` — `collect`, `generate_text_cumulative`, `undecodable_ids_mask`
- `scripts/train_adapter_smoke.py` — the closest existing analog to this phase's teaching run
  (load → inject → freeze → `train()` → canary → `export_adapter`), including the explicit
  `raise SystemExit` proof style and `weight_decay=0.0`
- `scripts/demo_app.py` — the offline-Gradio pattern (analytics kill-switch before `import gradio`,
  `share=False`, `forbid_ids` captured at build time, CPU-pinned `RuntimeConfig`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Measured finding — record this, do not carry it as a check

**PITFALLS-12's `forbid_ids` sub-filter is structurally unfireable.** Measured against the real
frozen tokenizer this session: all 256 byte ids are live, and BPE falls back to bytes for anything
unmerged, so `encode()` **can never emit a dead id**. Dead ids (7,645 of 8,192) are unreachable
*merges*, not unreachable bytes. The fact-set report should state this as a no-op rather than
performing it as theatre. Only the token-count half of filter (a) has any content — and per D-04
it is a census, not a gate.

**Token census measured on candidate values** (all round-trip exact, zero dead ids):

| value | tokens | value | tokens |
|---|---|---|---|
| `Max`, `Lily` | **1** | `Zorp`, `Kalo`, `Krix`, `7412`, `Voss` | 4 |
| `dog` | 2 | `Zibby`, `Halvo`, `Oberlin`, `Lisbon` | 5 |
| `Fenn`, `Tarn`, `Vim` | 3 | `Rafael`, `Ipanema`, `kombucha`, `Pemberly` | 6–7 |
| `blue` | 4 | `Marrowgate`, `accordion` | 8–9 |

The load-bearing reading: **cheap tokenization is the warning sign, not the reward.** `Max` and
`Lily` cost 1 token *because* they are frequent in the training fixture — exactly the prior mass
that makes them invalid under D-01. Short invented names (3–4 tokens) are *cheaper than or equal
to* common English words like `blue` (4). The tradeoff D-01 was willing to pay costs approximately
nothing.

### Reusable Assets
- **LoRA runtime is complete and consumable** (Phase 9): `LoRAConfig(r=8, α=16)` → 331,776
  trainable params / ~1.35 MB adapter; `inject_lora` → `mark_only_lora_trainable`;
  `export_adapter`/`load_adapter` through the `weights_only=True` choke point;
  `set_adapter_enabled` / `adapter_disabled` / `eject_adapter` for the live toggle — with the
  toggle×merge guards now in place (09-REVIEW CR-01, fixed).
- **`scripts/train_adapter_smoke.py`** is a near-template for the teaching run: load vanilla → load
  base state → `inject_lora` → freeze → `train()` → params-actually-update canary → `export_adapter`
  with the base fingerprint **read from** the base checkpoint, never recomputed.
- **`scripts/make_transcripts.py`** is the template for scripted evaluation: `encode_dialogue`-built
  prompts truncated to end at `<|assistant|>` (8186), `collect(...)` with `stop_ids={8184, 8185}`
  and `forbid_ids`, stop-fraction and role-token-leakage proxies, committed markdown evidence.
- **`masked_perplexity()`** (`src/personacore/evaluation/`) is the frozen dialogue-val gate metric —
  the exact instrument D-11.2's no-collateral-collapse check and D-15's paired replay comparison
  need. `estimate_loss`'s random-batch mean is disallowed for gates (Phase 12 12-02).
- **`undecodable_ids_mask`** + `build_demo`-time `forbid_ids` capture — reuse verbatim
  (ARCHITECTURE Anti-pattern 7).

### Established Patterns
- **Pre-registration lives in the committed driver** as module-level constants + gate as pure
  functions, tested by loading the script via `importlib` rather than moving rules into the package
  where the driver could drift (Phase 13 13-01).
- **Committed report + blocking user verdict** before the design it gates hardens (Phase 11 11-03
  inflation gate; Phase 12 12-04 D-07 checkpoint).
- **Honest negatives stand unamended**; discretionary continuations are logged separately, dated
  after the verdict (Phase 12 §8 → λ=0.01).
- **Explicit `raise SystemExit`, never `-O`-strippable `assert`**, for every proof check in a script.
- **Prompts are id sequences from `encode_dialogue`**, never hand-formatted strings.
- **New CSV file per run/arm**, fieldnames fixed at run start (ARCHITECTURE Anti-pattern 3).
- CPU-only, GPU-free test suite; heavy artifacts and `data/` are gitignored, evidence lives in
  `results/`.

### Integration Points
- Base substrate: `checkpoints/convbase_best.pt` (full, EWC extras embedded) for training;
  `convbase_slim.pt` (`weights_only=True`, 55.6 MB) for the demo path.
- Load ordering is load-bearing: **load vanilla → load base state_dict → `inject_lora` → freeze.**
  Injecting before loading breaks every checkpoint key (ARCHITECTURE Anti-pattern 1).
- Phase 15 consumes this phase's recall numbers (DOC-02) and `merged_state_dict()` / `scale·B@A`
  for the ΔW heatmaps (VIZ-02) — the adapter must never ship merged.

</code_context>

<specifics>
## Specific Ideas

- **The recurring principle, stated by the user across every decision this session:** prove the
  strong version unless cost is prohibitive. It produced adversarial fact values over convenient
  ones, reserved gate probes as *proven*-unguessable held-out seeds rather than assumed ones,
  entirely held-out template families over new instances of taught ones, a two-tier fact labelling
  over silent attrition, and all three controls over the one SC2 requires.
- **Documented judgment beats silent judgment.** Wherever a mechanical rule cannot see the failure
  mode that matters (close-call guessability, contradiction detection), the fallback is a human
  call that **quotes the exact triggering text in the committed report** — never an unlogged tally.
  This appears in D-03 and again in D-10 by explicit analogy.
- **Every control names the gap it closes**, in the opening line of its report section. Generic
  rigor is not a justification (D-11).
- **One measured source over three guesses.** The calibration run was deliberately grown to answer
  threshold, family allocation, and replay together (D-09/D-14/D-15) rather than letting each be
  independently justified and checked for compatibility afterward.

</specifics>

<deferred>
## Deferred Ideas

- **Demo surface & clean-room evidence — NOT DISCUSSED, the phase's largest open scope question.**
  This session hit its context limit before reaching it. The researcher/planner must resolve:
  - **Teach-in-UI vs ship-a-trained-adapter.** `ARCHITECTURE.md` §Stage 3 proposes a new
    `scripts/personalize_demo.py` with `gr.Blocks` **Teach/Chat/Reset** tabs — live on-device
    training inside the UI. SC4 and DEMO-07 only require that *"the adapter toggles on/off live —
    same process, same prompt, memory on/off."* That gap is the difference between a small plan and
    a large one and should be an explicit, argued decision, not an inherited assumption.
  - **New script vs extending `scripts/demo_app.py`**, which is honesty-locked (08-UI-SPEC) as the
    M1 TinyStories story-completer with "no personalization yet — that's Milestone 2" in its
    description string.
  - **Where SC2's context-token dump lives** — scripted harness only, or surfaced in the UI.
    PITFALLS-11 step 3 calls displaying the exact token ids fed to the model "the single feature
    [that] converts 'trust me' into 'check it'."
  - **The generation-budget constraint flagged in D-04** — max new tokens per recall response vs
    the token cost of the locked fact values. An engineering constraint of the demo surface, to be
    named as such, never as a guessability proxy.

  If the user wants these decided by them rather than by the planner, run a second
  `/gsd-discuss-phase 14` pass (choose "Update it") before planning.

- **DEMO-F1 two-persona adapter swap** — the strongest scientific control (same base weights, two
  adapters, two memories). Already a Future Requirement; needs a second teaching set + training run.
- **DEMO-F2 prompt-stuffed comparative baseline** — measuring prompt-vs-weight recall *parity*.
  Already a Future Requirement. Note D-11.1's question-fairness check is deliberately narrower and
  must be labelled to keep the two distinct.
- **Merged-slim export path** (`merge()` → `export_slim`) — carried from Phase 9's deferred list.
  Not needed here: merging destroys the toggle, which is the demo.

</deferred>

---

*Phase: 14-Teach-Then-Recall Demo*
*Context gathered: 2026-08-01*
