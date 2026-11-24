# Use of AI tools: the full account (recorded 2026-11-24)

The README of this repository has a short version of this text. Paths are relative to the
repository root, and "README line N" refers to `README.md` as of this commit.

This is a single-author project built with AI coding agents (`CITATION.cff:5-7`; `AUTHORSHIP.md`
lines 15–16). Each statement below names the record that supports it. Claude Code drafted this
text on 2026-11-24 from the records it cites.

`AUTHORSHIP.md` means `docs/AUTHORSHIP.md` on the branch `docs/authorship` (commit `86cda17`). Claude
Code wrote it from the repository's artifacts, and it covers milestone v4.0, Phases 20–25 (its lines
6–12; §4.1, line 227).

- **What the author did.**
  - He directed the work and decided which measurements to run and what to report
    (`paper/erasure_draft.md:795`).
  - In Phases 20–25 he made the calls the process reserves for a person: the locked decisions in
    each `CONTEXT.md`, the rulings on human-UAT items and the answers to blocking checkpoints
    (`AUTHORSHIP.md` §3.2, lines 184–190).
  - He performed the operator acts that the code refuses to perform (`AUTHORSHIP.md` §4.2, line 244).
  - Some of his calls are stored in his own words, for example the `CURVE_K = 16` choice
    (`scripts/mitigation_budget.py:443-450`) and the Phase 40 ruling
    (`results/phase40_noise_floor_report.md:9-11`).
- **What the agents did.**
  - The code, including the experiments, was written by AI tools under the author's direction,
    mainly Claude Code (Anthropic); the author reports that he typed none of it
    (`paper/erasure_draft.md:795-798`; `AUTHORSHIP.md` §9, item 1, line 471).
  - The agents made the decisions that each `CONTEXT.md` lists under *Claude's Discretion*
    (`AUTHORSHIP.md` §4.2, line 250).
  - They did the research passes and drafted the decision records. They wrote the plans, tests,
    summaries, verification, review and security reports, the commit messages and `AUTHORSHIP.md`
    itself (`AUTHORSHIP.md` §3.2, lines 184–188; §4.1, line 227).
  - The post-hoc extension of the paper was designed in conversation with Claude, and its rule,
    driver, tests and audit scripts were written with Claude outside Claude Code
    (`paper/erasure_draft.md:798-801`).
  - Claude produced the first draft of the paper and its LaTeX conversion
    (`paper/erasure_draft.md:801-803`).
  - A Cursor agent made 7 commits on 2026-09-01 (`git log --author="Cursor Agent"`; `AUTHORSHIP.md`
    §4.1, line 229). They made continuous integration pass on Linux, which included editing five
    test files (`a97b9ff`, `e1e1ca9`), and added the one-command demo, the license and the citation
    file. They also edited the README: 19 of its lines blame to them (`8875b0d`, `f98c52f`).
- **What git shows and does not show.** All other commits are under the author's identity: 2,472
  as `Rafael` and 4 as `RAFAELDCOELHO` (`git log origin/main --format=%an | sort | uniq -c`). So
  `git blame` attributes every line of the central modules to him, and that attribution says
  nothing about whether a person or a model wrote the line (`AUTHORSHIP.md` §3.1, lines 170–172).
  Only 205 of the 2,483 commits on `origin/main` carry a `Claude-Session:` trailer
  (`git log origin/main --format=%B | grep -c '^Claude-Session:'`).
- **What does not depend on who wrote a line.**
  - The v3.0 erasure rule is code committed before the data it judges: `scripts/erasure_gate.py`
    entered in `23a830c`, and a test checks in git that this commit precedes every v3.0 result
    (`tests/test_phase16_prereg.py:176`).
  - Corrections to a frozen rule are dated continuations, not edits (`AUTHORSHIP.md` lines
    60–61).
  - Negative and null results are reported with the verdict the committed rule returned. For
    example, the erasure verdict is `FAILURE` (`results/phase19_erasure_report.md:9`), and the
    mitigation frontier has 0 PASS, 32 FAIL, 6 INCONCLUSIVE and 6 REFUSED
    (`results/phase25_frontier.json`, `verdicts.tallies`).
- **Responsibility.**
  - No AI system is listed as an author (`CITATION.cff:5-7`).
  - For the paper, the author is responsible for every claim in it
    (`paper/erasure_draft.md:807-808`).
