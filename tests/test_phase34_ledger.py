"""Plan 34-03: the v5.0 disposition ledger is data with a closed domain.

`results/phase34_ledger.json` is a NEW file (D-12): the frozen v4.0 block embeds the phase28
ledger's rows digest, so v5.0 rows never go into `results/phase28_ledger.json`. Same schema and
six-value domain as phase28; RE-DEFERRED rows add exactly `target` and `prerequisite`. The census
is derived at test time from every REVIEW heading, staged row and SECURITY risk id of Phases 29-33
(D-13), the phase28 ledger's still-open rows are re-disposed by reference, 33-REVIEW WR-01/02 stay
deferred because the module is pinned (D-14), and the `v5.0` tag hand-off is a row (D-11).
CPU-only, no torch.
"""

import hashlib
import json
import pathlib
import re
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _path in (_ROOT / "scripts", _ROOT / "tests"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import _prose  # noqa: E402  (scripts/ is not a package)
import phase28_report  # noqa: E402

from test_phase28_ledger import (  # noqa: E402
    DISPOSITIONS,
    REQUIRED_KEYS,
    _domain_violations,
    _fixed_violations,
    _resolve,
)

LEDGER = _ROOT / "results/phase34_ledger.json"
P28_LEDGER = _ROOT / "results/phase28_ledger.json"
P33_RECORD = _ROOT / "results/phase33_admission.json"
RE_DEFERRED_KEYS = frozenset({"target", "prerequisite"})
PHASES = range(29, 34)
_PHASE_ROOTS = (_ROOT / ".planning/phases", _ROOT / ".planning/milestones/v5.0-phases")
_REVIEW_HEADING = re.compile(r"^### ((?:CR|WR|IN)-\d+)\b", re.M)
_STAGED_ROW = re.compile(r"^\| `([^`]+)` \|", re.M)
_RISK_ID = re.compile(r"\b(?:AR|UF)-\d\d-\d\d\b")
_RECORD_FIELD = re.compile(
    r"results/(phase32_frontier|phase33_admission)\.json::([A-Za-z0-9_.\[\]]+)"
)


def _load(path=LEDGER):
    return json.loads(path.read_text(encoding="utf-8"))


def _phase_dir(nn):
    """The one phase dir for `nn`, before or after the milestone archive move — never zero."""
    found = [p for root in _PHASE_ROOTS for p in root.glob(f"{nn}-*") if p.is_dir()]
    assert len(found) == 1, (nn, found)
    return found[0]


def _review_ids(nn):
    text = (_phase_dir(nn) / f"{nn}-REVIEW.md").read_text(encoding="utf-8")
    ids = _REVIEW_HEADING.findall(text)
    assert ids, f"{nn}-REVIEW.md has no CR/WR/IN heading"
    return ids


def _staged_ids():
    text = (_phase_dir(33) / "33-03-SUMMARY.md").read_text(encoding="utf-8")
    section = text.split("## Phase 34 ledger rows", 1)[1].split("\n## ", 1)[0]
    ids = _STAGED_ROW.findall(section)
    assert ids, "33-03-SUMMARY staged table parsed empty"
    return ids


def _security_files():
    found = {}
    for root in _PHASE_ROOTS:
        for path in root.glob("*/[0-9][0-9]-SECURITY.md"):
            nn = int(path.name[:2])
            if nn in PHASES:
                assert nn not in found, (nn, found[nn], path)
                found[nn] = path
    return found


def _security_ids():
    ids = set()
    for path in _security_files().values():
        ids |= set(_RISK_ID.findall(path.read_text(encoding="utf-8")))
    assert ids, "no AR-/UF- id in the v5.0 SECURITY files"
    return ids


def _key_violations(ledger):
    """Rows whose key set is not exactly REQUIRED_KEYS (| target, prerequisite if RE-DEFERRED)."""
    violations = []
    for row in ledger["rows"]:
        if row.get("disposition") == "RE-DEFERRED":
            expected = REQUIRED_KEYS | RE_DEFERRED_KEYS
            empty = [k for k in sorted(RE_DEFERRED_KEYS) if not str(row.get(k) or "").strip()]
        else:
            expected, empty = REQUIRED_KEYS, []
        if set(row) != expected or empty:
            violations.append((row.get("id"), sorted(set(row) ^ expected), empty))
    return violations


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------
# Schema, domain, identity.
# ---------------------------------------------------------------------------------------------


def test_schema_matches_the_v4_ledger():
    schema, p28 = _load()["schema"], _load(P28_LEDGER)["schema"]
    assert schema["dispositions"] == p28["dispositions"] == sorted(DISPOSITIONS)
    assert schema["required_keys"] == p28["required_keys"] == sorted(REQUIRED_KEYS)
    assert schema["re_deferred_keys"] == ["prerequisite", "target"]


def test_every_row_has_exactly_its_keys():
    assert _key_violations(_load()) == []


def test_disposition_domain_is_closed():
    assert _domain_violations(_load()) == []


def test_ids_milestones_and_categories():
    rows, p28 = _load()["rows"], _load(P28_LEDGER)
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    assert {row["milestone"] for row in rows} <= {"v3.0", "v4.0", "v5.0"}
    p28_milestone = {row["id"]: row["milestone"] for row in p28["rows"]}
    wrong = [
        row["id"]
        for row in rows
        if row["milestone"]
        != (p28_milestone.get(row["id"][4:]) if row["id"].startswith("P28-") else "v5.0")
    ]
    assert wrong == [], wrong
    vocabulary = {row["category"] for row in p28["rows"]}
    assert {row["category"] for row in rows} <= vocabulary


def test_fixed_rows_cite_a_commit_and_a_collectable_test():
    assert _fixed_violations(_load()) == []


# ---------------------------------------------------------------------------------------------
# D-13: census derived from the sources; phase28's open rows by reference.
# ---------------------------------------------------------------------------------------------


def test_phase28_open_rows_are_redisposed_by_reference():
    p28 = _load(P28_LEDGER)
    open_ids = {row["id"] for row in p28["rows"] if row["disposition"] == "RE-DEFERRED"}
    assert open_ids
    by_ref = [row for row in _load()["rows"] if row["id"].startswith("P28-")]
    assert {row["id"][4:] for row in by_ref} == open_ids
    file_sha, digest = _sha256(P28_LEDGER), phase28_report.ledger_rows_digest(p28)
    missing = [
        row["id"] for row in by_ref if file_sha not in row["source"] or digest not in row["source"]
    ]
    assert missing == [], missing
    unchanged = subprocess.run(
        ("git", "diff", "--quiet", "HEAD", "--", "results/phase28_ledger.json"), cwd=_ROOT
    )
    assert unchanged.returncode == 0, "results/phase28_ledger.json differs from HEAD"


def test_every_review_finding_has_a_row():
    ids = {row["id"] for row in _load()["rows"]}
    missing = [f"P{nn}-{rid}" for nn in PHASES for rid in _review_ids(nn)]
    missing = [rid for rid in missing if rid not in ids]
    assert missing == [], missing


def test_every_staged_row_is_present():
    ids = {row["id"] for row in _load()["rows"]}
    missing = [rid for rid in _staged_ids() if rid not in ids]
    assert missing == [], missing


def test_every_security_risk_id_is_named():
    assert set(_security_files()) == {29, 32, 33}
    text = "\n".join(f"{r['id']} {r['source']} {r['evidence']}" for r in _load()["rows"])
    missing = sorted(rid for rid in _security_ids() if rid not in text)
    assert missing == [], missing


# ---------------------------------------------------------------------------------------------
# D-14, D-11, D-09 (data side).
# ---------------------------------------------------------------------------------------------


def test_phase33_review_rows_are_deferred_because_the_module_is_pinned():
    rows = {row["id"]: row for row in _load()["rows"]}
    for rid in ("P33-WR-01", "P33-WR-02"):
        assert rows[rid]["disposition"] == "RE-DEFERRED", rid
        assert "phase33_admission" in rows[rid]["target"], rid
    pinned = _load(P33_RECORD)["provenance"]["module_sha256"]["scripts/phase33_admission.py"]
    assert _sha256(_ROOT / "scripts/phase33_admission.py") == pinned


def test_the_v5_tag_handoff_is_recorded():
    handoff = [
        row
        for row in _load()["rows"]
        if row["disposition"] == "RE-DEFERRED" and "/gsd-complete-milestone" in row["target"]
    ]
    assert len(handoff) == 1, [row["id"] for row in handoff]
    prerequisite = handoff[0]["prerequisite"]
    assert "`v5.0`" in prerequisite and "push" in prerequisite and "main" in prerequisite


def test_named_limitation_reasons_bound_to_record_fields_match_the_records():
    records, checked, failures = {}, [], []
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


def test_no_reason_says_never_exercised():
    said = [row["id"] for row in _load()["rows"] if "never exercised" in row["reason"].lower()]
    assert said == [], said


# ---------------------------------------------------------------------------------------------
# Close block and byte stability.
# ---------------------------------------------------------------------------------------------


def test_close_block_shape():
    close = _load()["close"]
    assert set(close) == {"ci_run"}
    run = close["ci_run"]
    if run is not None:
        assert set(run) == {"id", "url", "head_sha", "conclusion", "recorded"}
        assert run["conclusion"] == "success"
        assert re.fullmatch(r"[0-9a-f]{40}", run["head_sha"]), run["head_sha"]
        assert str(run["id"]).isdigit(), run["id"]


def test_ledger_redump_is_byte_stable():
    raw = LEDGER.read_bytes()
    dumped = json.dumps(json.loads(raw), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert dumped.encode("utf-8") == raw


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


def test_a_re_deferred_row_without_a_target_is_red(tmp_path):
    planted = _load()
    row = next(r for r in planted["rows"] if r["disposition"] == "RE-DEFERRED")
    del row["target"]
    (tmp_path / "ledger.json").write_text(json.dumps(planted), encoding="utf-8")
    assert _key_violations(_load(tmp_path / "ledger.json")) == [(row["id"], ["target"], ["target"])]
