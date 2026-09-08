"""PLAN 25-18 TASK 0 (Rule 4 deviation, D-25-18-RECALL) — condition (b)'s missing producer.

MEASURED 2026-09-08 over the 44 committed point records: only the two DP sigma=0 controls carry
``taught_recall`` / ``heldout_recall``. ``scripts/phase25_points.py::measure_stage`` scores recall
under ``if plan["is_control"]:`` only, and ``25-14-SUMMARY.md`` line 162 states the false premise
that 25-18 "consumes ... the control's ``taught_recall``" — the frozen pin
``mitigation_gate.mitigation_point_verdict`` takes ``point_taught_recall`` and
``point_heldout_recall`` PER POINT, and ``phase25_verdict.POINT_RECORD_FIELDS`` requires both on
every record. So 42/44 verdicts were uncomputable and the plan's plan-time "measured live on one
point" used fabricated recall values (``tests/test_phase25_verdict.py::_full_kwargs``).

THE OPERATOR DECIDED (2026-09-08): score ALL 42 unscored adapters — never a subset, because a subset
chosen after seeing extraction is the reduction this milestone forbids — with the SAME instrument
the controls used, ``teach_persona.score_arm(arm, fs.LOCKED_FACTS, adapter, device)``, BEFORE any
verdict is seen. Estimated from the controls' own ``scoring_seconds`` (914.5 s at n=8, 1070.4 s at
n=64): 21 x 914.5 + 21 x 1070.4 = 11.58 h of MPS time. The point records stay BYTE-UNCHANGED; the
readings land in ``results/phase25_recall.json``, keyed by point, each entry pinned to the adapter's
sha256 the record already carries. All 44 adapters are on disk and hash to their records.

SURVIVABILITY, PORTED FROM THE SWEEP DRIVER (25-10 / 25-14), CALLED NEVER RE-IMPLEMENTED:
``phase25_run.atomic_write_json`` for every sidecar and for the artifact; ``phase25_run.beat`` /
``start_heartbeat`` for the wall-clock beat in the five-field shape ``phase25_watch`` reads, into
the SAME ``data/phase25_heartbeat.jsonl`` the watcher already polls; ``phase25_run.device`` for the
preflighted device. One gitignored sidecar per point under ``data/`` so a kill costs at most one
point; a relaunch reuses a sidecar only if its ``adapter_sha256`` equals the record's, and REFUSES
one that differs. The order is ``ORDERED_POINT_KEYS()``.

CPU-safe at import: torch and every model module are imported inside the one function that scores.
``--dry-run`` exercises every structural path without touching the device; ``--emit`` assembles the
artifact from the 42 sidecars plus the 2 records and asserts set equality against the pinned 44.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_prereg  # noqa: E402  (scripts/ is not a package)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same — CPU-safe at import; torch stays lazy)
import phase25_venue  # noqa: E402  (same)

from personacore.provenance import git_sha  # noqa: E402

RECORD = _ROOT / "results" / "phase25_recall.json"
SIDECAR_DIR = _ROOT / "data"
INSTRUMENT = "teach_persona.score_arm"
RECALL_FIELDS = ("taught_recall", "heldout_recall", "taught_recall_off", "heldout_recall_off")
SOURCE_POINT_RECORD = "point_record"

DEVIATION = (
    "Rule 4 (D-25-18-RECALL): condition (b) had no per-point producer — the sweep driver scored "
    "recall only under is_control, so 42/44 records lack taught/heldout recall. Decided by the "
    "operator 2026-09-08 to score all 42 adapters (never a subset) at ~11.6 h MPS before any "
    "verdict is seen. Point records byte-unchanged; this artifact is keyed by point and pinned "
    "to each record's adapter_sha256."
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase25_recall] {message}")


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    """Repo-relative when inside the root; the path as given otherwise (tests use tmp dirs)."""
    path = pathlib.Path(path)
    return str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)


def sidecar_path(point_key):
    return SIDECAR_DIR / f"phase25_recall_{point_key}.json"


def point_record(point_key):
    path = _ROOT / phase25_prereg.point_record_path(point_key)
    _prove(path.exists(), f"{point_key}: no committed record at {_rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def _tier(block):
    """`phase25_points.measure_stage`'s count shape — numerator/denominator, never a bare rate."""
    import phase14_recall as recall  # LAZY — torch-touching

    return {
        "numerator": int(block["k"]),
        "denominator": int(block["n"]),
        "rate": block["rate"],
        "questions": block["questions"],
        "draws_per_question": 1 + recall.N_SEEDED_SAMPLES,
        "per_family": block["per_family"],
    }


