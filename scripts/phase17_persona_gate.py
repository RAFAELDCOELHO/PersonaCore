"""ISO-01 pre-flight gate: can the UN-ADAPTED base already produce the 24 minted persona values?

Measures, for every value in ``scripts/phase17_persona_facts.py``:

  (a) the tokenizer census — the live token count and byte-fallback round-trip against the FROZEN
      ``artifacts/tokenizer.json``, printed NEXT TO the transcribed ``VALUE_TOKEN_CENSUS`` literal
      so a divergence between the measured-once census and the tokenizer is visible rather than
      inferred;
  (b) base guessability — the frozen base is prompted with the fixture's OWN ``core_held_out``
      questions for that value's slot, BEFORE anything is taught. A value the base can already
      produce is a validity failure of the whole matrix: an off-diagonal hit on it could never be
      separated from the base's own prior.

RESEARCH F-13 is what this measurement buys. If the base produces ZERO containments of each minted
value, then an off-diagonal hit later cannot be the base's own prior — it must come from adapter
*i*. ISO-03's adapter-off column is then the higher-powered confirmation rather than the only
control.

**That inference holds only if the probe ran on the BASE.** A model carrying a trained adapter is
LESS likely than the base to emit the 24 minted values, so probing one would return a flatteringly
clean gate and a human would record GO on the wrong model — the exact failure class this phase
exists to catch, arriving through the phase's own gate. ``build_unadapted_base`` therefore builds
the base and nothing else, and ``tests/test_phase17_personas.py::
test_the_probe_runs_on_an_unadapted_base`` AST-asserts that no function in this file reaches an
adapter path at all.

The guessability instrument itself is IMPORTED from ``scripts/phase14_factset_gate.py`` at its D-16
public entry point and is never copied (TH-17-17): a second copy is a second guessability rule free
to drift from the one Phase 14 and Phase 16 already published under.

The rendered verdict is the USER'S at the ROADMAP SC2 checkpoint — this script only measures and
writes; ``## Verdict`` stays PENDING until a human records GO / ADAPT / STOP in plan 17-07. A
recorded verdict is committed evidence: a rerun refuses to clobber it unless ``--force`` is passed.

SECURITY: the base is read ONLY through ``personacore.checkpoint.load_slim`` —
``weights_only=True``, the restricted unpickler, zero code execution on load (T-14-22 / TH-17-14).
There is no direct ``torch.load`` in this driver and no full-resume-checkpoint read:
``phase14_factset_gate.main()`` reaches the same architecture through the TRUSTED full checkpoint,
and that half is deliberately not copied here. No minted value is real data — everything in
``results/`` ships
publicly. Every proof check is an explicit ``raise SystemExit`` and never an ``-O``-strippable
``assert``, so a failure exits non-zero under ``PYTHONOPTIMIZE``.

Run: ``python scripts/phase17_persona_gate.py`` (inside the Python 3.11 venv, on the M3).
"""

import os
import pathlib
import sys
import time

# An uncovered MPS op falls back to CPU rather than crashing the run (T-05-04 precedent).
# Set BEFORE torch is imported so the backend honors it for the whole process. Torch arrives
# TRANSITIVELY through every sibling import below (``phase14_factset_gate`` imports it at :45), so
# this statement must precede them — there is no direct torch symbol in this driver to import.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `scripts/` is sys.path[0] only when a script in it is run DIRECTLY; an importlib-loaded test
# harness gets no such entry (phase17_personas.py:41-46, the same bootstrap for the same reason).
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import phase14_factset as fs  # noqa: E402  (needs the sys.path bootstrap above)
import phase14_factset_gate as instrument  # noqa: E402  (the D-16 guessability entry point)
import phase14_recall as recall  # noqa: E402
import phase16_persistence as persistence  # noqa: E402
import phase17_isolation as isolation  # noqa: E402
import phase17_persona_facts as facts  # noqa: E402
import phase17_personas as personas  # noqa: E402
from _verdict import recorded_verdict  # noqa: E402

from personacore.checkpoint import load_slim  # noqa: E402
from personacore.config import ModelConfig, RuntimeConfig  # noqa: E402
from personacore.model import GPT  # noqa: E402
from personacore.preflight import preflight_device  # noqa: E402
from personacore.provenance import git_sha  # noqa: E402
from personacore.seeding import seed_everything  # noqa: E402
from personacore.tokenizer import from_json  # noqa: E402

