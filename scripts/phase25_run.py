"""THE 44-POINT FRONTIER DRIVER — the process that spends this phase's 107-150 GPU hours.

**THIS IS A PORT, NOT AN INVENTION, AND SAYING SO IS THE POINT.** D-09's shape-keyed block resume
already exists in full at `scripts/phase23_run.py`: `_never_taught_draws_path` builds the cache
path, `_never_taught_load_draws` refuses a cache whose `(adapter_sha256, corpus_sha256, k)` do not
describe this measurement, the draw loop skips a shape already present, and the block is persisted
as each shape completes. All four are ported here onto the 44-point key space with Phase 25's paths.
`scripts/phase23_run.py` itself is READ and never modified.

**THE ONE REAL GAP WAS THE WRITE, AND IT WAS [BLOCKING].** `phase23_run._never_taught_write_draws`
is `path.write_text(json.dumps(blob, sort_keys=True))` over a block MEASURED at **973,486 bytes**
(`data/phase23_never_taught_seed1337_draws.json`, 28 Aug 2026). A kill landing inside that single
`write_text` truncates the destination, and the next `json.loads` rejects the whole file — which
converts D-09's "a kill costs one shape (~33 min)" into "a kill costs the whole point (~2.2 h)",
the exact failure D-09 exists to prevent. :func:`atomic_write_json` closes it.

  CORRECTION TO 25-10-PLAN.md, MEASURED. The plan states `grep -rn "os.replace" scripts/ src/`
  returns **0** and that "there is NO atomic-write helper anywhere in the repo". Measured on the
  tree this module was written against, that command returns **2** hits, both in
  `scripts/phase25_record.py` — line 941 is a live `os.replace` and line 913 its docstring.
  `phase25_record.write_point_record` (wave 2) already writes the per-point RECORD atomically by
  exactly this recipe. So the atomic write is a SECOND application of a same-phase sibling's
  pattern rather than the first in the repository. The gap the plan identified is real and
  unchanged in substance — the DRAW CACHE, which is 973,486 B against the record's ~100 KB, is
  written non-atomically by `phase23_run` and is what this module fixes — but the claim of
  novelty is false and is corrected here rather than inherited.

**§O1 — THE DRIVER COMMITS, AND THAT IS A DELIBERATE, NAMED, PHASE-LOCAL EXCEPTION.**
`.planning/STATE.md` records the Phase-23 mechanism verbatim: *"THE PER-SEED COMMIT DISCIPLINE HELD,
AND IT IS A MECHANISM. The driver's git surface is read-only, so the sub-mode scores exactly ONE
unscored seed and exits; the commit is the operator's act at the process boundary."* That discipline
cannot hold here, for three checkable reasons recorded at
:data:`phase25_prereg.GIT_SURFACE_EXCEPTION`. This driver therefore runs `git add` and `git commit`,
**scoped to the record of the point it just completed and to nothing else**.

`config.json` sets `branching_strategy: none`, so those commits land on **`main`**. That is a
CONSEQUENCE of §O1 rather than an accident, and it is named here so it is never discovered. The
mitigation is the scoping itself: each commit stages exactly one existing file under `results/`,
resolved from `phase25_record.point_record_path`, so a six-day unattended run cannot stage source,
tests, planning documents, or anything under the gitignored `data/` and `checkpoints/`.

**"NARROWLY SCOPED" IS A STRUCTURAL GUARANTEE HERE, NOT PROSE.**
:data:`ALLOWED_GIT_ACTIONS` and :data:`READ_ONLY_GIT_ACTIONS` are enforced from OUTSIDE this file by
`tests/test_phase25_driver.py::test_the_drivers_executable_git_actions_are_exactly_add_and_commit`,
an **AST walk over this very module** that resolves the first argv element after `"git"` at every
`subprocess` call site and refuses any subcommand outside those two tuples. The check is
deliberately not implemented here: a module that checks itself proves nothing, because the same
edit that widens the surface is free to weaken the check. It also cannot be a grep — this docstring
names `git push` and `git rm` on purpose, so a textual gate over this file goes FALSE-RED today.
Only a parse can tell prose about a name from the name
(`tests/test_phase24_correction.py`'s mechanic 4; RPT-02).

**THE HEARTBEAT IS A WALL-CLOCK BEAT FROM A THREAD, AND THE MEASUREMENT IS WHY.** See
:func:`_heartbeat_loop`.

CPU-safe at import: `torch` and every model module are imported INSIDE the functions that need
them, so `--dry-run` and the whole test battery run without touching a GPU.
"""

import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent

