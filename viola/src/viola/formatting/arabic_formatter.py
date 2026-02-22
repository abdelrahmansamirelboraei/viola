from __future__ import annotations

from typing import Any, Dict, List, Optional

from viola.policy.engine import ResponsePolicy

_RLM = "\u200F"


def _rtl(s: str) -> str:
    return "\n".join([_RLM + line for line in s.splitlines()])


def _safe_get_top(items: List[Dict[str, Any]] | None, key: str) -> Optional[Any]:
    if not items:
        return None
    return items[0].get(key)


def _style_block(style: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    lines.append(style.get("intro", "🟣 Viola — معاك خطوة بخطوة."))
    # Trend hints (small)
    trend = style.get("trend_7d")
    if trend and trend != "غير كافي":
        lines.append(f"• اتجاه آخر 7 أيام: {trend}")
    ls = style.get("last_severity")
    if isinstance(ls, int):
        lines.append(f"• آخر شدة مسجلة: {ls}")
    lm = style.get("last_checkin_mood")
    if isinstance(lm, int):
        lines.append(f"• آخر Check-in مزاج: {lm} (كل ما يزيد أفضل)")
    nudges = style.get("nudges") or []
    if nudges:
        lines.append("")
        lines.append("📌 ملاحظة مهمة:")
        for n in nudges[:3]:
            lines.append(f"- {n}")
    lines.append("")
    return lines


def format_cbt(payload: Dict[str, Any]) -> str:
    analysis = payload.get("analysis", {}) or {}
    plan = payload.get("plan", {}) or {}
    summary = payload.get("memory_summary", {}) or {}

    user_id = (summary.get("user_id") or "default")
    policy = ResponsePolicy()
    ctx = policy.build_context(user_id=user_id, days=7)
    style = policy.decide_style(ctx)

    severity = analysis.get("severity")
    top_emotion = _safe_get_top(analysis.get("emotions"), "name")
    top_emotion_conf = _safe_get_top(analysis.get("emotions"), "confidence")

    lines: List[str] = []
    lines.extend(_style_block(style))

    lines.append("🧠 خطة مساعدة (CBT)")
    lines.append("")
    lines.append(f"• شدة الشعور (0-100): {severity}")
    if top_emotion:
        lines.append(f"• الشعور الأوضح: {top_emotion} (ثقة {top_emotion_conf})")
    lines.append("")

    interventions = plan.get("interventions", []) or []
    if not interventions:
        lines.append("مفيش تشوهات معرفية واضحة اتلقطت في الرسالة دي.")
        lines.append("خلّينا نسأل سؤالين بسيطين:")
        lines.append("؟ إيه أكتر فكرة مضايقاك دلوقتي؟")
        lines.append("؟ وإيه أصغر خطوة تقدر تعملها خلال 10 دقايق؟")
    else:
        lines.append("✅ هنشتغل على الأفكار دي خطوة بخطوة:")
        lines.append("")
        for idx, itv in enumerate(interventions, start=1):
            dist = itv.get("distortion")
            conf = itv.get("confidence")
            lines.append(f"{idx}) التشوه المعرفي: {dist} (ثقة {conf})")

            qs = itv.get("questions", []) or []
            if qs:
                lines.append("   أسئلة تفكيك:")
                for q in qs:
                    lines.append(f"   ؟ {q}")

            refr = itv.get("reframes", []) or []
            if refr:
                lines.append("   إعادة صياغة مقترحة:")
                for r in refr:
                    lines.append(f"   ↻ {r}")

            ex = itv.get("exercises", []) or []
            if ex:
                lines.append("   تمرين سريع:")
                for e in ex:
                    lines.append(f"   ✓ {e}")

            lines.append("")

    lines.append("🧩 ختام:")
    lines.append(style.get("closing", "لو تحب، رد على سؤال واحد بس من اللي فوق ونكمل سوا."))

    lines.append("")
    lines.append("📌 ملخص سريع عن نمطك (من الذاكرة):")
    lines.append(f"• عدد الرسائل: {summary.get('total_messages')}")
    lines.append(f"• متوسط الشدة: {round(float(summary.get('avg_severity', 0.0)), 1)}")
    if summary.get("top_emotion_overall"):
        lines.append(f"• أكتر شعور متكرر: {summary.get('top_emotion_overall')}")
    if summary.get("top_distortion_overall"):
        lines.append(f"• أكتر تشوه متكرر: {summary.get('top_distortion_overall')}")

    return _rtl("\n".join(lines))


def format_crisis(payload: Dict[str, Any]) -> str:
    analysis = payload.get("analysis", {}) or {}
    resp = payload.get("response", {}) or {}
    summary = payload.get("memory_summary", {}) or {}

    user_id = (summary.get("user_id") or "default")
    policy = ResponsePolicy()
    ctx = policy.build_context(user_id=user_id, days=7)
    style = policy.decide_style(ctx)

    lines: List[str] = []
    # In crisis mode, keep it direct but still adaptive
    lines.append("🔴 Viola — وضع الأمان (Crisis Mode)")
    lines.append("")
    lines.append(resp.get("message", ""))
    lines.append("")
    lines.append("خطوات دلوقتي:")
    for s in (resp.get("steps_now", []) or []):
        lines.append(f"- {s}")

    lines.append("")
    lines.append("طلب المساعدة:")
    for s in (resp.get("seek_help", []) or []):
        lines.append(f"- {s}")

    lines.append("")
    # Add small adaptive nudge if exists
    nudges = style.get("nudges") or []
    if nudges:
        lines.append("📌 ملاحظة:")
        for n in nudges[:2]:
            lines.append(f"- {n}")

    lines.append("")
    lines.append(f"• شدة الشعور (0-100): {analysis.get('severity')}")

    lines.append("")
    lines.append("📌 ملخص سريع (من الذاكرة):")
    lines.append(f"• عدد الرسائل: {summary.get('total_messages')}")
    lines.append(f"• مرات تفعيل وضع الأمان: {summary.get('crisis_count')}")

    return _rtl("\n".join(lines))


def format_payload(payload: Dict[str, Any]) -> str:
    mode = payload.get("mode")
    if mode == "crisis":
        return format_crisis(payload)
    return format_cbt(payload)
