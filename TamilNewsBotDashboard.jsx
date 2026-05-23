import { useState } from "react";

const FILES = {
  "main.py": {
    icon: "🚀",
    desc: "Flask app + live dashboard + entry point",
    color: "#ff6b35",
    code: `"""
Tamil Tanglish Breaking News Bot — main.py
Flask web server + scheduler launcher
"""

import os, logging
from flask import Flask, jsonify
from dotenv import load_dotenv
from scheduler import start_scheduler, run_news_cycle

load_dotenv()
app = Flask(__name__)

# Logging: file + console
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s",
  handlers=[
    logging.FileHandler("logs/bot.log"),
    logging.StreamHandler()
  ]
)

@app.route("/")
def home():
    return "<h1>🎬 Tamil News Bot — Live</h1>"

@app.route("/status")
def status():
    return jsonify({
      "status": "running",
      "cycle":  "every 30 minutes",
      "target": "Instagram"
    })

@app.route("/run")
def manual_run():
    result = run_news_cycle()
    return jsonify(result)

@app.route("/logs")
def view_logs():
    with open("logs/bot.log") as f:
        lines = f.readlines()[-50:]
    return "<pre>" + "".join(lines) + "</pre>"

if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=5000)`,
  },

  "news_fetcher.py": {
    icon: "📰",
    desc: "Fetch India/TN/Cinema/IPL news — dedup + ranking",
    color: "#00c9ff",
    code: `"""
news_fetcher.py
Fetches from NewsAPI + GNews.
Deduplicates against posted cache.
Scores by Tamil/cricket relevance.
"""

SEARCH_QUERIES = [
  "Tamil Nadu",
  "Chennai",
  "IPL cricket CSK",
  "Kollywood cinema",
  "Rajinikanth OR Vijay OR Ajith",
]

def get_fresh_articles(limit=3):
    posted  = _load_posted_cache()
    all_art = fetch_news_newsapi() + fetch_news_gnews()
    fresh   = _deduplicate(all_art, posted)
    fresh.sort(key=_score_article, reverse=True)
    chosen  = fresh[:limit]
    _save_posted_cache(posted | {a["title"] for a in chosen})
    return chosen

def _score_article(article):
    score = 0
    text  = f"{article['title']} {article['description']}".lower()
    HIGH  = ["tamil","chennai","csk","ipl","rajinikanth","vijay"]
    for kw in HIGH:
        if kw in text: score += 2
    if article.get("urlToImage"): score += 1
    return score`,
  },

  "ai_writer.py": {
    icon: "🤖",
    desc: "OpenAI GPT → viral Tamil Tanglish meme captions",
    color: "#a855f7",
    code: `"""
ai_writer.py
Uses GPT-4o-mini to convert English news
into viral Tamil Tanglish Instagram content.
"""

SYSTEM_PROMPT = """
You are a viral Tamil meme page admin.
Write in TANGLISH only.
Style:
- SHORT punchy lines (max 6 words)
- Dramatic, emotional, shocking
- Heavy emoji usage 😱💔🔥😭
- Gen-Z Chennai slang
- Sun TV + Reddit + Meme energy

Return JSON only:
{
  "headline":   "...",   # max 60 chars
  "subtext":    "...",   # max 100 chars
  "caption":    "...",   # max 200 chars
  "hashtags":   [...],   # 15-20 tags
  "emoji_mood": "🔥"
}
"""

def generate_content(article):
    response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": build_prompt(article)},
      ],
      temperature=0.85,
      response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

# Example output:
# headline:   "CSK fans ku ippo thookam varala 😭🏏"
# subtext:    "Last over la wicket pochu... RIP boys 💔"
# emoji_mood: "💔"`,
  },

  "image_generator.py": {
    icon: "🎨",
    desc: "Pillow cinematic poster — 1080×1350 Instagram format",
    color: "#f59e0b",
    code: `"""
image_generator.py
Generates cinematic Tamil breaking-news posters.
Layout:
  [RED BREAKING NEWS BAR]
  [NEWS PHOTO / GEMINI BG]
  [GOLD HEADLINE TEXT]
  [━━ DIVIDER ━━]
  [WHITE SUBTEXT]
  [BOTTOM INFO BAR]
  [WATERMARK]
"""

COLORS = {
  "bg_dark":    (5,   10,  35),   # deep navy
  "gold":       (255, 200, 0),    # headline
  "white":      (255, 255, 255),
  "red_alert":  (220, 30,  30),   # top bar
  "glow_blue":  (0,   120, 255),
}

def generate_poster(article, content):
    img  = Image.new("RGB", (1080, 1350))
    img  = draw_gradient_bg(img)       # navy gradient
    img  = add_grid_overlay(img)       # scan-line aesthetic
    draw = ImageDraw.Draw(img)

    # Red breaking-news bar (top)
    draw.rectangle([(0,0),(1080,90)], fill=COLORS["red_alert"])
    draw.text((40,22), "🔴  BREAKING NEWS  |  LIVE", ...)

    # News photo or Gemini background
    news_img = fetch_news_image(article["urlToImage"])
    img.paste(news_img, (0, 110))

    # Gold headline (large, bold)
    draw.text((50, 590), content["headline"],
              font=get_font(64, bold=True),
              fill=COLORS["gold"])

    # Gold divider line
    draw.rectangle([(50,680),(1030,684)], fill=COLORS["gold"])

    # White subtext
    draw.text((50, 700), content["subtext"],
              font=get_font(42), fill=COLORS["white"])

    # Bottom bar with timestamp + branding
    draw.rectangle([(0,1190),(1080,1350)], fill=COLORS["bg_dark"])
    draw.text((50,1210), f"🕐 {now}",  ...)
    draw.text((750,1204), "🎬 TAMIL BREAKING NEWS", ...)

    img.save(output_path, "PNG", quality=95)
    return output_path`,
  },

  "instagram_uploader.py": {
    icon: "📲",
    desc: "Instagram Graph API — host → container → publish",
    color: "#e1306c",
    code: `"""
instagram_uploader.py
3-step Instagram Graph API upload pipeline.
"""

GRAPH = "https://graph.facebook.com/v21.0"

def upload_to_instagram(image_path, caption):
    # Step 1: Host image publicly (IG needs a URL)
    image_url = upload_image_to_imgbb(image_path)

    # Step 2: Create media container
    container_id = create_media_container(
      ig_user_id   = os.getenv("IG_USER_ID"),
      access_token = os.getenv("IG_ACCESS_TOKEN"),
      image_url    = image_url,
      caption      = caption,
    )

    # Step 2.5: Wait for container to process
    wait_for_container_ready(container_id)

    # Step 3: Publish!
    media_id = publish_container(container_id)

    return {"status": "success", "media_id": media_id}

# IG API Requirements:
# ✅ Professional/Business account
# ✅ Facebook Page connected
# ✅ Long-lived access token (60 days)
# ✅ Permissions: instagram_content_publish`,
  },

  "scheduler.py": {
    icon: "⏰",
    desc: "APScheduler — full pipeline every 30 min, IST timezone",
    color: "#10b981",
    code: `"""
scheduler.py
APScheduler runs run_news_cycle() every 30 minutes.
Timezone: Asia/Kolkata (IST)
"""

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

def run_news_cycle():
    # 1. Fetch fresh news
    articles = get_fresh_articles(limit=2)

    for article in articles:
        # 2. Generate Tamil Tanglish content
        content    = generate_content(article)

        # 3. Generate poster image
        image_path = generate_poster(article, content)

        # 4. Format Instagram caption
        caption    = format_caption_for_instagram(content)

        # 5. Upload to Instagram
        result     = upload_to_instagram(image_path, caption)

        logger.info(f"✅ Posted! ID: {result['media_id']}")

def start_scheduler(interval_minutes=30):
    scheduler.add_job(
      func=run_news_cycle,
      trigger="interval",
      minutes=interval_minutes,
      max_instances=1,          # no overlapping cycles
    )
    scheduler.start()
    run_news_cycle()            # run immediately on startup`,
  },

  ".env.example": {
    icon: "🔑",
    desc: "Environment variables — copy to .env and fill in",
    color: "#6b7280",
    code: `# Tamil Tanglish News Bot — API Keys
# Copy this to .env and fill in your actual values

# OpenAI (Tamil content generation)
# https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-key-here

# Google Gemini (AI background images)
# https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-gemini-key

# NewsAPI (primary news)
# https://newsapi.org — Free: 100 req/day
NEWS_API_KEY=your-newsapi-key

# GNews (backup news source)
# https://gnews.io — Free: 100 req/day
GNEWS_API_KEY=your-gnews-key

# Instagram Graph API
# https://developers.facebook.com
IG_ACCESS_TOKEN=your-long-lived-ig-token
IG_USER_ID=your-ig-business-user-id

# ImgBB image hosting (IG needs public URLs)
# https://api.imgbb.com — Free: 1000/month
IMGBB_API_KEY=your-imgbb-key`,
  },

  "requirements.txt": {
    icon: "📦",
    desc: "Python dependencies — pip install -r requirements.txt",
    color: "#3b82f6",
    code: `# Tamil Tanglish News Bot — Dependencies

flask>=3.0.0           # Web dashboard
openai>=1.40.0         # GPT-4o-mini content
google-generativeai>=0.8.0  # Gemini images
requests>=2.31.0       # HTTP + news fetch
Pillow>=10.3.0         # Poster generation
APScheduler>=3.10.4    # 30-min automation
python-dotenv>=1.0.0   # .env loading`,
  },
};

