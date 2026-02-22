from __future__ import annotations

from datetime import datetime
import json
import os
from typing import Optional, Tuple, Dict, Any

from viola.config.settings import settings
from viola.domain.entities import SessionReport
from viola.domain.models import Session, Analysis, CBTPlan, Metadata
from viola.services.transcription import TranscriptionService
from viola.services.nlp_analysis import NLPAnalysisService
from viola.services.cbt_engine import CBTEngine
from viola.services.response import ResponseFormatter
from viola.services.storage import StorageService
from viola.services.safety_gate import apply_safety_gate


class ViolaPipeline:
    def __init__(
        self,
        *,
        transcriber: TranscriptionService,
        analyzer: NLPAnalysisService,
        cbt_engine: CBTEngine,
        formatter: ResponseFormatter,
        storage: StorageService,
    ) -> None:
        self.transcriber = transcriber
        self.analyzer = analyzer
        self.cbt_engine = cbt_engine
        self.formatter = formatter
        self.storage = storage

    def run_text(self, text: str, session_id: Optional[str] = None) -> Tuple[str, str]:
        sid = session_id or self._new_session_id()

        session = self._load_or_new_domain_session(sid)

        # ---- SAFETY GATE ----
        crisis_response = apply_safety_gate(text, session)
        if crisis_response:
            self._save_domain_session(session)
            return crisis_response, ""

        analysis = self.analyzer.analyze(text)
        cbt = self.cbt_engine.generate(analysis)
        output = self.formatter.format(cbt)

        session = self._load_or_new_domain_session(sid)
        session = session.add_turn(
            user_text=text,
            analysis=Analysis(
                summary=analysis.summary,
                automatic_thought=analysis.auto_thought,
                cognitive_distortions=list(analysis.distortions),
                emotions=dict(analysis.emotion_scores),
                indicators={},
            ),
            plan=CBTPlan(
                socratic_questions=list(cbt.socratic_questions),
                small_step=cbt.behavioral_step,
                coping_statement=None,
            ),
            assistant_text=output,
        )
        self._save_domain_session(session)

        report = SessionReport(
            session_id=sid,
            input_type="text",
            language=settings.language,
            audio_path=None,
            raw_text=text,
            transcript=None,
            analysis={
                "emotion_scores": analysis.emotion_scores,
                "distortions": analysis.distortions,
                "summary": analysis.summary,
                "auto_thought": analysis.auto_thought,
            },
            cbt={
                "summary": cbt.summary,
                "auto_thought": cbt.auto_thought,
                "distortions": cbt.distortions,
                "socratic_questions": cbt.socratic_questions,
                "behavioral_step": cbt.behavioral_step,
            },
            disclaimer=settings.disclaimer,
        )

        saved = self.storage.save_report(report)
        return output, saved

    def run_audio(self, audio_path: str, session_id: Optional[str] = None) -> Tuple[str, str]:
        sid = session_id or self._new_session_id()

        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(audio_path)

            transcript = self.transcriber.transcribe(audio_path)

        except Exception as exc:
            output = (
                "🟣 Viola\n\n"
                "حصلت مشكلة أثناء قراءة الملف الصوتي أو تحويله إلى نص.\n"
                f"المسار: {audio_path}\n"
                f"التفاصيل: {type(exc).__name__}: {exc}\n\n"
                "✅ تأكد إن الملف موجود أو مرّر مسار كامل.\n"
                "✅ جرّب ملف wav لو mp3 عامل مشكلة.\n\n"
                f"⚠️ {settings.disclaimer}"
            )

            session = self._load_or_new_domain_session(sid)
            session = session.add_turn(
                user_text="(audio input)",
                analysis=Analysis(
                    summary="Audio processing failed",
                    automatic_thought=None,
                    cognitive_distortions=[],
                    emotions={},
                    indicators={
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "audio_path": audio_path,
                    },
                ),
                plan=CBTPlan(),
                assistant_text=output,
            )
            self._save_domain_session(session)

            report = SessionReport(
                session_id=sid,
                input_type="audio",
                language=settings.language,
                audio_path=audio_path,
                raw_text=None,
                transcript="",
                analysis={},
                cbt={},
                disclaimer=settings.disclaimer,
            )
            saved = self.storage.save_report(report)
            return output, saved

        if not transcript.text.strip():
            output = (
                "🟣 Viola\n\n"
                "لم يتم تفعيل تحويل الصوت إلى نص بعد في هذه النسخة.\n"
                "جرّب إدخال نص الآن (--text)، وسنضيف transcription قريبًا.\n\n"
                f"⚠️ {settings.disclaimer}"
            )

            session = self._load_or_new_domain_session(sid)
            session = session.add_turn(
                user_text="(audio input)",
                analysis=Analysis(
                    summary="Empty transcript",
                    automatic_thought=None,
                    cognitive_distortions=[],
                    emotions={},
                    indicators={"audio_path": audio_path, "transcript_empty": True},
                ),
                plan=CBTPlan(),
                assistant_text=output,
            )
            self._save_domain_session(session)

            report = SessionReport(
                session_id=sid,
                input_type="audio",
                language=settings.language,
                audio_path=audio_path,
                raw_text=None,
                transcript="",
                analysis={},
                cbt={},
                disclaimer=settings.disclaimer,
            )
            saved = self.storage.save_report(report)
            return output, saved

        analysis = self.analyzer.analyze(transcript.text)
        cbt = self.cbt_engine.generate(analysis)
        output = self.formatter.format(cbt)

        session = self._load_or_new_domain_session(sid)
        session = session.add_turn(
            user_text=transcript.text,
            analysis=Analysis(
                summary=analysis.summary,
                automatic_thought=analysis.auto_thought,
                cognitive_distortions=list(analysis.distortions),
                emotions=dict(analysis.emotion_scores),
                indicators={"audio_path": audio_path},
            ),
            plan=CBTPlan(
                socratic_questions=list(cbt.socratic_questions),
                small_step=cbt.behavioral_step,
                coping_statement=None,
            ),
            assistant_text=output,
        )
        self._save_domain_session(session)

        report = SessionReport(
            session_id=sid,
            input_type="audio",
            language=settings.language,
            audio_path=audio_path,
            raw_text=None,
            transcript=transcript.text,
            analysis={
                "emotion_scores": analysis.emotion_scores,
                "distortions": analysis.distortions,
                "summary": analysis.summary,
                "auto_thought": analysis.auto_thought,
            },
            cbt={
                "summary": cbt.summary,
                "auto_thought": cbt.auto_thought,
                "distortions": cbt.distortions,
                "socratic_questions": cbt.socratic_questions,
                "behavioral_step": cbt.behavioral_step,
            },
            disclaimer=settings.disclaimer,
        )

        saved = self.storage.save_report(report)
        return output, saved

    def _save_domain_session(self, session: Session) -> None:
        os.makedirs("data/domain_sessions", exist_ok=True)
        path = os.path.join("data/domain_sessions", f"{session.session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_or_new_domain_session(self, session_id: str) -> Session:
        path = os.path.join("data/domain_sessions", f"{session_id}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                d: Dict[str, Any] = json.load(f)

            meta = d.get("metadata") or {}
            session = Session.new(
                session_id=d.get("session_id", session_id),
                metadata=Metadata(
                    app_version=meta.get("app_version", "0.1.0"),
                    locale=meta.get("locale", settings.language),
                    source=meta.get("source", "cli"),
                    extra=meta.get("extra", {}) or {},
                ),
            )

            for t in (d.get("turns") or []):
                a = t.get("analysis") or {}
                p = t.get("plan") or {}
                session = session.add_turn(
                    user_text=str(t.get("user_text", "")),
                    analysis=Analysis(
                        summary=str(a.get("summary", "")),
                        automatic_thought=a.get("automatic_thought", None),
                        cognitive_distortions=list(a.get("cognitive_distortions") or []),
                        emotions=dict(a.get("emotions") or {}),
                        indicators=dict(a.get("indicators") or {}),
                    ),
                    plan=CBTPlan(
                        socratic_questions=list(p.get("socratic_questions") or []),
                        small_step=p.get("small_step", None),
                        coping_statement=p.get("coping_statement", None),
                    ),
                    assistant_text=str(t.get("assistant_text", "")),
                )

            return session

        return Session.new(
            session_id=session_id,
            metadata=Metadata(source="cli", locale=settings.language),
        )

    def _new_session_id(self) -> str:
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


