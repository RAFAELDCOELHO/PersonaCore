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

WHY ``json`` IS IMPORTABLE HERE AND NOWHERE IN ``mitigation_*`` (D-22) — DO NOT TIDY THE TWO
FILES TOGETHER
---------------------------------------------------------------------------------------------
The two emitters below write ``results/phase21_*.json``, and ``json`` is reachable from this
module for exactly one reason: this file is OUTSIDE ``tests/test_phase20_prereg.py:72``'s
``scripts/mitigation_*.py`` glob, whose accumulated import set is asserted a subset of
``{"pathlib", "sys", "erasure_gate"}``. Merging this emitter into ``scripts/mitigation_unit.py``
— or renaming this file to ``mitigation_something.py`` — turns that assertion RED at import. The
rule lives in the frozen pin and does zero I/O; its EMISSION lives here. That split is a
constraint, not a stylistic preference, and it is recorded here so a later reader does not
"simplify" it away.

**Every pinned value in the emitted artifact is IMPORTED from** :mod:`mitigation_unit` **and
computed at write time.** Retyping a pinned number into this driver would make the
pre-registration and the published record two sources that can disagree, and only one of them is
frozen — ``tests/test_phase21_unit_record.py::test_artifact_values_come_from_the_pin`` recomputes
every one of them from the pin and asserts equality.

WHAT IS DELIBERATELY *NOT* IN ``results/phase21_multiplicity.json``
------------------------------------------------------------------
Re-benchmarking D-02's ragged-vs-uniform accumulation ratios (1.14x ragged / 1.39x uniform /
1.35x vmap-uniform) on the REAL bins is a DEFERRED item in ``21-CONTEXT.md``'s ``<deferred>``
list, not an oversight. It is a throughput measurement, it needs a training loop rather than a
loader, and nothing in UNIT-01..UNIT-06 rests on it. Naming the exclusion here stops a later
reader reading its absence as a gap in the record.

