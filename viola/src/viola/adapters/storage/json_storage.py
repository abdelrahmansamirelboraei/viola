from __future__ import annotations

import json
from pathlib import Path
from viola.config.settings import settings
from viola.domain.entities import SessionReport
from viola.services.storage import StorageService


class JsonStorage(StorageService):
    def __init__(self) -> None:
        Path(settings.sessions_dir).mkdir(parents=True, exist_ok=True)

    def save_report(self, report: SessionReport) -> str:
        path = Path(settings.sessions_dir) / f"{report.session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        return str(path)
