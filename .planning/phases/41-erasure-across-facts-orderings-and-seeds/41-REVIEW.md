---
phase: 41-erasure-across-facts-orderings-and-seeds
reviewed: 2026-10-08T13:23:17Z
depth: deep
review_base: c271c67
files_reviewed: 2
files_reviewed_list:
  - scripts/phase41_prereg.py
  - tests/test_phase41_prereg.py
findings:
  critical: 1
  warning: 3
  info: 7
  total: 11
status: issues_found
---

# Phase 41: Code Review Report (pre-registration, before freeze)

**Reviewed:** 2026-10-08T13:23:17Z
**Depth:** deep (cross-checked against phase35_prereg fill/e1_stop/rules, phase40_prereg R-3 b readers, erasure_gate, phase19_erasure, phase36_ledger, and the Phase 35 ordering legs)
**Files Reviewed:** 2
**Status:** issues_found
**Stopping rule applied:** Rafael's Phase 35 rule. A finding is a BLOCKER only if it changes a read value or an emitted verdict in a real fill. Deliberate-bypass hardening is info.

All experiments ran with `.venv/bin/python` (3.11) at HEAD c271c67 with a clean `scripts tests results`
tree. `tests/test_phase41_prereg.py` was green at that HEAD: `58 passed in 4.03s`. Scratch scripts are in
the session scratchpad. No repository file other than this report was written.

## Summary

The fills, the census, the stop predicate, the R-3 b copy and the two fill-input builders all hold
up under direct experiment. In particular, `phase35_prereg.fill` accepts the builders' exact kwargs
on planted records (item 9). One verdict-changing defect is in condition (b): at the boundary,
float arithmetic reads an allowed move of exactly 8/27 as beyond the margin, and the real seed-1337
hometown baseline can reach that case. There are three warnings:
- condition (a) cannot fail at any judged stop, but nothing declares this;
- the frozen ENTRIES text does not state the D-17 counting unit;
- the calibration prefix places a training CSV where the Phase 35 ordering legs will count it.

### Items asked to examine, outcome

| # | Item | Outcome |
|---|---|---|
| 1 | Fill bindings, census, leg (a) composition | No finding. The file fills exactly `e1_checkpoint_grid`, `e1_alternative_ordering` and `e1_condition_b_margin`, and none of the three has a `results/phase41_*` input. The slot census accepts the `fill("slot", **builder())` form. |
| 2 | driver_stop vs e1_stop | No finding. The two are equal on all 63 complete sequences. On the 30 partial ones `driver_stop` returns None and `e1_stop` raises (test green). This matches D-09 and e1_stop's own refusal. |
| 3 | condition_b slots and baseline | Slot set and baseline are correct (7 = CORE_SLOTS minus the target; Phase 40 full of the same seed, through the same `_pooled_rows`). **Boundary arithmetic is wrong: CR-01.** |
| 4 | cell_verdict precedence, 5 keys | Precedence equals `erasure_gate.erasure_succeeded` (scripts/erasure_gate.py:221-227 and the no-delta branch). Every branch returns the fixed 5 keys. IN-05 covers the INCONCLUSIVE branch dropping failed conditions. **WR-01: (a) is vacuous.** |
| 5 | summary_counts with NOT_RUN | The code counts pairs, and CONTEXT supports pairs (see WR-02 for the example). The frozen ENTRIES text does not say so: WR-02. |
| 6 | varies_labels, D-28 | No finding. No exact 8/27 range reads below the margin, and pet_name is computed from the full group only (27, 26, 27, 25, 27). |
| 7 | R-3 b per unit, pause, resume | The R-3 b readers are a faithful seed→unit copy of phase40_prereg:1391-1572. The pause compares seconds. **IN-03: a stale declaration still lifts the pause.** |
| 8 | confirmation_failures(confirmations, reads=None) | IN-04. |
| 9 | floors/band builders vs phase35 rules | No finding. `fill("e1_condition_a_floors", **floors_fill_inputs())` and `fill("e1_condition_c_band_inputs", **band_fill_inputs())` both succeed on planted records in a temporary root. |
| 10 | GRID exemption | IN-07. |
| 11 | GRADIENT_HEADROOM, VALUE_NLL_SECONDS, 1.44 | There is no `1.44` / `1,44` in either file (grep exit 1). VALUE_NLL_SECONDS is computed. IN-01 and IN-02 cover the remaining issues. |
| 12 | D11_REFERENCE_* | No finding. The digest is read from the record, and the test proves the record is tracked and names the arm adapter. |

