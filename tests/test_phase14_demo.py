"""Structural regression tests for ``scripts/personalize_demo.py`` (DEMO-07 / D-17 / D-18).

What this pins, forever — three claims the demo makes that only a test can hold:

  1. **D-17 mask parity.** The demo builds its ``forbid_ids`` from the identical
     ``undecodable_ids_mask(tok, vocab_size)`` call ``scripts/demo_app.py:90`` makes, and it
     actually threads the result into its generation call.
  2. **D-18 prompt byte-identity.** The live token panel and the scoring harness's committed
     context dump render the SAME ``ids`` line for the same question, because both route
     through ``phase14_recall.render_context_dump``.
  3. **The offline stylesheet lock.** The served page carries zero remote stylesheets.

Plus the clean-room posture: no locked fact value reaches the demo process by ANY path,
including a transitive import.

**Scripts-load / gradio deviation, justified.** ``tests/test_demo_callback.py:3-6`` states the
house convention: tests import nothing from gradio and nothing from ``scripts/``. This module
deviates deliberately. D-17 and D-18 both justify themselves with "structurally enforced rather
than by convention", and enforcement that cannot import the file it enforces is not enforcement.
The ``demo`` extra is installed in CI (``.github/workflows/ci.yml``), in ``Makefile:install``,
and in CLAUDE.md's documented setup so all three move together — omitting it makes this module a
hard pytest COLLECTION error, not a skip.

**Which assertions run in CI and which are local-only — stated rather than left to a reader.**
D-17's literal wording is to compare the mask tensors captured inside BOTH scripts'
``build_demo()``. That comparison **cannot run in CI**, because ``build_demo()`` on either side
needs a checkpoint and ``checkpoints/ is gitignored`` (``.gitignore:14``). So:

  - **What runs in CI:** ``build_forbid_ids`` produces a tensor ``torch.equal`` to the same
    ``undecodable_ids_mask`` call ``demo_app.py`` makes, at the same pinned shape, dtype, and
    7645 count; plus a source assertion that ``build_demo`` calls it and threads ``forbid_ids=``
    through. That catches the named ARCHITECTURE Anti-pattern 7 drift — a missing mask, a wrong
    ``vocab_size``, a mask built but never passed.
  - **What CI does NOT catch:** a divergence introduced *inside* ``demo_app.build_demo()``
    itself. That is acceptable **only** because D-17 freezes that file — and
    ``test_demo_app_frozen`` below is what makes the freeze real.
  - **local-only:** the two genuinely checkpoint-dependent assertions at the bottom, each
    carrying its own reason comment. A silently-skipped test is convention wearing a test's
    clothes, so no ``skipif`` here goes unexplained.

The same split applies to the stylesheet lock: CI asserts ``gr.Blocks(theme=THEME).stylesheets``
is empty on the real theme object plus a source assertion that ``build_demo`` passes
``theme=THEME``; the literal ``build_demo().stylesheets == []`` is local-only. D-18's
byte-identity test needs no such weakening — neither side needs a checkpoint, so it is fully
CI-enforced.

CPU-only: no GPU, no generation, and ``launch()`` is never called.
"""

import ast
import importlib.util
import inspect
import pathlib
import re
import subprocess
import sys

import gradio as gr
import pytest
import torch

from personacore.dialogue import build_recall_prompt
from personacore.generation import undecodable_ids_mask
from personacore.tokenizer import from_json

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_REPO_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

_TOKENIZER_PATH = _REPO_ROOT / "artifacts" / "tokenizer.json"  # git-tracked — CI has it.

# The commit that last touched scripts/demo_app.py. D-17 freezes that file for this phase.
_DEMO_APP_SHA = "cdd778692bfb2a14167ba33545a2f6a09148d451"


