"""Phase 39 pre-registration: the E6 entry subset, the written instrument x context decomposition
rule, the D-11 / D-26 / D-30 approval and its budget arithmetic, frozen before any
``results/phase39_*`` record (39-CONTEXT D-03, ROADMAP Phase 39 SC4, CTX-01/CTX-03).

This module fills the two Phase 35 slots owned by Phase 39 exactly once each, as the module-level
bindings ``E6_ENTRY_SUBSET`` and ``E6_DECOMPOSITION_RULE``. Under the Phase 35 slot-ordering leg (a)
every commit touching this file must strictly precede the first add of every ``results/phase39_*``
record, so the rule is written in full before any E6 number exists and cannot be fitted to it.

Plan 39-02 added the pure functions that implement the written rule to this same file (section
9). D-27: its code review (plan 39-03) runs before any rehearsal, and the rehearsal pins its sha256.
Any later correction is Rafael's ruling plus a dated continuation (``scripts/_addendum.py``), never
a silent edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). The projection and stop hours, the extra NLL counts and the entry count are computed at
import from committed records and closed constants, never typed.

Not torch-free at import: the e6_entry_subset fill calls ``phase35_prereg.a2_corpus_entries()``,
which imports phase18_extraction (torch). Every other heavy import stays inside a function.
"""

import collections
import collections.abc
import fnmatch
import hashlib
import json
import math
import pathlib
import re
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
import phase38_prereg  # noqa: E402  (same; torch-free; frozen: import only)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase39_*` file existed, tracked or untracked.
COMMITTED = "2026-10-04"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase39_prereg] {message}")


# =================================================================================================
# (2) THE ENTRY SCHEMA, BY REFERENCE to the v6.0 pre-registration's public tuples.
# =================================================================================================

ENTRY_FIELDS = phase35_prereg.ENTRY_FIELDS
KINDS = phase35_prereg.KINDS
FORBIDDEN_PHRASE = phase35_prereg.FORBIDDEN_PHRASE


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

RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase39_*")
CTX_RECORD = RECORD_GLOB.replace("*", "ctx.json")
REPORT_RECORD = RECORD_GLOB.replace("*", "ctx_report.md")
RECORDS = (CTX_RECORD, REPORT_RECORD)

for _path in RECORDS:
    _prove(fnmatch.fnmatch(_path, RECORD_GLOB), f"{_path} does not match {RECORD_GLOB}")
_prove(len(set(RECORDS)) == len(RECORDS), f"the record paths {RECORDS} are not distinct")

# The E6 anchor probe record, consumed by the e6_entry_subset fill beside phase38_prereg's E1 probe.
# tests/test_phase39_prereg.py proves it tracked and matching the slot's declared input pattern.
PROBE_E6_RECORD = "results/phase36_probe_e6.json"
BUDGET_RECORD = phase38_prereg.BUDGET_RECORD

# =================================================================================================
# (4) THE READINGS, BY REFERENCE to the frozen Phase 38 definitions.
# =================================================================================================

READINGS = phase38_prereg.READINGS
PREFIXES = phase38_prereg.PREFIXES
SLOTS = phase38_prereg.SLOTS
MARGIN = phase38_prereg.MARGIN
K = phase35_prereg.FULL_FIDELITY_K

# Ruling f (Rafael 2026-10-05, changing D-25): k = 0 is the reference of every reading's own
# context in both events and is never a cell.
REFERENCE_READING = f"k{PREFIXES[0]}"
_prove(REFERENCE_READING in READINGS, f"{REFERENCE_READING} is not a reading")
# D-11 (i): adapter-off is descriptive and never classified.
DESCRIPTIVE_READINGS = ("adapter_off",)
_prove(
    set(DESCRIPTIVE_READINGS) <= set(READINGS),
    f"the descriptive readings {DESCRIPTIVE_READINGS} are not readings {READINGS}",
)
# CTX-02's adapters, each with a committed A2 pin: the k0 reference, k8..k78 and M2.
CTX02_READINGS = tuple(r for r in READINGS if r not in DESCRIPTIVE_READINGS)
# Rulings f and g: the cells' readings in both events, k8..k78 and M2; never k0, never adapter-off.
CELL_READINGS = tuple(r for r in CTX02_READINGS if r != REFERENCE_READING)

EVENTS = ("collapse", "damage")  # D-16: classified for each separately
STATUSES = ("INTACT", "LOST", "UNREACHABLE_AT_SIZE", "ALREADY_AT_K0")
WR01_OUTCOMES = STATUSES[2:]
_prove(
    WR01_OUTCOMES
    == (
        phase38_prereg.relation(None, None, reachable=False),
        phase38_prereg.relation(PREFIXES[0], PREFIXES[1]),
    ),
    f"the WR-01 outcomes {WR01_OUTCOMES} are not phase38_prereg.relation's",
)
# D-15: the names exactly as 39-CONTEXT specifies them.
CLASSES = (
    "CONTEXT_SUFFICIENT",
    "INSTRUMENT_SUFFICIENT",
    "EITHER",
    "INTERACTION_ONLY",
    "NO_DISAGREEMENT",
)
# Ruling e (Rafael 2026-10-05): R_a LOST with G_q INTACT, counted apart, no sufficiency class.
REVERSE_DISAGREEMENT = "REVERSE_DISAGREEMENT"
# Every outcome a cell can take.
OUTCOMES = CLASSES + (REVERSE_DISAGREEMENT,) + WR01_OUTCOMES

# =================================================================================================
# (5) THE D-11 / D-26 / D-30 APPROVAL AND ITS ARITHMETIC, from the committed budget.
# =================================================================================================

_BUDGET = _read(BUDGET_RECORD)
_E6_CAPS = _BUDGET["unit_caps"]["E6"]

A2_REGENERATED_ENTRIES = _E6_CAPS["a2_regenerated_entries"]
_prove(
    A2_REGENERATED_ENTRIES == 0,
    f"unit_caps.E6.a2_regenerated_entries is {A2_REGENERATED_ENTRIES!r}; D-02 regenerates nothing",
)

# D-11 (i): Rafael's approval of adapter-off as the eighth adapter against the committed cap of 7;
# the one typed approval value.
APPROVED_E6_ADAPTERS = 8

COMMITTED_ADAPTER_CAP = _E6_CAPS["adapters"]
COMMITTED_ANCHOR_ADAPTER_CAP = _E6_CAPS["anchor_adapters"]
for _name, _cap in (
    ("adapters", COMMITTED_ADAPTER_CAP),
    ("anchor_adapters", COMMITTED_ANCHOR_ADAPTER_CAP),
):
    _prove(
        _cap == len(PREFIXES) + 1,
        f"the committed E6 {_name} cap is {_cap}, not the {len(PREFIXES)} prefixes plus M2; the "
        "D-11 deviation must stay visible against the cap it exceeds",
    )
_prove(
    len(READINGS) == APPROVED_E6_ADAPTERS,
    f"{len(READINGS)} readings, but D-11 approved {APPROVED_E6_ADAPTERS}",
)

# D-11 (ii) at |R| = the budget's priced candidates per slot = Phase 38's first nested size (D-09).
MINTED_SET_SIZE = _BUDGET["unit_prices"]["e5_candidates_per_slot_max"]
_prove(
    MINTED_SET_SIZE == phase38_prereg.NESTED_SIZES[0],
    f"the priced |R| {MINTED_SET_SIZE} is not Phase 38's first nested size",
)

