"""Запуск CLI priceformation (git-сабмодуль) из бота."""

import asyncio
import dataclasses
import json
import os
import re
import time
from pathlib import Path

from autosnab_bot import config

PRICEFORMATION_DIR = config.BASE_DIR.parent / "priceformation"
RESULT_DIR = PRICEFORMATION_DIR / "file_prices" / "result"
README_FILE = PRICEFORMATION_DIR / "README.md"

PARSE = "parse"
GET_SUPPLIERS = "get_supliers"
GET_PRODUCT_TYPES = "get_product_types"
LOAD_SUPPLIER_PRICES = "load_supplier_prices"
# Что принимает load_supplier_prices: прайсы, json-файлы поставщика (territories.json, tire.json …) и zip с ними.
SUPPLIER_FILE_EXTENSIONS = (".xls", ".xlsx", ".json", ".zip")
# Пункт меню «обновить прайсы всех поставщиков» в CLI: API запаски, Форточек, МИМ, затем почта.
UPDATE_COMMANDS = {
    "zapaska_load_api_data": "Запаска (API)",
    "four_tochki_load_api_data": "Форточки (API)",
    "mim_load_api_data": "МИМ (API)",
    "fetch_mail_prices": "почта",
}

COMMAND_TIMEOUT = 30 * 60

# VIRTUAL_ENV бота сбивает uv с окружения сабмодуля, а токен бота priceformation не нужен.
_HIDDEN_ENV = frozenset(("VIRTUAL_ENV", "TELEGRAM_BOT_TOKEN"))

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Один запуск за раз: команды пишут в одни и те же папки file_prices.
_lock = asyncio.Lock()


@dataclasses.dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def json(self) -> object:
        """JSON-ответ CLI: последняя строка вывода (выше могут быть предупреждения uv)."""
        return json.loads(self.output.strip().rsplit("\n", 1)[-1])


def is_available() -> bool:
    return (PRICEFORMATION_DIR / "pyproject.toml").is_file()


def is_busy() -> bool:
    return _lock.locked()


async def run_command(*args: str) -> CommandResult:
    """Запустить `priceformation <args>` в окружении сабмодуля, stdout и stderr вместе."""
    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "--project",
        str(PRICEFORMATION_DIR),
        "priceformation",
        *args,
        cwd=PRICEFORMATION_DIR,
        env={key: value for key, value in os.environ.items() if key not in _HIDDEN_ENV},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=COMMAND_TIMEOUT)
    except TimeoutError:
        process.kill()
        await process.wait()
        return CommandResult(-1, f"Команда не завершилась за {COMMAND_TIMEOUT // 60} мин. и была остановлена")
    return CommandResult(process.returncode or 0, strip_ansi(stdout.decode(errors="replace")))


async def make_price() -> tuple[CommandResult, list[Path]]:
    """Сформировать общий прайс; вернуть результат и файлы, записанные за этот запуск."""
    async with _lock:
        started = time.time()
        result = await run_command(PARSE)
    return result, result_files_since(started)


async def update_all_prices() -> dict[str, CommandResult]:
    """Обновить прайсы всех поставщиков. Сбой одного источника не отменяет остальные, как в CLI."""
    async with _lock:
        return {label: await run_command(command, "--json") for command, label in UPDATE_COMMANDS.items()}


async def get_suppliers() -> dict[str, str]:
    """Каталог поставщиков: ИД → название."""
    result = await run_command(GET_SUPPLIERS)
    catalog = result.json() if result.ok else None
    if not isinstance(catalog, dict):
        raise RuntimeError(tail(result.output, 300) or "не удалось получить список поставщиков")
    return {supplier_id: entry["sup_title"] for supplier_id, entry in catalog.items()}


async def get_product_types() -> list[str]:
    """Типы товара, которые priceformation ставит в колонку «Тип товара» прайсов."""
    result = await run_command(GET_PRODUCT_TYPES)
    payload = result.json() if result.ok else None
    types = payload.get("types") if isinstance(payload, dict) else None
    if not isinstance(types, list):
        raise RuntimeError(tail(result.output, 300) or "не удалось получить типы товара")
    return [str(product_type) for product_type in types]


async def load_supplier_prices(supplier_id: str, sources: list[Path]) -> CommandResult:
    """Разложить файлы (или zip) по папке поставщика; имена назначает priceformation по маскам поставщика."""
    async with _lock:
        return await run_command(LOAD_SUPPLIER_PRICES, json.dumps({supplier_id: [str(path) for path in sources]}))


def is_supplier_file(file_name: str | None) -> bool:
    return file_name is not None and Path(file_name).suffix.lower() in SUPPLIER_FILE_EXTENSIONS


def result_files_since(started: float) -> list[Path]:
    if not RESULT_DIR.is_dir():
        return []
    return sorted(path for path in RESULT_DIR.iterdir() if path.is_file() and path.stat().st_mtime >= started)


def strip_ansi(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text)


def tail(text: str, limit: int) -> str:
    """Последние строки текста, не длиннее limit символов."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[-limit:]
    newline = cut.find("\n")
    return "…\n" + (cut[newline + 1 :] if newline != -1 else cut)
