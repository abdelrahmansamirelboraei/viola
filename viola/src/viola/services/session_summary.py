from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple


def _safe_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _clip(s: str, n: int = 260) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _pick_top_emotions(turns: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
    emotion_totals: Dict[str, float] = {}
    emotion_counts: Dict[str, int] = {}

    for t in turns:
        analysis = _safe_dict(t.get("analysis"))
        emotions = _safe_dict(analysis.get("emotions"))
        for k, v in emotions.items():
            try:
                fv = float(v)
            except Exception:
                continue
            emotion_totals[k] = emotion_totals.get(k, 0.0) + fv
            emotion_counts[k] = emotion_counts.get(k, 0) + 1

    avg_emotions = {
        k: (emotion_totals[k] / emotion_counts[k])
        for k in emotion_totals
        if emotion_counts.get(k, 0) > 0
    }
    return sorted(avg_emotions.items(), key=lambda kv: kv[1], reverse=True)[:4]


def _pick_top_distortions(turns: List[Dict[str, Any]]) -> List[str]:
    distortions: List[str] = []
    for t in turns:
        analysis = _safe_dict(t.get("analysis"))
        distortions.extend([str(x) for x in _safe_list(analysis.get("cognitive_distortions"))])
    return [name for name, _ in Counter(distortions).most_common(5)]


def build_session_summary(domain_session: Dict[str, Any]) -> Tuple[str, str]:
    turns = _safe_list(domain_session.get("turns"))
    n = len(turns)

    if n == 0:
        summary = "لم يتم تسجيل أي تيرنز في هذه الجلسة."
        closing = "أتمنى لك يومًا أهدأ وخطوات بسيطة في اتجاه أفضل. 🤍"
        return summary, closing

    # --- Guided slots (if present) ---
    guided_state = _safe_dict(domain_session.get("guided_state"))
    slots = _safe_dict(guided_state.get("slots"))

    situation = _clip(str(slots.get("situation", "") or ""))
    thought = _clip(str(slots.get("thought", "") or ""))
    emotions_report = _clip(str(slots.get("emotions_report", "") or ""))
    evidence_for = _clip(str(slots.get("evidence_for", "") or ""))
    evidence_against = _clip(str(slots.get("evidence_against", "") or ""))
    alternative_view = _clip(str(slots.get("alternative_view", "") or ""))
    balanced_thought = _clip(str(slots.get("balanced_thought", "") or ""))
    tiny_action = _clip(str(slots.get("tiny_action", "") or ""))
    review = _clip(str(slots.get("review", "") or ""))

    # --- Analysis-derived signals ---
    top_emotions = _pick_top_emotions(turns)
    top_distortions = _pick_top_distortions(turns)

    # --- Compact highlights from last turns ---
    summaries: List[str] = []
    for t in turns:
        analysis = _safe_dict(t.get("analysis"))
        s = str(analysis.get("summary", "") or "").strip()
        if s:
            summaries.append(s)

    tail_summaries = summaries[-3:] if summaries else []

    # --- Build final summary ---
    lines: List[str] = []
    lines.append("🟣 ملخص الجلسة (Multi-Turn)")
    lines.append("")
    lines.append(f"- عدد الأدوار (Turns): {n}")

    if tail_summaries:
        lines.append("")
        lines.append("📌 نقاط بارزة من تطور الكلام:")
        for i, s in enumerate(tail_summaries, start=1):
            lines.append(f"  {i}) {s}")

    # Guided CBT block (the real session core)
    lines.append("")
    lines.append("🧩 خريطة الجلسة (CBT Guided)")
    if situation:
        lines.append(f"- الموقف: {situation}")
    if thought:
        lines.append(f"- الفكرة التلقائية: {thought}")
    if emotions_report:
        lines.append(f"- المشاعر/الشدّة: {emotions_report}")

    if evidence_for:
        lines.append(f"- أدلة مؤيدة للفكرة: {evidence_for}")
    if evidence_against:
        lines.append(f"- أدلة ضد الفكرة / حقائق موازنة: {evidence_against}")

    if alternative_view:
        lines.append(f"- تفسير بديل/أكثر توازنًا: {alternative_view}")
    if balanced_thought:
        lines.append(f"- الفكرة المتوازنة الجديدة: {balanced_thought}")

    if tiny_action:
        lines.append(f"- خطوة عملية صغيرة: {tiny_action}")
    if review:
        lines.append(f"- مراجعة (العقبة/التوقع): {review}")

    # Add analysis signals for extra insight
    if top_distortions:
        lines.append("")
        lines.append("⚠️ مؤشرات تشوهات معرفية كانت الأكثر ظهورًا:")
        for d in top_distortions:
            lines.append(f"- {d}")

    if top_emotions:
        lines.append("")
        lines.append("❤️ مشاعر بارزة (متوسط تقديري من التحليل):")
        for name, score in top_emotions:
            lines.append(f"- {name}: {score:.2f}")

    # If guided was missing, still provide a gentle direction
    if not any([situation, thought, balanced_thought, tiny_action]):
        lines.append("")
        lines.append("ملاحظة: لم تكتمل مراحل الجلسة الموجّهة بالكامل، لكننا نقدر نكمّلها في جلسة لاحقة.")

    summary_text = "\n".join(lines)

    closing = (
        "🌙 خاتمة لطيفة\n\n"
        "اللي عملته هنا مش مجرد كلام — ده تدريب مباشر لعقلك إنه يبدّل من (تلقائي/قاسي) إلى (متوازن/مفيد).\n"
        "لو حسّيت إنك رجعت لنفس الدوامة، ارجع للفكرة المتوازنة والخطوة الصغيرة… وابدأ من أصغر نقطة.\n\n"
        "أتمنى لك حياة أسعد فعلًا: هدوء أكتر، وضوح أكتر، ورحمة بنفسك أكتر. 🤍"
    )

    return summary_text, closing
