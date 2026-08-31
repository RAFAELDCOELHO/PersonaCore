"""D-16'S STALL WATCHER — IT DETECTS, AND IT IS STRUCTURALLY UNABLE TO ACT.

The v4.0 frontier sweep runs 4.5–6.3 days unattended as a user LaunchAgent with **`KeepAlive`
FALSE** (D-12). That flag is not a convenience: an automatic restart would re-enter a sweep point
WITHOUT passing the driver's deliberate resume logic, and D-10's one-attempt rule — whose unit is
the sweep point — would be violated by a supervisor rather than by a person. So nothing in this
system is allowed to relaunch the sweep.

**This module therefore exists to make a kill DIAGNOSABLE, not RECOVERABLE.** It reads the
heartbeat, and on silence it writes one timestamped stall record and stops. It does not `kill`, it
does not `terminate`, it does not `Popen`, it does not shell out to `launchctl`, it does not
`unlink` a lock file and it does not clean up a half-written cache. Detection and correction stay
in different processes operated by different agents — one of them a human.

**THAT SEPARATION IS ONE LINE OF CODE AWAY FROM COLLAPSING, WHICH IS WHY IT IS NOT DEFENDED BY
PROSE.** `FORBIDDEN_ACTIONS` below is enforced by `tests/test_phase25_watch.py
::test_the_watcher_takes_no_action`, an **AST walk over this very file** that collects every
identifier appearing in a CALL position and refuses any member of that tuple. The check is
deliberately not implemented here: a module that checks itself proves nothing, because the same
edit that adds the action can weaken the check. It also cannot be a grep — the paragraph you are
reading names `kill` and `launchctl` on purpose, so a textual gate over this file goes false-RED
today. Only a parse tells prose about a name from the name (`tests/test_phase24_correction.py`'s
mechanic 4; `.planning/REQUIREMENTS.md`'s RPT-02 row records four independent instances of that
false-RED class in Phase 20 alone).

**N IS AN OUTPUT OF MEASUREMENT, AND THE MEASUREMENT SAYS SOMETHING SURPRISING.** D-16 asks for the
worst-case gap between heartbeat lines at the slowest attack shape. Measured, that is A3 at
**3.78 min** (seed 1337, K=16). But the true worst case **is not in the draw loop at all**:
`dp_n64` training runs **23.05 min emitting no per-shape line whatsoever**. An event-driven beat
tied to the existing prompt counter (`scripts/phase23_run.py:4524`, one line per 24 prompts) would
therefore have to be set coarser than that training leg or it false-fires on all **22** n=64
training legs — pushing N into a measured **28.08–38.15 min** envelope, roughly **7×** coarser than
the draw loop's own 5.03-min ceiling-regime resolution, and buying nothing.

So the beat is a **wall-clock 60 s timer in the driver's OUTER loop**, whose sampling rate is
independent of which stage is running, and `STALL_THRESHOLD_MINUTES = 5` means *five missed beats*
rather than *five minutes of draw-loop silence*. `N_DERIVATION` carries that whole table as DATA
rather than as this paragraph, pinned at full precision and re-derived from
`results/phase23_cost.json` by the test — asserted against its sources, never against itself.

CPU-only, GPU-free, stdlib only. This watcher runs beside a saturated GPU for six days and must
cost nothing: no torch, no numpy, no network, and — load-bearing — **no `subprocess`**.
"""

import argparse
import datetime
import json
import pathlib

# =================================================================================================
# ===== (a) THE CONTRACT, PINNED AS DATA =====
# =================================================================================================

# The beat's period. Read `HEARTBEAT_SECONDS_PROVENANCE` before changing it: the number is only
# meaningful together with WHERE the beat is emitted from.
HEARTBEAT_SECONDS = 60

HEARTBEAT_SECONDS_PROVENANCE = {
    "emitted_from": (
        "the driver's OUTER loop, on a wall-clock timer — never from the draw loop, never from a "
        "prompt counter and never from a per-shape callback"
    ),
    "governs": (
        "THE SAMPLING RATE OF THE STALL SIGNAL, AND NOTHING ELSE. It selects no K, sizes no run "
        "and renders no verdict. It does not throttle, pace or gate the sweep in any way — the "
        "driver emits a line and continues"
    ),
    "why_wall_clock_and_not_event_driven": (
        "A wall-clock beat's period is INDEPENDENT OF WHICH STAGE IS RUNNING, so a 23-minute "
        "training leg and a 0.4-minute draw block are sampled identically. An event-driven beat "
        "inherits the stage's own timescale, and the measured spread between those timescales is "
        "60x — see N_DERIVATION['event_driven_alternative']"
    ),
    "missed_beats_at_threshold": 5,
    "missed_beats_rule": (
        "STALL_THRESHOLD_MINUTES * 60 / HEARTBEAT_SECONDS. N is stated in MINUTES because the "
        "operator reads it in minutes, and in MISSED BEATS because that is what the watcher "
        "actually counts"
    ),
}

