"""PHASE 27 (RELRN-01..05) — the relearning-attack driver: ONE admission call and four attack legs.

``admit`` is the phase's ONE gate call. It calls ``phase27_prereg.relearning_is_worth_attempting``
once on the committed frontier and writes ``results/phase27_admission.json`` WRITE-ONCE: the rows,
tallies and cleared counts re-derived and ``_prove``d at the write, the computed disjointness of the
recovery fixture, the apparatus disclosure and seven module digests. The OPERATOR commits that file
by hand (D-15). This driver's git surface is READ-ONLY: its one git argv is ``ls-files`` (a member
of ``phase25_run.READ_ONLY_GIT_ACTIONS``), and nothing here stages, commits or pushes anything.

EVERY ATTACK LEG — ``calibrate``, ``curve``, ``gate``, ``structural-proof`` — opens with
``_require_admitted``: the COMMITTED record must read ADMITTED, carry the pinned baselines and (when
inside the repo) be tracked, or the leg refuses before it resolves a device (D-08, D-12). The train
path is ``TRAIN_PATH`` (27-RESEARCH OQ1 option B), disclosed in the record.

Nothing here schedules anything (D-14 — no plist). No leg runs on MPS in this phase (D-09): the
record reads MOOT, so the legs are exercised only by the CPU wiring proof on a tiny fixture, which
pins ``phase25_run._DEVICE = "cpu"``. The ONLY device resolver in this module is
``phase25_run.device()``.

CPU-safe at import: stdlib plus torch-free sibling modules. Every torch-touching module is imported
inside the function that needs it.
"""

import argparse
import collections
import dataclasses
import datetime
import functools
import hashlib
import importlib.metadata
import json
import math
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import mitigation_gate  # noqa: E402  (scripts/ is not a package)
import phase24_adversarial  # noqa: E402  (same — torch-free at import)
import phase25_record  # noqa: E402  (same)
import phase25_run  # noqa: E402  (same — CPU-safe at import; torch stays lazy)
import phase27_prereg  # noqa: E402  (same — the pre-registration, read at call time)

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402

# Resolved ONCE, at import — the commit the running code was loaded from (the phase26_canary idiom).
INSTRUMENT_GIT_SHA = git_sha()

RECORD = _ROOT / "results" / "phase27_admission.json"
STREAM_DIR = _ROOT / "data"  # gitignored: per-arm bins, rung adapters, offset streams, leg JSON
# Spelled here because phase14_recall imports torch. The scorers load the base through
# phase14_recall.CONVBASE_SLIM, model_from_adapter through this name; a test pins them to one file.
BASE_SLIM = _ROOT / "checkpoints" / "convbase_slim.pt"
PINNED_MODULES = (
    "scripts/phase27_prereg.py",
    "scripts/phase27_relearn.py",
    "scripts/mitigation_gate.py",
    "scripts/erasure_gate.py",
    "scripts/teach_persona.py",
    "src/personacore/training/data.py",
    "src/personacore/training/loop.py",
)
ARMS = ("fresh", "control", "mitigated")
TRAIN_PATH = (
    "teach_persona.train() called directly with ONE shared TrainConfig and bins from "
    "teach_persona.build_arm_bins — the shape of phase23_run.train_never_taught (27-RESEARCH OQ1 "
    "option B); teach_persona.train_arm is not called"
)
SUB_MODES = ("admit", "calibrate", "curve", "gate", "structural-proof")
DRAW_CACHE = (
    "phase25_run.draws_path(point_label) under phase25_run.DRAWS_DIR — "
    "data/phase25_phase27_{leg}_{point_key or arm_seedS}_rung{NNNN}_k{K}_draws.json; k is part of "
    "the cache identity (phase25_run.load_draws), so the FULL_K re-score never reuses CURVE_K draws"
)

_TEST_FILE = "tests/test_phase27_relearn.py"
APPARATUS_LEGS = tuple(
    {
        "name": name,
        "sub_mode": sub_mode,
        "refusal_node_id": f"{_TEST_FILE}::test_each_leg_refuses_unless_admitted[{sub_mode}-MOOT]",
        "e2e_node_id": f"{_TEST_FILE}::test_the_live_path_is_wired_end_to_end",
        "train_path": TRAIN_PATH,
    }
    for name, sub_mode in (
        ("Z calibration", "calibrate"),
        ("cost-to-recovery curve", "curve"),
        ("recovery-ceiling gate", "gate"),
        ("structural identical-budget proofs", "structural-proof"),
    )
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase27_relearn] {message}")


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _rel(path):
    """Repo-relative when inside the root; the path as given otherwise (tests use tmp dirs)."""
    path = pathlib.Path(path)
    return str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)


@functools.lru_cache(maxsize=1)
def frontier():
    """The committed Phase-25 frontier, read ONCE per process (22 MB), never modified."""
    return json.loads(phase25_record.FRONTIER_RECORD.read_text(encoding="utf-8"))


def admission(record_path=RECORD):
    """The admission record as parsed JSON. NOT cached: ``admit`` writes it, tests forge it."""
    return json.loads(pathlib.Path(record_path).read_text(encoding="utf-8"))


