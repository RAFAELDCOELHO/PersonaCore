"""Plans 35-01/02: the v6.0 pre-registration skeleton, its core, and the PREREG-09 research.

What this file proves, CPU-only:
- the one-run audit port reproduces the two values printed in arXiv 2305.08846v1 (App. D p. 46,
  §7 p. 28) within the declared tolerance, holds the delta = 0, v = r closed form, and a dropped
  delta lands outside the tolerance;
- E3's accounting is basic composition BY REFERENCE, with SELECTION_ACCOUNTED False;
- the research note cites both sources with pages and its first add precedes every commit of
  scripts/phase35_prereg.py (ROADMAP P35 SC5), RED on a planted throwaway repo;
- every entry has exactly the four D-14 fields and none carries a proposer field (runtime + AST,
  RED on planted copies);
- the module imports without torch, and this file has zero skips.
- (Plan 02) the module is frozen before every results/phase36_* .. phase45_* file; the closed
  pins are imported, never copied; seeds, targets, the AUDIT-02 cut and the (b) margin are read
  from their sources, never retyped (AST, RED on planted copies); R1a re-derives from its record.
- (Plan 03) the deferred-slot registry: 17 slots reachable only through fill(), every rule
  exercised through fill() with each refusal (D-06, D-11, D-16, D-17 incl. B4, RECIPE-04,
  COST-02, D-14, W3) watched firing on records planted under tmp_path.
- (Plan 04) D-02 made mechanical: the slot census (undeclared, outside owner, different rule) over
  scripts/ and src/, the per-fill-file ordering legs (a)/(b)/(c) on throwaway repos, the
  input-record registry, and the census that every prereg function has a CPU test, each watched RED.

It reads only tracked files and git history and writes nothing under results/. A shallow clone
FAILS, never skips.
"""

import ast
import fnmatch
import inspect
import json
import math
import pathlib
import subprocess
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

import erasure_gate  # noqa: E402  (scripts/ is not a package)
import mitigation_budget  # noqa: E402  (same)
import mitigation_gate  # noqa: E402  (same)
import mitigation_unit  # noqa: E402  (same)
import phase19_floor  # noqa: E402  (same)
import phase25_epsilon  # noqa: E402  (same)
import phase25_gate05  # noqa: E402  (same)
import phase25_record  # noqa: E402  (same)
import phase26_prereg  # noqa: E402  (same)
import phase29_prereg  # noqa: E402  (same)
import phase35_prereg  # noqa: E402  (same)

from test_phase29_prereg import (  # noqa: E402  (underscore names only)
    _assert_frozen_before,
    _git,
    _module_targets,
    _numeric_constants,
    _planted,
)

PREREG = "scripts/phase35_prereg.py"
NOTE = ".planning/research/V6-PREREG-09.md"


def _git_in(repo):
    """A git runner bound to `repo`; real-repo and throwaway-repo legs share one check body."""

    def run(*args, check=True):
        return subprocess.run(
            ("git", "-C", str(repo), *args), capture_output=True, text=True, check=check
        )

    return run


def _planted_repo(root, commits):
    """A throwaway repo under `root` (a tmp_path subdirectory): one commit per element of
    `commits`, each a list of (relpath, text) pairs."""
    root.mkdir(parents=True)
    run = _git_in(root)
    run("-c", "init.defaultBranch=main", "init", "-q")
    for index, files in enumerate(commits):
        for relpath, text in files:
            target = root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        run("add", *(relpath for relpath, _ in files))
        run(
            "-c",
            "user.name=planted",
            "-c",
            "user.email=planted@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-q",
            "-m",
            f"step-{index}",
        )
    return run


def _insert_at(source, lineno, col_offset, text):
    """Insert `text` at an AST position (1-based line, UTF-8 byte column)."""
    lines = source.splitlines(keepends=True)
    raw = lines[lineno - 1].encode("utf-8")
    lines[lineno - 1] = (raw[:col_offset] + text.encode("utf-8") + raw[col_offset:]).decode("utf-8")
    return "".join(lines)


# =================================================================================================
# (1) THE ONE-RUN AUDIT BOUND (D-11).
# =================================================================================================


def _tolerance():
    return phase35_prereg.ENTRIES["one_run_tolerance"]["value"]


def test_one_run_reproduces_appendix_d_p46():
    pin = phase35_prereg.ONE_RUN_PUBLISHED["app_d_p46"]
    assert _tolerance() == 1e-3
    assert pin["inputs"] == (1000, 100, 75, 1e-4, 0.05)
    assert pin["published"] == 0.673
    assert abs(phase35_prereg.eps_lower_one_run(*pin["inputs"]) - pin["published"]) < _tolerance()


def test_one_run_reproduces_section7_p28():
    pin = phase35_prereg.ONE_RUN_PUBLISHED["sec7_p28"]
    assert _tolerance() == 1e-3
    assert pin["inputs"] == (100000, 1510, 1439, 1e-5, 0.05)
    assert pin["published"] == 2.675
    assert abs(phase35_prereg.eps_lower_one_run(*pin["inputs"]) - pin["published"]) < _tolerance()


def test_one_run_closed_form_at_delta_zero():
    expected = -math.log(0.05 ** (-1 / 16) - 1)
    assert abs(phase35_prereg.eps_lower_one_run(16, 16, 16, 0, 0.05) - expected) < 1e-8


def test_one_run_tolerance_cannot_absorb_a_dropped_delta():
    assert abs(phase35_prereg.eps_lower_one_run(1000, 100, 75, 0, 0.05) - 0.673) > _tolerance()


def test_one_run_reproduction_holds(monkeypatch):
    assert phase35_prereg.one_run_reproduction_holds() is True
    monkeypatch.setattr(phase35_prereg, "eps_lower_one_run", lambda *a: 0.0)
    assert phase35_prereg.one_run_reproduction_holds() is False


@pytest.mark.parametrize(
    "args",
    [
        (100, 50, 51, 1e-5, 0.05),  # v > r
        (100, 101, 50, 1e-5, 0.05),  # r > m
        (True, 1, 1, 1e-5, 0.05),  # m is a bool
        (100, 1.0, 1, 1e-5, 0.05),  # r is a float
        (100, 50, 40, 1e-5, 0),  # beta = 0
        (100, 50, 40, 1e-5, 1),  # beta = 1
        (100, 50, 40, -1e-5, 0.05),  # negative delta
        (100, 50, 40, True, 0.05),  # delta is a bool
    ],
)
def test_one_run_refuses_bad_inputs(args):
    with pytest.raises(SystemExit):
        phase35_prereg.eps_lower_one_run(*args)


def test_one_run_p_value_refuses_an_infinite_eps():
    with pytest.raises(SystemExit):
        phase35_prereg.p_value_one_run(100, 50, 40, float("inf"), 1e-5)


# =================================================================================================
# (2) E3 BASIC COMPOSITION, BY REFERENCE (D-12).
# =================================================================================================


def test_composition_is_basic_and_by_reference():
    assert phase35_prereg.CURVE_TOTAL is phase25_epsilon.curve_total
    assert phase35_prereg.SELECTION_ACCOUNTED is False
    assert phase35_prereg.SELECTION_ACCOUNTED is phase25_epsilon.SELECTION_ACCOUNTED
    assert phase35_prereg.DELTA is mitigation_unit.DELTA
    total = phase35_prereg.CURVE_TOTAL([1.5, 2.25, 0.25], delta=mitigation_unit.DELTA)
    assert total == (4.0, 3 * 1e-5)
    with pytest.raises(ValueError):
        phase35_prereg.CURVE_TOTAL([1.5, None], delta=mitigation_unit.DELTA)


# =================================================================================================
# (3) THE RESEARCH NOTE AND ITS ORDERING (D-10, PREREG-09, ROADMAP P35 SC5).
# =================================================================================================


def test_research_note_cites_both_sources_with_pages():
    note = _ROOT / NOTE
    assert note.is_file(), f"{NOTE} is missing"
    text = note.read_text(encoding="utf-8")
    for needed in (
        "2305.08846v1",
        "2110.03620v2",
        "Theorem 5.2",
        "Corollary 5.4",
        "Appendix D",
        "Theorem 2",
        "Theorem 6",
        "p. 46",
        "p. 28",
        # The single PDF line carrying each pinned value, verbatim (Rafael's review, 2026-10-01).
        "obtain a lower bound of ε≥0.673 for δ = 10−4 and 95% confidence. (This is slightly",
        "In Figure 11, the highest value of the lower bound is ε ≥2.675 for δ = 10−5, which is",
    ):
        assert needed in text, f"{NOTE} does not cite {needed!r}"
    assert "não verificado" not in text


def _note_ordering_failures(run, note, prereg):
    """Every commit touching `prereg` must have the note's first add as an ancestor (or be it)."""
    failures = []
    if run("rev-parse", "--is-shallow-repository").stdout.strip() != "false":
        failures.append("shallow clone: the ordering cannot be checked (fetch-depth: 0)")
    adds = run("log", "--diff-filter=A", "--format=%H", "--", note).stdout.split()
    if not adds:
        failures.append(f"{note} has no add commit: commit the note first")
    prereg_commits = run("log", "--format=%H", "--", prereg).stdout.split()
    if run("ls-files", prereg).stdout.strip() and not prereg_commits:
        failures.append(f"{prereg} is tracked but has no commit")
    pairs_checked = 0
    for commit in prereg_commits:
        pairs_checked += 1
        if not adds:
            continue
        if run("merge-base", "--is-ancestor", adds[-1], commit, check=False).returncode != 0:
            failures.append(f"{prereg} commit {commit} does not descend from {note}'s first add")
    return failures, pairs_checked


def test_research_note_precedes_every_prereg_commit():
    failures, pairs = _note_ordering_failures(_git_in(_ROOT), NOTE, PREREG)
    assert failures == []
    assert pairs == len(_git("log", "--format=%H", "--", PREREG).split())
    if _git("ls-files", PREREG):
        assert pairs >= 1


def test_research_note_ordering_reds_on_a_planted_repo(tmp_path):
    note, prereg = "note.md", "scripts/p.py"

    green = _planted_repo(tmp_path / "green", [[(note, "n")], [(prereg, "p")]])
    assert _note_ordering_failures(green, note, prereg) == ([], 1)

    reversed_order = _planted_repo(tmp_path / "reversed", [[(prereg, "p")], [(note, "n")]])
    failures, _ = _note_ordering_failures(reversed_order, note, prereg)
    assert failures

    never_added = _planted_repo(tmp_path / "never", [[(prereg, "p")]])
    failures, _ = _note_ordering_failures(never_added, note, prereg)
    assert any("commit the note first" in failure for failure in failures), failures


# =================================================================================================
# (4) ENTRIES: EXACTLY FOUR FIELDS, NO PROPOSER (D-07 as amended by D-14).
# =================================================================================================


def test_entries_have_exactly_the_four_fields():
    entries = phase35_prereg.ENTRIES
    assert entries
    for name, entry in entries.items():
        assert set(entry) == set(phase35_prereg.ENTRY_FIELDS)
        assert set(entry) == {"value", "derivation", "kind", "source"}, name
        assert entry["kind"] in ("derived", "preference"), name
        assert isinstance(entry["derivation"], str) and entry["derivation"].strip(), name
        assert isinstance(entry["source"], str) and entry["source"].strip(), name
    with pytest.raises(TypeError):
        entries["planted"] = {}


def _good_entry():
    return {"value": 1, "derivation": "d", "kind": "derived", "source": "s"}


def test_entries_refuse_an_unknown_kind_or_missing_field():
    phase35_prereg._prove_entry("ok", _good_entry())
    bad_kind = {**_good_entry(), "kind": "guess"}
    missing_source = {k: v for k, v in _good_entry().items() if k != "source"}
    empty_derivation = {**_good_entry(), "derivation": ""}
    for entry in (bad_kind, missing_source, empty_derivation):
        with pytest.raises(SystemExit):
            phase35_prereg._prove_entry("x", entry)


def _entries_node(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_ENTRIES" for target in node.targets
        ):
            return node
    return None


_PROVENANCE_KEYS = ("proposer", "adopted_by")


