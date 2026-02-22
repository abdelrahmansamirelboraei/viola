from __future__ import annotations

from typing import Any, List


class ResponseFormatter:
    def format(self, plan: Any) -> str:
        """
        Format CBTPlan (or crisis plan) into Markdown text for CLI/Web.
        """

        summary = (getattr(plan, "summary", "") or "").strip()
        auto_thought = (getattr(plan, "auto_thought", "") or "").strip()
        distortions: List[str] = list(getattr(plan, "distortions", []) or [])
        questions: List[str] = list(getattr(plan, "socratic_questions", []) or [])
        step = (getattr(plan, "behavioral_step", "") or "").strip()

        # Crisis detector (kept simple & robust)
        is_crisis = (
            ("🚨" in summary)
            or ("جهة طوارئ" in step)
            or ("الطوارئ" in step)
            or ("إيذاء النفس" in auto_thought)
            or ("انتح" in auto_thought)
        )

        lines: List[str] = []
        lines.append("🟣 Viola (CBT دعم ذاتي)\n")

        lines.append("**تلخيص سريع:**")
        lines.append(f"- {summary}" if summary else "- (بدون ملخص)")
        lines.append("")

        lines.append("**الفكرة التلقائية المحتملة:**")
        lines.append(f"- {auto_thought}" if auto_thought else "- (غير متاحة)")
        lines.append("")

        lines.append("**تشوهات معرفية محتملة (مؤشرات):**")
        if distortions:
            for d in distortions:
                lines.append(f"- {d}")
        else:
            lines.append("- (غير متاح/غير مناسب الآن)" if is_crisis else "- غير محدد (محتاج تفاصيل أكثر)")
        lines.append("")

        lines.append("**أسئلة أمان سريعة:**" if is_crisis else "**أسئلة سوكراتية تساعدك تعيد صياغة الفكرة:**")
        if questions:
            for q in questions:
                lines.append(f"- {q}")
        else:
            lines.append("- (لا يوجد)")
        lines.append("")

        lines.append("**خطوة عملية صغيرة الآن:**")
        lines.append(f"- {step}" if step else "- (لا يوجد)")
        lines.append("")

        lines.append(
            "⚠️ Viola provides CBT-style self-help guidance and emotional indicators. "
            "It is not a medical diagnosis or a substitute for professional care."
        )

        return "\n".join(lines)
