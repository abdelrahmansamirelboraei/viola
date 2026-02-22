from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import re


@dataclass
class AnalysisResult:
    # Backward-compatible fields used by pipeline/formatter
    emotion_scores: Dict[str, float]
    distortions: List[str]
    summary: str
    auto_thought: str

    # Semi-structured CBT fields
    topic: str = "general"
    keywords: List[str] = field(default_factory=list)

    situation: str = ""
    trigger: str = ""
    emotions: List[Dict[str, object]] = field(default_factory=list)
    body_sensations: List[str] = field(default_factory=list)
    behaviors: List[str] = field(default_factory=list)
    needs: List[str] = field(default_factory=list)
    core_belief_hint: str = ""

    risk_flags: List[str] = field(default_factory=list)
    raw_text: str = ""


_AR_KEEP = re.compile(r"[^\u0600-\u06FF0-9\s\.\,\!\?\:\؛\،\-\_\(\)\"\'\n]+")


def _clean(text: str) -> str:
    t = (text or "").strip()
    t = _AR_KEEP.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _sentences(text: str) -> List[str]:
    parts = re.split(r"[\.!\?\n]+", text or "")
    return [p.strip() for p in parts if p.strip()]


def _tokenize(text: str) -> List[str]:
    t = re.sub(r"[^\u0600-\u06FF0-9\s]+", " ", text or "")
    toks = [x.strip() for x in t.split() if x.strip()]
    return toks


def _top_keywords(tokens: List[str], k: int = 10) -> List[str]:
    stop = {
        "انا","أنا","انت","إنت","انتي","إنتي","هو","هي","هم","احنا","إحنا",
        "في","على","من","الى","إلى","عن","ده","دي","دا","اللي","التي","هذا","هذه","ذلك",
        "لكن","بس","يعني","جدا","جداً","اوي","أوي","او","أو",
        "مش","ما","مفيش","فيه","كان","كنت","لو","لما","علشان","عشان","مع","كل","اي","إيه"
    }
    freq: Dict[str, int] = {}
    for w in tokens:
        lw = w.lower()
        if lw in stop or len(lw) <= 2:
            continue
        freq[lw] = freq.get(lw, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:k]]