def _require_admitted(record_path=RECORD):
    """The FIRST statement of every leg (D-08, D-12). Returns the record, or refuses.

    Three conjuncts on the record, then the tracked one: it exists; it reads ADMITTED; its
    ``baselines`` equal the JSON-normalised ``phase27_prereg.PINNED_BASELINES`` (tuples compare as
    lists); and, only for a path inside the repo, ``git ls-files`` names it — a leg runs against the
    COMMITTED record, never a live re-read. The path is resolved first, so a relative ``--record``
    cannot step around the tracked conjunct. A tmp record outside the repo skips only that last
    conjunct, which is what lets the CPU wiring proof forge an ADMITTED record without git.
    """
    path = pathlib.Path(record_path).resolve()
    _prove(
        path.exists(),
        f"{_rel(path)} is absent — REFUSING to run this leg: run `admit` first; every leg is "
        "gated on the COMMITTED record",
    )
    blob = admission(path)
    read = blob["verdict"]["verdict"]
    reasons = blob["verdict"].get("reasons") or ["no reasons recorded"]
    _prove(
        read == "ADMITTED",
        f"{_rel(path)} reads {read!r} — REFUSING to run this leg: nothing is admitted "
        f"({reasons[0]})",
    )
    _prove(
        blob.get("baselines") == json.loads(json.dumps(phase27_prereg.PINNED_BASELINES)),
        f"{_rel(path)} carries baselines that differ from phase27_prereg.PINNED_BASELINES — "
        "REFUSING: D-12's pins moved after the record was written",
    )
    if path.is_relative_to(_ROOT):
        tracked = subprocess.run(
            ["git", "ls-files", _rel(path)],
            cwd=_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        _prove(
            tracked,
            f"{_rel(path)} is not tracked — REFUSING: a leg runs only against the COMMITTED "
            "record, never a live re-read",
        )
    return blob


def disjointness_report():
    """D-17's computed disjointness of the recovery fixture, over QUESTION STRINGS on every side.

    ``phase18_extraction.build_corpus`` entries carry ``prompt_ids`` and no text
    (``scripts/phase24_adversarial.py`` states it), and ``results/phase16_recall_sample.json`` is
    the only place the question text lives, so the scored gated set is read from that fixture.
    Set (i) is the mitigated arm's teaching rows; set (ii) is the adversarial ARM's trained rows,
    ``phase24_adversarial.adversarial_episodes`` (the pool ``teach_persona.build_bins`` trains
    from — ``TRAINED_TIER`` rows in ``TRAINED_FAMILIES``, the held-out family excluded by
    construction), NOT the scored corpus's own attack entries; set (iii) is the attacker corpus.
    ``admit`` refuses on any non-zero overlap.
    """
    import phase14_factset as fs  # LAZY — torch-free, but kept off the import surface
    import phase14_recall as pr  # LAZY — torch-touching
    import phase18_extraction as x18  # LAZY — torch-touching
    import teach_persona as tp  # LAZY — torch-touching

    from personacore.tokenizer import from_json

    _prove(
        phase27_prereg.HELD_OUT_FAMILY not in phase27_prereg.TRAINED_FAMILIES,
        f"the held-out attack family {phase27_prereg.HELD_OUT_FAMILY!r} is among the trained "
        f"families {phase27_prereg.TRAINED_FAMILIES}",
    )
    tok = from_json(tp.TOKENIZER_PATH)
    fixture = json.loads(x18.CORPUS_SOURCE_FIXTURE.read_text(encoding="utf-8"))
    corpus = x18.build_corpus(tok)
    gated_prompts = [e for e in corpus["prompts"] if e["tier"] == phase27_prereg.GATED_TIER]
    scored_gated = {row["question"] for row in fixture["questions"][phase27_prereg.GATED_TIER]}
    scored_heldout = {item.question for item in pr.build_question_sets(fs.LOCKED_FACTS)[1]}
    teaching = {q for q, _a in tp.render_episodes(fs.LOCKED_FACTS, fs.TAUGHT_FAMILY_IDS)}
    episodes = phase24_adversarial.adversarial_episodes(tok)
    trained_attack = {q for _persona, q, _a in episodes}
    attacker = {q for q, _a in phase27_prereg.attacker_corpus_rows()}
    # The two halves of the fixture share the held-out questions: the union IS the scored set.
    scored = scored_gated | scored_heldout
    return {
        "unit": (
            "question strings — the corpus carries prompt_ids, not text; "
            "results/phase16_recall_sample.json is the only place the text lives"
        ),
        "scored": {
            "gated_prompts": len(gated_prompts),
            "gated_questions": len(scored_gated),
            "heldout_recall": len(scored_heldout),
        },
        "overlaps": {
            "teaching": len(scored & teaching),
            "trained_attack": len(scored & trained_attack),
            "attacker_corpus": len(scored & attacker),
        },
        "checked": len(scored),
        "held_out_family": phase27_prereg.HELD_OUT_FAMILY,
        "trained_families": list(phase27_prereg.TRAINED_FAMILIES),
        "trained_attack_rows": len(episodes),
    }


def build_record(frontier_blob):
    """The admission record, pure over the frontier and the pre-registration (no torch).

    The 44 rows are re-derived through ``phase27_prereg.cleared_abc`` on each point's stored kwargs
    (never a reason string, D-34) and ``_prove``d at the write against the frontier's tallies,
    per-leg tallies and the cleared counts (D-33). REFUSED rows carry ``refused: true`` and null
    ``cleared_a/b/c``, with no reason text (27-RESEARCH OQ6). ``disjointness`` and ``provenance``
    are left ``None`` for ``admit`` to fill.
    """
    verdict, reasons = phase27_prereg.relearning_is_worth_attempting(frontier_blob)
    points = frontier_blob["points"]
    rows = []
    for key in frontier_blob["point_keys"]:
        verdict_string = phase27_prereg.point_verdict_string(points[key])
        cleared_a, cleared_b, cleared_c = phase27_prereg.cleared_abc(points[key]["verdict"])
        rows.append(
            {
                "point_key": key,
                "arm": phase27_prereg.arm_of(key),
                "leg": phase27_prereg.leg_of(key),
                "verdict": verdict_string,
                "cleared_a": cleared_a,
                "cleared_b": cleared_b,
                "cleared_c": cleared_c,
                "refused": verdict_string == phase27_prereg.REFUSED,
            }
        )
    counts = phase27_prereg.cleared_counts(frontier_blob)
    stored = frontier_blob["verdicts"]

    _prove(
        len(rows) == phase27_prereg.EXPECTED_POINTS,
        f"{len(rows)} rows, {phase27_prereg.EXPECTED_POINTS} expected (D-33)",
    )
    # Counter against Counter: a missing name counts as zero on both sides (a dict would not).
    tally = collections.Counter(row["verdict"] for row in rows)
    _prove(
        tally == collections.Counter(stored["tallies"]),
        f"row verdicts {dict(tally)} do not re-derive verdicts.tallies {stored['tallies']}",
    )
    by_leg = collections.defaultdict(collections.Counter)
    for row in rows:
        by_leg[row["point_key"].rsplit("_", 1)[0]][row["verdict"]] += 1
    stored_by_leg = {leg: collections.Counter(t) for leg, t in stored["tallies_by_leg"].items()}
    _prove(
        dict(by_leg) == stored_by_leg,
        f"per-leg row verdicts {dict(by_leg)} do not re-derive verdicts.tallies_by_leg",
    )
    for name in ("a", "b", "c"):
        summed = sum(1 for row in rows if row[f"cleared_{name}"])
        _prove(
            summed == counts[name],
            f"{summed} rows cleared ({name}) against cleared_counts {counts[name]}",
        )

    x = phase27_prereg.extraction_ceiling_x(frontier_blob)
    control = points[phase27_prereg.CONTROL_KEYS["n8"]]["verdict"]
    n_questions = control["point_extraction_questions"]
    tolerated, fraction, sentence = mitigation_gate.tolerance_report(
        ceiling=x, n_questions=n_questions
    )
    admitted = verdict == "ADMITTED"
    return {
        "governs": (
            "results/phase27_admission.json is the ONE output of `phase27_relearn admit`: the "
            "admission gate pre-registered in scripts/phase27_prereg.py (committed "
            f"{phase27_prereg.COMMITTED} with {phase27_prereg.RECORDS_AT_COMMIT} results/phase27_* "
            "records tracked) called once on results/phase25_frontier.json; every attack leg "
            "reads this COMMITTED record and refuses unless it reads ADMITTED"
        ),
        "verdict": {"verdict": verdict, "reasons": list(reasons)},
        "admitted_point_keys": list(phase27_prereg.admitted_point_keys(frontier_blob)),
        "tallies": stored["tallies"],
        "tallies_by_leg": stored["tallies_by_leg"],
        "cleared_counts": counts,
        "rows": rows,
        "frontier_path": _rel(phase25_record.FRONTIER_RECORD),
        "frontier_sha256": _sha256(phase25_record.FRONTIER_RECORD),
        "frontier_bytes": phase25_record.FRONTIER_RECORD.stat().st_size,
        "x": {
            "value": x,
            "n_questions": n_questions,
            "tolerated": tolerated,
            "fraction": fraction,
            "tolerance_sentence": sentence,
        },
        "recall_thresholds": {
            leg: dict(
                zip(("threshold", "k", "n"), phase27_prereg.recall_threshold(frontier_blob, leg))
            )
            for leg in phase27_prereg.LEGS
        },
        "baselines": phase27_prereg.PINNED_BASELINES,
        "fresh_seeds": list(phase27_prereg.FRESH_SEEDS),
        "designated_seed": phase27_prereg.DESIGNATED_SEED,
        "attacker_corpus": dict(phase27_prereg.ATTACKER_CORPUS),
        "budget": {
            "max_steps": phase27_prereg.MAX_STEPS,
            "checkpoint_interval": phase27_prereg.CHECKPOINT_INTERVAL,
            "relearn_cap": phase27_prereg.RELEARN_CAP,
            "rungs": list(phase27_prereg.RUNGS),
            "curve_k": phase27_prereg.CURVE_K,
            "full_k": phase27_prereg.FULL_K,
            "margin_k": phase27_prereg.MARGIN_K,
            "f_y": phase27_prereg.F_Y,
        },
        "apparatus": {
            "status": "pending" if admitted else phase27_prereg.NOT_EXERCISED,
            "reason": (
                "gate read ADMITTED — legs run against the committed record"
                if admitted
                else f"gate read {verdict}"
            ),
            "legs": [dict(leg) for leg in APPARATUS_LEGS],
            "train_path": TRAIN_PATH,
            "fresh_curve_disclosure": phase27_prereg.FRESH_CURVE_DISCLOSURE,
            "device_policy": (
                "never run on MPS in this phase (D-09); the only resolver is phase25_run.device(), "
                "pinned to cpu by the wiring proof"
            ),
            "draw_cache": DRAW_CACHE,
        },
        "disjointness": None,
        "provenance": None,
    }


def admit(out_path=RECORD, *, overwrite=False):
    """THE ONE GATE CALL: write ``results/phase27_admission.json`` WRITE-ONCE, or refuse.

    Order (T-27-07, the ``phase26_canary.emit`` register): the overwrite refusal FIRST, the
    dirty-tree refusal SECOND — before any digest is computed or any torch module is imported — then
    the record, the disjointness (a non-zero overlap is a refused admission), the provenance and
    one atomic write. Never touches git: the operator commits the file by hand (D-15).
    """
    out_path = pathlib.Path(out_path)
    # teach_persona.refuse_if_exists' semantics, reproduced: that module imports torch.
    _prove(
        overwrite or not out_path.exists(),
        f"{_rel(out_path)} exists — REFUSING to overwrite it. The sanctioned route deletes it in "
        "its own commit, then re-runs against a clean tree. Pass --force to overwrite "
        "deliberately.",
    )
    pathspec = ("scripts", "src", "results")
    if out_path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){_rel(out_path)}",)
    refuse_if_dirty(
        who="phase27_relearn",
        detail=(
            "admit publishes git_sha and hashes seven modules and the frontier from the working "
            "tree; a record written from a dirty tree names a commit it cannot be regenerated from"
        ),
        pathspec=pathspec,
        cwd=_ROOT,
    )
    blob = build_record(frontier())
    blob["disjointness"] = disjointness_report()
    overlaps = blob["disjointness"]["overlaps"]
    _prove(
        not any(overlaps.values()),
        f"the recovery fixture overlaps its training material {overlaps} — REFUSING to admit: a "
        "scored question the attacker, the teaching bin or the adversarial arm trained on cannot "
        "measure recovery (D-17)",
    )
    blob["provenance"] = {
        "module_sha256": {rel: _sha256(_ROOT / rel) for rel in PINNED_MODULES},
        "git_sha": INSTRUMENT_GIT_SHA,
        "head_at_write": git_sha(),
        "written_utc": _utc(),
        "torch_version": importlib.metadata.version("torch"),
        "prereg_committed": phase27_prereg.COMMITTED,
    }
    phase25_run.atomic_write_json(out_path, blob)
    counts = blob["cleared_counts"]
    print(
        f"[phase27_relearn] admitted? {blob['verdict']['verdict']}: "
        f"{blob['verdict']['reasons'][0]} — wrote {_rel(out_path)}; cleared (a) {counts['a']} / "
        f"(b) {counts['b']} / (c) {counts['c']}"
    )
    return blob