_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_SRC = str(_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import phase25_prereg  # noqa: E402  (needs the sys.path insert; scripts/ is not a package)
import phase25_record  # noqa: E402  (same)
import phase25_venue  # noqa: E402  (same) — the launch banner's ONE producer

# `phase18_extraction` is NOT imported here. It is heavy and torch-touching, and `phase23_run.py`
# imports it lazily for exactly that reason (`phase23_run.py:4316`). A module-scope import would
# make `--dry-run` — and every test in this plan's battery — pull torch. The three constants this
# module needs from it (`ATTACK_FAMILIES`, `GATED_TIER`, `REPORTED_TIER`) are already re-exported
# by `phase25_record`, which resolves them from the COMMITTED LITERAL via
# `phase25_gate05._committed_literal` and therefore never imports the module at all.
ATTACK_FAMILIES = phase25_record.ATTACK_FAMILIES


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — `phase25_record._prove`'s register, this prefix.

    ``SystemExit`` and deliberately NOT ``assert``: an ``assert`` is strippable under ``-O``, and a
    proof that disappears under an optimisation flag is not a proof.
    """
    if not condition:
        raise SystemExit(f"[phase25_run] {message}")


def _rel(path):
    """A repo-relative rendering for the log, falling back to the absolute path off-tree."""
    try:
        return str(pathlib.Path(path).resolve().relative_to(_ROOT))
    except ValueError:
        return str(path)


# =================================================================================================
# ===== (a) THE ATOMIC WRITE — THE [BLOCKING] GAP, CLOSED BEFORE ANY POINT RUNS =====
# =================================================================================================


def atomic_write_json(path, blob):
    """Serialise ``blob`` and land it at ``path`` ATOMICALLY. Returns ``path``.

    **EVERY STEP IS LOAD-BEARING AND NONE IS DECORATION:**

      * **Serialise FIRST, before opening anything.** A blob carrying a non-serialisable value then
        leaves NO file at all rather than a truncated one. `phase23_run.py:4470` records this
        failure the expensive way: a `Tensor` echoed into the block raised
        ``TypeError: Object of type Tensor is not JSON serializable`` inside `json.dumps` AFTER
        2.3 h of drawing.
      * **A temporary file in the DESTINATION'S OWN DIRECTORY.** ``os.replace`` is atomic on POSIX
        only WITHIN one filesystem. A temp file in ``/tmp`` crossing a mount point silently
        degrades the rename into a copy-then-unlink, which is exactly the torn write this function
        exists to prevent.
      * **``flush()`` then ``os.fsync()`` BEFORE the replace.** Without the fsync the RENAME can be
        durable while the BYTES are not: after a power loss the directory entry points at a file
        whose contents never reached the platter. `fsync` orders the data before the metadata.
      * **``os.replace`` and not ``os.rename``.** ``replace`` overwrites an existing destination on
        every platform; ``rename`` does not on Windows.
      * **The temp file is unlinked on ANY exception**, including ``KeyboardInterrupt`` and
        ``SystemExit`` — hence ``BaseException``. A crashed write must leave the previous blob
        intact AND no stray sibling that a later glob would read as a real cache.

    THE MEASUREMENT THAT MOTIVATES IT: the block this replaces is **973,486 bytes**
    (`data/phase23_never_taught_seed1337_draws.json`), and the writer being replaced,
    `phase23_run._never_taught_write_draws`, is a bare ``path.write_text``. A kill inside that call
    yields JSON ``json.loads`` rejects, turning D-09's "lose one shape (~33 min)" into "lose the
    whole point (~2.2 h)".
    """
    path = pathlib.Path(path)
    payload = json.dumps(blob, sort_keys=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        pathlib.Path(handle.name).unlink(missing_ok=True)
        raise
    return path


# =================================================================================================
# ===== (b) THE PORTED CACHE HELPERS — PHASE 23'S MECHANISM, PHASE 25'S KEY SPACE =====
# =================================================================================================

DRAWS_DIR = _ROOT / "data"

CACHE_IDENTITY_FIELDS = ("adapter_sha256", "corpus_sha256", "k")


def draws_path(point_key):
    """Where ONE point's RAW draws are persisted, per shape, as they are produced.

    Under ``data/`` and therefore gitignored (`.gitignore:17`) — this is working state, not a
    published artifact, and every figure derived from it lands in the committed point record. It is
    ALSO why each completed shape block's sha256 travels inside that record (D-10): with the cache
    invisible to git, the recorded digests are the only residue a delete-and-redraw would leave.

    The key is routed through `phase25_prereg.point_record_path` purely for its charset refusal, so
    one rule governs both the record path and this one; the returned string is discarded.
    """
    phase25_prereg.point_record_path(point_key)
    return DRAWS_DIR / f"phase25_{point_key}_draws.json"


def load_draws(path, *, adapter_sha256, corpus_sha256, k):
    """Recorded draws for this point, REFUSED unless they describe this exact measurement.

    `phase23_run._never_taught_load_draws`'s three-field identity, ported verbatim in BEHAVIOUR with
    the message rewritten to name Phase 25's paths. A missing cache is the normal first-attempt
    state and returns an empty blob rather than raising.

    **THAT ``k`` IS PART OF THE IDENTITY BUYS D-11'S CORRECTNESS FOR FREE, AND IT IS NAMED HERE
    RATHER THAN DISCOVERED.** A point promoted from ``CURVE_K = 16`` to ``FULL_FIDELITY_K = 48``
    REFUSES to reuse its own K=16 draws, because the recorded ``k`` no longer matches. Without that
    field the promotion would silently pool 16-draw and 48-draw questions into one reading and
    publish it at the higher K's apparent statistical power. The refusal is a FEATURE.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return {
            "adapter_sha256": adapter_sha256,
            "corpus_sha256": corpus_sha256,
            "k": k,
            "shapes": {},
        }
    blob = json.loads(path.read_text(encoding="utf-8"))
    for field, expected in (
        ("adapter_sha256", adapter_sha256),
        ("corpus_sha256", corpus_sha256),
        ("k", k),
    ):
        _prove(
            blob.get(field) == expected,
            f"{_rel(path)} records {field}={blob.get(field)!r} against this point's "
            f"{expected!r}. Reusing it would pool draws taken off different weights, a different "
            "corpus or a DIFFERENT DRAW BUDGET into one reading — the last of which is D-11's "
            "K=16 to K=48 promotion, where the pooled reading would be published at the higher "
            "K's apparent power. Delete it in a reviewed step to re-draw",
        )
    return blob


