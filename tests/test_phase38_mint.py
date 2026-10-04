"""Plan 38-03: the E5 minting command (scripts/phase38_mint.py), CPU-only.

What this file proves, with prereg.SLACK_PER_SLOT monkeypatched to 24 (no test runs the 2048 mint):
- derive() refuses a report whose bytes are not the pinned digest (D-24) and questions that are not
  phase17_isolation.held_out_by_slot() (D-32) before any minting, and a short name slot is the D-26
  STOP naming every slot's count;
- derive() returns exactly prereg.mint_all's lists, the nested sizes, the numeric neighbour counts,
  the approval block, the completion source and the Phase 17 filter proof on the scored prefixes;
- one REAL small run through main() into a tmp root writes the record (hashes, provenance, the
  dirty-tree pathspec), its slots feed prereg.max_set_size and phase36_caps.check_unit_caps (the
  consumer chain plan 05 uses), a second run verifies it, and an edited copy fails verification;
- the writer refuses a non-minting path first, an existing record, an untracked prereg and a dirty
  tree; main takes no argument and calls derive() with no override (AST);
- the committed record, if any, is honest: the small lists are prefixes of it (D-25).

`git status --porcelain -- results ledger` is unchanged by every test and the real results/ never
gains a phase38 record.
"""

import ast
import copy
import hashlib
import json
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

import phase14_recall  # noqa: E402  (scripts/ is not a package)
import phase36_caps  # noqa: E402  (same)
import phase38_mint  # noqa: E402  (same; never aliased — _untested_functions counts by name)
import phase38_prereg as prereg  # noqa: E402  (same)

from personacore.provenance import git_sha  # noqa: E402
from test_phase29_prereg import _git, _planted  # noqa: E402
from test_phase36_prereg import _skip_failures, _untested_functions  # noqa: E402

SMALL = 24
_REAL_RECORD = _ROOT / prereg.MINTING_RECORD


@pytest.fixture(autouse=True)
def _real_tree_untouched():
    before = _git("status", "--porcelain", "--", "results", "ledger")
    record_before = _REAL_RECORD.exists()
    yield
    assert _git("status", "--porcelain", "--", "results", "ledger") == before
    assert _REAL_RECORD.exists() == record_before


@pytest.fixture
def recorder(monkeypatch):
    calls = []
    monkeypatch.setattr(phase38_mint, "refuse_if_dirty", lambda **kw: calls.append(kw))
    monkeypatch.chdir(_ROOT)  # main() chdirs to _ROOT; restore the cwd afterwards
    return calls


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


def test_a_changed_report_byte_is_the_d24_stop(monkeypatch, tmp_path, recorder):
    blob = bytearray((_ROOT / prereg.PHASE17_REPORT).read_bytes())
    blob[100] ^= 1
    monkeypatch.setattr(phase38_mint, "report_bytes", lambda: bytes(blob))
    monkeypatch.setattr(prereg, "mint_all", _never)
    with pytest.raises(SystemExit, match="D-24"):
        phase38_mint.main([], out_root=tmp_path)
    assert list(tmp_path.iterdir()) == [] and recorder == []


def test_questions_that_are_not_held_out_are_the_d32_stop(monkeypatch, tmp_path, recorder):
    import phase17_isolation

    real = phase17_isolation.held_out_by_slot()
    swapped = {slot: list(reversed(items)) for slot, items in real.items()}
    monkeypatch.setattr(phase17_isolation, "held_out_by_slot", lambda: swapped)
    monkeypatch.setattr(prereg, "mint_all", _never)
    with pytest.raises(SystemExit, match="D-32"):
        phase38_mint.main([], out_root=tmp_path)
    assert list(tmp_path.iterdir()) == [] and recorder == []


def test_a_short_name_slot_is_the_d26_stop(monkeypatch, tmp_path, recorder):
    monkeypatch.setattr(prereg, "SLACK_PER_SLOT", SMALL)
    monkeypatch.setattr(prereg, "MAX_DRAWS", 50)
    with pytest.raises(SystemExit, match="D-26") as stop:
        phase38_mint.main([], out_root=tmp_path)
    for slot in prereg.NAME_SLOTS:
        assert f"'{slot}':" in str(stop.value), slot
    assert list(tmp_path.iterdir()) == [] and recorder == []


def _never(*args, **kwargs):
    raise AssertionError("minting was reached past a refused premise")


# =================================================================================================
# THE WRITER, VERIFY MODE AND THE REAL SMALL RUN THROUGH main().
# =================================================================================================


def _plain(value):
    return json.loads(json.dumps(value))


