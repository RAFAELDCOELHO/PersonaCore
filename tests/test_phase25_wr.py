"""PLAN 25-04 — the four repaired 24-REVIEW refusals (WR-01, WR-04, WR-06, WR-08), WATCHED.

D-41 fixes four of 24-REVIEW's eight warnings before any sweep point exists and defers three with
their unreachability RECORDED rather than silenced. This file is the watching half: every refusal
below was observed FAILING against a scratch copy of the pre-fix tree (``git archive`` of the
pre-plan commit into a scratch directory — never ``git stash``, which shares one stack across
worktrees) and then observed passing here.

**EVERY LINE NUMBER IN 24-REVIEW.md IS STALE by roughly +24.** Nothing below resolves a site by
line number; every site is reached through a symbol (``build_bins``, ``_mix_adversarial``,
``_refuse_ambiguous_aligned_input``) or through an AST walk.

**NO FIGURE IS SPELLED TWICE.** The ratio bounds come from
``mitigation_budget.ADVERSARIAL_RATIO_GRID``, the clean-episode counts from the committed
``phase21_unit_record.ARTIFACTS["multiplicity"]`` geometry, and the two unreachability products are
COMPUTED here from both — so a hand-edited digit in the source comment cannot be matched by a
hand-edited digit in the expectation.

**The pair discipline, from ``tests/test_phase24_bins.py``.** ``test_wr06_the_adversarial_pool_is_
read_exactly_once`` is the WR-06 refusal proper and is the one that was RED pre-fix.
``test_wr06_family_labels_stay_paired_with_their_episodes`` is its LOAD-BEARING half: it proves the
family column reaches the reported counts POSITIONALLY, so the AST assertion is guarding something
that can actually go wrong. It is green on both trees BY DESIGN — pre-fix the two accessors are
themselves thin views onto ``_adversarial_pool``, so a patched pool flows through either shape.
Saying so here is the point: a companion that looked RED pre-fix would be measuring the patch, not
the pairing.

CPU-only. No GPU, no MPS, no network, no training — every test below builds bins or walks an AST.
"""

import ast
import json
import math
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import mitigation_budget as mb  # noqa: E402  (scripts/ is not a package)
import phase14_factset as fs  # noqa: E402
import phase21_unit_record as ur  # noqa: E402
import phase24_adversarial as pa  # noqa: E402
import teach_persona as tp  # noqa: E402
from _prose import normalized  # noqa: E402

from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

# The pinned legal domain, IMPORTED. `build_bins`' refusal names these two bounds, and retyping
# either here would let a hand-edited pin be matched by a hand-edited expectation.
GRID_LO = min(mb.ADVERSARIAL_RATIO_GRID)
GRID_HI = max(mb.ADVERSARIAL_RATIO_GRID)
# The smallest ratio that actually places episodes — the operand of the WR-02/WR-03 deferral.
SMALLEST_NONZERO_RATIO = min(ratio for ratio in mb.ADVERSARIAL_RATIO_GRID if ratio > 0)

_TEACH_SOURCE = pathlib.Path(tp.__file__).read_text(encoding="utf-8")


def _clean_episodes_by_capacity():
    """``{n_facts: clean episode count}`` off the COMMITTED multiplicity record.

    Keyed by ``n_facts`` and never by arm name: 24-REVIEW's WR-05 is precisely that the geometry
    rows key on ``dp_n8``/``dp_n64`` while the adversarial rows key on ``adv_n8``/``adv_n64``, and
    that warning is not this plan's to repair. The capacity is the same either way.
    """
    record = json.loads(ur.ARTIFACTS["multiplicity"].read_text(encoding="utf-8"))
    return {row["n_facts"]: row["episodes"] for row in record["corpus_geometry"]}


def _tokenizer():
    """``tests/test_phase24_bins.py::_tokenizer`` — seed, then the FROZEN production tokenizer."""
    seed_everything(tp.SEED)
    return from_json(tp.TOKENIZER_PATH)


def _clean_episodes():
    """The n=8 teaching pool — the 176 episodes ``build_arm_bins('dp_n8', ...)`` renders."""
    return tp.render_episodes(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)


