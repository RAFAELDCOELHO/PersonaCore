"""Guards for the k* driver (`scripts/erasure_kstar_run.py`).

Committed WITH the driver, after the rule. Everything here except the last test is CPU logic that
needs no committed k* record; the last one runs the summary reduction on the committed M1 record.
"""

import ast
import json
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

DRIVER = _ROOT / "scripts" / "erasure_kstar_run.py"
FORBIDDEN = {"erasure_succeeded", "select_ablation_prefix", "_selected_components"}


def _forbidden_hits(source):
    """Names, attributes, import aliases and whole-string constants equal to a forbidden name."""
    hits = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name):
            hits.add(node.id)
        elif isinstance(node, ast.Attribute):
            hits.add(node.attr)
        elif isinstance(node, ast.alias):
            hits.add(node.name.rsplit(".", 1)[-1])
            if node.asname:
                hits.add(node.asname)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            hits.add(node.value)
    return hits & FORBIDDEN


@pytest.fixture
def run():
    import erasure_kstar_run

    return erasure_kstar_run


def _boom(*args, **kwargs):
    raise AssertionError("the measurement was reached")


# --- KSTAR_NO_VERDICT and the committed-prefix rule, by AST ---------------------------------


def test_driver_never_computes_a_verdict_or_re_sweeps():
    assert not _forbidden_hits(DRIVER.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "snippet",
    [
        "from phase19_erasure import erasure_succeeded as v\nv(1)",
        "getattr(m, 'erasure_succeeded')",
        "pin.select_ablation_prefix(1)",
        "x = _selected_components",
    ],
)
def test_the_forbidden_name_scan_sees_the_bypasses(snippet):
    assert _forbidden_hits(snippet)


# --- paths and refusals ---------------------------------------------------------------------


def test_record_paths_are_the_zero_padded_names_the_rule_states(run):
    assert run.arm_path(8).name == "erasure_kstar_arm_k008.json"
    assert run.arm_path(64).name == "erasure_kstar_arm_k064.json"


def test_measure_refuses_a_k_outside_the_checkpoints_before_anything_else(run, monkeypatch):
    monkeypatch.setattr(run.pin, "run_erasure_arm", _boom)
    for bad in (0, 7, 78, 128):
        with pytest.raises(SystemExit, match="pre-registered checkpoint"):
            run.measure(bad)


def test_measure_refuses_to_overwrite_an_existing_record(run, monkeypatch, tmp_path):
    existing = tmp_path / "erasure_kstar_arm_k008.json"
    existing.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(run, "arm_path", lambda k: existing)
    monkeypatch.setattr(run.pin, "run_erasure_arm", _boom)
    with pytest.raises(SystemExit, match="exists"):
        run.measure(8)


def test_measure_holds_only_the_rule_and_the_driver_to_a_clean_tree(run, monkeypatch, tmp_path):
    seen = {}

    def dirty(**kwargs):
        seen.update(kwargs)
        raise SystemExit("dirty tree")

    monkeypatch.setattr(run, "arm_path", lambda k: tmp_path / f"k{k}.json")
    monkeypatch.setattr("personacore.provenance.refuse_if_dirty", dirty)
    monkeypatch.setattr(run.pin, "run_erasure_arm", _boom)
    with pytest.raises(SystemExit, match="dirty tree"):
        run.measure(8)
    assert sorted(seen["pathspec"]) == sorted(run.RULE_PATHSPEC)
    assert not any(path.startswith("results") for path in seen["pathspec"])


def test_summarize_refuses_a_missing_checkpoint(run, monkeypatch, tmp_path):
    monkeypatch.setattr(run, "arm_path", lambda k: tmp_path / f"k{k}.json")
    monkeypatch.setattr(run, "SUMMARY_PATH", tmp_path / "summary.json")
    with pytest.raises(SystemExit, match="missing checkpoint"):
        run.summarize()


def test_summarize_refuses_to_overwrite_a_summary(run, monkeypatch, tmp_path):
    summary = tmp_path / "summary.json"
    summary.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(run, "SUMMARY_PATH", summary)
    with pytest.raises(SystemExit, match="exists"):
        run.summarize()


# --- curve agreement and provenance ---------------------------------------------------------


