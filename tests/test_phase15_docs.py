"""DOC-02 / D-15 / D-16 / D-17 doc-integrity contracts for the v2.0 narrative.

CPU-only, GPU/MPS-free, no torch, no network, no ``subprocess``. This module reads committed
markdown and committed JSON and nothing else. Pins:
  1. ``test_limitations_quotes_are_verbatim`` — D-15. Each of the NINE Limitations blockquotes in
     ``docs/REPORT.md`` reproduces its cited source's exact wording under the
     ``<verbatim_normalization>`` rule, ellipsis fragments appear in SOURCE ORDER, the count is
     nine, and the claim-bound group ordering holds. Prevents a limitation being paraphrased,
     softened, truncated invisibly, reordered, or quietly dropped back to eight.
  2. ``test_headline_numbers_match_sources`` — D-16. Each of README's three headline numbers
     appears in its cited source report AND shares its bullet with the qualifier keyphrases that
     bound it; the bare ``see Limitations`` pointer is absent; R1's corrected tokenizer-corpus
     attribution is present and the wrong one is gone; and README's + ``demo_v2.ipynb``'s links
     into the report's Limitations section resolve to a heading that actually exists. Prevents a
     front-page number drifting from its source, losing its caveat, or pointing at nothing.
  3. ``test_verdict_section_is_dated_and_separated`` — D-17. The Phase 15 correlation addendum in
     ``results/phase13_ab_report.md`` is read SECTION-ANCHORED (the CR-02 shape), carries a Phase
     15 marker, a ``YYYY-MM-DD`` date and the does-not-reopen-or-amend statement, sits after every
     pre-existing Phase 13 heading, and has displaced none of them. Prevents an append blending
     into or overwriting a prior phase's recorded evidence.
  4. ``test_report_names_the_artifact_vmax_driver`` — D-02 / D-04 / D-18 / ROADMAP SC3. Inside a
     section-anchored read of ``### The Two Signature Figures``, the report names the same
     ``vmax_driver`` layer/projection and value that ``scripts/plot_phase15.py`` reads from
     ``results/phase15_norms.json``, names every block's ``nonpositive_cells`` count, and carries
     ``blocks.fisher.variant`` verbatim. Prevents the caption and the report saying different
     THINGS rather than different amounts, and prevents SC3's Fisher variant going unnamed.

**Why a convention needs a test.** D-15's exact-quote rule, D-16's inline-qualifier density and
D-17's separation of appended Phase 15 material from Phase 13's recorded evidence are all
POLICIES. A future edit can break any of them silently while every other test in this repo stays
green, because nothing else in the suite reads prose. The Limitations section in particular is
the deliverable most able to be quietly softened: **paraphrase-to-shorten and severity-reordering
are editorializing disguised as editing**, and both look like ordinary copy-editing in a diff.
This file is what makes them a test failure instead of a proofreading miss — the doc-side
instance of the same declared-invariant-becomes-structural move D-07 makes for the plotting path
and D-17/D-18 made for Phase 14's demo.
"""

import importlib.util
import json
import math
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# The one file that cites ITSELF: L8 carries a Milestone 1 passage from this same report forward
# into the Milestone 2 Limitations section.
_SELF_CITED = "docs/REPORT.md"

_LIMITATIONS_HEADING_PREFIX = "## Milestone 2 Limitations"


