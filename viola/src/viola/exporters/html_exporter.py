from __future__ import annotations

import html
import json
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from viola.config.settings import settings


def _escape(s: str) -> str:
    return html.escape(s or "")


def _badge(text: str) -> str:
    return f'<span class="badge">{_escape(text)}</span>'


def _ul(items: List[str]) -> str:
    if not items:
        return '<p class="muted">—</p>'
    lis = "".join(f"<li>{_escape(x)}</li>" for x in items)
    return f"<ul>{lis}</ul>"


def _format_ts(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y — %H:%M UTC")
    except Exception:
        return ts


def _render_turn(turn: Dict[str, Any], idx: int, total: int) -> str:
    created_at = _format_ts(str(turn.get("created_at", "")))
    user_text = str(turn.get("user_text", ""))
    assistant_text = str(turn.get("assistant_text", ""))

    analysis = turn.get("analysis") or {}
    plan = turn.get("plan") or {}

    summary = str(analysis.get("summary", "") or "")
    auto_thought = str(analysis.get("automatic_thought", "") or "")
    distortions = analysis.get("cognitive_distortions") or []
    emotions = analysis.get("emotions") or {}
    questions = plan.get("socratic_questions") or []
    small_step = str(plan.get("small_step", "") or "")

    emotions_html = (
        "".join(_badge(f"{k} ({float(v):.2f})") for k, v in emotions.items())
        if isinstance(emotions, dict) and emotions
        else '<p class="muted">—</p>'
    )

    distortions_html = (
        "".join(_badge(str(x)) for x in distortions)
        if distortions
        else '<p class="muted">—</p>'
    )

    open_attr = " open" if idx == total else ""

    return f"""
    <div class="tl_item anim">
      <div class="tl_marker" aria-hidden="true">
        <div class="dot"></div>
      </div>

      <details class="turn card"{open_attr}>
        <summary class="turn_head">
          <div class="turn_title">الدور {idx}</div>
          <div class="turn_meta">🕒 {created_at}</div>
        </summary>

        <div class="section">
          <div class="label">💬 إدخال المستخدم</div>
          <pre>{_escape(user_text)}</pre>
        </div>

        <div class="grid">
          <div class="mini">
            <div class="label">📌 تلخيص</div>
            <pre>{_escape(summary) if summary else '<span class="muted">—</span>'}</pre>
          </div>

          <div class="mini">
            <div class="label">🧠 الفكرة التلقائية</div>
            <pre>{_escape(auto_thought) if auto_thought else '<span class="muted">—</span>'}</pre>
          </div>
        </div>

        <div class="grid">
          <div class="mini">
            <div class="label">⚠️ تشوهات معرفية</div>
            {distortions_html}
            <div class="divider"></div>
            <div class="label">❤️ مشاعر</div>
            {emotions_html}
          </div>

          <div class="mini">
            <div class="label">❓ أسئلة سوكراتية</div>
            {_ul([str(x) for x in questions])}
            <div class="divider"></div>
            <div class="label">🚀 خطوة عملية</div>
            <pre>{_escape(small_step) if small_step else '<span class="muted">—</span>'}</pre>
          </div>
        </div>

        <div class="section">
          <div class="label">🟣 رد Viola</div>
          <pre>{_escape(assistant_text)}</pre>
        </div>
      </details>
    </div>
    """


def export_domain_session_to_html(
    domain_session_path: str,
    out_dir: str = "data/html",
    title: str = "Viola (CBT)",
    open_in_browser: bool = True,
) -> str:
    with open(domain_session_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    session_id = str(data.get("session_id", "unknown"))
    created_at = _format_ts(str(data.get("created_at", "")))
    updated_at = _format_ts(str(data.get("updated_at", "")))
    turns = data.get("turns") or []
    total = len(turns)

    timeline_html = "".join(
        _render_turn(t, i + 1, total) for i, t in enumerate(turns)
    ) if turns else "<p class='muted'>لا توجد Turns بعد.</p>"

    disclaimer_text = str(getattr(settings, "disclaimer", "") or "")
    disclaimer_html = _escape(disclaimer_text) if disclaimer_text else "هذا المحتوى إرشادي وليس تشخيصًا طبيًا."

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(out_dir) / f"viola_{session_id}_{ts}.html"

    html_doc = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8" />
<title>{_escape(title)} — {session_id}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
:root {{
  --bg:#0b0b10;
  --card:rgba(255,255,255,0.05);
  --border:rgba(255,255,255,0.12);
  --text:#f2f2f2;
  --muted:rgba(242,242,242,0.70);
  --accent:#a855f7;
}}
body {{
  background:var(--bg);
  color:var(--text);
  font-family:Segoe UI,Tahoma,Arial;
  margin:30px;
  line-height:1.9;
}}
.wrap {{ max-width: 980px; margin: 0 auto; }}

h2 {{
  margin:0 0 8px 0;
  font-weight:900;
}}
.meta {{
  color:var(--muted);
  font-size:13px;
  direction:ltr;
  text-align:left;
  margin-bottom:18px;
}}

.card {{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:18px;
  padding:18px;
}}
.turn {{
  padding:0;
}}
.turn > summary {{
  list-style:none;
  cursor:pointer;
  padding:18px;
  border-radius:18px;
}}
.turn[open] > summary {{
  border-bottom:1px solid var(--border);
  border-bottom-left-radius:0;
  border-bottom-right-radius:0;
}}
.turn > summary::-webkit-details-marker {{ display:none; }}

.turn_head {{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
}}
.turn_title {{ font-weight:900; }}
.turn_meta {{
  direction:ltr;
  font-size:13px;
  color:var(--muted);
}}

.section {{
  padding:18px;
}}

.grid {{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
  padding:0 18px 18px 18px;
}}
@media (max-width:800px) {{
  .grid {{ grid-template-columns:1fr; }}
}}

.mini {{
  background:rgba(255,255,255,0.04);
  padding:14px;
  border-radius:14px;
  border:1px solid rgba(255,255,255,0.10);
}}

.label {{
  font-weight:800;
  margin-bottom:6px;
}}
.badge {{
  display:inline-block;
  padding:5px 10px;
  margin:4px 6px 0 0;
  border-radius:999px;
  background:rgba(168,85,247,0.15);
  border:1px solid rgba(255,255,255,0.10);
  font-size:13px;
}}
pre {{
  white-space:pre-wrap;
  margin:0;
}}
.divider {{
  height:1px;
  background:rgba(255,255,255,0.10);
  margin:10px 0;
}}
.muted {{ color: var(--muted); }}

.pill {{
  display:inline-block;
  padding:10px 12px;
  border-radius:12px;
  background:rgba(255,255,255,0.06);
  border:1px solid var(--border);
}}

.anim {{
  animation:fadeUp .28s ease both;
}}
@keyframes fadeUp {{
  from {{opacity:0; transform:translateY(8px);}}
  to {{opacity:1; transform:translateY(0);}}
}}

 /* Timeline layout */
.timeline {{
  position: relative;
  padding-right: 22px; /* space for the vertical line (RTL) */
}}

.timeline::before {{
  content:"";
  position:absolute;
  top:0;
  bottom:0;
  right: 10px; /* line position (RTL) */
  width:2px;
  background: rgba(168,85,247,0.28);
  border-radius: 2px;
}}

.tl_item {{
  position: relative;
  display: grid;
  grid-template-columns: 22px 1fr; /* marker + card */
  gap: 14px;
  align-items: start;
  margin-bottom: 16px;
}}

.tl_marker {{
  position: relative;
  height: 100%;
  display:flex;
  justify-content:center;
}}

.dot {{
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 0 4px rgba(168,85,247,0.15);
  margin-top: 18px; /* align with card header */
}}
</style>
</head>
<body>
<div class="wrap">
  <h2>Viola CBT — Timeline</h2>
  <div class="meta">
    <div><span class="muted">Session:</span> {session_id}</div>
    <div><span class="muted">Created:</span> {created_at}</div>
    <div><span class="muted">Updated:</span> {updated_at}</div>
    <div><span class="muted">Turns:</span> {total}</div>
  </div>

  <div class="timeline">
    {timeline_html}
  </div>

  <div class="card muted" style="margin-top:18px;">
    <span class="pill">⚠️ {disclaimer_html}</span>
  </div>
</div>
</body>
</html>
"""
    out_path.write_text(html_doc, encoding="utf-8")

    if open_in_browser:
        webbrowser.open(out_path.resolve().as_uri())

    return os.fspath(out_path)
