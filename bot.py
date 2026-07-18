import subprocess
import sys
import os
import telebot
import json
import threading
import time
import random
import string
import re
import requests
import zipfile
import hashlib
import base64
import shutil
import psutil
import resource
import ast
import importlib
import pkgutil
from telebot import types
from datetime import datetime, timedelta
from html import escape
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# ─── التحقق من المكتبات المطلوبة ───
required_modules = {
    'telebot': 'pyTelegramBotAPI',
    'requests': 'requests',
    'Crypto': 'pycryptodome',
    'psutil': 'psutil'
}
missing_packages = []
for module, package in required_modules.items():
    try:
        __import__(module)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f"جاري تثبيت المكتبات المفقودة: {missing_packages}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("تم التثبيت بنجاح. يرجى إعادة تشغيل السكربت.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"فشل التثبيت: {e}")
        sys.exit(1)

# ─── الإعدادات الأساسية ───
TOKEN = '8864213768:AAExfTH0Ky_8ERip_jmw55DITevtM-kpPw8'
ADMIN_ID = 5680657013
HIDDEN_LONG = "ㅤ" * 50
bot = telebot.TeleBot(TOKEN, threaded=True, parse_mode="HTML")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNNING_DIR = os.path.join(BASE_DIR, 'active_bots')
LOGS_DIR = os.path.join(BASE_DIR, 'bot_logs')
DB_DIR = os.path.join(BASE_DIR, 'database')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
STORE_DIR = os.path.join(BASE_DIR, 'store_files')
THUMBS_DIR = os.path.join(ASSETS_DIR, 'thumbs')
MARKET_DIR = os.path.join(BASE_DIR, 'market')
ENV_DIR = os.path.join(BASE_DIR, 'bot_environments')
ENCRYPTED_DIR = os.path.join(BASE_DIR, 'encrypted_files')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
GIFTS_DIR = os.path.join(BASE_DIR, 'gifts')

