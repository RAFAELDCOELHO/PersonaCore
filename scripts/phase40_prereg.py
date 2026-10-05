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
teach_persona and torch. Every other heavy import (phase19_erasure, phase19_run,
phase18_extraction, phase14_factset, phase38_rank, phase36_ledger) stays inside the function that
needs it. phase38_prereg and phase39_prereg are module-level imports for the E2 + E5 + E6 record
total; measured, importing them opens no checkpoints/ or data/ file.
"""

import collections.abc
import fnmatch
import json
import math
import pathlib
import sys

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
