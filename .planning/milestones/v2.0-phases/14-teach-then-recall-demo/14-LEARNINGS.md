---
phase: 14
phase_name: "teach-then-recall-demo"
project: "PersonaCore"
generated: "2026-08-02"
counts:
  decisions: 12
  lessons: 12
  patterns: 12
  surprises: 10
missing_artifacts:
  - "UAT.md"
---

# Phase 14 Learnings: teach-then-recall-demo

The phase that had to make the project's central claim true rather than merely plausible:
a LoRA adapter recalls taught facts from an empty prompt in a fresh process, with the base
scoring exactly zero on the identical prompts. Most of what follows is about the machinery
built to keep that claim honest — and the places where the machinery itself was found wanting.

## Decisions

### Locked facts name IDs and resolve through the committed pools
`LOCKED_FACTS` et al. list fact **ids** and resolve them against `all_pools()` rather than
re-typing `Fact(...)` literals.

**Rationale:** Re-typing 38 four-field literals creates a second, silently divergeable copy of
every value/slot/tier. A mistyped `"marrowgate"` would seat a value the gate never probed and
nothing would catch it. With id resolution a typo is a `KeyError` at import. Pre-registration is
not weakened — the membership decision is still a committed literal list in git history.
**Source:** 14-03-SUMMARY.md

### Pre-registration is a committed literal plus git history, never a claim
`TAUGHT_THRESHOLD`/`HELDOUT_THRESHOLD` shipped as `None`; `CALIBRATION_DECISION_RULE` and the
D-20 reconciliation shipped as module-level constants **before** the runs they govern.

**Rationale:** `git log -S` on the constant is the proof, checked by a human at the
checkpoint. The rule was committed at `d7d7917` (01:52), 1h45m before the calibration run at
`0425fdc`; the D-20 framing at `48d557a`, 53 min before the scored run at `043bf4d`.
**Source:** 14-05-SUMMARY.md, 14-07-SUMMARY.md, 14-09-SUMMARY.md, 14-10-SUMMARY.md

### The soft tier is a separate constant, excluded mechanically rather than editorially
`LOCKED_FACTS` and `SOFT_TIER_FACTS` never concatenate before scoring.

**Rationale:** Low-cardinality slots (`favorite_color`) have real base prior mass, so their
close calls are structural. Keeping them in a separate constant means every pre-registered
threshold computes over the core tier alone by construction. Any harness that concatenates them
has broken D-05. Both retained soft facts carry their own quoted close call — the tier is
excluded because its own survivors demonstrate why, not on principle.
**Source:** 14-02-SUMMARY.md, 14-03-SUMMARY.md

### `normalize()` is duplicated rather than imported, and pinned by an equivalence test
The recall driver re-implements `phase14_factset.normalize_for_match`'s four-line composition.

**Rationale:** The import topology forbids reuse twice over — a module-level import leaks the
locked values into the demo process, and a per-call import leaks them on first call. So the
composition is duplicated and `test_normalizer_agrees_with_the_gate_normalizer` runs both over
six fixtures. Duplication that nothing pins is duplication that drifts, and a drifted scoring
normalizer would make the gate's verdict and the recall score answer subtly different questions.
**Source:** 14-05-SUMMARY.md

### `penalty_fn=None` is structurally forced, not preferred
EWC is switched off on the teaching path, with both reasons documented in place.

**Rationale:** (a) With the base frozen the EWC quadratic anchor is a constant, contributing
zero gradient while crediting EWC with retention that frozen-base LoRA produces by construction;
(b) `inject_lora` renames base params with a `.base.` infix while Fisher keys are vanilla-GPT
names, so `EWCPenalty.__call__` raises `ValueError` — a hard crash, not a silent no-op.
**Source:** 14-07-SUMMARY.md

### The negative register result is recorded unamended and does not reopen D-01
Second person measured 0.8045 held-out against first person's 0.5519 — a −0.2526 margin where
D-21 needed +0.10. `REAL_RUN_SECOND_PERSON` stayed `False`.

