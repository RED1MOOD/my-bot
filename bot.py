#!/usr/bin/env python3
"""
Quran Video Generator Bot - Single File Edition
==================================================
A complete Telegram bot that generates Quran videos with Arabic text overlays.
All-in-one file: settings, API, video renderer, and bot handlers.

Setup:
    pip install python-telegram-bot==20.7 APScheduler==3.10.4 moviepy==1.0.3 Pillow==10.2.0 requests==2.31.0 python-dotenv==1.0.0 arabic-reshaper==3.0.0 python-bidi==0.4.2 numpy==1.26.3 imageio==2.33.1 imageio-ffmpeg==0.4.9 setuptools==68.2.2

Run:
    python quran_bot_single_file.py

Author: AI Assistant
"""

import sys
import os
import logging
import asyncio
import random
import textwrap
import requests
import numpy as np
from pathlib import Path
from datetime import datetime, time as dt_time
from typing import Optional, List, Dict, Any

# =============================================================================
# SETTINGS & CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.absolute()

# Telegram (CHANGE THESE!)
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
DEFAULT_FONT = FONTS_DIR / "Amiri-Regular.ttf"
DEFAULT_BG = BG_DIR / "default.mp4"

# API URLs
MP3QURAN_API = "https://www.mp3quran.net/api/v3"
QURAN_COM_API = "https://api.quran.com/api/v4"

# Reciters mapping (popular reciters)
RECITERS = {
    "mishary": {"id": 7, "name": "مشاري راشد العفاسي", "server": "https://server8.mp3quran.net/afs"},
    "abdulbasit": {"id": 1, "name": "عبد الباسط عبد الصمد", "server": "https://server7.mp3quran.net/basit"},
    "maher": {"id": 9, "name": "ماهر المعيقلي", "server": "https://server12.mp3quran.net/maher"},
    "sudais": {"id": 3, "name": "عبدالرحمن السديس", "server": "https://server11.mp3quran.net/sds"},
    "shuraim": {"id": 4, "name": "سعود الشريم", "server": "https://server7.mp3quran.net/shur"},
    "minshawi": {"id": 5, "name": "محمد صديق المنشاوي", "server": "https://server10.mp3quran.net/minsh"},
    "husary": {"id": 6, "name": "محمود خليل الحصري", "server": "httpsserver13.mp3quran.net/husr"},
    "ajmi": {"id": 8, "name": "أحمد بن علي العجمي", "server": "https://server10.mp3quran.net/ajm"},
    "ghamidi": {"id": 10, "name": "سعد الغامدي", "server": "https://server7.mp3quran.net/sgd"},
    "juhany": {"id": 11, "name": "عبدالله عواد الجهني", "server": "https://server16.mp3quran.net/jhn"},
}

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

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# QURAN API
# =============================================================================

