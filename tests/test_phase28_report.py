"""Plan 28-05: the Phase-28 report renderer's guarantees, as CPU tests (SC2, SC4; RPT-01).

The two TEMPLATE SOURCES carry no bare numeral outside the D-19 grammar (the scan reads the
``.tmpl`` files only — never a Python file whose docstrings discuss numerals, and never the rendered
output by value); every ``PUBLICATION_OBLIGATION`` path resolves and its scalar is published; every
constant the report binds equals its module pin; every provenance digest recomputes from bytes; the
confound and the lead are the records' own words; the renderer is torch-free and clock-free. Every
prose comparison is ``_prose.normalized(a) in _prose.normalized(b)`` (D-22), EXCEPT the
byte-identity tests in section (8), added by plan 28-06: the installed spans in ``docs/REPORT.md``
and ``README.md`` are compared with a fresh render under plain ``==`` — D-22's byte clause — so a
re-render that drifts by one byte from the published block is RED (D-17, D-20; T-28-02).
"""

import ast
import difflib
import hashlib
import json
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in ("scripts", "src"):
    if str(_ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(_ROOT / _sub))

import _prose  # noqa: E402  (scripts/ is not a package)
import mitigation_budget  # noqa: E402
import mitigation_gate  # noqa: E402
import mitigation_unit  # noqa: E402
import phase25_prereg  # noqa: E402
import phase26_prereg  # noqa: E402
import phase28_report  # noqa: E402

from personacore.privacy import accountant  # noqa: E402

_RENDERER = _ROOT / "scripts/phase28_report.py"
_TEMPLATES = (phase28_report.TEMPLATE_REPORT, phase28_report.TEMPLATE_GLANCE)

# ---- D-19: the exempt grammar, applied in this order (the ISO date must go before `NN-NN`) -----
_PLACEHOLDER = r"\$\{[^}]*\}"
_EXEMPT = (
    r"Phase \d+",
    r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b",
    r"§\d+(?:\.\d+)?[a-z]?",
    r"\b\d{2}-\d{2}\b",
    r"\bv\d+\.\d+\b",
    r"sha256",
)


def _bare_numerals(text):
    """``(lineno, line)`` for every line still carrying a digit after the placeholders and the
    exempt tokens are stripped. Newlines are never removed, so line numbers are the file's own."""
    stripped = re.sub(_PLACEHOLDER, "", text)
    for pattern in _EXEMPT:
        stripped = re.sub(pattern, "", stripped)
    lines = text.splitlines()
    return [
        (i + 1, lines[i]) for i, line in enumerate(stripped.splitlines()) if re.search(r"\d", line)
    ]


def _anchored_section(text, heading, stop=r"### "):
    """``tests/test_phase18_docs.py::_anchored_section``'s shape: from ``heading`` at line start up
    to the next ``stop`` heading or EOF — anchored on the section, never a tail after a literal."""
    found = re.compile(rf"^{re.escape(heading)}\b.*?(?=^{stop}|\Z)", re.M | re.S).search(text)
    return found.group(0) if found else None


def _dequoted(text):
    return re.sub(r"^> ?", "", text, flags=re.M)


@pytest.fixture(scope="module")
def records():
    return phase28_report.load()[0]


@pytest.fixture(scope="module")
def block():
    return phase28_report.render_report()


# =================================================================================================
# (1) THE TEMPLATE SOURCE CARRIES NO TYPED NUMBER (D-18, D-19; T-28-03, T-28-15).
# =================================================================================================


def test_template_scan_report_has_no_bare_numeral():
    hits = _bare_numerals(phase28_report.TEMPLATE_REPORT.read_text(encoding="utf-8"))
    assert hits == [], "\n".join(f"{n}: {line}" for n, line in hits)


def test_template_scan_glance_has_no_bare_numeral():
    hits = _bare_numerals(phase28_report.TEMPLATE_GLANCE.read_text(encoding="utf-8"))
    assert hits == [], "\n".join(f"{n}: {line}" for n, line in hits)


