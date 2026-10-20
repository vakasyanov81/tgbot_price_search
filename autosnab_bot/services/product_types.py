"""Типы товара для фильтра поиска: список из CLI priceformation, закешированный на время работы бота."""

import dataclasses
import datetime
import logging
import time

from autosnab_bot.services import priceformation_reference

logger = logging.getLogger(__name__)

# Список типов меняется только с обновлением priceformation; запуск CLI занимает секунды.
CACHE_TTL = datetime.timedelta(hours=1).total_seconds()


@dataclasses.dataclass
class _TypesCache:
    types: list[str] = dataclasses.field(default_factory=list)
    loaded_at: float = 0

    def is_fresh(self) -> bool:
        return bool(self.types) and time.monotonic() - self.loaded_at < CACHE_TTL


_cache = _TypesCache()


async def get_product_types() -> list[str]:
    """Типы товара; при ошибке CLI — прежний список (или пустой, если его ещё не было)."""
    if _cache.is_fresh():
        return _cache.types
    try:
        fetched = await priceformation_reference.get_product_types()
    except RuntimeError, ValueError, OSError:
        logger.exception('Не удалось получить типы товара из priceformation')
        return _cache.types
    _cache.types = fetched
    _cache.loaded_at = time.monotonic()
    return fetched
