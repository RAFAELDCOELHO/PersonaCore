"""Phase 38 fill of e5_set_sizes: the E5 set sizes, declared before any scoring (RANK-01).

What it declares (38-CONTEXT):
- D-07: one maximum set per slot, for all eight slots;
- D-08: the nested sizes are read at prefixes of that one set (phase38_prereg.nested_sizes);
- D-09: "as far as minting allows" — each size is read from the committed minting record;
- D-31: |R| counts the taught value, so size = min(e5_max_set_size, n_cleared + 1)
  (phase38_prereg.max_set_size), never typed.

Fill file 2 of Phase 38 (Phase 35 legs (a)/(b)): it consumes results/phase38_minting.json, so it is
committed after that record and before every other results/phase38_* record.

Frozen once any other results/phase38_* record exists: any correction is a dated continuation
module, never an edit.
"""

import json
import pathlib

import phase35_prereg
import phase36_caps
import phase38_prereg

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MINTING_RECORD = phase38_prereg.MINTING_RECORD
_RECORD = json.loads((_REPO_ROOT / MINTING_RECORD).read_text(encoding="utf-8"))
_SIZES = {
    slot: phase38_prereg.max_set_size(_RECORD["slots"][slot]["n_cleared"])
    for slot in phase38_prereg.SLOTS
}
_DRIFT = {
    slot: (size, _RECORD["slots"][slot]["max_set_size"])
    for slot, size in _SIZES.items()
    if size != _RECORD["slots"][slot]["max_set_size"]
}
if _DRIFT:
    raise SystemExit(
        f"[phase38_sizes_prereg] max_set_size(n_cleared) != the record's max_set_size: {_DRIFT}"
    )

_DERIVATION = {
    "value": _SIZES,
    "derivation": "D-07: one maximum set per slot, for all eight slots; D-08: nested sizes are "
    "read at prefixes of that set; D-09: as far as minting allows; D-31: |R| counts the taught "
    "value, so size = min(e5_max_set_size, n_cleared + 1) per slot, read from the committed "
    "minting record through phase38_prereg.max_set_size, never typed.",
    "kind": "derived",
    "source": f"38-CONTEXT D-07, D-08, D-09 (255380f), D-31 (f7ad285); "
    f"{MINTING_RECORD} slots[*].n_cleared",
}

E5_SET_SIZES = phase35_prereg.fill(
    "e5_set_sizes",
    set_sizes=_SIZES,
    input_records=(MINTING_RECORD,),
    derivation=_DERIVATION,
)

# D-23: sets and max_set_size only; the 8 prefix readings are checked by the rank driver against
# phase38_prereg.APPROVED_E5_PREFIXES, never here.
phase36_caps.check_unit_caps("E5", **phase36_caps.counts_for("e5_set_sizes", E5_SET_SIZES))
