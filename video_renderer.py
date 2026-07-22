import os
os.environ['IMAGEIO_FFMPEG_EXE'] = '/usr/bin/ffmpeg'

from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
from pathlib import Path
import textwrap

class QuranVideoRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.size = settings.VIDEO_SIZES[settings.DEFAULT_SIZE]
        self.font_path = str(settings.DEFAULT_FONT)
        
    def prepare_arabic_text(self, text: str, font_size: int = 60):
        """تحضير النص العربي للعرض"""
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
    
    def create_text_clip(self, text: str, duration: float, font_size: int = 70):
        """إنشاء مقطع نصي متحرك"""
        def make_frame(t):
            # إنشاء صورة شفافة
            img = Image.new('RGBA', self.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype(self.font_path, font_size)
            except:
                font = ImageFont.load_default()
            
            # تحضير النص
            arabic_text = self.prepare_arabic_text(text, font_size)
            
            # تقسيم النص إذا كان طويلاً
            lines = textwrap.wrap(arabic_text, width=25)
            
            # حساب الارتفاع الكلي
            line_height = font_size + 20
            total_height = len(lines) * line_height
            y_start = (self.size[1] - total_height) // 2
            
            # تأثير الظهور والتلاشي
            alpha = 255
            if t < 0.5:
                alpha = int((t / 0.5) * 255)
            elif t > duration - 0.5:
                alpha = int(((duration - t) / 0.5) * 255)
            
            # رسم النص
            y = y_start
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.size[0] - text_width) // 2
                
                # ظل خلف النص
                draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, alpha))
                # النص الأساسي
                draw.text((x, y), line, font=font, fill=(255, 255, 255, alpha))
                y += line_height
            
            return np.array(img)
        
        return VideoClip(make_frame, duration=duration)
    
    def render_video(self, audio_path: Path, verses: list, output_path: Path, 
                     bg_path: Path = None, progress_callback=None):
        """تصيير الفيديو النهائي"""
        
        # تحميل الصوت
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        
        # الخلفية
        if bg_path and bg_path.exists():
            bg = VideoFileClip(str(bg_path)).resize(self.size).loop(duration=duration)
        else:
            # خلفية سوداء مع تأثير بسيط
            bg = ColorClip(size=self.size, color=(20, 20, 30)).set_duration(duration)
        
        # تقسيم الوقت على الآيات
        verse_duration = duration / max(len(verses), 1)
        clips = [bg]
        
        for i, verse in enumerate(verses):
            start = i * verse_duration
            txt_clip = self.create_text_clip(
                verse['text'], 
                duration=verse_duration
            ).set_start(start).set_duration(verse_duration)
            clips.append(txt_clip)
            
            if progress_callback:
                progress_callback((i + 1) / len(verses) * 100)
        
        # دمج كل شيء
        final = CompositeVideoClip(clips).set_audio(audio)
        
        # تصدير
        final.write_videofile(
            str(output_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='ultrafast',
            logger=None
        )
        
        # تنظيف
        final.close()
        audio.close()
        for c in clips:
            c.close()
        
        return output_path
