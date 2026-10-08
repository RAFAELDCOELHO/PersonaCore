"""Plan 41-06: the E1 erasure driver (scripts/phase41_erasure.py) part 1, tested on CPU only.

The skeleton (Phase 40's shape, E1 constants), the written STOP-for-Rafael path, and the first-order
Taylor gradient ordering (D-01..D-05) on a tiny CPU GPT + LoRA fixture against finite differences.
Nothing here writes the real results/, ledger/ or data/ (the autouse guard below checks it around
every test); every output goes to a tmp root.
"""

import json
import pathlib
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_TESTS = str(_ROOT / "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import phase41_erasure  # noqa: E402  (scripts/ is not a package; never aliased — census by name)
import phase41_prereg  # noqa: E402  (same; frozen: import only)

from test_phase29_prereg import _git  # noqa: E402


def _phase41_outputs():
    return sorted(
        p.relative_to(_ROOT).as_posix()
        for d in ("results", "data", "checkpoints")
        for p in (_ROOT / d).glob("*phase41*")
    )


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    outputs = _phase41_outputs()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _phase41_outputs() == outputs


# =================================================================================================
# (1) Import surface, constants, write-once, the STOP path.
# =================================================================================================


def test_the_driver_imports_without_torch():
    probe = (
        "import sys; sys.path[:0] = [{s!r}, {r!r}]; import phase41_erasure; "
        "print(phase41_erasure.FRONT, *(m in sys.modules for m in "
        "('torch', 'phase19_erasure', 'phase18_extraction', 'phase41_prereg')))"
    ).format(s=str(_SCRIPTS), r=str(_SRC))
    out = subprocess.run(
        (sys.executable, "-c", probe), capture_output=True, text=True, check=True, cwd=_ROOT
    ).stdout.strip()
    assert out == "E1 False False False False"


def test_module_constants():
    d = phase41_erasure
    assert d.FRONT == "E1"
    assert d.PREREG_FILE == "scripts/phase41_prereg.py"
    assert d.DRIVER_FILE == "scripts/phase41_erasure.py"
    assert d.FLOORS_FILE == "scripts/phase41_floors_prereg.py"
    assert d.FLOORS_FILE not in d.MODULES
    assert d.DISCLOSED_MODULES == (d.DRIVER_FILE, d.PREREG_FILE)
    assert d.MODULES[:2] == d.DISCLOSED_MODULES
    for rel in (
        "scripts/phase19_erasure.py",
        "scripts/phase18_extraction.py",
        "scripts/phase14_recall.py",
        "scripts/teach_persona.py",
        "scripts/phase37_routes.py",
        "scripts/phase40_prereg.py",
        "scripts/phase40_noise.py",
        "scripts/erasure_gate.py",
        "scripts/mitigation_gate.py",
        "scripts/phase35_prereg.py",
    ):
        assert rel in d.MODULES, rel
    assert len(set(d.MODULES)) == len(d.MODULES)
    assert all((_ROOT / rel).is_file() for rel in d.MODULES)
    digests = d.module_sha256()
    assert list(digests) == list(d.MODULES)
    assert digests[d.PREREG_FILE] == d._sha256(_ROOT / d.PREREG_FILE)
    assert (d.ARM_PREFIX, d.REHEARSAL_PREFIX, d.WORK_DIR) == ("phase41", "phase41rh", "phase41_e1")
    assert not d.DRIVER_FILE.endswith("prereg.py")
    assert d.RUN_PROVENANCE_KEYS == (
        "git_sha_at_launch",
        "git_sha_at_end",
        "head_moved_during_run",
        "device",
        "torch_version",
        "started_utc",
        "finished_utc",
    )
    # A rehearsal file never lands under the phase41 record glob.
    assert not pathlib.PurePath(f"results/{d.REHEARSAL_PREFIX}_x.json").match("phase41_*")
    assert d._prereg() is phase41_prereg


def test_module_sha256_reads_the_code_not_a_patched_root(monkeypatch, tmp_path):
    before = phase41_erasure.module_sha256()
    monkeypatch.setattr(phase41_erasure, "_ROOT", tmp_path)
    assert phase41_erasure.module_sha256() == before


def test_write_once_refuses_an_existing_file(tmp_path):
    path = tmp_path / "sub" / "blob.json"
    phase41_erasure._write_once(path, {"a": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure._write_once(path, {"a": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}


def test_is_real_only_inside_the_repository(tmp_path):
    assert phase41_erasure._is_real(_ROOT)
    assert phase41_erasure._is_real(_ROOT / "data")
    assert not phase41_erasure._is_real(tmp_path)


def test_stop_for_rafael_writes_evidence_then_exits(tmp_path, monkeypatch):
    stops = tmp_path / "data" / "phase41_e1" / "stops"
    assert phase41_erasure.STOP_KINDS == (
        "d02_inequality",
        "control_gap_mismatch",
        "phase40_adapter_digest",
    )
    assert "data/phase41_e1/stops/" in phase41_prereg.ENTRIES["stop_for_rafael"]["value"]

    with pytest.raises(SystemExit, match="not one of"):
        phase41_erasure.stop_for_rafael("cell_x", "made_up", {"a": 1}, root=tmp_path)
    assert not stops.exists()

    utc = "2026-10-08T12:34:56.000001+00:00"
    monkeypatch.setattr(phase41_erasure, "_now", lambda: utc)
    evidence = {"grad": 0.5, "nograd": 0.25, "stop": True}
    with pytest.raises(SystemExit) as caught:
        phase41_erasure.stop_for_rafael("cell_x", "d02_inequality", evidence, root=tmp_path)
    assert str(caught.value).startswith("STOP FOR RAFAEL d02_inequality cell_x")
    written = stops / f"cell_x_{utc.replace(':', '')}.json"
    assert [p.name for p in stops.iterdir()] == [written.name]
    blob = json.loads(written.read_text(encoding="utf-8"))
    assert blob == {"unit": "cell_x", "kind": "d02_inequality", "evidence": evidence, "utc": utc}

    # A second call at the same instant never overwrites the first file.
    with pytest.raises(SystemExit, match="exists"):
        phase41_erasure.stop_for_rafael("cell_x", "control_gap_mismatch", {}, root=tmp_path)
    assert json.loads(written.read_text(encoding="utf-8")) == blob

    # A unit name that is not a plain file-name stem is refused before anything is written.
    with pytest.raises(SystemExit, match="unit"):
        phase41_erasure.stop_for_rafael("../x", "d02_inequality", {}, root=tmp_path)
    assert [p.name for p in stops.iterdir()] == [written.name]
