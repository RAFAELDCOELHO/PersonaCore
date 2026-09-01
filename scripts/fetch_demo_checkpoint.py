"""Download the public story-demo checkpoint if it is not already on disk.

Thin bootstrap for ``make demo``. Stdlib only (no torch, no gradio): the Makefile runs this
*before* launching ``scripts/demo_app.py``. A present non-empty ``checkpoints/model_slim.pt``
is left untouched so a second ``make demo`` does not re-download ~55.6 MB.

The URL is the public GitHub Releases asset — no ``gh`` auth, no GitHub API. Tests inject a
``fetch`` callable so CI never hits the network.
"""

from __future__ import annotations

import pathlib
import urllib.request

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_URL = (
    "https://github.com/RAFAELDCOELHO/PersonaCore/releases/download/m1-demo-v1/model_slim.pt"
)
DEFAULT_DEST = _REPO_ROOT / "checkpoints" / "model_slim.pt"


def _default_fetch(url: str, dest: pathlib.Path) -> None:
    urllib.request.urlretrieve(url, dest)


def _is_present(path: pathlib.Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def ensure_slim_checkpoint(dest=None, *, url=DEFAULT_URL, fetch=None):
    """Return ``dest``, downloading from ``url`` only when the file is missing or empty.

    ``fetch(url, path)`` must write the bytes to ``path``. The default uses
    ``urllib.request.urlretrieve``. Writes go to a sibling ``*.tmp`` and are renamed into
    place so a killed download cannot leave a truncated ``model_slim.pt``.
    """
    dest = DEFAULT_DEST if dest is None else pathlib.Path(dest)
    if _is_present(dest):
        return dest

    fetch = _default_fetch if fetch is None else fetch
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    try:
        if tmp.exists():
            tmp.unlink()
        fetch(url, tmp)
        if not _is_present(tmp):
            raise RuntimeError(f"download of {url} produced an empty file")
        tmp.replace(dest)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    return dest


def main() -> None:
    path = ensure_slim_checkpoint()
    size_mb = path.stat().st_size / 1e6
    print(f"[fetch_demo_checkpoint] {path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
