import html

from telegram import Update
from telegram.ext import ContextTypes

from autosnab_bot.services.product_types import get_product_types
from autosnab_bot.services.response import send_response
from autosnab_bot.services.type_menu import ACTIVE_MARK, ALL_TYPES, USER_TYPE_FILTER


async def handle_type_chip(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    """Нажатие на чипс типа товара: переключить фильтр. False — это не чипс, а поисковый запрос."""
    label = text.strip().removeprefix(ACTIVE_MARK.strip()).strip()
    if label != ALL_TYPES and label not in await get_product_types():
        return False
    if context.user_data is not None:
        if label == ALL_TYPES:
            context.user_data.pop(USER_TYPE_FILTER, None)
        else:
            context.user_data[USER_TYPE_FILTER] = label
    if label == ALL_TYPES:
        message = "Фильтр снят: поиск по всем типам товара"
    else:
        message = f"Фильтр: <b>{html.escape(label)}</b>. Поиск идёт только по этому типу товара"
    # Ответ несёт меню с новой отметкой активного чипса (см. send_response).
    await send_response(update, context, response=message)
    return True
