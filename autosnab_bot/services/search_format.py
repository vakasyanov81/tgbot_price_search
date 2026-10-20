"""Текст выдачи поиска: строка на позицию, цена и остаток без «.0»."""

import html

from autosnab_bot.services.price_list import PriceInfo, price_data


def prepare_search_result(source: price_data) -> str:
    return '\n'.join(search_result_lines(source))


def search_result_lines(source: price_data) -> list[str]:
    """Строки выдачи; у названия с несколькими строками прайса — первая (самая дешёвая)."""
    numbered = enumerate(source.items(), start=1)
    return [_result_line(row, title, prices) for row, (title, prices) in numbered]


def try_to_int(raw_number: str) -> str:
    try:
        return str(int(float(raw_number)))
    except ValueError, OverflowError:
        return raw_number


def _result_line(row: int, title: str, prices: list[PriceInfo]) -> str:
    cheapest = prices[0]
    name = html.escape(cheapest.title or title)
    price = html.escape(try_to_int(cheapest.price))
    rest = html.escape(try_to_int(cheapest.rest))
    supplier = f' ({html.escape(cheapest.supplier)})' if cheapest.supplier else ''
    return f'{row}. {name} - {price}Руб. {rest} шт.{supplier}'
