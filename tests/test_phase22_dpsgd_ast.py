"""Phase 22 — D-05 axis 1: what the DP step CAN reach between the noise write and ``step()``.

V-11. Read off the AST as a transitive closure over the DP step's own call graph, **because the
property is about what the step CAN reach and not about what today's body happens to call**. A
runtime check on today's inputs cannot see the future edit that inserts a ``.backward()``, a
``.grad`` write, a renormalisation, a second clip constant or an in-step re-seed — and D-17's
table says those last two are exactly what the remaining two fakes require, because both are
POSITIVE CODE INSERTIONS.

**Every guard here takes SOURCE TEXT, never a path, and that is the whole design.** Every AST guard
already in this repo reads a fixed committed path (``_EXTRACTION_PATH``, ``PLOT_SCRIPT``,
``_GATE_MODULES``) and therefore cannot be pointed at the mutated source that FAKE 2's and FAKE 4's
positive controls (V-19, V-21) must feed it. ``tests/test_phase20_prereg.py:153-155`` states the
rule this satisfies: *a guard proved correct in a scratch repository and a guard running against
this one must be the SAME code, or the proof is about a different function than the one CI runs.*
So the live check (plan 22-04 Task 2, which passes the mechanism module's own bytes) and the fake
probes (plan 22-09, which pass a mutated string) execute identical code.

**A guard nobody has watched fail is a guard nobody has verified.** The self-tests below are that
watching, in-process and committed rather than recorded in a plan SUMMARY: six distinct RED inputs
and both meta-guards, each observed raising. Every RED source differs from the GREEN baseline by
exactly ONE line, so a failure is attributable to the mutation rather than to two different
fixtures.

Other test modules consume these helpers directly::

    _ROOT = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_ROOT / "tests"))

    from test_phase22_dpsgd_ast import (  # noqa: E402  (tests/ is not a package)
        _assert_no_forbidden_between_noise_and_step,
        _assert_single_clip_constant,
    )

Plan 22-04 appended the LIVE half at the bottom of this file: the same functions the synthetic
probes above exercise, fed ``src/personacore/privacy/dpsgd.py``'s real bytes. That is
``tests/test_phase20_prereg.py:153-155``'s rule — *a guard proved correct in a scratch repository
and a guard running against this one must be the SAME code, or the proof is about a different
function than the one CI runs.*

CPU-only, GPU-free, no torch, no network.
"""

import ast
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# V-25's site A. The pin is READ by a test and never imported by `src/`: `scripts/` is not a
# package and the pre-registration import ceiling runs ONE WAY (D-10). A test is the sanctioned
# reader — `scripts/mitigation_accountant.py::SENSITIVITY_MULTIPLIER_REASON` says so in the frozen
# file itself. Idempotence guard per tests/test_phase22_accountant.py's shape.
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mitigation_accountant  # noqa: E402  (needs the sys.path insert above)

# The D-05 axis-1 token set, widened by D-17 to catch FAKE 4's in-step re-seed. Four families:
# gradient recomputation (`backward`), renormalisation after the noise (`clip_grad_norm_`,
# `clip_grad_value_`, `normalize`, `renorm`), and RNG re-seeding (`manual_seed`, `seed`,
# `set_rng_state`, `initial_seed`). The `.grad`-Store half is NOT a call and is detected
# structurally by the closure walk itself.
_FORBIDDEN_BETWEEN_NOISE_AND_STEP = frozenset(
    {
        "backward",
        "clip_grad_norm_",
        "clip_grad_value_",
        "normalize",
        "renorm",
        "manual_seed",
        "seed",
        "set_rng_state",
        "initial_seed",
    }
)

# Class-body numeric constants the mechanism is allowed to carry. DELIBERATELY EMPTY: a future
# plan that adds one adds its name here IN THE SAME COMMIT as the constant, which is
# `tests/test_phase14_scoring.py:539-543`'s allowlist discipline. An entry pre-added ahead of its
# constant is an exemption granted to code that does not exist.
_ALLOWED_CLASS_CONSTANTS = frozenset()


def _is_self_attr(node):
    """``True`` for a ``self.<attr>`` expression, whatever its context."""
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _forbidden_calls_reachable_from(source_text, *, entry, forbidden):
    """``{function: sorted(hits)}`` over the transitive closure of ``entry``'s call graph.

    Takes TEXT. See the module docstring for why that is load-bearing rather than convenient.

    A hit is either a call whose callee name is in ``forbidden`` — matched on ``func.id`` OR
    ``func.attr``, so ``normalize(...)``, ``torch.nn.utils.clip_grad_norm_(...)`` and
    ``self._g.manual_seed(...)`` all count — or a ``.grad`` attribute in a **Store** context,
    which is the ``.grad``-write half and is not a call at all.

    The frontier also traverses into an ``ast.Attribute`` callee (``self._helper(...)``), which
    ``tests/test_phase18_docs.py:665``'s ``ast.Name``-only walk does not. Without that arm a
    method-based mechanism closes after ONE hop and the guard is blind to anything a helper does:
    the `id`-or-`attr` match is `tests/test_phase14_scoring.py:506`'s, adopted here for exactly
    that reason. (A consequence worth naming: ``optimizer.step()`` matches a method also called
    ``step``, so the entry re-enters its own frontier — harmless, because ``seen`` absorbs it.)

    Both meta-guards are ``assert``s inside this function rather than in its callers, so every
    consumer inherits them and none can forget one.
    """
    tree = ast.parse(source_text)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert entry in functions, (
        f"{entry} is gone — this guard would check nothing. The closure is seeded at {entry}, so "
        f"a rename makes every assertion below green over an empty walk "
        f"(found: {sorted(functions)})"
    )

    seen, frontier, hits = set(), [entry], {}
    while frontier:
        name = frontier.pop()
        if name in seen or name not in functions:
            continue
        seen.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call):
                callee = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if callee is not None:
                    frontier.append(callee)
                    if callee in forbidden:
                        hits.setdefault(name, []).append(callee)
            elif isinstance(node, ast.Attribute) and node.attr == "grad":
                if isinstance(node.ctx, ast.Store):
                    hits.setdefault(name, []).append(".grad=")

    assert len(seen) > 1, (
        f"the closure over {entry} found only {seen} — the walk broke. A closure that stops at "
        "its own entry reports no offenders no matter what the rest of the module does"
    )
    return {name: sorted(hit) for name, hit in hits.items() if hit}


