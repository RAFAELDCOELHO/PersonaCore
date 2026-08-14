---
phase: 16-weight-vs-prompt-persistence-control
verified: 2026-08-14T11:59:28Z
status: passed
score: 5/5 ROADMAP success criteria verified
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 5/5 (3 warnings escalated)
  verified_at_commit: 127d60dab7480c9ec3ac1ec347570b2a2051f159
  gaps_closed:
    - "W-1 — D-28's reading qualification is now attached to the report that cites the monotone permission (LADDER_ANOMALY_CAVEAT, emitted at write_persistence_report; `grep -i anomal` on the report: 0 -> 2 matches), pinned by a test proven to fail when the emit site is removed"
    - "W-2 — PERSISTENCE_REPORT_FRAMING no longer claims unqualified pre-registration; it names SWEEP_NO_BASELINE_CAVEAT and LADDER_ANOMALY_CAVEAT as the two exceptions, states both WEAKEN the report's claims, and discloses the arm-SHA / report-SHA split inside the report"
    - "W-3 — PERS-01 flipped to Complete in .planning/REQUIREMENTS.md (checkbox :49 and traceability row :189)"
  gaps_remaining: []
  regressions: []
  measurement_regression_check: "NONE. results/ diff between the arm commit e9b921a and 127d60d is 5 added / 1 removed line in the report text only; all four arm JSONs, the ladder report and both raw logs are byte-unchanged. The committed report was re-rendered in this verifier's process from the committed arm JSONs with the committed code and came out BYTE-IDENTICAL, provenance lines included."
warnings_closed:
  - id: W-1
    verdict: CLOSED (substance) — see residual R-1
    evidence: "results/phase16_persistence_report.md:263 renders LADDER_ANOMALY_CAVEAT directly beneath the D-28 permission (:261). Names `(2, 2)`, `(1, 2)`, `(1, 30)`; names the induction-head reading FALSIFIED; records the more conservative `span_5_synthetic` reading as declined by explicit decision, 'not an omission'. Every factual claim in it corroborated against results/phase16_ladder_report.md:55-60,106-107. tests/test_phase16_driver.py:1769 renders the report and asserts the caveat is IN the rendered text; mutation-proved: deleting the emit site from write_persistence_report flips that assertion to False."
  - id: W-2
    verdict: CLOSED
    evidence: "The unqualified clause 'committed to git BEFORE the run that filled it' is deleted. The replacement names both exceptions, states both WEAKEN the claims, and discloses the SHA split. Exhaustiveness verified independently: of the 20 long framing constants that write_persistence_report renders, `git log -S` dates exactly TWO after the arm-run SHA dc9d6c1 — SWEEP_NO_BASELINE_CAVEAT (8401515) and LADDER_ANOMALY_CAVEAT (127d60d). The other 18 are ancestors of dc9d6c1."
  - id: W-3
    verdict: CLOSED
    evidence: ".planning/REQUIREMENTS.md:49 `- [x] **PERS-01**` and :189 `| PERS-01 | 16 | Complete |`. Substance re-confirmed: 5a17920 is a git ancestor of e9b921a and of HEAD."
