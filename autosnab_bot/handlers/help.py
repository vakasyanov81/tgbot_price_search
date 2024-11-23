from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.response import send_response
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def help_(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_response(
        update,
        context,
        response="Для поиска по прайсу необходимо загрузить файл price.xlsx выполнив команду /download",
    )
