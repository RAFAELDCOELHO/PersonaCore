"""Phase 37 pre-registration: the R1b tolerance, the definition of "replicated" and every rule R1a
and R1b apply, frozen before any ``results/phase37_*`` record (37-CONTEXT D-01, REPRO-03 SC3/SC4).

This module is committed before R1a's record and R1b's records alike. It fills the v6.0 slot
``r1b_tolerance_and_replicated`` exactly once, as the module-level binding
``R1B_TOLERANCE_AND_REPLICATED``. Once the first Phase 37 record lands, every commit touching this
file must strictly precede it (the v6.0 slot-ordering leg (a)), so nothing here can be tuned to a
replica's numbers.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer, PREREG-07). The three zero tolerances are Rafael's ruling and say so with
``kind = "preference"`` (PREREG-06). The destroyed_pct tolerance and the R1b cost are computed at
import from committed records and never typed.

Torch-free at import: it reads JSON records and the public names of the closed v6.0
pre-registration, never the Phase 19 pin.
"""

import collections.abc
import fnmatch
import json
import math
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

import phase19_floor  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase35_prereg  # noqa: E402  (same; torch-free)
import phase36_prereg  # noqa: E402  (same; torch-free)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase37_*` file existed, tracked or untracked.
COMMITTED = "2026-10-03"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase37_prereg] {message}")


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
# (3) THE RECORD PATHS (D-01), derived from the path the v6.0 pre-registration reserved.
# =================================================================================================

RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase37_"))
R1A_RECORD = RECORD_GLOB.replace("*", "r1a.json")
R1B_RECORD = RECORD_GLOB.replace("*", "r1b.json")
R1B_ARM_RECORD = RECORD_GLOB.replace("*", "r1b_arm.json")
RECORDS = (R1A_RECORD, R1B_ARM_RECORD, R1B_RECORD)

for _path in RECORDS:
    _prove(fnmatch.fnmatch(_path, RECORD_GLOB), f"{_path} does not match {RECORD_GLOB}")
_prove(len(set(RECORDS)) == len(RECORDS), f"the record paths {RECORDS} are not distinct")

# The committed inputs this module reads. The tests prove each against the modules that own it.
ERASED_RECORD = "results/phase19_arm_erased.json"
CURVE_RECORD = "results/phase19_collateral_curve.json"
BUDGET_RECORD = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p.startswith("results/phase36_budget")
)
FLOOR_RECORD = phase19_floor.EVIDENCE_ARTIFACT["DIALOGUE_PPL_NOISE_FLOOR"]
_prove(
    FLOOR_RECORD == phase19_floor.EVIDENCE_ARTIFACT["NONTARGET_NOISE_FLOOR"],
    "the dialogue and non-target noise floors no longer share one evidence record",
)

# =================================================================================================
# (4) D-02: THE destroyed_pct TOLERANCE, computed from the records.
# =================================================================================================


def destroyed_pct_tolerance(dialogue_floor, gap):
    """MARGIN_K x the dialogue noise floor / the pre-erasure on-off gap x 100, in percentage points.

    The operation order is D-02's, left to right. Floating point is not associative: putting the
    x 100 first gives a result one ulp lower, so the order is part of the pre-registration.
    """
    return phase35_prereg.MARGIN_K * dialogue_floor / gap * 100


_FLOORS = _read(FLOOR_RECORD)
DIALOGUE_FLOOR = _FLOORS["dialogue_ppl_noise_floor"]["value"]
NONTARGET_FLOOR = _FLOORS["nontarget_noise_floor"]["value"]
_prove(
    DIALOGUE_FLOOR == phase19_floor.DIALOGUE_PPL_NOISE_FLOOR,
    f"{FLOOR_RECORD} dialogue floor {DIALOGUE_FLOOR!r} is not the locked constant",
)
_prove(
    NONTARGET_FLOOR == phase19_floor.NONTARGET_NOISE_FLOOR,
    f"{FLOOR_RECORD} non-target floor {NONTARGET_FLOOR!r} is not the locked constant",
)