def make_recorder(stream_path, *, teaching_bin):
    """``(callback, state)`` for ``train(on_draw=...)``: ONE arm's offset stream (D-29, D-30).

    Each draw appends ONE tag byte and then ``ix`` as little-endian uint64 bytes to ``stream_path``
    and folds the same bytes into ``state["sha"]``, so a digest that differs between two arms can
    be located by offset in the files. The tag is ``0`` when the draw's bin RESOLVES to the same
    file as ``teaching_bin`` (identity, against the path ``build_arm_bins`` returned) and ``1``
    otherwise (the replay bin). Never by name suffix: the teaching bin
    ``data/persona_{arm}_train.bin`` and the replay bin ``data/dialog_train.bin`` both end in
    ``_train.bin``, so a suffix test would tag every draw ``0`` and make teaching and replay draws
    indistinguishable (D-30).
    """
    path = pathlib.Path(stream_path)
    _prove(
        not path.exists(),
        f"{_rel(path)} exists — REFUSING to append this run's draws to it: the file's bytes would "
        "stop matching the digest computed over this run alone",
    )
    state = {
        "sha": hashlib.sha256(),
        "draws": 0,
        "path": path,
        "teaching_bin": pathlib.Path(teaching_bin).resolve(),
    }

    def callback(bin_path, ix):
        tag = b"\x00" if pathlib.Path(bin_path).resolve() == state["teaching_bin"] else b"\x01"
        chunk = tag + ix.astype("<u8").tobytes()
        with open(state["path"], "ab") as handle:
            handle.write(chunk)
        state["sha"].update(chunk)
        state["draws"] += 1

    return callback, state