def test_template_scan_planted_numeral_is_red(tmp_path):
    planted = tmp_path / "planted.md.tmpl"
    planted.write_text(
        "## ${derived.report_title}\n\nThe mechanism: 32 of ${derived.noised_dp_total} points.\n",
        encoding="utf-8",
    )
    hits = _bare_numerals(planted.read_text(encoding="utf-8"))
    assert len(hits) == 1 and hits[0][0] == 3 and "32 of" in hits[0][1], hits


def test_template_scan_exempt_tokens_are_not_hits(tmp_path):
    planted = tmp_path / "exempt.md.tmpl"
    planted.write_text(
        "Phase 28 RELRN-02 D-25-18-ADV64-REFUSED 2026-09-05 c673b4c §12.5c 23-12 v3.0 sha256\n",
        encoding="utf-8",
    )
    assert _bare_numerals(planted.read_text(encoding="utf-8")) == []


def test_template_scan_bare_year_and_all_digit_sha_are_hits(tmp_path):
    for text in ("recorded in 2026 by the gate\n", "figure committed at 1234567\n"):
        planted = tmp_path / "hit.md.tmpl"
        planted.write_text("prose without digits\n" + text, encoding="utf-8")
        hits = _bare_numerals(planted.read_text(encoding="utf-8"))
        assert len(hits) == 1 and hits[0] == (2, text.rstrip("\n")), hits


# =================================================================================================
# (2) EVERY OBLIGATION PATH RESOLVES AND IS PUBLISHED (D-23).
# =================================================================================================


def test_every_obligation_path_resolves(records, block):
    pairs = list(phase25_prereg.PUBLICATION_OBLIGATION) + list(
        phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION
    )
    assert len(pairs) == len(phase25_prereg.PUBLICATION_OBLIGATION) + len(
        phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION
    )
    frontier, canary = records["frontier"], records["canary"]
    misses, scalars, expanded = [], [], 0
    for path, why in pairs:
        if path == "<artifact absent>":
            assert (_ROOT / phase28_report.RECORDS["canary"]).is_file(), why
            continue
        if "<key>" in path:
            for key in canary["audited_point_keys"]:
                concrete = path.replace("<key>", key)
                point = canary["points"][key]
                if point["verdict"] is None:
                    # The record's own named degenerate case: the sigma=0 control publishes no
                    # epsilon, so the canary stores `verdict: null` and says why in `comparison`.
                    assert frontier["points"][key]["epsilon"] is None, key
                    assert point["comparison"].startswith("VACUOUS BY CONSTRUCTION"), key
                    continue
                try:
                    value = phase28_report.resolve(canary, concrete)
                except KeyError:
                    misses.append((concrete, why))
                    continue
                if concrete.endswith(".verdict.verdict"):
                    assert value in phase26_prereg.VERDICTS, (concrete, value)
                expanded += 1
            continue
        try:
            value = phase28_report.resolve(frontier, path)
        except KeyError:
            try:
                value = phase28_report.resolve(canary, path)
            except KeyError:
                misses.append((path, why))
                continue
        if isinstance(value, (bool, int, float, str)):
            scalars.append((path, value))
    assert not misses, "\n".join(f"{path}: {why}" for path, why in misses)
    assert expanded == (len(canary["audited_point_keys"]) - 1) * sum(
        "<key>" in path for path, _ in pairs
    )
    unpublished = [
        path
        for path, value in scalars
        if _prose.normalized(phase28_report._fmt(value)) not in _prose.normalized(block)
    ]
    assert not unpublished, unpublished
    assert scalars


# =================================================================================================
# (3) EVERY CONSTANT THE REPORT BINDS IS ITS MODULE PIN (SC2, D-06).
# =================================================================================================


def _phase18_k_by_ast():
    tree = ast.parse((_ROOT / "scripts/phase18_extraction.py").read_text(encoding="utf-8"))
    values = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "K" for t in node.targets)
    ]
    assert len(values) == 1, values
    return values[0]