@pytest.fixture(scope="module")
def written(tmp_path_factory):
    """One REAL main() run at SLACK_PER_SLOT = 24 into a tmp root (Pitfall 12)."""
    root = tmp_path_factory.mktemp("mint")
    calls = []
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(prereg, "SLACK_PER_SLOT", SMALL)
        mp.setattr(phase38_mint, "refuse_if_dirty", lambda **kw: calls.append(kw))
        mp.chdir(_ROOT)
        assert phase38_mint.main([], out_root=root) == 0
    path = root / prereg.MINTING_RECORD
    return {"root": root, "path": path, "record": json.loads(path.read_text()), "calls": calls}


def test_main_writes_the_record_with_hashes_and_provenance(written, derived):
    record = written["record"]
    for key in derived:
        assert record[key] == _plain(derived[key]), key
    assert set(record["input_sha256"]) == set(phase38_mint.INPUT_RECORDS)
    for rel, digest in record["input_sha256"].items():
        assert digest == hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest(), rel
    provenance = record["provenance"]
    assert provenance["run"]["device"] == "cpu"
    assert provenance["run"]["git_sha"] == provenance["head_at_write"] == git_sha()
    assert set(provenance["run"]) == {
        "git_sha",
        "device",
        "torch_version",
        "started_utc",
        "finished_utc",
    }
    assert set(provenance["module_sha256"]) == set(phase38_mint.MODULES)
    for rel, digest in provenance["module_sha256"].items():
        assert digest == hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest(), rel
    assert [c["pathspec"] for c in written["calls"]] == [("scripts", "src", "results")]
    assert [c["cwd"] for c in written["calls"]] == [phase38_mint._ROOT]
    assert [c["who"] for c in written["calls"]] == ["phase38_mint"]


def test_the_record_feeds_the_sizes_and_caps_consumer(written):
    slots = written["record"]["slots"]
    sizes = {slot: prereg.max_set_size(slots[slot]["n_cleared"]) for slot in prereg.SLOTS}
    assert sizes["birth_year"] == 220
    checked = phase36_caps.check_unit_caps("E5", sets=len(sizes), max_set_size=max(sizes.values()))
    assert checked == {"sets": len(prereg.SLOTS), "max_set_size": max(sizes.values())}
    assert sizes == {slot: slots[slot]["max_set_size"] for slot in prereg.SLOTS}


def test_a_second_main_verifies_and_changes_nothing(written, recorder, monkeypatch, capsys):
    before = written["path"].read_bytes()
    monkeypatch.setattr(prereg, "SLACK_PER_SLOT", SMALL)
    assert phase38_mint.main([], out_root=written["root"]) == 0
    assert written["path"].read_bytes() == before
    assert recorder == []
    out = capsys.readouterr().out
    assert "MINTING VERIFIED" in out
    for slot in prereg.SLOTS:
        assert f"{slot}:" in out, slot


def _edit_cleared(record):
    record["slots"]["person_name"]["cleared"][0] += "x"


def _edit_input(record):
    record["input_sha256"][prereg.PHASE17_REPORT] = "0" * 64


@pytest.mark.parametrize("edit", [_edit_cleared, _edit_input])
def test_an_edited_record_fails_verification(
    written, derived, tmp_path, recorder, monkeypatch, edit
):
    # derive() is the cached small derivation here; the real one ran in `written` and in the
    # verify test above, and check_record compares against it either way.
    monkeypatch.setattr(phase38_mint, "derive", lambda: derived)
    good = tmp_path / "good" / prereg.MINTING_RECORD
    good.parent.mkdir(parents=True)
    good.write_bytes(written["path"].read_bytes())
    assert phase38_mint.check_record(derived, good)["slots"] == written["record"]["slots"]
    record = copy.deepcopy(written["record"])
    edit(record)
    bad = tmp_path / "bad" / prereg.MINTING_RECORD
    bad.parent.mkdir(parents=True)
    bad.write_text(json.dumps(record))
    before = bad.read_bytes()
    with pytest.raises(SystemExit, match="STOP"):
        phase38_mint.main([], out_root=tmp_path / "bad")
    assert bad.read_bytes() == before and recorder == []


def test_a_dirty_tree_writes_nothing(derived, tmp_path, monkeypatch):
    def dirty(**kw):
        raise SystemExit("dirty")

    monkeypatch.setattr(phase38_mint, "refuse_if_dirty", dirty)
    monkeypatch.setattr(phase38_mint, "derive", lambda: derived)
    monkeypatch.chdir(_ROOT)
    with pytest.raises(SystemExit, match="dirty"):
        phase38_mint.main([], out_root=tmp_path)
    assert not (tmp_path / prereg.MINTING_RECORD).exists()


