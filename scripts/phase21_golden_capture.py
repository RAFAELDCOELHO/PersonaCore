"""ONE-TIME capture of the two v2.0 golden fixtures, BEFORE any Phase-21 source edit.

Phase 21 adds two additive kwargs whose entire claim is *"byte-identical to v2.0 when ``None``"* —
``build_bins(..., align_facts=None)`` (21-04) and ``render_family(..., forms=None)`` (21-05). That
claim is only falsifiable against bytes that PREDATE the kwarg, so this script runs in wave 1 and
writes:

  - ``tests/fixtures/golden_build_bins_v2.json``   — the v2.0 ``build_bins`` byte-level baseline
  - ``tests/fixtures/golden_render_family_v2.json`` — the v2.0 ``render_family`` byte-level baseline

    .venv/bin/python scripts/phase21_golden_capture.py

**WHY THE GIT CHECK IS THE FIRST THING THIS FILE DOES.** A golden fixture captured AFTER the edit
encodes the NEW behaviour as the OLD baseline, which silently turns every downstream identity
assertion into a tautology (T-21-05). Making that a *promise* would be worth nothing, so it is
MECHANICAL: ``_refuse_if_dirty()`` runs at module scope, ahead of the two sibling imports below, and
raises ``SystemExit`` if either captured file has staged or unstaged changes. Importing this module
runs that check — deliberately; there is no way to reach the capture code with a dirty tree.

**WHY THIS FILE IS NOT ``scripts/mitigation_*.py``.** That glob carries a hard import ceiling of
``{pathlib, sys, erasure_gate}`` (``tests/test_phase20_prereg.py:522``), which puts ``json`` and
``subprocess`` out of reach. A capture driver needs both, so it lives outside the glob — the same
rule/emission split D-22 records.

**WHY ``replay_ratio = 0.0`` IS LOAD-BEARING, not a default taken for convenience.** At any non-zero
ratio ``build_bins`` calls ``_prepend_replay``, which reads the PersonaChat replay bins under
``data/`` (``teach_persona.py:333-340``). ``data/`` is gitignored and machine-local
(``.gitignore:17``), so a fixture captured at a non-zero ratio would be unreproducible on CI —
precisely where the byte-identity claim has to hold (T-21-15). At ``0.0`` that branch is never
entered and the fixture depends on nothing outside git.

**WHAT MAKES THE CAPTURE REPRODUCIBLE.** Every input is pinned explicitly rather than inherited:
the seed (``seed_everything(SEED)``, the ``teach_persona.py:440-441`` idiom), the FROZEN tokenizer,
the fact tuple and its order, the register, and the replay ratio. Family ids are passed as
``teach_persona``'s own frozensets but ``render_episodes:251`` sorts them, and this script sorts
them again where it iterates directly — frozenset iteration order over strings varies with
``PYTHONHASHSEED`` across processes, so an unsorted iteration would produce a fixture that fails to
reproduce in a fresh interpreter.

**ON THE TWO FLOAT STATS.** ``build_bins`` returns ``float(np.mean(mask))`` (``:270``) and
``float(np.mean(lengths))`` (``:317``) — float64 means over integer arrays, deterministic for a
fixed array, and converted to Python floats so no numpy scalar repr can drift underneath them. They
travel inside ``stats_repr`` and are compared by exact ``repr`` equality. A drift there is a FINDING
worth surfacing, not noise worth tolerating. The bin ``sha256`` values are captured and asserted
separately and unconditionally, so a float surprise can never weaken the byte-level guarantee.

**ON ``meta.tokenizer_sha256``.** The bins are a function of the tokenizer, and
``artifacts/tokenizer.json`` is FROZEN. Recording its hash is what lets a consuming test tell a
STALE fixture from a code regression (T-21-16) instead of reporting one as the other. It is recorded
for the ``build_bins`` fixture only: ``render_family`` never touches the tokenizer, and pinning an
irrelevant input there would invite a false STALE reading later.
"""

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

GOLDEN_BUILD_BINS = _REPO_ROOT / "tests" / "fixtures" / "golden_build_bins_v2.json"
GOLDEN_RENDER_FAMILY = _REPO_ROOT / "tests" / "fixtures" / "golden_render_family_v2.json"

# The two files whose v2.0 behaviour these fixtures freeze. Both are edited later in this phase —
# `teach_persona.py` by 21-04, `phase14_factset.py` by 21-05 — which is the whole reason the
# capture must observably precede them.
WATCHED = ("scripts/teach_persona.py", "scripts/phase14_factset.py")

