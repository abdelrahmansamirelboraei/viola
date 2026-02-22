from __future__ import annotations

import json
from typing import Any, Dict

from viola.router import process_text
from viola.formatting.arabic_formatter import format_payload
from viola.reporting.weekly import build_weekly_report, format_weekly_report
from viola.growth.planner import GrowthPlanner, format_weekly_plan
from viola.growth.checkin import run_checkin


_RLM = "\u200F"


def _rtl_lines(s: str) -> str:
    return "\n".join([_RLM + line for line in s.splitlines()])


def run_cli(text: str, user_id: str = "default", as_json: bool = True) -> int:
    payload: Dict[str, Any] = process_text(text, user_id=user_id)

    if as_json:
        out = json.dumps(payload, ensure_ascii=False, indent=2)
        print(_rtl_lines(out))
        return 0

    print(format_payload(payload))
    return 0


def run_report(user_id: str = "default", days: int = 7, as_json: bool = False) -> int:
    report = build_weekly_report(user_id=user_id, days=days)

    if as_json:
        out = json.dumps(report, ensure_ascii=False, indent=2)
        print(_rtl_lines(out))
        return 0

    print(format_weekly_report(report))
    return 0


def run_plan(user_id: str = "default", days: int = 7, as_json: bool = False) -> int:
    plan = GrowthPlanner().build_weekly_plan(user_id=user_id, days=days)

    if as_json:
        out = json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)
        print(_rtl_lines(out))
        return 0

    print(format_weekly_plan(plan))
    return 0


def run_daily_checkin(user_id: str, mood: int, note: str = "", as_json: bool = False) -> int:
    if as_json:
        # store + output as json-ish
        from viola.memory.store import MemoryStore
        store = MemoryStore()
        ev = store.append_checkin(user_id=user_id, mood=mood, note=note)
        summary = store.get_summary(user_id)
        out = json.dumps({"event": ev, "memory_summary": summary}, ensure_ascii=False, indent=2)
        print(_rtl_lines(out))
        return 0

    print(run_checkin(user_id=user_id, mood=mood, note=note))
    return 0