def _load(name, filename):
    """``importlib``-load a ``scripts/`` module WITHOUT registering it in ``sys.modules``.

    ``spec_from_file_location`` + ``module_from_spec`` + ``exec_module`` deliberately skips the
    ``sys.modules`` registration a plain ``import`` performs. That matters here: ``scripts/`` is
    on ``sys.path`` for this module, so a plain ``import phase14_factset`` would seed the very
    entry ``test_demo_process_is_fact_free`` measures and turn it spuriously red depending on
    test order.
    """
    spec = importlib.util.spec_from_file_location(name, _REPO_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pd = _load("personalize_demo", "personalize_demo.py")
pr = _load("phase14_recall", "phase14_recall.py")

# Every string the UI puts on screen. Scanned wholesale rather than sampled: one careless
# f-string is the entire failure mode these two copy tests exist to catch.
_UI_COPY = (
    pd.TITLE,
    pd.DESCRIPTION,
    pd.HONESTY_LOCK,
    pd.TEXTBOX_PLACEHOLDER,
    pd.EMPTY_CHAT,
    pd.EXAMPLES_CAPTION,
    pd.MEMORY_LABEL,
    pd.MEMORY_INFO,
    pd.RESET_LABEL,
    pd.STATUS_ON,
    pd.STATUS_OFF,
    pd.STATUS_DELETED,
    pd.PANEL_LABEL,
    pd.PANEL_CAPTION,
    pd.ACCORDION_LABEL,
    pd.SLIDER_INFO,
    *pd.EXAMPLES,
)

_DEMO_SOURCE = (_REPO_ROOT / "scripts" / "personalize_demo.py").read_text(encoding="utf-8")

_REAL_ARTIFACTS = (
    _REPO_ROOT / "checkpoints" / "model_slim.pt",
    _REPO_ROOT / "checkpoints" / "convbase_slim.pt",
    _REPO_ROOT / "checkpoints" / "persona_adapter.pt",
)
_HAVE_REAL_ARTIFACTS = all(p.exists() for p in _REAL_ARTIFACTS)


@pytest.fixture(scope="module")
def tok():
    return from_json(_TOKENIZER_PATH)


# --------------------------------------------------------------------------- #
# D-17 — the forbid_ids mask
# --------------------------------------------------------------------------- #


def test_forbid_ids_parity(tok):
    """D-17: the demo's mask is the SAME construction ``scripts/demo_app.py:90`` uses.

    ARCHITECTURE Anti-pattern 7 is a generation path that samples over the full 8192-id table
    while the frozen tokenizer decodes only 547 live ids. The pinned numbers below are the same
    ones ``tests/test_forbid_ids.py`` already holds for ``demo_app``'s side, so a drift on
    either side of the duplication shows up as a failure rather than as a crash on camera.
    """
    mine = pd.build_forbid_ids(tok, 8192)
    theirs = undecodable_ids_mask(tok, 8192)  # the literal call demo_app.py makes.

    assert torch.equal(mine, theirs)
    assert mine.shape == (1, 8192)
    assert mine.dtype == torch.bool
    # 8192 total - 547 decodable (256 bytes + 283 merges + 8 specials) = 7645 dead ids.
    assert int(mine.sum()) == 7645
    assert not bool(mine[0, 8184]), "eos is a registered special — it must NEVER be masked"


def test_forbid_ids_threaded_through():
    """The half of D-17 a tensor comparison structurally cannot see.

    A mask that is built correctly and then never passed to the generation call is
    indistinguishable, tensor-wise, from a correct implementation — and produces exactly the
    Anti-pattern 7 crash the mask exists to prevent. Only the source can answer it.
    """
    src = inspect.getsource(pd.build_demo)
    assert "build_forbid_ids(" in src
    assert "forbid_ids=forbid_ids" in src


# --------------------------------------------------------------------------- #
# D-18 — the token panel and the harness dump are one renderer
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "question",
    [
        "",
        "what is the name of your dog?",
        "tell me the name you go by.",
        "what is the town you live in?",
        "who am i?",
        "something the model has never been asked before, with punctuation!",
    ],
)
def test_prompt_ids_identical(tok, question):
    """D-18: two code paths claiming to show the same thing stay true only under enforcement.

    The demo panel and the harness's committed dump must render a CHARACTER-IDENTICAL ``ids``
    line for the same question, and the ids must equal ``build_recall_prompt`` element for
    element — nothing reordered, nothing elided, no re-encoding for display.
    """
    panel = pd.render_token_panel(tok, question, source="demo panel").splitlines()
    dump = pr.render_context_dump(tok, question, source="harness dump").splitlines()

    assert panel[0] == dump[0]  # byte-identical ids line
    assert ast.literal_eval(panel[0].split(" : ", 1)[1]) == build_recall_prompt(tok, question)
    assert panel[1] == dump[1]  # and the decoded line too
    # Only the `source` line differs — it is the provenance label, by design.
    assert panel[2] != dump[2]