for d in [RUNNING_DIR, LOGS_DIR, DB_DIR, ASSETS_DIR, STORE_DIR, THUMBS_DIR, 
          MARKET_DIR, ENV_DIR, ENCRYPTED_DIR, TEMP_DIR, GIFTS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

USERS_DB = os.path.join(DB_DIR, 'users.json')
FILES_DB = os.path.join(DB_DIR, 'files.json')
SETTINGS_DB = os.path.join(DB_DIR, 'settings.json')
STORE_DB = os.path.join(DB_DIR, 'store.json')
ADMINS_DB = os.path.join(DB_DIR, 'admins.json')
MARKET_DB = os.path.join(DB_DIR, 'market.json')
SECURITY_DB = os.path.join(DB_DIR, 'security.json')
GIFTS_DB = os.path.join(DB_DIR, 'gifts.json')
STOP_REASONS_DB = os.path.join(DB_DIR, 'stop_reasons.json')
INSTALLED_LIBS_DB = os.path.join(DB_DIR, 'installed_libs.json')
GIFT_CODES_DB = os.path.join(DB_DIR, 'gift_codes.json')

# ─── القفل والمتغيرات العامة ───
db_lock = threading.Lock()
cancel_states = {}
last_bot_messages = {}
active_processes = {}
process_hours = {}
user_notifications = {}
process_resources = {}
paused_bots = set()

RESOURCE_LIMITS = {
    'max_cpu_percent': 80,
    'max_memory_mb': 256,
    'max_disk_usage_mb': 100,
    'max_processes': 20,
    'max_log_size_mb': 5,
    'ram_pause_threshold': 90,
    'ram_resume_threshold': 80
}

# ─── دوال قاعدة البيانات ───
def read_json(path):
    with db_lock:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except:
            return {}

def write_json(path, data):
    with db_lock:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except:
            pass

class DatabaseManager:
    @staticmethod
    def get_users():
        return read_json(USERS_DB)
    @staticmethod
    def save_users(data):
        write_json(USERS_DB, data)
    @staticmethod
    def get_files():
        return read_json(FILES_DB)
    @staticmethod
    def save_files(data):
        write_json(FILES_DB, data)
    @staticmethod
    def get_settings():
        return read_json(SETTINGS_DB)
    @staticmethod
    def save_settings(data):
        write_json(SETTINGS_DB, data)
    @staticmethod
    def get_store():
        return read_json(STORE_DB)
    @staticmethod
    def save_store(data):
        write_json(STORE_DB, data)
    @staticmethod
    def get_admins():
        data = read_json(ADMINS_DB)
        return data.get("admins", [ADMIN_ID])
    @staticmethod
    def save_admins(data):
        write_json(ADMINS_DB, {"admins": data})
    @staticmethod
    def get_market():
        return read_json(MARKET_DB)
    @staticmethod
    def save_market(data):
        write_json(MARKET_DB, data)
    @staticmethod
    def get_security():
        return read_json(SECURITY_DB)
    @staticmethod
    def save_security(data):
        write_json(SECURITY_DB, data)
    @staticmethod
    def get_gifts():
        return read_json(GIFTS_DB)
    @staticmethod
    def save_gifts(data):
        write_json(GIFTS_DB, data)
    @staticmethod
    def get_stop_reasons():
        return read_json(STOP_REASONS_DB)
    @staticmethod
    def save_stop_reasons(data):
        write_json(STOP_REASONS_DB, data)
    @staticmethod
    def get_installed_libs():
        return read_json(INSTALLED_LIBS_DB)
    @staticmethod
    def save_installed_libs(data):
        write_json(INSTALLED_LIBS_DB, data)
    @staticmethod
    def get_gift_codes():
        return read_json(GIFT_CODES_DB)
    @staticmethod
    def save_gift_codes(data):
        write_json(GIFT_CODES_DB, data)

# ─── نظام التشفير ───
class EncryptionManager:
    @staticmethod
    def get_master_key():
        security = DatabaseManager.get_security()
        master_key = security.get('master_key')
        if not master_key:
            master_key = base64.b64encode(get_random_bytes(32)).decode('utf-8')
            security['master_key'] = master_key
            DatabaseManager.save_security(security)
        return base64.b64decode(master_key)

    @staticmethod
    def generate_file_key(fid, user_id):
        security = DatabaseManager.get_security()
        file_keys = security.get('file_keys', {})
        if fid not in file_keys:
            combined = f"{fid}:{user_id}:{ADMIN_ID}:{TOKEN}"
            salt = hashlib.sha256(combined.encode()).digest()[:16]
            master_key = EncryptionManager.get_master_key()
            kdf = hashlib.pbkdf2_hmac('sha256', master_key, salt, 100000, dklen=32)
            file_keys[fid] = {
                'key': base64.b64encode(kdf).decode('utf-8'),
                'salt': base64.b64encode(salt).decode('utf-8'),
                'user_id': user_id
            }
            security['file_keys'] = file_keys
            DatabaseManager.save_security(security)
        return file_keys[fid]

    @staticmethod
    def get_file_key(fid):
        security = DatabaseManager.get_security()
        return security.get('file_keys', {}).get(fid)

    @staticmethod
    def encrypt_content(content, fid, user_id):
        try:
            file_key_info = EncryptionManager.generate_file_key(fid, user_id)
            key = base64.b64decode(file_key_info['key'])
            salt = base64.b64decode(file_key_info['salt'])
            cipher = AES.new(key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(content.encode('utf-8'), AES.block_size))
            encrypted_data = {
                'iv': base64.b64encode(cipher.iv).decode('utf-8'),
                'ciphertext': base64.b64encode(ct_bytes).decode('utf-8'),
                'salt': base64.b64encode(salt).decode('utf-8'),
                'fid': fid,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            return json.dumps(encrypted_data)
        except Exception as e:
            print(f"خطأ تشفير: {e}")
            return None

    @staticmethod
    def decrypt_content(encrypted_json, fid):
        try:
            data = json.loads(encrypted_json)
            file_key_info = EncryptionManager.get_file_key(fid)
            if not file_key_info:
                return None
            key = base64.b64decode(file_key_info['key'])
            iv = base64.b64decode(data['iv'])
            ct = base64.b64decode(data['ciphertext'])
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except Exception as e:
            print(f"خطأ فك تشفير: {e}")
            return None

    @staticmethod
    def save_encrypted_file(fid, content, user_id):
        encrypted_content = EncryptionManager.encrypt_content(content, fid, user_id)
        if encrypted_content:
            encrypted_path = os.path.join(ENCRYPTED_DIR, f"{fid}.enc")
            with open(encrypted_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_content)
            return True
        return False

    @staticmethod
    def load_encrypted_file(fid):
        encrypted_path = os.path.join(ENCRYPTED_DIR, f"{fid}.enc")
        if os.path.exists(encrypted_path):
            with open(encrypted_path, 'r', encoding='utf-8') as f:
                encrypted_content = f.read()
            return EncryptionManager.decrypt_content(encrypted_content, fid)
        return None

# ─── نظام استخراج المكتبات من الكود ───
class SmartInstaller:
    LIBRARY_MAP = {
        'telebot': 'pyTelegramBotAPI', 'telegram': 'python-telegram-bot', 'pyrogram': 'pyrogram',
        'aiogram': 'aiogram', 'requests': 'requests', 'aiohttp': 'aiohttp', 'flask': 'Flask',
        'django': 'Django', 'fastapi': 'fastapi', 'numpy': 'numpy', 'pandas': 'pandas',
        'pillow': 'Pillow', 'pil': 'Pillow', 'opencv': 'opencv-python', 'cv2': 'opencv-python',
        'matplotlib': 'matplotlib', 'sqlalchemy': 'SQLAlchemy', 'pymongo': 'pymongo',
        'redis': 'redis', 'psycopg2': 'psycopg2-binary', 'mysql': 'mysql-connector-python',
        'sqlite3': None, 'json': None, 'os': None, 'sys': None, 're': None, 'time': None,
        'datetime': None, 'random': None, 'string': None, 'hashlib': None, 'base64': None,
        'threading': None, 'subprocess': None, 'math': None, 'typing': None, 'collections': None,
        'itertools': None, 'functools': None, 'pathlib': None, 'inspect': None, 'textwrap': None,
        'html': None, 'urllib': None, 'http': None, 'socket': None, 'asyncio': None, 'logging': None,
        'warnings': None, 'traceback': None, 'copy': None, 'pickle': None, 'csv': None, 'xml': None,
        'html.parser': None, 'uuid': None, 'secrets': None, 'hmac': None, 'bisect': None, 'heapq': None,
        'enum': None, 'dataclasses': None, 'zoneinfo': None, 'calendar': None, 'decimal': None,
        'fractions': None, 'numbers': None, 'statistics': None, 'typing_extensions': 'typing_extensions',
        'pydantic': 'pydantic', 'jinja2': 'Jinja2', 'markupsafe': 'MarkupSafe', 'werkzeug': 'Werkzeug',
        'click': 'click', 'itsdangerous': 'itsdangerous', 'colorama': 'colorama', 'rich': 'rich',
        'typer': 'typer', 'httpx': 'httpx', 'tornado': 'tornado', 'twisted': 'Twisted', 'scrapy': 'Scrapy',
        'beautifulsoup4': 'beautifulsoup4', 'bs4': 'beautifulsoup4', 'lxml': 'lxml', 'selenium': 'selenium',
        'playwright': 'playwright', 'pyppeteer': 'pyppeteer', 'schedule': 'schedule', 'apscheduler': 'APScheduler',
        'celery': 'celery', 'rabbitmq': 'pika', 'pika': 'pika', 'kafka': 'kafka-python',
        'elasticsearch': 'elasticsearch', 'pysftp': 'pysftp', 'paramiko': 'paramiko', 'fabric': 'fabric',
        'ansible': 'ansible', 'docker': 'docker', 'kubernetes': 'kubernetes', 'boto3': 'boto3',
        'botocore': 'botocore', 'google.cloud': 'google-cloud-storage', 'firebase_admin': 'firebase-admin',
        'pyrebase': 'Pyrebase4', 'sendgrid': 'sendgrid', 'twilio': 'twilio', 'stripe': 'stripe',
        'ccxt': 'ccxt', 'yfinance': 'yfinance', 'tensorflow': 'tensorflow', 'torch': 'torch',
        'keras': 'keras', 'sklearn': 'scikit-learn', 'xgboost': 'xgboost', 'lightgbm': 'lightgbm',
        'catboost': 'catboost', 'optuna': 'optuna', 'openai': 'openai', 'anthropic': 'anthropic',
        'gradio': 'gradio', 'streamlit': 'streamlit', 'plotly': 'plotly', 'seaborn': 'seaborn',
        'networkx': 'networkx', 'geopandas': 'geopandas', 'shapely': 'shapely', 'pyproj': 'pyproj',
        'folium': 'folium', 'geopy': 'geopy', 'phonenumbers': 'phonenumbers', 'faker': 'Faker',
        'pytest': 'pytest', 'black': 'black', 'isort': 'isort', 'flake8': 'flake8', 'mypy': 'mypy',
        'cryptography': 'cryptography', 'pynacl': 'PyNaCl', 'bcrypt': 'bcrypt', 'pyjwt': 'PyJWT',
        'authlib': 'Authlib', 'oauthlib': 'oauthlib', 'flask_login': 'Flask-Login', 'uvicorn': 'uvicorn',
        'gunicorn': 'gunicorn', 'sentry_sdk': 'sentry-sdk', 'loguru': 'loguru', 'prometheus_client': 'prometheus-client',
        'influxdb': 'influxdb-client', 'neo4j': 'neo4j', 'boto3': 'boto3', 'google.generativeai': 'google-generativeai',
        'cohere': 'cohere', 'huggingface_hub': 'huggingface-hub', 'transformers': 'transformers',
        'datasets': 'datasets', 'tokenizers': 'tokenizers', 'accelerate': 'accelerate', 'diffusers': 'diffusers',
        'peft': 'peft', 'bitsandbytes': 'bitsandbytes', 'safetensors': 'safetensors', 'onnx': 'onnx',
        'nltk': 'nltk', 'spacy': 'spacy', 'gensim': 'gensim', 'textblob': 'textblob',
        'sentence_transformers': 'sentence-transformers', 'chromadb': 'chromadb', 'faiss': 'faiss-cpu',
        'openai': 'openai', 'gradio': 'gradio', 'jupyter': 'jupyter', 'ipython': 'ipython',
        'notebook': 'notebook', 'jupyterlab': 'jupyterlab', 'ipywidgets': 'ipywidgets', 'qgrid': 'qgrid',
        'dtale': 'dtale', 'sweetviz': 'sweetviz', 'pandas_profiling': 'ydata-profiling',
        'great_expectations': 'great-expectations', 'pandera': 'pandera', 'pydantic_settings': 'pydantic-settings',
        'python-dotenv': 'python-dotenv', 'environs': 'environs', 'dynaconf': 'dynaconf',
        'fire': 'fire', 'docopt': 'docopt', 'invoke': 'invoke', 'scp': 'scp',
        'ftplib': None, 'smtplib': None, 'imaplib': None, 'poplib': None, 'nntplib': None,
        'telnetlib': None, 'socketserver': None, 'http.server': None, 'xmlrpc': None, 'wsgiref': None,
        'cgi': None, 'cgitb': None, 'mmap': None, 'msvcrt': None, 'winreg': None, 'winsound': None,
        'ossaudiodev': None, 'spwd': None, 'crypt': None, 'nis': None, 'pipes': None, 'sunau': None,
        'uu': None, 'xdrlib': None, 'zipapp': None, '_thread': None, 'atexit': None, 'contextlib': None,
        'contextvars': None, 'concurrent': None, 'multiprocessing': None, 'sched': None, 'signal': None,
        'ssl': None, 'stat': None, 'tempfile': None, 'tty': None, 'webbrowser': None, 'gzip': None,
        'bz2': None, 'lzma': None, 'zlib': None, 'binascii': None, 'codecs': None, 'encodings': None,
        'io': None, 'fnmatch': None, 'glob': None, 'linecache': None, 'shutil': None, 'filecmp': None,
        'fileinput': None, 'mailbox': None, 'mimetypes': None, 'netrc': None, 'plistlib': None,
        'tomllib': None, 'configparser': None, 'csv': None, 'pickle': None, 'shelve': None, 'dbm': None,
        'secrets': None, 'quopri': None, 'email': None, 'struct': None, 'argparse': None, 'optparse': None,
        'getopt': None, 'plac': 'plac', 'pysftp': 'pysftp', 'ftplib': None, 'smtplib': None,
        'imaplib': None, 'poplib': None, 'nntplib': None, 'telnetlib': None, 'socketserver': None,
        'http.server': None, 'xmlrpc': None, 'wsgiref': None, 'cgi': None, 'cgitb': None, 'mmap': None,
        'msvcrt': None, 'winreg': None, 'winsound': None, 'ossaudiodev': None, 'spwd': None, 'crypt': None,
        'nis': None, 'pipes': None, 'sunau': None, 'uu': None, 'xdrlib': None, 'zipapp': None,
        '_thread': None, 'atexit': None, 'contextlib': None, 'contextvars': None, 'concurrent': None,
        'multiprocessing': None, 'sched': None, 'signal': None, 'ssl': None, 'stat': None, 'tempfile': None,
        'tty': None, 'webbrowser': None, 'gzip': None, 'bz2': None, 'lzma': None, 'zlib': None,
        'binascii': None, 'codecs': None, 'encodings': None, 'io': None, 'fnmatch': None, 'glob': None,
        'linecache': None, 'shutil': None, 'filecmp': None, 'fileinput': None, 'mailbox': None,
        'mimetypes': None, 'netrc': None, 'plistlib': None, 'tomllib': None, 'configparser': None,
        'csv': None, 'pickle': None, 'shelve': None, 'dbm': None, 'secrets': None, 'quopri': None,
        'email': None, 'struct': None, 'argparse': None, 'optparse': None, 'getopt': None
    }

    @staticmethod
    def extract_imports(code_content):
        libraries = set()
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        lib_name = alias.name.split('.')[0]
                        libraries.add(lib_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        lib_name = node.module.split('.')[0]
                        libraries.add(lib_name)
        except:
            patterns = [
                r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, code_content, re.MULTILINE):
                    libraries.add(match.group(1))
        return libraries

    @staticmethod
    def get_pip_name(lib_name):
        return SmartInstaller.LIBRARY_MAP.get(lib_name.lower(), lib_name)

    @staticmethod
    def install_libraries(code_content, fid=None, notify_chat=None):
        imports = SmartInstaller.extract_imports(code_content)
        installed = DatabaseManager.get_installed_libs()
        results = {'installed': [], 'already': [], 'failed': [], 'skipped': []}
        for lib in imports:
            pip_name = SmartInstaller.get_pip_name(lib)
            if pip_name is None:
                results['skipped'].append(lib)
                continue
            if pip_name in installed and installed[pip_name].get('status') == 'ok':
                results['already'].append(pip_name)
                continue
            try:
                try:
                    importlib.import_module(lib)
                    installed[pip_name] = {'status': 'ok', 'date': datetime.now().isoformat()}
                    DatabaseManager.save_installed_libs(installed)
                    results['already'].append(pip_name)
                    continue
                except ImportError:
                    pass
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet", pip_name],
                    timeout=180,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                installed[pip_name] = {'status': 'ok', 'date': datetime.now().isoformat()}
                DatabaseManager.save_installed_libs(installed)
                results['installed'].append(pip_name)
            except Exception as e:
                results['failed'].append(f"{pip_name}: {str(e)[:50]}")
        return results

# ─── إدارة العمليات ───
class ProcessManager:
    @staticmethod
    def start_script(fid):
        files = DatabaseManager.get_files()
        if fid not in files:
            return False
        file_info = files[fid]
        user_id = file_info.get('user_id')
        if not Utilities.verify_file_access(fid, user_id):
            return False
        encrypted_content = EncryptionManager.load_encrypted_file(fid)
        if not encrypted_content:
            return False
        SmartInstaller.install_libraries(encrypted_content, fid)
        env_dir = os.path.join(ENV_DIR, fid)
        if not os.path.exists(env_dir):
            os.makedirs(env_dir)
        env_file_path = os.path.join(env_dir, f"{fid}.py")
        if fid in active_processes and active_processes[fid].poll() is None:
            return True
        if len(active_processes) >= RESOURCE_LIMITS['max_processes']:
            return False
        if fid in paused_bots:
            return False
        try:
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_content)
        except:
            return False
        log_path = os.path.join(LOGS_DIR, f"{fid}.log")
        try:
            log_file = open(log_path, "a", encoding="utf-8")
            proc = subprocess.Popen(
                [sys.executable, "-u", env_file_path],
                stdout=log_file,
                stderr=log_file,
                stdin=subprocess.PIPE,
                cwd=env_dir,
                start_new_session=True,
                env={**os.environ, "PYTHONPATH": env_dir}
            )
            active_processes[fid] = proc
            process_resources[fid] = {
                'pid': proc.pid,
                'start_time': time.time(),
                'cpu_usage': 0,
                'memory_usage': 0
            }
            return True
        except:
            return False

    @staticmethod
    def stop_script(fid, reason=None):
        stopped = False
        # 1. إيقاف العملية من active_processes
        if fid in active_processes:
            proc = active_processes[fid]
            try:
                # قتل مجموعة العملية
                try:
                    os.killpg(os.getpgid(proc.pid), 9)
                except:
                    pass
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except:
                    pass
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except:
                    pass
                # التأكد بـ psutil
                try:
                    p = psutil.Process(proc.pid)
                    p.kill()
                    p.wait(timeout=2)
                except:
                    pass
            except:
                pass
            finally:
                if fid in active_processes:
                    del active_processes[fid]
                stopped = True

        # 2. إيقاف أي عملية أخرى مرتبطة بالملف
        try:
            env_dir = os.path.join(ENV_DIR, fid)
            env_file = os.path.join(env_dir, f"{fid}.py")
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', []) or []
                    if any(env_file in str(arg) for arg in cmdline):
                        proc.kill()
                        try:
                            proc.wait(timeout=2)
                        except:
                            pass
                except:
                    pass
        except:
            pass

        # 3. تنظيف الموارد
        if fid in process_hours:
            del process_hours[fid]
        if fid in process_resources:
            del process_resources[fid]
        if fid in paused_bots:
            paused_bots.discard(fid)

        # 4. حفظ سبب الإيقاف
        if reason:
            stop_reasons = DatabaseManager.get_stop_reasons()
            stop_reasons[fid] = {
                'reason': reason,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'stopped_by': 'system'
            }
            DatabaseManager.save_stop_reasons(stop_reasons)

        return stopped

    @staticmethod
    def pause_bot(fid, reason="ضغط على موارد السيرفر"):
        if fid not in paused_bots:
            paused_bots.add(fid)
            ProcessManager.stop_script(fid, reason)
            return True
        return False

    @staticmethod
    def resume_bot(fid):
        if fid in paused_bots:
            paused_bots.discard(fid)
            return ProcessManager.start_script(fid)
        return False

    @staticmethod
    def stop_all():
        for fid in list(active_processes.keys()):
            ProcessManager.stop_script(fid)
        paused_bots.clear()
        return True

    @staticmethod
    def write_stdin(fid, cmd):
        if fid in active_processes and active_processes[fid].poll() is None:
            try:
                proc = active_processes[fid]
                if proc.stdin:
                    proc.stdin.write(cmd.encode('utf-8') + b'\n')
                    proc.stdin.flush()
                    return True
            except:
                pass
        return False

    @staticmethod
    def get_resource_usage(fid):
        if fid not in process_resources:
            return None
        try:
            proc = psutil.Process(process_resources[fid]['pid'])
            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_info().rss / (1024 * 1024)
            return {'cpu': cpu, 'memory': mem}
        except:
            return None

    @staticmethod
    def cleanup_file(fid):
        """حذف كل الملفات المرتبطة ببوت نهائياً"""
        ProcessManager.stop_script(fid)
        try:
            encrypted_path = os.path.join(ENCRYPTED_DIR, f"{fid}.enc")
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
        except:
            pass
        try:
            log_path = os.path.join(LOGS_DIR, f"{fid}.log")
            if os.path.exists(log_path):
                os.remove(log_path)
        except:
            pass
        try:
            env_dir = os.path.join(ENV_DIR, fid)
            if os.path.exists(env_dir):
                shutil.rmtree(env_dir, ignore_errors=True)
        except:
            pass
        try:
            security = DatabaseManager.get_security()
            file_keys = security.get('file_keys', {})
            if fid in file_keys:
                del file_keys[fid]
                security['file_keys'] = file_keys
                DatabaseManager.save_security(security)
        except:
            pass
        try:
            stop_reasons = DatabaseManager.get_stop_reasons()
            if fid in stop_reasons:
                del stop_reasons[fid]
                DatabaseManager.save_stop_reasons(stop_reasons)
        except:
            pass

# ─── نظام أكواد الهدايا ───
class GiftCodeManager:
    @staticmethod
    def generate_code(length=12):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def create_code(code, reward_type, reward_value, max_uses=1, expires_days=None):
        codes = DatabaseManager.get_gift_codes()
        if code in codes:
            return False, "الكود موجود بالفعل"
        codes[code] = {
            'reward_type': reward_type,  # 'points', 'vip_days', 'vip_lifetime'
            'reward_value': reward_value,
            'max_uses': max_uses,
            'used_count': 0,
            'used_by': [],
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'expires_at': (datetime.now() + timedelta(days=expires_days)).strftime("%Y-%m-%d %H:%M:%S") if expires_days else None,
            'active': True
        }
        DatabaseManager.save_gift_codes(codes)
        return True, "تم إنشاء الكود"

    @staticmethod
    def redeem_code(code, user_id):
        codes = DatabaseManager.get_gift_codes()
        if code not in codes:
            return False, "❌ الكود غير صالح!"
        c = codes[code]
        if not c.get('active', True):
            return False, "❌ الكود غير نشط!"
        if c['max_uses'] != -1 and c['used_count'] >= c['max_uses']:
            return False, "❌ الكود استُنفذ!"
        if user_id in c['used_by']:
            return False, "❌ لقد استخدمت هذا الكود من قبل!"
        if c.get('expires_at'):
            try:
                exp = datetime.strptime(c['expires_at'], "%Y-%m-%d %H:%M:%S")
                if datetime.now() > exp:
                    return False, "❌ انتهت صلاحية الكود!"
            except:
                pass
        # تطبيق المكافأة
        users = DatabaseManager.get_users()
        if str(user_id) not in users:
            return False, "❌ المستخدم غير موجود!"
        reward_type = c['reward_type']
        reward_value = c['reward_value']
        if reward_type == 'points':
            users[str(user_id)]['points'] = users[str(user_id)].get('points', 0) + reward_value
        elif reward_type == 'vip_days':
            current_exp = users[str(user_id)].get('expiry')
            if current_exp and current_exp not in [None, 'null', 'LIFETIME']:
                try:
                    base = datetime.strptime(current_exp, "%Y-%m-%d %H:%M:%S")
                except:
                    base = datetime.now()
            else:
                base = datetime.now()
            new_exp = base + timedelta(days=reward_value)
            users[str(user_id)]['expiry'] = new_exp.strftime("%Y-%m-%d %H:%M:%S")
        elif reward_type == 'vip_lifetime':
            users[str(user_id)]['expiry'] = 'LIFETIME'
        DatabaseManager.save_users(users)
        # تحديث الكود
        c['used_count'] += 1
        c['used_by'].append(user_id)
        codes[code] = c
        DatabaseManager.save_gift_codes(codes)
        return True, reward_type

    @staticmethod
    def delete_code(code):
        codes = DatabaseManager.get_gift_codes()
        if code in codes:
            del codes[code]
            DatabaseManager.save_gift_codes(codes)
            return True
        return False

# ─── الأدوات المساعدة ───
class Utilities:
    @staticmethod
    def gen_id(length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def get_user_lang(user_id):
        users = DatabaseManager.get_users()
        u = users.get(str(user_id), {})
        return u.get('lang', 'ar')

    @staticmethod
    def get_user_style(user_id):
        users = DatabaseManager.get_users()
        u = users.get(str(user_id), {})
        return u.get('button_style', 'default')

    @staticmethod
    def set_user_lang(user_id, lang):
        users = DatabaseManager.get_users()
        if str(user_id) in users:
            users[str(user_id)]['lang'] = lang
            DatabaseManager.save_users(users)

    @staticmethod
    def set_user_style(user_id, style):
        users = DatabaseManager.get_users()
        if str(user_id) in users:
            users[str(user_id)]['button_style'] = style
            DatabaseManager.save_users(users)

    @staticmethod
    def get_text(user_id, key, **kwargs):
        lang = Utilities.get_user_lang(user_id)
        text_dict = TRANSLATIONS.get(key, {})
        text = text_dict.get(lang, text_dict.get('ar', key))
        if kwargs:
            text = text.format(**kwargs)
        return text

    @staticmethod
    def create_button(text, callback_data, user_id, style_override=None, url=None):
        style = style_override or Utilities.get_user_style(user_id) or 'default'
        if url:
            btn = types.InlineKeyboardButton(text=text, url=url)
        else:
            btn = types.InlineKeyboardButton(text=text, callback_data=callback_data)
        if style != 'default' and hasattr(btn, 'style'):
            btn.style = style
        return btn

    @staticmethod
    def format_border(user_id, title_key, content_key, **kwargs):
        title = Utilities.get_text(user_id, title_key, **kwargs)
        content = Utilities.get_text(user_id, content_key, **kwargs)
        settings = DatabaseManager.get_settings()
        name = settings.get('bot_name', 'بوت الاستضافة')
        return (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━ \n"
            f"┃ ✦ {title}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{content}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"┃ 🤖 <b>{name}</b>\n"
            f"┃ 🔒 نظام آمن • 📡 @REDMOOD\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{HIDDEN_LONG}"
        )

    @staticmethod
    def delete_last_message(chat_id):
        if chat_id in last_bot_messages:
            try:
                bot.delete_message(chat_id, last_bot_messages[chat_id])
            except:
                pass

    @staticmethod
    def save_message(chat_id, msg_id):
        last_bot_messages[chat_id] = msg_id

    @staticmethod
    def send_message(chat_id, user_id, text, markup=None):
        Utilities.delete_last_message(chat_id)
        settings = DatabaseManager.get_settings()
        try:
            if settings.get('bot_image'):
                msg = bot.send_photo(chat_id, settings['bot_image'], caption=text, parse_mode="HTML", reply_markup=markup)
            else:
                msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            Utilities.save_message(chat_id, msg.message_id)
            return msg
        except:
            msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            Utilities.save_message(chat_id, msg.message_id)
            return msg

    @staticmethod
    def edit_message(call, user_id, text, markup):
        try:
            if call.message.content_type == 'photo':
                bot.edit_message_caption(text[:4096], call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
            else:
                bot.edit_message_text(text[:4096], call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
            Utilities.save_message(call.message.chat.id, call.message.message_id)
        except:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            settings = DatabaseManager.get_settings()
            try:
                if settings.get('bot_image'):
                    msg = bot.send_photo(call.message.chat.id, settings['bot_image'], caption=text[:4096], parse_mode="HTML", reply_markup=markup)
                else:
                    msg = bot.send_message(call.message.chat.id, text[:4096], parse_mode="HTML", reply_markup=markup)
                Utilities.save_message(call.message.chat.id, msg.message_id)
            except:
                msg = bot.send_message(call.message.chat.id, text[:4096], parse_mode="HTML", reply_markup=markup)
                Utilities.save_message(call.message.chat.id, msg.message_id)

    @staticmethod
    def delete_messages(chat_id, *msg_ids):
        for msg_id in msg_ids:
            if msg_id:
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass

    @staticmethod
    def is_user_pro(uid):
        if uid == ADMIN_ID or Utilities.is_admin(uid):
            return True
        users = DatabaseManager.get_users()
        u = users.get(str(uid), {})
        expiry = u.get('expiry')
        if not expiry or expiry == 'null':
            return False
        if expiry == 'LIFETIME' or expiry == 0:
            return True
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < exp_date:
                return True
            else:
                u['expiry'] = None
                users[str(uid)] = u
                DatabaseManager.save_users(users)
                return False
        except:
            return False

    @staticmethod
    def check_subscription(user_id):
        if user_id == ADMIN_ID or Utilities.is_admin(user_id):
            return True
        settings = DatabaseManager.get_settings()
        channels = settings.get('channels', [])
        if not channels:
            return True
        try:
            for ch in channels:
                member = bot.get_chat_member(ch["username"], user_id)
                if member.status in ['left', 'kicked']:
                    return False
            return True
        except:
            return True

    @staticmethod
    def is_admin(user_id):
        if user_id == ADMIN_ID:
            return True
        admins = DatabaseManager.get_admins()
        return user_id in admins

    @staticmethod
    def is_main_admin(user_id):
        return user_id == ADMIN_ID

    @staticmethod
    def add_admin(user_id):
        admins = DatabaseManager.get_admins()
        if user_id not in admins:
            admins.append(user_id)
            DatabaseManager.save_admins(admins)
            return True
        return False

    @staticmethod
    def remove_admin(user_id):
        if user_id == ADMIN_ID:
            return False
        admins = DatabaseManager.get_admins()
        if user_id in admins:
            admins.remove(user_id)
            DatabaseManager.save_admins(admins)
            return True
        return False

    @staticmethod
    def get_thumb():
        settings = DatabaseManager.get_settings()
        thumb = settings.get('file_thumb')
        if thumb and os.path.exists(thumb):
            return thumb
        return None

    @staticmethod
    def verify_file_access(fid, user_id):
        files = DatabaseManager.get_files()
        if fid not in files:
            return False
        file_info = files[fid]
        file_user_id = file_info.get('user_id')
        if user_id == ADMIN_ID or Utilities.is_admin(user_id):
            return True
        if file_user_id == user_id:
            return True
        if file_info.get('type') == 'store':
            store = DatabaseManager.get_store()
            if fid in store:
                return True
        return False

    @staticmethod
    def get_logs(fid, lines=40):
        log_path = os.path.join(LOGS_DIR, f"{fid}.log")
        try:
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    last = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    output = "".join(last)
                    safe = escape(output)
                    if len(safe) > 3000:
                        safe = safe[:3000] + "\n..."
                    return f"<pre><code>{safe}</code></pre>"
            return "لا يوجد مخرجات."
        except:
            return "خطأ في قراءة السجلات."

    @staticmethod
    def update_token_in_memory(content, new_token):
        try:
            keywords = ["TOKEN", "bot_token", "api_key", "tok", "TKN", "BOT_TKN", "API_TOKEN"]
            pattern = r"(['\"])\d{8,12}:[a-zA-Z0-9_-]{35,}(['\"])"
            new_content = re.sub(pattern, f"\\1{new_token}\\2", content)
            for kw in keywords:
                kw_pattern = rf"{kw}\s*=\s*(['\"])[^'\"]+(['\"])"
                new_content = re.sub(kw_pattern, f"{kw} = \\1{new_token}\\2", new_content)
            return new_content
        except:
            return None

    @staticmethod
    def check_token(token):
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            res = requests.get(url, timeout=15).json()
            if res.get("ok"):
                return True, res["result"]
            return False, res.get("description")
        except Exception as e:
            return False, str(e)

    @staticmethod
    def auto_fix_code(code):
        fixes = [
            (r'print\s+(\S+)', r'print(\1)'),
            (r'raw_input', 'input'),
            (r'xrange', 'range'),
            (r'\.iteritems\(\)', '.items()'),
            (r'\.itervalues\(\)', '.values()'),
            (r'\.iterkeys\(\)', '.keys()'),
        ]
        for pattern, replacement in fixes:
            code = re.sub(pattern, replacement, code)
        return code

    @staticmethod
    def create_zip(files_list, zip_name):
        zip_path = os.path.join(TEMP_DIR, zip_name)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in files_list:
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
        return zip_path

    @staticmethod
    def set_cancel(uid, state=True):
        cancel_states[uid] = state

    @staticmethod
    def is_cancelled(uid):
        return cancel_states.get(uid, False)

    @staticmethod
    def clear_cancel(uid):
        if uid in cancel_states:
            del cancel_states[uid]

    @staticmethod
    def cleanup_temp_files():
        try:
            for f in os.listdir(TEMP_DIR):
                path = os.path.join(TEMP_DIR, f)
                if os.path.isfile(path):
                    os.remove(path)
        except:
            pass

    @staticmethod
    def cleanup_old_logs():
        try:
            now = time.time()
            for f in os.listdir(LOGS_DIR):
                path = os.path.join(LOGS_DIR, f)
                if os.path.isfile(path):
                    if os.path.getsize(path) > RESOURCE_LIMITS['max_log_size_mb'] * 1024 * 1024:
                        with open(path, 'w') as fp:
                            fp.truncate(0)
                    if now - os.path.getmtime(path) > 7 * 86400:
                        os.remove(path)
        except:
            pass

    @staticmethod
    def extend_file_time(fid, additional_hours, user_id):
        files = DatabaseManager.get_files()
        if fid not in files:
            return False, "الملف غير موجود"
        file_info = files[fid]
        if file_info.get('type') == 'pro':
            return True, "البوت VIP غير محدود"
        users = DatabaseManager.get_users()
        user = users.get(str(user_id), {})
        current_points = user.get('points', 0)
        if current_points < additional_hours:
            return False, f"النقاط غير كافية. مطلوب: {additional_hours}, متوفر: {current_points}"
        users[str(user_id)]['points'] = current_points - additional_hours
        DatabaseManager.save_users(users)
        expires_at = file_info.get('expires_at')
        if expires_at:
            try:
                current_exp = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                new_exp = current_exp + timedelta(hours=additional_hours)
                files[fid]['expires_at'] = new_exp.strftime("%Y-%m-%d %H:%M:%S")
            except:
                new_exp = datetime.now() + timedelta(hours=additional_hours)
                files[fid]['expires_at'] = new_exp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            new_exp = datetime.now() + timedelta(hours=additional_hours)
            files[fid]['expires_at'] = new_exp.strftime("%Y-%m-%d %H:%M:%S")
        DatabaseManager.save_files(files)
        current_hours = process_hours.get(fid, 0)
        process_hours[fid] = current_hours + additional_hours
        return True, f"تم تمديد البوت بـ {additional_hours} ساعة"

# ─── الترجمات (العربية افتراضية) ───
TRANSLATIONS = {
    'welcome': {
        'ar': 'أهلاً {name}! 👋\n\n🏅 الرتبة: {rank}\n💎 النقاط: {points}\n📅 عضو منذ: {date}',
        'en': 'Welcome {name}! 👋\n\n🏅 Rank: {rank}\n💎 Points: {points}\n📅 Member since: {date}'
    },
    'main_menu_title': {'ar': '⚡ القائمة الرئيسية ⚡', 'en': '⚡ Main Menu ⚡'},
    'main_menu_rank': {'ar': '🏅 الرتبة: {rank}', 'en': '🏅 Rank: {rank}'},
    'main_menu_points': {'ar': '💎 النقاط: {points}', 'en': '💎 Points: {points}'},
    'upload': {'ar': '📤 رفع ملف جديد', 'en': '📤 Upload New File'},
    'my_files': {'ar': '📁 ملفاتي', 'en': '📁 My Files'},
    'store': {'ar': '🛒 المتجر', 'en': '🛒 Store'},
    'wallet': {'ar': '💰 المحفظة', 'en': '💰 Wallet'},
    'profile': {'ar': '👤 الملف الشخصي', 'en': '👤 Profile'},
    'install_library': {'ar': '📚 تثبيت مكتبة', 'en': '📚 Install Library'},
    'settings': {'ar': '⚙️ الإعدادات', 'en': '⚙️ Settings'},
    'contact_dev': {'ar': '💬 تواصل مع المطور', 'en': '💬 Contact Developer'},
    'admin_panel': {'ar': '🔐 لوحة الإدارة', 'en': '🔐 Admin Panel'},
    'pro_panel': {'ar': '👑 لوحة Pro', 'en': '👑 Pro Panel'},
    'download_all': {'ar': '📥 تحميل الكل', 'en': '📥 Download All'},
    'auto_fix': {'ar': '🔧 إصلاح تلقائي', 'en': '🔧 Auto Fix'},
    'test_run': {'ar': '🧪 تشغيل تجريبي', 'en': '🧪 Test Run'},
    'sell_store': {'ar': '💰 بيع في المتجر', 'en': '💰 Sell in Store'},
    'back': {'ar': '🔙 رجوع', 'en': '🔙 Back'},
    'cancel': {'ar': '❌ إلغاء', 'en': '❌ Cancel'},
    'bot_locked': {'ar': '🔒 البوت مغلق', 'en': '🔒 Bot Locked'},
    'bot_locked_desc': {'ar': 'الخدمة موقفة مؤقتاً.\nتواصل مع الدعم عبر الزر أدناه.', 'en': 'Service is temporarily paused.\nContact support via the button below.'},
    'subscription_required': {'ar': '📢 اشتراك مطلوب', 'en': '📢 Subscription Required'},
    'subscription_desc': {'ar': 'يرجى الاشتراك في القنوات التالية للمتابعة:', 'en': 'Please join the following channels to continue:'},
    'verify': {'ar': '✅ تحقق', 'en': '✅ Verify'},
    'join': {'ar': '📢 انضم {name}', 'en': '📢 Join {name}'},
    'language_selection': {'ar': '🌐 اختيار اللغة', 'en': '🌐 Select Language'},
    'choose_lang': {'ar': 'يرجى اختيار لغتك المفضلة:', 'en': 'Please choose your preferred language:'},
    'english': {'ar': '🇬🇧 الإنجليزية', 'en': '🇬🇧 English'},
    'arabic': {'ar': '🇸🇦 العربية', 'en': '🇸🇦 Arabic'},
    'settings_title': {'ar': '⚙️ الإعدادات', 'en': '⚙️ Settings'},
    'change_lang': {'ar': '🌐 تغيير اللغة', 'en': '🌐 Change Language'},
    'change_style': {'ar': '🎨 تغيير لون الأزرار', 'en': '🎨 Change Button Color'},
    'style_default': {'ar': '⚪ افتراضي', 'en': '⚪ Default'},
    'style_primary': {'ar': '🔵 أزرق', 'en': '🔵 Blue'},
    'style_success': {'ar': '🟢 أخضر', 'en': '🟢 Green'},
    'style_danger': {'ar': '🔴 أحمر', 'en': '🔴 Red'},
    'style_updated': {'ar': '✅ تم تحديث لون الأزرار.', 'en': '✅ Button color updated.'},
    'lang_updated': {'ar': '✅ تم تحديث اللغة.', 'en': '✅ Language updated.'},
    'wallet_title': {'ar': '💰 المحفظة', 'en': '💰 Wallet'},
    'balance': {'ar': '💎 الرصيد: {balance}', 'en': '💎 Balance: {balance}'},
    'rank': {'ar': '🏅 الرتبة: {rank}', 'en': '🏅 Rank: {rank}'},
    'vip_expiry': {'ar': '⏳ صلاحية VIP: {expiry}', 'en': '⏳ VIP expiry: {expiry}'},
    'points_info': {'ar': '💡 كل نقطة = ساعة استضافة.', 'en': '💡 Each point = 1 hour of hosting.'},
    'daily_bonus': {'ar': '🎁 المكافأة اليومية', 'en': '🎁 Daily Bonus'},
    'referral_link': {'ar': '🔗 رابط الإحالة', 'en': '🔗 Referral Link'},
    'daily_claimed': {'ar': '❌ تم المطالبة اليوم!', 'en': '❌ Already claimed today!'},
    'daily_earned': {'ar': '🎉 لقد حصلت على {points} نقاط!', 'en': '🎉 You earned {points} points!'},
    'referral_text': {'ar': '🔗 رابط الإحالة الخاص بك:\n<code>{link}</code>\n\n💰 تكسب 10 نقاط لكل مستخدم جديد!', 'en': '🔗 Your referral link:\n<code>{link}</code>\n\n💰 You earn 10 points for each new user!'},
    'help_title': {'ar': '❓ المساعدة', 'en': '❓ Help'},
    'help_text': {'ar': '📖 دليل المساعدة\n\n1️⃣ ارفع ملف .py واختر نوع الاستضافة\n2️⃣ الاستضافة المجانية تستهلك نقاط (نقطة لكل ساعة)\n3️⃣ استضافة VIP حتى انتهاء الاشتراك\n4️⃣ احصل على نقاط عبر المكافأة اليومية والإحالات والأكواد\n5️⃣ أدر ملفاتك من قسم "ملفاتي"\n6️⃣ استخدم الطرفية للتفاعل مع البوتات العاملة', 
              'en': '📖 Help Guide\n\n1️⃣ Upload a .py file and choose hosting type\n2️⃣ Free hosting consumes points (1 point per hour)\n3️⃣ VIP hosting until subscription ends\n4️⃣ Earn points via daily bonus, referrals, and codes\n5️⃣ Manage your files from "My Files"\n6️⃣ Use the terminal to interact with running bots'},
    'upload_choice': {'ar': '📤 اختر نوع الاستضافة:', 'en': '📤 Choose hosting type:'},
    'free_host': {'ar': '🆓 مجاني (نقاط)', 'en': '🆓 Free (points)'},
    'vip_host': {'ar': '👑 VIP (حتى انتهاء الاشتراك)', 'en': '👑 VIP (until subscription ends)'},
    'send_file': {'ar': '📎 أرسل ملف .py الخاص بك:', 'en': '📎 Send your .py file:'},
    'invalid_file': {'ar': '❌ يرجى إرسال ملف .py.', 'en': '❌ Please send a .py file.'},
    'set_duration': {'ar': '⏱️ تحديد المدة', 'en': '⏱️ Set Duration'},
    'duration_prompt': {'ar': '📄 الملف: <b>{name}</b>\n\n💎 نقاطك: <code>{points}</code>\n\n⏱️ أدخل عدد الساعات (الحد الأقصى {max}):', 
                   'en': '📄 File: <b>{name}</b>\n\n💎 Your points: <code>{points}</code>\n\n⏱️ Enter number of hours (max {max}):'},
    'invalid_number': {'ar': '❌ يرجى إدخال رقم صحيح.', 'en': '❌ Please enter a valid number.'},
    'min_hour': {'ar': '⚠️ ساعة واحدة على الأقل.', 'en': '⚠️ Minimum 1 hour.'},
    'insufficient_points': {'ar': '❌ المطلوب: {required}\n💎 المتوفر: {available}', 'en': '❌ Required: {required}\n💎 Available: {available}'},
    'file_uploaded': {'ar': '✅ تم رفع الملف.\n\n📄 {name}\n🏷️ {type}\n⏱️ {duration}\n\n⏳ في انتظار الموافقة.', 
                 'en': '✅ File uploaded.\n\n📄 {name}\n🏷️ {type}\n⏱️ {duration}\n\n⏳ Waiting for approval.'},
    'file_accepted': {'ar': '🎉 تم قبول الملف تلقائياً!\n\n📄 {name}\n⏱️ {duration}\n\n🚀 يعمل الآن.', 
                 'en': '🎉 File accepted automatically!\n\n📄 {name}\n⏱️ {duration}\n\n🚀 Now running.'},
    'file_approved': {'ar': '🎉 تمت الموافقة على ملفك!\n\n📄 {name}\n⏱️ {duration}\n\n🚀 يعمل الآن.', 
                 'en': '🎉 Your file has been approved!\n\n📄 {name}\n⏱️ {duration}\n\n🚀 Now running.'},
    'file_rejected': {'ar': '❌ تم رفض ملفك \'{name}\'.', 'en': '❌ Your file \'{name}\' has been rejected.'},
    'my_files_title': {'ar': '📁 ملفاتي', 'en': '📁 My Files'},
    'files_count': {'ar': '📊 الملفات: {count}', 'en': '📊 Files: {count}'},
    'running_count': {'ar': '🟢 يعمل: {count}', 'en': '🟢 Running: {count}'},
    'stopped_count': {'ar': '🔴 متوقف: {count}', 'en': '🔴 Stopped: {count}'},
    'no_files': {'ar': '📭 لا توجد ملفات.', 'en': '📭 No files.'},
    'file_manager': {'ar': '⚙️ إدارة الملف', 'en': '⚙️ File Manager'},
    'file_status': {'ar': '📊 الحالة: {status}', 'en': '📊 Status: {status}'},
    'file_remaining': {'ar': '⏱️ المتبقي: {remaining}', 'en': '⏱️ Remaining: {remaining}'},
    'file_type': {'ar': '🏷️ النوع: {type}', 'en': '🏷️ Type: {type}'},
    'file_created': {'ar': '📅 تاريخ الإنشاء: {created}', 'en': '📅 Created: {created}'},
    'start': {'ar': '🟢 تشغيل', 'en': '🟢 Start'},
    'stop': {'ar': '🔴 إيقاف', 'en': '🔴 Stop'},
    'terminal': {'ar': '💻 الطرفية', 'en': '💻 Terminal'},
    'change_token': {'ar': '🔑 تغيير التوكن', 'en': '🔑 Change Token'},
    'token_info': {'ar': 'ℹ️ معلومات التوكن', 'en': 'ℹ️ Token Info'},
    'delete': {'ar': '🗑️ حذف', 'en': '🗑️ Delete'},
    'confirm_delete': {'ar': '⚠️ هل أنت متأكد من حذف هذا الملف؟', 'en': '⚠️ Are you sure you want to delete this file?'},
    'yes': {'ar': '✅ نعم', 'en': '✅ Yes'},
    'no': {'ar': '❌ لا', 'en': '❌ No'},
    'deleted': {'ar': '🗑️ تم الحذف: {name}', 'en': '🗑️ Deleted: {name}'},
    'terminal_title': {'ar': '💻 الطرفية', 'en': '💻 Terminal'},
    'terminal_output': {'ar': '📄 الملف: {name}\n📊 الحالة: {status}\n\n💻 الطرفية:\n{output}', 
                   'en': '📄 File: {name}\n📊 Status: {status}\n\n💻 Terminal:\n{output}'},
    'refresh': {'ar': '🔄 تحديث', 'en': '🔄 Refresh'},
    'input': {'ar': '⌨️ إدخال', 'en': '⌨️ Input'},
    'input_sent': {'ar': '✅ تم الإرسال: <code>{cmd}</code>', 'en': '✅ Sent: <code>{cmd}</code>'},
    'process_not_running': {'ar': '❌ العملية لا تعمل.', 'en': '❌ Process not running.'},
    'token_updated': {'ar': '✅ تم تحديث التوكن. يرجى إعادة تشغيل الملف.', 'en': '✅ Token updated. Please restart the file.'},
    'token_failed': {'ar': '❌ فشل تحديث التوكن.', 'en': '❌ Failed to update token.'},
    'token_valid': {'ar': '✅ التوكن صالح.', 'en': '✅ Token is valid.'},
    'token_invalid': {'ar': '❌ التوكن غير صالح.', 'en': '❌ Token is invalid.'},
    'no_token': {'ar': '❌ لم يتم العثور على توكن.', 'en': '❌ No token found.'},
    'bot_name': {'ar': '🤖 اسم البوت: {name}', 'en': '🤖 Bot name: {name}'},
    'bot_image': {'ar': '🖼️ صورة البوت: {state}', 'en': '🖼️ Bot image: {state}'},
    'file_thumb': {'ar': '🖼️ الصورة المصغرة: {state}', 'en': '🖼️ File thumbnail: {state}'},
    'auto_approve': {'ar': '✅ الموافقة التلقائية: {state}', 'en': '✅ Auto-approve: {state}'},
    'enabled': {'ar': '🟢 مفعل', 'en': '🟢 Enabled'},
    'disabled': {'ar': '🔴 معطل', 'en': '🔴 Disabled'},
    'change_name': {'ar': '✏️ تغيير الاسم', 'en': '✏️ Change Name'},
    'change_image': {'ar': '🖼️ تغيير الصورة', 'en': '🖼️ Change Image'},
    'remove_image': {'ar': '🗑️ إزالة الصورة', 'en': '🗑️ Remove Image'},
    'add_image': {'ar': '➕ إضافة صورة', 'en': '➕ Add Image'},
    'change_thumb': {'ar': '🖼️ تغيير الصورة المصغرة', 'en': '🖼️ Change Thumbnail'},
    'remove_thumb': {'ar': '🗑️ إزالة الصورة المصغرة', 'en': '🗑️ Remove Thumbnail'},
    'add_thumb': {'ar': '➕ إضافة صورة مصغرة', 'en': '➕ Add Thumbnail'},
    'name_set': {'ar': '✅ تم تعيين الاسم: {name}', 'en': '✅ Name set to: {name}'},
    'image_updated': {'ar': '✅ تم تحديث الصورة.', 'en': '✅ Image updated.'},
    'thumb_updated': {'ar': '✅ تم تحديث الصورة المصغرة.', 'en': '✅ Thumbnail updated.'},
    'admin_panel_title': {'ar': '🔐 لوحة الإدارة', 'en': '🔐 Admin Panel'},
    'admin_stats': {'ar': '👥 المستخدمين: {users}\n📁 الملفات: {files}\n⏳ المعلقة: {pending}\n🟢 النشطة: {active}\n👮 الأدمن: {admins}\n\n🔒 حالة البوت: {state}\n✅ الموافقة التلقائية: {auto}', 
               'en': '👥 Users: {users}\n📁 Files: {files}\n⏳ Pending: {pending}\n🟢 Active: {active}\n👮 Admins: {admins}\n\n🔒 Bot state: {state}\n✅ Auto-approve: {auto}'},
    'unlock': {'ar': '🔓 فتح', 'en': '🔓 Unlock'},
    'lock': {'ar': '🔒 قفل', 'en': '🔒 Lock'},
    'auto_approve_toggle': {'ar': '✅ تفعيل الموافقة التلقائية', 'en': '✅ Enable Auto-approve'},
    'manual_approve': {'ar': '👤 موافقة يدوية', 'en': '👤 Manual approve'},
    'users_list': {'ar': '👥 المستخدمين', 'en': '👥 Users'},
    'admins_list': {'ar': '👮 الأدمن', 'en': '👮 Admins'},
    'store_management': {'ar': '🛒 إدارة المتجر', 'en': '🛒 Store Management'},
    'pending_files': {'ar': '⏳ الملفات المعلقة', 'en': '⏳ Pending Files'},
    'broadcast': {'ar': '📢 إذاعة', 'en': '📢 Broadcast'},
    'channels': {'ar': '📢 القنوات', 'en': '📢 Channels'},
    'all_files': {'ar': '📁 جميع الملفات', 'en': '📁 All Files'},
    'stop_all': {'ar': '🛑 إيقاف الكل', 'en': '🛑 Stop All'},
    'pending_count': {'ar': '⏳ المعلقة: {count}', 'en': '⏳ Pending: {count}'},
    'file_review': {'ar': '👁️ مراجعة', 'en': '👁️ Review'},
    'file_owner': {'ar': '👤 المالك: {owner}', 'en': '👤 Owner: {owner}'},
    'approve': {'ar': '✅ قبول', 'en': '✅ Approve'},
    'reject': {'ar': '❌ رفض', 'en': '❌ Reject'},
    'user_management': {'ar': '⚙️ إدارة المستخدم', 'en': '⚙️ User Management'},
    'user_id': {'ar': '🆔 المعرف: {id}', 'en': '🆔 ID: {id}'},
    'user_username': {'ar': '👤 اسم المستخدم: @{username}', 'en': '👤 Username: @{username}'},
    'user_joined': {'ar': '📅 انضم: {date}', 'en': '📅 Joined: {date}'},
    'user_points': {'ar': '💎 النقاط: {points}', 'en': '💎 Points: {points}'},
    'user_rank': {'ar': '🏅 الرتبة: {rank}', 'en': '🏅 Rank: {rank}'},
    'user_expiry': {'ar': '⏳ صلاحية VIP: {expiry}', 'en': '⏳ VIP expiry: {expiry}'},
    'user_files': {'ar': '📁 الملفات: {files}', 'en': '📁 Files: {files}'},
    'user_status': {'ar': '📊 الحالة: {status}', 'en': '📊 Status: {status}'},
    'active': {'ar': '🟢 نشط', 'en': '🟢 Active'},
    'banned': {'ar': '🔴 محظور', 'en': '🔴 Banned'},
    'ban': {'ar': '🔴 حظر', 'en': '🔴 Ban'},
    'unban': {'ar': '🟢 فك الحظر', 'en': '🟢 Unban'},
    'grant_vip': {'ar': '👑 منح VIP', 'en': '👑 Grant VIP'},
    'remove_vip': {'ar': '❌ إزالة VIP', 'en': '❌ Remove VIP'},
    'charge': {'ar': '💰 شحن', 'en': '💰 Charge'},
    'message_user': {'ar': '💬 رسالة', 'en': '💬 Message'},
    'charge_points': {'ar': '💎 أدخل النقاط للإضافة:', 'en': '💎 Enter points to add:'},
    'charge_success': {'ar': '✅ تم إضافة {amount} نقاط.', 'en': '✅ Added {amount} points.'},
    'message_sent': {'ar': '✅ تم إرسال الرسالة.', 'en': '✅ Message sent.'},
    'grant_vip_prompt': {'ar': '⏳ أدخل عدد الأيام (0 مدى الحياة):', 'en': '⏳ Enter days (0 for lifetime):'},
    'grant_vip_success': {'ar': '👑 تم منح VIP لمدة {duration}.', 'en': '👑 VIP granted for {duration}.'},
    'remove_vip_success': {'ar': '❌ تم إزالة VIP.', 'en': '❌ VIP removed.'},
    'add_admin': {'ar': '➕ إضافة أدمن', 'en': '➕ Add Admin'},
    'add_admin_prompt': {'ar': '🆔 أدخل معرف المستخدم:', 'en': '🆔 Enter the user ID:'},
    'admin_added': {'ar': '✅ تم إضافة الأدمن: {id}', 'en': '✅ Admin added: {id}'},
    'admin_exists': {'ar': '⚠️ المستخدم أدمن بالفعل.', 'en': '⚠️ User is already an admin.'},
    'admin_removed': {'ar': '✅ تم إزالة الأدمن.', 'en': '✅ Admin removed.'},
    'cannot_remove_owner': {'ar': '❌ لا يمكن إزالة المالك الرئيسي!', 'en': '❌ Cannot remove the main owner!'},
    'only_owner': {'ar': '⚠️ فقط المالك الرئيسي يمكنه فعل هذا.', 'en': '⚠️ Only the main owner can do this.'},
    'store_item': {'ar': '📄 الملف: {name}\n💰 السعر: {price}', 'en': '📄 File: {name}\n💰 Price: {price}'},
    'add_store_file': {'ar': '➕ إضافة ملف للمتجر', 'en': '➕ Add Store File'},
    'set_price': {'ar': '💰 تحديد السعر', 'en': '💰 Set Price'},
    'price_prompt': {'ar': '💰 أدخل السعر بالنقاط:', 'en': '💰 Enter price in points:'},
    'store_added': {'ar': '✅ تم الإضافة: {name}\n💰 السعر: {price}', 'en': '✅ Added: {name}\n💰 Price: {price}'},
    'price_updated': {'ar': '✅ تم تحديث السعر إلى {price}.', 'en': '✅ Price updated to {price}.'},
    'store_deleted': {'ar': '🗑️ تم الحذف: {name}', 'en': '🗑️ Deleted: {name}'},
    'broadcast_sending': {'ar': '📢 جاري الإرسال لـ {count} مستخدم...', 'en': '📢 Sending to {count} users...'},
    'broadcast_complete': {'ar': '✅ اكتملت الإذاعة.\n\n✅ نجح: {success}\n❌ فشل: {failed}\n📊 الإجمالي: {total}', 
                      'en': '✅ Broadcast complete.\n\n✅ Successful: {success}\n❌ Failed: {failed}\n📊 Total: {total}'},
    'channels_list': {'ar': '📢 القنوات: {count}', 'en': '📢 Channels: {count}'},
    'add_channel': {'ar': '➕ إضافة قناة', 'en': '➕ Add Channel'},
    'add_channel_prompt': {'ar': '📢 أرسل معرف القناة (مثال: @channel):', 'en': '📢 Send the channel username (e.g., @channel):'},
    'channel_added': {'ar': '✅ تم الإضافة: {name}', 'en': '✅ Added: {name}'},
    'channel_not_found': {'ar': '❌ القناة غير موجودة.', 'en': '❌ Channel not found.'},
    'channel_removed': {'ar': '✅ تم الإزالة: {name}', 'en': '✅ Removed: {name}'},
    'library_install': {'ar': '📚 جاري تثبيت المكتبة: {lib}', 'en': '📚 Installing library: {lib}'},
    'library_installed': {'ar': '✅ تم التثبيت: {lib}', 'en': '✅ Installed: {lib}'},
    'library_timeout': {'ar': '⏱️ انتهت المهلة: {lib}', 'en': '⏱️ Timeout: {lib}'},
    'library_failed': {'ar': '❌ فشل: {lib}', 'en': '❌ Failed: {lib}'},
    'edit_store': {'ar': '✏️ تعديل عنصر المتجر', 'en': '✏️ Edit Store Item'},
    'change_price': {'ar': '💰 تغيير السعر', 'en': '💰 Change Price'},
    'buy': {'ar': '💰 شراء', 'en': '💰 Buy'},
    'buy_confirm_text': {'ar': '📄 الملف: {name}\n💰 السعر: {price}\n💎 رصيدك: <code>{balance}</code>\n\n{status}', 
                    'en': '📄 File: {name}\n💰 Price: {price}\n💎 Your balance: <code>{balance}</code>\n\n{status}'},
    'sufficient': {'ar': '✅ نقاط كافية!', 'en': '✅ Sufficient points!'},
    'insufficient': {'ar': '❌ نقاط غير كافية!', 'en': '❌ Insufficient points!'},
    'purchase_success': {'ar': '🎉 تم الشراء بنجاح!', 'en': '🎉 Purchase successful!'},
    'purchase_failed': {'ar': '❌ فشل الشراء.', 'en': '❌ Purchase failed.'},
    'store_empty': {'ar': '📭 المتجر فارغ.', 'en': '📭 Store is empty.'},
    'test_run_select': {'ar': '📄 اختر ملفاً للتشغيل التجريبي:', 'en': '📄 Select a file to test:'},
    'test_run_success': {'ar': '✅ تم التشغيل التجريبي بنجاح!', 'en': '✅ Test run successful!'},
    'test_run_error': {'ar': '❌ خطأ: {error}', 'en': '❌ Error: {error}'},
    'access_denied': {'ar': '🚫 ممنوع الوصول!', 'en': '🚫 Access denied!'},
    'file_not_found': {'ar': '❌ الملف غير موجود!', 'en': '❌ File not found!'},
    'download_failed': {'ar': '❌ فشل التحميل!', 'en': '❌ Download failed!'},
    'no_files_to_download': {'ar': '📭 لا توجد ملفات للتحميل!', 'en': '📭 No files to download!'},
    'vip_only': {'ar': '👑 VIP فقط!', 'en': '👑 VIP only!'},
    'insufficient_points_short': {'ar': '❌ نقاط غير كافية!', 'en': '❌ Insufficient points!'},
    'file_saved': {'ar': '✅ تم حفظ الملف بنجاح.', 'en': '✅ File saved successfully.'},
    'save_failed': {'ar': '❌ فشل حفظ الملف.', 'en': '❌ Failed to save file.'},
    'new_user_notify': {'ar': '🎉 مستخدم جديد!\n\n👤 الاسم: {name}\n🆔 المعرف: <code>{id}</code>\n👤 اسم المستخدم: {username}\n📅 التاريخ: {date}', 
                   'en': '🎉 New user registered!\n\n👤 Name: {name}\n🆔 ID: <code>{id}</code>\n👤 Username: {username}\n📅 Date: {date}'},
    'user_banned_notify': {'ar': '🔴 لقد تم حظرك.', 'en': '🔴 You have been banned.'},
    'user_unbanned_notify': {'ar': '🟢 تم رفع الحظر عنك.', 'en': '🟢 Your ban has been lifted.'},
    'vip_granted_notify': {'ar': '👑 تم ترقيتك إلى VIP لمدة {duration}.', 'en': '👑 You have been upgraded to VIP for {duration}.'},
    'vip_removed_notify': {'ar': '❌ تم إلغاء صلاحية VIP الخاصة بك.', 'en': '❌ Your VIP status has been removed.'},
    'points_added_notify': {'ar': '💰 تم إضافة <b>{amount}</b> نقاط إلى رصيدك.', 'en': '💰 <b>{amount}</b> points have been added to your balance.'},
    'admin_promoted_notify': {'ar': '👮 لقد تم تعيينك أدمن!', 'en': '👮 You have been made an admin!'},
    'file_upload_notify': {'ar': '📤 رفع ملف جديد\n\n👤 المستخدم: {user}\n🆔 المعرف: <code>{id}</code>\n📄 الملف: {file}\n🏷️ النوع: {type}\n⏱️ المدة: {duration}', 
                      'en': '📤 New file upload\n\n👤 User: {user}\n🆔 ID: <code>{id}</code>\n📄 File: {file}\n🏷️ Type: {type}\n⏱️ Duration: {duration}'},
    'time_expired_notify': {'ar': '⏱️ انتهت مدة البوت \'{name}\'.', 'en': '⏱️ Your bot \'{name}\' has reached its time limit.'},
    'stopped_subscription_notify': {'ar': '🔴 تم إيقاف البوت \'{name}\' بسبب عدم الاشتراك.', 'en': '🔴 Your bot \'{name}\' was stopped due to missing subscription.'},
    'resource_limit_notify': {'ar': '⚠️ تم إيقاف البوت \'{name}\' بسبب تجاوز حدود الموارد.', 'en': '⚠️ Your bot \'{name}\' was stopped due to exceeding resource limits.'},
    'system_usage': {'ar': '📊 استخدام النظام:\n🖥️ CPU: {cpu}%\n💾 الذاكرة: {mem_mb} ميجابايت\n⚙️ العمليات النشطة: {processes}', 
                'en': '📊 System Usage:\n🖥️ CPU: {cpu}%\n💾 Memory: {mem_mb} MB\n⚙️ Active processes: {processes}'},
    'not_subscribed': {'ar': '❌ أنت غير مشترك.', 'en': '❌ You are not subscribed.'},
    'subscribe_first': {'ar': '⚠️ يرجى الاشتراك أولاً.', 'en': '⚠️ Please subscribe first.'},
    'previous': {'ar': '◀️ السابق', 'en': '◀️ Previous'},
    'next': {'ar': '▶️ التالي', 'en': '▶️ Next'},
    'locked': {'ar': '🔒 مقفل', 'en': '🔒 Locked'},
    'unlocked': {'ar': '🔓 مفتوح', 'en': '🔓 Unlocked'},
    'enter_library_name': {'ar': '📚 أدخل اسم المكتبة للتثبيت:', 'en': '📚 Enter the library name to install:'},
    'enter_message': {'ar': '💬 أدخل الرسالة للإرسال:', 'en': '💬 Enter the message to send:'},
    'send_token': {'ar': '🔑 أرسل التوكن الجديد:', 'en': '🔑 Send the new token:'},
    'enter_name': {'ar': '✏️ أدخل اسم البوت الجديد:', 'en': '✏️ Enter the new bot name:'},
    'send_image': {'ar': '🖼️ أرسل صورة:', 'en': '🖼️ Send an image:'},
    'error': {'ar': '❌ خطأ', 'en': '❌ Error'},
    'success': {'ar': '✅ نجاح', 'en': '✅ Success'},
    'invalid_user_id': {'ar': '❌ معرف المستخدم غير صالح.', 'en': '❌ Invalid user ID.'},
    'failed': {'ar': '❌ فشلت العملية.', 'en': '❌ Operation failed.'},
    'invalid_price': {'ar': '❌ سعر غير صالح.', 'en': '❌ Invalid price.'},
    'referral_bonus': {'ar': '🎁 مكافأة الإحالة', 'en': '🎁 Referral Bonus'},
    'approved': {'ar': '✅ تم القبول', 'en': '✅ Approved'},
    'rejected': {'ar': '❌ تم الرفض', 'en': '❌ Rejected'},
    'no_pending': {'ar': '📭 لا توجد ملفات معلقة.', 'en': '📭 No pending files.'},
    'running': {'ar': '🟢 يعمل', 'en': '🟢 Running'},
    'stopped': {'ar': '🔴 متوقف', 'en': '🔴 Stopped'},
    'pending_review': {'ar': '⏳ قيد المراجعة', 'en': '⏳ Pending Review'},
    'accepted': {'ar': '✅ تم القبول', 'en': '✅ Accepted'},
    'file': {'ar': '📄 الملف: {name}', 'en': '📄 File: {name}'},
    'duration': {'ar': '⏱️ المدة: {duration}', 'en': '⏱️ Duration: {duration}'},
    'unbanned': {'ar': '🟢 تم رفع الحظر', 'en': '🟢 Unbanned'},
    'done': {'ar': '✅ تم', 'en': '✅ Done'},
    'downloaded': {'ar': '✅ تم التحميل', 'en': '✅ Downloaded'},
    'started': {'ar': '✅ تم التشغيل', 'en': '✅ Started'},
    'start_failed': {'ar': '❌ فشل التشغيل', 'en': '❌ Failed to start'},
    'all_stopped': {'ar': '🛑 تم إيقاف جميع العمليات.', 'en': '🛑 All processes stopped.'},
    'image_removed': {'ar': '🗑️ تم إزالة الصورة.', 'en': '🗑️ Image removed.'},
    'thumb_removed': {'ar': '🗑️ تم إزالة الصورة المصغرة.', 'en': '🗑️ Thumbnail removed.'},
    'invalid_username': {'ar': '❌ اسم المستخدم غير صالح.', 'en': '❌ Invalid username.'},
    'time_expired': {'ar': '⏱️ انتهى الوقت', 'en': '⏱️ Time Expired'},
    'vip_removed': {'ar': '❌ تم إزالة VIP.', 'en': '❌ VIP removed.'},
    'extend_time': {'ar': '⏱️ تمديد الوقت', 'en': '⏱️ Extend Time'},
    'extend_prompt': {'ar': '⏱️ أدخل عدد الساعات الإضافية:', 'en': '⏱️ Enter additional hours:'},
    'extend_success': {'ar': '✅ {message}', 'en': '✅ {message}'},
    'extend_failed': {'ar': '❌ {message}', 'en': '❌ {message}'},
    'bot_paused': {'ar': '⏸️ البوت متوقف مؤقتاً بسبب ضغط السيرفر.', 'en': '⏸️ Bot paused due to server load.'},
    'bot_resumed': {'ar': '▶️ تم استئناف البوت.', 'en': '▶️ Bot resumed.'},
    'stop_reason': {'ar': '🛑 سبب الإيقاف: {reason}', 'en': '🛑 Stop reason: {reason}'},
    'stopped_by_admin': {'ar': '🛑 تم إيقاف البوت من قبل الإدارة.\n📋 السبب: {reason}', 'en': '🛑 Bot stopped by admin.\n📋 Reason: {reason}'},
    'gifts_title': {'ar': '🎁 نظام الهدايا', 'en': '🎁 Gift System'},
    'send_gift_all': {'ar': '🎁 إرسال هدية للجميع', 'en': '🎁 Send Gift to All'},
    'send_gift_user': {'ar': '🎁 إرسال هدية لمستخدم', 'en': '🎁 Send Gift to User'},
    'gift_points_prompt': {'ar': '💎 أدخل عدد النقاط:', 'en': '💎 Enter points amount:'},
    'gift_sent_all': {'ar': '🎁 تم إرسال {points} نقطة لـ {count} مستخدم!', 'en': '🎁 Sent {points} points to {count} users!'},
    'gift_sent_user': {'ar': '🎁 تم إرسال {points} نقطة للمستخدم!', 'en': '🎁 Sent {points} points to user!'},
    'view_system_usage': {'ar': '📊 عرض استهلاك الموارد', 'en': '📊 View System Usage'},
    'system_usage_current': {'ar': '📊 استهلاك الموارد الحالي:\n\n🖥️ CPU: {cpu}%\n💾 RAM: {ram}% ({ram_mb} MB)\n💾 RAM المستخدم: {used_mb} MB / {total_mb} MB\n⚙️ البوتات النشطة: {active}\n⏸️ البوتات المتوقفة مؤقتاً: {paused}', 
                        'en': '📊 Current System Usage:\n\n🖥️ CPU: {cpu}%\n💾 RAM: {ram}% ({ram_mb} MB)\n💾 RAM Used: {used_mb} MB / {total_mb} MB\n⚙️ Active Bots: {active}\n⏸️ Paused Bots: {paused}'},
    'download_specific': {'ar': '📥 تحميل ملف محدد', 'en': '📥 Download Specific File'},
    'choose_file_download': {'ar': '📄 اختر الملف للتحميل:', 'en': '📄 Choose file to download:'},
    'smart_install': {'ar': '📚 التثبيت الذكي للمكتبات', 'en': '📚 Smart Library Install'},
    'smart_install_results': {'ar': '📚 نتائج التثبيت الذكي:\n\n✅ تم التثبيت: {installed}\n📦 مثبت مسبقاً: {already}\n⏭️ تم التخطي (مدمج): {skipped}\n❌ فشل: {failed}', 
                         'en': '📚 Smart Install Results:\n\n✅ Installed: {installed}\n📦 Already installed: {already}\n⏭️ Skipped (built-in): {skipped}\n❌ Failed: {failed}'},
    'preview_code': {'ar': '👁️ معاينة الكود', 'en': '👁️ Preview Code'},
    'extend_time_btn': {'ar': '⏱️ تمديد الوقت', 'en': '⏱️ Extend Time'},
    'file_extended': {'ar': '✅ تم تمديد الوقت بنجاح!\n⏱️ الوقت الجديد: {hours} ساعة', 'en': '✅ Time extended successfully!\n⏱️ New time: {hours} hours'},
    'stop_bot_admin': {'ar': '🛑 إيقاف البوت (أدمن)', 'en': '🛑 Stop Bot (Admin)'},
    'enter_stop_reason': {'ar': '📋 أدخل سبب الإيقاف:', 'en': '📋 Enter stop reason:'},
    'bot_stopped_admin': {'ar': '🛑 تم إيقاف البوت.\n📋 السبب: {reason}', 'en': '🛑 Bot stopped.\n📋 Reason: {reason}'},
    'user_gift_notify': {'ar': '🎁 لقد تلقيت هدية!\n💎 <b>{points}</b> نقاط من الإدارة.', 'en': '🎁 You received a gift!\n💎 <b>{points}</b> points from admin.'},
    'ram_alert': {'ar': '⚠️ تنبيه! استهلاك الرام وصل إلى {ram}%\n⏸️ تم إيقاف جميع البوتات مؤقتاً.', 'en': '⚠️ Alert! RAM usage reached {ram}%\n⏸️ All bots paused temporarily.'},
    'ram_normal': {'ar': '✅ استهلاك الرام عاد للطبيعي ({ram}%).\n▶️ تم استئناف البوتات.', 'en': '✅ RAM usage back to normal ({ram}%).\n▶️ Bots resumed.'},
    'rules_title': {'ar': '📋 القوانين والشروط', 'en': '📋 Rules & Terms'},
    'rules_text': {'ar': '📋 قوانين استخدام البوت:\n\n'
                      '1️⃣ ممنوع رفع بوتات الاستضافة (Hosting Bots)\n'
                      '2️⃣ ممنوع رفع ملفات تحتوي على محتوى غير قانوني\n'
                      '3️⃣ ممنوع استخدام البوت لأغراض الاختراق أو الاحتيال\n'
                      '4️⃣ ممنوع إساءة استخدام موارد السيرفر\n'
                      '5️⃣ الالتزام بسياسة الاستخدام العادل\n'
                      '6️⃣ الإدارة تحتفظ بحق إيقاف أي بوت دون إشعار مسبق\n'
                      '7️⃣ في حال مخالفة القوانين، سيتم حظر الحساب تلقائياً\n\n'
                      '🛡️ نظام الكشف الآلي يعمل على مراقبة جميع الملفات المرفوعة',
                 'en': '📋 Bot Usage Rules:\n\n'
                      '1️⃣ Hosting bots are strictly prohibited\n'
                      '2️⃣ No illegal content\n'
                      '3️⃣ No hacking or fraud\n'
                      '4️⃣ No server resource abuse\n'
                      '5️⃣ Fair use policy applies\n'
                      '6️⃣ Admin reserves right to stop any bot without notice\n'
                      '7️⃣ Violations result in automatic ban\n\n'
                      '🛡️ Automated detection system monitors all uploads'},
    'view_rules': {'ar': '📋 القوانين', 'en': '📋 Rules'},
    'hosting_detected': {'ar': '🚨 تم رصد محاولة رفع بوت استضافة!', 'en': '🚨 Hosting bot upload detected!'},
    'remaining_time': {'ar': '⏱️ الوقت المتبقي: {remaining}', 'en': '⏱️ Remaining time: {remaining}'},
    'time_expired_short': {'ar': '⏱️ انتهى الوقت', 'en': '⏱️ Time expired'},
    # ─── ترجمات جديدة ───
    'redeem_code': {'ar': '🔑 إدخال كود', 'en': '🔑 Enter Code'},
    'enter_gift_code': {'ar': '🔑 أدخل كود الهدية:', 'en': '🔑 Enter gift code:'},
    'gift_code_redeemed': {'ar': '🎉 تم استبدال الكود بنجاح!\n💰 المكافأة: {reward}', 'en': '🎉 Code redeemed successfully!\n💰 Reward: {reward}'},
    'gift_code_invalid': {'ar': '❌ الكود غير صالح!', 'en': '❌ Invalid code!'},
    'gift_code_used': {'ar': '❌ لقد استخدمت هذا الكود من قبل!', 'en': '❌ You already used this code!'},
    'gift_code_expired': {'ar': '❌ انتهت صلاحية الكود!', 'en': '❌ Code expired!'},
    'gift_codes_admin': {'ar': '🎫 نظام أكواد الهدايا', 'en': '🎫 Gift Code System'},
    'create_code': {'ar': '➕ إنشاء كود جديد', 'en': '➕ Create New Code'},
    'delete_code': {'ar': '🗑️ حذف كود', 'en': '🗑️ Delete Code'},
    'code_created': {'ar': '✅ تم إنشاء الكود: <code>{code}</code>\n🎁 النوع: {type}\n💰 القيمة: {value}\n📊 الاستخدامات: {uses}', 'en': '✅ Code created: <code>{code}</code>\n🎁 Type: {type}\n💰 Value: {value}\n📊 Uses: {uses}'},
    'code_deleted': {'ar': '🗑️ تم حذف الكود.', 'en': '🗑️ Code deleted.'},
    'admin_download_file': {'ar': '📥 تحميل الملف', 'en': '📥 Download File'},
    'file_sent_admin': {'ar': '📄 تم إرسال الملف للأدمن.', 'en': '📄 File sent to admin.'},
    'vip_expired_stop': {'ar': '⏱️ انتهى اشتراك VIP. تم إيقاف البوت.', 'en': '⏱️ VIP subscription expired. Bot stopped.'},
    'vip_duration': {'ar': '⏳ مدة الاشتراك', 'en': '⏳ Subscription Duration'},
    'new_bot_uploaded': {'ar': '📤 بوت جديد مرفوع!\n\n👤 المستخدم: {user}\n🆔 المعرف: <code>{id}</code>\n📄 الملف: {file}\n🏷️ النوع: {type}\n⏱️ المدة: {duration}\n🕐 الوقت: {time}', 'en': '📤 New bot uploaded!\n\n👤 User: {user}\n🆔 ID: <code>{id}</code>\n📄 File: {file}\n🏷️ Type: {type}\n⏱️ Duration: {duration}\n🕐 Time: {time}'},
    'download_single': {'ar': '📥 تحميل', 'en': '📥 Download'},
    'delete_all_files': {'ar': '🗑️ حذف جميع الملفات', 'en': '🗑️ Delete All Files'},
    'delete_all_confirm': {'ar': '⚠️ هل أنت متأكد من حذف جميع الملفات؟\n🔴 هذا الإجراء لا يمكن التراجع عنه!', 'en': '⚠️ Are you sure you want to delete ALL files?\n🔴 This action cannot be undone!'},
    'all_files_deleted': {'ar': '🗑️ تم حذف جميع الملفات بنجاح.', 'en': '🗑️ All files deleted successfully.'},
}

# ─── دوال لوحة المفاتيح ───
def build_main_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'upload'), "nav_upload", uid))
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'my_files'), "nav_files", uid),
        Utilities.create_button(Utilities.get_text(uid, 'store'), "nav_store", uid)
    )
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'wallet'), "nav_wallet", uid),
        Utilities.create_button(Utilities.get_text(uid, 'profile'), "nav_stats", uid)
    )
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'install_library'), "nav_lib", uid),
        Utilities.create_button(Utilities.get_text(uid, 'settings'), "nav_settings", uid)
    )
    if Utilities.is_user_pro(uid):
        kb.row(
            Utilities.create_button(Utilities.get_text(uid, 'pro_panel'), "nav_pro", uid)
        )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'contact_dev'), None, uid, url=f"tg://user?id={ADMIN_ID}"))
    if Utilities.is_admin(uid):
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'admin_panel'), "nav_admin", uid))
    return kb

