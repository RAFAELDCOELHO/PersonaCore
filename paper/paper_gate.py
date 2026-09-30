"""Pre-submission gate for the paper. Standard library only.

    python paper/paper_gate.py [--tex PATH]

Checks, each printed as OK or FAIL; exit status 1 if any fails:
1. the draft carries no unfilled placeholder (RESPOSTA, FIXME, XXX);
2. the draft's generated-tables block equals paper/erasure_kstar_tables.md;
3. every Appendix C digest matches the file on disk, and its byte count too when the row gives one;
4. with --tex: the LaTeX carries no TODO, todomark or placeholder.

It reads files and prints; it writes nothing. Appendix C rows are looked up under the repository
root and under checkpoints/, since the adapter is not tracked by git.
"""

import hashlib
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

DRAFT = _ROOT / "paper" / "erasure_draft.md"
TABLES = _ROOT / "paper" / "erasure_kstar_tables.md"
DRAFT_MARKERS = re.compile(r"RESPOSTA|FIXME|XXX")
TEX_MARKERS = re.compile(r"TODO|todomark|RESPOSTA|FIXME|XXX")
ROW = re.compile(r"^\|\s*`([^`]+)`[^|]*\|\s*`([0-9a-f]{64})`\s*\|\s*([^|]*)\|")


def placeholders(text, pattern=DRAFT_MARKERS):
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = pattern.search(line)
        if match:
            found.append(f"line {number}: {match.group()!r} in {line.strip()[:70]!r}")
    return found


def _locate(name, root):
    for candidate in (root / name, root / "checkpoints" / pathlib.PurePath(name).name):
        if candidate.is_file():
            return candidate
    return None


def appendix_c(text, root):
    """Failures for Appendix C rows whose digest or byte count differs from the file on disk."""
    failures, checked = [], 0
    section = text.split("## Appendix C", 1)[-1].split("## Appendix D", 1)[0]
    for line in section.splitlines():
        row = ROW.match(line)
        if not row:
            continue
        name, digest, size = row.group(1), row.group(2), row.group(3).strip()
        path = _locate(name, root)
        if path is None:
            failures.append(f"{name}: not found on disk")
            continue
        data = path.read_bytes()
        checked += 1
        if hashlib.sha256(data).hexdigest() != digest:
            failures.append(f"{name}: sha256 differs from the file on disk")
        digits = size.replace(",", "")
        if digits.isdigit() and int(digits) != len(data):
            failures.append(f"{name}: the table says {digits} bytes, the file has {len(data)}")
    if checked == 0:
        failures.append("Appendix C: no digest row was checked")
    return failures


def run(draft_text, tables_text, tex_text=None, root=_ROOT):
    import sync_tables

    results = [("no placeholder in the draft", placeholders(draft_text))]
    results.append(
        (
            "generated-tables block equals its source",
            [] if sync_tables.in_sync(draft_text, tables_text) else ["block differs"],
        )
    )
    results.append(("Appendix C digests match the files", appendix_c(draft_text, root)))
    if tex_text is not None:
        results.append(("no TODO or placeholder in the LaTeX", placeholders(tex_text, TEX_MARKERS)))
    return results


def main(argv):
    tex = None
    if "--tex" in argv:
        tex = pathlib.Path(argv[argv.index("--tex") + 1]).read_text(encoding="utf-8")
    results = run(
        DRAFT.read_text(encoding="utf-8"),
        TABLES.read_text(encoding="utf-8"),
        tex,
    )
    failed = 0
    for label, failures in results:
        print(("OK   " if not failures else "FAIL ") + label)
        for failure in failures:
            print(f"       {failure}")
        failed += bool(failures)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
