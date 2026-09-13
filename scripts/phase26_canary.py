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
``git_sha()`` and ``refuse_if_dirty()`` (both ``personacore.provenance``) are its only reads; the
operator commits the artifact (plan 26-05).

CPU-safe at import: torch and every model module are imported inside the functions that score.
``--dry-run`` exercises every structural path without touching the device.
"""

import argparse
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
import phase25_venue  # noqa: E402  (same)
import phase26_prereg  # noqa: E402  (same — the dated pre-registration, stdlib only)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

# Resolved ONCE, at import — the commit the running code was actually loaded from. A per-write
# `git rev-parse` in a 30-hour run under an operator committing to the same tree named two
# different SHAs from ONE process, neither the loaded one (26-REVIEW WR-02). The per-write HEAD
# still travels beside it, under its own honest name (`head_at_write`).
INSTRUMENT_GIT_SHA = git_sha()

RECORD = _ROOT / "results" / "phase26_canary.json"
SOURCES = _ROOT / "results" / "phase26_canary_sources.json"  # the WR-01 continuation of RECORD
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
# What a sidecar says about the process that wrote it; travels with its sha256 (26-REVIEW WR-01).
_SOURCE_PROVENANCE_KEYS = (
    "instrument_git_sha",
    "scoring_seconds",
    "device",
    "torch_version",
    "utc",
)


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


def _source_pin(path, blob):
    """A sidecar named by its bytes and by the provenance it carries — never by path alone."""
    return {
        "path": _rel(path),
        "sha256": _sha256(path),
        "provenance": {k: blob[k] for k in _SOURCE_PROVENANCE_KEYS},
    }


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
        "instrument_git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
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


# =================================================================================================
# ===== THE ASSEMBLY — the ONLY reader of any verdict (D-19, D-13, D-03, D-05, D-18) =====
# =================================================================================================


def _fact_ids(blob, tier):
    return set(blob[tier]["per_fact"])


def _prove_shape(blob, name):
    """26-REVIEW WR-04: a sidecar with the right hash can still be truncated or foreign. The
    question count and the per-fact sum are proved per tier BEFORE any of it is read."""
    for tier in TIERS:
        _prove(
            blob[tier]["questions"] == EXPECTED_QUESTIONS[tier],
            f"{name}: {tier} has {blob[tier]['questions']} questions, expected "
            f"{EXPECTED_QUESTIONS[tier]}",
        )
        _prove(
            sum(f["n_questions"] for f in blob[tier]["per_fact"].values())
            == EXPECTED_QUESTIONS[tier],
            f"{name}: {tier} per_fact n_questions do not sum to {EXPECTED_QUESTIONS[tier]}",
        )


def _exclusions(off_blob, tiers, of):
    """D-07 under EXCLUSION_SCOPE == 'either': any adapter-off answered question in EITHER tier."""
    excluded = sorted(
        {
            fid
            for tier in tiers
            for fid, f in off_blob[tier]["per_fact"].items()
            if f["answered_questions"] > 0
        }
    )
    return {"excluded": excluded, "n": of - len(excluded), "of": of}


def _readings(blob, in_tier, out_tier, *, excluded_in, excluded_out, n_in, n_out):
    """Fact unit (decides) and question unit (reported) for one tier pair, over the non-excluded
    facts of each population."""
    in_facts = {f: v for f, v in blob[in_tier]["per_fact"].items() if f not in excluded_in}
    out_facts = {f: v for f, v in blob[out_tier]["per_fact"].items() if f not in excluded_out}
    _prove(
        len(in_facts) == n_in and len(out_facts) == n_out,
        f"{blob.get('point_key', blob.get('arm'))}: {len(in_facts)} IN / {len(out_facts)} OUT "
        f"facts after exclusions, expected {n_in} / {n_out}",
    )
    fact_unit = phase26_prereg.epsilon_lower(
        sum(1 for f in in_facts.values() if f["member"]),
        n_in,
        sum(1 for f in out_facts.values() if f["member"]),
        n_out,
    )
    question_unit = phase26_prereg.epsilon_lower(
        sum(f["answered_questions"] for f in in_facts.values()),
        sum(f["n_questions"] for f in in_facts.values()),
        sum(f["answered_questions"] for f in out_facts.values()),
        sum(f["n_questions"] for f in out_facts.values()),
    )
    return {"fact_unit": fact_unit, "question_unit": question_unit}


def emit(out_path=RECORD, *, overwrite=False):
    """Assemble ``results/phase26_canary.json`` from the OFF sidecar + 16 point sidecars, or REFUSE.

    WRITE-ONCE (T-26-03; the `phase25_recall.emit` register): a second ``--emit`` over the
    committed file would republish it under a different commit. ``--force`` is the explicit
    escape hatch. Nothing below reads a verdict before every sidecar has been proved present and
    pinned; exclusions -> ceiling -> power gate -> verdicts, in that order.
    """
    _prove(
        overwrite or not pathlib.Path(out_path).exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. The sanctioned route deletes it in "
        "its own commit, then re-runs against a clean tree (scripts/phase25_record.py "
        "RERUN_ROUTE). Pass --force to overwrite deliberately.",
    )
    out_path = pathlib.Path(out_path)
    # 26-REVIEW WR-03: `emitted_git_sha` below names a commit; `prereg_module_sha256` and
    # `frontier_sha256` are hashed from the WORKING TREE. Both are lies from a dirty tree, so the
    # register's guard (`scripts/phase21_emit.py:77`, `phase25_record._write`) runs BEFORE any
    # sidecar is read. The record being (re)placed is excluded, exactly as those emitters do.
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){_rel(out_path)}",)
    refuse_if_dirty(
        who="phase26_canary",
        detail=(
            "emit publishes emitted_git_sha and hashes scripts/ and results/ from the working "
            "tree; a record emitted from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_ROOT,
    )
    fr = frontier()
    pinned = phase26_prereg.audited_point_keys(fr)
    noised = phase26_prereg.noised_point_keys(fr)
    control = phase26_prereg.CONTROL_KEY

    off = off_sidecar_path()
    _prove(
        off.exists(),
        f"the adapter-off sidecar {_rel(off)} is missing — the audit is not complete; record the "
        f"dated D-19 named limitation in {_rel(OPERATIONAL_NOTE)} instead of assembling a "
        "partial artifact",
    )
    off_blob = json.loads(off.read_text(encoding="utf-8"))
    base = _ROOT / off_blob["base_path"]
    _prove(base.exists(), f"the OFF sidecar's base {off_blob['base_path']} is not on disk")
    _prove(
        off_blob["base_sha256"] == _sha256(base),
        f"{off.name} describes base {off_blob['base_sha256']!r}, not the bytes at "
        f"{off_blob['base_path']} — REFUSED (T-26-07)",
    )

    missing = [key for key in pinned if not sidecar_path(key).exists()]
    _prove(
        not missing,
        f"{len(missing)} of {len(pinned)} point sidecars missing: {missing} — not scored; a "
        f"partial artifact is NEVER assembled (D-19) — add the dated named-limitation entry to "
        f"{_rel(OPERATIONAL_NOTE)}",
    )
    _prove_shape(off_blob, off.name)
    sidecars = {}
    for key in pinned:
        blob = json.loads(sidecar_path(key).read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == fr["points"][key]["adapter_sha256"],
            f"{key}: sidecar adapter {blob['adapter_sha256']!r} != frontier "
            f"{fr['points'][key]['adapter_sha256']!r} — REFUSED (T-26-07)",
        )
        _prove_shape(blob, key)
        for tier in TIERS:
            # A fact absent from the OFF per_fact would read as "adapter-off never answered it"
            # — the opposite of D-07's strictest reading. Identity, not cardinality.
            _prove(
                _fact_ids(blob, tier) == _fact_ids(off_blob, tier),
                f"{key}: {tier} fact set differs from the OFF sidecar's — exclusions would be "
                "computed over a different population",
            )
        sidecars[key] = blob
    _prove(
        set(sidecars) == set(pinned) and len(sidecars) == len(pinned),
        f"{len(sidecars)} entries against {len(pinned)} pinned keys",
    )

    # (4) exclusions BEFORE anything else is read (D-07), over the OFF populations as MEASURED.
    in_of, out_of = len(_fact_ids(off_blob, "in_taught")), len(_fact_ids(off_blob, "out_taught"))
    _prove(
        in_of == 8 and out_of == 56, f"OFF populations {in_of} IN / {out_of} OUT, expected 8 / 56"
    )
    out_x = _exclusions(off_blob, OUT_TIERS, out_of)
    in_x = _exclusions(off_blob, IN_TIERS, in_of)
    n_in, n_out = in_x["n"], out_x["n"]
    _prove(n_in > 0 and n_out > 0, f"n_in = {n_in}, n_out = {n_out}: a population is empty")
    exclusions = {
        "rule": phase26_prereg.EXCLUSION_SCOPE,
        "rationale": phase26_prereg.EXCLUSION_SCOPE_RATIONALE,
        "out": out_x,
        "in": in_x,
    }

    # (5) the ceiling on the REAL n's, BEFORE any verdict (D-13, Pitfall 6).
    ceiling = phase26_prereg.auditor_ceiling(n_in, n_out)
    reachable = [k for k in noised if fr["points"][k]["epsilon"] < ceiling]
    reachable_claims = f"{len(reachable)}/{len(noised)}"

    # (6) readings per point: taught tier decides, held-out reported (D-10).
    kw = {"excluded_in": set(in_x["excluded"]), "excluded_out": set(out_x["excluded"])}
    readings = {
        k: {
            **_readings(b, "in_taught", "out_taught", n_in=n_in, n_out=n_out, **kw),
            "heldout_reported": _readings(
                b, "in_heldout", "out_heldout", n_in=n_in, n_out=n_out, **kw
            ),
        }
        for k, b in sidecars.items()
    }

    # (7) the power gate at the control (D-03, D-04).
    power = phase26_prereg.power_gate(
        readings[control]["fact_unit"]["epsilon_lower"], phase26_prereg.power_threshold(fr)
    )
    print(
        f"[phase26_canary] {phase26_prereg.POWER_SENTENCE} control epsilon_lower = "
        f"{power['control_epsilon_lower']!r} vs threshold {power['threshold']!r}: "
        f"{'PASSED' if power['passed'] else 'FAILED'}"
    )

    # (8)-(9) verdicts in order, each beside the sanctioned epsilon sentence.
    import phase25_epsilon  # LAZY — reads results/phase21_multiplicity.json at call time

    curve_total = fr["epsilon_report"]["curve_total_epsilon"]
    points = {}
    for key in pinned:
        record, blob = fr["points"][key], sidecars[key]
        sentence = phase25_epsilon.report_epsilon(
            point_epsilon=record["epsilon"],
            curve_total_epsilon=curve_total,
            selection_accounted=False,
        )
        _prove(
            sentence == fr["epsilon_report"]["rendered"][key],
            f"{key}: report_epsilon renders differently from the frontier's epsilon_report",
        )
        entry = {
            "adapter_sha256": record["adapter_sha256"],
            "adapter_path": record["adapter_path"],
            "sigma": record["sigma"],
            "epsilon_upper": record["epsilon"],
            **readings[key],
            "epsilon_sentence": sentence,
            "source": _rel(sidecar_path(key)),
            "source_sha256": _sha256(sidecar_path(key)),
            "source_provenance": {k: blob[k] for k in _SOURCE_PROVENANCE_KEYS},
        }
        if key == control:
            entry["verdict"] = None
            entry["comparison"] = (
                "VACUOUS BY CONSTRUCTION: the control publishes no epsilon ("
                + record["epsilon_omitted_reason"]
                + "); its reading is the power gate's and feeds nothing else (D-01)"
            )
            entry["reproduction_gate"] = blob.get("reproduction_gate")
        else:
            entry["verdict"] = phase26_prereg.point_verdict(
                readings[key]["fact_unit"],
                record["epsilon"],
                power=power,
                auditor_ceiling=ceiling,
            )
        points[key] = entry
    summary = {v: 0 for v in phase26_prereg.VERDICTS}
    for key in noised:
        summary[points[key]["verdict"]["verdict"]] += 1

    import phase18_extraction  # LAZY — heavy; import-only for the rationale
    import phase25_gate05  # LAZY — import-only for FILLER_EXPOSURE_OMITTED

    blob = {
        "governs": {
            "why_not_nll_exposure_on_filler": phase25_gate05.FILLER_EXPOSURE_OMITTED,
            "both_denominators": phase18_extraction.CLUSTER_DENOMINATOR_RATIONALE,
            "one_sided": phase26_prereg.ONE_SIDED_CLAUSE,
        },
        "instrument": INSTRUMENT,
        "audit_target_rule": phase26_prereg.RULE,
        "resolved_target": phase26_prereg.resolve_audit_target(fr),
        "extension": phase26_prereg.EXTENSION,
        "audited_point_keys": list(pinned),
        "deciding_tier": phase26_prereg.DECIDING_TIER,
        "membership_rule": phase26_prereg.MEMBERSHIP_RULE,
        "unit": phase26_prereg.UNIT,
        "frontier_path": _rel(phase25_record.FRONTIER_RECORD),
        "frontier_sha256": _sha256(phase25_record.FRONTIER_RECORD),
        "frontier_bytes": phase25_record.FRONTIER_RECORD.stat().st_size,
        "base_path": off_blob["base_path"],
        "base_sha256": off_blob["base_sha256"],
        "off_sidecar": _rel(off),
        "off_sidecar_sha256": _sha256(off),
        "off_sidecar_provenance": {k: off_blob[k] for k in _SOURCE_PROVENANCE_KEYS},
        "prereg_module_sha256": _sha256(PREREG_MODULE),
        "prereg_committed": phase26_prereg.COMMITTED,
        "waiver_continuation": phase26_prereg.WAIVER_CONTINUATION,
        "exclusions": exclusions,
        "n_in": n_in,
        "n_out": n_out,
        "auditor_ceiling": ceiling,
        "reachable_claims": reachable_claims,
        "reachable_keys": reachable,
        "power_gate": power,
        "joint_coverage": phase26_prereg.JOINT_COVERAGE,
        "z": phase26_prereg.Z,
        "delta": phase26_prereg.DELTA,
        "curve_total_epsilon": curve_total,
        "curve_total_is_context_only": phase26_prereg.EXTENSION,
        "emitted_utc": _utc(),
        "emitted_git_sha": git_sha(),
        "points": points,
        "summary": summary,
    }
    phase25_run.atomic_write_json(out_path, blob)
    print(
        f"[phase26_canary] emitted {_rel(out_path)}: {summary}; reachable claims "
        f"{reachable_claims} (auditor_ceiling = {ceiling!r}); power gate "
        f"{'PASSED' if power['passed'] else 'FAILED'}"
    )
    return blob


def pin_sources(out_path=SOURCES, *, record_path=RECORD, overwrite=False):
    """DATED CONTINUATION, 2026-09-13 (26-REVIEW WR-01) of the write-once artifact (D-18).

    The committed ``results/phase26_canary.json`` names its 17 gitignored inputs by PATH only. This
    pins each one — sha256 of the bytes, the provenance the sidecar carries, and the proof that the
    file on disk RE-DERIVES the artifact's exclusions and fact-unit readings (a re-scored sidecar
    under the same adapter hash is not the one the artifact was assembled from). Written beside
    the artifact, never into it; ``--force`` is the escape hatch. Publishes NO git SHA: every
    field here is a content hash or a copied provenance field, verifiable without a tree.
    """
    _prove(
        overwrite or not pathlib.Path(out_path).exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. Pass --force to overwrite.",
    )
    record_path = pathlib.Path(record_path)
    _prove(record_path.exists(), f"{_rel(record_path)} is missing — nothing to pin")
    art = json.loads(record_path.read_text(encoding="utf-8"))

    off = _ROOT / art["off_sidecar"]
    _prove(off.exists(), f"the OFF sidecar {art['off_sidecar']} is not on disk")
    off_blob = json.loads(off.read_text(encoding="utf-8"))
    _prove(
        off_blob["base_sha256"] == art["base_sha256"],
        f"{off.name}: base {off_blob['base_sha256']!r} != the artifact's {art['base_sha256']!r}",
    )
    for scope, tiers in (("out", OUT_TIERS), ("in", IN_TIERS)):
        _prove(
            _exclusions(off_blob, tiers, art["exclusions"][scope]["of"])
            == art["exclusions"][scope],
            f"{off.name}: the OFF sidecar on disk does not re-derive the artifact's {scope} "
            "exclusions — it is not the file the artifact was assembled from",
        )

    kw = {
        "excluded_in": set(art["exclusions"]["in"]["excluded"]),
        "excluded_out": set(art["exclusions"]["out"]["excluded"]),
        "n_in": art["n_in"],
        "n_out": art["n_out"],
    }
    points = {}
    for key in art["audited_point_keys"]:
        entry = art["points"][key]
        path = _ROOT / entry["source"]
        _prove(path.exists(), f"{key}: {entry['source']} is not on disk")
        blob = json.loads(path.read_text(encoding="utf-8"))
        _prove(
            blob["adapter_sha256"] == entry["adapter_sha256"],
            f"{key}: sidecar adapter {blob['adapter_sha256']!r} != the artifact's "
            f"{entry['adapter_sha256']!r}",
        )
        _prove(
            _readings(blob, "in_taught", "out_taught", **kw)["fact_unit"] == entry["fact_unit"],
            f"{key}: the sidecar on disk does not re-derive the artifact's fact_unit reading — "
            "it is not the file the artifact was assembled from",
        )
        points[key] = _source_pin(path, blob)

    blob = {
        "continues": _rel(record_path),
        "artifact_sha256": _sha256(record_path),
        "why": (
            "26-REVIEW WR-01: the artifact names its sidecars by path under gitignored data/; "
            "this sibling pins each by sha256 and provenance and proves it re-derives the "
            "artifact's exclusions and fact-unit readings. The artifact is write-once (D-18) and "
            "is not re-emitted."
        ),
        "pinned_utc": _utc(),
        "off_sidecar": _source_pin(off, off_blob),
        "points": points,
    }
    phase25_run.atomic_write_json(out_path, blob)
    print(f"[phase26_canary] pinned {len(points)} point sidecars + OFF into {_rel(out_path)}")
    return blob


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 26 canary audit: adapter-off once, then adapter-on over 16 dp_n8 points."
    )
    parser.add_argument("--points", nargs="+", default=None)
    parser.add_argument("--heartbeat", default=str(phase25_run.HEARTBEAT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--emit", action="store_true", help="assemble results/phase26_canary.json")
    parser.add_argument(
        "--pin-sources",
        action="store_true",
        help="write results/phase26_canary_sources.json — sha256 + provenance of every sidecar",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing artifact")
    return parser


def main(argv=None):
    print(phase25_venue.launch_banner(), flush=True)
    args = build_parser().parse_args(argv)
    if args.emit:
        emit(overwrite=args.force)
        return 0
    if args.pin_sources:
        pin_sources(overwrite=args.force)
        return 0
    heartbeat = pathlib.Path(args.heartbeat)
    points = phase26_prereg.audited_point_keys(frontier()) if args.points is None else args.points
    score_off_once(dry_run=args.dry_run, heartbeat_path=heartbeat)  # D-17: once, before any point
    for key in points:
        score_point(key, dry_run=args.dry_run, heartbeat_path=heartbeat)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