def test_a_non_minting_path_is_refused_before_any_other_check(derived, tmp_path, recorder):
    path = tmp_path / "results" / "phase37_x.json"
    path.parent.mkdir()
    path.write_text("{}")  # exists too: the glob refusal must come first
    with pytest.raises(SystemExit, match="MINTING_GLOB"):
        phase38_mint.write_record(derived, path, base=tmp_path, run={})
    assert recorder == [] and path.read_text() == "{}"


def test_an_existing_record_is_never_overwritten(derived, tmp_path, recorder):
    path = tmp_path / prereg.MINTING_RECORD
    path.parent.mkdir()
    path.write_text("{}")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        phase38_mint.write_record(derived, path, base=tmp_path, run={})
    assert recorder == [] and path.read_text() == "{}"


def test_an_untracked_prereg_is_refused(derived, tmp_path, recorder, monkeypatch):
    real_run = phase38_mint.subprocess.run

    def untracked(args, **kw):
        if args[:3] == ["git", "ls-files", "--error-unmatch"]:
            return real_run(["git", "ls-files", "--error-unmatch", "no/such/file"], **kw)
        return real_run(args, **kw)

    monkeypatch.setattr(phase38_mint.subprocess, "run", untracked)
    with pytest.raises(SystemExit, match="not tracked"):
        phase38_mint.write_record(derived, tmp_path / prereg.MINTING_RECORD, base=tmp_path, run={})
    assert recorder == [] and list(tmp_path.iterdir()) == []


def test_a_record_under_the_root_excludes_itself_from_the_dirty_check(derived, monkeypatch):
    # A sibling name under the glob that never exists: the refusal stops before any write.
    path = _ROOT / "results" / "phase38_minting_probe.json"
    assert not path.exists()
    calls = []

    def stop(**kw):
        calls.append(kw)
        raise SystemExit("recorded")

    monkeypatch.setattr(phase38_mint, "refuse_if_dirty", stop)
    with pytest.raises(SystemExit, match="recorded"):
        phase38_mint.write_record(derived, path, base=_ROOT, run={})
    assert [c["pathspec"] for c in calls] == [
        ("scripts", "src", "results", ":(exclude)results/phase38_minting_probe.json")
    ]
    assert not path.exists()


def test_main_refuses_any_argument():
    with pytest.raises(SystemExit) as stop:
        phase38_mint.main(["bogus"])
    assert stop.value.code == phase38_mint.__doc__


def test_main_calls_derive_with_no_override():
    tree = ast.parse((_SCRIPTS / "phase38_mint.py").read_text(encoding="utf-8"))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    calls = [
        n
        for n in ast.walk(main)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "derive"
    ]
    assert len(calls) == 1
    assert calls[0].args == [] and calls[0].keywords == []


def test_the_committed_record_is_honest_in_both_states(derived):
    tracked = _git("ls-files", prereg.MINTING_RECORD)
    if tracked:
        committed = json.loads(_REAL_RECORD.read_text(encoding="utf-8"))
        assert committed["per_slot"] == prereg.SLACK_PER_SLOT
        for slot in prereg.NAME_SLOTS:
            small = derived["slots"][slot]["cleared"]
            assert committed["slots"][slot]["cleared"][: len(small)] == small, slot
        for slot in prereg.NUMERIC_RANGES:
            assert committed["slots"][slot]["cleared"] == derived["slots"][slot]["cleared"], slot
    else:
        assert tracked == ""
        assert prereg.MINTING_RECORD not in _git("ls-files", "results")


def test_helpers(tmp_path):
    with pytest.raises(SystemExit, match=r"^\[phase38_mint\] no$"):
        phase38_mint._prove(False, "no")
    assert phase38_mint._prove(True, "yes") is None
    (tmp_path / "f").write_bytes(b"abc")
    assert phase38_mint._sha256(tmp_path / "f") == hashlib.sha256(b"abc").hexdigest()
    assert phase38_mint._now().endswith("+00:00")


def test_tokenizer_path_is_the_recall_constant():
    rel = pathlib.Path(phase14_recall.TOKENIZER_PATH).resolve().relative_to(_ROOT).as_posix()
    assert phase38_mint.TOKENIZER == rel
    assert phase38_mint.INPUT_RECORDS == (prereg.PHASE17_REPORT, rel)


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


def test_every_phase38_mint_function_has_a_cpu_test():
    source = (_SCRIPTS / "phase38_mint.py").read_text(encoding="utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert len(defs) >= 8, "meta-guard: the census would be vacuous"
    assert _untested_functions("phase38_mint", source, test_source) == []
