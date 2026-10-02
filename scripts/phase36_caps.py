"""Phase 36 unit caps (D-09): the per-front unit limits the committed budget carries, enforced here.

The v6.0 pre-registration's slot rules check hours, not units, and that module is closed, so the
cap contract lives in Phase 36's own code. An owner phase (38, 39, 41, 42) calls
``check_unit_caps`` from its fill file or driver; ``tests/test_phase36_caps.py`` scans every
tracked owner fill file and reds on an over-cap value.

Caps are read only from the COMMITTED budget record (``phase30_points._tracked_json``: an untracked
or working-tree-edited record is refused). The budget contract is re-proved locally from the public
names of the v6.0 pre-registration; its private helpers are never called. Torch-free at import:
``seed_list`` (torch) is called inside ``prove_budget_shape`` only.
"""

import collections.abc
import math
import pathlib
import subprocess
import sys
import types

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase30_points  # noqa: E402  (scripts/ is not a package; torch-free)
import phase35_prereg  # noqa: E402  (same)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase36_caps] {message}")


BUDGET_RECORD = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase36_budget")
)

# D-09 plus the plan-time additions surfaced at the budget checkpoint. R1b and the probes carry no
# caps (R1b is one erased-arm reading, D-04).
CAP_FIELDS = types.MappingProxyType(
    {
        "E1": ("cells", "checkpoints_per_cell", "k48_confirms_per_cell", "calibrations"),
        "E2": ("adapters", "seeds"),
        "E3": ("recipes", "sigmas", "max_steps", "max_batch"),
        "E4": ("points",),
        "E5": ("sets", "max_set_size", "prefixes"),
        "E6": ("adapters", "anchor_adapters", "anchor_slots", "entries", "max_k"),
    }
)

# The owner slots whose filled values are scanned against the caps, and the front each binds.
SLOT_COUNTS = types.MappingProxyType(
    {
        "e1_checkpoint_grid": "E1",
        "e3_grid_subset": "E3",
        "e5_set_sizes": "E5",
        "e6_entry_subset": "E6",
    }
)

