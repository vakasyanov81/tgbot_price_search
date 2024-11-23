from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.handlers.response import send_response_as_markdown
from autosnab_bot.services.price_list import prepare_search_result, price_list_instance
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = price_list_instance.search(update.message.text)
    response_txt = prepare_search_result(result)
    found_txt = f"Найдено {len(list(result.keys()))} позиций \n"
    await send_response_as_markdown(
        update,
        context,
        response=found_txt + response_txt,
    )
