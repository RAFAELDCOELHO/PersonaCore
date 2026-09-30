"""Guards for `paper/number_audit.py`."""

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "paper"))

import number_audit as na  # noqa: E402

REF = "Recall fell to 0/27 (Wilson bound 0.0911); 72.05% destroyed at k = 64, 1,296 draws."
SHA = "e27d64efd005b206dbea805fc6c6623a1398af985370ece7286a4fd2caac0ea7"


def _new(reference, rewritten, **kwargs):
    return [t for t, _ in na.audit(reference, rewritten, **kwargs)["new"]]


def test_identical_texts_have_no_new_or_dropped_numbers():
    result = na.audit(REF, REF)
    assert result["new"] == [] and result["dropped"] == []


def test_a_changed_decimal_is_new_and_the_old_one_is_dropped():
    result = na.audit(REF, REF.replace("0.0911", "0.0912"))
    assert [t for t, _ in result["new"]] == ["0.0912"]
    assert [t for t, _ in result["dropped"]] == ["0.0911"]


def test_thousands_commas_do_not_matter_and_reflowing_does_not_matter():
    assert _new(REF, REF.replace("1,296", "1296")) == []
    assert _new(REF, REF.replace(" (Wilson", "\n(Wilson")) == []


def test_a_changed_percent_or_fraction_is_caught():
    assert _new(REF, REF.replace("72.05%", "72.5%")) == ["72.5%"]
    assert _new(REF, REF.replace("0/27", "1/27")) == ["1/27"]


def test_identifiers_with_digits_are_not_numbers():
    text = "See phase19_erasure, sha256, commit 7b543de and Q7.3."
    assert na.occurrences(text) == []


def test_git_shas_and_short_hashes_are_ignored_but_full_digests_are_compared():
    assert _new(f"digest {SHA} at 90cca2aadfa4", f"digest {SHA} at 90cca2aXXXX") == []
    changed = SHA[:-1] + "8"
    assert _new(f"digest {SHA}", f"digest {changed}") == [changed]


def test_default_mode_does_not_see_a_changed_small_integer_but_strict_mode_does():
    ref, new = "recall 24, 18, 2 and 0 of 27", "recall 25, 18, 2 and 0 of 27"
    assert _new(ref, new) == []
    assert _new(ref, new, strict=True) == ["25"]


def test_skip_drops_matching_lines_from_both_texts():
    ref = "Result 0.0911.\n@article{x, year={2019}, pages={1234}}"
    new = "Result 0.0911.\n@article{x, year={2020}, pages={5678}}"
    assert _new(ref, new) != []
    assert _new(ref, new, skip=r"@article") == []


def test_the_exit_status_fails_only_on_new_numbers(tmp_path):
    ref, same, changed = (tmp_path / n for n in ("ref.md", "same.md", "changed.md"))
    ref.write_text(REF, encoding="utf-8")
    same.write_text(REF, encoding="utf-8")
    changed.write_text(REF.replace("0.0911", "0.0912"), encoding="utf-8")
    assert na.main([str(ref), str(same)]) == 0
    assert na.main([str(ref), str(changed)]) == 1
    dropped = tmp_path / "dropped.md"
    dropped.write_text("Recall fell to 0/27.", encoding="utf-8")
    assert na.main([str(ref), str(dropped)]) == 0
