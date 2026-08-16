"""D-09's prefix stability and D-06's strided seeds — the draw layer, proved by running it.

CPU-only, GPU-free, no checkpoint I/O, no model load. Both proofs drive the REAL
``scripts/phase14_recall.py::draw_all`` against the ``fake_lm`` fixture; neither re-implements the
loop, and neither retypes a seed.

**Why this file exists, stated against the alternative.** D-09 lets family zero spend 9 draws while
the A1/A2/A3 attacks spend 64, on the ground that the 9-draw run is the byte-identical PREFIX of
the 64-draw run. The seed *arithmetic* behind that — ``question_seed(index) + s`` does not mention
how many draws follow — is provable by reading two lines, and a test asserting it would only be
re-typing the source. What is NOT provable by reading is that the ``draw_all`` CODE PATH honours it,
and that is exactly the gap D-09 names. The only way to close it is to run the loop at both budgets
and compare.

**What this test catches, MEASURED rather than asserted.** Four mutations were applied to
``draw_all`` and run against ``test_prefix_is_budget_independent``:

* seed becomes ``question_seed(index) + s + n_samples`` -> **RED**. Draw *s* now depends on the
  budget, which is the defect in its purest form.
* ``for s in reversed(range(n_samples))`` -> **RED**. Draw ORDER becomes budget-relative.
* the generator hoisted above the loop and seeded once -> **GREEN**. One shared stream is still
  consumed in draw order, so the first 9 draws read the same prefix of it at either budget. Worth
  recording: this is the mutation 18-02-PLAN proposed, and it does not falsify the claim.
* ``SAMPLE_TEMPERATURE`` 0.8 -> 1.7 -> **GREEN**. Both compared runs shift together.

So this test pins **budget-independence**, not the absolute stream: a change that moves both runs
equally is invisible to it by construction, and D-01's "identical stream" requirement is a
*different* claim needing a different guard. The two RED rows are the ones D-09 actually asked
for — they are precisely the edits that would make family zero stop being a prefix of the attacks
while leaving the seed arithmetic in the source looking correct.

``test_strided_seeds_are_disjoint`` is the other half: D-06 replaces family zero's ``SEED + index``
with ``SEED + index*K`` for the attacks, and the collapse it removes is a MEASURED quantity — 216
questions x 64 draws land on 279 distinct seeds unstrided, and on all 13,824 strided.
"""

import importlib.util
import pathlib
import sys

import torch

from personacore.dialogue import build_recall_prompt
from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recall = _load("phase14_recall")
extraction = _load("phase18_extraction")

# Imported, never retyped: K=64 and the 9-draw family-zero budget are pre-registered in
# `scripts/phase18_extraction.py` (D-09/D-06), and `SEED` lives in the recall driver. A test that
# re-typed any of them would keep passing after the constant it is guarding moved.
K = extraction.K
FAMILY_ZERO_DRAWS = extraction.FAMILY_ZERO_DRAWS

# D-02's attack corpus: A1/A2/A3 transform all 216 core questions. Written as the split so the
# provenance of the total is visible rather than asserted.
N_SOURCE_QUESTIONS = 112 + 104

_TOKENIZER = from_json(_REPO_ROOT / "artifacts" / "tokenizer.json")


class _IdDecoder:
    """A decoder whose output is INJECTIVE on the id sequence it is handed.

    ``draw_all`` uses its ``tok`` argument for exactly one thing — ``tok.decode(gen_ids)`` — so the
    prefix comparison is only as strong as that decode is faithful. The real BPE decoder is *lossy*
    for this purpose in two ways: distinct id sequences can render to the same string, which would
    let a genuine divergence compare equal, and it raises ``UnicodeDecodeError`` on byte sequences
    that are not valid UTF-8, which a hash-driven fake model produces constantly. Joining the ids
    is both total and injective, so a single differing token anywhere in a completion fails the
    assertion. The real tokenizer is still used for the PROMPT and the forbid mask below, where
    faithfulness is what matters.
    """

    def decode(self, ids):
        return " ".join(str(i) for i in ids)


