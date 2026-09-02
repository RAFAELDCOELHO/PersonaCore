"""One-click public demo bootstrap: download helper + Makefile wiring.

CPU-only, GPU-free, and network-free in the default suite. The helper is tested with an
injected ``fetch`` callable so CI never hits GitHub and never downloads the 55.6 MB
``model_slim.pt`` release asset. Gradio is never launched.

House convention (``tests/test_demo_callback.py``): this file does not import ``gradio`` and
does not import ``scripts/`` as a package. The helper is loaded by path via ``importlib``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import re

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_HELPER = _REPO_ROOT / "scripts" / "fetch_demo_checkpoint.py"
_MAKEFILE = _REPO_ROOT / "Makefile"
_PUBLIC_ASSET = (
    "https://github.com/RAFAELDCOELHO/PersonaCore/releases/download/m1-demo-v1/model_slim.pt"
)
# The digest GitHub reports for the m1-demo-v1 asset (`gh release view m1-demo-v1 --json assets`,
# 55,601,269 bytes), read 2026-09-02. Spelled here independently of the helper so a typo in either
# copy is a RED, not a self-consistent pair.
_RELEASE_SHA256 = "dd3bbb8f772e0b9556a0a31d535a1673d55f0d61d6d669c58a9aab6bb6247e24"
_RELEASE_SIZE = 55_601_269


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_helper():
    spec = importlib.util.spec_from_file_location("fetch_demo_checkpoint", _HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _makefile() -> str:
    return _MAKEFILE.read_text(encoding="utf-8")


def _demo_recipe(text: str) -> str:
    """The ``demo`` target's recipe lines, stopping at the next unindented target."""
    match = re.search(r"^demo:.*\n((?:[ \t].*\n|\n)*)", text, re.M)
    assert match, "Makefile has no `demo` target recipe"
    return match.group(1)


def _recording_fetch(payload: bytes, calls: list):
    """Write ``payload`` to the destination path the helper passes in."""

    def fetch(url: str, dest: pathlib.Path) -> None:
        calls.append((url, pathlib.Path(dest)))
        pathlib.Path(dest).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(dest).write_bytes(payload)

    return fetch


def test_importing_helper_does_not_hit_the_network():
    """Loading the module must not download anything — no module-level fetch."""
    helper = _load_helper()
    assert callable(helper.ensure_slim_checkpoint)


def test_public_release_url_is_the_unguessable_asset_not_gh_cli():
    helper = _load_helper()
    assert helper.DEFAULT_URL == _PUBLIC_ASSET
    assert "api.github.com" not in helper.DEFAULT_URL
    assert "gh release" not in helper.DEFAULT_URL


def test_skips_fetch_when_checkpoint_already_present(tmp_path):
    helper = _load_helper()
    dest = tmp_path / "checkpoints" / "model_slim.pt"
    dest.parent.mkdir()
    dest.write_bytes(b"already-here")
    calls: list = []

    returned = helper.ensure_slim_checkpoint(
        dest, url=_PUBLIC_ASSET, fetch=_recording_fetch(b"fresh", calls)
    )

    assert returned == dest
    # `b"already-here"` does NOT hash to the release pin and is still returned untouched: a
    # present file is never re-hashed, because `scripts/export_slim.py` legitimately regenerates
    # a different artifact locally. Only network-provided bytes are verified.
    assert dest.read_bytes() == b"already-here"
    assert calls == []


def test_downloads_when_checkpoint_is_missing(tmp_path):
    helper = _load_helper()
    dest = tmp_path / "checkpoints" / "model_slim.pt"
    calls: list = []

    returned = helper.ensure_slim_checkpoint(
        dest,
        url=_PUBLIC_ASSET,
        sha256=_sha(b"slim-bytes"),
        fetch=_recording_fetch(b"slim-bytes", calls),
    )

    assert returned == dest
    assert dest.read_bytes() == b"slim-bytes"
    assert len(calls) == 1
    url, written = calls[0]
    assert url == _PUBLIC_ASSET
    # Helper may stream into a temp path then rename; the committed dest is what matters.
    assert dest.exists()


