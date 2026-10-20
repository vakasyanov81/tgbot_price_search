import html
from collections.abc import Callable

from autosnab_bot.services.price_list import price_data


class PriceListSearch:
    def __init__(self, data_loader) -> None:
        self.is_loaded = bool(data_loader.load_price())
        self.price_list: price_data = data_loader.get_price_list()

    def search(self, search_string: str, search_limit: int = 50, product_type: str | None = None) -> price_data:
        """Поиск по названию позиции в прайсе; product_type — только позиции этого типа товара"""
        return self.strict_search(search_string, search_limit, product_type) or self.no_accurate_search(
            search_string, search_limit, product_type
        )

    def strict_search(self, search_string: str, search_limit: int = 50, product_type: str | None = None) -> price_data:
        """Строгий поиск по точному вхождению"""
        search_string = search_string.lower()
        return self._collect(lambda title: search_string in title, search_limit, product_type)

    def no_accurate_search(
        self, search_string: str, search_limit: int = 50, product_type: str | None = None
    ) -> price_data:
        """Не строгий поиск"""
        search_chunks = search_string.lower().split()
        if len(search_chunks) <= 1:
            return {}
        return self._collect(lambda title: all(chunk in title for chunk in search_chunks), search_limit, product_type)

    def _collect(self, matches: Callable[[str], bool], search_limit: int, product_type: str | None) -> price_data:
        result: price_data = {}
        for title, prices in self.price_list.items():
            if not matches(title):
                continue
            if product_type:
                prices = [info for info in prices if info.product_type == product_type]
                if not prices:
                    continue
            result[title] = prices
            if len(result) >= search_limit:
                break
        return result


def prepare_search_result(source: price_data) -> str:
    # добавить сортировку по цене, сначала дешевые.
    lines = []
    for row, (title, prices) in enumerate(source.items(), start=1):
        price = html.escape(try_to_int(prices[0].price))
        rest = html.escape(try_to_int(prices[0].rest))
        line = f"{row}. {html.escape(title)} - {price}Руб. {rest} шт."
        if prices[0].supplier:
            line += f" ({html.escape(prices[0].supplier)})"
        lines.append(line)
    return "\n".join(lines)


def try_to_int(val: str) -> str:
    try:
        return str(int(float(val)))
    except ValueError, OverflowError:
        return val
