"""Committed-fixture data path (D-06 / TRAIN-03): encode -> uint16 -> doc-level split -> get_batch.

Bounded fixture ONLY — the full-corpus uint16 memmap + TinyStories fetch is Phase 5 (PRE-01).
The split happens at DOCUMENT boundaries (the eos id 8184), never mid-story, which gives a
provable no-leakage train/val guarantee (TRAIN-03 / Pitfall 3): no sentence straddles the cut,
so the bigram cannot "memorize" val through a leaked prefix. ``get_batch`` is the nanoGPT idiom:
random contiguous ``block_size`` windows with the next-token target shifted by one, every index
strictly in-bounds (Pitfall 3 — bound the start to ``len(arr) - block_size - 1``).

The frozen tokenizer (``artifacts/tokenizer.json``) is LOADED, never retrained (Pitfall 6).
Storage stays ``uint16`` (compact); indices are cast to ``int64`` only at batch time for
``nn.Embedding`` / ``cross_entropy``.
"""

import numpy as np
import torch

from personacore.tokenizer import from_json

TOKENIZER_PATH = "artifacts/tokenizer.json"


def load_split(fixture_path, eos_id=8184, val_docs=1):
    """Encode the fixture and split it at document boundaries into disjoint train/val arrays.

    Loads the FROZEN tokenizer (never ``.train()`` — Pitfall 6), encodes the fixture so the
    ``<|endoftext|>`` marker maps atomically to ``eos_id`` (8184), then partitions the token
    stream into per-document lists on that boundary (eos kept as each doc's terminator). The
    last ``val_docs`` whole documents go to val, the rest to train — no document straddles the
    cut (no leakage, Pitfall 3). Returns two ``np.uint16`` arrays.
    """
    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
    with open(fixture_path, encoding="utf-8") as fh:
        text = fh.read()
    ids = tok.encode(text, allowed_special="all")  # <|endoftext|> -> atomic eos_id (8184)

    docs, cur = [], []
    for t in ids:
        cur.append(t)
        if t == eos_id:
            docs.append(cur)
            cur = []
    # A trailing fragment with no closing eos is a real document only if it carries content.
    # A whitespace-only tail (e.g. the file's final "\n" after the last <|endoftext|>) is NOT a
    # document — promoting it would make val a degenerate single-newline run that "leaks" into
    # train everywhere (Pitfall 3 / no-leakage contract). Drop it; keep a content-bearing tail.
    if cur and tok.decode(cur).strip():
        docs.append(cur)

    assert len(docs) >= 2, "fixture must contain >= 2 documents (D-06)"
    assert 1 <= val_docs < len(docs), "val_docs reserves >=1 doc, train stays non-empty"

    train_ids = np.array([t for d in docs[:-val_docs] for t in d], dtype=np.uint16)
    val_ids = np.array([t for d in docs[-val_docs:] for t in d], dtype=np.uint16)
    return train_ids, val_ids


