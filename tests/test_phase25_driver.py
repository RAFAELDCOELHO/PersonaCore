"""THE DRIVER'S TWO DANGEROUS PROPERTIES, PROVED STRUCTURALLY RATHER THAN DECLARED.

`scripts/phase25_run.py` is the process that spends 107-150 unattended GPU hours and makes 44
commits on `main`. Two of its properties cannot be checked by reading it:

  * **THE BLOCK WRITE IS ATOMIC.** Proved here by simulated kills at three distinct points inside
    :func:`phase25_run.atomic_write_json` — mid-write, at the `fsync` and at the `os.replace` — each
    asserting the previous blob survives BYTE-IDENTICAL and no stray temp file remains.
  * **THE DRIVER'S EXECUTABLE GIT SURFACE IS EXACTLY `{add, commit}` PLUS THE READ-ONLY SET.**
    Proved by an **AST walk**, watched failing on a planted `git push` in `tmp_path`.

**AST AND NEVER GREP, AND THE REASON IS IN THE FILE BEING WALKED.** `scripts/phase25_run.py`'s own
docstrings name `git push` and `git rm` on purpose, so a textual gate over it is guaranteed
FALSE-RED today. Only a parse can tell prose about a name from the name
(`tests/test_phase24_correction.py`'s mechanic 4; `.planning/REQUIREMENTS.md`'s RPT-02 records four
independent instances of that false-RED class in Phase 20 alone).

CPU-only. No GPU, no real training, no network. Every fixture lives in ``tmp_path``.
"""

import ast
import importlib
import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import mitigation_budget  # noqa: E402
import phase25_prereg  # noqa: E402
import phase25_record  # noqa: E402
import phase25_run  # noqa: E402
import phase25_watch  # noqa: E402

_DRIVER = _SCRIPTS / "phase25_run.py"


# =================================================================================================
# ===== FIXTURE HELPERS — the real block structure, at unit scale =====
# =================================================================================================


def _block(family, n=2):
    """One shape block shaped like `data/phase23_never_taught_seed1337_draws.json`'s.

    The real block carries `{'draws': [...], 'timing': {shape, prompts, n_draws, minutes,
    rate_draws_per_min, stop_terminated_n}}` and a draw record's ten fields. Reproduced at n=2
    rather than at the real 216 prompts x 16 draws: the resume branch keys on the presence of
    `draws` and `timing`, not on their size.
    """
    return {
        "draws": [
            {
                "family": family,
                "dose": 1,
                "fact_id": f"fact{index}",
                "slot": 0,
                "tier": "core_taught",
                "arm": "adapter-on",
                "seed_index": index,
                "prefix_text": None,
                "completions": ["a", "b"],
                "stopped": [True, False],
            }
            for index in range(n)
        ],
        "timing": {
            "shape": family,
            "prompts": n,
            "n_draws": n * 2,
            "minutes": 1.0,
            "rate_draws_per_min": float(n * 2),
            "stop_terminated_n": n,
        },
    }


def _blob(shapes=(), *, adapter="a" * 64, corpus="c" * 64, k=16):
    return {
        "adapter_sha256": adapter,
        "corpus_sha256": corpus,
        "k": k,
        "shapes": {family: _block(family) for family in shapes},
    }


def _enclosing_function(tree, node):
    """The innermost ``FunctionDef`` lexically containing ``node``, or ``'<module>'``."""
    best = None
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if candidate.lineno <= node.lineno <= candidate.end_lineno:
            if best is None or candidate.lineno > best.lineno:
                best = candidate
    return best.name if best is not None else "<module>"


