"""Phase 37 R1a (REPRO-01) — the Phase 19 verdict re-derived from committed records, one command.

    .venv/bin/python scripts/phase37_r1a.py        # CPU, seconds, no checkpoint

It re-derives the verdict from the committed erased arm through `phase37_routes.rederive` (the
pin's own functions fed the corrected inputs of defects A-D, the ONE `pin.render_verdict`) and
asserts EXACTLY the four REPRO-01 numbers of `phase35_prereg.R1A_ASSERTIONS`: k, the target's
correct/questions, the non-targets beyond `phase35_prereg.e1_condition_b_margin()`, and the
destroyed percentage of the dialogue on-off gap. It also re-derives the (b) noise floor from the
replicate arm (D-13) and checks the FAILURE verdict and its reasons against the recorded
`## Verdict` of results/phase19_erasure_report.md.

A divergence is a STOP for a root-cause investigation — never an adjustment (D-10). It names the
key, the re-derived value and the asserted one, and nothing is written.

On success it writes `results/phase37_r1a.json` ONCE (clean tree, tracked pre-registration, input
records hashed from their bytes) and, once that record exists, re-derives and VERIFIES it instead of
writing, so an outsider's run exits 0. It never calls `phase19_run.report()` and never writes a
Phase 19 path. It takes no arguments.
"""

import datetime
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import _verdict  # noqa: E402
import erasure_gate  # noqa: E402
import phase19_erasure as pin  # noqa: E402
import phase19_floor as floor  # noqa: E402
import phase19_run as p19run  # noqa: E402  — the two record-path constants only
import phase35_prereg  # noqa: E402
import phase37_routes as routes  # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Every record R1a reads, derived from the pin's / driver's own constants (never typed).
INPUT_RECORDS = tuple(
    pathlib.Path(p).resolve().relative_to(_ROOT).as_posix()
    for p in (
        pin.arm_record_path("erased"),
        pin.arm_record_path("replicate"),
        pin.PHASE18_ARM_RECORD_PATH,
        pin.DIALOGUE_FLOOR_RECORD_PATH,
        p19run.NOISE_FLOORS_PATH,
        p19run.CALIBRATION_CORRECTION_PATH,
        pin.ERASURE_REPORT_PATH,
    )
)

MODULES = (
    "scripts/phase19_erasure.py",
    "scripts/erasure_gate.py",
    "scripts/phase19_run.py",
    "scripts/phase35_prereg.py",
    "scripts/phase37_prereg.py",
    "scripts/phase37_routes.py",
    "scripts/phase37_r1a.py",
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase37_r1a] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def derive(erased=None):
    """REPRO-01 on ``erased`` (default: the committed erased arm). SystemExit on any divergence."""
    committed = erased is None
    if committed:
        erased = json.loads(pin.arm_record_path("erased").read_text(encoding="utf-8"))
    got = routes.rederive(erased)
    for key, expected in phase35_prereg.R1A_ASSERTIONS.items():
        value = tuple(got[key]) if isinstance(expected, tuple) else got[key]
        _prove(
            value == expected,
            f"STOP: {key} re-derives {value!r} but R1a asserts {expected!r}. "
            "Investigate the root cause; never adjust (D-10)",
        )
    _prove(
        got["margin"] == erasure_gate.MARGIN_K * floor.NONTARGET_NOISE_FLOOR,
        f"STOP: the (b) margin {got['margin']!r} is not MARGIN_K x the locked (b) floor",
    )
    if committed:
        cross = phase35_prereg.r1a_rederive()
        for key in ("k", "destroyed_pct", "margin"):
            _prove(
                got[key] == cross[key],
                f"STOP: {key} is {got[key]!r} through the routes but {cross[key]!r} through "
                "phase35_prereg.r1a_rederive",
            )
    b_floor = routes.b_floor_from_replicate()  # D-13
    section = _verdict.recorded_verdict(pin.ERASURE_REPORT_PATH.read_text(encoding="utf-8"))
    _prove(section is not None, f"{pin.ERASURE_REPORT_PATH} has no `## Verdict` section")
    _prove(
        f"**{got['verdict']}**" in section,
        f"STOP: the verdict re-derives {got['verdict']!r}, not the recorded one",
    )
    for reason in got["reasons"]:
        _prove(f"- {reason}\n" in section, f"STOP: reason {reason!r} is not a recorded reason")
    return {
        "assertions": {key: got[key] for key in phase35_prereg.R1A_ASSERTIONS},
        "margin": got["margin"],
        "b_floor": b_floor,
        "verdict": got["verdict"],
        "reasons": got["reasons"],
        "target_fact_id": got["target_fact_id"],
        "nontarget_deltas_by_slot": got["nontarget_deltas_by_slot"],
        "routes": {
            **{letter: "phase37_routes." + fn.__name__ for letter, fn in routes.ROUTES.items()},
            "E": "phase37_routes.select_target_prefix",
        },
    }