# The five fields every beat carries. `point`, `stage`, `shape` and `draw_index` are the diagnostic
# payload: they are what turns "it died" into "it died HERE", and the stall record copies all five
# verbatim rather than summarising them.
HEARTBEAT_FIELDS = ("utc", "point", "stage", "shape", "draw_index")

# N. Five missed 60-second beats. Derived below, not chosen.
STALL_THRESHOLD_MINUTES = 5

N_DERIVATION = {
    "governs": (
        "WHEN A STALL RECORD IS WRITTEN, AND NOTHING ELSE. It triggers no restart, kills no "
        "process, deletes no cache and changes no sweep parameter. A stall record is a note for a "
        "human, so N's only cost of being wrong is a false note or a late one"
    ),
    "requirement": (
        "D-16: 'N is derived from the measured worst-case gap between heartbeat lines at the "
        "slowest attack shape, not chosen by convention.'"
    ),
    # -----------------------------------------------------------------------------------------
    # The cadence the contract deliberately does NOT use, named so the counterfactual is checkable.
    # -----------------------------------------------------------------------------------------
    "existing_event_cadence_source": "scripts/phase23_run.py:4524",
    "existing_event_cadence": "if (index + 1) % 24 == 0 or index + 1 == len(cell)",
    "prompts_per_printed_line": 24,
    # -----------------------------------------------------------------------------------------
    # REGIME 1 — MEASURED. Real draws, real EOS behaviour, seed 1337, K=16, 216 prompts/shape.
    # This is the regime D-16's words point at, and it is what N is set above.
    # -----------------------------------------------------------------------------------------
    "measured_seed1337": {
        "record": "data/phase23_never_taught_seed1337_draws.json",
        "path": "shapes[*].timing",
        "k": 16,
        "prompts_per_shape": 216,
        "shape_minutes": {
            "A3": 34.03443515971303,
            "A1-aggressive": 32.731153954161954,
            "A1-mild": 29.013322102076685,
            "A2": 26.46837622569874,
        },
        "gap_24_prompt_minutes": {
            "A3": 3.7816039066347806,
            "A1-aggressive": 3.6367948837957726,
            "A1-mild": 3.2237024557862983,
            "A2": 2.9409306917443048,
        },
        "rule": "timing.minutes * 24 / timing.prompts",
        "worst_shape": "A3",
    },
    # THE MEASURED WORST CASE — the number D-16 names. N sits ABOVE it.
    "worst_24_prompt_gap_measured_minutes": 3.7816039066347806,
    # -----------------------------------------------------------------------------------------
    # REGIME 2 — THE NO-EOS CEILING. `phase23_cost.json`'s bracket assumes NOTHING stops early
    # (`stop_terminated_n_ceiling: 0`), so every draw runs to `mean_tokens_ceiling: 48`. This is a
    # BOUND, not a rate — but it is the bound an event-driven beat would have to survive.
    # -----------------------------------------------------------------------------------------
    "ceiling_no_eos": {
        "record": "results/phase23_cost.json",
        "path": "generation.per_shape[*].draws_per_min_ceiling",
        "k": 16,
        "prompts_per_shape": 216,
        "shape_minutes": {
            "A1-mild": 45.27308433651924,
            "A3": 43.82077188855037,
            "A1-aggressive": 43.52801223797724,
            "A2": 43.25040738768876,
        },
        "gap_24_prompt_minutes": {
            "A1-mild": 5.030342704057693,
            "A3": 4.868974654283375,
            "A1-aggressive": 4.836445804219693,
            "A2": 4.805600820854306,
        },
        "rule": "24 * k / draws_per_min_ceiling",
        "worst_shape": "A1-mild",
    },
    # THE CEILING WORST CASE. Note it is ABOVE N — see `why_the_draw_gaps_do_not_bound_n`.
    "worst_24_prompt_gap_ceiling_minutes": 5.030342704057693,
    # -----------------------------------------------------------------------------------------
    # REGIME 3 — D-11's promotion. Candidates clearing all three conditions are re-drawn at
    # `FULL_FIDELITY_K = 48`, which triples the gap at a stroke.
    # -----------------------------------------------------------------------------------------
    "full_fidelity_projection": {
        "k": 48,
        "k_source": "mitigation_budget.FULL_FIDELITY_K, promoted by D-11",
        "rule": "24 * 48 / draws_per_min_ceiling, worst shape",
        "worst_shape": "A1-mild",
        "worst_24_prompt_gap_minutes": 15.091028112173081,
    },
    # -----------------------------------------------------------------------------------------
    # THE TRUE WORST CASE, AND IT IS NOT IN THE DRAW LOOP. Training emits no per-shape line at all.
    # -----------------------------------------------------------------------------------------
    "training_legs": {
        "record": "results/phase23_cost.json",
        "path": "training.{dp_n8,dp_n64}.seconds_total",
        "dp_n8_seconds": 205.44225783273578,
        "dp_n64_seconds": 1383.276182374917,
        "per_shape_lines_emitted": 0,
        "why_zero": (
            "the per-shape line is printed by the DRAW loop. `train_arm` runs before any draw "
            "exists, so an event-driven beat is silent for the whole leg"
        ),
    },
    "dp_n8_training_minutes": 3.4240376305455964,
    "dp_n64_training_minutes": 23.05460303958195,
    # -----------------------------------------------------------------------------------------
    # THE CONCLUSION, AS A FIELD RATHER THAN A PARAGRAPH.
    # -----------------------------------------------------------------------------------------
    "event_driven_alternative": {
        "n64_training_legs": 22,
        "n64_training_legs_composition": (
            "16 sigma points + 6 ADVERSARIAL_RATIO_GRID ratios at n=64. D-08's 44 points are "
            "2 x (16 + 6), so exactly half of them carry a dp_n64-scale training leg"
        ),
        "max_silence_rule": (
            "dp_n64_training_minutes + the FIRST 24-prompt gap after training resumes — the leg "
            "emits nothing, and the beat that ends the silence only lands 24 prompts later"
        ),
        "max_silence_at_curve_k_minutes": 28.084945743639643,
        "max_silence_at_full_fidelity_k_minutes": 38.145631151755026,
        "minimum_threshold_minutes_envelope": (28.084945743639643, 38.145631151755026),
        "stated_round_figure_minutes": 35,
        "stated_round_figure_status": (
            "A ROUND FIGURE INSIDE THE MEASURED ENVELOPE, NOT ITSELF A MEASUREMENT. 35 sits "
            "between the K=16 and K=48 bounds above and is 6.96x the ceiling gap; the envelope "
            "ends are 5.58x and 7.58x. The envelope is the measured statement and the round "
            "figure is the one a human quotes — both are recorded so neither is mistaken for the "
            "other"
        ),
        "coarser_than_ceiling_gap_factor_envelope": (5.583107831000283, 7.583107831000282),
        "coarser_denominator": "worst_24_prompt_gap_ceiling_minutes",
        "conclusion": (
            "An event-driven beat tied to the prompt counter would force N >= ~35 min to avoid "
            "firing on all 22 n=64 training legs — about 7x coarser than the draw loop can itself "
            "resolve, and it buys nothing. That is WHY the beat is a wall-clock timer in the "
            "outer loop and why N is 5 missed beats rather than 5 minutes of draw-loop silence"
        ),
    },
    "why_the_draw_gaps_do_not_bound_n": (
        "N BOUNDS MISSED WALL-CLOCK BEATS, NOT DRAW-LOOP LINES, and the measurement is what forces "
        "that distinction rather than decorating it. N = 5 sits ABOVE the measured worst gap "
        "(3.78 min) but BELOW the no-EOS ceiling gap (5.03 min) and far below the K=48 projection "
        "(15.09 min). Under an EVENT-driven beat, N = 5 would therefore false-fire in the ceiling "
        "regime and on every promoted K=48 shape. Under the WALL-CLOCK beat it fires on neither, "
        "because the driver emits a line every 60 s regardless of stage. The window the wall-clock "
        "beat exists to open is (3.78, 23.05) — above the measured draw gap, below the dp_n64 "
        "training leg — and 5 is inside it"
    ),
    # -----------------------------------------------------------------------------------------
    # WHAT N COSTS WHEN IT IS TOO COARSE: the detection latency, against the run's own envelope.
    # -----------------------------------------------------------------------------------------
    "run_envelope_hours": (107.0, 150.0),
    "run_envelope_source": "25-VALIDATION.md — ~107 h at the measured rate, ~150 h at the ceiling",
    # Worst case = the SHORTEST run, where 5 minutes is the largest share of the whole.
    "detection_latency_fraction_of_run": 0.000778816199376947,
    "detection_latency_fraction_rule": (
        "STALL_THRESHOLD_MINUTES / (107 h * 60), the SHORTEST run in the envelope, because that is "
        "where the latency is the largest fraction of the whole"
    ),
    "detection_latency_percent_envelope": (0.05555555555555555, 0.0778816199376947),
    "detection_latency_note": (
        "0.056%-0.078% of a 107-150 h sweep — recomputed here rather than carried over. "
        "25-VALIDATION.md quotes '0.005%' for the same quantity; that reading is ~14x too small "
        "(5 / (107 * 60) = 7.8e-4, i.e. 0.078%, not 5e-5). The conclusion is unchanged and in the "
        "same direction: the latency is negligible against the run either way"
    ),
}


