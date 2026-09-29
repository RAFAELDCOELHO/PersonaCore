# Phase 34: v5.0 Report and Milestone Close - Research

**Researched:** 2026-09-28
**Domain:** Record-bound report rendering (reusing the frozen Phase 28 engine), disposition ledger, a tag-derived dependency-equality test, and a CI-gated close
**Confidence:** HIGH. Every load-bearing claim below was measured in this session against HEAD `76f9f1d` or against a scratch clone of it.

## Summary

Phase 34 follows the Phase 28 pattern, and the engine it needs already exists. `scripts/phase28_report.py` exports `resolve`, `_fmt`, `_Template`, `_table`, `_cell`, `_markers`, `_span`, `_prove`, `_github_anchor`, `_blockquote`, `install`, `ledger_rows_digest` and `ledger_frozen_bytes`, and it imports without torch (measured). The new module `scripts/phase34_report.py` imports those names. It needs its own `Bindings` subclass and its own three-line `render()`, because `phase28_report.render()` hardcodes phase28's `Bindings` and `Bindings.__getitem__` dispatches on phase28's module-level `RECORDS`/`DERIVED`/`TABLES`/`PATHS`. `install()` can be reused for the REPORT append. It **cannot** do the README insertion: with `glance_heading`, it requires `"\n- "` right after the heading, but the heading is now followed by `<!-- PHASE28-GLANCE-BEGIN -->`, so it refuses.

The biggest finding is not in CONTEXT. **Installing the D-02 blocks turns three existing Phase 28 guards RED, while `phase28_report.py check` stays exit 0.** I measured this in a scratch clone with probe blocks placed exactly as D-02 specifies. `tests/test_phase28_report.py::test_report_section_is_after_every_prior_heading`, `::test_glance_deleted_nothing` and `::test_write_installs_pre_publish_then_refuses` all fail; the other 84 tests across 6 guard files pass. Each of the three encodes "the v4.0 block is the last thing installed" rather than "the v4.0 block is byte-identical". So Phase 34 must amend those three tests with a dated-continuation comment. The engine is not touched and the byte-identity tests stay unchanged. This is a natural RED: install first, watch the three fail, then amend.

Several CONTEXT premises were measured as partly false:
- (a) The v5 half of each `condition_c_vs_v4` row has **no** `label`/`quoted_reasons`. Only the v4 half has them.
- (b) `results/phase28_ledger.json` has **5** RE-DEFERRED rows, not 6, and Phase 29 DEBT-01..04 already closed all 5.
- (c) The 15 rows staged in 33-03-SUMMARY use four disposition strings outside the closed domain.
- (d) phase28's ledger schema also requires `category`.
- (e) The CI on `origin/main` is **already RED**: run `36433089806` fails `tests/test_phase31_probe.py::test_plist_mirrors_the_canary_agent` on a host path. `tests/test_phase32_points.py:1045-1049` makes the same assertion and has never run in CI.

**Primary recommendation:** Wave 1 fixes the two host-path plist tests and upgrades RPT-05, then the developer does push 1. The next waves build `phase34_report.py`, its templates and `results/phase34_ledger.json` with tests, then render to scratch for the developer's read, then run `write` once and amend the three Phase 28 guards on their natural RED in the same publishing commit. Push 2 follows, then `close.ci_run`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| v5.0 numbers | Committed records (`results/phase32_frontier.json`, `results/phase33_admission.json`) | — | D-21: the renderer reads records directly and nothing is typed |
| Rendering and binding | `scripts/phase34_report.py` (new), importing the phase28 engine helpers | `scripts/phase34_*.md.tmpl` | The template holds prose plus `${…}`, and the module holds the bindings |
| Published surfaces | `docs/REPORT.md` (append after `PHASE28-REPORT-END`), `README.md` (above `PHASE28-GLANCE-BEGIN`) | — | D-02 |
| Dispositions | `results/phase34_ledger.json` (new) | `tests/test_phase34_ledger.py` | D-12: one ledger per milestone |
| Dependency equality | `tests/test_package.py` | `.planning/MILESTONES.md` (derived tag set) | D-10 |
| Close evidence | GitHub Actions run on the developer's push | `results/phase34_ledger.json::close.ci_run` | D-15, D-38. Claude never pushes |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Carried from Phase 28 and binding here without re-litigation:**
- a template with named bindings (D-16);
- byte-identity re-render against the committed records (D-17);
- a numeral scan over the template SOURCE with the strict identifier grammar (D-18/D-19);
- FROZEN AT PUBLISH, with corrections only as dated addenda through `scripts/_addendum.py` (D-20);
- the renderer reads committed records directly and carries a sha256 per source (D-21);
- cross-surface prose goes through `scripts/_prose.py::normalized` (D-22);
- the date stamp is a pinned constant (D-24);
- one ledger per milestone with a closed disposition domain, where `FIXED` requires a test (D-28/D-29);
- the register is the ledger filtered to NAMED-LIMITATION (D-30);
- STATE/ROADMAP/REQUIREMENTS are edited by hand with a snapshot before and a diff of all three
  after, and zero `gsd-sdk` mutation handlers (D-34).

### Area A — Renderer and the frozen v4.0 block (RPT-04, SC1)

- **D-01: A new module `scripts/phase34_report.py` imports phase28_report's engine and never edits
  `scripts/phase28_report.py`.** Measured 2026-09-28: `Bindings`, `render`, `resolve`, `_fmt` and
  `_Template` are importable. `Bindings.__getitem__`, however, dispatches on phase28's module-level
  `RECORDS` / `TABLES` / `DERIVED` / `PATHS` dicts, which are v4.0's. The new module therefore
  subclasses (or re-parametrizes) `Bindings` with its own records, tables and derived values instead
  of calling phase28's as-is.
- **D-02: New sentinels `PHASE34-REPORT` and `PHASE34-GLANCE`.**
  - The report block is appended after `<!-- PHASE28-REPORT-END -->` (`docs/REPORT.md:1609`).
  - The glance block is inserted in `README.md` ABOVE `<!-- PHASE28-GLANCE-BEGIN -->`
    (`README.md:111`), at the top of the "Results at a glance" list, with zero deletions.
  - `python scripts/phase28_report.py check` must stay exit 0 throughout. That is SC1's
    "frozen v4.0 block re-renders byte-identical", tested as it stands and never re-rendered with
    `write`.
- **D-03: Test file naming follows `tests/test_phase34_*.py`.** It needs a byte-identity test of
  both new blocks, a numeral scan of the new template sources (natural RED, per the memory rule),
  and an assertion that the v4.0 `check` still passes.

### Area B — What the v5.0 section publishes (RPT-04)