def build_pro_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'download_all'), "pro_download_all", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'auto_fix'), "pro_auto_fix", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'test_run'), "pro_test_run", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'sell_store'), "pro_sell", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
    return kb

def build_cancel_keyboard(uid, data="cancel"):
    kb = types.InlineKeyboardMarkup()
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'cancel'), data, uid))
    return kb

def build_back_keyboard(uid, data="nav_main"):
    kb = types.InlineKeyboardMarkup()
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), data, uid))
    return kb

def build_language_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(Utilities.create_button("🇸🇦 العربية", "set_lang_ar", uid))
    kb.add(Utilities.create_button("🇬🇧 الإنجليزية", "set_lang_en", uid))
    return kb

def build_style_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'style_default'), "set_style_default", uid, style_override='default'))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'style_primary'), "set_style_primary", uid, style_override='primary'))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'style_success'), "set_style_success", uid, style_override='success'))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'style_danger'), "set_style_danger", uid, style_override='danger'))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_settings", uid))
    return kb

def build_settings_keyboard(uid):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'change_lang'), "nav_change_lang", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'change_style'), "nav_change_style", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'view_rules'), "nav_rules", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
    return kb

# ─── تهيئة قاعدة البيانات ───
def init_database():
    default_channels = [
        {"username": "@PRO_APK_MOOD", "name": "PRO_APK_MOOD"}
    ]
    settings = DatabaseManager.get_settings()
    if 'channels' not in settings:
        settings['channels'] = default_channels
    defaults = {
        "bot_name": "بوت الاستضافة الاحترافي",
        "bot_image": None,
        "file_thumb": None,
        "bot_locked": False,
        "auto_approve": True
    }
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    DatabaseManager.save_settings(settings)
    for path in [USERS_DB, FILES_DB, STORE_DB, MARKET_DB, SECURITY_DB, GIFTS_DB, STOP_REASONS_DB, INSTALLED_LIBS_DB, GIFT_CODES_DB]:
        if not os.path.exists(path):
            write_json(path, {})
    admins = DatabaseManager.get_admins()
    if ADMIN_ID not in admins:
        admins.append(ADMIN_ID)
        DatabaseManager.save_admins(admins)
    security = DatabaseManager.get_security()
    if 'master_key' not in security:
        master_key = base64.b64encode(get_random_bytes(32)).decode('utf-8')
        security['master_key'] = master_key
        security['file_keys'] = {}
        DatabaseManager.save_security(security)

