"""
==============================================================
 image_generator.py — Generate cinematic Tamil news posters
 Uses Pillow for layout + Gemini API for background imagery
==============================================================
"""

import os
import io
import json
import logging
import textwrap
import requests
import base64
import time
from datetime import datetime
from pathlib import Path
from PIL import (
    Image, ImageDraw, ImageFont, ImageFilter,
    ImageEnhance, ImageOps
)

logger = logging.getLogger(__name__)

# ── Canvas dimensions (Instagram Portrait 4:5) ───────────────
WIDTH  = 1080
HEIGHT = 1350

# ── Color palette ─────────────────────────────────────────────
COLORS = {
    "bg_dark":       (5,   10,  35),      # deep navy
    "bg_mid":        (10,  20,  60),
    "gold":          (255, 200, 0),
    "gold_light":    (255, 230, 100),
    "white":         (255, 255, 255),
    "red_alert":     (220, 30,  30),
    "accent_blue":   (0,   120, 255),
    "glow_yellow":   (255, 240, 50),
    "text_sub":      (200, 200, 220),
    "overlay":       (0,   0,   0,   160),
}

# ── Font paths (fallback to PIL default) ─────────────────────
FONT_DIR = Path("fonts")


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font; falls back to PIL default if custom fonts missing."""
    font_file = "bold.ttf" if bold else "regular.ttf"
    font_path = FONT_DIR / font_file
    try:
        return ImageFont.truetype(str(font_path), size)
    except (IOError, OSError):
        try:
            # Try system fonts
            system_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
            for sf in system_fonts:
                if os.path.exists(sf):
                    return ImageFont.truetype(sf, size)
        except Exception:
            pass
        return ImageFont.load_default()


def _draw_gradient_bg(img: Image.Image) -> Image.Image:
    """Draw a deep navy-to-midnight gradient background."""
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(COLORS["bg_dark"][0] + (COLORS["bg_mid"][0] - COLORS["bg_dark"][0]) * ratio)
        g = int(COLORS["bg_dark"][1] + (COLORS["bg_mid"][1] - COLORS["bg_dark"][1]) * ratio)
        b = int(COLORS["bg_dark"][2] + (COLORS["bg_mid"][2] - COLORS["bg_dark"][2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return img


def _add_grid_overlay(img: Image.Image) -> Image.Image:
    """Subtle news-grid / scan-line aesthetic."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    # Horizontal scan lines every 4px
    for y in range(0, HEIGHT, 4):
        draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 8))
    # Vertical grid lines
    for x in range(0, WIDTH, 60):
        draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 5))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def _draw_glow_rect(draw: ImageDraw.Draw, xy: tuple, color: tuple, radius: int = 12):
    """Draw a rounded rectangle with a subtle glow border."""
    x1, y1, x2, y2 = xy
    # Outer glow
    for offset in range(6, 0, -1):
        alpha = int(80 * (1 - offset / 6))
        glow_color = (*color[:3], alpha)
        draw.rounded_rectangle(
            [x1 - offset, y1 - offset, x2 + offset, y2 + offset],
            radius=radius + offset,
            outline=glow_color,
            width=1,
        )
    draw.rounded_rectangle(xy, radius=radius, fill=(*color[:3], 30), outline=color, width=2)


def _fetch_news_image(url: str) -> Image.Image | None:
    """Download and prepare the news article image."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return img
    except Exception as e:
        logger.warning(f"Could not fetch news image: {e}")
        return None


def _generate_bg_with_gemini(headline: str) -> Image.Image | None:
    """
    Use Gemini Imagen to generate a dramatic news background image.
    Falls back to None if API unavailable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        prompt = (
            f"Cinematic dramatic news background for: {headline[:80]}. "
            "Dark deep blue atmosphere, glowing city skyline, dramatic lighting, "
            "photorealistic, ultra HD, no text, news broadcast aesthetic."
        )

        # Gemini 2.0 Flash image generation
        model    = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_modalities=["image"]),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img_bytes = base64.b64decode(part.inline_data.data)
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                logger.info("Gemini background generated ✅")
                return img

    except Exception as e:
        logger.warning(f"Gemini image generation skipped: {e}")
    return None


