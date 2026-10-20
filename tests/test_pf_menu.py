import asyncio
from pathlib import Path

import pytest

from autosnab_bot.handlers import pf_menu
from autosnab_bot.handlers.pf_callbacks import CALLBACK_PREFIX, MAKE_PRICE, SHOW_HELP, UPDATE_ALL
from autosnab_bot.services import priceformation
from autosnab_bot.services.priceformation_cli import CommandResult
from tests.fakes import FakeBot, keyboard_labels, make_context, make_update

OK = CommandResult(0, 'готово')


def press(callback_data: str) -> list[str]:
    context = make_context()
    asyncio.run(pf_menu.priceformation_action(make_update(callback_data=callback_data), context))
    bot: FakeBot = context.bot
    return [*bot.texts, *bot.documents]


def test_menu_shows_buttons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pf_menu, 'is_available', lambda: True)
    context = make_context()
    asyncio.run(pf_menu.priceformation_menu(make_update('/pf'), context))
    assert 'Загрузить прайс поставщика' in keyboard_labels(context.bot.sent[0])


def test_menu_without_submodule(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pf_menu, 'is_available', bool)
    context = make_context()
    asyncio.run(pf_menu.priceformation_menu(make_update('/pf'), context))
    assert 'git submodule update --init' in context.bot.texts[0]


def test_make_price_sends_log_and_files(monkeypatch: pytest.MonkeyPatch) -> None:
    async def make_price() -> tuple[CommandResult, list[Path]]:
        return OK, [Path('price_drom_2026-10-20.xlsx')]

    monkeypatch.setattr(priceformation, 'make_price', make_price)
    monkeypatch.setattr(pf_menu, 'send_document', _fake_send_document)
    assert press(MAKE_PRICE)[1:] == ['<b>Общий прайс сформирован</b>\n<pre>готово</pre>', 'sent']


def test_update_all_reports_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    async def update_all_prices() -> dict[str, CommandResult]:
        return {'почта': OK}

    monkeypatch.setattr(priceformation, 'update_all_prices', update_all_prices)
    assert press(UPDATE_ALL)[-1] == '<b>Обновление прайсов поставщиков</b>\n✅ почта'


def test_busy_blocks_file_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(priceformation, 'is_busy', lambda: True)
    assert press(MAKE_PRICE) == ['Уже выполняется другая команда, дождитесь её завершения']


def test_help_sends_readme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pf_menu, 'send_document', _fake_send_document)
    assert press(SHOW_HELP) == ['sent']


def test_unknown_button_is_ignored() -> None:
    assert press(f'{CALLBACK_PREFIX}nope') == []


async def _fake_send_document(update: object, context: object, path: Path) -> None:
    context.bot.documents.append('sent')  # type: ignore[attr-defined]