# ─── معالج الأمر /start ───
@bot.message_handler(commands=['start'])
def start_command(msg):
    try:
        uid = msg.from_user.id
        settings = DatabaseManager.get_settings()
        if settings.get('bot_locked', False) and not Utilities.is_admin(uid):
            try:
                bot.delete_message(msg.chat.id, msg.message_id)
            except:
                pass
            Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'bot_locked', 'bot_locked_desc'),
                                   types.InlineKeyboardMarkup().add(Utilities.create_button(Utilities.get_text(uid, 'contact_dev'), None, uid, url=f"tg://user?id={ADMIN_ID}")))
            return
        users = DatabaseManager.get_users()
        Utilities.clear_cancel(uid)
        if str(uid) not in users:
            if len(msg.text.split()) > 1:
                ref = msg.text.split()[1]
                if ref.isdigit() and int(ref) != uid:
                    udb = DatabaseManager.get_users()
                    if str(ref) in udb:
                        udb[str(ref)]['points'] = udb[str(ref)].get('points', 0) + 10
                        DatabaseManager.save_users(udb)
                        try:
                            bot.send_message(int(ref), Utilities.format_border(int(ref), 'referral_bonus', '💰 لقد حصلت على 10 نقاط لإحالة مستخدم جديد!'))
                        except:
                            pass
            users[str(uid)] = {
                'username': msg.from_user.username,
                'first_name': msg.from_user.first_name,
                'last_name': msg.from_user.last_name,
                'points': 10,
                'join_date': str(datetime.now().date()),
                'is_banned': 0,
                'expiry': None,
                'last_daily': None,
                'notifications': True,
                'lang': 'ar',
                'button_style': 'default'
            }
            DatabaseManager.save_users(users)
            user_notifications[uid] = True
            try:
                name = escape(f"{msg.from_user.first_name} {msg.from_user.last_name or ''}")
                uname = f"@{msg.from_user.username}" if msg.from_user.username else "None"
                cap = Utilities.get_text(uid, 'new_user_notify', name=name, id=uid, username=uname, date=datetime.now().strftime('%Y-%m-%d %H:%M'))
                for adm in DatabaseManager.get_admins():
                    try:
                        photos = bot.get_user_profile_photos(uid)
                        if photos.total_count > 0:
                            bot.send_photo(adm, photos.photos[0][-1].file_id, caption=cap, parse_mode="HTML")
                        else:
                            bot.send_message(adm, cap, parse_mode="HTML")
                    except:
                        pass
            except:
                pass
        users = DatabaseManager.get_users()
        if users.get(str(uid), {}).get('is_banned', 0) == 1:
            bot.send_message(msg.chat.id, Utilities.format_border(uid, 'banned', '🔴 لقد تم حظرك.'))
            return
        if not Utilities.check_subscription(uid):
            subscription_required(msg.chat.id, uid)
            return
        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except:
            pass
        u = users.get(str(uid), {})
        if 'lang' not in u:
            lang_text = Utilities.get_text(uid, 'choose_lang')
            Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'language_selection', 'choose_lang'),
                                   build_language_keyboard(uid))
            return
        vip = Utilities.is_user_pro(uid)
        rank = 'VIP' if vip else 'مجاني'
        text = Utilities.get_text(uid, 'welcome', name=escape(msg.from_user.first_name), rank=rank, points=u.get('points', 0), date=u.get('join_date', 'today'))
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'main_menu_title', text), build_main_keyboard(uid))
    except Exception as e:
        print(f"Start error: {e}")