def _wrap_text_lines(text: str, font: ImageFont.FreeTypeFont,
                     max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words  = text.split()
    lines  = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_text_shadow(draw, pos, text, font, shadow_color=(0, 0, 0), offset=3):
    """Draw text with a shadow for readability."""
    x, y = pos
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)


def generate_poster(
    article: dict,
    content:  dict,
    output_path: str | None = None,
) -> str:
    """
    Generate a cinematic Tamil breaking-news Instagram poster.

    Args:
        article:     Raw news article dict (title, urlToImage, source, ...)
        content:     AI-generated content dict (headline, subtext, caption, ...)
        output_path: Where to save the image. Auto-generated if None.

    Returns:
        Path to the saved PNG file.
    """
    os.makedirs("generated", exist_ok=True)

    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"generated/poster_{ts}.png"

    # ── 1. Base canvas ────────────────────────────────────────
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg_dark"])
    img = _draw_gradient_bg(img)

    # ── 2. Try Gemini background (optional) ───────────────────
    gemini_bg = _generate_bg_with_gemini(content.get("headline", ""))
    if gemini_bg:
        gemini_bg = gemini_bg.resize((WIDTH, HEIGHT))
        gemini_bg = gemini_bg.filter(ImageFilter.GaussianBlur(radius=3))
        enhancer  = ImageEnhance.Brightness(gemini_bg)
        gemini_bg = enhancer.enhance(0.35)           # very dark overlay
        img.paste(gemini_bg, (0, 0))

    # ── 3. Grid aesthetic ─────────────────────────────────────
    img = _add_grid_overlay(img)

    draw = ImageDraw.Draw(img, "RGBA")

    # ── 4. Top breaking-news bar ──────────────────────────────
    draw.rectangle([(0, 0), (WIDTH, 90)], fill=COLORS["red_alert"])
    font_breaking = _get_font(38, bold=True)
    draw.text((40, 22), "🔴  BREAKING NEWS  |  LIVE UPDATE", font=font_breaking, fill=COLORS["white"])

    # ── 5. News article image (center section) ────────────────
    news_img = _fetch_news_image(article.get("urlToImage"))
    img_y_start = 110
    img_height  = 460

    if news_img:
        news_img = news_img.resize((WIDTH, img_height))
        # Dark overlay on the image
        overlay = Image.new("RGBA", (WIDTH, img_height), (5, 10, 35, 160))
        news_img_rgba = news_img.convert("RGBA")
        news_img_rgba.paste(overlay, (0, 0), overlay)
        img.paste(news_img_rgba.convert("RGB"), (0, img_y_start))
    else:
        # Fallback: cinematic gradient block
        for y in range(img_y_start, img_y_start + img_height):
            ratio = (y - img_y_start) / img_height
            r = int(10  + 40  * ratio)
            g = int(20  + 60  * ratio)
            b = int(60  + 100 * ratio)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Image source credit
    font_tiny = _get_font(22)
    source    = article.get("source", "News Update")
    draw.text((40, img_y_start + img_height - 35), f"📰 {source}",
              font=font_tiny, fill=(*COLORS["gold"], 200))

    # ── 6. Emoji mood badge ───────────────────────────────────
    emoji_mood = content.get("emoji_mood", "🔥")
    font_emoji = _get_font(72, bold=True)
    draw.text((WIDTH - 110, img_y_start + 20), emoji_mood, font=font_emoji, fill=COLORS["white"])

    # ── 7. Main headline ──────────────────────────────────────
    headline_y     = img_y_start + img_height + 30
    font_headline  = _get_font(64, bold=True)
    padding        = 50
    max_text_width = WIDTH - padding * 2

    headline_text  = content.get("headline", "BREAKING NEWS")
    headline_lines = _wrap_text_lines(headline_text, font_headline, max_text_width, draw)

    for i, line in enumerate(headline_lines[:3]):
        y = headline_y + i * 76
        # Shadow
        _draw_text_shadow(draw, (padding, y), line, font_headline, offset=4)
        # Main text
        draw.text((padding, y), line, font=font_headline, fill=COLORS["gold"])

    # ── 8. Gold divider line ──────────────────────────────────
    divider_y = headline_y + len(headline_lines[:3]) * 76 + 20
    draw.rectangle([(padding, divider_y), (WIDTH - padding, divider_y + 4)],
                   fill=COLORS["gold"])
    divider_y += 20

    # ── 9. Subtext ────────────────────────────────────────────
    font_subtext  = _get_font(42)
    subtext       = content.get("subtext", "")
    subtext_lines = _wrap_text_lines(subtext, font_subtext, max_text_width, draw)

    for i, line in enumerate(subtext_lines[:2]):
        y = divider_y + 10 + i * 52
        _draw_text_shadow(draw, (padding, y), line, font_subtext, offset=3)
        draw.text((padding, y), line, font=font_subtext, fill=COLORS["white"])

    # ── 10. Bottom info bar ───────────────────────────────────
    bar_y = HEIGHT - 160
    draw.rectangle([(0, bar_y), (WIDTH, HEIGHT)], fill=(*COLORS["bg_dark"], 240))
    draw.rectangle([(0, bar_y), (WIDTH, bar_y + 4)], fill=COLORS["gold"])

    # Timestamp
    now        = datetime.now().strftime("%d %b %Y  •  %I:%M %p")
    font_meta  = _get_font(28)
    draw.text((padding, bar_y + 20), f"🕐 {now}", font=font_meta, fill=COLORS["text_sub"])

    # Branding / watermark
    font_brand = _get_font(32, bold=True)
    brand_text = "🎬 TAMIL BREAKING NEWS"
    bbox       = draw.textbbox((0, 0), brand_text, font=font_brand)
    brand_x    = WIDTH - bbox[2] - padding
    draw.text((brand_x, bar_y + 14), brand_text, font=font_brand, fill=COLORS["gold"])

    # Bottom tagline
    font_tag   = _get_font(24)
    tag_text   = "Follow for live updates • Share pannunga 🔄"
    draw.text((padding, bar_y + 65), tag_text, font=font_tag, fill=COLORS["text_sub"])

    # Hashtag preview
    hashtags   = content.get("hashtags", [])
    hash_prev  = "  ".join(hashtags[:5]) if hashtags else ""
    draw.text((padding, bar_y + 100), hash_prev, font=font_tag, fill=(*COLORS["accent_blue"], 200))

    # ── 11. Corner accent circles ─────────────────────────────
    draw.ellipse([(-40, -40), (80, 80)],   fill=(*COLORS["gold"], 25))
    draw.ellipse([(WIDTH - 80, HEIGHT - 80), (WIDTH + 40, HEIGHT + 40)],
                 fill=(*COLORS["red_alert"], 25))

    # ── 12. Watermark logo overlay ────────────────────────────
    _add_watermark(draw, img)

    # ── 13. Save ──────────────────────────────────────────────
    img.save(output_path, "PNG", quality=95)
    logger.info(f"✅ Poster saved: {output_path}")
    return output_path


