import json
import subprocess
import sys
from pathlib import Path

import pytest

CASES_DIR = Path(__file__).parent / "cases"

def load_cases():
    for p in sorted(CASES_DIR.glob("*.json")):
        yield json.loads(p.read_text(encoding="utf-8"))

@pytest.mark.system
@pytest.mark.parametrize("case", list(load_cases()), ids=lambda c: c["id"])
def test_cli_system(case):
    cmd = [
        sys.executable, "-m", "viola",
        "--text", case["input_text"]
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    assert r.returncode == 0, (r.stdout + "\n" + r.stderr)

    out = (r.stdout or "") + (r.stderr or "")
    assert "Traceback" not in out
    assert "NameError" not in out
