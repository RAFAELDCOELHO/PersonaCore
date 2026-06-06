"""Text generation toolkit — public import surface (GEN-01 / GEN-02).

Re-exports the pure sampling transforms (06-01) and the shared ``generate`` / ``collect``
decode core (06-02). The ``generate_text`` streaming wrapper (06-03) joins this barrel when
it lands — do not import ``text`` here yet (it does not exist).
"""

from .core import collect, generate
from .sampling import apply_temperature, next_token, top_k_filter, top_p_filter

__all__ = [
    "apply_temperature",
    "collect",
    "generate",
    "next_token",
    "top_k_filter",
    "top_p_filter",
]
