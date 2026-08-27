"""THE PROTOCOL-MATCHED COMPARATOR'S CPU-PROVABLE HALF — everything checkable before the GPU run.

23-16 builds the comparator's ``train()`` call, its grad-clip capture bracket and its training leg.
The training leg costs ~100 minutes on this M3 and belongs to 23-17. **Everything else about the
comparator is decidable on a laptop CPU in under a second**, and this file decides it — so a
dropped data kwarg, a retyped constant, an un-restored monkeypatch or a newly-added production
keyword is a red test rather than a well-formed run answering a different question.

**NO TEST HERE MAY TRAIN.** None constructs a model, loads the base checkpoint, or calls
``tp.train``. The plan's acceptance criteria enforce that with an AST walk over this file rather
than with a grep — a grep would be reddened by this very paragraph and would still miss
``from personacore.model.gpt import GPT``.

**EVERY EXPECTED VALUE IS READ FROM A COMMITTED SOURCE, NEVER TYPED.** The protocol figures come
from ``results/phase23_sigma_zero.json`` (the arm being matched), the key sets from AST censuses of
the LIVE ``scripts/teach_persona.py``, and the clip constant from ``phase23_matched_prereg``. A
hand-typed 8 / 32 / 200 here would be a second source for one fact — which is the defect this whole
gap closure exists to correct.

CPU-only, GPU-free, no network, no training.
"""

import ast
import collections
import json
import pathlib
import sys

import pytest
import torch

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import phase23_matched_prereg as mp  # noqa: E402  (needs the sys.path insert above)
import phase23_prereg  # noqa: E402  (same reason)
import phase23_resume_prereg as rp  # noqa: E402  (same reason)
import phase23_run  # noqa: E402  (same reason)
import teach_persona as tp  # noqa: E402  (same reason)

from personacore.config import TrainConfig  # noqa: E402

_TEACH = _ROOT / "scripts" / "teach_persona.py"
_SIGMA_ZERO_RECORD = _ROOT / "results" / "phase23_sigma_zero.json"
_RUN_SOURCE = _ROOT / "scripts" / "phase23_run.py"
_LOOP = _ROOT / "src" / "personacore" / "training" / "loop.py"
_MATCHED_RECORD = _ROOT / mp.MATCHED_CONTROL_RECORD

# The seed every check below builds the call at. `SEED_LADDER[0]` rather than a literal: it is the
# ladder's first entry, the same seed the σ=0 record was measured at, and it is what
# `prove_matched_protocol` itself uses.
_SEED = phase23_run.SEED_LADDER[0]

# The largest PRE-clip gradient norm the debug record measured on the DP arm. NOT typed as a bare
# constant — it is asserted to appear in the committed pin's own grad_clip entry first (see
# `test_the_matched_grad_clip_is_the_non_binding_bound`), so this literal is bound to the pin
# rather than being a second source for it.
_MEASURED_DP_PRE_CLIP_MAX = 2.278


def _call():
    """``matched_control_call`` at the ladder's first seed — the object under test throughout."""
    return phase23_run.matched_control_call(_SEED)


def _teach_source():
    return _TEACH.read_text(encoding="utf-8")


def _sigma_zero_training_block():
    """The committed σ=0 record's ``training`` block — the shape the comparator must reproduce."""
    assert _SIGMA_ZERO_RECORD.exists(), (
        f"{_SIGMA_ZERO_RECORD} is missing. It is the COMMITTED artifact of plan 23-10 and the only "
        "source of truth for the protocol this comparator matches; a skipped test here would be a "
        "protocol nobody checked"
    )
    return json.loads(_SIGMA_ZERO_RECORD.read_text(encoding="utf-8"))["training"]


# ---------------------------------------------------------------------------------------------
# TEST 1 — the DP wiring keys, read from the live caller's AST
# ---------------------------------------------------------------------------------------------