def _add_watermark(draw: ImageDraw.Draw, img: Image.Image):
    """Add a semi-transparent watermark in the top-right corner."""
    font_wm  = _get_font(20)
    wm_text  = "@TamilBreakingNews"
    bbox     = draw.textbbox((0, 0), wm_text, font=font_wm)
    x = WIDTH - bbox[2] - 20
    y = 100
    # Dark backing
    draw.rectangle([x - 8, y - 4, x + bbox[2] + 8, y + bbox[3] + 4],
                   fill=(0, 0, 0, 120))
    draw.text((x, y), wm_text, font=font_wm, fill=(*COLORS["gold_light"], 200))


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    sample_article = {
        "title":      "CSK defeats MI in last-over thriller",
        "source":     "Cricbuzz",
        "urlToImage": None,
    }
    sample_content = {
        "headline":   "CSK FAN-A SOLLANUM: NAMMA THAAN BEST 🏆",
        "subtext":    "Last over la 6 runs venum... yaaru? MS DHONI 💪",
        "caption":    "Semma match da! Chennai makkaley proud aaganum!",
        "hashtags":   ["#CSK", "#IPL2025", "#Dhoni", "#Chennai", "#TamilCricket"],
        "emoji_mood": "🏏",
    }
    path = generate_poster(sample_article, sample_content)
    print(f"Generated: {path}")
