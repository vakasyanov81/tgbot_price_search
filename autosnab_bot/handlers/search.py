import asyncio
import html

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from autosnab_bot.handlers.type_filter import handle_type_chip
from autosnab_bot.services.price_search import prepare_search_result
from autosnab_bot.services.price_search_cache import get_search_instance
from autosnab_bot.services.price_sources import PriceSource, get_source
from autosnab_bot.services.response import edit_response, send_response
from autosnab_bot.services.type_menu import user_type_filter
from autosnab_bot.services.validate_user import validate_user

# Ключ выбранного прайса в user_data (см. /source).
USER_SOURCE = "search_source"

# Ответы на поисковые запросы в chat_data: ИД сообщения с запросом → ИД ответа бота.
# Нужны, чтобы при редактировании запроса переписать ответ, а не присылать новый.
SEARCH_REPLIES = "search_replies"
MAX_SEARCH_REPLIES = 200


def user_source(context: ContextTypes.DEFAULT_TYPE) -> PriceSource:
    return get_source((context.user_data or {}).get(USER_SOURCE))


@validate_user
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Поиск по тексту сообщения; отредактированный запрос переписывает прежний ответ."""
    message = update.message or update.edited_message
    if message is None or message.text is None:
        return

    # Чипс меню внизу приходит обычным текстом; отредактированное сообщение — всегда запрос.
    if update.message is not None and await handle_type_chip(update, context, message.text):
        return

    response = await search_response(context, message.text)
    replies = _search_replies(context)
    reply_id = replies.get(message.message_id) if update.edited_message else None
    if reply_id is not None:
        try:
            await edit_response(update, context, reply_id, response)
            return
        except BadRequest as exc:
            # Результат не изменился — ответ уже верный.
            if "not modified" in str(exc).lower():
                return
            # Иначе ответ удалён или его нельзя изменить: пришлём новый.

    reply = await send_response(update, context, response=response)
    replies[message.message_id] = reply.message_id
    while len(replies) > MAX_SEARCH_REPLIES:
        del replies[next(iter(replies))]


async def search_response(context: ContextTypes.DEFAULT_TYPE, text: str) -> str:
    """Текст ответа на запрос: источник и найденные позиции, либо почему искать не в чем."""
    source = user_source(context)
    path = source.latest_file()
    if path is None:
        not_ready = f"{html.escape(source.title)} ещё не сформирован. {source.how_to_make}."
        return f"{not_ready}\nВыбрать другой прайс: /source"

    price_search = await asyncio.to_thread(get_search_instance, source.key, path)
    if not price_search.is_loaded:
        return f"Не удалось прочитать {html.escape(path.name)}: нет листа price или колонки «Номенклатура»"

    product_type = user_type_filter(context)
    result = price_search.search(text, product_type=product_type)
    header = [f"Источник: {html.escape(source.title)} ({html.escape(path.name)})"]
    if product_type:
        header.append(f"Тип товара: {html.escape(product_type)}")
    header.append(f"Найдено {len(result)} позиций ")
    found_txt = "\n".join(header) + "\n"
    return found_txt + prepare_search_result(result)


def _search_replies(context: ContextTypes.DEFAULT_TYPE) -> dict[int, int]:
    if context.chat_data is None:
        return {}
    return context.chat_data.setdefault(SEARCH_REPLIES, {})
