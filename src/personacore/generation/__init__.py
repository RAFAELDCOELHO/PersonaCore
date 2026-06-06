"""Text generation toolkit — public import surface (GEN-01).

Re-exports the pure sampling transforms. The ``generate`` / ``collect`` core (06-02) and the
``generate_text`` streaming wrapper (06-03) join this barrel as they land — do not import
``core``/``text`` here yet (they do not exist).
"""

from .sampling import apply_temperature, next_token, top_k_filter, top_p_filter

__all__ = [
    "apply_temperature",
    "next_token",
    "top_k_filter",
    "top_p_filter",
]
