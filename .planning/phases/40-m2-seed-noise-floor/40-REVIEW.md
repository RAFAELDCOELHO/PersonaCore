---
phase: 40-m2-seed-noise-floor
reviewed: 2026-10-05T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - scripts/phase40_prereg.py
  - tests/test_phase40_prereg.py
findings:
  critical: 0
  warning: 3
  info: 7
  total: 10
status: issues_found
---

# Phase 40: Code Review Report

**Reviewed:** 2026-10-05
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

I reviewed `scripts/phase40_prereg.py` (at 8805c0d) and `tests/test_phase40_prereg.py` against
40-CONTEXT (D-01..D-16, the Addendum, and the Approvals at 03de080) and plans 40-02/40-03. I
checked the estimators against the committed v3.0 records and ran experiments on the
seed-outcome, manifest and gap edge cases. The suite passes (46 tests in 3.79 s), and ruff check
and format are clean.

These parts match the committed records and Rafael's rulings, measured:
- `pair_d` reproduces 0.14814814814814814 (Phase 18 vs replicate) and 0.2592592592592592 (Phase 18 vs retrain).
- The `d12_table` same-seed pair reproduces v3.0's signed `delta_taught_to_m2`.
- The pooled 27 = 14 + 13 denominator holds on `phase19_arm_retrain.json`.
- `E2_PROJECTION_HOURS` 7.9518624092864085, `E2_TOTAL_HOURS` 77.78526798055215 and the E2+E5+E6 totals 78.12639556620314 / 78.12556459250179 all equal the Approvals bullets.
- `fsum(front_hours)` equals the committed `total_hours`.
- The v3.0 dialogue floor's seed_a `adapter_on` equals the replicate A2 record's `dialogue_ppl`, so the `gap_pair` prediction compares like with like.
- Every seed and ledger case asked about classifies correctly: start+lost+start+end gives whole, multiple losts give dropped, an open attempt refuses, and no attempt gives not_run.

**Under Rafael's stopping rule, none of the findings blocks.** No finding changes a value read, a
verdict, the noise floor, the gap floor or the seed/rerun selection in a real fill as plans
40-05..40-07 call these functions. WR-01..WR-03 are latent: each changes an outcome only on an
input the planned driver does not produce. They are worth closing now because the file freezes
at the first `results/phase40_*` record. After that, any fix has to be a dated continuation.

## Warnings

### WR-01: seed_outcomes reads only the LAST attempt, so a once-whole seed can be reclassified "dropped" and re-run

**File:** `scripts/phase40_prereg.py:1238-1255`, `1258-1268`
**Issue:** R-3 b says "A regra vale só para queda (sem linha de fim), nunca para semente concluída."
`seed_outcomes` looks only at `mine[-1]`. If a seed's ledger has an end line followed by a later
start and lost, the seed becomes "dropped":
- `build_record` (40-07) would then exclude that seed's whole records from both estimators.
- `pending_seeds(rerun={seed})` would schedule the completed seed again.

The planned driver cannot reach this state, because `pending_seeds` never schedules a whole seed.
It takes a driver bug or a manual `phase36_ledger.append("start", ...)`. Even so, the ruled
condition is enforced nowhere in the frozen code.

**Evidence:**
```
$ .venv/bin/python <scratchpad>/exp40.py   # leg E1: start,end(seed1337.json),start,lost for 1337
== E1 whole seed then a later lost attempt
dropped (1337, 2024, 1338, 2025, 1339)
```
**Fix:** in `seed_outcomes`, after the open-attempt check:
```python
_prove(
    not any(c["event"] == "end" for _, c in mine[:-1]),
    f"seed {seed}: a whole seed has a later attempt (R-3 b: never for a completed seed)",
)
```

### WR-02: the "approved" check is a substring test that accepts negations

**File:** `scripts/phase40_prereg.py:1329`, `1377`
**Issue:** The test is `"approved" in text`, so "not approved", "não approved" and "unapproved"
all pass. This applies to both the R-3 b manifest (condition a) and the relaunch declaration
(condition b). Plan 40-06 has Claude call `drop_attempt(..., approved=<text>)` and
`declare_relaunch(..., approved=<text>)` with Rafael's reply. A conditional or negated reply would
therefore be accepted as his approved, and the rerun would become eligible. This is new to Phase
40: no other script uses this check.

**Evidence:**
```
== E3 'approved' substring
'not approved' [] []
'não approved' [] []
'unapproved' [] []
```
(`dropped_manifest_failures` and `relaunch_declaration_failures` both return `[]`.)

