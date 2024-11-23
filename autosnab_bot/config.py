import os
from pathlib import Path, PurePath

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = PurePath(BASE_DIR, "upload")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOW_USER_LIST = os.getenv("ALLOW_USER_LIST", "")
