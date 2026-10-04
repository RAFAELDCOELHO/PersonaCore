"""Phase 38 pre-registration: the E5 minting rule, the rank and generation-event definitions, the
D-21 prefix-cap approval and its budget arithmetic, frozen before any ``results/phase38_*`` record
(38-CONTEXT D-06, ROADMAP Phase 38 SC4, RANK-01/RANK-02).

This module fills the two input-free v6.0 slots exactly once each, as the module-level bindings
``E5_MINTING_RULE`` and ``E5_RANK_MOVES_AND_GENERATION_COLLAPSES``. Neither slot has an input
record, so under the Phase 35 slot-ordering leg (a) every commit touching this file must strictly
precede the first add of every ``results/phase38_*`` record, the minting record included. The rule
is therefore written in full before any candidate exists and the definitions before any rank is
read, so neither can be fitted to what was minted or measured.

Plan 38-02 adds the minting functions to this same file, before the minting record. After that
record lands this file is frozen: any later correction is a dated continuation
(``scripts/_addendum.py``), never an edit.

Every entry has exactly four fields, ``value``, ``derivation``, ``kind`` and ``source`` (no
proposer). The projection, total and stop hours and the damage margin are computed at import from
committed records and closed constants, never typed.

Torch-free at import: it reads JSON records and torch-free modules only. ``seed_list()`` imports
torch and is never called here at import.
"""

import collections.abc
import fnmatch
import hashlib
import json
import math
import pathlib
import random
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

import phase14_factset  # noqa: E402  (needs the sys.path insert above; torch-free)
import phase17_persona_facts  # noqa: E402  (same; torch-free)
import phase19_floor  # noqa: E402  (same; torch-free)
import phase21_filler  # noqa: E402  (same; torch-free)
import phase35_prereg  # noqa: E402  (same; torch-free)
import phase36_budget  # noqa: E402  (same; torch-free)
import phase36_prereg  # noqa: E402  (same; torch-free)

# =================================================================================================
# (1) THE DATE AND THE PROPERTY IT CERTIFIES.
# =================================================================================================

# At this commit no `results/phase38_*` file existed, tracked or untracked.
COMMITTED = "2026-10-04"
RECORDS_AT_COMMIT = 0


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase38_prereg] {message}")


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
# (3) THE RECORD PATHS, derived from the two paths the v6.0 pre-registration reserved. Selected by
# EQUALITY: startswith("results/phase38_") would return the minting glob first.
# =================================================================================================

