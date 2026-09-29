"""Phase 34 report renderer — the v5.0 block over the frozen Phase 28 engine (D-01).

``scripts/phase28_report.py`` is imported, never edited: its ``resolve``, ``_fmt``, ``_Template``,
``_table``, ``_cell``, ``install``, ``_span``, ``_markers``, ``_github_anchor``, ledger digests and
ledger tables are reused, and its ``Bindings`` is subclassed over THIS module's records, derived
values, tables and paths. The subclass never falls through to phase28's v4.0 dispatch: an unknown
prefix raises ``KeyError``.

Binding prefixes: ``meta`` (the pinned ``PUBLISHED`` stamp) · ``frontier`` / ``admission`` /
``ledger`` (record field paths, ``[]``-indexed; ``ledger.row.<ID>.<key>`` and
``ledger.count.<DISPOSITION>`` as in phase28) · ``derived.<name>`` (functions of record fields) ·
``table.<name>`` (Markdown tables over record rows) · ``path.<name>`` (repo paths). Nothing else.

``write`` installs both blocks and is PRE-PUBLISH ONLY (carried D-20): once the publishing commit
lands, the block is frozen and corrections are dated continuations through ``scripts/_addendum.py``.
``check`` re-renders and diffs against the committed spans.

``CONTRACT`` is a post-hoc publication contract WRITTEN AFTER THE RESULTS. It is not a
pre-registration: it lists the record fields the published block must bind, chosen once the
records were already committed. A late pre-registration would be refused by phase29_prereg's
ancestry guard and would claim something false (D-08).
"""

import difflib
import hashlib
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in ("scripts", "src"):
    if str(_ROOT / _sub) not in sys.path:
        sys.path.insert(0, str(_ROOT / _sub))

import phase28_report as p28  # noqa: E402  (scripts/ is not a package)

# ---- pinned constants (carried D-24: a clock in the template breaks byte-identity) -------------
PUBLISHED = "2026-09-28"
REPORT_STEM = "PHASE34-REPORT"
GLANCE_STEM = "PHASE34-GLANCE"
REPORT_PATH = _ROOT / "docs/REPORT.md"
README_PATH = _ROOT / "README.md"
TEMPLATE_REPORT = _ROOT / "scripts/phase34_report.md.tmpl"
TEMPLATE_GLANCE = _ROOT / "scripts/phase34_glance.md.tmpl"
ANCHOR_BEGIN = p28._markers(p28.GLANCE_STEM)[0]

# The key MUST be "ledger": phase28's ledger helpers read records["ledger"].
RECORDS = {
    "frontier": "results/phase32_frontier.json",
    "admission": "results/phase33_admission.json",
    "ledger": "results/phase34_ledger.json",
}
GIT_FIELD = {"frontier": "provenance.git_sha", "admission": "provenance.git_sha"}

PATHS = {
    "renderer": "scripts/phase34_report.py",
    "template_report": "scripts/phase34_report.md.tmpl",
    "template_glance": "scripts/phase34_glance.md.tmpl",
    "report_test": "tests/test_phase34_report.py",
    "frontier": RECORDS["frontier"],
    "admission": RECORDS["admission"],
    "ledger": RECORDS["ledger"],
    "recipe": "scripts/phase30_points.py",
    "refusal_surface": "scripts/phase33_admission.py",
}

_prove = p28._prove


# ---- records ----------------------------------------------------------------------------------


def load():
    """Parse every record from bytes; ``(records, {name: (sha256, n)})``; prove the chain."""
    records, digests = {}, {}
    for name, rel in RECORDS.items():
        raw = (_ROOT / rel).read_bytes()
        records[name] = json.loads(raw)
        digests[name] = (hashlib.sha256(raw).hexdigest(), len(raw))
    chain = records["admission"]["frontier"]
    _prove(
        chain["sha256"] == digests["frontier"][0] and chain["path"] == RECORDS["frontier"],
        "admission.frontier does not name the committed frontier bytes (carried D-21)",
    )
    return records, digests


def _null_cell(value):
    if value is None:
        return "null"
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        value = "; ".join(value)
    return p28._cell(value)


def _verdicts(records):
    return records["frontier"]["verdicts"]


def _capacity(leg):
    return int(leg.split("_n", 1)[1])


def _legs(records):
    return sorted(_verdicts(records)["tallies_by_leg"], key=_capacity)


def _control(records, leg):
    return p28.resolve(records["frontier"], "verdicts.control_readings." + leg)


