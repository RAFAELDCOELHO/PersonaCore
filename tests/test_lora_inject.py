"""LoRA injection pins (LORA-01 / LORA-05): allowlist, ordering, tied tensor, param census.

Pins the post-load injection machinery on a tiny CPU fixture:

  1. Wrap count — ``inject_lora`` wraps exactly ``6 * n_layer`` projections and nothing else.
  2. Allowlist cross-pin — ``TARGET_PROJECTIONS`` equals the seam test's ``PROJECTIONS``
     tuple (``tests/test_gpt_lora_seam.py:16``); production code never imports from tests/.
  3. Tied-tensor safety (LORA-05) — post-injection ``lm_head.weight`` still IS ``wte.weight``
     (``data_ptr`` identity) and neither head nor embedding is a ``LoRALinear`` (PITFALLS P1).
  4. Load->inject ordering — injection after weights exist leaves logits BIT-identical
     (B=0 + loaded base => identity).
  5. Param-count closed form (LORA-05) — trainable census == r * n_layer * 18 * n_embd
     after ``mark_only_lora_trainable``; only ``lora_`` params are trainable.
  6. ``lora_state_dict`` filter — exactly 2 * 6 * n_layer tensors, no base weights leak.
  7. Key-audited apply — ``load_adapter_weights`` reproduces logits across identically
     injected models; a corrupted dict raises ``ValueError`` BEFORE any weight loads (P4).
  8. ``snapshot_params`` — detached clones immune to later in-place mutation (the canary).
  9. ISO-06 — every ``inject_lora`` CONSUMER call site in the repo injects at the artifact's
     own ``lora_config``, not at ``LoRAConfig()`` defaults (static AST scan, bottom of file).

CPU-only, GPU-free.
"""

import ast
import pathlib

import pytest
import torch
import torch.nn as nn

from personacore.config import ModelConfig
from personacore.lora import (
    TARGET_PROJECTIONS,
    LoRAConfig,
    LoRALinear,
    inject_lora,
    load_adapter_weights,
    lora_state_dict,
    mark_only_lora_trainable,
    snapshot_params,
)
from personacore.model import GPT

# Canonical allowlist restated from tests/test_gpt_lora_seam.py::PROJECTIONS (line 16) — the
# cross-pin target. Tests may restate the literal; production code never imports from tests/.
PROJECTIONS = ("q_proj", "k_proj", "v_proj", "c_proj", "fc_in", "fc_out")


def _tiny_config() -> ModelConfig:
    # vocab_size/eos_id stay at the LOCKED defaults (8192/8184); everything else is shrunk
    # for a cheap CPU fixture (tests/test_slim_checkpoint.py precedent).
    return ModelConfig(block_size=32, n_layer=1, n_head=2, n_embd=16)


def _build_injected(r: int = 4):
    """Seeded tiny GPT with LoRA injected — the load->inject->freeze substrate."""
    torch.manual_seed(1234)
    cfg = _tiny_config()
    model = GPT(cfg)
    lora_cfg = LoRAConfig(r=r)
    n = inject_lora(model, lora_cfg)
    return model, cfg, lora_cfg, n


def _nudge_lora_b(model, seed: int) -> None:
    """Make the adapter delta nonzero/distinctive so applies are observable."""
    torch.manual_seed(seed)
    with torch.no_grad():
        for name, p in model.named_parameters():
            if "lora_B" in name:
                nn.init.normal_(p)


def test_wrap_count_and_targets():
    model, cfg, _, n = _build_injected()
    assert n == 6 * cfg.n_layer
    for block in model.blocks:
        for name in ("q_proj", "k_proj", "v_proj", "c_proj"):
            assert isinstance(getattr(block.attn, name), LoRALinear)
        for name in ("fc_in", "fc_out"):
            assert isinstance(getattr(block.mlp, name), LoRALinear)


def test_allowlist_cross_pin():
    # TARGET_PROJECTIONS must equal the structural seam gate's tuple — one canonical allowlist.
    assert TARGET_PROJECTIONS == PROJECTIONS