def _entry_string_failures(source):
    tree = ast.parse(source)
    failures = []
    entries = _entries_node(tree)
    if entries is None:
        return ["no module-level _ENTRIES assignment"]
    for node in ast.walk(entries):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value in _PROVENANCE_KEYS:
                    failures.append(f"_ENTRIES key {key.value!r} at line {key.lineno}")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and phase35_prereg.FORBIDDEN_PHRASE in node.value
        ):
            failures.append(f"forbidden phrase at line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value in _PROVENANCE_KEYS:
                    failures.append(f"module dict key {key.value!r} at line {key.lineno}")
    return failures


def _first_inner(entries, wanted_key):
    """(key node, value node) of the first inner-dict item keyed `wanted_key`, in source order."""
    found = []
    for node in ast.walk(entries.value):
        if isinstance(node, ast.Dict) and node is not entries.value:
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == wanted_key:
                    found.append((key, value))
    assert found, f"no inner {wanted_key!r} key in _ENTRIES"
    return min(found, key=lambda pair: (pair[0].lineno, pair[0].col_offset))


def test_no_proposer_or_adopted_by_in_any_entry(tmp_path):
    for name, entry in phase35_prereg.ENTRIES.items():
        for banned in _PROVENANCE_KEYS:
            assert banned not in entry, name
    for banned in _PROVENANCE_KEYS:
        with pytest.raises(SystemExit) as refused:
            phase35_prereg._prove_entry("x", {**_good_entry(), banned: "Rafael"})
        assert banned in str(refused.value)

    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    tree = ast.parse(source)
    entries = _entries_node(tree)
    assert entries is not None, "meta-guard: _ENTRIES not found, the walk would be vacuous"
    assert _entry_string_failures(source) == []

    kind_key, _ = _first_inner(entries, "kind")
    planted_key = _insert_at(source, kind_key.lineno, kind_key.col_offset, '"proposer": "Rafael", ')
    ast.parse(planted_key)
    assert _entry_string_failures(_planted(tmp_path, source, planted_key, "key.py"))

    _, derivation = _first_inner(entries, "derivation")
    assert isinstance(derivation, ast.Constant) and isinstance(derivation.value, str)
    planted_phrase = _insert_at(
        source, derivation.lineno, derivation.col_offset + 1, phase35_prereg.FORBIDDEN_PHRASE
    )
    ast.parse(planted_phrase)
    assert _entry_string_failures(_planted(tmp_path, source, planted_phrase, "phrase.py"))

    assert real.read_bytes() == before


# =================================================================================================
# (5) CPU-ONLY AT IMPORT, AND ZERO SKIPS (D-13 / PREREG-08).
# =================================================================================================

_HEAVY = (
    "torch",
    "teach_persona",
    "phase19_erasure",
    "phase18_extraction",
    "phase23_run",
    "phase26_canary",
)


def test_the_prereg_imports_without_torch():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase35_prereg; "
        f"print(*[name in sys.modules for name in {_HEAVY!r}])"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"] * len(_HEAVY), out.stdout


_SKIP_ATTRS = ("skip", "skipif", "importorskip", "xfail")


def _skip_failures(source):
    failures = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr in _SKIP_ATTRS:
            failures.append(f"{node.attr} at line {node.lineno}")
        elif isinstance(node, ast.Name) and node.id == "_MPS_SKIP":
            failures.append(f"_MPS_SKIP at line {node.lineno}")
    return failures


def test_no_skips_in_this_file(tmp_path):
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert _skip_failures(source) == []
    planted = source + '\n\ndef test_planted():\n    pytest.skip("x")\n'
    assert _skip_failures(_planted(tmp_path, source, planted, "skip.py"))


# =================================================================================================
# (6) PLAN 02 — ANCESTRY AND RECORD PATHS (PREREG-05 SC1, D-01).
# =================================================================================================


def test_phase35_prereg_is_frozen_before_every_v6_result():
    tracked = sorted(
        {
            path
            for spec in phase35_prereg.ARTIFACT_PATHSPECS
            for path in _git("ls-files", spec).split()
        }
    )
    _assert_frozen_before(PREREG, tracked)


def test_pathspecs_are_derived_and_cover_results_phase36_to_45():
    paths = phase35_prereg.V6_RESULT_PATHS
    specs = phase35_prereg.ARTIFACT_PATHSPECS
    assert specs == tuple(f"results/phase{n}_*" for n in range(36, 46))
    assert specs == tuple(sorted({p.split("_", 1)[0] + "_*" for p in paths}))
    assert len(set(paths)) == len(paths), "duplicate V6_RESULT_PATHS entry"
    for path in paths:
        assert path.startswith("results/phase"), path
        assert 36 <= int(path.removeprefix("results/phase").split("_", 1)[0]) <= 45, path


def test_pathspecs_are_disjoint_from_every_v5_tag_result():
    tracked = _git("ls-tree", "-r", "--name-only", "v5.0", "results").split()
    assert tracked, "v5.0 tracks no results file: this disjointness check would be blind"
    patterns = phase35_prereg.ARTIFACT_PATHSPECS + phase35_prereg.V6_RESULT_PATHS
    clashes = [path for path in tracked for pat in patterns if fnmatch.fnmatch(path, pat)]
    assert clashes == []


def test_records_at_commit_is_zero_and_pins_by_reference():
    assert phase35_prereg.RECORDS_AT_COMMIT == 0
    assert phase35_prereg.F_Y is mitigation_gate.F_Y
    assert phase35_prereg.F_C is mitigation_gate.F_C
    assert phase35_prereg.DIALOGUE_GAP_BAND is mitigation_gate.dialogue_gap_band
    assert phase35_prereg.CEILING_CLAUSE is phase26_prereg.CEILING_CLAUSE
    assert phase35_prereg.SIGMA_LADDER is mitigation_budget.SIGMA_LADDER
    assert phase35_prereg.MARGIN_K is erasure_gate.MARGIN_K


# =================================================================================================
# (7) PLAN 02 — SEEDS (D-05) AND E1 TARGETS (D-03).
# =================================================================================================


def test_seed_ladder_is_unchanged_since_its_first_add():
    import phase23_run  # teach_persona -> torch at import: inside the test only

    assert _git("rev-parse", "--is-shallow-repository") == "false", "shallow clone"
    first_add = _git("log", "--diff-filter=A", "--format=%H", "--", "scripts/phase23_run.py")
    first_add = first_add.split()[-1]
    assert first_add.startswith("5303819")
    tree = ast.parse(_git("show", f"{first_add}:scripts/phase23_run.py"))
    ladders = [value for name, value in _module_targets(tree) if name == "SEED_LADDER"]
    assert len(ladders) == 1, ladders
    assert ast.literal_eval(ladders[0]) == phase23_run.SEED_LADDER
    assert phase35_prereg.seed_list() is phase23_run.SEED_LADDER
    assert len(phase35_prereg.seed_list()) == 5


def test_seed_ladder_starts_with_the_phase19_seeds():
    import phase19_erasure  # torch at import: inside the test only

    assert phase35_prereg.e1_teaching_seeds() == phase19_erasure.DIALOGUE_NOISE_FLOOR_SEEDS
    assert phase35_prereg.e1_teaching_seeds() == phase35_prereg.seed_list()[:2]


def test_e1_targets_are_the_13_of_13_rows():
    import phase19_erasure  # torch at import: inside the test only

    assert phase35_prereg.e1_targets() == ("pet_name", "cat_name", "street", "sibling_name")
    fields = phase19_erasure.TARGET_RANKING_FIELDS
    slot, successes, n = (fields.index(f) for f in ("slot", "successes", "n_questions"))
    expected = tuple(r[slot] for r in phase19_erasure.TARGET_RANKING if r[successes] == r[n])
    assert phase35_prereg.e1_targets() == expected


# =================================================================================================
# (8) PLAN 02 — THE AUDIT-02 CUT (D-09), R1a AND THE (b) MARGIN (D-01, D-16), THE A2 CORPUS.
# =================================================================================================


def test_audit02_cut_is_read_from_the_canary_record():
    import phase26_canary  # git_sha() subprocess at import: inside the test only

    record = json.loads(phase26_canary.RECORD.read_text(encoding="utf-8"))
    ceiling = record["auditor_ceiling"]
    qualifying = [
        p["epsilon_upper"]
        for p in record["points"].values()
        if p.get("epsilon_upper") is not None and p["epsilon_upper"] >= ceiling
    ]
    assert len(qualifying) == 11
    assert min(qualifying) == 3.7965357228934966
    cut = phase35_prereg.audit02_cut()
    assert cut == 3.7965357228934966
    assert phase35_prereg.e4_runs(cut) is False
    assert phase35_prereg.e4_runs(math.nextafter(cut, math.inf)) is True
    for bad in (True, math.inf):
        with pytest.raises(SystemExit):
            phase35_prereg.e4_runs(bad)


def test_r1a_assertions_rederive_from_the_erased_record():
    import phase19_erasure  # torch at import: inside the test only

    assertions = phase35_prereg.R1A_ASSERTIONS
    rederived = phase35_prereg.r1a_rederive()
    assert rederived["k"] == 78 == assertions["k"]
    assert rederived["destroyed_pct"] == 77.6370113463966 == assertions["destroyed_pct"]
    assert assertions["target_correct"] == (0, 27)
    assert assertions["nontargets_beyond_margin"] == (7, 7)
    record = json.loads(phase19_erasure.arm_record_path("erased").read_text(encoding="utf-8"))
    # The trap, executable: config.k is the A2 attack budget, not the ablated-component count.
    assert record["config"]["k"] == 48
    assert len(record["config"]["ablated_components"]) == 78


def test_r1a_margin_is_the_noise_floor_record_read():
    path = _ROOT / phase19_floor.EVIDENCE_ARTIFACT["NONTARGET_NOISE_FLOOR"]
    floor = json.loads(path.read_text(encoding="utf-8"))["nontarget_noise_floor"]
    margin = phase35_prereg.e1_condition_b_margin()
    assert margin == 0.2962962962962963
    assert margin == floor["margin_at_gate"]
    assert margin == erasure_gate.MARGIN_K * floor["value"]
    assert phase35_prereg.r1a_rederive()["margin"] == margin


def test_a2_corpus_entries_are_the_216_a2_prompts():
    import phase18_extraction  # torch at import: inside the test only

    entries = phase35_prereg.a2_corpus_entries()
    assert len(entries) == 216
    assert all(entry["family"] == "A2" for entry in entries)
    corpus = json.loads(phase18_extraction.CORPUS_PATH.read_text(encoding="utf-8"))
    assert len(entries) == sum(p["family"] == "A2" for p in corpus["prompts"])


# =================================================================================================
# (9) PLAN 02 — CORE ENTRIES (D-01 "the inherited values still hold", D-14).
# =================================================================================================


def test_entries_f_y_f_c_equal_their_v4_tag_values():
    assert _git("rev-parse", "--is-shallow-repository") == "false", "shallow clone"
    tree = ast.parse(_git("show", "v4.0:scripts/mitigation_gate.py"))
    at_tag = {}
    for name in ("F_Y", "F_C"):
        values = [value for target, value in _module_targets(tree) if target == name]
        assert len(values) == 1, (name, values)
        at_tag[name] = ast.literal_eval(values[0])
    # The values on record at the immutable v4.0 tag, typed here and only here.
    assert at_tag == {"F_Y": 0.7, "F_C": 0.5}
    for name in ("F_Y", "F_C"):
        assert getattr(mitigation_gate, name) == at_tag[name]
        assert phase35_prereg.ENTRIES[name]["value"] == at_tag[name]


_CORE_ENTRIES = (
    "F_Y",
    "F_C",
    "dialogue_gap_band",
    "audit02_cut",
    "e4_runs",
    "audit03_ceiling_clause",
    "seed_list",
    "e1_teaching_seeds",
    "e1_targets",
    "e1_condition_b_margin",
    "r1a_assertions",
    "e3_sigmas",
    "mps_ceiling_hours",
    "e5_max_set_size",
)


def test_entries_label_f_y_and_f_c_as_preferences():
    entries = phase35_prereg.ENTRIES
    assert entries["F_Y"]["kind"] == entries["F_C"]["kind"] == "preference"
    assert entries["F_Y"]["value"] == mitigation_gate.F_Y
    assert entries["F_C"]["value"] == mitigation_gate.F_C
    missing = [name for name in _CORE_ENTRIES if name not in entries]
    assert missing == []
    assert entries["e1_condition_b_margin"]["value"] is phase35_prereg.e1_condition_b_margin
    assert entries["seed_list"]["value"] is phase35_prereg.seed_list
    assert entries["dialogue_gap_band"]["value"] is mitigation_gate.dialogue_gap_band
    assert entries["e3_sigmas"]["value"] == (0.0, 0.5, 1.0)
    assert all(s in mitigation_budget.SIGMA_LADDER for s in entries["e3_sigmas"]["value"])


# =================================================================================================
# (10) PLAN 02 — AST GUARDS, EACH WATCHED RED ON A PLANTED COPY (PREREG-05, T-35-07).
# =================================================================================================

_PINS = (
    "erasure_gate",
    "phase19_erasure",
    "mitigation_gate",
    "mitigation_budget",
    "phase18_extraction",
    "phase26_canary",
)
_LAZY = ("phase19_erasure", "phase18_extraction", "phase23_run", "phase26_canary", "teach_persona")


def _function(tree, name):
    found = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1, f"meta-guard: {len(found)} top-level def {name}"
    return found[0]


def _import_of(nodes, module):
    found = [
        n
        for n in nodes
        if isinstance(n, ast.Import) and any(alias.name == module for alias in n.names)
    ]
    assert len(found) == 1, f"meta-guard: {len(found)} `import {module}` nodes"
    return found[0]


def _replace_lines(source, start, end, new_lines):
    """Replace 1-based lines start..end (inclusive) with `new_lines` (end = start - 1 inserts)."""
    lines = source.splitlines(keepends=True)
    lines[start - 1 : end] = [line + "\n" for line in new_lines]
    return "".join(lines)


def _pin_import_failures(source, required=_PINS):
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    failures = [f"pin {pin} is never imported" for pin in required if pin not in imported]
    for node in tree.body:
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module]
        else:
            continue
        failures += [
            f"top-level lazy import {n} at line {node.lineno}" for n in names if n in _LAZY
        ]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in _PINS:
            failures.append(f"from {node.module} import ... copies a pin at line {node.lineno}")
    return failures


