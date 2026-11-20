"""Меню внизу экрана: фильтр поиска по типу товара."""

from itertools import batched

from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from autosnab_bot.services.price_sources import PriceSource, get_source
from autosnab_bot.services.product_types import get_product_types

# Выбранный тип товара в user_data; нет ключа — поиск по всем типам.
USER_TYPE_FILTER = 'type_filter'
USER_SOURCE = 'search_source'
ALL_TYPES = 'Все'
ACTIVE_MARK = '✅ '
CHIPS_PER_ROW = 2


def user_source(context: ContextTypes.DEFAULT_TYPE) -> PriceSource:
    return get_source((context.user_data or {}).get(USER_SOURCE))


async def source_types(source: PriceSource) -> list[str]:
    labels = [label for group in source.product_groups for label in await get_product_types(group)]
    return list(dict.fromkeys(labels))


async def user_type_filter(context: ContextTypes.DEFAULT_TYPE, source: PriceSource) -> str | None:
    selected = (context.user_data or {}).get(USER_TYPE_FILTER)
    return selected if selected and selected in await source_types(source) else None


async def type_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """«Все» и типы товара из priceformation, активный отмечен."""
    labels = [ALL_TYPES, *await source_types(user_source(context))]
    selected = (context.user_data or {}).get(USER_TYPE_FILTER)
    active = selected if selected in labels else ALL_TYPES
    chips = [KeyboardButton(_chip_label(label, active)) for label in labels]
    rows = tuple(batched(chips, CHIPS_PER_ROW, strict=False))
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def _chip_label(label: str, active: str) -> str:
    return f'{ACTIVE_MARK}{label}' if label == active else label
