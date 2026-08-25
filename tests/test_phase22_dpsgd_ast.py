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

No assertion in THIS plan reads ``src/personacore/privacy/dpsgd.py`` — that module does not exist
yet, and its live check is plan 22-04's.

CPU-only, GPU-free, no torch, no network.
"""

import ast

import pytest

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
