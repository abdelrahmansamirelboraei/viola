from __future__ import annotations

import html
import os
import webbrowser
from datetime import datetime
from pathlib import Path


def save_and_open_html_rtl(
    text: str,
    out_dir: str = "data/html",
    title: str = "Viola Output",
) -> str:
    """
    Save text into an RTL HTML file and open it in the default browser.
    Returns the saved file path.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"viola_{ts}.html"

    escaped = html.escape(text)

    html_doc = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 24px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, Arial, sans-serif;
      line-height: 1.8;
      background: #0b0b10;
      color: #f2f2f2;
    }}
    .card {{
      max-width: 900px;
      margin: 0 auto;
      padding: 20px 22px;
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 14px;
      background: rgba(255,255,255,0.04);
    }}
    pre {{
      white-space: pre-wrap;
      word-wrap: break-word;
      margin: 0;
      font-size: 16px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <pre>{escaped}</pre>
  </div>
</body>
</html>
"""
    path.write_text(html_doc, encoding="utf-8")

    webbrowser.open(path.resolve().as_uri())
    return os.fspath(path)
