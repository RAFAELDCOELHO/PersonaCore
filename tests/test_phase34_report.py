"""Plan 34-04: the v5.0 renderer's guarantees, as CPU tests (D-01, D-03..D-09; RPT-04).

The two template sources carry no bare numeral (the phase28 numeral grammar, imported — one
grammar); every ``CONTRACT`` path resolves and is bound; the lead is per leg and precedes the
admission reasons; the refused leg is NOT MEASURED; the v4.0 -> v5.0 comparison is the record's
rows; every provenance digest recomputes from bytes; the renderer is torch-free and clock-free; and
the frozen v4.0 block still checks. The byte-identity and install tests are section (8).
Prose comparisons use ``_prose.normalized(a) in _prose.normalized(b)``.
"""

import ast
import copy
import hashlib
import pathlib
import re
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in ("scripts", "src", "tests"):
    if str(_ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(_ROOT / _sub))

import _prose  # noqa: E402  (scripts/ is not a package)
import phase28_report  # noqa: E402
import phase34_report  # noqa: E402

from test_phase28_report import _bare_numerals, _git, _markers, _span, _unified  # noqa: E402

_RENDERER = _ROOT / "scripts/phase34_report.py"
_TEMPLATES = (phase34_report.TEMPLATE_REPORT, phase34_report.TEMPLATE_GLANCE)
_PLACEHOLDER = re.compile(r"\$\{([^}]*)\}")
_PREFIXES = {"meta", "frontier", "admission", "ledger", "derived", "table", "path"}


@pytest.fixture(scope="module")
def loaded():
    return phase34_report.load()


@pytest.fixture(scope="module")
def records(loaded):
    return loaded[0]


@pytest.fixture(scope="module")
def block():
    return phase34_report.render_report()


@pytest.fixture(scope="module")
def glance():
    return phase34_report.render_glance()


def _norm_in(needle, haystack):
    return _prose.normalized(needle) in _prose.normalized(haystack)


# ---- (1) the template sources carry no typed number (carried D-18/D-19) ----------------------


def test_template_scan_report_has_no_bare_numeral():
    hits = _bare_numerals(phase34_report.TEMPLATE_REPORT.read_text(encoding="utf-8"))
    assert hits == [], hits


def test_template_scan_glance_has_no_bare_numeral():
    hits = _bare_numerals(phase34_report.TEMPLATE_GLANCE.read_text(encoding="utf-8"))
    assert hits == [], hits


def test_template_scan_typed_count_is_red(tmp_path):
    text = phase34_report.TEMPLATE_REPORT.read_text(encoding="utf-8")
    typed = "- the first leg: 0 of 6 PASS, all 6 INCONCLUSIVE."
    planted = tmp_path / "typed.md.tmpl"
    planted.write_text(text + typed + "\n", encoding="utf-8")
    hits = _bare_numerals(planted.read_text(encoding="utf-8"))
    assert hits == [(len(text.splitlines()) + 1, typed)], hits


# ---- (2) the post-hoc contract (D-08) ---------------------------------------------------------


def _uncovered(template_texts):
    names = {m for text in template_texts for m in _PLACEHOLDER.findall(text)}
    covered = set()
    for path, _why in phase34_report.CONTRACT:
        if any(n == path or n.startswith(path + ".") for n in names):
            covered.add(path)
        if any(path in phase34_report.COVERED_BY.get(n, ()) for n in names):
            covered.add(path)
    return [path for path, _why in phase34_report.CONTRACT if path not in covered]


def test_every_contract_path_resolves_and_is_bound(records):
    for path, why in phase34_report.CONTRACT:
        prefix, _, rest = path.partition(".")
        phase28_report.resolve(records[prefix], rest)
        assert why.strip(), path
    # D-08's minimum set: every listed field is the contract's own path or one of its parents.
    for required in (
        "frontier.verdicts.tallies_by_leg",
        "frontier.verdicts.leg_refusals",
        "frontier.verdicts.control_readings",
        "frontier.verdicts.condition_c_vs_v4",
        "admission.admission.verdict",
        "admission.admission.reasons",
        "admission.limitation",
        "admission.scope",
    ):
        assert any(
            p == required or p.startswith(required + ".") for p, _ in phase34_report.CONTRACT
        ), required
    for name, paths in phase34_report.COVERED_BY.items():
        assert set(paths) <= {p for p, _ in phase34_report.CONTRACT}, name
    texts = [t.read_text(encoding="utf-8") for t in _TEMPLATES]
    assert _uncovered(texts) == []


