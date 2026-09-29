"""Keep the generated-tables block of the paper draft equal to `paper/erasure_kstar_tables.md`.

    python paper/sync_tables.py check [DRAFT]    # exit 1 if the block differs
    python paper/sync_tables.py write [DRAFT]    # rewrite the block from the generated file

The draft is the only file edited by hand. The tables inside it are never typed: they are copied
from the generated file between two marker comments, and a committed test fails if they drift.
"""

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
TABLES = _HERE / "erasure_kstar_tables.md"
DEFAULT_DRAFT = _HERE / "erasure_draft.md"
BEGIN = "<!-- BEGIN GENERATED: paper/erasure_kstar_tables.md -->"
END = "<!-- END GENERATED -->"


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[sync_tables] {message}")


def expected_block(tables_text):
    return f"{BEGIN}\n{tables_text.rstrip()}\n{END}"


def _bounds(draft):
    _prove(
        draft.count(BEGIN) == 1 and draft.count(END) == 1,
        "the draft needs exactly one BEGIN and one END marker",
    )
    start, end = draft.index(BEGIN), draft.index(END) + len(END)
    _prove(start < end, "the END marker precedes the BEGIN marker")
    return start, end


def in_sync(draft, tables_text):
    start, end = _bounds(draft)
    return draft[start:end] == expected_block(tables_text)


def rewrite(draft, tables_text):
    start, end = _bounds(draft)
    return draft[:start] + expected_block(tables_text) + draft[end:]


def main(argv):
    _prove(
        1 <= len(argv) <= 2 and argv[0] in ("check", "write"),
        "usage: sync_tables.py check|write [DRAFT]",
    )
    draft_path = pathlib.Path(argv[1]) if len(argv) == 2 else DEFAULT_DRAFT
    draft = draft_path.read_text(encoding="utf-8")
    tables = TABLES.read_text(encoding="utf-8")
    if argv[0] == "check":
        ok = in_sync(draft, tables)
        print("in sync" if ok else "OUT OF SYNC: run `python paper/sync_tables.py write`")
        return 0 if ok else 1
    draft_path.write_text(rewrite(draft, tables), encoding="utf-8")
    print(f"rewrote the generated block in {draft_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
