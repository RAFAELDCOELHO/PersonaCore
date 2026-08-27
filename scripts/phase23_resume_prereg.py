"""THE KILLED RUN'S CONTINUATION — a SECOND rule, arriving VISIBLY beside the frozen pin.

**WHY THIS IS A NEW FILE AND NOT AN EDIT TO ``scripts/phase23_matched_prereg.py``. MEASURED, NOT
STYLISTIC.** ``git merge-base --is-ancestor HEAD d99d2aa`` exits **NON-ZERO**: ``d99d2aa`` is the
EARLIEST add of ``results/phase23_matched_*`` and it is already an ancestor of ``HEAD``, not a
descendant. ``tests/test_phase20_prereg.py``'s ``_assert_ordering_holds`` requires every commit
touching a pre-registration to be a STRICT ANCESTOR of its artifact glob's earliest add, and it
takes ``adds[-1]`` — the EARLIEST — so a delete-and-re-add cycle launders nothing. A second commit
touching the matched pin would therefore redden
``tests/test_phase23_matched_prereg.py::test_the_matched_prereg_precedes_every_matched_artifact``
**PERMANENTLY, with no recovery path.** The pin is not edited here, not wrapped, and not passed a
filtered input.

**THE ROUTE, AT ITS TRUE STRENGTH — this is the REMEDY SHAPE of clause (4), not its CASE.** Clause
(4) of ``prove_first_attempt``'s refusal is about a comparator RENAMED OUT of
``MATCHED_ARTIFACT_GLOB`` (``results/phase23_rematch_*``): such an arm is not refused, and what
raises its cost is that a second comparator "would have to arrive with a NEW pre-registration. That
is VISIBLE, NOT REFUSED." **These artifacts keep their names and stay INSIDE the glob**, so this is
not that case. What is borrowed is the remedy the clause names — a second rule arrives with its own
pre-registration, visible rather than refused — and ``scripts/_addendum.py``'s docstring documents
the same route for the phase-17/18 writers frozen by this guard class.
``23-17-SUMMARY.md``'s "Notes for whoever plans the completion", item 3, names it too.

**THE DISCRIMINATION, ARGUED FROM WRITE-ORDERING ALONE.**

``phase23_run.matched`` writes ``results/phase23_matched_control.json`` as its **LAST act**, AFTER
the ``for seed in seeds:`` loop has scored EVERY seed in ``phase23_run.SEED_LADDER``. So a COMPLETED
attempt necessarily leaves ``len(scored) == len(ladder)``. **``len(scored) < len(ladder)`` is a
state the completion path CANNOT PRODUCE.**

A completed attempt whose record was then DELETED still leaves ``len(ladder)`` scored seeds:
deleting the record does not un-score the seeds, and ``phase23_run._state_record`` refuses to
overwrite a recorded value at a different one. To read fewer, an operator would additionally have to
delete seed blocks from the driver's working state — and that state file is force-tracked, so such a
delete is a VISIBLE DIFF against ``git show HEAD:``, which is exactly what conjunct 5 compares.

The argument is about the ORDER THE WRITER WRITES IN. It is not about ``0.7837301587301587``,
``0.7678571428571429`` or ``0.7718253968253969``, and it would be the same argument at any three
values.

**WHY THAT ARGUMENT IS INDEPENDENT OF THE READINGS, AND HOW A REVIEWER CHECKS IT.**

Three readings were on screen when this module was written. Narrowing a refusal after seeing its
readings is indistinguishable from narrowing it BECAUSE of them unless the independence is
STRUCTURAL. It is made structural in three ways, all checkable:

  (a) ``prove_killed_run_continuation``'s signature carries **no rate, count, k, n, floor or
      reading** — only seed SETS, seed COUNTS, trained/scored STATUS, and one boolean. A reading
      cannot enter it. Check it by reading the signature, or with the AST gate in
      ``tests/test_phase23_resume_prereg.py``.

  (b) ``seed_status`` reads ``"primary" in block`` and ``"adapter_sha256" in block`` — **key
      MEMBERSHIP, never a value.** No comparison against any recorded number occurs anywhere in
      this module.

  (c) ``test_the_continuation_predicate_is_invariant_under_arbitrary_readings`` REBUILDS EVERY SEED
      BLOCK as ``{k: <arbitrary> for k in block}`` — every value replaced, KEY PRESENCE ALONE
      preserved — in three variants, and proves the derived arguments, the return value AND the
      refusal message bit-identical across all four states. Perturbing only ``primary.rate``/``.k``/
      ``.n`` would NOT prove this: ``heldout_on.rate``, ``final_train_loss`` and
      ``training_seconds`` were on screen too, so a narrowing keyed on any of those would survive a
      three-field probe. The whole-block substitution is what makes the independence a fact rather
      than a claim.

An AST tripwire in the test file additionally refuses ANY float constant in this module. There is no
quantity here that is not a seed, a count or a boolean.

CPU-only, GPU-free, no torch, no network, no subprocess, stdlib only. The CALLER runs git and passes
the results in, exactly as ``prove_first_attempt`` takes its caller's ``git ls-files`` result.
"""

