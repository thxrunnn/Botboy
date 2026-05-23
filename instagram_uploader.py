"""
==============================================================
 instagram_uploader.py — Upload posts via Instagram Graph API
 Requires: Professional IG account + Facebook Page
==============================================================
"""

import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

# ── Instagram Graph API base URL ──────────────────────────────
GRAPH_BASE = "https://graph.facebook.com/v21.0"

# ── Imgbb (free image host) for temporary public URLs ─────────
IMGBB_API  = "https://api.imgbb.com/1/upload"


def _upload_image_to_host(image_path: str) -> str | None:
    """
    Upload image to ImgBB to get a public URL.
    Instagram Graph API requires a publicly accessible image URL.

    Free plan: 1000 uploads/month. Sufficient for 48 posts/day.
    Set IMGBB_API_KEY in your .env file.
    """
    api_key = os.getenv("IMGBB_API_KEY")
    if not api_key:
        logger.error("IMGBB_API_KEY not set — cannot get public image URL")
        return None

    try:
        with open(image_path, "rb") as f:
            img_data = f.read()

        resp = requests.post(
            IMGBB_API,
            params={"key": api_key, "expiration": 3600},   # auto-delete after 1h
            files={"image": img_data},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        url  = data["data"]["url"]
        logger.info(f"Image hosted at: {url}")
        return url

    except Exception as e:
        logger.error(f"ImgBB upload failed: {e}")
        return None


def _create_media_container(
    ig_user_id:  str,
    access_token: str,
    image_url:   str,
    caption:     str,
) -> str | None:
    """
    Step 1: Create an IG media container (returns container ID).
    """
    url    = f"{GRAPH_BASE}/{ig_user_id}/media"
    params = {
        "image_url":    image_url,
        "caption":      caption[:2200],       # IG caption max 2200 chars
        "access_token": access_token,
    }

    try:
        resp = requests.post(url, data=params, timeout=30)
        resp.raise_for_status()
        container_id = resp.json().get("id")
        logger.info(f"Media container created: {container_id}")
        return container_id

    except requests.HTTPError as e:
        logger.error(f"Container creation failed: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Container creation error: {e}")
        return None


def _wait_for_container_ready(
    container_id: str,
    access_token:  str,
    max_wait:     int = 60,
) -> bool:
    """
    Poll the container status until it's FINISHED (ready to publish).
    Instagram needs time to process the image.
    """
    url    = f"{GRAPH_BASE}/{container_id}"
    params = {"fields": "status_code", "access_token": access_token}

    for attempt in range(max_wait // 5):
        try:
            resp   = requests.get(url, params=params, timeout=15)
            status = resp.json().get("status_code", "")
            logger.info(f"Container status: {status} (attempt {attempt + 1})")

            if status == "FINISHED":
                return True
            if status == "ERROR":
                logger.error("Container processing failed on IG side")
                return False

            time.sleep(5)
        except Exception as e:
            logger.warning(f"Status check error: {e}")
            time.sleep(5)

    logger.error("Container timed out waiting for FINISHED status")
    return False


def _publish_container(
    ig_user_id:   str,
    access_token:  str,
    container_id: str,
) -> str | None:
    """
    Step 2: Publish the media container to Instagram.
    Returns the published media ID.
    """
    url    = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    params = {
        "creation_id":  container_id,
        "access_token": access_token,
    }

    try:
        resp = requests.post(url, data=params, timeout=30)
        resp.raise_for_status()
        media_id = resp.json().get("id")
        logger.info(f"✅ Published to Instagram! Media ID: {media_id}")
        return media_id

    except requests.HTTPError as e:
        logger.error(f"Publish failed: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Publish error: {e}")
        return None


def upload_to_instagram(image_path: str, caption: str) -> dict:
    """
    Full pipeline: host image → create container → publish.

    Args:
        image_path: Local path to the generated poster PNG
        caption:    Instagram caption (Tanglish + hashtags)

    Returns:
        dict with status, media_id, error
    """
    access_token = os.getenv("IG_ACCESS_TOKEN")
    ig_user_id   = os.getenv("IG_USER_ID")

    if not access_token or not ig_user_id:
        logger.error("IG_ACCESS_TOKEN or IG_USER_ID not configured")
        return {"status": "error", "error": "Missing Instagram credentials"}

    # ── Step 0: Host image publicly ───────────────────────────
    logger.info(f"Uploading image: {image_path}")
    image_url = _upload_image_to_host(image_path)
    if not image_url:
        return {"status": "error", "error": "Image hosting failed"}

    # ── Step 1: Create media container ────────────────────────
    container_id = _create_media_container(ig_user_id, access_token, image_url, caption)
    if not container_id:
        return {"status": "error", "error": "Container creation failed"}

    # ── Step 1.5: Wait for processing ─────────────────────────
    ready = _wait_for_container_ready(container_id, access_token)
    if not ready:
        return {"status": "error", "error": "Container not ready to publish"}

    # ── Step 2: Publish ───────────────────────────────────────
    media_id = _publish_container(ig_user_id, access_token, container_id)
    if not media_id:
        return {"status": "error", "error": "Publish step failed"}

    return {
        "status":     "success",
        "media_id":   media_id,
        "image_path": image_path,
    }


def check_api_quota(access_token: str, ig_user_id: str) -> dict:
    """
    Check current IG API rate limit usage.
    Instagram allows 200 posts/day per account.
    """
    url    = f"{GRAPH_BASE}/{ig_user_id}"
    params = {
        "fields":       "username,media_count",
        "access_token": access_token,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"IG account: @{data.get('username')} — {data.get('media_count')} posts")
        return data
    except Exception as e:
        logger.error(f"Quota check failed: {e}")
        return {}


# ── Quick test (dry run) ──────────────────────────────────────
if __name__ == "__main__":
    print("Instagram Uploader — config check")
    tok = os.getenv("IG_ACCESS_TOKEN", "NOT SET")
    uid = os.getenv("IG_USER_ID",      "NOT SET")
    print(f"  IG_ACCESS_TOKEN: {'✅ set' if tok != 'NOT SET' else '❌ MISSING'}")
    print(f"  IG_USER_ID:      {'✅ set' if uid != 'NOT SET' else '❌ MISSING'}")
    print(f"  IMGBB_API_KEY:   {'✅ set' if os.getenv('IMGBB_API_KEY') else '❌ MISSING'}")
