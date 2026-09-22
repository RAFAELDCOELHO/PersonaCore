"""Phase 28 report renderer — every number in the published block is ADDRESSED, never typed.

The two templates (``scripts/phase28_report.md.tmpl`` for ``docs/REPORT.md``,
``scripts/phase28_glance.md.tmpl`` for ``README.md``) carry prose and ``${dotted.binding}``
placeholders and nothing else. This module reads the committed records DIRECTLY (D-21: no derived
extract, no cache), builds one mapping over them, and fills the templates with
``string.Template.substitute`` so a missing binding raises ``KeyError`` instead of rendering blank
(D-16, D-23's rule: an unresolvable path is RED, never a licence to paraphrase around it).

Binding prefixes: ``meta`` (the pinned ``PUBLISHED`` stamp, D-24) · ``frontier`` / ``canary`` /
``admission`` / ``sigma_zero`` / ``cost`` / ``control_floor`` (record field paths, ``[]``-indexed) ·
``const.<module>.<NAME>`` (module constants; ``phase18_extraction.K`` is read by AST, never
imported) · ``derived.<name>`` (functions whose inputs are record fields) · ``table.<name>``
(Markdown tables over record rows) · ``quote.<name>`` (verbatim text, proved present in its source
at render time) · ``slice.<name>`` / ``blockquote.<name>`` (anchored slices of committed ``.md``
files) · ``path.<name>`` (repo paths) · ``ledger.row.<ID>.<key>`` / ``ledger.count.<DISPOSITION>``.

``write`` installs both blocks between sentinels and is PRE-PUBLISH ONLY (D-20: once the
publishing commit lands, the block is frozen and corrections are dated continuations through
``scripts/_addendum.py``). ``check`` re-renders and diffs against the committed spans (T-28-02).

Threats: T-28-01 (records read as bytes, sha256 + size recorded in the provenance table),
T-28-03 (numbers addressed, never typed), T-28-06 (the gitignored sweep log is never read — the
log line is quoted from ``verdicts.adversarial_no_replay``), T-28-13 (no clock, no HEAD SHA).
"""

import ast
import collections.abc
import difflib
import hashlib
import json
import pathlib
import re
import string
import subprocess
import sys

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

from personacore.privacy import accountant  # noqa: E402

# ---- pinned constants (D-24: a clock in the template breaks byte-identity by construction) ----
PUBLISHED = "2026-09-21"
REPORT_STEM = "PHASE28-REPORT"
GLANCE_STEM = "PHASE28-GLANCE"
REPORT_PATH = _ROOT / "docs/REPORT.md"
README_PATH = _ROOT / "README.md"
GLANCE_HEADING = "## Results at a glance"
TEMPLATE_REPORT = _ROOT / "scripts/phase28_report.md.tmpl"
TEMPLATE_GLANCE = _ROOT / "scripts/phase28_glance.md.tmpl"
EXPECTATION_COMMIT = "c673b4c"

RECORDS = {
    "frontier": "results/phase25_frontier.json",
    "canary": "results/phase26_canary.json",
    "admission": "results/phase27_admission.json",
    "sigma_zero": "results/phase23_sigma_zero.json",
    "cost": "results/phase23_cost.json",
    "control_floor": "results/phase23_control_floor.json",
    "ledger": "results/phase28_ledger.json",
}
OP_NOTE = "results/phase25_operational_note.md"
REQUIREMENTS = ".planning/REQUIREMENTS.md"
ROADMAP = ".planning/ROADMAP.md"
EXTRACTION_REPORT = "results/phase18_extraction_report.md"
ERASURE_REPORT = "results/phase19_erasure_report.md"
PHASE18_EXTRACTION = _ROOT / "scripts/phase18_extraction.py"

