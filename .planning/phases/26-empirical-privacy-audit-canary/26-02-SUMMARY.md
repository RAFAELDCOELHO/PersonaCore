---
phase: 26-empirical-privacy-audit-canary
plan: 02
subsystem: privacy-audit
tags: [canary, driver, sidecar, launchagent, epsilon-lower, adapter-off-once, write-once]
requires:
  - scripts/phase26_prereg.py (audited_point_keys, noised_point_keys, power_threshold, power_gate, epsilon_lower, auditor_ceiling, point_verdict, RULE, EXTENSION, constants)
  - scripts/phase25_recall.py (whole-file template — copied, scorer swapped)
  - scripts/phase25_run.py (atomic_write_json, beat, start_heartbeat, device, HEARTBEAT_PATH — CALLED)
  - scripts/phase25_prereg.py (prove_reproduction, point_record_path, REPRODUCTION_K/N — import-only, byte-untouched)
  - scripts/phase14_recall.py (load_adapted_model, complete_question, score_question, contains_value, N_SEEDED_SAMPLES, CONVBASE_SLIM — lazy)
  - scripts/phase14_factset.py / scripts/phase21_filler.py (LOCKED_FACTS, FILLER_FACTS, FILLER_SLOT_FORMS, family ids, render_family — lazy)
  - scripts/phase25_epsilon.py (report_epsilon), scripts/phase25_gate05.py (FILLER_EXPOSURE_OMITTED), scripts/phase18_extraction.py (CLUSTER_DENOMINATOR_RATIONALE) — lazy, import-only
  - results/phase25_frontier.json (read as data, never modified)