def test_matched_kwargs_carry_every_dp_wiring_key():
    """Every key the DP path wires into ``train()``, except ``dp_fn``, reaches the comparator.

    The key set is READ FROM THE AST CENSUS of the live ``teach_persona.py``, never from a literal
    in this test — that is the entire point of the gate. A retyped list here would be a copy free
    to disagree with the caller it is supposed to mirror, and both would look right.

    ``dp_fn`` is the one exclusion and it is asserted in BOTH dicts' direction: its absence is what
    makes this a NON-DP arm reaching the DP arm's data wiring, which is the claim the comparator
    rests on.
    """
    accum, kwargs_keys = mp.dp_wiring_key_census(_teach_source())
    fields, kwargs = _call()
    carried = set(fields) | set(kwargs)

    for key in sorted((set(accum) | set(kwargs_keys)) - {"dp_fn"}):
        assert key in carried, (
            f"the live DP wiring passes {key!r} but the comparator does not. `fact_bin`/`n_facts` "
            "select the fact-aligned packer and `replay_windows` runs the train-time replay pass; "
            "dropping either silently returns this arm to the OLD random-window protocol at a lot "
            "of 8 windows instead of 65"
        )

    assert "dp_fn" not in fields and "dp_fn" not in kwargs, (
        "the comparator passes `dp_fn`. It must appear in NEITHER dict: a non-DP arm that reaches "
        "the DP data wiring is the comparator; one that also reaches the DP seam is a second DP arm"
    )


# ---------------------------------------------------------------------------------------------
# TEST 2 — the production call's WHOLE keyword set, including the 15 the census above cannot see
# ---------------------------------------------------------------------------------------------


def test_matched_call_reproduces_the_production_call_key_set():
    """The third AST gate: the comparator's key set IS the production set minus two omissions.

    THE FAILURE THIS EXISTS TO CATCH, named rather than implied: a NEW keyword added to the
    production ``train(...)`` call in ``teach_persona.py`` — say ``extra_eval_fns=``, which is a
    real parameter of ``train()`` that the production call does not currently pass. The
    ``dp_fn``-branch census would stay GREEN (no branch changed) and the DP-wiring census would
    stay GREEN (neither DP dict changed), while the comparator silently stopped matching. That is
    the 23-08 failure shape one level up: a hand-drawn boundary that did not know what it excluded.
    """
    production = mp.prove_train_call_keys(_teach_source())
    _fields, kwargs = _call()

    seen = {"train_config", "runtime_config", "model", "model_config"} | set(kwargs)
    expected = set(production) - {"resume_from", "dp_fn"}
    assert seen == expected, (
        "the comparator's train(...) keyword set is not the production set minus "
        "{resume_from, dp_fn}.\n"
        f"  EXTRA   (comparator passes, production does not): {sorted(seen - expected)}\n"
        f"  MISSING (production passes, comparator does not): {sorted(expected - seen)}"
    )
    assert {"resume_from", "dp_fn"} <= set(production), (
        "the two deliberate omissions are no longer IN the production set, so subtracting them "
        "proves nothing. This assertion is what stops the subtraction going vacuous"
    )


# ---------------------------------------------------------------------------------------------
# TEST 3 — the protocol, asserted against the committed σ=0 record rather than against literals
# ---------------------------------------------------------------------------------------------


def test_matched_protocol_reproduces_the_sigma_zero_records_own_shape():
    """Field by field against ``results/phase23_sigma_zero.json`` — the arm being matched.

    The committed record is the source of truth. A hand-typed 8 / 32 / 200 in this test would be a
    SECOND SOURCE FOR ONE FACT, free to agree with a comparator that had drifted away from the arm
    it controls for.
    """
    training = _sigma_zero_training_block()
    fields, kwargs = _call()

    assert training["grad_accum_steps"] == fields["grad_accum_steps"]
    assert training["capacity_n_facts"] == kwargs["n_facts"]
    assert training["replay_windows_per_step"] == kwargs["replay_windows"]
    assert training["batch_size"] == fields["batch_size"]
    assert training["max_steps"] == fields["max_steps"]
    assert training["block_size"] == tp.BLOCK_SIZE

    # The lot the two arms share, stated as the number the equalisation is FOR: 33 teaching windows
    # (one fact's worth under the fact-aligned packer) plus the replay budget, against the old
    # control's `batch_size` alone.
    assert kwargs["replay_windows"] > fields["batch_size"], (
        "the comparator's replay budget no longer exceeds one micro-batch, so the lot it builds is "
        "not the DP arm's 65-window lot. The 8.125x lot-volume difference is the largest per-step "
        "effect this comparator exists to remove"
    )


# ---------------------------------------------------------------------------------------------
# TEST 4 — bin IDENTITY, not bin equivalence
# ---------------------------------------------------------------------------------------------


