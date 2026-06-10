"""Text generation toolkit — public import surface (GEN-01 / GEN-02).

Re-exports the pure sampling transforms (06-01), the shared ``generate`` / ``collect`` decode
core (06-02), the ``generate_text`` / ``generate_text_str`` streaming text wrapper (06-03),
and the ``generate_text_cumulative`` Gradio-shaped adapter (08-02 / DEMO-01).
"""

from .core import collect, generate
from .sampling import apply_temperature, next_token, top_k_filter, top_p_filter
from .text import generate_text, generate_text_cumulative, generate_text_str

__all__ = [
    "apply_temperature",
    "collect",
    "generate",
    "generate_text",
    "generate_text_cumulative",
    "generate_text_str",
    "next_token",
    "top_k_filter",
    "top_p_filter",
]