def _dedup(seq: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out


def _normalize_for_match(text: str) -> str:
    t = (text or "").strip()
    # normalize common Arabic letter variants
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")
    t = re.sub(r"\s+", " ", t)
    return t


def _detect_topic(text: str) -> str:
    lowered = _normalize_for_match(text).lower()

    topics = {
        "work": (["شغل","deadline","ديدلاين","تسليم","عميل","مدير","مكتب","مشروع","bug","باگ","ticket","تذكره"], 4),
        "study": (["امتحان","مذاكره","جامعه","كليه","محاضره","واجب","كورس","كورسات","دراسه","revision"], 4),
        "relationships": (["خناقه","اتخانقت","زعل","حب","حبيب","علاقه","مرفوض","رفض","اهلي","امي","ابويا"], 3),
        "health": (["تعب","صداع","مرض","دكتور","مستشفي","نوم","ارق","تنفس","ضغط","دواء"], 2),
        "anxiety": (["قلقان","قلق","توتر","متوتر","خوف","هلع","مرعوب","panic"], 2),
        "self_worth": (["انا فاشل","فاشل","غبي","عديم","مش كفايه","مش نافع"], 2),
    }

    scores: Dict[str, int] = {k: 0 for k in topics}
    for name, (words, weight) in topics.items():
        for w in words:
            if w in lowered:
                scores[name] += weight

    winner = max(scores.items(), key=lambda kv: kv[1])[0]
    if scores[winner] == 0:
        return "general"

    if scores.get("work", 0) >= 4:
        return "work"
    if scores.get("study", 0) >= 4:
        return "study"

    return winner


def _extract_situation_and_trigger(text: str, sents: List[str]) -> Tuple[str, str]:
    situation = sents[0] if sents else _clean(text)
    situation = situation[:260]

    trig_patterns = [
        r"(?:لما|عندما|وقت ما)\s+(.+)$",
        r"(?:بسبب|عشان|علشان|لان)\s+(.+)$",
        r"(?:بعد|قبل)\s+(.+)$",
        r"(?:عند)\s+(.+)$",
    ]
    trigger = ""
    for p in trig_patterns:
        m = re.search(p, _normalize_for_match(text))
        if m:
            trigger = (m.group(1) or "").strip()
            break

    if not trigger:
        t = _normalize_for_match(text)
        if re.search(r"(امتحان|اختبار|انترفيو|مقابله|تقييم)", t):
            trigger = "تقييم/اختبار"
        elif re.search(r"(deadline|ديدلاين|تسليم)", t, flags=re.IGNORECASE):
            trigger = "ضغط وقت/موعد تسليم"
        elif re.search(r"(خناقه|اتخانقت|خلاف|زعل)", t):
            trigger = "خلاف/توتر في علاقة"
        elif re.search(r"(نوم|ارق|سهر)", t):
            trigger = "نوم غير كافي"

    return situation, trigger[:220]


def _extract_auto_thought(text: str, sents: List[str]) -> str:
    markers = [
        "مش قادر", "مستحيل", "اكيد", "هفشل", "فاشل", "مش كفايه", "مرفوض",
        "مفيش فايده", "خلاص", "هتبوظ", "كارثه", "هيحصل"
    ]
    norm = _normalize_for_match(text)
    for s in sents:
        ns = _normalize_for_match(s)
        if any(m in ns for m in markers):
            return s[:240].strip()
    return (sents[0] if sents else text).strip()[:240]


def _extract_emotions(text: str) -> Tuple[List[Dict[str, object]], Dict[str, float]]:
    t = _normalize_for_match(text)

    lex = {
        "قلق": ["قلقان","قلق","توتر","متوتر","خوف","هلع","مرعوب","panic"],
        "حزن": ["حزين","زعلان","محبط","احباط","مكسور","اكتئاب"],
        "غضب": ["غضبان","متعصب","عصبي","بزعق","بعصب","قرفان"],
        "ذنب": ["ذنب","لوم","بانيب","تانيب"],
        "خجل": ["مكسوف","خجلان","احراج"],
        "إرهاق": ["تعبان","مرهق","مجهد","منهك","مش قادر"],
    }

    intensity = None
    m = re.search(r"(\d{1,2})\s*(?:/10|من\s*10)", t)
    if m:
        try:
            intensity = max(0, min(10, int(m.group(1))))
        except Exception:
            intensity = None

    emotions: List[Dict[str, object]] = []
    scores: Dict[str, float] = {k: 0.0 for k in lex}

    for emo, words in lex.items():
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", t, flags=re.IGNORECASE):
                scores[emo] += 0.35

    for k in scores:
        scores[k] = min(1.0, scores[k])

    for emo, sc in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
        if sc <= 0:
            continue
        guessed = intensity if intensity is not None else (7 if sc >= 0.7 else 5)
        emotions.append({"name": emo, "intensity": guessed})

    return emotions[:4], scores


def _extract_body_sensations(text: str) -> List[str]:
    t = _normalize_for_match(text)
    pats = [
        ("ضيق تنفس", r"(ضيق|مخنوق|مش قادر اتنفس|تنفسي)"),
        ("شد/توتر عضلي", r"(شد|توتر في الجسم|مشدود)"),
        ("خفقان", r"(خفقان|دقات|قلبي بيدق)"),
        ("صداع", r"(صداع|دماغي بتوجعني)"),
        ("معدة", r"(معدتي|غثيان|مغص)"),
    ]
    out: List[str] = []
    for label, pat in pats:
        if re.search(pat, t):
            out.append(label)
    return _dedup(out)


def _extract_behaviors(text: str) -> List[str]:
    t = _normalize_for_match(text)
    out: List[str] = []
    if re.search(r"(بتجنب|بتفادى|بتهرب|مبعملش|مش بعمل|بسوف|باجل|تسويف|مكسل)", t):
        out.append("تجنب/تسويف")
    if re.search(r"(بفكر كتير|تفكير زائد|overthink|براجع مليون مره)", t, flags=re.IGNORECASE):
        out.append("اجترار/Overthinking")
    if re.search(r"(بعزل نفسي|بقعد لوحدي|مش بكلم حد)", t):
        out.append("انسحاب/عزلة")
    if re.search(r"(بعصب|بانفجر|بزعق|بعلي صوتي)", t):
        out.append("اندفاع/غضب")
    if re.search(r"(بنام كتير|سهران|مبنمش|مش بنام)", t):
        out.append("نمط نوم مضطرب")
    return _dedup(out)


def _extract_needs(text: str) -> List[str]:
    t = _normalize_for_match(text)
    out: List[str] = []
    if re.search(r"(محتاج|نفسي|عايز)", t):
        if re.search(r"(اطمن|امان|خوف)", t):
            out.append("أمان/طمأنة")
        if re.search(r"(يتفهمني|يفهمني|قبول|تقدير|احترام)", t):
            out.append("قبول/تقدير")
        if re.search(r"(خطة|نظام|تحكم|سيطرة)", t):
            out.append("تنظيم/تحكم")
        if re.search(r"(راحة|نوم|استراحة)", t):
            out.append("راحة/تعافي")
        if re.search(r"(مساعدة|حد يسمعني|دعم)", t):
            out.append("دعم/احتواء")
    return _dedup(out)


def _detect_distortions(text: str) -> List[str]:
    t = _normalize_for_match(text)
    d: List[str] = []
    if re.search(r"(دايما|دائما|ابدا|ولا مره|مستحيل)", t):
        d.append("تفكير أبيض/أسود")
    if re.search(r"(كارثه|مصيبه|خلاص انتهى|هيتدمر|هينهار|ضاع كل حاجه)", t):
        d.append("تهويل/كارثية")
    if re.search(r"(اكيد).*(شايفني|فاكرني|بيفكر|هيقول|هيشوفني)", t):
        d.append("قراءة أفكار")
    if re.search(r"(لازم|مفروض)", t):
        d.append("عبارات يجب/لازم")
    if re.search(r"(انا فاشل|غبي|عديم|فاشله)", t):
        d.append("وَسْم/تصنيف")
    if re.search(r"(ده بسببي|انا السبب)", t):
        d.append("شخصنة/لوم ذات")
    return _dedup(d)


def _core_belief_hint(auto_thought: str, distortions: List[str], topic: str) -> str:
    t = _normalize_for_match(auto_thought or "")

    if "وَسْم/تصنيف" in distortions or re.search(r"(انا فاشل|غبي|عديم|مش كفايه)", t):
        return "قد يكون فيه اعتقاد جذري عن الكفاية/القيمة الذاتية (أنا مش كفاية)."
    if topic == "relationships" and re.search(r"(مرفوض|مش محبوب|هيبعد|مش عايزني)", t):
        return "قد يكون فيه اعتقاد جذري عن القبول (أنا مرفوض/مش محبوب)."
    if topic in ("work", "study") and re.search(r"(هفشل|مش هقدر|مستحيل)", t):
        return "قد يكون فيه اعتقاد جذري عن القدرة/الكفاءة (أنا مش قادر/هفشل)."
    if "تهويل/كارثية" in distortions:
        return "قد يكون فيه اعتقاد جذري مرتبط بالأمان (لو غلطت هتبقى كارثة)."
    return ""


def _risk_flags(text: str) -> List[str]:
    t = _normalize_for_match(text)

    # Broad Arabic + English patterns
    patterns = [
        r"\bانتحر\b",
        r"\bانتحار\b",
        r"عايز\s+انتحر",
        r"نفسي\s+انتحر",
        r"هنتحر",
        r"هقتل\s+نفسي",
        r"اقتل\s+نفسي",
        r"اذي\s+نفسي",
        r"ااذي\s+نفسي",
        r"\bsuicide\b",
        r"\bkill myself\b",
        r"\bself harm\b",
    ]

    for p in patterns:
        if re.search(p, t, flags=re.IGNORECASE):
            return ["self_harm_language"]

    return []


class RuleBasedArabicAnalyzer:
    def analyze(self, text: str) -> AnalysisResult:
        raw = text or ""
        cleaned = _clean(raw)
        sents = _sentences(raw)
        tokens = _tokenize(raw)

        topic = _detect_topic(raw)
        situation, trigger = _extract_situation_and_trigger(raw, sents)
        auto = _extract_auto_thought(raw, sents)

        emotions_list, emotion_scores = _extract_emotions(raw)
        body = _extract_body_sensations(raw)
        behaviors = _extract_behaviors(raw)
        needs = _extract_needs(raw)
        distortions = _detect_distortions(raw)
        belief = _core_belief_hint(auto, distortions, topic)

        keywords = _top_keywords(tokens, k=12)
        summary = (sents[0] if sents else cleaned).strip()[:240]

        return AnalysisResult(
            emotion_scores=emotion_scores,
            distortions=distortions,
            summary=summary,
            auto_thought=auto,
            topic=topic,
            keywords=keywords,
            situation=situation,
            trigger=trigger,
            emotions=emotions_list,
            body_sensations=body,
            behaviors=behaviors,
            needs=needs,
            core_belief_hint=belief,
            risk_flags=_risk_flags(raw),
            raw_text=raw,
        )
