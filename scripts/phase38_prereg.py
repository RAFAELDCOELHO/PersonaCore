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