# =================================================================================================
# ===== (b) READING THE HEARTBEAT — READ ONLY, ALWAYS =====
# =================================================================================================


def read_last_beat(heartbeat_path):
    """The last COMPLETE beat in the heartbeat file, or ``None``.

    **The file is opened READ-ONLY and this module never writes to it.** The heartbeat is the
    driver's own record; a watcher that edits it destroys the one artifact that says where the run
    died (threat T-25-24).

    **A TRUNCATED FINAL LINE IS EXPECTED, NOT EXCEPTIONAL — AND IT IS WHY THE HEARTBEAT IS
    LINE-ORIENTED AND APPEND-ONLY RATHER THAN A REWRITTEN JSON BLOB.** The interesting case for
    this whole module is a process killed mid-write, so the very last bytes on disk are the ones
    most likely to be half a line. With append-only lines, a torn tail costs at most the newest
    beat and every earlier beat is still parseable — this function simply walks backwards to the
    previous complete line. With a rewritten blob, the same kill leaves a file `json.loads`
    rejects outright, and the diagnostic value of every beat ever written is lost at once. That is
    exactly the `_never_taught_write_draws` failure mode 25-VALIDATION.md calls out, and the
    heartbeat is shaped to be immune to it.

    Returns ``None`` when no complete beat exists yet — an empty heartbeat is the normal state
    between the LaunchAgent starting and the driver's first beat, so it is not a stall.
    """
    text = pathlib.Path(heartbeat_path).read_text(encoding="utf-8")
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            beat = json.loads(line)
        except ValueError:
            # A torn tail. Keep walking backwards to the previous complete line.
            continue
        if isinstance(beat, dict) and "utc" in beat:
            return beat
    return None


