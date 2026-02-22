from __future__ import annotations

from abc import ABC, abstractmethod
from viola.domain.entities import Transcript


class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> Transcript:
        # Convert audio -> Arabic text (MVP: can be dummy)
        raise NotImplementedError