const PIPELINE_STEPS = [
  { step: "01", label: "NEWS FETCH", sub: "NewsAPI + GNews\nEvery 30 min", icon: "📰", color: "#00c9ff" },
  { step: "02", label: "AI WRITE", sub: "OpenAI GPT-4o-mini\nTamil Tanglish", icon: "🤖", color: "#a855f7" },
  { step: "03", label: "POSTER GEN", sub: "Pillow + Gemini\n1080×1350 px", icon: "🎨", color: "#f59e0b" },
  { step: "04", label: "IG UPLOAD", sub: "Graph API\nAuto publish", icon: "📲", color: "#e1306c" },
];

const SETUP_STEPS = [
  { num: "1", title: "Install dependencies", cmd: "pip install -r requirements.txt" },
  { num: "2", title: "Download fonts", cmd: "python setup_fonts.py" },
  { num: "3", title: "Configure .env", cmd: "cp .env.example .env  # then fill in keys" },
  { num: "4", title: "Run the bot", cmd: "python main.py" },
  { num: "5", title: "View dashboard", cmd: "open http://localhost:5000" },
];

export default function TamilNewsBot() {
  const [activeFile, setActiveFile] = useState("main.py");
  const [activeTab, setActiveTab] = useState("files");

  const file = FILES[activeFile];

  return (
    <div style={{
      minHeight: "100vh",
      background: "#050a1c",
      fontFamily: "'Courier New', monospace",
      color: "#e2e8f0",
    }}>
      {/* ── Header ── */}
      <div style={{
        background: "linear-gradient(135deg, #0d0d2b 0%, #1a0a2e 50%, #0d1a3a 100%)",
        borderBottom: "2px solid #ffd700",
        padding: "24px 32px",
        display: "flex",
        alignItems: "center",
        gap: 20,
      }}>
        <div style={{
          background: "#dc1e1e",
          borderRadius: 8,
          padding: "6px 14px",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 2,
          animation: "pulse 1.5s infinite",
        }}>
          🔴 LIVE
        </div>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#ffd700", letterSpacing: 1 }}>
            🎬 TAMIL TANGLISH BREAKING NEWS BOT
          </div>
          <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>
            AI-Powered Instagram Automation • Posts every 30 minutes • 24/7 🤖
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ color: "#10b981", fontSize: 13, fontWeight: 600 }}>● RUNNING</div>
          <div style={{ color: "#64748b", fontSize: 11 }}>Asia/Kolkata IST</div>
        </div>
      </div>

      {/* ── Pipeline visual ── */}
      <div style={{
        background: "linear-gradient(90deg, #0a1628 0%, #0d1f3c 100%)",
        borderBottom: "1px solid #1e3a5f",
        padding: "20px 32px",
        display: "flex",
        alignItems: "center",
        gap: 0,
        overflowX: "auto",
      }}>
        {PIPELINE_STEPS.map((s, i) => (
          <div key={s.step} style={{ display: "flex", alignItems: "center" }}>
            <div style={{
              textAlign: "center",
              padding: "12px 20px",
              borderRadius: 10,
              border: `1px solid ${s.color}40`,
              background: `${s.color}10`,
              minWidth: 120,
            }}>
              <div style={{ fontSize: 28 }}>{s.icon}</div>
              <div style={{ color: s.color, fontSize: 11, fontWeight: 700, letterSpacing: 1, marginTop: 4 }}>
                STEP {s.step}
              </div>
              <div style={{ color: "#f1f5f9", fontSize: 13, fontWeight: 600, marginTop: 2 }}>
                {s.label}
              </div>
              <div style={{ color: "#64748b", fontSize: 10, marginTop: 3, whiteSpace: "pre-line" }}>
                {s.sub}
              </div>
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <div style={{ color: "#ffd700", fontSize: 20, padding: "0 8px", flexShrink: 0 }}>→</div>
            )}
          </div>
        ))}
        <div style={{ marginLeft: 8, color: "#64748b", fontSize: 18 }}>↩️</div>
        <div style={{ color: "#64748b", fontSize: 11, marginLeft: 4 }}>repeat</div>
      </div>

      {/* ── Tab nav ── */}
      <div style={{
        display: "flex",
        gap: 0,
        borderBottom: "1px solid #1e3a5f",
        padding: "0 32px",
        background: "#060c1f",
      }}>
        {["files", "setup", "style"].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: "none",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid #ffd700" : "2px solid transparent",
              color: activeTab === tab ? "#ffd700" : "#64748b",
              padding: "14px 20px",
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: 1,
              cursor: "pointer",
              textTransform: "uppercase",
            }}
          >
            {tab === "files" ? "📁 Project Files" : tab === "setup" ? "⚙️ Setup Guide" : "🎨 Post Style"}
          </button>
        ))}
      </div>

      {/* ── Files Tab ── */}
      {activeTab === "files" && (
        <div style={{ display: "flex", height: "calc(100vh - 280px)", minHeight: 500 }}>
          {/* File sidebar */}
          <div style={{
            width: 220,
            background: "#060c1f",
            borderRight: "1px solid #1e3a5f",
            overflowY: "auto",
            flexShrink: 0,
          }}>
            {Object.entries(FILES).map(([name, meta]) => (
              <div
                key={name}
                onClick={() => setActiveFile(name)}
                style={{
                  padding: "12px 16px",
                  cursor: "pointer",
                  borderLeft: activeFile === name ? `3px solid ${meta.color}` : "3px solid transparent",
                  background: activeFile === name ? `${meta.color}15` : "transparent",
                  borderBottom: "1px solid #0d1f3c",
                  transition: "all 0.15s",
                }}
              >
                <div style={{ fontSize: 16 }}>{meta.icon}</div>
                <div style={{
                  color: activeFile === name ? meta.color : "#94a3b8",
                  fontSize: 12,
                  fontWeight: 600,
                  marginTop: 3,
                }}>
                  {name}
                </div>
                <div style={{ color: "#475569", fontSize: 10, marginTop: 2, lineHeight: 1.3 }}>
                  {meta.desc}
                </div>
              </div>
            ))}
          </div>

          {/* Code panel */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* File header */}
            <div style={{
              background: "#0a1628",
              borderBottom: "1px solid #1e3a5f",
              padding: "10px 24px",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}>
              <span style={{ fontSize: 18 }}>{file.icon}</span>
              <span style={{ color: file.color, fontWeight: 700, fontSize: 14 }}>{activeFile}</span>
              <span style={{ color: "#475569", fontSize: 12 }}>—</span>
              <span style={{ color: "#64748b", fontSize: 12 }}>{file.desc}</span>
            </div>

            {/* Code */}
            <div style={{
              flex: 1,
              overflowY: "auto",
              padding: "20px 28px",
              background: "#040810",
            }}>
              <pre style={{
                margin: 0,
                fontSize: 12.5,
                lineHeight: 1.7,
                color: "#c9d8f0",
                whiteSpace: "pre-wrap",
                fontFamily: "'Courier New', monospace",
              }}>
                {file.code.split("\n").map((line, i) => {
                  const isComment   = line.trim().startsWith("#") || line.trim().startsWith('"""');
                  const isKeyword   = /^\s*(def |class |import |from |return |if |for |else|try|except)/.test(line);
                  const isString    = line.includes('"') || line.includes("'");
                  return (
                    <div key={i} style={{
                      color: isComment ? "#4a6741"
                           : isKeyword ? "#c792ea"
                           : "#c9d8f0",
                      display: "flex",
                      gap: 16,
                    }}>
                      <span style={{ color: "#2d4a6b", userSelect: "none", minWidth: 24, textAlign: "right" }}>
                        {i + 1}
                      </span>
                      <span>{line}</span>
                    </div>
                  );
                })}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* ── Setup Tab ── */}
      {activeTab === "setup" && (
        <div style={{ padding: "32px", maxWidth: 800 }}>
          <div style={{ marginBottom: 32 }}>
            <div style={{ color: "#ffd700", fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
              🚀 Quick Start — 5 Steps to Go Live
            </div>
            {SETUP_STEPS.map(s => (
              <div key={s.num} style={{
                display: "flex",
                gap: 16,
                marginBottom: 12,
                alignItems: "flex-start",
              }}>
                <div style={{
                  background: "#ffd70020",
                  border: "1px solid #ffd70060",
                  borderRadius: "50%",
                  width: 32,
                  height: 32,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#ffd700",
                  fontWeight: 700,
                  fontSize: 14,
                  flexShrink: 0,
                }}>
                  {s.num}
                </div>
                <div>
                  <div style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600 }}>{s.title}</div>
                  <div style={{
                    background: "#040810",
                    border: "1px solid #1e3a5f",
                    borderRadius: 6,
                    padding: "6px 14px",
                    marginTop: 6,
                    color: "#10b981",
                    fontSize: 13,
                    fontFamily: "monospace",
                  }}>
                    $ {s.cmd}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginBottom: 28 }}>
            <div style={{ color: "#ffd700", fontSize: 16, fontWeight: 700, marginBottom: 14 }}>
              🔑 API Keys Needed
            </div>
            {[
              { name: "OpenAI", use: "Tamil Tanglish content", cost: "~$15/month", url: "platform.openai.com", color: "#10b981" },
              { name: "NewsAPI", use: "News headlines", cost: "Free (100 req/day)", url: "newsapi.org", color: "#00c9ff" },
              { name: "GNews", use: "Backup news source", cost: "Free (100 req/day)", url: "gnews.io", color: "#00c9ff" },
              { name: "Gemini", use: "AI background images", cost: "Free tier", url: "aistudio.google.com", color: "#a855f7" },
              { name: "ImgBB", use: "Image hosting (IG needs URLs)", cost: "Free / $5/mo", url: "api.imgbb.com", color: "#f59e0b" },
              { name: "Instagram", use: "Auto-post via Graph API", cost: "Free", url: "developers.facebook.com", color: "#e1306c" },
            ].map(api => (
              <div key={api.name} style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "10px 16px",
                background: "#0a1628",
                border: `1px solid ${api.color}30`,
                borderRadius: 8,
                marginBottom: 8,
              }}>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <div style={{ color: api.color, fontWeight: 700, width: 100, fontSize: 13 }}>{api.name}</div>
                  <div style={{ color: "#94a3b8", fontSize: 12 }}>{api.use}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "#10b981", fontSize: 11 }}>{api.cost}</div>
                  <div style={{ color: "#475569", fontSize: 10 }}>{api.url}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{
            background: "#0a1f0a",
            border: "1px solid #10b98140",
            borderRadius: 10,
            padding: 20,
          }}>
            <div style={{ color: "#10b981", fontSize: 14, fontWeight: 700, marginBottom: 8 }}>
              🌐 Replit Deployment
            </div>
            <div style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.8 }}>
              1. Create Replit project (Python template)<br />
              2. Upload all project files<br />
              3. Add secrets in Replit Secrets tab (same as .env keys)<br />
              4. Shell: <span style={{ color: "#10b981" }}>pip install -r requirements.txt && python setup_fonts.py</span><br />
              5. Run → Always On keeps it live 24/7<br />
              6. Free alternative: <span style={{ color: "#ffd700" }}>UptimeRobot.com</span> pings every 5 min to prevent sleep
            </div>
          </div>
        </div>
      )}

      {/* ── Style Tab ── */}
      {activeTab === "style" && (
        <div style={{ padding: "32px", maxWidth: 800 }}>
          <div style={{ color: "#ffd700", fontSize: 18, fontWeight: 700, marginBottom: 20 }}>
            🎨 Post Style & Meme Vibe
          </div>

          {/* Sample post preview */}
          <div style={{
            background: "linear-gradient(160deg, #050a23 0%, #0d1a3a 60%, #0a1020 100%)",
            border: "2px solid #ffd700",
            borderRadius: 16,
            overflow: "hidden",
            maxWidth: 380,
            marginBottom: 32,
            boxShadow: "0 0 40px #ffd70020",
          }}>
            {/* Red bar */}
            <div style={{
              background: "#dc1e1e",
              padding: "10px 16px",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: 2,
              color: "white",
            }}>
              🔴 BREAKING NEWS  |  LIVE UPDATE
            </div>
            {/* Photo area */}
            <div style={{
              height: 160,
              background: "linear-gradient(135deg, #0d3060 0%, #1a0a3e 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 48,
              position: "relative",
            }}>
              🏏
              <div style={{
                position: "absolute",
                right: 12, top: 12,
                fontSize: 32,
              }}>💔</div>
              <div style={{
                position: "absolute",
                bottom: 8, left: 12,
                color: "#ffd70080",
                fontSize: 10,
                background: "#00000060",
                padding: "2px 8px",
                borderRadius: 4,
              }}>📰 Cricbuzz</div>
            </div>
            {/* Headline */}
            <div style={{ padding: "14px 16px 4px" }}>
              <div style={{
                color: "#ffd700",
                fontSize: 17,
                fontWeight: 700,
                lineHeight: 1.3,
                letterSpacing: 0.5,
              }}>
                CSK fans ku ippo thookam varala 😭🏏
              </div>
            </div>
            {/* Divider */}
            <div style={{
              height: 2,
              background: "#ffd700",
              margin: "10px 16px",
            }}/>
            {/* Subtext */}
            <div style={{ padding: "0 16px 12px", color: "#e2e8f0", fontSize: 13 }}>
              Last over la wicket pochu... RIP boys 💔
            </div>
            {/* Bottom bar */}
            <div style={{
              background: "#050a1c",
              borderTop: "2px solid #ffd700",
              padding: "8px 16px",
              display: "flex",
              justifyContent: "space-between",
              fontSize: 10,
            }}>
              <span style={{ color: "#64748b" }}>🕐 23 May 2026 • 08:30 PM</span>
              <span style={{ color: "#ffd700", fontWeight: 700 }}>🎬 TAMIL BREAKING NEWS</span>
            </div>
            {/* Hashtags */}
            <div style={{ padding: "6px 16px 12px", color: "#3b82f6", fontSize: 10 }}>
              #CSK #IPL2025 #Chennai #TamilCricket #Tanglish
            </div>
          </div>

          {/* Style breakdown */}
          <div style={{ color: "#ffd700", fontSize: 15, fontWeight: 700, marginBottom: 14 }}>
            ✍️ AI Writing Style Guide
          </div>
          {[
            { label: "Language", val: "Tamil Tanglish — Tamil words in English letters" },
            { label: "Tone", val: "Dramatic, emotional, shocking, cinematic" },
            { label: "Emojis", val: "Heavy — 😱💔🔥😭🤯🏏🎬 — multiple per line" },
            { label: "Line length", val: "Max 6 words per line — punchy and scannable" },
            { label: "Audience", val: "Gen-Z Chennai youth, cricket + cinema fans" },
            { label: "Vibe", val: "Sun TV drama + Reddit meme + Koothu energy" },
            { label: "Hashtags", val: "15-20 per post: Tamil + English + trending mix" },
          ].map(s => (
            <div key={s.label} style={{
              display: "flex",
              gap: 12,
              padding: "8px 0",
              borderBottom: "1px solid #1e3a5f",
              fontSize: 13,
            }}>
              <div style={{ color: "#64748b", minWidth: 110 }}>{s.label}</div>
              <div style={{ color: "#c9d8f0" }}>{s.val}</div>
            </div>
          ))}

          <div style={{ marginTop: 24, color: "#ffd700", fontSize: 15, fontWeight: 700, marginBottom: 14 }}>
            🖼️ Poster Design Specs
          </div>
          {[
            { label: "Size", val: "1080 × 1350 px (Instagram portrait 4:5)" },
            { label: "Background", val: "Deep navy gradient + grid scan-line overlay" },
            { label: "Top bar", val: "Red BREAKING NEWS alert banner" },
            { label: "Photo zone", val: "News image or Gemini AI generated background" },
            { label: "Headline", val: "Gold (#FFD700) bold font — 64px" },
            { label: "Divider", val: "Gold horizontal rule for visual hierarchy" },
            { label: "Bottom bar", val: "Timestamp + page branding + hashtag preview" },
            { label: "Watermark", val: "@TamilBreakingNews top-right corner" },
          ].map(s => (
            <div key={s.label} style={{
              display: "flex",
              gap: 12,
              padding: "8px 0",
              borderBottom: "1px solid #1e3a5f",
              fontSize: 13,
            }}>
              <div style={{ color: "#64748b", minWidth: 110 }}>{s.label}</div>
              <div style={{ color: "#c9d8f0" }}>{s.val}</div>
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #060c1f; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
      `}</style>
    </div>
  );
}
