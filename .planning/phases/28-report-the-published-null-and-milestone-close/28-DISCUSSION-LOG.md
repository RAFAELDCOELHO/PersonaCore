# Phase 28: Report, the Published Null, and Milestone Close - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-17
**Phase:** 28-report-the-published-null-and-milestone-close
**Areas discussed:** Todo fold-in, Where the null is published, Generated not authored, RPT-03 and
the debt ledger, Where milestone close ends, Ship decision, Figures, Hand-off boundary, v5.0 block

**Measurements taken during the discussion** (each one checked a stated premise before it was
accepted):

| Premise as stated | Measured | Outcome |
|---|---|---|
| SC3: `pyproject.toml` carries forward sha256-identical | `5065bc5` (2026-09-01) added `license = "MIT"`, pin `81d07d5d…` → `15ffd6b5…`; deps unchanged | **FALSE as written**; substance holds |
| SC4: "the DP arms take 32 replay windows per step" | `dp_replay_source`: 32 at n=8, **256 at n=64** | n=8 figure only |
| SC4: condition (c) fails on all 12 adversarial points | 6 `adv_n8` INCONCLUSIVE with (c) failing; 6 `adv_n64` REFUSED before (c) was applied | true of readings, not of verdicts |
| "recorded before any run" is citable | `c673b4c` (09:27) is an ancestor of `9bb34ad` (19:37), the first v4.0 result | provable by test |
| a 22.3 MB re-render read needs caching | `json.load` 0.056–0.063 s, sha256 0.011 s; 10 test files already read it | premise dropped |
| commit-order tests can't run in CI | `.github/workflows/ci.yml:28` sets `fetch-depth: 0` | premise dropped |
| σ ≥ 15.3 is planning prose only | `sigma_for(4.0, 200, 1e-5)` = 15.289937507119 on the frontier's own inputs | reproducible |
| DEF-17-01 "confirmed still open" | `make lint` → "All checks passed!"; fixed at `7b38e38` | stale reading |
| 24-UAT item 3: instrument consumed by nothing | `phase25_record.py:553` / `:574`; `refusal.by_family` in every point | closed by measurement |
| CI is current | last 6 runs on `main` green, but `main` is **27 commits ahead** of `origin/main` | Phase 27 never CI-run |

---

## Todo fold-in

| Option | Description | Selected |
|--------|-------------|----------|
| Fold it in | The ruling names Phase 28 as owner; its limitation list and obligations (a)-(f) go into CONTEXT.md | ✓ |
| Keep it separate | Leave the todo pending and listed under Deferred | |

**User's choice:** Fold it in.
**Notes:** "a própria proveniência já nomeia Phase 28 como dona, o planner não pode perder isso se
estiver explícito no contexto, não pendurado em lista separada de Deferred." Source correction
recorded during the discussion: the ruling was made at Phase 27's human verification
(`27-HUMAN-UAT.md`), not in plan 27-05.

---

## Where the null is published

| Option | Description | Selected |
|--------|-------------|----------|
| Results + limitations | One section: null, confound, canary, MOOT, ledger. Build decisions get pointers only | ✓ |
| Full M1/M2-style story | Adds per-decision narrative sections; ~3× the prose and bindings | |
| Results only | Limitations and ledger move to a separate generated file | |

**User's choice:** Results + limitations, one section, same file.
**Notes:** "Decisões de build recebem um ponteiro cada para seus registros de fase, nunca seção
própria duplicando narrativa já documentada em outro lugar. Menos prosa, menos vínculo — mesma
lição que a re-auditoria de v3.0 já mediu como causa direta de erro de contagem."

| Option | Description | Selected |
|--------|-------------|----------|
| Glance bullets, rendered | v3.0 + v4.0 bullets inserted, rendered by the same renderer, same byte test | ✓ |
| Dated section only | A `## v4.0 results` section like v3.0's; glance stays v2.0-only | |
| Both, glance authored | Bullets typed by hand with a numeric test | |

**User's choice:** Glance bullets, rendered.

| Option | Description | Selected |
|--------|-------------|----------|
| Quote, bracket, reproduce | Recorded quote + grid bracket + `sigma_for` at render time | ✓ |
| Quote + record bracket only | No number outside a committed record | |
| Quote only | Closest to SC1's literal wording | |

**User's choice:** Quote, bracket, reproduce.

