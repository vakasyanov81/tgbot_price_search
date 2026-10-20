import asyncio

import pytest

from autosnab_bot.services import priceformation_reference
from autosnab_bot.services.priceformation_cli import CommandResult


def stub_run(monkeypatch: pytest.MonkeyPatch, outcome: CommandResult) -> None:
    async def run_command(*_args: str) -> CommandResult:
        return outcome

    monkeypatch.setattr(priceformation_reference, 'run_command', run_command)


def test_get_suppliers(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(0, '{"1": {"sup_code": "poshk", "sup_title": "Пошк"}}'))
    assert asyncio.run(priceformation_reference.get_suppliers()) == {'1': 'Пошк'}


def test_get_suppliers_error(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(1, 'boom'))
    with pytest.raises(RuntimeError, match='boom'):
        asyncio.run(priceformation_reference.get_suppliers())


def test_get_product_types(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(0, '{"ok": true, "types": ["Диск"]}'))
    assert asyncio.run(priceformation_reference.get_product_types()) == ['Диск']


def test_get_product_types_error(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_run(monkeypatch, CommandResult(1, ''))
    with pytest.raises(RuntimeError, match='типы товара'):
        asyncio.run(priceformation_reference.get_product_types())
