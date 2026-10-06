"""Phase 40 pre-registration: E2's seed count, both written noise-floor estimators, the record
paths and the D-11 / D-13 / D-14 approval with its budget arithmetic, frozen before any
``results/phase40_*`` record (40-CONTEXT D-15/D-16, NOISE-01, NOISE-02).

This module fills the two Phase 35 slots owned by Phase 40 exactly once each, as the module-level
bindings ``E2_S`` (read from the Phase 36 budget record, never typed) and
``E2_NOISE_FLOOR_ESTIMATOR`` (one entry holding both estimators, D-16 path 1). Under the Phase 35
slot-ordering leg (a) every commit touching this file must strictly precede the first add of every
``results/phase40_*`` record, so the rule is written in full before any E2 number exists.

Plan 40-03 adds the pure functions that implement the estimators to this same file; plan 40-04's
review with Rafael runs before any driver code. Once any ``results/phase40_*`` record exists this
file is closed: any correction is Rafael's ruling plus a dated continuation through
``scripts/_addendum.py``, never an edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). S, the projection, total and stop hours and the D-13 NLL count are computed at import
from committed records and the modules that own each term, never typed.

Not torch-free at import: ``phase35_prereg.seed_list()`` imports phase23_run, which imports
teach_persona and torch. The heavy imports are written inside the functions that need them, but
importing this module still loads most of them (IN-06). Measured at import: loads
phase14_factset, phase18_extraction, phase19_erasure, phase19_floor, phase36_ledger,
phase38_rank; never phase19_run.
phase14_factset, phase18_extraction, phase19_floor and phase36_ledger arrive through the
module-level phase35/36/38/39 prereg imports (phase38_prereg and phase39_prereg are there for the
E2 + E5 + E6 record total); phase19_erasure and phase38_rank through ``d13_nlls_per_adapter()``,
which runs at import because D13_INCLUDED is True. Measured, importing this module opens no
checkpoints/ or data/ file (tests/test_phase40_prereg.py's audit hook).
"""

import collections.abc
import fnmatch
import itertools
import json
import math
import pathlib
import re
import statistics
import sys
import types

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase35_prereg  # noqa: E402  (needs the sys.path insert above)
import phase36_prereg  # noqa: E402  (same; torch-free)
import phase38_prereg  # noqa: E402  (same; frozen: import only)
import phase39_prereg  # noqa: E402  (same; frozen: import only)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase40_*` file existed, tracked or untracked.
COMMITTED = "2026-10-05"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase40_prereg] {message}")


# =================================================================================================
# (2) THE ENTRY SCHEMA, BY REFERENCE to the v6.0 pre-registration's public tuples.
# =================================================================================================

ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE


def _prove_count(name, value, low=0):
    """An ``int`` (bool excluded) of at least ``low``, never a float out of arithmetic."""
    _prove(
        isinstance(value, int) and not isinstance(value, bool) and value >= low,
        f"{name} is {value!r}, not an int >= {low} (bool excluded)",
    )


def _prove_entry(name, entry):
    """Refuse any entry that is not exactly the four fields with a known kind."""
    _prove(
        isinstance(entry, collections.abc.Mapping),
        f"entry {name!r} is {type(entry).__name__}, not a mapping",
    )
    for banned in ("proposer", "adopted_by"):
        _prove(
            banned not in entry,
            f"entry {name!r} carries a {banned!r} key. Entries hold exactly {ENTRY_FIELDS}; who "
            "suggested what lives in the discussion logs and git",
        )
    _prove(
        set(entry) == set(ENTRY_FIELDS),
        f"entry {name!r} has fields {sorted(entry)}, expected exactly {sorted(ENTRY_FIELDS)}",
    )
    _prove(entry["kind"] in KINDS, f"entry {name!r} has kind {entry['kind']!r}, not one of {KINDS}")
    for field in ("derivation", "source"):
        text = entry[field]
        _prove(
            isinstance(text, str) and text.strip(),
            f"entry {name!r} has an empty or non-str {field}",
        )
        _prove(
            FORBIDDEN_PHRASE not in text, f"entry {name!r} {field} contains {FORBIDDEN_PHRASE!r}"
        )
    value = entry["value"]
    _prove(
        not (isinstance(value, str) and FORBIDDEN_PHRASE in value),
        f"entry {name!r} value contains {FORBIDDEN_PHRASE!r}",
    )


def _read(rel):
    """A committed JSON record, by repository-relative path."""
    return json.loads((_REPO_ROOT / rel).read_text(encoding="utf-8"))


# =================================================================================================
# (3) THE RECORD PATHS, derived from the path the v6.0 pre-registration reserved (by EQUALITY).
# =================================================================================================

RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase40_*")
# The noise-floor record Phase 41's e1_condition_c_band_inputs rule reads (a registry read).
NOISE_FLOOR_RECORD = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
_prove(
    NOISE_FLOOR_RECORD == RECORD_GLOB.replace("*", "noise_floor.json"),
    f"the registry's noise-floor record {NOISE_FLOOR_RECORD} is not {RECORD_GLOB}'s noise_floor",
)
REPORT_RECORD = RECORD_GLOB.replace("*", "noise_floor_report.md")
BUDGET_RECORD = phase35_prereg.SLOTS["e2_S"]["input_records"][0]

# D-01: the two groups, kept separate.
GROUPS = ("full", "m2")
# Claude's discretion (40-CONTEXT): the pinned A2 pass's arm label. "retrain" is in
# phase19_erasure.PARITY_ASSERTED_ARMS (the parity check runs before the first draw) and carries
# no components.
A2_LABEL = "retrain"


def seed_record(seed):
    """The per-seed record of one whole seed (named by its ledger end line)."""
    path = RECORD_GLOB.replace("*", f"seed{seed}.json")
    _prove(fnmatch.fnmatch(path, RECORD_GLOB), f"{path} does not match {RECORD_GLOB}")
    return path


def a2_record(group, seed):
    """The A2 arm record run_erasure_arm writes for ``group`` at ``seed``."""
    _prove(group in GROUPS, f"group {group!r} is not one of {GROUPS}")
    path = RECORD_GLOB.replace("*", f"a2_{group}_seed{seed}.json")
    _prove(fnmatch.fnmatch(path, RECORD_GLOB), f"{path} does not match {RECORD_GLOB}")
    return path


