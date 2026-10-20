import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from autosnab_bot.handlers.type_filter import handle_type_chip
from autosnab_bot.services.price_sources import PriceSource, get_source
from autosnab_bot.services.response import send_response
from autosnab_bot.services.search_replies import SearchReplies, digest
from autosnab_bot.services.search_reply import search_reply
from autosnab_bot.services.type_menu import user_type_filter
from autosnab_bot.services.validate_user import validate_user

logger = logging.getLogger(__name__)

# Ключ выбранного прайса в user_data (см. /source).
USER_SOURCE = 'search_source'


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
    replies = SearchReplies(context.chat_data)
    previous = replies.previous(message.message_id) if update.edited_message else None
    if previous is not None and previous[1] == digest(response):
        return  # результат не изменился — прежний ответ верный
    # Ответ несёт меню внизу (иначе клиент может его потерять), а сообщение с таким меню
    # Telegram редактировать не даёт: заменяем ответ — новый присылаем, прежний удаляем.
    reply = await send_response(update, context, response=response)
    if previous is not None:
        await _delete_reply(update, context, previous[0])
    replies.remember(message.message_id, reply.message_id, digest(response))


async def search_response(context: ContextTypes.DEFAULT_TYPE, text: str) -> str:
    """Ответ на запрос по прайсу и фильтру типа товара, выбранным пользователем."""
    return await search_reply(user_source(context), user_type_filter(context), text)


async def _delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    if update.effective_chat is None:
        return
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    except TelegramError:
        # Уже удалён пользователем или старше 48 часов — остаётся в истории, новый ответ уже отправлен.
        logger.info('Не удалось удалить прежний ответ %s', message_id)