def test_tied_tensor_never_wrapped():
    model, _, _, _ = _build_injected()
    # data_ptr identity reused verbatim from tests/test_gpt_weight_tying.py (LORA-05).
    assert model.lm_head.weight.data_ptr() == model.wte.weight.data_ptr()
    assert not isinstance(model.lm_head, LoRALinear)
    assert not isinstance(model.wte, LoRALinear)


def test_injection_preserves_logits_bit_identical():
    torch.manual_seed(1234)
    cfg = _tiny_config()
    model = GPT(cfg).eval()
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        before, _ = model(idx)
    inject_lora(model, LoRAConfig(r=4))
    model.eval()  # fresh LoRALinear children default to train mode.
    with torch.no_grad():
        after, _ = model(idx)
    # B=0 + loaded base => bit-identity (the load->inject ordering pin).
    assert torch.equal(before, after)


def test_trainable_census_formula():
    model, cfg, lora_cfg, _ = _build_injected()
    mark_only_lora_trainable(model)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Closed form verified in 09-RESEARCH.md: r * n_layer * 18 * n_embd (LORA-05).
    assert trainable == lora_cfg.r * cfg.n_layer * 18 * cfg.n_embd
    for name, p in model.named_parameters():
        if p.requires_grad:
            assert "lora_" in name, f"non-LoRA param is trainable: {name}"
        else:
            assert "lora_" not in name, f"LoRA param is frozen: {name}"


def test_lora_state_dict_filter():
    model, cfg, _, _ = _build_injected()
    adapter = lora_state_dict(model)
    assert all("lora_" in k for k in adapter)
    assert len(adapter) == 2 * 6 * cfg.n_layer  # one A + one B per wrapped projection.
    # Base weights never leak into the persona file.
    assert not any(".base." in k for k in adapter)


def test_load_adapter_weights_applies_bit_identical():
    model_a, cfg, _, _ = _build_injected()
    model_b, _, _, _ = _build_injected()  # identically seeded -> identical base + lora_A.
    _nudge_lora_b(model_a, seed=7)
    load_adapter_weights(model_b, {"adapter": lora_state_dict(model_a)})
    model_a.eval()
    model_b.eval()
    idx = torch.randint(0, cfg.vocab_size, (2, 12))
    with torch.no_grad():
        logits_a, _ = model_a(idx)
        logits_b, _ = model_b(idx)
    assert torch.equal(logits_a, logits_b)


def test_load_adapter_weights_raises_before_loading():
    model_a, _, _, _ = _build_injected()
    model_b, _, _, _ = _build_injected()
    _nudge_lora_b(model_a, seed=11)  # adapter values differ from model_b's zeros.
    adapter = lora_state_dict(model_a)
    before = {k: v.clone() for k, v in lora_state_dict(model_b).items()}

    # One key removed -> ValueError (PITFALLS P4: no bare strict=False).
    missing_one = dict(adapter)
    del missing_one[sorted(missing_one)[0]]
    with pytest.raises(ValueError):
        load_adapter_weights(model_b, {"adapter": missing_one})

    # One key renamed -> ValueError.
    renamed_one = dict(adapter)
    renamed_one["blocks.0.attn.q_proj.lora_Z"] = renamed_one.pop(sorted(renamed_one)[0])
    with pytest.raises(ValueError):
        load_adapter_weights(model_b, {"adapter": renamed_one})

    # Correct key set, ONE wrong-shaped tensor -> ValueError BEFORE any tensor copies
    # (CR-02: load_state_dict(strict=False) copies shape-matching tensors first, so a bare
    # strict=False call would half-apply the crafted artifact before raising).
    k0 = sorted(adapter)[0]
    wrong_shape = dict(adapter)
    wrong_shape[k0] = torch.zeros(adapter[k0].shape[0] + 1, adapter[k0].shape[1])
    with pytest.raises(ValueError, match="shape/dtype"):
        load_adapter_weights(model_b, {"adapter": wrong_shape})

    # Correct key set + shapes, ONE wrong-dtype tensor -> same friendly refusal.
    wrong_dtype = dict(adapter)
    wrong_dtype[k0] = adapter[k0].double()
    with pytest.raises(ValueError, match="shape/dtype"):
        load_adapter_weights(model_b, {"adapter": wrong_dtype})

    # The audit fires BEFORE any weight is loaded: model_b's lora tensors are unchanged.
    after = lora_state_dict(model_b)
    for k, v in before.items():
        assert torch.equal(v, after[k]), f"failed audit mutated {k}"


