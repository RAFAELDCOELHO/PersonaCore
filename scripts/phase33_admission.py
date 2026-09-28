"""Phase 33 admission driver (ADMIT-01, ADMIT-02): the frozen v5.0 admission contract, called once.

* ``admit`` calls ``phase29_prereg.admission`` on the committed ``results/phase32_frontier.json``
  and writes ``results/phase33_admission.json`` write-once. It refuses an existing record, then a
  record committed at HEAD but absent on disk, then a dirty tree, all before any digest. There is
  no ``--force``. It never commits: the developer reviews the printed block first (D-05).
* The four legs (``calibrate``, ``curve``, ``gate``, ``structural-proof``) are a REFUSAL SURFACE
  ONLY (D-01). The plan-time admission read MOOT, so no relearning body was built behind them.
  Every leg refuses, including on a forged ADMITTED record, and writes nothing.
* Everything the decision depends on is imported from ``phase29_prereg`` by reference (D-03);
  nothing here re-derives admission, the scope rule or the record path.

Torch-free at import. Never imports ``phase32_points`` (AR-32-02, D-12).
"""

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

# Never patched: the code this file ships in (module hashes read it).
_ROOT = pathlib.Path(__file__).resolve().parent.parent
# Patchable: the results repository (tests point it at a scratch repo).
_GIT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_budget  # noqa: E402  (scripts/ is not a package)
import mitigation_gate  # noqa: E402  (same)
import phase25_prereg  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same)
import phase27_prereg  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

INSTRUMENT_GIT_SHA = git_sha()

# Derived from the pre-registration's one path tuple, never typed (D-03, D-04).
RECORD_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase33_admission")
)
FRONTIER_PATH = next(
    p for p in phase29_prereg.V5_RESULT_PATHS if p.startswith("results/phase32_frontier")
)
DIRTY_PATHSPEC = ("scripts", "src", "results", f":(exclude){RECORD_PATH}")

# This module, the prereg, and the modules admission() reaches or reads constants from.
PINNED_MODULES = tuple(
    pathlib.Path(path).resolve().relative_to(_ROOT).as_posix()
    for path in (
        __file__,
        phase29_prereg.__file__,
        mitigation_gate.__file__,
        mitigation_budget.__file__,
        phase27_prereg.__file__,
        phase25_record.__file__,
        phase25_prereg.__file__,
    )
)

# (sub-command, requirement): mirrors Phase 27's sub-modes (D-16).
LEGS = (
    ("calibrate", "RELRN-09"),
    ("curve", "RELRN-06"),
    ("gate", "RELRN-07"),
    ("structural-proof", "RELRN-08"),
)

# The only unbound text in the limitation (D-08); every value in it is bound from the record.
_LEG_LINE = "{leg} measured: {counts} of {total}; admission verdict {verdict}"
_SURFACE_LINE = (
    "only the refusal surface exists: the advr relearning legs ({legs}) were not built because "
    "the scope rule read {verdict}"
)