**Fix:** require the standalone token and refuse a negation:
```python
import re
def _approved(text):
    return isinstance(text, str) and bool(re.search(r"(?<![\w-])approved\b", text)) \
        and not re.search(r"\b(not|não|nao|un)[\s-]*approved\b", text, re.I)
```
Use `_approved` at both sites. Rafael should rule whether this counts as a BLOCK, because it
changes manifest acceptance when the input is negated.

### WR-03: dialogue_gap trusts the caller's `device` and ignores the record's own `config.device`

**File:** `scripts/phase40_prereg.py:1071-1106`
**Issue:** The R-1 mps-equality refusal fires only when `device == "mps"` exactly. The function
never compares `device` with `record["config"]["device"]`, which run_erasure_arm writes. Two
callers would silently skip the R-1 check and label a real MPS reading `rehearsal: True`:
- a caller passing "mps:0";
- a caller passing the emit process's own device ("cpu"; `record_layout` says the noise-floor
  record is "built on CPU").

Plan 40-07 passes the seed record's `provenance.run.device`, so the planned fill is correct only
if that string is exactly "mps".

**Evidence:** a record with `config.device == "mps"` and a CPU adapter-off:
```
record config.device: mps
mps:0 -> no refusal; rehearsal True matches False
cpu -> no refusal; rehearsal True matches False
mps -> [phase40_prereg] adapter-off 4.573348505014267 != committed 4.573349214207799 on mps (D-09, R-1 mps-equality)
```
**Fix:** at the top of `dialogue_gap`:
```python
_prove(device == record["config"]["device"],
       f"device {device!r} != the A2 record's config.device {record['config']['device']!r}")
```
Alternatively, drop the parameter and read the device from the record.

## Info

### IN-01: The R-2 reading records |pre - post| but not the pre values themselves
**File:** `scripts/phase40_prereg.py:1098-1113`. R-2 is ruled as "pre is recorded beside". The
reading has only `pre_post_abs_difference` and the flag. Evidence (E7): the keys have no
`pre_*` field, and `{'adapter_on': 0.5, 'adapter_off': 0.0}`. The values can be recovered from
the A2 record, which the seed record names by sha256. **Fix:** add
`"pre": {"adapter_on": pre["adapter_on"], "adapter_off": pre["adapter_off"]}`.

### IN-02: Under R-1 with "post", only the post adapter-off is compared on mps
**File:** `scripts/phase40_prereg.py:1092-1097`. Evidence (E8): a record whose pre-off is 4.5 and
whose post-off is the committed value returns `adapter_off_matches_committed True` on mps, with
no refusal. The ruled text says "every A2 record's adapter-off". **Fix:** under mps-equality, also
check `pre["adapter_off"] == committed_off`, or rule that only the post reading counts.

### IN-03: The manifest's `kept` entries are not validated beyond their prefix, and None raises
**File:** `scripts/phase40_prereg.py:1340-1353`. Evidence (E4/E5): a `path` of
`<dir>/../../../results/phase40_seed2024.json` with empty `from` and `sha256` returns `[]`, and
`dropped_manifest_failures(None, ...)` raises `TypeError`, although the docstring says "Never
raises". This is deliberate-bypass hardening. **Fix:** reject `..` segments
(`pathlib.PurePosixPath(p).parts`), require `re.fullmatch(r"[0-9a-f]{64}", sha256)`, and
refuse a non-mapping manifest.

### IN-04: a2_rows does not check the record's K
**File:** `scripts/phase40_prereg.py:932-948`. Evidence (E9): a copy of the retrain record with
`config.k = 1` is accepted, giving 8 rows. run_erasure_arm's Phase 18 parity assertion covers
this in a real fill. **Fix (optional):** compare `record["config"]["k"]` with the Phase 18 record's k.

### IN-05: The non-vacuity leg of test_r3_conditions_and_record_total_are_quoted_verbatim is a tautology
**File:** `tests/test_phase40_prereg.py:509-515`. Evidence: with both prereg constants set to
`'wrong'`, the leg still passes ("non-vacuity leg passes against wrong constants"). The leg never
plants a change into the CONTEXT text. The equality legs above it are what carry the test.
**Fix:** plant one changed character into `_approvals_text()` and assert that `_one_quote` no
longer equals the constant, as `test_approvals_rulings_r1_to_r4_match_the_typed_values` does.

### IN-06: The module docstring understates what importing the module loads
**File:** `scripts/phase40_prereg.py:20-24` vs `280-281`. `d13_nlls_per_adapter()` runs at import
because `D13_INCLUDED` is True, so importing the prereg loads phase19_erasure, phase38_rank and
phase18_extraction. Evidence: `['phase19_erasure', 'phase38_rank', 'phase18_extraction']` are in
`sys.modules` after `import phase40_prereg`. No checkpoint is opened (the audit-hook test is
green). **Fix:** reword the docstring.