info:
  - id: I-1
    carried_forward: true
    concern: "Stale line citations in both committed reports, shifted by Phase 16's own additions to the cited file"
    detail: "`scripts/phase14_recall.py:1336 run_bit_identity_control` is cited in results/phase16_persistence_report.md:111,226,257 and the function now lives at :1413. NOT addressed at 127d60d; carried forward unchanged. The cited CLAIM is true and independently confirmed at results/phase14_recall_report.md:538."
  - id: I-2
    carried_forward: true
    concern: "A citable aggregate wall clock that cannot be reconciled against the four condition clocks printed above it"
    detail: "results/phase16_persistence_report.md:105 prints 'Citable four-arm wall clock: ~39 min' while the four printed condition clocks sum to 137.2 min, and claims the sweep's clock is 'reported separately' — no separate sweep clock is printed. WALL_CLOCK_NOTE is a pre-run constant (daac1f1). NOT addressed at 127d60d; carried forward unchanged."
  - id: R-1
    new: true
    concern: "D-28's note is attached as a faithful English rendering, not as the verbatim string, and is not read from `_CONTEXT_PATH`"
    detail: "D-28 (16-CONTEXT.md:276-279) says any report citing the permission 'MUST attach this note verbatim' and the note is written in Portuguese. `grep -c 'anomalias mecanicamente' results/phase16_persistence_report.md` = 0. LADDER_ANOMALY_CAVEAT is a hand-written English constant that carries all four elements of the note (two unexplained anomalies / induction-head FALSIFIED / conservative reading available / declined by explicit decision) and adds the measured basis. The report already embeds a verbatim Portuguese qualifier elsewhere (D-25 at :216, read from `_CONTEXT_PATH`), so the mechanism the original W-1 remedy named exists and was not used. Consequence: nothing ties the constant to 16-CONTEXT.md, so an amendment to D-28 would not surface as a test failure. Not escalated: the concern W-1 actually named — that a reader of the report alone never learns of the anomalies — is objectively closed, and the fix's own commit message quotes D-28's 'verbatim' wording, so the rendering was chosen with the requirement in view."
  - id: R-2
    new: true
    concern: "The new disclosure paragraph is itself post-run text, and its 'two exceptions' list does not name the constant that carries it"
    detail: "PERSISTENCE_REPORT_FRAMING was introduced pre-run (daac1f1) but its text was AMENDED at 127d60d, after the arms ran. It is the only framing constant modified rather than introduced post-run. The sentence 'All framing strings predate the run ... EXCEPT X and Y' is therefore literally inexact about the sentence making it — though the same paragraph says both additions were made 'at the human-verification checkpoint', so the amendment is self-evident to a reader. Same family: 'assembled ... after two report-generation fixes' counts 1b8e04a and 8401515 but not 127d60d, the commit that assembled the committed text."
  - id: R-3
    new: true
    concern: "The W-1 test's secondary assertion is no longer independently load-bearing"
    detail: "tests/test_phase16_driver.py asserts both `LADDER_ANOMALY_CAVEAT in text` and `'anomal' in text.lower()`. Mutation check: with the caveat's emit site removed, the first assertion fails (the pin holds) but the second still passes, because the W-2 framing paragraph also contains the word 'anomalies'. The primary assertion carries the entire pin. Cosmetic; the test does detect the regression it was written for."
---

# Phase 16: Weight-vs-Prompt Persistence Control — Verification Report

**Phase Goal:** Measure what memory-in-weights buys over prompting as a paired number with a bound
— four arms on the same committed question fixture, with the shared instrument's pairing defect
fixed first and the headline licensed by a capability ladder that runs *before* anything is scored.

**Verified:** 2026-08-14T11:59:28Z (re-verification) — supersedes the 2026-08-14T11:39:24Z pass
**Status:** passed — 5/5 success criteria VERIFIED, all 3 escalated warnings CLOSED
**Re-verification:** Yes — after warning closure at `127d60d`
**Method:** The persistence report was RE-RENDERED in this verifier's own process from the committed
arm JSONs using the committed driver, and compared byte-for-byte against the committed file. Every
headline number was recomputed independently. The new test was mutation-checked. No SUMMARY or
commit-message claim was accepted as evidence.

---

## Re-verification: Warning Closure

