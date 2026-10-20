import asyncio
import importlib

from autosnab_bot.services import type_menu
from tests.fakes import keyboard_labels, make_context, make_update

search_module = importlib.import_module('autosnab_bot.handlers.search')
TIRE = 'Легковая шина'


def test_keyboard_marks_active_type() -> None:
    keyboard = asyncio.run(type_menu.type_keyboard(make_context({type_menu.USER_TYPE_FILTER: 'Диск'})))
    assert [[button.text for button in row] for row in keyboard.keyboard] == [
        ['Все', TIRE],
        ['Грузовая шина', '✅ Диск'],
    ]
    assert keyboard.resize_keyboard is True


def test_chip_sets_and_clears_filter() -> None:
    context = make_context()
    asyncio.run(search_module.search(make_update(TIRE), context))
    assert context.user_data == {type_menu.USER_TYPE_FILTER: TIRE}
    assert f'✅ {TIRE}' in keyboard_labels(context.bot.sent[-1])

    asyncio.run(search_module.search(make_update(f'✅ {TIRE}'), context))
    assert context.user_data == {type_menu.USER_TYPE_FILTER: TIRE}

    asyncio.run(search_module.search(make_update('Все'), context))
    assert context.user_data == {}
    assert '✅ Все' in keyboard_labels(context.bot.sent[-1])
    assert context.bot.texts[-1] == 'Фильтр снят: поиск по всем типам товара'
