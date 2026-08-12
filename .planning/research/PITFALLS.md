# Pitfalls Research

**Domain:** Adversarial privacy / extraction auditing of a small (13.9M) from-scratch LM with weight-resident LoRA memory
**Researched:** 2026-08-12
**Confidence:** HIGH for repo-grounded pitfalls (read from `results/phase14_recall_report.md`, `scripts/phase14_*.py`, `.planning/RETROSPECTIVE.md`, `v2.0-MILESTONE-AUDIT.md`) · MEDIUM for literature-derived pitfalls (arXiv/USENIX/IEEE S&P sources listed at the bottom)

---

## The one finding that should reshape Phase 16

**PersonaCore has already measured its own in-context extraction ability and it is 1/1944 = 0.0005.**

`results/phase14_recall_report.md:378` — with each fact's own first-person statement placed
*directly in the `<|system|>` persona span*, the un-adapted base answered 1 of 1944 attempts.
The phase's own verdict text (`:587`) says it plainly: *"the base's in-context extraction is close
to non-functional independent of whether memory is present."*

Phase 16 is a weight-vs-prompt comparison. The prompt arm's outcome is therefore **already known
to be ~zero before the phase runs**, and it is zero for a reason that has nothing to do with
weights being better than prompting: at 13.9M parameters this model cannot do in-context retrieval
at all. A Phase-16 report that says "weights beat prompting, 0.49 vs 0.00" would be the single most
credibility-destroying sentence available in this milestone — a reviewer who reads
`phase14_recall_report.md` will find the number that invalidates it, in the project's own repo,
written by the project.

Everything in the Phase-16 section below follows from this. The honest headline is not "weights
beat prompting" but **"at this scale prompting is not a functioning memory mechanism, so the
comparison is a floor measurement"** — which is a *stronger* portfolio result, because it is the
kind of thing only someone who actually ran the control can say.

---

## Critical Pitfalls

### P16-1: The comparison is pre-rigged and the project already knows it

**What goes wrong:**
Phase 16 runs prompt-stuffed vs adapter-only, gets ~0.49 vs ~0.00, and publishes a mechanism
comparison. The prompt arm scored 0 because the model has no functioning in-context retrieval, not
because weights are a superior memory substrate. The claim is unearned and the counter-evidence is
already committed in this repo at `results/phase14_recall_report.md:378,587`.

**Why it happens:**
The result *looks* like the thesis. Confirmation is cheap; the D-11.1 fairness-control text is 400
lines deep in a Phase-14 report nobody re-reads while writing Phase 16. This is the project's own
recorded failure mode: *"stale requirement text is more dangerous than a missing requirement — it
reads as authoritative"* (RETROSPECTIVE, v2.0 Key Lesson 5) — here the inverse, a live limitation
that reads as finished business.

**How to avoid:**
1. **In-context capability ladder, as a blocking positive control.** Before the comparison runs,
   measure whether the prompt arm can do *anything*: (a) verbatim repeat at distance ~2 tokens
   ("The code is ZARF. The code is ___"), (b) same-turn retrieval, (c) persona-span retrieval at
   the true Phase-14 distance. Commit the ladder's prompts as module literals.
2. **Structural licensing.** `scripts/phase16_*.py` carries a module-level
   `licensed_headline(ladder) -> str` that returns the *comparative* claim only when the ladder is
   non-zero at some rung, and returns the *floor* claim otherwise. The report generator calls it;
   it does not accept a hand-typed headline. Watch it fail before trusting it (v2.0 pattern).
3. **Quote the 1/1944 prior in the pre-registration commit**, not in the results write-up — so the
   record shows the limitation was known before the number existed.

**Warning signs:**
The draft report contains "vs" between two numbers where one of them is 0. Any sentence of the form
"weights outperform prompting". The ladder was skipped as "obviously it can read its context."

**Phase to address:** **Phase 16** (blocking, before any comparison is scored).

---

### P16-2: Token-budget confound — the two arms are not the same experiment

**What goes wrong:**
The prompt-stuffed arm carries +N persona tokens the adapter-only arm does not. That changes
positional offsets, eats generation headroom against `block_size=256`, and changes which prompts
fit at all. Any difference between arms is then jointly attributable to "has the fact" and "has
60 more tokens".

**Why it happens:**
The arms are conceptually "same question, one has the fact" — the length difference is invisible
until someone asks why the adapter arm generated 40 tokens and the prompt arm 24.

**How to avoid:**
- **Length-matched distractor arm** (third condition): adapter-only *plus* a same-length
  **irrelevant** persona span. If the distractor arm matches the plain adapter arm, length is not
  a confound; if it does not, the whole comparison is length-driven.
- **Equalize the generation budget explicitly.** `phase14_recall.derive_recall_budget` /
  `PREAMBLE_HEADROOM` / `TAIL_HEADROOM` / `BUDGET_STEP` already exist — reuse, do not re-derive.
  Assert `max_new_tokens` identical across arms.
- **Structural assert:** `abs(len(prompt_ids_stuffed) - len(prompt_ids_distractor)) <= BUDGET_TOL`,
  raising `SystemExit` (not `assert` — this project already banned `-O`-strippable asserts in
  drivers, see `phase14_factset_gate.py` docstring).
- Publish per-arm context length in the results table as a required column.

**Warning signs:**
Arms have different `max_new_tokens`. No context-length column in the table. Any prompt truncated
in one arm and not the other.

**Phase to address:** **Phase 16.**

---

### P16-3: A prompt-arm "hit" that is the model's prior, not the context

**What goes wrong:**
The prompt arm answers "Rafael" and it is scored a hit — but the model emits "Rafael" for that
question regardless of what is in the persona span. The prompt arm is credited with reading the
context when it is reciting a prior.