| ID | Claim under test | Independent evidence | Verdict |
|---|---|---|---|
| **W-1** | D-28's reading qualification now sits beside the monotone permission it qualifies | `grep -i "anomal" results/phase16_persistence_report.md` → **2 matches** (was 0): :263 the caveat, :101 the framing. :263 renders directly under `### Monotone degradation (D-28)` (:259) and immediately after the permission paragraph (:261). | **CLOSED** |
| W-1a | The caveat names the rungs | :263 contains `` `(2, 2)` ``, `` `(1, 2)` ``, `` `(1, 30)` `` — and those are exactly the two anomalies the committed ladder names at `phase16_ladder_report.md:106-107`. | ✓ |
| W-1b | The induction-head reading is named FALSIFIED | :263 — "An induction-head reading … was **FALSIFIED** by span 5 scoring 0 of 216 at both distances". Corroborated against the ladder table: `(5, 2)` = 0/216 and `(5, 30)` = 0/216 (`phase16_ladder_report.md:59-60`). | ✓ |
| W-1c | The conservative reading is recorded as DECLINED, not omitted | :263 — "A stronger, more conservative reading — … below `span_5_synthetic` — remains available and was NOT taken here: that is an explicit decision recorded before this run, **not an omission**." | ✓ |
| W-1d | A test pins the RENDERED REPORT, not the constant's existence | `tests/test_phase16_driver.py::test_ladder_anomaly_caveat_accompanies_the_monotone_permission` calls `_render()`, which invokes `write_persistence_report` into `tmp_path` and asserts the file content equals the returned text, then asserts the caveat is in it. **Mutation-proved:** a copy of the driver with the emit site deleted (constant kept) renders a report where `LADDER_ANOMALY_CAVEAT in text` is **False** → the committed assertion fails. | ✓ |
| W-1e | The factual content of the caveat is true | `(2, 2)` PASS at 15/216; `(1, 2)` FAIL at 1/216; `(1, 30)` FAIL at 3/216; `(5, 2)`/`(5, 30)` 0/216 — all read off `results/phase16_ladder_report.md:55-60`, which is byte-unchanged since 5a17920. | ✓ |
| **W-2** | The framing no longer claims unqualified pre-registration | The clause "committed to git BEFORE the run that filled it" is **deleted** (`git show 127d60d`). Replaced by a paragraph naming `SWEEP_NO_BASELINE_CAVEAT` and `LADDER_ANOMALY_CAVEAT` as exceptions. | **CLOSED** |
| W-2a | Both exceptions are stated to WEAKEN the claims | :101 — "Both **WEAKEN** what the report claims — one records that the flat sweep is uninformative, the other that the licensed rung came with unexplained anomalies — so neither was written to fit a number." | ✓ |
| W-2b | The exception list is EXHAUSTIVE | Independent AST + `git log -S` sweep of every long framing constant `write_persistence_report` renders: **20 constants, exactly 2 introduced after the arm SHA dc9d6c1** — `SWEEP_NO_BASELINE_CAVEAT` (8401515) and `LADDER_ANOMALY_CAVEAT` (127d60d). The remaining 18 (`GATE_FRAMING`, `MONOTONE_CLAIM_LICENSED`, `WALL_CLOCK_NOTE`, `WILSON_LABEL`, `HEADLINE_MECHANISM_CAVEAT`, …) are all ancestors of dc9d6c1. | ✓ |
| W-2c | The arm-SHA / report-SHA split is disclosed in the report | :101 — "the four arms were recorded at one git SHA and this report was assembled at a later one, after two report-generation fixes; NO arm was re-run and the arm JSONs are byte-unchanged". The arm SHA itself is printed at :10/:31/:52/:73/:94 (`dc9d6c1207a4f…`). The assembling SHA cannot be embedded without breaking the byte-reproducibility this report's tests rely on — the qualitative disclosure is the maximum achievable. | ✓ (see R-2) |
| **W-3** | PERS-01 marked Complete | `.planning/REQUIREMENTS.md:49` → `- [x] **PERS-01**`; `:189` → `\| PERS-01 \| 16 \| Complete \|`. Substance re-confirmed: `git merge-base --is-ancestor 5a17920 e9b921a` exit 0. | **CLOSED** |

### Measurement regression check — no number moved

The three fixes are textual by construction, and this is proved three independent ways:

| Check | Result |
|---|---|
| `git diff --stat e9b921a 127d60d -- results/` | `phase16_persistence_report.md \| 6 +++++-` — **one file, 5 added / 1 removed line**, both in prose |
| Arm JSONs, ladder report, both raw logs diffed across the same range | **empty** — byte-unchanged |
| **Re-render**: committed driver + committed arm JSONs → report text, in this verifier's process | **BYTE-IDENTICAL to the committed file**, provenance lines included. The report is a pure function of the committed data; nothing was hand-typed into it |

Independent recomputation from the raw arm JSONs (fresh process, importing the committed statistics):

| Quantity | Required to be | Recomputed | Match |
|---|---|---|---|
| `adapter-only` pooled, gated tier | 90/104, rate 0.865385, 936 draws | 90/104 = 0.865385, 936 draws | ✓ |
| `adapter-only` two-stage cluster bootstrap 95% | (0.721154, 0.971154) | (0.721154, 0.971154) | ✓ |
| Bootstrap brackets its own point estimate | all four arms | `0.721154 ≤ 0.865385 ≤ 0.971154` → True; True for all four | ✓ |
| `base-neither` / `embedding-cosine` / `prompt-stuffed` pooled | 0/104, Wilson 0.025355, rule-of-three 0.028846 | identical for all three | ✓ |
| Three cleared Holm pairs | p = 0.0078125 at alphas 0.0083333 / 0.0100000 / 0.0125000, all rejected | identical, signs `(1,1,1,1,1,1,1,1)` ×3 | ✓ |
| Three floor pairs | p = 1.0, not rejected | identical, signs `(0,…,0)` ×3 | ✓ |
| Seven sweep cells | 0/270 each, 2430 draws | 7 cells, all `n_answerable=0` of 270, 2430 draws; only the 320/448 cells `crosses_block_size=True` with 270/270 over-block and 270/270 statement-outside | ✓ |
| Arms are one comparison | 4 pids, 1 SHA, 270 records each | pids `[16115, 23448, 26135, 26193]`, `git_sha` set of size 1 (`dc9d6c1…`), 270/270/270/270 | ✓ |
| Sweep on one arm only | 1 | `len(sweeps) == 1` | ✓ |

**No number moved.**

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|---|---|---|
| SC1 | Ladder runs and is committed BEFORE any comparison is scored; `licensed_headline()` branches pushed before the run; CPU-only ancestry test | VERIFIED | `git merge-base --is-ancestor 5a17920 e9b921a` = true (DAG ancestry, not dates); `e9b921a` is an ancestor of HEAD, so no history was rewritten by the fix. `git log 5a17920..HEAD -- scripts/phase16_ladder.py` is **still EMPTY** — the ladder script remains frozen after the run it licensed. All 5 branches present incl. `no_rung_passed`. `test_phase16_prereg.py` uses `merge-base --is-ancestor`, pins the full 40-char SHA, and `23a830c` is still an ancestor of HEAD. |
| SC2 | Four arms, same 270 fixture questions, four fresh processes, paired by `seed_index`, parity columns published | VERIFIED | Re-confirmed by recomputation above: 4 arm JSONs × 270 records, **4 distinct pids**, **1 shared git_sha** `dc9d6c1`. `assert_arms_are_pairable` and `assert_arm_parity` are **CALLED** at `phase16_persistence.py:2830-2831` (shifted from :2800-2801 by the +33 lines this fix added) — and they ran in this verifier's own re-render, since `run_report_mode()` executes them before any statistic. PERS-05 fix (`item.seed_index`) untouched by this commit. |
| SC3 | Instrument integrity widened, never weakened; `assert_value_in_prompt` twin; every `draw_all` asserts; no skip mode | VERIFIED | Untouched by `127d60d` (which changed 4 files: the driver, its test, the report and REQUIREMENTS.md — not `phase14_recall.py` or `test_phase14_scoring.py`). Guard suite green in the full run below. |
| SC4 | Every rate ships denominator + bound; fact-level (n=8) cluster resampling; Wilson labelled; `3/n` at zero; no bare `0%`; exact sign test over 256 partitions, Holm over 6 | VERIFIED | Every number recomputed and matched exactly (table above). Two-stage bootstrap brackets its own estimate for all four arms. `grep "0%" results/phase16_*.md` → zero matches. |
| SC5 | PERS-03 on the prompt-stuffed arm alone; adapter gets the proof; base-neither and embedding-cosine not_applicable; truncation derived; no turns axis; monotone only if ladder off floor | VERIFIED (W-1 now closed) | `sweep` non-null on `phase16_arm_prompt-stuffed.json` only, `_prove(len(sweeps) == 1)` enforced and exercised in the re-render. 7 cells; truncation DERIVED (only 320/448 cross 256, 270/270 each). `applicability` = {adapter-only: proof, base-neither: not_applicable, embedding-cosine: not_applicable, prompt-stuffed: measured}. `monotone_claim_allowed("span_2")` → True. **The D-28 reading qualification that was missing now renders at :263.** |

