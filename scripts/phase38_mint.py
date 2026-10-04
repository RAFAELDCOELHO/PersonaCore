"""Phase 38 (RANK-01) — mint the E5 candidate sets from the frozen rule, one command.

    .venv/bin/python scripts/phase38_mint.py        # CPU, about a minute, no checkpoint

It proves its premises before minting anything: the Phase 17 report the names are cleared against
hashes to `phase38_prereg.PHASE17_REPORT_SHA256` (D-24), and the questions parsed from it equal
`phase17_isolation.held_out_by_slot()` slot by slot and in order (D-32). It then runs
`phase38_prereg.mint_all` at the frozen `SLACK_PER_SLOT` and `MAX_DRAWS`, and re-runs the four
Phase 17 minting filters on the union of the scored prefixes as a proof.

A name slot short of `SLACK_PER_SLOT` is a STOP that goes to Rafael with every slot's count (D-26):
nothing is written and the slack is never lowered.

On success it writes `results/phase38_minting.json` ONCE (clean tree, tracked pre-registration,
input records hashed from their bytes) and, once that record exists, re-mints and VERIFIES it
instead of writing, so an outsider's run exits 0. Nothing here decides a candidate: the rule is
`phase38_prereg`'s, and this command only runs it and records what it returned. It takes no
arguments.
"""

import datetime
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase38_prereg as prereg  # noqa: E402

from personacore.tokenizer import from_json  # noqa: E402

_ROOT = pathlib.Path(__file__).resolve().parent.parent

TOKENIZER = "artifacts/tokenizer.json"
INPUT_RECORDS = (prereg.PHASE17_REPORT, TOKENIZER)
MODULES = (
    "scripts/phase38_prereg.py",
    "scripts/phase38_mint.py",
    "scripts/phase14_factset.py",
    "scripts/phase17_persona_facts.py",
    "scripts/phase21_filler.py",
    "scripts/phase35_prereg.py",
    "scripts/phase17_personas.py",
    "scripts/phase17_isolation.py",
)


def _prove(condition, message):
    if not condition:
        raise SystemExit(f"[phase38_mint] {message}")


def _sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def report_bytes():
    """The Phase 17 report's bytes, the one source of the clearance completions and questions."""
    return (_ROOT / prereg.PHASE17_REPORT).read_bytes()


def phase17_proof(tok, slots, questions):
    """The four Phase 17 minting filters on the union of every slot's scored prefix.

    The scored prefix of a slot is its first max |R| - 1 cleared values (|R| counts the taught
    value). Each filter raises SystemExit itself on a failure.
    """
    import phase17_persona_facts
    import phase17_personas  # torch at import

    values = [v for row in slots.values() for v in row["cleared"][: row["max_set_size"] - 1]]
    functions = (
        phase17_personas.filter_token_budget,
        phase17_personas.filter_roundtrip,
        phase17_personas.filter_substring_disjoint,
        phase17_personas.filter_absent_from_questions,
    )
    phase17_personas.filter_token_budget({v: len(tok.encode(v)) for v in values})
    phase17_personas.filter_roundtrip(tok, values)
    phase17_personas.filter_substring_disjoint(values, phase17_persona_facts.FORBIDDEN_VALUES)
    phase17_personas.filter_absent_from_questions(values, questions)
    return {
        "passed": True,
        "values_checked": len(values),
        "functions": [f"{fn.__module__}.{fn.__name__}" for fn in functions],
    }


def derive():
    """Prove D-24 and D-32, mint every slot, prove the Phase 17 filters; the record body."""
    blob = report_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    _prove(
        digest == prereg.PHASE17_REPORT_SHA256,
        f"D-24 STOP: {prereg.PHASE17_REPORT} hashes to {digest}, not the pinned "
        f"{prereg.PHASE17_REPORT_SHA256}; the clearance would run against other completions",
    )
    completions, questions_by_slot = prereg.parse_completions(blob.decode("utf-8"))
    import phase17_isolation  # torch at import

    held_out = phase17_isolation.held_out_by_slot()
    for slot in prereg.SLOTS:
        _prove(
            list(questions_by_slot[slot]) == [item.question for item in held_out[slot]],
            f"D-32 STOP: the questions parsed for {slot} are not "
            "phase17_isolation.held_out_by_slot() in order",
        )
    tok = from_json(_ROOT / TOKENIZER)
    # Read at call time, never bound as defaults: the frozen values, or a test's monkeypatch.
    result = prereg.mint_all(
        tok,
        completions,
        questions_by_slot,
        per_slot=prereg.SLACK_PER_SLOT,
        max_draws=prereg.MAX_DRAWS,
    )
    questions = [q for slot in prereg.SLOTS for q in questions_by_slot[slot]]
    proof = phase17_proof(tok, result["slots"], questions)
    for slot, row in result["slots"].items():
        row["nested_sizes"] = list(prereg.nested_sizes(row["max_set_size"]))
        if slot in prereg.NUMERIC_RANGES:
            row["neighbour_counts"] = {
                str(n): sum(1 for i in row["neighbour_d1"] if i < n - 1)
                for n in row["nested_sizes"]
            }
    clearance = prereg.ENTRIES["e5_minting_rule"]["value"]["clearance"]
    return {
        "rule_entry": "phase38_prereg.ENTRIES['e5_minting_rule']",
        "approval": prereg.approval_block(),
        "completion_source": {
            "path": prereg.PHASE17_REPORT,
            "sha256": digest,
            "device": clearance["device"],
            "base_git": clearance["base_git"],
            "completions": prereg.COMPLETIONS_TOTAL,
        },
        **{k: result[k] for k in ("seed", "per_slot", "max_draws", "stream", "stop_draw")},
        "slots": result["slots"],
        "phase17_filter_proof": proof,
    }
