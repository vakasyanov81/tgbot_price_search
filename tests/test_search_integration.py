"""Выбор источника и поиск с настоящим чтением Excel, без сети и боевых файлов."""

import asyncio
from pathlib import Path

import pytest
from openpyxl import load_workbook

from autosnab_bot import handlers
from autosnab_bot.services import price_sources
from tests.fakes import keyboard_labels, make_context, make_update
from tests.price_helpers import DROM_HEADER, write_price


@pytest.fixture
def _result_prices(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_price(
        tmp_path / 'price_drom_akb_2026-11-17.xlsx',
        [DROM_HEADER, ('Аккумулятор', 'Бренд', 'АКБ 255', '', '', 6000, 2, '')],
        sheet='Аккумуляторы',
    )
    common = write_price(
        tmp_path / 'price_2026-11-17.xlsx',
        [DROM_HEADER, ('Шина', 'Бренд', 'Шина 255', '', '', 5000, 4, '')],
        sheet='Шины и диски',
    )
    workbook = load_workbook(common)
    batteries = workbook.create_sheet('Аккумуляторы')
    batteries.append(['Название', 'Цена продажи', 'Закупочная цена', 'Остаток', 'Поставщик'])
    batteries.append(['АКБ 255', 6000, 4500, 2, 'Поставщик АКБ'])
    extra = workbook.create_sheet('Спецпредложения')
    extra.append(['Название', 'Цена продажи', 'Закупочная цена', 'Остаток'])
    extra.append(['АКБ 255 специальный', 7000, 5000, 1])
    workbook.save(common)
    monkeypatch.setattr(price_sources, 'RESULT_DIR', tmp_path)


@pytest.mark.parametrize(
    ('source_key', 'file_name', 'source_title', 'expected_positions'),
    [
        ('drom', 'price_drom_akb_2026-11-17.xlsx', 'Прайс для Дрома (АКБ)', ['1. АКБ 255 - 6000р 2 шт.']),
        (
            'inner',
            'price_2026-11-17.xlsx',
            'Общий прайс',
            [
                '1. Шина 255 - 5000р 4 шт.',
                '2. АКБ 255 - 4500р/6000р 2 шт. (Поставщик АКБ)',
                '3. АКБ 255 специальный - 5000р/7000р 1 шт.',
            ],
        ),
        (
            'sheet:Аккумуляторы',
            'price_2026-11-17.xlsx',
            'Общий прайс — Аккумуляторы',
            ['1. АКБ 255 - 4500р/6000р 2 шт. (Поставщик АКБ)'],
        ),
        ('sheet:Шины и диски', 'price_2026-11-17.xlsx', 'Общий прайс — Шины и диски', ['1. Шина 255 - 5000р 4 шт.']),
        (
            'sheet:Спецпредложения',
            'price_2026-11-17.xlsx',
            'Общий прайс — Спецпредложения',
            ['1. АКБ 255 специальный - 5000р/7000р 1 шт.'],
        ),
    ],
)
def test_selected_source_searches_real_workbook(
    _result_prices: None,
    source_key: str,
    file_name: str,
    source_title: str,
    expected_positions: list[str],
) -> None:
    if source_key.startswith('sheet:'):
        sheet_name = source_key.removeprefix('sheet:')
        sources = price_sources.get_sources()
        source_key = next(source.key for source in sources if source.sheet_name == sheet_name)
    context = make_context()

    async def choose_and_search() -> None:
        await handlers.choose_source(make_update('/source'), context)
        await handlers.set_source(make_update(callback_data=f'src:{source_key}'), context)
        await handlers.search(make_update('255'), context)

    asyncio.run(choose_and_search())

    labels = keyboard_labels(context.bot.sent[0])
    expected_button = f'{source_title}: {file_name}'
    assert any(expected_button in label for label in labels)
    assert context.bot.texts[1] == f'Поиск будет идти по: <b>{source_title}</b>'
    assert context.bot.texts[-1].splitlines() == [
        f'Источник: {source_title} ({file_name})',
        f'Найдено {len(expected_positions)} позиций',
        *expected_positions,
    ]


@pytest.mark.parametrize(
    ('sheet_name', 'expected_types'),
    [
        ('Шины и диски', ['Легковая шина', 'Грузовая шина', 'Диск']),
        ('Аккумуляторы', ['Аккумулятор']),
        (None, ['Легковая шина', 'Грузовая шина', 'Диск', 'Аккумулятор']),
    ],
)
def test_common_price_keyboard_matches_selected_sheet(
    _result_prices: None, sheet_name: str | None, expected_types: list[str]
) -> None:
    source = next(
        source
        for source in price_sources.get_sources()
        if source.sheet_name == sheet_name and source.key.startswith('inner')
    )
    context = make_context()
    asyncio.run(handlers.set_source(make_update(callback_data=f'src:{source.key}'), context))
    assert keyboard_labels(context.bot.sent[-1]) == ['✅ Все', *expected_types]


def test_source_menu_lists_workbook_sheets_under_common_price(_result_prices: None) -> None:
    context = make_context()
    asyncio.run(handlers.choose_source(make_update('/source'), context))
    labels = keyboard_labels(context.bot.sent[0])
    titles = [label.split(':', 1)[0] for label in labels]
    assert titles == [
        '✅ Прайс для Дрома (АКБ)',
        'Прайс для Дрома (шины) (не сформирован)',
        'Общий прайс',
        'Общий прайс — Шины и диски',
        'Общий прайс — Аккумуляторы',
        'Общий прайс — Спецпредложения',
        'Полный прайс (не сформирован)',
    ]