def test_load_adapter_weights_refuses_wrong_rank():
    """CR-02 secondary: an r=8 artifact onto an r=4 injection has IDENTICAL key names but
    different shapes — the audit must raise the friendly ValueError (not torch's opaque
    aggregated size-mismatch RuntimeError) and leave the victim bit-unchanged."""
    model_r4, _, _, _ = _build_injected(r=4)
    model_r8, _, _, _ = _build_injected(r=8)
    _nudge_lora_b(model_r8, seed=13)
    before = {k: v.clone() for k, v in lora_state_dict(model_r4).items()}
    with pytest.raises(ValueError, match="shape/dtype"):
        load_adapter_weights(model_r4, {"adapter": lora_state_dict(model_r8)})
    after = lora_state_dict(model_r4)
    for k, v in before.items():
        assert torch.equal(v, after[k]), f"wrong-rank refusal mutated {k}"


def test_load_adapter_weights_refuses_wrong_alpha():
    """W1 (v2.0-MILESTONE-AUDIT.md:45): `alpha` is invisible to the key and shape audits.

    An artifact taught at alpha=32 and injected under alpha=16 has an IDENTICAL key set and
    IDENTICAL tensor shapes — only `LoRALinear.scale = alpha / r` differs, so before this audit
    the delta was applied at the wrong magnitude with no error at all. Shipped consumers were
    benign only because the committed adapter's config happened to equal `LoRAConfig()`; a
    Phase-17 adapter taught at another alpha would not be.
    """
    model, _, lora_cfg, _ = _build_injected(r=4)  # scale = 16.0 / 4 = 4.0.
    donor, _, _, _ = _build_injected(r=4)
    _nudge_lora_b(donor, seed=17)
    adapter = lora_state_dict(donor)
    before = {k: v.clone() for k, v in lora_state_dict(model).items()}

    drifted = {"r": lora_cfg.r, "alpha": 32.0, "dropout": 0.0, "targets": PROJECTIONS}
    with pytest.raises(ValueError, match="scale mismatch"):
        load_adapter_weights(model, {"adapter": adapter, "lora_config": drifted})

    # The refusal precedes the load, like the key and shape audits beside it.
    after = lora_state_dict(model)
    for k, v in before.items():
        assert torch.equal(v, after[k]), f"scale refusal mutated {k}"

    # Positive control: the artifact's OWN config loads. Without it this test would also pass
    # against an audit that rejected every artifact.
    honest = {"r": lora_cfg.r, "alpha": lora_cfg.alpha, "dropout": 0.0, "targets": PROJECTIONS}
    load_adapter_weights(model, {"adapter": adapter, "lora_config": honest})
    k0 = sorted(adapter)[0]
    assert torch.equal(lora_state_dict(model)[k0], adapter[k0])


def test_snapshot_params_detached_clones():
    model, _, _, _ = _build_injected()
    snap = snapshot_params(model)
    assert set(snap.keys()) == {n for n, _ in model.named_parameters()}
    name, param = next(iter(model.named_parameters()))
    original = param.detach().clone()
    assert snap[name].requires_grad is False  # detached clone, not a live view.
    with torch.no_grad():
        param.add_(1.0)
    assert torch.equal(snap[name], original)  # snapshot immune to the mutation.
    assert not torch.equal(snap[name], param)


# ===== ISO-06: the regression half of the W1 fix (quick task 260814-d0j) =====
#
# `src/personacore/lora/inject.py` already RAISES on a scale mismatch at load time, and
# `test_load_adapter_weights_refuses_wrong_alpha` above pins that runtime audit. This block is
# the STATIC half, and it exists because Phase 17 multiplies the consumer call sites from three
# to N+1: a new sweep driver that forgets `**artifact["lora_config"]` would be caught only at
# runtime, in the middle of an ~hour-long GPU sweep, instead of in CI in one second.

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# HARD-EQUALITY allowlists, as (file, enclosing function). A Phase-17 driver adds ONE visible
# line here — never a membership relation, which is the guard getting weaker while looking
# bigger. The enclosing function names were resolved from the AST, not typed from memory.
INJECT_LORA_CONSUMERS = (
    ("scripts/personalize_demo.py", "build_demo"),
    ("scripts/phase14_recall.py", "load_adapted_model"),
    ("scripts/phase14_recall.py", "run_bit_identity_control"),
)