def normalize_quote(text: str) -> str:
    """Whitespace and blockquote markers ONLY. See ``15-05-PLAN.md`` ``<verbatim_normalization>``.

    Strip at most ONE leading ``>`` (plus at most one following space) per line, then collapse
    every whitespace run — newlines included — to a single space.

    **Why this exists, so a future reader does not mistake it for a relaxation.** D-15's locked
    intent is that a limitation is reproduced without being softened, summarized or reordered. It
    is a claim about *wording*, not about file encoding. The Limitations entries are markdown
    blockquotes, so a correctly-written quote necessarily rewraps its source's lines and prefixes
    each with ``> ``. That is presentation, and it changes no word — but it means a correct quote
    is NEVER a raw byte-substring of its source. Provable on L8: the phrase
    ``the bounded TinyStories corpus`` spans a newline at ``docs/REPORT.md:61-62``, so
    ``grep -F 'the bounded TinyStories corpus' docs/REPORT.md`` correctly returns no match today.
    The normalization is what makes D-15 mechanically checkable at all.

    **What it MUST NOT do, and this is the whole basis of its legitimacy.** It alters no word, no
    digit, no punctuation mark, no markdown emphasis marker, and not the ``…`` truncation
    ellipsis. If a future edit adds any other substitution — case folding, punctuation stripping,
    ellipsis handling, smart-quote folding — the rule has stopped being presentation-normalization
    and has become the softening D-15 exists to close. Adding one is a VIOLATION, not a
    refinement. Both sides of every comparison go through this function; a normalized quote is
    never compared against a raw source.
    """
    unquoted = re.sub(r"(?m)^[ \t]*>[ \t]?", "", text)
    return re.sub(r"\s+", " ", unquoted).strip()


def _read(rel_path: str) -> str:
    """Read a committed file and refuse to return an empty string.

    The meta-guard habit from ``tests/test_phase14_scoring.py:423-424``: a renamed or emptied
    report must fail loudly here rather than make every substring assertion below pass vacuously.
    """
    path = _REPO_ROOT / rel_path
    assert path.exists(), f"{rel_path} is missing — a cited source was renamed or deleted"
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{rel_path} read empty"
    return text


def _anchored_section(text: str, heading: str, stop: str = r"## ") -> str | None:
    """The slice from ``heading`` at line start up to the next ``stop`` heading, or EOF.

    Anchored on the SECTION, never ``text.split(<heading>)[-1]``. That last-occurrence form is
    the CR-02 failure recorded at ``scripts/phase14_recall.py:1627-1635`` and shared out as
    ``scripts/_verdict.py::VERDICT_SECTION``: a later section that QUOTES a heading string in its
    own prose put the tail inside that prose, and the guard read the wrong text. The reports this
    module reads do exactly that — ``results/phase13_ab_report.md`` names ``## Pre-Registration``,
    ``## Gate Verdict`` and ``## Verdict`` inside the Phase 15 addendum's separation comment — so
    the anchored form is a correctness requirement here, not a style preference.
    """
    pattern = re.compile(rf"^{re.escape(heading)}\b.*?(?=^{stop}|\Z)", re.M | re.S)
    found = pattern.search(text)
    return found.group(0) if found else None


# --------------------------------------------------------------------------- #
# D-15 — the nine Limitations quotes
# --------------------------------------------------------------------------- #

