"""Run-once encode of PersonaChat self_revised -> the four dialogue bins (DATA-02/DATA-03).

The dialogue sibling of ``scripts/encode_corpus.py``: turn the two checksum-verified fb-dialog
files into flat aligned memmaps — ``data/dialog_{train,val}.bin`` (``np.uint16`` token streams)
plus ``data/dialog_{train,val}_mask.bin`` (``np.uint8`` D-01 loss masks), 1:1 length-aligned
per split. The split is PersonaChat's NATIVE file-level train/valid split, so no dialogue can
straddle the cut by construction (no-leakage discipline).

ALL tokenization flows through ``encode_dialogue`` — the SAME single path the inflation gate
measured (Pitfall 4: gate and bins can never tokenize differently). This script adds only the
D-07 persona cap (140 tokens, pinned in CONTEXT independent of the gate verdict): whole persona
lines are kept in order and dropping starts at the first line that would push the persona span
(``<|system|>`` token + persona ids — metric 2's accounting) past the cap. Line-granular, never
mid-line.

Gate governance (T-11-07): this script REFUSES to run unless ``results/inflation_report.md``
carries a recorded non-STOP ``## Verdict`` (GO/ADAPT — D-09) — verdict-before-format-hardening
is enforced in code, not convention. All sanity checks are loud ``SystemExit``s, never
``-O``-strippable bare asserts.

Run manually AFTER ``scripts/fetch_personachat.py`` and AFTER the D-09 verdict is recorded —
NOT part of automated verification:
  python scripts/prepare_dialog_corpus.py
Outputs the four ``data/dialog_*`` bins (gitignored).
"""

import pathlib
import re

import numpy as np

from personacore.dialogue import detokenize, encode_dialogue, parse_episodes
from personacore.tokenizer import from_json
from personacore.training.data import get_batch_memmap_masked

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"
REPORT_PATH = _REPO_ROOT / "results" / "inflation_report.md"  # carries the D-09 verdict
RAW_DIR = _REPO_ROOT / "data" / "raw" / "personachat"  # fetch_personachat.py's output
EOS_ID = 8184  # ModelConfig.eos_id — exactly one per dialogue (document separator only)

PERSONA_CAP = 140  # D-07: persona-span token budget (<|system|> + persona ids), line-granular
BLOCK_SIZE = 256  # ModelConfig.block_size — the smoke-draw window
MASK_FRACTION_BAND = (0.30, 0.70)  # Pitfall 14: ~0%/~100% means the mask is wrong (~45-55% ok)

# split name -> (input txt, token bin, mask bin) — PersonaChat's native file-level split.
SPLITS = {
    "train": (
        RAW_DIR / "train_self_revised.txt",
        _REPO_ROOT / "data" / "dialog_train.bin",
        _REPO_ROOT / "data" / "dialog_train_mask.bin",
    ),
    "val": (
        RAW_DIR / "valid_self_revised.txt",
        _REPO_ROOT / "data" / "dialog_val.bin",
        _REPO_ROOT / "data" / "dialog_val_mask.bin",
    ),
}