**Rationale:** D-12, verbatim. D-01's register lock rests on qualitative 14-RESEARCH F3/F5
evidence; this arm was designed to *supplement* the head-to-head D-01 lacked, not replace it.
Re-authoring the teaching register after seeing a number is exactly the move the pre-registration
block exists to prevent.
**Source:** 14-09-SUMMARY.md

### A wiring correction shows both numbers side by side and labels its projections
`lock_thresholds` had been fed the no-replay arm while `replay_required=True` selected the
replay config. The identical committed rule was re-applied to the matching arm.

**Rationale:** Replacing the old number silently is what makes a correction indistinguishable
from a threshold chosen to be cleared. Both sets appear in the report; the held-out threshold
lands on the pre-registered `THRESHOLD_FLOOR` (0.2000) rather than the discount's 0.1504 — the
floor doing the job it was committed for. The resulting margins are labelled **projections**,
because an arm cannot be independent evidence for a threshold derived from it.
**Source:** 14-09-SUMMARY.md

### The demo imports the harness's decode constants rather than holding its own
`DECODE_KW` contains no float literal of its own.

**Rationale:** The demo ran package defaults (`temperature=1.0`) while every committed number
was measured at 0.8/0.95 — the page and the report described two different systems. The demo
mirrors the **sampled** draw, not greedy, because 8 of 9 scored draws come from it and greedy is
the measured looping failure mode on this base.
**Source:** 14-09-SUMMARY.md

### The fairness control runs with the adapter DISABLED
D-11.1 places the fact in the persona span and asks the recall question adapter-off.

**Rationale:** The control exists to qualify the *closed-book* arm. Measuring the adapted model
— which already has the fact in its weights — answers a different question.
**Source:** 14-10-SUMMARY.md

### The real arm's adapter breaks the arm-scoped naming on purpose
`arm_outputs("real")` returns `checkpoints/persona_adapter.pt`, not `phase14_real_adapter.pt`.

**Rationale:** That is the path the harness (14-06) and the demo (14-08) already hardcode.
Calibration arms keep scoped names because they are disposable evidence. Left unfixed, a
successful teaching run would end with the harness reporting "missing adapter" and pointing at
the wrong cause.
**Source:** 14-07-SUMMARY.md

### The code was the outlier, so the code moved
`TRANSCRIPTS_PATH` pointed at `phase14_recall_transcripts.md` while 14-RESEARCH, 14-PATTERNS,
14-06-PLAN, 14-10-PLAN, 14-VALIDATION and 14-11's own verify block all named
`phase14_transcripts.md`.

**Rationale:** Six planning documents against one constant. The report's Clean-Room Evidence
section would have pointed a reader at a filename that does not exist.
**Source:** 14-11-SUMMARY.md

### The CDN strip is a middleware on a supported seam, not a template patch
`StripThirdPartyAssets` threads in via `launch(app_kwargs={"middleware": [...]})` and rewrites
the **rendered** response.

**Rationale:** The offending `<script>` is hardcoded in Gradio's `index.html` and Gradio exposes
no suppression knob (`head=`/`head_paths=` only append). Rewriting the rendered response assumes
nothing about template layout. Scope is limited to elements that *load* — anchors and `og:` meta
cost zero requests and are left byte-for-byte.
**Source:** 14-11-SUMMARY.md

---

## Lessons

### A hand-crafted fixture cannot catch a defect in the writer's own output
`assert_report_not_clobbered` misread its own freshly-written PENDING report as a recorded
verdict, because `SHIP_DECISION_HEADER` quotes `` `## Verdict` `` inside its own D-12 comment and
`.split("## Verdict")[-1]` landed in that prose. The existing test wrote a two-line fixture
instead of round-tripping the real writer, so it never saw it.

**Context:** CR-02. Consequence was a data-loss path: every legitimate re-drive aborted, leaving
`--force` — which disables the guard entirely — as the only way through. An operator who learns
`--force` is always required passes it after a human records a verdict.
**Source:** 14-REVIEW.md (CR-02), 14-VERIFICATION.md