def _align_pairs():
    """The PINNED aligned-branch shape: ``[(fact, ALREADY-RENDERED episodes), ...]``."""
    return [(fact, tp.render_episodes([fact], fs.TAUGHT_FAMILY_IDS)) for fact in fs.LOCKED_FACTS]


def _branch_kwargs(branch):
    """The two CALL SHAPES of one function, so a parametrized test really covers both branches."""
    if branch == "flat":
        return _clean_episodes(), {}
    return [], {"align_facts": _align_pairs()}


def _build(tmp_path, name, episodes, **kwargs):
    """One build under ``tmp_path``; returns ``(stats, bin_path, mask_path)``."""
    bin_path = tmp_path / f"{name}.bin"
    mask_path = tmp_path / f"{name}_mask.bin"
    stats = tp.build_bins(_tokenizer(), episodes, bin_path, mask_path, **kwargs)
    return stats, bin_path, mask_path


def _mix_adversarial_tree():
    """``_mix_adversarial``'s own AST node, resolved BY SYMBOL — never by a 24-REVIEW line."""
    tree = ast.parse(_TEACH_SOURCE)
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_mix_adversarial"
    ]
    assert len(functions) == 1, (
        f"expected exactly one `_mix_adversarial` in {tp.__file__}, found {len(functions)} — "
        "the AST census below would be counting the wrong function body"
    )
    return functions[0]


# =============================================================================================
# ===== WR-01: ONE RATIO DOMAIN, AGREED ACROSS BOTH BRANCHES ==================================
# =============================================================================================


@pytest.mark.parametrize("branch", ("flat", "aligned"))
def test_wr01_a_negative_ratio_is_refused_on_both_branches(tmp_path, branch):
    """A negative ``adversarial_ratio`` refuses BEFORE either branch dispatches.

    The class Phase 20 recorded twice: THE GUARD REFUSES A NAME WHERE THE HARM IS A PROPERTY. The
    flat branch dispatched on ``adversarial_ratio > 0``, which -1.0 fails, so the mixer never ran
    and the CONTROL was built under an ``adv_n8`` / ``adv_n64`` arm name — with no additive
    ``adversarial_*`` stats key for any downstream reader to check.
    """
    episodes, kwargs = _branch_kwargs(branch)
    with pytest.raises(SystemExit) as excinfo:
        _build(tmp_path, "negative", episodes, adversarial_ratio=-1.0, **kwargs)

    message = str(excinfo.value)
    assert "adversarial_ratio=-1.0" in message, (
        f"the {branch} branch's refusal does not carry the OFFENDING VALUE: {message!r}. An "
        "operator who cannot see which number was rejected cannot tell a typo from a bad grid."
    )
    assert "ADVERSARIAL_RATIO_GRID" in message and f"[{GRID_LO}, {GRID_HI}]" in message, (
        f"the {branch} branch's refusal does not name the pinned legal domain by reference to "
        f"mitigation_budget.ADVERSARIAL_RATIO_GRID's bounds [{GRID_LO}, {GRID_HI}]: {message!r}"
    )


@pytest.mark.parametrize("branch", ("flat", "aligned"))
def test_wr01_a_nan_ratio_is_refused_on_both_branches(tmp_path, branch):
    """NaN is the LOAD-BEARING case: it is exactly where the two pre-fix guards disagreed.

    ``float("nan") > 0`` is **False** and ``bool(float("nan"))`` is **True**. The flat branch
    dispatched on the comparison and the aligned branch refused on the truthiness, so one single
    value took two different routes through one function: the flat branch silently skipped the
    mixer and emitted a bin BYTE-IDENTICAL TO THE CONTROL (measured token digest ``f146d426…``)
    under an adversarial arm name, while the aligned branch raised on the same input.
    ``math.isfinite`` is what catches NaN and ±inf together; neither spelling caught either.
    """
    assert not (math.nan > 0) and bool(math.nan), (
        "the premise of this test is false on this interpreter: NaN must fail `> 0` and pass "
        "truthiness, which is what made the two pre-fix guards disagree on exactly this value"
    )

    episodes, kwargs = _branch_kwargs(branch)
    with pytest.raises(SystemExit) as excinfo:
        _build(tmp_path, "nan", episodes, adversarial_ratio=math.nan, **kwargs)

    message = str(excinfo.value)
    assert "adversarial_ratio=nan" in message, (
        f"the {branch} branch's refusal does not carry the offending value: {message!r}"
    )
    assert "ADVERSARIAL_RATIO_GRID" in message and f"[{GRID_LO}, {GRID_HI}]" in message, (
        f"the {branch} branch's refusal does not name the pinned legal domain: {message!r}"
    )