def test_the_matched_arm_trains_on_the_sigma_zero_arms_own_bins():
    """The three corpus paths the comparator reads ARE the three digested dp_n8 bins.

    IDENTITY, not equivalence: an equivalent rebuild would be a second corpus that happens to
    agree, and "happens to agree" is what ``prove_bins_match`` exists to stop being an assumption.
    Written as a test rather than a comment because a comment cannot redden.
    """
    _fields, kwargs = _call()
    read = {
        str(pathlib.Path(kwargs[key]).resolve())
        for key in ("train_bin", "train_mask_bin", "fact_bin")
    }
    digested = {str(pathlib.Path(path).resolve()) for path in phase23_run.DP_N8_BIN_SHA256}
    assert read == digested, (
        "the comparator does not read exactly the three bins `DP_N8_BIN_SHA256` pins to 23-07's "
        f"recorded digests.\n  reads:    {sorted(read)}\n  digested: {sorted(digested)}"
    )


# ---------------------------------------------------------------------------------------------
# TEST 5 — the clip constant, and the margin it clears the measured norms by
# ---------------------------------------------------------------------------------------------


def test_the_matched_grad_clip_is_the_non_binding_bound():
    """23-08 enumerated four residual differences BY HAND and MISSED this one.

    MEASURED, and the reason the constant exists: the old control's clip BOUND ON 19 OF ITS FIRST
    25 STEPS at mean shrink 0.8071, while the DP arm — where ``loop.py``'s clip branch is
    structurally unreachable — was never clipped at all. The comparator equalises that by CONSTANT;
    ``captured_grad_clip`` is what makes the constant's inertness an observation at run time.
    """
    fields, _kwargs = _call()
    assert fields["grad_clip"] == mp.MATCHED_GRAD_CLIP
    assert mp.MATCHED_GRAD_CLIP == phase23_run.SIGMA_ZERO_CLIP_NORM, (
        "the comparator's C and the σ=0 arm's C have diverged. They are the same repository "
        "non-binding bound and a difference between them would be a difference between the two "
        "arms nobody declared"
    )

    # The literal below is BOUND TO THE PIN rather than being a second source for it: the pin's own
    # grad_clip entry is the committed record of what was measured.
    measured = next(e for e in mp.MATCHED_EQUALISED if e["mechanism"] == "grad_clip")["measured"]
    assert str(_MEASURED_DP_PRE_CLIP_MAX) in measured, (
        f"{_MEASURED_DP_PRE_CLIP_MAX} no longer appears in the committed grad_clip measurement "
        f"{measured!r}. This test's margin check would then rest on a number nothing records"
    )
    assert mp.MATCHED_GRAD_CLIP > _MEASURED_DP_PRE_CLIP_MAX * 1e5, (
        f"C = {mp.MATCHED_GRAD_CLIP!r} clears the largest measured pre-clip norm "
        f"{_MEASURED_DP_PRE_CLIP_MAX} by under five orders of magnitude. The bound must be so far "
        "above the operating point that binding is implausible before the run, not merely unlikely"
    )


# ---------------------------------------------------------------------------------------------
# TEST 6 — what the DEFAULT would have done, so dropping the constant cannot pass silently
# ---------------------------------------------------------------------------------------------


def test_the_default_grad_clip_would_not_be_equalised():
    """The RED this file exists to keep watched: the default BINDS at this operating point.

    ``TrainConfig``'s default ``grad_clip`` is 1.0 and every measured DP pre-clip norm is above it,
    so a future edit dropping ``grad_clip`` from ``matched_control_call`` would silently restore
    the exact asymmetry the comparator was built to remove — and every other test in this file
    would stay green. This one would not.
    """
    default = TrainConfig().grad_clip
    assert default == 1.0
    assert default < _MEASURED_DP_PRE_CLIP_MAX, (
        f"the default grad_clip {default!r} is no longer below the measured DP pre-clip norms "
        f"(max {_MEASURED_DP_PRE_CLIP_MAX}). If that ever becomes true the equalisation is moot — "
        "but until then, omitting the constant reinstates the confound"
    )
    assert default != mp.MATCHED_GRAD_CLIP, (
        "the equalised clip has collapsed onto the default, so passing it explicitly no longer "
        "changes anything and this whole mechanism has gone inert without saying so"
    )