def _assert_no_forbidden_between_noise_and_step(source_text, *, entry):
    """D-05 axis 1: nothing recomputes, rewrites, renormalises or re-seeds after the noise.

    D-03's surviving rule, and its basis is NOT that DP requires it — DP is closed under
    post-processing, so epsilon survives ``clip_grad_norm_`` and AdamW's own per-parameter rescale
    by sqrt(v); an absolute "nothing re-normalises after noise" rule would forbid the optimizer.
    The rule that survives contact is *nothing between the noise and* ``optimizer.step()``, and it
    stands on auditability: a renormalisation over the MIXED buffer makes the released private
    magnitude a function of PUBLIC data, and — measured — it erases exactly the signal the
    wrong-sensitivity positive control detects, so that fake would converge AND pass.
    """
    offenders = _forbidden_calls_reachable_from(
        source_text, entry=entry, forbidden=_FORBIDDEN_BETWEEN_NOISE_AND_STEP
    )
    # HARD EQUALITY against the empty dict. Never `in`, never a subset relation: a membership
    # check is the guard getting weaker while looking bigger
    # (tests/test_phase14_scoring.py:554-555).
    assert offenders == {}, (
        f"functions reachable from {entry} reach forbidden tokens: {offenders}. Between the noise "
        "write and optimizer.step() there may be no .backward(), no .grad write, no clip/normalize "
        "and no re-seed — the first two would recompute or overwrite the released noised sum, the "
        "third makes its magnitude a function of public data, and the fourth is FAKE 4 itself"
    )


def _assert_single_clip_constant(source_text, *, class_name, allowed_attr):
    """D-17/FAKE 2's structural half: exactly ONE ``self.<attr>`` is used as a clip.

    "Looks like a clip constant" is a DECIDABLE AST rule here, not a judgement call:

    **Scope** — the method whose body contains an ``ast.BinOp(op=ast.Div)`` whose LEFT operand is
    a ``self.<attr>`` read. That is ``self.C / norm``, unique to the per-record clip. **The
    narrowness is load-bearing.** A broader "an ``ast.Compare`` OR a ``self.<attr>`` division"
    locator also matches a ``finalize``-style method, whose D-16 invariants mandate
    ``self._writes == len(self._params)`` and a ``self._prev_gen_state is not None`` guard: two
    matching methods make the rule undecidable, and a locator that unions across them yields
    ``{"C", "_writes", "_prev_gen_state"}`` — reddening the hard equality below ON CORRECT CODE.
    If a future edit ever puts a ``self.<attr> / ...`` division in a second method, do NOT widen
    the allow-set to recover; pass the method name explicitly, so the scope stays exact rather
    than the membership growing.

    **Not the noise-bearing method**, either: ``std = self.sigma * self.C`` has TWO legitimate
    ``self`` operands, so any predicate scoped there can never equal ``{"C"}``. That product has
    its own dedicated guard (V-25 requires a two-operand ``Mult`` over ``self.sigma`` and
    ``self.C`` with no ``Constant`` operand), so scoping this one to the clip leaves no gap.

    **Membership** — a ``self.<attr>`` read is clip-bearing iff the ``ast.Attribute`` node is a
    DIRECT operand of an ``ast.Compare`` (its ``left`` or one of its ``comparators``) or a DIRECT
    operand of an ``ast.BinOp`` whose op is ``ast.Div``. *Direct* means the ``Attribute`` IS the
    operand, not nested inside another expression. So
    ``coef = 1.0 if norm <= self.C else self.C / norm`` contributes ``{"C"}``;
    ``norm <= self.C * (1 + self.sensitivity_tolerance)`` contributes nothing (the comparator is
    the ``Mult``, not either attribute); and ``self._clip_bind_count += 1`` contributes nothing at
    all. An assigned-but-never-read ``self._c2 = 0.5`` clips nothing and does not trip this — a
    guard that reddened on it would also redden on ``self._writes = 0``.

    **Assertion** — hard equality, never a subset. An EMPTY set fails it too, so a collapsed scope
    reddens rather than passing over nothing.
    """
    tree = ast.parse(source_text)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert class_name in classes, (
        f"{class_name} is gone — this guard would check nothing (found: {sorted(classes)})"
    )
    class_node = classes[class_name]

    scoped = []
    for node in ast.walk(class_node):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(
            isinstance(inner, ast.BinOp)
            and isinstance(inner.op, ast.Div)
            and _is_self_attr(inner.left)
            for inner in ast.walk(node)
        ):
            scoped.append(node)
    assert len(scoped) == 1, (
        f"expected exactly ONE clip-bearing method in {class_name} (the one dividing a "
        f"self.<attr> by a norm), found {[node.name for node in scoped]}. Zero means the "
        "per-record clip is gone or was rewritten past this locator; two or more means the scope "
        "is undecidable — pass the method name explicitly rather than widening the membership rule"
    )

    clip_bearing = set()
    for node in ast.walk(scoped[0]):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            operands = [node.left, node.right]
        else:
            continue
        clip_bearing.update(operand.attr for operand in operands if _is_self_attr(operand))

    assert clip_bearing == {allowed_attr}, (
        f"{class_name}.{scoped[0].name} treats {sorted(clip_bearing)} as clip constants, not "
        f"exactly {{{allowed_attr!r}}}. D-17 makes the wrong-sensitivity fake impossible by giving "
        "the mechanism ONE clip constant captured in __init__ and read everywhere; a second one is "
        "FAKE 2, and it is the insertion that lets the code clip to one bound while the accountant "
        "is told another"
    )

    class_constants = set()
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign) or not isinstance(stmt.value, ast.Constant):
            continue
        if isinstance(stmt.value.value, bool) or not isinstance(stmt.value.value, (int, float)):
            continue
        class_constants.update(
            target.id
            for target in stmt.targets
            if isinstance(target, ast.Name) and target.id not in _ALLOWED_CLASS_CONSTANTS
        )
    assert class_constants == set(), (
        f"{class_name} carries class-body numeric constants {sorted(class_constants)} outside "
        f"_ALLOWED_CLASS_CONSTANTS {sorted(_ALLOWED_CLASS_CONSTANTS)}. A class attribute is a "
        "second source of truth that __init__'s single capture cannot see, so it is the same fake "
        "arriving one scope higher"
    )


# The call whose name identifies a Gaussian draw. Matched on `func.id` OR `func.attr` for the
# reason `_forbidden_calls_reachable_from` gives: a dotted-path match is blind to
# `from torch import normal` and to any aliasing.
_NOISE_CALL = "normal"


def _called_names(node):
    """Every callee name reachable syntactically inside ``node`` (``id`` or ``attr``)."""
    return {
        getattr(call.func, "id", None) or getattr(call.func, "attr", None)
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
    }


def _divides_by(node, divisor):
    """``True`` when ``node`` contains a ``BinOp(Div)`` whose RIGHT operand is ``Name(divisor)``."""
    return any(
        isinstance(inner, ast.BinOp)
        and isinstance(inner.op, ast.Div)
        and isinstance(inner.right, ast.Name)
        and inner.right.id == divisor
        for inner in ast.walk(node)
    )


