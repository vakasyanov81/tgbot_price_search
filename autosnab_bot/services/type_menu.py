"""Меню внизу экрана: фильтр поиска по типу товара."""

from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from autosnab_bot.services.product_types import get_product_types

# Выбранный тип товара в user_data; нет ключа — поиск по всем типам.
USER_TYPE_FILTER = "type_filter"
ALL_TYPES = "Все"
ACTIVE_MARK = "✅ "
CHIPS_PER_ROW = 2


def user_type_filter(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    return (context.user_data or {}).get(USER_TYPE_FILTER)


async def type_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """«Все» и типы товара из priceformation, активный отмечен."""
    active = user_type_filter(context) or ALL_TYPES
    labels = [ALL_TYPES, *await get_product_types()]
    chips = [KeyboardButton(ACTIVE_MARK + label if label == active else label) for label in labels]
    rows = [chips[i : i + CHIPS_PER_ROW] for i in range(0, len(chips), CHIPS_PER_ROW)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)
