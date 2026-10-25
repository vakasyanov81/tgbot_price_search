import asyncio

import pytest

from autosnab_bot.services import priceformation_vendors
from autosnab_bot.services.priceformation_cli import CommandResult

VENDORS_JSON = (
    '{"ok": true, "action": "get_vendors", "vendors": ['
    '{"folder": "poshk", "name": "Пошк", "enabled": true},'
    '{"folder": "mim", "name": "МИМ", "enabled": false}]}'
)
TOGGLED_JSON = '{"ok": true, "action": "toggle_vendor", "vendor": {"folder": "mim", "name": "МИМ", "enabled": true}}'


def stub_run(monkeypatch: pytest.MonkeyPatch, outcome: CommandResult, calls: list[tuple[str, ...]]) -> None:
    async def run_command(*args: str) -> CommandResult:
        calls.append(args)
        return outcome

    monkeypatch.setattr(priceformation_vendors, 'run_command', run_command)


def test_get_vendors_reads_activity_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    stub_run(monkeypatch, CommandResult(0, VENDORS_JSON), calls)

    vendors = asyncio.run(priceformation_vendors.get_vendors())

    assert calls == [('get_vendors',)]
    assert vendors == [
        priceformation_vendors.Vendor('poshk', 'Пошк', True),
        priceformation_vendors.Vendor('mim', 'МИМ', False),
    ]


def test_toggle_vendor_passes_folder_and_returns_new_state(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    stub_run(monkeypatch, CommandResult(0, TOGGLED_JSON), calls)

    vendor = asyncio.run(priceformation_vendors.toggle_vendor('mim'))

    assert calls == [('toggle_vendor', 'mim')]
    assert vendor == priceformation_vendors.Vendor('mim', 'МИМ', True)


def test_get_vendors_error_message_from_cli_json(monkeypatch: pytest.MonkeyPatch) -> None:
    error = '{"ok": false, "action": "get_vendors", "error": {"kind": "KeyError", "message": "boom"}}'
    stub_run(monkeypatch, CommandResult(1, error), [])

    with pytest.raises(RuntimeError, match='boom'):
        asyncio.run(priceformation_vendors.get_vendors())


def test_toggle_vendor_error_text_when_output_is_not_json(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(1, 'uv: command not found'), [])

    with pytest.raises(RuntimeError, match='uv: command not found'):
        asyncio.run(priceformation_vendors.toggle_vendor('mim'))


def test_get_vendors_rejects_unexpected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(0, '["не поставщики"]'), [])

    with pytest.raises(RuntimeError):
        asyncio.run(priceformation_vendors.get_vendors())


def test_get_vendors_without_list_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(0, '{"ok": true, "action": "get_vendors"}'), [])

    with pytest.raises(RuntimeError, match='список поставщиков'):
        asyncio.run(priceformation_vendors.get_vendors())


def test_vendor_with_wrong_field_type_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = '{"ok": true, "vendors": [{"folder": "poshk", "name": "Пошк", "enabled": "yes"}]}'
    stub_run(monkeypatch, CommandResult(0, broken), [])

    with pytest.raises(RuntimeError, match='неизвестного формата'):
        asyncio.run(priceformation_vendors.get_vendors())


def test_toggle_without_vendor_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(0, '{"ok": true, "action": "toggle_vendor"}'), [])

    with pytest.raises(RuntimeError, match='неизвестного формата'):
        asyncio.run(priceformation_vendors.toggle_vendor('mim'))