## Critical Issues

### CR-01: condition (b) reads an exact 8/27 move as "beyond the margin", which flips SUCCESS to FAILURE

**File:** `scripts/phase41_prereg.py:1043-1049` (`delta = post["rate"] - pre["rate"]`, `"beyond": abs(delta) > margin`)

**Issue:** ENTRIES["condition_b"] (:487) writes the rule as `|post rate - pre rate| <= E1_CONDITION_B_MARGIN`.
The margin is 8/27 (0.2962962962962963), so a move of exactly 8 of 27 questions must hold. The code
compares float differences of `n/27`. For 8 of the 20 (pre, post) pairs with |Δn| = 8, the
difference rounds to 0.29629629629629634 > margin, and those pairs read "beyond":
(7,15), (9,17), (11,19), (13,21), (15,7), (17,9), (19,11), (21,13).
A real baseline can reach one of them: seed 1337's intact full adapter has hometown = 21/27
(`results/phase40_a2_full_seed1337.json`), so any 1337 cell whose stop record reads hometown 13/27
gets FAILURE (b) instead of SUCCESS. Seed 2024's baselines (27, 27, 27, 27, 23, 16, 22, 26) hit
none of the pairs. `nontarget_damage` (D-19) inherits the misread.

The v3.0 pin has the same arithmetic (`phase19_erasure.nontarget_deltas` + `worst <= margin`), so
v3.0 would misread the same counts too. That convention is a defect, not a rule.

**Experiment:**
```
.venv/bin/python -c "import sys,json; sys.path[:0]=['scripts','src']; import phase41_prereg as p, erasure_gate
pre=p.record_rows(json.load(open('results/phase40_a2_full_seed1337.json'))); post={k:dict(v) for k,v in pre.items()}
post['hometown'].update(n_answerable=13, rate=13/27); post['pet_name'].update(n_answerable=0, rate=0.0)
b=p.condition_b(post,pre,'pet_name'); print(p.cell_verdict(stop=64,target_n=0,target_q=27,zero_results_have_nll=True,a={'holds':True},b=b,c={'holds':True}))"
```
Output: `hometown 21->13 (|dn| = 8 = margin x 27): FAILURE ['(b)'] ['hometown']`. The full sweep found
"exactly-8/27 moves read 'beyond' by condition_b: 8". The same check through the pin's arithmetic
printed `pin (b) on same counts: False`.

**Fix:** compare exactly, and keep the float delta for display only:
```python
from fractions import Fraction
margin_q = Fraction(margin).limit_denominator(phase19_erasure.N_TARGET_QUESTIONS)
_prove(float(margin_q) == margin, f"margin {margin!r} is not a ratio over N_TARGET_QUESTIONS")
...
exact = abs(Fraction(post["n_answerable"], post["n_questions"])
            - Fraction(pre["n_answerable"], pre["n_questions"]))
slots[slot] = {..., "beyond": exact > margin_q}
```
Add a test that plants hometown 21→13 on the real 1337 rows and asserts `holds is True`. Also apply
Fraction to `varies_labels` (`>=`) so both sides of the 8/27 boundary use one arithmetic (that side
is green today: 0 undershoots).

## Warnings

### WR-01: condition (a) cannot fail at any judged stop, but the prereg presents it as a test

