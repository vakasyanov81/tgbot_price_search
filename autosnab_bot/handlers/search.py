import asyncio
import hashlib
import html
import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from autosnab_bot.handlers.type_filter import handle_type_chip
from autosnab_bot.services.price_search import search_result_lines
from autosnab_bot.services.price_search_cache import get_search_instance
from autosnab_bot.services.price_sources import PriceSource, get_source
from autosnab_bot.services.response import send_response
from autosnab_bot.services.type_menu import user_type_filter
from autosnab_bot.services.validate_user import validate_user

logger = logging.getLogger(__name__)

# Ключ выбранного прайса в user_data (см. /source).
USER_SOURCE = "search_source"

# Ответы на поисковые запросы в chat_data: ИД сообщения с запросом → ответ бота.
# Нужны, чтобы при редактировании запроса заменить ответ, а не добавить ещё один.
SEARCH_REPLIES = "search_replies"
MAX_SEARCH_REPLIES = 200

# Telegram не принимает сообщения длиннее 4096 символов; длинные названия (диски) в 50 строк туда не влезают.
MESSAGE_LIMIT = 4096
NOTE_RESERVE = 60
# Сколько самых дешёвых позиций показывать.
MAX_RESULTS = 50


def user_source(context: ContextTypes.DEFAULT_TYPE) -> PriceSource:
    return get_source((context.user_data or {}).get(USER_SOURCE))


@validate_user
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Поиск по тексту сообщения; отредактированный запрос заменяет прежний ответ новым."""
    message = update.message or update.edited_message
    if message is None or message.text is None:
        return

    # Чипс меню внизу приходит обычным текстом; отредактированное сообщение — всегда запрос.
    if update.message is not None and await handle_type_chip(update, context, message.text):
        return

    response = await search_response(context, message.text)
    digest = _digest(response)
    replies = _search_replies(context)
    previous = replies.get(message.message_id) if update.edited_message else None
    if previous is not None and previous[1] == digest:
        return  # результат не изменился — прежний ответ верный

    # Ответ несёт меню внизу (иначе клиент может его потерять), а сообщение с таким меню
    # Telegram редактировать не даёт: заменяем ответ — новый присылаем, прежний удаляем.
    reply = await send_response(update, context, response=response)
    if previous is not None:
        await _delete_reply(update, context, previous[0])
    replies[message.message_id] = (reply.message_id, digest)
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
    # Все совпадения нужны для общего числа найденных; показываются самые дешёвые.
    result = price_search.search(text, search_limit=None, product_type=product_type)
    header = [f"Источник: {html.escape(source.title)} ({html.escape(path.name)})"]
    if product_type:
        header.append(f"Тип товара: {html.escape(product_type)}")
    lines = search_result_lines(dict(list(result.items())[:MAX_RESULTS]))
    found = f"Найдено {len(result)} позиций"
    shown = _lines_that_fit("\n".join([*header, found]), lines, note_needed=len(result) > len(lines))
    if shown < len(result):
        found += f", показаны {shown} самых дешёвых — уточните запрос"
    return "\n".join([*header, found, *lines[:shown]])


def _lines_that_fit(header: str, lines: list[str], note_needed: bool) -> int:
    """Сколько первых строк результата помещается в одно сообщение вместе с заголовком."""
    # Место под «, показаны NN самых дешёвых — уточните запрос», если она будет.
    reserve = NOTE_RESERVE if note_needed else 0
    if len(header) + reserve + sum(len(line) + 1 for line in lines) <= MESSAGE_LIMIT:
        return len(lines)
    length = len(header) + NOTE_RESERVE
    for count, line in enumerate(lines):
        length += len(line) + 1
        if length > MESSAGE_LIMIT:
            return count
    return len(lines)


def _search_replies(context: ContextTypes.DEFAULT_TYPE) -> dict[int, tuple[int, str]]:
    """ИД запроса → (ИД ответа, отпечаток текста ответа). Старые записи (только ИД ответа) приводятся к паре."""
    if context.chat_data is None:
        return {}
    replies = context.chat_data.setdefault(SEARCH_REPLIES, {})
    for query_id, record in replies.items():
        if isinstance(record, int):
            replies[query_id] = (record, "")
    return replies


def _digest(response: str) -> str:
    return hashlib.sha256(response.encode()).hexdigest()[:16]


async def _delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    if update.effective_chat is None:
        return
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    except TelegramError:
        # Уже удалён пользователем или старше 48 часов — остаётся в истории, новый ответ уже отправлен.
        logger.info("Не удалось удалить прежний ответ %s", message_id)
