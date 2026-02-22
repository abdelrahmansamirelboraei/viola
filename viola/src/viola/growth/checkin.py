from __future__ import annotations

from typing import List
from viola.memory.store import MemoryStore

_RLM = "\u200F"


def _rtl(s: str) -> str:
    return "\n".join([_RLM + line for line in s.splitlines()])


def run_checkin(user_id: str, mood: int, note: str = "") -> str:
    store = MemoryStore()
    store.append_checkin(user_id=user_id, mood=mood, note=note)
    summary = store.get_summary(user_id)

    lines: List[str] = []
    lines.append("🟪 Viola — Daily Check-in")
    lines.append("")
    lines.append(f"• مزاجك دلوقتي (0-100): {mood} (كل ما يزيد أفضل)")
    if note:
        lines.append(f"• ملاحظة: {note}")
    lines.append("")
    lines.append("✅ اقتراح صغير لمدة 5 دقائق (اختار واحد):")
    lines.append("- تنفّس 4-6 لمدة دقيقتين.")
    lines.append("- اكتب جملة واحدة: (إيه الفكرة اللي مزعجاني؟ وإيه رد واقعي عليها؟)")
    lines.append("- خطوة 10 دقائق ناحية حاجة مفيدة (حتى لو بسيطة).")
    lines.append("")
    lines.append("📌 من الذاكرة:")
    lines.append(f"- عدد الـ check-ins: {summary.get('checkins_count')}")
    lines.append(f"- متوسط المزاج: {round(float(summary.get('avg_checkin_mood', 0.0)), 1)}")
    lines.append(f"- آخر مزاج مسجل: {summary.get('last_checkin_mood')}")
    return _rtl("\n".join(lines))