class QuranAPI:
    """Interface for fetching Quran audio and text from online APIs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuranVideoBot/1.0 (Python requests)'
        })
    
    def get_surah_audio(self, reciter_key: str, surah_number: int, save_path: Path) -> Optional[Path]:
        """Download surah audio from MP3Quran servers."""
        try:
            reciter = RECITERS.get(reciter_key, RECITERS["mishary"])
            url = f"{reciter['server']}/{surah_number:03d}.mp3"
            logger.info(f"Downloading audio from: {url}")
            
            response = self.session.get(url, stream=True, timeout=120)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Audio saved: {save_path}")
                return save_path
            else:
                logger.error(f"Failed to download audio: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
        return None
    
    def get_ayahs_text(self, surah_number: int) -> List[Dict[str, str]]:
        """Fetch Uthmani text of verses from Quran.com API."""
        try:
            url = f"{QURAN_COM_API}/quran/verses/uthmani?chapter_number={surah_number}"
            response = self.session.get(url, timeout=30)
            data = response.json()
            verses = data.get('verses', [])
            return [{"text": v['text_uthmani'], "verse_key": v['verse_key']} for v in verses]
        except Exception as e:
            logger.error(f"Error fetching verses: {e}")
            return []
    
    def get_surah_info(self, surah_number: int) -> Dict[str, Any]:
        """Get surah metadata."""
        try:
            url = f"{QURAN_COM_API}/chapters/{surah_number}"
            response = self.session.get(url, timeout=30)
            return response.json().get('chapter', {})
        except Exception as e:
            logger.error(f"Error fetching surah info: {e}")
            return {}

quran = QuranAPI()

# =============================================================================
# VIDEO RENDERER
# =============================================================================

try:
    os.environ['IMAGEIO_FFMPEG_EXE'] = '/usr/bin/ffmpeg'
    from moviepy.editor import (
        VideoClip, AudioFileClip, CompositeVideoClip, 
        ColorClip, concatenate_videoclips
    )
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import arabic_reshaper
    from bidi.algorithm import get_display
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import video libraries: {e}")
    MOVIEPY_AVAILABLE = False


class QuranVideoRenderer:
    """Renders Quran videos with Arabic text overlays and animated backgrounds."""
    
    def __init__(self, size_key: str = "shorts"):
        self.size = VIDEO_SIZES.get(size_key, VIDEO_SIZES["shorts"])
        self.font_path = str(DEFAULT_FONT) if DEFAULT_FONT.exists() else None
        self._ensure_font()
    
    def _ensure_font(self):
        """Ensure a valid Arabic font is available."""
        if self.font_path and Path(self.font_path).exists():
            return
        # Try system fonts
        system_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
        for f in system_fonts:
            if Path(f).exists():
                self.font_path = f
                logger.info(f"Using system font: {f}")
                return
        logger.warning("No suitable font found! Text rendering may fail.")
    
    def prepare_arabic_text(self, text: str) -> str:
        """Reshape and reorder Arabic text for proper display."""
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
    
    def create_animated_background(self, duration: float) -> VideoClip:
        """Create an animated gradient background with subtle particles."""
        w, h = self.size
        
        def make_frame(t):
            # Create gradient background
            img = np.zeros((h, w, 3), dtype=np.uint8)
            
            # Animated gradient colors (dark blue to dark purple)
            phase = (t / duration) * 2 * np.pi
            r1, g1, b1 = 10, 15, 35
            r2, g2, b2 = 25, 10, 40
            
            for y in range(h):
                ratio = y / h
                r = int(r1 + (r2 - r1) * ratio + 5 * np.sin(phase + ratio * 3))
                g = int(g1 + (g2 - g1) * ratio + 5 * np.cos(phase + ratio * 2))
                b = int(b1 + (b2 - b1) * ratio + 8 * np.sin(phase * 0.5 + ratio * 4))
                img[y, :] = [max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))]
            
            # Add subtle particles
            np.random.seed(42)
            num_particles = 30
            for i in range(num_particles):
                px = int((np.sin(phase * 0.3 + i * 1.5) * 0.4 + 0.5) * w)
                py = int((np.cos(phase * 0.2 + i * 2.1) * 0.4 + 0.5) * h)
                size = int(2 + np.sin(phase + i) * 1.5)
                brightness = int(100 + np.sin(phase * 2 + i) * 50)
                color = (brightness, brightness + 20, brightness + 40)
                
                for dy in range(-size, size + 1):
                    for dx in range(-size, size + 1):
                        if dx*dx + dy*dy <= size*size:
                            x, y = px + dx, py + dy
                            if 0 <= x < w and 0 <= y < h:
                                img[y, x] = color
            
            return img
        
        return VideoClip(make_frame, duration=duration)
    
    def create_text_frame(self, text: str, font_size: int = 70, 
                         subtitle: str = "", subtitle_size: int = 35):
        """Create a single frame with Arabic text overlay."""
        w, h = self.size
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, font_size)
            sub_font = ImageFont.truetype(self.font_path, subtitle_size) if subtitle else None
        except Exception:
            font = ImageFont.load_default()
            sub_font = None
        
        # Prepare main text
        arabic_text = self.prepare_arabic_text(text)
        lines = textwrap.wrap(arabic_text, width=30)
        
        line_height = font_size + 20
        total_height = len(lines) * line_height
        y_start = (h - total_height) // 2 - (40 if subtitle else 0)
        
        # Draw main text with shadow
        y = y_start
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (w - text_width) // 2
            
            # Shadow
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 180))
            # Main text with golden gradient effect
            draw.text((x, y), line, font=font, fill=(255, 235, 180, 255))
            y += line_height
        
        # Draw subtitle (surah name)
        if subtitle and sub_font:
            sub_arabic = self.prepare_arabic_text(subtitle)
            bbox = draw.textbbox((0, 0), sub_arabic, font=sub_font)
            sub_width = bbox[2] - bbox[0]
            sub_x = (w - sub_width) // 2
            sub_y = h - 120
            draw.text((sub_x + 2, sub_y + 2), sub_arabic, font=sub_font, fill=(0, 0, 0, 150))
            draw.text((sub_x, sub_y), sub_arabic, font=sub_font, fill=(200, 180, 140, 255))
        
        return np.array(img)
    
    def create_text_clip(self, text: str, duration: float, 
                         subtitle: str = "", fade_in: float = 0.5, fade_out: float = 0.5):
        """Create an animated text clip with fade effects."""
        def make_frame(t):
            frame = self.create_text_frame(text, subtitle=subtitle)
            
            # Apply fade
            alpha = 1.0
            if t < fade_in:
                alpha = t / fade_in
            elif t > duration - fade_out:
                alpha = (duration - t) / fade_out
            
            alpha = max(0, min(1, alpha))
            frame = frame.astype(float)
            frame[:, :, 3] = frame[:, :, 3] * alpha
            return frame.astype(np.uint8)
        
        return VideoClip(make_frame, duration=duration).set_position("center")
    
    def render_video(self, audio_path: Path, verses: List[Dict], output_path: Path,
                     surah_name: str = "", progress_callback=None) -> Optional[Path]:
        """Render the final Quran video."""
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available!")
            return None
        
        try:
            # Load audio
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration
            logger.info(f"Audio duration: {duration:.2f}s")
            
            # Create animated background
            logger.info("Creating animated background...")
            bg = self.create_animated_background(duration)
            
            # Calculate verse timing
            num_verses = max(len(verses), 1)
            verse_duration = duration / num_verses
            clips = [bg]
            
            logger.info(f"Rendering {num_verses} verses...")
            
            for i, verse in enumerate(verses):
                start_time = i * verse_duration
                text = verse.get('text', '')
                
                if not text:
                    continue
                
                # Create text clip for this verse
                txt_clip = self.create_text_clip(
                    text,
                    duration=verse_duration,
                    subtitle=f"سورة {surah_name}" if surah_name else ""
                ).set_start(start_time)
                
                clips.append(txt_clip)
                
                if progress_callback:
                    progress_callback((i + 1) / num_verses * 100)
                
                logger.info(f"Verse {i+1}/{num_verses} rendered")
            
            # Composite everything
            logger.info("Compositing video...")
            final = CompositeVideoClip(clips).set_audio(audio)
            
            # Export
            logger.info(f"Exporting to {output_path}...")
            final.write_videofile(
                str(output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                preset='ultrafast',
                logger=None
            )
            
            # Cleanup
            final.close()
            audio.close()
            for c in clips:
                c.close()
            
            logger.info(f"Video saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Rendering error: {e}", exc_info=True)
            return None


# =============================================================================
# TELEGRAM BOT
# =============================================================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# Conversation states
SELECT_RECIter, SELECT_SURAH, SELECT_FORMAT, GENERATING = range(4)

def is_admin(update: Update) -> bool:
    """Check if user is the admin."""
    return update.effective_user.id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized access.")
        return
    
    welcome = (
        "🕌 <b>مرحباً بك في بوت مولد فيديوهات القرآن</b>\n\n"
        "📌 <b>الأوامر المتاحة:</b>\n"
        "/generate - توليد فيديو جديد\n"
        "/status - حالة النظام\n"
        "/auto - تشغيل/إيقاف التوليد التلقائي\n"
        "/cancel - إلغاء العملية الحالية\n\n"
        "🎬 اضغط /generate للبدء"
    )
    await update.message.reply_text(welcome, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command."""
    if not is_admin(update):
        return
    
    help_text = (
        "📖 <b>دليل الاستخدام:</b>\n\n"
        "1️⃣ /generate - ابدأ معالج توليد الفيديو\n"
        "2️⃣ اختر القارئ من القائمة\n"
        "3️⃣ اختر رقم السورة (1-114)\n"
        "4️⃣ اختر صيغة الفيديو (Shorts/Reels/YouTube)\n"
        "5️⃣ انتظر حتى يكتمل التصيير\n\n"
        "⚙️ <b>إعدادات متقدمة:</b>\n"
        "/auto - تفعيل التوليد اليومي التلقائي\n"
        "/status - فحص حالة VPS والموارد\n"
        "/cancel - إلغاء أي عملية جارية"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def generate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start video generation wizard."""
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
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    
    await update.message.reply_text(
        "🎙 <b>اختر القارئ:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_RECIter

async def select_reciter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reciter selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return ConversationHandler.END
    
    reciter_key = query.data.split("_")[1]
    context.user_data['reciter_key'] = reciter_key
    reciter_name = RECITERS[reciter_key]['name']
    
    # Build surah selection keyboard
    keyboard = []
    row = []
    for i in range(1, 115):
        row.append(InlineKeyboardButton(str(i), callback_data=f"sura_{i}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    
    await query.edit_message_text(
        f"✅ القارئ: <b>{reciter_name}</b>\n\n📖 اختر رقم السورة:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_SURAH

async def select_surah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle surah selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return ConversationHandler.END
    
    surah = int(query.data.split("_")[1])
    context.user_data['surah'] = surah
    surah_name = SURAH_NAMES[surah - 1] if surah <= 114 else f"سورة {surah}"
    context.user_data['surah_name'] = surah_name
    
    keyboard = [
        [InlineKeyboardButton("📱 Shorts / Reels (9:16)", callback_data="fmt_shorts")],
        [InlineKeyboardButton("🎬 YouTube (16:9)", callback_data="fmt_youtube")],
        [InlineKeyboardButton("⬜ Square (1:1)", callback_data="fmt_square")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]
    
    await query.edit_message_text(
        f"✅ السورة: <b>{surah_name}</b>\n\n📱 اختر صيغة الفيديو:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return SELECT_FORMAT

async def select_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format selection and start generation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return ConversationHandler.END
    
    fmt = query.data.split("_")[1]
    context.user_data['format'] = fmt
    
    reciter_key = context.user_data['reciter_key']
    surah = context.user_data['surah']
    surah_name = context.user_data['surah_name']
    
    await query.edit_message_text(
        f"⏳ <b>جاري التحضير...</b>\n\n"
        f"🎙 القارئ: {RECITERS[reciter_key]['name']}\n"
        f"📖 السورة: {surah_name}\n"
        f"📱 الصيغة: {fmt}",
        parse_mode="HTML"
    )
    
    # Start generation in background
    asyncio.create_task(
        generate_video_task(update, context, query)
    )
    return ConversationHandler.END

async def generate_video_task(update: Update, context: ContextTypes.DEFAULT_TYPE, query):
    """Background task for video generation."""
    data = context.user_data
    reciter_key = data['reciter_key']
    surah = data['surah']
    surah_name = data['surah_name']
    fmt = data['format']
    
    try:
        # Download audio
        audio_path = AUDIO_DIR / f"{reciter_key}_{surah:03d}.mp3"
        if not audio_path.exists():
            await query.edit_message_text(
                f"🔽 <b>جاري تحميل التلاوة...</b>\nسورة {surah_name}",
                parse_mode="HTML"
            )
            result = quran.get_surah_audio(reciter_key, surah, audio_path)
            if not result:
                await query.edit_message_text("❌ فشل تحميل الصوت")
                return
        
        # Fetch verses
        await query.edit_message_text(
            f"📜 <b>جاري جلب نص الآيات...</b>\nسورة {surah_name}",
            parse_mode="HTML"
        )
        verses = quran.get_ayahs_text(surah)
        
        if not verses:
            await query.edit_message_text("❌ خطأ في جلب نص الآيات")
            return
        
        # Render video
        await query.edit_message_text(
            f"🎬 <b>جاري تصيير الفيديو...</b>\n"
            f"سورة {surah_name} | {len(verses)} آية\n"
            f"⏳ قد يستغرق بضع دقائق...",
            parse_mode="HTML"
        )
        
        renderer = QuranVideoRenderer(size_key=fmt)
        output_path = OUTPUT_DIR / f"surah_{surah:03d}_{reciter_key}_{fmt}.mp4"
        
        def progress(p):
            # Update progress every 20%
            if int(p) % 20 == 0:
                asyncio.create_task(
                    query.edit_message_text(
                        f"🎬 <b>جاري التصيير...</b> {p:.0f}%\n"
                        f"سورة {surah_name}",
                        parse_mode="HTML"
                    )
                )
        
        result = renderer.render_video(
            audio_path, verses, output_path, 
            surah_name=surah_name,
            progress_callback=progress
        )
        
        if result and result.exists():
            # Send video
            await context.bot.send_video(
                chat_id=ADMIN_ID,
                video=open(result, 'rb'),
                caption=(
                    f"✅ <b>تم الإنشاء بنجاح!</b>\n\n"
                    f"📖 سورة {surah_name}\n"
                    f"🎙 {RECITERS[reciter_key]['name']}\n"
                    f"📱 صيغة: {fmt}"
                ),
                parse_mode="HTML",
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
                connect_timeout=60
            )
            await query.edit_message_text("✅ تم الإرسال!")
        else:
            await query.edit_message_text("❌ فشل تصيير الفيديو")
            
    except Exception as e:
        logger.error(f"Generation error: {e}", exc_info=True)
        await query.edit_message_text(f"❌ خطأ: {str(e)[:200]}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show system status."""
    if not is_admin(update):
        return
    
    import platform
    import psutil
    
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status_text = (
            "📊 <b>حالة النظام</b>\n\n"
            f"🖥 CPU: {cpu}%\n"
            f"💾 RAM: {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)\n"
            f"💿 Disk: {disk.percent}% used\n"
            f"🐍 Python: {platform.python_version()}\n"
            f"🎬 MoviePy: {'✅' if MOVIEPY_AVAILABLE else '❌'}\n"
            f"🔤 Font: {'✅' if DEFAULT_FONT.exists() else '❌'}\n"
            f"🎵 FFmpeg: {'✅' if os.path.exists('/usr/bin/ffmpeg') else '❌'}\n\n"
            f"📁 Videos: {len(list(OUTPUT_DIR.glob('*.mp4')))} file(s)"
        )
    except ImportError:
        status_text = (
            "📊 <b>حالة النظام</b>\n\n"
            f"🐍 Python: {platform.python_version()}\n"
            f"🎬 MoviePy: {'✅' if MOVIEPY_AVAILABLE else '❌'}\n"
            f"🔤 Font: {'✅' if DEFAULT_FONT.exists() else '❌'}\n"
            f"🎵 FFmpeg: {'✅' if os.path.exists('/usr/bin/ffmpeg') else '❌'}\n\n"
            f"📁 Videos: {len(list(OUTPUT_DIR.glob('*.mp4')))} file(s)\n\n"
            "⚠️ Install psutil for detailed stats: pip install psutil"
        )
    
    await update.message.reply_text(status_text, parse_mode="HTML")

async def auto_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle daily auto-generation."""
    if not is_admin(update):
        return
    
    job_queue = context.job_queue
    jobs = job_queue.get_jobs_by_name("daily_quran")
    
    if jobs:
        for job in jobs:
            job.schedule_removal()
        await update.message.reply_text(
            "⏹ <b>التوليد التلقائي متوقف</b>\n"
            "لن يتم إنشاء فيديوهات تلقائياً.",
            parse_mode="HTML"
        )
    else:
        job_queue.run_daily(
            daily_generation,
            time=dt_time(hour=6, minute=0),
            name="daily_quran",
            chat_id=ADMIN_ID
        )
        await update.message.reply_text(
            "▶️ <b>التوليد التلقائي مفعل!</b>\n"
            "📅 يومياً الساعة 6:00 صباحاً\n"
            "سيتم إنشاء فيديو عشوائي تلقائياً.",
            parse_mode="HTML"
        )

async def daily_generation(context: ContextTypes.DEFAULT_TYPE):
    """Daily auto-generation task."""
    try:
        surah = random.randint(1, 114)
        reciter_key = random.choice(list(RECITERS.keys()))
        surah_name = SURAH_NAMES[surah - 1]
        
        await context.bot.send_message(
            ADMIN_ID,
            f"🤖 <b>التوليد التلقائي اليومي</b>\n"
            f"📖 سورة {surah_name}\n"
            f"🎙 {RECITERS[reciter_key]['name']}\n"
            f"⏳ جاري التحضير...",
            parse_mode="HTML"
        )
        
        # Reuse generation logic
        audio_path = AUDIO_DIR / f"{reciter_key}_{surah:03d}.mp3"
        if not audio_path.exists():
            quran.get_surah_audio(reciter_key, surah, audio_path)
        
        verses = quran.get_ayahs_text(surah)
        if verses:
            renderer = QuranVideoRenderer(size_key="shorts")
            output_path = OUTPUT_DIR / f"auto_surah_{surah:03d}_{reciter_key}.mp4"
            result = renderer.render_video(audio_path, verses, output_path, surah_name=surah_name)
            
            if result and result.exists():
                await context.bot.send_video(
                    ADMIN_ID,
                    video=open(result, 'rb'),
                    caption=f"🤖 <b>فيديو اليوم التلقائي</b>\n📖 سورة {surah_name}",
                    parse_mode="HTML"
                )
                
    except Exception as e:
        logger.error(f"Daily generation error: {e}")
        await context.bot.send_message(
            ADMIN_ID,
            f"❌ خطأ في التوليد التلقائي: {str(e)[:200]}",
            parse_mode="HTML"
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation."""
    if not is_admin(update):
        return
    await update.message.reply_text("✅ تم إلغاء العملية الحالية.")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ حدث خطأ غير متوقع. تحقق من اللوجز."
        )

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("Quran Video Generator Bot - Starting...")
    logger.info(f"Admin ID: {ADMIN_ID}")
    logger.info(f"Output dir: {OUTPUT_DIR}")
    logger.info(f"MoviePy available: {MOVIEPY_AVAILABLE}")
    logger.info(f"Font exists: {DEFAULT_FONT.exists()}")
    logger.info("=" * 50)
    
    # Build application with extended timeouts
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(60)
        .write_timeout(60)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Conversation handler for video generation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate", generate_start)],
        states={
            SELECT_RECIter: [CallbackQueryHandler(select_reciter, pattern="^rec_")],
            SELECT_SURAH: [CallbackQueryHandler(select_surah, pattern="^sura_")],
            SELECT_FORMAT: [CallbackQueryHandler(select_format, pattern="^fmt_")],
        },
        fallbacks=[
            CallbackQueryHandler(
                lambda u, c: u.callback_query.edit_message_text("❌ تم الإلغاء"), 
                pattern="^cancel$"
            ),
            CommandHandler("cancel", cancel)
        ],
        per_message=False
    )
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("auto", auto_schedule))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running! Press Ctrl+C to stop.")
    
    # Run with polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
