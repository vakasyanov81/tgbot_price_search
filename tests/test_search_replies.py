from typing import Any

from autosnab_bot.services import search_replies

QUERY = 10
REPLY = 101


def test_remember_and_previous() -> None:
    chat_data: dict[Any, Any] = {}
    replies = search_replies.SearchReplies(chat_data)
    replies.remember(QUERY, REPLY, search_replies.digest('ответ'))
    expected = (REPLY, search_replies.digest('ответ'))
    assert search_replies.SearchReplies(chat_data).previous(QUERY) == expected


def test_legacy_record_becomes_pair() -> None:
    chat_data: dict[Any, Any] = {search_replies.SEARCH_REPLIES: {QUERY: REPLY}}
    assert search_replies.SearchReplies(chat_data).previous(QUERY) == (REPLY, '')


def test_without_chat_data() -> None:
    replies = search_replies.SearchReplies(None)
    replies.remember(QUERY, REPLY, 'x')
    assert replies.previous(QUERY) == (REPLY, 'x')


def test_bounded(monkeypatch: Any) -> None:
    monkeypatch.setattr(search_replies, 'MAX_SEARCH_REPLIES', 2)
    chat_data: dict[Any, Any] = {}
    replies = search_replies.SearchReplies(chat_data)
    for query_id in (1, 2, 3):
        replies.remember(query_id, REPLY, 'x')
    assert list(chat_data[search_replies.SEARCH_REPLIES]) == [2, 3]