def _assert_noise_precedes_divide(source_text, *, class_name, divisor="accum"):
    """D-02/FAKE 3's STRUCTURAL half: the draw is a statement EARLIER than the ``/N``.

    This is the detector that catches *noise added after averaging* where the runtime differential
    structurally cannot: at ``sigma = 0`` the drawn values are exact zeros, so ``(S + 0)/N`` and
    ``(S/N) + 0`` are the same bytes, and at ``N = 1`` the divide is a no-op at every sigma.
    Statement ORDER is observable at both. (22-06 measured the sigma-of-zero half and 22-11 measured
    the ``N = 1`` half; D-17's table credits the sigma-of-zero identity with detecting FAKE 3 and
    that row is FALSE — see ``tests/test_phase22_fakes.py::test_fake_noise_after_averaging``.)

    **The plan text asked for ``method="finalize"`` and that is UNSATISFIABLE against the shipped
    module**, which is why this takes no method name and LOCATES one instead. Measured against
    ``dpsgd.py``: ``finalize``'s body contains neither a ``torch.normal`` call nor any division —
    it delegates to ``_noised_private``, which owns both. A guard scoped to ``finalize`` would find
    zero of each and pass over nothing.

    **Scope** — the method that takes a parameter named ``divisor`` AND contains a ``BinOp(Div)``
    whose RIGHT operand is a ``Name`` load of it. Hard-asserted to be exactly ONE, so a collapsed
    or duplicated scope reddens rather than passing over the wrong body.

    **The noise statement** — the first top-level statement of that method whose subtree calls a
    NOISE PRODUCER. Producers are derived from the class rather than hard-coded: ``normal`` itself,
    plus every method of the class whose own body calls it (which resolves ``self._draw_noise()``,
    one hop). Meta-guarded to be more than ``{"normal"}`` alone, so a walk that stopped finding
    ``normal`` cannot report a vacuous pass.

    **Assertion** — ``noise_index < divide_index``, strictly. Equality is refused too: a single
    statement doing both (``[(buf / accum) + drawn ...]``) is FAKE 3 written on one line.
    """
    tree = ast.parse(source_text)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert class_name in classes, (
        f"{class_name} is gone — this guard would check nothing (found: {sorted(classes)})"
    )
    methods = {
        node.name: node
        for node in ast.walk(classes[class_name])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    producers = {_NOISE_CALL} | {
        name for name, node in methods.items() if _NOISE_CALL in _called_names(node)
    }
    # META-GUARD: some method really does call `normal`, so an "index not found" below means the
    # statement is absent rather than that the walk never recognised a draw at all.
    assert producers != {_NOISE_CALL}, (
        f"no method of {class_name} calls {_NOISE_CALL!r}, so the noise producer set is just "
        f"{sorted(producers)} and this guard would be looking for a statement that cannot exist"
    )

    scoped = [
        node
        for node in methods.values()
        if divisor in {arg.arg for arg in node.args.args + node.args.kwonlyargs}
        and _divides_by(node, divisor)
    ]
    assert len(scoped) == 1, (
        f"expected exactly ONE method of {class_name} dividing by its own {divisor!r} parameter, "
        f"found {[node.name for node in scoped]}. Zero means D-02's '/N LAST' divide is gone or "
        "was rewritten past this locator; two or more means the order rule is being asserted about "
        "an ambiguous body"
    )
    method = scoped[0]

    noise_index = next(
        (i for i, stmt in enumerate(method.body) if _called_names(stmt) & producers), None
    )
    divide_index = next(
        (i for i, stmt in enumerate(method.body) if _divides_by(stmt, divisor)), None
    )
    assert noise_index is not None, (
        f"{class_name}.{method.name} divides by {divisor!r} but no statement in it reaches a noise "
        f"producer {sorted(producers)} — the draw left the method that owns the divide, so their "
        "relative order is no longer checkable here"
    )
    assert divide_index is not None, (
        f"{class_name}.{method.name} was located as the divide-bearing method but no top-level "
        f"statement divides by {divisor!r} — the locator and the index walk disagree"
    )
    assert noise_index < divide_index, (
        f"{class_name}.{method.name} draws the noise at statement {noise_index} and divides by "
        f"{divisor!r} at statement {divide_index}. D-02 puts the /N LAST: the noise is added to "
        "the SUM, because one record moves the SUM by at most C and that is the sensitivity the "
        "accountant is told. Dividing first releases noise N times too large for that sensitivity "
        "— FAKE 3, and it is INVISIBLE at sigma = 0 (the draw is exact zeros) and at N = 1 (the "
        "divide is a no-op), which is why the order is pinned structurally as well as by magnitude"
    )


# =============================================================================================
# The synthetic sources. ONE template, so every RED input differs from GREEN by exactly one line
# and a failure is attributable to the mutation rather than to two different fixtures — the
# one-kwarg-apart discipline of tests/test_phase21_replay_volume.py's negative control, applied
# to source text. Names like `torch` and `_global_norm` are never resolved: these strings are
# parsed, never executed.
# =============================================================================================
_TEMPLATE = """
class DPStep:
    def __init__(self, sigma, clip_norm, generator, params):
        self.sigma = sigma
        self.C = clip_norm  # SINGLE source of truth — the clip AND the noise std read this.
        self._g = generator
        self._params = params
        self._accum = {{p: 0.0 for p in params}}
        self._writes = 0
        self._records = 0
        self._clip_bind_count = 0
        self._prev_gen_state = None
{init_extra}
    def absorb_record(self, params):
        norm = _global_norm(params)
        coef = 1.0 if norm <= self.C else self.C / norm
{clip_extra}
        self._clip_bind_count += 1
        for p in params:
            self._accum[p] += p.grad.detach() * coef
            p.grad = None

    def _noise(self, params):
        for p in params:
            std = self.sigma * self.C
            self._accum[p] += torch.normal(0.0, std, size=p.shape, generator=self._g)

    def step(self, params, optimizer):
        self._noise(params)
{step_extra}
        optimizer.step()

    def finalize(self, params):
        if self._writes != len(self._params):
            raise RuntimeError("the single-write count did not match the parameter count")
        if self._prev_gen_state is None:
            raise RuntimeError("the generator state was never captured")
        return self._records
{method_extra}
"""


def _source(*, init_extra="", clip_extra="", step_extra="", method_extra=""):
    return _TEMPLATE.format(
        init_extra=init_extra,
        clip_extra=clip_extra,
        step_extra=step_extra,
        method_extra=method_extra,
    )


GREEN = _source()


def test_green_baseline_passes_every_guard():
    """The correct mechanism is GREEN under all three guards — the half a RED-only suite skips.

    ``absorb_record`` writes ``p.grad = None`` (D-01's per-micro-step drain, a ``.grad`` Store)
    and is NOT reachable from ``step``, which is the point: the drain is legitimate where it
    lives, and the guard's claim is scoped to what the step can reach after the noise.
    ``finalize``'s two D-16 invariants are the methods the clip-constant locator must NOT select.
    """
    _assert_no_forbidden_between_noise_and_step(GREEN, entry="step")
    _assert_single_clip_constant(GREEN, class_name="DPStep", allowed_attr="C")


@pytest.mark.parametrize(
    ("token", "line"),
    [
        ("backward", "        loss.backward()"),
        ("clip_grad_norm_", "        torch.nn.utils.clip_grad_norm_(params, 1.0)"),
        ("normalize", "        normalize(params)"),
        ("manual_seed", "        self._g.manual_seed(1234)"),
    ],
)
def test_forbidden_token_between_noise_and_step_reddens(token, line):
    """One RED input per forbidden family, each one line away from GREEN.

    ``normalize(...)`` is a bare ``ast.Name`` callee; the other three are ``ast.Attribute``
    callees at one, three and two levels of dotting. All four must be caught, or the guard only
    sees the call shape someone happened to write first.
    """
    with pytest.raises(AssertionError, match="forbidden tokens"):
        _assert_no_forbidden_between_noise_and_step(_source(step_extra=line), entry="step")


def test_grad_store_between_noise_and_step_reddens():
    """The ``.grad``-write half — NOT a call, so a call-only walk would miss it entirely.

    An assignment to ``.grad`` after the noise overwrites the released noised sum with something
    the accountant never charged for. It is detected as an ``ast.Attribute`` in a **Store**
    context, which is why ``absorb_record``'s legitimate ``p.grad.detach()`` READ in the same
    template does not trip anything.
    """
    with pytest.raises(AssertionError, match=r"\.grad="):
        _assert_no_forbidden_between_noise_and_step(
            _source(step_extra="        params[0].grad = self._accum[params[0]]"), entry="step"
        )


def test_closure_follows_an_attribute_callee():
    """FAKE-hiding via a helper: ``self._helper()`` whose body calls ``backward``.

    This is the case that passes if the ``attr`` arm of the frontier is dropped — the closure
    would stop at ``step``, never enter ``_helper``, and report no offenders while the module
    recomputes gradients after the noise. It is also the exact limitation
    ``tests/test_phase18_docs.py``'s ``ast.Name``-only walk has, inherited deliberately here as a
    test rather than as a caveat.
    """
    hidden = _source(
        step_extra="        self._helper(loss)",
        method_extra="\n    def _helper(self, loss):\n        loss.backward()\n",
    )
    # The mutation is only meaningful if the helper is genuinely reached: assert the offender is
    # attributed to _helper, not to step, so a guard that flagged the call site by name would fail.
    with pytest.raises(AssertionError, match="_helper"):
        _assert_no_forbidden_between_noise_and_step(hidden, entry="step")


def test_second_clip_constant_reddens():
    """FAKE 2's structural half: a second ``self.<attr>`` USED as a clip.

    The mutation both assigns ``self._c2`` and divides by it inside the clip-bearing method, so
    the clip-bearing set becomes ``{"C", "_c2"}``. That is the insertion D-17 leaves as the only
    route to a wrong sensitivity, and it is invisible to a runtime magnitude check that compares
    the code's own constant against itself.
    """
    with pytest.raises(AssertionError, match="clip constants"):
        _assert_single_clip_constant(
            _source(
                init_extra="        self._c2 = 0.5",
                clip_extra="        coef = self._c2 / norm",
            ),
            class_name="DPStep",
            allowed_attr="C",
        )


def test_assigned_but_unread_constant_does_not_redden():
    """The negative half: a bare ``self._c2 = 0.5`` that nothing reads clips NOTHING.

    Deliberate, not an oversight. A guard that reddened on an assigned-but-unused float would
    also redden on the template's own ``self._writes = 0``, ``self._records = 0`` and
    ``self._clip_bind_count = 0`` — three D-16 counters — making the guard unusable on correct
    code and, predictably, the first thing a future plan would weaken to a subset check.
    """
    _assert_single_clip_constant(
        _source(init_extra="        self._c2 = 0.5"), class_name="DPStep", allowed_attr="C"
    )


def test_meta_guards_bite():
    """Both meta-guards, each with its own failing input. Neither has ever been merely read.

    A closure guard has two ways to be green over nothing — the entry point renamed away, and a
    walk that collapses to its own seed — and both leave every offender assertion trivially
    satisfied. ``tests/test_phase15_plots.py:326`` and ``tests/test_phase18_docs.py:656`` name the
    same two; here each gets an input that provokes it, so the guard's bite is a test result
    rather than a claim.
    """
    with pytest.raises(AssertionError, match="would check nothing"):
        _assert_no_forbidden_between_noise_and_step(
            "class DPStep:\n    def apply(self):\n        pass\n", entry="step"
        )

    with pytest.raises(AssertionError, match="the walk broke"):
        _assert_no_forbidden_between_noise_and_step(
            "class DPStep:\n    def step(self):\n        x = 1\n        return x\n", entry="step"
        )

    with pytest.raises(AssertionError, match="would check nothing"):
        _assert_single_clip_constant(GREEN, class_name="NotAClass", allowed_attr="C")


# =============================================================================================
# THE LIVE HALF (plan 22-04). Everything below feeds the REAL bytes of
# `src/personacore/privacy/dpsgd.py` into the SAME functions the six synthetic mutations above
# were watched biting. Nothing here re-implements a helper: `tests/test_phase20_prereg.py:153-155`
# — *a guard proved correct in a scratch repository and a guard running against this one must be
# the SAME code, or the proof is about a different function than the one CI runs.*
# =============================================================================================

_DPSGD_PATH = _ROOT / "src" / "personacore" / "privacy" / "dpsgd.py"


def _dpsgd_source():
    """The mechanism's own bytes, behind the meta-guard an emptied or renamed module fails."""
    source = _DPSGD_PATH.read_text(encoding="utf-8")
    assert source.strip(), f"{_DPSGD_PATH} is empty — every guard below would pass over no source"
    assert "class DPSGD" in source, (
        f"{_DPSGD_PATH} no longer defines `class DPSGD`. Without this meta-guard a renamed class "
        "would make the clip-constant guard's own 'is gone' assertion the only thing standing "
        "between a rewritten mechanism and a green suite"
    )
    return source


# The two `.grad` writes the mechanism is ALLOWED to make, as a hard-equality allowlist per entry.
#
# WHY THIS IS NOT `_assert_no_forbidden_between_noise_and_step(..., entry="finalize")`, recorded
# because the plan text asked for exactly that and it is UNSATISFIABLE ON CORRECT CODE. The
# wrapper asserts `offenders == {}`, and a `.grad` Store is an offender. But the mechanism has two
# `.grad` Stores BY CONSTRUCTION and both are mandated by the same decisions the guard exists to
# protect: D-01's per-micro-step drain (`p.grad = None` in `absorb_record`, without which record
# i's clip sees records 1..i summed) and D-01's SINGLE combining write (`p.grad = private` in
# `_write_once`, which IS the release). Measured against the shipped module, the wrapper reports
# `{'absorb_record': ['.grad=']}` and `{'_write_once': ['.grad=']}` respectively.
#
# So `== {}` at those entries could only be reached by contorting the mechanism to hide its own
# release write, or by scoping the guard to a method that structurally cannot write `.grad` — the
# guard getting weaker while looking bigger. A hard-equality ALLOWLIST is strictly stronger than
# `== {}` over a hand-picked scope: it pins WHICH function writes `.grad`, HOW MANY writes it is
# credited with, and that nothing else reachable from the entry writes one or reaches any
# forbidden token. A third write, a write moved into a helper, or any `backward` / `clip_grad_norm_`
# / `normalize` / `manual_seed` anywhere in the closure all redden it.
#
# The wrapper itself still runs live, at `_noised_private` — the noise-bearing method — where
# `== {}` is both satisfiable and exactly the D-05 axis-1 claim: from the draw through the divide,
# nothing recomputes, renormalises, re-seeds or writes `.grad`.
_ALLOWED_GRAD_WRITES = {
    "absorb_record": {"absorb_record": [".grad="]},
    "finalize": {"_write_once": [".grad="]},
}


@pytest.mark.parametrize("entry", sorted(_ALLOWED_GRAD_WRITES))
def test_dpsgd_step_reaches_no_forbidden_call(entry):
    """V-11 live: the ONLY thing the step path reaches is its own two mandated ``.grad`` writes."""
    offenders = _forbidden_calls_reachable_from(
        _dpsgd_source(), entry=entry, forbidden=_FORBIDDEN_BETWEEN_NOISE_AND_STEP
    )
    # HARD EQUALITY, never `in` and never a subset (tests/test_phase14_scoring.py:554-555).
    assert offenders == _ALLOWED_GRAD_WRITES[entry], (
        f"functions reachable from DPSGD.{entry} reach {offenders}, not exactly "
        f"{_ALLOWED_GRAD_WRITES[entry]}. Between the noise write and optimizer.step() there may "
        "be no .backward(), no clip/normalize and no re-seed, and the ONLY .grad writes in the "
        "whole mechanism are D-01's per-micro-step drain and D-01's single combining write"
    )


def test_dpsgd_noise_path_reaches_no_forbidden_call():
    """The wrapper itself, live: from the noise draw through the divide, ``offenders == {}``."""
    _assert_no_forbidden_between_noise_and_step(_dpsgd_source(), entry="_noised_private")


def test_dpsgd_has_exactly_one_clip_constant():
    """V-11 live / FAKE 2: the clip-bearing set in the mechanism's own bytes is exactly ``{"C"}``.

    ``_ALLOWED_CLASS_CONSTANTS`` was NOT widened for this module and the guard's clip-operand
    predicate was NOT touched. ``self._clip_bind_count`` appears only as an assignment target — an
    ``ast.Assign`` in ``__init__`` and an ``ast.AugAssign`` in ``absorb_record`` — and never as a
    direct operand of a comparison or a division, which is the half the pinned predicate turns on.
    Measured against the shipped module: the clip-bearing set is ``{"C"}`` and the class body
    carries no numeric constants at all.
    """
    _assert_single_clip_constant(_dpsgd_source(), class_name="DPSGD", allowed_attr="C")


def test_dpsgd_draws_the_noise_before_it_divides():
    """D-02 live / FAKE 3: the draw is a strictly earlier statement than the ``/accum``.

    Measured against the shipped module: the divide-bearing method is ``_noised_private``, the
    noise statement is index 3 (``noise = self._draw_noise()``) and the divide is index 7 (the
    ``return``). The RED half — the two statements swapped — is in
    ``tests/test_phase22_fakes.py::test_fake_noise_after_averaging``, fed to THIS function.
    """
    _assert_noise_precedes_divide(_dpsgd_source(), class_name="DPSGD")


_RESEED_CALLS = frozenset({"manual_seed", "seed", "set_state"})

# The methods allowed to touch the generator's seed/state, as a HARD-EQUALITY allowlist naming
# WHICH call each one is credited with — the `_ALLOWED_GRAD_WRITES` discipline, applied to FAKE 4.
#
# WHY THE EXEMPTION LIST WAS WIDENED, recorded rather than granted silently (plan 22-06 (f)).
# `__init__` was the sole exemption because D-17's construct-once seeding lives there. Plan 22-06
# adds `load_noise_rng_state`, whose body IS `self._g.set_state(state)` — FAKE 4's own shape. It is
# not FAKE 4 because of WHERE it is callable from: `training/loop.py::train`'s `resume_from` block
# and tests, never a step method. DPSGD-05 requires it — a write-only `dp_noise_rng` slot means a
# resumed run re-seeds from the caller's seed and REPLAYS noise it already released, which is FAKE 4
# ARRIVING THROUGH PRODUCTION and which D-16 invariant 4 is structurally blind to (`_prev_gen_state`
# is None on a fresh object, so the continuity check is vacuous on the first post-resume step).
#
# A NAME-ONLY exemption would be the guard getting weaker while looking bigger: a future author
# could park a re-seed in a method spelled `load_noise_rng_state` and call it from `finalize`. So
# the exemption ships PAIRED with `test_reseed_exempt_methods_are_unreachable_from_the_step_path`,
# which walks the same closure the `.grad` guards use and asserts no step entry can reach it.
_ALLOWED_RESEED_SITES = {
    "__init__": ["manual_seed"],
    "load_noise_rng_state": ["set_state"],
}

# The public step entries `_optimizer_step` drives between `zero_grad` and `optimizer.step()`:
# `begin_step` -> `absorb_record` -> `finalize`. Only the last two are walked by the closure
# helper — `begin_step` is a LEAF (it calls no DPSGD method at all), and the helper's own
# `len(seen) > 1` meta-guard REFUSES a leaf entry rather than reporting a vacuous "no offenders".
# That refusal is correct and is not worked around: `begin_step` gets the stronger direct
# assertion below, that it is a leaf, which IS its reachability proof.
_STEP_ENTRIES = ("absorb_record", "finalize")
_LEAF_STEP_ENTRY = "begin_step"


def _reseed_sites(source_text):
    """``{method: sorted(calls)}`` per ``DPSGD`` method that touches the generator seed/state."""
    tree = ast.parse(source_text)
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "DPSGD" in classes, f"DPSGD is gone (found: {sorted(classes)})"

    seeding_sites = {}
    for method in ast.walk(classes["DPSGD"]):
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(method):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) in _RESEED_CALLS:
                seeding_sites.setdefault(method.name, []).append(node.func.attr)
    return {name: sorted(calls) for name, calls in seeding_sites.items()}


