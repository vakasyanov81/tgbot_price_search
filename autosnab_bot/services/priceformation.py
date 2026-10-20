"""Команды priceformation, которые меняют файлы: выполняются по одной за раз."""

import asyncio
import json
import time
from pathlib import Path

from autosnab_bot.services.priceformation_cli import CommandResult, result_files_since, run_command

PARSE = 'parse'
LOAD_SUPPLIER_PRICES = 'load_supplier_prices'
# Что принимает load_supplier_prices: прайсы, json-файлы поставщика (territories.json, tire.json …) и zip с ними.
SUPPLIER_FILE_EXTENSIONS = ('.xls', '.xlsx', '.json', '.zip')
# Пункт меню «обновить прайсы всех поставщиков» в CLI: API запаски, Форточек, МИМ, затем почта.
UPDATE_COMMANDS = {
    'zapaska_load_api_data': 'Запаска (API)',
    'four_tochki_load_api_data': 'Форточки (API)',
    'mim_load_api_data': 'МИМ (API)',
    'fetch_mail_prices': 'почта',
}

# Один запуск за раз: команды пишут в одни и те же папки file_prices.
_lock = asyncio.Lock()


def is_busy() -> bool:
    return _lock.locked()


async def make_price() -> tuple[CommandResult, list[Path]]:
    """Сформировать общий прайс; вернуть результат и файлы, записанные за этот запуск."""
    async with _lock:
        started = time.time()
        command_result = await run_command(PARSE)
    return command_result, result_files_since(started)


async def update_all_prices() -> dict[str, CommandResult]:
    """Обновить прайсы всех поставщиков по очереди. Сбой одного источника не отменяет остальные, как в CLI."""
    outcomes: dict[str, CommandResult] = {}
    async with _lock:
        for command, label in UPDATE_COMMANDS.items():
            # Источники обновляются строго по очереди, как в CLI, поэтому await в цикле, а не gather.
            outcomes[label] = await run_command(command, '--json')  # noqa: WPS476
    return outcomes


async def load_supplier_prices(supplier_id: str, sources: list[Path]) -> CommandResult:
    """Разложить файлы (или zip) по папке поставщика; имена назначает priceformation по маскам поставщика."""
    mapping = json.dumps({supplier_id: [str(path) for path in sources]})
    async with _lock:
        return await run_command(LOAD_SUPPLIER_PRICES, mapping)


def is_supplier_file(file_name: str | None) -> bool:
    return file_name is not None and Path(file_name).suffix.lower() in SUPPLIER_FILE_EXTENSIONS
