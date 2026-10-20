import functools
import math
from collections.abc import Callable
from typing import Protocol

from autosnab_bot.services.price_list import PriceInfo, price_data

type Match = tuple[str, list[PriceInfo]]
type TitleMatcher = Callable[[str], bool]


class PriceLoader(Protocol):
    def load_price(self) -> bool: ...

    def get_price_list(self) -> price_data: ...


class PriceListSearch:
    def __init__(self, data_loader: PriceLoader) -> None:
        self.is_loaded = bool(data_loader.load_price())
        self.price_list: price_data = data_loader.get_price_list()

    def search(self, search_string: str, search_limit: int | None = 50, product_type: str | None = None) -> price_data:
        """Поиск по названию позиции в прайсе, сначала дешёвые; product_type — только позиции этого типа товара.

        search_limit — сколько самых дешёвых позиций вернуть (None — все найденные).
        """
        strict = self.strict_search(search_string, search_limit, product_type)
        return strict or self.no_accurate_search(search_string, search_limit, product_type)

    def strict_search(
        self, search_string: str, search_limit: int | None = 50, product_type: str | None = None
    ) -> price_data:
        """Строгий поиск по точному вхождению"""
        matches = functools.partial(_has_chunk, search_string.lower())
        return self._collect(matches, search_limit, product_type)

    def no_accurate_search(
        self, search_string: str, search_limit: int | None = 50, product_type: str | None = None
    ) -> price_data:
        """Не строгий поиск"""
        search_chunks = search_string.lower().split()
        if len(search_chunks) <= 1:
            return {}
        matches = functools.partial(_has_all_chunks, search_chunks)
        return self._collect(matches, search_limit, product_type)

    def _collect(self, matches: TitleMatcher, search_limit: int | None, product_type: str | None) -> price_data:
        """Все совпадения, по возрастанию цены; у названия с несколькими строками первой идёт самая дешёвая."""
        found: list[Match] = []
        for title, prices in self.price_list.items():
            of_type = _of_type(prices, product_type) if matches(title) else []
            if of_type:
                found.append((title, sorted(of_type, key=price_value)))
        found.sort(key=_cheapest_price)
        return dict(found[:search_limit])


def price_value(price_info: PriceInfo) -> float:
    """Цена для сортировки; позиции без цены или с нечисловой ценой — в конец."""
    try:
        return float(price_info.price)
    except ValueError:
        return math.inf


def _has_chunk(chunk: str, title: str) -> bool:
    return chunk in title


def _has_all_chunks(chunks: list[str], title: str) -> bool:
    return all(chunk in title for chunk in chunks)


def _of_type(prices: list[PriceInfo], product_type: str | None) -> list[PriceInfo]:
    if not product_type:
        return prices
    return [price_info for price_info in prices if price_info.product_type == product_type]


def _cheapest_price(match: Match) -> float:
    return price_value(match[1][0])
