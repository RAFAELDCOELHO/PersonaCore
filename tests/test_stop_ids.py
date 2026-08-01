"""Phase-11 D-03: additive ``stop_ids`` kwarg on ``generate()`` (12-02, T-12-03).

Pins the exact replacement semantics ``stops = stop_ids if stop_ids is not None else
{eid}`` — default None is bit-identical to v1.0 single-EOS behavior; a provided set
REPLACES (does not extend) the EOS stop, so EOS is only a stop when it is a member.
Stop-without-yield (D-05) holds for every member id.

CPU-only tiny GPT fixture with forced-argmax stubs — same recipe as
``tests/test_generation.py::test_eos_stop``.
"""

import torch

from personacore.config import ModelConfig
from personacore.generation import collect
from personacore.model import GPT


def _tiny_model():
    return GPT(
        ModelConfig(
            block_size=8,
            vocab_size=16,
            n_layer=1,
            n_head=1,
            n_embd=8,
            eos_id=15,
        )
    )


def _force_argmax(model, forced_id):
    """Make ``forced_id`` the argmax at every position of every forward pass."""

    def _forward(idx, targets=None):
        logits = torch.full((idx.size(0), idx.size(1), model.config.vocab_size), -1e9)
        logits[..., forced_id] = 1e9
        return logits, None

    model.forward = _forward  # type: ignore[method-assign]


def test_default_equivalent_to_v1_eos_stop():
    # stop_ids omitted: identical asserts to test_generation.test_eos_stop — the first
    # candidate token is EOS, so nothing is yielded or appended.
    model = _tiny_model()
    _force_argmax(model, model.config.eos_id)
    prompt = torch.tensor([[1, 2, 3]])
    out = collect(model, prompt, max_new_tokens=5, greedy=True)
    assert out[0, -1].item() != model.config.eos_id
    assert out.shape[1] == prompt.shape[1]


def test_custom_stop_id_halts_without_yield():
    model = _tiny_model()
    _force_argmax(model, 7)
    prompt = torch.tensor([[1, 2, 3]])
    out = collect(model, prompt, max_new_tokens=5, greedy=True, stop_ids={7})
    assert out.shape[1] == prompt.shape[1]  # id 7 was never yielded/appended
    assert out[0, -1].item() != 7


def test_multi_id_set_stops_on_first_member():
    prompt = torch.tensor([[1, 2, 3]])
    for forced in (7, 15):  # whichever member appears first stops — EOS still stops too
        model = _tiny_model()
        _force_argmax(model, forced)
        stops = {model.config.eos_id, 7}
        out = collect(model, prompt, max_new_tokens=5, greedy=True, stop_ids=stops)
        assert out.shape[1] == prompt.shape[1]
        assert out[0, -1].item() not in stops


def test_eos_not_implicitly_included_in_custom_set():
    # stop_ids={7} REPLACES the EOS stop: with EOS forced as argmax, generation runs to
    # max_new_tokens and every new token IS the (yielded) EOS id.
    model = _tiny_model()
    eos_id = model.config.eos_id
    _force_argmax(model, eos_id)
    prompt = torch.tensor([[1, 2, 3]])
    out = collect(model, prompt, max_new_tokens=4, greedy=True, stop_ids={7})
    assert out.shape[1] == prompt.shape[1] + 4
    assert (out[0, prompt.shape[1] :] == eos_id).all()
