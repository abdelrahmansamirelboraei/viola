from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from faster_whisper import WhisperModel
from viola.domain.entities import Transcript
from viola.services.transcription import TranscriptionService


from viola.domain.entities import Transcript
from viola.services.transcription import TranscriptionService
from faster_whisper import WhisperModel


class FasterWhisperTranscriber(TranscriptionService):
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        # model_size: tiny/base/small/medium/large-v3 (bigger = better but slower)
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> Transcript:
        segments, _info = self.model.transcribe(
            audio_path,
            language="ar",
            vad_filter=True,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
    vad_parameters={"min_silence_duration_ms": 300},
)



        

        text_parts: List[str] = []
        segs_out: List[Dict[str, Any]] = []

        for s in segments:
            text_parts.append(s.text.strip())
            segs_out.append(
                {
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": s.text.strip(),
                }
            )

        full_text = " ".join([t for t in text_parts if t])
        return Transcript(text=full_text, segments=segs_out or None)
