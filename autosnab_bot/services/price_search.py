import html
import math
from collections.abc import Callable

from autosnab_bot.services.price_list import PriceInfo, price_data


class PriceListSearch:
    def __init__(self, data_loader) -> None:
        self.is_loaded = bool(data_loader.load_price())
        self.price_list: price_data = data_loader.get_price_list()

    def search(self, search_string: str, search_limit: int | None = 50, product_type: str | None = None) -> price_data:
        """Поиск по названию позиции в прайсе, сначала дешёвые; product_type — только позиции этого типа товара.

        search_limit — сколько самых дешёвых позиций вернуть (None — все найденные).
        """
        return self.strict_search(search_string, search_limit, product_type) or self.no_accurate_search(
            search_string, search_limit, product_type
        )

    def strict_search(
        self, search_string: str, search_limit: int | None = 50, product_type: str | None = None
    ) -> price_data:
        """Строгий поиск по точному вхождению"""
        search_string = search_string.lower()
        return self._collect(lambda title: search_string in title, search_limit, product_type)

    def no_accurate_search(
        self, search_string: str, search_limit: int | None = 50, product_type: str | None = None
    ) -> price_data:
        """Не строгий поиск"""
        search_chunks = search_string.lower().split()
        if len(search_chunks) <= 1:
            return {}
        return self._collect(lambda title: all(chunk in title for chunk in search_chunks), search_limit, product_type)

    def _collect(
        self, matches: Callable[[str], bool], search_limit: int | None, product_type: str | None
    ) -> price_data:
        """Все совпадения, по возрастанию цены; у названия с несколькими строками первой идёт самая дешёвая."""
        found: list[tuple[str, list[PriceInfo]]] = []
        for title, prices in self.price_list.items():
            if not matches(title):
                continue
            if product_type:
                prices = [info for info in prices if info.product_type == product_type]
                if not prices:
                    continue
            found.append((title, sorted(prices, key=price_value)))
        found.sort(key=lambda item: price_value(item[1][0]))
        return dict(found[:search_limit])


def price_value(info: PriceInfo) -> float:
    """Цена для сортировки; позиции без цены или с нечисловой ценой — в конец."""
    try:
        return float(info.price)
    except ValueError:
        return math.inf


def prepare_search_result(source: price_data) -> str:
    return "\n".join(search_result_lines(source))


def search_result_lines(source: price_data) -> list[str]:
    lines = []
    for row, (title, prices) in enumerate(source.items(), start=1):
        price = html.escape(try_to_int(prices[0].price))
        rest = html.escape(try_to_int(prices[0].rest))
        line = f"{row}. {html.escape(prices[0].title or title)} - {price}Руб. {rest} шт."
        if prices[0].supplier:
            line += f" ({html.escape(prices[0].supplier)})"
        lines.append(line)
    return lines


def try_to_int(val: str) -> str:
    try:
        return str(int(float(val)))
    except ValueError, OverflowError:
        return val