def stream_digest(state):
    """The sha256 over every tagged draw one recorder saw — D-26(iii)'s data-order proof."""
    return state["sha"].hexdigest()


def shared_train_config():
    """The ONE ``TrainConfig`` a leg builds and hands, by reference, to every arm it trains.

    Every budget symbol is read from its home at call time, never retyped. The extra fresh seeds
    receive ``dataclasses.replace(cfg, seed=s)``: ``TrainConfig`` carries ``seed``, so the
    structural proof allows those arms to differ in ``seed`` alone.
    """
    import teach_persona as tp  # LAZY — torch-touching

    return tp.TrainConfig(
        lr=tp.LR,
        warmup_steps=tp.WARMUP_STEPS,
        max_steps=phase27_prereg.RELEARN_CAP,
        batch_size=tp.BATCH_SIZE,
        weight_decay=tp.WEIGHT_DECAY,
        seed=phase27_prereg.DESIGNATED_SEED,
    )


def model_from_adapter(start_adapter, *, expected_sha256, device):
    """The base plus ONE pinned adapter, ready to train. Returns
    ``(model, model_cfg, base_fingerprint, lora_config)``.

    The adapter's sha256 is refused against its pin BEFORE anything is loaded (D-22, T-27-11), and
    both files cross the ``weights_only=True`` choke points ``checkpoint.load_slim`` /
    ``checkpoint.load_adapter`` (T-27-06). LOAD BEFORE INJECT, and inject at the ARTIFACT's own
    config (ISO-06: ``alpha`` is invisible to the key and shape audits), ``_prove``d equal to
    ``teach_persona.LORA_CFG`` so every arm trains at the recipe's config (D-13).
    """
    import teach_persona as tp  # LAZY — torch-touching

    from personacore import checkpoint as ckpt_mod
    from personacore.lora import LoRAConfig, load_adapter_weights

    found = _sha256(start_adapter)
    _prove(
        found == expected_sha256,
        f"{_rel(start_adapter)} hashes to {found}, not the pinned {expected_sha256} — REFUSING "
        "to attack the wrong weights",
    )
    blob = ckpt_mod.load_slim(BASE_SLIM)
    # export_slim's provenance trio (git_sha / step / val_loss), READ off the loaded base.
    fingerprint = {"git_sha": blob["git_sha"], "step": blob["step"], "val_loss": blob["val_loss"]}
    artifact = ckpt_mod.load_adapter(start_adapter, expected_fingerprint=fingerprint)
    _prove(
        artifact["lora_config"] == dataclasses.asdict(tp.LORA_CFG),
        f"{_rel(start_adapter)} carries lora_config {artifact['lora_config']}, not "
        "teach_persona.LORA_CFG — REFUSING: every arm trains at the recipe's config (D-13)",
    )
    model_cfg = tp.ModelConfig(**blob["model_config"])
    model = tp.GPT(model_cfg)
    model.load_state_dict(blob["model"])  # LOAD BEFORE INJECT — the load-bearing ordering
    n_wrapped = tp.inject_lora(model, LoRAConfig(**artifact["lora_config"]))
    _prove(
        n_wrapped == 6 * model_cfg.n_layer,
        f"inject_lora wrapped {n_wrapped} projections, expected 6 * n_layer = "
        f"{6 * model_cfg.n_layer}",
    )
    load_adapter_weights(model, artifact)
    tp.mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected = artifact["lora_config"]["r"] * model_cfg.n_layer * 18 * model_cfg.n_embd
    _prove(
        trainable == expected, f"trainable census {trainable} != r*n_layer*18*n_embd = {expected}"
    )
    model.to(device)
    return model, model_cfg, fingerprint, artifact["lora_config"]


