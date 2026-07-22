import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Telegram
BOT_TOKEN = "6858517910:AAGQ3WoJy1hGPls_cn1IDmd9rV7o8KXn_eM"
ADMIN_ID = 5680657013

# Paths
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BG_DIR = ASSETS_DIR / "backgrounds"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_DIR = ASSETS_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

for d in [ASSETS_DIR, FONTS_DIR, BG_DIR, AUDIO_DIR, OUTPUT_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Video Settings
VIDEO_SIZES = {
    "youtube": (1920, 1080),   # 16:9
    "shorts": (1080, 1920),    # 9:16
    "square": (1080, 1080)     # 1:1
}

DEFAULT_SIZE = "shorts"
DEFAULT_FONT = FONTS_DIR / "Amiri-Regular.ttf"  # ضع خط عثماني هنا
DEFAULT_BG = BG_DIR / "default.mp4"             # خلفية افتراضية

# API URLs
MP3QURAN_API = "https://www.mp3quran.net/api/v3"
QURAN_COM_API = "https://api.quran.com/api/v4"
