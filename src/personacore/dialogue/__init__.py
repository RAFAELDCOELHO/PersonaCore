"""Phase 11 — conversational data pipeline (DATA-01..02, DATA-04): public import surface.

Plan 11-01 ships ``parse_episodes`` (from-scratch fb-dialog parser, DATA-01), plus the
serialization trio ``detokenize`` (D-06 regex normalizer), ``render_document`` (D-04 role-token
document form), and ``encode_dialogue`` (span-wise id+mask encoder with D-01 semantics) — the
single source of truth every downstream consumer (inflation gate, bins) tokenizes through.
Plan 11-03 adds ``compute_inflation_metrics`` (the four D-08 gate metrics, DATA-04).
"""

from .inflation import compute_inflation_metrics
from .parse import parse_episodes
from .serialize import PERSONA_CAP, cap_persona, detokenize, encode_dialogue, render_document

__all__ = [
    "PERSONA_CAP",
    "cap_persona",
    "compute_inflation_metrics",
    "detokenize",
    "encode_dialogue",
    "parse_episodes",
    "render_document",
]
