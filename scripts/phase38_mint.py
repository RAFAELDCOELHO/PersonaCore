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
import fnmatch
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import phase25_run  # noqa: E402  — atomic_write_json, the one os.replace writer
import phase38_prereg as prereg  # noqa: E402

from personacore.provenance import git_sha, refuse_if_dirty  # noqa: E402
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


def write_record(derived, path, *, base, run):
    """Write ``derived`` to ``path`` ONCE: minting path, no overwrite, tracked prereg, clean."""
    path = pathlib.Path(path)
    rel = path.relative_to(base).as_posix()
    _prove(
        fnmatch.fnmatch(rel, prereg.MINTING_GLOB),
        f"{rel} does not match MINTING_GLOB {prereg.MINTING_GLOB!r}: the mint writes nothing else",
    )
    _prove(
        not path.exists(),
        f"{path} exists — REFUSING to overwrite it. The minting record is write-once; corrections "
        "are dated continuations",
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "scripts/phase38_prereg.py"],
        cwd=_ROOT,
        capture_output=True,
    )
    _prove(
        tracked.returncode == 0,
        "the pre-registration scripts/phase38_prereg.py is not tracked: a record cannot precede it",
    )
    pathspec = ("scripts", "src", "results")
    if path.is_relative_to(_ROOT):
        pathspec += (f":(exclude){path.relative_to(_ROOT).as_posix()}",)
    refuse_if_dirty(
        who="phase38_mint",
        detail=(
            "the minting record publishes git_sha and hashes the rule's modules and its input "
            "records from the working tree; lists minted from a dirty tree name a commit they "
            "cannot be re-minted from"
        ),
        pathspec=pathspec,
        cwd=_ROOT,
    )
    record = {
        **derived,
        "input_sha256": {r: _sha256(_ROOT / r) for r in INPUT_RECORDS},
        "provenance": {
            "run": {
                key: run[key]
                for key in ("git_sha", "device", "torch_version", "started_utc", "finished_utc")
            },
            "module_sha256": {r: _sha256(_ROOT / r) for r in MODULES},
            "head_at_write": git_sha(),
            "written_utc": _now(),
        },
    }
    phase25_run.atomic_write_json(path, record)
    return record


def check_record(derived, path):
    """Verify an existing minting record against a fresh mint and fresh input digests."""
    record = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    for key, value in derived.items():
        plain = json.loads(json.dumps(value))  # tuples -> lists, as the record stores them
        _prove(
            record.get(key) == plain,
            f"STOP: the record's {key} differs from the fresh mint; re-minting does not "
            "reproduce it",
        )
    fresh = {r: _sha256(_ROOT / r) for r in INPUT_RECORDS}
    _prove(
        record.get("input_sha256") == fresh,
        "STOP: an input record's bytes differ from the SHA-256 the minting record holds",
    )
    return record


def main(argv=None, *, out_root=None):
    if argv:
        raise SystemExit(__doc__)
    base = pathlib.Path(out_root).resolve() if out_root is not None else _ROOT
    os.chdir(_ROOT)  # git_sha() reads the process cwd
    path = base / prereg.MINTING_RECORD
    started = _now()
    derived = derive()
    finished = _now()
    if path.exists():
        check_record(derived, path)
        print(f"MINTING VERIFIED (record re-minted and matched) {path}")
    else:
        import torch  # only for the provenance version string

        run = {
            "git_sha": git_sha(),
            "device": "cpu",
            "torch_version": torch.__version__,
            "started_utc": started,
            "finished_utc": finished,
        }
        write_record(derived, path, base=base, run=run)
        print(f"MINTING WRITTEN {path}")
    print(f"  stop_draw: {derived['stop_draw']}  per_slot: {derived['per_slot']}")
    for slot, row in derived["slots"].items():
        print(f"  {slot}: n_cleared {row['n_cleared']}  max_set_size {row['max_set_size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
