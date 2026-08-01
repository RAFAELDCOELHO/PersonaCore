---
phase: 13
slug: ewc-a-b-no-forgetting-experiment
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-01
---

# Phase 13 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Scope note: this phase ships offline research drivers (training, plotting, sampling) and
committed evidence artifacts. There is no network surface, no authentication, no untrusted
user input, and no multi-tenant data. The live threat classes are **Tampering** (recorded
evidence being silently overwritten or read from a mutable reference), **Repudiation**
(provenance of pre-registered rules and reported numbers), and **Info Disclosure / EoP**
(pickle deserialization via `torch.load`). ASVS L1 is the appropriate bar.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| driver → committed Phase-12 evidence | `scripts/finetune_ab.py` writes into `results/`; a stray write target would clobber recorded evidence (`finetune_prod.csv`, convbase trio) | CSV evidence rows |
| driver → local checkpoints | pickle deserialization of `checkpoints/best.pt` (full pickle) and `checkpoints/fisher_tinystories.pt` (restricted) | tensors + pickled Python objects |
| sample script → arm checkpoints | pickle deserialization of `checkpoints/phase13_{arm}_latest.pt` | tensors + pickled Python objects |
| driver → D-11 reference input | `results/finetune_prod.csv` read at run time and used as the sole enforced reproduction basis | float endpoints (mutable file) |
| scripts → committed evidence artifacts | refuse-to-rerun guards on arm outputs and the samples markdown | markdown / CSV / PNG |
| report → committed artifacts | every published number must trace to a committed artifact or a cited exception | reported floats + protocol claims |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-01 | Tampering | `finetune_ab.py` output paths | mitigate | `refuse_if_exists` on all arm outputs; Phase-12 paths never write targets; pinned by tests | closed |
| T-13-02 | Info Disclosure / EoP | `torch.load` of `best.pt` | mitigate | `weights_only=False` only on the project's own anchor with the T-12-10 comment; Fisher via `load_fisher` (`weights_only=True`, fingerprint-pinned) | closed |
| T-13-03 | Repudiation | pre-registration provenance | mitigate | constants committed before runs (git order); git SHA in report preamble; `git_sha()` provenance echo | closed |
| T-13-04 | Tampering | arm output paths on relaunch | mitigate | `refuse_if_exists` fires on any rerun; message names only the arm's own outputs | closed |
| T-13-05 | Repudiation | run provenance | mitigate | per-arm provenance echo (seed, config, penalty bit, `git_sha`) + D-11 side-by-side print | closed (see WARNING-3) |
| T-13-06 | DoS | 37-min MPS run crash mid-flight | mitigate | `PYTORCH_ENABLE_MPS_FALLBACK=1` set before `import torch`; sequential arms | closed |
| T-13-07 | Info Disclosure / EoP | `torch.load` of arm checkpoints | mitigate | `weights_only=False` only on the project's own checkpoints with the T-12-10 comment | closed |
| T-13-08 | Tampering | samples / figures overwrite | mitigate | refuse-to-rerun guard on the samples markdown; figures regenerable from committed CSVs | closed |
| T-13-09 | Repudiation | cherry-picking accusation surface | mitigate | seeded prompt selection, one-run both-arms protocol, per-PROMPT warm generator, proxies over ALL generations, **stated in the file header** | closed |
| T-13-10 | Repudiation | report numbers provenance | mitigate | all cells read from committed artifacts; λ=0 frontier exception row; verdict computed from committed constants | closed (see WARNING-2) |
| T-13-11 | Tampering | pre-registration table drift | mitigate | pre-reg table byte-unchanged from the Plan 13-01 commit | closed |
| T-13-SC | Tampering | package installs | accept | no packages installed this phase — verified, see Accepted Risks Log | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Verification Evidence

### T-13-01 — Tampering, arm output paths — CLOSED

- `refuse_if_exists` defined `scripts/finetune_ab.py:134-142` (SystemExit naming the offender);
  **called at `:180`, before any compute** — after arg validation, before preflight/`torch.load`.