### IN-07: d13_block does not check the R_q denominator
**File:** `scripts/phase40_prereg.py:1410-1413`. `n` is `len(ranks)` and is not compared with
`N_TARGET_QUESTIONS`. Evidence: `test_d13_block_reduction` itself passes 3 and 2 ranks and gets a
block back. **Fix (optional):** `_prove(len(ranks) == pin.N_TARGET_QUESTIONS)` per set.

## Latent-red check (tests reading real git/tree state)

None found that would flip when plans 05-10 land:
- The ancestry guards use the earliest add, and the test-file guard uses only this file's first add.
- `test_records_at_commit` reads the prereg's first commit.
- The slot census will scan the future `phase40_noise.py` by design.
- `_UNCONFIRMED` is meant to be edited in plan 04, before any record exists.
- `_ADDENDUM_SHA = "544ed02"` is a short SHA. It resolves uniquely today
  (`git rev-parse --disambiguate=544ed02` gives 1 line, with about 14k objects), so the
  ambiguity risk is negligible.

Evidence script: `/private/tmp/claude-501/-Users-juliorcoelho-PersonaCore/d19c6c2a-db59-41c1-946c-681523a61ee9/scratchpad/exp40.py`.

## Resolution (2026-10-06)

Rafael's reply, pasted text (proposto pelo Claude (claude.ai), adotado por Rafael), copied byte for byte from the paste. Every edit landed in `scripts/phase40_prereg.py` and `tests/test_phase40_prereg.py` before his "reviewed", with no `results/phase40_*` record tracked. After each commit, `tests/test_phase40_prereg.py`, `tests/test_phase35_prereg.py`, `tests/test_phase36_caps.py` and `ruff check . && ruff format --check .` ran green. Each fix's test was seen RED first.

### Rulings per finding (verbatim)

```
Decisões por achado:
- WR-01, WR-02, WR-03: corrigir.
- IN-01, IN-03, IN-04, IN-05, IN-06, IN-07: corrigir.
- IN-02: opção a. Em MPS, a leitura pré e a leitura pós com adaptador desligado são conferidas contra o valor commitado, e qualquer uma que difira recusa o gap.
```

| Finding | Ruling | Fix commit | RED seen first | After the fix |
|---------|--------|------------|----------------|---------------|
| WR-01 | fix | 75a2ab5 | start,end,start,(lost or end) for 1337: DID NOT RAISE | `seed_outcomes` refuses a whole seed with a later attempt (R-3 b) |
| WR-02 | fix | f3b50da | 'not approved' gave `[]` from both R-3 b sites | `_approved(text)`: the standalone token `approved`, no `not`/`não`/`nao`/`un` before it, used at both sites; "approved", APPROVALS_RULING and "aprovo a re-execução. approved" still pass |
| WR-03 | fix | 9f4592a | 'mps:0' and 'cpu' on an mps record: DID NOT RAISE | `dialogue_gap` refuses a device that is not the record's `config.device` |
| IN-01 | fix | 4b12a5d | `KeyError: 'pre'` | the reading carries `pre` {adapter_on, adapter_off, adapter_off_matches_committed} |
| IN-02 | option a | 4b12a5d | pre adapter-off off the committed value on mps: DID NOT RAISE | on mps under mps-equality, pre and post adapter-off are both checked against the committed 4.573349214207799 and either differing refuses; R-2 post still picks the reading the gap uses; off mps both match flags are recorded |
| IN-03 | fix | bc21cc3 | a `..` kept path gave `[]` | refuses a `..` segment, a sha256 that is not 64 lowercase hex, an empty `from`, and a non-mapping manifest (returned as a failure, never raised) |
| IN-04 | fix | 97a06bf | `config.k = 1`: DID NOT RAISE | `a2_rows` refuses a record whose `config.k` differs from the Phase 18 record's (48) |
| IN-05 | fix | 7dc13b6 | under a parser that ignores the text, the old leg passed and the new leg failed | the non-vacuity leg plants one character into 40-CONTEXT at 03de080 and requires the parsed quote to follow it |
| IN-06 | fix | cf49c7e | the docstring had no 'Measured at import' line | the docstring line "Measured at import: loads phase14_factset, phase18_extraction, phase19_erasure, phase19_floor, phase36_ledger, phase38_rank; never phase19_run." is checked against the audit-hook probe's `sys.modules` |
| IN-07 | fix (with ruling c) | 541da56 | the old test's 3 and 2 ranks gave a block back | an R_q set off N_TARGET_QUESTIONS (or a rank that is not an int >= 1, or an empty curve) is a malformed reading: `d13_block` returns `d13_not_measured("malformed_reading", ...)` (ruling c), not a SystemExit |