def test_six_closed_pins_imported_never_copied(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    tree = ast.parse(source)
    assert _pin_import_failures(source) == []

    canary = _import_of(ast.walk(_function(tree, "audit02_cut")), "phase26_canary")
    deleted = _replace_lines(source, canary.lineno, canary.end_lineno, [])
    ast.parse(deleted)
    failures = _pin_import_failures(_planted(tmp_path, source, deleted, "deleted.py"))
    assert any("phase26_canary" in f for f in failures), failures

    anchor = _import_of(tree.body, "mitigation_gate").end_lineno
    for name, line, expected in (
        ("lazy.py", "import phase19_erasure  # noqa: E402", "top-level lazy import"),
        ("copy.py", "from mitigation_gate import F_Y  # noqa: E402", "copies a pin"),
    ):
        planted = _replace_lines(source, anchor + 1, anchor, [line])
        ast.parse(planted)
        failures = _pin_import_failures(_planted(tmp_path, source, planted, name))
        assert any(expected in f for f in failures), (name, failures)

    assert real.read_bytes() == before


def _docstring_nodes(tree):
    owners = [tree] + [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return {
        id(owner.body[0].value)
        for owner in owners
        if owner.body
        and isinstance(owner.body[0], ast.Expr)
        and isinstance(owner.body[0].value, ast.Constant)
        and isinstance(owner.body[0].value.value, str)
    }


def _forbidden_literals():
    """The census sets, DERIVED from the live sources, never retyped."""
    import phase23_run  # torch at import: inside the test only
    import phase26_canary  # git_sha() subprocess at import: inside the test only

    canary = json.loads(phase26_canary.RECORD.read_text(encoding="utf-8"))
    path = _ROOT / phase19_floor.EVIDENCE_ARTIFACT["NONTARGET_NOISE_FLOOR"]
    floor = json.loads(path.read_text(encoding="utf-8"))["nontarget_noise_floor"]
    seeds = set(phase23_run.SEED_LADDER)
    floats = {
        phase35_prereg.audit02_cut(),
        canary["auditor_ceiling"],
        floor["margin_at_gate"],
        floor["value"],
    }
    names = set(phase35_prereg.e1_targets())
    for found in (seeds, floats, names):
        assert found, "meta-guard: an empty census set would be vacuous"
    return seeds, floats, names


def _literal_failures(source, seeds, floats, names):
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    constants = [n for n in ast.walk(tree) if isinstance(n, ast.Constant)]
    assert constants, "meta-guard: the walk visited no Constant"
    failures = [
        f"retyped {n.value!r} at line {n.lineno}"
        for n in _numeric_constants(tree)
        if (type(n.value) is int and n.value in seeds)
        or (type(n.value) is float and n.value in floats)
    ]
    failures += [
        f"retyped {n.value!r} at line {n.lineno}"
        for n in constants
        if isinstance(n.value, str) and id(n) not in docstrings and n.value in names
    ]
    return failures


def test_no_seed_target_or_record_value_is_retyped(tmp_path):
    seeds, floats, names = _forbidden_literals()
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    tree = ast.parse(source)
    assert _literal_failures(source, seeds, floats, names) == []

    ret = [n for n in ast.walk(_function(tree, "seed_list")) if isinstance(n, ast.Return)][-1]
    line = " " * ret.col_offset + f"return {tuple(phase35_prereg.seed_list())!r}"
    seed_plant = _replace_lines(source, ret.lineno, ret.end_lineno, [line])

    ret = [n for n in ast.walk(_function(tree, "audit02_cut")) if isinstance(n, ast.Return)][-1]
    line = " " * ret.col_offset + f"return {phase35_prereg.audit02_cut()!r}"
    cut_plant = _replace_lines(source, ret.lineno, ret.lineno - 1, [line])

    name_plant = source + f"_T = {phase35_prereg.e1_targets()[0]!r}\n"

    for name, planted in (("seed.py", seed_plant), ("cut.py", cut_plant), ("name.py", name_plant)):
        ast.parse(planted)
        copied = _planted(tmp_path, source, planted, name)
        assert _literal_failures(copied, seeds, floats, names), name

    assert real.read_bytes() == before


def _entry_value_nodes(source):
    entries = _entries_node(ast.parse(source))
    assert entries is not None, "meta-guard: no _ENTRIES"
    nodes = {}
    for key, inner in zip(entries.value.keys, entries.value.values, strict=True):
        for field, value in zip(inner.keys, inner.values, strict=True):
            if field.value == "value":
                nodes[key.value] = value
    assert set(nodes) == set(phase35_prereg.ENTRIES), "meta-guard: _ENTRIES walk incomplete"
    return nodes


def _is_attribute(node, module, attr):
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == module
        and node.attr == attr
    )


_ENTRY_ATTRIBUTES = {
    "F_Y": ("mitigation_gate", "F_Y"),
    "F_C": ("mitigation_gate", "F_C"),
    "delta": ("mitigation_unit", "DELTA"),
}
_MODULE_ATTRIBUTES = {
    "F_Y": ("mitigation_gate", "F_Y"),
    "F_C": ("mitigation_gate", "F_C"),
    "DELTA": ("mitigation_unit", "DELTA"),
    "MARGIN_K": ("erasure_gate", "MARGIN_K"),
    "CURVE_K": ("mitigation_budget", "CURVE_K"),
    "FULL_FIDELITY_K": ("mitigation_budget", "FULL_FIDELITY_K"),
    "STEP_BUDGET": ("mitigation_budget", "STEP_BUDGET"),
}


def _binding_failures(source):
    nodes = _entry_value_nodes(source)
    failures = [
        f"entry {name} value is not {module}.{attr}"
        for name, (module, attr) in _ENTRY_ATTRIBUTES.items()
        if not _is_attribute(nodes[name], module, attr)
    ]
    targets = list(_module_targets(ast.parse(source)))
    for name, (module, attr) in _MODULE_ATTRIBUTES.items():
        values = [value for target, value in targets if target == name]
        if len(values) != 1 or not _is_attribute(values[0], module, attr):
            failures.append(f"module binding {name} is not one {module}.{attr}")
    return failures


def test_entries_bind_f_y_f_c_and_delta_by_attribute(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    assert _binding_failures(source) == []

    node = _entry_value_nodes(source)["F_Y"]
    assert node.lineno == node.end_lineno
    raw = source.splitlines(keepends=True)[node.lineno - 1].encode("utf-8")
    text = repr(mitigation_gate.F_Y).encode("utf-8")
    line = (raw[: node.col_offset] + text + raw[node.end_col_offset :]).decode("utf-8")
    entry_plant = _replace_lines(source, node.lineno, node.lineno, [line.rstrip("\n")])

    assign = [
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "F_C" for t in n.targets)
    ]
    assert len(assign) == 1
    module_plant = _replace_lines(
        source, assign[0].lineno, assign[0].lineno, [f"F_C = {mitigation_gate.F_C!r}"]
    )

    for name, planted, expected in (
        ("entry.py", entry_plant, "entry F_Y"),
        ("module.py", module_plant, "module binding F_C"),
    ):
        ast.parse(planted)
        failures = _binding_failures(_planted(tmp_path, source, planted, name))
        assert any(expected in f for f in failures), (name, failures)

    assert real.read_bytes() == before


# =================================================================================================
# (11) PLAN 03 — THE REGISTRY OF DEFERRED SLOTS (D-02, D-15). Every rule is called through fill(),
# the way owners will call it. Records are planted under tmp_path only.
# =================================================================================================

_BUDGET = "results/phase36_budget.json"

_SLOT_OWNERS = {
    "v6_budget_and_stop_line": 36,
    "e2_S": 40,
    "r1b_tolerance_and_replicated": 37,
    "e1_checkpoint_grid": 41,
    "e1_condition_a_floors": 41,
    "e1_alternative_ordering": 41,
    "e3_grid_subset": 42,
    "e4_parameters": 43,
    "e5_minting_rule": 38,
    "e5_set_sizes": 38,
    "e6_entry_subset": 39,
    "e3_recall_threshold": 42,
    "e1_condition_b_margin": 41,
    "e1_condition_c_band_inputs": 41,
    "e2_noise_floor_estimator": 40,
    "e5_rank_moves_and_generation_collapses": 38,
    "e6_decomposition_rule": 39,
}


def _entry(value, source="test source"):
    return {"value": value, "derivation": "test derivation", "kind": "preference", "source": source}


def _inputs(root, monkeypatch, records):
    """Plant `{relpath: payload}` under `root` (JSON, or verbatim bytes) and point the module's
    `_REPO_ROOT` at it. `_v4_control()` still runs `git show` in the REAL repository."""
    for relpath, payload in records.items():
        target = root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, bytes):
            target.write_bytes(payload)
        else:
            target.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(phase35_prereg, "_REPO_ROOT", root)
    return tuple(records)


def _v4_path():
    return phase25_record.point_record_path(phase25_record.point_key("dp_n8", 0.0))


def _v4_bytes():
    return _v4_path().read_bytes()


def _v4_record():
    return json.loads(_v4_bytes())


def _control_payload(recipe, seed, taught, heldout):
    return {
        "recipe": dict(recipe),
        "seed": seed,
        "sigma": 0.0,
        "taught_recall": {"numerator": taught[0], "denominator": taught[1]},
        "heldout_recall": {"numerator": heldout[0], "denominator": heldout[1]},
    }


def _budget_payload(e2_seed_count=None, **hours):
    front_hours = {f: hours.get(f, 5.0) for f in phase35_prereg.V6_MPS_FRONTS}
    if e2_seed_count is None:
        e2_seed_count = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    return {
        "front_hours": front_hours,
        "total_hours": math.fsum(front_hours.values()),
        "stop_line_hours": 60.0,
        "e2_seed_count": e2_seed_count,
    }


def _measured(value, paths):
    """A derivation that names every input it read."""
    return _entry(value, source=" ".join(paths))


def test_slot_registry_declares_the_seventeen_slots():
    slots = phase35_prereg.SLOTS
    assert len(slots) == 17
    assert set(slots) == set(_SLOT_OWNERS)
    for name, slot in slots.items():
        assert slot["owner_phase"] == _SLOT_OWNERS[name], name
        assert set(slot) == {"owner_phase", "rule", "input_records"}, name
        assert slot["rule"].__name__ == "_rule_" + name
        assert slot["rule"].__module__ == "phase35_prereg"
    with pytest.raises(TypeError):
        slots["planted"] = {}
    with pytest.raises(TypeError):
        slots["e2_S"]["owner_phase"] = 36


def test_slot_fill_refuses_an_undeclared_or_non_string_slot():
    for bad in ("e9_undeclared", None):
        with pytest.raises(SystemExit) as refused:
            phase35_prereg.fill(bad)
        assert "not declared" in str(refused.value)
    glob = phase35_prereg.owner_prereg_glob("e2_S")
    assert glob == "scripts/phase40_*prereg.py"
    assert fnmatch.fnmatch("scripts/phase40_prereg.py", glob)
    assert fnmatch.fnmatch("scripts/phase40_seeds_prereg.py", glob)
    assert not fnmatch.fnmatch("scripts/phase40_driver.py", glob)
    assert not fnmatch.fnmatch("scripts/phase41_prereg.py", glob)


def test_slot_d04_deferred_slots_stay_with_their_phases():
    slots = phase35_prereg.SLOTS
    assert slots["e1_alternative_ordering"]["owner_phase"] == 41
    assert slots["e6_entry_subset"]["owner_phase"] == 39
    for name in ("e1_alternative_ordering", "e6_entry_subset"):
        assert name not in phase35_prereg.ENTRIES


def test_slot_measured_rules_consume_their_inputs(tmp_path, monkeypatch):
    for name, slot in phase35_prereg.SLOTS.items():
        params = inspect.signature(slot["rule"]).parameters.values()
        keyword_only = {p.name for p in params if p.kind is inspect.Parameter.KEYWORD_ONLY}
        measured = bool(slot["input_records"]) and name != "e1_condition_b_margin"
        assert ({"input_records", "derivation"} <= keyword_only) == measured, name

    minting = "results/phase38_minting.json"
    paths = _inputs(tmp_path, monkeypatch, {minting: {"m": 16}, "results/phase39_x.json": {}})
    consume = phase35_prereg._consume_inputs
    good = phase35_prereg._consume_inputs("e5_set_sizes", 7, (minting,), _measured(7, (minting,)))
    assert dict(good) == {minting: {"m": 16}}

    missing = "results/phase38_minting_missing.json"
    absolute = str(tmp_path / minting)
    for records, derivation in (
        (("results/phase39_x.json",), _measured(7, paths)),  # matches no declared pattern
        ((absolute,), _measured(7, (absolute,))),  # absolute
        (("../" + minting,), _measured(7, ("../" + minting,))),  # a `..` part
        ((missing,), _measured(7, (missing,))),  # missing file
        ((minting,), _entry(7, source="names nothing")),  # source omits the path
        ((minting,), _measured(8, (minting,))),  # value is not the filled value
        ((minting,), {**_measured(7, (minting,)), "proposer": "Rafael"}),  # D-14
        ((), _measured(7, (minting,))),  # no input at all
        ((minting, minting), _measured(7, (minting,))),  # review IN-02: a duplicate path
    ):
        with pytest.raises(SystemExit):
            consume("e5_set_sizes", 7, records, derivation)

    with pytest.raises(SystemExit):
        phase35_prereg._budget_front_hours({_BUDGET: {"front_hours": {"E1": 1.0}}}, "E1")


def test_e2_S_refuses_more_seeds_than_the_list(tmp_path, monkeypatch):
    most = len(phase35_prereg.seed_list())
    least = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    assert least == 2

    def e2(root, payload, derivation_value, **kwargs):
        paths = _inputs(root, monkeypatch, {_BUDGET: payload})
        return phase35_prereg.fill(
            "e2_S", input_records=paths, derivation=_measured(derivation_value, paths), **kwargs
        )

    with pytest.raises(SystemExit) as refused:  # D-06: a STOP, derived from the list's length
        e2(tmp_path / "d06", _budget_payload(e2_seed_count=most + 1), most + 1)
    assert "D-06" in str(refused.value) and "never extended" in str(refused.value)

    for count in (most, least):  # S is READ from the budget record's e2_seed_count
        assert e2(tmp_path / f"ok{count}", _budget_payload(e2_seed_count=count), count) == count
        assert e2(tmp_path / f"eq{count}", _budget_payload(e2_seed_count=count), count, s=count)
    with pytest.raises(SystemExit) as refused:  # a typed S that differs from the read one
        e2(tmp_path / "typed", _budget_payload(e2_seed_count=least), least, s=most)
    assert "read" in str(refused.value)
    for name, payload, value, kwargs in (
        ("below", _budget_payload(e2_seed_count=least - 1), least - 1, {}),
        ("bool", _budget_payload(e2_seed_count=True), True, {}),
        ("float", _budget_payload(e2_seed_count=float(least)), float(least), {}),
        ("s_float", _budget_payload(), least, {"s": float(least)}),
        ("derivation", _budget_payload(), most, {}),  # derivation value is not the read S
        ("noe2", _budget_payload(E2=0.0), least, {}),
    ):
        with pytest.raises(SystemExit):
            e2(tmp_path / name, payload, value, **kwargs)


def test_budget_record_is_revalidated_by_every_consumer(tmp_path, monkeypatch):
    """Review WR-03: a published budget record that breaks the budget rule funds nothing, and a
    malformed one is a _prove refusal, never a TypeError."""
    least = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    good = _budget_payload()
    assert phase35_prereg._budget_record({_BUDGET: good}) == good
    assert phase35_prereg._budget_front_hours({_BUDGET: good}, "E2") == good["front_hours"]["E2"]
    huge = {f: 1e6 for f in phase35_prereg.V6_MPS_FRONTS}
    for name, payload in (
        ("ceiling", {**good, "front_hours": huge, "total_hours": 8e6, "stop_line_hours": 9e9}),
        ("strings", {**good, "front_hours": {f: "5" for f in phase35_prereg.V6_MPS_FRONTS}}),
        ("total", {**good, "total_hours": good["total_hours"] + 1}),
        ("fronts", {**good, "front_hours": {"E2": 5.0}}),
        ("count", {k: v for k, v in good.items() if k != "e2_seed_count"}),
    ):
        with pytest.raises(SystemExit):
            phase35_prereg._budget_record({_BUDGET: payload})
        paths = _inputs(tmp_path / name, monkeypatch, {_BUDGET: payload})
        with pytest.raises(SystemExit):
            phase35_prereg.fill("e2_S", input_records=paths, derivation=_measured(least, paths))
        with pytest.raises(SystemExit):
            phase35_prereg.fill(
                "e1_checkpoint_grid",
                checkpoints=_CHECKPOINTS,
                input_records=paths,
                derivation=_measured(_CHECKPOINTS, paths),
            )


def _v4_recipe():
    import teach_persona  # torch at import: inside the e3 tests only

    return {
        "lr": teach_persona.LR,
        "steps": phase35_prereg.STEP_BUDGET,
        "batch": teach_persona.BATCH_SIZE,
    }


