import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
# Состояние бота между перезапусками: выбранный прайс для поиска и т.п.
STATE_FILE = BASE_DIR / "bot_state.pickle"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOW_USER_LIST = os.getenv("ALLOW_USER_LIST", "")