- `arm_outputs` `:125-131` returns exactly the two arm-scoped write targets.
- Complete write-target enumeration by grep: `_preseed_csv(arm_csv, …)` (`:160` write mode,
  invoked `:260`), `arm_csv.parent.mkdir` (`:258`), `log_path=str(arm_csv)` (`:293`),
  `checkpoint_path=str(arm_ckpt)` (`:295`). No other write path exists in the file.
- `PROD_CSV` is opened in read mode only (`:333`); `convbase` appears nowhere.
- Tests: `tests/test_phase13_driver.py:80-89` (`test_arm_outputs_scoped`, parametrized over both
  arms, asserts `finetune_prod`/`convbase` absent) and `:91-101` (`test_refuse_to_rerun_guard`,
  asserts SystemExit names the existing file, returns `None` when absent).
- Empirical: `git log -1 -- results/finetune_prod.csv` → `87198ec` (Phase 12-05);
  `git status --porcelain results/finetune_prod.csv` empty.

### T-13-02 — Info Disclosure / EoP, `torch.load` of `best.pt` — CLOSED

- `scripts/finetune_ab.py:207-208`: `# weights_only=False: TRUSTED-only read of the project's OWN
  anchor checkpoint (T-12-10).` immediately above `torch.load(BEST_PATH, weights_only=False)`.
- Full-pickle load sites in the driver: exactly one (grep for `torch.load` → `:208` only).
- Fisher goes through `load_fisher` (`:222`) with `expected_fingerprint` built at `:221` from
  `git_sha`/`step`/`val_loss`. `src/personacore/checkpoint.py` `load_fisher` uses
  `torch.load(..., weights_only=True)`, then a schema gate, a missing-key gate, and a hard
  `ValueError` on fingerprint mismatch — the restricted unpickler, no code execution.

### T-13-03 — Repudiation, pre-registration provenance — CLOSED

- Git ordering (pre-registration proof): `c3d942e` driver → `91aedd1` tests → `8fa2aa1` report
  preamble → `ead34c1` EWC CSV → `389e861` naive CSV. Rules precede every Phase-13 number.
- `git diff c3d942e HEAD -- scripts/finetune_ab.py` is **empty** — the driver is byte-identical to
  its pre-registration commit; the constants block (`:66-106`) has not moved.
- Report preamble cites `c3d942e` and `91aedd1`, and the `## Pre-Registration` table carries a
  per-row "Locked at" column.
- Provenance echo `scripts/finetune_ab.py:322-329` including `git_sha()` at `:329`. Confirmed to
  have actually executed: both run logs print the block with `driver git_sha:
  5e908ac…` (EWC) / `ead34c1…` (naive) and the anchor fingerprint trio.
- **Caveat (WARNING-1):** two constants in the same pre-registration block,
  `PROD_DIALOG_4000`/`PROD_RETENTION_4000` (`:105-106`), are commented "these literals are the
  tripwire" but are referenced only inside a `print()` at `:347`. The declared tripwire is inert.
  This does not break the git-order pre-registration proof, so T-13-03 stays closed, but it is
  logged as unregistered surface UF-1 below. **Update (pass 2):** the tripwire is no longer
  inert — it is now enforced from *outside* the frozen driver by
  `tests/test_phase13_driver.py::test_prod_csv_matches_preregistered_literals` (`:114-130`). See
  UF-1 below for the enforcement evidence.

### T-13-04 — Tampering, relaunch — CLOSED

Same guard as T-13-01. The SystemExit message (`:139-142`) interpolates only `paths` — the arm's
own two outputs — so an operator instruction to delete never names a Phase-12 artifact.

### T-13-05 — Repudiation, run provenance — CLOSED (with WARNING-3)

- Code present: provenance echo `:322-329`; D-11 side-by-side table printed `:337-346`.
- Verified to have run: I read both captured logs. The EWC log contains the full echo plus
  `D-11 cross-check … dialog_ppl 4.573349 / 4.573349 / +0.000000`, `retention_ppl 3.891140 /
  3.891140 / +0.000000`, `D-11 MATCH`. The naive log contains the matching echo with
  `penalty_fn: None (λ=0)` and an identical `TrainConfig` repr and anchor fingerprint — the
  one-bit claim's provenance evidence.