# The SHAREABLE base artifact, read under `weights_only=True` (T-14-22). Never the full resume
# checkpoint: that read must disable the restricted unpickler by necessity (it carries pickled
# optimizer/RNG/numpy objects), and this driver takes the restricted path instead (TH-17-14).
CONVBASE_SLIM = recall.CONVBASE_SLIM
TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # FROZEN — never retrain
REPORT_PATH = _REPO_ROOT / "results" / "phase17_personas_report.md"  # COMMITTED evidence (SC2)

# Transcribed from plan 17-03's SUMMARY — WHAT EACH MINTING SCREEN ACTUALLY REJECTED while the 24
# values were authored, over the 34 candidate strings that were measured. A filter that bit nothing
# is worth stating as such: "the material passed the gate" must not be read as the gate having
# bitten. The two token-budget rejections happened during authoring, on candidates that were never
# committed; on the 24 committed values all four filters reject nothing.
#
# The D-05 row is the finding worth carrying to the checkpoint: it is NOT one of the four
# mechanical filters and structurally cannot be one. Substring-disjointness passes a one-character
# neighbour happily, so that screen was applied by measurement during authoring and pinned as a
# committed test (`test_values_are_not_token_level_neighbours`) rather than added as a fifth
# filter — a new filter belongs in the pre-registration, and that file is git-ancestry-pinned.
MINTING_SCREEN_RECORD = (
    (
        "`filter_token_budget` (<= 8 ids)",
        "2 of 34",
        "`vurthwaite` (10 ids), `thornebank` (9 ids)",
    ),
    ("`filter_roundtrip`", "0 of 34", "34/34 round-tripped exact, 0 dead ids"),
    (
        "`filter_substring_disjoint`",
        "0 of 34",
        "no nesting in minted union forbidden, under the scorer's own `normalize`",
    ),
    (
        "`filter_absent_from_questions`",
        "0 of 34",
        "no candidate appears in any of the 104 fixture questions",
    ),
    (
        "D-05 neighbour screen (**not** one of the four)",
        "2 of 34",
        "`tarrowgate` (edit distance 1 from a locked Phase 14 street value), "
        "`1971` (edit distance 1 from a calibration-pool year)",
    ),
)


def _prove(condition, message):
    """Loud proof: ``SystemExit`` naming the violated contract (never an ``-O``-strippable assert).

    Own ``[phase17_persona_gate]`` prefix, never imported from a sibling driver — an abort that
    names the wrong driver sends its reader to the wrong file.
    """
    if not condition:
        raise SystemExit(f"[phase17_persona_gate] PROOF FAILED: {message}")


def assert_report_not_clobbered():
    """A recorded (non-PENDING) verdict is committed evidence (SC2) — never clobber it silently.

    A rerun would reset ``## Verdict`` to PENDING and drop the hand-written GO / ADAPT rationale,
    which IS the blocking human judgment ISO-01 requires.

    CR-02: reads the first ``## Verdict`` SECTION through ``_verdict.recorded_verdict``, never the
    tail after the last occurrence of the literal — a prose mention of the heading is not a recorded
    verdict, and a file with no verdict section is refused rather than overwritten blind.

    Module-level, zero-arg, reading ``REPORT_PATH`` and ``sys.argv`` at call time: that is what
    makes it monkeypatchable, and an inline block in ``main()`` was unreachable from any test
    without a 278 MB checkpoint — which is how this defect survived the first CR-02 fix in Phase 14.
    """
    if REPORT_PATH.exists() and "--force" not in sys.argv[1:]:
        recorded = recorded_verdict(REPORT_PATH.read_text(encoding="utf-8"))
        if recorded is None or "PENDING" not in recorded:
            raise SystemExit(
                f"[phase17_persona_gate] {REPORT_PATH} already carries a recorded verdict — "
                "it is committed evidence (ROADMAP SC2). Pass --force to overwrite and re-measure."
            )