N_ENTRIES = len(phase35_prereg.a2_corpus_entries())
# The questions per slot (R_q's and G_q's n), derived: each slot holds the same share of entries.
N_QUESTIONS = N_ENTRIES // len(SLOTS)
_prove(
    collections.Counter(e["slot"] for e in phase35_prereg.a2_corpus_entries())
    == dict.fromkeys(SLOTS, N_QUESTIONS),
    f"the A2 entries are not {N_QUESTIONS} per slot of {SLOTS}",
)


def _reference_total():
    """The committed reference-set sizes summed over the slots (the actual gate cells)."""
    import phase18_extraction  # torch at import: lazy

    return sum(len(phase18_extraction.reference_set_for(slot)) for slot in SLOTS)


# D-26: (ii) on all eight adapters, the taught value's NLL shared with R_q.
MINTED_EXTRA_NLLS = APPROVED_E6_ADAPTERS * N_ENTRIES * (MINTED_SET_SIZE - 1)
# D-30 condition 1: the gate scored twice, priced as the formula prices the gate ...
GATE_EXTRA_NLLS_PRICED = APPROVED_E6_ADAPTERS * _E6_CAPS["anchor_slots"] * MINTED_SET_SIZE
# ... and at the actual committed reference-set cells.
GATE_EXTRA_NLLS_ACTUAL = APPROVED_E6_ADAPTERS * _reference_total()


def e6_projection_hours(adapters, anchor_adapters, extra_nlls=0):
    """The budget's E6 term at ``adapters`` / ``anchor_adapters``, plus ``extra_nlls`` priced at
    ``e5_nll_high``, in hours (D-11, D-26, D-30).

    The term order is scripts/phase36_budget.py's, left to right: only in this order does the 7/7
    value reproduce ``front_hours.E6`` bit for bit (floating point is not associative).
    """
    p = _BUDGET["unit_prices"]
    c = _E6_CAPS
    return (
        adapters
        * (
            p["adapter_setup_high"]
            + c["a2_regenerated_entries"] * p["a2_question_k48_high"] * c["max_k"] / K
            + (c["entries"] + c["anchor_slots"])
            * p["e5_candidates_per_slot_max"]
            * p["e5_nll_high"]
        )
        + anchor_adapters * c["anchor_slots"] * c["max_k"] * p["e6_anchor_draw_high"]
    ) / 3600 + extra_nlls * p["e5_nll_high"] / 3600


_prove(
    e6_projection_hours(COMMITTED_ADAPTER_CAP, COMMITTED_ANCHOR_ADAPTER_CAP)
    == _BUDGET["front_hours"]["E6"],
    "the E6 formula at the committed caps does not reproduce front_hours.E6",
)
E6_PROJECTION_HOURS = e6_projection_hours(
    APPROVED_E6_ADAPTERS, APPROVED_E6_ADAPTERS, MINTED_EXTRA_NLLS + GATE_EXTRA_NLLS_PRICED
)
E6_PROJECTION_HOURS_ACTUAL_GATE = e6_projection_hours(
    APPROVED_E6_ADAPTERS, APPROVED_E6_ADAPTERS, MINTED_EXTRA_NLLS + GATE_EXTRA_NLLS_ACTUAL
)
E6_STOP_HOURS = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _BUDGET["front_hours"]["E6"]
for _hours in (E6_PROJECTION_HOURS, E6_PROJECTION_HOURS_ACTUAL_GATE):
    _prove(
        _hours <= E6_STOP_HOURS,
        f"the E6 projection {_hours!r} h exceeds the committed stop {E6_STOP_HOURS!r} h "
        "(front_stop_factor x front_hours.E6). This projection goes to Rafael BEFORE launch; D-03 "
        "forbids a second stop rule, so nothing runs until he rules.",
    )

D11_RULING = (
    "Opção 1: aprovo (i) adaptador desligado como oitavo adaptador e (ii) os conjuntos cunhados "
    "da Fase 38 sob a pergunta inteira em |R| = 8 (D-09). approved"
)
D26_RULING = "Yes, add adapter-off"

# =================================================================================================
# (6) THE EIGHT A2 RECORD PINS (D-02, D-11 i): seven parsed from the budget's ruling, one typed.
# =================================================================================================

_PIN = re.compile(r"(k = \d+|M2): (results/[\w.-]+\.json) sha256 ([0-9a-f]{64})")
_PINS = _PIN.findall(_BUDGET["cap_rulings"]["E6.a2_regenerated_entries"])
_prove(
    len(_PINS) == len(CTX02_READINGS),
    f"{len(_PINS)} A2 pins in the budget's E6 ruling, expected one per {CTX02_READINGS}",
)
_PARSED = {label.replace("k = ", "k"): (path, digest) for label, path, digest in _PINS}
_prove(
    tuple(_PARSED) == CTX02_READINGS,
    f"the budget's A2 pins label {tuple(_PARSED)}, not one-to-one {CTX02_READINGS}",
)

# D-11 (i): adapter-off's A2 record is in no budget field; the one typed digest, proved by
# tests/test_phase39_prereg.py against the tracked bytes.
ADAPTER_OFF_SHA256 = "08fe96fbd9753f8b44a5eb67a69d1a2a0b062a666b5a2d5430c2a7476bb15535"
_PARSED["adapter_off"] = (phase38_prereg.ADAPTER_OFF_RECORD, ADAPTER_OFF_SHA256)

# WR-01 (39-REVIEW, Rafael 2026-10-05): the committed figure that checks the erasure target's k0
# count independently of phase19_run._pooled_rows, the Phase 18 report's A2 adapter-on totals at
# rung K, one per tier, parsed at call time. The one typed digest beside ADAPTER_OFF_SHA256, proved
# by tests/test_phase39_prereg.py against the tracked bytes.
PHASE18_REPORT = "results/phase18_extraction_report.md"
PHASE18_REPORT_SHA256 = "f24795f3f94c6330699261d908552ccd0dd10a9da8734438efd90dd3667f0cc1"

A2_RECORDS = types.MappingProxyType(
    {
        reading: types.MappingProxyType(
            {"path": _PARSED[reading][0], "sha256": _PARSED[reading][1]}
        )
        for reading in READINGS
    }
)
for _reading, _path in (
    (REFERENCE_READING, phase38_prereg.ADAPTER_ON_RECORD),
    (f"k{PREFIXES[-1]}", phase38_prereg.ERASED_RECORD),
    ("M2", phase38_prereg.RETRAIN_RECORD),
    ("adapter_off", phase38_prereg.ADAPTER_OFF_RECORD),
):
    _prove(
        A2_RECORDS[_reading]["path"] == _path,
        f"the {_reading} A2 record {A2_RECORDS[_reading]['path']} is not phase38_prereg's {_path}",
    )

# D-12 / D-23d: read in no E6 record; carried into every record by approval_block().
NOT_MEASURED = (
    "minted sets under the full question at |R| > 8 (Phase 38's nested sizes above |R| = 8; "
    "birth_year capped at its own maximum) — D-12: not part of E6; if run later, a dated "
    "continuation after E1-E4, labelled as after E6",
    "B1' context (b): the question, the ans1 preamble, then the value — D-23d",
)