def test_dropping_a_contract_binding_is_red(tmp_path):
    text = phase34_report.TEMPLATE_REPORT.read_text(encoding="utf-8")
    assert "${table.condition_c_vs_v4}" in text
    dropped = tmp_path / "dropped.md.tmpl"
    dropped.write_text(text.replace("${table.condition_c_vs_v4}", ""), encoding="utf-8")
    glance_text = phase34_report.TEMPLATE_GLANCE.read_text(encoding="utf-8")
    uncovered = _uncovered([dropped.read_text(encoding="utf-8"), glance_text])
    assert uncovered == ["frontier.verdicts.condition_c_vs_v4.rows"], uncovered


def test_contract_is_declared_post_hoc():
    doc = _prose.normalized(ast.get_docstring(ast.parse(_RENDERER.read_text(encoding="utf-8"))))
    assert "not a pre-registration" in doc
    assert "WRITTEN AFTER THE RESULTS" in doc


# ---- (3) the lead (D-04, D-05) ----------------------------------------------------------------


def _legs(records):
    return phase34_report._legs(records)


def _lead_line(lines, leg):
    found = [i for i, line in enumerate(lines) if line.startswith(f"- `{leg}`:")]
    assert len(found) == 1, (leg, found)
    return found[0]


def test_lead_legs_precede_the_admission_reasons(records, block):
    lines = block.splitlines()
    reasons = records["admission"]["admission"]["reasons"]
    first_reason = next(i for i, line in enumerate(lines) if reasons[0] in line)
    tallies = records["frontier"]["verdicts"]["tallies_by_leg"]
    legs = _legs(records)
    assert len(legs) > 1
    for leg in legs:
        i = _lead_line(lines, leg)
        assert i < first_reason, (leg, i, first_reason)
        n = sum(tallies[leg].values())
        if all(v == 0 for k, v in tallies[leg].items() if k != "REFUSED"):
            assert "PASS" not in lines[i]
            assert f"REFUSED {n} of {n}" in lines[i]
        else:
            assert "PASS" in lines[i]
            assert f"{tallies[leg]['PASS']} of {n}" in lines[i]
    # no aggregate count precedes the per-leg lines
    head = "\n".join(lines[: _lead_line(lines, legs[0])])
    assert str(sum(sum(t.values()) for t in tallies.values())) not in head.replace(
        phase34_report.PUBLISHED, ""
    )
    admission_line = next(i for i, line in enumerate(lines) if line.startswith("Admission: "))
    assert _lead_line(lines, legs[-1]) < admission_line < first_reason
    for reason in reasons:
        assert _norm_in(f'> "{reason}"', block), reason


def test_lead_title_has_no_underscore_and_anchor_matches(records, block):
    b = phase34_report.Bindings(records)
    title = b["derived.report_title"]
    assert "_" not in title
    assert records["admission"]["admission"]["verdict"] in title
    for leg in _legs(records):
        assert b[f"derived.leg_label.{leg}"] in title
    assert b["derived.report_anchor"] == phase28_report._github_anchor(title)
    assert block.startswith(f"\n## {title}\n")


def test_n64_is_not_measured_never_held(records, block, glance):
    tallies = records["frontier"]["verdicts"]["tallies_by_leg"]
    refused = [
        leg
        for leg in _legs(records)
        if all(v == 0 for k, v in tallies[leg].items() if k != "REFUSED")
    ]
    assert refused == sorted(records["frontier"]["verdicts"]["leg_refusals"])
    lines = block.splitlines()
    for leg in refused:
        assert "NOT MEASURED" in lines[_lead_line(lines, leg)]
        assert _norm_in(records["frontier"]["verdicts"]["leg_refusals"][leg], block)
    for text in (block, glance):
        assert "mitigation held" not in text.lower()
        assert "never exercised" not in text.lower()
    for template in _TEMPLATES:
        prose = _PLACEHOLDER.sub("", template.read_text(encoding="utf-8"))
        assert not re.search(r"\bheld\b", prose, re.I), template


