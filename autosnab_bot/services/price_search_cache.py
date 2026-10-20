from autosnab_bot import config
from autosnab_bot.services.price_list import PriceListDataLoader
from autosnab_bot.services.price_search import PriceListSearch

search_instance: PriceListSearch | None = None


def _load_search() -> PriceListSearch:
    return PriceListSearch(PriceListDataLoader(config.PRICE_FILE_NAME))


def reload_price() -> None:
    global search_instance
    search_instance = _load_search()


def get_search_instance() -> PriceListSearch:
    global search_instance
    if search_instance is None:
        search_instance = _load_search()
    return search_instance
