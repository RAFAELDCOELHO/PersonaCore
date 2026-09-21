"""Plan 28-03: the disposition ledger is data with a closed domain, and FIXED requires a test.

`results/phase28_ledger.json` carries one row per open item across v3.0 and v4.0 (D-28). This file
checks the schema, the six-value disposition domain (D-29), that every FIXED row cites a commit git
resolves AND a test node id pytest collects, that record-bound reasons equal the record's own field
under `_prose.normalized` (T-28-01), that SC3's v3.0 counts derive from the SOURCE documents on both
sides (never a literal), and the two D-39 / D-31 regressions the FIXED stamp rows cite. CPU-only,
no torch.
"""

import json
import pathlib
import re
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import _prose  # noqa: E402  (scripts/ is not a package)

LEDGER = _ROOT / "results/phase28_ledger.json"
REQUIRED_KEYS = frozenset(
    {"id", "milestone", "category", "source", "disposition", "evidence", "reason"}
)
DISPOSITIONS = frozenset(
    {
        "FIXED",
        "CLOSED-EARLIER",
        "RE-DEFERRED",
        "NAMED-LIMITATION",
        "ACCEPTED",
        "FORBIDDEN-BY-GUARD",
    }
)
_SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
_NODE_ID = re.compile(r"tests/[^ ;]+::[A-Za-z_0-9\[\]-]+")
_RECORD_FIELD = re.compile(
    r"results/(phase25_frontier|phase26_canary|phase27_admission)\.json::([A-Za-z0-9_.\[\]]+)"
)
_STAMP_HEADER = "| Category | Item | Evidence it is a stale stamp, not open work | Deferred At |"
_AUDIT = _ROOT / ".planning/milestones/v3.0-MILESTONE-AUDIT.md"
_STATE = _ROOT / ".planning/STATE.md"
_PHASE19 = _ROOT / ".planning/milestones/v3.0-phases/19-selective-memory-erasure"
_PHASE19_PLANS = ("19-08", "19-09", "19-12", "19-13", "19-16")


def _load(path=LEDGER):
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args):
    return subprocess.run(("git", *args), cwd=_ROOT, capture_output=True, text=True)


def _domain_violations(ledger):
    """Rows whose disposition is outside DISPOSITIONS — shared with the planted-RED probe."""
    return [
        (row.get("id"), row.get("disposition"))
        for row in ledger["rows"]
        if row.get("disposition") not in DISPOSITIONS
    ]


def _fixed_violations(ledger):
    """FIXED rows whose evidence lacks a resolvable commit or a collectable test node id."""
    failures = []
    for row in ledger["rows"]:
        if row["disposition"] != "FIXED":
            continue
        shas = _SHA.findall(row["evidence"])
        if not shas or _git("cat-file", "-e", f"{shas[0]}^{{commit}}").returncode != 0:
            failures.append((row["id"], "no resolvable commit sha", row["evidence"]))
        node_ids = _NODE_ID.findall(row["evidence"])
        if not node_ids:
            failures.append((row["id"], "no test node id", row["evidence"]))
            continue
        collected = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", node_ids[0]],
            cwd=_ROOT,
            capture_output=True,
            text=True,
        )
        if collected.returncode != 0 or node_ids[0] not in collected.stdout:
            failures.append((row["id"], "node id not collected", node_ids[0]))
    return failures


def _resolve(record, dotted):
    """Resolve `a.b[3].c` against `record` by `[]` only — a missing key raises, never None."""
    value = record
    for part in dotted.split("."):
        match = re.fullmatch(r"([A-Za-z0-9_]+)((?:\[\d+\])*)", part)
        value = value[match.group(1)]
        for index in re.findall(r"\[(\d+)\]", match.group(2)):
            value = value[int(index)]
    return value


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    return text.split("\n---", 1)[0]


# ---------------------------------------------------------------------------------------------
# Schema, domain, identity.
# ---------------------------------------------------------------------------------------------


def test_every_row_has_exactly_the_required_keys():
    violations = [
        (row.get("id"), sorted(set(row) ^ REQUIRED_KEYS))
        for row in _load()["rows"]
        if set(row) != REQUIRED_KEYS
    ]
    assert violations == [], violations


def test_disposition_domain_is_closed():
    ledger = _load()
    assert _domain_violations(ledger) == []
    assert ledger["schema"]["dispositions"] == sorted(DISPOSITIONS)
    assert sorted(ledger["schema"]["required_keys"]) == sorted(REQUIRED_KEYS)


def test_ids_are_unique_and_milestone_is_v3_or_v4():
    rows = _load()["rows"]
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    assert {row["milestone"] for row in rows} <= {"v3.0", "v4.0"}


def test_fixed_rows_cite_a_commit_and_a_collectable_test():
    assert _fixed_violations(_load()) == []


def test_re_deferred_rows_name_a_target():
    missing = [
        row["id"]
        for row in _load()["rows"]
        if row["disposition"] == "RE-DEFERRED"
        and not any(t in row["reason"] for t in ("v5.0", "Phase ", "plan 28-"))
    ]
    assert missing == [], missing


def test_forbidden_by_guard_rows_name_the_guard():
    missing = [
        row["id"]
        for row in _load()["rows"]
        if row["disposition"] == "FORBIDDEN-BY-GUARD"
        and not any(g in row["evidence"] for g in ("V3_ARTIFACT_GLOBS", "results/phase1", "prereg"))
    ]
    assert missing == [], missing