**Score: 5/5 ROADMAP success criteria VERIFIED. 0 warnings open.**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `results/phase16_ladder_report.md` | PERS-01 blocking ladder, committed pre-comparison | VERIFIED | Committed once at 5a17920, byte-unchanged through `127d60d`. |
| `results/phase16_arm_{4 conditions}.json` | 270 records, 4 pids, 1 SHA | VERIFIED | Byte-unchanged across `e9b921a..127d60d`. |
| `results/phase16_persistence_report.md` | four-arm evidence + verdict + every mandated qualifier | VERIFIED | Re-render is byte-identical. Now carries the D-28 anomaly note (:263) and the disclosed pre-registration exceptions (:101). |
| `results/phase16_persistence_raw.log` | verbatim per-condition stdout | VERIFIED | Byte-unchanged. |
| `scripts/phase16_ladder.py` | pre-registered thresholds + `licensed_headline()` | VERIFIED | Still frozen since 5a17920. |
| `scripts/phase16_persistence.py` | four-arm driver, stats, sweep, report writer | VERIFIED | `LADDER_ANOMALY_CAVEAT` defined at :1817 and **emitted** at :2482; parity asserts wired at :2830-2831. ruff check + format clean. |
| `tests/test_phase16_driver.py` | pins the rendered report | VERIFIED | New test renders and asserts; mutation-proved to fail when the emit site is removed. |
| `.planning/REQUIREMENTS.md` | traceability for 12 IDs | VERIFIED | PERS-01 flipped; all 12 Phase-16 IDs now Complete except STAT-04, which correctly stays Pending until v3.0 close (Phase 18). |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `phase16_persistence.py` | `phase16_persistence_report.md` | `write_persistence_report` renders every framing constant | **WIRED (re-proved)** | Re-render from committed data is byte-identical to the committed file — the strongest available proof that the report is generated, not authored. |
| `MONOTONE_CLAIM_LICENSED` | `LADDER_ANOMALY_CAVEAT` | adjacent emit in the report body list (:2479-2483) | **WIRED (was the W-1 gap)** | The two now render as consecutive paragraphs; removing the second breaks the committed test. |
| `phase16_persistence_report.md` | `phase16_ladder_report.md` | headline = ladder's `licensed_headline` branch, cited by commit | WIRED | :280 cites branch `span_2` at `5a17920`, parsed by `_LADDER_VERDICT_RE` from the committed file. |
| `phase16_persistence.py` | `phase16_ladder.py` | `monotone_claim_allowed` reads `ladder.HEADLINE_BRANCHES` | WIRED | Import-time dependency; unchanged. |
| arm JSONs | report | `run_report_mode` → `assert_arms_are_pairable` + `assert_arm_parity` | WIRED | Both executed during this verifier's re-render; a broken arm set would have aborted it. |
| `phase16_persistence.py` | `16-CONTEXT.md` | D-25 qualifier read verbatim from `_CONTEXT_PATH` | WIRED | Still verbatim at report :216 (Portuguese, byte-compared by `test_report_carries_every_verbatim_clause`). **D-28's note does NOT use this path** — see R-1. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| `phase16_persistence_report.md` | pooled rates, p-values, bootstrap | `results/phase16_arm_*.json` via `per_fact_by_arm` | Yes — recomputed independently, exact match | FLOWING |
| `phase16_persistence_report.md` | ladder branch + statement | `results/phase16_ladder_report.md` parsed by `_LADDER_VERDICT_RE` | Yes | FLOWING |
| `phase16_persistence_report.md` | floor in both units | `results/phase14_recall_report.md:378` | Yes | FLOWING |
| `phase16_ladder_report.md` | 7 rung cells | run stdout → `phase16_ladder_raw.log` | Yes | FLOWING |
| sweep table | 7 cell rates + crop evidence | `phase16_arm_prompt-stuffed.json:sweep.cells` | Yes — 7 cells, 0/270 each, correct crossing flags | FLOWING |
| `MONOTONE_CLAIM_LICENSED` | D-28 permission text | module constant + `LADDER_ANOMALY_CAVEAT` | **Yes — the mandated note now renders beside it** | **FLOWING (was HOLLOW)** |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full suite green at the stated baseline | `.venv/bin/python -m pytest -q` | `578 passed, 1 skipped in 122.56s` (577 → 578: exactly the one new test) | ✓ PASS |
| The three report-qualifier tests | `pytest tests/test_phase16_driver.py -k "ladder_anomaly or sweep_no_baseline or verbatim_clause"` | `3 passed` | ✓ PASS |
| **Report is generated, not authored** | re-render from committed arm JSONs, diff vs committed | **byte-identical** | ✓ PASS |
| **W-1 pin is real** | driver copy with the emit site deleted → render | `LADDER_ANOMALY_CAVEAT in text` = **False** (committed assertion would fail) | ✓ PASS |
| W-1 pin's secondary assertion | same mutant | `"anomal" in text` = True via the framing paragraph — not independently load-bearing (R-3) | ℹ️ |
| Framing exception list is exhaustive | AST scan of the 20 rendered framing constants × `git log -S` vs `dc9d6c1` | exactly 2 post-run, both named | ✓ PASS |
| Ancestry guards after the fix | `merge-base --is-ancestor` for 5a17920→e9b921a, e9b921a→HEAD, 23a830c→HEAD | all exit 0 | ✓ PASS |
| Ladder branches still frozen | `git log 5a17920..HEAD -- scripts/phase16_ladder.py` | empty | ✓ PASS |
| STAT-04 dependency freeze | `git log 23a830c..HEAD -- pyproject.toml requirements.txt` | empty | ✓ PASS |
| `DEGEN-2` absent from code/tests (D-10) | `grep -rn "DEGEN-2" scripts/ src/ tests/` | 0 hits | ✓ PASS |
| `phase14_recall_report.md` unamended (D-19) | `git log -1 -- results/phase14_recall_report.md` | `a2bc82d 2026-08-02` — untouched across Phase 16 | ✓ PASS |
| Lint | `ruff check .` / `ruff format --check .` | `All checks passed!` / `148 files already formatted` | ✓ PASS |
| Working tree clean | `git status --porcelain` | only this untracked VERIFICATION.md | ✓ PASS |