def _by_leg(records, leg):
    rows = [
        v for v in _verdicts(records)["condition_c_vs_v4"]["by_leg"].values() if v["leg"] == leg
    ]
    _prove(len(rows) == 1, f"condition_c_vs_v4.by_leg has {len(rows)} entries for {leg}")
    return rows[0]


def _all_refused(tallies):
    return all(v == 0 for k, v in tallies.items() if k != "REFUSED")


def _outcome(tallies):
    total = sum(tallies.values())
    if _all_refused(tallies):
        return f"REFUSED {tallies['REFUSED']} of {total}"
    parts = [f"PASS {tallies['PASS']} of {total}"]
    parts += [f"{k} {v} of {total}" for k, v in tallies.items() if k != "PASS" and v]
    return ", ".join(parts)


# ---- derived ----------------------------------------------------------------------------------


def _leg_label(leg):
    return leg.replace("_", " ")


def _known_leg_label(records, leg):
    if leg not in _legs(records):
        raise KeyError(leg)
    return _leg_label(leg)


def _report_title(records):
    tallies = _verdicts(records)["tallies_by_leg"]
    legs = "; ".join(f"{_leg_label(leg)} {_outcome(tallies[leg])}" for leg in _legs(records))
    verdict = records["admission"]["admission"]["verdict"]
    return f"v5.0 — admission {verdict}: {legs} (recorded {PUBLISHED})"


def _lead_lines(records):
    tallies = _verdicts(records)["tallies_by_leg"]
    lines = []
    for leg in _legs(records):
        line = f"- `{leg}`: {_outcome(tallies[leg])}"
        if _all_refused(tallies[leg]):
            line += (
                f" — NOT MEASURED: refused under `{_by_leg(records, leg)['v5_state']}` "
                f"(`verdicts.leg_refusals.{leg}`, quoted below)"
            )
        lines.append(line + ".")
    return "\n".join(lines)


def _recall(records, spec):
    leg, _, tier = spec.rpartition(".")
    k, n = _control(records, leg)["recall_counts"][tier]
    return f"{k}/{n}"


def _ledger_count(**where):
    return lambda r: str(len(p28._ledger_filter(r, **where)))


DERIVED = {
    "report_title": _report_title,
    "report_anchor": lambda r: p28._github_anchor(_report_title(r)),
    "lead_lines": _lead_lines,
    "admission_reasons_quoted": lambda r: "\n".join(
        f'> "{reason}"' for reason in r["admission"]["admission"]["reasons"]
    ),
    "limitation_legs": lambda r: "\n".join(
        f'> "{r["admission"]["limitation"]["legs"][leg]}"' for leg in _legs(r)
    ),
    "relearn_scope_count": lambda r: str(len(r["admission"]["scope"]["relearn_point_keys"])),
    "ledger_total": lambda r: str(len(r["ledger"]["rows"])),
    "ledger_named_limitation_count": _ledger_count(disposition="NAMED-LIMITATION"),
    "ledger_v5_count": _ledger_count(milestone="v5.0"),
    # phase28's still-open rows, carried by reference: every row not of milestone v5.0.
    "ledger_by_reference_count": lambda r: str(
        sum(row["milestone"] != "v5.0" for row in r["ledger"]["rows"])
    ),
}

# Parametrized derived names: ``derived.<name>.<arg>``.
DERIVED_BY_ARG = {
    "leg_label": _known_leg_label,
    "leg_total": lambda r, leg: str(sum(_verdicts(r)["tallies_by_leg"][leg].values())),
    "recall": _recall,
}


# ---- tables -----------------------------------------------------------------------------------


def _condition_c_vs_v4(records):
    rows = [
        (
            _null_cell(row["ratio"]),
            _null_cell(row["v4_key"]),
            _null_cell(row["v4"]["verdict"]),
            _null_cell(row["v4"]["label"]),
            _null_cell(row["v4"]["quoted_reasons"]),
            _null_cell(row["v5_key"]),
            _null_cell(row["v5"]["state"]),
            _null_cell(row["v5"]["verdict"]),
            _null_cell(row["v5"]["cleared_c"]),
        )
        for row in _verdicts(records)["condition_c_vs_v4"]["rows"]
    ]
    return p28._table(
        (
            "ratio",
            "v4.0 key",
            "v4.0 verdict",
            "v4.0 (c) label",
            "v4.0 quoted_reasons",
            "v5.0 key",
            "v5.0 state",
            "v5.0 verdict",
            "v5.0 cleared_c",
        ),
        rows,
    )


