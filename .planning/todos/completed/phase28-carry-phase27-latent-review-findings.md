---
id: phase28-carry-phase27-latent-review-findings
type: decision
resolves_phase: 28
created: 2026-09-16
status: resolved
decided_by: developer
---

# Phase 28 — carry Phase 27's latent review findings as NAMED LIMITATIONS; no adv_* admission until v5.0

Ruled by the developer on 2026-09-16 at Phase 27's human verification (`27-HUMAN-UAT.md`), after
`27-VERIFICATION.md` (commit `0ab0e53`) reproduced every Critical and Warning of `27-REVIEW.md`
(commit `a1dec50`) and falsified none. All are latent under the MOOT reading: every attack leg
refuses on the committed record `results/phase27_admission.json` (operator commit `88dff77`).

## Ruling 1 — named limitations, the record is not re-issued

Phase 28 publishes these beside RELRN-02..05 (the D-05 limitation) in its named-limitation list:

- **CR-01** — the D-18 attacker-corpus bin pin in `train_relearn_arm` disables itself on row-level corpus drift.
- **CR-02** — a leg passes `_require_admitted` with a tracked-but-edited record or an out-of-tree `--record`, and trusts the record's admitted keys over the frontier (no leg-time `frontier_sha256` / key re-derivation).
- **WR-02** — `structural-proof` exits 0 without every mitigated reading and records (does not refuse) diverging offset streams.
- **WR-03** — a live leg writes `run.csv` under `results/phase27_*` (not gitignored; matches `ARTIFACT_GLOB`).
- **WR-06** — the required `baseline` never moves the verdict; a re-run of `gate` overwrites the published output.
- inconsequential: **WR-01** (`admit` cannot write an INCONCLUSIVE record — conservative), **WR-04** (`on_draw` records nothing on the unmasked/fact-aligned branches the driver never takes).

**Obligation on the first phase that reads ADMITTED**, before its first leg, in its continuation
driver / pre-registration continuation (never an edit of `scripts/phase27_prereg.py`, whose ancestry
guard would redden, nor of the modules the record's `provenance.module_sha256` pins):
(a) refuse unless both corpus pins hold (CR-01); (b) compare the record's bytes with HEAD, re-derive
`admitted_point_keys` and check `frontier_sha256` at leg time (CR-02); (c) require every expected arm
reading and refuse on diverging streams (WR-02); (d) route run CSVs under the gitignored out-dir
(WR-03); (e) pre-register one gate baseline per leg and refuse to overwrite a gate output (WR-06);
(f) enforce Ruling 2 before any `adv_*` admission.

## Ruling 2 — WR-05: no adversarial point is admissible until v5.0

The driver would calibrate an adversarial point's Z threshold against the DP control
(`dp_n8` taught 790/1008 → 0.5486), while the frontier judged `adv_n8` against its own control
(879/1008 → 0.6104); D-12/D-24/D-28 never covered the arm. Ruling: no `adv_*` point is admissible
until the v5.0 adversarial re-measurement (Phase 28 SC4's deferral) pins the adversarial arm's own
control; DP-control calibration of adversarial points is not accepted. Latent today: 0 of 12
adversarial points admissible (6 INCONCLUSIVE, 6 REFUSED).

---

**Resolved 2026-09-21 (plan 28-03):** carried into `results/phase28_ledger.json` as rows CR-01, CR-02, WR-01, WR-02, WR-03, WR-04, WR-05, WR-06 (Ruling 1 and Ruling 2, category `review-finding`) and OBLIG-A, OBLIG-B, OBLIG-C, OBLIG-D, OBLIG-E, OBLIG-F (obligations (a)-(f) verbatim, category `inherited-obligation`), all `NAMED-LIMITATION`; the report renders them via D-30.
