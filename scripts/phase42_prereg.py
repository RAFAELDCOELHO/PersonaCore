"""Phase 42 pre-registration, fill file 1: E3's grid of DP-SGD recipes, the record paths and every
written decision, frozen before any ``results/phase42_*`` record (42-CONTEXT D-01..D-23;
RECIPE-01..RECIPE-04).

Owner 42, ``scripts/phase42_*prereg.py``. This module fills ``e3_grid_subset``, the only Phase 42
slot with no in-phase input. Under the Phase 35 slot-ordering leg (a) every commit touching this
file must therefore strictly precede the first add of every ``results/phase42_*`` record. The
threshold slot ``e3_recall_threshold`` is filled later, in ``scripts/phase42_threshold_prereg.py``,
after the three new sigma = 0 control records are committed (D-19).

Importing this module re-runs the reused v4.0 control's SHA-256 check against tag v5.0 and the P22
check for every T the grid uses (RECIPE-04), both inside the Phase 35 grid rule. It writes nothing
at import (tests/test_phase36_caps.py executes it in a fresh module). Not torch-free at import:
``teach_persona`` and ``seed_list()`` load torch.

Plans 42-02 and 42-03 add the pure functions to this same file; plan 42-06's review with Rafael runs
before any run. Once any ``results/phase42_*`` record is tracked this file is closed: any correction
is Rafael's ruling plus a dated continuation (``scripts/_addendum.py``), never an edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). Steps, batch, seed, counts, prices and onsets are read from the modules and records that
own them, never typed; lr = 1e-3 is the one caller-chosen literal (D-02).
"""

import collections.abc
import hashlib
import json
import pathlib
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
import phase36_caps  # noqa: E402  (same; torch-free)
import phase36_prereg  # noqa: E402  (same)
import teach_persona  # noqa: E402  (same; torch at import)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase42_*` file existed, tracked or untracked.
COMMITTED = "2026-10-13"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase42_prereg] {message}")


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
# (3) THE RECORD GLOBS, from the paths the v6.0 pre-registration reserved (selected by EQUALITY),
# and the inputs its registry declares for the grid slot.
# =================================================================================================

RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase42_*")
CONTROL_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase42_control_*.json"
)
BUDGET_RECORD = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][0]
V4_CONTROL_RECORD = phase35_prereg.SLOTS["e3_grid_subset"]["input_records"][1]

_BUDGET = _read(BUDGET_RECORD)
_V4 = _read(V4_CONTROL_RECORD)

# D-03: the reused control, read from its committed bytes (the Phase 35 rule compares the same
# bytes with `git show v5.0:` at every import of this file).
V4_CONTROL_SHA256 = hashlib.sha256((_REPO_ROOT / V4_CONTROL_RECORD).read_bytes()).hexdigest()
V4_CONTROL_COUNTS = types.MappingProxyType(
    {
        "taught": (_V4["taught_recall"]["numerator"], _V4["taught_recall"]["denominator"]),
        "heldout": (_V4["heldout_recall"]["numerator"], _V4["heldout_recall"]["denominator"]),
    }
)

# =================================================================================================
# (4) THE GRID (RECIPE-01; D-01, D-02, D-04): lr x T at batch teach_persona.BATCH_SIZE (q = 1),
# one seed for the whole grid.
# =================================================================================================

SEED = phase35_prereg.seed_list()[0]
T_MAX = phase36_prereg.ENTRIES["e3_max_steps"]["value"]
# D-02: 1e-3 is caller-chosen, the one typed literal of this file.
LRS = (teach_persona.LR, 1e-3)
STEPS = (phase35_prereg.STEP_BUDGET, T_MAX)
# RECIPES[0] is the v4.0 recipe. MappingProxyType, never dict: an entry value holds no mutable
# container; the Phase 35 rule accepts any Mapping.
RECIPES = tuple(
    types.MappingProxyType({"lr": lr, "steps": t, "batch": teach_persona.BATCH_SIZE})
    for lr in LRS
    for t in STEPS
)
CONTROL_SIGMA = phase35_prereg.E3_SIGMAS[0]
NOISED_SIGMAS = tuple(s for s in phase35_prereg.E3_SIGMAS if s > CONTROL_SIGMA)

# =================================================================================================
# (5) THE ENTRIES: one entry per decision.
# =================================================================================================

_ENTRIES = {
    "e3_grid_subset": {
        "value": RECIPES,
        "derivation": (
            "RECIPE-01, D-01: batch fixed at teach_persona.BATCH_SIZE, so q = 1; the accountant is "
            "frozen at q = 1 (src/personacore/privacy/accountant.py:850, where a penalty out of "
            "caution is still a wrong published number). D-02: a 2x2 factorial, lr in "
            "(teach_persona.LR, 1e-3) x T in (phase35_prereg.STEP_BUDGET, "
            "phase36_prereg.ENTRIES['e3_max_steps']), batch 8; the v4.0 corner (lr 3e-4, T = 200, "
            "batch 8) is one of the 4, inside unit_caps.E3. D-03: the v4.0 sigma = 0 control is "
            "reused by SHA-256 against tag v5.0, consumed as a declared input of this fill; only "
            "the record is reused, never the adapter. D-09: no fifth recipe; the recipes cap "
            "stays at 4."
        ),
        "kind": "preference",
        "source": (
            "42-CONTEXT D-01, D-02, D-03, D-09 (dc578f9); "
            f"{BUDGET_RECORD} front_hours.E3, unit_caps.E3; {V4_CONTROL_RECORD}"
        ),
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset({"e3_grid_subset"})


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered names."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(
        set(ENTRIES) == _ENTRY_NAMES,
        f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra",
    )


_prove_entries()

# =================================================================================================
# (6) THE SLOT FILL: once, the whole value of its module-level binding. The one Phase 42 slot with
# no in-phase input, so leg (a) puts this file before every results/phase42_* record. The rule
# checks the v4.0 control against tag v5.0 and P22 for every T used (RECIPE-04, D-08).
# =================================================================================================

E3_GRID_SUBSET = phase35_prereg.fill(
    "e3_grid_subset",
    recipes=RECIPES,
    seed=SEED,
    input_records=(BUDGET_RECORD, V4_CONTROL_RECORD),
    derivation=ENTRIES["e3_grid_subset"],
)

# The grid's counts and its sigma count against the committed caps (unit_caps.E3).
phase36_caps.check_unit_caps("E3", **phase36_caps.counts_for("e3_grid_subset", E3_GRID_SUBSET))
phase36_caps.check_unit_caps("E3", sigmas=len(phase35_prereg.E3_SIGMAS))

# D-08: the onsets the rule computed, re-asserted by the driver before any stage-2 training.
P22_ONSETS = E3_GRID_SUBSET["p22_onset_sigma"]
