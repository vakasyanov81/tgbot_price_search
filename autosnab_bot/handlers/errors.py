import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ошибка в обработчике: записать в лог и сказать пользователю, а не молчать."""
    logger.error('Ошибка при обработке обновления', exc_info=context.error)
    if not isinstance(update, Update) or update.effective_chat is None:
        return
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Не удалось выполнить запрос: {context.error}. Попробуйте ещё раз или уточните запрос',
        )
    except TelegramError:
        logger.exception('Не удалось сообщить пользователю об ошибке')
