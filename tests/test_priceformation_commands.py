import asyncio
import json
from pathlib import Path

import pytest

from autosnab_bot.services import priceformation
from autosnab_bot.services.priceformation_cli import CommandResult

OK = CommandResult(0, '{"ok": true}')


def recorder(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, ...]]:
    calls: list[tuple[str, ...]] = []

    async def run_command(*args: str) -> CommandResult:
        assert priceformation.is_busy()
        calls.append(args)
        return OK

    monkeypatch.setattr(priceformation, 'run_command', run_command)
    return calls


def test_make_price(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = recorder(monkeypatch)
    monkeypatch.setattr(priceformation, 'result_files_since', lambda _started: [tmp_path])
    assert asyncio.run(priceformation.make_price()) == (OK, [tmp_path])
    assert calls == [('parse',)]
    assert not priceformation.is_busy()


def test_update_all_runs_every_source(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = recorder(monkeypatch)
    outcomes = asyncio.run(priceformation.update_all_prices())
    assert list(outcomes) == list(priceformation.UPDATE_COMMANDS.values())
    assert [call[0] for call in calls] == list(priceformation.UPDATE_COMMANDS)


def test_load_supplier_prices(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = recorder(monkeypatch)
    sources = [Path('/a/price.xlsx'), Path('/b/territories.json')]
    asyncio.run(priceformation.load_supplier_prices('4', sources))
    command, mapping = calls[0]
    assert command == 'load_supplier_prices'
    assert json.loads(mapping) == {'4': ['/a/price.xlsx', '/b/territories.json']}


@pytest.mark.parametrize(
    ('file_name', 'expected'),
    [
        ('price.xls', True),
        ('Прайс.XLSX', True),
        ('territories.json', True),
        ('mim.zip', True),
        ('price.csv', False),
        ('xlsx', False),
        (None, False),
    ],
)
def test_is_supplier_file(file_name: str | None, expected: bool) -> None:
    assert priceformation.is_supplier_file(file_name) is expected