# Repo paths the templates name. Bound (``${path.<name>}``) rather than typed because a path such as
# ``scripts/phase28_report.py`` carries digits the D-19 template scan does not exempt.
PATHS = {
    "renderer": "scripts/phase28_report.py",
    "template_report": "scripts/phase28_report.md.tmpl",
    "template_glance": "scripts/phase28_glance.md.tmpl",
    "prereg_test": "tests/test_phase28_prereg.py",
    "report_test": "tests/test_phase28_report.py",
    "frontier": RECORDS["frontier"],
    "canary": RECORDS["canary"],
    "admission": RECORDS["admission"],
    "sigma_zero": RECORDS["sigma_zero"],
    "cost": RECORDS["cost"],
    "ledger": RECORDS["ledger"],
    "op_note": OP_NOTE,
    "figure_dp": "results/phase25_frontier_dp.png",
    "figure_adv": "results/phase25_frontier_adversarial.png",
    "privacy_pkg": "src/personacore/privacy/",
    "canary_script": "scripts/phase26_canary.py",
    "relearn_script": "scripts/phase27_relearn.py",
    "extraction_report": EXTRACTION_REPORT,
    "erasure_report": ERASURE_REPORT,
    "research_summary": ".planning/research/SUMMARY.md",
    "requirements": REQUIREMENTS,
    "roadmap": ROADMAP,
}

# The bracket point whose inputs feed the accountant at render time (D-06).
BRACKET_KEY = "dp_n8_sigma16p000000"
TARGET_EPSILON_FACT = 4.0
REPRODUCE_SIGMA = 16.0

# quote name -> (source, verbatim text). Source is "git:<sha>:<path>" or a HEAD-tracked path.
# Every quote is proved present in its source (under _prose.normalized) when it is bound.
_EXPECTATION_SOURCE = f"git:{EXPECTATION_COMMIT}:.planning/research/SUMMARY.md"
QUOTES = {
    "expectation_l8": (
        _EXPECTATION_SOURCE,
        "Under a fact-level unit the per-coordinate noise-to-signal ratio is `σ√d/L` = **72σ at "
        "L=8 facts** `[MEASURED, STACK]`, and reaching ε_fact ≤ 4 needs σ ≥ 15.3 `[MEASURED, this "
        "synthesis]` — a ratio near 1,100. Secret Sharer Table 3 is the direct precedent: "
        "per-record clipping destroyed single-record memorization at *every* ε tested including "
        "ε = 10⁹ `[LIT]`.",
    ),
    "expectation_threshold": (
        _EXPECTATION_SOURCE,
        "reaching ε_fact ≤ 4 needs σ ≥ 15.3 `[MEASURED, this synthesis]`",
    ),
    "expectation_lever": (
        _EXPECTATION_SOURCE,
        "So growing the lot is free privacy-wise and improves signal-to-noise linearly: L=8 → 72σ, "
        "L=64 → 9σ, L=576 → 1σ.",
    ),
    "req_23_12_retraction": (
        REQUIREMENTS,
        '**RETRACTED IN PLACE 2026-08-28 (plan 23-12).** The sentence above — *"Training is ~17 s '
        "per arm. **Evaluation costs ~1,010× training** — it is the binding constraint by three "
        'orders of magnitude, and no sweep density may be chosen without it."* — and the '
        "`h/point` column of the table above are left unamended as the record of what was "
        "believed when this preamble was written, per the UNIT-04 and DPSGD-03 precedents in this "
        "same document. Plan 23-11 measured both on real runs, and both are **FALSE**.",
    ),
    "v3_extraction_verdict": (
        EXTRACTION_REPORT,
        "**`LEAKAGE_DEMONSTRATED`** — returned by `null_result_is_admissible` and carried through "
        "`assemble_verdict` unchanged.",
    ),
    "v3_erasure_verdict": (
        ERASURE_REPORT,
        "**FAILURE** — returned by the committed `erasure_succeeded`, with its own reasons, "
        "neither recomputed nor paraphrased here:",
    ),
    "v3_ship_decision": (ERASURE_REPORT, "Phase 19 ship decision: DO NOT SHIP"),
}

# slice name -> (path, kind, anchor). kind: "heading" (anchor heading .. next "### "),
# "sentinels" (<!-- anchor-BEGIN --> .. <!-- anchor-END -->), "bullet" (line starting with anchor
# up to the next line starting "- " or a blank line).
SLICES = {
    "op_note_12_5c": (OP_NOTE, "heading", "### 12.5c"),
    "req_23_12_continuation": (REQUIREMENTS, "sentinels", "23-12-CONTINUATION"),
    "roadmap_v5": (ROADMAP, "bullet", "- 🔮 **v5.0"),
}


