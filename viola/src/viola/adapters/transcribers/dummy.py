from __future__ import annotations

from viola.domain.entities import Transcript
from viola.services.transcription import TranscriptionService


class DummyTranscriber(TranscriptionService):
    def transcribe(self, audio_path: str) -> Transcript:
        # MVP fallback: no transcription yet
        return Transcript(text="")