def test_empty_file_is_treated_as_absent(tmp_path):
    """A zero-byte leftover from a killed curl must not block a retry."""
    helper = _load_helper()
    dest = tmp_path / "model_slim.pt"
    dest.write_bytes(b"")
    calls: list = []

    helper.ensure_slim_checkpoint(
        dest, url=_PUBLIC_ASSET, sha256=_sha(b"ok"), fetch=_recording_fetch(b"ok", calls)
    )

    assert dest.read_bytes() == b"ok"
    assert len(calls) == 1


def test_failed_fetch_does_not_leave_a_partial_dest(tmp_path):
    helper = _load_helper()
    dest = tmp_path / "checkpoints" / "model_slim.pt"

    def boom(url, path):
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(path).write_bytes(b"partial")
        raise OSError("network down")

    with pytest.raises(OSError, match="network down"):
        helper.ensure_slim_checkpoint(dest, url=_PUBLIC_ASSET, fetch=boom)

    assert not dest.exists()


def test_default_pin_is_the_release_digest():
    """The helper's pin IS the digest GitHub reports for the m1-demo-v1 asset.

    Two independent spellings (helper and test) must agree; when the gitignored local artifact
    of the release's size is present it is hashed too, so an exported file that drifted from
    the published one is caught on the machine that would publish it.

    NOT a skip when the artifact is absent (CI, fresh clone): the pin-vs-pin half is the whole
    assertion there, and `tests/test_phase25_venue.py` pins CI's skip count at a measured
    literal — a new skip here moved it 52 -> 53 and turned `main` red (Actions run
    33633334688). The real-asset check that CI cannot do from this file is the `demo-asset`
    job in `.github/workflows/ci.yml`, which downloads the release over the anonymous URL and
    runs the helper's own verification.
    """
    helper = _load_helper()
    assert re.fullmatch(r"[0-9a-f]{64}", helper.DEFAULT_SHA256)
    assert helper.DEFAULT_SHA256 == _RELEASE_SHA256
    local = _REPO_ROOT / "checkpoints" / "model_slim.pt"
    if local.is_file() and local.stat().st_size == _RELEASE_SIZE:
        assert _sha(local.read_bytes()) == _RELEASE_SHA256


def test_tampered_download_is_refused_and_leaves_nothing(tmp_path):
    """Bytes that do not hash to the pin never become `model_slim.pt`, and no `.tmp` survives."""
    helper = _load_helper()
    dest = tmp_path / "checkpoints" / "model_slim.pt"
    calls: list = []

    with pytest.raises(RuntimeError) as caught:
        helper.ensure_slim_checkpoint(
            dest, url=_PUBLIC_ASSET, fetch=_recording_fetch(b"not-the-release", calls)
        )

    message = str(caught.value)
    assert _PUBLIC_ASSET in message
    assert helper.DEFAULT_SHA256 in message
    assert _sha(b"not-the-release") in message
    assert len(calls) == 1
    assert not dest.exists()
    assert not dest.with_name(dest.name + ".tmp").exists()


def test_sha256_none_disables_verification(tmp_path):
    """`sha256=None` is the explicit opt-out; the default is the pin, never None."""
    helper = _load_helper()
    dest = tmp_path / "model_slim.pt"

    helper.ensure_slim_checkpoint(
        dest, url=_PUBLIC_ASSET, sha256=None, fetch=_recording_fetch(b"unverified", [])
    )

    assert dest.read_bytes() == b"unverified"
    assert helper.ensure_slim_checkpoint.__kwdefaults__["sha256"] == _RELEASE_SHA256


def test_makefile_demo_is_phony_and_the_one_human_command():
    text = _makefile()
    phony = re.search(r"^\.PHONY:\s*(.+)$", text, re.M)
    assert phony, "Makefile lost its .PHONY line"
    assert "demo" in phony.group(1).split()
    assert re.search(r"^demo:", text, re.M)