# ---------------------------------------------------------------------------------------------
# TEST 7 — the capture bracket, watched observing AND watched restoring
# ---------------------------------------------------------------------------------------------


def test_captured_grad_clip_observes_and_restores():
    """A shadow that leaks is a shadow that corrupts every later test in the process.

    Two halves, both watched: INSIDE the bracket the captured value equals what the real call
    returned (so the recorded quantity is the PRE-clip norm and not something else), and OUTSIDE it
    the module attribute is the ORIGINAL CALLABLE BY IDENTITY — captured before entering, compared
    with ``is``, because an equal-looking replacement is exactly what a leak looks like.

    CPU tensors only; a two-parameter toy module, no model, no checkpoint.
    """
    layer = torch.nn.Linear(2, 1)
    params = list(layer.parameters())
    assert len(params) == 2, "the toy module must have two parameters for the norm to combine any"
    for param in params:
        param.grad = torch.ones_like(param)

    original = torch.nn.utils.clip_grad_norm_

    with phase23_run.captured_grad_clip() as box:
        assert torch.nn.utils.clip_grad_norm_ is not original, (
            "the bracket did not install its wrapper, so it would record nothing and report "
            "`non-binding` by having observed no norms at all"
        )
        returned = torch.nn.utils.clip_grad_norm_(params, mp.MATCHED_GRAD_CLIP)
        assert len(box["norms"]) == 1
        assert box["norms"][0] == float(returned), (
            f"the bracket recorded {box['norms'][0]!r} but the call returned {float(returned)!r}. "
            "The recorded quantity must be the PRE-clip global norm the call returns, unmodified"
        )

    assert torch.nn.utils.clip_grad_norm_ is original, (
        "`captured_grad_clip` did not restore `clip_grad_norm_`. A leaked shadow would keep "
        "appending to a dead box for the rest of the process and would silently wrap every later "
        "clip in this test session"
    )
    assert box["norms"], "the box must still carry its observations after the bracket exits"


# ---------------------------------------------------------------------------------------------
# TEST 8 — the one-attempt rule, driven in both directions
# ---------------------------------------------------------------------------------------------


def test_a_second_matched_attempt_is_refused():
    """``prove_first_attempt`` refuses a tracked artifact and admits an empty result.

    Both directions, because a guard that refuses everything is as useless as one that refuses
    nothing — and this one is what 23-17 calls with its own ``git ls-files`` result in hand.
    """
    with pytest.raises(SystemExit, match="ONE ATTEMPT"):
        mp.prove_first_attempt([mp.MATCHED_CONTROL_RECORD])
    assert mp.prove_first_attempt([]) is True


# ---------------------------------------------------------------------------------------------
# TEST 9 — the GPU run's own preflight, exercised here at zero cost
# ---------------------------------------------------------------------------------------------


def test_the_matched_preflight_runs_against_live_source():
    """The same gate the 100-minute run will hit, run against live source for free.

    ``prove_matched_protocol`` reads ``loop.py`` and ``teach_persona.py`` off disk and drives all
    three AST censuses plus both directions of the key-set subtraction. Running it in CI means a
    protocol drift is a red test in one second rather than a ``SystemExit`` after the GPU is warm.
    """
    census = phase23_run.prove_matched_protocol()
    assert sum(census.values()) == sum(mp.DP_FN_BRANCH_COUNTS.values()), (
        f"the live dp_fn branch census sums to {sum(census.values())} against the pinned ledger's "
        f"{sum(mp.DP_FN_BRANCH_COUNTS.values())}. The pin is EDIT-ONCE, so a genuine new branch in "
        "`loop.py` cannot be absorbed by amending it — it has to be dispositioned somewhere else"
    )
    assert sum(census.values()) == len(mp.DP_FN_BRANCH_DISPOSITIONS), (
        "every counted branch must carry a disposition, or the ledger names a difference between "
        "the comparator and the σ=0 arm that nobody dispositioned"
    )


# ---------------------------------------------------------------------------------------------
# TESTS 10-18 — THE RECORD'S STRUCTURAL GUARDS, written BEFORE the run so they are live the
# moment it lands.
#
# THERE IS NO SKIP OF ANY FORM IN THIS FILE, and the plan's acceptance gate proves that by AST
# rather than by grep — a grep would be reddened by this very sentence. A silently-skipped guard
# is the "declared invariant quietly becomes false" defect this project keeps naming, so the
# vacuity shape below ASSERTS SOMETHING in the absent-record case: that the sub-mode which writes
# the record is registered, named in its own message.
# ---------------------------------------------------------------------------------------------


