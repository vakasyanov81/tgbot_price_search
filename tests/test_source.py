import asyncio
from pathlib import Path

import pytest

from autosnab_bot import handlers
from autosnab_bot.services.price_sources import PriceSource
from tests.fakes import keyboard_labels, make_context, make_update

SEARCH_SOURCE = 'search_source'


@pytest.fixture(autouse=True)
def _only_drom_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    def latest_file(source: PriceSource) -> Path | None:
        return Path('price_drom_2026-10-20.xlsx') if source.key == 'drom' else None

    monkeypatch.setattr(PriceSource, 'latest_file', latest_file)


def test_choose_source_lists_prices() -> None:
    context = make_context()
    asyncio.run(handlers.choose_source(make_update('/source'), context))
    assert keyboard_labels(context.bot.sent[0]) == [
        '✅ Прайс для Дрома: price_drom_2026-10-20.xlsx',
        'Общий прайс (не сформирован)',
        'Полный прайс (не сформирован)',
    ]


def test_set_source_remembers_choice() -> None:
    context = make_context()
    asyncio.run(handlers.set_source(make_update(callback_data='src:inner'), context))
    assert context.user_data == {SEARCH_SOURCE: 'inner'}
    assert 'ещё не сформирован' in context.bot.texts[0]


def test_set_source_ignores_unknown() -> None:
    context = make_context()
    asyncio.run(handlers.set_source(make_update(callback_data='src:nope'), context))
    asyncio.run(handlers.set_source(make_update(), context))
    assert not context.user_data
    assert not context.bot.sent
