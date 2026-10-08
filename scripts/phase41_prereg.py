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

import erasure_gate  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase35_prereg  # noqa: E402  (same)
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
_DEFAULT = "default taken at plan time, not yet confirmed by Rafael"

# D-11 (Rafael 2026-10-08, 41-01 checkpoint): checkpoints/phase19_erase_calibration_adapter.pt is
# untracked, so the prediction's expected sha256 is read from the committed record that carries
# it (tracked since 69fc671), never typed.
D11_REFERENCE_RECORD = "results/phase19_calibration_curve.json"
D11_REFERENCE_KEY = "adapter_in_sha256"
D11_REFERENCE_SHA256 = _read(D11_REFERENCE_RECORD)[D11_REFERENCE_KEY]

# D-26: Rafael's reply, verbatim: the ONE line of
# .planning/phases/41-erasure-across-facts-orderings-and-seeds/41-DISCUSSION-LOG.md at commit
# 3787b9d starting `> "Opção 2, com duas amarras:`, the text between its first and last double
# quote (proved by tests/test_phase41_prereg.py).
D26_RULING = (
    "Opção 2, com duas amarras:1. Confirmações adicionais em K = 48 são permitidas, como "
    "manda o ERASE-07 (uma confirmação não zero continua para o próximo checkpoint). O teto "
    "natural é a grade: no máximo 4 confirmações por célula, uma por checkpoint depois do "
    "primeiro zero em K = 16. Cada confirmação é gravada no registro da célula com suas "
    "horas, lançadas na fatia do E1.2. O custo fica sob a pausa da fatia já decidida (52,78 "
    "h, decisão minha ao passar dela). Não há pausa por confirmação.Desvio declarado em "
    "relação ao limite de 1 por célula da Fase 36 (unit_caps.E1.k48_confirms_per_cell), com "
    "o motivo: o limite foi uma suposição de preço e a regra de parada do ERASE-07 é a "
    "medição. Nenhuma célula vira NOT_REACHED por falta de confirmação; NOT_REACHED só "
    "quando não há zero confirmado até o checkpoint 128."
)

# Phase 36's committed per-cell K = 48 cap, read; D-26 declares the deviation from it.
_K48_CAP = _BUDGET["unit_caps"]["E1"]["k48_confirms_per_cell"]

