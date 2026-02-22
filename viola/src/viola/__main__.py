from __future__ import annotations

import argparse
import sys

from viola.adapters.io.cli import run_cli, run_report, run_plan, run_daily_checkin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="viola", description="Viola: Arabic CBT assistant (CLI)")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--text", "-t", type=str, help="Input text (Arabic supported)")
    mode.add_argument("--report", action="store_true", help="Print a mood/CBT tracking report from memory")
    mode.add_argument("--plan", action="store_true", help="Print a weekly growth plan based on memory")
    mode.add_argument("--checkin", action="store_true", help="Log a daily check-in mood score (0-100)")

    parser.add_argument("--user", "-u", type=str, default="default", help="User id for memory store")
    parser.add_argument("--days", type=int, default=7, help="Range in days (used with --report/--plan)")

    parser.add_argument("--mood", type=int, help="Check-in mood 0-100 (required with --checkin)")
    parser.add_argument("--note", type=str, default="", help="Optional check-in note (used with --checkin)")

    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--plain", action="store_true", help="Output plain text (therapeutic/pretty)")

    args = parser.parse_args(argv)

    if args.report:
        as_json = True if args.json else False
        return run_report(user_id=args.user, days=args.days, as_json=as_json)

    if args.plan:
        as_json = True if args.json else False
        return run_plan(user_id=args.user, days=args.days, as_json=as_json)

    if args.checkin:
        if args.mood is None:
            parser.error("--mood is required with --checkin (0-100).")
        as_json = True if args.json else False
        return run_daily_checkin(user_id=args.user, mood=args.mood, note=args.note, as_json=as_json)

    # text mode:
    as_json = True
    if args.plain:
        as_json = False
    if args.json:
        as_json = True

    return run_cli(text=args.text, user_id=args.user, as_json=as_json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
