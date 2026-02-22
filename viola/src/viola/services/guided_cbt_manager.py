from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


def _safe_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _clip(s: str, n: int = 180) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


@dataclass
class GuidedState:
    stage: str = "clarify"  # clarify | thought | emotions | evidence_for | evidence_against | alternative | balanced | action | review
    asked: List[str] = None  # asked questions texts
    slots: Dict[str, str] = None  # collected info

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "asked": self.asked or [],
            "slots": self.slots or {},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GuidedState":
        return cls(
            stage=str(d.get("stage", "clarify") or "clarify"),
            asked=list(d.get("asked") or []),
            slots=dict(d.get("slots") or {}),
        )


class GuidedCBTManager:
    """
    Guided CBT manager (rule-based) that decides the next best follow-up question
    based on what we already captured in the session.
    """

    def __init__(self, *, max_depth: int = 8) -> None:
        self.max_depth = max_depth

    def next_question(self, domain_session: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Returns (question_text, updated_domain_session).
        Stores guided_state under domain_session['guided_state'].
        """
        state = GuidedState.from_dict(_safe_dict(domain_session.get("guided_state")))

        turns = _safe_list(domain_session.get("turns"))
        last_turn = turns[-1] if turns else {}
        last_user = str(last_turn.get("user_text", "") or "").strip()
        analysis = _safe_dict(last_turn.get("analysis"))
        auto_thought = str(analysis.get("automatic_thought", "") or "").strip()
        summary = str(analysis.get("summary", "") or "").strip()

        slots = state.slots or {}
        asked = state.asked or []

        # Try to auto-fill from analysis
        if summary and not slots.get("situation"):
            slots["situation"] = _clip(summary, 220)

        if auto_thought and not slots.get("thought"):
            slots["thought"] = _clip(auto_thought, 220)

        # If we already asked too many questions, move to review/action
        if len(asked) >= self.max_depth and state.stage not in ("action", "review"):
            state.stage = "action"

        # Stage routing
        stage = state.stage

        # If user gave a very short input, treat it as answer to the last question and continue
        # (We don't need heavy NLP here.)
        if stage == "clarify":
            if not slots.get("situation"):
                q = "خلّيني أفهم الصورة: إيه الموقف بالتحديد اللي حصل، وإمتى؟ (جملة أو جملتين)"
            else:
                state.stage = "thought"
                q = self._question_thought(slots)
        elif stage == "thought":
            if not slots.get("thought"):
                q = self._question_thought(slots)
            else:
                state.stage = "emotions"
                q = self._question_emotions()
        elif stage == "emotions":
            # emotions can be missing from rule analyzer; ask anyway
            state.stage = "evidence_for"
            q = self._question_evidence_for(slots)
        elif stage == "evidence_for":
            state.stage = "evidence_against"
            q = self._question_evidence_against(slots)
        elif stage == "evidence_against":
            state.stage = "alternative"
            q = self._question_alternative(slots)
        elif stage == "alternative":
            state.stage = "balanced"
            q = self._question_balanced(slots)
        elif stage == "balanced":
            state.stage = "action"
            q = self._question_action()
        elif stage == "action":
            state.stage = "review"
            q = self._question_review()
        else:  # review
            q = "لو تحب نكمّل: إيه أصعب جزء لسه موجود؟ ولا نعمل إنهاء للجلسة وملخص؟"

        asked.append(q)
        state.asked = asked
        state.slots = slots
        domain_session["guided_state"] = state.to_dict()

        # Also store last_followup for UI
        domain_session["guided_state"]["last_followup"] = q
        domain_session["guided_state"]["last_user_seen"] = _clip(last_user, 220)

        return q, domain_session

    @staticmethod
    def _question_thought(slots: Dict[str, str]) -> str:
        sit = slots.get("situation", "")
        if sit:
            return f"في الموقف ده: إيه أول فكرة تلقائية جات في بالك؟ (مثال: \"أنا...\" أو \"هيحصل...\")\n\nالموقف: {sit}"
        return "إيه أول فكرة تلقائية جات في بالك وقتها؟ (مثال: \"أنا...\" أو \"هيحصل...\")"

    @staticmethod
    def _question_emotions() -> str:
        return "إيه الشعور/المشاعر اللي طلعت مع الفكرة دي؟ وقيّم شدتها من 0 إلى 10."

    @staticmethod
    def _question_evidence_for(slots: Dict[str, str]) -> str:
        th = slots.get("thought", "")
        if th:
            return f"خلّينا نختبر الفكرة: ما الدليل اللي بيخلّيك تصدّق إن \"{th}\" صحيحة؟ (نقطة أو نقطتين)"
        return "ما الدليل اللي بيخلّيك تصدّق الفكرة دي؟ (نقطة أو نقطتين)"

    @staticmethod
    def _question_evidence_against(slots: Dict[str, str]) -> str:
        th = slots.get("thought", "")
        if th:
            return f"تمام. دلوقتي: ما الدليل ضد فكرة \"{th}\"؟ أو إيه الحقائق اللي بتقول إن الصورة مش سودا كده؟"
        return "ما الدليل ضد الفكرة دي؟ أو إيه الحقائق اللي بتقول إن الصورة مش سودا كده؟"

    @staticmethod
    def _question_alternative(slots: Dict[str, str]) -> str:
        sit = slots.get("situation", "")
        th = slots.get("thought", "")
        if sit and th:
            return f"لو بصّينا للموقف من زاوية أهدى: إيه تفسير بديل/أكثر توازنًا للموقف بدل \"{th}\"؟\n\nالموقف: {sit}"
        return "إيه تفسير بديل/أكثر توازنًا للموقف؟"

    @staticmethod
    def _question_balanced(slots: Dict[str, str]) -> str:
        th = slots.get("thought", "")
        if th:
            return f"ممتاز. اكتبلي جملة واحدة \"فكرة متوازنة\" بديلة بدل \"{th}\" (تكون رحيمة وواقعية)."
        return "اكتبلي جملة واحدة \"فكرة متوازنة\" بديلة (رحيمة وواقعية)."

    @staticmethod
    def _question_action() -> str:
        return "إيه أصغر خطوة عملية تقدر تعملها خلال 10 دقائق تخدمك دلوقتي؟ (خطوة واحدة بس)"

    @staticmethod
    def _question_review() -> str:
        return "بعد الخطوة دي، تتوقع شعورك هينزل قد إيه من 0–10؟ وإيه العقبة اللي ممكن تعطلّك؟"
