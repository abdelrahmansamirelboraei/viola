from __future__ import annotations

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from viola.router import process_text
from viola.reporting.weekly import build_weekly_report, format_weekly_report
from viola.growth.planner import GrowthPlanner, format_weekly_plan

app = Flask(__name__, template_folder="web/templates")
app.secret_key = "CHANGE_ME_TO_SOMETHING_RANDOM_AND_LONG"

USERS = {"admin": generate_password_hash("admin123")}

def require_login() -> bool:
    return "user_id" in session

@app.get("/")
def home():
    return redirect(url_for("chat_page")) if require_login() else redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()

    if not username or not password:
        flash("اكتب اليوزر والباسورد.")
        return redirect(url_for("login"))

    stored = USERS.get(username)
    if stored and check_password_hash(stored, password):
        session["user_id"] = username
        return redirect(url_for("chat_page"))

    flash("بيانات الدخول غلط.")
    return redirect(url_for("login"))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/chat")
def chat_page():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("chat.html", user_id=session["user_id"])

@app.post("/chat")
def chat_send():
    if not require_login():
        return redirect(url_for("login"))

    text = (request.form.get("text") or "").strip()
    if not text:
        flash("اكتب رسالة.")
        return redirect(url_for("chat_page"))

    out = process_text(text, user_id=session["user_id"])
    mode = out.get("mode")
    analysis = out.get("analysis", {}) or {}

    reply = ""
    if mode == "crisis":
        resp = out.get("response", {}) or {}
        reply = (resp.get("message", "") or "") + "\n\n" + "\n".join(["- " + s for s in (resp.get("steps_now", []) or [])])
    else:
        sev = analysis.get("severity")
        emotions = analysis.get("emotions", []) or []
        top_emo = emotions[0].get("name") if emotions else None
        reply = f"شدة الشعور: {sev}\n"
        if top_emo:
            reply += f"الشعور الأوضح: {top_emo}\n"

    return render_template("chat.html", user_id=session["user_id"], last_text=text, last_reply=reply, mode=mode)

@app.get("/report")
def report_page():
    if not require_login():
        return redirect(url_for("login"))
    rep = build_weekly_report(user_id=session["user_id"], days=7)
    return render_template("report.html", user_id=session["user_id"], report_text=format_weekly_report(rep))

@app.get("/plan")
def plan_page():
    if not require_login():
        return redirect(url_for("login"))
    plan = GrowthPlanner().build_weekly_plan(user_id=session["user_id"], days=7)
    return render_template("plan.html", user_id=session["user_id"], plan_text=format_weekly_plan(plan))
