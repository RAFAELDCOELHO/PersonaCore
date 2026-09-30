"""Compare the numbers of a rewritten paper against the reference draft.

    python paper/number_audit.py REFERENCE REWRITTEN [--strict] [--skip REGEX]

The reference draft is the only text whose numbers were bound to records, so any number in the
rewrite that the draft does not contain is a candidate for a retyped, rounded or invented value.
Exit status 1 if the rewrite contains such a number; numbers the rewrite dropped are reported too
but do not fail the audit, because deleting a sentence is legitimate.

Default mode is a coarse net: it compares numbers with a decimal point, a slash, a percent sign or
at least three digits, plus 40+ character hex digests. It does NOT see bare small integers, and
the results live partly there ("24, 18, 2 and 0 of 27"). `--strict` compares every number by
occurrence count, which catches a changed 24 but also fires on section numbers and references.
`--skip REGEX` drops matching lines from both texts (use it for a bibliography).
"""

import re
import sys
from collections import Counter

HEX = re.compile(r"\b(?=[0-9a-f]*[a-f])[0-9a-f]{6,}\b")
DIGEST = re.compile(r"\b[0-9a-f]{40,64}\b")
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?:/\d[\d,]*)?%?")


def significant(token):
    return any(c in token for c in "./%") or len(token) >= 3


def occurrences(text, skip=None):
    """(token, line) for every number and long digest in `text`, thousands commas removed."""
    found = []
    for line in text.splitlines():
        if skip and re.search(skip, line):
            continue
        for digest in DIGEST.findall(line):
            found.append((digest, line))
        cleaned = HEX.sub(" ", line)
        for match in NUMBER.finditer(cleaned):
            found.append((match.group().replace(",", ""), line))
    return found


def audit(reference, rewritten, strict=False, skip=None):
    ref, new = occurrences(reference, skip), occurrences(rewritten, skip)

    def keep(token):
        return strict or significant(token) or len(token) >= 40

    ref_count = Counter(t for t, _ in ref if keep(t))
    new_count = Counter(t for t, _ in new if keep(t))
    if not strict:
        ref_count, new_count = Counter(set(ref_count)), Counter(set(new_count))
    context = {}
    for token, line in new:
        context.setdefault(token, []).append(line.strip()[:110])
    return {
        "new": sorted((new_count - ref_count).items()),
        "dropped": sorted((ref_count - new_count).items()),
        "context": context,
    }


def report(result):
    out = [f"NEW numbers, not in the reference: {len(result['new'])}"]
    for token, extra in result["new"]:
        shown = result["context"].get(token, ["?"])[0]
        out.append(f"  {token}  (+{extra})  | {shown}")
    out.append(f"DROPPED numbers, in the reference only: {len(result['dropped'])}")
    for token, missing in result["dropped"]:
        out.append(f"  {token}  (-{missing})")
    return "\n".join(out)


def main(argv):
    args = list(argv)
    strict = "--strict" in args
    args = [a for a in args if a != "--strict"]
    skip = None
    if "--skip" in args:
        at = args.index("--skip")
        skip = args[at + 1]
        del args[at : at + 2]
    if len(args) != 2:
        raise SystemExit("usage: number_audit.py REFERENCE REWRITTEN [--strict] [--skip REGEX]")
    texts = [open(path, encoding="utf-8").read() for path in args]
    result = audit(texts[0], texts[1], strict=strict, skip=skip)
    print(report(result))
    return 1 if result["new"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