### A guard rail whose predicate is too weak is not a guard rail
Two tests promised "no fact value in this process". `test_no_fact_strings_at_import` compared
whole strings for equality, so a taught value embedded in a 1,302-character constant was
invisible; `test_demo_process_is_fact_free` only asserted `sys.modules` membership, so a value
typed directly into a third module was outside its field of view. Both passed. Both invariants
were false.

**Context:** The value sat in `RECONCILIATION_A`, module-level report prose that the demo
transitively imported. No prompt path read it, so nothing user-visible was wrong — but the phase
asserts the invariant twice, and the structure backing it was absent.
**Source:** 14-VERIFICATION.md

### A CPU-only test suite cannot see a device-only bug
`complete_question` built `torch.Generator(device="cpu")` while `torch.multinomial` received
device-resident probs. On MPS that raises on the **first seeded draw of the first question**. The
whole suite is CPU-only, so it passed CI green and would have killed both the calibration run and
the real scored run at their first sampled token.

**Context:** Caught by a throughput benchmark before any arm ran, not by a test.
**Source:** 14-09-SUMMARY.md

### Structural unmeasurability is not measurement of zero
`F4` and `F5` showed `gain: 0.0` and were proposed for reallocation. Every question those
families generate names its own fact value, so the harness's `contains_value` filter drops all of
them — the gain is missing, not zero. A reader skimming the number would wrongly conclude
reversed-direction teaching failed.

**Context:** The report had to say so in the one place a refusal could land, because an
unrecorded refusal is a silently altered allocation.
**Source:** 14-09-SUMMARY.md

### A pre-registered boundary can be float-unsatisfiable
`replay_required(2.0, 2.2) is False` cannot hold under the naive formula: a 10% increase in
decimal reconstructs in binary as `0.10000000000000009`, strictly greater than the trigger — so
the boundary case trips a rule whose stated semantics are "the boundary does not trigger".

**Context:** The plan's own verify block asserted a result the formula could not produce. Fixed
with `RATIO_DECIMALS = 10`, six orders coarser than double noise and six finer than any effect
these gates resolve.
**Source:** 14-07-SUMMARY.md

### The mutation that models a leak is an overlap, not a move
The plan's negative control said to verify the leakage test by moving a held-out family into
`TAUGHT_FAMILY_IDS`. Doing exactly that leaves the suite **green, and correctly so** — a move
removes the family's questions from the never-seen split at the same time it adds them to the
corpus, so no leak exists to detect. The mutation that bites is adding `F7` to taught while
leaving it in held-out.

**Context:** The leakage tests' real teeth are against reserved probes leaking into taught
wording and W-04 cross-family nesting, not against allocation moves, which are self-consistent by
construction.
**Source:** 14-04-SUMMARY.md

### Literal source-grep acceptance criteria collide with the comments that explain them
Three separate times, a docstring or comment that correctly described the rule *wrote the
forbidden literal while doing so*: `grep -c "8186"` returned 1 because the docstring said "the
literal 8186 is never written here"; `grep -c "phase14_factset"` and `"cache_examples"` tripped on
explanatory comments; the collapse control's docstring named `estimate_loss` while the criterion
required zero occurrences.

**Context:** All three were reworded, no behaviour changed. A whole-file literal grep is a blunt
instrument that treats prose and code alike.
**Source:** 14-01-SUMMARY.md, 14-08-SUMMARY.md, 14-10-SUMMARY.md

### `sys.modules` is polluted by pytest collection order, not just by your module
`test_no_fact_strings_at_import` could not read a virgin `sys.modules`: another test file loads
`teach_persona` at **module scope**, and pytest imports every test module during collection, so
both names were resident before any test in the file ran.

**Context:** Fixed by popping both names, loading the driver inside the window, and restoring in
a `finally` — which makes the test measure the driver's own import topology rather than pytest's
collection order. Verified still red under a hoist of either edge.
**Source:** 14-05-SUMMARY.md

### A structural test can be blind to the thing it was written to prevent
`test_no_remote_stylesheets` asserts on `demo.stylesheets`. The actual offline violation was a
`<script src="https://cdnjs.cloudflare.com/...">` hardcoded in Gradio's template — a different
element type, structurally outside the assertion's reach. Only a live browser trace caught it.