INJECT_LORA_PRODUCERS = (
    # Plan 23-08's never-taught arm. It DEFINES the config its exported adapter carries
    # (`export_adapter(lora_config=asdict(tp.LORA_CFG))`), so it is a producer — and it passes
    # `teach_persona.LORA_CFG` rather than a second bare `LoRAConfig()`, which is STRICTLY
    # stronger here: CTRL-03 requires this arm to share the taught arms' budget exactly, and a
    # local `LoRAConfig()` would be a second definition free to drift from the one it mirrors.
    ("scripts/phase23_run.py", "train_never_taught"),
    ("scripts/teach_persona.py", "train_arm"),
    ("scripts/train_adapter_smoke.py", "main"),
)


def _scanned_files():
    """The D-21 file set: ``scripts/*.py`` + ``src/**/*.py``.

    Deliberately not cached: the deliberate-RED probe that proves this guard bites edits a file
    under ``scripts/``, and a cache would make the guard blind to exactly what it is tested on.
    """
    return sorted((_REPO_ROOT / "scripts").glob("*.py")) + sorted(
        (_REPO_ROOT / "src").rglob("*.py")
    )


def _enclosing_functions(tree):
    """``{node: enclosing FunctionDef/AsyncFunctionDef or None}``; ``ast.walk`` is breadth-first,
    so a parent is always resolved before its children."""
    enclosing = {tree: None}
    for parent in ast.walk(tree):
        owner = (
            parent
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
            else enclosing[parent]
        )
        for child in ast.iter_child_nodes(parent):
            enclosing[child] = owner
    return enclosing


def _is_bare_lora_config(node):
    """``LoRAConfig()`` with no arguments — the PRODUCER form, and D-20's diagonal anchor."""
    return (
        isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "LoRAConfig"
        and not node.args
        and not node.keywords
    )


def _reads_artifact_config(node):
    """``LoRAConfig(**<expr>["lora_config"])`` — the CONSUMER form ISO-06 requires."""
    if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "LoRAConfig"):
        return False
    return any(
        keyword.arg is None
        and isinstance(keyword.value, ast.Subscript)
        and isinstance(keyword.value.slice, ast.Constant)
        and keyword.value.slice.value == "lora_config"
        for keyword in node.keywords
    )


