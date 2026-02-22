from __future__ import annotations

import re

# NOTE: English comments as requested.
# This normalizer is intentionally simple (rules-based) to improve pattern matching.
# It can be expanded later with dialect mappings and tokenization.

_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"

# Common Arabic letter normalization
_TRANSLATION_TABLE = str.maketrans({
    # Alef variants -> Alef
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    # Hamza on waw/ya -> basic letters
    "ؤ": "و",
    "ئ": "ي",
    # Alef maqsura -> ya
    "ى": "ي",
    # Ta marbuta -> ha (helps some matches; can be debated)
    "ة": "ه",
})

# Normalize punctuation/spaces
_MULTI_SPACE = re.compile(r"\s+")
# Keep Arabic letters, numbers, and basic punctuation; replace others with space
_NON_WORD = re.compile(r"[^\w\u0600-\u06FF]+", re.UNICODE)

def normalize_arabic(text: str) -> str:
    if not isinstance(text, str):
        return ""

    t = text.strip()

    # Remove tatweel
    t = t.replace(_TATWEEL, "")

    # Remove Arabic diacritics
    t = _DIACRITICS.sub("", t)

    # Normalize letters
    t = t.translate(_TRANSLATION_TABLE)

    # Normalize punctuation to spaces (light)
    t = _NON_WORD.sub(" ", t)

    # Normalize spaces
    t = _MULTI_SPACE.sub(" ", t).strip()

    return t