def test_constants_match_modules_and_record(records):
    f, admission = records["frontier"], records["admission"]
    points, verdicts = f["points"], f["verdicts"]
    p = points[phase28_report.BRACKET_KEY]
    steps, delta = p["composed_steps"], p["delta"]
    mismatches = []

    def check(name, got, want):
        if got != want:
            mismatches.append(f"{name}: {got!r} != {want!r}")

    check("bracket sigma", p["sigma"], phase28_report.REPRODUCE_SIGMA)
    check("epsilon_for", accountant.epsilon_for(p["sigma"], steps, delta), p["epsilon"])
    check(
        "derived.sigma_for_eps4",
        phase28_report.DERIVED["sigma_for_eps4"](records),
        repr(accountant.sigma_for(phase28_report.TARGET_EPSILON_FACT, steps, delta)),
    )
    check(
        "target epsilon", phase28_report.TARGET_EPSILON_FACT, 4.0
    )  # the D-06 target, spelled ONCE
    check(
        "capacity_branch in CAPACITY_BRANCHES",
        verdicts["capacity_branch"] in mitigation_gate.CAPACITY_BRANCHES,
        True,
    )
    check("CURVE_K", mitigation_budget.CURVE_K, verdicts["curve_k"])
    check(
        "FULL_FIDELITY_K vs record", mitigation_budget.FULL_FIDELITY_K, verdicts["full_fidelity_k"]
    )
    check("FULL_FIDELITY_K vs phase18 K", mitigation_budget.FULL_FIDELITY_K, _phase18_k_by_ast())
    check("DELTA vs epsilon_report", mitigation_unit.DELTA, f["epsilon_report"]["delta"])
    for key in f["point_keys"]:  # delta and composed_steps: EVERY point, both arms
        check(f"{key}.delta", points[key]["delta"], mitigation_unit.DELTA)
        check(f"{key}.composed_steps", points[key]["composed_steps"], mitigation_budget.STEP_BUDGET)

    # q and clip_norm are checked over the NOISED DP points only: the two sigma=0 controls carry
    # clip_norm = 1000000.0 (unclipped by design) and the twelve adv_* points carry q = None and
    # clip_norm = None (the adversarial arm has no mechanism). The count is record-derived.
    dp_keys = [k for k in points if points[k]["arm"] in {"dp_n8", "dp_n64"}]
    dp_sigma_zero = [k for k in dp_keys if points[k]["sigma"] == 0]
    noised = [k for k in dp_keys if points[k]["sigma"] > 0]
    assert len(noised) == len(dp_keys) - len(dp_sigma_zero) and noised
    for key in noised:
        check(f"{key}.q", points[key]["q"], mitigation_unit.SAMPLING_RATE_Q)
        check(f"{key}.clip_norm", points[key]["clip_norm"], mitigation_budget.CLIP_NORM)
    for key in dp_sigma_zero:
        check(
            f"{key}.clip_norm is not CLIP_NORM",
            points[key]["clip_norm"] != mitigation_budget.CLIP_NORM,
            True,
        )
    for key in points:
        if points[key]["arm"].startswith("adv_"):
            check(f"{key}.q", points[key]["q"], None)
            check(f"{key}.clip_norm", points[key]["clip_norm"], None)

    check(
        "SIGMA_LADDER",
        tuple(mitigation_budget.SIGMA_LADDER),
        tuple(sorted(points[k]["sigma"] for k in f["point_keys"] if k.startswith("dp_n8_"))),
    )
    check("F_Y", mitigation_gate.F_Y, admission["budget"]["f_y"])
    check("MARGIN_K", mitigation_gate.MARGIN_K, admission["budget"]["margin_k"])
    assert not mismatches, "\n".join(mismatches)


# =================================================================================================
# (4) EVERY DIGEST IN THE PROVENANCE TABLE RECOMPUTES FROM BYTES (D-21; T-28-01).
# =================================================================================================


def _table_rows(section):
    rows = [line for line in section.splitlines() if line.startswith("| ")]
    return [[c.strip() for c in row.strip("|").split(" | ")] for row in rows[1:]]


