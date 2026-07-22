import logging
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import *
from src.quran_api import quran
from src.video_renderer import QuranVideoRenderer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# States
SELECT_RECIter, SELECT_SURAH, SELECT_FORMAT, GENERATING = range(4)

def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized access.")
        return
    await update.message.reply_text(
        "🕌 مرحباً بك في بوت مولد فيديوهات القرآن\n\n"
        "الأوامر المتاحة:\n"
        "/generate - توليد فيديو جديد\n"
        "/status - حالة النظام\n"
        "/auto - تشغيل/إيقاف التوليد التلقائي\n"
        "/settings - الإعدادات"
    )

async def generate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return ConversationHandler.END
    
    reciters = quran.get_reciters_list()[:10]  # أول 10 قراء
    keyboard = [[InlineKeyboardButton(r['name'], callback_data=f"rec_{r['id']}")] 
                for r in reciters]
    keyboard.append([InlineKeyboardButton("إلغاء", callback_data="cancel")])
    
    await update.message.reply_text(
        "🎙 اختر القارئ:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_RECIter

async def select_reciter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return ConversationHandler.END
    
    reciter_id = int(query.data.split("_")[1])
    context.user_data['reciter_id'] = reciter_id
    
    # اختيار السورة
    keyboard = []
    for i in range(1, 115):
        if i % 5 == 1:
            keyboard.append([])
        keyboard[-1].append(InlineKeyboardButton(str(i), callback_data=f"sura_{i}"))
    
    await query.edit_message_text(
        "📖 اختر رقم السورة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_SURAH

async def select_surah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    surah = int(query.data.split("_")[1])
    context.user_data['surah'] = surah
    
    keyboard = [
        [InlineKeyboardButton("YouTube (16:9)", callback_data="fmt_youtube")],
        [InlineKeyboardButton("Shorts/Reels (9:16)", callback_data="fmt_shorts")],
        [InlineKeyboardButton("Square (1:1)", callback_data="fmt_square")]
    ]
    
    await query.edit_message_text(
        "📱 اختر صيغة الفيديو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_FORMAT

async def select_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    fmt = query.data.split("_")[1]
    context.user_data['format'] = fmt
    
    await query.edit_message_text("⏳ جاري التحضير...")
    
    # بدء التوليد
    asyncio.create_task(generate_video_task(update, context))
    return ConversationHandler.END

async def generate_video_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = context.user_data
    
    reciter_id = data['reciter_id']
    surah = data['surah']
    fmt = data['format']
    
    try:
        # تحميل الصوت
        audio_path = AUDIO_DIR / f"{reciter_id}_{surah}.mp3"
        if not audio_path.exists():
            await query.edit_message_text("🔽 جاري تحميل التلاوة...")
            quran.get_surah_audio(reciter_id, surah, audio_path)
        
        # جلب النص
        await query.edit_message_text("📜 جاري جلب نص الآيات...")
        verses = quran.get_ayahs_text(surah)
        
        if not verses:
            await query.edit_message_text("❌ خطأ في جلب النص")
            return
        
        # تصيير الفيديو
        await query.edit_message_text("🎬 جاري تصيير الفيديو... (قد يستغرق دقائق)")
        
        renderer = QuranVideoRenderer(type('S', (), {
            'VIDEO_SIZES': VIDEO_SIZES,
            'DEFAULT_SIZE': fmt,
            'DEFAULT_FONT': DEFAULT_FONT,
            'DEFAULT_BG': DEFAULT_BG
        }))
        
        output_path = OUTPUT_DIR / f"surah_{surah}_{fmt}.mp4"
        
        def progress(p):
            asyncio.create_task(
                query.edit_message_text(f"🎬 جاري التصيير... {p:.0f}%")
            )
        
        renderer.render_video(audio_path, verses, output_path, DEFAULT_BG, progress)
        
        # إرسال الفيديو
        await context.bot.send_video(
            chat_id=ADMIN_ID,
            video=open(output_path, 'rb'),
            caption=f"✅ سورة {surah} - صيغة {fmt}",
            supports_streaming=True
        )
        
        await query.edit_message_text("✅ تم الإنشاء بنجاح!")
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        await query.edit_message_text(f"❌ خطأ: {str(e)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text("✅ البوت يعمل | VPS Active")

async def auto_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    
    job_queue = context.job_queue
    
    if job_queue.get_jobs_by_name("daily_quran"):
        # إيقاف
        for job in job_queue.get_jobs_by_name("daily_quran"):
            job.schedule_removal()
        await update.message.reply_text("⏹ التوليد التلقائي متوقف")
    else:
        # تشغيل يومياً الساعة 6 صباحاً
        job_queue.run_daily(
            daily_generation,
            time=datetime.time(hour=6, minute=0),
            name="daily_quran"
        )
        await update.message.reply_text("▶️ التوليد التلقائي مفعل (يومياً 6:00 ص)")

async def daily_generation(context: ContextTypes.DEFAULT_TYPE):
    """مهمة التوليد اليومية"""
    # توليد فيديو عشوائي
    import random
    surah = random.randint(1, 114)
    # ... نفس منطق التوليد

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate", generate_start)],
        states={
            SELECT_RECIter: [CallbackQueryHandler(select_reciter, pattern="^rec_")],
            SELECT_SURAH: [CallbackQueryHandler(select_surah, pattern="^sura_")],
            SELECT_FORMAT: [CallbackQueryHandler(select_format, pattern="^fmt_")],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("❌ تم الإلغاء"), pattern="^cancel$")]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("auto", auto_schedule))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
