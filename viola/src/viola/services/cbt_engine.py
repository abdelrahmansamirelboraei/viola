from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CBTPlan:
    summary: str
    auto_thought: str
    distortions: List[str]
    socratic_questions: List[str]
    behavioral_step: str


class CBTEngine:
    def generate(self, analysis) -> CBTPlan:

        # 🚨 CRISIS MODE
        if getattr(analysis, "risk_flags", None):
            if "self_harm_language" in analysis.risk_flags:
                return CBTPlan(
                    summary="🚨 محتاج أتعامل مع كلامك بجدية شديدة.",
                    auto_thought="ذكرت أفكار عن إيذاء النفس.",
                    distortions=[],
                    socratic_questions=[
                        "هل أنت في خطر فوري الآن؟",
                        "هل في شخص قريب منك تقدر تتواصل معاه فورًا؟",
                    ],
                    behavioral_step=(
                        "من فضلك تواصل فورًا مع جهة طوارئ في بلدك.\n"
                        "لو في مصر: 122 (شرطة) أو 123 (إسعاف).\n"
                        "لو في بلد تانية: اتصل برقم الطوارئ المحلي حالًا.\n\n"
                        "لو تقدر، ابعد عن أي شيء ممكن يسبب أذى، "
                        "وتواصل مع شخص تثق فيه الآن."
                    ),
                )

        # fallback safe minimal CBT
        return CBTPlan(
            summary="خلينا نفهم أكتر اللي بيحصل جواك.",
            auto_thought=getattr(analysis, "auto_thought", ""),
            distortions=getattr(analysis, "distortions", []),
            socratic_questions=[
                "إيه أكتر حاجة مضايقاك دلوقتي؟",
                "إيه اللي خلاك تحس بالشكل ده النهاردة؟",
            ],
            behavioral_step="خلينا نبدأ بخطوة صغيرة: خُد نفس عميق وبعدين احكيلي أكتر."
        )