def _prove(condition, message):
    """``SystemExit`` on a broken invariant — ``_addendum``'s register, one type for callers."""
    if not condition:
        raise SystemExit(f"[phase28_report] {message}")


def _markers(stem):
    return f"<!-- {stem}-BEGIN -->", f"<!-- {stem}-END -->"


def _github_anchor(heading_text):
    """GitHub's heading anchor rule, the one ``tests/test_phase15_docs.py`` derives links with."""
    return "".join(c for c in heading_text.lower().replace(" ", "-") if c.isalnum() or c == "-")


# ---- records ----------------------------------------------------------------------------------


def resolve(node, path):
    """Index ``node`` by a dotted path; ``KeyError(path)`` on absence — never ``.get``."""
    for part in path.split("."):
        try:
            node = node[int(part)] if isinstance(node, list) else node[part]
        except (KeyError, IndexError, TypeError, ValueError):
            raise KeyError(path) from None
    return node


def _fmt(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(v, (bool, int, float, str)) for v in value):
        return ", ".join(_fmt(v) for v in value)
    raise KeyError("unrenderable")


def load():
    """Parse every record from bytes; return ``(records, digests)`` with ``{name: (sha256, n)}``."""
    records, digests = {}, {}
    for name, rel in RECORDS.items():
        raw = (_ROOT / rel).read_bytes()
        records[name] = json.loads(raw)
        digests[name] = (hashlib.sha256(raw).hexdigest(), len(raw))
    return records, digests


