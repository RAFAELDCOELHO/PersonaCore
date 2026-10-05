"""Phase 39 pre-registration: the E6 entry subset, the written instrument x context decomposition
rule, the D-11 / D-26 / D-30 approval and its budget arithmetic, frozen before any
``results/phase39_*`` record (39-CONTEXT D-03, ROADMAP Phase 39 SC4, CTX-01/CTX-03).

This module fills the two Phase 35 slots owned by Phase 39 exactly once each, as the module-level
bindings ``E6_ENTRY_SUBSET`` and ``E6_DECOMPOSITION_RULE``. Under the Phase 35 slot-ordering leg (a)
every commit touching this file must strictly precede the first add of every ``results/phase39_*``
record, so the rule is written in full before any E6 number exists and cannot be fitted to it.

Plan 39-02 adds the pure functions that implement the written rule to this same file. D-27: its code
review (plan 39-03) runs before any rehearsal, and the rehearsal pins its sha256. Any later
correction is Rafael's ruling plus a dated continuation (``scripts/_addendum.py``), never a silent
edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). The projection and stop hours, the extra NLL counts and the entry count are computed at
import from committed records and closed constants, never typed.

Not torch-free at import: the e6_entry_subset fill calls ``phase35_prereg.a2_corpus_entries()``,
which imports phase18_extraction (torch). Every other heavy import stays inside a function.
"""

import collections.abc
import fnmatch
import json
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

# D-25: k = 0 is the damage reference of every reading's own context.
REFERENCE_READING = f"k{PREFIXES[0]}"
_prove(REFERENCE_READING in READINGS, f"{REFERENCE_READING} is not a reading")
# D-11 (i): adapter-off is descriptive and never classified.
DESCRIPTIVE_READINGS = ("adapter_off",)
_prove(
    set(DESCRIPTIVE_READINGS) <= set(READINGS),
    f"the descriptive readings {DESCRIPTIVE_READINGS} are not readings {READINGS}",
)
# CTX-02's adapters: k0..k78 and M2.
CLASSIFIED_READINGS = tuple(r for r in READINGS if r not in DESCRIPTIVE_READINGS)
# D-25: the k = 0 cell has no damage class.
DAMAGE_READINGS = tuple(r for r in CLASSIFIED_READINGS if r != REFERENCE_READING)

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
    len(_PINS) == len(CLASSIFIED_READINGS),
    f"{len(_PINS)} A2 pins in the budget's E6 ruling, expected one per {CLASSIFIED_READINGS}",
)
_PARSED = {label.replace("k = ", "k"): (path, digest) for label, path, digest in _PINS}
_prove(
    tuple(_PARSED) == CLASSIFIED_READINGS,
    f"the budget's A2 pins label {tuple(_PARSED)}, not one-to-one {CLASSIFIED_READINGS}",
)

# D-11 (i): adapter-off's A2 record is in no budget field; the one typed digest, proved by
# tests/test_phase39_prereg.py against the tracked bytes.
ADAPTER_OFF_SHA256 = "08fe96fbd9753f8b44a5eb67a69d1a2a0b062a666b5a2d5430c2a7476bb15535"
_PARSED["adapter_off"] = (phase38_prereg.ADAPTER_OFF_RECORD, ADAPTER_OFF_SHA256)

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
        "classified_readings": list(CLASSIFIED_READINGS),
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