| Option | Description | Selected |
|--------|-------------|----------|
| Verdict, then mechanism | Verbatim branch + existentials, then `cleared_counts` | ✓ |
| Mechanism first | Plain-language sentence first | |
| Verdict only | Breakdown moves to the first table | |

**User's choice:** Verdict, then mechanism.

| Option | Description | Selected |
|--------|-------------|----------|
| Right after the lead | n=64's control learned 87/1008; `L=64 → 9σ` quoted beside it | ✓ |
| In the n=64 subsection | Lead stays clean | |
| Limitations register only | A named-limitation row | |

**User's choice:** Right after the lead.

| Option | Description | Selected |
|--------|-------------|----------|
| One ε per σ | Each ε beside its `dp_n8` canary verdict; n=64 stated unauditable | ✓ |
| Per point, n=64 flagged | 15 ε values the canary never saw | |
| n=8 only | Hides that the formal claim is identical at n=64 | |

**User's choice:** One ε per σ.

---

## Generated, not authored

| Option | Description | Selected |
|--------|-------------|----------|
| Template with named bindings | Placeholders bound to record paths/constants; byte-identity re-render; template-source scan | ✓ |
| Authored prose + numeral scanner | Value-matching each numeral against declared sources | |
| Tables generated, prose reviewed | SC2's literal minimum | |

**User's choice:** Template with named bindings.
**Notes:** "um segundo teste escaneia o TEMPLATE e falha em qualquer numeral solto fora da gramática
de identificador — não checa o resultado renderizado por valor (fraco, '0' bate com qualquer coisa),
checa a fonte antes da renderização acontecer."

| Option | Description | Selected |
|--------|-------------|----------|
| Strict: identifiers only | Phase numbers, REQ-IDs, decision IDs, dates, SHAs, section refs, years | ✓ |
| Pragmatic: labels exempt too | n=8, K=48 and point keys treated as names | |

**User's choice:** Strict.

| Option | Description | Selected |
|--------|-------------|----------|
| Frozen at publish, dated continuation | Block pinned at commit; corrections appended with their own bindings | ✓ |
| Re-render in place | Template fixes rewrite published prose; git holds the diff | |
| Freeze prose, re-render tables | Tables may re-render if a record changes | |

**User's choice:** Frozen at publish, dated continuation.

---

## RPT-03 and the debt ledger

| Option | Description | Selected |
|--------|-------------|----------|
| Add a dependency-array test | `tomllib` comparison across v1.0/v2.0/v3.0/HEAD; hash pin demoted to change detector; test renamed | ✓ |
| Keep the hash pin only | Report the change in prose, no new test | |
| Re-pin to v3.0 bytes | Revert the MIT line | |

**User's choice:** Add a dependency-array test.
**Notes:** "Pin de hash mantido como detector de mudança, não mais prova de garantia substantiva. …
nome que afirma algo falso não sobrevive. Linha MIT publicada como um-liner datado, reconhecendo a
mudança sem reverter decisão já revisada."

| Option | Description | Selected |
|--------|-------------|----------|
| `results/phase28_ledger.json`, rendered | Row per item; counts derived by `len()`; no gate needed | ✓ |
| Planning-only ledger | Table in the milestone audit, summary line in REPORT.md | |
| Table in the template | Rows hand-typed with identifier-only text | |

**User's choice:** `results/phase28_ledger.json`, rendered.

| Option | Description | Selected |
|--------|-------------|----------|
| Record only | No archived file edited | |
| Fix the mechanical ones | Tags, frontmatter, artifact names | |
| Fix only what tooling reads | Frontmatter fields + stale artifact names that make `verify.artifacts` wrong | ✓ |

**User's choice:** Fix only what tooling reads.
**Notes:** "Tags soltas em prosa, o dígito extra de 77,6% — imperfeições que só afetam leitura humana
de texto histórico, nunca consumidas por ferramenta — ficam registradas, nunca editadas. … fechando
só o custo real e ativo que deixar tudo como registro permitiria continuar indefinidamente."

| Option | Description | Selected |
|--------|-------------|----------|
| One ledger, milestone column | v3.0 + v4.0 items in one file; SC3's 16+6 is a filtered view | ✓ |
| v3.0 only, per SC3 | Two lists to keep true | |
| Two files | Separate inheritance and limitation files | |