# ---- (4) the comparison is the record's rows (D-06) -------------------------------------------


def test_comparison_table_is_the_record_rows(records, block):
    table = phase34_report.Bindings(records)["table.condition_c_vs_v4"]
    assert table in block
    rows = records["frontier"]["verdicts"]["condition_c_vs_v4"]["rows"]
    assert len(table.splitlines()) - 2 == len(rows)
    for row in rows:
        assert f"| {row['v5_key']} |" in table, row["v5_key"]
    assert _norm_in(records["frontier"]["verdicts"]["condition_c_vs_v4"]["notes"], block)
    assert "| null |" in table  # the refused leg's cleared_c is rendered, not blanked


def test_no_figures(block, glance):
    assert "![" not in block and "![" not in glance


def test_templates_use_only_v5_prefixes():
    for template in _TEMPLATES:
        names = _PLACEHOLDER.findall(template.read_text(encoding="utf-8"))
        assert names, template
        bad = sorted({n for n in names if n.partition(".")[0] not in _PREFIXES})
        assert bad == [], (template, bad)


def test_unknown_prefix_never_reaches_the_v4_dispatch(records):
    b = phase34_report.Bindings(records)
    for key in ("frontier.nonexistent", "quote.anything", "const.x", "canary.summary"):
        with pytest.raises(KeyError):
            b[key]


# ---- (5) provenance (carried D-21) ------------------------------------------------------------


def test_provenance_digests_recompute_from_bytes(loaded, block):
    records, digests = loaded
    for name, rel in phase34_report.RECORDS.items():
        raw = (_ROOT / rel).read_bytes()
        assert digests[name] == (hashlib.sha256(raw).hexdigest(), len(raw)), name
    assert records["admission"]["frontier"]["sha256"] == digests["frontier"][0]
    assert records["admission"]["frontier"]["path"] == phase34_report.RECORDS["frontier"]
    for name in ("frontier", "admission"):
        assert f"| {digests[name][0]} | {digests[name][1]} |" in block, name
    ledger = records["ledger"]
    row = (
        f"| {phase34_report.RECORDS['ledger']} (`rows` only) | "
        f"{phase28_report.ledger_rows_digest(ledger)} | "
        f"{phase28_report.ledger_frozen_bytes(ledger)} | — |"
    )
    assert row in block


def test_ledger_provenance_is_invariant_under_close(loaded):
    records, digests = loaded
    closed = copy.deepcopy(records)
    closed["ledger"]["close"]["ci_run"] = "https://example.invalid/actions/runs/123456789"
    for fn in (phase28_report.ledger_rows_digest, phase28_report.ledger_frozen_bytes):
        assert fn(closed["ledger"]) == fn(records["ledger"])
    before = phase34_report.Bindings(records, digests)["table.sources"]
    after = phase34_report.Bindings(closed, digests)["table.sources"]
    assert before == after


# ---- (6) torch-free, clock-free, no planning read ---------------------------------------------


def test_renderer_imports_without_torch_in_a_fresh_interpreter():
    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import phase34_report; "
        "print('torch' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=_ROOT, capture_output=True, text=True, check=True
    )
    assert out.stdout.split() == ["False"], out.stdout


def test_renderer_has_no_clock_head_or_planning_read():
    tree = ast.parse(_RENDERER.read_text(encoding="utf-8"))
    clocks = [
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in {"today", "now", "utcnow"}
    ]
    assert not clocks, clocks
    strings = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and any(word in node.value for word in ("rev-parse", ".planning/"))
    ]
    assert not strings, strings


# ---- (7) the frozen v4.0 block (D-03) ---------------------------------------------------------


