from __future__ import annotations

from abc import ABC, abstractmethod
from viola.core.types.analysis import TextAnalysis


class Analyzer(ABC):
    @abstractmethod
    def analyze(self, text: str) -> TextAnalysis:
        raise NotImplementedError