def subscription_required(chat_id, uid):
    settings = DatabaseManager.get_settings()
    channels = settings.get('channels', [])
    if not channels:
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'join', name=ch['name']), f"https://t.me/{ch['username'].replace('@', '')}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'verify'), "check_sub", uid))
    Utilities.send_message(chat_id, uid, Utilities.format_border(uid, 'subscription_required', 'subscription_desc'), kb)

# ─── معالج الأزرار ───
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        uid = call.from_user.id
        cid = call.message.chat.id
        data = call.data
        users = DatabaseManager.get_users()
        settings = DatabaseManager.get_settings()

        if settings.get('bot_locked', False) and not Utilities.is_admin(uid):
            bot.answer_callback_query(call.id, "🔒 البوت مغلق!", show_alert=True)
            Utilities.send_message(cid, uid, Utilities.format_border(uid, 'bot_locked', 'bot_locked_desc'),
                                   types.InlineKeyboardMarkup().add(Utilities.create_button(Utilities.get_text(uid, 'contact_dev'), f"tg://user?id={ADMIN_ID}", uid)))
            return
        if str(uid) in users and users[str(uid)].get('is_banned', 0) == 1:
            bot.answer_callback_query(call.id, "🔴 أنت محظور!", show_alert=True)
            return
        if data == "cancel":
            Utilities.set_cancel(uid, True)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'cancel'))
            u = users.get(str(uid), {})
            vip = Utilities.is_user_pro(uid)
            rank = 'VIP' if vip else 'مجاني'
            text = Utilities.get_text(uid, 'main_menu_rank', rank=rank) + '\n' + Utilities.get_text(uid, 'main_menu_points', points=u.get('points', 0))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'main_menu_title', text), build_main_keyboard(uid))
            return
        if data == "cancel_admin":
            Utilities.set_cancel(uid, True)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'cancel'))
            admin_panel(call, uid)
            return
        if data == "check_sub":
            if Utilities.check_subscription(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'verify'))
                u = users.get(str(uid), {})
                if 'lang' not in u:
                    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'language_selection', 'choose_lang'),
                                          build_language_keyboard(uid))
                    return
                vip = Utilities.is_user_pro(uid)
                rank = 'VIP' if vip else 'مجاني'
                text = Utilities.get_text(uid, 'main_menu_rank', rank=rank) + '\n' + Utilities.get_text(uid, 'main_menu_points', points=u.get('points', 0))
                Utilities.edit_message(call, uid, Utilities.format_border(uid, 'main_menu_title', text), build_main_keyboard(uid))
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'not_subscribed'), show_alert=True)
            return
        if not Utilities.check_subscription(uid) and not Utilities.is_admin(uid):
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'subscribe_first'), show_alert=True)
            return
        Utilities.clear_cancel(uid)

        if data == "set_lang_en":
            Utilities.set_user_lang(uid, 'en')
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'lang_updated'))
            u = users.get(str(uid), {})
            vip = Utilities.is_user_pro(uid)
            rank = 'VIP' if vip else 'Free'
            text = Utilities.get_text(uid, 'welcome', name=escape(call.from_user.first_name), rank=rank, points=u.get('points', 0), date=u.get('join_date', 'today'))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'main_menu_title', text), build_main_keyboard(uid))
            return
        if data == "set_lang_ar":
            Utilities.set_user_lang(uid, 'ar')
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'lang_updated'))
            u = users.get(str(uid), {})
            vip = Utilities.is_user_pro(uid)
            rank = 'VIP' if vip else 'مجاني'
            text = Utilities.get_text(uid, 'welcome', name=escape(call.from_user.first_name), rank=rank, points=u.get('points', 0), date=u.get('join_date', 'today'))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'main_menu_title', text), build_main_keyboard(uid))
            return
        if data.startswith("set_style_"):
            style = data.split("_")[2]
            Utilities.set_user_style(uid, style)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'style_updated'))
            settings_panel(call, uid)
            return

        if data == "nav_main":
            u = users.get(str(uid), {})
            vip = Utilities.is_user_pro(uid)
            rank = 'VIP' if vip else 'مجاني'
            text = Utilities.get_text(uid, 'main_menu_rank', rank=rank) + '\n' + Utilities.get_text(uid, 'main_menu_points', points=u.get('points', 0))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'main_menu_title', text), build_main_keyboard(uid))
        elif data == "nav_settings":
            settings_panel(call, uid)
        elif data == "nav_rules":
            text = Utilities.get_text(uid, 'rules_text')
            kb = types.InlineKeyboardMarkup()
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_settings", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'rules_title', text), kb)
        elif data == "nav_change_lang":
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'language_selection', 'choose_lang'), build_language_keyboard(uid))
        elif data == "nav_change_style":
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'change_style', 'Choose a button color:'), build_style_keyboard(uid))
        elif data == "nav_pro":
            if not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'pro_panel', '👑 لوحة Pro - مميزات حصرية للمشتركين VIP.'), build_pro_keyboard(uid))
        elif data == "pro_download_all":
            if not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            files = DatabaseManager.get_files()
            u_files = {fid: f for fid, f in files.items() if f.get('user_id') == uid and f.get('status') == 'active'}
            if not u_files:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_files'), show_alert=True)
                return
            kb = types.InlineKeyboardMarkup(row_width=1)
            for fid, f in u_files.items():
                kb.add(Utilities.create_button(f"📄 {f.get('file_name', '?')[:30]}", f"dl_specific_{fid}", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'download_all'), "pro_download_all_zip", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_pro", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'download_specific', 'choose_file_download'), kb)
        elif data == "pro_download_all_zip":
            if not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            files = DatabaseManager.get_files()
            u_files = {fid: f for fid, f in files.items() if f.get('user_id') == uid and f.get('status') == 'active'}
            if not u_files:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_files'), show_alert=True)
                return
            decrypted_files = []
            for fid in u_files.keys():
                if Utilities.verify_file_access(fid, uid):
                    content = EncryptionManager.load_encrypted_file(fid)
                    if content:
                        original_name = u_files[fid].get('file_name', f'{fid}.py')
                        temp_path = os.path.join(TEMP_DIR, f"{original_name}")
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        decrypted_files.append((temp_path, original_name))
            if decrypted_files:
                zip_name = f"files_{uid}_{Utilities.gen_id(4)}.zip"
                zip_path = os.path.join(TEMP_DIR, zip_name)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for temp_path, arc_name in decrypted_files:
                        zipf.write(temp_path, arc_name)
                try:
                    with open(zip_path, 'rb') as f:
                        bot.send_document(cid, f, caption="📦 أرشيف ملفاتك")
                    for temp_path, _ in decrypted_files:
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    os.remove(zip_path)
                except:
                    bot.answer_callback_query(call.id, Utilities.get_text(uid, 'download_failed'), show_alert=True)
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_files_to_download'), show_alert=True)
        elif data.startswith("dl_specific_"):
            fid = data.split("_")[2]
            if not Utilities.verify_file_access(fid, uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
                return
            files = DatabaseManager.get_files()
            if fid not in files:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
                return
            content = EncryptionManager.load_encrypted_file(fid)
            if not content:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'download_failed'), show_alert=True)
                return
            try:
                original_name = files[fid].get('file_name', f'{fid}.py')
                temp_path = os.path.join(TEMP_DIR, original_name)
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                thumb = Utilities.get_thumb()
                with open(temp_path, 'rb') as f:
                    if thumb:
                        with open(thumb, 'rb') as t:
                            bot.send_document(cid, f, thumb=t, caption=f"📄 {original_name}", parse_mode="HTML")
                    else:
                        bot.send_document(cid, f, caption=f"📄 {original_name}", parse_mode="HTML")
                os.remove(temp_path)
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'downloaded'))
            except Exception as e:
                print(f"Download error: {e}")
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'download_failed'), show_alert=True)
        elif data == "pro_auto_fix":
            if not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            m = bot.send_message(cid, Utilities.format_border(uid, 'auto_fix', '🔧 أرسل ملف .py لتحليله وإصلاحه:'), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, auto_fix_step, m.message_id, uid)
        elif data == "pro_test_run":
            if not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            files = DatabaseManager.get_files()
            u_files = {fid: f for fid, f in files.items() if f.get('user_id') == uid and f.get('status') == 'active'}
            if not u_files:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_files'), show_alert=True)
                return
            kb = types.InlineKeyboardMarkup(row_width=1)
            for fid, f in u_files.items():
                kb.add(Utilities.create_button(f"📄 {f.get('file_name', '?')[:25]}", f"testrun_{fid}", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_pro", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'test_run', Utilities.get_text(uid, 'test_run_select')), kb)
        elif data.startswith("testrun_"):
            fid = data.split("_")[1]
            if not Utilities.verify_file_access(fid, uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
                return
            content = EncryptionManager.load_encrypted_file(fid)
            if not content:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'), show_alert=True)
                return
            try:
                exec(compile(content, f"test_{fid}", 'exec'), {})
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'test_run_success'))
            except Exception as e:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'test_run_error', error=str(e)[:100]), show_alert=True)
        elif data == "pro_sell":
            if not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            m = bot.send_message(cid, Utilities.format_border(uid, 'sell_store', Utilities.get_text(uid, 'send_file')), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, sell_file_step, m.message_id, uid)
        elif data == "nav_wallet":
            u = users.get(str(uid), {})
            vip = Utilities.is_user_pro(uid)
            exp = "لا يوجد"
            if vip:
                e = u.get('expiry')
                if e == 'LIFETIME' or e == 0:
                    exp = "مدى الحياة"
                elif e:
                    exp = e
            today = str(datetime.now().date())
            can_claim = u.get('last_daily') != today
            text = (Utilities.get_text(uid, 'balance', balance=u.get('points', 0)) + '\n' +
                    Utilities.get_text(uid, 'rank', rank='VIP' if vip else 'مجاني') + '\n' +
                    Utilities.get_text(uid, 'vip_expiry', expiry=exp) + '\n\n' +
                    Utilities.get_text(uid, 'points_info'))
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                Utilities.create_button(Utilities.get_text(uid, 'daily_bonus') + (' ✅' if can_claim else ' ❌'), "daily", uid),
                Utilities.create_button(Utilities.get_text(uid, 'referral_link'), "ref", uid)
            )
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'redeem_code'), "redeem_code", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'wallet_title', text), kb)
        elif data == "redeem_code":
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'redeem_code', Utilities.get_text(uid, 'enter_gift_code')), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, redeem_code_step, m.message_id, uid)
        elif data == "daily":
            u = users.get(str(uid))
            today = str(datetime.now().date())
            if u.get('last_daily') == today:
                return bot.answer_callback_query(call.id, Utilities.get_text(uid, 'daily_claimed'), show_alert=True)
            gift = random.randint(5, 15)
            u['points'] = u.get('points', 0) + gift
            u['last_daily'] = today
            users[str(uid)] = u
            DatabaseManager.save_users(users)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'daily_earned', points=gift), show_alert=True)
            vip = Utilities.is_user_pro(uid)
            text = (Utilities.get_text(uid, 'balance', balance=u.get('points', 0)) + '\n' +
                    Utilities.get_text(uid, 'rank', rank='VIP' if vip else 'مجاني') + '\n' +
                    Utilities.get_text(uid, 'daily_earned', points=gift))
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                Utilities.create_button(Utilities.get_text(uid, 'daily_bonus') + ' ❌', "daily", uid),
                Utilities.create_button(Utilities.get_text(uid, 'referral_link'), "ref", uid)
            )
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'redeem_code'), "redeem_code", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'wallet_title', text), kb)
        elif data == "ref":
            info = bot.get_me()
            link = f"https://t.me/{info.username}?start={uid}"
            text = Utilities.get_text(uid, 'referral_text', link=link)
            kb = types.InlineKeyboardMarkup()
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_wallet", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'referral_link', text), kb)
        elif data == "nav_help":
            text = Utilities.get_text(uid, 'help_text')
            kb = types.InlineKeyboardMarkup()
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'contact_dev'), None, uid, url=f"tg://user?id={ADMIN_ID}"))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'help_title', text), kb)
        elif data == "nav_upload":
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                Utilities.create_button(Utilities.get_text(uid, 'free_host'), "up_free", uid),
                Utilities.create_button(Utilities.get_text(uid, 'vip_host'), "up_pro", uid)
            )
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'upload', Utilities.get_text(uid, 'upload_choice')), kb)
        elif data.startswith("up_"):
            h_type = data.split("_")[1]
            if h_type == "pro" and not Utilities.is_user_pro(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_only'), show_alert=True)
                return
            if h_type == "free":
                u = users.get(str(uid), {})
                if u.get('points', 0) < 1:
                    bot.answer_callback_query(call.id, Utilities.get_text(uid, 'insufficient_points_short'), show_alert=True)
                    return
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'upload', Utilities.get_text(uid, 'send_file')), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, upload_step, h_type, m.message_id, uid)
        elif data == "nav_files":
            files = DatabaseManager.get_files()
            u_files = {fid: f for fid, f in files.items() if f.get('user_id') == uid and f.get('status') == 'active'}
            if not u_files:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_files'), show_alert=True)
                return
            kb = types.InlineKeyboardMarkup(row_width=1)
            for fid, f in u_files.items():
                running = fid in active_processes and active_processes[fid].poll() is None
                icon = "🟢" if running else "🔴"
                ft = "VIP" if f.get('type') == 'pro' else "مجاني"
                kb.add(Utilities.create_button(f"{icon} {ft} {f.get('file_name', '?')[:25]}", f"manage_{fid}", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
            running_count = sum(1 for fid in u_files if fid in active_processes and active_processes[fid].poll() is None)
            text = (Utilities.get_text(uid, 'files_count', count=len(u_files)) + '\n' +
                    Utilities.get_text(uid, 'running_count', count=running_count) + '\n' +
                    Utilities.get_text(uid, 'stopped_count', count=len(u_files) - running_count))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'my_files_title', text), kb)
        elif data.startswith("manage_"):
            file_panel(call, data.split("_")[1], uid)
        elif data.startswith("toggle_"):
            toggle_file(call, data.split("_")[1], uid)
        elif data.startswith("delc_"):
            fid = data.split("_")[1]
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                Utilities.create_button(Utilities.get_text(uid, 'yes'), f"del_{fid}", uid),
                Utilities.create_button(Utilities.get_text(uid, 'no'), f"manage_{fid}", uid)
            )
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'delete', Utilities.get_text(uid, 'confirm_delete')), kb)
        elif data.startswith("del_"):
            delete_file(call, data.split("_")[1], uid)
        elif data.startswith("term_"):
            terminal(call, data.split("_")[1], uid)
        elif data.startswith("rterm_"):
            terminal(call, data.split("_")[1], uid)
        elif data.startswith("inp_"):
            fid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'input', Utilities.get_text(uid, 'input') + ':'), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, input_step, fid, m.message_id, uid)
        elif data.startswith("chtoken_"):
            fid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'change_token', Utilities.get_text(uid, 'send_token')), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, token_step, fid, m.message_id, uid)
        elif data.startswith("tokinfo_"):
            token_info(call, data.split("_")[1], uid)
        elif data.startswith("extend_"):
            fid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'extend_time', Utilities.get_text(uid, 'extend_prompt')), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, extend_step, fid, m.message_id, uid)
        elif data.startswith("preview_"):
            fid = data.split("_")[1]
            preview_code(call, fid, uid)
        elif data == "nav_store":
            store_view(call, uid)
        elif data.startswith("buy_"):
            buy_confirm(call, data.split("_")[1], uid)
        elif data.startswith("ebuy_"):
            buy_execute(call, data.split("_")[1], uid)
        elif data == "nav_lib":
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'install_library', Utilities.get_text(uid, 'enter_library_name')), reply_markup=build_cancel_keyboard(uid))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, library_step, m.message_id, uid)
        elif data == "nav_stats":
            files = DatabaseManager.get_files()
            u = users.get(str(uid), {})
            u_files = [f for f in files.values() if f.get('user_id') == uid and f.get('status') == 'active']
            running = sum(1 for fid, f in files.items() if f.get('user_id') == uid and fid in active_processes and active_processes[fid].poll() is None)
            vip = Utilities.is_user_pro(uid)
            exp = "لا يوجد"
            if vip:
                e = u.get('expiry')
                if e == 'LIFETIME' or e == 0:
                    exp = "مدى الحياة"
                elif e:
                    try:
                        ed = datetime.strptime(e, "%Y-%m-%d %H:%M:%S")
                        rem = ed - datetime.now()
                        exp = f"{rem.days} يوم"
                    except:
                        exp = e
            text = (Utilities.get_text(uid, 'user_id', id=uid) + '\n' +
                    Utilities.get_text(uid, 'user_username', username=u.get('username', 'None')) + '\n' +
                    Utilities.get_text(uid, 'user_joined', date=u.get('join_date', '?')) + '\n\n' +
                    Utilities.get_text(uid, 'rank', rank='VIP' if vip else 'مجاني') + '\n' +
                    Utilities.get_text(uid, 'vip_expiry', expiry=exp) + '\n' +
                    Utilities.get_text(uid, 'balance', balance=u.get('points', 0)) + '\n\n' +
                    Utilities.get_text(uid, 'files_count', count=len(u_files)) + '\n' +
                    Utilities.get_text(uid, 'running_count', count=running))
            kb = types.InlineKeyboardMarkup()
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'wallet'), "nav_wallet", uid))
            kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'profile', text), kb)
        elif data == "nav_admin" and Utilities.is_admin(uid):
            admin_panel(call, uid)
        elif data == "lock_bot" and Utilities.is_admin(uid):
            new_state = not settings.get('bot_locked', False)
            settings['bot_locked'] = new_state
            DatabaseManager.save_settings(settings)
            st = Utilities.get_text(uid, 'locked') if new_state else Utilities.get_text(uid, 'unlocked')
            bot.answer_callback_query(call.id, f"🔒 البوت {st}")
            admin_panel(call, uid)
        elif data == "adm_users" and Utilities.is_admin(uid):
            users_panel(call, uid)
        elif data.startswith("userpage_"):
            page = int(data.split("_")[1])
            users_panel(call, uid, page)
        elif data.startswith("uctrl_") and Utilities.is_admin(uid):
            user_panel(call, data.split("_")[1], uid)
        elif data.startswith("ban_") and Utilities.is_admin(uid):
            ban_toggle(call, data.split("_")[1], uid)
        elif data.startswith("pro_") and Utilities.is_admin(uid):
            tuid = data.split("_")[1]
            if Utilities.is_user_pro(int(tuid)):
                pro_remove(call, tuid, uid)
            else:
                try:
                    bot.delete_message(cid, call.message.message_id)
                except:
                    pass
                m = bot.send_message(cid, Utilities.format_border(uid, 'grant_vip', Utilities.get_text(uid, 'grant_vip_prompt')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
                Utilities.save_message(cid, m.message_id)
                bot.register_next_step_handler(m, pro_grant_step, tuid, m.message_id, uid)
        elif data.startswith("charge_") and Utilities.is_admin(uid):
            tuid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'charge', Utilities.get_text(uid, 'charge_points')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, charge_step, tuid, m.message_id, uid)
        elif data.startswith("msguser_") and Utilities.is_admin(uid):
            tuid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'message_user', Utilities.get_text(uid, 'enter_message')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, message_user_step, tuid, m.message_id, uid)
        elif data == "adm_admins" and Utilities.is_admin(uid):
            admins_panel(call, uid)
        elif data == "add_admin" and Utilities.is_main_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'add_admin', Utilities.get_text(uid, 'add_admin_prompt')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, add_admin_step, m.message_id, uid)
        elif data == "add_admin" and not Utilities.is_main_admin(uid):
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'only_owner'), show_alert=True)
        elif data.startswith("rmadmin_") and Utilities.is_admin(uid):
            aid = int(data.split("_")[1])
            if aid == ADMIN_ID:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'cannot_remove_owner'), show_alert=True)
            elif not Utilities.is_main_admin(uid) and aid != uid:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'only_owner'), show_alert=True)
            elif Utilities.remove_admin(aid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'admin_removed'))
                admins_panel(call, uid)
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'failed'), show_alert=True)
        elif data == "adm_store" and Utilities.is_admin(uid):
            store_panel(call, uid)
        elif data == "add_store" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'add_store_file', Utilities.get_text(uid, 'send_file')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, store_add_step, m.message_id, uid)
        elif data.startswith("estore_"):
            store_edit(call, data.split("_")[1], uid)
        elif data.startswith("sprice_"):
            sid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'set_price', Utilities.get_text(uid, 'price_prompt')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, store_price_step, sid, m.message_id, uid)
        elif data.startswith("delstore_"):
            store_delete(call, data.split("_")[1], uid)
        elif data == "adm_pending" and Utilities.is_admin(uid):
            pending_list(call, uid)
        elif data.startswith("vpend_") and Utilities.is_admin(uid):
            pending_view(call, data.split("_")[1], uid)
        elif data.startswith("approve_") and Utilities.is_admin(uid):
            approve_file(call, data.split("_")[1], uid)
        elif data.startswith("reject_") and Utilities.is_admin(uid):
            reject_file(call, data.split("_")[1], uid)
        elif data == "adm_broadcast" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'broadcast', Utilities.get_text(uid, 'enter_message')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, broadcast_step, m.message_id, uid)
        elif data == "adm_settings" and Utilities.is_admin(uid):
            settings_panel(call, uid)
        elif data == "adm_channels" and Utilities.is_admin(uid):
            channels_panel(call, uid)
        elif data == "add_channel" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'add_channel', Utilities.get_text(uid, 'add_channel_prompt')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, add_channel_step, m.message_id, uid)
        elif data.startswith("delch_") and Utilities.is_admin(uid):
            del_channel(call, int(data.split("_")[1]), uid)
        elif data == "set_img" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'add_image', Utilities.get_text(uid, 'send_image')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, set_image_step, m.message_id, uid)
        elif data == "rm_img" and Utilities.is_admin(uid):
            settings['bot_image'] = None
            DatabaseManager.save_settings(settings)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'image_removed'))
            settings_panel(call, uid)
        elif data == "set_thumb" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'add_thumb', Utilities.get_text(uid, 'send_image')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, set_thumb_step, m.message_id, uid)
        elif data == "rm_thumb" and Utilities.is_admin(uid):
            if settings.get('file_thumb') and os.path.exists(settings.get('file_thumb', '')):
                try:
                    os.remove(settings['file_thumb'])
                except:
                    pass
            settings['file_thumb'] = None
            DatabaseManager.save_settings(settings)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'thumb_removed'))
            settings_panel(call, uid)
        elif data == "set_name" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'change_name', Utilities.get_text(uid, 'enter_name')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, set_name_step, m.message_id, uid)
        elif data == "stop_all" and Utilities.is_admin(uid):
            ProcessManager.stop_all()
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'all_stopped'))
            admin_panel(call, uid)
        elif data == "delete_all_files" and Utilities.is_admin(uid):
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                Utilities.create_button("✅ نعم، احذف الكل", "confirm_delete_all", uid),
                Utilities.create_button("❌ إلغاء", "nav_admin", uid)
            )
            Utilities.edit_message(call, uid, Utilities.format_border(uid, 'delete_all_files', 'delete_all_confirm'), kb)
        elif data == "confirm_delete_all" and Utilities.is_admin(uid):
            ProcessManager.stop_all()
            files = DatabaseManager.get_files()
            for fid in list(files.keys()):
                ProcessManager.cleanup_file(fid)
            security = DatabaseManager.get_security()
            security['file_keys'] = {}
            DatabaseManager.save_security(security)
            DatabaseManager.save_stop_reasons({})
            DatabaseManager.save_files({})
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'all_files_deleted'), show_alert=True)
            admin_panel(call, uid)
        elif data == "toggle_auto" and Utilities.is_admin(uid):
            new_state = not settings.get('auto_approve', True)
            settings['auto_approve'] = new_state
            DatabaseManager.save_settings(settings)
            st = Utilities.get_text(uid, 'enabled') if new_state else Utilities.get_text(uid, 'disabled')
            bot.answer_callback_query(call.id, f"✅ الموافقة التلقائية {st}")
            settings_panel(call, uid)
        elif data == "adm_files" and Utilities.is_admin(uid):
            all_files_panel(call, uid)
        elif data.startswith("afpage_"):
            page = int(data.split("_")[1])
            all_files_panel(call, uid, page)
        elif data.startswith("afile_"):
            fid = data.split("_")[1]
            file_panel_admin(call, fid, uid)
        elif data == "download_all_files" and Utilities.is_admin(uid):
            all_files = DatabaseManager.get_files()
            decrypted_files = []
            for fid in all_files.keys():
                if Utilities.verify_file_access(fid, ADMIN_ID):
                    content = EncryptionManager.load_encrypted_file(fid)
                    if content:
                        original_name = all_files[fid].get('file_name', f'{fid}.py')
                        temp_path = os.path.join(TEMP_DIR, original_name)
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        decrypted_files.append((temp_path, original_name))
            if decrypted_files:
                zip_name = f"all_files_{Utilities.gen_id(4)}.zip"
                zip_path = os.path.join(TEMP_DIR, zip_name)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for temp_path, arc_name in decrypted_files:
                        zipf.write(temp_path, arc_name)
                try:
                    with open(zip_path, 'rb') as f:
                        bot.send_document(cid, f, caption="📦 جميع ملفات البوتات")
                    for temp_path, _ in decrypted_files:
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    os.remove(zip_path)
                except:
                    bot.answer_callback_query(call.id, Utilities.get_text(uid, 'download_failed'), show_alert=True)
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_files_to_download'), show_alert=True)
        elif data == "adm_gifts" and Utilities.is_admin(uid):
            gifts_panel(call, uid)
        elif data == "gift_all" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'gifts_title', Utilities.get_text(uid, 'gift_points_prompt')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, gift_all_step, m.message_id, uid)
        elif data == "gift_user" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'gifts_title', "🆜 أدخل معرف المستخدم ثم النقاط (مثال: 123456789 50):"), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, gift_user_step, m.message_id, uid)
        elif data == "adm_system_usage" and Utilities.is_admin(uid):
            show_system_usage(call, uid)
        elif data.startswith("stopbotadmin_") and Utilities.is_admin(uid):
            fid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'stop_bot_admin', Utilities.get_text(uid, 'enter_stop_reason')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, stop_bot_admin_step, fid, m.message_id, uid)
        elif data.startswith("unstopadmin_") and Utilities.is_admin(uid):
            fid = data.split("_")[1]
            files = DatabaseManager.get_files()
            if fid in files:
                files[fid]['admin_stopped'] = False
                DatabaseManager.save_files(files)
                stop_reasons = DatabaseManager.get_stop_reasons()
                if fid in stop_reasons:
                    del stop_reasons[fid]
                    DatabaseManager.save_stop_reasons(stop_reasons)
                user_id = files[fid]['user_id']
                try:
                    bot.send_message(user_id, Utilities.format_border(user_id, 'success', "✅ تم إلغاء إيقاف البوت من قبل الإدارة. يمكنك الآن تشغيله."))
                except:
                    pass
                bot.answer_callback_query(call.id, "✅ تم إلغاء الإيقاف")
                file_panel_admin(call, fid, uid)
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        elif data.startswith("delfileadmin_") and Utilities.is_admin(uid):
            fid = data.split("_")[1]
            files = DatabaseManager.get_files()
            if fid in files:
                fname = files[fid].get('file_name', '?')
                user_id = files[fid]['user_id']
                ProcessManager.cleanup_file(fid)
                del files[fid]
                DatabaseManager.save_files(files)
                try:
                    bot.send_message(user_id, Utilities.format_border(user_id, 'deleted', f"🗑️ تم حذف ملفك '{fname}' من قبل الإدارة."))
                except:
                    pass
                bot.answer_callback_query(call.id, f"🗑️ تم الحذف: {fname}")
                all_files_panel(call, uid)
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        elif data.startswith("startfileadmin_") and Utilities.is_admin(uid):
            fid = data.split("_")[1]
            files = DatabaseManager.get_files()
            if fid in files:
                if ProcessManager.start_script(fid):
                    bot.answer_callback_query(call.id, "✅ تم التشغيل")
                else:
                    bot.answer_callback_query(call.id, "❌ فشل التشغيل", show_alert=True)
                file_panel_admin(call, fid, uid)
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        elif data.startswith("dl_"):
            # تحميل الملف - متاح فقط للأدمن الآن
            if not Utilities.is_admin(uid):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
                return
            fid = data.split("_")[1]
            download_file(call, fid, uid)
        # ─── نظام أكواد الهدايا ───
        elif data == "adm_gift_codes" and Utilities.is_admin(uid):
            gift_codes_panel(call, uid)
        elif data == "create_gift_code" and Utilities.is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = bot.send_message(cid, Utilities.format_border(uid, 'gift_codes_admin', "🎫 أرسل الكود والنوع والقيمة والاستخدامات (مثال: ABC123 points 50 10):"), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
            Utilities.save_message(cid, m.message_id)
            bot.register_next_step_handler(m, create_gift_code_step, m.message_id, uid)
        elif data.startswith("delgiftcode_") and Utilities.is_admin(uid):
            code = data.split("_", 1)[1]
            if GiftCodeManager.delete_code(code):
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'code_deleted'))
            else:
                bot.answer_callback_query(call.id, Utilities.get_text(uid, 'failed'))
            gift_codes_panel(call, uid)
    except Exception as e:
        print(f"Callback error: {e}")