def run_id(seed):
    """The ledger run id of ``seed``'s attempts (one ledger attempt per seed, D-15)."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    return phase36_ledger.run_id(40, "E2", f"seed{seed}")


# =================================================================================================
# (4) THE D-11 / D-13 / D-14 APPROVAL AND ITS ARITHMETIC, from the committed budget.
# =================================================================================================

_BUDGET = _read(BUDGET_RECORD)
_E2_CAPS = _BUDGET["unit_caps"]["E2"]


def e2_projection_hours(d13_adapters=0, d13_nlls_per_adapter=0):
    """The budget's E2 term in hours, plus the D-13 scoring of ``d13_adapters`` M2 adapters at
    ``d13_nlls_per_adapter`` NLLs each (adapter setup + NLLs at the committed high prices).

    The committed term comes first, in scripts/phase36_budget.py's ``_front_seconds`` order: only
    in this order does the no-D-13 value reproduce ``front_hours.E2`` bit for bit (floating point
    is not associative).
    """
    p = _BUDGET["unit_prices"]
    e2 = _E2_CAPS
    committed = (
        e2["seeds"]
        * (p["e2_train_m2_high"] + p["e2_train_full_high"] + e2["adapters"] * p["e2_a2_pass_high"])
        / 3600
    )
    return (
        committed
        + d13_adapters * (p["adapter_setup_high"] + d13_nlls_per_adapter * p["e5_nll_high"]) / 3600
    )


_prove(
    e2_projection_hours() == _BUDGET["front_hours"]["E2"],
    "the E2 formula at the committed caps does not reproduce front_hours.E2",
)


def d13_nlls_per_adapter():
    """D-13's NLLs per M2 adapter, from the modules that own each term.

    38-D-08: the nested anchor prefixes share the largest prefix's scores, so the anchor costs the
    largest size; the gate re-scores the committed |R|; R_q scores the committed |R| per question,
    and the minted |R| = MINTED_SET_SIZE set shares the taught value's NLL with it (39-D-26).
    """
    import phase18_extraction  # torch at import: lazy
    import phase19_erasure as pin  # torch at import: lazy
    import phase38_rank  # torch at import: lazy

    slot = pin.TARGET_SLOT
    anchor = phase38_rank.scoring_plan(slots=(slot,))[slot]["size"]
    refs = len(phase18_extraction.reference_set_for(slot))
    questions = sum(e["slot"] == slot for e in phase35_prereg.a2_corpus_entries())
    _prove(
        questions == pin.N_TARGET_QUESTIONS,
        f"{questions} A2 questions on {slot}, not phase19_erasure.N_TARGET_QUESTIONS",
    )
    return anchor + refs + questions * refs + questions * (phase39_prereg.MINTED_SET_SIZE - 1)


# Rafael's reply at plan 40-01, quoted character for character from 40-CONTEXT.md at the Approvals
# commit 03de080 (tests/test_phase40_prereg.py proves each against that commit).
# The "- **Approvals reply (verbatim):**" bullet: the FIRST paragraph of his reply only.
APPROVALS_RULING = (
    "aprovo D-11 (+0 h). aprovo D-13 (+0,0609 h). R-1 a. R-2 a. R-3 b. R-4 a. approved"
)
# The "- **R-3 b conditions (verbatim):**" bullet: his second paragraph.
R3_CONDITIONS_RULING = (
    "Condições do R-3 b: a nova tentativa de uma semente derrubada exige meu approved e uma nota "
    "de causa; usa a mesma semente e o mesmo HEAD (ou a mudança é declarada); os resultados "
    "parciais da tentativa derrubada são mantidos e listados no registro; se as duas tentativas "
    "produzirem o mesmo adaptador, a igualdade tensor a tensor entre elas é reportada. A regra "
    "vale só para queda (sem linha de fim), nunca para semente concluída."
)
# The "- **Record total (verbatim):**" bullet: his third paragraph.
RECORD_TOTAL_RULING = (
    "No registro, mostre também o total projetado incluindo os extras já aprovados do E5 e do E6, "
    "não só o total commitado da Fase 36."
)
# The Addendum ruling (D-07 / D-08 amended, D-08b): 40-DISCUSSION-LOG.md at 544ed02, the
# "**Rafael (verbatim):**" line and its continuation lines joined by one space.
ADDENDUM_RULING = (
    "Opção 1 (correção), com dois ajustes:1. D-08 passa a dizer: persona_adapter.pt e "
    "phase19_erase_dialogue_floor_seed1337_adapter.pt são o mesmo adaptador (72 tensores iguais; "
    "o sha do arquivo difere só pelo nome gravado no zip). O relatório do milestone registra isso "
    "como correção da nota do scout, não como limitação do v3.0.2. A diferença residual "
    "(contagens do A2 do lado ensinado vindas dos sorteios do run_arm da Fase 18, e não do "
    "run_erasure_arm) é reportada com o tamanho medido contra o completo@1337. Ela só recebe o "
    "nome de limitação do v3.0 se as contagens diferirem em pesos idênticos. Se o completo@1337 "
    "novo não reproduzir os pesos bit a bit, o relatório diz que os dois efeitos não se "
    "separam.3. Correção de D-02 (checagem de determinismo): toda comparação entre adaptador novo "
    "e commitado é feita tensor a tensor (torch.equal em todos os tensores, mais metadados), "
    "nunca pelo sha256 do arquivo. Vale para M2@1337 contra phase19_erase_reference_adapter.pt e "
    "para completo@1337 contra persona_adapter.pt."
)

# Typed ruling values, each from its Approvals bullet at 03de080.
# "- **D-11:** approved" ("aprovo D-11 (+0 h)").
D11_APPROVED = True
# "- **D-13/D-14:** approved — included in the driver" ("aprovo D-13 (+0,0609 h)").
D13_INCLUDED = True

# "- **R-1 (adapter-off check, device-scoped):** mps-equality".
ADAPTER_OFF_RULES = ("mps-equality", "record-only")
ADAPTER_OFF_RULE = "mps-equality"
# "- **R-2 (pre != post dialogue reading):** post".
PRE_POST_RULES = ("post", "mean", "refuse")
PRE_POST_RULE = "post"
# "- **R-3 (dropped seed):** rerun-as-new-attempt" (True), under R3_CONDITIONS_RULING.
DROPPED_SEED_RERUN = True
# "- **R-4 (A2 records and the approval block):** seed-record-names-a2".
A2_APPROVAL_RULE = "seed-record-names-a2"

_prove(ADAPTER_OFF_RULE in ADAPTER_OFF_RULES, f"R-1 {ADAPTER_OFF_RULE!r} is not an option")
_prove(PRE_POST_RULE in PRE_POST_RULES, f"R-2 {PRE_POST_RULE!r} is not an option")
_prove(type(DROPPED_SEED_RERUN) is bool, "R-3 DROPPED_SEED_RERUN is not a bool")

if D13_INCLUDED:
    D13_NLLS_PER_ADAPTER = d13_nlls_per_adapter()
    D13_ADAPTERS = _E2_CAPS["seeds"]  # one M2 adapter per seed
else:
    D13_NLLS_PER_ADAPTER = 0
    D13_ADAPTERS = 0

E2_PROJECTION_HOURS = e2_projection_hours(D13_ADAPTERS, D13_NLLS_PER_ADAPTER)
E2_TOTAL_HOURS = math.fsum({**_BUDGET["front_hours"], "E2": E2_PROJECTION_HOURS}.values())
E2_STOP_HOURS = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _BUDGET["front_hours"]["E2"]
_prove(
    E2_PROJECTION_HOURS <= E2_STOP_HOURS,
    f"the E2 projection {E2_PROJECTION_HOURS!r} h exceeds the committed stop {E2_STOP_HOURS!r} h "
    "(front_stop_factor x front_hours.E2). This projection goes to Rafael BEFORE launch; 38-D-23 "
    "forbids a second stop rule, so nothing runs until he rules.",
)

# RECORD_TOTAL_RULING: the projected total with the approved E5 and E6 extras, imported from the
# frozen preregs, never retyped. E6_PROJECTION_HOURS is the priced projection Phase 39 approved;
# the actual-gate one (its D-30 variant) is shown beside it.
E2_E5_E6_TOTAL_HOURS = math.fsum(
    {
        **_BUDGET["front_hours"],
        "E2": E2_PROJECTION_HOURS,
        "E5": phase38_prereg.E5_PROJECTION_HOURS,
        "E6": phase39_prereg.E6_PROJECTION_HOURS,
    }.values()
)
E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE = math.fsum(
    {
        **_BUDGET["front_hours"],
        "E2": E2_PROJECTION_HOURS,
        "E5": phase38_prereg.E5_PROJECTION_HOURS,
        "E6": phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE,
    }.values()
)

APPROVAL_KEYS = (
    "ruling",
    "r3_conditions",
    "record_total_ruling",
    "addendum_ruling",
    "source",
    "rulings",
    "d11_approved",
    "d11_extra_seconds_reason",
    "d13_included",
    "d13_nlls_per_adapter",
    "d13_adapters",
    "e2_projection_hours",
    "committed_front_hours_e2",
    "e2_total_hours",
    "committed_total_hours",
    "e5_projection_hours",
    "e6_projection_hours",
    "e6_projection_hours_actual_gate",
    "e2_e5_e6_total_hours",
    "e2_e5_e6_total_hours_e6_actual_gate",
    "e2_stop_hours",
    "committed_unit_caps_e2",
    "budget_record",
    "untouched",
)


def approval_block():
    """D-11 / D-13 / D-14 and R-1..R-4: the approval, the projection, the totals and the stop,
    embedded in every Phase 40 seed record and in the noise-floor record (the A2 records carry none:
    R-4). A fresh JSON-ready dict on every call."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    block = {
        "ruling": APPROVALS_RULING,
        "r3_conditions": R3_CONDITIONS_RULING,
        "record_total_ruling": RECORD_TOTAL_RULING,
        "addendum_ruling": ADDENDUM_RULING,
        "source": (
            "40-CONTEXT Approvals (03de080); Addendum D-07/D-08/D-08b (544ed02); "
            "D-11/D-13/D-14 (9d53c09)"
        ),
        "rulings": {
            "R-1": ADAPTER_OFF_RULE,
            "R-2": PRE_POST_RULE,
            "R-3": "rerun-as-new-attempt" if DROPPED_SEED_RERUN else "never-rerun",
            "R-4": A2_APPROVAL_RULE,
        },
        "d11_approved": D11_APPROVED,
        "d11_extra_seconds_reason": (
            "dialogue_ppl_pair is measured inside every A2 pass (e2_a2_pass_high); read from the "
            "arm record (P-1)"
        ),
        "d13_included": D13_INCLUDED,
        "d13_nlls_per_adapter": D13_NLLS_PER_ADAPTER,
        "d13_adapters": D13_ADAPTERS,
        "e2_projection_hours": E2_PROJECTION_HOURS,
        "committed_front_hours_e2": _BUDGET["front_hours"]["E2"],
        "e2_total_hours": E2_TOTAL_HOURS,
        "committed_total_hours": _BUDGET["total_hours"],
        "e5_projection_hours": phase38_prereg.E5_PROJECTION_HOURS,
        "e6_projection_hours": phase39_prereg.E6_PROJECTION_HOURS,
        "e6_projection_hours_actual_gate": phase39_prereg.E6_PROJECTION_HOURS_ACTUAL_GATE,
        "e2_e5_e6_total_hours": E2_E5_E6_TOTAL_HOURS,
        "e2_e5_e6_total_hours_e6_actual_gate": E2_E5_E6_TOTAL_HOURS_E6_ACTUAL_GATE,
        "e2_stop_hours": E2_STOP_HOURS,
        "committed_unit_caps_e2": dict(_E2_CAPS),
        "budget_record": BUDGET_RECORD,
        "untouched": [
            phase36_ledger.LEDGER_PATH,
            BUDGET_RECORD,
            "scripts/phase36_ledger.py",
            "scripts/phase36_caps.py",
        ],
    }
    _prove(tuple(block) == APPROVAL_KEYS, f"approval_block keys {tuple(block)} != APPROVAL_KEYS")
    return block


