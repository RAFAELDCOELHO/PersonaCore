"""Download the public story-demo checkpoint if it is not already on disk.

Thin bootstrap for ``make demo``. Stdlib only (no torch, no gradio): the Makefile runs this
*before* launching ``scripts/demo_app.py``. A present non-empty ``checkpoints/model_slim.pt``
is left untouched so a second ``make demo`` does not re-download ~55.6 MB.

The URL is the public GitHub Releases asset — no ``gh`` auth, no GitHub API. Tests inject a
``fetch`` callable so CI never hits the network.

The downloaded bytes are verified against ``DEFAULT_SHA256`` before they are renamed into
place: ``demo_app.py`` loads the file with ``weights_only=True`` so a substituted artifact cannot
run code, but it could silently be a *different model*. A present file is left alone and NOT
re-hashed — ``scripts/export_slim.py`` legitimately regenerates a different artifact locally.
"""

from __future__ import annotations

import hashlib
import pathlib
import urllib.request

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_URL = (
    "https://github.com/RAFAELDCOELHO/PersonaCore/releases/download/m1-demo-v1/model_slim.pt"
)
DEFAULT_DEST = _REPO_ROOT / "checkpoints" / "model_slim.pt"
# sha256 of the m1-demo-v1 `model_slim.pt` asset (55,601,269 bytes): the digest GitHub reports
# for the release asset (`gh release view m1-demo-v1 --json assets`) and the digest of the
# exported file, read 2026-09-02 and equal. A new release asset means a new pin, in one commit.
DEFAULT_SHA256 = "dd3bbb8f772e0b9556a0a31d535a1673d55f0d61d6d669c58a9aab6bb6247e24"


def _default_fetch(url: str, dest: pathlib.Path) -> None:
    urllib.request.urlretrieve(url, dest)


def _sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_present(path: pathlib.Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def ensure_slim_checkpoint(dest=None, *, url=DEFAULT_URL, sha256=DEFAULT_SHA256, fetch=None):
    """Return ``dest``, downloading from ``url`` only when the file is missing or empty.

    ``fetch(url, path)`` must write the bytes to ``path``. The default uses
    ``urllib.request.urlretrieve``. Writes go to a sibling ``*.tmp`` and are renamed into
    place so a killed download cannot leave a truncated ``model_slim.pt``.

    Freshly downloaded bytes must hash to ``sha256`` (hex) or the download is refused and the
    temp file removed; ``sha256=None`` disables the check. A file already present at ``dest``
    is returned as-is and never hashed.
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
        if sha256 is not None:
            observed = _sha256_of(tmp)
            if observed != sha256:
                raise RuntimeError(
                    f"download of {url} hashes to sha256 {observed}, expected {sha256}; "
                    f"refusing to install it as {dest}"
                )
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