def test_provenance_digests_recompute_from_bytes(records, block):
    section = _anchored_section(block, "### Provenance")
    assert section is not None
    rows = _table_rows(section)
    drift, seen = [], set()
    for source, sha, size, _git_sha in rows:
        if source.endswith(" (`rows` only)"):
            rel = source[: -len(" (`rows` only)")]
            canonical = json.dumps(
                records["ledger"]["rows"], sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
            want_sha = hashlib.sha256(canonical).hexdigest()
            if want_sha != phase28_report.ledger_rows_digest(records["ledger"]):
                drift.append(f"{rel}: ledger_rows_digest disagrees with the canonical rows dump")
            # `close` is outside the size column as it is outside the digest (28-07, D-38).
            want_size = phase28_report.ledger_frozen_bytes(records["ledger"])
        else:
            rel = source
            want_sha = hashlib.sha256((_ROOT / rel).read_bytes()).hexdigest()
            want_size = (_ROOT / rel).stat().st_size
        seen.add(rel)
        if sha != want_sha:
            drift.append(f"{rel}: sha256 {sha} != {want_sha}")
        if int(size) != want_size:
            drift.append(f"{rel}: bytes {size} != {want_size}")
    assert not drift, "\n".join(drift)
    assert set(phase28_report.RECORDS.values()) <= seen, seen


def test_ledger_size_column_is_invariant_under_close(records):
    """Filling ``close.ci_run`` must not move the published ledger row (natural RED at 28-07:
    with the run recorded, the whole-file size read 49297 against the published 49057 while the
    rows digest was unchanged)."""
    ledger = records["ledger"]
    filled = dict(ledger)
    filled["close"] = {
        **ledger["close"],
        "ci_run": {"id": "0", "url": "u", "head_sha": "0" * 40, "conclusion": "success"},
    }
    nulled = dict(ledger)
    nulled["close"] = {**ledger["close"], "ci_run": None}
    assert (
        phase28_report.ledger_frozen_bytes(filled)
        == phase28_report.ledger_frozen_bytes(nulled)
        == phase28_report.ledger_frozen_bytes(ledger)
    )
    assert phase28_report.ledger_rows_digest(filled) == phase28_report.ledger_rows_digest(ledger)


# =================================================================================================
# (5) THE CONFOUND AND THE LEAD ARE THE RECORDS' OWN WORDS (SC4, D-02, D-03, D-08..D-10).
# =================================================================================================


def test_confound_is_quoted_from_the_records(records, block):
    f = records["frontier"]
    text = _prose.normalized(_dequoted(block))
    no_replay = f["verdicts"]["adversarial_no_replay"]
    refused_key = f["verdicts"]["refused_points"][0]
    quoted = [
        no_replay["finding"],
        no_replay["log_line"],
        no_replay["log_source"],
        no_replay["dp_replay_source"],
        f["verdicts"]["amended_criterion"],
        f["verdicts"]["leg_refusals"]["adv_n64"],
        f["points"][refused_key]["verdict"]["early_return_reason"],
    ]
    missing = [q for q in quoted if _prose.normalized(q) not in text]
    assert not missing, missing

    note = (_ROOT / phase28_report.OP_NOTE).read_text(encoding="utf-8")
    section = _anchored_section(note, "### 12.5c")
    assert section is not None
    paragraphs = [p for p in section.split("\n\n") if p.strip()]
    assert _prose.normalized(paragraphs[1]) in text, paragraphs[1]

    # The sweep log is never read: its name reaches the block only through the record's fields.
    source = _RENDERER.read_text(encoding="utf-8")
    assert "logs/" not in source
    in_fields = sum(
        s.count("phase25_sweep.out")
        for s in (no_replay["log_source"], no_replay["dp_replay_source"])
    )
    assert in_fields and block.count("phase25_sweep.out") == in_fields


def _lead_lines(block):
    lines = block.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## "))
    return [line for line in lines[start + 1 :] if line.strip() and not line.startswith("*")]


def test_lead_is_the_gates_own_output(records, block):
    f, admission = records["frontier"], records["admission"]
    ex = f["verdicts"]["arm_existentials"]
    first, second = (_prose.normalized(line) for line in _lead_lines(block)[:2])
    for phrase in (f["verdicts"]["capacity_branch"], ex["dp"], ex["adversarial"]):
        assert _prose.normalized(phrase) in first, phrase

    # (a)/(b) over the NOISED DP points, re-derived here from admission.rows + frontier sigma.
    noised = [
        r
        for r in admission["rows"]
        if r["arm"] == "dp" and f["points"][r["point_key"]]["sigma"] > 0
    ]
    a, b, total = (
        sum(r["cleared_a"] for r in noised),
        sum(r["cleared_b"] for r in noised),
        len(noised),
    )
    assert total and f"{a} of {total}" in second, second
    assert re.search(rf"\b{b}\b", second), (b, second)

    relearning = _prose.normalized(_anchored_section(block, "### Relearning"))
    counts = admission["cleared_counts"]
    by_leg = counts["by_leg"]
    assert sum(v["b"] for v in by_leg.values()) == counts["b"]
    absent = [
        name
        for name, n in [("cleared_counts.b", counts["b"])]
        + [(f"by_leg.{leg}.b", by_leg[leg]["b"]) for leg in by_leg]
        if not re.search(rf"\b{n}\b", relearning)
    ]
    assert not absent, absent


def test_the_caveat_precedes_the_first_subsection(records, block):
    k, n = records["frontier"]["verdicts"]["control_readings"]["dp_n64"]["recall_counts"]["taught"]
    assert f"{k}/{n}" in block
    assert block.index(f"{k}/{n}") < block.index("\n### ")


# =================================================================================================
# (6) NO EPSILON WITHOUT ITS CANARY VERDICT IN THE EXPECTATION SECTION (D-07).
# =================================================================================================


def test_no_epsilon_without_a_verdict(records, block):
    f, canary = records["frontier"], records["canary"]
    section = _anchored_section(block, "### The standing expectation")
    assert section is not None
    lines = [_prose.normalized(line) for line in section.splitlines()]
    violations = []
    for key in ("dp_n8_sigma12p000000", "dp_n8_sigma16p000000"):
        assert key in canary["audited_point_keys"]
        eps = _prose.normalized(phase28_report._fmt(f["points"][key]["epsilon"]))
        verdict = _prose.normalized(canary["points"][key]["verdict"]["verdict"])
        carrying = [line for line in lines if eps in line]
        if not carrying:
            violations.append(f"{key}: epsilon {eps} absent from the section")
        violations += [f"{key}: {line}" for line in carrying if verdict not in line]
    assert not violations, "\n".join(violations)


# =================================================================================================
# (7) THE RENDERER IS TORCH-FREE, CLOCK-FREE, HEAD-FREE, LOG-FREE (D-24; T-28-06, T-28-13).
# =================================================================================================


def test_renderer_imports_without_torch_in_a_fresh_interpreter():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase28_report; "
        "print('torch' in sys.modules, 'phase18_extraction' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False", "False"], out.stdout


