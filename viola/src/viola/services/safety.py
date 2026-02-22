from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RiskAssessment:
    level: RiskLevel
    score: int
    signals: list[str]


_AR_SUICIDE = [
    "انتحر", "انتحار", "أنتحر", "عايز انتحر", "هنتحر",
    "هموت نفسي", "أقتل نفسي", "اقتل نفسي",
    "إيذاء النفس", "أذى نفسي", "أؤذي نفسي"
]
_AR_INTENT = ["هعمل", "هخلص", "النهارده", "دلوقتي", "حالاً", "حالا"]
_AR_PLAN = ["خطة", "طريقة", "وسيلة", "حبوب", "سم", "سلاح", "شنق", "قفز", "جرعة"]


def assess_risk_ar(text: str) -> RiskAssessment:
    t = (text or "").strip().lower()
    score = 0
    signals: list[str] = []

    if any(k in t for k in _AR_SUICIDE):
        score += 70
        signals.append("suicidal_ideation")

    if any(k in t for k in _AR_INTENT):
        score += 15
        signals.append("intent_or_urgency")

    if any(k in t for k in _AR_PLAN):
        score += 20
        signals.append("plan_or_means")

    if re.search(r"(مش هأذي نفسي|مش هاقتل نفسي|مش هنتحر|انا بأمان|أنا بأمان)", t):
        score -= 40
        signals.append("safety_denial")

    if score >= 70:
        lvl = RiskLevel.HIGH
    elif score >= 35:
        lvl = RiskLevel.MEDIUM
    else:
        lvl = RiskLevel.LOW

    return RiskAssessment(level=lvl, score=score, signals=signals)