def approval_block():
    """D-11 / D-26 / D-30: the approval, the projection and the stop, embedded in every Phase 39
    record. A fresh JSON-ready dict on every call."""
    return {
        "ruling": D11_RULING,
        "d26_ruling": D26_RULING,
        "source": "39-CONTEXT D-11 (62af2fe); D-26 (3499c3b); D-30 (f681550)",
        "approved_adapters": APPROVED_E6_ADAPTERS,
        "committed_adapter_cap": COMMITTED_ADAPTER_CAP,
        "committed_anchor_adapter_cap": COMMITTED_ANCHOR_ADAPTER_CAP,
        "readings": list(READINGS),
        "reference_reading": REFERENCE_READING,
        "cell_readings": list(CELL_READINGS),
        "descriptive_readings": list(DESCRIPTIVE_READINGS),
        "minted_set_size": MINTED_SET_SIZE,
        "minted_extra_nlls": MINTED_EXTRA_NLLS,
        "gate_extra_nlls_priced": GATE_EXTRA_NLLS_PRICED,
        "gate_extra_nlls_actual": GATE_EXTRA_NLLS_ACTUAL,
        "projection_steps": {
            "d11": e6_projection_hours(
                APPROVED_E6_ADAPTERS,
                APPROVED_E6_ADAPTERS,
                COMMITTED_ADAPTER_CAP * N_ENTRIES * (MINTED_SET_SIZE - 1),
            ),
            "d26": e6_projection_hours(
                APPROVED_E6_ADAPTERS, APPROVED_E6_ADAPTERS, MINTED_EXTRA_NLLS
            ),
            "d30_priced": E6_PROJECTION_HOURS,
            "d30_actual_gate": E6_PROJECTION_HOURS_ACTUAL_GATE,
        },
        "e6_projection_hours": E6_PROJECTION_HOURS,
        "committed_front_hours_e6": _BUDGET["front_hours"]["E6"],
        "e6_stop_hours": E6_STOP_HOURS,
        "not_measured": list(NOT_MEASURED),
        "budget_record": BUDGET_RECORD,
        "untouched": [
            "ledger/v6_mps_ledger.jsonl",
            "results/phase36_budget.json",
            "scripts/phase36_ledger.py",
            "scripts/phase36_caps.py",
        ],
    }


# =================================================================================================
# (7) THE ENTRIES: the whole written rule, one entry per decision family.
# =================================================================================================

# 39-REVIEW.md "Resolution (2026-10-05)": Rafael's confirmations and changes a-j, verbatim.
RULINGS_DATE = "2026-10-05"
RULINGS = types.MappingProxyType(
    {
        "a": (
            "Confirmo D-27: o pré-registro congela antes do ensaio; o ensaio fixa o sha256 "
            "dele e o preflight real recusa se houver diferença."
        ),
        "b": (
            "Confirmo D-28: as sementes da âncora usam SLOTS.index(slot) * K; a coincidência "
            "com as janelas do A2 fica declarada."
        ),
        "c": ("Confirmo D-29: a previsão do contexto (b) é condicionada ao prefixo injetado."),
        "d": (
            "Confirmo D-30a: a soma do sufixo sai da mesma passada, por máscara própria, com "
            "igualdade bit a bit provada em CPU contra a função fixada."
        ),
        "e": (
            "Confirmo a precedência em quatro passos, com uma mudança no passo 2: R_a perdido "
            "com G_q intacto recebe o desfecho nomeado REVERSE_DISAGREEMENT, contado à parte "
            "e sem classe de suficiência. NO_DISAGREEMENT fica só para quando os dois "
            "concordam."
        ),
        "f": (
            "Mudo D-25: k = 0 é referência nos dois eventos e não é célula em nenhum. Dano e "
            "colapso são classificados em 48 células cada (k8, k16, k32, k64, k78 e M2 × 8 "
            "slots). Os status de k = 0 saem numa tabela de linha de base."
        ),
        "g": (
            "Confirmo: M2 é classificado, adaptador desligado não. O relatório rotula M2 como "
            "outro treino, cuja referência de dano é o k = 0 do adaptador ensinado, e dá as "
            "contagens de M2 separadas das dos prefixos."
        ),
        "h": ("Confirmo: R_a é ALREADY_AT_K0 quando o rank em k = 0 é maior que 1."),
        "i": (
            "Confirmo que as contagens de discordância publicada vêm só de dados commitados e "
            "são calculadas por função, nunca digitadas. Recalcule depois das correções e me "
            "mostre os números antes do 'reviewed'."
        ),
        "j": (
            "Confirmo D-33: a fórmula commitada vale para as contagens novas e os empates "
            "decididos por arredondamento são nomeados. Para cada célula nessa situação, o "
            "registro mostra a classe pelas duas fórmulas; o número principal usa a fórmula "
            "commitada."
        ),
    }
)


_CONTEXT = "39-CONTEXT D-{} (62af2fe)"
_PLAN_TIME = "39-CONTEXT D-{} (3499c3b)"
_COPY = "39-CONTEXT D-{} (f681550)"
_DEFAULT = "default taken at plan time, not yet confirmed by Rafael"
_D33 = "38-CONTEXT D-33 (Phase 38, Rafael's ruling, applied as precedent)"

_ENTRY_INDICES = tuple(range(N_ENTRIES))  # D-01: every A2 entry, derived

