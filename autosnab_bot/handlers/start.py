from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_response(
        update,
        context,
        response='Салам, пополам! Это бот для поиска позиций по прайс листу!\n'
        'Внизу — типы товара: нажмите на тип, чтобы искать только по нему.',
    )
