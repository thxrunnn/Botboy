# 🎬 Tamil Tanglish Breaking News Bot
### Fully Automated AI-Powered Instagram News System

---

## 🚀 What This Does

Every **30 minutes**, this bot automatically:
1. 📰 **Fetches** latest India/Tamil Nadu/IPL/Cinema news
2. 🤖 **Rewrites** it in viral Tamil Tanglish meme style (GPT-4o-mini)
3. 🎨 **Generates** a cinematic breaking-news poster (Pillow + Gemini)
4. 📲 **Uploads** the poster to your Instagram automatically
5. 🔄 **Repeats** forever, 24/7, with zero manual work

---

## 📁 Project Structure

```
tamil_news_bot/
│
├── main.py                 # Flask app + dashboard + entry point
├── news_fetcher.py         # Fetch news from NewsAPI + GNews
├── ai_writer.py            # OpenAI Tamil Tanglish content generator
├── image_generator.py      # Pillow poster generator + Gemini backgrounds
├── instagram_uploader.py   # Instagram Graph API uploader
├── scheduler.py            # APScheduler 30-minute automation
├── setup_fonts.py          # Download fonts (run once)
│
├── fonts/                  # Font files (auto-downloaded)
├── generated/              # Generated poster images saved here
├── logs/                   # bot.log + posted_headlines.json
│
├── .env.example            # Template — copy to .env and fill in keys
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## ⚙️ Setup Guide

### Step 1 — Clone & Install

```bash
pip install -r requirements.txt
python setup_fonts.py      # Download fonts once
```

### Step 2 — Configure API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
# Now edit .env with your actual keys
```

#### API Keys You Need:

| Service | What It Does | Get It Free At |
|---------|-------------|----------------|
| **OpenAI** | Tamil Tanglish AI writing | platform.openai.com |
| **Gemini** | AI background images | aistudio.google.com |
| **NewsAPI** | Fetch news headlines | newsapi.org |
| **GNews** | Backup news source | gnews.io |
| **ImgBB** | Host images (IG needs public URLs) | api.imgbb.com |
| **Instagram Graph API** | Auto-post to Instagram | developers.facebook.com |

---

### Step 3 — Instagram Setup (Important!)

Instagram Graph API requires a Professional account:

1. **Convert** your Instagram to a Professional/Business account
2. **Create** a Facebook Page and connect it to your IG
3. **Go to** [Facebook Developer Console](https://developers.facebook.com)
4. **Create an App** → Add Instagram product
5. **Get Access Token** with permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
6. **Get Long-Lived Token** (valid 60 days — refresh it monthly)
7. **Find your IG User ID** in Graph API Explorer: `GET /me?fields=instagram_business_account`

---

### Step 4 — Run the Bot

```bash
python main.py
```

Open your browser at `http://localhost:5000` to see the dashboard.

---

## 🌐 Deploy on Replit

1. **Create** a new Replit project → Python template
2. **Upload** all files from this project
3. **Add Secrets** (Replit's `.env` equivalent):
   - Go to **Secrets** tab in Replit
   - Add each key from `.env.example`
4. **Install dependencies:**
   In Replit Shell: `pip install -r requirements.txt && python setup_fonts.py`
5. **Set `main.py`** as the entry point
6. **Run** — Replit keeps it alive 24/7 with Always On (paid) or use UptimeRobot (free)

### Keep Alive with UptimeRobot (Free):
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Add monitor → HTTP → your Replit URL → Every 5 min
3. This pings your Flask app and prevents Replit from sleeping

---

## 🧪 Test Individual Components

```bash
# Test news fetching only
python news_fetcher.py

# Test AI content generation only
python ai_writer.py

# Test poster generation only  
python image_generator.py

# Test full pipeline (one cycle)
python scheduler.py

# Check Instagram upload config
python instagram_uploader.py
```

---

## 📊 API Limits & Cost Estimates

| Service | Free Tier | Bot Usage | Status |
|---------|-----------|-----------|--------|
| NewsAPI | 100 req/day | ~48 req/day | ✅ Free |
| GNews | 100 req/day | ~48 req/day | ✅ Free |
| OpenAI GPT-4o-mini | Pay per use | ~$0.50/day | 💰 ~$15/month |
| Gemini API | Free tier generous | Low usage | ✅ Free |
| ImgBB | 1000 uploads/month | 48/day = ~1440/month | ⚠️ Upgrade $5/month |
| Instagram Graph API | 200 posts/day | 48 posts/day | ✅ Free |

**Estimated monthly cost: ~$15-20 USD** (mostly OpenAI)

---

## ⚠️ Common Issues

**"No articles fetched"**
→ Check NEWS_API_KEY and GNEWS_API_KEY in .env

**"Container creation failed" (Instagram)**
→ Your IG access token may have expired. Refresh it (valid 60 days)
→ Make sure your IG account is Professional/Business, not Personal

**"ImgBB upload failed"**
→ Check IMGBB_API_KEY. Free plan: 1000 uploads/month

**Posters look plain (no Gemini background)**
→ This is normal! Gemini image generation is optional. The Pillow gradient design still looks great.

**Rate limit errors (OpenAI)**
→ Bot automatically retries with backoff. If persistent, upgrade OpenAI tier.

---

## 🎨 Customize the Bot

**Change posting frequency:**
```python
# In scheduler.py, line: start_scheduler(interval_minutes=30)
start_scheduler(interval_minutes=60)   # Post every hour instead
```

**Change news topics:**
```python
# In news_fetcher.py, edit SEARCH_QUERIES list
SEARCH_QUERIES = ["Your topic", "Another topic", ...]
```

**Change poster colors:**
```python
# In image_generator.py, edit COLORS dict
COLORS["gold"] = (255, 100, 0)  # Orange instead of gold
```

**Change AI writing style:**
```python
# In ai_writer.py, edit SYSTEM_PROMPT
# Add more slang, change tone, etc.
```

---

## 📜 License

MIT License — Free to use, modify, and distribute.

---

*Built with ❤️ for Tamil meme culture*  
*Chennai makkaley — namma news semma 🔥*