# The exact json.dumps kwargs the render capture hashes through. Recorded INTO the fixture so the
# consuming test reads its serialization from the fixture instead of retyping it — a retyped
# separator is a wrong separator, and it would fail as a behaviour change.
RENDER_SERIALIZATION = {"ensure_ascii": False, "sort_keys": False, "separators": [",", ":"]}


def _git(*args):
    """Run a git command at the repo root and return its stripped stdout."""
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _refuse_if_dirty():
    """Abort unless both captured files are clean in git. See this module's docstring."""
    dirty = _git("status", "--porcelain", "--", *WATCHED)
    if dirty:
        raise SystemExit(
            "[phase21_golden_capture] REFUSING to capture: the working tree is dirty for "
            f"{' and/or '.join(WATCHED)}.\n{dirty}\n"
            "A golden fixture captured AFTER the edit encodes the NEW behaviour as the OLD "
            "baseline, which turns every 'byte-identical to v2.0 when None' assertion downstream "
            "into a tautology. This refusal is why that constraint is mechanical and not a "
            f"promise. Restore with `git checkout -- {' '.join(WATCHED)}` and re-run."
        )


_refuse_if_dirty()  # BEFORE the two imports below — the check is worthless after them.

import phase14_factset as fs  # noqa: E402  (sibling script; the path insert above is what finds it)
import teach_persona as tp  # noqa: E402


def _sha256_file(path):
    """sha256 of a file read as BYTES.

    Never as text: a text read normalizes line endings, so a CRLF rewrite would pass a text-mode
    hash while changing the file on disk (``tests/test_package.py:33-35``).
    """
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _write(path, payload):
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[phase21_golden_capture] wrote {path.relative_to(_REPO_ROOT)}")


def capture_build_bins(captured_at_sha):
    """The v2.0 ``build_bins`` baseline: today's `real` fact set, taught families, replay 0.0."""
    tp.seed_everything(tp.SEED)
    tok = tp.from_json(tp.TOKENIZER_PATH)  # FROZEN production artifact — never retrain

    facts = fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS  # `arm_spec('real')`, teach_persona.py:418
    family_ids = fs.TAUGHT_FAMILY_IDS
    second_person = False
    replay_ratio = 0.0

    episodes = tp.render_episodes(facts, family_ids, second_person=second_person)

    # Under a temp dir, never `data/` and never a `tp.arm_outputs(...)` path: a capture must not be
    # able to overwrite an arm's RECORDED evidence (T-21-17).
    with tempfile.TemporaryDirectory() as tmp:
        bin_path = pathlib.Path(tmp) / "tokens.bin"
        mask_path = pathlib.Path(tmp) / "mask.bin"
        stats = tp.build_bins(tok, episodes, bin_path, mask_path, replay_ratio=replay_ratio)
        payload = {
            "meta": {
                "captured_at_sha": captured_at_sha,
                "arm": "real-facts-taught-families",
                "facts": [f.id for f in facts],
                "family_ids": sorted(family_ids),
                "second_person": second_person,
                "replay_ratio": replay_ratio,
                "tokenizer_sha256": _sha256_file(tp.TOKENIZER_PATH),
                "recipe": (
                    "seed_everything(SEED); tok = from_json(TOKENIZER_PATH); "
                    "episodes = render_episodes(LOCKED_FACTS + SOFT_TIER_FACTS, "
                    "TAUGHT_FAMILY_IDS, second_person=False); "
                    "build_bins(tok, episodes, <tmp>/tokens.bin, <tmp>/mask.bin, "
                    "replay_ratio=0.0)"
                ),
            },
            "token_bin_sha256": _sha256_file(bin_path),
            "mask_bin_sha256": _sha256_file(mask_path),
            "token_bin_bytes": os.path.getsize(bin_path),
            "mask_bin_bytes": os.path.getsize(mask_path),
            "stats_repr": repr(stats),
        }

    # uint16 ids against uint8 mask over a 1:1-aligned pair (`build_bins` proof 1) — exactly 2x.
    assert payload["token_bin_bytes"] == 2 * payload["mask_bin_bytes"], payload
    _write(GOLDEN_BUILD_BINS, payload)
    return payload


def main():
    _refuse_if_dirty()  # again at call time: import may have happened arbitrarily long ago
    tp.refuse_if_exists([GOLDEN_BUILD_BINS, GOLDEN_RENDER_FAMILY])

    captured_at_sha = _git("rev-parse", "HEAD")
    build = capture_build_bins(captured_at_sha)

    print(f"[phase21_golden_capture] captured at {captured_at_sha}")
    print(f"[phase21_golden_capture] build_bins  {build['stats_repr']}")


if __name__ == "__main__":
    main()
