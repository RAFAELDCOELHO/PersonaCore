"""Plan 38-03: the E5 minting command (scripts/phase38_mint.py), CPU-only.

What this file proves, with prereg.SLACK_PER_SLOT monkeypatched to 24 (no test runs the 2048 mint):
- derive() refuses a report whose bytes are not the pinned digest (D-24) and questions that are not
  phase17_isolation.held_out_by_slot() (D-32) before any minting, and a short name slot is the D-26
  STOP naming every slot's count;
- derive() returns exactly prereg.mint_all's lists, the nested sizes, the numeric neighbour counts,
  the approval block, the completion source and the Phase 17 filter proof on the scored prefixes.

It never writes under the real results/.
"""

import pathlib
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

import phase38_mint  # noqa: E402  (scripts/ is not a package; never aliased)
import phase38_prereg as prereg  # noqa: E402  (same)

SMALL = 24


@pytest.fixture(scope="module")
def tok():
    from personacore.tokenizer import from_json

    return from_json(_ROOT / "artifacts" / "tokenizer.json")


@pytest.fixture(scope="module")
def parsed():
    text = (_ROOT / prereg.PHASE17_REPORT).read_text(encoding="utf-8")
    return prereg.parse_completions(text)


@pytest.fixture(scope="module")
def derived():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(prereg, "SLACK_PER_SLOT", SMALL)
        return phase38_mint.derive()


@pytest.fixture(scope="module")
def direct(tok, parsed):
    completions, questions = parsed
    return prereg.mint_all(tok, completions, questions, per_slot=SMALL)


def _questions(parsed):
    return [q for slot in prereg.SLOTS for q in parsed[1][slot]]


def test_report_bytes_are_the_pinned_report():
    import hashlib

    blob = phase38_mint.report_bytes()
    assert hashlib.sha256(blob).hexdigest() == prereg.PHASE17_REPORT_SHA256


def test_derive_reproduces_mint_all(derived, direct):
    assert tuple(derived["slots"]) == prereg.SLOTS
    for key in ("seed", "per_slot", "max_draws", "stream", "stop_draw"):
        assert derived[key] == direct[key], key
    assert derived["per_slot"] == SMALL
    assert derived["max_draws"] == prereg.MAX_DRAWS
    for slot in prereg.SLOTS:
        got, want = derived["slots"][slot], direct["slots"][slot]
        for key in ("cleared", "n_cleared", "taught_token_count", "rejections", "max_set_size"):
            assert got[key] == want[key], (slot, key)
        assert got["nested_sizes"] == list(prereg.nested_sizes(got["max_set_size"])), slot
    for slot in prereg.NAME_SLOTS:
        assert derived["slots"][slot]["n_cleared"] >= SMALL, slot
    assert derived["slots"]["birth_year"]["n_cleared"] == 219
    assert derived["slots"]["birth_year"]["max_set_size"] == 220
    assert derived["slots"]["house_number"]["n_cleared"] == 8768
    assert derived["slots"]["house_number"]["max_set_size"] == 512


def test_derive_carries_approval_and_completion_source(derived):
    assert derived["approval"] == prereg.approval_block()
    assert derived["rule_entry"] == "phase38_prereg.ENTRIES['e5_minting_rule']"
    clearance = prereg.ENTRIES["e5_minting_rule"]["value"]["clearance"]
    assert derived["completion_source"] == {
        "path": prereg.PHASE17_REPORT,
        "sha256": prereg.PHASE17_REPORT_SHA256,
        "device": "mps",
        "base_git": clearance["base_git"],
        "completions": 416,
    }
    assert derived["completion_source"]["completions"] == prereg.COMPLETIONS_TOTAL


def test_neighbour_counts_per_nested_size(derived):
    for slot in prereg.NUMERIC_RANGES:
        row = derived["slots"][slot]
        flags = prereg.neighbour_flags(row["cleared"])
        assert row["neighbour_d1"] == [i for i, f in enumerate(flags) if f]
        want = {str(n): sum(flags[: n - 1]) for n in row["nested_sizes"]}
        assert row["neighbour_counts"] == want, slot
    for slot in prereg.NAME_SLOTS:
        assert "neighbour_counts" not in derived["slots"][slot], slot


def test_phase17_proof_on_the_scored_prefixes(derived, tok, parsed):
    proof = derived["phase17_filter_proof"]
    scored = sum(derived["slots"][s]["max_set_size"] - 1 for s in prereg.SLOTS)
    assert proof["passed"] is True
    assert proof["values_checked"] == scored
    assert proof["functions"] == [
        "phase17_personas.filter_token_budget",
        "phase17_personas.filter_roundtrip",
        "phase17_personas.filter_substring_disjoint",
        "phase17_personas.filter_absent_from_questions",
    ]
    small = {s: {"cleared": ["zorbaxil", "quentolm"], "max_set_size": 2} for s in ("a",)}
    assert phase38_mint.phase17_proof(tok, small, _questions(parsed))["values_checked"] == 1
    with pytest.raises(SystemExit, match="fixture question"):
        phase38_mint.phase17_proof(tok, small, ["is it zorbaxil?"])


def test_a_changed_report_byte_is_the_d24_stop(monkeypatch):
    blob = bytearray((_ROOT / prereg.PHASE17_REPORT).read_bytes())
    blob[100] ^= 1
    monkeypatch.setattr(phase38_mint, "report_bytes", lambda: bytes(blob))
    monkeypatch.setattr(prereg, "mint_all", _never)
    with pytest.raises(SystemExit, match="D-24"):
        phase38_mint.derive()


def test_questions_that_are_not_held_out_are_the_d32_stop(monkeypatch):
    import phase17_isolation

    real = phase17_isolation.held_out_by_slot()
    swapped = {slot: list(reversed(items)) for slot, items in real.items()}
    monkeypatch.setattr(phase17_isolation, "held_out_by_slot", lambda: swapped)
    monkeypatch.setattr(prereg, "mint_all", _never)
    with pytest.raises(SystemExit, match="D-32"):
        phase38_mint.derive()


def test_a_short_name_slot_is_the_d26_stop(monkeypatch):
    monkeypatch.setattr(prereg, "SLACK_PER_SLOT", SMALL)
    monkeypatch.setattr(prereg, "MAX_DRAWS", 50)
    with pytest.raises(SystemExit, match="D-26") as stop:
        phase38_mint.derive()
    for slot in prereg.NAME_SLOTS:
        assert f"'{slot}':" in str(stop.value), slot


def _never(*args, **kwargs):
    raise AssertionError("minting was reached past a refused premise")
