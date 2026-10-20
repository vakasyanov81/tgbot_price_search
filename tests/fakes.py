"""Фейки Telegram для тестов обработчиков: бот, обновление и контекст."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

ALLOWED_USER = 1
FIRST_MESSAGE_ID = 100

type UserData = dict[Any, Any]


class FakeTelegramFile:
    def __init__(self, file_bytes: bytes) -> None:
        self._file_bytes = file_bytes

    async def download_to_drive(self, target: Path) -> None:
        target.write_bytes(self._file_bytes)


class FakeBot:
    """Записывает отправленное; ошибки правки и удаления задаются при создании."""

    def __init__(self, edit_error: Exception | None = None, delete_error: Exception | None = None) -> None:
        self.sent: list[dict[str, Any]] = []
        self.edited: list[dict[str, Any]] = []
        self.deleted: list[int] = []
        self.documents: list[str] = []
        self.files: dict[str, bytes] = {}
        self._edit_error = edit_error
        self._delete_error = delete_error

    async def send_message(self, **kwargs: Any) -> SimpleNamespace:
        self.sent.append(kwargs)
        return SimpleNamespace(message_id=FIRST_MESSAGE_ID + len(self.sent))

    async def edit_message_text(self, text: str, **kwargs: Any) -> None:
        if self._edit_error:
            raise self._edit_error
        self.edited.append({'text': text, **kwargs})

    async def delete_message(self, **kwargs: Any) -> None:
        if self._delete_error:
            raise self._delete_error
        self.deleted.append(kwargs['message_id'])

    async def send_document(self, **kwargs: Any) -> None:
        self.documents.append(kwargs['filename'])

    async def get_file(self, file_id: str) -> FakeTelegramFile:
        return FakeTelegramFile(self.files[file_id])

    @property
    def texts(self) -> list[str]:
        return [message['text'] for message in self.sent]


async def answer_callback() -> None:
    """Ответ на нажатие кнопки (query.answer) — в тестах ничего не делает."""


def make_update(
    text: str | None = None,
    *,
    edited: bool = False,
    callback_data: str | None = None,
    document: Any = None,
    user_id: int = ALLOWED_USER,
    message_id: int = 1,
) -> Any:
    message = SimpleNamespace(text=text, message_id=message_id, document=document)
    has_message = text is not None or document is not None
    query = SimpleNamespace(data=callback_data, answer=answer_callback) if callback_data else None
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        effective_chat=SimpleNamespace(id=ALLOWED_USER),
        message=message if has_message and not edited else None,
        edited_message=message if edited else None,
        callback_query=query,
    )


def make_context(user_data: UserData | None = None, bot: FakeBot | None = None) -> Any:
    return SimpleNamespace(
        bot=bot or FakeBot(),
        user_data={} if user_data is None else user_data,
        chat_data={},
        bot_data={},
        error=None,
    )


def make_document(file_name: str, file_size: int = 1, file_id: str = 'file-1') -> Any:
    return SimpleNamespace(file_name=file_name, file_size=file_size, file_id=file_id)


def keyboard_labels(message: dict[str, Any]) -> list[str]:
    """Подписи кнопок нижнего меню или встроенных кнопок сообщения."""
    markup = message['reply_markup']
    rows = getattr(markup, 'keyboard', None) or markup.inline_keyboard
    return [button.text for row in rows for button in row]
