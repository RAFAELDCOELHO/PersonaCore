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