- **D-04: The verdict comes first, then the mechanism, with n8 and n64 as distinct findings from
  line 1.** The lead has one line per leg, bound to `results/phase32_frontier.json::verdicts.
  tallies_by_leg`:
  - `advr_n8`: 0 of 6 PASS, all 6 INCONCLUSIVE;
  - `advr_n64`: 6 of 6 REFUSED.

  Then comes `results/phase33_admission.json::admission.verdict` (MOOT), with its three `reasons`
  quoted verbatim. No aggregate "0 of 12" headline hides the per-leg split.
- **D-05: n64 is stated as NOT MEASURED, never as "the mitigation held".** Its refusal is quoted
  verbatim from `verdicts.leg_refusals.advr_n64`, and its control's readings are bound to
  `verdicts.control_readings.advr_n64`: `unlearnable: true`, taught `[0, 1008]`, heldout `[1, 648]`.
  This follows Phase 33 D-08's wording discipline.
- **D-06: The v4→v5 comparison is a table rendered from `verdicts.condition_c_vs_v4.rows`.** For
  each ratio it shows the (c) label and `quoted_reasons` for v4 and v5 side by side, plus the
  `by_leg` summary (`tk/tn`, `hk/hn`, `v4_state`/`v5_state`, `k5`/`k6`). It is never reconstructed
  in prose. The record's own `notes` travel with it, covering why the ratio-0 control's dialogue
  half passes by self-reference (D-18) and why `k5` excludes it.
- **D-07: No figures.** No phase32 PNG exists. With 0 PASS and n64 refused, the table carries the
  finding. Generating plots is deferred.
- **D-08: A post-hoc publication contract, declared as NOT a pre-registration.**
  `phase34_report.py` declares a `(field_path, why)` tuple covering at least:
  - `verdicts.tallies_by_leg`, `verdicts.leg_refusals` and `verdicts.control_readings`;
  - `verdicts.condition_c_vs_v4`;
  - `admission.verdict` / `admission.reasons`, `limitation` and `scope` from the phase33 record.

  A test resolves every path against the committed records and requires a binding for each in the
  template. The module's docstring states the contract was written after the results. A late
  pre-registration would be refused by `phase29_prereg`'s ancestry guard and would claim something
  false. No v5.0 `PUBLICATION_OBLIGATION` exists in `phase29_prereg.py` (measured).
- **D-09: The ship / withheld-claims block is rendered from `results/phase34_ledger.json`**, the
  Phase 28 D-13 pattern.
  - Withheld: the NAMED-LIMITATION rows + `leg_refusals` + the admission `reasons`; any claim that
    replay-bearing adversarial training preserves weight-based memory while removing leakage; any
    conclusion at n64.
  - Shipped: the replay-bearing recipe, each leg's own control, and the refusal surface as
    CPU-tested code. Per Phase 33 D-08, the text never says the relearning apparatus was "built and
    never exercised", only that the refusal surface exists.

### Area C — RPT-05 and the tag that does not exist yet

- **D-10: The required tag set is DERIVED from `.planning/MILESTONES.md`, not typed.** The test
  parses the `## vX.Y … (Shipped: …)` headings. It requires every shipped milestone's tag to be
  present and asserts `[project].dependencies` (stdlib `tomllib`) equal across all of them and HEAD.
  - **Today:** MILESTONES lists v1.0–v4.0 as shipped, so the test requires those four tags, and
    HEAD stands in for v5.0. The current test hardcodes `v1.0/v2.0/v3.0` and does not even include
    `v4.0`; that gap closes with this change.
  - **After `/gsd-complete-milestone`:** once it writes "v5.0 … (Shipped: …)", the v5.0 tag is
    required without any hand edit, so the test anchors on a fixed tag, not a moving HEAD. A clone
    missing a required tag goes RED instead of passing vacuously.

  Keep the existing shallow-clone refusal. Test 1 renames or supersedes
  `test_runtime_dependencies_identical_across_four_milestones` (its name would turn false), and the
  `PYPROJECT_SHA256` change detector stays as it is (Phase 28 D-26).
- **D-11: A hand-off obligation on the milestone close, recorded in the ledger and in the phase
  SUMMARY.** From the moment MILESTONES.md says v5.0 shipped, CI needs the `v5.0` tag on origin.
  The developer must push the tag together with main, or the next CI run is RED. This is the
  v2.0/v3.0 "tags never pushed" lesson from 28-07.

### Area D — Ledger (single source per milestone)

- **D-12: A new `results/phase34_ledger.json`, NOT an extension of `results/phase28_ledger.json`.**
  Measured 2026-09-28: the frozen v4.0 block embeds the phase28 ledger's rows digest
  `bb9f82fe290d7578…` literally in `docs/REPORT.md`. It also renders the NAMED-LIMITATION register,
  the withheld claims and the per-disposition counts from ALL rows, with no milestone filter
  (`scripts/phase28_report.py:552-576`). Appending v5.0 rows would therefore break SC1's
  byte-identical re-render. The data is a digested input of the frozen block, so it carries the
  same freeze as code.
  - The new ledger uses the same schema (`id`, `milestone`, `source`, `disposition`, `evidence`,
    `reason`, plus `target`/prerequisite where RE-DEFERRED) and the same closed domain.
  - `close.ci_run` sits outside the rows digest, as in phase28.
  - The path is already under `phase29_prereg`'s ancestry guard (`results/phase34_*`, RPT-04).