# =================================================================================================
# ===== (c) THE CHECK — ITS ONLY EFFECT IS ONE APPENDED LINE =====
# =================================================================================================

NO_ACTION_REASON = (
    "D-16: heartbeat silence is DETECTED, never ACTED ON. An automatic restart would re-enter a "
    "sweep point WITHOUT passing the driver's deliberate resume logic, making a supervisor — not a "
    "person — the thing that violates D-10's one-attempt rule. The LaunchAgent therefore runs with "
    "KeepAlive FALSE (D-12) and this watcher cannot kill, relaunch or clean up anything. "
    "Correcting a stall is a human act, taken after reading this record."
)


def check(heartbeat_path, *, stall_record_path, now):
    """Detect silence past ``STALL_THRESHOLD_MINUTES`` and record it. Return the record or ``None``.

    ``now`` is INJECTED rather than read from the clock, so the test observes the boundary without
    sleeping and the operator, the LaunchAgent and the test all execute this same function.

    **A DETECTED STALL IS A SUCCESSFUL RUN OF THE WATCHER.** This returns normally and ``main``
    exits 0. A non-zero exit would make a LaunchAgent-managed watcher look like a crashing job and
    invite exactly the automatic remediation D-16 forbids (threat T-25-25).

    **The append is this function's ONLY side effect.** It writes to ``stall_record_path`` and to
    nothing else — not the heartbeat, not a lock file, not a literal path — and it APPENDS rather
    than overwrites, so a six-day silence leaves a history rather than a single point (T-25-22).
    """
    beat = read_last_beat(heartbeat_path)
    if beat is None:
        return None

    silence_minutes = (now - datetime.datetime.fromisoformat(beat["utc"])).total_seconds() / 60.0
    if silence_minutes < STALL_THRESHOLD_MINUTES:
        return None

    record = {
        "detected_utc": now.isoformat(),
        "heartbeat": str(heartbeat_path),
        # All five fields VERBATIM. `point`, `stage`, `shape` and `draw_index` are *where* it died,
        # which is the entire diagnostic value of the record.
        "last_beat": {field: beat.get(field) for field in HEARTBEAT_FIELDS},
        "silence_minutes": silence_minutes,
        "stall_threshold_minutes": STALL_THRESHOLD_MINUTES,
        "heartbeat_seconds": HEARTBEAT_SECONDS,
        "missed_beats": silence_minutes * 60.0 / HEARTBEAT_SECONDS,
        # The literal. A record that merely omits an action field would be read as an oversight.
        "action_taken": "none",
        "action_taken_reason": NO_ACTION_REASON,
    }
    with stall_record_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


