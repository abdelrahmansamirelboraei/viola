from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _default_memory_path() -> str:
    # Use per-user AppData folder for stable storage when running as an .exe
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "Viola", "memory.json")


@dataclass
class MemoryConfig:
    path: str = _default_memory_path()
    max_events: int = 2000


class MemoryStore:
    def __init__(self, config: Optional[MemoryConfig] = None) -> None:
        self.config = config or MemoryConfig()
        self._ensure_file()

    def _ensure_file(self) -> None:
        os.makedirs(os.path.dirname(self.config.path), exist_ok=True)
        if not os.path.exists(self.config.path):
            self._write({
                "version": 1,
                "created_at": _utc_now_iso(),
                "users": {}
            })

    def _read(self) -> Dict[str, Any]:
        with open(self.config.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        with open(self.config.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_user(self, user_id: str = "default") -> Dict[str, Any]:
        db = self._read()
        users = db.setdefault("users", {})
        user = users.get(user_id)
        if user is None:
            user = {
                "created_at": _utc_now_iso(),
                "events": [],
                "stats": {
                    "total_messages": 0,
                    "emotion_counts": {},
                    "distortion_counts": {},
                    "crisis_count": 0,
                    "avg_severity": 0.0,
                    "last_severity": None,
                    "last_top_emotion": None,
                    "last_updated_at": None,
                    "checkins_count": 0,
                    "avg_checkin_mood": 0.0,
                    "last_checkin_mood": None,
                },
            }
            users[user_id] = user
            self._write(db)
        return user

    def get_events(self, user_id: str = "default") -> List[Dict[str, Any]]:
        user = self.get_user(user_id)
        return list(user.get("events", []) or [])

    def get_events_since_days(self, user_id: str = "default", days: int = 7) -> List[Dict[str, Any]]:
        events = self.get_events(user_id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        out: List[Dict[str, Any]] = []
        for e in events:
            ts = e.get("ts")
            if not isinstance(ts, str):
                continue
            dt = _parse_iso(ts)
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                out.append(e)
        return out

    def _append_event_core(self, user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        db = self._read()
        users = db.setdefault("users", {})
        user = users.get(user_id)
        if user is None:
            user = self.get_user(user_id)
            db = self._read()
            users = db.setdefault("users", {})
            user = users[user_id]

        events: List[Dict[str, Any]] = user.setdefault("events", [])
        events.append(event)

        if len(events) > self.config.max_events:
            del events[: len(events) - self.config.max_events]

        stats = user.setdefault("stats", {})
        stats["last_updated_at"] = event.get("ts")
        users[user_id] = user
        db["users"] = users
        self._write(db)
        return event

    def append_event(self, user_id: str, text: str, analysis_dict: Dict[str, Any], mode: str) -> Dict[str, Any]:
        event = {
            "ts": _utc_now_iso(),
            "type": "message",
            "mode": mode,
            "text": text,
            "severity": analysis_dict.get("severity"),
            "top_emotion": (analysis_dict.get("emotions") or [{}])[0].get("name") if analysis_dict.get("emotions") else None,
            "emotions": analysis_dict.get("emotions", []),
            "distortions": analysis_dict.get("distortions", []),
            "crisis_flag": analysis_dict.get("crisis_flag", False),
        }

        user = self.get_user(user_id)
        stats = user.setdefault("stats", {})
        stats["total_messages"] = int(stats.get("total_messages", 0)) + 1

        sev = analysis_dict.get("severity")
        if isinstance(sev, int):
            prev_avg = float(stats.get("avg_severity", 0.0))
            n = stats["total_messages"]
            stats["avg_severity"] = prev_avg + (sev - prev_avg) / float(n)
            stats["last_severity"] = sev

        emo_counts: Dict[str, int] = stats.setdefault("emotion_counts", {})
        for e in analysis_dict.get("emotions", []):
            name = e.get("name")
            if name:
                emo_counts[name] = int(emo_counts.get(name, 0)) + 1

        dist_counts: Dict[str, int] = stats.setdefault("distortion_counts", {})
        for d in analysis_dict.get("distortions", []):
            name = d.get("name")
            if name:
                dist_counts[name] = int(dist_counts.get(name, 0)) + 1

        if analysis_dict.get("crisis_flag") is True:
            stats["crisis_count"] = int(stats.get("crisis_count", 0)) + 1

        top_emotion = event.get("top_emotion")
        if top_emotion:
            stats["last_top_emotion"] = top_emotion

        db = self._read()
        db.setdefault("users", {})[user_id] = user
        self._write(db)

        return self._append_event_core(user_id, event)

    def append_checkin(self, user_id: str, mood: int, note: str = "") -> Dict[str, Any]:
        mood = max(0, min(100, int(mood)))

        event = {
            "ts": _utc_now_iso(),
            "type": "checkin",
            "mood": mood,
            "note": note,
        }

        user = self.get_user(user_id)
        stats = user.setdefault("stats", {})
        stats["checkins_count"] = int(stats.get("checkins_count", 0)) + 1
        n = stats["checkins_count"]

        prev_avg = float(stats.get("avg_checkin_mood", 0.0))
        stats["avg_checkin_mood"] = prev_avg + (mood - prev_avg) / float(n)
        stats["last_checkin_mood"] = mood

        db = self._read()
        db.setdefault("users", {})[user_id] = user
        self._write(db)

        return self._append_event_core(user_id, event)

    def get_summary(self, user_id: str = "default") -> Dict[str, Any]:
        user = self.get_user(user_id)
        stats = user.get("stats", {})
        events = user.get("events", [])

        emo_counts = stats.get("emotion_counts", {}) or {}
        dist_counts = stats.get("distortion_counts", {}) or {}

        top_emotion = max(emo_counts.items(), key=lambda x: x[1])[0] if emo_counts else None
        top_distortion = max(dist_counts.items(), key=lambda x: x[1])[0] if dist_counts else None

        return {
            "user_id": user_id,
            "total_messages": stats.get("total_messages", 0),
            "avg_severity": stats.get("avg_severity", 0.0),
            "last_severity": stats.get("last_severity"),
            "last_top_emotion": stats.get("last_top_emotion"),
            "top_emotion_overall": top_emotion,
            "top_distortion_overall": top_distortion,
            "crisis_count": stats.get("crisis_count", 0),
            "events_count": len(events),
            "last_updated_at": stats.get("last_updated_at"),
            "checkins_count": stats.get("checkins_count", 0),
            "avg_checkin_mood": stats.get("avg_checkin_mood", 0.0),
            "last_checkin_mood": stats.get("last_checkin_mood"),
        }
