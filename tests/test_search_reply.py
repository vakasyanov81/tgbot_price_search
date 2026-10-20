import asyncio
import functools
import operator
from pathlib import Path

import pytest

from autosnab_bot.services import search_reply
from autosnab_bot.services.price_list import PriceInfo
from autosnab_bot.services.price_search import PriceListSearch
from autosnab_bot.services.price_sources import DEFAULT_SOURCE, SOURCES_BY_KEY, PriceSource
from tests.price_helpers import StubLoader, numbered_prices, price_info

DROM_FILE = Path('price_drom_2026-10-20.xlsx')
DISK = 'Диск'
MANY = 120
LONG_TITLE_LENGTH = 150


def many_prices() -> dict[str, list[PriceInfo]]:
    return numbered_prices('kama', MANY, functools.partial(operator.add, 1000))


def reply_for(
    monkeypatch: pytest.MonkeyPatch,
    titles_prices: dict[str, list[PriceInfo]],
    text: str,
    product_type: str | None = None,
) -> str:
    search = PriceListSearch(StubLoader(titles_prices))
    monkeypatch.setattr(search_reply, 'get_search_instance', lambda _key, _path: search)
    monkeypatch.setattr(PriceSource, 'latest_file', lambda _source: DROM_FILE)
    return asyncio.run(search_reply.search_reply(DEFAULT_SOURCE, product_type, text))


def test_reply_shows_source_type_total_and_cheapest(monkeypatch: pytest.MonkeyPatch) -> None:
    titles_prices = many_prices()
    lines = reply_for(monkeypatch, titles_prices, 'kama', DISK).split('\n')
    assert lines[0] == f'Источник: Прайс для Дрома ({DROM_FILE.name})'
    assert lines[1] == f'Тип товара: {DISK}'
    assert lines[2] == 'Найдено 0 позиций'


def test_reply_counts_all_and_shows_fifty(monkeypatch: pytest.MonkeyPatch) -> None:
    titles_prices = many_prices()
    lines = reply_for(monkeypatch, titles_prices, 'kama').split('\n')
    assert lines[1] == f'Найдено {MANY} позиций, показаны {search_reply.MAX_RESULTS} самых дешёвых — уточните запрос'
    assert lines[2].startswith('1. kama 0 - 1000Руб.')
    assert len(lines) == 2 + search_reply.MAX_RESULTS


def test_long_reply_fits_telegram_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    long_title = 'диск ' + 'x' * LONG_TITLE_LENGTH
    titles_prices = {
        f'{long_title} {index}': [price_info('1000', index, product_type=DISK)]
        for index in range(search_reply.MAX_RESULTS)
    }
    reply = reply_for(monkeypatch, titles_prices, 'диск', DISK)
    assert len(reply) <= search_reply.MESSAGE_LIMIT
    after_shown = reply.split('показаны ')[1]
    shown = int(after_shown.split(' ')[0])
    assert 0 < shown < search_reply.MAX_RESULTS


def test_reply_without_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    assert reply_for(monkeypatch, {}, 'kama').split('\n')[1] == 'Найдено 0 позиций'


def test_reply_when_price_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PriceSource, 'latest_file', lambda _source: None)
    reply = asyncio.run(search_reply.search_reply(SOURCES_BY_KEY['full'], None, 'kama'))
    assert reply.startswith('Полный прайс ещё не сформирован.')
    assert '/source' in reply


def test_reply_when_price_unreadable(monkeypatch: pytest.MonkeyPatch) -> None:
    search = PriceListSearch(StubLoader({}, loaded=False))
    monkeypatch.setattr(search_reply, 'get_search_instance', lambda _key, _path: search)
    monkeypatch.setattr(PriceSource, 'latest_file', lambda _source: DROM_FILE)
    reply = asyncio.run(search_reply.search_reply(DEFAULT_SOURCE, None, 'kama'))
    assert reply.startswith(f'Не удалось прочитать {DROM_FILE.name}')


def test_short_result_fits_whole() -> None:
    assert search_reply.lines_that_fit('header', ['1. a', '2. b'], total_found=2) == 2
