"""PHASE 26 (CANARY-01 / CANARY-02) — the empirical epsilon_lower audit driver.

Built line-for-line on ``scripts/phase25_recall.py`` (sidecar per point under ``data/``, sha-pinned
reuse-or-refuse, heartbeat, atomic writes, ``--dry-run`` / ``--emit`` / ``--force``), with the
scorer swapped: ``teach_persona.score_arm`` cannot render filler (``render_family`` without
``forms=`` raises ``KeyError`` on a filler slot) and returns no per-fact counts, so this module
replays ``score_items``' two calls — ``phase14_recall.complete_question`` then
``phase14_recall.score_question`` — per fact, with the SAME ``enumerate`` index per list (the
per-question seed; RESEARCH Pitfall 1), over four lists: IN taught / IN held-out (the 8
``LOCKED_FACTS``), OUT taught / OUT held-out (the 56 ``FILLER_FACTS`` rendered with
``forms=FILLER_SLOT_FORMS``). ONE instrument for IN and OUT (D-06, D-08).

THE ADAPTER-OFF ARM IS MEASURED ONCE (D-17) on the sha256-pinned base — the D-07 guessability
probe — and written to its own sidecar; every point's sidecar is pinned to the frontier's
``adapter_sha256`` and reused only when the hash matches (D-16). At the control the IN-taught sum
is routed through ``phase25_prereg.prove_reproduction`` BEFORE its sidecar is written (D-15): a
halt there is the designed outcome.

NO VERDICT IS COMPUTED OR READ ANYWHERE BUT ``emit`` (D-17, D-19), and ``emit`` refuses unless the
OFF sidecar and all 16 point sidecars exist — a partial artifact is NEVER assembled; the refusal
names ``results/phase26_operational_note.md`` for the dated D-19 named limitation. Exclusions,
the auditor's ceiling and the power gate are computed BEFORE any verdict (D-13, D-03), then
``results/phase26_canary.json`` is written WRITE-ONCE (D-18), pinned in both directions to
``results/phase25_frontier.json``.

SURVIVABILITY, CALLED NEVER RE-IMPLEMENTED: ``phase25_run.atomic_write_json`` / ``beat`` /
``start_heartbeat`` / ``device``; the beat lands in the SAME ``data/phase25_heartbeat.jsonl`` the
installed ``com.personacore.phase25.watch`` agent polls. The driver builds NO git argv (T-26-05):
``git_sha()`` is its only read; the operator commits the artifact (plan 26-05).

CPU-safe at import: torch and every model module are imported inside the functions that score.
``--dry-run`` exercises every structural path without touching the device.
"""

import datetime
import functools
import hashlib
import json
import pathlib
import platform
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
import phase26_prereg  # noqa: E402  (same — the dated pre-registration, stdlib only)

from personacore.provenance import git_sha  # noqa: E402

RECORD = _ROOT / "results" / "phase26_canary.json"
OPERATIONAL_NOTE = _ROOT / "results" / "phase26_operational_note.md"
SIDECAR_DIR = _ROOT / "data"  # gitignored (`data/`)
PREREG_MODULE = _ROOT / "scripts" / "phase26_prereg.py"
INSTRUMENT = (
    "phase14_recall.complete_question + phase14_recall.score_question (teach_persona.score_items' "
    "two calls, replayed per fact with the same enumerate index)"
)
TIERS = ("in_taught", "in_heldout", "out_taught", "out_heldout")
IN_TIERS, OUT_TIERS = TIERS[:2], TIERS[2:]
EXPECTED_QUESTIONS = {"in_taught": 112, "in_heldout": 72, "out_taught": 784, "out_heldout": 504}


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase26_canary] {message}")


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    """Repo-relative when inside the root; the path as given otherwise (tests use tmp dirs)."""
    path = pathlib.Path(path)
    return str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)


def sidecar_path(point_key):
    # T-26-06: the charset `_prove` inside point_record_path is the refusal; its return is unused.
    phase25_prereg.point_record_path(point_key)
    return SIDECAR_DIR / f"phase26_canary_{point_key}.json"


def off_sidecar_path():
    return SIDECAR_DIR / "phase26_canary_off.json"


@functools.lru_cache(maxsize=1)
def frontier():
    """The audited artifact, read ONCE per process (22 MB), never modified."""
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))


def point_record(point_key):
    fr = frontier()
    _prove(
        point_key in phase26_prereg.audited_point_keys(fr),
        f"{point_key!r} is not one of the 16 audited dp_n8 keys (T-26-06)",
    )
    return fr["points"][point_key]


# =================================================================================================
# ===== THE ITEMS — teach_persona.calibration_items' rule, with the filler forms (D-06, D-08) =====
# =================================================================================================


def _items(facts, family_ids, forms=None):
    """``(family_id, fact, question)`` for every scorable question, the same self-naming filter
    ``calibration_items`` applies; equal AS A LIST to it on ``LOCKED_FACTS`` with ``forms=None``
    (that equality is what makes the seeds identical to the published run). ``sorted(family_ids)``
    is load-bearing (``phase21_filler.render_filler_episodes``)."""
    import phase14_factset as fs  # LAZY — torch-touching neighbours
    import phase14_recall as pr  # LAZY — torch-touching

    items = []
    for fact in facts:
        for family_id in sorted(family_ids):
            for question, _answer in fs.render_family(family_id, fact, forms=forms):
                if pr.contains_value(question, fact.value):
                    continue
                items.append((family_id, fact, question))
    return items