**File:** `scripts/phase41_prereg.py:466-479` (ENTRIES["condition_a"]), `:1013-1020`, `:1098`

**Issue:** the stop requires a zero K = 48 count on the target's 27 questions (`stop_rule`, `e1_stop`).
So at every judged cell, `target_n = 0`, `upper = wilson_upper_bound(0, 27) = ERASURE_FLOOR_MIN`, and
`lock_erasure_floor` is `max(ERASURE_FLOOR_MIN, ...)` (scripts/phase19_erasure.py:929). (a) therefore
holds by construction, whatever the calibration rate. The four calibrations (~1.24 h MPS at
1120.33 s each) cannot change any verdict, and "(a)" can never appear in a cell's `failed` list.
This changes no verdict, so it is not a BLOCKER. However, the entry, D-12's side-by-side table and
the verdict all read as if (a) were a live gate, and nothing declares otherwise before the freeze.

**Experiment:** `min floor over all calibration rates n/23: 0.09107873950450847  wilson(0,27): 0.09107873950450847  (a) at a stop can fail: False`.

**Fix:** state it in ENTRIES["condition_a"] before the freeze: "at a judged stop target_n = 0, so (a)
holds by construction (floor >= ERASURE_FLOOR_MIN = wilson(0, 27)); the floor is published (D-12)
but cannot decide a verdict". Then prove it in `cell_verdict` (`_prove(a["holds"], ...)` when
`stop in GRID`), so a driver that passed a non-zero target fails loudly. Rafael may also want to
rule on whether the calibrations still earn their budget line.

### WR-02: D-17's counting unit is fixed only in a docstring; the frozen ENTRIES text leaves it open

**File:** `scripts/phase41_prereg.py:557-566` (ENTRIES["summary_line"]), `:1129-1147` (`summary_counts`)

**Issue:** the code counts PAIRS. Inside "não replicado", a pair counts once under each outcome
either seed carries, so the sub-counts overlap and need not sum to the label count. CONTEXT supports
this reading. Rafael's text (41-DISCUSSION-LOG:108) is "dos 8 pares, quantos em cada um dos três
rótulos, com INCONCLUSIVE e NOT_REACHED contados à parte dentro de 'não replicado'": the counting
unit of the sentence is pairs. 41-03-PLAN's action (:108) also says pairs. Its behaviour line (:93,
"per seed-verdict occurrence as the action states") contradicts the action it cites.

The defect is that 41-03-PLAN:108 requires the semantics to be documented "in the docstring and the
ENTRIES["summary_line"] derivation". Only the docstring has it. The derivation is still "D-17: a
pre-registered summary line with no threshold." The frozen written rule therefore admits both
readings, and they emit different numbers.

**Experiment (pairs (NR, NR), (INC, NR), six (S, S)):**
`code (pairs): 2 {'INCONCLUSIVE': 1, 'NOT_REACHED': 2, 'NOT_RUN': 0} sum of sub-counts = 3`;
`per seed-verdict occurrence: {'INCONCLUSIVE': 1, 'NOT_REACHED': 3, 'NOT_RUN': 0}`.
On the test's own 8 combos, pairs give {INC 2, NR 2, NOT_RUN 1} and occurrences give {INC 2, NR 3,
NOT_RUN 2}.

**Fix:** append to ENTRIES["summary_line"] value/derivation: "inside 'não replicado' each sub-key
counts PAIRS carrying that outcome at either seed (a pair counts once per sub-key; sub-counts may
overlap and need not sum to the label count)". Have Rafael confirm at 41-05, since the planner
default affects an emitted count.

### WR-03: the 'phase41' calibration prefix puts the training CSV where the Phase 35 ordering legs count it as a phase-41 record

**File:** `scripts/phase41_prereg.py:442-457` (ENTRIES["calibration"]: "a Phase 41 arm name and prefix 'phase41'"), `:738-748` (record_layout)

