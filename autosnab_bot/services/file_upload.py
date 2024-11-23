import os

from autosnab_bot.config import UPLOAD_DIR


async def upload_file(_file, file_name):
    await _file.download_to_drive(str(UPLOAD_DIR) + os.sep + file_name)
    return _file
