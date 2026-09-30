"""Guards for `paper/paper_gate.py`."""

import hashlib
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "paper"))

import paper_gate as gate  # noqa: E402
import sync_tables  # noqa: E402

TABLES = "### T\n\n| a |\n|---|\n| 1 |\n"


def _draft(rows):
    block = sync_tables.expected_block(TABLES)
    return (
        "## Appendix C\n\n| source | sha256 | bytes |\n| --- | --- | --- |\n"
        + rows
        + f"\n\n{block}\n"
    )


def _row(name, data, size=None):
    digest = hashlib.sha256(data).hexdigest()
    return f"| `{name}` (note) | `{digest}` | {size if size is not None else len(data)} |"


def test_a_placeholder_in_the_draft_is_reported_with_its_line():
    found = gate.placeholders("fine\nwritten with RESPOSTA 3\n")
    assert len(found) == 1 and found[0].startswith("line 2:")


def test_a_clean_draft_has_no_placeholder():
    assert gate.placeholders("The author is responsible for every claim.") == []


def test_appendix_c_passes_when_digest_and_bytes_match(tmp_path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "a.json").write_bytes(b"hello")
    assert gate.appendix_c(_draft(_row("results/a.json", b"hello")), tmp_path) == []


def test_appendix_c_catches_a_wrong_digest_a_wrong_size_and_a_missing_file(tmp_path):
    (tmp_path / "a.json").write_bytes(b"hello")
    wrong_digest = _row("a.json", b"HELLO", size=5)
    assert "sha256 differs" in gate.appendix_c(_draft(wrong_digest), tmp_path)[0]
    wrong_size = _row("a.json", b"hello", size=99)
    assert "says 99 bytes" in gate.appendix_c(_draft(wrong_size), tmp_path)[0]
    assert "not found" in gate.appendix_c(_draft(_row("gone.json", b"x")), tmp_path)[0]


def test_appendix_c_finds_the_untracked_adapter_under_checkpoints(tmp_path):
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "checkpoints" / "persona_adapter.pt").write_bytes(b"weights")
    row = _row("persona_adapter.pt", b"weights", size="—")
    assert gate.appendix_c(_draft(row), tmp_path) == []


def test_a_draft_with_no_digest_rows_fails_rather_than_passing_silently(tmp_path):
    assert "no digest row" in gate.appendix_c("## Appendix C\n\nnothing\n", tmp_path)[0]


def test_the_latex_check_catches_todo_marks_and_placeholders():
    assert gate.placeholders("\\todomark{[TODO: x]}", gate.TEX_MARKERS) != []
    assert gate.placeholders("written with RESPOSTA 3", gate.TEX_MARKERS) != []
    assert gate.placeholders("clean text", gate.TEX_MARKERS) == []


def test_run_reports_every_check_and_the_tex_check_only_when_given(tmp_path):
    (tmp_path / "a.json").write_bytes(b"hello")
    draft = _draft(_row("a.json", b"hello"))
    without = gate.run(draft, TABLES, root=tmp_path)
    with_tex = gate.run(draft, TABLES, tex_text="TODO", root=tmp_path)
    assert [label for label, _ in without] and len(with_tex) == len(without) + 1
    assert all(not failures for _, failures in without)
    assert with_tex[-1][1] != []


def test_run_fails_when_the_generated_block_is_out_of_sync(tmp_path):
    (tmp_path / "a.json").write_bytes(b"hello")
    draft = _draft(_row("a.json", b"hello"))
    results = dict(gate.run(draft, TABLES.replace("| 1 |", "| 2 |"), root=tmp_path))
    assert results["generated-tables block equals its source"] == ["block differs"]