def _record():
    """The REAL matched record, or ``None`` after asserting the writer that produces it exists."""
    if not _MATCHED_RECORD.exists():
        assert "matched" in phase23_run._TABLE, (
            f"{mp.MATCHED_CONTROL_RECORD} has not been written yet AND `phase23_run._TABLE` "
            "carries no `matched` sub-mode, so nothing in this repository can ever produce it. "
            "This is the vacuity branch of the record guards and it deliberately asserts rather "
            "than passing quietly"
        )
        return None
    return json.loads(_MATCHED_RECORD.read_text(encoding="utf-8"))


def test_matched_record_floor_re_derives():
    """The floor re-derives from the record's OWN counts through the blind reduction.

    Counts, not rates: ``k/n`` recomputed here is what the record claims its readings ARE, so a
    ``rate`` that drifted from its own denominator is caught in the same assertion.
    """
    record = _record()
    if record is None:
        return
    rates = [entry["primary"]["k"] / entry["primary"]["n"] for entry in record["per_seed"]]
    for entry, rate in zip(record["per_seed"], rates):
        assert entry["primary"]["rate"] == rate, (
            f"seed {entry['seed']}'s recorded rate {entry['primary']['rate']!r} is not "
            f"{entry['primary']['k']}/{entry['primary']['n']} = {rate!r} — the reading and its own "
            "denominator disagree"
        )
    assert record["readings"] == rates
    assert record["floor"] == phase23_prereg.noise_floor(rates), (
        f"the recorded floor {record['floor']!r} is not `phase23_prereg.noise_floor` over the "
        f"record's own counts ({phase23_prereg.noise_floor(rates)!r}). A floor that does not "
        "re-derive from its own artifact is a number whose provenance is a claim"
    )


def test_matched_record_carries_every_floor_provenance_key():
    """All EIGHT ``FLOOR_PROVENANCE_KEYS`` at the top level — an unlabelled number is borrowed."""
    record = _record()
    if record is None:
        return
    missing = [key for key in phase23_prereg.FLOOR_PROVENANCE_KEYS if key not in record]
    assert not missing, (
        f"{mp.MATCHED_CONTROL_RECORD} is missing {missing!r} from FLOOR_PROVENANCE_KEYS. "
        "`sigma_zero_verdict` refuses a floor whose artifact, commit, device, seeds or reduction "
        "is unstated and never defaults it"
    )
    assert record["reduction"] == "phase23_prereg.noise_floor"


def test_matched_record_grad_clip_was_non_binding_on_every_seed():
    """Every seed: zero binding clips, a full call count, and a margin under C.

    The CALL COUNT is the half that is easy to lose. ``bound_count == 0`` is also what a branch
    that was NEVER TAKEN reports, so without ``calls == MAX_STEPS`` a comparator whose clip
    equalisation never ran at all would pass as a comparator whose clip never bound.
    """
    record = _record()
    if record is None:
        return
    evidence = record["grad_clip_evidence"]
    assert len(evidence) == record["n_seeds"], (
        f"grad-clip evidence covers {len(evidence)} seed(s) against {record['n_seeds']} readings"
    )
    for seed, block in sorted(evidence.items()):
        assert block["bound_count"] == 0, (
            f"seed {seed} bound its clip on {block['bound_count']} step(s) — the comparator "
            "differs from the σ=0 arm by CLIPPING rather than by protocol"
        )
        assert block["calls"] == tp.MAX_STEPS, (
            f"seed {seed} recorded {block['calls']} clip call(s) over a {tp.MAX_STEPS}-step run. "
            "`loop.py` fires the clip once per optimizer step IFF `dp_fn is None`, so a lower "
            "count means the branch was never taken and the equalisation never applied"
        )
        assert block["max_pre_clip_norm"] < mp.MATCHED_GRAD_CLIP, (
            f"seed {seed}'s largest pre-clip norm {block['max_pre_clip_norm']!r} reaches C = "
            f"{mp.MATCHED_GRAD_CLIP!r}"
        )
        assert block["checked_before_scoring"] is True