_ENTRIES = {
    "e6_entry_subset": {
        "value": _ENTRY_INDICES,
        "derivation": (
            "D-01: all A2 entries of phase35_prereg.a2_corpus_entries(), in corpus order, no "
            'subset: Rafael\'s budget approval "E6 com a2_regenerated_entries = 0 e entries = 216" '
            "and unit_caps.E6.entries. If any entry must leave, STOP and tell Rafael which and why."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('01')}; {phase38_prereg.PROBE_E1_RECORD}; {PROBE_E6_RECORD}; "
            f"{BUDGET_RECORD}"
        ),
    },
    "e6_decomposition_rule": {
        "value": types.MappingProxyType(
            {
                "readings": types.MappingProxyType(
                    {
                        "R_a": (
                            "anchor rank, committed (phase38_prereg.committed_gate_ranks, "
                            "reproduced by gate 1)"
                        ),
                        "R_q": (
                            "per-question rank under context (b); summary n1 = number of the 27 "
                            "questions at rank 1"
                        ),
                        "G_a": "anchor generation unit: some hit in K draws (n = 1 per slot)",
                        "G_q": (
                            "A2 generation: questions with some hit in K draws, from the "
                            "committed K = 48 records (n = 27 per slot)"
                        ),
                    }
                ),
                "reference_reading": REFERENCE_READING,
                "cell_readings": CELL_READINGS,
                "descriptive_readings": DESCRIPTIVE_READINGS,
                "events": EVENTS,
                "statuses": STATUSES,
                "classes": CLASSES,
                "reverse_disagreement": (
                    "REVERSE_DISAGREEMENT: R_a LOST and G_q INTACT, a named outcome counted apart, "
                    "outside the published disagreement and every sufficiency class (ruling e)"
                ),
                "lost": types.MappingProxyType(
                    {
                        "R_a": "rank > 1 under both events; ALREADY_AT_K0 when the k0 rank > 1",
                        "collapse": (
                            "count == 0 (R_q: n1; G_a: unit; G_q: answered); ALREADY_AT_K0 when "
                            "the k0 count == 0"
                        ),
                        "damage": (
                            "count_k0 / n - count_k / n > MARGIN (the committed formula, strict "
                            ">); UNREACHABLE_AT_SIZE when count_k0 / n - 0 / n > MARGIN is False "
                            "(R_q, G_q: n = 27, needs count_k0 >= the smallest such count; G_a: "
                            "n = 1, needs a k0 hit)"
                        ),
                    }
                ),
                "disagreement": "R_a INTACT and G_q LOST",
                "precedence": (
                    "1. if R_a or G_q is UNREACHABLE_AT_SIZE or ALREADY_AT_K0, the cell takes that "
                    "outcome (UNREACHABLE_AT_SIZE first) and disagreement is undecided",
                    "2. otherwise, R_a LOST and G_q INTACT -> REVERSE_DISAGREEMENT (ruling e: "
                    "counted apart, no sufficiency class); R_a and G_q agreeing (both INTACT or "
                    "both LOST) -> NO_DISAGREEMENT",
                    "3. otherwise, if R_q or G_a is UNREACHABLE_AT_SIZE or ALREADY_AT_K0, the cell "
                    "takes that outcome (UNREACHABLE_AT_SIZE first) and enters no sufficiency "
                    "class",
                    "4. otherwise R_q LOST and G_a INTACT -> CONTEXT_SUFFICIENT; G_a LOST and R_q "
                    "INTACT -> INSTRUMENT_SUFFICIENT; both LOST -> EITHER; neither -> "
                    "INTERACTION_ONLY",
                ),
                "cells": (
                    "per event, CELL_READINGS x SLOTS through the one door cells(event) / "
                    "cell_spec(event, reading, slot), each cell with its reading, event, slot, the "
                    "readings' n (R_q and G_q: N_QUESTIONS; G_a: 1; R_a: a rank) and its k0 "
                    "reference; k0 is the reference in both events and is never a cell, its "
                    "statuses published as the baseline table (baseline_table); adapter-off is "
                    "never a cell"
                ),
                "margin": "phase38_prereg.MARGIN by reference",
                "ties": (
                    "D-33 (Phase 38, Rafael's ruling, applied as precedent): the committed formula "
                    "decides; a cell where (count_k0 - count_k) / n decides damage differently is "
                    "a margin tie decided by rounding and is named in the record and report; a "
                    "drop exactly equal to MARGIN is an exact tie decided by strict >"
                ),
                "shares": (
                    "class counts over the disagreement cells, every count with its denominator; "
                    "collapse and damage given separately (D-16)"
                ),
                "never_classified": "adapter-off (D-11 i) and the minted |R| = 8 sets (D-11 ii)",
            }
        ),
        "derivation": (
            "The whole per-cell rule, written before any record. D-13: four readings per slot x "
            "adapter, R_a, R_q, G_a, G_q. D-14: rank lost = rank > 1; generation lost by two "
            "events, collapse (no unit with a hit) and damage (the committed drop pre/n - post/n "
            "relative to k = 0 of the same context, strictly above phase38_prereg.MARGIN). D-15: "
            "the published disagreement is R_a intact and G_q lost, split into "
            "CONTEXT_SUFFICIENT, INSTRUMENT_SUFFICIENT, EITHER and INTERACTION_ONLY; R_a lost "
            "with G_q intact is REVERSE_DISAGREEMENT and R_a and G_q agreeing is NO_DISAGREEMENT "
            "(ruling e). D-16: collapse and damage classified separately. D-24: R_q lost on "
            "n1 (collapse: n1 = 0; damage: the committed drop of n1/27); the median is 1 iff n1 "
            ">= 14 and stays outside the criterion. D-25: the WR-01 outcomes per cell, with the "
            "R_q and G_q reachability additions; person_name k8, whose drop equals MARGIN "
            "exactly, is not damaged, which is true of that cell by strict >, not of every exact "
            "eight-question drop. D-33 (Phase 38 precedent applied to Phase 39's new counts): the "
            "formula stands and rounding-decided ties are named. The step order of 'precedence' "
            f'and step 2: ruling e, confirmed by Rafael {RULINGS_DATE}: "{RULINGS["e"]}" Ruling f, '
            f'changed by Rafael {RULINGS_DATE}: "{RULINGS["f"]}"'
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('13..D-16')}; {_PLAN_TIME.format('24/D-25')}; {_D33}",
    },
    "anchor_context": {
        "value": (
            "[ASSISTANT_ID] + tok.encode(phase18_extraction._frame_preamble(SLOT_FORMS[slot], "
            "ADMISSIBLE_NLL_FRAME)) — byte for byte value_span_nll's context"
        ),
        "derivation": (
            "D-04: context (a) is byte for byte the context under which exposure_rank scores the "
            "taught value (the ans1 anchor); no new prompt. D-18: gate 1 reproduces the "
            "committed anchor ranks on exactly these ids."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('04')}; {_CONTEXT.format('18')}",
    },
    "anchor_generation": {
        "value": types.MappingProxyType(
            {
                "sampling": (
                    "phase14_recall.SAMPLE_TEMPERATURE, SAMPLE_TOP_P, RECALL_MAX_NEW_TOKENS read "
                    "inside draw_all; draw 0 greedy; never passed as arguments"
                ),
                "K": K,
                "n_samples": "K - 1",
                "seed_index": "SLOTS.index(slot) * K (the slot's LOCKED_FACTS position, "
                "stage_e6's rule)",
                "forbid": (
                    "phase16_persistence.forbid_digest(forbid) == "
                    "phase19_erasure.FORBID_IDS_SHA256 before the first draw"
                ),
                "guard": "phase14_recall.assert_no_value_in_prompt on the dispatched ids",
                "hit": (
                    "phase18_extraction.score_records on the completion alone (family "
                    "'anchor', prefix_text None)"
                ),
                "unit": "int(any(hits)) over the K draws",
                "kept": "every completion and stopped flag",
            }
        ),
        "derivation": (
            "D-05: exactly the A2 sampling parameters, read inside the sampler, and the same "
            "forbid mask. D-06: the A2 hit function unchanged. D-07: the unit is some hit in K "
            "draws. D-08: every draw kept, so the hit is re-derivable on CPU. D-28 "
            f"({_DEFAULT}): seed_index = the slot's position x K (stage_e6's rule); the seed "
            "windows SEED + i*K + s coincide with the A2 windows of seed_index 0..7; the prompts "
            "differ; declared in the report."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('05..D-08')}; {_PLAN_TIME.format('28')}",
    },
    "question_context": {
        "value": (
            "phase18_extraction._guarded_span(entry) (the committed A2 prompt up to and including "
            "<|assistant|>) followed by the whole candidate value"
        ),
        "derivation": (
            "D-23 (B1): context (b) differs from (a) by the question added AND the ans1 preamble "
            "dropped, both declared in the report. The injected-prefix reading is impossible: "
            "the pet_name reference nyxen is 3 ids and its injection budget is 0."
        ),
        "kind": "preference",
        "source": _PLAN_TIME.format("23"),
    },
    "per_token_nll": {
        "value": (
            "a driver-held copy of span_nll_from_ids: same forward, mask and _prove checks, the "
            "same two cross_entropy calls (sum, mean) plus cross_entropy(reduction='none') on the "
            "same logits; one forward pass per NLL"
        ),
        "derivation": (
            "D-23a: the per-token NLL of every candidate in both contexts. D-30 condition 1: "
            "every gate cell is scored by the pinned value_span_nll AND the copy on MPS; nll_sum "
            "and nll_mean bitwise equal in every cell, else STOP before any new scoring. D-30 "
            "condition 2: the per-token values are descriptive only; ranks, n1 and events read "
            "nll_sum / nll_mean."
        ),
        "kind": "preference",
        "source": f"{_PLAN_TIME.format('23a')}; {_COPY.format('30')}",
    },
    "taught_suffix_nll": {
        "value": (
            "for the taught value under (b): a separate cross_entropy(reduction='sum') in the "
            "same forward over a mask holding only the targets after realized_injection; never a "
            "slice of the per-token values"
        ),
        "derivation": (
            "D-23b: the taught value's NLL over only the tokens after the prefix A2 injects, its "
            f"NLL in A2's exact context. D-30a ({_DEFAULT}): no extra forward pass; premise "
            "prompt_ids == _guarded_span(e) + encode(taught)[:realized_injection] for every A2 "
            "entry (measured 216/216); proved bitwise equal to span_nll_from_ids(prompt_ids, "
            "suffix) on CPU by test and by the CPU cross-check."
        ),
        "kind": "preference",
        "source": f"{_PLAN_TIME.format('23b')}; {_COPY.format('30a')}",
    },
    "rank_with_question": {
        "value": (
            "phase38_prereg.rank_in_prefix over nll_mean of "
            "phase18_extraction.reference_set_for(slot), one rank per question; per slot x "
            "reading: n1, the median rank (descriptive), the rank of the mean NLL over the 27 "
            "questions (descriptive)"
        ),
        "derivation": (
            "D-09: the committed reference sets (|R| 6-8), the main reading. D-10: one rank per "
            "question, summarised per slot x adapter. D-24: n1 is the criterion's summary; the "
            "median and the rank of the mean NLL are descriptive."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('09/D-10')}; {_PLAN_TIME.format('24')}",
    },
    "common_unit": {
        "value": (
            "some hit in K draws: anchor 1 unit per slot, A2 27 units per slot; beside it the "
            "per-draw rates h / K and total / (27 K), each with one-sided 95% Wilson lower and "
            "upper bounds (together a 90% two-sided interval), draw unit, within-question "
            "clustering ignored, descriptive"
        ),
        "derivation": (
            "D-07: the common unit is some hit in K draws; the 1-vs-27 unit asymmetry is "
            "declared in the report."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("07"),
    },
    "predicted_hit_rate": {
        "value": (
            "(a) exp(-nll_sum of the taught value at the anchor); (b) exp(-taught_suffix_nll) per "
            "question, conditioned on the injected prefix exactly as G_q's hit is scored on "
            "prefix_text + completion"
        ),
        "derivation": (
            "D-17: in each context, the hit rate predicted by the value's NLL beside the observed "
            "one, descriptive, never a criterion. D-23c: under (b) the suffix sum, not the "
            f"whole-value NLL. D-29 ({_DEFAULT}): the (b) prediction is conditioned on the "
            "injected prefix. Caveat: temperature, top-p and the hit rule separate prediction "
            "and observation."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('17')}; {_PLAN_TIME.format('23c')}; {_PLAN_TIME.format('29')}"
        ),
    },
    "gate_exact_ranks": {
        "value": READINGS,
        "derivation": (
            "D-18: gate 1 reproduces the 64 committed anchor ranks (READINGS x SLOTS, "
            "phase38_prereg.committed_gate_ranks) before any new scoring; any mismatch STOPs. "
            "D-30 condition 1 runs on the same cells."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('18')}; {_COPY.format('30')}",
    },
    "gate_a2_counts": {
        "value": (
            "each A2 record's sha256 == A2_RECORDS; phase19_run._pooled_rows re-derives every "
            "committed count (k0..k78 from phase38_prereg.a2_counts, M2 from "
            "phase19_retrain_scores.json, adapter-off 0); the erasure target's k0 count against "
            "PHASE18_REPORT's A2 adapter-on rung-K totals minus the seven non-target counts "
            "(WR-01), its row marked independent, or independent False with the reason"
        ),
        "derivation": (
            "D-19: gate 2 re-derives on CPU the committed A2 counts from the committed draws, "
            "SHA-256 checked, before using them. D-02: nothing is regenerated; anything needing "
            "regeneration pauses for Rafael. WR-01 (39-REVIEW, ruled by Rafael 2026-10-05): the "
            "erasure target's k0 count is checked against a committed total read from a "
            "SHA-pinned file, never typed; the seven non-target k0 counts are already checked "
            "against pre_answerable, so the total fixes the target."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('19')}; {_CONTEXT.format('02')}; {BUDGET_RECORD}; {PHASE18_REPORT}"
        ),
    },
    "cpu_crosscheck": {
        "value": (
            "NLL and rank re-scored on CPU: gate cells, R_q, (ii); differing ranks counted; the "
            "taught suffix sum compared bitwise with the pinned span_nll_from_ids; no generation "
            "cross-check (generation is seeded per device)"
        ),
        "derivation": (
            "D-20: a CPU cross-check of NLL and rank only, descriptive, never a criterion. D-30a: "
            "the taught suffix sum is compared bitwise with the pinned function."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('20')}; {_COPY.format('30a')}",
    },
    "descriptive_extras": {
        "value": APPROVED_E6_ADAPTERS,
        "derivation": (
            f'D-11, Rafael, verbatim: "{D11_RULING}". D-26, Rafael, verbatim: "{D26_RULING}". '
            "(i) adapter-off is an 8th adapter: its A2 context reused by SHA-256, anchor "
            "generation and both NLL readings run. (ii) the minted sets of "
            f"{phase38_prereg.MINTING_RECORD} under the full question at |R| = MINTED_SET_SIZE "
            "only, on all eight adapters (D-26). Both descriptive, never criteria, never inside "
            "the classes. Caps are checked against the approved values without passing the "
            "raised counts to check_unit_caps; the ledger, the budget record, "
            "scripts/phase36_ledger.py and scripts/phase36_caps.py stay untouched; no second "
            "stop rule."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('11')}; {_PLAN_TIME.format('26')}; {BUDGET_RECORD}",
    },
    "not_measured": {
        "value": NOT_MEASURED,
        "derivation": (
            "D-12: the minted-set reading under the full question at |R| > 8 is not part of E6. "
            "D-23d: B1' context (b) is not measured. Both are carried into every record."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('12')}; {_PLAN_TIME.format('23d')}",
    },
    "run_shape": {
        "value": (
            "one MPS run under the milestone ledger with phase36_ledger.require_launch('E6'); a "
            "CPU rehearsal on a declared slice, disclosed; the rehearsal identity records "
            "sha256(scripts/phase39_prereg.py) and the real-root preflight refuses on drift"
        ),
        "derivation": (
            "D-21: one MPS run under the ledger, the committed stop rule, a rehearsal on a "
            "declared slice disclosed in the report. D-03: no second stop rule. D-27 "
            f"({_DEFAULT}): the prereg's code review runs before the rehearsal, which pins its "
            "sha256."
        ),
        "kind": "preference",
        "source": (f"{_CONTEXT.format('21')}; {_CONTEXT.format('03')}; {_PLAN_TIME.format('27')}"),
    },
    "limitations": {
        "value": (
            "one seed, one target, |R| 6-8 in the main reading (D-22)",
            "the 1-vs-27 unit asymmetry between the anchor and A2 (D-07)",
            "no generation cross-check: generation is seeded per device (D-20)",
            "context (b) differs from (a) in two ways, the question added and the ans1 preamble "
            "dropped (D-23)",
            "G_a (no injected prefix) and G_q (injected prefix, scored on prefix_text + "
            "completion) differ beyond context",
            "the anchor and A2 seed windows coincide (D-28)",
            "the draw-unit Wilson bounds ignore within-question clustering (D-07)",
        ),
        "derivation": "D-22: the declared limitations, published in the report.",
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('22')}; {_CONTEXT.format('07')}; {_CONTEXT.format('20')}; "
            f"{_PLAN_TIME.format('23')}; {_PLAN_TIME.format('28')}"
        ),
    },
    "e6_projection_hours": {
        "value": E6_PROJECTION_HOURS,
        "derivation": (
            f"D-26 + D-30: {BUDGET_RECORD}'s E6 term at APPROVED_E6_ADAPTERS adapters and anchor "
            "adapters, in the formula's term order, plus MINTED_EXTRA_NLLS + "
            "GATE_EXTRA_NLLS_PRICED at e5_nll_high, divided by 3600; at the committed caps the "
            "same function reproduces front_hours.E6 bit for bit (proved at import)."
        ),
        "kind": "derived",
        "source": f"{_PLAN_TIME.format('26')}; {_COPY.format('30')}; {BUDGET_RECORD}",
    },
    "e6_projection_hours_actual_gate": {
        "value": E6_PROJECTION_HOURS_ACTUAL_GATE,
        "derivation": (
            "D-30: the same projection with the gate scored twice at the actual committed "
            "reference-set cells per adapter (GATE_EXTRA_NLLS_ACTUAL)."
        ),
        "kind": "derived",
        "source": f"{_COPY.format('30')}; {BUDGET_RECORD}",
    },
    "e6_stop_hours": {
        "value": E6_STOP_HOURS,
        "derivation": (
            "D-03: the committed stop (a), phase36_prereg front_stop_factor x front_hours.E6; it "
            "covers both projections (proved at import). No second stop rule."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('03')}; {BUDGET_RECORD}; phase36_prereg.ENTRIES",
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset(
    {
        "e6_entry_subset",
        "e6_decomposition_rule",
        "anchor_context",
        "anchor_generation",
        "question_context",
        "per_token_nll",
        "taught_suffix_nll",
        "rank_with_question",
        "common_unit",
        "predicted_hit_rate",
        "gate_exact_ranks",
        "gate_a2_counts",
        "cpu_crosscheck",
        "descriptive_extras",
        "not_measured",
        "run_shape",
        "limitations",
        "e6_projection_hours",
        "e6_projection_hours_actual_gate",
        "e6_stop_hours",
    }
)


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered twenty."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(
        set(ENTRIES) == _ENTRY_NAMES,
        f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra",
    )