**Issue:** `teach_persona.arm_outputs('e1_calibration_seed1337', prefix='phase41')['csv']` is
`results/phase41_e1_calibration_seed1337/run.csv`. That path:
- is not gitignored (`git check-ignore` exit 1);
- matches `results/phase41_*`;
- is a declared input of no phase-41 slot.

The Phase 35 legs enumerate records with `git ls-files results/phase{owner}_*`
(tests/test_phase35_prereg.py:2489), and that pathspec reaches into subdirectories (it lists
`results/phase14_cal_first_person/run.csv`). The repo has tracked training CSVs before. If the
stage-1 commit includes this CSV, two things happen:
- leg (c) is red until the floors are filled;
- leg (a) is red permanently, because `phase41_floors_prereg.py` cannot strictly precede a record
  committed before it.

This is RESEARCH Pitfall 2, and `record_layout` names data/ for the raw arm and M1 but not for the
training CSV. Whether the driver commits the CSV is unverified (no driver yet). The mechanism itself
is demonstrated.

**Experiment:** `fnmatch(..., 'results/phase41_*')` → True; declared input → False;
`git ls-files 'results/phase14_*' | grep run.csv` → 3 tracked CSVs.

**Fix:** in ENTRIES["calibration"] / ["record_layout"], choose a prefix that `results/phase41_*`
does not match (`fnmatch('results/phase41cal_…', 'results/phase41_*')` → False), or state that
`arm_outputs` csv/bin/checkpoint paths are never committed and are moved under `data/phase41_e1/`.

## Info

### IN-01: GRADIENT_HEADROOM's text overstates the headroom slightly and is consumed by no rule

**File:** `scripts/phase41_prereg.py:227-234, 333-334`

**Issue:** 288/5 = 57.6 value NLLs per gradient (forward+backward) means backward ≤ 56.6 forwards
(printed `backward/forward ceiling = 56.599999999999994`), while CONTEXT D-05 says "~57×".
ENTRIES["d02_equality"] also adds a no-grad value NLL "at every gradient", which takes one more
value NLL out of each gradient's share: 56.6 for forward+backward, so backward ≤ 55.6×. Calibrations
re-rank 6 times (`rerank_points(..., calibration=True)` = (0, 16, 32, 48, 64, 128)) against
MAX_GRADIENTS_PER_CELL = 5, but calibrations are priced separately. Nothing reads GRADIENT_HEADROOM
(grep: only :232 and the derivation f-string), and the measured CPU ratio is 4.33×
(41-RESEARCH:259). No value changes.

**Fix:** reword it as "≤ 57.6 value NLLs per gradient step including D-02's no-grad check, i.e.
backward ≤ ~55.6× forward".

### IN-02: alternative_variant compares CPU-rehearsal seconds with an MPS-priced line and never records the ratio D-05 says the rehearsal measures

**File:** `scripts/phase41_prereg.py:1692-1707`

**Issue:** 417.56 s is an MPS price (`results/phase19_collateral_curve.json::device` = `mps`), and
`alternative_variant(cpu_seconds, mps_seconds)` compares CPU wall seconds with it. The research
measured CPU forward+backward at 24.8 ms, so 5 gradients take about 0.12 s and the CPU leg cannot
flip the variant. D-05's "the CPU rehearsal measures the backward/forward ratio" has no rule or
field here. This is a planner default and is unconfirmed.

**Fix:** record the ratio as a descriptive field, and label `cpu_seconds` as CPU-measured.

### IN-03: e1_pause_due accepts a stale declaration from any earlier or fabricated pause

**File:** `scripts/phase41_prereg.py:1877-1894` (41-04 deviation 3)

**Issue:** each declaration is checked against its own `e1_hours_at_pause`. Any approved declaration
listing a cell therefore lifts the pause for that cell forever, for example at a second pause for
an R-3 b rerun of that cell. **Experiment:** `stale declaration (hours 1.0, no such pause) lifts
pause at 60 h: True`. The driver's `resume_declaration_failures(notice)` call is the intended check,
so this is deliberate-bypass hardening.

