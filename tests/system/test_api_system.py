import json
from pathlib import Path

import pytest
import requests

BASE_URL = "http://127.0.0.1:5000"
ENDPOINT = "/api/analyze"

CASES_DIR = Path(__file__).parent / "cases"

def load_cases():
    for p in sorted(CASES_DIR.glob("*.json")):
        yield json.loads(p.read_text(encoding="utf-8"))

def server_up():
    try:
        r = requests.get(BASE_URL, timeout=1)
        return r.status_code < 500
    except Exception:
        return False

@pytest.mark.system
@pytest.mark.parametrize("case", list(load_cases()), ids=lambda c: c["id"])
def test_api_system(case):
    if not server_up():
        pytest.skip("API server is not running on 127.0.0.1:5000")

    payload = {"text": case["input_text"]}
    r = requests.post(BASE_URL + ENDPOINT, json=payload, timeout=15)
    assert r.status_code == 200

    data = r.json()
    output = data.get("output") or data.get("response") or ""
    assert isinstance(output, str)
    assert output.strip() != ""