def test_renderer_has_no_clock_and_no_head_sha():
    tree = ast.parse(_RENDERER.read_text(encoding="utf-8"))
    clocks = [
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in {"today", "now", "utcnow"}
    ]
    assert not clocks, clocks
    forbidden = ("rev-parse", "logs/", "mitigation_point_verdict")
    strings = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and any(word in node.value for word in forbidden)
    ]
    assert not strings, strings


def test_every_quote_binding_is_used_or_removed():
    templates = "\n".join(t.read_text(encoding="utf-8") for t in _TEMPLATES)
    dead = [name for name in phase28_report.QUOTES if f"${{quote.{name}}}" not in templates]
    assert not dead, dead


# =================================================================================================
# (8) THE INSTALLED BLOCKS ARE BYTE-IDENTICAL TO A RE-RENDER (plan 28-06; D-17, D-20, D-22's byte
# clause; T-28-02, T-28-16). RED while the sentinels are absent, GREEN once `write` has run.
# =================================================================================================

_REPORT_REL = "docs/REPORT.md"
_README_REL = "README.md"


def _markers(stem):
    return f"<!-- {stem}-BEGIN -->", f"<!-- {stem}-END -->"


def _span(relative_path, stem):
    """``tests/test_phase25_correction.py::_span``'s shape: the text strictly between a stem's own
    sentinels, each counted with ``str.count`` (exactly one) and BEGIN before END."""
    text = (_ROOT / relative_path).read_text(encoding="utf-8")
    begin, end = _markers(stem)
    for sentinel in (begin, end):
        found = text.count(sentinel)
        assert found == 1, (
            f"{relative_path}: {sentinel} occurs {found} time(s); exactly one is required. A "
            "missing or duplicated sentinel makes the guard scan the wrong text, which is how a "
            "guard passes vacuously"
        )
    assert text.index(begin) < text.index(end), (
        f"{relative_path}: {stem}'s END sentinel precedes its BEGIN sentinel, so the span is empty "
        "or inverted"
    )
    return text.split(begin, 1)[1].split(end, 1)[0]