def test_empty_question_scaffold_is_populated(tok):
    """14-UI-SPEC: the panel is POPULATED at startup, never blank — with real computed data.

    An empty ``gr.Code`` reads as broken and a ``"waiting…"`` string reads as a pending fetch,
    which is a fatal framing for an offline demo. Three real ids in the permanent three-line
    format read as a panel that works and simply has nothing in it yet.
    """
    scaffold = pd.render_token_panel(tok, "", source=pd.PANEL_SOURCE_SCAFFOLD).splitlines()
    assert scaffold[0] == "ids   (3) : [8187, 8185, 8186]"
    assert scaffold[1] == "decoded   : <|system|><|user|><|assistant|>"
    assert scaffold[2] == f"source    : {pd.PANEL_SOURCE_SCAFFOLD}"


def test_memory_toggle_is_weights_not_prompt():
    """The entire claim: memory ON/OFF is an ADAPTER swap, never a prompt edit.

    ``build_recall_prompt``'s ``persona=`` argument exists only for the D-11.1 fairness control
    (14-01). If the demo ever passed it, the toggle would be injecting persona TEXT into the
    context — the exact thing the token panel is on screen to disprove — and the demo would be
    showing prompt-based personalization while claiming weight-based personalization.
    """
    src = inspect.getsource(pd.build_demo)
    assert "build_recall_prompt(tok, question)" in src
    assert "persona=" not in _DEMO_SOURCE, "the toggle must never inject persona text"
    # The toggle and Reset act on the MODEL, not on the prompt.
    assert "set_adapter_enabled(" in src
    assert "eject_adapter(" in src


# --------------------------------------------------------------------------- #
# The offline guarantee
# --------------------------------------------------------------------------- #


def test_no_remote_stylesheets():
    """14-UI-SPEC's offline lock, in its CI-runnable form.

    MEASURED: the stock ``gr.themes.Default()`` carries exactly one Google Fonts stylesheet URL
    for its BODY font, and the ``font=`` override empties ``_stylesheets`` while changing no
    other theme variable. The full ``build_demo().stylesheets == []`` assertion needs a
    checkpoint and is the local-only test at the bottom of this file.
    """
    assert gr.themes.Default()._stylesheets, "the stock theme is expected to carry a remote URL"
    assert gr.Blocks(theme=pd.THEME).stylesheets == []
    assert "theme=THEME" in inspect.getsource(pd.build_demo)


def test_analytics_killswitch_precedes_gradio_import():
    """T-14-27: the kill-switch is ORDER-dependent, so its position is the contract.

    ``GRADIO_ANALYTICS_ENABLED`` is read at gradio import time; setting it afterwards kills
    telemetry but not the startup version-check HTTP ping (08-RESEARCH Pitfall 5). An import
    reordering — by a human or by a formatter — would silently reopen a network call on a demo
    whose whole thesis is on-device operation.
    """
    killswitch = _DEMO_SOURCE.index('os.environ["GRADIO_ANALYTICS_ENABLED"]')
    gradio_import = _DEMO_SOURCE.index("import gradio as gr")
    assert killswitch < gradio_import
    assert "analytics_enabled=False" in inspect.getsource(pd.build_demo)
    assert "share=False" in inspect.getsource(pd.main)


