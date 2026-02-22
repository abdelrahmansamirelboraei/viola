from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal, Optional


InputType = Literal["text", "audio"]


@dataclass
class Transcript:
    text: str
    segments: Optional[List[Dict[str, Any]]] = None


@dataclass
class AnalysisResult:
    # Indicators only (MVP)
    emotion_scores: Dict[str, float]
    distortions: List[str]
    summary: str
    auto_thought: str


@dataclass
class CBTResponse:
    # The CBT-style output to show the user
    summary: str
    auto_thought: str
    distortions: List[str]
    socratic_questions: List[str]
    behavioral_step: str


@dataclass
class SessionReport:
    session_id: str
    input_type: InputType
    language: str
    audio_path: Optional[str]
    raw_text: Optional[str]
    transcript: Optional[str]
    analysis: Dict[str, Any]
    cbt: Dict[str, Any]
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

