from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass(frozen=True)
class CrisisResponse:
    crisis_flag: bool
    message: str
    steps_now: List[str] = field(default_factory=list)
    seek_help: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crisis_flag": self.crisis_flag,
            "message": self.message,
            "steps_now": self.steps_now,
            "seek_help": self.seek_help,
            "metadata": self.metadata,
        }


class CrisisResponder:
    def build(self, crisis_signals: List[str] | None = None) -> CrisisResponse:
        crisis_signals = crisis_signals or []

        message = (
            "أنا واخد كلامك بجد. لو أنت في خطر دلوقتي أو ناوي تأذي نفسك، "
            "الأهم إنك تطلب مساعدة فورية حالًا."
        )

        steps_now = [
            "لو تقدر: ابعد عن أي حاجة ممكن تستخدمها في أذى نفسك، وروّح لمكان فيه ناس حواليك.",
            "اتصل فورًا بشخص قريب منك تثق فيه وخليه يفضل معاك (مكالمة أو حضور).",
            "لو الخطر فوري: اتصل برقم الطوارئ في بلدك أو اذهب لأقرب مستشفى/طوارئ حالًا.",
            "خد نفس ببطء 4 ثواني… وطلع النفس 6 ثواني… كرر 5 مرات (بس لتقليل التوتر اللحظي).",
        ]

        seek_help = [
            "لو تقدر دلوقتي: تواصل مع مختص نفسي (طبيب/أخصائي) أو خدمات الطوارئ.",
            "لو مش قادر تتواصل مع مختص: خليك مع صديق/قريب بدل ما تبقى لوحدك.",
            "لو تحب: قولّي أنت دلوقتي لوحدك ولا مع حد؟ (ده سؤال أمان، مش تفاصيل مؤذية).",
        ]

        return CrisisResponse(
            crisis_flag=True,
            message=message,
            steps_now=steps_now,
            seek_help=seek_help,
            metadata={"engine": "crisis_v1", "signals": crisis_signals},
        )
