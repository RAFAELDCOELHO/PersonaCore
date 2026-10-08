"""Phase 41 pre-registration, fill file 1: E1's checkpoint grid, its alternative ablation ordering,
condition (b)'s margin, the record paths and every written decision, frozen before any
``results/phase41_*`` record (41-CONTEXT D-01..D-28; ERASE-03..ERASE-10).

Owner 41, ``scripts/phase41_*prereg.py``. This module fills ``e1_checkpoint_grid``,
``e1_alternative_ordering`` and ``e1_condition_b_margin``: the three Phase 41 slots with no
in-phase input. Under the Phase 35 slot-ordering leg (a) every commit touching this file must
therefore strictly precede the first add of every ``results/phase41_*`` record, calibrations and
band inputs included. The floors (``e1_condition_a_floors``) and the band
(``e1_condition_c_band_inputs``) are filled later, together, in
``scripts/phase41_floors_prereg.py``, after the calibration and band-input records are committed.

Plans 41-03 and 41-04 add the pure functions to this same file; plan 41-05's review with Rafael
runs before any driver code. Once any ``results/phase41_*`` record is tracked this file is closed:
any correction is Rafael's ruling plus a dated continuation, never an edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). Targets, seeds, K values, the margin, budget hours and prices are read from the modules
and records that own them, never typed; the grid is the one caller-chosen literal (D-07).

Not torch-free at import: ``phase35_prereg.e1_teaching_seeds()`` calls ``seed_list()``, which
imports phase23_run and torch, and ``e1_targets()`` reads phase19_erasure. The heavy modules
(phase19_erasure, phase18_extraction, phase19_run, phase40_prereg, phase36_ledger,
mitigation_gate) are imported inside the functions that need them; plans 41-03 and 41-04 add most
of those functions.
"""