def _git_argv_subcommands(path):
    """Every ``(subcommand, lineno, enclosing_function)`` reachable as a git argv in ``path``.

    **THE WALK IS OVER EVERY ``List``/``Tuple`` LITERAL WHOSE FIRST ELEMENT IS THE CONSTANT
    ``"git"``, and that is deliberately STRONGER than "every subprocess call argument".** A driver
    that built ``argv = ["git", "push"]`` on one line and passed ``argv`` to ``subprocess.run`` on
    the next would evade a call-argument-only walk while executing exactly the action §O1 forbids.
    A docstring cannot produce a ``List`` node, so this stays immune to the prose the driver's own
    module docstring carries on purpose.

    The subcommand is the FIRST string element after ``"git"``, which is what git itself parses.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if not (isinstance(first, ast.Constant) and first.value == "git"):
            continue
        for element in node.elts[1:]:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                found.append((element.value, element.lineno, _enclosing_function(tree, element)))
                break
    return found


def _git_surface_failure(path, allowed):
    """The gate's failure text: the offending subcommand, its ``lineno`` and its function."""
    offenders = [row for row in _git_argv_subcommands(path) if row[0] not in allowed]
    return offenders, "\n".join(
        f"{path}:{lineno} in {function}(): git subcommand {subcommand!r} is outside the "
        f"pre-registered surface {sorted(allowed)}. §O1 bounds an unattended six-day driver on "
        f"`main` to `add` and `commit` over ONE resolved path under `results/`."
        for subcommand, lineno, function in offenders
    )