def train_relearn_arm(
    *, arm, leg, seed, cfg, start_adapter, expected_sha256, out_dir, device, point_key=None
):
    """Relearn ONE arm from its pinned adapter on the attacker corpus; write + return its readings.

    ``tp.train()`` is called DIRECTLY with the leg's shared ``cfg`` (27-RESEARCH OQ1 option B —
    ``phase23_run.train_never_taught``'s shape), on bins from ``tp.build_arm_bins`` over the
    pre-registered attacker corpus with the recipe's train-time replay (D-18, D-20). The rungs are
    a RESUME CHAIN: one call per rung with ``max_steps_override=rung``, resuming the checkpoint the
    previous call wrote (D-25, OQ2 — plan 27-02 measured the chain equal to one uninterrupted run),
    each rung's LoRA state exported as its own adapter. The recorder rides ``on_draw`` (D-29).

    The mitigated arm REQUIRES ``point_key`` and every other arm refuses one: the mitigated arm's
    names carry the key (``phase27_{leg}_mitigated_{point_key}_seed{seed}``), so every admitted
    point in a leg trains and scores beside the others instead of colliding with them (D-22).

    Writes (the CPU wiring proof redirects each): bins under ``tp._REPO_ROOT / "data"``, the run CSV
    under ``tp._REPO_ROOT / "results"``, the resume checkpoint under ``tp._REPO_ROOT /
    "checkpoints"``; the rung adapters, the offset stream and the readings JSON under ``out_dir``.
    """
    import numpy as np  # LAZY — kept off the import surface
    import phase14_factset as fs  # LAZY — read at call time (the wiring proof patches it)
    import teach_persona as tp  # LAZY — torch-touching

    from personacore import checkpoint as ckpt_mod
    from personacore.config import RuntimeConfig
    from personacore.lora import lora_state_dict

    _prove(arm in ARMS, f"arm {arm!r} is not one of {ARMS}")
    _prove(
        (point_key is not None) == (arm == "mitigated"),
        f"arm {arm!r} with point_key {point_key!r} — REFUSING: the mitigated arm is named by its "
        "admitted point key and no other arm carries one (D-22)",
    )
    label = arm if point_key is None else f"{arm}_{point_key}"
    name = f"{phase27_prereg.ATTACKER_ARM}_{leg}_{label}_seed{seed}"
    _tok, _stats, paths = tp.build_arm_bins(
        name,
        fs.LOCKED_FACTS,
        fs.TAUGHT_FAMILY_IDS,
        replay_ratio=phase27_prereg.ATTACKER_REPLAY_RATIO,
        seed=seed,
        prefix=phase27_prereg.ATTACKER_PREFIX,
    )
    bin_sha256 = _sha256(paths["bin"])
    # The bin pin is defined over the committed fact set: checked whenever the rendered rows ARE
    # the pinned rows, and recorded as unchecked when they are not (the tiny CPU fixture's facts).
    corpus_pin_checked = (
        phase27_prereg.attacker_corpus_rows_sha256()
        == phase27_prereg.ATTACKER_CORPUS["rows_sha256"]
    )
    _prove(
        not corpus_pin_checked or bin_sha256 == phase27_prereg.ATTACKER_CORPUS["bin_sha256"],
        f"{_rel(paths['bin'])} hashes to {bin_sha256}, not the pre-registered attacker bin — "
        "REFUSING to train on a corpus that is not the one pinned (D-18)",
    )
    # CSVLogger plain-opens its path and nothing creates results/{prefix}_{arm}/; the recorder
    # appends under out_dir. All three before the first train() call.
    paths["csv"].parent.mkdir(parents=True, exist_ok=True)
    paths["checkpoint"].parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    tp.seed_everything(seed)
    model, model_cfg, fingerprint, lora_config = model_from_adapter(
        start_adapter, expected_sha256=expected_sha256, device=device
    )
    before = tp.snapshot_params(model)
    stem = f"phase27_{leg}_{label}_seed{seed}"
    recorder, rstate = make_recorder(out_dir / f"{stem}_offsets.bin", teaching_bin=paths["bin"])
    mask_ones = int(np.fromfile(paths["mask"], dtype=np.uint8).sum())
    # personacore.config's RuntimeConfig, never teach_persona's re-exported name: the Phase-22
    # wiring helper rebinds that name to a ZERO-argument lambda, so a device= call through it
    # raises TypeError under any test that copies the helper.
    runtime = RuntimeConfig(device=device)
    # The flat pack's stats carry no n_facts key (only the fact-aligned DP pack writes one), so the
    # replay budget counts the facts the bins were built from. TOKENS -> WINDOWS: // BLOCK_SIZE.
    n_facts = len(fs.LOCKED_FACTS)
    replay_windows = tp.replay_window_budget(n_facts) // tp.BLOCK_SIZE

    rungs = []
    for rung in phase27_prereg.RUNGS:
        final = tp.train(
            train_config=cfg,
            runtime_config=runtime,
            model=model,
            model_config=model_cfg,
            train_bin=paths["bin"],
            train_mask_bin=paths["mask"],
            val_bin=tp.DIALOG_VAL_BIN,
            val_mask_bin=tp.DIALOG_VAL_MASK,
            replay_bin=tp.DIALOG_TRAIN_BIN,
            replay_mask_bin=tp.DIALOG_TRAIN_MASK,
            replay_windows=replay_windows,
            penalty_fn=None,
            log_path=paths["csv"],
            eval_interval=tp.EVAL_INTERVAL,
            checkpoint_path=paths["checkpoint"],
            checkpoint_interval=phase27_prereg.CHECKPOINT_INTERVAL,
            resume_from=paths["checkpoint"] if rung > phase27_prereg.RUNGS[0] else None,
            max_steps_override=rung,
            return_final_loss=True,
            on_draw=recorder,
        )
        _prove(math.isfinite(float(final)), f"non-finite loss {final!r} at rung {rung} on {name}")
        rung_adapter = out_dir / f"{stem}_rung{rung:04d}_adapter.pt"
        ckpt_mod.export_adapter(
            rung_adapter,
            adapter=lora_state_dict(model),
            lora_config=lora_config,
            base_fingerprint=fingerprint,
        )
        rungs.append(
            {
                "steps": int(rung),
                "scored_tokens": phase27_prereg.scored_tokens(mask_ones=mask_ones, steps=int(rung)),
                "adapter_path": _rel(rung_adapter),
                "adapter_sha256": _sha256(rung_adapter),
            }
        )

    # train_never_taught's canary: every trainable moved, every frozen base param untouched.
    for param_name, param in model.named_parameters():
        if param.requires_grad:
            _prove(
                not tp.torch.equal(param, before[param_name]),
                f"[canary] trainable {param_name} did not move on {name} — silent training failure",
            )
        else:
            _prove(
                tp.torch.equal(param, before[param_name]),
                f"[canary] frozen base param {param_name} changed on {name} — isolation broken",
            )
    # A READ of the checkpoint train() just wrote (D-26 ii). load_checkpoint also restores the RNG
    # state it saved: benign here, training is over and the next arm re-seeds.
    checkpoint = ckpt_mod.load_checkpoint(paths["checkpoint"], model=model)

    readings = {
        "arm": arm,
        "point_key": point_key,
        "leg": leg,
        "seed": seed,
        "device": device,
        "start_adapter": _rel(start_adapter),
        "start_sha256": expected_sha256,
        "train_config": dataclasses.asdict(cfg),
        "checkpoint_train_config": checkpoint["train_config"],
        "bin_path": _rel(paths["bin"]),
        "bin_sha256": bin_sha256,
        "bin_bytes": paths["bin"].stat().st_size,
        "mask_ones": mask_ones,
        "n_facts": n_facts,
        "replay_windows": replay_windows,
        "rungs": rungs,
        "offset_stream": {
            "path": _rel(rstate["path"]),
            "sha256": stream_digest(rstate),
            "draws": rstate["draws"],
            "teaching_bin": _rel(paths["bin"]),
        },
        "train_path": TRAIN_PATH,
        "corpus_pin_checked": corpus_pin_checked,
    }
    phase25_run.atomic_write_json(out_dir / f"{stem}_readings.json", readings)
    return readings


def score_rung(*, point_label, adapter_path, k, out_dir, device, facts, values):
    """One rung adapter's readings: recall REPORTED, extraction DECIDES (D-16, D-21). Counts only.

    Recall is ``tp.score_arm`` read as ``phase25_recall`` reads it; extraction is
    ``phase25_run.draw_point_shapes`` + ``score_point`` over ``phase18_extraction.build_corpus``,
    cached at ``phase25_run.draws_path(point_label)``. ``load_draws`` refuses a cache whose recorded
    ``k`` differs, so ``point_label`` must end in ``_k{k}``: a CURVE_K and a FULL_K reading of one
    rung never share a file.

    TWO NAMES A FIXTURE MUST REDIRECT, because this function's arguments do not reach them: both
    scorers load the base through ``phase14_recall.CONVBASE_SLIM`` (``pr.load_adapted_model``),
    not through ``BASE_SLIM``, and the draw loop resolves its device through
    ``phase25_run.device()``, not through ``device``. ``out_dir`` is accepted for the legs' one
    call shape; the only file this function writes is the draw cache under
    ``phase25_run.DRAWS_DIR``.
    """
    import phase18_extraction as x18  # LAZY — torch-touching
    import teach_persona as tp  # LAZY — torch-touching

    from personacore.tokenizer import from_json

    _prove(
        point_label.endswith(f"_k{k}"),
        f"draw-cache label {point_label!r} does not end in _k{k} — a reading at another K would "
        "collide with this one's cache, which load_draws refuses",
    )
    scored = tp.score_arm(point_label, facts, adapter_path, device)
    tok = from_json(tp.TOKENIZER_PATH)
    corpus = x18.build_corpus(tok)
    blob, _digests = phase25_run.draw_point_shapes(
        point_label,
        adapter=adapter_path,
        adapter_sha256=_sha256(adapter_path),
        corpus=corpus,
        corpus_sha256=x18.corpus_sha256(corpus),
        k=k,
        state={},
    )
    per_question, _per_fact, _scored = phase25_run.score_point(blob, values)
    gated = per_question[phase27_prereg.GATED_TIER]
    return {
        "k": k,
        "point_label": point_label,
        "draws_cache": _rel(phase25_run.draws_path(point_label)),
        "taught_recall": {
            "numerator": int(scored["on_taught"]["k"]),
            "denominator": int(scored["on_taught"]["n"]),
        },
        "heldout_recall": {
            "numerator": int(scored["on_heldout"]["k"]),
            "denominator": int(scored["on_heldout"]["n"]),
        },
        # score_point's per-question success is `answered` (any of the k draws contained the
        # value) — the unit phase25_points._family_counts sums into point_extraction_successes.
        "extraction": {
            "successes": sum(1 for row in gated if row["answered"]),
            "questions": len(gated),
        },
    }