def test_matched_record_declares_the_branch_census():
    """The recorded census equals a LIVE census of ``loop.py`` — not a copy free to go stale."""
    record = _record()
    if record is None:
        return
    live = mp.dp_fn_branch_census(_LOOP.read_text(encoding="utf-8"))
    recorded = collections.Counter(
        {
            (entry["function"], entry["condition"]): entry["count"]
            for entry in record["dp_fn_branch_census"]
        }
    )
    assert sum(recorded.values()) == sum(mp.DP_FN_BRANCH_COUNTS.values()), (
        f"the recorded census sums to {sum(recorded.values())} against the blind ledger's "
        f"{sum(mp.DP_FN_BRANCH_COUNTS.values())}"
    )
    assert recorded == live, (
        "the census in the record and a live census of `loop.py` disagree.\n"
        f"  recorded: {sorted(recorded.items())}\n"
        f"  live:     {sorted(live.items())}"
    )


def test_matched_record_declares_the_visibility():
    """The disclosure TRAVELS WITH THIS ARTIFACT, not only with the verdict four plans downstream.

    Driven with the REAL record through the pin's own refusal, because a reader who opens the
    control record and never opens the verdict record would otherwise get the protocol with no
    disclosure at all.
    """
    record = _record()
    if record is None:
        return
    assert mp.prove_control_record_declares_visibility(record) is True
    assert record["sigma_zero_was_visible"] is True
    assert record["sigma_zero_visibility_disclosure"] == mp.SIGMA_ZERO_VISIBILITY_DISCLOSURE, (
        "the record's disclosure is not `phase23_matched_prereg.SIGMA_ZERO_VISIBILITY_DISCLOSURE` "
        "VERBATIM. A paraphrase is a second source for one statement, free to soften it"
    )


def test_matched_record_records_the_attempt_state():
    """Both refusals' INPUTS are recorded, and the scope is stated at its TRUE strength.

    FOUR clauses, not three. A test checking only three passes against a scope naming three of
    four — which is exactly how the overclaim survived a revision — so clauses (3) and (4) are
    asserted BY NAME here, and (4) in BOTH halves: the auditability AND its non-retroactive start
    point. An auditability claim without its start point is the same overclaim in new clothes.
    """
    record = _record()
    if record is None:
        return

    # WIDENED, NOT DELETED, and the continuation branch's assertions are at least as hard as the
    # first-attempt branch's. 23-17's run was harness-killed at 3 of 5 seeds, so the completion is
    # a CONTINUATION: both lists below are legitimately non-empty and a bare `== []` would go RED
    # against a correct record. What the two branches share is that the recorded attempt state must
    # match the rule that actually governed the run.
    attempt = record["attempt"]
    assert attempt in ("first", "continuation"), (
        f"the record declares attempt {attempt!r}, which is neither of the two branches "
        "`phase23_run.matched` can take"
    )
    if attempt == "first":
        assert record["matched_glob_at_start"] == [], (
            f"the record says a matched artifact was ALREADY TRACKED at run start: "
            f"{record['matched_glob_at_start']!r}"
        )
        assert record["prior_scored_seeds_at_start"] == [], (
            f"the record says the state file already held SCORED matched seeds at run start: "
            f"{record['prior_scored_seeds_at_start']!r}"
        )
        assert record["continuation_rule"] is None
        assert record["continuation_fingerprint"] is None
    else:
        assert record["continuation_rule"] == (
            "phase23_resume_prereg.prove_killed_run_continuation"
        )
        assert record["continuation_scope"] == rp.CONTINUATION_SCOPE, (
            "the record's continuation scope is not `phase23_resume_prereg.CONTINUATION_SCOPE` "
            "VERBATIM. A paraphrase is a second source for one statement, free to soften it"
        )
        fingerprint = record["continuation_fingerprint"]
        assert fingerprint["record_exists"] is False
        assert set(fingerprint["scored_seeds"]) == set(fingerprint["committed_scored_seeds"]), (
            "the recorded fingerprint says the working tree and git history disagreed about which "
            "seeds had scored, which conjunct 5 refuses — so this record cannot have been written"
        )
        assert len(fingerprint["scored_seeds"]) < len(phase23_run.SEED_LADDER), (
            "the fingerprint records a FULL scored set, which is what a COMPLETED attempt leaves. "
            "A continuation is by definition the completion of a run that never wrote its record"
        )
        # RE-ADMITTED under its own rule, PASSING ITS OWN `tracked` — with `tracked=[]` conjuncts 6
        # and 7 would be satisfied vacuously and two of the seven would go silently untested
        # forever. `ladder` is converted back with `tuple(...)` and NEVER sorted: conjuncts 3 and 4
        # INDEX it, and `sorted(SEED_LADDER)` would make this re-admission REFUSE.
        assert rp.prove_killed_run_continuation(
            tracked=fingerprint["tracked"],
            ladder=tuple(fingerprint["ladder"]),
            trained_seeds=set(fingerprint["trained_seeds"]),
            scored_seeds=set(fingerprint["scored_seeds"]),
            committed_scored_seeds=set(fingerprint["committed_scored_seeds"]),
            record_exists=fingerprint["record_exists"],
        )
        assert "WRITE-ORDERING" in record["continuation_discrimination"].upper() or (
            "LAST act" in record["continuation_discrimination"]
        ), (
            "the record does not name the write-ordering that discriminates a killed run from a "
            f"deleted-and-re-run one: {record['continuation_discrimination']!r}"
        )

    # THE FROZEN RULE STILL GOVERNS. The continuation is an exception that arrived BESIDE it, never
    # a replacement for it, so this key and the whole scope block below are UNTOUCHED.
    assert record["one_attempt_rule"] == "phase23_matched_prereg.prove_first_attempt"

    scope = record["one_attempt_scope"].upper()
    for clause in (
        "ACROSS COMMITS",  # (1)
        "UNCOMMITTED WINDOW",  # (2)
        "PREVENTED BY NOTHING",  # (3) — the full-delete case, refused by nothing in real time
        "AUDITABLE AFTER THE FACT",  # (4a) — what the same-session commit buys
        "NOT RETROACTIVE",  # (4b) — and where that auditability BEGINS
        "DISCIPLINE, NOT A MECHANISM",
    ):
        assert clause in scope, (
            f"the recorded one-attempt scope omits {clause!r}. A rule whose recorded scope "
            "overclaims is the defect this record exists to prevent"
        )
    assert "NOT 'CLOSED'" in scope, (
        "the scope no longer says the residual is not 'closed'. That word is the whole difference "
        "between the weakest true guarantee and the strongest sayable one"
    )


