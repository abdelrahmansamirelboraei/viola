import argparse
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def _parse_junit(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {"found": False}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Handle both <testsuite> and <testsuites>
        if root.tag == "testsuite":
            suites = [root]
        else:
            suites = root.findall("testsuite")

        total = failures = errors = skipped = 0
        duration = 0.0

        for s in suites:
            total += int(s.attrib.get("tests", 0))
            failures += int(s.attrib.get("failures", 0))
            errors += int(s.attrib.get("errors", 0))
            skipped += int(s.attrib.get("skipped", 0))
            try:
                duration += float(s.attrib.get("time", 0.0))
            except Exception:
                pass

        return {
            "found": True,
            "total": total,
            "failures": failures,
            "errors": errors,
            "skipped": skipped,
            "duration": duration,
        }
    except Exception:
        return {"found": False}


def _run_pytest(args_list: list[str]) -> int:
    cmd = [sys.executable, "-m", "pytest"] + args_list
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="viola_test",
        description="Run Viola system tests with a clean summary.",
    )

    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--all", action="store_true", help="Run all system tests (default).")
    scope.add_argument("--pipeline", action="store_true", help="Run only pipeline system tests.")
    scope.add_argument("--cli", action="store_true", help="Run only CLI system tests.")
    scope.add_argument("--api", action="store_true", help="Run only API system tests.")

    parser.add_argument("--no-junit", action="store_true", help="Do not write JUnit XML report.")
    parser.add_argument("--quiet", action="store_true", help="Pass -q to pytest.")
    parser.add_argument("--verbose", action="store_true", help="Pass -v to pytest.")
    parser.add_argument("--maxfail", type=int, default=0, help="Stop after N failures (0 = no limit).")

    ns, extra = parser.parse_known_args()

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    junit_path = reports_dir / "system-tests.xml"

    # Build pytest args
    pytest_args: list[str] = ["-m", "system"]

    if ns.pipeline:
        pytest_args += ["-k", "pipeline"]
    elif ns.cli:
        pytest_args += ["-k", "cli"]
    elif ns.api:
        pytest_args += ["-k", "api"]
    else:
        # default: all system tests
        pass

    if ns.quiet:
        pytest_args += ["-q"]
    if ns.verbose:
        pytest_args += ["-v"]

    if ns.maxfail and ns.maxfail > 0:
        pytest_args += [f"--maxfail={ns.maxfail}"]

    if not ns.no_junit:
        pytest_args += [f"--junitxml={junit_path.as_posix()}"]

    # Allow extra args passthrough
    pytest_args += extra

    print("=" * 72)
    print("Viola System Test Runner")
    print(f"Command: python -m pytest {' '.join(pytest_args)}")
    print("=" * 72)

    start = time.time()
    code = _run_pytest(pytest_args)
    wall = time.time() - start

    # Summary
    summary = _parse_junit(junit_path) if not ns.no_junit else {"found": False}

    print("\n" + "-" * 72)
    if summary.get("found"):
        total = summary["total"]
        failures = summary["failures"]
        errors = summary["errors"]
        skipped = summary["skipped"]
        dur = summary["duration"]

        passed = total - failures - errors - skipped
        status = "PASS" if code == 0 else "FAIL"

        print(f"Result: {status}")
        print(f"Total: {total} | Passed: {passed} | Skipped: {skipped} | Failures: {failures} | Errors: {errors}")
        print(f"Time:  {dur:.2f}s (pytest) | {wall:.2f}s (wall)")
        print(f"Report: {junit_path.as_posix()}")
    else:
        status = "PASS" if code == 0 else "FAIL"
        print(f"Result: {status}")
        print(f"Time:  {wall:.2f}s (wall)")
        if not ns.no_junit:
            print("Report: (not found / could not parse)")

    print("-" * 72)

    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