def write_draws(path, blob):
    """Persist the point's draw cache. ATOMIC, via :func:`atomic_write_json`.

    This is the one line that differs from `phase23_run._never_taught_write_draws`, and it is the
    [BLOCKING] fix: that function's ``path.write_text`` over 973,486 B is not atomic.
    """
    return atomic_write_json(path, blob)


# =================================================================================================
# ===== (c) THE SKIP-COMPLETE-SHAPE BRANCH — "COMPLETE" IS A CONJUNCTION =====
# =================================================================================================


def shape_is_complete(blob, family):
    """``True`` when ``family``'s block carries BOTH ``draws`` and ``timing``.

    **A CONJUNCTION, AND DELIBERATELY STRONGER THAN THE PORT SOURCE.**
    `phase23_run.py:4452` tests `if family in recorded["shapes"]` — a PRESENCE check — and then
    reads `shape["draws"]` and `shape["timing"]` unconditionally. That is safe there only because
    the single writer sets both keys in one dict literal. Here the writer is atomic and the reader
    must survive a blob written by an older or a partial writer, so completeness is asserted on the
    two fields the resume path actually consumes. A block carrying `draws` but no `timing` is
    INCOMPLETE and is redrawn from scratch: a half block that skipped would drop a shape's timing
    out of the record silently, and the record's rate figures are what price the sweep.
    """
    shape = blob.get("shapes", {}).get(family)
    return isinstance(shape, dict) and "draws" in shape and "timing" in shape


def pending_shapes(blob, families=None):
    """The families still owed a draw block, in `phase18_extraction.ATTACK_FAMILIES` order."""
    families = ATTACK_FAMILIES if families is None else families
    return tuple(family for family in families if not shape_is_complete(blob, family))


def block_sha256(blob, family):
    """The sha256 of one completed shape block's canonical bytes — D-10's residue.

    Recorded into the point record as each shape lands. `data/` is gitignored, so without these
    digests a delete-and-redraw INSIDE one point would leave no trace at all; with them, the
    committed record pins the bytes the reading came off.
    """
    import hashlib

    canonical = json.dumps(blob["shapes"][family], sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# =================================================================================================
# ===== (d) THE HEARTBEAT — WALL-CLOCK, APPEND-ONLY, FROM ITS OWN THREAD (D-12) =====
# =================================================================================================

HEARTBEAT_PATH = _ROOT / "data" / "phase25_heartbeat.jsonl"

# The five fields, and the SAME five `phase25_watch.HEARTBEAT_FIELDS` reads. A test asserts the two
# tuples are equal as sets: a mis-shaped line does not raise in the watcher, it yields `None` in the
# diagnostic fields — so a silently wrong beat would never fail loudly on its own.
HEARTBEAT_FIELDS = ("utc", "point", "stage", "shape", "draw_index")

# The stages a beat can name. `train` is the one that matters: it is the 23.05-min leg that emits no
# draw-loop line at all, and the reason the beat cannot be event-driven.
STAGES = ("start", "train", "draw", "score", "record", "commit", "done")


def beat(heartbeat_path, *, point, stage, shape, draw_index):
    """Append EXACTLY ONE JSON line carrying the five fields. Returns the beat dict.

    **APPEND-ONLY AND LINE-ORIENTED, WHICH IS THE WHOLE POINT.** The interesting case for this file
    is a process killed mid-write, so the last bytes on disk are the ones most likely to be half a
    line. With append-only lines a torn tail costs at most the newest beat and every earlier beat
    stays parseable — which is precisely what `phase25_watch.read_last_beat`'s backwards walk
    handles. A rewritten JSON blob would leave a file `json.loads` rejects outright and lose the
    diagnostic value of every beat ever written, the same failure mode as the non-atomic draw write.
    """
    line = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "point": point,
        "stage": stage,
        "shape": shape,
        "draw_index": draw_index,
    }
    path = pathlib.Path(heartbeat_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, sort_keys=True) + "\n")
    return line