def _others(count, steps=None):
    """Recipes kept off the v4 recipe by batch 16."""
    steps = phase35_prereg.STEP_BUDGET if steps is None else steps
    lrs = (1e-4, 3e-4, 1e-3, 3e-3, 1e-2)
    return [{"lr": lr, "steps": steps, "batch": 16} for lr in lrs[:count]]


def _fill_grid(root, monkeypatch, recipes, seed, *, list_v4=False, v4_payload=None, fifth=None):
    """Plant the budget record (and the v4.0 record when the grid holds the v4 recipe or the case
    lists it), then fill e3_grid_subset. The v4.0 record is LISTED only when `list_v4`."""
    records = {_BUDGET: _budget_payload()}
    v4 = phase35_prereg._V4_CONTROL_RECORD
    if list_v4 or _v4_recipe() in [dict(r) for r in recipes]:
        records[v4] = _v4_bytes() if v4_payload is None else v4_payload
    _inputs(root, monkeypatch, records)
    paths = (_BUDGET, v4) if list_v4 else (_BUDGET,)
    return phase35_prereg.fill(
        "e3_grid_subset",
        recipes=tuple(recipes),
        seed=seed,
        input_records=paths,
        derivation=_measured(tuple(recipes), paths),
        fifth_recipe_derivation=fifth,
    )


def test_e3_grid_is_four_recipes_by_three_sigmas(tmp_path, monkeypatch):
    seeds = phase35_prereg.seed_list()
    record_seed = _v4_record()["seed"]
    grid = _fill_grid(tmp_path / "g4", monkeypatch, _others(4), seeds[0])
    sigmas = phase35_prereg.E3_SIGMAS
    assert len(grid["cells"]) == 12
    for i, recipe in enumerate(_others(4)):
        cells = grid["cells"][i * len(sigmas) : (i + 1) * len(sigmas)]
        assert tuple(c["sigma"] for c in cells) == sigmas
        assert all(dict(c["recipe"]) == recipe for c in cells)
    assert all(c["reuse"] is None for c in grid["cells"])
    assert phase35_prereg.E3_N == len(phase25_gate05.GATE05_SLOTS)
    assert all(c["n"] == phase35_prereg.E3_N for c in grid["cells"])
    assert grid["n"] == phase35_prereg.E3_N
    assert grid["unit"] == mitigation_unit.PRIVACY_UNIT

    fifth = _entry("the saved run fits", source=_BUDGET)
    for name, recipes, seed, kwargs in (
        ("three", _others(3), seeds[0], {}),
        ("five_no_v4", _others(5), seeds[0], {}),
        ("five_no_fifth", [_v4_recipe(), *_others(4)], record_seed, {"list_v4": True}),
        ("duplicate", [*_others(3), _others(1)[0]], seeds[0], {}),
        ("off_list_seed", _others(4), max(seeds) + 1, {}),
        ("float_seed", _others(4), float(seeds[0]), {}),  # review IN-01
        ("four_plus_fifth", _others(4), seeds[0], {"fifth": fifth}),
    ):
        with pytest.raises(SystemExit):
            _fill_grid(tmp_path / name, monkeypatch, recipes, seed, **kwargs)

    five = _fill_grid(
        tmp_path / "g5",
        monkeypatch,
        [_v4_recipe(), *_others(4)],
        record_seed,
        list_v4=True,
        fifth=fifth,
    )
    assert len(five["cells"]) == 15


def test_e3_grid_refuses_a_fifth_recipe_without_a_reused_control(tmp_path, monkeypatch):
    record_seed = _v4_record()["seed"]
    other_seed = next(s for s in phase35_prereg.seed_list() if s != record_seed)
    with pytest.raises(SystemExit):
        _fill_grid(
            tmp_path,
            monkeypatch,
            [_v4_recipe(), *_others(4)],
            other_seed,
            fifth=_entry("the saved run fits", source=_BUDGET),
        )


def test_e3_grid_reuses_the_v4_control_only_when_byte_identical_to_v5(tmp_path, monkeypatch):
    record = _v4_record()
    digest = record["adapter_sha256"]
    assert phase35_prereg._is_hex_digest(digest) is True
    for bad in (digest[:63], digest.upper(), None):
        assert phase35_prereg._is_hex_digest(bad) is False
    real_record, recorded = phase35_prereg._v4_control()  # the unpatched real tree
    assert real_record["seed"] == record["seed"]
    assert dict(recorded) == _v4_recipe()
    assert phase35_prereg._V4_CONTROL_RECORD == str(_v4_path().relative_to(_ROOT))

    recipes = [_v4_recipe(), *_others(3)]
    grid = _fill_grid(tmp_path / "reuse", monkeypatch, recipes, record["seed"], list_v4=True)
    reused = [c for c in grid["cells"] if c["reuse"] is not None]
    assert len(reused) == 1
    assert reused[0]["reuse"] == phase35_prereg._V4_CONTROL_RECORD
    assert dict(reused[0]["recipe"]) == _v4_recipe()
    assert reused[0]["sigma"] == phase35_prereg.E3_SIGMAS[0]

    with pytest.raises(SystemExit):  # the reuse happens, the record is not consumed
        _fill_grid(tmp_path / "unlisted", monkeypatch, recipes, record["seed"])
    with pytest.raises(SystemExit) as refused:  # a modified copy, still valid JSON
        _fill_grid(
            tmp_path / "modified",
            monkeypatch,
            recipes,
            record["seed"],
            list_v4=True,
            v4_payload=_v4_bytes() + b"\n",
        )
    assert "v5.0" in str(refused.value)

    other_seed = next(s for s in phase35_prereg.seed_list() if s != record["seed"])
    with pytest.raises(SystemExit):  # listed, but no reuse at another seed
        _fill_grid(tmp_path / "other_listed", monkeypatch, recipes, other_seed, list_v4=True)
    other = _fill_grid(tmp_path / "other", monkeypatch, recipes, other_seed)
    assert all(c["reuse"] is None for c in other["cells"])
    with pytest.raises(SystemExit):  # listed with no v4 recipe in the grid
        _fill_grid(tmp_path / "no_v4", monkeypatch, _others(4), record["seed"], list_v4=True)


def test_e3_grid_refuses_a_p22_crossing(tmp_path, monkeypatch):
    budget = phase35_prereg.STEP_BUDGET
    assert abs(phase35_prereg.p22_onset_sigma(budget) - 0.078902) < 1e-6  # 22-VERIFICATION :175
    assert phase35_prereg.ENTRIES["p22_two_oracle_budget"]["value"] == 1e-9
    line = (_ROOT / "tests/test_phase22_accountant.py").read_text(encoding="utf-8").splitlines()
    assert "1e-9 * abs(b)" in line[535]
    assert phase35_prereg._p22_breached(0.05, budget) is True
    assert phase35_prereg._p22_breached(0.3, budget) is False

    seed = phase35_prereg.seed_list()[0]
    with pytest.raises(SystemExit) as refused:
        _fill_grid(tmp_path / "t9000", monkeypatch, [*_others(3), *_others(1, 9000)], seed)
    assert "RECIPE-04" in str(refused.value)
    grid = _fill_grid(tmp_path / "t400", monkeypatch, [*_others(3), *_others(1, 400)], seed)
    assert set(grid["p22_onset_sigma"]) == {budget, 400}

    entry = phase35_prereg.ENTRIES["p22_two_oracle_budget"]
    monkeypatch.setattr(
        phase35_prereg,
        "ENTRIES",
        {**phase35_prereg.ENTRIES, "p22_two_oracle_budget": {**entry, "value": 1e-6}},
    )
    assert phase35_prereg.p22_onset_sigma(budget) < 0.07  # the rule reads the entry


def _grid_keys(grid):
    """The grid recipe keys (lr, steps, batch, seed) in grid order: the threshold's derivation
    value (review WR-06)."""
    return tuple(
        dict.fromkeys(
            (c["recipe"]["lr"], c["recipe"]["steps"], c["recipe"]["batch"], c["seed"])
            for c in grid["cells"]
        )
    )


def _fill_threshold(root, monkeypatch, grid, controls, value=None):
    paths = _inputs(root, monkeypatch, controls)
    return phase35_prereg.fill(
        "e3_recall_threshold",
        grid=grid,
        input_records=paths,
        derivation=_measured(_grid_keys(grid) if value is None else value, paths),
    )


def test_e3_recall_threshold_keys_each_control_by_its_recorded_recipe(tmp_path, monkeypatch):
    f_y = phase35_prereg.F_Y
    seed = phase35_prereg.seed_list()[0]
    recipes = _others(4)
    grid = _fill_grid(tmp_path, monkeypatch, recipes, seed)

    def key(recipe, s=seed):
        return (recipe["lr"], recipe["steps"], recipe["batch"], s)

    order = (2, 0, 3, 1)  # NOT the grid's order: a positional pairing would mismatch
    controls = {
        f"results/phase42_control_{tag}.json": _control_payload(
            recipes[i], seed, (0, 48) if i == 3 else (40, 48), (20, 40)
        )
        for tag, i in zip("abcd", order, strict=True)
    }
    result = _fill_threshold(tmp_path, monkeypatch, grid, controls)
    assert set(result) == {key(r) for r in recipes}
    for tag, i in zip("abcd", order, strict=True):
        if i == 3:
            assert result[key(recipes[i])] == phase29_prereg.REFUSED
        else:
            assert dict(result[key(recipes[i])]) == {
                "control": f"results/phase42_control_{tag}.json",
                "taught": f_y * 40 / 48,
                "heldout": f_y * 20 / 40,
            }

    stranger = {"lr": 5e-2, "steps": phase35_prereg.STEP_BUDGET, "batch": 16}
    good = [_control_payload(r, seed, (40, 48), (20, 40)) for r in recipes]
    v4 = phase35_prereg._V4_CONTROL_RECORD
    for name, payloads, extra in (
        ("stranger", [*good[:3], _control_payload(stranger, seed, (40, 48), (20, 40))], {}),
        ("twice", [*good, good[0]], {}),
        ("three", good[:3], {}),
        ("noised", [*good[:3], {**good[3], "sigma": 0.5}], {}),
        ("v4_listed", good, {v4: _v4_bytes()}),
    ):
        planted = {
            f"results/phase42_control_{name}_{i}.json": p for i, p in enumerate(payloads)
        } | extra
        with pytest.raises(SystemExit):
            _fill_threshold(tmp_path / name, monkeypatch, grid, planted)

    record = _v4_record()
    reuse_grid = _fill_grid(
        tmp_path / "reuse", monkeypatch, [_v4_recipe(), *recipes[:3]], record["seed"], list_v4=True
    )
    third = {
        f"results/phase42_control_r{i}.json": _control_payload(
            r, record["seed"], (40, 48), (20, 40)
        )
        for i, r in enumerate(recipes[:3])
    }
    reused = _fill_threshold(
        tmp_path / "reuse", monkeypatch, reuse_grid, {**third, v4: _v4_bytes()}
    )
    taught, heldout = record["taught_recall"], record["heldout_recall"]
    assert dict(reused[key(_v4_recipe(), record["seed"])]) == {
        "control": v4,
        "taught": f_y * taught["numerator"] / taught["denominator"],
        "heldout": f_y * heldout["numerator"] / heldout["denominator"],
    }
    rerun = {
        **third,
        "results/phase42_control_v4.json": _control_payload(
            _v4_recipe(), record["seed"], (40, 48), (20, 40)
        ),
    }
    with pytest.raises(SystemExit):  # the reused control is the one consumed
        _fill_threshold(tmp_path / "rerun", monkeypatch, reuse_grid, rerun)


def test_e4_parameters_gate_on_the_reproduction(tmp_path, monkeypatch):
    paths = _inputs(tmp_path, monkeypatch, {"results/phase38_minting.json": {"m": 16}})
    delta = phase35_prereg.DELTA

    def e4(m, k_plus, k_minus, inclusion=0.5, beta=0.05, value=None):
        chosen = {"m": m, "k_plus": k_plus, "k_minus": k_minus} if value is None else value
        return phase35_prereg.fill(
            "e4_parameters",
            m=m,
            inclusion_probability=inclusion,
            k_plus=k_plus,
            k_minus=k_minus,
            beta=beta,
            input_records=paths,
            derivation=_measured(chosen, paths),
        )

    assert phase35_prereg.ENTRIES["e4_inclusion_probability"]["value"] == 0.5
    small = e4(16, 8, 8)
    assert small["ceiling"] == phase35_prereg.eps_lower_one_run(16, 16, 16, delta, 0.05)
    assert small["runs"] is False
    one_sided = e4(16, 4, 0)  # zero guesses on one side is a well-defined count (WR-01)
    assert one_sided["ceiling"] == phase35_prereg.eps_lower_one_run(16, 4, 4, delta, 0.05)
    large = e4(184, 92, 92)
    assert large["runs"] is True
    assert large["ceiling"] > phase35_prereg.audit02_cut()
    for args, kwargs in (
        ((16, 8, 8), {"inclusion": 0.25}),
        ((16, 9, 8), {}),
        ((16, 8, 8), {"beta": 0.1}),
        ((16, 8, 8), {"beta": True}),
        ((16, 8, 8), {"beta": math.nan}),
        ((16, -1, 5), {}),  # review WR-01: a negative count, r = 4
        ((16, 5, -1), {}),
        ((16, True, 5), {}),
        ((16, 5, False), {}),
        ((0, 0, 0), {}),
        ((-4, 1, 1), {}),
        ((True, 1, 0), {}),
        ((16, 0, 0), {}),  # r = 0: no guess
        ((16, 8, 8), {"value": 16}),  # review WR-06: the derivation names m alone
    ):
        with pytest.raises(SystemExit):
            e4(*args, **kwargs)
    monkeypatch.setattr(phase35_prereg, "one_run_reproduction_holds", lambda: False)
    with pytest.raises(SystemExit) as refused:
        e4(16, 8, 8)
    assert "D-11" in str(refused.value)


def test_e4_beta_is_the_one_sided_95_level_of_phase26_and_both_pins():
    entry = phase35_prereg.ENTRIES["e4_beta"]
    assert entry["kind"] == "preference"
    assert set(entry) == {"value", "derivation", "kind", "source"}
    z = erasure_gate._Z_ONE_SIDED_95
    assert phase26_prereg.Z is z
    assert abs(0.5 * math.erfc(z / math.sqrt(2)) - entry["value"]) < 1e-12
    for pin in phase35_prereg.ONE_RUN_PUBLISHED.values():
        assert pin["inputs"][4] == entry["value"]


