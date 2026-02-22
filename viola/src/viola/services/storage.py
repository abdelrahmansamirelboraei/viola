from __future__ import annotations

from abc import ABC, abstractmethod
from viola.domain.entities import SessionReport


class StorageService(ABC):
    @abstractmethod
    def save_report(self, report: SessionReport) -> str:
        # Persist report and return path
        raise NotImplementedError