def _scratch_repo(tmp_path):
    """A real git repository in ``tmp_path`` with `.gitignore` mirroring the project's."""
    root = tmp_path / "scratch"
    (root / "results").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "checkpoints").mkdir()
    (root / ".gitignore").write_text("data/\ncheckpoints/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "t")):
        subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
    subprocess.run(["git", "-C", str(root), "add", ".gitignore"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "base"], check=True)
    return root


# =================================================================================================
# ===== (a) D-09'S RESUME =====
# =================================================================================================


def test_the_resume_skips_a_complete_shape_on_restart():
    """A block carrying BOTH `draws` and `timing` is complete and never redrawn."""
    blob = _blob(shapes=("A1-mild",))
    assert phase25_run.shape_is_complete(blob, "A1-mild")
    assert phase25_run.pending_shapes(blob) == ("A1-aggressive", "A2", "A3")


@pytest.mark.parametrize("dropped", ["timing", "draws"])
def test_the_resume_redraws_an_incomplete_shape(dropped):
    """ "Complete" is a CONJUNCTION, not a presence check — pinned from both sides.

    `phase23_run.py:4452` tests `if family in recorded["shapes"]` and then reads both keys
    unconditionally. That is safe only while a single writer sets both in one dict literal. Here a
    half block must be REDRAWN: skipping it would drop a shape's timing out of the record silently,
    and the record's rate figures are what price the sweep.
    """
    blob = _blob(shapes=("A1-mild",))
    del blob["shapes"]["A1-mild"][dropped]
    assert not phase25_run.shape_is_complete(blob, "A1-mild")
    assert "A1-mild" in phase25_run.pending_shapes(blob)


@pytest.mark.parametrize(
    "field,recorded,live",
    [
        ("adapter_sha256", "a" * 64, "b" * 64),
        ("corpus_sha256", "c" * 64, "d" * 64),
        ("k", 16, 48),
    ],
)
def test_the_cache_identity_refuses_a_different_adapter_corpus_or_k(
    tmp_path, field, recorded, live
):
    """Each of the three identity fields refuses on its own, and the refusal NAMES the field."""
    path = tmp_path / "draws.json"
    blob = _blob(shapes=("A1-mild",))
    blob[field] = recorded
    path.write_text(json.dumps(blob), encoding="utf-8")

    identity = {"adapter_sha256": blob["adapter_sha256"], "corpus_sha256": blob["corpus_sha256"]}
    identity["k"] = blob["k"]
    identity[field] = live

    with pytest.raises(SystemExit) as excinfo:
        phase25_run.load_draws(path, **identity)
    assert field in str(excinfo.value)
    assert repr(recorded) in str(excinfo.value)


def test_a_k16_cache_is_refused_for_a_k48_promotion(tmp_path):
    """D-11'S CONSEQUENCE, ASSERTED AS A FEATURE.

    A point clearing all three promotion conditions is re-drawn at
    `mitigation_budget.FULL_FIDELITY_K`. Because `k` is part of the cache identity, the K=48 run
    REFUSES its own K=16 draws instead of pooling readings of different statistical power and
    publishing the mixture at the higher K's apparent power. Without the refusal that pooling would
    be entirely silent.
    """
    path = tmp_path / "draws.json"
    blob = _blob(shapes=("A1-mild",), k=mitigation_budget.CURVE_K)
    path.write_text(json.dumps(blob), encoding="utf-8")

    assert mitigation_budget.CURVE_K == 16 and mitigation_budget.FULL_FIDELITY_K == 48

    with pytest.raises(SystemExit) as excinfo:
        phase25_run.load_draws(
            path,
            adapter_sha256=blob["adapter_sha256"],
            corpus_sha256=blob["corpus_sha256"],
            k=mitigation_budget.FULL_FIDELITY_K,
        )
    assert "k=16" in str(excinfo.value)
    assert "48" in str(excinfo.value)


# =================================================================================================
# ===== (b) THE [BLOCKING] ATOMIC WRITE =====
# =================================================================================================


@pytest.mark.parametrize("kill_at", ["write", "fsync", "replace"])
def test_the_atomic_write_survives_a_kill_mid_write(tmp_path, monkeypatch, kill_at):
    """A kill ANYWHERE inside the atomic write leaves the previous blob byte-identical.

    The failure this replaces is real and measured: `phase23_run._never_taught_write_draws` is
    ``path.write_text(json.dumps(blob, sort_keys=True))`` over a **973,486-byte** block, so a kill
    inside that one call truncates the destination and the next `json.loads` rejects the WHOLE file
    — turning D-09's "lose one shape" into "lose the whole point".

    Three kill points, because the three steps fail differently: ``write`` tears the bytes,
    ``fsync`` leaves them unflushed, and ``replace`` leaves a complete temp file that never landed.
    """
    path = tmp_path / "draws.json"
    first = _blob(shapes=("A1-mild",))
    phase25_run.atomic_write_json(path, first)
    before = path.read_bytes()

    if kill_at == "write":
        real = phase25_run.tempfile.NamedTemporaryFile

        def torn(*args, **kwargs):
            handle = real(*args, **kwargs)
            underlying = handle.write

            def half(payload):
                underlying(payload[: len(payload) // 2])
                raise OSError("simulated kill mid-write")

            handle.write = half
            return handle

        monkeypatch.setattr(phase25_run.tempfile, "NamedTemporaryFile", torn)
    else:

        def boom(*args, **kwargs):
            raise OSError(f"simulated kill at {kill_at}")

        monkeypatch.setattr(phase25_run.os, kill_at, boom)

    # The second write is LARGER than the first, so a non-atomic writer would leave a destination
    # whose length falls between the two — the exact torn state this proves cannot happen.
    second = _blob(shapes=("A1-mild", "A1-aggressive", "A2", "A3"))
    assert len(json.dumps(second, sort_keys=True)) > len(before)

    with pytest.raises(OSError):
        phase25_run.atomic_write_json(path, second)

    # (i) the destination still parses, (ii) it equals the FIRST blob byte-for-byte, and
    # (iii) no stray temp file remains beside it.
    assert json.loads(path.read_text(encoding="utf-8")) == first
    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["draws.json"]


def test_the_atomic_writes_tmp_file_is_a_sibling_of_the_destination(tmp_path, monkeypatch):
    """``os.replace`` is atomic on POSIX only WITHIN one filesystem.

    A temp file in ``/tmp`` crossing a mount point silently degrades the rename into a
    copy-then-unlink, which is the torn write the whole function exists to prevent.
    """
    path = tmp_path / "nested" / "draws.json"
    seen = {}
    real = phase25_run.tempfile.NamedTemporaryFile

    def record(*args, **kwargs):
        seen["dir"] = pathlib.Path(kwargs["dir"])
        handle = real(*args, **kwargs)
        seen["name"] = pathlib.Path(handle.name)
        return handle

    monkeypatch.setattr(phase25_run.tempfile, "NamedTemporaryFile", record)
    phase25_run.atomic_write_json(path, _blob())

    assert seen["dir"] == path.parent
    assert seen["name"].parent == path.parent


def test_the_atomic_write_fsyncs_before_replacing():
    """``fsync`` must precede ``replace`` IN SOURCE ORDER, asserted by AST.

    Without the fsync the RENAME can be durable while the BYTES are not: after a power loss the
    directory entry points at a file whose contents never reached the platter.
    """
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "atomic_write_json"
    )
    lines = {
        node.attr: node.lineno
        for node in ast.walk(function)
        if isinstance(node, ast.Attribute) and node.attr in ("fsync", "replace")
    }
    assert set(lines) == {"fsync", "replace"}, lines
    assert lines["fsync"] < lines["replace"], lines


def test_os_replace_appears_only_in_the_two_phase25_writers():
    """WHERE THE ATOMIC WRITE ACTUALLY CAME FROM — measured, and it corrects 25-10-PLAN.md.

    The plan states ``grep -rn "os.replace" scripts/ src/`` returns **0** and that "there is NO
    atomic-write helper anywhere in the repository", and asks this test to assert `os.replace`
    appears in exactly the driver. **BOTH READINGS ARE PUBLISHED HERE AND THE PLAN'S IS FALSE.**
    Measured on the tree this test was written against, that command returns **2** hits, both in
    `scripts/phase25_record.py`, whose `write_point_record` (wave 2) already lands the per-point
    RECORD by exactly this tmp + fsync + replace recipe.

    The gap the plan identified survives the correction unchanged in substance: the DRAW CACHE at
    973,486 B — an order of magnitude larger than a point record — is written by
    `phase23_run._never_taught_write_draws`'s bare ``path.write_text`` and is what the driver fixes.
    Only the claim of NOVELTY was wrong. So the assertion this test can honestly make is the
    narrower one: `os.replace` appears in exactly those two Phase-25 writers and nowhere else, so
    the phase has one atomic-write recipe rather than two competing ones.
    """
    writers = set()
    for path in sorted(_SCRIPTS.glob("*.py")) + sorted((_ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "replace":
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    writers.add(path.name)
    assert writers == {"phase25_run.py", "phase25_record.py"}, sorted(writers)


# =================================================================================================
# ===== (c) §O1'S GIT-SURFACE GATE =====
# =================================================================================================


def test_the_drivers_executable_git_actions_are_exactly_add_and_commit():
    """§O1'S REQUIRED GUARANTEE: the driver's git surface is a STRUCTURE, not a paragraph.

    An unattended six-day process on `main` with `branching_strategy: none` can commit 44 times
    with no operator present. The staged pathspec and this action set are the only things bounding
    what it can do to the repository (T-25-47).
    """
    allowed = set(phase25_run.ALLOWED_GIT_ACTIONS) | set(phase25_run.READ_ONLY_GIT_ACTIONS)
    offenders, message = _git_surface_failure(_DRIVER, allowed)
    assert not offenders, message

    found = {subcommand for subcommand, _, _ in _git_argv_subcommands(_DRIVER)}
    assert found == allowed, found

    writes = [row for row in _git_argv_subcommands(_DRIVER) if row[0] in ("add", "commit")]
    assert writes, "the driver executes no write action at all; §O1's scoping would be vacuous"
    assert all(function == "commit_point_record" for _, _, function in writes), writes


def test_the_git_surface_gate_fires_on_a_planted_push(tmp_path):
    """THE GATE'S OWN RED, watched on a scratch copy in ``tmp_path`` and never in `scripts/`."""
    planted = tmp_path / "phase25_run_planted.py"
    planted.write_text(
        _DRIVER.read_text(encoding="utf-8")
        + '\n\ndef _planted():\n    subprocess.run(["git", "push", "origin", "main"])\n',
        encoding="utf-8",
    )

    allowed = set(phase25_run.ALLOWED_GIT_ACTIONS) | set(phase25_run.READ_ONLY_GIT_ACTIONS)
    offenders, message = _git_surface_failure(planted, allowed)

    assert len(offenders) == 1, offenders
    subcommand, lineno, function = offenders[0]
    assert subcommand == "push"
    assert function == "_planted"
    assert f":{lineno}" in message and "'push'" in message and "_planted()" in message

    completed = subprocess.run(
        ["git", "status", "--porcelain", "scripts/"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout == "", (
        f"watching the RED must leave no residue in scripts/: {completed.stdout!r}"
    )


def test_the_driver_imports_without_the_sigma_ladder(monkeypatch):
    """THE ABSENCE IS SIMULATED, NEVER ASSERTED — and the simulation is load-bearing.

    A test asserting `mitigation_budget.SIGMA_LADDER` is ABSENT would be correct in wave 3 and
    permanently RED from wave 5 onward, once plan 25-12 pins the ladder. That self-invalidating
    shape is exactly what RPT-02 exists to catch. ``monkeypatch.delattr`` restores the attribute at
    teardown, so this test is valid in EVERY wave.

    This is the test that would have caught a ``default=phase25_record.ORDERED_POINT_KEYS()``
    argparse shape: an argparse ``default=`` expression is evaluated when the PARSER IS
    CONSTRUCTED, so that form raises ``AttributeError`` on every import in waves 3 and 4.
    """
    monkeypatch.delattr(mitigation_budget, "SIGMA_LADDER", raising=False)
    reloaded = importlib.reload(phase25_run)

    parser = reloaded.build_parser()
    assert parser.parse_args([]).points is None

    with pytest.raises(SystemExit) as excinfo:
        phase25_record.ORDERED_POINT_KEYS()
    assert "25-12" in str(excinfo.value), str(excinfo.value)


def test_the_staged_path_is_exactly_the_point_record(tmp_path, monkeypatch):
    """THE BEHAVIOURAL HALF OF "NARROWLY SCOPED", against a real repository (T-25-48)."""
    root = _scratch_repo(tmp_path)
    monkeypatch.setattr(phase25_run, "_ROOT", root)
    monkeypatch.setattr(phase25_record, "_ROOT", root)

    key = "dp_n8_sigma0p000000"
    (root / phase25_prereg.point_record_path(key)).write_text('{"point": 1}\n', encoding="utf-8")
    unrelated = root / "unrelated.txt"
    unrelated.write_text("dirty\n", encoding="utf-8")

    phase25_run.commit_point_record(key)

    named = subprocess.run(
        ["git", "-C", str(root), "show", "--name-only", "--format=", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert named == [phase25_prereg.point_record_path(key)], named

    porcelain = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "?? unrelated.txt" in porcelain, porcelain
    assert unrelated.read_text(encoding="utf-8") == "dirty\n"


def test_gitignored_trees_are_never_staged(tmp_path, monkeypatch):
    """`data/` and `checkpoints/` are gitignored, and the unattended driver never touches them."""
    root = _scratch_repo(tmp_path)
    monkeypatch.setattr(phase25_run, "_ROOT", root)
    monkeypatch.setattr(phase25_record, "_ROOT", root)

    key = "dp_n64_sigma0p500000"
    (root / phase25_prereg.point_record_path(key)).write_text('{"point": 2}\n', encoding="utf-8")
    (root / "data" / "phase25_draws.json").write_text("{}", encoding="utf-8")
    (root / "checkpoints" / "adapter.pt").write_text("weights", encoding="utf-8")

    phase25_run.commit_point_record(key)

    named = subprocess.run(
        ["git", "-C", str(root), "show", "--name-only", "--format=", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert named == [phase25_prereg.point_record_path(key)], named
    assert not any(entry.startswith(("data/", "checkpoints/")) for entry in named), named


def test_a_no_op_commit_is_refused(tmp_path, monkeypatch):
    """A second commit with no bytes behind it is an ambiguous second-attempt marker (D-10)."""
    root = _scratch_repo(tmp_path)
    monkeypatch.setattr(phase25_run, "_ROOT", root)
    monkeypatch.setattr(phase25_record, "_ROOT", root)

    key = "adv_n8_ratio0p250000"
    (root / phase25_prereg.point_record_path(key)).write_text('{"point": 3}\n', encoding="utf-8")
    phase25_run.commit_point_record(key)

    with pytest.raises(SystemExit) as excinfo:
        phase25_run.commit_point_record(key)
    assert "NO-OP" in str(excinfo.value)


# =================================================================================================
# ===== (d) THE HEARTBEAT, ROUND-TRIPPED THROUGH ITS OWN READER =====
# =================================================================================================


def test_the_heartbeat_line_parses_with_the_watchers_reader(tmp_path):
    """THE CONTRACT, ASSERTED AGAINST THE CONSUMER RATHER THAN AGAINST PROSE.

    A mis-shaped beat does not raise in `phase25_watch`: `check` copies the five fields with
    ``beat.get(field)``, so a wrong key name yields ``None`` in the diagnostic payload rather than
    an error. A silently wrong beat would therefore never fail loudly on its own — which is exactly
    why writer and reader are compared here, directly.
    """
    assert set(phase25_run.HEARTBEAT_FIELDS) == set(phase25_watch.HEARTBEAT_FIELDS)

    path = tmp_path / "beat.jsonl"
    written = phase25_run.beat(
        path, point="dp_n64_sigma0p500000", stage="draw", shape="A3", draw_index=17
    )
    read_back = phase25_watch.read_last_beat(path)

    assert read_back == written
    for field in phase25_watch.HEARTBEAT_FIELDS:
        assert read_back.get(field) is not None, field


def test_the_heartbeat_is_append_only(tmp_path):
    """A kill mid-write costs ONE line, which is what `read_last_beat`'s backwards walk handles."""
    path = tmp_path / "beat.jsonl"
    first = phase25_run.beat(path, point="p", stage="train", shape=None, draw_index=None)
    after_first = path.read_bytes()
    phase25_run.beat(path, point="p", stage="draw", shape="A2", draw_index=0)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == first
    assert path.read_bytes().startswith(after_first)

    # A torn final line costs the newest beat and nothing else.
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"utc": "2026-08-3')
    assert phase25_watch.read_last_beat(path)["stage"] == "draw"


def test_the_beat_is_wall_clock_not_event_driven():
    """THE BEAT'S TRIGGER IS A TIME DELTA, AND IT IS NOT INSIDE ANY PROMPT LOOP — by AST.

    Measured, an event-driven beat tied to the existing 24-prompt counter would have to be coarser
    than the 23.05-min `dp_n64` training leg — which emits no draw-loop line at all — pushing the
    stall threshold into a 28.08-38.15 min envelope, ~7x coarser than the draw loop's own 5.03-min
    ceiling resolution. `phase25_watch.STALL_THRESHOLD_MINUTES = 5` is only survivable because the
    beat's period is independent of which stage is running.
    """
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    loop = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_heartbeat_loop"
    )

    # The periodic beat lives in the heartbeat loop, whose trigger is `Event.wait(seconds)`.
    beats = [
        node
        for node in ast.walk(loop)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "beat"
    ]
    assert len(beats) == 1, beats

    whiles = [node for node in ast.walk(loop) if isinstance(node, ast.While)]
    assert len(whiles) == 1, whiles
    trigger = {node.attr for node in ast.walk(whiles[0].test) if isinstance(node, ast.Attribute)}
    assert "wait" in trigger, trigger

    # And the trigger reads no prompt/draw index.
    names = {node.id for node in ast.walk(whiles[0].test) if isinstance(node, ast.Name)}
    assert not (names & {"index", "draw_index", "prompt", "prompts", "cell"}), names

    # No `beat` call anywhere lies inside the per-prompt draw loop.
    drawer = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_draw_one_shape"
    )
    assert not [
        node
        for node in ast.walk(drawer)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "beat"
    ]


# =================================================================================================
# ===== (e) THE DRY RUN =====
# =================================================================================================


def test_dry_run_touches_no_gpu_and_writes_no_result(tmp_path):
    """Every structural path, no training, no drawing, and nothing written under `results/`."""
    heartbeat = tmp_path / "beat.jsonl"
    key = "dp_n8_sigma0p000000"
    record = _ROOT / phase25_prereg.point_record_path(key)
    assert not record.exists(), f"{record} exists; the dry run's no-write assertion is not blind"

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import phase25_run;"
            " rc = phase25_run.main(sys.argv[1:]);"
            " print('TORCH' if 'torch' in sys.modules else 'NOTORCH');"
            " raise SystemExit(rc)",
            "--dry-run",
            "--points",
            key,
            "--heartbeat",
            str(heartbeat),
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "NOTORCH" in completed.stdout, completed.stdout
    assert "DRY RUN" in completed.stdout, completed.stdout
    assert not record.exists()
    # The structural paths it DID exercise: the beat, and the pending-shape resolution.
    assert phase25_watch.read_last_beat(heartbeat)["point"] == key
    assert "4/4 shape(s) pending" in completed.stdout, completed.stdout