_PRE = _read(ERASED_RECORD)["pre_erasure"]["dialogue_ppl"]
G0 = _PRE["adapter_on"] - _PRE["adapter_off"]  # r1a_rederive's g0 expression
DESTROYED_PCT_TOLERANCE = destroyed_pct_tolerance(DIALOGUE_FLOOR, G0)
_prove(
    math.isfinite(DESTROYED_PCT_TOLERANCE) and DESTROYED_PCT_TOLERANCE > 0,
    f"destroyed_pct tolerance {DESTROYED_PCT_TOLERANCE!r} is not a finite positive number",
)

# =================================================================================================
# (5) D-06: THE R1b COST, from the records, against 1.5x its budget front.
# =================================================================================================


def r1b_cost_hours(arm_minutes, sweep_minutes):
    """One erased arm plus one selection sweep, in hours (D-06)."""
    return (arm_minutes + sweep_minutes) / 60


R1B_COST_HOURS = r1b_cost_hours(
    _read(ERASED_RECORD)["config"]["wall_clock_min"], _read(CURVE_RECORD)["wall_clock_min"]
)
R1B_COST_CAP_HOURS = (
    phase36_prereg.ENTRIES["front_stop_factor"]["value"]
    * _read(BUDGET_RECORD)["front_hours"]["R1b"]
)
_prove(
    R1B_COST_HOURS <= R1B_COST_CAP_HOURS,
    f"R1b costs {R1B_COST_HOURS!r} h, above the {R1B_COST_CAP_HOURS!r} h cap (front_stop_factor x "
    "front_hours.R1b). D-06: this sum goes to Rafael BEFORE launch; nothing runs until he rules.",
)

# =================================================================================================
# (6) THE ENTRIES (D-02..D-07, D-11..D-16).
# =================================================================================================

_CONTEXT = "37-CONTEXT D-{} (d684f30)"
_ADDENDUM = "37-CONTEXT addendum D-{} (d710181)"
_RULINGS = "37-CONTEXT addendum D-{} (1eec113)"