def test_dpsgd_never_reseeds_its_generator():
    """FAKE 4's structural half: the seed/state calls are EXACTLY the two sanctioned ones.

    HARD EQUALITY against ``_ALLOWED_RESEED_SITES``, never a subset: a third site, a re-seed moved
    into a helper, or an extra call credited to an exempt method all redden this. Every occurrence
    outside those two is FAKE 4's positive insertion — an in-step re-seed makes every step draw the
    same noise vector while the accountant charges for T independent compositions.
    """
    seeding_sites = _reseed_sites(_dpsgd_source())

    # META-GUARD: __init__ must still carry a seeding call, or this walk is green over a
    # mechanism whose construct-once seeding was deleted outright.
    assert seeding_sites.get("__init__"), (
        "no manual_seed/seed/set_state call was found in DPSGD.__init__ — either the walk broke "
        f"or the construct-once seeding is gone (sites found: {seeding_sites})"
    )
    assert seeding_sites == _ALLOWED_RESEED_SITES, (
        f"DPSGD's generator seed/state call sites are {seeding_sites}, not exactly "
        f"{_ALLOWED_RESEED_SITES}. Anything else is FAKE 4's positive insertion — the runtime "
        "generator-continuity invariant catches it on today's inputs, and this catches the FUTURE "
        "edit that a runtime check cannot see"
    )