def _lists():
    """The four item lists, in ``TIERS`` order; each is its OWN ``enumerate`` from 0 (Pitfall 1)."""
    import phase14_factset as fs  # LAZY — torch-touching neighbours
    import phase21_filler as pf  # LAZY — imports phase14_factset at module scope

    lists = {
        "in_taught": _items(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS),
        "in_heldout": _items(fs.LOCKED_FACTS, fs.HELDOUT_FAMILY_IDS),
        "out_taught": _items(pf.FILLER_FACTS, fs.TAUGHT_FAMILY_IDS, forms=pf.FILLER_SLOT_FORMS),
        "out_heldout": _items(pf.FILLER_FACTS, fs.HELDOUT_FAMILY_IDS, forms=pf.FILLER_SLOT_FORMS),
    }
    for tier, items in lists.items():
        _prove(
            len(items) == EXPECTED_QUESTIONS[tier],
            f"{tier}: {len(items)} scorable questions, expected {EXPECTED_QUESTIONS[tier]}",
        )
    return lists


# =================================================================================================
# ===== THE SCORER — score_items' two calls, per fact, counts kept (D-14, Pitfall 2) =====
# =================================================================================================


def _score_list(model, tok, device, forbid, items, *, label, heartbeat_state=None):
    """One list, one ``enumerate`` from 0: ``index`` is the per-question seed offset."""
    import phase14_recall as pr  # LAZY — torch-touching
    import phase18_extraction  # LAZY — heavy; import-only for CLUSTER_DENOMINATOR_RATIONALE

    per_question, per_fact = [], {}
    for index, (family_id, fact, question) in enumerate(items):
        if heartbeat_state is not None:
            heartbeat_state["shape"] = label
            heartbeat_state["draw_index"] = index
        drawn = pr.complete_question(model, tok, question, device, forbid, index=index)
        k, n = pr.score_question(drawn["completions"], fact.value)
        per_question.append(
            {
                "fact": fact.id,
                "family": family_id,
                "index": index,
                "k": k,
                "n": n,
                "answered": k > 0,
            }
        )
        f = per_fact.setdefault(
            fact.id, {"answered_questions": 0, "n_questions": 0, "k": 0, "n": 0, "member": False}
        )
        f["answered_questions"] += int(k > 0)
        f["n_questions"] += 1
        f["k"] += k
        f["n"] += n
        f["member"] = f["answered_questions"] >= 1  # D-14: existential
    total_k = sum(r["k"] for r in per_question)
    total_n = sum(r["n"] for r in per_question)
    print(f"[phase26_canary] {label}: {total_k}/{total_n} draws over {len(items)} questions")
    return {
        "per_question": per_question,
        "per_fact": per_fact,
        "k": total_k,
        "n": total_n,
        "questions": len(items),
        "questions_answered": sum(1 for r in per_question if r["k"] > 0),
        "draws_per_question": pr.N_SEEDED_SAMPLES + 1,
        "unit_rationale": phase18_extraction.CLUSTER_DENOMINATOR_RATIONALE,
    }


def _prove_host_adapter(point_key):
    """The point's adapter is on disk and hashes to the frontier's pin (T-26-07)."""
    record = point_record(point_key)
    adapter = _ROOT / record["adapter_path"]
    _prove(adapter.exists(), f"{point_key}: adapter {record['adapter_path']} is not on disk")
    _prove(
        _sha256(adapter) == record["adapter_sha256"],
        f"{point_key}: {record['adapter_path']} hashes to a different adapter than the frontier "
        "pins; a reading over the wrong weights is not this point's reading",
    )
    return record, adapter


def _provenance(device, scoring_seconds):
    import torch  # LAZY — torch-touching

    return {
        "scoring_seconds": scoring_seconds,
        "instrument": INSTRUMENT,
        "instrument_git_sha": git_sha(),
        "device": device,
        "torch_version": torch.__version__,
        "platform": platform.platform(),
        "utc": _utc(),
    }