_CHECKPOINTS = (8, 16, 32, 64, 78)  # ablation prefix counts, not K


def _fill_checkpoint_grid(root, monkeypatch):
    paths = _inputs(root, monkeypatch, {_BUDGET: _budget_payload()})
    grid = phase35_prereg.fill(
        "e1_checkpoint_grid",
        checkpoints=_CHECKPOINTS,
        input_records=paths,
        derivation=_measured(_CHECKPOINTS, paths),
    )
    return grid, paths


def test_slot_e1_rules(tmp_path, monkeypatch):
    grid, paths = _fill_checkpoint_grid(tmp_path / "grid", monkeypatch)
    assert grid["checkpoints"] == _CHECKPOINTS
    assert grid["read_k"] == mitigation_budget.CURVE_K
    assert grid["confirm_k"] == mitigation_budget.FULL_FIDELITY_K
    assert grid["not_reached"] == phase35_prereg.NOT_REACHED
    with pytest.raises(SystemExit):
        phase35_prereg.fill(
            "e1_checkpoint_grid",
            checkpoints=(8, 8, 16),
            input_records=paths,
            derivation=_measured((8, 8, 16), paths),
        )

    assert phase35_prereg.fill("e1_alternative_ordering", ordering=_entry("x")) == _entry("x")


# ERASE-09's band, READ from the band-input and noise-floor records (review CR-01, Rafael
# 2026-10-01: the floors pattern). Records are planted under tmp_path only.

_NOISE = "results/phase40_noise_floor.json"
_BAND_ORDERING = "greedy_loo"


def _band_record(seed, control_gap, ordering=_BAND_ORDERING):
    return {"seed": seed, "ordering": ordering, "control_gap": control_gap}


def _fill_band(root, monkeypatch, band_inputs, band_records, *, consumed=None, value=None):
    records = {f"results/phase41_band_inputs_{i}.json": p for i, p in enumerate(band_records)}
    planted = {**records, _NOISE: {"gap_noise_floor": 0.1}}
    _inputs(root, monkeypatch, planted)
    paths = tuple(planted) if consumed is None else consumed
    return phase35_prereg.fill(
        "e1_condition_c_band_inputs",
        band_inputs=band_inputs,
        input_records=paths,
        derivation=_measured(tuple(band_inputs) if value is None else value, paths),
    )


def test_band_inputs_are_read_from_their_records(tmp_path, monkeypatch):
    teaching = phase35_prereg.e1_teaching_seeds()
    gaps = dict(zip(teaching, (1.0, 1.5), strict=True))
    keys = [(seed, _BAND_ORDERING) for seed in teaching]
    records = [_band_record(seed, gaps[seed]) for seed in teaching]
    out = _fill_band(tmp_path / "ok", monkeypatch, dict.fromkeys(keys), records)
    for seed, ordering in keys:
        assert out[(seed, ordering)] == mitigation_gate.dialogue_gap_band(
            control_gap=gaps[seed], gap_noise_floor=0.1
        )
    with pytest.raises(TypeError):
        out[keys[0]] = None
    same = {key: {"control_gap": gaps[key[0]], "gap_noise_floor": 0.1} for key in keys}
    assert _fill_band(tmp_path / "same", monkeypatch, same, records) == out

    band_paths = tuple(f"results/phase41_band_inputs_{i}.json" for i in range(len(records)))
    off_seed = next(s for s in phase35_prereg.seed_list() if s not in teaching)
    for name, band, planted, kwargs, expected in (
        ("no_noise", dict.fromkeys(keys), records, {"consumed": band_paths}, "not consumed"),
        ("no_band", dict.fromkeys(keys), records, {"consumed": (_NOISE,)}, "not consumed"),
        (
            "typed",
            {
                **dict.fromkeys(keys),
                keys[0]: {"control_gap": gaps[teaching[0]], "gap_noise_floor": 99.0},
            },
            records,
            {},
            "they are read",
        ),
        ("duplicate", dict.fromkeys(keys), [*records, records[0]], {}, "two band-input records"),
        (
            "orphan",
            dict.fromkeys(keys),
            [*records, _band_record(teaching[0], 1.0, "other")],
            {},
            "serves no key",
        ),
        ("missing", dict.fromkeys(keys), records[:1], {}, "without a band-input record"),
        ("one_seed", dict.fromkeys(keys[:1]), records[:1], {}, "every e1 teaching seed"),
        (
            "off_seed",
            {**dict.fromkeys(keys), (off_seed, _BAND_ORDERING): None},
            records,
            {},
            "seed",
        ),
        ("float_seed", {(float(teaching[0]), _BAND_ORDERING): None}, records, {}, "int"),
        ("value", dict.fromkeys(keys), records, {"value": dict.fromkeys(keys)}, "chosen value"),
    ):
        with pytest.raises(SystemExit) as refused:
            _fill_band(tmp_path / name, monkeypatch, band, planted, **kwargs)
        assert expected in str(refused.value), (name, str(refused.value))


# ERASE-07's NOT_REACHED outcome (Rafael's review, 2026-10-01).


def _readings(*zero_at, confirmed=()):
    """A CURVE_K read per grid checkpoint up to the last one named: zero at `zero_at`, its
    FULL_FIDELITY_K confirmation zero exactly at `confirmed`."""
    last = max((*zero_at, *confirmed), default=_CHECKPOINTS[-1])
    return {
        c: {
            "curve_k_zero": c in zero_at,
            "full_fidelity_k_zero": (c in confirmed) if c in zero_at else None,
        }
        for c in _CHECKPOINTS
        if c <= last
    }


def test_e1_stop_not_reached_is_neither_pass_nor_fail(tmp_path, monkeypatch):
    grid, _ = _fill_checkpoint_grid(tmp_path, monkeypatch)
    # One checkpoint reads zero at CURVE_K but its FULL_FIDELITY_K confirmation is non-zero.
    readings = {c: {"curve_k_zero": False, "full_fidelity_k_zero": None} for c in _CHECKPOINTS}
    readings[_CHECKPOINTS[1]] = {"curve_k_zero": True, "full_fidelity_k_zero": False}
    out = phase35_prereg.e1_stop(grid=grid, readings=readings)
    assert out["stop"] == phase35_prereg.NOT_REACHED == grid["not_reached"]
    assert out["judged"] is False
    passed, failed = mitigation_gate.V4_VERDICTS[:2]
    assert (passed, failed) == ("PASS", "FAIL")
    assert out["stop"] not in (passed, failed)
    for domain in (
        erasure_gate.VERDICTS,
        mitigation_gate.V4_VERDICTS,
        phase29_prereg.VERDICTS,
        (phase29_prereg.REFUSED,),
    ):
        assert phase35_prereg.NOT_REACHED not in domain
    with pytest.raises(TypeError):
        out["judged"] = True


def test_e1_stop_at_the_first_confirmed_zero(tmp_path, monkeypatch):
    grid, _ = _fill_checkpoint_grid(tmp_path, monkeypatch)
    first, second, third = _CHECKPOINTS[:3]
    stop = phase35_prereg.e1_stop(grid=grid, readings=_readings(third, confirmed=(third,)))
    assert dict(stop) == {"stop": third, "judged": True}
    # A non-zero confirmation continues to the next checkpoint.
    stop = phase35_prereg.e1_stop(grid=grid, readings=_readings(first, second, confirmed=(second,)))
    assert dict(stop) == {"stop": second, "judged": True}

    good = _readings(second, confirmed=(second,))
    missing = {k: v for k, v in good.items() if k != first}
    confirm_without_zero = {**good, first: {"curve_k_zero": False, "full_fidelity_k_zero": False}}
    zero_without_confirm = {**good, first: {"curve_k_zero": True, "full_fidelity_k_zero": None}}
    outside = {**good, first + 1: {"curve_k_zero": False, "full_fidelity_k_zero": None}}
    past_stop = {**good, third: {"curve_k_zero": False, "full_fidelity_k_zero": None}}
    for bad in (missing, confirm_without_zero, zero_without_confirm, outside, past_stop):
        with pytest.raises(SystemExit):
            phase35_prereg.e1_stop(grid=grid, readings=bad)
    with pytest.raises(SystemExit):
        phase35_prereg.e1_stop(grid={"checkpoints": _CHECKPOINTS}, readings=good)


# ERASE-06's floors, COMPUTED from the calibration record of the cell's (ordering, seed) (Rafael's
# reviews and his option-A ruling, 2026-10-01). Records are planted under tmp_path only.

_CAL_ARM = "results/phase19_arm_cal-erased.json"
_CAL_CORPUS = "results/phase19_calibration_corpus.json"
_CORRECTION = "results/phase19_calibration_correction.json"
_ORDERING = "greedy_loo"
_FIXTURE = "synthetic test fixture — not a reading, never cite as a measurement"


def _cal_draws():
    return json.loads((_ROOT / _CAL_ARM).read_text(encoding="utf-8"))["draws"]


def _calibration_payload(cal_key, draws, family="A2", corpus=_CAL_CORPUS):
    """A calibration record keyed by (ordering[, seed]); no target field."""
    return {
        "ordering": cal_key[0],
        "seed": cal_key[1] if len(cal_key) == 2 else None,
        "family": family,
        "corpus": corpus,
        "draws": draws,
    }


def _fill_floors(root, monkeypatch, floors, payloads, *, corpora=None, consumed=None, named=None):
    """Plant `payloads` and `corpora` ({relpath: bytes}, default the real corpus) under `root`.
    input_records is `consumed` (default every planted path); the derivation's source names
    `named` (default input_records)."""
    records = {f"results/phase41_calibration_{i}.json": p for i, p in enumerate(payloads)}
    if corpora is None:
        corpora = {_CAL_CORPUS: (_ROOT / _CAL_CORPUS).read_bytes()}
    _inputs(root, monkeypatch, {**records, **corpora})
    paths = (*records, *corpora) if consumed is None else consumed
    return phase35_prereg.fill(
        "e1_condition_a_floors",
        floors=floors,
        input_records=paths,
        derivation=_measured(tuple(floors), paths if named is None else named),
    )


def _target_keys(*cal_key):
    return [(target, *(cal_key or (_ORDERING,))) for target in phase35_prereg.e1_targets()]


def test_e1_floors_declare_phase19_calibration_corpus():
    import phase19_erasure  # torch at import: inside the test only

    declared = phase35_prereg.SLOTS["e1_condition_a_floors"]["input_records"]
    corpus = phase19_erasure.CALIBRATION_CORPUS_PATH.relative_to(_ROOT).as_posix()
    assert declared == ("results/phase41_calibration_*.json", corpus)
    assert corpus == _CAL_CORPUS


def test_e1_floors_reproduce_phase19_corrected_floor(tmp_path, monkeypatch):
    """Positive control: ONE calibration record (the real cal-erased draws) serves the FOUR targets
    and gives Phase 19's CORRECTED floor (0/23, reachability-min), never the defect-B floor."""
    import phase19_erasure  # torch at import: inside the test only

    keys = _target_keys()
    assert len(keys) == len(phase35_prereg.e1_targets())
    out = _fill_floors(
        tmp_path,
        monkeypatch,
        dict.fromkeys(keys),
        [_calibration_payload((_ORDERING,), _cal_draws())],
    )
    correction = json.loads((_ROOT / _CORRECTION).read_text(encoding="utf-8"))
    defect_b = phase19_erasure.lock_erasure_floor(phase19_erasure._calibration_rate())
    assert defect_b == correction["pin_internal_target_floor"]
    assert set(out) == set(keys)
    for key in keys:
        row = out[key]
        assert row["floor"] == phase19_floor.TARGET_FLOOR
        assert row["floor_branch"] == phase19_floor.FLOOR_BRANCH
        assert row["calibration_rate"] == 0.0
        assert row["calibration_successes"] == correction["calibration_successes"]
        assert row["calibration_questions"] == correction["calibration_questions"]
        assert row["calibration_record"] == "results/phase41_calibration_0.json"
        assert row["floor"] != defect_b
    with pytest.raises(TypeError):
        out[keys[0]]["floor"] = 0.0


def test_e1_floors_refuse_a_typed_floor_or_a_mismatched_record(tmp_path, monkeypatch):
    targets = phase35_prereg.e1_targets()
    keys = _target_keys()
    draws = _cal_draws()
    one = [_calibration_payload((_ORDERING,), draws)]
    floor = phase19_floor.TARGET_FLOOR

    # A supplied value equal to the computed floor is accepted.
    out = _fill_floors(
        tmp_path / "equal", monkeypatch, {**dict.fromkeys(keys), keys[0]: floor}, one
    )
    assert out[keys[0]]["floor"] == floor
    # One record per (ordering, seed): 4 targets x 2 seeds -> 8 rows from 2 records.
    seeds = phase35_prereg.e1_teaching_seeds()
    seeded = [key for seed in seeds for key in _target_keys(_ORDERING, seed)]
    out = _fill_floors(
        tmp_path / "seeded",
        monkeypatch,
        dict.fromkeys(seeded),
        [_calibration_payload((_ORDERING, seed), draws) for seed in seeds],
    )
    assert set(out) == set(seeded)
    for key in seeded:
        index = seeds.index(key[2])
        assert out[key]["calibration_record"] == f"results/phase41_calibration_{index}.json"

    with pytest.raises(SystemExit) as refused:
        _fill_floors(
            tmp_path / "typed", monkeypatch, {**dict.fromkeys(keys), keys[0]: floor * 2}, one
        )
    assert "computed" in str(refused.value)

    other = json.loads((_ROOT / _CAL_CORPUS).read_text(encoding="utf-8"))
    other["fact_id"] = "cal_planted_other"
    for name, floors, planted, expected in (
        ("missing", dict.fromkeys(_target_keys(_ORDERING, seeds[0])), one, "without a"),
        ("duplicate", dict.fromkeys(keys), [*one, *one], "two calibration records"),
        (
            "orphan",
            dict.fromkeys(keys),
            [*one, _calibration_payload(("other",), draws)],
            "serving no floor",
        ),
        ("target", dict.fromkeys(keys), [{**one[0], "target": targets[0]}], "target field"),
        (  # review WR-02: each ordering covers only some targets
            "per_cell",
            dict.fromkeys(
                [(t, _ORDERING) for t in targets[:2]] + [(t, "alt") for t in targets[2:]]
            ),
            [*one, _calibration_payload(("alt",), draws)],
            "every e1 target",
        ),
        (  # review WR-02: one ordering with seeded and unseeded keys
            "arity",
            dict.fromkeys([*keys, *_target_keys(_ORDERING, seeds[0])]),
            [*one, _calibration_payload((_ORDERING, seeds[0]), draws)],
            "mixes seeded and unseeded",
        ),
        (  # review IN-01: a float seed equal to a teaching seed
            "float_seed",
            dict.fromkeys(_target_keys(_ORDERING, float(seeds[0]))),
            [_calibration_payload((_ORDERING, seeds[0]), draws)],
            "int",
        ),
        ("family", dict.fromkeys(keys), [_calibration_payload((_ORDERING,), draws, "A0")], "A2"),
    ):
        with pytest.raises(SystemExit) as refused:
            _fill_floors(tmp_path / name, monkeypatch, floors, planted)
        assert expected in str(refused.value), (name, str(refused.value))
    with pytest.raises(SystemExit) as refused:
        _fill_floors(
            tmp_path / "fact",
            monkeypatch,
            dict.fromkeys(keys),
            one,
            corpora={_CAL_CORPUS: json.dumps(other).encode("utf-8")},
        )
    assert "calibration fact" in str(refused.value)