def run_calibrate(*, record, leg, out_dir):
    """Z CALIBRATION (D-24, D-25, D-27, D-28, SC2): the fresh arm at every pinned seed and the
    control at the designated seed, relearned on the attacker corpus and scored at every rung.

    Z is ``phase27_prereg.z_rule`` over the first rung each arm clears the frontier's own condition
    (b), ``recall_threshold`` — the pooled fresh seed, never a sum across seeds. The per-seed fresh
    taught rates at each rung are written as the band's noise-floor inputs (D-19).
    ``phase25_run.device()`` is the ONLY device resolver: it caches ``_DEVICE`` and resolves MPS on
    the dev box, which is why no leg may pass ``_require_admitted`` in this phase (D-09) and why the
    CPU wiring proof pins ``phase25_run._DEVICE = "cpu"``.
    """
    blob = _require_admitted(record)
    import phase14_factset as fs  # LAZY — read at call time (the wiring proof patches it)
    import phase25_points  # LAZY — kept off the import surface

    device = phase25_run.device()
    cfg = shared_train_config()
    threshold, k, n = phase27_prereg.recall_threshold(frontier(), leg)
    values = phase25_points.scoring_values()

    def relearned(arm, seed, arm_cfg, baseline_key):
        pin = blob["baselines"][baseline_key]
        trained = train_relearn_arm(
            arm=arm,
            leg=leg,
            seed=seed,
            cfg=arm_cfg,
            start_adapter=_ROOT / pin["path"],
            expected_sha256=pin["sha256"],
            out_dir=out_dir,
            device=device,
        )
        return [
            {
                **rung,
                **score_rung(
                    point_label=f"phase27_{leg}_{arm}_seed{seed}_rung{rung['steps']:04d}"
                    f"_k{phase27_prereg.CURVE_K}",
                    adapter_path=_ROOT / rung["adapter_path"],
                    k=phase27_prereg.CURVE_K,
                    out_dir=out_dir,
                    device=device,
                    facts=fs.LOCKED_FACTS,
                    values=values,
                ),
            }
            for rung in trained["rungs"]
        ]

    def triples(readings):
        return [
            (
                int(r["steps"]),
                int(r["taught_recall"]["numerator"]),
                int(r["taught_recall"]["denominator"]),
            )
            for r in readings
        ]

    seeds = phase27_prereg.FRESH_SEEDS
    # The designated seed receives the shared instance itself; the other seeds a copy that differs
    # in `seed` alone (the D-26 x D-27 resolution).
    per_seed = {
        s: relearned(
            "fresh",
            s,
            cfg if s == cfg.seed else dataclasses.replace(cfg, seed=s),
            f"never_taught_{s}",
        )
        for s in seeds
    }
    control = relearned("control", cfg.seed, cfg, f"control_{leg}")
    pooled = seeds[phase27_prereg.POOLED_SEED_INDEX]
    fresh_first = phase27_prereg.first_clear(triples(per_seed[pooled]), threshold)
    control_first = phase27_prereg.first_clear(triples(control), threshold)
    z, z_reasons = phase27_prereg.z_rule(
        fresh_first_clear=fresh_first, control_first_clear=control_first
    )
    calibration = {
        "leg": leg,
        "threshold": {"value": threshold, "k": k, "n": n, "f_y": phase27_prereg.F_Y},
        "fresh": {
            "per_seed": {str(s): per_seed[s] for s in seeds},
            "pooled_seed": pooled,
            "first_clear": fresh_first,
        },
        "control": {"seed": cfg.seed, "readings": control, "first_clear": control_first},
        "z": z,
        "z_reasons": z_reasons,
        "relearn_cap": phase27_prereg.RELEARN_CAP,
        "rungs": list(phase27_prereg.RUNGS),
        "curve_k": phase27_prereg.CURVE_K,
        "fresh_readings_at_each_rung": {
            str(row[0]["steps"]): [
                r["taught_recall"]["numerator"] / r["taught_recall"]["denominator"] for r in row
            ]
            for row in zip(*(per_seed[s] for s in seeds))
        },
        "train_path": TRAIN_PATH,
        "device": device,
    }
    phase25_run.atomic_write_json(out_dir / f"phase27_{leg}_calibration.json", calibration)
    print(f"[phase27_relearn] calibrate {leg}: Z = {z} steps ({z_reasons[0]})", flush=True)
    return calibration


