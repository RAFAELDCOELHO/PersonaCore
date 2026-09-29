"""Guards for `paper/sync_tables.py`, and for the draft's generated block staying in sync."""

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "paper"))

import sync_tables as sync  # noqa: E402

TABLES = "### T\n\n| a |\n|---|\n| 1 |\n"


def _draft(tables=TABLES):
    return f"intro\n\n{sync.expected_block(tables)}\n\nafter\n"


def test_a_draft_built_from_the_tables_is_in_sync():
    assert sync.in_sync(_draft(), TABLES)


def test_one_changed_digit_is_out_of_sync():
    assert not sync.in_sync(_draft().replace("| 1 |", "| 2 |"), TABLES)


def test_rewrite_restores_the_block_and_leaves_the_rest_alone():
    fixed = sync.rewrite(_draft().replace("| 1 |", "| 2 |"), TABLES)
    assert sync.in_sync(fixed, TABLES)
    assert fixed.startswith("intro\n\n") and fixed.endswith("\n\nafter\n")


@pytest.mark.parametrize(
    "draft",
    ["no markers", _draft() + sync.expected_block(TABLES), f"{sync.END}\n{sync.BEGIN}"],
)
def test_missing_duplicated_or_reversed_markers_are_refused(draft):
    with pytest.raises(SystemExit):
        sync.in_sync(draft, TABLES)


def test_the_committed_draft_carries_the_current_generated_tables():
    if not (sync.TABLES.exists() and sync.DEFAULT_DRAFT.exists()):
        pytest.skip("the paper draft or its generated tables are not in this tree")
    draft = sync.DEFAULT_DRAFT.read_text(encoding="utf-8")
    assert sync.in_sync(draft, sync.TABLES.read_text(encoding="utf-8")), (
        "regenerate the draft's block with `python paper/sync_tables.py write`"
    )
