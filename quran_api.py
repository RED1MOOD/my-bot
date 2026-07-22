import requests
from pathlib import Path
import json

class QuranAPI:
    def __init__(self):
        self.session = requests.Session()
        self.reciters = self._load_reciters()
    
    def _load_reciters(self):
        """جلب قائمة القراء من MP3Quran"""
        try:
            r = self.session.get("https://www.mp3quran.net/api/v3/reciters", timeout=30)
            return r.json().get('reciters', [])
        except Exception as e:
            print(f"Error loading reciters: {e}")
            return []
    
    def get_surah_audio(self, reciter_id: int, surah_number: int, save_path: Path):
        """تحميل صوت السورة"""
        try:
            url = f"https://server8.mp3quran.net/{reciter_id}/{surah_number:03d}.mp3"
            r = self.session.get(url, stream=True, timeout=60)
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return save_path
        except Exception as e:
            print(f"Error downloading audio: {e}")
        return None
    
    def get_ayahs_text(self, surah_number: int):
        """جلب نص الآيات من Quran.com API"""
        try:
            url = f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={surah_number}"
            r = self.session.get(url, timeout=30)
            data = r.json()
            verses = data.get('verses', [])
            return [{"text": v['text_uthmani'], "verse_key": v['verse_key']} for v in verses]
        except Exception as e:
            print(f"Error fetching verses: {e}")
            return []
    
    def get_reciters_list(self):
        return self.reciters

quran = QuranAPI()