provides:
  - scripts/phase26_canary.py — the audit driver (653 lines): _items, _lists, _score_list, score_off_once, score_point, emit, build_parser, main
  - artifacts/com.personacore.phase26.canary.plist — the LaunchAgent (NOT launched; plan 26-04's gate)
affects:
  - 26-03 (tests over this driver: AST, dry-run, refusals, plist, kwargs trace), 26-04 (launch), 26-05 (emit + commit the artifact)
tech-stack:
  added: []
  patterns: [sidecar-per-point sha-pinned reuse-or-refuse, OFF arm once on the pinned base, lazy torch imports, write-once artifact with --force, no git argv in the driver]
key-files:
  created:
    - scripts/phase26_canary.py
    - artifacts/com.personacore.phase26.canary.plist
  modified: []
decisions:
  - "score_off_once's reuse branch and emit hash the base: reuse branch imports phase14_recall lazily only for CONVBASE_SLIM (reached only when a sidecar exists); emit hashes off_blob['base_path'] on disk so --emit never imports torch"
  - "--skip-off omitted: reuse-by-hash already makes a second run reuse the OFF sidecar (plan allowed omission)"
  - "emit's first statement is the overwrite _prove (out_path is wrapped in pathlib.Path AFTER it), so the AST criterion holds literally"
metrics:
  duration: ~45 min
  completed: 2026-09-10
  tasks: 2
  files: 2
---

# Phase 26 Plan 02: The Canary Audit Driver and Its LaunchAgent Summary

`scripts/phase26_canary.py` replays `teach_persona.score_items`' two calls per fact over four lists (IN taught/held-out on the 8 `LOCKED_FACTS`, OUT taught/held-out on the 56 `FILLER_FACTS` rendered with `forms=FILLER_SLOT_FORMS`), one `enumerate` per list, measures the adapter-off arm once on the sha256-pinned base, routes the control's IN-taught sum through `prove_reproduction` before writing, and assembles `results/phase26_canary.json` only after the OFF sidecar and all 16 point sidecars exist — exclusions, ceiling and power gate before any verdict, write-once, pinned to the frontier in both directions. The plist mirrors the recall agent and was NOT launched.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Driver scoring half — `_items`, `_lists`, `_score_list`, `score_off_once`, `score_point` | `d438d09` | scripts/phase26_canary.py (381 lines) |
| 2 | Driver assembly half — `emit`, `build_parser`, `main`; the plist | `a038182` | scripts/phase26_canary.py (653 lines), artifacts/com.personacore.phase26.canary.plist |

Base: `6f7befd` on `main`. Hooks ran; explicit `git add <file>` only. `git diff --stat HEAD~2 -- scripts/teach_persona.py scripts/phase25_prereg.py scripts/phase18_extraction.py scripts/phase21_filler.py .planning/STATE.md .planning/ROADMAP.md` → empty.

## Acceptance criteria — verified by running them

**Task 1 verify one-liner** (plan `<automated>`): printed `OK`; `ruff check` → `All checks passed!`; `ruff format --check` → `1 file already formatted`. Extra criteria in the same run:
- `sidecar_path("../x")` → `SystemExit: [phase25_prereg] point_key '../x' is not a non-empty alphanu…` (charset refusal via `point_record_path`); `sidecar_path("dp_n8_sigma0p500000") == _ROOT/"data"/"phase26_canary_dp_n8_sigma0p500000.json"`; `off_sidecar_path() == _ROOT/"data"/"phase26_canary_off.json"`.
- `score_point("dp_n8_sigma0p500000", dry_run=True)` → `("dry_run", None)` printing `DRY RUN — would score checkpoints/phase25_sigma0p500000_dp_n8_adapter.pt`; `score_off_once(dry_run=True)` → `("dry_run", None)`.
- AST: exactly one `prove_reproduction` call site, inside `score_point`, inside the `point_key == phase26_prereg.CONTROL_KEY` branch, line-before `atomic_write_json`; `_score_list` has exactly one `for` over `enumerate(items)` and passes `index=index` to `pr.complete_question`; no top-level import of torch/teach_persona/phase14_*/phase21_filler/phase18_extraction; no `torch.load`; no list/tuple literal starting with `"git"`.

**Task 2:**
- `.venv/bin/python scripts/phase26_canary.py --dry-run` → exit 0; first line `[phase25_launch] pid=… ppid=… pgid=… sid=…` (the banner), then `off: DRY RUN — would score the adapter-off arm on phase25_sigma0p000000_dp_n8_adapter.pt`, then 16 `DRY RUN` lines in `ORDERED_POINT_KEYS()` order (`dp_n8_sigma0p000000` … `dp_n8_sigma80p000000`). `python -X importtime … --dry-run 2>&1 | grep -c "| torch"` → `0`.
- `emit()` on an empty `SIDECAR_DIR` → `SystemExit: … the adapter-off sidecar …/phase26_canary_off.json is missing — the audit is not complete; record the dated D-19 named limitation in results/phase26_operational_note.md …`; no file written. With the OFF sidecar and 15 point sidecars → `1 of 16 point sidecars missing: ['dp_n8_sigma80p000000'] — not scored; a partial artifact is NEVER assembled (D-19) — add the dated named-limitation entry to results/phase26_operational_note.md`; no file written.
- Full assembly on 17 fake sidecars (one filler fact planted with an adapter-off hit; control planted 8/8): `n_in/n_out 8 55`, `auditor_ceiling 2.768716915791795` (lower than 2.7859 at n_out=56 — Pitfall 6 observed), `reachable 4/15 [sigma24, 32, 50, 80]`, power gate `PASSED` (`2.7687 vs 0.6339783761989397`, `POWER_SENTENCE` printed), `summary {'BROKEN': 0, 'CONSISTENT': 15, 'INCONCLUSIVE': 0}`, control `verdict None`; every `epsilon_sentence` equalled `fr["epsilon_report"]["rendered"][key]` (all 16, control with `None`). Sigma-80 reasons carried `0/8`, `0/55`, `direction_1 = TPR_lb <= delta: direction 1 undefined`, `direction_2 = -0.0480`, `epsilon_lower = -0.048… vs epsilon_upper = 0.6339…: CONSISTENT — this test can only accuse…`; sigma-0.5's last reason was the D-13 ceiling clause. Second `emit` → `REFUSING to overwrite`; `overwrite=True` re-emitted. (All in a `tempfile.mkdtemp()`; nothing under `data/` or `results/`.)
- AST: `emit.body[1]` (after the docstring) is the overwrite `_prove`; `auditor_ceiling` call at line 503 precedes the only `point_verdict` call at 563; `report_epsilon` called with exactly `point_epsilon, curve_total_epsilon, selection_accounted`; `main` calls `score_off_once` (line 646) before the `for` loop (648); every keyword `main` passes to `score_off_once` / `score_point` / `emit` is a declared parameter.
- `plutil -lint artifacts/com.personacore.phase26.canary.plist` → `OK`; `plistlib`: `Label == "com.personacore.phase26.canary"`, `KeepAlive is False`, `RunAtLoad is False`, `ProgramArguments[:3] == ["/usr/bin/caffeinate", "-dims", "/Users/juliorcoelho/PersonaCore/.venv/bin/python"]`, `[3]` ends with `scripts/phase26_canary.py`, `--heartbeat` value equals the recall plist's, `PERSONACORE_SWEEP_ACTIVE == "1"`, `StandardOutPath` differs. `diff` against the recall plist: exactly the header comment, Label, `ProgramArguments[3]`, and the two log paths.
- `.venv/bin/python -m pytest -q tests/test_phase25_recall.py tests/test_phase25_close.py tests/test_phase26_prereg.py` → `55 passed in 2.58s`.

## The live-path kwargs trace (Phase-25 lesson: dry-run tests hide an unwired driver)

Every call site in the file was bound against the callee's `inspect.signature` (AST walk + `sig.bind`), all `OK`:

- `main` → `score_off_once(dry_run=, heartbeat_path=)`, `score_point(key, dry_run=, heartbeat_path=)`, `emit(overwrite=)` — each name declared.
- `score_off_once` / `score_point` → `_prove_host_adapter(point_key)`; `phase25_run.beat(heartbeat_path, **state)` with `state` keys exactly `point, stage, shape, draw_index` (= `beat`'s keyword-only set); `start_heartbeat(heartbeat_path, state)`; `device()`; `pr.load_adapted_model(device, adapter_path=)` → 5-tuple `(model, cfg, tok, forbid, artifact)`; `_lists()`; `_score_list(model, tok, device, forbid, items, label=, heartbeat_state=)`; `adapter_disabled(model)`; `phase25_prereg.prove_reproduction(k, n)` with `int`s; `_provenance(device, scoring_seconds)`; `atomic_write_json(path, blob)`.
- `_score_list` → `pr.complete_question(model, tok, question, device, forbid, index=index)`; `pr.score_question(drawn["completions"], fact.value)`.
- `_items` → `fs.render_family(family_id, fact, forms=forms)`; `pr.contains_value(question, fact.value)`.
- `emit` → `_readings(blob, in_tier, out_tier, n_in=, n_out=, **kw)` with `kw` keys `excluded_in, excluded_out`; `phase26_prereg.epsilon_lower(members, n_in, nonmembers, n_out)`; `auditor_ceiling(n_in, n_out)`; `power_gate(control_eps_lower, power_threshold(fr))`; `point_verdict(reading, eps_upper, power=, auditor_ceiling=)`; `phase25_epsilon.report_epsilon(point_epsilon=, curve_total_epsilon=, selection_accounted=)`.
- Record keys dereferenced (`adapter_path, adapter_sha256, arm, sigma, epsilon, delta, epsilon_omitted_reason`) all present on the frontier's control record; sidecar keys `emit` reads (`per_fact[fid].answered_questions/n_questions/member`, `adapter_sha256`, `base_path`, `base_sha256`, `reproduction_gate`) are exactly what `_score_list` / `score_point` / `score_off_once` write.

**Live smoke (not a run):** the real loader on the real device with the control adapter, `_lists()` → `{in_taught: 112, in_heldout: 72, out_taught: 784, out_heldout: 504}`, then `_score_list` on a 3-question slice: adapter-ON `27/27` (fact `cand_person_quillon` member=True, 3/3 questions, 9 draws/question), `adapter_disabled` IN `0/27`, OUT `0/27` (`filler_boat_kestrelaine` renders and scores through the filler forms). `device mps`, 27.3 s, heartbeat state advanced to `draw_index 2`; the blob plus `_provenance(...)` is `json.dumps`-serialisable. No sidecar was written (`ls data/ | grep -c phase26` → `0`).

## Deviations from Plan

None in substance. Two in-plan choices exercised:
1. `--skip-off` omitted (the plan sanctions omission; reuse-by-hash covers the rerun case).
2. `emit` hashes `off_blob["base_path"]` on disk rather than importing `phase14_recall` for `CONVBASE_SLIM` (the plan offers either), so `--emit` never imports torch. `score_off_once`'s reuse branch does import it lazily — reached only when an OFF sidecar exists, never on this host's dry run.

## Known Stubs

None. Every function has its live path wired; `--dry-run` returns before the lazy imports by design.

## Threat Flags

None beyond the plan's register (T-26-01 … T-26-07 all mitigated as specified: only `load_adapted_model` deserialises; every write is `atomic_write_json`; write-once `_prove` first; `KeepAlive false`; no git argv; keys through `point_record_path` + `audited_point_keys`; sha mismatches refused).

## Self-Check: PASSED

- `scripts/phase26_canary.py` — FOUND
- `artifacts/com.personacore.phase26.canary.plist` — FOUND
- commit `d438d09` — FOUND
- commit `a038182` — FOUND
