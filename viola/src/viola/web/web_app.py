from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Optional

from flask import Flask, render_template, request, jsonify, redirect, session, abort

from viola.pipelines.main_pipeline import ViolaPipeline
from viola.adapters.analyzers.rule_based_ar import RuleBasedArabicAnalyzer
from viola.adapters.storage.json_storage import JsonStorage
from viola.services.cbt_engine import CBTEngine
from viola.services.response import ResponseFormatter


# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


# ---------- Credentials ----------
DEV_USER = os.getenv("VIOLA_DEV_USERNAME", "")
DEV_PASS = os.getenv("VIOLA_DEV_PASSWORD", "")
APP_USER = os.getenv("VIOLA_USER_USERNAME", "")
APP_PASS = os.getenv("VIOLA_USER_PASSWORD", "")
SECRET_KEY = os.getenv("VIOLA_SECRET_KEY", "dev-secret-change-me")


def build_pipeline() -> ViolaPipeline:
    return ViolaPipeline(
        transcriber=None,
        analyzer=RuleBasedArabicAnalyzer(),
        cbt_engine=CBTEngine(),
        formatter=ResponseFormatter(),
        storage=JsonStorage(),
    )


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )
    app.secret_key = SECRET_KEY
    # ---- security hardening (auto-added) ----
    if not SECRET_KEY or SECRET_KEY.strip() == "" or SECRET_KEY == "dev-secret-change-me":
        raise RuntimeError("VIOLA_SECRET_KEY must be set to a strong value (not default).")

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False

    if not (DEV_USER and DEV_PASS and APP_USER and APP_PASS):
        raise RuntimeError("VIOLA_* credentials must be set (DEV_USER/DEV_PASS/APP_USER/APP_PASS).")
    # -----------------------------------------


    pipeline = build_pipeline()

    def require_login(role: Optional[str] = None) -> None:
        user_role = session.get("role")
        if not user_role:
            abort(401)
        if role and user_role != role:
            abort(403)

    @app.get("/")
    def home():
        return redirect("/login")

    @app.get("/login")
    def login_page():
        return render_template("login.html")

    @app.get("/chat")
    def chat_page():
        require_login(role="user")
        return render_template("client.html")

    @app.get("/admin")
    def admin_page():
        require_login(role="developer")
        return render_template("admin.html")

    @app.post("/api/login")
    def api_login():
        payload: dict[str, Any] = request.get_json(force=True) or {}
        role = (payload.get("role") or "").strip()
        username = (payload.get("username") or "").strip()
        password = (payload.get("password") or "").strip()
    # ---- security hardening (auto-added) ----
    if (username is None) or (password is None) or str(username).strip() == "" or str(password).strip() == "":
        return jsonify({"ok": False, "error": "username/password required"}), 400
    # -----------------------------------------

        if role not in {"user", "developer"}:
            return jsonify({"ok": False}), 400

        if role == "developer":
            ok = (username == DEV_USER) and (password == DEV_PASS)
        else:
            ok = (username == APP_USER) and (password == APP_PASS)

        if not ok:
            return jsonify({"ok": False}), 401

        session.clear()
        session["role"] = role
        session["username"] = username
        session["sid"] = uuid.uuid4().hex  # 🔥 fixed session_id

        return jsonify({"ok": True, "role": role})

    @app.post("/api/chat")
    def api_chat():
        require_login(role="user")

        payload = request.get_json(force=True) or {}
        text = (payload.get("text") or "").strip()
        if not text:
            return jsonify({"ok": False, "error": "Empty text"}), 400

        sid = session.get("sid")
        if not sid:
            sid = uuid.uuid4().hex
            session["sid"] = sid

        output, _ = pipeline.run_text(text, session_id=sid)

        return jsonify({"ok": True, "response": output})

    

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app


def run_web(host: str = "127.0.0.1", port: int = 8000) -> None:
    app = create_app()
    app.run(host=host, port=port, debug=False)