_ENTRIES = {
    "tolerance_k": {
        "value": 0,
        "derivation": (
            "D-02: k is an integer count and the replica must give exactly the committed k. "
            "Rafael's ruling: no written derivation makes 0 follow from a measurement. The MPS k* "
            "curve agreement at |difference| = 0.0 (scripts/erasure_kstar_prereg.py, "
            "CURVE_AGREEMENT_DIALOGUE_TOLERANCE) is context, not a derivation."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('02')}; phase35_prereg.R1A_ASSERTIONS['k']",
    },
    "tolerance_target_correct": {
        "value": 0,
        "derivation": (
            "D-02: tolerance on the numerator of target_correct; the denominator must be equal "
            "exactly. Rafael's ruling, not derived from a measurement."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('02')}; phase35_prereg.R1A_ASSERTIONS['target_correct']",
    },
    "tolerance_nontargets_beyond_margin": {
        "value": 0,
        "derivation": (
            "D-02: tolerance on the count of non-targets beyond the margin; the denominator (the "
            "seven non-target slots) must be equal exactly. Rafael's ruling, not derived from a "
            "measurement."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('02')}; phase35_prereg.R1A_ASSERTIONS['nontargets_beyond_margin']"
        ),
    },
    "tolerance_destroyed_pct": {
        "value": DESTROYED_PCT_TOLERANCE,
        "derivation": (
            "D-02: MARGIN_K x floor / g0 x 100, in percentage points, in that operation order. "
            "MARGIN_K is erasure_gate.MARGIN_K via phase35_prereg.MARGIN_K; floor is "
            f"{FLOOR_RECORD}::dialogue_ppl_noise_floor.value; g0 is "
            f"{ERASED_RECORD}::pre_erasure.dialogue_ppl adapter_on minus adapter_off, the "
            "committed erased arm's pre-erasure on-off gap. Computed at import, never typed: "
            f"{DESTROYED_PCT_TOLERANCE!r}."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('02')}; {FLOOR_RECORD}; {ERASED_RECORD}",
    },
    "replicated_definition": {
        "value": tuple(phase35_prereg.R1A_ASSERTIONS),
        "derivation": (
            "D-03: REPLICATED iff for every key abs(replica - committed) <= tolerance[key] "
            "(inclusive, the gate's <=). Tuple keys require an equal denominator and compare "
            "numerators. Draw bit-identity is reported beside the result and never enters it."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('03')}; {_CONTEXT.format('02')}",
    },
    "draw_identity_description": {
        "value": ("completions", "entries"),
        "derivation": (
            "D-03: bit-identity of the replica's draws against the committed erased arm, counted "
            "in completions out of the committed count (216 entries x 48 completions) and in "
            "entries out of 216. Description only, never a criterion."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('03')}; {ERASED_RECORD}::draws",
    },
    "not_replicated_rule": {
        "value": "NOT_REPLICATED",
        "derivation": (
            "D-04: a replica outside the tolerance publishes a write-once NOT_REPLICATED record "
            "beside the v3.0 verdict; the verdict does not change. It carries the per-fact "
            "non-target context of D-12. A root-cause investigation comes before any new run."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('04')}; {_ADDENDUM.format('12')}",
    },
    "one_attempt": {
        "value": 1,
        "derivation": (
            "D-04 + D-11: one attempt. D-11, verbatim: A started attempt is THE attempt. Any R1b "
            "launch counts as D-04's one attempt, including a crash that leaves no record and "
            'only a ledger lost line. A relaunch needs Rafael\'s "approved", a ledger reconcile '
            "and a root-cause note first (the 36-07 W3 pattern). D-15, verbatim: D-11 governs "
            'EVERY relaunch. A second R1b run of any kind needs Rafael\'s "approved", a ledger '
            "reconcile and a root-cause note first. That covers a crash, a completed "
            "NOT_REPLICATED, and a D-07 divergence (k ≠ 78 or a different set). This "
            "supersedes D-07's \"A new run needs only Rafael's approved\". D-16, verbatim: The "
            "attempt starts at the ledger start line. A launch the driver refuses in preflight "
            "(dirty tree, untracked prereg, failed require_launch, wrong device, adapter "
            "mismatch) happens before the start line and runs nothing on MPS, so it is not an "
            'attempt. D-11\'s "Any R1b launch counts" means any launch that has written its '
            "start line. These are Rafael's rulings, quoted, not a reading of them."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('04')}; {_ADDENDUM.format('11')}; {_RULINGS.format('15')}; "
            f"{_RULINGS.format('16')}"
        ),
    },
    "prefix_divergence_rule": {
        "value": "set_equal",
        "derivation": (
            "D-07: the erased arm runs iff the re-measured k equals the committed k AND the set "
            "of the re-measured ordered[:k] equals the committed ordered_prefix set; how many "
            "positions moved is description. ablate_components (scripts/phase19_erasure.py) "
            "zeros both factors of each address on clones and refuses duplicates, so a set-equal "
            "prefix gives identical weights in any order. The arm receives the RE-MEASURED list: "
            "it sits downstream of the measurement. Otherwise the arm does not run and the "
            "record reports only k and the set difference."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('07')}; {CURVE_RECORD}::ordered_prefix",
    },
    "nontarget_context": {
        "value": ("replica_delta", "committed_delta", "abs_diff", "noise_floor"),
        "derivation": (
            "D-12: for each non-target slot, the replica pooled delta, the committed pooled "
            "delta and their absolute difference, beside nontarget_noise_floor.value. Context, "
            "never the criterion."
        ),
        "kind": "preference",
        "source": f"{_ADDENDUM.format('12')}; {FLOOR_RECORD}::nontarget_noise_floor.value",
    },
    "sweep_in_both_branches": {
        "value": ("ordered_prefix", "curve"),
        "derivation": (
            "D-14: the re-measured ordered[:k] and the curve rows are recorded in REPLICATED and "
            "NOT_REPLICATED alike, as description, so a root-cause investigation has the data. "
            "The verdict fields stay k and the set difference."
        ),
        "kind": "preference",
        "source": f"{_ADDENDUM.format('14')}; {_CONTEXT.format('07')}",
    },
    "r1b_scope": {
        "value": types.MappingProxyType(
            {
                "re_measured": (
                    "ordering_288_addresses",
                    "stopping_rule",
                    "k",
                    "a2_entries_216_at_k48",
                    "post_erasure",
                    "pre_erasure.dialogue_ppl",
                    "pre_erasure.retention_ppl",
                    "pre_erasure.exposure",
                ),
                "inherited": (
                    "committed_prefix_as_comparator",
                    "adapter_in_sha256",
                    "pre_erasure.per_fact",
                ),
            }
        ),
        "derivation": (
            "D-05: R1b re-measures the 288-address ordering, the stopping rule, k, the 216 A2 "
            "entries at K = 48 and the post-erasure block, plus the three pre-erasure quantities "
            "run_erasure_arm measures itself (its docstring: the other three pre-erasure "
            "quantities ARE measured here). It inherits the committed prefix as comparator, the "
            "adapter_in SHA-256 and the pre-erasure per_fact block, which the pin reads from "
            "Phase 18's committed record. The retrain and replicate arms are out of scope."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('05')}; scripts/phase19_erasure.py run_erasure_arm",
    },
    "r1b_cost_hours": {
        "value": R1B_COST_HOURS,
        "derivation": (
            "D-06: (erased-arm wall_clock_min + sweep wall_clock_min) / 60, read from "
            f"{ERASED_RECORD}::config.wall_clock_min and {CURVE_RECORD}::wall_clock_min, proved "
            "<= front_stop_factor x front_hours.R1b (phase36_prereg.ENTRIES and "
            f"{BUDGET_RECORD}) = {R1B_COST_CAP_HOURS!r} h at import. A sum above the cap goes to "
            "Rafael BEFORE launch."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('06')}; {ERASED_RECORD}; {CURVE_RECORD}; {BUDGET_RECORD}",
    },
    "r1a_extra_assertions": {
        "value": ("b_floor_from_replicate_arm", "verdict_matches_recorded"),
        "derivation": (
            "D-13: R1a also re-derives the (b) floor from results/phase19_arm_replicate.json, the "
            "way phase19_run.report() does, and adds that record to the input SHA-256 list. "
            "REPRO-01 SC1: the verdict and its three reasons equal the recorded Verdict section "
            "of results/phase19_erasure_report.md. The four REPRO-01 numbers stay the headline."
        ),
        "kind": "preference",
        "source": (
            f"{_ADDENDUM.format('13')}; results/phase19_arm_replicate.json; "
            "results/phase19_erasure_report.md"
        ),
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset(
    {
        "tolerance_k",
        "tolerance_target_correct",
        "tolerance_nontargets_beyond_margin",
        "tolerance_destroyed_pct",
        "replicated_definition",
        "draw_identity_description",
        "not_replicated_rule",
        "one_attempt",
        "prefix_divergence_rule",
        "nontarget_context",
        "sweep_in_both_branches",
        "r1b_scope",
        "r1b_cost_hours",
        "r1a_extra_assertions",
    }
)


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered fourteen."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(
        set(ENTRIES) == _ENTRY_NAMES,
        f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra",
    )


