from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.response import send_response
from autosnab_bot.services.price_search import prepare_search_result
from autosnab_bot.services.price_search_cache import get_search_instance
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_search_instance().search(update.message.text)
    response_txt = prepare_search_result(result)
    found_txt = f"Найдено {len(list(result.keys()))} позиций \n"
    await send_response(
        update,
        context,
        response=found_txt + response_txt,
    )