**Context:** PROJECT.md requires the demo to run with no internet and privacy-by-design is the
thesis; a CDN hit on page load falsifies the claim on camera.
**Source:** 14-11-SUMMARY.md

### In Gradio, `.change()` fires on programmatic updates and `.input()` does not
Binding the memory toggle to `.change()` would have let `on_reset`'s `gr.update(value=False)`
re-enter `on_toggle`, overwriting the `MEMORY: DELETED` banner with `MEMORY: OFF` — claiming the
adapter was merely gated off when it had been ejected.

**Context:** Precisely the misrepresentation class 14-RESEARCH Pitfall 9 exists to prevent.
**Source:** 14-08-SUMMARY.md

### "Replay required" is not "replay solves it"
Replay at ratio 1.0 removed ~87% of the collapse and **still tripped the trigger** (+29.39%
against 0.10), while costing 0.27 of taught recall and 0.30 of held-out recall.

**Context:** The paired arm is the whole point of D-15 and it says both halves out loud. The
replay arm's held-out rate also sat *below* the threshold this same run derived from the
no-replay arm — applying both derivations as written produced a real run configured to fail its
own gate.
**Source:** 14-09-SUMMARY.md

### A guard passing and the artifact being clean are two different claims
`assert_no_value_in_prompt` guarded every prompt during the run. Separately, a script re-read all
540 committed `decoded :` lines and matched them against every locked and soft value: 0 leaks.

**Context:** The guard's silence and the artifact's content agree — but they had to be checked
independently to know that. The five-by-hand spot check remains the human's at the checkpoint; a
guard and a reader are different assurances.
**Source:** 14-11-SUMMARY.md

---

## Patterns

### Anchor a section read on the heading, never on the last occurrence of its literal
`re.compile(r"^## Verdict\b(.*?)(?=^## |\Z)", re.M | re.S)`, with `None` (no section at all)
distinguished from an empty body so the caller refuses rather than overwriting blind.

**When to use:** Any guard that reads a named section out of a document the same program writes.
Five copies of this read existed in the repo, four of them as naive `split(...)[-1]`; the idiom
now lives once in `scripts/_verdict.py`.
**Source:** 14-REVIEW.md (CR-02), quick task 260802-h3g

### Separate expensive measurement from cheap framing with a JSON dump
`dump_results` writes the measurements beside the report; `--rewrite-report` regenerates the
prose with no GPU, byte-stably.

**When to use:** Any long unrepeatable run whose report will need wording fixes. Without a
re-render path, a wording fix is either a re-measurement or a hand-edit of generated evidence —
and hand-editing an artifact whose purpose is auditability defeats the artifact.
**Source:** 14-09-SUMMARY.md

### Commit the framing before the run, and make `git log -S` the check
`REPORT_OPENER`, `RECONCILIATION_A/B/C`, `FAILURE_BRANCH`, `THREATS_TO_VALIDITY` are module-level
string constants.

**When to use:** Whenever a report will interpret a number that does not exist yet. A reviewer
can diff the framing independently of the numbers, and the git ordering proves the framing was
not composed after the result.
**Source:** 14-10-SUMMARY.md

### Guard a dangerous keyword argument by parsing the AST, not the source text
`test_persona_argument_is_scoped_to_the_fairness_control` collects every `build_recall_prompt`
call site tagged with its enclosing function and asserts exactly one passes `persona`.

**When to use:** When the docstrings legitimately discuss the dangerous identifier at length —
precisely because it is dangerous — so a source-text grep cannot distinguish prose from a call.
**Source:** 14-10-SUMMARY.md

### Prefer a mechanical filter to a hardcoded denylist when a later plan will rewrite the config
`build_question_sets` drops questions satisfying `contains_value(question, fact.value)` rather
than skipping `F4`/`F5` by name.

**When to use:** Any filter over a configuration a downstream plan is scheduled to change.
Hardcoding the family names would have broken silently when 14-09 rewrote the allocation.
**Source:** 14-06-SUMMARY.md

