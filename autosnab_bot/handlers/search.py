from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.services.price_search import prepare_search_result
from autosnab_bot.services.price_search_cache import get_search_instance
from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import validate_user


@validate_user
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.text is None:
        return

    price_search = get_search_instance()
    if not price_search.is_loaded:
        await send_response(
            update,
            context,
            response="Прайс не загружен. Выполните команду /download и загрузите файл price.xlsx",
        )
        return

    result = price_search.search(message.text)
    found_txt = f"Найдено {len(result)} позиций \n"
    await send_response(
        update,
        context,
        response=found_txt + prepare_search_result(result),
    )