CPU-only: no MPS, no CUDA, no ``torch.compile``.
"""

import datetime
import hashlib
import json
import pathlib
import platform
import sys
import tempfile

import numpy as np

from personacore.provenance import git_sha, refuse_if_dirty
from personacore.seeding import seed_everything
from personacore.tokenizer import from_json
from personacore.training.data import (
    fact_window_span,
    get_batch_fact_aligned,
    get_batch_memmap_masked,
)

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_unit as mu  # noqa: E402  (the FROZEN pin — every pinned value is IMPORTED)
import phase14_factset as fs  # noqa: E402  (sibling script; the path insert above is what finds it)
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

# The dirty-tree scope for a PUBLICATION: everything, MINUS the two artifacts being written.
# Derived from `ARTIFACTS` rather than retyped, so a path can never be watched and written under
# two different spellings.
#
# The exclusions are not a softening — they are what makes the guard reachable at all. Re-emitting
# requires deleting the previous artifact first (`refuse_if_exists`), which is itself a dirty
# working tree; without the exclusions the guard would refuse every re-emission including the
# clean ones, and the first person to need one would delete the guard. What the recorded `git_sha`
# claims is that the CODE and INPUTS at that commit reproduce these bytes; the previous contents
# of the output file are neither.
_PUBLICATION_PATHSPEC = (
    ".",
    *(f":(exclude){path.relative_to(_ROOT)}" for path in ARTIFACTS.values()),
)

_DIRTY_DETAIL = (
    "`provenance.git_sha()` records HEAD at write time, so a record written from a dirty tree "
    "names a commit that does NOT contain the code that produced it — the artifact points at a "
    "tree it cannot be regenerated from. That is not hypothetical: 21-REVIEW.md CR-02 found BOTH "
    "committed artifacts carrying exactly that defect (phase21_privacy_unit.json recorded "
    "fa97b666, where `emit_privacy_unit` was not yet defined; phase21_multiplicity.json recorded "
    "17b3c856, where `emit_multiplicity` was not yet defined). Commit the tree, then re-run. Do "
    "NOT work around this by writing to a temporary path and copying the file into results/ — "
    "that reproduces CR-02 with extra steps."
)

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

# D-26's measurement budget, IMPORTED from the run script rather than retyped, so the recorded
# denominators are the ones the real run uses and cannot drift from them.
SEED = tp.SEED  # 1337
BATCH_SIZE = tp.BATCH_SIZE  # 8
MAX_STEPS = tp.MAX_STEPS  # 200
BLOCK_SIZE = tp.BLOCK_SIZE  # 256

# The two DP capacities this milestone runs (UNIT-06). Both, always: the whole point of the n=64
# row is that a record checked only at n=8 leaves open the reading that the small arm was special.
CAPACITY_ARMS = ("dp_n8", "dp_n64")

# The fact-map id given to REPLAY tokens in the `replay-in-bin @1.0` row. Replay is PUBLIC
# PersonaChat dialogue and belongs to NO privacy record (D-07), so under
# `first-token-owns-draw` a draw starting inside the replay prefix is owned by no fact. It is
# counted under this sentinel and reported as `replay_draws` ALONGSIDE the per-fact summary
# rather than folded into it: crediting it to a fact would inflate that fact, and dropping it
# would break the conservation law silently. 65535 is uint16's maximum and cannot collide with a
# fact index at any capacity this project will reach.
REPLAY_FACT_ID = 65535

# D-24's published n=8 table (`scripts/teach_persona.py:146-151`), to the 4 decimals it states.
# A MODULE CONSTANT so the value the artifact PUBLISHES and the value its reproduction flag is
# CHECKED AGAINST are one object. Two copies is how `n8_rows_reproduce_the_documented_table`
# became a hardcoded `True` that nothing evaluated (21-REVIEW.md WR-01).
DOCUMENTED_N8_TABLE = {"3": 0.4211, "4": 0.4923, "5": 0.5479}


def refuse_existing_artifacts(paths=None):
    """Refuse-to-rerun for the artifact paths — ``teach_persona.refuse_if_exists``, IMPORTED.

    The write path plan 21-11 fills in. The refusal is INHERITED rather than invented so there is
    one refuse-to-rerun implementation in the repository and not two: a recorded artifact silently
    replaced by a rerun on drifted code is the failure mode, and it is identical here and in
    ``teach_persona``.
    """
    return tp.refuse_if_exists([pathlib.Path(p) for p in (paths or ARTIFACTS.values())])


def is_publication_target(path):
    """Is ``path`` one of the two PERMANENT, committed records in :data:`ARTIFACTS`?

    Resolved before comparison, so a relative path, a symlinked route or a ``..`` detour to the
    same file all answer the same. The comparison is by RESOLVED PATH and never by name: a
    ``tmp_path/phase21_privacy_unit.json`` in a test shares the basename with the real record and
    must not be mistaken for it.
    """
    path = pathlib.Path(path).resolve()
    return any(path == artifact.resolve() for artifact in ARTIFACTS.values())


def refuse_dirty_publication(path):
    """Refuse to write a PUBLISHED record from a dirty tree. No-op for any other path.

    **Why this is scoped to the publication targets instead of firing on every call.** The defect
    CR-02 names is a false `provenance.git_sha` in a file that is COMMITTED and then quoted
    forever; nothing else this module writes survives the process that wrote it. Guarding every
    call would instead make `emit_privacy_unit(path=tmp_path/...)` — the write path
    ``tests/test_phase21_unit_record.py::test_driver_refuses_to_rerun`` exercises — fail whenever
    the working tree happened to be dirty, which is a test outcome that depends on git state
    rather than on code. A guard that turns the suite red during ordinary development is a guard
    that gets deleted.

    **Why it is HERE (and in `_write`) rather than at module scope, which is what 21-REVIEW.md
    CR-02 prescribed.** Mirroring `phase21_golden_capture.py`'s module-scope placement was tried
    first and MEASURED: `phase21_golden_capture` is imported by no test, so its import-time
    refusal costs the suite nothing, but this module is imported by
    `tests/test_phase21_unit_record.py:35` and `tests/test_phase21_multiplicity.py`. A
    `SystemExit` raised while pytest is COLLECTING is an `INTERNALERROR` that aborts the whole
    run, so the observed result was `no tests ran in 3.63s` for the ENTIRE 989-test suite on any
    tree with an uncommitted file under `scripts/` or `src/` — i.e. during every edit that would
    precede a re-emission. The module-scope site that CR-02 correctly asks for lives in
    `scripts/phase21_emit.py`, which nothing imports, and which runs its check BEFORE importing
    this module — a strictly stronger position than the top of this file, because it also covers
    this file's own import.
    """
    if not is_publication_target(path):
        return None
    return refuse_if_dirty(
        who="phase21_unit_record",
        detail=_DIRTY_DETAIL,
        pathspec=_PUBLICATION_PATHSPEC,
        cwd=_ROOT,
    )


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


# =================================================================================================
# THE MEASUREMENT. One corpus builder, shared by BOTH emitters, so the padded-bin share recorded in
# `phase21_privacy_unit.json` and the geometry recorded in `phase21_multiplicity.json` cannot be
# two numbers that disagree.
# =================================================================================================


def _per_fact_episodes(facts, second_person):
    """Each fact's rendered episodes, in the order the FLAT packer concatenates them.

    ``teach_persona.render_episodes`` flattens ``facts x sorted(family_ids)`` into one list, which
    is unusable as a fact map because the boundaries are gone. This regroups the identical cross
    product — and the regrouping is VERIFIED, not assumed: the caller asserts the flattened result
    is EQUAL to ``render_episodes``'s own output. Without that assertion the fact map would be a
    second implementation of the packer's ordering, free to drift from the bin it labels.

    ``forms`` is resolved from the WHOLE fact list via ``teach_persona._slot_forms_for``, never per
    fact. At n=64 a per-fact call would return ``None`` for the 8 locked facts and the widened
    union for the 56 filler ones — two different grammars inside one corpus.
    """
    forms = tp._slot_forms_for(facts)
    return [
        [
            episode
            for family_id in sorted(fs.TAUGHT_FAMILY_IDS)
            for episode in fs.render_family(
                family_id, fact, second_person=second_person, forms=forms
            )
        ]
        for fact in facts
    ]


def _write_fact_map(bin_path, fact_ids):
    """Write the third bin for a FLAT corpus, at the path ``fact_bin_path`` derives.

    The aligned packer writes its own fact bin; the flat one does not, because a flat bin has no
    privacy records — which is UNIT-01's whole complaint. The map is therefore synthesised HERE so
    the one counter can be pointed at both compositions, and it goes to the path
    ``teach_persona.fact_bin_path`` derives rather than to a literal, per that function's docstring.
    """
    path = tp.fact_bin_path(bin_path)
    np.asarray(fact_ids, dtype=np.uint16).tofile(path)
    return path


def _measure_capacity(tok, arm, workdir, *, with_replay_row):
    """Build every bin one capacity needs, under ``workdir``, and return the OBSERVED geometry.

    ``workdir`` is a temporary directory and never an ``arm_outputs`` path: those hold RECORDED
    evidence, and ``build_bins`` would happily overwrite them.

    Three corpora come out of one render:

    * ``facts_only`` — the flat v3.0 packing at ``replay_ratio = 0.0`` (D-10's composition), plus a
      synthesised fact map. This is what ``count_unaligned`` measures for the ``facts-only`` row.
    * ``aligned`` — the ragged fact-aligned packing (D-01/D-05), three bins written by
      ``_build_aligned_bins`` itself. This is the ``fact-aligned`` row AND the source of every
      ``corpus_geometry`` number.
    * ``replay`` — the flat packing at ``replay_ratio = 1.0`` on the LEGACY ``n_facts=None`` sizing,
      built only when ``with_replay_row`` is set. Deliberately the legacy branch: the row exists to
      characterise the OLD loader against the OLD bin, which is the comparison D-10's consequence
      is measured against.
    """
    facts, second_person, replay_ratio = tp.arm_spec(arm)
    if replay_ratio != 0.0:
        raise ValueError(
            f"{arm} declares replay_ratio={replay_ratio}; both DP arms must be 0.0 (D-10 puts "
            "replay outside the teaching bin), or the 'facts-only' row would not be facts only"
        )

    per_fact = _per_fact_episodes(facts, second_person)
    flat_episodes = [episode for episodes in per_fact for episode in episodes]
    if flat_episodes != tp.render_episodes(
        facts, fs.TAUGHT_FAMILY_IDS, second_person=second_person
    ):
        raise ValueError(
            "the per-fact regrouping does not flatten to teach_persona.render_episodes' own "
            "output — the fact map would be labelling a bin packed in a different order"
        )

    # Per-fact FLAT token lengths, from the real encoder one episode at a time — the same call
    # `build_bins` makes. Cross-checked against `teaching_tokens` below, so this is a measured
    # decomposition of the bin rather than a parallel implementation of it.
    per_fact_lengths = []
    for episodes in per_fact:
        total = 0
        for question, answer in episodes:
            ids, _mask = tp.encode_dialogue(tok, [], [(question, answer)])
            total += len(ids)
        per_fact_lengths.append(total)

    out = {
        "arm": arm,
        "facts": facts,
        "n_facts": len(facts),
        "second_person": second_person,
        "episodes": len(flat_episodes),
        "per_fact_lengths": per_fact_lengths,
        "teaching_tokens": sum(per_fact_lengths),
    }

    workdir = pathlib.Path(workdir)
    flat_map = [index for index, length in enumerate(per_fact_lengths) for _ in range(length)]

    facts_bin = workdir / f"{arm}_facts_only.bin"
    facts_mask = workdir / f"{arm}_facts_only_mask.bin"
    flat_stats = tp.build_bins(tok, flat_episodes, facts_bin, facts_mask, replay_ratio=0.0)
    if flat_stats["teaching_tokens"] != out["teaching_tokens"]:
        raise ValueError(
            f"the flat packer wrote {flat_stats['teaching_tokens']:,} teaching tokens but the "
            f"per-fact decomposition sums to {out['teaching_tokens']:,} — the fact map would "
            "mis-attribute every draw past the first divergence"
        )
    out["facts_only"] = {
        "bin": facts_bin,
        "mask": facts_mask,
        "fact": _write_fact_map(facts_bin, flat_map),
        "stats": flat_stats,
    }

    aligned_bin = workdir / f"{arm}_aligned.bin"
    aligned_mask = workdir / f"{arm}_aligned_mask.bin"
    aligned_stats = tp.build_bins(
        tok, [], aligned_bin, aligned_mask, align_facts=list(zip(facts, per_fact))
    )
    out["aligned"] = {
        "bin": aligned_bin,
        "mask": aligned_mask,
        "fact": tp.fact_bin_path(aligned_bin),
        "stats": aligned_stats,
    }

    if with_replay_row:
        replay_bin = workdir / f"{arm}_replay_in_bin.bin"
        replay_mask = workdir / f"{arm}_replay_in_bin_mask.bin"
        replay_stats = tp.build_bins(tok, flat_episodes, replay_bin, replay_mask, replay_ratio=1.0)
        # `_prepend_replay` INSERTS the replay slice at index 0, so replay is a PREFIX and every
        # fact's offset shifts by exactly `replay_tokens`.
        replay_map = [REPLAY_FACT_ID] * replay_stats["replay_tokens"] + flat_map
        out["replay"] = {
            "bin": replay_bin,
            "mask": replay_mask,
            "fact": _write_fact_map(replay_bin, replay_map),
            "stats": replay_stats,
        }
    return out


def _measure_all(workdir, *, with_aligned_rows=False):
    """Both capacities, one tokenizer load, one seeding. Returns ``{arm: measurement}``.

    ``with_aligned_rows`` runs ``count_aligned`` while the bins still exist. ``workdir`` is a
    temporary directory in both emitters' default path, so a caller that deferred the count until
    after the return would be pointing the loader at deleted files.
    """
    seed_everything(SEED)
    tok = from_json(tp.TOKENIZER_PATH)  # FROZEN production artifact — never retrain
    measurements = {
        arm: _measure_capacity(tok, arm, workdir, with_replay_row=(arm == "dp_n8"))
        for arm in CAPACITY_ARMS
    }
    if with_aligned_rows:
        for measurement in measurements.values():
            measurement["aligned_row"] = _aligned_row(measurement)
    return measurements


def _provenance(**extra):
    """``git_sha`` + wall clock + interpreter + the pin's digest, on every artifact.

    ``pin_sha256`` is read from the pin FILE rather than declared, so an artifact written against
    an edited pin carries a digest that does not match 21-01's recorded ``45f37e15…`` — visible in
    the record itself, independently of the git-ancestry guard.
    """
    pin = _ROOT / "scripts" / "mitigation_unit.py"
    record = {
        "git_sha": git_sha(),
        "written_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": platform.python_version(),
        "seed": SEED,
        "pin_module": "scripts/mitigation_unit.py",
        "pin_sha256": hashlib.sha256(pin.read_bytes()).hexdigest(),
        "epsilon_computed": False,
        "epsilon_note": (
            "NO EPSILON IS COMPUTED ANYWHERE IN PHASE 21. This artifact records the privacy UNIT "
            "and the data path that makes it real; the accountant that consumes them is Phase 22 "
            "(DPSGD-01). A number labelled epsilon here would be a bound with no mechanism behind "
            "it, which is precisely the substitution UNIT-03 exists to refuse."
        ),
    }
    record.update(extra)
    return record


def _write(path, document):
    """Refuse-to-rerun and refuse-if-dirty, then write. Both refusals are IMPORTED, not invented.

    Recorded evidence is never silently replaced by a rerun on drifted code, and the abort names
    the file and the delete command.

    **This is the root seam and that is why the dirty check is here.** Both emitters route their
    bytes through this one function, so a check here cannot be bypassed by calling
    ``emit_multiplicity`` directly, by importing ``multiplicity_document`` and writing the JSON by
    hand, or by any future third emitter. The emitters ALSO check before starting their
    measurement — not for safety but for courtesy, since discovering the refusal after building
    two corpora wastes the run — but this is the check that makes the property true.

    It runs AFTER the document is built, which is the point: the measurement takes minutes, and a
    tree that was clean when it started can be dirty by the time the bytes land. The recorded
    ``git_sha`` was captured inside that window by ``_provenance()``, so the tree must still be
    clean HERE for it to mean anything.
    """
    path = pathlib.Path(path)
    refuse_existing_artifacts([path])
    refuse_dirty_publication(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


# =================================================================================================
# ARTIFACT 1 — results/phase21_privacy_unit.json (SC1 / SC4; UNIT-01, UNIT-04, UNIT-05)
# =================================================================================================


def _lot_geometry(measurements):
    """The aligned bin's size at each capacity, in BOTH units, because they are not the same size.

    ``padded_tokens`` is the bin as WRITTEN — ``total_windows * block_size + 1``, where the ``+1``
    is the label-shift tail. ``trainable_tokens`` is ``total_windows * block_size``: the tail
    excluded.

    The distinction is the whole of 21-REVIEW.md WR-01 and it is not a rounding preference. See
    :func:`_share_of_the_combined_lot` for which one the published share divides by and the
    measurement that settles it.
    """
    return {
        m["n_facts"]: {
            "total_windows": int(m["aligned"]["stats"]["n_windows"]),
            "padded_tokens": int(m["aligned"]["stats"]["tokens"]),
            "trainable_tokens": int(m["aligned"]["stats"]["n_windows"]) * BLOCK_SIZE,
        }
        for m in measurements.values()
    }


def _share_of_the_combined_lot(replay_tokens, geo):
    """THE one derivation of "what fraction of one lot is public replay". Both callers use it.

    ``replay_tokens / (replay_tokens + trainable_tokens)`` — the LABEL-SHIFT TAIL EXCLUDED from
    the denominator.

    **WHY THE TAIL IS EXCLUDED, MEASURED RATHER THAN ARGUED (21-REVIEW.md WR-01).** The review
    found ``n8_rows_reproduce_the_documented_table`` published as a hardcoded ``True`` that was
    false at the precision it claimed: the 3-window row measured 0.4210 against D-24's documented
    0.4211. It traced the cause correctly to a denominator disagreement — D-24 divided by 8448,
    the artifact by 8449 — but a disagreement is not yet an answer, and "whichever makes the flag
    True" is not a reason. The deciding test is UNIT INVARIANCE:

        a share is a share only if it does not depend on whether you count in windows or tokens

    The numerator is ``REPLAY_WINDOWS_PER_FACT * n_facts * block_size``, a whole number of windows
    with remainder exactly 0 (``replay_window_budget(8) % 256 == 0``, measured). So the same
    quantity is computable in either unit, and it must come out the same. Observed at n=8, w=3:

        windows          24 / (24 + 33)       = 0.4210526315789473
        tokens / 8448  6144 / (6144 + 8448)   = 0.4210526315789473   <- identical, bit for bit
        tokens / 8449  6144 / (6144 + 8449)   = 0.4210237785239498   <- disagrees

    Only ``total_windows * block_size`` is unit-invariant. 8449 is not a "share of the lot" in any
    consistent unit: it compares a tail-free numerator against a tail-bearing denominator. The
    ``+1`` token is a TARGET-ONLY position — it is never a window start, so it belongs to no
    window and cannot appear in a window-basis count at all.

    **This is not a denominator tuned to make a flag come out True, and the check that it isn't is
    that the flag it does NOT rescue stays false.** ``documented_n64_claim_holds`` is the
    load-bearing claim in this block, and the correction moves the n=64 share from 44.7549% to
    44.7552% — against a documented 49.90%. It was false before and it is false after. What the
    correction does change is that the linear premise's own prediction becomes EXACT: at 8448 the
    n=64 share under linear scaling is 0.49230769230769234, bit-identical to n=8, where at 8449 it
    was 49.2278% — "almost unchanged" only because the tail broke the arithmetic.

    **D-24 IS NOT REOPENED.** ``REPLAY_WINDOWS_PER_FACT = 4`` is a locked decision pinned by
    ``tests/test_phase21_replay_volume.py``. What this settles is which denominator D-24's own
    table was computed under — and the answer is that D-24 was right and the artifact was wrong.
    Both numbers are published side by side in every row regardless, so a reader can recompute.
    """
    return replay_tokens / (replay_tokens + geo["trainable_tokens"])


def _d24_candidate_table(geometry):
    """D-24's 3/4/5-window candidate table, RECOMPUTED at both capacities on the observed bins.

    Two things at once, and the second is the finding:

    1. **A validation of this measurement against a documented one.** The three n=8 rows of the
       table at ``scripts/teach_persona.py:146-151`` (42.11% / 49.23% / 54.79%) are compared
       against the shares computed here from the OBSERVED bin, to the 4 decimals the comment
       states. ``n8_rows_reproduce_the_documented_table`` is the RESULT of that comparison —
       :data:`DOCUMENTED_N8_TABLE` is the same object the artifact publishes, so the claim and the
       check cannot be two numbers. It was a hardcoded ``True`` that nothing evaluated until
       21-REVIEW.md WR-01, and it was FALSE: the 3-window row measured 0.4210 against 0.4211
       because the artifact divided by the tail-bearing 8449 where D-24 divided by 8448. See
       :func:`_share_of_the_combined_lot` for the unit-invariance measurement that settles which
       denominator the quantity has, and for why the answer is not "the one that makes this True".

    2. **The n=64 half of that comment is FALSE, and it is recorded rather than smoothed.**
       ``teach_persona.py:162-163`` states *"The share holds across capacities for free: 49.90% at
       n=64, because both sides scale with ``n_facts``."* Both sides do NOT scale with
       ``n_facts``. Replay does, exactly (``4 * n_facts * block_size``); the teaching bin does
       not, because the 56 filler facts pack to ~5.05 windows each against the 8 locked facts'
       4.125. This survives the denominator correction unchanged — which is the evidence that the
       correction was not made to flatter the record: it rescues nothing that was failing.

    **This does NOT reopen D-24.** ``REPLAY_WINDOWS_PER_FACT = 4`` is a locked decision pinned by
    ``tests/test_phase21_replay_volume.py``, it was chosen on the n=8 table, and that table is
    exactly reproduced. What is corrected is a stated CONSEQUENCE of the choice at the other
    capacity — recorded here because the same table's own "closest to 50%" criterion ranks the
    candidates differently at n=64 than at n=8, and a reader who quotes 49.90% is quoting a
    number no bin produces.

    Every row carries BOTH bin sizes, so a reader who disagrees with the choice can recompute the
    other share without re-running the measurement.
    """
    n8, n64 = geometry[8], geometry[64]
    documented_n64 = 0.4990
    filler_facts = 64 - 8
    filler_windows = n64["total_windows"] - n8["total_windows"]
    linear_n64_trainable = 8 * n8["trainable_tokens"]
    linear_n64_share = tp.replay_window_budget(64) / (
        tp.replay_window_budget(64) + linear_n64_trainable
    )
    n8_share = _share_of_the_combined_lot(tp.replay_window_budget(8), n8)
    n64_share = _share_of_the_combined_lot(tp.replay_window_budget(64), n64)
    n64_at_5 = _share_of_the_combined_lot(5 * 64 * BLOCK_SIZE, n64)
    # The share the OLD (tail-bearing) denominator gave, kept only to publish how little the
    # correction moved the claim it does not rescue.
    n64_at_4 = tp.replay_window_budget(64)
    n64_share_with_tail = n64_at_4 / (n64_at_4 + n64["padded_tokens"])
    return {
        "criterion": (
            "share of the combined lot = replay_tokens / (replay_tokens + "
            "aligned_teaching_bin_trainable_tokens)"
        ),
        "rows": [
            {
                "windows_per_fact": w,
                "n_facts": n,
                "replay_tokens": w * n * BLOCK_SIZE,
                "replay_windows": w * n,
                "aligned_teaching_bin_tokens_padded": geometry[n]["padded_tokens"],
                "aligned_teaching_bin_trainable_tokens": geometry[n]["trainable_tokens"],
                "aligned_teaching_bin_windows": geometry[n]["total_windows"],
                "share_of_the_combined_lot": _share_of_the_combined_lot(
                    w * n * BLOCK_SIZE, geometry[n]
                ),
                "share_computed_in_windows": (w * n) / (w * n + geometry[n]["total_windows"]),
                "is_the_pinned_constant": w == tp.REPLAY_WINDOWS_PER_FACT,
            }
            for w in (3, 4, 5)
            for n in sorted(geometry)
        ],
        # COMPUTED, not asserted (WR-01). `DOCUMENTED_N8_TABLE` is the object published below.
        "n8_rows_reproduce_the_documented_table": all(
            round(_share_of_the_combined_lot(w * 8 * BLOCK_SIZE, n8), 4)
            == DOCUMENTED_N8_TABLE[str(w)]
            for w in (3, 4, 5)
        ),
        "n8_rows_reproduce_the_documented_table_tolerance": (
            "round(share, 4) == the documented value EXACTLY — the comment states 4 decimals, so "
            "the comparison is made at 4 decimals and at no other precision"
        ),
        "documented_n8_table": DOCUMENTED_N8_TABLE,
        "denominator_reconciliation": {
            "disagreement": (
                "D-24's table divides by 8448 at n=8; this artifact divided by 8449 until "
                "21-REVIEW.md WR-01. They differ by the LABEL-SHIFT TAIL, the trailing +1 token "
                "of an aligned bin (total_windows * block_size + 1), and the difference is "
                "visible only in the 3-window row's 4th decimal: 0.4211 vs 0.4210."
            ),
            "resolved_in_favour_of": "D-24 (the tail EXCLUDED — trainable_tokens)",
            "resolved_by": (
                "UNIT INVARIANCE, measured. The numerator is a whole number of windows "
                "(replay_window_budget(n) % block_size == 0), so the share must be computable in "
                "windows or in tokens and come out the same. It does, bit for bit, only when the "
                "denominator is total_windows * block_size. Every row publishes both "
                "share_of_the_combined_lot and share_computed_in_windows so this is checkable "
                "from the artifact alone."
            ),
            "why_the_tail_is_not_part_of_the_lot": (
                "The +1 token is a TARGET-ONLY position: it is the label for the last window's "
                "final input token and is never itself a window start. It belongs to no window, "
                "so it cannot appear in a window-basis count, and a token-basis count that "
                "includes it is measuring a different thing from the one it is compared against."
            ),
            "what_the_correction_does_not_rescue": (
                f"documented_n64_claim_holds is still False: the corrected n=64 share is "
                f"{n64_share:.6%} against the documented 49.90%, where the old tail-bearing "
                f"denominator gave {n64_share_with_tail:.6%}. The correction moves it by "
                f"{abs(n64_share - n64_share_with_tail):.2e} and leaves the claim just as false. "
                "A denominator chosen to flatter the record would have rescued the claim this "
                "block is actually about; this one does not touch it."
            ),
        },
        "documented_n64_claim": (
            "scripts/teach_persona.py:162-163 — 'The share holds across capacities for free: "
            "49.90% at n=64, because both sides scale with n_facts.'"
        ),
        "documented_n64_claim_value": documented_n64,
        "documented_n64_claim_holds": round(n64_share, 4) == documented_n64,
        "measured_n64_share_at_the_pinned_constant": n64_share,
        "why_the_premise_fails": (
            f"Replay scales exactly with n_facts; the TEACHING BIN does not. The {filler_facts} "
            f"filler facts pack to {filler_windows} of the {n64['total_windows']} ragged windows "
            f"({filler_windows / filler_facts:.3f} each) against the 8 locked facts' "
            f"{n8['total_windows']} ({n8['total_windows'] / 8:.3f} each), so the n=64 bin is "
            f"{n64['trainable_tokens']:,} trainable tokens where linear scaling from n=8 predicts "
            f"8 x {n8['trainable_tokens']:,} = {linear_n64_trainable:,}. Under the linear premise "
            f"the share would be {linear_n64_share:.4%} — i.e. EXACTLY the n=8 value of "
            f"{n8_share:.4%}, not the 49.90% stated — so the documented figure does not follow "
            "from its own stated reason either."
        ),
        "linear_premise_share_at_n64": linear_n64_share,
        "linear_premise_equals_the_n8_share": linear_n64_share == n8_share,
        "consequence_recorded_not_acted_on": (
            f"At n=64 the table's own 'closest to 50%' criterion ranks 5 windows "
            f"({n64_at_5:.2%}) ahead of the pinned 4 ({n64_share:.2%}). D-24 is a LOCKED decision "
            "taken on the n=8 geometry and REPLAY_WINDOWS_PER_FACT is pinned by test; this "
            "artifact RECORDS the divergence and changes nothing. Re-opening it would be a dated "
            "continuation, not an edit."
        ),
    }


def privacy_unit_document(measurements):
    """SC1 + SC4's record, every pinned value COMPUTED from :mod:`mitigation_unit` at write time."""
    geometry = _lot_geometry(measurements)
    replay_share = {}
    for n_facts, geo in geometry.items():
        volume = tp.replay_window_budget(n_facts)
        replay_share[n_facts] = {
            "n_facts": n_facts,
            "replay_tokens": volume,
            "replay_windows": volume // BLOCK_SIZE,
            "aligned_teaching_bin_tokens_padded": geo["padded_tokens"],
            "aligned_teaching_bin_trainable_tokens": geo["trainable_tokens"],
            "aligned_teaching_bin_windows": geo["total_windows"],
            # THE SAME derivation the candidate table's `is_the_pinned_constant` row uses. This
            # value and that one are the same quantity, so they come from one function: computing
            # a number twice in one artifact is how the artifact acquires two answers.
            "share_of_the_combined_lot": _share_of_the_combined_lot(volume, geo),
            "denominator": "replay_tokens + aligned_teaching_bin_trainable_tokens",
            "denominator_excludes": (
                "the LABEL-SHIFT TAIL (the trailing +1 token). Both bin sizes are published above "
                "— see d24_candidate_table_reproduced.denominator_reconciliation for the "
                "unit-invariance measurement that chooses between them (21-REVIEW.md WR-01)."
            ),
        }

    return {
        "unit": {
            "privacy_unit": mu.PRIVACY_UNIT,
            "privacy_n_rule": "N = n_facts",
            "rationale": (
                "An example-level epsilon bounds nothing about a FACT. "
                "`get_batch_memmap_masked` (src/personacore/training/data.py:117) draws "
                "`batch_size` window START OFFSETS with `np.random.randint` over a FLAT "
                "CONCATENATED bin — with replacement, and with no notion of where one fact ends "
                "and the next begins — so a single fact is touched an unbounded number of times "
                "per pass and `one example` is not a stable quantity to protect."
            ),
            "measured_multiplicity": (
                "NOT restated here. The OBSERVED per-fact distribution (min/max/mean/spread, "
                "every row labelled with its bin composition and carrying its own denominator) "
                "is in results/phase21_multiplicity.json. A number appearing in two artifacts is "
                "two numbers that can disagree."
            ),
            "pin_arithmetic": mu.PRIVACY_UNIT_ARITHMETIC,
        },
        "lot": {
            "sampling_rate_q": mu.SAMPLING_RATE_Q,
            "privacy_n_rule": "N = n_facts",
            "privacy_n_at_capacities": {n: mu.privacy_n(n) for n in (8, 64)},
            "replay_in_lot": True,
            "replay_inside_privacy_n": False,
            "epsilon_consequence": mu.REPLAY_OUTSIDE_N,
            "replay_volume": {
                "replay_windows_per_fact": tp.REPLAY_WINDOWS_PER_FACT,
                "replay_tokens_per_fact": tp.REPLAY_WINDOWS_PER_FACT * BLOCK_SIZE,
                "replay_tokens_at_n8": tp.replay_window_budget(8),
                "replay_tokens_at_n64": tp.replay_window_budget(64),
                "observed_share_of_the_padded_bin": list(replay_share.values()),
                "d24_candidate_table_reproduced": _d24_candidate_table(geometry),
                "separate_pass_per_lot": True,
                "rejected_raw_constant": 947.625,
                "rejected_raw_constant_reason": (
                    "7581 / 8 — read off PRIVATE token lengths. A replay volume derived from the "
                    "corpus is a side channel: it publishes a function of the facts it is meant "
                    "to be independent of (D-11 / D-24)."
                ),
            },
        },
        "delta": {
            "delta": mu.DELTA,
            "ceiling": mu.DELTA_TIMES_N_CEILING,
            "ceiling_rule": "delta * N < ceiling",
            "rejected_recipe": mu.REJECTED_DELTA_RECIPE,
            "rejected_recipe_reason": mu.REJECTED_DELTA_REASON,
            "capacities": [
                {
                    "n": mu.privacy_n(n),
                    "pinned_delta_times_n": mu.DELTA * n,
                    "pinned_margin": mu.DELTA_TIMES_N_CEILING / (mu.DELTA * n),
                    "rejected_delta": mu.rejected_delta(n),
                    "rejected_delta_times_n": mu.rejected_delta(n) * n,
                    "rejected_overshoot_multiple": (
                        mu.rejected_delta(n) * n / mu.DELTA_TIMES_N_CEILING
                    ),
                }
                for n in (8, 64)
            ],
        },
        "provenance": _provenance(),
    }


def emit_privacy_unit(path=None, workdir=None):
    """Write ``results/phase21_privacy_unit.json``. Refuses to overwrite an existing record.

    ``workdir`` is only used for the OBSERVED padded-bin share in the ``lot`` block — the one
    number here that is a measurement rather than a pinned value. It defaults to a temporary
    directory, which is deleted on return.
    """
    path = pathlib.Path(path or ARTIFACTS["privacy_unit"])
    # Refuse BEFORE spending the measurement, as well as inside `_write` — a driver that builds
    # two corpora and only then discovers it may not write has wasted the run for nothing.
    refuse_existing_artifacts([path])
    refuse_dirty_publication(path)
    if workdir is None:
        with tempfile.TemporaryDirectory() as tmp:
            document = privacy_unit_document(_measure_all(tmp))
    else:
        document = privacy_unit_document(_measure_all(workdir))
    _write(path, document)
    return document


# =================================================================================================
# ARTIFACT 2 — results/phase21_multiplicity.json (SC3 / UNIT-03, D-26)
# =================================================================================================


def _analytic_expectations(*, total_draws, mean_fact_length, bin_tokens):
    """BOTH rules' closed forms, each NAMED, computed from the observed geometry at write time.

    UNIT-03 refuses an analytic number AS the measurement, so these travel in a separately named
    field BESIDE the measured value and never in place of it (T-21-51). Both rules appear because
    the frozen pin's ``262.94`` is the OVERLAP rule's figure while every row here is counted under
    ``first-token-owns-draw`` — publishing one without the other is exactly how a reader ends up
    comparing two quantities that answer different questions.
    """
    support = bin_tokens - BLOCK_SIZE - 1
    return {
        "labelled": "ANALYTIC — an expectation over the draw distribution, NOT a measurement",
        "draw_start_offsets": support,
        "draw_start_offsets_formula": "bin_tokens - block_size - 1",
        "mean_fact_length": mean_fact_length,
        "first_token_rule": total_draws * mean_fact_length / support,
        "overlap_rule": total_draws * (mean_fact_length + BLOCK_SIZE) / support,
        "rule_this_row_was_counted_under": ATTRIBUTION_RULE,
        "which_one_matches_this_row": "first_token_rule",
        "gap_between_the_two_rules": total_draws * BLOCK_SIZE / support,
        "note": (
            "`first_token_rule` is the closed form for THIS row's attribution rule. "
            "`overlap_rule` is the REJECTED rule's closed form and is the quantity "
            "scripts/mitigation_unit.py's PRIVACY_UNIT_ARITHMETIC computes. They differ by "
            "total_draws * block_size / draw_start_offsets per fact. Neither is wrong; a row "
            "that does not name its rule is unreadable."
        ),
    }


def _split_replay_sentinel(row):
    """Move the replay sentinel's draws OUT of the per-fact summary, keeping BOTH denominators.

    On the ``replay-in-bin @1.0`` composition a draw whose first token is a replay token is owned
    by NO privacy record. Two wrong answers were available and both are refused: crediting those
    draws to a fact inflates that fact, and dropping them breaks the conservation law silently.
    The sentinel is therefore removed from ``counts``, ``min``/``max``/``mean``/``spread`` are
    recomputed over the facts ALONE, and the removed total is published as ``replay_draws`` with
    the exact conservation law it satisfies. That is the number the row is really about: it is how
    much of the budget bought no teaching at all.
    """
    counts = {key: value for key, value in row["counts"].items() if key != REPLAY_FACT_ID}
    replay_draws = row["counts"].get(REPLAY_FACT_ID, 0)
    row = dict(row)
    row["counts"] = counts
    row["n_facts"] = len(counts)
    row.update(_summarise(counts))
    row["replay_fact_id"] = REPLAY_FACT_ID
    row["replay_draws"] = replay_draws
    row["draws_landing_on_a_fact"] = sum(counts.values())
    row["conservation"] = "draws_landing_on_a_fact + replay_draws == total_draws"
    if row["draws_landing_on_a_fact"] + replay_draws != row["total_draws"]:
        raise ValueError(
            f"{row['draws_landing_on_a_fact']} fact draws + {replay_draws} replay draws != "
            f"{row['total_draws']} total draws — a draw was lost or double-counted"
        )
    return row


def _unaligned_row(corpus, measurement, *, bin_composition, extra=None):
    """One ``count_unaligned`` row at the D-26 budget, with its analytic expectation attached."""
    row = count_unaligned(
        corpus["bin"],
        corpus["mask"],
        corpus["fact"],
        steps=MAX_STEPS,
        batch_size=BATCH_SIZE,
        seed=SEED,
        block_size=BLOCK_SIZE,
        bin_composition=bin_composition,
    )
    if extra == "replay":
        row = _split_replay_sentinel(row)
    row["analytic_expectation"] = _analytic_expectations(
        total_draws=row["total_draws"],
        mean_fact_length=measurement["teaching_tokens"] / measurement["n_facts"],
        bin_tokens=row["bin_tokens"],
    )
    row["conservation_pinned_mean"] = row["total_draws"] / measurement["n_facts"]
    return row


def _aligned_row(measurement):
    """The fact-aligned row: ONE FULL LOT, so ``steps == n_facts`` and every count must be 1.

    One lot is the unit of the aligned accounting — ``grad_accum_steps = n_facts`` (SC2) — so the
    per-fact multiplicity this row reports is exactly what one privacy record contributes to one
    optimiser step. Counting a longer run would multiply every entry by the number of lots and say
    nothing new: the aligned draw is DETERMINISTIC, so at any multiple of ``n_facts`` the counts
    are exactly ``steps / n_facts`` with ``spread == 0``.

    ``count_aligned`` runs at its ``strict=True`` DEFAULT. A mis-built bin must abort rather than
    quietly produce a published row (T-21-63).
    """
    corpus = measurement["aligned"]
    n_facts = measurement["n_facts"]
    row = count_aligned(
        corpus["bin"],
        corpus["mask"],
        corpus["fact"],
        steps=n_facts,
        n_facts=n_facts,
        block_size=BLOCK_SIZE,
        bin_composition=BIN_COMPOSITION_LABELS[2],
    )
    row["lot_length_steps"] = n_facts
    row["analytic_expectation"] = {
        "labelled": "ANALYTIC — exactly 1 per micro-step, DETERMINISTIC, by construction",
        "first_token_rule": 1.0,
        "overlap_rule": 1.0,
        "rule_this_row_was_counted_under": ATTRIBUTION_RULE,
        "which_one_matches_this_row": "both",
        "note": (
            "The two attribution rules COINCIDE on an aligned bin: a block_size-aligned window "
            "overlaps exactly one fact, which SC2's input-space purity proof establishes at build "
            "time. The measured value is still reported from a counter proven able to report "
            "otherwise — plan 21-10 observed per_step_distinct_facts == 2 on a rolled bin."
        ),
    }
    return row


def _corpus_geometry(measurement):
    """The OBSERVED ragged geometry for one capacity — this is what discharges A3.

    ``21-RESEARCH.md`` assumption A3 estimated the n=64 corpus at ~264 windows from "56 filler
    facts at ~4 windows each", and marked it ``[ASSUMED — depends on values not yet minted]``. It
    is not adjusted to fit here and the corpus is not adjusted to hit it: the observed total is
    published and the divergence is stated.

    ``grad_accum_steps`` is ASSERTED equal to the OBSERVED micro-step count of one full lot, not
    declared equal to ``n_facts``. SC2's claim is that one micro-step is one privacy record; a
    declared value would restate the claim instead of checking it.
    """
    stats = measurement["aligned"]["stats"]
    aligned_row = measurement["aligned_row"]
    n_facts = measurement["n_facts"]

    observed_records = [fact for fact, count in aligned_row["counts"].items() if count > 0]
    micro_steps = sum(aligned_row["counts"].values())
    if not (len(observed_records) == micro_steps == n_facts):
        raise ValueError(
            f"one lot produced {micro_steps} micro-step(s) over {len(observed_records)} distinct "
            f"privacy record(s) against n_facts = {n_facts} — grad_accum_steps = n_facts is not "
            "true of this bin, so SC2 would be a declaration rather than a measurement"
        )

    windows_per_fact = list(stats["windows_per_fact"])
    total_tokens = int(stats["tokens"])
    return {
        "n_facts": n_facts,
        "arm": measurement["arm"],
        "episodes": measurement["episodes"],
        "windows_per_fact": windows_per_fact,
        "total_windows": int(stats["n_windows"]),
        "total_tokens": total_tokens,
        "total_tokens_formula": "total_windows * block_size + 1 (the label-shift tail)",
        "teaching_tokens": measurement["teaching_tokens"],
        "pad_tokens": int(stats["pad_tokens"]),
        "pad_fraction": stats["pad_tokens"] / total_tokens,
        "pad_fraction_denominator": "total_tokens (padded, including the label-shift tail)",
        "per_fact_token_lengths": measurement["per_fact_lengths"],
        "per_fact_token_min": min(measurement["per_fact_lengths"]),
        "per_fact_token_max": max(measurement["per_fact_lengths"]),
        "grad_accum_steps": micro_steps,
        "grad_accum_steps_source": (
            "OBSERVED: the number of micro-steps one full lot of get_batch_fact_aligned produced, "
            "asserted equal to len(distinct fact indices the loader returned) and to n_facts"
        ),
        "replay_windows_per_lot": tp.replay_window_budget(n_facts) // BLOCK_SIZE,
        "replay_tokens_per_lot": tp.replay_window_budget(n_facts),
    }


def multiplicity_document(measurements):
    """SC3's labelled measured rows, the observed geometry at both capacities, and the findings."""
    n8, n64 = measurements["dp_n8"], measurements["dp_n64"]

    rows = [
        _unaligned_row(n8["replay"], n8, bin_composition=BIN_COMPOSITION_LABELS[0], extra="replay"),
        _unaligned_row(n8["facts_only"], n8, bin_composition=BIN_COMPOSITION_LABELS[1]),
        n8["aligned_row"],
        _unaligned_row(n64["facts_only"], n64, bin_composition=BIN_COMPOSITION_LABELS[1]),
        n64["aligned_row"],
    ]

    geometry = [_corpus_geometry(n8), _corpus_geometry(n64)]
    a3 = _discharge_a3(geometry)

    replay_row, facts_row = rows[0], rows[1]
    return {
        "budget": {
            "seed": SEED,
            "max_steps": MAX_STEPS,
            "batch_size": BATCH_SIZE,
            "block_size": BLOCK_SIZE,
            "total_draws_unaligned": MAX_STEPS * BATCH_SIZE,
            "attribution_rule": ATTRIBUTION_RULE,
            "attribution_rule_note": (
                "Under first-token-owns-draw the conservation law is an EXACT EQUALITY, so the "
                "per-fact MEAN is pinned at total_draws / n_facts by arithmetic and carries no "
                "information about the corpus. Everything this measurement says lives in "
                "min / max / spread — which is why D-26 asks for those and not an expectation."
            ),
            "device": _DEVICE,
        },
        "rows": rows,
        "corpus_geometry": geometry,
        "a3_discharge": a3,
        "pin_discrepancy": _pin_discrepancy(n8),
        "findings": _findings(replay_row, facts_row, n8, geometry),
        "provenance": _provenance(row_schema=list(ROW_SCHEMA) + ["analytic_expectation"]),
    }


def _discharge_a3(geometry):
    """``21-RESEARCH.md`` A3, replaced by a measurement — the assumed number is NOT back-fitted."""
    n8, n64 = geometry[0], geometry[1]
    filler_windows = n64["total_windows"] - n8["total_windows"]
    filler_facts = n64["n_facts"] - n8["n_facts"]
    return {
        "assumption": (
            "21-RESEARCH.md A3 [ASSUMED — depends on values not yet minted]: the 56 filler facts "
            "were assumed to render ~22 rows / ~4 windows each, giving n=64 ~= 264 windows."
        ),
        "assumed_total_windows": 264,
        "observed_total_windows": n64["total_windows"],
        "holds": n64["total_windows"] == 264,
        "divergence_windows": n64["total_windows"] - 264,
        "divergence_fraction": (n64["total_windows"] - 264) / 264,
        "why": (
            f"The 8 locked facts pack to {n8['total_windows']} windows "
            f"({n8['total_windows'] / n8['n_facts']:.3f} per fact) and the {filler_facts} filler "
            f"facts to {filler_windows} ({filler_windows / filler_facts:.3f} per fact). The "
            "filler facts are LONGER than the locked ones, so the ~4-windows-each estimate "
            "under-counts them. The corpus was NOT adjusted to reach 264; the measurement is "
            "published as taken."
        ),
        "observed_filler_windows": filler_windows,
        "observed_filler_windows_per_fact": filler_windows / filler_facts,
        "observed_locked_windows_per_fact": n8["total_windows"] / n8["n_facts"],
    }


def _pin_discrepancy(n8):
    """The 262.9437-vs-207.018 finding, RECORDED with both numbers and their reconciliation.

    Plan 21-10 measured that ``scripts/mitigation_unit.py``'s ``262.9437`` is the OVERLAP rule's
    figure — the alternative the pinned ``ATTRIBUTION_RULE`` explicitly rejects. Neither number is
    wrong; they answer different questions and they reconcile exactly.

    **The pin is NOT edited to settle this.** ``scripts/mitigation_unit.py`` is frozen from the
    first ``results/phase21_*`` commit onward; editing a closed pre-registration permanently
    reddens the ancestry guard and a delete-and-re-add cannot launder it (``adds[-1]``, measured on
    a real cycle by plan 21-03). A correction to the pin is a DATED CONTINUATION via
    ``scripts/_addendum.py``, which is not this plan. The artifact's duty is to RECORD the
    discrepancy so nobody quotes 262.9437 as this rule's measurement.
    """
    n_facts = n8["n_facts"]
    mean_length = n8["teaching_tokens"] / n_facts
    bin_tokens = n8["teaching_tokens"]
    support = bin_tokens - BLOCK_SIZE - 1
    total_draws = MAX_STEPS * BATCH_SIZE
    overlap = total_draws * (mean_length + BLOCK_SIZE) / support
    first_token = total_draws * mean_length / support
    return {
        "status": "RECORDED, NOT RESOLVED — the pin is frozen and is not edited",
        "pin_module": "scripts/mitigation_unit.py",
        "pin_figure": overlap,
        "pin_figure_rule": "overlap (credit every fact the window touches) — the REJECTED rule",
        "pin_formula": (
            f"{total_draws} * ({mean_length} + {BLOCK_SIZE}) / "
            f"({bin_tokens} - {BLOCK_SIZE} - 1) = {overlap}"
        ),
        "artifact_rule": ATTRIBUTION_RULE,
        "artifact_rule_figure": first_token,
        "artifact_rule_formula": (
            f"{total_draws} * {mean_length} / ({bin_tokens} - {BLOCK_SIZE} - 1) = {first_token}"
        ),
        "gap_per_interior_fact": total_draws * BLOCK_SIZE / support,
        "reconciliation": (
            f"{overlap} - {total_draws} * {BLOCK_SIZE} / {support} = {first_token}. The two "
            "figures reconcile EXACTLY, so neither is wrong — they answer different questions."
        ),
        "conservation_pinned_mean": total_draws / n_facts,
        "conservation_pinned_mean_note": (
            f"Under the pinned rule the per-fact mean is {total_draws} / {n_facts} = "
            f"{total_draws / n_facts} BY ARITHMETIC. Publishing it would restate the budget, not "
            "the corpus. The measurement is in min / max / spread."
        ),
        "how_a_correction_would_be_made": (
            "scripts/_addendum.py — a dated continuation. NEVER an edit to scripts/"
            "mitigation_unit.py: from the first results/phase21_* commit that file is frozen, and "
            "tests/test_phase20_prereg.py:157 takes adds[-1] so a delete-and-re-add cannot "
            "launder a wrong ordering (measured on a real cycle by plan 21-03)."
        ),
    }


def _findings(replay_row, facts_row, n8, geometry):
    """The two results that appear in no source document and should survive into the report."""
    lengths = n8["per_fact_lengths"]
    return {
        "d10_doubles_the_unaligned_multiplicity": {
            "claim": (
                "Moving replay OUT of the teaching bin (D-10) roughly DOUBLES the old path's "
                "per-fact multiplicity, because the same 1,600 draws now land on half as much "
                "data. A decision taken purely for honest accounting made the UNALIGNED number "
                "WORSE — which STRENGTHENS UNIT-01's indictment rather than weakening it, and "
                "only shows up because BOTH numbers were measured instead of one."
            ),
            "replay_in_bin": {
                "bin_composition": replay_row["bin_composition"],
                "bin_tokens": replay_row["bin_tokens"],
                "mean_over_facts": replay_row["mean"],
                "min": replay_row["min"],
                "max": replay_row["max"],
                "spread": replay_row["spread"],
                "replay_draws": replay_row["replay_draws"],
                "draws_landing_on_a_fact": replay_row["draws_landing_on_a_fact"],
                "total_draws": replay_row["total_draws"],
            },
            "facts_only": {
                "bin_composition": facts_row["bin_composition"],
                "bin_tokens": facts_row["bin_tokens"],
                "mean_over_facts": facts_row["mean"],
                "min": facts_row["min"],
                "max": facts_row["max"],
                "spread": facts_row["spread"],
                "total_draws": facts_row["total_draws"],
            },
            "ratio_of_the_means": facts_row["mean"] / replay_row["mean"],
            "ratio_denominator": "facts-only mean / replay-in-bin mean, over the SAME 8 facts",
            "second_reading": (
                "The replay-in-bin row's other number is the sharper one: "
                f"{replay_row['replay_draws']} of {replay_row['total_draws']} draws "
                f"({replay_row['replay_draws'] / replay_row['total_draws']:.1%}) started inside "
                "the public replay prefix and bought NO teaching at all. Under an example-level "
                "accounting those draws are indistinguishable from the ones that touched a fact."
            ),
        },
        "d11_teaching_tokens_side_channel": {
            "channel": (
                "The v3.0 replay sizing is round(replay_ratio * teaching_tokens), and "
                "teaching_tokens is the sum of the FACTS' OWN token lengths. The volume of "
                "'public' data in the lot was therefore a function of PRIVATE content, which "
                "breaks the un-clipped public-gradient argument: the public term stops being "
                "independent of the private records."
            ),
            "what_made_it_measurable": (
                "The per-fact token lengths are not uniform. Observed across the 8 locked facts: "
                f"min {min(lengths)}, max {max(lengths)}, spread {max(lengths) - min(lengths)} "
                f"tokens over a total of {sum(lengths)}. A corpus whose facts all packed to the "
                "same length would leak nothing through this channel and the defect would have "
                "been invisible."
            ),
            "per_fact_token_lengths": lengths,
            "closure": (
                "D-24: replay_window_budget(n_facts) = REPLAY_WINDOWS_PER_FACT * n_facts * "
                "block_size. Every factor is public BY DERIVATION — 4 is a small integer authored "
                "before any fact existed, n_facts is a COUNT of records, block_size is a model "
                "hyperparameter. replay_ratio and teaching_tokens are IGNORED ENTIRELY on that "
                "branch, and the closure is proven by a DIFFERENTIAL (vary the fact VALUES at "
                "fixed n_facts, observe the volume unchanged) rather than by a constant assertion "
                "that would pass whenever the corpus happened to land on the same number."
            ),
            "closure_is_watched": (
                "tests/test_phase21_replay_volume.py — the LEGACY n_facts=None branch is retained "
                "deliberately so test_side_channel_negative_control has a live positive control "
                "proving the differential can see a side channel at all."
            ),
            "replay_windows_per_lot_observed": {
                geo["n_facts"]: geo["replay_windows_per_lot"] for geo in geometry
            },
        },
    }


def emit_multiplicity(path=None, workdir=None):
    """Measure both paths at both capacities and write ``results/phase21_multiplicity.json``.

    Bins are built under a temporary directory, never at an ``arm_outputs`` path, so no recorded
    arm evidence is touched. ``git status --porcelain data/`` is empty after this runs.
    """
    path = pathlib.Path(path or ARTIFACTS["multiplicity"])
    refuse_existing_artifacts([path])
    refuse_dirty_publication(path)
    if workdir is None:
        with tempfile.TemporaryDirectory() as tmp:
            document = multiplicity_document(_measure_all(tmp, with_aligned_rows=True))
    else:
        document = multiplicity_document(_measure_all(workdir, with_aligned_rows=True))
    _write(path, document)
    return document