def test_reseed_exempt_methods_are_unreachable_from_the_step_path():
    """The other half of the exemption: no step entry's call graph can reach a sanctioned re-seed.

    Without this, ``_ALLOWED_RESEED_SITES`` would be a NAME-based pass: a re-seed parked in a
    method spelled ``load_noise_rng_state`` and called from ``finalize`` would satisfy the
    hard-equality guard above while being FAKE 4 verbatim. This walks the SAME closure the
    ``.grad`` guards use — ``_forbidden_calls_reachable_from`` with the exempt method names as the
    forbidden token set — so the exemption is conditional on unreachability, not on spelling.
    """
    source = _dpsgd_source()
    exempt = frozenset(_ALLOWED_RESEED_SITES)

    # `begin_step` is a LEAF, and that is its reachability proof. Asserted directly because the
    # closure helper's `len(seen) > 1` meta-guard refuses a leaf entry outright — correctly, since
    # a walk that stops at its own entry reports no offenders no matter what the module does.
    tree = ast.parse(source)
    methods = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert _LEAF_STEP_ENTRY in methods, f"{_LEAF_STEP_ENTRY} is gone — this guard checks nothing"
    leaf_callees = {
        getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        for node in ast.walk(methods[_LEAF_STEP_ENTRY])
        if isinstance(node, ast.Call)
    }
    assert not (leaf_callees & set(methods)), (
        f"{_LEAF_STEP_ENTRY} is no longer a leaf — it calls {sorted(leaf_callees & set(methods))}. "
        "Add it to _STEP_ENTRIES so the closure walk covers it; the direct leaf assertion here is "
        "only sufficient while it reaches nothing"
    )

    for entry in _STEP_ENTRIES:
        offenders = _forbidden_calls_reachable_from(source, entry=entry, forbidden=exempt)
        # `.grad=` hits are the two writes D-01 mandates and are not what this guard is about;
        # only a call INTO an exempt method counts here.
        reached = {
            name: [hit for hit in hits if hit in exempt]
            for name, hits in offenders.items()
            if any(hit in exempt for hit in hits)
        }
        assert reached == {}, (
            f"DPSGD.{entry}'s call graph reaches a re-seed-exempt method: {reached}. The exemption "
            f"in _ALLOWED_RESEED_SITES is safe ONLY because {sorted(exempt)} are unreachable from "
            "the step path; a call from a step method turns the sanctioned restore into FAKE 4"
        )

    # META-GUARD: the closure really does resolve calls into DPSGD methods, so an empty `reached`
    # above means "unreachable" rather than "the walk never followed a self.<method>() call".
    control = _forbidden_calls_reachable_from(
        source, entry="finalize", forbidden=frozenset({"_write_once", "_noised_private"})
    )
    assert control.get("finalize") == ["_noised_private", "_write_once"], (
        f"the closure from finalize reported {control} for its own two mandated helpers — the "
        "self.<method>() arm of the walk is broken, and the unreachability assertions above are "
        "then vacuous"
    )