def score_off_once(*, dry_run=False, heartbeat_path=None):
    """The adapter-OFF arm, ONCE (D-17), on the sha256-pinned base — the D-07 probe.

    Host adapter = the control's (the base does not vary across points; ``adapter_disabled``
    flips only the LoRA ``enabled`` flags). Returns ``(status, blob_or_None)``.
    """
    control = phase26_prereg.CONTROL_KEY
    record, host = _prove_host_adapter(control)

    sidecar = off_sidecar_path()
    if sidecar.exists():
        import phase14_recall as pr  # LAZY — torch-touching; only for CONVBASE_SLIM

        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["base_sha256"] == _sha256(pr.CONVBASE_SLIM),
            f"{sidecar.name} describes base {blob['base_sha256']!r}, not the live "
            f"{_rel(pr.CONVBASE_SLIM)} — REFUSED, not reused",
        )
        print(f"[phase26_canary] off: REUSING {_rel(sidecar)}")
        return "reused", blob

    if dry_run:
        print(f"[phase26_canary] off: DRY RUN — would score the adapter-off arm on {host.name}")
        return "dry_run", None

    import phase14_recall as pr  # LAZY — torch-touching

    from personacore.lora import adapter_disabled  # LAZY — torch-touching

    heartbeat_path = phase25_run.HEARTBEAT_PATH if heartbeat_path is None else heartbeat_path
    state = {"point": "off", "stage": "score", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        device = phase25_run.device()
        started = time.time()
        model, _cfg, tok, forbid, _artifact = pr.load_adapted_model(device, adapter_path=host)
        lists = _lists()
        with adapter_disabled(model):
            scored = {
                tier: _score_list(
                    model, tok, device, forbid, items, label=f"OFF {tier}", heartbeat_state=state
                )
                for tier, items in lists.items()
            }
        scoring_seconds = time.time() - started
    finally:
        stop.set()
        thread.join()

    blob = {
        "arm": "off",
        "base_path": _rel(pr.CONVBASE_SLIM),
        "base_sha256": _sha256(pr.CONVBASE_SLIM),
        "host_point_key": control,
        "host_adapter_sha256": record["adapter_sha256"],
        **scored,
        **_provenance(device, scoring_seconds),
    }
    phase25_run.atomic_write_json(sidecar, blob)
    print(
        f"[phase26_canary] off: taught IN {blob['in_taught']['k']}/{blob['in_taught']['n']}, "
        f"OUT {blob['out_taught']['k']}/{blob['out_taught']['n']} in {scoring_seconds:.1f}s"
    )
    phase25_run.beat(heartbeat_path, point="off", stage="done", shape=None, draw_index=None)
    return "scored", blob


def score_point(point_key, *, dry_run=False, heartbeat_path=None):
    """One adapter's ON arm over the four lists, sidecar-persisted. Returns ``(status, blob)``.

    ``status`` is ``reused`` (sidecar matched the adapter), ``dry_run`` or ``scored``.
    """
    record, adapter = _prove_host_adapter(point_key)

    sidecar = sidecar_path(point_key)
    if sidecar.exists():
        blob = json.loads(sidecar.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == record["adapter_sha256"],
            f"{sidecar.name} describes adapter {blob['adapter_sha256']!r}, not the frontier's "
            f"{record['adapter_sha256']!r} — REFUSED, not reused",
        )
        print(f"[phase26_canary] {point_key}: REUSING {_rel(sidecar)}")
        return "reused", blob

    if dry_run:
        print(f"[phase26_canary] {point_key}: DRY RUN — would score {record['adapter_path']}")
        return "dry_run", None

    import phase14_recall as pr  # LAZY — torch-touching

    heartbeat_path = phase25_run.HEARTBEAT_PATH if heartbeat_path is None else heartbeat_path
    state = {"point": point_key, "stage": "score", "shape": None, "draw_index": None}
    phase25_run.beat(heartbeat_path, **state)
    stop, thread = phase25_run.start_heartbeat(heartbeat_path, state)
    try:
        device = phase25_run.device()
        started = time.time()
        model, _cfg, tok, forbid, _artifact = pr.load_adapted_model(device, adapter_path=adapter)
        scored = {
            tier: _score_list(
                model,
                tok,
                device,
                forbid,
                items,
                label=f"{point_key} ON {tier}",
                heartbeat_state=state,
            )
            for tier, items in _lists().items()
        }
        scoring_seconds = time.time() - started
    finally:
        stop.set()
        thread.join()

    blob = {
        "point_key": point_key,
        "arm": record["arm"],
        "sigma": record["sigma"],
        "adapter_path": record["adapter_path"],
        "adapter_sha256": record["adapter_sha256"],
        "epsilon_upper": record["epsilon"],
        "delta": record["delta"],
        **scored,
    }
    if point_key == phase26_prereg.CONTROL_KEY:
        # D-15: the auditor must reproduce the artifact's 790/1008 BEFORE its reading is trusted.
        # A halt here is the designed outcome; nothing is written.
        k, n = int(scored["in_taught"]["k"]), int(scored["in_taught"]["n"])
        phase25_prereg.prove_reproduction(k, n)
        print(f"[phase26_canary] REPRODUCTION GATE PASSED {k}/{n}")
        blob["reproduction_gate"] = {
            "passed": True,
            "expected": [phase25_prereg.REPRODUCTION_K, phase25_prereg.REPRODUCTION_N],
            "observed": [k, n],
        }
    blob.update(_provenance(device, scoring_seconds))
    phase25_run.atomic_write_json(sidecar, blob)
    print(
        f"[phase26_canary] {point_key}: taught IN {blob['in_taught']['k']}/{blob['in_taught']['n']}"
        f", OUT {blob['out_taught']['k']}/{blob['out_taught']['n']} in {scoring_seconds:.1f}s"
    )
    phase25_run.beat(heartbeat_path, point=point_key, stage="done", shape=None, draw_index=None)
    return "scored", blob