def _condition_c_by_leg(records):
    rows = []
    for leg in _legs(records):
        b = _by_leg(records, leg)
        rows.append(
            (
                leg,
                b["twin"],
                f"{b['tk']}/{b['tn']}",
                f"{b['hk']}/{b['hn']}",
                b["v4_state"],
                b["v5_state"],
                b["k5"],
                b["k6"],
            )
        )
    return p28._table(("leg", "twin", "tk/tn", "hk/hn", "v4_state", "v5_state", "k5", "k6"), rows)


def _control_table(records):
    rows = []
    for leg in _legs(records):
        c = _control(records, leg)
        rows.append(
            (
                leg,
                c["source"],
                c["unlearnable"],
                _recall(records, leg + ".taught"),
                _recall(records, leg + ".heldout"),
                c["adapter_off"],
                c["adapter_on"],
            )
        )
    return p28._table(
        ("leg", "source", "unlearnable", "taught", "heldout", "adapter_off", "adapter_on"), rows
    )


def _withheld_claims(records):
    rows = [
        (r["id"], r["reason"]) for r in p28._ledger_filter(records, disposition="NAMED-LIMITATION")
    ]
    refusals = _verdicts(records)["leg_refusals"]
    rows += [("verdicts.leg_refusals." + leg, refusals[leg]) for leg in refusals]
    rows += [
        (f"admission.reasons[{i}]", reason)
        for i, reason in enumerate(records["admission"]["admission"]["reasons"])
    ]
    return p28._table(("withheld", "why"), rows)


def _sources(records, digests):
    rows = []
    for name, rel in RECORDS.items():
        sha, size = digests[name]
        if name == "ledger":
            rows.append(
                (
                    rel + " (`rows` only)",
                    p28.ledger_rows_digest(records[name]),
                    p28.ledger_frozen_bytes(records[name]),
                    "—",
                )
            )
        else:
            rows.append((rel, sha, size, p28.resolve(records[name], GIT_FIELD[name])))
    return p28._table(("source", "sha256", "bytes", "record-carried git_sha"), rows)


TABLES = {
    "condition_c_vs_v4": _condition_c_vs_v4,
    "condition_c_by_leg": _condition_c_by_leg,
    "control_readings": _control_table,
    "withheld_claims": _withheld_claims,
    "named_limitations": p28._named_limitations,
    "ledger_by_disposition": p28._ledger_by_disposition,
}


# ---- the post-hoc publication contract (D-08) — NOT a pre-registration ------------------------

CONTRACT = (
    ("frontier.verdicts.tallies_by_leg", "the per-leg lead: one line per leg, no aggregate (D-04)"),
    ("frontier.verdicts.leg_refusals", "the refused leg is quoted verbatim, not measured (D-05)"),
    ("frontier.verdicts.control_readings", "each leg's own control, bound not typed (D-05)"),
    # verdicts.condition_c_vs_v4, field by field, so dropping its table is uncovered (D-06).
    ("frontier.verdicts.condition_c_vs_v4.rows", "the per-ratio comparison is the record's rows"),
    ("frontier.verdicts.condition_c_vs_v4.by_leg", "the per-leg comparison summary"),
    ("frontier.verdicts.condition_c_vs_v4.notes", "the record's notes travel with the table"),
    ("frontier.verdicts.condition_c_vs_v4.statement", "the comparison's own statement, quoted"),
    ("admission.admission.verdict", "the admission verdict follows the per-leg lead (D-04)"),
    ("admission.admission.reasons", "the admission reasons, quoted verbatim in order (D-04)"),
    ("admission.limitation", "the relearning limitation and its surface (D-09)"),
    ("admission.scope", "the relearning scope rule and its empty point set (D-09)"),
)

# table./derived. binding -> the CONTRACT paths it renders.
COVERED_BY = {
    "derived.lead_lines": ("frontier.verdicts.tallies_by_leg",),
    "derived.report_title": ("frontier.verdicts.tallies_by_leg", "admission.admission.verdict"),
    "derived.admission_reasons_quoted": ("admission.admission.reasons",),
    "derived.limitation_legs": ("admission.limitation",),
    "derived.relearn_scope_count": ("admission.scope",),
    "table.control_readings": ("frontier.verdicts.control_readings",),
    "table.condition_c_vs_v4": ("frontier.verdicts.condition_c_vs_v4.rows",),
    "table.condition_c_by_leg": ("frontier.verdicts.condition_c_vs_v4.by_leg",),
    "table.withheld_claims": ("frontier.verdicts.leg_refusals", "admission.admission.reasons"),
}


# ---- bindings + template ----------------------------------------------------------------------