def test_dpsgd_has_no_numeric_sigma_or_clip_default():
    """D-08, structurally: ``sigma`` and ``clip_norm`` are keyword-only with EMPTY default slots.

    Python's AST spells "no default" as a ``None`` slot in ``kw_defaults``, so this is an
    assertion about the grammar rather than a grep that a docstring sentence could satisfy.

    Phase 20's Z boundary is the reason: Phase 22 names NO sigma and NO C value anywhere in its
    tree, so there is nothing for Phase 23 to override and nothing to drift. Phase 23 supplies
    both from ``scripts/mitigation_budget.py``.
    """
    tree = ast.parse(_dpsgd_source())
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "DPSGD" in classes, f"DPSGD is gone (found: {sorted(classes)})"
    init = next(
        (
            node
            for node in classes["DPSGD"].body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "__init__"
        ),
        None,
    )
    assert init is not None, "DPSGD.__init__ is gone — this guard would check nothing"

    names = [arg.arg for arg in init.args.kwonlyargs]
    slots = dict(zip(names, init.args.kw_defaults))
    assert len(init.args.kw_defaults) == len(names), "kwonlyargs/kw_defaults are out of step"
    # META-GUARD: some kwonly argument DOES carry a default, so a `None` slot below means "no
    # default" rather than "the parse returned an empty list".
    assert any(slot is not None for slot in init.args.kw_defaults), (
        "no keyword-only argument of DPSGD.__init__ carries a default, so an all-None kw_defaults "
        "list is indistinguishable from a broken parse and the assertion below proves nothing"
    )
    for required in ("sigma", "clip_norm"):
        assert required in slots, (
            f"{required} is not a KEYWORD-ONLY argument of DPSGD.__init__ (kwonlyargs: {names}). "
            "A positional sigma or C can be supplied by accident and by order"
        )
        assert slots[required] is None, (
            f"DPSGD.__init__ gives {required} a default of "
            f"{ast.dump(slots[required])}. D-08: sigma and clip_norm are keyword-only with NO "
            "default, so Phase 22 names no value for either and Phase 20's Z boundary stays "
            "untouched — a default here is a Phase-23 resource parameter smuggled into Phase 22"
        )


# =============================================================================================
# V-25 (plan 22-09, D-18). THE THREE-SITE ADJACENCY CONSISTENCY CHECK.
#
# The definitional half every guard above is structurally blind to. Single-sourcing `self.C`
# proves the code is SELF-CONSISTENT; it does not prove `C` is the RIGHT sensitivity for the
# adjacency the report claims. An implementation can pass all four D-05 axes and all four D-16
# runtime invariants while publishing an epsilon that is 2x optimistic, because every one of those
# guards compares C against C.
#
# NO IMPORT CONNECTS THE THREE SITES and that is forced, not incidental: the `mitigation_*.py`
# ceiling admits only `{pathlib, sys, erasure_gate}`, and `src/` never puts `scripts/` on the
# path. So this is a multi-site SOURCE READ — the same shape D-05 axis 1 already builds.
#
# `scripts/mitigation_accountant.py::SENSITIVITY_MULTIPLIER_REASON` names THIS test by symbol, so
# the name `test_adjacency_relation_consistent` is load-bearing: the pin freezes at the first
# tracked `results/phase23_*` artifact and a frozen file citing a test that does not exist cannot
# be corrected except by a dated continuation.
#
# PROVENANCE, recorded honestly. `.planning/research/PITFALLS.md` P3 already prescribed
# `NEIGHBOURING` and `SENSITIVITY_MULTIPLIER` and assigned them to "P20 (constant), P21
# (accountant consumes it)". Measured against HEAD before this phase,
# `grep -rn "NEIGHBOURING\|SENSITIVITY_MULTIPLIER" scripts/ src/ tests/` returned ZERO hits: both
# phases closed without landing them. This is a carry-forward gap being closed, not a new question.
# =============================================================================================

