from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class Metadata:
    app_version: str = "0.1.0"
    locale: str = "ar"
    source: str = "cli"
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Analysis:
    summary: str
    automatic_thought: Optional[str] = None
    cognitive_distortions: List[str] = field(default_factory=list)
    emotions: Dict[str, float] = field(default_factory=dict)
    indicators: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CBTPlan:
    socratic_questions: List[str] = field(default_factory=list)
    small_step: Optional[str] = None
    coping_statement: Optional[str] = None


@dataclass(frozen=True)
class Turn:
    turn_id: str
    created_at: str
    user_text: str
    analysis: Analysis
    plan: CBTPlan
    assistant_text: str


@dataclass(frozen=True)
class Session:
    session_id: str
    created_at: str
    updated_at: str
    turns: List[Turn] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)

    @staticmethod
    def new(session_id: str, metadata: Optional[Metadata] = None) -> "Session":
        now = utc_now_iso()
        return Session(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            turns=[],
            metadata=metadata or Metadata(),
        )

    def add_turn(
        self,
        user_text: str,
        analysis: Analysis,
        plan: CBTPlan,
        assistant_text: str,
    ) -> "Session":
        now = utc_now_iso()
        t = Turn(
            turn_id=new_id("turn"),
            created_at=now,
            user_text=user_text,
            analysis=analysis,
            plan=plan,
            assistant_text=assistant_text,
        )
        return Session(
            session_id=self.session_id,
            created_at=self.created_at,
            updated_at=now,
            turns=[*self.turns, t],
            metadata=self.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