class Bindings(p28.Bindings):
    """``${prefix.rest}`` -> string over the v5.0 records. Unknown prefix raises ``KeyError``."""

    def __getitem__(self, key):
        prefix, _, rest = key.partition(".")
        if prefix == "meta" and rest == "published":
            return PUBLISHED
        if prefix == "ledger" and rest.partition(".")[0] in ("row", "count"):
            return super().__getitem__(key)
        if prefix in RECORDS:
            return p28._fmt(p28.resolve(self.records[prefix], rest))
        if prefix == "derived":
            if rest in DERIVED:
                return DERIVED[rest](self.records)
            name, _, arg = rest.partition(".")
            if name in DERIVED_BY_ARG and arg:
                return DERIVED_BY_ARG[name](self.records, arg)
            raise KeyError(key)
        if prefix == "table":
            if rest == "sources":
                _prove(self.digests is not None, "table.sources needs the load() digests")
                return _sources(self.records, self.digests)
            return TABLES[rest](self.records)
        if prefix == "path":
            return PATHS[rest]
        raise KeyError(key)


def render(template_path, records, digests):
    text = pathlib.Path(template_path).read_text(encoding="utf-8")
    body = p28._Template(text).substitute(Bindings(records, digests))
    return "\n" + body.strip("\n") + "\n"


def render_report():
    return render(TEMPLATE_REPORT, *load())


def render_glance():
    return render(TEMPLATE_GLANCE, *load())


# ---- install / check --------------------------------------------------------------------------


def install_glance(path, stem, block):
    """Insert ``block`` between the stem's sentinels directly ABOVE phase28's glance BEGIN (D-02).

    PRE-PUBLISH ONLY. Zero deletions: the prefix and the suffix are proved byte-identical on the
    produced text.
    """
    path = pathlib.Path(path)
    begin, end = p28._markers(stem)
    text = path.read_text(encoding="utf-8")
    _prove(
        begin not in text and end not in text,
        f"write refused: {stem} is already (partly) installed in {path} (carried D-20)",
    )
    _prove(text.count(ANCHOR_BEGIN) == 1, f"{path}: {ANCHOR_BEGIN} must occur exactly once")
    i = text.index(ANCHOR_BEGIN)
    updated = text[:i] + begin + block + end + "\n" + text[i:]
    _prove(
        updated[:i] == text[:i] and updated.endswith(text[i:]) and block in updated,
        f"the rewritten {path} does not keep its prefix and suffix byte-identical",
    )
    path.write_text(updated, encoding="utf-8")
    return updated


def check():
    """Re-render and compare with the committed spans; 1 on drift or absent sentinels."""
    status = 0
    for path, stem, rendered in (
        (REPORT_PATH, REPORT_STEM, render_report()),
        (README_PATH, GLANCE_STEM, render_glance()),
    ):
        committed = p28._span(path, stem)
        rel = path.relative_to(_ROOT)
        if committed is None:
            print(f"[phase34_report] {rel}: {stem} sentinels absent (pre-publish state)")
            status = 1
        elif committed != rendered:
            print(f"[phase34_report] {rel}: {stem} block drifted")
            sys.stdout.writelines(
                difflib.unified_diff(
                    committed.splitlines(True), rendered.splitlines(True), "committed", "rendered"
                )
            )
            status = 1
    return status


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = "usage: phase34_report.py render (--stdout report|glance | --out DIR) | write | check"
    if argv[:1] == ["check"]:
        return check()
    if argv[:1] == ["write"]:
        for path, stem in ((REPORT_PATH, REPORT_STEM), (README_PATH, GLANCE_STEM)):
            text = path.read_text(encoding="utf-8")
            _prove(
                not any(m in text for m in p28._markers(stem)),
                f"write refused: {stem} already present in {path} (carried D-20)",
            )
        report, glance = render_report(), render_glance()
        p28.install(REPORT_PATH, REPORT_STEM, report)
        install_glance(README_PATH, GLANCE_STEM, glance)
        print("[phase34_report] installed both blocks (pre-publish only, carried D-20)")
        return 0
    if argv[:2] == ["render", "--stdout"] and argv[2:3] in (["report"], ["glance"]):
        sys.stdout.write(render_report() if argv[2] == "report" else render_glance())
        return 0
    if argv[:2] == ["render", "--out"] and len(argv) == 3:
        out = pathlib.Path(argv[2])
        out.mkdir(parents=True, exist_ok=True)
        (out / "phase34_report.md").write_text(render_report(), encoding="utf-8")
        (out / "phase34_glance.md").write_text(render_glance(), encoding="utf-8")
        print(f"[phase34_report] wrote {out / 'phase34_report.md'} and {out / 'phase34_glance.md'}")
        return 0
    print(usage, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