def _require_go_verdict(report_path):
    """T-11-07 gate: hard-exit unless the report's ``## Verdict`` section reads GO or ADAPT."""
    if not report_path.exists():
        raise SystemExit(
            f"[prepare_dialog_corpus] {report_path} missing — run "
            "`python scripts/measure_inflation.py` and record the D-09 verdict first."
        )
    text = report_path.read_text(encoding="utf-8")
    section = re.search(r"^## Verdict\b(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if section is None:
        raise SystemExit(
            "[prepare_dialog_corpus] no '## Verdict' section in the inflation report — "
            "the D-09 verdict must be recorded before any bin is built (T-11-07)."
        )
    word = re.search(r"[A-Za-z]+", section.group(1))
    verdict = word.group(0).upper() if word else "PENDING"
    if verdict not in ("GO", "ADAPT"):
        raise SystemExit(
            f"[prepare_dialog_corpus] recorded verdict is {verdict!r} — bins may only be "
            "built on GO/ADAPT (D-09). STOP/PENDING must be escalated, not bypassed."
        )
    return verdict


def _cap_persona(tok, persona):
    """D-07: keep whole persona lines in order under the 140-token span budget.

    The span cost mirrors inflation metric 2 exactly: 1 (the ``<|system|>`` token) + the ids
    of the newline-joined, detokenized persona — recomputed on the full join per candidate so
    BPE merges across line boundaries are accounted for. Dropping starts at the FIRST line
    that would push the span past the cap; no mid-line truncation.
    """
    kept = []
    for line in persona:
        candidate = kept + [line]
        cost = 1 + len(tok.encode("\n".join(detokenize(p) for p in candidate)))
        if cost > PERSONA_CAP:
            break
        kept = candidate
    return kept


def build_split(tok, name, txt_path, bin_path, mask_path):
    """Encode one split's episodes into aligned token/mask bins; return (episodes, capped)."""
    if not txt_path.exists():
        raise FileNotFoundError(
            f"Missing {txt_path}. Run `python scripts/fetch_personachat.py` first."
        )
    episodes = parse_episodes(txt_path)

    try:
        from tqdm import tqdm  # optional progress bar; only used if already importable

        it = tqdm(episodes, desc=f"encode {name}", unit="ep")
    except ImportError:
        it = episodes

    id_shards, mask_shards = [], []
    capped = 0
    for persona, turns in it:
        kept = _cap_persona(tok, persona)
        capped += kept != persona
        ids, mask = encode_dialogue(tok, kept, turns)
        id_shards.append(np.asarray(ids, dtype=np.uint16))
        mask_shards.append(np.asarray(mask, dtype=np.uint8))

    np.concatenate(id_shards).tofile(bin_path)
    np.concatenate(mask_shards).tofile(mask_path)
    return len(episodes), capped


def sanity_check(tok, name, bin_path, mask_path, n_episodes):
    """Loud post-build proofs per split: alignment, eos count, mask fraction, smoke draw."""
    ids = np.fromfile(bin_path, dtype=np.uint16)
    mask = np.fromfile(mask_path, dtype=np.uint8)

    if len(ids) != len(mask):
        raise SystemExit(
            f"[prepare_dialog_corpus] {name}: token bin has {len(ids):,} elements but mask "
            f"bin has {len(mask):,} — bins must be 1:1 aligned (T-11-04)."
        )
    eos_count = int(np.count_nonzero(ids == EOS_ID))
    if eos_count != n_episodes:
        raise SystemExit(
            f"[prepare_dialog_corpus] {name}: eos count {eos_count:,} != episode count "
            f"{n_episodes:,} — eos 8184 must appear exactly once per dialogue."
        )
    frac = float(mask.mean())
    lo, hi = MASK_FRACTION_BAND
    if not lo <= frac <= hi:
        raise SystemExit(
            f"[prepare_dialog_corpus] {name}: masked fraction {frac:.4f} outside "
            f"[{lo}, {hi}] — ~0%/~100% means the mask is wrong (Pitfall 14)."
        )
    prefix = tok.decode(ids[:200].astype(np.int64).tolist())
    print(f"  {bin_path.name}: {len(ids):,} tokens, {eos_count:,} episodes (eos)")
    print(f"  {mask_path.name}: {len(mask):,} elements, masked fraction {frac:.4f}")
    print(f"  decoded prefix: {prefix[:200]!r}")

    # End-to-end smoke: a masked batch drawn from the REAL bins carries -100 sentinels.
    x, y = get_batch_memmap_masked(bin_path, mask_path, 4, BLOCK_SIZE, "cpu")
    if tuple(x.shape) != (4, BLOCK_SIZE) or tuple(y.shape) != (4, BLOCK_SIZE):
        raise SystemExit(
            f"[prepare_dialog_corpus] {name}: smoke draw shapes {tuple(x.shape)}/"
            f"{tuple(y.shape)} != (4, {BLOCK_SIZE})."
        )
    if int(x.max()) >= 8192:
        raise SystemExit(
            f"[prepare_dialog_corpus] {name}: smoke draw x.max()={int(x.max())} >= 8192 — "
            "ids out of vocab range."
        )
    if not bool((y == -100).any()):
        raise SystemExit(
            f"[prepare_dialog_corpus] {name}: smoke draw y contains NO -100 sentinel — "
            "mask never applied (Pitfall 14)."
        )
    print(f"  smoke draw: x/y (4, {BLOCK_SIZE}), y contains -100, x.max() < 8192 — ok")


def main():
    verdict = _require_go_verdict(REPORT_PATH)
    print(f"[prepare_dialog_corpus] D-09 verdict: {verdict} — proceeding to bins")
    print(f"[prepare_dialog_corpus] frozen tokenizer: {TOKENIZER_PATH}")
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)

    for name, (txt_path, bin_path, mask_path) in SPLITS.items():
        print(f"[prepare_dialog_corpus] encoding {name}: {txt_path}")
        n_episodes, capped = build_split(tok, name, txt_path, bin_path, mask_path)
        print(
            f"[prepare_dialog_corpus] {name}: {n_episodes:,} episodes, "
            f"{capped:,} personas capped at {PERSONA_CAP} tokens (D-07)"
        )
        sanity_check(tok, name, bin_path, mask_path, n_episodes)
    print("[prepare_dialog_corpus] done — four data/dialog_* bins written (gitignored)")


if __name__ == "__main__":
    main()