_E1_PRICE_KEYS = (
    "e1_calibration_seconds",
    "e1_k16_seconds",
    "e1_k48_seconds",
    "e1_ordering_seconds",
)

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
            "as in the current ordering; ties by address (layer, projection, j), as "
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
    "targets": {
        "value": (
            "phase35_prereg.e1_targets(): every slot at 13/13 in phase19_erasure.TARGET_RANKING, "
            "by the committed rule, never typed"
        ),
        "derivation": (
            "ERASE-03, 35 D-03: the four facts E1 erases are computed by the Phase 35 rule over "
            "phase19_erasure.TARGET_RANKING and bound to TARGETS; no target name is typed in any "
            "scripts/phase41_*.py."
        ),
        "kind": "preference",
        "source": (
            "41-CONTEXT carried forward (447747c); 35-CONTEXT D-03; phase35_prereg.e1_targets"
        ),
    },
    "seeds_and_adapters": {
        "value": types.MappingProxyType(
            {
                "seeds": "phase35_prereg.e1_teaching_seeds() = seed_list()[:2]",
                "adapters": (
                    f"{NOISE_FLOOR_RECORD}::phase41_adapters[seed][group] {{path, sha256}}; the "
                    "driver's preflight refuses a sha256 mismatch; never retrained"
                ),
                "use": (
                    "full = the intact adapter of every cell of that seed; m2 = the pet_name M1 x "
                    "M2 comparison only (D-18)"
                ),
            }
        ),
        "derivation": (
            "ERASE-05, 35 D-05: the two teaching seeds are read from the Phase 35 core and the "
            "adapters are reused by sha256 from the committed Phase 40 record, never retrained."
        ),
        "kind": "preference",
        "source": f"41-CONTEXT carried forward (447747c); 35-CONTEXT D-05; {NOISE_FLOOR_RECORD}",
    },
    "stop_rule": {
        "value": (
            "per cell, at each GRID checkpoint in order: ablate ordering[:c]; K = "
            "E1_CHECKPOINT_GRID['read_k'] read over all 216 a2_corpus_entries() (D-27); if the "
            "target's pooled 27-question count is 0, a K = confirm_k pass "
            "(phase19_erasure.run_erasure_arm 'erased'); zero there stops; else continue; "
            "phase35_prereg.e1_stop(grid=E1_CHECKPOINT_GRID, readings=...) is called once on the "
            "cell's readings and must equal the driver's stop; exposure rank "
            "(phase18_extraction.measure_exposure, |R| = 8) at every read checkpoint, never in the "
            "stop"
        ),
        "derivation": (
            "ERASE-07, D-07, D-27: the stop is Phase 35's e1_stop over the filled grid; the read "
            "covers all A2 questions, only the target's enter the stop, and rank is recorded but "
            "never stops a cell."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('07')}; {_RULINGS.format('27')}; phase35_prereg.e1_stop",
    },
    "k48_confirmations": {
        "value": types.MappingProxyType(
            {
                "max_per_cell": len(GRID),
                "per_checkpoint": 1,
                "committed_cap": _K48_CAP,
                "hours": (
                    "each confirmation's started_utc / finished_utc and seconds in the cell "
                    "record; charged to E1's share"
                ),
                "pause": "none per confirmation; the D-23 share pause covers it",
                "not_reached": (
                    "only when no zero is confirmed by GRID[-1]; never for lack of a confirmation"
                ),
                "caps_call": (
                    "the count is never passed to phase36_caps.check_unit_caps as "
                    "k48_confirms_per_cell"
                ),
            }
        ),
        "derivation": (
            "D-26, ERASE-07: further K = confirm_k confirmations are allowed: a non-zero "
            "confirmation continues to the next checkpoint, at most one per grid checkpoint after "
            "the first K = read_k zero, so at most len(GRID) per cell, the most "
            'phase35_prereg.e1_stop admits (D-26 reads Rafael\'s "4" as four beyond the first). '
            "Each is recorded in the cell record with its hours, charged to E1; no pause per "
            "confirmation (the D-23 share pause covers the cost). Declared deviation from "
            f"unit_caps.E1.k48_confirms_per_cell = {_K48_CAP} in {BUDGET_RECORD}: that cap was a "
            "pricing assumption; ERASE-07's stop is the measurement. Nothing in "
            "scripts/phase41_*.py passes this count to "
            f'phase36_caps.check_unit_caps. Rafael\'s ruling, verbatim: "{D26_RULING}"'
        ),
        "kind": "preference",
        "source": (
            f"{_RULINGS.format('26')}; 41-DISCUSSION-LOG Plan-phase rulings (3787b9d); "
            f"{BUDGET_RECORD} unit_caps.E1"
        ),
    },
    "calibration": {
        "value": (
            "one calibration per (ordering, seed); one fresh adapter per seed trained with "
            "teach_persona.train_arm on teach_persona.arm_spec('cal_first_person_replay') (the "
            "recipe of phase19_erasure._cmd_cal_train) with seed=, a Phase 41 arm name and prefix "
            "'phase41', shared by both orderings of that seed; "
            "checkpoints/phase19_erase_calibration_adapter.pt is never an input of the floors "
            "(D-10); the ordering runs on phase19_erasure.select_calibration_fact() (D-03): greedy "
            "= phase19_erasure.select_ablation_prefix with "
            "phase19_erasure.reference_set_for_calibration twin references, prefix ordered[:k]; "
            "gradient = the gradient ordering at every grid checkpoint and a rank-stop scan with "
            "the same twin references (the pin's clause: the first prefix whose rank != 1, else "
            "288); cal-erased by phase19_erasure.run_erasure_arm('cal-erased', "
            "corpus_path=phase19_erasure.CALIBRATION_CORPUS_PATH) with its raw record under data/ "
            "and its draws folded into calibration_record(ordering, seed)"
        ),
        "derivation": (
            "ERASE-06, D-03, D-10: floors are keyed by (target, ordering, seed) with one "
            "calibration per (ordering, seed); calibration and target adapters share a training "
            "generation at each seed (RESEARCH Pattern 7, Pitfalls 2-3)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('03, D-10')}; 41-RESEARCH Pattern 7; {CALIBRATION_CORPUS}",
    },
    "condition_a": {
        "value": (
            "erasure_gate.wilson_upper_bound(target n_answerable, 27) <= "
            "E1_CONDITION_A_FLOORS[(target, ordering, seed)]['floor'], the floors computed by the "
            "e1_condition_a_floors rule from the calibration records (lock_erasure_floor / "
            "floor_branch inside), filled in scripts/phase41_floors_prereg.py"
        ),
        "derivation": (
            "ERASE-06, D-10: condition (a) reads the target's Wilson upper bound against the "
            "floor of its own (target, ordering, seed)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('10')}; {CALIBRATION_GLOB}",
    },
    "condition_b": {
        "value": (
            "the 7 slots of phase18_extraction.CORE_SLOTS other than the target, each its own "
            "n/27; pre = the intact full adapter of the SAME seed, "
            "results/phase40_a2_full_seed<s>.json through "
            "phase40_prereg.slot_rows(a2_rows(...)), never the K = 48 record's pre_erasure "
            "(seed-1337 Phase 18) and never the pin's pet_name-hardwired helpers; |post rate - pre "
            "rate| <= E1_CONDITION_B_MARGIN per slot; every slot beyond the margin named"
        ),
        "derivation": (
            "ERASE-10, D-15, 35 D-16: (b) reads every non-target against the sampling-noise "
            "margin, with the same seed's intact adapter as the baseline (RESEARCH Pattern 8, "
            "Pitfalls 4-5)."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; 35-CONTEXT D-16; 41-RESEARCH Pattern 8",
    },
    "condition_c": {
        "value": (
            "the dialogue gap (adapter_on - adapter_off of the K = 48 stop record's dialogue_ppl) "
            "inside E1_CONDITION_C_BAND_INPUTS[(seed, ordering)] = "
            "mitigation_gate.dialogue_gap_band(control_gap, gap_noise_floor); control_gap "
            "re-measured on the intact full adapter in each (seed, ordering) prep unit before any "
            f"ablation and required equal to {NOISE_FLOOR_RECORD} "
            "per_seed[seed].full.dialogue_gap.gap (else stop for Rafael, never corrected); "
            "retention carries no verdict"
        ),
        "derivation": (
            "ERASE-09, D-13, D-14: (c) is the dialogue band only. Retention carries no verdict, "
            "for three reasons: (1) the v4.0 cap results/phase20_retention_floor.json::cap is "
            "anchored on adapter-off; Phase 40's intact full and M2 adapters "
            "(results/phase40_a2_*_seed*.json::retention_ppl) sit above it and v3.0's ablated arm "
            "(results/phase19_arm_erased.json) below, so the leg would fail an erasure that "
            "preserves the adapter and pass one that destroys it; (2) it is the same defect "
            "Phase 19's report published for the dialogue leg, which ERASE-09 corrects with the "
            "band anchored on the adapted model; (3) a declared change from the (c) of v3.0 and "
            "v4.0, not an omission. Descriptive, declared in advance: retention_ppl at each "
            "cell's stop beside the same seed's intact adapter (and, for pet_name, its M2); a "
            "column 'passaria no teto do v4.0: sim/não'; the retention spread across Phase 40's "
            "five seeds beside the two-seed floor."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('13, D-14')}; {NOISE_FLOOR_RECORD}; "
            "results/phase20_retention_floor.json"
        ),
    },
    "verdict": {
        "value": (
            "INCONCLUSIVE first, in erasure_gate.erasure_succeeded's precedence (no target "
            "questions; target zero without phase37_routes.route_a's zero-result NLL flag; no "
            "non-target delta); else SUCCESS iff (a), (b) and (c) hold, else FAILURE; every "
            "failed condition listed and, for (b), each non-target beyond the margin; NOT_REACHED "
            "cells carry no (b)/(c) verdict; erasure_gate.erasure_succeeded itself is never "
            "called (its (c) is the v3.0 one-sided cap)"
        ),
        "derivation": (
            "D-15, ERASE-09: each cell carries its own verdict and every condition that failed."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; scripts/erasure_gate.py",
    },
    "pair_labels": {
        "value": types.MappingProxyType(
            {
                "PASS": "SUCCESS at both seeds",
                "FAILURE replicada": "FAILURE at both seeds",
                "não replicado": (
                    "any other combination, published with each seed's verdict in full (e.g. "
                    "'SUCCESS na 1337, NOT_REACHED na 2024'); never the pair's PASS or FAILURE"
                ),
            }
        ),
        "derivation": "ERASE-10, D-16: no (target, ordering) pair reads PASS without both seeds.",
        "kind": "preference",
        "source": _CONTEXT.format("16"),
    },
    "summary_line": {
        "value": (
            "of the 8 (target, ordering) pairs, the count under each label; INCONCLUSIVE, "
            "NOT_REACHED and NOT_RUN counted separately inside 'não replicado'; no threshold, no "
            "aggregation beyond the count; the full 4 x 2 x 2 table published"
        ),
        "derivation": "D-17: a pre-registered summary line with no threshold.",
        "kind": "preference",
        "source": _CONTEXT.format("17"),
    },
    "m1_m2": {
        "value": (
            "pet_name cells only: per non-target, full intact, M1 at the stop and M2 of the same "
            "seed (each /27) with M1 - full and M2 - full, the min-max of "
            "recall_floor.m2.per_slot[slot].counts over the five Phase 40 M2 seeds beside, and "
            "'dentro da faixa' / 'fora da faixa' for M1's count; other targets: 'sem M2, "
            "comparação não feita'; 'fora da faixa' is not a statistical test (two seeds against "
            "five retrains)"
        ),
        "derivation": "D-18: the M1 x M2 comparison is descriptive and has no verdict.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('18')}; {NOISE_FLOOR_RECORD}",
    },
    "varies_label": {
        "value": (
            "'varia entre seeds' when max(recall_floor.full.per_slot[slot].range, "
            "recall_floor.m2.per_slot[slot].range) >= E1_CONDITION_B_MARGIN; pet_name as a "
            "non-target from the five Phase 40 full A2 records only (D-28: no pet_name row in "
            "recall_floor; one-group basis stated); computed, never typed; both groups' min-max "
            "beside each delta; per cell the count of slots beyond the margin among labelled and "
            "unlabelled slots and whether (b) would fail on the unlabelled slots alone; the label "
            "never discounts a delta nor enters a verdict"
        ),
        "derivation": (
            "D-19, D-28: the label uses the published floor's convention (the larger of the two "
            "groups); gate (b) still reads all seven non-targets against the margin."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('19')}; {_RULINGS.format('28')}; {NOISE_FLOOR_RECORD}",
    },
    "d13_block": {
        "value": (
            "pet_name cells only, at the stop: phase40_noise.d13_scores on the M1 adapter (anchor "
            "rank at 8/32/128/512, R_q n1 on the committed and minted lists), each beside the "
            f"min-max of {NOISE_FLOOR_RECORD} d13.blocks over the five M2 seeds with "
            "'dentro'/'fora'; descriptive; a scoring failure is recorded as not measured, never "
            "drops the cell"
        ),
        "derivation": "D-20: the whole D-13 block at the stop of the pet_name cells, descriptive.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('20')}; {NOISE_FLOOR_RECORD}",
    },
    "predictions": {
        "value": types.MappingProxyType(
            {
                "d11_calibration_identity": (
                    "the new seed-1337 calibration adapter is tensor-identical (torch.equal per "
                    "tensor, never the file sha256) to teach_persona.arm_outputs("
                    "phase19_erasure.CALIBRATION_ARM, prefix=phase19_erasure.RETRAIN_PREFIX)"
                    "['adapter']; that reference file is identified by "
                    f"{D11_REFERENCE_RECORD}::{D11_REFERENCE_KEY} = {D11_REFERENCE_SHA256} (read "
                    "from the committed record, the .pt being untracked); a reference file whose "
                    "sha256 differs from the record is a reported finding before any torch.equal "
                    "comparison; descriptive; a mismatch is a finding, not a failure; the floors "
                    "still come from the new adapters"
                ),
                "d21_d13_at_stop": (
                    "in all 4 pet_name cells, R_q n1 falls outside the M2 range on both lists and "
                    "the anchor rank at 512 inside; the (1337, greedy) cell repeats Phase 39's "
                    "reading only if it stops at 64 (R_q n1 11/27 there); descriptive; a mismatch "
                    "is a finding, not a failure"
                ),
                "greedy_1337_phase19_prefix": (
                    "the (pet_name, greedy, 1337) ordering's first len(ordered_prefix) addresses "
                    "equal results/phase19_collateral_curve.json ordered_prefix (the adapter is "
                    "tensor-identical to persona_adapter.pt); descriptive; a mismatch is a "
                    "finding, not a failure"
                ),
                "d02_cpu_equality": (
                    "the grad-enabled value NLL equals phase19_erasure.value_span_nll_mean bit "
                    "for bit on CPU (measured in research); descriptive; a mismatch is a finding, "
                    "not a failure"
                ),
            }
        ),
        "derivation": (
            "D-11, D-21 (Phase 40 D-07 pattern): predictions written before any run, read as "
            "description. D-11's reference digest is read from "
            f"{D11_REFERENCE_RECORD}::{D11_REFERENCE_KEY} ({D11_REFERENCE_SHA256}), never typed "
            "(Rafael 2026-10-08)."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('11, D-21')}; {D11_REFERENCE_RECORD}; Rafael 2026-10-08 "
            "(41-01-SUMMARY checkpoint reply, c12e7f5)"
        ),
    },
    "d06_correlation": {
        "value": (
            "Spearman rho = 1 - 6 sum d^2 / (n (n^2 - 1)) between the intact-adapter gradient "
            "ranking and the greedy ordered on the calibration fact, per seed, from the two "
            "calibration records of that seed; descriptive, no verdict"
        ),
        "derivation": "D-06: declared in advance, descriptive.",
        "kind": "preference",
        "source": _CONTEXT.format("06"),
    },
    "d12_side_by_side": {
        "value": (
            "per (ordering, seed): calibration rate (successes/questions), floor and "
            "floor_branch, side by side"
        ),
        "derivation": "D-12: how far the floor moves between seeds, descriptive.",
        "kind": "preference",
        "source": _CONTEXT.format("12"),
    },
    "execution_order": {
        "value": (
            "prep units first (4: per seed in SEEDS, per ordering in ORDERINGS), then all 8 "
            "greedy cells pair by pair (each target in TARGETS order, seed 1337 then 2024), then "
            "the 8 gradient cells in the same pair order"
        ),
        "derivation": (
            "D-22: the floors and band slots are each filled once and need every (ordering, "
            "seed) present, so the prep units run first."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("22"),
    },
    "e1_pause": {
        "value": (
            "before every cell: E1 spent (phase36_ledger.spent(fronts=('E1',)), lost attempts "
            "included) >= front_hours.E1 -> pause for Rafael; the notice gives E1 hours, "
            "completed pairs, any half-done pair, and what remains for E3, E4 and the 90 h line; "
            "completing a half-done pair is his call; the global ledger stops stay above it"
        ),
        "derivation": "D-23: E1 pauses at its own share for Rafael's decision.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('23')}; {BUDGET_RECORD} front_hours.E1",
    },
    "crash_rule": {
        "value": (
            "Phase 40's R-3 b per unit (prep unit or cell): a new attempt only after Rafael's "
            "approved and a cause note, same seed and same HEAD (or the change declared); partial "
            "outputs kept under data/phase41_dropped and listed; adapters and orderings compared "
            "between attempts with torch.equal; a crash only (no end line), never a finished unit"
        ),
        "derivation": "D-24: the crash rule is Phase 40's R-3 b, per unit.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('24')}; 40-CONTEXT R-3 b",
    },
    "operations": {
        "value": (
            "the waiter follows the driver PID, never the appended log; bootout only after two "
            "exit checks (ps -p on the noted PID, then an empty pgrep); per-block relaunch of the "
            "pending units without changing HEAD; each launch gate records sysctl vm.swapusage, "
            "memory_pressure, top RSS and the newest JetsamEvent; the collector LaunchDaemon "
            "com.polybot.negrisk-books stays stopped until the run ends"
        ),
        "derivation": "D-25: Phase 40's operational lessons.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('25')}; 40-09-SUMMARY",
    },
    "e1_share_hours": {
        "value": _BUDGET["front_hours"]["E1"],
        "derivation": "D-23: the share the pause reads, front_hours.E1 of the committed budget.",
        "kind": "derived",
        "source": f"{_CONTEXT.format('23')}; {BUDGET_RECORD} front_hours.E1",
    },
    "e1_unit_prices": {
        "value": types.MappingProxyType(
            {key: _BUDGET["unit_prices"][key] for key in _E1_PRICE_KEYS}
        ),
        "derivation": (
            "D-05: the four E1 unit prices of the committed budget; e1_ordering_seconds is the "
            "ordering-cost bound (VALUE_NLL_SECONDS = e1_ordering_seconds / "
            "phase19_erasure.N_COMPONENTS)."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('05')}; {BUDGET_RECORD} unit_prices",
    },
    "record_layout": {
        "value": (
            "calibration and band records per (ordering, seed); one cell record per cell naming "
            "its K = 16 records k16_record and K = 48 records k48_record, all under results/; the "
            "raw cal-erased arm record and the M1 export under data/phase41_e1/; the band record "
            "measured first inside each prep attempt whose end line names the calibration record, "
            "and carrying no provenance.run"
        ),
        "derivation": f"D-04, D-13, D-22: {_DEFAULT}.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('04, D-13, D-22')}; Claude's Discretion",
    },
    "alternative_variant": {
        "value": (
            "D-05's assertion evaluated on the CPU rehearsal and again on the MPS launch-gate "
            "smoke; failing on either selects the static variant before any record; the chosen "
            "variant written into every gradient record"
        ),
        "derivation": f"D-05: {_DEFAULT}.",
        "kind": "preference",
        "source": _CONTEXT.format("05"),
    },
    "not_run": {
        "value": (
            "a cell never started (the D-23 pause or a stop) reads NOT_RUN in its pair and is "
            "counted separately in D-17"
        ),
        "derivation": f"D-17, D-23: {_DEFAULT}.",
        "kind": "preference",
        "source": _CONTEXT.format("17, D-23"),
    },
    "resume_declaration": {
        "value": (
            "after a D-23 pause the run resumes only through a written declaration under "
            "data/phase41_resume/ carrying Rafael's approved verbatim and the cells it covers"
        ),
        "derivation": (
            f"D-23 (Claude's Discretion: mirrors phase40_prereg.RELAUNCH_DECLARATION_KEYS): "
            f"{_DEFAULT}."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('23')}; Claude's Discretion",
    },
    "d02_equality": {
        "value": (
            "the grad-path value must equal value_span_nll_mean exactly on every device, at every "
            "gradient; a non-zero difference stops for Rafael, never a tolerance"
        ),
        "derivation": f"D-02 (Claude's Discretion: equality on MPS): {_DEFAULT}.",
        "kind": "preference",
        "source": f"{_CONTEXT.format('02')}; Claude's Discretion",
    },
    "control_gap_scope": {
        "value": (
            "D-13's equality refuses on mps; on the CPU rehearsal the reading is recorded, "
            "labelled rehearsal, and never refused"
        ),
        "derivation": f"D-13: {_DEFAULT}.",
        "kind": "preference",
        "source": _CONTEXT.format("13"),
    },
    "approvals": {
        "value": (
            "one approved per launch; stage-1 records under one approved, then the floors fill "
            "file committed under it; stage-2 records under three approved: ledger and cell "
            "records, the erasure record, the report"
        ),
        "derivation": f"ERASE-06, ERASE-10 SC5 (41-CONTEXT Approvals): {_DEFAULT}.",
        "kind": "preference",
        "source": "41-CONTEXT Approvals (447747c)",
    },
    "prep_order": {
        "value": (
            "seed-major: the calibration adapter is trained in the first prep unit of its seed "
            "and reused, digest-checked, by the second"
        ),
        "derivation": f"D-10, D-22: {_DEFAULT}.",
        "kind": "preference",
        "source": _CONTEXT.format("10, D-22"),
    },
    "stop_for_rafael": {
        "value": (
            "an in-run STOP writes its evidence under data/phase41_e1/stops/ and raises "
            "SystemExit; the attempt is then reconciled lost and Rafael rules"
        ),
        "derivation": f"D-13, D-23, D-24: {_DEFAULT}.",
        "kind": "preference",
        "source": _CONTEXT.format("13, D-23, D-24"),
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset(
    {
        "e1_checkpoint_grid",
        "e1_alternative_ordering",
        "targets",
        "seeds_and_adapters",
        "stop_rule",
        "k48_confirmations",
        "calibration",
        "condition_a",
        "condition_b",
        "condition_c",
        "verdict",
        "pair_labels",
        "summary_line",
        "m1_m2",
        "varies_label",
        "d13_block",
        "predictions",
        "d06_correlation",
        "d12_side_by_side",
        "execution_order",
        "e1_pause",
        "crash_rule",
        "operations",
        "e1_share_hours",
        "e1_unit_prices",
        "record_layout",
        "alternative_variant",
        "not_run",
        "resume_declaration",
        "d02_equality",
        "control_gap_scope",
        "approvals",
        "prep_order",
        "stop_for_rafael",
    }
)


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

# =================================================================================================
# (7) THE GATE COMPOSITION (plan 41-03; D-15, D-16, D-17, D-09; ERASE-09, ERASE-10; RESEARCH
# Pattern 8). Pure functions of records: the per-target conditions (a)/(b)/(c), the cell verdict,
# the two-seed pair label and the summary counts. erasure_gate.erasure_succeeded is never called
# (its (c) is the v3.0 one-sided cap), nor the pin's pet_name-hardwired (b) helpers
# (nontarget_rows, nontarget_deltas, target_fact_id, render_verdict).
# =================================================================================================

# The verdict strings, selected from the gate's domain by EQUALITY, never retyped as a new domain.
SUCCESS = next(v for v in erasure_gate.VERDICTS if v == "SUCCESS")
FAILURE = next(v for v in erasure_gate.VERDICTS if v == "FAILURE")
INCONCLUSIVE = next(v for v in erasure_gate.VERDICTS if v == "INCONCLUSIVE")

# D-17 / D-23 (ENTRIES["not_run"], a planner default): a cell never started.
NOT_RUN = "NOT_RUN"
_prove(
    NOT_RUN not in erasure_gate.VERDICTS and NOT_RUN != phase35_prereg.NOT_REACHED,
    f"NOT_RUN {NOT_RUN!r} collides with a verdict or NOT_REACHED",
)
# Every per-seed outcome a pair can carry.
SEED_OUTCOMES = (*erasure_gate.VERDICTS, phase35_prereg.NOT_REACHED, NOT_RUN)

# D-16: PASS, FAILURE replicada, não replicado, in the entry's key order.
PAIR_LABELS = tuple(ENTRIES["pair_labels"]["value"])


def nontarget_slots(target):
    """ERASE-10 / D-15 (Pitfall 4): the core slots of ``phase18_extraction.CORE_SLOTS`` other than
    ``target``, in that order: (b)'s non-targets are per target, never the pin's pet_name set."""
    import phase18_extraction  # torch at import: lazy

    _prove(target in TARGETS, f"target {target!r} is not one of {TARGETS}")
    return tuple(slot for slot in phase18_extraction.CORE_SLOTS if slot != target)


def record_rows(record):
    """D-15: a K = confirm_k A2 arm record's per-slot rows over all 8 core slots, through
    ``phase40_prereg.slot_rows(a2_rows(record, *a2_scope(record)))`` (pooled 27 = 14 + 13 from the
    draws; ``a2_rows`` proves the Phase 18 k), never the record's per_fact or pre_erasure."""
    import phase40_prereg  # reads records at import: lazy

    return phase40_prereg.slot_rows(
        phase40_prereg.a2_rows(record, *phase40_prereg.a2_scope(record))
    )


def k16_slot_counts(draws):
    """ERASE-07 / D-27: a K = read_k read's ``{slot: {n_answerable, n_questions, rate}}`` over the
    8 core slots, pooled by ``phase19_run._pooled_rows`` over both ``CORPUS_TIERS``. The draws must
    be the A2 family the Phase 18 corpus entries carry (read from
    ``phase35_prereg.a2_corpus_entries()``, never typed), hold every corpus tier, and carry exactly
    ``E1_CHECKPOINT_GRID["read_k"]`` completions each; each core slot pools
    ``phase19_erasure.N_TARGET_QUESTIONS`` questions."""
    import phase14_factset  # torch-free; lazy like every pin import
    import phase18_extraction  # torch at import: lazy
    import phase19_erasure  # torch at import: lazy
    import phase19_run  # torch at import: lazy

    corpus_families = {entry["family"] for entry in phase35_prereg.a2_corpus_entries()}
    families = {draw["family"] for draw in draws}
    _prove(
        len(corpus_families) == 1 and families == corpus_families,
        f"draw family {sorted(families)} is not the A2 corpus family {sorted(corpus_families)}",
    )
    (family,) = corpus_families
    tiers = tuple(sorted({draw["tier"] for draw in draws}))
    _prove(
        set(tiers) == set(phase18_extraction.CORPUS_TIERS),
        f"draw tiers {tiers} are not phase18_extraction.CORPUS_TIERS",
    )
    read_k = E1_CHECKPOINT_GRID["read_k"]
    _prove(
        all(len(draw["completions"]) == read_k for draw in draws),
        f"a draw does not carry exactly read_k = {read_k} completions",
    )
    values = {f.id: f.value for f in phase14_factset.LOCKED_FACTS + phase14_factset.SOFT_TIER_FACTS}
    rows = phase19_run._pooled_rows(draws, values, family, tiers)
    core = phase18_extraction.CORE_SLOTS
    by_slot = {}
    for fact_id, row in rows.items():
        if row["slot"] in core:
            _prove(row["slot"] not in by_slot, f"two facts on slot {row['slot']!r}")
            _prove(
                row["n_questions"] == phase19_erasure.N_TARGET_QUESTIONS,
                f"fact {fact_id!r} pools {row['n_questions']} questions, not "
                "phase19_erasure.N_TARGET_QUESTIONS",
            )
            by_slot[row["slot"]] = {
                "n_answerable": row["n_answerable"],
                "n_questions": row["n_questions"],
                "rate": row["rate"],
            }
    _prove(set(by_slot) == set(core), f"rows cover slots {sorted(by_slot)}, not {sorted(core)}")
    return {slot: by_slot[slot] for slot in core}


def k16_target_count(draws, target):
    """ERASE-07 / D-27: the target's ``(n_answerable, n_questions)`` at a K = read_k read; only
    these 27 questions enter the stop."""
    _prove(target in TARGETS, f"target {target!r} is not one of {TARGETS}")
    row = k16_slot_counts(draws)[target]
    return row["n_answerable"], row["n_questions"]


def condition_a(n_answerable, n_questions, floor):
    """ERASE-06 / D-10: (a) holds iff ``erasure_gate.wilson_upper_bound(n_answerable,
    n_questions)`` (questions as the unit) is at or below the (target, ordering, seed) floor."""
    _prove_count("n_answerable", n_answerable)
    _prove_count("n_questions", n_questions, low=1)
    _prove(n_answerable <= n_questions, f"{n_answerable} answerable of {n_questions} questions")
    upper = erasure_gate.wilson_upper_bound(n_answerable, n_questions)
    return {"upper": upper, "floor": floor, "holds": upper <= floor}


def condition_b(post_rows, pre_rows, target):
    """ERASE-10 / D-15 (Pattern 8, Pitfalls 4-5): (b) per target. Each of
    ``nontarget_slots(target)`` is its own n/27; ``pre_rows`` are the intact full adapter of the
    SAME seed (results/phase40_a2_full_seed<s>.json through ``record_rows``), never a K =
    confirm_k record's pre_erasure. ``beyond`` iff ``|post rate - pre rate| >
    E1_CONDITION_B_MARGIN``; every slot beyond is named, in ``nontarget_slots`` order; (b) holds
    iff none is."""
    import phase19_erasure  # torch at import: lazy

    margin = E1_CONDITION_B_MARGIN
    slots = {}
    for slot in nontarget_slots(target):
        for name, rows in (("post", post_rows), ("pre", pre_rows)):
            _prove(slot in rows, f"{name} rows carry no {slot!r} row")
            _prove(
                rows[slot]["n_questions"] == phase19_erasure.N_TARGET_QUESTIONS,
                f"{name} {slot!r} pools {rows[slot]['n_questions']} questions, not "
                "phase19_erasure.N_TARGET_QUESTIONS",
            )
        pre, post = pre_rows[slot], post_rows[slot]
        delta = post["rate"] - pre["rate"]
        slots[slot] = {
            "pre": [pre["n_answerable"], pre["n_questions"]],
            "post": [post["n_answerable"], post["n_questions"]],
            "delta": delta,
            "abs_delta": abs(delta),
            "beyond": abs(delta) > margin,
        }
    beyond = [slot for slot, row in slots.items() if row["beyond"]]
    return {"margin": margin, "slots": slots, "beyond": beyond, "holds": not beyond}


def condition_c(dialogue_ppl, band):
    """ERASE-09 / D-13: (c) holds iff the dialogue gap ``adapter_on - adapter_off`` of the stop
    record lies inside the (seed, ordering) band ``(lo, hi)`` of E1_CONDITION_C_BAND_INPUTS
    (``DIALOGUE_GAP_BAND``). Retention carries no verdict (D-14)."""
    _prove(
        isinstance(band, tuple) and len(band) == 2 and band[0] <= band[1],
        f"band {band!r} is not an ordered (lo, hi) pair",
    )
    lo, hi = band
    gap = dialogue_ppl["adapter_on"] - dialogue_ppl["adapter_off"]
    return {"gap": gap, "lo": lo, "hi": hi, "holds": lo <= gap <= hi}


def cell_verdict(*, stop, target_n, target_q, zero_results_have_nll, a, b, c):
    """D-15 / ERASE-09: one cell's verdict. A NOT_REACHED stop (``e1_stop(...)["stop"]``) gets no
    verdict (``judged`` False). Then INCONCLUSIVE in ``erasure_gate.erasure_succeeded``'s
    precedence: no target questions; target zero without the zero-result NLL flag
    (``phase37_routes.route_a``); no non-target slot in (b). Else SUCCESS iff (a), (b) and (c)
    hold, else FAILURE with every failed condition in (a), (b), (c) order and, for (b), every
    non-target beyond the margin. ``a``/``b``/``c`` are the condition dicts (``None`` allowed only
    where the verdict never reads them)."""
    _prove(
        stop in GRID or stop == phase35_prereg.NOT_REACHED,
        f"stop {stop!r} is neither a grid checkpoint nor NOT_REACHED",
    )
    if stop == phase35_prereg.NOT_REACHED:
        verdict = {"verdict": phase35_prereg.NOT_REACHED, "judged": False, "reason": None}
        return {**verdict, "failed": [], "beyond": []}
    reason = None
    if target_q == 0:
        reason = "no target questions scored"
    elif target_n == 0 and not zero_results_have_nll:
        reason = "target recall is zero but no teacher-forced NLL was recorded"
    elif not (b and b["slots"]):
        reason = "no non-target slot scored in (b)"
    if reason is not None:
        return {
            "verdict": INCONCLUSIVE,
            "judged": True,
            "failed": [],
            "beyond": [],
            "reason": reason,
        }
    failed = [name for name, cond in (("(a)", a), ("(b)", b), ("(c)", c)) if not cond["holds"]]
    verdict = FAILURE if failed else SUCCESS
    _prove(verdict in erasure_gate.VERDICTS, f"verdict {verdict!r} is not in VERDICTS")
    return {
        "verdict": verdict,
        "judged": True,
        "failed": failed,
        "beyond": list(b["beyond"]),
        "reason": None,
    }


def pair_label(verdicts):
    """D-16 / ERASE-10: one (target, ordering) pair's label from ``{seed: outcome}`` keyed by
    exactly SEEDS: PASS iff SUCCESS at both seeds, FAILURE replicada iff FAILURE at both, else não
    replicado. ``text`` publishes each seed's outcome in full, "<v1> na <s1>, <v2> na <s2>"."""
    _prove(set(verdicts) == set(SEEDS), f"pair seeds {sorted(verdicts)} are not {SEEDS}")
    for seed in SEEDS:
        _prove(
            verdicts[seed] in SEED_OUTCOMES, f"outcome {verdicts[seed]!r} not in {SEED_OUTCOMES}"
        )
    outcomes = {verdicts[seed] for seed in SEEDS}
    if outcomes == {SUCCESS}:
        label = PAIR_LABELS[0]
    elif outcomes == {FAILURE}:
        label = PAIR_LABELS[1]
    else:
        label = PAIR_LABELS[2]
    return {"label": label, "text": ", ".join(f"{verdicts[s]} na {s}" for s in SEEDS)}


def summary_counts(pairs):
    """D-17: of the (target, ordering) pairs, keyed by exactly TARGETS x ORDERINGS, the count under
    each label; inside não replicado, the PAIRS carrying INCONCLUSIVE, NOT_REACHED or NOT_RUN at
    either seed (a pair counts once under a sub-key, so the sub-counts may overlap). No
    threshold."""
    expected = {(t, o) for t in TARGETS for o in ORDERINGS}
    _prove(
        set(pairs) == expected,
        f"pairs {sorted(set(pairs) ^ expected, key=repr)} are missing or extra",
    )
    counts = dict.fromkeys(PAIR_LABELS, 0)
    inside = dict.fromkeys((INCONCLUSIVE, phase35_prereg.NOT_REACHED, NOT_RUN), 0)
    for verdicts in pairs.values():
        label = pair_label(verdicts)["label"]
        counts[label] += 1
        if label == PAIR_LABELS[2]:
            for outcome in inside:
                inside[outcome] += outcome in verdicts.values()
    return {**counts, "inside_nao_replicado": inside, "n_pairs": len(pairs)}


def not_reached_sentence():
    """D-09: the sentence a NOT_REACHED cell is published with, from GRID[-1] and
    ``phase19_erasure.N_COMPONENTS``."""
    import phase19_erasure  # torch at import: lazy

    return f"não apagado com {GRID[-1]} de {phase19_erasure.N_COMPONENTS} componentes removidos"


def floors_fill_inputs():
    """ERASE-06 / D-10 / D-12: the exact kwargs of ``phase35_prereg.fill("e1_condition_a_floors",
    ...)``: every (target, ordering, seed) key with value None (the floors are computed), the four
    calibration records plus the calibration corpus, and a four-field derivation whose value is the
    key tuple and whose source names every consumed path. A fresh object each call, so the floors
    fill file and the CPU rehearsal pass identical, unshared arguments."""
    keys = tuple((t, o, s) for t in TARGETS for o in ORDERINGS for s in SEEDS)
    input_records = tuple(calibration_record(o, s) for s in SEEDS for o in ORDERINGS) + (
        CALIBRATION_CORPUS,
    )
    derivation = {
        "value": keys,
        "derivation": (
            "ERASE-06 / D-10 / D-03: one calibration per (ordering, seed) on "
            "select_calibration_fact() with a fresh adapter per seed; the floors are computed by "
            "the e1_condition_a_floors rule (lock_erasure_floor, floor_branch) from each record's "
            "own draws pooled over CORPUS_TIERS; never typed"
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('10, D-12')}; " + " ".join(input_records),
    }
    _prove_entry("floors_fill_inputs", derivation)
    return {"floors": dict.fromkeys(keys), "input_records": input_records, "derivation": derivation}


def band_fill_inputs():
    """ERASE-09 / D-13: the exact kwargs of ``phase35_prereg.fill("e1_condition_c_band_inputs",
    ...)``: every (seed, ordering) key with value None (the inputs are read), the Phase 40 noise
    floor record plus the four band-input records, and a four-field derivation whose value is the
    key tuple and whose source names every consumed path. A fresh object each call."""
    keys = tuple((s, o) for s in SEEDS for o in ORDERINGS)
    input_records = (NOISE_FLOOR_RECORD,) + tuple(
        band_record(s, o) for s in SEEDS for o in ORDERINGS
    )
    derivation = {
        "value": keys,
        "derivation": (
            "ERASE-09 / D-13: control_gap re-measured on the intact full adapter, equal to Phase "
            "40's gap; gap_noise_floor read from the Phase 40 record; band = DIALOGUE_GAP_BAND"
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('13')}; " + " ".join(input_records),
    }
    _prove_entry("band_fill_inputs", derivation)
    return {
        "band_inputs": dict.fromkeys(keys),
        "input_records": input_records,
        "derivation": derivation,
    }


# =================================================================================================
# (8) THE DECLARED DESCRIPTIVE READINGS (plan 41-03; D-06, D-12, D-14, D-18, D-19, D-20, D-21,
# D-28): rules on committed records, written before any record. None of them feeds cell_verdict.
# =================================================================================================

V4_CAP_LABEL = "passaria no teto do v4.0"
VARIES_LABEL = "varia entre seeds"
INSIDE, OUTSIDE = "dentro da faixa", "fora da faixa"
NO_M2 = "sem M2, comparação não feita"


def spearman_rho(order_a, order_b):
    """D-06: Spearman's rho in closed form, ``1 - 6 sum d^2 / (n (n^2 - 1))``, between two full
    permutations of the same ``phase19_erasure.N_COMPONENTS`` addresses (JSON lists are read as
    tuples); a prefix, a duplicate or a different address set is refused. Descriptive."""
    import phase19_erasure  # torch at import: lazy

    index = set(phase19_erasure.component_index())
    n = phase19_erasure.N_COMPONENTS
    orders = []
    for name, order in (("order_a", order_a), ("order_b", order_b)):
        order = tuple(tuple(address) for address in order)
        _prove(len(order) == n, f"{name} has {len(order)} addresses, not N_COMPONENTS = {n}")
        _prove(len(set(order)) == n, f"{name} repeats an address")
        _prove(set(order) == index, f"{name} is not a permutation of component_index()")
        orders.append(order)
    first, second = orders
    rank = {address: i for i, address in enumerate(second)}
    d2 = sum((i - rank[address]) ** 2 for i, address in enumerate(first))
    return 1 - 6 * d2 / (n * (n * n - 1))


def d12_rows(floors):
    """D-12: the e1_condition_a_floors mapping, one row per (ordering, seed) in ORDERINGS x SEEDS
    order: calibration rate (successes / questions), floor and floor_branch side by side. Every
    target of an (ordering, seed) carries the same calibration row, or it is refused."""
    expected = {(t, o, s) for t in TARGETS for o in ORDERINGS for s in SEEDS}
    _prove(
        set(floors) == expected,
        f"floor keys {sorted(set(floors) ^ expected, key=repr)} are missing or extra",
    )
    rows = []
    for ordering in ORDERINGS:
        for seed in SEEDS:
            group = [dict(floors[(t, ordering, seed)]) for t in TARGETS]
            _prove(
                all(row == group[0] for row in group),
                f"targets disagree on the calibration row of ({ordering!r}, {seed})",
            )
            rows.append({"ordering": ordering, "seed": seed, **group[0]})
    return rows


def retention_floor_record():
    """D-14: ``(repo-relative path, record)`` of ``phase20_run.RETENTION_FLOOR_PATH`` (the v4.0
    cap and the retention noise floor)."""
    import phase20_run  # torch at import: lazy

    rel = phase20_run.RETENTION_FLOOR_PATH.relative_to(_REPO_ROOT).as_posix()
    return rel, _read(rel)


def retention_rows(stop_record, full_record, m2_record, *, cap):
    """D-14 (descriptive, no verdict): retention_ppl at the cell's stop, of the same seed's intact
    full adapter and, for pet_name cells, of its M2 (``m2_record`` None otherwise), each read by
    ``phase37_routes.route_d``; beside the v4.0 cap with "passaria no teto do v4.0: sim/não"."""
    import phase37_routes  # torch at import: lazy

    stop = phase37_routes.route_d(stop_record)
    return {
        "stop": stop,
        "intact_full": phase37_routes.route_d(full_record),
        "m2": None if m2_record is None else phase37_routes.route_d(m2_record),
        "cap": cap,
        V4_CAP_LABEL: "sim" if stop <= cap else "não",
    }


def retention_spread(full_records, m2_records, *, floor):
    """D-14: the retention_ppl spread per group over Phase 40's seeds (``{seed: A2 record}``, the
    same seeds in both groups), min, max and range beside the two-seed retention noise floor."""
    import phase37_routes  # torch at import: lazy

    _prove(
        full_records and list(full_records) == list(m2_records),
        f"full seeds {list(full_records)} != m2 seeds {list(m2_records)}",
    )
    spread = {}
    for group, records in (("full", full_records), ("m2", m2_records)):
        values = [phase37_routes.route_d(record) for record in records.values()]
        spread[group] = {
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "n": len(values),
        }
    return {**spread, "seeds": list(full_records), "retention_ppl_noise_floor": floor}


def _group_range(counts):
    """One group's min-max of ``[[n, q], ...]`` counts and its rate range (max - min of n / q)."""
    import phase19_erasure  # torch at import: lazy

    _prove(counts, "a group has no counts")
    _prove(
        all(q == phase19_erasure.N_TARGET_QUESTIONS for _, q in counts),
        "a count's denominator is not phase19_erasure.N_TARGET_QUESTIONS",
    )
    rates = [n / q for n, q in counts]
    ns = tuple(n for n, _ in counts)
    return {"counts": ns, "min": min(ns), "max": max(ns), "range": max(rates) - min(rates)}


def slot_ranges(noise_floor, full_rows_by_seed):
    """D-19 / D-28: per core slot, the min-max of each group's counts in
    ``recall_floor.<group>.per_slot[slot]`` and its rate range (the recorded range is proved equal
    to the counts'); a slot absent from both groups (pet_name: no row in recall_floor) takes the
    full group from ``full_rows_by_seed`` (``record_rows`` of the five Phase 40 full A2 records,
    seeds == phase40_prereg.SEEDS) with basis "full only"; a slot in one group only is refused.
    ``range`` = the larger group range, the published floor's convention."""
    import phase18_extraction  # torch at import: lazy
    import phase40_prereg  # reads records at import: lazy

    _prove(
        list(full_rows_by_seed) == list(phase40_prereg.SEEDS),
        f"full rows seeds {list(full_rows_by_seed)} are not phase40_prereg.SEEDS",
    )
    recall = noise_floor["recall_floor"]
    groups = ("full", "m2")
    ranges = {}
    for slot in phase18_extraction.CORE_SLOTS:
        present = [g for g in groups if slot in recall[g]["per_slot"]]
        if not present:
            counts = [
                [rows[slot]["n_answerable"], rows[slot]["n_questions"]]
                for rows in full_rows_by_seed.values()
            ]
            full = _group_range(counts)
            ranges[slot] = {"basis": "full only", "full": full, "range": full["range"]}
            continue
        _prove(present == list(groups), f"slot {slot!r} is in one group only ({present})")
        entry = {"basis": "full and m2"}
        for group in groups:
            row = recall[group]["per_slot"][slot]
            entry[group] = _group_range(row["counts"])
            _prove(
                entry[group]["range"] == row["range"],
                f"{group} {slot!r}: recorded range {row['range']!r} is not its counts' range",
            )
        entry["range"] = max(entry[group]["range"] for group in groups)
        ranges[slot] = entry
    return ranges


def varies_labels(ranges):
    """D-19: the slots labelled "varia entre seeds", those whose range is at least
    E1_CONDITION_B_MARGIN. Computed, never typed; the label never discounts a delta."""
    return frozenset(slot for slot, row in ranges.items() if row["range"] >= E1_CONDITION_B_MARGIN)


def nontarget_damage(condition_b_result, labels):
    """D-19: of (b)'s slots beyond the margin, how many carry the label and how many do not, and
    whether (b) would fail on the unlabelled alone. Reads ``condition_b_result``, never changes
    it."""
    beyond = condition_b_result["beyond"]
    labelled = tuple(slot for slot in beyond if slot in labels)
    unlabelled = tuple(slot for slot in beyond if slot not in labels)
    return {
        "beyond_labelled": len(labelled),
        "beyond_unlabelled": len(unlabelled),
        "b_fails_on_unlabelled_alone": bool(unlabelled),
        "labelled": labelled,
        "unlabelled": unlabelled,
    }


def in_range(value, low, high):
    """D-18 / D-20: "dentro da faixa" iff ``low <= value <= high``, else "fora da faixa"."""
    return INSIDE if low <= value <= high else OUTSIDE


def m1_m2_rows(target, *, full_rows, m1_rows, m2_rows, noise_floor):
    """D-18 (descriptive): pet_name cells only (``phase19_erasure.TARGET_SLOT``), per non-target,
    full intact, M1 at the stop and M2 of the same seed (each [n, 27]), M1 - full and M2 - full
    (rates), the min-max of ``recall_floor.m2.per_slot[slot].counts`` and M1's count dentro/fora.
    Any other target: {"comparison": "sem M2, comparação não feita"}. Not a statistical test."""
    import phase19_erasure  # torch at import: lazy

    _prove(target in TARGETS, f"target {target!r} is not one of {TARGETS}")
    if target != phase19_erasure.TARGET_SLOT:
        return {"comparison": NO_M2}
    per_slot = noise_floor["recall_floor"]["m2"]["per_slot"]
    rows = {}
    for slot in nontarget_slots(target):
        m2_range = _group_range(per_slot[slot]["counts"])
        full, m1, m2 = full_rows[slot], m1_rows[slot], m2_rows[slot]
        rows[slot] = {
            "full": [full["n_answerable"], full["n_questions"]],
            "m1": [m1["n_answerable"], m1["n_questions"]],
            "m2": [m2["n_answerable"], m2["n_questions"]],
            "m1_minus_full": m1["rate"] - full["rate"],
            "m2_minus_full": m2["rate"] - full["rate"],
            "m2_range": (m2_range["min"], m2_range["max"]),
            "m1_in_range": in_range(m1["n_answerable"], m2_range["min"], m2_range["max"]),
        }
    return rows


def _anchor_size(block):
    """The largest anchor-curve size of a D-13 block, read (``max(keys, key=int)``), never typed."""
    return max(block["anchor_curve"], key=int)


def d13_ranges(noise_floor):
    """D-20: the min-max over Phase 40's D-13 blocks (the five M2 seeds) of the anchor rank at the
    largest anchor size and of R_q n1 on the committed and minted lists; every block measured and
    at the same anchor size."""
    blocks = list(noise_floor["d13"]["blocks"].values())
    _prove(blocks and all(b["measured"] is True for b in blocks), "a D-13 block is not measured")
    sizes = {_anchor_size(block) for block in blocks}
    _prove(len(sizes) == 1, f"the D-13 blocks disagree on the anchor size: {sorted(sizes)}")
    (size,) = sizes
    readings = {
        f"anchor_{size}": [block["anchor_curve"][size]["rank"] for block in blocks],
        "r_q_committed": [block["r_q"]["committed"]["n1"] for block in blocks],
        "r_q_minted": [block["r_q"]["minted"]["n1"] for block in blocks],
    }
    return {name: (min(values), max(values)) for name, values in readings.items()}


def d13_comparison(block, ranges):
    """D-20 (descriptive): one pet_name cell's D-13 block at the stop, each reading beside its
    Phase 40 M2 range with dentro/fora; a block not measured stays {"measured": False}."""
    if block["measured"] is False:
        return {"measured": False, "readings": None}
    _prove(block["measured"] is True, f"block measured is {block['measured']!r}")
    size = _anchor_size(block)
    anchor = f"anchor_{size}"
    _prove(anchor in ranges, f"no Phase 40 range for {anchor!r}")
    values = {
        anchor: block["anchor_curve"][size]["rank"],
        "r_q_committed": block["r_q"]["committed"]["n1"],
        "r_q_minted": block["r_q"]["minted"]["n1"],
    }
    readings = {
        name: {"value": value, "range": ranges[name], "label": in_range(value, *ranges[name])}
        for name, value in values.items()
    }
    return {"measured": True, "anchor": anchor, "readings": readings}


def d21_reading(comparisons_by_cell):
    """D-21 (prediction, descriptive): over the pet_name cells keyed by exactly ORDERINGS x SEEDS,
    "held" per cell iff R_q n1 is fora on both lists and the anchor rank dentro; prediction_held is
    None while any cell is not measured. Never a criterion."""
    expected = {(o, s) for o in ORDERINGS for s in SEEDS}
    _prove(
        set(comparisons_by_cell) == expected,
        f"cells {sorted(set(comparisons_by_cell) ^ expected, key=repr)} are missing or extra",
    )
    per_cell = {}
    for cell, comparison in comparisons_by_cell.items():
        if not comparison["measured"]:
            per_cell[cell] = "not measured"
            continue
        labels = {name: r["label"] for name, r in comparison["readings"].items()}
        held = (
            labels["r_q_committed"] == OUTSIDE
            and labels["r_q_minted"] == OUTSIDE
            and labels[comparison["anchor"]] == INSIDE
        )
        per_cell[cell] = "held" if held else "not held"
    outcomes = set(per_cell.values())
    return {
        "prediction": ENTRIES["predictions"]["value"]["d21_d13_at_stop"],
        "per_cell": per_cell,
        "prediction_held": None if "not measured" in outcomes else outcomes == {"held"},
        "criterion": False,
    }


# =================================================================================================
# (9) THE UNITS AND THEIR ORDER (plan 41-04; D-22, ENTRIES["execution_order"], ["prep_order"]).
# A unit is one ledger attempt: a prep unit per (ordering, seed), then a cell per (target,
# ordering, seed). Its run id is run_id(unit); its end line names unit_record(unit).
# =================================================================================================


def prep_unit(ordering, seed):
    """D-22: the prep unit of one (ordering, seed): its calibration and its band inputs."""
    _prove_unit(ordering=ordering, seed=seed)
    return f"prep_{ordering}_seed{seed}"


def cell_unit(target, ordering, seed):
    """D-22: the unit of one cell (target, ordering, seed)."""
    _prove_unit(target=target, ordering=ordering, seed=seed)
    return f"cell_{target}_{ordering}_seed{seed}"


# D-22 + ENTRIES["prep_order"] (seed-major): the prep units first.
PREP_UNITS = tuple(prep_unit(o, s) for s in SEEDS for o in ORDERINGS)
# D-22: then every greedy cell pair by pair (TARGETS order, SEEDS order), then every gradient cell.
CELL_UNITS = tuple(cell_unit(t, o, s) for o in ORDERINGS for t in TARGETS for s in SEEDS)
UNITS = PREP_UNITS + CELL_UNITS

_UNIT_KEYS = types.MappingProxyType(
    {
        **{prep_unit(o, s): ("prep", o, s) for s in SEEDS for o in ORDERINGS},
        **{
            cell_unit(t, o, s): ("cell", t, o, s) for o in ORDERINGS for t in TARGETS for s in SEEDS
        },
    }
)
_prove(tuple(_UNIT_KEYS) == UNITS, "the unit keys are not UNITS, in UNITS order")


def unit_key(unit):
    """D-22: ``("prep", ordering, seed)`` or ``("cell", target, ordering, seed)``; refuses a name
    outside UNITS."""
    _prove(isinstance(unit, str) and unit in _UNIT_KEYS, f"unit {unit!r} is not one of UNITS")
    return _UNIT_KEYS[unit]


def unit_record(unit):
    """D-22 / D-24: the record a unit's ledger end line names: calibration_record(ordering, seed)
    for a prep unit (the band record carries no provenance.run), cell_record(...) for a cell."""
    kind, *key = unit_key(unit)
    return calibration_record(*key) if kind == "prep" else cell_record(*key)


def pair_units(target, ordering):
    """D-16: the two cells of one (target, ordering) pair, in SEEDS order."""
    return tuple(cell_unit(target, ordering, s) for s in SEEDS)


# =================================================================================================
# (10) THE STOP READINGS (ERASE-07, D-07, D-27) AND THE D-26 CONFIRMATION ACCOUNTING. The driver's
# per-checkpoint stop is proved equal to phase35_prereg.e1_stop on every reads sequence.
# =================================================================================================


def _is_seconds(value):
    """A finite real >= 0 (bool excluded): a measured time, never None."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def stop_readings(reads):
    """ERASE-07: phase35_prereg.e1_stop's ``readings`` from the driver's per-checkpoint reads,
    ``(checkpoint, k16_zero, k48_zero or None)`` in GRID order from GRID[0] with no gap or repeat:
    k48_zero is None exactly when the K = read_k read is not zero, and nothing is read after a
    confirmed zero. A prefix of GRID is allowed (the driver calls this after each checkpoint)."""
    readings = {}
    for index, read in enumerate(reads):
        _prove(
            isinstance(read, collections.abc.Sequence)
            and not isinstance(read, str)
            and len(read) == 3,
            f"read {index} {read!r} is not (checkpoint, k16_zero, k48_zero)",
        )
        checkpoint, k16, k48 = read
        _prove(
            not any(r["curve_k_zero"] and r["full_fidelity_k_zero"] for r in readings.values()),
            f"read {index} at checkpoint {checkpoint!r} comes after a confirmed zero",
        )
        _prove(
            index < len(GRID) and checkpoint == GRID[index],
            f"read {index} at checkpoint {checkpoint!r}: reads run in GRID {GRID} order from "
            "GRID[0], with no gap and no repeat",
        )
        _prove(isinstance(k16, bool), f"checkpoint {checkpoint}: k16_zero {k16!r} is not a bool")
        _prove(
            isinstance(k48, bool) if k16 else k48 is None,
            f"checkpoint {checkpoint}: k48_zero {k48!r} must be a bool iff the K = read_k read is "
            "zero, else None",
        )
        readings[checkpoint] = {"curve_k_zero": k16, "full_fidelity_k_zero": k48}
    return readings


def driver_stop(reads):
    """ERASE-07 / D-26: the predicate the driver applies after each checkpoint: the first
    checkpoint whose K = read_k read and K = confirm_k confirmation are both zero; NOT_REACHED once
    every GRID checkpoint is read with no such checkpoint; None while reads are a strict prefix of
    GRID with no stop (continue). On every complete reads sequence it equals
    ``phase35_prereg.e1_stop(grid=E1_CHECKPOINT_GRID, readings=stop_readings(reads))["stop"]``."""
    readings = stop_readings(reads)
    for checkpoint, reading in readings.items():
        if reading["curve_k_zero"] and reading["full_fidelity_k_zero"]:
            return checkpoint
    return phase35_prereg.NOT_REACHED if len(readings) == len(GRID) else None


# D-26: one confirmation of a cell, as the cell record carries it.
CONFIRMATION_KEYS = ("checkpoint", "k48_zero", "seconds", "started_utc", "finished_utc", "record")


def confirmation_failures(confirmations, reads=None):
    """D-26: the failures of a cell's K = confirm_k confirmations; [] when they hold. At most one
    per GRID checkpoint, at most ENTRIES["k48_confirmations"]["value"]["max_per_cell"] per cell,
    each with its measured seconds. Given the cell's reads, each confirmation sits at a checkpoint
    whose K = read_k read was zero, agrees with that read's k48_zero, and every zero read has its
    confirmation."""
    cap = ENTRIES["k48_confirmations"]["value"]["max_per_cell"]
    read_k = E1_CHECKPOINT_GRID["read_k"]
    failures = []
    if len(confirmations) > cap:
        failures.append(f"D-26: {len(confirmations)} confirmations, above max_per_cell = {cap}")
    valid = {}
    for index, item in enumerate(confirmations):
        if not isinstance(item, collections.abc.Mapping):
            failures.append(f"D-26: confirmation {index} is {type(item).__name__}, not a mapping")
            continue
        if set(item) != set(CONFIRMATION_KEYS) or len(item) != len(CONFIRMATION_KEYS):
            failures.append(
                f"D-26: confirmation {index} keys {sorted(item)} are not {list(CONFIRMATION_KEYS)}"
            )
            continue
        checkpoint = item["checkpoint"]
        if checkpoint not in GRID:
            failures.append(f"D-26: confirmation at checkpoint {checkpoint!r} outside GRID {GRID}")
            continue
        if checkpoint in valid:
            failures.append(f"D-26: checkpoint {checkpoint} confirmed twice (one per checkpoint)")
        valid[checkpoint] = item
        if not isinstance(item["k48_zero"], bool):
            failures.append(
                f"D-26: checkpoint {checkpoint} k48_zero {item['k48_zero']!r} not a bool"
            )
        if not _is_seconds(item["seconds"]):
            failures.append(
                f"D-26: checkpoint {checkpoint} seconds {item['seconds']!r} is not a finite "
                "real >= 0"
            )
    if reads is None:
        return failures
    readings = stop_readings(reads)
    for checkpoint, item in valid.items():
        reading = readings.get(checkpoint)
        if reading is None:
            failures.append(
                f"D-26: confirmation at checkpoint {checkpoint} has no K = {read_k} read"
            )
        elif not reading["curve_k_zero"]:
            failures.append(
                f"D-26: confirmation at checkpoint {checkpoint} whose K = {read_k} read was "
                "non-zero"
            )
        elif item["k48_zero"] != reading["full_fidelity_k_zero"]:
            failures.append(
                f"D-26: checkpoint {checkpoint} k48_zero {item['k48_zero']!r} != the read's "
                f"{reading['full_fidelity_k_zero']!r}"
            )
    for checkpoint, reading in readings.items():
        if reading["curve_k_zero"] and checkpoint not in valid:
            failures.append(
                f"D-26: the zero K = {read_k} read at checkpoint {checkpoint} is without its "
                "confirmation"
            )
    return failures


def confirmation_hours(confirmations):
    """D-26: the hours of a cell's confirmations (math.fsum of their seconds / 3600), charged to
    E1's share; refuses confirmations that fail confirmation_failures."""
    failures = confirmation_failures(confirmations)
    _prove(not failures, f"confirmations refused: {failures}")
    return math.fsum(item["seconds"] for item in confirmations) / 3600


# =================================================================================================
# (11) THE D-05 VARIANT, D-02 EQUALITY AND D-13 CONTROL-GAP RULES (ENTRIES["alternative_variant"],
# ["d02_equality"], ["control_gap_scope"]), written before any run.
# =================================================================================================

ADAPTIVE, STATIC = VARIANTS = ("adaptive", "static")


def ordering_cost_fits(seconds):
    """D-05: a cell's ordering cost fits in unit_prices.e1_ordering_seconds of the budget."""
    _prove(_is_seconds(seconds), f"ordering cost {seconds!r} is not a finite real >= 0")
    return seconds <= ENTRIES["e1_unit_prices"]["value"]["e1_ordering_seconds"]


def alternative_variant(cpu_seconds, mps_seconds):
    """D-05 + ENTRIES["alternative_variant"]: ADAPTIVE iff the ordering cost fits on both the CPU
    rehearsal and the MPS launch-gate smoke, else STATIC; both must be measured (None refused)."""
    for name, value in (("cpu_seconds", cpu_seconds), ("mps_seconds", mps_seconds)):
        _prove(
            _is_seconds(value),
            f"{name} {value!r} is not a measured finite real >= 0 (None: not yet measured)",
        )
    fits = ordering_cost_fits(cpu_seconds) and ordering_cost_fits(mps_seconds)
    return ADAPTIVE if fits else STATIC


def rerank_points(variant, *, calibration):
    """D-01, D-03, D-05: where the gradient ordering is (re-)ranked, 0 being the intact adapter.
    ADAPTIVE: a cell at 0 and every GRID checkpoint but the last; a calibration (rank stop) at 0
    and every GRID checkpoint. STATIC: once, at 0."""
    _prove(variant in VARIANTS, f"variant {variant!r} is not one of {VARIANTS}")
    _prove(isinstance(calibration, bool), f"calibration {calibration!r} is not a bool")
    if variant == STATIC:
        return (0,)
    return (0,) + (GRID if calibration else GRID[:-1])


def d02_check(grad_value, nograd_value):
    """D-02 + ENTRIES["d02_equality"]: the grad-path value NLL against value_span_nll_mean; any
    non-zero or non-finite difference stops for Rafael, never a tolerance."""
    for name, value in (("grad_value", grad_value), ("nograd_value", nograd_value)):
        _prove(
            isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{name} {value!r} is not a real",
        )
    equal = grad_value == nograd_value
    finite = math.isfinite(grad_value) and math.isfinite(nograd_value)
    return {
        "grad": grad_value,
        "nograd": nograd_value,
        "difference": grad_value - nograd_value,
        "equal": equal,
        "stop": not (equal and finite),
    }


def control_gap_check(measured, committed, *, device):
    """D-13 + ENTRIES["control_gap_scope"]: the re-measured control gap against the committed
    per_seed[seed].full.dialogue_gap.gap; inequality stops on mps; on the cpu rehearsal it is
    recorded, labelled rehearsal, never refused."""
    _prove(device in ("mps", "cpu"), f"device {device!r} is not mps or cpu")
    for name, value in (("measured", measured), ("committed", committed)):
        _prove(
            isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{name} {value!r} is not a real",
        )
    equal = measured == committed
    return {
        "measured": measured,
        "committed": committed,
        "equal": equal,
        "device": device,
        "rehearsal": device == "cpu",
        "stop": device == "mps" and not equal,
    }


# =================================================================================================
# (12) PER-UNIT OUTCOMES AND PAIR PROGRESS (D-22, D-24): read from the append-only ledger, never
# from logs (phase40_prereg.seed_outcomes / pending_seeds re-keyed per unit).
# =================================================================================================


def _prove_units(units):
    """Every unit a member of UNITS."""
    unknown = [u for u in units if not (isinstance(u, str) and u in _UNIT_KEYS)]
    _prove(not unknown, f"units {unknown!r} are not in UNITS")


def unit_outcomes(ledger_lines, units):
    """D-24: each unit whole / dropped / not_run from its LAST ledger attempt of run_id(unit); a
    whole unit's end line names unit_record(unit)."""
    import phase36_ledger  # torch-free; lazy so the import surface stays small

    _prove_units(units)
    attempts = phase36_ledger._attempts(ledger_lines)
    outcomes = {}
    for unit in units:
        mine = [(start, close) for start, close in attempts if start["run_id"] == run_id(unit)]
        if not mine:
            outcomes[unit] = "not_run"
            continue
        _prove(
            all(close is not None for _, close in mine),
            f"unit {unit}: an attempt is still open: phase36_ledger.py reconcile first",
        )
        _prove(
            not any(close["event"] == "end" for _, close in mine[:-1]),
            f"unit {unit}: a whole unit has a later attempt (R-3 b: never for a completed unit)",
        )
        close = mine[-1][1]
        if close["event"] == "lost":
            outcomes[unit] = "dropped"
        else:
            _prove(
                close["record"] == unit_record(unit),
                f"unit {unit}: the end line names {close['record']!r}, not {unit_record(unit)}",
            )
            outcomes[unit] = "whole"
    return outcomes


def pending_units(outcomes, rerun=frozenset()):
    """D-24 / R-3 b: the not_run units plus each dropped unit in ``rerun`` (Rafael's manifest
    approved it), in UNITS order. A whole or not_run unit is never in ``rerun``."""
    _prove_units(outcomes)
    _prove(
        all(outcomes.get(u) == "dropped" for u in rerun),
        f"R-3 b: only a dropped unit can be re-run, never a whole or not-run one ({sorted(rerun)})",
    )
    return tuple(
        unit
        for unit in UNITS
        if outcomes.get(unit) == "not_run" or (outcomes.get(unit) == "dropped" and unit in rerun)
    )


def pair_progress(outcomes):
    """D-23: the (target, ordering) pairs, in CELL_UNITS order, with both seeds whole
    (completed), one seed whole (half_done), or none (untouched)."""
    missing = [u for u in CELL_UNITS if u not in outcomes]
    _prove(not missing, f"outcomes lack cells {missing}")
    progress = {"completed": [], "half_done": [], "untouched": []}
    for ordering in ORDERINGS:
        for target in TARGETS:
            whole = sum(outcomes[u] == "whole" for u in pair_units(target, ordering))
            key = "completed" if whole == len(SEEDS) else "half_done" if whole else "untouched"
            progress[key].append((target, ordering))
    return {key: tuple(pairs) for key, pairs in progress.items()}


# =================================================================================================
# (13) THE D-23 PAUSE AND ITS RESUME DECLARATION (ENTRIES["e1_pause"], ["resume_declaration"]).
# =================================================================================================

RESUME_ROOT = "data/phase41_resume"
RESUME_DECLARATION_KEYS = ("e1_hours_at_pause", "cells", "approved")


def resume_declaration_name(n):
    """D-23: the n-th resume declaration (n >= 1), under RESUME_ROOT (data/, gitignored)."""
    _prove_count("n", n, low=1)
    return f"{RESUME_ROOT}/resume_{n:02d}.json"


def resume_declaration_failures(declaration, *, e1_hours_at_pause):
    """D-23: the failures of a resume declaration; [] when it holds: exactly
    RESUME_DECLARATION_KEYS, e1_hours_at_pause equal to the pause notice's e1_hours, cells a
    non-empty list of distinct CELL_UNITS, and Rafael's approved. Never raises."""
    if not isinstance(declaration, collections.abc.Mapping):
        return [f"D-23: declaration is {type(declaration).__name__}, not a mapping"]
    keys = tuple(declaration)
    if set(keys) != set(RESUME_DECLARATION_KEYS) or len(keys) != len(RESUME_DECLARATION_KEYS):
        missing = sorted(set(RESUME_DECLARATION_KEYS) - set(keys))
        extra = sorted(set(keys) - set(RESUME_DECLARATION_KEYS))
        return [f"D-23: declaration keys: missing {missing}, extra {extra}"]
    failures = []
    at = declaration["e1_hours_at_pause"]
    if not (_is_seconds(at) and at == e1_hours_at_pause):
        failures.append(f"D-23: e1_hours_at_pause {at!r} != the notice's {e1_hours_at_pause!r}")
    cells = declaration["cells"]
    if not (
        isinstance(cells, (list, tuple))
        and cells
        and all(isinstance(c, str) and c in CELL_UNITS for c in cells)
        and len(set(cells)) == len(cells)
    ):
        failures.append(f"D-23: cells {cells!r} are not a non-empty list of distinct CELL_UNITS")
    if not _approved(declaration["approved"]):
        failures.append(f"D-23: approved {declaration['approved']!r} lacks Rafael's 'approved'")
    return failures


def e1_pause_due(e1_seconds, *, cell, declarations):
    """D-23, checked before every cell: True iff E1's spent seconds (lost attempts included)
    reach ENTRIES["e1_share_hours"] and no resume declaration listing ``cell`` holds. Here a
    declaration is checked against its own e1_hours_at_pause; the driver checks that value against
    the pause notice (resume_declaration_failures) before passing the declaration."""
    _prove(_is_seconds(e1_seconds), f"e1_seconds {e1_seconds!r} is not a finite real >= 0")
    _prove(cell in CELL_UNITS, f"cell {cell!r} is not one of CELL_UNITS")
    if e1_seconds < ENTRIES["e1_share_hours"]["value"] * 3600:
        return False
    for declaration in declarations:
        if not isinstance(declaration, collections.abc.Mapping):
            continue
        own = declaration.get("e1_hours_at_pause")
        if not resume_declaration_failures(declaration, e1_hours_at_pause=own) and (
            cell in declaration["cells"]
        ):
            return False
    return True


def pause_notice(*, by_front_seconds, total_seconds, outcomes):
    """D-23: what Rafael reads at the pause: E1 hours (phase36_ledger.spent's by_front, lost
    attempts included), the completed and half-done pairs, and the hours left for E3, E4 (their
    front_hours minus spent) and to the stop line, all from the inputs and the budget."""
    fronts = ("E1", "E3", "E4")
    for front in fronts:
        _prove(
            front in by_front_seconds and _is_seconds(by_front_seconds[front]),
            f"by_front_seconds[{front!r}] is missing or not a finite real >= 0",
        )
    _prove(_is_seconds(total_seconds), f"total_seconds {total_seconds!r} is not a finite real >= 0")
    progress = pair_progress(outcomes)
    hours = _BUDGET["front_hours"]
    return {
        "e1_hours": by_front_seconds["E1"] / 3600,
        "completed_pairs": progress["completed"],
        "half_done_pairs": progress["half_done"],
        "remaining_hours": {f: hours[f] - by_front_seconds[f] / 3600 for f in fronts[1:]},
        "to_90h": _BUDGET["stop_line_hours"] - total_seconds / 3600,
    }


# =================================================================================================
# (14) R-3 b PER UNIT (D-24): phase40_prereg's crash readers re-keyed per unit (a prep unit or a
# cell); a new attempt of a dropped unit only, never a rerun of a whole unit.
# =================================================================================================

# R-3 b (c): a crashed attempt's partial outputs are kept (never deleted) under DROPPED_ROOT, which
# .gitignore's data/ covers, and listed in the records.
DROPPED_ROOT = "data/phase41_dropped"
DROPPED_MANIFEST = "manifest.json"
DROPPED_MANIFEST_KEYS = (
    "unit",
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


def lost_attempts(ledger_lines, unit):
    """R-3 b (e): the utc of every lost line of run_id(unit), in ledger order; reconcile writes a
    lost line only for an open start, so each closes a crashed attempt."""
    _prove_units((unit,))
    return [
        line["utc"]
        for line in ledger_lines
        if line["event"] == "lost" and line["run_id"] == run_id(unit)
    ]


def dropped_attempt_dir(unit, lost_utc):
    """R-3 b (c): where a crashed attempt's kept outputs and its manifest live (no ':' in it)."""
    _prove_units((unit,))
    _prove(isinstance(lost_utc, str) and lost_utc, f"lost_utc {lost_utc!r} is not a non-empty str")
    return f"{DROPPED_ROOT}/{run_id(unit).replace('/', '_')}_{lost_utc.replace(':', '')}"


def _text(value):
    """A str non-empty after strip."""
    return isinstance(value, str) and bool(value.strip())


def _approved(text):
    """Rafael's approved (Phase 40 WR-02, regex verbatim): the standalone token ``approved``,
    never a negated one ("not", "não", "nao" or "un" before it)."""
    return (
        isinstance(text, str)
        and re.search(r"(?<![\w-])approved\b", text) is not None
        and re.search(r"\b(?:not|não|nao|un)[\s-]*approved\b", text, re.IGNORECASE) is None
    )


def dropped_manifest_failures(manifest, *, unit, lost_utc):
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
    if manifest["unit"] != unit:
        failures.append(f"unit {manifest['unit']!r} != {unit!r} (b: same unit)")
    if manifest["run_id"] != run_id(unit):
        failures.append(f"run_id {manifest['run_id']!r} != {run_id(unit)!r} (b: same unit)")
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
    prefix = dropped_attempt_dir(unit, lost_utc) + "/"
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
    """R-3 b (b), only for a unit's latest crashed attempt: the launch HEAD is the drop-time HEAD,
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
