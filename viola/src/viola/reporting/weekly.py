from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from viola.memory.store import MemoryStore


_RLM = "\u200F"


def _rtl(s: str) -> str:
    return "\n".join([_RLM + line for line in s.splitlines()])


def _top_k(counter: Dict[str, int], k: int = 3) -> List[Tuple[str, int]]:
    return sorted(counter.items(), key=lambda x: x[1], reverse=True)[:k]


def _trend(sev: List[int]) -> str:
    if len(sev) < 2:
        return "غير كافي"
    first = sum(sev[: max(1, len(sev)//3)]) / float(max(1, len(sev)//3))
    last = sum(sev[-max(1, len(sev)//3):]) / float(max(1, len(sev)//3))
    if last > first + 5:
        return "🔺 بيزيد"
    if last < first - 5:
        return "🔻 بيتحسن"
    return "➡️ ثابت تقريبًا"


def build_weekly_report(user_id: str = "default", days: int = 7) -> Dict[str, Any]:
    store = MemoryStore()
    events = store.get_events_since_days(user_id=user_id, days=days)
    summary_all = store.get_summary(user_id=user_id)

    sev_list: List[int] = [e.get("severity") for e in events if isinstance(e.get("severity"), int)]
    avg_sev = round(sum(sev_list) / float(len(sev_list)), 1) if sev_list else 0.0

    emo_counts: Dict[str, int] = {}
    dist_counts: Dict[str, int] = {}
    crisis_count = 0

    for e in events:
        if e.get("crisis_flag") is True:
            crisis_count += 1

        top_emo = e.get("top_emotion")
        if isinstance(top_emo, str) and top_emo:
            emo_counts[top_emo] = emo_counts.get(top_emo, 0) + 1

        for d in (e.get("distortions") or []):
            name = d.get("name")
            if isinstance(name, str) and name:
                dist_counts[name] = dist_counts.get(name, 0) + 1

    report = {
        "user_id": user_id,
        "days": days,
        "events_in_range": len(events),
        "avg_severity_in_range": avg_sev,
        "severity_trend": _trend(sev_list),
        "top_emotions_in_range": _top_k(emo_counts, 3),
        "top_distortions_in_range": _top_k(dist_counts, 3),
        "crisis_count_in_range": crisis_count,
        "overall_summary": summary_all,
    }

    # Recommendation (very simple v1)
    rec: List[str] = []
    top_dist = report["top_distortions_in_range"][0][0] if report["top_distortions_in_range"] else None
    if top_dist == "overgeneralization":
        rec.append("ركّز الأسبوع الجاي على تحويل (دايمًا/أبدًا) لـ (أحيانًا) + اكتب استثناءين يوميًا.")
    elif top_dist == "fortune_telling":
        rec.append("اكتب دليلين مع/ضد توقعك، وخد خطوة صغيرة يوميًا تزود فرص النتيجة الأحسن.")
    elif top_dist == "catastrophizing":
        rec.append("اكتب 3 سيناريوهات (الأسوأ/الأفضل/الأقرب) + خطة 3 خطوات للأقرب للواقع.")
    elif top_dist == "should_statements":
        rec.append("استبدل (لازم/مفروض) بـ (يفضل/أتمنى) واكتب نفس الجملة بصياغة أرحم.")
    elif top_dist == "labeling":
        rec.append("حوّل الألقاب لوصف سلوك محدد: بدل 'أنا فاشل' -> 'أنا اتأخرت في X'.")

    if not rec:
        rec.append("اختار تمرين CBT واحد كل يوم (5 دقايق) + سؤال تفكيك واحد بس. الاستمرارية أهم من الكمال.")

    report["recommendations"] = rec
    return report


def format_weekly_report(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("🟪 Viola — تقرير المتابعة")
    lines.append("")
    lines.append(f"• المستخدم: {report.get('user_id')}")
    lines.append(f"• الفترة: آخر {report.get('days')} يوم")
    lines.append(f"• عدد الرسائل في الفترة: {report.get('events_in_range')}")
    lines.append(f"• متوسط الشدة في الفترة: {report.get('avg_severity_in_range')}")
    lines.append(f"• اتجاه الشدة: {report.get('severity_trend')}")
    lines.append(f"• مرات تفعيل وضع الأمان في الفترة: {report.get('crisis_count_in_range')}")
    lines.append("")

    top_emo = report.get("top_emotions_in_range") or []
    lines.append("🙂 أكثر المشاعر تكرارًا (في الفترة):")
    if top_emo:
        for name, cnt in top_emo:
            lines.append(f"- {name}: {cnt}")
    else:
        lines.append("- لا يوجد بيانات كافية")

    lines.append("")
    top_dist = report.get("top_distortions_in_range") or []
    lines.append("🧠 أكثر التشوهات تكرارًا (في الفترة):")
    if top_dist:
        for name, cnt in top_dist:
            lines.append(f"- {name}: {cnt}")
    else:
        lines.append("- لا يوجد بيانات كافية")

    lines.append("")
    lines.append("🎯 توصية الأسبوع القادم:")
    for r in (report.get("recommendations") or []):
        lines.append(f"- {r}")

    # Overall snapshot (very short)
    overall = report.get("overall_summary", {}) or {}
    lines.append("")
    lines.append("📌 لقطة عامة (كل البيانات):")
    lines.append(f"- إجمالي الرسائل: {overall.get('total_messages')}")
    lines.append(f"- متوسط الشدة العام: {round(float(overall.get('avg_severity', 0.0)), 1)}")
    if overall.get("top_emotion_overall"):
        lines.append(f"- أكتر شعور عام: {overall.get('top_emotion_overall')}")
    if overall.get("top_distortion_overall"):
        lines.append(f"- أكتر تشوه عام: {overall.get('top_distortion_overall')}")

    return _rtl("\n".join(lines))
