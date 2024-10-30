import os
from typing import NamedTuple


class Config(NamedTuple):
    TG_TOKEN = os.getenv('TG_TOKEN')
    OPEN_AI_TOKEN = os.getenv('OPEN_AI_TOKEN')
    MODEL_VOICE_TRANSLIT = "whisper-1"
    CHAT_GPT_MODEL = "gpt-3.5-turbo"
    ALLOW_USER_LIST = os.getenv('ALLOW_USER_LIST')
    UPLOAD_DIR = 'upload'

