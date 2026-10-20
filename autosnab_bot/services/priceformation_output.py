"""Тексты ответов по результатам команд priceformation (HTML для Telegram)."""

import html
import json
from collections.abc import Mapping
from pathlib import Path

from autosnab_bot.services.priceformation_cli import ERROR_TAIL, CommandResult, tail

# Запас под заголовок и теги: лимит сообщения Telegram 4096 символов.
LOG_LIMIT = 3500


def log_block(output: str) -> str:
    """Хвост вывода CLI блоком <pre>; пустой вывод — пустая строка."""
    text = tail(output, LOG_LIMIT)
    return f'<pre>{html.escape(text)}</pre>' if text else ''


def error_text(output: str) -> str:
    """Текст ошибки из JSON-ответа CLI; если ответ не JSON — хвост вывода."""
    error = _json_error(output)
    if error:
        return error
    return tail(output, ERROR_TAIL) or 'неизвестная ошибка'


def update_report(outcomes: Mapping[str, CommandResult]) -> str:
    """Итог обновления прайсов: по строке на источник."""
    lines = ['<b>Обновление прайсов поставщиков</b>']
    for label, outcome in outcomes.items():
        status = '✅' if outcome.ok else '❌'
        reason = '' if outcome.ok else f': {html.escape(error_text(outcome.output))}'
        lines.append(f'{status} {html.escape(label)}{reason}')
    return '\n'.join(lines)


def placed_names(outcome: CommandResult) -> list[str]:
    """Имена, под которыми priceformation положил файлы (из поля files JSON-ответа)."""
    try:
        payload = outcome.json()
    except ValueError:
        return []
    files = payload.get('files', []) if isinstance(payload, dict) else []
    return [Path(path).name for path in files if isinstance(path, str)]


def _json_error(output: str) -> str:
    last_line = output.strip().rsplit('\n', 1)[-1]
    try:
        payload = json.loads(last_line)
    except ValueError:
        return ''
    error = payload.get('error') if isinstance(payload, dict) else None
    if isinstance(error, dict):
        error = error.get('message') or error.get('kind')
    return str(error) if error else ''
