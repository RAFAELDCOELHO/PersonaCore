"""UNIT-03's INSTRUMENT: the per-fact multiplicity COUNTER, and where its artifact will land.

UNIT-03 refuses the analytic number as the artifact. D-26 fixes WHAT is measured — both paths,
an instrumented loader, ``SEED = 1337``, ``MAX_STEPS = 200``, ``BATCH_SIZE = 8``, every row
labelled with its bin composition — but not HOW WE KNOW THE COUNTER COUNTS. This module is the
counter; ``tests/test_phase21_multiplicity.py`` is the evidence that it counts. Plan 21-11 adds
the artifact emission; **this plan writes no artifact**.

WHY THIS FILE IS NOT NAMED ``mitigation_*`` (D-22)
--------------------------------------------------
``tests/test_phase20_prereg.py:72``'s ``scripts/mitigation_*.py`` glob carries a HARD IMPORT
CEILING accumulated across every module in the glob (``:498``) and asserted a subset of
``{"pathlib", "sys", "erasure_gate"}`` (``:522``). ``json``, ``numpy`` and ``torch`` are therefore
unreachable from any ``mitigation_*`` module. ``scripts/mitigation_unit.py`` holds the RULE and
does zero I/O; this module holds its EMISSION and is deliberately outside the glob. Renaming this
file into the glob would turn ``test_phase20_prereg.py`` red at import.

THE ATTRIBUTION RULE — ``21-RESEARCH.md`` Open Question 2, RESOLVED
------------------------------------------------------------------
A random ``block_size`` window over an UNALIGNED bin can overlap two facts, and the two defensible
attributions give different conservation laws:

===============================================  =========================  =====================
rule                                             conservation RHS           note
===============================================  =========================  =====================
**first token's fact owns the draw**  (CHOSEN)   ``steps * batch_size``     an EXACT EQUALITY
every overlapped fact is credited                ``> steps * batch_size``   an INEQUALITY
===============================================  =========================  =====================

Chosen: the FIRST. It makes the conservation law an equality with no tolerance to tune and no
distributional assumption; it matches D-26's own denominator (``MAX_STEPS * BATCH_SIZE`` = 1,600
draws); and the ALIGNED answer is unchanged either way, because an aligned window overlaps exactly
one fact by construction. The rejected rule is richer — it is a genuine measure of "how often is
this fact's data read" — but it leaves nothing to check exactly, which is the entire value of the
conservation law as an instrument test.

**The rule is named in ONE place and imported from it.** An UNNAMED attribution rule is precisely
how the artifact's two labelled rows stop being comparable: the same corpus yields two different
"multiplicities" and a reader cannot tell which was recorded.

WHAT THE CONSERVATION LAW COSTS, STATED SO IT IS NOT MISREAD
------------------------------------------------------------
Under the chosen rule ``sum(counts.values()) == total_draws`` EXACTLY, so the per-fact MEAN is
pinned at ``total_draws / n_facts`` by arithmetic and carries no information about the corpus.
Everything the measurement says lives in ``min`` / ``max`` / ``spread``. That is why D-26 requires
"min/max/mean/spread, not merely an expectation", and it is why the frozen module's analytic
``262.94`` (``scripts/mitigation_unit.py``'s ``PRIVACY_UNIT_ARITHMETIC``) is NOT the quantity this
counter reports: that figure is the OVERLAP expectation — its ``(947.625 + 256)`` numerator is the
number of start offsets from which a ``block_size`` window TOUCHES a fact of 947.625 tokens — i.e.
it is the rejected rule's number. The two are reconciled, not confused:

    first-token E[count for fact f] = total_draws * starts_owned_by_f / draw_start_offsets
    overlap     E[count for fact f] = total_draws * (L_f + block_size) / draw_start_offsets

They differ by ``total_draws * block_size / draw_start_offsets`` per fact. Neither is wrong; they
answer different questions, and a row that does not name its rule is unreadable.

HOW EACH PATH IS INSTRUMENTED, WITH THE ROUTE THAT WAS REJECTED
---------------------------------------------------------------
* **Unaligned** — ``count_unaligned`` runs the draws through
  :func:`personacore.training.data.get_batch_memmap_masked`, THE SAME function training uses, and
  observes the start indices by WRAPPING ``np.random.randint`` for the duration of the count. The
  wrapper asserts it saw exactly ``steps`` calls of size ``batch_size``; that call-count assertion
  is what proves it observed ALL of them, and the instrument's own provenance is part of the
  evidence. **REJECTED:** re-deriving the indices by seeding identically and calling
  ``np.random.randint`` again with the same arguments. That measures a RE-IMPLEMENTATION of the
  draw rather than the draw itself, and it would pass unchanged if the loader stopped drawing.
  **ALSO REJECTED:** adding a ``return_indices=None`` kwarg to ``get_batch_memmap_masked``. D-10
  reuses that function UNCHANGED, plan 21-06's success criterion is that it stays byte-unchanged,
  and a fourth additive default-``None`` kwarg with no is-wired pair is the exact defect class this
  phase exists to eliminate (``21-VALIDATION.md:138``).

* **Aligned** — ``count_aligned`` runs micro-steps of
  :func:`personacore.training.data.get_batch_fact_aligned` and counts the OBSERVED ``fact_index``,
  plus ``per_step_distinct_facts``, which is what makes "1 by construction" a VERIFIED number
  rather than an assumed one. The window range comes from
  :func:`personacore.training.data.fact_window_span` — the function the LOADER ITSELF draws
  through, exported by plan 21-06 for exactly this reason — so the counter is never a second
  implementation of the loader's window arithmetic, free to drift from the draw it is describing.
  Nothing about the draw is recomputed here; only the abort is suppressed, and only under
  ``strict=False``, and only in a test. **REJECTED:** counting distinct ids from the windows the
  loader returns. It is impossible: the loader RAISES before returning on exactly the bins the
  non-vacuity test needs, and it returns ``(x, y, fact_index)`` carrying no fact ids at all.

CPU-only: no MPS, no CUDA, no ``torch.compile``.
"""

