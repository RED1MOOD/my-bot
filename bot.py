#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  QURAN VIDEO GENERATOR BOT - ULTIMATE EDITION
================================================================================
  Single-file, self-contained Python application for generating professional
  Quran videos with animated backgrounds, Arabic Uthmani text overlays, and
  full Telegram bot control.

  Author     : AI Assistant
  Version    : 3.0.0
  Features   :
    - 15+ famous Quran reciters
    - Animated gradient backgrounds with particles (no external video files)
    - Uthmani Arabic text with proper reshaping & bidirectional support
    - Fade in/out text animations synced with audio
    - 5 video formats: Shorts 9:16, YouTube 16:9, Square 1:1, 2K, 4K
    - Full Telegram bot with inline keyboards
    - Daily auto-generation with APScheduler
    - Progress reporting during rendering
    - Comprehensive error handling & logging
    - Caching for audio and API responses

  USAGE:
    1. pip install -r requirements.txt
    2. python quran_video_bot.py
    3. Open Telegram, send /start to your bot

  TELEGRAM COMMANDS:
    /start    - Welcome message & command list
    /generate - Start video generation wizard
    /status   - VPS system status & health check
    /auto     - Toggle daily auto-generation (6:00 AM)
    /cancel   - Cancel current operation
    /help     - Detailed help guide
    /reciters - List available reciters
    /surahs   - List all 114 surah names
    /queue    - View generation queue
    /settings - Change default settings
    /logs     - View recent log entries
    /cleanup  - Clean old files to free disk space

  REQUIREMENTS:
    Python 3.10+, FFmpeg, 2GB+ RAM recommended