def test_e1_floors_corpus_is_a_declared_consumed_input(tmp_path, monkeypatch):
    """Planted RED: the corpus a calibration record names must be consumed through the slot's
    declared inputs and named in the derivation's source."""
    keys = dict.fromkeys(_target_keys())
    record = "results/phase41_calibration_0.json"
    one = [_calibration_payload((_ORDERING,), _cal_draws())]
    assert _fill_floors(tmp_path / "ok", monkeypatch, keys, one)

    with pytest.raises(SystemExit) as refused:  # the record's corpus is not in input_records
        _fill_floors(tmp_path / "unconsumed", monkeypatch, keys, one, consumed=(record,))
    assert "was not consumed" in str(refused.value)
    with pytest.raises(SystemExit) as refused:  # the declared corpus consumed, another one named
        _fill_floors(
            tmp_path / "other_named",
            monkeypatch,
            keys,
            [_calibration_payload((_ORDERING,), _cal_draws(), corpus="results/phase19_b.json")],
        )
    assert "not a consumed input" in str(refused.value)
    with pytest.raises(SystemExit) as refused:  # the derivation's source omits the corpus
        _fill_floors(tmp_path / "unnamed", monkeypatch, keys, one, named=(record,))
    assert "source omits" in str(refused.value)
    stray = "results/phase19_other_corpus.json"
    with pytest.raises(SystemExit) as refused:  # a corpus outside the declared pattern
        _fill_floors(
            tmp_path / "stray",
            monkeypatch,
            keys,
            [_calibration_payload((_ORDERING,), _cal_draws(), corpus=stray)],
            corpora={stray: (_ROOT / _CAL_CORPUS).read_bytes()},
        )
    assert "not a declared input" in str(refused.value)


def _synthetic_fixture_draws(answerable):
    """SYNTHETIC TEST FIXTURE: not a reading, never cite as a measurement. The real cal-erased
    draws with the first ``answerable`` questions given one completion naming the calibration
    fact's value, so the REAL scorer (per_fact_rows -> score_records) counts them answerable."""
    import phase19_erasure  # torch at import: inside the test only

    value = phase19_erasure.select_calibration_fact().value
    draws = _cal_draws()
    for draw in draws[:answerable]:
        draw["completions"][0] = " " + value
    return draws


@pytest.mark.parametrize("branch", ("discount", "ceiling"))
def test_e1_floors_synthetic_fixture_cover_discount_and_ceiling(tmp_path, monkeypatch, branch):
    """SYNTHETIC TEST FIXTURE: not a reading, never cite as a measurement. Real draws only exercise
    reachability-min; this planted record covers the other two branches through the real route.
    The expected floor is lock_erasure_floor / floor_branch of the rate this test planted."""
    import phase19_erasure  # torch at import: inside the test only

    questions = len(_cal_draws())  # one draw record per question
    lo, hi = phase19_erasure.ERASURE_FLOOR_MIN, phase19_erasure.FLOOR_CEILING

    def lands(k):
        if phase19_erasure.floor_branch(k / questions) != branch:
            return False
        # discount: the discounted floor strictly between the clamp and the ceiling.
        return branch == "ceiling" or lo < phase19_erasure.lock_erasure_floor(k / questions) < hi

    answerable = next(k for k in range(questions + 1) if lands(k))
    keys = _target_keys()
    payload = {
        **_calibration_payload((_ORDERING,), _synthetic_fixture_draws(answerable)),
        "fixture": _FIXTURE,
    }
    out = _fill_floors(tmp_path, monkeypatch, dict.fromkeys(keys), [payload])
    rate = answerable / questions
    for key in keys:
        row = out[key]
        assert row["calibration_successes"] == answerable
        assert row["calibration_questions"] == questions
        assert row["calibration_rate"] == rate
        assert row["floor"] == phase19_erasure.lock_erasure_floor(rate)
        assert row["floor_branch"] == phase19_erasure.floor_branch(rate) == branch
    if branch == "discount":
        assert lo < out[keys[0]]["floor"] < hi
    else:
        assert out[keys[0]]["floor"] == hi


def _calibration_rate_references(source):
    rule = _function(ast.parse(source), "_rule_e1_condition_a_floors")
    return [
        node.lineno
        for node in ast.walk(rule)
        if (isinstance(node, ast.Name) and node.id == "_calibration_rate")
        or (isinstance(node, ast.Attribute) and node.attr == "_calibration_rate")
    ]


def test_e1_floors_never_reference_the_defect_b_rate(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    assert _calibration_rate_references(source) == []

    rule = _function(ast.parse(source), "_rule_e1_condition_a_floors")
    anchor = _import_of(ast.walk(rule), "phase19_erasure")
    line = " " * anchor.col_offset + "_ = phase19_erasure._calibration_rate()"
    planted = _replace_lines(source, anchor.end_lineno + 1, anchor.end_lineno, [line])
    ast.parse(planted)
    assert _calibration_rate_references(_planted(tmp_path, source, planted, "defect_b.py"))
    assert real.read_bytes() == before


def test_e1_targets_pool_to_the_27_question_target_denominator():
    import phase18_extraction  # torch at import: inside the test only
    import phase19_erasure  # same

    draws = json.loads((_ROOT / "results/phase18_arm_adapter-on.json").read_text(encoding="utf-8"))[
        "draws"
    ]
    fixture = json.loads((_ROOT / "results/phase16_recall_sample.json").read_text(encoding="utf-8"))
    assert phase19_erasure.N_TARGET_QUESTIONS == sum(
        phase19_erasure.TARGET_QUESTION_COUNTS.values()
    )
    assert phase19_erasure.ERASURE_FLOOR_MIN == erasure_gate.wilson_upper_bound(
        0, phase19_erasure.N_TARGET_QUESTIONS
    )
    for target in phase35_prereg.e1_targets():
        fact_ids = {draw["fact_id"] for draw in draws if draw["slot"] == target}
        assert len(fact_ids) == 1, (target, fact_ids)
        counts = phase19_erasure.target_question_counts(
            fixture, fact_ids.pop(), phase18_extraction.CORPUS_TIERS
        )
        assert counts["pooled"] == phase19_erasure.N_TARGET_QUESTIONS, (target, counts)


def test_slot_e1_condition_b_margin_is_the_core_read():
    assert phase35_prereg.fill("e1_condition_b_margin") == phase35_prereg.e1_condition_b_margin()
    rule = phase35_prereg.SLOTS["e1_condition_b_margin"]["rule"]
    assert not inspect.signature(rule).parameters


def test_slot_budget_halts_above_the_ceiling(tmp_path, monkeypatch):
    paths = _inputs(tmp_path, monkeypatch, {"results/phase36_probe_a.json": {}})
    fronts = {f: 5.0 for f in phase35_prereg.V6_MPS_FRONTS}

    least = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]

    def budget(front_hours, stop_line_hours, count=least, value=None):
        chosen = {
            "front_hours": dict(front_hours),
            "stop_line_hours": stop_line_hours,
            "e2_seed_count": count,
        }
        return phase35_prereg.fill(
            "v6_budget_and_stop_line",
            front_hours=front_hours,
            stop_line_hours=stop_line_hours,
            e2_seed_count=count,
            input_records=paths,
            derivation=_measured(chosen if value is None else value, paths),
        )

    out = budget(fronts, 60.0)
    assert out["total_hours"] == 40.0 and out["stop_line_hours"] == 60.0
    assert out["e2_seed_count"] == least
    assert dict(out["front_hours"]) == fronts
    most = len(phase35_prereg.seed_list())
    for kwargs in ({"value": fronts}, {"count": most + 1}, {"count": least - 1}):
        with pytest.raises(SystemExit):  # derivation of front_hours only; D-06; below the floor
            budget(fronts, 60.0, **kwargs)
    missing = {f: h for f, h in fronts.items() if f != "E6"}
    for front_hours, stop in ((missing, 60.0), (fronts, 30.0)):
        with pytest.raises(SystemExit):
            budget(front_hours, stop)
    with pytest.raises(SystemExit) as refused:
        budget(fronts, 91.0)
    assert "HALT" in str(refused.value)


def test_slot_e5_e6_set_sizes_and_entry_subset(tmp_path, monkeypatch):
    minting = _inputs(tmp_path / "m", monkeypatch, {"results/phase38_minting.json": {}})
    most = phase35_prereg.ENTRIES["e5_max_set_size"]["value"]
    assert most == 512

    def sizes(set_sizes):
        return phase35_prereg.fill(
            "e5_set_sizes",
            set_sizes=set_sizes,
            input_records=minting,
            derivation=_measured(set_sizes, minting),
        )

    assert dict(sizes({"a": 1, "b": most})) == {"a": 1, "b": most}
    for bad in ({"a": most + 1}, {"a": 0}):
        with pytest.raises(SystemExit):
            sizes(bad)

    probe = _inputs(tmp_path / "p", monkeypatch, {"results/phase36_probe_a.json": {}})
    size = len(phase35_prereg.a2_corpus_entries())

    def subset(indices):
        return phase35_prereg.fill(
            "e6_entry_subset",
            entry_indices=indices,
            input_records=probe,
            derivation=_measured(indices, probe),
        )

    assert subset((0, size - 1)) == (0, size - 1)
    for bad in ((size,), (1, 0)):
        with pytest.raises(SystemExit):
            subset(bad)


_DESIGN_SLOTS = {
    "r1b_tolerance_and_replicated": lambda e: {"tolerance": {"k": 0}, "replicated_definition": e},
    "e5_minting_rule": lambda e: {"minting_rule": e},
    "e2_noise_floor_estimator": lambda e: {"estimator": e},
    "e5_rank_moves_and_generation_collapses": lambda e: {"moves": e, "collapses": e},
    "e6_decomposition_rule": lambda e: {"decomposition": e},
}


def test_design_slots_return_read_only_copies():
    """Review WR-04: a design rule's result neither follows the caller's later edits nor takes an
    assignment, and a mapping value is frozen too."""
    for slot, kwargs in _DESIGN_SLOTS.items():
        entry = _entry({"rule": "text"})
        out = phase35_prereg.fill(slot, **kwargs(entry))
        entry["proposer"] = "planted"
        entry["value"]["rule"] = "edited"
        frozen = [out[k] for k in ("replicated_definition", "moves", "collapses") if k in out]
        for got in frozen or [out]:
            assert "proposer" not in got and got["value"]["rule"] == "text", slot
            with pytest.raises(TypeError):
                got["proposer"] = "planted"
            with pytest.raises(TypeError):
                got["value"]["rule"] = "edited"
    ordering = _entry("ordering text")
    out = phase35_prereg.fill("e1_alternative_ordering", ordering=ordering)
    ordering["value"] = ""
    assert out["value"] == "ordering text"
    with pytest.raises(TypeError):
        out["value"] = ""
    assert phase35_prereg._frozen_entry("x", _entry(1))["value"] == 1


def test_every_declared_input_pattern_is_consumed_unless_optional(tmp_path, monkeypatch):
    """The root cause CR-01 names: a declared pattern no consumed path matches is refused unless
    the rule passes it as optional (only e3's reused v4.0 control is)."""
    band = "results/phase41_band_inputs_a.json"
    paths = _inputs(tmp_path, monkeypatch, {band: {}, _NOISE: {}})
    consume = phase35_prereg._consume_inputs
    slot = "e1_condition_c_band_inputs"
    assert set(consume(slot, 1, paths, _measured(1, paths))) == set(paths)
    with pytest.raises(SystemExit) as refused:  # planted RED: the Phase 40 record left out
        consume(slot, 1, (band,), _measured(1, (band,)))
    assert "was not consumed" in str(refused.value)
    assert consume(slot, 1, (band,), _measured(1, (band,)), optional=(_NOISE,))
    with pytest.raises(SystemExit):  # optional must name a declared pattern
        consume(slot, 1, paths, _measured(1, paths), optional=("results/phase40_other.json",))
    for name in ("e3_grid_subset", "e3_recall_threshold"):
        source = inspect.getsource(phase35_prereg.SLOTS[name]["rule"])
        assert "optional=(_V4_CONTROL_RECORD,)" in source, name
    rules = [
        n
        for n in ast.parse((_ROOT / PREREG).read_text(encoding="utf-8")).body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_rule_")
    ]
    optional = {
        rule.name
        for rule in rules
        for node in ast.walk(rule)
        if isinstance(node, ast.keyword) and node.arg == "optional"
    }
    assert optional == {"_rule_e3_grid_subset", "_rule_e3_recall_threshold"}


def test_grids_must_be_fill_results(tmp_path, monkeypatch):
    """Review IN-04: e1_stop and e3_recall_threshold refuse a hand-built grid with the right
    keys."""
    grid, _ = _fill_checkpoint_grid(tmp_path / "e1", monkeypatch)
    assert isinstance(grid, phase35_prereg._Filled)
    readings = _readings(_CHECKPOINTS[0], confirmed=(_CHECKPOINTS[0],))
    assert phase35_prereg.e1_stop(grid=grid, readings=readings)["judged"] is True
    with pytest.raises(SystemExit):
        phase35_prereg.e1_stop(grid=dict(grid), readings=readings)

    seed = phase35_prereg.seed_list()[0]
    recipes = _others(4)
    e3 = _fill_grid(tmp_path / "e3", monkeypatch, recipes, seed)
    controls = {
        f"results/phase42_control_{i}.json": _control_payload(r, seed, (40, 48), (20, 40))
        for i, r in enumerate(recipes)
    }
    assert len(_fill_threshold(tmp_path / "real", monkeypatch, e3, controls)) == 4
    with pytest.raises(SystemExit):
        _fill_threshold(tmp_path / "hand", monkeypatch, dict(e3), controls)
    with pytest.raises(SystemExit):  # review WR-06: the derivation value is the grid's keys
        _fill_threshold(tmp_path / "paths", monkeypatch, e3, controls, value=tuple(controls))