_prove(set(SLOT_COUNTS) <= set(phase35_prereg.SLOTS), "SLOT_COUNTS names an undeclared slot")
_prove(set(CAP_FIELDS) < set(phase35_prereg.V6_MPS_FRONTS), "CAP_FIELDS names an unknown front")


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def tracked_files():
    """``git ls-files`` of the repository, as a list."""
    listed = subprocess.run(
        ["git", "ls-files"], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    return listed.stdout.splitlines()


def prove_budget_shape(record):
    """The v6.0 budget contract re-proved locally, plus the D-09 ``unit_caps`` block. Returns it."""
    fields = {"front_hours", "total_hours", "stop_line_hours", "e2_seed_count", "unit_caps"}
    _prove(
        isinstance(record, collections.abc.Mapping) and fields <= set(record),
        f"the budget record must be a mapping carrying {sorted(fields)}",
    )
    hours = record["front_hours"]
    fronts = phase35_prereg.V6_MPS_FRONTS
    _prove(
        isinstance(hours, collections.abc.Mapping) and set(hours) == set(fronts),
        f"front_hours must be keyed by exactly V6_MPS_FRONTS {fronts}",
    )
    for front, value in hours.items():
        _prove(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value >= 0,
            f"front_hours[{front!r}] = {value!r} is not a finite number >= 0",
        )
    total = math.fsum(hours.values())
    _prove(
        record["total_hours"] == total,
        f"total_hours {record['total_hours']!r} is not the exact fsum of front_hours ({total})",
    )
    stop_line = record["stop_line_hours"]
    ceiling = phase35_prereg.ENTRIES["mps_ceiling_hours"]["value"]
    _prove(
        isinstance(stop_line, (int, float))
        and not isinstance(stop_line, bool)
        and math.isfinite(stop_line),
        f"stop_line_hours {stop_line!r} is not finite",
    )
    _prove(
        total <= stop_line <= ceiling,
        f"need total {total} <= stop_line_hours {stop_line} <= mps_ceiling_hours {ceiling}",
    )
    seeds = record["e2_seed_count"]
    least = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    _prove(
        isinstance(seeds, int)
        and not isinstance(seeds, bool)
        and least <= seeds <= len(phase35_prereg.seed_list()),
        f"e2_seed_count {seeds!r} is not an int in {least}..len(seed_list())",
    )
    caps = record["unit_caps"]
    _prove(
        isinstance(caps, collections.abc.Mapping) and set(caps) == set(CAP_FIELDS),
        f"unit_caps must be keyed by exactly {sorted(CAP_FIELDS)}",
    )
    for front, names in CAP_FIELDS.items():
        block = caps[front]
        _prove(
            isinstance(block, collections.abc.Mapping) and set(block) == set(names),
            f"unit_caps[{front!r}] must carry exactly {names}",
        )
        for name, value in block.items():
            _prove(
                _is_count(value), f"unit_caps[{front!r}][{name!r}] = {value!r} is not an int >= 0"
            )
    _prove(
        caps["E2"]["seeds"] == seeds,
        f"unit_caps['E2']['seeds'] {caps['E2']['seeds']} is not e2_seed_count {seeds}",
    )
    return record


def committed_budget(tracked=None):
    """The COMMITTED budget record, shape re-proved. Refuses while it is untracked or edited."""
    tracked = tracked_files() if tracked is None else tracked
    return prove_budget_shape(
        phase30_points._tracked_json(BUDGET_RECORD, tracked, "the v6.0 budget")
    )


def check_unit_caps(front, *, tracked=None, **counts):
    """Refuse any count above the committed cap of ``front`` (D-09). Returns the counts checked."""
    _prove(front in CAP_FIELDS, f"front {front!r} has no unit caps; capped: {tuple(CAP_FIELDS)}")
    _prove(counts, f"no count given for front {front}")
    for name, count in counts.items():
        _prove(name in CAP_FIELDS[front], f"{name!r} is not a {front} cap: {CAP_FIELDS[front]}")
        _prove(_is_count(count), f"{front} {name} = {count!r} is not an int >= 0")
    caps = committed_budget(tracked)["unit_caps"][front]
    for name, count in counts.items():
        _prove(
            count <= caps[name],
            f"{front} {name} = {count} exceeds the committed cap {caps[name]} in {BUDGET_RECORD}. "
            "D-09: exceeding a Phase 36 cap needs Rafael's approved",
        )
    return dict(counts)


def counts_for(slot, value):
    """The cap-relevant counts of an owner slot's filled ``value``."""
    _prove(slot in SLOT_COUNTS, f"slot {slot!r} binds no unit cap; capped: {tuple(SLOT_COUNTS)}")
    if slot == "e1_checkpoint_grid":
        return {"checkpoints_per_cell": len(value["checkpoints"])}
    if slot == "e3_grid_subset":
        recipes = [c["recipe"] for c in value["cells"]]
        return {
            "recipes": len({tuple(sorted(r.items())) for r in recipes}),
            "max_steps": max(r["steps"] for r in recipes),
            "max_batch": max(r["batch"] for r in recipes),
        }
    if slot == "e5_set_sizes":
        return {"sets": len(value), "max_set_size": max(value.values())}
    return {"entries": len(value)}


def owner_overruns(values_by_slot, record):
    """One failure string per owner count above ``record``'s cap; [] when every value fits."""
    failures = []
    for slot, value in values_by_slot.items():
        front = SLOT_COUNTS[slot]
        caps = record["unit_caps"][front]
        for name, count in counts_for(slot, value).items():
            if count > caps[name]:
                failures.append(f"{slot}: {front} {name} = {count} exceeds the cap {caps[name]}")
    return failures
