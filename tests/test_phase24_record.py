"""The committed ADVT-03 token-budget record, RE-DERIVED rather than read back and believed.

The subject is ``results/phase24_token_budget.json`` and its emitter ``scripts/phase24_record.py``.
The path is resolved from ``phase24_record.TOKEN_BUDGET_RECORD`` and never spelled a second time in
executable code — ``tests/test_phase23_budget.py:359``'s ``_cost_record`` register: one small parser
per record, the path owned by the module that writes it.

**What makes this more than a schema check.** A record whose numbers are only ever compared against
themselves proves nothing; a hand-edited figure would pass every key-presence assertion in this
file. :func:`test_scored_tokens_re_derive_from_a_rebuild` therefore rebuilds the two control rows'
bins live and compares the scored-token counts under EXACT ``==``. That test was watched failing on
a deliberate one-digit hand edit before it was allowed to be green.

CPU-only, GPU/MPS-free, no training. The rebuild lands under ``tmp_path``, never ``data/``.
"""

import hashlib
import json
import pathlib
import sys

import numpy as np

from personacore.seeding import seed_everything
from personacore.tokenizer import from_json

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_budget as mb  # noqa: E402  (scripts/ is not a package)
import phase14_factset as fs  # noqa: E402
import phase18_extraction as p18  # noqa: E402
import phase24_adversarial as pa  # noqa: E402
import phase24_record as rec  # noqa: E402
import teach_persona as tp  # noqa: E402


def _record():
    """The committed record, parsed. ONE reader, and the path comes from its owning module."""
    return json.loads(rec.TOKEN_BUDGET_RECORD.read_text(encoding="utf-8"))