**User's choice:** One ledger, milestone column.

| Option | Description | Selected |
|--------|-------------|----------|
| One file, two renderings | Limitation register = ledger rows with `NAMED-LIMITATION` | ✓ |
| Separate register | Standalone file with its own bindings | |

**User's choice:** One file, two renderings.

| Option | Description | Selected |
|--------|-------------|----------|
| Short subsection, bound | The ~1,010× retraction and the σ=0 halt, numbers bound to phase 23 records | ✓ |
| Pointer only | One line with links | |
| Leave to the limitation register | Rows instead of narrative | |

**User's choice:** Short subsection, bound.

---

## Where milestone close ends

| Option | Description | Selected |
|--------|-------------|----------|
| Verdicts stand, fix the UAT stamp | 23/27 keep `human_needed` + ledger rows; 25's UAT stamp → `complete` | ✓ |
| Leave all three, ledger rows only | Nothing edited | |
| Ask for rulings first | Dated discharge files beside each verdict | |

**User's choice:** Verdicts stand, fix the UAT stamp.
**Notes:** "O selo de UAT de Phase 25 MUDA para complete, porque ele registra estado de fluxo de
trabalho (itens pendentes), não julgamento — e com zero itens pendentes, partial seria falso por
definição própria do campo, não proteção de veredito nenhuma."

| Option | Description | Selected |
|--------|-------------|----------|
| Dated note, row unchanged | Records filter-then-refuse at `:289-292` / `:300` | ✓ |
| Amend the wording | Rewrites a ticked requirement | |
| Hand to the milestone audit | Closes the milestone with a known-open item | |

**User's choice:** Dated note, row unchanged.

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, at a checkpoint you perform | Developer pushes; green CI over Phase 27 + report; run id in the ledger | ✓ |
| Defer to milestone close | complete-milestone owns push and verification | |
| Local `make test` is enough | No CI parity condition | |

**User's choice:** Yes, at a checkpoint you perform.

| Option | Description | Selected |
|--------|-------------|----------|
| Requirements, roadmap, state only | PROJECT.md, MILESTONES.md and the tag belong to complete-milestone | ✓ |
| Also PROJECT.md | Narrative twin written in-phase | |
| Everything in-phase | Workflows only verify | |

**User's choice:** Requirements, roadmap, state only.
**Notes:** "fronteira nomeada, não sobreposta, preservando a mesma disciplina de 'onde cada coisa
vive' que já protegeu cada decisão de escopo desta sessão."

---

## Ship decision, figures, v5.0

| Option | Description | Selected |
|--------|-------------|----------|
| Rendered from ledger + records | Withheld-claims list = `NAMED-LIMITATION` rows + existential fields | ✓ |
| Authored, v3.0 style | Prose ship decision with individually bound claims | |
| No ship section | Results and limitations only | |

**User's choice:** Rendered from ledger + records.

| Option | Description | Selected |
|--------|-------------|----------|
| Embed, rely on Phase 25's guards | Captions bound to record fields; no PNG byte test | ✓ |
| Embed with a re-render test | Red on a matplotlib upgrade | |
| Link only | Text-only section | |

**User's choice:** Embed, rely on Phase 25's guards.

| Option | Description | Selected |
|--------|-------------|----------|
| One rendered block | What v5.0 would re-measure, bound to the roadmap entry and WR-05 | ✓ |
| No future-work block | Measurement-only report | |

**User's choice:** One rendered block.

---

## Claude's Discretion

- Renderer and template file layout, names, marker naming, and whether a `make report` target exists
- Which tables exist beyond those the obligations force, and their column order
- Ledger schema keys beyond the required six; where the pinned date constant lives
- Test file naming, following the Phase 26/27 convention
- Section title wording, constrained to carry the branch name rather than describe it
- Plan and wave structure, and the sequencing of the two human checkpoints

## Deferred Ideas

- The v5.0 replay-bearing adversarial re-run (published as confounded here; measured there)
- Relearning as a diagnostic on the DP points that failed (b)
- Phase 22's WARNING-4 / WARNING-5 — ledger rows, fix deferred, not on the publishing path
- `scripts/phase18_extraction.py:85-87`'s throughput-comment debt — `FORBIDDEN-BY-GUARD`
- Erasure at higher adapter rank; the frozen-tokenizer retrain
- Publishing adapter weights for third-party reproduction
