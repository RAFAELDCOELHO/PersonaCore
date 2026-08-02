# Phase 14: Teach-Then-Recall Demo - Research

**Researched:** 2026-08-01
**Domain:** LoRA knowledge injection at 13.9M params + clean-room recall protocol + offline Gradio Blocks demo
**Confidence:** HIGH on repo seams and measured base behavior (first-party, re-verified this session) · MEDIUM on knowledge-injection recipe (literature is at 7B+ scale; 13.9M is extrapolation) · LOW on achievable recall rates (must be measured — this is what D-09's calibration run exists for)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Fact-set selection (the validity foundation)**

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

**Pre-flight gate shape**

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

**Thresholds, scoring & controls**

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

**Teaching grammar & held-out split**

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

**Demo surface & clean-room evidence**

- **D-16:** **The demo ships a pre-trained adapter with a live toggle + Reset — there is NO Teach
  tab.** The UI loads `convbase_slim.pt` + the persona `adapter.pt` produced by the gated offline
  teaching script, and offers memory **ON/OFF** (`set_adapter_enabled`) plus **Reset**
  (`eject_adapter` — "drop the adapter, instant forget"). Teaching provably happened in a
  *different process*, so PITFALLS-11 step 1 ("save adapter; **kill the process**") is satisfied by
  construction and the clean-room claim is inherited rather than re-argued.
  **The "no watch-it-learn moment" cost is accepted as the correct trade, not a compromise:**
  ARCHITECTURE §Stage 3's in-UI Teach tab would put teaching and recall in the same process, so the
  clean room would have to be re-established afterward (realistically by forcing a restart before
  recall — the Teach tab arguing against itself), undermining exactly the claim SC4 exists to
  demonstrate. **No stretch or deferred Teach tab** — this decision is closed, not an expectation
  to manage later. Do not reintroduce it during planning.

- **D-17:** **New standalone `scripts/personalize_demo.py`; `scripts/demo_app.py` stays LITERALLY
  untouched.** The M1 demo's 08-UI-SPEC honesty lock ("This is the Milestone-1 base model: no chat
  tuning, no personalization yet — that's Milestone 2") stays true and the v1.0 artifact stays
  reproducible exactly as shipped. The small offline boilerplate is therefore duplicated
  (analytics kill-switch **before** `import gradio`, `share=False`, CPU-pinned `RuntimeConfig`,
  `forbid_ids` captured at build time).
  **Required mitigation:** a CPU-only regression test (no GPU, no generation) asserting
  `personalize_demo.py`'s `forbid_ids` construction matches `demo_app.py`'s — **comparing the
  resulting mask tensors directly**, same mask-building call from the same source function, not
  trusting visual code similarity. This makes the ARCHITECTURE Anti-pattern-7 drift risk
  structurally caught by CI, in the register of Phase 12's WR-04 duplicated-`cap_persona` fix —
  except the fix here is a shared *test* rather than a shared *function*, precisely because
  `demo_app.py` must not be refactored.
  **Scope rule for the same treatment:** cover other duplicated boilerplate this way **only where a
  named, documented anti-pattern is attached to getting it wrong**; name any such piece explicitly
  in the plan. Generic duplication (analytics kill-switch ordering, CPU pin) with no named failure
  mode does not need its own test. `forbid_ids` does, because it has an anti-pattern number.

- **D-18:** **The context-token dump lives in BOTH places.** The scripted recall harness writes the
  exact prompt token ids into the committed `results/` evidence (SC2's literal requirement), AND
  the demo displays the exact ids fed to the model each turn — PITFALLS-11 step 3 calls the live
  display "the single feature [that] converts 'trust me' into 'check it'," letting a reviewer
  watching the demo see the fact string is absent from context without opening a report.
  **Required mitigation:** the UI panel must render its token-id display **from the exact same
  prompt-construction function the harness calls**, never a parallel reimplementation that could
  silently diverge from what the model actually receives. A regression test asserts the UI panel's
  displayed ids and the harness's committed dump are **byte-identical for the same input** — same
  structural-enforcement register as D-17's drift test. This is the same failure mode under a
  different name: two code paths claiming to show or prove the same thing, which stays true only if
  something enforces it structurally rather than by convention.
  *Shape consequence:* the toggle alone could ride `gr.ChatInterface`'s `additional_inputs` (as the
  M1 sliders do), but Reset/eject is stateful and destructive and the token panel is a second
  output — together these commit the demo to `gr.Blocks`.

- **D-19:** **Generation budget is derived from the fact-set token census, with a hard fit guard.**
  The scoring harness uses a **fixed** `max_new_tokens` derived from the locked fact set's token
  census plus documented headroom, and **raises `SystemExit` if any locked fact's value cannot
  fit** — an unutterable fact would otherwise present as a recall failure while the real cause is
  budget, the single most misleading way this could break. The demo UI keeps an exploration slider
  **whose minimum is that constant**, so no in-UI setting can manufacture a false negative; the
  minimum needs a comment saying why it is not zero.
  **The derivation must be committed as an auditable computation** — a small function or a clearly
  commented constant derivation in the harness showing the fact-set token census it was computed
  from, the headroom formula, and the resulting constant, **in one place a future reader can
  re-derive without re-running anything.** Not a number that "was derived" in a chat log, and not a
  comment saying "trust this." Same discipline this phase applies to every other locked number.

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

### Deferred Ideas (OUT OF SCOPE)

- **ARCHITECTURE §Stage 3's in-UI Teach tab — CLOSED, not deferred.** Rejected on the merits in
  D-16 (it would put teaching and recall in one process, forcing the clean room to be re-proved).
  Recorded here so a future reader does not mistake its absence for an oversight or revive it as a
  stretch goal. Reopening it requires a new decision, not a plan-time judgment call.
- **DEMO-F1 two-persona adapter swap** — the strongest scientific control (same base weights, two
  adapters, two memories). Already a Future Requirement; needs a second teaching set + training run.
- **DEMO-F2 prompt-stuffed comparative baseline** — measuring prompt-vs-weight recall *parity*.
  Already a Future Requirement. Note D-11.1's question-fairness check is deliberately narrower and
  must be labelled to keep the two distinct.
- **Merged-slim export path** (`merge()` → `export_slim`) — carried from Phase 9's deferred list.
  Not needed here: merging destroys the toggle, which is the demo.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **DEMO-05** | Teach-then-recall clean-room demo — 5–10 atomic user facts, ~20–50 template/hand-written paraphrases per fact (no external-API augmentation), LoRA adapter on the frozen conversational base, fresh-process empty-prompt scripted recall with pre-registered thresholds, base-without-adapter control | §Measured Findings F1–F5 (prompt shape, base register, base cannot in-context-copy); §Architecture Patterns 1–4 (teaching bins, load order, `penalty_fn=None`, answer-span masking is already implemented by `encode_dialogue`); §Don't Hand-Roll (masking, prompt construction, adapter export); §Pitfalls 1–8 |
| **DEMO-06** | Held-out-phrasing recall split — taught phrasings vs never-seen phrasings scored and reported separately (learning vs memorization) | §Architecture Pattern 5 (template-family grammar + structural leakage guard); §Architecture Pattern 6 (deterministic scoring + mechanical contradiction detector); §Pitfall 6 (reversal curse interacts with D-13); §Validation Architecture |
| **DEMO-07** | Adapter on/off toggle in the Gradio demo — same process, same prompt, memory on/off live | §Architecture Pattern 7 (Blocks wiring, `set_adapter_enabled`/`eject_adapter` semantics, concurrency); §Gap G1 (no id-space streaming helper exists — must be added for D-18); §Pitfalls 9–11 |
</phase_requirements>

---

## Summary

Phase 14 is unusually well-served by existing code: **every mechanism this phase needs already exists, is tested, and is consumable without modification.** LoRA injection/toggle/eject/export, `weights_only=True` adapter load, answer-span loss masking, the `-100` masked-batch training seam, deterministic masked-PPL evaluation, dead-id `forbid_ids`, `stop_ids` turn stopping, and the offline-Gradio pattern are all shipped and green (286 tests). The phase's work is therefore **almost entirely data design, experimental protocol, and evidence plumbing** — not new ML machinery. The one genuine code gap is a small id-space streaming helper (§Gap G1), because today's `generate_text_cumulative` takes a *string* prompt and the clean-room discipline requires *id* prompts.

The load-bearing new information from this session is **measured, first-party, and changes the teaching-set design**. Running `convbase_slim.pt` on the exact prompt shape this phase will use produced three findings the planner must build on. (1) The bare-persona prompt shape `<|system|><|user|>{question}<|assistant|>` works — the base stays in dialogue register and produces coherent replies from a 13–19-token prompt, so the "empty prompt" clean room is realizable inside the project's existing dialogue grammar with zero new format. (2) The base answers **in the first person as a PersonaChat speaker** ("i am a cop", "i live in the country") — it was never trained to answer *about a user* in second person, so a teaching set written in second-person assistant register ("your dog is Zorp") fights the base's learned register, while first-person persona register ("i have a dog named zorp") is in-distribution. (3) **The base cannot copy a fact from context**: with `i live in oberlin.` in the `<|system|>` span and the question `where do you live?`, it answered `i live in the country`; with the fact one user-turn back it answered `i have 2 dogs, he is a cop`. In one probe it copied the *syntactic frame* from the persona (`i have a dog named ...`) but substituted a wrong value (`my name is cuddling`) — structure copied, content not. This last finding puts **D-11.1's question-fairness control at high risk of returning a negative**, which the planner must design the report framing for *before* the run rather than discover afterward.

Everything else the phase needs is prescriptive and settled: teaching data materializes as tiny gitignored `uint16`/`uint8` bins through the already-tested `get_batch_memmap_masked` path (`train()` has no in-memory masked seam — §Pattern 1); `penalty_fn=None` is structurally forced, not merely preferable, because `inject_lora` renames base params with a `.base.` infix and `EWCPenalty.__call__` raises `ValueError` on any fisher key missing from `model.named_parameters()` (§Pattern 3); and `convbase_best.pt` and `convbase_slim.pt` carry the *identical* provenance trio (`04e724c…` / step 4000 / val_loss 1.5235939979553224), so an adapter fingerprinted against the training checkpoint loads warning-free in the demo against the slim one (§Pattern 8).

**Primary recommendation:** Author the teaching set in the base's **first-person PersonaChat register**, materialize it as tiny on-disk masked bins consumed by the untouched `train()` with `penalty_fn=None` and `weight_decay=0.0`, build every prompt (harness *and* UI) through one new three-line `build_recall_prompt()` in `personacore/dialogue/serialize.py` — the exact `cap_persona` shared-source-of-truth precedent that D-18's byte-identity test then enforces — and design the D-11.1 fairness-control report section up front to survive a negative, because the measured evidence says it will probably produce one.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fact-set validity gate (tokenizer census + guessability) | Script driver (`scripts/`) | Permanent CPU test (tokenizer half only) | D-06/D-07: pre-registration must live in the committed driver so git history is the proof (Phase-13 13-01 precedent); the guessability half needs the 278 MB checkpoint and cannot enter the CPU-only suite |
| Teaching-set template grammar | Script driver (data authoring) | Package (`encode_dialogue`) for tokenization | The grammar is experiment data, not reusable machinery; tokenization must route through the single shared encoder or gate and bins diverge (Pitfall 4 lineage) |
| Teaching corpus → masked bins | Script driver writing to `data/` | `personacore.training.data.get_batch_memmap_masked` | `train()` exposes masking *only* through aligned `.bin` paths; reusing the tested path is zero new code |
| Adapter training run | Script driver | Untouched `personacore.training.train` | `train_adapter_smoke.py` is a near-verbatim template (load → inject → freeze → train → canary → export) |
| Recall prompt construction | **Package** (`dialogue/serialize.py`) | — | D-18 requires harness and UI to call *the same function*; a shared function must live in the package (the `cap_persona` precedent) |
| Streaming generation from ids | **Package** (`generation/text.py`) | — | Gap G1: today's wrappers take string prompts; both consumers need the id-space form |
| Scoring rules + thresholds | Script driver (module-level pure functions) | Test via `importlib` | Phase-13 13-01 locked precedent: rules stay in the driver, tests load it by path |
| Live toggle / eject | Package (`lora/inject.py`, shipped) | Demo script wiring | `set_adapter_enabled` / `eject_adapter` already implement the exact semantics with merge-blindness guards (09-REVIEW CR-01, fixed) |
| Demo UI surface | Script (`scripts/personalize_demo.py`) | Package for every callback's logic | Phase-1 D-04 house rule: scripts are thin wiring; tested logic lives in the package |
| Committed evidence | `results/` (git-tracked) | — | `data/`, `checkpoints/`, `logs/`, `*.pt` are gitignored; only `results/` markdown/CSV/PNG ships |

---

## Project Constraints (from CLAUDE.md)

Directives the planner must not contradict:

1. **GSD workflow enforcement** — file-changing work runs through a GSD command, not ad-hoc edits.
2. **Python 3.11 venv is MANDATORY** — the box runs 3.14, which is an unsupported target. All commands run as `.venv/bin/python` / `.venv/bin/pytest`. `[VERIFIED: .venv/bin/python → 3.11.15]`
3. **Zero budget, no external APIs** — teaching paraphrases are template/hand-written only (also REQUIREMENTS §Out of Scope).
4. **From scratch** — no HF `peft`/`transformers` model code; no `tiktoken`/HF `tokenizers` as the implementation (oracle-only in tests).
5. **Memory in weights only** — no vector store, no RAG, no facts in a system prompt at demo time.
6. **Offline logging** — CSV + matplotlib only; no wandb/network.
7. **MPS-primary, fp32, no AMP / no `GradScaler` / no `torch.compile`** on the M3 path.
8. **CPU-only, GPU-free pytest suite** — every test must run without MPS or a checkpoint.
9. **`weights_only=True` slim/adapter contract is LOCKED** — every shareable artifact loads through the `load_slim` / `load_adapter` choke points.
10. **New CSV file per run/arm, fieldnames fixed at run start** (ARCHITECTURE Anti-pattern 3).
11. **Explicit `raise SystemExit`, never `-O`-strippable `assert`**, for every proof check in a script.
12. **Prompts are `encode_dialogue` id sequences, never hand-formatted strings** (inflation-report Pitfall 4).
13. **`ruff` line-length 100**, `select = ["E","F","W","I"]`; `make format` then `make lint`.

---

## Measured Findings (first-party, this session)

These are the highest-value inputs to planning. All were run against the real frozen tokenizer and the real `convbase_slim.pt` inside the 3.11 venv.

### F1 — Tokenizer census independently reproduces CONTEXT.md exactly `[VERIFIED: direct encode/decode, artifacts/tokenizer.json]`

| value | tokens | round-trip | value | tokens | round-trip |
|---|---|---|---|---|---|
| `Max`, `Lily` | **1** | ✓ | `Zibby`,`Halvo`,`Oberlin`,`Lisbon` | 5 | ✓ |
| `dog` | 2 | ✓ | `Rafael`,`Ipanema` | 6 | ✓ |
| `Zorp`,`Kalo`,`Krix`,`7412`,`Voss`,`blue` | 4 | ✓ | `kombucha`,`Pemberly` | 7 | ✓ |
| — | | | `Marrowgate` 8 · `accordion` 9 | | ✓ |

Live decodable ids: **547** of 8192 — unchanged. Confirms D-04's band and CONTEXT.md's "cheap tokenization is the warning sign, not the reward." **The `forbid_ids` sub-filter of PITFALLS-12 is a genuine no-op** (all 256 byte ids live ⇒ `encode()` cannot emit a dead id) — report it as a no-op, do not perform it as theatre.

### F2 — The bare-persona clean-room prompt shape works `[VERIFIED: convbase_slim.pt, greedy, forbid_ids on, stop_ids={8184,8185}]`

`encode_dialogue(tok, [], [(question, "")])` truncated at `<|assistant|>` (id 8186) produces a **13–19 token** prompt beginning `[8187, 8185, …]` — a bare `<|system|>` with zero persona content, then the user turn. The base stays in dialogue register and produces coherent replies. Sample:

```
prompt_len=19  q="what is your dog's name?"  -> 'i am a cop. i am a cop.'
prompt_len=13  q='where do i live?'          -> 'i live in the country i live in the country.'
prompt_len=14  q='what is my name?'          -> 'i am a college student'
```

**Consequence:** the clean-room prompt is realizable inside the existing dialogue grammar with **no new format and no new tokens**. The committed context dump is literally this id list.

### F3 — The base answers in FIRST PERSON as a PersonaChat speaker `[VERIFIED: same run]`

Every completion above is self-description (`i am …`, `i live in …`), never second-person assistant register (`you are …`, `your dog is …`). The base was fine-tuned on PersonaChat, where the `<|system|>` span describes the *speaker's own* persona. **A teaching set written as `"your dog is named zorp"` asks the adapter to install a register the base has never produced; `"i have a dog named zorp"` is in-distribution.**

This aligns with the v2.0 research framing already on file — FEATURES §4: *"stage 2 can train the skill of persona-consistent dialogue (persona in context), so stage 3 personalization becomes 'move the persona from the prompt into the weights' — a crisp prompt→weights distillation story."* The first-person choice is the research-sanctioned one and makes DEMO-F2 (prompt-stuffed baseline) the natural future control.

**This is a decision the planner must make explicitly and up front**, because D-14 requires the calibration set's family structure to mirror the real set's likely final shape — the register cannot be changed after calibration without invalidating it.

### F4 — The base CANNOT copy a fact from context (structure yes, content no) `[VERIFIED: same run, 6 probes]`

| Fact placement | Question | Base completion |
|---|---|---|
| `<\|system\|>` persona: `i have a dog named zorp.` | `what is your dog's name?` | `i am a cop, i am a cop. i am a cop.` |
| `<\|system\|>` persona: `i live in oberlin.` | `where do you live?` | `i live in the country i live in the country.` |
| prior user turn: `my dog is named zorp.` | `what is my dog's name?` | `i have 2 dogs, he is a cop.` |
| prior user turn: `i live in oberlin.` | `where do i live?` | `i live in the country i live in the country.` |
| `<\|system\|>` persona + 1 warm turn | `what is your dog's name?` | `i have a dog named my name is cuddling.` |

The last row is diagnostic: the base copied the **syntactic frame** (`i have a dog named …`) from the persona span but substituted a wrong value. At 13.9M params with a 3.229 tokens/word inflation tax, in-context value copying is not a capability this base has.

**Three consequences the planner must design for:**
1. **D-11.1's question-fairness control will likely return a NEGATIVE.** It is a locked control and must still run — but its report section (which D-11 requires to open by naming the gap it closes) must be written to remain honest and informative under a negative result. The available honest framing, which costs nothing: *a question the adapter answers correctly is by construction answerable, so fairness is only load-bearing for questions the adapter fails* — and for those, the report says plainly that in-context fairness could not be established at this scale, and cites the measured probe. This is the Phase-13 §13-03 honest-negative register applied prospectively.
2. **It strengthens, not weakens, the core claim.** If the base cannot recall a fact even with the fact in context, then adapter-ON recall on an empty prompt is a capability the prompt route does not provide at this scale. That is the strongest possible form of "memory lives in weights" — and it is a Phase-15/DOC-02 narrative asset (and a preview of DEMO-F2's likely outcome).
3. **The base-without-adapter closed-book control (SC2, required) is nearly guaranteed to pass**, and D-02/D-03's pre-teaching guessability gate is the *stronger* evidence for the same point because it is measured before any teaching exists.

### F5 — Teaching-corpus size and answer lengths `[VERIFIED: encode_dialogue on representative QA episodes]`

One `(question, answer)` episode ⇒ **26–45 ids**, mean ≈ 34; answer content spans **11–24 tokens**. An 8-fact × 30-paraphrase set ⇒ ≈ **8,200 tokens**, comfortably above `get_batch_memmap_masked`'s hard floor of `block_size + 1 = 257`. At `batch_size=8 × block_size=256 = 2048` tokens/step, each step sees ~25 % of the corpus; a 200-step run is ≈ 50 epochs — the deliberate overfit ARCHITECTURE Anti-pattern 6 prescribes.

`encode_dialogue` mask output on a single-turn episode: `<|system|>`=0, persona=0, first `<|user|>`=0, question=0, `<|assistant|>`=0, **answer=1, final eos=1**. This is *exactly* the answer-span masking PITFALLS-14 requires, already built in target space, already golden-fixture tested (`tests/test_dialogue_serialize.py`, `tests/test_masked_batch.py`). **Do not write a new masking implementation.**

### F6 — Base fingerprint trio matches across the training and demo checkpoints `[VERIFIED: torch.load / load_slim]`

`convbase_best.pt` and `convbase_slim.pt` both carry `git_sha=04e724c67033f9a2ed8b705a07ad025c867a18c5`, `step=4000`, `val_loss=1.5235939979553224`. An adapter exported with the fingerprint read from `convbase_best.pt` therefore loads through `load_adapter(expected_fingerprint=<slim trio>)` **without emitting the D-02 mismatch `UserWarning`**. `convbase_best.pt` additionally carries `fisher` / `theta_star` / `ewc_lambda` / `fisher_meta` extras (278 MB); the slim is 55.6 MB.

---

## Standard Stack

### Core — every dependency is already installed; this phase adds NOTHING

| Library | Installed version | Purpose | Why Standard |
|---------|------------------|---------|--------------|
| `torch` | **2.7.1** `[VERIFIED: .venv]` | model, training, MPS | Pinned line; MPS available `[VERIFIED: torch.backends.mps.is_available() → True]` |
| `numpy` | **2.4.6** `[VERIFIED: .venv]` | `uint16`/`uint8` teaching bins | The established memmap corpus format |
| `gradio` | **5.50.0** `[VERIFIED: .venv]` | `gr.Blocks` demo (D-18 forces Blocks over ChatInterface) | Already the shipped M1 demo surface; `>=5,<6` pinned in `pyproject.toml [demo]` |
| `pytest` | **9.0.3** `[VERIFIED: .venv]` | CPU-only suite (286 tests currently collected) | `[tool.pytest.ini_options]` in `pyproject.toml` |
| `matplotlib` | 3.10.9 `[VERIFIED: .venv]` | not needed this phase (Phase 15 owns figures) | — |

### Supporting — in-repo, consumed verbatim

| Module | Purpose | When to Use |
|--------|---------|-------------|
| `personacore.lora` (`inject_lora`, `mark_only_lora_trainable`, `set_adapter_enabled`, `adapter_disabled`, `eject_adapter`, `lora_state_dict`, `snapshot_params`) | injection, freeze, live toggle, reset | teaching run + demo |
| `personacore.checkpoint` (`export_adapter`, `load_adapter`, `load_slim`) | `weights_only=True` artifact choke points | adapter ship path, demo load |
| `personacore.dialogue` (`encode_dialogue`, `cap_persona`, `detokenize`, `render_document`) | the single tokenization source of truth | teaching bins, prompts, scoring normalization |
| `personacore.training` (`train`) | the untouched v1.0 loop, masked-bin seam, resume, canary-compatible | teaching + calibration runs |
| `personacore.evaluation` (`masked_perplexity`) | THE frozen dialogue-val gate metric | D-11.2 collapse check, D-15 replay arms |
| `personacore.generation` (`collect`, `generate`, `undecodable_ids_mask`) | id-space decoding + dead-id mask | recall harness, demo |
| `personacore.preflight` / `seeding` / `provenance` | device gate, `seed_everything`, `git_sha()` | every driver |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| On-disk teaching bins | `train(fixed_batch=…)` | `fixed_batch` reuses **one** batch every step (max `batch_size × block_size` tokens ≈ 2,048 at defaults) — an 8,200-token corpus does not fit, and there is no window randomization. Rejected. |
| On-disk teaching bins | a new in-memory `batch_fn` seam in `train()` | `train()` accepts no `batch_fn` kwarg; adding one modifies the frozen v1.0 loop for zero benefit at 8 KB of tokens. Rejected — ARCHITECTURE's "in-memory" suggestion predates the shipped masked-bin seam. |
| `gr.Blocks` | `gr.ChatInterface` + `additional_inputs` | D-18's stateful destructive Reset and second (token-panel) output rule it out. Locked. |
| Substring scoring | id-subsequence scoring | BPE is context-dependent at merge boundaries, so a value's id sequence differs between "…named zorp" and "zorp…". Keep D-10's normalized string match as the gate; id-subsequence is at best a diagnostic. |

**Installation:** none. `.venv` already satisfies `.[cpu,dev,demo]`.

---

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** Every dependency it uses (`torch`, `numpy`, `gradio`, `pytest`) is already pinned in `pyproject.toml` and already installed in the project venv, all verified above.

`slopcheck` is not available on this machine `[VERIFIED: command -v slopcheck → not found]` and was not installed, because there is no package to check. **Standing rule for the planner:** if any plan introduces a new import that is not in `pyproject.toml`, that plan must first run the Package Legitimacy Gate and gate the install behind a `checkpoint:human-verify` task. Adding a dependency for this phase would also need to clear CLAUDE.md's from-scratch constraint.

| Package | Registry | Disposition |
|---------|----------|-------------|
| *(none)* | — | No new packages introduced |

---

## Architecture Patterns

### System Architecture Diagram

```
                      PROCESS 1 — offline teaching (gated, headless)
  ┌───────────────────────────────────────────────────────────────────────────────┐
  │ candidate fact pool (hand-authored)                                           │
  │        │                                                                       │
  │        ├──▶ tokenizer census (encode/decode round-trip)  ──┐                   │
  │        └──▶ base guessability probe (convbase_best,        │                   │
  │             ~3-5 reserved questions/candidate, greedy+N)   ├─▶ phase14_        │
  │                                                            │   factset_        │
  │                            ══ BLOCKING USER VERDICT ═══════┴─▶ report.md       │
  │                                        │                                       │
  │                          locked fact set (5-10) + soft tier                    │
  │                                        │                                       │
  │        ┌───────────────────────────────┴──────────────────────────┐            │
  │        ▼                                                          ▼            │
  │  TAUGHT template families ─▶ (q,a) episodes            HELD-OUT families       │
  │        │                      encode_dialogue()         + reserved gate probes │
  │        │                      answer-span mask=1              │                │
  │        ▼                                                      │                │
  │  data/persona_train.bin (uint16) + _mask.bin (uint8)          │  (never enters │
  │        │        [+ optional PersonaChat replay slice - D-15]  │   the bins;    │
  │        ▼                                                      │   leakage test)│
  │  vanilla GPT ─load convbase_best─▶ inject_lora(r=8,a=16) ─▶ freeze             │
  │        │                                                      │                │
  │        ▼  train(train_bin, train_mask_bin, penalty_fn=None, wd=0.0)            │
  │  params-update canary ─▶ export_adapter(fingerprint READ from base)            │
  │        │                                                      │                │
  └────────┼──────────────────────────────────────────────────────┼────────────────┘
           ▼  checkpoints/persona_adapter.pt (~1.35 MB)           │
        ════════════ PROCESS BOUNDARY (kill; PITFALLS-11 step 1) ═╪══════════
           │                                                      │
  ┌────────┴──────────────────────────┐   ┌───────────────────────┴─────────────┐
  │ PROCESS 2 — scored recall harness │   │ PROCESS 3 — Gradio Blocks demo      │
  │ load_slim(convbase_slim)          │   │ load_slim(convbase_slim)            │
  │ inject_lora + load_adapter_weights│   │ inject_lora + load_adapter_weights  │
  │        │                          │   │        │                            │
  │  build_recall_prompt(tok, q) ◀────┼───┼────────┘  ◀── SHARED FUNCTION (D-18)│
  │        │  (ids only, no fact)     │   │        │                            │
  │        ├─▶ context-token dump     │   │        ├─▶ token-id panel (live)     │
  │        │                          │   │        │                            │
  │        ▼ collect(greedy + N seeds)│   │        ▼ stream_from_ids(...)        │
  │  score: normalize + substring     │   │  memory ON/OFF -> set_adapter_enabled│
  │  contradiction detector           │   │  Reset        -> eject_adapter       │
  │  controls: closed-book / fairness │   │                                     │
  │            collapse / bit-identity│   │                                     │
  │        ▼                          │   └─────────────────────────────────────┘
  │  results/phase14_recall_report.md │
  │  results/phase14_transcripts.md   │
  └───────────────────────────────────┘
```

### Recommended Project Structure (additions only)

```
src/personacore/
├── dialogue/serialize.py     # + build_recall_prompt(tok, question) -> list[int]   (SHARED, D-18)
└── generation/text.py        # + generate_text_from_ids(...)  cumulative str stream (Gap G1)
scripts/
├── phase14_factset_gate.py   # D-06 gated report driver (census + guessability probes)
├── teach_persona.py          # bins builder + adapter training run (calibration & real arms)
├── phase14_recall.py         # scored recall harness + all three D-11 controls + dumps
└── personalize_demo.py       # D-16/D-17/D-18 Blocks demo (demo_app.py untouched)
tests/
├── test_phase14_factset.py   # D-07 permanent tokenizer-half census test
├── test_phase14_teaching.py  # family disjointness + token-level no-leakage + mask fixture
├── test_phase14_scoring.py   # importlib-loaded scoring/contradiction/threshold pure functions
├── test_phase14_demo.py      # D-17 forbid_ids mask-tensor parity + D-18 prompt byte-identity
└── test_recall_prompt.py     # build_recall_prompt / generate_text_from_ids on tiny fixtures
results/
├── phase14_factset_report.md      # D-06 gated report
├── phase14_calibration_report.md  # D-09/D-14/D-15 (decision rule committed BEFORE it runs)
├── phase14_recall_report.md       # DEMO-05/06 thresholds, taught vs held-out, controls
└── phase14_transcripts.md         # every completion, failures included
```

### Pattern 1: Teaching data materializes as tiny on-disk masked bins

**What:** the teaching-set builder writes `data/persona_train.bin` (`np.uint16`) and `data/persona_train_mask.bin` (`np.uint8`), 1:1 length-aligned, exactly as `scripts/prepare_dialog_corpus.py` does.

**When to use:** always — this is not a preference, it is the only masked path `train()` exposes.

**Why:** `train()`'s data source is one of `fixed_batch` / `train_bin` (± `train_mask_bin`) / `corpus_path` / synthetic `[VERIFIED: src/personacore/training/loop.py:312-370]`. Masking exists **only** on the `train_bin` + `train_mask_bin` branch, which routes to the golden-fixture-tested `get_batch_memmap_masked` and its `y[m == 0] = -100` target-space shift. `fixed_batch` holds one batch (~2,048 tokens at defaults) and never re-randomizes. There is no `batch_fn` kwarg. `data/` is gitignored, so nothing personal is committed.

```python
# Source: scripts/prepare_dialog_corpus.py:107-111 (verbatim idiom)
np.concatenate(id_shards).tofile(bin_path)      # np.uint16
np.concatenate(mask_shards).tofile(mask_path)   # np.uint8
```

Hard floor: `len(bin) > block_size + 1 = 257`. Measured corpus ≈ 8,200 tokens (F5) — 32× headroom.

### Pattern 2: Answer-span masking is already implemented — reuse `encode_dialogue`

**What:** build every teaching episode as `encode_dialogue(tok, persona, [(question, answer)])`.

**Why:** the returned mask is already answer-only in target space `[VERIFIED: src/personacore/dialogue/serialize.py:57-85 + measured F5]` — `<|system|>`/persona/`<|user|>`/question/`<|assistant|>` all mask 0; answer content and the terminating eos mask 1. That is precisely PITFALLS-14's personalization regime, and it inherits the golden-fixture test that kills the off-by-one bug family. **Phase 12 chose *unmasked* for stage-2 LM tuning; Phase 14 uses *masked* — the reversal is by design, and the plan must say so and cite PITFALLS-14 (Claude's Discretion, resolved).**

The corresponding `train()` call sets **both** `train_mask_bin` and — if an in-loop val is wanted — `val_bin` + `val_mask_bin` (the loop raises if `val_mask_bin` is set without a `.bin` `val_bin`, `[VERIFIED: loop.py:282-288]`).

### Pattern 3: `penalty_fn=None` is structurally forced, not merely preferable

**What:** the teaching run passes no EWC penalty.

**Why (two independent reasons):**
1. **PITFALLS P7:** with the base frozen, base θ never moves, so the classic quadratic anchor is a constant — zero gradient into A/B, pure wasted compute, and a chart that would credit EWC with retention frozen-base LoRA produces by construction.
2. **Mechanical, verified:** `inject_lora` renames every wrapped base parameter with a `.base.` infix `[VERIFIED: lora/layer.py:26 + inject.py:41]`, while the Fisher cache keys are vanilla-GPT names. `EWCPenalty.__call__` raises `ValueError` on *any* fisher key missing from `model.named_parameters()` `[VERIFIED: continual/ewc.py:63-70]`. Passing the existing Fisher to an injected model is therefore a hard crash, not a silent no-op.

The plan should state this reasoning explicitly (Claude's Discretion asked for it) rather than leaving `penalty_fn=None` implicit.

### Pattern 4: Load order and freeze discipline (unchanged, verbatim from Phase 9)

```python
# Source: scripts/train_adapter_smoke.py:95-116 — the near-verbatim template
blob = torch.load(CONVBASE_BEST, weights_only=False)      # TRUSTED own checkpoint
model = GPT(ModelConfig(**blob["model_config"]))
model.load_state_dict(blob["model"])                       # LOAD BEFORE INJECT (Anti-pattern 1)
n = inject_lora(model, LoRAConfig())                       # r=8, alpha=16
if n != 6 * n_layer: raise SystemExit(...)                 # 36 wrappers at 6 layers
mark_only_lora_trainable(model)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
if trainable != cfg.r * n_layer * 18 * n_embd: raise SystemExit(...)   # 331,776
model.to(runtime.device)
before = snapshot_params(model)                            # canary snapshot AFTER .to()
... train(..., weight_decay=0.0, penalty_fn=None) ...
# canary: every requires_grad param moved; every frozen param bit-identical
export_adapter(path, adapter=lora_state_dict(model), lora_config=asdict(cfg),
               base_fingerprint={"git_sha": blob["git_sha"], "step": blob["step"],
                                 "val_loss": blob["val_loss"]})   # READ, never recomputed
```

**Anti-pattern:** injecting before loading breaks every checkpoint key. **Anti-pattern:** recomputing the fingerprint instead of reading it from the base checkpoint.

### Pattern 5: Template families and a *structural* held-out guarantee

**What a family is:** a syntactic/pragmatic frame class, not an instance. Each family is a named generator with a stable id, so allocation is data, not prose. Illustrative grammar (final allocation is derived from calibration per D-14):

| id | family | example (first-person register, per F3) |
|----|--------|------------------------------------------|
| `F1` | direct wh-question | `what is your dog's name?` → `my dog is named zorp.` |
| `F2` | imperative / request | `tell me your dog's name.` → `i have a dog named zorp.` |
| `F3` | statement completion | `your dog is named` → `zorp.` |
| `F4` | reversed direction | `who is zorp?` → `zorp is my dog.` |
| `F5` | yes/no verification | `is your dog named zorp?` → `yes, my dog is zorp.` |
| `F6` | topic-shifted preamble | `i love animals. what is your dog called?` |
| `F7` | indirect / memory framing | `do you remember your dog's name?` |
| `F8` | third-party framing | `if someone asked about your dog, what would you say?` |

**The structural guarantee (three mechanical checks, all cheap and all CPU-testable):**
1. `TAUGHT_FAMILY_IDS` and `HELDOUT_FAMILY_IDS` are disjoint sets asserted by a test.
2. Every held-out question's rendered, `detokenize`d string is asserted absent from the teaching corpus text.
3. **Token-level:** every held-out question's `encode_dialogue` id sequence is asserted **not** to be a contiguous subsequence of `data/persona_train.bin`. This is the direct analog of Phase 11's document-boundary no-leakage discipline and costs milliseconds on an 8 K-token bin. String-level checks alone can miss a leak that survives detokenization differences; the token check cannot.
4. D-08's reserved gate probes are seeded into `HELDOUT_FAMILY_IDS` and carry their base-failure provenance (commit SHA + quoted base completion) into the DEMO-06 report.

**Paraphrase count:** literature says QA generalization rises monotonically with paraphrase count and saturates around ~10 per fact at 7B+ scale `[CITED: arxiv.org/abs/2404.00213; arxiv.org/abs/2312.05934]`. DEMO-05 specifies 20–50, well above saturation, which is the correct posture at 13.9M where per-example signal is weaker. **Treat ~10 as a floor observed at a much larger scale, not a target** — D-14's calibration run is what turns this into a measured number for *this* model.

### Pattern 6: Deterministic scoring with a mechanical contradiction detector

**Scoring (D-10, locked):** normalize (lowercase → `detokenize` → collapse whitespace → strip punctuation) then case-insensitive substring containment of the fact value; run greedy + N seeded samples per question; report `k/N` per question and aggregate over taught and held-out tiers separately.

**Whitespace hazard to guard:** byte-level BPE can surface a value with an interior space or a fragment artifact (measured: `'i am a mort of musician'`). Collapsing whitespace before matching is necessary; do **not** skip it. Keep the normalizer as one committed pure function with a unit test — it is a scoring rule and belongs in the driver (Phase-13 13-01 precedent), loaded by test via `importlib`.

**Mechanical contradiction detector (D-10 asks for one; here is one that needs no hand-curated per-slot list):**

> A completion is a **contradiction event** iff it contains the correct value **and** at least one *other* value drawn from `LOCKED_VALUES ∪ GATE_REJECTED_CANDIDATES` — the union of the locked fact values and the candidate pool the D-06 gate already rejected.

The candidate pool is committed material produced by plan 1 of this phase, so the detector's lexicon is auditable, pre-existing, and requires zero new editorial judgment — exactly the property that got the stricter contradiction-as-failure gate rejected. Optional second signal (report separately, never gate): a hedging regex (`\bor\b|maybe|i think|actually`) co-occurring with a second value. Any residual human-reviewed contradictions fall back to D-03's quoted-evidence discipline.

### Pattern 7: Gradio Blocks wiring for a live in-process toggle

**Shape (forced by D-18):** `gr.Blocks` — Reset is stateful and destructive, and the token panel is a second output.

**Mechanics:**
- Load once at build time: `load_slim(convbase_slim)` → vanilla `GPT` → `inject_lora` → `load_adapter_weights(model, load_adapter(path, expected_fingerprint=slim_trio))`. Fingerprints match (F6) → no warning.
- **Memory ON/OFF** = `set_adapter_enabled(model, bool)`. Cost is 36 Python bool writes — instantaneous by construction, and the `enabled` flag gates the delta branch so OFF is bit-identical to the base `[VERIFIED: lora/layer.py:40]`. It refuses (`RuntimeError`) if any module is merged — never merge in the demo path.
- **Reset** = `eject_adapter(model)` — removes every wrapper, returning the vanilla module tree. **This is one-way within the process**: after eject there is nothing to re-enable. The UI must reflect that honestly — disable the toggle and state "adapter deleted; restart the app to reload it." Silently re-injecting a fresh (B=0) adapter would be indistinguishable from OFF and would misrepresent what Reset did.
- **Concurrency:** Gradio's default is one worker per event (`default_concurrency_limit=1`) `[CITED: gradio.app/guides/queuing]`, but *different* events run concurrently, and variables created outside a function are shared globally across all users `[CITED: gradio.app/guides/state-in-blocks]`. The model here is exactly such a global, and the toggle mutates it. Cheapest correct fix: give every model-touching event the **same `concurrency_id`** so they serialize, and state the single-user-local-demo assumption in the docstring. `share=False` + localhost already bounds the exposure.
- **Offline boilerplate (duplicated per D-17):** `os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"` **before** `import gradio`, `analytics_enabled=False`, `share=False`, `RuntimeConfig(device="cpu")`, `forbid_ids = undecodable_ids_mask(tok, vocab_size)` captured at build time.
- **Streaming shape:** Gradio replaces the displayed message on each yield, so the callback yields the **growing cumulative** string (08-RESEARCH Pitfall 1). With a second output (token panel), yield a tuple each step.

### Pattern 8: Provenance and clean-room evidence

Per-question context dump (committed to `results/`), containing at minimum: the exact prompt id list, its `detokenize`d rendering, its length, and an explicit `SystemExit` assertion that **no locked fact value string appears in the decoded prompt** and no fact value's id sequence appears in the prompt ids. Run-level provenance: `git_sha()`, `os.getpid()`, wall-clock, `preflight_device` summary, seed, SHA-256 of `convbase_slim.pt` and the adapter file, and the base-fingerprint trio.

Process isolation is achieved by *being separate `python` invocations* — teaching, scoring, and demo are three scripts. Recording each run's PID and timestamp plus the adapter file's on-disk existence between them makes the boundary auditable. **Do not spawn a subprocess per question** — one fresh process for the whole scored run, with each question an independent prompt never concatenated with any prior turn (the `make_transcripts.py` posture), fully satisfies PITFALLS-11 and costs nothing.

### Anti-Patterns to Avoid

- **Hand-formatted prompt strings.** Prompts are `encode_dialogue` id sequences (inflation-report Pitfall 4). `generate_text*` prepends `[eos_id]` and encodes a *string* — using it for recall would build a prompt the model was never trained on and would make the token dump lie.
- **A parallel prompt builder in the demo.** D-18 forbids it; one function, two callers, one byte-identity test.
- **Merging the adapter anywhere in the demo path.** Merge destroys the toggle and every toggle/eject function raises on a merged module by design.
- **Facts in the `<|system|>` span at teaching or recall time.** That is prompt-stuffing (REQUIREMENTS §Out of Scope) and falsifies the claim at the moment it is demonstrated. The only legitimate place a fact appears in context is inside the explicitly-labelled D-11.1 fairness control.
- **`assert` for proof checks in scripts.** `python -O` strips them; use `raise SystemExit`.
- **Appending columns to an existing CSV.** New file per run/arm, fieldnames fixed at start.
- **Committing personal facts.** Use synthetic/invented values throughout (PITFALLS Claim-Integrity table); `results/` is public.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Answer-only loss masking | a QA masking routine | `encode_dialogue` + `get_batch_memmap_masked` | Target-space `-100` shift already correct and fixture-tested; PITFALLS-14's off-by-one family is already dead |
| Recall prompt construction | a formatted f-string | `build_recall_prompt` over `encode_dialogue` | Guarantees prompt tokenization matches training bins; D-18's byte-identity test depends on one function |
| Adapter save/load | `torch.save(model.state_dict())` | `export_adapter` / `load_adapter` | `weights_only=True` LOCKED contract, key+shape audit before mutation (09-REVIEW CR-02, fixed), fingerprint provenance |
| Toggle / reset semantics | ad-hoc flag flipping | `set_adapter_enabled` / `adapter_disabled` / `eject_adapter` | Merge-blindness guards (CR-01, fixed) prevent a dead "memory off" switch — the exact failure that would falsify DEMO-07 |
| Dialogue-quality metric | a bespoke score | `masked_perplexity` on `dialog_val.bin`+mask | THE frozen gate metric; `estimate_loss` is disallowed for gates (Phase 12 12-02) |
| Dead-id masking | a custom filter | `undecodable_ids_mask` at build time | ARCHITECTURE Anti-pattern 7; skipping it re-imports the pre-CR-01 crash class |
| Turn stopping | trimming decoded text | `stop_ids={8184, 8185}` | Stop-without-yield is the pinned idiom; text trimming cannot see a mid-glyph boundary |
| Determinism / provenance | ad-hoc seeding | `seed_everything`, `preflight_device(strict=True)`, `git_sha()` | QA-02 reproducibility contract |
| Cumulative streaming decode | a decode-per-token loop | `generate_text`'s cumulative-buffer idiom (reuse in the new id-space helper) | Byte-level BPE glyphs span ids; naive per-token decode raises `UnicodeDecodeError` or emits mojibake |

**Key insight:** this phase's failure modes are *experimental-design* failures (leakage, guessability, cherry-picking, a dead toggle), not implementation failures. Every line of ML machinery it needs is already written and tested — so every hand-rolled reimplementation is pure added risk with zero narrative payoff.

---

## Gaps in Existing Code

### G1 — There is no id-space streaming generation helper (must be added)

`generate_text` / `generate_text_str` / `generate_text_cumulative` all take a **string** prompt and build ids as `[eos_id] + tokenizer.encode(prompt)` `[VERIFIED: generation/text.py:95]`. The clean-room discipline requires the prompt to be an `encode_dialogue` id sequence beginning `[8187, 8185, …]`. The core `generate`/`collect` are id-space but yield ids, not display text.

**Recommendation:** add one small helper beside the existing wrappers, e.g. `generate_text_from_ids(model, tokenizer, prompt_ids, *, max_new_tokens, **gen_kw)` that drives `core.generate` from a supplied id tensor and reuses `generate_text`'s cumulative-buffer decode (including the `UnicodeDecodeError` continue). ~15 lines, unit-testable on the existing tiny-GPT fixtures, and it gives the harness and the UI one shared decode path. Do **not** inline it in the demo script — that would create the second code path D-18 exists to prevent.

### G2 — `build_recall_prompt` has no home yet

Three lines, and it belongs next to `cap_persona` in `dialogue/serialize.py`, whose docstring already establishes the "SINGLE source of truth … both import THIS function, so prompts tokenize identically to the training bins by construction" pattern that D-18 is asking for.

```python
ASSISTANT_ID = SPECIAL_TOKENS["<|assistant|>"]  # 8186

def build_recall_prompt(tok, question, persona=()):
    """The clean-room prompt: <|system|>[persona] <|user|>question <|assistant|> — ids only."""
    ids, _mask = encode_dialogue(tok, list(persona), [(question, "")])
    return ids[: ids.index(ASSISTANT_ID) + 1]
```

Default `persona=()` yields a bare `<|system|>` with no content — the strongest form of "empty prompt": the context carries the question and nothing else.

---

## Common Pitfalls

### Pitfall 1: Teaching in a register the base never produced
**What goes wrong:** the teaching set uses second-person assistant phrasing ("your dog is Zorp") while the base only ever produces first-person PersonaChat self-description. The adapter must install both a fact *and* a register with 331,776 parameters; recall rates come in low and the cause is mis-attributed to capacity.
**Why it happens:** the demo narrative ("the model remembers *you*") pulls toward second person; nobody checks what the base actually emits.
**How to avoid:** F3 measured it — teach first-person. Frame the claim as FEATURES §4 already does: the persona moves from the prompt into the weights.
**Warning signs:** taught-phrasing recall well below held-out expectations; completions that answer in the wrong grammatical person.

### Pitfall 2: The question-fairness control returns a negative and the report has no framing for it
**What goes wrong:** D-11.1 runs, the base fails *with* the fact in context (F4 says it will), and the report is left unable to say what the control was supposed to establish.
**How to avoid:** write that section's framing before the run: fairness is only load-bearing for questions the adapter fails; questions the adapter answers are answerable by construction; and an in-context negative is itself a reportable capability finding that *strengthens* the weights-vs-prompt claim.
**Warning signs:** a plan that treats D-11.1's outcome as assumed rather than measured.

### Pitfall 3: The held-out split leaks through shared template structure
**What goes wrong:** "held-out" phrasings are new instances of taught families, so the number measures paraphrase interpolation rather than internalization — the exact thing D-13 rejects.
**How to avoid:** whole families held out, plus the three mechanical disjointness/leakage assertions in Pattern 5 — including the token-level contiguous-subsequence check against the bin.
**Warning signs:** held-out recall statistically indistinguishable from taught recall; a "held-out" question that differs from a taught one by one word.

### Pitfall 4: Reversal-curse families dragged into the gated held-out tier
**What goes wrong:** a reversed-direction family (`who is Zorp?`) is held out and fails near-completely, pulling the pre-registered held-out number down for a reason documented in the literature rather than a property of this model. `[CITED: arxiv.org/abs/2309.12288 — "A is B" fine-tuning does not yield "B is A"; persists across fine-tuning methods; the in-context case is the documented exception]`
**How to avoid:** PITFALLS-12 already prescribes teaching QA forms **in both directions** — so reversed forms belong in the *taught* families. If any reversed family is nonetheless held out, report it as a separately labelled tier with the citation, in D-05's soft-tier register. The D-09/D-14 decision rule must settle this **before** calibration.
**Warning signs:** a family allocation that puts all reversed forms on the held-out side.

### Pitfall 5: The teaching corpus is too small to draw a window
**What goes wrong:** `get_batch_memmap_masked` calls `np.random.randint(0, len(data) - block_size - 1)`; with ≤ 257 tokens this raises an opaque numpy error.
**How to avoid:** assert bin length > `block_size + 1` at build time with a `SystemExit` naming the number. Measured corpora are ~8,200 tokens (F5), but a shrunken fact set (D-06's explicitly anticipated outcome) plus few families could approach the floor.
**Warning signs:** `ValueError: low >= high` from numpy at step 0.

### Pitfall 6: Generation budget silently causes false-negative recall
**What goes wrong:** `max_new_tokens` is too small for the model's preamble plus the fact value, so the value never gets uttered and the transcript reads as a memory failure. D-19 names this "the single most misleading way this could break."
**Why it happens:** greedy decoding on this base loops (measured: `i live in the country i live in the country.`), consuming budget before reaching the value.
**How to avoid:** D-19's derived constant with the auditable computation and the `SystemExit` fit guard; the UI slider floors at that constant. Budget the *observed answer length* (11–24 tokens, F5) plus the value's census, plus documented headroom for the looping preamble.
**Warning signs:** completions that end mid-sentence at exactly `max_new_tokens`; a stop-fraction well below the Phase-12 transcripts' 30/30.

### Pitfall 7: The Fisher-bearing checkpoint is loaded into an injected model
**What goes wrong:** `EWCPenalty` raises `ValueError` naming every fisher key as missing, because injection renamed base params with `.base.`.
**How to avoid:** `penalty_fn=None` (Pattern 3). Also note `convbase_best.pt` is 278 MB precisely because it carries `fisher`/`theta_star`; the teaching run needs only `model` + `model_config` + the fingerprint trio from it.

### Pitfall 8: MPS silent-freeze class (inherited, still live)
**What goes wrong:** trainable params never move while loss looks plausible (PITFALLS P5).
**How to avoid:** the `snapshot_params` canary after `.to(device)`, with `raise SystemExit` on any trainable that did not move or any frozen param that did — `train_adapter_smoke.py` already does exactly this on real weights. Plus a finite-loss check.

### Pitfall 9: Reset leaves a toggle that appears to work but cannot
**What goes wrong:** after `eject_adapter`, the wrappers are gone; a UI that still offers "memory ON" either errors or silently does nothing.
**How to avoid:** disable the toggle after Reset and say why in the UI copy.

### Pitfall 10: Two Gradio events mutate the shared model concurrently
**What goes wrong:** a toggle flip lands mid-generation, so the streamed answer is half memory-on and half memory-off — and the token panel no longer describes what produced the text.
**How to avoid:** one `concurrency_id` across all model-touching events; document the single-user local assumption.

### Pitfall 11: Adapter-off bit-identity checked on MPS across processes
**What goes wrong:** the D-11.3 bit-identity claim is made on a backend with reduction-order variance. Phase 13 measured eval PPL differing by ~3.6e-8 across processes on MPS while free-running generation was bit-identical.
**How to avoid:** run the logits comparison on **CPU** (the standing "correctness on CPU, MPS for performance" discipline) and use `torch.equal`. With the adapter disabled the wrapper's forward is literally `self.base(x)`, so bit-identity is structural — but proving it on the deterministic backend removes the only source of doubt.

---

## Code Examples

### Building the teaching bins

```python
# Source: composition of scripts/prepare_dialog_corpus.py:107-111 and
#         src/personacore/dialogue/serialize.py::encode_dialogue (both verified in-repo)
id_shards, mask_shards = [], []
for fact in LOCKED_FACTS:
    for family_id in TAUGHT_FAMILY_IDS:
        for question, answer in render_family(family_id, fact):   # first-person register (F3)
            ids, mask = encode_dialogue(tok, [], [(question, answer)])
            id_shards.append(np.asarray(ids, dtype=np.uint16))
            mask_shards.append(np.asarray(mask, dtype=np.uint8))   # answer + eos == 1
tokens = np.concatenate(id_shards)
if len(tokens) <= BLOCK_SIZE + 1:
    raise SystemExit(f"teaching corpus {len(tokens)} tokens <= block_size+1 — cannot draw a window")
tokens.tofile(PERSONA_BIN)
np.concatenate(mask_shards).tofile(PERSONA_MASK_BIN)
```

### Scored recall on one question (harness)

```python
# Source: scripts/make_transcripts.py:67-81 (the pinned scripted-eval idiom)
prompt_ids = build_recall_prompt(tok, question)            # SHARED with the UI (D-18)
dump_context(question, prompt_ids, tok)                    # SC2 evidence + fact-absence SystemExit
idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
out = collect(model, idx, max_new_tokens=MAX_NEW_TOKENS,   # D-19 derived constant
              forbid_ids=forbid, stop_ids={8184, 8185}, greedy=True)
gen = out[0, len(prompt_ids):].tolist()
hit = normalize(tok.decode(gen)).find(normalize(fact.value)) >= 0
```

### The live toggle

```python
# Source: src/personacore/lora/inject.py:109-185 (verified)
def on_toggle(enabled):
    set_adapter_enabled(model, bool(enabled))   # 36 bool writes; OFF is bit-identical to base
    return f"memory: {'ON' if enabled else 'OFF'}"

def on_reset():
    eject_adapter(model)                        # one-way: wrappers removed, vanilla tree back
    return gr.update(value=False, interactive=False), "adapter deleted — restart to reload"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Adapt `W_q`,`W_v` only (LoRA paper) | Adapt all linear projections | QLoRA era | The project's six-projection allowlist is already current practice `[CITED: FEATURES §1]` |
| "Fine-tune the fact sentence" | Paraphrase-augmented SFT; accuracy rises with paraphrase count | 2023–2024 knowledge-injection work | DEMO-05's 20–50 per fact is above the ~10 saturation reported at 7B+ `[CITED: arxiv.org/abs/2404.00213, arxiv.org/abs/2312.05934]` |
| "LoRA forgets less, so it's safe" | LoRA at matched learning performance forgets comparably during knowledge injection | 2025–2026 empirical work | Justifies D-11.2's collapse control and D-15's replay arm rather than assuming safety `[ASSUMED — search-surfaced summary, primary text not read]` |
| Assume memorized facts generalize | LoRA memory capacity saturates as a function of rank; FFN/early-layer placement memorizes more | 2026 empirical analysis `[CITED: arxiv.org/html/2603.01097v4]` | Context for r=8 / 331,776 params holding 5–10 facts (comfortable); **not** a reason to change the locked target list |
| Assume bidirectional fact recall | Reversal curse: "A is B" does not yield "B is A" under fine-tuning | 2023, replicated since | Reversed forms must be *taught*, not held out (Pitfall 4) `[CITED: arxiv.org/abs/2309.12288]` |

**Deprecated/outdated within this repo's own planning docs:**
- ARCHITECTURE §Stage 3's **in-UI Teach tab** — closed on the merits by D-16.
- ARCHITECTURE §Stage 3's **"in-memory masked batches"** — predates the shipped masked-bin seam; `train()` has no in-memory masked path (Pattern 1).
- ARCHITECTURE's **"ship path = merge → export_slim"** — merging destroys the toggle; the demo path stays unmerged (LORA-04 / REQUIREMENTS §Out of Scope).
- ARCHITECTURE's `run_ab_forgetting.py` / DailyDialog references — superseded by Phase 11's D-00 (DailyDialog cut) and Phase 13's `finetune_ab.py`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | ~20–50 paraphrases/fact will suffice at 13.9M; the ~10 saturation figure is a 7B+ observation extrapolated downward | Pattern 5 | Recall misses thresholds; **mitigated by design** — D-09/D-14's calibration run exists to measure this rather than assume it |
| A2 | 331,776 trainable params (r=8) hold 5–10 facts without capacity collapse | Pattern 4 / State of the Art | If wrong, recall saturates low; rank is locked by LORA-01/Phase 9, so the response is honest reporting under D-12, not a rank change |
| A3 | ~100–300 deliberate-overfit steps is the right budget band (ARCHITECTURE §Stage 3) | Claude's Discretion | Under-training reads as capacity failure; over-training risks D-11.2 collapse. Calibration measures both arms |
| A4 | "LoRA at matched performance forgets comparably" — from a search-result summary, primary text not read | State of the Art | Only affects narrative emphasis; D-11.2 and D-15 measure collapse directly regardless |
| A5 | Gradio 5.50's default one-worker-per-event does not prevent cross-event interleaving on a shared global model | Pattern 7 / Pitfall 10 | If Gradio actually serializes all events, the `concurrency_id` is redundant (harmless); if it does not, omitting it produces the half-on/half-off failure |
| A6 | F4's finding (base cannot copy from context) generalizes beyond the 6 greedy probes run this session | Measured Findings / Pitfall 2 | If the base *can* sometimes copy in-context, D-11.1 succeeds and the report framing is simply unused — the prepared framing costs nothing |
| A7 | First-person teaching register outperforms second-person at this scale | F3 / Pitfall 1 | Untested head-to-head. The calibration run could carry a small register arm at near-zero cost — worth the planner's consideration |

---

## Open Questions (RESOLVED)

> All five were substantively resolved during the discuss and planning passes. Each carries its
> resolving decision or committed constant below; none is an open item entering execution.

1. **Teaching register: first-person persona vs second-person user-fact.**
   **RESOLVED — D-01** locks first person on the measured F3/F5 evidence; **D-21** adds the
   `cal_second_person` calibration arm and `teach_persona.first_person_wins` so the head-to-head
   is measured rather than asserted.
   - What we know: the base emits first person exclusively (F3); FEATURES §4's "move the persona from the prompt into the weights" framing supports first person; DEMO-05's wording says "user facts."
   - What's unclear: whether second person is merely harder or effectively unreachable at 331,776 params.
   - Recommendation: **choose first-person and say so in the plan**, framed as prompt→weights persona distillation. If cheap, add a register arm to the calibration run — but the register must be fixed before the calibration set is authored (D-14 requires calibration to mirror the real set's shape).

2. **What the D-11.1 fairness control claims when it fails.**
   **RESOLVED — D-20** pre-registers the three-part reconciliation plus its failure branch as
   committed report text in plan 14-10, before the run that produces the number.
   - What we know: F4 says it will probably fail.
   - What's unclear: whether a different in-context placement (multi-turn, longer warm-up, repeated statement) would succeed — 6 probes is a small sample.
   - Recommendation: run the control as locked, on the full final question set; pre-write the negative-result framing (Pitfall 2); record the measured in-context negative as a first-class finding, not a footnote.

3. **In-loop validation source for the teaching run.**
   **RESOLVED — plan 14-07** passes `val_bin=DIALOG_VAL_BIN` + `val_mask_bin=DIALOG_VAL_MASK`, so
   the in-loop curve IS the collateral-collapse signal; gates still use `masked_perplexity`.
   - What we know: `val_mask_bin` requires a `.bin` `val_bin`. Candidates: a held-out slice of the teaching corpus, or `dialog_val.bin`+mask.
   - Recommendation: use `dialog_val.bin`+mask so the in-loop curve *is* the collateral-collapse signal, giving D-11.2/D-15 a per-step trace instead of only endpoint numbers. Gate decisions still use the deterministic `masked_perplexity` sweep, never in-loop `val_loss` (Phase 12 12-02).

4. **How many decode seeds N for the k/N success rate.**
   **RESOLVED — plan 14-05** commits `N_SEEDED_SAMPLES = 8` and `question_seed(i) = SEED + i`.
   - What we know: D-10 requires greedy + N seeded samples; Phase 12/13 used a single seeded warm sample per transcript.
   - Recommendation: N in the 5–10 band with fixed per-question seeds derived from `SEED + question_index` so the whole run is re-derivable; commit the seed derivation. Cost is trivial (13.9M model, ≤ 64 new tokens).

5. **Whether the calibration run's replay arm uses PersonaChat bins directly or an interleaved mix.**
   **RESOLVED — plan 14-04** implements replay as a build-time concatenation ratio
   (`REPLAY_RATIO`) inside `build_bins`, leaving `train()` untouched.
   - What we know: D-15 requires a paired with/without-replay comparison on masked dialogue val PPL.
   - What's unclear: replay ratio and mechanism. `train()` takes exactly one `train_bin`, so replay means **concatenating a PersonaChat slice into the persona bins at build time** — a build-time ratio, not a loop change.
   - Recommendation: implement replay as a build-time concatenation ratio constant; it keeps `train()` untouched and makes the ratio an auditable committed number.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 venv | everything (3.14 system Python unsupported) | ✓ | 3.11.15 | — |
| `torch` | training + inference | ✓ | 2.7.1 | — |
| MPS backend | teaching/calibration runs | ✓ | `is_available() → True` | CPU (slower, still viable at 13.9M) |
| `numpy` | teaching bins | ✓ | 2.4.6 | — |
| `gradio` | DEMO-07 Blocks demo | ✓ | 5.50.0 | — |
| `pytest` | CPU suite (286 tests collected) | ✓ | 9.0.3 | — |
| `checkpoints/convbase_best.pt` | teaching run + guessability gate | ✓ | 278 MB, sha `04e724c`, step 4000 | — |
| `checkpoints/convbase_slim.pt` | demo + recall harness | ✓ | 55.6 MB, same trio | — |
| `artifacts/tokenizer.json` | everything | ✓ | frozen, 547 live ids | — |
| `data/dialog_val.bin` + `_mask.bin` | D-11.2 collapse metric, D-15 replay | ✓ | 1.28 MB / 638 KB | — |
| `data/dialog_train.bin` + `_mask.bin` | D-15 replay slice source | ✓ | 10.5 MB / 5.3 MB | — |
| `matplotlib` | not needed (Phase 15 owns figures) | ✓ | 3.10.9 | — |
| Disk headroom | checkpoints/bins | ✓ | 521 GiB free | — |
| `ctx7` CLI | documentation lookup | ✗ | — | WebSearch/WebFetch used instead |
| `slopcheck` | package legitimacy gate | ✗ | — | N/A — phase adds no packages |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `ctx7` (used WebSearch/WebFetch); `slopcheck` (no packages to check).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` → `[tool.pytest.ini_options]`, `testpaths=["tests"]`, `pythonpath=["."]` |
| Quick run command | `.venv/bin/pytest -q tests/test_phase14_*.py` |
| Full suite command | `make test` (`.venv/bin/pytest -q`) — 286 tests currently collected in 0.74 s |

The suite is **CPU-only and GPU-free by contract**; nothing here may require MPS or a checkpoint.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| DEMO-05 | Locked fact values keep their token census and byte-fallback round-trip (D-07; tokenizer half only, docstring states why guessability is not permanent) | unit | `.venv/bin/pytest tests/test_phase14_factset.py -x` | ❌ Wave 0 |
| DEMO-05 | Teaching episodes mask exactly the answer span + eos (golden fixture, target space) | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_answer_span_mask -x` | ❌ Wave 0 |
| DEMO-05 | Teaching bin length > `block_size + 1`; token/mask bins element-aligned | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_bin_shape -x` | ❌ Wave 0 |
| DEMO-05 | 5–10 facts taught into a LoRA adapter on the frozen base; base params bit-untouched | script proof (`raise SystemExit` canary, real weights, MPS) | `.venv/bin/python scripts/teach_persona.py` | ❌ Wave 0 |
| DEMO-05 | Fresh-process empty-prompt recall meets pre-registered thresholds; context dump proves no fact in context; base-without-adapter control fails closed-book | script proof + committed report | `.venv/bin/python scripts/phase14_recall.py` | ❌ Wave 0 |
| DEMO-05 | D-19 generation budget derivation + fit guard (pure function) | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_generation_budget -x` | ❌ Wave 0 |
| DEMO-06 | Taught and held-out family id sets are disjoint | unit | `.venv/bin/pytest tests/test_phase14_teaching.py::test_families_disjoint -x` | ❌ Wave 0 |
| DEMO-06 | No held-out question's id sequence is a contiguous subsequence of the teaching bin (token-level no-leakage) | unit (tiny synthetic bin) | `.venv/bin/pytest tests/test_phase14_teaching.py::test_no_token_leakage -x` | ❌ Wave 0 |
| DEMO-06 | Scoring normalizer + substring gate + mechanical contradiction detector behave as specified, incl. whitespace-fragment cases | unit (importlib-loaded driver) | `.venv/bin/pytest tests/test_phase14_scoring.py -x` | ❌ Wave 0 |
| DEMO-06 | Pre-registered thresholds are literal module constants in the committed driver | unit (importlib) | `.venv/bin/pytest tests/test_phase14_scoring.py::test_preregistration_constants -x` | ❌ Wave 0 |
| DEMO-06 | Taught vs held-out reported separately; all transcripts committed incl. failures | script output review | inspect `results/phase14_recall_report.md`, `results/phase14_transcripts.md` | ❌ Wave 0 |
| DEMO-07 | `personalize_demo.py`'s `forbid_ids` mask tensor equals `demo_app.py`'s (D-17) | unit (CPU, no gradio launch, no generation) | `.venv/bin/pytest tests/test_phase14_demo.py::test_forbid_ids_parity -x` | ❌ Wave 0 |
| DEMO-07 | UI token panel ids are byte-identical to the harness's committed dump for the same input (D-18) | unit | `.venv/bin/pytest tests/test_phase14_demo.py::test_prompt_ids_identical -x` | ❌ Wave 0 |
| DEMO-07 | `build_recall_prompt` ends at `<|assistant|>` and contains no fact substring; `generate_text_from_ids` streams cumulatively | unit (tiny GPT fixture) | `.venv/bin/pytest tests/test_recall_prompt.py -x` | ❌ Wave 0 |
| DEMO-07 | Adapter-off logits bit-identical to un-adapted base **on real weights** (D-11.3) | script proof, CPU | `.venv/bin/python scripts/phase14_recall.py` (control 3) | ❌ Wave 0 |
| DEMO-07 | Toggle enable/disable round-trip; eject returns vanilla tree; merged-module refusals | unit — **already green** | `.venv/bin/pytest tests/test_lora_toggle.py -x` | ✅ exists |

### Sampling Rate

- **Per task commit:** `.venv/bin/pytest -q tests/test_phase14_*.py tests/test_recall_prompt.py` (sub-second)
- **Per wave merge:** `make test` (full 286+ suite) **and** `make lint`
- **Phase gate:** full suite green + all four `results/phase14_*.md` artifacts committed + the D-06 blocking user verdict recorded, before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_phase14_factset.py` — covers DEMO-05 (D-07 permanent tokenizer census)
- [ ] `tests/test_phase14_teaching.py` — covers DEMO-05/DEMO-06 (mask fixture, bin shape, family disjointness, token-level no-leakage)
- [ ] `tests/test_phase14_scoring.py` — covers DEMO-06 (importlib-loaded scoring rules, thresholds, contradiction detector, D-19 budget)
- [ ] `tests/test_phase14_demo.py` — covers DEMO-07 (D-17 mask parity, D-18 prompt byte-identity)
- [ ] `tests/test_recall_prompt.py` — covers the two new package functions (G1, G2)
- [ ] No framework install needed — pytest 9.0.3 present and the suite is already green

**Not automatable in the CPU suite (script proofs with `raise SystemExit`, by design):** the guessability gate, the calibration run, the teaching run, the scored recall run, and all three D-11 controls. Each needs the 278/55.6 MB checkpoints and MPS; all follow the established `train_adapter_smoke.py` / `finetune_ab.py` proof register.

---

## Security Domain

The security surface of this project is **claim integrity + privacy + untrusted deserialization**, per PITFALLS §Claim-Integrity & Privacy Mistakes.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local single-user demo, `share=False`, localhost bind |
| V3 Session Management | no | No sessions; no persisted user state |
| V4 Access Control | no | No multi-tenant surface |
| V5 Input Validation | **yes** | `max_new_tokens` bounded `(0, 4096]` before the loop (T-06-04); D-19 floors the UI slider at the derived constant; `forbid_ids` masks all 7,645 dead ids so the strict decoder can never see an unknown id |
| V6 Cryptography | no | No secrets, no crypto — SHA-256 file digests are provenance, not security |
| V14 / Deserialization | **yes** | Every shareable artifact loads through `load_slim` / `load_adapter` with `weights_only=True` (restricted unpickler, zero code execution). Full checkpoints load `weights_only=False` **only** for the project's own trusted files, and that must be stated in each script's docstring |
| Network egress | **yes** | `GRADIO_ANALYTICS_ENABLED=False` set **before** `import gradio` (kills telemetry and the version-check ping), `analytics_enabled=False`, `share=False` — no tunnel binary download |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Pickle RCE via a foreign checkpoint/adapter | Elevation of Privilege | `weights_only=True` choke points; `weights_only=False` restricted to own-trusted files with a docstring stating so |
| Adapter loaded onto the wrong base | Tampering | `base_fingerprint` trio checked by `load_adapter`; key + shape audit before any tensor is copied (`load_adapter_weights`) |
| Dead-id sampling crash / DoS | Denial of Service | `undecodable_ids_mask` captured at build time (Anti-pattern 7); bounded `max_new_tokens` |
| Real personal data in a public repo | Information Disclosure | Synthetic/invented fact values only; `data/`, `checkpoints/`, `logs/`, `*.pt` gitignored; only `results/` markdown ships |
| Claim falsified by prompt leakage | Spoofing (of the novel claim) | Clean-room protocol: separate processes, id-space prompts, committed context dumps, `SystemExit` on any fact string found in a prompt |
| Silent "memory off" that is still on | Spoofing | `set_adapter_enabled` / `adapter_disabled` refuse on merged modules; D-11.3 measures bit-identity on real weights |
| Demo reaching the network | Information Disclosure | Analytics kill-switch ordering + `share=False`; the offline guarantee is a documented invariant of `demo_app.py` and must be duplicated verbatim |

---

## Sources

### Primary (HIGH confidence — first-party, verified this session)

- `src/personacore/lora/{layer,inject,config}.py` — `LoRALinear` identity gate, `scale` single source of truth, allowlist injection, toggle/eject/merge guards
- `src/personacore/checkpoint.py` — `export_adapter`/`load_adapter`/`load_slim` choke points, fingerprint semantics
- `src/personacore/dialogue/serialize.py` — `encode_dialogue` span-wise mask semantics (answer + eos = 1), `cap_persona` shared-source-of-truth precedent
- `src/personacore/training/{loop,data}.py` — `train()` data seams (no in-memory masked path), `get_batch_memmap_masked` target-space `-100`
- `src/personacore/continual/ewc.py` — `EWCPenalty` raises on fisher keys missing from `named_parameters()`
- `src/personacore/generation/{core,text}.py` — `collect`/`generate`, `stop_ids`, `undecodable_ids_mask`, cumulative-decode idiom, **string-only prompt wrappers (Gap G1)**
- `src/personacore/evaluation/perplexity.py` — `masked_perplexity` as THE frozen gate metric
- `scripts/{train_adapter_smoke,make_transcripts,demo_app,finetune_ab,prepare_dialog_corpus}.py` — the four templates this phase composes
- `tests/test_phase13_driver.py` — the `importlib` script-loading convention for pre-registered rules
- `results/{inflation_report,phase13_ab_report}.md` — the gated-report and pre-registration report registers
- **Live measurements (this session):** tokenizer census (19 values), `convbase_slim.pt` completions on 9 prompt configurations, `encode_dialogue` episode/mask shapes, base fingerprint trios, venv package versions, 286-test collection

### Secondary (MEDIUM confidence — literature, cross-referenced with in-repo research)

- [Injecting New Knowledge into LLMs via Supervised Fine-Tuning (arXiv 2404.00213)](https://arxiv.org/abs/2404.00213) — paraphrase augmentation drives QA generalization; token-based vs fact-based scaling
- [Fine-Tuning or Retrieval? (arXiv 2312.05934)](https://arxiv.org/pdf/2312.05934) — recall rises monotonically with paraphrase count
- [The Reversal Curse (arXiv 2309.12288)](https://arxiv.org/abs/2309.12288) — "A is B" fine-tuning does not yield "B is A"; persists across fine-tuning methods; in-context is the documented exception
- [Understanding LoRA as Knowledge Memory (arXiv 2603.01097v4)](https://arxiv.org/html/2603.01097v4) — rank-dependent memory capacity and saturation; FFN/early-layer placement memorizes more
- [Gradio queuing guide](https://gradio.app/guides/queuing) — `default_concurrency_limit=1`, shared `concurrency_id` semantics
- [Gradio state-in-blocks guide](https://gradio.app/guides/state-in-blocks) — variables outside a function are shared globally across users
- `.planning/research/{PITFALLS,ARCHITECTURE,FEATURES}.md` §11/§12/§14, §Stage 3, §4 — the converged v2.0 research this phase implements

### Tertiary (LOW confidence — flagged in the Assumptions Log)

- Search-summary claim that "LoRA at matched learning performance forgets comparably during knowledge injection" (A4) — primary text not read; D-11.2/D-15 measure this directly regardless

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — zero new packages; every version verified in the project venv
- Repo seams / integration: **HIGH** — every claim read line-by-line from shipped, tested code
- Base-model behavior (register, in-context copying, prompt shape): **HIGH** for what was measured, **MEDIUM** for generalization (9 prompt configurations, greedy)
- Architecture patterns: **HIGH** — each is an existing in-repo precedent, not a proposal
- Pitfalls: **HIGH** — 8 of 11 derive from measured facts or shipped-code guarantees
- Teaching recipe (paraphrase count, step budget, achievable recall): **LOW–MEDIUM** — literature is 7B+ scale; **this is exactly what D-09's calibration run is for, and the phase is already designed to measure rather than assume it**

**Research date:** 2026-08-01
**Valid until:** 2026-08-31 for the literature and Gradio findings (30 days, stable domain); the in-repo findings are valid until the code changes — the base-behavior measurements (F2–F4) are specific to `convbase_slim.pt` @ `04e724c` step 4000 and must be re-measured against any future base checkpoint (the same checkpoint-specificity D-07 names for the guessability gate).