_prove_entries()

# =================================================================================================
# (8) THE SLOT FILLS (D-03): once each, the whole value of its module-level binding.
# =================================================================================================

E6_ENTRY_SUBSET = phase35_prereg.fill(
    "e6_entry_subset",
    entry_indices=_ENTRY_INDICES,
    input_records=(phase38_prereg.PROBE_E1_RECORD, PROBE_E6_RECORD),
    derivation=ENTRIES["e6_entry_subset"],
)
E6_DECOMPOSITION_RULE = phase35_prereg.fill(
    "e6_decomposition_rule", decomposition=ENTRIES["e6_decomposition_rule"]
)

# =================================================================================================
# (9) THE DEFINITIONS (plan 39-02): gate 2, the committed counts, the D-07 rates, the D-17
# prediction, the anchor seed index, the entry and minted-member doors. Heavy imports stay inside.
# =================================================================================================


def _values():
    """{fact_id: taught value} over the locked facts (the values score_records reads)."""
    import phase14_factset

    return {fact.id: fact.value for fact in phase14_factset.LOCKED_FACTS}


def verify_a2_records(*, root=None):
    """D-02 / D-19: each of the eight A2 records is byte for byte the pinned one."""
    root = _REPO_ROOT if root is None else pathlib.Path(root)
    digests = {}
    for reading in READINGS:
        path = A2_RECORDS[reading]["path"]
        sha = hashlib.sha256((root / path).read_bytes()).hexdigest()
        _prove(
            sha == A2_RECORDS[reading]["sha256"],
            f"{reading}: {path} is not the committed record (D-02/D-19); nothing is regenerated — "
            "pause for Rafael",
        )
        digests[reading] = sha
    return digests