Re-running the reviewer's experiments (`exp40.py` legs, on the fixed file):
- E1 now raises "a whole seed has a later attempt".
- E3: all four negations fail at both sites.
- E4 gives the `..`, sha256 and `from` failures.
- E5 returns "manifest is NoneType, not a mapping".
- E6: 'mps:0' and 'cpu' raise on config.device, and 'mps' raises R-1.
- E7 records `pre`.
- E8 raises R-1.
- E9 raises on k.

### Confirmations per item (verbatim) and their prereg home

Item d was not asked again (R-1..R-4 were ruled at 40-01). The quotes live in `CONFIRMATIONS`. Each is written as `confirmed by Rafael 2026-10-06 (<letter>): "..."` into its entry's derivation, all in 0c80656. `_DEFAULT` was deleted.

| Item | Rafael (verbatim) | Entry | Ruling |
|------|-------------------|-------|--------|
| a | "Confirmo: desvio-padrão amostral (n−1) por slot, com o populacional ao lado." | `e2_noise_floor_estimator` | D-04 sample SD (statistics.stdev, n - 1) with the population SD beside — confirmed. |
| b | "Confirmo: rótulo 'retrain' nos dois grupos, com a paridade afirmada; o grupo fica nos campos da Fase 40. O relatório explica o rótulo uma vez." | `a2_pass` | A2 label 'retrain' for both groups — confirmed. The report's one-time explanation of the label is plan 07's. |
| c | "Confirmo a ordem (D-13 por último na unidade de cada semente), com uma mudança: uma falha do D-13 (exceção, portão diferente ou leitura fora de formato) nunca derruba a semente. Ela é gravada no registro da semente como D-13 não medido, com o motivo, e a semente termina normalmente. Só a morte do processo conta como queda, pelo R-3 b." | `run_order` | D-15 placement — CHANGED: a D-13 failure never drops the seed. Implemented in 541da56: `D13_FAILURE_KINDS = ("exception", "gate_mismatch", "malformed_reading")`, `d13_not_measured(kind, reason)`, `d13_block(...)` returning it for a gate mismatch or a malformed reading, `d13_reading(blocks_by_seed)` for the noise-floor record; the run_order value and d13_addition's anchor_gate say so. |
| e | "Confirmo: com menos de 2 sementes inteiras, nenhum piso é publicado e a fase para para mim. Com 2 a 4, o registro declara quantas sementes e quantos pares entraram." | `e2_noise_floor_estimator` | INSUFFICIENT_SEEDS — CHANGED (addition): with 2 to 4 whole seeds the record declares how many seeds and pairs entered. Implemented in 01a33ee: recall_floor's `published` and gap_noise_floor carry `n_seeds` and `n_pairs` (group_floor already did); tested at S' = 2, 3, 5; the estimator's `minimum` key says so. |
| f | "Confirmo os registros e a ordem de commit: livro-caixa, registros de cada semente, piso, relatório, cada um com meu approved." | `record_layout` | Records and commit order — confirmed. |
| g | "Confirmo, com um acréscimo: como todos os adaptadores usam os mesmos números aleatórios e o piso de amostragem do v3.0 usou sorteios independentes, o piso de treino não é um limite superior de 'treino mais amostragem' e pode sair menor que 0,148." | `e2_noise_floor_estimator` | D-05 wording — confirmed with an addition, written verbatim into the derivation; the report wording is the driver plans' job. |
| h | "Confirmo: taxa do M2 menos taxa do completo, o mesmo sinal do v3.0." | `d12_rereading` | D-12 sign (m2 - full, v3.0's) — confirmed. |
| i | "Confirmo: as previsões do D-07 são lidas como descrição; uma diferença é um achado, não uma falha." | `predictions` | D-07 predictions — confirmed (descriptive; a mismatch is a finding). |

On c: "portão diferente" is implemented as the D-13 anchor gate, `gate_rank != a2_rank` (the committed |R| rank against the A2 record's exposure rank). That is the only gate in D-13. The driver must catch every exception raised by its D-13 scoring, including the prereg's `SystemExit`, and record it as `d13_not_measured("exception", reason)`.

Open question on f: his words end "cada um com meu approved", but the record_layout value (unchanged) says "after Rafael's approved". This section does not settle whether that means one approved per commit step or one approved for the whole sequence. The driver plans quote his words.

---

_Reviewed: 2026-10-05_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