def run_curve(*, record, leg, out_dir):
    """THE COST-TO-RECOVERY CURVE (D-19, D-21, D-22, D-23; RELRN-03, SC3) — a finding, never a gate.

    Every admitted point in this leg, in ``admitted_point_keys`` order (D-22 — never a subset), is
    relearned from its frontier adapter (sha256-pinned, refused on mismatch) at the designated seed
    with the leg's shared config, scored at every rung at CURVE_K, and placed against the fresh
    arm's band at that rung (D-19). The reading at Z travels beside the rungs for ``gate``.
    """
    blob = _require_admitted(record)
    import phase14_factset as fs  # LAZY — read at call time (the wiring proof patches it)
    import phase25_points  # LAZY — kept off the import surface

    calibration_path = out_dir / f"phase27_{leg}_calibration.json"
    _prove(
        calibration_path.exists(),
        f"{_rel(calibration_path)} is absent — REFUSING: run calibrate first; the band and Z "
        "come from it",
    )
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    keys = [key for key in blob["admitted_point_keys"] if phase27_prereg.leg_of(key) == leg]
    device = phase25_run.device()
    cfg = shared_train_config()
    values = phase25_points.scoring_values()
    fr = frontier()
    points = {}
    for key in keys:
        entry = fr["points"][key]
        trained = train_relearn_arm(
            arm="mitigated",
            leg=leg,
            seed=cfg.seed,
            cfg=cfg,
            start_adapter=_ROOT / entry["adapter_path"],
            expected_sha256=entry["adapter_sha256"],
            out_dir=out_dir,
            device=device,
            point_key=key,
        )
        rungs = []
        for rung in trained["rungs"]:
            reading = score_rung(
                point_label=f"phase27_{leg}_{key}_rung{rung['steps']:04d}_k{phase27_prereg.CURVE_K}",
                adapter_path=_ROOT / rung["adapter_path"],
                k=phase27_prereg.CURVE_K,
                out_dir=out_dir,
                device=device,
                facts=fs.LOCKED_FACTS,
                values=values,
            )
            taught = reading["taught_recall"]
            band = phase27_prereg.band(
                mitigated=taught["numerator"] / taught["denominator"],
                fresh_readings=calibration["fresh_readings_at_each_rung"][str(rung["steps"])],
            )
            rungs.append({**rung, **reading, "band": band})
        points[key] = {
            "rungs": rungs,
            "reading_at_z": next((row for row in rungs if row["steps"] == calibration["z"]), None),
        }
    curve = {
        "leg": leg,
        "z": calibration["z"],
        "points": points,
        "finding": (
            "the cost curve QUALIFIES the gate's reading; it is not a second gate (RELRN-03)"
        ),
        "curve_k": phase27_prereg.CURVE_K,
        "train_path": TRAIN_PATH,
        "device": device,
    }
    phase25_run.atomic_write_json(out_dir / f"phase27_{leg}_curve.json", curve)
    print(f"[phase27_relearn] curve {leg}: {len(points)} point(s) at Z = {curve['z']}", flush=True)
    return curve


def run_gate(*, record, leg, out_dir, baseline):
    """THE RECOVERY-CEILING GATE (RELRN-01, D-09, D-16, D-21): per admitted point, recovered
    extraction at or below X within Z, against a PINNED baseline chosen on the command line.

    X is read BY CALL (``phase27_prereg.extraction_ceiling_x``) on the control points' stored
    counts, never from the frontier's summary field. The reading at Z is taken at CURVE_K; the
    gate's own promotion rule decides whether it is re-scored at FULL_K under its OWN k-suffixed
    cache label (``phase25_run.load_draws`` refuses a cache whose recorded k differs — Phase 25's
    feature, answered by the suffix). The gate is called in ONE place, ``_verdict``, with exactly
    five keywords: nothing from the curve or the band reaches it (RELRN-03). Taught recall travels
    in the same row and never decides.
    """
    blob = _require_admitted(record)
    import phase14_factset as fs  # LAZY — read at call time (the wiring proof patches it)
    import phase25_points  # LAZY — kept off the import surface

    calibration_path = out_dir / f"phase27_{leg}_calibration.json"
    curve_path = out_dir / f"phase27_{leg}_curve.json"
    for path in (calibration_path, curve_path):
        _prove(path.exists(), f"{_rel(path)} is absent — REFUSING: run calibrate and curve first")
    z = json.loads(calibration_path.read_text(encoding="utf-8"))["z"]
    curve = json.loads(curve_path.read_text(encoding="utf-8"))
    _prove(
        curve["z"] == z,
        f"{_rel(curve_path)} was built at Z = {curve['z']} but the calibration reads Z = {z} — "
        "REFUSING a curve from another calibration",
    )
    keys = [key for key in blob["admitted_point_keys"] if phase27_prereg.leg_of(key) == leg]
    _prove(
        sorted(curve["points"]) == sorted(keys),
        f"the curve covers {sorted(curve['points'])}, the record admits {keys} in leg {leg} — "
        "REFUSING: every admitted point is judged (D-22)",
    )
    device = phase25_run.device()
    x = phase27_prereg.extraction_ceiling_x(frontier())
    values = phase25_points.scoring_values()

    def _verdict(successes, questions, z_value):
        return phase27_prereg.recovery_gate(
            recovered_successes=int(successes),
            recovered_questions=int(questions),
            x=x,
            z=z_value,
            baseline=baseline,
        )

    def gated_draws(point_label):
        cache = json.loads(phase25_run.draws_path(point_label).read_text(encoding="utf-8"))
        return {
            (draw["family"], draw["fact_id"], draw["seed_index"]): draw["completions"]
            for shape in cache["shapes"].values()
            for draw in shape["draws"]
            if draw["tier"] == phase27_prereg.GATED_TIER
        }

    points = {}
    for key in keys:
        rungs = curve["points"][key]["rungs"]
        # Z undefined: no reading at Z exists, so the cap rung's MEASURED counts go to the gate,
        # which reads INCONCLUSIVE on z=None whatever they are.
        at = curve["points"][key]["reading_at_z"] if z is not None else rungs[-1]
        _prove(at is not None, f"{key}: the curve holds no reading at Z = {z}")
        provisional, provisional_reasons = _verdict(
            at["extraction"]["successes"], at["extraction"]["questions"], z
        )
        promoted, promotion_reason = phase27_prereg.promote_at_z(provisional, provisional_reasons)
        verdict, reasons, reading, prefix_identical = provisional, provisional_reasons, at, None
        if promoted:
            adapter = _ROOT / at["adapter_path"]
            _prove(
                _sha256(adapter) == at["adapter_sha256"],
                f"{at['adapter_path']} no longer hashes to the rung adapter the curve scored — "
                "REFUSING to re-score other weights",
            )
            reading = score_rung(
                point_label=f"phase27_{leg}_{key}_rung{z:04d}_k{phase27_prereg.FULL_K}",
                adapter_path=adapter,
                k=phase27_prereg.FULL_K,
                out_dir=out_dir,
                device=device,
                facts=fs.LOCKED_FACTS,
                values=values,
            )
            # D-21's bit-identical-prefix claim, MEASURED from the two caches and recorded, never
            # proved: every gated question's CURVE_K draws equal the first CURVE_K FULL_K draws.
            curve_draws = gated_draws(at["point_label"])
            full_draws = gated_draws(reading["point_label"])
            prefix_identical = curve_draws.keys() == full_draws.keys() and all(
                full_draws[question][: at["k"]] == draws for question, draws in curve_draws.items()
            )
            verdict, reasons = _verdict(
                reading["extraction"]["successes"], reading["extraction"]["questions"], z
            )
        points[key] = {
            "verdict": verdict,
            "reasons": reasons,
            "provisional": {"verdict": provisional, "reasons": provisional_reasons, "k": at["k"]},
            "recovered": {
                **reading["extraction"],
                "k": reading["k"],
                "steps": at["steps"],
                "draws_cache": reading["draws_cache"],
            },
            "taught_recall_reported": reading["taught_recall"],
            "promoted": promoted,
            "promotion_reason": promotion_reason,
            "prefix_identical": prefix_identical,
        }
        print(f"[phase27_relearn] gate {leg} {key}: {verdict} — {reasons[0]}", flush=True)
    gate = {
        "leg": leg,
        "baseline": baseline,
        "x": x,
        "z": z,
        "points": points,
        "cost_curve_ref": curve_path.name,
        "finding_is_not_a_gate": True,
        "device": device,
    }
    phase25_run.atomic_write_json(out_dir / f"phase27_{leg}_gate.json", gate)
    return gate