- **D-13: The census covers the whole of v5.0 plus v4.0's still-open rows.**
  - All carried items from REVIEW / VERIFICATION / SECURITY / UAT across Phases 29–33, including:
    - the 15 rows staged in `33-03-SUMMARY.md` (P31-WR-01; P32 CR-01/WR-01/WR-02/WR-04/WR-05 +
      IN-*; IN-03's dated continuation; ACTRL-01 NAMED-LIMITATION);
    - `33-REVIEW.md` WR-01/WR-02/IN-01..03;
    - what 30/31/32 carried forward.
  - The 6 RE-DEFERRED rows of `results/phase28_ledger.json` are re-disposed in the v5.0 ledger BY
    REFERENCE (id + the phase28 ledger's sha256). They are never copied back into the frozen file.
  - Ids carry the phase prefix (Phase 33 D-11).
  - The planner re-measures each item's guard status before assigning a disposition, per the
    Phase 28 D-32 pattern: this list is the pattern, not the census. Every count in prose comes
    from `len()`.
- **D-14: 33-REVIEW WR-01 (`git_sha()` reads the cwd) and WR-02 (`--out` bypasses write-once) are
  RE-DEFERRED, not fixed.**
  - Measured: `scripts/phase33_admission.py` is pinned in `results/phase33_admission.json::
    provenance.module_sha256` (`2041aecc…` = live), guarded at `tests/test_phase33_admission.py:424`,
    so a fix reddens that guard.
  - The record is unaffected, because it was written from the repo root and its `git_sha` holds.
  - Target: "the milestone that reuses `phase33_admission`". Prerequisite: fix with a dated pin
    continuation before reuse. This is the same treatment as AR-32-02/03.

### Area E — Close and the push (RPT-06, D-38)

- **D-15: Two developer pushes, both human checkpoints. Claude never runs `git push`.**
  - **Push 1, at the START of the phase, before the publishing commit.** Measured: `main` is 75
    commits ahead of `origin/main` (`68d2bee`, the Phase 31 close), so none of the Phase 32–33 code
    has run in CI. Any CI defect then surfaces before the freeze. In Phase 28 the first push found
    4 failures only after publishing.
  - **Push 2, after the publishing commit.** Its green run id, head sha, conclusion and url are
    recorded in `results/phase34_ledger.json::close.ci_run`, and the rows stay byte-unchanged.
  - Record the id and head of the run from push 1 as well, for the audit trail. Only push 2's run
    closes RPT-06.
- **D-16: Ticks and the boundary.** RPT-04..06 are ticked by hand only after their evidence exists.
  RPT-06 needs a green run whose head contains the publishing commit. `/gsd-complete-milestone`
  owns PROJECT.md, MILESTONES.md and the `v5.0` tag (see D-11).

### Claude's Discretion
- Template file names (`scripts/phase34_report.md.tmpl` / `phase34_glance.md.tmpl` are the
  expectation) and the constant naming inside `phase34_report.py`.
- How `Bindings` is re-parametrized (subclass versus constructor arguments), as long as
  `phase28_report.py` is byte-unchanged.
- Section title wording. Constraint: it names MOOT and the per-leg outcome, not a phrase describing
  them.
- Plan/wave structure and sequencing of the two push checkpoints and the developer's read of the
  rendered blocks before the publishing commit (the 28-06 pattern).

### Deferred Ideas (OUT OF SCOPE)
- Frontier plots for the v5.0 sweep (`results/phase34_*.png`). Not needed with 0 PASS and n64
  refused; they can be added in a future milestone that has a non-empty frontier.
- README "Repository status (recorded 2026-09-02)" still describes v4.0 as in progress. That is a
  dated corrections-table entry for the milestone close or a later docs pass, not this report.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RPT-04 | The v5.0 section of `docs/REPORT.md` and the README glance is rendered from committed records under the numeral scan | §Architecture Patterns 1–4, §Pitfalls 1–9, and the natural-RED list of three phase28 guards |
| RPT-05 | Runtime dependencies are identical across every milestone tag | §Code Examples "RPT-05 test". The tag set derived from MILESTONES today = `['v4.0','v3.0','v2.0','v1.0']`, all on origin, deps equal at all 4 + HEAD (measured) |
| RPT-06 | The milestone closes on a green CI run of the developer's push (D-38) | §Pre-push checklist, §RPT-06 procedure. origin CI is currently RED (run 36433089806) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11 `.venv` only. Never validate against the local 3.14. Use `.venv/bin/python`, `.venv/bin/pytest` and `.venv/bin/ruff` (ruff 0.15.16 is present).
- No new runtime dependency. `pyproject.toml` is sha-pinned (`tests/test_package.py::PYPROJECT_SHA256`) and must not change in this phase.
- Tests must be CPU-only and GPU-free. The renderer must stay torch-free.
- Do not use wandb or any network service in code. `gh` is used by the orchestrator/developer only to *read* the run.
- The GSD workflow applies. Planning files are edited by hand with zero `gsd-sdk` mutation handlers (memory: they corrupt frontmatter). Snapshot STATE/ROADMAP/REQUIREMENTS before editing and diff all three after.
- Never commit secrets. **Claude never runs `git push`** (D-38).
- Global: register durable outcomes in the Obsidian vault (orchestrator's job at phase end).

## Standard Stack

No packages are installed. Everything is already present and verified in `.venv`:

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11.15 (`.venv`) | runtime [VERIFIED: `.venv/bin/python --version`] |
| stdlib `string.Template`, `hashlib`, `json`, `tomllib`, `re`, `subprocess`, `difflib` | 3.11 | rendering, digests, RPT-05 parsing [VERIFIED: phase28_report.py / test_package.py use them] |
| pytest | installed in `.venv` | tests |
| ruff | 0.15.16 | `make lint` / CI lint step [VERIFIED] |
| `gh` CLI | authenticated as RAFAELDCOELHO | reading run id/head/conclusion (read-only) [VERIFIED: `gh auth status`, `gh run list`] |

## Package Legitimacy Audit

Not applicable. The phase installs no external package, and adding one would redden `test_pyproject_sha256_pin_detects_any_change`. slopcheck was not run because there is nothing to check.

## Architecture Patterns

### System Architecture Diagram

```
results/phase32_frontier.json ──bytes──┐
results/phase33_admission.json ─bytes──┼─► phase34_report.load() ─► records + {name: (sha256, bytes)}
results/phase34_ledger.json ───bytes──┘                 │
                                                        ▼
scripts/phase34_report.md.tmpl ─► _Template.substitute(Bindings34) ─► report block ─┐
scripts/phase34_glance.md.tmpl ─► _Template.substitute(Bindings34) ─► glance block ─┤
                                                                                    ▼
             render --out <scratch> (developer read) ── write (ONCE) ──► docs/REPORT.md  (append after PHASE28-REPORT-END)
                                                                  └──► README.md       (insert above PHASE28-GLANCE-BEGIN)
                                                                                    │
                        check (phase34) + byte-identity tests ◄─────────────────────┘
                        phase28_report.py check (must stay 0) — independent, unchanged
                                                                                    │
             developer push 2 ─► GitHub Actions ─► gh run view ─► ledger close.ci_run (outside rows digest)
```

### Recommended file set (real paths)

```
scripts/phase34_report.py          # NEW — Bindings34, render, install_glance, check, main (render --stdout|--out, write, check)
scripts/phase34_report.md.tmpl     # NEW — report template (one "## " heading, "### " subsections)
scripts/phase34_glance.md.tmpl     # NEW — glance bullet(s), no heading
results/phase34_ledger.json        # NEW — {close, governs, rows, schema}; json.dumps(indent=2, sort_keys=True, ensure_ascii=False)+"\n"
tests/test_phase34_report.py       # NEW — numeral scan, contract, byte identity, placement, torch/clock-free
tests/test_phase34_ledger.py       # NEW — schema/domain/FIXED-needs-test/close shape/redump-stable/by-reference sha
tests/test_package.py              # EDIT — derived-tag RPT-05 test replaces the four-milestone test
tests/test_phase28_report.py       # EDIT (dated continuation) — 3 placement guards scoped to the v4.0 block
tests/test_phase31_probe.py        # EDIT (push-1 prerequisite) — host-independent heartbeat assertion (= f47468b)
tests/test_phase32_points.py       # EDIT (push-1 prerequisite) — same fix at :1045-1049
```

### Pattern 1: Bindings subclass over the frozen engine (D-01)

`phase28_report.render()` does `_Template(text).substitute(Bindings(records, digests))` with *phase28's* `Bindings`, so it cannot be reused. Write the three lines yourself:

```python
# scripts/phase34_report.py (sketch — names are discretionary)
import phase28_report as p28  # noqa: E402  (after the sys.path insert, same as phase28_report)

PUBLISHED = "2026-09-DD"            # D-24 pinned; the publishing day
REPORT_STEM, GLANCE_STEM = "PHASE34-REPORT", "PHASE34-GLANCE"
RECORDS = {
    "frontier": "results/phase32_frontier.json",
    "admission": "results/phase33_admission.json",
    "ledger": "results/phase34_ledger.json",   # key MUST be "ledger": p28._ledger_filter reads records["ledger"]
}

class Bindings(p28.Bindings):
    def __getitem__(self, key):
        prefix, _, rest = key.partition(".")
        if prefix == "meta" and rest == "published":
            return PUBLISHED
        if prefix in RECORDS:
            return p28._fmt(p28.resolve(self.records[prefix], rest))
        if prefix == "derived":
            return DERIVED[rest](self.records)
        if prefix == "table":
            return _sources(self.records, self.digests) if rest == "sources" else TABLES[rest](self.records)
        if prefix == "path":
            return PATHS[rest]
        raise KeyError(key)   # never fall through to phase28's dispatch (its RECORDS are v4.0's)

def render(template_path, records, digests):
    body = p28._Template(pathlib.Path(template_path).read_text(encoding="utf-8")).substitute(
        Bindings(records, digests))
    return "\n" + body.strip("\n") + "\n"          # same framing as phase28 (byte-identity relies on it)
```

Reuse `p28.install(REPORT_PATH, REPORT_STEM, block)` for the REPORT append. With no `glance_heading` it appends `"\n" + BEGIN + block + END + "\n"` at EOF and refuses once present [VERIFIED: phase28_report.py:729-767]. **Do not** reuse it for README, because the `after.startswith("\n- ")` proof fails when PHASE28's BEGIN sentinel follows the heading. Write a small `install_glance()` that:
- refuses if the PHASE34 pair is present;
- requires exactly one `<!-- PHASE28-GLANCE-BEGIN -->`;
- produces `text[:i] + BEGIN + block + END + "\n" + text[i:]`;
- proves on the produced bytes that both the prefix and the suffix (from the PHASE28 BEGIN onward) are byte-identical.

### Pattern 2: What the v5.0 records actually contain (measured; bind these paths)

- `frontier.verdicts.tallies_by_leg.advr_n8` = `{PASS:0, FAIL:0, INCONCLUSIVE:6, REFUSED:0}`; `.advr_n64` = `{…, REFUSED:6}`. Derive denominators as `sum(values())` or `len(point_keys with leg prefix)` and never type 6.
- `frontier.verdicts.leg_refusals` has **only** `advr_n64`, a long string containing `(0.0, 1.0]` and `Y_heldout=0.0010802469135802468`.
- `frontier.verdicts.control_readings.{advr_n8,advr_n64}` hold `adapter_off`, `adapter_on`, `recall_counts.{taught,heldout}=[k,n]`, `source` and `unlearnable`.
- `frontier.verdicts.condition_c_vs_v4`: `rows` (12), `by_leg.{n8,n64}` (`tk,tn,hk,hn,k5,k6,leg,twin,v4_hk,v4_hn,v4_k,v4_n_evaluated,v4_state,v4_tk,v4_tn,v5_state`) and `notes` (one string).
  - **Row shape:** `v4` = `{cleared_c, condition_c, label, quoted_reasons, verdict}`. `v5` = `{cleared_c, condition_c, state, verdict}`, plus `control_recall_counts` on the 5 non-control n64 rows. **The v5 half has no `label` or `quoted_reasons`** (D-06 premise partly false).
  - `v5.state` values are `measured`, `refused_by_route` (the n64 control row) and `refused_prereg03`.
  - `cleared_c` is `null` on the n64 rows, both halves. `v5.condition_c` is `null` on the 5 PREREG-03 rows.
- `frontier.verdicts.replicated_at_second_seed` = `false`; `route` = `"phase20_gate_coverage.corrected_point_verdict (D-34)"`.
- `admission.admission.verdict` = `"MOOT"`, and `admission.admission.reasons` has 3 strings. **reasons[0] begins `"0 of 12 points PASS; tallies {...}"`**, which is exactly the aggregate D-04 forbids as a headline. Quote it verbatim, but only *after* the two per-leg lead lines.
- `admission.limitation` = `{legs.{advr_n8,advr_n64}, requirements[4], scope_rule, surface}` and `admission.scope` = `{relearn_point_keys:[], rule, verdict}`.
- `admission.frontier` = `{bytes: 56857, path, sha256: 4a4bcb60…}`. A cheap chain test asserts this equals the frontier digest from `load()`.

Top-level record prefixes: `frontier`, `admission`, `ledger`. The phase33 record's own key is also `admission`, so the binding reads `${admission.admission.verdict}`. You can instead name the record prefix `admission_record` for readability. That is a discretionary choice, but make it before writing templates.

### Pattern 3: The comparison table (D-06), corrected to the real shape

Columns per row:
- ratio (`repr`) and v4_key;
- v4 verdict, v4 `label`, v4 `quoted_reasons` joined with "; ";
- v5_key, v5 `state`, v5 `verdict`, v5 `cleared_c`.

Then a `by_leg` table and `notes` rendered once below both. Render `null` explicitly. `p28._fmt(None)` raises `KeyError("unrenderable")`, so `_cell(None)` crashes. Use a local cell function that maps `None` to a fixed token such as `null`. The record's `notes` already explains `None where the point never reached the pin`, so quoting `notes` next to the table covers it. Do not paraphrase `notes`.

### Pattern 4: Publication contract (D-08) as data plus one test

```python
CONTRACT = (  # post-hoc — written AFTER the results; NOT a pre-registration (docstring says so)
    ("frontier.verdicts.tallies_by_leg", "…why…"),
    ("frontier.verdicts.leg_refusals", "…"),
    ("frontier.verdicts.control_readings", "…"),
    ("frontier.verdicts.condition_c_vs_v4", "…"),
    ("admission.admission.verdict", "…"), ("admission.admission.reasons", "…"),
    ("admission.limitation", "…"), ("admission.scope", "…"),
)
COVERED_BY = {"table.condition_c_vs_v4": ("frontier.verdicts.condition_c_vs_v4",), …}
```

The test does two things for every path. First it calls `p28.resolve(records[prefix], rest)`. Then it requires that either a `${path…}` placeholder in the template starts with the path, or a `table.`/`derived.` binding in the template lists the path in `COVERED_BY`. A tmp-copy check proves that dropping the binding from the template makes the test RED.

### Anti-Patterns to Avoid

- **Calling `p28.render` / `p28.Bindings` unmodified.** This renders v4.0 prefixes, or raises on `frontier.` because it reads phase25's record.
- **Reading `.planning/*` live from phase34 templates** (the `quote`/`slice` kinds). The milestone close edits REQUIREMENTS/ROADMAP, and a live read would redden the frozen v5.0 block later. Quote only records. If a planning quote is essential, use the `git:<sha>:<path>` source form (`p28._source_text`).
- **Adding anything to the ledger `close` block after the publishing commit other than `ci_run`.** `p28.ledger_frozen_bytes` nulls only `close.ci_run`, so any other late key moves the provenance "bytes" cell and reddens byte-identity (the 28-07 natural RED at 49057→49297).
- **Adding v5.0 rows to `results/phase28_ledger.json`** (D-12; also `test_ids_are_unique_and_milestone_is_v3_or_v4`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dotted record access | a new getter with `.get` | `phase28_report.resolve` | raises `KeyError(path)`; blank is impossible |
| Scalar formatting | f-strings with rounding | `phase28_report._fmt` (+ a null-aware wrapper) | `repr` floats keep byte-identity with the records |
| Markdown tables | a new table writer | `phase28_report._table` / `_cell` | pipe/newline escaping already proven |
| Ledger digest and size | a new digest | `phase28_report.ledger_rows_digest` / `ledger_frozen_bytes` | `close` stays outside both (28-07 fix) |
| Anchors | a hand-written anchor | `phase28_report._github_anchor` | the same rule `test_phase15_docs` uses |
| Numeral scan | a new regex set | `from test_phase28_report import _bare_numerals` (tests dir on sys.path; precedent `tests/test_phase32_live.py` imports `from test_phase25_driver import _scratch_repo`) | one grammar (D-18/D-19) |
| Prose comparison | `in` on raw text | `_prose.normalized(a) in _prose.normalized(b)` | D-22; also keeps `test_phase25_correction`'s register logic sound |
| Run metadata | parsing Actions HTML | `gh run view <id> --json databaseId,headSha,conclusion,url,status` | read-only, exact fields |

## Runtime State Inventory

This is not a rename or migration phase, but the close touches live state:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `results/phase28_ledger.json` rows are digested into the frozen block (`bb9f82fe…`). Its SC3-SHA256-CLAUSE row's evidence names `tests/test_package.py::test_runtime_dependencies_identical_across_four_milestones` as its 2nd node id | Do not edit the file. After the rename, record the supersession as a v5.0 ledger row by reference. No test reads that 2nd node id (`_fixed_violations` reads only `node_ids[0]` of FIXED rows, and this row is ACCEPTED), measured |
| Live service config | GitHub remote tags: `m1-demo-v1, v1.0, v2.0, v3.0, v4.0` present on origin (`git ls-remote --tags origin`, measured). `v5.0` does not exist yet | D-11: the developer pushes `v5.0` with main at `/gsd-complete-milestone` |
| OS-registered state | None. No launchd agent is involved in this phase (verified: phase34 runs no sweep) | none |
| Secrets/env vars | None. `gh` uses its keyring auth, and nothing is written to the repo | none |
| Build artifacts | None. The editable install is unaffected (no package change) | none |

## Common Pitfalls

### Pitfall 1: Three Phase 28 placement guards go RED on install (measured, natural RED)
**What goes wrong:** In a scratch clone with probe blocks placed per D-02:
- `test_report_section_is_after_every_prior_heading` fails with `('## v5.0 — probe heading', '## v4.0 — …')`, because it asserts the v4.0 heading is the file's last `## `.
- `test_glance_deleted_nothing` fails with `assert 12 …`, because it asserts the bullet count = pre-publish count + PHASE28 span's bullets.
- `test_write_installs_pre_publish_then_refuses` fails because `_stripped` leaves the PHASE34 blocks, so phase28's glance `install` refuses (`"\n- "` expected) and the EOF append lands after PHASE34.

`phase28_report.py check` stays **0** and the other 84 tests in the six guard files pass.
**How to avoid:** Put the three amendments in the publishing commit, after watching them fail. Scope each one to the v4.0 block:
- (a) The v4.0 heading is the last `## ` *outside later-milestone sentinel spans*, or every `## ` after it lies inside a `PHASE34-REPORT` span.
- (b) Subtract the bullets inside every later GLANCE span.
- (c) Strip the later-milestone blocks as well as PHASE28 before `write`, and compare against the current file minus the later blocks.

Add a dated-continuation comment in each test. The byte-identity tests (`test_report_block_is_byte_identical`, `test_glance_block_is_byte_identical`) are untouched.
**Warning signs:** a plan that says "`phase28 check` green ⇒ SC1 done" without running `tests/test_phase28_report.py`.

### Pitfall 2: CI is already RED on origin, and push 1 would fail twice
**What goes wrong:** Run `36433089806` (schedule, origin/main `68d2bee`) shows `1 failed, 3058 passed, 72 skipped`. `test_phase31_probe.py::test_plist_mirrors_the_canary_agent` compares the plist's absolute `/Users/juliorcoelho/…` heartbeat path with `str(phase25_run.HEARTBEAT_PATH)`, which is `/home/runner/…` on CI. `tests/test_phase32_points.py:1045-1049` has the identical assertion and has never run in CI.
**How to avoid:** Before push 1, apply commit `f47468b`'s fix. It lives on `origin/cursor/fix-plist-heartbeat-test-1976`, **not on main**; compare suffix parts of `HEARTBEAT_PATH.relative_to(_ROOT)`. Apply it to both files. Neither file is pinned by a results `module_sha256` (grep found none). `tests/test_phase33_admission.py:460` only reads `test_phase32_points.py` for its import census, which the edit does not change.

### Pitfall 3: The `append_addendum` census in planning files
**What goes wrong:** `tests/test_phase25_correction.py::test_no_continuation_was_written_by_append_addendum` pins the total occurrences across ROADMAP + REQUIREMENTS + 25-CONTEXT at **3** (measured: ROADMAP 2, REQUIREMENTS 0, 25-CONTEXT 1). Phase 28's RPT-01 row broke this (fd03998).
**How to avoid:** No Phase 34 edit to ROADMAP or REQUIREMENTS may spell that helper name. Write "`scripts/_addendum.py`" instead.

### Pitfall 4: The frozen engine reads planning files live
`phase28_report` reads `.planning/REQUIREMENTS.md` (quote `req_23_12_retraction`, sentinel slice `23-12-CONTINUATION` at lines 186/271), `.planning/ROADMAP.md` (bullet slice starting `- 🔮 **v5.0`, line 9, which stops at the next `- `/blank line) and `.planning/research/SUMMARY.md` (via `git:c673b4c:` pin). The Phase 34 ticks and progress-row edits must leave those spans, and the 🔮 bullet with its continuation lines 10-13, byte-identical. Run `.venv/bin/python scripts/phase28_report.py check` after every planning edit.

### Pitfall 5: Numeral-scan traps in the new templates
The scan (`test_phase28_report._bare_numerals`) exempts only `Phase N`, UPPER-ID-with-hyphens, ISO dates, hex shas containing a letter, `§N`, `NN-NN`, `vN.N` and `sha256`. These hit:
- `advr_n8`, `advr_n64`, `n=64`, `n8` (lowercase): bind leg names from records (`frontier.verdicts.condition_c_vs_v4.by_leg.n8.leg`) or from derived values;
- a bare `v5` or `v4`: write `v5.0`/`v4.0`;
- `RELRN-06..09`: the `..09` survives, so list each id or bind `admission.limitation.requirements`;
- any count: "0 of 6", "12", "two legs" is fine, "2 legs" is not.

Start with the planted-numeral natural RED from `tests/test_phase28_report.py:105-112`.

### Pitfall 6: Repo-wide AST censuses that scan `scripts/phase34_*.py`
- `tests/test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control` scans `phase30..34`. It fails on:
  - a Name or Attribute `control_readings`;
  - a bare string constant exactly `"control_readings"`, unless it is a dict key or a subscript whose chain is rooted at a **plain Name**. `records["frontier"]["verdicts"]["control_readings"]` passes; `self.records[...]["control_readings"]` (Attribute root) **fails**;
  - **any string constant starting with `dp_n`**, docstrings excepted.

  Dotted-path strings like `"frontier.verdicts.control_readings"` pass (not an exact match). Local variable names must not be `control_readings`.
- `tests/test_phase29_prereg.py::test_no_v5_module_uses_the_accountant` scans `phase29..34` and fails on an import of `personacore.privacy*` / `phase25_epsilon`, or on the names `epsilon_for`, `sigma_for`, `delta_closed` or `delta_quadrature`. Importing `phase28_report` is fine (AST-only). The accountant loads transitively, which is the same stated posture as phase29.
- `tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers` means no `os.replace` in phase34 (write with `Path.write_text` like phase28's `install`).
- `tests/test_phase23_resume.py::test_resume_from_none_is_inert` runs a **text** grep for `train_arm(` over `scripts/` and `tests/`, docstrings included. Never write that token.
- `tests/test_phase21_sc5.py` scans every `tests/**/*.py` for `(?:==|!=)\s*10(?![0-9_])`, comments included. Keep that out of new tests.
- `mitigation_gate.ratchet_k` K-menu and ISO-06 `inject_lora` do not apply here (no training code).

### Pitfall 7: STAT-02 and headline-number guards over README/REPORT
`tests/test_phase18_docs.py::test_no_bare_zero_percent_in_docs` bans `\b0(\.0+)?%` anywhere in both files. The point-level `verdict.reasons` (a)-sentences contain `(0.0000%)`, so never bind them (phase28 avoided them the same way). `tests/test_phase15_docs.py::test_headline_numbers_match_sources` requires `0.3483`, `8.52417066884246` and `3.229` each to appear in **exactly one** README bullet. I measured that no string or number in `frontier.verdicts` or the phase33 record contains any of those, nor `0.801544` (rho) or a bare zero percent. Re-check on the *rendered* blocks in a test.

### Pitfall 8: `close.ci_run` and the frozen size
`ledger_frozen_bytes` nulls `close.ci_run` only. Record push 1's run **before** the publishing commit (for example `close.preflight_ci_run`, part of the frozen bytes) or in the SUMMARY only. Fill only `close.ci_run` after publish. Mirror `test_close_block_shape` with the phase34 key set.

### Pitfall 9: Clean-tree probes and suite duration
11 probes fail while `results/`, `tests/` or `scripts/` hold untracked or modified files. Run the full suite (~25 min locally; CI ~30 min) only on a committed tree, using `nohup … & ` plus a `grep '^EXIT='` waiter, because Bash caps at 600 s.

### Pitfall 10: The ubuntu skip pin
`tests/test_phase25_venue.py` pins the CI skip total. Measured: the test files changed since origin/main (`test_phase30_*`, `test_phase32_{frontier,live,points}`, `test_phase33_admission`) contain no `skipif`/`pytest.skip`/`needs_adapters`; the only hits in `test_phase32_points.py:1059-1081` are an AST helper, not a skip. The baseline at `68d2bee` was 72 skipped in CI. New phase34 tests must not skip. If push 1 reports ≠72, measure (`gh run view <id> --log | grep "passed.*skipped"`) before trusting any diagnosis.

## Code Examples

### RPT-05 test (replaces `test_runtime_dependencies_identical_across_four_milestones`)
```python
# tests/test_package.py — uses the existing _git/_deps helpers and tomllib
import re
_SHIPPED = re.compile(r"^## (v\d+\.\d+)\b[^\n]*\(Shipped: \d{4}-\d{2}-\d{2}\)\s*$", re.M)

def _required_tags(milestones_text):
    return _SHIPPED.findall(milestones_text)

def test_runtime_dependencies_identical_across_every_milestone_tag():
    assert _git("rev-parse", "--is-shallow-repository") == "false", "…fetch-depth: 0…"
    required = _required_tags((_ROOT / ".planning/MILESTONES.md").read_text(encoding="utf-8"))
    assert required, "no '## vX.Y … (Shipped: …)' heading parsed — the derivation is blind"
    missing = sorted(set(required) - set(_git("tag", "-l").split()))
    assert not missing, f"shipped milestones without a tag in this clone: {missing} (push tags)"
    head = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
    by_rev = {tag: _deps(tag) for tag in required} | {"HEAD": head}
    assert all(deps == head for deps in by_rev.values()), by_rev

def test_required_tags_are_derived_not_typed():
    # natural input = the real file; a synthetic heading proves a future v5.0 line becomes required
    text = (_ROOT / ".planning/MILESTONES.md").read_text(encoding="utf-8")
    assert _required_tags("## v9.9 Name (Shipped: 2099-01-01)\n" + text)[0] == "v9.9"
```
Measured today: the derived list is `['v4.0','v3.0','v2.0','v1.0']`, and dependencies are `['numpy~=2.4', 'regex~=2026.5']` at all four tags and at HEAD. Also update the `test_pyproject_sha256_pin_detects_any_change` docstring, which names the old test (prose only; the constant is unchanged).

### RPT-06 read (orchestrator/developer; read-only)
```bash
gh run list --branch main --event push --limit 3 --json databaseId,headSha,status,conclusion,url
gh run view <ID> --json databaseId,headSha,conclusion,url,status
git merge-base --is-ancestor <PUBLISHING_SHA> <headSha> && echo contains-publishing-commit
```
Write `{"id": "<ID>", "url": …, "head_sha": …, "conclusion": "success", "recorded": "YYYY-MM-DD"}` into `close.ci_run` (the phase28 key set). Re-dump with `json.dumps(indent=2, sort_keys=True, ensure_ascii=False)+"\n"`, and prove that the rows digest and frozen bytes are unchanged.

## Ledger census inputs (measured facts the planner must carry)

- **phase28 RE-DEFERRED rows = 5** (TD-16-R1, TD-17-SUMMARY-FRONTMATTER, IN-07, P22-WARNING-4, P22-WARNING-5), not 6. Phase 29 closed all five:
  - DEBT-01 closes IN-07 (5e0a1f3);
  - DEBT-02 closes TD-16-R1 (29-03);
  - DEBT-03 closes TD-17 (5523d50, `tests/test_phase29_debt.py`);
  - DEBT-04 re-records P22-WARNING-4/5 as a named limitation (63ca8de; `test_named_limitations_record_p22_warning_4_5`).

  Re-dispose them by reference as `{id, phase28 ledger sha256}`. The phase28 file sha256 is not the rows digest; state which one is used.
- **phase28 ledger schema:** `required_keys = [category, disposition, evidence, id, milestone, reason, source]` (category included; D-12's list omits it). Dispositions: `ACCEPTED, CLOSED-EARLIER, FIXED, FORBIDDEN-BY-GUARD, NAMED-LIMITATION, RE-DEFERRED`.
- **33-03-SUMMARY's 15 staged rows use out-of-domain labels.** These must be mapped into the closed domain, and FIXED needs commit + collectable node id:
  - `BY-REFERENCE` (P32-WR-02);
  - `CLOSED` (P32-WR-03; fixed at 325aaf0→f7c1a83, a FIXED candidate);
  - `DATED-CONTINUATION (2026-09-28)` (P32-IN-03);
  - `NAMED-LIMITATION (partial exercise)` (ACTRL-01).
- **Other sources to re-measure:**
  - 33-REVIEW WR-01/WR-02/IN-01..03, with WR-01/02 = AR-33-02/01 (33-SECURITY.md:61-62);
  - 32-SECURITY AR-32-01..03 plus UF-32-01..03 (:91);
  - 31-REVIEW WR-02 and IN-01..05;
  - 30-REVIEW, all fixed per "Fix Status (2026-09-25)" (CLOSED-EARLIER candidates);
  - 29-REVIEW `status: fixed`;
  - RELRN-06..09 as NAMED-LIMITATION bound to `results/phase33_admission.json::limitation.*`.

## State of the Art (in this repo)

| Old | Current | When | Impact |
|-----|---------|------|--------|
| Hardcoded `{v1.0,v2.0,v3.0}` tag set | derived from MILESTONES headings | this phase | a future v5.0 tag becomes required automatically |
| `write` re-runnable | `write` refuses once installed (8a466d8, quick-260922-ti5) | 2026-09-22 | `phase28` install is safe to reuse for the REPORT append |
| Whole-file ledger size in provenance | `ledger_frozen_bytes` (89aae4f) | 2026-09-22 | reuse it for phase34's ledger provenance row |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `/gsd-complete-milestone` will write the v5.0 MILESTONES heading as `## v5.0 … (Shipped: YYYY-MM-DD)` like v1.0–v4.0 | RPT-05 | If the format differs, the derivation misses v5.0. The regex is asserted non-empty; add a test that the newest heading parses |
| A2 | The developer accepts amending three `tests/test_phase28_report.py` placement guards (a test edit, not an engine edit) | Pitfall 1 | If refused, D-02 placement must change, which still breaks the glance-count and write-install tests. No placement avoids it |
| A3 | Applying f47468b's approach to both plist tests is acceptable before push 1 | Pitfall 2 | Otherwise push 1 is RED on ≥2 known failures |

## Open Questions (RESOLVED)

Resolutions (2026-09-28): Q1 → R-1 (amend after natural RED); Q2 → planner adopts the recommendation (v4 label+quoted_reasons, v5 state+verdict+cleared_c), surfaced at the 34-05 read; Q3 → planner adopts the recommended mapping, surfaced at the 34-05 read; Q4 → R-3 (push-1 id in SUMMARY only); Q5 → rename + v5.0 ACCEPTED ledger row, surfaced at the 34-05 read. See § Developer Rulings.

1. **The three Phase 28 guard amendments (Pitfall 1).** CONTEXT does not anticipate them.
   - Recommendation: amend in the publishing commit with dated-continuation comments, after natural RED. Surface this to the developer at the 28-06-style read checkpoint.
2. **How D-06 is rendered, given the v5 half has no label or reasons.**
   - Recommendation: v4 columns `label` + `quoted_reasons`, and v5 columns `state` + `verdict` + `cleared_c`. Quote `notes` verbatim.
3. **Disposition mapping for the four out-of-domain staged labels.**
   - Recommendation: P32-WR-03 → FIXED (325aaf0/f7c1a83 + a node id from `tests/test_phase30_points.py` WR-03 planted-red test; re-measure). P32-WR-02 → ACCEPTED. P32-IN-03 → RE-DEFERRED (code fix) with the continuation cited in evidence. ACTRL-01 → NAMED-LIMITATION.
4. **Where push 1's run id lives.**
   - Recommendation: `close.preflight_ci_run`, written before the publishing commit, or the SUMMARY only.
5. **The renamed RPT-05 test and the frozen phase28 ledger pointer.**
   - Recommendation: rename, and add a v5.0 ledger row (ACCEPTED) recording the supersession by reference.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | all | ✓ | 3.11.15 | — |
| ruff | lint gate | ✓ | 0.15.16 | — |
| git + tags v1.0–v4.0 local and on origin | RPT-05 | ✓ | — | — |
| `gh` (authenticated) | RPT-06 read | ✓ | — | GitHub web UI read by the developer |
| network push | RPT-06 | developer only | — | none (D-38) |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (`.venv`), config `pyproject.toml [tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`), `tests/conftest.py` |
| Quick run command | `.venv/bin/pytest -q -p no:cacheprovider tests/test_phase34_report.py tests/test_phase34_ledger.py tests/test_package.py tests/test_phase28_report.py tests/test_phase28_ledger.py tests/test_phase28_prereg.py tests/test_phase25_correction.py tests/test_phase15_docs.py tests/test_phase18_docs.py` (~30 s, measured for the existing six at 28.7 s) |
| Census run | `.venv/bin/pytest -q tests/test_phase29_prereg.py::test_no_v5_module_uses_the_accountant tests/test_phase30_points.py::test_ast_guard_no_v5_module_reaches_a_dp_control tests/test_phase21_sc5.py tests/test_phase25_driver.py::test_os_replace_appears_only_in_the_two_phase25_writers tests/test_phase23_resume.py::test_resume_from_none_is_inert` (~6 s measured) |
| Frozen check | `.venv/bin/python scripts/phase28_report.py check` (exit 0) and `.venv/bin/python scripts/phase34_report.py check` |
| Full suite command | `nohup sh -c ".venv/bin/pytest -q -p no:cacheprovider > $LOG 2>&1; echo EXIT=\$? >> $LOG" &` plus a waiter (~25 min, committed tree only) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RPT-04 | templates carry no bare numeral (+ planted RED) | unit | `pytest tests/test_phase34_report.py -k numeral` | ❌ Wave 0 |
| RPT-04 | every CONTRACT path resolves and is bound (+ tmp-copy RED) | unit | `pytest tests/test_phase34_report.py -k contract` | ❌ |
| RPT-04 | lead: per-leg lines precede `admission.reasons`, and n64 wording is "not measured" (no "held") | unit | `-k lead` | ❌ |
| RPT-04 | installed spans == fresh render (both stems) | unit | `-k byte_identical` | ❌ |
| RPT-04 | placement: PHASE34 report after PHASE28-REPORT-END; glance directly above PHASE28-GLANCE-BEGIN; zero deletions | unit | `-k placement` | ❌ |
| RPT-04 | v4.0 frozen block still byte-identical | unit | `pytest tests/test_phase28_report.py` (after the 3 amendments) | ✅ (edit) |
| RPT-04 | renderer torch-free, clock-free, no `rev-parse` | unit | `-k torch or clock` | ❌ |
| RPT-04 | provenance digests recompute; `admission.frontier.sha256` == frontier digest | unit | `-k provenance` | ❌ |
| RPT-04 | ledger schema/domain/FIXED-needs-test/redump-stable/close shape/by-reference sha | unit | `pytest tests/test_phase34_ledger.py` | ❌ |
| RPT-05 | deps equal across the derived tag set + HEAD; missing tag RED; derivation non-vacuous | unit | `pytest tests/test_package.py` | ✅ (edit) |
| RPT-06 | `close.ci_run` success; head contains the publishing commit | unit + manual | `pytest tests/test_phase34_ledger.py -k close`; the developer push is manual | ❌ |

### Sampling Rate
- **Per task commit:** the quick run plus the census run plus both `check`s.
- **Per wave merge:** the full suite on a committed tree.
- **Phase gate:** full suite green locally, then push 2 green in CI, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_phase34_report.py`, `tests/test_phase34_ledger.py` (new)
- [ ] `tests/test_package.py` derived-tag test (edit)
- [ ] Plist host-path fixes in `tests/test_phase31_probe.py` and `tests/test_phase32_points.py` (push-1 prerequisite)

### Pre-push checklist (push 1 and push 2)
1. `git ls-remote --tags origin` lists v1.0–v4.0 (measured ✓).
2. Both plist tests are host-independent (Pitfall 2).
3. `phase28_report.py check` = 0 and the 6 guard files are green.
4. The `append_addendum` total is 3.
5. The full local suite is green on a committed tree, with skips recorded to compare with CI's 72.
6. `git status --short` is clean, and `.claude/scheduled_tasks.lock` (currently shown deleted) is not staged.
7. The developer runs `git push origin main`. Claude reads the run with `gh`.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2/V3/V4 | no | — (offline renderer) |
| V5 Input Validation | yes | records parsed from committed bytes; `resolve` raises on absence; `substitute` raises on a missing binding |
| V6 Cryptography | yes (integrity only) | stdlib `hashlib.sha256` per source (D-21) |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Hand-typed or edited numbers in the published block | Tampering | numeral scan + byte-identity re-render |
| Post-publish rewrite | Tampering | `install` refuses when sentinels exist; corrections go through `scripts/_addendum.py` |
| Claimed-green close without evidence | Repudiation | run id/head/url recorded; ancestry check of the publishing commit |
| Tag-less clone passing vacuously | Repudiation | shallow refusal + derived required-tag check |
| Push by an agent | Elevation | D-38. Claude never pushes; human checkpoint |

## Sources

### Primary (HIGH — measured in this session)
- `scripts/phase28_report.py` (full read), `tests/test_phase28_report.py`, `tests/test_phase28_ledger.py`, `tests/test_package.py`, `tests/test_phase25_correction.py:360-500`, `tests/test_phase29_prereg.py:420-600`, `tests/test_phase30_points.py:577-706`, `tests/test_phase21_sc5.py:170-215`, `tests/test_phase25_driver.py:341-362`, `tests/test_phase23_resume.py:255-290`, `tests/test_phase18_docs.py:955-980`, `tests/test_phase15_docs.py:334-420`
- `results/phase32_frontier.json`, `results/phase33_admission.json`, `results/phase28_ledger.json` (parsed)
- Scratch-clone install probe: `check=0`; `3 failed, 84 passed` over the six guard files
- `gh run list` / `gh run view 36433089806 --log-failed`; `git ls-remote --tags origin`; `git show f47468b`
- `.planning/milestones/v4.0-phases/28-…/28-07-SUMMARY.md` (push-1 failure causes, the 49057 frozen-bytes fix)

### Secondary
- 33-03-SUMMARY (staged rows), 32/33-SECURITY (AR rows), 29-02/03 SUMMARY (DEBT closures)

## Metadata

**Confidence breakdown:**
- Engine reuse and placement breakage: HIGH (executed)
- Record shapes: HIGH (parsed)
- CI state and push prerequisites: HIGH (run logs)
- Ledger dispositions: MEDIUM (the planner must re-measure each row per D-13)

**Research date:** 2026-09-28
**Valid until:** the next commit that touches `README.md`, `docs/REPORT.md`, `tests/test_phase28_report.py` or the records, or the next CI run

## Developer Rulings (2026-09-28, at plan-phase, before planning)

Premises re-measured by the orchestrator before asking: `gh run list --branch main` shows 36433089806 (schedule) and 36325420904 (push) both `failure`; f47468b is contained only in `origin/cursor/fix-plist-heartbeat-test-1976`; the three guards exist at `tests/test_phase28_report.py:542,575,654`.

- **R-1 (Open Question 1 / A2): AMEND after natural RED.** The three placement guards (`test_report_section_is_after_every_prior_heading`, `test_glance_deleted_nothing`, `test_write_installs_pre_publish_then_refuses`) are generalised in the publishing commit, only after they go RED naturally from the install, each carrying a dated-continuation comment (2026-09-28). `scripts/phase28_report.py` and every byte-identity test stay untouched.
- **R-2 (A3 / Pitfall 2): PORT the plist fix into a Phase 34 plan.** A wave-1 plan applies f47468b's approach to BOTH `tests/test_phase31_probe.py` and `tests/test_phase32_points.py` (~1045-1049), in its own commit, separate from the report commit, so push 1 can be green.
- **R-3 (Open Question 4): push 1's run id is recorded in the plan SUMMARY only.** `close.ci_run` in the v5.0 ledger holds only the final green run (Phase 28 key set); no `close.preflight_ci_run` key.
- Open Questions 2, 3, 5 are left to the planner's recommendation, surfaced to the developer at the pre-publish read checkpoint (28-06-style).