_prove_entries()

# =================================================================================================
# (7) THE SLOT FILL (D-01): once, the whole value of its module-level binding.
# =================================================================================================

R1B_TOLERANCE_AND_REPLICATED = phase35_prereg.fill(
    "r1b_tolerance_and_replicated",
    tolerance={key: ENTRIES[f"tolerance_{key}"]["value"] for key in phase35_prereg.R1A_ASSERTIONS},
    replicated_definition=ENTRIES["replicated_definition"],
)
# The slot accepts a SUBSET of the assertion keys; Phase 37 tolerates every one of them.
_prove(
    set(R1B_TOLERANCE_AND_REPLICATED["tolerance"]) == set(phase35_prereg.R1A_ASSERTIONS),
    "the filled tolerance does not cover every R1a assertion",
)

# =================================================================================================
# (8) THE RULES, MECHANICAL. Pure and torch-free; every output is JSON-serialisable.
# =================================================================================================


def _prove_number(name, value):
    _prove(
        isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
        f"{name} is {value!r}, not a finite number",
    )


def replicated(rederived):
    """D-03: REPLICATED iff every R1a assertion is within its tolerance (inclusive).

    Pair keys (numerator, denominator) need an equal denominator and compare numerators.
    """
    tolerance = R1B_TOLERANCE_AND_REPLICATED["tolerance"]
    missing = sorted(set(phase35_prereg.R1A_ASSERTIONS) - set(rederived))
    _prove(not missing, f"the re-derived assertions lack {missing}")
    per_key = {}
    for key, committed in phase35_prereg.R1A_ASSERTIONS.items():
        replica = rederived[key]
        if isinstance(committed, tuple):
            replica = tuple(replica)
            _prove(len(replica) == 2, f"{key} is {replica!r}, not a (numerator, denominator) pair")
            for part in replica:
                _prove_number(key, part)
            abs_diff = abs(replica[0] - committed[0])
            within = replica[1] == committed[1] and abs_diff <= tolerance[key]
            replica, committed = list(replica), list(committed)
        else:
            _prove_number(key, replica)
            abs_diff = abs(replica - committed)
            within = abs_diff <= tolerance[key]
        per_key[key] = {
            "replica": replica,
            "committed": committed,
            "abs_diff": abs_diff,
            "tolerance": tolerance[key],
            "within": within,
        }
    ok = all(row["within"] for row in per_key.values())
    return {
        "verdict": "REPLICATED" if ok else ENTRIES["not_replicated_rule"]["value"],
        "per_key": per_key,
    }