def test_v4_block_still_checks_and_engine_is_untouched():
    assert phase28_report.check() == 0
    diff = subprocess.run(
        ("git", "diff", "--quiet", "HEAD", "--", "scripts/phase28_report.py"), cwd=_ROOT
    )
    assert diff.returncode == 0


def test_rendered_blocks_pass_the_docs_number_rules(block, glance):
    for text in (block, glance):
        assert not re.search(r"\b0(\.0+)?%", text)
    for number in ("0.3483", "8.52417066884246", "3.229"):
        assert number not in glance, number
    assert "\n## " not in glance
    bullets = [line for line in glance.splitlines() if line.startswith("- ")]
    assert len(bullets) == 1 and bullets[0].startswith("- **v5.0 — "), bullets
    anchor = phase34_report.Bindings(phase34_report.load()[0])["derived.report_anchor"]
    assert f"(docs/REPORT.md#{anchor})" in glance


# =================================================================================================
# (8) THE INSTALLED BLOCKS (plan 34-05; D-02, D-03, carried D-17/D-20/D-24). RED while the PHASE34
# sentinels are absent ("occurs 0 time(s)"), GREEN once `write` has run.
# =================================================================================================

_REPORT_REL = "docs/REPORT.md"
_README_REL = "README.md"


def test_report_sentinels_occur_exactly_once():
    _span(_REPORT_REL, phase34_report.REPORT_STEM)


def test_glance_sentinels_occur_exactly_once():
    _span(_README_REL, phase34_report.GLANCE_STEM)


def test_report_block_is_byte_identical():
    committed = _span(_REPORT_REL, phase34_report.REPORT_STEM)
    rendered = phase34_report.render_report()
    assert committed == rendered, _unified(committed, rendered)


def test_glance_block_is_byte_identical():
    committed = _span(_README_REL, phase34_report.GLANCE_STEM)
    rendered = phase34_report.render_glance()
    assert committed == rendered, _unified(committed, rendered)


def test_placement_report_block_follows_the_v4_block():
    span = _span(_REPORT_REL, phase34_report.REPORT_STEM)
    text = (_ROOT / _REPORT_REL).read_text(encoding="utf-8")
    begin34 = _markers(phase34_report.REPORT_STEM)[0]
    end28 = _markers(phase28_report.REPORT_STEM)[1]
    assert text.index(begin34) > text.index(end28)
    headings = [line for line in span.splitlines() if line.startswith("## ")]
    assert len(headings) == 1, headings


def test_placement_glance_sits_directly_above_the_v4_glance():
    span = _span(_README_REL, phase34_report.GLANCE_STEM)
    text = (_ROOT / _README_REL).read_text(encoding="utf-8")
    end34 = _markers(phase34_report.GLANCE_STEM)[1]
    begin28 = _markers(phase28_report.GLANCE_STEM)[0]
    assert text.count(end34 + "\n" + begin28) == 1
    assert "\n## " not in span and not span.startswith("## "), span


def _install_inverse(relative_path, text, stem):
    """Remove the stem's block by the exact inverse of `write` (REPORT: EOF append with a leading
    newline; README: inserted directly above the v4.0 anchor)."""
    begin, end = _markers(stem)
    for sentinel in (begin, end):
        found = text.count(sentinel)
        assert found == 1, f"{relative_path}: {sentinel} occurs {found} time(s); exactly one"
    span = text.split(begin, 1)[1].split(end, 1)[0]
    block = begin + span + end + "\n"
    if relative_path == _REPORT_REL:
        block = "\n" + block
    assert text.count(block) == 1, relative_path
    stripped = text.replace(block, "", 1)
    assert begin not in stripped and end not in stripped, relative_path
    return stripped


_STEMS = ((_REPORT_REL, phase34_report.REPORT_STEM), (_README_REL, phase34_report.GLANCE_STEM))


