"""Текст ответа на поисковый запрос: источник, фильтр, сколько найдено и самые дешёвые позиции."""

import asyncio
import html
import itertools
from pathlib import Path

from telegram.constants import MessageLimit

from autosnab_bot.services.price_list import price_data
from autosnab_bot.services.price_search_cache import get_search_instance
from autosnab_bot.services.price_sources import PriceSource
from autosnab_bot.services.search_format import search_result_lines

# Telegram не принимает сообщения длиннее 4096 символов; длинные названия (диски) в 50 строк туда не влезают.
MESSAGE_LIMIT = MessageLimit.MAX_TEXT_LENGTH
# Место под «, показаны NN самых дешёвых — уточните запрос».
NOTE_RESERVE = 60
# Сколько самых дешёвых позиций показывать.
MAX_RESULTS = 50


async def search_reply(source: PriceSource, product_type: str | None, text: str) -> str:
    """Ответ на запрос text по прайсу source; product_type — фильтр по типу товара."""
    path = source.latest_file()
    if path is None:
        not_ready = f'{html.escape(source.title)} ещё не сформирован. {source.how_to_make}.'
        return f'{not_ready}\nВыбрать другой прайс: /source'
    price_search = await asyncio.to_thread(get_search_instance, source.key, path)
    if not price_search.is_loaded:
        return f'Не удалось прочитать {html.escape(path.name)}: нет листа price или колонки «Номенклатура»'
    # Все совпадения нужны для общего числа найденных; показываются самые дешёвые.
    found = price_search.search(text, search_limit=None, product_type=product_type)
    return _fit_reply(_header(source, path, product_type), found)


def lines_that_fit(header: str, lines: list[str], total_found: int) -> int:
    """Сколько первых строк результата помещается в одно сообщение вместе с заголовком.

    Если найдено больше, чем строк, к заголовку допишется пометка «показаны N» — под неё оставляется место.
    """
    reserve = NOTE_RESERVE if total_found > len(lines) else 0
    if len(header) + reserve + _text_length(lines) <= MESSAGE_LIMIT:
        return len(lines)
    length = len(header) + NOTE_RESERVE
    for count, line in enumerate(lines):
        length += len(line) + 1
        if length > MESSAGE_LIMIT:
            return count
    return len(lines)


def _header(source: PriceSource, path: Path, product_type: str | None) -> list[str]:
    title = html.escape(source.title)
    file_name = html.escape(path.name)
    header = [f'Источник: {title} ({file_name})']
    if product_type:
        escaped_type = html.escape(product_type)
        header.append(f'Тип товара: {escaped_type}')
    return header


def _fit_reply(header: list[str], found: price_data) -> str:
    cheapest = dict(itertools.islice(found.items(), MAX_RESULTS))
    lines = search_result_lines(cheapest)
    total = f'Найдено {len(found)} позиций'
    heading = '\n'.join([*header, total])
    shown = lines_that_fit(heading, lines, total_found=len(found))
    if shown < len(found):
        total = f'{total}, показаны {shown} самых дешёвых — уточните запрос'
    return '\n'.join([*header, total, *lines[:shown]])


def _text_length(lines: list[str]) -> int:
    """Длина строк вместе с переводами строк между ними и заголовком."""
    return sum(len(line) + 1 for line in lines)