# ─── دوال اللوحات والمعالجات ───
def settings_panel(call, uid):
    settings = DatabaseManager.get_settings()
    has_img = "✅" if settings.get('bot_image') else "❌"
    has_thumb = "✅" if settings.get('file_thumb') and os.path.exists(settings.get('file_thumb', '')) else "❌"
    auto_approve = "✅" if settings.get('auto_approve', True) else "❌"
    text = (Utilities.get_text(uid, 'bot_name', name=settings.get('bot_name', 'غير محدد')) + '\n' +
            Utilities.get_text(uid, 'bot_image', state=has_img) + '\n' +
            Utilities.get_text(uid, 'file_thumb', state=has_thumb) + '\n' +
            Utilities.get_text(uid, 'auto_approve', state=auto_approve))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'settings_title', text), build_settings_keyboard(uid))

def auto_fix_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.document or not msg.document.file_name.endswith('.py'):
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_file')), build_back_keyboard(uid, "nav_pro"))
        return
    try:
        finfo = bot.get_file(msg.document.file_id)
        file_content = bot.download_file(finfo.file_path).decode('utf-8')
        fixed_content = Utilities.auto_fix_code(file_content)
        fixed_name = f"fixed_{msg.document.file_name}"
        temp_path = os.path.join(TEMP_DIR, fixed_name)
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        with open(temp_path, 'rb') as f:
            bot.send_document(msg.chat.id, f, caption="🔧 الملف المُصلح")
        os.remove(temp_path)
    except Exception as e:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', f"🔧 فشل الإصلاح: {str(e)[:200]}"), build_back_keyboard(uid, "nav_pro"))

def sell_file_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.document or not msg.document.file_name.endswith('.py'):
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_file')), build_back_keyboard(uid, "nav_pro"))
        return
    m = bot.send_message(msg.chat.id, Utilities.format_border(uid, 'set_price', Utilities.get_text(uid, 'price_prompt')), reply_markup=build_cancel_keyboard(uid))
    Utilities.save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, sell_price_step, msg.document, m.message_id, uid)

def sell_price_step(msg, doc, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_price')), build_back_keyboard(uid, "nav_pro"))
        return
    price = int(msg.text.strip())
    market = DatabaseManager.get_market()
    sid = Utilities.gen_id()
    market[sid] = {
        'name': doc.file_name,
        'price': price,
        'seller_id': uid,
        'seller_name': f"{msg.from_user.first_name} {msg.from_user.last_name or ''}",
        'rating': 0,
        'votes': 0,
        'downloads': 0,
        'category': 'عام',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    DatabaseManager.save_market(market)
    finfo = bot.get_file(doc.file_id)
    with open(os.path.join(MARKET_DIR, f"{sid}.py"), 'wb') as f:
        f.write(bot.download_file(finfo.file_path))
    Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', f"✅ تم عرض الملف للبيع!\n📄 {doc.file_name}\n💰 السعر: {price} نقطة"), build_back_keyboard(uid, "nav_pro"))

def store_view(call, uid):
    store = DatabaseManager.get_store()
    if not store:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'store_empty'), show_alert=True)
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for sid, item in store.items():
        kb.add(Utilities.create_button(f"📄 {item['name'][:15]} • {item['price']}نق", f"buy_{sid}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
    users = DatabaseManager.get_users()
    text = Utilities.get_text(uid, 'store') + '\n\n' + Utilities.get_text(uid, 'balance', balance=users.get(str(uid), {}).get('points', 0))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'store', text), kb)

def buy_confirm(call, sid, uid):
    store = DatabaseManager.get_store()
    item = store.get(sid)
    if not item:
        return
    users = DatabaseManager.get_users()
    pts = users.get(str(uid), {}).get('points', 0)
    status = Utilities.get_text(uid, 'sufficient') if pts >= item['price'] else Utilities.get_text(uid, 'insufficient')
    text = Utilities.get_text(uid, 'buy_confirm_text', name=item['name'], price=item['price'], balance=pts, status=status)
    kb = types.InlineKeyboardMarkup(row_width=2)
    if pts >= item['price']:
        kb.add(
            Utilities.create_button(Utilities.get_text(uid, 'buy'), f"ebuy_{sid}", uid),
            Utilities.create_button(Utilities.get_text(uid, 'cancel'), "nav_store", uid)
        )
    else:
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_store", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'buy', text), kb)

def buy_execute(call, sid, uid):
    users = DatabaseManager.get_users()
    store = DatabaseManager.get_store()
    item = store.get(sid)
    if not item:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'), show_alert=True)
        return
    if users.get(str(uid), {}).get('points', 0) < item['price']:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'insufficient_points_short'), show_alert=True)
        return
    users[str(uid)]['points'] -= item['price']
    DatabaseManager.save_users(users)
    path = os.path.join(STORE_DIR, f"{sid}.py")
    try:
        thumb = Utilities.get_thumb()
        with open(path, 'rb') as f:
            if thumb:
                with open(thumb, 'rb') as t:
                    bot.send_document(uid, f, thumb=t, caption=f"✅ تم الشراء: {item['name']}", parse_mode="HTML")
            else:
                bot.send_document(uid, f, caption=f"✅ تم الشراء: {item['name']}", parse_mode="HTML")
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'purchase_success'))
        store_view(call, uid)
    except:
        users[str(uid)]['points'] += item['price']
        DatabaseManager.save_users(users)
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'purchase_failed'), show_alert=True)

def admin_panel(call, uid):
    users = DatabaseManager.get_users()
    files = DatabaseManager.get_files()
    pending = [f for f in files.values() if f.get('status') == 'pending']
    active = sum(1 for fid in active_processes if active_processes[fid].poll() is None)
    settings = DatabaseManager.get_settings()
    locked = settings.get('bot_locked', False)
    auto_approve = settings.get('auto_approve', True)
    state = Utilities.get_text(uid, 'locked') if locked else Utilities.get_text(uid, 'unlocked')
    auto = Utilities.get_text(uid, 'enabled') if auto_approve else Utilities.get_text(uid, 'disabled')
    text = Utilities.get_text(uid, 'admin_stats', users=len(users), files=len(files), pending=len(pending), active=active,
                           admins=len(DatabaseManager.get_admins()), state=state, auto=auto)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'unlock') if locked else Utilities.get_text(uid, 'lock'), "lock_bot", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'auto_approve_toggle') if auto_approve else Utilities.get_text(uid, 'manual_approve'), "toggle_auto", uid))
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'users_list'), "adm_users", uid),
        Utilities.create_button(Utilities.get_text(uid, 'admins_list'), "adm_admins", uid)
    )
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'store_management'), "adm_store", uid),
        Utilities.create_button(Utilities.get_text(uid, 'pending_files') + f" ({len(pending)})", "adm_pending", uid)
    )
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'broadcast'), "adm_broadcast", uid),
        Utilities.create_button(Utilities.get_text(uid, 'channels'), "adm_channels", uid)
    )
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'all_files'), "adm_files", uid),
        Utilities.create_button(Utilities.get_text(uid, 'stop_all'), "stop_all", uid)
    )
    kb.row(
        Utilities.create_button(Utilities.get_text(uid, 'delete_all_files'), "delete_all_files", uid)
    )
    kb.row(
        Utilities.create_button("🎁 " + Utilities.get_text(uid, 'gifts_title'), "adm_gifts", uid),
        Utilities.create_button(Utilities.get_text(uid, 'view_system_usage'), "adm_system_usage", uid)
    )
    kb.row(
        Utilities.create_button("🎫 " + Utilities.get_text(uid, 'gift_codes_admin'), "adm_gift_codes", uid)
    )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'settings'), "adm_settings", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'admin_panel_title', text), kb)

def users_panel(call, uid, page=0):
    users = DatabaseManager.get_users()
    user_ids = list(users.keys())
    items_per_page = 10
    total_pages = (len(user_ids) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_users = user_ids[start_idx:end_idx]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for uid_iter in page_users:
        u = users[uid_iter]
        name = u.get('first_name', 'Unknown')
        kb.add(Utilities.create_button(f"👤 {name[:10]}", f"uctrl_{uid_iter}", uid))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(Utilities.create_button(Utilities.get_text(uid, 'previous'), f"userpage_{page-1}", uid))
    if page < total_pages - 1:
        nav_buttons.append(Utilities.create_button(Utilities.get_text(uid, 'next'), f"userpage_{page+1}", uid))
    if nav_buttons:
        kb.row(*nav_buttons)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    text = f"📄 صفحة {page+1} من {total_pages}\n👥 إجمالي المستخدمين: {len(users)}"
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'users_list', text), kb)

def all_files_panel(call, uid, page=0):
    files = DatabaseManager.get_files()
    file_ids = list(files.keys())
    items_per_page = 10
    total_pages = (len(file_ids) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_files = file_ids[start_idx:end_idx]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for fid in page_files:
        f = files[fid]
        kb.add(Utilities.create_button(f"📄 {f.get('file_name', '?')[:15]}", f"afile_{fid}", uid))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(Utilities.create_button(Utilities.get_text(uid, 'previous'), f"afpage_{page-1}", uid))
    if page < total_pages - 1:
        nav_buttons.append(Utilities.create_button(Utilities.get_text(uid, 'next'), f"afpage_{page+1}", uid))
    if nav_buttons:
        kb.row(*nav_buttons)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'download_all'), "download_all_files", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    text = f"📄 صفحة {page+1} من {total_pages}\n📁 إجمالي الملفات: {len(files)}"
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'all_files', text), kb)

def file_panel_admin(call, fid, uid):
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    f = files[fid]
    content = EncryptionManager.load_encrypted_file(fid)
    preview = "🚫 ممنوع الوصول"
    if content:
        safe = escape(content[:1000])
        if len(safe) > 3000:
            safe = safe[:3000] + "\n..."
        preview = f"<pre><code class='language-python'>{safe}</code></pre>"
    running = fid in active_processes and active_processes[fid].poll() is None
    stop_reasons = DatabaseManager.get_stop_reasons()
    reason_text = ""
    admin_stop_text = ""
    if files[fid].get('admin_stopped', False):
        admin_stop_text = "\n🔴 ⚠️ البوت موقوف من الإدارة"
    if fid in stop_reasons:
        reason_text = f"\n🛑 السبب: {stop_reasons[fid].get('reason', 'غير معروف')}"
    text = (Utilities.get_text(uid, 'file', name=f.get('file_name')) + '\n' +
            Utilities.get_text(uid, 'user_id', id=f.get('user_id')) + '\n' +
            Utilities.get_text(uid, 'file_type', type='VIP' if f.get('type') == 'pro' else 'مجاني') + '\n' +
            Utilities.get_text(uid, 'file_status', status=Utilities.get_text(uid, 'running') if running else Utilities.get_text(uid, 'stopped')) + '\n' +
            Utilities.get_text(uid, 'file_created', created=f.get('created_at')) + reason_text + admin_stop_text + '\n\n👁️ المعاينة:\n' + preview)
    kb = types.InlineKeyboardMarkup(row_width=2)
    if files[fid].get('admin_stopped', False):
        kb.add(Utilities.create_button("✅ إلغاء إيقاف البوت", f"unstopadmin_{fid}", uid))
    else:
        kb.add(Utilities.create_button("🛑 إيقاف + سبب", f"stopbotadmin_{fid}", uid))
    kb.add(Utilities.create_button("🗑️ حذف الملف", f"delfileadmin_{fid}", uid))
    kb.add(Utilities.create_button("🔄 تشغيل البوت", f"startfileadmin_{fid}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'admin_download_file'), f"dl_{fid}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "afpage_0", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'file', text), kb)

def admins_panel(call, uid):
    admins = DatabaseManager.get_admins()
    text = Utilities.get_text(uid, 'admins_list') + f" ({len(admins)}):\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    if Utilities.is_main_admin(uid):
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'add_admin'), "add_admin", uid))
    for aid in admins:
        try:
            user = bot.get_chat(aid)
            name = user.first_name
            owner = "👑" if aid == ADMIN_ID else "👮"
            text += f"{owner} {escape(name)} - <code>{aid}</code>\n"
            if aid != ADMIN_ID and Utilities.is_main_admin(uid):
                kb.add(Utilities.create_button(f"❌ إزالة {name[:10]}", f"rmadmin_{aid}", uid))
        except:
            text += f"👮 <code>{aid}</code>\n"
            if aid != ADMIN_ID and Utilities.is_main_admin(uid):
                kb.add(Utilities.create_button(f"❌ إزالة {aid}", f"rmadmin_{aid}", uid))
    if not Utilities.is_main_admin(uid):
        text += "\n\n" + Utilities.get_text(uid, 'only_owner')
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'admins_list', text), kb)

def add_admin_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not Utilities.is_main_admin(uid):
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'only_owner')), build_back_keyboard(uid, "adm_admins"))
        return
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_user_id')), build_back_keyboard(uid, "adm_admins"))
        return
    new_id = int(msg.text.strip())
    if Utilities.add_admin(new_id):
        try:
            bot.send_message(new_id, Utilities.format_border(new_id, 'admin_promoted_notify', '👮 لقد تم تعيينك أدمن!'))
        except:
            pass
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'admin_added', id=new_id)), build_back_keyboard(uid, "adm_admins"))
    else:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'admin_exists')), build_back_keyboard(uid, "adm_admins"))

def user_panel(call, tuid, uid):
    users = DatabaseManager.get_users()
    u = users.get(str(tuid))
    if not u:
        return
    banned = u.get('is_banned', 0) == 1
    vip = Utilities.is_user_pro(int(tuid))
    exp = "لا يوجد"
    if vip:
        e = u.get('expiry')
        if e == 'LIFETIME' or e == 0:
            exp = "مدى الحياة"
        elif e:
            exp = e
    files = DatabaseManager.get_files()
    u_files = [f for f in files.values() if f.get('user_id') == int(tuid)]
    text = (Utilities.get_text(uid, 'user_id', id=tuid) + '\n' +
            Utilities.get_text(uid, 'user_username', username=u.get('username', 'None')) + '\n' +
            Utilities.get_text(uid, 'user_joined', date=u.get('join_date', '?')) + '\n\n' +
            Utilities.get_text(uid, 'balance', balance=u.get('points', 0)) + '\n' +
            Utilities.get_text(uid, 'rank', rank='VIP' if vip else 'مجاني') + '\n' +
            Utilities.get_text(uid, 'vip_expiry', expiry=exp) + '\n\n' +
            Utilities.get_text(uid, 'files_count', count=len(u_files)) + '\n' +
            Utilities.get_text(uid, 'user_status', status=Utilities.get_text(uid, 'banned') if banned else Utilities.get_text(uid, 'active')))
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'unban') if banned else Utilities.get_text(uid, 'ban'), f"ban_{tuid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'remove_vip') if vip else Utilities.get_text(uid, 'grant_vip'), f"pro_{tuid}", uid)
    )
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'charge'), f"charge_{tuid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'message_user'), f"msguser_{tuid}", uid)
    )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "adm_users", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'user_management', text), kb)

