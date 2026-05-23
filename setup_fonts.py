"""
==============================================================
 setup_fonts.py — Download free bold fonts for poster design
 Run once before starting the bot: python setup_fonts.py
==============================================================
"""

import os
import requests
from pathlib import Path

FONT_DIR = Path("fonts")
FONT_DIR.mkdir(exist_ok=True)

# Google Fonts — Bebas Neue (cinematic bold headlines)
# These are open-source fonts, safe for commercial use
FONTS = {
    "bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/bebasneuepro/"
        "BebasNeuePro-Bold.ttf"
    ),
    "regular.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/bebasneuepro/"
        "BebasNeuePro-Regular.ttf"
    ),
}

# Fallback fonts (simpler, definitely available)
FALLBACK_FONTS = {
    "bold.ttf":    "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Bold.ttf",
    "regular.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf",
}


def download_font(filename: str, url: str) -> bool:
    dest = FONT_DIR / filename
    if dest.exists():
        print(f"  ✅ {filename} already exists")
        return True
    try:
        print(f"  ⬇️  Downloading {filename}...")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        print(f"  ✅ {filename} saved ({len(resp.content)//1024} KB)")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


if __name__ == "__main__":
    print("🔤 Downloading fonts for Tamil News Bot poster...")
    for fname, url in FONTS.items():
        ok = download_font(fname, url)
        if not ok:
            print(f"  🔄 Trying fallback for {fname}...")
            download_font(fname, FALLBACK_FONTS[fname])
    print("\n✅ Font setup complete! Run `python main.py` to start the bot.")