def test_matched_record_names_its_omitted_fields():
    """The six absent diagnostics are DECLARED in the record, with the reason beside them."""
    record = _record()
    if record is None:
        return
    omitted = record["omitted_fields"]
    for name in (
        "ppl_adapter_on",
        "ppl_adapter_off",
        "ppl_scored_targets",
        "teaching_tokens",
        "replay_tokens",
        "replay_ratio",
    ):
        assert name in omitted["fields"], (
            f"{name!r} is absent from the comparator's per-seed block AND from `omitted_fields`, "
            "so a reader diffing this record against the old control record's `per_seed` finds "
            "the difference and no explanation"
        )
        assert omitted["fields"][name] is None
    assert "masked_perplexity" in omitted["ppl_omitted_reason"], (
        "the omission reason does not name `masked_perplexity`, which is the sweep whose absence "
        f"causes it: {omitted['ppl_omitted_reason']!r}"
    )


def _matched_writer():
    """The ``matched`` sub-mode's own AST node, from live source."""
    tree = ast.parse(_RUN_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "matched":
            return node
    raise AssertionError(f"no `def matched` in {_RUN_SOURCE} — the record writer has no writer")


def _matched_branch():
    """The ``if not scored:`` node that selects between the two one-attempt rules."""
    guards = [
        item
        for item in ast.walk(_matched_writer())
        if isinstance(item, ast.If)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "prove_first_attempt"
            for call in ast.walk(item)
        )
    ]
    assert len(guards) == 1, (
        f"`matched` has {len(guards)} branches reaching `prove_first_attempt`, not one — which "
        "rule governs a run would then depend on which branch a reader happened to look at"
    )
    return guards[0]


def _called_attrs(nodes):
    return {
        call.func.attr
        for node in nodes
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    }