**Why it happens:**
The symmetric mistake to P18-1. The adapter arm gets a negative control (Phase 14's 0/2430); the
prompt arm silently does not.

**How to avoid:**
**Counterfactual slot arm.** Run the identical prompt with a *different* value in the same slot. A
prompt-arm hit counts only if the answer tracks the swapped value. Report *slot-tracking rate*, not
raw hit rate. Reuse the existing D-02(b) base-guessability machinery in
`scripts/phase14_factset_gate.py` — it already prompts the un-adapted base with reserved probes.

**Warning signs:**
A prompt-arm hit rate above ~0 with no counterfactual arm. Values chosen for readability
("Rafael", "Lisbon") rather than for non-guessability.

**Phase to address:** **Phase 16.**

---

### P16-4: A privacy conclusion drawn from a capability comparison

**What goes wrong:**
Phase 16 measures *utility* — what memory-in-weights buys. The write-up then says something like
"and because the fact never appears in the prompt, it is private." Nothing in Phase 16 measures
extractability. This is a category error that reads as spin.

**Why it happens:**
The milestone is named "Adversarial Privacy Audit". Every phase inside it drifts toward privacy
vocabulary.

**How to avoid:**
**Banned-vocabulary lint on Phase 16's generated report.** A CPU-only test greps Phase 16's report
for `privacy|private|leak|secure|guarantee|cannot be extracted|protected` and fails. Phase 16 is
licensed to make availability and utility claims only; **Phase 18 is the only phase licensed to
speak about extraction**, and even then within P18-4's bounds. This mirrors the v2.0 pattern of
converting a declared invariant into a mechanism that fails loudly on every suite run.

**Warning signs:**
Privacy words appear in a Phase-16 draft. The phase summary conflates "not in the prompt" with
"not obtainable".

**Phase to address:** **Phase 16** (lint) — enforced for the whole milestone.

---

### P16-5: A question set authored after seeing what the adapter answers well

**What goes wrong:**
New questions are written for Phase 16 and, without anyone intending it, they favour phrasings the
adapter is known to handle. The comparison's question set becomes an unregistered degree of freedom.

**Why it happens:**
Phase 14's taught/held-out families are in the repo and their per-family rates are visible. Writing
"just a couple more natural questions" is a 10-minute task that quietly moves a headline.

**How to avoid:**
- **Reuse the frozen Phase-14 question families verbatim.** They were committed pre-run and
  calibrated on a *disjoint* set at `CALIBRATION_SHA 0425fdc4…`. Import them; do not retype them —
  the v2.0 "import the constant rather than retype it" rule.
- Any genuinely new question must pass the existing `phase14_factset_gate.py` guessability gate,
  and the gate report must be committed before Phase 16's comparison runs.
- **Prompt-identity assert:** outside the persona span, the token ids of the two arms' prompts must
  be *element-wise identical*. Phase 14 already records every scored prompt's ids before the model
  is called; extend that record, don't rebuild it.

**Warning signs:**
Any question added during Phase 16 execution rather than during Phase 16 pre-registration. A
question set whose size differs from Phase 14's.

**Phase to address:** **Phase 16.**

---

### P17-1: Personas that are not actually adversarial — the worthless green matrix

**What goes wrong:**
Three personas are generated, they differ in every slot, their names share no tokens, and the
off-diagonal is uniformly zero. The matrix is published as "perfect isolation" when it demonstrates
only that three unrelated facts are unrelated. This is the highest-probability way Phase 17 produces
a result that looks great and means nothing.

**Why it happens:**
Persona generators naturally produce *diverse* personas — diversity is the opposite of what an
isolation test needs. Adversariality has to be engineered, and "these are adversarial" is exactly
the kind of declared invariant this project has already been burned by.

**How to avoid:**
**A committed adversariality gate that runs and passes BEFORE any adapter is trained**, emitting
`results/phase17_adversariality_report.md`. Mechanical checks, each a hard `SystemExit`:
- **Slot collision:** for every persona pair, ≥1 shared slot with *different* values.
- **Name collision:** shared token prefix ≥ k ids, or bounded edit distance — measured on the
  frozen tokenizer's ids, not on characters.
- **Non-guessability:** every value passes the existing `phase14_factset_gate.py` base-guessability
  probe (a value the base already emits makes its column uninterpretable).
- **Representability:** every value round-trips `encode`→`decode` exactly and shares no token id
  with `undecodable_ids_mask` (see P18-5).

**Warning signs:**
The persona generator has a "make them distinct" step. No pair shares a slot. The adversariality
claim lives in a docstring rather than a report.

**Phase to address:** **Phase 17** (gate must precede adapter training).

---

### P17-2: The missing base row — off-diagonal zero compared against zero

**What goes wrong:**
`M[B][A's question] = 0` is read as "adapter B is isolated from A's fact". But the *base* also
scores 0 on A's question, because A's fact is unguessable by construction. Isolation was never
tested; unguessability was re-tested. This is structurally identical to the failure that produced
v2.0's 1/1944 question-fairness problem, where a closed-book failure could not be read as absent
memory.

**Why it happens:**
The matrix is conceptually N×N. The base is "not a persona", so it does not get a row, so nobody
ever computes the floor.

**How to avoid:**
- **Make the base literally row 0.** The matrix is (N+1)×N by construction, not N×N with a footnote.
  A test asserts `matrix.rows[0].label == "base (adapter off)"` and that the artifact has N+1 rows.
- **Gate on the excess, not the raw cell.** The reported isolation statistic is
  `M_ij − M_base,j`, with raw `M_ij` reported descriptively alongside.
- **State the ceiling too:** the informative content of the matrix is the *contrast*
  `M_ii ≫ M_ij ≈ M_base,j`. Without a high diagonal (P17-3) and a measured base row, a green matrix
  carries no information.

**Warning signs:**
The matrix is N×N. The word "isolation" appears next to a cell value with no base comparison. Every
cell in a column is zero including the diagonal.

**Phase to address:** **Phase 17.**

---

### P17-3: Isolation bought by under-training — a weak diagonal

**What goes wrong:**
Adapters 2, 3, 4 are trained with the recipe tuned for the *one* adapter this project has ever
trained (`persona_adapter.pt`). One of them under-trains, its diagonal lands at 0.08, its
off-diagonal is 0, and the matrix reads as isolated. It is an adapter that learned nothing.

**Why it happens:**
N=1 hyperparameter validation. PROJECT.md's own framing: *"Only one persona adapter was ever
trained."* LR/steps/λ that worked for one persona's fact distribution are assumed to transfer.

**How to avoid:**
- **Per-persona diagonal floor as a committed module literal**, derived by the *existing* rule
  (`max(THRESHOLD_FLOOR, round(rate * THRESHOLD_DISCOUNT, 4))`, `THRESHOLD_DISCOUNT = 0.60`)
  against Phase 14's 0.4921 — pushed before any adapter trains.
- **A failing diagonal makes that persona's row `INCONCLUSIVE`, never `ISOLATED`.** Encode this as
  a function in the driver (`row_verdict(diag, floor) -> str`) that the report generator must call;
  it cannot emit `ISOLATED` for a row whose diagonal is below floor.
- Report each adapter's training curve and final adapter norm alongside its row, so a weak diagonal
  is visible rather than inferred.

**Warning signs:**
Any diagonal below the floor. Diagonals varying by more than ~2× across personas. Nobody looked at
the new adapters' training loss.

**Phase to address:** **Phase 17.**

---

### P17-4: Scoring asymmetry between diagonal and off-diagonal cells

**What goes wrong:**
The diagonal is scored with the forgiving normalized/fuzzy matcher (whitespace-collapsed,
punctuation-stripped, hedging-tolerant — Phase 14's `_WHITESPACE_RE` / `_EDGE_PUNCT_RE` /
`HEDGING_RE` pipeline), and the off-diagonal ends up scored more strictly, or vice-versa. Isolation
is then an artifact of the scorer.

**Why it happens:**
Diagonal and off-diagonal are usually written as different code paths — "does it recall its own
fact" vs "does it leak someone else's" feel like different questions.

**How to avoid:**
**One cell-blind scorer, structurally proven blind.**
- The scorer's signature takes `(completion, target)` and **no `(i, j)` argument at all** — it is
  incapable of knowing which cell it is scoring. A test inspects the signature
  (`inspect.signature`) and fails if a cell/row/col/persona parameter is ever added.
- The driver records the scorer kwargs per cell into the artifact; a test asserts all
  `(N+1)×N` kwarg dicts are equal.
- A swap test: score cell (i,j) and (j,i) with the values exchanged and assert symmetric treatment.

**Warning signs:**
Two functions with "recall" and "leak" in their names. Any `if i == j:` in the scoring path.

**Phase to address:** **Phase 17.**

---

### P17-5: Seed variance mistaken for interference (and the reverse)

**What goes wrong:**
Sampling at `temperature=0.8, top_p=0.95` produces one off-diagonal hit out of 200. It is written up
as measurable cross-persona interference. Re-running with another seed produces zero. Or the reverse:
a real interference effect smaller than seed spread is declared absent.

**Why it happens:**
N=3-4 personas × one seed each is not a sample. The project already knows this failure class and
already handled it correctly once — v2.0 gated a correlation's *sign* and explicitly refused to gate
its *magnitude* at n=36.

**How to avoid:**
- **Deterministic per-cell generators**, `SEED + cell_index`, exactly the
  `make_retention_samples.py:8-14` discipline already in the repo — an early stop in one cell cannot
  shift another cell's stream.
- **Replicate the most collision-prone pair across ≥3 seeds** (already in PROJECT.md's plan) and use
  the diagonal's seed spread as the noise floor. Pre-register: *an off-diagonal effect smaller than
  the measured diagonal seed spread is reported as not-detectable, not as isolation and not as
  interference.*
- **Gate only the contrast that N supports.** Gate "diagonal exceeds base row"; report the matrix
  descriptively. **No aggregate "isolation rate %" over 9-16 cells** — that number would imply a
  precision N=3-4 cannot carry.

**Warning signs:**
A single-seed off-diagonal hit in the abstract. Any percentage computed across matrix cells. Greedy
decoding used for the diagonal and sampling for the off-diagonal.

**Phase to address:** **Phase 17.**

---

### P17-6: Shared teaching template contaminates the off-diagonal

**What goes wrong:**
All personas are taught with the same template. Adapter B, asked A's question, emits a plausible
slot-filler because the *template* taught it "questions of this shape get a name-shaped answer".
That is scored as leakage of A's fact when it is a template artifact — or, worse, it happens to
match A's value by chance and inflates apparent interference.

**Why it happens:**
The teaching pipeline is shared by design (it should be), so the template is a hidden common cause.

**How to avoid:**
- **A template-only control persona:** same template, a held-out value taught to *nobody*. Its
  column measures pure template-driven emission and belongs in the matrix as a labelled column.
- Score exact target match, and *separately* record "answered with a well-formed but wrong value"
  as its own category. A leak and a confabulation are different findings and must not share a cell.

**Warning signs:**
Off-diagonal completions that are fluent, correctly-shaped, and wrong. No distinction in the
artifact between "wrong answer" and "no answer".

**Phase to address:** **Phase 17.**

---

### P18-1: No negative control — "extraction" indistinguishable from the base guessing

**What goes wrong:**
The attacker asks the adapter-active model for the taught name, gets it, and the audit records a
successful extraction. But the un-adapted base emits the same common name for that prompt. Nothing
was extracted from the weights; a prior was elicited. This is the canonical error the memorization
literature was built to prevent (counterfactual memorization; Carlini's canary/rank framing).

**Why it happens:**
The adapter-active arm is the interesting one, so it gets run first and often alone. The base arm
feels like a formality.

**How to avoid:**
- **Every attack runs in both arms** — adapter off and adapter on — with *identical prompt token
  ids, identical seeds, identical budget, identical `forbid_ids`, identical `stop_ids`*. The driver
  should construct one prompt object and dispatch it twice, so divergence is impossible by
  construction rather than by review. Phase 14's toggle already proves adapter-off logits are
  bit-identical to the un-adapted base (max |diff| 0.0) — reuse that, it is the arm's validity proof.
- **The reported statistic is the differential**, `ASR_on − ASR_off`, with both arms published.
- **Target selection runs the D-02(b) guessability gate first** — `scripts/phase14_factset_gate.py`
  already prompts the un-adapted base with reserved probes before anything is taught. It exists;
  use it.

**Warning signs:**
Any extraction number reported without its adapter-off twin. Targets chosen for realism rather than
for non-guessability. The base arm run with a different sampling budget "because it wasn't finding
anything anyway".

**Phase to address:** **Phase 18** (and target selection in **Phase 17**).

---

### P18-2: Multiple attempts inflate success with no budget disclosure

**What goes wrong:**
The attacker gets 32 samples per prompt; success is "at least one sample contained the target". The
headline is 40%. A different paper's headline at 1 attempt would be 3%. The numbers are
incomparable, and if the base arm got fewer attempts the differential is meaningless.

**Why it happens:**
Sampling is free at this scale, so the budget drifts upward during exploration and whatever budget
was running when the good number appeared becomes the reported budget. The jailbreak-evaluation
literature documents 20-30 point inflation from generation budget alone.

**How to avoid:**
- **Attempt budget K is a module-level literal in a commit pushed before the run**, exactly the v2.0
  pre-registration discipline. Not a CLI default, not a notebook variable.
- **Report ASR@1 and ASR@K separately**, plus the cumulative-by-attempt curve. Never a single
  headline extraction number.
- **Identical K for both arms** — assert it in the driver, not in the write-up.
- Also report *unique* successes (a target extracted by 1 attack family vs 4 is a different finding).

**Warning signs:**
K appears only in the results file and not in a prior commit. Base arm K ≠ adapter arm K. A single
percentage described as "the extraction rate".

**Phase to address:** **Phase 18.**

---

### P18-3: The attack prompt leaks the answer (information injection)

**What goes wrong:**
A prefix-injection attack contains `"My name is Raf"` and the model completes `"ael"`. Scored as a
successful extraction, it is mostly the audit telling the model what to say. The unlearning-evaluation
literature quantifies this as an *information injection* problem — an optimized prefix can carry
enough bits to encode the answer outright, making the evaluation inconclusive.

**Why it happens:**
Prefix injection is a legitimate attack family; it *has* to put part of the target in the prompt.
The line between "attack" and "answer key" is a judgement call nobody wrote down.

**How to avoid:**
- **A declared per-attack-family injection budget**, committed before the run: how many characters
  / token ids of the target the prompt is permitted to contain. Zero for paraphrase and role-play;
  an explicit, small, pre-registered number for prefix injection.
- **Score only the unprompted remainder.** For prefix attacks the scored span is the target's
  *suffix beyond the injected prefix* — the discoverable-extraction convention.
- **A substring-aware guard, not exact-equality.** This is the exact bug that already bit this
  project: Phase 14's fact-freeness tests used exact-equality predicates and passed while the
  invariant was violated by a *substring* embedding. The audit trail is in `14-VERIFICATION.md` and
  the fix (`_strings_in`, depth-capped recursion; fresh-interpreter module scan) is in the repo.
  Reuse those, do not rewrite an equality check.
- **Record every attack prompt's token ids in the artifact before the model is called**, as Phase 14
  does, with the realized injection measured (not declared) per prompt.

**Warning signs:**
Any attack template containing a literal from the fact set that is not covered by a declared budget.
An injection check written as `target in prompt` on normalized strings only. Prefix attacks with
100% success.

**Phase to address:** **Phase 18.**

---

### P18-4: Declaring the system private because a weak attacker failed

**What goes wrong:**
Four hand-written attack families find nothing. The report says "no extraction was possible". A
failure to extract with a weak attacker is absence of evidence. The adversarial-robustness
literature's entire origin story is defenses that looked robust because the attack was bad, and the
privacy-auditing literature says the same thing formally: an empirical audit produces a *lower bound
on leakage*, never an upper bound on privacy.

**Why it happens:**
"We found nothing" is the comfortable outcome, and it is also the outcome you get for free by
attacking badly. There is no natural forcing function to attack harder.

**How to avoid:**
1. **A positive control that must reproduce.** The Phase-14 taught-template direct question is a
   *known-extractable* target at 0.4921. Run it as attack family zero. If it does not reproduce
   within a pre-registered band, the harness is broken and **no privacy statement of any kind is
   admissible from that run**. This is the single highest-value guard in Phase 18 — it converts
   "our attacks found nothing" from unfalsifiable into a testable claim about the attacks.
2. **A committed threat-model table, written before the run**, with two columns: *what the attacker
   has* (prompt access, the question set, knowledge of the persona schema, K attempts, sampling
   control) and **what the attacker does not have** — no gradients, no logits, no fine-tuning /
   relearning attack, no inspection of the 1.35 MB adapter file, no access to the pre-adaptation
   checkpoint. The relearning attack in particular is documented to recover ~88% of supposedly
   removed information; naming it as *not run* is mandatory, and it becomes the obvious Phase-19+
   follow-up.
3. **The report's conclusion sentence is templated from that table**, so the scope cannot silently
   widen between the driver and the prose.
4. Note the deeper asymmetry honestly: **black-box is the weakest threat model available here.**
   The adapter is a portable file; anyone holding it has white-box access, and v1.0 already shipped
   weights on a GitHub Release. A black-box audit says nothing about that adversary.

**Warning signs:**
The word "cannot" or "impossible" in a Phase-18 draft. All arms at zero including the positive
control. No list of attacks *not* run. The threat model appears in the results file rather than in
a prior commit.

**Phase to address:** **Phase 18.**

---

### P18-5: The 547-live-id tokenizer silently suppresses extraction

**What goes wrong:**
A target value tokenizes into a long byte-fallback sequence, or contains an id in the 7,645-strong
dead set that `undecodable_ids_mask` forbids at sampling time. The target is literally
unproducible. Extraction rate is 0. It is written up as privacy. It is tokenizer debt — the largest
known quality ceiling in this project, and explicitly out of scope for v3.0, which means it must be
*measured around*, not fixed.

**Why it happens:**
`forbid_ids` is threaded through every sampling path by design (CR-01, and finally into
`evaluate.py` at `3781a97`). It is invisible, correct, and it makes some strings unreachable. A zero
caused by masking is indistinguishable from a zero caused by absent memory unless someone checks.

**How to avoid:**
- **Hard gate at target selection:** every target's ids must (a) round-trip `encode`→`decode`
  exactly and (b) have **empty intersection with `undecodable_ids_mask(tok, vocab_size)`**. One
  `SystemExit`, run before anything is taught. The census machinery already exists in
  `phase14_factset_gate.py` (D-02(a)/D-04 tokenizer census).
- **Per-target token count is a required column** in the extraction report next to its rate.
- **The decisive one: for every target with zero extractions, record its teacher-forced NLL under
  the adapter.** This separates the two zeros that look identical:
  - low NLL (the model assigns the target high probability) + zero extraction ⇒ **the attack is
    weak / sampling never reached it** — a P18-4 finding, not a privacy finding;
  - high NLL ⇒ the target genuinely is not recoverable under this prompt distribution.
  Without this, every zero in the audit is uninterpretable.

**Warning signs:**
A target with an unusually high token count. Zero extraction across *all* attack families for one
target and normal rates for others. No NLL column.

**Phase to address:** **Phase 18** (measurement), **Phase 17** (target/persona-value selection).

---

### P18-6: `0/n` reported as `0%`

**What goes wrong:**
"0/240 extractions — 0% leakage." At n=240 the 95% upper bound is ~1.25%; at n=40 it is ~7.5%. `0%`
asserts a precision the sample cannot carry, and it is the exact form of claim a reviewer will
attack first.

**Why it happens:**
Zero is unambiguous-looking. Phase 14's `0/2430` was reported as a *count*, correctly — the risk is
that a smaller Phase-18 n gets reported as a *rate*.

**How to avoid:**
- **Rule of three**: for 0 successes in n trials the one-sided 95% upper bound is ≈ `3/n`. Report
  `0/n (95% upper bound p ≤ 3/n)`, never a bare `0%`. For non-zero counts use Clopper-Pearson
  exact intervals — the same discipline v2.0 applied to the Spearman CI.
- Put the helper in the committed driver and have the report generator call it, so the interval
  cannot be omitted by a writer in a hurry.
- Pre-register n. A small n is fine; an unstated n is not.

**Warning signs:**
Any `0%` or `100%` in a results table. A rate reported without its denominator. n chosen after the
first look at results.

**Phase to address:** **Phase 18** (and **Phase 17** for zero cells in the matrix).

---

### X-1: Availability sold as authorization

**What goes wrong:**
The Phase-14 toggle is described, or allowed to be read, as a privacy control. It is 36 boolean
writes on one model object in one process. Adapter-off logits being bit-identical to the base proves
the *off state is complete* — it proves nothing about who may flip it back. The adapter file sits on
disk; anyone with the process or the file has the memory. Calling that "privacy" is the claim most
likely to be attacked, and the milestone exists partly to say so out loud.

**Why it happens:**
The toggle demos beautifully. "Memory off" reads as "memory gone".

**How to avoid:**
- **Fix the honest framing in one committed sentence and reuse it verbatim everywhere:**
  *"The toggle controls **availability**, not **authorization**: when off, the adapter's effect on
  logits is exactly zero (measured, max |diff| 0.0), and when on it returns in full. Nothing about
  the off state prevents it being turned on. Only erasure would change that — which is why erasure
  is Phase 19+."*
- **Banned-claim lint across all v3.0-touched docs** (README, `docs/REPORT.md`, notebooks, the demo
  UI strings): fail the suite on `guarantee|provably|impossible|cannot be recovered|deleted|erased`
  unless the sentence is in a committed allow-list keyed to the artifact that supports it. Same
  shape as v2.0's structural guards; watch it fail before trusting it.
- Audit the **demo UI copy** too — the label next to the toggle is a published claim.

**Warning signs:**
"Memory off" / "forget me" / "deleted" in UI strings. The word "guarantee" anywhere near the toggle.
PROJECT.md's own line *"weight-based memory a privacy guarantee by design"* being carried forward
into v3.0 documents unqualified — v3.0 is precisely the milestone that must qualify it.

**Phase to address:** **Cross-cutting; lint lands in Phase 16, applies through 18 and the milestone
writeup. PROJECT.md's "privacy guarantee by design" wording should be re-read against v3.0's
findings at milestone close** (v2.0 Key Lesson 5).

---

### X-2: Pre-registration that only works in one direction

**What goes wrong:**
Gates are pre-registered for "extraction succeeds" (thresholds, margins). Then nothing extracts, and
the null result has no pre-registered validity conditions — so "we found nothing" is publishable
regardless of how bad the attack was. The pre-registration discipline that made v2.0 credible
silently fails to bind the *comfortable* outcome.

**Why it happens:**
Pre-registration templates are built for positive findings. Adversarial work inverts the incentive:
the null is the desirable outcome *and* the free one.

**How to avoid:**
**Pre-register admissibility, not just thresholds.** A committed
`null_result_is_admissible(run) -> bool` in the Phase-18 driver, returning `False` unless *all* of:
- the P18-4 positive control reproduced within its band;
- the pre-registered attack budget K was actually spent, per family;
- the adapter-off base arm was measured at the same K;
- every zero-extraction target has a recorded teacher-forced NLL (P18-5);
- every target passed the tokenizer-representability gate.

The report generator **refuses to write "no extraction observed"** when it returns `False`; it
writes `INCONCLUSIVE` instead. Both branches — `EXTRACTION FOUND` and `NO EXTRACTION (admissible)`
and `INCONCLUSIVE` — get their prose templates committed *before* the run, in the D-20 style Phase
14 already used for its pre-registered failure branch (`FAILURE_BRANCH` in `phase14_recall.py`).

**Warning signs:**
Only one verdict template exists in the driver. The pre-registration has thresholds but no
"conditions under which a null is meaningless" section.

**Phase to address:** **Phase 18** (with the same pattern applied to Phase 17's matrix verdict).

---

### X-3: Phase 19's go/no-go creating motivated interpretation of 16-18

**What goes wrong:**
Erasure is the exciting phase. Whether it is attempted depends on 16-18's numbers. Every ambiguous
result in 16-18 acquires a direction it "should" point, and the interpretation drifts — not through
dishonesty but through a hundred small framing choices made while knowing what the next phase needs.

**Why it happens:**
The decision is downstream of the data and the decider is the same person who produced the data.
This is the structural setup pre-registration exists for, and PROJECT.md already flags it.

**How to avoid:**
- **Commit `scripts/phase19_gate.py` before Phase 16's first run**, containing module-level
  literals and `should_attempt_erasure(m16, m17, m18) -> (bool, reason)`. It reads the committed
  artifacts and computes the decision. Nobody types the verdict.
- **Make that commit a hard precondition of Phase 16's plan**, not a note. v1.0's WR-04 ("regenerate
  the tokenizer before Phase 5") was prose in a verification report and became permanent debt;
  v1.0's `forbid_ids` warning crossed *two milestones*. The project's own Top Lesson 1:
  *"warnings need gates, not just records."*
- Pre-register the **erasure target** too: what erasure would have to beat (Phase 18's measured
  extraction rate; Phase 17's diagonal; Phase 16's retention/utility cost) — so Phase 19 cannot be
  declared a success against a bar invented afterwards.
- Note the literature's warning while writing that bar: unlearning that only suppresses output is
  routinely reversed by relearning/prompt attacks. An erasure claim gated on black-box
  non-extraction is the same absence-of-evidence error as P18-4, one phase later.

**Warning signs:**
The Phase-19 criteria are described in prose in PROJECT.md and nowhere in code. Any 16-18 number
being discussed in terms of what it "means for erasure" before it is committed.

**Phase to address:** **Phase 16 plan precondition** (gate file committed) · consumed at
**Phase 19 entry**.

---

### X-4: Verification and requirement artifacts rotting mid-milestone

**What goes wrong:**
Phase 16's VERIFICATION sits at `gaps_found` after the gaps are closed; Phase 17's VALIDATION status
cells keep plan-time marks; a requirement's wording outlives the decision that superseded it. At
milestone audit everything has to be re-verified from scratch. This is not hypothetical — it is
exactly what happened across v2.0 (50 stale status cells, a stale `gaps_found 55/57`, W2a).

**Why it happens:**
Metadata updates are the last thing before the next phase's first exciting thing.

**How to avoid:**
- **Re-stamp at phase close, in the same commit as the fix** — the v1.0 lesson ("keep checkbox state
  mechanical") re-confirmed by v2.0.
- **Specific v3.0 exposure:** the D-11.1 question-fairness limitation text will be quoted by Phase
  16 and Phase 18. Re-read it against whatever Phase 16 measures, and if Phase 16's ICL ladder
  changes what that limitation means, **append a dated continuation — never edit it in place**
  (v2.0's honest-negatives rule).

**Warning signs:**
Any VERIFICATION frontmatter whose status contradicts a green suite. A requirement naming a file
that a later decision moved.

**Phase to address:** **Every phase, at close** — make it a success criterion, not a habit.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip the Phase-16 in-context capability ladder ("obviously it can read its context") | Saves ~30 min | Publishes a mechanism comparison the repo's own 1/1944 refutes; the most attackable claim in the milestone | **Never** |
| Skip the base (adapter-off) arm in Phase 18 because "it never finds anything" | Halves attack runtime | Every extraction number becomes uninterpretable; identical to the failure the 1/1944 control exposed | **Never** |
| Reuse `persona_adapter.pt`'s hyperparameters for personas 2-4 without checking diagonals | No calibration run | Isolation bought by under-training; a green matrix that means nothing | Acceptable **only** with the P17-3 diagonal floor gate enforcing it |
| Author new Phase-16 questions instead of importing Phase-14's frozen families | Nicer-reading questions | Unregistered degree of freedom on a headline comparison | Only via the committed factset gate, pre-run |
| Choose persona values for realism rather than tokenizer-representability | Better demo copy | Silent zero-extraction from `undecodable_ids_mask`, read as privacy | **Never** — gate is one `SystemExit` |
| Report a single headline extraction rate | Clean abstract | Incomparable, budget-inflated, and unreproducible | Never; report ASR@1, ASR@K, and the curve |
| Let the attempt budget K settle during exploration | Faster iteration | Post-hoc budget = a threshold chosen after seeing the data | **Never** — K is a pushed literal |
| Describe the toggle as "memory off" in UI copy | Great demo line | Sells availability as authorization; the milestone's central honesty claim collapses | Never — allow-listed wording only |
| Defer Phase-19 criteria until 16-18 results exist | Feels sensible | Motivated interpretation of every ambiguous 16-18 number | **Never** — that is the entire point of X-3 |
| Skip re-stamping a VERIFICATION after gap closure | Saves 2 min | A full re-audit at milestone close (measured cost: v2.0) | Never |

---

## Integration Gotchas — reusing v2.0 mechanisms inside v3.0

There are no external services here. The integration surface is **v2.0's own machinery**, and the
project's Top Lesson 3 is *"fix all consumers, not the one that reported it."*

| v2.0 mechanism | Common mistake in v3.0 | Correct approach |
|----------------|------------------------|------------------|
| `undecodable_ids_mask` / `forbid_ids` | New Phase-17/18 sampling paths omit it (the exact bug that crossed two milestones in `evaluate.py`) | Every new generation call passes it; add each new driver to `tests/test_forbid_ids.py`'s consumer sweep |
| `LoRAConfig()` defaults at injection (audit item **W1**) | New multi-adapter loading in Phase 17 copies the defaults pattern; `alpha` drift applies deltas at the wrong magnitude **silently** — shapes match, so nothing raises | `LoRAConfig(**artifact["lora_config"])` at every call site. Fix W1 *before* Phase 17 multiplies the call sites from 2 to N |
| `build_recall_prompt` | Phase 16/18 hand-format attack strings instead of using the shared builder | Every scored prompt is a `build_recall_prompt` id sequence — the D-18 rule Phase 14 already enforces |
| Fact-freeness checks | Re-implemented as exact-equality; misses substring embedding (documented Phase-14 bug) | Import `_strings_in` / the fresh-interpreter module probe from the Phase-14 tests |
| `_verdict.recorded_verdict` | New drivers re-implement `text.split("## Verdict")[-1]` — the CR-02 bug, five times over | Import the one shared reader; it exists precisely for this |
| Adapter-off bit-identity (max \|diff\| 0.0) | Assumed to still hold once N adapters can be loaded into one process | Re-assert it per adapter in Phase 17; toggle × multi-adapter is a new state space (cf. `09-REVIEW.md` CR-01, toggle×merge state blindness) |
| Committed-artifact-only plotting (Phase 15 pattern) | Phase 17's matrix figure drawn straight from checkpoints | Extract once to `results/phase17_matrix.json`, plot only from it; reuse the AST-walk + fresh-interpreter no-torch guard |
| Committed figures (audit item **W4**) | New v3.0 figures again unpinned in CI | One assert per figure diffing the `tmp_path` regeneration against the committed PNG |

---

## Statistical & Scale Traps

Small-n traps, not throughput traps — the compute here is minutes on an M3.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Rate reported from a handful of trials | `0%`, `100%`, or a 4-decimal rate over <50 attempts | Rule of three for zeros (`p ≤ 3/n`), Clopper-Pearson otherwise; helper in the committed driver | Immediately at n < ~100; catastrophically at n < 30 |
| Multiple-attempt inflation | ASR climbs whenever the budget is raised | K pre-registered; ASR@1 + ASR@K + cumulative curve; same K in both arms | Any K > 1 |
| Multiple comparisons across the matrix / attack families | One cell or family is "significant" out of 16 | No per-cell significance claims; gate the contrast, report cells descriptively | N×N ≥ ~9 cells, or ≥4 attack families |
| Seed variance read as effect | An effect that vanishes on re-run | Deterministic per-cell seeds; ≥3-seed replication of the worst pair; effects below diagonal seed spread are not-detectable | N=3-4 personas, single seed |
| Aggregating heterogeneous cells into one number | "Isolation: 96%" | Forbid aggregate rates over the matrix; publish the matrix | Always at this N |
| Sampling-based extraction underestimating memorization | Greedy/low-K extraction reports zero for a target with low teacher-forced NLL | Record per-target NLL for every zero (P18-5); treat discoverable extraction as a lower bound | Whenever any target reports zero |

---

## Claim & Threat-Model Mistakes

The security failures available in this milestone are **claims**, not vulnerabilities.

| Mistake | Risk | Prevention |
|---------|------|------------|
| "Weight-based memory is private" as an unqualified claim | The whole milestone reads as marketing; a reviewer only needs the black-box threat model to dismantle it | A black-box audit lower-bounds leakage; it can never upper-bound privacy. Say it in the report, in the committed template |
| Toggle framed as access control | X-1; the demo's best moment becomes its weakest claim | Availability-not-authorization sentence, allow-listed and lint-enforced |
| Omitting the white-box adversary | The adapter is a 1.35 MB portable file; v1.0 already published weights on a GitHub Release | Threat-model table names white-box adapter inspection as explicitly out of scope and unmeasured |
| Omitting the relearning/fine-tuning attack | Literature reports ~88% recovery of "removed" information via finetuning on adjacent facts; not naming it looks like not knowing it | Name it in the not-run column; it becomes the natural Phase-19+ stress test |
| Real personal data in the fact set | `results/` ships publicly | Phase 14's T-14-05 rule already holds: no candidate value is real personal data. Re-assert for the N new personas |
| Erasure claimed from non-extraction | Suppression mistaken for removal — the dominant documented failure of LLM unlearning | Phase-19 bar pre-registered in X-3's gate file, and it must require more than black-box silence |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Toggle labelled "Memory off" / "Forget me" | Reader concludes the fact is gone; it is one boolean away | Label states availability: e.g. "Adapter: ON / OFF (weights unchanged)" |
| Multi-persona demo implying per-user isolation as a security property | Reads as multi-tenancy; the matrix measures behaviour, not a boundary | Present M_ij as a measurement with its base row visible, never as a guarantee |
| The extraction audit presented as a red-team pass/fail badge | Implies certification | Present as "what these four attacks, at this budget, found — and what was not attempted" |
| A green isolation matrix shown without the base row | Reader cannot tell trivial from meaningful | Ship the (N+1)×N figure; the base row is part of the visual |

---

## "Looks Done But Isn't" Checklist

- [ ] **Phase 16 comparison:** in-context capability ladder run and reported — verify the licensed-headline function was actually called by the report generator, and that it was watched failing.
- [ ] **Phase 16 arms:** length-matched distractor arm present; `max_new_tokens` asserted equal; context length is a published column.
- [ ] **Phase 16 prompt arm:** counterfactual slot-swap arm present; hits scored as slot-tracking, not raw match.
- [ ] **Phase 16 report:** banned-vocabulary lint green (no privacy words).
- [ ] **Phase 17 personas:** adversariality report committed *before* the first adapter trained; slot collisions, name collisions, non-guessability and tokenizer round-trip all mechanically checked.
- [ ] **Phase 17 matrix:** base is row 0 in the artifact; excess-over-base is the gated statistic; raw cells reported too.
- [ ] **Phase 17 diagonals:** every M_ii above its pre-registered floor, or that row is stamped INCONCLUSIVE by the driver (not by a human).
- [ ] **Phase 17 scorer:** signature verified cell-blind by test; per-cell kwargs asserted identical.
- [ ] **Phase 17 replication:** worst pair replicated ≥3 seeds; noise floor published; no aggregate isolation percentage anywhere.
- [ ] **Phase 18 controls:** adapter-off arm at identical prompts/seeds/K; positive control (Phase-14 direct question) reproduced within band.
- [ ] **Phase 18 budget:** K in a commit that provably precedes the run; ASR@1 and ASR@K both reported; base arm same K.
- [ ] **Phase 18 injection:** per-family injection budget declared pre-run and *measured* per prompt; scoring strips the injected span; the check is substring-aware.
- [ ] **Phase 18 tokenizer:** every target passes the representability gate; token counts published; every zero-extraction target has a teacher-forced NLL.
- [ ] **Phase 18 statistics:** no bare `0%`; rule-of-three / Clopper-Pearson bounds emitted by the driver.
- [ ] **Phase 18 verdict:** `null_result_is_admissible` exists, all three verdict templates committed pre-run, INCONCLUSIVE is reachable.
- [ ] **Cross-cutting:** `phase19_gate.py` committed before Phase 16's first run; threat-model table committed before Phase 18's first run; W1 (`LoRAConfig` defaults) fixed before Phase 17 multiplies its call sites.
- [ ] **Every phase at close:** VERIFICATION re-stamped in the same commit as the fix; PROJECT.md's "privacy guarantee by design" wording re-read against what v3.0 actually measured.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| P16-1 published before the ladder was run | **LOW** (minutes of compute) — but **HIGH** if the claim already shipped | Run the ladder; append a **dated continuation** to the report (never edit the original — v2.0 rule); reframe headline to the floor claim |
| P17-1 personas turn out non-adversarial after training | MEDIUM — N adapter retrains, minutes each | Regenerate personas through the gate; keep the original matrix as a labelled "non-adversarial baseline" — it is genuinely informative as a contrast |
| P17-3 a diagonal lands below floor | LOW | Stamp that row INCONCLUSIVE, report it, optionally retrain that persona with a *recorded, dated* hyperparameter change. Do not lower the floor |
| P18-2 K drifted during the run | MEDIUM | Re-run at the committed K. If the drifted run is kept, it is exploratory and must be labelled as such, outside the gate |
| P18-4 all arms zero including the positive control | LOW to diagnose, HIGH if published | Verdict is INCONCLUSIVE by construction. Debug the harness; a broken harness cannot produce a privacy result |
| P18-5 a target was unrepresentable | LOW | Re-select the target through the gate; publish the excluded target and *why* — a tokenizer-driven exclusion is an honest, interesting disclosure |
| X-1 an authorization claim already shipped | MEDIUM | Dated correction note in `docs/REPORT.md` + README + UI string change; the v2.0 precedent is that the report carries text now known to be wrong, corrected by dated note rather than by edit |
| X-3 Phase-19 criteria written after 16-18 | **HIGH — unrecoverable** | There is no fix. The gate file must precede Phase 16 |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification (how you know prevention worked) |
|---------|------------------|-----------------------------------------------|
| P16-1 pre-rigged comparison | Phase 16 | Ladder results in the committed artifact; `licensed_headline()` called by the generator; a test that feeds it an all-zero ladder and asserts the comparative claim is refused |
| P16-2 token-budget confound | Phase 16 | Distractor arm in the artifact; `SystemExit` on length mismatch, watched failing; context-length column present |
| P16-3 prompt-arm prior | Phase 16 | Counterfactual arm in the artifact; slot-tracking rate reported |
| P16-4 privacy claim from capability | Phase 16 (lint) | CPU-only test greps the generated report for banned vocabulary and fails |
| P16-5 unfair question set | Phase 16 | Question families imported (not retyped) from Phase 14; factset-gate report committed pre-run |
| P17-1 non-adversarial personas | Phase 17 | `results/phase17_adversariality_report.md` committed with a git timestamp preceding the first adapter checkpoint |
| P17-2 missing base row | Phase 17 | Artifact has N+1 rows; test asserts row 0 label and that the gated statistic is the excess |
| P17-3 weak diagonal | Phase 17 | Floor is a module literal in a prior commit; `row_verdict()` cannot emit ISOLATED below floor |
| P17-4 scoring asymmetry | Phase 17 | `inspect.signature` test proves scorer is cell-blind; per-cell kwargs equality asserted |
| P17-5 seed variance | Phase 17 | ≥3-seed replication in the artifact; noise floor published; no aggregate percentage (grep test) |
| P17-6 template contamination | Phase 17 | Template-only control column present; wrong-value confabulations recorded separately from leaks |
| P18-1 no negative control | Phase 18 (+17 target selection) | Both arms present per attack with asserted-identical prompt ids and K; differential is the reported statistic |
| P18-2 attempt inflation | Phase 18 | `K` literal in a commit preceding the run artifact; ASR@1, ASR@K, cumulative curve all present |
| P18-3 prompt leaks the answer | Phase 18 | Per-prompt *measured* injection recorded; substring-aware guard reused from Phase 14; scored span excludes injected prefix |
| P18-4 weak-attacker null | Phase 18 | Positive control reproduced within band; threat-model table committed pre-run; not-run attacks enumerated |
| P18-5 tokenizer suppression | Phase 18 (+17 selection) | Representability gate green; token counts published; NLL recorded for every zero |
| P18-6 `0/n` as `0%` | Phase 18 (+17 zero cells) | Interval helper called by the generator; grep test fails on a bare `0%` |
| X-1 availability vs authorization | Phase 16 lint → milestone writeup | Allow-list lint green across README / REPORT / notebook / UI strings |
| X-2 one-directional pre-registration | Phase 18 (pattern also in 17) | `null_result_is_admissible()` exists, is imported by the generator, and INCONCLUSIVE is reachable in a test |
| X-3 Phase-19 motivated interpretation | Phase 16 precondition | `scripts/phase19_gate.py` commit SHA precedes Phase 16's first result artifact |
| X-4 artifact rot | Every phase close | VERIFICATION status matches suite state at milestone audit with zero reconciliation needed |

---

## Sources

**Repo-grounded (HIGH confidence — read directly):**
- `results/phase14_recall_report.md:378,566-570,587` — the 1/1944 in-context control and its recorded limitation
- `scripts/phase14_factset_gate.py` — existing D-02(b) base-guessability gate + D-02(a)/D-04 tokenizer census (reusable for Phases 17 and 18)
- `scripts/phase14_recall.py` — pre-registered literals, `CALIBRATION_SHA`, `derive_recall_budget`, `FAILURE_BRANCH` (the pre-registered failure-branch pattern X-2 generalizes)
- `scripts/_verdict.py` — the CR-02 post-mortem on five copies of one fragile read
- `.planning/RETROSPECTIVE.md` — v1.0/v2.0 lessons: declared invariants, post-hoc thresholds, artifact rot, documented-not-scheduled, stale requirement text
- `.planning/milestones/v2.0-MILESTONE-AUDIT.md` — W1 (LoRAConfig defaults, silent alpha drift), W4 (unpinned figures), the Phase-14 exact-equality-vs-substring bug

**External literature (MEDIUM confidence — WebSearch-discovered, publication-checked, not Context7-verifiable):**
- Carlini et al., *The Secret Sharer* (USENIX Security 2019) — canary/exposure design, out-of-distribution canaries — https://www.usenix.org/system/files/sec19-carlini.pdf
- Carlini et al., *Quantifying Memorization Across Neural Language Models* (ICLR 2023) — discoverable extraction, counterfactual memorization, filtering "common" memorization — https://arxiv.org/pdf/2202.07646
- *Measuring memorization through probabilistic discoverable extraction* (NAACL 2025) — greedy single-sample extraction underestimates memorization; multi-attempt formalization — https://arxiv.org/pdf/2410.19482
- Carlini, Athalye et al., *On Evaluating Adversarial Robustness* (2019) — weak attacks make vulnerable systems look robust; adaptive-attack principle; evaluation checklist — https://nicholas.carlini.com/papers/2019_howtoeval.pdf
- Lukas et al., *Analyzing Leakage of PII in Language Models* (IEEE S&P 2023) — black-box extraction/inference/reconstruction game definitions; separating memorization from inference — https://arxiv.org/abs/2302.00539
- Deeb & Roger, *Do Unlearning Methods Remove Information from Language Model Weights?* (2024) — ~88% recovery via finetuning on adjacent facts; suppression ≠ removal — https://arxiv.org/abs/2410.08827
- *Existing LLM Unlearning Evaluations Are Inconclusive* (2025) — information injection via prompting and via finetuning; injection-budget disclosure; task-format sensitivity — https://arxiv.org/html/2506.00688
- Lynch et al., *Eight Methods to Evaluate Robust Unlearning in LLMs* (2024) — multi-probe evaluation, output vs logit vs probe disagreement — https://arxiv.org/pdf/2402.16835
- *Single-Configuration Attack Success Rate Is Not Enough* (2026) — generation budget inflates ASR 20-30 points; pre-select budgets, report per-attempt and cumulative — https://arxiv.org/pdf/2605.09070
- Privacy-auditing literature (e.g. *Debugging Differential Privacy*, one-run auditing line of work) — empirical audits lower-bound leakage; failing to find a violation does not prove the guarantee — https://arxiv.org/pdf/2202.12219
- Cohen et al., *Evaluating the Ripple Effects of Knowledge Editing* + *Pitfalls of Knowledge Editing in LLMs* (EMNLP Findings 2024) — locality/specificity failures, unintended alteration of non-target knowledge (Phase 17 and Phase 19 relevance) — https://arxiv.org/pdf/2307.12976 · https://aclanthology.org/2024.findings-emnlp.550.pdf
- Rule of three for zero events (one-sided Clopper-Pearson) — https://en.wikipedia.org/wiki/Rule_of_three_(statistics)

**Confidence notes:** the P16-1 finding, the reusable-gate identifications, and every "this already bit
this project" claim are HIGH — they were read from the repo, not inferred. The literature-derived
pitfalls (P18-2 budget inflation magnitude, the 88% relearning-recovery figure, injection-bit
estimates) are MEDIUM: single-source or search-summarized, cited for the *pattern* rather than the
exact number. No claim here depends on a specific external number being right.

---
*Pitfalls research for: adversarial privacy/extraction auditing of a small weight-memory LM*
*Researched: 2026-08-12*