def test_named_limitation_reasons_bound_to_record_fields_match_the_records():
    records = {}
    checked, failures = [], []
    for row in _load()["rows"]:
        if row["disposition"] != "NAMED-LIMITATION":
            continue
        for name, dotted in _RECORD_FIELD.findall(row["source"]):
            if name not in records:
                records[name] = _load(_ROOT / "results" / f"{name}.json")
            value = _resolve(records[name], dotted)
            text = value if isinstance(value, str) else repr(value)
            checked.append((row["id"], dotted))
            if _prose.normalized(text) not in _prose.normalized(row["reason"]):
                failures.append((row["id"], dotted, text[:80]))
    assert checked, "no NAMED-LIMITATION row binds a record field"
    assert failures == [], failures


# ---------------------------------------------------------------------------------------------
# SC3's counts: both sides parsed from the sources, never a literal.
# ---------------------------------------------------------------------------------------------


def _audit_tech_debt_item_count():
    lines = _AUDIT.read_text(encoding="utf-8").splitlines()
    start = lines.index("tech_debt:")
    count = 0
    for line in lines[start + 1 :]:
        if re.match(r"^\S", line):
            break
        if re.match(r'^\s+- "', line):
            count += 1
    return count


def _state_stale_stamp_row_count():
    lines = _STATE.read_text(encoding="utf-8").splitlines()
    header = lines.index(_STAMP_HEADER)
    assert lines[header + 1].startswith("|---"), lines[header + 1]
    count = 0
    for line in lines[header + 2 :]:
        if not line.startswith("|"):
            break
        count += 1
    return count


def test_v3_counts_derive_from_the_sources():
    v3 = [row for row in _load()["rows"] if row["milestone"] == "v3.0"]
    tech_debt = [row for row in v3 if row["category"] == "tech-debt"]
    stamps = [row for row in v3 if row["category"] == "stale-stamp"]
    assert len(tech_debt) == _audit_tech_debt_item_count() > 0
    assert len(stamps) == _state_stale_stamp_row_count() > 0


def test_close_block_shape():
    close = _load()["close"]
    assert set(close) == {"ci_run"}
    if close["ci_run"] is not None:
        assert set(close["ci_run"]) == {"id", "url", "head_sha", "conclusion", "recorded"}
        assert close["ci_run"]["conclusion"] == "success"


def test_ledger_redump_is_byte_stable():
    raw = LEDGER.read_bytes()
    assert (
        json.dumps(json.loads(raw), indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
        + b"\n"
        == raw
    )


# ---------------------------------------------------------------------------------------------
# The regressions the FIXED stamp rows cite (D-39, D-31).
# ---------------------------------------------------------------------------------------------


def test_quick_task_summaries_are_named_for_the_audit_tool():
    violations = []
    for task_dir in sorted(p for p in (_ROOT / ".planning/quick").iterdir() if p.is_dir()):
        summaries = sorted(task_dir.glob("*SUMMARY.md"))
        if not summaries:
            continue
        names = [p.name for p in summaries]
        if names != ["SUMMARY.md"]:
            violations.append((task_dir.name, names))
            continue
        if not re.search(r"^status: complete\s*$", _frontmatter(summaries[0]), re.M):
            violations.append((task_dir.name, "status is not complete"))
    assert violations == [], violations


def test_debug_sessions_are_not_left_fixing():
    violations = []
    for session in sorted((_ROOT / ".planning/debug").glob("*.md")):
        match = re.search(r"^status: (.+?)\s*$", _frontmatter(session), re.M)
        status = match.group(1) if match else None
        if status not in {"resolved", "complete"}:
            violations.append((session.name, status))
    assert violations == [], violations


def _plan_artifacts(plan_path):
    """`(path, contains)` pairs under the PLAN frontmatter's `artifacts:` block."""
    block = _frontmatter(plan_path)
    start = block.index("artifacts:")
    end = block.find("key_links:", start)
    section = block[start : end if end != -1 else None]
    pairs = []
    for match in re.finditer(r'- path: "([^"]+)"(.*?)(?=\n\s*- path:|\Z)', section, re.S):
        contains = re.search(r'contains: "([^"]+)"', match.group(2))
        pairs.append((match.group(1), contains.group(1) if contains else None))
    return pairs


def test_phase19_plan_result_artifacts_exist():
    missing = []
    for plan in _PHASE19_PLANS:
        pairs = _plan_artifacts(_PHASE19 / f"{plan}-PLAN.md")
        assert pairs, plan
        for path, contains in pairs:
            if path.startswith("checkpoints/"):
                continue  # gitignored by design — unverifiable from a clone (D-31)
            if not (_ROOT / path).is_file():
                missing.append((plan, path))
            elif plan == "19-16" and contains is not None:
                if contains not in (_ROOT / path).read_text(encoding="utf-8"):
                    missing.append((plan, path, f"pattern {contains!r} absent"))
    assert missing == [], missing


# ---------------------------------------------------------------------------------------------
# Planted RED: the checkers refuse what they exist to refuse.
# ---------------------------------------------------------------------------------------------


def test_a_lowercase_disposition_is_red(tmp_path):
    planted = _load()
    planted["rows"][0]["disposition"] = "fixed"
    (tmp_path / "ledger.json").write_text(json.dumps(planted), encoding="utf-8")
    assert _domain_violations(_load(tmp_path / "ledger.json")) == [
        (planted["rows"][0]["id"], "fixed")
    ]


def test_a_missing_test_node_id_is_red(tmp_path):
    planted = _load()
    fixed = next(row for row in planted["rows"] if row["disposition"] == "FIXED")
    fixed["evidence"] = "0000000; tests/test_phase28_ledger.py::test_that_does_not_exist"
    planted["rows"] = [fixed]
    (tmp_path / "ledger.json").write_text(json.dumps(planted), encoding="utf-8")
    reasons = {f[1] for f in _fixed_violations(_load(tmp_path / "ledger.json"))}
    assert reasons == {"no resolvable commit sha", "node id not collected"}