### Smoke-test the report writer on synthetic records before the long run
`write_recall_report` would otherwise first execute at the **end** of a multi-hour run, where a
`KeyError` in one table row costs the whole run rather than a red test.

**When to use:** Any artifact writer that only runs after expensive work. Render it end to end
into `tmp_path` on fabricated records covering both the healthy and the failure branch.
**Source:** 14-10-SUMMARY.md

### Verify the negative control — confirm the test goes red, then revert byte-clean
Done for the leakage tests (F7 overlap), for `test_no_fact_values_in_ui_chrome` (pasting a locked
value into `EXAMPLES`), and for both import-topology edges (hoisting each import).

**When to use:** Every test whose whole value is catching something that is currently absent. A
green test proves nothing until you have seen it red for the right reason.
**Source:** 14-04-SUMMARY.md, 14-05-SUMMARY.md, 14-08-SUMMARY.md

### Freeze a file with `git diff <PINNED_SHA> HEAD -- <path>` inside a permanent test
Not a working-tree `git diff --quiet`, which passes on a **staged** edit.

**When to use:** Any file a decision record says must not change. The test survives the phase.
**Source:** 14-08-SUMMARY.md

### One renderer for the committed evidence and the live UI, pinned by a byte-identity test
`render_context_dump` serves both the harness's committed dumps and the demo's token panel;
`test_prompt_ids_identical` asserts character-identical `ids` lines.

**When to use:** Whenever a UI claims to show what a measurement recorded. Two renderers is the
D-17/D-18 failure mode under a third name.
**Source:** 14-05-SUMMARY.md, 14-08-SUMMARY.md

### Name-scope every write target per arm and refuse before writing
`arm_outputs(arm)` plus `refuse_if_exists` on all five targets, with pairwise disjointness
CI-tested across all four arms.

**When to use:** Any multi-arm experiment writing adapters, CSVs, and checkpoints in one run.
Verified: re-running the real arm exits 1 naming all five paths.
**Source:** 14-04-SUMMARY.md, 14-07-SUMMARY.md

### Pin two files that must agree on the bare literals, not on `a.X == b.X`
`test_decode_settings_match_the_scoring_harness` asserts the literals `0.8`/`0.95`, the **exact
key set**, and that `**DECODE_KW` actually reaches the generation call.

**When to use:** Any cross-file coupling. `a.X == b.X` alone is a tautology that stays green when
both sides change together; asserting the literals forces both files to be looked at together.
**Source:** 14-09-SUMMARY.md

### Enforce a lazy cross-script import with a test, not a convention
`test_no_fact_strings_at_import` fails on a hoist of either the `phase14_factset` or the
`teach_persona` edge — verified red under both, not assumed.

**When to use:** When an import topology is load-bearing for a privacy or clean-room claim.
Prose in a docstring is not enforcement.
**Source:** 14-05-SUMMARY.md

---

## Surprises

### Second person beat first person on held-out recall by 0.25
0.8045 vs 0.5519, where D-21 needed +0.10 the other way.

**Impact:** Recorded unamended under D-12 and did **not** reopen D-01 mid-phase. Two caveats
carried: the arms score different fact sets (disjointness is required by D-21, so this is the
strongest head-to-head allowed, not a clean A/B), and the second-person arm also collapsed the
base worst of the three at +310.00%.
**Source:** 14-09-SUMMARY.md

### Teaching without replay collapsed the conversational base 22× past the trigger
+224.81% masked dialogue-val PPL against a `COLLAPSE_PPL_TRIGGER` of 0.10.

**Impact:** Not a marginal call. 200 steps at batch 8 × 256 over a 9,065-token corpus is ~50
epochs — the deliberate overfit the architecture prescribes — and it evidently overwrites
conversational competence along with installing the facts.
**Source:** 14-09-SUMMARY.md

### The question-fairness control came back essentially negative: 1/1944
The base cannot extract a fact even when that fact is sitting in its own persona span.

