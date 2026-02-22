from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from typing import Optional, Dict, Any


HIGH_KEYWORDS = [
    "انتحر", "انتحار", "عايز انتحر",
    "أقتل نفسي", "اقتل نفسي",
    "هموت نفسي", "أؤذي نفسي", "اذي نفسي"
]

SAFE_YES = {"انا بأمان", "أنا بأمان", "انا بأمان الآن", "أنا بأمان الآن", "بأمان"}
SAFE_NO  = {"مش بأمان", "مش بأمان الآن", "مش امان", "مش آمان"}


def _get_or_init_extra(session) -> Dict[str, Any]:
    """
    Returns a mutable dict stored in session.metadata.extra.
    - If metadata.extra is None, create a new dict via dataclasses.replace(metadata, extra=...).
    - Never assign to metadata.extra directly because metadata may be frozen.
    """
    md = session.metadata
    extra = getattr(md, "extra", None)

    if isinstance(extra, dict):
        return extra

    # extra is None or not a dict -> create dict and attach via replace
    new_extra: Dict[str, Any] = {}

    try:
        if is_dataclass(md):
            session.metadata = replace(md, extra=new_extra)
            return session.metadata.extra  # type: ignore[attr-defined]
    except FrozenInstanceError:
        # If md is frozen AND session.metadata assignment fails (rare), we still return local dict
        return new_extra

    # Fallback: if not a dataclass, try object setattr
    try:
        object.__setattr__(md, "extra", new_extra)
    except Exception:
        pass
    return new_extra


def apply_safety_gate(text: str, session) -> Optional[str]:
    """
    Returns:
        - crisis_response (str) if crisis mode should override normal CBT
        - None if pipeline should continue normally
    """
    normalized = (text or "").strip().lower()

    extra = _get_or_init_extra(session)
    safety: Dict[str, Any] = extra.setdefault("safety", {})

    crisis_mode = bool(safety.get("crisis_mode", False))
    safe_confirmed = bool(safety.get("safe_confirmed", False))

    # --- Explicit safety confirmation ---
    if normalized in SAFE_NO:
        safety["crisis_mode"] = True
        safety["safe_confirmed"] = False
        safety["low_streak"] = 0
        return (
            "🚨 Crisis Mode\n\n"
            "تمام. بما إنك **مش بأمان**: أهم حاجة دلوقتي الأمان.\n"
            "هل أنت في خطر فوري الآن؟ لو نعم اتصل بالطوارئ فورًا.\n"
            "في مصر: 122 أو 123. في بلد تانية: رقم الطوارئ المحلي.\n"
            "لو تقدر: ابعد عن أي وسيلة أذى، وكلم شخص قريب منك الآن.\n\n"
            "اكتب: (أنا بأمان) لو الوضع اتغيّر."
        )

    if normalized in SAFE_YES:
        safety["safe_confirmed"] = True
        safety["crisis_mode"] = True  # keep it until we decide to exit (later)
        safety["low_streak"] = int(safety.get("low_streak", 0))
        return (
            "✅ تمام. هنكمل بهدوء.\n\n"
            "لو رجعت أفكار إيذاء النفس تاني، قولّي فورًا.\n"
            "دلوقتي قولي: تحب نبدأ منين؟"
        )

    # --- Detect high risk ---
    if any(k in normalized for k in HIGH_KEYWORDS):
        safety["crisis_mode"] = True
        safety["safe_confirmed"] = False
        safety["low_streak"] = 0
        return (
            "🚨 Crisis Mode\n\n"
            "أنا باخد كلامك بجدية.\n"
            "هل أنت في خطر فوري الآن؟\n"
            "هل تقدر تتواصل مع شخص قريب منك فورًا؟\n\n"
            "لو في خطر فوري: اتصل بالطوارئ الآن.\n"
            "في مصر: 122 أو 123.\n\n"
            "اكتب: (أنا بأمان) أو (مش بأمان)"
        )

    # --- If already in crisis and not confirmed safe, keep gate ON ---
    if crisis_mode and not safe_confirmed:
        return (
            "🚨 قبل ما نكمل أي موضوع، محتاج أتأكد إنك بأمان.\n"
            "اكتب: (أنا بأمان) أو (مش بأمان)"
        )

    return None