@pytest.mark.parametrize("slot", sorted(_DESIGN_SLOTS))
def test_slot_design_entries_refuse_a_proposer(slot):
    kwargs = _DESIGN_SLOTS[slot]
    assert phase35_prereg.fill(slot, **kwargs(_entry("rule text")))
    with pytest.raises(SystemExit):
        phase35_prereg.fill(slot, **kwargs({**_entry("rule text"), "proposer": "Rafael"}))


# =================================================================================================
# (12) PLAN 04 — THE SLOT CENSUS (D-02's three red cases, PREREG-05 SC1). Every file that could fill
# a slot is parsed; planted owner files live under tmp_path only.
# =================================================================================================


def _fill_calls(source):
    """``(slot or None, Call)`` for every ``phase35_prereg.fill(...)`` call in `source`."""
    calls = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and _is_attribute(node.func, "phase35_prereg", "fill"):
            first = node.args[0] if node.args else None
            constant = isinstance(first, ast.Constant) and isinstance(first.value, str)
            calls.append((first.value if constant else None, node))
    return calls


def _scanned_sources(root):
    """``(posix relpath, source)`` for scripts/**/*.py (minus the prereg itself) and src/**/*.py,
    recursively: owner_prereg_glob's ``*`` crosses ``/`` (review WR-05)."""
    prereg = root / PREREG
    paths = [p for p in (root / "scripts").rglob("*.py") if p != prereg]
    paths += (root / "src").rglob("*.py")
    return sorted((p.relative_to(root).as_posix(), p.read_text(encoding="utf-8")) for p in paths)


def _reaches_slots(node):
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        if _is_attribute(node, "phase35_prereg", "SLOTS"):
            return True
        node = node.value
    return False


def _is_fill_of(node, slot):
    return (
        isinstance(node, ast.Call)
        and _is_attribute(node.func, "phase35_prereg", "fill")
        and bool(node.args)
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == slot
    )


def _span(node):
    return (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)


def _slot_census_failures(sources):
    """D-02 checks 1-3 over ``(relpath, source)`` pairs: (1) undeclared or non-constant slot,
    (2) a fill outside its owner's fill files, a slot filled twice, a write to SLOTS, (3) a slot
    name bound to anything but its own fill call, a ``_rule_*`` reached directly, an alias."""
    slots = phase35_prereg.SLOTS
    upper = {name.upper(): name for name in slots}
    failures, sites = [], {}
    for relpath, source in sources:
        tree = ast.parse(source)
        bound = {  # keyed by position: _fill_calls parses its own tree
            _span(node.value): node.targets[0].id
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        }
        for slot, call in _fill_calls(source):
            where = f"{relpath}:{call.lineno}"
            if slot is None:
                failures.append(f"{where}: non-constant slot argument to phase35_prereg.fill")
                continue
            if slot not in slots:
                failures.append(f"{where}: undeclared slot {slot!r}")
                continue
            glob = phase35_prereg.owner_prereg_glob(slot)
            if not fnmatch.fnmatch(relpath, glob):
                failures.append(f"{where}: fills {slot} outside its owner ({glob})")
            sites.setdefault(slot, []).append(where)
            if bound.get(_span(call)) != slot.upper():
                failures.append(
                    f"{where}: different rule: fill({slot!r}) is not the whole value of the "
                    f"module-level binding {slot.upper()}"
                )
        for name, value in _module_targets(tree):
            if name in upper and not _is_fill_of(value, upper[name]):
                failures.append(
                    f"{relpath}:{value.lineno}: different rule: {name} is bound to something "
                    f"other than phase35_prereg.fill({upper[name]!r}, ...)"
                )
        for node in ast.walk(tree):
            where = f"{relpath}:{getattr(node, 'lineno', '?')}"
            if (
                isinstance(node, (ast.Subscript, ast.Attribute))
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and _reaches_slots(node)
            ):
                failures.append(f"{where}: registry write to phase35_prereg.SLOTS")
            if isinstance(node, ast.Attribute) and node.attr.startswith("_rule_"):
                failures.append(f"{where}: _rule_ reference .{node.attr}")
            if isinstance(node, ast.Call) and _reaches_slots(node.func):
                failures.append(f"{where}: registry call through phase35_prereg.SLOTS")
            if (
                isinstance(node, ast.Subscript)
                and _reaches_slots(node)
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == "rule"
            ):
                failures.append(f"{where}: registry rule access phase35_prereg.SLOTS[...]['rule']")
            if isinstance(node, ast.Call) and node.args:
                func = getattr(node.func, "attr", getattr(node.func, "id", None))
                first = node.args[0]
                if (
                    func == "getattr"
                    and isinstance(first, ast.Name)
                    and first.id == "phase35_prereg"
                ):
                    failures.append(f"{where}: dynamic access getattr(phase35_prereg, ...)")
                if (
                    func in ("import_module", "__import__")
                    and isinstance(first, ast.Constant)
                    and first.value == "phase35_prereg"
                ):
                    failures.append(f"{where}: dynamic import of phase35_prereg")
            if isinstance(node, ast.Import):
                failures += [
                    f"{where}: alias: import phase35_prereg as {a.asname}"
                    for a in node.names
                    if a.name == "phase35_prereg" and a.asname not in (None, "phase35_prereg")
                ]
            if isinstance(node, ast.ImportFrom) and node.module == "phase35_prereg":
                for a in node.names:
                    if a.name.startswith("_rule_"):
                        failures.append(f"{where}: _rule_ import {a.name} from phase35_prereg")
                    elif a.name in ("fill", "*"):
                        failures.append(f"{where}: alias: from phase35_prereg import {a.name}")
                    elif a.name == "SLOTS":
                        failures.append(f"{where}: registry import of SLOTS (registry write risk)")
    failures += [
        f"slot {slot} filled twice: {', '.join(where)}"
        for slot, where in sorted(sites.items())
        if len(where) > 1
    ]
    return failures


def test_slot_census_scans_scripts_recursively(tmp_path):
    """Review WR-05: a file under scripts/<sub>/ matches owner_prereg_glob and is scanned."""
    (tmp_path / "scripts" / "sub").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    nested = tmp_path / "scripts" / "sub" / "x.py"
    nested.write_text(
        "import phase35_prereg\nS = phase35_prereg.SLOTS['e2_S']['rule'](s=5)\n", encoding="utf-8"
    )
    (tmp_path / PREREG).write_text("ignored = 1\n", encoding="utf-8")
    sources = _scanned_sources(tmp_path)
    assert [path for path, _ in sources] == ["scripts/sub/x.py"]
    assert any("registry call" in f for f in _slot_census_failures(sources))
    assert fnmatch.fnmatch("scripts/phase40_sub/x_prereg.py", "scripts/phase40_*prereg.py")


def test_slot_census_is_green_on_the_real_tree():
    sources = _scanned_sources(_ROOT)
    assert len(sources) > 1, "meta-guard: the census scanned nothing"
    assert any(path.startswith("src/") for path, _ in sources), "meta-guard: src/ not scanned"
    assert PREREG not in dict(sources)
    assert _slot_census_failures(sources) == []


_E2_S_FILL = 'E2_S = phase35_prereg.fill("e2_S", s=5)'


def test_slot_census_reds_on_planted_owner_files(tmp_path):
    def owner_file(name, *lines):
        text = "\n".join(("import phase35_prereg", *lines)) + "\n"
        return _planted(tmp_path, "", text, name)

    count = iter(range(1000))

    def sources(*files):
        return [(rel, owner_file(f"{next(count)}.py", *lines)) for rel, *lines in files]

    p40, p41 = "scripts/phase40_prereg.py", "scripts/phase41_prereg.py"
    assert _slot_census_failures(sources((p40, _E2_S_FILL))) == []
    multi_file = sources(
        (
            p41,
            "E1_ALTERNATIVE_ORDERING = "
            'phase35_prereg.fill("e1_alternative_ordering", ordering=None)',
        ),
        (
            "scripts/phase41_floors_prereg.py",
            'E1_CONDITION_A_FLOORS = phase35_prereg.fill("e1_condition_a_floors", floors=None)',
        ),
    )
    assert _slot_census_failures(multi_file) == []

    for expected, files in (
        ("undeclared", [(p40, 'E9_UNDECLARED = phase35_prereg.fill("e9_undeclared")')]),
        ("non-constant", [(p40, 'S = "e2_S"', "E2_S = phase35_prereg.fill(S, s=5)")]),
        ("outside its owner", [(p41, _E2_S_FILL)]),
        ("outside its owner", [("scripts/phase40_driver.py", _E2_S_FILL)]),
        ("filled twice", [(p40, _E2_S_FILL), ("scripts/phase40_seeds_prereg.py", _E2_S_FILL)]),
        ("filled twice", [(p40, _E2_S_FILL, _E2_S_FILL.replace("E2_S =", "E2_S_AGAIN ="))]),
        ("different rule", [(p40, "E2_S = 5")]),
        ("_rule_ reference", [(p40, "E2_S = phase35_prereg._rule_e2_S(s=5)")]),
        ("_rule_ import", [(p40, "from phase35_prereg import _rule_e2_S")]),
        ("different rule", [(p40, _E2_S_FILL.replace("E2_S =", "S ="))]),
        ("registry write", [(p40, 'phase35_prereg.SLOTS["e2_S"] = None')]),
        ("alias", [(p40, "from phase35_prereg import fill", 'E2_S = fill("e2_S", s=5)')]),
        # review WR-05: reaching a rule without fill, under any name, from any file.
        (
            "registry call",
            [("scripts/phase37_driver.py", 'S = phase35_prereg.SLOTS["e2_S"]["rule"](s=5)')],
        ),
        ("registry rule access", [(p40, 'R = phase35_prereg.SLOTS["e2_S"]["rule"]')]),
        ("getattr", [(p40, 'S = getattr(phase35_prereg, "fill")("e2_S", s=5)')]),
        (
            "dynamic import",
            [(p40, "import importlib", 'M = importlib.import_module("phase35_prereg")')],
        ),
        ("dynamic import", [(p40, 'M = __import__("phase35_prereg")')]),
        ("_rule_ reference", [(p40, "M = phase35_prereg", "S = M._rule_e2_S(s=5)")]),
    ):
        failures = _slot_census_failures(sources(*files))
        assert any(expected in f for f in failures), (expected, files, failures)


def _dispatch_failures(source):
    tree = ast.parse(source)
    calls = [n for n in ast.walk(_function(tree, "fill")) if isinstance(n, ast.Call)]
    dispatch = [c for c in calls if isinstance(c.func, ast.Subscript)]
    failures = []
    if [ast.unparse(c.func) for c in dispatch] != ["SLOTS[slot]['rule']"]:
        failures.append(f"fill dispatches {[ast.unparse(c.func) for c in dispatch]}")
    failures += [
        f"fill calls {ast.unparse(c.func)} at line {c.lineno}"
        for c in calls
        if not isinstance(c.func, ast.Subscript)
        and not (isinstance(c.func, ast.Name) and c.func.id in ("_prove", "isinstance"))
    ]
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    failures += [
        f"rule {slot['rule'].__name__} is not a module-level def"
        for slot in phase35_prereg.SLOTS.values()
        if slot["rule"].__name__ not in defined
    ]
    return failures