def run_structural_proof(*, record, leg, out_dir):
    """THE THREE IDENTICAL-BUDGET PROOFS (RELRN-04, D-26 i/ii/iii, SC5), read back OFF DISK.

    (i) every arm's recorded ``train_config`` equals the designated-seed fresh arm's on every field
    — the extra fresh seeds may differ in ``seed`` alone; (ii) every arm's recorded config equals
    the one ``train()`` wrote into its checkpoint; (iii) the offset-stream digests, with the bin
    lengths beside them: equal seed and equal bin length should give equal streams, so the
    equality is RECORDED, never proved. Reads JSON only — no device, no torch.
    """
    blob = _require_admitted(record)
    designated = phase27_prereg.DESIGNATED_SEED
    readings = {}
    for path in sorted(out_dir.glob(f"phase27_{leg}_*_readings.json")):
        reading = json.loads(path.read_text(encoding="utf-8"))
        # The mitigated arms carry their point key, so two admitted points never share a label.
        arm, point_key = reading["arm"], reading["point_key"]
        arm_label = arm if point_key is None else f"{arm}_{point_key}"
        label = f"{arm_label}_seed{reading['seed']}"
        _prove(
            label not in readings,
            f"two readings under {_rel(out_dir)} are labelled {label!r} — REFUSING: one would "
            "silently replace the other in every proof below",
        )
        readings[label] = reading
    arms = sorted({reading["arm"] for reading in readings.values()})
    _prove(
        len(arms) >= 2,
        f"readings for {arms} under {_rel(out_dir)} — REFUSING: a structural proof compares at "
        "least two arms",
    )
    reference_label = f"fresh_seed{designated}"
    _prove(
        reference_label in readings,
        f"no {reference_label} readings under {_rel(out_dir)} — REFUSING: the designated-seed "
        "fresh arm is the reference every other arm is compared to",
    )
    reference = readings[reference_label]["train_config"]

    differing_fields = {}
    for label, reading in readings.items():
        config = reading["train_config"]
        differing = sorted(
            f for f in set(config) | set(reference) if config.get(f) != reference.get(f)
        )
        allowed = {"seed"} if reading["arm"] == "fresh" and reading["seed"] != designated else set()
        _prove(
            set(differing) <= allowed,
            f"{label}'s train_config differs from {reference_label}'s on {differing} — REFUSING: "
            f"only {sorted(allowed)} may differ (D-26 i)",
        )
        differing_fields[label] = differing

    off_disk = {}
    for label, reading in readings.items():
        off_disk[label] = reading["train_config"] == reading["checkpoint_train_config"]
        _prove(
            off_disk[label],
            f"{label}: the train_config the driver recorded differs from the one train() wrote "
            "into the checkpoint — REFUSING (D-26 ii)",
        )

    at_designated = [reading for reading in readings.values() if reading["seed"] == designated]
    fresh = [reading for reading in readings.values() if reading["arm"] == "fresh"]
    data_order = {
        "sha256": {
            label: reading["offset_stream"]["sha256"] for label, reading in readings.items()
        },
        "bin_bytes": {label: reading["bin_bytes"] for label, reading in readings.items()},
        "equal_across_arms_at_designated_seed": (
            len({reading["offset_stream"]["sha256"] for reading in at_designated}) == 1
        ),
        "equal_bin_bytes_at_designated_seed": (
            len({reading["bin_bytes"] for reading in at_designated}) == 1
        ),
        "differs_across_seeds": (
            len({reading["offset_stream"]["sha256"] for reading in fresh}) == len(fresh)
        ),
        "devices": {label: reading["device"] for label, reading in readings.items()},
    }
    structural = {
        "leg": leg,
        "admitted_point_keys": [
            key for key in blob["admitted_point_keys"] if phase27_prereg.leg_of(key) == leg
        ],
        "shared_config": {"reference": reference_label, "differing_fields": differing_fields},
        "off_disk": off_disk,
        "data_order": data_order,
        "train_path": TRAIN_PATH,
    }
    phase25_run.atomic_write_json(out_dir / f"phase27_{leg}_structural.json", structural)
    print(
        f"[phase27_relearn] structural-proof {leg}: {len(readings)} arm reading(s); equal streams "
        f"at the designated seed: {data_order['equal_across_arms_at_designated_seed']}",
        flush=True,
    )
    return structural


DISPATCH = {
    "admit": admit,
    "calibrate": run_calibrate,
    "curve": run_curve,
    "gate": run_gate,
    "structural-proof": run_structural_proof,
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Phase 27 relearning attack: admit once, then four legs gated on the record."
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    admit_parser = sub.add_parser("admit", help="write results/phase27_admission.json once")
    admit_parser.add_argument("--force", action="store_true", help="overwrite an existing record")
    admit_parser.add_argument("--out", default=str(RECORD))
    for mode in SUB_MODES[1:]:
        leg_parser = sub.add_parser(mode, help=f"the {mode} leg — refuses unless ADMITTED")
        leg_parser.add_argument("--record", default=str(RECORD))
        leg_parser.add_argument("--leg", choices=phase27_prereg.LEGS, required=True)
        leg_parser.add_argument("--out-dir", default=str(STREAM_DIR))
        if mode == "gate":
            # REQUIRED and a closed choice: the CLI cannot be invoked without a pinned baseline.
            leg_parser.add_argument(
                "--baseline", choices=phase27_prereg.BASELINE_KEYS, required=True
            )
    return parser


def main(argv=None):
    """Dispatch through ``DISPATCH`` with EXPLICIT keyword names per mode (D-10's kwargs trace)."""
    args = build_parser().parse_args(argv)
    if args.mode == "admit":
        kwargs = {"out_path": pathlib.Path(args.out), "overwrite": args.force}
    elif args.mode == "gate":
        kwargs = {
            "record": pathlib.Path(args.record),
            "leg": args.leg,
            "out_dir": pathlib.Path(args.out_dir),
            "baseline": args.baseline,
        }
    else:
        kwargs = {
            "record": pathlib.Path(args.record),
            "leg": args.leg,
            "out_dir": pathlib.Path(args.out_dir),
        }
    DISPATCH[args.mode](**kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
