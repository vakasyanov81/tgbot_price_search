import asyncio
from types import SimpleNamespace

from telegram import Update
from telegram.error import TelegramError

from autosnab_bot import handlers
from tests.fakes import keyboard_labels, make_context, make_update


def test_start_and_help_show_menu() -> None:
    context = make_context()
    asyncio.run(handlers.start(make_update('/start'), context))
    asyncio.run(handlers.help_(make_update('/help'), context))
    assert context.bot.texts[0].startswith('Салам, пополам!')
    assert '/source' in context.bot.texts[1]
    assert all('✅ Все' in keyboard_labels(message) for message in context.bot.sent)


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
