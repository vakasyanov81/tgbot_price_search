import asyncio
from pathlib import Path

import pytest

from autosnab_bot.handlers import update_menu
from autosnab_bot.services import validate_user
from autosnab_bot.services.system_update import StepResult
from tests.fakes import ALLOWED_USER, keyboard_labels, make_context, make_update

ADMIN_COMMAND = '/script_manager'


def _fake_steps(ok: bool) -> list[StepResult]:
    return [StepResult('git pull --ff-only', ok, 'Already up to date.')]


def test_script_manager_shows_update_and_logs_buttons_to_admin() -> None:
    context = make_context()
    asyncio.run(update_menu.script_manager(make_update(ADMIN_COMMAND), context))

    assert keyboard_labels(context.bot.sent[0]) == ['Обновить систему', 'Выгрузить логи']


def test_export_logs_sends_archive_and_removes_it(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / 'autosnab-logs.zip'
    archive.write_bytes(b'zip')

    async def fake_build() -> Path:
        return archive

    sent: list[Path] = []

    async def fake_send_document(_update: object, _context: object, path: Path) -> None:
        sent.append(path)

    monkeypatch.setattr(update_menu, 'build_logs_archive', fake_build)
    monkeypatch.setattr(update_menu, 'send_document', fake_send_document)
    context = make_context()
    asyncio.run(update_menu.export_logs(make_update(callback_data=update_menu.LOGS_CALLBACK), context))

    assert sent == [archive]
    assert not archive.exists()


def test_export_logs_ignores_message_without_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    async def fake_build() -> Path:
        calls.append(1)
        raise AssertionError('не должно вызываться')

    monkeypatch.setattr(update_menu, 'build_logs_archive', fake_build)
    context = make_context()
    asyncio.run(update_menu.export_logs(make_update('/script_manager'), context))

    assert calls == []
    assert context.bot.sent == []


def test_export_logs_ignores_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ADMIN_USER_IDS', frozenset())
    calls: list[int] = []

    async def fake_build() -> Path:
        calls.append(1)
        raise AssertionError('не должно вызываться')

    monkeypatch.setattr(update_menu, 'build_logs_archive', fake_build)
    context = make_context()
    update = make_update(callback_data=update_menu.LOGS_CALLBACK, user_id=ALLOWED_USER)
    asyncio.run(update_menu.export_logs(update, context))

    assert calls == []
    assert 'только администраторам' in context.bot.texts[0]


def test_script_manager_denies_allowed_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ADMIN_USER_IDS', frozenset())
    context = make_context()
    asyncio.run(update_menu.script_manager(make_update(ADMIN_COMMAND), context))

    assert 'только администраторам' in context.bot.texts[0]
    assert context.bot.sent[0]['reply_markup'] is None


def test_update_system_restarts_service_after_successful_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    restarts: list[int] = []

    async def fake_update_code() -> list[StepResult]:
        return _fake_steps(ok=True)

    async def fake_restart() -> StepResult:
        restarts.append(1)
        return StepResult('systemctl --user restart autosnab-bot.service', ok=True, output='')

    monkeypatch.setattr(update_menu, 'update_code', fake_update_code)
    monkeypatch.setattr(update_menu, 'restart_service', fake_restart)
    context = make_context()
    asyncio.run(update_menu.update_system(make_update(callback_data=update_menu.UPDATE_CALLBACK), context))

    assert restarts == [1]
    assert any('git pull --ff-only' in text for text in context.bot.texts)


def test_update_system_keeps_service_running_after_failed_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    restarts: list[int] = []

    async def fake_update_code() -> list[StepResult]:
        return _fake_steps(ok=False)

    async def fake_restart() -> StepResult:
        restarts.append(1)
        return StepResult('systemctl', ok=True, output='')

    monkeypatch.setattr(update_menu, 'update_code', fake_update_code)
    monkeypatch.setattr(update_menu, 'restart_service', fake_restart)
    context = make_context()
    asyncio.run(update_menu.update_system(make_update(callback_data=update_menu.UPDATE_CALLBACK), context))

    assert restarts == []
    assert any('ОШИБКА' in text for text in context.bot.texts)


def test_update_system_reports_restart_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_update_code() -> list[StepResult]:
        return _fake_steps(ok=True)

    async def fake_restart() -> StepResult:
        return StepResult('systemctl --user restart autosnab-bot.service', ok=False, output='Unit not found.')

    monkeypatch.setattr(update_menu, 'update_code', fake_update_code)
    monkeypatch.setattr(update_menu, 'restart_service', fake_restart)
    context = make_context()
    asyncio.run(update_menu.update_system(make_update(callback_data=update_menu.UPDATE_CALLBACK), context))

    assert 'Unit not found.' in context.bot.texts[-1]


def test_update_system_ignores_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ADMIN_USER_IDS', frozenset())
    calls: list[int] = []

    async def fake_update_code() -> list[StepResult]:
        calls.append(1)
        return []

    monkeypatch.setattr(update_menu, 'update_code', fake_update_code)
    context = make_context()
    update = make_update(callback_data=update_menu.UPDATE_CALLBACK, user_id=ALLOWED_USER)
    asyncio.run(update_menu.update_system(update, context))

    assert calls == []