- **WARNING-3:** those logs live only at
  `/private/tmp/claude-501/.../scratchpad/{ewc,naive}_run.log` — an ephemeral session directory.
  No `results/phase13_*_run.log` is tracked by git, while Phase 12's analogue
  (`results/finetune_prod_run.log`) **is** committed and is cited by this phase's own report as
  the source of the twin config. The declared mitigation ("captured in the background-run log")
  held at execution time but leaves no durable in-repo artifact. Recommend committing both logs.

### T-13-06 — DoS, MPS run crash — CLOSED

- `scripts/finetune_ab.py:36` `os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")` sits
  **before** `import torch` at `:38` (ordering enforced by the `# noqa: E402` on the import).
  Same pattern in `scripts/make_retention_samples.py:37` before `:39`.
- Sequential arms confirmed by log mtimes (EWC 15:13, naive 15:52) and by both runs reaching the
  end-of-run proofs (`proofs passed:` lines, wall 37.6 / 38.3 min, exit clean).

### T-13-07 — Info Disclosure / EoP, arm checkpoints — CLOSED

- `scripts/make_retention_samples.py:108-109`: TRUSTED-only T-12-10 comment directly above
  `torch.load(path, weights_only=False, map_location="cpu")`.
- Only one `torch.load` in the file; `path` comes exclusively from `ARMS` (`:56-59`), both
  repo-local `checkpoints/phase13_{arm}_latest.pt` written by this repo's own driver.
- **Re-audit pass 2 (post-`f06f92a`):** re-grepped the current file — still exactly one
  `torch.load`, now at `:113`, still carrying the T-12-10 TRUSTED-only comment at `:112`, still
  fed only from `ARMS` (`:60-63`). The RNG fix added no new deserialization site and did not
  widen `weights_only`. (UF-4's read-side gap — no `step == 4000` / cross-arm config pin on the
  loaded blob — is unchanged and still logged below.)

### T-13-08 — Tampering, samples / figures overwrite — CLOSED

- Samples guard `scripts/make_retention_samples.py:119-126` — `SystemExit` naming the file,
  raised **first** in `main()`, before checkpoint loads.
- Figures: `plot_forgetting_curve(out_dir)` / `plot_frontier(out_dir)` are `out_dir`-parameterized
  so the smoke test renders into `tmp_path`; both PNGs regenerate byte-identically (SHA-256) from
  the committed CSVs per 13-VERIFICATION, so overwrite is recoverable by design.
