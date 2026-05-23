"""
==============================================================
 ai_writer.py — AI-powered Tamil Tanglish content generator
 Uses OpenAI GPT to rewrite news as viral meme-style captions
==============================================================
"""

import os
import json
import logging
import time
from openai import OpenAI

logger = logging.getLogger(__name__)

# ── OpenAI client ─────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Master system prompt ──────────────────────────────────────
SYSTEM_PROMPT = """
You are a viral Tamil meme page admin — the most famous breaking-news Instagram page in Chennai.
You write in TANGLISH only (Tamil words written in English letters mixed with English).
Your style:
- SHORT punchy lines (max 6 words per line)
- Dramatic, emotional, shocking tone
- Heavy emoji usage 😱💔🔥😭🤯
- Gen-Z Chennai slang
- Think: Sun TV + Reddit + Meme page energy

Example style:
HEADLINE: "CSK fans ku ippo thookam varala 😭🏏"
SUBTEXT: "Last over la wicket pochu... RIP boys 💔"
CAPTION: "Ippa en feel panrom theriyuma? 😤 Yellarum semma paithiyam!"
HASHTAGS: #CSK #IPL2025 #ChennaiMakkals #CricketMeme #Tanglish

Rules:
1. ALWAYS respond in valid JSON only — no markdown, no preamble
2. Keys: headline, subtext, caption, hashtags (array of strings), emoji_mood
3. headline max 60 chars
4. subtext max 100 chars
5. caption max 200 chars (for Instagram post)
6. hashtags: 15-20 relevant tags
7. emoji_mood: one dominant emoji that captures the vibe
"""


def _call_openai_with_retry(prompt: str, retries: int = 3) -> str:
    """
    Call OpenAI ChatCompletion with exponential backoff on rate limit.
    Returns raw text response.
    """
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",           # cost-effective, fast
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.85,              # creative but not chaotic
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        except Exception as e:
            err = str(e)
            if "rate_limit" in err.lower() or "429" in err:
                wait = 2 ** attempt * 5        # 5s, 10s, 20s
                logger.warning(f"OpenAI rate limit — waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                logger.error(f"OpenAI API error: {e}")
                raise
    raise RuntimeError("OpenAI: max retries exceeded")


def _build_prompt(article: dict) -> str:
    """Build the user-facing prompt from article data."""
    return f"""
Convert this English news into viral Tamil Tanglish Instagram breaking-news content.

NEWS TITLE: {article.get('title', '')}
NEWS DESCRIPTION: {article.get('description', '')[:300]}
SOURCE: {article.get('source', 'Unknown')}
CATEGORY: {article.get('query', 'General')}

Generate a JSON with:
- headline: Short punchy Tamil Tanglish (shock factor, emotional)
- subtext: One extra line of context in Tanglish
- caption: Full Instagram caption with emojis and Tanglish storytelling
- hashtags: Array of 15-20 relevant hashtags (mix Tamil + English + trending)
- emoji_mood: Single emoji representing the emotion of this news

Remember: Chennai meme page vibe. Make it VIRAL. Make it EMOTIONAL. Keep it TANGLISH.
"""


def generate_content(article: dict) -> dict:
    """
    Generate viral Tamil Tanglish content for one news article.
    Returns dict with: headline, subtext, caption, hashtags, emoji_mood
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set — returning placeholder content")
        return _fallback_content(article)

    try:
        prompt = _build_prompt(article)
        raw    = _call_openai_with_retry(prompt)
        data   = json.loads(raw)

        # Validate required keys
        required = ["headline", "subtext", "caption", "hashtags", "emoji_mood"]
        for key in required:
            if key not in data:
                data[key] = _fallback_content(article)[key]

        # Ensure hashtags is a list
        if isinstance(data["hashtags"], str):
            data["hashtags"] = data["hashtags"].split()

        logger.info(f"✅ Content generated: {data['headline'][:50]}...")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error from OpenAI: {e}")
        return _fallback_content(article)
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        return _fallback_content(article)


def _fallback_content(article: dict) -> dict:
    """
    Fallback content when OpenAI is unavailable.
    Uses basic template with the raw title.
    """
    title = article.get("title", "Big news vanduchu!")
    return {
        "headline":   f"BREAKING: {title[:55]}",
        "subtext":    "Ippo news full vera level 🔥",
        "caption":    (
            f"🚨 BREAKING NEWS 🚨\n\n"
            f"{title}\n\n"
            "Chennai makkaley — comment pannunga unga thoughts! 👇\n"
            "Share pannunga yellarukkum theriyanum! 🔄"
        ),
        "hashtags": [
            "#TamilNews", "#BreakingNews", "#Chennai", "#TamilNadu",
            "#Tanglish", "#TamilMemes", "#IndiaNews", "#Viral",
            "#TamilInstagram", "#ChennaiMakkals", "#TrendingNow",
            "#NewsUpdate", "#TamilMedia", "#InstaNews", "#TamilPeople",
        ],
        "emoji_mood": "🔥",
    }


def format_caption_for_instagram(content: dict) -> str:
    """
    Combine all content fields into a final Instagram caption string.
    """
    hashtag_str = " ".join(content.get("hashtags", []))
    caption = (
        f"{content['emoji_mood']} BREAKING NEWS {content['emoji_mood']}\n\n"
        f"📢 {content['headline']}\n\n"
        f"{content['subtext']}\n\n"
        f"{content['caption']}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👇 Comment pannunga | 🔄 Share pannunga\n"
        f"❤️ Follow @tamilbreaking_news for more!\n\n"
        f"{hashtag_str}"
    )
    return caption


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    sample_article = {
        "title":       "CSK defeats MI in last-over thriller at Chepauk",
        "description": "Chennai Super Kings won a nail-biting match against Mumbai Indians.",
        "source":      "Cricbuzz",
        "query":       "IPL cricket",
    }
    result = generate_content(sample_article)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n--- INSTAGRAM CAPTION ---")
    print(format_caption_for_instagram(result))