# --------------------------------------------------------------------------- #
# Clean room — the demo process holds an integer, not the answers
# --------------------------------------------------------------------------- #


def test_no_fact_values_in_ui_chrome():
    """B-01: no locked or soft fact value may appear in the demo's copy or its source.

    The demo process must never hold the fact strings. The values are read through a
    non-registering ``importlib`` load (see ``_load``) so this test cannot pollute
    ``test_demo_process_is_fact_free``.
    """
    fs = _load("phase14_factset", "phase14_factset.py")
    values = [f.value for f in fs.LOCKED_FACTS + fs.SOFT_TIER_FACTS]
    assert len(values) == 10, "8 locked core + 2 soft tier — the fact set this phase locked"

    normalized_source = fs.normalize_for_match(_DEMO_SOURCE)
    for value in values:
        needle = fs.normalize_for_match(value)
        for copy in _UI_COPY:
            assert needle not in fs.normalize_for_match(copy), f"{value!r} leaked into UI copy"
        assert needle not in normalized_source, f"{value!r} appears in the demo source"


def test_no_recall_numbers_in_ui_copy():
    """14-UI-SPEC's claim rules: no recall rate in the UI, ever.

    Copy carrying a measured rate goes stale the moment the harness is re-run and overclaims the
    moment it is not. The header points at ``results/phase14_recall_report.md`` instead, which
    carries taught vs never-seen rates and every failure. Only the four FIXED structural numbers
    the spec allows may appear, so they are removed before the check rather than special-cased
    inside it.
    """
    allowed = ("13.9M", "331,776", "1.35 MB", "36")
    for copy in _UI_COPY:
        stripped = copy
        for literal in allowed:
            stripped = stripped.replace(literal, "")
        assert "%" not in stripped, f"a percentage appears in UI copy: {copy!r}"
        assert not re.search(r"\d+\.\d+", stripped), f"a measured fraction appears in: {copy!r}"


def test_budget_import_is_an_integer():
    """14-UI-SPEC: the demo IMPORTS the budget integer and never re-derives it.

    Re-deriving would require the locked fact values in this process — the census
    ``derive_recall_budget`` consumes — which is exactly the clean-room posture's prohibition.

    Deliberately ``==`` and not ``is`` (W-09): ``spec_from_file_location`` produces separate
    module objects, and CPython interns small ints, so an ``is`` check on a ~48-valued integer
    would be True no matter how it was derived — it would assert nothing. The source-absence
    check below is the assertion doing the real work.
    """
    assert pd.RECALL_MAX_NEW_TOKENS == pr.RECALL_MAX_NEW_TOKENS
    assert isinstance(pd.RECALL_MAX_NEW_TOKENS, int)
    assert not isinstance(pd.RECALL_MAX_NEW_TOKENS, bool)
    assert pd.RECALL_MAX_NEW_TOKENS > 0
    assert "derive_recall_budget" not in _DEMO_SOURCE
    # The slider floors AND defaults at the imported integer, so the demo's opening UI state IS
    # the measured condition.
    assert "minimum=RECALL_MAX_NEW_TOKENS" in inspect.getsource(pd.build_demo)
    assert "value=RECALL_MAX_NEW_TOKENS" in inspect.getsource(pd.build_demo)


def test_demo_process_is_fact_free():
    """The only check that can see a TRANSITIVE leak (W-08 / 14-05 ``<import_topology>``).

    The source grep and the UI-copy scan above are both blind to an indirect import: a fact
    value reaching this process through ``phase14_recall`` -> ``teach_persona`` ->
    the fact set would leave the demo's own source spotless. The clean-room posture is that the
    fact strings never enter this process by ANY path, so the check is on ``sys.modules``.

    Both names are POPPED first and restored afterwards, because
    ``tests/test_phase14_teaching.py`` loads ``teach_persona`` at collection time and would
    otherwise seed the very entries this test measures — the
    ``tests/test_phase14_scoring.py::test_no_fact_strings_at_import`` precedent.
    """
    saved = {
        name: sys.modules.pop(name)
        for name in ("phase14_factset", "teach_persona")
        if name in sys.modules
    }
    try:
        _load("personalize_demo", "personalize_demo.py")
        assert "phase14_factset" not in sys.modules
        assert "teach_persona" not in sys.modules
    finally:
        sys.modules.update(saved)