def test_slot_fill_dispatches_only_the_declared_rule(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    assert _dispatch_failures(source) == []

    returns = [
        n for n in ast.walk(_function(ast.parse(source), "fill")) if isinstance(n, ast.Return)
    ]
    assert len(returns) == 1, "meta-guard: fill has one return"
    ret = returns[0]
    line = " " * ret.col_offset + "return _rule_e2_S(**inputs)"
    planted = _replace_lines(source, ret.lineno, ret.end_lineno, [line])
    ast.parse(planted)
    assert _dispatch_failures(_planted(tmp_path, source, planted, "dispatch.py"))

    assert real.read_bytes() == before


# =================================================================================================
# (13) PLAN 04 — PER-FILL-FILE ORDERING (D-02, B1/B2/B6/B7). Legs: (a) a fill file precedes every
# record of its phase, minus its slots' declared inputs only when EVERY slot it fills consumes an
# in-phase input; (b) every tracked declared input precedes the fill file's first commit; (c) a
# phase-O record outside the inputs of all O's slots requires every O slot filled.
# =================================================================================================


def _is_fill_file(path):
    """The SAME predicate the census applies: ``path`` matches some slot's owner_prereg_glob
    (review IN-03; the ordering legs once used a narrower regex)."""
    globs = {phase35_prereg.owner_prereg_glob(slot) for slot in phase35_prereg.SLOTS}
    return any(fnmatch.fnmatch(path, glob) for glob in globs)


def test_fill_file_predicate_agrees_with_owner_prereg_glob():
    globs = {phase35_prereg.owner_prereg_glob(slot) for slot in phase35_prereg.SLOTS}
    for name, expected in (
        ("scripts/phase40_prereg.py", True),
        ("scripts/phase40_seeds_prereg.py", True),
        ("scripts/phase40_seeds-prereg.py", True),
        ("scripts/phase41_sub/floors_prereg.py", True),
        ("scripts/phase40_driver.py", False),
        ("scripts/phase35_prereg.py", False),
        ("scripts/phase46_prereg.py", False),
    ):
        assert _is_fill_file(name) is expected, name
        assert any(fnmatch.fnmatch(name, g) for g in globs) is expected, name


def _fill_sites(run):
    """``{fill file: frozenset(declared slots it fills)}`` for the tracked fill files at HEAD."""
    sites = {}
    for path in run("ls-files", "scripts").stdout.split():
        if _is_fill_file(path):
            source = run("show", f"HEAD:{path}").stdout
            slots = frozenset(s for s, _ in _fill_calls(source) if s in phase35_prereg.SLOTS)
            if slots:
                sites[path] = slots
    return sites


def _slot_ordering_failures(run):
    """``(failures, pairs_checked)``; each leg failure starts with its marker (a), (b) or (c)."""
    slots = phase35_prereg.SLOTS
    failures, pairs = [], 0
    if run("rev-parse", "--is-shallow-repository").stdout.strip() != "false":
        failures.append("(shallow) shallow clone: no leg can be checked (fetch-depth: 0)")

    def first_add(path):
        return run("log", "--diff-filter=A", "--format=%H", "--", path).stdout.split()[-1]

    def before(x, y):
        return x != y and run("merge-base", "--is-ancestor", x, y, check=False).returncode == 0

    def records(owner):
        return run("ls-files", f"results/phase{owner}_*").stdout.split()

    def inputs(names):
        return {pat for s in names for pat in slots[s]["input_records"]}

    def is_input(record, pats):
        return any(fnmatch.fnmatch(record, p) for p in pats)

    sites = _fill_sites(run)
    filled = {slot for names in sites.values() for slot in names}
    for owner in sorted({s["owner_phase"] for s in slots.values()}):
        owner_slots = {name for name, s in slots.items() if s["owner_phase"] == owner}
        tracked = [r for r in records(owner) if not is_input(r, inputs(owner_slots))]
        failures += [
            f"(c) slot {slot} is unfilled while phase {owner} record {r} is tracked"
            for slot in sorted(owner_slots - filled)
            for r in tracked
        ]

    for path, names in sorted(sites.items()):
        owner = int(path.removeprefix("scripts/phase").split("_", 1)[0])
        commits = run("log", "--format=%H", "--", path).stdout.split()
        pats = inputs(names)
        own = f"results/phase{owner}_"
        free = sorted(
            s for s in names if not any(p.startswith(own) for p in slots[s]["input_records"])
        )
        exempt = set() if free else pats
        note = f" (slots {', '.join(free)} have no phase-{owner} input)" if free else ""
        for record in records(owner):
            if is_input(record, exempt):
                continue
            added = first_add(record)
            for commit in commits:
                pairs += 1
                if not before(commit, added):
                    failures.append(
                        f"(a) fill file {path} commit {commit} does not strictly precede "
                        f"record {record}{note}"
                    )
        for i in sorted({i for p in pats for i in run("ls-files", p).stdout.split()}):
            pairs += 1
            if not before(first_add(i), commits[-1]):
                failures.append(
                    f"(b) declared input {i} of {path} is not first added strictly before "
                    f"{path}'s first commit"
                )
    return failures, pairs


def _ordering_after_every_commit(run):
    """The verdict as of every commit, oldest first. Detaches HEAD: planted repositories only."""
    top = pathlib.Path(run("rev-parse", "--show-toplevel").stdout.strip()).resolve()
    phase35_prereg._prove(top != _ROOT.resolve(), "refusing to detach HEAD in the real repository")
    verdicts = []
    for sha in run("rev-list", "--reverse", "HEAD").stdout.split():
        run("checkout", "-q", "--detach", sha)
        verdicts.append(_slot_ordering_failures(run))
    return verdicts


def test_slot_ordering_every_commit_refuses_the_real_repo():
    head = _git("rev-parse", "HEAD")
    with pytest.raises(SystemExit, match="real repository"):
        _ordering_after_every_commit(_git_in(_ROOT))
    assert _git("rev-parse", "HEAD") == head


def test_slot_ordering_is_green_on_the_real_repo():
    failures, pairs = _slot_ordering_failures(_git_in(_ROOT))
    assert failures == []
    assert isinstance(pairs, int)  # 0 today is honest-green: no fill file, no v6.0 record


def _fill_file(path, *slots):
    lines = "".join(f'{s.upper()} = phase35_prereg.fill("{s}")\n' for s in slots)
    return (path, "import phase35_prereg\n" + lines)


def _record(path):
    return (f"results/{path}", "{}")


_P41_FIRST = _fill_file(
    "scripts/phase41_prereg.py",
    "e1_checkpoint_grid",
    "e1_alternative_ordering",
    "e1_condition_b_margin",
)
_P41_FLOORS = _fill_file(
    "scripts/phase41_floors_prereg.py", "e1_condition_a_floors", "e1_condition_c_band_inputs"
)


def test_slot_ordering_reds_on_a_planted_repo(tmp_path):
    greens = {
        "g36": [
            [_record("phase36_probe_a.json")],
            [_fill_file("scripts/phase36_prereg.py", "v6_budget_and_stop_line")],
            [_record("phase36_budget.json")],
        ],
        "g41": [
            [_P41_FIRST],
            [_record("phase41_calibration_a.json")],
            [_record("phase41_band_inputs_a.json")],
            [_P41_FLOORS],
            [_record("phase41_erasure_a.json")],
        ],
        "g42": [
            [_fill_file("scripts/phase42_prereg.py", "e3_grid_subset")],
            [_record("phase42_control_a.json")],
            [_fill_file("scripts/phase42_threshold_prereg.py", "e3_recall_threshold")],
            [_record("phase42_point_a.json")],
        ],
        "g38": [
            [
                _fill_file(
                    "scripts/phase38_prereg.py",
                    "e5_minting_rule",
                    "e5_rank_moves_and_generation_collapses",
                )
            ],
            [_record("phase38_minting.json")],
            [_fill_file("scripts/phase38_sizes_prereg.py", "e5_set_sizes")],
            [_record("phase38_rank_a.json")],
        ],
    }
    for name, commits in greens.items():
        verdicts = _ordering_after_every_commit(_planted_repo(tmp_path / name, commits))
        assert len(verdicts) == len(commits), name
        assert [failures for failures, _ in verdicts] == [[]] * len(commits), (name, verdicts)
        assert verdicts[-1][1] > 0, name

    def red(name, commits, leg):
        failures, _ = _slot_ordering_failures(_planted_repo(tmp_path / name, commits))
        assert failures and all(f.startswith(leg) for f in failures), (name, failures)
        return failures

    red("c40", [[_record("phase40_seeds.json")]], "(c)")
    c41 = red(
        "c41", [[_P41_FIRST], [_record("phase41_erasure_a.json")]], "(c)"
    )  # B6: leg (c) still bites on a non-input Phase 41 record
    for slot in ("e1_condition_a_floors", "e1_condition_c_band_inputs"):
        assert any(f"slot {slot} " in f for f in c41), (slot, c41)

    p40 = _fill_file("scripts/phase40_prereg.py", "e2_S", "e2_noise_floor_estimator")
    red("a40", [[_record("phase40_seeds.json")], [p40]], "(a)")
    red("a40_same", [[_record("phase40_seeds.json"), p40]], "(a)")
    red(  # B2: an own-phase INPUT after its fill file, no non-input record anywhere
        "b36",
        [
            [_fill_file("scripts/phase36_prereg.py", "v6_budget_and_stop_line")],
            [_record("phase36_probe_a.json")],
        ],
        "(b)",
    )

    def names(failures, path, record):
        return any(path in f and record in f for f in failures)

    a41 = red(  # B1: the alternative ordering came after its calibration
        "a41",
        [
            [_record("phase41_calibration_a.json")],
            [_P41_FIRST],
            [_record("phase41_band_inputs_a.json")],
            [_P41_FLOORS],
        ],
        "(a)",
    )
    assert names(a41, "scripts/phase41_prereg.py", "phase41_calibration_a.json"), a41

    b7_38 = red(  # B7: the minting rule cannot ride on e5_set_sizes' exemption
        "b7_38",
        [
            [_record("phase38_minting.json")],
            [
                _fill_file(
                    "scripts/phase38_prereg.py",
                    "e5_minting_rule",
                    "e5_set_sizes",
                    "e5_rank_moves_and_generation_collapses",
                )
            ],
            [_record("phase38_rank_a.json")],
        ],
        "(a)",
    )
    assert names(b7_38, "scripts/phase38_prereg.py", "phase38_minting.json"), b7_38

    b7_41 = red(  # B7: the alternative ordering cannot ride on the floors' exemption
        "b7_41",
        [
            [
                _fill_file(
                    "scripts/phase41_prereg.py", "e1_checkpoint_grid", "e1_condition_b_margin"
                )
            ],
            [_record("phase41_calibration_a.json")],
            [_record("phase41_band_inputs_a.json")],
            [
                _fill_file(
                    "scripts/phase41_floors_prereg.py",
                    "e1_alternative_ordering",
                    "e1_condition_a_floors",
                    "e1_condition_c_band_inputs",
                )
            ],
            [_record("phase41_erasure_a.json")],
        ],
        "(a)",
    )
    assert names(b7_41, "scripts/phase41_floors_prereg.py", "phase41_calibration_a.json"), b7_41


def test_every_slot_input_is_a_v6_path_or_a_v5_record():
    v5 = set(_git("ls-tree", "-r", "--name-only", "v5.0", "results").split())
    assert v5, "v5.0 tracks no results file: this registry check would be blind"
    v6 = phase35_prereg.V6_RESULT_PATHS
    seen = {"v6": 0, "v5": 0}
    for name, slot in phase35_prereg.SLOTS.items():
        for pat in slot["input_records"]:
            declared = pat in v6 or any(fnmatch.fnmatch(pat, v) for v in v6)
            assert declared or pat in v5, (name, pat)
            seen["v6" if declared else "v5"] += 1
            number = pat.removeprefix("results/phase").split("_", 1)[0]
            if number.isdigit() and 36 <= int(number) <= 45:
                assert declared, (name, pat)
    assert seen["v6"] and seen["v5"], seen


# =================================================================================================
# (14) PLAN 04 — EVERY PREREG FUNCTION HAS A CPU TEST (D-13 / PREREG-08).
# =================================================================================================


def _untested_functions(prereg_source, test_source):
    """Module-level defs of the prereg that the test source never CALLS (review IN-05: a bare
    mention, e.g. an ``is`` assert, is not a test). A ``_rule_<slot>`` counts as tested through a
    ``phase35_prereg.fill("<slot>", ...)`` call."""
    calls = [n.func for n in ast.walk(ast.parse(test_source)) if isinstance(n, ast.Call)]
    named = {f.id for f in calls if isinstance(f, ast.Name)}
    named |= {f.attr for f in calls if isinstance(f, ast.Attribute)}
    named |= {"_rule_" + slot for slot, _ in _fill_calls(test_source) if slot is not None}
    defs = [n.name for n in ast.parse(prereg_source).body if isinstance(n, ast.FunctionDef)]
    return sorted(name for name in defs if name not in named)


def test_prereg_helpers_behave(monkeypatch):
    with pytest.raises(SystemExit) as refused:
        phase35_prereg._prove(False, "x")
    assert str(refused.value).startswith("[phase35_prereg]")
    assert abs(math.fsum(phase35_prereg._binom_pmf(i, 16, 0.3) for i in range(17)) - 1.0) < 1e-12
    assert phase35_prereg._binom_pmf(17, 16, 0.3) == 0.0
    for bad in (True, 1.0):
        with pytest.raises(SystemExit):
            phase35_prereg._prove_count("x", bad)
    phase35_prereg._prove_count("x", 3)
    for bad in (True, "1"):
        with pytest.raises(SystemExit):
            phase35_prereg._prove_real("x", bad)
    phase35_prereg._prove_real("x", 0.5)
    for bad in (math.inf, math.nan, True):
        with pytest.raises(SystemExit):
            phase35_prereg._prove_finite("x", bad)
    phase35_prereg._prove_finite("x", 0.5)
    phase35_prereg._prove_one_run_inputs(100, 50, 50, 1e-5)
    with pytest.raises(SystemExit):
        phase35_prereg._prove_one_run_inputs(100, 50, 51, 1e-5)  # v > r
    assert phase35_prereg._p_value(100, 50, 40, 1.0, 1e-5) == phase35_prereg.p_value_one_run(
        100, 50, 40, 1.0, 1e-5
    )
    assert phase35_prereg._prove_entries() is None
    assert phase35_prereg._prove_slots() is None
    assert phase35_prereg._prove_derivation_value("x", _entry(1), 1) is None
    with pytest.raises(SystemExit):
        phase35_prereg._prove_derivation_value("x", _entry(1), 2)
    fronts = {f: 5.0 for f in phase35_prereg.V6_MPS_FRONTS}
    least = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    assert phase35_prereg._prove_budget(fronts, 60.0, least) == 40.0
    for args in ((fronts, 91.0, least), (fronts, 30.0, least), ({**fronts, "E1": "5"}, 60.0, 2)):
        with pytest.raises(SystemExit):
            phase35_prereg._prove_budget(*args)
    targets = phase35_prereg.e1_targets()
    assert phase35_prereg._prove_cells_cover_targets("x", {(t, "o"): None for t in targets}) is None
    with pytest.raises(SystemExit):
        phase35_prereg._prove_cells_cover_targets("x", {(targets[0], "o"): None})
    bad_entries = {**phase35_prereg.ENTRIES, "x": {**_good_entry(), "kind": "guess"}}
    monkeypatch.setattr(phase35_prereg, "ENTRIES", bad_entries)
    with pytest.raises(SystemExit):
        phase35_prereg._prove_entries()

    # The design rules, each through a literal fill("<slot>") call (the census below counts these).
    design = {slot: kwargs(_entry("rule text")) for slot, kwargs in _DESIGN_SLOTS.items()}
    assert phase35_prereg.fill(
        "r1b_tolerance_and_replicated", **design["r1b_tolerance_and_replicated"]
    )
    assert phase35_prereg.fill("e5_minting_rule", **design["e5_minting_rule"])
    assert phase35_prereg.fill("e2_noise_floor_estimator", **design["e2_noise_floor_estimator"])
    assert phase35_prereg.fill(
        "e5_rank_moves_and_generation_collapses",
        **design["e5_rank_moves_and_generation_collapses"],
    )
    assert phase35_prereg.fill("e6_decomposition_rule", **design["e6_decomposition_rule"])


def test_every_rule_has_a_cpu_test(tmp_path):
    real = _ROOT / PREREG
    before = real.read_bytes()
    source = before.decode("utf-8")
    test_source = pathlib.Path(__file__).read_text(encoding="utf-8")
    defs = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    assert defs, "meta-guard: the prereg defines no function, the census would be vacuous"
    assert _untested_functions(source, test_source) == []

    planted = source + '\n\ndef _rule_planted_untested(*, entry):\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "untested.py")
    assert _untested_functions(copied, test_source) == ["_rule_planted_untested"]

    # Review IN-05: a bare mention is not a test; only a call is.
    planted = source + '\n\ndef planted_helper():\n    """Planted."""\n'
    copied = _planted(tmp_path, source, planted, "mentioned.py")
    mentioned = test_source + "\nassert phase35_prereg.planted_helper is not None\n"
    assert _untested_functions(copied, mentioned) == ["planted_helper"]
    called = test_source + "\nphase35_prereg.planted_helper()\n"
    assert _untested_functions(copied, called) == []

    assert real.read_bytes() == before