- **Re-audit pass 2 — guard specifically checked for weakening.** The T-13-09 remediation
  required regenerating the samples, i.e. exactly the situation in which a refuse-to-rerun guard
  gets "temporarily" relaxed. It was not: `git diff 4f4a58d HEAD -- scripts/make_retention_samples.py`
  shows **no hunk touching `main()`'s guard block**, which still reads
  `if SAMPLES_PATH.exists(): raise SystemExit(…)` at `:123-130` — unconditional, no force flag,
  no env override, no `--overwrite` argument anywhere in the file, and still the **first**
  statement in `main()`, ahead of both checkpoint loads. Regeneration was done by deleting the
  stale artifact (the guard's own documented escape hatch), leaving the control in force.

### T-13-09 — Repudiation, cherry-picking accusation surface — CLOSED (was OPEN/BLOCKER)

**Re-audit 2026-08-01 (pass 2) — independently verified, not taken on the file's word.**
Traced the generator end-to-end through the real call chain rather than trusting the comment:
`gen_rng = torch.Generator(device=device).manual_seed(SEED + story_idx)` is constructed
**inside** the per-prompt loop (`scripts/make_retention_samples.py:164`, loop opens `:159`) and
passed as `generator=gen_rng` to `_complete` `:166` → `**kw` → `collect`
(`src/personacore/generation/core.py:83-92`) → `generate(generator=…)` `:35, :73` →
`next_token(generator=…)` (`src/personacore/generation/sampling.py:70`) →
`torch.multinomial(probs, num_samples=1, generator=generator)` `:103`. The warm path therefore
consumes **zero** draws from the global RNG, and the seed is a pure function of `story_idx` —
independent of the arm, of every earlier prompt, and of whether any earlier prompt stopped
early. Cross-prompt RNG coupling is eliminated structurally, not merely re-seeded around. The
greedy path short-circuits to `argmax` (`sampling.py:91-92`) and consumes no draw, so it cannot
re-introduce coupling either; `model.eval()` (`:118`) removes the only other in-loop RNG
consumer (dropout). `seed_everything(SEED)` at `:157` is now explicitly non-load-bearing.

Artifact-side re-verification (measured on the committed markdown, this pass):
- The prompt-20081 EWC anomaly that exposed the defect is **gone** — its warm block is now 230
  chars; all **20** warm blocks span 186–234 and all **20** greedy blocks 197–232, a uniform
  band with no short outlier, consistent with the claimed `0/20` eos terminations in both arms.
- Independent recount of `<|user|>`/`<|assistant|>`/`<|system|>` occurrences inside the per-arm
  sections of `results/phase13_retention_samples.md`: naive **79**, EWC **69** — exactly the
  counts the file's own proxy table and the report publish.
- The two previously-false provenance sentences now describe the implemented protocol:
  `phase13_retention_samples.md:8-11` ("per-PROMPT `torch.Generator` seeded `1337 +
  story_idx`, identical across arms … an early stop in one prompt cannot shift any later
  prompt's stream") and `results/phase13_ab_report.md:341-344` (same claim, `## Retention
  Samples`). Both are now true of the code as written. No residual overstatement found.
- `git diff 4f4a58d HEAD -- scripts/make_retention_samples.py` touches only the docstring, the
  `SEED` comment, the generator construction/threading and the header strings — the T-13-08
  guard and the T-13-07 `torch.load` site are byte-unchanged (see those entries).

**Resolution (option A, below):** `scripts/make_retention_samples.py` now builds a per-PROMPT
`torch.Generator(device=device).manual_seed(SEED + story_idx)` and threads it into the warm
`_complete()` call, and `results/phase13_retention_samples.md` was regenerated (the stale file was
deleted first — the T-13-08 refuse-to-rerun guard is untouched and still in force). Both arms are
still loaded in ONE process run (D-12). The header sentence and
`results/phase13_ab_report.md` `## Retention Samples` now state the protocol actually used.

Evidence for the closure:

- **Cross-process reproducibility preserved.** Two full regenerations in separate processes are
  byte-identical (`diff` empty; SHA-256 `c59a6c31…6be313e6` both times).
- **Pairing proven by perturbation.** Shortening prompt 20081's generation budget (the same RNG
  perturbation an early stop causes) changes **0 of the 4** later prompts under the new protocol
  and **4 of 4** under the old per-arm-seed protocol. The defect and its fix are both demonstrated
  against the same model and prompt set.
- **Greedy halves unchanged** across the regeneration (argmax is RNG-free), confirming the same
  step-4000 endpoints produced the new file.
- **Updated proxies (re-derived from the new samples):** naive `0/20` stops / **79** leakage;
  EWC `0/20` stops / **69** leakage. The EWC arm's single early stop was itself a product of the
  shifted stream and does not recur. The substantive negative result is unchanged: **both arms
  leak role tokens mid-story and neither yields an intact story-mode generator.**

The original analysis is retained below as the audit trail of the defect.

Three of the four declared elements are present in code:

- seeded prompt selection — `_build_prompts` `:87-103`, local `np.random.default_rng(SEED)` `:94`;
- one-run both-arms — single `for label, ckpt_path in ARMS` loop `:146-171`, both checkpoints
  loaded in one process;
- proxies over ALL generations — `n_stopped`/`n_completions`/`leakage` accumulated per generation
  `:160-162`, reported per arm `:192-197`.

The fourth element — "stated in the file header" — is present as text but the statement it makes
is **false against the committed artifact**, which converts the mitigation into an expansion of
the very repudiation surface it was meant to close. Verified independently of 13-REVIEW:

1. `seed_everything(SEED)` is at `scripts/make_retention_samples.py:153`, **outside** the
   per-prompt loop (`:155-167`) — one seed per arm, ten prompts inside the stream.
2. `_complete` (`:70-84`) never passes `generator=`, so `next_token` reaches
   `torch.multinomial(probs, num_samples=1, generator=None)`
   (`src/personacore/generation/sampling.py:103`) — the **global** torch RNG. Greedy returns
   `argmax` (`sampling.py:91-92`) and consumes no draw.
3. `generate` returns early on a stop id **after** the draw for that token
   (`src/personacore/generation/core.py`, `if tok in stops: return`). Draws consumed by a warm
   completion are therefore `len(gen) + (1 if stopped else 0)` — arm-dependent.
4. The committed artifact records naive `0/20` stops and EWC `1/20`. Measuring warm-block lengths
   in `results/phase13_retention_samples.md` myself: EWC prompt **20081** is **151** chars against
   a 195–241 band across all other warm blocks, and it is the **6th of 10** prompts. The last four
   prompts' warm completions in the EWC arm were drawn from a shifted stream.

Two committed evidence files assert the opposite with no caveat:

- `results/phase13_retention_samples.md:8-9` — "re-seeded to 1337 before EACH arm, so both arms
  draw from the identical stream and a text difference is a weight difference";
- `results/phase13_ab_report.md:342` — "warm-sampling RNG re-seeded per arm so both arms draw the
  identical stream".

`## Threats to Validity` in the report does not name it (grep for `RNG`/`stream`/`desync` returns
only line 342 and unrelated matches at 168/247/259). The published leakage counts (79 / 70) are
compared across arms as if paired on the warm half; they are real per-arm measurements but not a
paired comparison after prompt 20081.

**Blast radius:** limited to the D-12 supplementary samples. No headline number is sampled — the
2×2, the gate verdict, the D-11 cross-check, the trajectory table and both figures are all
teacher-forced eval over committed CSVs.

**To close, either:** (A) thread a per-prompt `torch.Generator(device=…).manual_seed(SEED +
story_idx)` into the warm `_complete()` call and regenerate the samples, keeping the claim; or
(B) keep the artifact and correct both sentences to state that streams are aligned only up to the
first early stop (EWC arm, prompt 20081, 6th of 10), plus a threats-register line.

**Option (A) was taken** — see the resolution block at the top of this entry. Note the generator
must sit on the *model's* device, not `"cpu"`: `torch.multinomial` rejects a cross-device
generator (`Expected a 'mps' device type for generator but found 'cpu'`), and an MPS generator was
verified deterministic across processes.

### T-13-10 — Repudiation, report numbers provenance — CLOSED (with WARNING-2)

- `## Evidence Index` maps every artifact to its role and states the tracing rule.
- The λ=0 frontier point carries its exception row under `## Pre-Registration` ("Provenance
  exception", `ft_lr_9e-5.csv` has no `retention_ppl`, cited to `666d096`, "not recomputed here").
- 13-VERIFICATION independently re-derived the 2×2 cells, the gate verdict (33.6068×), all 16
  trajectory deltas and all six D-11 cells from the committed CSVs — exact matches.
- **WARNING-2:** the pre-registered gate `ewc_mitigates` is executed by no shipping code path —
  only by `tests/test_phase13_driver.py` and by ad-hoc session commands. The published verdict is
  reproducible but is not the output of a committed artifact-producing step. Secondly, the report
  publishes the sample proxies (79 / 69, 0/20, 0/20), which are non-CSV numbers sourced from
  `phase13_retention_samples.md` — traceable to a committed artifact, and since the T-13-09
  remediation that artifact's pairing claim holds as stated.
- **Re-audit pass 2 — the changed numbers were re-traced, not assumed.** The proxies moved with
  the regeneration (EWC eos `1/20 → 0/20`, EWC leakage `70 → 69`), so every published sample
  number was re-derived: the report's `## Retention Samples` table (`:349-350`) and its inline
  citation (`:178`, "79 (naive) vs 69 (EWC)") match `phase13_retention_samples.md:17-18`
  byte-for-byte, and both match my own independent recount off the rendered samples (79 / 69)
  and block-length scan (no early stop in any of the 40 blocks). The CSV-sourced numbers are
  also re-confirmed unchanged: the 2×2 cells equal the final rows of the committed arm CSVs
  exactly — naive `4.192794562524908` / `8.52417066884246`, EWC `4.573349242745997` /
  `3.8911400839446597`, both files clean in `git status`. WARNING-2 (the gate is executed only
  by tests, not by a shipping artifact-producing step) is unchanged.

### T-13-11 — Tampering, pre-registration table drift — CLOSED

`git diff 8fa2aa1 HEAD -- results/phase13_ab_report.md` removes exactly seven lines, all of them
`_Pending — filled by Plan 13-04 after both arms run._` placeholders. Every pre-registration table
row is byte-unchanged from the pre-run commit.

**Re-audit pass 2 (the report was edited again after the RNG fix, so this was re-run):** extracted
the whole `## Pre-Registration` section from `8fa2aa1` and from `HEAD` and compared —
**byte-identical, 2931 bytes both sides.** The post-fix report edits touched only the
`## Retention Samples` prose and proxy table. `git diff c3d942e HEAD -- scripts/finetune_ab.py`
is **still empty** (re-verified this pass), so the constants block backing T-13-03 is also intact.

### T-13-SC — Tampering, package installs — ACCEPTED, verified

Re-verified pass 2 after three further commits (`f06f92a`, `efc3571`, `ef65247`, `0794cdc`):
`git diff --stat c3d942e~1 HEAD -- pyproject.toml requirements.txt Makefile` is empty. The full
changed-file list across the phase contains only planning docs, `results/` evidence, three
`scripts/` files and two `tests/` files. No dependency was added, pinned, or upgraded, so there is
no package-legitimacy surface to audit.

---

## Unregistered Flags (WARNING — not blockers)

No SUMMARY in this phase declared a `## Threat Flags` section, so none of the following was
mapped to a threat ID at execution time. Recorded here so they do not vanish.

| ID | Surface | Category | Evidence | Why unregistered |
|----|---------|----------|----------|------------------|
| UF-1 | D-11 reference input integrity | Tampering (read side) | **RESOLVED (pass 2, `efc3571`)** — see verification note below the table | Was: the `finetune_ab.py:105-106` literals were referenced only in a `print()` at `:347`, so the declared tripwire did not exist for any future re-run |
| UF-2 | D-11 tolerance reuses the claim margin | Tampering | `finetune_ab.py:350` — `abs(ret − prod) > MARGIN`, where MARGIN is the minimum effect size allowed to *claim* mitigation | A reproduction drift of one full claim margin passes silently; observed drift is ~1e-7, so a tolerance five orders tighter is available. A separate `REPRO_TOL` would make the two quantities distinct |
| UF-3 | Run-provenance logs not retained in-repo | Repudiation | no `results/phase13_*_run.log` in `git ls-files`; echoes exist only in an ephemeral scratchpad. **Pass 2 addendum:** the same gap now also covers the sampling path — the report's `## Threats to Validity` row "free-running generation … bit-identical, two separate sampling runs, `diff` empty" and this file's post-fix regeneration-pair evidence (SHA-256 `c59a6c31…6be313e6`, which I re-computed on the committed artifact and it matches) both rest on runs whose logs/second copies are not committed | See T-13-05 WARNING-3; Phase 12 committed its analogue. Not a T-13-09 blocker: the pairing claim is a *within-run* property, proven by reading the code path, not by cross-process determinism |
| UF-4 | Read-side inputs unvalidated | Tampering | `make_retention_samples.py:106-115` accepts any blob at the arm checkpoint paths (no `step == 4000`, no cross-arm `git_sha`/`train_config` equality, no `ewc_lambda` asymmetry check); `finetune_ab.py:230, 249-252` trusts `retention_anchors.json` for the step-0 retention point with no pin to `best.pt`, although the JSON carries its own `git_sha` | The phase's artifact-isolation discipline (D-07 / WR-02) is write-side only; nothing pins the artifacts being *read* |
| UF-5 | Raw model output escapes its blockquote in committed evidence | Tampering (rendered artifact integrity) | `make_retention_samples.py:228, 238, 242` interpolate `f"> {text}"`; multi-line completions leave sample blocks partly outside the quote (measured on the committed markdown; line numbers shifted by `f06f92a`, the defect is unchanged) | Generated text — including literal `<\|user\|>` / `<\|assistant\|>` role tokens, the very contamination being measured — renders as document prose, visually indistinguishable from the script's own claims |

**UF-1 enforcement verified (pass 2), not taken on the test's docstring.** The test exists at
`tests/test_phase13_driver.py:114-130`, is collected by the default suite (no marker, no skip —
`pytest tests/test_phase13_driver.py` → **8 passed**), reads the final row of `fab.PROD_CSV` and
asserts `step == MAX_STEPS` plus `abs(csv − PROD_DIALOG_4000) < 1e-9` and
`abs(csv − PROD_RETENTION_4000) < 1e-9` — the pre-registered literals are the assertion's
source of truth and the mutable CSV is the thing under test, which is the correct direction.

I confirmed it actually *fails* rather than merely passing: re-executing the test function
against a copy of `finetune_prod.csv` with `retention_ppl` perturbed by **+1e-8** (five orders
below `MARGIN`, so the driver's own `:350` check would still pass silently) raises
`AssertionError`; against a truncated CSV it fails on the `step` assertion. The tripwire is live
on every commit, not only on a re-run of the 37-minute arm.

Residual scope note (not a blocker, no new flag opened): the test pins the **final row only**, so
drift in an intermediate `finetune_prod.csv` row would still pass. That matches UF-1's original
scope (the D-11 step-4000 endpoints) and UF-2 below is unaffected — the driver's run-time
reproduction tolerance at `finetune_ab.py:350` is still `MARGIN`, not the test's `1e-9`.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-13-01 | T-13-SC | No packages were installed, added, or upgraded during Phase 13. Verified: `git diff --stat c3d942e~1 HEAD -- pyproject.toml requirements.txt Makefile` is empty and the phase's changed-file set contains no dependency manifest. There is no supply-chain surface to audit for this phase; the risk is accepted as nil rather than mitigated by a control. | gsd-security-auditor | 2026-08-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-01 | 12 | 11 | 1 | gsd-security-auditor |
| 2026-08-01 (pass 2, re-audit @ `0794cdc`) | 12 | 12 | 0 | gsd-security-auditor |

**Pass 2 scope.** Re-audit after the T-13-09 fix (`f06f92a`) and the UF-1 enforcement commit
(`efc3571`). T-13-09 re-verified independently by tracing the generator through the real call
chain into `torch.multinomial` and by re-measuring the committed samples (the 151-char
prompt-20081 outlier is gone; leakage recount 79 / 69 matches both artifacts) — **closed, and
the two previously-false provenance sentences now match the implemented protocol.** T-13-07,
T-13-08 (guard specifically checked for weakening — intact, no force flag), T-13-10 (changed
proxy numbers re-traced) and T-13-11 (pre-reg section re-extracted, byte-identical) re-confirmed
closed; the frozen driver diff is still empty, so the remaining threats are unaffected by the
fix. UF-1 moved from inert-tripwire to enforced (drift-injection proved the new test fails).
UF-2, UF-3, UF-4, UF-5 remain open warnings; WARNING-2 and WARNING-3 are unchanged.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed — **0 open**; T-13-09 independently re-verified closed at pass 2
- [x] `status: verified` set in frontmatter

**Approval:** approved. All 12 threats closed. Four non-blocking warnings (UF-2 D-11 tolerance
reuses the claim margin, UF-3 run/regeneration provenance not retained in-repo, UF-4 read-side
inputs unpinned, UF-5 raw model output escapes its blockquote) carry to the next phase.