def test_both_one_attempt_rules_are_reachable_and_the_frozen_one_gets_an_unfiltered_argument():
    """The branch is a MECHANISM, not a comment — and the frozen refusal stays REACHABLE.

    ``if not matched_glob_at_start and not scored:`` would only ever call ``prove_first_attempt``
    with an argument control flow had ALREADY PROVED EMPTY. That is filtering by control flow, and
    it makes the frozen rule's refusal unreachable while leaving the call site looking correct.
    ``not scored`` alone is one token shorter and strictly stronger. The B4 case below — a tracked
    artifact beside an EMPTY scored set — is exactly the case the filtered predicate would have
    made unreachable, and it is watched firing here.
    """
    branch = _matched_branch()
    assert isinstance(branch.test, ast.UnaryOp) and isinstance(branch.test.op, ast.Not), (
        f"the branch predicate is a {type(branch.test).__name__}, not `not <name>`. A `BoolOp` "
        "here would hand the frozen rule an argument the branch had already proved empty"
    )
    assert isinstance(branch.test.operand, ast.Name), (
        "the branch predicate is not `not <single name>`, so what it filters on is not readable "
        f"from the call site: {ast.dump(branch.test.operand)}"
    )
    assert "prove_first_attempt" in _called_attrs(branch.body)
    assert "prove_killed_run_continuation" in _called_attrs(branch.orelse)
    assert "prove_killed_run_continuation" not in _called_attrs(branch.body)
    assert "prove_first_attempt" not in _called_attrs(branch.orelse)

    # B4 — WATCHED FIRING. A tracked artifact with an EMPTY scored set reaches the FROZEN rule with
    # the real, non-empty list and raises its own refusal.
    with pytest.raises(SystemExit) as refusal:
        mp.prove_first_attempt([rp.seed_run_csv(phase23_run.SEED_LADDER[0])])
    assert "ONE ATTEMPT — REFUSED" in str(refusal.value)

    # And the other branch, against constructed state: a killed run is ADMITTED by the NEW rule.
    ladder = phase23_run.SEED_LADDER
    scored = set(ladder[:3])
    assert (
        rp.prove_killed_run_continuation(
            tracked=sorted(rp.seed_run_csv(seed) for seed in [*sorted(scored), ladder[3]]),
            ladder=ladder,
            trained_seeds=scored,
            scored_seeds=scored,
            committed_scored_seeds=scored,
            record_exists=False,
        )
        is True
    )


def test_the_matched_writer_does_not_inline_the_reduction():
    """The writer CALLS the blind reduction; it never types a spread of its own.

    ``scripts/phase19_floor.py``'s property 2: a reduction chosen in the artifact writer is a
    reduction chosen with the numbers already visible. This test is what makes that structural
    rather than a matter of care.
    """
    node = _matched_writer()
    walked = list(ast.walk(node))
    calls = [item for item in walked if isinstance(item, ast.Call)]
    assert calls, "META: the AST walk found no Call nodes at all — the scan is broken, not clean"

    def _spread(item):
        if not isinstance(item, ast.Call):
            return None
        if isinstance(item.func, ast.Name) and item.func.id in {"max", "min"}:
            return item.func.id
        if isinstance(item.func, ast.Attribute) and item.func.attr in {"max", "min"}:
            return item.func.attr
        return None

    inlined = [(_spread(item), item.lineno) for item in calls if _spread(item)]
    assert not inlined, (
        f"`matched` calls {inlined} — the spread is typed in the writer instead of being CALLED "
        "out of `phase23_prereg.noise_floor`"
    )
    subtractions = [
        item.lineno
        for item in walked
        if isinstance(item, ast.BinOp)
        and isinstance(item.op, ast.Sub)
        and (_spread(item.left) or _spread(item.right))
    ]
    assert not subtractions, (
        f"`matched` subtracts one spread from another at line(s) {subtractions}"
    )

    called = [
        item.func.id
        for item in calls
        if isinstance(item.func, ast.Name) and item.func.id == "noise_floor"
    ]
    assert called, (
        "`matched` never calls `noise_floor`. With no spread typed either, the writer would be "
        "reducing nothing — which is how this guard could pass while measuring nothing"
    )


def test_matched_record_names_the_superseded_ledger():
    """The OLD hand-drawn ledger is cited BY NAME, together with the entry it missed."""
    record = _record()
    if record is None:
        return
    superseded = record["superseded_ledger"]
    assert "residual_differences" in superseded and "grad_clip" in superseded, (
        "the record does not name both `residual_differences` and the `grad_clip` entry that "
        f"ledger omitted: {superseded!r}"
    )
