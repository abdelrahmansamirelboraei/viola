from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from viola.core.types.analysis import TextAnalysis
from viola.cbt.rules.ar_cbt_templates import QUESTIONS, REFRAMES, EXERCISES


@dataclass(frozen=True)
class CbtIntervention:
    distortion: str
    questions: List[str] = field(default_factory=list)
    reframes: List[str] = field(default_factory=list)
    exercises: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(frozen=True)
class CbtPlan:
    severity: int
    top_emotion: Optional[str]
    interventions: List[CbtIntervention] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "top_emotion": self.top_emotion,
            "interventions": [
                {
                    "distortion": x.distortion,
                    "confidence": x.confidence,
                    "questions": x.questions,
                    "reframes": x.reframes,
                    "exercises": x.exercises,
                }
                for x in self.interventions
            ],
            "notes": self.notes,
        }


class CbtEngine:
    def build_plan(self, analysis: TextAnalysis, max_distortions: int = 2) -> CbtPlan:
        top_emotion = analysis.top_emotion().name if analysis.top_emotion() else None

        # pick top distortions
        distortions = analysis.distortions[:max_distortions]

        interventions: List[CbtIntervention] = []
        for d in distortions:
            interventions.append(
                CbtIntervention(
                    distortion=d.name,
                    confidence=d.confidence,
                    questions=QUESTIONS.get(d.name, [])[:4],
                    reframes=REFRAMES.get(d.name, [])[:2],
                    exercises=EXERCISES.get(d.name, [])[:2],
                )
            )

        notes: List[str] = []
        if analysis.crisis_flag:
            notes.append("CRISIS_FLAG: route to crisis-mode response and encourage immediate support.")

        if not interventions:
            notes.append("No distortions detected. Use supportive reflection + gentle check-in questions.")

        return CbtPlan(
            severity=analysis.severity,
            top_emotion=top_emotion,
            interventions=interventions,
            notes=notes,
        )
