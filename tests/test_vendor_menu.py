import asyncio
from typing import Any

import pytest

from autosnab_bot.handlers import vendor_menu
from autosnab_bot.services import priceformation_vendors, validate_user
from tests.fakes import keyboard_labels, make_context, make_update

VENDORS = [
    priceformation_vendors.Vendor('poshk', 'Пошк', True),
    priceformation_vendors.Vendor('mim', 'МИМ', False),
]


def _callback_update(callback_data: str) -> tuple[Any, list[Any]]:
    """Нажатие кнопки и список клавиатур, которыми его перерисовали."""
    redrawn: list[Any] = []

    async def edit_message_reply_markup(reply_markup: Any) -> None:
        redrawn.append(reply_markup)

    update = make_update(callback_data=callback_data)
    update.callback_query.edit_message_reply_markup = edit_message_reply_markup
    return update, redrawn


def _stub_vendors(monkeypatch: pytest.MonkeyPatch, vendors: list[priceformation_vendors.Vendor]) -> None:
    async def get_vendors() -> list[priceformation_vendors.Vendor]:
        return vendors

    monkeypatch.setattr(priceformation_vendors, 'get_vendors', get_vendors)


def test_show_vendors_lists_suppliers_with_activity_marks(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_vendors(monkeypatch, VENDORS)
    context = make_context()
    update, _ = _callback_update(vendor_menu.VENDORS_CALLBACK)
    asyncio.run(vendor_menu.show_vendors(update, context))

    assert keyboard_labels(context.bot.sent[0]) == ['[✅] Пошк', '[ ] МИМ']
    message = context.bot.sent[0]
    rows = message['reply_markup'].inline_keyboard
    assert [row[0].callback_data for row in rows] == ['script_vendor:poshk', 'script_vendor:mim']


def test_show_vendors_reports_cli_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def get_vendors() -> list[priceformation_vendors.Vendor]:
        raise RuntimeError('KeyError: boom')

    monkeypatch.setattr(priceformation_vendors, 'get_vendors', get_vendors)
    context = make_context()
    update, _ = _callback_update(vendor_menu.VENDORS_CALLBACK)
    asyncio.run(vendor_menu.show_vendors(update, context))

    assert 'Не удалось получить поставщиков' in context.bot.texts[0]
    assert 'KeyError: boom' in context.bot.texts[0]


def test_show_vendors_denies_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ADMIN_USER_IDS', frozenset())
    calls: list[int] = []

    async def get_vendors() -> list[priceformation_vendors.Vendor]:
        calls.append(1)
        return VENDORS

    monkeypatch.setattr(priceformation_vendors, 'get_vendors', get_vendors)
    context = make_context()
    update, _ = _callback_update(vendor_menu.VENDORS_CALLBACK)
    asyncio.run(vendor_menu.show_vendors(update, context))

    assert calls == []
    assert 'только администраторам' in context.bot.texts[0]


def test_switch_vendor_toggles_folder_and_redraws_list(monkeypatch: pytest.MonkeyPatch) -> None:
    toggled: list[str] = []

    async def toggle_vendor(folder: str) -> priceformation_vendors.Vendor:
        toggled.append(folder)
        return priceformation_vendors.Vendor(folder, 'МИМ', True)

    async def get_vendors() -> list[priceformation_vendors.Vendor]:
        return [priceformation_vendors.Vendor('poshk', 'Пошк', True), priceformation_vendors.Vendor('mim', 'МИМ', True)]

    monkeypatch.setattr(priceformation_vendors, 'toggle_vendor', toggle_vendor)
    monkeypatch.setattr(priceformation_vendors, 'get_vendors', get_vendors)
    update, redrawn = _callback_update('script_vendor:mim')
    context = make_context()
    asyncio.run(vendor_menu.switch_vendor(update, context))

    assert toggled == ['mim']
    assert context.bot.sent == []
    labels = [button.text for row in redrawn[0].inline_keyboard for button in row]
    assert labels == ['[✅] Пошк', '[✅] МИМ']


def test_switch_vendor_reports_cli_error_and_keeps_list(monkeypatch: pytest.MonkeyPatch) -> None:
    async def toggle_vendor(_folder: str) -> priceformation_vendors.Vendor:
        raise RuntimeError('неизвестный поставщик: mim')

    monkeypatch.setattr(priceformation_vendors, 'toggle_vendor', toggle_vendor)
    update, redrawn = _callback_update('script_vendor:mim')
    context = make_context()
    asyncio.run(vendor_menu.switch_vendor(update, context))

    assert 'Не удалось переключить поставщика' in context.bot.texts[0]
    assert 'неизвестный поставщик: mim' in context.bot.texts[0]
    assert redrawn == []


def test_switch_vendor_denies_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ADMIN_USER_IDS', frozenset())
    calls: list[str] = []

    async def toggle_vendor(folder: str) -> priceformation_vendors.Vendor:
        calls.append(folder)
        return priceformation_vendors.Vendor(folder, 'МИМ', True)

    monkeypatch.setattr(priceformation_vendors, 'toggle_vendor', toggle_vendor)
    update, _ = _callback_update('script_vendor:mim')
    context = make_context()
    asyncio.run(vendor_menu.switch_vendor(update, context))

    assert calls == []
    assert 'только администраторам' in context.bot.texts[0]


def test_vendor_menu_ignores_message_without_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_vendors(monkeypatch, VENDORS)
    context = make_context()
    asyncio.run(vendor_menu.show_vendors(make_update('/script_manager'), context))

    assert context.bot.sent == []


def test_switch_vendor_ignores_message_without_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def toggle_vendor(folder: str) -> priceformation_vendors.Vendor:
        calls.append(folder)
        return priceformation_vendors.Vendor(folder, 'МИМ', True)

    monkeypatch.setattr(priceformation_vendors, 'toggle_vendor', toggle_vendor)
    context = make_context()
    asyncio.run(vendor_menu.switch_vendor(make_update('/script_manager'), context))

    assert calls == []
    assert context.bot.sent == []