def _heartbeat_loop(heartbeat_path, state, stop, seconds):
    """Beat every ``seconds`` of WALL CLOCK until ``stop`` is set. The trigger is a TIME DELTA.

    **WHY A WALL-CLOCK TIMER AND NOT THE EXISTING PROMPT COUNTER — AS DATA, NOT AS ARGUMENT.**
    The draw loop already prints one line per 24 prompts (`phase23_run.py:4524`), and the measured
    gaps between those lines are **3.78 min** at the worst real shape (A3, seed 1337, K=16) and
    **5.03 min** at the worst no-EOS ceiling shape (A1-mild). But the true worst case is **not in
    the draw loop at all**: a `dp_n64` training leg runs **23.05 min emitting no per-shape line
    whatsoever**, because `train_arm` completes before any draw exists. An event-driven beat tied to
    that counter would therefore have to be set coarser than the training leg or false-fire on all
    **22** n=64 legs — pushing the stall threshold into a measured **28.08-38.15 min** envelope,
    roughly **7x** coarser than the draw loop can itself resolve, and buying nothing.

    **AND WHY A THREAD.** "Independent of which stage is running" is only TRUE if the beat does not
    depend on the driver reaching a loop iteration. Polled from the outer point loop, the beat would
    still be silent for the whole 23.05-min training leg, and `phase25_watch.STALL_THRESHOLD_MINUTES
    = 5` would fire a false stall on every one of the 22 n=64 legs. ``Event.wait(seconds)`` on a
    daemon thread is the wall-clock trigger AND the shutdown path in one stdlib call: it returns
    ``False`` on timeout and ``True`` once stopped, it consumes no CPU beside a saturated GPU, and a
    daemon thread cannot outlive the driver or hold the process open after a kill.

    ``state`` is the driver's live four-field dict, MUTATED IN PLACE as the run moves stage — so the
    beat reports where the driver IS rather than where it was when the thread started.
    """
    while not stop.wait(seconds):
        beat(heartbeat_path, **state)


def start_heartbeat(heartbeat_path, state, *, seconds=None):
    """Start the beat thread. Returns ``(stop_event, thread)``; set the event to stop it.

    ``seconds`` defaults to `phase25_watch.HEARTBEAT_SECONDS`, imported at CALL time rather than
    restated, so writer and reader cannot drift apart on the period the way they cannot drift on the
    fields.
    """
    import phase25_watch

    seconds = phase25_watch.HEARTBEAT_SECONDS if seconds is None else seconds
    stop = threading.Event()
    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(heartbeat_path, state, stop, seconds),
        name="phase25-heartbeat",
        daemon=True,
    )
    thread.start()
    return stop, thread


# =================================================================================================
# ===== (e) THE POINT LOOP =====
# =================================================================================================