from phase23_matched_prereg import (
    MATCHED_ARM_PREFIX,
    MATCHED_CONTROL_RECORD,
    MATCHED_VERDICT_RECORD,
    matched_arm,
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — the frozen pin's ``_prove`` register, reproduced.

    Never ``assert``. ``python -O`` strips ``assert`` outright, and this module is entirely
    refusals: under ``-O`` a bare-``assert`` implementation would admit every case it exists to
    reject, silently.
    """
    if not condition:
        raise SystemExit(f"[phase23_resume_prereg] {message}")


def seed_run_csv(seed):
    """The tracked per-seed training curve for one matched seed. RESOLVED, never retyped.

    ``matched_arm`` returns the arm name WITHOUT the prefix and ``teach_persona.arm_outputs``
    composes ``{prefix}_{arm}``, so the real path is ``results/{MATCHED_ARM_PREFIX}_{arm}/run.csv``.
    Dropping the prefix yields ``results/matched_control_seed1337/run.csv``, which matches nothing
    in ``git ls-files`` — so conjunct 7 would refuse every real state.
    """
    return f"results/{MATCHED_ARM_PREFIX}_{matched_arm(seed)}/run.csv"


def seed_status(section):
    """``(trained, scored)`` as frozensets of INTS, derived from KEY PRESENCE ALONE.

    ``section`` is the driver's working-state ``matched`` block: ``{"1337": {...}, ...}``. A seed is
    TRAINED when its block carries ``adapter_sha256`` and SCORED when it carries ``primary``.
    Membership only — no value is read, compared or thresholded, which is half of why this rule
    cannot have been narrowed by a reading.

    **SETS, NEVER SORTED LISTS.** ``sorted(['1337', '1338', '2024'])`` is
    ``['1337', '1338', '2024']`` while the ladder's first three entries are ``(1337, 2024, 1338)``,
    so a sorted-list comparison against a ladder prefix is FALSE for the very state this rule exists
    to admit.
    """
    trained = frozenset(int(seed) for seed, block in section.items() if "adapter_sha256" in block)
    scored = frozenset(int(seed) for seed, block in section.items() if "primary" in block)
    return trained, scored


CONTINUATION_SCOPE = """\
THE SCOPE OF THE CONTINUATION RULE, STATED AT ITS TRUE STRENGTH — FIVE CLAUSES, AND THE FIFTH IS
ABOUT THIS MODULE ITSELF.

  (1) IT BINDS ON COMMITTED STATE PLUS THE WORKING TREE, AND ONLY THERE. Conjunct 5 compares the
      working tree's scored set against the one `git show HEAD:` records. An operator with a dirty
      tree and no commit is OUTSIDE this rule exactly as clause (1) of
      `phase23_matched_prereg.prove_first_attempt` describes its own uncommitted window. This rule
      narrows that window; it does not close it.

  (2) IT CANNOT DISTINGUISH A HARNESS KILL FROM A SIGKILL AN OPERATOR SENT — nor does it need to.
      Both leave the SAME partial state, and neither produced a reading that was then discarded:
      the discrimination is the write-ordering, not the intent behind the kill.

  (3) IT DOES NOT RE-ESTABLISH BLINDNESS. The blindness is SPENT. Readings from the killed attempt
      are on screen and this rule does not pretend otherwise. All it says is that the continuation
      is the SAME attempt — never that it is a blind one.

  (4) IT IS SCOPED TO ONE FILENAME GLOB AND ONE SEED LADDER. A comparator under any other name is
      NOT REFUSED by this function, exactly as clause (4) of the frozen rule records for itself.

  (5) THIS MODULE IS NOT FROZEN, AND NOTHING FREEZES IT. `scripts/phase23_matched_prereg.py` is
      held EDIT-ONCE by `tests/test_phase23_matched_prereg.py`'s `_assert_ordering_holds` against
      `MATCHED_ARTIFACT_GLOB`. THIS MODULE CANNOT BE REGISTERED AGAINST THAT SAME GLOB: `adds[-1]`
      for that glob is `d99d2aa`, which PRECEDES any commit of this file, so the ancestry conjunct
      (`merge-base --is-ancestor prereg first_add`) can NEVER hold for it. What stands in for a
      freeze is strictly weaker and is named so: `test_the_resume_pin_has_exactly_one_commit`
      asserts this file has exactly ONE commit, so a second edit reddens the suite VISIBLY. That is
      DETECTION AFTER THE FACT, NOT PREVENTION, and it is not the ancestry guarantee the frozen pin
      carries. There is no override flag, no force flag and no warning branch here, and none is to
      be added regardless of how the run turns out.
"""


def prove_killed_run_continuation(
    *,
    tracked,
    ladder,
    trained_seeds,
    scored_seeds,
    committed_scored_seeds,
    record_exists,
):
    """ADMIT the continuation of a killed matched run. SEVEN NAMED CONJUNCTS, EIGHT REFUSALS.

    Keyword-only, so a caller cannot transpose ``trained`` with ``scored``. Every argument is a
    seed set, a seed ladder, a path list or a boolean; none is a reading. See the module docstring
    for why that is the whole independence argument.

    Conjunct 2 is SPLIT (2a/2b) because the two states it separates need two DIFFERENT messages:
    an EMPTY scored set is a FIRST attempt and ``prove_first_attempt``'s business, while a FULL one
    is a COMPLETED attempt and needs the write-ordering argument. One refusal cannot carry both.
    """
    ladder = tuple(ladder)
    tracked = list(tracked)
    trained = set(trained_seeds)
    scored = set(scored_seeds)
    committed = set(committed_scored_seeds)

    # ===== CONJUNCT 1 — the record is recorded evidence =====
    _prove(
        record_exists is False,
        f"{MATCHED_CONTROL_RECORD} ALREADY EXISTS. A continuation completes a run that never "
        "wrote its record; a run whose record is on disk has already published its readings, and "
        "`phase23_run.matched` refuses it independently. There is no force flag.",
    )

    # ===== CONJUNCT 2a — an empty scored set is a FIRST attempt, not a continuation =====
    _prove(
        len(scored) > 0,
        "NO SEED HAS SCORED, so this is not a continuation of anything — it is a FIRST ATTEMPT, "
        "and `phase23_matched_prereg.prove_first_attempt` is the rule that governs it. That rule "
        "is frozen, unedited and reached on its own branch with the real, unfiltered "
        "`git ls-files` result. This function must not be asked to admit a state it has no "
        "evidence about.",
    )

    # ===== CONJUNCT 2b — a COMPLETED attempt, refused by the WRITE-ORDERING argument =====
    _prove(
        len(scored) < len(ladder),
        f"ALL {len(ladder)} LADDER SEEDS HAVE SCORED: {sorted(scored)}. That is a COMPLETED "
        f"attempt, not a killed one.\n"
        "\n"
        "THE DISCRIMINATION IS THE RECORD'S WRITE-ORDERING AND NOTHING ELSE. "
        f"`phase23_run.matched` writes {MATCHED_CONTROL_RECORD} as its LAST act, AFTER the "
        "`for seed in seeds:` loop has scored EVERY seed in the ladder. A completed attempt "
        "therefore NECESSARILY leaves every ladder seed scored, and a scored set SHORTER than the "
        "ladder is a state the completion path CANNOT PRODUCE.\n"
        "\n"
        "Deleting a completed attempt's record does NOT un-score its seeds — "
        "`phase23_run._state_record` refuses to overwrite a recorded value at a different one — so "
        "to reach a short scored set the seed blocks would have to be deleted too, which is a "
        "VISIBLE DIFF against `git show HEAD:` and is what conjunct 5 compares. This refusal is "
        "the one that makes a deleted-and-re-run attempt inadmissible, and it is argued from the "
        "order the writer writes in, never from any reading.",
    )

    # ===== CONJUNCT 3 — a killed loop leaves a PREFIX of the ladder, in LADDER ORDER =====
    prefix = set(ladder[: len(scored)])
    _prove(
        scored == prefix,
        f"the scored seeds {sorted(scored)} are not the first {len(scored)} entries of the ladder "
        f"{list(ladder)}, which are {sorted(prefix)}. `phase23_run.matched` scores seeds "
        "SEQUENTIALLY in ladder order, so a killed run leaves a PROPER PREFIX. A scored set with a "
        "hole in it is a state the loop cannot produce, and a state nobody can explain is a state "
        "this rule does not admit.\n"
        "\n"
        "NOTE FOR A READER CHECKING THIS BY HAND: the ladder is NOT sorted, and `sorted(ladder)` "
        "is a DIFFERENT list. Compare SETS against a ladder PREFIX, never sorted lists against "
        "each other, and record the ladder in LADDER ORDER — this conjunct and conjunct 4 INDEX "
        "it.",
    )

    # ===== CONJUNCT 4 — at most ONE trained-but-unscored seed, and it is the NEXT one =====
    following = ladder[len(scored)]
    ahead = trained - scored
    _prove(
        scored <= trained and ahead in (set(), {following}),
        f"trained {sorted(trained)} against scored {sorted(scored)}: the trained-but-unscored set "
        f"is {sorted(ahead)}, which is neither empty nor exactly the NEXT ladder entry "
        f"[{following}]. `phase23_run.matched` trains and scores ONE seed at a time, so a kill can "
        "leave at most one seed trained and not yet scored, and it is the seed the ladder was "
        "about to reach. Anything else — a scored seed with no adapter, or two seeds running ahead "
        "— is a state the loop cannot produce.",
    )

    # ===== CONJUNCT 5 — the working tree agrees with HISTORY, and the remedy is an ORDERING =====
    _prove(
        scored == committed,
        f"THE WORKING TREE AND GIT HISTORY DISAGREE about which matched seeds have scored. The "
        f"working tree says {sorted(scored)}; `git show HEAD:` says {sorted(committed)}. Seeds in "
        f"the tree but not in history: {sorted(scored - committed)}. Seeds in history but not in "
        f"the tree: {sorted(committed - scored)}.\n"
        "\n"
        "THIS IS WHAT A HAND-EDITED STATE FILE LOOKS LIKE — AND IT IS ALSO WHAT A SECOND KILL "
        "LOOKS LIKE BEFORE ITS STATE IS COMMITTED. The two are not told apart here, and the second "
        "one is ordinary.\n"
        "\n"
        "THE REMEDY IS NOT A FLAG AND NOT A SECOND NARROWING. If a seed has just scored and the "
        "state file is not yet committed, COMMIT IT AND THE NEWLY COMPLETED SEED DIRECTORY FIRST, "
        "then re-launch:\n"
        "\n"
        "    git add data/phase23_run_state.json results/<the newly completed seed directory>\n"
        "    git commit -m 'run: <seed> completed'\n"
        "\n"
        "Now HEAD and the tree agree and this conjunct passes. Committing EARLIER makes the "
        "residual MORE auditable, not less: it lands the completed seeds in history sooner, which "
        "is exactly what the same-session commit discipline buys. Adding an override here would "
        "buy nothing except the ability to publish a state history cannot corroborate.",
    )

    # ===== CONJUNCT 6 — no RECORD may be in the tracked set =====
    records = [path for path in tracked if path in (MATCHED_CONTROL_RECORD, MATCHED_VERDICT_RECORD)]
    _prove(
        not records,
        f"a published RECORD is already tracked: {records}. The tracked set a continuation is "
        "admitted against may contain per-seed training curves and nothing else. A tracked record "
        "means a prior attempt PUBLISHED its readings, which is a completed attempt by another "
        "route, and conjunct 1 refuses it from the other side.",
    )

    # ===== CONJUNCT 7 — every tracked path is a per-seed run.csv for a seed the run has reached ==
    reachable = trained | {following}
    allowed = {seed_run_csv(seed): seed for seed in reachable}
    stray = [path for path in tracked if path not in allowed]
    _prove(
        not stray,
        f"tracked paths {stray} are not per-seed training curves for any seed this run has "
        f"reached. The admissible set is {sorted(allowed)} — one "
        "`results/{MATCHED_ARM_PREFIX}_{matched_arm(seed)}/run.csv` per seed in "
        f"trained | {{next}} = {sorted(reachable)}. A tracked artifact for a seed the loop has not "
        "reached, or a tracked path that is not a per-seed curve at all, is evidence of an attempt "
        "this rule has no account of.",
    )

    return True


# =================================================================================================
# ===== THE SELF-CHECK — every refusal WATCHED FIRING, against CONSTRUCTED inputs =====
#
# CONSTRUCTED THROUGHOUT and labelled so. **THIS SELF-CHECK OPENS NO FILE** and runs no subprocess,
# so it is TIME-INVARIANT: it reads the same on the day this module lands and after the run it
# governs has written five scored seeds into the driver's working state. A self-check that read
# that state would refuse itself the moment the run completed.
#
# The synthetic ladder below is DELIBERATELY NOT the production `phase23_run.SEED_LADDER` — it is
# five arbitrary seeds in a deliberately NON-SORTED order, which is the only property of the real
# ladder these conjuncts depend on. Retyping the real ladder here would make this module a second
# source for a fact `phase23_run.py` already owns; the production ladder is passed IN by the caller.
# =================================================================================================

if __name__ == "__main__":  # pragma: no cover - self-check, not a test suite
    _LADDER = (11, 44, 22, 55, 33)  # SYNTHETIC. Non-sorted, exactly as the real ladder is.
    _SCORED = frozenset(_LADDER[:3])
    _TRACKED = sorted(seed_run_csv(seed) for seed in _LADDER[:4])

    def _refused(**kwargs):
        try:
            prove_killed_run_continuation(**kwargs)
        except SystemExit as refusal:
            return str(refusal)
        raise SystemExit(
            "[phase23_resume_prereg] prove_killed_run_continuation did NOT refuse — the guard is "
            "a comment, not a mechanism"
        )

    def _case(**overrides):
        case = dict(
            tracked=_TRACKED,
            ladder=_LADDER,
            trained_seeds=_SCORED,
            scored_seeds=_SCORED,
            committed_scored_seeds=_SCORED,
            record_exists=False,
        )
        case.update(overrides)
        return case

    _prove(
        prove_killed_run_continuation(**_case()) is True,
        "the killed-run state was REFUSED — the rule admits nothing it exists to admit",
    )
    print(
        f"[phase23_resume_prereg] 0/9 ADMITTED the killed-run state: scored {sorted(_SCORED)} of "
        f"ladder {list(_LADDER)}, record absent, {len(_TRACKED)} tracked curve(s)"
    )

    _prove(
        prove_killed_run_continuation(**_case(trained_seeds=_SCORED | {_LADDER[3]})) is True,
        "a SECOND kill leaving one trained-but-unscored seed was refused",
    )
    print("[phase23_resume_prereg] 0b/9 ADMITTED a second kill (one trained, unscored, next seed)")

    _FOUR = frozenset(_LADDER[:4])
    _prove(
        prove_killed_run_continuation(
            **_case(
                trained_seeds=_FOUR,
                scored_seeds=_FOUR,
                committed_scored_seeds=_FOUR,
                tracked=sorted(seed_run_csv(seed) for seed in _LADDER[:4]),
            )
        )
        is True,
        "a FOUR-scored state whose state file HAS been committed was refused",
    )
    print("[phase23_resume_prereg] 0c/9 ADMITTED four scored, committed — the rule is on PREFIXES")

    _msg = _refused(**_case(record_exists=True))
    _prove("ALREADY EXISTS" in _msg, f"the record refusal omits its cause: {_msg!r}")
    print(f"[phase23_resume_prereg] 1/9 EXISTING RECORD REFUSED:\n{_msg}")

    _msg = _refused(
        **_case(
            trained_seeds=frozenset(),
            scored_seeds=frozenset(),
            committed_scored_seeds=frozenset(),
            tracked=[],
        )
    )
    _prove(
        "prove_first_attempt" in _msg, f"the empty-scored refusal misroutes the reader: {_msg!r}"
    )
    print(
        f"[phase23_resume_prereg] 2/9 EMPTY SCORED SET REFUSED (routed to the frozen rule):\n{_msg}"
    )

    _ALL = frozenset(_LADDER)
    _msg = _refused(
        **_case(
            trained_seeds=_ALL,
            scored_seeds=_ALL,
            committed_scored_seeds=_ALL,
            tracked=sorted(seed_run_csv(seed) for seed in _LADDER),
        )
    )
    _prove("WRITE-ORDERING" in _msg, f"the completed-attempt refusal omits the argument: {_msg!r}")
    print(f"[phase23_resume_prereg] 3/9 COMPLETED ATTEMPT REFUSED (write-ordering):\n{_msg}")

    _HOLE = frozenset({_LADDER[0], _LADDER[2]})
    _msg = _refused(**_case(trained_seeds=_HOLE, scored_seeds=_HOLE, committed_scored_seeds=_HOLE))
    _prove("PREFIX" in _msg, f"the non-prefix refusal omits the shape it wanted: {_msg!r}")
    print(f"[phase23_resume_prereg] 4/9 NON-PREFIX SCORED SET REFUSED:\n{_msg}")

    _msg = _refused(
        **_case(
            trained_seeds=_SCORED | {_LADDER[3], _LADDER[4]},
            tracked=sorted(seed_run_csv(seed) for seed in _LADDER),
        )
    )
    _prove("NEXT ladder entry" in _msg, f"the run-ahead refusal omits the bound: {_msg!r}")
    print(f"[phase23_resume_prereg] 5/9 TWO SEEDS RUNNING AHEAD REFUSED:\n{_msg}")

    _msg = _refused(**_case(committed_scored_seeds=frozenset(_LADDER[:2])))
    for _clause in ("git add data/phase23_run_state.json", "SECOND KILL", "NOT A FLAG"):
        _prove(_clause in _msg, f"the history-disagreement refusal omits {_clause!r}: {_msg!r}")
    print(
        "[phase23_resume_prereg] 6/9 TREE-vs-HISTORY DISAGREEMENT REFUSED (remedy carried):\n"
        f"{_msg}"
    )

    _msg = _refused(**_case(tracked=[*_TRACKED, MATCHED_CONTROL_RECORD]))
    _prove(MATCHED_CONTROL_RECORD in _msg, f"the tracked-record refusal omits the path: {_msg!r}")
    print(f"[phase23_resume_prereg] 7/9 TRACKED RECORD REFUSED:\n{_msg}")

    _UNREACHED = seed_run_csv(_LADDER[4])
    _msg = _refused(**_case(tracked=[*_TRACKED, _UNREACHED]))
    _prove(_UNREACHED in _msg, f"the unreached-seed refusal omits the path: {_msg!r}")
    print(f"[phase23_resume_prereg] 8/9 UNREACHED SEED'S CURVE REFUSED:\n{_msg}")

    _NOT_A_CURVE = "results/phase23_matched_control_seed11/notes.txt"
    _msg = _refused(**_case(tracked=[*_TRACKED, _NOT_A_CURVE]))
    _prove(_NOT_A_CURVE in _msg, f"the non-curve refusal omits the path: {_msg!r}")
    print(f"[phase23_resume_prereg] 9/9 NON-CURVE TRACKED PATH REFUSED:\n{_msg}")

    for _clause in ("(1)", "(2)", "(3)", "(4)", "(5)", "NOT FROZEN", "DETECTION AFTER THE FACT"):
        _prove(
            _clause in CONTINUATION_SCOPE.upper(),
            f"CONTINUATION_SCOPE omits {_clause!r} — a scope that omits a clause is the overclaim "
            "this register exists to refuse",
        )
    print(
        "[phase23_resume_prereg] CONTINUATION_SCOPE carries all FIVE clauses, (5) disclosing "
        "that this module is NOT FROZEN and its guard is DETECTION AFTER THE FACT"
    )