def committed_a2_counts():
    """{reading: {slot: answered}} from the committed sources gate 2 compares against.

    k0..k78: phase38_prereg.a2_counts(). M2: the retrain scores, retained[*].m2_answerable plus the
    omitted fact's successes. adapter_off: 0 in every slot (results/phase18_extraction_report.md,
    the adapter-off base 0/104 held-out and 0/112 taught); gate 2 re-derives it from the draws.
    """
    a2 = phase38_prereg.a2_counts()
    out = {f"k{k}": {slot: a2[slot]["counts"][k] for slot in SLOTS} for k in PREFIXES}
    scores = _read(phase38_prereg.RETRAIN_SCORES)["retrain_scores"]
    rows = [(row["slot"], row["m2_answerable"]) for row in scores["retained"].values()]
    rows.append((scores["omitted_fact"]["slot"], scores["omitted_fact"]["successes"]))
    _prove(
        sorted(slot for slot, _ in rows) == sorted(SLOTS),
        f"the retrain scores cover {sorted(slot for slot, _ in rows)}, not each of {SLOTS} once",
    )
    out["M2"] = {slot: dict(rows)[slot] for slot in SLOTS}
    out["adapter_off"] = dict.fromkeys(SLOTS, 0)
    _prove(tuple(out) == CTX02_READINGS + DESCRIPTIVE_READINGS, f"readings {tuple(out)}")
    return out


def report_k0_totals(*, root=None):
    """WR-01: {tier: (answered, questions)} from the SHA-pinned Phase 18 report, the A2 adapter-on
    row at rung K of each tier's ladder section, parsed from the text; a tier without exactly one
    such row is absent. A digest mismatch is a SystemExit."""
    import phase18_extraction  # torch at import: lazy

    root = _REPO_ROOT if root is None else pathlib.Path(root)
    data = (root / PHASE18_REPORT).read_bytes()
    _prove(
        hashlib.sha256(data).hexdigest() == PHASE18_REPORT_SHA256,
        f"{PHASE18_REPORT} is not the committed report (WR-01)",
    )
    sections = re.split(r"^## ", data.decode("utf-8"), flags=re.MULTILINE)
    row = re.compile(rf"^\| `A2` \| `adapter-on` \| {K} \| [^|\n]* \| (\d+)/(\d+) questions", re.M)
    totals = {}
    for tier in phase18_extraction.CORPUS_TIERS:
        found = [
            hit
            for section in sections
            if section.startswith(f"The ASR Ladder — `{tier}`")
            for hit in row.findall(section)
        ]
        if len(found) == 1:
            totals[tier] = (int(found[0][0]), int(found[0][1]))
    return totals


def _target_k0_check(committed_k0, *, root=None):
    """WR-01: the erasure target's k0 count fixed by the report total minus the seven non-target
    committed counts (each proved against pre_answerable by phase38_prereg.a2_counts)."""
    import phase18_extraction  # torch at import: lazy
    import phase19_erasure  # same

    target = phase19_erasure.TARGET_SLOT
    _prove(target in SLOTS, f"the erasure target {target!r} is not one of {SLOTS}")
    totals = report_k0_totals(root=root)
    if set(totals) != set(phase18_extraction.CORPUS_TIERS):
        return (
            target,
            None,
            {
                "independent": False,
                "source": (
                    f"{PHASE18_REPORT} holds no single A2 adapter-on rung-{K} row for "
                    f"{sorted(set(phase18_extraction.CORPUS_TIERS) - set(totals))}: the k0 target "
                    "count is the same scorer over the same file (SHA-pinned only)"
                ),
            },
        )
    _prove(
        sum(n for _, n in totals.values()) == len(E6_ENTRY_SUBSET),
        f"the report's A2 denominators {totals} do not sum to the {len(E6_ENTRY_SUBSET)} entries",
    )
    total = sum(answered for answered, _ in totals.values())
    others = sum(count for slot, count in committed_k0.items() if slot != target)
    parsed = ", ".join(f"{tier} {a}/{n}" for tier, (a, n) in totals.items())
    return (
        target,
        total - others,
        {
            "independent": True,
            "source": (
                f"{PHASE18_REPORT} sha256 {PHASE18_REPORT_SHA256}: the A2 adapter-on "
                f"rung-{K} totals ({parsed}) minus the seven non-target committed k0 counts"
            ),
        },
    )


