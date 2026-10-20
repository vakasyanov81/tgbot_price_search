from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.type_filter import send_type_menu
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_type_menu(
        update,
        context,
        "Салам, пополам! Это бот для поиска позиций по прайс листу!\n"
        "Внизу — типы товара: нажмите на тип, чтобы искать только по нему.",
    )
