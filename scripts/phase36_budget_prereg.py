"""Phase 36 fill of v6_budget_and_stop_line: the v6.0 MPS budget and stop line.

Committed after Rafael's approved (36-CONTEXT D-16 / Addendum Q4), in its own commit, before
results/phase36_budget.json. Every number is derived from the five committed probe records by
phase36_budget; RULING holds Rafael's rulings and his approved reply verbatim.

Frozen once results/phase36_budget.json exists: any correction is a dated continuation module,
never an edit.
"""

import phase35_prereg
import phase36_budget

RULING = {
    "unit_caps": {
        "E1": {
            "calibrations": 4,
            "cells": 16,
            "checkpoints_per_cell": 5,
            "k48_confirms_per_cell": 1,
        },
        "E2": {"adapters": 2, "seeds": 5},
        "E3": {"max_batch": 8, "max_steps": 800, "recipes": 4, "sigmas": 3},
        "E4": {"points": 3},
        "E5": {"max_set_size": 512, "prefixes": 6, "sets": 8},
        "E6": {
            "a2_regenerated_entries": 0,
            "adapters": 7,
            "anchor_adapters": 7,
            "anchor_slots": 8,
            "entries": 216,
            "max_k": 48,
        },
    },
    "cuts": {},
    "divergences_investigated": {},
    "price_rulings": {"single_run_draw_loop": "spread_scaled"},
    "cap_rulings": {
        "E6.a2_regenerated_entries": "Rafael (2026-10-02): a geração no contexto A2 "
        "não é refeita. Reaproveitar os registros "
        "commitados a K = 48, verificados por SHA-256 — "
        "k = 0: results/phase18_arm_adapter-on.json "
        "sha256 "
        "71fb062779b6b4c21f09636f6fcfa99b1052aa2685450cfce87bf799c85c4c7c; "
        "k = 8: results/erasure_kstar_arm_k008.json "
        "sha256 "
        "d4ee51c16e239d6afc6cdb12d875224c5706ba3c1e43f6d5f4a3dfdf1ec017bc; "
        "k = 16: results/erasure_kstar_arm_k016.json "
        "sha256 "
        "944ed82179ce158ec0b6cb244e5a25993e1a02921f6c5460e6c8b563c57f0c18; "
        "k = 32: results/erasure_kstar_arm_k032.json "
        "sha256 "
        "f595b0c8e8435f1d4c10708f1c98f193b5bffd3019ce60e102a786e6c4e1b721; "
        "k = 64: results/erasure_kstar_arm_k064.json "
        "sha256 "
        "051a3ee4fcb146932d773b6b9e72afff0eb448282f2fc5c8c12ccc44299c08ab; "
        "k = 78: results/phase19_arm_erased.json sha256 "
        "c10313a75a233cddf75ab51d21e9db8e8a3788ecae15163d7e2dc0c78677e505; "
        "M2: results/phase19_arm_retrain.json sha256 "
        "fd3499397e269590ee514d9b0d465203d87c3d721af2e70c89fcf6dce83bdb42. "
        "O orçamento do E6 cobre só a geração na âncora "
        "e a pontuação de NLL e rank. Teto: entradas A2 "
        "re-geradas = 0. Se a Fase 39 achar um registro "
        "que não serve, ela pausa e pergunta a Rafael; "
        "não regenera sozinha."
    },
    "approved": "approved: total e frentes como na tabela do dry com os três itens; linha de "
    "parada 90 h; S = 5; reserva do E4 com 3 pontos; 4 receitas; lote 8; 5 pontos de "
    "checagem por célula; E6 com a2_regenerated_entries = 0 e entries = 216.",
}

_PROBES = phase36_budget.probe_record_paths()
_CHOSEN = phase36_budget.chosen(_PROBES, **RULING)

V6_BUDGET_AND_STOP_LINE = phase35_prereg.fill(
    "v6_budget_and_stop_line",
    front_hours=_CHOSEN["front_hours"],
    stop_line_hours=_CHOSEN["stop_line_hours"],
    e2_seed_count=_CHOSEN["e2_seed_count"],
    input_records=_PROBES,
    derivation=phase36_budget.derivation(_CHOSEN, _PROBES, **RULING),
)