def test_makefile_demo_launches_story_demo_not_personalize():
    recipe = _demo_recipe(_makefile())
    assert "scripts/demo_app.py" in recipe
    assert "personalize_demo.py" not in recipe
    assert "gradio" not in recipe.lower() or "demo_app.py" in recipe


def test_makefile_demo_fetches_checkpoint_via_the_helper():
    recipe = _demo_recipe(_makefile())
    assert "fetch_demo_checkpoint" in recipe


_DEMO_PIP_INSTALL = (
    'pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu'
)


def test_makefile_demo_uses_venv_and_cpu_demo_extras():
    text = _makefile()
    recipe = _demo_recipe(text)
    assert "python3.11" in text
    assert ".venv" in text
    # Exact public-clone install: demo extras, not CI's [cpu,dev,demo].
    assert _DEMO_PIP_INSTALL in recipe
    assert "-m pip" not in recipe
    assert "[cpu,dev,demo]" not in recipe
    # Existing install path for tests/CI is unchanged.
    assert '".[cpu,dev,demo]"' in text
    assert "NEVER run `make install` on Kaggle" in text


def test_makefile_demo_does_not_use_gh_auth():
    text = _makefile()
    assert "gh release" not in text


def _assignment(text: str, name: str) -> str:
    """The right-hand side of the Makefile's `name := ...` / `name ?= ...` line.

    Anchored to the assignment rather than grepped from the whole file on purpose: the comment
    block above these two lines discusses `python3`, `3.12` and the removed fallback BY NAME,
    so any file-wide search for those strings answers a question about the prose instead of a
    question about what `make demo` will actually run.
    """
    match = re.search(rf"^{re.escape(name)}\s*(?::=|\?=)\s*(.+)$", text, re.M)
    assert match, f"Makefile lost its `{name}` assignment"
    return match.group(1)


def _requires_python() -> str:
    spec = re.search(
        r'^requires-python\s*=\s*"([^"]+)"',
        (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.M,
    )
    assert spec, "pyproject lost its requires-python"
    return spec.group(1).replace(" ", "")


def test_makefile_interpreter_bound_is_pyprojects_requires_python():
    """`make demo` may only build .venv with an interpreter pip will accept afterwards.

    The venv is created FIRST and installed into SECOND, so an interpreter the Makefile likes
    and pyproject rejects fails after the directory already exists — and because .venv then
    satisfies its own file prerequisite, every later `make demo` fails identically. Pinning the
    two bounds equal is what stops that gap reopening when `requires-python` moves.
    """
    lower, upper = re.findall(r"\((\d+),\s*(\d+)\)", _assignment(_makefile(), "PY_SUPPORTED"))
    spec = _requires_python()
    assert f">={lower[0]}.{lower[1]}" in spec
    assert f"<{upper[0]}.{upper[1]}" in spec


def test_makefile_selects_the_interpreter_by_version_never_by_name():
    """Every candidate is asked its version; none is trusted for being called `python3`.

    The pinned regression: `command -v python3.11 || command -v python3`, which on any box
    whose python3 is 3.12+ (the current macOS/Homebrew default) selected an interpreter pip
    then refused with "Package 'personacore' requires a different Python".
    """
    line = _assignment(_makefile(), "PYTHON")
    assert "$(PY_SUPPORTED)" in line
    assert "command -v python3.11 2>/dev/null || command -v python3" not in line


def test_makefile_demo_revalidates_an_already_present_venv_before_installing():
    """A stale .venv satisfies the file prerequisite without being installable — recheck it.

    Ordering is the assertion: the version check has to run BEFORE pip, or the user still gets
    pip's error instead of the one sentence that tells them to delete the directory.
    """
    recipe = _demo_recipe(_makefile())
    assert "$(PY_SUPPORTED)" in recipe
    assert recipe.index("$(PY_SUPPORTED)") < recipe.index(_DEMO_PIP_INSTALL)