def _draw_inputs(model):
    """``(tok, prompt_ids, forbid)`` — a real recall prompt and the real dead-id mask.

    The mask is the production one (``undecodable_ids_mask``): 547 of 8192 ids decodable, both
    ``STOP_IDS`` members among them, so the stop-without-yield path is genuinely reachable here and
    a draw that terminates early is compared as such.
    """
    from personacore.generation import undecodable_ids_mask

    forbid = undecodable_ids_mask(_TOKENIZER, model.config.vocab_size)
    prompt_ids = build_recall_prompt(_TOKENIZER, "What is my name?")
    return _IdDecoder(), prompt_ids, forbid


def test_prefix_is_budget_independent(fake_lm):
    """D-09: the first 9 draws at the K=64 budget are the 9 draws family zero actually spends."""
    tok, prompt_ids, forbid = _draw_inputs(fake_lm)

    # The fixture's own premise first: a model that answered differently on the second call would
    # make every comparison below meaningless, and would do it by looking like a draw-loop defect.
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    first, first_loss = fake_lm(idx)
    second, _ = fake_lm(idx)
    assert torch.equal(first, second)
    assert first_loss is None
    assert first.shape == (1, len(prompt_ids), fake_lm.config.vocab_size)

    for index in (0, 7):
        long_completions, long_stopped = recall.draw_all(
            fake_lm, tok, prompt_ids, "cpu", forbid, index, n_samples=K - 1
        )
        short_completions, short_stopped = recall.draw_all(
            fake_lm, tok, prompt_ids, "cpu", forbid, index, n_samples=FAMILY_ZERO_DRAWS - 1
        )

        # Both budgets are what they claim to be — 1 greedy + n seeded. Without this a fixture that
        # short-circuited to an empty list would satisfy the prefix equality vacuously.
        assert len(long_completions) == K
        assert len(long_stopped) == K
        assert len(short_completions) == FAMILY_ZERO_DRAWS
        assert len(short_stopped) == FAMILY_ZERO_DRAWS

        # ...and the draws actually differ from one another, so "equal prefixes" is a fact about
        # the seeding rather than about a degenerate model that emits one completion forever.
        assert len(set(long_completions)) == K

        assert long_completions[:FAMILY_ZERO_DRAWS] == short_completions
        assert long_stopped[:FAMILY_ZERO_DRAWS] == short_stopped


def test_strided_seeds_are_disjoint(fake_lm):
    """D-06: ``SEED + index*K + s`` gives every draw slot its own seed; the unstrided form does not.

    ``fake_lm`` is requested but unused — the seed sets are pure arithmetic over the real
    ``question_seed``. It is taken so this test and its neighbour name the same fixture, which is
    what keeps a future edit from quietly making one of them depend on a model and the other not.
    """
    assert fake_lm is not None

    # The stride is the CALLER's arithmetic: an attack passes `src_index * K` as draw_all's
    # positional `index`, so `question_seed` itself is untouched. Read through the real function.
    strided = {
        recall.question_seed(src * K) + s for src in range(N_SOURCE_QUESTIONS) for s in range(K)
    }
    assert len(strided) == N_SOURCE_QUESTIONS * K == 13824

    unstrided = {
        recall.question_seed(src) + s for src in range(N_SOURCE_QUESTIONS) for s in range(K)
    }
    # 279, the measured collapse D-06 names: the union of 216 length-64 windows each offset by one
    # is a single contiguous run, so 13,824 draw slots share 279 seeds — 98% of the randomness the
    # question-level cluster bootstrap assumes is independent is not.
    assert len(unstrided) == 279
    assert len(unstrided) == N_SOURCE_QUESTIONS + K - 1

    for src in (0, 1, 2, 111):
        assert recall.question_seed(src * K) == recall.SEED + src * K