**Fix (optional):** pass the current notice's `e1_hours` into `e1_pause_due` and require equality
there.

### IN-04: confirmation_failures / confirmation_hours leave fields unchecked and raise instead of returning

**File:** `scripts/phase41_prereg.py:1611-1681` (41-04 deviation 2)

**Issue:** `started_utc`, `finished_utc` and `record` are never checked: None passes, and `record`
is not proved to be `k48_record(...)`. `confirmation_hours` validates without `reads`. Given
malformed reads, the function raises SystemExit from `stop_readings` instead of returning failures.
**Experiment:** `confirmation with None utc/record accepted: True hours 0.001388888888888889`;
`confirmation_failures raised instead of returning: [phase41_prereg] read 0 at checkpoint 32: ...`.

**Fix:** check that the two utc fields are non-empty strings and that `record` matches
`RECORD_GLOB`. Either document the raise or catch it into a failure.

### IN-05: an INCONCLUSIVE cell_verdict drops failed (b)/(c) from `failed`/`beyond`

**File:** `scripts/phase41_prereg.py:1083-1097`

**Issue:** D-15 says each cell carries "every condition that failed". The INCONCLUSIVE branches return
`failed: [], beyond: []` even when the b dict has slots beyond. This matches erasure_gate's early
returns. The cell record must keep the full `b`/`c` dicts beside the verdict.

**Fix:** state that in record_layout.

### IN-06: test and copy looseness

**File:** `tests/test_phase41_prereg.py:1920` (`pytest.raises((SystemExit, KeyError))`, so a KeyError
regression would still pass); `scripts/phase41_prereg.py:2035-2042` (`relaunch_declaration_failures`
has no Mapping guard and raises TypeError on a non-mapping, copied from phase40_prereg)

**Fix:** use `SystemExit` only, and add the mapping guard that `dropped_manifest_failures` has.

### IN-07: limits of the GRID exemption and prose numbers

**File:** `tests/test_phase41_prereg.py:494-500`; `scripts/phase41_prereg.py:295, 388, 468, 483`

**Issue:** `_without_grid` blanks the whole GRID statement's lines, so any value placed on the same
physical line (`;`) or inside the GRID expression escapes the scan (deliberate bypass). Derived
counts appear typed inside ENTRIES prose ("216 questions", "27", "/27"). String content is not
scanned, and no value is read from it.

**Fix:** optional. Also assert that the GRID node is a Tuple of int Constants and that its line
holds one statement.

---

## NOT VERIFIED

- Whether the future driver commits the `results/phase41_e1_calibration_seed*/run.csv` file (WR-03
  trigger). No driver exists.
- MPS behaviour of any rule (no MPS run). D-02 equality on MPS is open (RESEARCH A1).
- How likely the CR-01 trigger (1337 hometown landing on exactly 13/27 at a stop) is. The trigger
  is reachable; its probability is not measured.

_Reviewed: 2026-10-08T13:23:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

---

## Resolution (2026-10-08)

Rafael's reply at the 41-05 checkpoint, 2026-10-08, verbatim:

```text
CR-01: corrigir como recomendado, estendido. Toda comparação de taxas de contagem da Fase 41 é exata, com Fraction sobre as contagens inteiras: a condição (b), o rótulo do D-19 e o "dentro/fora da faixa" do D-18. O float fica só para exibição. A margem exata é recuperada do valor commitado (a Fraction de denominador 27 cujo float é igual ao commitado, com asserção), nunca digitada. Um empate exato em 8/27 passa, pela regra ≤. Teste com os quatro pares medidos (15→7, 17→9, 19→11, 21→13).
Nota, sem reabrir nada: conferi nos registros commitados que nenhuma leitura cai num desses empates de um jeito que o float mude. No E5 não há empate; no E6 há um só (person_name k8, 26→18), em que float e conta exata concordam; na Fase 40 as diferenças do adendo são 7, 14, 11, 6 e 12; no v3.0 os deltas do M2 são 7/27 e 3/27 e a falha do M1 não depende de empate. A nota entra no relatório do milestone.

WR-01: como recomendado. As quatro calibrações ficam. A entrada diz que (a) é vazia no ponto de parada julgado, com asserção em cell_verdict. O relatório do milestone registra isso como achado sobre o desenho do portão: a regra de parada já implica (a), e as calibrações (1,245 h) alimentam só o D-12.

WR-02: contar pares, escrito em ENTRIES["summary_line"]. Os três rótulos somam 8. Dentro de "não replicado", cada par aparece uma única vez, sob a combinação dos vereditos das duas seeds (por exemplo "SUCCESS + NOT_REACHED"), para as subcontagens somarem o total sem dupla contagem. NOT_RUN entra como um valor de veredito nessas combinações.

WR-03: como recomendado: entrada no .gitignore para o diretório do CSV de calibração, com um teste de que ele é ignorado.

IN-01: corrigir o texto como recomendado.
IN-02: limitação conhecida; o registro diz qual medição (CPU ou MPS) decidiu a variante.
IN-03, IN-04, IN-06, IN-07: limitações conhecidas.
IN-05: corrigir: um INCONCLUSIVE preenche as listas de condições e de não-alvos que falharam, como o D-15 pede.

Desvios do 41-04: confirmo os três; o terceiro como limitação conhecida (é o IN-03).

Padrões do planner: aceito os nove. No d02_equality, a igualdade é exercitada no smoke do MPS antes de qualquer registro, para uma diferença sistemática aparecer antes da rodada e não no meio dela.

reviewed
```

Each finding was treated as a hypothesis and reproduced before any fix (CR-01: the review's
experiment printed `FAILURE ['(b)'] ['hometown']` at c271c67 and `SUCCESS` after 2b0a2e8). Each fix
is its own commit, tests written first and seen RED.

| Finding | Ruling | Outcome |
|---|---|---|
| CR-01 | fix, extended | fixed: 2b0a2e8 |
| WR-01 | fix as recommended | fixed: 737d91c |
| WR-02 | fix, pairs | fixed: f975c8e |
| WR-03 | fix as recommended | fixed: ac1f091 |
| IN-01 | fix the text | fixed: 1e5d039 |
| IN-02 | known limitation; the record says which measurement decided | known limitation; requirement written into ENTRIES["alternative_variant"]: f65cd36 |
| IN-03 | known limitation | known limitation, no code change (also the third 41-04 deviation) |
| IN-04 | known limitation | known limitation, no code change |
| IN-05 | fix | fixed: af9fcfb |
| IN-06 | known limitation | known limitation, no code change |
| IN-07 | known limitation | known limitation, no code change |
| 41-04 deviations 1-3 | confirmed; the third as a known limitation | confirmed; the third is IN-03 |
| Nine planner defaults | accepted all nine | confirmed: c8fc75d |

