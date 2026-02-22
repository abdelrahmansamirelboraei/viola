from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class DistortionHit:
    name: str
    confidence: float  # 0..1
    signals: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EmotionHit:
    name: str
    confidence: float  # 0..1
    signals: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TextAnalysis:
    text: str
    severity: int  # 0..100
    emotions: List[EmotionHit] = field(default_factory=list)
    distortions: List[DistortionHit] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    crisis_flag: bool = False
    crisis_signals: List[str] = field(default_factory=list)

    def top_emotion(self) -> Optional[EmotionHit]:
        return max(self.emotions, key=lambda e: e.confidence, default=None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "severity": self.severity,
            "emotions": [
                {"name": e.name, "confidence": e.confidence, "signals": e.signals}
                for e in self.emotions
            ],
            "distortions": [
                {"name": d.name, "confidence": d.confidence, "signals": d.signals}
                for d in self.distortions
            ],
            "crisis_flag": self.crisis_flag,
            "crisis_signals": self.crisis_signals,
            "metadata": self.metadata,
        }
