from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.response import send_response
from autosnab_bot.services.file_upload import upload_file
from autosnab_bot.services.price_list import price_list_instance
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if ".xlsx" not in doc.file_name:
        await send_response(
            update,
            context,
            response="Не верный формат файла. Необходим файл в формате xlsx",
        )
        return

    _file = await context.bot.get_file(update.message.document)
    await upload_file(_file, "price.xlsx")
    price_list_instance.load_price()

    await send_response(
        update,
        context,
        response="Прайс загружен!",
    )