_ACCOUNTANT_PATH = _ROOT / "src" / "personacore" / "privacy" / "accountant.py"

# The declaration marker every site states its relation with. Matched after normalisation, so
# ``THE ADJACENCY RELATION IS **add/remove one fact**`` and a lowercase unformatted version are
# the same statement to this guard.
_ADJACENCY_MARKER = "the adjacency relation is"

# How much text after the marker counts as the DECLARATION. Measured: at both sites the word
# "replace" first appears 239 characters into the tail — inside the sentence that REJECTS
# replace-one — so a 60-character window reads the relation each site ADOPTS and never the one it
# argues against. That distinction is the whole reason this is a windowed read rather than a
# file-wide substring scan; see test_adjacency_relation_consistent's docstring.
_DECLARATION_WINDOW = 60


def _normalized(text):
    """Lowercased, emphasis-stripped, whitespace-collapsed — one spelling per statement."""
    return " ".join(text.replace("*", " ").replace("`", " ").lower().split())


def _declared_relations(docstring):
    """Every ``the adjacency relation is <...>`` declaration in a module docstring, normalised."""
    normalized = _normalized(docstring)
    declarations, start = [], 0
    while True:
        found = normalized.find(_ADJACENCY_MARKER, start)
        if found < 0:
            return declarations
        tail = normalized[found + len(_ADJACENCY_MARKER) :].lstrip()
        declarations.append(tail[:_DECLARATION_WINDOW])
        start = found + len(_ADJACENCY_MARKER)


def _module_docstring(source_text, *, label):
    """A module docstring behind the two meta-guards an emptied or docstring-less module fails."""
    assert source_text.strip(), f"{label} is empty — every adjacency assertion would pass over it"
    tree = ast.parse(source_text)
    assert tree.body, f"{label} parses to an EMPTY module body — this guard would check nothing"
    docstring = ast.get_docstring(tree)
    assert docstring and docstring.strip(), (
        f"{label} has no module docstring. The adjacency relation is a DEFINITION, not a code "
        "artifact — the docstring is where this site states it, so a missing one is a site that "
        "states nothing, and absence must never be read as agreement"
    )
    return docstring


def _noise_std_expression(source_text):
    """The ``std=`` keyword expression of the module's ``torch.normal`` call, or ``None``."""
    for node in ast.walk(ast.parse(source_text)):
        if not isinstance(node, ast.Call):
            continue
        if (getattr(node.func, "attr", None) or getattr(node.func, "id", None)) != "normal":
            continue
        for keyword in node.keywords:
            if keyword.arg == "std":
                return keyword.value
    return None


def _assert_adjacency_consistent(*, relation, multiplier, accountant_src, dpsgd_src):
    """V-25's whole comparison, over TEXT, so the RED probes and the live check are ONE function.

    ``tests/test_phase20_prereg.py:153-155``'s rule: a guard proved correct on mutated text and the
    guard CI runs must be the SAME code, or the proof is about a different function than the one
    that runs. The live test passes the real bytes; ``test_adjacency_check_bites`` passes mutated
    ones; both arrive here.

    ``relation`` and ``multiplier`` are VALUES rather than a third source string, because site A is
    a pin whose constants a test reads directly — that is the reader the frozen file's own
    ``SENSITIVITY_MULTIPLIER_REASON`` names. The two ``src/`` sites are text because their
    statements live in prose and in an expression, neither of which is importable.

    ASSERTION ORDER IS LOAD-BEARING: presence at every site FIRST, agreement second. A consistency
    check that reads a missing relation as agreement is the vacuous-guard failure this ordering
    exists to prevent, and it is the same discipline as V-02's ``a != 0.0 and b != 0.0``
    precondition.
    """
    # META-GUARDS. A relation degraded to "" makes every substring check below pass trivially.
    assert len(relation) > 10, (
        f"NEIGHBOURING is {relation!r} — too short to name a relation. A degraded or emptied "
        "relation string makes every containment check below vacuously true"
    )
    assert isinstance(multiplier, float), (
        f"SENSITIVITY_MULTIPLIER is {multiplier!r} ({type(multiplier).__name__}), not a float"
    )
    wanted = _normalized(relation)

    sites = {
        "src/personacore/privacy/accountant.py": _module_docstring(
            accountant_src, label="accountant.py"
        ),
        "src/personacore/privacy/dpsgd.py": _module_docstring(dpsgd_src, label="dpsgd.py"),
    }

    # 1. PRESENCE, each site separately messaged. Absent must never count as agreement.
    declarations = {}
    for label, docstring in sites.items():
        declared = _declared_relations(docstring)
        assert declared, (
            f"{label}'s module docstring contains no '{_ADJACENCY_MARKER} ...' statement. This "
            "site therefore states NO adjacency relation, and a consistency check that treats "
            "silence as agreement is exactly the guard D-18 exists to refuse: the pin would say "
            f"{relation!r} and nothing here would contradict it, including an implementation "
            "built for the other convention"
        )
        declarations[label] = declared

    # 2. AGREEMENT. Every declaration at every site names the relation the pin froze.
    for label, declared in declarations.items():
        for statement in declared:
            assert statement.startswith(wanted), (
                f"{label} declares the adjacency relation as {statement!r}, which does not begin "
                f"with the pinned {relation!r} (scripts/mitigation_accountant.py::NEIGHBOURING). "
                "The relation is a definition; nothing in a training loop records which one was "
                "meant, and papers use both — so the only check available is that the places "
                "STATING it agree"
            )

    # 2b. PITFALLS P3's stated warning sign, VERBATIM: the report says add/remove and the
    # accountant's docstring says replace. Read off the DECLARATION rather than off the file,
    # because all three sites mention replace-one in the sentence that REJECTS it — a file-wide
    # substring scan reddens on correct code and would have to be deleted to ship.
    for label, declared in declarations.items():
        for statement in declared:
            assert not ("replace" in statement and multiplier == 1.0), (
                f"{label} declares {statement!r} while SENSITIVITY_MULTIPLIER is {multiplier!r}. "
                "That pair is PITFALLS P3's warning sign: replace-one is BOUNDED DP with "
                "Delta = 2C, so a multiplier of 1.0 under it halves the noise the accountant "
                "charges for. Each half is internally coherent at one site and wrong across sites"
            )

    # 3. THE MULTIPLIER MATCHES THE CODE, NOT ONLY THE PROSE. `std=` must be exactly
    # `self.sigma * self.C`.
    std_node = _noise_std_expression(dpsgd_src)
    assert std_node is not None, (
        "the noise call is gone — this guard would check nothing. V-25's third assertion is about "
        "the arithmetic of the `std=` argument of `torch.normal`, so a renamed or removed draw "
        "leaves the check green over an expression that no longer exists"
    )
    operands = (
        [std_node.left, std_node.right]
        if isinstance(std_node, ast.BinOp) and isinstance(std_node.op, ast.Mult)
        else []
    )
    attrs = {operand.attr for operand in operands if _is_self_attr(operand)}
    numeric = [
        ast.dump(node)
        for node in ast.walk(std_node)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
    ]
    assert attrs == {"sigma", "C"} and not numeric, (
        f"the noise std is `{ast.unparse(std_node)}` — a {type(std_node).__name__} over "
        f"self attributes {sorted(attrs)} with numeric operands {numeric}. D-18 requires exactly "
        "`self.sigma * self.C`: a two-operand Mult over two `self` attributes with NO numeric "
        "factor. A `2.0 *` here is SENSITIVITY_MULTIPLIER = 2.0 in code while the pin says 1.0, "
        "and since epsilon is roughly linear in mu over the operating range, that is roughly 2x "
        "ON EVERY PUBLISHED EPSILON — the difference between a defensible number and one an "
        "informed reader discounts by half"
    )

    # 4. The pinned multiplier itself.
    assert multiplier == 1.0, (
        f"SENSITIVITY_MULTIPLIER is {multiplier!r}, not 1.0, while the relation is {relation!r}. "
        "add/remove-one is UNBOUNDED DP: removing a record changes the clipped sum by g_i, whose "
        "norm is at most C, so Delta = C and the multiplier is 1.0. replace-one is BOUNDED DP, "
        "Delta = 2C. D-02's own sensitivity argument — one record moves the sum by at most C — IS "
        "the add/remove-one argument, so 1.0 is the reading this project already assumed"
    )