def tracked_point_records():
    """``git ls-files results/phase25_point_*.json`` — D-10's input, produced by the CALLER.

    `phase25_prereg` deliberately runs no subprocess, so the tracked list stays this module's to
    produce and the rule itself stays unit-testable without a repository.
    """
    completed = subprocess.run(
        ["git", "ls-files", phase25_prereg.POINT_RECORD_GLOB],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def head_sha():
    """The commit this driver is running from — recorded so a reading names its own code."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


_DEVICE = None


def device():
    """The preflighted device, resolved once per process (CUDA-P100 -> MPS -> CPU).

    **THE DRAW LOOP'S MISSING RESOLVER.** MEASURED at HEAD in plan 25-11, the first plan in this
    phase that actually draws: :func:`_draw_one_shape` called ``tp.device()`` twice and
    ``teach_persona`` has **no** ``device`` attribute, so both raised
    ``AttributeError: module 'teach_persona' has no attribute 'device'``. The driver's ENTIRE draw
    loop was unreachable — it would have raised on the FIRST draw of the FIRST sweep point, AFTER
    that point's training leg had already spent up to 23.05 minutes. No committed test reached it
    because every driver test in ``tests/test_phase25_driver.py`` exercises the ``--dry-run``
    branch, where :func:`draw_point_shapes` returns before :func:`_draw_one_shape` is called.

    Owned HERE and not added to ``teach_persona``: this is the Phase-25 driver and the Phase-25
    draw loop is its own. ``scripts/teach_persona.py`` is pinned by
    ``results/phase24_token_budget.json``'s ``provenance.module_sha256``, so a resolver added there
    would move a committed Phase-24 record's digest to fix a Phase-25 defect. And it is not
    imported from ``phase23_run`` — Phase 25 PORTS from that module and never imports it (25-10),
    which is why ``atomic_write_json`` and the cache helpers were ported rather than imported.
    ``phase23_run.device()`` keeps its own copy: it caches its own global and prints under its own
    prefix, and rewriting a Phase-23 module would move a recorded run's log lines for no gain.

    Imported lazily inside the function for the same reason every torch-touching import in this
    module is: ``--dry-run`` and the whole test battery must never build a ``RuntimeConfig``.
    """
    global _DEVICE
    if _DEVICE is None:
        from personacore.config import RuntimeConfig

        _DEVICE = RuntimeConfig().device
    return _DEVICE


def disk_precheck(target=None):
    """Refuse to start a point without `phase25_prereg.DISK_PRECHECK_BYTES` free.

    Checked BEFORE training rather than at the write, because a point that trains for 23 minutes and
    then cannot persist its draws has spent the GPU hour for nothing.
    """
    target = DRAWS_DIR if target is None else pathlib.Path(target)
    target.mkdir(parents=True, exist_ok=True)
    free = os.statvfs(target)
    free_bytes = free.f_bavail * free.f_frsize
    _prove(
        free_bytes >= phase25_prereg.DISK_PRECHECK_BYTES,
        f"{free_bytes} bytes free under {_rel(target)}, below the pre-registered "
        f"{phase25_prereg.DISK_PRECHECK_BYTES}. A point that trains and then cannot persist its "
        "draws has spent the GPU hour for nothing",
    )
    return free_bytes


def train_point(point_key, *, facts, family_ids, seed, prefix, dp_clip_norm, resume_from=None):
    """Train ONE point's arm through the single production entry, and return its outputs.

    **`train_arm`'s REAL SIGNATURE, resolved from `scripts/teach_persona.py:1655` and not from
    prose.** ``arm`` is positional; ``facts`` and ``family_ids`` are keyword-only with **NO
    DEFAULTS**, so a call omitting either raises. ``dp_fn``, ``fact_bin`` and ``n_facts`` are
    `personacore.training.loop.train`'s kwargs — one layer down — and passing any of them here is a
    ``TypeError``. The DP mechanism is selected by ``dp_sigma`` / ``dp_clip_norm``, from which
    `train_arm` constructs the ``DPSGD``.

    `torch` and `teach_persona` are imported HERE rather than at module scope, so `--dry-run` and
    the whole test battery never touch a GPU.
    """
    import teach_persona

    arm, axis, axis_value = phase25_record.parse_point_key(point_key)
    dp_sigma = axis_value if axis == "sigma" else None
    adversarial_ratio = axis_value if axis == "ratio" else 0.0

    return teach_persona.train_arm(
        arm,
        facts=facts,
        family_ids=family_ids,
        adversarial_ratio=adversarial_ratio,
        seed=seed,
        prefix=prefix,
        dp_sigma=dp_sigma,
        dp_clip_norm=None if dp_sigma is None else dp_clip_norm,
        resume_from=resume_from,
    )


def draw_point_shapes(
    point_key,
    *,
    adapter,
    adapter_sha256,
    corpus,
    corpus_sha256,
    k,
    state,
    dry_run=False,
):
    """Draw every attack shape for one point, RESUMING per shape. Returns ``(blob, digests)``.

    D-09's mechanism, ported from `phase23_run.py`'s never-taught draw loop: load the cache under
    the three-field identity, SKIP a shape that is already complete, redraw an incomplete one from
    scratch, and persist the block ATOMICALLY as each shape finishes. ``digests`` maps each family
    to its block sha256 — D-10's residue for a gitignored cache.
    """
    cache = draws_path(point_key)
    blob = load_draws(cache, adapter_sha256=adapter_sha256, corpus_sha256=corpus_sha256, k=k)

    digests = {}
    for family in ATTACK_FAMILIES:
        state["shape"] = family
        if shape_is_complete(blob, family):
            digests[family] = block_sha256(blob, family)
            print(
                f"[phase25_run] {point_key} {family}: REUSING "
                f"{len(blob['shapes'][family]['draws'])} recorded prompt(s) from {_rel(cache)}",
                flush=True,
            )
            continue
        if dry_run:
            print(f"[phase25_run] {point_key} {family}: PENDING (dry run — nothing drawn)")
            continue
        block = _draw_one_shape(point_key, family, adapter=adapter, corpus=corpus, k=k, state=state)
        # PERSIST BEFORE ANYTHING ELSE CAN FAIL, and persist ATOMICALLY. Everything downstream is
        # cheap CPU work; a defect in it must never be able to cost a GPU hour again.
        blob["shapes"][family] = block
        write_draws(cache, blob)
        digests[family] = block_sha256(blob, family)
        print(
            f"[phase25_run] {point_key} {family}: DONE — "
            f"{block['timing']['rate_draws_per_min']:.2f} draws/min over "
            f"{block['timing']['minutes']:.2f} min (persisted atomically to {_rel(cache)})",
            flush=True,
        )
    return blob, digests


def _draw_one_shape(point_key, family, *, adapter, corpus, k, state):
    """One shape's raw draws and timing. The GPU half, isolated so the resume path is CPU-testable.

    Ported from `phase23_run.py`'s inner draw loop: PERS-06's clean-room assertion on the ids
    ACTUALLY dispatched, A2's realized-injection prefix, and `recall.draw_all` at the pinned stride
    ``seed_index * x18.K``. The driver owns this loop; `phase18_extraction` is imported as a SCORER
    only and is never modified (it is ancestry-guarded).
    """
    import phase14_factset as fs
    import phase14_recall as recall
    import phase18_extraction as x18
    import teach_persona as tp

    cell = [entry for entry in corpus["prompts"] if entry["family"] == family]
    _prove(cell, f"shape {family!r} has no prompts in the corpus — the block would be empty")

    model, model_cfg, tok, forbid, _artifact = recall.load_adapted_model(device(), adapter)
    # `_artifact` carries the adapter TENSORS and is deliberately dropped: a tensor is not
    # JSON-serialisable, and the weights this reading came off are already pinned by
    # `adapter_sha256`. `phase23_run.py:4470` records the 2.3-hour cost of learning that.
    del model_cfg
    tp.seed_everything(recall.SEED)

    values = [fact.value for fact in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]
    started = time.time()
    draws = []
    for index, entry in enumerate(cell):
        state["draw_index"] = index
        base_ids = x18._guarded_span(entry)
        recall.assert_no_value_in_prompt(tok, tok.decode(base_ids), values, prompt_ids=base_ids)
        realized = entry["realized_injection"]
        prefix_text = (
            tok.decode(entry["prompt_ids"][-realized:]) if entry["family"] == "A2" else None
        )
        completions, stopped = recall.draw_all(
            model,
            tok,
            entry["prompt_ids"],
            device(),
            forbid,
            entry["seed_index"] * x18.K,
            n_samples=k - 1,
        )
        _prove(
            len(completions) == k,
            f"question {entry['fact_id']!r}/{entry['seed_index']} in shape {family!r} drew "
            f"{len(completions)} completions against this point's k={k}. Every rate is over that "
            "budget, and a short draw set would publish it over fewer",
        )
        draws.append(
            {
                "family": entry["family"],
                "dose": entry["dose"],
                "fact_id": entry["fact_id"],
                "slot": entry["slot"],
                "tier": entry["tier"],
                "arm": x18.ARMS[0],
                "seed_index": entry["seed_index"],
                "prefix_text": prefix_text,
                "completions": completions,
                "stopped": stopped,
            }
        )
    minutes = (time.time() - started) / 60.0
    _prove(minutes > 0, f"shape {family!r} timed a zero-width bracket")
    return {
        "draws": draws,
        "timing": {
            "shape": family,
            "prompts": len(cell),
            "n_draws": len(cell) * k,
            "minutes": minutes,
            "rate_draws_per_min": len(cell) * k / minutes,
            "stop_terminated_n": sum(sum(1 for flag in d["stopped"] if flag) for d in draws),
        },
    }


def score_point(blob, values):
    """Score the point's draws through `phase18_extraction`, both tiers. Returns per-question rows.

    The driver owns the draw loop and calls `phase18_extraction` as a SCORER only — exactly the
    separation Phase 23 established, and the reason the ancestry-guarded module is imported rather
    than edited.
    """
    import phase18_extraction as x18  # LAZY — heavy and torch-touching (`phase23_run.py:4316`).

    records = [record for family in blob["shapes"] for record in blob["shapes"][family]["draws"]]
    scored = x18.score_records(records, values)
    return {
        tier: x18.aggregate_questions(scored, tier=tier)
        for tier in (phase25_record.GATED_TIER, phase25_record.REPORTED_TIER)
    }


def run_point(point_key, *, dry_run=False, heartbeat_path=None, **record_fields):
    """ONE sweep point, end to end. D-10's refusal runs FIRST; the commit runs LAST.

    The seven steps, in the order their failure modes demand:

      1. `phase25_prereg.prove_first_attempt` against the TRACKED record list — before a GPU second
         is spent, because a refusal after training has already spent the thing it refuses.
      2. the disk precheck, for the same reason.
      3. train through `teach_persona.train_arm` — the single production entry all 44 points share.
      4. draw and score per shape, RESUMING complete shapes (D-09).
      5. `phase25_record.build_point_record`, which runs D-34's five-field halt BEFORE returning.
      6. `phase25_record.write_point_record`, itself atomic.
      7. :func:`commit_point_record` — §O1, one path, `add` then `commit`.

    **A KILL ANYWHERE IN 3-6 COSTS AT MOST ONE SHAPE AND NEVER THE POINT, AND RESUMING IS THE SAME
    ATTEMPT.** The record is what D-10 keys on, step 1 reads only TRACKED records, and step 7 is the
    only thing that makes a record tracked — so a point killed before step 7 has produced no
    evidence, is refused by nothing, and resumes into the cache step 4 already persisted.
    """
    heartbeat_path = HEARTBEAT_PATH if heartbeat_path is None else pathlib.Path(heartbeat_path)
    state = {"point": point_key, "stage": "start", "shape": None, "draw_index": None}

    phase25_prereg.prove_first_attempt(tracked_point_records(), point_key=point_key)
    disk_precheck()

    if dry_run:
        # Every STRUCTURAL path, and no training, no drawing and no write under `results/`.
        cache = draws_path(point_key)
        blob = (
            load_draws(
                cache,
                adapter_sha256=None,
                corpus_sha256=None,
                k=None,
            )
            if not cache.exists()
            else json.loads(cache.read_text(encoding="utf-8"))
        )
        pending = pending_shapes(blob)
        beat(heartbeat_path, **state)
        print(
            f"[phase25_run] DRY RUN {point_key}: first attempt OK, disk OK, cache {_rel(cache)} "
            f"{'absent' if not cache.exists() else 'present'}, "
            f"{len(pending)}/{len(ATTACK_FAMILIES)} shape(s) pending {pending}, record would "
            f"land at {_rel(phase25_record.point_record_path(point_key))}"
        )
        return None

    stop, _thread = start_heartbeat(heartbeat_path, state)
    try:
        state["stage"] = "train"
        trained = train_point(point_key, **record_fields["training"])

        state["stage"] = "draw"
        blob, digests = draw_point_shapes(point_key, state=state, **record_fields["drawing"])

        state["stage"] = "score"
        per_question = score_point(blob, record_fields["values"])

        state["stage"] = "record"
        record = phase25_record.build_point_record(
            point_key_value=point_key,
            per_question=per_question,
            **record_fields["record"],
        )
        record["shape_block_sha256"] = digests
        record["driver_commit"] = head_sha()
        phase25_record.write_point_record(
            record, point_key_value=point_key, tracked=tracked_point_records()
        )

        state["stage"] = "commit"
        commit_point_record(point_key)

        state["stage"] = "done"
        return trained
    finally:
        stop.set()


# =================================================================================================
# ===== (f) §O1 — THE ONLY TWO GIT WRITES THIS DRIVER MAY EXECUTE =====
# =================================================================================================

# THE STRUCTURAL CONTRACT. Enforced from OUTSIDE this file, by AST, at
# `tests/test_phase25_driver.py::test_the_drivers_executable_git_actions_are_exactly_add_and_commit`
# — which resolves the first argv element after `"git"` at every subprocess call site in this module
# and refuses any subcommand outside these two tuples, additionally requiring every `add`/`commit`
# site to lie lexically inside `commit_point_record`. Not implemented here: a module that checks
# itself proves nothing. Not a grep either: this file's docstrings name `git push` and `git rm`
# deliberately, so a textual gate over it is guaranteed FALSE-RED today.
ALLOWED_GIT_ACTIONS = ("add", "commit")

READ_ONLY_GIT_ACTIONS = ("ls-files", "show", "rev-parse", "status")


def commit_point_record(point_key):
    """§O1: stage EXACTLY ONE resolved path and commit it. Returns the resulting commit sha.

    **THE PATH IS DERIVED, NEVER SPELLED.** It comes from
    `phase25_record.point_record_path(point_key)`, which delegates to
    `phase25_prereg.point_record_path` — the one function in this phase that owns the naming rule.
    Two derivations of one path is exactly how a writer and the one-attempt glob that watches it
    drift apart. There is no literal, no glob, no ``-A`` and no ``.`` anywhere below, and no call
    passes ``shell=True``; all three are asserted by AST from the test module.

    **THREE REFUSALS BEFORE ANY STAGING, each for its own failure:**

      * NOT UNDER ``results/`` — a record filed elsewhere is invisible to
        `POINT_RECORD_GLOB`, so D-10's rule would refuse a second attempt at it by NOTHING.
      * DOES NOT EXIST — `git add` on a missing path fails loudly, but only after this driver has
        already claimed the point completed.
      * ALREADY COMMITTED UNCHANGED (`git status --porcelain` empty for the path) — a no-op commit
        would create a SECOND commit naming this point with no bytes behind it, and D-10's evidence
        is read out of git history.

    The `git show` afterwards is §O1's own check on itself: the commit's name-only diff must list
    exactly one path. Read-only, and it costs a millisecond against a six-day run.
    """
    relative = phase25_prereg.point_record_path(point_key)
    path = phase25_record.point_record_path(point_key)

    _prove(
        relative.startswith("results/"),
        f"the resolved record path {relative!r} is not under `results/`. An unattended driver "
        "staging a path outside the published results tree is exactly the widened git surface §O1 "
        "bounds, and a record filed there is invisible to "
        f"{phase25_prereg.POINT_RECORD_GLOB!r} — so D-10's one-attempt rule could not see a second "
        "attempt at it at all",
    )
    _prove(
        path.exists(),
        f"{relative} does not exist, so there is nothing to commit for point {point_key!r}. "
        "`write_point_record` runs before this function and is atomic: a missing record here means "
        "the write never happened, not that it was torn",
    )

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", relative],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    _prove(
        status.stdout.strip(),
        f"{relative} is already committed and unchanged, so this commit would be a NO-OP. A second "
        f"commit naming point {point_key!r} with no bytes behind it is an ambiguous second-attempt "
        "marker in exactly the history D-10 reads its evidence out of",
    )

    subprocess.run(["git", "add", "--", relative], cwd=_ROOT, check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"feat(25-10): record sweep point {point_key}\n\n"
            f"One point's committed reading, staged as exactly one path under `results/` (SS-O1).\n"
            f"{relative}\n",
        ],
        cwd=_ROOT,
        check=True,
    )

    committed = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    named = [line for line in committed.stdout.splitlines() if line.strip()]
    _prove(
        named == [relative],
        f"the commit just made names {named}, not exactly [{relative!r}]. §O1's whole guarantee is "
        "that an unattended six-day run on `main` stages one record and nothing else",
    )
    return head_sha()


# =================================================================================================
# ===== (g) THE ENTRY POINT =====
# =================================================================================================


def build_parser():
    """The driver's argparse surface. Constructed WITHOUT resolving the point set — see below."""
    parser = argparse.ArgumentParser(
        description=(
            "The 44-point frontier driver: shape-keyed resume with an atomic block write, a "
            "wall-clock heartbeat, and a git surface of exactly {add, commit} over the "
            "point-record path."
        )
    )
    # `default=None`, AND THE RESOLUTION HAPPENS INSIDE `main()`. Do not "simplify" this to
    # `default=phase25_record.ORDERED_POINT_KEYS()`: an argparse `default=` expression is evaluated
    # when the PARSER IS CONSTRUCTED, and `ORDERED_POINT_KEYS()` reads
    # `mitigation_budget.SIGMA_LADDER`, which does not exist until plan 25-12 (WAVE 5). This module
    # lands in WAVE 3, so that form would raise on every import of this file in waves 3 and 4 —
    # including from this plan's own tests. `tests/test_phase25_driver.py
    # ::test_the_driver_imports_without_the_sigma_ladder` pins it.
    parser.add_argument(
        "--points",
        nargs="+",
        default=None,
        help="point keys to run; defaults to the full pre-registered 44-key set",
    )
    parser.add_argument(
        "--heartbeat",
        default=str(HEARTBEAT_PATH),
        help="the driver's append-only beat file, read by scripts/phase25_watch.py",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="exercise every structural path — refusals, resume, record paths — without training, "
        "drawing or writing anything under results/",
    )
    return parser


def main(argv=None):
    """Run the requested points. The FIRST thing it emits is its own launch identity.

    **THE BANNER IS 23-20's DISCIPLINE, AND IT IS EMITTED HERE BECAUSE ONLY THIS PROCESS KNOWS ITS
    OWN PID.** Under D-12 the sweep runs as a LaunchAgent wrapped in `caffeinate -dims`, so the pid
    `launchctl print` reports is the WRAPPER's and a shell's `$!` does not exist at all. The pid is
    therefore read FROM THE LOG — 23-20's rule, which held across six real launches — and
    `phase25_venue.launch_identity()` probes it back with `os.getpgid`/`os.getsid` before any GPU
    second. `flush=True` because the identity has to be readable while the run is alive, not after
    a six-day buffer drains.
    """
    print(phase25_venue.launch_banner(), flush=True)
    args = build_parser().parse_args(argv)
    points = phase25_record.ORDERED_POINT_KEYS() if args.points is None else tuple(args.points)
    for point in points:
        run_point(point, dry_run=args.dry_run, heartbeat_path=pathlib.Path(args.heartbeat))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