# ``(limitation_id, source_path, quote)``. Every quote below is the blockquote AS ACTUALLY
# WRITTEN in ``docs/REPORT.md``'s Limitations section, ``> `` markers and line wrapping included;
# every ``source_path`` is the citation that entry carries. Raw strings so L1's ``λ\*`` survives.
_LIMITATION_QUOTES = (
    (
        "L1",
        "results/finetune_smoke_report.md",
        r"""
> **EWC not demonstrable at this budget** (no λ satisfies both the within-margin rule and the
> retention demonstrability guard) — surfaced, never massaged (pre-registered §8 all-fail
> outcome: λ\* = None, demonstrable = False).
""",
    ),
    (
        "L7",
        "results/phase13_ab_report.md",
        r"""
> **Named limitation (D-05 obligation 2):** that floor was **NOT re-verified at the 4000-step
> production budget**, and **NOT re-verified inside collapse dynamics** — it was measured in a
> stable regime, on the masked arm, at a shorter budget, while both Phase-13 arms are unmasked
> and one of them drifts by +6.42 PPL. **Seed-to-seed variance could plausibly scale with drift
> magnitude**, and a floor measured in a stable regime would not capture that. Nothing here rules
> that out.
>
> …
>
> That is corroboration from a free check, not a re-measurement — the honest re-measurement (a
> 1337/2024 seed pair at 4000 unmasked steps, ~75 min) was not run.
""",
    ),
    (
        "L4",
        "results/phase14_recall_report.md",
        r"""
> **Measured.** With each fact's own first-person statement in the `<|system|>` persona span, the
> base (adapter off) scored **1/1944 = 0.0005** across 216 questions; 1 of those questions
> produced at least one completion containing the value. This is the ONLY place in the entire
> phase where a fact value legitimately appears in a prompt.
""",
    ),
    (
        "L2",
        "results/phase14_recall_report.md",
        r"""
> See `## Control 1 — Question Fairness (D-11.1)`, part (a). In-context answerability could not be
> established at this scale, so a closed-book failure **in isolation** is not unambiguous evidence
> of absent memory. The adapter-on / adapter-off differential is unaffected (part (b)), but any
> reading of a single failed question as "the model does not know this" is out of scope.
""",
    ),
    (
        "L6",
        "results/phase14_recall_report.md",
        r"""
> **Consequence for what a clean held-out result may claim:** it demonstrates generalization
> **within that scope** — across held-out template families in the taught direction — and **not**
> immunity to every documented fine-tuning limitation. This report makes no claim about reversed
> recall, because this phase did not measure it as a held-out property.
""",
    ),
    (
        "L5",
        "results/phase14_recall_report.md",
        r"""
> See `## Soft Tier — Excluded From The Gate (D-05)`. Two of the taught facts contribute nothing to
> either threshold, so the headline number describes the proper-noun core only — a narrower set
> than "everything the adapter was taught."
""",
    ),
    (
        "L3",
        "results/phase14_calibration_report.md",
        r"""
> **What the paired arm shows replay actually BUYS, and what it costs.** Replay at ratio 1.0 moves
> the collapse from +224.81% to +29.39% — a large mitigation — while taught recall falls from
> 0.6825 to 0.4143, a fall of 0.2683. **The replay arm ITSELF still trips the trigger.** Replay at
> this ratio reduces the collateral collapse but does not eliminate it, so 'replay required'
> should not be read as 'replay solves it'.
>
> …
""",
    ),
    (
        "L9",
        "results/phase14_recall_report.md",
        r"""
> (1) No-collateral-collapse (D-11 control 2): the taught persona measurably raises off-topic
> dialogue cost (+27.16%) relative to the pre-adapter conversational base, but does not eliminate
> the collapse signature entirely. The adapter reduces, rather than removes, deviation from
> general conversational behavior on unrelated prompts.
>
> …
""",
    ),
    (
        "L8",
        _SELF_CITED,
        r"""
> **What actually trained.** Training learned 283 of the 7,928 requested merges before the
> bounded TinyStories corpus exhausted its mergeable pairs — the trainer itself warns
> "corpus exhausted: learned 283 of 7928 requested merges; vocab_size=8192 has 7645 dead ids".
> The *effective* vocabulary is therefore 547 live ids (256 bytes + 283 learned merges + 8
> specials); the locked 8192-row table is reserved capacity. The trade-off is stated plainly:
> shape stability for every downstream checkpoint, in exchange for 7645 dead rows the model
> carries in its embedding table.
>
> …
>
> Of the headline count, 2,935,680 parameters (7645 dead rows × 384 dims, ~21%) are embedding
> rows for ids that can never occur in the training data or be decoded — counted in the headline
> because they are part of the shipped tensor.
""",
    ),
)

# The four claim groups, in the order D-15 requires: ordered by WHICH CLAIM each bounds, never by
# severity and never by how comfortable each is to read. A future reshuffle is editorializing.
_CLAIM_GROUP_HEADINGS = (
    '### Bounding "EWC mitigates forgetting"',
    '### Bounding "memory lives in the weights"',
    '### Bounding "…without damaging the base"',
    '### Bounding "13.9M-parameter from-scratch base"',
)