def test_adjacency_relation_consistent():
    """V-25 -- the relation agrees across the pin, the accountant's prose and the noise line.

    NAMED BY A PRE-REGISTRATION. ``scripts/mitigation_accountant.py::SENSITIVITY_MULTIPLIER_REASON``
    cites this test by symbol, and that file freezes at the first tracked ``results/phase23_*``
    artifact, after which a citation to a test that does not exist could only be corrected by a
    dated continuation. The name is a constraint, not a preference.

    THREE SITES, NO IMPORT BETWEEN THEM. Site A is the frozen pin, read through the ``sys.path``
    insert at the top of this file. Site B is ``accountant.py``'s module docstring. Site C is
    ``dpsgd.py``'s module docstring AND its ``torch.normal`` ``std=`` expression -- prose and
    arithmetic, because prose alone is what P3's warning sign is made of.

    WHY THE ``replace-one`` CHECK READS A WINDOWED DECLARATION RATHER THAN THE WHOLE FILE, which
    is a correction of plan 22-09's own instruction rather than an embellishment. The plan says to
    assert no site CONTAINS the string ``replace-one`` while the multiplier is 1.0. Measured, all
    three sites contain it -- once in ``accountant.py``, once in ``dpsgd.py`` and five times in the
    pin -- every occurrence inside the sentence REJECTING it, which is the argument the pin exists
    to record. Applied literally the assertion reddens on correct code and would have to be
    deleted. What survives contact is the check on the relation each site ADOPTS: the 60-character
    window after ``the adjacency relation is``, measured to sit 179 characters clear of the
    nearest rejection sentence at both sites.
    """
    _assert_adjacency_consistent(
        relation=mitigation_accountant.NEIGHBOURING,
        multiplier=mitigation_accountant.SENSITIVITY_MULTIPLIER,
        accountant_src=_ACCOUNTANT_PATH.read_text(encoding="utf-8"),
        dpsgd_src=_dpsgd_source(),
    )


def test_adjacency_check_bites():
    """The RED half: the same helper the live test runs, fed mutated ``dpsgd.py`` TEXT.

    Three mutations, one per failure mode V-25 exists to refuse -- the relation SWAPPED, the
    relation ABSENT, and a numeric factor slipped into the noise line. Each replacement is
    asserted to have actually applied before it is fed in, because a mutation that silently
    matched nothing would make this test green over the unmutated source and prove precisely
    nothing about the guard.
    """
    relation = mitigation_accountant.NEIGHBOURING
    multiplier = mitigation_accountant.SENSITIVITY_MULTIPLIER
    accountant_src = _ACCOUNTANT_PATH.read_text(encoding="utf-8")
    real = _dpsgd_source()

    declaration = "THE ADJACENCY RELATION IS **add/remove one fact**"
    noise_line = "std=self.sigma * self.C,"
    for target in (declaration, noise_line):
        assert real.count(target) == 1, (
            f"the mutation target {target!r} appears {real.count(target)} times in dpsgd.py, not "
            "once — the replacements below would be no-ops and this RED test would be watching "
            "the unmutated source"
        )

    # (a) the relation SWAPPED to replace-one, with the multiplier left at the add/remove-one
    # value. PITFALLS P3's fake exactly: internally coherent at one site, 2x wrong across sites.
    swapped = real.replace(declaration, "THE ADJACENCY RELATION IS **replace one fact**")
    with pytest.raises(AssertionError, match="does not begin with the pinned"):
        _assert_adjacency_consistent(
            relation=relation,
            multiplier=multiplier,
            accountant_src=accountant_src,
            dpsgd_src=swapped,
        )

    # (b) the relation ABSENT. T-22-44: a consistency check that passes because a site states
    # nothing is the vacuous guard the presence-before-agreement ordering exists to prevent.
    removed = real.replace(declaration, "THE MECHANISM IS A GAUSSIAN")
    with pytest.raises(AssertionError, match="no '.*' statement"):
        _assert_adjacency_consistent(
            relation=relation,
            multiplier=multiplier,
            accountant_src=accountant_src,
            dpsgd_src=removed,
        )

    # (c) a `2.0 *` factor in the noise line: SENSITIVITY_MULTIPLIER = 2.0 in code while the pin
    # says 1.0. The prose still agrees at all three sites, so ONLY the AST arm can see this one.
    doubled = real.replace(noise_line, "std=2.0 * self.sigma * self.C,")
    with pytest.raises(AssertionError, match="ON EVERY PUBLISHED EPSILON"):
        _assert_adjacency_consistent(
            relation=relation,
            multiplier=multiplier,
            accountant_src=accountant_src,
            dpsgd_src=doubled,
        )

    # The control: the same helper, the same call shape, the REAL bytes — green.
    _assert_adjacency_consistent(
        relation=relation,
        multiplier=multiplier,
        accountant_src=accountant_src,
        dpsgd_src=real,
    )
