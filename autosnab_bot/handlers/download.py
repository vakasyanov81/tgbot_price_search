import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot import config
from autosnab_bot.services.file_upload import upload_file
from autosnab_bot.services.price_search_cache import reload_price
from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.document is None:
        return

    doc = message.document
    if not doc.file_name or not doc.file_name.lower().endswith(".xlsx"):
        await send_response(
            update,
            context,
            response="Не верный формат файла. Необходим файл в формате xlsx",
        )
        return

    _file = await context.bot.get_file(doc)
    await upload_file(_file, config.PRICE_FILE_NAME)
    await asyncio.to_thread(reload_price)

    await send_response(
        update,
        context,
        response="Прайс загружен!",
    )
