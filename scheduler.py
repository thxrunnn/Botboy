"""
==============================================================
 scheduler.py — APScheduler automation: run every 30 minutes
 Full pipeline: fetch → write → generate → upload
==============================================================
"""

import logging
import traceback
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

# ── Import pipeline modules ───────────────────────────────────
from news_fetcher      import get_fresh_articles
from ai_writer         import generate_content, format_caption_for_instagram
from image_generator   import generate_poster
from instagram_uploader import upload_to_instagram

logger = logging.getLogger(__name__)

# ── Global scheduler instance ─────────────────────────────────
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")   # IST


def run_news_cycle() -> dict:
    """
    Full automation pipeline for one cycle:
    1. Fetch fresh news
    2. Generate AI Tamil Tanglish content
    3. Generate poster image
    4. Upload to Instagram

    Returns summary dict.
    """
    cycle_start = datetime.now()
    logger.info("=" * 60)
    logger.info(f"🚀 News cycle started at {cycle_start.strftime('%d %b %Y %I:%M %p IST')}")
    logger.info("=" * 60)

    results = []

    # ── Step 1: Fetch articles ────────────────────────────────
    try:
        articles = get_fresh_articles(limit=2)     # post max 2 per cycle (saves API quota)
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        return {"status": "error", "step": "fetch", "error": str(e)}

    if not articles:
        logger.info("No fresh articles found this cycle. Skipping.")
        return {"status": "skipped", "reason": "no fresh articles"}

    # ── Process each article ──────────────────────────────────
    for idx, article in enumerate(articles, start=1):
        logger.info(f"--- Processing article {idx}/{len(articles)} ---")
        logger.info(f"    Title: {article['title'][:80]}")

        result = {"title": article["title"], "status": "pending"}

        # ── Step 2: Generate AI content ───────────────────────
        try:
            content = generate_content(article)
            logger.info(f"    ✅ Content: {content['headline'][:50]}")
        except Exception as e:
            logger.error(f"    ❌ Content generation error: {e}")
            result.update({"status": "error", "step": "content", "error": str(e)})
            results.append(result)
            continue

        # ── Step 3: Generate poster image ─────────────────────
        try:
            image_path = generate_poster(article, content)
            logger.info(f"    ✅ Poster: {image_path}")
        except Exception as e:
            logger.error(f"    ❌ Image generation error: {e}")
            result.update({"status": "error", "step": "image", "error": str(e)})
            results.append(result)
            continue

        # ── Step 4: Format caption ────────────────────────────
        try:
            caption = format_caption_for_instagram(content)
        except Exception as e:
            logger.warning(f"    ⚠️ Caption formatting error (using fallback): {e}")
            caption = content.get("caption", article["title"])

        # ── Step 5: Upload to Instagram ───────────────────────
        try:
            upload_result = upload_to_instagram(image_path, caption)
            if upload_result["status"] == "success":
                logger.info(f"    ✅ Instagram post live! ID: {upload_result.get('media_id')}")
                result.update({
                    "status":   "posted",
                    "media_id": upload_result.get("media_id"),
                    "poster":   image_path,
                })
            else:
                logger.error(f"    ❌ Upload failed: {upload_result.get('error')}")
                result.update({
                    "status": "upload_failed",
                    "error":  upload_result.get("error"),
                    "poster": image_path,    # poster was generated, just not uploaded
                })
        except Exception as e:
            logger.error(f"    ❌ Upload exception: {e}")
            result.update({"status": "error", "step": "upload", "error": str(e)})

        results.append(result)

    # ── Cycle summary ─────────────────────────────────────────
    elapsed = (datetime.now() - cycle_start).seconds
    posted  = sum(1 for r in results if r["status"] == "posted")
    logger.info("=" * 60)
    logger.info(f"✅ Cycle done in {elapsed}s — {posted}/{len(results)} posted to Instagram")
    logger.info("=" * 60)

    return {
        "status":      "completed",
        "elapsed_sec": elapsed,
        "articles":    len(articles),
        "posted":      posted,
        "results":     results,
    }


def _on_job_executed(event):
    """Called when a scheduled job completes successfully."""
    logger.info(f"⏰ Scheduled job ran at {datetime.now().strftime('%H:%M')} IST")


def _on_job_error(event):
    """Called when a scheduled job raises an exception."""
    logger.error(f"💥 Scheduled job FAILED: {event.exception}")
    logger.error(traceback.format_exc())


def start_scheduler(interval_minutes: int = 30):
    """
    Start the APScheduler background scheduler.
    Runs run_news_cycle() every `interval_minutes` minutes.
    Also runs immediately on startup.
    """
    # Listen for job events
    scheduler.add_listener(_on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(_on_job_error,    EVENT_JOB_ERROR)

    # Schedule recurring job
    scheduler.add_job(
        func=run_news_cycle,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="news_cycle",
        name="Tamil News Bot Cycle",
        replace_existing=True,
        max_instances=1,             # prevent overlap if a cycle is slow
        misfire_grace_time=120,      # if delayed ≤2min, still run
    )

    scheduler.start()
    logger.info(f"⏰ Scheduler started — running every {interval_minutes} minutes (IST)")

    # Run once immediately on startup (don't wait 30 min)
    logger.info("🔄 Running initial cycle on startup...")
    try:
        run_news_cycle()
    except Exception as e:
        logger.error(f"Initial cycle failed: {e}")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


# ── Standalone test ───────────────────────────────────────────
if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    print("Running single news cycle (test mode)...")
    result = run_news_cycle()
    print("\nResult:", result)