@pytest.mark.parametrize(("relative_path", "stem"), _STEMS)
def test_install_deleted_nothing(relative_path, stem):
    """History-based (a later sanctioned edit never reddens it): the OLDEST commit whose blob holds
    the BEGIN sentinel, minus its block, equals its parent's blob. Before any such commit exists the
    working tree stands in for it and HEAD for its parent."""
    begin = _markers(stem)[0]
    pub = None
    for revision in _git("log", "--format=%H", "--", relative_path).split():
        if begin in _git("show", f"{revision}:{relative_path}"):
            pub = revision  # keep walking: the last match is the oldest
    if pub is None:
        text = (_ROOT / relative_path).read_text(encoding="utf-8")
        parent = _git("show", f"HEAD:{relative_path}")
    else:
        text = _git("show", f"{pub}:{relative_path}")
        parent = _git("show", f"{pub}~1:{relative_path}")
    assert _install_inverse(relative_path, text, stem) == parent


def _tmp_docs34(tmp_path, monkeypatch, report_text, readme_text):
    tmp_report, tmp_readme = tmp_path / "REPORT.md", tmp_path / "README.md"
    tmp_report.write_text(report_text, encoding="utf-8")
    tmp_readme.write_text(readme_text, encoding="utf-8")
    monkeypatch.setattr(phase34_report, "REPORT_PATH", tmp_report)
    monkeypatch.setattr(phase34_report, "README_PATH", tmp_readme)
    return tmp_report, tmp_readme


def test_write_refuses_once_installed(tmp_path, monkeypatch):
    for relative_path, stem in _STEMS:
        _span(relative_path, stem)  # installed, else this is vacuous
    published_report = (_ROOT / _REPORT_REL).read_bytes()
    published_readme = (_ROOT / _README_REL).read_bytes()
    tmp_report, tmp_readme = _tmp_docs34(
        tmp_path, monkeypatch, published_report.decode("utf-8"), published_readme.decode("utf-8")
    )
    with pytest.raises(SystemExit, match="refused"):
        phase34_report.main(["write"])
    assert tmp_report.read_bytes() == published_report
    assert tmp_readme.read_bytes() == published_readme


def test_write_installs_pre_publish_then_refuses(tmp_path, monkeypatch):
    texts = {rel: (_ROOT / rel).read_text(encoding="utf-8") for rel, _ in _STEMS}
    stripped = {rel: _install_inverse(rel, texts[rel], stem) for rel, stem in _STEMS}
    tmp_report, tmp_readme = _tmp_docs34(
        tmp_path, monkeypatch, stripped[_REPORT_REL], stripped[_README_REL]
    )
    assert phase34_report.main(["write"]) == 0
    assert tmp_report.read_bytes() == (_ROOT / _REPORT_REL).read_bytes()
    assert tmp_readme.read_bytes() == (_ROOT / _README_REL).read_bytes()
    with pytest.raises(SystemExit, match="refused"):
        phase34_report.main(["write"])
    assert tmp_report.read_bytes() == (_ROOT / _REPORT_REL).read_bytes()
    assert tmp_readme.read_bytes() == (_ROOT / _README_REL).read_bytes()


def test_published_date_is_pinned_not_clocked(block):
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", phase34_report.PUBLISHED)
    title = next(line for line in block.splitlines() if line.startswith("## "))
    assert phase34_report.PUBLISHED in title, title


def test_install_glance_refuses_without_exactly_one_v4_anchor(tmp_path):
    readme = (_ROOT / _README_REL).read_text(encoding="utf-8")
    anchor = _markers(phase28_report.GLANCE_STEM)[0]
    begin34, end34 = _markers(phase34_report.GLANCE_STEM)
    if begin34 in readme:
        readme = _install_inverse(_README_REL, readme, phase34_report.GLANCE_STEM)
    assert readme.count(anchor) == 1
    tmp_readme = tmp_path / "README.md"
    tmp_readme.write_text(readme.replace(anchor, "", 1), encoding="utf-8")
    before = tmp_readme.read_bytes()
    with pytest.raises(SystemExit, match="exactly once"):
        phase34_report.install_glance(tmp_readme, phase34_report.GLANCE_STEM, "- **x**\n")
    assert tmp_readme.read_bytes() == before
    assert end34 not in tmp_readme.read_text(encoding="utf-8")
