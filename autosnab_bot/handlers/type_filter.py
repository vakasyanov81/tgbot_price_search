import html

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from autosnab_bot.services.product_types import get_product_types
from autosnab_bot.services.response import send_response

# Выбранный тип товара в user_data; нет ключа — поиск по всем типам.
USER_TYPE_FILTER = "type_filter"
ALL_TYPES = "Все"
ACTIVE_MARK = "✅ "
CHIPS_PER_ROW = 2


def user_type_filter(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    return (context.user_data or {}).get(USER_TYPE_FILTER)


async def type_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """Меню внизу экрана: «Все» и типы товара из priceformation, активный отмечен."""
    active = user_type_filter(context) or ALL_TYPES
    labels = [ALL_TYPES, *await get_product_types()]
    chips = [KeyboardButton(ACTIVE_MARK + label if label == active else label) for label in labels]
    rows = [chips[i : i + CHIPS_PER_ROW] for i in range(0, len(chips), CHIPS_PER_ROW)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


async def send_type_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    await send_response(update, context, response=text, keyboard=await type_keyboard(context))


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
    await send_type_menu(update, context, message)
    return True