def _dialogue(on, off):
    return {"adapter_on": on, "adapter_off": off}


def test_curve_agreement_holds_at_zero_difference(run):
    record = {"dialogue_ppl": _dialogue(4.85, 4.57)}
    row = {"dialogue_ppl": _dialogue(4.85, 4.57), "target_rank": 2}
    got = run._curve_agreement(record, row, 2)
    assert got["curve_agreement"] and got["dialogue_on_abs_diff"] == 0.0


def test_curve_agreement_fails_beyond_the_tolerance(run):
    row = {"dialogue_ppl": _dialogue(4.85, 4.57), "target_rank": 2}
    assert not run._curve_agreement({"dialogue_ppl": _dialogue(4.851, 4.57)}, row, 2)[
        "curve_agreement"
    ]
    assert not run._curve_agreement({"dialogue_ppl": _dialogue(4.85, 4.571)}, row, 2)[
        "curve_agreement"
    ]


def test_curve_agreement_fails_on_a_rank_mismatch(run):
    record = {"dialogue_ppl": _dialogue(4.85, 4.57)}
    row = {"dialogue_ppl": _dialogue(4.85, 4.57), "target_rank": 2}
    got = run._curve_agreement(record, row, 1)
    assert not got["curve_agreement"] and not got["target_rank_equal"]


def _record(sha="abc1234", torch="2.7.1", device="mps"):
    return {"config": {"git_sha": sha, "torch": torch, "device": device}}


def test_provenance_requires_the_records_to_agree(run):
    records = {8: _record(), 16: _record(), 32: _record(), 64: _record()}
    assert run._provenance(records)["8"]["git_sha"] == "abc1234"
    for field, other in (("sha", "def5678"), ("torch", "2.8.0"), ("device", "cpu")):
        mixed = dict(records)
        mixed[32] = _record(**{field: other})
        with pytest.raises(SystemExit, match="disagree"):
            run._provenance(mixed)


def test_provenance_refuses_an_unknown_git_sha(run):
    records = {k: _record(sha="unknown") for k in (8, 16, 32, 64)}
    with pytest.raises(SystemExit, match="git_sha"):
        run._provenance(records)


# --- the summary path against the committed M1 record ---------------------------------------


def test_summary_path_reproduces_phase19_on_the_committed_m1_record(run, monkeypatch):
    """The block builder, run on the committed M1 record as k = 78, returns Phase 19's numbers.

    0/27 at the locked floor, all seven non-targets over the margin, the 77.64% destroyed
    adaptation, curve agreement (the calibration witness: the committed curve row and the committed
    M1 record agree exactly), and every per-slot delta re-derived from the counts, so a delta
    attached to the wrong slot cannot pass on the count of seven alone.
    """
    import phase14_factset as factset
    import phase19_erasure as pin
    import phase19_run as p19run

    erased = pin.arm_record_path("erased")
    monkeypatch.setattr(run, "arm_path", lambda k: erased)
    record = json.loads(erased.read_text(encoding="utf-8"))
    phase18 = json.loads(pin.PHASE18_ARM_RECORD_PATH.read_text(encoding="utf-8"))
    values = {f.id: f.value for f in factset.LOCKED_FACTS + factset.SOFT_TIER_FACTS}
    block = run._checkpoint_block(78, record, run._curve(), phase18, values)

    assert block["target"]["successes"] == 0 and block["target"]["n_questions"] == 27
    assert block["target"]["clears_target_floor"]
    assert block["nontarget_over_margin_count"] == 7
    assert abs(block["dialogue"]["adaptation_destroyed_this_run"] - 0.776370113463966) < 1e-12
    assert block["curve_agreement"]["curve_agreement"]

    family = record["config"]["attack_family"]
    tiers = tuple(sorted({d["tier"] for d in record["draws"] if d["family"] == family}))
    pre = p19run._pooled_rows(phase18["draws"], values, family, tiers)
    post = p19run._pooled_rows(record["draws"], values, family, tiers)
    for fact_id, row in pin.nontarget_rows(post).items():
        direct = abs(row["n_answerable"] - pre[fact_id]["n_answerable"]) / row["n_questions"]
        assert abs(block["nontarget"][row["slot"]]["delta"] - direct) < 1e-12, row["slot"]
