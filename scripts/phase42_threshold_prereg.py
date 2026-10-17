"""Phase 42 fill file 2 (owner phase 42): the recall threshold of every E3 grid recipe, filled from
the committed sigma = 0 controls (RECIPE-03; 42-CONTEXT D-12, D-18, D-19).

It holds only ``e3_recall_threshold``, the one Phase 42 slot that consumes in-phase inputs: Phase
35 leg (a) makes it precede every ``results/phase42_*`` record except the control records, and leg
(b) makes every control record precede it.

Its kwargs are phase42_prereg's pre-registered builder, so nothing is typed: each recipe's
threshold is F_Y x ITS OWN control's recall on each leg (taught, held-out), read from the committed
records; the v4.0 recipe's from the reused v4.0 record; REFUSED for a control that does not learn
(phase29_prereg.control_is_unlearnable).

Frozen from its first commit: any correction is a dated continuation, never an edit.
"""

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:] = [
    p for p in (str(_ROOT / "scripts"), str(_ROOT / "src")) if p not in sys.path
] + sys.path

import phase35_prereg  # noqa: E402  (needs the sys.path insert above)
import phase42_prereg  # noqa: E402  (same)

E3_RECALL_THRESHOLD = phase35_prereg.fill(
    "e3_recall_threshold", **phase42_prereg.threshold_fill_inputs()
)
