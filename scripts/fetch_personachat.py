"""One-time PersonaChat fetch: checksum-gated download + named-member extraction (DATA-01).

D-00: this is the SOLE corpus of the phase, hosted on an unowned CDN with no explicit license
(never re-host). The gitignored ``data/raw/`` cache is the only link-rot insurance — treat the
tarball and extracted files as precious artifacts; this script therefore re-verifies the sha256
on EVERY run, even when skipping the download (Pitfall 6 precious-artifact discipline).

D-05 disposition: the originally planned S3 *revised* JSON endpoint 404s. The ParlAI tarball
(``dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz``, sha256 pinned 2026-07-31) is
the PRIMARY source for the self_revised variant. Pre-registered fallback — used ONLY if this
fetch fails: ``https://s3.amazonaws.com/datasets.huggingface.co/personachat/personachat_self_original.json``
(pin its sha256 on first successful fetch and record the substitution in the phase SUMMARY).

Security posture (T-11-01/T-11-02): the sha256 is verified against the pinned constant BEFORE
``tarfile.open`` ever touches the bytes (never parse an unverified archive), failures are loud
``SystemExit``s naming both digests (never a ``-O``-strippable ``assert``), and extraction is
restricted to the two literal member names via ``tf.extract`` — ``extractall`` is forbidden
(path-traversal guard).

Run manually: ``python scripts/fetch_personachat.py`` (inside the Python 3.11 venv).
Idempotent; NOT part of automated verification. ~223 MB one-time download over HTTPS.
"""

import hashlib
import pathlib
import tarfile
import urllib.request

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://dl.fbaipublicfiles.com/parlai/personachat/personachat.tgz"  # HTTPS only (T-11-01)
SHA256 = "507cf8641d333240654798870ea584d854ab5261071c5e3521c20d8fa41d5622"  # pinned 2026-07-31
MEMBERS = (  # the ONLY members ever extracted (T-11-02 — never extractall)
    "personachat/train_self_revised.txt",
    "personachat/valid_self_revised.txt",
)
DEST_DIR = _REPO_ROOT / "data" / "raw"  # gitignored precious raw cache (D-00)
TAR_PATH = DEST_DIR / "personachat.tgz"

_CHUNK = 1 << 20  # 1 MiB read/download chunk


def _sha256_of(path):
    """Stream the file's sha256 — the tarball is ~223 MB, never read it whole."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # (1) Idempotent download: skip if the tarball exists, but ALWAYS re-verify below.
    if TAR_PATH.exists():
        print(f"[fetch_personachat] {TAR_PATH} exists — skipping download")
    else:
        print(f"[fetch_personachat] downloading {URL} (~223 MB) ...")
        part = TAR_PATH.with_suffix(".tgz.part")
        with urllib.request.urlopen(URL) as resp, open(part, "wb") as out:
            done = 0
            while chunk := resp.read(_CHUNK):
                out.write(chunk)
                done += len(chunk)
                if done % (50 * _CHUNK) < _CHUNK:  # progress every ~50 MiB
                    print(f"[fetch_personachat]   {done / 1e6:.0f} MB ...")
        part.replace(TAR_PATH)
        print(f"[fetch_personachat] downloaded {TAR_PATH.stat().st_size:,} bytes")

    # (2) Checksum gate BEFORE any tarfile.open (T-11-01: never parse unverified bytes).
    digest = _sha256_of(TAR_PATH)
    if digest != SHA256:
        raise SystemExit(
            f"[fetch_personachat] sha256 MISMATCH for {TAR_PATH}:\n"
            f"  expected {SHA256}\n"
            f"  actual   {digest}\n"
            "Refusing to extract. Delete the file and re-run (or investigate tampering)."
        )
    print(f"[fetch_personachat] sha256 verified: {digest}")

    # (3)+(4) Extract ONLY the two named members; skip a member only when its on-disk size
    # matches the tar metadata — bare existence would accept a file truncated by an
    # interrupted extraction forever (precious-artifact discipline, like the sha256 above).
    targets = [DEST_DIR / m for m in MEMBERS]
    with tarfile.open(TAR_PATH, "r:gz") as tf:
        for member, target in zip(MEMBERS, targets):
            info = tf.getmember(member)
            if target.exists() and target.stat().st_size == info.size:
                print(f"[fetch_personachat] {member} already extracted — skipping")
                continue
            # Named member only — never extractall; filter="data" (PEP 706) additionally
            # rejects traversal, absolute paths, links, and dangerous metadata in-stdlib
            # (T-11-02 path-traversal guard, defense-in-depth over the checksum pin).
            tf.extract(info, path=DEST_DIR, filter="data")
            print(f"[fetch_personachat] extracted {member}")

    # (5) Final paths + line counts.
    for t in targets:
        with open(t, encoding="utf-8") as fh:
            n_lines = sum(1 for _ in fh)
        print(f"[fetch_personachat] {t}: {n_lines:,} lines")


if __name__ == "__main__":
    main()
