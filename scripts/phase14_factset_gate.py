"""D-06 pre-flight gate: tokenizer census + base-model guessability, behind a blocking verdict.

Measures, for every candidate in every pool of ``scripts/phase14_factset.py``:

  (a) D-02(a)/D-04 tokenizer census — token count and byte-fallback round-trip, by direct
      ``encode``/``decode``, never assumed. Per D-04 the count is a CENSUS FIELD that can never
      reject a candidate; only the D-03 guessability verdict can.
  (b) D-02(b) base-model guessability — the UN-ADAPTED ``convbase_best.pt`` is prompted with each
      candidate's reserved probe questions BEFORE anything is taught. A fact the frozen base can
      already answer is a validity failure of the whole demo: a "successful recall" it could have
      guessed proves nothing.

Every probe prompt is a ``build_recall_prompt`` id sequence — the SAME call the scoring harness
and the demo make (D-18, Pitfall 4) — never a hand-formatted string. Decoding is greedy plus
three draws from one per-probe ``torch.Generator`` seeded ``SEED + probe_index``
(``make_retention_samples.py:8-14`` discipline: an early stop in one probe cannot shift a later
probe's stream). Every completion is quoted verbatim in the report so the human close-call
judgment at the D-06 checkpoint is auditable rather than asserted.

The rendered verdict is the USER'S at the blocking checkpoint — this script only measures and
writes; ``## Verdict`` stays PENDING until a human records GO / ADAPT / STOP. A recorded verdict
is committed evidence: a rerun refuses to clobber it unless ``--force`` is passed.

SECURITY: ``torch.load(CONVBASE_BEST, weights_only=False)`` is a TRUSTED-only read of the
project's OWN checkpoint (T-09-11, T-14-04) — the FULL resume checkpoint carries pickled
optimizer/RNG/numpy objects, so ``weights_only=True`` cannot load it. It is never a foreign
file. Every shareable artifact in this phase goes through ``load_slim`` / ``load_adapter``
(``weights_only=True``) instead. No candidate value is real personal data (T-14-05): everything
in ``results/`` ships publicly. Every proof check here is an explicit ``raise SystemExit`` and
never an ``-O``-strippable ``assert``, so any failure exits non-zero under ``PYTHONOPTIMIZE``.

Run: ``python scripts/phase14_factset_gate.py`` (inside the Python 3.11 venv, on the M3).
"""

import os
import pathlib
import sys
import time

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE importing torch so the backend honors it for the whole process.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import phase14_factset as fs  # noqa: E402  (sibling script; scripts/ is sys.path[0])
import torch  # noqa: E402  (must follow the MPS-fallback env set above)
from _verdict import recorded_verdict  # noqa: E402  (sibling script; scripts/ is sys.path[0])

from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.dialogue import build_recall_prompt  # noqa: E402
from personacore.generation import collect, undecodable_ids_mask  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONVBASE_BEST = _REPO_ROOT / "checkpoints" / "convbase_best.pt"  # own trusted checkpoint
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
REPORT_PATH = _REPO_ROOT / "results" / "phase14_factset_report.md"  # COMMITTED evidence (D-06)

PROBE_SEEDS = 4  # completions per probe question: greedy + 3 seeded samples
SEED = 1337  # seed_everything + base seed of the per-PROBE torch.Generator
PROBE_MAX_NEW_TOKENS = 32  # bounded BEFORE the loop (T-14-08) — recall answers are 11-24 ids
STOP_IDS = {8184, 8185}  # eos + <|user|> — decoding halts on a hallucinated user turn (12-02)
SURVIVOR_TARGET = (5, 10)  # ROADMAP total-fact target the survivor count is reported against
CORE_TARGET = (5, 8)  # D-05 core composition
SOFT_TARGET = (2, 3)  # D-05 labelled soft tier
TEMPERATURE = 0.8  # warm-sampling regime, identical to make_transcripts.py
TOP_P = 0.95


def _complete(model, prompt_ids, device, forbid, **kw):
    """One completion: returns the generated ids (make_transcripts.py:67-81, budget swapped)."""
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = collect(
        model,
        idx,
        max_new_tokens=PROBE_MAX_NEW_TOKENS,
        forbid_ids=forbid,
        stop_ids=STOP_IDS,
        **kw,
    )
    return out[0, len(prompt_ids) :].tolist()


