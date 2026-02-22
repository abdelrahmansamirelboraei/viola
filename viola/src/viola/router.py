from __future__ import annotations

import json
from typing import Dict, Any

from viola.analyzers.emotion_distortion import EmotionDistortionAnalyzer
from viola.cbt.engine import CbtEngine
from viola.crisis.responder import CrisisResponder
from viola.memory.store import MemoryStore


def process_text(text: str, user_id: str = "default") -> Dict[str, Any]:
    analyzer = EmotionDistortionAnalyzer()
    analysis = analyzer.analyze(text)
    analysis_dict = analysis.to_dict()

    store = MemoryStore()

    if analysis.crisis_flag:
        crisis = CrisisResponder().build(analysis.crisis_signals)

        store.append_event(
            user_id=user_id,
            text=text,
            analysis_dict=analysis_dict,
            mode="crisis",
        )

        return {
            "mode": "crisis",
            "analysis": analysis_dict,
            "response": crisis.to_dict(),
            "memory_summary": store.get_summary(user_id),
        }

    plan = CbtEngine().build_plan(analysis)

    store.append_event(
        user_id=user_id,
        text=text,
        analysis_dict=analysis_dict,
        mode="cbt",
    )

    return {
        "mode": "cbt",
        "analysis": analysis_dict,
        "plan": plan.to_dict(),
        "memory_summary": store.get_summary(user_id),
    }


def process_text_json(text: str, user_id: str = "default") -> str:
    return json.dumps(process_text(text, user_id=user_id), ensure_ascii=False, indent=2)


def memory_summary_json(user_id: str = "default") -> str:
    store = MemoryStore()
    return json.dumps(store.get_summary(user_id), ensure_ascii=False, indent=2)
