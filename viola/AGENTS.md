# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Viola is an Arabic-language CBT (Cognitive Behavioral Therapy) self-help assistant. It accepts Arabic text or audio input, performs rule-based NLP analysis (emotion detection, cognitive distortion identification), generates CBT-style responses (Socratic questions, behavioral steps), and outputs results in Arabic with RTL support. It is **not** a medical tool—always include the disclaimer from `config/settings.py`.

## Build & Run Commands

The project uses a Python venv at `.venv/` and has no `pyproject.toml` build config yet (the file is empty). Dependencies include `pydantic`, `faster-whisper` (optional, for audio), `arabic-reshaper`, and `python-bidi`.

```shell
# Activate the virtual environment
source .venv/Scripts/activate   # Windows-style venv (Scripts/ not bin/)

# Run with text input
python -m viola --text "أنا مش قادر أركز"

# Run with audio input (requires faster-whisper)
python -m viola --audio path/to/file.wav

# Run web chat UI (opens browser, serves on localhost:8765)
python -m viola --web

# Run guided CBT web chat (multi-step Socratic deepening)
python -m viola --web --guided

# Continue the last session
python -m viola --text "..." --continue

# Continue a specific session
python -m viola --text "..." --session 20260220_023033

# Open HTML timeline output in browser
python -m viola --text "..." --html
```

There are currently **no tests, no linter config, and no CI** set up.

## Architecture

The codebase follows a **hexagonal (ports & adapters)** pattern under `src/viola/`:

### Domain Layer (`domain/`)
- `entities.py` — Core data classes: `Transcript`, `AnalysisResult`, `CBTResponse`, `SessionReport`. These are the pipeline's lingua franca.
- `models.py` — Immutable frozen dataclasses for persistence: `Session`, `Turn`, `Analysis`, `CBTPlan`, `Metadata`. `Session` uses a functional append pattern (`add_turn()` returns a new `Session`).
- `cbt_models.py` — An extended variant of `models.py` with additional fields (`tags`, `device`, `model`). **Note:** both `models.py` and `cbt_models.py` define classes with the same names (`Session`, `Turn`, `Analysis`, etc.) — the pipeline currently imports from `models.py`.

### Services Layer (`services/`) — Abstract ports
- `transcription.py` — `TranscriptionService` ABC (audio → `Transcript`)
- `nlp_analysis.py` — `NLPAnalysisService` ABC (text → `AnalysisResult`)
- `storage.py` — `StorageService` ABC (persist `SessionReport`)
- `cbt_engine.py` — `CBTEngine` (concrete, not abstract): generates `CBTResponse` from `AnalysisResult` with hardcoded Arabic Socratic questions and behavioral steps.
- `response.py` — `ResponseFormatter`: formats `CBTResponse` into human-readable Arabic markdown-like text.
- `guided_cbt_manager.py` — `GuidedCBTManager`: stateful rule-based FSM that drives multi-turn guided CBT sessions through stages (clarify → thought → emotions → evidence_for → evidence_against → alternative → balanced → action → review). Stores state in the domain session JSON under `guided_state`.
- `session_summary.py` — `build_session_summary()`: aggregates turns into an Arabic session summary with top distortions and emotions.

### Adapters Layer (`adapters/`) — Concrete implementations
- `analyzers/rule_based_ar.py` — `RuleBasedArabicAnalyzer`: implements `NLPAnalysisService` using keyword/substring matching against hardcoded Arabic emotion and distortion lexicons. No ML models.
- `transcribers/whisper_transcriber.py` — `FasterWhisperTranscriber`: implements `TranscriptionService` using `faster-whisper`. Loaded lazily; gracefully falls back to `None` if the package is missing.
- `transcribers/dummy.py` — `DummyTranscriber`: returns empty transcript (testing fallback).
- `storage/json_storage.py` — `JsonStorage`: implements `StorageService`, writes session reports as JSON to `data/sessions/`.
- `io/cli.py` — CLI adapter: dispatches `--text`, `--audio`, `--web` modes; handles `--continue` and `--html` flags.
- `io/web_chat.py` — Embedded HTTP server (stdlib `http.server`) serving an inline RTL HTML/JS chat UI on port 8765. API endpoints: `GET /api/session`, `POST /api/message`, `POST /api/end`.

### Pipeline (`pipelines/main_pipeline.py`)
`ViolaPipeline` is the central orchestrator. It wires together all services and:
1. Accepts text or audio input
2. Runs transcription (audio only) → analysis → CBT generation → formatting
3. Persists both a flat `SessionReport` (to `data/sessions/`) and a domain `Session` (to `data/domain_sessions/`)

### Exporters (`exporters/html_exporter.py`)
Renders a domain session JSON into a standalone dark-themed RTL HTML timeline page, saved under `data/html/`.

### Entry Point (`__main__.py`)
Constructs the pipeline via `_build_pipeline()` (tries whisper, falls back to `None`) and delegates to `run_cli()`.

## Key Design Decisions

- **All domain models are frozen dataclasses** — mutations return new instances.
- **Two parallel persistence paths**: `data/sessions/` (flat reports) and `data/domain_sessions/` (full session with turns). The pipeline writes both.
- **Session IDs are timestamps** (`YYYYMMDD_HHMMSS`) generated via `datetime.utcnow()`.
- **The NLP analysis is entirely rule-based** (no ML inference at runtime). The emotion/distortion lexicons live in `RuleBasedArabicAnalyzer`.
- **Web chat is a zero-dependency embedded server** — no Flask/FastAPI. The full HTML/CSS/JS is an inline string in `web_chat.py`.
- **Arabic RTL** is a first-class concern throughout: HTML templates use `dir="rtl"`, `lang="ar"`, and all user-facing text is Arabic.

## Data Directories

- `data/sessions/` — Flat JSON session reports (one per run)
- `data/domain_sessions/` — Full multi-turn domain sessions (accumulated across `--continue` runs)
- `data/html/` — Generated HTML timeline exports