# --------------------------------------------------------------------------- #
# D-17 — the freeze itself
# --------------------------------------------------------------------------- #


def test_demo_app_frozen():
    """D-17: ``scripts/demo_app.py`` is unchanged, held by a PERMANENT test (W-05).

    The execution-time ``git diff --quiet -- <path>`` used elsewhere compares the WORKING TREE
    to the index, so a staged edit passes it and nothing survives the phase. This is the repo's
    existing stronger form (``tests/test_phase13_driver.py:112-123``): a diff against a pinned
    commit, re-run on every CI run, which catches a staged edit and outlives the phase that
    made the decision.
    """
    diff = subprocess.run(
        ["git", "diff", _DEMO_APP_SHA, "HEAD", "--", "scripts/demo_app.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert diff.stdout == "", f"scripts/demo_app.py changed since {_DEMO_APP_SHA} (D-17)"


# --------------------------------------------------------------------------- #
# Local-only: the two assertions that genuinely need gitignored checkpoints
# --------------------------------------------------------------------------- #


# local-only: this is D-17's LITERAL form — the two masks captured inside each real
# build_demo() — and it cannot run in CI because checkpoints/ is gitignored (.gitignore:14).
@pytest.mark.skipif(not _HAVE_REAL_ARTIFACTS, reason="real checkpoints absent (gitignored in CI)")
def test_forbid_ids_parity_real_artifacts():
    """Build BOTH real demos and compare the masks each one actually captured."""
    demo_app = _load("demo_app", "demo_app.py")

    mine = _captured_forbid_ids(pd.build_demo())
    theirs = _captured_forbid_ids(demo_app.build_demo())

    assert mine is not None and theirs is not None, "neither demo captured a forbid_ids mask"
    assert torch.equal(mine, theirs)


# local-only: 14-UI-SPEC's literal contract test. build_demo() loads two checkpoints, so it
# cannot run in CI for the same reason — checkpoints/ is gitignored (.gitignore:14).
@pytest.mark.skipif(not _HAVE_REAL_ARTIFACTS, reason="real checkpoints absent (gitignored in CI)")
def test_build_demo_stylesheets_real():
    """The served page carries zero remote stylesheets — asserted on the real built demo."""
    assert pd.build_demo().stylesheets == []


def _captured_forbid_ids(demo):
    """Recover the ``forbid_ids`` tensor a built demo closed over, whatever its UI shape.

    Both scripts capture the mask as a build-time local and close over it inside their callback,
    so the tensor exists nowhere else once ``build_demo()`` returns. The two UI shapes hide it at
    different depths, which is exactly why this walks rather than indexes: ``gr.Blocks`` registers
    the callback directly, while ``gr.ChatInterface`` wraps the user function in its own
    ``_submit_fn`` and keeps the original on the interface object. Both roots are seeded below and
    closures are followed transitively.
    """
    seen = set()
    queue = [getattr(demo, "fn", None)]
    queue += [getattr(f, "fn", None) for f in getattr(demo, "fns", {}).values()]
    while queue:
        target = queue.pop()
        if target is None or id(target) in seen:
            continue
        seen.add(id(target))
        for cell in getattr(target, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:  # pragma: no cover - an empty cell, nothing to inspect
                continue
            if isinstance(value, torch.Tensor) and value.dtype == torch.bool:
                return value
            if callable(value):
                queue.append(value)
            bound_to = getattr(value, "__self__", None)  # a bound method -> its interface object
            if bound_to is not None:
                queue.append(getattr(bound_to, "fn", None))
    return None