def ledger_rows_digest(ledger):
    """sha256 over ``rows`` only — ``close`` stays outside so 28-07 can fill ``ci_run`` (D-38)."""
    return hashlib.sha256(
        json.dumps(ledger["rows"], sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _source_text(source):
    if source.startswith("git:"):
        _, sha, path = source.split(":", 2)
        return subprocess.run(
            ("git", "show", f"{sha}:{path}"), cwd=_ROOT, capture_output=True, text=True, check=True
        ).stdout
    return (_ROOT / source).read_text(encoding="utf-8")


def quote(name):
    source, text = QUOTES[name]
    _prove(
        _prose.normalized(text) in _prose.normalized(_source_text(source)),
        f"quote {name!r} is not present verbatim in {source}",
    )
    return text


def extract_slice(name):
    path, kind, anchor = SLICES[name]
    text = (_ROOT / path).read_text(encoding="utf-8")
    if kind == "heading":
        found = re.compile(rf"^{re.escape(anchor)}\b.*?(?=^### |\Z)", re.M | re.S).search(text)
        _prove(found is not None, f"slice {name!r}: heading {anchor!r} absent from {path}")
        return found.group(0).rstrip("\n")
    if kind == "sentinels":
        begin, end = _markers(anchor)
        _prove(text.count(begin) == 1 and text.count(end) == 1, f"slice {name!r}: sentinels")
        return text.split(begin, 1)[1].split(end, 1)[0].strip("\n")
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(anchor)]
    _prove(len(starts) == 1, f"slice {name!r}: {anchor!r} occurs {len(starts)} time(s) in {path}")
    out = [lines[starts[0]]]
    for line in lines[starts[0] + 1 :]:
        if line.startswith("- ") or not line.strip():
            break
        out.append(line)
    return "\n".join(out)


def _blockquote(text):
    return "\n".join(f"> {line}" if line.strip() else ">" for line in text.splitlines())


def _phase18_k():
    """``K`` from ``scripts/phase18_extraction.py`` by AST — the module is ancestry-frozen and
    imports torch, so it is read, never imported."""
    tree = ast.parse(PHASE18_EXTRACTION.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "K" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise KeyError("const.phase18_extraction.K")


_CONST_MODULES = {
    "mitigation_gate": mitigation_gate,
    "mitigation_budget": mitigation_budget,
    "mitigation_unit": mitigation_unit,
    "phase25_prereg": phase25_prereg,
    "phase26_prereg": phase26_prereg,
}


def _const(rest):
    module, _, path = rest.partition(".")
    if module == "phase18_extraction":
        _prove(path == "K", f"const.phase18_extraction.{path}: only K is read by AST")
        return _phase18_k()
    if module not in _CONST_MODULES:
        raise KeyError(f"const.{rest}")
    name, _, inner = path.partition(".")
    try:
        value = getattr(_CONST_MODULES[module], name)
    except AttributeError:
        raise KeyError(f"const.{rest}") from None
    return resolve(value, inner) if inner else value


# ---- derived values (each: one line on what it is and which record fields feed it) ------------


def _sigma_of(records, key):
    return records["frontier"]["points"][key]["sigma"]


def _noised_dp_rows(records):
    # admission.rows with arm == "dp" whose frontier point has sigma > 0 (D-02 line 2 — NOT
    # cleared_counts.b, which also counts the two sigma=0 controls and two adv_n8 points).
    return [
        r
        for r in records["admission"]["rows"]
        if r["arm"] == "dp" and _sigma_of(records, r["point_key"]) > 0
    ]


def _recall_fraction(records, leg, tier):
    # control_readings.<leg>.recall_counts.<tier> = [k, n] -> "k/n (k/n as repr float)"
    k, n = records["frontier"]["verdicts"]["control_readings"][leg]["recall_counts"][tier]
    return f"{k}/{n} ({k / n!r})"


def _sigma_for_eps4(records):
    # accountant.sigma_for(4.0, composed_steps, delta) with both inputs read from the bracket point;
    # refuses to render unless epsilon_for(16.0, ...) re-derives the record's epsilon (D-06).
    p = records["frontier"]["points"][BRACKET_KEY]
    steps, delta = p["composed_steps"], p["delta"]
    _prove(p["sigma"] == REPRODUCE_SIGMA, f"{BRACKET_KEY} sigma is {p['sigma']!r}")
    rederived = accountant.epsilon_for(REPRODUCE_SIGMA, steps, delta)
    _prove(
        rederived == p["epsilon"],
        f"accountant.epsilon_for({REPRODUCE_SIGMA!r}, {steps!r}, {delta!r}) = {rederived!r} is not "
        f"bit-identical to the record's epsilon {p['epsilon']!r}; the render refuses (D-06)",
    )
    return repr(accountant.sigma_for(TARGET_EPSILON_FACT, steps, delta))


def _adv_n64_range(records, field):
    # min-max over the six frontier.verdicts.refused_points of points[k].verdict.<field>
    values = [
        records["frontier"]["points"][k]["verdict"][field]
        for k in records["frontier"]["verdicts"]["refused_points"]
    ]
    return f"{min(values)!r}–{max(values)!r}"


def _ledger_filter(records, **where):
    return [r for r in records["ledger"]["rows"] if all(r[k] == v for k, v in where.items())]


def _capacity(records, leg):
    # the numeral after "n" in a frontier.arms entry ("dp_n64" -> "64")
    _prove(leg in records["frontier"]["arms"], f"{leg} is not in frontier.arms")
    return leg.split("_n", 1)[1]


def _report_title(records):
    branch = records["frontier"]["verdicts"]["capacity_branch"]
    return f"v4.0 — the published null: `{branch}` (recorded {PUBLISHED})"


DERIVED = {
    "noised_dp_total": lambda r: str(len(_noised_dp_rows(r))),
    "noised_dp_cleared_a": lambda r: str(sum(x["cleared_a"] for x in _noised_dp_rows(r))),
    "noised_dp_cleared_b": lambda r: str(sum(x["cleared_b"] for x in _noised_dp_rows(r))),
    "noised_dp_cleared_c": lambda r: str(sum(x["cleared_c"] for x in _noised_dp_rows(r))),
    "sigma_for_eps4": _sigma_for_eps4,
    "target_epsilon_fact": lambda r: repr(TARGET_EPSILON_FACT),
    "reproduce_sigma": lambda r: repr(REPRODUCE_SIGMA),
    # sigma_zero.deviation / sigma_zero.floor
    "sigma_zero_deviation_over_floor": lambda r: repr(
        r["sigma_zero"]["deviation"] / r["sigma_zero"]["floor"]
    ),
    # len(PUBLICATION_OBLIGATION) + len(PUBLICATION_OBLIGATION_CONTINUATION)
    "obligation_count": lambda r: str(
        len(phase25_prereg.PUBLICATION_OBLIGATION)
        + len(phase26_prereg.PUBLICATION_OBLIGATION_CONTINUATION)
    ),
    "adv_n64_dialogue_range": lambda r: _adv_n64_range(r, "point_dialogue_ppl_on"),
    "adv_n64_retention_range": lambda r: _adv_n64_range(r, "point_retention_ppl"),
    "adv_n64_refused_count": lambda r: str(len(r["frontier"]["verdicts"]["refused_points"])),
    "canary_audited_count": lambda r: str(len(r["canary"]["audited_point_keys"])),
    "ledger_total": lambda r: str(len(r["ledger"]["rows"])),
    "ledger_v3_tech_debt_count": lambda r: str(
        len(_ledger_filter(r, milestone="v3.0", category="tech-debt"))
    ),
    "ledger_v3_stale_stamp_count": lambda r: str(
        len(_ledger_filter(r, milestone="v3.0", category="stale-stamp"))
    ),
    "ledger_v3_count": lambda r: str(len(_ledger_filter(r, milestone="v3.0"))),
    "ledger_v4_count": lambda r: str(len(_ledger_filter(r, milestone="v4.0"))),
    "ledger_named_limitation_count": lambda r: str(
        len(_ledger_filter(r, disposition="NAMED-LIMITATION"))
    ),
    "n_arms": lambda r: str(len(r["frontier"]["arms"])),
    "capacity_n8": lambda r: _capacity(r, "dp_n8"),
    "capacity_n64": lambda r: _capacity(r, "dp_n64"),
    "report_title": _report_title,
    "report_anchor": lambda r: _github_anchor(_report_title(r)),
    "ledger_rows_sha256": lambda r: ledger_rows_digest(r["ledger"]),
    # first paragraph of the bracket point's own canary epsilon_sentence (the field is 7 kB with
    # blank lines; it cannot live in a table cell, so it is quoted once, beside its verdict)
    "canary_epsilon_sentence_bracket": lambda r: r["canary"]["points"][BRACKET_KEY][
        "epsilon_sentence"
    ].split("\n\n")[0],
    "control_has_no_epsilon_first_clause": lambda r: r["frontier"]["epsilon_report"][
        "control_has_no_epsilon"
    ].split(".")[0],
}
for _leg in ("dp_n8", "dp_n64", "adv_n8", "adv_n64"):
    for _tier in ("taught", "heldout"):
        DERIVED[f"recall_fraction.{_leg}.{_tier}"] = lambda r, leg=_leg, tier=_tier: (
            _recall_fraction(r, leg, tier)
        )


# ---- tables -----------------------------------------------------------------------------------


def _cell(value):
    return _fmt(value).replace("\n", " ").replace("|", "\\|")


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _epsilon_by_sigma(records):
    f, c = records["frontier"], records["canary"]
    keys = sorted(c["audited_point_keys"], key=lambda k: f["points"][k]["sigma"])
    rows = []
    for key in keys:
        p, cp = f["points"][key], c["points"][key]
        twin = key.replace("dp_n8_", "dp_n64_", 1)
        _prove(f["points"][twin]["sigma"] == p["sigma"], f"{twin} is not {key}'s twin")
        if p["epsilon"] is None:
            eps = f["epsilon_report"]["control_has_no_epsilon"].split(".")[0]
        else:
            eps = p["epsilon"]
        if cp["verdict"] is None:
            canary_verdict, reasons = cp["comparison"].split(":")[0], ""
        else:
            canary_verdict = cp["verdict"]["verdict"]
            reasons = "; ".join(cp["verdict"]["reasons"])
        tv = f["points"][twin]["verdict"]
        rows.append(
            (
                p["sigma"],
                eps,
                p["verdict"]["verdict"],
                tv["verdict"] if tv["verdict"] is not None else tv["early_return_reason"],
                canary_verdict,
                reasons,
            )
        )
    legs = f["arms"]
    return _table(
        (
            "σ",
            "ε (frontier)",
            f"gate verdict `{legs[0]}`",
            f"gate verdict `{legs[1]}`",
            "canary verdict",
            "canary reasons",
        ),
        rows,
    )


def _tallies_by_leg(records):
    t = records["frontier"]["verdicts"]["tallies_by_leg"]
    verdicts = ("PASS", "FAIL", "INCONCLUSIVE", "REFUSED")
    return _table(
        ("leg", *verdicts),
        [(leg, *(t[leg][v] for v in verdicts)) for leg in records["frontier"]["arms"]],
    )


def _cleared_by_leg(records):
    by_leg = records["admission"]["cleared_counts"]["by_leg"]
    return _table(
        ("leg", "cleared (a)", "cleared (b)", "cleared (c)"),
        [
            (leg, by_leg[leg]["a"], by_leg[leg]["b"], by_leg[leg]["c"])
            for leg in records["frontier"]["arms"]
        ],
    )


def _adv_points(records):
    f = records["frontier"]
    rows = []
    for key in f["point_keys"]:
        if not key.startswith("adv_"):
            continue
        v = f["points"][key]["verdict"]
        verdict = v["verdict"] if v["verdict"] is not None else v["early_return_reason"]
        # The (c) reasons — the ones the prose above the table describes; a REFUSED point carries
        # only its refusal, so that is what it shows. (a)'s tolerance sentence is not published
        # here: it carries a bare `0.0000%` that tests/test_phase18_docs.py's STAT-02 guard forbids.
        reasons = [r for r in v["reasons"] if r.startswith("(c)")] or v["reasons"][:1]
        rows.append((key, f["points"][key]["ratio"], verdict, "; ".join(reasons)))
    return _table(("point", "ratio", "verdict / early return", "reasons (c), or the refusal"), rows)


def _self_corrections(records):
    cost, sz = records["cost"], records["sigma_zero"]
    return _table(
        ("correction", "record", "as measured"),
        [
            (
                "23-12 retraction of the evaluation-cost premise",
                RECORDS["cost"],
                "eval/training ratio dp_n8 "
                f"{cost['ratios']['dp_n8']['eval_over_training_floor']!r}–"
                f"{cost['ratios']['dp_n8']['eval_over_training_ceiling']!r}, dp_n64 "
                f"{cost['ratios']['dp_n64']['eval_over_training_floor']!r}–"
                f"{cost['ratios']['dp_n64']['eval_over_training_ceiling']!r}; "
                f"{cost['projection_not_published']}",
            ),
            (
                "σ=0 diagnostic halt",
                RECORDS["sigma_zero"],
                f"{sz['verdict']}: reading {sz['reading']!r} vs control central "
                f"{sz['control_central_reading']!r}, deviation {sz['deviation']!r} = "
                f"{sz['deviation'] / sz['floor']!r} × floor {sz['floor']!r} "
                f"({sz['floor_pin_module']}::{sz['floor_pin_symbol']})",
            ),
        ],
    )


def _named_limitations(records):
    return _table(
        ("id", "milestone", "source", "reason", "evidence"),
        [
            (r["id"], r["milestone"], r["source"], r["reason"], r["evidence"])
            for r in _ledger_filter(records, disposition="NAMED-LIMITATION")
        ],
    )


def _withheld_claims(records):
    ex = records["frontier"]["verdicts"]["arm_existentials"]
    rows = [(r["id"], r["reason"]) for r in _ledger_filter(records, disposition="NAMED-LIMITATION")]
    rows += [("arm_existentials.dp", ex["dp"]), ("arm_existentials.adversarial", ex["adversarial"])]
    return _table(("withheld", "why"), rows)


def _ledger_by_disposition(records):
    return _table(
        ("disposition", "rows"),
        [
            (d, len(_ledger_filter(records, disposition=d)))
            for d in records["ledger"]["schema"]["dispositions"]
        ],
    )


def _sources(records, digests):
    git_field = {
        "frontier": "provenance.git_sha",
        "canary": "emitted_git_sha",
        "admission": "provenance.git_sha",
        "sigma_zero": "git_sha",
        "cost": "git_sha",
        "control_floor": "git_sha",
    }
    rows = []
    for name, rel in RECORDS.items():
        sha, size = digests[name]
        if name == "ledger":
            rows.append((rel + " (`rows` only)", ledger_rows_digest(records[name]), size, "—"))
        else:
            rows.append((rel, sha, size, resolve(records[name], git_field[name])))
    # Only FROZEN published sources are digested. The two .planning files quoted above are edited
    # at milestone close (RPT ticks, Phase 28 row), so a digest over them would break byte-identity
    # by construction; their quotes/slices are still proved verbatim at every render.
    for rel in (OP_NOTE, EXTRACTION_REPORT, ERASURE_REPORT):
        raw = (_ROOT / rel).read_bytes()
        rows.append((rel, hashlib.sha256(raw).hexdigest(), len(raw), "—"))
    return _table(("source", "sha256", "bytes", "record-carried git_sha"), rows)


def _build_pointers(records):
    return _table(
        ("build decision", "record", "module"),
        [
            (
                f"privacy unit `{mitigation_unit.PRIVACY_UNIT}`",
                "results/phase21_privacy_unit.json",
                "scripts/mitigation_unit.py",
            ),
            (
                "per-example clipping",
                "results/phase25_clip_calibration.json",
                "src/personacore/privacy/dpsgd.py",
            ),
            (
                "fact-aligned sampler",
                "results/phase21_multiplicity.json",
                "src/personacore/training/data.py",
            ),
            (
                "pre-registration as phase zero",
                "results/phase20_gate_coverage_correction.json",
                "scripts/mitigation_gate.py",
            ),
        ],
    )


TABLES = {
    "epsilon_by_sigma": _epsilon_by_sigma,
    "tallies_by_leg": _tallies_by_leg,
    "cleared_by_leg": _cleared_by_leg,
    "adv_points": _adv_points,
    "self_corrections": _self_corrections,
    "named_limitations": _named_limitations,
    "withheld_claims": _withheld_claims,
    "ledger_by_disposition": _ledger_by_disposition,
    "build_pointers": _build_pointers,
}


# ---- bindings + template ----------------------------------------------------------------------


class Bindings(collections.abc.Mapping):
    """``${prefix.rest}`` -> string. Unknown prefix or missing name raises ``KeyError``."""

    def __init__(self, records, digests=None):
        self.records = records
        self.digests = digests

    def __getitem__(self, key):
        prefix, _, rest = key.partition(".")
        if prefix == "meta" and rest == "published":
            return PUBLISHED
        if prefix == "ledger":
            kind, _, spec = rest.partition(".")
            if kind == "row":
                row_id, _, field = spec.partition(".")
                rows = _ledger_filter(self.records, id=row_id)
                if len(rows) != 1:
                    raise KeyError(key)
                return _fmt(rows[0][field])
            if kind == "count":
                _prove(spec in self.records["ledger"]["schema"]["dispositions"], f"{key}: domain")
                return str(len(_ledger_filter(self.records, disposition=spec)))
            raise KeyError(key)
        if prefix in RECORDS:
            return _fmt(resolve(self.records[prefix], rest))
        if prefix == "const":
            return _fmt(_const(rest))
        if prefix == "derived":
            return DERIVED[rest](self.records)
        if prefix == "table":
            if rest == "sources":
                _prove(self.digests is not None, "table.sources needs the load() digests")
                return _sources(self.records, self.digests)
            return TABLES[rest](self.records)
        if prefix == "path":
            return PATHS[rest]
        if prefix == "quote":
            return quote(rest)
        if prefix == "slice":
            return extract_slice(rest)
        if prefix == "blockquote":
            return _blockquote(extract_slice(rest))
        raise KeyError(key)

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0


class _Template(string.Template):
    braceidpattern = r"[A-Za-z_][A-Za-z0-9_.:<>/-]*"


def render(template_path, records, digests):
    text = pathlib.Path(template_path).read_text(encoding="utf-8")
    body = _Template(text).substitute(Bindings(records, digests))
    return "\n" + body.strip("\n") + "\n"


def render_report():
    records, digests = load()
    return render(TEMPLATE_REPORT, records, digests)


def render_glance():
    records, digests = load()
    return render(TEMPLATE_GLANCE, records, digests)


# ---- install / check --------------------------------------------------------------------------


def install(path, stem, block, *, glance_heading=None):
    """Write ``block`` between the stem's sentinels ONLY. PRE-PUBLISH ONLY (D-20).

    A present pair is replaced in place; an absent pair is appended at EOF, or — with
    ``glance_heading`` — inserted after that heading and its blank line, before the first existing
    bullet (zero deletions). The prefix is proved byte-identical on the PRODUCED text.
    """
    path = pathlib.Path(path)
    begin, end = _markers(stem)
    text = path.read_text(encoding="utf-8")
    n_begin, n_end = text.count(begin), text.count(end)
    _prove(
        n_begin == n_end <= 1,
        f"{path}: {begin} occurs {n_begin} time(s) and {end} {n_end} time(s); exactly one pair or "
        "none is required — anything else makes the write ambiguous, and ambiguity is a rewrite",
    )
    if n_begin == 1:
        _prove(text.index(begin) < text.index(end), f"{path}: sentinels out of order")
        prefix = text.split(begin, 1)[0]
        suffix = text.split(end, 1)[1]
        updated = prefix + begin + block + end + suffix
    elif glance_heading is not None:
        found = text.count(glance_heading)
        _prove(found == 1, f"{path}: {glance_heading!r} occurs {found} time(s); one is required")
        head, rest = text.split(glance_heading, 1)
        heading_line, _, after = rest.partition("\n")
        _prove(after.startswith("\n- "), f"{path}: expected a blank line then a bullet after it")
        prefix = head + glance_heading + heading_line + "\n\n"
        updated = prefix + begin + block + end + "\n" + after
    else:
        prefix = text if text.endswith("\n") else text + "\n"
        updated = prefix + "\n" + begin + block + end + "\n"
    _prove(
        updated.startswith(prefix) and block in updated,
        f"the rewritten {path} does not carry its original prefix byte-identically, or lost the "
        "block — checked on the produced bytes, not assumed from the construction",
    )
    path.write_text(updated, encoding="utf-8")
    return updated


def _span(path, stem):
    begin, end = _markers(stem)
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if text.count(begin) != 1 or text.count(end) != 1:
        return None
    return text.split(begin, 1)[1].split(end, 1)[0]


def check():
    """Re-render and compare with the committed spans; 1 on drift or absent sentinels."""
    status = 0
    for path, stem, rendered in (
        (REPORT_PATH, REPORT_STEM, render_report()),
        (README_PATH, GLANCE_STEM, render_glance()),
    ):
        committed = _span(path, stem)
        if committed is None:
            rel = path.relative_to(_ROOT)
            print(f"[phase28_report] {rel}: {stem} sentinels absent (pre-publish state)")
            status = 1
        elif committed != rendered:
            print(f"[phase28_report] {path.relative_to(_ROOT)}: {stem} block drifted")
            sys.stdout.writelines(
                difflib.unified_diff(
                    committed.splitlines(True), rendered.splitlines(True), "committed", "rendered"
                )
            )
            status = 1
    return status


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = "usage: phase28_report.py render (--stdout report|glance | --out DIR) | write | check"
    if argv[:1] == ["check"]:
        return check()
    if argv[:1] == ["write"]:
        install(REPORT_PATH, REPORT_STEM, render_report())
        install(README_PATH, GLANCE_STEM, render_glance(), glance_heading=GLANCE_HEADING)
        print("[phase28_report] installed both blocks (pre-publish only, D-20)")
        return 0
    if argv[:2] == ["render", "--stdout"] and argv[2:3] in (["report"], ["glance"]):
        sys.stdout.write(render_report() if argv[2] == "report" else render_glance())
        return 0
    if argv[:2] == ["render", "--out"] and len(argv) == 3:
        out = pathlib.Path(argv[2])
        out.mkdir(parents=True, exist_ok=True)
        (out / "phase28_report.md").write_text(render_report(), encoding="utf-8")
        (out / "phase28_glance.md").write_text(render_glance(), encoding="utf-8")
        print(f"[phase28_report] wrote {out / 'phase28_report.md'} and {out / 'phase28_glance.md'}")
        return 0
    print(usage, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