import pathlib
import sys

import numpy as np

from personacore.seeding import seed_everything
from personacore.training.data import (
    fact_window_span,
    get_batch_fact_aligned,
    get_batch_memmap_masked,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import teach_persona as tp  # noqa: E402  (sibling script; the path insert above is what finds it)

# The resolution of `21-RESEARCH.md` Open Question 2. One place, imported by the tests and by the
# artifact schema, because two spellings of an attribution rule is two incomparable rows.
ATTRIBUTION_RULE = "first-token-owns-draw"

# D-26's three bin-composition labels, verbatim. A row without one re-opens the ambiguity SC3 left
# behind ("after build_bins packing at the chosen replay_ratio" predates D-10, which moved replay
# out of the teaching bin entirely), which is exactly what labelling closes IN THE ARTIFACT.
BIN_COMPOSITION_LABELS = (
    "replay-in-bin @1.0",
    "facts-only (D-10)",
    "fact-aligned (D-01, D-05)",
)

# The exact `results/phase21_*` paths this driver will write in plan 21-11, declared HERE so every
# consumer resolves them from a constant rather than from a string literal in a plan step. THIS
# PLAN WRITES NEITHER: `git ls-files 'results/phase21_*'` must still be empty at its close, because
# `adds[-1]` (`tests/test_phase20_prereg.py:157`) makes the ancestry ordering irrevocable.
ARTIFACTS = {
    "privacy_unit": _ROOT / "results" / "phase21_privacy_unit.json",
    "multiplicity": _ROOT / "results" / "phase21_multiplicity.json",
}

# The schema every row carries, so a silently thinned record fails a one-line assertion rather
# than reaching the artifact. D-26: "min/max/mean/spread, not merely an expectation".
ROW_SCHEMA = (
    "bin_composition",
    "attribution_rule",
    "seed",
    "steps",
    "batch_size",
    "total_draws",
    "bin_tokens",
    "n_windows",
    "n_facts",
    "min",
    "max",
    "mean",
    "spread",
)

_DEVICE = "cpu"


def refuse_existing_artifacts(paths=None):
    """Refuse-to-rerun for the artifact paths — ``teach_persona.refuse_if_exists``, IMPORTED.

    The write path plan 21-11 fills in. The refusal is INHERITED rather than invented so there is
    one refuse-to-rerun implementation in the repository and not two: a recorded artifact silently
    replaced by a rerun on drifted code is the failure mode, and it is identical here and in
    ``teach_persona``.
    """
    return tp.refuse_if_exists([pathlib.Path(p) for p in (paths or ARTIFACTS.values())])


def _summarise(counts):
    """``min``/``max``/``mean``/``spread`` over EVERY fact — including the ones drawn zero times.

    ``counts`` is seeded with every fact id in the map before any draw, so a fact that no draw
    landed on appears as ``0`` rather than vanishing. That distinction is load-bearing: a counter
    that summarised only the facts it observed would report a ``min`` above zero on a corpus where
    some fact is provably unreachable, which is the flattering direction.
    """
    values = sorted(counts.values())
    return {
        "min": values[0],
        "max": values[-1],
        "mean": sum(values) / len(values),
        "spread": values[-1] - values[0],
    }


def _row(*, bin_composition, seed, steps, batch_size, total_draws, bin_tokens, n_windows, counts):
    """One artifact row: the counts, their denominators, and the rule that produced them."""
    row = {
        "bin_composition": bin_composition,
        "attribution_rule": ATTRIBUTION_RULE,
        "seed": seed,
        "steps": steps,
        "batch_size": batch_size,
        "total_draws": total_draws,
        "bin_tokens": bin_tokens,
        "n_windows": n_windows,
        "n_facts": len(counts),
        "counts": dict(counts),
    }
    row.update(_summarise(counts))
    return row


def _read_fact_map(bin_path, fact_path):
    """The fact map, plus the token bin's element count, with the 1:1 contract asserted.

    A length skew between the token bin and the fact map silently mis-attributes draws — the same
    failure ``get_batch_fact_aligned`` refuses across three bins (D-06 proof 1). ``count_unaligned``
    draws through ``get_batch_memmap_masked``, which checks token-vs-mask and knows nothing about a
    third file, so the token-vs-fact half has to be checked here or nowhere.
    """
    fact_ids = np.fromfile(fact_path, dtype=np.uint16)
    bin_tokens = len(np.memmap(bin_path, dtype=np.uint16, mode="r"))
    if len(fact_ids) != bin_tokens:
        raise ValueError(
            f"the token bin {bin_path} has {bin_tokens} elements but the fact map {fact_path} has "
            f"{len(fact_ids)} — they must be element-aligned for a draw's START INDEX to name a "
            "fact at all. A skew here does not raise, it MIS-ATTRIBUTES, so it is checked before "
            "any counting rather than discovered in the artifact."
        )
    return fact_ids, bin_tokens


def count_unaligned(
    bin_path,
    mask_path,
    fact_path,
    *,
    steps,
    batch_size,
    seed,
    block_size,
    bin_composition,
):
    """Count per-fact draws on the REAL random-window path — UNIT-01's indictment, measured.

    Runs ``steps`` draws of :func:`personacore.training.data.get_batch_memmap_masked` — the same
    function ``train()`` uses — and attributes each drawn window to ``fact_ids[start]`` per
    :data:`ATTRIBUTION_RULE`.

    ``bin_composition`` is REQUIRED and has no default. D-26 makes the label part of the row, and a
    default would let the one field that disambiguates which bin was measured go quietly missing.
    The three PUBLISHED literals are in :data:`BIN_COMPOSITION_LABELS`; a synthetic validation
    fixture passes its own descriptive label, which is why membership is not enforced here.

    Returns a row dict carrying :data:`ROW_SCHEMA` plus ``counts`` and ``draw_start_offsets``.
    ``draw_start_offsets`` — ``bin_tokens - block_size - 1``, the size of ``np.random.randint``'s
    support — is the DENOMINATOR of the analytic expectation, and it is recorded because the naive
    denominator (``bin_tokens``) gives a different number: that is the exact confusion
    ``scripts/mitigation_unit.py`` had to write a formula into a frozen file to settle.
    """
    fact_ids, bin_tokens = _read_fact_map(bin_path, fact_path)

    seed_everything(seed)

    # THE PINNED ROUTE. The wrapper observes the REAL call in place; it does not re-create it.
    # Installed AFTER seeding so the spy's own bookkeeping cannot be confused with the seeding.
    real_randint = np.random.randint
    observed_sizes, observed_starts = [], []

    def _spy(*args, **kwargs):
        ix = real_randint(*args, **kwargs)
        observed_sizes.append(int(np.size(ix)))
        observed_starts.append(np.asarray(ix).copy())
        return ix

    np.random.randint = _spy
    try:
        for _ in range(steps):
            get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, _DEVICE)
    finally:
        np.random.randint = real_randint

    # The instrument's OWN provenance, asserted rather than assumed: a wrapper that saw fewer calls
    # than there were draws is an undercount that no downstream check would notice, because the
    # conservation law would still balance against the draws it DID see.
    if len(observed_sizes) != steps or set(observed_sizes) != {batch_size}:
        raise ValueError(
            f"the np.random.randint wrapper saw {len(observed_sizes)} call(s) of size(s) "
            f"{sorted(set(observed_sizes))} where {steps} call(s) of size {batch_size} were "
            "expected — the instrument did not observe every draw, so its counts are not a "
            "measurement of this budget."
        )

    counts = {int(f): 0 for f in np.unique(fact_ids)}
    for starts in observed_starts:
        for start in starts:
            counts[int(fact_ids[int(start)])] += 1

    row = _row(
        bin_composition=bin_composition,
        seed=seed,
        steps=steps,
        batch_size=batch_size,
        total_draws=steps * batch_size,
        bin_tokens=bin_tokens,
        n_windows=bin_tokens // block_size,
        counts=counts,
    )
    row["draw_start_offsets"] = bin_tokens - block_size - 1
    return row


