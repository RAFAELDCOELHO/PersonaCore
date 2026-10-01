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


def _budget_payload(**hours):
    front_hours = {f: hours.get(f, 5.0) for f in phase35_prereg.V6_MPS_FRONTS}
    return {
        "front_hours": front_hours,
        "total_hours": math.fsum(front_hours.values()),
        "stop_line_hours": 60.0,
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
    good = consume("e5_set_sizes", 7, (minting,), _measured(7, (minting,)))
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
    ):
        with pytest.raises(SystemExit):
            consume("e5_set_sizes", 7, records, derivation)

    with pytest.raises(SystemExit):
        phase35_prereg._budget_front_hours({_BUDGET: {"front_hours": {"E1": 1.0}}}, "E1")


def test_e2_S_refuses_more_seeds_than_the_list(tmp_path, monkeypatch):
    most = len(phase35_prereg.seed_list())
    _inputs(tmp_path / "empty", monkeypatch, {})
    with pytest.raises(SystemExit) as refused:
        phase35_prereg.fill("e2_S", s=most + 1, input_records=(_BUDGET,), derivation={})
    assert "D-06" in str(refused.value) and "never extended" in str(refused.value)

    paths = _inputs(tmp_path / "ok", monkeypatch, {_BUDGET: _budget_payload()})
    least = phase35_prereg.ENTRIES["e2_min_seeds"]["value"]
    assert least == 2
    for s in (most, least):
        assert phase35_prereg.fill("e2_S", s=s, input_records=paths, derivation=_measured(s, paths))
        assert (
            phase35_prereg.fill("e2_S", s=s, input_records=paths, derivation=_measured(s, paths))
            == s
        )
    for bad in (least - 1, True, float(most)):
        with pytest.raises(SystemExit):
            phase35_prereg.fill(
                "e2_S", s=bad, input_records=paths, derivation=_measured(bad, paths)
            )

    paths = _inputs(tmp_path / "noe2", monkeypatch, {_BUDGET: _budget_payload(E2=0.0)})
    with pytest.raises(SystemExit):
        phase35_prereg.fill(
            "e2_S", s=least, input_records=paths, derivation=_measured(least, paths)
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


def _fill_threshold(root, monkeypatch, grid, controls):
    paths = _inputs(root, monkeypatch, controls)
    return phase35_prereg.fill(
        "e3_recall_threshold", grid=grid, input_records=paths, derivation=_measured(paths, paths)
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

    def e4(m, k_plus, k_minus, inclusion=0.5):
        return phase35_prereg.fill(
            "e4_parameters",
            m=m,
            inclusion_probability=inclusion,
            k_plus=k_plus,
            k_minus=k_minus,
            beta=0.05,
            input_records=paths,
            derivation=_measured(m, paths),
        )

    assert phase35_prereg.ENTRIES["e4_inclusion_probability"]["value"] == 0.5
    small = e4(16, 8, 8)
    assert small["ceiling"] == phase35_prereg.eps_lower_one_run(16, 16, 16, delta, 0.05)
    assert small["runs"] is False
    large = e4(184, 92, 92)
    assert large["runs"] is True
    assert large["ceiling"] > phase35_prereg.audit02_cut()
    for args, kwargs in (((16, 8, 8), {"inclusion": 0.25}), ((16, 9, 8), {})):
        with pytest.raises(SystemExit):
            e4(*args, **kwargs)
    monkeypatch.setattr(phase35_prereg, "one_run_reproduction_holds", lambda: False)
    with pytest.raises(SystemExit) as refused:
        e4(16, 8, 8)
    assert "D-11" in str(refused.value)


def test_slot_e1_rules(tmp_path, monkeypatch):
    paths = _inputs(tmp_path / "grid", monkeypatch, {_BUDGET: _budget_payload()})
    checkpoints = (8, 16, 32, 64, 78)  # ablation prefix counts, not K
    grid = phase35_prereg.fill(
        "e1_checkpoint_grid",
        checkpoints=checkpoints,
        input_records=paths,
        derivation=_measured(checkpoints, paths),
    )
    assert grid["checkpoints"] == checkpoints
    assert grid["read_k"] == mitigation_budget.CURVE_K
    assert grid["confirm_k"] == mitigation_budget.FULL_FIDELITY_K
    with pytest.raises(SystemExit):
        phase35_prereg.fill(
            "e1_checkpoint_grid",
            checkpoints=(8, 8, 16),
            input_records=paths,
            derivation=_measured((8, 8, 16), paths),
        )

    paths = _inputs(tmp_path / "floors", monkeypatch, {"results/phase41_calibration_a.json": {}})
    targets = phase35_prereg.e1_targets()
    off_seed = next(
        s for s in phase35_prereg.seed_list() if s not in phase35_prereg.e1_teaching_seeds()
    )

    def floors_fill(floors):
        return phase35_prereg.fill(
            "e1_condition_a_floors",
            floors=floors,
            input_records=paths,
            derivation=_measured(floors, paths),
        )

    floors = {(t, "greedy_loo"): _entry(0.1) for t in targets}
    assert dict(floors_fill(floors)) == floors
    for bad in (
        {(t, "greedy_loo"): _entry(0.1) for t in targets[1:]},
        {**floors, (targets[0], "greedy_loo", off_seed): _entry(0.1)},
    ):
        with pytest.raises(SystemExit):
            floors_fill(bad)

    paths = _inputs(tmp_path / "band", monkeypatch, {"results/phase41_band_inputs_a.json": {}})
    teaching = phase35_prereg.e1_teaching_seeds()[0]

    def band_fill(seed):
        band = {(seed, "greedy_loo"): {"control_gap": 1.0, "gap_noise_floor": 0.1}}
        return phase35_prereg.fill(
            "e1_condition_c_band_inputs",
            band_inputs=band,
            input_records=paths,
            derivation=_measured(band, paths),
        )

    assert band_fill(teaching)[(teaching, "greedy_loo")] == mitigation_gate.dialogue_gap_band(
        control_gap=1.0, gap_noise_floor=0.1
    )
    with pytest.raises(SystemExit):
        band_fill(off_seed)
    assert phase35_prereg.fill("e1_alternative_ordering", ordering=_entry("x")) == _entry("x")


def test_slot_e1_condition_b_margin_is_the_core_read():
    assert phase35_prereg.fill("e1_condition_b_margin") == phase35_prereg.e1_condition_b_margin()
    rule = phase35_prereg.SLOTS["e1_condition_b_margin"]["rule"]
    assert not inspect.signature(rule).parameters


def test_slot_budget_halts_above_the_ceiling(tmp_path, monkeypatch):
    paths = _inputs(tmp_path, monkeypatch, {"results/phase36_probe_a.json": {}})
    fronts = {f: 5.0 for f in phase35_prereg.V6_MPS_FRONTS}

    def budget(front_hours, stop_line_hours):
        return phase35_prereg.fill(
            "v6_budget_and_stop_line",
            front_hours=front_hours,
            stop_line_hours=stop_line_hours,
            input_records=paths,
            derivation=_measured(front_hours, paths),
        )

    out = budget(fronts, 60.0)
    assert out["total_hours"] == 40.0 and out["stop_line_hours"] == 60.0
    assert dict(out["front_hours"]) == fronts
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


@pytest.mark.parametrize("slot", sorted(_DESIGN_SLOTS))
def test_slot_design_entries_refuse_a_proposer(slot):
    kwargs = _DESIGN_SLOTS[slot]
    assert phase35_prereg.fill(slot, **kwargs(_entry("rule text")))
    with pytest.raises(SystemExit):
        phase35_prereg.fill(slot, **kwargs({**_entry("rule text"), "proposer": "Rafael"}))