def build_unadapted_base(device):
    """The UN-ADAPTED base: ``(model, model_cfg, ckpt)``, with no adapter of any kind attached.

    A named function rather than an inline block in ``main()`` so the structural guard in
    ``tests/test_phase17_personas.py`` can assert on it without a 278 MB checkpoint on disk.

    **Why this is not delegated to the Phase 14 recall harness's adapted-model loader**
    (``scripts/phase14_recall.py:496``), which looks like the shared model-build entry point and
    which Phase 16 does call. Measured, end to end, in the working tree: it defaults its adapter
    path to the shippable persona file under ``checkpoints/`` (``:516``), raises ``SystemExit`` if
    that file is absent (``:530``), wraps every allowlisted projection in a LoRA module (``:557``)
    and copies the adapter tensors into them (``:565``) — all unconditionally. **There is no
    un-adapted return path.** Calling it without an adapter path does not give the base; it gives
    Phase 14's TAUGHT persona.

    Probing that model would measure a taught model, which is LESS likely than the base to emit the
    24 minted values. The ISO-01 gate would come back flatteringly clean, a human would record GO on
    the wrong model, and the whole F-13 inference — "an off-diagonal hit cannot be the base's own
    prior" — would rest on a measurement of something else. That is the failure class this phase
    exists to catch, arriving through the phase's own gate, which is why it gets a structural pin
    rather than care (TH-17-42).

    The body is the FIRST HALF of that same function (``phase14_recall.py:522-528``) and stops
    where the injection begins: ``load_slim`` (``weights_only=True``, the restricted unpickler —
    T-14-22 / TH-17-14) -> ``ModelConfig`` -> ``GPT`` -> ``load_state_dict`` -> ``.to(device)`` ->
    ``.eval()``. ``phase14_factset_gate.main():204`` reaches the same architecture through the
    TRUSTED full-resume checkpoint, with the restricted unpickler necessarily disabled; that half
    is deliberately NOT copied, because the shareable artifact plus the restricted unpickler gets
    to the same weights under a stricter bar.
    """
    if not CONVBASE_SLIM.exists():
        raise SystemExit(
            f"[phase17_persona_gate] missing {CONVBASE_SLIM} — the shareable base artifact. Run "
            "`python scripts/export_slim.py` to export it from checkpoints/convbase_best.pt. The "
            "ISO-01 guessability probe measures the REAL frozen base and has no meaning without it."
        )
    ckpt = load_slim(CONVBASE_SLIM)  # weights_only=True — restricted unpickler (T-14-22).
    model_cfg = ModelConfig(**ckpt["model_config"])
    model = GPT(model_cfg)
    model.load_state_dict(ckpt["model"])
    model.to(device)
    model.eval()
    return model, model_cfg, ckpt