**Probe Execution:** SKIPPED — no `scripts/*/tests/probe-*.sh` exist in this repository and no plan
declares one. The real-weights drivers were deliberately NOT re-run (artifacts committed, and the
re-render proves the report reproduces from them).

---

### Honesty Checks — the qualifications whose whole purpose is to survive editing

| Required qualification | Location | Status |
|---|---|---|
| D-30 two-mechanism caveat | `phase16_persistence_report.md:286` | PRESENT — unchanged by the fix |
| Declined `proxy_consistent` | `:284` | PRESENT |
| D-25 closed-set floor qualifier | `:214-218` | PRESENT verbatim (Portuguese), read from `_CONTEXT_PATH`, byte-compared by a test |
| PERS-03 flat zeros are uninformative, never "no effect" | `:247` | PRESENT with the exact required phrasing |
| Ladder names TWO monotonicity anomalies, claims no mechanism | `phase16_ladder_report.md:106-107` | PRESENT — exactly two, named |
| **D-28 note attached to the report citing the permission** | `phase16_persistence_report.md:263` | **PRESENT — W-1 closed** (substance complete; rendering not verbatim, R-1) |
| **Report's own pre-registration meta-claim** | `:99-101` | **QUALIFIED — W-2 closed**; exception list independently proved exhaustive |
| `phase14_recall_report.md` UNAMENDED (D-19) | git history | PRESENT |
| `DEGEN-2` nowhere in code or tests (D-10) | repo scan | PRESENT — 0 hits |
| Truncation `assert_value_in_prompt` caveat (pass ≠ in view) | `:249` | PRESENT |
| Arm-D soft-tier structural absence not dressed as a measured zero | `:182` | PRESENT |
| Wilson labelled as independence-assuming | `:178` | PRESENT |
| Draw unit labelled as forbidden for inference (T-16-26) | `:265-274` | PRESENT |

