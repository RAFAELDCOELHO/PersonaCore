"""Phase 41 fill file 2: condition (a)'s floors and condition (c)'s band, filled from the committed
stage-1 records (ERASE-06, ERASE-09; 41-CONTEXT D-10, D-12, D-13).

It holds BOTH in-phase-input slots, ``e1_condition_a_floors`` and ``e1_condition_c_band_inputs``,
in ONE file: split into two, each file's commit would have to precede the other slot's records
under the Phase 35 slot-ordering leg (a), a deadlock (red case b7_41). It is committed after every
declared input (leg (b)) and before every other ``results/phase41_*`` record (leg (a)).

Its kwargs are phase41_prereg's pre-registered builders, so nothing is typed: each (target,
ordering, seed) floor is computed by the e1_condition_a_floors rule (lock_erasure_floor,
floor_branch) from the committed (ordering, seed) calibration record and Phase 19's calibration
corpus; each (seed, ordering) band is DIALOGUE_GAP_BAND of the committed band-input record's
control gap and Phase 40's gap noise floor.

Frozen from its first commit: any correction is a dated continuation, never an edit.
"""

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:] = [
    p for p in (str(_ROOT / "scripts"), str(_ROOT / "src")) if p not in sys.path
] + sys.path

import phase35_prereg  # noqa: E402  (needs the sys.path insert above)
import phase41_prereg  # noqa: E402  (same)

E1_CONDITION_A_FLOORS = phase35_prereg.fill(
    "e1_condition_a_floors", **phase41_prereg.floors_fill_inputs()
)
E1_CONDITION_C_BAND_INPUTS = phase35_prereg.fill(
    "e1_condition_c_band_inputs", **phase41_prereg.band_fill_inputs()
)