def charge_step(msg, tuid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().lstrip('-').isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_number')), build_back_keyboard(uid, f"uctrl_{tuid}"))
        return
    amount = int(msg.text.strip())
    users = DatabaseManager.get_users()
    if str(tuid) in users:
        users[str(tuid)]['points'] = users[str(tuid)].get('points', 0) + amount
        DatabaseManager.save_users(users)
        try:
            bot.send_message(int(tuid), Utilities.format_border(int(tuid), 'points_added_notify', f"💰 تم إضافة <b>{amount}</b> نقاط إلى رصيدك."))
        except:
            pass
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'charge_success', amount=amount)), build_back_keyboard(uid, f"uctrl_{tuid}"))

def message_user_step(msg, tuid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    try:
        bot.copy_message(int(tuid), msg.chat.id, msg.message_id)
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'message_sent')), build_back_keyboard(uid, f"uctrl_{tuid}"))
    except Exception as e:
        print(f"Message send error: {e}")
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'failed')), build_back_keyboard(uid, f"uctrl_{tuid}"))

def pro_grant_step(msg, tuid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_number')), build_back_keyboard(uid, f"uctrl_{tuid}"))
        return
    days = int(msg.text.strip())
    users = DatabaseManager.get_users()
    if str(tuid) in users:
        if days == 0:
            users[str(tuid)]['expiry'] = 'LIFETIME'
            exp_text = "مدى الحياة"
        else:
            exp_date = datetime.now() + timedelta(days=days)
            users[str(tuid)]['expiry'] = exp_date.strftime("%Y-%m-%d %H:%M:%S")
            exp_text = f"{days} يوم"
        DatabaseManager.save_users(users)
        try:
            bot.send_message(int(tuid), Utilities.format_border(int(tuid), 'vip_granted_notify', f"👑 تم ترقيتك إلى VIP لمدة {exp_text}."))
        except:
            pass
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'grant_vip_success', duration=exp_text)), build_back_keyboard(uid, f"uctrl_{tuid}"))

def ban_toggle(call, tuid, uid):
    users = DatabaseManager.get_users()
    if str(tuid) in users:
        curr = users[str(tuid)].get('is_banned', 0)
        users[str(tuid)]['is_banned'] = 0 if curr == 1 else 1
        DatabaseManager.save_users(users)
        try:
            if users[str(tuid)]['is_banned'] == 1:
                bot.send_message(int(tuid), Utilities.format_border(int(tuid), 'banned', Utilities.get_text(int(tuid), 'user_banned_notify')))
            else:
                bot.send_message(int(tuid), Utilities.format_border(int(tuid), 'unbanned', Utilities.get_text(int(tuid), 'user_unbanned_notify')))
        except:
            pass
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'done'))
        user_panel(call, tuid, uid)

def pro_remove(call, tuid, uid):
    users = DatabaseManager.get_users()
    if str(tuid) in users:
        users[str(tuid)]['expiry'] = None
        DatabaseManager.save_users(users)
        try:
            bot.send_message(int(tuid), Utilities.format_border(int(tuid), 'vip_removed_notify', Utilities.get_text(int(tuid), 'vip_removed_notify')))
        except:
            pass
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'vip_removed'))
        user_panel(call, tuid, uid)

def store_panel(call, uid):
    store = DatabaseManager.get_store()
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'add_store_file'), "add_store", uid))
    for sid, item in store.items():
        kb.add(Utilities.create_button(f"📄 {item['name'][:20]} • {item['price']}نق", f"estore_{sid}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    text = Utilities.get_text(uid, 'store_management') + f": {len(store)}"
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'store_management', text), kb)

def store_add_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.document:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_file')), build_back_keyboard(uid, "adm_store"))
        return
    m = bot.send_message(msg.chat.id, Utilities.format_border(uid, 'set_price', Utilities.get_text(uid, 'price_prompt')), reply_markup=build_cancel_keyboard(uid, "cancel_admin"))
    Utilities.save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, store_price_add_step, msg.document, m.message_id, uid)

def store_price_add_step(msg, doc, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_price')), build_back_keyboard(uid, "adm_store"))
        return
    sid = Utilities.gen_id()
    store = DatabaseManager.get_store()
    store[sid] = {'name': doc.file_name, 'price': int(msg.text.strip())}
    DatabaseManager.save_store(store)
    finfo = bot.get_file(doc.file_id)
    with open(os.path.join(STORE_DIR, f"{sid}.py"), 'wb') as f:
        f.write(bot.download_file(finfo.file_path))
    Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'store_added', name=doc.file_name, price=msg.text)), build_back_keyboard(uid, "adm_store"))

def store_edit(call, sid, uid):
    store = DatabaseManager.get_store()
    item = store.get(sid)
    if not item:
        return
    text = Utilities.get_text(uid, 'store_item', name=item['name'], price=item['price'])
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'change_price'), f"sprice_{sid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'delete'), f"delstore_{sid}", uid)
    )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "adm_store", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'edit_store', text), kb)

def store_price_step(msg, sid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_price')), build_back_keyboard(uid, "adm_store"))
        return
    store = DatabaseManager.get_store()
    if sid in store:
        store[sid]['price'] = int(msg.text.strip())
        DatabaseManager.save_store(store)
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'price_updated', price=msg.text)), build_back_keyboard(uid, "adm_store"))

def store_delete(call, sid, uid):
    store = DatabaseManager.get_store()
    if sid in store:
        name = store[sid]['name']
        try:
            os.remove(os.path.join(STORE_DIR, f"{sid}.py"))
        except:
            pass
        del store[sid]
        DatabaseManager.save_store(store)
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'store_deleted', name=name))
        store_panel(call, uid)

# ─── معالجات الرفع والملفات ───
def upload_step(msg, h_type, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.document or not msg.document.file_name.endswith('.py'):
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_file')), build_back_keyboard(uid, "nav_upload"))
        return
    if h_type == "free":
        users = DatabaseManager.get_users()
        pts = users.get(str(uid), {}).get('points', 0)
        m = bot.send_message(
            msg.chat.id,
            Utilities.format_border(uid, 'set_duration', Utilities.get_text(uid, 'duration_prompt', name=escape(msg.document.file_name), points=pts, max=pts)),
            reply_markup=build_cancel_keyboard(uid)
        )
        Utilities.save_message(msg.chat.id, m.message_id)
        bot.register_next_step_handler(m, hours_step, msg.document, m.message_id, uid)
    else:
        complete_upload(msg.document, uid, h_type, 0, uid)

def hours_step(msg, doc, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_number')), build_back_keyboard(uid, "nav_upload"))
        return
    hours = int(msg.text.strip())
    users = DatabaseManager.get_users()
    pts = users.get(str(uid), {}).get('points', 0)
    if hours < 1:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'min_hour')), build_back_keyboard(uid, "nav_upload"))
        return
    if hours > pts:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'insufficient_points_short', Utilities.get_text(uid, 'insufficient_points', required=hours, available=pts)), build_back_keyboard(uid, "nav_wallet"))
        return
    complete_upload(doc, uid, "free", hours, uid)

def is_hosting_bot(content):
    hosting_keywords = [
        'active_processes', 'process_manager', 'bot_hosting', 'hosting_bot',
        'encrypted_dir', 'running_dir', 'bot_logs', 'bot_environments',
        'EncryptionManager', 'ProcessManager', 'hosting', 'استضافة',
        'infinity_polling', 'telebot.TeleBot', 'pyTelegramBotAPI',
        'DatabaseManager', 'get_files', 'get_users', 'admin_panel'
    ]
    content_lower = content.lower()
    score = 0
    for kw in hosting_keywords:
        if kw.lower() in content_lower:
            score += 1
    return score >= 3

def complete_upload(doc, user_id, h_type, hours, uid):
    fid = Utilities.gen_id()
    finfo = bot.get_file(doc.file_id)
    file_content = bot.download_file(finfo.file_path).decode('utf-8')

    # ─── كشف بوتات الاستضافة ───
    if is_hosting_bot(file_content) and not Utilities.is_admin(user_id):
        warning_text = """🚨 إشعار أمني تلقائي

اكتشف نظام الفحص الآلي لدينا أن الملف الذي قمت برفعه يحتوي على خصائص تتوافق مع بوتات الاستضافة (Hosting Bots)، وهو نوع غير مسموح بتشغيله على هذه المنصة.

📋 الإجراء المطلوب:
يُرجى حذف الملف المخالف أو استبداله بملف آخر متوافق مع سياسة الاستخدام.

⚠️ تنبيه: في حال إعادة رفع نفس النوع من الملفات مرة أخرى، سيتم تعليق حسابك وحظره تلقائيًا دون إشعار مسبق.

🛡️ Security System | Automated Detection & Protection Engine"""
        Utilities.send_message(user_id, uid, warning_text, build_back_keyboard(uid, "nav_upload"))
        for adm in DatabaseManager.get_admins():
            try:
                bot.send_message(adm, f"🚨 محاولة رفع بوت استضافة!\n👤 المستخدم: {user_id}\n📄 الملف: {doc.file_name}")
            except:
                pass
        return

    # ─── التثبيت الذكي للمكتبات ───
    install_results = SmartInstaller.install_libraries(file_content, fid)

    if not EncryptionManager.save_encrypted_file(fid, file_content, user_id):
        Utilities.send_message(user_id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'save_failed')), build_back_keyboard(uid))
        return

    now = datetime.now()
    files = DatabaseManager.get_files()
    files[fid] = {
        'user_id': user_id,
        'file_name': doc.file_name,
        'type': h_type,
        'status': 'active',
        'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
        'hours': hours,
        'admin_stopped': False,
        'started_at': now.strftime("%Y-%m-%d %H:%M:%S"),
        'expires_at': None
    }

    if h_type == 'free' and hours > 0:
        users = DatabaseManager.get_users()
        if str(user_id) in users:
            users[str(user_id)]['points'] -= hours
            DatabaseManager.save_users(users)
            expires = now + timedelta(hours=hours)
            files[fid]['expires_at'] = expires.strftime("%Y-%m-%d %H:%M:%S")
            process_hours[fid] = hours

    DatabaseManager.save_files(files)
    ProcessManager.start_script(fid)

    duration = str(hours) + ' ساعة' if h_type == 'free' else 'حتى انتهاء الاشتراك'
    text = Utilities.get_text(uid, 'file_accepted', name=doc.file_name, duration=duration)
    if install_results:
        installed = ", ".join(install_results['installed']) if install_results['installed'] else "لا يوجد"
        text += f"\n\n📚 المكتبات المثبتة: {installed}"
    Utilities.send_message(user_id, uid, Utilities.format_border(uid, 'accepted', text), build_back_keyboard(uid))

    # ─── إرسال الملف للأدمن مباشرةً ───
    try:
        user = bot.get_chat(user_id)
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        detailed_notify = Utilities.get_text(uid, 'new_bot_uploaded', 
            user=escape(user.first_name),
            id=user_id,
            file=doc.file_name,
            type='VIP' if h_type == 'pro' else 'مجاني',
            duration=str(hours) + ' ساعة' if h_type == 'free' else 'حتى انتهاء الاشتراك',
            time=now_time)

        # إرسال الملف كمستند للأدمن
        temp_path = os.path.join(TEMP_DIR, f"admin_{fid}_{doc.file_name}")
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(file_content)

        for adm in DatabaseManager.get_admins():
            try:
                bot.send_message(adm, detailed_notify, parse_mode="HTML")
                with open(temp_path, 'rb') as f:
                    bot.send_document(adm, f, caption=f"📄 ملف البوت: {doc.file_name}\n🆔 FID: {fid}")
                # أزرار تحكم سريعة
                kb = types.InlineKeyboardMarkup(row_width=2)
                kb.add(
                    types.InlineKeyboardButton("👁️ مراجعة", callback_data=f"vpend_{fid}"),
                    types.InlineKeyboardButton("🗑️ حذف", callback_data=f"delfileadmin_{fid}")
                )
                bot.send_message(adm, f"⚡ إجراء سريع للملف {fid}:", reply_markup=kb)
            except Exception as e:
                print(f"Admin notify error: {e}")
        try:
            os.remove(temp_path)
        except:
            pass
    except Exception as e:
        print(f"Upload notify error: {e}")

def pending_list(call, uid):
    files = DatabaseManager.get_files()
    pending = {fid: f for fid, f in files.items() if f.get('status') == 'pending'}
    if not pending:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_pending'), show_alert=True)
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for fid, f in pending.items():
        ft = "VIP" if f.get('type') == 'pro' else "مجاني"
        kb.add(Utilities.create_button(f"{ft} {f.get('file_name', '?')[:25]}", f"vpend_{fid}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    text = Utilities.get_text(uid, 'pending_files') + f": {len(pending)}"
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'pending_files', text), kb)

def pending_view(call, fid, uid):
    files = DatabaseManager.get_files()
    f = files.get(fid)
    if not f:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    content = EncryptionManager.load_encrypted_file(fid)
    preview = "❌ تعذر قراءة الملف"
    if content:
        safe = escape(content[:1000])
        if len(safe) > 3000:
            safe = safe[:3000] + "\n..."
        preview = f"<pre><code class='language-python'>{safe}</code></pre>"
    try:
        uinfo = bot.get_chat(f['user_id'])
        utext = f"{escape(uinfo.first_name)} (@{uinfo.username if uinfo.username else 'None'})"
    except:
        utext = f"🆔: {f['user_id']}"
    text = (Utilities.get_text(uid, 'file', name=f.get('file_name')) + '\n' +
            Utilities.get_text(uid, 'file_owner', owner=utext) + '\n' +
            Utilities.get_text(uid, 'user_id', id=f.get('user_id')) + '\n' +
            Utilities.get_text(uid, 'file_type', type='VIP' if f.get('type') == 'pro' else 'مجاني') + '\n' +
            (Utilities.get_text(uid, 'duration', duration=str(f.get('hours', 0)) + ' ساعة') if f.get('type') == 'free' else '') + '\n' +
            Utilities.get_text(uid, 'file_created', created=f.get('created_at')) + '\n\n👁️ المعاينة:\n' + preview)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'approve'), f"approve_{fid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'reject'), f"reject_{fid}", uid)
    )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "adm_pending", uid))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    m = bot.send_message(call.message.chat.id, Utilities.format_border(uid, 'file_review', text[:4000]), parse_mode="HTML", reply_markup=kb)
    Utilities.save_message(call.message.chat.id, m.message_id)

def approve_file(call, fid, uid):
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    now = datetime.now()
    files[fid]['status'] = 'active'
    files[fid]['started_at'] = now.strftime("%Y-%m-%d %H:%M:%S")
    h_type = files[fid].get('type')
    hours = files[fid].get('hours', 0)
    user_id = files[fid]['user_id']
    if h_type == 'free' and hours > 0:
        users = DatabaseManager.get_users()
        if str(user_id) in users:
            users[str(user_id)]['points'] -= hours
            DatabaseManager.save_users(users)
            expires = now + timedelta(hours=hours)
            files[fid]['expires_at'] = expires.strftime("%Y-%m-%d %H:%M:%S")
            process_hours[fid] = hours
    DatabaseManager.save_files(files)
    ProcessManager.start_script(fid)
    try:
        duration = str(hours) + ' ساعة' if h_type == 'free' else 'حتى انتهاء الاشتراك'
        text = Utilities.get_text(user_id, 'file_approved', name=files[fid]['file_name'], duration=duration)
        bot.send_message(user_id, Utilities.format_border(user_id, 'approved', text))
    except:
        pass
    bot.answer_callback_query(call.id, Utilities.get_text(uid, 'approved'))
    pending_list(call, uid)

def reject_file(call, fid, uid):
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    user_id = files[fid]['user_id']
    fname = files[fid]['file_name']
    ProcessManager.cleanup_file(fid)
    del files[fid]
    DatabaseManager.save_files(files)
    try:
        bot.send_message(user_id, Utilities.format_border(user_id, 'rejected', Utilities.get_text(user_id, 'file_rejected', name=fname)))
    except:
        pass
    bot.answer_callback_query(call.id, Utilities.get_text(uid, 'rejected'))
    pending_list(call, uid)

def file_panel(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    f = files[fid]
    content = EncryptionManager.load_encrypted_file(fid)
    preview = "❌ تعذر قراءة الملف"
    if content:
        safe = escape(content[:1000])
        if len(safe) > 3000:
            safe = safe[:3000] + "\n..."
        preview = f"<pre><code class='language-python'>{safe}</code></pre>"
    running = fid in active_processes and active_processes[fid].poll() is None
    hrs = "غير محدود"
    if f.get('type') == 'free':
        expires_at = f.get('expires_at')
        if expires_at:
            try:
                exp_time = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                remaining = exp_time - datetime.now()
                if remaining.total_seconds() > 0:
                    hrs = f"{remaining.days} يوم {remaining.seconds // 3600} ساعة"
                else:
                    hrs = Utilities.get_text(uid, 'time_expired_short')
            except:
                hrs = "غير معروف"
        elif fid in process_hours:
            hrs = f"{process_hours[fid]} ساعة"

    stop_reasons = DatabaseManager.get_stop_reasons()
    reason_text = ""
    admin_stop_text = ""
    if files[fid].get('admin_stopped', False):
        admin_stop_text = "\n🔴 ⚠️ البوت موقوف من الإدارة"
    if fid in stop_reasons:
        reason_text = f"\n🛑 السبب: {stop_reasons[fid].get('reason', 'غير معروف')}"

    text = (Utilities.get_text(uid, 'file', name=f.get('file_name')) + '\n' +
            Utilities.get_text(uid, 'file_type', type='VIP' if f.get('type') == 'pro' else 'مجاني') + '\n' +
            Utilities.get_text(uid, 'file_status', status=Utilities.get_text(uid, 'running') if running else Utilities.get_text(uid, 'stopped')) + '\n' +
            Utilities.get_text(uid, 'file_remaining', remaining=hrs) + '\n' +
            Utilities.get_text(uid, 'file_created', created=f.get('created_at')) + reason_text + admin_stop_text + '\n\n👁️ المعاينة:\n' + preview)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'stop') if running else Utilities.get_text(uid, 'start'), f"toggle_{fid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'terminal'), f"term_{fid}", uid)
    )
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'change_token'), f"chtoken_{fid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'token_info'), f"tokinfo_{fid}", uid)
    )
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'delete'), f"delc_{fid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'preview_code'), f"preview_{fid}", uid)
    )
    if f.get('type') == 'free':
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'extend_time_btn'), f"extend_{fid}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_files", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'file_manager', text), kb)

def toggle_file(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    if files[fid].get('admin_stopped', False) and not Utilities.is_admin(uid):
        stop_reasons = DatabaseManager.get_stop_reasons()
        reason = stop_reasons.get(fid, {}).get('reason', 'غير معروف')
        bot.answer_callback_query(call.id, f"🛑 البوت موقوف من الإدارة!\n📋 السبب: {reason}", show_alert=True)
        return
    running = fid in active_processes and active_processes[fid].poll() is None
    if running:
        ProcessManager.stop_script(fid)
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'stopped'))
    else:
        if ProcessManager.start_script(fid):
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'started'))
        else:
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'start_failed'), show_alert=True)
    file_panel(call, fid, uid)

def delete_file(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    files = DatabaseManager.get_files()
    if fid in files:
        fname = files[fid].get('file_name', '?')
        ProcessManager.cleanup_file(fid)
        del files[fid]
        DatabaseManager.save_files(files)
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'deleted', name=fname))
    u_files = {fid: f for fid, f in files.items() if f.get('user_id') == uid and f.get('status') == 'active'}
    if not u_files:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            Utilities.create_button(Utilities.get_text(uid, 'upload'), "nav_upload", uid),
            Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid)
        )
        Utilities.edit_message(call, uid, Utilities.format_border(uid, 'my_files_title', Utilities.get_text(uid, 'no_files')), kb)
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        for fid, f in u_files.items():
            running = fid in active_processes and active_processes[fid].poll() is None
            icon = "🟢" if running else "🔴"
            ft = "VIP" if f.get('type') == 'pro' else "مجاني"
            kb.add(Utilities.create_button(f"{icon} {ft} {f.get('file_name', '?')[:25]}", f"manage_{fid}", uid))
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_main", uid))
        Utilities.edit_message(call, uid, Utilities.format_border(uid, 'my_files_title', Utilities.get_text(uid, 'files_count', count=len(u_files))), kb)

def download_file(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    content = EncryptionManager.load_encrypted_file(fid)
    if not content:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'download_failed'), show_alert=True)
        return
    try:
        original_name = files[fid].get('file_name', f'{fid}.py')
        temp_path = os.path.join(TEMP_DIR, original_name)
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        thumb = Utilities.get_thumb()
        with open(temp_path, 'rb') as f:
            if thumb:
                with open(thumb, 'rb') as t:
                    bot.send_document(call.message.chat.id, f, thumb=t, caption=f"📄 {original_name}", parse_mode="HTML")
            else:
                bot.send_document(call.message.chat.id, f, caption=f"📄 {original_name}", parse_mode="HTML")
        os.remove(temp_path)
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'downloaded'))
    except Exception as e:
        print(f"Download error: {e}")
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'download_failed'), show_alert=True)