---

### Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| **STAT-01** | ✓ SATISFIED | Question is the unit; `cluster_bootstrap` accumulates `1 if k > 0 else 0`; draw counts labelled forbidden for inference. |
| **STAT-02** | ✓ SATISFIED | `report_proportion` emits rate + both denominators + Wilson; rule-of-three on every zero cell; zero `0%` matches. |
| **STAT-04** | ✓ SATISFIED (Phase-16 half) | `git log 23a830c..HEAD -- pyproject.toml requirements.txt` empty; correctly still `Pending` milestone-wide (closes at Phase 18). |
| **STAT-05** | ✓ SATISFIED | Every **gate** literal is pre-run (`licensed_headline` branches at 8f8d06e; `LADDER_CELL_PASS_K`, `SIGN_TEST_ALTERNATIVE`, `HOLM_FAMILY_PAIRS`, `COSINE_CHANCE_FLOOR`); the ladder script is frozen since 5a17920. The two post-run strings are **framing, not gates**, and are now disclosed in the report itself. |
| **STAT-06** | ✓ SATISFIED | `assert_family_closed` proves exactly 6 pairs enter, at runtime; replication and sweep carry no alpha. |
| **PERS-01** | ✓ SATISFIED | Ladder at 5a17920, a git ancestor of the arm-JSON commit and of HEAD; 7 rungs × 216 × 9 reproduce from the raw log. **REQUIREMENTS.md now marks it Complete (W-3 closed).** |
| **PERS-02** | ✓ SATISFIED | Identical 270-tuple question sets across four arms; pairing asserted at report assembly (executed in this verifier's re-render). |
| **PERS-03** | ✓ SATISFIED | 7 cells on the prompt-stuffed arm alone; truncation derived; overwrite on its own axis; weight arm covered by the bit-identity proof. |
| **PERS-04** | ✓ SATISFIED | Closed 20-value candidate pool, one forward pass, chance floor 0.05 proved at every call; explicitly not RAG. |
| **PERS-05** | ✓ SATISFIED | `item.seed_index` drawing, guarded; D-19 impact measured and reported. |
| **PERS-06** | ✓ SATISFIED | 71-file scan, hard equality vs a 2-entry allowlist, twin assert, dangling-entry check. |
| **PREREG-02** | ✓ SATISFIED | Ancestry-based CPU-only test; all three ancestry checks re-run green after the fix. |

**Orphan check:** `grep "Phase 16" .planning/REQUIREMENTS.md` maps exactly the 12 IDs the phase
declares. **No orphaned requirements.**

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` | — | **NONE** across all four files `127d60d` touched, and none in the report. |
| `results/phase16_persistence_report.md` | 111, 226, 257 | Stale `phase14_recall.py:1336` citation (now :1413) | ℹ️ Info (I-1) | Carried forward — not addressed at `127d60d`. Claim independently confirmed. |
| `results/phase16_persistence_report.md` | 105 | "~39 min" aggregate vs 137.2 min summed condition clocks | ℹ️ Info (I-2) | Carried forward — not addressed at `127d60d`. Pre-run constant. |
| `results/phase16_persistence_report.md` | 263 | D-28's note rendered in English, not the verbatim Portuguese string, and not read from `_CONTEXT_PATH` | ℹ️ Info (R-1) | Substance complete and corroborated; no test ties the constant to 16-CONTEXT.md, so a future amendment to D-28 would not surface as a failure. |
| `results/phase16_persistence_report.md` | 101 | The disclosure paragraph is itself post-run text and is not in its own exception list | ℹ️ Info (R-2) | Self-evident from the paragraph's own wording; no claim is strengthened by it. |
| `tests/test_phase16_driver.py` | 1782 | `assert "anomal" in text.lower()` also satisfied by the framing paragraph | ℹ️ Info (R-3) | Cosmetic; the primary assertion carries the pin (mutation-proved). |

---

### Human Verification Required

**None.** The three items escalated by the previous pass were decisions, and all three have been
made and implemented at `127d60d`; each was re-verified against the artifacts rather than against
the commit message. The remaining items are informational and none blocks phase close.

Optional, if literal compliance with D-28 is wanted (R-1): read the note from `_CONTEXT_PATH` the
way D-25's qualifier already is, and add it to `test_report_carries_every_verbatim_clause`'s
byte-comparison set. That would tie the report to the decision mechanically instead of by
authorship. It touches no measurement — the arm JSONs are byte-unchanged and the report
demonstrably regenerates identically.

---

## Gaps Summary

**No gaps. The phase goal is achieved and the three escalated warnings are closed.**

What was checked adversarially this pass, and what it showed:

- **The report was not hand-edited to look fixed.** Re-rendering it from the committed arm JSONs
  with the committed driver, in this verifier's own process, produced a **byte-identical** file.
  That also re-executed `assert_arms_are_pairable` and `assert_arm_parity` against the real arms.
- **No number moved.** The entire `results/` delta since the arm commit is 5 added and 1 removed
  line of prose in one file; all four arm JSONs, the ladder report and both raw logs are
  byte-unchanged. Independent recomputation reproduced 90/104 = 0.865385, the bootstrap
  (0.721154, 0.971154) bracketing its own estimate, the three cleared pairs at p = 0.0078125, the
  three floor pairs at p = 1.0, and all seven sweep cells at 0/270.
- **The W-1 fix is pinned, not decorative.** A driver copy with the emit site deleted renders a
  report that fails the committed assertion. And every factual claim inside the new caveat —
  `(2, 2)` passing at 15/216, `(1, 2)` and `(1, 30)` failing, span 5 at 0/216 on both distances —
  is corroborated against the committed ladder report, not against the CONTEXT prose.
- **The W-2 exception list is exhaustive, not asserted.** Of the 20 long framing constants the
  writer renders, `git log -S` dates exactly two after the arm-run SHA — the two the report names.
- **Nothing regressed.** Suite 578/1 skipped (exactly +1 for the new test), ruff clean, ladder
  script still frozen, Phase 14 report still unamended, `DEGEN-2` still absent, dependency freeze
  intact, all three ancestry guards green against the new HEAD.

Three residuals are recorded as information, none of which changes a number or a claim: D-28's note
is a faithful English rendering rather than the verbatim string and is not mechanically tied to
`16-CONTEXT.md` (R-1); the disclosure paragraph is itself post-run text and does not list itself
(R-2); the new test's secondary assertion is no longer independently load-bearing (R-3). The two
info items from the previous pass (stale `:1336` line citations, the unreconciled "~39 min" clock)
were not addressed and are carried forward unchanged.

**Recommendation:** close the phase.

---

_Verified: 2026-08-14T11:59:28Z (re-verification at `127d60d`)_
_Supersedes: 2026-08-14T11:39:24Z (`human_needed`, 3 warnings)_
_Verifier: Claude (gsd-verifier)_