# =================================================================================================
# ===== (d) THE OPERATOR AND THE LAUNCHAGENT RUN THE SAME CODE THE TEST RUNS =====
# =================================================================================================


def main(argv=None):
    """``--heartbeat`` / ``--stall-record`` / optional ``--now``. Exit 0, stalled or not."""
    parser = argparse.ArgumentParser(
        description=(
            "D-16's stall watcher: read the sweep heartbeat, and on silence past "
            "STALL_THRESHOLD_MINUTES append one stall record. It takes no other action, by "
            "construction — see FORBIDDEN_ACTIONS."
        )
    )
    parser.add_argument("--heartbeat", required=True, help="the driver's append-only beat file")
    parser.add_argument("--stall-record", required=True, help="the watcher's ONLY output path")
    parser.add_argument(
        "--now",
        default=None,
        help="ISO-8601 detection time; defaults to the current UTC clock",
    )
    args = parser.parse_args(argv)

    now = (
        datetime.datetime.fromisoformat(args.now)
        if args.now
        else datetime.datetime.now(datetime.timezone.utc)
    )
    record = check(
        pathlib.Path(args.heartbeat),
        stall_record_path=pathlib.Path(args.stall_record),
        now=now,
    )
    if record is None:
        print(f"[phase25_watch] alive — no silence past {STALL_THRESHOLD_MINUTES} min")
    else:
        last = record["last_beat"]
        print(
            f"[phase25_watch] STALL — {record['silence_minutes']:.2f} min of silence past "
            f"{STALL_THRESHOLD_MINUTES} min. Last beat: point {last['point']!r}, stage "
            f"{last['stage']!r}, shape {last['shape']!r}, draw_index {last['draw_index']!r} at "
            f"{last['utc']!r}. action_taken: {record['action_taken']!r} — recorded in "
            f"{args.stall_record}"
        )
    return 0


# =================================================================================================
# ===== (e) THE SELF-IMPOSED PROHIBITION =====
# =================================================================================================

# THE PROPERTY MOST LIKELY TO ROT. Every one of these is a plausible, well-meaning single-line
# addition to a watcher — "just restart it", "just clear the stale lock" — and every one of them
# converts a detector into a remediator and violates D-10 (threat T-25-21). None may appear in a
# CALL position anywhere in this module.
FORBIDDEN_ACTIONS = ("kill", "terminate", "Popen", "run", "launchctl", "unlink", "rmtree", "remove")

FORBIDDEN_ACTIONS_ENFORCEMENT = (
    "ENFORCED FROM OUTSIDE THIS FILE, BY AST, at `tests/test_phase25_watch.py"
    "::test_the_watcher_takes_no_action`. Not implemented here: a module that checks itself proves "
    "nothing, because the edit that adds the action is free to weaken the check in the same diff. "
    "Not a grep either: this module's own docstrings name `kill` and `launchctl` deliberately, so "
    "a textual gate over it goes FALSE-RED today — only a parse can tell prose about a name from "
    "the name. The guard is itself watched failing, against a scratch copy in `tmp_path` carrying "
    "a planted `launchctl` call; the real file is never mutated."
)


if __name__ == "__main__":
    raise SystemExit(main())
