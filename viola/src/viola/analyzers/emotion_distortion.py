from __future__ import annotations

from typing import List, Tuple
from viola.analyzers.base import Analyzer
from viola.analyzers.rules.ar_patterns import (
    COMPILED_EMOTIONS,
    COMPILED_DISTORTIONS,
    COMPILED_CRISIS,
)
from viola.core.types.analysis import TextAnalysis, EmotionHit, DistortionHit
from viola.text.normalizer import normalize_arabic


def _collect_hits(compiled_map, text: str) -> List[Tuple[str, List[str]]]:
    hits: List[Tuple[str, List[str]]] = []
    for name, regex_list in compiled_map.items():
        signals: List[str] = []
        for rgx in regex_list:
            m = rgx.search(text)
            if m:
                # Use matched snippet as a signal when possible
                signals.append(m.group(0))
        if signals:
            hits.append((name, signals))
    return hits


def _score_from_signals(signals_count: int, cap: int = 5) -> float:
    # Simple heuristic: more signals => higher confidence, capped.
    return min(1.0, signals_count / float(cap))


def _estimate_severity(emotions: List[EmotionHit], distortions: List[DistortionHit], crisis_flag: bool) -> int:
    base = 10
    base += int(sum(e.confidence for e in emotions) * 25)
    base += int(sum(d.confidence for d in distortions) * 15)
    if crisis_flag:
        base = max(base, 85)
    return max(0, min(100, base))


class EmotionDistortionAnalyzer(Analyzer):
    def analyze(self, text: str) -> TextAnalysis:
        # Normalize text to improve matching across spelling variants (أ/إ/آ, ى/ي, ة/ه, diacritics).
        normalized = normalize_arabic(text)

        crisis_signals: List[str] = []
        for rgx in COMPILED_CRISIS:
            m = rgx.search(normalized)
            if m:
                crisis_signals.append(m.group(0))
        crisis_flag = len(crisis_signals) > 0

        emotion_hits_raw = _collect_hits(COMPILED_EMOTIONS, normalized)
        distortion_hits_raw = _collect_hits(COMPILED_DISTORTIONS, normalized)

        emotions: List[EmotionHit] = [
            EmotionHit(name=n, confidence=_score_from_signals(len(sig)), signals=sig)
            for n, sig in emotion_hits_raw
        ]
        distortions: List[DistortionHit] = [
            DistortionHit(name=n, confidence=_score_from_signals(len(sig)), signals=sig)
            for n, sig in distortion_hits_raw
        ]

        severity = _estimate_severity(emotions, distortions, crisis_flag)

        return TextAnalysis(
            text=text,
            severity=severity,
            emotions=sorted(emotions, key=lambda e: e.confidence, reverse=True),
            distortions=sorted(distortions, key=lambda d: d.confidence, reverse=True),
            crisis_flag=crisis_flag,
            crisis_signals=crisis_signals,
            metadata={"engine": "rules_v1", "normalized_text": normalized},
        )