def _module_bindings(tree):
    """Every top-level ``NAME = <expr>`` in one module, as ``{name: expr}``."""
    return {
        target.id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def _module_aliases(tree):
    """``{alias: module}`` for every top-level ``import X`` / ``import X as Y`` in one module."""
    return {
        (name.asname or name.name): name.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for name in node.names
    }


def _resolve(config, bindings, aliases):
    """Resolve a config REFERENCE to the expression it names — locally, or across one import.

    Two forms, and both must resolve or the site lands in the unclassified bucket:

    * ``LORA_CFG`` — a bare ``ast.Name``, resolved through this module's own top-level assignments.
      Both original producers pass a module constant rather than an inline call.
    * ``tp.LORA_CFG`` — a module ATTRIBUTE, resolved through the ALIASED module's top-level
      assignments. Plan 23-08's driver imports ``teach_persona``'s anchor instead of re-spelling
      ``LoRAConfig()``, which is the stronger form: it CANNOT drift from the producer it mirrors,
      where a second bare call could. Resolving it keeps this guard's teeth either way — rebind
      ``teach_persona.LORA_CFG`` to ``LoRAConfig(alpha=32.0)`` and the site stops classifying as a
      producer, which is exactly the D-20 anchor movement this test exists to catch.
    """
    if isinstance(config, ast.Name):
        return bindings.get(config.id, config)
    if isinstance(config, ast.Attribute) and isinstance(config.value, ast.Name):
        module = aliases.get(config.value.id)
        if module is None:
            return config
        source = _REPO_ROOT / "scripts" / f"{module}.py"
        if not source.exists():
            return config
        return _module_bindings(ast.parse(source.read_text(encoding="utf-8"))).get(
            config.attr, config
        )
    return config


def _classify_inject_lora_sites():
    """Every ``inject_lora(model, cfg)`` in the scanned set, bucketed by what ``cfg`` is.

    A bare ``ast.Name`` second argument is resolved through the module's own top-level
    assignments, because both producers pass a module constant (``LORA_CFG``) rather than an
    inline call. Resolving it means a rebind to ``LoRAConfig(alpha=32.0)`` lands in the
    unclassified bucket and fails — D-20's anchor moving is exactly what this should catch.
    """
    consumers, producers, unclassified = set(), set(), set()
    for path in _scanned_files():
        file = path.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        enclosing = _enclosing_functions(tree)
        bindings = _module_bindings(tree)
        aliases = _module_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if "inject_lora" not in (
                getattr(node.func, "id", None),
                getattr(node.func, "attr", None),
            ):
                continue
            owner = enclosing[node]
            site = (file, "<module>" if owner is None else owner.name)
            config = node.args[1] if len(node.args) > 1 else None
            config = _resolve(config, bindings, aliases)
            if _reads_artifact_config(config):
                consumers.add(site)
            elif _is_bare_lora_config(config):
                producers.add(site)
            else:
                unclassified.add(site)
    return consumers, producers, unclassified


def test_every_inject_lora_consumer_reads_the_artifact_config():
    """ISO-06, the STATIC half: a consumer that injects at defaults turns this red in CI.

    PRODUCER vs CONSUMER is the whole distinction, and it is why "fix every LoRAConfig()" is
    the wrong instinct:

    * A **producer** DEFINES the config an adapter will be taught under and then carry in its
      own artifact. ``teach_persona.train_arm`` and ``train_adapter_smoke.main`` are the two,
      and ``LoRAConfig()`` there is correct — it is D-20's diagonal anchor, ``r=8,
      alpha=16.0``. Change it and Phase 17's diagonals stop being readable against Phase 14's
      taught-recall 0.3483 and Phase 16's 0.865385, because the adapters would no longer have
      been taught at the rank and scale those numbers were measured at.
    * A **consumer** READS an artifact written earlier and must inject at THAT artifact's
      config. ``alpha`` is invisible to the key and shape audits — an alpha=32 artifact under
      an alpha=16 injection has an identical key set and identical shapes — so before the W1
      fix the delta was silently applied at the wrong magnitude.

    Hard equality on all three buckets, never ``in``: a membership check would pass while a
    fourth, defaulted call site sat beside the three allowlisted ones.
    """
    scanned = _scanned_files()
    assert len(scanned) >= 2, (
        f"the ISO-06 scan collapsed to {len(scanned)} file(s) — a broken glob makes this guard "
        "green by scanning nothing, which is the exact failure mode it exists to close"
    )

    consumers, producers, unclassified = _classify_inject_lora_sites()

    assert sorted(consumers) == sorted(INJECT_LORA_CONSUMERS), (
        "the inject_lora CONSUMER set moved. A site that dropped **artifact['lora_config'] "
        "injects at LoRAConfig() defaults and applies the adapter delta at the wrong scale; a "
        "NEW Phase-17 consumer belongs in INJECT_LORA_CONSUMERS as one visible line.\n"
        f"  found:    {sorted(consumers)}\n  expected: {sorted(INJECT_LORA_CONSUMERS)}"
    )
    assert sorted(producers) == sorted(INJECT_LORA_PRODUCERS), (
        "the inject_lora PRODUCER set moved. These sites DEFINE the config an artifact will "
        "carry, and bare LoRAConfig() is correct there — it is D-20's anchor (r=8, alpha=16).\n"
        f"  found:    {sorted(producers)}\n  expected: {sorted(INJECT_LORA_PRODUCERS)}"
    )
    assert not unclassified, (
        f"inject_lora call site(s) matching neither form: {sorted(unclassified)}. An "
        "unanalysable config expression is not evidence of correctness — write it as "
        "LoRAConfig(**artifact['lora_config']) (consumer) or bare LoRAConfig() (producer)."
    )