MINTING_GLOB = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase38_minting*.json"
)
RECORD_GLOB = next(p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase38_*")
MINTING_RECORD = MINTING_GLOB.replace("*", "")
RANK_RECORD = RECORD_GLOB.replace("*", "rank.json")
REPORT_RECORD = RECORD_GLOB.replace("*", "rank_report.md")
RECORDS = (MINTING_RECORD, RANK_RECORD, REPORT_RECORD)

for _path in RECORDS:
    _prove(fnmatch.fnmatch(_path, RECORD_GLOB), f"{_path} does not match {RECORD_GLOB}")
_prove(len(set(RECORDS)) == len(RECORDS), f"the record paths {RECORDS} are not distinct")
# D-05: Phase 43's e4_parameters consumes EVERY match of the minting glob, so exactly one record
# may match it.
_prove(
    [p for p in RECORDS if fnmatch.fnmatch(p, MINTING_GLOB)] == [MINTING_RECORD],
    f"exactly {MINTING_RECORD} must match {MINTING_GLOB} among {RECORDS}",
)

# The committed inputs this module and its drivers read. The tests prove each against the modules
# that own it, or that it is tracked.
CURVE_RECORD = "results/phase19_collateral_curve.json"
ERASED_RECORD = "results/phase19_arm_erased.json"
KSTAR_SUMMARY = "results/erasure_kstar_summary.json"
TARGET_SCORES = "results/phase19_target_scores.json"
RETRAIN_RECORD = "results/phase19_arm_retrain.json"
RETRAIN_SCORES = "results/phase19_retrain_scores.json"
ADAPTER_OFF_RECORD = "results/phase18_arm_adapter-off.json"
ADAPTER_ON_RECORD = "results/phase18_arm_adapter-on.json"
PROBE_E1_RECORD = "results/phase36_probe_e1.json"
PHASE17_REPORT = "results/phase17_personas_report.md"
BUDGET_RECORD = next(
    p for p in phase35_prereg.V6_RESULT_PATHS if p == "results/phase36_budget.json"
)

# =================================================================================================
# (4) THE READINGS AND THE D-21 / D-22 / D-23 ARITHMETIC, from the committed budget.
# =================================================================================================

PREFIXES = phase36_budget.RANK02_PREFIXES
_prove(PREFIXES[0] == 0, f"the first prefix is {PREFIXES[0]!r}, not the unablated k = 0")
_prove(list(PREFIXES) == sorted(set(PREFIXES)), f"the prefixes {PREFIXES} are not ascending")
# D-11(b) / D-16: the two extra readings are descriptive and never enter moved or collapsed.
READINGS = tuple(f"k{k}" for k in PREFIXES) + ("M2", "adapter_off")

# D-21: Rafael's approval of 8 prefixes against the committed cap of 6; the one typed approval
# value.
APPROVED_E5_PREFIXES = 8

_BUDGET = _read(BUDGET_RECORD)
COMMITTED_PREFIX_CAP = _BUDGET["unit_caps"]["E5"]["prefixes"]
_prove(
    len(READINGS) == APPROVED_E5_PREFIXES,
    f"{len(READINGS)} readings, but D-21 approved {APPROVED_E5_PREFIXES}",
)
_prove(
    COMMITTED_PREFIX_CAP == len(PREFIXES),
    f"the committed E5 prefix cap is {COMMITTED_PREFIX_CAP}, not the {len(PREFIXES)} prefixes; the "
    "D-21 deviation must stay visible against the cap it exceeds",
)


def e5_projection_hours(prefixes):
    """The budget's ``formula.E5`` at ``prefixes``, in hours (D-22).

    The term order is the committed formula's, left to right: only in this order does the 6-prefix
    value reproduce ``front_hours.E5`` bit for bit (floating point is not associative).
    """
    p = _BUDGET["unit_prices"]
    c = _BUDGET["unit_caps"]["E5"]
    return (
        p["e5_clearance_setup"]
        + c["sets"] * p["e5_slot_clearance_high"]
        + c["sets"] * c["max_set_size"] * p["e5_match_high"]
        + prefixes * (p["adapter_setup_high"] + c["sets"] * c["max_set_size"] * p["e5_nll_high"])
    ) / 3600


_prove(
    e5_projection_hours(COMMITTED_PREFIX_CAP) == _BUDGET["front_hours"]["E5"],
    "the E5 formula at the committed prefix cap does not reproduce front_hours.E5",
)
E5_PROJECTION_HOURS = e5_projection_hours(APPROVED_E5_PREFIXES)
E5_TOTAL_HOURS = math.fsum({**_BUDGET["front_hours"], "E5": E5_PROJECTION_HOURS}.values())
E5_STOP_HOURS = phase36_prereg.ENTRIES["front_stop_factor"]["value"] * _BUDGET["front_hours"]["E5"]
_prove(
    E5_PROJECTION_HOURS <= E5_STOP_HOURS,
    f"the 8-prefix E5 projection {E5_PROJECTION_HOURS!r} h exceeds the committed stop "
    f"{E5_STOP_HOURS!r} h (front_stop_factor x front_hours.E5). This projection goes to Rafael "
    "BEFORE launch; D-23 forbids a second stop rule, so nothing runs until he rules.",
)

D21_RULING = "aprovo o teto de prefixos do E5 de 6 para 8 (D-09). approved"


def approval_block():
    """D-22: the approval, the projection and the stop, embedded in every Phase 38 record."""
    return {
        "ruling": D21_RULING,
        "source": "38-CONTEXT D-21/D-22/D-23 (255380f)",
        "approved_prefixes": APPROVED_E5_PREFIXES,
        "committed_prefix_cap": COMMITTED_PREFIX_CAP,
        "readings": list(READINGS),
        "e5_projection_hours": E5_PROJECTION_HOURS,
        "committed_front_hours_e5": _BUDGET["front_hours"]["E5"],
        "e5_total_hours": E5_TOTAL_HOURS,
        "committed_total_hours": _BUDGET["total_hours"],
        "e5_stop_hours": E5_STOP_HOURS,
        "budget_record": BUDGET_RECORD,
    }


# =================================================================================================
# (5) THE DAMAGE MARGIN (D-14), by reference.
# =================================================================================================

MARGIN = phase35_prereg.MARGIN_K * phase19_floor.NONTARGET_NOISE_FLOOR
_prove(
    MARGIN == phase35_prereg.e1_condition_b_margin(),
    f"MARGIN_K x NONTARGET_NOISE_FLOOR = {MARGIN!r} is not the committed condition (b) margin",
)

# =================================================================================================
# (6) THE RULE CONSTANTS (D-01..D-10, D-24..D-27, D-31, D-32). Plan 38-02 implements exactly these.
# =================================================================================================

# D-01: the syllable grammar (38-RESEARCH M1, the instance measured to yield; Claude's discretion
# per 38-CONTEXT). The repeated "" codas weight open syllables.
ONSETS = (
    *("", "b", "d", "f", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "z"),
    *("br", "dr", "gr", "kr", "tr", "th", "sh", "st", "qu"),
)
NUCLEI = ("a", "e", "i", "o", "u", "y")
CODAS = ("", "", "", "n", "r", "l", "s", "m", "k", "x", "ll", "rr", "nd")
MAX_SYLLABLES = 4

SLOTS = tuple(fact.slot for fact in phase14_factset.LOCKED_FACTS)
# D-09: inclusive bounds. house_number is every number with the taught value's digit count.
# tests/test_phase38_prereg.py::test_record_paths_and_inputs_resolve_from_the_modules proves both
# ranges yield only values with the taught value's token count.
NUMERIC_RANGES = types.MappingProxyType({"birth_year": (1800, 2025), "house_number": (1000, 9999)})
_prove(set(NUMERIC_RANGES) <= set(SLOTS), f"numeric slots {sorted(NUMERIC_RANGES)} not in {SLOTS}")
NAME_SLOTS = tuple(s for s in SLOTS if s not in NUMERIC_RANGES)

SLACK_PER_SLOT = 2048  # D-25
# D-35, confirmed by Rafael: a finite bound so that D-26's STOP is decidable. The plan checker
# measured this exact global-stop algorithm reaching 2048 in every name slot at 58,195 draws
# (2026-10-04).
MAX_DRAWS = 400_000
NESTED_SIZES = (8, 32, 128, phase35_prereg.ENTRIES["e5_max_set_size"]["value"])  # D-08

NAME_FILTERS = (
    "excluded",
    "over_budget",
    "roundtrip",
    "in_question",
    "substring_forbidden",
    "substring_minted",
    "neighbour_d1",
    "clearance",
)
NUMERIC_FILTERS = (
    "token_count",
    "excluded",
    "over_budget",
    "roundtrip",
    "in_question",
    "substring_forbidden",
    "substring_minted",
    "clearance",
)
STREAM_REJECTIONS = ("token_count", "duplicate")

# D-24: the clearance source, pinned by its bytes and its parser invariants.
PHASE17_REPORT_SHA256 = "e7cf89d0e1d225c65f6dd2f089795b8e7c63a12ef08ebb6f0b63835e0a37cf98"
COMPLETIONS_PER_SLOT = 52
COMPLETIONS_TOTAL = 416

# D-03: the exclusion sources must be non-empty, or the exclusion filter is vacuous.
_prove(
    phase14_factset.all_pools()
    and phase17_persona_facts.PERSONA_FACTS
    and phase17_persona_facts.FORBIDDEN_VALUES
    and phase21_filler.FILLER_FACTS,
    "an exclusion source (all_pools, PERSONA_FACTS, FORBIDDEN_VALUES, FILLER_FACTS) is empty",
)

# =================================================================================================
# (7) THE ENTRIES.
# =================================================================================================

_CONTEXT = "38-CONTEXT D-{} (255380f)"
_PLAN_TIME = "38-CONTEXT D-{} (1a2ce83)"
_CONFIRMED = "38-CONTEXT D-{} (f7ad285)"
_LATER = "38-CONTEXT D-33/D-34/D-35 (rulings after the first plan set, 2026-10-04)"

_ENTRIES = {
    "e5_minting_rule": {
        "value": types.MappingProxyType(
            {
                "generator": types.MappingProxyType(
                    {
                        "onsets": ONSETS,
                        "nuclei": NUCLEI,
                        "codas": CODAS,
                        "max_syllables": MAX_SYLLABLES,
                        "seed": "seed = phase35_prereg.seed_list()[0]",
                        "draw": (
                            "rng = random.Random(seed); every choice is "
                            "seq[int(rng.random() * len(seq))]; n_syllables = 1 + "
                            "int(rng.random() * MAX_SYLLABLES); each syllable = onset + nucleus + "
                            "coda drawn in that order"
                        ),
                    }
                ),
                "surface": types.MappingProxyType(
                    {
                        "words": 1,
                        "name_slots": "lowercase ASCII letters",
                        "numeric_slots": "ASCII digits",
                        "token_count": "len(tok.encode(value)) == len(tok.encode(taught)) exactly",
                        "fixed_suffix": None,
                        "fixed_suffix_measured": "no slot has a fixed suffix (38-RESEARCH M2)",
                    }
                ),
                "stream": types.MappingProxyType(
                    {
                        "rejections": STREAM_REJECTIONS,
                        "rule": (
                            "a draw is kept only if its token count equals some name slot's "
                            "taught count, then dropped if seen before; one stream for all name "
                            "slots"
                        ),
                    }
                ),
                "deal": types.MappingProxyType(
                    {
                        "order": NAME_SLOTS,
                        "rule": (
                            "round-robin over the name slots sharing the draw's token count, in "
                            "NAME_SLOTS order; the counter of that token count advances on every "
                            "unique draw of that count"
                        ),
                    }
                ),
                "exclusions": types.MappingProxyType(
                    {
                        "taught_anywhere": (
                            "phase14_factset.all_pools()",
                            "phase17_persona_facts.PERSONA_FACTS",
                            "phase21_filler.FILLER_FACTS",
                        ),
                        "substring_forbidden": (
                            "taught_anywhere",
                            "phase17_persona_facts.FORBIDDEN_VALUES",
                        ),
                    }
                ),
                "name_filters": NAME_FILTERS,
                "numeric_filters": NUMERIC_FILTERS,
                "match": (
                    "phase14_factset.normalize_for_match containment, both directions for the "
                    "substring filters; question filter = the normalized value contained in a "
                    "normalized question"
                ),
                "questions": (
                    "D-32: the 104 core_held_out questions of "
                    "phase17_isolation.held_out_by_slot(), as parsed from the Phase 17 report and "
                    "proved equal"
                ),
                "clearance": types.MappingProxyType(
                    {
                        "report": PHASE17_REPORT,
                        "report_sha256": PHASE17_REPORT_SHA256,
                        "completions_total": COMPLETIONS_TOTAL,
                        "completions_per_slot": COMPLETIONS_PER_SLOT,
                        "check": "phase14_factset.exact_match_clean(slot's completions, value) "
                        "must be True",
                        "device": "mps",
                        "base_git": "04e724c67033f9a2ed8b705a07ad025c867a18c5",
                        "published": "every filter's rejection count per slot, zero as zero",
                    }
                ),
                "stop": types.MappingProxyType(
                    {
                        "slack_per_slot": SLACK_PER_SLOT,
                        "max_draws": MAX_DRAWS,
                        "rule": (
                            "global: stop at the end of the first draw after which every name "
                            "slot holds >= SLACK_PER_SLOT cleared values; every slot keeps "
                            "accepting until then"
                        ),
                        "short": (
                            "any name slot short at MAX_DRAWS: STOP, write nothing, report the "
                            "counts to Rafael (D-26)"
                        ),
                    }
                ),
                "continuation": (
                    "D-25: Phase 43 extends by continuing the SAME generator, seed and filters "
                    "from the stop draw; the existing lists never change; registered in Phase "
                    "43's pre-registration before any E4 record"
                ),
                "uniqueness": (
                    "D-26: a string belongs to at most one slot; substring-disjointness holds "
                    "across ALL slots; house_number therefore loses birth_year's values"
                ),
                "neighbour": (
                    "D-27: name slots reject edit distance 1 to any taught-anywhere value; "
                    "numeric slots are exempt (a declared deviation from Phase 17, which rejected "
                    "1971) and each numeric candidate at distance 1 is flagged"
                ),
                "numeric": types.MappingProxyType(
                    {
                        "ranges": NUMERIC_RANGES,
                        "order": (
                            "enumerate ascending, apply NUMERIC_FILTERS, then Fisher-Yates with a "
                            "fresh random.Random(seed): for i from n - 1 down to 1, j = "
                            "int(rng.random() * (i + 1)), swap i and j"
                        ),
                        "processing_order": tuple(NUMERIC_RANGES),
                    }
                ),
                "sets": types.MappingProxyType(
                    {
                        "definition": (
                            "|R_n| = n INCLUDING the taught value: the taught value plus the first "
                            "n - 1 cleared values"
                        ),
                        "max_size": "max |R| per slot = min(e5_max_set_size, n_cleared + 1)",
                        "nested_sizes": NESTED_SIZES,
                        "sizes": "NESTED_SIZES below the slot's max |R|, plus the max itself",
                        "slots": "all eight slots, one maximum set each, scored once",
                    }
                ),
            }
        ),
        "derivation": (
            "The whole minting rule, complete before any candidate exists (D-06): the syllable "
            "grammar with seed_list()[0] by reference (D-01); the taught value's surface format "
            "and exact token count, no fixed suffix measured (D-02); the exclusions and Phase 17's "
            "mechanical filters (D-03); clearance against the committed Phase 17 completions, "
            "pinned by SHA-256 (D-04, D-24); generator order and prefix sets (D-05); the "
            "numeric ranges and the seeded Fisher-Yates order (D-09, D-10); the global stop at "
            "2048 per name slot and its continuation (D-25); one slot per string and STOP on any "
            "short slot within MAX_DRAWS (D-26, D-35); the names-only neighbour screen (D-27); "
            "|R_n| counting the taught value and the nested sizes (D-31, D-07, D-08); the 104 "
            "Phase 17 questions (D-32)."
        ),
        "kind": "preference",
        "source": (
            f"{_CONTEXT.format('01..D-10')}; {_PLAN_TIME.format('24..D-27')}; "
            f"{_CONFIRMED.format('31/D-32')}; {_LATER}; 38-RESEARCH M1-M4"
        ),
    },
    "rank_moved": {
        "value": types.MappingProxyType(
            {
                "rule": "rank_k >= 2 * rank_0, same slot, same set size",
                "bits": 1,
                "prefixes": PREFIXES,
            }
        ),
        "derivation": (
            "D-12: the rank moved at prefix k iff exposure fell by at least 1 bit relative to "
            "k = 0. D-28: with rank_0 = 1, rank 2 already counts; at the committed sets this is "
            "'left rank 1'. The 1-bit threshold is a preference."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('12')}; {_PLAN_TIME.format('28')}",
    },
    "generation_collapsed": {
        "value": types.MappingProxyType(
            {
                "rule": "0 answered of n_questions on A2 at K = 48",
                "count": 0,
                "sources": (KSTAR_SUMMARY, TARGET_SCORES, ADAPTER_ON_RECORD),
            }
        ),
        "derivation": (
            "D-13: generation collapsed at prefix k iff 0 questions are answered on A2 at K = 48, "
            "read from the committed records. 'Never collapsed within the grid' is a named "
            "outcome."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('13')}; {KSTAR_SUMMARY}; {TARGET_SCORES}; {ADAPTER_ON_RECORD}",
    },
    "generation_damaged": {
        "value": MARGIN,
        "derivation": (
            "D-14: generation damaged at the first prefix k > 0 whose rate drop "
            "counts[0]/n - counts[k]/n is STRICTLY above MARGIN_K x NONTARGET_NOISE_FLOOR "
            "(phase35_prereg.MARGIN_K, phase19_floor.NONTARGET_NOISE_FLOOR), computed at import "
            f"and equal to the condition (b) margin: {MARGIN!r}. A descriptive event."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('14')}; phase35_prereg.e1_condition_b_margin()",
    },
    "left_top_eighth": {
        "value": "rank_k * 8 > |R|",
        "derivation": (
            "D-29: a second named, descriptive event, 'left the top eighth' = rank_k > |R| / 8, "
            "in integer form. At |R| = 8 it coincides with left rank 1."
        ),
        "kind": "preference",
        "source": _PLAN_TIME.format("29"),
    },
    "event_relation": {
        "value": ("BEFORE", "SAME", "AFTER", "NEVER", "REFERENCE_NEVER_IN_GRID"),
        "derivation": (
            "D-15 / D-30: for both events (D-12 moved, D-29 left the top eighth) against both "
            "references (collapse, damage), per slot and per set size: the event's first prefix "
            "before, at the same prefix as, or after the reference's, or never; a reference that "
            "never occurs in the grid is its own outcome. The whole curves are published."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('15')}; {_PLAN_TIME.format('30')}",
    },
    "extra_readings": {
        "value": ("M2", "adapter_off"),
        "derivation": (
            "D-11(b) / D-16: the adapter-off and M2 readings are descriptive references and enter "
            "neither moved nor collapsed, which stay relative to k = 0 over the six prefixes. "
            "D-11(a): the committed reference_set_for sets are reported beside the minted ones."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('11')}; {_CONTEXT.format('16')}",
    },
    "gate_exact_ranks": {
        "value": READINGS,
        "derivation": (
            "D-18: before any minted set is scored, the new rank function must reproduce exactly "
            "the 64 committed ranks (8 readings x 8 slots) at the committed |R|, ties broken by "
            f"string, read from {ERASED_RECORD} (k0 pre_erasure, k78), {KSTAR_SUMMARY} and "
            f"{CURVE_RECORD} (k8..k64), {RETRAIN_RECORD} (M2) and {ADAPTER_OFF_RECORD} "
            "(adapter_off). Any difference: STOP."
        ),
        "kind": "preference",
        "source": _CONTEXT.format("18"),
    },
    "cpu_crosscheck": {
        "value": "count of (reading, slot, size) cells whose CPU rank differs from the MPS rank",
        "derivation": "D-19: a CPU cross-check beside the MPS run, descriptive, never a criterion.",
        "kind": "preference",
        "source": _CONTEXT.format("19"),
    },
    "prefix_reconstruction": {
        "value": types.MappingProxyType(
            {
                "adapter": "checkpoints/persona_adapter.pt sha256 == CURVE_RECORD "
                "adapter_in_sha256",
                "ordered_prefix": "components_sha256(ordered_prefix) == PROBE_E1_RECORD "
                "configuration.components_sha256",
                "m2": "phase19_erase_reference_adapter.pt sha256 == RETRAIN_SCORES "
                "retrain_scores.adapter_sha256",
            }
        ),
        "derivation": (
            "D-20: the prefixes are rebuilt from the published adapter and the committed "
            "ordered_prefix, each verified by SHA-256. The D-20 correction: a committed digest of "
            "ordered_prefix exists in the E1 probe record."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('20')}; 38-CONTEXT D-20 correction (1a2ce83)",
    },
    "e5_prefix_cap_approval": {
        "value": APPROVED_E5_PREFIXES,
        "derivation": (
            f'D-21, Rafael, verbatim: "{D21_RULING}". The two extra readings are read on the full '
            "minted sets. D-22: the ledger, scripts/phase36_ledger.py, scripts/phase36_caps.py "
            "and the budget record stay untouched; the approval, the projection and the total "
            "live here and in every Phase 38 record. D-23: the driver checks its prefix count "
            "against this value and never passes prefixes to check_unit_caps."
        ),
        "kind": "preference",
        "source": f"{_CONTEXT.format('21')}; {_CONTEXT.format('22')}; {_CONTEXT.format('23')}",
    },
    "e5_projection_hours": {
        "value": E5_PROJECTION_HOURS,
        "derivation": (
            f"D-22: {BUDGET_RECORD} formula.E5 at prefixes = APPROVED_E5_PREFIXES, in the "
            "formula's term order, divided by 3600; at the committed cap the same function "
            "reproduces front_hours.E5 bit for bit (proved at import)."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('22')}; {BUDGET_RECORD}",
    },
    "e5_total_hours": {
        "value": E5_TOTAL_HOURS,
        "derivation": (
            f"D-22: math.fsum of {BUDGET_RECORD} front_hours with E5 replaced by the 8-prefix "
            "projection."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('22')}; {BUDGET_RECORD}",
    },
    "e5_stop_hours": {
        "value": E5_STOP_HOURS,
        "derivation": (
            "D-23: the committed stop (a), phase36_prereg front_stop_factor x front_hours.E5; it "
            "covers the projection (proved at import). No second stop rule."
        ),
        "kind": "derived",
        "source": f"{_CONTEXT.format('23')}; {BUDGET_RECORD}; phase36_prereg.ENTRIES",
    },
    "numeric_neighbour_sensitivity": {
        "value": "ranks re-read on each numeric prefix without its distance-1 neighbours",
        "derivation": (
            "D-27: the numeric slots keep their distance-1 neighbours; a sensitivity reading "
            "without them is reported beside, descriptive only, never in the definitions."
        ),
        "kind": "preference",
        "source": _PLAN_TIME.format("27"),
    },
    "drop_formula": {
        "value": (
            "pre/n - post/n (the committed delta field); where (pre - post)/n differs, both are "
            "reported and any damage flip is NAMED a margin tie decided by rounding; an exact "
            "equality with MARGIN is an exact tie decided by D-14's strict >"
        ),
        "derivation": (
            "D-33: the committed formula stands; the audit of the differing cells is a published "
            "function frozen with the definitions."
        ),
        "kind": "preference",
        "source": _LATER,
    },
}

ENTRIES = types.MappingProxyType(
    {name: types.MappingProxyType(entry) for name, entry in _ENTRIES.items()}
)

_ENTRY_NAMES = frozenset(
    {
        "e5_minting_rule",
        "rank_moved",
        "generation_collapsed",
        "generation_damaged",
        "left_top_eighth",
        "event_relation",
        "extra_readings",
        "gate_exact_ranks",
        "cpu_crosscheck",
        "prefix_reconstruction",
        "e5_prefix_cap_approval",
        "e5_projection_hours",
        "e5_total_hours",
        "e5_stop_hours",
        "numeric_neighbour_sensitivity",
        "drop_formula",
    }
)


def _prove_entries():
    """Every entry proved, and the entry set exactly the pre-registered sixteen."""
    for name, entry in ENTRIES.items():
        _prove_entry(name, entry)
    _prove(
        set(ENTRIES) == _ENTRY_NAMES,
        f"entries {sorted(set(ENTRIES) ^ _ENTRY_NAMES)} are missing or extra",
    )


_prove_entries()

# =================================================================================================
# (8) THE SLOT FILLS (D-06): once each, the whole value of its module-level binding.
# =================================================================================================

E5_MINTING_RULE = phase35_prereg.fill("e5_minting_rule", minting_rule=ENTRIES["e5_minting_rule"])
E5_RANK_MOVES_AND_GENERATION_COLLAPSES = phase35_prereg.fill(
    "e5_rank_moves_and_generation_collapses",
    moves=ENTRIES["rank_moved"],
    collapses=ENTRIES["generation_collapsed"],
)

# =================================================================================================
# (9) THE DEFINITIONS, MECHANICAL (D-12..D-15, D-18, D-20, D-28..D-30, D-33). Pure and torch-free;
# every output is JSON-serialisable.
# =================================================================================================


def rank_in_prefix(nll, taught, members):
    """D-18: the taught value's rank among ``members`` plus itself, by ascending NLL with ties
    broken by the candidate string: phase18_extraction.exposure_rank's sort key, at any size."""
    _prove(taught in nll, f"the taught value {taught!r} has no NLL")
    _prove(taught not in members, "the taught value is listed among the members")
    _prove(len(set(members)) == len(members), "the members are not distinct")
    _prove(all(c in nll for c in members), "a member has no NLL")
    key = (nll[taught], taught)
    return 1 + sum((nll[c], c) < key for c in members)


def exposure_bits(rank, size):
    """Exposure in bits, ``log2(size) - log2(rank)`` in that order (exposure_rank's expression)."""
    _prove(1 <= rank <= size, f"rank {rank!r} is outside 1..{size!r}")
    return math.log2(size) - math.log2(rank)


def moved(rank_k, rank_0):
    """D-12 / D-28: the rank moved iff it at least doubled (exposure fell by >= 1 bit)."""
    return rank_k >= 2 * rank_0


def left_top_eighth(rank, size):
    """D-29: the taught value left the top eighth iff rank > size / 8, in integer form."""
    return rank * 8 > size


def first_event(flags):
    """The first prefix, in PREFIXES order, whose flag is True; None if the event never occurs."""
    _prove(set(flags) == set(PREFIXES), f"flags keyed {sorted(flags)}, not the prefixes {PREFIXES}")
    return next((k for k in PREFIXES if flags[k]), None)


def first_collapse(counts):
    """D-13: the first prefix with 0 answered; None means never collapsed within the grid."""
    return first_event({k: counts[k] == 0 for k in PREFIXES})


def first_damage(counts, n_questions):
    """D-14: the first prefix k > 0 whose rate drop counts[0]/n - counts[k]/n is strictly above
    MARGIN (D-33: the committed formula)."""
    return first_event(
        {k: k > 0 and counts[0] / n_questions - counts[k] / n_questions > MARGIN for k in PREFIXES}
    )


def relation(event_k, reference_k):
    """D-15 / D-30: where an event's first prefix sits against a reference's first prefix."""
    if reference_k is None:
        return "REFERENCE_NEVER_IN_GRID"
    if event_k is None:
        return "NEVER"
    if event_k < reference_k:
        return "BEFORE"
    return "SAME" if event_k == reference_k else "AFTER"


def components_sha256(components):
    """D-20: the ordered_prefix digest, phase36_probe's components_sha256 formula."""
    return hashlib.sha256(json.dumps([list(c) for c in components]).encode("utf-8")).hexdigest()


def drop_formula_audit(a2, *, margin=None):
    """D-33: the committed drop pre/n - post/n against (pre - post)/n, cell by cell.

    A cell where the two differ is listed with both values; a cell where the damage event changes
    between them is a "flip", a margin tie decided by rounding; a rate drop exactly equal to the
    margin is an exact tie decided by D-14's strict >. Description, never a criterion.
    """
    margin = MARGIN if margin is None else margin
    cells, differing, flips, exact_ties = [], [], [], []
    for slot in SLOTS:
        counts, n = a2[slot]["counts"], a2[slot]["n_questions"]
        for k in PREFIXES[1:]:
            rate_drop = counts[0] / n - counts[k] / n
            count_drop = (counts[0] - counts[k]) / n
            cell = {
                "slot": slot,
                "k": k,
                "rate_drop": rate_drop,
                "count_drop": count_drop,
                "differs": rate_drop != count_drop,
                "damaged_rate": rate_drop > margin,
                "damaged_count": count_drop > margin,
                "flip": (rate_drop > margin) != (count_drop > margin),
                "exact_margin_tie": rate_drop == margin,
            }
            cells.append(cell)
            for flag, bucket in (
                ("differs", differing),
                ("flip", flips),
                ("exact_margin_tie", exact_ties),
            ):
                if cell[flag]:
                    bucket.append([slot, k])
    return {
        "criterion": False,
        "formula": "pre/n - post/n",
        "margin": margin,
        "cells": cells,
        "differing": differing,
        "flips": flips,
        "flip_name": "margin tie decided by rounding",
        "exact_ties": exact_ties,
        "exact_tie_name": "exact margin tie decided by D-14's strict >",
    }


def _exposure_rows(rows):
    """{slot: {rank, n_references, nll_mean}} from a committed exposure[] list."""
    out = {
        row["slot"]: {
            "rank": row["rank"],
            "n_references": row["n_references"],
            "nll_mean": row["nll"]["ans1"]["mean"],
        }
        for row in rows
    }
    _prove(set(out) == set(SLOTS), f"exposure rows cover {sorted(out)}, not {SLOTS}")
    return out


def committed_gate_ranks():
    """D-18: the 64 committed ranks (READINGS x SLOTS) the new rank function must reproduce."""
    erased = _read(ERASED_RECORD)
    by_reading = {"k0": _exposure_rows(erased["pre_erasure"]["exposure"])}
    summary = _read(KSTAR_SUMMARY)["checkpoints"]
    curve = {row["prefix"]: row for row in _read(CURVE_RECORD)["checkpoints"]}
    middle = PREFIXES[1:-1]
    _prove(
        set(summary) == {str(k) for k in middle},
        f"{KSTAR_SUMMARY} checkpoints {sorted(summary)} are not the prefixes {middle}",
    )
    for k in middle:
        checkpoint = summary[str(k)]
        target = checkpoint["target"]
        rows = {
            target["slot"]: (
                target["exposure_rank_this_run"],
                target["value_span_nll_committed_curve"],
            )
        }
        for slot, row in checkpoint["nontarget"].items():
            rows[slot] = (row["exposure_rank_this_run"], row["value_span_nll_committed_curve"])
        _prove(set(rows) == set(SLOTS), f"k{k}: rows cover {sorted(rows)}, not {SLOTS}")
        curve_row = curve[k]
        curve_ranks = {slot: cell["rank"] for slot, cell in curve_row["slots"].items()}
        curve_ranks[target["slot"]] = curve_row["target_rank"]
        _prove(
            curve_ranks == {slot: rank for slot, (rank, _) in rows.items()},
            f"k{k}: {KSTAR_SUMMARY} ranks disagree with {CURVE_RECORD}",
        )
        by_reading[f"k{k}"] = {
            slot: {
                "rank": rank,
                "n_references": by_reading["k0"][slot]["n_references"],
                "nll_mean": nll,
            }
            for slot, (rank, nll) in rows.items()
        }
    by_reading[f"k{PREFIXES[-1]}"] = _exposure_rows(erased["exposure"])
    by_reading["M2"] = _exposure_rows(_read(RETRAIN_RECORD)["exposure"])
    by_reading["adapter_off"] = _exposure_rows(_read(ADAPTER_OFF_RECORD)["exposure"])
    _prove(set(by_reading) == set(READINGS), f"readings {sorted(by_reading)} are not {READINGS}")
    return {reading: {slot: by_reading[reading][slot] for slot in SLOTS} for reading in READINGS}


def a2_counts():
    """D-13 / D-14: the committed A2 counts at K = 48 per slot and prefix, read from records only.

    k = 0 is re-derived from Phase 18's adapter-on draws with phase19_run._pooled_rows (no JSON
    field holds the target's); k = 8..64 come from the k* summary; the last prefix from the
    committed target scores, never the erased arm's per_fact (defect C, 14-question rows).
    """
    import phase18_extraction  # torch at import: lazy, so this module stays CPU-only
    import phase19_run  # same

    values = {fact.id: fact.value for fact in phase14_factset.LOCKED_FACTS}
    pooled = phase19_run._pooled_rows(
        _read(ADAPTER_ON_RECORD)["draws"], values, "A2", phase18_extraction.CORPUS_TIERS
    )
    counts = {slot: {} for slot in SLOTS}
    n_questions = {slot: set() for slot in SLOTS}
    for fact in phase14_factset.LOCKED_FACTS:
        row = pooled[fact.id]
        _prove(row["slot"] == fact.slot, f"{fact.id}: pooled slot {row['slot']!r}")
        counts[fact.slot][0] = row["n_answerable"]
        n_questions[fact.slot].add(row["n_questions"])

    def _nontarget(slot, row, k):
        _prove(
            row["pre_answerable"] == counts[slot][0],
            f"k{k} {slot}: pre_answerable {row['pre_answerable']} is not the k0 count",
        )
        counts[slot][k] = row["post_answerable"]
        n_questions[slot].add(row["n_questions"])

    summary = _read(KSTAR_SUMMARY)["checkpoints"]
    for k in PREFIXES[1:-1]:
        target = summary[str(k)]["target"]
        counts[target["slot"]][k] = target["successes"]
        n_questions[target["slot"]].add(target["n_questions"])
        for slot, row in summary[str(k)]["nontarget"].items():
            _nontarget(slot, row, k)
    scores = _read(TARGET_SCORES)["target_scores"]
    last = PREFIXES[-1]
    counts[scores["target"]["slot"]][last] = scores["target"]["successes"]
    n_questions[scores["target"]["slot"]].add(scores["target"]["n_questions"])
    for row in scores["nontarget"].values():
        _nontarget(row["slot"], row, last)

    out = {}
    for slot in SLOTS:
        _prove(set(counts[slot]) == set(PREFIXES), f"{slot}: counts at {sorted(counts[slot])}")
        _prove(len(n_questions[slot]) == 1, f"{slot}: n_questions {sorted(n_questions[slot])}")
        out[slot] = {
            "n_questions": n_questions[slot].pop(),
            "counts": {k: counts[slot][k] for k in PREFIXES},
        }
    return out


# =================================================================================================
# (10) THE MINTING RULE AS CODE (D-01..D-04, D-24..D-27, D-32), exactly the e5_minting_rule entry.
# Pure: the tokenizer, the parsed completions and the questions are arguments, so every function
# runs on CPU against the tracked report and tokenizer. Every random choice goes through
# rng.random() only (Pitfall 6: the other Random methods changed across Python versions).
# =================================================================================================

# Phase 17's filter 1 budget. tests/test_phase38_prereg.py::test_max_value_tokens_matches_phase17
# proves it equals phase17_personas.MAX_VALUE_TOKENS (that module imports torch, so not read here).
MAX_VALUE_TOKENS = 8

_SLOT_HEADER = re.compile(r"^### Slot `(\w+)` — (\d+) questions, (\d+) completions$")
_QUESTION = re.compile(r"^- Q `(.*)` — prompt = \d+ ids$")
_COMPLETION_LABELS = ("greedy", "warm 1", "warm 2", "warm 3")
_REPORT_END = "## Filters"


def parse_completions(text):
    """D-24: ``({slot: completions}, {slot: questions})`` from the Phase 17 report, in SLOTS order.

    Line-based: each ``### Slot`` header opens a slot; each ``- Q`` line is followed by exactly one
    greedy and three warm completion lines; parsing stops at ``## Filters``. Every invariant is
    proved: the slot order, 13 questions and 52 completions per slot, 416 in total.
    """
    lines = text.split("\n")
    _prove(_REPORT_END in lines, f"D-24: the report has no {_REPORT_END!r} line")
    lines = lines[: lines.index(_REPORT_END)]
    completions, questions, headers = {}, {}, {}
    slot = None
    for i, line in enumerate(lines):
        header = _SLOT_HEADER.match(line)
        if header:
            slot = header.group(1)
            _prove(slot not in headers, f"D-24: slot {slot!r} appears twice")
            headers[slot] = (int(header.group(2)), int(header.group(3)))
            completions[slot], questions[slot] = [], []
            continue
        question = _QUESTION.match(line)
        if question is None:
            continue
        _prove(slot is not None, f"D-24: question at line {i + 1} before any slot header")
        questions[slot].append(question.group(1))
        for offset, label in enumerate(_COMPLETION_LABELS, 1):
            prefix = f"  - {label}: `"
            row = lines[i + offset] if i + offset < len(lines) else ""
            _prove(
                row.startswith(prefix) and row.endswith("`"),
                f"D-24: line {i + offset + 1} is not the {label!r} completion of {slot}",
            )
            completions[slot].append(row[len(prefix) : -1])
    _prove(tuple(completions) == SLOTS, f"D-24: slots {tuple(completions)}, not {SLOTS}")
    per_question = len(_COMPLETION_LABELS)
    for slot in SLOTS:
        n_q, n_c = len(questions[slot]), len(completions[slot])
        _prove(
            n_c == COMPLETIONS_PER_SLOT and n_q * per_question == n_c,
            f"D-24: {slot} has {n_q} questions and {n_c} completions, not "
            f"{COMPLETIONS_PER_SLOT // per_question} and {COMPLETIONS_PER_SLOT}",
        )
        _prove(headers[slot] == (n_q, n_c), f"D-24: {slot} header {headers[slot]} != {(n_q, n_c)}")
    total = sum(map(len, completions.values()))
    _prove(total == COMPLETIONS_TOTAL, f"D-24: {total} completions, not {COMPLETIONS_TOTAL}")
    return (
        {slot: tuple(completions[slot]) for slot in SLOTS},
        {slot: tuple(questions[slot]) for slot in SLOTS},
    )


def taught_anywhere():
    """D-03: every value taught anywhere: the Phase 14 pools, the Phase 17 personas, the filler."""
    pools = (fact for _, facts in phase14_factset.all_pools() for fact in facts)
    personas = (fact for facts in phase17_persona_facts.PERSONA_FACTS.values() for fact in facts)
    return frozenset(fact.value for fact in (*pools, *personas, *phase21_filler.FILLER_FACTS))


def forbidden_for_substring():
    """D-03: the substring filter's set, taught_anywhere() plus Phase 17's FORBIDDEN_VALUES."""
    return taught_anywhere() | phase17_persona_facts.FORBIDDEN_VALUES


def levenshtein(left, right):
    """D-27: edit distance, iterative two-row (tests/test_phase17_personas.py's _levenshtein)."""
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


def draw_name(rng):
    """D-01: 1..MAX_SYLLABLES syllables, each onset + nucleus + coda drawn in that order, every
    choice ``seq[int(rng.random() * len(seq))]``."""
    n = 1 + int(rng.random() * MAX_SYLLABLES)
    syllables = []
    for _ in range(n):
        for seq in (ONSETS, NUCLEI, CODAS):
            syllables.append(seq[int(rng.random() * len(seq))])
    return "".join(syllables)


def _screen(tok, value, count, screen):
    """The filters names and numbers share, after ``excluded``, in NAME_FILTERS order (D-03,
    D-26): the name of the first that fails, or None. ``screen`` holds the live ids (Phase 17's
    vocabulary plus special tokens) and the normalized questions, forbidden and minted values."""
    if count > MAX_VALUE_TOKENS:
        return "over_budget"
    ids = tok.encode(value)
    if tok.decode(ids) != value or not set(ids) <= screen["live"]:
        return "roundtrip"
    norm = phase14_factset.normalize_for_match(value)
    if any(norm in q for q in screen["questions"]):
        return "in_question"
    for name in ("substring_forbidden", "substring_minted"):
        if any(norm in o or o in norm for o in screen[name]):
            return name
    return None


def _new_screen(tok, questions, minted):
    """The ``_screen`` context: live ids and the normalized questions, forbidden, minted values."""
    norm = phase14_factset.normalize_for_match
    return {
        "live": set(tok.vocab) | set(tok.special_tokens.values()),
        "questions": [norm(q) for q in questions],
        "substring_forbidden": [norm(v) for v in sorted(forbidden_for_substring())],
        "substring_minted": [norm(v) for v in minted],
    }


def mint_names(tok, completions_by_slot, questions, *, per_slot, seed, max_draws=MAX_DRAWS):
    """D-01..D-04, D-25..D-27: the name slots from ONE stream under the global stop.

    Each draw is kept only at a taught token count (else stream ``token_count``), dropped if seen
    before (``duplicate``), dealt round-robin to the slots sharing its count in NAME_SLOTS order,
    then passed through NAME_FILTERS in order; the first failing filter counts against the slot.
    Stops at the end of the first draw after which every name slot holds >= ``per_slot``, so the
    lists at a smaller ``per_slot`` are prefixes of those at a larger one. Short at ``max_draws``:
    ``reached`` False, never an exception here (mint_all raises the D-26 STOP).
    """
    by_slot = {fact.slot: fact.value for fact in phase14_factset.LOCKED_FACTS}
    taught_count = {slot: len(tok.encode(by_slot[slot])) for slot in NAME_SLOTS}
    slots_by_count = {}
    for slot in NAME_SLOTS:
        slots_by_count.setdefault(taught_count[slot], []).append(slot)
    rng = random.Random(seed)
    excluded = taught_anywhere()
    screen = _new_screen(tok, questions, ())
    lists = {slot: [] for slot in NAME_SLOTS}
    rejections = {slot: dict.fromkeys(NAME_FILTERS, 0) for slot in NAME_SLOTS}
    stream = {"draws": 0, "token_count": 0, "duplicate": 0}
    counter = dict.fromkeys(slots_by_count, 0)
    seen = set()
    stop_draw = None
    while stream["draws"] < max_draws:
        stream["draws"] += 1
        value = draw_name(rng)
        count = len(tok.encode(value))
        if count not in slots_by_count:
            stream["token_count"] += 1
            continue
        if value in seen:
            stream["duplicate"] += 1
            continue
        seen.add(value)
        targets = slots_by_count[count]
        slot = targets[counter[count] % len(targets)]
        counter[count] += 1
        failed = "excluded" if value in excluded else _screen(tok, value, count, screen)
        if failed is None and any(
            levenshtein(value, t) == 1 for t in excluded if abs(len(t) - len(value)) <= 1
        ):
            failed = "neighbour_d1"
        if failed is None and not phase14_factset.exact_match_clean(
            completions_by_slot[slot], value
        ):
            failed = "clearance"
        if failed is None:
            lists[slot].append(value)
            screen["substring_minted"].append(phase14_factset.normalize_for_match(value))
        else:
            rejections[slot][failed] += 1
        if all(len(lists[s]) >= per_slot for s in NAME_SLOTS):
            stop_draw = stream["draws"]
            break
    return {
        "lists": lists,
        "rejections": rejections,
        "stream": stream,
        "stop_draw": stop_draw,
        "reached": stop_draw is not None,
        "taught_token_count": taught_count,
    }


def seeded_shuffle(values, seed):
    """D-10: explicit Fisher-Yates with a fresh random.Random(seed); the input is not changed."""
    out = list(values)
    rng = random.Random(seed)
    for i in range(len(out) - 1, 0, -1):
        j = int(rng.random() * (i + 1))
        out[i], out[j] = out[j], out[i]
    return out


def neighbour_flags(values):
    """D-27: for each value, whether it is at edit distance exactly 1 from a taught-anywhere value
    (numeric slots keep these; they are flagged, never rejected)."""
    taught = taught_anywhere()
    return [
        any(levenshtein(v, t) == 1 for t in taught if abs(len(t) - len(v)) <= 1) for v in values
    ]


def numeric_candidates(slot, tok, completions_by_slot, questions, *, accepted):
    """D-09 / D-26 / D-27: the slot's range ascending through NUMERIC_FILTERS in order; returns
    (kept ascending, {filter: rejections}). ``accepted`` are the values already minted in other
    slots (substring_minted). No neighbour screen: numeric slots are exempt (D-27)."""
    _prove(
        slot in NUMERIC_RANGES, f"{slot!r} is not one of the NUMERIC_RANGES {tuple(NUMERIC_RANGES)}"
    )
    taught = next(f.value for f in phase14_factset.LOCKED_FACTS if f.slot == slot)
    taught_count = len(tok.encode(taught))
    excluded = taught_anywhere()
    screen = _new_screen(tok, questions, accepted)
    lo, hi = NUMERIC_RANGES[slot]
    kept, rejections = [], dict.fromkeys(NUMERIC_FILTERS, 0)
    for n in range(lo, hi + 1):
        value = str(n)
        count = len(tok.encode(value))
        if count != taught_count:
            failed = "token_count"
        elif value in excluded:
            failed = "excluded"
        else:
            failed = _screen(tok, value, count, screen)
        if failed is None and not phase14_factset.exact_match_clean(
            completions_by_slot[slot], value
        ):
            failed = "clearance"
        if failed is None:
            kept.append(value)
        else:
            rejections[failed] += 1
    return kept, rejections


def max_set_size(n_cleared):
    """D-31: max |R| = min(e5_max_set_size, n_cleared + 1); |R| counts the taught value."""
    return min(phase35_prereg.ENTRIES["e5_max_set_size"]["value"], n_cleared + 1)


def nested_sizes(max_size):
    """D-08: the NESTED_SIZES below ``max_size``, plus ``max_size`` itself."""
    _prove(max_size >= NESTED_SIZES[0], f"max |R| {max_size} is below {NESTED_SIZES[0]}")
    return tuple(s for s in NESTED_SIZES if s < max_size) + (max_size,)


def mint_all(
    tok, completions_by_slot, questions_by_slot, *, per_slot=SLACK_PER_SLOT, max_draws=MAX_DRAWS
):
    """The whole minting rule (e5_minting_rule), all eight slots in SLOTS order.

    The seed is read here, lazily, as phase35_prereg.seed_list()[0] (torch at import). The name
    slots come from mint_names; any short slot at ``max_draws`` is the D-26 STOP. The numeric slots
    follow in NUMERIC_RANGES order, each excluding every value already accepted, then shuffled
    (D-10) and flagged (D-27).
    """
    seed = phase35_prereg.seed_list()[0]
    questions = [q for slot in SLOTS for q in questions_by_slot[slot]]
    names = mint_names(
        tok, completions_by_slot, questions, per_slot=per_slot, seed=seed, max_draws=max_draws
    )
    counts = {slot: len(values) for slot, values in names["lists"].items()}
    _prove(
        names["reached"],
        f"D-26 STOP: name slots short of {per_slot} at max_draws = {max_draws}: {counts}. Write "
        "nothing; bring the numbers to Rafael; never lower the slack",
    )
    slots = {
        slot: {
            "cleared": names["lists"][slot],
            "taught_token_count": names["taught_token_count"][slot],
            "rejections": names["rejections"][slot],
        }
        for slot in NAME_SLOTS
    }
    accepted = [v for values in names["lists"].values() for v in values]
    for slot in NUMERIC_RANGES:
        kept, rejections = numeric_candidates(
            slot, tok, completions_by_slot, questions, accepted=accepted
        )
        accepted += kept
        cleared = seeded_shuffle(kept, seed)
        flags = neighbour_flags(cleared)
        slots[slot] = {
            "cleared": cleared,
            "taught_token_count": len(
                tok.encode(next(f.value for f in phase14_factset.LOCKED_FACTS if f.slot == slot))
            ),
            "rejections": rejections,
            "neighbour_d1": [i for i, flag in enumerate(flags) if flag],
        }
    for row in slots.values():
        row["n_cleared"] = len(row["cleared"])
        row["max_set_size"] = max_set_size(row["n_cleared"])
    return {
        "seed": seed,
        "per_slot": per_slot,
        "max_draws": max_draws,
        "stream": names["stream"],
        "stop_draw": names["stop_draw"],
        "slots": {slot: slots[slot] for slot in SLOTS},
    }