def _first_missing_fragment(quote: str, normalized_source: str) -> str | None:
    """The first ``…``-delimited fragment not found in ``normalized_source`` IN ORDER.

    Truncation semantics are preserved by walking the source with an advancing ``str.find``
    cursor: a truncation that reorders its fragments is a paraphrase wearing an ellipsis.
    """
    cursor = 0
    for fragment in (f for f in (normalize_quote(p) for p in quote.split("…")) if f):
        found = normalized_source.find(fragment, cursor)
        if found < 0:
            return fragment
        cursor = found + len(fragment)
    return None


def test_limitations_quotes_are_verbatim():
    """D-15: every Limitations quote reproduces its cited source's exact wording.

    Both sides go through ``normalize_quote`` — whitespace and ``> `` markers only. ``grep`` is
    NOT usable for these nine and is deliberately absent from this module: grep is line-oriented
    and five of the nine (L2, L5, L6, L7, L8) span multiple source lines, so a line-oriented
    check is not merely weaker, it is unrunnable and reports a false failure.
    """
    # Meta-guard 1: the R2 count. Nine, not eight — a future edit cannot quietly drop one.
    assert len(_LIMITATION_QUOTES) == 9, "the Limitations fixture must carry all nine negatives"

    report = _read("docs/REPORT.md")
    section = _anchored_section(report, _LIMITATIONS_HEADING_PREFIX)

    # Meta-guard 2: the anchored read found something. This anchoring is LOAD-BEARING for L8: the
    # phrase `the bounded TinyStories corpus` also lives in the untouched v1.0 text at
    # docs/REPORT.md:61, so a whole-file assertion would pass even if L8's blockquote had been
    # paraphrased away entirely.
    assert section, f"{_LIMITATIONS_HEADING_PREFIX!r} section not found in docs/REPORT.md"
    assert section.strip(), "the Limitations section anchored empty"
    normalized_section = normalize_quote(section)

    # The v1.0 half of the report — everything OUTSIDE the Limitations section. L8 cites this
    # same file, so comparing its quote against the whole working file is self-satisfying: the
    # blockquote would match itself and prove nothing.
    outside_limitations = report.replace(section, "")
    assert len(outside_limitations) < len(report), "the Limitations section did not excise"
    assert outside_limitations.strip(), "docs/REPORT.md is nothing but its Limitations section"
    normalized_outside = normalize_quote(outside_limitations)

    for limitation_id, source_path, quote in _LIMITATION_QUOTES:
        normalized_quote = normalize_quote(quote)
        assert normalized_quote, f"{limitation_id}: the fixture quote normalized to nothing"

        assert normalized_quote in normalized_section, (
            f"{limitation_id}: this quote is no longer in docs/REPORT.md's Limitations section "
            f"as written — a word, digit, punctuation mark or emphasis marker changed"
        )

        if source_path == _SELF_CITED:
            normalized_source = normalized_outside
        else:
            normalized_source = normalize_quote(_read(source_path))
        assert normalized_source, f"{limitation_id}: {source_path} normalized to nothing"

        missing = _first_missing_fragment(quote, normalized_source)
        assert missing is None, (
            f"{limitation_id}: fragment not found in {source_path} in source order — the quote "
            f"does not reproduce its source's exact wording: {missing[:120]!r}"
        )

    # R2 — the section states NINE and records how the ninth entered the record.
    assert "NINE honest negatives" in normalized_section
    assert "surfaced during Phase 15 research" in normalized_section

    # L8's key phrase, under normalization. It spans a newline in its source
    # (docs/REPORT.md:61-62), so `grep -F 'the bounded TinyStories corpus' docs/REPORT.md`
    # correctly returns NO match; it is contiguous only after normalization. Do not "fix" this
    # assertion by editing the quote — the quote is right and grep is the wrong tool.
    assert "the bounded TinyStories corpus" in normalized_section

    # R1 — the correction is present, evidence-named, and OUTSIDE the quote: it lives in the
    # section text that FOLLOWS L8's blockquote, not inside it.
    l8_quote = dict((lid, q) for lid, _, q in _LIMITATION_QUOTES)["L8"]
    after_l8 = normalized_section.split(normalize_quote(l8_quote), 1)[1]
    for evidence in ("train_tokenizer.py", "tiny_corpus.txt", "11,469"):
        assert evidence in after_l8, f"the L8 correction no longer names {evidence}"

    # Claim-bound ordering. Ordering by severity or by comfort is the editorializing D-15 forbids.
    positions = [section.find(heading) for heading in _CLAIM_GROUP_HEADINGS]
    absent = [h for h, p in zip(_CLAIM_GROUP_HEADINGS, positions) if p < 0]
    assert not absent, f"a claim-group heading is missing: {absent}"
    assert positions == sorted(positions), (
        "the claim groups have been reordered — D-15 orders by which claim each limitation "
        "bounds, never by severity"
    )