def _prove(condition, message):
    """``SystemExit`` on a broken invariant. Never ``assert``: ``python -O`` strips it."""
    if not condition:
        raise SystemExit(f"[phase33_admission] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _inside(path):
    return pathlib.Path(path).resolve().is_relative_to(pathlib.Path(_GIT_ROOT).resolve())


def _rel(path):
    """Repo-relative posix path inside ``_GIT_ROOT``; the bare name outside it (no tmp path)."""
    path = pathlib.Path(path).resolve()
    if _inside(path):
        return path.relative_to(pathlib.Path(_GIT_ROOT).resolve()).as_posix()
    return path.name


def _committed(path):
    """Is ``path`` committed at HEAD? Reads HEAD, not the index, so a staged ``git rm`` still
    counts as committed. Outside ``_GIT_ROOT`` (or with no HEAD) it reads False."""
    if not _inside(path):
        return False
    done = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", f"HEAD:{_rel(path)}"],
        cwd=_GIT_ROOT,
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def _resolve(path):
    path = pathlib.Path(path)
    return path if path.is_absolute() else pathlib.Path(_GIT_ROOT) / path


def limitation(result, frontier, scope):
    """The MOOT named limitation, bound from admission()'s reasons, the frontier's per-leg
    tallies and the scope rule (D-08). A leg with its own reason carries it verbatim."""
    legs = {}
    for leg, tallies in sorted(frontier["verdicts"]["tallies_by_leg"].items()):
        own = [r for r in result["reasons"] if r.startswith(f"{leg} ")]
        if own:
            legs[leg] = own[0]
            continue
        legs[leg] = _LEG_LINE.format(
            leg=leg,
            counts=", ".join(f"{n} {key}" for key, n in sorted(tallies.items())),
            total=sum(tallies.values()),
            verdict=result["verdict"],
        )
    return {
        "legs": legs,
        "scope_rule": scope["rule"],
        "requirements": [req for _sub, req in LEGS],
        "surface": _SURFACE_LINE.format(
            legs=", ".join(sub for sub, _req in LEGS), verdict=scope["verdict"]
        ),
    }


def admit(out_path=RECORD_PATH):
    """THE ONE GATE CALL: write the admission record write-once, or refuse. Never commits."""
    out = _resolve(out_path)
    rel = _rel(out)
    _prove(
        not out.exists(),
        f"{rel} exists — REFUSING to overwrite it. The only route is to delete it in its own "
        "commit (D-06); there is no --force",
    )
    _prove(
        not _committed(out),
        f"{rel} is tracked but absent — REFUSING: it is committed at HEAD; commit the deletion "
        "on its own first (D-13)",
    )
    refuse_if_dirty(
        who="phase33_admission",
        detail=(
            "admit publishes git_sha and hashes the gate modules and the frontier from the working "
            "tree; a record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=DIRTY_PATHSPEC,
        cwd=_GIT_ROOT,
    )
    frontier_file = pathlib.Path(_GIT_ROOT) / FRONTIER_PATH
    _prove(_committed(frontier_file), f"{FRONTIER_PATH} is not committed at HEAD — REFUSING")
    raw = frontier_file.read_bytes()
    frontier = json.loads(raw)
    result = phase29_prereg.admission(frontier)
    scope = phase29_prereg.relearning_scope(result)
    blob = {
        "admission": result,
        "scope": scope,
        "frontier": {
            "path": FRONTIER_PATH,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
        "provenance": {
            "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PINNED_MODULES},
            "git_sha": INSTRUMENT_GIT_SHA,
            "head_at_write": git_sha(),
            "prereg_committed": phase29_prereg.COMMITTED,
        },
        "limitation": limitation(result, frontier, scope),
    }
    phase25_run.atomic_write_json(out, blob)
    review = {
        "verdict": result["verdict"],
        "reasons": result["reasons"],
        "scope_rule": scope["rule"],
        "control_readings": result["control_readings"],
    }
    print(json.dumps(review, indent=1), flush=True)
    print(f"[phase33_admission] wrote {rel}", flush=True)
    print("(NOT committed; D-05 developer review first)", flush=True)
    return blob


def refuse_leg(record_path=RECORD_PATH):
    """Every leg's whole body (D-01). Order exists -> verdict -> committed keeps the message on
    the real MOOT record identical before and after its commit (D-02)."""
    path = _resolve(record_path).resolve()
    rel = _rel(path)
    _prove(
        path.exists(),
        f"{rel} is absent — REFUSING to run this leg: run `admit` first; every leg is gated on "
        "the COMMITTED admission record",
    )
    verdict = json.loads(path.read_text(encoding="utf-8"))["admission"]["verdict"]
    _prove(
        verdict in phase29_prereg.VERDICTS,
        f"{rel} reads {verdict!r}, not a phase29_prereg verdict — REFUSING",
    )
    _prove(
        verdict == "ADMITTED",
        f"{rel} reads {verdict!r} — REFUSING to run this leg: "
        f"{phase29_prereg.SCOPE_RULE[verdict]}; only the refusal surface exists",
    )
    if _inside(path):
        _prove(
            _committed(path),
            f"{rel} is not tracked at HEAD — REFUSING: a leg runs only against the COMMITTED "
            "admission record",
        )
    raise SystemExit(
        "[phase33_admission] REFUSING: the relearning legs were not built (plan-time admission "
        "read MOOT, D-01); no leg body exists"
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="phase33_admission.py",
        description="Phase 33: admit once; the four legs are a refusal surface only.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    admit_parser = sub.add_parser("admit", help="write the admission record once; never commits")
    admit_parser.add_argument("--out", default=RECORD_PATH)
    for leg, requirement in LEGS:
        leg_parser = sub.add_parser(leg, help=f"{requirement}: refuses (no leg body exists)")
        leg_parser.add_argument("--record", default=RECORD_PATH)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "admit":
        admit(out_path=args.out)
    else:
        refuse_leg(record_path=args.record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
