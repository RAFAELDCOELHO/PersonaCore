# Handoff: from draft to paper

## What this is

A pre-registered audit of whether one taught fact can be removed from a rank-8 LoRA adapter over a
13.9M-parameter decoder, with a methodological finding: exposure rank and generation recall
disagree about the collateral damage, and the rank-based stopping point moves with the candidate-set
size. The target is an arXiv preprint (cs.LG), no page limit, full appendices.

The text is finished as an argument. What remains is typesetting, prose polish, and the
bibliography. Nothing in the results is open.

## Files

- `erasure_draft.md`: the only hand-edited source. Every number in it was bound to a committed
  record, either by a generator or by a script that reads the record.
- `figure1_three_instruments.svg`: generated from the committed records. Convert it to a vector PDF
  for LaTeX. Do not redraw it, restyle the data, or re-plot it.
- `erasure_kstar_tables.md`: generated. Appendix D of the draft is a byte-for-byte copy of it.
- `MANIFEST.sha256` and `REPO_HEAD.txt`: the hashes of these files and the repository commit they
  were taken from.

## Rules that cannot bend

1. **No number is retyped, rounded, recomputed or added.** If a sentence needs a number the draft
   does not contain, write `[TODO: source]` and stop. Small-looking numbers count: "24, 18, 2 and 0
   of 27" is a result.
2. **Do not strengthen or weaken a claim.** Keep every hedge and scope statement: one target fact,
   one greedy ordering, one adapter, one seed; "post hoc"; "bracket (32, 64]"; "at most"; "not a
   measurement of forgetting in this setting". Do not add generalization claims.
3. **Keep the disclosures exactly.** (a) The gate's verdict was reached along a hand-driven path
   around five published defects in the closed pin (the table in Section 6.1), and mechanical
   reproducibility of that verdict by the pin alone is withheld. (b) The k* extension is post hoc
   (Section 3.8 and item 7 of Section 6). (c) No relearning attack was run.
4. **Appendices A, B and D are verbatim.** They are emitted from code or copied from a generated
   file. Do not reflow text inside the quotations or edit table cells.
5. **The verdict is the gate's return value at k = 78: FAILURE.** The extension computes no verdict
   (Section 3.8). Do not write one.
6. **Do not invent, add or substitute citations.** See below.

## Citations

Resolve each reference by identifier and confirm it is the work the sentence describes.

- Checked against arXiv: 2410.02879; 2406.13356 (the final version is titled "Unlearning or
  Obfuscating? Jogging the Memory of Unlearned LLMs via Benign Relearning", ICLR 2025); 2401.06121
  (TOFU).
- **Not yet checked:** every other identifier, every venue and year, and, for every reference,
  whether the work says what Section 7 attributes to it. List each unchecked reference as such in
  the change log.
- Two different first authors are cited as "Hu et al." (LoRA and the relearning paper). Tell them
  apart by year.
- The sentences about benchmark model sizes are deliberately unspecific ("orders of magnitude
  larger"). Replace that with a number only if you cite each benchmark's model size.

## AI-use statement

The paper needs a short statement of which AI tools produced code and text, consistent with the
project's `AUTHORSHIP.md`. The human author is responsible for every claim.

## What to return

1. The paper source (LaTeX preferred), and confirmation that it builds.
2. A change log listing every edit that touched a sentence containing a number, a hedge or a
   citation.
3. A list of every `[TODO]` you added.

## How the result will be checked

- `python paper/number_audit.py erasure_draft.md <your text> --skip '<bibliography lines>'` must
  report no new numbers that the draft lacks. Each new number will be traced to a source or
  removed. A second run with `--strict` compares every number by occurrence.
- Appendix D is compared byte for byte with `erasure_kstar_tables.md`.
- Every hedge in the draft is read against the rewrite.
