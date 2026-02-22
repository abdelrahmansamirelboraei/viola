import ast
import importlib
import inspect
import json
import pkgutil
from types import ModuleType
from typing import Any, Callable, Optional, Tuple

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


def _safe_import(mod_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(mod_name)
    except Exception:
        return None


def _looks_like_pipeline(obj: Any) -> bool:
    return any(hasattr(obj, m) and callable(getattr(obj, m)) for m in PIPELINE_METHOD_CANDIDATES)


def _call_pipeline(pipeline: Any, text: str) -> Any:
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

        # Prefer direct text handlers
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

        # Otherwise look for pipeline builders
        for name in BUILD_FN_CANDIDATES:
            fn = getattr(mod, name, None)
            if callable(fn):
                hints.append(f"{mod.__name__}.{name}")
                return fn, None, hints

    return None, None, hints


def _as_structured(output: Any) -> Any:
    if isinstance(output, (dict, list)):
        return output

    if isinstance(output, str):
        s = output.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except Exception:
                try:
                    return ast.literal_eval(s)
                except Exception:
                    return output

    return output


def run_pipeline(text: str) -> Any:
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
        "Tried text functions: " + ", ".join(sorted(TEXT_FN_CANDIDATES)) + "\n"
        "And pipeline builders: " + ", ".join(sorted(BUILD_FN_CANDIDATES)) + "\n\n"
        "Discovered candidates (first 50):\n" + hint_text
    )


def run_viola(text: str) -> Any:
    return _as_structured(run_pipeline(text))
