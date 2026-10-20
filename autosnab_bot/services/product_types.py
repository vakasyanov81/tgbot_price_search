"""Типы товара для фильтра поиска: список из CLI priceformation, закешированный на время работы бота."""

import logging
import time

from autosnab_bot.services import priceformation

logger = logging.getLogger(__name__)

# Список типов меняется только с обновлением priceformation; запуск CLI занимает секунды.
CACHE_TTL = 60 * 60

_types: list[str] = []
_loaded_at = 0.0


async def get_product_types() -> list[str]:
    """Типы товара; при ошибке CLI — прежний список (или пустой, если его ещё не было)."""
    global _types, _loaded_at
    if _types and time.monotonic() - _loaded_at < CACHE_TTL:
        return _types
    try:
        _types = await priceformation.get_product_types()
        _loaded_at = time.monotonic()
    except RuntimeError, ValueError, OSError:
        logger.exception("Не удалось получить типы товара из priceformation")
    return _types
