from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from viola.memory.store import MemoryStore
from viola.growth.templates import (
    WEEKLY_FOCUS,
    DAILY_MICRO_HABITS,
    GENERIC_WEEKLY,
    GENERIC_HABITS,
)

_RLM = "\u200F"


def _rtl(s: str) -> str:
    return "\n".join([_RLM + line for line in s.splitlines()])


@dataclass(frozen=True)
class WeeklyPlan:
    user_id: str
    days: int
    focus_distortion: Optional[str] = None
    focus_text: str = ""
    daily_micro_habits: List[str] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "days": self.days,
            "focus_distortion": self.focus_distortion,
            "focus_text": self.focus_text,
            "daily_micro_habits": self.daily_micro_habits,
            "checkpoints": self.checkpoints,
            "metadata": self.metadata,
        }


class GrowthPlanner:
    def build_weekly_plan(self, user_id: str = "default", days: int = 7) -> WeeklyPlan:
        store = MemoryStore()
        summary = store.get_summary(user_id)

        focus_dist = summary.get("top_distortion_overall")
        if isinstance(focus_dist, str) and focus_dist in WEEKLY_FOCUS:
            focus_text = WEEKLY_FOCUS[focus_dist]
            habits = DAILY_MICRO_HABITS.get(focus_dist, [])[:3]
        else:
            focus_dist = None
            focus_text = GENERIC_WEEKLY
            habits = GENERIC_HABITS[:3]

        checkpoints = [
            "يوم 1: اختار جملة واحدة مزعجة وحوّلها لصياغة واقعية.",
            "يوم 3: راجع أشد فكرة تكررت وطبّق تمرينين عليها.",
            "يوم 7: اعمل تقرير (report) وشوف الاتجاه + اختار تركيز الأسبوع الجاي.",
        ]

        return WeeklyPlan(
            user_id=user_id,
            days=days,
            focus_distortion=focus_dist,
            focus_text=focus_text,
            daily_micro_habits=habits,
            checkpoints=checkpoints,
            metadata={"engine": "growth_plan_v1", "based_on": "memory_summary"},
        )


def format_weekly_plan(plan: WeeklyPlan) -> str:
    lines: List[str] = []
    lines.append("🟪 Viola — خطة تطوير أسبوعية")
    lines.append("")
    lines.append(f"• المستخدم: {plan.user_id}")
    lines.append(f"• المدة: {plan.days} أيام")
    lines.append("")
    if plan.focus_distortion:
        lines.append(f"🎯 محور الأسبوع (تشوه متكرر): {plan.focus_distortion}")
    else:
        lines.append("🎯 محور الأسبوع: عام (بدون تشوه واضح متكرر)")
    lines.append(f"• الهدف: {plan.focus_text}")
    lines.append("")
    lines.append("✅ عادات يومية صغيرة (اختار 1–2 فقط يوميًا):")
    for h in plan.daily_micro_habits:
        lines.append(f"- {h}")
    lines.append("")
    lines.append("📍 نقاط متابعة:")
    for c in plan.checkpoints:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("🧩 قاعدة مهمة: الاستمرارية أهم من الكمال. 10 دقايق يوميًا تكسب.")
    return _rtl("\n".join(lines))