def count_aligned(
    bin_path,
    mask_path,
    fact_path,
    *,
    steps,
    n_facts,
    block_size,
    bin_composition,
    strict=True,
):
    """Count per-fact micro-steps on the FACT-ALIGNED path, and observe the "1" it claims.

    One micro-step is one privacy record (D-01 / D-05 / D-06), so the count is per STEP and the
    conservation law is ``sum(counts.values()) + <steps that raised> == steps`` — an exact equality
    in every case, including the mis-built bins ``strict=False`` exists to observe.

    ``per_step_distinct_facts`` is the number of distinct fact ids present in the windows the step
    draws. It is what makes "1 by construction" a VERIFIED number rather than an assumed one, and
    it is what the non-vacuity test reads.

    ``strict`` — the DEFAULT is ``True`` and that is the path plan 21-11 uses for the record:

    * ``strict=True``: the loader's raise propagates UNTOUCHED. A mis-built bin must never quietly
      produce a published row.
    * ``strict=False``: BOTH calls — ``fact_window_span`` AND the loader — sit inside ONE
      ``try/except ValueError``, and the step's outcome is RECORDED instead of aborting the count.

    **Both calls, not only the loader's, and the ORDER inside the ``try`` is the whole mechanism.**
    ``np.unique`` runs IMMEDIATELY AFTER ``fact_window_span`` and STRICTLY BEFORE the loader call,
    because on the roll-by-1 adversary EVERY step raises — the loader raises impurity on the
    contiguous facts and ``fact_window_span`` raises on the one fact the roll leaves
    non-contiguous. With ``np.unique`` placed after the loader call, every step exits before
    reaching it, ``per_step_distinct_facts`` is all ``None``, and the non-vacuity test's
    ``max(...)`` dies on an empty sequence: the test would ERROR rather than fail, a strictly worse
    outcome than the abort this parameter exists to prevent. The ``stage`` local (``"span"`` then
    ``"loader"``) is what lets ONE ``except`` arm name WHICH call raised, so a suppressed abort is
    an OBSERVATION and never a silence — and a span failure is STRONGER evidence of a mis-built bin
    than ``distinct == 2``, so it is its own outcome class rather than folded into the count.

    ``fact_window_span``'s contiguity raise is NOT relaxed to make this route work. That raise is
    plan 21-06's packing-defect guard, it is shared with the LOADER, and the standing rule is that
    a shared predicate is never adjusted to fit a caller.

    The map is read ONCE here for the span observation; the LOADER re-reads all three bins on every
    call, which is where D-06's run-time-consumption property lives and where
    ``tests/test_phase21_aligned_loader.py`` proves it. This function does not re-assert it.
    """
    fact_ids, bin_tokens = _read_fact_map(bin_path, fact_path)
    n_windows = (bin_tokens - 1) // block_size

    counts = {index: 0 for index in range(n_facts)}
    per_step_fact_index, per_step_distinct_facts, per_step_raised = [], [], []

    for step in range(steps):
        fact_index = step % n_facts
        stage, distinct, raised = "span", None, None
        try:
            start, k = fact_window_span(fact_ids, fact_index, block_size)
            distinct = int(np.unique(fact_ids[start : start + k * block_size]).size)
            stage = "loader"
            _x, _y, observed = get_batch_fact_aligned(
                bin_path,
                mask_path,
                fact_path,
                block_size,
                _DEVICE,
                step=step,
                n_facts=n_facts,
            )
            counts[int(observed)] += 1
        except ValueError:
            if strict:
                raise
            raised = stage
        per_step_fact_index.append(fact_index)
        per_step_distinct_facts.append(distinct)
        per_step_raised.append(raised)

    row = _row(
        bin_composition=bin_composition,
        seed=None,  # the aligned draw is DETERMINISTIC — q = 1, no subsampling (D-01/D-07)
        steps=steps,
        batch_size=None,  # RAGGED by construction: 4 or 5 windows per record, never a scalar
        total_draws=steps,
        bin_tokens=bin_tokens,
        n_windows=n_windows,
        counts=counts,
    )
    row["per_step_fact_index"] = per_step_fact_index
    row["per_step_distinct_facts"] = per_step_distinct_facts
    row["per_step_raised"] = per_step_raised
    return row