def _probe(model, tok, device, forbid, question, index):
    """``PROBE_SEEDS`` completions for one reserved question: greedy + 3 warm draws.

    The warm draws come from ONE per-probe ``torch.Generator`` (device-matched — ``multinomial``
    rejects a cross-device generator), so an early stop in one probe cannot shift a later
    probe's stream. Returns ``(prompt_ids, [completion text, ...])``.
    """
    prompt_ids = build_recall_prompt(tok, question)
    texts = [tok.decode(_complete(model, prompt_ids, device, forbid, greedy=True))]
    gen_rng = torch.Generator(device=device).manual_seed(SEED + index)
    for _ in range(PROBE_SEEDS - 1):
        ids = _complete(
            model,
            prompt_ids,
            device,
            forbid,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            generator=gen_rng,
        )
        texts.append(tok.decode(ids))
    return prompt_ids, texts


def _quote(text):
    """Verbatim completion on ONE markdown line — literal newlines/tabs shown as escapes."""
    return text.replace("\n", "\\n").replace("\t", "\\t")


def assert_report_not_clobbered():
    """A recorded (non-PENDING) verdict is committed evidence (D-06) — never clobber it silently.

    A rerun would reset ``## Verdict`` to PENDING and drop the hand-added
    ``## Close-Call Rejections`` rows, which ARE the documented judgment D-03 requires.

    CR-02: reads the first ``## Verdict`` SECTION, never the tail after the last occurrence of
    the literal — a prose mention of the heading is not a recorded verdict, and a file with no
    verdict section is refused rather than overwritten blind. Full story at
    ``phase14_recall.assert_report_not_clobbered``.

    Module-level, zero-arg, reading ``REPORT_PATH`` and ``sys.argv`` at call time: that is what
    makes it monkeypatchable, and an inline block in ``main()`` was unreachable from any test
    without a 278 MB checkpoint — which is how this defect survived the first CR-02 fix.
    """
    if REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
        recorded = recorded_verdict(REPORT_PATH.read_text(encoding="utf-8"))
        if recorded is None or "PENDING" not in recorded:
            raise SystemExit(
                f"[phase14_factset_gate] {REPORT_PATH} already carries a recorded verdict — "
                "it is committed evidence (D-06). Pass --force to overwrite and re-measure."
            )


