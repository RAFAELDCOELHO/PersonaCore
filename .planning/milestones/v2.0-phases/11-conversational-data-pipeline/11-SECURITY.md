---
phase: 11
slug: conversational-data-pipeline
status: verified
threats_open: 0
asvs_level: 1
created: 2026-07-31
---

# Phase 11 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| internet → data/raw/ | untrusted ~223 MB archive from an unowned CDN crosses into the repo working tree | PersonaChat tarball (public dataset, sha256-pinned) |
| data/raw text → parser | corpus text treated as trusted-after-verification (checksum-gated at fetch) | fb-dialog plain text |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-11-01 | Tampering | downloaded personachat.tgz | mitigate | sha256 vs pinned constant BEFORE `tarfile.open`, `SystemExit` on mismatch, HTTPS-only, re-verified every run (`scripts/fetch_personachat.py:71-79`) | closed |
| T-11-02 | Tampering | tar extraction paths | mitigate | two literal named members only via `tf.extract(..., filter="data")` (PEP 706); no `extractall` (`fetch_personachat.py:86-94`) | closed |
| T-11-03 | Tampering | parser/prepare script consuming corpus text | mitigate (11-04) / accept (11-01) | input only from checksum-gated extraction; strict 4-field split raises on malformed lines + zero-turn guard (`dialogue/parse.py:33-47`); episode-count sanity `SystemExit`s (`prepare_dialog_corpus.py:139-149`); `allowed_special="none"` blocks special-token injection (`serialize.py:76-81`) | closed |
| T-11-04 | Tampering | misaligned token/mask bins at train time | mitigate | length-equality `ValueError` in `get_batch_memmap_masked` (`training/data.py:112-116`), tested (`test_masked_batch.py:83-88`) | closed |
| T-11-05 | Spoofing/DoS | endpoint dead or moved (link rot) | transfer/accept | pre-registered S3 fallback endpoint with pin-on-first-fetch (fetch docstring); D-00 precious local cache; substitution recorded in 11-03-SUMMARY | closed |
| T-11-06 | Info Disclosure | re-hosting an unlicensed corpus | mitigate | `data/` gitignored (`.gitignore:17`), `git ls-files data/` empty, committed fixtures synthetic | closed |
| T-11-07 | Elevation (process) | bins built before gate verdict | mitigate | `_require_go_verdict` `SystemExit` as first statement of `main()` (`prepare_dialog_corpus.py:61-82,183`); verdict overwrite guard in `measure_inflation.py:69-75` | closed |
| T-11-SC | Tampering | package installs | accept | no packages installed this phase; `git log` confirms no dependency-file changes in any phase-11 commit | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-11-01 | T-11-SC | No packages installed during phase 11 (RESEARCH Package Legitimacy Audit: none); supply-chain surface unchanged | plan-time register (user-approved plans) | 2026-07-31 |
| AR-11-02 | T-11-05 (accept leg) | Link rot on the unowned CDN endpoint is transferred to the pre-registered fallback + precious local cache; residual risk (both endpoints dead AND cache lost) accepted | plan-time register (user-approved plans) | 2026-07-31 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-31 | 8 | 8 | 0 | gsd-security-auditor (register authored at plan time; post-review hardening commits c6f1db5..90b3a25 verified in place) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-31
