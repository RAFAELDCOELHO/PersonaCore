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
import fnmatch
import hashlib
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import _verdict  # noqa: E402
import erasure_gate  # noqa: E402
import phase19_erasure as pin  # noqa: E402
import phase19_floor as floor  # noqa: E402
import phase19_run as p19run  # noqa: E402  — the two record-path constants only
import phase25_run  # noqa: E402  — atomic_write_json, the one os.replace writer
import phase35_prereg  # noqa: E402
import phase37_prereg as prereg  # noqa: E402
import phase37_routes as routes  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

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
    # WR-04: EQUAL, ordered, to the `- (a|b|c) ` lines of `### 1.` — a dropped reason must refuse.
    recorded = [
        line[2:]
        for line in section.split("### 2.")[0].splitlines()
        if re.match(r"- \([abc]\) ", line)
    ]
    _prove(
        list(got["reasons"]) == recorded,
        f"STOP: the reasons re-derive {got['reasons']!r}, not the recorded {recorded!r}",
    )
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


def write_record(derived, path, *, base, run):
    """Write ``derived`` to ``path`` ONCE: phase37 path, no overwrite, tracked prereg, clean."""
    path = pathlib.Path(path)
    rel = path.relative_to(base).as_posix()
    _prove(
        fnmatch.fnmatch(rel, prereg.RECORD_GLOB),
        f"{rel} does not match RECORD_GLOB {prereg.RECORD_GLOB!r}: R1a never writes Phase 19",
    )
    _prove(
        not path.exists(),
        f"{path} exists — REFUSING to overwrite it. The R1a record is write-once; corrections "
        "are dated continuations",
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "scripts/phase37_prereg.py"],
        cwd=_ROOT,
        capture_output=True,
    )
    _prove(
        tracked.returncode == 0,
        "the pre-registration scripts/phase37_prereg.py is not tracked: a record cannot precede it",
    )
    pathspec = ("scripts", "src", "results")
    if path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){path.relative_to(_ROOT).as_posix()}",)
    refuse_if_dirty(
        who="phase37_r1a",
        detail=(
            "the R1a record publishes git_sha and hashes its modules and input records from the "
            "working tree; a record written from a dirty tree names a commit it cannot be "
            "regenerated from"
        ),
        pathspec=pathspec,
        cwd=_ROOT,
    )
    record = {
        **derived,
        "input_sha256": {r: _sha256(_ROOT / r) for r in INPUT_RECORDS},
        "provenance": {
            "run": {
                key: run[key]
                for key in ("git_sha", "device", "torch_version", "started_utc", "finished_utc")
            },
            "module_sha256": {r: _sha256(_ROOT / r) for r in MODULES},
            "head_at_write": git_sha(),
            "written_utc": _now(),
        },
    }
    phase25_run.atomic_write_json(path, record)
    return record


def check_record(derived, path):
    """Verify an existing R1a record against a fresh derivation and fresh input digests."""
    record = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for key in ("assertions", "margin", "b_floor", "verdict", "reasons"):
        _prove(
            record.get(key) == derived[key],
            f"STOP: the record's {key} is {record.get(key)!r} but re-derives {derived[key]!r}",
        )
    fresh = {r: _sha256(_ROOT / r) for r in INPUT_RECORDS}
    _prove(
        record.get("input_sha256") == fresh,
        "STOP: an input record's bytes differ from the SHA-256 the R1a record holds",
    )
    return record


def main(argv=None, *, out_root=None):
    if argv:
        raise SystemExit(__doc__)
    base = pathlib.Path(out_root) if out_root is not None else _ROOT
    path = base / prereg.R1A_RECORD
    started = _now()
    derived = derive()
    finished = _now()
    if path.exists():
        check_record(derived, path)
        print(f"R1a REPRODUCED (record verified) {path}")
    else:
        import torch  # only for the provenance version string

        run = {
            "git_sha": git_sha(),
            "device": "cpu",
            "torch_version": torch.__version__,
            "started_utc": started,
            "finished_utc": finished,
        }
        write_record(derived, path, base=base, run=run)
        print(f"R1a REPRODUCED (record written) {path}")
    for key, value in derived["assertions"].items():
        print(f"  {key}: {value!r}")
    print(f"  margin: {derived['margin']!r}  b_floor: {derived['b_floor']!r}")
    print(f"  verdict: {derived['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