def _rebuild_scored_tokens(tmp_path, arm, ratio):
    """Rebuild one row's bins from scratch and return ``(scored_tokens, total_tokens, fraction)``.

    Deliberately NOT a call into ``phase24_record._row``: an independent re-derivation that reused
    the emitter's own code path would agree with it by construction. This drives ``tp.build_bins``
    directly, the same way the emitter's docstring says the record was produced.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    facts, _second_person, _replay_ratio = tp.arm_spec(arm)
    episodes = tp.render_episodes(facts, fs.TAUGHT_FAMILY_IDS)
    bin_path = tmp_path / f"{arm}.bin"
    mask_path = tmp_path / f"{arm}_mask.bin"
    seed_everything(tp.SEED)
    stats = tp.build_bins(
        from_json(tp.TOKENIZER_PATH),
        episodes,
        bin_path,
        mask_path,
        align_facts=None,
        adversarial_ratio=ratio,
        seed=tp.SEED,
    )
    scored = int(np.fromfile(mask_path, dtype=np.uint8).sum())
    return scored, int(stats["tokens"]), float(stats["mask_fraction"])


# =============================================================================================
# ===== 1. COVERAGE ===========================================================================
# =============================================================================================


def test_the_record_covers_every_grid_point_at_both_capacities():
    """``{arm} x ADVERSARIAL_RATIO_GRID`` under HARD SET EQUALITY, not a count.

    A count is satisfied by twelve copies of one point. The grid is IMPORTED from
    ``mitigation_budget`` so a moved grid reddens this instead of agreeing with a stale record.
    """
    record = _record()

    # Non-vacuity FIRST: an empty grid or a one-armed record would make the equality below
    # trivially satisfiable by an empty record.
    assert mb.ADVERSARIAL_RATIO_GRID, "the pinned grid is empty — every assertion below is vacuous"
    assert set(record["arms"]) == set(rec.ARMS), (
        f"the record names arms {record['arms']} against the emitter's {list(rec.ARMS)}"
    )
    assert len(rec.ARMS) > 1, "one capacity is not 'both capacities' — D-07 runs the grid at two"

    expected = {(arm, ratio) for arm in rec.ARMS for ratio in mb.ADVERSARIAL_RATIO_GRID}
    observed = {(row["arm"], row["adversarial_ratio"]) for row in record["rows"]}
    assert observed == expected, (
        f"the record covers {sorted(observed)} against the full cross product {sorted(expected)}. "
        f"Missing: {sorted(expected - observed)}. Unexpected: {sorted(observed - expected)}."
    )
    assert len(record["rows"]) == len(expected), (
        f"{len(record['rows'])} rows for {len(expected)} distinct points — a duplicated point "
        "would make every per-row assertion below run twice on one measurement."
    )


# =============================================================================================
# ===== 2. COUNTS, NEVER RATES ================================================================
# =============================================================================================


def test_every_row_reports_counts_with_a_denominator():
    """Every measured figure is an integer COUNT carrying its own denominator and source label.

    The counts-never-rates discipline made checkable: the rate is DERIVABLE from the counts (and
    that derivation is asserted here to 1e-9), while the counts are not derivable from the rate.
    A record holding only ``mask_fraction`` would be a pre-reduced scalar nothing can re-derive.
    """
    rows = _record()["rows"]
    assert rows, "no rows — every assertion below is vacuous"

    for row in rows:
        label = f"{row['arm']} @ adversarial_ratio={row['adversarial_ratio']!r}"
        scored, total = row["scored_tokens"], row["total_tokens"]

        assert isinstance(scored, int) and not isinstance(scored, bool), (
            f"{label}: scored_tokens is {type(scored).__name__}, not an int — a float here is the "
            "signature of mask_fraction * total_tokens, which is exactly the derivation this "
            "record refuses to make."
        )
        assert isinstance(total, int) and total > 0, f"{label}: total_tokens is {total!r}"
        assert 0 <= scored <= total, (
            f"{label}: scored_tokens {scored} outside [0, total_tokens {total}]"
        )

        for key in ("scored_tokens_denominator", "scored_tokens_source", "mask_fraction_source"):
            value = row.get(key)
            assert isinstance(value, str) and value.strip(), (
                f"{label}: {key} is {value!r} — every measured figure carries its own denominator "
                "and its own source label (phase21_unit_record._corpus_geometry's discipline)."
            )

        assert abs(scored / total - row["mask_fraction"]) < 1e-9, (
            f"{label}: scored_tokens / total_tokens = {scored / total!r} against the recorded "
            f"mask_fraction {row['mask_fraction']!r}. The rate and the counts have drifted, so at "
            "least one of them was not measured off the bin that was written."
        )


def test_scored_tokens_re_derive_from_a_rebuild(tmp_path):
    """The two CONTROL rows' scored-token counts, rebuilt live and compared under exact ``==``.

    Scoped to ``adversarial_ratio == 0.0`` on purpose: those two builds are the cheap ones (no
    corpus pass, no interleave) and keep this module inside 24-VALIDATION.md's sampling budget.
    The ten non-zero rows are covered structurally instead — by
    :func:`test_every_row_reports_counts_with_a_denominator`'s counts-to-rate agreement and by
    ``tests/test_phase24_band.py``'s independent build of both upper corners.

    A hand-edited number goes RED here. That was WATCHED, not assumed.
    """
    control = mb.ADVERSARIAL_RATIO_GRID[0]
    rows = {row["arm"]: row for row in _record()["rows"] if row["adversarial_ratio"] == control}
    assert set(rows) == set(rec.ARMS), (
        f"the control point {control!r} is recorded for {sorted(rows)} and not for every arm — "
        "this test would silently check fewer rows than it claims."
    )

    for arm, row in rows.items():
        scored, total, fraction = _rebuild_scored_tokens(tmp_path / arm, arm, control)
        assert scored == row["scored_tokens"], (
            f"{arm} @ the control point rebuilt {scored:,} scored tokens against the recorded "
            f"{row['scored_tokens']:,}. Either the record was hand-edited, or the packer, the "
            "tokenizer or the teaching pack moved without the record being regenerated."
        )
        assert total == row["total_tokens"], (
            f"{arm}: rebuilt {total:,} total tokens against the recorded {row['total_tokens']:,}"
        )
        assert fraction == row["mask_fraction"], (
            f"{arm}: rebuilt mask_fraction {fraction!r} against the recorded "
            f"{row['mask_fraction']!r}"
        )


# =============================================================================================
# ===== 3. THE BAND, AT EVERY POINT ===========================================================
# =============================================================================================


def test_every_point_clears_the_band():
    """Every one of the twelve points clears the floor by ``MASK_FRACTION_MARGIN``, and the
    fraction is monotonically NON-INCREASING in ``adversarial_ratio`` within each arm.

    The monotonicity half is the measured content of "only the floor binds". Both effects of the
    mixture are supposed to push the fraction down — a long unmasked attack prompt and a short
    masked refusal — so if the sequence ever rises, the one-sided reasoning that lets this phase
    ignore the band's upper bound has stopped holding and the ceiling needs checking too.
    """
    record = _record()
    floor, ceiling = tp.MASK_FRACTION_BAND
    target = floor + pa.MASK_FRACTION_MARGIN

    for row in record["rows"]:
        label = f"{row['arm']} @ adversarial_ratio={row['adversarial_ratio']!r}"
        assert row["mask_fraction"] >= target, (
            f"{label}: mask_fraction {row['mask_fraction']:.6f} below the required "
            f"{floor} + {pa.MASK_FRACTION_MARGIN} = {target:.6f}. "
            "teach_persona._prove_floor_and_band SystemExits at BUILD time below the floor, so "
            "this point would burn a sweep point's compute before failing."
        )
        assert row["mask_fraction"] <= ceiling, (
            f"{label}: mask_fraction {row['mask_fraction']:.6f} above the band ceiling {ceiling}"
        )

    for arm in rec.ARMS:
        ordered = [
            row["mask_fraction"]
            for ratio in mb.ADVERSARIAL_RATIO_GRID
            for row in record["rows"]
            if row["arm"] == arm and row["adversarial_ratio"] == ratio
        ]
        assert len(ordered) == len(mb.ADVERSARIAL_RATIO_GRID), (
            f"{arm} contributes {len(ordered)} points to the monotonicity check against "
            f"{len(mb.ADVERSARIAL_RATIO_GRID)} grid points — the check would be run on a subset."
        )
        assert ordered == sorted(ordered, reverse=True), (
            f"{arm}'s mask_fraction is not non-increasing in adversarial_ratio: {ordered}. The "
            "mixture is supposed to push the fraction DOWN on both counts, so a rise means the "
            "'only the floor binds' analysis behind ignoring the band ceiling no longer holds."
        )


# =============================================================================================
# ===== 4. THE CONFOUND, KEPT DISTINCT ========================================================
# =============================================================================================


def test_the_token_budget_confound_keeps_both_figures_distinct():
    """3.73x (cross-family) and 1.40x (one uppercased sentence) never collapse into one number.

    They describe different things — a per-family corpus mean over 112 rows each, against a
    per-sentence perturbation cost for one 51-character sentence — and are trivially conflated,
    which is the whole reason ADVT-03's disclosure exists.
    """
    record = _record()
    disclosure = record["token_budget_disclosure"]

    assert disclosure["cross_family_inflation"] == 3.73, (
        f"cross_family_inflation is {disclosure['cross_family_inflation']!r}; the measured "
        "cross-family prompt-token ratio is 3.73."
    )
    note = disclosure["cross_family_inflation_note"].lower()
    assert "a3/a2" in note, "the note must name WHICH two families the ratio is taken over"
    assert "not the 1.40x" in note, (
        "the note must state in words that this is NOT the 1.40x single-sentence figure — a "
        "reader who sees only the number will use it as if it were."
    )

    # 1.40 may appear in PROSE (it must, above) but never as the VALUE of an inflation field.
    numeric_inflation = {
        key: value
        for key, value in disclosure.items()
        if "inflation" in key and isinstance(value, (int, float)) and not isinstance(value, bool)
    }
    assert numeric_inflation, "no numeric inflation field at all — the assertion below is vacuous"
    for key, value in numeric_inflation.items():
        assert abs(value - 1.40) > 1e-9, (
            f"{key} is {value!r} — ADVT-03's 1.40x single-sentence figure has been substituted "
            "for the cross-family measurement."
        )

    corpus_block = record["attack_corpus"]
    assert corpus_block["held_out_family"] not in corpus_block["trained_families"], (
        f"{corpus_block['held_out_family']!r} appears in trained_families "
        f"{corpus_block['trained_families']} — the held-out family is, by definition, not trained."
    )
    assert corpus_block["held_out_family"] == pa.HELD_OUT_FAMILY
    assert list(corpus_block["trained_families"]) == list(pa.TRAINED_FAMILIES)

    # The digest is RECOMPUTED here, never compared against a pasted copy of itself.
    live = p18.corpus_sha256(json.loads(p18.CORPUS_PATH.read_text(encoding="utf-8")))
    assert corpus_block["sha256"] == live, (
        f"the record names corpus sha256 {corpus_block['sha256']} against the live "
        f"{live} — the attack corpus has moved since the record was written, so every per-family "
        "token figure in it describes a corpus that no longer exists."
    )


# =============================================================================================
# ===== 5. THE PROVENANCE PINS, AGAINST THE LIVE BYTES ========================================
# =============================================================================================


def test_the_provenance_pins_match_the_live_module_bytes():
    """Every ``provenance.module_sha256`` entry (and ``tokenizer_sha256``) equals the file on disk.

    The sibling of the ``corpus_sha256`` check above, and it exists because that asymmetry was a
    real defect: 24-VERIFICATION found `corpus_sha256` guarded and `module_sha256` NOT, so two of
    the four pins rotted through a whole plan while this suite stayed green. That is the
    "green guard, unenforced invariant" shape this repository keeps re-finding.

    ``scripts/phase24_record.py:418`` calls a non-matching digest "visible in the record itself" —
    but visible to WHOM? Nothing looked. This test is what looks.

    Digests are recomputed from BYTES here (``tests/test_package.py:36``'s rule) rather than
    through the emitter's own ``_sha256``: a pin re-derived by the function that wrote it would
    agree with it by construction even if that function started hashing text.

    ALL drifted modules are collected before asserting, so one failure names every one of them
    with both digests — a bare ``assert recorded == live`` inside the loop would name the first
    and hide the rest, which is a worse guard than none where the reader concludes "one file".
    """
    pins = dict(_record()["provenance"]["module_sha256"])
    assert pins, "provenance.module_sha256 is empty — this assertion would be vacuous"

    # The emitter must pin ITSELF, or the record cannot claim its own reproducibility.
    emitter = str(pathlib.Path(rec.__file__).resolve().relative_to(_ROOT))
    assert emitter in pins, (
        f"{emitter} is not among the pinned modules {sorted(pins)} — the record does not name the "
        "bytes that wrote it, so no digest in it can establish that HEAD regenerates it."
    )
    pins[str(tp.TOKENIZER_PATH.relative_to(_ROOT))] = _record()["provenance"]["tokenizer_sha256"]

    drifted = []
    for name, recorded in pins.items():
        path = _ROOT / name
        assert path.is_file(), f"provenance pins {name}, which does not exist at {path}"
        live = hashlib.sha256(path.read_bytes()).hexdigest()
        if live != recorded:
            drifted.append((name, recorded, live))

    assert not drifted, (
        f"{len(drifted)} of {len(pins)} provenance digests no longer match the files on disk:\n"
        + "".join(
            f"    {name}\n      recorded {rec_}\n      live     {liv}\n"
            for name, rec_, liv in drifted
        )
        + "  provenance.module_sha256 claims these bytes regenerate this record. They no longer "
        "do. The record's NUMBERS may still be correct — check them separately — but the pin is "
        "no longer evidence of anything. Re-emit: delete "
        f"{rec.TOKEN_BUDGET_RECORD.relative_to(_ROOT)} at a clean tree and run "
        "`python scripts/phase24_record.py`, then confirm every substantive figure came out "
        "byte-identical before committing."
    )