**Impact:** The most important thing for the human to weigh, and the pre-registered D-20
reconciliation anticipated exactly it: (a) a closed-book failure *in isolation* can no longer be
read as unambiguous evidence of absent memory; (b) the phase's claim rests on the
adapter-on/adapter-off **differential**, where the weakness is shared by both arms and cancels;
(c) the held-out rate is what separates knowledge-extraction from stimulus-response completion.
No new metric was introduced and no framing was authored after seeing the number.
**Source:** 14-11-SUMMARY.md

### The closed-book control was exactly 0.0000 — across 2,430 completions
Zero on all six calibration tiers too, across 3,276 closed-book completions.

**Impact:** The strongest possible form of the statement that the recall rates come from the
adapter. Same weights, same process, same per-question seeds, only the 36 LoRA `enabled` flags
differing.
**Source:** 14-09-SUMMARY.md, 14-11-SUMMARY.md

### Every proposed family move was refused — saturation arrived by an unpredicted route
14-07 predicted an unchanged allocation. It happened, but not because the measured families
saturated (they gained +0.65 to +0.70) — because two families are structurally unmeasurable by
this harness, and the W-03 paraphrase band refused both moves.

**Impact:** An upstream note that "at most one family (F6, 4 instances) can move" was off by one
step of arithmetic: 22 − 4 = 18, already below the `[20, 50]` floor. **No** family can move today.
The remedy, if calibration ever demands more held-out families, is to add paraphrase instances
first — a fact-set change, not a threshold to relax.
**Source:** 14-07-SUMMARY.md, 14-09-SUMMARY.md

### The demo page loaded a CDN script, caught only in a live browser after the measured run
`cdnjs.cloudflare.com/.../iframeResizer.contentWindow.min.js`, hardcoded in Gradio's template.

**Impact:** Fixed by middleware on the rendered response. Safe to record post-run because it
touched no measured artifact — the adapter, both evidence artifacts, both run logs, the
thresholds and `DECODE_KW` are untouched; the middleware sits on the HTTP response of a third
process that produces no number in the report.
**Source:** 14-11-SUMMARY.md

### 80 of 220 taught questions named their own fact value
`F5` is yes/no verification and `F4` is the reversed direction — naming the value is the
*definition* of both frames.

**Impact:** The run would have aborted on its **first** taught question. Suppressing the abort
instead would have scored questions that already contain the answer — measuring copying from
context, not memory in the weights, falsifying the claim at the moment it is demonstrated.
**Source:** 14-06-SUMMARY.md

### The 4.5737 / 4.5733 gap was the dead-id mask, not run-to-run noise
`teach_persona` called `masked_perplexity` without `forbid_ids`; the harness passed it.

**Impact:** Reproducible rather than stochastic, measured at +0.0083%, and it did not flip the
D-15 verdict. But both reports described the two call sites as "the same instrument" and one
added "**It is not a proxy**" — claims that were literally false. Fixed in `a2bc82d`.
**Source:** 14-11-SUMMARY.md, 14-REVIEW.md (WR-01)

### Adapter-OFF PPL came back identical to four decimals across three independently trained adapters
4.5737 on all three calibration arms, matching the Phase-12 frozen-base anchor.

**Impact:** A free cross-arm confirmation that `adapter_disabled` restores the pre-injection base
exactly. The closed-book pass paid for itself twice — it also supplied the baseline without which
a held-out rate is unjudgeable.
**Source:** 14-09-SUMMARY.md

### The base's failure mode was the generic non-answer, not a competing value
Across 256 core completions the base named a concrete alternative in the right slot only three
times. Its dominant behaviour is a generic non-answer (`i am a cop.`) — and all four genuine
guessability close calls landed in the low-cardinality soft slots.

**Impact:** The core tier passed the mechanical floor 38/38 with 0/16 containments. The 16→8 core
reduction is therefore a **composition** choice (one fact per slot), not gate attrition — and
filing those 8 trims alongside the 4 soft close calls in one table would have misreported the
gate as finding 12 guessability failures when it found 4.
**Source:** 14-02-SUMMARY.md