def _unified(committed, rendered):
    return "".join(
        difflib.unified_diff(
            committed.splitlines(True), rendered.splitlines(True), "committed", "rendered"
        )
    )


def test_report_sentinels_occur_exactly_once():
    _span(_REPORT_REL, phase28_report.REPORT_STEM)


def test_glance_sentinels_occur_exactly_once():
    _span(_README_REL, phase28_report.GLANCE_STEM)


def test_report_block_is_byte_identical():
    committed = _span(_REPORT_REL, phase28_report.REPORT_STEM)
    rendered = phase28_report.render_report()
    assert committed == rendered, _unified(committed, rendered)


def test_glance_block_is_byte_identical():
    committed = _span(_README_REL, phase28_report.GLANCE_STEM)
    rendered = phase28_report.render_glance()
    assert committed == rendered, _unified(committed, rendered)


def test_report_section_is_after_every_prior_heading():
    """D-01: the section is appended AFTER every existing ``## `` heading — its own ``## `` is the
    last one in the file, so nothing above the insertion point moved."""
    span = _span(_REPORT_REL, phase28_report.REPORT_STEM)
    in_span = [line for line in span.splitlines() if line.startswith("## ")]
    assert len(in_span) == 1, in_span
    whole = (_ROOT / _REPORT_REL).read_text(encoding="utf-8")
    headings = [line for line in whole.splitlines() if line.startswith("## ")]
    assert headings[-1] == in_span[0], (headings[-1], in_span[0])


def test_glance_adds_no_heading():
    """D-11: the README bullets live INSIDE ``## Results at a glance`` — no new ``## `` heading."""
    span = _span(_README_REL, phase28_report.GLANCE_STEM)
    assert "\n## " not in span and not span.startswith("## "), span


def _git(*args):
    return subprocess.run(
        ["git", "-C", str(_ROOT), *args], check=True, capture_output=True, text=True
    ).stdout


def _glance_section(text):
    section = _anchored_section(text, phase28_report.GLANCE_HEADING, stop=r"## ")
    assert section is not None, phase28_report.GLANCE_HEADING
    return section


def _bullets(text):
    return [line for line in text.splitlines() if line.startswith("- **")]


def test_glance_deleted_nothing():
    """T-28-16: the pre-existing first bullet still follows the END sentinel, and the section's
    bullet count equals the pre-publish blob's count plus the span's own. The pre-publish revision
    is DERIVED (``tests/test_phase18_docs.py``'s shape): the newest committed README whose blob
    lacks the BEGIN sentinel — never a pinned hash."""
    begin, end = _markers(phase28_report.GLANCE_STEM)
    before = None
    for revision in _git("log", "--format=%H", "--", _README_REL).split():
        blob = _git("show", f"{revision}:{_README_REL}")
        if begin not in blob:
            before = blob
            break
    assert before is not None, f"no committed {_README_REL} without {begin}"
    old_section = _glance_section(before)
    old_bullets = _bullets(old_section)
    assert old_bullets, old_section

    after = (_ROOT / _README_REL).read_text(encoding="utf-8")
    tail = after.split(end, 1)[1]
    first_after = next(line for line in tail.splitlines() if line.strip())
    assert first_after == old_bullets[0], (first_after, old_bullets[0])

    span = _span(_README_REL, phase28_report.GLANCE_STEM)
    assert _bullets(span), span
    assert len(_bullets(_glance_section(after))) == len(old_bullets) + len(_bullets(span))


def test_published_date_is_pinned_not_clocked():
    """T-28-13: ``PUBLISHED`` is an ISO date literal, and the rendered title carries it."""
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", phase28_report.PUBLISHED)
    title = next(
        line for line in phase28_report.render_report().splitlines() if line.startswith("## ")
    )
    assert phase28_report.PUBLISHED in title, title