# =================================================================================================
# (5) THE ENTRIES: the whole written rule, one entry per decision family.
# =================================================================================================

_CONTEXT = "40-CONTEXT D-{} (9d53c09)"
_ADDENDUM = "40-CONTEXT Addendum D-{} (544ed02)"
_APPROVALS = "40-CONTEXT Approvals (03de080)"
_DEFAULT = "default taken at plan time, not yet confirmed by Rafael"

_ENTRIES = {
    "e2_S": {
        "value": _BUDGET["e2_seed_count"],
        "derivation": (
            "NOISE-01, D-15: COST-01 chose S inside the Phase 36 budget record (e2_seed_count, "
            "checked there against D-06 and e2_min_seeds); this slot READS it, never types it "
            "(35-CONTEXT Addendum to D-15, Rafael 2026-10-01). SEEDS = seed_list()[:S]."
        ),
        "kind": "derived",
        "source": f"{BUDGET_RECORD}::e2_seed_count; 35-CONTEXT Addendum to D-15",
    },
    "e2_noise_floor_estimator": {
        "value": types.MappingProxyType(
            {
                "recall_floor": types.MappingProxyType(
                    {
                        "groups": GROUPS,
                        "slots": (
                            "phase19_erasure.GATED_NONTARGET_SLOTS (the 7 gated non-targets), by "
                            "reference"
                        ),
                        "measure": (
                            "A2 recall at K = the Phase 18 record's config k per fact, pooled over "
                            "both tiers by phase19_run._pooled_rows: n_answerable / n_questions "
                            "with the 27 = 14 core_taught + 13 core_held_out denominator; never an "
                            "arm record's per_fact (19-09 defect C)"
                        ),
                        "pair_statistic": (
                            "d(i, j) = phase19_erasure.nontarget_noise_floor("
                            "phase19_erasure.nontarget_deltas(nontarget_rows(rows_i), "
                            "nontarget_rows(rows_j))): the largest |recall difference| over the 7 "
                            "slots, v3.0's own statistic"
                        ),
                        "pairs": (
                            "every unordered pair of whole seeds of the SAME group, in seed_list "
                            "order: C(S', 2) pairs, S' the whole seeds"
                        ),
                        "group_floor": "the arithmetic mean of d over the group's pairs",
                        "published": (
                            "the larger of the two group floors, beside "
                            "phase19_floor.NONTARGET_NOISE_FLOOR; v3.0's (b) margin "
                            "phase35_prereg.e1_condition_b_margin() is never amended (NOISE-02)"
                        ),
                        "beside": (
                            "the max and min of d over the pairs, every pair's d, and per slot "
                            "the range and the sample standard deviation (statistics.stdev, n - 1) "
                            "with the population standard deviation (statistics.pstdev) beside, "
                            "across the whole seeds"
                        ),
                        "sampling_noise": (
                            "every A2 measurement is itself a sample, so this training-seed floor "
                            "INCLUDES sampling noise; every adapter is drawn at the same "
                            "per-question generator states (seed_index x K stride under "
                            "seed_everything(phase14_recall.SEED)) — common random numbers — so "
                            "the sampling part of a pair difference is correlated across "
                            "adapters, not independent"
                        ),
                        "minimum": (
                            "S' >= phase35_prereg.ENTRIES['e2_min_seeds'] whole seeds; below it "
                            "no floor is published and the record status is INSUFFICIENT_SEEDS"
                        ),
                    }
                ),
                "gap_noise_floor": types.MappingProxyType(
                    {
                        "adapters": (
                            "the full group only; the M2 gaps are read the same way and shown "
                            "beside it, descriptive"
                        ),
                        "gap": (
                            "adapter_on - adapter_off of each A2 arm record's dialogue reading "
                            "(masked_perplexity through phase19_erasure.dialogue_ppl_pair inside "
                            "run_erasure_arm, measured before the draws as "
                            "pre_erasure.dialogue_ppl and after them as dialogue_ppl on the same "
                            "adapter); when the two readings differ, PRE_POST_RULE decides (R-2: "
                            "post = the record's own dialogue_ppl with pre beside; mean = the mean "
                            "of both readings; refuse = no gap), and pre_post_equal is recorded "
                            "either way"
                        ),
                        "adapter_off": (
                            "device-scoped (R-1, ADAPTER_OFF_RULE): the committed reference is "
                            "results/phase19_noise_floors.json dialogue_ppl_noise_floor "
                            "seed_a.adapter_off == seed_b.adapter_off, read at call time with "
                            "adapter_off_identical_across_seeds true, never retyped; under "
                            "mps-equality the pre_erasure AND the post adapter-off reading on mps "
                            "must each equal it or the gap refuses (Rafael 2026-10-06, IN-02 "
                            "option a; R-2 still picks the reading the gap uses), and a "
                            "reading on any other device (the CPU rehearsal, whose off differs "
                            "from the MPS one) is recorded beside it with "
                            "adapter_off_matches_committed false and labelled rehearsal; under "
                            "record-only no device refuses and the match flag is recorded"
                        ),
                        "pair_statistic": (
                            "|gap_i - gap_j| over every unordered pair of whole full-group seeds"
                        ),
                        "value": "the arithmetic mean over those pairs; the max beside it",
                        "contract": (
                            "results/phase40_noise_floor.json::gap_noise_floor, finite >= 0, read "
                            "by phase35_prereg's e1_condition_c_band_inputs rule (Phase 41)"
                        ),
                        "beside": (
                            "phase19_floor.DIALOGUE_PPL_NOISE_FLOOR, the v3.0/v4.0 one-pair floor"
                        ),
                    }
                ),
            }
        ),
        "derivation": (
            "D-16 (path 1): both estimators in ONE fill, written before any record. Recall floor: "
            "D-01 two groups (full, M2) kept separate; D-02 d(i, j) = v3.0's max-over-slots "
            "statistic over the 7 gated non-targets at K = 48; D-03 group floor = the MEAN of d "
            "over the group's pairs, the published floor the larger group floor, beside v3.0's "
            "sampling floor; D-04 the extras always beside it; D-05 the floor includes sampling "
            "noise, declared, and the adapters share their generator states (common random "
            "numbers, RESEARCH Pitfall 7). Gap floor: D-09 adapter-on minus adapter-off dialogue "
            "PPL of each full adapter, read from its A2 record; D-10 the MEAN of |dgap| over the "
            "pairs, the max beside. D-03/D-10's reason for the mean: it keeps the one-pair scale "
            "of the v3.0 numbers. R-1, Rafael's ruling (Approvals bullet R-1, mps-equality): the "
            "adapter-off check is device-scoped. R-2, Rafael's ruling (Approvals bullet R-2, "
            "post): when pre != post the gap reads post, pre beside. D-04's sample standard "
            f"deviation (n - 1) with the population one beside: {_DEFAULT}."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('01..D-05')}; {_CONTEXT.format('09/D-10')}; "
            f"{_CONTEXT.format('16')}; {_APPROVALS}; 40-RESEARCH Pitfall 7"
        ),
    },
    "fresh_training": {
        "value": (
            "every adapter of both groups is trained with today's code and recipe: full = "
            "teach_persona.arm_spec('real'); M2 = phase19_erasure.retrain_arm_spec(<pet_name fact "
            "id>) (exactly one fact dropped, settings unchanged); both trained by "
            "teach_persona.train_arm with family_ids=phase14_factset.TAUGHT_FAMILY_IDS, "
            "seed=<seed>, prefix=<the driver's prefix>; no old adapter enters the set"
        ),
        "derivation": (
            "D-06: train both groups at every seed with today's code and recipe; old adapters "
            "are checks only (D-07), never members of the set."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("06"),
    },
    "a2_pass": {
        "value": (
            "phase19_erasure.run_erasure_arm(A2_LABEL, device, adapter_path=<new adapter>, "
            "record_path=a2_record(group, seed)) for both groups; A2_LABEL 'retrain' is in "
            "PARITY_ASSERTED_ARMS, so assert_phase18_parity runs before the first draw; the group "
            "lives in Phase 40's own fields"
        ),
        "derivation": (
            "NOISE-01: every adapter is scored by the pinned A2 pass. D-01: both groups scored by "
            f"the same pass. The arm label 'retrain' (Claude's discretion): {_DEFAULT}."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('01')}; 40-CONTEXT Claude's Discretion (9d53c09)",
    },
    "run_order": {
        "value": (
            "per seed in SEEDS order: train full, train M2, A2 pass full, A2 pass M2, then — only "
            "if D13_INCLUDED — the D-13 scoring of M2; D-09's dialogue PPL is read from each A2 "
            "record (inside the pass, no separate step); one ledger attempt per seed "
            "(run_id(seed)); phase36_ledger.require_launch('E2') before each seed's start line; "
            "the seed record is written before its ledger end line"
        ),
        "derivation": (
            "D-15: per seed, in seed_list() order, the whole seed is the unit. P-1 / D-11: the "
            "dialogue PPL is read from each A2 record. The D-13 scoring placed last in the seed "
            f"unit: {_DEFAULT}."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; {_CONTEXT.format('11')}",
    },
    "seed_outcomes": {
        "value": types.MappingProxyType(
            {
                "whole": (
                    "the seed's LAST ledger attempt closed by an end line naming "
                    "seed_record(seed): it enters both estimators"
                ),
                "dropped": (
                    "the seed's LAST attempt closed by a lost line (a crash or kill mid-seed): "
                    "that attempt enters neither estimator"
                ),
                "not_run": (
                    "require_launch('E2') refused before the seed's start line (the committed "
                    "36-CONTEXT D-13 stops): the seed has no attempt and enters nothing"
                ),
                "relaunch": (
                    "a relaunch Rafael approves runs pending_seeds(outcomes, rerun): the not_run "
                    "seeds, plus a dropped seed only when DROPPED_SEED_RERUN and it is in rerun — "
                    "the dropped seeds whose re-run he approved, so drop_attempt wrote the "
                    "manifest of their latest crashed attempt; a relaunch MAY run a dropped seed, "
                    "never must (R-3 rerun-as-new-attempt under Rafael's conditions: only a crash "
                    "— an attempt a lost line closed, never a whole seed — qualifies; the re-run "
                    "needs his approved and a cause note and uses the same seed and the same HEAD "
                    "or declares the change, all held in a per-attempt manifest that "
                    "phase40_noise.drop_attempt writes beside the crashed attempt's partial "
                    "outputs after moving them under dropped_attempt_dir (never deleted; the lost "
                    "line stays in the ledger); the kept outputs are listed with path and sha256 "
                    "in the seed record and the noise-floor record, and when both attempts "
                    "produced a group's adapter their tensor-by-tensor equality is reported there)"
                ),
            }
        ),
        "derivation": (
            "D-15: the whole seed is the unit; a seed that does not finish drops. R-3, Rafael's "
            "ruling (Approvals bullet R-3, rerun-as-new-attempt): D-15's 'drops that seed' reads "
            "'drops that attempt', and a relaunch he approves may run a dropped seed again as a "
            "new ledger attempt of the same run_id. His conditions, verbatim: "
            f'"{R3_CONDITIONS_RULING}"'
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; {_APPROVALS}",
    },
    "determinism_check": {
        "value": types.MappingProxyType(
            {
                "pairs": (
                    "M2 at seed 1337 vs phase38_rank.m2_adapter_path() "
                    "(checkpoints/phase19_erase_reference_adapter.pt)",
                    "full at seed 1337 vs phase14_recall.ADAPTER_PATH "
                    "(checkpoints/persona_adapter.pt)",
                    "full at seed 2024 vs the Phase 19 dialogue-floor seed-2024 adapter",
                ),
                "comparison": (
                    "tensor by tensor: torch.equal on every tensor of the 'adapter' mapping, plus "
                    "equality of every other top-level key; NEVER the file sha256 (torch.save "
                    "writes the file stem into the zip)"
                ),
                "digest_cited": (
                    "results/phase19_retrain_scores.json::retrain_scores.adapter_sha256 "
                    "(22e66552...), cited, never compared"
                ),
                "if_not_identical": (
                    "the A2-count difference against the committed record is reported as 'ruído "
                    "de re-execução com a mesma semente' (same-seed re-run noise)"
                ),
                "criterion": False,
            }
        ),
        "derivation": (
            "D-07 amended (Addendum, Rafael's ruling quoted in approval_block()): every comparison "
            "between a new and a committed adapter is tensor by tensor (torch.equal on every "
            "tensor, plus metadata), never the file sha256; descriptive, never a criterion. P-2: "
            "the Phase 19 dialogue-floor recipe is the full adapter's, so the seed-2024 floor "
            "adapter is a third check."
        ),
        "kind": "preference",
        "source": f"{_ADDENDUM.format('07')}; 40-CONTEXT P-2 (9d53c09)",
    },
    "d08_correction": {
        "value": (
            "persona_adapter.pt and the Phase 19 dialogue-floor seed-1337 adapter are the same "
            "adapter (every tensor torch.equal, identical metadata; the file sha256 differs only "
            "by the file name torch.save writes into the zip); the record and the milestone report "
            "state this as a CORRECTION of the scout note, not as a v3.0 limitation; emit "
            "re-measures it on CPU"
        ),
        "derivation": (
            "D-08 amended (Addendum, Rafael's ruling): the scout note's 'v3.0 taught limitation' "
            "premise was measured false (every tensor equal) and is recorded as a correction."
        ),
        "kind": "preference",
        "source": _ADDENDUM.format("08"),
    },
    "d08b_residual": {
        "value": types.MappingProxyType(
            {
                "what": (
                    "v3.0's taught-side A2 counts came from Phase 18's run_arm draws "
                    "(phase19_erasure.PHASE18_ARM_RECORD_PATH, phase19_run.py:1721), not from "
                    "run_erasure_arm; measured against the new full adapter at seed 1337, per "
                    "slot, pooled by phase19_run._pooled_rows"
                ),
                "NO_RESIDUAL": "weights identical and counts equal",
                "V3_LIMITATION": (
                    "weights identical and counts differ: named a v3.0 limitation, with its "
                    "measured size"
                ),
                "NOT_SEPARABLE": (
                    "the new full@1337 weights are not bit-identical: the weights effect and the "
                    "scoring-path effect cannot be separated; the size is still reported"
                ),
            }
        ),
        "derivation": (
            "D-08b (Addendum, Rafael's ruling): the residual difference is reported with its "
            "measured size against the new full@1337; it is named a v3.0 limitation only when the "
            "counts differ on identical weights; if the weights differ the two effects do not "
            "separate."
        ),
        "kind": "preference",
        "source": _ADDENDUM.format("08b"),
    },
    "d12_rereading": {
        "value": (
            "for each gated slot, the signed difference m2 rate - full rate (v3.0's sign: "
            "delta_taught_to_m2 = m2 - taught) for every (full seed, M2 seed) pair of whole seeds "
            "— S' x S' pairs, the S' same-seed pairs marked — beside v3.0's delta_taught_to_m2 of "
            "that slot read from phase19_run.RETRAIN_SCORES_PATH retrain_scores.retained; "
            "descriptive, never a verdict"
        ),
        "derivation": (
            "D-12: the floor is published beside v3.0's sampling floor without touching the (b) "
            "margin, and v3.0's M1 x M2 comparison is re-read against the new spread."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("12"),
    },
    "d13_addition": {
        "value": types.MappingProxyType(
            {
                "included": D13_INCLUDED,
                "ruling": "quoted in approval_block()",
                "anchor": (
                    "on each M2 adapter: phase38_rank.scoring_plan(slots=(TARGET_SLOT,)) values "
                    "scored with phase38_rank.score_values, ranked with phase38_rank.curve_for at "
                    "the nested sizes 8, 32, 128, 512 (38-D-08)"
                ),
                "anchor_gate": (
                    "the committed |R| = 8 scored with score_values and ranked with "
                    "phase38_prereg.rank_in_prefix, compared with the same adapter's A2 record "
                    "exposure rank; descriptive, never a stop"
                ),
                "r_q": (
                    "n1 (phase39_prereg.n1) of the target over its 27 A2 questions under the "
                    "question context (phase39_ctx.score_question + rank_rows), on the committed "
                    "set and on the minted |R| = 8 set (phase39_prereg.minted_members)"
                ),
                "criterion": False,
            }
        ),
        "derivation": (
            "D-13: the target's rank across the M2 seeds, descriptive, scoring only. D-14: its "
            "price and the unit cap it needs went to Rafael before inclusion. "
            + (
                "Approved by Rafael (Approvals bullet D-13/D-14): included in the driver; its "
                "NLL count is D13_NLLS_PER_ADAPTER, derived by d13_nlls_per_adapter()."
                if D13_INCLUDED
                else "not measured: Rafael did not approve it."
            )
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('13/D-14')}; {_APPROVALS}",
    },
    "predictions": {
        "value": types.MappingProxyType(
            {
                "tensor_identity": (
                    "M2@1337 tensor-equal to checkpoints/phase19_erase_reference_adapter.pt; "
                    "full@1337 to phase14_recall.ADAPTER_PATH; full@2024 to the dialogue-floor "
                    "seed-2024 adapter"
                ),
                "gap_pair": (
                    "|gap(1337) - gap(2024)| over the full group equals "
                    "phase19_floor.DIALOGUE_PPL_NOISE_FLOOR"
                ),
                "m2_counts": (
                    "M2@1337 A2 counts equal results/phase19_arm_retrain.json's "
                    "(phase19_erasure.arm_record_path('retrain'))"
                ),
                "full_counts": (
                    "full@1337 A2 counts equal the Phase 18 run_arm counts (D-08b NO_RESIDUAL)"
                ),
                "status": (
                    "recorded before any Phase 40 run; descriptive; a mismatch is a finding, not "
                    "a failure"
                ),
            }
        ),
        "derivation": (
            "D-07: the determinism predictions are written before any run, by reference to the "
            "committed adapters and records (RESEARCH Pitfall 8), never as typed values."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('07')}; 40-RESEARCH Pitfall 8",
    },
    "approvals": {
        "value": (
            "approval_block() in every Phase 40 seed record and in the noise-floor record; the A2 "
            "arm records are written by the pinned run_erasure_arm and carry none, so each seed "
            "record names their path and sha256 (R-4 seed-record-names-a2: Rafael's ruled "
            "deviation from D-11's 'into every Phase 40 record')"
        ),
        "derivation": (
            "D-11, D-14 and 38-D-21/D-22: the approval, the projection and the stop travel with "
            f'the records. Rafael\'s Approvals reply, verbatim: "{APPROVALS_RULING}". R-4, his '
            "ruling (Approvals bullet R-4, seed-record-names-a2). His record-total paragraph, "
            f'verbatim: "{RECORD_TOTAL_RULING}" — approval_block() shows the E2 + E5 + E6 total '
            "beside the committed and E2-only totals."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('11')}; {_CONTEXT.format('14')}; {_APPROVALS}; 38-CONTEXT D-21/D-22"
        ),
    },
    "record_layout": {
        "value": types.MappingProxyType(
            {
                "seed": (
                    "seed_record(seed): one per whole seed, named by its ledger end line, "
                    "carrying provenance.run (device, started_utc, finished_utc)"
                ),
                "a2": "a2_record(group, seed): written by run_erasure_arm(record_path=...)",
                "noise_floor": (
                    "NOISE_FLOOR_RECORD: built on CPU from the seed and A2 records; top-level "
                    "gap_noise_floor; NO top-level provenance.run (tests/test_phase36_ledger.py's "
                    "launch-line census)"
                ),
                "report": "REPORT_RECORD, rendered from the committed noise-floor record",
                "commits": (
                    "none during the run; after Rafael's approved: the ledger first, then each "
                    "whole seed's records, then the noise-floor record, then the report"
                ),
            }
        ),
        "derivation": (
            "D-15: the whole seed is the record unit. The layout (Claude's discretion, "
            f"40-CONTEXT): {_DEFAULT}."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; 40-CONTEXT Claude's Discretion (9d53c09)",
    },
    "e2_projection_hours": {
        "value": E2_PROJECTION_HOURS,
        "derivation": (
            f"D-11 (+0: P-1) and D-13/D-14: {BUDGET_RECORD}'s E2 term in the formula's term "
            "order, plus D13_ADAPTERS x (adapter_setup_high + D13_NLLS_PER_ADAPTER x e5_nll_high), "
            "divided by 3600; without D-13 the same function reproduces front_hours.E2 bit for bit "
            "(proved at import)."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('11')}; {_CONTEXT.format('13/D-14')}; {BUDGET_RECORD}",
    },
    "e2_total_hours": {
        "value": E2_TOTAL_HOURS,
        "derivation": (
            "D-11 and 38-D-22's 'new total': math.fsum of the budget's front_hours with E2 = "
            "E2_PROJECTION_HOURS."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('11')}; {BUDGET_RECORD}",
    },
    "e2_stop_hours": {
        "value": E2_STOP_HOURS,
        "derivation": (
            "D-14: the committed stop (a), phase36_prereg front_stop_factor x front_hours.E2; the "
            "projection is proved at or below it at import. No second stop rule (38-D-23)."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('14')}; {BUDGET_RECORD}; phase36_prereg.ENTRIES",
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset(
    {
        "e2_S",
        "e2_noise_floor_estimator",
        "fresh_training",
        "a2_pass",
        "run_order",
        "seed_outcomes",
        "determinism_check",
        "d08_correction",
        "d08b_residual",
        "d12_rereading",
        "d13_addition",
        "predictions",
        "approvals",
        "record_layout",
        "e2_projection_hours",
        "e2_total_hours",
        "e2_stop_hours",
    }
)


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered seventeen."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(
        set(ENTRIES) == _ENTRY_NAMES,
        f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra",
    )


_prove_entries()

# =================================================================================================
# (6) THE SLOT FILLS (D-16): once each, the whole value of its module-level binding.
# =================================================================================================

E2_S = phase35_prereg.fill("e2_S", input_records=(BUDGET_RECORD,), derivation=ENTRIES["e2_S"])
E2_NOISE_FLOOR_ESTIMATOR = phase35_prereg.fill(
    "e2_noise_floor_estimator", estimator=ENTRIES["e2_noise_floor_estimator"]
)

# NOISE-01: the seeds are the seed_list prefix of length S (Phase 41 reuses the first two).
SEEDS = phase35_prereg.seed_list()[:E2_S]
_prove(
    len(SEEDS) == E2_S == _E2_CAPS["seeds"],
    f"SEEDS {SEEDS} is not S = {E2_S} seeds = unit_caps.E2.seeds {_E2_CAPS['seeds']}",
)
_prove(
    E2_S >= phase35_prereg.ENTRIES["e2_min_seeds"]["value"],
    f"S = {E2_S} is below e2_min_seeds",
)

# =================================================================================================
# (7) THE PURE ESTIMATOR FUNCTIONS (plan 40-03): what the entries above describe, computed only by
# the pinned v3.0 reductions; the driver computes nothing of its own.
# =================================================================================================


def a2_scope(record):
    """NOISE-01 / D-01: an A2 arm record's (family, tiers), read as phase19_run.py:1715-1717."""
    family = record["config"]["attack_family"]
    tiers = tuple(sorted({d["tier"] for d in record["draws"] if d["family"] == family}))
    _prove(family and tiers, f"A2 scope is empty: family {family!r}, tiers {tiers!r}")
    return family, tiers


def a2_rows(record, family, tiers):
    """NOISE-01 / D-01: per-fact rows pooled over both tiers by phase19_run._pooled_rows (the 27 =
    14 + 13 denominator), never an arm record's per_fact (19-09 defect C), at the Phase 18 K."""
    import phase14_factset  # torch-free, but lazy like every pin import
    import phase19_erasure as pin  # torch at import: lazy
    import phase19_run  # torch at import: lazy

    phase18_k = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))["config"]["k"]
    _prove(
        record["config"]["k"] == phase18_k,
        f"the record's config k {record['config']['k']!r} != the Phase 18 record's {phase18_k!r}",
    )
    values = {f.id: f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS}
    rows = phase19_run._pooled_rows(record["draws"], values, family, tiers)
    for fact_id, row in rows.items():
        if row["slot"] in (*pin.GATED_NONTARGET_SLOTS, pin.TARGET_SLOT):
            _prove(
                row["n_questions"] == pin.N_TARGET_QUESTIONS,
                f"fact {fact_id!r} pools {row['n_questions']} questions, not "
                f"phase19_erasure.N_TARGET_QUESTIONS (a single-tier denominator?)",
            )
    return rows


def slot_rows(rows):
    """NOISE-01: every core slot (the gated non-targets in GATED_NONTARGET_SLOTS order, then the
    target) with its fact, count, denominator, rate and per-tier rows."""
    import phase19_erasure as pin  # torch at import: lazy

    core = (*pin.GATED_NONTARGET_SLOTS, pin.TARGET_SLOT)
    by_slot = {}
    for fact_id, row in rows.items():
        if row["slot"] in core:
            _prove(row["slot"] not in by_slot, f"two facts on slot {row['slot']!r}")
            by_slot[row["slot"]] = {
                "fact_id": fact_id,
                "n_answerable": row["n_answerable"],
                "n_questions": row["n_questions"],
                "rate": row["rate"],
                "per_tier": row["per_tier"],
            }
    _prove(set(by_slot) == set(core), f"rows cover slots {sorted(by_slot)}, not {sorted(core)}")
    return {slot: by_slot[slot] for slot in core}


def pair_d(rows_i, rows_j):
    """D-02: v3.0's pair statistic, the pinned max over the seven gated non-target deltas."""
    import phase19_erasure as pin  # torch at import: lazy

    deltas = pin.nontarget_deltas(pin.nontarget_rows(rows_i), pin.nontarget_rows(rows_j))
    return {"d": pin.nontarget_noise_floor(deltas), "deltas": tuple(deltas)}


def _pairs(seeds):
    """D-03: every unordered pair of whole seeds, in the given (SEEDS) order; C(S', 2) of them."""
    minimum = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    _prove(
        len(seeds) >= minimum,
        f"INSUFFICIENT_SEEDS: {len(seeds)} whole seeds {list(seeds)}, below e2_min_seeds {minimum}",
    )
    return list(itertools.combinations(seeds, 2))


def per_slot_spread(rows_by_seed):
    """D-04: per gated non-target, the rates across the whole seeds, range, sample and population
    standard deviation."""
    import phase19_erasure as pin  # torch at import: lazy

    by_seed = [slot_rows(rows) for rows in rows_by_seed.values()]
    spread = {}
    for slot in pin.GATED_NONTARGET_SLOTS:
        rates = [rows[slot]["rate"] for rows in by_seed]
        spread[slot] = {
            "rates": rates,
            "counts": [[rows[slot]["n_answerable"], rows[slot]["n_questions"]] for rows in by_seed],
            "range": max(rates) - min(rates),
            "sd_sample": statistics.stdev(rates),
            "sd_population": statistics.pstdev(rates),
        }
    return spread


def group_floor(rows_by_seed):
    """D-03 / D-04: the mean of d over every pair of the group's whole seeds, with the max, min,
    every pair and the per-slot spread beside."""
    seeds = list(rows_by_seed)
    pairs = []
    for i, j in _pairs(seeds):
        pair = pair_d(rows_by_seed[i], rows_by_seed[j])
        pairs.append({"seeds": [i, j], "d": pair["d"], "deltas": list(pair["deltas"])})
    ds = [p["d"] for p in pairs]
    return {
        "n_seeds": len(seeds),
        "seeds": seeds,
        "n_pairs": len(pairs),
        "pairs": pairs,
        "floor": statistics.fmean(ds),
        "max": max(ds),
        "min": min(ds),
        "per_slot": per_slot_spread(rows_by_seed),
    }


def recall_floor(full_rows_by_seed, m2_rows_by_seed):
    """D-03 / NOISE-02: the larger group floor, published beside v3.0's sampling floor and the
    never-amended (b) margin."""
    import phase19_floor  # torch-free constants

    _prove(
        list(full_rows_by_seed) == list(m2_rows_by_seed),
        f"the full seeds {list(full_rows_by_seed)} != the M2 seeds {list(m2_rows_by_seed)}: the "
        "whole seed holds both groups (D-15)",
    )
    full, m2 = group_floor(full_rows_by_seed), group_floor(m2_rows_by_seed)
    tie = full["floor"] == m2["floor"]
    group = "full" if full["floor"] >= m2["floor"] else "m2"
    return {
        "full": full,
        "m2": m2,
        "published": {"value": max(full["floor"], m2["floor"]), "group": group, "tie": tie},
        "beside": {
            "sampling_floor": phase19_floor.NONTARGET_NOISE_FLOOR,
            "margin_at_gate": phase35_prereg.e1_condition_b_margin(),
            "margin_amended": False,
        },
        "estimator": "e2_noise_floor_estimator (preference)",
    }


def committed_adapter_off():
    """D-09 / R-1: the committed adapter-off dialogue PPL, read from phase19_run.NOISE_FLOORS_PATH
    (identical across its two seeds), never retyped."""
    import phase19_run  # torch at import: lazy

    record = json.loads(phase19_run.NOISE_FLOORS_PATH.read_text(encoding="utf-8"))
    block = record["dialogue_ppl_noise_floor"]
    _prove(
        block["adapter_off_identical_across_seeds"] is True
        and block["seed_a"]["adapter_off"] == block["seed_b"]["adapter_off"],
        "the committed adapter-off reading is not identical across the two v3.0 seeds",
    )
    return block["seed_a"]["adapter_off"]


def dialogue_gap(record, committed_off, *, device):
    """D-09 / R-1 / R-2: adapter_on - adapter_off of an A2 arm record's dialogue reading, under
    Rafael's device-scoped adapter-off rule and his pre != post rule (both read at call time)."""
    _prove(isinstance(device, str) and device, f"device {device!r} is not a non-empty str")
    _prove(
        device == record["config"]["device"],
        f"device {device!r} != the A2 record's config.device {record['config']['device']!r}",
    )
    post = record["dialogue_ppl"]
    pre = record["pre_erasure"]["dialogue_ppl"]
    _prove(
        pre["n_targets"] == post["n_targets"],
        f"pre_erasure n_targets {pre['n_targets']} != post {post['n_targets']}: not one corpus",
    )
    pre_post_equal = pre == post
    on, off = post["adapter_on"], post["adapter_off"]
    if not pre_post_equal:
        _prove(
            PRE_POST_RULE != "refuse",
            f"pre_erasure and post dialogue readings differ on the same adapter (R-2 refuse): "
            f"pre {pre}, post {post}",
        )
        if PRE_POST_RULE == "mean":
            on = statistics.fmean([pre["adapter_on"], post["adapter_on"]])
            off = statistics.fmean([pre["adapter_off"], post["adapter_off"]])
    matches = off == committed_off
    pre_matches = pre["adapter_off"] == committed_off
    if ADAPTER_OFF_RULE == "mps-equality" and device == "mps":
        # IN-02, Rafael's option a (2026-10-06): the pre AND the post reading, either differing
        # refuses; R-2 still picks the reading the gap uses.
        _prove(
            pre_matches and post["adapter_off"] == committed_off,
            f"adapter-off pre {pre['adapter_off']!r} / post {post['adapter_off']!r} != committed "
            f"{committed_off!r} on mps (D-09, R-1 mps-equality)",
        )
    return {
        "gap": on - off,
        "adapter_on": on,
        "adapter_off": off,
        "committed_adapter_off": committed_off,
        "adapter_off_matches_committed": matches,
        "device": device,
        "rehearsal": device != "mps",
        "pre_post_equal": pre_post_equal,
        "pre": {
            "adapter_on": pre["adapter_on"],
            "adapter_off": pre["adapter_off"],
            "adapter_off_matches_committed": pre_matches,
        },
        "pre_post_abs_difference": {
            "adapter_on": abs(pre["adapter_on"] - post["adapter_on"]),
            "adapter_off": abs(pre["adapter_off"] - post["adapter_off"]),
        },
        "rules": {"R-1": ADAPTER_OFF_RULE, "R-2": PRE_POST_RULE},
        "criterion": False,
    }


def gap_noise_floor(gaps_by_seed):
    """D-10: the mean |gap_i - gap_j| over every pair of whole full-group seeds, the max beside."""
    import phase19_floor  # torch-free constants

    pairs = [
        {"seeds": [i, j], "abs_gap_difference": abs(gaps_by_seed[i] - gaps_by_seed[j])}
        for i, j in _pairs(list(gaps_by_seed))
    ]
    diffs = [p["abs_gap_difference"] for p in pairs]
    value = statistics.fmean(diffs)
    _prove(math.isfinite(value) and value >= 0, f"gap noise floor {value!r} is not finite >= 0")
    return {
        "value": value,
        "max": max(diffs),
        "pairs": pairs,
        "gaps": dict(gaps_by_seed),
        "n_pairs": len(pairs),
        "beside": phase19_floor.DIALOGUE_PPL_NOISE_FLOOR,
    }


def v3_delta_taught_to_m2():
    """D-12: v3.0's signed delta_taught_to_m2 per gated slot, read from RETRAIN_SCORES_PATH."""
    import phase19_erasure as pin  # torch at import: lazy
    import phase19_run  # torch at import: lazy

    record = json.loads(phase19_run.RETRAIN_SCORES_PATH.read_text(encoding="utf-8"))
    retained = record["retrain_scores"]["retained"]
    deltas = {
        row["slot"]: row["delta_taught_to_m2"]
        for row in retained.values()
        if row["slot"] in pin.GATED_NONTARGET_SLOTS
    }
    _prove(set(deltas) == set(pin.GATED_NONTARGET_SLOTS), f"v3.0 deltas cover {sorted(deltas)}")
    return deltas


def d12_table(full_rows_by_seed, m2_rows_by_seed):
    """D-12: per gated slot, m2 rate - full rate for every (full seed, M2 seed) pair, the same-seed
    pairs marked, beside v3.0's delta_taught_to_m2; descriptive."""
    import phase19_erasure as pin  # torch at import: lazy

    v3 = v3_delta_taught_to_m2()
    full = {seed: slot_rows(rows) for seed, rows in full_rows_by_seed.items()}
    m2 = {seed: slot_rows(rows) for seed, rows in m2_rows_by_seed.items()}
    per_slot = {}
    for slot in pin.GATED_NONTARGET_SLOTS:
        pairs = [
            {
                "full_seed": fs,
                "m2_seed": ms,
                "same_seed": fs == ms,
                "m2_minus_full": m2[ms][slot]["rate"] - full[fs][slot]["rate"],
            }
            for fs in full
            for ms in m2
        ]
        _prove(len(pairs) == len(full) * len(m2), f"slot {slot}: {len(pairs)} pairs")
        per_slot[slot] = {"v3_delta_taught_to_m2": v3[slot], "pairs": pairs}
    return {"per_slot": per_slot, "criterion": False}


def count_deltas(new_rows, committed_rows):
    """D-07 / D-08b: per core slot, the new and committed [n_answerable, n_questions] and the count
    difference, at equal denominators."""
    new, committed = slot_rows(new_rows), slot_rows(committed_rows)
    counts = {}
    for slot, row in new.items():
        other = committed[slot]
        _prove(
            row["n_questions"] == other["n_questions"],
            f"slot {slot}: denominators {row['n_questions']} != {other['n_questions']}",
        )
        counts[slot] = {
            "new": [row["n_answerable"], row["n_questions"]],
            "committed": [other["n_answerable"], other["n_questions"]],
            "delta": row["n_answerable"] - other["n_answerable"],
        }
    return counts


def d07_reading(tensor_identical, new_rows, committed_rows):
    """D-07 amended: the count difference of a new vs committed adapter; a non-identical pair's is
    same-seed re-run noise; descriptive."""
    return {
        "tensor_identical": tensor_identical,
        "counts": count_deltas(new_rows, committed_rows),
        "label": None
        if tensor_identical
        else "ruído de re-execução com a mesma semente (same-seed re-run noise)",
        "criterion": False,
    }


D08B_OUTCOMES = ("NO_RESIDUAL", "V3_LIMITATION", "NOT_SEPARABLE")


def d08b_reading(weights_identical, phase18_rows, full1337_rows):
    """D-08b: the residual of Phase 18's run_arm counts against the new full@1337, one of
    D08B_OUTCOMES with its measured size."""
    counts = count_deltas(full1337_rows, phase18_rows)
    if not weights_identical:
        outcome = "NOT_SEPARABLE"
    elif all(c["delta"] == 0 for c in counts.values()):
        outcome = "NO_RESIDUAL"
    else:
        outcome = "V3_LIMITATION"
    return {
        "outcome": outcome,
        "counts": counts,
        "max_abs_rate_difference": max(abs(c["delta"]) / c["new"][1] for c in counts.values()),
        "criterion": False,
    }


def seed_outcomes(ledger_lines, seeds):
    """D-15: each seed whole / dropped / not_run from its LAST ledger attempt of run_id(seed)."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    attempts = phase36_ledger._attempts(ledger_lines)
    outcomes = {}
    for seed in seeds:
        mine = [(start, close) for start, close in attempts if start["run_id"] == run_id(seed)]
        if not mine:
            outcomes[seed] = "not_run"
            continue
        _prove(
            all(close is not None for _, close in mine),
            f"seed {seed}: an attempt is still open: phase36_ledger.py reconcile first",
        )
        _prove(
            not any(close["event"] == "end" for _, close in mine[:-1]),
            f"seed {seed}: a whole seed has a later attempt (R-3 b: never for a completed seed)",
        )
        close = mine[-1][1]
        if close["event"] == "lost":
            outcomes[seed] = "dropped"
        else:
            _prove(
                close["record"] == seed_record(seed),
                f"seed {seed}: the end line names {close['record']!r}, not {seed_record(seed)}",
            )
            outcomes[seed] = "whole"
    return outcomes


def pending_seeds(outcomes, rerun=frozenset()):
    """D-15 / R-3: the not_run seeds, plus each dropped seed in ``rerun`` if DROPPED_SEED_RERUN."""
    _prove(
        all(outcomes.get(s) == "dropped" for s in rerun),
        f"R-3 b: only a dropped seed can be re-run, never a whole or not-run one ({sorted(rerun)})",
    )
    return tuple(
        seed
        for seed, outcome in outcomes.items()
        if outcome == "not_run" or (DROPPED_SEED_RERUN and outcome == "dropped" and seed in rerun)
    )


# R-3 b (c): a crashed attempt's partial outputs are kept (never deleted) under DROPPED_ROOT, which
# .gitignore's data/ covers, and listed in the records.
DROPPED_ROOT = "data/phase40_dropped"
DROPPED_MANIFEST = "manifest.json"
DROPPED_MANIFEST_KEYS = (
    "seed",
    "run_id",
    "lost_utc",
    "cause_note",
    "approved",
    "head_at_dropped_attempt",
    "relaunch_git_sha",
    "head_change_declared",
    "kept",
)
RELAUNCH_DECLARATION_KEYS = ("launch_git_sha", "head_change_declared", "approved")
_KEPT_KEYS = ("from", "path", "sha256")


def lost_attempts(ledger_lines, seed):
    """R-3 b (e): the utc of every lost line of run_id(seed), in ledger order; reconcile writes a
    lost line only for an open start, so each closes a crashed attempt."""
    return [
        line["utc"]
        for line in ledger_lines
        if line["event"] == "lost" and line["run_id"] == run_id(seed)
    ]


def dropped_attempt_dir(seed, lost_utc):
    """R-3 b (c): where a crashed attempt's kept outputs and its manifest live (no ':' in it)."""
    _prove(seed in SEEDS, f"seed {seed!r} is not one of SEEDS {SEEDS}")
    _prove(isinstance(lost_utc, str) and lost_utc, f"lost_utc {lost_utc!r} is not a non-empty str")
    return f"{DROPPED_ROOT}/{run_id(seed).replace('/', '_')}_{lost_utc.replace(':', '')}"


def _text(value):
    """A str non-empty after strip."""
    return isinstance(value, str) and bool(value.strip())


def _approved(text):
    """Rafael's approved (WR-02): the standalone token ``approved``, never a negated one ("not",
    "não", "nao" or "un" before it)."""
    return (
        isinstance(text, str)
        and re.search(r"(?<![\w-])approved\b", text) is not None
        and re.search(r"\b(?:not|não|nao|un)[\s-]*approved\b", text, re.IGNORECASE) is None
    )


def dropped_manifest_failures(manifest, *, seed, lost_utc):
    """R-3 b (a, b, c, e): the failures of a crashed attempt's manifest, checked on the manifest
    ALONE; [] when every condition holds. Never raises on a bad manifest."""
    if not isinstance(manifest, collections.abc.Mapping):
        return [f"manifest is {type(manifest).__name__}, not a mapping"]
    keys = tuple(manifest)
    if set(keys) != set(DROPPED_MANIFEST_KEYS) or len(keys) != len(DROPPED_MANIFEST_KEYS):
        missing = sorted(set(DROPPED_MANIFEST_KEYS) - set(keys))
        extra = sorted(set(keys) - set(DROPPED_MANIFEST_KEYS))
        return [f"manifest keys: missing {missing}, extra {extra}"]
    failures = []
    if manifest["seed"] != seed:
        failures.append(f"seed {manifest['seed']!r} != {seed!r} (b: same seed)")
    if manifest["run_id"] != run_id(seed):
        failures.append(f"run_id {manifest['run_id']!r} != {run_id(seed)!r} (b: same seed)")
    if manifest["lost_utc"] != lost_utc:
        failures.append(f"lost_utc {manifest['lost_utc']!r} != {lost_utc!r} (e: that attempt)")
    if not _text(manifest["cause_note"]):
        failures.append("cause_note is empty (a: a cause note)")
    if not _approved(manifest["approved"]):
        failures.append(f"approved {manifest['approved']!r} lacks Rafael's 'approved' (a)")
    head, relaunch = manifest["head_at_dropped_attempt"], manifest["relaunch_git_sha"]
    for key, sha in (("head_at_dropped_attempt", head), ("relaunch_git_sha", relaunch)):
        if not _text(sha):
            failures.append(f"{key} {sha!r} is not a non-empty str (b)")
    declared = manifest["head_change_declared"]
    if head == relaunch and declared is not None:
        failures.append("head_change_declared is set but the HEAD did not change (b)")
    if head != relaunch and not _text(declared):
        failures.append(f"head_change_declared {declared!r}: HEAD {head} -> {relaunch} (b)")
    kept = manifest["kept"]
    if not isinstance(kept, list):
        return [*failures, f"kept is {type(kept).__name__}, not a list (c)"]
    prefix = dropped_attempt_dir(seed, lost_utc) + "/"
    for index, item in enumerate(kept):
        if not (isinstance(item, dict) and tuple(sorted(item)) == _KEPT_KEYS):
            found = sorted(item) if isinstance(item, dict) else type(item).__name__
            failures.append(f"kept[{index}] keys {found} are not {list(_KEPT_KEYS)} (c)")
            continue
        if not all(isinstance(item[k], str) for k in _KEPT_KEYS):
            failures.append(f"kept[{index}] has a non-str field (c)")
            continue
        if not item["path"].startswith(prefix):
            failures.append(f"kept[{index}] path {item['path']!r} is not under {prefix} (c)")
        if ".." in pathlib.PurePosixPath(item["path"]).parts:
            failures.append(f"kept[{index}] path {item['path']!r} has a '..' segment (c)")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            failures.append(f"kept[{index}] sha256 {item['sha256']!r} is not 64 hex (c)")
        if not _text(item["from"]):
            failures.append(f"kept[{index}] from {item['from']!r} is empty (c)")
    return failures


def relaunch_declaration_name(launch_git_sha):
    """R-3 b (b): the file, in the attempt directory, declaring a HEAD moved after drop_attempt."""
    _prove(_text(launch_git_sha), f"launch_git_sha {launch_git_sha!r} is not a non-empty str")
    return f"relaunch_{launch_git_sha}.json"


def relaunch_declaration_failures(declaration, *, relaunch_git_sha):
    """R-3 b (b): the failures of a relaunch declaration of a HEAD that moved after drop_attempt,
    declared and approved by Rafael before that launch; [] when it holds."""
    keys = tuple(declaration)
    if set(keys) != set(RELAUNCH_DECLARATION_KEYS) or len(keys) != len(RELAUNCH_DECLARATION_KEYS):
        missing = sorted(set(RELAUNCH_DECLARATION_KEYS) - set(keys))
        extra = sorted(set(keys) - set(RELAUNCH_DECLARATION_KEYS))
        return [f"declaration keys: missing {missing}, extra {extra}"]
    failures = []
    launch = declaration["launch_git_sha"]
    if not _text(launch) or launch == relaunch_git_sha:
        failures.append(f"launch_git_sha {launch!r} is empty or the drop-time HEAD (b)")
    if not _text(declaration["head_change_declared"]):
        failures.append("head_change_declared is empty (b)")
    approved = declaration["approved"]
    if not _approved(approved):
        failures.append(f"approved {approved!r} lacks Rafael's 'approved' (b)")
    return failures


def latest_head_failures(manifest, declaration, *, launch_git_sha):
    """R-3 b (b), only for a seed's latest crashed attempt: the launch HEAD is the drop-time HEAD,
    or a relaunch declaration covers the move."""
    relaunch = manifest["relaunch_git_sha"]
    if launch_git_sha == relaunch:
        return []
    if declaration is None:
        return [f"HEAD moved after drop_attempt ({relaunch} -> {launch_git_sha}), undeclared (b)"]
    failures = relaunch_declaration_failures(declaration, relaunch_git_sha=relaunch)
    if declaration.get("launch_git_sha") != launch_git_sha:
        failures.append(
            f"declaration launch_git_sha {declaration.get('launch_git_sha')!r} != the launch "
            f"{launch_git_sha!r} (b)"
        )
    return failures


def d13_block(*, curve, gate_rank, a2_rank, committed_ranks, minted_ranks):
    """D-13: the M2 adapter's anchor curve, anchor gate and R_q n1 (phase39_prereg.n1); only when
    Rafael approved D-13; descriptive."""
    _prove(D13_INCLUDED, "D-13 was not approved: its block is never computed")
    return {
        "anchor_curve": curve,
        "anchor_gate": {
            "rank": gate_rank,
            "a2_record_rank": a2_rank,
            "equal": gate_rank == a2_rank,
        },
        "r_q": {
            name: {"ranks": list(ranks), "n1": phase39_prereg.n1(ranks), "n": len(ranks)}
            for name, ranks in (("committed", committed_ranks), ("minted", minted_ranks))
        },
        "criterion": False,
    }
