"""Ответы бота на поисковые запросы чата: чтобы при правке запроса заменить ответ, а не добавить ещё один."""

import hashlib
from typing import Any, cast

# Ключ в chat_data: ИД сообщения с запросом → (ИД ответа бота, отпечаток текста ответа).
SEARCH_REPLIES = 'search_replies'
MAX_SEARCH_REPLIES = 200

type _Replies = dict[int, tuple[int, str]]


class SearchReplies:
    def __init__(self, chat_data: dict[Any, Any] | None) -> None:
        stored: dict[int, tuple[int, str] | int] = {}
        if chat_data is not None:
            stored = chat_data.setdefault(SEARCH_REPLIES, {})
        # Записи старого формата (только ИД ответа) приводятся к паре.
        for query_id, record in stored.items():
            if isinstance(record, int):
                stored[query_id] = (record, '')
        self._replies = cast(_Replies, stored)

    def previous(self, query_id: int) -> tuple[int, str] | None:
        return self._replies.get(query_id)

    def remember(self, query_id: int, reply_id: int, digest: str) -> None:
        self._replies[query_id] = (reply_id, digest)
        while len(self._replies) > MAX_SEARCH_REPLIES:
            self._replies.pop(next(iter(self._replies)))


def digest(response: str) -> str:
    return hashlib.sha256(response.encode()).hexdigest()
