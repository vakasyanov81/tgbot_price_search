import threading
from pathlib import Path

from autosnab_bot.services.price_list import PriceListDataLoader
from autosnab_bot.services.price_search import PriceListSearch

# Загруженный прайс каждого вида: ключ источника → (файл, mtime, поиск).
# Новый файл (свежая дата) или перезаписанный старый читаются заново.
_cache: dict[str, tuple[Path, float, PriceListSearch]] = {}
_lock = threading.Lock()


def get_search_instance(source_key: str, path: Path) -> PriceListSearch:
    """Поиск по файлу прайса; файл читается при первом обращении или после его замены."""
    mtime = path.stat().st_mtime
    with _lock:
        cached = _cache.get(source_key)
        if cached is not None and cached[:2] == (path, mtime):
            return cached[2]
        search = PriceListSearch(PriceListDataLoader(path))
        _cache[source_key] = (path, mtime, search)
        return search
