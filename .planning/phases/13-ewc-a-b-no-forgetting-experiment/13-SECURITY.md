---
phase: 13
slug: ewc-a-b-no-forgetting-experiment
status: draft
threats_open: 1
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
| T-13-09 | Repudiation | cherry-picking accusation surface | mitigate | seeded prompt selection, one-run both-arms protocol, proxies over ALL generations, **stated in the file header** | **OPEN** |
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
  logged as unregistered surface UF-1 below.

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

### T-13-08 — Tampering, samples / figures overwrite — CLOSED

- Samples guard `scripts/make_retention_samples.py:119-126` — `SystemExit` naming the file,
  raised **first** in `main()`, before checkpoint loads.
- Figures: `plot_forgetting_curve(out_dir)` / `plot_frontier(out_dir)` are `out_dir`-parameterized
  so the smoke test renders into `tmp_path`; both PNGs regenerate byte-identically (SHA-256) from
  the committed CSVs per 13-VERIFICATION, so overwrite is recoverable by design.

### T-13-09 — Repudiation, cherry-picking accusation surface — **OPEN (BLOCKER)**

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

**To close, either:** (A) thread a per-prompt `torch.Generator(device="cpu").manual_seed(SEED +
story_idx)` into the warm `_complete()` call and regenerate the samples, keeping the claim; or
(B) keep the artifact and correct both sentences to state that streams are aligned only up to the
first early stop (EWC arm, prompt 20081, 6th of 10), plus a threats-register line.

### T-13-10 — Repudiation, report numbers provenance — CLOSED (with WARNING-2)

- `## Evidence Index` maps every artifact to its role and states the tracing rule.
- The λ=0 frontier point carries its exception row under `## Pre-Registration` ("Provenance
  exception", `ft_lr_9e-5.csv` has no `retention_ppl`, cited to `666d096`, "not recomputed here").
- 13-VERIFICATION independently re-derived the 2×2 cells, the gate verdict (33.6068×), all 16
  trajectory deltas and all six D-11 cells from the committed CSVs — exact matches.
- **WARNING-2:** the pre-registered gate `ewc_mitigates` is executed by no shipping code path —
  only by `tests/test_phase13_driver.py` and by ad-hoc session commands. The published verdict is
  reproducible but is not the output of a committed artifact-producing step. Secondly, the report
  publishes the sample proxies (79 / 70, 0/20, 1/20), which are non-CSV numbers sourced from
  `phase13_retention_samples.md` — traceable to a committed artifact (so provenance holds), but
  from the artifact whose pairing claim is open under T-13-09.

### T-13-11 — Tampering, pre-registration table drift — CLOSED

`git diff 8fa2aa1 HEAD -- results/phase13_ab_report.md` removes exactly seven lines, all of them
`_Pending — filled by Plan 13-04 after both arms run._` placeholders. Every pre-registration table
row is byte-unchanged from the pre-run commit.

### T-13-SC — Tampering, package installs — ACCEPTED, verified

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
| UF-1 | D-11 reference input integrity | Tampering (read side) | `finetune_ab.py:105-106` literals used only in `print()` at `:347`; the only enforced comparison (`:350`) is against the mutable `results/finetune_prod.csv` parsed at `:333-336` | T-13-01 / T-13-04 cover **write** targets only. Sound in fact today (`finetune_prod.csv` untouched since `87198ec`; run log shows +0.000000 deltas vs the literals), but the declared tripwire does not exist for any future re-run |
| UF-2 | D-11 tolerance reuses the claim margin | Tampering | `finetune_ab.py:350` — `abs(ret − prod) > MARGIN`, where MARGIN is the minimum effect size allowed to *claim* mitigation | A reproduction drift of one full claim margin passes silently; observed drift is ~1e-7, so a tolerance five orders tighter is available. A separate `REPRO_TOL` would make the two quantities distinct |
| UF-3 | Run-provenance logs not retained in-repo | Repudiation | no `results/phase13_*_run.log` in `git ls-files`; echoes exist only in an ephemeral scratchpad | See T-13-05 WARNING-3; Phase 12 committed its analogue |
| UF-4 | Read-side inputs unvalidated | Tampering | `make_retention_samples.py:106-115` accepts any blob at the arm checkpoint paths (no `step == 4000`, no cross-arm `git_sha`/`train_config` equality, no `ewc_lambda` asymmetry check); `finetune_ab.py:230, 249-252` trusts `retention_anchors.json` for the step-0 retention point with no pin to `best.pt`, although the JSON carries its own `git_sha` | The phase's artifact-isolation discipline (D-07 / WR-02) is write-side only; nothing pins the artifacts being *read* |
| UF-5 | Raw model output escapes its blockquote in committed evidence | Tampering (rendered artifact integrity) | `make_retention_samples.py:219, 229, 233` interpolate `f"> {text}"`; multi-line completions leave 21 of 40 sample blocks partly outside the quote (measured on the committed markdown) | Generated text — including literal `<\|user\|>` / `<\|assistant\|>` role tokens, the very contamination being measured — renders as document prose, visually indistinguishable from the script's own claims |

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

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [ ] `threats_open: 0` confirmed — **1 open (T-13-09)**
- [ ] `status: verified` set in frontmatter

**Approval:** pending — T-13-09 must be closed (regenerate with a per-prompt generator, or correct
the two provenance sentences and add a threats-register line) before this phase ships.
