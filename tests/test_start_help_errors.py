import asyncio
from types import SimpleNamespace

import pytest
from telegram import Update
from telegram.error import TelegramError

from autosnab_bot import handlers
from autosnab_bot.services import validate_user
from tests.fakes import keyboard_labels, make_context, make_update


def test_start_and_help_show_menu() -> None:
    context = make_context()
    asyncio.run(handlers.start(make_update('/start'), context))
    asyncio.run(handlers.help_(make_update('/help'), context))
    assert context.bot.texts[0].startswith('Салам, пополам!')
    assert '/source' in context.bot.texts[1]
    assert all('✅ Все' in keyboard_labels(message) for message in context.bot.sent)


def test_help_lists_admin_command_only_for_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_user, 'ADMIN_USER_IDS', frozenset())
    context = make_context()
    asyncio.run(handlers.help_(make_update('/help'), context))
    assert '/start' in context.bot.texts[0]
    assert '/script_manager' not in context.bot.texts[0]


def test_help_lists_admin_command_for_admin() -> None:
    context = make_context()
    asyncio.run(handlers.help_(make_update('/help'), context))
    assert '/script_manager' in context.bot.texts[0]


def real_update() -> Update:
    chat = {'id': 1, 'type': 'private'}
    message = {'message_id': 1, 'date': 0, 'chat': chat, 'text': 'r15'}
    return Update.de_json({'update_id': 1, 'message': message}, None)


def test_error_handler_tells_user() -> None:
    context = make_context()
    context.error = RuntimeError('boom')
    update = real_update()
    asyncio.run(handlers.on_error(update, context))
    assert context.bot.texts == ['Не удалось выполнить запрос: boom. Попробуйте ещё раз или уточните запрос']


def test_error_handler_without_chat_is_silent() -> None:
    context = make_context()
    asyncio.run(handlers.on_error(SimpleNamespace(), context))
    assert context.bot.sent == []


def test_error_handler_survives_send_failure() -> None:
    async def send_message(**_kwargs: object) -> None:
        raise TelegramError('blocked')

    context = make_context()
    context.bot.send_message = send_message
    update = real_update()
    asyncio.run(handlers.on_error(update, context))
