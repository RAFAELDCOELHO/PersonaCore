---
phase: 12
slug: stage-2-conversational-fine-tune
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-01
---

# Phase 12 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| own checkpoint deserialization | `torch.load(weights_only=False)` on best.pt / per-arm latest / convbase_best.pt — project's OWN trusted artifacts only | model + optimizer state (trusted, local) |
| shippable artifact | convbase_slim.pt MUST load under `weights_only=True` (LOCKED contract — the artifact others may load) | model weights only, no pickled code |

No new network, user-input, or foreign-deserialization boundaries this phase.

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-12-01 | Tampering | training trajectory (v1.0 drift via loop edits) | mitigate | default-None kwargs (`loop.py:181-199`); golden-trajectory bit-identity (`test_loop_penalty_fn.py:108`); full suite 274 passed | closed |
| T-12-02 | Repudiation | CSV telemetry (columns appended to old files) | mitigate | per-run fieldnames (`loop.py:382`); DictWriter `extrasaction="raise"` (`logging.py:30`); `CSV_FIELDNAMES` untouched | closed |
| T-12-03 | Tampering | generate() (v1.0 drift via stop_ids edit) | mitigate | default-equivalence (`core.py:62,77`; `test_stop_ids.py:43`); test_generation.py green | closed |
| T-12-04 | Repudiation | gate-metric claim integrity (wrong denominator) | mitigate | hand-counted K=7 oracle + masking-selectivity tests (`test_masked_perplexity.py:29,60,71`) | closed |
| T-12-05 | Tampering | frozen sub-bin silent rebuild | mitigate | refuse-to-rerun SystemExit on both outputs (`build_retention_bin.py:66-73`); seeded local rng (line 95, SEED=1337) | closed |
| T-12-06 | Repudiation | anchor claim integrity (asserted-not-measured) | mitigate | anchors measured on best.pt, committed JSON with git_sha; fullval 2.10655 < 2.1066 proof (`build_retention_bin.py:159-177`; `results/retention_anchors.json`) | closed |
| T-12-07 | Spoofing | untrusted pickle load (retention bin build) | accept | TRUSTED-only comment on own-checkpoint load (`build_retention_bin.py:132-134`) — see Accepted Risks | closed |
| T-12-08 | Repudiation | thresholds chosen after seeing results | mitigate | git order proven (driver `10ba73e` ancestor of first CSV `7aac9e3`); blind K=2 + per-gate counterfactual_k in report | closed |
| T-12-09 | Tampering | smoke report/verdict overwritten | mitigate | `_never_clobber_guard()` SystemExit on non-PENDING verdict, both write paths (`finetune_smoke.py:710-718,749,1056`) | closed |
| T-12-10 | Spoofing | untrusted pickle load (smoke driver / Fisher) | accept | trusted-only comments on all `weights_only=False` sites; Fisher via `load_fisher(weights_only=True)` + fingerprint trio (`checkpoint.py:323-330`) — see Accepted Risks | closed |
| T-12-11 | Denial of service | multi-hour sequence lost to interruption | mitigate | SKIP-IF-DONE resume (`finetune_smoke.py:355-383`); absorbed a real mid-λ-100 kill with deterministic replay | closed |
| T-12-12 | Elevation of privilege | slim artifact carrying pickled code | mitigate | `export_slim` + in-driver `weights_only=True` load proof (`finetune_dialog.py:258,282`); live-proven: convbase_slim.pt loads under weights_only=True (101 tensors) | closed |
| T-12-13 | Repudiation | production run bypassing D-07 gate | mitigate | `_require_go_verdict` — three SystemExit paths, called before any training (`finetune_dialog.py:89-112,134`); recorded verdict GO | closed |
| T-12-14 | Tampering | Fisher/λ mismatch corrupting EWC arm | mitigate | fingerprint trio from anchor blob → `load_fisher(expected_fingerprint=...)`, hard ValueError on mismatch; `checkpoint_extra` self-contained resume (`finetune_dialog.py:177-178,243-248`) | closed |
| T-12-15 | Information disclosure | transcripts leaking non-corpus data | accept | prompts sourced exclusively from public PersonaChat val split (`make_transcripts.py:46,133`) — see Accepted Risks | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-12-01 | T-12-07, T-12-10 | `weights_only=False` used only on the project's own checkpoints; every load site carries a TRUSTED-only comment. Fisher cache and shippable convbase_slim.pt use the restricted `weights_only=True` unpickler. Residual: a locally tampered checkpoint executes code on load — no foreign files enter this path. | gsd-security-auditor | 2026-08-01 |
| AR-12-02 | T-12-15 | Generations conditioned only on public PersonaChat validation episodes; model trained only on public TinyStories + PersonaChat. No residual beyond public-corpus content. | gsd-security-auditor | 2026-08-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags (resolved)

- `scripts/finetune_smoke_stage3_override.py` — gate-halt override wrapper (surfaced from 12-04 SUMMARY body; no formal Threat Flags section existed). Verified in code against T-12-08's pre-registration discipline: re-evaluates Stage-2 gate arithmetic verbatim and SystemExits if any arm now passes (lines 76-82); calls pre-registered `stage3_lambda()`/`write_report()` unchanged (lines 160-162); commit `7b27a5b` is a proven git ancestor of the first λ CSV commit `814e58e`. Informational — resolved.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-01 | 15 | 15 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-01
