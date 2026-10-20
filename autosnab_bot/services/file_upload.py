from telegram import File

from autosnab_bot import config


async def upload_file(_file: File, file_name: str) -> None:
    target = config.UPLOAD_DIR / file_name
    partial = target.with_name(target.name + ".part")
    await _file.download_to_drive(partial)
    partial.replace(target)