import collections.abc
import fnmatch
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

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase41_*` file existed, tracked or untracked.
COMMITTED = "2026-10-08"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase41_prereg] {message}")


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
# (3) THE RECORD PATHS, from the paths the v6.0 pre-registration reserved (selected by EQUALITY),
# and the inputs its registry declares.
# =================================================================================================

RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase41_*")
CALIBRATION_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase41_calibration_*.json"
)
BAND_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase41_band_inputs_*.json"
)
BUDGET_RECORD = phase35_prereg.SLOTS["e1_checkpoint_grid"]["input_records"][0]
CALIBRATION_CORPUS = phase35_prereg.SLOTS["e1_condition_a_floors"]["input_records"][1]
NOISE_FLOOR_RECORD = phase35_prereg.SLOTS["e1_condition_c_band_inputs"]["input_records"][0]
ERASURE_RECORD = RECORD_GLOB.replace("*", "erasure.json")
REPORT_RECORD = RECORD_GLOB.replace("*", "erasure_report.md")

# ERASE-03 (35 D-03): every slot at 13/13 in phase19_erasure.TARGET_RANKING, by the committed rule.
TARGETS = phase35_prereg.e1_targets()
# ERASE-05 (35 D-05): seed_list()[:2].
SEEDS = phase35_prereg.e1_teaching_seeds()

# D-07: caller-chosen, the one typed literal of this file; also the re-ranking points of D-01.
GRID = (16, 32, 48, 64, 128)

_BUDGET = _read(BUDGET_RECORD)


def _prove_path(path, glob, *, unit=False):
    """``path`` matches ``glob``; a per-cell record also matches neither prep glob."""
    _prove(fnmatch.fnmatch(path, glob), f"{path} does not match {glob}")
    if unit:
        for prep in (CALIBRATION_GLOB, BAND_GLOB):
            _prove(not fnmatch.fnmatch(path, prep), f"{path} would read as a prep record {prep}")
    return path


def _prove_unit(target=None, ordering=None, seed=None, checkpoint=None):
    """Each given argument is a member of the pre-registered set it names."""
    for name, value, members in (
        ("target", target, TARGETS),
        ("ordering", ordering, ORDERINGS),
        ("seed", seed, SEEDS),
        ("checkpoint", checkpoint, GRID),
    ):
        if value is not None:
            _prove(value in members, f"{name} {value!r} is not one of {members}")


def calibration_record(ordering, seed):
    """The calibration record of one (ordering, seed) (ERASE-06, D-10)."""
    _prove_unit(ordering=ordering, seed=seed)
    return _prove_path(CALIBRATION_GLOB.replace("*", f"{ordering}_seed{seed}"), CALIBRATION_GLOB)


def band_record(seed, ordering):
    """The band-input record of one (seed, ordering) (ERASE-09, D-13)."""
    _prove_unit(ordering=ordering, seed=seed)
    return _prove_path(BAND_GLOB.replace("*", f"{ordering}_seed{seed}"), BAND_GLOB)


def cell_record(target, ordering, seed):
    """The record of one cell (target, ordering, seed) (D-15)."""
    _prove_unit(target=target, ordering=ordering, seed=seed)
    path = RECORD_GLOB.replace("*", f"cell_{target}_{ordering}_seed{seed}.json")
    return _prove_path(path, RECORD_GLOB, unit=True)


def k16_record(target, ordering, seed, checkpoint):
    """The K = read_k record of one cell at one grid checkpoint (ERASE-07, D-27)."""
    _prove_unit(target=target, ordering=ordering, seed=seed, checkpoint=checkpoint)
    path = RECORD_GLOB.replace("*", f"k16_{target}_{ordering}_seed{seed}_k{checkpoint:03d}.json")
    return _prove_path(path, RECORD_GLOB, unit=True)


def k48_record(target, ordering, seed, checkpoint):
    """The K = confirm_k A2 arm record of one cell at one grid checkpoint (ERASE-07, D-26)."""
    _prove_unit(target=target, ordering=ordering, seed=seed, checkpoint=checkpoint)
    path = RECORD_GLOB.replace("*", f"a2_{target}_{ordering}_seed{seed}_k{checkpoint:03d}.json")
    return _prove_path(path, RECORD_GLOB, unit=True)


def run_id(unit):
    """The ledger run id of one Phase 41 unit (a prep unit or a cell) on front E1."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    return phase36_ledger.run_id(41, "E1", unit)


# =================================================================================================
# (4) THE PER-NLL COST (Rafael 2026-10-08, 41-01 checkpoint): the budget's ordering price over the
# 288 components, computed, never CONTEXT D-05's rounded figure.
# =================================================================================================


def value_nll_seconds():
    """The measured upper bound on one value NLL: ``unit_prices.e1_ordering_seconds /
    phase19_erasure.N_COMPONENTS`` (the 417.56 s ordering line is the whole Phase 19 collateral
    run, N_COMPONENTS single-ablation NLLs plus the rank scan plus the curve)."""
    import phase19_erasure  # torch at import; already loaded by e1_targets()

    return _BUDGET["unit_prices"]["e1_ordering_seconds"] / phase19_erasure.N_COMPONENTS


VALUE_NLL_SECONDS = value_nll_seconds()
# D-01 / D-05: at most one gradient at the intact adapter and one at each checkpoint before the
# last, so at most len(GRID) gradients per cell.
MAX_GRADIENTS_PER_CELL = len(GRID)
# D-05's headroom: how many value NLLs one gradient (forward + backward) may cost before a cell's
# ordering cost leaves the budget's ordering line.
GRADIENT_HEADROOM = _BUDGET["unit_prices"]["e1_ordering_seconds"] / (
    MAX_GRADIENTS_PER_CELL * VALUE_NLL_SECONDS
)

# =================================================================================================
# (5) THE ENTRIES: one entry per decision.
# =================================================================================================

_CONTEXT = "41-CONTEXT D-{} (447747c)"
_RULINGS = "41-CONTEXT D-{} (3787b9d)"

_ENTRIES = {
    "e1_checkpoint_grid": {
        "value": GRID,
        "derivation": (
            "ERASE-07, D-07: one grid for all cells, powers of 2 from 16 to 128 plus 48, which "
            "splits (32, 64], the interval where the committed pet_name zero lies: k* = 64 in "
            "results/erasure_kstar_summary.json (A2, K = 48, seed 1337, current ordering) and "
            "Phase 39's committed A2 read 2/27 at k = 32 and 0/27 at k = 64 "
            "(results/phase39_ctx_report.md:151-183). That prior reading placing 48 is declared a "
            "design input; no threshold depends on it. The grid points are also D-01's re-ranking "
            "points. D-08: no checkpoint at 288: removing every component gives the base model, "
            "the same in every cell and already measured; the report cites the adapter-off record "
            "phase38_prereg.ADAPTER_OFF_RECORD as the end point without new measurement. D-09: a "
            "cell with no zero confirmed by the last checkpoint is NOT_REACHED "
            "(phase35_prereg.NOT_REACHED), published with the A2 count and rank at every "
            'checkpoint and the sentence "não apagado com 128 de 288 componentes removidos"; it '
            "never counts as PASS nor as FAIL. D-27: each checkpoint is read at K = read_k over "
            "all phase35_prereg.a2_corpus_entries() (216 questions, the configuration Phase 36 "
            "priced); only the target's 27 enter the stop; per-fact damage at every checkpoint is "
            "descriptive. The first K = read_k zero is confirmed at K = confirm_k. Rank never "
            "enters the stop; it is recorded at every read checkpoint through "
            "phase18_extraction.measure_exposure."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('07, D-08, D-09')}; {_RULINGS.format('27')}; "
            f"{BUDGET_RECORD} front_hours.E1, unit_caps.E1"
        ),
    },
    "e1_alternative_ordering": {
        "value": "gradient",
        "derivation": (
            "ERASE-04, D-01: a first-order Taylor (gradient) ordering re-ranked at every grid "
            "checkpoint. s_j is a scale on rank-1 component j of the adapter as ablated so far "
            "(only components not yet ablated). Each component is scored by its predicted rise of "
            "the value NLL on removal, -dNLL/ds_j at s_j = 1, largest predicted rise first; never "
            "the absolute value: a component whose removal lowers the target NLL goes to the back, "
            "as in the current ordering. Ties by address (layer, projection, j), as "
            "phase19_erasure.select_ablation_prefix. The leading components are ablated up to the "
            "next checkpoint. D-02: the NLL is the one the current ordering uses, "
            "phase19_erasure.value_span_nll_mean (same value, same context, same scoring "
            "function); the only differences between the two orderings are the estimator and the "
            "re-ranking. D-03: the ordering is a rule over the fact being erased, so a calibration "
            "runs it on phase19_erasure.select_calibration_fact(). In a cell it is re-ranked over "
            "the not-yet-ablated components at the intact adapter and at each grid checkpoint "
            f"before the last, at most MAX_GRADIENTS_PER_CELL = len(GRID) = "
            f"{MAX_GRADIENTS_PER_CELL} gradients; in a calibration (rank stop, k may pass the last "
            "checkpoint) it is re-ranked at every grid checkpoint and positions past the last "
            "checkpoint are taken from the last ranking. D-04: the ordering actually applied is "
            "written into every cell and calibration record (MPS backward may not be bitwise "
            "deterministic; reproduction uses the recorded ordering). D-05: one value NLL costs at "
            f"most VALUE_NLL_SECONDS = unit_prices.e1_ordering_seconds / "
            f"phase19_erasure.N_COMPONENTS = {VALUE_NLL_SECONDS!r} s (Rafael 2026-10-08, the "
            "measured figure, computed); the assertion is that a cell's ordering cost fits in "
            f"{BUDGET_RECORD} unit_prices.e1_ordering_seconds, which holds while one gradient "
            "(forward + backward) costs at most GRADIENT_HEADROOM = e1_ordering_seconds / "
            f"(MAX_GRADIENTS_PER_CELL x VALUE_NLL_SECONDS) = {GRADIENT_HEADROOM!r} value NLLs. "
            "Written static fallback (no new decision needed): if that assertion fails, or if a "
            "calibration turns out unable to take a grid-dependent ordering, the alternative "
            "ordering becomes the static gradient ordering, one gradient on the intact adapter, "
            "with the same correlation reading. D-06 (descriptive, declared in advance): the "
            "Spearman rank correlation, per seed, on the calibration fact, between the gradient "
            "ordering on the intact adapter and the current ordering, descriptive; no verdict."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('01..D-06')}; 41-DISCUSSION-LOG Ordenação alternativa; "
            f"{BUDGET_RECORD} unit_prices.e1_ordering_seconds; Rafael 2026-10-08 (41-01-SUMMARY "
            "checkpoint reply, c12e7f5)"
        ),
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset({"e1_checkpoint_grid", "e1_alternative_ordering"})


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
# (6) THE SLOT FILLS: once each, the whole value of its module-level binding. The three Phase 41
# slots with no in-phase input, so leg (a) puts this file before every results/phase41_* record.
# =================================================================================================

E1_CHECKPOINT_GRID = phase35_prereg.fill(
    "e1_checkpoint_grid",
    checkpoints=GRID,
    input_records=(BUDGET_RECORD,),
    derivation=ENTRIES["e1_checkpoint_grid"],
)
E1_ALTERNATIVE_ORDERING = phase35_prereg.fill(
    "e1_alternative_ordering", ordering=ENTRIES["e1_alternative_ordering"]
)
E1_CONDITION_B_MARGIN = phase35_prereg.fill("e1_condition_b_margin")

# The current ordering first; "greedy" is the key the Phase 40 consumer test's band uses.
ORDERINGS = ("greedy", E1_ALTERNATIVE_ORDERING["value"])

# The grid's count against the committed cap. D-26: the K = 48 confirmation count is never passed.
phase36_caps.check_unit_caps(
    "E1", **phase36_caps.counts_for("e1_checkpoint_grid", E1_CHECKPOINT_GRID)
)
