import asyncio
import html

from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.services.price_search import prepare_search_result
from autosnab_bot.services.price_search_cache import get_search_instance
from autosnab_bot.services.price_sources import PriceSource, get_source
from autosnab_bot.services.response import send_response
from autosnab_bot.services.validate_user import validate_user

# Ключ выбранного прайса в user_data (см. /source).
USER_SOURCE = "search_source"


def user_source(context: ContextTypes.DEFAULT_TYPE) -> PriceSource:
    return get_source((context.user_data or {}).get(USER_SOURCE))


@validate_user
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.text is None:
        return

    source = user_source(context)
    path = source.latest_file()
    if path is None:
        await send_response(
            update,
            context,
            response=f"{html.escape(source.title)} ещё не сформирован. {source.how_to_make}.\n"
            "Выбрать другой прайс: /source",
        )
        return

    price_search = await asyncio.to_thread(get_search_instance, source.key, path)
    if not price_search.is_loaded:
        await send_response(
            update,
            context,
            response=f"Не удалось прочитать {html.escape(path.name)}: нет листа price или колонки «Номенклатура»",
        )
        return

    result = price_search.search(message.text)
    source_txt = f"Источник: {html.escape(source.title)} ({html.escape(path.name)})"
    found_txt = f"{source_txt}\nНайдено {len(result)} позиций \n"
    await send_response(
        update,
        context,
        response=found_txt + prepare_search_result(result),
    )