def get_batch(arr, batch_size, block_size, device):
    """Draw ``batch_size`` random contiguous ``(x, y)`` windows from ``arr`` (nanoGPT idiom).

    Start indices are bounded to ``len(arr) - block_size - 1`` so neither ``x`` nor the +1
    shifted ``y`` ever overruns the array (Pitfall 3). Windows are cast ``uint16`` -> ``int64``
    for ``nn.Embedding`` / ``cross_entropy`` and moved to ``device``.
    """
    ix = np.random.randint(0, len(arr) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(arr[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(arr[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)


def get_batch_memmap(bin_path, batch_size, block_size, device):
    """Draw ``batch_size`` random ``(x, y)`` windows from a flat ``uint16`` ``.bin`` memmap.

    The full-corpus analog of :func:`get_batch` (PRE-01): identical nanoGPT indexing — the same
    ``len(data) - block_size - 1`` start bound (Pitfall 3, no overrun), the same ``uint16`` ->
    ``int64`` cast at draw time, the same ``.to(device)``. The ONLY difference is the in-RAM
    ``arr`` is replaced by a ``np.memmap`` that is **re-opened every call**: a long-lived memmap
    accumulates RSS across thousands of training steps (nanoGPT leak — Pitfall 1), so it is opened
    fresh and discarded per batch. Plain ``.to(device)`` only — the CUDA-only pinned-host /
    async-copy transfer flags have no MPS/CPU path this phase, so they are deliberately absent.
    """
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    return x.to(device), y.to(device)


def get_batch_memmap_masked(bin_path, mask_path, batch_size, block_size, device):
    """Draw masked ``(x, y)`` windows from aligned token (uint16) and mask (uint8) ``.bin`` files.

    The dialogue analog of :func:`get_batch_memmap` (DATA-03 / D-03): identical nanoGPT
    indexing — the same ``len(data) - block_size - 1`` start bound, the same ``uint16`` ->
    ``int64`` cast, the same plain ``.to(device)`` — and BOTH memmaps are **re-opened every
    call** (a long-lived memmap accumulates RSS across thousands of training steps, the
    nanoGPT leak — Pitfall 1). The token/mask bins must be element-aligned; a length
    mismatch raises loudly (T-11-04) rather than skewing labels silently.

    The +1 label shift is applied to token AND mask slices IDENTICALLY — ``y`` and ``m``
    share the ``i + 1 : i + 1 + block_size`` slice, so token j's mask governs the
    prediction OF token j (target-space semantics, D-01). Wherever the shifted mask is 0,
    ``y`` is set to ``-100`` — ``F.cross_entropy``'s default ``ignore_index`` — so loss
    masking lives entirely in the data path and the LOCKED ``forward(idx, targets=None)``
    contract needs zero changes.
    """
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    mask = np.memmap(mask_path, dtype=np.uint8, mode="r")
    if len(data) != len(mask):
        raise ValueError(
            f"token/mask bin length mismatch: {bin_path} has {len(data)} elements but "
            f"{mask_path} has {len(mask)} — bins must be element-aligned (T-11-04)"
        )
    ix = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    m = torch.stack(
        [torch.from_numpy(mask[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    y[m == 0] = -100
    return x.to(device), y.to(device)


def fact_window_impurities(fact_ids, block_size, *, space="input"):
    """Indices of every ``block_size``-aligned window carrying MORE THAN ONE distinct fact id.

    The ONE purity predicate for the fact-aligned path (D-05): ``build_bins``' build-time
    proof 7, the loader's run-time check and the tests all drive THIS implementation, so
    there is no second copy to drift. Pure numpy — no I/O, no torch. Callers pass ids they
    read BACK FROM DISK (``np.fromfile``), never the packer's own arithmetic: a packing bug
    that writes correct offsets over wrong bytes passes an offset check and must fail this one.

    **Length contract.** The aligned bins carry ``n_windows * block_size + 1`` elements. The
    trailing ``+1`` is the LABEL-SHIFT TAIL — one pad slot so that every window's target slice
    ``[k*B+1 : (k+1)*B+1]`` is in range for all ``k``, which is what makes the target-space
    claim assertable DIRECTLY over all ``n`` windows instead of inferred from three premises.
    A length whose ``(len - 1) % block_size`` is non-zero therefore raises HERE, before the
    purity loop, and the message names the remainder so a truncate-by-1 adversary is
    distinguishable from an impurity finding.

    **``space`` takes exactly two values and defaults to ``"input"``.** There is no union mode,
    and adding one would be a denial of service rather than a stricter check: on a CORRECTLY
    built bin target space is never empty (see below), so a union default would make
    ``build_bins``' proof 7 abort every aligned build.

    * ``"input"`` — ``fact_ids[:-1].reshape(-1, block_size)``. This is D-05/SC2's claim
      verbatim: *no ``block_size``-aligned window contains token ids from two fact shards* is a
      statement about the WINDOW. Proof 7(a)'s ``== []`` assertion and the loader's run-time
      check both use it.
    * ``"target"`` — ``fact_ids[1:].reshape(-1, block_size)``. MEASURED, and it is why the
      default is a correction rather than a preference: window ``k``'s target slice is
      ``fact_ids[k*block_size + 1 : (k+1)*block_size + 1]``, whose LAST element is index
      ``(k+1)*block_size`` — the FIRST token of window ``k+1``. When window ``k`` is a fact's
      last window that element belongs to the NEXT fact, so on a correct bin target space
      returns EXACTLY ``n_facts - 1`` rows, never ``[]``.

    That target-space count is a POSITIVE property of a correct bin, not a defect to be
    waived, and it is the claim that actually supports *one micro-step is one privacy record*:
    each boundary token is the next fact's ``<|system|>`` token, which carries mask 0
    (``src/personacore/dialogue/serialize.py:81``, ``emit([system_id], 0)``), so
    ``y[m == 0] = -100`` above sets it to ``F.cross_entropy``'s ``ignore_index`` and it
    contributes NOTHING to the record's loss. The label shift therefore never leaks one fact's
    gradient into another record's micro-step.

    **DERIVED CONSTRAINT on the packer — a consequence, not a decision.** Padding slots inside
    a fact's final window MUST carry that fact's OWN id. A reserved sentinel would put two
    distinct ids in every fact's last window in INPUT space, making this guard permanently
    unsatisfiable with a long debugging path, and sentinel ``0`` additionally collides with
    fact index 0 in a ``uint16`` map. The padding is masked to 0 anyway, so the id it carries
    is purely an accounting label.

    Returns:
        ``list[int]`` — impure window indices, in ascending order. Empty is the PASS condition
        for ``space="input"`` only.
    """
    if space not in ("input", "target"):
        raise ValueError(
            f"fact_window_impurities: space={space!r} is not a supported space — pass "
            "'input' (the default, D-05/SC2's window claim) or 'target' (the +1 label-shift "
            "reading). There is deliberately no union mode: it would refuse every correctly "
            "built bin."
        )
    fact_ids = np.asarray(fact_ids)
    remainder = (len(fact_ids) - 1) % block_size
    if remainder != 0:
        raise ValueError(
            f"fact bin length {len(fact_ids)} is not n_windows * block_size + 1 for "
            f"block_size={block_size}: (len - 1) % block_size == {remainder}, expected 0. "
            "The trailing +1 is the LABEL-SHIFT TAIL, one pad slot so every window's target "
            "slice is in range — a bin off by this remainder is truncated or mis-packed, "
            "which is a LENGTH failure and not a window-content finding."
        )
    rows = (fact_ids[:-1] if space == "input" else fact_ids[1:]).reshape(-1, block_size)
    return [k for k in range(rows.shape[0]) if np.unique(rows[k]).size != 1]


def fact_window_span(fact_ids, fact_index, block_size):
    """The contiguous run of ``block_size``-aligned windows that fact ``fact_index`` OWNS.

    Returns ``(start_element, n_windows)`` — the element offset of the fact's FIRST window and
    how many windows it spans (4 or 5 under D-01's RAGGED geometry). Pure numpy: no I/O, no
    torch, no ``device``.

    **EXPORTED on purpose, and the docstring says why because the reason is a design
    constraint, not a convenience.** Plan 21-10's ``count_aligned`` needs exactly this window
    range in order to observe ``per_step_distinct_facts``; a second copy of the arithmetic
    would be a second implementation, free to drift from the one the loader actually draws
    through, so the counter would end up measuring a different draw than the one served. One
    function, two callers.

    Window owners are read from the FACT BIN'S CONTENTS — ``fact_ids[k * block_size]`` for each
    window ``k`` — never from a ``cumsum`` of the padded lengths. That distinction is the whole
    of D-06: a cumsum reconstruction reproduces the packer's own arithmetic and therefore shares
    any packing defect, and it makes run-time consumption of the map UNOBSERVABLE — a loader
    that never reads the bytes cannot be caught reading the wrong ones.

    Raises ``ValueError`` if the fact owns no window (its privacy record exists in the
    accounting and nowhere in the bin) or if its windows are not contiguous (a fact split
    across shards is a packing defect, not a draw to serve).

    The ``n_windows * block_size + 1`` LENGTH contract is deliberately not re-checked here: it
    lives in :func:`fact_window_impurities`, the one purity predicate, and the three-bin length
    equality lives in :func:`get_batch_fact_aligned`. The owners are read with a STRIDED slice
    rather than a reshape precisely so this function carries no second copy of that guard.
    """
    fact_ids = np.asarray(fact_ids)
    n_windows = (len(fact_ids) - 1) // block_size
    owners = fact_ids[: n_windows * block_size : block_size]
    rows = np.flatnonzero(owners == fact_index)
    if rows.size == 0:
        raise ValueError(
            f"fact {fact_index} owns no block_size-aligned window in a fact map of "
            f"{n_windows} window(s) carrying ids {np.unique(owners).tolist()} — that fact's "
            "privacy record exists in the accounting and nowhere in the bin, so "
            "grad_accum_steps = n_facts would count a record the loop never draws."
        )
    if int(rows[-1] - rows[0]) + 1 != int(rows.size):
        gaps = [int(rows[j]) for j in range(1, rows.size) if rows[j] - rows[j - 1] != 1]
        raise ValueError(
            f"fact {fact_index} owns NON-CONTIGUOUS windows {rows.tolist()} — the run breaks "
            f"before window(s) {gaps}. A fact split across shards is a packing defect, not a "
            "draw to serve: its micro-step would not be one privacy record."
        )
    return int(rows[0]) * block_size, int(rows.size)


def get_batch_fact_aligned(bin_path, mask_path, fact_path, block_size, device, *, step, n_facts):
    """Draw EVERY window of ONE fact — one micro-step, one privacy record (D-01 / D-05 / D-06).

    The fact-aligned SIBLING of :func:`get_batch_memmap_masked`, not a replacement: that
    function is byte-unchanged and stays the replay draw's path (D-10). Returns
    ``(x, y, fact_index)``.

    **Deterministic, not random — ``q = 1``, no subsampling.** The record for this micro-step is
    ``step % n_facts``, and the batch is EVERY window that fact owns, in bin order. Under D-01's
    ragged geometry that is 4 or 5 windows, so the batch size VARIES by record. That is not a
    defect to smooth over: it is exactly what makes one micro-step one privacy record, and D-02
    measured the ragged accumulation at 1.14x the batched reference against 1.39x for
    uniform-W, so the cheap path is also the honest one. ``torch.stack`` refuses a ragged vmap
    batch outright, which is why vmap leaves the critical path entirely (D-02): with one record
    per micro-step the ordinary backward hands back the per-record gradient directly.

    **All THREE memmaps are re-opened on EVERY call**, for two independent reasons that are
    recorded here because either one alone would justify it:

    1. A long-lived memmap accumulates RSS across thousands of training steps — the nanoGPT
       leak (Pitfall 1), the same reason documented at :func:`get_batch_memmap_masked`.
    2. D-06: the fact map is CONSUMED AT RUN TIME, not merely asserted once at build time. A
       cached handle (or boundaries reconstructed from a stored ``cumsum``) would make "one
       window, one fact" a claim about a PAST construction, and would make the
       mutate-between-calls proof in ``tests/test_phase21_aligned_loader.py`` impossible to
       write — which is the same thing as making the property impossible to check.

    **The draw-time purity check is INPUT space, and widening it to target space would raise on
    every fact but the last, on a PERFECTLY built bin.** Window ``k``'s target slice ends at
    ``fact_ids[(k + 1) * block_size]`` — the FIRST token of window ``k + 1`` — which for a
    fact's last window belongs to the NEXT fact. The property is nonetheless sound: that
    boundary token is the next fact's ``<|system|>`` token, which carries mask 0
    (``src/personacore/dialogue/serialize.py:81``, ``emit([system_id], 0)``), so ``y[m == 0] =
    -100`` below sets it to ``F.cross_entropy``'s ``ignore_index`` and it contributes NOTHING to
    this record's loss. The counted, POSITIVE form of that claim — exactly ``n_facts - 1``
    boundary rows, each masked, each in fact order — is a whole-bin invariant asserted once at
    build time by ``teach_persona._build_aligned_bins``' proof 7(b); it belongs there, not in a
    per-draw check. Only the ``k`` windows being handed back are checked here, so the per-call
    cost is O(batch) rather than O(corpus).

    The slice passed to :func:`fact_window_impurities` carries a trailing ``+1``, and that is
    REQUIRED rather than incidental: the predicate raises on
    ``(len - 1) % block_size != 0`` (the LABEL-SHIFT TAIL contract), so a bare
    ``k * block_size`` slice would raise SPURIOUSLY on every valid draw —
    ``(1024 - 1) % 256 == 255``. Relaxing that remainder assertion to make a short slice fit
    would silently kill the truncation adversary for the packer and the tests as well as for
    the loader.

    **D-03/D-04 are VERIFIED here, not implemented.** Within one fact the loss is a MEAN over
    its windows, and it costs ZERO new loss code: ``y[m == 0] = -100`` below plus
    ``F.cross_entropy``'s default ``reduction="mean"`` (``src/personacore/model/gpt.py:212``)
    averages over NON-IGNORED targets only, and with one fact per micro-step that IS
    mean-over-the-record. The accepted cost, named rather than glossed: a 5-window fact's
    windows count 1/5 each where a 4-window fact's count 1/4 — which weights by PRIVACY RECORD
    rather than by how text happens to pack into ``block_size``.

    ``fact_index`` is returned because the guarantee has to be observable from OUTSIDE the
    loader: it is the run-time attribution the D-06 proof reads, and it is what makes
    ``grad_accum_steps = n_facts`` an OBSERVED property of the micro-step sequence instead of a
    number declared from a bin's shape.

    Every failure raises ``ValueError`` in the ``:112-116`` register — name every path and every
    length — and each class carries a DISTINGUISHABLE message so a red is identified by which
    guard fired, not by "an exception occurred".
    """
    data = np.memmap(bin_path, dtype=np.uint16, mode="r")
    mask = np.memmap(mask_path, dtype=np.uint8, mode="r")
    try:
        facts = np.memmap(fact_path, dtype=np.uint16, mode="r")
    except (FileNotFoundError, ValueError) as exc:
        # Do NOT let np.memmap's own FileNotFoundError carry the message: with three bins in
        # play the caller needs to know WHICH one is absent.
        raise ValueError(
            f"the fact bin {fact_path} could not be opened ({exc}) — a fact-aligned draw "
            f"cannot proceed without it (token bin {bin_path}, mask bin {mask_path} were "
            "opened). Falling back to positionally-guessed boundaries would make "
            "grad_accum_steps = n_facts a declaration instead of a property of the data (D-06)."
        ) from exc

    if not len(data) == len(mask) == len(facts):
        raise ValueError(
            f"the three aligned bins are not 1:1: {bin_path} has {len(data)} elements, "
            f"{mask_path} has {len(mask)} and the fact bin {fact_path} has {len(facts)} — all "
            "three must match element for element (T-11-04 extended from two files to three, "
            "D-06 proof 1). A length skew silently mis-attributes windows to records."
        )

    n_windows = (len(facts) - 1) // block_size
    observed = np.unique(facts[: n_windows * block_size : block_size])
    if observed.size != n_facts:
        raise ValueError(
            f"the fact bin {fact_path} carries {observed.size} distinct fact id(s) "
            f"{observed.tolist()} across {n_windows} window(s), but n_facts={n_facts} was "
            "declared. Content purity alone does not pin n_facts, so the loader asserts both — "
            "otherwise grad_accum_steps = n_facts would bound a lot the bin does not contain."
        )

    fact_index = step % n_facts
    start, k = fact_window_span(facts, fact_index, block_size)

    # INPUT space, the DEFAULT, on the drawn slice only. The trailing +1 is the label-shift tail.
    impure = fact_window_impurities(facts[start : start + k * block_size + 1], block_size)
    if impure:

        def _row_ids(row):
            at = start + row * block_size
            return np.unique(facts[at : at + block_size]).tolist()

        detail = "; ".join(
            f"window {start // block_size + row} carries ids {_row_ids(row)}" for row in impure
        )
        raise ValueError(
            f"the fact bin {fact_path} is IMPURE on the draw for fact {fact_index}: {detail} — "
            f"every one of that fact's {k} window(s) must carry only id {fact_index}. SC2's "
            "'one window, one fact' is FALSE for this draw, so this micro-step is not one "
            "privacy record."
        )

    ix = range(start, start + k * block_size, block_size)
    x = torch.stack([torch.from_numpy(data[i : i + block_size].astype(np.int64)) for i in ix])
    y = torch.stack(
        [torch.from_numpy(data[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    m = torch.stack(
        [torch.from_numpy(mask[i + 1 : i + 1 + block_size].astype(np.int64)) for i in ix]
    )
    y[m == 0] = -100
    return x.to(device), y.to(device), fact_index