def main() -> None:
    assert_report_not_clobbered()

    if not CONVBASE_BEST.exists():
        raise SystemExit(
            f"[phase14_factset_gate] missing {CONVBASE_BEST} — the D-02(b) guessability probe "
            "measures the REAL frozen base and has no meaning without it."
        )

    started = time.time()
    summary = preflight_device(strict=True)
    print(f"[phase14_factset_gate] preflight: {summary}")
    runtime = RuntimeConfig()
    device = runtime.device
    seed_everything(SEED)

    # weights_only=False: the FULL resume checkpoint carries pickled optimizer/RNG/numpy
    # objects. TRUSTED-only read of the project's OWN checkpoint (T-09-11) — never a foreign
    # file. The SHAREABLE artifact path stays weights_only=True via load_slim / load_adapter.
    blob = torch.load(CONVBASE_BEST, weights_only=False)
    model_cfg = ModelConfig(**blob["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(blob["model"])
    model.to(device)
    model.eval()
    base_sha = blob.get("git_sha", "unknown")
    base_step = blob.get("step", "unknown")
    base_val = blob.get("val_loss", "unknown")
    print(
        f"[phase14_factset_gate] base fingerprint: sha={base_sha} step={base_step} val={base_val}"
    )

    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
    # .to(device): next_token masked_fills logits in place on the model device.
    forbid = undecodable_ids_mask(tok, model_cfg.vocab_size).to(device)

    # ===== (a) D-02(a) tokenizer census — measured, never assumed; a CENSUS field (D-04) =====
    census = {}
    for pool_name, pool in fs.all_pools():
        for fact in pool:
            n_tokens, roundtrip = fs.token_census(tok, fact.value)
            if not roundtrip:
                raise SystemExit(
                    f"[phase14_factset_gate] byte-fallback round-trip FAILED for "
                    f"{fact.id!r} value {fact.value!r} — the tokenizer cannot represent it "
                    "exactly, so no downstream match on it would mean anything."
                )
            census[fact.id] = (pool_name, n_tokens, roundtrip)
    print(f"[phase14_factset_gate] census: {len(census)} candidates, all round-trip exact")

    # ===== (b) D-02(b) guessability probes on the UN-ADAPTED base =====
    # Cached per QUESTION: the base is stateless and the prompt is identical, so two facts
    # sharing a slot's reserved phrasing provably receive the same completions. Caching makes
    # that identity explicit (and halves the run) instead of leaving it accidental.
    probe_cache = {}
    completions = {}
    for pool_name, pool in fs.all_pools():
        for fact in pool:
            per_question = []
            for question in fs.GATE_PROBES[fact.id]:
                if question not in probe_cache:
                    probe_cache[question] = _probe(
                        model, tok, device, forbid, question, len(probe_cache)
                    )
                per_question.append((question, *probe_cache[question]))
            completions[fact.id] = per_question
            texts = [t for _q, _ids, ts in per_question for t in ts]
            passed = fs.exact_match_clean(texts, fact.value)
            print(
                f"[phase14_factset_gate] {pool_name:12} {fact.id:24} {'PASS' if passed else 'FAIL'}"
            )
    print(f"[phase14_factset_gate] probed {len(probe_cache)} unique reserved questions")

    # ===== Verdicts, survivors =====
    verdicts = {}
    for _pool_name, pool in fs.all_pools():
        for fact in pool:
            texts = [t for _q, _ids, ts in completions[fact.id] for t in ts]
            hits = [t for t in texts if not fs.exact_match_clean([t], fact.value)]
            verdicts[fact.id] = (len(hits), len(texts), hits[0] if hits else "")

    # ===== Report =====
    blocks = [
        "# Phase 14 Fact-Set Pre-Flight Report (D-02 / D-03 / D-04 / D-06)",
        "",
        "> **What these numbers are:** a PRE-TEACHING measurement of the FROZEN, UN-ADAPTED",
        f"> `checkpoints/convbase_best.pt` (step {base_step}, val_loss {base_val}, git",
        f"> `{base_sha}`) — how much prior mass it already carries on each candidate fact value,",
        "> probed through `build_recall_prompt`, the SAME call the scoring harness and the demo",
        "> make, so gate and harness can never construct a different prompt (D-18, Pitfall 4).",
        "> Plus the D-02(a) tokenizer census of every candidate value, measured by direct",
        "> `encode`/`decode`.",
        "> **What they are not:** a recall measurement — nothing has been taught yet, and no",
        "> adapter exists. They are also **checkpoint-specific** (D-07): these priors belong to",
        "> this checkpoint at this point in training and have no meaning as a standing invariant.",
        "> Re-running against a future checkpoint requires a FRESH gated measurement, not a test",
        "> re-run. The permanent CPU regression test covers the tokenizer half only.",
        "",
        "## Run Provenance",
        "",
        f"- Driver commit (D-08 provenance for every reserved probe below): `{git_sha()}`",
        f"- Base checkpoint fingerprint: git `{base_sha}`, step `{base_step}`, "
        f"val_loss `{base_val}`",
        f"- Seed: `{SEED}` — `seed_everything({SEED})`, then a per-probe "
        f"`torch.Generator(SEED + probe_index)`",
        f"- Decoding: greedy + {PROBE_SEEDS - 1} warm draws (temperature {TEMPERATURE}, top_p "
        f"{TOP_P}), `max_new_tokens={PROBE_MAX_NEW_TOKENS}`, `stop_ids={sorted(STOP_IDS)}`, "
        "dead ids forbidden",
        f"- Device: `{summary}` · pid `{os.getpid()}`",
        "",
        "## Tokenizer Census (D-02a / D-04)",
        "",
    ]

    for pool_name, pool in fs.all_pools():
        blocks += [
            f"### Pool `{pool_name}` ({len(pool)} candidates)",
            "",
            "| id | slot | tier | value | tokens | round-trip |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for fact in pool:
            _p, n_tokens, roundtrip = census[fact.id]
            blocks.append(
                f"| `{fact.id}` | `{fact.slot}` | {fact.tier} | `{fact.value}` | "
                f"{n_tokens} | {'exact' if roundtrip else 'FAILED'} |"
            )
        blocks.append("")

    blocks += [
        "**D-04 — token count is a CENSUS FIELD, never a reject criterion.** Every count above is",
        "recorded and none of them disqualifies a candidate; only the D-03 exact-match floor plus",
        "a human-recorded close call can reject one. Cheap tokenization is the warning sign, not",
        "the reward: `Max` and `Lily` cost one token *because* the base carries prior mass on",
        "them, which is exactly what makes them invalid under D-01.",
        "",
        "**Measured no-op.** PITFALLS-12's `forbid_ids` sub-filter of the tokenizer pre-flight is",
        "structurally unfireable and is therefore REPORTED, not performed: all 256 byte ids are",
        "live and BPE falls back to bytes for anything unmerged, so `encode()` can never emit a",
        "dead id. The 7,645 dead ids are unreachable *merges*, not unreachable bytes. (The",
        "`forbid_ids` mask is still applied during generation below — that is the CR-01 decoder",
        "guard, a different mechanism from the tokenizer pre-flight sub-filter named here.)",
        "",
        "## Base Guessability Probes (D-02b)",
        "",
        "Every reserved probe question and every completion, verbatim. Completions are the raw",
        "`tok.decode` of the generated ids with literal newlines rendered as `\\n`. Reserved",
        "probes are PERMANENTLY BANNED from every teaching set (D-08) and become seed members of",
        "DEMO-06's never-seen split, carrying the driver commit above as their base-failure",
        "provenance. Two candidates competing for one slot in the `candidate` pool hold DISJOINT",
        "reserved phrasings; later pools reuse the same halves, so an identical question shows",
        "identical completions by construction (the base is stateless and the prompt is the same",
        "id sequence).",
        "",
    ]

    for pool_name, pool in fs.all_pools():
        blocks += [f"### Pool `{pool_name}`", ""]
        for fact in pool:
            n_hits, n_total, _first = verdicts[fact.id]
            mark = "PASS" if n_hits == 0 else "FAIL"
            blocks += [
                f"#### `{fact.id}` — `{fact.slot}` = `{fact.value}` ({fact.tier}) — "
                f"**{mark}** ({n_hits}/{n_total} completions contained the value)",
                "",
            ]
            for question, prompt_ids, texts in completions[fact.id]:
                blocks.append(f"- Q `{question}` — prompt = {len(prompt_ids)} ids")
                for k, text in enumerate(texts):
                    mode = "greedy" if k == 0 else f"warm {k}"
                    blocks.append(f"  - {mode}: `{_quote(text)}`")
            blocks.append("")

    blocks += [
        "## Exact-Match Verdicts (D-03 mechanical floor)",
        "",
        "The objective, pre-registerable half of the rule: a candidate PASSES iff the normalized",
        "value appears in ZERO of its completions. The boundary is unforgiving — ONE containment",
        "out of N is a FAIL. Normalization is `phase14_factset.normalize_for_match` (lowercase →",
        "`detokenize` → collapse whitespace → strip edge punctuation).",
        "",
        "| pool | id | slot | tier | value | contained | verdict | offending completion |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for pool_name, pool in fs.all_pools():
        for fact in pool:
            n_hits, n_total, first = verdicts[fact.id]
            mark = "PASS" if n_hits == 0 else "**FAIL**"
            quoted = f"`{_quote(first)}`" if first else "—"
            blocks.append(
                f"| {pool_name} | `{fact.id}` | `{fact.slot}` | {fact.tier} | `{fact.value}` | "
                f"{n_hits}/{n_total} | {mark} | {quoted} |"
            )

    blocks += [
        "",
        "## Known Close-Call Triggers (pre-registered)",
        "",
        "The frozen base's own prior-mass answer per slot, measured on `convbase_slim.pt` and",
        "recorded in 14-CONTEXT D-01. These were identified **BEFORE the candidate pools were",
        "authored** — they are pre-registered triggers, not discoveries made during this run. A",
        "candidate colliding with one of them is a close-call rejection waiting to happen; start",
        "the human review here.",
        "",
        "| slot | measured base prior |",
        "| --- | --- |",
    ]
    for slot, priors in fs.BASE_PRIOR_SEEDS.items():
        blocks.append(f"| `{slot}` | {', '.join(f'`{p}`' for p in priors)} |")

    blocks += [
        "",
        "## Close-Call Rejections (D-03, human-recorded)",
        "",
        "| fact | slot | quoted base completion | reason |",
        "| --- | --- | --- | --- |",
        "| | | | |",
        "",
        "Every close-call rejection **MUST quote the specific base completion text that triggered",
        "it**. A rejection without a quote is not a valid rejection: this tier exists for the",
        "failure mode exact-match structurally cannot see — semantic proximity (same category,",
        "adjacent plausible value, right slot) that would make a reader suspect the base half-knew",
        "the answer. It is a documented judgment, never a silent one. Leave the table empty if",
        "nothing is rejected on close-call grounds.",
        "",
        "## Survivor Count",
        "",
        "Mechanical-floor survivors only — subtract any close-call rejections recorded above",
        "before reading this against the targets.",
        "",
        "| pool | core survivors | core target | soft survivors | soft target | total | "
        "total target |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for pool_name, pool in fs.all_pools():
        core_ok = sum(1 for f in pool if f.tier == "core" and verdicts[f.id][0] == 0)
        soft_ok = sum(1 for f in pool if f.tier == "soft" and verdicts[f.id][0] == 0)
        n_core = sum(1 for f in pool if f.tier == "core")
        n_soft = sum(1 for f in pool if f.tier == "soft")
        core_target = (
            f"{CORE_TARGET[0]}-{CORE_TARGET[1]} (D-05)" if pool_name == "candidate" else "n/a"
        )
        soft_target = (
            f"{SOFT_TARGET[0]}-{SOFT_TARGET[1]} (D-05)" if pool_name == "candidate" else "n/a"
        )
        total_target = (
            f"{SURVIVOR_TARGET[0]}-{SURVIVOR_TARGET[1]} (ROADMAP)"
            if pool_name == "candidate"
            else (">= 6 (D-09.1)" if pool_name == "calibration" else ">= 4 (D-21.1)")
        )
        blocks.append(
            f"| {pool_name} | {core_ok}/{n_core} | {core_target} | {soft_ok}/{n_soft} | "
            f"{soft_target} | {core_ok + soft_ok} | {total_target} |"
        )

    blocks += [
        "",
        "The `candidate` pool is deliberately over-authored (two candidates per slot) so attrition",
        f"can land inside D-05's {CORE_TARGET[0]}-{CORE_TARGET[1]} core /",
        f"{SOFT_TARGET[0]}-{SOFT_TARGET[1]} soft composition across DISTINCT slots. If it falls",
        "short, that is exactly the information D-06 exists to surface before the set is locked —",
        "say so in the verdict rather than relaxing the filter.",
        "",
        "## Verdict",
        "",
        "PENDING — user decision at checkpoint.",
        "",
    ]

    REPORT_PATH.write_text("\n".join(blocks), encoding="utf-8")
    wall = time.time() - started

    # ===== provenance echo (finetune_ab.py:322-329 shape) =====
    print("[phase14_factset_gate] ===== provenance =====")
    print(f"  seed: {SEED} (seed_everything before the GPT build; per-probe Generator SEED + i)")
    print(f"  driver git_sha: {git_sha()}")
    print(f"  pid: {os.getpid()}  wall: {wall / 60:.1f} min")
    print(f"  preflight: {summary}")
    print(f"  base fingerprint: git_sha={base_sha} step={base_step} val_loss={base_val}")
    n_pass = sum(1 for v in verdicts.values() if v[0] == 0)
    print(
        f"[phase14_factset_gate] wrote {REPORT_PATH}: {len(verdicts)} candidates, "
        f"{n_pass} passed the mechanical floor"
    )


if __name__ == "__main__":
    main()