def test_wr01_the_control_ratio_still_builds_and_is_not_caught_by_the_domain_check(tmp_path):
    """NON-VACUITY. ``0.0`` is ``ADVERSARIAL_RATIO_GRID[0]`` — the sweep's OWN control point.

    A domain check that refused the control would refuse the arm the whole record is built from,
    and every refusal above would be green while the sweep could not run at all.
    """
    stats, bin_path, mask_path = _build(
        tmp_path, "control", _clean_episodes(), adversarial_ratio=GRID_LO, replay_ratio=0.0
    )
    assert bin_path.exists() and mask_path.exists()
    assert "adversarial_ratio" not in stats, (
        "the additive adversarial stats keys appeared at the control ratio — the mixture ran "
        "where D-09's grid point 0 says nothing should be placed"
    )


# =============================================================================================
# ===== WR-04: REPLAY AND ADVERSARIAL, REFUSED ON BOTH BRANCHES ===============================
# =============================================================================================


def test_wr04_replay_and_adversarial_together_are_refused_on_the_flat_branch(tmp_path):
    """After both mixers ran, ``replay_ratio`` stopped describing the bin. Measured, not argued.

    Pre-fix, ``replay_ratio=0.5, adversarial_ratio=0.25`` returned stats recording
    ``replay_ratio: 0.5`` over a bin that is 3,790 replay tokens of 15,477 — 0.2449. D-34 is what
    makes that expensive: every point record carries ``records_per_lot`` / ``composed_lot_sizes``
    read LIVE at write time and asserted against the pin under EXACT equality, so a bin whose
    composition the recorded ratio does not describe either halts the sweep late or publishes an
    epsilon that does not describe what happened.
    """
    with pytest.raises(SystemExit) as excinfo:
        _build(
            tmp_path,
            "both",
            _clean_episodes(),
            replay_ratio=0.5,
            adversarial_ratio=SMALLEST_NONZERO_RATIO,
        )

    message = str(excinfo.value)
    assert "replay_ratio=0.5" in message, f"the refusal does not name replay's value: {message!r}"
    assert f"adversarial_ratio={SMALLEST_NONZERO_RATIO}" in message, (
        f"the refusal does not name the adversarial value: {message!r}"
    )
    for token in ("D-34", "records_per_lot", "composed_lot_sizes", "epsilon"):
        assert token in message, (
            f"the refusal does not name {token!r} — the LIVE MECHANISM consequence is the whole "
            f"reason this pair is refused rather than tolerated: {message!r}"
        )


def test_wr04_the_aligned_branch_refusal_of_the_pair_still_fires(tmp_path):
    """The aligned twin's PRE-EXISTING refusal, re-asserted so the symmetry is proved not assumed.

    WR-04 is a MISSING mirror, so the repair is only meaningful if the mirrored-from side still
    works. This also covers the `> 0` rewrite of that guard's truthiness test (WR-01): a botched
    rewrite would silently stop refusing a positive replay ratio on the aligned path.
    """
    with pytest.raises(SystemExit) as excinfo:
        _build(tmp_path, "aligned_pair", [], align_facts=_align_pairs(), replay_ratio=0.5)

    message = str(excinfo.value)
    assert "replay_ratio=0.5" in message and "D-10" in message, (
        f"the aligned branch's replay refusal no longer names its value and its reason: {message!r}"
    )


