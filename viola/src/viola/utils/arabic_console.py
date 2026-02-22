from __future__ import annotations

import arabic_reshaper
from bidi.algorithm import get_display


def ar(text: str) -> str:
    # Reshape Arabic letters then apply bidi algorithm for RTL display in LTR terminals
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped, base_dir="R")