def main() -> None:
    # FIRST, before anything expensive. A run that refuses to write its report only at the end has
    # already spent the GPU half for nothing (RESEARCH Pitfall 7).
    assert_report_not_clobbered()

    started = time.time()
    summary = preflight_device(strict=True)
    print(f"[phase17_persona_gate] preflight: {summary}")
    runtime = RuntimeConfig()
    device = runtime.device
    # ONE seed constant in play. `seed_everything` takes the recall harness's SEED and the per-probe
    # `torch.Generator` inside the imported instrument takes its own; they are the same number
    # today, and the report states a single seed, so a divergence would make that statement false.
    _prove(
        recall.SEED == instrument.SEED,
        f"phase14_recall.SEED is {recall.SEED} but the imported guessability instrument seeds its "
        f"per-probe generator from {instrument.SEED}. This report states ONE seed; two would make "
        "the recorded provenance describe a stream nobody drew from",
    )
    seed_everything(recall.SEED)

    tok = from_json(TOKENIZER_PATH)  # FROZEN production artifact — never retrain (Pitfall 6)
    # Built ONCE and threaded everywhere, recorded by content sha256 (the mask is a device-resident
    # tensor built from a loaded tokenizer, so it can be neither an import-time constant nor
    # meaningfully compared with `is` after a `.to(device)`). Never build a second mask.
    forbid, forbid_sha = persistence.resolve_forbid(tok, ModelConfig.vocab_size)
    n_masked = int(forbid.sum())
    # .to(device): next_token masked_fills logits IN PLACE on the model device (CR-01).
    forbid = forbid.to(device)
    print(f"[phase17_persona_gate] forbid_ids: {n_masked} masked, sha256 {forbid_sha[:12]}")

    # ===== The fixture, regrouped by SLOT (D-02) — 13 questions x 8 slots = 104 =====
    by_slot = isolation.held_out_by_slot()
    questions_by_slot = {
        slot: tuple(item.question for item in items) for slot, items in by_slot.items()
    }
    all_questions = tuple(q for slot in personas.CORE_SLOTS for q in questions_by_slot[slot])

    # ===== The four mechanical filters, on CPU, BEFORE the model load =====
    # Seconds of CPU that make the expensive GPU half fail fast on material that was never going to
    # work. ONE entry point rather than four call sites, so this driver and the CPU tests cannot
    # drift into checking different subsets of the same rule.
    checked = facts.assert_material_passes_filters(tok, all_questions)
    print(f"[phase17_persona_gate] four minting filters passed over {len(checked)} values")

    # ===== The tokenizer census: the transcribed literal NEXT TO the live re-measurement =====
    census = {}
    for fact in facts.all_facts():
        n_tokens, roundtrip = fs.token_census(tok, fact.value)
        census[fact.id] = (n_tokens, roundtrip, facts.VALUE_TOKEN_CENSUS[fact.id])
    # `filter_token_budget` reads the TRANSCRIBED literal, so it structurally cannot see a live
    # count that has drifted past the ceiling. This is the same bound, measured.
    over = sorted(
        key for key, (live, _rt, _lit) in census.items() if live > personas.MAX_VALUE_TOKENS
    )
    _prove(
        not over,
        f"{over} measure over MAX_VALUE_TOKENS = {personas.MAX_VALUE_TOKENS} against the frozen "
        "tokenizer right now, whatever the transcribed census says. The recall budget is derived "
        "from the census, so a 9-token value moves RECALL_MAX_NEW_TOKENS from 48 to 56 and this "
        "phase stops sharing a generation budget with any published Phase 14 or Phase 16 number",
    )
    diverged = sorted(key for key, (live, _rt, lit) in census.items() if live != lit)
    print(f"[phase17_persona_gate] census: 24 values, {len(diverged)} diverged from the literal")

    # ===== The UN-ADAPTED base. No adapter. =====
    model, model_cfg, ckpt = build_unadapted_base(device)
    _prove(
        model_cfg.vocab_size == ModelConfig.vocab_size,
        f"the base checkpoint declares vocab_size {model_cfg.vocab_size} but the forbid_ids mask "
        f"above was sized at {ModelConfig.vocab_size}. A mis-sized mask leaves dead ids unmasked, "
        "so a value could be 'produced' out of ids the tokenizer cannot decode",
    )
    base_sha = ckpt["git_sha"]
    base_step = ckpt["step"]
    base_val = ckpt["val_loss"]
    print(
        f"[phase17_persona_gate] base fingerprint: sha={base_sha} step={base_step} val={base_val} "
        "(no adapter injected, no adapter weights loaded)"
    )

    # ===== Guessability on the UN-ADAPTED base (RESEARCH F-07) =====
    # Probed with the fixture's OWN 13 held-out questions per slot rather than the hand-written
    # slot bank: it measures the base on the exact instrument the matrix scores on, at 13 x 4 = 52
    # completions per slot against Phase 14's 4 x 4 = 16.
    #
    # Cached per QUESTION. The base is stateless and the prompt is the same id sequence, so the
    # three personas' values for a slot are provably judged against ONE shared set of completions;
    # caching makes that identity explicit instead of leaving it accidental, and takes the run from
    # 1,248 generations to 8 x 13 x 4 = 416. `start_index` offsets the per-probe generator seeding
    # so every batch draws a disjoint stream.
    probe_cache = {}
    for slot in personas.CORE_SLOTS:
        anchor = next(
            fact.value for fact in facts.PERSONA_FACTS[personas.PERSONAS[0]] if fact.slot == slot
        )
        fresh = tuple(q for q in questions_by_slot[slot] if q not in probe_cache)
        probed = instrument.probe_guessability(
            model, tok, device, forbid, anchor, fresh, start_index=len(probe_cache)
        )
        for entry in probed["probes"]:
            probe_cache[entry["question"]] = entry
        # Not a restatement of what the instrument just computed: it checks that reading the
        # completions back OUT of the cache reproduces the text set the instrument itself judged.
        # Every one of the 24 verdicts below is derived from the cache, so a flattening that
        # dropped the greedy draw would silently narrow all of them.
        cached = [text for question in fresh for text in probe_cache[question]["completions"]]
        _prove(
            fs.exact_match_clean(cached, anchor) == probed["clean"],
            f"the cached completions for slot {slot!r} give a different guessability verdict than "
            "the instrument returned over the same probes — the cache read is losing completions, "
            "and every value judged from it would be judged on less evidence than was generated",
        )
        print(f"[phase17_persona_gate] probed slot {slot:14} {len(fresh):2} fresh question(s)")

    _prove(
        len(probe_cache) == personas.QUESTIONS_PER_SLOT * personas.SLOTS_EXPECTED,
        f"{len(probe_cache)} unique questions were probed, not "
        f"{personas.QUESTIONS_PER_SLOT * personas.SLOTS_EXPECTED}. Every per-slot denominator in "
        "this report, and the 416-completion claim it rests on, assumes the 8 slots hold disjoint "
        "question sets of exactly 13",
    )

    # ===== Per-value verdicts, all 24 through the same code path =====
    # `exact_match_clean` is the imported objective half of the guessability rule — the same
    # function the instrument applies internally — so the anchor value is judged by exactly the
    # same call as the other two values in its slot rather than reading a returned field for one
    # and computing it for two.
    verdicts = {}
    for persona, persona_facts in facts.PERSONA_FACTS.items():
        for fact in persona_facts:
            texts = [
                text
                for question in questions_by_slot[fact.slot]
                for text in probe_cache[question]["completions"]
            ]
            hits = [text for text in texts if not fs.exact_match_clean([text], fact.value)]
            verdicts[fact.id] = (len(hits), len(texts), fs.exact_match_clean(texts, fact.value))
            mark = "clean" if not hits else "NOT CLEAN"
            print(
                f"[phase17_persona_gate] {persona:10} {fact.id:22} {mark:9} "
                f"{len(hits)}/{len(texts)}"
            )
    n_clean = sum(1 for _hits, _total, clean in verdicts.values() if clean)

    # =========================================================================================
    # ===== The report ========================================================================
    # =========================================================================================
    blocks = [
        "# Phase 17 Persona Pre-Flight Report (ISO-01 / D-04 / D-05 / D-06)",
        "",
        "> **What these numbers are:** a PRE-TEACHING measurement of the FROZEN, UN-ADAPTED base —",
        "> how much prior mass it already carries on each of the 24 minted persona values, probed",
        "> through `build_recall_prompt`, the SAME call the scoring harness and the demo make,",
        "> with the fixture's OWN held-out questions for each value's slot (RESEARCH F-07). Plus",
        "> the tokenizer census of every value, measured by direct `encode`/`decode`.",
        "> **What they are not:** a recall measurement — nothing has been taught yet and no",
        "> Phase 17 adapter exists. They are also **checkpoint-specific**: these priors belong to",
        "> this checkpoint at this point in training and have no meaning as a standing invariant.",
        "> A future checkpoint requires a FRESH gated measurement, not a test re-run. The",
        "> permanent CPU regression test (`tests/test_phase17_personas.py`) covers the tokenizer",
        "> half only.",
        "",
        "## Base",
        "",
        f"- Checkpoint: `{CONVBASE_SLIM.relative_to(_REPO_ROOT)}`, read through "
        "`personacore.checkpoint.load_slim` (`weights_only=True`, the restricted unpickler)",
        f"- Fingerprint: git `{base_sha}`, step `{base_step}`, val_loss `{base_val}`",
        f"- Architecture: {model_cfg.n_layer} layers x {model_cfg.n_head} heads, "
        f"n_embd {model_cfg.n_embd}, vocab_size {model_cfg.vocab_size}",
        "",
        "**No adapter was injected and no adapter weights were loaded.** The model probed below is",
        "the base checkpoint as exported, with nothing attached to it. This is the load-bearing",
        "property of the whole report: a model carrying a trained adapter is LESS likely than the",
        "base to emit these 24 values, so probing one would return a clean gate for the wrong",
        "reason and this document would be evidence about a different model. It is pinned",
        "structurally by `tests/test_phase17_personas.py`'s un-adapted-base scan, which",
        "AST-asserts that no function in the driver reaches an adapter path at all.",
        "",
        "## Tokenizer Census",
        "",
        "The transcribed `VALUE_TOKEN_CENSUS` literal beside the live re-measurement against the",
        "frozen `artifacts/tokenizer.json`. They are two different things on purpose: the literal",
        "is the expectation the budget-parity proof reads, and a divergence means either the",
        "frozen tokenizer changed or a value was edited after it was measured — both invalidate",
        "the claim that this material fits `RECALL_MAX_NEW_TOKENS = 48`.",
        "",
        "| persona | id | slot | value | transcribed | live | round-trip | agrees |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for persona, persona_facts in facts.PERSONA_FACTS.items():
        for fact in persona_facts:
            live, roundtrip, literal = census[fact.id]
            blocks.append(
                f"| {persona} | `{fact.id}` | `{fact.slot}` | `{fact.value}` | {literal} | "
                f"{live} | {'exact' if roundtrip else '**FAILED**'} | "
                f"{'yes' if live == literal else '**DIVERGED**'} |"
            )
    blocks += [
        "",
        f"Ceiling: `MAX_VALUE_TOKENS = {personas.MAX_VALUE_TOKENS}`. Measured maximum: "
        f"{max(live for live, _rt, _lit in census.values())}. Rows diverging from the transcribed "
        f"literal: **{len(diverged)}**.",
        "",
        "## Guessability",
        "",
        f"Every completion the un-adapted base produced, verbatim. Per slot: "
        f"{personas.QUESTIONS_PER_SLOT} held-out questions x "
        f"{instrument.PROBE_SEEDS} draws (greedy + {instrument.PROBE_SEEDS - 1} warm) = "
        f"{personas.QUESTIONS_PER_SLOT * instrument.PROBE_SEEDS} completions, cached per question",
        "and shared across the three personas' values for that slot — the base is stateless and",
        "the prompt is the same id sequence, so the three values are provably judged against ONE",
        "set of completions rather than three independently generated ones.",
        "",
        "The mechanical half of the rule is `phase14_factset.exact_match_clean`: a value passes",
        "iff its normalized form appears in ZERO of the completions. The boundary is unforgiving —",
        "ONE containment out of 52 is a failure. **The close-call tier is the human judgment this",
        "report exists for**: a value the base does not produce exactly but comes semantically",
        "close to is a value whose off-diagonal cell would later be ambiguous, and only a reader",
        "of the quoted text below can see that.",
        "",
    ]
    for slot in personas.CORE_SLOTS:
        slot_questions = questions_by_slot[slot]
        n_completions = sum(len(probe_cache[q]["completions"]) for q in slot_questions)
        blocks += [
            f"### Slot `{slot}` — {len(slot_questions)} questions, {n_completions} completions",
            "",
            "| persona | id | value | contained | verdict |",
            "| --- | --- | --- | --- | --- |",
        ]
        for persona, persona_facts in facts.PERSONA_FACTS.items():
            fact = next(f for f in persona_facts if f.slot == slot)
            n_hits, n_total, is_clean = verdicts[fact.id]
            blocks.append(
                f"| {persona} | `{fact.id}` | `{fact.value}` | {n_hits}/{n_total} | "
                f"clean={is_clean} |"
            )
        blocks += ["", "Completions, verbatim:", ""]
        for question in slot_questions:
            entry = probe_cache[question]
            blocks.append(f"- Q `{question}` — prompt = {len(entry['prompt_ids'])} ids")
            for k, text in enumerate(entry["completions"]):
                mode = "greedy" if k == 0 else f"warm {k}"
                shown = text.replace("\n", "\\n").replace("\t", "\\t")
                blocks.append(f"  - {mode}: `{shown}`")
        blocks.append("")

    blocks += [
        f"**{n_clean} of {len(verdicts)} values are clean on the mechanical floor.**",
        "",
        "## Filters",
        "",
        "What each minting screen rejected while the 24 values were authored, over the 34",
        "candidate strings that were measured (transcribed from plan 17-03). A screen that bit",
        "nothing is recorded as such: 'the material passed the gate' must not be read as the gate",
        "having bitten. On the 24 COMMITTED values all four mechanical filters reject nothing —",
        "they were re-run on CPU immediately before the probes above and passed.",
        "",
        "| screen | rejected | which |",
        "| --- | --- | --- |",
    ]
    for screen, rejected, which in MINTING_SCREEN_RECORD:
        blocks.append(f"| {screen} | {rejected} | {which} |")
    blocks += [
        "",
        "The D-05 row is the one to carry into the verdict. It is **not** one of the four",
        "mechanical filters and structurally cannot be: substring-disjointness passes a",
        "one-character neighbour happily, because neither of two near-twin values contains the",
        "other. That screen was applied by measurement during authoring and is pinned as a",
        "committed test rather than added as a fifth filter — a new filter belongs in the",
        "pre-registration, and that file is git-ancestry-pinned.",
        "",
        "## Provenance",
        "",
        f"- Driver commit: `{git_sha()}`",
        f"- Base checkpoint fingerprint: git `{base_sha}`, step `{base_step}`, "
        f"val_loss `{base_val}`",
        f"- Seed: `{recall.SEED}` — `seed_everything({recall.SEED})`, then a per-probe "
        f"`torch.Generator({recall.SEED} + probe_index)`",
        f"- Decoding: greedy + {instrument.PROBE_SEEDS - 1} warm draws (temperature "
        f"{instrument.TEMPERATURE}, top_p {instrument.TOP_P}), "
        f"`max_new_tokens={instrument.PROBE_MAX_NEW_TOKENS}`, "
        f"`stop_ids={sorted(instrument.STOP_IDS)}`",
        f"- `forbid_ids`: sha256 `{forbid_sha}`, {n_masked} of {ModelConfig.vocab_size} ids masked",
        f"- Tokenizer: `{TOKENIZER_PATH.relative_to(_REPO_ROOT)}` (FROZEN — never retrained)",
        f"- Fixture: the binding `results/phase16_recall_sample.json` `core_held_out` tier, "
        f"{len(all_questions)} questions regrouped into {personas.SLOTS_EXPECTED} slots",
        f"- Probes: {len(probe_cache)} unique questions, "
        f"{sum(len(entry['completions']) for entry in probe_cache.values())} completions generated",
        f"- Device: `{summary}` · pid `{os.getpid()}` · wall "
        f"`{(time.time() - started) / 60:.1f}` min",
        "",
        "## Recording The Verdict",
        "",
        "These instructions live ABOVE the verdict section, not inside it, and that placement is",
        "load-bearing rather than tidy. `assert_report_not_clobbered` refuses to overwrite this",
        "file once the recorded verdict no longer reads as unrecorded, and it reads the verdict",
        "SECTION — everything from that heading to the end of the file. Boilerplate left sitting",
        "under the heading therefore travels INTO the recorded verdict, and any sentence there",
        "naming the unrecorded state would keep the guard permanently disarmed after a human had",
        "written GO. That is the CR-02 failure class, arriving through the wording of the thing it",
        "protects, so the section below holds the verdict and nothing else.",
        "",
        "Replace the whole line below BY HAND with `GO` or `ADAPT` as the first word, followed by",
        "the reasoning and any value you are uneasy about. `ADAPT` replaces named values in",
        "`scripts/phase17_persona_facts.py` — **never** in `scripts/phase17_personas.py`, which is",
        "git-ancestry-pinned — re-measures `VALUE_TOKEN_CENSUS` in the same commit, re-runs the",
        "D-05 neighbour screen, and re-runs this gate. `STOP` escalates. Nothing downstream trains",
        "until the section below reads GO or ADAPT: `teach_persona._require_go_verdict` refuses on",
        "STOP and on an unrecorded verdict alike.",
        "",
        "## Verdict",
        "",
        "PENDING — user decision at the ISO-01 checkpoint (ROADMAP SC2).",
        "",
    ]

    REPORT_PATH.write_text("\n".join(blocks), encoding="utf-8")
    wall = time.time() - started

    print("[phase17_persona_gate] ===== provenance =====")
    print(f"  seed: {recall.SEED} (seed_everything; per-probe Generator SEED + i)")
    print(f"  driver git_sha: {git_sha()}")
    print(f"  pid: {os.getpid()}  wall: {wall / 60:.1f} min")
    print(f"  preflight: {summary}")
    print(f"  base fingerprint: git_sha={base_sha} step={base_step} val_loss={base_val}")
    print("  base build: load_slim only — no adapter injected, no adapter weights loaded")
    print(
        f"[phase17_persona_gate] wrote {REPORT_PATH}: {len(verdicts)} values, "
        f"{n_clean} clean on the mechanical floor"
    )


if __name__ == "__main__":
    main()