def terminal(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    files = DatabaseManager.get_files()
    if fid not in files:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'))
        return
    running = fid in active_processes and active_processes[fid].poll() is None
    output = Utilities.get_logs(fid, 40)
    text = Utilities.get_text(uid, 'terminal_output', name=files[fid]['file_name'],
                             status=Utilities.get_text(uid, 'running') if running else Utilities.get_text(uid, 'stopped'),
                             output=output)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        Utilities.create_button(Utilities.get_text(uid, 'refresh'), f"rterm_{fid}", uid),
        Utilities.create_button(Utilities.get_text(uid, 'input'), f"inp_{fid}", uid)
    )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), f"manage_{fid}", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'terminal_title', text), kb)

def input_step(msg, fid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text:
        return
    if ProcessManager.write_stdin(fid, msg.text):
        text = Utilities.get_text(uid, 'input_sent', cmd=escape(msg.text))
    else:
        text = Utilities.get_text(uid, 'process_not_running')
    Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'input', text), build_back_keyboard(uid, f"term_{fid}"))

def token_step(msg, fid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text:
        return
    token = msg.text.strip()
    content = EncryptionManager.load_encrypted_file(fid)
    if not content:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'file_not_found')), build_back_keyboard(uid, f"manage_{fid}"))
        return
    updated_content = Utilities.update_token_in_memory(content, token)
    if updated_content:
        files = DatabaseManager.get_files()
        if fid in files:
            user_id = files[fid].get('user_id')
            if EncryptionManager.save_encrypted_file(fid, updated_content, user_id):
                Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'token_updated')), build_back_keyboard(uid, f"manage_{fid}"))
            else:
                Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'save_failed')), build_back_keyboard(uid, f"manage_{fid}"))
        else:
            Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'file_not_found')), build_back_keyboard(uid, f"manage_{fid}"))
    else:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'token_failed')), build_back_keyboard(uid, f"manage_{fid}"))

def token_info(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    content = EncryptionManager.load_encrypted_file(fid)
    if not content:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'), show_alert=True)
        return
    try:
        tokens = re.findall(r"(\d{8,12}:[a-zA-Z0-9_-]{35,})", content)
        if not tokens:
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'no_token'), show_alert=True)
            return
        token = tokens[0]
        valid, info = Utilities.check_token(token)
        if valid:
            text = Utilities.get_text(uid, 'token_valid') + '\n\n' + \
                   f"🤖 اسم البوت: {escape(info.get('first_name'))}\n👤 المستخدم: @{info.get('username')}\n🆔 المعرف: <code>{info.get('id')}</code>"
        else:
            text = Utilities.get_text(uid, 'token_invalid') + '\n\n' + escape(str(info))
        kb = types.InlineKeyboardMarkup()
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), f"manage_{fid}", uid))
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        m = bot.send_message(call.message.chat.id, Utilities.format_border(uid, 'token_info', text), parse_mode="HTML", reply_markup=kb)
        Utilities.save_message(call.message.chat.id, m.message_id)
    except:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'error'), show_alert=True)

def extend_step(msg, fid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_number')), build_back_keyboard(uid, f"manage_{fid}"))
        return
    hours = int(msg.text.strip())
    success, message = Utilities.extend_file_time(fid, hours, uid)
    if success:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'extend_success', message=message)), build_back_keyboard(uid, f"manage_{fid}"))
    else:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'extend_failed', message=message)), build_back_keyboard(uid, f"manage_{fid}"))

def preview_code(call, fid, uid):
    if not Utilities.verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'access_denied'), show_alert=True)
        return
    content = EncryptionManager.load_encrypted_file(fid)
    if not content:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'file_not_found'), show_alert=True)
        return
    safe = escape(content[:3000])
    if len(safe) > 3000:
        safe = safe[:3000] + "\n..."
    text = f"👁️ معاينة الكود:\n\n<pre><code class='language-python'>{safe}</code></pre>"
    kb = types.InlineKeyboardMarkup()
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), f"manage_{fid}", uid))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    m = bot.send_message(call.message.chat.id, Utilities.format_border(uid, 'preview_code', text), parse_mode="HTML", reply_markup=kb)
    Utilities.save_message(call.message.chat.id, m.message_id)

def library_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text:
        return
    lib = msg.text.strip()
    m = bot.send_message(msg.chat.id, Utilities.format_border(uid, 'library_install', Utilities.get_text(uid, 'library_install', lib=escape(lib))))
    Utilities.save_message(msg.chat.id, m.message_id)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib], timeout=120)
        text = Utilities.get_text(uid, 'library_installed', lib=escape(lib))
    except subprocess.TimeoutExpired:
        text = Utilities.get_text(uid, 'library_timeout', lib=escape(lib))
    except:
        text = Utilities.get_text(uid, 'library_failed', lib=escape(lib))
    bot.edit_message_text(Utilities.format_border(uid, 'library_install', text), msg.chat.id, m.message_id, parse_mode="HTML", reply_markup=build_back_keyboard(uid))

def broadcast_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    users = DatabaseManager.get_users()
    uids = list(users.keys())
    success, failed = 0, 0
    wait = bot.send_message(msg.chat.id, Utilities.format_border(uid, 'broadcast', Utilities.get_text(uid, 'broadcast_sending', count=len(uids))))
    Utilities.save_message(msg.chat.id, wait.message_id)
    for user_id in uids:
        try:
            if msg.content_type == 'text':
                bot.send_message(int(user_id), msg.text, parse_mode="HTML")
            elif msg.content_type == 'photo':
                bot.send_photo(int(user_id), msg.photo[-1].file_id, caption=msg.caption, parse_mode="HTML")
            elif msg.content_type == 'document':
                bot.send_document(int(user_id), msg.document.file_id, caption=msg.caption, parse_mode="HTML")
            success += 1
            time.sleep(0.05)
        except Exception as e:
            failed += 1
    text = Utilities.get_text(uid, 'broadcast_complete', success=success, failed=failed, total=len(uids))
    bot.edit_message_text(Utilities.format_border(uid, 'broadcast', text), msg.chat.id, wait.message_id, parse_mode="HTML", reply_markup=build_back_keyboard(uid, "nav_admin"))

def channels_panel(call, uid):
    settings = DatabaseManager.get_settings()
    channels = settings.get('channels', [])
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'add_channel'), "add_channel", uid))
    for i, ch in enumerate(channels):
        kb.add(Utilities.create_button(f"❌ إزالة {ch['name']}", f"delch_{i}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    text = Utilities.get_text(uid, 'channels_list', count=len(channels))
    if channels:
        text += "\n\n" + "\n".join([f"📢 {ch['name']} ({ch['username']})" for ch in channels])
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'channels', text), kb)

def add_channel_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text:
        return
    username = msg.text.strip()
    if not username.startswith('@'):
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_username')), build_back_keyboard(uid, "adm_channels"))
        return
    try:
        chat = bot.get_chat(username)
        settings = DatabaseManager.get_settings()
        settings['channels'] = settings.get('channels', []) + [{"username": username, "name": chat.title}]
        DatabaseManager.save_settings(settings)
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'channel_added', name=chat.title)), build_back_keyboard(uid, "adm_channels"))
    except:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'channel_not_found')), build_back_keyboard(uid, "adm_channels"))

def del_channel(call, index, uid):
    settings = DatabaseManager.get_settings()
    try:
        channels = settings.get('channels', [])
        if 0 <= index < len(channels):
            name = channels[index]['name']
            del channels[index]
            settings['channels'] = channels
            DatabaseManager.save_settings(settings)
            bot.answer_callback_query(call.id, Utilities.get_text(uid, 'channel_removed', name=name))
        channels_panel(call, uid)
    except:
        bot.answer_callback_query(call.id, Utilities.get_text(uid, 'error'))

def set_name_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text:
        return
    settings = DatabaseManager.get_settings()
    settings['bot_name'] = msg.text.strip()
    DatabaseManager.save_settings(settings)
    Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'name_set', name=msg.text.strip())), build_back_keyboard(uid, "adm_settings"))

def set_image_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.photo:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'send_image')), build_back_keyboard(uid, "adm_settings"))
        return
    try:
        fid = msg.photo[-1].file_id
        settings = DatabaseManager.get_settings()
        settings['bot_image'] = fid
        DatabaseManager.save_settings(settings)
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'image_updated')), build_back_keyboard(uid, "adm_settings"))
    except:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'failed')), build_back_keyboard(uid, "adm_settings"))

def set_thumb_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.photo:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'send_image')), build_back_keyboard(uid, "adm_settings"))
        return
    try:
        finfo = bot.get_file(msg.photo[-1].file_id)
        path = os.path.join(THUMBS_DIR, "thumb.jpg")
        with open(path, "wb") as f:
            f.write(bot.download_file(finfo.file_path))
        settings = DatabaseManager.get_settings()
        settings['file_thumb'] = path
        DatabaseManager.save_settings(settings)
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'thumb_updated')), build_back_keyboard(uid, "adm_settings"))
    except:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'failed')), build_back_keyboard(uid, "adm_settings"))


# ─── نظام أكواد الهدايا ───
def gift_codes_panel(call, uid):
    codes = DatabaseManager.get_gift_codes()
    text = f"🎫 نظام أكواد الهدايا\n\n📊 عدد الأكواد: {len(codes)}\n\nالأكواد النشطة:\n"
    for code, info in codes.items():
        status = "🟢" if info.get('active', True) else "🔴"
        uses = f"{info['used_count']}/{info['max_uses']}" if info['max_uses'] != -1 else f"{info['used_count']}/∞"
        text += f"{status} <code>{code}</code> | {info['reward_type']} | {uses}\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(Utilities.create_button("➕ إنشاء كود جديد", "create_gift_code", uid))
    for code in list(codes.keys())[:10]:
        kb.add(Utilities.create_button(f"🗑️ حذف {code[:15]}", f"delgiftcode_{code}", uid))
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'gift_codes_admin', text), kb)

def create_gift_code_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    parts = msg.text.strip().split()
    if len(parts) < 3:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', "❌ الصيغة: CODE TYPE VALUE [USES] [DAYS]"), build_back_keyboard(uid, "adm_gift_codes"))
        return
    code = parts[0].upper()
    reward_type = parts[1]
    reward_value = int(parts[2]) if parts[2].isdigit() else 0
    max_uses = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1
    expires_days = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None
    success, msg_text = GiftCodeManager.create_code(code, reward_type, reward_value, max_uses, expires_days)
    if success:
        type_str = "نقاط" if reward_type == 'points' else "أيام VIP" if reward_type == 'vip_days' else "VIP مدى الحياة"
        text = Utilities.get_text(uid, 'code_created', code=code, type=type_str, value=reward_value, uses=max_uses)
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', text), build_back_keyboard(uid, "adm_gift_codes"))
    else:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', msg_text), build_back_keyboard(uid, "adm_gift_codes"))

def redeem_code_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text:
        return
    code = msg.text.strip().upper()
    success, result = GiftCodeManager.redeem_code(code, uid)
    if success:
        reward_text = ""
        if result == 'points':
            reward_text = "نقاط"
        elif result == 'vip_days':
            reward_text = "أيام VIP"
        elif result == 'vip_lifetime':
            reward_text = "VIP مدى الحياة"
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'gift_code_redeemed', reward=reward_text)), build_back_keyboard(uid, "nav_wallet"))
    else:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', result), build_back_keyboard(uid, "nav_wallet"))

# ─── ميزات الأدمن الجديدة ───
def gifts_panel(call, uid):
    text = "🎁 نظام الهدايا والمكافآت\n\nاختر نوع الهدية:"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        Utilities.create_button("🎁 هدية للجميع", "gift_all", uid),
        Utilities.create_button("🎁 هدية لمستخدم", "gift_user", uid)
    )
    kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
    Utilities.edit_message(call, uid, Utilities.format_border(uid, 'gifts_title', text), kb)

def gift_all_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_number')), build_back_keyboard(uid, "adm_gifts"))
        return
    points = int(msg.text.strip())
    users = DatabaseManager.get_users()
    count = 0
    for user_id in users:
        try:
            users[user_id]['points'] = users[user_id].get('points', 0) + points
            count += 1
            try:
                bot.send_message(int(user_id), Utilities.format_border(int(user_id), 'user_gift_notify', f"🎁 لقد تلقيت هدية!\n💰 <b>{points}</b> نقاط من الإدارة."))
            except:
                pass
        except:
            pass
    DatabaseManager.save_users(users)
    Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'gift_sent_all', points=points, count=count)), build_back_keyboard(uid, "adm_gifts"))

def gift_user_step(msg, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', "❌ يرجى إدخال: معرف_المستخدم النقاط"), build_back_keyboard(uid, "adm_gifts"))
        return
    target_id = int(parts[0])
    points = int(parts[1])
    users = DatabaseManager.get_users()
    if str(target_id) not in users:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'invalid_user_id')), build_back_keyboard(uid, "adm_gifts"))
        return
    users[str(target_id)]['points'] = users[str(target_id)].get('points', 0) + points
    DatabaseManager.save_users(users)
    try:
        bot.send_message(target_id, Utilities.format_border(target_id, 'user_gift_notify', f"🎁 لقد تلقيت هدية!\n💰 <b>{points}</b> نقاط من الإدارة."))
    except:
        pass
    Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'gift_sent_user', points=points)), build_back_keyboard(uid, "adm_gifts"))

def show_system_usage(call, uid):
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_mb = mem.used / (1024 * 1024)
        total_mb = mem.total / (1024 * 1024)
        active_count = sum(1 for fid in active_processes if active_processes[fid].poll() is None)
        paused_count = len(paused_bots)
        text = Utilities.get_text(uid, 'system_usage_current', cpu=cpu, ram=round(ram_percent, 1), ram_mb=round(ram_mb, 1), used_mb=round(ram_mb, 1), total_mb=round(total_mb, 1), active=active_count, paused=paused_count)
        kb = types.InlineKeyboardMarkup()
        kb.add(Utilities.create_button("🔄 تحديث", "adm_system_usage", uid))
        kb.add(Utilities.create_button(Utilities.get_text(uid, 'back'), "nav_admin", uid))
        Utilities.edit_message(call, uid, Utilities.format_border(uid, 'view_system_usage', text), kb)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)[:100]}", show_alert=True)

def stop_bot_admin_step(msg, fid, prompt_id, uid):
    if Utilities.is_cancelled(uid):
        Utilities.clear_cancel(uid)
        return
    Utilities.delete_messages(msg.chat.id, prompt_id, msg.message_id)
    reason = msg.text.strip() if msg.text else "تم الإيقاف من قبل الإدارة"
    files = DatabaseManager.get_files()
    if fid in files:
        user_id = files[fid]['user_id']
        files[fid]['admin_stopped'] = True
        DatabaseManager.save_files(files)
        ProcessManager.stop_script(fid, reason)
        try:
            bot.send_message(user_id, Utilities.format_border(user_id, 'stopped_by_admin', Utilities.get_text(user_id, 'stopped_by_admin', reason=reason)))
        except:
            pass
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'success', Utilities.get_text(uid, 'bot_stopped_admin', reason=reason)), build_back_keyboard(uid, "adm_files"))
    else:
        Utilities.send_message(msg.chat.id, uid, Utilities.format_border(uid, 'error', Utilities.get_text(uid, 'file_not_found')), build_back_keyboard(uid, "adm_files"))

# ─── مراقبة الموارد الذكية ───
def resource_monitoring():
    ram_alert_sent = False
    while True:
        try:
            for fid in list(active_processes.keys()):
                usage = ProcessManager.get_resource_usage(fid)
                if usage:
                    if usage['cpu'] > RESOURCE_LIMITS['max_cpu_percent'] or usage['memory'] > RESOURCE_LIMITS['max_memory_mb']:
                        files = DatabaseManager.get_files()
                        if fid in files:
                            user_id = files[fid]['user_id']
                            ProcessManager.stop_script(fid, "تجاوز حدود الموارد")
                            try:
                                bot.send_message(user_id, Utilities.format_border(user_id, 'resource_limit_notify', f"⚠️ تم إيقاف البوت '{files[fid]['file_name']}' بسبب تجاوز حدود الموارد."))
                            except:
                                pass
                            for adm in DatabaseManager.get_admins():
                                try:
                                    bot.send_message(adm, f"⚠️ بوت {files[fid]['file_name']} (مستخدم: {user_id}) توقف بسبب استهلاك عالٍ.\n🖥️ CPU: {usage['cpu']}%\n💾 الذاكرة: {usage['memory']:.2f} ميجابايت")
                                except:
                                    pass

            mem = psutil.virtual_memory()
            ram_percent = mem.percent

            if ram_percent >= RESOURCE_LIMITS['ram_pause_threshold'] and not ram_alert_sent:
                for fid in list(active_processes.keys()):
                    ProcessManager.pause_bot(fid, "ضغط على موارد السيرفر")
                ram_alert_sent = True
                for adm in DatabaseManager.get_admins():
                    try:
                        bot.send_message(adm, Utilities.format_border(adm, 'ram_alert', f"⚠️ تنبيه! استهلاك الرام وصل إلى {ram_percent}%\n⏸️ تم إيقاف جميع البوتات مؤقتاً."))
                    except:
                        pass
            elif ram_percent <= RESOURCE_LIMITS['ram_resume_threshold'] and ram_alert_sent:
                files = DatabaseManager.get_files()
                for fid in list(paused_bots):
                    if fid in files:
                        ProcessManager.resume_bot(fid)
                ram_alert_sent = False
                for adm in DatabaseManager.get_admins():
                    try:
                        bot.send_message(adm, Utilities.format_border(adm, 'ram_normal', f"✅ استهلاك الرام عاد للطبيعي ({ram_percent}%).\n▶️ تم استئناف البوتات."))
                    except:
                        pass

            Utilities.cleanup_temp_files()
            Utilities.cleanup_old_logs()
        except:
            pass
        time.sleep(60)

# ─── حلقة المراقبة ───
def monitoring_loop():
    while True:
        try:
            files = DatabaseManager.get_files()

            for fid in list(active_processes.keys()):
                proc = active_processes.get(fid)
                if not proc or proc.poll() is not None:
                    if fid in active_processes:
                        del active_processes[fid]
                    continue

                if fid not in files:
                    ProcessManager.stop_script(fid, "الملف محذوف")
                    continue

                uid = str(files[fid]['user_id'])

                if not Utilities.check_subscription(int(uid)):
                    ProcessManager.stop_script(fid, "عدم الاشتراك في القنوات")
                    try:
                        bot.send_message(int(uid), Utilities.format_border(int(uid), 'stopped', Utilities.get_text(int(uid), 'stopped_subscription_notify', name=files[fid]['file_name'])))
                    except:
                        pass
                    continue

                # فحص انتهاء الوقت للمجاني
                if not Utilities.is_user_pro(int(uid)) and files[fid].get('type') == 'free':
                    expires_at = files[fid].get('expires_at')
                    if expires_at:
                        try:
                            exp_time = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                            if datetime.now() >= exp_time:
                                fname = files[fid].get('file_name', '?')
                                ProcessManager.cleanup_file(fid)
                                del files[fid]
                                DatabaseManager.save_files(files)
                                try:
                                    bot.send_message(int(uid), Utilities.format_border(int(uid), 'time_expired', Utilities.get_text(int(uid), 'time_expired_notify', name=fname)))
                                except:
                                    pass
                                for adm in DatabaseManager.get_admins():
                                    try:
                                        bot.send_message(adm, f"⏱️ بوت {fname} للمستخدم {uid} انتهى وقتها وتم الحذف التلقائي.")
                                    except:
                                        pass
                        except:
                            pass
                    elif fid in process_hours:
                        process_hours[fid] -= 1
                        if process_hours[fid] <= 0:
                            fname = files[fid].get('file_name', '?')
                            ProcessManager.cleanup_file(fid)
                            del files[fid]
                            DatabaseManager.save_files(files)
                            try:
                                bot.send_message(int(uid), Utilities.format_border(int(uid), 'time_expired', Utilities.get_text(int(uid), 'time_expired_notify', name=fname)))
                            except:
                                pass

                # فحص انتهاء VIP
                if files[fid].get('type') == 'pro' and not Utilities.is_user_pro(int(uid)):
                    fname = files[fid].get('file_name', '?')
                    ProcessManager.cleanup_file(fid)
                    del files[fid]
                    DatabaseManager.save_files(files)
                    try:
                        bot.send_message(int(uid), Utilities.format_border(int(uid), 'vip_expired_stop', f"⏱️ انتهى اشتراك VIP. تم إيقاف وحذف البوت '{fname}'."))
                    except:
                        pass
                    for adm in DatabaseManager.get_admins():
                        try:
                            bot.send_message(adm, f"⏱️ بوت VIP {fname} للمستخدم {uid} انتهى اشتراكه وتم الحذف.")
                        except:
                            pass

            # تنظيف العمليات اليتيمة
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', []) or []
                    cmd_str = ' '.join(str(c) for c in cmdline)
                    if ENV_DIR in cmd_str and 'python' in cmd_str.lower():
                        found = False
                        for fid in files:
                            env_file = os.path.join(ENV_DIR, fid, f"{fid}.py")
                            if env_file in cmd_str:
                                found = True
                                break
                        if not found:
                            proc.kill()
                except:
                    pass

        except Exception as e:
            print(f"Monitoring error: {e}")
        time.sleep(60)

def keep_alive():
    links = ["https://www.google.com", "https://www.bing.com", "https://www.wikipedia.org"]
    while True:
        try:
            requests.get(random.choice(links), timeout=15)
            time.sleep(random.randint(120, 240))
        except:
            time.sleep(60)

threading.Thread(target=resource_monitoring, daemon=True).start()
threading.Thread(target=monitoring_loop, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

init_database()

print("=" * 50)
print("🤖 بوت الاستضافة الاحترافي | REDMOOD")
print("📡 t.me/REDMOOD")
print("📢 t.me/PRO_APK_MOOD")
print("=" * 50)

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Polling error: {e}")
        time.sleep(5)