def score_point(point_key, *, dry_run=False, heartbeat_path=None):
    """One adapter's recall, sidecar-persisted. Returns ``(status, blob_or_None)``.

    ``status`` is one of ``point_record`` (the control already carries it), ``reused`` (sidecar
    matched the adapter), ``dry_run`` (would score) or ``scored``.
    """
    record = point_record(point_key)
    arm = record["arm"]
    adapter = _ROOT / record["adapter_path"]
    _prove(adapter.exists(), f"{point_key}: adapter {record['adapter_path']} is not on disk")
    _prove(
        _sha256(adapter) == record["adapter_sha256"],
        f"{point_key}: {record['adapter_path']} hashes to a different adapter than the record "
        "pins; a reading over the wrong weights is not this point's reading",
    )

    if all(field in record for field in RECALL_FIELDS):
        print(f"[phase25_recall] {point_key}: recall RECORDED in the point record — skipping")
        return SOURCE_POINT_RECORD, None

    sidecar = sidecar_path(point_key)
    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == record["adapter_sha256"],
            f"{sidecar.name} describes adapter {blob['adapter_sha256']!r}, not the record's "
            f"{record['adapter_sha256']!r} — REFUSED, not reused",
        )
        print(f"[phase25_recall] {point_key}: REUSING {_rel(sidecar)}")
        return "reused", blob

    if dry_run:
        print(f"[phase25_recall] {point_key}: DRY RUN — would score {record['adapter_path']}")
        return "dry_run", None

    import phase14_factset as fs  # LAZY — torch-touching
    import teach_persona as tp  # LAZY — torch-touching

    heartbeat_path = phase25_run.HEARTBEAT_PATH if heartbeat_path is None else heartbeat_path
    state = {"point": point_key, "stage": "score", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        device = phase25_run.device()
        started = time.time()
        scored = tp.score_arm(arm, fs.LOCKED_FACTS, adapter, device)
        scoring_seconds = time.time() - started
    finally:
        stop.set()
        thread.join()

    blob = {
        "point_key": point_key,
        "arm": arm,
        "adapter_path": record["adapter_path"],
        "adapter_sha256": record["adapter_sha256"],
        "taught_recall": _tier(scored["on_taught"]),
        "heldout_recall": _tier(scored["on_heldout"]),
        "taught_recall_off": _tier(scored["off_taught"]),
        "heldout_recall_off": _tier(scored["off_heldout"]),
        "per_family_gain": scored["per_family_gain"],
        "scoring_seconds": scoring_seconds,
        "instrument": INSTRUMENT,
        "instrument_git_sha": git_sha(),
        "device": device,
        "utc": _utc(),
    }
    phase25_run.atomic_write_json(sidecar, blob)
    k, n = blob["taught_recall"]["numerator"], blob["taught_recall"]["denominator"]
    print(f"[phase25_recall] {point_key}: taught recall {k}/{n} in {scoring_seconds:.1f}s")
    phase25_run.beat(heartbeat_path, point=point_key, stage="done", shape=None, draw_index=None)
    return "scored", blob


def _measure_sidecar_device(point_key):
    sidecar = SIDECAR_DIR / f"phase25_{point_key}_measure.json"
    if not sidecar.exists():
        return None
    return json.loads(sidecar.read_text(encoding="utf-8")).get("device")


def _entry_from_record(point_key, record):
    return {
        "point_key": point_key,
        "arm": record["arm"],
        "adapter_path": record["adapter_path"],
        "adapter_sha256": record["adapter_sha256"],
        **{field: record[field] for field in RECALL_FIELDS},
        "per_family_gain": record["per_family_gain"],
        "scoring_seconds": record["scoring_seconds"],
        "instrument": INSTRUMENT,
        "instrument_git_sha": record["git_sha"],
        # The record carries no device field; the control's measure sidecar (gitignored) does.
        "device": _measure_sidecar_device(point_key),
        "utc": record["timestamp"],
        "source": SOURCE_POINT_RECORD,
    }


def emit(out_path=RECORD):
    """Assemble the 44-point artifact from 2 records + 42 sidecars. Set equality is asserted."""
    pinned = tuple(phase25_record.ORDERED_POINT_KEYS())
    points, sources = {}, {SOURCE_POINT_RECORD: 0, "sidecar": 0}
    for key in pinned:
        record = point_record(key)
        if all(field in record for field in RECALL_FIELDS):
            points[key] = _entry_from_record(key, record)
            sources[SOURCE_POINT_RECORD] += 1
            continue
        sidecar = sidecar_path(key)
        _prove(sidecar.exists(), f"{key}: no sidecar at {_rel(sidecar)} — not scored")
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == record["adapter_sha256"],
            f"{key}: sidecar adapter {blob['adapter_sha256']!r} != record "
            f"{record['adapter_sha256']!r}",
        )
        points[key] = {**blob, "source": _rel(sidecar)}
        sources["sidecar"] += 1

    _prove(
        set(points) == set(pinned) and len(points) == len(pinned),
        f"{len(points)} entries against {len(pinned)} pinned keys; missing "
        f"{sorted(set(pinned) - set(points))} extra {sorted(set(points) - set(pinned))}",
    )
    denominators = {
        (entry["taught_recall"]["denominator"], entry["heldout_recall"]["denominator"])
        for entry in points.values()
    }
    _prove(
        len(denominators) == 1,
        f"the 44 entries carry {sorted(denominators)} (taught, held-out) denominators; one "
        "instrument over the 8 LOCKED_FACTS yields one pair",
    )
    blob = {
        "governs": DEVIATION,
        "instrument": INSTRUMENT,
        "instrument_call": (
            "teach_persona.score_arm(arm, fs.LOCKED_FACTS, adapter, device) — the call "
            "phase25_points.measure_stage makes for the controls"
        ),
        "point_records_byte_unchanged": True,
        "sources": sources,
        "denominators": {"taught": denominators.pop()[0]}
        | {"heldout": next(iter(points.values()))["heldout_recall"]["denominator"]},
        "set_equality": (
            f"{len(points)} == {len(pinned)} against phase25_record.ORDERED_POINT_KEYS()"
        ),
        "total_scoring_hours": sum(e["scoring_seconds"] for e in points.values()) / 3600,
        "emitted_utc": _utc(),
        "emitted_git_sha": git_sha(),
        "points": points,
    }
    phase25_run.atomic_write_json(out_path, blob)
    print(f"[phase25_recall] emitted {out_path} ({sources})")
    return blob


def build_parser():
    parser = argparse.ArgumentParser(description="Score recall on the 42 unscored sweep adapters.")
    parser.add_argument("--points", nargs="+", default=None)
    parser.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--emit", action="store_true", help="assemble results/phase25_recall.json")
    return parser


def main(argv=None):
    print(phase25_venue.launch_banner(), flush=True)
    args = build_parser().parse_args(argv)
    if args.emit:
        emit()
        return 0
    points = phase25_record.ORDERED_POINT_KEYS() if args.points is None else tuple(args.points)
    for key in points:
        score_point(key, dry_run=args.dry_run, heartbeat_path=pathlib.Path(args.heartbeat))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
