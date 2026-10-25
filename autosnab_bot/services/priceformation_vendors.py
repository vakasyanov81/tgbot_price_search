"""Поставщики priceformation (файлы конфигов) и их активность: команды CLI get_vendors и toggle_vendor."""

import contextlib
from dataclasses import dataclass

from autosnab_bot.services.priceformation_cli import CommandResult, run_command
from autosnab_bot.services.priceformation_output import error_text

GET_VENDORS = 'get_vendors'
TOGGLE_VENDOR = 'toggle_vendor'
_UNEXPECTED_VENDOR = 'priceformation вернул поставщика неизвестного формата'


@dataclass(frozen=True)
class Vendor:
    folder: str
    name: str
    enabled: bool


async def get_vendors() -> list[Vendor]:
    payload = _payload(await run_command(GET_VENDORS))
    entries = payload.get('vendors')
    if not isinstance(entries, list):
        raise RuntimeError('priceformation не вернул список поставщиков')
    return [_vendor(entry) for entry in entries]


async def toggle_vendor(folder: str) -> Vendor:
    payload = _payload(await run_command(TOGGLE_VENDOR, folder))
    return _vendor(payload.get('vendor'))


def _payload(command_result: CommandResult) -> dict[str, object]:
    payload = _parse(command_result)
    if not command_result.ok or payload.get('ok') is not True:
        raise RuntimeError(error_text(command_result.output))
    return payload


def _parse(command_result: CommandResult) -> dict[str, object]:
    payload: object = None
    with contextlib.suppress(ValueError):
        payload = command_result.json()
    return payload if isinstance(payload, dict) else {}


def _vendor(entry: object) -> Vendor:
    if not isinstance(entry, dict):
        raise RuntimeError(_UNEXPECTED_VENDOR)
    folder = _field(entry, 'folder', str)
    name = _field(entry, 'name', str)
    enabled = _field(entry, 'enabled', bool)
    return Vendor(folder=folder, name=name, enabled=enabled)


def _field[Kind](entry: dict[str, object], key: str, kind: type[Kind]) -> Kind:
    found = entry.get(key)
    if not isinstance(found, kind):
        raise RuntimeError(_UNEXPECTED_VENDOR)
    return found