# =============================================================================================
# ===== WR-06: ONE PAIRED POOL READ ===========================================================
# =============================================================================================


def test_wr06_the_adversarial_pool_is_read_exactly_once():
    """``_mix_adversarial`` calls ``_adversarial_pool`` ONCE and neither thin view at all.

    Pre-fix this walked two independent reads zipped by index with only a ``len()`` check between
    them. D-36 computes ``held_out_generalization`` from the per-family counts carried by all 44
    point records, so a one-off pairing would mislabel every family count in the artifact with no
    assertion firing.
    """
    calls = [
        node.func.attr
        for node in ast.walk(_mix_adversarial_tree())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert calls.count("_adversarial_pool") == 1, (
        f"`_mix_adversarial` calls `_adversarial_pool` {calls.count('_adversarial_pool')} times, "
        f"expected exactly 1 — the whole census is {calls}"
    )
    for view in ("adversarial_episodes", "adversarial_episode_families"):
        assert calls.count(view) == 0, (
            f"`_mix_adversarial` still calls `{view}` — that is one half of the index-paired read "
            f"WR-06 names, and the pairing is what D-36's per-family counts rest on: {calls}"
        )


def test_wr06_family_labels_stay_paired_with_their_episodes(tmp_path, monkeypatch):
    """THE LOAD-BEARING HALF: permuting the family column MOVES the reported counts.

    Without this, the AST assertion above is guarding an invariant nobody showed can break. Here
    the pool is returned with its family labels rotated by one against their episodes, and the
    per-family counts in ``build_bins``' stats move accordingly — so the counts really are read
    POSITIONALLY and a one-off pairing really would publish A3's episodes as A1-mild's.

    Green on the pre-fix tree TOO, by design: both thin views are themselves ``_adversarial_pool``
    readers, so a patched pool reaches either call shape. That is what makes this a companion
    rather than the refusal.
    """
    ratio = SMALLEST_NONZERO_RATIO
    paired = _build(tmp_path, "paired", _clean_episodes(), adversarial_ratio=ratio)[0]

    real_pool = pa._adversarial_pool(_tokenizer())
    monkeypatch.setattr(
        pa,
        "_adversarial_pool",
        lambda _tok, _pool=real_pool: (_pool[0], _pool[1][1:] + _pool[1][:1]),
    )
    permuted = _build(tmp_path, "permuted", _clean_episodes(), adversarial_ratio=ratio)[0]

    paired_counts = paired["adversarial_family_counts"]
    permuted_counts = permuted["adversarial_family_counts"]
    assert paired_counts != permuted_counts, (
        f"rotating the family column by one left the reported counts at {paired_counts} — the "
        "labels are NOT reaching the report positionally, so `test_wr06_the_adversarial_pool_is_"
        "read_exactly_once` is guarding an invariant that cannot break and is vacuous"
    )
    assert sum(paired_counts.values()) == sum(permuted_counts.values()), (
        f"the permutation changed the TOTAL ({paired_counts} -> {permuted_counts}), so it "
        "resized the mixture instead of relabelling it and proves nothing about pairing"
    )
    assert set(paired_counts) == set(permuted_counts) == set(pa.TRAINED_FAMILIES), (
        f"the reported families {sorted(permuted_counts)} are not D-10's trained set "
        f"{sorted(pa.TRAINED_FAMILIES)}"
    )


# =============================================================================================
# ===== WR-08: NO BYTES LAND WHEN A PROOF FAILS ===============================================
# =============================================================================================


def _explode(*_args, **_kwargs):
    """A ``_prove_floor_and_band`` that always refuses — the FAILING-PROOF stand-in."""
    raise SystemExit("[test_phase25_wr] forced _prove_floor_and_band failure")


def test_wr08_no_bytes_land_when_a_proof_fails(tmp_path, monkeypatch):
    """THE NATURAL RED: pre-fix, both bins were on disk after a REFUSED flat build.

    ``tofile`` ran above proof 1, so a build the 1:1 check or the floor/band check rejected had
    already written bytes. That collides with ``refuse_if_exists`` — a later run finds a
    never-validated corpus and reads it as recorded evidence — and with D-10, whose one-attempt
    rule needs "no reading landed" to be CHECKABLE rather than asserted.
    """
    monkeypatch.setattr(tp, "_prove_floor_and_band", _explode)
    bin_path = tmp_path / "flat.bin"
    mask_path = tmp_path / "flat_mask.bin"

    with pytest.raises(SystemExit):
        tp.build_bins(_tokenizer(), _clean_episodes(), bin_path, mask_path)

    assert not bin_path.exists(), (
        f"{bin_path.name} exists after a REFUSED build — a failed build left bytes that "
        "`refuse_if_exists` will treat as a completed point's evidence (WR-08)"
    )
    assert not mask_path.exists(), f"{mask_path.name} exists after a REFUSED build (WR-08)"


def test_wr08_the_same_holds_on_the_aligned_branch(tmp_path, monkeypatch):
    """The aligned twin had the IDENTICAL inversion — including the third ``*_fact.bin``."""
    monkeypatch.setattr(tp, "_prove_floor_and_band", _explode)
    bin_path = tmp_path / "aligned.bin"
    mask_path = tmp_path / "aligned_mask.bin"
    fact_path = tp.fact_bin_path(bin_path)

    with pytest.raises(SystemExit):
        tp.build_bins(_tokenizer(), [], bin_path, mask_path, align_facts=_align_pairs())

    for path in (bin_path, mask_path, fact_path):
        assert not path.exists(), (
            f"{path.name} exists after a REFUSED aligned build — proof 1 and the floor/band proof "
            "must both run before any of the THREE bins land (WR-08)"
        )


# =============================================================================================
# ===== WR-02 / WR-03 / WR-07: DEFERRED, WITH THE UNREACHABILITY RECORDED =====================
# =============================================================================================


def test_wr02_wr03_wr07_are_recorded_as_deferred_with_their_reason():
    """D-41 defers three warnings and requires their unreachability RECORDED, never silenced.

    Read through ``scripts/_prose.normalized`` because the comments LINE-WRAP: the measured defect
    behind that module is a ``grep -c`` returning 0 on a file that contained the phrase. The two
    products are COMPUTED here from the grid's smallest non-zero entry and the committed
    clean-episode geometry, so the source comment's arithmetic is checked against an independent
    derivation rather than against a retyped copy of itself.
    """
    source = normalized(_TEACH_SOURCE)
    for marker in ("WR-02", "WR-03", "WR-07"):
        assert marker in source, (
            f"{marker} is deferred by D-41 but is not RECORDED anywhere in {tp.__file__} — a "
            "deferral that leaves no trace in the source is indistinguishable from a silencing"
        )

    episodes = _clean_episodes_by_capacity()
    assert set(episodes) == {8, 64}, (
        f"the committed multiplicity geometry carries capacities {sorted(episodes)}, not the two "
        "the WR-02/WR-03 deferral reasons over"
    )
    measured_n8 = len(_clean_episodes())
    assert measured_n8 == episodes[8], (
        f"the n=8 arm renders {measured_n8} clean episodes against the committed geometry's "
        f"{episodes[8]} — the unreachability products below would reason over the wrong count"
    )

    for n_facts, n_clean in sorted(episodes.items()):
        product = round(SMALLEST_NONZERO_RATIO * n_clean)
        claim = normalized(f"round({SMALLEST_NONZERO_RATIO} * {n_clean}) = {product}")
        assert claim in source, (
            f"the WR-02/WR-03 deferral does not carry its own arithmetic for n={n_facts}: "
            f"expected {claim!r} in {tp.__file__}. The `n_want < 1` refusal is deferred BECAUSE "
            "it is unreachable, and an unreachability claim without its computed product is a "
            "silencing with a comment on it"
        )
        assert product >= 1, (
            f"round({SMALLEST_NONZERO_RATIO} * {n_clean}) = {product} REACHES the `n_want < 1` "
            "branch — WR-02/WR-03's unreachability is FALSE at this capacity and the deferral "
            "must be re-opened rather than left recorded"
        )