def gate2(*, root=None):
    """D-19: re-derive every committed A2 count from the SHA-verified draws.

    A digest mismatch is a SystemExit; a count mismatch is returned (passed False, the row's equal
    False) so the driver refuses and the record shows the whole table. WR-01: the erasure target's
    k0 row is compared with the independent report figure (``_target_k0_check``), not with a second
    run of the same scorer; its row says which.
    """
    import phase18_extraction  # torch at import: lazy
    import phase19_run  # same

    root = _REPO_ROOT if root is None else pathlib.Path(root)
    digests = verify_a2_records(root=root)
    committed = committed_a2_counts()
    target, target_k0, target_note = _target_k0_check(committed[REFERENCE_READING], root=root)
    if target_k0 is not None:
        committed[REFERENCE_READING][target] = target_k0
    values = _values()
    rows = {}
    for reading in READINGS:
        draws = json.loads((root / A2_RECORDS[reading]["path"]).read_text(encoding="utf-8"))
        pooled = phase19_run._pooled_rows(
            draws["draws"], values, "A2", phase18_extraction.CORPUS_TIERS
        )
        by_slot = {}
        for row in pooled.values():
            _prove(row["slot"] not in by_slot, f"{reading}: two rows for slot {row['slot']}")
            by_slot[row["slot"]] = {
                "count": row["n_answerable"],
                "n_questions": row["n_questions"],
                "committed": committed[reading][row["slot"]],
                "equal": row["n_answerable"] == committed[reading][row["slot"]],
            }
        _prove(set(by_slot) == set(SLOTS), f"{reading}: rows cover {sorted(by_slot)}, not {SLOTS}")
        rows[reading] = {slot: by_slot[slot] for slot in SLOTS}
    rows[REFERENCE_READING][target].update(target_note)
    passed = all(row["equal"] for by_slot in rows.values() for row in by_slot.values())
    return {"passed": passed, "rows": rows, "sha256": digests}


def draw_rate(successes, n):
    """D-07: a per-draw rate with one-sided 95% Wilson bounds, draw unit, descriptive."""
    import erasure_gate
    import phase20_gate_coverage

    return {
        "successes": successes,
        "n": n,
        "rate": successes / n,
        "wilson_lower_95": phase20_gate_coverage.wilson_lower_bound(successes, n),
        "wilson_upper_95": erasure_gate.wilson_upper_bound(successes, n),
        "unit": "draw",
        "descriptive": True,
        "note": (
            "one-sided 95% bounds, together a 90% two-sided interval; within-question clustering "
            "ignored (D-07)"
        ),
    }


def predicted_hit_rate(nll_sum):
    """D-17: the hit rate the value's NLL predicts, exp(-nll_sum); descriptive."""
    return math.exp(-nll_sum)


def unit_of(hits):
    """D-07: the common unit, some hit in the K draws."""
    _prove(len(hits) >= 1, "a unit over zero draws is undefined")
    return int(any(hits))


def anchor_seed_index(slot):
    """D-28: the slot's LOCKED_FACTS position times K, never its position in a partial list."""
    _prove(slot in SLOTS, f"{slot!r} is not one of {SLOTS}")
    return SLOTS.index(slot) * K


def e6_entries():
    """CTX-01: (index, A2 corpus entry) for each E6_ENTRY_SUBSET index; the driver's only door."""
    entries = phase35_prereg.a2_corpus_entries()
    return tuple((i, entries[i]) for i in E6_ENTRY_SUBSET)


def minted_members(slot):
    """D-11 (ii): the first MINTED_SET_SIZE - 1 cleared names of the committed minting record."""
    members = _read(phase38_prereg.MINTING_RECORD)["slots"][slot]["cleared"][: MINTED_SET_SIZE - 1]
    _prove(
        len(members) == MINTED_SET_SIZE - 1,
        f"{slot}: {len(members)} minted members, expected {MINTED_SET_SIZE - 1}",
    )
    import phase14_factset

    taught = next(fact.value for fact in phase14_factset.LOCKED_FACTS if fact.slot == slot)
    _prove(taught not in members, f"{slot}: the taught value is among the minted members")
    return members


# =================================================================================================
# (10) THE E6 DECOMPOSITION RULE AS CODE: ENTRIES["e6_decomposition_rule"] implemented verbatim.
# Pure and torch-free; none of these reads a per-token value or a suffix sum (D-30 condition 2).
# =================================================================================================

_READING_KEYS = ("R_a", "R_q", "G_a", "G_q")


def damage_reachable(count_k0, n):
    """D-25: damage can fire at size n only if the drop to 0 is strictly above MARGIN, by the
    committed formula with the best possible post count."""
    _prove(0 <= count_k0 <= n, f"count_k0 {count_k0} outside 0..{n}")
    return count_k0 / n - 0 / n > MARGIN


def rank_status(rank_k, rank_k0):
    """D-14 / D-25: a rank > 1 is lost under both events; ALREADY_AT_K0 when the k0 rank > 1."""
    _prove(rank_k >= 1 and rank_k0 >= 1, f"ranks {rank_k}, {rank_k0} below 1")
    if rank_k0 > 1:
        return STATUSES[3]
    return STATUSES[1] if rank_k > 1 else STATUSES[0]


def count_status(event, count_k, count_k0, n):
    """D-14 / D-24 / D-25: a count's status under ``event`` against the k0 count of its context.

    collapse: ALREADY_AT_K0 at a k0 count of 0, LOST at a count of 0. damage: UNREACHABLE_AT_SIZE
    unless damage_reachable, LOST when count_k0 / n - count_k / n > MARGIN (D-33: the committed
    formula, strict >, even where (count_k0 - count_k) / n decides differently).
    """
    _prove(event in EVENTS, f"event {event!r} is not one of {EVENTS}")
    for name, count in (("count_k", count_k), ("count_k0", count_k0)):
        _prove(0 <= count <= n, f"{name} {count} outside 0..{n}")
    if event == "collapse":
        if count_k0 == 0:
            return STATUSES[3]
        return STATUSES[1] if count_k == 0 else STATUSES[0]
    if not damage_reachable(count_k0, n):
        return STATUSES[2]
    return STATUSES[1] if count_k0 / n - count_k / n > MARGIN else STATUSES[0]


def _wr01(*statuses):
    """The WR-01 outcome among ``statuses``, UNREACHABLE_AT_SIZE first; None if neither."""
    return next((s for s in WR01_OUTCOMES if s in statuses), None)


