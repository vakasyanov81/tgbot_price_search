import asyncio
import importlib
from types import SimpleNamespace

import pytest
from telegram.error import BadRequest

from autosnab_bot.handlers import type_filter
from autosnab_bot.services import validate_user

# handlers/__init__ экспортирует функцию search, она перекрывает одноимённый модуль.
search_module = importlib.import_module("autosnab_bot.handlers.search")


class FakeBot:
    def __init__(self, edit_error=None):
        self.sent = []
        self.edited = []
        self.edit_error = edit_error

    async def send_message(self, **kwargs):
        self.sent.append(kwargs["text"])
        return SimpleNamespace(message_id=100 + len(self.sent))

    async def edit_message_text(self, **kwargs):
        if self.edit_error:
            raise self.edit_error
        self.edited.append((kwargs["message_id"], kwargs["text"]))


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    monkeypatch.setattr(validate_user, "ALLOWED_USER_IDS", frozenset({1}))

    async def fake_response(_context, text):
        return f"результат: {text}"

    monkeypatch.setattr(search_module, "search_response", fake_response)

    async def fake_types():
        return ["Легковая шина", "Диск"]

    monkeypatch.setattr(type_filter, "get_product_types", fake_types)


def make_update(text, message_id=10, edited=False):
    message = SimpleNamespace(text=text, message_id=message_id)
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=1),
        effective_chat=SimpleNamespace(id=1),
        message=None if edited else message,
        edited_message=message if edited else None,
    )


def run(update, context):
    asyncio.run(search_module.search(update, context))  # type: ignore[arg-type]


def test_edited_query_edits_previous_reply():
    context = SimpleNamespace(bot=FakeBot(), chat_data={}, user_data={})
    run(make_update("185 65"), context)
    run(make_update("185 70", edited=True), context)

    assert context.bot.sent == ["результат: 185 65"]
    assert context.bot.edited == [(101, "результат: 185 70")]


def test_edited_query_without_known_reply_sends_new():
    context = SimpleNamespace(bot=FakeBot(), chat_data={}, user_data={})
    run(make_update("185 70", edited=True), context)

    assert context.bot.sent == ["результат: 185 70"]
    assert context.chat_data[search_module.SEARCH_REPLIES] == {10: 101}


def test_unchanged_result_is_not_resent():
    context = SimpleNamespace(bot=FakeBot(), chat_data={}, user_data={})
    run(make_update("kama"), context)
    context.bot.edit_error = BadRequest("Message is not modified: specified new message content ...")
    run(make_update("kama", edited=True), context)

    assert context.bot.sent == ["результат: kama"]


def test_deleted_reply_gets_new_one():
    context = SimpleNamespace(bot=FakeBot(), chat_data={}, user_data={})
    run(make_update("kama"), context)
    context.bot.edit_error = BadRequest("Message to edit not found")
    run(make_update("nokian", edited=True), context)

    assert context.bot.sent == ["результат: kama", "результат: nokian"]
    assert context.chat_data[search_module.SEARCH_REPLIES] == {10: 102}


def test_replies_map_is_bounded(monkeypatch):
    monkeypatch.setattr(search_module, "MAX_SEARCH_REPLIES", 2)
    context = SimpleNamespace(bot=FakeBot(), chat_data={}, user_data={})
    for message_id in (1, 2, 3):
        run(make_update("q", message_id=message_id), context)

    assert list(context.chat_data[search_module.SEARCH_REPLIES]) == [2, 3]
