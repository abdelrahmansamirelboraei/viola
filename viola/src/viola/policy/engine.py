from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from viola.memory.store import MemoryStore


@dataclass(frozen=True)
class PolicyContext:
    user_id: str
    last_severity: Optional[int] = None
    avg_severity: float = 0.0
    last_checkin_mood: Optional[int] = None
    avg_checkin_mood: float = 0.0
    top_distortion: Optional[str] = None
    top_emotion: Optional[str] = None
    trend_7d: str = "غير كافي"
    flags: List[str] = field(default_factory=list)


class ResponsePolicy:
    """
    Decides response tone + extra nudges based on memory summary + recent events.
    """

    def build_context(self, user_id: str, days: int = 7) -> PolicyContext:
        store = MemoryStore()
        summary = store.get_summary(user_id)
        events = store.get_events_since_days(user_id=user_id, days=days)

        sev_list: List[int] = [e.get("severity") for e in events if isinstance(e.get("severity"), int)]
        trend = self._trend(sev_list)

        flags: List[str] = []

        last_sev = summary.get("last_severity")
        if not isinstance(last_sev, int):
            last_sev = None

        avg_sev = float(summary.get("avg_severity", 0.0) or 0.0)

        last_mood = summary.get("last_checkin_mood")
        if not isinstance(last_mood, int):
            last_mood = None

        avg_mood = float(summary.get("avg_checkin_mood", 0.0) or 0.0)

        top_dist = summary.get("top_distortion_overall")
        if not isinstance(top_dist, str):
            top_dist = None

        top_emo = summary.get("top_emotion_overall")
        if not isinstance(top_emo, str):
            top_emo = None

        # Flags (simple heuristics)
        if last_sev is not None and last_sev >= 75:
            flags.append("high_severity_recent")

        if trend == "🔺 بيزيد":
            flags.append("deteriorating_trend")

        if last_mood is not None and last_mood <= 35:
            flags.append("low_mood_recent")

        if (trend == "🔺 بيزيد") and (last_mood is not None and last_mood <= 35):
            flags.append("needs_extra_support")

        return PolicyContext(
            user_id=user_id,
            last_severity=last_sev,
            avg_severity=avg_sev,
            last_checkin_mood=last_mood,
            avg_checkin_mood=avg_mood,
            top_distortion=top_dist,
            top_emotion=top_emo,
            trend_7d=trend,
            flags=flags,
        )

    def decide_style(self, ctx: PolicyContext) -> Dict[str, Any]:
        """
        Returns a style dict used by formatter:
        - intro
        - closing
        - nudges (list)
        - intensity (soft/normal/firm)
        """
        intensity = "normal"
        nudges: List[str] = []

        intro = "🟣 Viola — معاك خطوة بخطوة."
        closing = "لو تحب، رد على سؤال واحد بس من اللي فوق ونكمل سوا."

        if "needs_extra_support" in ctx.flags:
            intensity = "soft"
            intro = "🟣 Viola — واضح إن الأسبوع صعب عليك. خلّينا ناخدها بهدوء وبخطوة صغيرة."
            nudges.append("لو تقدر: ابعد عن العزلة واتكلم مع شخص قريب منك حتى لو 5 دقائق.")
            nudges.append("خلّينا نركّز على أمانك وتهدئة جسمك الأول (تنفس 4-6 دقيقتين).")
            closing = "أنا معاك. قولّي: دلوقتي لوحدك ولا مع حد؟"

        elif "deteriorating_trend" in ctx.flags:
            intensity = "firm"
            intro = "🟣 Viola — في مؤشرات إن الضغط بيزيد. هنحتاج نظام أبسط وثابت."
            nudges.append("اختار تمرين واحد يوميًا (5-10 دقايق) بدل ما تحاول تعمل كل حاجة مرة واحدة.")
            nudges.append("لو الشدة عالية جدًا أو في أفكار مؤذية، اطلب دعم فوري من شخص قريب/مختص.")
            closing = "اختار تمرين واحد من تحت وقلّي هتعمله امتى النهارده."

        elif "high_severity_recent" in ctx.flags:
            intensity = "soft"
            intro = "🟣 Viola — الشدة عالية شوية. خلّينا نهدّي الأول وبعدين نفكك الفكرة."
            nudges.append("قبل أي تحليل: تنفّس 4-6 لمدة دقيقتين.")
            closing = "بعد التنفس، قولي: إيه جملة واحدة بتلخص الفكرة اللي مزعجاك؟"

        elif "low_mood_recent" in ctx.flags:
            intensity = "soft"
            intro = "🟣 Viola — مزاجك واطي الفترة دي. ده مفهوم. هنمشي بخطوات صغيرة جدًا."
            nudges.append("حتى لو مش قادر: خطوة 5 دقايق كفاية النهارده.")
            closing = "اختار أصغر خطوة ممكنة (حتى 5 دقايق) وقلّي هتعمل إيه."

        else:
            # Positive trend option
            if ctx.trend_7d == "🔻 بيتحسن":
                intro = "🟣 Viola — في تحسّن ملحوظ. خلّينا نثبت اللي شغال ونكمل."
                nudges.append("حافظ على عادة صغيرة يوميًا عشان التحسن يكمل.")
                closing = "قلّي: إيه أكتر حاجة نفعتك آخر مرة وعايز تكررها؟"

        return {
            "intensity": intensity,
            "intro": intro,
            "closing": closing,
            "nudges": nudges,
            "trend_7d": ctx.trend_7d,
            "last_severity": ctx.last_severity,
            "last_checkin_mood": ctx.last_checkin_mood,
        }

    def _trend(self, sev: List[int]) -> str:
        if len(sev) < 2:
            return "غير كافي"
        third = max(1, len(sev) // 3)
        first_avg = sum(sev[:third]) / float(third)
        last_avg = sum(sev[-third:]) / float(third)
        if last_avg > first_avg + 5:
            return "🔺 بيزيد"
        if last_avg < first_avg - 5:
            return "🔻 بيتحسن"
        return "➡️ ثابت تقريبًا"