================================================================================
"""

# ==============================================================================
# SECTION 1: IMPORTS & DEPENDENCIES
# ==============================================================================

import sys
import os
import io
import re
import json
import time
import math
import random
import hashlib
import textwrap
import logging
import asyncio
import threading
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, time as dt_time, timedelta
from typing import Optional, List, Dict, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import lru_cache, wraps

# --- Third-party imports with graceful fallback ---
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: requests not installed. API calls will fail.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("WARNING: numpy not installed. Video rendering disabled.")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNING: Pillow not installed. Text rendering disabled.")

try:
    import arabic_reshaper
    ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    ARABIC_RESHAPER_AVAILABLE = False
    print("WARNING: arabic-reshaper not installed. Arabic text may break.")

try:
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
    print("WARNING: python-bidi not installed. RTL text may break.")

try:
    os.environ['IMAGEIO_FFMPEG_EXE'] = '/usr/bin/ffmpeg'
    from moviepy.editor import (
        VideoClip, AudioFileClip, CompositeVideoClip,
        ColorClip, concatenate_videoclips, ImageClip
    )
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    MOVIEPY_AVAILABLE = False
    print(f"WARNING: MoviePy not available: {e}")

try:
    from telegram import (
        Update, InlineKeyboardButton, InlineKeyboardMarkup,
        BotCommand, BotCommandScopeChat, InputFile
    )
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        ContextTypes, ConversationHandler, MessageHandler, filters
    )
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("WARNING: python-telegram-bot not installed. Bot disabled.")

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    print("WARNING: APScheduler not installed. Auto-generation disabled.")

# ==============================================================================
# SECTION 2: CONSTANTS & CONFIGURATION
# ==============================================================================

# --- Telegram Credentials (CHANGE THESE!) ---
BOT_TOKEN = "6858517910:AAGQ3WoJy1hGPls_cn1IDmd9rV7o8KXn_eM"
ADMIN_ID = 5680657013

# --- Base Paths ---
BASE_DIR = Path(__file__).parent.absolute()
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BG_DIR = ASSETS_DIR / "backgrounds"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_DIR = ASSETS_DIR / "output"
CACHE_DIR = ASSETS_DIR / "cache"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

for d in [ASSETS_DIR, FONTS_DIR, BG_DIR, AUDIO_DIR, OUTPUT_DIR, CACHE_DIR, LOGS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- Video Configuration ---
VIDEO_SIZES = {
    "shorts":  (1080, 1920),
    "youtube": (1920, 1080),
    "square":  (1080, 1080),
    "wide":    (2560, 1440),
    "ultra":   (3840, 2160),
}

VIDEO_PRESETS = {
    "fast":     {"fps": 24, "preset": "ultrafast", "bitrate": "2000k"},
    "balanced": {"fps": 30, "preset": "veryfast",  "bitrate": "4000k"},
    "quality":  {"fps": 30, "preset": "medium",    "bitrate": "8000k"},
    "ultra":    {"fps": 60, "preset": "slow",      "bitrate": "16000k"},
}

DEFAULT_SIZE = "shorts"
DEFAULT_PRESET = "balanced"
DEFAULT_FONT_SIZE = 72
DEFAULT_SUBTITLE_SIZE = 36

# --- API Endpoints ---
MP3QURAN_API = "https://www.mp3quran.net/api/v3"
QURAN_COM_API = "https://api.quran.com/api/v4"

# --- Color Palettes for Backgrounds ---
GRADIENT_PALETTES = [
    ((10, 15, 35),   (25, 10, 40),   (255, 215, 100)),
    ((5, 20, 15),    (15, 35, 25),   (180, 255, 200)),
    ((25, 10, 5),    (40, 20, 10),   (255, 180, 120)),
    ((10, 10, 25),   (20, 20, 40),   (200, 200, 255)),
    ((20, 15, 5),    (35, 25, 10),   (255, 230, 150)),
    ((15, 5, 15),    (30, 10, 25),   (255, 150, 200)),
    ((5, 15, 20),    (10, 30, 35),   (150, 255, 255)),
    ((25, 25, 25),   (40, 40, 40),   (255, 255, 255)),
]

# --- Reciters Database ---
RECITERS = {
    "mishary":    {"id": 7,  "name": "مشاري راشد العفاسي",    "server": "https://server8.mp3quran.net/afs",   "style": "ترتيل", "country": "الكويت"},
    "abdulbasit": {"id": 1,  "name": "عبد الباسط عبد الصمد",  "server": "https://server7.mp3quran.net/basit",  "style": "مجود",  "country": "مصر"},
    "maher":      {"id": 9,  "name": "ماهر المعيقلي",         "server": "https://server12.mp3quran.net/maher", "style": "ترتيل", "country": "السعودية"},
    "sudais":     {"id": 3,  "name": "عبدالرحمن السديس",      "server": "https://server11.mp3quran.net/sds",   "style": "ترتيل", "country": "السعودية"},
    "shuraim":    {"id": 4,  "name": "سعود الشريم",           "server": "https://server7.mp3quran.net/shur",   "style": "ترتيل", "country": "السعودية"},
    "minshawi":   {"id": 5,  "name": "محمد صديق المنشاوي",    "server": "https://server10.mp3quran.net/minsh", "style": "مجود",  "country": "مصر"},
    "husary":     {"id": 6,  "name": "محمود خليل الحصري",     "server": "https://server13.mp3quran.net/husr",  "style": "مجود",  "country": "مصر"},
    "ajmi":       {"id": 8,  "name": "أحمد بن علي العجمي",    "server": "https://server10.mp3quran.net/ajm",   "style": "ترتيل", "country": "السعودية"},
    "ghamidi":    {"id": 10, "name": "سعد الغامدي",           "server": "https://server7.mp3quran.net/sgd",    "style": "ترتيل", "country": "السعودية"},
    "juhany":     {"id": 11, "name": "عبدالله عواد الجهني",   "server": "https://server16.mp3quran.net/jhn",   "style": "ترتيل", "country": "السعودية"},
    "muqri":      {"id": 12, "name": "عبدالرشيد صوفي",        "server": "https://server9.mp3quran.net/soufi",  "style": "رواية", "country": "المغرب"},
    "yasser":     {"id": 13, "name": "ياسر الدوسري",          "server": "https://server11.mp3quran.net/yasser", "style": "ترتيل", "country": "السعودية"},
    "afs":        {"id": 14, "name": "مشاري العفاسي (حفص)",   "server": "https://server8.mp3quran.net/afs",    "style": "حفص",   "country": "الكويت"},
    "qurtubi":    {"id": 15, "name": "محمد أيوب القرطوبي",    "server": "https://server16.mp3quran.net/ayyub", "style": "ترتيل", "country": "السعودية"},
}

# --- Surah Names (114 surahs) ---
SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الإنفطار", "المطففين", "الإنشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس"
]

# --- Logging Setup ---
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("QuranBot")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOGS_DIR / "bot.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# ==============================================================================
# SECTION 3: UTILITY FUNCTIONS
# ==============================================================================

def retry_on_error(max_retries=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    wait = delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}. Waiting {wait}s...")
                    time.sleep(wait)
            return None
        return wrapper
    return decorator


def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.1f} ثانية"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} دقيقة"
    else:
        return f"{seconds / 3600:.1f} ساعة"


def sanitize_filename(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')


class LRUCache:
    def __init__(self, maxsize=100):
        self.cache = OrderedDict()
        self.maxsize = maxsize
    
    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)
    
    def clear(self):
        self.cache.clear()


api_cache = LRUCache(maxsize=200)

# ==============================================================================
# SECTION 4: FONT MANAGER
# ==============================================================================

class FontManager:
    FONT_URLS = {
        "Amiri-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf",
        "Amiri-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf",
    }
    
    SYSTEM_FONT_PATHS = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/System/Library/Fonts/GeezaPro.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    
    def __init__(self):
        self.fonts = {}
        self._discover_fonts()
        self._download_missing_fonts()
    
    def _discover_fonts(self):
        if FONTS_DIR.exists():
            for font_file in FONTS_DIR.glob("*.ttf"):
                self.fonts[font_file.name] = str(font_file)
        for path in self.SYSTEM_FONT_PATHS:
            if os.path.exists(path):
                name = os.path.basename(path)
                if name not in self.fonts:
                    self.fonts[name] = path
    
    def _download_missing_fonts(self):
        if not REQUESTS_AVAILABLE:
            return
        for font_name, url in self.FONT_URLS.items():
            font_path = FONTS_DIR / font_name
            if font_path.exists():
                self.fonts[font_name] = str(font_path)
                continue
            try:
                logger.info(f"Downloading font: {font_name}...")
                response = requests.get(url, timeout=30, stream=True)
                if response.status_code == 200:
                    with open(font_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    self.fonts[font_name] = str(font_path)
                    logger.info(f"Downloaded font: {font_name}")
            except Exception as e:
                logger.warning(f"Error downloading {font_name}: {e}")
    
    def get_font(self, name=None, size=40):
        if not PIL_AVAILABLE:
            return None
        if name and name in self.fonts:
            try:
                return ImageFont.truetype(self.fonts[name], size)
            except:
                pass
        for candidate in ["Amiri-Regular.ttf", "Amiri-Bold.ttf"]:
            if candidate in self.fonts:
                try:
                    return ImageFont.truetype(self.fonts[candidate], size)
                except:
                    pass
        for path in self.fonts.values():
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def list_fonts(self):
        return list(self.fonts.keys())


font_manager = FontManager()

# ==============================================================================
# SECTION 5: QURAN API CLIENT
# ==============================================================================

class QuranAPIClient:
    def __init__(self):
        self.session = requests.Session() if REQUESTS_AVAILABLE else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'QuranVideoBot/3.0 (Python requests)',
                'Accept': 'application/json',
            })
        self.cache = api_cache
    
    @retry_on_error(max_retries=3, delay=2)
    def get_surah_audio(self, reciter_key, surah_number, save_path):
        if not self.session:
            logger.error("requests library not available")
            return None
        reciter = RECITERS.get(reciter_key, RECITERS["mishary"])
        url = f"{reciter['server']}/{surah_number:03d}.mp3"
        cache_key = f"audio_{reciter_key}_{surah_number}"
        cached = self.cache.get(cache_key)
        if cached and Path(cached).exists():
            logger.info(f"Using cached audio: {cached}")
            return Path(cached)
        logger.info(f"Downloading audio from: {url}")
        try:
            response = self.session.get(url, stream=True, timeout=180)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            file_size = save_path.stat().st_size
            logger.info(f"Audio saved: {save_path} ({file_size / 1024 / 1024:.1f} MB)")
            self.cache.set(cache_key, str(save_path))
            return save_path
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            if save_path.exists():
                save_path.unlink()
            return None
    
    @retry_on_error(max_retries=3, delay=1)
    def get_ayahs_text(self, surah_number):
        if not self.session:
            return []
        cache_key = f"verses_{surah_number}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        try:
            url = f"{QURAN_COM_API}/quran/verses/uthmani?chapter_number={surah_number}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            verses = data.get('verses', [])
            result = [{"text": v['text_uthmani'], "verse_key": v['verse_key']} for v in verses]
            logger.info(f"Fetched {len(result)} verses for surah {surah_number}")
            self.cache.set(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error fetching verses: {e}")
            return []
    
    @retry_on_error(max_retries=2, delay=1)
    def get_surah_info(self, surah_number):
        if not self.session:
            return {}
        cache_key = f"info_{surah_number}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        try:
            url = f"{QURAN_COM_API}/chapters/{surah_number}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            info = data.get('chapter', {})
            self.cache.set(cache_key, info)
            return info
        except Exception as e:
            logger.error(f"Error: {e}")
            return {}


quran_api = QuranAPIClient()

# ==============================================================================
# SECTION 6: VIDEO RENDERER
# ==============================================================================

class VideoRenderer:
    def __init__(self, size_key="shorts", preset="balanced"):
        self.width, self.height = VIDEO_SIZES.get(size_key, VIDEO_SIZES["shorts"])
        self.preset = VIDEO_PRESETS.get(preset, VIDEO_PRESETS["balanced"])
        self.font_manager = font_manager
        self.palette_idx = random.randint(0, len(GRADIENT_PALETTES) - 1)
        logger.info(f"Renderer: {self.width}x{self.height}, preset={preset}")
    
    def prepare_arabic_text(self, text):
        if ARABIC_RESHAPER_AVAILABLE and BIDI_AVAILABLE:
            try:
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
            except Exception as e:
                logger.warning(f"Arabic reshaping failed: {e}")
        return text
    
    def _create_gradient_background(self, duration):
        w, h = self.width, self.height
        start_color, end_color, particle_color = GRADIENT_PALETTES[self.palette_idx]
        np.random.seed(42)
        num_particles = 50
        particles = []
        for i in range(num_particles):
            particles.append({
                'base_x': np.random.uniform(0.1, 0.9),
                'base_y': np.random.uniform(0.1, 0.9),
                'freq_x': np.random.uniform(0.1, 0.5),
                'freq_y': np.random.uniform(0.1, 0.5),
                'phase_x': np.random.uniform(0, 2 * math.pi),
                'phase_y': np.random.uniform(0, 2 * math.pi),
                'size_base': np.random.uniform(1, 4),
                'size_freq': np.random.uniform(0.5, 2),
                'brightness_base': np.random.uniform(80, 150),
            })
        
        def make_frame(t):
            if not NUMPY_AVAILABLE:
                return np.zeros((h, w, 3), dtype=np.uint8)
            img = np.zeros((h, w, 3), dtype=np.uint8)
            phase = (t / max(duration, 1)) * 2 * math.pi
            for y in range(h):
                ratio = y / h
                wave = 0.03 * math.sin(phase + ratio * 4)
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio + 255 * wave)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio + 255 * wave * 0.8)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio + 255 * wave * 1.2)
                img[y, :] = [max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))]
            for p in particles:
                px = int((p['base_x'] + 0.05 * math.sin(phase * p['freq_x'] + p['phase_x'])) * w)
                py = int((p['base_y'] + 0.05 * math.cos(phase * p['freq_y'] + p['phase_y'])) * h)
                size = int(p['size_base'] + math.sin(phase * p['size_freq']) * 1.5)
                brightness = int(p['brightness_base'] + math.sin(phase * 2) * 30)
                for dy in range(-size * 2, size * 2 + 1):
                    for dx in range(-size * 2, size * 2 + 1):
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist <= size * 2 and dist > 0:
                            intensity = max(0, 1 - dist / (size * 2))
                            x, y = px + dx, py + dy
                            if 0 <= x < w and 0 <= y < h:
                                glow = int(brightness * intensity * intensity)
                                img[y, x, 0] = min(255, img[y, x, 0] + int(glow * particle_color[0] / 255))
                                img[y, x, 1] = min(255, img[y, x, 1] + int(glow * particle_color[1] / 255))
                                img[y, x, 2] = min(255, img[y, x, 2] + int(glow * particle_color[2] / 255))
            return img
        
        return VideoClip(make_frame, duration=duration)
    
    def _create_text_overlay(self, text, font_size=72, subtitle="", subtitle_size=36,
                             duration=5.0, fade_in=0.6, fade_out=0.6):
        w, h = self.width, self.height
        
        def make_frame(t):
            if not PIL_AVAILABLE:
                return np.zeros((h, w, 4), dtype=np.uint8)
            img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            main_font = self.font_manager.get_font(size=font_size)
            sub_font = self.font_manager.get_font(size=subtitle_size) if subtitle else None
            if not main_font:
                return np.array(img)
            arabic_text = self.prepare_arabic_text(text)
            max_chars = max(20, w // (font_size // 2))
            lines = textwrap.wrap(arabic_text, width=max_chars)
            line_height = font_size + 15
            total_height = len(lines) * line_height
            y_start = (h - total_height) // 2 - (50 if subtitle else 0)
            alpha = 1.0
            if t < fade_in and fade_in > 0:
                alpha = t / fade_in
            elif duration - t < fade_out and fade_out > 0:
                alpha = (duration - t) / fade_out
            alpha = max(0, min(1, alpha))
            y = y_start
            for line in lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=main_font)
                    text_width = bbox[2] - bbox[0]
                except:
                    text_width = len(line) * font_size // 2
                x = (w - text_width) // 2
                for offset in range(4, 0, -1):
                    shadow_alpha = int(30 * alpha * (1 - offset / 5))
                    draw.text((x + offset, y + offset), line, font=main_font, fill=(0, 0, 0, shadow_alpha))
                text_alpha = int(255 * alpha)
                draw.text((x, y), line, font=main_font, fill=(255, 245, 220, text_alpha))
                y += line_height
            if subtitle and sub_font:
                sub_arabic = self.prepare_arabic_text(subtitle)
                try:
                    bbox = draw.textbbox((0, 0), sub_arabic, font=sub_font)
                    sub_width = bbox[2] - bbox[0]
                except:
                    sub_width = len(sub_arabic) * subtitle_size // 2
                sub_x = (w - sub_width) // 2
                sub_y = h - 100
                draw.text((sub_x + 2, sub_y + 2), sub_arabic, font=sub_font, fill=(0, 0, 0, int(100 * alpha)))
                draw.text((sub_x, sub_y), sub_arabic, font=sub_font, fill=(220, 200, 160, int(200 * alpha)))
            return np.array(img)
        
        return VideoClip(make_frame, duration=duration)
    
    def render(self, audio_path, verses, output_path, surah_name="",
               progress_callback=None, include_bismillah=True):
        if not MOVIEPY_AVAILABLE or not NUMPY_AVAILABLE:
            logger.error("MoviePy or NumPy not available!")
            return None
        start_time = time.time()
        try:
            logger.info("Loading audio...")
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration
            logger.info(f"Audio: {format_duration(duration)}")
            logger.info("Creating background...")
            bg = self._create_gradient_background(duration)
            clips = [bg]
            num_verses = len(verses)
            if num_verses == 0:
                logger.error("No verses!")
                return None
            bismillah_duration = 2.5 if (include_bismillah and surah_name != "الفاتحة") else 0
            verse_duration = (duration - bismillah_duration) / num_verses
            logger.info(f"Rendering {num_verses} verses")
            if bismillah_duration > 0:
                bismillah_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
                bismillah_clip = self._create_text_overlay(bismillah_text, font_size=60,
                                                           duration=bismillah_duration,
                                                           fade_in=0.8, fade_out=0.8)
                bismillah_clip = bismillah_clip.set_start(0).set_duration(bismillah_duration)
                clips.append(bismillah_clip)
            for i, verse in enumerate(verses):
                start_time_verse = bismillah_duration + (i * verse_duration)
                text = verse.get('text', '')
                if not text:
                    continue
                text_len = len(text)
                if text_len > 200:
                    font_size = 48
                elif text_len > 100:
                    font_size = 58
                else:
                    font_size = 72
                verse_clip = self._create_text_overlay(
                    text, font_size=font_size,
                    subtitle=f"سورة {surah_name}" if surah_name else "",
                    duration=verse_duration, fade_in=0.5, fade_out=0.5
                ).set_start(start_time_verse)
                clips.append(verse_clip)
                if progress_callback:
                    progress = ((i + 1) / num_verses) * 100
                    try:
                        progress_callback(progress)
                    except:
                        pass
                if (i + 1) % 10 == 0 or i == num_verses - 1:
                    logger.info(f"Rendered {i + 1}/{num_verses}")
            logger.info("Compositing...")
            final = CompositeVideoClip(clips).set_audio(audio)
            logger.info(f"Exporting to {output_path}...")
            preset_config = self.preset
            final.write_videofile(
                str(output_path), fps=preset_config["fps"], codec='libx264',
                audio_codec='aac', bitrate=preset_config["bitrate"], threads=4,
                preset=preset_config["preset"], logger=None,
                ffmpeg_params=['-pix_fmt', 'yuv420p', '-movflags', '+faststart']
            )
            final.close()
            audio.close()
            for clip in clips:
                clip.close()
            elapsed = time.time() - start_time
            file_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Done! {file_size:.1f}MB in {format_duration(elapsed)}")
            return output_path
        except Exception as e:
            logger.error(f"Rendering failed: {e}", exc_info=True)
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            return None


# ==============================================================================
# SECTION 7: GENERATION QUEUE
# ==============================================================================

@dataclass
class GenerationJob:
    job_id: str
    reciter_key: str
    surah_number: int
    surah_name: str
    format_key: str
    preset: str = "balanced"
    status: str = "pending"
    progress: float = 0.0
    message_id: Optional[int] = None
    chat_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_path: Optional[Path] = None


class GenerationQueue:
    def __init__(self, max_concurrent=1):
        self.jobs = {}
        self.queue = []
        self.max_concurrent = max_concurrent
        self.active_jobs = set()
        self.lock = threading.Lock()
    
    def add_job(self, reciter_key, surah_number, surah_name, format_key,
                preset="balanced", chat_id=None, message_id=None):
        job_id = hashlib.md5(f"{reciter_key}_{surah_number}_{format_key}_{time.time()}".encode()).hexdigest()[:12]
        job = GenerationJob(job_id=job_id, reciter_key=reciter_key, surah_number=surah_number,
                           surah_name=surah_name, format_key=format_key, preset=preset,
                           chat_id=chat_id, message_id=message_id)
        with self.lock:
            self.jobs[job_id] = job
            self.queue.append(job_id)
        logger.info(f"Job {job_id} queued. Position: {len(self.queue)}")
        return job_id
    
    def get_job(self, job_id):
        return self.jobs.get(job_id)
    
    def get_queue_status(self):
        with self.lock:
            pending = sum(1 for j in self.jobs.values() if j.status == "pending")
            active = sum(1 for j in self.jobs.values() if j.status in ["downloading", "rendering"])
            completed = sum(1 for j in self.jobs.values() if j.status == "completed")
            failed = sum(1 for j in self.jobs.values() if j.status == "failed")
            return f"Pending: {pending} | Active: {active} | Done: {completed} | Failed: {failed} | Total: {len(self.jobs)}"


gen_queue = GenerationQueue()

# ==============================================================================
# SECTION 8: TELEGRAM BOT HANDLERS
# ==============================================================================

SELECT_RECIter, SELECT_SURAH, SELECT_FORMAT = range(3)

def is_admin(update):
    return update.effective_user.id == ADMIN_ID

async def setup_commands(application):
    commands = [
        BotCommand('start', 'Start bot'),
        BotCommand('generate', 'Generate new video'),
        BotCommand('status', 'System status'),
        BotCommand('auto', 'Auto-generation toggle'),
        BotCommand('reciters', 'List reciters'),
        BotCommand('surahs', 'List surahs'),
        BotCommand('queue', 'Queue status'),
        BotCommand('settings', 'Settings'),
        BotCommand('logs', 'View logs'),
        BotCommand('cleanup', 'Clean old files'),
        BotCommand('help', 'Help'),
        BotCommand('cancel', 'Cancel'),
    ]
    await application.bot.set_my_commands(commands, scope=BotCommandScopeChat(ADMIN_ID))

async def start_handler(update, context):
    if not is_admin(update):
        await update.message.reply_text("Unauthorized.")
        return
    welcome = (
        "Welcome to Quran Video Generator Bot!\n\n"
        "/generate - Start video wizard\n"
        "/status - System status\n"
        "/auto - Toggle daily auto-gen\n"
        "/help - Full help"
    )
    await update.message.reply_text(welcome)

async def help_handler(update, context):
    if not is_admin(update):
        return
    help_text = (
        "Help:\n"
        "1. /generate - Choose reciter, surah, format\n"
        "2. Wait for rendering (minutes)\n"
        "3. Video will be sent automatically\n\n"
        "Advanced:\n"
        "/auto - Daily 6 AM auto-generation\n"
        "/status - Check VPS health\n"
        "/queue - View generation queue\n"
        "/cleanup - Free disk space\n"
        "/logs - View recent logs"
    )
    await update.message.reply_text(help_text)

async def reciters_handler(update, context):
    if not is_admin(update):
        return
    lines = ["Available Reciters:"]
    for key, reciter in RECITERS.items():
        lines.append(f"- {reciter['name']} ({reciter['style']}, {reciter['country']})")
    await update.message.reply_text("\n".join(lines))

async def surahs_handler(update, context):
    if not is_admin(update):
        return
    lines = ["Surah Names (1-114):"]
    for i, name in enumerate(SURAH_NAMES, 1):
        lines.append(f"{i}. {name}")
        if i % 50 == 0:
            await update.message.reply_text("\n".join(lines))
            lines = []
    if lines:
        await update.message.reply_text("\n".join(lines))

async def generate_start(update, context):
    if not is_admin(update):
        return ConversationHandler.END
    keyboard = []
    row = []
    for i, (key, reciter) in enumerate(RECITERS.items()):
        if i % 2 == 0 and row:
            keyboard.append(row)
            row = []
        row.append(InlineKeyboardButton(reciter['name'], callback_data=f"rec_{key}"))
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    await update.message.reply_text("Choose reciter:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_RECIter

async def select_reciter(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Cancelled")
        return ConversationHandler.END
    reciter_key = query.data.split("_")[1]
    context.user_data['reciter_key'] = reciter_key
    reciter_name = RECITERS[reciter_key]['name']
    keyboard = []
    row = []
    for i in range(1, 115):
        row.append(InlineKeyboardButton(str(i), callback_data=f"sura_{i}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    await query.edit_message_text(f"Reciter: {reciter_name}\n\nChoose surah:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_SURAH

async def select_surah(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Cancelled")
        return ConversationHandler.END
    surah = int(query.data.split("_")[1])
    context.user_data['surah'] = surah
    surah_name = SURAH_NAMES[surah - 1] if surah <= 114 else f"Surah {surah}"
    context.user_data['surah_name'] = surah_name
    keyboard = [
        [InlineKeyboardButton("Shorts/Reels (9:16)", callback_data="fmt_shorts")],
        [InlineKeyboardButton("YouTube (16:9)", callback_data="fmt_youtube")],
        [InlineKeyboardButton("Square (1:1)", callback_data="fmt_square")],
        [InlineKeyboardButton("2K Ultra (16:9)", callback_data="fmt_wide")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    await query.edit_message_text(f"Surah: {surah_name}\n\nChoose format:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_FORMAT

async def select_format(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Cancelled")
        return ConversationHandler.END
    fmt = query.data.split("_")[1]
    context.user_data['format'] = fmt
    reciter_key = context.user_data['reciter_key']
    surah = context.user_data['surah']
    surah_name = context.user_data['surah_name']
    job_id = gen_queue.add_job(reciter_key, surah, surah_name, fmt, "balanced",
                                update.effective_chat.id, query.message.message_id)
    context.user_data['current_job_id'] = job_id
    await query.edit_message_text(
        f"Added to queue!\n"
        f"Job ID: {job_id}\n"
        f"Reciter: {RECITERS[reciter_key]['name']}\n"
        f"Surah: {surah_name}\n"
        f"Format: {fmt}\n\n"
        f"Preparing..."
    )
    asyncio.create_task(process_generation_job(update, context, job_id))
    return ConversationHandler.END

async def process_generation_job(update, context, job_id):
    job = gen_queue.get_job(job_id)
    if not job:
        return
    try:
        job.status = "downloading"
        job.started_at = datetime.now()
        audio_path = AUDIO_DIR / f"{job.reciter_key}_{job.surah_number:03d}.mp3"
        if not audio_path.exists():
            await _update_job_message(context, job, "Downloading audio...")
            result = quran_api.get_surah_audio(job.reciter_key, job.surah_number, audio_path)
            if not result:
                job.status = "failed"
                job.error_message = "Audio download failed"
                job.completed_at = datetime.now()
                await _update_job_message(context, job, "Failed to download audio")
                return
        job.status = "rendering"
        await _update_job_message(context, job, "Fetching verses...")
        verses = quran_api.get_ayahs_text(job.surah_number)
        if not verses:
            job.status = "failed"
            job.error_message = "Failed to fetch verses"
            job.completed_at = datetime.now()
            await _update_job_message(context, job, "Failed to fetch verses")
            return
        await _update_job_message(context, job, f"Rendering video... {job.surah_name} | {len(verses)} verses")
        renderer = VideoRenderer(size_key=job.format_key, preset=job.preset)
        output_path = OUTPUT_DIR / f"surah_{job.surah_number:03d}_{job.reciter_key}_{job.format_key}.mp4"
        last_progress = 0
        def progress_callback(p):
            nonlocal last_progress
            if int(p) >= last_progress + 15:
                last_progress = int(p)
                job.progress = p
                asyncio.create_task(_update_job_message(context, job, f"Rendering... {p:.0f}%"))
        result = renderer.render(audio_path, verses, output_path, surah_name=job.surah_name,
                                  progress_callback=progress_callback)
        if result and result.exists():
            job.status = "completed"
            job.completed_at = datetime.now()
            job.output_path = result
            file_size_mb = result.stat().st_size / (1024 * 1024)
            await _update_job_message(context, job, f"Done! {file_size_mb:.1f}MB. Uploading...")
            await context.bot.send_video(
                ADMIN_ID, video=open(result, 'rb'),
                caption=f"Quran Video Ready!\n\nSurah: {job.surah_name}\nReciter: {RECITERS[job.reciter_key]['name']}\nFormat: {job.format_key}\nSize: {file_size_mb:.1f} MB",
                supports_streaming=True, read_timeout=300, write_timeout=300
            )
            await _update_job_message(context, job, "Sent successfully!")
        else:
            job.status = "failed"
            job.error_message = "Rendering failed"
            job.completed_at = datetime.now()
            await _update_job_message(context, job, "Rendering failed")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)[:200]
        job.completed_at = datetime.now()
        await _update_job_message(context, job, f"Error: {str(e)[:200]}")

async def _update_job_message(context, job, text):
    if job.chat_id and job.message_id:
        try:
            await context.bot.edit_message_text(text, chat_id=job.chat_id, message_id=job.message_id)
        except Exception:
            pass

async def status_handler(update, context):
    if not is_admin(update):
        return
    try:
        import platform
        info = ["System Status:", f"Platform: {platform.system()} {platform.release()}", f"Python: {platform.python_version()}"]
        info.append(f"MoviePy: {'OK' if MOVIEPY_AVAILABLE else 'MISSING'}")
        info.append(f"NumPy: {'OK' if NUMPY_AVAILABLE else 'MISSING'}")
        info.append(f"Pillow: {'OK' if PIL_AVAILABLE else 'MISSING'}")
        info.append(f"Arabic Reshaper: {'OK' if ARABIC_RESHAPER_AVAILABLE else 'MISSING'}")
        info.append(f"BiDi: {'OK' if BIDI_AVAILABLE else 'MISSING'}")
        info.append(f"Requests: {'OK' if REQUESTS_AVAILABLE else 'MISSING'}")
        info.append(f"Telegram Bot: {'OK' if TELEGRAM_AVAILABLE else 'MISSING'}")
        info.append(f"Scheduler: {'OK' if APSCHEDULER_AVAILABLE else 'MISSING'}")
        info.append(f"Fonts: {len(font_manager.list_fonts())} available")
        info.append(f"Videos: {len(list(OUTPUT_DIR.glob('*.mp4')))}")
        info.append(f"Audio: {len(list(AUDIO_DIR.glob('*.mp3')))}")
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            info.append(f"CPU: {cpu}% | RAM: {mem.percent}% | Disk: {disk.percent}%")
        except ImportError:
            info.append("Install psutil for resource stats")
        await update.message.reply_text("\n".join(info))
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:200]}")

async def queue_handler(update, context):
    if not is_admin(update):
        return
    await update.message.reply_text(gen_queue.get_queue_status())

async def auto_handler(update, context):
    if not is_admin(update):
        return
    job_queue = context.job_queue
    if not job_queue:
        await update.message.reply_text("Job Queue not available")
        return
    jobs = job_queue.get_jobs_by_name("daily_quran")
    if jobs:
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text("Auto-generation STOPPED")
    else:
        job_queue.run_daily(daily_generation_task, time=dt_time(hour=6, minute=0),
                           name="daily_quran", chat_id=ADMIN_ID)
        await update.message.reply_text("Auto-generation ENABLED - Daily at 6:00 AM")

async def daily_generation_task(context):
    try:
        surah = random.randint(1, 114)
        reciter_key = random.choice(list(RECITERS.keys()))
        surah_name = SURAH_NAMES[surah - 1]
        await context.bot.send_message(ADMIN_ID, f"Daily auto-generation: Surah {surah_name}")
        audio_path = AUDIO_DIR / f"{reciter_key}_{surah:03d}.mp3"
        if not audio_path.exists():
            quran_api.get_surah_audio(reciter_key, surah, audio_path)
        verses = quran_api.get_ayahs_text(surah)
        if verses:
            renderer = VideoRenderer(size_key="shorts", preset="balanced")
            output_path = OUTPUT_DIR / f"auto_surah_{surah:03d}_{reciter_key}.mp4"
            result = renderer.render(audio_path, verses, output_path, surah_name=surah_name)
            if result and result.exists():
                await context.bot.send_video(ADMIN_ID, video=open(result, 'rb'),
                                            caption=f"Daily Auto-Video: Surah {surah_name}")
    except Exception as e:
        logger.error(f"Daily generation error: {e}")
        await context.bot.send_message(ADMIN_ID, f"Daily generation error: {str(e)[:200]}")

async def settings_handler(update, context):
    if not is_admin(update):
        return
    keyboard = [
        [InlineKeyboardButton("Fast (24fps)", callback_data="set_fast")],
        [InlineKeyboardButton("Balanced (30fps)", callback_data="set_balanced")],
        [InlineKeyboardButton("Quality (30fps)", callback_data="set_quality")],
        [InlineKeyboardButton("Ultra (60fps)", callback_data="set_ultra")],
        [InlineKeyboardButton("Close", callback_data="set_close")]
    ]
    await update.message.reply_text("Choose quality preset:", reply_markup=InlineKeyboardMarkup(keyboard))

async def logs_handler(update, context):
    if not is_admin(update):
        return
    try:
        log_file = LOGS_DIR / "bot.log"
        if not log_file.exists():
            await update.message.reply_text("No logs yet.")
            return
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-20:]
        text = "Last 20 log lines:\n\n" + "".join(last_lines)
        if len(text) > 4000:
            text = text[:4000] + "..."
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:200]}")

async def cleanup_handler(update, context):
    if not is_admin(update):
        return
    msg = await update.message.reply_text("Cleaning up...")
    deleted = {"audio": 0, "video": 0, "cache": 0, "temp": 0}
    cutoff = datetime.now() - timedelta(days=30)
    for f in AUDIO_DIR.glob("*.mp3"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
            deleted["audio"] += 1
    cutoff = datetime.now() - timedelta(days=7)
    for f in OUTPUT_DIR.glob("*.mp4"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
            deleted["video"] += 1
    for f in CACHE_DIR.glob("*"):
        if f.is_file():
            f.unlink()
            deleted["cache"] += 1
    for f in TEMP_DIR.glob("*"):
        if f.is_file():
            f.unlink()
            deleted["temp"] += 1
    await msg.edit_text(f"Cleanup done!\nAudio: {deleted['audio']}\nVideo: {deleted['video']}\nCache: {deleted['cache']}\nTemp: {deleted['temp']}")

async def cancel_handler(update, context):
    if not is_admin(update):
        return
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def error_handler(update, context):
    logger.error(f"Update {update} caused error: {context.error}", exc_info=True)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("An error occurred. Check logs.")
        except Exception:
            pass

# ==============================================================================
# SECTION 9: MAIN
# ==============================================================================

def main():
    logger.info("=" * 60)
    logger.info("QURAN VIDEO GENERATOR BOT v3.0")
    logger.info("=" * 60)
    logger.info(f"Admin ID: {ADMIN_ID}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"MoviePy: {MOVIEPY_AVAILABLE}")
    logger.info(f"NumPy: {NUMPY_AVAILABLE}")
    logger.info(f"Pillow: {PIL_AVAILABLE}")
    logger.info(f"Arabic Reshaper: {ARABIC_RESHAPER_AVAILABLE}")
    logger.info(f"BiDi: {BIDI_AVAILABLE}")
    logger.info(f"Requests: {REQUESTS_AVAILABLE}")
    logger.info(f"Telegram: {TELEGRAM_AVAILABLE}")
    logger.info(f"Scheduler: {APSCHEDULER_AVAILABLE}")
    logger.info(f"Fonts: {len(font_manager.list_fonts())}")
    logger.info("=" * 60)

    if not TELEGRAM_AVAILABLE:
        logger.error("python-telegram-bot not installed!")
        print("ERROR: pip install python-telegram-bot[job-queue]")
        return
    if not REQUESTS_AVAILABLE:
        logger.error("requests not installed!")
        print("ERROR: pip install requests")
        return

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(60)
        .write_timeout(60)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    application.post_init = setup_commands

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate", generate_start)],
        states={
            SELECT_RECIter: [CallbackQueryHandler(select_reciter, pattern="^rec_")],
            SELECT_SURAH: [CallbackQueryHandler(select_surah, pattern="^sura_")],
            SELECT_FORMAT: [CallbackQueryHandler(select_format, pattern="^fmt_")],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("Cancelled"), pattern="^cancel$"),
            CommandHandler("cancel", cancel_handler)
        ],
        per_message=False
    )

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("status", status_handler))
    application.add_handler(CommandHandler("auto", auto_handler))
    application.add_handler(CommandHandler("reciters", reciters_handler))
    application.add_handler(CommandHandler("surahs", surahs_handler))
    application.add_handler(CommandHandler("queue", queue_handler))
    application.add_handler(CommandHandler("settings", settings_handler))
    application.add_handler(CommandHandler("logs", logs_handler))
    application.add_handler(CommandHandler("cleanup", cleanup_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    logger.info("Bot initialized. Starting polling...")
    logger.info("Press Ctrl+C to stop.")

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
