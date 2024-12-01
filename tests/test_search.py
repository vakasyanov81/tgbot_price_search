from autosnab_bot.services.price_list import PriceInfo, price_data
from autosnab_bot.services.price_search import PriceListSearch


class PriceListSimpleDataLoader:
    def __init__(self, items):
        self.price_list: price_data = items

    def get_price_list(self) -> price_data:
        return self.price_list

    def load_price(self):
        pass


def get_instance(data) -> PriceListSearch:
    return PriceListSearch(PriceListSimpleDataLoader(data))


def search(title, search_string):
    _price_list = get_instance({title: PriceInfo("10", "10", "1", 1)})
    return _price_list.search(search_string)


def test_search():
    assert {} == search("185/60r15 bfgoodrich g-force winter 2 88t", "185 65 r15")
    assert "185/65r15 bfgoodrich g-force winter 2 88t" in search(
        "185/65r15 bfgoodrich g-force winter 2 88t", "185 65 r15"
    )
