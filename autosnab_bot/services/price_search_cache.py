from autosnab_bot.services.price_list import PriceListDataLoader
from autosnab_bot.services.price_search import PriceListSearch


def get_instance_search_from_file() -> PriceListSearch:
    return PriceListSearch(PriceListDataLoader("price.xlsx"))


search_instance = get_instance_search_from_file()


def reload_price():
    global search_instance
    search_instance = get_instance_search_from_file()


def get_search_instance():
    global search_instance
    return search_instance