# --------------------------------------------------------------------------- #
# D-16 — README's three headline numbers
# --------------------------------------------------------------------------- #

# ``(label, number_string, source_path, qualifier_keyphrases)``. The number strings and the
# qualifier spellings are the ones Plan 15-06 actually wrote; `1.129` is deliberately absent
# because README renders it `1.129×` (U+00D7) while its source writes `1.129x` (ASCII).
_HEADLINE_NUMBERS = (
    (
        "recall (held-out)",
        "0.3483",
        "results/phase14_recall_report.md",
        ("proper-noun core", "reversed phrasings"),
    ),
    (
        "retention (naive arm)",
        "8.52417066884246",
        "results/phase13_ab_report.md",
        ("teacher-forced", "noise floor"),
    ),
    (
        "inflation (dialogue)",
        "3.229",
        "results/inflation_report.md",
        ("same-run baseline",),
    ),
)


def _github_anchor(heading_text: str) -> str:
    """GitHub's heading anchor: lowercase, spaces to hyphens, drop everything else non-alnum.

    The em dash collapses to the empty string, which is why the correct anchor carries a DOUBLE
    hyphen where the dash was. Derived from the heading as actually written, never retyped.
    """
    return "".join(c for c in heading_text.lower().replace(" ", "-") if c.isalnum() or c == "-")


def test_headline_numbers_match_sources():
    """D-16: each README headline number matches its source and carries its qualifier inline."""
    # Meta-guard: the fixture and the file under test both have content before any ABSENCE
    # assertion below — an empty README would otherwise satisfy every "does not contain" check.
    assert _HEADLINE_NUMBERS, "the headline-number fixture is empty"
    readme = _read("README.md")

    # Every headline bullet is multi-line, so bullets are split on the leading "- ", not on lines.
    bullets = re.split(r"\n(?=- )", readme)
    assert len(bullets) > len(_HEADLINE_NUMBERS), "README did not split into bullets"

    for label, number, source_path, qualifiers in _HEADLINE_NUMBERS:
        assert number in readme, f"{label}: {number} is no longer on the front page"
        assert number in _read(source_path), (
            f"{label}: {number} has drifted from its cited source {source_path}"
        )
        carrying = [b for b in bullets if number in b]
        assert len(carrying) == 1, (
            f"{label}: expected exactly one README bullet carrying {number}, found {len(carrying)}"
        )
        for qualifier in qualifiers:
            assert qualifier in carrying[0], (
                f"{label}: the bullet carrying {number} lost its inline qualifier {qualifier!r} — "
                f"a headline number without its bound is what D-16 exists to prevent"
            )

    # D-16 forbids the bare-pointer antipattern outright: a number's caveat may never be
    # OUTSOURCED to a link. The docs/REPORT.md links in those bullets are additive; each already
    # carries a complete inline qualifier above.
    assert "see Limitations" not in readme

    # R1 — README states the corrected tokenizer-corpus attribution directly (it carries no
    # stands-as-written protection, so it was fixed in place rather than by dated note).
    # Normalized, so a line wrap cannot hide the wrong attribution.
    assert "bounded TinyStories corpus" not in normalize_quote(readme)
    assert "tiny_corpus.txt" in readme
    assert "11,469" in readme

    # T-15-25 — the cross-document anchor resolves. Plans 15-05/15-06/15-07 ran in one wave and
    # could not check each other; this is where a dangling link becomes a failure.
    report = _read("docs/REPORT.md")
    heading = re.search(rf"^{re.escape(_LIMITATIONS_HEADING_PREFIX)}.*$", report, re.M)
    assert heading, "the Limitations heading is gone from docs/REPORT.md — every link dangles"
    link = f"docs/REPORT.md#{_github_anchor(heading.group(0).lstrip('# '))}"
    assert link in readme, f"README does not link to the Limitations heading as written ({link})"
    assert link in _read("demo_v2.ipynb"), f"demo_v2.ipynb's Limitations link dangles ({link})"


