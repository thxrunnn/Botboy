"""
==============================================================
 TAMIL TANGLISH BREAKING NEWS BOT — main.py
 Instagram Automation | AI-Powered | 24/7 Runner
==============================================================
"""

import os
import logging
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv
from scheduler import start_scheduler, run_news_cycle

# ── Load environment variables ──────────────────────────────
load_dotenv()

# ── Flask app setup ─────────────────────────────────────────
app = Flask(__name__)

# ── Logging configuration ────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ── Dashboard HTML (simple status page) ─────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tamil News Bot — Live Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: monospace; background: #0d0d0d; color: #f0e040; padding: 30px; }
    h1   { font-size: 2rem; border-bottom: 2px solid #f0e040; padding-bottom: 8px; }
    .card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px;
            padding: 16px; margin: 12px 0; }
    .status-ok  { color: #40ff80; }
    .status-err { color: #ff4040; }
    a { color: #f0e040; }
  </style>
</head>
<body>
  <h1>🎬 Tamil Tanglish News Bot 🤖</h1>
  <div class="card">
    <b>Status:</b> <span class="status-ok">● Running</span><br>
    <b>Cycle:</b> Every 30 minutes<br>
    <b>Target:</b> Instagram (@your_page)<br>
  </div>
  <div class="card">
    <b>Endpoints:</b><br>
    <a href="/status">/status</a> — JSON health check<br>
    <a href="/run">/run</a> — Trigger one news cycle manually<br>
    <a href="/logs">/logs</a> — View recent logs<br>
  </div>
  <div class="card">
    <b>Bot is live. Sit back. Let it post. 🚀</b>
  </div>
</body>
</html>
"""


# ── Routes ───────────────────────────────────────────────────
@app.route("/")
def home():
    return DASHBOARD_HTML


@app.route("/status")
def status():
    return jsonify({
        "status": "running",
        "bot": "Tamil Tanglish Breaking News Bot",
        "cycle_minutes": 30,
        "message": "Automation is live 💪"
    })


@app.route("/run")
def manual_run():
    """Manually trigger one news cycle (for testing)."""
    logger.info("Manual run triggered via /run endpoint")
    try:
        result = run_news_cycle()
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Manual run failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs")
def view_logs():
    """Return last 50 lines of the bot log."""
    try:
        with open("logs/bot.log", "r") as f:
            lines = f.readlines()
        last_50 = "".join(lines[-50:])
        return f"<pre style='background:#111;color:#0f0;padding:20px'>{last_50}</pre>"
    except FileNotFoundError:
        return "<pre>No logs yet.</pre>"


# ── Entry Point ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🚀 Tamil News Bot starting...")
    start_scheduler()                          # kick off APScheduler
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