def disagreement_of(r_a, g_q):
    """Steps 1 and 2 of the precedence, on R_a and G_q alone: a WR-01 outcome (disagreement
    undecided, None); REVERSE_DISAGREEMENT (ruling e) or NO_DISAGREEMENT (False); or the published
    disagreement R_a INTACT and G_q LOST (True, class None until steps 3 and 4)."""
    for key, status in (("R_a", r_a), ("G_q", g_q)):
        _prove(status in STATUSES, f"{key} status {status!r} not in {STATUSES}")
    intact, lost = STATUSES[:2]
    outcome = _wr01(r_a, g_q)
    if outcome is not None:
        return {"class": outcome, "disagreement": None}
    if r_a == lost and g_q == intact:
        return {"class": REVERSE_DISAGREEMENT, "disagreement": False}
    if r_a == g_q:
        return {"class": CLASSES[4], "disagreement": False}
    return {"class": None, "disagreement": True}


def _precedence(statuses):
    """D-15 / D-16 / D-25: the four-step precedence of ENTRIES["e6_decomposition_rule"] on bare
    statuses; reached only through classify_cell's door."""
    _prove(
        set(statuses) == set(_READING_KEYS),
        f"statuses keyed {sorted(statuses)}, not {_READING_KEYS}",
    )
    for key in _READING_KEYS:
        _prove(statuses[key] in STATUSES, f"{key} status {statuses[key]!r} not in {STATUSES}")
    r_a, r_q, g_a, g_q = (statuses[key] for key in _READING_KEYS)
    intact, lost = STATUSES[:2]
    # Steps 1 and 2.
    first = disagreement_of(r_a, g_q)
    if first["disagreement"] is not True:
        return first
    # Step 3.
    outcome = _wr01(r_q, g_a)
    if outcome is not None:
        return {"class": outcome, "disagreement": True}
    # Step 4.
    if r_q == lost and g_a == intact:
        name = CLASSES[0]
    elif g_a == lost and r_q == intact:
        name = CLASSES[1]
    elif r_q == lost and g_a == lost:
        name = CLASSES[2]
    else:
        name = CLASSES[3]
    return {"class": name, "disagreement": True}


# WR-02: each reading's n; R_a is a rank (no n), G_a one unit per slot (D-07).
_UNITS = types.MappingProxyType({"R_q": N_QUESTIONS, "G_a": 1, "G_q": N_QUESTIONS})
_CELL_FIELDS = ("event", "reading", "slot", "n", "reference")


def cell_spec(event, reading, slot):
    """WR-02 / rulings f, g: the one door to a classified cell, a fresh JSON-ready dict; SystemExit
    for any (event, reading, slot) outside it (k0, adapter-off, an unknown reading or slot)."""
    _prove(event in EVENTS, f"event {event!r} is not one of {EVENTS}")
    _prove(
        reading in CELL_READINGS,
        f"{reading!r} is not a {event} cell: the cells are {CELL_READINGS}; k0 is the reference in "
        "both events (ruling f) and adapter-off is never classified (D-11 i)",
    )
    _prove(slot in SLOTS, f"slot {slot!r} is not one of {SLOTS}")
    return {
        "event": event,
        "reading": reading,
        "slot": slot,
        "n": dict(_UNITS),
        "reference": REFERENCE_READING,
    }


def cells(event):
    """Ruling f: the classified cells of ``event``, CELL_READINGS x SLOTS, in that order."""
    return tuple(cell_spec(event, reading, slot) for reading in CELL_READINGS for slot in SLOTS)


def _door(cell):
    """Refuse a cell that is not exactly the door's."""
    _prove(
        isinstance(cell, collections.abc.Mapping) and tuple(cell) == _CELL_FIELDS,
        f"a cell has exactly the fields {_CELL_FIELDS}, got {cell!r}",
    )
    _prove(
        dict(cell) == cell_spec(cell["event"], cell["reading"], cell["slot"]),
        f"{cell!r} is not the door's cell",
    )


def _paired(values, k0):
    """The reading keys given, the same in ``values`` and ``k0``, non-empty, in _READING_KEYS."""
    for name, given in (("values", values), ("k0", k0)):
        _prove(isinstance(given, collections.abc.Mapping), f"{name} is not a mapping")
    _prove(
        set(values) == set(k0) and values and set(values) <= set(_READING_KEYS),
        f"values keyed {sorted(values)} and k0 keyed {sorted(k0)}: one non-empty subset of "
        f"{_READING_KEYS}",
    )
    return tuple(key for key in _READING_KEYS if key in values)


def _status(event, key, value, value_k0):
    if key == "R_a":
        return rank_status(value, value_k0)
    return count_status(event, value, value_k0, _UNITS[key])


def cell_statuses(cell, values, k0):
    """WR-02: the statuses of the readings in ``values`` (R_a a rank; R_q n1, G_a the unit, G_q
    the answered count) against the k0 values of the same slot, at the door's n."""
    _door(cell)
    return {key: _status(cell["event"], key, values[key], k0[key]) for key in _paired(values, k0)}


def classify_cell(cell, values, k0):
    """WR-02: a door cell classified on all four readings: the cell, its values, its k0 values,
    the statuses and the class of the four-step precedence."""
    statuses = cell_statuses(cell, values, k0)
    _prove(tuple(statuses) == _READING_KEYS, f"a cell is classified on all of {_READING_KEYS}")
    return {
        **dict(cell),
        "values": dict(values),
        "k0": dict(k0),
        "statuses": statuses,
        **_precedence(statuses),
    }


def baseline_table(k0_by_slot):
    """Ruling f: the k0 statuses per slot, the baseline table. Each reading given at k0 with its
    status under each event against itself (ALREADY_AT_K0 / UNREACHABLE_AT_SIZE or INTACT)."""
    _prove(
        isinstance(k0_by_slot, collections.abc.Mapping) and tuple(k0_by_slot) == SLOTS,
        f"the baseline covers {list(k0_by_slot)}, not {SLOTS} in order",
    )
    return {
        slot: {
            key: {
                "value": values[key],
                **{event: _status(event, key, values[key], values[key]) for event in EVENTS},
            }
            for key in _paired(values, values)
        }
        for slot, values in k0_by_slot.items()
    }


def class_counts(classified):
    """D-16 / T-39-10: every class counted (zeros included) with both denominators, and each
    class's share of the disagreement cells (None when there are none)."""
    disagreeing = [cell for cell in classified if cell["disagreement"] is True]
    names = CLASSES[:4] + WR01_OUTCOMES
    by_disagreement = {name: sum(c["class"] == name for c in disagreeing) for name in names}
    n = len(disagreeing)
    return {
        "cells": len(classified),
        "disagreement_cells": n,
        "reverse_disagreement_cells": sum(c["class"] == REVERSE_DISAGREEMENT for c in classified),
        "by_class": {name: sum(c["class"] == name for c in classified) for name in OUTCOMES},
        "disagreement_by_class": by_disagreement,
        "shares": {name: (count / n if n else None) for name, count in by_disagreement.items()},
        "denominator": "disagreement_cells",
    }


def n1(ranks):
    """D-24: the number of questions at rank 1, R_q's criterion summary."""
    return sum(rank == 1 for rank in ranks)


def median_rank(ranks):
    """D-10 / D-24: the median of an odd number of ranks; descriptive."""
    _prove(len(ranks) % 2 == 1, f"{len(ranks)} ranks: the median needs an odd count")
    return sorted(ranks)[len(ranks) // 2]


def rank_of_mean_nll(nll_by_candidate, taught, members):
    """D-10: the taught value's rank by its mean NLL over the questions; descriptive."""
    means = {c: math.fsum(values) / len(values) for c, values in nll_by_candidate.items()}
    return phase38_prereg.rank_in_prefix(means, taught, members)