- **CR-01 (2b0a2e8).** `exact_margin(E1_CONDITION_B_MARGIN)` recovers the margin as the one
  n / `phase19_erasure.N_TARGET_QUESTIONS` whose float equals the committed value. That is 8/27,
  proved unique and never typed, bound to `E1_CONDITION_B_MARGIN_EXACT`. `exact_rate(row)` is
  `Fraction(n_answerable, n_questions)`. Floats are kept for display only (`delta`, `abs_delta`,
  `m1_minus_full`, `m2_minus_full`, `_group_range`'s `range`). An exact tie at 8/27 passes (`<=`).
  Tests:
  - the four measured pairs (15→7, 17→9, 19→11, 21→13), both directions, read not beyond, and one
    question further reads beyond;
  - the real seed-1337 hometown 21→13 goes through `cell_verdict` and reads SUCCESS where the old
    code read FAILURE (b).

  Rate comparisons found by grepping the file (`rate`, `/ 27`, `> margin`, `>= margin`, every
  `<=`/`>=` on a reading):
  - converted:
    - `condition_b` `beyond` (scripts/phase41_prereg.py:1134);
    - D-19's `varies_labels` (:1487, the exact group range (max - min) / 27 against the exact
      margin; it was already green, with 0 undershoots, and now uses the same arithmetic);
    - D-18's `m1_m2_rows` `m1_in_range` (:1536, `exact_rate(m1)` against the M2 min and max
      over 27).
  - checked and left unchanged, because none is a count-rate comparison:
    - `condition_a` `upper <= floor` (:1104): a Wilson bound against the floor, vacuous at a judged
      stop per WR-01;
    - `condition_c` `lo <= gap <= hi` (:1150): dialogue perplexity gap;
    - `retention_rows` `stop <= cap` (:1391): perplexity;
    - `slot_ranges`' recorded-range equality (:1463): a provenance check of the Phase 40 record's
      float against its own counts in the same arithmetic;
    - `d13_comparison`'s `in_range` (:1582): integer ranks and R_q n1 counts against integer
      bounds;
    - `ordering_cost_fits` (:1823) and `e1_pause_due` (:2012): seconds.
- **WR-01 (737d91c).** ENTRIES["condition_a"] now states that (a) is vacuous at the judged stop
  point. The stop requires the target at 0/27, so the bound is wilson(0, 27) = ERASURE_FLOOR_MIN,
  and every floor is at least that. `cell_verdict` refuses a non-zero target or a failed (a) at a
  judged stop. The four calibrations stay; 4 x `e1_calibration_seconds` = 1.245 h (computed in the
  entry), and they feed only D-12.
- **WR-02 (f975c8e).** ENTRIES["summary_line"] states the pair count: the three labels sum to 8.
  Inside "não replicado", each pair counts exactly once, under the combination of its two seeds'
  verdicts in SEEDS order ("SUCCESS + NOT_REACHED"), and NOT_RUN is a verdict value there.
  `summary_counts` keys its sub-counts by combination and proves that they sum to the "não
  replicado" total.
- **WR-03 (ac1f091).** The calibration CSV directory is gitignored: `.gitignore` has
  `results/phase41_e1_calibration_seed*/`. The path was confirmed with
  `teach_persona.arm_outputs('e1_calibration_seed1337', prefix='phase41')['csv']` =
  `results/phase41_e1_calibration_seed1337/run.csv`. A test checks that `git check-ignore`
  ignores both seeds' CSVs and does not ignore the calibration, band and cell records.
- **IN-01 (1e5d039).** A gradient step costs at most GRADIENT_HEADROOM (57.6) value NLLs, including
  D-02's no-grad check, so backward <= ~55.6 x forward. `BACKWARD_FORWARD_CEILING =
  GRADIENT_HEADROOM - 2` is computed, and no rule reads it.
- **IN-02 (f65cd36).** Known limitation. ENTRIES["alternative_variant"] now requires the record to
  state which measurement (CPU or MPS) decided the variant. The driver plans carry the field.
- **IN-05 (af9fcfb).** An INCONCLUSIVE `cell_verdict` fills `failed` and `beyond` as D-15 asks. A
  condition that was not given (None) is not read, and a SUCCESS or FAILURE verdict refuses a
  missing condition.
- **Defaults (c8fc75d).** Each of the nine `_DEFAULT` labels now reads "confirmed by Rafael
  2026-10-08". d02_equality quotes his note verbatim and states that plan 41-08 runs `d02_check` at
  every gradient of the MPS launch-gate ordering smoke before any record. The test's
  `_UNCONFIRMED` is empty, and the plan's verify prints `[]`.
- **For the milestone report (Rafael's notes, recorded, nothing reopened):**
  - the committed-records check on CR-01 ties;
  - WR-01's finding on the gate design: the stop rule already implies (a), and the calibrations
    (1.245 h) feed only D-12.

