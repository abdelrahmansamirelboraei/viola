import ast
import json
import importlib
import inspect
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional, Tuple, Any

import pytest

CASES_DIR = Path(__file__).parent / "cases"

BUILD_FN_CANDIDATES = {
    "build_pipeline",
    "build_default_pipeline",
    "create_pipeline",
    "make_pipeline",
    "get_pipeline",
}

TEXT_FN_CANDIDATES = {
    "handle_text",
    "analyze_text",
    "process_text",
    "run_text",
    "respond",
    "generate_response",
}

PIPELINE_METHOD_CANDIDATES = ("run", "process", "analyze", "__call__")


def load_cases():
    for p in sorted(CASES_DIR.glob("*.json")):
        yield json.loads(p.read_text(encoding="utf-8"))


def _safe_import(mod_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(mod_name)
    except Exception:
        return None


def _looks_like_pipeline(obj) -> bool:
    return any(hasattr(obj, m) and callable(getattr(obj, m)) for m in PIPELINE_METHOD_CANDIDATES)


def _call_pipeline(pipeline, text: str):
    for m in PIPELINE_METHOD_CANDIDATES:
        if hasattr(pipeline, m) and callable(getattr(pipeline, m)):
            return getattr(pipeline, m)(text)
    raise RuntimeError("Pipeline object found but no callable method matched.")


def _find_entrypoint() -> Tuple[Optional[Callable], Optional[Callable], list[str]]:
    hints: list[str] = []

    viola = _safe_import("viola")
    if not viola or not hasattr(viola, "__path__"):
        return None, None, ["Could not import 'viola' package. Is it importable from this venv?"]

    for modinfo in pkgutil.walk_packages(viola.__path__, viola.__name__ + "."):
        mod = _safe_import(modinfo.name)
        if not mod:
            continue

        for name in TEXT_FN_CANDIDATES:
            fn = getattr(mod, name, None)
            if callable(fn):
                hints.append(f"{mod.__name__}.{name}")
                try:
                    sig = inspect.signature(fn)
                    params = list(sig.parameters.values())
                    if len(params) >= 1:
                        return None, fn, hints
                except Exception:
                    return None, fn, hints

        for name in BUILD_FN_CANDIDATES:
            fn = getattr(mod, name, None)
            if callable(fn):
                hints.append(f"{mod.__name__}.{name}")
                return fn, None, hints

    return None, None, hints


def run_pipeline(text: str):
    build_fn, text_fn, hints = _find_entrypoint()

    if text_fn:
        return text_fn(text)

    if build_fn:
        pipeline = build_fn()
        if not _looks_like_pipeline(pipeline):
            if isinstance(pipeline, dict):
                for k in ("pipeline", "app", "engine"):
                    if k in pipeline and _looks_like_pipeline(pipeline[k]):
                        return _call_pipeline(pipeline[k], text)
            raise RuntimeError(
                "Found a pipeline builder but returned object doesn't look like a pipeline. "
                f"Builder: {build_fn.__module__}.{build_fn.__name__}"
            )
        return _call_pipeline(pipeline, text)

    hint_text = "\n".join(hints[:50]) if hints else "(no hints found)"
    raise NotImplementedError(
        "Could not auto-discover a Viola pipeline entrypoint.\n"
        "Searched for text functions: " + ", ".join(sorted(TEXT_FN_CANDIDATES)) + "\n"
        "And pipeline builders: " + ", ".join(sorted(BUILD_FN_CANDIDATES)) + "\n\n"
        "Discovered candidates (first 50):\n" + hint_text
    )


def _as_structured(output: Any) -> Any:
    # If it's already dict/list, keep it
    if isinstance(output, (dict, list)):
        return output

    # If it's string that looks like JSON or python dict repr, parse it
    if isinstance(output, str):
        s = output.strip()
        if s.startswith("{") or s.startswith("["):
            # Try JSON first
            try:
                return json.loads(s)
            except Exception:
                # Fallback to Python literal (dict repr)
                try:
                    return ast.literal_eval(s)
                except Exception:
                    return output

    return output


def _get_path(obj: Any, path: str):
    # dotted path access for dicts: "analysis.severity"
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(f"Missing path: {path} (stuck at '{part}')")
    return cur


@pytest.mark.system
@pytest.mark.parametrize("case", list(load_cases()), ids=lambda c: c["id"])
def test_pipeline_system(case):
    raw = run_pipeline(case["input_text"])
    data = _as_structured(raw)

    exp = case.get("expect", {})

    # Basic checks
    assert data is not None

    # If we expect structured output, enforce dict
    if exp.get("output_type") == "dict":
        assert isinstance(data, dict), f"Expected dict output but got: {type(data)}\nRAW:\n{raw}"

    # Must-have paths
    for p in exp.get("must_have_paths", []):
        _ = _get_path(data, p)

    # Equals checks
    for p, v in exp.get("equals", {}).items():
        got = _get_path(data, p)
        assert got == v, f"Path {p} expected {v} but got {got}"

    # Severity range checks
    if "severity_min" in exp:
        sev = _get_path(data, "analysis.severity")
        assert sev >= exp["severity_min"], f"severity {sev} < min {exp['severity_min']}"
    if "severity_max" in exp:
        sev = _get_path(data, "analysis.severity")
        assert sev <= exp["severity_max"], f"severity {sev} > max {exp['severity_max']}"

    # Crisis flag check
    if "crisis_flag" in exp:
        cf = _get_path(data, "analysis.crisis_flag")
        assert cf == exp["crisis_flag"], f"crisis_flag expected {exp['crisis_flag']} got {cf}"

    # Emotion check: any emotion.name in list
    if "emotion_any_of" in exp:
        emotions = _get_path(data, "analysis.emotions")
        names = []
        if isinstance(emotions, list):
            for e in emotions:
                if isinstance(e, dict) and "name" in e:
                    names.append(e["name"])
        assert any(n in exp["emotion_any_of"] for n in names), f"Expected emotion any of {exp['emotion_any_of']} but got {names}"

    # Not-contains (apply to raw string too, for safety)
    raw_s = raw if isinstance(raw, str) else str(raw)
    for bad in exp.get("not_contains_any", []):
        assert bad not in raw_s
