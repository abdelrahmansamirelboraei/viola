from __future__ import annotations

from abc import ABC, abstractmethod
from viola.domain.entities import AnalysisResult


class NLPAnalysisService(ABC):
    @abstractmethod
    def analyze(self, text: str) -> AnalysisResult:
        # Extract indicators: emotions + CBT distortions + basic summary
        raise NotImplementedError