def prefix_decision(k, remeasured, committed):
    """D-07: run the erased arm iff k equals the committed k AND the address sets are equal."""
    remeasured = [tuple(a) for a in remeasured]
    committed = [tuple(a) for a in committed]
    committed_k = phase35_prereg.R1A_ASSERTIONS["k"]
    _prove(
        len(committed) == committed_k,
        f"the committed prefix has {len(committed)} addresses, R1a asserts k = {committed_k}",
    )
    k_equal = k == committed_k
    set_equal = set(remeasured) == set(committed)
    positions_moved = None
    if k_equal:
        positions_moved = sum(a != b for a, b in zip(remeasured, committed, strict=False))
        positions_moved += abs(len(remeasured) - len(committed))
    return {
        "k": k,
        "committed_k": committed_k,
        "k_equal": k_equal,
        "set_equal": set_equal,
        "only_in_remeasured": [list(a) for a in sorted(set(remeasured) - set(committed))],
        "only_in_committed": [list(a) for a in sorted(set(committed) - set(remeasured))],
        "positions_moved": positions_moved,
        "run_arm": k_equal and set_equal,
    }


_DRAW_IDENTITY_KEYS = ("family", "fact_id", "slot", "tier", "seed_index")


def draw_identity(replica_draws, committed_draws):
    """D-03: how many draws differ from the committed arm. Description, never a criterion.

    Entries are compared position by position. An entry missing on either side, with another
    identity or another completion count differs whole: all its committed completions count.
    """
    differing_entries = differing_completions = 0
    for i in range(max(len(replica_draws), len(committed_draws))):
        replica = replica_draws[i] if i < len(replica_draws) else None
        committed = committed_draws[i] if i < len(committed_draws) else None
        committed_completions = committed.get("completions", []) if committed else []
        if (
            replica is None
            or committed is None
            or any(replica.get(key) != committed.get(key) for key in _DRAW_IDENTITY_KEYS)
            or len(replica.get("completions", [])) != len(committed_completions)
        ):
            differing_entries += 1
            differing_completions += len(committed_completions)
            continue
        changed = sum(
            a != b for a, b in zip(replica["completions"], committed_completions, strict=True)
        )
        differing_completions += changed
        differing_entries += bool(changed)
    return {
        "bit_identical": differing_entries == 0,
        "differing_completions": differing_completions,
        "n_completions": sum(len(d.get("completions", [])) for d in committed_draws),
        "differing_entries": differing_entries,
        "n_entries": len(committed_draws),
        "criterion": False,
    }


def nontarget_context(replica_by_slot, committed_by_slot):
    """D-12: per non-target slot, both pooled deltas and their distance, beside the floor."""
    _prove(
        set(replica_by_slot) == set(committed_by_slot),
        f"slot sets differ: {sorted(set(replica_by_slot) ^ set(committed_by_slot))}",
    )
    return {
        "criterion": False,
        "noise_floor": NONTARGET_FLOOR,
        "slots": {
            slot: {
                "replica_delta": replica_by_slot[slot],
                "committed_delta": committed_by_slot[slot],
                "abs_diff": abs(replica_by_slot[slot] - committed_by_slot[slot]),
                "noise_floor": NONTARGET_FLOOR,
            }
            for slot in committed_by_slot
        },
    }