# --------------------------------------------------------------------------- #
# D-16 (extension) — the SIGNATURE number is bound to the artifact it came from
# --------------------------------------------------------------------------- #

# The four SHIPPED documents that restate the correlation in prose. `.planning/ROADMAP.md` also
# carries it but is a planning artifact, not a deliverable, and is deliberately out of scope so
# ordinary planning churn cannot redden a docs test.
_RHO_SITES = (
    "README.md",
    "docs/REPORT.md",
    "demo_v2.ipynb",
    "results/phase13_ab_report.md",
)

# ``render_verdict_section``'s two pre-authored branch words, keyed by whether the gate holds.
_VERDICT_WORD = {True: "GATE PASSES", False: "GATE MISSES"}


def _phase15_stats():
    """The pre-registered rule module, loaded BY PATH — ``scripts/`` is not an importable package.

    Pure numpy (no torch), so importing it keeps this module's stated no-torch contract. It is
    byte-frozen since the pre-registration commit; this test reads it, never writes it.
    """
    spec = importlib.util.spec_from_file_location(
        "phase15_stats", _REPO_ROOT / "scripts" / "phase15_stats.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_correlation_rho_matches_the_artifact_it_was_computed_from():
    """The signature number is RECOMPUTED, not string-matched against a hardcoded literal.

    ``_HEADLINE_NUMBERS`` protects three lesser numbers by asserting each appears in its cited
    source. That shape is too weak for rho, for two reasons:

      1. README renders rho in a PARAGRAPH, not a bullet, so the ``\\n(?=- )`` bullet split files
         it under an unrelated bullet and the inline-qualifier assertion would scan the wrong span.
      2. A literal row only catches PROSE drift. It cannot catch ARTIFACT drift — if
         ``results/phase15_norms.json`` were rebuilt from different checkpoints, a hardcoded
         `0.801544` would keep passing while the prose silently stopped describing the data.

    So this recomputes rho from the committed artifact through the frozen pre-registered rule and
    requires the prose to match THAT. It fails if either side moves independently of the other.

    This is also the only test that would catch a transposition of the naive and EWC arms in
    ``scripts/extract_deltas.py``: swapping them inverts ``naive - ewc``, flips rho to its negative,
    and emits the pre-authored MISS paragraph — while every prose site still read the old value.
    """
    stats = _phase15_stats()
    artifact = json.loads(_read("results/phase15_norms.json"))
    fisher, reduction = stats.load_pairs(artifact)

    # Meta-guard: a truncated artifact must not reduce this to a vacuous pass before any
    # membership assertion runs. ``load_pairs`` already raises on a malformed artifact; this
    # pins the count the pre-registration fixed.
    assert len(fisher) == len(reduction) == stats.N_CELLS, (
        f"expected {stats.N_CELLS} cell pairs from the artifact, got {len(fisher)}"
    )

    rho = stats.spearman(fisher, reduction)
    assert math.isfinite(rho), f"the recomputed correlation is not finite: {rho!r}"
    rendered = f"{rho:.6f}"

    for site in _RHO_SITES:
        assert rendered in _read(site), (
            f"{site} does not carry the correlation as recomputed from "
            f"results/phase15_norms.json ({rendered}) — either the prose drifted from the "
            f"artifact or the artifact was rebuilt without the prose following it"
        )

    # The recorded VERDICT WORD must follow from the recomputed number, not merely be present.
    # Without this, an arm transposition could flip the sign and the addendum would still read
    # 'GATE PASSES' while the underlying correlation had become negative.
    lo, hi, _degenerate = stats.bootstrap_ci(
        fisher, reduction, n_boot=stats.N_BOOT, seed=stats.SEED, alpha=stats.CI_ALPHA
    )
    expected_word = _VERDICT_WORD[bool(stats.ewc_dodges_high_fisher(rho, lo, hi))]
    addendum = _anchored_section(_read("results/phase13_ab_report.md"), _ADDENDUM_HEADING)
    assert addendum, "the Phase 15 addendum section is gone — the verdict has no recorded home"
    assert expected_word in addendum, (
        f"the recomputed correlation ({rendered}, CI [{lo:.6f}, {hi:.6f}]) implies "
        f"{expected_word!r}, which the recorded addendum does not state"
    )


# --------------------------------------------------------------------------- #
# D-17 — the appended verdict is dated, marked, and visibly separate
# --------------------------------------------------------------------------- #

_ADDENDUM_HEADING = "## Phase 15 Addendum"

# Every Phase 13 heading that existed before Phase 15 appended anything. An append can never have
# displaced one.
_PHASE_13_HEADINGS = (
    "## Pre-Registration",
    "## 2×2 Result",
    "## Gate Verdict",
    "## Threats to Validity",
    "## Figures",
    "## Evidence Index",
)


def test_verdict_section_is_dated_and_separated():
    """D-17: the Phase 15 addendum is dated, marked, last, and has displaced nothing.

    The section read is ANCHORED — never a ``str.split`` on the ``## Verdict`` heading literal
    taking ``[-1]``, nor any other last-occurrence substring read (the exact forbidden call is
    spelled out nowhere in this file so ``grep -c 'split(...)'`` stays a usable guard). This is
    not a style preference. That form is verbatim the
    CR-02 failure recorded at ``scripts/phase14_recall.py:1627-1635``: a guard took the tail after
    the LAST occurrence of a heading literal, a later section quoted that heading in its own
    prose, and the guard read the prose instead of the section. This exact file reproduces that
    condition — the addendum's separation comment quotes ``## Pre-Registration``,
    ``## Gate Verdict`` and ``## Verdict``, and its own sub-heading ``### Verdict`` is a prefix
    match for anything doing naive substring work. ``scripts/_verdict.py::VERDICT_SECTION``
    consequently matches NOTHING here (Phase 13's heading is ``## Gate Verdict``), so this test
    reuses that regex's SHAPE, anchored on the addendum's own heading.
    """
    report = _read("results/phase13_ab_report.md")

    headings = re.findall(r"^## .+$", report, re.M)
    # Meta-guard: the heading scan found something before anything is asserted about ordering.
    assert headings, "no `## ` headings found in results/phase13_ab_report.md — the scan broke"

    section = _anchored_section(report, _ADDENDUM_HEADING)
    assert section, f"{_ADDENDUM_HEADING!r} section not found — the D-17 append is gone"
    body = normalize_quote(section)
    assert body, "the addendum anchored empty"

    assert "Phase 15" in body, "the addendum no longer marks itself as Phase 15 material"
    assert re.search(r"\b\d{4}-\d{2}-\d{2}\b", body), "the addendum carries no YYYY-MM-DD date"
    # Normalized: the pre-registered renderer wraps this phrase across a hard line break, and the
    # renderer is byte-frozen at 0e1af98 (T-15-09) — the reader normalizes, the file does not move.
    assert "does not reopen or amend" in body

    assert ("GATE PASSES" in body) != ("GATE MISSES" in body), (
        "the addendum must record exactly one of GATE PASSES / GATE MISSES"
    )
    if "GATE MISSES" in body:
        # D-11's miss register, pre-registered before any number existed. The gate PASSED, so this
        # branch is dormant by design — it exists so a future re-drive that misses cannot record
        # the miss in softer language than the one that was locked in advance.
        assert "suggestive but not statistically demonstrated at n = 36" in body

    # Visibly separate, appended, not blended in: the addendum is the LAST `## ` heading.
    assert headings[-1].startswith(_ADDENDUM_HEADING), (
        f"the Phase 15 addendum is no longer the last `## ` heading (last is {headings[-1]!r}) — "
        f"an append that sits among Phase 13's sections reads as amending them"
    )

    for phase_13_heading in _PHASE_13_HEADINGS:
        assert phase_13_heading in headings, (
            f"{phase_13_heading!r} is gone from Phase 13's recorded evidence — the Phase 15 "
            f"append displaced it"
        )


# --------------------------------------------------------------------------- #
# D-02 / D-04 / D-18 / ROADMAP SC3 — the report names the artifact's own fields
# --------------------------------------------------------------------------- #

_FIGURES_HEADING = "### The Two Signature Figures"


def test_report_names_the_artifact_vmax_driver():
    """The figure caption and the report cannot disagree without this test going red.

    D-04's invariant is that a reader comparing figure and report finds **different amounts,
    never different things**. ``scripts/plot_phase15.py`` renders each block's ``vmax_driver``
    from ``results/phase15_norms.json``; this asserts the report names the same field values,
    read from the artifact rather than hardcoded a second time.

    The read is SECTION-ANCHORED on ``### The Two Signature Figures`` (pinned in ``15-05-PLAN.md``
    ``<pinned_headings>``). A whole-file substring fallback would be materially weaker: projection
    names like ``q_proj`` appear elsewhere in the report — the LoRA decision sections name all six
    — so a disclosure that had drifted into the wrong section would still pass.
    """
    artifact = json.loads(_read("results/phase15_norms.json"))
    blocks = artifact["blocks"]
    assert blocks, "results/phase15_norms.json carries no blocks"

    section = _anchored_section(_read("docs/REPORT.md"), _FIGURES_HEADING, stop=r"#{2,3} ")
    # Meta-guard, mandatory: a heading rename would otherwise make every assertion below pass
    # vacuously on an empty string — the exact failure mode tests/test_phase14_scoring.py:423-424
    # exists to prevent. Plan 15-05 had to add two following `### ` headings for this very reason;
    # without them the section ran to EOF and the anchoring proved nothing.
    assert section, f"{_FIGURES_HEADING!r} section not found in docs/REPORT.md"
    assert section.strip(), "the figures section anchored empty"
    # Normalized for the same reason the quotes are: the report's markdown is hand-wrapped, so a
    # layer/projection phrase or the variant string can legally straddle a line break.
    body = normalize_quote(section)

    for name, block in blocks.items():
        driver = block["vmax_driver"]
        phrase = f"layer {driver['layer']}'s `{driver['projection']}`"
        assert phrase in body, (
            f"{name}: the report does not name the artifact's vmax driver {phrase!r} — the "
            f"figure caption and the report would be free to disagree"
        )
        assert str(driver["value"]) in body, (
            f"{name}: the report does not carry the driver cell's value {driver['value']}"
        )
        # Pitfall 5 — the counts are STATED, never left for the figure to imply by looking clean.
        assert f"`nonpositive_cells` = {block['nonpositive_cells']}" in body, (
            f"{name}: the report does not state nonpositive_cells = {block['nonpositive_cells']}"
        )

    # ROADMAP SC3 requires *the named Fisher variant* in the v2.0 narrative. Asserting the
    # artifact's own string, inside the anchored section, is what makes "named" checkable instead
    # of a proofreading obligation. The coarse `regime` label is NOT the variant.
    variant = blocks["fisher"]["variant"]
    assert variant in body, f"SC3: the report does not name the Fisher variant {variant!r}"
